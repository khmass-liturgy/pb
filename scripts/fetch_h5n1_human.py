#!/usr/bin/env python3
"""WHO 「H5N1 사람 감염 누적 확진 사례(국가별·연도별 확진자·사망자)」 → h5n1_human/latest.json

AI 탭의 「사람 감염(WHO)」 화면이 읽는다. WHO(세계보건기구) 세계인플루엔자프로그램(GIP)이 2003년 이후 WHO에 보고된
실험실 확진 A(H5N1) 사람 감염을 국가별·연도별 확진자(cases, 사망자 포함)와 사망자(deaths)로 정리해 PDF 표로 올린다.

WHO 페이지 주소에 날짜가 들어가고(…--2003-2026--6-september-2026) 갱신 때마다 바뀌어 고정 주소가 없다. 그래서
  ① WHO 서태평양지역사무소의 주간 조류인플루엔자 속보(…/wpro---documents/…/avian-influenza/ai_YYYYMMDD.pdf, 최근 약 6주를 거꾸로 확인)가
     링크해 둔 「최신 누적표」 WHO 게시 페이지 주소를 찾고,
  ② 그 페이지의 PDF 링크로 표를 받아 pdfplumber 로 읽는다(글자가 들어 있는 PDF라 OCR 필요 없음).
표의 합계 행과 국가별 합이 모든 기간에서 같을 때만 쓰고, 어긋나면 이전 자료를 그대로 둔다(수집 실패가 자료를 지우지 않는다).

실행: python scripts/fetch_h5n1_human.py              (최신 표 찾기 → 읽기 → 저장)
      python scripts/fetch_h5n1_human.py --pdf 파일.pdf   (내려받기 없이 로컬 PDF로 시험)
모든 시각은 KST.
"""

from __future__ import annotations

import html
import io
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
OUT = Path("h5n1_human/latest.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; pb-h5n1-who/1.0)"}
WPRO = "https://cdn.who.int/media/docs/default-source/wpro---documents/emergency/surveillance/avian-influenza/ai_{d}.pdf"
TABLE_PAGE_RE = re.compile(r"https://www\.who\.int/publications/m/item/cumulative-number-of-confirmed-human-cases-for-avian-influenza-a\(h5n1\)[^\s\"'<>]*")
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"], 1)}

KO = {
    "Australia": "호주", "Azerbaijan": "아제르바이잔", "Bangladesh": "방글라데시", "Cambodia": "캄보디아", "Canada": "캐나다", "Chile": "칠레",
    "China": "중국", "Djibouti": "지부티", "Ecuador": "에콰도르", "Egypt": "이집트", "India": "인도", "Indonesia": "인도네시아", "Iraq": "이라크",
    "Lao People's Democratic Republic": "라오스", "Mexico": "멕시코", "Myanmar": "미얀마", "Nepal": "네팔", "Nigeria": "나이지리아",
    "Pakistan": "파키스탄", "Spain": "스페인", "Thailand": "태국", "Turkey": "튀르키예", "Türkiye": "튀르키예",
    "United Kingdom of Great Britain and Northern Ireland": "영국", "United States of America": "미국", "Viet Nam": "베트남",
}


# ── PDF 표 읽기 ─────────────────────────────────────────────────────────────
def _clean_name(n) -> str | None:
    if not n:
        return None
    n = re.sub(r"[\*†‡]+", "", str(n).replace("\n", " ")).strip()
    return re.sub(r"\s+", " ", n) or None


def _int(c) -> int | None:
    c = ("" if c is None else str(c)).strip()
    if c == "":
        return 0            # 빈 칸은 0(국가 합계로 검산한다)
    return int(c) if re.fullmatch(r"\d+", c) else None


