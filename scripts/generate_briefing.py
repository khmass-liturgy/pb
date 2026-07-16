#!/usr/bin/env python3
"""
축산·수의 업계 일일 브리핑 자동 생성 스크립트
매일 GitHub Actions에서 실행됩니다.

개선사항:
- prices/prices.json 실제 수집 데이터를 프롬프트에 직접 주입
- 가축질병·방역 동향을 구글 뉴스 RSS에서 실시간 수집
- gpt-4o 모델 사용으로 품질 향상
"""

import os
import sys
import json
import re
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from openai import OpenAI

# ── 날짜 설정 (KST) ─────────────────────────────────────────────────────────
KST = timezone(timedelta(hours=9))
today = datetime.now(KST)
date_str  = today.strftime("%Y년 %m월 %d일")
file_date = today.strftime("%Y-%m-%d")
weekday   = ["월","화","수","목","금","토","일"][today.weekday()]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# ── 실제 시세 데이터 로드 ────────────────────────────────────────────────────
def load_prices():
    """prices/prices.json에서 실제 수집된 시세 로드"""
    try:
        with open("prices/prices.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        prices = data.get("prices", {})
        updated = data.get("updated", "")
        if not prices:
            return None, updated
        return prices, updated
    except Exception as e:
        print(f"  ⚠️ prices.json 로드 실패: {e}")
        return None, ""

def format_prices(prices):
    """시세 데이터를 브리핑용 텍스트로 변환"""
    if not prices:
        return "※ 시세 데이터 수집 실패 — 다봄 Actions 확인 필요"

    lines = []

    # 육계
    ch = prices.get("chicken")
    if ch:
        diff_s = f"({'+' if (ch.get('diff_sanji_live') or 0)>0 else ''}{ch.get('diff_sanji_live','N/A')})" if ch.get('diff_sanji_live') is not None else ""
        diff_w = f"({'+' if (ch.get('diff_wholesale_all') or 0)>0 else ''}{ch.get('diff_wholesale_all','N/A')})" if ch.get('diff_wholesale_all') is not None else ""
        lines.append(f"【육계】{ch.get('date','')} 기준")
        lines.append(f"  산지(생계유통 대): {int(ch['sanji_live']):,}원/kg {diff_s}" if ch.get('sanji_live') else "  산지: N/A")
        lines.append(f"  도매(전체): {int(ch['wholesale_all']):,}원/kg {diff_w}" if ch.get('wholesale_all') else "  도매: N/A")
        if ch.get('consumer'):
            lines.append(f"  소매: {int(ch['consumer']):,}원/kg")

    # 계란
    eg = prices.get("egg")
    if eg:
        diff_xl = f"({'+' if (eg.get('diff_xl_10') or 0)>0 else ''}{eg.get('diff_xl_10','N/A')})" if eg.get('diff_xl_10') is not None else ""
        lines.append(f"\n【계란】{eg.get('date','')} 기준 (10개 단위)")
        lines.append(f"  XL(특란): {int(eg['xl_10']):,}원/10개 {diff_xl}" if eg.get('xl_10') else "  XL: N/A")
        lines.append(f"  L(대란): {int(eg['l_10']):,}원/10개" if eg.get('l_10') else "  L: N/A")
        lines.append(f"  30개환산 XL: {int(eg['xl_30']):,}원" if eg.get('xl_30') else "")

    # 돼지
    pg = prices.get("pig")
    if pg:
        diff_a = f"({'+' if (pg.get('diff_avg') or 0)>0 else ''}{pg.get('diff_avg','N/A')})" if pg.get('diff_avg') is not None else ""
        diff_p = f"({'+' if (pg.get('diff_pig') or 0)>0 else ''}{pg.get('diff_pig','N/A')})" if pg.get('diff_pig') is not None else ""
        lines.append(f"\n【돼지】{pg.get('date','')} 기준 (산지가격)")
        lines.append(f"  농가수취 평균: {int(pg['avg_per_kg']):,}원/kg {diff_a}" if pg.get('avg_per_kg') else "  농가수취 평균: N/A")
        lines.append(f"  비육돈: {pg.get('pig_110kg')}천원/110kg ({int(pg['pig_per_kg']):,}원/kg) {diff_p}" if pg.get('pig_per_kg') else "  비육돈: N/A")
        lines.append(f"  전월평균: {int(pg['month_avg_per_kg']):,}원/kg" if pg.get('month_avg_per_kg') else "")
        lines.append(f"  전년동월평균: {int(pg['year_avg_per_kg']):,}원/kg" if pg.get('year_avg_per_kg') else "")

    # 한우
    cw = prices.get("cow")
    if cw:
        diff_c = f"({'+' if (cw.get('diff_castrated') or 0)>0 else ''}{cw.get('diff_castrated','N/A')})" if cw.get('diff_castrated') is not None else ""
        lines.append(f"\n【한우】{cw.get('date','')} 기준 (천원/마리)")
        lines.append(f"  농가수취 거세우: {int(cw['hanwoo_castrated']):,}천원 {diff_c}" if cw.get('hanwoo_castrated') else "  거세우: N/A")
        lines.append(f"  농가수취 평균: {int(cw['hanwoo_avg']):,}천원" if cw.get('hanwoo_avg') else "")
        lines.append(f"  큰암소: {int(cw['big_cow']):,}천원" if cw.get('big_cow') else "")
        lines.append(f"  수송아지(6~7월령): {int(cw['calf_m_67']):,}천원" if cw.get('calf_m_67') else "")
        lines.append(f"  암송아지(6~7월령): {int(cw['calf_f_67']):,}천원" if cw.get('calf_f_67') else "")

    return "\n".join(l for l in lines if l)

# ── 가축질병·방역 동향 — 데일리벳 + Google 뉴스 수집 ────────────────────────
def fetch_dailyvet_welfare():
    """
    데일리벳 동물복지·방역 카테고리 기사 수집
    URL: https://www.dailyvet.co.kr/category/news/animalwelfare
    """
    url = "https://www.dailyvet.co.kr/category/news/animalwelfare"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        html = resp.text

        items = []
        seen = set()
        # 데일리벳 뉴스 링크: /news/ 포함 URL
        links = re.findall(
            r'href="(https://www\.dailyvet\.co\.kr/news/[^"]+)"[^>]*>([^<]{10,120})<',
            html
        )
        dates = re.findall(r'(\d{4}\.\d{2}\.\d{2})', html)
        date_idx = 0

        for href, title in links:
            title = title.strip()
            if not title or title in seen:
                continue
            if any(x in title for x in ['로그인','AI 기사요약','일부 결과','댓글','좋아요']):
                continue
            seen.add(title)
            date = dates[date_idx] if date_idx < len(dates) else ""
            if date:
                date_idx += 1
            items.append({"title": title, "link": href, "date": date})
            if len(items) >= 8:
                break

        return items
    except Exception as e:
        print(f"  ⚠️ 데일리벳 수집 실패: {e}")
        return []


def fetch_disease_news():
    """
    가축질병·방역 동향 수집
    1) 데일리벳 동물복지·방역 카테고리 (주요 소스)
    2) Google 뉴스 RSS (AI·구제역·ASF 보완)
    """
    results = []

    # ① 데일리벳 기사
    dv_items = fetch_dailyvet_welfare()
    if dv_items:
        results.append("[데일리벳 동물복지·방역 최신 기사]")
        for item in dv_items[:6]:
            results.append(f"  - {item['title']} ({item['date']}) {item['link']}")
    else:
        results.append("[데일리벳] 수집 실패 — Google 뉴스로 대체")

    results.append("")

    # ② Google 뉴스 RSS (가축전염병 보완)
    keywords = [
        ("고병원성 조류인플루엔자 AI", "고병원성 AI"),
        ("구제역 FMD", "구제역"),
        ("아프리카돼지열병 ASF", "ASF"),
    ]
    for query, label in keywords:
        try:
            rss_url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=ko&gl=KR&ceid=KR:ko&when=7d"
            resp = requests.get(rss_url, headers=HEADERS, timeout=10)
            resp.encoding = 'utf-8'
            titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', resp.text)
            dates  = re.findall(r'<pubDate>(.*?)</pubDate>', resp.text)
            items  = []
            for i, title in enumerate(titles[1:3]):
                date_s = dates[i].strip()[:16] if i < len(dates) else ""
                items.append(f"  - {title.strip()} ({date_s})")
            if items:
                results.append(f"[{label}]")
                results.extend(items)
            else:
                results.append(f"[{label}] 최근 7일 특이사항 없음")
        except Exception as e:
            results.append(f"[{label}] 수집 실패: {e}")

    return "\n".join(results)

# ── 메인 ────────────────────────────────────────────────────────────────────
def update_readme(file_date, date_str, weekday):
    readme_path = "README.md"
    new_entry = f"- [{date_str} ({weekday}요일)](briefings/{file_date}.md)"
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "## 최근 브리핑" in content:
            lines = content.splitlines()
            result, in_section, entry_count = [], False, 0
            for line in lines:
                if line.strip() == "## 최근 브리핑":
                    in_section = True
                    result.append(line)
                    result.append(new_entry)
                elif in_section and line.startswith("- ["):
                    if entry_count < 29:
                        result.append(line)
                    entry_count += 1
                else:
                    in_section = False
                    result.append(line)
            content = "\n".join(result)
        else:
            content += f"\n\n## 최근 브리핑\n{new_entry}\n"
    else:
        content = (
            "# 🐄 축산·수의 업계 일일 브리핑\n\n"
            "매일 자동 생성되는 축산·수의 업계 브리핑입니다.\n\n"
            f"## 최근 브리핑\n{new_entry}\n"
        )
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ README 업데이트 완료")

def main():
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("❌ 오류: GITHUB_TOKEN이 없습니다.")
        sys.exit(1)

    print(f"📋 브리핑 생성 시작: {date_str} ({weekday}요일)")

    # 실제 시세 데이터 로드
    print("  💰 시세 데이터 로드 중...")
    prices, prices_updated = load_prices()
    prices_text = format_prices(prices)
    print(f"  {'✅' if prices else '⚠️'} 시세: {prices_updated or '없음'}")

    # 가축질병 방역 뉴스 수집
    print("  🦠 방역 뉴스 수집 중...")
    disease_news = fetch_disease_news()
    print("  ✅ 방역 뉴스 수집 완료")

    # 브리핑 프롬프트 (실제 데이터 주입)
    prompt = f"""오늘 날짜: {date_str} ({weekday}요일)

당신은 축산·수의 업계 전문 애널리스트입니다.
아래에 제공된 【실제 수집 데이터】를 반드시 사용하여 오늘의 일일 브리핑을 작성하세요.
데이터가 없는 항목만 "추정" 또는 "확인 필요"로 표시하세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【실제 수집된 산지·도매 시세】 (출처: KAPE 다봄, {prices_updated})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{prices_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【실제 수집된 가축질병·방역 뉴스】 (출처: Google 뉴스, 최근 7일)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{disease_news}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

위 데이터를 바탕으로 아래 5개 섹션으로 브리핑을 작성하세요.

### 1. 🐄 축산물 산지·도매 시세 분석
- 위의 실제 수집 데이터를 그대로 인용하여 표 형태로 정리
- 전일 대비 등락(▲▼) 명시
- 시세 수준에 대한 전문가 코멘트 (최근 추세, 계절적 요인 등)
- 육계·계란·돼지·한우 각각 1~2줄 분석

### 2. 🌾 사료 원료 및 에너지 시세
- 옥수수 CBOT 선물가 (최신 학습 데이터 기준, 추정 명시)
- 대두박 CBOT 선물가 (추정)
- WTI 원유가 (추정)
- 환율 USD/KRW (추정)
- 국내 배합사료 가격 동향

### 3. 📰 축산·수의 업계 주요 뉴스
- 국내 축산 정책 및 규제 동향
- 수의사·동물병원 관련 이슈
- 동물약품·사료회사 동향
- 소비 트렌드 및 수출입 현황

### 4. 🦠 가축질병·방역 동향
- 위의 【데일리벳 동물복지·방역 최신 기사】를 최우선으로 인용·요약
- 각 기사 제목과 핵심 내용을 1~2줄로 정리 (URL은 괄호 안에 표시)
- 고병원성 AI·구제역·ASF 관련 기사가 있으면 별도 강조
- 농가 방역 관련 주의사항·정책 동향 포함
- 데일리벳 기사가 없는 경우 Google 뉴스 수집 결과 활용

### 5. 🌤️ 날씨 및 사양관리
- 오늘·금주 날씨 전망 (서울 기준 추정)
- {today.month}월 계절적 특성에 따른 가금류 사양관리 포인트
- 고온다습 시 폐사 예방, 음수 관리 등 실무 조언
- 계절성 질병(열스트레스, 뉴캐슬, 마렉 등) 주의사항

## 출력 형식 요구사항
- 제목: # {date_str} ({weekday}요일) 축산·수의 일일 브리핑
- 각 섹션은 ### 헤더로 구분
- 시세는 반드시 위의 실제 데이터 수치 사용 (추정값 혼용 금지)
- 전문적이고 실무에 바로 활용 가능한 내용
- 분량: A4 3~4페이지 (마크다운 기준 약 1,500~2,500단어)
"""

    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=github_token,
    )

    print("  🤖 AI 브리핑 생성 중...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,   # 낮춰서 실제 데이터에 충실하게
        max_tokens=8192,
    )

    briefing_text = response.choices[0].message.content.strip()
    if not briefing_text:
        print("❌ 오류: 응답이 비어있습니다.")
        sys.exit(1)

    os.makedirs("briefings", exist_ok=True)
    output_path = f"briefings/{file_date}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(briefing_text)
    print(f"✅ 브리핑 저장 완료: {output_path}")

    update_readme(file_date, date_str, weekday)

if __name__ == "__main__":
    main()
