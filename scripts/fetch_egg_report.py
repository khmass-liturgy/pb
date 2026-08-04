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


def find_latest_board_no_from_list():
    """
    목록 페이지(boardInfoNo=0159)에서 실제 최신 게시글 번호를 추출.
    상세 페이지가 boardNo 파라미터를 무시하고 항상 최신글을 보여주는 것으로
    보였던 적이 있으나(과거 확인 시점), 그 동작에 계속 의존하면 사이트 쪽
    동작이 바뀌었을 때 같은 옛 게시글만 계속 받아오면서도 실패로 표시되지
    않는 문제가 있다. 목록에서 직접 번호를 뽑아 이 문제를 없앤다.
    """
    try:
        r = requests.get(LIST_URL, headers=HEADERS, params={
            "boardInfoNo": "0159", "pageIndex": "1", "pageUnit": "9",
            "searchCondition": "SUBJECT", "searchKeyword": "",
        }, timeout=20)
        r.encoding = "utf-8"
        html = r.text
        print(f"  목록 페이지 HTTP {r.status_code} / {len(html)}bytes")
    except Exception as e:
        print(f"  ⚠️ 목록 페이지 요청 실패: {e}")
        return []

    # 여러 CMS 렌더링 패턴을 폭넓게 시도 (사이트 구조 변경에 대비)
    # 0-패딩 없는 형태("boardNo":41038)도 있을 수 있어 자릿수를 4~8로 넓힌다
    patterns = [
        r'boardNo["\'=:\s]+0*(\d{4,8})',
        r"fn_view\(['\"]?0*(\d{4,8})",
        r"fn_select\(['\"]?0*(\d{4,8})",
        r'data-board-?no=["\']?0*(\d{4,8})',
        r'boardNo=0*(\d{4,8})',
        r"goDetail\(['\"]?0*(\d{4,8})",
        r"nttSn=0*(\d{4,8})",
        r"bbsSn=0*(\d{4,8})",
        r"pstSn=0*(\d{4,8})",
    ]
    found = []
    for pat in patterns:
        found += re.findall(pat, html)

    # 8자리로 0-패딩 통일 (요청 파라미터는 항상 8자리 형태를 씀)
    found = [f.zfill(8) for f in found if f.isdigit()]

    # 중복 제거, 숫자 큰 순(최신순) 정렬
    uniq = sorted(set(found), key=lambda x: int(x), reverse=True)
    if uniq:
        print(f"  목록에서 후보 {len(uniq)}개 발견 (최신순 상위 5개): {uniq[:5]}")
    else:
        print("  ⚠️ 목록 페이지에서 게시글 번호를 찾지 못함 (사이트 구조 확인 필요)")
        _diag_dump("목록 페이지", html)
    return uniq


def get_latest():
    """
    최신 게시글의 boardNo / attachNo / 제목을 반환.
    ① 목록 페이지에서 후보 번호를 뽑아 실제로 첨부파일이 걸린 것을 검증
    ② 실패 시 detail.do 에 존재할 수 없는 번호("00000000")를 보내본다.
       예전에 이 사이트는 boardNo 값과 무관하게 최신 글을 보여줬는데, 그 동작이
       아직 유효하면 이 방법으로도 최신 글을 받아온다. 다만 실제 게시글 번호를
       하드코딩해두면(과거의 00041017처럼) 그 가정이 깨졌을 때도 조용히 같은
       옛날 글을 계속 돌려주므로, 일부러 존재할 수 없는 번호를 써서 가정이
       깨졌을 경우 눈에 띄게 실패하도록 한다.
    """
    for board_no in find_latest_board_no_from_list()[:5]:
        attach_no, title, _ = fetch_detail(board_no)
        if attach_no:
            print(f"  ✅ 목록 기반 확인: boardNo={board_no}, attachNo={attach_no}, 제목={title}")
            return board_no, attach_no, title
        print(f"  boardNo={board_no}: 첨부파일 없음 → 다음 후보")

    print("  ⚠️ 목록 기반 탐색 실패 → 폴백(boardNo 무시 동작 가정) 시도")
    attach_no, title, html = fetch_detail("00000000")
    board_no = ""
    m = re.search(r'name="boardNo"[^>]*value="(\d+)"', html)
    if m:
        board_no = m.group(1)
    print(f"  boardNo={board_no or '(추출 실패)'}, attachNo={attach_no or '(없음)'}, 제목={title}")

    if not attach_no:
        _diag_dump("상세 페이지(boardNo=00000000)", html)
        # 마지막 시도: 예전에 실제로 통했던 특정 번호로도 한 번 확인
        # (이 번호가 여전히 통하면 "게시글이 그대로"라는 뜻, 이것마저 실패하면
        #  detail.do 자체 구조가 바뀐 것)
        attach_no2, title2, html2 = fetch_detail("00041017")
        print(f"  참고용 재확인(boardNo=00041017): attachNo={attach_no2 or '(없음)'}, 제목={title2}")
        if not attach_no2:
            _diag_dump("상세 페이지(boardNo=00041017, 참고용)", html2)

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
