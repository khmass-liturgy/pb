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


def get_latest():
    """상세 페이지에서 boardNo / attachNo / 제목 추출"""
    r = requests.get(DETAIL_URL, headers=HEADERS, params={
        "boardInfoNo": "0159", "boardNo": "00041017",
        "boardSkin": "default", "dmlType": "SELECT",
        "pageIndex": "1", "pageUnit": "9",
    }, timeout=20)
    r.encoding = "utf-8"
    html = r.text
    print(f"  상세 HTTP {r.status_code} / {len(html)}bytes")

    # boardNo
    board_no = ""
    m = re.search(r'name="boardNo"[^>]*value="(\d+)"', html)
    if m: board_no = m.group(1)

    # attachNo (8자리, 다운로드 href에서)
    attach_no = ""
    m = re.search(r'attachfileDownload\.do\?attachNo=(\d{8})"', html)
    if m:
        attach_no = m.group(1)
    else:
        # &#034; 엔티티 버전
        m = re.search(r'attachfileDownload\.do\?attachNo=(\d{8})&#034;', html)
        if m: attach_no = m.group(1)

    # 제목 (data-value="7월 20일 주간 계란 수급 정보(51차).pdf")
    title = ""
    m = re.search(r'data-value="([^"]*주간\s*계란[^"]*\.pdf)"', html)
    if m:
        title = m.group(1).replace(".pdf", "").strip()
    else:
        # fallback: <title> 태그
        m = re.search(r'<title>([^<]*주간[^<]*계란[^<]*)</title>', html)
        if m: title = m.group(1).strip()

    print(f"  boardNo={board_no}, attachNo={attach_no}, 제목={title}")
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
    result = {"text": "", "tables": [], "summary": {}}
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

    period = re.search(r"(\d+월\s*\d+일\s*[~∼～]\s*\d+월?\s*\d+일)", text)
    if period: s["period"] = period.group(1).strip()

    seq = re.search(r"(\d+)\s*차", text)
    if seq: s["sequence"] = seq.group(1) + "차"

    lay = re.search(r"산란율[^\d]*([\d.]+)\s*%", text)
    if lay: s["laying_rate"] = lay.group(1) + "%"

    prod = re.search(r"생산량[^\d]*([\d,]+)\s*(백만개|천개)", text)
    if prod: s["production"] = prod.group(1) + prod.group(2)

    price = re.search(r"특란[^\d]*([\d,]+)\s*원", text)
    if price: s["xl_price_won"] = price.group(1) + "원"

    for kw in ["공급 과잉","공급과잉","수급 안정","수급안정","공급 부족","공급부족"]:
        if kw in text:
            s["supply_status"] = kw
            break

    chg = re.search(r"전주\s*대비\s*([^\n,。]{2,20})", text)
    if chg: s["vs_last_week"] = chg.group(1).strip()

    return result


def save(board_no, attach_no, title, parsed, pdf_bytes):
    Path("egg_report").mkdir(exist_ok=True)
    now = datetime.now(KST)
    out = {
        "updated":   now.strftime("%Y-%m-%d %H:%M KST"),
        "title":     title,
        "board_no":  board_no,
        "attach_no": attach_no,
        "url":       f"{BASE}/v3/board/detail.do?boardInfoNo=0159&boardNo={board_no}&dmlType=SELECT",
        "summary":   parsed["summary"],
        "text":      parsed["text"][:5000],
        "tables":    parsed["tables"][:5],
    }
    with open("egg_report/latest.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    with open("egg_report/latest.pdf", "wb") as f:
        f.write(pdf_bytes)
    print(f"  ✅ latest.json + latest.pdf 저장")
    print(f"  요약: {out['summary']}")


def main():
    print("🥚 주간 계란 수급 정보 수집 시작\n")

    print("📋 게시글 정보 조회...")
    board_no, attach_no, title = get_latest()

    if not attach_no:
        print("❌ attachNo 미발견")
        sys.exit(1)

    print(f"\n📥 PDF 다운로드 (attachNo={attach_no})...")
    pdf_bytes = download_pdf(attach_no)

    print("\n📄 PDF 파싱...")
    parsed = parse_pdf(pdf_bytes)
    print(f"  텍스트 앞부분:\n{parsed['text'][:400]}")

    print("\n💾 저장...")
    save(board_no, attach_no, title, parsed, pdf_bytes)
    print(f"\n✅ 완료 — {title}")


if __name__ == "__main__":
    main()
