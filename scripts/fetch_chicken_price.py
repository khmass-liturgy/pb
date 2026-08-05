#!/usr/bin/env python3
"""
한국육계협회 육계 시세 수집기
외부 HTML 파서 의존성 없이 실행됩니다.

필수 패키지:
- requests
선택 패키지:
- playwright (requests 경로 실패 시 브라우저 폴백)
"""

from __future__ import annotations

import html as html_lib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import requests

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

KST = timezone(timedelta(hours=9))
SOURCE_URL = "https://chicken.or.kr/ch_price/price_2025.php"
OUTPUT_PATH = Path("chicken_price/latest.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7",
    "Cache-Control": "no-cache",
}

PROXY_URLS = [
    lambda u: "https://api.allorigins.win/raw?url=" + quote(u, safe=""),
    lambda u: "https://api.codetabs.com/v1/proxy/?quest=" + quote(u, safe=""),
    lambda u: "https://corsproxy.io/?url=" + quote(u, safe=""),
]

ERROR_MARKERS = (
    "invalid ssl certificate",
    "cloudflare",
    "error 526",
    "error 521",
    "access denied",
    "attention required",
    "just a moment",
    "ray id",
)


@dataclass(frozen=True)
class Cell:
    text: str
    rowspan: int = 1
    colspan: int = 1
    header: bool = False


