#!/usr/bin/env python3
"""
유료서비스 "기술탐구" 메뉴용 최신 논문 수집기.

PubMed(NCBI E-utils, 무료·키 불필요)에서 육계·산란계 관련 최근 논문을
카테고리별(질병논문/사양관리기술/컨설팅도구) 5편씩 가져온 뒤, Anthropic API로
제목·초록을 한글로 번역하고 "연구설계·핵심 수치"까지 요약한다.

매주 일요일 GitHub Actions(fetch-research-papers.yml)가 이 스크립트를 돌려
research_papers/latest.json 을 갱신한다. ANTHROPIC_API_KEY가 없거나 API
호출이 실패하면 그 카테고리는 이전 데이터를 그대로 유지한다(부분 실패가
전체를 지우지 않는다는 이 저장소의 공통 규칙).
"""

from __future__ import annotations

import json
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

KST = timezone(timedelta(hours=9))
OUTPUT_PATH = Path("research_papers/latest.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; pb-research-papers/1.0)"}

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-sonnet-5"
ANTHROPIC_MODEL_FALLBACK = "claude-3-5-sonnet-20241022"  # 기본 모델 ID가 거부될 때만 씀

# 카테고리별 PubMed 검색어 — 제목/초록(tiab)에 육계·산란계·가금 키워드와
# 카테고리 키워드가 함께 들어간 논문만 고른다.
#
# 주의 두 가지(둘 다 실제로 겪은 버그):
# 1) 홑단어 "layer"를 OR에 넣으면 "muscle layer"·"nanofluid layer"처럼 전혀
#    무관한 분야(공학·의학)까지 걸린다 — 반드시 "laying hen(s)"처럼 구를
#    따옴표로 묶어 쓴다. poultry/broiler/chicken 정도만 홑단어로 써도 된다.
# 2) OR 항목이 너무 많으면(한쪽에 5개 이상) PubMed 파서가 괄호 우선순위를
#    안정적으로 지키지 못해 AND가 사실상 무시되고 완전히 무관한 최신 논문이
#    섞여 나오는 현상이 있었다(예: 산부인과·건선 논문). 각 괄호는 2~4개
#    OR 항목으로 짧게 유지한다.
CATEGORIES = {
    "disease": {
        "label": "질병논문",
        "query": '(broiler[tiab] OR poultry[tiab] OR chicken[tiab] OR "laying hen"[tiab] OR "laying hens"[tiab]) '
                 'AND (disease[tiab] OR virus[tiab] OR pathogen[tiab])',
    },
    "management": {
        "label": "사양관리기술",
        "query": '(broiler[tiab] OR poultry[tiab] OR chicken[tiab] OR "laying hen"[tiab] OR "laying hens"[tiab]) '
                  'AND (nutrition[tiab] OR feed[tiab] OR housing[tiab] OR welfare[tiab])',
    },
    "consulting": {
        "label": "컨설팅도구",
        "query": '(poultry[tiab] OR broiler[tiab] OR "laying hen"[tiab]) '
                  'AND ("precision livestock farming"[tiab] OR "decision support"[tiab] '
                  'OR "farm management"[tiab] OR benchmarking[tiab])',
    },
}

RESULTS_PER_CATEGORY = 5
RECENCY_DAYS = 730  # 최근 2년 이내로 한정


