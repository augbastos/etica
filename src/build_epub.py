"""
Monta a edição EPUB3 reflowável (Kindle/celular) a partir dos fragmentos em
src/parts/, da capa (build/cover.png) e da arte em assets/.
Saída: build/etica-spinoza-2026.epub
Pré-requisito: rode gen_cover.py antes (gera build/cover.png).
"""
import re
import shutil
import zipfile
from pathlib import Path
import book_meta as M
from _gates import run_gates

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
PARTS = SRC / "parts"
ASSETS = ROOT / "assets"
BUILD = ROOT / "build"
STAGE = BUILD / "_epub"
OEBPS = STAGE / "OEBPS"
IMG = OEBPS / "images"
UID = "urn:uuid:9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6e"
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}


def sanitize(fragment: str) -> str:
    """Reescreve caminhos de imagem e devolve XHTML bem-formado."""
    s = fragment.replace("../assets/", "images/")
    try:
        from lxml import html as LH, etree
        doc = LH.fragment_fromstring(f"<div>{s}</div>")
        out = doc.text or ""
        out += "".join(etree.tostring(c, encoding="unicode", method="xml") for c in doc)
        return out
    except Exception:
        s = re.sub(r'<(img|br|hr)((?:[^>]*?))\s*/?>', r'<\1\2/>', s)
        s = re.sub(r'&(?!#?\w+;)', '&amp;', s)
        return s


def xhtml(title: str, body: str) -> str:
    return (f'<?xml version="1.0" encoding="utf-8"?>\n'
            f'<!DOCTYPE html>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" '
            f'lang="{M.LANG}" xml:lang="{M.LANG}">\n'
            f'<head><meta charset="utf-8"/><title>{title}</title>'
            f'<link rel="stylesheet" type="text/css" href="epub.css"/></head>\n'
            f'<body>\n{body}\n</body>\n</html>\n')


def opener(n, title, epi, ref, svg) -> str:
    return (f'<div class="epub-opener">'
            f'<div class="kick">Parte {ROMAN[n]}</div>'
            f'<img src="images/{svg}" alt=""/>'
            f'<p class="epigraph">“{epi}”<span class="ref">{ref}</span></p>'
            f'</div>')


def clean_title(t):
    return t.replace("<br>", " ").replace("  ", " ")


