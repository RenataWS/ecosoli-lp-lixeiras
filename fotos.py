#!/usr/bin/env python3
"""Monta as fotos de produto da LP a partir das fotos reais em `produtos/`.

    python3 fotos.py            # gera as cenas
    python3 fotos.py --preview  # grava também um contato em /tmp para conferir

São três tipos de cena.

**Cena de estúdio** (os cards do portfólio): fundo claro montado aqui mesmo, com
as peças recortadas do fundo branco do acervo.

**Cena de ambiente** (hero e três dos quatro cartões de "Ambientes atendidos"): parte
da geração de IA que já existia em `magnific/` — o lobby, o escritório, o
corredor de hotel, a clínica, o condomínio — só que a lixeira genérica que a IA
desenhou é apagada e no lugar entra a peça real do catálogo, com a luz, a sombra
e o reflexo daquela cena. O ambiente continua ilustração; o produto passa a ser
o que a Ecosoli vende de fato.

**Cena com piso montado** (o cartão de condomínio): a faixa alta de uma dessas
gerações entra inteira, porque ali não há lixeira desenhada nenhuma, e o chão da
frente é construído a partir da cor do piso da própria foto. É a saída para peça
larga demais para caber numa cena já ocupada — ver as notas em CENAS.

Apagar o objeto é interpolação horizontal linha a linha entre o que sobrou dos
dois lados. Preserva a estratificação da cena — linha do piso, laje, horizonte —
que é o que o olho usa para ler o espaço, e perde os detalhes verticais, que a
peça nova cobre por cima. Por isso as caixas de `apagar` são só as faixas que
a peça nova não alcança — apagar o objeto inteiro levaria junto o piso e o fundo.

Cada cena é montada no dobro do tamanho final e reduzida no fim (supersampling),
porque as bordas recortadas ficam duras quando compostas no tamanho de uso.

O enquadramento não é livre — ver as notas em CENAS.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PROD = os.path.join(HERE, "produtos")
ASSETS = os.path.join(HERE, "assets")
MAGNIFIC = os.path.join(HERE, "magnific")

SUPER = 2  # fator de supersampling


# ── recorte da peça ────────────────────────────────────────────────────────────

def recortar(nome, thresh=30, lado_max=3000):
    """Devolve a peça em RGBA, já aparada na sua caixa de conteúdo.

    Fundo branco de estúdio sai por preenchimento a partir das bordas — não por
    limiar de luminância, que comeria o corpo branco das lixeiras pintadas e os
    reflexos do inox polido.
    """
    caminho = achar(nome)
    im = Image.open(caminho)

    if im.mode in ("RGBA", "LA"):                     # já veio com transparência
        im = im.convert("RGBA")
    else:
        im = im.convert("RGB")
        if max(im.size) > lado_max:
            im.thumbnail((lado_max, lado_max), Image.LANCZOS)
        w, h = im.size
        tela = im.copy()
        MAGENTA = (255, 0, 255)
        bordas = ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
                  (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2))
        for xy in bordas:
            ImageDraw.floodfill(tela, xy, MAGENTA, thresh=thresh)
        a = np.asarray(tela)
        fundo = (a[:, :, 0] == 255) & (a[:, :, 1] == 0) & (a[:, :, 2] == 255)
        mascara = Image.fromarray(np.where(fundo, 0, 255).astype(np.uint8))
        mascara = mascara.filter(ImageFilter.GaussianBlur(1.2))
        m = np.asarray(mascara).astype(np.float32)
        m = np.clip((m - 90) * (255 / 125), 0, 255)   # aperta a transição, mata o halo
        im = im.convert("RGBA")
        im.putalpha(Image.fromarray(m.astype(np.uint8)))

    return aparar(im)


def achar(nome):
    for ext in (".jpg", ".jpeg", ".png"):
        p = os.path.join(PROD, nome + ext)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(nome)


def aparar(im, limiar=12):
    a = np.asarray(im)[:, :, 3]
    ys, xs = np.where(a > limiar)
    if len(xs) == 0:
        return im
    return im.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))


# ── fundos de estúdio ──────────────────────────────────────────────────────────

def fundo_claro(w, h):
    """Estúdio claro, com um leve piso — combina com o branco do card."""
    y = np.linspace(0, 1, h)[:, None]
    x = np.linspace(0, 1, w)[None, :]
    base = np.zeros((h, w, 3), np.float32)
    topo = np.array([255, 255, 255], np.float32)
    baixo = np.array([225, 234, 229], np.float32)
    t = np.clip((y - 0.15) / 0.85, 0, 1) ** 1.4
    for i in range(3):
        base[:, :, i] = topo[i] * (1 - t) + baixo[i] * t
    vinheta = 1 - 0.10 * (((x - 0.5) * 2) ** 2 + ((y - 0.45) * 1.6) ** 2)
    base *= np.clip(vinheta, 0, 1)[:, :, None]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


# ── fundo de ambiente: apagar o objeto gerado ──────────────────────────────────

def apagar(im, caixa, margem=0.006, suavizar=6):
    """Tira da cena o objeto que a IA desenhou. `caixa` em coordenadas relativas."""
    W, H = im.size
    x0, x1 = int(caixa[0] * W), int(caixa[1] * W)
    y0, y1 = int(caixa[2] * H), int(caixa[3] * H)
    m = max(4, int(margem * W))
    a = np.asarray(im).astype(np.float32)

    esq = a[y0:y1, max(0, x0 - m):x0].mean(axis=1)
    dire = a[y0:y1, x1:x1 + m].mean(axis=1)
    t = np.linspace(0, 1, x1 - x0, dtype=np.float32)[None, :, None]
    a[y0:y1, x0:x1] = esq[:, None, :] * (1 - t) + dire[:, None, :] * t

    im.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), (0, 0))

    pad = max(12, int(0.018 * W))               # costura das bordas do remendo
    cx0, cy0 = max(0, x0 - pad), max(0, y0 - pad)
    cx1, cy1 = min(W, x1 + pad), min(H, y1 + pad)
    reg = im.crop((cx0, cy0, cx1, cy1))
    bor = reg.filter(ImageFilter.GaussianBlur(suavizar))
    mask = Image.new("L", reg.size, 0)
    ImageDraw.Draw(mask).rectangle([pad - 14, pad - 14, reg.width - pad + 14,
                                    reg.height - pad + 14], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(12))
    im.paste(Image.composite(bor, reg, mask), (cx0, cy0))


def grao(im, forca=2.4, semente=7):
    """Devolve grão à área remendada, que sai lisa demais da interpolação."""
    a = np.asarray(im).astype(np.float32)
    a += np.random.default_rng(semente).normal(0, forca, a.shape)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ── luz, sombra e reflexo ──────────────────────────────────────────────────────

def acender(p, quente=1.07, frio=0.90, brilho=0.86, lado=0.26):
    """Casa a peça (estúdio, luz neutra e chapada) com a luz da cena.

    `lado` inclina a iluminação para o lado de onde vem a luz na foto; sem isso a
    peça fica plana e denuncia a montagem.
    """
    rgb = np.asarray(p.convert("RGB")).astype(np.float32)
    g = np.linspace(1.0 + lado * 0.35, 1.0 - lado, rgb.shape[1], dtype=np.float32)[None, :, None]
    rgb *= g
    rgb[:, :, 0] *= quente
    rgb[:, :, 2] *= frio
    rgb *= brilho
    out = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    return Image.merge("RGBA", (*out.split(), p.getchannel("A")))


def sombra_projetada(larg, opac=0.42, alonga=2.3, inclina=1.25, desfoque=0.10, cor=(24, 15, 6)):
    """Elipse esticada na direção oposta à luz, apagando com a distância.

    A silhueta achatada do próprio objeto não serve para um cilindro: vira um
    retângulo duro. Uma elipse com decaimento lê como sombra de luz baixa.
    """
    W = int(larg * alonga) + int(larg * abs(inclina)) + 40
    H = int(larg * 0.62) + 40
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.ellipse([20, H // 2 - int(larg * 0.16), 20 + int(larg * alonga), H // 2 + int(larg * 0.16)],
              fill=255)
    m = m.transform(m.size, Image.AFFINE, (1, -inclina, 0, 0, 1, 0), Image.BICUBIC)
    a = np.asarray(m).astype(np.float32)
    queda = np.linspace(1.0, 0.05, W, dtype=np.float32)[None, :] ** 1.6
    if inclina < 0:
        queda = queda[:, ::-1]
    m = Image.fromarray(np.clip(a * queda * opac, 0, 255).astype(np.uint8))
    m = m.filter(ImageFilter.GaussianBlur(max(4, larg * desfoque)))
    t = Image.new("RGBA", m.size, cor + (0,))
    t.putalpha(m)
    return t


def oclusao(larg, opac=0.72, cor=(10, 7, 2)):
    """O escuro logo debaixo da peça — é o que assenta o objeto no chão."""
    W, H = int(larg * 1.15), max(8, int(larg * 0.30))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([int(W * 0.06), int(H * 0.30), int(W * 0.94), int(H * 0.86)],
                              fill=int(255 * opac))
    m = m.filter(ImageFilter.GaussianBlur(max(3, larg * 0.045)))
    t = Image.new("RGBA", m.size, cor + (0,))
    t.putalpha(m)
    return t


def reflexo(p, compressao=0.55, opac=0.30, desfoque=3.0):
    """Reflexo no piso polido: espelhado, comprimido pela perspectiva e sumindo."""
    esp = p.transpose(Image.FLIP_TOP_BOTTOM)
    alt = max(2, int(esp.height * compressao))
    esp = esp.resize((esp.width, alt), Image.LANCZOS)
    g = (np.linspace(1.0, 0.0, alt, dtype=np.float32) ** 1.35)[:, None] * opac
    a = np.asarray(esp.getchannel("A")).astype(np.float32) * g
    esp.putalpha(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    return esp.filter(ImageFilter.GaussianBlur(desfoque))


# ── composição ─────────────────────────────────────────────────────────────────

def colocar(tela, item, luz):
    """Encaixa a peça pela base, na altura e no centro horizontal pedidos."""
    W, H = tela.size
    p = recortar(item["arq"], thresh=item.get("thresh", 30))
    alt = int(H * item["altura"])
    larg = max(1, int(p.width * alt / p.height))
    p = p.resize((larg, alt), Image.LANCZOS)
    p = acender(p, **{**luz, **item.get("luz", {})})
    if item.get("desfoque"):
        p = p.filter(ImageFilter.GaussianBlur(item["desfoque"] * SUPER))

    x = int(W * item["x"] - larg / 2)
    yb = int(H * item["base"])

    if item.get("sombra", True):
        s = sombra_projetada(larg, **item.get("sombra_ops", {}))
        dx = -int(larg * 0.10) if s.width > larg else 0
        tela.alpha_composite(s, (x + dx, yb - s.height // 2))
        o = oclusao(larg, **item.get("oclusao_ops", {}))
        tela.alpha_composite(o, (x - (o.width - larg) // 2, yb - o.height // 2))
    if item.get("reflexo"):
        tela.alpha_composite(reflexo(p, **item["reflexo"]), (x, yb - 2))
    tela.alpha_composite(p, (x, yb - alt))


def montar(cena):
    W, H = cena["tam"]
    w, h = W * SUPER, H * SUPER

    amb = cena.get("ambiente")
    if amb:
        fundo = Image.open(os.path.join(MAGNIFIC, amb["foto"])).convert("RGB")
        for caixa in amb.get("apagar", []):
            apagar(fundo, caixa)
        if amb.get("recorte"):
            rx0, rx1, ry0, ry1 = amb["recorte"]
            fw, fh = fundo.size
            fundo = fundo.crop((int(rx0 * fw), int(ry0 * fh), int(rx1 * fw), int(ry1 * fh)))
        fundo = fundo.resize((w, h), Image.LANCZOS)
        if amb.get("apagar"):
            fundo = grao(fundo)
    else:
        fundo = fundo_claro(w, h)

    tela = fundo.convert("RGBA")
    luz = cena.get("luz", {})
    for item in cena.get("pecas", []):
        colocar(tela, item, luz)

    out = tela.convert("RGB").resize((W, H), Image.LANCZOS)
    out = out.filter(ImageFilter.UnsharpMask(radius=1.1, percent=52, threshold=3))
    return out


# ── cenas ──────────────────────────────────────────────────────────────────────
# A ordem das cores é a da CONAMA 275: azul (papel), vermelho (plástico), verde
# (vidro), amarelo (metal). Manter as quatro visíveis no hero foi pedido
# explícito, e é isso que amarra o enquadramento: o hero é `object-fit:cover`, e
# quanto mais estreita e alta a tela, menos da largura da foto sobra — em 1440px
# aparece inteira, num iPhone de 390px sobram 26%. Por isso são duas artes,
# trocadas por `<picture>` em 700px: a deitada e uma em pé.
#
# Nos cards vale a mesma lógica: no desktop o `.card-media` mostra só a faixa
# central da imagem, então a peça principal fica entre 30% e 70% da largura e as
# de apoio nas beiradas, que só aparecem no mobile.

LUZ_LOBBY = {"quente": 1.07, "frio": 0.90, "brilho": 0.86, "lado": 0.26}

CENAS = {
    # ── hero: lobby corporativo, luz de fim de tarde entrando pela esquerda ──
    "hero_bg": {
        "tam": (1800, 1012),
        "ambiente": {"foto": "heroBgA.jpg", "apagar": [(.473, .939, .188, 1.0)]},
        "luz": LUZ_LOBBY,
        "pecas": [
            {"arq": "conama_azul_papel",        "altura": .464, "x": .528, "base": .773,
             "desfoque": .45, "reflexo": {"opac": .26}},
            {"arq": "conama_vermelho_plastico", "altura": .516, "x": .603, "base": .808,
             "desfoque": .30, "reflexo": {"opac": .28}},
            {"arq": "conama_verde_vidro",       "altura": .573, "x": .689, "base": .848,
             "desfoque": .15, "reflexo": {"opac": .30}},
            {"arq": "conama_amarelo_metal",     "altura": .642, "x": .794, "base": .895,
             "reflexo": {"opac": .32}},
        ],
    },
    # No celular o recorte do cover deixa ver só de 33% a 91% da largura desta
    # arte — as quatro peças moram nessa faixa. O pedaço de lobby escolhido é o
    # da parede de vidro com o jardim, que dá textura ao terço superior, o único
    # que o texto do hero não cobre.
    "hero_bg_mobile": {
        "tam": (900, 1200),
        "ambiente": {"foto": "heroBgA.jpg", "apagar": [(.473, .939, .188, 1.0)],
                     "recorte": (.160, .580, .0, 1.0)},
        "luz": LUZ_LOBBY,
        "pecas": [
            {"arq": "conama_azul_papel",        "altura": .270, "x": .420, "base": .845,
             "desfoque": .45, "reflexo": {"opac": .26}},
            {"arq": "conama_vermelho_plastico", "altura": .285, "x": .553, "base": .872,
             "desfoque": .30, "reflexo": {"opac": .28}},
            {"arq": "conama_verde_vidro",       "altura": .300, "x": .686, "base": .900,
             "desfoque": .15, "reflexo": {"opac": .30}},
            {"arq": "conama_amarelo_metal",     "altura": .315, "x": .810, "base": .930,
             "reflexo": {"opac": .32}},
        ],
    },

    # ── ambientes atendidos ──
    "opt_amb_escritorio": {
        "tam": (1000, 1325),
        # a estação gerada ocupa 78% da largura: apagá-la inteira levaria junto o
        # piso e as mesas do fundo. Só se apaga a faixa do topo dela, que as
        # peças novas não alcançam; o resto some coberto.
        "ambiente": {"foto": "amb_escritorio.jpg",
                     "apagar": [(.06, .94, .29, .47), (.10, .92, .86, 1.0)]},
        "luz": {"quente": 1.02, "frio": 0.98, "brilho": 0.96, "lado": 0.16},
        "pecas": [
            {"arq": "quadrada_azul_papel", "thresh": 12,        "altura": .500, "x": .250, "base": .905,
             "desfoque": .20, "reflexo": {"opac": .14}},
            {"arq": "quadrada_vermelha_plastico", "thresh": 12, "altura": .520, "x": .500, "base": .925,
             "desfoque": .10, "reflexo": {"opac": .15}},
            {"arq": "quadrada_verde_vidro", "thresh": 12,       "altura": .540, "x": .755, "base": .945,
             "reflexo": {"opac": .16}},
        ],
    },
    "opt_amb_hotel": {
        "tam": (1000, 1325),
        "ambiente": {"foto": "amb_hotel.jpg", "apagar": [(.13, .91, .49, 1.0)]},
        "luz": {"quente": 1.14, "frio": 0.78, "brilho": 0.60, "lado": 0.30},
        "pecas": [
            {"arq": "conama_azul_papel",    "altura": .620, "x": .330, "base": 1.03,
             "desfoque": .15, "reflexo": {"opac": .10}},
            {"arq": "conama_amarelo_metal", "altura": .640, "x": .700, "base": 1.05,
             "reflexo": {"opac": .10}},
        ],
    },
    "opt_amb_clinica": {
        "tam": (1000, 1325),
        "ambiente": {"foto": "amb_clinica.jpg", "apagar": [(.28, .68, .46, .94)]},
        "luz": {"quente": 1.0, "frio": 1.01, "brilho": 1.0, "lado": 0.14},
        "pecas": [
            {"arq": "pedal_verde_vidro", "altura": .385, "x": .470, "base": .888,
             "reflexo": {"opac": .18},
             "oclusao_ops": {"opac": .58},
             "sombra_ops": {"opac": .34, "alonga": 2.0, "inclina": -1.2}},
        ],
    },
    # Esta é a única das cinco que não monta nada: chega pronta do cliente, com o
    # conjunto na barra de suporte — o que mais vende para condomínio — já na
    # cena. Três montagens foram tentadas antes e reprovadas; o conjunto tem
    # 1,85 m de largura por 0,96 m de altura e, na escala da cena que existia
    # aqui, não cabia sem ficar plantado no meio da circulação. A foto nova
    # resolve na origem. Só o enquadramento passa por aqui: 1089x1444 é o mesmo
    # 3:4 do cartão, então a redução não corta nada.
    "opt_amb_condominio": {
        "tam": (1000, 1325),
        "ambiente": {"foto": "amb_condominio_conjunto.png"},
    },

    # ── cards do portfólio: estúdio ──
    "opt_p_inox": {
        "tam": (1000, 667),
        "luz": {"quente": 1.0, "frio": 1.0, "brilho": 1.0, "lado": 0.0},
        "pecas": [
            {"arq": "inox_quadrada_aberta", "altura": .56, "x": .150, "base": .88,
             "sombra_ops": {"opac": .22, "alonga": 1.7, "inclina": .5}},
            {"arq": "inox_basculante",      "altura": .44, "x": .855, "base": .88,
             "sombra_ops": {"opac": .22, "alonga": 1.7, "inclina": .5}},
            {"arq": "inox_meialua",         "altura": .74, "x": .50,  "base": .93,
             "sombra_ops": {"opac": .26, "alonga": 1.8, "inclina": .5}},
        ],
    },
    "opt_p_pilhas": {
        "tam": (1000, 667),
        "luz": {"quente": 1.0, "frio": 1.0, "brilho": 1.0, "lado": 0.0},
        "pecas": [
            {"arq": "pilhas_cilindrica", "altura": .58, "x": .170, "base": .90,
             "sombra_ops": {"opac": .22, "alonga": 1.7, "inclina": .5}},
            {"arq": "pilhas_frontal",    "altura": .60, "x": .850, "base": .90,
             "sombra_ops": {"opac": .18, "alonga": 1.7, "inclina": .5}},
            {"arq": "pilhas_quadrada",   "altura": .78, "x": .50,  "base": .94,
             "sombra_ops": {"opac": .26, "alonga": 1.8, "inclina": .5}},
        ],
    },
    "opt_p_urbana": {
        "tam": (1000, 667),
        "luz": {"quente": 1.0, "frio": 1.0, "brilho": 1.0, "lado": 0.0},
        "pecas": [
            {"arq": "urbana_dupla", "altura": .60, "x": .180, "base": .90,
             "sombra_ops": {"opac": .20, "alonga": 1.7, "inclina": .5}},
            {"arq": "urbana_pes",   "altura": .80, "x": .530, "base": .95,
             "sombra_ops": {"opac": .24, "alonga": 1.8, "inclina": .5}},
        ],
    },
}


def main():
    os.makedirs(ASSETS, exist_ok=True)
    alvo = [a for a in sys.argv[1:] if not a.startswith("--")]
    feitas = []
    for nome, cena in CENAS.items():
        if alvo and nome not in alvo:
            continue
        im = montar(cena)
        destino = os.path.join(ASSETS, nome + ".webp")
        im.save(destino, "WEBP", quality=80, method=6)
        feitas.append((nome, im))
        print("OK -> assets/%-22s %dx%d  %5.0f KB" %
              (nome + ".webp", *im.size, os.path.getsize(destino) / 1024))

    if "--preview" in sys.argv:
        larg = 700
        cols = [im.resize((larg, int(im.height * larg / im.width)), Image.LANCZOS)
                for _, im in feitas]
        contato = Image.new("RGB", (larg, sum(c.height + 8 for c in cols)), "white")
        y = 0
        for c in cols:
            contato.paste(c, (0, y))
            y += c.height + 8
        contato.save("/tmp/ecobin/preview_cenas.jpg", quality=88)
        print("preview -> /tmp/ecobin/preview_cenas.jpg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
