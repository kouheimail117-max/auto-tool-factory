"""tools/*.json から静的サイトを dist/ に生成する。依存ライブラリなし。"""
import json, html, sys, datetime, pathlib, zlib, struct, math
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

# ---------- おひさまアイコン（PNG）を作る ----------
def _png(w, h, rows):
    raw = b"".join(b"\x00" + bytes(r) for r in rows)
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))

def _seg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)

def icon_png(size):
    k = 120 / size
    rays = [(60 + 44 * math.cos(a), 60 + 44 * math.sin(a), 60 + 54 * math.cos(a), 60 + 54 * math.sin(a))
            for a in [i * math.pi / 4 for i in range(8)]]
    pts = [((1 - t) ** 2 * 52 + 2 * (1 - t) * t * 60 + t * t * 68, (1 - t) ** 2 * 70 + 2 * (1 - t) * t * 78 + t * t * 70)
           for t in [i / 12 for i in range(13)]]
    smile = [pts[i] + pts[i + 1] for i in range(12)]
    BG, ORA, YEL, BRN, PNK = (255, 248, 231), (245, 166, 35), (255, 213, 74), (90, 58, 26), (255, 158, 170)
    rows = []
    for j in range(size):
        y = (j + 0.5) * k
        row = []
        for i in range(size):
            x = (i + 0.5) * k
            col = list(BG)
            def paint(c, d, op=1.0):
                a = max(0.0, min(1.0, 0.5 - d / k)) * op
                if a > 0:
                    for n in range(3):
                        col[n] = col[n] * (1 - a) + c[n] * a
            r = math.hypot(x - 60, y - 60)
            if r > 40:
                paint(ORA, min(_seg(x, y, *s) for s in rays) - 3)
            if r < 39.5:
                paint(ORA, r - 37.5)
                paint(YEL, r - 34.5)
                if 49 < y < 63:
                    for ex in (48, 72):
                        paint(BRN, (math.hypot((x - ex) / 3.5, (y - 56) / 5) - 1) * 3.5)
                if 60 < y < 76:
                    for bx in (40, 80):
                        paint(PNK, math.hypot(x - bx, y - 68) - 6, 0.7)
                if 66 < y < 78 and 48 < x < 72:
                    paint(BRN, min(_seg(x, y, *s) for s in smile) - 1.5)
            row += [int(round(v)) for v in col]
        rows.append(row)
    return _png(size, size, rows)

SW_JS = ('self.addEventListener("install",function(){self.skipWaiting()});'
         'self.addEventListener("activate",function(e){e.waitUntil(self.clients.claim())});'
         'self.addEventListener("fetch",function(e){if(e.request.mode==="navigate"){'
         'e.respondWith(fetch(e.request).catch(function(){return new Response('
         '"インターネットにつながっていないみたい。つながったらもう一度開いてね",'
         '{headers:{"Content-Type":"text/plain; charset=utf-8"}})}))}});')

INSTALL = ('<div class="inst" id="inst" hidden><button id="instb" type="button">☀ ホーム画面・デスクトップに追加</button>'
           '<p id="insttip" hidden></p></div>'
           '<script>(function(){'
           'if("serviceWorker" in navigator){navigator.serviceWorker.register("/sw.js").catch(function(){})}'
           'var box=document.getElementById("inst"),btn=document.getElementById("instb"),tip=document.getElementById("insttip"),ev=null;'
           'if(window.matchMedia("(display-mode: standalone)").matches||navigator.standalone)return;'
           'box.hidden=false;'
           'window.addEventListener("beforeinstallprompt",function(x){x.preventDefault();ev=x});'
           'window.addEventListener("appinstalled",function(){box.hidden=true});'
           'btn.addEventListener("click",function(){'
           'if(ev){ev.prompt();ev.userChoice.then(function(r){if(r.outcome==="accepted")box.hidden=true;ev=null});return}'
           'var ua=navigator.userAgent;'
           'if(/iPhone|iPad|iPod/.test(ua)||(/Macintosh/.test(ua)&&"ontouchend" in document)){'
           'tip.textContent="画面の共有ボタン（四角に上向き矢印のマーク）をタップして「ホーム画面に追加」を選んでね"}'
           'else{tip.textContent="ブラウザのメニュー（︙ や …）から「アプリをインストール」または「ホーム画面に追加」を選んでね。パソコンならデスクトップにアイコンができるよ"}'
           'tip.hidden=false})})();</script>')

