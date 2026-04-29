#!/usr/bin/env python3
"""URLからQRコードPNGを生成する。

使い方:
    python3 generate_qr.py <url> <出力ファイル名(任意)>

例:
    python3 generate_qr.py https://gosuenaga.github.io/kage-handoff/dhu-content-design-b/ dhu_handoff_qr.png
"""
import sys
import subprocess

try:
    import qrcode
except ImportError:
    print("qrcode が未インストールです。インストールします…")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "qrcode[pil]"])
    import qrcode

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    url = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "qr.png"
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=14,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0a0a0a", back_color="#ffffff")
    img.save(out)
    print(f"OK: {out}  ({url})")

if __name__ == "__main__":
    main()
