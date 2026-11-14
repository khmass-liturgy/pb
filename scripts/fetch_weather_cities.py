#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
국내 주요 지점 날씨 예보(MET Norway / Yr.no)를 서버(GitHub Actions)에서 미리 받아
weather/kr_forecast.json 으로 커밋한다.

왜 이렇게 하나:
- 날씨 탭은 원래 브라우저가 기상 API(해외)를 직접 부른다. 그런데 일부 농가
  네트워크(모바일·사내망)에서는 그 API와 공개 CORS 프록시가 전부 막혀
  "날씨 정보를 가져오지 못했습니다"가 반복된다.
- 사이트의 다른 데이터처럼 서버가 미리 받아 저장소에 커밋해 두면, 브라우저는 이미
  잘 읽히는 경로(raw GitHub / Firebase getPublicContent)로 가져올 수 있다.
- 농장 위치가 정확히 일치하진 않으므로, 브라우저는 실시간 호출이 모두 실패했을 때만
  이 파일에서 "가장 가까운 지점" 예보를 보여 준다(근사치 안내 배너 함께).

출처(2026-11 변경): Open-Meteo 대신 MET Norway(노르웨이 기상청, api.met.no)의 공개
locationforecast/2.0 을 쓴다. 키가 필요 없고 서버(해외 IP)에서 안정적으로 열린다.
- MET Norway 는 지점을 한 번에 여러 개 받는 엔드포인트가 없어 지점마다 한 번씩
  호출한다(약식 UA·요청 간 간격으로 예의 지킴). 반드시 "식별 가능한 User-Agent"를
  보내야 한다(브라우저로는 커스텀 UA를 못 보내서 서버에서만 가능).
- 응답은 시간대별(timeseries) 자료라, 브라우저 파서가 그대로 읽을 수 있도록
  Open-Meteo 와 똑같은 모양의 daily/hourly(필드 이름·단위 동일)로 변환해서 저장한다.
  그래서 index.html 의 fetchWeather / pickNearestCity 는 전혀 바꿀 필요가 없다.
- 날씨 코드는 MET Norway 의 symbol_code 를 WMO 코드(브라우저가 아는 값)로 바꾼다.

한 지점이 실패하면 이전 커밋 파일의 그 지점 값을 그대로 쓰고 stale 로 표시한다
(부분 실패가 전체를 비우지 않게 — 다른 fetch 스크립트들과 같은 원칙).
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
UTC = timezone.utc
OUT = Path(__file__).resolve().parent.parent / "weather" / "kr_forecast.json"

# 전국 주요 축산 권역을 고르게 덮는 지점들(시·도 + 주요 사육 밀집지). 이름은 화면 안내용.
CITIES = [
    ("서울", 37.57, 126.98), ("인천", 37.46, 126.71), ("수원", 37.26, 127.03),
    ("포천", 37.89, 127.20), ("춘천", 37.88, 127.73), ("강릉", 37.75, 128.90),
    ("원주", 37.34, 127.92), ("청주", 36.64, 127.49), ("음성", 36.94, 127.69),
    ("충주", 36.99, 127.93), ("대전", 36.35, 127.38), ("천안", 36.82, 127.11),
    ("홍성", 36.60, 126.66), ("보령", 36.33, 126.61), ("전주", 35.82, 127.15),
    ("김제", 35.80, 126.88), ("익산", 35.95, 126.96), ("정읍", 35.57, 126.86),
    ("광주", 35.16, 126.85), ("나주", 35.02, 126.71), ("목포", 34.81, 126.39),
    ("순천", 34.95, 127.49), ("영암", 34.80, 126.70), ("대구", 35.87, 128.60),
    ("안동", 36.57, 128.73), ("포항", 36.02, 129.37), ("경주", 35.86, 129.22),
    ("부산", 35.18, 129.08), ("창원", 35.23, 128.68), ("진주", 35.18, 128.11),
    ("제주", 33.50, 126.53), ("서귀포", 33.25, 126.56), ("세종", 36.48, 127.29),
]

API = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
# MET Norway TOS: 애플리케이션을 식별할 수 있는 User-Agent 필수(연락처 겸 사이트 도메인 포함).
HEADERS = {
    "User-Agent": "polcon.cc livestock-weather/1.0 (https://polcon.cc; GitHub Actions scheduled fetch)",
    "Accept": "application/json",
}

