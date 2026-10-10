import json, ssl, time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode
ctx = ssl.create_default_context()
H = {"User-Agent": "Mozilla/5.0 (compatible; pb-probe/1.0)", "Accept": "application/json"}
def get(u, tries=5):
    for i in range(tries):
        try:
            with urlopen(Request(u, headers=H), timeout=60, context=ctx) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except HTTPError as e:
            if e.code == 429:
                w = 15 * (i + 1); print("   429 → wait", w); time.sleep(w); continue
            return e.code, str(e)
        except Exception as e:
            return 0, "ERR %s %s" % (type(e).__name__, str(e)[:200])
    return 429, "gave up"
B = "https://comtradeapi.un.org/public/v1/preview/C/M/HS"
def q(period, cmd, partner=None):
    d = {"reporterCode": "410", "period": period, "cmdCode": cmd, "flowCode": "M", "maxRecords": "500", "includeDesc": "true"}
    if partner is not None: d["partnerCode"] = partner
    return B + "?" + urlencode(d)
# 월별 세계 합계: 기간 목록 한 번에
for label, periods in (("2025 H1", "202501,202502,202503,202504,202505,202506"), ("2025 H2", "202507,202508,202509,202510,202511,202512"), ("2026 H1", "202601,202602,202603,202604,202605,202606")):
    st, body = get(q(periods, "0207,040711,040721,040790", "0"))
    print("==", label, st, len(body))
    try:
        rows = json.loads(body).get("data", [])
        print("  rows", len(rows))
        for r in sorted(rows, key=lambda r: (r["cmdCode"], r["period"])): print("   ", r["cmdCode"], r["period"], r.get("netWgt"), r.get("primaryValue"))
    except Exception: print("  ", body[:300])
    time.sleep(8)
# 국가별(0207, 2025-06)
st, body = get(q("202506", "0207")); print("== partners 0207 202506", st, len(body))
try:
    rows = json.loads(body).get("data", []); rows.sort(key=lambda r: -(r.get("netWgt") or 0))
    for r in rows[:8]: print("   ", r.get("partnerCode"), r.get("partnerDesc"), r.get("netWgt"), r.get("primaryValue"))
except Exception: print(body[:300])