# ---------- ツールごとのアイコン ----------
_S = 'stroke="#5A3A1A" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"'
ICONS = {
    "people": ("#FFE0E6", f'<circle cx="30" cy="19" r="5" fill="#FFE2C6" {_S}/><path d="M21 35 a9 9 0 0 1 18 0z" fill="#8FD3F4" {_S}/>'
                          f'<circle cx="18" cy="19" r="5" fill="#FFE2C6" {_S}/><path d="M9 35 a9 9 0 0 1 18 0z" fill="#FF9EAA" {_S}/>'),
    "tag": ("#FFF0C2", f'<path d="M11 11 H25 L38 24 L25 37 L11 23 Z" fill="#FFB65C" {_S}/><circle cx="17" cy="17" r="2.5" fill="#fff" {_S}/>'
                       '<path d="M22 30 L30 22" stroke="#5A3A1A" stroke-width="2.2" stroke-linecap="round"/>'
                       '<circle cx="22.5" cy="23" r="1.8" fill="#5A3A1A"/><circle cx="29.5" cy="29" r="1.8" fill="#5A3A1A"/>'),
    "bolt": ("#FFF3B0", f'<path d="M27 8 L14 27 H23 L20 40 L34 20 H25 Z" fill="#FFD54A" {_S}/>'),
    "fuel": ("#D9F2E6", f'<rect x="12" y="12" width="17" height="26" rx="3" fill="#6CC59A" {_S}/>'
                        f'<rect x="15.5" y="15.5" width="10" height="7" rx="1.5" fill="#fff" {_S}/>'
                        '<path d="M29 18 H32 A2 2 0 0 1 34 20 V31 A2 2 0 0 0 38 31 V17 L35 13" fill="none" stroke="#5A3A1A" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'),
    "house": ("#FFE6D1", f'<rect x="14" y="23" width="20" height="15" rx="2" fill="#FFF3D6" {_S}/>'
                         f'<path d="M10 25 L24 12 L38 25" fill="#F28C38" {_S}/><rect x="21" y="29" width="6" height="9" rx="1.5" fill="#C9874A"/>'),
    "piggy": ("#FFE0E6", f'<circle cx="24" cy="10" r="4" fill="#FFD54A" {_S}/>'
                         f'<path d="M17 20 L19 14 L23 18" fill="#FFB3C1" {_S}/>'
                         f'<rect x="16" y="33" width="4" height="5" rx="1.5" fill="#FFB3C1" {_S}/><rect x="27" y="33" width="4" height="5" rx="1.5" fill="#FFB3C1" {_S}/>'
                         f'<ellipse cx="24" cy="27" rx="13" ry="9.5" fill="#FFB3C1" {_S}/>'
                         f'<ellipse cx="36" cy="27" rx="3" ry="3.5" fill="#FF9EAA" {_S}/><circle cx="31" cy="23.5" r="1.4" fill="#5A3A1A"/>'
                         '<rect x="20" y="18" width="8" height="2" rx="1" fill="#5A3A1A"/>'),
    "heart": ("#FFE0E6", f'<path d="M24 37 C10 28 10 15 18 14 C21 13.5 23 15 24 17 C25 15 27 13.5 30 14 C38 15 38 28 24 37 Z" fill="#FF8A9B" {_S}/>'
                         '<ellipse cx="18.5" cy="19" rx="2" ry="3" fill="#fff" opacity="0.8"/>'),
    "clock": ("#E3F1FF", f'<rect x="21" y="7" width="6" height="4" rx="1.2" fill="#8FC1F4" {_S}/><circle cx="24" cy="25" r="13" fill="#fff" {_S}/>'
                         '<path d="M24 17 V25 L30 28" fill="none" stroke="#E0670F" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'),
    "calendar": ("#E3F1FF", f'<rect x="11" y="13" width="26" height="24" rx="3" fill="#fff" {_S}/>'
                            f'<path d="M11 21 V16 A3 3 0 0 1 14 13 H34 A3 3 0 0 1 37 16 V21 Z" fill="#FF8A9B" {_S}/>'
                            '<path d="M17 10 V15 M31 10 V15" stroke="#5A3A1A" stroke-width="2.4" stroke-linecap="round"/>'
                            '<g fill="#F5A623"><circle cx="17" cy="26" r="1.7"/><circle cx="24" cy="26" r="1.7"/><circle cx="31" cy="26" r="1.7"/>'
                            '<circle cx="17" cy="32" r="1.7"/><circle cx="24" cy="32" r="1.7"/></g>'),
    "coin": ("#FFF3B0", f'<circle cx="24" cy="24" r="13" fill="#FFD54A" {_S}/><circle cx="24" cy="24" r="9.5" fill="none" stroke="#F5A623" stroke-width="2"/>'
                        '<path d="M19.5 17.5 L24 23.5 L28.5 17.5 M24 23.5 V31 M20 25 H28 M20 28.5 H28" fill="none" stroke="#5A3A1A" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'),
    "calc": ("#FFF0C2", f'<rect x="14" y="10" width="20" height="28" rx="4" fill="#FFB65C" {_S}/><rect x="17.5" y="13.5" width="13" height="7" rx="1.5" fill="#FFF8E7"/>'
                        '<g fill="#fff"><circle cx="19" cy="26" r="1.9"/><circle cx="24" cy="26" r="1.9"/><circle cx="29" cy="26" r="1.9"/>'
                        '<circle cx="19" cy="32" r="1.9"/><circle cx="24" cy="32" r="1.9"/><circle cx="29" cy="32" r="1.9"/></g>'),
}
ICON_RULES = [
    ("people", ["割り勘", "割勘", "わりかん", "warikan", "人数", "一人あたり", "1人あたり"]),
    ("tag", ["割引", "セール", "値引", "税込", "税抜", "消費税", "waribiki", "%", "％"]),
    ("bolt", ["電気", "電力", "ワット", "denki"]),
    ("fuel", ["ガソリン", "燃費", "給油", "gasorin"]),
    ("house", ["家賃", "住宅", "引っ越し", "引越", "yachin"]),
    ("piggy", ["貯金", "貯蓄", "積立", "積み立て", "chokin"]),
    ("heart", ["bmi", "体重", "身長", "カロリー", "健康"]),
    ("clock", ["秒", "時間", "分給", "byou"]),
    ("coin", ["時給", "年収", "月収", "給料", "給与", "収入", "円", "jikyuu"]),
    ("calendar", ["日数", "何日", "年齢", "誕生日", "カレンダー", "日"]),
]

