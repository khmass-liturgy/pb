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

# ── 주간 계란 수급 정보 로드 ────────────────────────────────────────────────────
def load_egg_report():
    """egg_report/latest.json 로드 (fetch_egg_report.py가 매주 저장)"""
    path = "egg_report/latest.json"
    if not os.path.exists(path):
        return None, None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        title   = data.get("title", "")
        updated = data.get("updated", "")
        summary = data.get("summary", {})
        text    = data.get("text", "")
        tables  = data.get("tables", [])

        lines = [f"[주간 계란 수급 정보] {title} (수집: {updated})"]
        lines.append(f"원본 URL: {data.get('url','')}")
        lines.append("")

        if summary:
            meta = []
            for k, v in summary.items():
                label = {"period":"대상기간","sequence":"차수","supply_status":"수급상황"}.get(k, k)
                meta.append(f"{label}: {v}")
            if meta:
                lines.append("▶ " + " / ".join(meta))
                lines.append("")

        # ★ 섹션별 <요약> 블록 (핵심 데이터)
        sections = [s for s in data.get("sections", []) if "생산" not in s.get("title","")]

        # 용어 설명·통계표 등 부가 블록 제외
        DROP_PATS = [
            r"수급\s*강도\s*구분",           # 용어 설명
            r"선별\s*포장\s*처리\s*실적",   # 권역별·규격별 통계표
            r"이력제\s*자료",                 # 위 표의 부제
        ]

        def _clean(txt):
            if not txt:
                return txt
            t = re.sub(r"\s+", " ", str(txt)).strip()
            # □ 구간 단위로 잘라 제외 대상 블록 제거
            def _drop(m):
                seg = m.group(0)
                return " " if any(re.search(p, seg) for p in DROP_PATS) else seg
            t = re.sub(r"[□■▣◇◆]\s*[^□■▣◇◆]*", _drop, t)
            # 마커 없이 이어진 경우: 가장 앞선 매칭 지점부터 끝까지 제거
            idxs = [m.start() for p in DROP_PATS for m in [re.search(p, t)] if m]
            if idxs:
                t = t[:min(idxs)]
            return re.sub(r"\s+", " ", t).strip()

        sections = [{**s, "summary": _clean(s.get("summary",""))} for s in sections]
        sections = [s for s in sections if len(s.get("summary","")) > 20]
        if sections:
            lines.append("▶ 섹션별 요약 (PDF <요약> 원문)")
            for sec in sections:
                lines.append(f"  [{sec.get('no','')}] {sec.get('title','')}")
                lines.append(f"    {sec.get('summary','')}")
                lines.append("")
        elif text:
            lines.append("▶ PDF 전문 (요약 추출 실패)")
            lines.append(text[:1500])

        return "\n".join(lines), updated
    except Exception as e:
        return f"계란 수급 정보 로드 실패: {e}", None


