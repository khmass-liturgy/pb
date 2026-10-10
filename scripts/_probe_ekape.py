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
    for (a, b) in (("2018-06-04", "2018-06-12"), ("2019-06-03", "2019-06-11"), ("2020-06-01", "2020-06-09"), ("2020-12-01", "2020-12-09"), ("2021-01-04", "2021-01-12")):
        q = urlencode({"menuSn": menu, "boardInfoNo": "", "radioChk": "day", "startYYMMDD": a, "endYYMMDD": b, "searchStartDate": a, "searchEndDate": b, "searchStartDate2": ""})
        t = req(B + path + "?" + q)
        p = RowParser(); p.feed(t)
        print("==", name, a, len(t))
        for r in p.rows[:7]: print("  ROW", r[:9])
