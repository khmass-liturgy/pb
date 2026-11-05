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

── 빠른 집계(quick) ──
「발생·검출 현황」 표는 며칠~몇 주 늦게 올라온다(26/27 시즌 첫 발생 연천 산란계 11.4 확진도 표에 없음).
그래서 발생 당일 나오는 ① 농식품부 가축전염병 보도자료 게시판(bbs/FMD-AI2/393, 중수본 「…고병원성 조류인플루엔자
발생에 따라 방역관리 강화」 — 중계 서버 허용 목록에 393을 넣어야 열림) 과 ② 최근 사흘 「가금농장 고병원성 AI 확진」
보도 본문을 Claude(ANTHROPIC_API_KEY)에게 주고 확진 농장(시도·시군·축종·마릿수·확진일·혈청형)만 JSON으로 뽑아
`quick`에 쌓는다. 같은 농장(시도·시군·확진일 ±2일)이 농식품부 표에 들어오면 quick에서 뺀다. 화면은 「보도 기준」으로 따로 표시.
API 키가 없으면 quick은 이전 값 그대로 둔다.
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


# ── 빠른 집계: 보도자료·보도 본문 → 확진 농장 ─────────────────────────────
PRESS_LIST_URL = f"{BASE}/bbs/FMD-AI2/393/artclList.do"
PRESS_POST_RE = re.compile(r'href="(/bbs/FMD-AI2/393/(\d+)/artclView\.do[^"]*)"[^>]*>([\s\S]*?)</a>')
AI_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
SIDO = {"서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"}
SIDO_LONG = {"서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구", "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
             "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기", "강원도": "강원", "강원특별자치도": "강원", "충청북도": "충북",
             "충청남도": "충남", "전라북도": "전북", "전북특별자치도": "전북", "전라남도": "전남", "경상북도": "경북", "경상남도": "경남",
             "제주도": "제주", "제주특별자치도": "제주"}
SP_OK = {"닭", "오리", "메추리", "기타"}
EXTRACT_PROMPT = """다음은 국내 고병원성 조류인플루엔자(AI) 관련 {kind}입니다(게재 {pub}).
이 글에서 **국내 가금농장에서 고병원성 AI가 확진된 농장**만 골라 JSON 배열로 출력하세요. 다른 글은 쓰지 마세요.
[{{"conf":"YYYY-MM-DD","rep":"YYYY-MM-DD","sido":"경기","sgg":"연천군","sp":"닭","breed":"산란계","cnt":12345,"approx":false,"sero":"H5N1","kind":"신고","nth":1}}]
규칙:
- 확진(고병원성으로 확인)된 농장만. '의심', '검사 중', '저병원성', 야생조류 검출, 해외 발생, 과거 시즌 사례, 방역 대책 설명은 빼세요.
- conf: 고병원성 확진일. 글에 '4일'처럼 일만 있으면 게재 연·월을 쓰고, 확진일이 없으면 게재일.
- sido: 서울·부산·대구·인천·광주·대전·울산·세종·경기·강원·충북·충남·전북·전남·경북·경남·제주 중 하나(짧은 이름).
- sgg: 시·군·구 이름 그대로(예: 연천군, 천안시 동남구는 천안시). 모르면 그 농장은 빼세요.
- sp: 닭·오리·메추리·기타 중 하나. breed: 산란계·육계·종계·토종닭·육용오리·종오리·메추리 등 글에 나온 대로.
- rep: 농장이 신고한 날(예: '전날(3일) 신고'), 없으면 "". 
- cnt: 그 농장 사육 마릿수(정수, '약 1만2천 마리'는 12000). 없으면 null. approx: '약', '~여 마리'처럼 대략값이면 true. sero: H5N1 등, 없으면 "". kind: 신고/예찰, 없으면 "".
- nth: '올겨울 N번째', '이번 동절기 N번째'가 있으면 N, 없으면 null.
- 글에 없는 내용은 지어내지 마세요. 해당 농장이 없으면 [] 만 출력하세요.

제목: {title}

본문:
{text}"""


def season_start(today: datetime) -> str:
    return f"{today.year if today.month >= 9 else today.year - 1}-09-01"


