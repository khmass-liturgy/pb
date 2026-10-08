#!/usr/bin/env python3
"""가금 질병·백신 주간 브리핑 — 유료서비스 「가금 질병·백신 주간 브리핑」 카드용.

매주 월요일 오전 7시(KST)에 최근 새로 공개된 가금(산란계·육계) 질병·백신 자료를 모아 현장 컨설팅에 도움이 되는
핵심 3건만 골라 한국어로 정리해 `poultry_disease_brief/latest.json` 에 쌓는다(최근 26주).

후보
  · 원 논문: PubMed(최근 3주 새로 등록된 논문, 백신·진단·변이주/역학·사양환경과 방역 키워드)
  · 정부·국제기구·수의기관 보고서와 신뢰할 만한 전문 분석: Google 뉴스 RSS 의 site: 검색(WOAH·EFSA·USDA APHIS·영국 APHA/gov.uk·FAO·
    농림축산검역본부·The Poultry Site·WATTPoultry 등)

선별·정리는 Claude(ANTHROPIC_API_KEY)가 한다. 논문은 초록, 기관 자료·기사는 본문(앞 6천 자)만 근거로 쓰게 하고 기사에 없는
내용은 쓰지 못하게 한다. 원문 제목·발행기관·발행일·링크는 Claude가 아니라 이 스크립트가 원자료에서 그대로 가져온다.
이전 주에 다룬 자료(PMID·주소·제목)는 후보에서 뺀다. 키가 없거나 API 호출이 실패하면 이전 JSON을 지우지 않는다.
모든 시각은 KST.
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote, urlparse

import requests

from fetch_industry_news import HEADERS as NEWS_HEADERS, article_text, decode_google_url, key_of, split_source
from translation_glossary import apply_glossary

KST = timezone(timedelta(hours=9))
OUT_PATH = Path("poultry_disease_brief/latest.json")
KEEP_WEEKS = 26
PICKS = 3
PUBMED_DAYS = 21
NEWS_DAYS = 14
MAX_PAPERS = 30
MAX_OFFICIAL = 20

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODELS = ("claude-sonnet-5", "claude-3-5-sonnet-20241022", "claude-haiku-4-5-20251001")   # 앞 모델이 거부되면 다음 모델
PUBMED_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; pb-disease-brief/1.0)"}
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# PubMed 검색어 — fetch_research_papers.py 와 같은 이유로 괄호마다 OR 항목을 2~4개로 짧게 유지한다
HOST = '(poultry[tiab] OR broiler[tiab] OR chicken[tiab] OR "laying hens"[tiab])'
PUBMED_QUERIES = [
    HOST + ' AND (vaccine[tiab] OR vaccination[tiab] OR immunity[tiab])',
    HOST + ' AND (diagnosis[tiab] OR detection[tiab] OR surveillance[tiab])',
    HOST + ' AND ("infectious bronchitis"[tiab] OR "Newcastle disease"[tiab] OR "infectious bursal disease"[tiab])',
    HOST + ' AND ("avian influenza"[tiab] OR "Marek"[tiab] OR "avian metapneumovirus"[tiab])',
    HOST + ' AND (variant[tiab] OR genotype[tiab] OR epidemiology[tiab] OR outbreak[tiab])',
    HOST + ' AND (coccidiosis[tiab] OR mycoplasma[tiab] OR "fowl adenovirus"[tiab])',
    HOST + ' AND (housing[tiab] OR ventilation[tiab] OR biosecurity[tiab]) AND (vaccine[tiab] OR disease[tiab])',
]

# 정부·국제기구·수의기관과 전문 매체 — (Google 뉴스 site: 검색어, 분류)
NEWS_QUERIES = [
    ("site:woah.org avian OR poultry vaccine OR disease", "official"),
    ("site:efsa.europa.eu avian influenza OR poultry", "official"),
    ("site:aphis.usda.gov poultry disease OR avian influenza vaccine", "official"),
    ("site:gov.uk avian influenza OR Newcastle poultry APHA", "official"),
    ("site:fao.org avian influenza OR poultry disease", "official"),
    ("site:qia.go.kr 가금 질병 OR 조류인플루엔자 OR 뉴캐슬", "official"),
    ("site:thepoultrysite.com infectious bronchitis OR Newcastle OR IBD OR coccidiosis vaccine", "analysis"),
    ("site:wattagnet.com poultry vaccine OR disease", "analysis"),
    ("가금 질병 백신 검역본부 발표", "official"),
]
OFFICIAL_HOSTS = ("woah.org", "efsa.europa.eu", "usda.gov", "gov.uk", "fao.org", "qia.go.kr", "who.int", "ema.europa.eu", "fda.gov", "go.kr")

AD = re.compile(r"sponsored|advertorial|press release|광고|협찬|\bwebinar\b|\bpodcast\b|giveaway", re.I)
TOPIC_HINT = re.compile(r"vaccin|immun|diagnos|detect|PCR|surveillance|variant|genotype|epidemi|outbreak|infectious bronchitis|Newcastle|bursal|avian influenza|"
                        r"Marek|metapneumo|coccidi|mycoplasma|adenovirus|housing|ventilation|biosecurity|백신|면역|진단|변이|역학|방역|질병", re.I)


# ── 후보 수집 ─────────────────────────────────────────────────────────────────
def _text(el: ET.Element | None) -> str:
    return "".join(el.itertext()).strip() if el is not None else ""


def pubmed_candidates() -> tuple[list[dict], int, int]:
    ids: dict[str, None] = {}
    ok = fail = 0
    for q in PUBMED_QUERIES:
        try:
            r = requests.get(ESEARCH_URL, params={"db": "pubmed", "term": q, "retmax": 12, "sort": "most+recent", "datetype": "edat",
                                                  "reldate": PUBMED_DAYS, "retmode": "json"}, headers=PUBMED_HEADERS, timeout=30)
            r.raise_for_status()
            for i in r.json().get("esearchresult", {}).get("idlist", []):
                ids.setdefault(i, None)
            ok += 1
        except Exception as exc:
            fail += 1
            print(f"::warning::PubMed 검색 실패: {type(exc).__name__}: {exc}")
    pmids = list(ids)[:MAX_PAPERS]
    if not pmids:
        return [], ok, fail
    out = []
    try:
        r = requests.get(EFETCH_URL, params={"db": "pubmed", "id": ",".join(pmids), "rettype": "abstract", "retmode": "xml"},
                         headers=PUBMED_HEADERS, timeout=60)
        r.raise_for_status()
        for art in ET.fromstring(r.text).findall(".//PubmedArticle"):
            pmid = _text(art.find(".//PMID"))
            title = _text(art.find(".//ArticleTitle"))
            abstract = " ".join(_text(p) for p in art.findall(".//Abstract/AbstractText"))
            if not (pmid and title and len(abstract) > 200):
                continue
            journal = _text(art.find(".//Journal/Title"))
            year, month = _text(art.find(".//JournalIssue/PubDate/Year")), _text(art.find(".//JournalIssue/PubDate/Month"))
            pub = (f"{year}-{month}".strip("-") if year else _text(art.find(".//JournalIssue/PubDate/MedlineDate")))
            # 온라인 공개일(있으면)이 더 정확하다
            for d in art.findall(".//ArticleDate"):
                y, m, dd = _text(d.find("Year")), _text(d.find("Month")), _text(d.find("Day"))
                if y and m and dd:
                    pub = f"{y}-{int(m):02d}-{int(dd):02d}"
                    break
            doi = next((e.text or "" for e in art.findall(".//ELocationID") if e.get("EIdType") == "doi"), "")
            types = [(_text(t)) for t in art.findall(".//PublicationType")]
            if any(t in ("Retracted Publication", "Retraction of Publication", "Comment", "Editorial", "Letter") for t in types):
                continue
            out.append({"cls": "paper", "id": "pmid:" + pmid, "title": title, "publisher": journal, "date": pub,
                        "url": f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        "pubmed": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", "text": abstract,
                        "ptype": ", ".join(t for t in types if t not in ("Journal Article",))[:80]})
    except Exception as exc:
        print(f"::warning::PubMed 초록 가져오기 실패: {type(exc).__name__}: {exc}")
    return out, ok, fail


def news_candidates() -> tuple[list[dict], int, int]:
    found: dict[str, dict] = {}
    ok = fail = 0
    for q, cls in NEWS_QUERIES:
        ko = bool(re.search(r"[가-힣]", q))
        url = "https://news.google.com/rss/search?q=" + quote(q + f" when:{NEWS_DAYS}d") + \
              ("&hl=ko&gl=KR&ceid=KR:ko" if ko else "&hl=en-US&gl=US&ceid=US:en")
        try:
            r = requests.get(url, headers=NEWS_HEADERS, timeout=30)
            r.raise_for_status()
            for it in ET.fromstring(r.content).iter("item"):
                title, src = split_source((it.findtext("title") or "").strip(), (it.findtext("source") or "").strip())
                try:
                    ts = parsedate_to_datetime(it.findtext("pubDate")).astimezone(KST)
                except Exception:
                    continue
                if not title or AD.search(title) or not TOPIC_HINT.search(title):
                    continue
                if (datetime.now(KST) - ts) > timedelta(days=NEWS_DAYS):
                    continue
                src_el = it.find("source")
                host = urlparse((src_el.get("url") or "") if src_el is not None else "").netloc.lower()
                kind = "official" if (cls == "official" or any(h in host for h in OFFICIAL_HOSTS)) else "analysis"
                k = key_of(title) if ko else re.sub(r"[^a-z0-9]", "", title.lower())[:40]
                found.setdefault(k, {"cls": kind, "id": "n:" + k, "title": title, "publisher": src, "date": ts.strftime("%Y-%m-%d"),
                                     "link": it.findtext("link") or "", "text": ""})
            ok += 1
        except Exception as exc:
            fail += 1
            print(f"::warning::뉴스 검색 실패({q[:40]}): {type(exc).__name__}: {exc}")
    items = sorted(found.values(), key=lambda i: i["date"], reverse=True)
    off = [i for i in items if i["cls"] == "official"][:MAX_OFFICIAL // 2]
    ana = [i for i in items if i["cls"] != "official"][:MAX_OFFICIAL // 2]
    return off + ana, ok, fail


# ── Claude ────────────────────────────────────────────────────────────────────
def claude(prompt: str, api_key: str, max_tokens: int) -> str:
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    resp = None
    for model in MODELS:
        resp = requests.post(ANTHROPIC_URL, headers=headers, timeout=180,
                             json={"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]})
        if resp.ok:
            break
        print(f"  Anthropic 응답 {resp.status_code} (model={model}): {resp.text[:200]}")
        if resp.status_code not in (400, 404):
            break
    resp.raise_for_status()
    texts = [b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text"]
    if not texts:
        raise ValueError("응답에 text 블록이 없음")
    return texts[0].strip()


def parse_json(text: str):
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    m = re.search(r"\{[\s\S]*\}", text)
    return json.loads(m.group(0)) if m else None


def listing(c: dict, n: int) -> str:
    head = f"[{n}] ({'원 논문' if c['cls'] == 'paper' else '정부·국제기구·수의기관' if c['cls'] == 'official' else '전문 분석·매체'}) {c['title']} — {c['publisher']} ({c['date']})"
    return head + (f"\n    초록: {c['text'][:450]}" if c["text"] else "")


def choose(cands: list[dict], prev_titles: list[str], api_key: str) -> list[int]:
    prompt = (
        "당신은 산란계·육계 농장 현장 컨설팅을 하는 수의사를 돕는 자료 큐레이터입니다. 아래는 최근 새로 공개된 가금 질병·백신 관련 자료 후보입니다.\n"
        f"이 중 현장 컨설팅에 도움이 되는 핵심 자료 {PICKS}건만 고르세요.\n"
        "우선순위: 질병 진단, 백신 효과·접종법·면역, 변이주와 역학, 사양환경이 방역·백신 성적에 미치는 영향.\n"
        "원칙:\n"
        "- 원 논문과 정부·국제기구·수의기관 자료(1차 자료)를 우선하고, 전문 분석·매체는 1차 자료가 약할 때만.\n"
        "- 광고성 자료, 근거가 약한 주장(표본 극소·단순 의견·시장 홍보), 현장 적용과 거리가 먼 기초 실험은 제외.\n"
        "- 산란계와 육계를 균형 있게 다루되, 그 주의 중요도에 따라 한쪽으로 쏠려도 됩니다. 억지로 비율을 맞추지 마세요.\n"
        "- 같은 주제에 쏠리지 않게 하고, 아래 '이전 브리핑'과 같은 주제·자료는 새로운 후속 정보가 분명할 때만 고르세요.\n"
        "- 후보 중 기준을 만족하는 것이 3건보다 적으면 그 수만 고르세요(억지로 채우지 마세요).\n"
        '출력은 JSON 한 개만: {"picks":[후보번호,...]}\n\n'
        "이전 브리핑 제목:\n" + ("\n".join("- " + t for t in prev_titles[:40]) or "(없음)") + "\n\n후보:\n"
        + "\n".join(listing(c, i) for i, c in enumerate(cands))
    )
    data = parse_json(claude(prompt, api_key, 500)) or {}
    out = []
    for i in data.get("picks", []):
        try:
            i = int(i)
        except Exception:
            continue
        if 0 <= i < len(cands) and i not in out:
            out.append(i)
    return out[:PICKS]


def analyze(picks: list[dict], api_key: str) -> dict | None:
    blocks = []
    for n, c in enumerate(picks):
        kind = "원 논문(초록만 제공)" if c["cls"] == "paper" else ("정부·국제기구·수의기관 자료" if c["cls"] == "official" else "전문 분석·매체 기사")
        body = c["text"][:6000] if c["text"] else "(본문을 읽지 못했습니다. 제목과 출처로 알 수 있는 범위로만 쓰고, 한계에 '본문을 확인하지 못함'을 쓰세요)"
        blocks.append(f"### 자료 {n}\n유형: {kind}\n제목: {c['title']}\n발행기관/저널: {c['publisher']}\n발행일: {c['date']}\n본문:\n{body}")
    prompt = (
        "다음 가금 질병·백신 자료 각각을 산란계·육계 농장 현장 컨설턴트(수의사)가 읽을 한국어 브리핑으로 정리하세요.\n"
        "엄격한 규칙:\n"
        "- 제공된 제목·본문(초록)에 있는 사실만 쓰세요. 없는 수치·결과·제품·기관을 지어내지 마세요. 확실하지 않으면 쓰지 마세요.\n"
        "- 원 논문은 초록만 읽은 것이므로 '초록 기준'임을 전제로 하고, 초록에서 확인되지 않는 것은 '초록만으로는 확인할 수 없음'이라고 쓰세요.\n"
        "- '조류독감'이 아니라 '조류인플루엔자'. 전문용어는 국내 수의 현장에서 쓰는 표현(IB, ND, IBD, 콕시듐증 등)을 쓰세요.\n"
        "- 항목별 필드(모두 필수):\n"
        '  · title: 한국어 제목 한 줄(45자 안팎)\n'
        '  · species: "산란계" | "육계" | "공통" 중 하나 (자료가 다루는 대상 기준)\n'
        '  · topic: "진단" | "백신·면역" | "변이·역학" | "사양환경·방역" 중 하나\n'
        '  · new: ① 무엇이 새로 나왔는지 — 핵심 사실 2~3개(문자열 배열, 각 한 문장, 가능하면 수치·설계 포함)\n'
        '  · why: ② 왜 현장적으로 중요한지 — 1~2개(문자열 배열)\n'
        '  · caution: ③ 농장 적용 시 주의점 — 1~3개(문자열 배열)\n'
        '  · limits: ③ 연구(자료)의 한계 — 1~3개(문자열 배열). 실험 감염인지 현장 자료인지, 표본 수, 단일 지역·기간, 이해관계 등 본문에서 확인되는 범위에서만\n'
        '  · evidence: 근거 수준 한 줄(예: "현장 감염 자료 기반 관찰연구", "백신 실험 감염 시험", "정부 감시 보고서")\n'
        "- checkpoints: 위 자료들을 종합해 이번 주 현장에서 확인할 점 3줄 이내(문자열 배열, 각 한 문장, 자료에 근거한 것만, 일반론 금지).\n"
        '출력은 JSON 한 개만: {"items":[{"idx":자료번호,"title":"","species":"","topic":"","new":[],"why":[],"caution":[],"limits":[],"evidence":""}],"checkpoints":[]}\n\n'
        + "\n\n".join(blocks)
    )
    data = parse_json(claude(prompt, api_key, 5000))
    if not data or not isinstance(data.get("items"), list):
        return None
    return data


def clean_list(v, n: int) -> list[str]:
    return [apply_glossary(str(x).strip()) for x in v if x and str(x).strip()][:n] if isinstance(v, list) else []


def monday_of(dt: datetime) -> str:
    return (dt - timedelta(days=dt.weekday())).strftime("%Y-%m-%d")


def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("ANTHROPIC_API_KEY 가 없어 선별·정리를 할 수 없습니다 — 이전 값을 유지합니다")
        return 0

    prev = {}
    if OUT_PATH.exists():
        try:
            prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
    now = datetime.now(KST)
    week = monday_of(now)
    past = [w for w in (prev.get("weeks") or []) if w.get("week") != week]       # 같은 주 재실행은 덮어쓴다
    seen_ids = {i.get("id") for w in past for i in w.get("items", [])}
    seen_titles = {key_of(i.get("origTitle", "")) for w in past for i in w.get("items", [])}
    prev_titles = [i.get("title", "") + " / " + i.get("origTitle", "") for w in past[:8] for i in w.get("items", [])]

    papers, pok, pfail = pubmed_candidates()
    news, nok, nfail = news_candidates()
    print(f"PubMed 검색 {pok}건 성공/{pfail}건 실패 · 논문 후보 {len(papers)}건 | 뉴스 검색 {nok}건 성공/{nfail}건 실패 · 기관/분석 후보 {len(news)}건")
    if pok + nok == 0:
        print("모든 검색이 실패해 이전 값을 유지합니다")
        return 1
    cands = [c for c in papers + news if c["id"] not in seen_ids and key_of(c["title"]) not in seen_titles]
    if len(cands) < PICKS:
        print("새 후보가 부족해 이전 값을 유지합니다")
        return 0

    idxs = choose(cands, prev_titles, api_key)
    if not idxs:
        print("Claude가 고른 자료가 없어 이전 값을 유지합니다")
        return 0
    picks = [dict(cands[i]) for i in idxs]
    print("선별: " + " | ".join(p["title"][:50] for p in picks))

    for c in picks:           # 논문이 아닌 자료는 원문을 읽어 와야 요약할 수 있다
        if c["cls"] != "paper":
            try:
                url = decode_google_url(c.get("link", "")) or ""
                c["url"] = url or c.get("link", "")
                c["text"] = article_text(url) if url else ""
            except Exception as exc:
                c["url"] = c.get("link", "")
                print(f"  원문 처리 실패({c['title'][:30]}): {type(exc).__name__}: {str(exc)[:80]}")

    data = analyze(picks, api_key)
    if not data:
        print("Claude 정리 결과를 읽지 못해 이전 값을 유지합니다")
        return 1

    items = []
    for it in data["items"]:
        try:
            c = picks[int(it.get("idx"))]
        except Exception:
            continue
        new, why, caution, limits = (clean_list(it.get(k), 3) for k in ("new", "why", "caution", "limits"))
        title = apply_glossary(str(it.get("title") or "").strip())
        if not (title and new and why and caution and limits):
            print(f"  필드 누락으로 제외: {c['title'][:40]}")
            continue
        items.append({
            "id": c["id"], "title": title,
            "species": it.get("species") if it.get("species") in ("산란계", "육계", "공통") else "공통",
            "topic": it.get("topic") if it.get("topic") in ("진단", "백신·면역", "변이·역학", "사양환경·방역") else "백신·면역",
            "cls": c["cls"], "evidence": apply_glossary(str(it.get("evidence") or "").strip()),
            "new": new, "why": why, "caution": caution, "limits": limits,
            # ④ 원문 정보는 모델이 쓰지 않고 원자료에서 그대로 가져온다
            "origTitle": c["title"], "publisher": c["publisher"], "date": c["date"], "url": c["url"],
            **({"pubmed": c["pubmed"]} if c.get("pubmed") else {}),
        })
    if not items:
        print("검증을 통과한 항목이 없어 이전 값을 유지합니다")
        return 1
    checkpoints = clean_list(data.get("checkpoints"), 3)

    weeks = sorted(past + [{"week": week, "items": items, "checkpoints": checkpoints}], key=lambda w: w["week"], reverse=True)[:KEEP_WEEKS]
    out = {"updated": now.strftime("%Y-%m-%d %H:%M KST"), "weeks": weeks}
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"저장: {week}주 {len(items)}건, 체크포인트 {len(checkpoints)}줄 (보관 {len(weeks)}주)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
