#!/usr/bin/env python3
"""
축산물품질평가원 공공데이터 API - URL 탐색 + 수집
GitHub Actions에서 실행하면 실제 작동하는 URL을 자동 탐색합니다.
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

def try_url(url, params, label=""):
    """URL 테스트 → (성공여부, 응답텍스트)"""
    try:
        r = requests.get(url, params=params, timeout=10)
        size = len(r.text)
        has_data = r.status_code == 200 and size > 200 and "<item>" in r.text
        print(f"  {'✅' if has_data else '❌'} [{label}] HTTP {r.status_code} ({size}bytes)")
        if r.status_code == 200 and size > 50:
            print(f"     {r.text[:200]}")
        return has_data, r.text if has_data else ""
    except Exception as e:
        print(f"  ❌ [{label}] {e}")
        return False, ""

def find_and_call(api_key, candidates, date_params):
    """후보 URL들을 순서대로 시도해서 첫 번째 성공한 것 반환"""
    for label, url in candidates:
        ok, text = try_url(url, {**date_params, "serviceKey": api_key}, label)
        if ok:
            return url, text
    return None, ""

def parse_xml_items(xml_text):
    try:
        root = ET.fromstring(xml_text)
        return root.findall('.//item')
    except:
        return []

def xml_val(item, *tags):
    for tag in tags:
        el = item.find(tag)
        if el is not None and el.text:
            v = el.text.strip()
            try: return int(v.replace(',',''))
            except: return v
    return None

def main():
    api_key = get_api_key()
    now_kst = datetime.now(KST)
    today = now_kst.strftime("%Y%m%d")
    start = (now_kst - timedelta(days=5)).strftime("%Y%m%d")
    
    date_params = {"pageNo":1,"numOfRows":20,"startYmd":start,"endYmd":today}
    result = {"updated": now_kst.strftime("%Y-%m-%d %H:%M KST"), "prices":{}}
    Path("prices").mkdir(exist_ok=True)

    # ── 육계 산지 URL 탐색 ──────────────────────────────────────────────────
    print("\n🐔 육계 산지가격 URL 탐색...")
    chicken_prod_candidates = [
        ("broilerProducerPriceInfo", f"{BASE}/poultry/broilerProducerPriceInfo"),
        ("chickenProducerPriceInfo", f"{BASE}/poultry/chickenProducerPriceInfo"),
        ("broilerProducer",          f"{BASE}/poultry/broilerProducer"),
        ("broilerSanji",             f"{BASE}/poultry/broilerSanji"),
        ("broiler",                  f"{BASE}/poultry/broiler"),
        ("nativechichen",            f"{BASE}/poultry/nativechichen"),
        ("poultryProducer",          f"{BASE}/poultry/poultryProducer"),
        ("layingChicken",            f"{BASE}/poultry/layingChicken"),
        ("chickenPrice",             f"{BASE}/poultry/chickenPrice"),
        ("broilerPrice",             f"{BASE}/poultry/broilerPrice"),
    ]
    prod_url, prod_xml = find_and_call(api_key, chicken_prod_candidates, date_params)

    # ── 육계 도매 URL 탐색 ──────────────────────────────────────────────────
    print("\n🐔 육계 도매가격 URL 탐색...")
    chicken_whole_candidates = [
        ("broilerWholesalePriceInfo", f"{BASE}/poultry/broilerWholesalePriceInfo"),
        ("chickenWholesalePriceInfo", f"{BASE}/poultry/chickenWholesalePriceInfo"),
        ("broilerWholesale",          f"{BASE}/poultry/broilerWholesale"),
        ("broilerDomaePriceInfo",     f"{BASE}/poultry/broilerDomaePriceInfo"),
        ("chickenDomaePriceInfo",     f"{BASE}/poultry/chickenDomaePriceInfo"),
        ("poultryWholesale",          f"{BASE}/poultry/poultryWholesale"),
    ]
    whole_url, whole_xml = find_and_call(api_key, chicken_whole_candidates, date_params)

    # 육계 결과 조합
    if prod_xml or whole_xml:
        chicken = {"date": today[:4]+"-"+today[4:6]+"-"+today[6:]}
        if prod_xml:
            items = parse_xml_items(prod_xml)
            if items:
                latest = items[0]
                chicken["sanji_live"] = xml_val(latest, "avgPrice","average","price","sajiPrice")
                chicken["sanji_url"]  = prod_url
        if whole_xml:
            items = parse_xml_items(whole_xml)
            if items:
                latest = items[0]
                chicken["wholesale_all"] = xml_val(latest, "avgPrice","average","price")
                chicken["wholesale_url"] = whole_url
        result["prices"]["chicken"] = chicken
        print(f"\n  ✅ 육계: 산지={chicken.get('sanji_live')} 도매={chicken.get('wholesale_all')}")

    # ── 계란 URL 탐색 ───────────────────────────────────────────────────────
    print("\n🥚 계란 일일가격 URL 탐색...")
    egg_candidates = [
        ("egg/dailyPriceInfo",       f"{BASE}/egg/dailyPriceInfo"),
        ("egg/eggDailyPriceInfo",    f"{BASE}/egg/eggDailyPriceInfo"),
        ("poultry/egg",              f"{BASE}/poultry/egg"),
        ("poultry/eggPrice",         f"{BASE}/poultry/eggPrice"),
        ("poultry/eggDailyPrice",    f"{BASE}/poultry/eggDailyPrice"),
        ("egg/eggPrice",             f"{BASE}/egg/eggPrice"),
        ("egg/price",                f"{BASE}/egg/price"),
        ("poultry/layingHen",        f"{BASE}/poultry/layingHen"),
        ("poultry/layingOldChicken", f"{BASE}/poultry/layingOldChicken"),
    ]
    egg_url, egg_xml = find_and_call(api_key, egg_candidates, date_params)

    if egg_xml:
        items = parse_xml_items(egg_xml)
        egg = {"date": today[:4]+"-"+today[4:6]+"-"+today[6:], "egg_url": egg_url, "records":[]}
        for item in items[:10]:
            size_name = xml_val(item, "sizeName","typeName","gradeName","gubn","size")
            avg_price = xml_val(item, "avgPrice","average","price")
            egg["records"].append({"size": str(size_name), "price": avg_price})
            print(f"     계란 {size_name}: {avg_price}")
        # XL/특란 → 10개 단위
        for r in egg["records"]:
            s = str(r.get("size",""))
            if any(x in s for x in ["XL","특란","특"]):
                egg["xl_10"] = round(r["price"]*10) if r.get("price") else None
            elif any(x in s for x in ["L","대란","대"]):
                egg["l_10"] = round(r["price"]*10) if r.get("price") else None
        result["prices"]["egg"] = egg
        print(f"\n  ✅ 계란: XL={egg.get('xl_10')} L={egg.get('l_10')}")

    # 성공한 URL 저장 (다음 실행 참고용)
    url_log = {
        "chicken_producer": prod_url,
        "chicken_wholesale": whole_url,
        "egg": egg_url,
    }
    result["found_urls"] = url_log

    with open("prices/prices.json","w",encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    total = len(result["prices"])
    print(f"\n✅ prices.json 저장 완료 ({total}개 수집)")
    print(f"   발견된 URL: {json.dumps(url_log, ensure_ascii=False, indent=2)}")

if __name__ == "__main__":
    main()
