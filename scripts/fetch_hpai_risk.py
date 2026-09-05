#!/usr/bin/env python3
"""
WOAH WAHIS — 고병원성 조류인플루엔자(HPAI) 발생 현황 수집

무엇을 만드는가
---------------
"발생위험도"를 한 숫자로 계산해 주는 공개 모델은 찾지 못했다. 실제로 존재하는
전 세계 위험도 모델은 Dellicour 등의 생태적소모델(eLife, Boosted Regression
Trees)인데, 배포되는 것이 480MB짜리 입력자료·R 스크립트 묶음이라 정적
대시보드가 주기적으로 받아 쓸 수 있는 국가별 위험도 수치가 아니다.

그래서 이 스크립트는 위험도 점수를 지어내지 않는다. 대신 WOAH(세계동물보건기구)
WAHIS에 각국이 공식 신고한 **관측된 발생 사실**을 모아, 아래 세 축으로 정리한다.
위험 판단의 근거가 되는 규칙은 JSON에 그대로 담아 화면에 표시한다.

  ① 야생조류 vs 가금 — WAHIS가 질병 코드로 구분해 신고받는다
       668 High pathogenicity avian influenza viruses (poultry)
       671 Influenza A viruses of high pathogenicity (non-poultry including wild birds)
     EFSA 분기보고서는 가금 발생의 90% 이상이 야생조류로부터의 1차 유입이라고
     보고한다. 즉 야생조류 검출은 가금 발생의 선행지표로 볼 근거가 있다.
  ② 철새 이동경로 — 한반도가 속한 동아시아-대양주 철새경로(EAAF) 국가를 표시한다.
  ③ 대륙/지역 — WAHIS 자체 지역 구분을 그대로 쓴다(임의로 나누지 않는다).

주의: 여기서 매기는 단계(level)는 검증된 위험도 모델이 아니라 관측값을 정해진
규칙으로 분류한 것이다. 규칙은 LEVEL_RULE에 문자열로 담아 화면에 노출한다.

API 메모
--------
- POST https://wahis.woah.org/api/v1/pi/event/filtered-list  (인증 불필요)
  GET으로 부르면 400. 서버측 질병 필터 파라미터는 형식을 찾지 못해
  (diseases/disease/diseaseIds/firstLevelDisease 모두 무시됨) 최신순으로
  여러 페이지를 받아 질병명으로 직접 걸러낸다.
- 최소 헤더(Content-Type만)로도 200이 온다 — CI에서 안전.
"""

import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

KST = timezone(timedelta(hours=9))
OUT_PATH = Path("hpai_risk/latest.json")

BASE = "https://wahis.woah.org/api/v1/pi"
EVENT_URL = f"{BASE}/event/filtered-list?language=en"
COUNTRY_URL = f"{BASE}/country/list?language=en"
REGION_URL = f"{BASE}/country/list-geo-region?language=en"
HUMAN_URL = "https://wahis.woah.org/#/event-management"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

PAGES = 8          # 8페이지(800건)면 대략 9개월치가 들어온다
PAGE_SIZE = 100
WINDOW_DAYS = 180  # 집계 대상 기간

# 동아시아-대양주 철새경로(EAAF) 국가 — EAAFP가 밝히는 22개국에
# 지리적으로 경로상에 있는 대만(Chinese Taipei)을 더했다.
# 한국 양계 관점에서 가장 중요한 선행 관찰 대상이라 별도 축으로 둔다.
EAAF_ISO = {
    "USA", "RUS", "MNG", "CHN", "PRK", "KOR", "JPN", "PHL", "VNM", "LAO",
    "THA", "KHM", "MMR", "BGD", "IND", "MYS", "SGP", "BRN", "IDN", "TLS",
    "PNG", "AUS", "NZL", "TWN",
}
KOREA_ISO = "KOR"

# 화면에 그대로 띄울 분류 규칙 — 근거 없는 점수가 아니라는 걸 사용자가 알 수 있게 한다.
LEVEL_RULE = (
    "최근 180일 신고를 기준으로 분류 — "
    "진행중: WOAH에 '진행중(On-going)'으로 신고된 발생이 있음 · "
    "최근신고: 진행중은 없으나 90일 내 신고가 있음 · "
    "소강: 90일 넘게 신고 없음"
)


