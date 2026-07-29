#!/usr/bin/env python3
"""
KAPE 다봄 — 주간 계란 수급 정보 PDF 자동 수집·파싱
매주 월요일 GitHub Actions에서 실행 → egg_report/latest.json 저장

흐름:
  1. 목록 페이지에서 최신 게시글 boardNo + 제목 파악
  2. 게시글 상세에서 attachNo(PDF 첨부번호) 추출
  3. PDF 다운로드 → pdfplumber로 텍스트·표 추출
  4. 핵심 수치 파싱 → latest.json 저장
"""

import os, sys, re, json, io
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
import pdfplumber
from pypdf import PdfReader

KST = timezone(timedelta(hours=9))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Referer":    "https://www.ekapepia.com/",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

LIST_URL   = "https://www.ekapepia.com/v3/board/list.do"
DETAIL_URL = "https://www.ekapepia.com/v3/board/detail.do"
DL_URL     = "https://www.ekapepia.com/common/attachfile/attachfileDownload.do"


def get_latest_board():
    """목록 페이지에서 최신 게시글 boardNo·제목 반환"""
    params = {"boardInfoNo": "0159", "pageIndex": "1", "pageUnit": "9",
              "searchCondition": "SUBJECT", "searchKeyword": ""}
    r = requests.get(LIST_URL, headers=HEADERS, params=params, timeout=15)
    r.encoding = "utf-8"
    if r.status_code != 200:
        raise Exception(f"목록 HTTP {r.status_code}")

    # 게시글 번호 + 제목 추출 (첫 번째 = 최신)
    # 패턴: boardNo=XXXXXXXX 와 그 근처 제목
    board_nos = re.findall(r"boardNo=(\d{8})", r.text)
    titles    = re.findall(r"주간\s*계란\s*수급\s*정보[^\n<]{0,40}", r.text)

    if not board_nos:
        raise Exception("boardNo를 찾을 수 없음")

    board_no = board_nos[0]
    title    = titles[0].strip() if titles else f"주간 계란 수급 정보 (boardNo={board_no})"
    print(f"  최신 게시글: {title} (boardNo={board_no})")
    return board_no, title


def get_attach_no(board_no):
    """게시글 상세에서 attachNo 추출"""
    params = {
        "boardInfoNo": "0159", "boardNo": board_no,
        "boardSkin": "default", "dmlType": "SELECT",
        "pageIndex": "1", "pageUnit": "9",
    }
    r = requests.get(DETAIL_URL, headers=HEADERS, params=params, timeout=15)
    r.encoding = "utf-8"
    if r.status_code != 200:
        raise Exception(f"상세 HTTP {r.status_code}")

    attach_nos = re.findall(r"attachNo=(\d+)", r.text)
    if not attach_nos:
        raise Exception("attachNo를 찾을 수 없음")

    attach_no = attach_nos[0]
    print(f"  첨부 번호: {attach_no}")
    return attach_no


def download_pdf(attach_no):
    """PDF 바이너리 다운로드"""
    r = requests.get(DL_URL, headers=HEADERS,
                     params={"attachNo": attach_no}, timeout=30)
    if r.status_code != 200:
        raise Exception(f"PDF 다운로드 HTTP {r.status_code}")
    if len(r.content) < 1000:
        raise Exception(f"PDF 너무 작음 ({len(r.content)}bytes)")
    print(f"  PDF 다운로드: {len(r.content):,}bytes")
    return r.content


