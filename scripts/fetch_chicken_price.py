#!/usr/bin/env python3
"""
한국육계협회(chicken.or.kr) 육계 시세 수집 (서버측) → chicken_price/latest.json

왜 서버에서 모으는가:
  브라우저에서 chicken.or.kr을 CORS 프록시로 직접 긁는 방식을 오래 써왔는데,
  대시보드에 "저장값(2026-07-02)"만 계속 뜨는 문제가 있었다. 확인해보니
  이 사이트는 예전부터 자동화된 요청(봇 UA·클라우드 IP 등)에 403을 자주
  돌려주는 것으로 파악됐고, 브라우저 쪽에서 매번 라이브 스크래핑을 시도하다
  실패하면 조용히 코드에 박아둔 옛날 폴백 데이터로 넘어가 버리니, 사이트가
  실제로 갱신돼도 화면은 계속 예전 날짜에 머물러 있었던 것이다.

  이 프로젝트의 다른 데이터(주가·뉴스·계란 수급)와 같은 구조로 통일한다:
  서버(GitHub Actions)가 주기적으로 긁어 결과를 JSON으로 커밋해두고,
  브라우저는 그 정적 JSON 하나만 읽는다 — 프록시도, 반복 스크래핑도 필요 없다.
"""

import re, sys, json, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import quote

import requests

KST = timezone(timedelta(hours=9))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

CHPRICE_URL = "https://chicken.or.kr/ch_price/price_2025.php"

# ── 프록시 경유 폴백 ──────────────────────────────────────────────────────────
# chicken.or.kr은 네트워크 자체가 막히는 게 아니라 403을 "정상 응답"으로 돌려주는
# 경우가 있어(WAF/봇 차단), 네트워크 예외뿐 아니라 403/429/503 응답도 폴백 대상에
# 포함시킨다 — 그래야 실제로 막힌 상황에서 프록시로 넘어간다.
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
BLOCK_STATUS = (403, 429, 503)


def get_with_proxy_fallback(session, url, timeout=20):
    """직접 연결이 네트워크 예외로 막히거나 403/429/503을 반환하면 공개 프록시로 재시도."""
    try:
        r = session.get(url, timeout=timeout)
        if r.status_code == 200:
            return r
        print("      직접 연결 HTTP %d → 프록시 경유 재시도" % r.status_code)
        if r.status_code not in BLOCK_STATUS:
            return r  # 200도, 알려진 차단 코드도 아니면 그대로 반환(원인 파악용)
    except NETWORK_ERRORS as e:
        print("      직접 연결 실패(%s) → 프록시 경유 재시도" % type(e).__name__)

    last = None
    for i, tmpl in enumerate(PROXY_TEMPLATES, 1):
        try:
            r = session.get(tmpl(url), timeout=timeout + 10)
            if r.status_code == 200 and len(r.content) > 500:
                print("      ✅ 프록시 %d 성공 (%dbytes)" % (i, len(r.content)))
                return r
            print("      프록시 %d 실패: HTTP %d / %dbytes" % (i, r.status_code, len(r.content)))
        except Exception as e:
            last = e
            print("      프록시 %d 실패: %s" % (i, e))
    if last:
        raise last
    raise Exception("모든 경로 실패")


# ── HTML 표 파싱 ──────────────────────────────────────────────────────────────
def _cell_text(cell_html):
    return re.sub(r"<[^>]+>", "", cell_html)