def esearch_pmids(query: str) -> list[str]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": RESULTS_PER_CATEGORY,
        # "date"는 유효한 정렬 스키마가 아니라 조용히 무시된다(NCBI가 그냥
        # 경고만 주고 relevance로 돌아감) — 최근순 정렬은 pub_date를 쓴다.
        "sort": "pub_date",
        "datetype": "pdat",
        "reldate": RECENCY_DAYS,
        "retmode": "json",
    }
    resp = requests.get(ESEARCH_URL, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json().get("esearchresult", {}).get("idlist", [])


def _text(el: ET.Element | None) -> str:
    return "".join(el.itertext()).strip() if el is not None else ""


def efetch_articles(pmids: list[str]) -> list[dict[str, str]]:
    if not pmids:
        return []
    params = {"db": "pubmed", "id": ",".join(pmids), "rettype": "abstract", "retmode": "xml"}
    resp = requests.get(EFETCH_URL, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)

    articles = []
    for art in root.findall(".//PubmedArticle"):
        pmid = _text(art.find(".//PMID"))
        title = _text(art.find(".//ArticleTitle"))
        abstract = " ".join(_text(p) for p in art.findall(".//Abstract/AbstractText"))
        journal = _text(art.find(".//Journal/Title")) or _text(art.find(".//Journal/ISOAbbreviation"))

        year = _text(art.find(".//JournalIssue/PubDate/Year"))
        month = _text(art.find(".//JournalIssue/PubDate/Month"))
        medline_date = _text(art.find(".//JournalIssue/PubDate/MedlineDate"))
        pub_date = f"{year}-{month}".strip("-") if year else medline_date

        first_author_el = art.find(".//AuthorList/Author")
        first_author = ""
        if first_author_el is not None:
            last = _text(first_author_el.find("LastName"))
            first_author = last + (" 외" if len(art.findall(".//AuthorList/Author")) > 1 else "")

        doi = ""
        for eid in art.findall(".//ELocationID"):
            if eid.get("EIdType") == "doi":
                doi = eid.text or ""
        url = f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        if title and abstract:
            articles.append({
                "pmid": pmid, "title_en": title, "abstract_en": abstract,
                "journal": journal, "pub_date": pub_date, "author": first_author, "url": url,
            })
    return articles


def translate_and_summarize(articles: list[dict[str, str]]) -> list[dict[str, str]] | None:
    """Anthropic API로 제목 번역 + 연구설계·수치까지 포함한 한글 요약을 만든다."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or not articles:
        return None

    numbered = "\n\n".join(
        f"[{i+1}] TITLE: {a['title_en']}\nABSTRACT: {a['abstract_en']}"
        for i, a in enumerate(articles)
    )
    prompt = (
        "다음은 가금류(육계/산란계) 관련 최신 학술논문들의 영문 제목과 초록입니다. "
        "각 논문마다 아래 JSON 배열 형식으로만 한국어 결과를 출력하세요. "
        "다른 설명 문장 없이 JSON 배열 하나만 출력합니다.\n\n"
        '형식: [{"title_ko": "한글 제목", '
        '"summary_ko": "3~5문장. 연구 설계(대상·표본수·기간·방법)와 핵심 수치 결과를 반드시 포함"}, ...]\n\n'
        f"논문 목록:\n{numbered}"
    )

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body_base = {"max_tokens": 4000, "messages": [{"role": "user", "content": prompt}]}

    # 모델 ID는 시간이 지나며 바뀔 수 있어(구/신모델 교체), 기본 모델이
    # "model not found"류로 거부되면 알려진 안정 모델로 한 번 더 시도한다.
    # 그 외 오류(키 무효, 요금 문제 등)는 재시도해도 소용없으니 바로 올린다.
    resp = None
    for model in (ANTHROPIC_MODEL, ANTHROPIC_MODEL_FALLBACK):
        resp = requests.post(ANTHROPIC_URL, headers=headers, json={**body_base, "model": model}, timeout=120)
        if resp.ok:
            break
        print(f"  Anthropic API 응답 {resp.status_code} (model={model}): {resp.text[:300]}")
        if resp.status_code not in (400, 404) or model == ANTHROPIC_MODEL_FALLBACK:
            break
    resp.raise_for_status()
    blocks = resp.json().get("content", [])
    # content[0]이 항상 답변 텍스트라고 가정하면 안 된다 — 모델이 추론
    # 과정을 담은 thinking 블록을 먼저 반환하면 실제 답은 뒤쪽 블록에 있다.
    # type이 "text"인 첫 블록을 찾는다(KeyError 'text'로 실패했던 원인).
    text_blocks = [b.get("text", "") for b in blocks if b.get("type") == "text"]
    if not text_blocks:
        raise ValueError(f"응답에 text 블록이 없음: {[b.get('type') for b in blocks]}")
    text = text_blocks[0].strip()
    # 코드펜스로 감싸 나오는 경우가 있어 벗겨낸다
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    parsed = json.loads(text)
    if not isinstance(parsed, list) or len(parsed) != len(articles):
        raise ValueError(f"번역 결과 개수 불일치: {len(parsed) if isinstance(parsed, list) else '리스트 아님'}")
    return parsed


def build_category(key: str, meta: dict[str, str]) -> dict[str, Any] | None:
    print(f"[{meta['label']}] PubMed 검색 중...")
    try:
        pmids = esearch_pmids(meta["query"])
        time.sleep(0.4)  # NCBI 요청 간 예의상 텀
        articles = efetch_articles(pmids)
    except (requests.RequestException, ET.ParseError) as exc:
        print(f"[{meta['label']}] PubMed 수집 실패: {exc}")
        return None
    if not articles:
        print(f"[{meta['label']}] 결과 없음")
        return None
    print(f"[{meta['label']}] {len(articles)}편 수집, 번역·요약 중...")

    try:
        translated = translate_and_summarize(articles)
    except (requests.RequestException, ValueError, json.JSONDecodeError, KeyError) as exc:
        print(f"[{meta['label']}] 번역·요약 실패: {exc}")
        translated = None

    papers = []
    for i, art in enumerate(articles):
        tr = translated[i] if translated else {}
        papers.append({
            "title_en": art["title_en"],
            "title_ko": tr.get("title_ko") or art["title_en"],
            "summary_ko": tr.get("summary_ko") or "(번역 실패 — 영문 초록 참고) " + art["abstract_en"][:200],
            "journal": art["journal"],
            "pub_date": art["pub_date"],
            "author": art["author"],
            "url": art["url"],
        })
    return {"label": meta["label"], "papers": papers, "translated": translated is not None}


def load_previous() -> dict[str, Any]:
    if not OUTPUT_PATH.exists():
        return {}
    try:
        return json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def main() -> int:
    prev = load_previous()
    prev_categories = prev.get("categories", {})
    categories: dict[str, Any] = {}
    stale: dict[str, bool] = {}

    for key, meta in CATEGORIES.items():
        result = build_category(key, meta)
        if result is None:
            if key in prev_categories:
                categories[key] = prev_categories[key]
                stale[key] = True
                print(f"[{meta['label']}] 이번 수집 실패 → 이전 데이터 유지")
            else:
                print(f"[{meta['label']}] 이전 데이터도 없어 이 카테고리는 비웁니다")
            continue
        categories[key] = result

    if not categories:
        print("모든 카테고리 수집에 실패했고 이전 데이터도 없습니다.")
        return 1

    now = datetime.now(KST)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps({
        "updated": now.strftime("%Y-%m-%d %H:%M KST"),
        "stale": stale,
        "categories": categories,
        "source": "PubMed(NCBI) — 원문 제목/초록을 Claude API로 번역·요약",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("저장 완료:", OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
