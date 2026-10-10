#!/usr/bin/env python3
"""시세예측용 과거 자료 누적 — 이미 매일 수집하는 JSON을 날짜별로 이어 붙여 `price_history/daily.json`에 쌓는다.

육계·계란 시세예측 화면(index.html `pf*`)은 가격의 과거 실적이 있어야 모형을 학습하고 백테스트할 수 있다.
원천 JSON(`poultry_price/latest.json` 등)은 최근 1~2달치만 갖고 있어서, 매일 이 스크립트가 새 날짜를 이어 붙인다.
서로 다른 조사처·단계의 가격은 섞지 않고 시리즈를 따로 둔다:
  · egg            계란 특란(XL) 산지가격, 원/10개, 전국 (다봄 distrPrice)
  · broiler_live   육계 생계유통(대), 원/kg (다봄 distrPrice)
  · broiler_assoc  육계 대(1.6kg 이상) 협회 시세, 원/kg (대한양계협회, 오후 1시 게재)
  · feed_monthly   배합사료 월별 생산량(톤) — 농식품부, 월 단위로 수정되기도 해서 새 값으로 덮어쓴다

같은 날짜가 다시 오면 새 값으로 덮어쓴다(수정 반영). 값이 없거나 숫자가 아니면 건너뛴다.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
OUT = Path("price_history/daily.json")

SERIES_META = {
    "egg": {"label": "계란 특란(XL) 산지가격", "unit": "원/10개", "source": "다봄(ekapepia) 계란 유통단계별 가격, 전국"},
    "broiler_live": {"label": "육계 생계유통(대)", "unit": "원/kg", "source": "다봄(ekapepia) 육계 유통단계별 가격"},
    "broiler_assoc": {"label": "육계 대(1.6kg 이상) 협회 시세", "unit": "원/kg", "source": "대한양계협회 금일 육계시세"},
}


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def merge_rows(existing: list, new_rows: list[tuple[str, float]]) -> list:
    limit = (datetime.now(KST) + timedelta(days=1)).strftime("%Y-%m-%d")      # 오늘보다 뒤 날짜는 잘못 읽은 값
    by_date = {r[0]: r[1] for r in (existing or []) if isinstance(r, list) and len(r) == 2 and r[0] <= limit}
    for d, v in new_rows:
        if isinstance(v, (int, float)) and v > 0 and d <= limit:
            by_date[d] = v
    return [[d, by_date[d]] for d in sorted(by_date)]


def main() -> int:
    data = load(OUT) or {}
    series = data.get("series") or {}

    pp = load(Path("poultry_price/latest.json")) or {}
    for key, src in (("egg", "egg"), ("broiler_live", "chicken")):
        rows = [(r["date"], r["value"]) for r in ((pp.get(src) or {}).get("rows") or []) if r.get("date") and r.get("value")]
        meta = dict(SERIES_META[key])
        cur = series.get(key) or {}
        cur.update(meta)
        cur["rows"] = merge_rows(cur.get("rows"), rows)
        series[key] = cur

    bt = load(Path("broiler_price_today/latest.json")) or {}
    big = next((r for r in (bt.get("rows") or []) if r.get("grade") == "대"), None)
    label = bt.get("date_label") or ""          # 예: "10/08"
    updated = bt.get("updated") or ""           # 예: "2026-10-10 03:14 KST"
    try:
        m, d = (int(x) for x in label.split("/"))
        y = int(updated[:4]) if updated[:4].isdigit() else datetime.now(KST).year
        # 1월에 12월 시세가 게재되는 연말·연초 경계
        if m == 12 and int(updated[5:7] or 0) == 1:
            y -= 1
        date = f"{y:04d}-{m:02d}-{d:02d}"
    except Exception:
        date = None
    if big and date and isinstance(big.get("today"), (int, float)):
        cur = series.get("broiler_assoc") or {}
        cur.update(SERIES_META["broiler_assoc"])
        cur["rows"] = merge_rows(cur.get("rows"), [(date, big["today"])])
        series["broiler_assoc"] = cur

    feed = data.get("feed_monthly") or {}
    fp = load(Path("feed_production/latest.json")) or {}
    for year, yd in (fp.get("years") or {}).items():
        g = yd.get("groups") or {}
        for i in range(12):
            def v(name):
                arr = g.get(name) or []
                return arr[i] if i < len(arr) else None
            s, f, lay, rear = v("broiler_starter"), v("broiler_finisher"), v("layer_laying"), v("layer_rearing")
            if None in (s, f, lay, rear):
                continue
            feed[f"{year}-{i + 1:02d}"] = {"broiler": round(s + f, 1), "layer_laying": lay, "layer_rearing": rear}

    # 소급 수집한 과거 연도(feed_production/history.json) — 월별 사료 생산량을 같은 모양으로 합친다.
    hist = load(Path("feed_production/history.json")) or {}
    for year, yd in (hist.get("years") or {}).items():
        g = yd.get("groups") or {}
        for i in range(12):
            def hv(name):
                arr = g.get(name) or []
                return arr[i] if i < len(arr) else None
            s, f, lay, rear = hv("broiler_starter"), hv("broiler_finisher"), hv("layer_laying"), hv("layer_rearing")
            if None in (s, f, lay, rear):
                continue
            feed.setdefault(f"{year}-{i + 1:02d}", {"broiler": round(s + f, 1), "layer_laying": lay, "layer_rearing": rear})

    out = {
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
        "note": "다봄·대한양계협회·농식품부 자료를 날짜별로 이어 붙인 누적 자료. 시리즈별 조사처가 다르므로 서로 섞어 쓰지 않는다.",
        "series": series,
        "feed_monthly": dict(sorted(feed.items())),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    # 숫자만 바뀐 게 아니면(= 새 날짜가 없으면) updated만 바뀌어 매일 커밋되지 않도록, 본문이 같으면 쓰지 않는다.
    prev = load(OUT)
    if prev and prev.get("series") == out["series"] and prev.get("feed_monthly") == out["feed_monthly"]:
        print("새 자료 없음 — 변경 없음")
        return 0
    OUT.write_text(text, encoding="utf-8")
    for k, s in series.items():
        r = s["rows"]
        print(f"{k}: {len(r)}건 ({r[0][0]} ~ {r[-1][0]})" if r else f"{k}: 없음")
    print(f"feed_monthly: {len(feed)}개월")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
