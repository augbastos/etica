# -*- coding: utf-8 -*-
"""
build_lang.py — montador PARAMETRIZADO por idioma (PT/EN/ES/RU/ZH/JA).

Lê o conteúdo de cada edição e gera PDF (6×9", Paged.js) + EPUB3:
  - PT  : meta de src/book_meta.py, parts de src/parts/
  - outros: meta de i18n/<code>/meta.json, parts de i18n/<code>/parts/

Ordem do livro: prefácio → partes I–V (com aberturas) → posfácio → glossário
→ carta final (closing.html, se existir).

Saída: build/<code>/ethics-<code>.pdf  e  build/<code>/ethics-<code>.epub

NÃO roda os gates do PT (são da fidelidade da adaptação à fonte EN; a fidelidade
das traduções vem do swarm de revisão). CJK (zh/ja) recebe stack de fonte serif.

Uso:
  python build_lang.py pt
  python build_lang.py en --epub-only
  python build_lang.py zh
"""
from __future__ import annotations
import json
import re
import shutil
import sys
import uuid
import zipfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
ASSETS = ROOT / "assets"
BUILD = ROOT / "build"
I18N = ROOT / "i18n"
_UID_BASE = uuid.UUID("9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6e")


def book_uid(code: str) -> str:
    """UUID VÁLIDO e único por idioma (uuid5 determinístico). O mesmo valor
    DEVE ir no OPF (dc:identifier) e no NCX (dtb:uid): o KDP rejeita a conversão
    se NCX != OPF (erro NCX-001), e `urn:uuid:...-en` não é UUID válido (OPF-085)."""
    return f"urn:uuid:{uuid.uuid5(_UID_BASE, code)}"
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
CJK_NUM = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五"}
PART_WORD = {"en": "Part", "es": "Parte", "ru": "Часть", "pt": "Parte"}

# rótulos do aparato/sumário por idioma (fallback EN)
LABELS = {
    "pt": dict(preface="Prefácio", posface="Posfácio", glossary="Glossário", closing="Carta final", titlepage="Folha de rosto", toc="Sumário", cover="Capa"),
    "en": dict(preface="Preface", posface="Afterword", glossary="Glossary", closing="A Closing Letter", titlepage="Title page", toc="Contents", cover="Cover"),
    "es": dict(preface="Prefacio", posface="Epílogo", glossary="Glosario", closing="Carta final", titlepage="Portada", toc="Índice", cover="Portada"),
    "ru": dict(preface="Предисловие", posface="Послесловие", glossary="Глоссарий", closing="Заключительное письмо", titlepage="Титульный лист", toc="Содержание", cover="Обложка"),
    "zh": dict(preface="前言", posface="后记", glossary="术语表", closing="结语", titlepage="扉页", toc="目录", cover="封面"),
    "ja": dict(preface="序文", posface="あとがき", glossary="用語集", closing="結びの言葉", titlepage="扉", toc="目次", cover="表紙"),
}


def parts_dir(code: str) -> Path:
    return (SRC / "parts") if code == "pt" else (I18N / code / "parts")


def labels(code: str) -> dict:
    return LABELS.get(code, LABELS["en"])


def part_kicker(code: str, n: int) -> str:
    if code in ("zh", "ja"):
        return f"第{CJK_NUM[n]}部"
    return f"{PART_WORD.get(code, 'Part')} {ROMAN[n]}"


def font_style(code: str) -> str:
    if code == "zh":
        return ('body,h1,h2,h3,h4,p,.epigraph,.sub{font-family:"Noto Serif SC",'
                '"Source Han Serif SC","Songti SC","SimSun",Georgia,serif !important}')
    if code == "ja":
        return ('body,h1,h2,h3,h4,p,.epigraph,.sub{font-family:"Noto Serif JP",'
                '"Source Han Serif","Yu Mincho","Hiragino Mincho ProN","MS Mincho",Georgia,serif !important}')
    return ""


