#!/usr/bin/env python3
"""
유료서비스 "사료곡물 원료 품질평가" — 세계 곡물 품질 흐름 지표 수집기.

미국·브라질·아르헨티나·유럽의 주요 곡물 산지 대표 지점 날씨를 ERA5 재분석
(ECMWF/Copernicus, Open-Meteo Archive API 경유)에서 받아, "최근 30일"의 강수·수분수지
(강수-증발산)·고온일수·평균 최고기온·강수일수를 1991~2020 평년과 비교해 z-점수로 만든다.

  · 건조·고온 신호 ↑ : 가뭄·열 스트레스 → 수량 감소, 옥수수 아플라톡신 위험
  · 다습 신호 ↑      : 수확기 수분 상승, 곰팡이·DON·푸모니신·발아 위험

실제 곰팡이독소 농도나 로트 품질을 측정한 값이 아니라 "기상으로 본 위험의 높낮이"다.

두 단계로 나뉜다.
 ① 평년(baseline): 1991~2020 전 기간을 한 번 받아 지점별·날짜별 평균·표준편차를 grain_quality/baseline.json에
    저장한다. 이 요청은 무겁다(Open-Meteo는 기간이 길수록 호출 수를 많이 센다 — 한 지점이 시간당 한도에
    걸릴 만큼). 그래서 지점 하나씩, 429(시간당 한도)가 오면 거기서 멈추고 다음 실행에서 이어 받는다.
    평년은 변하지 않으므로 완성되면 다시 받지 않는다.
 ② 최근값: 최근 약 4개월만 받아(가볍다) 평년과 비교해 grain_quality/latest.json(최근 13주 흐름 포함)을 만든다.
평년이 아직 덜 모인 지역은 이전 값을 유지하고 stale 표시한다(이 저장소의 공통 규칙: 부분 실패가 전체를 지우지 않는다).
"""

from __future__ import annotations

import json
import math
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

KST = timezone(timedelta(hours=9))
OUTPUT_PATH = Path("grain_quality/latest.json")
BASELINE_PATH = Path("grain_quality/baseline.json")
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; pb-grain-quality/1.0)"}

BASE_START = 1991
BASE_END = 2020
WINDOW = 30          # 일
WEEKS_BACK = 12      # 최근 13개 시점(주 단위)
HEAT_C = 35.0        # 고온일 기준 일 최고기온
WET_MM = 5.0         # 강수일 기준 일 강수량
METRICS = ("p", "wb", "heat", "wet", "tmax")

# 지역별 대표 지점 (주요 생산벨트)
REGIONS = {
    "us": {"name": "미국", "points": [("아이오와", 42.0, -93.5), ("일리노이", 40.2, -89.0), ("네브래스카", 41.0, -98.0)]},
    "br": {"name": "브라질", "points": [("마토그로수", -13.0, -56.0), ("파라나", -24.5, -52.0), ("고이아스", -16.5, -50.0)]},
    "ar": {"name": "아르헨티나", "points": [("코르도바", -32.0, -63.5), ("부에노스아이레스 북부", -34.5, -61.0), ("산타페", -31.0, -61.0)]},
    "eu": {"name": "유럽", "points": [("프랑스 중부", 47.5, 2.0), ("루마니아 남부", 44.3, 26.5), ("헝가리", 47.0, 19.5)]},
}
# z-점수 분모 하한 — 평년 편차가 거의 없는 지점(예: 고온일 0일, 건기)에서 z가 폭주하지 않게
SD_FLOOR = {"p": 12.0, "wb": 20.0, "heat": 1.5, "wet": 1.5, "tmax": 0.8}
# 비윤년 기준 365일 달력(월/일) — 평년 통계의 색인
CAL = [(m, d) for m in range(1, 13) for d in range(1, [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1] + 1)]
CAL_IDX = {md: i for i, md in enumerate(CAL)}


class RateLimited(Exception):
    pass


def point_key(name: str) -> str:
    return name


def fetch_rows(lat: float, lng: float, start: date, end: date) -> list[tuple[date, float, float, float]]:
    params = {
        "latitude": lat, "longitude": lng, "start_date": start.isoformat(), "end_date": end.isoformat(),
        "daily": "precipitation_sum,temperature_2m_max,et0_fao_evapotranspiration", "timezone": "UTC",
    }
    last = None
    for attempt in range(3):
        try:
            r = requests.get(ARCHIVE_URL, params=params, headers=HEADERS, timeout=120)
            if r.status_code == 429:
                raise RateLimited(r.text[:120])
            r.raise_for_status()
            d = r.json()["daily"]
            out = []
            for t, p, tx, et in zip(d["time"], d["precipitation_sum"], d["temperature_2m_max"], d["et0_fao_evapotranspiration"]):
                out.append((date.fromisoformat(t), 0.0 if p is None else p, tx if tx is not None else math.nan, 0.0 if et is None else et))
            return out
        except RateLimited:
            raise
        except (requests.RequestException, KeyError, ValueError) as exc:
            last = exc
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"ERA5 수집 실패({lat},{lng}): {last}")


