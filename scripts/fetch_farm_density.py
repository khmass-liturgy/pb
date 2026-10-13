#!/usr/bin/env python3
"""
가축위생방역지원본부 「전국 시군별 ○○ 사육규모 현황」(공공데이터포털 파일데이터, CSV, 연 1회 갱신)에서
가금류 시·군별 사육 농가 수(호수)·마릿수(두수)를 모아 farm_density/sigun.json 으로 저장한다.

- 출처: https://www.data.go.kr/data/<id>/fileData.do (공공저작물 출처표시 제1유형)
- 이 시리즈에는 ‘일반 산란계’ 시·군별 표가 없다(산란중추·산란종계만 있음). 그래서 합계에서 일반 산란계는 빠진다.
- CSV 열: 순번, 품종, 시도, 시군, 년도, 전체호수, 전체두수, 규모별 호수·수수…  (한 파일에 2018~2026년이 모두 들어 있음)
- 시군이 ‘용인시 처인구’처럼 구까지 적힌 행은 ‘용인시’로 합친다.
- 광역시·특별시는 시도=시군(예: 부산/부산)으로 들어 있다.
- 파일 인코딩은 cp949.

사용: python scripts/fetch_farm_density.py            (네트워크 필요, 출력: farm_density/sigun.json)
      python scripts/fetch_farm_density.py --dir DIR   (이미 받은 CSV 폴더 DIR에서 읽기: 파일명 <id>.csv)
"""
import csv
import io
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
OUT = Path("farm_density/sigun.json")
# data.go.kr 파일데이터 id → (키, 이름)
SETS = {
    "15147324": ("broiler", "육계"),
    "15147325": ("broiler_breeder", "육용종계"),
    "15147326": ("native", "토종닭"),
    "15147327": ("native_breeder", "토종종계"),
    "15147328": ("baeksemi", "백세미"),
    "15147330": ("layer_pullet", "산란중추"),
    "15147331": ("layer_breeder", "산란종계"),
    "15147332": ("duck_breeder", "종오리"),
    "15147333": ("duck_meat", "육용오리"),
    "15147334": ("duck_layer", "산란오리"),
    "15147335": ("duck_general", "일반오리"),
}
UA = {"User-Agent": "Mozilla/5.0"}


def read_csv_bytes(raw):
    for enc in ("utf-8-sig", "cp949"):
        try:
            return list(csv.DictReader(io.StringIO(raw.decode(enc))))
        except UnicodeDecodeError:
            continue
    raise ValueError("encoding")


def download(did):
    import requests
    page = requests.get(f"https://www.data.go.kr/data/{did}/fileData.do", headers=UA, timeout=30).text
    m = re.search(r"fileDownload\.do\?atchFileId=[A-Z_0-9]+&fileDetailSn=\d+&insertDataPrcus=N", page)
    if not m:
        raise RuntimeError(f"{did}: 다운로드 링크를 찾지 못함")
    r = requests.get("https://www.data.go.kr/cmm/cmm/" + m.group(0), headers={**UA, "Referer": f"https://www.data.go.kr/data/{did}/fileData.do"}, timeout=60)
    r.raise_for_status()
    return r.content


def to_int(x):
    x = (x or "").replace(",", "").strip()
    return int(x) if re.fullmatch(r"\d+", x) else 0


def main():
    src_dir = None
    if "--dir" in sys.argv:
        src_dir = Path(sys.argv[sys.argv.index("--dir") + 1])
    rows = {}      # (sido, sigun) → {key:{farms,heads}}
    years = {}
    for did, (key, name) in SETS.items():
        try:
            raw = (src_dir / f"{did}.csv").read_bytes() if src_dir else download(did)
        except Exception as e:
            print("건너뜀", did, name, e)
            continue
        data = read_csv_bytes(raw)
        ys = sorted({r["년도"] for r in data if r.get("년도")})
        if not ys:
            continue
        y = ys[-1]
        years[key] = y
        for r in data:
            if r["년도"] != y:
                continue
            sido, sg = r["시도"].strip(), r["시군"].strip().split(" ")[0]
            d = rows.setdefault((sido, sg), {})
            cur = d.setdefault(key, {"farms": 0, "heads": 0})
            cur["farms"] += to_int(r["전체호수"])
            cur["heads"] += to_int(r["전체두수"])
    out = {
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
        "source": "가축위생방역지원본부 「전국 시군별 ○○ 사육규모 현황」(공공데이터포털 파일데이터)",
        "note": "농가 수(호수)는 정확하나 사육 마릿수는 일부 오차가 있을 수 있다고 제공기관이 안내함. 일반 산란계 시·군별 자료는 이 시리즈에 없음.",
        "years": years,
        "types": {k: n for _, (k, n) in SETS.items()},
        "rows": [
            {"sido": s, "sgg": g, "farms": sum(v["farms"] for v in d.values()), "heads": sum(v["heads"] for v in d.values()),
             "by": {k: v["farms"] for k, v in d.items() if v["farms"]},
             "hby": {k: v["heads"] for k, v in d.items() if v["heads"]}}
            for (s, g), d in sorted(rows.items())
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("저장", OUT, len(out["rows"]), "개 시군, 농가 합계", sum(r["farms"] for r in out["rows"]))


if __name__ == "__main__":
    main()
