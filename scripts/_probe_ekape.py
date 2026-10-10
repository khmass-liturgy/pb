import re, ssl
from urllib.request import Request, urlopen
from urllib.parse import urlencode
ctx = ssl.create_default_context()
H = {"User-Agent": "Mozilla/5.0 (compatible; pb-probe/1.0)", "Accept-Language": "ko-KR,ko;q=0.9", "Content-Type": "application/x-www-form-urlencoded"}
def req(u, data=None):
    try:
        r = Request(u, headers=H, data=urlencode(data).encode() if data else None)
        with urlopen(r, timeout=40, context=ctx) as x:
            return x.read().decode("utf-8", "replace")
    except Exception as e:
        return "ERR %s %s" % (type(e).__name__, e)
def dates(t):
    d = sorted(set(re.findall(r"(20\d\d[-.]\d\d[-.]\d\d)", t)))
    return len(d), (d[0], d[-1]) if d else None
U = "https://www.ekapepia.com/v3/price/livestock/egg/distrPrice.do?menuSn=36&boardInfoNo="
t = req(U)
print("BASE", len(t), dates(t))
for m in re.finditer(r"searchStartDate", t):
    s = max(0, m.start() - 250); print("CTX:", re.sub(r"\s+", " ", t[s:m.start() + 350])); print("----")
    break
i = t.find("<form")
fs = [m.start() for m in re.finditer(r"<form", t)]
for f in fs[:4]:
    print("FORM:", re.sub(r"\s+", " ", t[f:f + 500])); print("----")
for m in re.finditer(r"function\s+(\w*[sS]earch\w*|\w*[Ss]ubmit\w*)\s*\(", t):
    s = m.start(); print("FN:", re.sub(r"\s+", " ", t[s:s + 600])); print("----")
tests = [
 ("GET ymd", U + "&" + urlencode({"searchStartDate": "2021-01-01", "searchEndDate": "2021-12-31"})),
 ("GET ymd nodash", U + "&" + urlencode({"searchStartDate": "20210101", "searchEndDate": "20211231"})),
 ("GET radio", U + "&" + urlencode({"radioChk": "1", "searchStartDate": "2021-01-01", "searchEndDate": "2021-12-31", "startYYMMDD": "2021-01-01", "endYYMMDD": "2021-12-31"})),
]
for n, u in tests:
    x = req(u); print(n, len(x), dates(x), x[:120].replace("\n", " ") if x.startswith("ERR") else "")
for n, d in [("POST A", {"menuSn": "36", "boardInfoNo": "", "searchStartDate": "2021-01-01", "searchEndDate": "2021-12-31"}),
             ("POST B", {"menuSn": "36", "boardInfoNo": "", "radioChk": "1", "startYYMMDD": "2021-01-01", "endYYMMDD": "2021-12-31", "searchStartDate": "2021-01-01", "searchEndDate": "2021-12-31"}),
             ("POST C", {"menuSn": "36", "boardInfoNo": "", "radioChk": "2", "startYYMM": "2021-01", "endYYMM": "2021-12"})]:
    x = req("https://www.ekapepia.com/v3/price/livestock/egg/distrPrice.do", d); print(n, len(x), dates(x), x[:120].replace("\n", " ") if x.startswith("ERR") else "")
    ds = re.findall(r"(20\d\d-\d\d-\d\d)", x); print("  sample dates:", sorted(set(ds))[:3], sorted(set(ds))[-3:])
