#!/usr/bin/env python3
"""AI 관련 소식 자동 등록 — 매일 아침 검색어 「조류인플루엔자」로 기사를 찾아 중복 없는 1건을 올린다.

AI관련정보 탭의 「AI 관련 소식」 목록은 관리자가 화면에서 올리는 소식이며 Firebase Storage
`public_content/hpai_news/latest.json`(누구나 읽기·관리자만 쓰기)에 있다. 이 스크립트는 같은 파일에 서비스 계정(Admin SDK)으로
소식 1건을 추가한다(`FIREBASE_SERVICE_ACCOUNT_JSON` — 자동 문자 발송 작업과 같은 저장소 시크릿).

· 검색: Google 뉴스 RSS(국내판) `조류인플루엔자` 최근 3일, 가금 방역 맥락이 있는 기사만(fetch_industry_news.relevant)
· 중복 제거: ① 이미 올라간 소식(제목·원문 주소) ② 예전에 자동으로 올렸다가 지워진 기사(`auto.seen`) ③ 제목이 거의 같은 다른 매체 기사(단어 유사도)
· 하루 1건: 오늘 이미 자동 등록했으면 건너뛴다(FORCE=1이면 다시 실행)
· 요약: 원문을 읽어 Claude(ANTHROPIC_API_KEY)가 2~3문장으로 줄이고, 키가 없으면 본문 앞부분을 쓴다
· 켜고 끄기: 화면의 관리 상자에서 「자동 등록」을 끄면 `auto.enabled=false`가 저장되어 이 스크립트가 아무것도 하지 않는다

모든 시각은 KST. 실패하면 기존 소식은 손대지 않는다.
"""

from __future__ import annotations

import json
import os
import random
import re
import string
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote

import requests

from fetch_industry_news import HEADERS, ai_summary, article_text, decode_google_url, key_of, lead_summary, relevant, split_source

KST = timezone(timedelta(hours=9))
KEYWORD = "조류인플루엔자"
LOOKBACK_DAYS = 3
BUCKET = "chicken-dx.firebasestorage.app"
OBJECT = "public_content/hpai_news/latest.json"
LEGACY = Path("hpai_news/news.json")      # Firebase에 아직 한 번도 발행되지 않았을 때의 시작점(화면의 이전 로직과 같다)
SEEN_KEEP = 400
SIMILARITY = 0.55


def tokens(title: str) -> set[str]:
    t, _ = split_source(title, "")
    return {w for w in re.findall(r"[가-힣A-Za-z0-9]+", t) if len(w) >= 2}


def similar(a: str, b: str) -> bool:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return False
    return len(ta & tb) / len(ta | tb) >= SIMILARITY


def new_id() -> str:
    """화면(newHpaiNewsId)과 같은 모양: hn + 시각(36진수) + 무작위 5자."""
    digits = string.digits + string.ascii_lowercase
    n, out = int(datetime.now(timezone.utc).timestamp() * 1000), ""
    while n:
        n, r = divmod(n, 36)
        out = digits[r] + out
    return "hn" + out + "".join(random.choices(digits, k=5))


def search(keyword: str) -> list[dict]:
    url = "https://news.google.com/rss/search?q=" + quote(f"{keyword} when:{LOOKBACK_DAYS}d") + "&hl=ko&gl=KR&ceid=KR:ko"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    out = []
    for it in ET.fromstring(r.content).iter("item"):
        title, src = split_source((it.findtext("title") or "").strip(), (it.findtext("source") or "").strip())
        try:
            ts = parsedate_to_datetime(it.findtext("pubDate")).astimezone(KST)
        except Exception:
            continue
        if title and (datetime.now(KST) - ts) <= timedelta(days=LOOKBACK_DAYS) and relevant(title):
            out.append({"title": title, "source": src, "link": it.findtext("link") or "", "ts": ts})
    out.sort(key=lambda i: i["ts"], reverse=True)
    return out


def is_duplicate(cand_title: str, cand_url: str, items: list[dict], seen: set[str]) -> str | None:
    """중복이면 이유를, 아니면 None."""
    tk = "t:" + key_of(cand_title)
    if tk in seen:
        return "이전에 자동 등록(삭제됨 포함)"
    if cand_url and ("u:" + cand_url) in seen:
        return "이전에 자동 등록한 원문 주소"
    for it in items:
        if cand_url and it.get("link") == cand_url:
            return "같은 원문 주소의 소식이 이미 있음"
        if key_of(split_source(it.get("title", ""), "")[0]) == key_of(cand_title):
            return "같은 제목의 소식이 이미 있음"
    for it in items[:80]:
        if similar(cand_title, it.get("title", "")):
            return "제목이 거의 같은 소식이 이미 있음"
    return None