# ── 해외 조류인플루엔자 발생동향 — KAHIS 국외현황 + Google 뉴스 ──────────────
def fetch_kahis_overseas_ai():
    """
    해외 AI 발생동향 수집
    1) KAHIS 해외위생정보 동향 (게시판 목록에서 AI 관련 글 필터)
    2) Google 뉴스 RSS 보완 (HPAI 해외 최신)
    """
    results = []

    # ① KAHIS 국외현황 게시판 (조류인플루엔자 관련만 필터)
    try:
        url = "https://home.kahis.go.kr/home/lkdissinfo/lkdissinfoBbsList.do?type=1_5hwwsdx"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.encoding = resp.apparent_encoding or "utf-8"
        html = resp.text

        # 게시글 제목·날짜 추출 (제목: <a ...>제목</a> 패턴)
        title_pats = re.findall(r'javascript:fn_select\([^)]+\)[^>]*>([^<]+)<', html)
        date_pats  = re.findall(r'(\d{4}-\d{2}-\d{2})', html)
        rows = list(zip(date_pats, title_pats))
        # 조류인플루엔자 관련만 필터 (가금 포함)
        ai_keywords = ["조류인플루엔자", "AI", "HPAI", "LPAI", "고병원성", "가금"]
        ai_rows = []
        for no, title, date in rows:
            title = re.sub(r"\s+", " ", title).strip()
            if any(k in title for k in ai_keywords):
                ai_rows.append((date, title))

        if ai_rows:
            # 최신순 정렬
            ai_rows.sort(key=lambda x: x[0], reverse=True)
            results.append(f"[KAHIS 해외 조류인플루엔자 발생동향] (최신 {min(len(ai_rows),10)}건)")
            for date, title in ai_rows[:10]:
                results.append(f"  • {date} | {title}")
            results.append(f"  ※ 총 {len(ai_rows)}건 (게시판 1페이지 기준) · 상세: https://home.kahis.go.kr/home/lkdissinfo/lkdissinfoBbsList.do?type=1_5hwwsdx")
        else:
            results.append("[KAHIS 해외 AI] 1페이지 내 AI 관련 게시글 없음 (2025.01 이후 검역본부로 이관)")

    except Exception as e:
        results.append(f"[KAHIS 해외 AI] 수집 실패: {e}")

    results.append("")

    # ② Google 뉴스 RSS — 해외 HPAI 최신 동향 보완
    try:
        queries = [
            ("고병원성 조류인플루엔자 해외 발생 2026", "해외 HPAI"),
            ("avian influenza HPAI outbreak 2026", "HPAI (영문)"),
        ]
        results.append("[Google 뉴스 — 해외 HPAI 최신 동향]")
        for query, label in queries:
            rss_url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=ko&gl=KR&ceid=KR:ko&when=14d"
            resp = requests.get(rss_url, headers=HEADERS, timeout=10)
            resp.encoding = "utf-8"
            titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", resp.text)
            dates  = re.findall(r"<pubDate>(.*?)</pubDate>", resp.text)
            for i, title in enumerate(titles[1:4]):
                date_s = dates[i].strip()[:16] if i < len(dates) else ""
                results.append(f"  • [{label}] {title.strip()} ({date_s})")
    except Exception as e:
        results.append(f"  수집 실패: {e}")

    return "\n".join(results)


# ── 가축전염병 발생현황 — KAHIS 국가가축방역통합시스템 ───────────────────────
def fetch_kahis_disease():
    """
    KAHIS 법정가축전염병 발생현황 파싱
    URL: https://home.kahis.go.kr/home/lkntscrinfo/selectLkntsOccrrncList.do
    테이블 구조: 가축전염병명 | 농장명 | 농장소재지 | 발생일자(진단일) | 축종 | 발생두수 | 진단기관 | 종식일
    """
    url = "https://home.kahis.go.kr/home/lkntscrinfo/selectLkntsOccrrncList.do"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        html = resp.text

        # <td> 셀 추출
        cells = re.findall(r'<td[^>]*>([\s\S]*?)</td>', html)
        # 태그 제거
        def clean_cell(s):
            s = re.sub(r'<[^>]+>', '', s)
            return re.sub(r'\s+', ' ', s).strip()
        cells = [clean_cell(c) for c in cells if clean_cell(c)]

        # 8개 컬럼 단위로 행 구성
        # 컬럼: 질병명, 농장명(농장주), 농장소재지, 발생일자(진단일), 축종(품종), 발생두수(마리), 진단기관, 종식일
        rows = []
        i = 0
        while i + 7 < len(cells):
            # 첫 번째 셀이 질병명처럼 보이는 경우만 행으로 간주
            disease = cells[i]
            date_str = cells[i+3]
            species  = cells[i+4]
            count    = cells[i+5]
            region   = cells[i+2]
            end_date = cells[i+7]

            # 날짜 패턴 확인으로 유효 행 필터
            if re.search(r'\d{4}-\d{2}-\d{2}', date_str):
                rows.append({
                    "disease": disease,
                    "region":  region,
                    "date":    date_str.split('(')[0].strip(),
                    "species": species,
                    "count":   count,
                    "ended":   "종식" if end_date and end_date not in ('-','') else "진행중",
                })
                i += 8
            else:
                i += 1

        if not rows:
            return "KAHIS 파싱 실패 — 데이터 없음"

        # 질병별 집계
        from collections import defaultdict
        by_disease = defaultdict(list)
        for r in rows:
            by_disease[r['disease']].append(r)

        # 결과 텍스트 생성
        lines = [f"[KAHIS 법정가축전염병 발생현황] 조회일: {datetime.now(KST).strftime('%Y-%m-%d')} / 총 {len(rows)}건"]
        lines.append("")

        # 종식되지 않은 건 (진행중) 우선
        active = [r for r in rows if r['ended'] == '진행중']
        ended  = [r for r in rows if r['ended'] == '종식']

        if active:
            lines.append(f"▶ 현재 진행중 ({len(active)}건)")
            for r in active[:15]:
                lines.append(f"  • {r['disease']} | {r['region']} | {r['species']} {r['count']}마리 | 발생일 {r['date']}")
            lines.append("")

        lines.append(f"▶ 최근 종식 완료 ({len(ended)}건 중 최신 10건)")
        for r in ended[:10]:
            lines.append(f"  • {r['disease']} | {r['region']} | {r['species']} {r['count']}마리 | 발생일 {r['date']}")

        lines.append("")
        lines.append("▶ 질병별 발생 건수 (이번 조회 기준)")
        for disease, cases in sorted(by_disease.items(), key=lambda x: -len(x[1])):
            total_count = sum(int(c['count']) for c in cases if c['count'].replace(',','').isdigit())
            lines.append(f"  • {disease}: {len(cases)}건 / {total_count:,}마리")

        return "\n".join(lines)

    except Exception as e:
        print(f"  ⚠️ KAHIS 수집 실패: {e}")
        return f"KAHIS 수집 실패: {e}"


