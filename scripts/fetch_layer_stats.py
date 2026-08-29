#!/usr/bin/env python3
"""
축산물품질평가원 축산유통 통계누리(mtrace.go.kr) — 산란계·육계 사육 통계 수집

통계표: DT_1EO071 "닭 시도 용도별(산란계,육용계) 사육규모별 가구수 및 마리수"
        (분기 단위, orgId=323)

이 표 하나에 산란계·육용계의 가구수(사육농가수)와 마리수(사육수)가 함께 들어
있다. 예전에는 DT_1EO415(산란계 월령별 마리수)를 썼는데, 그 표에는 농가수가
없고 산란계만 있어 이 표로 바꿨다. 두 표의 산란계 마리수는 서로 일치한다.

사육규모별(1만 미만 / 1만~3만 / …) 세부는 받지 않고 합계(OV_L2_ID=00)만 쓴다.

API 메모 — mtrace는 KOSIS 계열 OLAP이라 절차가 정해져 있다.
  1) GET  statHtml.do (KOSIS 파라미터)  → 세션 확보. 건너뛰면 이후 POST가 실패한다.
  2) POST periodDivSelect.do            → 조회 가능한 분기 목록
  3) POST html.do                       → 표 HTML이 담긴 JSON
핵심은 `fieldList`다. 화면에서 자바스크립트가 채우는 값이라 1)의 HTML에는 비어
있는데, 비어 있으면 서버가 조회 대신 "페이지를 찾을 수 없습니다" HTML을 200 OK로
돌려준다. 상태코드만으로는 성공과 구분되지 않아 응답이 JSON인지까지 확인한다.
"""

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

KST = timezone(timedelta(hours=9))
OUT_PATH = Path("layer_stats/latest.json")

ORG_ID = "323"
TBL_ID = "DT_1EO071"
LIST_ID = "323_003_001"
BASE = "https://mtrace.go.kr"
PAGE_URL = (f"{BASE}/statHtml/statHtml.do?orgId={ORG_ID}&tblId={TBL_ID}"
            f"&vw_cd=xtl&list_id={LIST_ID}&conn_path=MT_ZTITLE")
HUMAN_URL = f"{BASE}/stats/stp/dtl/stl/xtlStatsList.do"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}
AJAX = {"Referer": PAGE_URL, "X-Requested-With": "XMLHttpRequest", "Origin": BASE}

# 표의 열 순서와 같아야 한다
ITEMS = [("T01", "layer_farms"), ("T02", "layer_birds"),
         ("T03", "broiler_farms"), ("T04", "broiler_birds")]
# 시도 코드(00=전국). 실적이 없는 시도는 서버가 '-'로 준다.
SIDO = ["00", "11", "21", "22", "23", "24", "25", "26", "29",
        "41", "31", "32", "33", "34", "35", "36", "37", "38", "39"]


def label_period(code):
    m = re.fullmatch(r"(\d{4})0?(\d)", code or "")
    return f"{m.group(1)} {m.group(2)}/4" if m else (code or "")


