#!/usr/bin/env python3
"""육용종계 사육현황(육성계·성계)과 초생추 병아리 생산잠재력 — KREI 육계관측 월보 → broiler_breeder/latest.json

자료원: KREI 농업관측센터 「축산관측 육계」 월보(aglook.krei.re.kr). 월보 2쪽의 「종계 사육 동향」(월말 종계 전체·성계 마릿수,
종계 입식·도태)과 3쪽의 「병아리 입식 마릿수 추정」이 이 화면의 원자료다. 대한양계협회 종계 DB·생산통계는 회원 전용이라 수집하지 않는다.
월보 PDF는 글자가 그림으로 들어 있어 텍스트를 뽑을 수 없으므로, 새 호가 올라오면 해당 쪽을 이미지로 만들어 Claude(비전)가 표를 읽게 하고,
읽은 값이 말이 되는지(성계 ≤ 전체, 직전 값과 비슷한지) 검사한 뒤에만 broiler_breeder/data.json 에 합친다.

· broiler_breeder/data.json   — 월별 원자료(사람이 읽고 확인한 값 + 이 스크립트가 합친 값). 이 파일이 원본이다.
· broiler_breeder/latest.json — 화면이 읽는 파일: data.json + 예측(성계 흐름, 병아리 생산능력) + 백테스트.

예측 모델(전부 이 파일 안에서 계산, 외부 모델 없음):
  ① 성계 흐름: Δ성계(t) = a·종계입식(t−L) − b·종계도태(t). 입식한 병아리가 약 L개월 뒤 성계(산란 가능)가 된다는 구조이고,
     L·a·b 는 월보 자료로 최소제곱 추정(L은 4~7 중 오차가 가장 작은 값). 입식은 이미 아는 값이라 L개월 앞까지 계산되며,
     미래 도태는 최근 12개월 평균으로 둔다(도태는 AI 살처분·노계 정리에 좌우돼 가장 불확실한 값).
  ② 병아리 생산능력: 월 병아리 입식 ≈ 계수 × 전월 성계 마릿수(계수 = 병아리 입식 ÷ 전월 성계, 만 마리/천 마리). 계수 추정 방식
     (전체 평균 / 최근 12개월 / 계절 보정)은 롤링 백테스트 오차가 가장 작은 것을 고른다.
  ③ 평가: 같은 달 전년 입식을 그대로 쓴 값보다 나을 때만 「보통」, 아니면 「낮음」, 표본이 모자라면 「검증 불가」.
     병아리 입식은 성계 외에 작업일수·육계 수요·수입 종란에도 좌우되므로 이 값은 입식 예측이 아니라 「성계 기준 생산능력」이다.

실행: python scripts/fetch_broiler_breeder.py            (새 호 확인 → 합치기 → 예측)
      OFFLINE=1 python scripts/fetch_broiler_breeder.py   (내려받기 없이 data.json 으로 예측만 다시 계산)
모든 시각은 KST. 내려받기·읽기에 실패해도 기존 data.json 은 그대로 두고 예측만 갱신한다.
"""

from __future__ import annotations

import base64
import io
import json
import math
import os
import re
import statistics as st
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "broiler_breeder" / "data.json"
OUT = ROOT / "broiler_breeder" / "latest.json"

LIST_URL = "https://aglook.krei.re.kr/main/uObserveMonth/OVR0000000014"
DOWNLOAD = "https://aglook.krei.re.kr/main/uObserveMonth/OVR0000000014/download/{id}/ORGTEXT_FILE"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-sonnet-5"
ANTHROPIC_MODEL_FALLBACK = "claude-3-5-sonnet-20241022"

DEFAULT_CULL = 450          # 도태 자료가 6개월도 안 쌓였을 때만 쓰는 값(천 마리/월)
Z80 = 1.28                  # 80% 구간


# ── 달 계산 ────────────────────────────────────────────────────────────────
def shift(ym: str, k: int) -> str:
    y, m = int(ym[:4]), int(ym[5:7])
    m += k
    y += (m - 1) // 12
    m = (m - 1) % 12 + 1
    return f"{y}-{m:02d}"