def fetch_disease_news():
    """KAHIS 국내 + 해외 AI + 데일리벳 병행 수집"""
    results = []

    # ① KAHIS 법정가축전염병 발생현황 (주요 소스)
    print("  🔍 KAHIS 가축전염병 발생현황 수집...")
    kahis = fetch_kahis_disease()
    results.append(kahis)
    results.append("")

    # ② 해외 조류인플루엔자 발생동향
    print("  🔍 해외 조류인플루엔자 동향 수집...")
    overseas_ai = fetch_kahis_overseas_ai()
    results.append(overseas_ai)
    results.append("")

    # ② 데일리벳 animalwelfare 기사 (방역 뉴스 보완)
    print("  🔍 데일리벳 방역 기사 수집...")
    try:
        url = "https://www.dailyvet.co.kr/category/news/animalwelfare"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        links = re.findall(
            r'href="(https://www\.dailyvet\.co\.kr/news/[^"]+)"[^>]*>([^<]{10,120})<',
            resp.text
        )
        dates = re.findall(r'(\d{4}\.\d{2}\.\d{2})', resp.text)
        items, seen, di = [], set(), 0
        for href, title in links:
            title = title.strip()
            if not title or title in seen: continue
            if any(x in title for x in ['로그인','AI 기사요약','댓글','좋아요']): continue
            seen.add(title)
            date = dates[di] if di < len(dates) else ""
            if date: di += 1
            items.append(f"  - {title} ({date}) {href}")
            if len(items) >= 6: break
        if items:
            results.append("[데일리벳 방역·동물복지 최신 기사]")
            results.extend(items)
    except Exception as e:
        results.append(f"[데일리벳] 수집 실패: {e}")

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


# ── AI 제공자 어댑터 ────────────────────────────────────────────────────────
# GitHub Models 가 2026-07-30 자로 완전 종료되어(플레이그라운드·추론 API·BYOK 모두)
# 다른 제공자로 옮겼다. 한 곳이 막혀도 시크릿만 바꿔 끼울 수 있도록 어댑터로 분리한다.
#
# 사용법: 저장소 Secrets 에 아래 중 하나만 등록하면 자동 선택된다.
#   GEMINI_API_KEY  → Google AI Studio (무료 일 1,500회, 한국어 우수) · 권장
#   GROQ_API_KEY    → Groq (무료 일 14,400회, 응답 빠름)
#   OPENAI_API_KEY  → OpenAI (유료)
# AI_PROVIDER 환경변수로 강제 지정도 가능: gemini | groq | openai

PROVIDERS = [
    ("gemini", "GEMINI_API_KEY", "gemini-3-flash"),
    ("groq",   "GROQ_API_KEY",   "llama-3.3-70b-versatile"),
    ("openai", "OPENAI_API_KEY", "gpt-4o"),
]

# 모델명이 바뀌거나 특정 모델이 내려갔을 때 순서대로 재시도할 후보.
# 2026-04 부터 Gemini 무료 티어는 Flash·Flash-Lite 계열만 제공된다(Pro 는 유료).
MODEL_FALLBACKS = {
    "gemini": ["gemini-3-flash", "gemini-2.5-flash",
               "gemini-3.1-flash-lite", "gemini-2.5-flash-lite", "gemini-2.0-flash"],
    "groq":   ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
    "openai": ["gpt-4o", "gpt-4o-mini"],
}


