#!/usr/bin/env python3
"""Empacota o build num documento HTML completo, pronto para subir em qualquer host.

O arquivo gerado pelo build.py é um fragmento (o publicador de artifacts injeta o
esqueleto). Este script separa <head> de <body> e monta o documento final.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "ecosoli-lixeiras.html")
OUT = os.path.join(HERE, "index.html")

# Elementos que pertencem ao <head>. `title` e `style` são pares (têm fechamento);
# `meta` e `link` são vazios. Tratar `title` como vazio corta o head cedo demais.
PARES = ("title", "style")
VAZIOS = ("meta", "link", "base")


def main():
    frag = open(SRC, encoding="utf-8").read()

    head, i = [], 0
    while i < len(frag):
        resto = frag[i:]
        avanco = len(resto) - len(resto.lstrip())
        j = i + avanco
        resto = resto.lstrip()

        if resto.startswith("<!--"):          # comentário: pertence ao head enquanto estivermos nele
            fim = frag.index("-->", j) + 3
            i = fim
            continue

        m = re.match(r"<([a-zA-Z][a-zA-Z0-9]*)", resto)
        if not m:
            break
        tag = m.group(1).lower()

        if tag in PARES:
            fim = frag.index(f"</{tag}>", j) + len(tag) + 3
        elif tag in VAZIOS:
            fim = frag.index(">", j) + 1
        else:
            break                              # primeiro elemento de conteúdo: acabou o head

        head.append(frag[j:fim])
        i = fim

    head_html = "\n".join(head).strip()
    body_html = frag[i:].strip()

    doc = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#062718">
{head_html}
</head>
<body>
{body_html}
</body>
</html>
"""
    open(OUT, "w", encoding="utf-8").write(doc)

    # Verificação: nada pode ter se perdido no caminho.
    perdeu = []
    for marca in ("Lixeiras Para Coleta Seletiva", "SOLICITAR ORÇAMENTO PARA EMPRESA",
                  "+13 Anos de Experiência", "FAQPage", "wa.me/", "@font-face",
                  "og:image", 'rel="icon"', "catalogo-lixeiras-ecosoli.pdf"):
        if doc.count(marca) < frag.count(marca):
            perdeu.append(marca)
    if perdeu:
        print("ERRO — conteúdo perdido:", perdeu, file=sys.stderr)
        return 1

    print(f"OK -> index.html  ({os.path.getsize(OUT)/1024:.0f} KB)")
    print(f"   <head>: {len(head)} elementos   |   <body>: {len(body_html)/1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
