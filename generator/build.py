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
:root{--bg:#f3f5f8;--ink:#1b1f2a;--sub:#5b6272;--ai:#1f2d4f;--ok:#2f8a64;--line:#c6ccd6;--field:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#141925;--ink:#eef1f6;--sub:#a3abbb;--ai:#9fb4e6;--ok:#5cc496;--line:#343c4f;--field:#1c2231}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif;line-height:1.8}
main{max-width:34rem;margin:0 auto;padding:2rem 1.25rem 3rem}h1{color:var(--ai);font-size:1.9rem;line-height:1.3}
label{display:block;font-weight:700;margin:1rem 0 .3rem}input{font:inherit;font-size:1.15rem;width:100%;padding:.6rem;border:1px solid var(--line);border-radius:.5rem;background:var(--field);color:var(--ink)}
dl{display:grid;grid-template-columns:1fr auto;gap:.6rem 1rem;margin:2rem 0;padding:1rem 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
dt{color:var(--sub)}dd{margin:0;font-weight:700;font-size:1.25rem;color:var(--ok);text-align:right}
a{color:var(--ai)}.ad{min-height:6rem;border:1px dashed var(--line);display:flex;align-items:center;justify-content:center;color:var(--sub);font-size:.85rem;margin:2rem 0}
"""

def page(title, desc, body, path):
    url = site["base_url"].rstrip("/") + "/" + path
    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>
<meta name="description" content="{e(desc)}"><link rel="canonical" href="{e(url)}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<style>{CSS}</style></head><body><main>{body}
<p><a href="{e(site["base_url"].rstrip("/"))}/">{e(site["site_name"])} トップへ</a></p></main></body></html>"""

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
    body = (f"<h1>{e(t['h1'])}</h1><p>{e(t['description'])}</p>{inputs}<dl>{outs}</dl>"
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
    idx = f"<h1>{e(site['site_name'])}</h1><p>毎日の「いくら？」「何日？」をすぐ計算。</p><ul>{items}</ul>{ad_tag()}"
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
