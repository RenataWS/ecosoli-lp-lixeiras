# Ecosoli — Landing Page de Lixeiras para Coleta Seletiva

Landing page de lixeiras para coleta seletiva e gestão de resíduos da **Ecosoli**
(Vinhedo/SP), construída a partir do briefing "LP Lixeiras".

Destino: `https://ecosolicnpj.com.br/lixeiras`

Repositório irmão: [`ecosoli-lp-filtros-cisternas`](https://github.com/RenataWS/ecosoli-lp-filtros-cisternas)
— mesma estrutura, mesma paleta e os mesmos assets de marca.

---

## O entregável

**`index.html`** — documento único, ~1,3 MB, pronto para subir em qualquer host.

Imagens e fontes vão embutidas em base64, então a página **não faz nenhuma
requisição externa**: funciona assim que o arquivo chega no servidor, sem
depender de CDN, de configuração de MIME type ou de plugin.

Duas coisas ficam de fora do base64, em **`public/`**:

- **`og-lixeiras.jpg`** — a imagem que aparece quando alguém compartilha o link.
  Precisa ser arquivo de verdade: WhatsApp, Facebook e LinkedIn só leem
  `og:image` com URL absoluta e ignoram data URI.
- **`catalogo-lixeiras-ecosoli.pdf`** — o catálogo de 19 páginas que a página
  oferece para download (o arquivo original do cliente é
  `Catalogo Ecosoli_Ecollux_Lixeiras Inox.pdf`; foi renomeado porque espaço e
  acento em nome de arquivo quebram a URL).

O `deploy.yml` sobe o conteúdo de `public/` ao lado do `index.html`, então os
dois respondem em `…/lixeiras/<arquivo>`. Mudar o nome de qualquer um dos dois
ou o diretório de destino quebra o que aponta para eles — no caso da imagem, as
redes cacheiam o resultado, então o estrago não se corrige sozinho.

Para publicar no HostGator, basta colocar o `index.html` e o conteúdo de
`public/` na pasta do subdiretório correspondente.

---

## Como editar

O `index.html` é gerado — não se edita nele. O fonte é o `lp_template.html`,
onde as imagens aparecem como marcadores `{{ASSET:nome}}` em vez de blocos de
base64, o que mantém o arquivo legível (52 KB contra 1,2 MB).

```bash
# 1. editar o conteúdo/estilo
$EDITOR lp_template.html

# 2. injetar os assets  →  ecosoli-lixeiras.html
python3 build.py

# 3. empacotar no documento completo  →  index.html
python3 standalone.py
```

`build.py` resolve cada `{{ASSET:nome}}` procurando `assets/nome.{webp,woff2,png,jpg}`
e falha se algum estiver faltando.

As nove fotos com produto — as duas do hero, os quatro cartões de ambiente e os
três cards de portfólio — não se editam à mão: são montadas por `fotos.py`, que
recorta as peças de `produtos/` e as compõe na cena. Mexer no enquadramento é
mexer no dicionário `CENAS`, e depois:

```bash
python3 fotos.py             # gera as nove
python3 fotos.py hero_bg     # ou só a cena que você mexeu
python3 fotos.py --preview   # grava um contato em /tmp para conferir antes
```

Se a foto do hero ou o texto da peça de compartilhamento mudarem, regerar a
imagem também:

```bash
python3 og.py    # → public/og-lixeiras.jpg
```

`og.py` monta a peça em HTML (mesma foto, fonte e paleta do hero), fotografa com
o Chrome headless e salva em 1200x630 — o formato que as redes recortam sem
cortar nada.

`standalone.py` separa `<head>` de `<body>` e monta o documento com `<!DOCTYPE>`,
`<html lang="pt-BR">` e as metatags no lugar certo. O template é um fragmento,
então essa etapa é obrigatória — sem ela as metatags de SEO caem dentro do
`<body>` e são ignoradas pelos buscadores. Ao final ele confere se nada se perdeu
no caminho, inclusive a linha de prova social do briefing.

---

## Publicar

O deploy é manual, pelo GitHub Actions:

```bash
gh workflow run deploy.yml -R RenataWS/ecosoli-lp-lixeiras -f server-dir=./
gh run watch -R RenataWS/ecosoli-lp-lixeiras
```

O workflow sobe apenas `index.html` e o conteúdo de `public/` por FTP, usando os
secrets `FTP_SERVER`, `FTP_USERNAME` e `FTP_PASSWORD`.

Depois de publicar, **confira a página com uma query string** —
`…/lixeiras/?v=1`. O site tem cache de página em disco com validade de 8 horas
(`cache-control: max-age=28800`), e ele guarda até resposta de 404: hoje
`/lixeiras/` devolve a página "não encontrada" do WordPress com status 200,
servida do cache. O arquivo real que o deploy sobe passa na frente do WordPress,
mas se a versão com `?v=1` mostrar a landing page e a versão sem mostrar o 404,
é só cache velho — purgar pelo painel do WordPress ou esperar as 8 horas.

**A conta FTP deste repositório não é a da LP de filtros e cisternas.** Lá o
home do usuário FTP já está dentro de `public_html/filtros-e-cisternas/`, e é
por isso que o `server-dir` padrão é `./`. Reaproveitar aqueles secrets aqui
sobrescreveria a outra landing page. Este repositório precisa de uma conta FTP
própria, com diretório `public_html/lixeiras`.

---

## Decisões que valem conhecer antes de mexer

**O texto é o do briefing, literalmente.** Headlines, sub-headlines, rótulos de
CTA e a prova social não foram reescritos nem "melhorados" — inclusive
`faturamento faturado para empresas cadastradas`, na lâmina de compra
corporativa, que parece erro de digitação mas está assim no documento original.
Corrigir só com validação do cliente.

**A página é fechada.** Todos os 14 CTAs abrem o WhatsApp, cada um com uma
mensagem de abertura própria que identifica de qual bloco da página o contato
veio — inclusive os `[VER LINHA ...]` de cada card de produto, que no briefing
apontariam para o catálogo. Não há formulário e o único link que tira o
visitante da página é o download do catálogo. O número fica na constante `WA`, e
é o mesmo publicado na LP de filtros e cisternas: `5519920033125`.

**O catálogo em PDF tem duas entradas, e nenhuma delas substitui um CTA.** Um
botão secundário translúcido (`.btn--vidro`) ao lado do CTA amarelo do hero, e a
faixa verde (`.catalogo`) no fim do portfólio. Os quatro `[VER LINHA ...]`
continuam indo para o WhatsApp: o catálogo é o caminho de quem quer especificar
antes de falar, não o de quem já quer comprar. Os links usam caminho absoluto de
raiz (`/lixeiras/catalogo-lixeiras-ecosoli.pdf`) porque o canonical é `/lixeiras`
sem barra final — com caminho relativo, quem chega por essa URL baixaria da raiz
do domínio e tomaria 404. **Se o slug mudar, esses dois `href` mudam junto.**
Vale saber que o PDF cobre inox, urbana e coletores de pilhas, mas **não tem a
linha plástica** — por isso a faixa não promete "todas as linhas".

**Toda lixeira que aparece na página é uma peça real do catálogo.** O que
continua gerado por IA é o **ambiente** em volta dela: o lobby do hero, o
escritório, o corredor de hotel, a clínica e o condomínio. Essas cenas vieram do
Seedream 5 Pro via Magnific (originais em `magnific/`) desenhando uma lixeira
genérica junto; o `fotos.py` apaga essa lixeira e põe no lugar a peça real,
recortada do fundo branco do estúdio e reacesa com a luz, a sombra e o reflexo
daquela cena. Ambiente ilustrado, produto verdadeiro.

Duas exceções seguem inteiramente geradas: a foto da lâmina de **ESG**, em que a
pessoa interage com a lixeira e trocar a peça exigiria refazer a mão; e o card da
**linha plástica**, porque o acervo é todo de aço inox e não existe foto dessa
linha — pôr inox ali seria prometer polipropileno e mostrar outra coisa. A
fachada (`opt_fachada.webp`) é foto real, reaproveitada do repositório de filtros
e cisternas.

**As peças vêm de `produtos/`**, que guarda só os originais que o `fotos.py` usa,
já reduzidos. O acervo completo do cliente — 337 arquivos — está fora do
repositório, em `~/Projects/NDP/Clients/eco/Produtos Ecobin/`. Para trocar uma
peça, copie o original para `produtos/` com um nome semântico e aponte o `CENAS`
para ele.

Três coisas do `fotos.py` valem saber antes de mexer:

- **O recorte é por preenchimento a partir das bordas**, nunca por limiar de
  luminância, que comeria o corpo branco das lixeiras pintadas e os reflexos do
  inox polido. A tolerância é por peça (`thresh`): nas lixeiras de corpo branco
  encostando em fundo branco ela precisa cair para 12, senão o preenchimento
  vaza para dentro e arranca um pedaço do produto.
- **Apagar a lixeira gerada é interpolação horizontal**, linha a linha, entre o
  que sobrou dos dois lados. Preserva a estratificação da cena — linha do piso,
  laje, horizonte — e perde os detalhes verticais. Por isso as caixas de
  `apagar` cobrem só as faixas que a peça nova não alcança: apagar o objeto
  inteiro levaria junto o piso e o fundo.
- **A sombra é uma elipse esticada com decaimento**, não a silhueta achatada da
  peça: a silhueta de um cilindro vira um retângulo duro no chão. O que assenta
  o objeto é a oclusão logo abaixo dele; sem ela a peça flutua, por mais correta
  que a sombra longa esteja.

**A ordem das cores no hero é a do CONAMA 275** — azul (papel), vermelho
(plástico), verde (vidro), amarelo (metal). Se a foto for trocada, manter as
quatro visíveis: foi pedido explícito. É esse pedido que obriga o hero a ter
**duas artes**, trocadas por `<picture>` em 700px: a foto é `object-fit:cover`, e
quanto mais estreita e alta a tela, menos da largura dela sobra — em 1440px
aparece inteira, num iPhone de 390px sobram 26%. Não existe escala em que as
quatro peças caibam nessa faixa e ainda tenham presença no desktop, então
`hero_bg` (1800x1012) atende o desktop e `hero_bg_mobile` (900x1200), em pé,
atende o celular. Mesma regra vale para os cards: no desktop o `.card-media` só
mostra a faixa central da imagem, e é por isso que a peça principal de cada card
fica entre 30% e 70% da largura, com as de apoio nas beiradas.

**Paleta e tipografia vêm do `ecosolicnpj.com.br`**, lidas das variáveis CSS da
LP de filtros e cisternas: verde `#2FA862`, verde escuro `#1B7440`, verde
profundo `#0E4527`, amarelo `#FFBA2F`, azul-água `#1D6E8F`, tinta `#252525`.
Poppins em todos os pesos.

**A página é deliberadamente light-only** — espelha o site da marca. O
`color-scheme: light` no `:root` evita que campos nativos fiquem escuros quando
o sistema do visitante está em modo escuro.

**O hero repete a receita da LP de filtros**: foto em `position:absolute` sobre
a seção inteira, véu em degradê por cima (`.hero-veil`) e o texto em `z-index:2`.
O véu aqui é mais leve que o da LP irmã, a pedido, para a foto aparecer mais.

---

## Estrutura

Sete lâminas, na ordem do briefing, mais uma acrescentada a pedido:

1. Hero
2. **Ambientes atendidos** — escritório, hotel, clínica e condomínio *(fora do
   briefing; acrescentada para reforçar a conexão com o ambiente corporativo)*
3. Categorias do portfólio — 4 linhas de produto
4. Prova social, ESG e PNRS — carrossel infinito de logomarcas de clientes
5. Foco B2B e condomínios
6. FAQ
7. Fechamento de conversão
8. Rodapé, com a fachada da unidade de Vinhedo

Dados estruturados em JSON-LD no fim do documento: `LocalBusiness` (Ecosoli),
`Organization` (Ecollux), `Service` e `FAQPage` com 8 perguntas.

---

## Pendências

- **Slug final** — o `<link rel="canonical">` aponta para `/lixeiras`, conforme
  o briefing.
- **Perguntas 5 a 8 do FAQ** — as 4 primeiras são do briefing; as outras quatro
  foram escritas a partir do que o próprio briefing afirma (atendimento
  consultivo, faturamento, adesivagem, área de entrega). Não cravam prazo de
  entrega nem quantidade mínima, porque esse dado não existe no material.
  Pedem validação do cliente.
- **Carrossel de clientes** — as logomarcas vieram do carrossel publicado em
  `ecosolicnpj.com.br`. Vale confirmar se a lista segue atual.
- **Foto de ambiente real** — as cenas em volta do produto continuam geradas,
  porque o acervo não tem nenhuma foto de peça instalada em ambiente corporativo
  com qualidade de uso: as poucas que existem são de celular e com marca d'água.
  Se o cliente fotografar instalações, as fotos entram no lugar das cenas em
  `assets/hero_bg*.webp`, `assets/opt_amb_*.webp` e `assets/opt_esg.webp`.
- **Linha plástica fora do catálogo** — o PDF não traz essa linha, e o acervo de
  fotos também não: das 337 imagens, nenhuma é de peça em polipropileno. Por isso
  o card da linha plástica é o único do portfólio que segue com foto gerada. Se o
  cliente mandar as fotos, entram em `produtos/` e viram cena pelo `fotos.py`
  como as outras; se mandar um catálogo que inclua a linha, é só trocar
  `public/catalogo-lixeiras-ecosoli.pdf` pelo arquivo novo (mesmo nome) e
  reajustar o texto da faixa, que hoje enumera as linhas cobertas.
