#!/usr/bin/env python3
"""KAPE 다봄 계란 산지가격(특란/XL, 원/10개) 수집기."""

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
SOURCE_URL = "https://www.ekapepia.com/v3/price/livestock/egg/distrPrice.do?menuSn=36&boardInfoNo="
OUTPUT_PATH = Path("egg_price/latest.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; pb-egg-price/1.0)", "Accept-Language": "ko-KR,ko;q=0.9"}
PROXY_URLS = [
    lambda url: "https://api.allorigins.win/raw?url=" + quote(url, safe=""),
    lambda url: "https://api.codetabs.com/v1/proxy/?quest=" + quote(url, safe=""),
]


class RowParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self.row: list[str] | None = None
        self.cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in ("td", "th") and self.row is not None and self.cell is not None:
            self.row.append(" ".join(html.unescape("".join(self.cell)).split()))
            self.cell = None
        elif tag == "tr" and self.row:
            self.rows.append(self.row)
            self.row = None


def normalize_date(value: str) -> str | None:
    match = re.search(r"(20\d{2})[./-]\s*(\d{1,2})[./-]\s*(\d{1,2})", value)
    if not match:
        match = re.search(r"(\d{1,2})월\s*(\d{1,2})일", value)
        if not match:
            return None
        year = datetime.now(KST).year
        month, day = map(int, match.groups())
    else:
        year, month, day = map(int, match.groups())
    try:
        return datetime(year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        return None


def parse_egg_price_html(page_html: str) -> list[dict[str, Any]]:
    """산지가격 XL의 원/30개와 원/10개 중 두 번째 숫자를 선택한다."""
    parser = RowParser()
    parser.feed(page_html)
    parsed: dict[str, dict[str, Any]] = {}
    for row in parser.rows:
        if not row:
            continue
        date = normalize_date(row[0])
        if not date:
            continue
        numbers: list[int] = []
        for cell in row[1:]:
            match = re.search(r"(?<!\d)(\d[\d,]*)(?!\d)", cell.replace(" ", ""))
            if match:
                numbers.append(int(match.group(1).replace(",", "")))
        # 실제 표: 산지 30구, 산지 10구, 도매 30구, 도매 10구, 소비자가...
        if len(numbers) < 4:
            continue
        parsed.setdefault(date, {"date": date, "farm_per_10": numbers[1]})
    return sorted(parsed.values(), key=lambda item: item["date"], reverse=True)[:30]


def fetch_html() -> str | None:
    urls = [SOURCE_URL] + [factory(SOURCE_URL) for factory in PROXY_URLS]
    for url in urls:
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.encoding = response.apparent_encoding or "utf-8"
            if response.ok and len(parse_egg_price_html(response.text)) >= 1:
                return response.text
        except requests.RequestException as exc:
            print(f"request failed: {type(exc).__name__}: {exc}")
    return None


def main() -> int:
    page_html = fetch_html()
    rows = parse_egg_price_html(page_html) if page_html else []
    if not rows:
        print("유효한 계란 산지가격을 찾지 못했습니다.")
        return 1
    now = datetime.now(KST)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps({
        "updated": now.strftime("%Y-%m-%d %H:%M KST"),
        "source_url": SOURCE_URL,
        "unit": "원/10개",
        "grade": "특란 (XL)",
        "rows": rows,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("수집 성공:", rows[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
