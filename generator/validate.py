"""ツール定義(JSON)の安全チェック。AIが作った定義もここを通らないと公開されない。"""
import re

SLUG = re.compile(r"^[a-z0-9-]{2,40}$")
VAR = re.compile(r"^[a-z][a-z0-9_]{0,20}$")
# 数式に使ってよいのは：変数・数字・演算子・かっこ・Math.関数だけ
EXPR_TOKEN = re.compile(r"Math\.(?:ceil|floor|round|abs|min|max|pow|sqrt|log|log10|exp)|[a-z][a-z0-9_]*|\d+(?:\.\d+)?|[+\-*/%(),\s]")

def validate(tool: dict) -> list[str]:
    errs = []
    for key in ("slug", "title", "h1", "description", "inputs", "outputs", "article"):
        if key not in tool:
            errs.append(f"{key} がありません")
    if errs:
        return errs
    if not SLUG.match(tool["slug"]):
        errs.append("slug は英小文字・数字・ハイフンのみ")
    ids = set()
    for i in tool["inputs"]:
        if not VAR.match(str(i.get("id", ""))):
            errs.append(f"入力IDが不正: {i.get('id')}")
        if not isinstance(i.get("default"), (int, float)):
            errs.append(f"default は数値: {i.get('id')}")
        ids.add(i.get("id"))
    if not (1 <= len(tool["inputs"]) <= 6):
        errs.append("入力は1〜6個")
    if not (1 <= len(tool["outputs"]) <= 6):
        errs.append("出力は1〜6個")
    for o in tool["outputs"]:
        expr = str(o.get("expr", ""))
        pos, rebuilt = 0, ""
        for m in EXPR_TOKEN.finditer(expr):
            if m.start() != pos:
                break
            tok = m.group(0)
            if re.fullmatch(r"[a-z][a-z0-9_]*", tok) and tok not in ids:
                errs.append(f"未定義の変数 {tok} ({o.get('label')})")
            rebuilt += tok
            pos = m.end()
        if rebuilt != expr:
            errs.append(f"数式に使えない文字があります: {expr}")
    if len(tool["article"]) < 80:
        errs.append("解説文が短すぎます（80字以上）")
    return errs