def icon_for(t):
    text = " ".join([t.get("h1", ""), t.get("title", ""), t.get("slug", ""), t.get("description", "")]).lower()
    key = "calc"
    for k, words in ICON_RULES:
        if any(w.lower() in text for w in words):
            key = k
            break
    bg, body = ICONS[key]
    return f'<svg class="ic" width="46" height="46" viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="23" fill="{bg}"/>{body}</svg>'

# ---------- イラスト ----------
SUN_BODY = ('<g stroke="#F5A623" stroke-width="6" stroke-linecap="round">'
            '<line x1="104" y1="60" x2="114" y2="60"/><line x1="91.1" y1="91.1" x2="98.2" y2="98.2"/>'
            '<line x1="60" y1="104" x2="60" y2="114"/><line x1="28.9" y1="91.1" x2="21.8" y2="98.2"/>'
            '<line x1="16" y1="60" x2="6" y2="60"/><line x1="28.9" y1="28.9" x2="21.8" y2="21.8"/>'
            '<line x1="60" y1="16" x2="60" y2="6"/><line x1="91.1" y1="28.9" x2="98.2" y2="21.8"/></g>'
            '<circle cx="60" cy="60" r="36" fill="#FFD54A" stroke="#F5A623" stroke-width="3"/>'
            '<ellipse cx="48" cy="56" rx="3.5" ry="5" fill="#5A3A1A"/><ellipse cx="72" cy="56" rx="3.5" ry="5" fill="#5A3A1A"/>'
            '<circle cx="40" cy="68" r="6" fill="#FF9EAA" opacity="0.7"/><circle cx="80" cy="68" r="6" fill="#FF9EAA" opacity="0.7"/>'
            '<path d="M52 70 Q60 78 68 70" stroke="#5A3A1A" stroke-width="3" fill="none" stroke-linecap="round"/>')

def sun(size):
    return f'<svg width="{size}" height="{size}" viewBox="0 0 120 120" aria-hidden="true">{SUN_BODY}</svg>'

