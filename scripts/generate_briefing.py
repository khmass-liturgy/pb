#!/usr/bin/env python3
"""
축산·수의 업계 일일 브리핑 자동 생성 스크립트
매일 GitHub Actions에서 실행됩니다.

GitHub Models (무료) 사용 — GITHUB_TOKEN은 Actions에서 자동 제공됩니다.
별도 API 키 불필요.
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from openai import OpenAI

# ── 날짜 설정 (KST) ─────────────────────────────────────────────────────────
KST = timezone(timedelta(hours=9))
today = datetime.now(KST)
date_str   = today.strftime("%Y년 %m월 %d일")
file_date  = today.strftime("%Y-%m-%d")
weekday    = ["월", "화", "수", "목", "금", "토", "일"][today.weekday()]

# ── 브리핑 프롬프트 ──────────────────────────────────────────────────────────
PROMPT = f"""오늘 날짜: {date_str} ({weekday}요일)

매일 아침 축산·수의 관련 업계 브리핑을 작성하세요.
아래 5개 항목을 포함하여 한국어로 보고서를 작성하세요.
가장 최신 학습 데이터 기준으로 시세와 정보를 제공하고, 불확실한 경우 추정임을 명시하세요.

### 1. 🐄 축산물 시세
- 간략한 한우,돼지,닭 (산지시세)
- 닭,돼지,한우,계란 산지시세는 https://www.ekapepia.com/v3/web/main.do?userGroup=producer 에서 추출

### 2. 🌾 사료 원료 시세
- 옥수수 (국제 선물가, CBOT)
- 대두박 (국제 선물가, CBOT)
- 원유가격 (WTI)
- 달러/원 환율
- 국내 코스피/코스닥 전일 지수

### 3. 📰 업계 뉴스
- 축산관련 주요 정책 및 규제 변화
- 수의관련 정책 및 주요뉴스
- 동물약품업계/사료회사 주요 이슈 (수출입, 동물약품회사, 사료회사 동향 등)
- 소비 트렌드 및 시장 변화

### 4. 🦠 질병/방역 동향
- 국내외 고병원성 조류인플루엔자(AI) 발생 현황
- 구제역(FMD) 발생 및 위험 경보
- 아프리카돼지열병(ASF) 동향
- 농림축산검역본부 홈페이지(https://www.qia.go.kr/listindexWebAction.do) 정보를 가져와서 질병방역정보를 가져와줘

### 5. 🌤️ 날씨 정보
- 오늘의 날씨 (온도/습도, 서울 기준)
- 육계/산란계 사양관리 컨설팅 포인트
- 해당월 계절별 가금류 질병발생 동향
- 금주 날씨 전망

## 출력 형식
- 날짜와 요일을 제목에 포함
- 각 섹션별 핵심 수치와 전일/전주 대비 변동 명시
- 특이사항이 없는 항목은 "이상 없음"으로 간략히 기재
- 전체 분량: A4 2~3페이지 분량
"""

# ── README 업데이트 ──────────────────────────────────────────────────────────
def update_readme(file_date: str, date_str: str, weekday: str) -> None:
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

# ── 메인 ────────────────────────────────────────────────────────────────────
def main() -> None:
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("❌ 오류: GITHUB_TOKEN이 없습니다.")
        sys.exit(1)

    print(f"📋 브리핑 생성 시작: {date_str} ({weekday}요일)")

    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=github_token,
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": PROMPT}],
        temperature=0.7,
        max_tokens=8192,
    )

    briefing_text = response.choices[0].message.content.strip()

    if not briefing_text:
        print("❌ 오류: 텍스트 응답을 받지 못했습니다.")
        sys.exit(1)

    os.makedirs("briefings", exist_ok=True)
    output_path = f"briefings/{file_date}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(briefing_text)
    print(f"✅ 브리핑 저장 완료: {output_path}")

    update_readme(file_date, date_str, weekday)


if __name__ == "__main__":
    main()
