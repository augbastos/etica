# -*- coding: utf-8 -*-
"""
make_kdp_guides.py — gera um guia de publicacao no KDP por idioma.

Cada guia (em PT, que e o que o Augusto le) traz os VALORES exatos dos campos do
KDP NA LINGUA do livro + arquivos a subir + respostas do form de IA + preco/royalty.
Saida: build/<code>/PUBLICAR-NO-KDP.md  (um por idioma).
"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"

PT_META = {
    "title": "Ética",
    "subtitle": "Spinoza para o século XXI — uma leitura moderna da obra que dissolveu a fronteira entre Deus e a Natureza",
    "author": "Benedictus de Spinoza",
}

CFG = {
    "en": dict(nome="Inglês", kdp_lang="English", market="Amazon.com",
               lang_note="",
               desc="A modern, faithful reading of Spinoza's Ethics — the work that dissolved the boundary between God and Nature. This designed edition sets Spinoza's own propositions and demonstrations apart, with their exact references, and surrounds them with clear explanation that never betrays the argument. A geometry of the soul, rebuilt for the 21st-century reader.",
               keywords=["Spinoza", "Ethics", "philosophy", "pantheism", "rationalism", "metaphysics", "modern philosophy classic"],
               cats=["Philosophy > Ethics & Moral Philosophy", "Philosophy > History & Surveys > Modern", "Religion & Spirituality > Philosophy"]),
    "pt": dict(nome="Português", kdp_lang="Portuguese", market="Amazon.com.br",
               lang_note="",
               desc="Uma leitura moderna e fiel da Ética de Spinoza — a obra que dissolveu a fronteira entre Deus e a Natureza. Esta edição, cuidadosamente desenhada, destaca as proposições e demonstrações do próprio Spinoza, com suas referências exatas, e as cerca de uma explicação clara que torna o argumento respirável sem traí-lo. Uma geometria da alma, reconstruída para o leitor do século XXI.",
               keywords=["Spinoza", "Ética", "filosofia", "panteísmo", "racionalismo", "metafísica", "clássico da filosofia"],
               cats=["Filosofia > Ética e Moral", "Filosofia > História e Pesquisas", "Religião e Espiritualidade > Filosofia"]),
    "es": dict(nome="Espanhol", kdp_lang="Spanish", market="Amazon.es (Espanha — maior público pagante em espanhol; nos *territórios* deixe **All**, assim vende também em .com.mx, .com.es e .com)",
               lang_note="",
               desc="Una lectura moderna y fiel de la Ética de Spinoza — la obra que disolvió la frontera entre Dios y la Naturaleza. Esta edición, cuidadosamente diseñada, destaca las proposiciones y demostraciones del propio Spinoza, con sus referencias exactas, y las rodea de una explicación clara que hace el argumento respirable sin traicionarlo. Una geometría del alma, reconstruida para el lector del siglo XXI.",
               keywords=["Spinoza", "Ética", "filosofía", "panteísmo", "racionalismo", "metafísica", "clásico de filosofía"],
               cats=["Filosofía > Ética y Moral", "Filosofía > Historia y Estudios", "Religión y Espiritualidad > Filosofía"]),
    "ru": dict(nome="Russo", kdp_lang="Russian", market="Amazon.com (não há loja Amazon na Rússia)",
               lang_note="O russo pode estar na lista de **idiomas com suporte limitado** do KDP. Se não aparecer no dropdown, selecione o mais próximo disponível e publique — o conteúdo é imagem (fixed-layout), então renderiza igual.",
               desc="Современное и точное прочтение «Этики» Спинозы — труда, растворившего границу между Богом и Природой. В этом тщательно оформленном издании собственные теоремы и доказательства Спинозы выделены, с точными ссылками, и окружены ясным объяснением, которое делает аргумент живым, не предавая его. Геометрия души, заново выстроенная для читателя XXI века.",
               keywords=["Спиноза", "Этика", "философия", "пантеизм", "рационализм", "метафизика", "классика философии"],
               cats=["Philosophy > Ethics & Moral Philosophy", "Philosophy > History & Surveys", "Religion & Spirituality > Philosophy"]),
    "zh": dict(nome="Chinês (simplificado)", kdp_lang="Chinese (Traditional)", market="Amazon.com (não há loja KDP na China)",
               lang_note="O texto é **chinês simplificado**, mas o KDP costuma listar só **Chinese (Traditional)**. Selecione essa opção — como é fixed-layout (imagem), o texto renderiza exatamente como desenhado, independente do rótulo do idioma.",
               desc="对斯宾诺莎《伦理学》的一次忠实而现代的重读——这部消弭了神与自然之界限的巨著。本精心设计的版本将斯宾诺莎本人的命题与证明单独呈现，并附以精确的出处，再以清晰的阐释环绕，使论证可呼吸而不失其真。一部为二十一世纪读者重建的灵魂几何学。",
               keywords=["斯宾诺莎", "伦理学", "哲学", "泛神论", "理性主义", "形而上学", "哲学经典"],
               cats=["Philosophy > Ethics & Moral Philosophy", "Philosophy > History & Surveys", "Religion & Spirituality > Philosophy"]),
    "ja": dict(nome="Japonês", kdp_lang="Japanese", market="Amazon.co.jp",
               lang_note="",
               desc="スピノザ『エチカ』——神と自然のあいだの境界を溶かした著作——の、忠実かつ現代的な読解。本書は丁寧に設計された版で、スピノザ自身の命題と証明を、正確な典拠とともに際立たせ、その周囲を、論証を裏切ることなく息づかせる明晰な解説で囲む。二十一世紀の読者のために再構築された、魂の幾何学。",
               keywords=["スピノザ", "エチカ", "哲学", "汎神論", "合理主義", "形而上学", "哲学の古典"],
               cats=["Philosophy > Ethics & Moral Philosophy", "Philosophy > History & Surveys", "Religion & Spirituality > Philosophy"]),
}


# Preço-âncora POR MERCADO (moeda e faixa de 70% específicas de cada loja KDP).
# Posicionamento premium: topo da faixa de 70% (edição curada, não compete com
# os textos grátis de domínio público).
PRICES = {
    "en": "**US$ 9,99**  ·  faixa 70%: US$ 2,99–9,99  ·  loja: Amazon.com",
    "pt": "**R$ 24,90 @ 70%**  ·  loja: Amazon.com.br  ·  faixa 70% BR = **R$ 5,99–R$ 24,99** (acima vira 35%; por isso NÃO converter $9,99 pelo câmbio — ~R$ 50 cairia pra 35%)  ·  ⚠️ **no Brasil o 70% EXIGE marcar KDP Select** (sem ele, 35% mesmo no preço certo)",
    "es": "**€ 9,99 @ 70%**  ·  faixa 70%: € 2,69–9,99  ·  loja: Amazon.es  ·  (Espanha = UE → 70% SEM precisar de KDP Select)",
    "ja": "**¥ 1.200 @ 70%**  ·  faixa 70%: ¥ 250–1.250  ·  loja: Amazon.co.jp  ·  ⚠️ **no Japão o 70% EXIGE marcar KDP Select** (igual Brasil/México/Índia)",
    "ru": "**US$ 9,99**  ·  faixa 70%: US$ 2,99–9,99  ·  loja: Amazon.com (sem loja russa)",
    "zh": "**US$ 9,99**  ·  faixa 70%: US$ 2,99–9,99  ·  loja: Amazon.com (sem loja na China)",
}


# Descrição em HTML aceito pelo KDP (subset: <h4>-<h6>,<p>,<b>,<i>,<u>,<ul>/<ol>/<li>,<br>).
# Mesma master (a versão EN); traduzida por idioma; mesma estrutura: gancho (h4) + corpo (p) + bordão (b).
# Título da obra em itálico só nos scripts latinos (en/pt/es); ru/zh/ja já têm aspas próprias da língua.
DESC_HTML = {
    "en": """<h4>A modern, faithful reading of Spinoza's <i>Ethics</i> — the work that dissolved the boundary between God and Nature.</h4>