def resolve_provider():
    """(provider, api_key, model) 반환. 키가 없으면 api_key=None"""
    forced = (os.environ.get("AI_PROVIDER") or "").strip().lower()
    model_override = (os.environ.get("AI_MODEL") or "").strip()

    for name, env_key, default_model in PROVIDERS:
        if forced and forced != name:
            continue
        key = os.environ.get(env_key)
        if key:
            return name, key, (model_override or default_model)

    return (forced or "none"), None, model_override


def _post_json(url, payload, headers, timeout=180):
    r = requests.post(url, json=payload, headers=headers, timeout=timeout)
    if r.status_code != 200:
        raise Exception("HTTP %d — %s" % (r.status_code, r.text[:300]))
    return r.json()


def _gen_gemini(api_key, model, prompt):
    """Google AI Studio (Gemini) — OpenAI SDK 없이 REST 직접 호출"""
    url = ("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent"
           % model)
    data = _post_json(url, {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.5, "maxOutputTokens": 8192},
    }, {"Content-Type": "application/json", "x-goog-api-key": api_key})

    cands = data.get("candidates") or []
    if not cands:
        fb = (data.get("promptFeedback") or {}).get("blockReason")
        raise Exception("응답 없음%s" % (" (차단: %s)" % fb if fb else ""))
    parts = (cands[0].get("content") or {}).get("parts") or []
    return "".join(p.get("text", "") for p in parts).strip()


def _gen_openai_compatible(base_url, api_key, model, prompt):
    """OpenAI 호환 chat/completions (Groq·OpenAI 공통)"""
    data = _post_json(base_url.rstrip("/") + "/chat/completions", {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 8192,
    }, {"Content-Type": "application/json",
        "Authorization": "Bearer " + api_key})

    choices = data.get("choices") or []
    if not choices:
        raise Exception("choices 없음 — %s" % str(data)[:200])
    return (choices[0].get("message") or {}).get("content", "").strip()


def _call_model(provider, api_key, model, prompt):
    if provider == "gemini":
        return _gen_gemini(api_key, model, prompt)
    if provider == "groq":
        return _gen_openai_compatible("https://api.groq.com/openai/v1",
                                      api_key, model, prompt)
    if provider == "openai":
        return _gen_openai_compatible("https://api.openai.com/v1",
                                      api_key, model, prompt)
    raise Exception("알 수 없는 제공자: %s" % provider)


def generate_with_provider(provider, api_key, model, prompt):
    """모델 폴백 + 재시도. 모델명이 바뀌어도 후보를 순서대로 시도한다."""
    import time as _t

    # 지정 모델을 맨 앞에 두고 후보 목록 구성 (중복 제거)
    candidates, seen = [], set()
    for m in [model] + MODEL_FALLBACKS.get(provider, []):
        if m and m not in seen:
            seen.add(m)
            candidates.append(m)

    last = None
    for m in candidates:
        for attempt in range(1, 4):
            try:
                text = _call_model(provider, api_key, m, prompt)
                if text:
                    if m != model:
                        print("    ℹ️ 대체 모델 사용: %s" % m)
                    return text
                last = Exception("빈 응답")
            except Exception as e:
                last = e
                msg = str(e)
                print("    ⚠️ [%s] 시도 %d/3 실패: %s" % (m, attempt, msg[:160]))
                # 모델이 없거나 권한 문제면 재시도 없이 다음 모델로
                if any(k in msg for k in ("HTTP 404", "HTTP 400", "HTTP 403",
                                          "not found", "does not exist",
                                          "decommissioned")):
                    break
            if attempt < 3:
                _t.sleep(5 * attempt)

    print("❌ 브리핑 생성 실패: %s" % last)
    return ""