HERO = ('<svg class="hero" viewBox="0 0 320 150" aria-hidden="true">'
        '<ellipse cx="160" cy="165" rx="210" ry="55" fill="#CDEB9A"/>'
        '<g fill="#fff" stroke="#F2D79B" stroke-width="2">'
        '<path d="M30 50 a14 14 0 0 1 26 -6 a11 11 0 0 1 18 8 a9 9 0 0 1 -2 17 h-40 a10 10 0 0 1 -2 -19z"/>'
        '<path d="M200 34 a11 11 0 0 1 20 -4 a9 9 0 0 1 14 6 a7 7 0 0 1 -2 13 h-30 a8 8 0 0 1 -2 -15z"/></g>'
        '<g transform="translate(80 78)"><rect x="0" y="22" width="44" height="34" rx="4" fill="#FFF3D6" stroke="#E0670F" stroke-width="2"/>'
        '<path d="M-6 24 L22 2 L50 24 Z" fill="#F28C38" stroke="#E0670F" stroke-width="2" stroke-linejoin="round"/>'
        '<rect x="16" y="36" width="12" height="20" rx="3" fill="#C9874A"/></g>'
        '<g transform="translate(150 92)"><rect x="0" y="16" width="32" height="26" rx="4" fill="#FFF3D6" stroke="#E0670F" stroke-width="2"/>'
        '<path d="M-5 18 L16 2 L37 18 Z" fill="#FFB65C" stroke="#E0670F" stroke-width="2" stroke-linejoin="round"/></g>'
        f'<g transform="translate(232 18) scale(0.62)">{SUN_BODY}</g></svg>')

COUNTER = ('<p class="count" id="cnt" hidden>☀ これまでに <b id="cntn">-</b> 人がきてくれたよ</p>'
           '<script>fetch("https://tally.yuki.sh/hits/kurashi-keisan/site.json")'
           '.then(function(r){return r.json()}).then(function(d){'
           'if(d&&d.visitor){document.getElementById("cntn").textContent=d.visitor.toLocaleString("ja-JP");'
           'document.getElementById("cnt").hidden=false}}).catch(function(){})</script>')

SEARCH_BOX = ("<div class='search'><label for='q'>☀ なにを計算したい？</label>"
              "<input id='q' type='search' placeholder='例：電気代、貯金、時給' autocomplete='off'></div>")

SEARCH_JS = ('<script>(function(){var q=document.getElementById("q"),'
             'items=document.querySelectorAll("ul.tools li"),none=document.getElementById("none");'
             'function kata(s){return s.replace(/[\\u30a1-\\u30f6]/g,function(c){return String.fromCharCode(c.charCodeAt(0)-96)})}'
             'function norm(s){return kata(s.normalize("NFKC").toLowerCase())}'
             'items.forEach(function(li){li.dataset.n=norm(li.dataset.k||"")});'
             'q.addEventListener("input",function(){var w=norm(q.value).split(/\\s+/).filter(Boolean),c=0;'
             'items.forEach(function(li){var ok=w.every(function(x){return li.dataset.n.indexOf(x)>=0});'
             'li.hidden=!ok;if(ok)c++});none.hidden=c>0})})();</script>')

CSS = """
:root{--bg:#fff8e7;--ink:#4a3420;--sub:#8a6a4a;--ai:#e0670f;--ok:#b54a0c;--line:#f2d79b;--field:#fff;--card:#fff;--sun:#ffe08a;--sunink:#6b4100}
@media (prefers-color-scheme:dark){:root{--bg:#231b13;--ink:#fbeedd;--sub:#cdb497;--ai:#ffad55;--ok:#ffc56e;--line:#54412c;--field:#2e2419;--card:#2b2117;--sun:#4a3618;--sunink:#ffe3a3}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"M PLUS Rounded 1c","Hiragino Maru Gothic ProN","Yu Gothic",sans-serif;line-height:1.8}
header{background:var(--sun);padding:.5rem 1.25rem;border-radius:0 0 1.5rem 1.5rem}
header a{display:flex;align-items:center;gap:.5rem;color:var(--sunink);text-decoration:none;font-weight:700;font-size:1.1rem}
main{max-width:34rem;margin:0 auto;padding:1.5rem 1.25rem 3rem}
.hero{display:block;width:100%;height:auto;margin:0 0 .5rem}
.card{background:var(--card);border:2px solid var(--line);border-radius:1.5rem;padding:.5rem 1.25rem 1.5rem;margin:1rem 0}
h1{color:var(--ai);font-size:1.7rem;line-height:1.35;margin:.2rem 0 .6rem}
h2{color:var(--ai);font-size:1.25rem;margin-top:2rem}
h2::before{content:"☀ "}
label{display:block;font-weight:700;margin:1rem 0 .3rem}
input{font:inherit;font-size:1.15rem;width:100%;padding:.65rem 1.1rem;border:2px solid var(--line);border-radius:999px;background:var(--field);color:var(--ink);outline:none}
input:focus{border-color:var(--ai)}
.search{background:var(--sun);border-radius:1.5rem;padding:.2rem 1.1rem 1.1rem;margin:1.25rem 0}
.search label{color:var(--sunink)}
.none{text-align:center;color:var(--sub);background:var(--card);border:2px dashed var(--line);border-radius:1.25rem;padding:1rem}
.say{display:flex;align-items:center;gap:.6rem;margin:1.5rem 0 .6rem}
.say span{background:var(--field);border:2px solid var(--line);border-radius:1rem;padding:.3rem .9rem;font-size:.95rem;font-weight:700}
dl{display:grid;grid-template-columns:1fr auto;gap:.6rem 1rem;margin:0;padding:1rem 1.25rem;background:var(--sun);border-radius:1.25rem}
dt{color:var(--sunink)}dd{margin:0;font-weight:700;font-size:1.3rem;color:var(--ok);text-align:right}
a{color:var(--ai)}
ul.tools{list-style:none;padding:0;display:grid;gap:.8rem}
ul.tools li{display:flex;align-items:center;gap:.8rem;background:var(--card);border:2px solid var(--line);border-radius:1.25rem;padding:.9rem 1.1rem}
ul.tools .ic{flex-shrink:0}
ul.tools li[hidden]{display:none}
ul.tools a{font-weight:700;text-decoration:none;font-size:1.1rem}
ul.tools small{color:var(--sub)}
.ad{min-height:6rem;border:2px dashed var(--line);border-radius:1.25rem;display:flex;align-items:center;justify-content:center;color:var(--sub);font-size:.85rem;margin:2rem 0}
.inst{text-align:center;margin:2rem 0 1rem}
.inst button{font:inherit;font-weight:700;font-size:1rem;background:var(--sun);color:var(--sunink);border:2px solid var(--ai);border-radius:999px;padding:.6rem 1.4rem;cursor:pointer}
.inst p{text-align:left;font-size:.9rem;color:var(--sub);background:var(--card);border:2px dashed var(--line);border-radius:1rem;padding:.6rem 1rem;margin:.8rem 0 0}
.count{text-align:center;background:var(--sun);color:var(--sunink);border-radius:999px;padding:.4rem 1rem;font-size:.95rem;margin:1rem 0}
.count b{color:var(--ok);font-size:1.2rem}
.back{display:inline-block;background:var(--ai);color:var(--bg);padding:.5rem 1.4rem;border-radius:999px;text-decoration:none;font-weight:700}
"""

