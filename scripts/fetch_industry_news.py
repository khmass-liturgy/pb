#!/usr/bin/env python3
"""양계 업계 소식 수집 — 유료서비스 「업계관련 소식」 카드용.

계란·조류인플루엔자·AI(고병원성)·육계·방역·양계 질병 등 양계 키워드로 Google 뉴스 RSS(한국어·국내판)를 검색해
`industry_news/latest.json` 에 쌓는다. 매일 한 번 돌고, 최근 14일치를 유지한다(이전 기사 + 새 기사 병합, 제목 중복 제거).

'AI'는 인공지능 기사와 섞이므로 제목에 가금·방역 맥락이 있을 때만 받는다. 모든 시각은 KST.
부분 실패는 이전 JSON을 지우지 않는다(키워드 하나 실패해도 나머지로 갱신).
"""

from __future__ import annotations

import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote

import requests

KST = timezone(timedelta(hours=9))
OUT_PATH = Path("industry_news/latest.json")
KEEP_DAYS = 14
MAX_ITEMS = 200
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}

# (묶음 이름, 검색어 목록) — 묶음은 화면의 필터 칩이 된다
GROUPS = [
    ("계란", ["계란 가격", "계란 산란계 수급", "달걀 가격", "계란 유통"]),
    ("조류인플루엔자·AI", ["조류인플루엔자", "고병원성 AI 가금농장", "AI 확진 살처분", "고병원성 AI 철새"]),
    ("육계", ["육계 시세", "닭고기 가격", "육계 농가", "삼계 닭고기 수급"]),
    ("방역", ["가금농장 방역", "양계 방역", "가축질병 닭 오리 방역"]),
    ("양계 질병", ["뉴캐슬병", "가금티푸스", "전염성기관지염 닭", "살모넬라 닭", "닭 질병 사료 양계"]),
    ("양계 산업", ["양계농가", "산란계 농가", "양계협회", "축산신문 양계"]),
]
TAG_WORDS = {
    "계란": ["계란", "달걀", "산란계", "난가", "알 "],
    "조류인플루엔자·AI": ["조류인플루엔자", "고병원성", "AI", "철새", "살처분"],
    "육계": ["육계", "닭고기", "삼계", "닭 ", "병아리"],
    "방역": ["방역", "소독", "이동제한", "행정명령"],
    "양계 질병": ["뉴캐슬", "티푸스", "기관지염", "살모넬라", "마이코플라스마", "대장균", "질병", "감염"],
    "양계 산업": ["양계", "농가", "가금", "종계", "오리", "메추리"],
}
STRONG = re.compile(r"계란|달걀|조류인플루엔자|육계|산란계|양계|가금|종계|닭고기|병아리|뉴캐슬|가금티푸스|삼계")
WEAK_AI = re.compile(r"\bAI\b|고병원성")
AI_CONTEXT = re.compile(r"고병원성|조류|확진|살처분|철새|가금|농장|방역|닭|오리|계란|산란|도래지|이동제한|행정명령")
NOT_AI_TECH = re.compile(r"인공지능|생성형|챗GPT|ChatGPT|딥러닝|반도체|로봇|자율주행|GPU|LLM")
WEAK_OTHER = re.compile(r"닭|오리|방역|가축질병|살처분|살모넬라")
POULTRY_CTX = re.compile(r"닭|오리|가금|양계|계란|조류|산란|육계|AI|농장|철새")


# 치킨 프랜차이즈 홍보·금융·요리 기사는 업계 소식이 아니다(산업 키워드가 함께 있으면 남긴다)
NOT_INDUSTRY = re.compile(r"1호점|가맹점|신메뉴|출시|프로모션|은행|전세금|맛집|레시피|이벤트|쿠폰|할인 행사")
INDUSTRY_CORE = re.compile(r"산란계|육계|조류인플루엔자|고병원성|양계|가금|종계|살처분|방역|수급")


def relevant(title: str) -> bool:
    if NOT_INDUSTRY.search(title) and not INDUSTRY_CORE.search(title):
        return False
    if NOT_AI_TECH.search(title) and not STRONG.search(title):
        return False
    if STRONG.search(title):
        return True
    if WEAK_AI.search(title):
        return bool(AI_CONTEXT.search(title))
    if WEAK_OTHER.search(title):
        return bool(POULTRY_CTX.search(title))
    return False


