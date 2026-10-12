#!/usr/bin/env python3
"""날씨 뉴스 수집 — 날씨예측 탭 「오늘의 날씨 뉴스」 카드용.

오늘 날씨·기상 특보(폭염·한파·호우·태풍·대설·강풍)·황사·이상기후·농업/축산 기상 키워드로 Google 뉴스 RSS(한국어·국내판)를
검색해 `weather_news/latest.json` 에 쌓는다. 날씨 기사는 금방 낡으므로 최근 3일치만 유지하고 하루 여러 번 갱신한다.
원문 주소 풀기·본문 추출·앞부분 요약은 양계 업계 소식 수집(fetch_industry_news.py)의 함수를 그대로 쓰고,
요약문은 Claude(ANTHROPIC_API_KEY, 없으면 본문 앞부분)로 만든다 — 기사에 없는 내용은 덧붙이지 않는다. 모든 시각은 KST.
검색 하나가 실패해도 나머지로 갱신하고, 전부 실패하면 이전 파일을 그대로 둔다.
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote

import requests

# 같은 scripts/ 폴더의 양계 업계 소식 수집 모듈 — 원문 주소·본문 추출·앞부분 요약을 재사용한다
import fetch_industry_news as fin

KST = timezone(timedelta(hours=9))
OUT_PATH = Path("weather_news/latest.json")
KEEP_DAYS = 3
MAX_ITEMS = 70
MAX_NEW_SUMMARIES = 40
HEADERS = fin.HEADERS

# (묶음 이름, 검색어 목록) — 묶음은 화면의 필터 칩이 된다
GROUPS = [
    ("오늘 날씨", ["오늘 날씨", "기상청 오늘 날씨 예보", "내일 날씨 전국"]),
    ("폭염·한파", ["폭염 특보", "폭염 가축 폐사", "한파 특보", "한파 한파주의보 가축"]),
    ("호우·태풍", ["호우 특보", "태풍 북상", "장마 집중호우 피해"]),
    ("눈·바람·먼지", ["대설 특보", "강풍 특보", "황사 미세먼지 예보"]),
    ("농업·축산 기상", ["농업 기상 정보", "축산농가 폭염 한파 대책", "이상기후 농가 피해"]),
    ("기상 전망", ["기상청 중기 예보 기온 전망", "기상청 1개월 전망", "이상기온 전망"]),
]
TAG_WORDS = {
    "오늘 날씨": ["오늘 날씨", "내일 날씨", "날씨", "예보", "기온", "일교차", "비 소식"],
    "폭염·한파": ["폭염", "무더위", "열대야", "한파", "추위", "영하", "강추위", "꽃샘추위"],
    "호우·태풍": ["호우", "태풍", "장마", "폭우", "집중호우", "침수", "물폭탄"],
    "눈·바람·먼지": ["대설", "폭설", "강풍", "황사", "미세먼지", "안개", "서리", "우박"],
    "농업·축산 기상": ["농업", "축산", "농가", "가축", "양계", "비닐하우스", "작물", "과수"],
    "기상 전망": ["전망", "중기예보", "1개월", "이상기온", "이상기후", "엘니뇨", "라니냐"],
}
WEATHER = re.compile(r"날씨|기상|폭염|무더위|열대야|한파|추위|영하|태풍|호우|폭우|장마|대설|폭설|강풍|황사|미세먼지|이상기후|이상기온|기온|서리|우박|가뭄|특보|예보|일교차|안개")
# 날씨 말고 다른 이야기(주가·부동산·연예·스포츠 광고성)가 제목의 중심인 기사는 거른다 — 재난 날씨 단어가 함께 있으면 남긴다
NOT_WEATHER = re.compile(r"베트남|태국|필리핀|인도네시아|Vietnam|코스피|코스닥|증시|주가|분양|청약|부동산|아파트|연예|드라마|예능|야구|축구|골프|이벤트|프로모션|쿠폰|할인|출시")
DISASTER = re.compile(r"폭염|한파|태풍|호우|폭우|대설|폭설|강풍|황사|특보|피해|경보")


# 태그 우선순위 — 구체적인 분류가 앞(카드 색·첫 배지가 「오늘 날씨」 하나로 쏠리지 않게)
TAG_ORDER = ["농업·축산 기상", "폭염·한파", "호우·태풍", "눈·바람·먼지", "기상 전망", "오늘 날씨"]
# 분류별 최대 보관 건수 — 「오늘 날씨」 기사는 비슷한 것이 수십 건씩 나와 다른 분류를 밀어내므로 상한을 둔다(기사는 첫 태그 기준으로 센다)
TAG_CAP = {"농업·축산 기상": 16, "폭염·한파": 14, "호우·태풍": 14, "눈·바람·먼지": 10, "기상 전망": 10, "오늘 날씨": 16}


def order_tags(tags: list[str]) -> list[str]:
    return sorted(dict.fromkeys(tags), key=lambda t: TAG_ORDER.index(t) if t in TAG_ORDER else 99)


def cap_items(items: list[dict]) -> list[dict]:
    used: dict[str, int] = {}
    out = []
    for it in items:                                    # 최신순으로 들어오므로 분류마다 최신 기사부터 남는다
        it["tags"] = order_tags(it.get("tags") or [])
        k = it["tags"][0] if it["tags"] else ""
        if used.get(k, 0) >= TAG_CAP.get(k, 10):
            continue
        used[k] = used.get(k, 0) + 1
        out.append(it)
    return out[:MAX_ITEMS]


SKIP_SOURCES = re.compile(r"Vietnam\.vn|VnExpress|Thanh Nien", re.I)     # 외국 지역 날씨를 다루는 매체


def relevant(title: str, source: str = "") -> bool:
    if source and SKIP_SOURCES.search(source):
        return False
    if not WEATHER.search(title):
        return False
    if NOT_WEATHER.search(title) and not DISASTER.search(title):
        return False
    return True


def tags_for(title: str) -> list[str]:
    return [g for g, words in TAG_WORDS.items() if any(w in title for w in words)]


def search(q: str) -> list[dict]:
    url = "https://news.google.com/rss/search?q=" + quote(q + " when:1d") + "&hl=ko&gl=KR&ceid=KR:ko"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    items = []
    for it in ET.fromstring(r.content).iter("item"):
        raw = (it.findtext("title") or "").strip()
        src = (it.findtext("source") or "").strip()
        title, src = fin.split_source(raw, src)
        try:
            ts = parsedate_to_datetime(it.findtext("pubDate")).astimezone(KST)
        except Exception:
            continue
        if title and relevant(title, src):
            items.append({"title": title, "source": src, "link": it.findtext("link") or "", "ts": ts.strftime("%Y-%m-%d %H:%M")})
    return items


def ai_summary(title: str, text: str, api_key: str) -> str | None:
    prompt = ("다음은 날씨·기상 관련 국내 뉴스 기사입니다. 한국어로 2~3문장, 150자 안팎으로 요약하세요.\n"
              "- 지역·기간·기온·강수량·특보 같은 핵심 사실 위주로, 기사에 없는 내용은 절대 덧붙이지 마세요.\n"
              "- 광고·기자 소개·관련기사 문구는 빼세요. 요약문만 출력하세요(머리말·따옴표·번호 없이).\n\n"
              f"제목: {title}\n\n본문:\n{text[:5000]}")
    resp = requests.post(fin.ANTHROPIC_URL, headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                         json={"model": fin.SUMMARY_MODEL, "max_tokens": 400, "messages": [{"role": "user", "content": prompt}]}, timeout=60)
    if not resp.ok:
        print(f"  Anthropic 응답 {resp.status_code}: {resp.text[:160]}")
        return None
    s = "".join(b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text").strip()
    return s if 20 <= len(s) <= 600 else None


def enrich(item: dict, api_key: str | None) -> dict:
    """원문 주소(url)와 요약(summary)을 채운다. 실패한 단계는 비워 두고 다음 실행에서 다시 시도한다."""
    out = {}
    try:
        url = item.get("url") or fin.decode_google_url(item.get("link", ""))
        if url:
            out["url"] = url
        text = fin.article_text(url) if url else ""
        if len(text) >= 150:
            s = ai_summary(item["title"], text, api_key) if api_key else None
            if s:
                out["summary"], out["summary_ai"] = s, True
            else:
                out["summary"], out["summary_ai"] = fin.lead_summary(text, title=item["title"]), False
        elif url:
            out["summary"], out["summary_ai"] = "", False
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
                    k = fin.key_of(it["title"])
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
    merged = {fin.key_of(i["title"]): i for i in (prev.get("items") or []) if i.get("ts", "") >= cutoff and relevant(i.get("title", ""), i.get("source", ""))}
    merged.update({k: {**merged.get(k, {}), **v} for k, v in found.items()})        # 이미 채운 요약·원문 주소는 새 검색 결과로 덮지 않는다
    items = cap_items(sorted(merged.values(), key=lambda i: i["ts"], reverse=True))
    todo = [i for i in items if "summary" not in i or not i.get("url")][:MAX_NEW_SUMMARIES]
    if todo:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip() or None
        print(f"원문·요약 처리 {len(todo)}건 ({'Claude 요약' if api_key else '본문 앞부분 요약(ANTHROPIC_API_KEY 없음)'})")
        with ThreadPoolExecutor(max_workers=4) as ex:
            for it, res in zip(todo, ex.map(lambda x: enrich(x, api_key), todo)):
                it.update(res)
        print(f"  요약 {sum(1 for i in todo if i.get('summary'))}건 · 원문주소 {sum(1 for i in todo if i.get('url'))}건")
    out = {"updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"), "groups": [g for g, _ in GROUPS], "items": items}

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
