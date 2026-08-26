#!/usr/bin/env python3
"""Gera public/og-lixeiras.jpg — a imagem que aparece quando alguém compartilha o link.

Ela não pode ir embutida no index.html: WhatsApp, Facebook e LinkedIn só leem
`og:image` com URL absoluta e ignoram data URI. Por isso é arquivo de verdade, e
o deploy.yml a sobe ao lado do index.html.

A peça é montada em HTML (mesma foto, mesma fonte e mesma paleta do hero) e
fotografada com o Chrome headless — assim ela continua reproduzível se o texto
ou a foto mudarem.
"""
import os
import subprocess
import sys

from build import find  # resolve assets/<nome>.<ext> e devolve (caminho, mime)

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, "_og.html")          # rascunho, ignorado pelo .gitignore
PNG = os.path.join(HERE, "_og.png")
OUT = os.path.join(HERE, "public", "og-lixeiras.jpg")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# 1200x630 é o formato que as redes recortam sem cortar nada (proporção 1.905:1).
LARGURA, ALTURA = 1200, 630

TITULO = "LIXEIRAS PARA<br>COLETA SELETIVA"
LINHA = "Aço inox, plásticas e urbanas — para empresas e condomínios"


def data_uri(nome):
    import base64
    path, mime = find(nome)
    return "data:%s;base64,%s" % (mime, base64.b64encode(open(path, "rb").read()).decode())


def main():
    html = f"""<!DOCTYPE html><html lang="pt-BR"><meta charset="utf-8"><style>
@font-face{{font-family:'Poppins';font-weight:500;src:url({data_uri('font_poppins_500')}) format('woff2')}}
@font-face{{font-family:'Poppins';font-weight:800;src:url({data_uri('font_poppins_800')}) format('woff2')}}
*{{margin:0;box-sizing:border-box}}
body{{width:{LARGURA}px;height:{ALTURA}px;overflow:hidden;position:relative;background:#0E4527;font-family:Poppins}}
img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 35%}}
/* Mesmo véu do hero da LP: escurece a esquerda para o texto assentar e deixa as
   quatro lixeiras do padrão CONAMA aparecendo à direita. */
.veu{{position:absolute;inset:0;background:
  linear-gradient(100deg, rgba(14,69,39,.94) 0%, rgba(14,69,39,.86) 34%, rgba(14,69,39,.40) 56%, rgba(14,69,39,.08) 76%),
  linear-gradient(180deg, rgba(0,0,0,.20), rgba(0,0,0,.32))}}
.copy{{position:absolute;left:64px;top:50%;transform:translateY(-50%);width:560px;z-index:2;color:#fff}}
h1{{font-weight:800;font-size:66px;line-height:1.04;letter-spacing:-.025em;text-shadow:0 2px 18px rgba(0,0,0,.35)}}
.regua{{width:120px;height:6px;border-radius:3px;background:#FFBA2F;margin:26px 0 22px}}
p{{font-weight:500;font-size:25px;line-height:1.4;color:#EAF6EF;text-shadow:0 1px 12px rgba(0,0,0,.4)}}
.marca{{position:absolute;left:64px;bottom:48px;z-index:2;font-weight:800;font-size:22px;letter-spacing:.16em;color:#FFBA2F}}
</style>
<img src="{data_uri('hero_bg')}" alt="">
<div class="veu"></div>
<div class="copy"><h1>{TITULO}</h1><div class="regua"></div><p>{LINHA}</p></div>
<div class="marca">ECOSOLI</div>
</html>"""
    open(TMP, "w", encoding="utf-8").write(html)

    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={LARGURA},{ALTURA}", f"--screenshot={PNG}",
                    "file://" + TMP], check=True, capture_output=True)

    from PIL import Image
    im = Image.open(PNG).convert("RGB")
    if im.size != (LARGURA, ALTURA):
        im = im.resize((LARGURA, ALTURA), Image.LANCZOS)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    im.save(OUT, quality=84, optimize=True, progressive=True)
    os.remove(PNG)

    print("OK -> %s  (%dx%d, %.0f KB)" % (os.path.relpath(OUT, HERE), *im.size,
                                          os.path.getsize(OUT) / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
