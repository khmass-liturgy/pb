import re, ssl, sys
from urllib.request import Request, urlopen
from urllib.parse import quote
ctx = ssl.create_default_context()
H = {"User-Agent": "Mozilla/5.0 (compatible; pb-probe/1.0)", "Accept-Language": "ko-KR,ko;q=0.9"}
def get(u):
    try:
        with urlopen(Request(u, headers=H), timeout=40, context=ctx) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:
        return "ERR %s %s" % (type(e).__name__, e)
def dates(t):
    d = sorted(set(re.findall(r"(20\d\d[-.]\d\d[-.]\d\d)", t)))
    return len(d), (d[0], d[-1]) if d else None
B = "https://www.ekapepia.com/v3/price/livestock/"
pages = {"egg": B+"egg/distrPrice.do?menuSn=36&boardInfoNo=", "chicken": B+"chicken/distrPrice.do?menuSn=35&boardInfoNo=",
         "chickenlive": B+"chicken/livePrice.do?menuSn=131", "eggprod": B+"egg/producer.do?menuSn=37"}
for k, u in pages.items():
    t = get(u)
    print("==", k, len(t), dates(t))
    if t.startswith("ERR"): print(t); continue
    print(" inputs:", sorted(set(re.findall(r'<input[^>]*name="([^"]+)"', t))))
    print(" selects:", sorted(set(re.findall(r'<select[^>]*name="([^"]+)"', t))))
    print(" forms:", re.findall(r'<form[^>]*action="([^"]*)"', t)[:5])
tests = []
for name in ("searchStartDate/searchEndDate", "startDate/endDate", "searchBgnDe/searchEndDe", "strtDt/endDt", "searchStartYmd/searchEndYmd"):
    a, b = name.split("/")
    for base in (pages["egg"], pages["chicken"]):
        u = base + "&%s=2021-01-01&%s=2021-12-31" % (a, b)
        t = get(u); print("TRY", name, base.split("/")[-2], len(t), dates(t))