def parse_pdf(pdf_bytes):
    """
    pdfplumber로 텍스트·표 추출
    반환: { text, tables, summary }
    """
    result = {"text": "", "tables": [], "summary": {}}

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        full_text = ""
        for page in pdf.pages:
            t = page.extract_text() or ""
            full_text += t + "\n"

            # 표 추출
            for tbl in page.extract_tables():
                if tbl and len(tbl) > 1:
                    result["tables"].append(tbl)

        result["text"] = full_text
        print(f"  PDF 텍스트: {len(full_text)}자 / 표 {len(result['tables'])}개")

    # 핵심 수치 파싱
    text = result["text"]
    s = result["summary"]

    # 대상 기간 (예: 7월 20일 ~ 7월 26일)
    period = re.search(r"(\d+월\s*\d+일\s*[~∼]\s*\d+월?\s*\d+일)", text)
    if period:
        s["period"] = period.group(1).strip()

    # 보고서 차수 (예: 51차)
    seq = re.search(r"(\d+)\s*차", text)
    if seq:
        s["sequence"] = seq.group(1) + "차"

    # 숫자 패턴으로 핵심 지표 추출
    # 계란 산란율 (%)
    lay_rate = re.search(r"산란율[^\d]*(\d{1,3}\.?\d*)\s*%", text)
    if lay_rate:
        s["laying_rate"] = lay_rate.group(1) + "%"

    # 생산량 (백만개)
    prod = re.search(r"생산량[^\d]*(\d[\d,\.]+)\s*(백만개|천개|개)", text)
    if prod:
        s["production"] = prod.group(1) + prod.group(2)

    # 도매가격 (특란 기준, 원/30개 또는 원/10개)
    price = re.search(r"특란[^\d]*(\d[\d,]+)\s*원", text)
    if price:
        s["xl_price"] = price.group(1) + "원"

    # 재고 수준
    stock = re.search(r"재고[^\d]*(\d[\d,\.]+)", text)
    if stock:
        s["stock"] = stock.group(1)

    # 수급 판단 키워드
    for kw in ["공급 과잉", "공급과잉", "수급 안정", "수급안정", "공급 부족", "공급부족"]:
        if kw in text:
            s["supply_status"] = kw
            break

    # 전주 대비 키워드
    change = re.search(r"전주\s*대비\s*([^\n,]{2,20})", text)
    if change:
        s["vs_last_week"] = change.group(1).strip()

    return result


def save_result(board_no, attach_no, title, parsed, pdf_bytes):
    """latest.json + 원본 PDF 저장"""
    Path("egg_report").mkdir(exist_ok=True)

    now = datetime.now(KST)
    output = {
        "updated":   now.strftime("%Y-%m-%d %H:%M KST"),
        "title":     title,
        "board_no":  board_no,
        "attach_no": attach_no,
        "url":       f"https://www.ekapepia.com/v3/board/detail.do?boardInfoNo=0159&boardNo={board_no}&dmlType=SELECT",
        "summary":   parsed["summary"],
        "text":      parsed["text"][:4000],  # 최대 4000자
        "tables":    parsed["tables"][:5],   # 최대 5개 표
    }

    with open("egg_report/latest.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 원본 PDF 저장 (브리핑 생성 시 참조용)
    with open("egg_report/latest.pdf", "wb") as f:
        f.write(pdf_bytes)

    print(f"  ✅ egg_report/latest.json 저장 ({len(output['text'])}자)")
    print(f"  ✅ egg_report/latest.pdf 저장 ({len(pdf_bytes):,}bytes)")
    print(f"  요약: {output['summary']}")


def main():
    print("🥚 주간 계란 수급 정보 PDF 수집 시작...")

    try:
        board_no, title = get_latest_board()
    except Exception as e:
        print(f"  ❌ 목록 조회 실패: {e}")
        sys.exit(1)

    try:
        attach_no = get_attach_no(board_no)
    except Exception as e:
        print(f"  ❌ 첨부번호 조회 실패: {e}")
        sys.exit(1)

    try:
        pdf_bytes = download_pdf(attach_no)
    except Exception as e:
        print(f"  ❌ PDF 다운로드 실패: {e}")
        sys.exit(1)

    try:
        parsed = parse_pdf(pdf_bytes)
    except Exception as e:
        print(f"  ❌ PDF 파싱 실패: {e}")
        # 파싱 실패해도 raw 저장은 시도
        parsed = {"text": "", "tables": [], "summary": {"parse_error": str(e)}}

    save_result(board_no, attach_no, title, parsed, pdf_bytes)
    print(f"\n✅ 완료 — {title}")


if __name__ == "__main__":
    main()
