#!/usr/bin/env python3
"""
축산물품질평가원 공공데이터 API 시세 수집
- 육계: 가금산물 일일거래가격정보 (15073985) → 육계 산지/도매가
- 계란: poultry/egg (기존 확인된 URL)
- 토종닭 nativechichen은 육계가 아니므로 제외

GitHub Actions에서 EKAPE_API_KEY 환경변수 필요
"""

import os, sys, requests, json, xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST   = timezone(timedelta(hours=9))
BASE  = "http://data.ekape.or.kr/openapi-data/service/user/grade"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; livestock-dashboard/1.0)",
    "Accept": "application/xml,text/xml,*/*",
}

def get_api_key():
    key = os.environ.get("EKAPE_API_KEY")
    if not key:
        print("❌ EKAPE_API_KEY 없음"); sys.exit(1)
    return key

def call_api(endpoint, api_key, days_back=5, rows=30):
    now   = datetime.now(KST)
    start = (now - timedelta(days=days_back)).strftime("%Y%m%d")
    end   = now.strftime("%Y%m%d")
    url   = f"{BASE}/{endpoint}"
    r = requests.get(url, headers=HEADERS, timeout=15, params={
        "serviceKey": api_key, "pageNo": 1, "numOfRows": rows,
        "startYmd": start, "endYmd": end,
    })
    r.encoding = 'utf-8'
    if r.status_code != 200 or not r.text.strip():
        print(f"  ❌ HTTP {r.status_code} → {url}")
        return []
    try:
        return ET.fromstring(r.text).findall('.//item')
    except Exception as e:
        print(f"  ❌ XML 파싱 오류: {e}")
        return []

def probe_url(endpoint, api_key, days_back=5):
    """URL 유효성 탐색 — 200 + <item> 있으면 True"""
    now   = datetime.now(KST)
    start = (now - timedelta(days=days_back)).strftime("%Y%m%d")
    end   = now.strftime("%Y%m%d")
    url   = f"{BASE}/{endpoint}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8, params={
            "serviceKey": api_key, "pageNo": 1, "numOfRows": 5,
            "startYmd": start, "endYmd": end,
        })
        r.encoding = 'utf-8'
        has_item = r.status_code == 200 and '<item>' in r.text
        print(f"  {'✅' if has_item else '❌'} HTTP {r.status_code} ({len(r.text)}B) {endpoint}")
        if has_item:
            print(f"     {r.text[:300]}")
        return has_item, r.text if has_item else ""
    except Exception as e:
        print(f"  ❌ {endpoint}: {e}")
        return False, ""

def ival(item, *tags):
    for tag in tags:
        el = item.find(tag)
        if el is not None and el.text and el.text.strip() not in ('', '0'):
            try: return int(float(el.text.strip().replace(',', '')))
            except: pass
    return None

def sval(item, tag):
    el = item.find(tag)
    return el.text.strip() if el is not None and el.text else ""

def diff(a, b):
    return round(a - b) if a and b else None

def to10(v):
    return round(v / 3) if v else None

def main():
    api_key = get_api_key()
    now_kst = datetime.now(KST)
    result  = {"updated": now_kst.strftime("%Y-%m-%d %H:%M KST"), "prices": {}}
    Path("prices").mkdir(exist_ok=True)

    # ── 육계 URL 탐색 ────────────────────────────────────────────────────────
    print("\n🐔 육계 생계가격 URL 탐색...")
    # 15073985 API의 가능한 엔드포인트 후보
    broiler_candidates = [
        "poultry/broilerDailyPriceInfo",
        "poultry/broilerSanjiPrice",
        "poultry/broilerPrice",
        "poultry/broilerProducerPrice",
        "poultry/chickenDailyPrice",
        "poultry/liveChickenPrice",
        "poultry/liveChicken",
        "poultry/broilerLivePrice",
        "poultry/broilerMarketPrice",
        "poultry/poultryDailyPrice",
        "poultry/broilerDomae",
        "poultry/broilerSanji",
        "poultry/chick",
        "poultry/dailyPrice",
        "poultry/priceInfo",
    ]

    broiler_url  = None
    broiler_xml  = ""
    for ep in broiler_candidates:
        ok, xml = probe_url(ep, api_key)
        if ok:
            broiler_url = ep
            broiler_xml = xml
            break

    if broiler_xml:
        try:
            items = ET.fromstring(broiler_xml).findall('.//item')
            items.sort(key=lambda x: sval(x,'modYmd'), reverse=True)
            r0 = items[0] if items else None
            r1 = items[1] if len(items)>1 else None

            # 태그 구조 출력
            if r0:
                print("\n  [첫 번째 item 태그]")
                for ch in r0:
                    print(f"    <{ch.tag}>{ch.text}</{ch.tag}>")

            date_raw = sval(r0,'modYmd') if r0 else ""
            date_str = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}" if len(date_raw)==8 else date_raw

            avg0 = ival(r0,'average','avgPrice','sanji','price') if r0 else None
            avg1 = ival(r1,'average','avgPrice','sanji','price') if r1 else None
            result["prices"]["chicken"] = {
                "date":            date_str,
                "sanji_live":      avg0,
                "prev_sanji":      avg1,
                "diff_sanji_live": diff(avg0, avg1),
                "source_url":      broiler_url,
            }
            print(f"\n  ✅ 육계: {date_str} / {avg0}원/kg")
        except Exception as e:
            print(f"  ❌ 파싱 오류: {e}")
    else:
        print("\n  ⚠️ 육계 URL 미발견 — 기존 nativechichen(토종닭) 데이터와 다름 주의")
        result["prices"]["chicken"] = {
            "date": None,
            "sanji_live": None,
            "note": "육계 API 엔드포인트 미발견 — 공공데이터포털에서 15073985 오퍼레이션 URL 확인 필요"
        }

    # ── 계란 (기존 확인된 URL) ────────────────────────────────────────────────
    print("\n🥚 계란 가격 수집...")
    items = call_api("poultry/egg", api_key)

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
        if w0:
            egg.update({
                "w_special_30": ival(w0,'special'), "w_verybig_30": ival(w0,'verybig'),
                "w_big_30":     ival(w0,'big'),     "w_medium_30":  ival(w0,'medium'),
                "xl_10":  to10(ival(w0,'special')), "l_10": to10(ival(w0,'big')),
                "m_10":   to10(ival(w0,'medium')),  "xl2_10": to10(ival(w0,'verybig')),
                "xl_30":  ival(w0,'special'),        "l_30": ival(w0,'big'),
                "diff_xl_10": diff(to10(ival(w0,'special')), to10(ival(w1,'special'))) if w1 else None,
                "diff_l_10":  diff(to10(ival(w0,'big')),     to10(ival(w1,'big')))     if w1 else None,
            })
        if p0:
            egg.update({
                "p_special_30": ival(p0,'special'), "p_verybig_30": ival(p0,'verybig'),
                "p_big_30":     ival(p0,'big'),     "p_medium_30":  ival(p0,'medium'),
                "p_xl_10": to10(ival(p0,'special')), "p_l_10": to10(ival(p0,'big')),
            })
        result["prices"]["egg"] = egg
        print(f"  ✅ {date_str} / 도매XL={egg.get('xl_10')}원/10개 산지XL={egg.get('p_xl_10')}원/10개")

    print("\n⚠️  돼지·한우: 공공데이터 API 미제공")

    with open("prices/prices.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n✅ prices.json 저장 완료 ({len(result['prices'])}개, {result['updated']})")

if __name__ == "__main__":
    main()
