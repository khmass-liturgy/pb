#!/usr/bin/env python3
"""
축산 협회 공지사항 수집 스크립트
GitHub Actions에서 매일 오전 8시 실행 → notices/notices.json 저장

수집 대상:
- 대한양계협회   (그누보드 방식)
- 대한계육협회   (커스텀 게시판)
- 농축산저널     (워드프레스/커스텀)
- 데일리벳       (워드프레스)
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
}

def get_html(url, timeout=15):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        return resp.text
    except Exception as e:
        print(f"    fetch 실패: {e}")
        return ""

def clean(text):
    """HTML 태그 제거 및 공백 정리"""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ── 그누보드 방식 (대한양계협회) ───────────────────────────────────────────
def parse_gnuboard(html, base_url):
    """
    그누보드 게시판 목록 파싱
    <td class="td_subject"><a href="...">제목</a></td>
    <td class="td_date">2026-04-17</td>
    """
    items = []
    # 글 목록 tr 찾기
    rows = re.findall(r'<tr[^>]*class="[^"]*bo_notice[^"]*"[^>]*>([\s\S]*?)</tr>|<tr[^>]*>([\s\S]*?td_subject[\s\S]*?)</tr>', html)

    # 더 단순한 방식: subject + date td 패턴
    # 그누보드는 td_subject, td_date 클래스 사용
    subjects = re.findall(
        r'class=["\']td_subject["\'][^>]*>([\s\S]*?)</td>', html)
    dates = re.findall(
        r'class=["\']td_date["\'][^>]*>([\s\S]*?)</td>', html)

    for i, subj in enumerate(subjects[:10]):
        # 링크 추출
        link_m = re.search(r'href=["\']([^"\']+)["\']', subj)
        link = ""
        if link_m:
            href = link_m.group(1)
            link = href if href.startswith('http') else base_url.rstrip('/') + '/' + href.lstrip('/')

        title = clean(subj)
        date = clean(dates[i]) if i < len(dates) else ""

        if title and len(title) > 2:
            items.append({"title": title, "link": link, "date": date})

    return items[:10]

# ── 대한계육협회 ────────────────────────────────────────────────────────────
def parse_chicken_assoc(html, base_url):
    """
    chicken.or.kr 커스텀 게시판 파싱
    <a href="boardview_2025.php?...">제목</a> 패턴
    """
    items = []
    rows = re.findall(
        r'<a\s+href=["\']([^"\']*boardview[^"\']*)["\'][^>]*>([\s\S]*?)</a>', html)

    # 날짜 패턴 (yyyy-mm-dd 또는 yy/mm/dd)
    date_pattern = re.compile(r'\d{4}[-./]\d{2}[-./]\d{2}|\d{2}[-./]\d{2}[-./]\d{2}')

    seen = set()
    for href, title_html in rows:
        title = clean(title_html)
        if not title or len(title) < 3 or title in seen:
            continue
        seen.add(title)
        link = href if href.startswith('http') else base_url.rstrip('/') + '/' + href.lstrip('/')
        items.append({"title": title, "link": link, "date": ""})
        if len(items) >= 10:
            break

    # 날짜는 본문 외부 td에서 추출 시도
    dates = date_pattern.findall(html)
    for i, item in enumerate(items):
        if i < len(dates):
            item["date"] = dates[i]

    return items

# ── 워드프레스/일반 뉴스 사이트 ────────────────────────────────────────────
def parse_news_site(html, base_url, link_pattern=None):
    """
    일반 뉴스/블로그 사이트 파싱
    <h2/h3/h4><a href="...">제목</a> 패턴
    """
    items = []
    # 제목+링크 패턴
    patterns = [
        r'<h[234][^>]*>\s*<a\s+href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>',
        r'<a\s+href=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*title[^"\']*["\'][^>]*>([\s\S]*?)</a>',
        r'<a\s+href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>',
    ]

    seen = set()
    for pat in patterns:
        matches = re.findall(pat, html)
        for href, title_html in matches:
            title = clean(title_html)
            if not title or len(title) < 5 or title in seen:
                continue
            # 너무 짧거나 메뉴 같은 텍스트 제외
            if len(title) < 8 or any(x in title for x in ['로그인', '회원가입', '전체메뉴', '더보기', 'HOME', 'MENU']):
                continue
            seen.add(title)
            link = href if href.startswith('http') else base_url.rstrip('/') + '/' + href.lstrip('/')
            items.append({"title": title, "link": link, "date": ""})
            if len(items) >= 10:
                break
        if len(items) >= 5:
            break

    # 날짜 추출 시도
    dates = re.findall(r'\d{4}[-./]\d{2}[-./]\d{2}', html)
    for i, item in enumerate(items):
        if i < len(dates):
            item["date"] = dates[i]

    return items[:10]

# ── 각 협회별 수집 ──────────────────────────────────────────────────────────
SITES = [
    {
        "id": "poultry",
        "name": "대한양계협회",
        "icon": "🥚",
        "boards": [
            {
                "label": "공지사항",
                "url": "https://www.poultry.or.kr/bbs/board.php?bo_table=notice",
                "parser": "gnuboard",
                "base": "https://www.poultry.or.kr",
            },
            {
                "label": "양계 정보마당",
                "url": "https://www.poultry.or.kr/bbs/board.php?bo_table=info",
                "parser": "gnuboard",
                "base": "https://www.poultry.or.kr",
            },
        ],
    },
    {
        "id": "chicken",
        "name": "대한계육협회",
        "icon": "🍗",
        "boards": [
            {
                "label": "공지사항",
                "url": "https://chicken.or.kr/bbs/boardlist_2025.php?Ncode=b3_1",
                "parser": "chicken",
                "base": "https://chicken.or.kr",
            },
            {
                "label": "최신육계뉴스",
                "url": "https://chicken.or.kr/bbs/boardlist_2025.php?Ncode=b3_2",
                "parser": "chicken",
                "base": "https://chicken.or.kr",
            },
        ],
    },
    {
        "id": "country",
        "name": "농축산저널",
        "icon": "📰",
        "boards": [
            {
                "label": "전체 뉴스",
                "url": "https://countrynews.co.kr/ko-kr",
                "parser": "news",
                "base": "https://countrynews.co.kr",
            },
        ],
    },
    {
        "id": "vet",
        "name": "데일리벳",
        "icon": "🩺",
        "boards": [
            {
                "label": "산업동물 뉴스",
                "url": "https://www.dailyvet.co.kr/category/news/practice/industrial-animal",
                "parser": "dailyvet",
                "base": "https://www.dailyvet.co.kr",
            },
            {
                "label": "가축질병·방역동향",
                "url": "https://www.dailyvet.co.kr/category/news/animalwelfare",
                "parser": "dailyvet",
                "base": "https://www.dailyvet.co.kr",
            },
        ],
    },
]

def parse_dailyvet(html, base_url):
    """
    데일리벳(WordPress) 기사 목록 파싱
    구조: <a href="https://www.dailyvet.co.kr/news/...">제목</a>
          날짜: 2026.07.15
    """
    items = []
    seen = set()
    # 기사 링크 패턴 (뉴스 URL만)
    links = re.findall(
        r'<a\s+href="(https://www\.dailyvet\.co\.kr/news/[^"]+)"[^>]*>([\s\S]*?)</a>',
        html
    )
    # 날짜 패턴
    dates = re.findall(r'(\d{4}\.\d{2}\.\d{2})', html)
    date_idx = 0

    for href, title_html in links:
        title = clean(title_html)
        if not title or len(title) < 5 or title in seen:
            continue
        # 너무 짧거나 메뉴성 텍스트 제외
        if any(x in title for x in ['로그인','회원가입','댓글','좋아요','더보기','AI 기사요약','일부 결과']):
            continue
        seen.add(title)
        date = dates[date_idx] if date_idx < len(dates) else ""
        if date:
            date_idx += 1
        items.append({"title": title, "link": href, "date": date})
        if len(items) >= 10:
            break

    return items


def fetch_board(board):
    html = get_html(board["url"])
    if not html:
        return []
    parser = board["parser"]
    base   = board["base"]
    if parser == "gnuboard":
        return parse_gnuboard(html, base)
    elif parser == "chicken":
        return parse_chicken_assoc(html, base)
    elif parser == "dailyvet":
        return parse_dailyvet(html, base)
    else:
        return parse_news_site(html, base)

def main():
    now_kst = datetime.now(KST)
    result = {
        "updated": now_kst.strftime("%Y-%m-%d %H:%M KST"),
        "sites": {}
    }
    Path("notices").mkdir(exist_ok=True)

    for site in SITES:
        print(f"{site['icon']} {site['name']} 수집 중...")
        site_result = {"name": site["name"], "icon": site["icon"], "boards": {}}

        for board in site["boards"]:
            print(f"  [{board['label']}] {board['url']}")
            items = fetch_board(board)
            site_result["boards"][board["label"]] = items
            print(f"  → {len(items)}개 수집")

        result["sites"][site["id"]] = site_result

    with open("notices/notices.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ notices/notices.json 저장 완료 ({result['updated']})")

if __name__ == "__main__":
    main()