def parse_chicken_price_html(html):
    """
    '생계'·'병아리'가 같이 있는 헤더 행을 찾아 컬럼 위치를 동적으로 파악한 뒤
    이후 행에서 날짜/생계/병아리/종계노계 값을 추출한다.
    """
    rows_out = []

    for table_m in re.finditer(r"<table\b[^>]*>([\s\S]*?)</table>", html, re.I):
        table_html = table_m.group(1)
        trs = [m.group(1) for m in re.finditer(r"<tr\b[^>]*>([\s\S]*?)</tr>", table_html, re.I)]
        if not trs:
            continue

        hdr_idx = -1
        for i, tr in enumerate(trs):
            txt = _cell_text(tr)
            if "생계" in txt and "병아리" in txt:
                hdr_idx = i
                break
        if hdr_idx < 0:
            continue

        hdr_cells = re.findall(r"<t[hd][^>]*>([\s\S]*?)</t[hd]>", trs[hdr_idx], re.I)
        date_idx = broiler_idx = chick_idx = breeding_idx = -1
        for i, cell in enumerate(hdr_cells):
            t = re.sub(r"\s+", "", _cell_text(cell))
            if re.search(r"날짜|일자|연월|기준일", t):
                date_idx = i
            elif "생계" in t and broiler_idx < 0:
                broiler_idx = i
            elif "병아리" in t:
                chick_idx = i
            elif "종계" in t:
                breeding_idx = i

        def get_num(cells, idx, fallback_idx):
            i = idx if idx >= 0 else fallback_idx
            if i < 0 or i >= len(cells):
                return None
            n = re.sub(r"[^0-9]", "", _cell_text(cells[i]))
            if not n or int(n) == 0:
                return None
            return int(n)

        for tr in trs[hdr_idx + 1:]:
            cells = re.findall(r"<td[^>]*>([\s\S]*?)</td>", tr, re.I)
            if len(cells) < 3:
                continue
            raw_date = _cell_text(cells[date_idx if date_idx >= 0 else 0]).strip()
            if not re.search(r"\d{4}|^\d{2}[./]\d{2}", raw_date):
                continue
            date = raw_date.replace(".", "-").replace("/", "-")[:10]
            if len(date) == 5:
                date = str(datetime.now(KST).year) + "-" + date

            b = get_num(cells, broiler_idx, 1)
            c = get_num(cells, chick_idx, 2)
            br = get_num(cells, breeding_idx, 3)
            if b or c or br:
                rows_out.append({"date": date, "broiler": b, "chick": c, "breeding": br})

        if rows_out:
            break  # 헤더를 찾은 표에서만 추출하면 충분

    return rows_out[:10]


def load_previous():
    p = Path("chicken_price/latest.json")
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def save(rows, stale):
    Path("chicken_price").mkdir(exist_ok=True)
    now = datetime.now(KST)
    out = {
        "updated": now.strftime("%Y-%m-%d %H:%M KST"),
        "updatedTs": int(now.timestamp()),
        "source_url": CHPRICE_URL,
        "rows": rows,
        "stale": stale,
    }
    Path("chicken_price/latest.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("  ✅ chicken_price/latest.json 저장 (%d건, stale=%s)" % (len(rows), stale))
    if rows:
        print("  최신: %s" % rows[0])


def main():
    print("🐔 한국육계협회 시세 수집 시작 (%s)\n" % datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"))
    session = requests.Session()
    session.headers.update(HEADERS)

    prev = load_previous()

    try:
        r = get_with_proxy_fallback(session, CHPRICE_URL, timeout=20)
        print("  응답: HTTP %d / %dbytes / %s" % (
            r.status_code, len(r.content), r.headers.get("Content-Type", "")))
        r.encoding = r.apparent_encoding or "utf-8"

        if r.status_code != 200:
            raise Exception("최종 응답도 HTTP %d" % r.status_code)

        rows = parse_chicken_price_html(r.text)
        print("  파싱된 행 수: %d" % len(rows))

        if len(rows) < 3:
            print("  응답 본문 앞부분(진단용): %r" % r.text[:500])
            raise Exception("파싱 결과 부족 (%d건) — 사이트 표 구조가 바뀌었을 수 있음" % len(rows))

        save(rows, stale=False)
        print("\n✅ 완료")

    except Exception as e:
        print("\n❌ 수집 실패: %s" % e)
        if prev and prev.get("rows"):
            print("  ⚡ 이전 데이터 유지 (stale 표시)")
            save(prev["rows"], stale=True)
        else:
            print("  이전 데이터도 없어 저장하지 않음")
            sys.exit(1)


if __name__ == "__main__":
    main()