def _sgg_key(s: str) -> str:
    s = re.sub(r"\s+", "", s or "")
    return re.sub(r"(시|군|구)$", "", s) if len(s) > 2 else s


def same_farm(a: dict, b: dict, days: int = 2) -> bool:
    if a.get("sido") != b.get("sido") or _sgg_key(a.get("sgg")) != _sgg_key(b.get("sgg")):
        return False
    try:
        da, db = datetime.strptime(a["conf"], "%Y-%m-%d"), datetime.strptime(b["conf"], "%Y-%m-%d")
    except (KeyError, ValueError):
        return False
    return abs((da - db).days) <= days and (not a.get("breed") or not b.get("breed") or a["breed"] == b["breed"]
                                            or a.get("sp") == b.get("sp"))


def ai_extract(title: str, text: str, kind: str, pub: datetime, api_key: str) -> list[dict] | None:
    prompt = EXTRACT_PROMPT.format(kind=kind, pub=pub.strftime("%Y-%m-%d"), title=title, text=text[:6000])
    resp = requests.post(ANTHROPIC_URL, headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                         json={"model": AI_MODEL, "max_tokens": 800, "messages": [{"role": "user", "content": prompt}]}, timeout=60)
    if not resp.ok:
        print(f"  Anthropic 응답 {resp.status_code}: {resp.text[:160]}")
        return None                     # 다음 실행 때 다시 시도
    out = "".join(b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text")
    m = re.search(r"\[[\s\S]*\]", out)
    try:
        rows = json.loads(m.group(0)) if m else []
    except json.JSONDecodeError:
        return []
    return [r for r in rows if isinstance(r, dict)]


def clean_quick(r: dict, pub: datetime, start: str) -> dict | None:
    """AI가 뽑은 한 줄을 검사해 지도에 넣을 모양으로 — 이상하면 버린다."""
    sido = SIDO_LONG.get(str(r.get("sido", "")).strip(), str(r.get("sido", "")).strip())
    sgg = re.sub(r"\s+", "", str(r.get("sgg", "")))
    sgg = re.sub(r"^(.+?[시군])(?:.+구)$", r"\1", sgg)          # 천안시동남구 → 천안시
    conf = str(r.get("conf", ""))
    if sido not in SIDO or not re.fullmatch(r"[가-힣]{1,6}[시군구]?", sgg or "") or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", conf):
        return None
    try:
        cd = datetime.strptime(conf, "%Y-%m-%d").replace(tzinfo=KST)
    except ValueError:
        return None
    if conf < start or cd > pub + timedelta(days=1) or cd < pub - timedelta(days=14):
        return None
    sp = str(r.get("sp", "")).strip()
    cnt = r.get("cnt")
    cnt = int(cnt) if isinstance(cnt, (int, float)) and 0 < cnt < 5_000_000 else 0
    sero = str(r.get("sero") or "").strip().upper()
    nth = r.get("nth")
    rp = str(r.get("rep") or "")
    rp = rp if re.fullmatch(r"\d{4}-\d{2}-\d{2}", rp) and rp <= conf else ""
    return {"kind": str(r.get("kind") or "").strip()[:4], "rep": rp, "approx": bool(r.get("approx")) and cnt > 0, "sido": sido, "sgg": sgg,
            "sp": sp if sp in SP_OK else "기타", "breed": str(r.get("breed") or sp or "").strip()[:10],
            "cnt": cnt, "sero": sero if re.fullmatch(r"H\d{1,2}(N\d{1,2})?", sero) else "", "conf": conf,
            "nth": int(nth) if isinstance(nth, int) and 0 < nth < 1000 else None}


def press_candidates() -> list[dict]:
    """농식품부 가축전염병 보도자료 게시판 — 중계 서버가 393 경로를 허용해야 열린다(안 열리면 빈 목록)."""
    html = _get(PRESS_LIST_URL)
    if not html:
        print("::notice::농식품부 보도자료 게시판(393)을 열지 못함 — 중계 서버 허용 목록에 FMD-AI2/393 추가 필요")
        return []
    out = []
    for href, art_id, inner in PRESS_POST_RE.findall(html):
        title = re.sub(r"<[^>]+>|\s+", " ", inner).strip()
        if "조류인플루엔자" in title and re.search(r"발생|확진|확인", title) and not re.search(r"의심|저병원성", title):
            out.append({"id": "p" + art_id, "title": title, "url": urljoin(BASE, href), "kind": "농식품부 보도자료"})
    return out[:6]


def press_text(url: str) -> str:
    html = _get(url) or ""
    html = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", html, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", html)
    t = re.sub(r"&nbsp;|&#160;", " ", t)
    t = re.sub(r"\s+", " ", t)
    i = t.find("조류인플루엔자")
    return t[max(0, i - 600): i + 5000] if i >= 0 else ""


