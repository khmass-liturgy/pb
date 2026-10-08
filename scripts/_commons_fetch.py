import json, os, re, sys, time
import requests
H = {"User-Agent": "pb-embryo-photos/1.0 (https://polcon.cc; research use)"}
TITLES = [
 "File:Anatomy of an amiotic egg.svg", "File:Chicken embryo.tif", "File:Chick embryo 3d yolk.jpg", "File:DRG Chicken e7.jpg",
 "File:Chick embryo 10d inside.jpg", "File:CDC PHIL 10149 – fertilized egg, 11 days old.jpg",
 "File:CDC microbiologist demonstrating how to candle an embryonated chicken egg.tiff", "File:CDC PHIL 10148 – candling, fertilized egg, non-viable.jpg",
 "File:Life Cycle of the Chicken.jpg", "File:Chick embryo development stage from incubator.jpg", "File:Chick embryo unborn from incubator.jpg",
 "File:Unborn chick embryo from incubator.jpg", "File:Egg -chick -yolk sac-6a.jpg", "File:מדגרה 3.jpg",
 "File:Chicks hatching USDA95c1973.jpg", "File:Chicks hatching.JPG", "File:Hatching.jpg", "File:Newly-hatched chickens.jpg",
 "File:Jielbeaumadier poussins agr paris 2013.jpeg",
]
out = "assets/embryo/cand"
os.makedirs(out, exist_ok=True)
credits = {}
for t in TITLES:
    try:
        r = requests.get("https://commons.wikimedia.org/w/api.php", headers=H, timeout=30, params={
            "action": "query", "format": "json", "titles": t, "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 800})
        r.raise_for_status()
        p = next(iter(r.json()["query"]["pages"].values()))
        ii = p["imageinfo"][0]
        em = ii.get("extmetadata") or {}
        g = lambda k: re.sub(r"<[^>]+>", "", (em.get(k) or {}).get("value", "")).strip()
        url = ii.get("thumburl") or ii["url"]
        ext = ".png" if url.lower().split("?")[0].endswith(".png") else ".jpg"
        slug = (re.sub(r"[^A-Za-z0-9]+", "_", t.replace("File:", ""))[:60].strip("_") or "x") + ext
        img = requests.get(url, headers=H, timeout=60)
        img.raise_for_status()
        open(os.path.join(out, slug), "wb").write(img.content)
        credits[slug] = {"title": t, "page": ii.get("descriptionurl"), "license": g("LicenseShortName"), "licenseUrl": g("LicenseUrl"),
                         "artist": g("Artist")[:120], "credit": g("Credit")[:120], "desc": g("ImageDescription")[:160],
                         "w": ii.get("thumbwidth"), "h": ii.get("thumbheight"), "bytes": len(img.content)}
        print("OK ", slug, credits[slug]["license"], len(img.content))
        time.sleep(1)
    except Exception as e:
        print("ERR", t, type(e).__name__, str(e)[:100])
json.dump(credits, open(os.path.join(out, "credits.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
