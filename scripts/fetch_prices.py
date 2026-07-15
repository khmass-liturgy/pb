#!/usr/bin/env python3
"""
다봄(KAPE) 축산물 산지시세 수집 스크립트
GitHub Actions에서 매일 실행 → prices/prices.json 저장

산지시세 전용 URL:
  육계: /v3/price/livestock/chicken/distrPrice.do?menuSn=35
  양돈: /v3/price/livestock/pig/producer.do?menuSn=119
  계란: /v3/mobile/price/livestock/egg/producer/nation.do?menuSn=136

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
    """<em>숫자</em>에서 숫자만 추출"""
    m = re.search(r'<em>([\d,]+)</em>', td_html)
    if m:
        try:
            return float(m.group(1).replace(',', ''))
        except:
            pass
    return None

def parse_rows(html, limit=3):
    """tbody에서 날짜 행 파싱 → [{"date":str, "tds":[em값...]}]"""
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

# ── 육계 산지시세 ─────────────────────────────────────────────────────────────
def fetch_chicken():
    """
    URL: /v3/price/livestock/chicken/distrPrice.do?menuSn=35
    컬럼: 날짜|산지생계유통대(1)|위탁생계중(2)|도매10호(3)|도매전체(4)|소매(5)
    """
    html = get_html(
        "https://www.ekapepia.com/v3/price/livestock/chicken/distrPrice.do?menuSn=35&boardInfoNo="
    )
    rows = parse_rows(html)
    if not rows:
        return None
    r0 = rows[0]; t0 = r0["tds"]
    t1 = rows[1]["tds"] if len(rows) > 1 else []
    return {
        "date":               r0["date"],
        "sanji_live":         t0[1] if len(t0)>1 else None,   # 생계유통(대) 원/kg
        "sanji_contract":     t0[2] if len(t0)>2 else None,   # 위탁생계(중) 원/kg
        "wholesale_10":       t0[3] if len(t0)>3 else None,   # 도매 10호
        "wholesale_all":      t0[4] if len(t0)>4 else None,   # 도매 전체
        "consumer":           t0[5] if len(t0)>5 else None,   # 소매
        "diff_sanji_live":    diff_calc(t0[1] if len(t0)>1 else None, t1[1] if len(t1)>1 else None),
        "diff_wholesale_all": diff_calc(t0[4] if len(t0)>4 else None, t1[4] if len(t1)>4 else None),
    }

# ── 양돈 산지시세 (산지가격 전용 페이지) ────────────────────────────────────
def fetch_pig():
    """
    URL: /v3/price/livestock/pig/producer.do?menuSn=119
    구조:
      농가수취 평균(원/kg)  / 비육돈(천원/110kg)
      금일 | 전일 | 전월평균 | 전년동월평균 | 전년말월평균
    td 구조: 구분(0) | 농가수취평균(1) | 비육돈(2)
    """
    html = get_html(
        "https://www.ekapepia.com/v3/price/livestock/pig/producer.do?menuSn=119&boardInfoNo="
    )
    rows = parse_rows(html, limit=5)
    if not rows:
        return None

    # 금일 / 전일
    r0 = rows[0]; t0 = r0["tds"]
    r1 = rows[1] if len(rows) > 1 else None; t1 = r1["tds"] if r1 else []
    # 전월평균
    r2 = rows[2] if len(rows) > 2 else None; t2 = r2["tds"] if r2 else []
    # 전년동월
    r3 = rows[3] if len(rows) > 3 else None; t3 = r3["tds"] if r3 else []

    avg_today  = t0[1] if len(t0)>1 else None   # 농가수취 평균 원/kg
    pig_today  = t0[2] if len(t0)>2 else None   # 비육돈 천원/110kg
    avg_prev   = t1[1] if len(t1)>1 else None
    pig_prev   = t1[2] if len(t1)>2 else None

    return {
        "date":              r0["date"],
        # 금일
        "avg_per_kg":        avg_today,           # 농가수취 평균 원/kg
        "pig_110kg":         pig_today,           # 비육돈 천원/110kg
        "pig_per_kg":        round(pig_today * 1000 / 110) if pig_today else None,
        # 전일
        "prev_avg_per_kg":   avg_prev,
        "prev_pig_110kg":    pig_prev,
        # 전일대비
        "diff_avg":          diff_calc(avg_today, avg_prev),
        "diff_pig":          diff_calc(pig_today, pig_prev),
        # 전월/전년 평균
        "month_avg_per_kg":  t2[1] if len(t2)>1 else None,
        "month_pig_110kg":   t2[2] if len(t2)>2 else None,
        "year_avg_per_kg":   t3[1] if len(t3)>1 else None,
        "year_pig_110kg":    t3[2] if len(t3)>2 else None,
    }

# ── 한우 산지시세 ─────────────────────────────────────────────────────────────
def fetch_cow():
    """
    URL: /v3/price/livestock/cow/producer.do
    컬럼: 날짜|큰암소|암송아지4~5|수송아지4~5|암송아지6~7|수송아지6~7|평균|거세우|비거세
    단위: 천원/마리
    """
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

# ── 계란 산지시세 (모바일 전국 페이지) ─────────────────────────────────────
def fetch_egg():
    """
    URL: /v3/mobile/price/livestock/egg/producer/nation.do?menuSn=136
    규격(26.5.21 변경): 왕→2XL, 특→XL, 대→L, 중→M, 소→S
    컬럼: 날짜|2XL_30|2XL_10|XL_30|XL_10|L_30|L_10|M_30|M_10|S_30|S_10
    단위: 원/30개, 원/10개
    """
    url = "https://www.ekapepia.com/v3/mobile/price/livestock/egg/producer/nation.do?menuSn=136&boardInfoNo="
    try:
        html = get_html(url)
        rows = parse_rows(html, limit=3)
        if not rows:
            return None
        r0 = rows[0]; t0 = r0["tds"]
        t1 = rows[1]["tds"] if len(rows) > 1 else []
        monthly = parse_egg_monthly(html)
        return {
            "date":       r0["date"],
            "xl2_30":     t0[1] if len(t0)>1 else None,
            "xl2_10":     t0[2] if len(t0)>2 else None,
            "xl_30":      t0[3] if len(t0)>3 else None,
            "xl_10":      t0[4] if len(t0)>4 else None,
            "l_30":       t0[5] if len(t0)>5 else None,
            "l_10":       t0[6] if len(t0)>6 else None,
            "m_30":       t0[7] if len(t0)>7 else None,
            "m_10":       t0[8] if len(t0)>8 else None,
            "diff_xl_10": diff_calc(t0[4] if len(t0)>4 else None, t1[4] if len(t1)>4 else None),
            "diff_l_10":  diff_calc(t0[6] if len(t0)>6 else None, t1[6] if len(t1)>6 else None),
            "monthly":    monthly,
        }
    except Exception as e:
        print(f"  ❌ 계란 오류: {e}")
        import traceback; traceback.print_exc()
        return None

def parse_egg_monthly(html):
    """2026년 월평균 파싱 → {"XL":{1:5208,...}, "L":{...}} 단위: 원/30개"""
    result = {}
    tbodies = re.findall(r'<tbody[^>]*>([\s\S]*?)</tbody>', html)
    if len(tbodies) < 2:
        return result
    grade_map = {"2XL":"2XL","XL":"XL","L":"L","M":"M","S":"S",
                 "왕":"2XL","특":"XL","대":"L","중":"M","소":"S"}
    for tr in re.findall(r'<tr[^>]*>([\s\S]*?)</tr>', tbodies[1]):
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
        ("pig",     fetch_pig,     "🐷 돼지(산지)"),
        ("cow",     fetch_cow,     "🐂 한우"),
        ("egg",     fetch_egg,     "🥚 계란"),
    ]:
        print(f"{label} 가격 수집...")
        try:
            data = fn()
            if data:
                result["prices"][name] = data
                print(f"  ✅ {data.get('date')} 수집 완료")
                # 주요 수치 출력
                if name=="pig" and data.get("avg_per_kg"):
                    print(f"     농가수취평균: {int(data['avg_per_kg']):,}원/kg  비육돈: {data.get('pig_110kg','-')}천원/110kg")
                elif name=="chicken" and data.get("sanji_live"):
                    print(f"     산지(대): {int(data['sanji_live']):,}원/kg  도매전체: {int(data.get('wholesale_all',0)):,}원/kg")
                elif name=="egg" and data.get("xl_10"):
                    print(f"     XL(특란): {int(data['xl_10']):,}원/10개  L(대란): {int(data.get('l_10',0)):,}원/10개")
            else:
                print(f"  ❌ 수집 실패")
        except Exception as e:
            print(f"  ❌ 오류: {e}")

    with open("prices/prices.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n✅ prices/prices.json 저장 완료 ({result['updated']})")

if __name__ == "__main__":
    main()