# ── 새 월보 읽기(KREI) ──────────────────────────────────────────────────────
PROMPT = """첨부는 한국농촌경제연구원(KREI) 농업관측센터 「축산관측 육계」 월보의 2쪽과 3쪽 이미지다. 표에 인쇄된 숫자를 그대로 읽어 JSON만 출력하라(설명·코드블록 금지).
없는 값은 null. 추측하거나 계산해 채우지 말 것. 쪽수 표시(예: 「축산관측 2026년 10월호 육계」)에서 호 정보를 읽어라.

{
 "issue": "YYYY-MM",                      // 3쪽 아래 「축산관측 YYYY년 M월호 육계」
 "breeder_table": [                       // 2쪽 「육용 종계 사육 마릿수 동향」 표, 올해(맨 윗 연도 행)만. 단위 천 마리
   {"ym":"YYYY-MM","total":8414,"adult":4578}   // 위 숫자=종계 전체, 괄호 안=성계
 ],
 "breeder_text": [                        // 2쪽 「사육 마릿수」 글머리 문장에서 읽은 월별 값. 단위 천 마리(예: 61만 5천 마리 → 615)
   {"ym":"YYYY-MM","total":null,"adult":null,"placed":615,"culled":320}
 ],
 "chick_placement": [                     // 3쪽 「육계 병아리 입식 마릿수 추정」 표의 올해 행. 단위 만 마리. 범위면 lo~hi
   {"ym":"YYYY-MM","value":null,"lo":7099,"hi":7235}
 ]
}
"""