def is_hpai(name):
    """HPAI 이벤트인지 (가금 668 / 비가금·야생조류 671 두 질병명 모두 매칭)"""
    n = (name or "").lower()
    return "influenza" in n and "high pathogenic" in n.replace("pathogenicity", "pathogenic")


def is_wild(name):
    """야생조류 포함 비가금 쪽 신고인지"""
    return "non-poultry" in (name or "").lower()


def get_json(session, url):
    r = session.get(url, timeout=40)
    r.raise_for_status()
    return r.json()


def fetch_events(session):
    """최신순으로 PAGES 페이지를 받아 HPAI 이벤트만 추린다.

    WAHIS는 페이지 하나가 가끔 60초를 넘겨 응답 없이 끊긴다(실제로 3페이지째에서
    ReadTimeout이 나 전체 수집이 실패한 적이 있다). 페이지 하나가 느린 것이지
    서버가 완전히 죽은 게 아니므로, 그 페이지만 짧게 재시도하고 그래도 안 되면
    포기한다 — 타임아웃을 무작정 늘리는 것보다 실행 시간을 예측 가능하게 유지한다.
    """
    events = []
    for page in range(1, PAGES + 1):
        body = {"pageNumber": page, "pageSize": PAGE_SIZE, "searchText": "",
                "sortColName": "", "sortColOrder": "DESC", "reportFilters": {}}
        rows = None
        for attempt in range(3):
            try:
                r = session.post(EVENT_URL, json=body, timeout=90)
                r.raise_for_status()
                rows = r.json().get("list", [])
                break
            except requests.exceptions.RequestException as e:
                print("  page %d 시도 %d/3 실패: %s" % (page, attempt + 1, type(e).__name__))
                if attempt < 2:
                    time.sleep(5 * (attempt + 1))
        if rows is None:
            raise RuntimeError("page %d 요청이 3회 모두 실패함 (마지막 페이지까지 못 받음)" % page)
        if not rows:
            break
        events += [x for x in rows if is_hpai(x.get("disease"))]
        print("  page %d: %d건 (누적 HPAI %d건)" % (page, len(rows), len(events)))
    return events


def day(s):
    """'2026-08-20T00:00:00.000+00:00' → date"""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s or "")
    return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=KST) if m else None