FORECAST_DAYS = 7


def _raw(url: str, timeout: int):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_city(lat: float, lng: float, timeout: int = 30):
    # met.no 는 소수점 4자리까지만 허용(초과 시 400). 직접 1회 + 재시도 1회.
    q = urllib.parse.urlencode({"lat": f"{lat:.4f}", "lon": f"{lng:.4f}"})
    url = f"{API}?{q}"
    last = None
    for attempt in ("직접", "직접(재시도)"):
        try:
            return _raw(url, timeout)
        except Exception as exc:
            last = exc
            print(f"::warning::{attempt} 실패: {exc}")
            time.sleep(1.0)
    raise last if last else RuntimeError("조회 실패")


# ── MET Norway symbol_code → WMO weather_code(브라우저가 아는 코드만 생성) ────────────
# 브라우저의 코드→아이콘 표(index.html 약 5815줄)에 있는 코드만 반환한다:
#   0·1·2·3 / 45·48 / 51·53·55 / 61·63·65 / 71·73·75·77 / 80·81·82 / 85·86 / 95·96·99
def symbol_to_wmo(code):
    if not code:
        return None
    c = str(code).split("_")[0]  # _day/_night/_polartwilight 꼬리 제거
    if "thunder" in c:
        return 96 if "heavy" in c else 95
    if "sleet" in c:                     # 진눈깨비 — 눈 계열로(눈송이 아이콘)
        if "showers" in c:
            return 85
        return 73 if "heavy" in c else 71
    if "snow" in c:
        shower = "showers" in c
        if "heavy" in c:
            return 86 if shower else 75
        if "light" in c:
            return 85 if shower else 71
        return 85 if shower else 73
    if "rain" in c:
        shower = "showers" in c
        if "heavy" in c:
            return 82 if shower else 65
        if "light" in c:
            return 80 if shower else 61
        return 81 if shower else 63
    if c == "fog":
        return 45
    if c == "cloudy":
        return 3
    if c == "partlycloudy":
        return 2
    if c == "fair":
        return 1
    if c == "clearsky":
        return 0
    return None


# 하루 대표 코드를 고를 때의 "심함" 순위(큰 값일수록 심함). 같은 심함이면 뒤의 것으로 덮지 않음.
_SEVERITY = {
    0: 0, 1: 1, 2: 2, 3: 3,
    45: 4, 48: 4,
    51: 5, 53: 6, 55: 7,
    61: 8, 63: 9, 65: 11,
    80: 8, 81: 9, 82: 12,
    71: 8, 73: 9, 75: 11, 77: 7,
    85: 8, 86: 11,
    95: 13, 96: 14, 99: 14,
}


def _entry_symbol(e):
    for k in ("next_1_hours", "next_6_hours", "next_12_hours"):
        blk = (e.get("data") or {}).get(k) or {}
        sym = (blk.get("summary") or {}).get("symbol_code")
        if sym:
            return sym
    return None


def _entry_precip(e):
    # 겹치지 않는 예보창의 강수량만 쓴다: next_1_hours(1시간) 우선, 없으면 next_6_hours(6시간).
    data = e.get("data") or {}
    for k in ("next_1_hours", "next_6_hours"):
        blk = data.get(k) or {}
        det = blk.get("details") or {}
        if "precipitation_amount" in det:
            return det["precipitation_amount"], k
    return None, None