def news_text(item: dict) -> str:
    try:
        import fetch_industry_news as fin       # Google 뉴스 링크 풀기·본문 추출 재사용
        url = fin.decode_google_url(item.get("link", ""))
        return fin.article_text(url) if url else ""
    except Exception as exc:
        print(f"  본문 못 읽음: {type(exc).__name__}")
        return ""


def update_quick(out: dict, prev: dict) -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    now = datetime.now(KST)
    start = season_start(now)
    quick = [q for q in prev.get("quick", []) if q.get("conf", "") >= start]
    seen = list(prev.get("quick_seen", []))
    if not api_key:
        print("::notice::ANTHROPIC_API_KEY 없음 — 빠른 집계(quick)는 이전 값 유지")
    else:
        cands = []
        try:
            cands += press_candidates()
        except Exception as exc:
            print(f"::notice::보도자료 게시판 실패 — {exc}")
        for n in out.get("news", []):
            key = "n" + re.sub(r"\W", "", n.get("title", ""))[:40]
            cands.append({"id": key, "title": n.get("title", ""), "news": n, "kind": "언론 보도", "url": ""})
        for c in cands:
            if c["id"] in seen:
                continue
            if c.get("news"):
                pub = now
                try:
                    from email.utils import parsedate_to_datetime
                    pub = parsedate_to_datetime(c["news"].get("date", "")).astimezone(KST)
                except Exception:
                    pass
                text, link, src = news_text(c["news"]) or c["title"], c["news"].get("link", ""), c["news"].get("source") or "언론"
            else:
                pub, text, link, src = now, press_text(c["url"]), c["url"], "농식품부 보도자료"
            if not text:
                continue
            rows = ai_extract(c["title"], text, c["kind"], pub, api_key)
            if rows is None:
                continue
            seen.append(c["id"])
            for r in rows:
                q = clean_quick(r, pub, start)
                if not q or _sgg_key(q["sgg"]) not in re.sub(r"\s+", "", c["title"] + text):   # 글에 없는 지명은 버린다(지어낸 값 방지)
                    continue
                q.update({"src": src, "title": c["title"][:80], "link": link, "found": now.strftime("%Y-%m-%d %H:%M")})
                old = next((x for x in quick if same_farm(x, q)), None)
                if old:      # 같은 농장 — 빈칸만 채우고, 보도자료가 언론 보도보다 우선
                    for k in ("cnt", "sero", "kind", "nth", "rep", "approx"):
                        if not old.get(k) and q.get(k):
                            old[k] = q[k]
                    if src == "농식품부 보도자료" and old.get("src") != src:
                        old.update({"src": src, "title": q["title"], "link": link})
                else:
                    quick.append(q)
                    print(f"  빠른 집계 추가: {q['conf']} {q['sido']} {q['sgg']} {q['breed']} {q['cnt']}수 ({src})")
        seen = seen[-300:]
    # 농식품부 표에 들어온 농장은 빼고(표가 공식), 시즌이 바뀌면 지운다
    table = [f for f in out.get("farms", []) if f.get("conf", "") >= start]
    quick = [q for q in quick if not any(same_farm(q, f, 3) for f in table)]
    quick.sort(key=lambda q: q["conf"])
    out["quick"], out["quick_seen"] = quick, seen


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
    try:
        update_quick(out, prev)
        print(f"빠른 집계(보도 기준) {len(out.get('quick', []))}건")
    except Exception as exc:
        print(f"::warning::빠른 집계 실패, 이전 값 유지 — {exc}")
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