def load_current(bucket):
    blob = bucket.blob(OBJECT)
    if blob.exists():
        return blob, json.loads(blob.download_as_text())
    if LEGACY.exists():
        data = json.loads(LEGACY.read_text(encoding="utf-8"))
        print("Firebase 발행본이 없어 저장소의 기존 파일에서 시작합니다")
        return blob, data
    return blob, {"items": []}


def main() -> int:
    sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    if not sa_json:
        print("FIREBASE_SERVICE_ACCOUNT_JSON 시크릿이 없어 자동 등록을 건너뜁니다 — 저장소 Settings > Secrets 에서 추가하세요")
        return 0
    import firebase_admin
    from firebase_admin import credentials, storage
    firebase_admin.initialize_app(credentials.Certificate(json.loads(sa_json)), {"storageBucket": BUCKET})
    bucket = storage.bucket()

    blob, data = load_current(bucket)
    items = data.get("items") if isinstance(data.get("items"), list) else []
    auto = dict(data.get("auto") or {})
    today = datetime.now(KST).strftime("%Y-%m-%d")
    keyword = auto.get("keyword") or KEYWORD

    if auto.get("enabled") is False:
        print("자동 등록이 꺼져 있어 건너뜁니다(화면의 관리 상자에서 켤 수 있습니다)")
        return 0
    if auto.get("lastPostDate") == today and os.environ.get("FORCE") != "1":
        print("오늘은 이미 자동 등록했습니다:", auto.get("lastTitle"))
        return 0

    cands = search(keyword)
    print(f"'{keyword}' 최근 {LOOKBACK_DAYS}일 후보 {len(cands)}건")
    seen = set(auto.get("seen") or [])
    posted = None
    for c in cands:
        reason = is_duplicate(c["title"], "", items, seen)
        if reason:
            print(f"  건너뜀({reason}): {c['title'][:40]}")
            continue
        url, text = "", ""
        try:
            url = decode_google_url(c["link"]) or ""
            text = article_text(url) if url else ""
        except Exception as exc:
            print(f"  원문 처리 실패({c['title'][:30]}): {type(exc).__name__}: {str(exc)[:80]}")
        reason = is_duplicate(c["title"], url, items, seen)         # 원문 주소까지 알게 된 뒤 한 번 더
        if reason:
            print(f"  건너뜀({reason}): {c['title'][:40]}")
            continue
        summary = ""
        if len(text) >= 150:
            key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
            try:
                summary = (ai_summary(c["title"], text, key) if key else None) or lead_summary(text, title=c["title"])
            except Exception as exc:
                print(f"  요약 실패: {type(exc).__name__}: {str(exc)[:80]}")
                summary = lead_summary(text, title=c["title"])
        body = (summary + "\n\n" if summary else "") + f"출처: {c['source'] or '언론사'} · {c['ts'].strftime('%Y-%m-%d')}"
        posted = {
            "id": new_id(), "title": c["title"] + (f" - {c['source']}" if c["source"] else ""),
            "text": body, "link": url or c["link"], "images": [],
            "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"), "auto": True,
        }
        seen.update({"t:" + key_of(c["title"]), *(["u:" + url] if url else [])})
        break

    if not posted:
        print("올릴 새 기사가 없습니다(모두 중복이거나 후보 없음)")
        auto.update({"lastRun": today, "lastStatus": "새 기사 없음"})
        data["auto"] = auto
        data["items"] = items
        blob.upload_from_string(json.dumps(data, ensure_ascii=False, indent=1), content_type="application/json")
        return 0

    auto.update({"enabled": True, "keyword": keyword, "lastRun": today, "lastPostDate": today, "lastTitle": posted["title"],
                 "lastStatus": "등록 완료", "seen": sorted(seen)[-SEEN_KEEP:]})
    data["items"] = [posted] + items
    data["auto"] = auto
    data["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M") + " UTC"
    data.setdefault("by", "자동 등록")
    blob.upload_from_string(json.dumps(data, ensure_ascii=False, indent=1), content_type="application/json")
    print("등록:", posted["title"])
    print("원문:", posted["link"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