class Series:
    """일별 값을 누적합으로 들고 있어 임의 30일 창의 지표를 O(1)로 구한다."""

    def __init__(self, rows):
        self.d0 = rows[0][0]
        n = len(rows)
        self.n = n
        self.last = rows[-1][0]
        self.cp = [0.0] * (n + 1)
        self.cwb = [0.0] * (n + 1)
        self.cheat = [0] * (n + 1)
        self.cwet = [0] * (n + 1)
        self.ctx = [0.0] * (n + 1)
        self.ctxn = [0] * (n + 1)
        for i, (_, p, tx, et) in enumerate(rows):
            self.cp[i + 1] = self.cp[i] + p
            self.cwb[i + 1] = self.cwb[i] + (p - et)
            self.cheat[i + 1] = self.cheat[i] + (1 if (not math.isnan(tx) and tx >= HEAT_C) else 0)
            self.cwet[i + 1] = self.cwet[i] + (1 if p >= WET_MM else 0)
            self.ctx[i + 1] = self.ctx[i] + (0.0 if math.isnan(tx) else tx)
            self.ctxn[i + 1] = self.ctxn[i] + (0 if math.isnan(tx) else 1)

    def window(self, end: date) -> dict | None:
        j = (end - self.d0).days + 1
        i = j - WINDOW
        if i < 0 or j > self.n:
            return None
        n_tx = self.ctxn[j] - self.ctxn[i]
        if not n_tx:
            return None
        return {
            "p": self.cp[j] - self.cp[i], "wb": self.cwb[j] - self.cwb[i],
            "heat": self.cheat[j] - self.cheat[i], "wet": self.cwet[j] - self.cwet[i],
            "tmax": (self.ctx[j] - self.ctx[i]) / n_tx,
        }


def mean_sd(xs: list[float]) -> tuple[float, float]:
    m = sum(xs) / len(xs)
    v = sum((x - m) ** 2 for x in xs) / max(1, len(xs) - 1)
    return m, math.sqrt(v)


