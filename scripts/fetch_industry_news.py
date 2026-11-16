#!/usr/bin/env python3
"""양계 업계 소식 수집 — 유료서비스 「업계관련 소식」 카드용.

계란·조류인플루엔자·AI(고병원성)·육계·방역·양계 질병 등 양계 키워드로 Google 뉴스 RSS(한국어·국내판)를 검색해
`industry_news/latest.json` 에 쌓는다. 매일 한 번 돌고, 최근 14일치를 유지한다(이전 기사 + 새 기사 병합, 제목 중복 제거).

'AI'는 인공지능 기사와 섞이므로 제목에 가금·방역 맥락이 있을 때만 받는다. 모든 시각은 KST.
부분 실패는 이전 JSON을 지우지 않는다(키워드 하나 실패해도 나머지로 갱신).
"""

from __future__ import annotations

import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote

import requests

KST = timezone(timedelta(hours=9))
OUT_PATH = Path("industry_news/latest.json")
KEEP_DAYS = 14
MAX_ITEMS = 200
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}

# (묶음 이름, 검색어 목록) — 묶음은 화면의 필터 칩이 된다
GROUPS = [
    ("계란", ["계란 가격", "계란 산란계 수급", "달걀 가격", "계란 유통"]),
    ("조류인플루엔자·AI", ["조류인플루엔자", "고병원성 AI 가금농장", "AI 확진 살처분", "고병원성 AI 철새"]),
    ("육계", ["육계 시세", "닭고기 가격", "육계 농가", "삼계 닭고기 수급"]),
    ("방역", ["가금농장 방역", "양계 방역", "가축질병 닭 오리 방역"]),
    ("양계 질병", ["뉴캐슬병", "가금티푸스", "전염성기관지염 닭", "살모넬라 닭", "닭 질병 사료 양계"]),
    ("양계 산업", ["양계농가", "산란계 농가", "양계협회", "축산신문 양계"]),
]
TAG_WORDS = {
    "계란": ["계란", "달걀", "산란계", "난가", "알 "],
    "조류인플루엔자·AI": ["조류인플루엔자", "고병원성", "AI", "철새", "살처분"],
    "육계": ["육계", "닭고기", "삼계", "닭 ", "병아리"],
    "방역": ["방역", "소독", "이동제한", "행정명령"],
    "양계 질병": ["뉴캐슬", "티푸스", "기관지염", "살모넬라", "마이코플라스마", "대장균", "질병", "감염"],
    "양계 산업": ["양계", "농가", "가금", "종계", "오리", "메추리"],
}
STRONG = re.compile(r"계란|달걀|조류인플루엔자|육계|산란계|양계|가금|종계|닭고기|병아리|뉴캐슬|가금티푸스|삼계")
WEAK_AI = re.compile(r"\bAI\b|고병원성")
AI_CONTEXT = re.compile(r"고병원성|조류|확진|살처분|철새|가금|농장|방역|닭|오리|계란|산란|도래지|이동제한|행정명령")
NOT_AI_TECH = re.compile(r"인공지능|생성형|챗GPT|ChatGPT|딥러닝|반도체|로봇|자율주행|GPU|LLM")
WEAK_OTHER = re.compile(r"닭|오리|방역|가축질병|살처분|살모넬라")
POULTRY_CTX = re.compile(r"닭|오리|가금|양계|계란|조류|산란|육계|AI|농장|철새")


# 치킨 프랜차이즈 홍보·금융·요리 기사는 업계 소식이 아니다(산업 키워드가 함께 있으면 남긴다)
NOT_INDUSTRY = re.compile(r"1호점|가맹점|신메뉴|출시|프로모션|은행|전세금|맛집|레시피|이벤트|쿠폰|할인 행사")
INDUSTRY_CORE = re.compile(r"산란계|육계|조류인플루엔자|고병원성|양계|가금|종계|살처분|방역|수급")


def relevant(title: str) -> bool:
    if NOT_INDUSTRY.search(title) and not INDUSTRY_CORE.search(title):
        return False
    if NOT_AI_TECH.search(title) and not STRONG.search(title):
        return False
    if STRONG.search(title):
        return True
    if WEAK_AI.search(title):
        return bool(AI_CONTEXT.search(title))
    if WEAK_OTHER.search(title):
        return bool(POULTRY_CTX.search(title))
    return False


