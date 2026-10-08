#!/usr/bin/env python3
"""동물용의약품 주간 소식 — 유료서비스 「동물약품 주간 소식」 카드용.

매주 금요일 오전 7시(KST)에 국내외 동물용의약품 소식(신제품·백신·항생제·인허가/정책·연구개발·제약업계 동향)을
Google 뉴스 RSS(국내판 한국어 + 해외판 영어)로 모으고, 가금(산란계·육계) 현장에 중요한 3~5건만 골라
`animal_drug_news/latest.json` 에 쌓는다(최근 12주 보관).

선별·요약은 Claude(ANTHROPIC_API_KEY)가 한다. 키가 없거나 호출이 실패하면 키워드 점수로 고르고 본문 앞부분을 발췌한다.
Claude에게는 후보 기사의 제목·본문만 주고 "기사에 없는 내용은 쓰지 말 것"을 요구하며, 영문 기사는 한국어로 옮긴다.
모든 시각은 KST. 수집이 통째로 실패하면 이전 JSON을 지우지 않는다.
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote

import requests

# 같은 폴더의 양계 업계 소식 수집기에서 원문 주소 풀기·본문 추출·발췌 요약을 그대로 가져다 쓴다
# (워크플로우가 `python scripts/fetch_animal_drug_news.py` 로 돌리므로 scripts/ 가 sys.path 에 들어 있다).
from fetch_industry_news import HEADERS, KST, article_text, decode_google_url, lead_summary, split_source, key_of
from translation_glossary import apply_glossary

OUT_PATH = Path("animal_drug_news/latest.json")
KEEP_WEEKS = 12
LOOKBACK_DAYS = 8            # 지난 한 주(+하루) 안의 기사만 후보
MAX_CANDIDATES = 24          # Claude에게 보여 줄 후보 수
PICK_MIN, PICK_MAX = 3, 5
MODEL = os.environ.get("ANIMAL_NEWS_MODEL", "claude-haiku-4-5-20251001")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

CATEGORIES = ["신제품·백신", "항생제·약제", "인허가·정책", "연구개발", "업계 동향"]

# (지역, 검색어, 언어 설정)
KO = ("ko", "&hl=ko&gl=KR&ceid=KR:ko")
EN = ("en", "&hl=en-US&gl=US&ceid=US:en")
QUERIES = [
    ("국내", "동물용의약품 신제품", KO),
    ("국내", "동물약품 출시", KO),
    ("국내", "가금 백신 출시 양계", KO),
    ("국내", "동물용의약품 허가 농림축산검역본부", KO),
    ("국내", "동물용 항생제 휴약기간 규제", KO),
    ("국내", "동물약품 제약사 양계 백신", KO),
    ("국내", "한국동물약품협회", KO),
    ("국내", "site:dailyvet.co.kr 신제품", KO),
    ("해외", "poultry vaccine launch", EN),
    ("해외", "poultry vaccine approval", EN),
    ("해외", "Zoetis OR Boehringer OR Ceva OR Elanco OR \"MSD Animal Health\" poultry", EN),
    ("해외", "FDA CVM approves poultry OR livestock drug", EN),
    ("해외", "EMA CVMP veterinary vaccine recommendation", EN),
    ("해외", "animal health acquisition OR investment poultry", EN),
    ("해외", "site:thepoultrysite.com vaccine", EN),
    ("해외", "Animal Pharm poultry", EN),
    ("해외", "antimicrobial resistance poultry antibiotic regulation", EN),
]

# ── 관련도 점수 ───────────────────────────────────────────────────────────────
DRUG = re.compile(r"동물약품|동물용의약품|동물의약품|백신|항생제|항균|구충|콕시듐|치료제|약제|휴약|허가|신제품|출시|"
                  r"vaccine|vaccin|antibiotic|antimicrobial|coccidi|veterinary|animal health|approval|approves|approved|launch|CVM|CVMP|drug", re.I)
POULTRY = re.compile(r"가금|양계|산란계|육계|닭|계란|오리|뉴캐슬|전염성|IBD|콕시듐|마이코|조류인플루엔자|"
                     r"poultry|chicken|broiler|layer|hen|avian|Newcastle|infectious bronchitis|Marek|coccidi|egg", re.I)
PET = re.compile(r"반려|강아지|고양이|펫|애견|\bdog\b|\bcat\b|\bpet\b|canine|feline|equine", re.I)
LAUNCH = re.compile(r"신제품|출시|론칭|개발|launch|introduc|new vaccine|new product", re.I)
APPROVE = re.compile(r"허가|승인|인증|고시|규제|휴약|approval|approves|approved|recommend|ban|restrict|regulat", re.I)
BIZ = re.compile(r"인수|합병|투자|M&A|acqui|merger|invest|partnership|제휴|협약", re.I)
PRIORITY_SRC = re.compile(r"데일리벳|검역본부|동물약품협회|thepoultrysite|poultry site|animal pharm|FDA|EMA|WATTAgNet|Feedstuffs", re.I)
JUNK = re.compile(r"주가|목표가|배당|코스닥|코스피|stock price|shares|dividend|펫푸드|사료 첨가", re.I)


def score(title: str, source: str) -> int:
    s = 0
    if DRUG.search(title):
        s += 2
    if POULTRY.search(title):
        s += 3
    if LAUNCH.search(title):
        s += 2
    if APPROVE.search(title):
        s += 2
    if BIZ.search(title):
        s += 1
    if PRIORITY_SRC.search(source or "") or PRIORITY_SRC.search(title):
        s += 1
    if PET.search(title) and not POULTRY.search(title):
        s -= 4
    if JUNK.search(title):
        s -= 3
    return s


def category_guess(title: str) -> str:
    if re.search(r"항생제|antibiotic|antimicrobial|휴약|내성", title, re.I):
        return "항생제·약제"
    if APPROVE.search(title):
        return "인허가·정책"
    if BIZ.search(title):
        return "업계 동향"
    if re.search(r"연구|논문|임상|효능|study|trial|research", title, re.I):
        return "연구개발"
    return "신제품·백신"


def search(region: str, q: str, lang: tuple[str, str]) -> list[dict]:
    url = "https://news.google.com/rss/search?q=" + quote(q + f" when:{LOOKBACK_DAYS}d") + lang[1]
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    out = []
    for it in ET.fromstring(r.content).iter("item"):
        raw = (it.findtext("title") or "").strip()
        title, src = split_source(raw, (it.findtext("source") or "").strip())
        try:
            ts = parsedate_to_datetime(it.findtext("pubDate")).astimezone(KST)
        except Exception:
            continue
        if (datetime.now(KST) - ts) > timedelta(days=LOOKBACK_DAYS):
            continue
        sc = score(title, src)
        if title and sc >= 3:
            out.append({"title": title, "source": src, "link": it.findtext("link") or "", "ts": ts.strftime("%Y-%m-%d %H:%M"),
                        "region": region, "lang": lang[0], "score": sc})
    return out


def collect() -> tuple[list[dict], int, int]:
    found: dict[str, dict] = {}
    ok = fail = 0
    for region, q, lang in QUERIES:
        try:
            for it in search(region, q, lang):
                k = key_of(it["title"]) if it["lang"] == "ko" else re.sub(r"[^a-z0-9]", "", it["title"].lower())[:40]
                cur = found.get(k)
                if cur is None or it["score"] > cur["score"]:
                    found[k] = it
            ok += 1
        except Exception as exc:
            fail += 1
            print(f"::warning::검색 실패({q}): {type(exc).__name__}: {exc}")
    cands = sorted(found.values(), key=lambda i: (i["score"], i["ts"]), reverse=True)
    return cands, ok, fail


# ── Claude 호출 ───────────────────────────────────────────────────────────────
def claude(prompt: str, api_key: str, max_tokens: int = 1500) -> str | None:
    resp = requests.post(ANTHROPIC_URL, headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                         json={"model": MODEL, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}, timeout=90)
    if not resp.ok:
        print(f"  Anthropic 응답 {resp.status_code}: {resp.text[:200]}")
        return None
    return "".join(b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text").strip()


def parse_json(text: str | None):
    if not text:
        return None
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def pick_with_claude(cands: list[dict], api_key: str) -> list[dict] | None:
    listing = "\n".join(f"{i}. [{c['region']}] {c['title']} — {c['source']} ({c['ts'][:10]})" for i, c in enumerate(cands))
    prompt = (
        "당신은 산란계·육계 현장 컨설턴트(수의사)를 돕는 편집자입니다. 아래는 지난 한 주 동안 모은 동물용의약품 관련 기사 후보입니다.\n"
        f"이 중 가금(산란계·육계) 컨설팅에 중요한 소식 {PICK_MIN}~{PICK_MAX}건을 고르세요.\n"
        "기준: ① 가금 백신·항생제·구충제·신제품·투여기술 ② 국내외 허가·휴약기간·항생제 규제·GMP 변경 ③ 해외 제약업계 동향(출시·인수합병·투자) ④ 연구 결과.\n"
        "- 같은 사건을 다룬 기사는 하나만, 국내와 해외가 섞이도록(가능하면), 광고성·반려동물 전용·주식 기사는 제외.\n"
        "- 각 기사에 category(다음 중 하나: " + " / ".join(CATEGORIES) + ")를 붙이세요.\n"
        '출력은 JSON 한 개만: {"picks":[{"id":번호,"category":"분류"}]}\n\n' + listing
    )
    data = parse_json(claude(prompt, api_key, 600))
    if not data or not isinstance(data.get("picks"), list):
        return None
    out, seen = [], set()
    for p in data["picks"]:
        try:
            i = int(p.get("id"))
        except Exception:
            continue
        if 0 <= i < len(cands) and i not in seen:
            seen.add(i)
            c = dict(cands[i])
            c["category"] = p.get("category") if p.get("category") in CATEGORIES else category_guess(c["title"])
            out.append(c)
    return out[:PICK_MAX] if len(out) >= 1 else None


def summarize_with_claude(item: dict, text: str, api_key: str) -> dict | None:
    body = text[:5000] if text else "(본문을 읽지 못했습니다. 제목만 근거로 삼으세요)"
    prompt = (
        "다음은 동물용의약품 관련 기사입니다. 산란계·육계 컨설턴트가 읽을 카드로 정리하세요.\n"
        "- 기사 제목과 본문에 있는 사실만 쓰고, 없는 내용·수치·제품명을 지어내지 마세요. 본문이 없으면 제목에서 알 수 있는 범위로만 쓰세요.\n"
        "- 영문 기사는 자연스러운 한국어로 옮기세요(제품명·회사명은 원문 표기 유지, '조류독감'이 아니라 '조류인플루엔자').\n"
        "- title: 한국어 제목 한 줄(40자 안팎).\n"
        "- summary: 핵심 사실 2~3개를 각각 한 문장으로(문자열 배열).\n"
        "- point: 가금 현장에서 이 소식이 갖는 의미나 확인할 점을 한 문장으로. 기사에 근거가 없으면 빈 문자열.\n"
        '출력은 JSON 한 개만: {"title":"","summary":["",""],"point":""}\n\n'
        f"제목: {item['title']}\n출처: {item['source']}\n\n본문:\n{body}"
    )
    data = parse_json(claude(prompt, api_key, 900))
    if not data or not isinstance(data.get("summary"), list):
        return None
    summ = [str(s).strip() for s in data["summary"] if str(s).strip()][:3]
    title = str(data.get("title") or "").strip()
    if not summ or not title:
        return None
    return {"title": apply_glossary(title), "summary": [apply_glossary(s) for s in summ],
            "point": apply_glossary(str(data.get("point") or "").strip())}


def build_item(c: dict, api_key: str | None) -> dict:
    url, text = "", ""
    try:
        url = decode_google_url(c.get("link", "")) or ""
        text = article_text(url) if url else ""
    except Exception as exc:
        print(f"  원문 처리 실패({c['title'][:30]}): {type(exc).__name__}: {str(exc)[:80]}")
    ai = summarize_with_claude(c, text, api_key) if api_key else None
    base = {"region": c["region"], "category": c.get("category") or category_guess(c["title"]), "source": c["source"],
            "date": c["ts"][:10], "url": url or c.get("link", ""), "titleOrig": c["title"]}
    if ai:
        base.update({"title": ai["title"], "summary": ai["summary"], "point": ai["point"], "ai": True})
    else:
        sents = [s for s in re.split(r"(?<=[.。다요])\s+", lead_summary(text, 220, c["title"])) if s.strip()][:2] if text else []
        base.update({"title": c["title"], "summary": sents, "point": "", "ai": False})
    return base


def friday_of(dt: datetime) -> str:
    """이 실행이 속한 주(월~일)의 금요일 날짜 — 같은 주에 다시 돌려도 같은 칸을 덮어쓰게 한다."""
    return (dt + timedelta(days=4 - dt.weekday())).strftime("%Y-%m-%d")


def main() -> int:
    prev = {}
    if OUT_PATH.exists():
        try:
            prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        except Exception:
            prev = {}

    cands, ok, fail = collect()
    print(f"검색 {ok}건 성공 / {fail}건 실패 · 후보 {len(cands)}건")
    if ok == 0:
        print("모든 검색이 실패해 이전 값을 유지합니다")
        return 1
    if not cands:
        print("이번 주 후보 기사가 없어 이전 값을 유지합니다")
        return 0
    cands = cands[:MAX_CANDIDATES]

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip() or None
    picks = pick_with_claude(cands, api_key) if api_key else None
    if not picks:
        print("키워드 점수로 선별합니다" + ("" if not api_key else " (Claude 선별 실패)"))
        picks, seen_cat = [], {}
        for c in cands:
            c = dict(c)
            c["category"] = category_guess(c["title"])
            if seen_cat.get((c["region"], c["category"]), 0) >= 2:
                continue
            seen_cat[(c["region"], c["category"])] = seen_cat.get((c["region"], c["category"]), 0) + 1
            picks.append(c)
            if len(picks) >= 4:
                break
    print(f"선별 {len(picks)}건: " + " | ".join(p["title"][:30] for p in picks))

    with ThreadPoolExecutor(max_workers=3) as ex:
        items = list(ex.map(lambda c: build_item(c, api_key), picks))

    now = datetime.now(KST)
    week = friday_of(now)
    weeks = [w for w in (prev.get("weeks") or []) if w.get("week") != week]
    weeks.insert(0, {"week": week, "items": items})
    weeks = sorted(weeks, key=lambda w: w["week"], reverse=True)[:KEEP_WEEKS]
    out = {"updated": now.strftime("%Y-%m-%d %H:%M KST"), "weeks": weeks}

    def core(d):
        return {k: v for k, v in d.items() if k != "updated"}
    if prev and core(prev) == core(out):
        print("변경 없음")
        return 0
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"저장: {week}주 {len(items)}건 (보관 {len(weeks)}주)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