def build(events, iso_by_name, region_by_iso):
    now = datetime.now(KST)
    cutoff = now - timedelta(days=WINDOW_DAYS)

    per = {}
    for e in events:
        # 기간 판정은 '신고 활동일(submissionDate)' 기준이다. 발생 시작일로 걸면
        # 2024년에 시작해 지금도 진행중인 사례(네덜란드·한국 등)가 통째로 빠져
        # 현재 상황을 오히려 잘못 보여준다. 시작일은 표시용으로만 쓴다.
        submitted = day(e.get("submissionDate"))
        started = day(e.get("eventStartDate")) or submitted
        if not submitted or submitted < cutoff:
            continue
        name = (e.get("country") or "").strip()
        iso = iso_by_name.get(name, "")
        c = per.setdefault(name, {
            "name": name, "iso": iso,
            "region": region_by_iso.get(iso, "기타"),
            "eaaf": iso in EAAF_ISO,
            "poultry": 0, "wild": 0, "ongoing": 0, "latest": None,
        })
        if is_wild(e.get("disease")):
            c["wild"] += 1
        else:
            c["poultry"] += 1
        if (e.get("eventStatus") or "").lower().startswith("on-going"):
            c["ongoing"] += 1
        d = submitted.strftime("%Y-%m-%d")
        if not c["latest"] or d > c["latest"]:
            c["latest"] = d
        s = started.strftime("%Y-%m-%d")
        if not c.get("first") or s < c["first"]:
            c["first"] = s

    countries = []
    for c in per.values():
        c["total"] = c["poultry"] + c["wild"]
        age = (now - day(c["latest"])).days if c["latest"] else 999
        c["days_since"] = age
        c["level"] = "ongoing" if c["ongoing"] else ("recent" if age <= 90 else "quiet")
        countries.append(c)
    countries.sort(key=lambda x: (-x["total"], x["name"]))

    def agg(rows):
        return {
            "countries": len(rows),
            "total": sum(r["total"] for r in rows),
            "poultry": sum(r["poultry"] for r in rows),
            "wild": sum(r["wild"] for r in rows),
            "ongoing": sum(r["ongoing"] for r in rows),
        }

    regions = []
    for rn in sorted({c["region"] for c in countries}):
        rows = [c for c in countries if c["region"] == rn]
        a = agg(rows)
        a["name"] = rn
        a["top"] = [r["name"] for r in rows[:3]]
        regions.append(a)
    regions.sort(key=lambda r: -r["total"])

    eaaf_rows = [c for c in countries if c["eaaf"]]
    korea = next((c for c in countries if c["iso"] == KOREA_ISO), None)

    return {
        "updated": now.strftime("%Y-%m-%d %H:%M KST"),
        "window_days": WINDOW_DAYS,
        "source": "WOAH WAHIS (세계동물보건기구 공식 신고)",
        "url": HUMAN_URL,
        "level_rule": LEVEL_RULE,
        "overall": agg(countries),
        "regions": regions,
        "flyway": {
            "name": "동아시아-대양주 철새경로 (EAAF)",
            "note": "한반도가 속한 철새 이동경로. 경로상 국가의 발생은 국내 유입 위험을 살피는 선행 관찰 대상이다.",
            **agg(eaaf_rows),
            "countries_list": eaaf_rows,
        },
        "korea": korea,
        "countries": countries,
        "stale": False,
    }


def keep_previous(reason):
    if not OUT_PATH.exists():
        print("  이전 데이터 없음 — 파일을 만들지 않음")
        return
    try:
        prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return
    prev["stale"] = True
    prev["stale_reason"] = reason
    prev["checked"] = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    OUT_PATH.write_text(json.dumps(prev, ensure_ascii=False, indent=2), encoding="utf-8")
    print("  ⚡ 이전 데이터 유지 + stale 표시")


def main():
    print("🦠 HPAI 발생 현황 수집 시작\n")
    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        countries_meta = get_json(session, COUNTRY_URL)
        iso_by_name = {c["name"]: c.get("isoCode", "") for c in countries_meta}
        id_to_iso = {c["areaId"]: c.get("isoCode", "") for c in countries_meta}

        region_by_iso = {}
        for reg in get_json(session, REGION_URL):
            for cid in reg.get("countryIds", []):
                iso = id_to_iso.get(cid)
                if iso:
                    region_by_iso[iso] = reg["name"]
        print("  국가 %d개 / 지역 매핑 %d개" % (len(iso_by_name), len(region_by_iso)))

        events = fetch_events(session)
        if not events:
            raise RuntimeError("HPAI 이벤트를 하나도 받지 못함")
        payload = build(events, iso_by_name, region_by_iso)
    except Exception as e:
        print("❌ 수집 실패: %s: %s" % (type(e).__name__, e))
        keep_previous("%s: %s" % (type(e).__name__, e))
        sys.exit(1)

    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    o = payload["overall"]
    print("\n✅ 최근 %d일 · %d개국 %d건 (가금 %d / 야생 %d / 진행중 %d)"
          % (payload["window_days"], o["countries"], o["total"],
             o["poultry"], o["wild"], o["ongoing"]))
    f = payload["flyway"]
    print("   철새경로(EAAF): %d개국 %d건 (진행중 %d)" % (f["countries"], f["total"], f["ongoing"]))
    k = payload["korea"]
    print("   한국: %s" % ("%d건 (가금 %d/야생 %d, 진행중 %d)"
                          % (k["total"], k["poultry"], k["wild"], k["ongoing"]) if k else "신고 없음"))
    for r in payload["regions"][:5]:
        print("   %-16s %4d건 (%d개국)" % (r["name"], r["total"], r["countries"]))


if __name__ == "__main__":
    main()