def parse_pdf(data: bytes) -> dict:
    import pdfplumber
    years: dict[int, dict[str, list[int]]] = {}       # year -> country -> [cases, deaths]
    period_total: dict[str, list[int]] = {}           # '2003-2009' -> [cases, deaths] (합계 행)
    period_country: dict[str, dict[str, list[int]]] = {}
    as_of = None
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for pi, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            m = re.search(r"as\s*of\s*(\d{1,2})\s*([A-Za-z]+)\s*(\d{4})", text)
            if m and m.group(2).lower() in MONTHS:
                as_of = date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))
            tables = page.extract_tables()
            if not tables:
                continue
            tb = tables[0]
            header = tb[0]
            labels = [re.sub(r"[\*†\s].*", "", str(h)) for h in header[1:] if h]       # '2003-2009*\ncases deaths' → '2003-2009'
            first_data = True
            for row in tb[1:]:
                name = _clean_name(row[0])
                cells = row[1:]
                if name is None and first_data:
                    name = "Australia"          # 첫 칸이 비는 첫 행 = 알파벳 첫 나라(PDF 표 추출이 이름을 놓침)
                first_data = False
                if name is None:
                    continue
                if name == "Total":
                    pairs = []
                    for c in cells:
                        if c:
                            pairs += [int(x) for x in str(c).split()]
                    if len(pairs) >= 2 * len(labels):
                        for i, lb in enumerate(labels):
                            period_total.setdefault(lb, pairs[2 * i:2 * i + 2])
                    continue
                vals = [_int(c) for c in cells if c is not None]
                if len(vals) < 2 * len(labels) or any(v is None for v in vals[:2 * len(labels)]):
                    continue
                for i, lb in enumerate(labels):
                    cd = vals[2 * i:2 * i + 2]
                    if re.fullmatch(r"\d{4}", lb):
                        if pi == 0 and int(lb) <= 2024:
                            continue
                        years.setdefault(int(lb), {})[name] = cd
                    elif pi == 0:
                        period_country.setdefault(lb, {})[name] = cd
    if as_of is None or not years:
        raise ValueError("표에서 기준일이나 연도별 값을 찾지 못했습니다.")

    # 검산: 기간별로 (연도별 합) = 합계 행, 1페이지 기간 열 = 합계 행
    problems = []
    for lb, tot in period_total.items():
        if re.fullmatch(r"\d{4}-\d{4}", lb):
            a, b = map(int, lb.split("-"))
            ys = [y for y in years if a <= y <= b]
            sc = sum(years[y][n][0] for y in ys for n in years[y]); sd = sum(years[y][n][1] for y in ys for n in years[y])
            if len(ys) == b - a + 1 and [sc, sd] != tot:
                problems.append(f"{lb}: 연도별 합 {sc}/{sd} ≠ 합계 {tot}")
            pc = period_country.get(lb)
            if pc and [sum(v[0] for v in pc.values()), sum(v[1] for v in pc.values())] != tot:
                problems.append(f"{lb}: 1쪽 국가 합 ≠ 합계 {tot}")
        elif re.fullmatch(r"\d{4}", lb) and int(lb) in years:
            y = int(lb)
            if [sum(v[0] for v in years[y].values()), sum(v[1] for v in years[y].values())] != tot:
                problems.append(f"{lb}: 국가 합 ≠ 합계 {tot}")
    if problems:
        raise ValueError("검산 실패: " + "; ".join(problems))
    if not period_total:
        raise ValueError("합계 행을 찾지 못해 검산할 수 없습니다.")
    return {"as_of": as_of, "years": years}


def build(parsed: dict) -> dict:
    years = sorted(parsed["years"])
    ylist = list(range(years[0], years[-1] + 1))
    names: list[str] = []
    for y in ylist:
        for n in parsed["years"].get(y, {}):
            if n not in names:
                names.append(n)
    countries = []
    for n in names:
        cases = [parsed["years"].get(y, {}).get(n, [0, 0])[0] for y in ylist]
        deaths = [parsed["years"].get(y, {}).get(n, [0, 0])[1] for y in ylist]
        if sum(cases) == 0:
            continue
        countries.append({"name": n, "ko": KO.get(n, n), "cases": cases, "deaths": deaths, "total_cases": sum(cases), "total_deaths": sum(deaths)})
    countries.sort(key=lambda c: (-c["total_deaths"], -c["total_cases"], c["name"]))
    return {
        "as_of": parsed["as_of"].isoformat(), "years": ylist, "countries": countries,
        "year_cases": [sum(c["cases"][i] for c in countries) for i in range(len(ylist))],
        "year_deaths": [sum(c["deaths"][i] for c in countries) for i in range(len(ylist))],
        "total_cases": sum(c["total_cases"] for c in countries), "total_deaths": sum(c["total_deaths"] for c in countries),
    }


