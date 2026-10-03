"""tools/*.json から静的サイトを dist/ に生成する。依存ライブラリなし。"""
import json, html, sys, datetime, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from validate import validate

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
site = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
e = lambda s: html.escape(str(s), quote=True)

def ad_tag():
    c = site.get("adsense_client")
    if not c:
        return "<div class='ad'>広告枠（site.json の adsense_client を設定すると表示）</div>"
    return (f"<script async src='https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={e(c)}' crossorigin='anonymous'></script>"
            f"<ins class='adsbygoogle' style='display:block' data-ad-client='{e(c)}' data-ad-format='auto' data-full-width-responsive='true'></ins>"
            "<script>(adsbygoogle=window.adsbygoogle||[]).push({});</script>")

CSS = """
:root{--bg:#fff8e7;--ink:#4a3420;--sub:#8a6a4a;--ai:#e0670f;--ok:#b54a0c;--line:#f2d79b;--field:#fff;--card:#fff;--sun:#ffe08a;--sunink:#6b4100}
@media (prefers-color-scheme:dark){:root{--bg:#231b13;--ink:#fbeedd;--sub:#cdb497;--ai:#ffad55;--ok:#ffc56e;--line:#54412c;--field:#2e2419;--card:#2b2117;--sun:#4a3618;--sunink:#ffe3a3}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"M PLUS Rounded 1c","Hiragino Maru Gothic ProN","Yu Gothic",sans-serif;line-height:1.8}
header{background:var(--sun);padding:.8rem 1.25rem;border-radius:0 0 1.5rem 1.5rem}
header a{color:var(--sunink);text-decoration:none;font-weight:700;font-size:1.1rem}
main{max-width:34rem;margin:0 auto;padding:1.5rem 1.25rem 3rem}
.card{background:var(--card);border:2px solid var(--line);border-radius:1.5rem;padding:.5rem 1.25rem 1.5rem;margin:1rem 0}
h1{color:var(--ai);font-size:1.7rem;line-height:1.35;margin:.2rem 0 .6rem}
h2{color:var(--ai);font-size:1.25rem;margin-top:2rem}
h2::before{content:"☀ "}
label{display:block;font-weight:700;margin:1rem 0 .3rem}
input{font:inherit;font-size:1.15rem;width:100%;padding:.65rem 1.1rem;border:2px solid var(--line);border-radius:999px;background:var(--field);color:var(--ink);outline:none}
input:focus{border-color:var(--ai)}
dl{display:grid;grid-template-columns:1fr auto;gap:.6rem 1rem;margin:1.5rem 0 0;padding:1rem 1.25rem;background:var(--sun);border-radius:1.25rem}
dt{color:var(--sunink)}dd{margin:0;font-weight:700;font-size:1.3rem;color:var(--ok);text-align:right}
a{color:var(--ai)}
ul.tools{list-style:none;padding:0;display:grid;gap:.8rem}
ul.tools li{background:var(--card);border:2px solid var(--line);border-radius:1.25rem;padding:.9rem 1.1rem}
ul.tools a{font-weight:700;text-decoration:none;font-size:1.1rem}
ul.tools small{color:var(--sub)}
.ad{min-height:6rem;border:2px dashed var(--line);border-radius:1.25rem;display:flex;align-items:center;justify-content:center;color:var(--sub);font-size:.85rem;margin:2rem 0}
.back{display:inline-block;background:var(--ai);color:var(--bg);padding:.5rem 1.4rem;border-radius:999px;text-decoration:none;font-weight:700}
"""

FONTS = ("<link rel='preconnect' href='https://fonts.googleapis.com'>"
         "<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>"
         "<link href='https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700&display=swap' rel='stylesheet'>")

def page(title, desc, body, path):
    base = site["base_url"].rstrip("/")
    url = base + "/" + path
    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>
<meta name="description" content="{e(desc)}"><link rel="canonical" href="{e(url)}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
{FONTS}<style>{CSS}</style></head><body>
<header><a href="{e(base)}/">☀ {e(site["site_name"])}</a></header><main>{body}
<p><a class="back" href="{e(base)}/">トップへもどる</a></p></main></body></html>"""

def tool_page(t):
    inputs = "".join(f"<label for='{e(i['id'])}'>{e(i['label'])}</label>"
                     f"<input id='{e(i['id'])}' type='number' inputmode='decimal' value='{e(i['default'])}'>" for i in t["inputs"])
    outs = "".join(f"<dt>{e(o['label'])}</dt><dd id='o{n}'>–</dd>" for n, o in enumerate(t["outputs"]))
    ids = [i["id"] for i in t["inputs"]]
    fns = ",".join(f"[({','.join(ids)})=>({o['expr']}),{json.dumps(o['unit'])},{int(o.get('digits',0))}]" for o in t["outputs"])
    js = f"""<script>
const ids={json.dumps(ids)},F=[{fns}];
function run(){{const v=ids.map(i=>parseFloat(document.getElementById(i).value)||0);
F.forEach(([f,u,d],n)=>{{const r=f(...v);document.getElementById("o"+n).textContent=
Number.isFinite(r)?r.toLocaleString("ja-JP",{{minimumFractionDigits:d,maximumFractionDigits:d}})+" "+u:"–";}});}}
ids.forEach(i=>document.getElementById(i).addEventListener("input",run));run();</script>"""
    body = (f"<h1>{e(t['h1'])}</h1><p>{e(t['description'])}</p>"
            f"<div class='card'>{inputs}<dl>{outs}</dl></div>"
            f"{ad_tag()}<h2>解説</h2><p>{e(t['article'])}</p>{js}")
    return page(t["title"], t["description"], body, f"{t['slug']}/")

def main():
    DIST.mkdir(exist_ok=True)
    tools = []
    for f in sorted((ROOT / "tools").glob("*.json")):
        t = json.loads(f.read_text(encoding="utf-8"))
        errs = validate(t)
        if errs:
            print(f"スキップ {f.name}: {errs}")
            continue
        (DIST / t["slug"]).mkdir(exist_ok=True)
        (DIST / t["slug"] / "index.html").write_text(tool_page(t), encoding="utf-8")
        tools.append(t)
    items = "".join(f"<li><a href='{e(t['slug'])}/'>{e(t['h1'])}</a><br><small>{e(t['description'])}</small></li>" for t in tools)
    idx = f"<h1>{e(site['site_name'])}</h1><p>毎日の「いくら？」「何日？」をすぐ計算。</p><ul class='tools'>{items}</ul>{ad_tag()}"
    (DIST / "index.html").write_text(page(site["site_name"], "暮らしの計算ツール集", idx, ""), encoding="utf-8")
    today = datetime.date.today().isoformat()
    base = site["base_url"].rstrip("/")
    urls = [f"{base}/"] + [f"{base}/{t['slug']}/" for t in tools]
    (DIST / "sitemap.xml").write_text("<?xml version='1.0' encoding='UTF-8'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
        + "".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls) + "</urlset>", encoding="utf-8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")
    c = site.get("adsense_client", "")
    if c.startswith("ca-pub-"):
        (DIST / "ads.txt").write_text(f"google.com, {c.replace('ca-','')}, DIRECT, f08c47fec0942fa0\n", encoding="utf-8")
    print(f"{len(tools)} ツールを生成しました → dist/")

if __name__ == "__main__":
    main()
