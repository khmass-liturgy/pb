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
# 산지가격(권역별) — 전국 옆에 수도권 XL 가격을 나란히 보여주기 위해 추가.
# 이 페이지는 원/30개 단위만 준다(원/10개 열이 없다). 하지만 "전국" 산지가격
# 페이지는 두 단위를 모두 주는데, 그 값으로 확인해 보면 원/10개 = round(원/30개 / 3)
# 관계가 10개 표본 전부 정확히 들어맞는다(예: 6433 → 2144, 6511 → 2170).
# 그래서 수도권도 같은 규칙으로 30개→10개 환산한다.
EGG_REGION_URL = "https://www.ekapepia.com/v3/price/livestock/egg/producer/region.do?menuSn=138"
CHICKEN_URL = "https://www.ekapepia.com/v3/price/livestock/chicken/distrPrice.do?menuSn=35&boardInfoNo="
# 생계유통가격 페이지 — 유통단계별가격(distrPrice, 위)과 다른 화면이다.
# distrPrice는 "생계유통(대)" 한 칸만 주지만, 이 페이지는 같은 생계유통 가격을
# 대/중/소 규격별로 나눠 준다(규격 기준: 대 1.6kg↑ · 중 1.4~1.6kg · 소 1.4kg↓,
# 페이지 하단에 명시돼 있음). 중·소는 실제 거래가 뜸해 대부분 날짜가 "-"다.
CHICKEN_GRADE_URL = "https://www.ekapepia.com/v3/price/livestock/chicken/livePrice.do?menuSn=131"
PIG_URL = "https://www.ekapepia.com/v3/price/livestock/pig/producer.do?searchCondition=&searchCondition1=&searchCondition2=&searchCondition3=&searchGubn=&searchStartDate=&searchEndDate=&ctdt=&typeCd=&searchType="
COW_URL = "https://www.ekapepia.com/v3/price/livestock/cow/distrPrice.do?menuSn=33&boardInfoNo="
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


def cell_number(value: str) -> int | None:
    match = re.search(r"(?<!\d)(\d[\d,]*)(?!\d)", value)
    return int(match.group(1).replace(",", "")) if match else None


def parse_egg(html_text: str) -> list[dict[str, int | str]]:
    parser = RowParser()
    parser.feed(html_text)
    values: dict[str, dict[str, int | str]] = {}
    for row in parser.rows:
        date = normalize_date(row[0]) if row else None
        numbers = row_numbers(row) if date else []
        # 실제로 쓰는 값은 numbers[1](XL 원/10개)뿐이라 최소 2개만 있으면 된다.
        # 예전엔 4개를 요구했는데, 갓 올라온 최신일자 행은 "전일대비" 등
        # 뒤쪽 칸이 아직 안 채워져 숫자가 2~3개뿐인 경우가 있어 그 조건 때문에
        # 최신 행이 통째로 걸러지고 그 앞의 "숫자 4개짜리" 옛날 행이 최신으로
        # 잘못 채택되는 문제가 있었다(진단 로그로 실제 확인됨).
        if date and len(numbers) >= 2:
            values.setdefault(date, {"date": date, "value": numbers[1]})
    return sorted(values.values(), key=lambda item: str(item["date"]), reverse=True)[:30]


def parse_egg_region(html_text: str) -> list[dict[str, int | str]]:
    """산지가격(권역별) 표에서 수도권 XL만 뽑아 원/10개로 환산한다.
    열 순서: [날짜, 전국, 수도권, 충청권, 전남, 전북, 경북, 경남, 제주]."""
    parser = RowParser()
    parser.feed(html_text)
    values: dict[str, dict[str, int | str]] = {}
    for row in parser.rows:
        date = normalize_date(row[0]) if row else None
        if not date or len(row) < 3:
            continue
        v30 = cell_number(row[2])  # 수도권, 원/30개
        if v30 is not None:
            values.setdefault(date, {"date": date, "value": round(v30 / 3)})
    return sorted(values.values(), key=lambda item: str(item["date"]), reverse=True)[:30]


def parse_chicken(html_text: str) -> list[dict[str, int | str]]:
    parser = RowParser()
    parser.feed(html_text)
    values: dict[str, dict[str, int | str]] = {}
    for row in parser.rows:
        date = normalize_date(row[0]) if row else None
        numbers = row_numbers(row) if date else []
        # 실제로 쓰는 값은 numbers[0](생계유통 대)뿐이라 최소 1개만 있으면 된다.
        # (egg와 동일한 이유로 4→1로 완화)
        if date and len(numbers) >= 1:
            values.setdefault(date, {"date": date, "value": numbers[0]})
    return sorted(values.values(), key=lambda item: str(item["date"]), reverse=True)[:30]


