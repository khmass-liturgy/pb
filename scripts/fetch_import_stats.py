#!/usr/bin/env python3
"""계란·닭고기 수입 통계 자동 수집 → `import_status/stats.json`.

시세예측 화면(index.html `pfImport*`)의 📦 수입 항목이 이 파일을 읽어 월별 수입량 그래프를 그린다.
사람이 보도를 정리한 `import_status/latest.json`(수동 조사)과는 따로 둔다 — 이 파일은 통계 원자료만 담는다.

품목(HS 코드): 닭고기 0207 · 병아리 외 닭의 알(종란) 040711 · 신선란 040721 · 기타 조란 040790.
자료원은 두 가지이며 위에서부터 시도해 월별로 먼저 얻은 값을 쓴다:
  1) 관세청 「품목별 국가별 수출입실적」 공공데이터 API(data.go.kr) — 서비스키가 있을 때만(DATA_GO_KR_KEY).
     발표가 가장 빠르다(보통 전월 자료).
  2) UN Comtrade 공개 미리보기 API(키 없음, 대한민국 신고분) — 신고 지연이 수개월이고 호출 제한(429)이 있다.
같은 달에 두 자료가 있으면 관세청 값을 쓴다. 어느 쪽이 실패해도 이전에 저장한 값은 지우지 않는다.
단위는 중량 톤(t)과 금액 천 달러(kUSD)로 통일한다.
"""
from __future__ import annotations

import json
import os
import ssl
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

KST = timezone(timedelta(hours=9))
OUT = Path("import_status/stats.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; pb-import-stats/1.0)", "Accept": "application/json, application/xml"}
CTX = ssl.create_default_context()
MONTHS_BACK = 36

# 화면에서 쓰는 묶음 → HS 코드
GROUPS = {
    "chicken": {"label": "닭고기 (HS 0207)", "hs": ["0207"]},
    "egg_fresh": {"label": "신선란 (HS 040721)", "hs": ["040721"]},
    "egg_hatching": {"label": "종란 (HS 040711)", "hs": ["040711"]},
}
COMTRADE = "https://comtradeapi.un.org/public/v1/preview/C/M/HS"
CUSTOMS = "https://apis.data.go.kr/1220000/Itemtrade/getItemtradeList"


def month_list(n: int) -> list[str]:
    d = datetime.now(KST).replace(day=1)
    out = []
    for _ in range(n):
        out.append(d.strftime("%Y%m"))
        d = (d - timedelta(days=1)).replace(day=1)
    return out[::-1]


def http_get(url: str, tries: int = 4, timeout: int = 60) -> str | None:
    for i in range(tries):
        try:
            with urlopen(Request(url, headers=HEADERS), timeout=timeout, context=CTX) as r:
                return r.read().decode("utf-8", "replace")
        except HTTPError as e:
            if e.code == 429:                       # 호출 제한 — 길게 쉬었다가 다시
                wait = 20 * (i + 1)
                print(f"    429, {wait}초 대기")
                time.sleep(wait)
                continue
            print(f"    HTTP {e.code}")
            return None
        except (URLError, OSError) as e:
            print(f"    요청 실패: {type(e).__name__}: {str(e)[:100]}")
            time.sleep(3)
    return None


def fetch_comtrade(prev_months: dict[str, dict], full: bool, skip: dict[str, set] | None = None) -> dict[str, dict[str, dict]]:
    """{그룹: {YYYYMM: {"t": 톤, "kusd": 천달러, "by": {국가: 톤}}}}

    한 번에 한 달·한 품목씩 부른다(기간 여러 개나 자릿수가 다른 HS를 섞으면 400이 난다). 국가를 지정하지 않으면
    세계 합계(partnerCode 0)와 국가별 행이 함께 온다. 이미 받아 둔 달은 건너뛰고, 최근 4개월은 정정될 수 있어 다시 받는다.
    아직 신고되지 않은 달은 빈 응답이다 — 그 달은 그냥 비워 둔다."""
    out: dict[str, dict[str, dict]] = {g: {} for g in GROUPS}
    months = month_list(MONTHS_BACK)
    recent = set(months[-4:])
    for gname, g in GROUPS.items():
        have = prev_months.get(gname, {})
        misses = 0
        for per in reversed(months):                       # 최근 달부터 — 신고 지연 구간은 빈 응답
            if not full and per in have and per not in recent:
                continue
            if skip and per in skip.get(gname, set()):           # 관세청 값이 이미 있는 달은 UN에 묻지 않는다(호출 제한 절약)
                continue
            q = urlencode({"reporterCode": "410", "period": per, "cmdCode": g["hs"][0], "flowCode": "M",
                           "maxRecords": "500", "includeDesc": "true"})
            body = http_get(COMTRADE + "?" + q)
            time.sleep(6)
            if not body:
                continue
            try:
                rows = json.loads(body).get("data") or []
            except ValueError:
                continue
            if not rows:
                misses += 1
                continue
            cell = {"t": 0.0, "kusd": 0.0, "by": {}}
            for r in rows:
                wt, val = r.get("netWgt"), r.get("primaryValue")
                if wt is None:
                    continue
                if r.get("partnerCode") in (0, "0"):
                    cell["t"], cell["kusd"] = wt / 1000.0, (val or 0) / 1000.0         # 세계 합계
                else:
                    name = r.get("partnerDesc") or str(r.get("partnerCode"))
                    cell["by"][name] = cell["by"].get(name, 0.0) + wt / 1000.0
            if not cell["t"] and cell["by"]:
                cell["t"] = sum(cell["by"].values())
            if cell["t"]:
                out[gname][per] = cell
        print(f"  {gname}: {len(out[gname])}개월 받음(빈 응답 {misses}개월)")
    return out


