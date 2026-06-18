#!/usr/bin/env python3
# caship.jp を XServer に丸ごと立ち上げて公開する全自動スクリプト。
# 前提（末永さんの唯一の手作業）: ~/dev/hal/.env に XSERVER_API_KEY=xs_... を1行追記済み。
#   APIキーは「対象サーバー xs630349 / 権限フル（ドメイン・DNS・FTP・SSL・サーバー情報）」で発行。
#
# やること:
#   1. server-info 取得（所有権トークン確認・hostname照合）
#   2. caship.jp の所有権確認TXTをDNSに登録（XServer DNS）
#   3. caship.jp をサーバーに追加（公開領域/vhost作成 + 無料SSL自動発行）
#   4. caship.jp 専用FTPアカウント作成（パスワードは生成して .env に保存）
#   5. サイト(index.html / assets / .htaccess)を public_html へFTPSアップロード
#   6. 反映状況を表示
# 何度流しても安全（既存はスキップ/無視）。

import os, ssl, sys, json, time, secrets, string, ftplib, pathlib, urllib.request, urllib.error

ENV   = os.path.expanduser("~/dev/hal/.env")
LOCAL = pathlib.Path(__file__).resolve().parent          # caship/
API   = "https://api.xserver.ne.jp/v1"
SERVERNAME = "xs630349.xsrv.jp"                            # 契約時の初期ドメイン（server_id=xs630349）
DOMAIN     = "caship.jp"
FTP_HOST   = "sv17075.xserver.jp"
FTP_ACCOUNT= f"caship@{DOMAIN}"
UPLOAD_FILES = ["index.html", ".htaccess"]
UPLOAD_DIRS  = ["assets"]

def env(k, d=None):
    if not os.path.exists(ENV): return d
    for ln in open(ENV, encoding="utf-8", errors="replace"):
        if ln.startswith(k + "="):
            return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return d

def env_set(k, v):
    lines, found = [], False
    if os.path.exists(ENV):
        for ln in open(ENV, encoding="utf-8", errors="replace"):
            if ln.startswith(k + "="):
                lines.append(f"{k}={v}\n"); found = True
            else:
                lines.append(ln)
    if not found:
        if lines and not lines[-1].endswith("\n"): lines[-1] += "\n"
        lines.append(f"{k}={v}\n")
    open(ENV, "w", encoding="utf-8").writelines(lines)

KEY = env("XSERVER_API_KEY")
if not KEY:
    sys.exit("✗ ~/dev/hal/.env に XSERVER_API_KEY=xs_... がありません。パネルのAPIキー管理で発行して追記してください。")

def api(method, path, body=None):
    url = API + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {KEY}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try: payload = json.loads(raw)
        except Exception: payload = {"raw": raw}
        return e.code, payload

# ── 1. server-info ───────────────────────────────────────────────
print(f"→ server-info ({SERVERNAME})")
st, info = api("GET", f"/server/{SERVERNAME}/server-info")
if st != 200:
    sys.exit(f"✗ server-info 失敗 HTTP {st}: {info}\n   SERVERNAME が違う可能性。パネルの初期ドメイン(xs######.xsrv.jp)を確認。")
token = info.get("domain_validation_token")
print(f"  hostname={info.get('hostname')} server_id={info.get('server_id')}")
print(f"  validation_token={'取得OK' if token else '無し'}")

# ── 2. 所有権確認TXT を DNS 登録（冪等）──────────────────────────
if token:
    txt = {"domain": DOMAIN, "host": "_xserver-verify", "type": "TXT",
           "content": f"xserver-verify={token}", "ttl": 3600}
    st, res = api("POST", f"/server/{SERVERNAME}/dns", txt)
    print(f"→ TXT _xserver-verify.{DOMAIN}  HTTP {st}: {res if st>=400 else 'OK'}")
    time.sleep(5)

