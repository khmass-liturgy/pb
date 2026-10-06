#!/usr/bin/env python3
"""사료원료 곡물(옥수수·대두·대두박·밀) 국제 선물 가격 동향과 1·3개월 전망 — 유료서비스 「사료곡물 가격동향·전망」용.

야후 파이낸스의 CBOT 선물(ZC=F 옥수수, ZS=F 대두, ZM=F 대두박, ZW=F 밀)과 대외 변수(원/달러, 달러지수,
브렌트유, 건화물 운임 ETF BDRY)의 10년 월봉·2년 일봉을 받아 지표를 계산하고, 같은 저장소의
grain_quality/latest.json(주요 산지 기상 흐름)을 공급 요인으로 결합해 `grain_price/latest.json` 을 만든다.

전망은 통계 모델이 아니라 "투명한 가중 점수"다. 요인 6개(추세·가격 위치·계절성·달러·유가·산지 기상)를
각각 -1~+1로 점수화해 가중합하고, 그 점수로 방향을 정한 뒤 최근 변동성(σ)으로 폭을 준다. 어떤 요인이 얼마나
작용했는지가 JSON에 그대로 남아 화면에서 설명된다. 투자·구매 판단용이 아니라 참고용이다.

모든 시각은 KST. 부분 실패(한 종목 수신 실패)는 이전 JSON 값을 지우지 않고 그 종목만 stale 로 표시한다.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import requests

KST = timezone(timedelta(hours=9))
OUT_PATH = Path("grain_price/latest.json")
GRAIN_QUALITY = Path("grain_quality/latest.json")
CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
}

# key: (야후 심볼, 이름, 단위 표기, 센트로 오는지(÷100), 톤 환산 계수, 톤 환산 단위)
# 곡물 선물은 센트/부셸(대두박은 $/short ton). 1톤 = 부셸 환산계수만큼의 부셸.
GRAINS = {
    "corn":    ("ZC=F", "옥수수", "$/부셸", True, 39.3683, "bu"),
    "soymeal": ("ZM=F", "대두박", "$/숏톤", False, 1.10231, "st"),
    "soybean": ("ZS=F", "대두", "$/부셸", True, 36.7437, "bu"),
    "wheat":   ("ZW=F", "밀", "$/부셸", True, 36.7437, "bu"),
}
MACRO = {
    "usdkrw": ("USDKRW=X", "원/달러 환율", "원"),
    "dxy":    ("DX-Y.NYB", "달러지수", "pt"),
    "brent":  ("BZ=F", "브렌트유", "$/배럴"),
    "bdry":   ("BDRY", "건화물 운임(BDRY ETF)", "$"),
}
# 산지 기상 신호를 어느 곡물에 얼마나 반영할지: (지역키, 핵심 달 집합) — 핵심 달에는 가중 1, 그 밖은 0.15
REGION_SEASON = {
    "corn":    [("us", {6, 7, 8, 9}), ("br", {11, 12, 1, 2, 3}), ("ar", {12, 1, 2, 3})],
    "soybean": [("us", {6, 7, 8, 9}), ("br", {11, 12, 1, 2, 3}), ("ar", {12, 1, 2, 3})],
    "soymeal": [("us", {6, 7, 8, 9}), ("br", {11, 12, 1, 2, 3}), ("ar", {12, 1, 2, 3})],
    "wheat":   [("eu", {4, 5, 6, 7}), ("ru", {4, 5, 6, 7}), ("us", {4, 5, 6, 7}), ("ar", {10, 11, 12})],
}
REGION_NAME = {"us": "미국", "br": "브라질", "ar": "아르헨티나", "eu": "유럽", "ru": "러시아"}
WEIGHTS = {"momentum": 0.30, "position": 0.15, "season": 0.15, "dollar": 0.10, "oil": 0.10, "weather": 0.20}
LABELS = {"momentum": "가격 추세", "position": "가격 위치(고점·저점)", "season": "계절성", "dollar": "달러 흐름",
          "oil": "국제 유가", "weather": "산지 기상"}


def clamp(x, lo=-1.0, hi=1.0):
    return max(lo, min(hi, x))


def pct(a, b):
    return (a / b - 1.0) if b else 0.0


def fetch(symbol: str, rng: str, interval: str):
    r = requests.get(CHART_URL.format(symbol), params={"interval": interval, "range": rng, "includePrePost": "false"},
                     headers=HEADERS, timeout=25)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    off = (res.get("meta") or {}).get("gmtoffset", 0)
    ts, close = res["timestamp"], res["indicators"]["quote"][0]["close"]
    rows = [(datetime.fromtimestamp(t + off, timezone.utc).strftime("%Y-%m-%d"), c) for t, c in zip(ts, close) if c is not None]
    return rows


def weekly(rows):
    """일봉 → 주 마지막 종가(ISO 주)."""
    out = {}
    for d, c in rows:
        dt = datetime.strptime(d, "%Y-%m-%d")
        out[dt.isocalendar()[:2]] = (d, c)
    return [out[k] for k in sorted(out)]


def sma(vals, n):
    return sum(vals[-n:]) / n if len(vals) >= n else None


def change(rows, days):
    """days 달력일 전 종가 대비 변화율."""
    if not rows:
        return None
    last_d = datetime.strptime(rows[-1][0], "%Y-%m-%d")
    target = last_d - timedelta(days=days)
    base = None
    for d, c in rows:
        if datetime.strptime(d, "%Y-%m-%d") <= target:
            base = c
        else:
            break
    return pct(rows[-1][1], base) if base else None


def annual_vol(rows, n=60):
    cl = [c for _, c in rows][-(n + 1):]
    if len(cl) < 20:
        return None
    rets = [math.log(cl[i] / cl[i - 1]) for i in range(1, len(cl)) if cl[i - 1] > 0 and cl[i] > 0]
    return statistics.pstdev(rets) * math.sqrt(252) if len(rets) > 5 else None


def seasonality(monthly, month):
    """같은 달에 시작해 1·3개월 뒤 평균 변화율과 상승 비율(10년 월봉)."""
    by = {}
    for i, (d, c) in enumerate(monthly):
        by[d[:7]] = (i, c)
    r1, r3 = [], []
    for ym, (i, c) in by.items():
        if int(ym[5:7]) != month:
            continue
        if i + 1 < len(monthly):
            r1.append(pct(monthly[i + 1][1], c))
        if i + 3 < len(monthly):
            r3.append(pct(monthly[i + 3][1], c))
    return {"n": len(r3), "avg1": statistics.mean(r1) if r1 else None, "avg3": statistics.mean(r3) if r3 else None,
            "up3": (sum(1 for x in r3 if x > 0) / len(r3)) if r3 else None}


def region_stress(gq, key):
    r = (gq.get("regions") or {}).get(key) or {}
    now = r.get("now") or {}
    dry, wet = now.get("dry"), now.get("wet")
    if not isinstance(dry, (int, float)) and not isinstance(wet, (int, float)):
        return None
    return max(dry or 0, wet or 0), ("가뭄" if (dry or 0) >= (wet or 0) else "과습")


def build_grain(key, series, macro_series, gq, month):
    sym, name, unit, cents, factor, kind = GRAINS[key]
    daily = series["daily"]
    monthly = series["monthly"]
    scale = 100.0 if cents else 1.0
    closes = [c / scale for _, c in daily]
    last = closes[-1]
    ma50, ma200 = sma(closes, 50), sma(closes, 200)
    hi52 = max(closes[-252:]); lo52 = min(closes[-252:])
    mclose = [c / scale for _, c in monthly]
    below = sum(1 for c in mclose if c <= last)
    pctile = below / len(mclose) * 100 if mclose else 50
    ch = {k: change([(d, c / scale) for d, c in daily], v) for k, v in (("1w", 7), ("1m", 30), ("3m", 91), ("6m", 182), ("1y", 365))}
    vol = annual_vol(daily) or 0.25
    s1, s3 = vol * math.sqrt(21 / 252), vol * math.sqrt(63 / 252)

    # ── 요인 점수 ──
    comp, why = {}, {}
    m1 = clamp(pct(last, ma50) / 0.06) if ma50 else 0
    m2 = clamp(pct(ma50, ma200) / 0.08) if ma50 and ma200 else 0
    m3 = clamp((ch["3m"] or 0) / 0.12)
    comp["momentum"] = (m1 + m2 + m3) / 3
    why["momentum"] = (f"50일 이동평균 {'위' if ma50 and last >= ma50 else '아래'}, "
                       f"3개월 {((ch['3m'] or 0) * 100):+.1f}%" + (", 장기(200일)선 위" if ma200 and last >= ma200 else ", 장기(200일)선 아래" if ma200 else ""))
    comp["position"] = clamp(-(pctile - 50) / 50) * 0.8
    why["position"] = f"최근 10년 가격 중 하위 {pctile:.0f}% 수준(52주 범위 {lo52:.2f}~{hi52:.2f})" if pctile < 50 else f"최근 10년 가격 중 상위 {100 - pctile:.0f}% 수준(52주 범위 {lo52:.2f}~{hi52:.2f})"
    se = seasonality(monthly, month)
    comp["season"] = clamp((se["avg3"] or 0) / 0.05) if se["n"] >= 7 and se["avg3"] is not None else 0
    why["season"] = (f"지난 {se['n']}년 {month}월 이후 3개월 평균 {se['avg3'] * 100:+.1f}%, 상승한 해 {se['up3'] * 100:.0f}%"
                     if se["n"] >= 7 and se["avg3"] is not None else "계절 자료 부족")
    dxy3 = change(macro_series["dxy"]["daily"], 91) if macro_series.get("dxy") else None
    comp["dollar"] = clamp(-(dxy3 or 0) / 0.04)
    why["dollar"] = (f"달러지수 3개월 {dxy3 * 100:+.1f}% → 달러 {'강세(원자재 가격에 부담)' if dxy3 > 0.005 else '약세(원자재 가격에 우호)' if dxy3 < -0.005 else '보합'}"
                     if dxy3 is not None else "자료 없음")
    oil3 = change(macro_series["brent"]["daily"], 91) if macro_series.get("brent") else None
    comp["oil"] = clamp((oil3 or 0) / 0.20)
    why["oil"] = (f"브렌트유 3개월 {oil3 * 100:+.1f}% → 에탄올·비료·운송비 {'상승 압력' if oil3 > 0.02 else '하락 압력' if oil3 < -0.02 else '보합'}"
                  if oil3 is not None else "자료 없음")
    # 산지 기상
    wsum, wtot, wdet = 0.0, 0.0, []
    for rk, months in REGION_SEASON[key]:
        st = region_stress(gq, rk)
        if not st:
            continue
        score, kind_ = st
        w = 1.0 if month in months else 0.15
        s = clamp((score - 1.0) / 2.0, 0, 1)
        wsum += w * s
        wtot += w
        wdet.append({"region": rk, "name": REGION_NAME[rk], "stress": round(score, 2), "kind": kind_,
                     "in_season": month in months})
    comp["weather"] = clamp(wsum / wtot * 1.6) if wtot else 0
    hot = [d for d in wdet if d["stress"] >= 2]
    why["weather"] = ("기상 부담 신호: " + ", ".join(f"{d['name']} {d['kind']} {d['stress']:.1f}점" + ("" if d["in_season"] else "(생육·수확 핵심기 아님, 반영 낮춤)") for d in hot)
                      if hot else "주요 산지에서 뚜렷한 기상 이상 신호 없음")

    score = sum(WEIGHTS[k] * comp[k] for k in WEIGHTS)
    direction = "up" if score > 0.18 else "down" if score < -0.18 else "flat"
    nz = [v for v in comp.values() if abs(v) > 0.12]
    agree = (sum(1 for v in nz if (v > 0) == (score > 0)) / len(nz)) if nz else 0
    conf = "높음" if agree >= 0.8 and abs(score) >= 0.3 else "보통" if agree >= 0.6 else "낮음"
    drift3, drift1 = score * 0.5 * s3, score * 0.5 * s1
    fx = (macro_series.get("usdkrw") or {}).get("daily")
    usdkrw = fx[-1][1] if fx else None
    # $/부셸 × (부셸/톤) = $/톤, $/숏톤 × 1.10231 = $/톤 → × 환율 ÷ 1000 = 원/kg (국제 선물 기준, 운임·프리미엄 미포함)
    krw_kg = last * factor * usdkrw / 1000 if usdkrw else None
    return {
        "name": name, "symbol": sym, "unit": unit,
        "last": round(last, 2), "date": daily[-1][0], "krw_per_kg": round(krw_kg) if krw_kg else None,
        "change": {k: (round(v * 100, 1) if v is not None else None) for k, v in ch.items()},
        "ma50": round(ma50, 2) if ma50 else None, "ma200": round(ma200, 2) if ma200 else None,
        "hi52": round(hi52, 2), "lo52": round(lo52, 2), "pos52": round((last - lo52) / (hi52 - lo52) * 100) if hi52 > lo52 else 50,
        "pctile10y": round(pctile), "vol": round(vol * 100, 1),
        "weekly": [[d, round(c / scale, 2)] for d, c in weekly(daily)[-104:]],
        "forecast": {
            "score": round(score * 100), "direction": direction, "confidence": conf,
            "m1": {"mid": round(last * (1 + drift1), 2), "lo": round(last * (1 + drift1 - s1), 2), "hi": round(last * (1 + drift1 + s1), 2), "pct": round(drift1 * 100, 1), "sigma": round(s1 * 100, 1)},
            "m3": {"mid": round(last * (1 + drift3), 2), "lo": round(last * (1 + drift3 - s3), 2), "hi": round(last * (1 + drift3 + s3), 2), "pct": round(drift3 * 100, 1), "sigma": round(s3 * 100, 1)},
            "drivers": [{"key": k, "label": LABELS[k], "weight": WEIGHTS[k], "score": round(comp[k] * 100), "text": why[k]} for k in WEIGHTS],
            "weather": wdet,
        },
    }


def fetch_news():
    items, seen = [], set()
    for q in ("국제 곡물 가격 옥수수 대두 when:7d", "곡물 선물 가격 전망 사료 when:14d"):
        try:
            url = "https://news.google.com/rss/search?q=" + quote(q) + "&hl=ko&gl=KR&ceid=KR:ko"
            r = requests.get(url, headers=HEADERS, timeout=25)
            r.raise_for_status()
            for it in ET.fromstring(r.content).iter("item"):
                title = (it.findtext("title") or "").strip()
                key = title[:24]
                if not title or key in seen:
                    continue
                seen.add(key)
                items.append({"title": title, "link": it.findtext("link") or "", "date": it.findtext("pubDate") or "",
                              "source": (it.findtext("source") or "").strip()})
        except Exception as exc:
            print(f"::warning::뉴스 수신 실패({q}): {exc}")
    return items[:8]


def main() -> int:
    prev = {}
    if OUT_PATH.exists():
        try:
            prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
    gq = {}
    if GRAIN_QUALITY.exists():
        try:
            gq = json.loads(GRAIN_QUALITY.read_text(encoding="utf-8"))
        except Exception:
            gq = {}

    raw, failed = {}, []
    for key, spec in list(GRAINS.items()) + [(k, (v[0],)) for k, v in MACRO.items()]:
        sym = spec[0]
        try:
            raw[key] = {"daily": fetch(sym, "2y", "1d"), "monthly": fetch(sym, "10y", "1mo")}
            print(f"{key}: 일봉 {len(raw[key]['daily'])} · 월봉 {len(raw[key]['monthly'])}")
        except Exception as exc:
            failed.append(key)
            print(f"::warning::{key}({sym}) 수신 실패: {type(exc).__name__}: {exc}")
    macro_raw = {k: raw[k] for k in MACRO if k in raw}
    month = datetime.now(KST).month
    out = {"updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"), "grains": {}, "macro": {}, "stale": {}}
    for key in GRAINS:
        if key in raw:
            out["grains"][key] = build_grain(key, raw[key], macro_raw, gq, month)
        elif (prev.get("grains") or {}).get(key):
            out["grains"][key] = prev["grains"][key]
            out["stale"][key] = True
    for key, (sym, name, unit) in MACRO.items():
        if key in raw:
            d = raw[key]["daily"]
            out["macro"][key] = {"name": name, "unit": unit, "last": round(d[-1][1], 2), "date": d[-1][0],
                                 "change": {"1m": round((change(d, 30) or 0) * 100, 1), "3m": round((change(d, 91) or 0) * 100, 1),
                                            "1y": round((change(d, 365) or 0) * 100, 1)},
                                 "vol": round((annual_vol(d) or 0) * 100, 1),
                                 "weekly": [[a, round(b, 2)] for a, b in weekly(d)[-104:]]}
        elif (prev.get("macro") or {}).get(key):
            out["macro"][key] = prev["macro"][key]
            out["stale"][key] = True
    out["news"] = fetch_news() or prev.get("news", [])
    out["weights"] = {k: {"label": LABELS[k], "weight": WEIGHTS[k]} for k in WEIGHTS}
    if not out["grains"]:
        print("곡물 자료를 하나도 못 받음")
        return 1
    # 변경 없을 때(같은 거래일 종가) 불필요한 커밋 방지
    def core(d):
        return {k: v for k, v in d.items() if k != "updated"}
    if prev and core(prev) == core(out):
        print("변경 없음")
        return 0
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("저장:", OUT_PATH, OUT_PATH.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
