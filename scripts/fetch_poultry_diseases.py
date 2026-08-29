#!/usr/bin/env python3
"""
The Poultry Site — "Diseases of Poultry" 질병 자료 수집 + 한글 번역

https://www.thepoultrysite.com/publications/diseases-of-poultry 의 질병 61종을
받아 본문을 한글로 번역해 poultry_disease/diseases.json 에 저장한다. 화면은
이 파일 하나만 읽어 한글 검색·열람을 처리한다.

왜 미리 번역해서 저장하는가
---------------------------
브라우저에서 그때그때 번역하지 않는다. 구글 번역 무료 엔드포인트는 호출이 몰리면
IP 단위로 429를 주고(실제로 겪었다) 본문이 HTML이라 파싱도 실패한다. 사용자가
검색할 때마다 실패하면 기능 자체가 못 쓰게 되므로, 수집 시점에 번역까지 끝내
결과만 정적 JSON으로 내려준다.

증분 번역
---------
전체 영문이 17만자쯤 되어 매번 다시 번역하면 낭비이고 429도 유발한다. 그래서
이전 결과를 읽어 **영문이 그대로면 기존 번역을 재사용**한다. 이번 실행에서 일부
번역이 실패해도 다음 실행이 빈 곳만 채우므로, 회차를 거듭하며 완성된다.
(부분 실패가 기존 데이터를 지우지 않는다는 이 저장소의 규칙과 같은 취지)

한글 검색
---------
제목 기계번역만으로는 현장에서 쓰는 병명으로 검색이 안 맞는 경우가 많다
(예: MAREK'S DISEASE → "마렉의 병"). 그래서 주요 질병에는 수의 현장에서 실제로
쓰는 이름을 KO_ALIASES에 직접 넣어 검색어에 포함시킨다.
"""

import json
import re
import sys
import time
import html as htmlmod
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

KST = timezone(timedelta(hours=9))
OUT_PATH = Path("poultry_disease/diseases.json")

BASE = "https://www.thepoultrysite.com"
INDEX_URL = f"{BASE}/publications/diseases-of-poultry"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# 본문이 아닌 공통 문구 — 문단 추출에서 제외한다.
# 61종 전부에 붙어 있던 "Sign up to our regular newsletter…"를 놓쳤던 적이 있어
# 뉴스레터 문구는 넓게 잡는다.
BOILER = re.compile(r"Global Ag Media provides|Sign up to our|newsletter|"
                    r"^©|cookie|privacy policy", re.I)

# 현장에서 쓰는 한글 병명. 기계번역 제목만으로는 검색이 안 걸리는 걸 보완한다.
# 키는 URL 슬러그(고정값)라 사이트 제목이 바뀌어도 매칭이 유지된다.
KO_ALIASES = {
    "escherichia-coli-infections": ["대장균증", "대장균 감염", "콜리바실로시스"],
    "salmonelloses": ["살모넬라증", "살모넬라"],
    "paratyphoid-infections": ["파라티푸스"],
    "fowl-cholera": ["가금 콜레라", "닭콜레라"],
    "mycoplasma": ["마이코플라스마", "만성호흡기병", "CRD", "MG", "MS"],
    "necrotic-enteritis": ["괴사성 장염"],
    "botulism": ["보툴리즘", "보툴리누스"],
    "avian-tuberculosis": ["가금 결핵"],
    "egg-drop-syndrome-1976": ["산란저하증후군", "EDS", "감란증후군"],
    "infectious-bursal-disease-gumboro": ["전염성 F낭병", "감보로", "IBD", "감보로병"],
    "infectious-bronchitis-ib": ["전염성 기관지염", "IB"],
    "fowl-pox": ["계두", "가금 두창"],
    "laryngotracheitis": ["전염성 후두기관염", "ILT"],
    "swollen-head-syndrome": ["종창두증후군", "부어오른 머리 증후군", "SHS"],
    "infectious-encephalomyelitis": ["전염성 뇌척수염", "AE"],
    "newcastle-disease": ["뉴캐슬병", "뉴캣슬병", "ND", "가금 뉴캐슬"],
    "reovirus-infections": ["레오바이러스", "바이러스성 관절염"],
    "virusinduced-neoplastic-diseases-mareks-disease": ["마렉병", "마렉씨병", "MD"],
    "lymphoid-leukosis": ["림프성 백혈병", "임파구성 백혈병"],
    "coccidiosis": ["콕시듐증", "콕시디아", "구포자충증"],
    "histomonosis": ["히스토모나스", "흑두병"],
    "ascaridiosis": ["회충증"],
    "knemidokoptosis": ["닭 옴진드기증", "각기병(다리비늘진드기)"],
    "aspergillosis": ["아스페르길루스증", "곰팡이성 폐렴"],
    "candidiasis": ["칸디다증"],
    "aflatoxicosis": ["아플라톡신 중독"],
    "fusariotoxicoses": ["푸사리움 독소중독", "곰팡이독소"],
    "vitamin-e-deficiency": ["비타민E 결핍"],
    "fatty-liver-haemorrhagic-syndrome": ["지방간 출혈 증후군", "FLHS"],
    "slipped-tendon-perosis": ["건활탈", "페로시스"],
    "gout": ["통풍", "요산증"],
    "cage-layer-fatigue": ["케이지 산란계 피로증", "골연화"],
    "deep-pectoral-myopathy": ["심부 흉근병증", "녹색근육병"],
    "amyloidosis": ["아밀로이드증"],
    "pulmonary-hypertension-ascitis-syndrome-in": ["복수증", "폐동맥고혈압증후군"],
    "dyschondroplasia": ["연골이형성증", "TD"],
    "gizzard-impaction-in-turkey-poults": ["근위 폐색"],
    "gastrointestinal-impaction": ["소화관 폐색"],
}


