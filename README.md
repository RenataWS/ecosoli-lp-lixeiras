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

A única exceção é **`public/og-lixeiras.jpg`**, a imagem que aparece quando
alguém compartilha o link. Ela precisa ser arquivo de verdade: WhatsApp,
Facebook e LinkedIn só leem `og:image` com URL absoluta e ignoram data URI. O
`deploy.yml` sobe o conteúdo de `public/` ao lado do `index.html`, então a
imagem responde em `…/lixeiras/og-lixeiras.jpg`. Mudar o nome do arquivo ou o
diretório de destino quebra o preview — e as redes cacheiam o resultado, então
o estrago não se corrige sozinho.

Para publicar no HostGator, basta colocar o `index.html` e a imagem de
compartilhamento na pasta do subdiretório correspondente.

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
apontariam para o catálogo. Não há formulário e não há link que tire o visitante
da página. O número fica na constante `WA`, e é o mesmo publicado na LP de
filtros e cisternas: `5519920033125`.

**As fotos são geradas por IA** (Seedream 5 Pro, via Magnific) e são
ilustrativas: os modelos que aparecem nelas não são itens do catálogo. Foram
dirigidas pela exigência do briefing — sempre lixeira de inox, com a
identificação de cores da reciclagem, dentro de ambiente corporativo
(escritório, hotel, clínica, prédio). As gerações originais estão em
`magnific/`. **A única foto real é a da fachada** (`opt_fachada.webp`),
reaproveitada do repositório de filtros e cisternas.

**A ordem das cores no hero é a do CONAMA 275** — azul (papel), vermelho
(plástico), verde (vidro), amarelo (metal). Se a foto for trocada, manter as
quatro visíveis: foi pedido explícito.

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
- **Foto de produto real** — os cards de portfólio usam imagem gerada. Quando o
  cliente enviar fotos do catálogo, substituir em `assets/opt_p_*.webp`, que é
  onde a exatidão importa.
