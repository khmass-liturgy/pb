import json, ssl, time
from urllib.request import Request, urlopen
from urllib.parse import urlencode
ctx = ssl.create_default_context()
H = {"User-Agent": "Mozilla/5.0 (compatible; pb-probe/1.0)", "Accept": "application/json"}
def get(u):
    try:
        with urlopen(Request(u, headers=H), timeout=60, context=ctx) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, "ERR %s %s" % (type(e).__name__, str(e)[:200])
B = "https://comtradeapi.un.org/public/v1/preview/C/M/HS"
for per in ("202606", "202605", "202604", "202512", "202412"):
    q = urlencode({"reporterCode": "410", "period": per, "cmdCode": "0207,0407", "flowCode": "M", "partnerCode": "0", "maxRecords": "50", "includeDesc": "true"})
    st, body = get(B + "?" + q)
    print("== period", per, st, len(body))
    try:
        j = json.loads(body); rows = j.get("data", [])
        print("  rows", len(rows), "count", j.get("count"))
        for r in rows[:6]: print("  ", r.get("cmdCode"), r.get("period"), r.get("partnerCode"), r.get("netWgt"), r.get("primaryValue"), r.get("qty"), r.get("qtyUnitCode"))
    except Exception:
        print("  body:", body[:300])
    time.sleep(1.2)
# 국가별
q = urlencode({"reporterCode": "410", "period": "202512", "cmdCode": "0207", "flowCode": "M", "maxRecords": "100", "includeDesc": "true"})
st, body = get(B + "?" + q); print("== by partner 0207 202512", st, len(body))
try:
    rows = json.loads(body).get("data", []); rows.sort(key=lambda r: -(r.get("netWgt") or 0))
    for r in rows[:6]: print("  ", r.get("partnerCode"), r.get("partnerDesc"), r.get("netWgt"), r.get("primaryValue"))
except Exception: print(body[:300])
# data.go.kr 접근성
st, body = get("https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList"); print("== data.go.kr customs", st, body[:200])
st, body = get("https://www.kati.net/"); print("== kati", st, len(body))