class TableParser(HTMLParser):
    """HTML 표의 셀 텍스트와 rowspan/colspan을 보존한다."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[Cell]]] = []
        self._table_depth = 0
        self._current_table: list[list[Cell]] | None = None
        self._current_row: list[Cell] | None = None
        self._current_cell: list[str] | None = None
        self._current_cell_meta: tuple[int, int, bool] = (1, 1, False)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table":
            self._table_depth += 1
            if self._table_depth == 1:
                self._current_table = []
        elif self._table_depth == 1 and tag == "tr":
            self._current_row = []
        elif self._table_depth == 1 and tag in ("th", "td"):
            self._current_cell = []
            attributes = {key.lower(): value for key, value in attrs}
            try:
                rowspan = max(1, int(attributes.get("rowspan") or 1))
                colspan = max(1, int(attributes.get("colspan") or 1))
            except ValueError:
                rowspan, colspan = 1, 1
            self._current_cell_meta = (rowspan, colspan, tag == "th")

    def handle_data(self, data: str) -> None:
        if self._current_cell is not None:
            self._current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if self._table_depth == 1 and tag in ("th", "td"):
            if self._current_row is not None and self._current_cell is not None:
                value = " ".join("".join(self._current_cell).split())
                rowspan, colspan, header = self._current_cell_meta
                self._current_row.append(Cell(
                    html_lib.unescape(value), rowspan, colspan, header
                ))
            self._current_cell = None

        elif self._table_depth == 1 and tag == "tr":
            if self._current_table is not None and self._current_row:
                self._current_table.append(self._current_row)
            self._current_row = None

        elif tag == "table":
            if self._table_depth == 1 and self._current_table is not None:
                self.tables.append(self._current_table)
                self._current_table = None
            self._table_depth = max(0, self._table_depth - 1)


def expand_table(table: list[list[Cell]]) -> list[list[Cell | None]]:
    """rowspan/colspan을 실제 열 좌표로 펼친 직사각형 그리드를 만든다."""
    grid: list[list[Cell | None]] = []

    for row_index, source_row in enumerate(table):
        while len(grid) <= row_index:
            grid.append([])
        column = 0

        for cell in source_row:
            while column < len(grid[row_index]) and grid[row_index][column] is not None:
                column += 1

            for row_offset in range(cell.rowspan):
                target_row = row_index + row_offset
                while len(grid) <= target_row:
                    grid.append([])
                required = column + cell.colspan
                if len(grid[target_row]) < required:
                    grid[target_row].extend([None] * (required - len(grid[target_row])))
                for column_offset in range(cell.colspan):
                    target_column = column + column_offset
                    if grid[target_row][target_column] is not None:
                        raise ValueError("겹치는 rowspan/colspan 셀이 있습니다.")
                    grid[target_row][target_column] = cell
            column += cell.colspan

    width = max((len(row) for row in grid), default=0)
    for row in grid:
        row.extend([None] * (width - len(row)))
    return grid


def normalize_header(value: str) -> str:
    return re.sub(r"[\s·ㆍ()\[\]/_-]+", "", value).lower()


def column_map(grid: list[list[Cell | None]], first_data_row: int) -> dict[str, int]:
    """여러 헤더 행의 상위/하위 이름을 합쳐 각 의미 열을 찾는다."""
    labels: list[str] = []
    width = len(grid[0]) if grid else 0
    for column in range(width):
        parts: list[str] = []
        for row in grid[:first_data_row]:
            cell = row[column]
            if cell and cell.text and cell.text not in parts:
                parts.append(cell.text)
        labels.append(normalize_header(" ".join(parts)))

    aliases = {
        "date": lambda h: any(word in h for word in ("기준일", "날짜", "일자", "연월일")),
        "large": lambda h: ("육계" in h or "생계" in h) and "대" in h,
        "medium": lambda h: ("육계" in h or "생계" in h) and "중" in h,
        "small": lambda h: ("육계" in h or "생계" in h) and "소" in h,
        "chick": lambda h: "병아리" in h,
        "breeding": lambda h: "종계노계" in h or ("종계" in h and "노계" in h),
    }
    result: dict[str, int] = {}
    for key, matches in aliases.items():
        candidates = [i for i, label in enumerate(labels) if matches(label)]
        if len(candidates) != 1:
            raise ValueError(f"{key} 열을 하나로 특정할 수 없습니다: {labels}")
        result[key] = candidates[0]
    return result


def is_real_source_html(page_html: str) -> bool:
    """HTTP 200 오류 페이지를 원본 페이지로 오인하지 않는다."""
    if not page_html or len(page_html) < 1000:
        return False

    lower = page_html.lower()
    if any(marker in lower for marker in ERROR_MARKERS):
        return False

    return any(keyword in page_html for keyword in ("육계", "생계", "병아리"))


def normalize_date(value: str) -> str | None:
    text = re.sub(r"\s+", "", value)
    now = datetime.now(KST)

    match = re.search(
        r"(?P<y>\d{4})[./-](?P<m>\d{1,2})[./-](?P<d>\d{1,2})",
        text,
    )
    if match:
        year = int(match.group("y"))
        month = int(match.group("m"))
        day = int(match.group("d"))
    else:
        match = re.search(r"(?P<m>\d{1,2})[./-](?P<d>\d{1,2})", text)
        if not match:
            return None
        year = now.year
        month = int(match.group("m"))
        day = int(match.group("d"))

    try:
        return datetime(year, month, day, tzinfo=KST).strftime("%Y-%m-%d")
    except ValueError:
        return None


def parse_number(value: str) -> int | None:
    cleaned = value.replace(",", "")
    match = re.search(r"\d+", cleaned)
    if not match:
        return None
    number = int(match.group())
    return number if number > 0 else None


def parse_price_html(page_html: str) -> list[dict[str, Any]]:
    """
    한국육계협회 가격표의 실제 데이터 열을 읽는다.

    원본 표는 다단 헤더 구조다.
      기준일 | 육계(대 | 중 | 소) | 병아리 | 종계노계 ...

    셀 위치가 아니라 펼친 헤더 이름으로 육계 대·중·소, 병아리,
    종계노계를 각각 찾는다. 열이 빠지거나 중복되면 잘못 저장하지 않고 실패한다.
    """
    parser = TableParser()
    parser.feed(page_html)

    results: list[dict[str, Any]] = []

    for table in parser.tables:
        try:
            grid = expand_table(table)
            first_data_row = next(
                i for i, row in enumerate(grid)
                if any(cell and normalize_date(cell.text) for cell in row)
            )
            columns = column_map(grid, first_data_row)
        except (StopIteration, ValueError):
            continue

        for row in grid[first_data_row:]:
            date_cell = row[columns["date"]]
            date = normalize_date(date_cell.text) if date_cell else None
            if not date:
                continue
            parsed = {
                key: parse_number(row[index].text) if row[index] else None
                for key, index in columns.items() if key != "date"
            }
            if not all(parsed.values()):
                continue
            results.append({"date": date, **parsed})

        if results:
            break

    deduplicated: dict[str, dict[str, Any]] = {}
    for row in results:
        deduplicated.setdefault(row["date"], row)

    return sorted(
        deduplicated.values(),
        key=lambda item: item["date"],
        reverse=True,
    )[:10]


def fetch_with_requests() -> str | None:
    session = requests.Session()
    session.headers.update(HEADERS)

    urls = [SOURCE_URL] + [factory(SOURCE_URL) for factory in PROXY_URLS]

    for index, url in enumerate(urls):
        label = "direct" if index == 0 else f"proxy-{index}"
        try:
            response = session.get(url, timeout=30)
            response.encoding = response.apparent_encoding or "utf-8"
            page_html = response.text

            print(f"[{label}] HTTP {response.status_code}, {len(page_html)} chars")

            if response.status_code == 200 and is_real_source_html(page_html):
                return page_html

            print(f"[{label}] rejected: block/error/non-source page")

        except requests.RequestException as exc:
            print(f"[{label}] request failed: {type(exc).__name__}: {exc}")

    return None


def fetch_with_browser() -> str | None:
    if not HAS_PLAYWRIGHT:
        print("[browser] playwright unavailable")
        return None

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = browser.new_context(
                user_agent=HEADERS["User-Agent"],
                locale="ko-KR",
            )
            page = context.new_page()
            response = page.goto(
                SOURCE_URL,
                wait_until="domcontentloaded",
                timeout=45000,
            )
            page.wait_for_timeout(2500)
            page_html = page.content()
            status = response.status if response else "unknown"
            print(f"[browser] HTTP {status}, {len(page_html)} chars")
            browser.close()

            return page_html if is_real_source_html(page_html) else None

    except Exception as exc:
        print(f"[browser] failed: {type(exc).__name__}: {exc}")
        return None


def load_previous() -> dict[str, Any] | None:
    try:
        return json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def save(
    rows: list[dict[str, Any]],
    stale: bool,
    error: str | None = None,
) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(KST)
    payload: dict[str, Any] = {
        "updated": now.strftime("%Y-%m-%d %H:%M KST"),
        "updatedTs": int(now.timestamp()),
        "source_url": SOURCE_URL,
        "rows": rows,
        "stale": stale,
    }

    if error:
        payload["error"] = error

    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"saved {OUTPUT_PATH}: rows={len(rows)}, stale={stale}")


def main() -> int:
    print(f"육계 시세 수집 시작: {datetime.now(KST):%Y-%m-%d %H:%M KST}")

    page_html = fetch_with_requests()
    if page_html is None:
        page_html = fetch_with_browser()

    rows = parse_price_html(page_html) if page_html else []

    # 최신 데이터가 1행만 있어도 정상이다.
    if rows:
        save(rows, stale=False)
        print("수집 성공:", rows[0])
        return 0

    message = "유효한 육계 시세 행을 찾지 못했습니다."
    previous = load_previous()

    if previous and previous.get("rows"):
        save(previous["rows"], stale=True, error=message)
        print("이전 데이터 유지(stale=true)")
        return 0

    print(message, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