# ── 최신 표 찾기 ────────────────────────────────────────────────────────────
def find_table_page() -> str | None:
    import pdfplumber
    import requests
    today = datetime.now(timezone.utc).date()
    for back in range(0, 45):
        d = (today - timedelta(days=back)).strftime("%Y%m%d")
        try:
            r = requests.get(WPRO.format(d=d), headers=HEADERS, timeout=40)
        except Exception:  # noqa: BLE001
            continue
        if r.status_code != 200 or not r.content.startswith(b"%PDF"):
            continue
        links = set()
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            for pg in pdf.pages:
                for a in pg.annots or []:
                    u = a.get("uri") or (a.get("data") or {}).get("URI")
                    if u:
                        links.add(u.decode("latin1") if isinstance(u, bytes) else u)
        for u in sorted(links):
            if TABLE_PAGE_RE.fullmatch(u):
                print(f"속보 ai_{d}.pdf 가 가리키는 누적표 페이지: {u}")
                return u
    return None


def table_pdf_url(page_url: str) -> str | None:
    import requests
    r = requests.get(page_url, headers=HEADERS, timeout=40)
    r.raise_for_status()
    for m in re.findall(r"https://cdn\.who\.int/media/docs/default-source/influenza/h5n1-human-case-cumulative-table/[^\"'<>\s]+?\.pdf[^\"'<>\s]*", r.text):
        return html.unescape(m).replace("&#39;", "").split("&#")[0]
    return None


def main() -> int:
    prev = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else None
    if "--pdf" in sys.argv:
        data, page_url, pdf_url = Path(sys.argv[sys.argv.index("--pdf") + 1]).read_bytes(), None, None
    else:
        try:
            import requests
            page_url = find_table_page()
            if not page_url:
                print("WHO 누적표 페이지를 찾지 못했습니다 — 이전 자료를 그대로 둡니다.")
                return 0
            if prev and prev.get("page_url") == page_url:
                print("새 누적표 없음.")
                return 0
            pdf_url = table_pdf_url(page_url)
            if not pdf_url:
                print("누적표 PDF 링크를 찾지 못했습니다 — 이전 자료를 그대로 둡니다.")
                return 0
            r = requests.get(pdf_url, headers=HEADERS, timeout=90)
            r.raise_for_status()
            data = r.content
        except Exception as e:  # noqa: BLE001
            print(f"누적표 내려받기 실패({type(e).__name__}: {e}) — 이전 자료를 그대로 둡니다.")
            return 0
    try:
        out = build(parse_pdf(data))
    except Exception as e:  # noqa: BLE001
        print(f"표 읽기 실패({type(e).__name__}: {e}) — 이전 자료를 그대로 둡니다.")
        return 1 if "--pdf" in sys.argv else 0
    if prev and prev.get("as_of") and out["as_of"] < prev["as_of"]:
        print("받은 표가 이전 자료보다 오래됐습니다 — 이전 자료를 그대로 둡니다.")
        return 0
    result = {
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
        "source": "WHO/GIP — Cumulative number of confirmed human cases for avian influenza A(H5N1) reported to WHO",
        "page_url": page_url or (prev or {}).get("page_url"), "pdf_url": pdf_url or (prev or {}).get("pdf_url"),
        "notes": [
            "WHO는 실험실에서 확진된 사례만 집계하며, 확진자 수(cases)에는 사망자(deaths)가 포함돼 있다. 모든 날짜는 발병 시점 기준이다.",
            "국가는 사례를 보고한 나라이며 노출이 일어난 나라와 다를 수 있다.",
            "일부 사례는 무증상 감염자의 검출을 포함한다. 미국의 2024~2025년 사례는 A(H5)로 보고된 것을 포함한다.",
        ],
        **out,
    }
    new = json.dumps(result, ensure_ascii=False, indent=1) + "\n"
    old = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    strip = lambda s: re.sub(r'"updated": "[^"]*"', "", s)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if strip(new) != strip(old):
        OUT.write_text(new, encoding="utf-8")
        print(f"갱신: 기준 {out['as_of']} · {len(out['countries'])}개국 · 확진 {out['total_cases']}명 · 사망 {out['total_deaths']}명")
    else:
        print("변경 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
