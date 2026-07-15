#!/usr/bin/env python3
"""
축산물품질평가원 공공데이터 API 기반 시세 수집 스크립트
GitHub Actions에서 매일 실행 → prices/prices.json 저장

API: 공공데이터포털 (data.go.kr) - 자동승인, 무료
- 육계 산지/도매 일일가격: data.ekape.or.kr/openapi-data/service/user/grade/poultry/
- 계란 일일가격: data.ekape.or.kr/openapi-data/service/user/grade/egg/

환경변수: EKAPE_API_KEY (GitHub Secrets → Settings → Secrets → EKAPE_API_KEY)
"""

import os
import sys
import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
BASE_URL = "http://data.ekape.or.kr/openapi-data/service/user/grade"

def get_api_key():
    key = os.environ.get("EKAPE_API_KEY")
    if not key:
        print("❌ EKAPE_API_KEY 환경변수 없음")
        print("   GitHub: Settings → Secrets → EKAPE_API_KEY 에 인증키 설정 필요")
        sys.exit(1)
    return key

def call_api(endpoint, params):
    """공공데이터 API 호출 → items 리스트 반환"""
    url = f"{BASE_URL}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.encoding = 'utf-8'
        print(f"    HTTP {resp.status_code} ({len(resp.text)}bytes)")
        if resp.status_code != 200:
            print(f"    ❌ 응답 오류: {resp.text[:200]}")
            return []
        root = ET.fromstring(resp.text)
        # 결과 코드 확인
        result_code = root.findtext('.//resultCode', '')
        result_msg  = root.findtext('.//resultMsg', '')
        if result_code not in ('00', '0000', ''):
            print(f"    ❌ API 오류: {result_code} - {result_msg}")
            return []
        items = root.findall('.//item')
        return items
    except Exception as e:
        print(f"    ❌ 오류: {e}")
        return []

def xml_text(item, tag, default=None):
    """XML item에서 태그 값 추출"""
    el = item.find(tag)
    if el is not None and el.text:
        return el.text.strip()
    return default

def safe_int(val):
    if val is None:
        return None
    try:
        return int(str(val).replace(',', ''))
    except:
        return None

def safe_float(val):
    if val is None:
        return None
    try:
        return float(str(val).replace(',', ''))
    except:
        return None

def date_params(api_key, days_back=2):
    """오늘~days_back일 전 날짜 파라미터 생성"""
    today = datetime.now(KST)
    start = today - timedelta(days=days_back)
    return {
        "serviceKey": api_key,
        "pageNo": 1,
        "numOfRows": 10,
        "startYmd": start.strftime("%Y%m%d"),
        "endYmd": today.strftime("%Y%m%d"),
    }

# ── 육계 산지가격 ─────────────────────────────────────────────────────────────
def fetch_chicken_producer(api_key):
    """
    엔드포인트: poultry/broilerProducerPriceInfo
    반환 필드: tradeDate(거래일), tradeGubn(거래구분), avgPrice(평균가격), unit(단위)
    """
    print("  GET 육계 산지가격...")
    params = date_params(api_key)
    items = call_api("poultry/broilerProducerPriceInfo", params)
    if not items:
        return None

    # 최신 날짜 데이터
    records = []
    for item in items:
        records.append({
            "date":      xml_text(item, "tradeDate") or xml_text(item, "modYmd", ""),
            "type":      xml_text(item, "tradeGubn") or xml_text(item, "typeName", ""),
            "avg_price": safe_int(xml_text(item, "avgPrice") or xml_text(item, "average")),
            "unit":      xml_text(item, "unit", "원/kg"),
        })

    if not records:
        return None

    # 날짜 정렬 후 최신 2일치
    records.sort(key=lambda x: x["date"], reverse=True)
    latest_date = records[0]["date"]
    today_records = [r for r in records if r["date"] == latest_date]
    prev_records  = [r for r in records if r["date"] != latest_date]

    def get_price(recs, type_hint=None):
        if not recs:
            return None
        if type_hint:
            matched = [r for r in recs if type_hint in (r["type"] or "")]
            if matched:
                return matched[0]["avg_price"]
        return recs[0]["avg_price"]

    today_price = get_price(today_records)
    prev_price  = get_price(prev_records)

    return {
        "date":           latest_date,
        "sanji_live":     today_price,
        "prev_sanji":     prev_price,
        "diff_sanji_live": round(today_price - prev_price) if today_price and prev_price else None,
        "records":        today_records[:5],
    }

# ── 육계 도매가격 ─────────────────────────────────────────────────────────────
def fetch_chicken_wholesale(api_key):
    """
    엔드포인트: poultry/broilerWholesalePriceInfo
    반환 필드: tradeDate, typeName(등급/부위), avgPrice
    """
    print("  GET 육계 도매가격...")
    params = date_params(api_key)
    items = call_api("poultry/broilerWholesalePriceInfo", params)
    if not items:
        return None

    records = []
    for item in items:
        records.append({
            "date":      xml_text(item, "tradeDate") or xml_text(item, "modYmd", ""),
            "type":      xml_text(item, "typeName", ""),
            "avg_price": safe_int(xml_text(item, "avgPrice") or xml_text(item, "average")),
        })

    if not records:
        return None

    records.sort(key=lambda x: x["date"], reverse=True)
    latest_date = records[0]["date"]
    today_records = [r for r in records if r["date"] == latest_date]
    prev_records  = [r for r in records if r["date"] != latest_date]

    # 10호 기준 도매가
    def get_10ho(recs):
        matched = [r for r in recs if "10" in (r["type"] or "")]
        if matched:
            return matched[0]["avg_price"]
        return recs[0]["avg_price"] if recs else None

    today_10 = get_10ho(today_records)
    prev_10  = get_10ho(prev_records)

    # 전체 평균
    all_prices = [r["avg_price"] for r in today_records if r["avg_price"]]
    avg_all = round(sum(all_prices) / len(all_prices)) if all_prices else None

    return {
        "date":               latest_date,
        "wholesale_10":       today_10,
        "wholesale_all":      avg_all,
        "diff_wholesale_all": round(avg_all - get_10ho(prev_records)) if avg_all and get_10ho(prev_records) else None,
        "records":            today_records[:5],
    }