def fetch_customs(key: str) -> dict[str, dict[str, dict]]:
    """관세청 품목별 국가별 수출입실적(data.go.kr). 응답은 XML — 필드명이 문서와 다를 수 있어 여러 이름을 허용한다."""
    out: dict[str, dict[str, dict]] = {g: {} for g in GROUPS}
    months = month_list(MONTHS_BACK)
    # 관세청(data.go.kr)은 해외(GitHub 러너) 접속에 응답하지 않는 경우가 있다 — 첫 호출이 두 번 연달아
    # 응답이 없으면 나머지는 시도하지 않고 바로 UN 자료로 넘어간다(전부 기다리면 50분 넘게 걸린다).
    probe = http_get(CUSTOMS + "?" + urlencode({"serviceKey": key, "strtYymm": months[-1], "endYymm": months[-1], "hsSgn": "0207", "numOfRows": 1, "pageNo": 1}),
                     tries=2, timeout=20)
    if probe is None:
        print("    관세청 서버가 응답하지 않습니다(해외 접속 차단 가능성) — 이번에는 건너뜁니다")
        return out
    for gname, g in GROUPS.items():
        for hs in g["hs"]:
            for i in range(0, len(months), 12):
                chunk = months[i:i + 12]
                q = urlencode({"serviceKey": key, "strtYymm": chunk[0], "endYymm": chunk[-1], "hsSgn": hs, "numOfRows": 999, "pageNo": 1})
                body = http_get(CUSTOMS + "?" + q)
                time.sleep(1)
                if not body:
                    continue
                try:
                    root = ET.fromstring(body)
                except ET.ParseError:
                    print("    XML 해석 실패:", body[:120].replace("\n", " "))
                    continue
                code = (root.findtext(".//resultCode") or root.findtext(".//returnReasonCode") or "").strip()
                if code and code not in ("00", "0", "000"):
                    print(f"    관세청 응답 오류 {code}: {(root.findtext('.//resultMsg') or root.findtext('.//returnAuthMsg') or '')[:80]}")
                    continue
                n_items = len(list(root.iter("item")))
                print(f"    {hs} {chunk[0]}~{chunk[-1]}: item {n_items}건")
                for it in root.iter("item"):
                    f = {c.tag: (c.text or "").strip() for c in it}
                    ym = (f.get("year") or f.get("yymm") or "").replace(".", "").replace("-", "")
                    if len(ym) != 6 or not ym.isdigit():
                        continue
                    try:
                        wgt, dlr = float(f.get("impWgt") or 0), float(f.get("impDlr") or 0)
                    except ValueError:
                        continue
                    if not wgt:
                        continue
                    cell = out[gname].setdefault(ym, {"t": 0.0, "kusd": 0.0, "by": {}})
                    cell["t"] += wgt / 1000.0                       # kg → t
                    cell["kusd"] += dlr / 1000.0                    # USD → 천 달러
                    name = f.get("statCdCntnKor1") or f.get("cntyNm") or f.get("statCd") or "기타"
                    cell["by"][name] = cell["by"].get(name, 0.0) + wgt / 1000.0
    return {g: d for g, d in out.items()}


def main() -> int:
    prev = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
        except ValueError:
            prev = {}
    key = os.environ.get("DATA_GO_KR_KEY", "").strip()
    sources = {}
    customs = {}
    if key:
        print("관세청 공공데이터 API 시도")
        customs = fetch_customs(key)
        print("  관세청 결과:", {g: f"{len(v)}개월" + (f" ({min(v)}~{max(v)})" if v else "") for g, v in customs.items()})
        sources["customs"] = {"name": "관세청 품목별 국가별 수출입실적(data.go.kr)", "months": sum(len(v) for v in customs.values())}
    else:
        print("DATA_GO_KR_KEY 없음 — 관세청 API는 건너뜁니다")
    print("UN Comtrade 공개 API 시도")
    comtrade = fetch_comtrade({g: (v or {}).get("months", {}) for g, v in (prev.get("series") or {}).items()}, os.environ.get("FULL") == "1",
                              {g: set(v) for g, v in customs.items()})
    sources["comtrade"] = {"name": "UN Comtrade(대한민국 신고분, 공개 미리보기)", "months": sum(len(v) for v in comtrade.values())}

    series = {}
    for g, meta in GROUPS.items():
        merged = dict((prev.get("series", {}).get(g, {}) or {}).get("months", {}))     # 이전 값 유지
        for per, cell in comtrade.get(g, {}).items():
            merged[per] = {**cell, "src": "comtrade"}
        for per, cell in customs.get(g, {}).items():
            merged[per] = {**cell, "src": "customs"}                                   # 관세청 값이 우선
        for cell in merged.values():
            cell["t"] = round(cell["t"], 1); cell["kusd"] = round(cell.get("kusd", 0), 1)
            cell["by"] = {k: round(v, 1) for k, v in sorted(cell.get("by", {}).items(), key=lambda kv: -kv[1])[:8]}
        series[g] = {"label": meta["label"], "months": dict(sorted(merged.items()))}
    have = sum(len(s["months"]) for s in series.values())
    if not have:
        print("받은 자료가 없어 파일을 만들지 않습니다")
        return 0
    out = {"updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"), "unit": {"weight": "톤(t)", "value": "천 달러(kUSD)"},
           "note": "관세청 API가 있으면 그 값을, 없으면 UN Comtrade 신고분을 쓴다. Comtrade는 신고가 수개월 늦다.", "sources": sources, "series": series}
    if prev.get("series") == out["series"]:
        print("새 자료 없음 — 변경 없음")
        return 0
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    for g, s in series.items():
        ks = list(s["months"])
        print(f"{g}: {len(ks)}개월" + (f" ({ks[0]} ~ {ks[-1]})" if ks else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
