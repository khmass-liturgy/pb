#!/usr/bin/env python3
"""
KAPE 다봄 — 주간 계란 수급 정보 PDF 자동 수집·파싱

확인된 HTML 구조:
  attachNo: href="/common/attachfile/attachfileDownload.do?attachNo=00089200"
  제목:     data-value="7월 20일 주간 계란 수급 정보(51차).pdf"
  boardNo:  <input type="hidden" name="boardNo" id="boardNo" value="00041017"/>
"""

import os, sys, re, json, io
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
import pdfplumber

# Playwright는 목록 페이지가 자바스크립트로 렌더링되는 경우에만 필요한
# 최후 수단이라 선택적으로 불러온다 (설치 안 돼 있어도 나머지는 동작해야 함).
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

KST = timezone(timedelta(hours=9))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Referer":    "https://www.ekapepia.com/",
    "Accept":     "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

BASE        = "https://www.ekapepia.com"
DETAIL_URL  = f"{BASE}/v3/board/detail.do"
DL_URL      = f"{BASE}/common/attachfile/attachfileDownload.do"


LIST_URL = f"{BASE}/v3/board/list.do"


def fetch_detail(board_no):
    """지정한 boardNo의 상세 페이지에서 attachNo / 제목 추출 (없으면 attach_no="")"""
    r = requests.get(DETAIL_URL, headers=HEADERS, params={
        "boardInfoNo": "0159", "boardNo": board_no,
        "boardSkin": "default", "dmlType": "SELECT",
        "pageIndex": "1", "pageUnit": "9",
    }, timeout=20)
    r.encoding = "utf-8"
    html = r.text

    attach_no = ""
    m = re.search(r'attachfileDownload\.do\?attachNo=(\d{8})(?:&#034;|")', html)
    if m:
        attach_no = m.group(1)

    title = ""
    m = re.search(r'data-value="([^"]*주간\s*계란[^"]*\.pdf)"', html)
    if m:
        title = m.group(1).replace(".pdf", "").strip()
    elif re.search(r'<title>([^<]*주간[^<]*계란[^<]*)</title>', html):
        title = re.search(r'<title>([^<]*주간[^<]*계란[^<]*)</title>', html).group(1).strip()

    return attach_no, title, html


def _diag_dump(label, html):
    """진단용: 실패 시 로그에서 바로 구조를 알 수 있도록 핵심 단서를 찍는다."""
    print(f"  ── [{label}] 진단 정보 ──")
    print(f"     길이: {len(html)}bytes")
    print(f"     '계란' 포함: {'계란' in html} / '수급' 포함: {'수급' in html}")
    print(f"     'attachfileDownload' 포함: {'attachfileDownload' in html}")
    print(f"     'boardNo' 포함: {'boardNo' in html} (등장 {html.count('boardNo')}회)")

    # boardNo가 있는데도 정규식이 못 잡았을 경우를 위해 등장 지점 주변을 그대로 출력
    if "boardNo" in html:
        idx = 0
        n = 0
        while True:
            idx = html.find("boardNo", idx)
            if idx < 0 or n >= 8:
                break
            print(f"     boardNo 주변[{n}]: {html[max(0,idx-20):idx+60]!r}")
            idx += 7
            n += 1

    for kw in ["nttSn", "bbsSn", "pstSn", "seq=", "postId", "artclView", "fn_view", "fn_select", "goDetail"]:
        if kw in html:
            print(f"     '{kw}' 등장 {html.count(kw)}회 — 예시: {html[html.find(kw):html.find(kw)+80]!r}")

    # <title> 태그
    m = re.search(r"<title>([^<]*)</title>", html)
    if m:
        print(f"     <title>: {m.group(1).strip()[:80]}")
    print(f"     앞부분 500자: {html[:500]!r}")
    print(f"     뒷부분 500자: {html[-500:]!r}")


