#!/usr/bin/env python3
"""
다봄(KAPE) 축산물 시세 수집 스크립트
GitHub Actions에서 매일 실행 → prices/prices.json 저장

HTML 구조: <em>6,141</em> <img src="kape_table_up.png"> 55
→ <em> 정규식으로 가격만 추출, 이미지/등락수치 무시
"""

import requests
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

def get_html(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.encoding = 'utf-8'
    return resp.text

def em_val(td_html):
    """<td> HTML에서 <em>숫자</em>만 추출 → float, 없으면 None"""
    m = re.search(r'<em>([\d,]+)</em>', td_html)
    if m:
        try:
            return float(m.group(1).replace(',', ''))
        except:
            pass
    return None

def parse_rows(html, tbody_pattern=None, limit=2):
    """
    tbody 안의 tr에서 td별 em값 추출
    반환: [{"date":str, "tds":[v0,v1,...]}]
    """
    # tbody 구간 추출
    tbody_m = re.search(r'<tbody[^>]*>([\s\S]*?)</tbody>', html)
    body = tbody_m.group(1) if tbody_m else html

    rows = []
    for tr in re.findall(r'<tr[^>]*>([\s\S]*?)</tr>', body):
        tds = re.findall(r'<td[^>]*>([\s\S]*?)</td>', tr)
        if not tds:
            continue
        # 날짜 포함 여부 확인
        date_m = re.search(r'(\d{2}년?\s*\d{2}월\s*\d{2}일|\d{2}월\s*\d{2}일)', tds[0])
        if not date_m:
            continue
        rows.append({
            "date": date_m.group(1).strip(),
            "tds": [em_val(td) for td in tds]
        })
        if len(rows) >= limit:
            break
    return rows

def diff_calc(a, b):
    """전일대비 계산"""
    if a is not None and b is not None:
        return round(a - b, 1)
    return None

# ── 육계 ─────────────────────────────────────────────────────────────────────
def fetch_chicken():
    """
    URL: /v3/price/livestock/chicken/distrPrice.do?menuSn=35
    컬럼(0-based td): 날짜|산지생계유통대(1)|위탁생계중(2)|도매10호(3)|도매전체(4)|소매(5)
    """
    html = get_html("https://www.ekapepia.com/v3/price/livestock/chicken/distrPrice.do?menuSn=35&boardInfoNo=")
    rows = parse_rows(html)
    if not rows:
        return None
    r0, r1 = rows[0], rows[1] if len(rows) > 1 else {}
    t0 = r0["tds"]
    t1 = r1.get("tds", []) if r1 else []
    return {
        "date":             r0["date"],
        "sanji_live":       t0[1] if len(t0)>1 else None,   # 생계유통(대) 원/kg
        "sanji_contract":   t0[2] if len(t0)>2 else None,   # 위탁생계(중) 원/kg
        "wholesale_10":     t0[3] if len(t0)>3 else None,   # 도매 10호 원/kg
        "wholesale_all":    t0[4] if len(t0)>4 else None,   # 도매 전체 원/kg
        "consumer":         t0[5] if len(t0)>5 else None,   # 소매 원/kg
        "diff_sanji_live":  diff_calc(t0[1] if len(t0)>1 else None, t1[1] if len(t1)>1 else None),
        "diff_wholesale_all": diff_calc(t0[4] if len(t0)>4 else None, t1[4] if len(t1)>4 else None),
    }

# ── 돼지 산지 ─────────────────────────────────────────────────────────────────
def fetch_pig():
    """
    URL: /v3/price/livestock/pig/distrPrice.do?menuSn=34
    컬럼: 날짜|산지(천원/110kg)(1)|도매탕박전체(2)|도매탕박1등급(3)|삼겹살소비자(4)
    산지: /v3/price/livestock/pig/producer.do
    """
    # 유통단계별 가격 (도매)
    html = get_html("https://www.ekapepia.com/v3/price/livestock/pig/distrPrice.do?menuSn=34&boardInfoNo=")
    rows = parse_rows(html)
    if not rows:
        return None
    r0 = rows[0]; r1 = rows[1] if len(rows) > 1 else None
    t0 = r0["tds"]; t1 = r1["tds"] if r1 else []

    sanji = t0[1] if len(t0)>1 else None
    return {
        "date":               r0["date"],
        "sanji_110kg":        sanji,
        "sanji_per_kg":       round(sanji * 1000 / 110) if sanji else None,
        "wholesale_all":      t0[2] if len(t0)>2 else None,
        "wholesale_1grade":   t0[3] if len(t0)>3 else None,
        "consumer_samgyupsal":t0[4] if len(t0)>4 else None,
        "diff_sanji":         diff_calc(sanji, t1[1] if len(t1)>1 else None),
        "diff_wholesale":     diff_calc(t0[2] if len(t0)>2 else None, t1[2] if len(t1)>2 else None),
    }

# ── 한우 산지 ─────────────────────────────────────────────────────────────────
def fetch_cow():
    """
    URL: /v3/price/livestock/cow/producer.do
    컬럼: 날짜|큰암소(1)|암송아지4~5(2)|수송아지4~5(3)|암송아지6~7(4)|수송아지6~7(5)|농가수취평균(6)|거세우(7)|비거세우(8)|육우(9)
    단위: 천원/마리
    """
    html = get_html("https://www.ekapepia.com/v3/price/livestock/cow/producer.do")
    rows = parse_rows(html)
    if not rows:
        return None
    r0 = rows[0]; r1 = rows[1] if len(rows) > 1 else None
    t0 = r0["tds"]; t1 = r1["tds"] if r1 else []
    return {
        "date":              r0["date"],
        "big_cow":           t0[1] if len(t0)>1 else None,   # 큰암소 천원/마리
        "calf_f_45":         t0[2] if len(t0)>2 else None,   # 암송아지(4~5월) 천원/마리
        "calf_m_45":         t0[3] if len(t0)>3 else None,   # 수송아지(4~5월) 천원/마리
        "calf_f_67":         t0[4] if len(t0)>4 else None,   # 암송아지(6~7월) 천원/마리
        "calf_m_67":         t0[5] if len(t0)>5 else None,   # 수송아지(6~7월) 천원/마리
        "hanwoo_avg":        t0[6] if len(t0)>6 else None,   # 농가수취 평균 천원/마리
        "hanwoo_castrated":  t0[7] if len(t0)>7 else None,   # 거세우 천원/마리
        "hanwoo_noncasted":  t0[8] if len(t0)>8 else None,   # 비거세우 천원/마리
        "diff_big_cow":      diff_calc(t0[1] if len(t0)>1 else None, t1[1] if len(t1)>1 else None),
        "diff_castrated":    diff_calc(t0[7] if len(t0)>7 else None, t1[7] if len(t1)>7 else None),
    }

# ── 계란 산지 ─────────────────────────────────────────────────────────────────
def fetch_egg():
    """
    URL: /v3/price/livestock/egg/distrPrice.do?menuSn=36
    컬럼: 날짜|특란산지(1)|대란산지(2)|특란도매(3)|대란도매(4)|소매특란10개(5)
    단위: 원/개 → 10개 단위로 계산
    
    산지(전국XL): /v3/price/livestock/egg/producer/nation.do
    단위: 원/30개 → 10개 환산
    """
    # 유통단계별
    html = get_html("https://www.ekapepia.com/v3/price/livestock/egg/distrPrice.do?menuSn=36&boardInfoNo=")
    rows = parse_rows(html)
    if not rows:
        return None
    r0 = rows[0]; r1 = rows[1] if len(rows) > 1 else None
    t0 = r0["tds"]; t1 = r1["tds"] if r1 else []

    def to10(v): return round(v * 10) if v else None  # 원/개 → 원/10개

    ss = t0[1] if len(t0)>1 else None   # 특란 산지(원/개)
    ws = t0[3] if len(t0)>3 else None   # 특란 도매(원/개)
    return {
        "date":                   r0["date"],
        "sanji_special":          to10(ss),       # 특란 산지 원/10개
        "sanji_large":            to10(t0[2] if len(t0)>2 else None),
        "wholesale_special":      to10(ws),       # 특란 도매 원/10개
        "wholesale_large":        to10(t0[4] if len(t0)>4 else None),
        "consumer_10":            t0[5] if len(t0)>5 else None,  # 소매 원/10개(이미 10개단위)
        "diff_sanji_special":     diff_calc(to10(ss), to10(t1[1] if len(t1)>1 else None)),
        "diff_wholesale_special": diff_calc(to10(ws), to10(t1[3] if len(t1)>3 else None)),
    }

def main():
    now_kst = datetime.now(KST)
    result = {"updated": now_kst.strftime("%Y-%m-%d %H:%M KST"), "prices": {}}
    Path("prices").mkdir(exist_ok=True)

    for name, fn, label in [
        ("chicken", fetch_chicken, "🐔 육계"),
        ("pig",     fetch_pig,     "🐷 돼지"),
        ("cow",     fetch_cow,     "🐂 한우"),
        ("egg",     fetch_egg,     "🥚 계란"),
    ]:
        print(f"{label} 가격 수집...")
        try:
            data = fn()
            if data:
                result["prices"][name] = data
                print(f"  ✅ {data.get('date')} 수집 완료")
            else:
                print(f"  ❌ 수집 실패")
        except Exception as e:
            print(f"  ❌ 오류: {e}")

    with open("prices/prices.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n✅ prices/prices.json 저장 완료 ({result['updated']})")

if __name__ == "__main__":
    main()
