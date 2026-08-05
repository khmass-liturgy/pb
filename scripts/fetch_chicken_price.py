#!/usr/bin/env python3
"""
한국육계협회 육계 시세 수집기
- 직접 요청 → 공개 프록시 → Playwright 순서로 시도
- HTTP 200이어도 Cloudflare/프록시 오류 페이지면 실패 처리
- 최신 유효 시세가 1행만 있어도 정상 저장
- 기존 JSON이 있으면 실패 시 stale=true로 유지
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

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


def is_real_source_html(html: str) -> bool:
    """프록시/Cloudflare 오류 페이지를 정상 HTML로 오인하지 않는다."""
    if not html or len(html) < 1000:
        return False
    low = html.lower()
    if any(marker in low for marker in ERROR_MARKERS):
        return False
    return "육계" in html or "생계" in html or "병아리" in html


def normalize_date(value: str) -> str | None:
    text = re.sub(r"\s+", "", value)
    now = datetime.now(KST)

    patterns = [
        (r"(?P<y>\d{4})[./-](?P<m>\d{1,2})[./-](?P<d>\d{1,2})", True),
        (r"(?P<m>\d{1,2})[./-](?P<d>\d{1,2})", False),
    ]
    for pattern, has_year in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        year = int(match.group("y")) if has_year else now.year
        month = int(match.group("m"))
        day = int(match.group("d"))
        try:
            return datetime(year, month, day, tzinfo=KST).strftime("%Y-%m-%d")
        except ValueError:
            return None
    return None


def parse_number(value: str) -> int | None:
    cleaned = value.replace(",", "")
    match = re.search(r"\d+", cleaned)
    if not match:
        return None
    number = int(match.group())
    return number if number > 0 else None


def parse_price_html(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[dict[str, Any]] = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue

        header_index = None
        headers: list[str] = []

        for i, row in enumerate(rows):
            cells = row.find_all(["th", "td"])
            texts = [re.sub(r"\s+", "", c.get_text(" ", strip=True)) for c in cells]
            joined = "|".join(texts)
            if ("생계" in joined or "육계" in joined) and "병아리" in joined:
                header_index = i
                headers = texts
                break

        if header_index is None:
            continue

        date_idx = next(
            (i for i, h in enumerate(headers) if any(k in h for k in ("일자", "날짜", "기준일", "연월일"))),
            0,
        )
        broiler_idx = next(
            (i for i, h in enumerate(headers) if "생계" in h or "육계" in h),
            None,
        )
        chick_idx = next((i for i, h in enumerate(headers) if "병아리" in h), None)
        breeding_idx = next(
            (i for i, h in enumerate(headers) if "종계" in h and "노계" in h),
            next((i for i, h in enumerate(headers) if "종계" in h), None),
        )

        for row in rows[header_index + 1:]:
            cells = row.find_all("td")
            values = [c.get_text(" ", strip=True) for c in cells]
            if len(values) < 2:
                continue

            date = normalize_date(values[date_idx] if date_idx < len(values) else "")
            if not date:
                continue

            def at(index: int | None) -> int | None:
                if index is None or index >= len(values):
                    return None
                return parse_number(values[index])

            item = {
                "date": date,
                "broiler": at(broiler_idx),
                "chick": at(chick_idx),
                "breeding": at(breeding_idx),
            }
            if any(item[k] is not None for k in ("broiler", "chick", "breeding")):
                results.append(item)

        if results:
            break

    # 중복 날짜 제거 후 최신순
    deduped: dict[str, dict[str, Any]] = {}
    for row in results:
        deduped.setdefault(row["date"], row)
    return sorted(deduped.values(), key=lambda x: x["date"], reverse=True)[:10]


def fetch_with_requests() -> str | None:
    session = requests.Session()
    session.headers.update(HEADERS)

    urls = [SOURCE_URL] + [factory(SOURCE_URL) for factory in PROXY_URLS]
    for index, url in enumerate(urls):
        label = "direct" if index == 0 else f"proxy-{index}"
        try:
            response = session.get(url, timeout=30)
            response.encoding = response.apparent_encoding or "utf-8"
            html = response.text
            print(f"[{label}] HTTP {response.status_code}, {len(html)} chars")
            if response.status_code == 200 and is_real_source_html(html):
                return html
            print(f"[{label}] rejected: block/error/non-source page")
        except requests.RequestException as exc:
            print(f"[{label}] request failed: {type(exc).__name__}: {exc}")
    return None


def fetch_with_browser() -> str | None:
    if not HAS_PLAYWRIGHT:
        print("[browser] playwright unavailable")
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = browser.new_context(
                user_agent=HEADERS["User-Agent"],
                locale="ko-KR",
            )
            page = context.new_page()
            response = page.goto(SOURCE_URL, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(2500)
            html = page.content()
            status = response.status if response else "unknown"
            print(f"[browser] HTTP {status}, {len(html)} chars")
            browser.close()
            return html if is_real_source_html(html) else None
    except Exception as exc:
        print(f"[browser] failed: {type(exc).__name__}: {exc}")
        return None


def load_previous() -> dict[str, Any] | None:
    try:
        return json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def save(rows: list[dict[str, Any]], stale: bool, error: str | None = None) -> None:
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

    html = fetch_with_requests()
    if html is None:
        html = fetch_with_browser()

    rows = parse_price_html(html) if html else []

    # 핵심 수정: 원본이 최신 1행만 제공해도 정상 데이터다.
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
