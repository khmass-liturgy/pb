#!/usr/bin/env python3
"""(사)대한산란계협회(kegg.or.kr) "중추가격" 게시물 수집기.

협회가 매월 게시판(https://kegg.or.kr/board/sub3?Ncode=breed)에 올리는 "중추가격"
글은 표가 텍스트가 아니라 이미지 한 장(그래프 + 연도별 월별 표)으로만 올라온다.
그래서 이 스크립트는 숫자를 파싱하지 않고, 그 이미지 자체를 원본 그대로
저장소에 미러링한다 — OCR로 숫자를 억지로 뽑으면 오독 위험이 있는데, 사료값도
아니고 시세 데이터에서 틀린 숫자를 보여주는 쪽이 아예 안 보여주는 쪽보다 더
나쁘다고 판단했다.

같은 글 번호(number=)를 계속 수정해서 쓰는 게시판이라 "작성일"이 실제
갱신일을 반영하지 않는다(예: 2026년 8월 자료인데 작성일은 2024-01-11로 찍혀
있음). 그래서 이미지 바이트의 해시가 바뀐 시점을 "실제로 새 이미지가 올라온
시점"의 대용치로 같이 기록해 둔다.

확인된 구조:
  목록: https://kegg.or.kr/board/sub3?Ncode=breed
        <a href="/board/view3?Ncode=breed&number=107...">중추가격</a>
  본문: https://kegg.or.kr/board/view3?Ncode=breed&number=107
        <td id='zoom_box' ...><img src="/upload/xxxx.jpg" ...>...<div class="snsShare">
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, urljoin

import requests

KST = timezone(timedelta(hours=9))
BASE_URL = "https://kegg.or.kr"
LIST_URL = f"{BASE_URL}/board/sub3?Ncode=breed"
JSON_OUTPUT_PATH = Path("jungchu_price/latest.json")
IMAGE_OUTPUT_PATH = Path("jungchu_price/latest.jpg")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; pb-jungchu-price/1.0)", "Accept-Language": "ko-KR,ko;q=0.9"}
PROXY_URLS = [
    lambda url: "https://api.allorigins.win/raw?url=" + quote(url, safe=""),
    lambda url: "https://api.codetabs.com/v1/proxy/?quest=" + quote(url, safe=""),
]

# 게시글 제목이 정확히 "중추가격"이 아니라 "중추가격(수정)"처럼 붙는 경우까지
# 열어두되, "산란실용병아리"나 "산란성계육"처럼 이름이 겹치는 다른 글은 배제한다.
TITLE_PATTERN = re.compile(r"^\s*중추\s*가격")


def _get_text(url: str) -> str | None:
    """직접 요청 실패 시 공개 CORS 프록시로 재시도(다른 fetch 스크립트와 동일한 관례)."""
    for candidate in [url] + [factory(url) for factory in PROXY_URLS]:
        try:
            resp = requests.get(candidate, headers=HEADERS, timeout=20)
            resp.encoding = resp.apparent_encoding or "utf-8"
            if resp.ok and resp.text:
                return resp.text
        except requests.RequestException as exc:
            print(f"  텍스트 요청 실패({candidate[:60]}...): {type(exc).__name__}: {exc}")
    return None


def _get_bytes(url: str) -> bytes | None:
    for candidate in [url] + [factory(url) for factory in PROXY_URLS]:
        try:
            resp = requests.get(candidate, headers=HEADERS, timeout=30)
            if resp.ok and resp.content:
                return resp.content
        except requests.RequestException as exc:
            print(f"  이미지 요청 실패({candidate[:60]}...): {type(exc).__name__}: {exc}")
    return None


def find_post_url() -> tuple[str, str] | None:
    """목록에서 "중추가격" 글의 상세 URL과 제목을 찾는다."""
    html = _get_text(LIST_URL)
    if not html:
        return None
    for m in re.finditer(r'<a href="(/board/view3\?Ncode=breed[^"]*)">([^<]*)</a>', html):
        title = m.group(2).strip()
        if TITLE_PATTERN.match(title):
            return urljoin(BASE_URL, m.group(1)), title
    return None


def find_image_url(detail_html: str) -> str | None:
    """본문 영역(zoom_box)에서 첨부 이미지 하나를 찾는다.

    SNS 공유 아이콘(twitter/band/kakao)도 <img>라서, zoom_box 시작부터
    snsShare 시작 전까지로 범위를 좁혀 찾는다.
    """
    start = detail_html.find("zoom_box")
    if start == -1:
        return None
    end = detail_html.find("snsShare", start)
    body = detail_html[start:end if end != -1 else start + 4000]
    m = re.search(r'<img[^>]+src="([^"]+)"', body)
    if not m:
        return None
    return urljoin(BASE_URL, m.group(1))


def main() -> int:
    now = datetime.now(KST)

    previous: dict = {}
    if JSON_OUTPUT_PATH.exists():
        try:
            previous = json.loads(JSON_OUTPUT_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            previous = {}

    def fail(reason: str) -> int:
        if not previous:
            print(f"수집 실패({reason})했고, 이전 데이터도 없습니다.")
            return 1
        print(f"수집 실패({reason}) — 이전 데이터를 그대로 유지합니다(stale).")
        previous["stale"] = True
        previous["last_error"] = reason
        previous["last_checked"] = now.strftime("%Y-%m-%d %H:%M KST")
        JSON_OUTPUT_PATH.write_text(json.dumps(previous, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0

    found = find_post_url()
    if not found:
        return fail("목록에서 '중추가격' 글을 찾지 못함")
    post_url, title = found

    detail_html = _get_text(post_url)
    if not detail_html:
        return fail("본문 페이지 요청 실패")

    image_url = find_image_url(detail_html)
    if not image_url:
        return fail("본문에서 첨부 이미지를 찾지 못함")

    image_bytes = _get_bytes(image_url)
    if not image_bytes:
        return fail("이미지 다운로드 실패")

    image_hash = hashlib.sha256(image_bytes).hexdigest()
    hash_changed = image_hash != previous.get("image_hash")
    # 게시판 "작성일"이 실제 갱신일을 반영하지 않으므로(같은 글을 계속 덮어씀),
    # 이미지 해시가 바뀐 시점을 "새 이미지가 올라온 걸 우리가 처음 확인한 시점"으로 기록한다.
    hash_updated_at = now.strftime("%Y-%m-%d %H:%M KST") if hash_changed else previous.get("hash_updated_at", now.strftime("%Y-%m-%d %H:%M KST"))

    IMAGE_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    IMAGE_OUTPUT_PATH.write_bytes(image_bytes)

    JSON_OUTPUT_PATH.write_text(json.dumps({
        "title": title,
        "post_url": post_url,
        "list_url": LIST_URL,
        "image_path": str(IMAGE_OUTPUT_PATH).replace("\\", "/"),
        "image_hash": image_hash,
        "hash_updated_at": hash_updated_at,
        "updated": now.strftime("%Y-%m-%d %H:%M KST"),
        "note": "대한산란계협회가 매월 게시하는 산란계 중추가격 표/그래프 이미지를 그대로 가져온 것입니다. "
                "이미지 제목에 적힌 '○○년 ○월 기준'이 실제 데이터 기준월이며, 게시판 작성일은 최초 등록일로 "
                "고정돼 있어 실제 갱신 여부와 무관합니다.",
        "stale": False,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"수집 성공: {title} ({post_url}) hash={image_hash[:12]} changed={hash_changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
