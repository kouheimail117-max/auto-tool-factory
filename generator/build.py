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
ul.tools li{background:var(--card);border:2px solid var(--line);border-radius:1.25rem;padding:.9rem 1.1rem}
ul.tools li[hidden]{display:none}
ul.tools a{font-weight:700;text-decoration:none;font-size:1.1rem}
ul.tools small{color:var(--sub)}
.ad{min-height:6rem;border:2px dashed var(--line);border-radius:1.25rem;display:flex;align-items:cent
