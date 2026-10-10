#!/usr/bin/env python3
"""시세예측용 과거 시세 소급 수집 — 다봄(ekapepia)이 2018-03-01부터 제공하는 일별 가격을 `price_history/daily.json`에 채워 넣는다.

다봄의 「유통단계별 가격」 화면은 기간(radioChk=day, startYYMMDD, endYYMMDD, searchStartDate, searchEndDate)을 주면
그 기간의 일별 표 전체를 한 번에 준다(2018-03-01 이전은 조회 불가). 한 해씩 끊어 받아 이어 붙이며, 매일 도는
accumulate_price_history.py와 같은 파일·같은 시리즈 이름(egg, broiler_live)을 쓴다.

  python scripts/backfill_price_history.py              # 2018-03-01 ~ 오늘 전체
  python scripts/backfill_price_history.py 2021 2023    # 해당 연도만

이상값(계란 800~6000원/10개, 육계 500~5000원/kg 밖)은 버리고 개수를 출력한다. 요청 실패는 해당 구간만 건너뛴다.
"""
from __future__ import annotations

import json
import re
import ssl
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fetch_poultry_price import HEADERS, RowParser, row_numbers
from accumulate_price_history import SERIES_META, merge_rows

KST = timezone(timedelta(hours=9))
OUT = Path("price_history/daily.json")
START = date(2018, 3, 1)
SSL_CONTEXT = ssl.create_default_context()
BASE = "https://www.ekapepia.com/v3/price/livestock/"
# (시리즈, 주소, menuSn, 값이 들어 있는 숫자 칸 번호, 허용 범위)
SOURCES = [
    ("egg", BASE + "egg/distrPrice.do", "36", 1, (800, 6000)),
    ("broiler_live", BASE + "chicken/distrPrice.do", "35", 0, (500, 5000)),
]


def fetch_window(url: str, menu: str, start: date, end: date) -> str | None:
    q = urlencode({
        "menuSn": menu, "boardInfoNo": "", "radioChk": "day",
        "startYYMMDD": start.isoformat(), "endYYMMDD": end.isoformat(),
        "searchStartDate": start.isoformat(), "searchEndDate": end.isoformat(), "searchStartDate2": "",
    })
    for attempt in range(3):
        try:
            with urlopen(Request(url + "?" + q, headers=HEADERS), timeout=60, context=SSL_CONTEXT) as r:
                return r.read().decode(r.headers.get_content_charset() or "utf-8", errors="replace")
        except (OSError, URLError) as exc:
            print(f"    재시도 {attempt + 1}: {type(exc).__name__}: {exc}")
            time.sleep(3 * (attempt + 1))
    return None


DAY_RE = re.compile(r"^(\d{1,2})월\s*(\d{1,2})일$")


def parse_window(page: str, idx: int, lo_hi: tuple[int, int], year: int) -> tuple[list[tuple[str, int]], int]:
    """다봄의 일별 표는 날짜 칸이 "01월 12일"처럼 연도 없이 나온다 — 조회한 구간의 연도를 붙인다.
    표 아래쪽의 월별 요약표("26년 01월")는 날짜 모양이 달라 걸러진다."""
    parser = RowParser()
    parser.feed(page)
    rows, dropped = {}, 0
    for row in parser.rows:
        m = DAY_RE.match(row[0]) if row else None
        d = None
        if m:
            try:
                d = date(year, int(m.group(1)), int(m.group(2))).isoformat()
            except ValueError:
                d = None
        nums = row_numbers(row) if d else []
        if d and len(nums) > idx:
            v = nums[idx]
            if lo_hi[0] <= v <= lo_hi[1]:
                rows.setdefault(d, v)
            else:
                dropped += 1
    return sorted(rows.items()), dropped


def main(argv: list[str]) -> int:
    reset = "--reset" in argv
    argv = [a for a in argv if a != "--reset"]
    today = datetime.now(KST).date()
    if len(argv) >= 2:
        y0, y1 = int(argv[0]), int(argv[1])
    else:
        y0, y1 = START.year, today.year
    data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    series = data.get("series") or {}
    for key, url, menu, idx, lo_hi in SOURCES:
        cur = series.get(key) or {}
        cur.update(SERIES_META[key])
        if reset:
            cur["rows"] = []
        total = 0
        for year in range(y0, y1 + 1):
            start, end = max(date(year, 1, 1), START), min(date(year, 12, 31), today)
            if start > end:
                continue
            page = fetch_window(url, menu, start, end)
            if page is None:
                print(f"  [{key}] {year}: 가져오기 실패 — 건너뜀")
                continue
            rows, dropped = parse_window(page, idx, lo_hi, year)
            rows = [r for r in rows if start.isoformat() <= r[0] <= end.isoformat()]
            print(f"  [{key}] {year}: {len(rows)}건 (범위 밖 {dropped}건 제외)" + (f", {rows[0][0]} ~ {rows[-1][0]}" if rows else ""))
            cur["rows"] = merge_rows(cur.get("rows"), rows)
            total += len(rows)
            time.sleep(1.5)
        series[key] = cur
        r = cur.get("rows") or []
        print(f"[{key}] 누적 {len(r)}건" + (f" ({r[0][0]} ~ {r[-1][0]})" if r else ""))
    data["series"] = series
    data.setdefault("feed_monthly", {})
    data["updated"] = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    data.setdefault("note", "다봄·대한양계협회·농식품부 자료를 날짜별로 이어 붙인 누적 자료. 시리즈별 조사처가 다르므로 서로 섞어 쓰지 않는다.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