FONTS = ("<link rel='preconnect' href='https://fonts.googleapis.com'>"
         "<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>"
         "<link href='https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700&display=swap' rel='stylesheet'>")

APP_HEAD = ("<link rel='manifest' href='/manifest.webmanifest'><meta name='theme-color' content='#ffe08a'>"
            "<link rel='icon' type='image/png' href='/icon-192.png'><link rel='apple-touch-icon' href='/icon-192.png'>")

def page(title, desc, body, path):
    base = site["base_url"].rstrip("/")
    url = base + "/" + path
    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>
<meta name="description" content="{e(desc)}"><link rel="canonical" href="{e(url)}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
{APP_HEAD}{FONTS}<style>{CSS}</style></head><body>
<header><a href="{e(base)}/">{sun(40)}{e(site["site_name"])}</a></header><main>{body}
{INSTALL}{COUNTER}
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
            f"<div class='card'>{inputs}<div class='say'>{sun(52)}<span>けいさんできたよ！</span></div><dl>{outs}</dl></div>"
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
    items = "".join(
        f"<li data-k='{e(' '.join([t['h1'], t['title'], t['description'], t['article'], t['slug']]))}'>"
        f"{icon_for(t)}<div><a href='{e(t['slug'])}/'>{e(t['h1'])}</a><br><small>{e(t['description'])}</small></div></li>" for t in tools)
    idx = (f"{HERO}<h1>{e(site['site_name'])}</h1><p>毎日の「いくら？」「何日？」をすぐ計算。</p>"
           f"{SEARCH_BOX}<ul class='tools'>{items}</ul>"
           f"<p id='none' class='none' hidden>{sun(40)}<br>見つからなかったよ。別のことばでさがしてみてね</p>"
           f"{SEARCH_JS}{ad_tag()}")
    (DIST / "index.html").write_text(page(site["site_name"], "暮らしの計算ツール集", idx, ""), encoding="utf-8")
    (DIST / "manifest.webmanifest").write_text(json.dumps({
        "name": site["site_name"], "short_name": site["site_name"], "lang": "ja",
        "start_url": "/", "scope": "/", "display": "standalone",
        "background_color": "#fff8e7", "theme_color": "#ffe08a",
        "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}]},
        ensure_ascii=False), encoding="utf-8")
    (DIST / "sw.js").write_text(SW_JS, encoding="utf-8")
    for s in (192, 512):
        (DIST / f"icon-{s}.png").write_bytes(icon_png(s))
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
