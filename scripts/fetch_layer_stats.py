#!/usr/bin/env python3
"""
축산물품질평가원 축산유통 통계누리(mtrace.go.kr) — 산란계 사육 마리수 수집

통계표: DT_1EO415 "(산란계)닭 시도, 월령별 마리수" (분기 단위, orgId=323)

이 사이트는 KOSIS 계열 OLAP 화면이라 단순 GET으로는 표가 안 나온다. 실제 순서는:

  1) GET  /statHtml/statHtml.do?orgId=..&tblId=..&vw_cd=..&list_id=..&conn_path=..
     → 세션 쿠키(JSESSIONID) 확보. 이 GET을 건너뛰면 이후 POST가 전부 실패한다.
  2) POST /statHtml/periodDivSelect.do  → 조회 가능한 분기 목록(JSON)
  3) POST /statHtml/html.do             → 표 HTML이 담긴 JSON

3)의 핵심은 `fieldList`다. 화면에서는 자바스크립트가 채우는 값이라 1)의 HTML에는
빈 문자열로 들어 있는데, 이게 비어 있으면 서버가 조회 대신 "페이지를 찾을 수 없습니다"
HTML(약 1017바이트)을 돌려준다 — 200 OK로 오기 때문에 상태코드만 봐서는 성공처럼
보인다. 그래서 아래 fetch_table()은 응답이 JSON인지까지 확인한다.

시도 코드(OV_L1_ID) 19개를 모두 요청해도 서버는 산란계 사육 실적이 있는 시도만
돌려준다(서울·부산·대전·제주 등은 빠짐). 브라우저로 같은 표를 열어도 동일하게
14행만 나오므로 이는 원본 데이터의 특성이지 수집 누락이 아니다.
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
TBL_ID = "DT_1EO415"
LIST_ID = "323_003_001"
BASE = "https://mtrace.go.kr"
PAGE_URL = (
    f"{BASE}/statHtml/statHtml.do?orgId={ORG_ID}&tblId={TBL_ID}"
    f"&vw_cd=xtl&list_id={LIST_ID}&conn_path=MT_ZTITLE"
)
# 사람이 눌러서 확인할 수 있는 주소 (index.html의 '원문' 링크)
HUMAN_URL = f"{BASE}/stats/stp/dtl/stl/xtlStatsList.do"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}
AJAX_HEADERS = {
    "Referer": PAGE_URL,
    "X-Requested-With": "XMLHttpRequest",
    "Origin": BASE,
}

# 월령 구분 항목 코드 (표의 열 순서와 같아야 한다)
ITEMS = [
    ("1022", "total"),     # 산란계:합계
    ("2023", "under3m"),   # 산란계:3개월미만
    ("3024", "m3to6"),     # 산란계:3~6개월
    ("4025", "over6m"),    # 산란계:6개월이상
]
# 시도 코드 전체. 실적이 없는 시도는 서버가 응답에서 빼고 준다.
REGION_CODES = [
    "1002", "2004", "3005", "4006", "5007", "6008", "7009", "8010", "9011",
    "10012", "11013", "12014", "13015", "14016", "15017", "16018", "17019",
    "18020", "19021",
]


def label_period(code):
    """'202602' → '2026 2/4'"""
    m = re.fullmatch(r"(\d{4})0?(\d)", code or "")
    return f"{m.group(1)} {m.group(2)}/4" if m else (code or "")


def base_params(period_codes):
    """html.do / periodDivSelect.do 공통 파라미터.

    itemMultiply·reqCellCnt는 화면이 셀 수를 세어 보내는 값이라 요청하는
    시도·항목·기간 수에 맞춰 같이 계산해 둔다.
    """
    cells_per_period = len(REGION_CODES) * len(ITEMS)
    return {
        "orgId": ORG_ID, "tblId": TBL_ID, "language": "ko",
        "colAxis": "TIME,ITEM", "rowAxis": "A", "isFirst": "N",
        "contextPath": "/statHtml", "vwCd": "xtl", "listId": LIST_ID,
        "connPath": "MT_ZTITLE", "statId": "1976001", "pubLog": "0",
        "viewKind": "1", "doAnal": "N", "dataOpt": "ko", "view": "table",
        "existStblCmmtKor": "N", "existStblCmmtEng": "N",
        "classAllArr": '[{"objVarId":"A","ovlSn":"1"}]',
        "classSet": '[{"objVarId":"A","ovlSn":"1","visible":"true"}]',
        "selectAllFlag": "N", "periodStr": "Q",
        "tblNm": "(산란계)닭 시도, 월령별 마리수",
        "itemMultiply": str(cells_per_period), "dbUser": "NSI_IN_323.",
        "usePivot": "N", "isChangedTableType": "N", "isChangedPeriodCo": "N",
        "isChangedPrdSort": "N", "p_classAllChkYn": "N", "p_classAllSelectYn": "N",
        "first_open": "Y", "reqCellCnt": str(cells_per_period * max(len(period_codes), 1)),
        "inheritYn": "N", "tableType": "default", "dataOpt2": "ko",
        "prdSort": "desc", "findData": "on",
        "downGridFileType": "xlsx", "downGridCellMerge": "Y", "downGridMeta": "Y",
        "downSort": "asc", "pointType": "screen", "downLargeFileType": "excel",
        "downLargeExprType": "1", "downLargeSort": "asc", "naviInfo": "tabTimeText",
        "itemChkLi": "4025", "classAllSelect": "on", "classLvlAllChk1_1": "on",
        "classChkLi1_1": "19021=", "defaultFolder": "1", "headCheck": "Q",
        "timeChkQ": period_codes[-1] if period_codes else "",
    }


def fetch_periods(session):
    """조회 가능한 분기 코드를 오름차순으로 반환."""
    r = session.post(f"{BASE}/statHtml/periodDivSelect.do",
                     data=base_params([]), headers=AJAX_HEADERS, timeout=40)
    r.raise_for_status()
    rows = r.json().get("result", [])
    return sorted({d["prdDe"] for d in rows if d.get("prdDe")})


def fetch_table(session, period_codes):
    """표 HTML 문자열 반환. period_codes는 최신순."""
    field_list = [{"targetId": "PRD", "targetValue": "",
                   "prdValue": "Q,%s,@" % ",".join(period_codes)}]
    field_list += [{"targetId": "ITM_ID", "targetValue": c, "prdValue": ""}
                   for c, _ in ITEMS]
    field_list += [{"targetId": "OV_L1_ID", "targetValue": c, "prdValue": ""}
                   for c in REGION_CODES]

    params = base_params(period_codes)
    params["fieldList"] = json.dumps(field_list, ensure_ascii=False)

    r = session.post(f"{BASE}/statHtml/html.do", data=params,
                     headers=AJAX_HEADERS, timeout=60)
    r.raise_for_status()
    # fieldList가 잘못되면 200 OK + 오류 HTML이 온다. JSON인지 먼저 확인.
    if "json" not in r.headers.get("Content-Type", "") and not r.text.lstrip().startswith("{"):
        raise RuntimeError("표 대신 HTML 응답을 받음 (%dbytes) — 요청 파라미터 확인 필요"
                           % len(r.content))
    data = r.json()
    if data.get("errMsg"):
        raise RuntimeError("서버 오류: %s" % data["errMsg"])
    result = data.get("result") or []
    if not result:
        raise RuntimeError("응답에 표가 없음")
    return result[0]


def parse_table(html, period_count):
    """
    표 HTML → {시도명: [기간0 값 4개, 기간1 값 4개, ...]}

    값 셀은 <td class='value' title='78,985,355'> 형태이고 결측은 '-'로 온다.
    행 단위로 끊어서 파싱해야 시도와 값이 어긋나지 않는다.
    """
    out = {}
    for tr in re.findall(r"<tr>([\s\S]*?)</tr>", html):
        m = re.search(r"<td class='first'[^>]*title='([^']*)'", tr)
        if not m:
            continue
        name = m.group(1).strip()
        vals = []
        for raw in re.findall(r"<td class='value'[^>]*title='([^']*)'", tr):
            raw = raw.replace(",", "").strip()
            vals.append(int(raw) if re.fullmatch(r"-?\d+", raw) else None)
        want = period_count * len(ITEMS)
        if name and len(vals) >= want:
            out[name] = vals[:want]
    return out


def build_payload(table, period_codes):
    """파싱 결과 → 화면이 그대로 쓰는 형태로 정리."""
    def slot(vals, period_idx, item_idx):
        i = period_idx * len(ITEMS) + item_idx
        return vals[i] if i < len(vals) else None

    cur, prev = period_codes[0], (period_codes[1] if len(period_codes) > 1 else None)

    nat = table.get("전국")
    if not nat or slot(nat, 0, 0) is None:
        raise RuntimeError("전국 합계를 찾지 못함")

    nat_total = slot(nat, 0, 0)
    nat_prev = slot(nat, 1, 0) if prev else None
    national = {
        "total": nat_total,
        "prev": nat_prev,
        "diff": (nat_total - nat_prev) if nat_prev else None,
        "pct": round((nat_total - nat_prev) / nat_prev * 100, 1) if nat_prev else None,
        "under3m": slot(nat, 0, 1),
        "m3to6": slot(nat, 0, 2),
        "over6m": slot(nat, 0, 3),
    }

    regions = []
    for name, vals in table.items():
        if name == "전국":
            continue
        total = slot(vals, 0, 0)
        if total is None:
            continue
        p = slot(vals, 1, 0) if prev else None
        regions.append({
            "name": name,
            "total": total,
            "prev": p,
            "pct": round((total - p) / p * 100, 1) if p else None,
            "share": round(total / nat_total * 100, 1) if nat_total else None,
        })
    regions.sort(key=lambda r: r["total"], reverse=True)

    # 서울·부산·대전·제주처럼 산란계 실적이 없어 표에서 빠지는 시도가 있어
    # 시도 합계는 전국보다 작다. 화면에서 숫자가 안 맞아 보이지 않도록
    # 그 차이를 '기타'로 따로 남긴다.
    listed = sum(r["total"] for r in regions)
    national["listed_sum"] = listed
    national["etc"] = nat_total - listed

    return {
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
        "period": label_period(cur),
        "period_code": cur,
        "prev_period": label_period(prev) if prev else None,
        "source": "축산물품질평가원 축산유통 통계누리",
        "table": "(산란계)닭 시도, 월령별 마리수",
        "url": HUMAN_URL,
        "national": national,
        "regions": regions,
        "stale": False,
    }


def load_previous():
    if not OUT_PATH.exists():
        return None
    try:
        return json.loads(OUT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def keep_previous(prev, reason):
    """
    수집 실패 시 이전 데이터를 그대로 두고 stale만 표시한다.
    분기 통계라 한 번 실패했다고 화면을 비우면 최대 3개월간 빈 화면이 된다.
    """
    if not prev:
        print("  이전 데이터도 없어 파일을 만들지 않음")
        return False
    prev["stale"] = True
    prev["stale_reason"] = reason
    prev["checked"] = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(json.dumps(prev, ensure_ascii=False, indent=2), encoding="utf-8")
    print("  ⚡ 이전 데이터 유지 + stale 표시")
    return True


def main():
    print("🥚 산란계 사육수 수집 시작\n")
    prev_json = load_previous()

    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        # 1) 세션 확보 — 이 GET 없이는 이후 POST가 전부 실패한다.
        r = session.get(PAGE_URL, timeout=40)
        r.raise_for_status()
        print("  세션 확보 OK (%dbytes)" % len(r.content))

        # 2) 최신 분기 2개 (현재 + 직전, 증감 계산용)
        periods = fetch_periods(session)
        if not periods:
            raise RuntimeError("조회 가능한 분기가 없음")
        target = periods[-2:][::-1]
        print("  분기 %d개 중 사용: %s" % (len(periods), ", ".join(target)))

        # 3) 표 조회
        html = fetch_table(session, target)
        table = parse_table(html, len(target))
        print("  시도 %d개 파싱" % len(table))

        payload = build_payload(table, target)
    except Exception as e:
        print("❌ 수집 실패: %s: %s" % (type(e).__name__, e))
        keep_previous(prev_json, "%s: %s" % (type(e).__name__, e))
        sys.exit(1)

    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    n = payload["national"]
    print("\n✅ %s 기준" % payload["period"])
    print("   전국 %s마리 (전분기 대비 %s%s)" % (
        format(n["total"], ","),
        ("+" if (n["diff"] or 0) >= 0 else "") + format(n["diff"], ",") if n["diff"] is not None else "-",
        " / %+.1f%%" % n["pct"] if n["pct"] is not None else ""))
    for r_ in payload["regions"][:5]:
        print("   %-4s %13s (%.1f%%)" % (r_["name"], format(r_["total"], ","), r_["share"]))
    print("   ... 시도 %d개" % len(payload["regions"]))


if __name__ == "__main__":
    main()