def _extract_board_nos(html):
    """HTML/JSON 텍스트에서 게시글 번호 후보를 폭넓게 추출 (8자리로 0-패딩 통일)"""
    patterns = [
        r'boardNo["\'=:\s]+0*(\d{4,8})',
        r"fn_view\(['\"]?0*(\d{4,8})",
        r"fn_select\(['\"]?0*(\d{4,8})",
        r'data-board-?no=["\']?0*(\d{4,8})',
        r'boardNo=0*(\d{4,8})',
        r"goDetail\(['\"]?0*(\d{4,8})",
        r"goBoardView\(['\"]?0*(\d{4,8})",
        r"nttSn=0*(\d{4,8})",
        r"bbsSn=0*(\d{4,8})",
        r"pstSn=0*(\d{4,8})",
    ]
    found = []
    for pat in patterns:
        found += re.findall(pat, html)
    found = [f.zfill(8) for f in found if f.isdigit()]
    return sorted(set(found), key=lambda x: int(x), reverse=True)


def find_latest_board_no_from_list():
    """
    목록 페이지(boardInfoNo=0159)에서 실제 최신 게시글 번호를 추출.

    확인 결과 이 목록은 처음 응답에 목록 항목이 없고(자바스크립트가 별도
    데이터를 받아와 화면에 채워 넣는 방식), goBoardView(boardNo) 같은 범용
    함수 정의만 있다. 실제 항목 데이터는 같은 URL을 AJAX로(XHR 헤더 또는
    POST, dmlType=LIST 등) 호출했을 때 반환되는 것으로 추정 — egovframe류
    게시판에서 흔한 구조. 여러 호출 방식을 순서대로 시도한다.
    """
    base_params = {
        "boardInfoNo": "0159", "pageIndex": "1", "pageUnit": "9",
        "searchCondition": "SUBJECT", "searchKeyword": "",
    }
    attempts = [
        ("GET 기본",            "GET",  base_params, {}),
        ("GET + XHR 헤더",       "GET",  base_params, {"X-Requested-With": "XMLHttpRequest"}),
        ("GET + dmlType=LIST",   "GET",  {**base_params, "dmlType": "LIST"}, {"X-Requested-With": "XMLHttpRequest"}),
        ("POST + dmlType=LIST",  "POST", {**base_params, "dmlType": "LIST"}, {"X-Requested-With": "XMLHttpRequest"}),
        ("POST 기본",            "POST", base_params, {"X-Requested-With": "XMLHttpRequest"}),
    ]

    last_html = ""
    for label, method, params, extra_headers in attempts:
        try:
            hdrs = {**HEADERS, **extra_headers}
            if method == "GET":
                r = requests.get(LIST_URL, headers=hdrs, params=params, timeout=20)
            else:
                r = requests.post(LIST_URL, headers=hdrs, data=params, timeout=20)
            r.encoding = "utf-8"
            html = r.text
            last_html = html
            uniq = _extract_board_nos(html)
            print(f"  [{label}] HTTP {r.status_code} / {len(html)}bytes / 후보 {len(uniq)}개")
            if uniq:
                print(f"    → 최신순 상위 5개: {uniq[:5]}")
                return uniq
        except Exception as e:
            print(f"  [{label}] 요청 실패: {e}")

    print("  ⚠️ 모든 방식에서 게시글 번호를 찾지 못함 (사이트 구조 확인 필요)")
    if last_html:
        _diag_dump("목록 페이지(마지막 시도)", last_html)
    return []


