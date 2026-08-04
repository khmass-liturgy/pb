#!/usr/bin/env python3
"""
브리핑 탭 뉴스 통합 수집 (서버측) → news/briefing.json

왜 서버에서 모으는가:
  브라우저에서 각 언론사를 직접 읽으려면 CORS 때문에 무료 프록시를 거쳐야 하고,
  프록시는 분당/월 호출 한도가 있어 앱을 열 때마다 한도가 차감된다.
  서버는 CORS 제약이 없으므로 직접 읽고, 대시보드는 결과 JSON 1개만 받는다.
  → 뉴스 4종을 봐도 브라우저 네트워크 호출은 1회.

소스를 추가/변경하려면 아래 SOURCES 리스트만 고치면 된다.
(기존 scripts/fetch_news.py = 뉴스 탭용 news/news.json 과는 별개 파일)
"""

import sys, re, json, time, html as htmlmod
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import quote
from email.utils import parsedate_to_datetime

import requests

KST = timezone(timedelta(hours=9))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

PER_SOURCE = 5   # 소스별 노출 건수


# ── 공통 유틸 ────────────────────────────────────────────────────────────────
def clean_text(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", htmlmod.unescape(s)).strip()


def kst_label(dt):
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(KST).strftime("%m.%d %H:%M")


def rfc822(s):
    try:
        return parsedate_to_datetime(s.strip())
    except Exception:
        return None


# ── 파서: RSS 2.0 ────────────────────────────────────────────────────────────
def parse_rss(xml, limit, strip_source=False):
    items, seen = [], set()
    for m in re.finditer(r"<item>([\s\S]*?)</item>", xml):
        body = m.group(1)

        def pick(tag):
            mm = re.search(r"<%s>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</%s>" % (tag, tag), body)
            return mm.group(1).strip() if mm else ""

        title, link = clean_text(pick("title")), pick("link")
        if not title or len(title) < 6 or not link or link in seen:
            continue

        # 구글 뉴스는 제목 끝에 " - 언론사"가 붙음 → 출처로 분리
        source = ""
        if strip_source and " - " in title:
            head, _, tail = title.rpartition(" - ")
            if head and len(tail) <= 20:
                title, source = head.strip(), tail.strip()

        seen.add(link)
        items.append({"title": title, "url": link,
                      "date": kst_label(rfc822(pick("pubDate"))), "source": source})
        if len(items) >= limit:
            break
    return items


# ── 파서: 축산신문 (mediaOn CMS) ──────────────────────────────────────────────
def parse_chuksan(html):
    items, seen = [], set()
    for m in re.finditer(r'href="([^"]*article\.html\?no=(\d+)[^"]*)"[^>]*>([\s\S]{0,300}?)</a>', html):
        href, aid, inner = m.group(1), m.group(2), m.group(3)
        if aid in seen:
            continue
        title = clean_text(inner).split("[축산신문")[0].strip()
        if len(title) < 8:
            continue
        url = href if href.startswith("http") else \
            "https://www.chuksannews.co.kr" + (href if href.startswith("/") else "/news/" + href)
        seen.add(aid)
        d = re.search(r"\d{4}[-.]\d{2}[-.]\d{2}", html[m.end():m.end() + 400])
        items.append({"title": title, "url": url, "date": d.group(0) if d else "", "source": ""})
        if len(items) >= PER_SOURCE:
            break
    return items


# ── 파서: 한돈뉴스 (ndsoft CMS) ───────────────────────────────────────────────
def parse_handon(html):
    items, seen = [], set()
    for m in re.finditer(r'href="([^"]*articleView\.html\?idxno=(\d+)[^"]*)"[^>]*>([\s\S]{0,300}?)</a>', html):
        href, aid, inner = m.group(1), m.group(2), m.group(3)
        if aid in seen:
            continue
        title = clean_text(inner)
        if len(title) < 8:
            continue
        url = href if href.startswith("http") else \
            "https://www.pignpork.com" + (href if href.startswith("/") else "/news/" + href)
        seen.add(aid)
        d = re.search(r"\d{2}\.\d{2}\s?\d{2}:\d{2}|\d{4}[-.]\d{2}[-.]\d{2}", html[m.end():m.end() + 400])
        items.append({"title": title, "url": url, "date": d.group(0) if d else "", "source": ""})
        if len(items) >= PER_SOURCE:
            break
    return items


def gnews(q):
    return "https://news.google.com/rss/search?q=" + quote(q) + "&hl=ko&gl=KR&ceid=KR:ko&when=14d"


# ── 소스 정의 (여기만 고치면 소스 추가/변경 완료) ─────────────────────────────
SOURCES = [
    {"id": "chuksan", "name": "축산신문", "icon": "📰", "color": "#C62828",
     "home": "https://www.chuksannews.co.kr/news/section_list_all.html?sec_no=2",
     "kind": "html", "parser": parse_chuksan,
     "urls": ["https://www.chuksannews.co.kr/news/section_list_all.html?sec_no=2"]},

    {"id": "handon", "name": "한돈뉴스", "icon": "🐷", "color": "#AD1457",
     "home": "https://www.pignpork.com/news/articleList.html?sc_section_code=S1N1&view_type=sm",
     "kind": "html", "parser": parse_handon,
     "urls": ["https://www.pignpork.com/news/articleList.html?sc_section_code=S1N1&view_type=sm"]},

    # 경제뉴스: 한국경제(광고 과다) → 연합인포맥스(증권방송 편성표 위주,
    # 실제 기사가 아님) → 아시아경제(개방형 경제 전문 언론사, 공식 RSS 제공)
    {"id": "econ", "name": "아시아경제", "icon": "💹", "color": "#0047A0",
     "home": "https://www.asiae.co.kr/list/economy",
     "kind": "rss", "urls": ["https://view.asiae.co.kr/rss/economy.htm"]},

    # 농식품부 보도자료 공식 RSS. mafra.go.kr 은 검색엔진 크롤러를 막아두지만
    # (robots.txt), RSS는 애초에 기계가 읽도록 만든 공개 피드이므로
    # requests로 직접 요청하면 정상 수집된다 — 구글 뉴스 검색 대체.
    {"id": "policy", "name": "농식품부 축산정책", "icon": "🏛️", "color": "#1B5E20",
     "home": "https://www.mafra.go.kr/home/5109/subview.do",
     "kind": "rss",
     "urls": ["https://www.mafra.go.kr/bbs/home/792/rssList.do?row=50"]},
]


def fetch_source(src, session):
    """소스 하나 수집 → items (URL 여러 개면 합쳐 중복 제거)"""
    merged, seen = [], set()
    base = src.get("home", "")
    origin = ""
    if base.startswith("http"):
        parts = base.split("/", 3)
        origin = "/".join(parts[:3])  # https://도메인

    for url in src["urls"]:
        try:
            r = session.get(url, timeout=20)
            if r.status_code != 200:
                raise Exception("HTTP %d" % r.status_code)
            r.encoding = r.apparent_encoding or "utf-8"
            got = (parse_rss(r.text, PER_SOURCE * 2, src.get("strip_source", False))
                   if src["kind"] == "rss" else src["parser"](r.text))
            for it in got:
                # 정부 사이트 등 일부 RSS는 <link>가 절대경로가 아닌 경우가 있어 보정
                if origin and it.get("url") and not it["url"].startswith("http"):
                    it["url"] = origin + ("" if it["url"].startswith("/") else "/") + it["url"]
                key = it["title"][:40]
                if key in seen:
                    continue
                seen.add(key)
                merged.append(it)
        except Exception as e:
            print("      ⚠️ %s… → %s" % (url[:55], e))
        time.sleep(0.3)
    return merged[:PER_SOURCE]


def main():
    now = datetime.now(KST)
    session = requests.Session()
    session.headers.update(HEADERS)

    print("📰 브리핑 뉴스 수집 시작 (%s)\n" % now.strftime("%Y-%m-%d %H:%M KST"))

    out_path = Path("news/briefing.json")
    old = {}
    if out_path.exists():
        try:
            old = json.loads(out_path.read_text(encoding="utf-8")).get("sources", {})
        except Exception:
            pass

    sources, failed = {}, []
    for src in SOURCES:
        print("  ▶ %s %s" % (src["icon"], src["name"]))
        items = fetch_source(src, session)

        if len(items) >= 2:
            sources[src["id"]] = {"name": src["name"], "icon": src["icon"],
                                  "color": src["color"], "home": src["home"],
                                  "items": items, "stale": False}
            for it in items[:3]:
                print("      · [%s] %s" % (it["date"], it["title"][:44]))
            print("      ✅ %d건" % len(items))
        else:
            failed.append(src["id"])
            prev = old.get(src["id"])
            if prev and prev.get("items"):
                prev["stale"] = True
                sources[src["id"]] = prev
                print("      ⚡ 실패 → 이전 값 유지 (%d건)" % len(prev["items"]))
            else:
                sources[src["id"]] = {"name": src["name"], "icon": src["icon"],
                                      "color": src["color"], "home": src["home"],
                                      "items": [], "stale": True}
                print("      ❌ 실패 · 이전 값 없음")

    if all(not s.get("items") for s in sources.values()):
        print("\n❌ 모든 소스 실패 — 파일을 덮어쓰지 않습니다.")
        sys.exit(1)

    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps({
        "updated": now.strftime("%Y-%m-%d %H:%M KST"),
        "updatedTs": int(now.timestamp()),
        "ok": len(SOURCES) - len(failed),
        "total": len(SOURCES),
        "order": [s["id"] for s in SOURCES],
        "sources": sources,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n✅ news/briefing.json 저장 — 성공 %d/%d" % (len(SOURCES) - len(failed), len(SOURCES)))


if __name__ == "__main__":
    main()
