# orient — クリエイティブ・オリエン（ゲート付きハンドオフ・インデックス）

GitHub Pages 上で配信する、関係者のみアクセスできる**クライアントサイド・ゲート**付きのインデックス。  
公開URL：**https://gosuenaga.github.io/kage-handoff/orient/**

## 認証
- 入力ボックスに**登録メールアドレス**を入れて「開く」で解錠
- マスター鍵：**`go`**（ゴウさん用バックドア・他言禁止）
- 内部仕様：`SHA-256(入力(lowercased+trim) + salt)` のhex一致で開錠（`auth.json` の `keys`）

## メンバー追加（メールアドレス）
```
python3 hash_key.py designer@example.com kubo@cyberagent.co.jp ...
git add auth.json && git commit -m "auth: add members" && git push
```
追加した本人には**生メアド**（小文字でtrim版）を伝えるだけでOK。チャットにハッシュは貼らない。

## オリエン項目の追加（公開する納品物を増やす）
`data.json` の `deliveries` 配列に追記してコミット&プッシュ：
```json
{
  "date": "YYYY-MM-DD",
  "title": "案件名 — 何回目のハンドオフ",
  "desc": "短い説明",
  "tags": ["RAG","広告業界"],
  "links": [
    { "label": "Dropbox 共有フォルダ", "url": "https://www.dropbox.com/..." }
  ]
}
```
日付は新しい順に自動でソート。

## 検索対策
- 全ページに `<meta name="robots" content="noindex,nofollow,noarchive,nosnippet">`
- `orient/robots.txt` で `Disallow: /`
- 共有URLは関係者以外に出さない（拡散リスク=URL知っている人 + メールアドレス）
- 真の機密はここに置かない（GH Pages は技術的には全ファイル公開）

## セキュリティ前提（重要）
- これは**「鍵を持つ関係者だけが見る」を目的とした門番**であり、強い秘密保全用ではない。
- `auth.json` は公開ファイル（ハッシュは見える）。サルトはコードに同梱（理論上ブルートフォース可）。
- 真に秘密のものは Dropbox 側で個別に出すか、サーバー認証付きの別経路で。

## 実装メモ
- `index.html` 1枚に gate と app を内包、`auth.json` / `data.json` を fetch
- 認証は localStorage に保存（同一ブラウザでは再入力不要）。ログアウトボタンで解除。
- GH Pages の publish は repo の Pages 設定に従う（main ブランチ）。
