import os, json, re, html, urllib.request
from datetime import datetime, timezone

SITE = "https://kurashi-keisan.online"
DIST = "dist"
NEW_LIST = "new_urls.json"
API = "https://bsky.social/xrpc/"
MAX_POSTS = 3

def call(method, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(API + method, data=json.dumps(data).encode(),
                                 headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def page_title(url):
    rel = url[len(SITE):].strip("/")
    if rel.endswith(".html"):
        path = os.path.join(DIST, rel)
    else:
        path = os.path.join(DIST, rel, "index.html")
    try:
        with open(path, encoding="utf-8") as fp:
            m = re.search(r"<title>(.*?)</title>", fp.read(), re.S)
            if m:
                return html.unescape(m.group(1)).strip()
    except Exception:
        pass
    return "新しいツール"

def main():
    handle = os.environ.get("BLUESKY_HANDLE")
    password = os.environ.get("BLUESKY_APP_PASSWORD")
    if not handle or not password:
        print("Blueskyの設定がないため投稿しません")
        return
    try:
        with open(NEW_LIST, encoding="utf-8") as fp:
            new = json.load(fp)
    except Exception:
        print("新しいページの一覧がありません")
        return
    new = [u for u in new if u.rstrip("/") != SITE]
    if not new:
        print("新しいツールなし")
        return
    if len(new) > 5:
        print("件数が多すぎるため投稿を見送りました:", len(new))
        return
    session = call("com.atproto.server.createSession",
                   {"identifier": handle, "password": password})
    for url in new[:MAX_POSTS]:
        title = page_title(url)
        head = f"新しい計算ツールを追加しました！\n\n{title}\n\n"
        text = head + url
        start = len(head.encode("utf-8"))
        end = start + len(url.encode("utf-8"))
        record = {
            "$type": "app.bsky.feed.post",
            "text": text,
            "langs": ["ja"],
            "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "facets": [{
                "index": {"byteStart": start, "byteEnd": end},
                "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}],
            }],
        }
        call("com.atproto.repo.createRecord",
             {"repo": session["did"], "collection": "app.bsky.feed.post",
              "record": record}, session["accessJwt"])
        print("投稿しました:", title)

try:
    main()
except Exception as e:
    print("Bluesky投稿エラー:", e)
