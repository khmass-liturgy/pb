#!/usr/bin/env python3
"""USDA NASS 주간 작황 보고서(Crop Progress) → usda_crop_progress/latest.json

「사료곡물 원료 품질평가」 메뉴의 「미국 작황·토양수분」 화면이 읽는다. NASS는 매주 월요일(휴일 다음엔 화요일) 오후 4시(미 동부)에
작황 보고서를 내며, 같은 파일을 Cornell 대학 USDA ESMIS 도서관(usda.library.cornell.edu)이 텍스트(.txt)로 그대로 올린다.
NASS 「Ag Insights」 화면(aginsights.nass.usda.gov)은 서버 렌더링 앱이라 긁을 수 없고 QuickStats API는 개인 키가 필요해서,
키 없이 받을 수 있는 이 텍스트 파일을 쓴다(내용은 같다).

읽는 표(전국 합계 행 「N States」와 「전주」·「전년」 행)
  · 토양수분: 표토(Topsoil)·심토(Subsoil) — 매우 건조/건조/적정/과습 % (전국 48개 주 + 주요 옥수수·대두 주)
  · 작물 진도: 옥수수·대두·겨울밀·봄밀·수수·보리·귀리의 파종·출현·개화·성숙·수확 등 % (올해·전주·작년·5년 평균)
  · 작황 등급: 같은 작물의 매우 나쁨~매우 좋음 % (생육기에만 실림)
숫자는 보고서에 인쇄된 값 그대로이며 계산해 채우지 않는다. 「-」는 0, 「(NA)」는 값 없음(None).

최근 몇 주 흐름(history)도 함께 쌓는다. 처음 실행하면 ESMIS 목록에 있는 최근 호들(약 10주)에서 채우고, 이후엔 새 호만 읽는다.
수집이 실패해도 이전 파일은 그대로 둔다(저장소 공통 규칙). 모든 시각은 KST.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

KST = timezone(timedelta(hours=9))
OUT = Path("usda_crop_progress/latest.json")
PAGE = "https://usda.library.cornell.edu/concern/publications/8336h188j"
HOST = "https://usda.library.cornell.edu"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; pb-usda-crop-progress/1.0)"}
HISTORY_WEEKS = 26
MONTHS = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], 1)}

# 읽을 작물(사료곡물 위주). 키 = 보고서 표 제목의 작물 이름
CROPS = {
    "Corn": ("corn", "옥수수"), "Soybeans": ("soy", "대두"), "Soybean": ("soy", "대두"),
    "Winter Wheat": ("winter_wheat", "겨울밀"), "Spring Wheat": ("spring_wheat", "봄밀"),
    "Sorghum": ("sorghum", "수수"), "Barley": ("barley", "보리"), "Oats": ("oats", "귀리"),
}
STAGES = {
    "Planted": "파종", "Emerged": "출현", "Silking": "개화(수염 출사)", "Blooming": "개화", "Dough": "호숙기", "Dented": "치아기(덴트)",
    "Mature": "성숙", "Setting Pods": "꼬투리 형성", "Dropping Leaves": "낙엽", "Headed": "출수", "Coloring": "착색", "Harvested": "수확",
}
STAGE_ORDER = ["Planted", "Emerged", "Blooming", "Silking", "Setting Pods", "Headed", "Dough", "Coloring", "Dented", "Dropping Leaves", "Mature", "Harvested"]
SOIL_STATES = ["Iowa", "Illinois", "Nebraska", "Minnesota", "Indiana", "Ohio", "Missouri", "Kansas", "South Dakota", "North Dakota", "Texas", "Wisconsin"]
SOIL_STATES_KO = {"Iowa": "아이오와", "Illinois": "일리노이", "Nebraska": "네브래스카", "Minnesota": "미네소타", "Indiana": "인디애나", "Ohio": "오하이오",
                  "Missouri": "미주리", "Kansas": "캔자스", "South Dakota": "사우스다코타", "North Dakota": "노스다코타", "Texas": "텍사스", "Wisconsin": "위스콘신"}


# ── 텍스트 표 읽기 ──────────────────────────────────────────────────────────
def _num(tok: str):
    tok = tok.strip()
    if tok == "-":
        return 0
    if tok.startswith("(NA") or tok in ("NA", "(X)", "(D)"):
        return None
    try:
        return int(tok)
    except ValueError:
        try:
            return float(tok)
        except ValueError:
            return None


ROW = re.compile(r"^(?P<name>[A-Za-z0-9][^:]*?)\s*\.{0,}\s*:\s*(?P<vals>.+?)\s*$")


def split_sections(text: str) -> list[tuple[str, list[str]]]:
    """(제목, 본문 줄들). 제목은 ' - Selected States'/' Condition' 형태의 줄에서 시작한다."""
    lines = text.splitlines()
    heads = []
    for i, l in enumerate(lines):
        if l and not l[0].isspace() and re.search(r" - Selected States|Condition - Selected States|Moisture Condition - Selected States", l):
            heads.append(i)
    out = []
    for k, i in enumerate(heads):
        end = heads[k + 1] if k + 1 < len(heads) else len(lines)
        body = lines[i:end]
        # 다음 표 제목 앞의 「다음 주 예정」 안내에서 끊는다
        for j, l in enumerate(body):
            if l.startswith("Crop Progress and Condition Tables Expected"):
                body = body[:j]
                break
        out.append((lines[i].strip(), body))
    return out


def table_rows(body: list[str], ncols: int) -> dict[str, list]:
    rows: dict[str, list] = {}
    for l in body[1:]:
        m = ROW.match(l)
        if not m:
            continue
        name = re.sub(r"\s*\.+$", "", m.group("name")).strip()
        toks = m.group("vals").split()
        if len(toks) != ncols:
            continue
        vals = [_num(t) for t in toks]
        if name in rows:        # 같은 이름이 둘이면 첫 번째만
            continue
        rows[name] = vals
    return rows


def total_row(rows: dict[str, list]) -> tuple[str, list] | None:
    for k, v in rows.items():
        if re.fullmatch(r"\d+ States?", k):
            return k, v
    return None


def parse_report(text: str) -> dict | None:
    m = re.search(r"Released\s+([A-Z][a-z]+)\s+(\d{1,2}),\s+(\d{4})", text)
    if not m:
        return None
    released = date(int(m.group(3)), MONTHS[m.group(1)], int(m.group(2)))
    wk = None
    w = re.search(r"Week Ending\s*\n?\s*([A-Z][a-z]+)\s+(\d{1,2}),\s+(\d{4})", text)
    if w:
        wk = date(int(w.group(3)), MONTHS[w.group(1)], int(w.group(2)))
    if wk is None:      # 월요일 발표 → 직전 일요일
        wk = released - timedelta(days=(released.weekday() + 1) % 7 or 7)
    res: dict = {"released": released.isoformat(), "week_ending": wk.isoformat(), "week_no": wk.isocalendar()[1],
                 "soil": {}, "progress": [], "condition": []}

    for title, body in split_sections(text):
        # 토양수분
        sm = re.match(r"(Topsoil|Subsoil) Moisture Condition", title)
        if sm:
            rows = table_rows(body, 4)
            kind = "topsoil" if sm.group(1) == "Topsoil" else "subsoil"
            t = total_row(rows)
            if not t:
                continue
            cat = lambda v: {"vs": v[0], "s": v[1], "a": v[2], "sur": v[3]}
            entry = {"states": int(t[0].split()[0]), "now": cat(t[1]),
                     "prev_week": cat(rows["Previous week"]) if "Previous week" in rows else None,
                     "prev_year": cat(rows["Previous year"]) if rows.get("Previous year") and None not in rows["Previous year"] else None}
            res["soil"][kind] = entry
            by = res["soil"].setdefault("by_state", {})
            for st in SOIL_STATES:
                if st in rows and None not in rows[st]:
                    by.setdefault(st, {})[kind] = cat(rows[st])
            continue
        # 작황 등급
        cm = re.match(r"(.+?) Condition - Selected States", title)
        if cm and cm.group(1) in CROPS:
            rows = table_rows(body, 5)
            t = total_row(rows)
            if not t or None in t[1]:
                continue
            cat = lambda v: {"vp": v[0], "p": v[1], "f": v[2], "g": v[3], "e": v[4]}
            key, ko = CROPS[cm.group(1)]
            by = {st: cat(rows[st]) for st in SOIL_STATES if st in rows and None not in rows[st]}
            res["condition"].append({"key": key, "label": ko, "states": int(t[0].split()[0]), "now": cat(t[1]),
                                     "prev_week": cat(rows["Previous week"]) if rows.get("Previous week") and None not in rows["Previous week"] else None,
                                     "prev_year": cat(rows["Previous year"]) if rows.get("Previous year") and None not in rows["Previous year"] else None,
                                     "by_state": by})
            continue
        # 작물 진도
        pm = re.match(r"(Corn|Soybeans|Winter Wheat|Spring Wheat|Sorghum|Barley|Oats) ([A-Za-z ]+?) - Selected States", title)
        if pm and pm.group(2) in STAGES:
            rows = table_rows(body, 4)
            t = total_row(rows)
            if not t:
                continue
            key, ko = CROPS[pm.group(1)]
            ly, pw, now, avg = t[1]
            if now is None:
                continue
            res["progress"].append({"key": f"{key}_{pm.group(2).lower().replace(' ', '_')}", "crop": key, "crop_ko": ko, "stage": pm.group(2),
                                    "stage_ko": STAGES[pm.group(2)], "states": int(t[0].split()[0]),
                                    "this_week": now, "prev_week": pw, "last_year": ly, "avg5": avg,
                                    "by_state": {st: {"this_week": rows[st][2], "avg5": rows[st][3]} for st in SOIL_STATES if st in rows and rows[st][2] is not None}})
    if not res["soil"] and not res["progress"] and not res["condition"]:
        return None
    res["progress"].sort(key=lambda p: (p["crop"], STAGE_ORDER.index(p["stage"]) if p["stage"] in STAGE_ORDER else 99))
    return res


def history_point(rep: dict) -> dict:
    """주별 흐름 한 점 — 화면의 미니 그래프에 쓰는 핵심 값만."""
    h: dict = {"week_ending": rep["week_ending"], "week_no": rep["week_no"]}
    for k in ("topsoil", "subsoil"):
        s = rep["soil"].get(k)
        if s:
            n = s["now"]
            h[k + "_a"] = n["a"]
            h[k + "_a_sur"] = (n["a"] or 0) + (n["sur"] or 0)
            h[k + "_dry"] = (n["vs"] or 0) + (n["s"] or 0)
    for c in rep["condition"]:
        n = c["now"]
        h[c["key"] + "_ge"] = (n["g"] or 0) + (n["e"] or 0)
    for p in rep["progress"]:
        if p["stage"] in ("Harvested", "Planted") and p["crop"] in ("corn", "soy", "winter_wheat"):
            h[p["key"]] = p["this_week"]
            h[p["key"] + "_avg5"] = p["avg5"]
    return h


# ── 수집 ───────────────────────────────────────────────────────────────────
def list_releases() -> list[tuple[str, str]]:
    """ESMIS 목록의 (주소, 날짜표시) — 최신 순."""
    r = requests.get(PAGE, headers=HEADERS, timeout=40)
    r.raise_for_status()
    seen, out = set(), []
    for href in re.findall(r'href="(/sites/default/release-files/\d+/prog[^"]*\.txt)"', r.text):
        if href not in seen:
            seen.add(href)
            out.append((HOST + href, href.rsplit("/", 1)[-1]))
    return out


def fetch_text(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.content.decode("utf-8", errors="replace")


def main() -> int:
    prev = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else None
    try:
        rels = list_releases()
    except Exception as e:  # noqa: BLE001
        print(f"ESMIS 목록을 읽지 못했습니다({type(e).__name__}: {e}) — 이전 자료를 그대로 둡니다.")
        return 0
    if not rels:
        print("목록에서 작황 보고서 파일을 찾지 못했습니다 — 이전 자료를 그대로 둡니다.")
        return 0

    latest_url = rels[0][0]
    if prev and prev.get("report_url") == latest_url and not (len(sys.argv) > 1 and sys.argv[1] == "--full"):
        print("새 작황 보고서 없음.")
        return 0

    hist = {h["week_ending"]: h for h in (prev or {}).get("history", [])}
    want = rels if (not prev or len(hist) < 4 or "--full" in sys.argv) else rels[:1]
    latest_rep = None
    for i, (url, label) in enumerate(want):
        try:
            rep = parse_report(fetch_text(url))
        except Exception as e:  # noqa: BLE001
            print(f"  읽기 실패 {label}: {type(e).__name__}: {e}")
            continue
        if not rep:
            print(f"  표를 찾지 못함 {label}")
            continue
        hist[rep["week_ending"]] = history_point(rep)
        if url == latest_url:
            latest_rep = rep
            latest_rep["report_url"] = url
    if not latest_rep:
        print("최신 보고서를 읽지 못했습니다 — 이전 자료를 그대로 둡니다.")
        return 0

    out = {
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
        "source": "USDA NASS 「Crop Progress」 (ESMIS 텍스트판)",
        "source_url": PAGE, "report_url": latest_url,
        "ag_insights_url": "https://aginsights.nass.usda.gov/",
        **{k: latest_rep[k] for k in ("released", "week_ending", "week_no", "soil", "progress", "condition")},
        "state_names": SOIL_STATES_KO,
        "history": [hist[k] for k in sorted(hist)][-HISTORY_WEEKS:],
    }
    new = json.dumps(out, ensure_ascii=False, indent=1) + "\n"
    old = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    strip = lambda s: re.sub(r'"updated": "[^"]*"', "", s)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if strip(new) != strip(old):
        OUT.write_text(new, encoding="utf-8")
        print(f"갱신: {out['released']} 발표 · {out['week_ending']} 주 · 흐름 {len(out['history'])}주")
    else:
        print("변경 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