<p>This designed edition sets Spinoza's own propositions and demonstrations apart, with their exact references, and surrounds them with clear explanation that never betrays the argument.</p>
<p><b>A geometry of the soul, rebuilt for the 21st-century reader.</b></p>""",
    "pt": """<h4>Uma leitura moderna e fiel da <i>Ética</i> de Spinoza — a obra que dissolveu a fronteira entre Deus e a Natureza.</h4>
<p>Esta edição, cuidadosamente desenhada, destaca as proposições e demonstrações do próprio Spinoza, com suas referências exatas, e as cerca de uma explicação clara que torna o argumento respirável sem traí-lo.</p>
<p><b>Uma geometria da alma, reconstruída para o leitor do século XXI.</b></p>""",
    "es": """<h4>Una lectura moderna y fiel de la <i>Ética</i> de Spinoza — la obra que disolvió la frontera entre Dios y la Naturaleza.</h4>
<p>Esta edición, cuidadosamente diseñada, destaca las proposiciones y demostraciones del propio Spinoza, con sus referencias exactas, y las rodea de una explicación clara que hace el argumento respirable sin traicionarlo.</p>
<p><b>Una geometría del alma, reconstruida para el lector del siglo XXI.</b></p>""",
    "ru": """<h4>Современное и точное прочтение «Этики» Спинозы — труда, растворившего границу между Богом и Природой.</h4>