def _img_b64(pdf_bytes: bytes, page: int, dpi: int = 130) -> str:
    import pdfplumber
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as p:
        im = p.pages[page].to_image(resolution=dpi).original.convert("RGB")
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def ask_claude(pdf_bytes: bytes, api_key: str) -> dict | None:
    import requests
    content = [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": _img_b64(pdf_bytes, i)}} for i in (1, 2)]
    content.append({"type": "text", "text": PROMPT})
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    for model in (ANTHROPIC_MODEL, ANTHROPIC_MODEL_FALLBACK):
        r = requests.post(ANTHROPIC_URL, headers=headers, timeout=120,
                          json={"model": model, "max_tokens": 2000, "temperature": 0, "messages": [{"role": "user", "content": content}]})
        if r.status_code == 200:
            text = "".join(b.get("text", "") for b in r.json().get("content", []))
            m = re.search(r"\{.*\}", text, flags=re.S)
            if m:
                try:
                    return json.loads(m.group(0))
                except ValueError:
                    return None
            return None
        print(f"Claude {model}: HTTP {r.status_code} {r.text[:160]}")
    return None


def _relay() -> tuple[str, str] | None:
    """국내 중계 서버(farm-pro/sms-relay, Oracle Cloud VM)의 주소·비밀값. 문자 발송·농식품부 수집과 같은 두 시크릿을 쓴다."""
    url = os.environ.get("SMS_RELAY_URL", "").strip()
    secret = os.environ.get("SMS_RELAY_SECRET", "").strip()
    return (re.sub(r"/send-sms/?$", "", url), secret) if url and secret else None


def kreI_get(url: str, ok, timeout: int = 60):
    """KREI 주소를 받는다. 직접 먼저, 막히면(접속 실패·오류 응답·엉뚱한 내용) 국내 중계 서버(/fetch-krei)로 우회한다.
    ok(response) 가 True 인 응답만 돌려주고, 둘 다 실패하면 RuntimeError."""
    import requests
    why: list[str] = []
    try:
        r = requests.get(url, headers=UA, timeout=timeout)
        if r.status_code == 200 and ok(r):
            return r
        why.append(f"직접 접속 HTTP {r.status_code}")
    except Exception as e:  # noqa: BLE001
        why.append(f"직접 접속 실패 {type(e).__name__}")
    relay = _relay()
    if relay:
        base, secret = relay
        try:
            r = requests.get(f"{base}/fetch-krei", params={"url": url}, headers={**UA, "Authorization": f"Bearer {secret}"}, timeout=timeout + 30)
            if r.status_code == 200 and ok(r):
                print("직접 접속이 안 돼 국내 중계 서버로 받았습니다.")
                return r
            why.append(f"중계 서버 HTTP {r.status_code}")
        except Exception as e:  # noqa: BLE001
            why.append(f"중계 서버 실패 {type(e).__name__}")
    else:
        why.append("중계 서버 설정(SMS_RELAY_URL/SMS_RELAY_SECRET) 없음")
    raise RuntimeError(" · ".join(why))


def newest_report_id() -> str | None:
    r = kreI_get(LIST_URL, lambda r: "ORGTEXT_FILE" in r.text, timeout=30)
    ids = re.findall(r"/download/(\d+)/ORGTEXT_FILE", r.text)
    return ids[0] if ids else None


def plausible(rec: dict, prev: dict | None) -> bool:
    """읽은 값이 말이 되는지 — 틀리게 읽은 숫자를 데이터에 섞지 않으려는 최소 검사."""
    t, a = rec.get("total"), rec.get("adult")
    if t is not None and not 6000 <= t <= 11000:
        return False
    if a is not None and not 3000 <= a <= 7000:
        return False
    if t is not None and a is not None and a >= t:
        return False
    if prev:
        for k, tol in (("total", 0.12), ("adult", 0.2)):
            if rec.get(k) is not None and prev.get(k) and abs(rec[k] / prev[k] - 1) > tol:
                return False
    for k, lo, hi in (("placed", 100, 1500), ("culled", 50, 1500)):
        if rec.get(k) is not None and not lo <= rec[k] <= hi:
            return False
    return True


def merge_report(data: dict, got: dict) -> int:
    """읽은 값을 data['months'] 에 합친다. 같은 달이면 새 값(더 최근 호)이 이긴다. 합친 달 수를 돌려준다."""
    months = {m["ym"]: m for m in data["months"]}
    issue = got.get("issue")
    changed = 0
    rows: dict[str, dict] = {}
    for r in (got.get("breeder_table") or []) + (got.get("breeder_text") or []):
        if not r or not re.fullmatch(r"\d{4}-\d{2}", str(r.get("ym", ""))):
            continue
        rows.setdefault(r["ym"], {}).update({k: v for k, v in r.items() if k != "ym" and isinstance(v, (int, float))})
    for ym in sorted(rows):
        rec = rows[ym]
        prev = months.get(shift(ym, -1))
        if not plausible(rec, prev):
            print(f"  건너뜀(이상한 값) {ym}: {rec}")
            continue
        cur = months.setdefault(ym, {"ym": ym})
        before = dict(cur)
        for k in ("total", "adult", "placed", "culled"):
            if k in rec:
                cur[k] = int(round(rec[k]))
        if issue and ym >= shift(issue, -3):
            cur["flags"] = sorted(set(cur.get("flags", [])) | ({"kreI_est"} if ym[:4] >= "2026" else set()))
        changed += cur != before
    for r in got.get("chick_placement") or []:
        ym = str(r.get("ym", ""))
        if not re.fullmatch(r"\d{4}-\d{2}", ym):
            continue
        v = r.get("value")
        mid = False
        if v is None and r.get("lo") and r.get("hi"):
            v, mid = (r["lo"] + r["hi"]) / 2, True
        if v is None or not 4500 <= v <= 9500:
            continue
        cur = months.setdefault(ym, {"ym": ym})
        # 범위 중간값은 이미 확정(비-중간값) 치가 있으면 덮지 않는다.
        if mid and "chick" in cur and "chick_mid" not in cur.get("flags", []):
            continue
        before = dict(cur)
        cur["chick"] = int(round(v))
        fl = set(cur.get("flags", []))
        (fl.add if mid else fl.discard)("chick_mid")
        cur["flags"] = sorted(fl) or None
        if not cur["flags"]:
            del cur["flags"]
        changed += cur != before
    data["months"] = [months[k] for k in sorted(months)]
    if issue:
        data["latest_report"] = issue
    return changed


def update_from_kreI(data: dict) -> bool:
    """새 월보가 있으면 읽어 data 에 합친다. 바뀌었으면 True."""
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        print("ANTHROPIC_API_KEY 없음 — 새 월보 읽기를 건너뜁니다.")
        return False
    try:
        fid = newest_report_id()
        if not fid:
            print("월보 목록에서 파일을 찾지 못했습니다.")
            return False
        if data.get("latest_file_id") == fid:
            print(f"새 월보 없음(파일 {fid}).")
            return False
        r = kreI_get(DOWNLOAD.format(id=fid), lambda r: r.content.startswith(b"%PDF"), timeout=90)
        got = ask_claude(r.content, key)
        if not got:
            print("Claude가 표를 읽지 못했습니다 — 이번에는 합치지 않습니다.")
            return False
        print("읽은 값:", json.dumps(got, ensure_ascii=False)[:600])
        merge_report(data, got)
        data["latest_file_id"] = fid
        return True
    except Exception as e:  # noqa: BLE001 — 수집 실패가 기존 자료·예측 갱신을 막지 않게
        print(f"새 월보 확인 실패: {type(e).__name__}: {e}")
        return False


# ── 예측 ───────────────────────────────────────────────────────────────────
def _lstsq2(X: list[tuple[float, float]], Y: list[float]) -> tuple[float, float]:
    sxx = sum(x[0] * x[0] for x in X); sxy = sum(x[0] * x[1] for x in X); syy = sum(x[1] * x[1] for x in X)
    sxY = sum(x[0] * y for x, y in zip(X, Y)); syY = sum(x[1] * y for x, y in zip(X, Y))
    det = sxx * syy - sxy * sxy
    return (sxY * syy - syY * sxy) / det, (sxx * syY - sxy * sxY) / det


def fit_adult(A: dict[str, float], P: dict[str, float], C: dict[str, float]) -> dict | None:
    best = None
    for L in range(4, 8):
        X, Y, keys = [], [], []
        for m in sorted(A):
            if shift(m, -1) in A and m in C and shift(m, -L) in P:
                X.append((P[shift(m, -L)], -C[m])); Y.append(A[m] - A[shift(m, -1)]); keys.append(m)
        if len(Y) < 8:
            continue
        try:
            a, b = _lstsq2(X, Y)
        except ZeroDivisionError:
            continue
        rmse = math.sqrt(sum((y - (a * x[0] + b * x[1])) ** 2 for x, y in zip(X, Y)) / len(Y))
        # b 는 도태가 성계를 줄이는 비율이라 양수(여기서는 X 에 −도태를 넣어 b>0 이 정상)
        if not (0.2 <= a <= 1.2 and 0.3 <= b <= 1.5):
            continue
        if best is None or rmse < best["rmse"]:
            best = {"L": L, "a": a, "b": b, "rmse": rmse, "n": len(Y), "sd_delta": st.pstdev(Y)}
    return best


def ratio_estimators(ratio: dict[str, float]):
    def est(kind: str, t: str):
        past = [m for m in sorted(ratio) if m < t]
        if len(past) < 10:
            return None
        if kind == "all":
            return st.mean(ratio[m] for m in past)
        if kind == "r12":
            return st.mean(ratio[m] for m in past[-12:])
        base = st.mean(ratio[m] for m in past)           # seas: 전체 평균과 같은 달 평균을 반반
        same = [ratio[m] for m in past if m[5:] == t[5:]]
        return base if not same else 0.5 * base + 0.5 * st.mean(same)
    return est


def build_forecast(data: dict) -> dict:
    months = data["months"]
    A, T, P, C, K = {}, {}, {}, {}, {}
    for m in data.get("prev_year", []):
        A[m["ym"]] = m["adult"]; T[m["ym"]] = m["total"]
        if "chick" in m:
            K[m["ym"]] = m["chick"]
    for m in months:
        if "adult" in m:
            A[m["ym"]] = m["adult"]; T[m["ym"]] = m["total"]
        if "placed" in m:
            P[m["ym"]] = m["placed"]
        if "culled" in m:
            C[m["ym"]] = m["culled"]
        if "chick" in m:
            K[m["ym"]] = m["chick"]
    last = max(m["ym"] for m in months if "adult" in m)
    out: dict = {"last_ym": last, "adult_forecast": [], "chick_potential": [], "model": {}}

    # ① 성계 흐름
    fit = fit_adult({m: A[m] for m in A if m >= "2025-01"}, P, C)
    culls12 = [C[m] for m in sorted(C) if m <= last][-12:]
    cull_base = st.mean(culls12) if len(culls12) >= 6 else DEFAULT_CULL
    model = {"cull_assumed": round(cull_base), "cull_months": len(culls12)}
    adult_path: dict[str, float] = {last: A[last]}
    if fit:
        model.update({"L": fit["L"], "a": round(fit["a"], 3), "b": round(fit["b"], 3), "adult_rmse": round(fit["rmse"]),
                      "adult_sd_delta": round(fit["sd_delta"]), "adult_n": fit["n"]})
        for h in range(1, 7):
            m = shift(last, h)
            src = shift(m, -fit["L"])
            if src not in P:
                break
            a_new = adult_path[shift(m, -1)] + fit["a"] * P[src] - fit["b"] * cull_base
            adult_path[m] = a_new
            sd = fit["rmse"] * math.sqrt(h)
            ly = A.get(shift(m, -12))
            out["adult_forecast"].append({
                "ym": m, "adult": round(a_new), "lo": round(a_new - Z80 * sd), "hi": round(a_new + Z80 * sd),
                "entering": P[src], "entering_ym": src, "yoy_pct": round((a_new / ly - 1) * 100, 1) if ly else None})
    else:
        model["note"] = "성계 흐름을 추정할 자료가 부족합니다."

    # ② 병아리 생산능력
    ratio = {m: K[m] / A[shift(m, -1)] for m in K if shift(m, -1) in A}
    est = ratio_estimators(ratio)
    tests = [m for m in sorted(ratio) if m >= "2025-01"]
    scores: dict[str, list[float]] = {}
    for kind in ("all", "r12", "seas"):
        e = []
        for t in tests:
            k = est(kind, t)
            if k is not None:
                e.append((k * A[shift(t, -1)] - K[t]) / K[t])
        if e:
            scores[kind] = e
    mape = {k: st.mean(abs(x) for x in v) for k, v in scores.items()}
    chosen = min(mape, key=mape.get) if mape else None
    naive_e = [abs(K[shift(t, -12)] - K[t]) / K[t] for t in tests if shift(t, -12) in K]
    model["ratio_method"] = {"all": "전체 평균", "r12": "최근 12개월 평균", "seas": "전체 평균+같은 달 평균(계절 보정)"}.get(chosen)
    model["ratio_mape"] = {k: round(v * 100, 1) for k, v in mape.items()}
    if chosen:
        sd_rel = st.pstdev(scores[chosen])
        bias = st.mean(scores[chosen])
        model["backtest"] = {
            "n": len(scores[chosen]), "mape_pct": round(mape[chosen] * 100, 1), "bias_pct": round(bias * 100, 1),
            "naive_last_year_mape_pct": round(st.mean(naive_e) * 100, 1) if naive_e else None, "naive_n": len(naive_e)}
        beats = bool(naive_e) and mape[chosen] < st.mean(naive_e)
        n_ok = len(scores[chosen]) >= 8
        model["grade"] = "검증 불가" if not n_ok else ("보통" if beats and mape[chosen] < 0.08 else "낮음")
        model["grade_why"] = ("같은 달 전년 입식을 그대로 쓴 값보다 오차가 작아 「보통」." if model["grade"] == "보통" else
                              "표본이 적어 검증하기 어렵다." if model["grade"] == "검증 불가" else
                              "같은 달 전년 입식을 그대로 쓴 값보다 오차가 커서 입식 예측으로는 쓰지 말고 성계 기준 생산능력 지표로만 본다.")
        ref_a = last
        for h in range(1, 7):
            m = shift(last, h)
            src = shift(m, -1)
            base = A[last] if h == 1 else adult_path.get(src)
            k = est(chosen, m) or est(chosen, shift(last, 1))
            if base is None or k is None:
                break
            v = k * base
            rel = Z80 * math.sqrt(sd_rel ** 2 + ((fit["rmse"] * math.sqrt(max(h - 1, 0)) / base) if fit and h > 1 else 0) ** 2)
            ly = K.get(shift(m, -12))
            kreI = (data.get("kreI_outlook") or {}).get(m)
            out["chick_potential"].append({
                "ym": m, "chick": round(v), "lo": round(v * (1 - rel)), "hi": round(v * (1 + rel)),
                "adult_basis": round(base), "ratio": round(k, 3),
                "last_year_chick": ly, "yoy_pct": round((v / ly - 1) * 100, 1) if ly else None, "kreI": kreI})
    out["model"] = model
    return out


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    if os.environ.get("OFFLINE") != "1" and update_from_kreI(data):
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("data.json 갱신")
    fc = build_forecast(data)
    for m in data["months"]:
        if "total" in m and "adult" in m:
            m["grower"] = m["total"] - m["adult"]
    result = {
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
        "source": data["source"], "source_url": data["source_url"], "latest_report": data["latest_report"],
        "units": data["units"], "notes": data["notes"],
        "months": data["months"], "prev_year": data["prev_year"], "kreI_outlook": data.get("kreI_outlook", {}),
        **fc,
    }
    new = json.dumps(result, ensure_ascii=False, indent=1) + "\n"
    old = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    # 갱신 시각만 다른 경우에는 다시 쓰지 않는다(불필요한 커밋 방지).
    strip = lambda s: re.sub(r'"updated": "[^"]*"', "", s)
    if strip(new) != strip(old):
        OUT.write_text(new, encoding="utf-8")
        print("latest.json 갱신")
    else:
        print("변경 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