def load_meta(code: str) -> dict:
    if code == "pt":
        sys.path.insert(0, str(SRC))
        import book_meta as M
        parts = [dict(n=n, title=t, epi=e, ref=r, svg=s) for (n, t, e, r, s) in M.PARTS]
        return dict(TITLE=M.TITLE, SUBTITLE=M.SUBTITLE, AUTHOR=M.AUTHOR,
                    EDITION=M.EDITION, LANG=M.LANG, PARTS=parts)
    j = json.loads((I18N / code / "meta.json").read_text(encoding="utf-8"))
    parts = []
    for p in j.get("parts", []):
        n = int(p["n"])
        parts.append(dict(n=n, title=p.get("title", ""), epi=p.get("epigraph", p.get("epi", "")),
                          ref=p.get("ref", ""), svg=f"part-opener-{n}.svg"))
    return dict(TITLE=j.get("title", "Ethics"), SUBTITLE=j.get("subtitle", ""),
                AUTHOR=j.get("author", "Benedictus de Spinoza"),
                EDITION=j.get("edition", ""), LANG=j.get("lang", code), PARTS=parts)


def frag(code: str, name: str) -> str:
    f = parts_dir(code) / name
    return f.read_text(encoding="utf-8") if f.exists() else ""


def has_closing(code: str) -> bool:
    return (parts_dir(code) / "closing.html").exists()


def cover_png(code: str) -> Path:
    c = BUILD / code / "cover.png"
    return c if c.exists() else (BUILD / "cover.png")


# ----------------------------------------------------------------------------
# PDF (Paged.js)
# ----------------------------------------------------------------------------
def pdf_opener(code, n, title, epi, ref, svg) -> str:
    return f'''
<section class="part-opener">
  <div class="art"><img src="../assets/{svg}" alt="" style="width:100%;height:100%;object-fit:cover;"></div>
  <div class="inner">
    <div class="part-kicker">{part_kicker(code, n)}</div>
    <h1>{title}</h1>
    <hr class="rule-gold">
    <p class="epigraph">“{epi}”</p>
    <p class="epigraph" style="font-size:9pt;letter-spacing:.2em;font-style:normal;margin-top:8mm;color:#c8a868;">{ref.upper()}</p>
  </div>
</section>'''


def build_pdf(code: str, meta: dict) -> Path:
    body = [frag(code, "preface.html")]
    for p in meta["PARTS"]:
        body.append(pdf_opener(code, p["n"], p["title"], p["epi"], p["ref"], p["svg"]))
        body.append(frag(code, f"parte-{p['n']}.html"))
    body.append(frag(code, "posface.html"))
    body.append(frag(code, "glossary.html"))
    if has_closing(code):
        body.append(frag(code, "closing.html"))
    extra = font_style(code)
    extra_tag = f"<style>{extra}</style>" if extra else ""
    html = f'''<!DOCTYPE html>
<html lang="{meta['LANG']}">
<head>
<meta charset="utf-8">
<title>{meta['TITLE']} — Spinoza 2026</title>
<link rel="stylesheet" href="book.css">
{extra_tag}
<script>window.PagedConfig = {{ auto: true, after: () => {{ window.__pagedDone = true; }} }};</script>
<script src="https://unpkg.com/pagedjs/dist/paged.polyfill.js"></script>
</head>
<body>
<section class="titlepage">
  <img class="mark" src="../assets/mark.svg" alt="">
  <h1>{meta['TITLE']}</h1>
  <p class="sub">{meta['SUBTITLE']}</p>
  <div class="author">{meta['AUTHOR']}</div>
  <div class="edition">{meta['EDITION']}</div>
</section>
{"".join(body)}
</body>
</html>'''
    if code != "pt":  # point figure refs at the localized SVGs
        loc = I18N / code / "assets"
        if loc.exists():
            for svg in loc.glob("*.svg"):
                html = html.replace(f"../assets/{svg.name}", f"../i18n/{code}/assets/{svg.name}")
    master = SRC / f"book-{code}.html"
    master.write_text(html, encoding="utf-8")
    outdir = BUILD / code
    outdir.mkdir(parents=True, exist_ok=True)
    pdf_out = outdir / f"ethics-{code}.pdf"
    sys.path.insert(0, str(SRC))
    from render import render
    render(str(master), str(pdf_out))
    return pdf_out


# ----------------------------------------------------------------------------
# EPUB3
# ----------------------------------------------------------------------------
# void elements stay self-closed (valid XHTML); everything else gets an explicit
# close tag, because the Kindle converter parses as lenient HTML and breaks on
# self-closed non-void tags like <span class="tick"/> (e.g. it never closes them).
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}


def expand_self_closing(s: str) -> str:
    def repl(m):
        tag, attrs = m.group(1), m.group(2)
        if tag.lower() in VOID:
            return m.group(0)
        return f"<{tag}{attrs}></{tag}>"
    return re.sub(r'<([a-zA-Z][a-zA-Z0-9]*)((?:\s[^<>]*?)?)\s*/>', repl, s)