# ── 3. ドメイン追加 + 無料SSL（冪等）────────────────────────────
st, res = api("POST", f"/server/{SERVERNAME}/domain", {"domain": DOMAIN, "ssl": True})
print(f"→ domain add {DOMAIN}  HTTP {st}: {json.dumps(res, ensure_ascii=False)}")
if st >= 400 and "exist" not in json.dumps(res).lower() and "登録済" not in json.dumps(res):
    print("  ⚠ ドメイン追加で警告。既存なら無視して続行。応答を確認のこと。")

# ── 4. caship 専用FTPアカウント作成（冪等）──────────────────────
ftp_pass = env("XSERVER_CASHIP_FTP_PASS")
if not ftp_pass:
    alph = string.ascii_letters + string.digits + "!#%@-_"
    ftp_pass = "".join(secrets.choice(alph) for _ in range(20))
ftp_body = {"ftp_account": FTP_ACCOUNT, "password": ftp_pass,
            "directory": f"/{DOMAIN}/public_html", "memo": "caship deploy"}
st, res = api("POST", f"/server/{SERVERNAME}/ftp", ftp_body)
print(f"→ ftp account {FTP_ACCOUNT}  HTTP {st}: {json.dumps(res, ensure_ascii=False)}")
if st < 400:
    env_set("XSERVER_CASHIP_FTP_PASS", ftp_pass)
    print("  FTPパスワードを .env (XSERVER_CASHIP_FTP_PASS) に保存")
elif "exist" in json.dumps(res).lower() or "登録済" in json.dumps(res):
    if not env("XSERVER_CASHIP_FTP_PASS"):
        sys.exit("✗ FTPアカウントは既存だが .env にパスワードが無い。パネルでFTPパスワードを再設定→.env XSERVER_CASHIP_FTP_PASS に保存して再実行。")
    print("  FTPアカウントは既存。保存済みパスワードで続行。")
else:
    sys.exit(f"✗ FTPアカウント作成失敗: {res}")

# SSL/DNS反映を少し待つ（FTP領域生成のため）
print("→ 公開領域の生成待ち 20s ...")
time.sleep(20)

# ── 5. FTPS アップロード ────────────────────────────────────────
def connect():
    f = ftplib.FTP_TLS(context=ssl.create_default_context())
    f.connect(FTP_HOST, 21, timeout=40); f.login(FTP_ACCOUNT, ftp_pass); f.prot_p()
    return f

def find_root(f):
    for c in ["public_html", f"{DOMAIN}/public_html", "/"]:
        try:
            f.cwd("/")
            for p in c.strip("/").split("/"):
                if p: f.cwd(p)
            f.nlst(); return f.pwd()
        except ftplib.error_perm:
            continue
    sys.exit("✗ public_html が見つかりません。SSL/領域生成待ちで再実行を。")

def ensure(f, path):
    f.cwd("/")
    for p in path.strip("/").split("/"):
        if not p: continue
        try: f.cwd(p)
        except ftplib.error_perm: f.mkd(p); f.cwd(p)

print(f"→ FTPS {FTP_ACCOUNT}@{FTP_HOST}")
f = connect()
ROOT = find_root(f)
print(f"  upload root: {ROOT}")
n = 0
for fn in UPLOAD_FILES:
    p = LOCAL / fn
    if p.exists():
        ensure(f, ROOT)
        with open(p, "rb") as fh: f.storbinary(f"STOR {fn}", fh)
        n += 1; print(f"  ↑ {fn}")
for d in UPLOAD_DIRS:
    base = LOCAL / d
    if base.exists():
        for root, _, files in os.walk(base):
            rel = os.path.relpath(root, LOCAL)
            ensure(f, f"{ROOT}/{rel}")
            for fn in files:
                if fn == ".DS_Store": continue
                with open(os.path.join(root, fn), "rb") as fh: f.storbinary(f"STOR {fn}", fh)
                n += 1; print(f"  ↑ {rel}/{fn}")
f.quit()
print(f"✅ アップロード {n} ファイル完了 → https://{DOMAIN}/")
print("   ※ SSL発行直後は数分〜最大1時間 https が不安定なことあり。少し待って確認。")
