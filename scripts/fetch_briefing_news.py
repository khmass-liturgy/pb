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

# ── 프록시 경유 폴백 ──────────────────────────────────────────────────────────
# 일부 정부(.go.kr) 사이트는 GitHub Actions 러너의 클라우드 IP 대역 자체를
# 막아둬서 응답이 아예 없이(ConnectTimeout) 연결이 끊긴다. WAF가 요청 내용을
# 걸러내는 게 아니라 IP 단위 차단이라 헤더를 바꿔도 소용없다 — 다른 IP를 거쳐
# 그대로 중계하는 공개 프록시로 우회한다. (브라우저 쪽 CORS_PROXIES와 동일한 목록)
PROXY_TEMPLATES = [
    lambda u: "https://api.codetabs.com/v1/proxy/?quest=" + quote(u, safe=""),
    lambda u: "https://api.allorigins.win/raw?url=" + quote(u, safe=""),
    lambda u: "https://corsproxy.io/?url=" + quote(u, safe=""),
]

NETWORK_ERRORS = (
    requests.exceptions.ConnectTimeout,
    requests.exceptions.ConnectionError,
    requests.exceptions.ReadTimeout,
)


def get_with_proxy_fallback(session, url, timeout=20, headers=None):
    """
    직접 연결이 네트워크 단계에서 막히면(타임아웃·연결거부) 공개 프록시를
    순서대로 거쳐 원문을 그대로 중계받는다. 프록시는 내용을 가공하지 않고
    그대로 전달하므로 RSS XML 파싱 로직은 그대로 쓸 수 있다.

    headers: 소스별 헤더 덮어쓰기. 일부 사이트는 특정 UA만 골라 차단하므로
             (SOURCES의 "headers" 참고) 그 소스에서만 다른 값을 쓴다.
    """
    try:
        return session.get(url, timeout=timeout, headers=headers)
    except NETWORK_ERRORS as e:
        print("        ⚠️ 직접 연결 실패(%s) → 프록시 경유 재시도" % type(e).__name__)

    last_err = None
    for i, tmpl in enumerate(PROXY_TEMPLATES, 1):
        try:
            r = session.get(tmpl(url), timeout=timeout + 10, headers=headers)
            if r.status_code == 200 and len(r.content) > 200:
                print("        ✅ 프록시 %d 성공 (%dbytes)" % (i, len(r.content)))
                return r
            print("        프록시 %d 실패: HTTP %d / %dbytes" % (i, r.status_code, len(r.content)))
        except Exception as e:
            last_err = e
            print("        프록시 %d 실패: %s" % (i, e))
    raise last_err or Exception("모든 프록시 실패")

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


def parse_pubdate(s):
    s = (s or "").strip()
    try:
        return parsedate_to_datetime(s)
    except Exception:
        pass
    # 농수축산신문 등 일부 국내 RSS는 시간대 없는 "2026-08-14 16:40:56" 형식이다.
    # 발행사가 한국이므로 KST로 못박아야 kst_label()이 UTC로 오인해 9시간 밀리지 않는다.
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?", s)
    if m:
        y, mo, d, hh, mi, ss = m.groups()
        return datetime(int(y), int(mo), int(d), int(hh), int(mi), int(ss or 0), tzinfo=KST)
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
                      "date": kst_label(parse_pubdate(pick("pubDate"))), "source": source})
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


# ── 해외 양계질병 뉴스: 구글 뉴스(영문) 검색 → 제목 한글 번역 ──────────────────
# 양계 질병 전문 매체(The Poultry Site, WATT Poultry, Poultry World,
# Poultry Health Today 등)는 직접 RSS가 404/403(Cloudflare)이라 서버에서
# 신뢰할 수 없다. 실제로 확인한 결과:
#   thepoultrysite.com/rss/news → 404, poultryworld.net/rss → 404,
#   wattagnet.com/rss/articles → 403, cidrap.umn.edu/rss.xml → 200이지만
#   2019~2022년 글만 반환(사실상 죽은 피드)
# 그래서 국내 뉴스와 같은 방식으로 구글 뉴스 검색을 거쳐 받는다.
#
# 쿼리를 짧게 유지하는 것이 중요하다. site: 를 여러 개 넣거나 질병명을 OR로
# 길게 늘어놓으면 구글이 when: 연산자를 무시하고 관련도 순으로 과거 기사까지
# 섞어 준다(2015·2017·2020년 기사와 섹션 랜딩 페이지가 실제로 딸려 나왔다).
# 아래 두 쿼리는 짧게 유지해 검증했을 때 받은 항목이 전부 7일 이내였다.
#
# urls는 폴백이 아니라 병합 목록이라 첫 쿼리가 앞자리를 차지한다. 그래서
# 관련성이 가장 높은 쿼리를 앞에 두고, 구글이 간헐적으로 0건을 주는 경우를
# 대비해 두 번째 쿼리를 예비로 둔다(0건이면 두 번째 결과가 자리를 채운다).
POULTRY_DISEASE_QUERIES = [
    '"bird flu" poultry when:7d',        # 주 쿼리 — 검증 시 10/10 가금 관련, 이탈 0
    'poultry biosecurity disease when:7d',  # 예비 — 주 쿼리가 0건일 때만 사실상 노출
]
# '전체 ↗' 링크가 가리킬 사람이 볼 검색 화면
GLOBAL_NEWS_QUERY = POULTRY_DISEASE_QUERIES[0]


