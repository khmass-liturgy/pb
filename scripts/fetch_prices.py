#!/usr/bin/env python3
"""
다봄(KAPE) 축산물 시세 수집 스크립트
GitHub Actions에서 매일 실행 → prices/prices.json 저장

핵심: 각 td 안의 가격 숫자만 추출, 등락(↑115, ↓45) 제외
구조: <td>1,685 <span class="down">↓115</span></td>
   또는 <td><em>1,685</em><img...> 115</td>
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
    "Referer": "https://www.ekapepia.com/",
}

def get_soup(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.encoding = 'utf-8'
    return BeautifulSoup(resp.text, 'lxml')

def extract_price_only(td):
    """
    td에서 가격 숫자만 추출, 등락 수치 제외
    다봄 구조:
      방식A: <td>1,685 <span class="down">↓115</span></td>
      방식B: <td><em>1,685</em><img src="kape_table_down.png"> 115</td>
      방식C: <td>1,685↓115</td>  (텍스트만)
    """
    # 방식A: em 태그에 가격이 있음
    em = td.find('em')
    if em:
        text = em.get_text(strip=True).replace(',', '')
        m = re.match(r'^[\d]+$', text)
        if m:
            try:
                return float(text)
            except:
                pass

    # 방식B: span.up/down/rise/fall 등 등락 태그 제거 후 추출
    clone = BeautifulSoup(str(td), 'lxml').find('td') or td
    # 등락 관련 태그 제거 (span, img, i, b 등)
    for tag in clone.find_all(['span', 'img', 'i', 'b', 'small']):
        tag.decompose()

    raw = clone.get_text(strip=True)

    # 방식C: 숫자,숫자 패턴에서 첫 번째 숫자 그룹만 (쉼표 포함)
    # ex) "1,685115" → "1,685"  /  "1,685 115" → "1,685"  /  "1,685↓115" → "1,685"
    # 쉼표로 구분된 숫자 패턴 우선
    m = re.match(r'^([\d]{1,3}(?:,\d{3})*(?:\.\d+)?)', raw.replace(' ',''))
    if m:
        try:
            return float(m.group(1).replace(',', ''))
        except:
            pass

    # 공백 기준 첫 번째 토큰에서 숫자
    first_token = raw.split()[0] if raw.split() else ''
    m2 = re.match(r'^([\d,]+)', first_token)
    if m2:
        try:
            return float(m2.group(1).replace(',', ''))
        except:
            pass

    return None

def extract_date(td):
    """날짜 td에서 텍스트만"""
    for tag in td.find_all(['img', 'span']):
        tag.decompose()
    return td.get_text(strip=True)

def parse_table(soup, col_map, limit=3):
    """
    tbody에서 파싱
    col_map: {컬럼인덱스: 필드명}
    """
    rows = []
    tbody = soup.find('tbody')
    if not tbody:
        # tbody 없으면 table 안의 tr 직접 탐색
        table = soup.find('table')
        if table:
            tbody = table

    if not tbody:
        return rows

    for tr in tbody.find_all('tr')[:limit]:
        tds = tr.find_all('td')
        if len(tds) < 2:
            continue
        date = extract_date(tds[0])
        if not date or not any(c.isdigit() for c in date):
            continue  # 헤더 행 스킵
        row = {"date": date}
        for idx, field in col_map.items():
            row[field] = extract_price_only(tds[idx]) if idx < len(tds) else None
        rows.append(row)

    return rows

def fetch_chicken():
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
        rows = parse_table(soup, col_map)
        if not rows:
            return None
        latest = rows[0]
        if len(rows) >= 2:
            prev = rows[1]
            def diff(a, b): return round(a - b, 1) if a and b else None
            latest["diff_sanji_live"]    = diff(latest.get("sanji_live"), prev.get("sanji_live"))
            latest["diff_wholesale_all"] = diff(latest.get("wholesale_all"), prev.get("wholesale_all"))
        latest["recent"] = [
            {"date": r["date"], "sanji_live": r.get("sanji_live"), "wholesale_all": r.get("wholesale_all")}
            for r in rows
        ]
        return latest
    except Exception as e:
        print(f"  ❌ 육계 오류: {e}")
        return None

def fetch_pig():
    url = "https://www.ekapepia.com/v3/price/livestock/pig/distrPrice.do?menuSn=34&boardInfoNo="
    try:
        soup = get_soup(url)
        col_map = {
            1: "sanji_110kg",
            2: "wholesale_all",
            3: "wholesale_1grade",
            4: "consumer_samgyupsal",
        }
        rows = parse_table(soup, col_map)
        if not rows:
            return None
        latest = rows[0]
        if latest.get("sanji_110kg"):
            latest["sanji_per_kg"] = round(latest["sanji_110kg"] * 1000 / 110)
        if len(rows) >= 2:
            prev = rows[1]
            def diff(a, b): return round(a - b, 1) if a and b else None
            latest["diff_sanji"]     = diff(latest.get("sanji_110kg"), prev.get("sanji_110kg"))
            latest["diff_wholesale"] = diff(latest.get("wholesale_all"), prev.get("wholesale_all"))
        latest["recent"] = [
            {"date": r["date"], "sanji_110kg": r.get("sanji_110kg"), "wholesale_all": r.get("wholesale_all")}
            for r in rows
        ]
        return latest
    except Exception as e:
        print(f"  ❌ 돼지 오류: {e}")
        return None

def fetch_egg():
    url = "https://www.ekapepia.com/v3/price/livestock/egg/distrPrice.do?menuSn=36&boardInfoNo="
    try:
        soup = get_soup(url)
        col_map = {
            1: "sanji_special",
            2: "sanji_large",
            3: "wholesale_special",
            4: "wholesale_large",
            5: "consumer_10",
        }
        rows = parse_table(soup, col_map)
        if not rows:
            return None
        latest = rows[0]
        if len(rows) >= 2:
            prev = rows[1]
            def diff(a, b): return round(a - b, 1) if a and b else None
            latest["diff_sanji_special"]     = diff(latest.get("sanji_special"), prev.get("sanji_special"))
            latest["diff_wholesale_special"] = diff(latest.get("wholesale_special"), prev.get("wholesale_special"))
        latest["recent"] = [
            {"date": r["date"], "sanji_special": r.get("sanji_special"), "wholesale_special": r.get("wholesale_special")}
            for r in rows
        ]
        return latest
    except Exception as e:
        print(f"  ❌ 계란 오류: {e}")
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
        print(f"  ✅ 산지(대) {chicken.get('sanji_live')}원/kg | 도매전체 {chicken.get('wholesale_all')}원/kg")
    else:
        print("  ❌ 수집 실패")

    print("🐷 돼지 가격 수집...")
    pig = fetch_pig()
    if pig:
        result["prices"]["pig"] = pig
        print(f"  ✅ 산지 {pig.get('sanji_110kg')}천원/110kg | 도매 {pig.get('wholesale_all')}원/kg")
    else:
        print("  ❌ 수집 실패")

    print("🥚 계란 가격 수집...")
    egg = fetch_egg()
    if egg:
        result["prices"]["egg"] = egg
        print(f"  ✅ 특란산지 {egg.get('sanji_special')}원/개 | 특란도매 {egg.get('wholesale_special')}원/개")
    else:
        print("  ❌ 수집 실패")

    with open("prices/prices.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ prices/prices.json 저장 완료 ({result['updated']})")

if __name__ == "__main__":
    main()
