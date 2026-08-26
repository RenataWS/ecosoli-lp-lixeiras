#!/usr/bin/env python3
"""Injeta os assets (fontes + imagens) como data URI no template e gera a LP final."""
import base64, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
TPL = os.path.join(HERE, "lp_template.html")
OUT = os.path.join(HERE, "ecosoli-lixeiras.html")

MIME = {".webp": "image/webp", ".woff2": "font/woff2", ".png": "image/png", ".jpg": "image/jpeg"}


def find(name):
    for ext in (".webp", ".woff2", ".png", ".jpg"):
        p = os.path.join(ASSETS, name + ext)
        if os.path.exists(p):
            return p, MIME[ext]
    raise FileNotFoundError(name)


def main():
    html = open(TPL, encoding="utf-8").read()
    used, missing = {}, []

    def sub(m):
        name = m.group(1)
        try:
            path, mime = find(name)
        except FileNotFoundError:
            missing.append(name)
            return ""
        if name not in used:
            raw = open(path, "rb").read()
            used[name] = "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode())
        return used[name]

    html = re.sub(r"\{\{ASSET:([a-zA-Z0-9_\-]+)\}\}", sub, html)

    if missing:
        print("ASSETS FALTANDO:", sorted(set(missing)), file=sys.stderr)
        return 1

    open(OUT, "w", encoding="utf-8").write(html)
    kb = os.path.getsize(OUT) / 1024
    print("OK -> %s  (%.0f KB, %d assets embutidos)" % (os.path.basename(OUT), kb, len(used)))
    for n, d in sorted(used.items(), key=lambda x: -len(x[1]))[:6]:
        print("   %-22s %5.0f KB" % (n, len(d) / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