def parse_chicken_grades(html_text: str) -> list[dict[str, int | str | None]]:
    """생계유통가격을 대/중/소 규격별로. cow와 같은 패턴 — 거래 없는 규격·날짜는
    None으로 두고 latest_metric()이 최근 날짜부터 거꾸로 찾아 최신 유효값을 고른다."""
    parser = RowParser()
    parser.feed(html_text)
    values: dict[str, dict[str, int | str | None]] = {}
    for row in parser.rows:
        date = normalize_date(row[0]) if row else None
        if not date or len(row) < 4:
            continue
        item = {
            "date": date,
            "large": cell_number(row[1]),
            "medium": cell_number(row[2]),
            "small": cell_number(row[3]),
        }
        values.setdefault(date, item)
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


def parse_cow(html_text: str) -> list[dict[str, int | str | None]]:
    """소 표의 첫 세 가격 열(암송아지·수송아지·농가수취가격)을 명시적으로 읽는다."""
    parser = RowParser()
    parser.feed(html_text)
    values: dict[str, dict[str, int | str | None]] = {}
    for row in parser.rows:
        date = normalize_date(row[0]) if row else None
        if not date or len(row) < 4:
            continue
        item = {
            "date": date,
            "female_calf": cell_number(row[1]),
            "male_calf": cell_number(row[2]),
            "farm_receipt_600kg": cell_number(row[3]),
        }
        # 최신일에 거래가 없어도 날짜 행은 보존한다. 각 카드의 최신 유효값은
        # latest_metric()이 이후 날짜부터 거꾸로 찾아 선택한다.
        values.setdefault(date, item)
    return sorted(values.values(), key=lambda item: str(item["date"]), reverse=True)[:30]


def latest_metric(rows: list[dict[str, int | str | None]], key: str) -> dict[str, int | str] | None:
    for row in rows:
        value = row.get(key)
        if isinstance(value, int):
            return {"value": value, "date": str(row["date"])}
    return None


def fetch_page(url: str, parser, label: str = "") -> list[dict[str, int | str]]:
    for i, candidate in enumerate((url, *(factory(url) for factory in PROXY_FACTORIES))):
        route = "직접" if i == 0 else f"프록시{i}"
        try:
            request = Request(candidate, headers=HEADERS)
            with urlopen(request, timeout=30, context=SSL_CONTEXT) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                page = response.read().decode(charset, errors="replace")
            print(f"  [{label}] {route} 응답 {len(page)}bytes")

            # 진단용: HTMLParser가 실제로 뽑아낸 원본 행(파싱 전)을 먼저 확인.
            # 최신 날짜 행이 애초에 존재하는지, 존재한다면 숫자 칸이 몇 개인지
            # 여기서 바로 눈으로 확인할 수 있다.
            raw = RowParser()
            raw.feed(page)
            dated_raw = []
            for row in raw.rows:
                d = normalize_date(row[0]) if row else None
                if d:
                    dated_raw.append((d, len(row_numbers(row)), row[:6]))
            if dated_raw:
                dates_found = sorted({d for d, _, _ in dated_raw}, reverse=True)
                print(f"  [{label}] 날짜행 {len(dated_raw)}개, 발견된 날짜(최신 5개): {dates_found[:5]}")
                today_str = datetime.now(KST).strftime("%Y-%m-%d")
                print(f"  [{label}] 오늘({today_str}) 행 존재 여부: {any(d==today_str for d,_,_ in dated_raw)}")
                for d, n, sample in dated_raw[:3]:
                    print(f"  [{label}] 샘플 — 날짜={d} 숫자칸수={n} 원본행={sample}")
            else:
                print(f"  [{label}] 날짜로 인식된 행이 하나도 없음 (표 구조 확인 필요)")
                print(f"  [{label}] 응답 앞부분: {page[:300]!r}")

            rows = parser(page)
            print(f"  [{label}] 최종 파싱 결과: {len(rows)}건" + (f", 최신={rows[0]}" if rows else ""))
            if rows:
                return rows
        except (OSError, URLError) as exc:
            print(f"  [{label}] {route} 실패: {type(exc).__name__}: {exc}")
    return []


def load_previous() -> dict | None:
    if not OUTPUT_PATH.exists():
        return None
    try:
        return json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"이전 파일 로드 실패: {exc}")
        return None


