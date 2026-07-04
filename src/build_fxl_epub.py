# -*- coding: utf-8 -*-
"""
build_fxl_epub.py — EPUB FIXED-LAYOUT (pre-paginado) a partir do PDF do livro.

Preserva a IDENTIDADE VISUAL COMPLETA no Kindle: cada pagina do PDF (design Paged.js,
geometria sagrada, selos, dropcaps, tipografia) e rasterizada em alta-res e embutida
numa pagina pre-paginada. O conversor KFX da Amazon aceita bem (e so imagem), ao
contrario do EPUB reflowable que ele recusava.

  python build_fxl_epub.py en   -> build/en/ethics-en-kindle-fxl.epub

Trade-off inerente do fixed-layout: o texto vira imagem (nao reflui/seleciona). Melhor
em tablet/app Kindle. E o jeito padrao de publicar livro ilustrado/arte no Kindle.

Requisitos: PyMuPDF (fitz), Pillow.
"""
import io
import re
import sys
import uuid
import zipfile
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image
from lxml import etree
from lxml import html as lhtml

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
TARGET_W = 1600   # largura alvo em px (≈266 DPI numa pagina 6")
JPG_Q = 86


def _norm(s):
    # Unicode-aware: mantem letras/digitos de QUALQUER escrita (cirilico, CJK, latino)
    s = re.sub(r"\s+", " ", s.lower())
    return "".join(ch for ch in s if ch.isalnum() or ch == " ").strip()


def section_titles(code):
    """Titulos de nivel 1 (h1/h2) lidos do EPUB base — p/ montar o nav navegavel."""
    epub = BUILD / code / f"ethics-{code}.epub"
    if not epub.exists():
        return []
    z = zipfile.ZipFile(epub)
    cont = etree.fromstring(z.read("META-INF/container.xml"))
    opf_path = cont.find(".//{*}rootfile").get("full-path")
    base = opf_path.rsplit("/", 1)[0] if "/" in opf_path else ""
    opf = etree.fromstring(z.read(opf_path))
    man = {it.get("id"): it.get("href") for it in opf.findall(".//{*}item")}
    spine = [man[ir.get("idref")] for ir in opf.findall(".//{*}itemref")]
    out = []
    for href in spine:
        if any(k in href for k in ("cover", "nav", "titlepage")):
            continue
        full = (base + "/" + href) if base else href
        root = lhtml.fromstring(z.read(full))
        for h in root.xpath(".//h1 | .//h2"):
            t = re.sub(r"^\s*\d+\.\s*", "", re.sub(r"\s+", " ", "".join(h.itertext())).strip())
            if t:
                out.append(t)
    return out


def render_pages(pdf_path, cover_path):
    """Retorna (paginas, page_texts). paginas = [(nome, jpeg, (w,h))], capa primeiro."""
    out = []
    texts = [""]  # idx 0 = capa (sem texto)
    if cover_path.exists():
        cov = Image.open(cover_path).convert("RGB")
        buf = io.BytesIO()
        cov.save(buf, "JPEG", quality=90, optimize=True)
        out.append(("cover.jpg", buf.getvalue(), cov.size))

    doc = fitz.open(pdf_path)
    for i, page in enumerate(doc, 1):
        zoom = TARGET_W / page.rect.width
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=JPG_Q, optimize=True)
        out.append((f"page-{i:03d}.jpg", buf.getvalue(), im.size))
        texts.append(_norm(page.get_text()))
    doc.close()
    return out, texts


def build_nav(code, titles, texts):
    """Mapeia cada titulo -> 1a pagina cujo texto o contem; retorna (xhtml, [(titulo,idx)])."""
    items = []
    used = 0
    for t in titles:
        key = _norm(t)[:24]
        if not key:
            continue
        for idx in range(used + 1, len(texts)):
            if key and key in texts[idx]:
                items.append((t, idx))
                used = idx
                break
    if not items:
        items = [("Start", 1)]
    li = "".join(f'<li><a href="../text/pg{idx}.xhtml">{t}</a></li>' for t, idx in items)
    nav = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE html>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops">\n'
        '<head><meta charset="utf-8"/><title>Contents</title></head>\n'
        f'<body><nav epub:type="toc" id="toc"><h1>Contents</h1><ol>{li}</ol></nav></body>\n'
        '</html>'
    )
    return nav, items


