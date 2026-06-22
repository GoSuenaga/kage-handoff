#!/usr/bin/env python3
# caship.jp へのコンテンツ更新専用（ドメイン/SSLは作成済み前提）。
# 既存の caship 専用FTP（.env XSERVER_CASHIP_FTP_PASS）で public_html へFTPSアップロードのみ。
import os, ssl, sys, ftplib, pathlib

ENV   = os.path.expanduser("~/dev/hal/.env")
LOCAL = pathlib.Path(__file__).resolve().parent
FTP_HOST = "sv17075.xserver.jp"
FTP_ACCOUNT = "caship@caship.jp"
UPLOAD_FILES = ["index.html", ".htaccess"]
UPLOAD_DIRS  = ["assets"]

def env(k, d=None):
    if not os.path.exists(ENV): return d
    for ln in open(ENV, encoding="utf-8", errors="replace"):
        if ln.startswith(k + "="):
            return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return d

PW = env("XSERVER_CASHIP_FTP_PASS")
if not PW: sys.exit("✗ .env に XSERVER_CASHIP_FTP_PASS がありません。")

def connect():
    f = ftplib.FTP_TLS(context=ssl.create_default_context())
    f.connect(FTP_HOST, 21, timeout=40); f.login(FTP_ACCOUNT, PW); f.prot_p()
    return f

def find_root(f):
    for c in ["public_html", "caship.jp/public_html", "/"]:
        try:
            f.cwd("/")
            for p in c.strip("/").split("/"):
                if p: f.cwd(p)
            f.nlst(); return f.pwd()
        except ftplib.error_perm:
            continue
    sys.exit("✗ public_html が見つかりません。")

def ensure(f, path):
    f.cwd("/")
    for p in path.strip("/").split("/"):
        if not p: continue
        try: f.cwd(p)
        except ftplib.error_perm: f.mkd(p); f.cwd(p)

f = connect(); ROOT = find_root(f); print(f"root: {ROOT}")
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
print(f"✅ {n} ファイル → https://caship.jp/")
