import os, sys, json, re, urllib.request
from xml.sax.saxutils import escape

SITE = "https://kurashi-keisan.online"
HOST = "kurashi-keisan.online"
KEY = "k7f3a9c2e8b14d6f0a5e2c9b7d3f1a8e"
DIST = "dist"
NEW_LIST = "new_urls.json"

def page_urls():
    urls = set()
    for root, dirs, files in os.walk(DIST):
        for f in files:
            if not f.endswith(".html") or f == "404.html":
                continue
            rel = os.path.relpath(os.path.join(root, f), DIST).replace(os.sep, "/")
            if rel == "index.html":
                urls.add(SITE + "/")
            elif rel.endswith("/index.html"):
                urls.add(SITE + "/" + rel[:-10])
            else:
                urls.add(SITE + "/" + rel)
    return sorted(urls)

def live_urls():
    try:
        with urllib.request.urlopen(SITE + "/sitemap.xml", timeout=20) as r:
            return set(re.findall(r"<loc>(.*?)</loc>", r.read().decode("utf-8")))
    except Exception:
        return set()

def prepare():
    urls = page_urls()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    lines += [f"  <url><loc>{escape(u)}</loc></url>" for u in urls]
    lines.append("</urlset>")
    with open(os.path.join(DIST, "sitemap.xml"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
    robots = os.path.join(DIST, "robots.txt")
    if not os.path.exists(robots):
        with open(robots, "w", encoding="utf-8") as fp:
            fp.write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    with open(os.path.join(DIST, KEY + ".txt"), "w", encoding="utf-8") as fp:
        fp.write(KEY)
    live = live_urls()
    new = [u for u in urls if escape(u) not in live]
    with open(NEW_LIST, "w", encoding="utf-8") as fp:
        json.dump(new, fp)
    print("ページ数:", len(urls), "/ 新しいページ:", len(new))

def ping():
    try:
        with open(NEW_LIST, encoding="utf-8") as fp:
            new = json.load(fp)
    except Exception:
        return
    if not new:
        print("新しいページなし")
        return
    body = json.dumps({"host": HOST, "key": KEY,
                       "keyLocation": f"{SITE}/{KEY}.txt",
                       "urlList": new}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
          headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("IndexNow送信:", r.status, len(new), "件")
    except Exception as e:
        print("IndexNowエラー:", e)

if sys.argv[1:] == ["ping"]:
    ping()
else:
    prepare()
