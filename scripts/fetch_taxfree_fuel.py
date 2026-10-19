#!/usr/bin/env python3
"""한국석유공사 오피넷 「면세유 평균판매가격(전국)」 수집.

오피넷 면세유평균판매가격 페이지(dopOsPdrgTaxfreeSelect.do)가 보여 주는 최근 이틀치 전국 평균(휘발유·자동차용경유·실내등유, 원/리터)과
전일대비를 읽어 taxfree_fuel/latest.json 에 저장한다.

※ 지역(시·도)별 면세유 평균은 오피넷이 2026년 2월까지만 공개하고 3월부터는 공개하지 않는다(표본 수 제한 — 해당 페이지 안내).
   그래서 이 스크립트는 전국 평균만 다룬다.
※ 가져오지 못하면 이전 값을 그대로 둔다(부분 실패가 좋은 자료를 지우지 않는 이 저장소의 규칙).
"""
import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
URL = "https://www.opinet.co.kr/user/dopospdrg/dopOsPdrgTaxfreeSelect.do"
OUT = Path("taxfree_fuel/latest.json")
KEYS = ["gasoline", "diesel", "kerosene"]          # 휘발유 · 자동차용경유 · 실내등유


def fetch_html() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (compatible; pb-dashboard)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def parse(html: str) -> dict:
    t = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", html)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"&nbsp;", " ", t)
    t = re.sub(r"\s+", " ", t)
    rows = re.findall(r"(\d{4})년\s?(\d{2})월\s?(\d{2})일\s+(\d{3,4}(?:\.\d+)?)\s+(\d{3,4}(?:\.\d+)?)\s+(\d{3,4}(?:\.\d+)?)", t)
    if len(rows) < 2:
        raise ValueError(f"가격 행을 찾지 못함({len(rows)}행)")
    diff = re.search(r"전일대비\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)", t)

    def day(r):
        return f"{r[0]}-{r[1]}-{r[2]}"

    prev, cur = sorted(rows[:2], key=day)                 # 표에는 이전 날짜가 위에 있다
    prices = {k: float(v) for k, v in zip(KEYS, cur[3:6])}
    before = {k: float(v) for k, v in zip(KEYS, prev[3:6])}
    for v in list(prices.values()) + list(before.values()):
        if not (500 <= v <= 4000):
            raise ValueError(f"가격이 비정상 범위: {v}")
    chg = ({k: float(v) for k, v in zip(KEYS, diff.groups())} if diff
           else {k: round(prices[k] - before[k], 2) for k in KEYS})
    return {"date": day(cur), "prev_date": day(prev), "prices": prices, "prev": before, "diff": chg}


def main() -> int:
    prev_json = None
    if OUT.exists():
        try:
            prev_json = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            prev_json = None
    try:
        data = parse(fetch_html())
    except Exception as exc:
        print(f"::warning::면세유 평균가 수집 실패: {type(exc).__name__}: {exc}")
        return 0 if prev_json else 1                       # 이전 값이 있으면 그대로 두고 통과
    out = {
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
        "scope": "전국",
        "unit": "원/리터",
        "source": "한국석유공사 오피넷 면세유 평균판매가격",
        "url": "https://www.opinet.co.kr/user/dopospdrg/dopOsPdrgTaxfreeSelect.do",
        "note": "지역(시·도)별 면세유 평균은 오피넷이 2026년 2월까지만 공개해 전국 평균만 제공합니다.",
        **data,
    }
    if prev_json and {k: v for k, v in prev_json.items() if k != "updated"} == {k: v for k, v in out.items() if k != "updated"}:
        print("변경 없음")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"저장: {out['date']} 경유 {out['prices']['diesel']} · 휘발유 {out['prices']['gasoline']} · 등유 {out['prices']['kerosene']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
