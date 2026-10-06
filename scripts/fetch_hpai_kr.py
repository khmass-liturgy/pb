#!/usr/bin/env python3
"""국내 고병원성 AI 가금농장 발생·야생조류 검출 현황 수집.

농림축산식품부 「고병원성 조류인플루엔자 발생·검출 현황('YY.M.D. 17시 기준)」 글
(https://www.mafra.go.kr/bbs/FMD-AI2/851/artclList.do)의 첨부 .hwp에는 그 시즌 처음부터
기준일까지의 가금농장 발생 목록과 야생조류 검출 목록이 표로 들어 있다. 가장 최근 글의
첨부를 받아 표를 읽어 hpai_kr/latest.json 으로 저장한다.

농식품부 게시판은 발생 직후가 아니라 가끔 갱신된다(25/26 시즌은 12.30 이후 3.22). 그래서
Google 뉴스 RSS에서 최근 사흘의 "가금농장 고병원성 AI" 보도 제목도 함께 모아 `news`에
넣어, 게시판이 늦을 때도 새 발생 소식을 볼 수 있게 한다(지도는 게시판 표 기준).

농식품부는 해외 IP를 막으므로 GitHub Actions에서는 자동 문자 발송과 같은 국내 중계 서버
(SMS_RELAY_URL/SMS_RELAY_SECRET)의 /fetch-mafra 경로를 쓴다(fetch_feed_production.py와 동일).

부분 실패는 이전 JSON을 지우지 않는다: 농식품부 표를 못 읽어도 news만 갱신하고, news를 못 받아도
표 데이터는 갱신한다. 둘 다 못 받으면 비정상 종료한다.
"""

from __future__ import annotations

import json
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, urljoin

import requests

KST = timezone(timedelta(hours=9))
OUT_PATH = Path("hpai_kr/latest.json")
BASE = "https://www.mafra.go.kr"
LIST_URL = f"{BASE}/bbs/FMD-AI2/851/artclList.do"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}
OLE2_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

_RELAY_URL = os.environ.get("SMS_RELAY_URL", "").strip()
_RELAY_SECRET = os.environ.get("SMS_RELAY_SECRET", "").strip()
RELAY_FETCH = (re.sub(r"/send-sms/?$", "", _RELAY_URL) + "/fetch-mafra") if _RELAY_URL and _RELAY_SECRET else None

TITLE_RE = re.compile(r"발생[·ㆍ・]?검출\s*현황\s*\(\s*['‘’]?(\d{2})\.(\d{1,2})\.(\d{1,2})\.?\s*(\d{1,2})시\s*기준")
POST_RE = re.compile(r'href="(/bbs/FMD-AI2/851/(\d+)/artclView\.do[^"]*)"[^>]*>([\s\S]*?)</a>')
FILE_RE = re.compile(r'href="(/bbs/FMD-AI2/851/\d+/download\.do)"[^>]*>\s*([^<]*?\.hwp)', re.I)


def _candidates(url: str):
    if RELAY_FETCH:
        yield (f"{RELAY_FETCH}?url={quote(url, safe='')}",
               {**HEADERS, "Authorization": f"Bearer {_RELAY_SECRET}"}, "국내 중계 서버")
    yield url, HEADERS, url[:70]


def _get(url: str, binary: bool = False):
    for candidate, headers, name in _candidates(url):
        try:
            resp = requests.get(candidate, headers=headers, timeout=30)
            if not resp.ok:
                print(f"  HTTP {resp.status_code}: {name}")
                continue
            if binary:
                if resp.content.startswith(OLE2_MAGIC):
                    return resp.content
                print(f"  .hwp가 아닌 응답({len(resp.content)}bytes): {name}")
                continue
            resp.encoding = "utf-8"
            if resp.text:
                return resp.text
        except requests.RequestException as exc:
            detail = type(exc).__name__ if name == "국내 중계 서버" else f"{type(exc).__name__}: {exc}"
            print(f"  요청 실패({name}): {detail}")
    return None


