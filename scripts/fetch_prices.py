#!/usr/bin/env python3
"""
다봄(KAPE) 축산물 시세 수집 스크립트
GitHub Actions에서 매일 실행 → prices/prices.json 저장
HTML 구조: <em>숫자</em> <img up/down> 등락수치
→ <em> 정규식으로 가격만 추출
"""

import requests
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://www.ekapepia.com/",
}

def get_html(url, timeout=15):
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.encoding = resp.apparent_encoding or 'utf-8'
    return resp.text

def em_val(td_html):
    m = re.search(r'<em>([\d,]+)</em>', td_html)
    if m:
        try:
            return float(m.group(1).replace(',', ''))
        except:
            pass
    return None

def parse_rows(html, limit=3):
    tbody_m = re.search(r'<tbody[^>]*>([\s\S]*?)</tbody>', html)
    body = tbody_m.group(1) if tbody_m else html
    rows = []
    for tr in re.findall(r'<tr[^>]*>([\s\S]*?)</tr>', body):
        tds = re.findall(r'<td[^>]*>([\s\S]*?)</td>', tr)
        if not tds:
            continue
        date_m = re.search(r'(\d{2}년?\s*\d{2}월\s*\d{2}일|\d{2}월\s*\d{2}일)', tds[0])
        if not date_m:
            continue
        rows.append({"date": date_m.group(1).strip(), "tds": [em_val(td) for td in tds]})
        if len(rows) >= limit:
            break
    return rows

def diff_calc(a, b):
    if a is not None and b is not None:
        return round(a - b, 1)
    return None

# ── 육계 ──────────────────────────────────────────────────────────────────────
def fetch_chicken():
    html = get_html("https://www.ekapepia.com/v3/price/livestock/chicken/distrPrice.do?menuSn=35&boardInfoNo=")
    rows = parse_rows(html)
    if not rows:
        return None
    r0 = rows[0]; t0 = r0["tds"]
    t1 = rows[1]["tds"] if len(rows) > 1 else []
    return {
        "date":              r0["date"],
        "sanji_live":        t0[1] if len(t0)>1 else None,
        "sanji_contract":    t0[2] if len(t0)>2 else None,
        "wholesale_10":      t0[3] if len(t0)>3 else None,
        "wholesale_all":     t0[4] if len(t0)>4 else None,
        "consumer":          t0[5] if len(t0)>5 else None,
        "diff_sanji_live":   diff_calc(t0[1] if len(t0)>1 else None, t1[1] if len(t1)>1 else None),
        "diff_wholesale_all":diff_calc(t0[4] if len(t0)>4 else None, t1[4] if len(t1)>4 else None),
    }

# ── 돼지 ──────────────────────────────────────────────────────────────────────
def fetch_pig():
    html = get_html("https://www.ekapepia.com/v3/price/livestock/pig/distrPrice.do?menuSn=34&boardInfoNo=")
    rows = parse_rows(html)
    if not rows:
        return None
    r0 = rows[0]; t0 = r0["tds"]
    t1 = rows[1]["tds"] if len(rows) > 1 else []
    sanji = t0[1] if len(t0)>1 else None
    return {
        "date":                r0["date"],
        "sanji_110kg":         sanji,
        "sanji_per_kg":        round(sanji * 1000 / 110) if sanji else None,
        "wholesale_all":       t0[2] if len(t0)>2 else None,
        "wholesale_1grade":    t0[3] if len(t0)>3 else None,
        "consumer_samgyupsal": t0[4] if len(t0)>4 else None,
        "diff_sanji":          diff_calc(sanji, t1[1] if len(t1)>1 else None),
        "diff_wholesale":      diff_calc(t0[2] if len(t0)>2 else None, t1[2] if len(t1)>2 else None),
    }