def convert(payload):
    """MET Norway locationforecast → Open-Meteo 모양의 {daily, hourly}."""
    ts = ((payload.get("properties") or {}).get("timeseries")) or []
    if not ts:
        return None

    today_kst = datetime.now(KST).date()
    horizon = today_kst + timedelta(days=FORECAST_DAYS - 1)

    hourly = {"time": [], "temperature_2m": [], "weather_code": [],
              "precipitation": [], "wind_speed_10m": [], "relative_humidity_2m": []}
    # 날짜별 집계(일별 변환용)
    agg = {}  # date(str) -> {temps, winds, hums, precip, daysyms:[(sev,wmo)], anysyms:[(sev,wmo)]}

    def bucket(d):
        return agg.setdefault(d, {"temps": [], "winds": [], "hums": [],
                                  "precip": 0.0, "dsym": [], "asym": []})

    for e in ts:
        t = e.get("time")
        if not t:
            continue
        try:
            dt_utc = datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        except ValueError:
            continue
        dt = dt_utc.astimezone(KST)
        dstr = dt.strftime("%Y-%m-%d")
        dobj = dt.date()
        if dobj < today_kst or dobj > horizon:
            continue

        inst = (((e.get("data") or {}).get("instant") or {}).get("details")) or {}
        temp = inst.get("air_temperature")
        wind = inst.get("wind_speed")
        hum = inst.get("relative_humidity")
        sym = _entry_symbol(e)
        wmo = symbol_to_wmo(sym)
        precip, _win = _entry_precip(e)

        # 시간대별(그대로 나열 — 앞 2~3일은 1시간 간격, 이후는 6시간 간격)
        hourly["time"].append(dt.strftime("%Y-%m-%dT%H:%M"))
        hourly["temperature_2m"].append(round(temp, 1) if temp is not None else None)
        hourly["weather_code"].append(wmo)
        hourly["precipitation"].append(round(precip, 2) if precip is not None else 0.0)
        hourly["wind_speed_10m"].append(round(wind, 1) if wind is not None else None)
        hourly["relative_humidity_2m"].append(round(hum) if hum is not None else None)

        b = bucket(dstr)
        if temp is not None:
            b["temps"].append(temp)
        if wind is not None:
            b["winds"].append(wind)
        if hum is not None:
            b["hums"].append(hum)
        if precip is not None:
            b["precip"] += precip
        if wmo is not None:
            sev = _SEVERITY.get(wmo, 0)
            b["asym"].append((sev, wmo))
            if 6 <= dt.hour < 18:            # 낮 시간대 대표 코드 우선
                b["dsym"].append((sev, wmo))

    if not agg:
        return None

    dates = sorted(agg.keys())
    daily = {"time": [], "weather_code": [], "temperature_2m_max": [],
             "temperature_2m_min": [], "precipitation_sum": [],
             "wind_speed_10m_max": [], "relative_humidity_2m_mean": []}
    for d in dates:
        b = agg[d]
        syms = b["dsym"] or b["asym"]
        code = max(syms)[1] if syms else None
        daily["time"].append(d)
        daily["weather_code"].append(code)
        daily["temperature_2m_max"].append(round(max(b["temps"]), 1) if b["temps"] else None)
        daily["temperature_2m_min"].append(round(min(b["temps"]), 1) if b["temps"] else None)
        daily["precipitation_sum"].append(round(b["precip"], 1))
        daily["wind_speed_10m_max"].append(round(max(b["winds"]), 1) if b["winds"] else None)
        daily["relative_humidity_2m_mean"].append(
            round(sum(b["hums"]) / len(b["hums"])) if b["hums"] else None)

    return {"daily": daily, "hourly": hourly}


def load_prev():
    try:
        prev = json.loads(OUT.read_text(encoding="utf-8"))
        return {c.get("name"): c for c in (prev.get("cities") or []) if c.get("name")}
    except Exception:
        return {}


def main() -> int:
    prev = load_prev()
    cities_out = []
    ok = 0
    for i, (name, lat, lng) in enumerate(CITIES):
        try:
            payload = fetch_city(lat, lng)
            conv = convert(payload)
            if not conv or not conv["daily"].get("time"):
                raise RuntimeError("유효한 예보 없음")
            cities_out.append({"name": name, "lat": lat, "lng": lng,
                               "daily": conv["daily"], "hourly": conv["hourly"]})
            ok += 1
        except Exception as exc:
            print(f"::warning::{name} 조회 실패({exc}) — 이전 값 유지")
            old = prev.get(name)
            if old:
                old = dict(old)
                old["stale"] = True
                cities_out.append(old)
        # met.no 에 예의: 지점 사이에 짧은 간격(마지막 지점 뒤는 생략)
        if i < len(CITIES) - 1:
            time.sleep(0.4)

    if ok == 0:
        print("::error::모든 지점 조회 실패 — 이전 파일 유지")
        return 0  # 빈 파일로 덮지 않음

    out = {
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
        "source": "MET Norway (Yr.no)",
        "cities": cities_out,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"날씨 지점 예보 저장: 성공 {ok}/{len(CITIES)}개 지점 · {out['updated']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