def find_latest_board_no_via_browser():
    """
    목록 페이지는 처음 HTML에 항목이 없고 자바스크립트가 별도 데이터를 받아와
    채워 넣는 방식으로 확인됐다(정적 요청 여러 방식을 다 시도해도 항목별
    게시글 번호가 아예 존재하지 않았음). requests는 자바스크립트를 실행하지
    못하므로 근본적으로 이 방식으로는 얻을 수 없는 데이터다.

    실제 브라우저(headless Chromium)로 페이지를 열어 자바스크립트를 실행시킨 뒤,
    ① 페이지가 내부적으로 호출하는 데이터 응답(XHR/fetch)을 가로채서 우선 확인하고
    ② 그래도 없으면 자바스크립트 실행이 끝난 최종 DOM에서 추출한다.
    """
    if not HAS_PLAYWRIGHT:
        print("  ⚠️ playwright 미설치 — 브라우저 탐색 건너뜀")
        return []

    captured_texts = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=HEADERS["User-Agent"])

            def on_response(resp):
                try:
                    if resp.status != 200:
                        return
                    ctype = resp.headers.get("content-type", "")
                    if "json" in ctype or "xml" in ctype or "text" in ctype:
                        body = resp.text()
                        if "boardNo" in body or "계란" in body:
                            captured_texts.append((resp.url, body))
                except Exception:
                    pass  # 응답 스트림이 이미 소비된 경우 등, 진단용이라 무시

            page.on("response", on_response)
            page.goto(LIST_URL + "?boardInfoNo=0159", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(1500)  # 지연 렌더링 대비 여유
            dom_html = page.content()
            browser.close()
    except Exception as e:
        print(f"  ⚠️ 브라우저 탐색 실패: {e}")
        return []

    print(f"  브라우저: 가로챈 응답 {len(captured_texts)}개, 최종 DOM {len(dom_html)}bytes")

    # ① 페이지가 자체적으로 호출한 데이터 응답에서 우선 추출
    for url, body in captured_texts:
        nos = _extract_board_nos(body)
        if nos:
            print(f"  ✅ 네트워크 응답에서 발견 ({url[:70]}): {nos[:5]}")
            return nos

    # ② 최종 렌더링된 DOM에서 추출 (버튼 onclick, data 속성 등)
    nos = _extract_board_nos(dom_html)
    if nos:
        print(f"  ✅ 렌더링된 DOM에서 발견: {nos[:5]}")
        return nos

    print("  ⚠️ 브라우저로도 게시글 번호를 찾지 못함")
    _diag_dump("브라우저 렌더링 결과", dom_html)
    return []


def get_latest():
    """
    최신 게시글의 boardNo / attachNo / 제목을 반환.
    ① 정적 요청(여러 방식)으로 목록에서 후보를 찾아본다 — 가장 빠름
    ② 실패하면 실제 브라우저로 자바스크립트를 실행해 찾는다 — 근본 해결책
    ③ 그래도 실패하면 예전 방식(존재 불가능한 번호로 질의)까지 시도하되,
       모두 실패하면 예외로 죽이지 않고 빈 값을 반환해 main()에서
       "이전 데이터 유지 + stale 표시"로 안전하게 처리되게 한다.
    """
    candidates = find_latest_board_no_from_list()
    if not candidates:
        print("  → 정적 탐색 실패, 브라우저 탐색으로 전환")
        candidates = find_latest_board_no_via_browser()

    for board_no in candidates[:5]:
        attach_no, title, _ = fetch_detail(board_no)
        if attach_no:
            print(f"  ✅ boardNo={board_no}, attachNo={attach_no}, 제목={title}")
            return board_no, attach_no, title
        print(f"  boardNo={board_no}: 첨부파일 없음 → 다음 후보")

    print("  ⚠️ 목록 기반 탐색 전부 실패 → 마지막 폴백(boardNo 무시 동작 가정) 시도")
    attach_no, title, html = fetch_detail("00000000")
    board_no = ""
    m = re.search(r'name="boardNo"[^>]*value="(\d+)"', html)
    if m:
        board_no = m.group(1)
    print(f"  boardNo={board_no or '(추출 실패)'}, attachNo={attach_no or '(없음)'}, 제목={title}")

    if not attach_no:
        _diag_dump("상세 페이지(boardNo=00000000)", html)

    return board_no, attach_no, title


def download_pdf(attach_no):
    """PDF 다운로드 — attachNo 8자리 문자열 그대로"""
    dl_headers = {
        **HEADERS,
        "Accept": "application/pdf,application/octet-stream,*/*",
    }
    r = requests.get(DL_URL, headers=dl_headers,
                     params={"attachNo": attach_no}, timeout=30)
    ct = r.headers.get("Content-Type", "")
    print(f"  HTTP {r.status_code} / {len(r.content):,}bytes / {ct}")
    if r.status_code != 200:
        raise Exception(f"HTTP {r.status_code}")
    if len(r.content) < 1000:
        print(f"  응답 내용: {r.text[:200]}")
        raise Exception(f"응답 너무 작음 ({len(r.content)}bytes)")
    return r.content


def parse_pdf(pdf_bytes):
    result = {"text": "", "tables": [], "summary": {}, "sections": []}
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += (page.extract_text() or "") + "\n"
                for tbl in page.extract_tables():
                    if tbl and len(tbl) > 1:
                        result["tables"].append(tbl)
            result["text"] = full_text
            print(f"  파싱: {len(full_text)}자 / 표 {len(result['tables'])}개")
    except Exception as e:
        print(f"  ⚠️ pdfplumber 실패: {e}")
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(pdf_bytes))
            result["text"] = "\n".join(p.extract_text() or "" for p in reader.pages)
            print(f"  pypdf 파싱: {len(result['text'])}자")
        except Exception as e2:
            print(f"  ⚠️ pypdf도 실패: {e2}")

    text = result["text"]
    s    = result["summary"]

    # ── 섹션별 <요약> 블록 추출 ─────────────────────────────────────────────
    # PDF 구조: "1 생산 동향" ... "<요약>" ... 내용 ... "2 유통 동향" ... "<요약>" ...
    sections = []
    # 섹션 헤더 위치 찾기 (숫자 + 한글 제목)
    header_pat = re.compile(r"(?:^|\n)\s*([1-9])\s+([가-힣][가-힣\s·]{1,15}동향|[가-힣][가-힣\s·]{1,15}현황|[가-힣][가-힣\s·]{1,15}전망)")
    headers = [(m.start(), m.group(1), m.group(2).strip()) for m in header_pat.finditer(text)]

    for i, (pos, num, title) in enumerate(headers):
        end = headers[i+1][0] if i+1 < len(headers) else len(text)
        block = text[pos:end]

        # 이 섹션 안의 <요약> 내용 추출
        m = re.search(r"<\s*요\s*약\s*>([\s\S]*?)(?=\n\s*[1-9]\s+[가-힣]|$)", block)
        if m:
            body = m.group(1).strip()
            # 줄바꿈 정리 (PDF 줄바꿈 → 공백, 불릿은 유지)
            body = re.sub(r"\n\s*", " ", body)
            body = re.sub(r"\s{2,}", " ", body).strip()
            if len(body) > 20:
                sections.append({"no": num, "title": title, "summary": body})

    # <요약> 헤더 없이 전체에서 찾기 (fallback)
    if not sections:
        for m in re.finditer(r"<\s*요\s*약\s*>([\s\S]{30,1200}?)(?=<\s*요\s*약\s*>|\n\s*[1-9]\s+[가-힣]|$)", text):
            body = re.sub(r"\n\s*", " ", m.group(1).strip())
            body = re.sub(r"\s{2,}", " ", body).strip()
            sections.append({"no": str(len(sections)+1), "title": "요약", "summary": body})

    result["sections"] = sections
    print(f"  요약 섹션 {len(sections)}개 추출")
    for sec in sections:
        print(f"    [{sec['no']}] {sec['title']}: {sec['summary'][:60]}...")

    # ── 메타 정보 ─────────────────────────────────────────────────────────
    period = re.search(r"(\d+월\s*\d+일\s*[~∼～]\s*\d+월?\s*\d+일)", text)
    if period: s["period"] = period.group(1).strip()

    seq = re.search(r"(\d+)\s*차", text)
    if seq: s["sequence"] = seq.group(1) + "차"

    # 수급 상황 키워드 (요약문 안에서 우선 탐색)
    summary_text = " ".join(sec["summary"] for sec in sections) or text
    for kw in ["강보합","약보합","보합","강세","약세","체화","공급 과잉","공급과잉",
               "수급 안정","수급안정","공급 부족","공급부족"]:
        if kw in summary_text:
            s["supply_status"] = kw
            break

    return result