def build():
    # Validation barrier: aborts (SystemExit 1) before staging any EPUB file
    # if a hard gate fails. Override only via SPINOZA_GATES env knobs.
    run_gates()

    if STAGE.exists():
        shutil.rmtree(STAGE)
    (STAGE / "META-INF").mkdir(parents=True)
    IMG.mkdir(parents=True)

    # ---- assets ----
    for svg in ASSETS.glob("*.svg"):
        shutil.copy(svg, IMG / svg.name)
    cover_png = BUILD / "cover.png"
    if cover_png.exists():
        shutil.copy(cover_png, IMG / "cover.png")
    shutil.copy(SRC / "epub.css", OEBPS / "epub.css")

    # ---- documentos de conteúdo ----
    docs = []  # (id, filename, nav_label, in_spine)

    # capa
    cover_body = '<div style="text-align:center;margin:0;padding:0;"><img src="images/cover.png" alt="Capa" style="max-width:100%;height:auto;"/></div>'
    (OEBPS / "cover.xhtml").write_text(xhtml("Capa", cover_body), encoding="utf-8")
    docs.append(("cover", "cover.xhtml", None, True))

    # folha de rosto
    tp = (f'<section class="titlepage">'
          f'<img class="mark" src="images/mark.svg" alt=""/>'
          f'<h1>{M.TITLE}</h1>'
          f'<p class="sub">{M.SUBTITLE}</p>'
          f'<div class="author">{M.AUTHOR}</div>'
          f'<div class="edition">{M.EDITION}</div>'
          f'</section>')
    (OEBPS / "titlepage.xhtml").write_text(xhtml(M.TITLE, tp), encoding="utf-8")
    docs.append(("titlepage", "titlepage.xhtml", "Folha de rosto", True))

    # prefácio
    (OEBPS / "preface.xhtml").write_text(
        xhtml("Prefácio", sanitize((PARTS / "preface.html").read_text(encoding="utf-8"))), encoding="utf-8")
    docs.append(("preface", "preface.xhtml", "Prefácio — Como ler Spinoza hoje", True))

    # partes
    for (n, title, epi, ref, svg) in M.PARTS:
        frag = sanitize((PARTS / f"parte-{n}.html").read_text(encoding="utf-8"))
        body = opener(n, title, epi, ref, svg) + "\n" + frag
        fn = f"part-{n}.xhtml"
        (OEBPS / fn).write_text(xhtml(f"Parte {ROMAN[n]}", body), encoding="utf-8")
        docs.append((f"part{n}", fn, f"Parte {ROMAN[n]} — {clean_title(title)}", True))

    # posfácio + glossário
    (OEBPS / "posface.xhtml").write_text(
        xhtml("Posfácio", sanitize((PARTS / "posface.html").read_text(encoding="utf-8"))), encoding="utf-8")
    docs.append(("posface", "posface.xhtml", "Posfácio — Deus, a Natureza e a Era da IA", True))
    (OEBPS / "glossary.xhtml").write_text(
        xhtml("Glossário", sanitize((PARTS / "glossary.html").read_text(encoding="utf-8"))), encoding="utf-8")
    docs.append(("glossary", "glossary.xhtml", "Glossário", True))

    # ---- nav.xhtml ----
    nav_items = "".join(
        f'<li><a href="{fn}">{lbl}</a></li>' for (_id, fn, lbl, _s) in docs if lbl)
    nav_body = (f'<nav epub:type="toc" id="toc"><h1>Sumário</h1><ol>{nav_items}</ol></nav>'
                f'<nav epub:type="landmarks" hidden="hidden"><ol>'
                f'<li><a epub:type="cover" href="cover.xhtml">Capa</a></li>'
                f'<li><a epub:type="bodymatter" href="part-1.xhtml">Início</a></li>'
                f'</ol></nav>')
    (OEBPS / "nav.xhtml").write_text(xhtml("Sumário", nav_body), encoding="utf-8")

    # ---- toc.ncx (compatibilidade) ----
    navpoints = ""
    for i, (_id, fn, lbl, _s) in enumerate([d for d in docs if d[2]], 1):
        navpoints += (f'<navPoint id="np{i}" playOrder="{i}">'
                      f'<navLabel><text>{lbl}</text></navLabel>'
                      f'<content src="{fn}"/></navPoint>')
    ncx = (f'<?xml version="1.0" encoding="utf-8"?>\n'
           f'<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
           f'<head><meta name="dtb:uid" content="{UID}"/></head>\n'
           f'<docTitle><text>{M.TITLE}</text></docTitle>\n'
           f'<navMap>{navpoints}</navMap></ncx>')
    (OEBPS / "toc.ncx").write_text(ncx, encoding="utf-8")

    # ---- manifest ----
    manifest = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
                '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
                '<item id="css" href="epub.css" media-type="text/css"/>',
                '<item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image"/>']
    for (_id, fn, _l, _s) in docs:
        manifest.append(f'<item id="{_id}" href="{fn}" media-type="application/xhtml+xml"/>')
    for svg in sorted(IMG.glob("*.svg")):
        sid = "img_" + re.sub(r'[^a-zA-Z0-9]', '_', svg.stem)
        manifest.append(f'<item id="{sid}" href="images/{svg.name}" media-type="image/svg+xml"/>')
    spine = "".join(f'<itemref idref="{_id}"/>' for (_id, _f, _l, in_spine) in docs if in_spine)

    opf = (f'<?xml version="1.0" encoding="utf-8"?>\n'
           f'<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">\n'
           f'<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
           f'<dc:identifier id="bookid">{UID}</dc:identifier>\n'
           f'<dc:title>{M.TITLE} — Spinoza para o século XXI</dc:title>\n'
           f'<dc:creator>{M.AUTHOR}</dc:creator>\n'
           f'<dc:language>{M.LANG}</dc:language>\n'
           f'<dc:date>2026-06-18</dc:date>\n'
           f'<dc:publisher>Edição modernizada · 2026</dc:publisher>\n'
           f'<dc:description>Adaptação didática moderna da Ética de Spinoza, fiel ao original de domínio público (tradução Elwes).</dc:description>\n'
           f'<meta name="cover" content="cover-image"/>\n'
           f'<meta property="dcterms:modified">2026-06-18T00:00:00Z</meta>\n'
           f'</metadata>\n'
           f'<manifest>{"".join(manifest)}</manifest>\n'
           f'<spine toc="ncx">{spine}</spine>\n'
           f'</package>')
    (OEBPS / "content.opf").write_text(opf, encoding="utf-8")

    # ---- META-INF/container.xml ----
    (STAGE / "META-INF" / "container.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>\n'
        '</container>', encoding="utf-8")

    # ---- zip ----
    out = BUILD / "etica-spinoza-2026.epub"
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        for p in sorted(STAGE.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(STAGE).as_posix(), compress_type=zipfile.ZIP_DEFLATED)
    print("OK ->", out, f"({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build()
