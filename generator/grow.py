"""Claude APIで新しい計算ツールを考案し tools/ に追加する（毎日自動実行される部分）。"""
import json, os, sys, pathlib, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from validate import validate

ROOT = pathlib.Path(__file__).resolve().parent.parent
site = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
key = os.environ.get("ANTHROPIC_API_KEY")
if not key:
    print("ANTHROPIC_API_KEY が未設定なので追加をスキップ"); sys.exit(0)

existing = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "tools").glob("*.json")]
example = existing[0] if existing else {}
taken = [t["slug"] + "：" + t["h1"] for t in existing]

PROMPT = f"""日本の一般の人が検索しそうな「計算ツール」を1つ考えて、次のJSON形式だけで返してください。前置きやコードブロックは不要です。
条件:
- 既存と重複しないこと。既存: {json.dumps(taken, ensure_ascii=False)}
- 実際に役立ち、計算式が正確であること（税率など年によって変わる値は使わない）
- expr は入力idと数字、+ - * / % ( ) と Math.ceil/floor/round/abs/min/max/pow/sqrt だけで書く
- article は計算方法と具体例を含む200〜400字の自然な日本語
- inputs は1〜6個、outputs は1〜6個
形式の例: {json.dumps(example, ensure_ascii=False)}"""

def ask():
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",
        data=json.dumps({"model": "claude-sonnet-5", "max_tokens": 2000,
                         "messages": [{"role": "user", "content": PROMPT}]}).encode(),
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.load(r)
    text = "".join(b.get("text", "") for b in data["content"])
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)

added = 0
for attempt in range(3 * site.get("max_new_tools_per_run", 1)):
    if added >= site.get("max_new_tools_per_run", 1):
        break
    try:
        tool = ask()
    except Exception as ex:
        print("生成失敗:", ex); continue
    errs = validate(tool)
    path = ROOT / "tools" / f"{tool.get('slug','x')}.json"
    if errs or path.exists():
        print("却下:", errs or "slug重複"); continue
    path.write_text(json.dumps(tool, ensure_ascii=False, indent=2), encoding="utf-8")
    print("追加:", tool["slug"]); added += 1