def sanitize(fragment: str) -> str:
    s = fragment.replace("../assets/", "images/")
    try:
        from lxml import html as LH, etree
        doc = LH.fragment_fromstring(f"<div>{s}</div>")
        out = doc.text or ""
        out += "".join(etree.tostring(c, encoding="unicode", method="xml") for c in doc)
        return expand_self_closing(out)
    except Exception:
        s = re.sub(r'<(img|br|hr)((?:[^>]*?))\s*/?>', r'<\1\2/>', s)
        s = re.sub(r'&(?!#?\w+;)', '&amp;', s)
        return expand_self_closing(s)


def xhtml(meta, title, body) -> str:
    return (f'<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" '
            f'lang="{meta["LANG"]}" xml:lang="{meta["LANG"]}">\n'
            f'<head><meta charset="utf-8"/><title>{title}</title>'
            f'<link rel="stylesheet" type="text/css" href="epub.css"/></head>\n'
            f'<body>\n{body}\n</body>\n</html>\n')


def epub_opener(code, n, title, epi, ref, svg) -> str:
    return (f'<div class="epub-opener"><div class="kick">{part_kicker(code, n)}</div>'
            f'<img src="images/{svg}" alt=""/>'
            f'<p class="epigraph">“{epi}”<span class="ref">{ref}</span></p></div>')


