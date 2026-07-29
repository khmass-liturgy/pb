#!/usr/bin/env python3
"""
KAPE 다봄 — 주간 계란 수급 정보 PDF 자동 수집·파싱

확인된 동작:
  - 목록/상세 페이지가 boardNo 무관하게 최신 게시글을 고정 반환
  - boardNo=00041017, attachNo=00089200 (8자리 0-padded 문자열)
  - PDF 다운로드: attachNo를 원본 문자열로 전달해야 함
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
    "Accept":     "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

DETAIL_URL = "https://www.ekapepia.com/v3/board/detail.do"
DL_URL     = "https://www.ekapepia.com/common/attachfile/attachfileDownload.do"


def get_latest():
    """
    상세 페이지는 boardNo 무관하게 항상 최신 게시글 반환.
    boardNo=0 으로 요청해도 최신 글이 나옴.
    attachNo 원본 문자열(0-padded) 추출.
    """
    r = requests.get(DETAIL_URL, headers=HEADERS, params={
        "boardInfoNo": "0159", "boardNo": "00000000",
        "boardSkin": "default", "dmlType": "SELECT",
        "pageIndex": "1", "pageUnit": "9",
    }, timeout=20)
    r.encoding = "utf-8"
    html = r.text
    print(f"  상세 페이지 HTTP {r.status_code} / {len(html)}bytes")

    # attachNo: 8자리 숫자 문자열 (0-padded)
    # 패턴 예: attachNo=00089200  또는  attachNo":"00089200"
    attach_nos = re.findall(r'attachNo[="\s:]+(\d{8})', html)
    # 제목: "7월 20일 주간 계란 수급 정보(51차)" 형태
    titles = re.findall(r'[1-9]\d*월\s*\d+일\s*주간\s*계란\s*수급[^\n<"]{0,40}', html)
    # boardNo 추출
    board_nos = re.findall(r'boardNo[="\s:]+(\d{8})', html)

    print(f"  attachNo 후보: {attach_nos[:3]}")
    print(f"  boardNo 후보:  {board_nos[:3]}")
    print(f"  제목 후보:     {titles[:3]}")

    if not attach_nos:
        # 6자리도 시도
        attach_nos = re.findall(r'attachNo[="\s:]+0*(\d{5,8})', html)
        # 0-pad 복원
        attach_nos = [n.zfill(8) for n in attach_nos]
        print(f"  attachNo (재시도): {attach_nos[:3]}")

    if not attach_nos:
        # 전체 HTML에서 다운로드 링크 직접 탐색
        dl_links = re.findall(r'attachfileDownload[^"\']*attachNo[=&]([^"\'&\s]+)', html)
        print(f"  다운로드 링크 attachNo: {dl_links[:3]}")
        attach_nos = dl_links

    attach_no = attach_nos[0] if attach_nos else None
    board_no  = board_nos[0]  if board_nos  else "00041017"
    title     = titles[0].strip() if titles else "주간 계란 수급 정보"

    return board_no, attach_no, title, html


def download_pdf(attach_no_str):
    """attachNo를 원본 문자열 그대로 전달"""
    print(f"  다운로드 URL: {DL_URL}?attachNo={attach_no_str}")
    r = requests.get(DL_URL, headers={
        **HEADERS,
        "Accept": "application/pdf,*/*",
    }, params={"attachNo": attach_no_str}, timeout=30)

    print(f"  HTTP {r.status_code} / {len(r.content)}bytes")
    print(f"  Content-Type: {r.headers.get('Content-Type','')}")

    if r.status_code != 200:
        raise Exception(f"HTTP {r.status_code}")
    if len(r.content) < 500:
        # 응답 내용 확인
        print(f"  응답 내용: {r.text[:300]}")
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
            print(f"  PDF 파싱: {len(full_text)}자 / 표 {len(result['tables'])}개")
            print(f"  텍스트 앞부분:\n{full_text[:500]}")
    except Exception as e:
        print(f"  ⚠️ pdfplumber 실패: {e}")
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(pdf_bytes))
            full_text = "\n".join(p.extract_text() or "" for p in reader.pages)
            result["text"] = full_text
            print(f"  pypdf 파싱: {len(full_text)}자")
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
        "url":       f"https://www.ekapepia.com/v3/board/detail.do?boardInfoNo=0159&boardNo={board_no}&dmlType=SELECT",
        "summary":   parsed["summary"],
        "text":      parsed["text"][:5000],
        "tables":    parsed["tables"][:5],
    }
    with open("egg_report/latest.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    with open("egg_report/latest.pdf", "wb") as f:
        f.write(pdf_bytes)
    print(f"\n✅ 저장 완료: latest.json ({len(parsed['text'])}자) + latest.pdf ({len(pdf_bytes):,}bytes)")
    print(f"   요약: {out['summary']}")


def main():
    print("🥚 주간 계란 수급 정보 수집 시작...\n")

    print("📋 최신 게시글 정보 조회...")
    try:
        board_no, attach_no, title, html = get_latest()
    except Exception as e:
        print(f"❌ 게시글 조회 실패: {e}")
        sys.exit(1)

    if not attach_no:
        print("\n⚠️ attachNo 미발견. HTML 패턴 확인:")
        # attachfile 관련 텍스트 출력
        for m in re.finditer(r'.{0,50}attach.{0,50}', html, re.I):
            print(f"  {m.group()}")
        sys.exit(1)

    print(f"\n  ✅ boardNo={board_no}, attachNo={attach_no}, 제목={title}")

    print(f"\n📥 PDF 다운로드...")
    try:
        pdf_bytes = download_pdf(attach_no)
    except Exception as e:
        print(f"❌ 다운로드 실패: {e}")
        sys.exit(1)

    print("\n📄 PDF 파싱...")
    parsed = parse_pdf(pdf_bytes)

    print("\n💾 저장...")
    save(board_no, attach_no, title, parsed, pdf_bytes)
    print(f"\n✅ 완료 — {title}")


if __name__ == "__main__":
    main()
