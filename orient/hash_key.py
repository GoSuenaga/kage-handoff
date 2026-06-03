#!/usr/bin/env python3
"""orient gate のメンバー鍵（メールアドレス）を auth.json に追加するヘルパー。

使い方:
    python3 hash_key.py designer1@example.com designer2@example.com ...
    → 入力をすべて小文字/trimし、SHA-256(入力 + salt) で 16進ハッシュ化、
       auth.json の keys 配列に重複なく追加して保存します。
       マスター鍵 'go' は既に登録済み。教える必要なし。
"""
import hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTH = HERE / "auth.json"

def hash_one(s, salt):
    norm = (s or "").strip().lower()
    return hashlib.sha256((norm + salt).encode("utf-8")).hexdigest()

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    data = json.loads(AUTH.read_text(encoding="utf-8"))
    salt = data["salt"]
    keys = set(data.get("keys", []))
    added = []
    for v in sys.argv[1:]:
        h = hash_one(v, salt)
        if h not in keys:
            keys.add(h); added.append((v.strip().lower(), h))
    data["keys"] = sorted(keys)
    AUTH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not added:
        print("変更なし（全て登録済み）"); return
    for v, h in added:
        print(f"+ {v}  →  {h}")
    print(f"\n{len(added)} 件追加。総鍵数: {len(keys)}。コミット&プッシュしてください。")

if __name__ == "__main__":
    main()