<p>В этом тщательно оформленном издании собственные теоремы и доказательства Спинозы выделены, с точными ссылками, и окружены ясным объяснением, которое делает аргумент живым, не предавая его.</p>
<p><b>Геометрия души, заново выстроенная для читателя XXI века.</b></p>""",
    "zh": """<h4>对斯宾诺莎《伦理学》的一次忠实而现代的重读——这部消弭了神与自然之界限的巨著。</h4>
<p>本精心设计的版本将斯宾诺莎本人的命题与证明单独呈现，并附以精确的出处，再以清晰的阐释环绕，使论证可呼吸而不失其真。</p>
<p><b>一部为二十一世纪读者重建的灵魂几何学。</b></p>""",
    "ja": """<h4>スピノザ『エチカ』——神と自然のあいだの境界を溶かした著作——の、忠実かつ現代的な読解。</h4>
<p>本書は丁寧に設計された版で、スピノザ自身の命題と証明を、正確な典拠とともに際立たせ、その周囲を、論証を裏切ることなく息づかせる明晰な解説で囲む。</p>
<p><b>二十一世紀の読者のために再構築された、魂の幾何学。</b></p>""",
}


# Categorias REAIS por marketplace primário (o seletor do KDP vem na língua da loja
# primária e tem CAMPO DE BUSCA). Árvore atual: topo "Não ficção/Nonfiction" → Filosofia.
# ru/zh têm marketplace primário .com → usam o seletor EM INGLÊS (iguais ao en).
# 3 escolhas p/ o livro: Metafísica (núcleo Deus/Natureza) + Ética e Moral + História/Moderna.
# NOMES REAIS verificados via breadcrumb das lojas (jun/2026). Caminho = departamento da
# loja → Filosofia → folha. ATENÇÃO: NÃO existe "Não ficção" como topo; cada loja tem o seu.
CATS = {
    # .com (inglês) — usado por en/ru/zh. Topo: Kindle eBooks › Politics & Social Sciences › Philosophy
    "en": ["Politics & Social Sciences › Philosophy › Metaphysics",
           "Politics & Social Sciences › Philosophy › Ethics & Morality",
           "Politics & Social Sciences › Philosophy › Modern  (alt: History & Surveys / Movements)"],
    "ru": ["Politics & Social Sciences › Philosophy › Metaphysics",
           "Politics & Social Sciences › Philosophy › Ethics & Morality",
           "Politics & Social Sciences › Philosophy › Modern  (alt: History & Surveys / Movements)"],
    "zh": ["Politics & Social Sciences › Philosophy › Metaphysics",
           "Politics & Social Sciences › Philosophy › Ethics & Morality",
           "Politics & Social Sciences › Philosophy › Modern  (alt: History & Surveys / Movements)"],
    # .com.br — topo: Sociedade e Ciências Sociais › Filosofia (folhas verificadas)
    "pt": ["Sociedade e Ciências Sociais › Filosofia › Metafísica",
           "Sociedade e Ciências Sociais › Filosofia › Ética e Moralidade",
           "Sociedade e Ciências Sociais › Filosofia › Movimentos  (alt: Religioso / Consciência e Pensamento)"],
    # .es — topo: Filosofía (folhas verificadas: Conciencia y pensamiento, Crítica…)
    "es": ["Filosofía › Metafísica",
           "Filosofía › Ética y moral",
           "Filosofía › Movimientos  (alt: Crítica / Conciencia y pensamiento)"],
    # .co.jp — topo: 人文・思想 › 哲学・思想 (folhas verificadas)
    "ja": ["人文・思想 › 哲学・思想 › 形而上学・存在論",
           "人文・思想 › 哲学・思想 › 倫理学",
           "人文・思想 › 哲学・思想 › 近代西洋哲学"],
}
CAT_NOTE = ("O seletor do KDP **não é texto livre**: abre uma árvore na língua da loja primária. "
            "Use o **campo de busca** dele com as palavras abaixo. Se algum nome exato divergir, "
            "pegue a folha **mais próxima** dentro de Filosofia. Máx. **3**.")
CAT_SEARCH = {"en": "Philosophy / Metaphysics / Ethics", "ru": "Philosophy / Metaphysics / Ethics",
              "zh": "Philosophy / Metaphysics / Ethics", "pt": "Filosofia / Metafísica / Ética",
              "es": "Filosofía / Metafísica / Ética", "ja": "哲学 / 倫理学 / 形而上学"}

# Lojas onde 70% EXIGE KDP Select (Brasil, Japão, México, Índia). Nas demais é opcional.
SELECT_REQ = {"pt", "ja"}

# PREÇO POR MARKETPLACE = topo da faixa de 70% de cada loja (premium + 70% garantido).
# NÃO usar a conversão automática do KDP: a partir de um preço-base ela ou barateia
# (base BRL) ou estoura o teto de lojas com teto baixo (CA/JP/IN) e cai pra 35%.
INTL_PRICE_TABLE = """\
| Loja | Preço (digite manualmente) | Faixa 70% |
|---|---|---|
| Amazon**.com** (EUA) | **US$ 9,99** | $2,99–9,99 |
| Amazon**.co.uk** | **£ 8,99** | £1,77–9,99 |
| Amazon **.de / .fr / .es / .it / .nl** | **€ 9,99** | €2,69–9,99 |
| Amazon**.ca** | **C$ 9,99** | C$2,99–9,99 |
| Amazon**.com.au** | **A$ 11,99** | A$3,99–11,99 |
| Amazon**.co.jp** | **¥ 1.250** | ¥250–1.250 |
| Amazon**.com.br** | **R$ 24,90** | R$5,99–24,99 |
| Amazon**.in** | **₹ 449** | ₹99–449 |
| Amazon**.com.mx** | **MX$ 149** | MX$34,99–149,99 |
"""


def meta(code):
    if code == "pt":
        return PT_META
    m = json.load(open(ROOT / "i18n" / code / "meta.json", encoding="utf-8"))
    return {"title": m["title"], "subtitle": m["subtitle"], "author": m["author"]}


def guide(code):
    c = CFG[code]
    m = meta(code)
    price = PRICES[code]
    desc_html = DESC_HTML[code]
    select_line = (
        "**KDP Select:** ⚠️ **OBRIGATÓRIO nesta loja para ter 70%** (sem ele cai pra 35%). "
        "Implica 90 dias de exclusividade do eBook + entra no Kindle Unlimited. Como você não vende em outro lugar, sem problema."
        if code in SELECT_REQ else
        "**KDP Select:** opcional. Marcar = 90 dias de exclusividade + Kindle Unlimited (mais alcance). Sem vender em outro lugar → vale marcar."
    )
    intl_table = "\n".join("> " + ln for ln in INTL_PRICE_TABLE.strip().split("\n"))
    folder = f"build/{code}"
    kw = "; ".join(c["keywords"])
    cats = "\n".join(f"   {i+1}. {x}" for i, x in enumerate(CATS[code]))
    lang_note = f"\n> ⚠️ **Nota de idioma:** {c['lang_note']}\n" if c["lang_note"] else ""
    return f"""# Publicar no KDP — edição {c['nome']} ({code})

