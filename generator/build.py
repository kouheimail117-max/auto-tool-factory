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
                        '
