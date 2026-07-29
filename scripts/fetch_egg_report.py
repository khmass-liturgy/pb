#!/usr/bin/env python3
"""
KAPE 다봄 — 주간 계란 수급 정보 PDF 자동 수집·파싱
흐름:
  1. 목록 페이지(boardInfoNo=0159)에서 최신 boardNo + attachNo 탐색
  2. 없으면 알려진 최신 boardNo에서 순차 탐색
  3. PDF 다운로드 → pdfplumber 파싱 → egg_report/latest.json 저장
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

LIST_URL   = "https://www.ekapepia.com/v3/board/list.do"
DETAIL_URL = "https://www.ekapepia.com/v3/board/detail.do"
DL_URL     = "https://www.ekapepia.com/common/attachfile/attachfileDownload.do"

# 알려진 최신 boardNo (2026-07-28 기준: 51차 = 00041017)
# 매주 약 2~3씩 증가하는 패턴
KNOWN_LATEST = 41017


def get_html(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params, timeout=20)
    r.encoding = "utf-8"
    if r.status_code != 200:
        raise Exception(f"HTTP {r.status_code}")
    return r.text


def find_latest_from_list():
    """목록 페이지에서 boardNo + attachNo 탐색"""
    html = get_html(LIST_URL, {
        "boardInfoNo": "0159", "pageIndex": "1", "pageUnit": "9",
        "searchCondition": "SUBJECT", "searchKeyword": "",
    })
    print(f"  목록 HTML ({len(html)}bytes) 앞부분:")
    print(html[:2000])

    # boardNo 패턴: 8자리 숫자
    board_nos = re.findall(r'boardNo[="\s]+0*(\d{5,8})', html)
    board_nos = [int(n) for n in board_nos if int(n) > 10000]

    # 첨부파일 번호
    attach_nos = re.findall(r'attachNo[="\s]+(\d+)', html)

    # 제목 추출
    titles = re.findall(r'주간\s*계란\s*수급[^\n<"]{0,60}', html)

    print(f"  boardNo 후보: {board_nos[:5]}")
    print(f"  attachNo 후보: {attach_nos[:5]}")
    print(f"  제목 후보: {titles[:3]}")

    if board_nos:
        return max(board_nos), titles[0].strip() if titles else ""
    return None, ""


def find_attach_from_detail(board_no):
    """상세 페이지에서 attachNo + 제목 추출"""
    html = get_html(DETAIL_URL, {
        "boardInfoNo": "0159", "boardNo": f"{board_no:08d}",
        "boardSkin": "default", "dmlType": "SELECT",
        "pageIndex": "1", "pageUnit": "9",
    })

    # attachNo
    attach_nos = re.findall(r'attachNo=(\d+)', html)
    # 제목
    titles = re.findall(r'주간\s*계란\s*수급[^\n<"]{0,60}', html)
    title  = titles[0].strip() if titles else f"주간 계란 수급 정보 ({board_no})"

    print(f"  boardNo={board_no} → attachNo 후보: {attach_nos[:3]}, 제목: {title}")

    if attach_nos:
        return int(attach_nos[0]), title
    return None, title


def probe_board_sequential(start_no, max_probe=10):
    """start_no부터 순방향으로 유효한 최신 게시글 탐색"""
    best_no   = None
    best_attach = None
    best_title  = ""

    for offset in range(max_probe, -1, -1):
        board_no = start_no + offset
        try:
            attach_no, title = find_attach_from_detail(board_no)
            if attach_no:
                best_no     = board_no
                best_attach = attach_no
                best_title  = title
                print(f"  ✅ 최신 boardNo={board_no}, attachNo={attach_no}")
                break
        except Exception as e:
            print(f"  boardNo={board_no}: {e}")
            continue

    return best_no, best_attach, best_title


def download_pdf(attach_no):
    r = requests.get(DL_URL, headers=HEADERS,
                     params={"attachNo": attach_no}, timeout=30)
    if r.status_code != 200:
        raise Exception(f"PDF HTTP {r.status_code}")
    if len(r.content) < 500:
        raise Exception(f"PDF 너무 작음 ({len(r.content)}bytes)")
    print(f"  PDF 다운로드: {len(r.content):,}bytes")
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
    except Exception as e:
        print(f"  ⚠️ pdfplumber 실패: {e}, pypdf 시도...")
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

    # 대상 기간
    period = re.search(r"(\d+월\s*\d+일\s*[~∼～]\s*\d+월?\s*\d+일)", text)
    if period: s["period"] = period.group(1).strip()

    # 차수
    seq = re.search(r"(\d+)\s*차", text)
    if seq: s["sequence"] = seq.group(1) + "차"

    # 산란율
    lay = re.search(r"산란율[^\d]*(\d{1,3}[.,]\d)\s*%", text)
    if lay: s["laying_rate"] = lay.group(1) + "%"

    # 생산량
    prod = re.search(r"생산량[^\d]*([\d,]+)\s*(백만개|천개)", text)
    if prod: s["production"] = prod.group(1) + prod.group(2)

    # 특란 도매가
    price = re.search(r"특란[^\d]*([\d,]+)\s*원", text)
    if price: s["xl_price_won"] = price.group(1) + "원"

    # 수급 상황
    for kw in ["공급 과잉", "공급과잉", "수급 안정", "수급안정", "공급 부족", "공급부족"]:
        if kw in text:
            s["supply_status"] = kw
            break

    # 전주 대비
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
        "url":       f"https://www.ekapepia.com/v3/board/detail.do?boardInfoNo=0159&boardNo={board_no:08d}&dmlType=SELECT",
        "summary":   parsed["summary"],
        "text":      parsed["text"][:5000],
        "tables":    parsed["tables"][:5],
    }
    with open("egg_report/latest.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    with open("egg_report/latest.pdf", "wb") as f:
        f.write(pdf_bytes)
    print(f"  ✅ latest.json + latest.pdf 저장 완료")
    print(f"  요약: {out['summary']}")


def main():
    print("🥚 주간 계란 수급 정보 수집 시작...\n")
    board_no = attach_no = None
    title = ""

    # 전략 1: 목록 페이지
    print("📋 전략 1: 목록 페이지 탐색")
    try:
        board_no, title = find_latest_from_list()
        if board_no:
            attach_no, title = find_attach_from_detail(board_no)
    except Exception as e:
        print(f"  목록 페이지 실패: {e}")

    # 전략 2: 알려진 boardNo 기준 순차 탐색
    if not attach_no:
        print(f"\n📋 전략 2: boardNo={KNOWN_LATEST} 기준 순방향 탐색")
        try:
            board_no, attach_no, title = probe_board_sequential(KNOWN_LATEST, max_probe=15)
        except Exception as e:
            print(f"  순차 탐색 실패: {e}")

    if not attach_no:
        print("❌ PDF를 찾지 못했습니다.")
        sys.exit(1)

    # PDF 다운로드 + 파싱
    print(f"\n📥 PDF 다운로드 (attachNo={attach_no})...")
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