# ── HWP 본문 텍스트 ─────────────────────────────────────────────────────────
def hwp_text(content: bytes) -> list[str]:
    """HWP 5.x 본문의 문단 텍스트를 한 줄씩. 표 셀도 한 칸씩 한 줄로 나온다."""
    import olefile
    import io

    ole = olefile.OleFileIO(io.BytesIO(content))
    compressed = bool(ole.openstream("FileHeader").read()[36] & 1)
    out: list[str] = []
    for name in sorted(s for s in ole.listdir() if s[0] == "BodyText"):
        data = ole.openstream(name).read()
        if compressed:
            data = zlib.decompress(data, -15)
        i = 0
        while i < len(data):
            h = struct.unpack("<I", data[i:i + 4])[0]
            tag, size = h & 0x3FF, (h >> 20) & 0xFFF
            i += 4
            if size == 0xFFF:
                size = struct.unpack("<I", data[i:i + 4])[0]
                i += 4
            if tag == 67:   # HWPTAG_PARA_TEXT
                out.append(data[i:i + size].decode("utf-16le", errors="ignore"))
            i += size
    lines = []
    for t in out:
        t = re.sub(r"[\x00-\x1f]", " ", t).strip()
        if t:
            lines.append(t)
    return lines


def _num(s: str) -> int:
    return int(re.sub(r"[^\d]", "", s) or 0)


def _date(s: str, ref: datetime) -> str:
    """'’25.9.12' · '10.21' · '(‘26.1.2)' → YYYY-MM-DD. 연도 표기가 없으면 기준일보다 뒤 달은 작년."""
    s = re.sub(r"[‘’'()\s]", "", s).strip(".")
    parts = [p for p in s.split(".") if p]
    if len(parts) == 3:
        y, m, d = 2000 + int(parts[0]), int(parts[1]), int(parts[2])
    else:
        m, d = int(parts[0]), int(parts[1])
        y = ref.year if m <= ref.month else ref.year - 1
    return f"{y:04d}-{m:02d}-{d:02d}"


def parse_tables(lines: list[str], ref: datetime) -> tuple[list[dict], list[dict]]:
    """(가금농장 목록, 야생조류 목록)."""
    # 가금농장 표 머리말 마지막 칸 '확진일', 야생조류 표 마지막 칸 '시료'
    farms: list[dict] = []
    wild: list[dict] = []
    try:
        fi = next(i for i, t in enumerate(lines) if t == "연번" and "신고일" in " ".join(lines[i:i + 6]))
        fi = next(i for i in range(fi, len(lines)) if lines[i] == "확진일") + 1
    except StopIteration:
        raise RuntimeError("가금농장 표 머리말을 찾지 못함(양식 변경?)")
    i = fi
    while i + 10 < len(lines) and lines[i].isdigit() and lines[i + 1] in ("신고", "예찰"):
        r = lines[i:i + 11]
        farms.append({"n": int(r[0]), "kind": r[1], "rep": _date(r[2], ref), "sido": r[3], "sgg": r[4],
                      "sp": r[5], "breed": r[6], "cnt": _num(r[7]), "sero": r[9], "conf": _date(r[10], ref)})
        i += 11
    try:
        wi = next(i for i, t in enumerate(lines) if t == "연번" and "도래지" in " ".join(lines[i:i + 8]))
        wi = next(i for i in range(wi, len(lines)) if lines[i] == "시료") + 1
    except StopIteration:
        wi = None
    if wi is not None:
        j = wi
        while j + 9 < len(lines) and lines[j].isdigit():
            r = lines[j:j + 10]
            wild.append({"n": int(r[0]), "date": _date(r[1], ref), "sido": r[2], "sgg": r[3], "spot": r[4],
                         "sero": r[5], "conf": _date(r[6], ref), "sample": r[9].replace("페사체", "폐사체")})
            j += 10
    return farms, wild


def latest_post() -> dict:
    html = _get(LIST_URL)
    if not html:
        raise RuntimeError("농식품부 게시판 목록을 받지 못함")
    best = None
    for href, art_id, inner in POST_RE.findall(html):
        title = re.sub(r"<[^>]+>|\s+", " ", inner).replace("&apos;", "'").replace("&#39;", "'").strip()
        m = TITLE_RE.search(title)
        if not m:
            continue
        y, mo, d, hh = 2000 + int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        ref = datetime(y, mo, d, hh, tzinfo=KST)
        if best is None or ref > best["ref"] or (ref == best["ref"] and int(art_id) > best["id"]):
            best = {"id": int(art_id), "title": title, "url": urljoin(BASE, href), "ref": ref}
    if not best:
        raise RuntimeError("'발생·검출 현황' 글을 목록에서 찾지 못함")
    return best


