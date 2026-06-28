#!/usr/bin/env python3
"""
축산·수의 업계 일일 브리핑 자동 생성 스크립트
매일 GitHub Actions에서 실행됩니다.

필요 환경변수:
  ANTHROPIC_API_KEY — GitHub Secrets에 저장
"""

import os
import sys
from datetime import datetime, timezone, timedelta
import anthropic

# ── 날짜 설정 (KST) ─────────────────────────────────────────────────────────
KST = timezone(timedelta(hours=9))
today = datetime.now(KST)
date_str   = today.strftime("%Y년 %m월 %d일")
file_date  = today.strftime("%Y-%m-%d")
weekday    = ["월", "화", "수", "목", "금", "토", "일"][today.weekday()]

# ── 브리핑 프롬프트 ──────────────────────────────────────────────────────────
PROMPT = f"""오늘 날짜: {date_str} ({weekday}요일)

매일 아침 축산·수의 관련 업계 브리핑을 작성하세요.
웹 검색을 통해 최신 정보를 수집하고 아래 5개 항목을 포함하여 한국어로 보고서를 작성하세요.

오늘 날짜를 기준으로 최근 24~48시간 이내 정보를 우선 수집하세요.

### 1. 🐄 축산물 시세
- 한우 (도매가, 등급별 시세 변동)
- 돼지 (삼겹살, 전지 등 주요 부위 도매가)
- 닭 (육계, 토종닭, 계란, 육계병아리, 삼계 도매가)
- 전일 대비 등락 방향 명시

### 2. 🌾 사료 원료 시세
- 옥수수 (국제 선물가, CBOT)
- 대두박 (국제가)
- 원유가격 (WTI)
- 달러/원 환율

### 3. 📰 업계 뉴스
- 축산관련 주요 정책 및 규제 변화
- 수의관련 정책 및 주요뉴스
- 업계 주요 이슈 (수출입, 기업 동향 등)
- 소비 트렌드 및 시장 변화

### 4. 🦠 질병/방역 동향
- 고병원성 조류인플루엔자(AI) 발생 현황
- 구제역(FMD) 발생 및 위험 경보
- 아프리카돼지열병(ASF) 동향
- 농림축산식품부 방역 조치 사항

### 5. 🌤️ 날씨 정보
- 오늘의 날씨 (온도/습도)
- 육계/산란계 사양관리 컨설팅 포인트
- 금주 날씨 전망

## 출력 형식
- 날짜와 요일을 제목에 포함
- 각 섹션별 핵심 수치와 전일/전주 대비 변동 명시
- 특이사항이 없는 항목은 "이상 없음"으로 간략히 기재
- 전체 분량: A4 1~2페이지 분량
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
                    result.append(new_entry)   # 최신 항목을 맨 위에 삽입
                elif in_section and line.startswith("- ["):
                    if entry_count < 29:       # 최근 30개만 유지
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
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ 오류: ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    print(f"📋 브리핑 생성 시작: {date_str} ({weekday}요일)")

    client = anthropic.Anthropic(api_key=api_key)

    # Claude API 호출 (웹 검색 도구 활성화)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8096,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 15,
            }
        ],
        messages=[{"role": "user", "content": PROMPT}],
    )

    # 최종 텍스트 추출 (tool_use 블록 제외)
    briefing_text = "\n".join(
        block.text for block in response.content
        if block.type == "text"
    ).strip()

    if not briefing_text:
        print("❌ 오류: Claude로부터 텍스트 응답을 받지 못했습니다.")
        sys.exit(1)

    # 파일 저장
    os.makedirs("briefings", exist_ok=True)
    output_path = f"briefings/{file_date}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(briefing_text)
    print(f"✅ 브리핑 저장 완료: {output_path}")

    # README 업데이트
    update_readme(file_date, date_str, weekday)


if __name__ == "__main__":
    main()