def gnews_en(q):
    return "https://news.google.com/rss/search?q=" + quote(q) + "&hl=en-US&gl=US&ceid=US:en"


def _translate_google(text, session):
    """구글 번역 비공식 엔드포인트(API 키 불필요). 되면 품질이 가장 낫다.

    다만 Actions 러너처럼 데이터센터 IP에서 부르면 429 "Sorry..." HTML을 돌려주며
    장시간 막히는 일이 잦다. 그 상태에서는 재시도해도 계속 429라서, 여기서는
    짧게만 재시도하고 실패로 넘겨 다음 제공자가 받게 한다.
    """
    for i in range(2):
        r = session.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "en", "tl": "ko", "dt": "t", "q": text},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            return "".join(seg[0] for seg in data[0] if seg[0]).strip() or None
        if r.status_code == 429 and i == 0:
            time.sleep(2)
            continue
        raise Exception("HTTP %d" % r.status_code)
    return None


def _translate_mymemory(text, session):
    """MyMemory 공개 API(키 불필요). 구글이 막혔을 때의 대체 경로.

    익명 호출은 하루 사용량 제한이 있고, 초과하면 200을 주면서 본문에
    "MYMEMORY WARNING: YOU USED ALL AVAILABLE FREE TRANSLATIONS" 같은 안내를
    담아 보낸다. 그 문자열을 제목으로 쓰면 안 되므로 걸러낸다.
    """
    r = session.get(
        "https://api.mymemory.translated.net/get",
        params={"q": text, "langpair": "en|ko"},
        timeout=15,
    )
    if r.status_code != 200:
        raise Exception("HTTP %d" % r.status_code)
    out = ((r.json().get("responseData") or {}).get("translatedText") or "").strip()
    if not out or "MYMEMORY WARNING" in out.upper() or "QUERY LENGTH LIMIT" in out.upper():
        return None
    return out


# 위에서부터 차례로 시도한다. 하나가 막혀도 다음 제공자가 받아 번역이 통째로
# 영어로 남는 일을 막는다.
TRANSLATORS = [("google", _translate_google), ("mymemory", _translate_mymemory)]


def translate_en_to_ko(text, session):
    """영문 제목을 한글로. 모든 제공자가 실패하면 None(호출부가 원문을 그대로 쓴다)."""
    for name, fn in TRANSLATORS:
        try:
            ko = fn(text, session)
            if ko:
                return ko
        except Exception as e:
            print("        번역 실패(%s): %s" % (name, e))
    return None


