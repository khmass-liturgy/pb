import re, ssl
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from fetch_poultry_price import RowParser
ctx = ssl.create_default_context()
H = {"User-Agent": "Mozilla/5.0 (compatible; pb-probe/1.0)", "Accept-Language": "ko-KR,ko;q=0.9"}
def req(u):
    with urlopen(Request(u, headers=H), timeout=60, context=ctx) as x:
        return x.read().decode("utf-8", "replace")
B = "https://www.ekapepia.com/v3/price/livestock/"
for name, path, menu in (("egg", "egg/distrPrice.do", "36"), ("chicken", "chicken/distrPrice.do", "35")):
    q = urlencode({"menuSn": menu, "boardInfoNo": "", "radioChk": "day", "startYYMMDD": "2021-01-04", "endYYMMDD": "2021-01-12", "searchStartDate": "2021-01-04", "searchEndDate": "2021-01-12", "searchStartDate2": ""})
    t = req(B + path + "?" + q)
    p = RowParser(); p.feed(t)
    print("==", name, len(t), "rows", len(p.rows))
    for r in p.rows[:14]: print("  ROW", r[:9])
    i = t.find("<tbody")
    print("  TBODY:", re.sub(r"\s+", " ", t[i:i + 900]))
