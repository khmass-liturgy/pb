#!/usr/bin/env python3
"""
축산물품질평가원 공공데이터 API 시세 수집 (정식 버전)
GitHub Actions에서 매일 실행 → prices/prices.json 저장

확인된 API:
  육계: .../poultry/nativechichen
    → agency(대리점), mart(마트), average(전체평균), 단위: 원/kg
  계란: .../poultry/egg
    → typeName(도매/산지), special(XL특란), verybig(2XL왕란),
       big(L대란), medium(M중란), small(S소란), 단위: 원/30개
"""

import os, sys, requests, json, xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
BASE = "http://data.ekape.or.kr/openapi-data/service/user/grade"

def get_api_key():
    key = os.environ.get("EKAPE_API_KEY")
    if not key:
        print("❌ EKAPE_API_KEY 없음")
        sys.exit(1)
    return key

def call_api(endpoint, api_key, days_back=5, rows=30):
    now   = datetime.now(KST)
    start = (now - timedelta(days=days_back)).strftime("%Y%m%d")
    end   = now.strftime("%Y%m%d")
    r = requests.get(f"{BASE}/{endpoint}", timeout=15, params={
        "serviceKey": api_key, "pageNo": 1, "numOfRows": rows,
        "startYmd": start, "endYmd": end,
    })
    r.encoding = 'utf-8'
    if r.status_code != 200 or not r.text.strip():
        print(f"  ❌ HTTP {r.status_code}")
        return []
    try:
        return ET.fromstring(r.text).findall('.//item')
    except Exception as e:
        print(f"  ❌ XML 파싱 오류: {e}")
        return []

def ival(item, tag):
    el = item.find(tag)
    if el is not None and el.text and el.text.strip() not in ('', '0'):
        try: return int(float(el.text.strip().replace(',','')))
        except: pass
    return None

def sval(item, tag):
    el = item.find(tag)
    return el.text.strip() if el is not None and el.text else ""

def diff(a, b):
    return round(a - b) if a and b else None

def to10(v):
    """원/30개 → 원/10개"""
    return round(v / 3) if v else None

def main():
    api_key = get_api_key()
    now_kst = datetime.now(KST)
    result  = {"updated": now_kst.strftime("%Y-%m-%d %H:%M KST"), "prices": {}}
    Path("prices").mkdir(exist_ok=True)

    # ── 육계 ─────────────────────────────────────────────────────────────────
    print("🐔 육계 가격 수집...")
    items = call_api("poultry/nativechichen", api_key)
    # modYmd 기준 정렬 후 최신 2일
    items.sort(key=lambda x: sval(x,'modYmd'), reverse=True)
    r0 = items[0] if len(items)>0 else None
    r1 = items[1] if len(items)>1 else None

    if r0:
        date_raw = sval(r0,'modYmd')  # 20260714
        date_str = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}" if len(date_raw)==8 else date_raw

        avg0 = ival(r0,'average'); avg1 = ival(r1,'average') if r1 else None
        agency0 = ival(r0,'agency'); mart0 = ival(r0,'mart')

        result["prices"]["chicken"] = {
            "date":            date_str,
            "sanji_live":      avg0,          # 전체 평균 원/kg
            "agency":          agency0,       # 대리점 원/kg
            "mart":            mart0,         # 마트 원/kg
            "prev_sanji":      avg1,
            "diff_sanji_live": diff(avg0, avg1),
        }
        d = result["prices"]["chicken"]["diff_sanji_live"]
        arrow = f"▲{d}" if d and d>0 else f"▼{abs(d)}" if d and d<0 else "±0"
        print(f"  ✅ {date_str} / 평균 {avg0:,}원/kg ({arrow})")

    # ── 계란 ─────────────────────────────────────────────────────────────────
    print("🥚 계란 가격 수집...")
    items = call_api("poultry/egg", api_key)

    # typeName 별 분리 (도매/산지), modYmd 기준 최신
    def filter_type(items, type_name):
        matched = [x for x in items if type_name in sval(x,'typeName')]
        matched.sort(key=lambda x: sval(x,'modYmd'), reverse=True)
        return matched

    wholesale = filter_type(items, "도매")
    producer  = filter_type(items, "산지")

    w0 = wholesale[0] if wholesale else None
    w1 = wholesale[1] if len(wholesale)>1 else None
    p0 = producer[0]  if producer  else None
    p1 = producer[1]  if len(producer)>1  else None

    if w0 or p0:
        date_raw = sval(w0 or p0,'modYmd')
        date_str = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}" if len(date_raw)==8 else date_raw

        egg = {"date": date_str}

        # 도매 (원/30개)
        if w0:
            egg.update({
                "w_special_30": ival(w0,'special'),   # XL 특란
                "w_verybig_30": ival(w0,'verybig'),   # 2XL 왕란
                "w_big_30":     ival(w0,'big'),        # L 대란
                "w_medium_30":  ival(w0,'medium'),     # M 중란
                # 10개 단위 환산
                "xl_10":        to10(ival(w0,'special')),
                "l_10":         to10(ival(w0,'big')),
                "m_10":         to10(ival(w0,'medium')),
                "xl2_10":       to10(ival(w0,'verybig')),
                # 30개 단위
                "xl_30":        ival(w0,'special'),
                "l_30":         ival(w0,'big'),
                # 전일대비 (10개)
                "diff_xl_10":   diff(to10(ival(w0,'special')), to10(ival(w1,'special'))) if w1 else None,
                "diff_l_10":    diff(to10(ival(w0,'big')),     to10(ival(w1,'big')))     if w1 else None,
            })

        # 산지 (원/30개)
        if p0:
            egg.update({
                "p_special_30": ival(p0,'special'),
                "p_verybig_30": ival(p0,'verybig'),
                "p_big_30":     ival(p0,'big'),
                "p_medium_30":  ival(p0,'medium'),
                # 산지 10개 환산
                "p_xl_10":      to10(ival(p0,'special')),
                "p_l_10":       to10(ival(p0,'big')),
            })

        result["prices"]["egg"] = egg

        xl10 = egg.get('xl_10'); l10 = egg.get('l_10')
        pxl10 = egg.get('p_xl_10'); pl10 = egg.get('p_l_10')
        print(f"  ✅ {date_str}")
        if xl10: print(f"     도매 XL(특란): {xl10:,}원/10개  L(대란): {l10:,}원/10개" if l10 else f"     도매 XL: {xl10:,}원/10개")
        if pxl10: print(f"     산지 XL(특란): {pxl10:,}원/10개  L(대란): {pl10:,}원/10개" if pl10 else f"     산지 XL: {pxl10:,}원/10개")

    # 돼지·한우 별도 API 없음 안내
    print("⚠️  돼지·한우: 공공데이터 API 없음 (KAMIS API 별도 신청 필요)")

    with open("prices/prices.json","w",encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n✅ prices.json 저장 완료 ({len(result['prices'])}개, {result['updated']})")

if __name__ == "__main__":
    main()