def load_previous():
    """이전 latest.json 로드 (없으면 None)"""
    p = Path("egg_report/latest.json")
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def save(board_no, attach_no, title, parsed, pdf_bytes, stale_weeks):
    Path("egg_report").mkdir(exist_ok=True)
    now = datetime.now(KST)
    out = {
        "updated":     now.strftime("%Y-%m-%d %H:%M KST"),
        "title":       title,
        "board_no":    board_no,
        "attach_no":   attach_no,
        "url":         f"{BASE}/v3/board/detail.do?boardInfoNo=0159&boardNo={board_no}&dmlType=SELECT",
        "summary":     parsed["summary"],
        "sections":    parsed.get("sections", []),
        "text":        parsed["text"][:3000],
        "tables":      parsed["tables"][:3],
        "stale_weeks": stale_weeks,  # 직전 실행과 board_no 가 같았던 연속 횟수
    }
    with open("egg_report/latest.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    with open("egg_report/latest.pdf", "wb") as f:
        f.write(pdf_bytes)
    print(f"  ✅ latest.json + latest.pdf 저장")
    print(f"  요약: {out['summary']}")


def main():
    print("🥚 주간 계란 수급 정보 수집 시작\n")

    prev = load_previous()
    prev_board_no = (prev or {}).get("board_no", "")

    print("📋 게시글 정보 조회...")
    board_no, attach_no, title = get_latest()

    if not attach_no:
        print("❌ attachNo 미발견 — 사이트 구조가 바뀌었을 수 있습니다.")
        # 완전히 빈 손으로 끝내지 않는다: 이전에 성공한 데이터가 있으면
        # 그대로 유지해 화면에는 계속 최신(구) 데이터가 뜨게 하고,
        # stale 표시를 남겨서 문제가 있다는 건 알 수 있게 한다.
        if prev:
            print("  ⚡ 이전 데이터 유지 (Actions 실패로는 표시되지만 화면은 정상 노출)")
            prev["stale_weeks"] = (prev or {}).get("stale_weeks", 0) + 1
            prev["updated"] = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST") + " (수집 실패, 이전 데이터)"
            Path("egg_report").mkdir(exist_ok=True)
            with open("egg_report/latest.json", "w", encoding="utf-8") as f:
                json.dump(prev, f, ensure_ascii=False, indent=2)
        sys.exit(1)

    # 직전 실행과 같은 글이 계속 나오면(=새 글 감지 실패 가능성) 연속 횟수를 누적해
    # 경고로 남긴다. 매주 새 글이 올라오므로 정상이라면 이 값은 계속 0이어야 한다.
    if board_no and board_no == prev_board_no:
        stale_weeks = (prev or {}).get("stale_weeks", 0) + 1
        print(f"  ⚠️ 직전 실행과 동일한 게시글(boardNo={board_no})이 {stale_weeks}회 연속 감지됨")
        if stale_weeks >= 2:
            print("  ⚠️ 새 게시글 감지 로직을 점검해야 할 수 있습니다 (사이트에 새 글이 없는지 직접 확인 권장).")
    else:
        stale_weeks = 0

    print(f"\n📥 PDF 다운로드 (attachNo={attach_no})...")
    pdf_bytes = download_pdf(attach_no)

    print("\n📄 PDF 파싱...")
    parsed = parse_pdf(pdf_bytes)
    print(f"  텍스트 앞부분:\n{parsed['text'][:400]}")

    print("\n💾 저장...")
    save(board_no, attach_no, title, parsed, pdf_bytes, stale_weeks)
    print(f"\n✅ 완료 — {title}")


if __name__ == "__main__":
    main()