# ── 소스 정의 (여기만 고치면 소스 추가/변경 완료) ─────────────────────────────
SOURCES = [
    {"id": "chuksan", "name": "축산신문", "icon": "📰", "color": "#C62828",
     "home": "https://www.chuksannews.co.kr/news/section_list_all.html?sec_no=2",
     "kind": "html", "parser": parse_chuksan,
     "urls": ["https://www.chuksannews.co.kr/news/section_list_all.html?sec_no=2"]},

    # 농수축산신문: 농업·수산·축산을 함께 다뤄 전체기사에는 축산 외 기사가 많이 섞인다.
    # 축산 섹션(S1N2) 전용 RSS를 쓰면 이 대시보드에 맞는 기사만 들어온다.
    {"id": "aflnews", "name": "농수축산신문", "icon": "🌾", "color": "#EF6C00",
     "home": "https://www.aflnews.co.kr/news/articleList.html?sc_section_code=S1N2&view_type=sm",
     "kind": "rss", "urls": ["https://www.aflnews.co.kr/rss/S1N2.xml"]},

    {"id": "handon", "name": "한돈뉴스", "icon": "🐷", "color": "#AD1457",
     "home": "https://www.pignpork.com/news/articleList.html?sc_section_code=S1N1&view_type=sm",
     "kind": "html", "parser": parse_handon,
     "urls": ["https://www.pignpork.com/news/articleList.html?sc_section_code=S1N1&view_type=sm"]},

    # 데일리벳(수의사 전문 매체, 워드프레스) — 뉴스 중 축산과 직접 관련된
    # 3개 카테고리만: 검역/방역/위생(prevention-hygiene) · 산업(industry) ·
    # 동물복지(animalwelfare). 반려동물 임상·수의대 소식 등은 제외된다.
    #
    # 워드프레스 category_name은 쉼표가 OR라 한 번의 요청으로 세 카테고리를 받는다.
    # 숫자 ID(?cat=5,8,10)도 결과가 같지만, ID는 사이트 재구축 시 조용히 바뀔 수
    # 있어 슬러그 방식을 쓴다.
    # 주의: 기사 URL의 /news/<슬러그>/ 는 "대표" 카테고리라서 policy 등으로 보일 수
    # 있는데, 그런 기사도 위 3개 중 하나에 교차 등록된 것이라 정상이다(확인함).
    # 이 사이트 WAF는 위 공용 HEADERS의 UA("...(KHTML, like Gecko) Chrome/125.0.0.0...")를
    # 골라서 405로 막는다(재현 확인). UA만 짧은 형태로 바꾸면 정상 200이라 이 소스에만
    # 덮어쓴다 — 공용 HEADERS를 건드리면 지금 잘 되는 다른 소스에 영향이 갈 수 있다.
    {"id": "dailyvet", "name": "데일리벳", "icon": "🩺", "color": "#5E35B1",
     "home": "https://www.dailyvet.co.kr/category/news/prevention-hygiene",
     "kind": "rss", "urls": ["https://www.dailyvet.co.kr/feed/"
                             "?category_name=prevention-hygiene,industry,animalwelfare"],
     "headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 Chrome/125.0 Safari/537.36"}},

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

    # 해외 양계질병 뉴스: 구글 뉴스(영문) → 제목 한글 번역
    # id는 'global' 그대로 둔다. 화면 상태키·브라우저 캐시(notice_cache)가 이
    # 이름을 쓰고 있어, 바꾸면 배포 직후 캐시가 남은 사용자에게 빈 카드가 뜬다.
    {"id": "global", "name": "해외 양계질병", "icon": "🦠", "color": "#00695C",
     "home": "https://news.google.com/search?q=" + quote(GLOBAL_NEWS_QUERY) + "&hl=en-US&gl=US&ceid=US:en",
     "kind": "rss_en", "urls": [gnews_en(q) for q in POULTRY_DISEASE_QUERIES]},
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
            r = get_with_proxy_fallback(session, url, timeout=20, headers=src.get("headers"))
            ctype = r.headers.get("Content-Type", "")
            print("      → HTTP %d / %dbytes / %s" % (r.status_code, len(r.content), ctype))
            if r.status_code != 200:
                print("        응답 본문 앞부분: %r" % r.text[:300])
                raise Exception("HTTP %d" % r.status_code)
            r.encoding = r.apparent_encoding or "utf-8"

            # RSS인데 <item> 이 하나도 없으면 WAF 차단 페이지 등을 받았을 가능성이 큼
            if src["kind"] in ("rss", "rss_en") and "<item" not in r.text:
                print("        ⚠️ <item> 태그 없음 — RSS가 아닌 다른 응답을 받은 것으로 보임")
                print("        응답 본문 앞부분: %r" % r.text[:500])

            if src["kind"] == "rss_en":
                # 영문 제목이라 " - 매체명" 접미사를 항상 출처로 분리(strip_source)한다.
                got = parse_rss(r.text, PER_SOURCE, strip_source=True)
                for it in got:
                    it["titleEn"] = it["title"]
                    ko = translate_en_to_ko(it["title"], session)
                    if ko:
                        it["title"] = ko
                    time.sleep(0.4)  # 무료 번역 엔드포인트 과호출 방지
            else:
                got = (parse_rss(r.text, PER_SOURCE * 2, src.get("strip_source", False))
                       if src["kind"] == "rss" else src["parser"](r.text))
            print("        파싱된 항목: %d개" % len(got))

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
