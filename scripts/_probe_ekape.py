import re, ssl
from urllib.request import Request, urlopen
from urllib.parse import urlencode
ctx = ssl.create_default_context()
H = {"User-Agent": "Mozilla/5.0 (compatible; pb-probe/1.0)", "Accept-Language": "ko-KR,ko;q=0.9"}
def req(u):
    try:
        with urlopen(Request(u, headers=H), timeout=40, context=ctx) as x:
            return x.read().decode("utf-8", "replace")
    except Exception as e:
        return "ERR %s %s" % (type(e).__name__, e)
def dates(t):
    d = sorted(set(re.findall(r"(20\d\d-\d\d-\d\d)", t)))
    return len(d), (d[0], d[-1]) if d else None
P = "https://www.ekapepia.com/v3/price/livestock/"
U = P + "egg/distrPrice.do"
t = req(U + "?menuSn=36&boardInfoNo=")
i = t.find("function searchDistrPriceInfo")
print("FN1:", re.sub(r"\s+", " ", t[i:i + 2200])); print("----")
j = t.find('id="searchForm"')
print("FORMSTART:", re.sub(r"\s+", " ", t[j - 20:j + 3000])); print("----")
for m in re.finditer(r'(name="radioChk"[^>]*>)', t):
    print("RADIO:", re.sub(r"\s+", " ", t[max(0, m.start() - 80):m.start() + 160]))
combos = [
 {"menuSn": "36", "boardInfoNo": "", "radioChk": "day", "startYYMMDD": "2021-01-01", "endYYMMDD": "2021-12-31", "searchStartDate": "2021-01-01", "searchEndDate": "2021-12-31"},
 {"menuSn": "36", "boardInfoNo": "", "radioChk": "day", "searchStartDate": "2021-01-01", "searchEndDate": "2021-12-31", "searchStartDate2": ""},
 {"menuSn": "36", "boardInfoNo": "", "radioChk": "day", "startYYMMDD": "2021-01-01", "endYYMMDD": "2021-12-31"},
 {"menuSn": "36", "boardInfoNo": "", "radioChk": "day", "startYYMMDD": "2021-01-01", "endYYMMDD": "2021-03-31", "searchStartDate": "2021-01-01", "searchEndDate": "2021-03-31", "searchStartDate2": ""},
]
for c in combos:
    x = req(U + "?" + urlencode(c))
    n, r = dates(x)
    print("COMBO", list(c)[2:], len(x), n, r)
    rows = re.findall(r"(20\d\d-\d\d-\d\d)", x)
    print("   first/last in body:", rows[:2], rows[-2:], "count", len(rows))
