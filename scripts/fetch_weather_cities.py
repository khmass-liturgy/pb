#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
국내 주요 지점 날씨 예보(Open-Meteo)를 서버(GitHub Actions)에서 미리 받아
weather/kr_forecast.json 으로 커밋한다.

왜 이렇게 하나:
- 날씨 탭은 원래 브라우저가 api.open-meteo.com(해외)을 직접 부른다. 그런데 일부
  농가 네트워크(모바일·사내망)에서는 open-meteo와 공개 CORS 프록시가 전부 막혀
  "날씨 정보를 가져오지 못했습니다"가 반복된다.
- 사이트의 다른 데이터처럼 서버가 미리 받아 저장소에 커밋해 두면, 브라우저는 이미
  잘 읽히는 경로(raw GitHub / Firebase getPublicContent)로 가져올 수 있다.
- 농장 위치가 정확히 일치하진 않으므로, 브라우저는 실시간 호출이 모두 실패했을 때만
  이 파일에서 "가장 가까운 지점" 예보를 보여 준다(근사치 안내 배너 함께).

GitHub 러너는 open-meteo에 직접 닿으므로 프록시가 필요 없다. 한 번의 요청으로 여러
지점을 받는다(latitude/longitude 를 콤마로 나열). 실패하면 이전 파일을 그대로 둔다.
"""
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
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

DAILY = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,relative_humidity_2m_mean"
HOURLY = "temperature_2m,weather_code,precipitation,wind_speed_10m,relative_humidity_2m"
HEADERS = {"User-Agent": "polcon-weather/1.0 (+https://polcon.cc)"}


def _get(url: str, timeout: int = 60):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_batch(cities):
    lats = ",".join(f"{c[1]:.4f}" for c in cities)
    lngs = ",".join(f"{c[2]:.4f}" for c in cities)
    q = urllib.parse.urlencode({
        "latitude": lats, "longitude": lngs,
        "daily": DAILY, "hourly": HOURLY,
        "timezone": "Asia/Seoul", "forecast_days": "7", "wind_speed_unit": "ms",
    })
    data = _get("https://api.open-meteo.com/v1/forecast?" + q)
    # 여러 지점이면 배열, 한 지점이면 객체 — 배열로 통일한다.
    if isinstance(data, dict):
        data = [data]
    return data


def main() -> int:
    try:
        results = fetch_batch(CITIES)
    except Exception as exc:  # 한 번 실패하면 2개로 나눠 재시도
        print(f"::warning::일괄 요청 실패({exc}) — 둘로 나눠 재시도")
        mid = len(CITIES) // 2
        try:
            results = fetch_batch(CITIES[:mid]) + fetch_batch(CITIES[mid:])
        except Exception as exc2:
            print(f"::error::날씨 지점 예보 조회 실패 — 이전 파일 유지: {exc2}")
            return 0  # 이전 커밋 유지(빈 파일로 덮지 않음)

    if len(results) != len(CITIES):
        print(f"::warning::응답 지점 수 불일치(요청 {len(CITIES)} / 응답 {len(results)})")

    cities_out = []
    for (name, lat, lng), res in zip(CITIES, results):
        daily = res.get("daily") if isinstance(res, dict) else None
        if not daily or not daily.get("time"):
            continue
        cities_out.append({
            "name": name, "lat": lat, "lng": lng,
            "daily": daily, "hourly": res.get("hourly") or {},
        })

    if not cities_out:
        print("::error::유효한 지점 예보가 없어 이전 파일 유지")
        return 0

    out = {
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
        "source": "Open-Meteo (ECMWF IFS)",
        "cities": cities_out,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"날씨 지점 예보 저장: {len(cities_out)}개 지점 · {out['updated']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