def main():
    provider, api_key, model = resolve_provider()
    if not api_key:
        print("❌ 오류: AI 제공자 API 키가 없습니다.")
        print("   저장소 Secrets 에 GEMINI_API_KEY 또는 GROQ_API_KEY 를 등록하세요.")
        sys.exit(1)

    print(f"📋 브리핑 생성 시작: {date_str} ({weekday}요일)")

    # 실제 시세 데이터 로드
    print("  💰 시세 데이터 로드 중...")
    # 시세 섹션 제거됨 (데이터 정확도 문제)

    # 주간 계란 수급 정보 로드
    print("  🥚 주간 계란 수급 정보 로드 중...")
    egg_report, egg_updated = load_egg_report()
    egg_section = egg_report or "이번 주 계란 수급 정보 없음 (매주 화요일 업데이트)"
    print(f"  {'✅' if egg_report else '⚠️'} 계란 수급 정보: {egg_updated or '없음'}")

    # 가축질병 방역 뉴스 수집
    print("  🦠 방역 뉴스 수집 중...")
    disease_news = fetch_disease_news()
    print("  ✅ 방역 뉴스 수집 완료")

    # 브리핑 프롬프트 (실제 데이터 주입)
    prompt = f"""오늘 날짜: {date_str} ({weekday}요일)

당신은 축산·수의 업계 전문 애널리스트입니다.
아래에 제공된 【실제 수집 데이터】를 반드시 사용하여 오늘의 일일 브리핑을 작성하세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【주간 계란 수급 정보】 (출처: KAPE 다봄, 매주 업데이트)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{egg_section}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【실제 수집된 가축전염병 발생현황 + 해외 AI 동향】 (출처: KAHIS 국내·국외현황 + 데일리벳)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{disease_news}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

위 데이터를 바탕으로 아래 3개 섹션으로 브리핑을 작성하세요.

### 1. 🥚 주간 계란 수급 동향
- 위의 【주간 계란 수급 정보】 ▶섹션별 요약 내용을 그대로 인용·정리
- 각 섹션(생산 동향 / 유통 동향 / 가격 동향 등)별로 소제목을 달고 핵심만 3~5줄
- PDF 요약문에 없는 내용은 절대 추가하지 말 것 (추정·창작 금지)
- 마지막에 "농가 시사점" 2~3줄만 추가
- 계란 수급 정보가 없으면 "이번 주 미발행"으로 표시하고 섹션 생략

### 2. 🦠 가축전염병 발생현황 및 방역 동향

**[국내 발생현황]**
- 위의 【KAHIS 가축전염병 발생현황】을 기반으로 작성 (실제 발생 데이터 그대로 인용)
- 현재 진행중인 발생 건 우선 정리: 질병명 / 발생지역 / 축종·두수 / 농가 주의사항
- 뉴캐슬·마렉 등 상시 관리 질병은 별도 이슈 없으면 생략
- 고병원성 AI·구제역·ASF·브루셀라·결핵 등 법정전염병 발생시 별도 강조
- KAHIS 데이터 기준 "현재 진행중 0건" 이면 "현재 법정전염병 특이 발생 없음"으로 표시

**[해외 조류인플루엔자(HPAI) 동향]**
- 위의 【해외 조류인플루엔자 발생동향】 데이터를 그대로 인용
- 국가별 발생 현황 요약 (가금 발생 우선, 야생조류 발생 별도 표시)
- 주요 수입국(미국·유럽·동남아 등) AI 발생시 국내 닭고기·종란 수입 영향 언급
- 데일리벳 방역 기사 중 주목할 내용 1~2건 요약

### 3. 🌤️ 날씨 및 축산농가 사양관리

**[오늘·금주 날씨 요약]**
- {today.month}월 {today.day}일 기준 날씨 전망 (기온·강수·풍속 등 핵심 수치 포함)
- 일교차, 습도, 강수 여부 — 축산농가 영향 중심으로 요약

**[가금류(닭·오리) 사양관리]**
- 현재 기온·습도 기준 열스트레스 지수(THI) 평가 및 위험도
- 고온기: 환기 설정값(최소·최대풍속), 쿨링패드·미스터 운영 기준
- 음수량 증가 대응 (수온 관리, 전해질 공급 여부)
- 사료 섭취량 변화 예측 및 급이 시간대 조정 권고
- 폐사 위험 시간대 (주로 새벽 2~4시, 오후 2~5시) 집중 점검 권고

**[양돈·한우 사양관리]**
- 돈사·우사 환기·냉방 운영 기준
- 고온 스트레스로 인한 번식 장애·수태율 저하 주의사항
- 음수·사료 관리 포인트

**[강수·태풍 대비]** ← 강수 예보 있는 경우에만 작성, 없으면 생략
- 축사 침수·누수 점검 항목
- 야외 가축 대피 및 사료 보관 주의사항
- 강풍 시 비닐하우스형 축사 보강 체크리스트

## 출력 형식 요구사항
- 제목: # {date_str} ({weekday}요일) 축산·수의 일일 브리핑
- 각 섹션은 ### 헤더로 구분
- 수치·근거가 있는 실무 중심 내용 (추정은 반드시 명시)
- 분량: A4 2~3페이지 (마크다운 기준 약 1,000~1,800단어)
"""

    print(f"  🤖 AI 브리핑 생성 중... ({provider} / {model})")
    briefing_text = generate_with_provider(provider, api_key, model, prompt)
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