def build_baseline(rows) -> dict:
    """지점 하나의 1991~2020 일별 자료 → 365일 달력별 30일 창 지표의 평균·표준편차."""
    ser = Series(rows)
    mean = {m: [] for m in METRICS}
    sd = {m: [] for m in METRICS}
    for (mo, da) in CAL:
        vals = {m: [] for m in METRICS}
        for y in range(BASE_START, BASE_END + 1):
            w = ser.window(date(y, mo, da))
            if w is None:
                continue
            for m in METRICS:
                vals[m].append(w[m])
        if len(vals["p"]) < 20:
            raise RuntimeError("평년 표본이 부족함")
        for m in METRICS:
            mu, s = mean_sd(vals[m])
            mean[m].append(round(mu, 2))
            sd[m].append(round(s, 2))
    return {"mean": mean, "sd": sd}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def ensure_baseline(base: dict) -> bool:
    """없는 지점의 평년을 하나씩 받는다. 429면 멈추고 False(다음 실행에서 이어 받음)."""
    base_end = date(BASE_END, 12, 31)
    complete = True
    for rkey, meta in REGIONS.items():
        for name, lat, lng in meta["points"]:
            k = f"{rkey}:{name}"
            if k in base:
                continue
            print(f"[평년] {meta['name']} {name} ERA5 {BASE_START}~{BASE_END} 수집 중...")
            try:
                rows = fetch_rows(lat, lng, date(BASE_START, 1, 1), base_end)
                base[k] = build_baseline(rows)
                BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
                BASELINE_PATH.write_text(json.dumps(base, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
                print(f"[평년] {k} 저장 ({len(base)}개 지점)")
                time.sleep(30)           # 시간당 호출 한도를 아끼려고 천천히
            except RateLimited as exc:
                print(f"[평년] 시간당 한도 도달 — 지금까지 {len(base)}개 지점 저장, 다음 실행에서 이어 받음 ({exc})")
                return False
            except Exception as exc:  # noqa: BLE001
                print(f"[평년] {k} 실패: {exc}")
                complete = False
    return complete


def scores(z: dict) -> tuple[float, float]:
    """건조·고온 점수(0~), 다습 점수(0~) — 1 안팎이 '주의', 2 이상이 '경계' 감각."""
    dry = max(0.0, -z["wb"]) + 0.7 * max(0.0, z["heat"]) + 0.5 * max(0.0, z["tmax"])
    wet = max(0.0, z["p"]) + 0.5 * max(0.0, z["wet"])
    return dry, wet


def build_region(rkey: str, meta: dict, base: dict, end: date) -> dict:
    series_list = []
    for name, lat, lng in meta["points"]:
        rows = fetch_rows(lat, lng, end - timedelta(days=130), end)     # 최근 ~4개월만(가볍다)
        series_list.append((name, Series(rows), base[f"{rkey}:{name}"]))
        time.sleep(2)
    last = min(s.last for _, s, _ in series_list)
    steps = []
    for k in range(WEEKS_BACK, -1, -1):
        e = last - timedelta(days=7 * k)
        md = (e.month, 28 if (e.month, e.day) == (2, 29) else e.day)
        i = CAL_IDX[md]
        per = []
        for _, s, b in series_list:
            cur = s.window(e)
            if cur is None:
                continue
            z = {m: max(-4.0, min(4.0, (cur[m] - b["mean"][m][i]) / max(b["sd"][m][i], SD_FLOOR[m]))) for m in METRICS}
            per.append((cur, {m: b["mean"][m][i] for m in METRICS}, z))
        if not per:
            continue
        avg = lambda idx, m: sum(p[idx][m] for p in per) / len(per)
        z = {m: avg(2, m) for m in METRICS}
        dry, wet = scores(z)
        steps.append({"end": e.isoformat(), "z": {m: round(v, 2) for m, v in z.items()},
                      "cur": {m: round(avg(0, m), 1) for m in METRICS}, "norm": {m: round(avg(1, m), 1) for m in METRICS},
                      "dry": round(dry, 2), "wet": round(wet, 2)})
    if not steps:
        raise RuntimeError("지표를 계산할 수 없음")
    now = steps[-1]
    return {
        "name": meta["name"], "points": [p[0] for p in meta["points"]], "asof": now["end"], "now": now,
        "series": [{"end": s["end"], "wb": s["z"]["wb"], "tmax": s["z"]["tmax"], "p": s["z"]["p"], "dry": s["dry"], "wet": s["wet"]} for s in steps],
    }


def main() -> int:
    base = load_json(BASELINE_PATH)
    ensure_baseline(base)                         # 덜 모였으면 모인 만큼만 — 아래에서 지역별로 걸러낸다
    prev_regions = load_json(OUTPUT_PATH).get("regions", {})
    end = date.today() - timedelta(days=6)        # ERA5 공개 지연
    regions, stale = {}, {}
    for key, meta in REGIONS.items():
        ready = all(f"{key}:{p[0]}" in base for p in meta["points"])
        if not ready:
            print(f"[{meta['name']}] 평년이 아직 덜 모여 건너뜀")
        else:
            try:
                regions[key] = build_region(key, meta, base, end)
                n = regions[key]["now"]
                print(f"[{meta['name']}] 기준일 {regions[key]['asof']} 건조 {n['dry']} 다습 {n['wet']}")
            except RateLimited as exc:
                print(f"[{meta['name']}] 시간당 한도 — 이전 값 유지 ({exc})")
            except Exception as exc:  # noqa: BLE001 — 한 지역 실패가 전체를 지우지 않게
                print(f"[{meta['name']}] 실패: {exc}")
        if key not in regions and key in prev_regions:
            regions[key] = prev_regions[key]
            stale[key] = True
    if not regions:
        print("계산된 지역이 없고 이전 데이터도 없습니다 — 평년 수집이 끝난 뒤 다시 실행하세요.")
        return 0 if BASELINE_PATH.exists() else 1   # 평년만 먼저 쌓는 단계는 실패가 아니다
    prev = load_json(OUTPUT_PATH)
    if prev.get("regions") == regions and prev.get("stale", {}) == stale:
        print("지표 변화 없음 — 파일을 다시 쓰지 않음")          # 같은 값으로 커밋이 쌓이지 않게
        return 0
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps({
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
        "source": "ERA5 재분석(ECMWF/Copernicus) — Open-Meteo Archive API · 평년 1991~2020",
        "window_days": WINDOW, "heat_c": HEAT_C, "wet_mm": WET_MM,
        "stale": stale, "regions": regions,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("저장 완료:", OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