def tags_for(title: str) -> list[str]:
    out = []
    for g, words in TAG_WORDS.items():
        if any(w in title for w in words):
            out.append(g)
    return out


def split_source(title: str, source: str) -> tuple[str, str]:
    """'기사 제목 - 언론사' 에서 언론사를 떼어 낸다."""
    m = re.match(r"^(.*)\s[-–]\s([^-–]+)$", title)
    if m and (not source or m.group(2).strip() == source):
        return m.group(1).strip(), (source or m.group(2).strip())
    return title.strip(), source


def search(q: str) -> list[dict]:
    url = "https://news.google.com/rss/search?q=" + quote(q + " when:2d") + "&hl=ko&gl=KR&ceid=KR:ko"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    items = []
    for it in ET.fromstring(r.content).iter("item"):
        raw = (it.findtext("title") or "").strip()
        src = (it.findtext("source") or "").strip()
        title, src = split_source(raw, src)
        try:
            ts = parsedate_to_datetime(it.findtext("pubDate")).astimezone(KST)
        except Exception:
            continue
        if title and relevant(title):
            items.append({"title": title, "source": src, "link": it.findtext("link") or "", "ts": ts.strftime("%Y-%m-%d %H:%M")})
    return items


def key_of(title: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", title)[:28]


# ── 기사 원문 주소 찾기 + 본문 요약 ───────────────────────────────────────────────
# Google 뉴스 RSS 링크는 언론사로 넘겨 주는 중간 주소라 원문 주소를 따로 풀어야 한다(batchexecute 호출).
# 원문 본문은 trafilatura 로 뽑고, 요약은 Claude(ANTHROPIC_API_KEY)로 만든다. 키가 없거나 호출이 실패하면
# 본문 앞부분 2문장으로 대신한다(summary_ai=False). 요약은 기사 내용을 짧게 줄인 것이며 원문은 링크로 안내한다.
SUMMARY_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MAX_NEW_SUMMARIES = 120      # 한 번에 처리할 기사 수(처음엔 밀린 기사를 나눠서 채운다)


def decode_google_url(link: str) -> str | None:
    m = re.search(r"/articles/([^?/]+)", link or "")
    if not m:
        return None
    gid = m.group(1)
    page = requests.get(f"https://news.google.com/rss/articles/{gid}?hl=ko&gl=KR&ceid=KR:ko", headers=HEADERS, timeout=20)
    sg = re.search(r'data-n-a-sg="([^"]+)"', page.text)
    ts = re.search(r'data-n-a-ts="([^"]+)"', page.text)
    if not sg or not ts:
        return None
    inner = json.dumps(["garturlreq", [["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1, None, None, None, None, None, 0, 1],
                                       "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0], gid, int(ts.group(1)), sg.group(1)],
                       separators=(",", ":"))
    freq = json.dumps([[["Fbv4je", inner, None, "generic"]]], separators=(",", ":"))
    resp = requests.post("https://news.google.com/_/DotsSplashUi/data/batchexecute",
                         headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
                         data="f.req=" + quote(freq), timeout=20)
    arr = json.loads(resp.text.split("\n\n", 1)[1])[:-2]
    url = json.loads(arr[0][2])[1]
    return url if isinstance(url, str) and url.startswith("http") else None


def article_text(url: str) -> str:
    import trafilatura
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    if not r.encoding or r.encoding.lower() == "iso-8859-1":
        r.encoding = r.apparent_encoding
    return (trafilatura.extract(r.text, include_comments=False, include_tables=False) or "").strip()


def lead_summary(text: str, limit: int = 170, title: str = "") -> str:
    """본문 앞부분 문장으로 대신하는 요약(제목 반복·기자명·출처 머리글 제거)."""
    if title and text.lstrip().startswith(title[:12]):
        text = text.lstrip()[len(title):] if text.lstrip().startswith(title) else text
    t = re.sub(r"^\s*[\(\[【][^\)\]】]{0,30}[\)\]】]\s*", "", text.replace("\n", " "))
    t = re.sub(r"^[^.。]{0,40}기자\s*[=:]?\s*", "", t)
    sents = re.split(r"(?<=[.。다요])\s+", t)
    out = ""
    for s in sents:
        if len(out) + len(s) > limit and out:
            break
        out += (" " if out else "") + s.strip()
        if len(out) >= 90:
            break
    return out[:limit + 20].strip()


def ai_summary(title: str, text: str, api_key: str) -> str | None:
    prompt = ("다음은 양계(닭·계란·오리) 관련 국내 뉴스 기사입니다. 한국어로 2~3문장, 150자 안팎으로 요약하세요.\n"
              "- 누가·무엇을·언제·수치 같은 핵심 사실 위주로, 기사에 없는 내용은 절대 덧붙이지 마세요.\n"
              "- 광고·기자 소개·관련기사 문구는 빼세요. 요약문만 출력하세요(머리말·따옴표·번호 없이).\n\n"
              f"제목: {title}\n\n본문:\n{text[:5000]}")
    resp = requests.post(ANTHROPIC_URL, headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                         json={"model": SUMMARY_MODEL, "max_tokens": 400, "messages": [{"role": "user", "content": prompt}]}, timeout=60)
    if not resp.ok:
        print(f"  Anthropic 응답 {resp.status_code}: {resp.text[:160]}")
        return None
    s = "".join(b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text").strip()
    return s if 20 <= len(s) <= 600 else None


def enrich(item: dict, api_key: str | None) -> dict:
    """원문 주소(url)와 요약(summary)을 채운다. 실패한 단계는 비워 두고 다음 실행에서 다시 시도한다."""
    out = {}
    try:
        url = item.get("url") or decode_google_url(item.get("link", ""))
        if url:
            out["url"] = url
        text = article_text(url) if url else ""
        if len(text) >= 150:
            s = ai_summary(item["title"], text, api_key) if api_key else None
            if s:
                out["summary"], out["summary_ai"] = s, True
            else:
                out["summary"], out["summary_ai"] = lead_summary(text, title=item["title"]), False
        elif url:
            out["summary"], out["summary_ai"] = "", False      # 본문을 못 읽은 기사(요약 없음) — 다시 시도하지 않는다
    except Exception as exc:
        print(f"  요약 실패({item.get('title', '')[:24]}): {type(exc).__name__}: {str(exc)[:80]}")
    return out


def main() -> int:
    prev = {}
    if OUT_PATH.exists():
        try:
            prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
    found: dict[str, dict] = {}
    ok = fail = 0
    for group, queries in GROUPS:
        for q in queries:
            try:
                for it in search(q):
                    k = key_of(it["title"])
                    cur = found.get(k)
                    if cur is None:
                        it["tags"] = tags_for(it["title"]) or [group]
                        if group not in it["tags"]:
                            it["tags"].append(group)
                        found[k] = it
                    elif group not in cur["tags"]:
                        cur["tags"].append(group)
                ok += 1
            except Exception as exc:
                fail += 1
                print(f"::warning::검색 실패({q}): {type(exc).__name__}: {exc}")
    print(f"검색 {ok}건 성공 / {fail}건 실패 · 새로 찾은 기사 {len(found)}건")
    if ok == 0:
        print("모든 검색이 실패해 이전 값을 유지합니다")
        return 1

    cutoff = (datetime.now(KST) - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d %H:%M")
    merged = {key_of(i["title"]): i for i in (prev.get("items") or []) if i.get("ts", "") >= cutoff and relevant(i.get("title", ""))}   # 필터를 다듬은 뒤에도 옛 기사에 다시 적용
    merged.update(found)
    items = sorted(merged.values(), key=lambda i: i["ts"], reverse=True)[:MAX_ITEMS]
    # 원문 주소·요약이 아직 없는 기사(새 기사 + 이전 실행에서 못 채운 기사)를 최신순으로 채운다
    todo = [i for i in items if "summary" not in i or not i.get("url")][:MAX_NEW_SUMMARIES]
    if todo:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip() or None
        print(f"원문·요약 처리 {len(todo)}건 ({'Claude 요약' if api_key else '본문 앞부분 요약(ANTHROPIC_API_KEY 없음)'})")
        with ThreadPoolExecutor(max_workers=4) as ex:
            for it, res in zip(todo, ex.map(lambda x: enrich(x, api_key), todo)):
                it.update(res)
        done = sum(1 for i in todo if i.get("summary"))
        print(f"  요약 {done}건 · 원문주소 {sum(1 for i in todo if i.get('url'))}건")
    out = {"updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"), "groups": [g for g, _ in GROUPS],
           "keywords": sorted({q for _, qs in GROUPS for q in qs}), "items": items}

    def core(d):
        return {k: v for k, v in d.items() if k != "updated"}
    if prev and core(prev) == core(out):
        print("변경 없음")
        return 0
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"저장: 기사 {len(items)}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