# ── 한우 ──────────────────────────────────────────────────────────────────────
def fetch_cow():
    html = get_html("https://www.ekapepia.com/v3/price/livestock/cow/producer.do")
    rows = parse_rows(html)
    if not rows:
        return None
    r0 = rows[0]; t0 = r0["tds"]
    t1 = rows[1]["tds"] if len(rows) > 1 else []
    return {
        "date":             r0["date"],
        "big_cow":          t0[1] if len(t0)>1 else None,
        "calf_f_45":        t0[2] if len(t0)>2 else None,
        "calf_m_45":        t0[3] if len(t0)>3 else None,
        "calf_f_67":        t0[4] if len(t0)>4 else None,
        "calf_m_67":        t0[5] if len(t0)>5 else None,
        "hanwoo_avg":       t0[6] if len(t0)>6 else None,
        "hanwoo_castrated": t0[7] if len(t0)>7 else None,
        "hanwoo_noncasted": t0[8] if len(t0)>8 else None,
        "diff_big_cow":     diff_calc(t0[1] if len(t0)>1 else None, t1[1] if len(t1)>1 else None),
        "diff_castrated":   diff_calc(t0[7] if len(t0)>7 else None, t1[7] if len(t1)>7 else None),
    }

# ── 계란 ──────────────────────────────────────────────────────────────────────
def fetch_egg():
    """
    계란 산지가격(전국) - 모바일 페이지
    URL: /v3/mobile/price/livestock/egg/producer/nation.do?menuSn=136
    규격(26.5.21 변경): 왕→2XL, 특→XL, 대→L, 중→M, 소→S
    컬럼: 날짜|2XL_30|2XL_10|XL_30|XL_10|L_30|L_10|M_30|M_10|S_30|S_10
    """
    url = "https://www.ekapepia.com/v3/mobile/price/livestock/egg/producer/nation.do?menuSn=136&boardInfoNo="
    try:
        html = get_html(url)
        rows = parse_rows(html, limit=3)
        if not rows:
            return None
        r0 = rows[0]; t0 = r0["tds"]
        t1 = rows[1]["tds"] if len(rows) > 1 else []

        # 월평균 파싱
        monthly = parse_egg_monthly(html)

        return {
            "date":      r0["date"],
            "xl2_30":    t0[1] if len(t0)>1 else None,   # 2XL 30개
            "xl2_10":    t0[2] if len(t0)>2 else None,   # 2XL 10개
            "xl_30":     t0[3] if len(t0)>3 else None,   # XL(특란) 30개
            "xl_10":     t0[4] if len(t0)>4 else None,   # XL(특란) 10개
            "l_30":      t0[5] if len(t0)>5 else None,   # L(대란) 30개
            "l_10":      t0[6] if len(t0)>6 else None,   # L(대란) 10개
            "m_30":      t0[7] if len(t0)>7 else None,   # M(중란) 30개
            "m_10":      t0[8] if len(t0)>8 else None,   # M(중란) 10개
            "diff_xl_10": diff_calc(t0[4] if len(t0)>4 else None, t1[4] if len(t1)>4 else None),
            "diff_l_10":  diff_calc(t0[6] if len(t0)>6 else None, t1[6] if len(t1)>6 else None),
            "monthly":   monthly,
        }
    except Exception as e:
        print(f"  ❌ 계란 오류: {e}")
        import traceback; traceback.print_exc()
        return None

def parse_egg_monthly(html):
    """
    2026년 월평균 파싱
    반환: {"XL": {1:5208, 2:5243, ...}, "L": {...}, ...} 단위: 원/30개
    """
    result = {}
    tbodies = re.findall(r'<tbody[^>]*>([\s\S]*?)</tbody>', html)
    if len(tbodies) < 2:
        return result
    monthly_body = tbodies[1]
    grade_map = {"2XL":"2XL","XL":"XL","L":"L","M":"M","S":"S",
                 "왕":"2XL","특":"XL","대":"L","중":"M","소":"S"}
    for tr in re.findall(r'<tr[^>]*>([\s\S]*?)</tr>', monthly_body):
        tds = re.findall(r'<td[^>]*>([\s\S]*?)</td>', tr)
        if not tds:
            continue
        grade_raw = re.sub(r'<[^>]+>', '', tds[0]).strip()
        grade = grade_map.get(grade_raw)
        if not grade:
            continue
        monthly = {}
        for i, td in enumerate(tds[1:13], 1):
            val = em_val(td)
            if val:
                monthly[i] = int(val)
        if monthly:
            result[grade] = monthly
    return result

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