def fetch_table_data() -> dict:
    post = latest_post()
    html = _get(post["url"])
    if not html:
        raise RuntimeError("글을 열지 못함")
    m = FILE_RE.search(html)
    if not m:
        raise RuntimeError("첨부 .hwp를 찾지 못함")
    content = _get(urljoin(BASE, m.group(1)), binary=True)
    if not content:
        raise RuntimeError("첨부 .hwp를 받지 못함")
    lines = hwp_text(content)
    farms, wild = parse_tables(lines, post["ref"])
    # 표 위 "총 N건" 과 읽은 행 수가 맞는지 확인(양식이 달라져 일부만 읽었는지 감지)
    tot = [int(x) for x in re.findall(r"총\s*(\d+)\s*건", " ".join(lines[:80]))]
    if tot and farms and tot[0] != len(farms):
        raise RuntimeError(f"가금농장 건수 불일치: 문서 {tot[0]}건, 읽은 행 {len(farms)}건")
    if not farms:
        raise RuntimeError("가금농장 행을 읽지 못함")
    return {"as_of": post["ref"].strftime("%Y-%m-%d %H:%M KST"), "title": post["title"], "url": post["url"],
            "farms": farms, "wild": wild}


# ── 뉴스(게시판이 늦을 때 보조) ─────────────────────────────────────────────
NEWS_URL = ("https://news.google.com/rss/search?q=" +
            quote("고병원성 AI 가금농장 확진 when:3d") + "&hl=ko&gl=KR&ceid=KR:ko")
NEWS_KEEP = re.compile(r"(고병원성|AI|조류인플루엔자).{0,40}(확진|발생|검출)|(확진|발생).{0,40}(고병원성|AI)")
NEWS_PREVENT = re.compile(r"대비|대응|예방|훈련|점검|대책|차단|캠페인|교육|특별방역|행정명령")   # 방역 준비 기사는 '발생 소식'이 아니다


def fetch_news() -> list[dict]:
    resp = requests.get(NEWS_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    items, seen = [], set()
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        key = re.sub(r"\s*-\s*[^-]+$", "", title)[:30]
        if not title or key in seen or not NEWS_KEEP.search(title) or ("확진" not in title and NEWS_PREVENT.search(title)):
            continue
        seen.add(key)
        items.append({"title": title, "link": it.findtext("link") or "", "date": it.findtext("pubDate") or "",
                      "source": (it.findtext("source") or "").strip()})
        if len(items) >= 8:
            break
    return items


def main() -> int:
    prev = {}
    if OUT_PATH.exists():
        try:
            prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
    out = dict(prev)
    errors = []
    try:
        out.update(fetch_table_data())
        out["table_stale"] = False
        print(f"표 갱신: {out['title']} · 가금농장 {len(out['farms'])}건 · 야생조류 {len(out['wild'])}건")
    except Exception as exc:
        errors.append(f"표: {exc}")
        out["table_stale"] = True
        print(f"::warning::농식품부 표를 못 받아 이전 값 유지 — {exc}")
    try:
        out["news"] = fetch_news()
        print(f"뉴스 {len(out['news'])}건")
    except Exception as exc:
        errors.append(f"뉴스: {exc}")
        print(f"::warning::뉴스를 못 받아 이전 값 유지 — {exc}")
    if len(errors) == 2:
        print("둘 다 실패:", errors)
        return 1
    out["checked"] = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    new_text = json.dumps(out, ensure_ascii=False, indent=1)
    # 내용이 같으면 확인 시각만 바뀌므로 파일을 다시 쓰지 않는다(매번 커밋되는 것 방지)
    def core(d):
        return {k: v for k, v in d.items() if k != "checked"}
    if prev and core(prev) == core(out):
        print("변경 없음")
        return 0
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(new_text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