def get(session, url):
    r = session.get(url, timeout=30)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text


def parse_index(html):
    """목록 페이지 → [{id, slug, title_en}]"""
    found = {}
    pat = r'href="(/publications/diseases-of-poultry/(\d+)/([^"#?]+))"[^>]*>([\s\S]{0,200}?)</a>'
    for m in re.finditer(pat, html):
        did, slug = m.group(2), m.group(3)
        title = htmlmod.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(4)))).strip()
        if did not in found or (not found[did]["title_en"] and title):
            found[did] = {"id": did, "slug": slug, "title_en": title,
                          "url": BASE + m.group(1)}
    return [found[k] for k in sorted(found, key=int)]


def parse_detail(html):
    """상세 페이지 → (문단 리스트, 문단별 그림번호, 이미지 목록)

    원문은 문단 앞에 그림번호를 붙여 두고("255.256.257. The Newcastle disease…"),
    같은 번호를 사진의 alt에 넣어 둔다. 그래서 번호를 버리지 않고 들고 있으면
    어느 사진이 어느 설명에 붙는지 그대로 복원할 수 있다.
    """
    i = html.find("<h1")
    seg = html[i if i > 0 else 0:]
    seg = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", "", seg)

    def clean(raw):
        s = htmlmod.unescape(re.sub(r"<[^>]+>", "", raw))
        s = re.sub(r"\s+", " ", s).strip()
        m = re.match(r"^((?:\d{1,4}\.\s*)+)", s)   # 앞머리 그림번호
        nums = re.findall(r"\d{1,4}", m.group(1)) if m else []
        return (s[m.end():].strip() if m else s), nums

    def pic(block):
        """블록 안 첫 본문 사진의 URL (없으면 '')"""
        for tag in re.findall(r"<img[^>]+>", block):
            src = ((re.search(r'src="([^"]+)"', tag) or [None, ""])[1]
                   or (re.search(r'data-src="([^"]+)"', tag) or [None, ""])[1])
            if not src.startswith("http") or "globalagmedia.com" not in src:
                continue
            # 같은 CDN에 로고(svg)도 올라와 있어 본문 사진과 섞인다
            if src.lower().endswith(".svg") or "logo" in src.lower():
                continue
            return src
        return ""

    paras, figs, images = [], [], []
    blocks = re.findall(r'<div class="fig">([\s\S]*?)<div class="break">', seg)
    if blocks:
        # 원문은 사진 한 장과 그 설명을 <div class="fig"> 한 덩어리로 묶어 둔다.
        # 이 구조를 그대로 따라가면 어느 사진이 어느 설명의 것인지 정확히 맞는다.
        # (그림번호로 짝지으려 했더니 61종 중 44종은 번호가 아예 없었다)
        for b in blocks:
            body = " ".join(re.findall(r"<p[^>]*>([\s\S]*?)</p>", b))
            s, nums = clean(body)
            if len(s) < 25 or BOILER.search(s):
                continue
            paras.append(s)
            figs.append(nums)
            images.append(pic(b))
    else:
        # fig 블록이 없는 페이지 — 문단만 뽑고 사진은 붙이지 않는다
        for p in re.findall(r"<p[^>]*>([\s\S]*?)</p>", seg):
            s, nums = clean(p)
            if len(s) > 40 and not BOILER.search(s):
                paras.append(s)
                figs.append(nums)
                images.append("")
    return paras, figs, images