def base_params():
    cells = len(SIDO) * len(ITEMS)
    return {
        "orgId": ORG_ID, "tblId": TBL_ID, "language": "ko",
        "colAxis": "TIME,ITEM", "rowAxis": "A,B", "isFirst": "N",
        "contextPath": "/statHtml", "vwCd": "xtl", "listId": LIST_ID,
        "connPath": "MT_ZTITLE", "statId": "1976001", "pubLog": "0",
        "viewKind": "1", "doAnal": "N", "dataOpt": "ko", "view": "table",
        "existStblCmmtKor": "Y", "existStblCmmtEng": "N",
        "classAllArr": '[{"objVarId":"A","ovlSn":"1"},{"objVarId":"B","ovlSn":"2"}]',
        "classSet": '[{"objVarId":"A","ovlSn":"1","visible":"true"},'
                    '{"objVarId":"B","ovlSn":"2","visible":"true"}]',
        "selectAllFlag": "N", "periodStr": "Q",
        "tblNm": "닭 시도 용도별(산란계,육용계) 사육규모별 가구수 및 마리수",
        "itemMultiply": str(cells), "dbUser": "NSI_IN_323.", "usePivot": "N",
        "isChangedTableType": "N", "isChangedPeriodCo": "N", "isChangedPrdSort": "N",
        "p_classAllChkYn": "N", "p_classAllSelectYn": "N", "first_open": "Y",
        "reqCellCnt": str(cells * 2), "inheritYn": "N", "tableType": "default",
        "dataOpt2": "ko", "prdSort": "desc", "findData": "on",
        "downGridFileType": "xlsx", "downGridCellMerge": "Y", "downGridMeta": "Y",
        "downSort": "asc", "pointType": "screen", "downLargeFileType": "excel",
        "downLargeExprType": "1", "downLargeSort": "asc", "naviInfo": "tabTimeText",
        "itemChkLi": "T04", "classAllSelect": "on",
        "classLvlAllChk1_1": "on", "classChkLi1_1": "39=",
        "classLvlAllChk2_1": "on", "classChkLi2_1": "20=",
        "defaultFolder": "1", "headCheck": "Q", "timeChkQ": "",
    }


def fetch_periods(session):
    r = session.post(f"{BASE}/statHtml/periodDivSelect.do",
                     data=base_params(), headers=AJAX, timeout=40)
    r.raise_for_status()
    return sorted({d["prdDe"] for d in r.json().get("result", []) if d.get("prdDe")})


def fetch_table(session, periods):
    fl = [{"targetId": "PRD", "targetValue": "", "prdValue": "Q,%s,@" % ",".join(periods)}]
    fl += [{"targetId": "ITM_ID", "targetValue": c, "prdValue": ""} for c, _ in ITEMS]
    fl += [{"targetId": "OV_L1_ID", "targetValue": c, "prdValue": ""} for c in SIDO]
    fl += [{"targetId": "OV_L2_ID", "targetValue": "00", "prdValue": ""}]  # 사육규모 합계

    p = base_params()
    p["timeChkQ"] = periods[-1]
    p["fieldList"] = json.dumps(fl, ensure_ascii=False)

    r = session.post(f"{BASE}/statHtml/html.do", data=p, headers=AJAX, timeout=60)
    r.raise_for_status()
    if "json" not in r.headers.get("Content-Type", "") and not r.text.lstrip().startswith("{"):
        raise RuntimeError("표 대신 HTML 응답을 받음 (%dbytes)" % len(r.content))
    data = r.json()
    if data.get("errMsg"):
        raise RuntimeError("서버 오류: %s" % data["errMsg"])
    if not data.get("result"):
        raise RuntimeError("응답에 표가 없음")
    return data["result"][0]


def num(raw):
    raw = (raw or "").replace(",", "").strip()
    return int(raw) if re.fullmatch(r"-?\d+", raw) else None


def parse_table(html, period_count):
    """행마다 시도명 + (기간 × 항목4) 값. 사육규모는 '합계'만 요청했다."""
    out = {}
    for tr in re.findall(r"<tr>([\s\S]*?)</tr>", html):
        heads = re.findall(r"<td class='first'[^>]*title='([^']*)'", tr)
        vals = [num(v) for v in re.findall(r"<td class='value'[^>]*title='([^']*)'", tr)]
        if not heads or not vals:
            continue
        name = heads[0].strip()
        want = period_count * len(ITEMS)
        if name and len(vals) >= want:
            out[name] = vals[:want]
    return out


