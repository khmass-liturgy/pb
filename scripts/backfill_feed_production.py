#!/usr/bin/env python3
"""배합사료 생산실적 과거 연도 소급 수집 — 시세예측 모형의 학습·백테스트용.

fetch_feed_production.py가 매일 올해·작년 두 해만 `feed_production/latest.json`에 두는 것과 달리, 여기서는 게시판을
더 깊이 뒤져 연도별 최신 글의 첨부 .xls(그 해 1~12월)를 받아 `feed_production/history.json`에 모은다.
같은 파서·같은 중계 서버(국내)를 쓰므로 SMS_RELAY_URL / SMS_RELAY_SECRET이 필요하다.
양식이 해마다 다를 수 있어 해당 연도만 건너뛰고 계속한다(실패한 연도는 출력에 남긴다).

  python scripts/backfill_feed_production.py [시작연도 끝연도]   # 기본: 2016 ~ (최신연도 - 2)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import fetch_feed_production as ff

OUT = Path("feed_production/history.json")


def list_all_posts(max_pages: int = 40) -> list[dict]:
    """ff.list_posts는 작년 12월분을 찾으면 멈춘다 — 여기서는 더 오래된 글까지 끝(빈 쪽)까지 훑는다."""
    posts, empty = [], 0
    for page in range(1, max_pages + 1):
        html = ff._get(f"{ff.LIST_URL}?page={page}")
        if not html:
            break
        found = 0
        for href, art_id, inner in ff.POST_RE.findall(html):
            title = ff.re.sub(r"\s*새글$", "", ff.re.sub(r"<[^>]+>|\s+", " ", inner).strip())
            m = ff.TITLE_RE.search(title)
            if m:
                found += 1
                posts.append({"year": int(m.group(1)), "month": int(m.group(2)), "id": int(art_id), "title": title, "url": ff.urljoin(ff.BASE, href)})
        empty = 0 if found else empty + 1
        if empty >= 3:                       # 연속 3쪽에 해당 글이 없으면 더 오래된 글이 없다고 본다
            break
    print(f"  게시판 {page}쪽까지 확인, 글 {len(posts)}건")
    return posts


def main(argv: list[str]) -> int:
    posts = list_all_posts()
    if not posts:
        print("게시판에서 글을 찾지 못함")
        return 1
    years_found = sorted({p["year"] for p in posts})
    print("게시판에서 찾은 연도:", years_found)
    latest = max(years_found)
    y0, y1 = (int(argv[0]), int(argv[1])) if len(argv) >= 2 else (2016, latest - 2)
    data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"years": {}}
    for year in range(y0, y1 + 1):
        try:
            got = ff.fetch_year(posts, year)
        except Exception as exc:                      # 양식 변경·글 없음 — 그 해만 건너뜀
            print(f"  {year}년 건너뜀: {type(exc).__name__}: {exc}")
            continue
        data["years"][str(year)] = {"through_month": got["through_month"], "post_title": got["post_title"], "groups": got["groups"]}
    data["updated"] = datetime.now(ff.KST).strftime("%Y-%m-%d %H:%M KST")
    data["source"] = "농림축산식품부 「배합사료 생산실적」 (연도별 최신 글의 첨부파일)"
    data["unit"] = "톤"
    data["years"] = dict(sorted(data["years"].items()))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("저장된 연도:", sorted(data["years"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