def build_epub(code: str, meta: dict) -> Path:
    L = labels(code)
    outdir = BUILD / code
    outdir.mkdir(parents=True, exist_ok=True)
    stage = outdir / "_epub"
    if stage.exists():
        shutil.rmtree(stage)
    oebps = stage / "OEBPS"
    img = oebps / "images"
    (stage / "META-INF").mkdir(parents=True)
    img.mkdir(parents=True)

    for svg in ASSETS.glob("*.svg"):
        shutil.copy(svg, img / svg.name)
    loc = I18N / code / "assets"  # localized figures override the PT ones
    if loc.exists():
        for svg in loc.glob("*.svg"):
            shutil.copy(svg, img / svg.name)
    cov = cover_png(code)
    if cov.exists():
        shutil.copy(cov, img / "cover.png")
    css = (SRC / "epub.css").read_text(encoding="utf-8")
    fs = font_style(code)
    if fs:
        css += "\n/* CJK font fallback */\n" + fs.replace(" !important", "")
    (oebps / "epub.css").write_text(css, encoding="utf-8")

    docs = []  # (id, filename, nav_label, in_spine)
    (oebps / "cover.xhtml").write_text(xhtml(meta, L["cover"],
        '<div style="text-align:center;margin:0;padding:0;"><img src="images/cover.png" alt="" style="max-width:100%;height:auto;"/></div>'), encoding="utf-8")
    docs.append(("cover", "cover.xhtml", None, True))

    tp = (f'<section class="titlepage"><img class="mark" src="images/mark.svg" alt=""/>'
          f'<h1>{meta["TITLE"]}</h1><p class="sub">{meta["SUBTITLE"]}</p>'
          f'<div class="author">{meta["AUTHOR"]}</div><div class="edition">{meta["EDITION"]}</div></section>')
    (oebps / "titlepage.xhtml").write_text(xhtml(meta, meta["TITLE"], tp), encoding="utf-8")
    docs.append(("titlepage", "titlepage.xhtml", L["titlepage"], True))

    (oebps / "preface.xhtml").write_text(xhtml(meta, L["preface"], sanitize(frag(code, "preface.html"))), encoding="utf-8")
    docs.append(("preface", "preface.xhtml", L["preface"], True))

    for p in meta["PARTS"]:
        n = p["n"]
        body = epub_opener(code, n, p["title"], p["epi"], p["ref"], p["svg"]) + "\n" + sanitize(frag(code, f"parte-{n}.html"))
        fn = f"part-{n}.xhtml"
        clean_t = p["title"].replace("<br>", " ").replace("  ", " ")
        (oebps / fn).write_text(xhtml(meta, f"{part_kicker(code, n)}", body), encoding="utf-8")
        docs.append((f"part{n}", fn, f"{part_kicker(code, n)} — {clean_t}", True))

    (oebps / "posface.xhtml").write_text(xhtml(meta, L["posface"], sanitize(frag(code, "posface.html"))), encoding="utf-8")
    docs.append(("posface", "posface.xhtml", L["posface"], True))
    (oebps / "glossary.xhtml").write_text(xhtml(meta, L["glossary"], sanitize(frag(code, "glossary.html"))), encoding="utf-8")
    docs.append(("glossary", "glossary.xhtml", L["glossary"], True))
    if has_closing(code):
        (oebps / "closing.xhtml").write_text(xhtml(meta, L["closing"], sanitize(frag(code, "closing.html"))), encoding="utf-8")
        docs.append(("closing", "closing.xhtml", L["closing"], True))

    nav_items = "".join(f'<li><a href="{fn}">{lbl}</a></li>' for (_i, fn, lbl, _s) in docs if lbl)
    nav_body = (f'<nav epub:type="toc" id="toc"><h1>{L["toc"]}</h1><ol>{nav_items}</ol></nav>'
                f'<nav epub:type="landmarks" hidden="hidden"><ol>'
                f'<li><a epub:type="cover" href="cover.xhtml">{L["cover"]}</a></li>'
                f'<li><a epub:type="bodymatter" href="part-1.xhtml">{part_kicker(code, 1)}</a></li></ol></nav>')
    (oebps / "nav.xhtml").write_text(xhtml(meta, L["toc"], nav_body), encoding="utf-8")

    navpoints = ""
    for i, (_id, fn, lbl, _s) in enumerate([d for d in docs if d[2]], 1):
        navpoints += (f'<navPoint id="np{i}" playOrder="{i}"><navLabel><text>{lbl}</text></navLabel>'
                      f'<content src="{fn}"/></navPoint>')
    ncx = (f'<?xml version="1.0" encoding="utf-8"?>\n'
           f'<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
           f'<head><meta name="dtb:uid" content="{book_uid(code)}"/></head>\n'
           f'<docTitle><text>{meta["TITLE"]}</text></docTitle>\n<navMap>{navpoints}</navMap></ncx>')
    (oebps / "toc.ncx").write_text(ncx, encoding="utf-8")

    manifest = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
                '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
                '<item id="css" href="epub.css" media-type="text/css"/>',
                '<item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image"/>']
    for (_id, fn, _l, _s) in docs:
        manifest.append(f'<item id="{_id}" href="{fn}" media-type="application/xhtml+xml"/>')
    for svg in sorted(img.glob("*.svg")):
        sid = "img_" + re.sub(r'[^a-zA-Z0-9]', '_', svg.stem)
        manifest.append(f'<item id="{sid}" href="images/{svg.name}" media-type="image/svg+xml"/>')
    spine = "".join(f'<itemref idref="{_id}"/>' for (_id, _f, _l, ins) in docs if ins)
    opf = (f'<?xml version="1.0" encoding="utf-8"?>\n'
           f'<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">\n'
           f'<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
           f'<dc:identifier id="bookid">{book_uid(code)}</dc:identifier>\n'
           f'<dc:title>{meta["TITLE"]}</dc:title>\n<dc:creator>{meta["AUTHOR"]}</dc:creator>\n'
           f'<dc:language>{meta["LANG"]}</dc:language>\n<dc:date>2026-06-25</dc:date>\n'
           f'<meta name="cover" content="cover-image"/>\n'
           f'<meta property="dcterms:modified">2026-06-25T00:00:00Z</meta>\n</metadata>\n'
           f'<manifest>{"".join(manifest)}</manifest>\n<spine toc="ncx">{spine}</spine>\n</package>')
    (oebps / "content.opf").write_text(opf, encoding="utf-8")
    (stage / "META-INF" / "container.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>\n'
        '</container>', encoding="utf-8")

    out = outdir / f"ethics-{code}.epub"
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        for p in sorted(stage.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(stage).as_posix(), compress_type=zipfile.ZIP_DEFLATED)
    shutil.rmtree(stage)
    print("OK EPUB ->", out, f"({out.stat().st_size // 1024} KB)")
    return out


def main():
    if len(sys.argv) < 2:
        print("uso: python build_lang.py <pt|en|es|ru|zh|ja> [--epub-only|--pdf-only]")
        sys.exit(1)
    code = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else ""
    meta = load_meta(code)
    print(f"== build [{code}] :: {meta['TITLE']} ==  parts_dir={parts_dir(code)}  closing={has_closing(code)}")
    if mode != "--pdf-only":
        build_epub(code, meta)
    if mode != "--epub-only":
        build_pdf(code, meta)


if __name__ == "__main__":
    main()