def tags_for(title: str) -> list[str]:
    out = []
    for g, words in TAG_WORDS.items():
        if any(w in title for w in words):
            out.append(g)
    return out


def split_source(title: str, source: str) -> tuple[str, str]:
    """'기사 제목 - 언론사' 에서 언론사를 떼어 낸다."""
    m = re.match(r"^(.*)\s[-–]\s([^-–]+)$", title)
    if m and (not source or m.group(2).strip() == source):
        return m.group(1).strip(), (source or m.group(2).strip())
    return title.strip(), source


def search(q: str) -> list[dict]:
    url = "https://news.google.com/rss/search?q=" + quote(q + " when:2d") + "&hl=ko&gl=KR&ceid=KR:ko"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    items = []
    for it in ET.fromstring(r.content).iter("item"):
        raw = (it.findtext("title") or "").strip()
        src = (it.findtext("source") or "").strip()
        title, src = split_source(raw, src)
        try:
            ts = parsedate_to_datetime(it.findtext("pubDate")).astimezone(KST)
        except Exception:
            continue
        if title and relevant(title):
            items.append({"title": title, "source": src, "link": it.findtext("link") or "", "ts": ts.strftime("%Y-%m-%d %H:%M")})
    return items


def key_of(title: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", title)[:28]


# ── 기사 원문 주소 찾기 + 본문 요약 ───────────────────────────────────────────────
# Google 뉴스 RSS 링크는 언론사로 넘겨 주는 중간 주소라 원문 주소를 따로 풀어야 한다(batchexecute 호출).
# 원문 본문은 trafilatura 로 뽑고, 요약은 Claude(ANTHROPIC_API_KEY)로 만든다. 키가 없거나 호출이 실패하면
# 본문 앞부분 2문장으로 대신한다(summary_ai=False). 요약은 기사 내용을 짧게 줄인 것이며 원문은 링크로 안내한다.
SUMMARY_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MAX_NEW_SUMMARIES = 120      # 한 번에 처리할 기사 수(처음엔 밀린 기사를 나눠서 채운다)


def decode_google_url(link: str) -> str | None:
    m = re.search(r"/articles/([^?/]+)", link or "")
    if not m:
        return None
    gid = m.group(1)
    page = requests.get(f"https://news.google.com/rss/articles/{gid}?hl=ko&gl=KR&ceid=KR:ko", headers=HEADERS, timeout=20)
    sg = re.search(r'data-n-a-sg="([^"]+)"', page.text)
    ts = re.search(r'data-n-a-ts="([^"]+)"', page.text)
    if not sg or not ts:
        return None
    inner = json.dumps(["garturlreq", [["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1, None, None, None, None, None, 0, 1],
                                       "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0], gid, int(ts.group(1)), sg.group(1)],
                       separators=(",", ":"))
    freq = json.dumps([[["Fbv4je", inner, None, "generic"]]], separators=(",", ":"))
    resp = requests.post("https://news.google.com/_/DotsSplashUi/data/batchexecute",
                         headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
                         data="f.req=" + quote(freq), timeout=20)
    arr = json.loads(resp.text.split("\n\n", 1)[1])[:-2]
    url = json.loads(arr[0][2])[1]
    return url if isinstance(url, str) and url.startswith("http") else None


def article_text(url: str) -> str:
    import trafilatura
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    if not r.encoding or r.encoding.lower() == "iso-8859-1":
        r.encoding = r.apparent_encoding
    return (trafilatura.extract(r.text, include_comments=False, include_tables=False) or "").strip()


def lead_summary(text: str, limit: int = 170, title: str = "") -> str:
    """본문 앞부분 문장으로 대신하는 요약(제목 반복·기자명·출처 머리글 제거)."""
    if title and text.lstrip().startswith(title[:12]):
        text = text.lstrip()[len(title):] if text.lstrip().startswith(title) else text
    t = re.sub(r"^\s*[\(\[【][^\)\]】]{0,30}[\)\]】]\s*", "", text.replace("\n", " "))
    t = re.sub(r"^[^.。]{0,40}기자\s*[=:]?\s*", "", t)
    sents = re.split(r"(?<=[.。다요])\s+", t)
    out = ""
    for s in sents:
        if len(out) + len(s) > limit and out:
            break
        out += (" " if out else "") + s.strip()
        if len(out) >= 90:
            break
    return out[:limit + 20].strip()


def ai_summary(title: str, text: str, api_key: str) -> str | None:
    prompt = ("다음은 양계(닭·계란·오리) 관련 국내 뉴스 기사입니다. 한국어로 2~3문장, 150자 안팎으로 요약하세요.\n"
              "- 누가·무엇을·언제·수치 같은 핵심 사실 위주로, 기사에 없는 내용은 절대 덧붙이지 마세요.\n"
              "- 광고·기자 소개·관련기사 문구는 빼세요. 요약문만 출력하세요(머리말·따옴표·번호 없이).\n\n"
              f"제목: {title}\n\n본문:\n{text[:5000]}")
    resp = requests.post(ANTHROPIC_URL, headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                         json={"model": SUMMARY_MODEL, "max_tokens": 400, "messages": [{"role": "user", "content": prompt}]}, timeout=60)
    if not resp.ok:
        print(f"  Anthropic 응답 {resp.status_code}: {resp.text[:160]}")
        return None
    s = "".join(b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text").strip()
    return s if 20 <= len(s) <= 600 else None


def enrich(item: dict, api_key: str | None) -> dict:
    """원문 주소(url)와 요약(summary)을 채운다. 실패한 단계는 비워 두고 다음 실행에서 다시 시도한다."""
    out = {}
    try:
        url = item.get("url") or decode_google_url(item.get("link", ""))
        if url:
            out["url"] = url
        text = article_text(url) if url else ""
        if len(text) >= 150:
            s = ai_summary(item["title"], text, api_key) if api_key else None
            if s:
                out["summary"], out["summary_ai"] = s, True
            else:
                out["summary"], out["summary_ai"] = lead_summary(text, title=item["title"]), False
        elif url:
            out["summary"], out["summary_ai"] = "", False      # 본문을 못 읽은 기사(요약 없음) — 다시 시도하지 않는다
    except Exception as exc:
        print(f"  요약 실패({item.get('title', '')[:24]}): {type(exc).__name__}: {str(exc)[:80]}")
    return out


# ── 핵심 소식 고르기(중복 묶기 + 업계 가치 판단) ─────────────────────────────────────
# 같은 사건을 여러 매체가 받아쓴 기사와, 지자체의 「방역 총력」류 단순 보도가 목록을 채워 읽을 것이 묻힌다(2026-11 소유자 요청).
# ① 제목이 겹치는 기사를 한 묶음(grp)으로 모으고 대표 기사 하나만 남긴다(업계 전문지 우선).
# ② 대표 기사마다 「업계에 의미 있는 소식인가」를 판단해 분류(cat)와 한 줄 이유(why)를 붙인다 — Claude Haiku,
#    키가 없으면 낱말 규칙. 판단 결과는 기사에 pick으로 남겨 다음 실행에서 다시 묻지 않는다(규칙 판단은 키가 생기면 다시 판단).
# 화면은 picks(고른 소식)를 먼저 보여 주고, 전체 기사(items)는 「전체 기사 보기」로 남긴다.
PICK_CATS = ["수급·가격", "정책·제도", "기업·단체 동향", "기술·연구", "질병·방역 분석", "해외 동향", "기타 업계"]
MAX_PICKS = 80
TRADE_PRESS = re.compile(r"농민신문|농수축산신문|축산신문|한국농정|축산경제|데일리벳|양계|농축유통|농어민신문|팜인사이트|라이브뉴스|livesnews|정책브리핑|농업인신문|축산뉴스|식품저널|푸드아이콘")
STOP_TOKENS = {"고병원성", "AI", "조류인플루엔자", "조류", "인플루엔자", "방역", "총력", "확진", "긴급", "비상", "강화", "차단", "차단방역", "농장",
               "가금", "가금농장", "가금농가", "발생", "확산", "검출", "항원", "관련", "위해", "대응", "나서", "실시", "추진", "올해", "최근"}
ROUTINE = re.compile(r"총력|비상|긴급 ?방역|차단 ?방역|방역 ?강화|소독|살처분|확진|항원|검출|유입 차단|예찰|위험주의보|방역대|이동제한|특교세|대책회의|행정명령|당부")
INSIGHT = re.compile(r"수급|가격|시세|전망|통계|유통|협회|지부|정책|개정|고시|법안|제도|지원사업|보조|수출|수입|공정위|계열|투자|인수|매출|실적|연구|개발|기술|스마트|"
                     r"동물복지|사육밀도|이력제|등급|칼럼|분석|진단|인터뷰|단지|백신|생산량|마릿수|관측|규모화|출범|승계|의혹")
CAT_RULES = [
    ("수급·가격", re.compile(r"수급|가격|시세|생산량|마릿수|관측|전망|유통|격차")),
    ("정책·제도", re.compile(r"정책|개정|고시|법안|제도|지원|보조|규제|공정위|이력제|등급|사육밀도|동물복지|백지화|단지")),
    ("기업·단체 동향", re.compile(r"협회|지부|계열|투자|인수|매출|실적|하림|마니커|체리부로|올품|출범|대표|회장|승계|의혹")),
    ("기술·연구", re.compile(r"연구|개발|기술|스마트|백신|특허|단축")),
    ("해외 동향", re.compile(r"미국|일본|중국|유럽|EU|브라질|태국|해외|글로벌|수출|수입")),
    ("질병·방역 분석", re.compile(r"조류인플루엔자|고병원성|AI|뉴캐슬|티푸스|살모넬라|질병|방역")),
]


def title_tokens(title: str) -> set[str]:
    out = set()
    for w in re.findall(r"[가-힣A-Za-z0-9]+", title):
        w = re.sub(r"(에서|으로|에게|까지|부터|서|에|은|는|이|가|을|를|도|의|로|와|과)$", "", w) if len(w) > 2 else w
        if len(w) >= 2 and w not in STOP_TOKENS:
            out.add(w)
    return out


def cluster(items: list[dict]) -> dict[int, int]:
    """제목 낱말이 많이 겹치고 3일 안에 나온 기사를 한 묶음으로. 반환: 기사 번호 → 묶음 대표 번호."""
    toks = [title_tokens(i["title"]) for i in items]
    day = [i.get("ts", "")[:10] for i in items]
    parent = list(range(len(items)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def near(a, b):
        try:
            return abs((datetime.strptime(day[a], "%Y-%m-%d") - datetime.strptime(day[b], "%Y-%m-%d")).days) <= 3
        except ValueError:
            return False
    for a in range(len(items)):
        for b in range(a + 1, len(items)):
            if not toks[a] or not toks[b] or not near(a, b):
                continue
            n = len(toks[a] & toks[b])
            r = n / min(len(toks[a]), len(toks[b]))
            if (n >= 3 and r >= 0.6) or (n >= 2 and r >= 0.8):
                parent[find(b)] = find(a)
    return {i: find(i) for i in range(len(items))}


def rule_pick(item: dict) -> dict:
    t = item.get("title", "")
    trade = bool(TRADE_PRESS.search(item.get("source", "")))
    keep = bool(INSIGHT.search(t)) and not (ROUTINE.search(t) and not re.search(r"수급|가격|전망|분석|칼럼|정책|제도", t))
    if trade and not ROUTINE.search(t):
        keep = True
    cat = next((c for c, rx in CAT_RULES if rx.search(t)), "기타 업계")
    return {"keep": keep, "cat": cat, "why": "", "ai": False}


def ai_picks(reps: list[dict], api_key: str) -> dict[int, dict]:
    """대표 기사 묶음(최대 40건)을 한 번에 판단. 반환: 목록 안 번호 → {keep, cat, why, same}."""
    lines = "\n".join(f"{n}. [{r.get('source', '')}] {r['title']} — {(r.get('summary') or '')[:110]}" for n, r in enumerate(reps))
    prompt = ("당신은 양계(육계·산란계·종계·오리) 업계 전문지의 편집자입니다. 아래 기사 목록에서 양계 농가·업계 종사자가 "
              "「단순 뉴스」가 아니라 **업계 정보**로 읽을 가치가 있는 것만 고르세요.\n\n"
              "고르는 것(keep=true): 수급·가격의 분석이나 통계, 정책·제도·법령·지원사업의 변화, 협회·계열회사·기업의 움직임(투자·분쟁·인사·조직), "
              "새 기술·연구·제품, 해외 시장·질병 동향, 질병·방역에 대한 분석·해설·새로운 양상.\n"
              "버리는 것(keep=false): 특정 지역의 AI 발생·확진·살처분 속보, 지자체의 「방역 총력·소독 실시·대책회의」 보도, 같은 사건을 다시 전한 기사, "
              "치킨 프랜차이즈 홍보, 일반 소비자용 생활 기사, 양계와 관련이 약한 기사.\n"
              "같은 사건·같은 발표를 다룬 기사가 목록에 여럿이면 가장 내용이 충실한 하나만 keep=true로 하고 나머지는 keep=false, same에 그 기사 번호를 적으세요.\n\n"
              f"분류(cat)는 다음 중 하나: {', '.join(PICK_CATS)}\n"
              "why는 「왜 업계에 중요한가」를 한국어 한 문장(40자 안팎)으로, 기사에 없는 사실은 쓰지 마세요.\n\n"
              '출력은 JSON 배열만: [{"i":0,"keep":true,"cat":"수급·가격","why":"…","same":null}, …] — 모든 번호를 빠짐없이.\n\n' + lines)
    resp = requests.post(ANTHROPIC_URL, headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                         json={"model": SUMMARY_MODEL, "max_tokens": 4000, "messages": [{"role": "user", "content": prompt}]}, timeout=120)
    if not resp.ok:
        print(f"  선별 응답 {resp.status_code}: {resp.text[:160]}")
        return {}
    text = "".join(b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text")
    m = re.search(r"\[.*\]", text, re.S)
    try:
        rows = json.loads(m.group(0)) if m else []
    except ValueError:
        return {}
    out = {}
    for r in rows if isinstance(rows, list) else []:
        if not isinstance(r, dict) or not isinstance(r.get("i"), int) or not 0 <= r["i"] < len(reps):
            continue
        cat = r.get("cat") if r.get("cat") in PICK_CATS else "기타 업계"
        same = r.get("same") if isinstance(r.get("same"), int) and 0 <= r["same"] < len(reps) and r["same"] != r["i"] else None
        out[r["i"]] = {"keep": bool(r.get("keep")), "cat": cat, "why": str(r.get("why") or "")[:90], "ai": True, "same": same}
    return out


def curate(items: list[dict], api_key: str | None) -> list[dict]:
    """items에 grp·pick을 채우고, 고른 소식(picks) 목록을 돌려준다."""
    grp = cluster(items)
    members: dict[int, list[int]] = {}
    for i, g in grp.items():
        members.setdefault(g, []).append(i)

    def rank(i):   # 대표 기사: 전문지 > AI 요약 있음 > 요약 있음 > 먼저 나온 기사
        it = items[i]
        return (0 if TRADE_PRESS.search(it.get("source", "")) else 1, 0 if it.get("summary_ai") else 1, 0 if it.get("summary") else 1, it.get("ts", ""))
    reps = {g: min(ms, key=rank) for g, ms in members.items()}
    for i, g in grp.items():
        items[i]["grp"] = key_of(items[reps[g]]["title"])
    # 판단이 필요한 대표 기사: 아직 판단이 없거나, 규칙으로만 판단했는데 이제 키가 있는 경우
    todo = [r for r in reps.values() if "pick" not in items[r] or (api_key and not items[r]["pick"].get("ai"))]
    todo.sort(key=lambda r: items[r].get("ts", ""), reverse=True)
    merged_into: dict[int, int] = {}
    if api_key and todo:
        print(f"핵심 소식 선별 {len(todo)}건 (Claude)")
        for s0 in range(0, len(todo), 40):
            batch = todo[s0:s0 + 40]
            try:
                res = ai_picks([items[r] for r in batch], api_key)
            except Exception as exc:
                print(f"  선별 실패: {type(exc).__name__}: {str(exc)[:80]}")
                res = {}
            for n, r in enumerate(batch):
                if n in res:
                    p = res[n]
                    if p.get("same") is not None:
                        merged_into[r] = batch[p["same"]]
                    items[r]["pick"] = {k: v for k, v in p.items() if k != "same"}
    for r in reps.values():
        if "pick" not in items[r]:
            items[r]["pick"] = rule_pick(items[r])
    picks = []
    extra: dict[int, list[int]] = {}
    for r, to in merged_into.items():     # 모델이 같은 사건이라고 본 묶음은 살아남은 쪽의 「다른 매체」로 센다
        extra.setdefault(to, []).extend(members[grp[r]])
    for g, r in reps.items():
        it = items[r]
        if not it["pick"].get("keep"):
            continue
        others = [i for i in members[g] if i != r] + extra.get(r, [])
        also = []
        for i in others:
            src = items[i].get("source", "")
            if src and src != it.get("source") and src not in also:
                also.append(src)
        picks.append({"title": it["title"], "source": it.get("source", ""), "link": it.get("link", ""), "url": it.get("url", ""), "ts": it.get("ts", ""),
                      "tags": it.get("tags", []), "summary": it.get("summary", ""), "summary_ai": bool(it.get("summary_ai")),
                      "cat": it["pick"].get("cat", "기타 업계"), "why": it["pick"].get("why", ""), "ai": bool(it["pick"].get("ai")),
                      "dup": len(others), "also": also[:5]})
    picks.sort(key=lambda p: p["ts"], reverse=True)
    return picks[:MAX_PICKS]


def main() -> int:
    prev = {}
    if OUT_PATH.exists():
        try:
            prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
    found: dict[str, dict] = {}
    ok = fail = 0
    for group, queries in GROUPS:
        for q in queries:
            try:
                for it in search(q):
                    k = key_of(it["title"])
                    cur = found.get(k)
                    if cur is None:
                        it["tags"] = tags_for(it["title"]) or [group]
                        if group not in it["tags"]:
                            it["tags"].append(group)
                        found[k] = it
                    elif group not in cur["tags"]:
                        cur["tags"].append(group)
                ok += 1
            except Exception as exc:
                fail += 1
                print(f"::warning::검색 실패({q}): {type(exc).__name__}: {exc}")
    print(f"검색 {ok}건 성공 / {fail}건 실패 · 새로 찾은 기사 {len(found)}건")
    if ok == 0:
        print("모든 검색이 실패해 이전 값을 유지합니다")
        return 1

    cutoff = (datetime.now(KST) - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d %H:%M")
    merged = {key_of(i["title"]): i for i in (prev.get("items") or []) if i.get("ts", "") >= cutoff and relevant(i.get("title", ""))}   # 필터를 다듬은 뒤에도 옛 기사에 다시 적용
    merged.update(found)
    items = sorted(merged.values(), key=lambda i: i["ts"], reverse=True)[:MAX_ITEMS]
    # 원문 주소·요약이 아직 없는 기사(새 기사 + 이전 실행에서 못 채운 기사)를 최신순으로 채운다
    todo = [i for i in items if "summary" not in i or not i.get("url")][:MAX_NEW_SUMMARIES]
    if todo:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip() or None
        print(f"원문·요약 처리 {len(todo)}건 ({'Claude 요약' if api_key else '본문 앞부분 요약(ANTHROPIC_API_KEY 없음)'})")
        with ThreadPoolExecutor(max_workers=4) as ex:
            for it, res in zip(todo, ex.map(lambda x: enrich(x, api_key), todo)):
                it.update(res)
        done = sum(1 for i in todo if i.get("summary"))
        print(f"  요약 {done}건 · 원문주소 {sum(1 for i in todo if i.get('url'))}건")
    picks = curate(items, os.environ.get("ANTHROPIC_API_KEY", "").strip() or None)
    print(f"핵심 소식 {len(picks)}건 / 전체 {len(items)}건")
    out = {"updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"), "groups": [g for g, _ in GROUPS],
           "keywords": sorted({q for _, qs in GROUPS for q in qs}), "pick_cats": PICK_CATS, "picks": picks, "items": items}

    def core(d):
        return {k: v for k, v in d.items() if k != "updated"}
    if prev and core(prev) == core(out):
        print("변경 없음")
        return 0
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"저장: 기사 {len(items)}건")
    return 0


def curate_only() -> int:
    """검색 없이, 지금 저장된 기사에서 핵심 소식만 다시 고른다(`--curate-only`)."""
    data = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    items = data.get("items") or []
    data["pick_cats"] = PICK_CATS
    data["picks"] = curate(items, os.environ.get("ANTHROPIC_API_KEY", "").strip() or None)
    OUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"핵심 소식 {len(data['picks'])}건 / 전체 {len(items)}건")
    return 0


if __name__ == "__main__":
    sys.exit(curate_only() if "--curate-only" in sys.argv else main())
