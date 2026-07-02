#!/usr/bin/env python3
"""
다봄(KAPE) 축산물 시세 수집 스크립트
GitHub Actions에서 매일 실행 → prices/prices.json 저장

핵심: 각 td 안의 <em> 태그에서 가격만 추출
      등락 이미지(kape_table_up/down.png)와 등락수치는 무시
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

def get_soup(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.encoding = 'utf-8'
    return BeautifulSoup(resp.text, 'lxml')

def extract_price_from_td(td):
    """
    td 안의 <em> 태그에서 가격 숫자만 추출
    구조 예시:
      <td><em>1,685</em><img src="kape_table_down.png"> 115</td>
    em 태그가 없으면 텍스트에서 첫 번째 숫자 그룹 추출
    """
    em = td.find('em')
    if em:
        text = em.get_text(strip=True)
    else:
        # em 태그 없는 경우 이미지 제거 후 첫 숫자 추출
        for img in td.find_all('img'):
            img.decompose()
        text = td.get_text(strip=True)
        # 첫 번째 숫자 그룹만 (쉼표 포함)
        m = re.match(r'^[\d,]+', text)
        text = m.group(0) if m else ""
    
    if not text or text == '-':
        return None
    try:
        return float(text.replace(',', ''))
    except:
        return None

def extract_date_from_td(td):
    """날짜 td에서 텍스트만 추출"""
    # 이미지 태그 제거
    for img in td.find_all('img'):
        img.decompose()
    return td.get_text(strip=True)

def parse_price_table(soup, col_map, limit=3):
    """
    tbody에서 행별로 파싱
    col_map: {컬럼인덱스: 필드명} 딕셔너리
    """
    rows = []
    tbody = soup.find('tbody')
    if not tbody:
        return rows
    
    for tr in tbody.find_all('tr')[:limit]:
        tds = tr.find_all('td')
        if not tds:
            continue
        
        date = extract_date_from_td(tds[0])
        if not date:
            continue
        
        row = {"date": date}
        for idx, field in col_map.items():
            if idx < len(tds):
                row[field] = extract_price_from_td(tds[idx])
            else:
                row[field] = None
        rows.append(row)
    
    return rows

def fetch_chicken():
    """
    육계 유통단계별가격
    컬럼: 날짜(0) | 산지매입생계유통대(1) | 위탁생계중(2) | 도매10호(3) | 도매전체(4) | 소매(5)
    """
    url = "https://www.ekapepia.com/v3/price/livestock/chicken/distrPrice.do?menuSn=35&boardInfoNo="
    try:
        soup = get_soup(url)
        col_map = {
            1: "sanji_live",      # 산지매입 생계유통(대)
            2: "sanji_contract",  # 위탁생계(중)
            3: "wholesale_10",    # 도매 10호
            4: "wholesale_all",   # 도매 전체
            5: "consumer",        # 소매
        }
        rows = parse_price_table(soup, col_map, limit=3)
        if not rows:
            return None
        
        latest = rows[0]
        # 전일대비 계산
        if len(rows) >= 2:
            prev = rows[1]
            def diff(a, b): return round(a - b) if a and b else None
            latest["diff_sanji_live"] = diff(latest.get("sanji_live"), prev.get("sanji_live"))
            latest["diff_wholesale_all"] = diff(latest.get("wholesale_all"), prev.get("wholesale_all"))
        
        latest["recent"] = [
            {"date": r["date"], "sanji_live": r.get("sanji_live"), "wholesale_all": r.get("wholesale_all")}
            for r in rows
        ]
        return latest
    except Exception as e:
        print(f"  ❌ 육계 오류: {e}")
        import traceback; traceback.print_exc()
        return None

def fetch_pig():
    """
    돼지 유통단계별가격
    컬럼: 날짜(0) | 산지(1) | 도매탕박전체(2) | 도매탕박1등급(3) | 삼겹살(4)
    """
    url = "https://www.ekapepia.com/v3/price/livestock/pig/distrPrice.do?menuSn=34&boardInfoNo="
    try:
        soup = get_soup(url)
        col_map = {
            1: "sanji_110kg",         # 산지(천원/110kg)
            2: "wholesale_all",        # 도매 탕박 전체
            3: "wholesale_1grade",     # 도매 탕박 1등급
            4: "consumer_samgyupsal",  # 삼겹살 소비자가
        }
        rows = parse_price_table(soup, col_map, limit=3)
        if not rows:
            return None
        
        latest = rows[0]
        # kg당 환산 (천원/110kg → 원/kg)
        if latest.get("sanji_110kg"):
            latest["sanji_per_kg"] = round(latest["sanji_110kg"] * 1000 / 110)
        
        if len(rows) >= 2:
            prev = rows[1]
            def diff(a, b): return round(a - b) if a and b else None
            latest["diff_sanji"] = diff(latest.get("sanji_110kg"), prev.get("sanji_110kg"))
            latest["diff_wholesale"] = diff(latest.get("wholesale_all"), prev.get("wholesale_all"))
        
        latest["recent"] = [
            {"date": r["date"], "sanji_110kg": r.get("sanji_110kg"), "wholesale_all": r.get("wholesale_all")}
            for r in rows
        ]
        return latest
    except Exception as e:
        print(f"  ❌ 돼지 오류: {e}")
        import traceback; traceback.print_exc()
        return None

def fetch_egg():
    """
    계란 유통단계별가격
    컬럼: 날짜(0) | 특란산지(1) | 대란산지(2) | 특란도매(3) | 대란도매(4) | 소매특란10개(5)
    """
    url = "https://www.ekapepia.com/v3/price/livestock/egg/distrPrice.do?menuSn=36&boardInfoNo="
    try:
        soup = get_soup(url)
        col_map = {
            1: "sanji_special",      # 특란 산지
            2: "sanji_large",        # 대란 산지
            3: "wholesale_special",  # 특란 도매
            4: "wholesale_large",    # 대란 도매
            5: "consumer_10",        # 소매 특란 10개
        }
        rows = parse_price_table(soup, col_map, limit=3)
        if not rows:
            return None
        
        latest = rows[0]
        if len(rows) >= 2:
            prev = rows[1]
            def diff(a, b): return round(a - b) if a and b else None
            latest["diff_sanji_special"] = diff(latest.get("sanji_special"), prev.get("sanji_special"))
            latest["diff_wholesale_special"] = diff(latest.get("wholesale_special"), prev.get("wholesale_special"))
        
        latest["recent"] = [
            {"date": r["date"], "sanji_special": r.get("sanji_special"), "wholesale_special": r.get("wholesale_special")}
            for r in rows
        ]
        return latest
    except Exception as e:
        print(f"  ❌ 계란 오류: {e}")
        import traceback; traceback.print_exc()
        return None

def main():
    now_kst = datetime.now(KST)
    result = {
        "updated": now_kst.strftime("%Y-%m-%d %H:%M KST"),
        "prices": {}
    }

    Path("prices").mkdir(exist_ok=True)

    print("🐔 육계 가격 수집...")
    chicken = fetch_chicken()
    if chicken:
        result["prices"]["chicken"] = chicken
        print(f"  ✅ 산지(대) {chicken.get('sanji_live')}원/kg, 도매전체 {chicken.get('wholesale_all')}원/kg")
    else:
        print("  ❌ 수집 실패")

    print("🐷 돼지 가격 수집...")
    pig = fetch_pig()
    if pig:
        result["prices"]["pig"] = pig
        print(f"  ✅ 산지 {pig.get('sanji_110kg')}천원/110kg ({pig.get('sanji_per_kg')}원/kg), 도매 {pig.get('wholesale_all')}원/kg")
    else:
        print("  ❌ 수집 실패")

    print("🥚 계란 가격 수집...")
    egg = fetch_egg()
    if egg:
        result["prices"]["egg"] = egg
        print(f"  ✅ 특란산지 {egg.get('sanji_special')}원/개, 특란도매 {egg.get('wholesale_special')}원/개")
    else:
        print("  ❌ 수집 실패")

    with open("prices/prices.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ prices/prices.json 저장 완료 ({now_kst.strftime('%Y-%m-%d %H:%M KST')})")

if __name__ == "__main__":
    main()