> Cada idioma é um **livro separado** no KDP (ASIN próprio). Crie um novo
> *Kindle eBook* (“+ Create” → Kindle eBook) e preencha com os valores abaixo.

## 📁 Arquivos desta edição
Pasta: `{folder}`
- **Manuscrito (subir):** `ethics-{code}-kindle-fxl.epub`  ← fixed-layout, design completo, epubcheck 0/0
- **Capa (campo separado):** `cover.jpg`  (1600×2560)

---

## 1) Aba “Kindle eBook Details”
{lang_note}
| Campo | Valor |
|---|---|
| **Language** | {c['kdp_lang']} |
| **Book Title** | `{m['title']}` |
| **Subtitle** | `{m['subtitle']}` |
| **Primary Author** | `{m['author']}` |
| **Contributor** (opcional) | papel **Editor/Translator** → seu pseudônimo ou selo editorial (não o nome real, mantém a separação) |
| **Description** | (cole o texto abaixo) |
| **Publishing Rights** | ✅ “I own the copyright…” (é adaptação/tradução ORIGINAL sua sobre fonte em domínio público) |
| **Keywords (7)** | {kw} |
| **Categories (3)** | {CAT_NOTE}<br>Buscar por: **{CAT_SEARCH[code]}** |
{cats}
| **Primary marketplace** | {c['market']} |

