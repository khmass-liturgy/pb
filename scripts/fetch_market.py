#!/usr/bin/env python3
"""
야후 파이낸스 시세 수집 (서버측)
GitHub Actions에서 실행 → market/quotes.json 저장

브라우저에서 직접 호출하면 CORS 때문에 무료 프록시를 거쳐야 하고,
프록시마다 분당/월 호출 한도가 있어 앱을 열 때마다 한도가 차감된다.
서버에서는 CORS 제약이 없으므로 야후에 직접 접근한다 → 프록시 불필요.
"""

import os, sys, json, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

KST = timezone(timedelta(hours=9))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{}"

# key: 대시보드 STOCK_DATA/GRAIN_DATA/OIL_DATA/FX_DATA 의 key 와 일치
# cents: 야후가 센트/부셸로 주는 CBOT 곡물 → 대시보드에서 100으로 나눔
SYMBOLS = [
    ("kospi",    "^KS11",    False),
    ("kosdaq",   "^KQ11",    False),
    ("sp500",    "^GSPC",    False),
    ("nasdaq",   "^IXIC",    False),
    ("dow",      "^DJI",     False),
    ("nikkei",   "^N225",    False),
    ("hangseng", "^HSI",     False),
    ("corn",     "ZC=F",     True),
    ("soybean",  "ZS=F",     True),
    ("wheat",    "ZW=F",     True),
    ("soymeal",  "ZM=F",     False),
    ("brent",    "BZ=F",     False),
    ("wti",      "CL=F",     False),
    ("usdkrw",   "USDKRW=X", False),
    ("jpykrw",   "JPYKRW=X", False),
    ("eurkrw",   "EURKRW=X", False),
    ("cnykrw",   "CNYKRW=X", False),
]


def day_key(epoch_sec, gmtoffset):
    """거래소 현지 날짜(YYYY-MM-DD)"""
    return datetime.utcfromtimestamp(epoch_sec + gmtoffset).strftime("%Y-%m-%d")


def fetch_one(symbol, session):
    """야후 차트 API → (current, previous_close, closes[])"""
    r = session.get(
        CHART_URL.format(symbol),
        params={"interval": "1d", "range": "1mo", "includePrePost": "false"},
        timeout=15,
    )
    if r.status_code != 200:
        raise Exception(f"HTTP {r.status_code}")

    res = (r.json().get("chart") or {}).get("result") or []
    if not res:
        raise Exception("result 없음")
    res = res[0]
    meta = res.get("meta") or {}

    cur = meta.get("regularMarketPrice")
    if cur is None:
        raise Exception("regularMarketPrice 없음")

    # ① meta.previousClose = 직전 거래일 종가 (range 와 무관하게 정확)
    prev = meta.get("previousClose")
    if not isinstance(prev, (int, float)) or prev <= 0:
        prev = None

    # 일봉 종가 배열 (추세용) + 날짜 경계 폴백
    ts = res.get("timestamp") or []
    quote = ((res.get("indicators") or {}).get("quote") or [{}])[0]
    cl = quote.get("close") or []
    gmt = meta.get("gmtoffset") or 0

    pairs = [(day_key(t, gmt), c) for t, c in zip(ts, cl) if c is not None]
    closes = [c for _, c in pairs]

    prev_by_day = None
    if len(pairs) >= 2:
        last_day = pairs[-1][0]
        for d, c in reversed(pairs[:-1]):
            if d != last_day:
                prev_by_day = c
                break

    if prev is None:
        prev = prev_by_day
    if prev is None:
        prev = meta.get("chartPreviousClose") or cur

    # ② 검증: 등락률 ±40% 초과면 비정상 → 더 그럴듯한 후보로 교체
    def err(p):
        return abs(cur / p - 1) if p and p > 0 else 99.0

    if err(prev) > 0.4:
        for alt in (prev_by_day, meta.get("chartPreviousClose")):
            if isinstance(alt, (int, float)) and alt > 0 and err(alt) < err(prev):
                prev = alt

    return cur, prev, closes[-12:]


def main():
    now = datetime.now(KST)
    session = requests.Session()
    session.headers.update(HEADERS)

    quotes, failed = {}, []

    print(f"📈 야후 시세 수집 시작 ({now.strftime('%Y-%m-%d %H:%M KST')})\n")

    for key, symbol, cents in SYMBOLS:
        try:
            cur, prev, closes = fetch_one(symbol, session)
            scale = 100.0 if cents else 1.0
            quotes[key] = {
                "symbol":  symbol,
                "current": round(cur / scale, 2),
                "prev":    round(prev / scale, 2),
                "trend":   [round(c / scale, 2) for c in closes],
            }
            pct = (cur - prev) / prev * 100 if prev else 0
            arrow = "▲" if pct > 0 else ("▼" if pct < 0 else "─")
            print(f"  ✅ {key:9s} {symbol:10s} {cur/scale:>12,.2f}  {arrow}{abs(pct):.2f}%")
        except Exception as e:
            failed.append(key)
            print(f"  ❌ {key:9s} {symbol:10s} {e}")
        time.sleep(0.4)  # 야후 과호출 방지

    # 기존 파일이 있으면 실패 항목은 이전 값 유지 (되돌아가지 않게)
    out_path = Path("market/quotes.json")
    if failed and out_path.exists():
        try:
            old = json.loads(out_path.read_text(encoding="utf-8")).get("quotes", {})
            for k in failed:
                if k in old:
                    quotes[k] = old[k]
                    quotes[k]["stale"] = True
                    print(f"  ⚡ {k}: 이전 값 유지")
        except Exception as e:
            print(f"  ⚠️ 기존 파일 병합 실패: {e}")

    if not quotes:
        print("\n❌ 수집된 항목이 없어 저장하지 않습니다.")
        sys.exit(1)

    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps({
        "updated":  now.strftime("%Y-%m-%d %H:%M KST"),
        "updatedTs": int(now.timestamp()),
        "ok":       len(SYMBOLS) - len(failed),
        "total":    len(SYMBOLS),
        "quotes":   quotes,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✅ market/quotes.json 저장 — 성공 {len(SYMBOLS)-len(failed)}/{len(SYMBOLS)}")


if __name__ == "__main__":
    main()