def build(table, periods):
    def slot(vals, p_idx, i_idx):
        i = p_idx * len(ITEMS) + i_idx
        return vals[i] if i < len(vals) else None

    cur, prev = periods[0], (periods[1] if len(periods) > 1 else None)

    def species(vals, farms_i, birds_i):
        f, b = slot(vals, 0, farms_i), slot(vals, 0, birds_i)
        pf = slot(vals, 1, farms_i) if prev else None
        pb = slot(vals, 1, birds_i) if prev else None
        return {
            "farms": f, "birds": b, "prev_farms": pf, "prev_birds": pb,
            "farms_pct": round((f - pf) / pf * 100, 1) if f is not None and pf else None,
            "birds_pct": round((b - pb) / pb * 100, 1) if b is not None and pb else None,
            "per_farm": round(b / f) if f and b else None,
        }

    nat = table.get("전국")
    if not nat:
        raise RuntimeError("전국 행을 찾지 못함")
    layer, broiler = species(nat, 0, 1), species(nat, 2, 3)
    if not layer["birds"] or not broiler["birds"]:
        raise RuntimeError("전국 마리수를 읽지 못함")

    regions = []
    for name, vals in table.items():
        if name == "전국":
            continue
        L, B = species(vals, 0, 1), species(vals, 2, 3)
        if not L["birds"] and not B["birds"]:
            continue          # 사육 실적이 없는 시도는 싣지 않는다
        regions.append({
            "name": name, "layer": L, "broiler": B,
            "layer_share": round(L["birds"] / layer["birds"] * 100, 1) if L["birds"] else None,
            "broiler_share": round(B["birds"] / broiler["birds"] * 100, 1) if B["birds"] else None,
        })
    regions.sort(key=lambda r: -((r["layer"]["birds"] or 0) + (r["broiler"]["birds"] or 0)))

    return {
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
        "period": label_period(cur), "period_code": cur,
        "prev_period": label_period(prev) if prev else None,
        "source": "축산물품질평가원 축산유통 통계누리",
        "table": "닭 시도 용도별(산란계,육용계) 사육규모별 가구수 및 마리수",
        "url": HUMAN_URL,
        "layer": layer, "broiler": broiler,
        "regions": regions,
        "stale": False,
    }


def keep_previous(reason):
    if not OUT_PATH.exists():
        print("  이전 데이터 없음 — 파일을 만들지 않음")
        return
    try:
        prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return
    prev["stale"] = True
    prev["stale_reason"] = reason
    prev["checked"] = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    OUT_PATH.write_text(json.dumps(prev, ensure_ascii=False, indent=2), encoding="utf-8")
    print("  ⚡ 이전 데이터 유지 + stale 표시")


def main():
    print("🐔 산란계·육계 사육 통계 수집 시작\n")
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        r = session.get(PAGE_URL, timeout=40)   # 세션 확보 — 없으면 이후 POST 실패
        r.raise_for_status()
        print("  세션 확보 OK (%dbytes)" % len(r.content))

        periods = fetch_periods(session)
        if not periods:
            raise RuntimeError("조회 가능한 분기가 없음")
        target = periods[-2:][::-1]
        print("  분기 %d개 중 사용: %s" % (len(periods), ", ".join(target)))

        table = parse_table(fetch_table(session, target), len(target))
        print("  시도 %d개 파싱" % len(table))
        payload = build(table, target)
    except Exception as e:
        print("❌ 수집 실패: %s: %s" % (type(e).__name__, e))
        keep_previous("%s: %s" % (type(e).__name__, e))
        sys.exit(1)

    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    L, B = payload["layer"], payload["broiler"]
    print("\n✅ %s 기준" % payload["period"])
    print("   산란계  %s농가 / %s마리 (호당 %s)" %
          (format(L["farms"], ","), format(L["birds"], ","), format(L["per_farm"] or 0, ",")))
    print("   육계    %s농가 / %s마리 (호당 %s)" %
          (format(B["farms"], ","), format(B["birds"], ","), format(B["per_farm"] or 0, ",")))
    for r_ in payload["regions"][:5]:
        print("   %-4s 산란계 %11s / 육계 %11s"
              % (r_["name"], format(r_["layer"]["birds"] or 0, ","),
                 format(r_["broiler"]["birds"] or 0, ",")))
    print("   ... 시도 %d개" % len(payload["regions"]))


if __name__ == "__main__":
    main()