**Description — cole EXATAMENTE este HTML no campo Description** (o KDP renderiza estas tags; cole o código, não o texto formatado):
```html
{desc_html}
```

*Prévia de como vai aparecer:* gancho em destaque + parágrafo + bordão em negrito.

---

## 2) Aba “Content”
1. **Upload eBook manuscript** → `ethics-{code}-kindle-fxl.epub`
2. **Upload cover** → `cover.jpg`
3. **Form de conteúdo de IA** (obrigatório):

| Pergunta | Resposta | Ferramenta |
|---|---|---|
| Texto criado com IA? | **Sim (AI-generated)** | Claude (Anthropic) |
| Tradução criada com IA? | **Sim (AI-generated)** | Claude (Anthropic) |
| Imagens criadas com IA? | **Não** | — (arte vetorial por código, não gerador de imagem) |

   - Texto: *“Adapted/translated from the public-domain source using Claude (Anthropic); human-edited.”*
4. **Preview** → confira que as páginas e figuras aparecem. Publica só depois disso.

---

## 3) Aba “Pricing”
- {select_line}
- **Território primário (Primary marketplace):** {c['market']}.
- **Territórios:** **All territories (worldwide rights)**.
- **Preço (posicionamento premium) desta edição:** {price}.
  - Topo da faixa de **70%** sinaliza edição séria/curada. Se quer “art-book/coleção” e não liga pro royalty, pode subir acima da faixa (cai pra 35%).
- **Royalty:** **70%** (rende mais que o 35% dentro da faixa elegível, mesmo com a taxa de entrega do arquivo).

> ⚠️ **PARIDADE DE PREÇO ENTRE LOJAS (importante):** **DESMARQUE** a conversão automática ("definir preços das outras lojas com base em…"). Se deixar marcado, o KDP converte do preço-base e o livro fica **barato** lá fora (ou cai pra 35% em CA/JP/IN, que têm teto baixo). Em vez disso, ponha **cada loja no topo da sua faixa de 70%**:
>
{intl_table}
> Confira que **cada linha mostra 70%**; se mostrar 35%, está acima do teto daquela loja → use o valor da tabela.

- **Publish.** Até 72h pra ir ao ar.

---

*Identidade visual 100% preservada (fixed-layout = páginas do PDF desenhado). Gerado por `src/build_fxl_epub.py`.*
"""


def main():
    for code in CFG:
        out = BUILD / code / "PUBLICAR-NO-KDP.md"
        out.write_text(guide(code), encoding="utf-8")
        print("OK ->", out)


if __name__ == "__main__":
    main()
