#!/usr/bin/env python3
"""대한양계협회(poultry.or.kr) 홈페이지 "금일 육계시세" 표 수집기.

협회 홈페이지 메인 화면(https://www.poultry.or.kr/)에 매일 오후 1시경 게시되는
표를 그대로 가져온다. 대/중/소/병아리 4개 규격의 금일·전일·전월·전년 값을 담고
있으며, 다른 패널이 쓰는 축산물품질평가원(다봄) 시세와는 출처가 다른 협회
자체 공시가다.
"""

from __future__ import annotations

import html
import json
import re
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

KST = timezone(timedelta(hours=9))
SOURCE_URL = "https://www.poultry.or.kr/"
OUTPUT_PATH = Path("broiler_price_today/latest.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; pb-broiler-price/1.0)", "Accept-Language": "ko-KR,ko;q=0.9"}
PROXY_URLS = [
    lambda url: "https://api.allorigins.win/raw?url=" + quote(url, safe=""),
    lambda url: "https://api.codetabs.com/v1/proxy/?quest=" + quote(url, safe=""),
]

# 표 원문 기준 — 병아리는 kg 단위가 아니라 마리당 가격이라 단위를 따로 둔다.
GRADE_INFO = {
    "대": {"spec": "1.6kg이상", "unit": "원/kg"},
    "중": {"spec": "1.6kg미만~1.4kg이상", "unit": "원/kg"},
    "소": {"spec": "1.4kg미만", "unit": "원/kg"},
    "병아리": {"spec": None, "unit": "원/마리"},
}
COLUMNS = ["today", "yesterday", "last_month", "last_year"]
GRADE_ORDER = {"대": 0, "중": 1, "소": 2, "병아리": 3}


class PriceTableParser(HTMLParser):
    """<table class="t_price"> 하나만 뽑아 행 단위 텍스트로 모은다."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_table = False
        self.table_depth = 0
        self.row: list[str] | None = None
        self.cell: list[str] | None = None
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = dict(attrs)
        if tag == "table":
            if not self.in_table and "t_price" in (attr_map.get("class") or "").split():
                self.in_table = True
                self.table_depth = 1
            elif self.in_table:
                self.table_depth += 1
        elif self.in_table and tag == "tr":
            self.row = []
        elif self.in_table and tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "table" and self.in_table:
            self.table_depth -= 1
            if self.table_depth <= 0:
                self.in_table = False
        elif self.in_table and tag in ("td", "th") and self.row is not None and self.cell is not None:
            self.row.append(" ".join(html.unescape("".join(self.cell)).split()))
            self.cell = None
        elif self.in_table and tag == "tr" and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)


def parse_price_table(page_html: str) -> dict[str, Any] | None:
    parser = PriceTableParser()
    parser.feed(page_html)
    rows = parser.rows
    if not rows:
        return None

    header = rows[0]
    date_label = header[0].strip() if header else None  # "09/14" 형식

    grades: dict[str, dict[str, int]] = {}
    for row in rows[1:]:
        if len(row) < 5:
            continue
        name = row[0].strip()
        if name not in GRADE_INFO:
            continue
        numbers: list[int | None] = []
        for cell in row[1:5]:
            match = re.search(r"-?\d[\d,]*", cell.replace(" ", ""))
            numbers.append(int(match.group(0).replace(",", "")) if match else None)
        if len(numbers) != 4 or any(n is None for n in numbers):
            continue
        grades[name] = dict(zip(COLUMNS, numbers))

    if not grades:
        return None
    return {"date_label": date_label, "grades": grades}


def fetch_html() -> str | None:
    urls = [SOURCE_URL] + [factory(SOURCE_URL) for factory in PROXY_URLS]
    for url in urls:
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.encoding = response.apparent_encoding or "utf-8"
            if response.ok and parse_price_table(response.text):
                return response.text
        except requests.RequestException as exc:
            print(f"request failed: {type(exc).__name__}: {exc}")
    return None


def main() -> int:
    page_html = fetch_html()
    parsed = parse_price_table(page_html) if page_html else None

    previous: dict[str, Any] = {}
    if OUTPUT_PATH.exists():
        try:
            previous = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            previous = {}

    now = datetime.now(KST)
    if not parsed:
        if not previous:
            print("유효한 육계시세 표를 찾지 못했고, 이전 데이터도 없습니다.")
            return 1
        print("수집 실패 — 이전 데이터를 그대로 유지합니다(stale).")
        previous["stale"] = True
        OUTPUT_PATH.write_text(json.dumps(previous, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0

    rows = [
        {
            "grade": grade,
            "spec": GRADE_INFO[grade]["spec"],
            "unit": GRADE_INFO[grade]["unit"],
            "today": values["today"],
            "yesterday": values["yesterday"],
            "last_month": values["last_month"],
            "last_year": values["last_year"],
        }
        for grade, values in parsed["grades"].items()
    ]
    rows.sort(key=lambda r: GRADE_ORDER.get(r["grade"], 99))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps({
        "date_label": parsed["date_label"],
        "rows": rows,
        "note": "게재시간 : 당일 오후 1시 · 대(1.6kg이상), 중(1.6kg미만~1.4kg이상), 소(1.4kg미만)",
        "updated": now.strftime("%Y-%m-%d %H:%M KST"),
        "source_url": SOURCE_URL,
        "stale": False,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("수집 성공:", rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
