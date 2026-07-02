#!/usr/bin/env python3
"""
다봄(KAPE) 축산물 시세 수집 스크립트
GitHub Actions에서 매일 실행 → prices/prices.json 저장
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

def clean_num(s):
    """숫자 문자열 정리 → float"""
    if not s:
        return None
    s = re.sub(r'[^\d.]', '', str(s).strip())
    try:
        return float(s) if s else None
    except:
        return None

def get_soup(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.encoding = 'utf-8'
    return BeautifulSoup(resp.text, 'lxml')

def parse_table_rows(soup, limit=3):
    """tbody의 첫 limit 행에서 날짜와 숫자값 추출"""
    rows = []
    tbody = soup.find('tbody')
    if not tbody:
        return rows
    for tr in tbody.find_all('tr')[:limit]:
        tds = tr.find_all('td')
        if not tds:
            continue
        date_text = tds[0].get_text(strip=True)
        vals = [clean_num(td.get_text(strip=True)) for td in tds[1:]]
        rows.append({"date": date_text, "vals": vals})
    return rows

def fetch_pig():
    """돼지 산지·도매·소비자 가격"""
    url = "https://www.ekapepia.com/v3/price/livestock/pig/distrPrice.do?menuSn=34&boardInfoNo="
    try:
        soup = get_soup(url)
        rows = parse_table_rows(soup, 3)
        if not rows:
            return None
        r = rows[0]
        # 컬럼 순서: 산지(천원/110kg), 도매탕박전체, 도매탕박전체, 1등급, 삼겹살
        return {
            "date": r["date"],
            "sanji_110kg": r["vals"][0],        # 천원/110kg
            "wholesale_all": r["vals"][1],       # 원/kg 전체평균
            "wholesale_1grade": r["vals"][3] if len(r["vals"])>3 else None,  # 1등급
            "consumer_samgyupsal": r["vals"][4] if len(r["vals"])>4 else None,  # 삼겹살 원/kg
            "recent": [
                {"date": row["date"], "sanji": row["vals"][0], "wholesale": row["vals"][1]}
                for row in rows
            ]
        }
    except Exception as e:
        print(f"  ❌ 돼지 오류: {e}")
        return None

def fetch_chicken():
    """육계 산지매입·도매·소매 가격"""
    url = "https://www.ekapepia.com/v3/price/livestock/chicken/distrPrice.do?menuSn=35&boardInfoNo="
    try:
        soup = get_soup(url)
        rows = parse_table_rows(soup, 3)
        if not rows:
            return None
        r = rows[0]
        # 컬럼 순서: 생계유통(대), 위탁생계(중), 도매10호, 도매전체, 소매
        return {
            "date": r["date"],
            "sanji_live": r["vals"][0],          # 생계유통(대) 원/kg
            "sanji_contract": r["vals"][1],      # 위탁생계(중) 원/kg
            "wholesale_10": r["vals"][2],         # 도매 10호 원/kg
            "wholesale_all": r["vals"][3],        # 도매 전체 원/kg
            "consumer": r["vals"][4] if len(r["vals"])>4 else None,  # 소매 원/kg
            "recent": [
                {"date": row["date"], "sanji": row["vals"][0], "wholesale": row["vals"][3]}
                for row in rows
            ]
        }
    except Exception as e:
        print(f"  ❌ 육계 오류: {e}")
        return None

def fetch_egg():
    """계란 산지·도매·소매 가격"""
    url = "https://www.ekapepia.com/v3/price/livestock/egg/distrPrice.do?menuSn=36&boardInfoNo="
    try:
        soup = get_soup(url)
        rows = parse_table_rows(soup, 3)
        if not rows:
            return None
        r = rows[0]
        # 컬럼 순서: 특란산지, 대란산지, 특란도매, 대란도매, 소매(특란10개)
        return {
            "date": r["date"],
            "sanji_special": r["vals"][0],       # 특란 산지 원/개
            "sanji_large": r["vals"][1] if len(r["vals"])>1 else None,
            "wholesale_special": r["vals"][2] if len(r["vals"])>2 else None,
            "wholesale_large": r["vals"][3] if len(r["vals"])>3 else None,
            "consumer_10": r["vals"][4] if len(r["vals"])>4 else None,  # 소매 특란 10개
            "recent": [
                {"date": row["date"], "sanji": row["vals"][0], "wholesale": row["vals"][2] if len(row["vals"])>2 else None}
                for row in rows
            ]
        }
    except Exception as e:
        print(f"  ❌ 계란 오류: {e}")
        return None

def fetch_cattle():
    """소 산지·도매 가격 (메인페이지에서 파싱)"""
    url = "https://www.ekapepia.com/v3/web/main.do?userGroup=producer"
    try:
        soup = get_soup(url)
        # 메인페이지의 소 관련 가격 테이블 파싱
        result = {"date": "", "items": []}
        
        # 소 가격 섹션 찾기
        tables = soup.find_all('table')
        for table in tables:
            text = table.get_text()
            if '거세' in text or '한우' in text or '송아지' in text:
                rows = table.find_all('tr')
                for tr in rows[:5]:
                    tds = tr.find_all('td')
                    if len(tds) >= 2:
                        name = tds[0].get_text(strip=True)
                        val = clean_num(tds[1].get_text(strip=True))
                        if name and val:
                            result["items"].append({"name": name, "value": val})
        
        return result if result["items"] else None
    except Exception as e:
        print(f"  ❌ 소 오류: {e}")
        return None

def main():
    now_kst = datetime.now(KST)
    result = {
        "updated": now_kst.strftime("%Y-%m-%d %H:%M KST"),
        "prices": {}
    }

    Path("prices").mkdir(exist_ok=True)

    print("🐷 돼지 가격 수집...")
    pig = fetch_pig()
    if pig:
        result["prices"]["pig"] = pig
        print(f"  ✅ 산지 {pig.get('sanji_110kg')}천원/110kg, 도매 {pig.get('wholesale_all')}원/kg")

    print("🐔 육계 가격 수집...")
    chicken = fetch_chicken()
    if chicken:
        result["prices"]["chicken"] = chicken
        print(f"  ✅ 산지(대) {chicken.get('sanji_live')}원/kg, 도매전체 {chicken.get('wholesale_all')}원/kg")

    print("🥚 계란 가격 수집...")
    egg = fetch_egg()
    if egg:
        result["prices"]["egg"] = egg
        print(f"  ✅ 특란산지 {egg.get('sanji_special')}원/개")

    with open("prices/prices.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ prices/prices.json 저장 완료")
    print(f"   업데이트: {result['updated']}")

if __name__ == "__main__":
    main()
