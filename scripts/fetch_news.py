#!/usr/bin/env python3
"""
뉴스 수집 스크립트
Google 뉴스 RSS를 서버에서 직접 파싱해 JSON으로 저장
GitHub Actions에서 실행됨 (CORS 문제 없음)
"""

import feedparser
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# KST 시간대
KST = timezone(timedelta(hours=9))

# 뉴스 채널 정의
CHANNELS = [
    {
        "id": "livestock",
        "label": "축산·농업",
        "rss": "https://news.google.com/rss/search?q=축산+농업+육계+양돈+한우&hl=ko&gl=KR&ceid=KR:ko"
    },
    {
        "id": "vet",
        "label": "수의·방역",
        "rss": "https://news.google.com/rss/search?q=수의사+가축방역+동물병원+가축전염병&hl=ko&gl=KR&ceid=KR:ko"
    },
    {
        "id": "disease",
        "label": "가축질병",
        "rss": "https://news.google.com/rss/search?q=AI+조류독감+구제역+럼피스킨+돼지열병&hl=ko&gl=KR&ceid=KR:ko"
    },
    {
        "id": "feed",
        "label": "사료·약품",
        "rss": "https://news.google.com/rss/search?q=배합사료+동물약품+사료가격&hl=ko&gl=KR&ceid=KR:ko"
    },
    {
        "id": "economy",
        "label": "경제",
        "rss": "https://news.google.com/rss/search?q=경제+금리+환율+물가&hl=ko&gl=KR&ceid=KR:ko"
    },
    {
        "id": "world",
        "label": "국제",
        "rss": "https://news.google.com/rss/search?q=국제+세계뉴스+미국+중국&hl=ko&gl=KR&ceid=KR:ko"
    },
]

CUTOFF_DAYS = 7  # 최근 7일 이내만

def parse_date(entry):
    """feedparser 날짜를 파싱"""
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        import calendar
        ts = calendar.timegm(entry.published_parsed)
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    return None

def fetch_channel(ch):
    """채널 RSS를 파싱해 기사 목록 반환"""
    try:
        feed = feedparser.parse(ch["rss"])
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=CUTOFF_DAYS)
        items = []
        for entry in feed.entries[:20]:
            pub = parse_date(entry)
            if pub and pub < cutoff:
                continue  # 7일 이전 제외
            # 날짜 포맷 (KST)
            date_str = ""
            if pub:
                kst_dt = pub.astimezone(KST)
                date_str = kst_dt.strftime("%m/%d %H:%M")
            items.append({
                "title": entry.get("title", "").strip(),
                "link":  entry.get("link", "").strip(),
                "date":  date_str,
                "source": entry.get("source", {}).get("title", "") if hasattr(entry, "source") else "",
            })
            if len(items) >= 10:
                break
        return items
    except Exception as e:
        print(f"  ❌ {ch['id']} 오류: {e}")
        return []

def main():
    now_kst = datetime.now(KST)
    result = {
        "updated": now_kst.strftime("%Y-%m-%d %H:%M KST"),
        "channels": {}
    }

    # news/ 폴더 생성
    Path("news").mkdir(exist_ok=True)

    for ch in CHANNELS:
        print(f"📰 {ch['label']} 수집 중...")
        items = fetch_channel(ch)
        result["channels"][ch["id"]] = {
            "label": ch["label"],
            "items": items,
            "count": len(items)
        }
        print(f"  ✅ {len(items)}개 수집")

    # news/news.json 저장
    output_path = "news/news.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {output_path} 저장 완료")
    print(f"   업데이트: {result['updated']}")
    total = sum(v["count"] for v in result["channels"].values())
    print(f"   총 기사: {total}개")

if __name__ == "__main__":
    main()
