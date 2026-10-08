import json, re, sys, urllib.parse
import requests
H = {"User-Agent": "pb-embryo-photos/1.0 (https://polcon.cc; research use)"}
QUERIES = [
  "chick embryo day 18", "chicken embryo late stage unhatched", "embryo chicken egg dissected 17 days", "chicken embryo 19 days", "chicken embryo 20 days",
  "domestic chicken hatching", "chicken hatching from egg", "hatching chick Gallus gallus domesticus", "chicks hatching incubator", "newly hatched chick egg shell",
  "chick pipping", "chick beak egg shell hole", "egg tooth chick", "chicken embryo day 5", "chicken embryo day 8", "chicken embryo day 12", "chicken embryo day 16",
  "chicken embryo yolk sac", "unhatched chick dead in shell", "chick breaking out of egg", "baby chick hatching egg", "Gallus gallus embryo photograph"
]
seen = {}
for q in QUERIES:
    try:
        r = requests.get("https://commons.wikimedia.org/w/api.php", headers=H, timeout=30, params={
            "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrsearch": q, "gsrlimit": 12,
            "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 640})
        r.raise_for_status()
        pages = (r.json().get("query") or {}).get("pages") or {}
    except Exception as e:
        print("QERR", q, e); continue
    for p in pages.values():
        ii = (p.get("imageinfo") or [{}])[0]
        if not ii or ii.get("mime", "").split("/")[0] != "image": continue
        t = p["title"]
        if t in seen: continue
        em = ii.get("extmetadata") or {}
        g = lambda k: re.sub(r"<[^>]+>", "", (em.get(k) or {}).get("value", "")).strip()
        seen[t] = {"title": t, "q": q, "lic": g("LicenseShortName"), "artist": g("Artist")[:50], "desc": g("ImageDescription")[:140],
                   "w": ii.get("width"), "h": ii.get("height"), "mime": ii.get("mime")}
for t, d in seen.items():
    print("%s | %s | %s | %sx%s | %s | %s" % (d["title"], d["lic"], d["artist"], d["w"], d["h"], d["q"], d["desc"]))
print("TOTAL", len(seen))