# ── 계란 일일가격 ─────────────────────────────────────────────────────────────
def fetch_egg(api_key):
    """
    엔드포인트: egg/dailyPriceInfo
    반환 필드: tradeDate, sizeName(특란/대란 등), avgPrice, unit
    """
    print("  GET 계란 일일가격...")
    params = date_params(api_key)
    items = call_api("egg/dailyPriceInfo", params)
    if not items:
        return None

    records = []
    for item in items:
        records.append({
            "date":      xml_text(item, "tradeDate") or xml_text(item, "modYmd", ""),
            "size":      xml_text(item, "sizeName") or xml_text(item, "typeName", ""),
            "avg_price": safe_int(xml_text(item, "avgPrice") or xml_text(item, "average")),
            "unit":      xml_text(item, "unit", ""),
        })

    if not records:
        return None

    records.sort(key=lambda x: x["date"], reverse=True)
    latest_date = records[0]["date"]
    today_records = [r for r in records if r["date"] == latest_date]
    prev_records  = [r for r in records if r["date"] != latest_date]

    def get_by_size(recs, keywords):
        for kw in keywords:
            matched = [r for r in recs if kw in (r["size"] or "")]
            if matched:
                return matched[0]["avg_price"]
        return None

    # XL=특란, L=대란 (2026.5.21 규격명 변경)
    xl_today = get_by_size(today_records, ["XL", "특란", "특"])
    l_today  = get_by_size(today_records, ["L", "대란", "대"])
    xl_prev  = get_by_size(prev_records,  ["XL", "특란", "특"])
    l_prev   = get_by_size(prev_records,  ["L", "대란", "대"])

    # 원/개 → 원/10개 환산
    def to10(v): return round(v * 10) if v else None

    return {
        "date":       latest_date,
        "xl_10":      to10(xl_today),   # XL(특란) 원/10개
        "l_10":       to10(l_today),    # L(대란) 원/10개
        "xl_30":      round(xl_today * 30) if xl_today else None,
        "l_30":       round(l_today  * 30) if l_today  else None,
        "diff_xl_10": round((xl_today - xl_prev) * 10) if xl_today and xl_prev else None,
        "diff_l_10":  round((l_today  - l_prev)  * 10) if l_today  and l_prev  else None,
        "records":    today_records[:8],
    }

# ── 메인 ──────────────────────────────────────────────────────────────────────
def main():
    api_key = get_api_key()
    now_kst = datetime.now(KST)
    result = {"updated": now_kst.strftime("%Y-%m-%d %H:%M KST"), "prices": {}}
    Path("prices").mkdir(exist_ok=True)

    print("🐔 육계 산지가격 수집...")
    producer = fetch_chicken_producer(api_key)
    wholesale = None
    print("🐔 육계 도매가격 수집...")
    wholesale = fetch_chicken_wholesale(api_key)

    if producer or wholesale:
        chicken = {
            "date":               (producer or wholesale or {}).get("date", ""),
            "sanji_live":         producer.get("sanji_live")     if producer  else None,
            "prev_sanji":         producer.get("prev_sanji")     if producer  else None,
            "diff_sanji_live":    producer.get("diff_sanji_live") if producer else None,
            "wholesale_10":       wholesale.get("wholesale_10")   if wholesale else None,
            "wholesale_all":      wholesale.get("wholesale_all")  if wholesale else None,
            "diff_wholesale_all": wholesale.get("diff_wholesale_all") if wholesale else None,
        }
        result["prices"]["chicken"] = chicken
        print(f"  ✅ 육계 수집 완료 ({chicken.get('date')})")
        if chicken.get("sanji_live"):
            diff = f" (▼{abs(chicken['diff_sanji_live'])})" if chicken.get("diff_sanji_live") and chicken["diff_sanji_live"] < 0 else \
                   f" (▲{chicken['diff_sanji_live']})" if chicken.get("diff_sanji_live") and chicken["diff_sanji_live"] > 0 else ""
            print(f"     산지: {chicken['sanji_live']:,}원/kg{diff}")
        if chicken.get("wholesale_all"):
            print(f"     도매: {chicken['wholesale_all']:,}원/kg")
    else:
        print("  ❌ 육계 수집 실패")

    print("\n🥚 계란 일일가격 수집...")
    egg = fetch_egg(api_key)
    if egg:
        result["prices"]["egg"] = egg
        print(f"  ✅ 계란 수집 완료 ({egg.get('date')})")
        if egg.get("xl_10"):
            print(f"     XL(특란): {egg['xl_10']:,}원/10개")
        if egg.get("l_10"):
            print(f"     L(대란): {egg['l_10']:,}원/10개")
    else:
        print("  ❌ 계란 수집 실패")

    # 돼지·한우는 별도 API 미포함 (다봄 차단으로 임시 제외)
    print("\n⚠️  돼지·한우: 공공데이터 API 미제공 → 추후 KAMIS API 연동 예정")

    with open("prices/prices.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    total = len(result["prices"])
    print(f"\n✅ prices/prices.json 저장 완료 ({total}개 축종, {result['updated']})")

if __name__ == "__main__":
    main()