def page_xhtml(img_name, w, h, title):
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE html>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml">\n'
        f'<head><meta charset="utf-8"/><title>{title}</title>'
        f'<meta name="viewport" content="width={w}, height={h}"/>'
        '<style>html,body{margin:0;padding:0}'
        f'img{{width:{w}px;height:{h}px;display:block}}</style></head>\n'
        f'<body><img src="../images/{img_name}" alt=""/></body>\n</html>'
    )


def build(code):
    pdf = BUILD / code / f"ethics-{code}.pdf"
    cover = BUILD / code / "cover.png"
    if not pdf.exists():
        print("nao achei", pdf)
        sys.exit(1)
    pages, texts = render_pages(pdf, cover)
    cw, ch = pages[0][2]  # resolucao da capa p/ original-resolution
    nav_xhtml, nav_items = build_nav(code, section_titles(code), texts)
    print(f"== fxl [{code}] :: {len(pages)} paginas (capa+PDF) | "
          f"{len(nav_items)} entradas no sumario ==")

    # manifest + spine
    man, spine = [], []
    man.append('<item id="cover-image" href="images/cover.jpg" '
               'media-type="image/jpeg" properties="cover-image"/>')
    man.append('<item id="nav" href="text/nav.xhtml" '
               'media-type="application/xhtml+xml" properties="nav"/>')
    for idx, (name, _data, _wh) in enumerate(pages):
        pid = f"pg{idx}"
        iid = f"img{idx}"
        man.append(f'<item id="{pid}" href="text/{pid}.xhtml" '
                   f'media-type="application/xhtml+xml"/>')
        if name != "cover.jpg":  # capa ja esta no manifest como cover-image
            man.append(f'<item id="{iid}" href="images/{name}" media-type="image/jpeg"/>')
        spine.append(f'<itemref idref="{pid}"/>')

    opf = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" '
        'unique-identifier="bookid" prefix="rendition: http://www.idpf.org/vocab/rendition/#">\n'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        f'<dc:identifier id="bookid">urn:uuid:'
        f'{uuid.uuid5(uuid.NAMESPACE_DNS, "etica-fxl-" + code)}</dc:identifier>\n'
        '<dc:title>Ethics</dc:title>\n'
        '<dc:creator>Benedictus de Spinoza</dc:creator>\n'
        f'<dc:language>{code}</dc:language>\n'
        '<meta property="dcterms:modified">2026-06-25T00:00:00Z</meta>\n'
        '<meta name="cover" content="cover-image"/>\n'
        # EPUB3 rendition (fixed layout)
        '<meta property="rendition:layout">pre-paginated</meta>\n'
        '<meta property="rendition:orientation">portrait</meta>\n'
        '<meta property="rendition:spread">none</meta>\n'
        # legado Amazon (Kindle Publishing Guidelines)
        '<meta name="fixed-layout" content="true"/>\n'
        '<meta name="orientation-lock" content="portrait"/>\n'
        f'<meta name="original-resolution" content="{cw}x{ch}"/>\n'
        '</metadata>\n'
        '<manifest>' + "".join(man) + '</manifest>\n'
        '<spine>' + "".join(spine) + '</spine>\n'
        '</package>'
    )

    container = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<container version="1.0" '
        'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" '
        'media-type="application/oebps-package+xml"/></rootfiles>\n</container>'
    )

    out = BUILD / code / f"ethics-{code}-kindle-fxl.epub"
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", container, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", opf, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/text/nav.xhtml", nav_xhtml, compress_type=zipfile.ZIP_DEFLATED)
        for idx, (name, data, (w, h)) in enumerate(pages):
            img_target = "cover.jpg" if name == "cover.jpg" else name
            z.writestr(f"OEBPS/images/{img_target}", data, compress_type=zipfile.ZIP_STORED)
            ttl = "Cover" if idx == 0 else f"Page {idx}"
            z.writestr(f"OEBPS/text/pg{idx}.xhtml", page_xhtml(img_target, w, h, ttl),
                       compress_type=zipfile.ZIP_DEFLATED)

    print("OK FXL ->", out, f"({out.stat().st_size // 1024} KB, {len(pages)} paginas)")
    return out


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "en")