# ── 번역 엔드포인트 ─────────────────────────────────────────────────────────
# 무료 엔드포인트는 호출이 몰리면 IP 단위로 막힌다. 하나만 쓰면 그날 번역이
# 통째로 실패하므로 성격이 다른 셋을 순서대로 시도한다.
# (실측: translate.googleapis.com이 429일 때도 clients5는 정상 응답했다)
def _tr_clients5(text, session):
    r = session.get("https://clients5.google.com/translate_a/t",
                    params={"client": "dict-chrome-ex", "sl": "en", "tl": "ko", "q": text},
                    timeout=20)
    if r.status_code != 200:
        return None
    d = r.json()
    if isinstance(d, list) and d:
        return d[0] if isinstance(d[0], str) else "".join(x for x in d[0] if isinstance(x, str))
    return None


def _tr_gtx(text, session):
    r = session.get("https://translate.googleapis.com/translate_a/single",
                    params={"client": "gtx", "sl": "en", "tl": "ko", "dt": "t", "q": text},
                    timeout=20)
    if r.status_code != 200:
        return None
    return "".join(seg[0] for seg in r.json()[0] if seg[0])


def _tr_mymemory(text, session):
    # 한 번에 보낼 수 있는 길이가 짧아 마지막 수단으로만 쓴다.
    r = session.get("https://api.mymemory.translated.net/get",
                    params={"q": text[:480], "langpair": "en|ko"}, timeout=25)
    if r.status_code != 200:
        return None
    return (r.json().get("responseData") or {}).get("translatedText")


TRANSLATORS = [("clients5", _tr_clients5), ("gtx", _tr_gtx), ("mymemory", _tr_mymemory)]
_tr_stats = {}


def translate(text, session):
    """영→한 번역. 모두 실패하면 None (호출부가 원문을 유지한다)."""
    for name, fn in TRANSLATORS:
        try:
            out = (fn(text, session) or "").strip()
            if out:
                _tr_stats[name] = _tr_stats.get(name, 0) + 1
                return out
        except Exception:
            pass
    _tr_stats["실패"] = _tr_stats.get("실패", 0) + 1
    return None


def save(diseases):
    """지금까지 모은 것을 파일로 쓴다.

    질병 한 종을 끝낼 때마다 호출한다. 전체가 20분 넘게 걸리는데 마지막에 한 번만
    저장하면 중간에 끊겼을 때 전부 날아가고, 다음 실행도 재사용할 번역이 없어
    처음부터 다시 하게 된다.
    """
    payload = {
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
        "source": "The Poultry Site — Diseases of Poultry",
        "url": INDEX_URL,
        "note": "영문 원문을 기계번역한 것으로, 진단·처방의 근거로 쓰기 전에 원문 확인이 필요합니다.",
        "count": len(diseases),
        "diseases": diseases,
    }
    OUT_PATH.parent.mkdir(exist_ok=True)
    tmp = OUT_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(OUT_PATH)   # 원자적 교체 — 중간에 끊겨도 깨진 JSON이 남지 않는다


def load_previous():
    if not OUT_PATH.exists():
        return {}
    try:
        prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    # slug → 이전 항목. 영문이 그대로면 번역을 재사용하기 위한 캐시.
    return {d["slug"]: d for d in prev.get("diseases", []) if d.get("slug")}


