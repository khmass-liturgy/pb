#!/usr/bin/env python3
"""농림축산식품부 「배합사료 생산실적」 월별 통계 수집 — 육계·산란계 생산잠재력 추정용.

농식품부 게시판(https://www.mafra.go.kr/bbs/home/789/artclList.do)에 매달 20일경
"YYYY년 M월 배합사료 생산(실적) 및 가격 통계" 글이 올라오고, 첨부
"YY년 M월 배합사료 생산실적.xls"(BIFF .xls, 시트 1장)에 그 해 1월~해당 월까지의
축종·용도별 월별 생산량(톤)이 들어 있다(0열=항목명, 1~12열=1~12월).

같은 달 글이 "(수정)"·"수정 게시"로 다시 올라오기도 하고, 뒤 달 파일에서 앞 달
수치가 조정되기도 하므로 연도마다 "가장 최근 글"(같은 달이면 글 번호가 큰 쪽 =
수정본)의 파일 하나만 쓴다. 전년 동월 비교를 위해 올해 최신 파일과 작년 최신
파일(보통 12월분 = 작년 1~12월 전체) 두 개를 받는다.

여기서는 원자료(톤)만 모은다. 1수당 사료섭취량 표준으로 마릿수를 환산하는
계산은 index.html이 사이트에 이미 있는 Ross 308 / Hy-Line Brown 표준표로 한다 —
표준값을 한 곳에만 둔다.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, urljoin

import requests
import xlrd

KST = timezone(timedelta(hours=9))
OUT_PATH = Path("feed_production/latest.json")
BASE = "https://www.mafra.go.kr"
LIST_URL = f"{BASE}/bbs/home/789/artclList.do"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}
PROXY_URLS = [
    lambda url: "https://api.allorigins.win/raw?url=" + quote(url, safe=""),
    lambda url: "https://api.codetabs.com/v1/proxy/?quest=" + quote(url, safe=""),
]
OLE2_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"   # .xls(BIFF) 파일 시그니처

# 농식품부는 해외 IP 접속을 막아 GitHub Actions(미국)에서도, 해외 공개 프록시에서도
# 접속이 안 된다(ConnectTimeout / 522). 그래서 자동 문자 발송용으로 이미 쓰는 국내
# 리전 중계 서버(farm-pro/sms-relay, Oracle Cloud VM)의 /fetch-mafra 경로로 받는다 —
# 같은 두 시크릿(SMS_RELAY_URL = …/send-sms, SMS_RELAY_SECRET)을 재사용한다. 이 서버는
# 배합사료 게시판(bbs/home/789)의 목록·글·첨부 주소만 허용한다.
# 시크릿이 없으면(로컬 실행 등) 직접 요청부터 한다. 공개 저장소라 Actions 로그가
# 공개되므로 중계 서버 주소는 출력하지 않는다.
_RELAY_URL = os.environ.get("SMS_RELAY_URL", "").strip()
_RELAY_SECRET = os.environ.get("SMS_RELAY_SECRET", "").strip()
RELAY_FETCH = (re.sub(r"/send-sms/?$", "", _RELAY_URL) + "/fetch-mafra") if _RELAY_URL and _RELAY_SECRET else None

# "2025년 8월 배합사료 생산 실적 및 가격 통계(수정)", "…생산실적 및 통계" 등 표기가 섞여 있다.
TITLE_RE = re.compile(r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*배합사료\s*생산\s*실적")
POST_RE = re.compile(r'href="(/bbs/home/789/(\d+)/artclView\.do)"[^>]*>([\s\S]*?)</a>')
FILE_RE = re.compile(r'href="(/bbs/home/789/\d+/download\.do)"[^>]*>\s*([^<]*?\.xlsx?)')

# 표의 항목명 → 묶음. 항목명은 시트 안에서 모두 한 번씩만 나온다(확인함).
GROUPS = {
    # 육계: 전기(초기 포함) / 후기. 육용어린·중병아리, 육용종계는 종계 육성용이라 뺀다.
    "broiler_starter":  ["육계초기", "육계전기"],
    "broiler_finisher": ["육계후기"],
    # 산란계: 중추(육성기 전체 = 어린+중+큰병아리) / 산란(산란전~말기, 질소저감사료 포함).
    # 산란종계는 뺀다.
    "layer_rearing": ["산란용어린병아리", "산란용중병아리", "산란용큰병아리"],
    "layer_laying":  ["산란전", "산란초기", "산란중기", "산란말기",
                      "산란전(질소저감사료)", "산란초기(질소저감사료)",
                      "산란중기(질소저감사료)", "산란말기(질소저감사료)"],
}
ALL_ROWS = [name for names in GROUPS.values() for name in names]


def _candidates(url: str):
    """(요청 주소, 헤더, 로그용 이름) — 국내 중계 서버 → 직접 → 공개 CORS 프록시 순."""
    if RELAY_FETCH:
        yield (f"{RELAY_FETCH}?url={quote(url, safe='')}",
               {**HEADERS, "Authorization": f"Bearer {_RELAY_SECRET}"}, "국내 중계 서버")
    yield url, HEADERS, url[:70]
    for factory in PROXY_URLS:
        proxied = factory(url)
        yield proxied, HEADERS, proxied[:70]


def _get(url: str, binary: bool = False):
    """프록시가 오류 페이지를 200으로 돌려주는 경우가 있어 바이너리는 .xls 시그니처까지 확인한다."""
    for candidate, headers, name in _candidates(url):
        try:
            resp = requests.get(candidate, headers=headers, timeout=30)
            if not resp.ok:
                print(f"  HTTP {resp.status_code}: {name}")
                continue
            if binary:
                if resp.content.startswith(OLE2_MAGIC):
                    return resp.content
                print(f"  .xls가 아닌 응답({len(resp.content)}bytes): {name}")
                continue
            resp.encoding = "utf-8"
            if resp.text:
                return resp.text
        except requests.RequestException as exc:
            # 예외 메시지에 요청 주소가 들어가므로 중계 서버일 때는 유형만 남긴다.
            detail = type(exc).__name__ if name == "국내 중계 서버" else f"{type(exc).__name__}: {exc}"
            print(f"  요청 실패({name}): {detail}")
    return None


def list_posts(max_pages: int = 6) -> list[dict]:
    """게시판 목록에서 배합사료 생산실적 글을 모은다. 작년 12월분까지 찾으면 멈춘다."""
    posts, this_year = [], None
    for page in range(1, max_pages + 1):
        html = _get(f"{LIST_URL}?page={page}")
        if not html:
            break
        for href, art_id, inner in POST_RE.findall(html):
            title = re.sub(r"<[^>]+>|\s+", " ", inner).strip()
            title = re.sub(r"\s*새글$", "", title)   # 목록의 "새글" 표시 배지
            m = TITLE_RE.search(title)
            if m:
                posts.append({"year": int(m.group(1)), "month": int(m.group(2)),
                              "id": int(art_id), "title": title, "url": urljoin(BASE, href)})
        if posts:
            this_year = this_year or max(p["year"] for p in posts)
            if any(p["year"] == this_year - 1 and p["month"] == 12 for p in posts):
                break
    return posts


def pick_latest(posts: list[dict], year: int) -> dict | None:
    """그 해의 가장 최근 달, 같은 달이면 글 번호가 큰 쪽(수정본)."""
    cands = [p for p in posts if p["year"] == year]
    return max(cands, key=lambda p: (p["month"], p["id"])) if cands else None


def find_attachment(post: dict) -> tuple[str, str]:
    html = _get(post["url"])
    if not html:
        raise RuntimeError(f"글을 열지 못함: {post['url']}")
    for href, name in FILE_RE.findall(html):
        name = name.strip()
        if "생산실적" in name and "시도별" not in name and "가격" not in name:
            return urljoin(BASE, href), name
    raise RuntimeError(f"생산실적 첨부파일을 찾지 못함: {post['title']}")


def parse_xls(content: bytes, expect_year: int) -> tuple[int, dict[str, list]]:
    """(자료 마지막 달, {항목명: 1~12월 톤}) — 아직 안 온 달은 None."""
    sh = xlrd.open_workbook(file_contents=content).sheet_by_index(0)

    # "●조회년도 : | 2026 | 년 | 08 | 월" 행에서 연·월을 읽는다.
    year = month = None
    for r in range(min(10, sh.nrows)):
        cells = [str(sh.cell_value(r, c)).strip() for c in range(min(6, sh.ncols))]
        if "조회년도" in cells[0]:
            year, month = int(float(cells[1])), int(float(cells[3]))
            break
    if year != expect_year or not month or not 1 <= month <= 12:
        raise RuntimeError(f"조회년도 불일치/누락: 파일 {year}년 {month}월, 기대 {expect_year}년")

    rows = {}
    for r in range(sh.nrows):
        label = str(sh.cell_value(r, 0)).strip()
        if label in ALL_ROWS and label not in rows:
            vals = []
            for c in range(1, 13):
                v = sh.cell_value(r, c)
                vals.append(round(float(v), 2) if c <= month and v not in ("", None) else None)
            rows[label] = vals
    missing = [n for n in ALL_ROWS if n not in rows]
    if missing:
        raise RuntimeError(f"표에서 항목을 찾지 못함(양식 변경?): {missing}")
    return month, rows


def group_series(rows: dict[str, list]) -> dict[str, list]:
    out = {}
    for key, names in GROUPS.items():
        series = []
        for i in range(12):
            vals = [rows[n][i] for n in names]
            series.append(None if any(v is None for v in vals) else round(sum(vals), 1))
        out[key] = series
    return out


def fetch_year(posts: list[dict], year: int) -> dict:
    post = pick_latest(posts, year)
    if not post:
        raise RuntimeError(f"{year}년 게시물을 찾지 못함")
    file_url, file_name = find_attachment(post)
    content = _get(file_url, binary=True)
    if not content:
        raise RuntimeError(f"첨부파일을 받지 못함: {file_name}")
    month, rows = parse_xls(content, year)
    print(f"  {year}년: '{post['title']}' → {file_name} (1~{month}월)")
    return {"through_month": month, "post_title": post["title"], "post_url": post["url"],
            "file": file_name, "rows": rows, "groups": group_series(rows)}


def keep_previous(reason: str):
    if not OUT_PATH.exists():
        print("  이전 데이터 없음 — 파일을 만들지 않음")
        return
    try:
        prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return
    prev["stale"] = True
    prev["stale_reason"] = reason
    OUT_PATH.write_text(json.dumps(prev, ensure_ascii=False, indent=1), encoding="utf-8")
    print("  ⚡ 이전 데이터 유지 + stale 표시")


def main():
    print("🌾 배합사료 생산실적 수집 시작\n")
    try:
        posts = list_posts()
        if not posts:
            raise RuntimeError("게시판에서 배합사료 생산실적 글을 찾지 못함")
        latest_year = max(p["year"] for p in posts)
        cur = fetch_year(posts, latest_year)
        prev = fetch_year(posts, latest_year - 1)
    except Exception as e:
        print(f"❌ 수집 실패: {type(e).__name__}: {e}")
        keep_previous(f"{type(e).__name__}: {e}")
        sys.exit(1)

    payload = {
        "source": "농림축산식품부 「배합사료 생산실적」",
        "url": LIST_URL,
        "unit": "톤",
        "latest": {"year": latest_year, "month": cur["through_month"]},
        "years": {str(latest_year): cur, str(latest_year - 1): prev},
        "stale": False,
    }

    # 내용이 그대로면 파일을 다시 쓰지 않는다 — 매일 돌려도 새 자료가 올라온 날만
    # 커밋되도록(갱신 시각까지 매번 바뀌면 워크플로가 매일 커밋하게 된다).
    if OUT_PATH.exists():
        try:
            old = json.loads(OUT_PATH.read_text(encoding="utf-8"))
            if {k: v for k, v in old.items() if k != "updated"} == payload:
                print(f"\n변경 없음 — {latest_year}년 {cur['through_month']}월 자료 그대로")
                return
        except Exception:
            pass

    payload = {"updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"), **payload}
    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    m = cur["through_month"] - 1
    print(f"\n✅ {latest_year}년 {cur['through_month']}월 기준 (톤, 전년 동월)")
    for key in GROUPS:
        a, b = cur["groups"][key][m], prev["groups"][key][m]
        pct = (a - b) / b * 100 if a is not None and b else None
        print(f"   {key:17s} {a:>12,.1f}  ({b:,.1f}, {pct:+.1f}%)" if pct is not None else f"   {key} {a}")


if __name__ == "__main__":
    main()
