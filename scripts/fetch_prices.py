#!/usr/bin/env python3
"""
다봄(KAPE) 축산물 시세 수집 스크립트
HTML 구조: <em>1,685</em> <img src="kape_table_down.png"> 115
→ <em> 태그 정규식으로 가격만 추출, 이미지/등락수치 무시
"""

import requests
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from html.parser import HTMLParser

KST = timezone(timedelta(hours=9))
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://www.ekapepia.com/",
}

def get_html(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.encoding = 'utf-8'
    return resp.text

def extract_em_values(html_text):
    """
    HTML에서 <em>숫자</em> 패턴만 추출
    예: <em>1,685</em> → 1685.0
    """
    pattern = r'<em>([\d,\.]+)</em>'
    matches = re.findall(pattern, html_text)
    result = []
    for m in matches:
        try:
            result.append(float(m.replace(',', '')))
        except:
            pass
    return result

def extract_dates(html_text):
    """tbody의 날짜 패턴 추출: 07월 02일 형태"""
    pattern = r'(\d{2}월\s*\d{2}일)'
    return re.findall(pattern, html_text)

def parse_price_table(html_text, col_indices, date_limit=3):
    """
    tbody 내 tr 행별로 파싱
    각 td에서 <em> 값만 추출 (이미지·등락수치 무시)
    col_indices: 가져올 열 인덱스 목록
    """
    # tbody 구간만 추출
    tbody_match = re.search(r'<tbody>([\s\S]*?)</tbody>', html_text)
    if not tbody_match:
        return []
    tbody = tbody_match.group(1)

    rows_data = []
    # tr 행 분리
    tr_list = re.findall(r'<tr[^>]*>([\s\S]*?)</tr>', tbody)

    for tr in tr_list[:date_limit + 5]:  # 여유있게 가져오기
        # td 목록 추출
        td_list = re.findall(r'<td[^>]*>([\s\S]*?)</td>', tr)
        if len(td_list) < 2:
            continue

        # 날짜 추출 (첫 번째 td)
        date_match = re.search(r'(\d{2}월\s*\d{2}일)', td_list[0])
        if not date_match:
            continue
        date_str = date_match.group(1).strip()

        # 각 열에서 em 값 추출
        row = {"date": date_str}
        for idx in col_indices:
            if idx < len(td_list):
                em_vals = extract_em_values(td_list[idx])
                row[f"col_{idx}"] = em_vals[0] if em_vals else None
            else:
                row[f"col_{idx}"] = None

        rows_data.append(row)
        if len(rows_data) >= date_limit:
            break

    return rows_data

def fetch_chicken():
    """
    육계 컬럼: 날짜(0) | 생계유통대(1) | 위탁생계중(2) | 도매10호(3) | 도매전체(4) | 소매(5)
    """
    url = "https://www.ekapepia.com/v3/price/livestock/chicken/distrPrice.do?menuSn=35&boardInfoNo="
    try:
        html = get_html(url)
        rows = parse_price_table(html, [1, 2, 3, 4, 5])
        if not rows:
            return None
        latest = rows[0]
        result = {
            "date": latest["date"],
            "sanji_live":      latest.get("col_1"),
            "sanji_contract":  latest.get("col_2"),
            "wholesale_10":    latest.get("col_3"),
            "wholesale_all":   latest.get("col_4"),
            "consumer":        latest.get("col_5"),
        }
        if len(rows) >= 2:
            prev = rows[1]
            def diff(a, b): return round(a - b) if a and b else None
            result["diff_sanji_live"]    = diff(result["sanji_live"],    prev.get("col_1"))
            result["diff_wholesale_all"] = diff(result["wholesale_all"], prev.get("col_4"))
        result["recent"] = [
            {"date": r["date"], "sanji_live": r.get("col_1"), "wholesale_all": r.get("col_4")}
            for r in rows
        ]
        return result
    except Exception as e:
        print(f"  ❌ 육계 오류: {e}")
        return None

def fetch_pig():
    """
    돼지 컬럼: 날짜(0) | 산지천원/110kg(1) | 도매탕박전체(2) | 도매탕박1등급(3) | 삼겹살(4)
    """
    url = "https://www.ekapepia.com/v3/price/livestock/pig/distrPrice.do?menuSn=34&boardInfoNo="
    try:
        html = get_html(url)
        rows = parse_price_table(html, [1, 2, 3, 4])
        if not rows:
            return None
        latest = rows[0]
        sanji = latest.get("col_1")
        result = {
            "date": latest["date"],
            "sanji_110kg":         sanji,
            "sanji_per_kg":        round(sanji * 1000 / 110) if sanji else None,
            "wholesale_all":       latest.get("col_2"),
            "wholesale_1grade":    latest.get("col_3"),
            "consumer_samgyupsal": latest.get("col_4"),
        }
        if len(rows) >= 2:
            prev = rows[1]
            def diff(a, b): return round(a - b, 1) if a and b else None
            result["diff_sanji"]     = diff(result["sanji_110kg"],   prev.get("col_1"))
            result["diff_wholesale"] = diff(result["wholesale_all"], prev.get("col_2"))
        result["recent"] = [
            {"date": r["date"], "sanji_110kg": r.get("col_1"), "wholesale_all": r.get("col_2")}
            for r in rows
        ]
        return result
    except Exception as e:
        print(f"  ❌ 돼지 오류: {e}")
        return None

def fetch_egg():
    """
    계란 컬럼: 날짜(0) | 특란산지(1) | 대란산지(2) | 특란도매(3) | 대란도매(4) | 소매특란10개(5)
    """
    url = "https://www.ekapepia.com/v3/price/livestock/egg/distrPrice.do?menuSn=36&boardInfoNo="
    try:
        html = get_html(url)
        rows = parse_price_table(html, [1, 2, 3, 4, 5])
        if not rows:
            return None
        latest = rows[0]
        result = {
            "date": latest["date"],
            "sanji_special":      latest.get("col_1"),
            "sanji_large":        latest.get("col_2"),
            "wholesale_special":  latest.get("col_3"),
            "wholesale_large":    latest.get("col_4"),
            "consumer_10":        latest.get("col_5"),
        }
        if len(rows) >= 2:
            prev = rows[1]
            def diff(a, b): return round(a - b, 1) if a and b else None
            result["diff_sanji_special"]     = diff(result["sanji_special"],     prev.get("col_1"))
            result["diff_wholesale_special"] = diff(result["wholesale_special"], prev.get("col_3"))
        result["recent"] = [
            {"date": r["date"], "sanji_special": r.get("col_1"), "wholesale_special": r.get("col_3")}
            for r in rows
        ]
        return result
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
