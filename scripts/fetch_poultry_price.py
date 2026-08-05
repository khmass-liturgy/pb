#!/usr/bin/env python3
"""다봄에서 계란 특란(XL)과 육계 생계유통(대)만 수집한다.

Python 표준 라이브러리만 사용하므로 GitHub Actions에서 패키지 설치가 필요 없다.
"""

from __future__ import annotations

import html
import json
import re
import ssl
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

KST = timezone(timedelta(hours=9))
EGG_URL = "https://www.ekapepia.com/v3/price/livestock/egg/distrPrice.do?menuSn=36&boardInfoNo="
CHICKEN_URL = "https://www.ekapepia.com/v3/price/livestock/chicken/distrPrice.do?menuSn=35&boardInfoNo="
PIG_URL = "https://www.ekapepia.com/v3/price/livestock/pig/producer.do?searchCondition=&searchCondition1=&searchCondition2=&searchCondition3=&searchGubn=&searchStartDate=&searchEndDate=&ctdt=&typeCd=&searchType="
OUTPUT_PATH = Path("poultry_price/latest.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; pb-poultry-price/1.0)", "Accept-Language": "ko-KR,ko;q=0.9"}
PROXY_FACTORIES = (
    lambda url: "https://api.allorigins.win/raw?url=" + quote(url, safe=""),
    lambda url: "https://api.codetabs.com/v1/proxy/?quest=" + quote(url, safe=""),
)
SSL_CONTEXT = ssl.create_default_context()


class RowParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in ("td", "th") and self._row is not None and self._cell is not None:
            self._row.append(" ".join(html.unescape("".join(self._cell)).split()))
            self._cell = None
        elif tag == "tr" and self._row:
            self.rows.append(self._row)
            self._row = None


def normalize_date(value: str) -> str | None:
    match = re.search(r"(20\d{2})[./-]\s*(\d{1,2})[./-]\s*(\d{1,2})", value)
    if match:
        year, month, day = map(int, match.groups())
    else:
        match = re.search(r"(\d{1,2})월\s*(\d{1,2})일", value)
        if not match:
            return None
        year = datetime.now(KST).year
        month, day = map(int, match.groups())
    try:
        return datetime(year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        return None


def row_numbers(row: list[str]) -> list[int]:
    numbers: list[int] = []
    for cell in row[1:]:
        # 가격 뒤에 붙는 증감량(예: "2,000 0")을 가격과 합치지 않는다.
        match = re.search(r"(?<!\d)(\d[\d,]*)(?!\d)", cell)
        if match:
            numbers.append(int(match.group(1).replace(",", "")))
    return numbers


def parse_egg(html_text: str) -> list[dict[str, int | str]]:
    parser = RowParser()
    parser.feed(html_text)
    values: dict[str, dict[str, int | str]] = {}
    for row in parser.rows:
        date = normalize_date(row[0]) if row else None
        numbers = row_numbers(row) if date else []
        if date and len(numbers) >= 4:
            # 산지 XL의 원/30개 다음 열이 산지 XL 원/10개다.
            values.setdefault(date, {"date": date, "value": numbers[1]})
    return sorted(values.values(), key=lambda item: str(item["date"]), reverse=True)[:30]


def parse_chicken(html_text: str) -> list[dict[str, int | str]]:
    parser = RowParser()
    parser.feed(html_text)
    values: dict[str, dict[str, int | str]] = {}
    for row in parser.rows:
        date = normalize_date(row[0]) if row else None
        numbers = row_numbers(row) if date else []
        if date and len(numbers) >= 4:
            # 육계 표의 첫 번째 가격 열이 생계유통(대), 단위는 원/kg이다.
            values.setdefault(date, {"date": date, "value": numbers[0]})
    return sorted(values.values(), key=lambda item: str(item["date"]), reverse=True)[:30]


def parse_pig(html_text: str) -> list[dict[str, int | str]]:
    parser = RowParser()
    parser.feed(html_text)
    values: dict[str, dict[str, int | str]] = {}
    for row in parser.rows:
        first = row[0] if row else ""
        date = normalize_date(first)
        numbers = row_numbers(row) if date else []
        if date and numbers and ("금일" in first or "전일" in first):
            # 농가수취 평균 열(첫 번째 숫자), 원/kg
            values.setdefault(date, {"date": date, "value": numbers[0]})
    return sorted(values.values(), key=lambda item: str(item["date"]), reverse=True)[:30]


def fetch_page(url: str, parser) -> list[dict[str, int | str]]:
    for candidate in (url, *(factory(url) for factory in PROXY_FACTORIES)):
        try:
            request = Request(candidate, headers=HEADERS)
            with urlopen(request, timeout=30, context=SSL_CONTEXT) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                page = response.read().decode(charset, errors="replace")
            rows = parser(page)
            if rows:
                return rows
        except (OSError, URLError) as exc:
            print(f"request failed: {type(exc).__name__}: {exc}")
    return []


def main() -> int:
    egg_rows = fetch_page(EGG_URL, parse_egg)
    chicken_rows = fetch_page(CHICKEN_URL, parse_chicken)
    pig_rows = fetch_page(PIG_URL, parse_pig)
    if not egg_rows or not chicken_rows or not pig_rows:
        print("계란·육계·양돈 시세를 찾지 못했습니다.")
        return 1
    now = datetime.now(KST)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps({
        "updated": now.strftime("%Y-%m-%d %H:%M KST"),
        "egg": {"label": "계란 산지가격", "grade": "특란 (XL)", "unit": "원/10개", "latest": egg_rows[0]["value"], "rows": egg_rows},
        "chicken": {"label": "생계유통(대)", "unit": "원/kg", "latest": chicken_rows[0]["value"], "rows": chicken_rows},
        "pig": {"label": "농가수취 평균", "unit": "원/kg", "latest": pig_rows[0]["value"], "rows": pig_rows},
        "source_urls": {"egg": EGG_URL, "chicken": CHICKEN_URL, "pig": PIG_URL},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("수집 성공:", {"egg": egg_rows[0], "chicken": chicken_rows[0], "pig": pig_rows[0]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
