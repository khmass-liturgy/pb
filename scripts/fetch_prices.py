#!/usr/bin/env python3
"""
축산물품질평가원 공공데이터 API 시세 수집
확인된 URL:
  육계: .../poultry/nativechichen  (agency=대리점가, average=전체평균, 단위:원/kg)
  계란: .../poultry/egg            (big=대란, medium=중란 등, 단위:원/30개 추정)
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

def call_api(url, api_key, days_back=5, rows=30):
    now = datetime.now(KST)
    start = (now - timedelta(days=days_back)).strftime("%Y%m%d")
    end   = now.strftime("%Y%m%d")
    params = {
        "serviceKey": api_key,
        "pageNo": 1,
        "numOfRows": rows,
        "startYmd": start,
        "endYmd":   end,
    }
    r = requests.get(url, params=params, timeout=15)
    r.encoding = 'utf-8'
    print(f"    HTTP {r.status_code} ({len(r.text)}bytes)")
    if r.status_code != 200 or not r.text.strip():
        return None
    # 전체 XML 출력 (디버그)
    print(f"    XML: {r.text[:600]}")
    return r.text

def parse_items(xml_text):
    try:
        root = ET.fromstring(xml_text)
        return root.findall('.//item')
    except:
        return []

def tag_val(item, tag, as_int=True):
    el = item.find(tag)
    if el is not None and el.text and el.text.strip():
        v = el.text.strip().replace(',','')
        if as_int:
            try: return int(float(v))
            except: return None
        return v
    return None

def diff_calc(a, b):
    if a is not None and b is not None:
        return round(a - b)
    return None

def main():
    api_key = get_api_key()
    now_kst = datetime.now(KST)
    result  = {"updated": now_kst.strftime("%Y-%m-%d %H:%M KST"), "prices": {}}
    Path("prices").mkdir(exist_ok=True)

    # ── 육계 ─────────────────────────────────────────────────────────────────
    print("\n🐔 육계 가격 수집...")
    chk_url = f"{BASE}/poultry/nativechichen"
    xml = call_api(chk_url, api_key)
    if xml:
        items = parse_items(xml)
        print(f"    item 수: {len(items)}")
        if items:
            # 모든 태그 출력
            print("    [첫번째 item 태그 전체]")
            for child in items[0]:
                print(f"      <{child.tag}>{child.text}</{child.tag}>")

            # 날짜 기준 최신 2개 추출
            dated = []
            for item in items:
                d = (tag_val(item,'tradeDate',False) or
                     tag_val(item,'modYmd',False) or
                     tag_val(item,'baseDate',False) or "")
                dated.append((d, item))
            dated.sort(key=lambda x: x[0], reverse=True)

            r0 = dated[0][1] if len(dated)>0 else None
            r1 = dated[1][1] if len(dated)>1 else None

            # 가격 필드 시도
            price_tags = ['average','avgPrice','sanji','price','agency','mart','franchise']
            today_price = None
            prev_price  = None
            for t in price_tags:
                v = tag_val(r0, t) if r0 else None
                if v:
                    today_price = v
                    break
            for t in price_tags:
                v = tag_val(r1, t) if r1 else None
                if v:
                    prev_price = v
                    break

            date_str = dated[0][0] if dated else ""
            result["prices"]["chicken"] = {
                "date":            date_str,
                "sanji_live":      today_price,
                "prev_sanji":      prev_price,
                "diff_sanji_live": diff_calc(today_price, prev_price),
            }
            print(f"  ✅ 육계: {date_str} / 가격={today_price}원/kg (전일={prev_price})")

    # ── 계란 ─────────────────────────────────────────────────────────────────
    print("\n🥚 계란 가격 수집...")
    egg_url = f"{BASE}/poultry/egg"
    xml = call_api(egg_url, api_key)
    if xml:
        items = parse_items(xml)
        print(f"    item 수: {len(items)}")
        if items:
            print("    [첫번째 item 태그 전체]")
            for child in items[0]:
                print(f"      <{child.tag}>{child.text}</{child.tag}>")

            dated = []
            for item in items:
                d = (tag_val(item,'tradeDate',False) or
                     tag_val(item,'modYmd',False) or
                     tag_val(item,'baseDate',False) or "")
                dated.append((d, item))
            dated.sort(key=lambda x: x[0], reverse=True)

            r0 = dated[0][1] if len(dated)>0 else None
            r1 = dated[1][1] if len(dated)>1 else None
            date_str = dated[0][0] if dated else ""

            # 계란 필드: big/medium/small 또는 xl/l/m 또는 특/대/중
            egg = {"date": date_str}
            # 모든 숫자 태그 출력
            if r0:
                for child in r0:
                    v = tag_val(r0, child.tag)
                    if v:
                        egg[f"raw_{child.tag}"] = v

            # 규격별 매핑 시도
            tag_map = {
                # 태그명 : (필드명, 단위설명)
                "big":    ("l_raw",  "대란/L"),
                "medium": ("m_raw",  "중란/M"),
                "large":  ("l_raw",  "대란/L"),
                "xl":     ("xl_raw", "특란/XL"),
                "extra":  ("xl_raw", "특란/XL"),
                "special":("xl_raw", "특란/XL"),
                "average":("avg_raw","전체평균"),
            }
            for tag, (field, desc) in tag_map.items():
                v0 = tag_val(r0, tag) if r0 else None
                v1 = tag_val(r1, tag) if r1 else None
                if v0:
                    egg[field] = v0
                    egg[f"prev_{field}"] = v1
                    print(f"      {desc}: {v0} (전일:{v1})")

            result["prices"]["egg"] = egg
            print(f"  ✅ 계란 raw 데이터 저장 완료")

    with open("prices/prices.json","w",encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n✅ prices.json 저장 완료 ({len(result['prices'])}개)")

if __name__ == "__main__":
    main()
