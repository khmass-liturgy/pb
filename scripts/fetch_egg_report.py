#!/usr/bin/env python3
"""디버그용 — HTML 전체 저장"""

import requests, sys
from pathlib import Path

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Referer":    "https://www.ekapepia.com/",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 알려진 URL 그대로
url = "https://www.ekapepia.com/v3/board/detail.do"
params = {
    "pageIndex": "1", "pageUnit": "9",
    "boardNo": "00041017", "boardSkin": "default",
    "boardInfoNo": "0159", "menuId": "",
    "dmlType": "SELECT", "searchType": "",
    "searchCondition": "SUBJECT", "searchKeyword": "",
}

r = requests.get(url, headers=HEADERS, params=params, timeout=20)
r.encoding = "utf-8"
html = r.text
print(f"HTTP {r.status_code} / {len(html)}bytes")

# HTML 저장
Path("egg_report").mkdir(exist_ok=True)
with open("egg_report/debug.html", "w", encoding="utf-8") as f:
    f.write(html)
print("egg_report/debug.html 저장 완료")

# attach 관련 패턴 전수 조사
import re
print("\n=== 'attach' 포함 라인 ===")
for i, line in enumerate(html.splitlines()):
    if "attach" in line.lower():
        print(f"  {i:4d}: {line.strip()[:120]}")

print("\n=== 'download' 포함 라인 ===")
for i, line in enumerate(html.splitlines()):
    if "download" in line.lower() or "Down" in line:
        print(f"  {i:4d}: {line.strip()[:120]}")

print("\n=== 'pdf' 포함 라인 ===")
for i, line in enumerate(html.splitlines()):
    if "pdf" in line.lower():
        print(f"  {i:4d}: {line.strip()[:120]}")

print("\n=== '89200' 포함 라인 ===")
for i, line in enumerate(html.splitlines()):
    if "89200" in line or "41017" in line:
        print(f"  {i:4d}: {line.strip()[:120]}")