def main() -> int:
    egg_rows = fetch_page(EGG_URL, parse_egg, "계란")
    chicken_rows = fetch_page(CHICKEN_URL, parse_chicken, "육계")
    chicken_grade_rows = fetch_page(CHICKEN_GRADE_URL, parse_chicken_grades, "육계(대중소)")
    egg_region_rows = fetch_page(EGG_REGION_URL, parse_egg_region, "계란(수도권)")
    pig_rows = fetch_page(PIG_URL, parse_pig, "양돈")
    cow_rows = fetch_page(COW_URL, parse_cow, "한우")

    prev = load_previous()
    stale: dict[str, bool] = {}

    # 넷 중 하나라도 실패했다고 전체를 통째로 안 바꾸면, 실제로는 잘 가져온
    # 나머지 항목까지 덩달아 안 갱신된다. 실패한 항목만 이전 값으로 채우고
    # 성공한 항목은 그대로 갱신한다 — 다른 수집 스크립트(fetch_egg_report,
    # fetch_market 등)와 동일한 "부분 실패해도 나머지는 살린다" 원칙.
    if not egg_rows:
        stale["egg"] = True
        egg_rows = (prev or {}).get("egg", {}).get("rows") or []
        print("  [계란] 이번 수집 실패 → 이전 데이터 유지")
    if not chicken_rows:
        stale["chicken"] = True
        chicken_rows = (prev or {}).get("chicken", {}).get("rows") or []
        print("  [육계] 이번 수집 실패 → 이전 데이터 유지")
    if not pig_rows:
        stale["pig"] = True
        pig_rows = (prev or {}).get("pig", {}).get("rows") or []
        print("  [양돈] 이번 수집 실패 → 이전 데이터 유지")
    if not cow_rows:
        stale["cow"] = True
        cow_rows = (prev or {}).get("cow", {}).get("rows") or []
        print("  [한우] 이번 수집 실패 → 이전 데이터 유지")
    # 대/중/소 규격별 가격은 기존 4종(계란·육계·양돈·한우)과 달리 있으면 좋은
    # 보조 정보다. 실패해도 전체 실행을 막지 않고, 이전 값이 있으면 그것만
    # stale로 표시해 채운다 — 이전 값도 없으면 그냥 빈 배열로 둔다(화면에서
    # "데이터 없음"으로 처리).
    if not chicken_grade_rows:
        stale["chicken_grades"] = True
        chicken_grade_rows = (prev or {}).get("chicken_grades", {}).get("rows") or []
        print("  [육계-대중소] 이번 수집 실패 → 이전 데이터 유지")
    if not egg_region_rows:
        stale["egg_region"] = True
        egg_region_rows = (prev or {}).get("egg_region", {}).get("rows") or []
        print("  [계란-수도권] 이번 수집 실패 → 이전 데이터 유지")

    if not egg_rows or not chicken_rows or not pig_rows or not cow_rows:
        print("계란·육계·양돈·한우 시세를 찾지 못했고, 이전 데이터도 없습니다.")
        return 1

    cow_items = {
        "female_calf": {"label": "암송아지(6~7개월)", "unit": "천원/마리", **(latest_metric(cow_rows, "female_calf") or {"value": None, "date": ""})},
        "male_calf": {"label": "수송아지(6~7개월)", "unit": "천원/마리", **(latest_metric(cow_rows, "male_calf") or {"value": None, "date": ""})},
        "farm_receipt_600kg": {"label": "농가수취가격(600kg)", "unit": "천원/마리", **(latest_metric(cow_rows, "farm_receipt_600kg") or {"value": None, "date": ""})},
    }
    chicken_grade_items = {
        "large":  {"label": "대", "spec": "1.6kg 이상",        **(latest_metric(chicken_grade_rows, "large")  or {"value": None, "date": ""})},
        "medium": {"label": "중", "spec": "1.4~1.6kg",          **(latest_metric(chicken_grade_rows, "medium") or {"value": None, "date": ""})},
        "small":  {"label": "소", "spec": "1.4kg 미만",          **(latest_metric(chicken_grade_rows, "small")  or {"value": None, "date": ""})},
    }
    now = datetime.now(KST)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps({
        "updated": now.strftime("%Y-%m-%d %H:%M KST"),
        "stale": stale,  # 이번 수집에 실패해 이전 데이터를 그대로 유지한 항목 표시
        "egg": {"label": "계란 산지가격", "region": "전국", "grade": "특란 (XL)", "unit": "원/10개", "latest": egg_rows[0]["value"], "rows": egg_rows},
        "egg_region": {"label": "계란 산지가격", "region": "수도권", "grade": "특란 (XL)", "unit": "원/10개", "latest": (egg_region_rows[0]["value"] if egg_region_rows else None), "rows": egg_region_rows},
        "chicken": {"label": "생계유통(대)", "unit": "원/kg", "latest": chicken_rows[0]["value"], "rows": chicken_rows},
        "chicken_grades": {"unit": "원/kg", "items": chicken_grade_items, "rows": chicken_grade_rows},
        "pig": {"label": "농가수취 평균", "unit": "원/kg", "latest": pig_rows[0]["value"], "rows": pig_rows},
        "cow": {"items": cow_items, "rows": cow_rows},
        "source_urls": {"egg": EGG_URL, "egg_region": EGG_REGION_URL, "chicken": CHICKEN_URL, "chicken_grades": CHICKEN_GRADE_URL, "pig": PIG_URL, "cow": COW_URL},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("수집 성공:", {"egg": egg_rows[0], "chicken": chicken_rows[0], "pig": pig_rows[0], "cow": cow_items})
    print("육계 대/중/소:", chicken_grade_items)
    print("계란 수도권:", egg_region_rows[0] if egg_region_rows else "없음")
    if stale:
        print("stale 표시된 항목:", list(stale.keys()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