def main():
    print("🐔 양계질병 자료 수집 시작\n")
    session = requests.Session()
    session.headers.update(HEADERS)
    prev = load_previous()
    print("  이전 데이터 %d종 (번역 재사용용)" % len(prev))

    try:
        index = parse_index(get(session, INDEX_URL))
    except Exception as e:
        print("❌ 목록 조회 실패: %s: %s" % (type(e).__name__, e))
        sys.exit(1)
    if not index:
        print("❌ 목록이 비어 있음 — 사이트 구조가 바뀌었을 수 있습니다")
        sys.exit(1)
    print("  질병 %d종 발견\n" % len(index))

    diseases, tr_new, tr_reused, failed = [], 0, 0, 0
    for n, item in enumerate(index, 1):
        slug = item["slug"]
        old = prev.get(slug, {})
        try:
            paras_en, figs, images = parse_detail(get(session, item["url"]))
        except Exception as e:
            print("  [%2d/%d] %-38s ⚠️ 본문 실패(%s) → 이전 값 유지"
                  % (n, len(index), slug[:36], type(e).__name__))
            if old:
                diseases.append(old)
            failed += 1
            continue

        if not paras_en and old.get("paras_en"):
            paras_en = old["paras_en"]
            figs = old.get("figs") or [[] for _ in paras_en]
            images = old.get("images") or ["" for _ in paras_en]

        # 제목 번역 (영문이 같으면 재사용)
        if old.get("title_en") == item["title_en"] and old.get("title_ko"):
            title_ko = old["title_ko"]
        else:
            title_ko = translate(item["title_en"].title(), session) or item["title_en"]
            time.sleep(0.4)

        # 본문 번역 — 문단 단위로, 영문이 같은 문단은 기존 번역 재사용
        old_map = dict(zip(old.get("paras_en", []), old.get("paras_ko", [])))
        paras_ko = []
        for en in paras_en:
            ko = old_map.get(en)
            if ko:
                paras_ko.append(ko)
                tr_reused += 1
                continue
            ko = translate(en, session)
            if ko:
                tr_new += 1
            else:
                ko = en          # 번역 실패 시 원문 유지 → 다음 실행에서 재시도
                failed += 1
            paras_ko.append(ko)
            time.sleep(0.4)

        aliases = KO_ALIASES.get(slug, [])
        # 표제어는 별칭이 있으면 그쪽을 쓴다. 원문 제목이 전부 대문자라
        # 기계번역이 약어를 망가뜨린다("INFECTIOUS BRONCHITIS (IB)" → "…(Ib)").
        # 별칭은 현장에서 쓰는 정식 병명이라 표제어로 더 적합하다.
        if aliases:
            title_ko = aliases[0]
        # 검색 문자열은 저장하지 않는다 — 한글 본문을 통째로 복제하는 셈이라
        # 파일이 두 배가 된다. 화면에서 불러올 때 만들어 쓴다(buildDiseaseSearch).
        diseases.append({
            "id": item["id"], "slug": slug, "url": item["url"],
            "title_en": item["title_en"], "title_ko": title_ko,
            "aliases": aliases,
            "paras_en": paras_en, "paras_ko": paras_ko,
            "figs": figs, "images": images,
        })
        print("  [%2d/%d] %-38s 문단 %d 사진 %d  %s"
              % (n, len(index), slug[:36], len(paras_en), len(images), title_ko[:22]), flush=True)
        save(diseases)          # 한 종 끝날 때마다 저장 — 중단돼도 여기까지는 남는다
        time.sleep(0.3)

    if not diseases:
        print("❌ 수집 결과 없음 — 기존 파일 유지")
        sys.exit(1)

    save(diseases)

    # 번역이 아직 안 끝난(원문 그대로인) 문단 수 — 다음 실행이 채운다
    pending = sum(1 for d in diseases for en, ko in zip(d["paras_en"], d["paras_ko"]) if en == ko)
    print("\n✅ %d종 저장 (%.0fKB)" % (len(diseases), OUT_PATH.stat().st_size / 1024))
    print("   번역: 신규 %d문단 / 재사용 %d문단 / 미번역 %d문단"
          % (tr_new, tr_reused, pending))
    if _tr_stats:
        print("   번역 경로별: %s" % ", ".join("%s %d" % kv for kv in sorted(_tr_stats.items())))
    if pending:
        print("   ※ 미번역 문단은 다음 실행에서 다시 시도합니다")


if __name__ == "__main__":
    main()
