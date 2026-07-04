# -*- coding: utf-8 -*-
"""
epub_kindle.py — converte um EPUB do livro numa versao KINDLE-SAFE.

O conversor da Amazon (KDP) falha em <img src="*.svg"> ("couldn't convert your
HTML file to Kindle format"), mesmo com EPUB valido. Fix: rasterizar todos os
SVG -> PNG (Chromium/Playwright, 3x, fundo transparente) e reescrever as refs
nos XHTML + o manifesto do content.opf. Reusavel pras 6 linguas.

  python epub_kindle.py en      -> build/en/ethics-en-kindle.epub

Requisitos: playwright (chromium), lxml.
"""
import sys, shutil, zipfile, re
from pathlib import Path
from lxml import etree

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
SCALE = 3  # densidade de rasterizacao


def svg_size(path: Path):
    r = etree.parse(str(path)).getroot()
    w, h = r.get("width"), r.get("height")
    if w and h:
        try:
            return int(float(re.sub(r"[^0-9.]", "", w))), int(float(re.sub(r"[^0-9.]", "", h)))
        except Exception:
            pass
    vb = r.get("viewBox")
    if vb:
        p = vb.replace(",", " ").split()
        if len(p) == 4:
            return int(float(p[2])), int(float(p[3]))
    return 600, 400


def rasterize(svgs, outdir):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for svg in svgs:
            w, h = svg_size(svg)
            # inline o SVG (img src=file:// e bloqueado dentro de set_content)
            markup = re.sub(r"<\?xml[^>]*\?>", "", svg.read_text(encoding="utf-8")).strip()
            # viewport no tamanho natural + DSF -> evita "Unable to capture screenshot"
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=SCALE)
            html = (f'<!DOCTYPE html><html><head><meta charset="utf-8">'
                    f'<style>html,body{{margin:0;padding:0;background:transparent}}'
                    f'svg{{display:block;width:{w}px;height:{h}px}}</style></head>'
                    f'<body>{markup}</body></html>')
            pg.set_content(html, wait_until="networkidle")
            pg.wait_for_timeout(200)
            png = outdir / (svg.stem + ".png")
            pg.screenshot(path=str(png), omit_background=True, clip={"x": 0, "y": 0, "width": w, "height": h})
            pg.close()
            print("  raster", svg.name, f"-> {png.name} ({w * SCALE}x{h * SCALE})")
        b.close()


def convert(code: str):
    src = BUILD / code / f"ethics-{code}.epub"
    if not src.exists():
        print("nao achei", src); sys.exit(1)
    stage = BUILD / code / "_kindle"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    with zipfile.ZipFile(src) as z:
        z.extractall(stage)
    img = stage / "OEBPS" / "images"
    svgs = sorted(img.glob("*.svg"))
    print(f"== kindle [{code}] :: {len(svgs)} svg -> png ==")
    rasterize(svgs, img)

    # mapa nome.svg -> nome.png + remove os svg
    names = {s.name: s.stem + ".png" for s in svgs}
    for s in svgs:
        s.unlink()

    # reescreve refs nos xhtml
    for xh in (stage / "OEBPS").glob("*.xhtml"):
        t = xh.read_text(encoding="utf-8")
        for svg_name, png_name in names.items():
            t = t.replace(f"images/{svg_name}", f"images/{png_name}")
        xh.write_text(t, encoding="utf-8")

    # reescreve o manifesto do content.opf (href + media-type)
    opf = stage / "OEBPS" / "content.opf"
    o = opf.read_text(encoding="utf-8")
    for svg_name, png_name in names.items():
        o = o.replace(f'href="images/{svg_name}" media-type="image/svg+xml"',
                      f'href="images/{png_name}" media-type="image/png"')
    opf.write_text(o, encoding="utf-8")

    out = BUILD / code / f"ethics-{code}-kindle.epub"
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        for p in sorted(stage.rglob("*")):
            if p.is_file() and p.name != "mimetype":
                z.write(p, p.relative_to(stage).as_posix(), compress_type=zipfile.ZIP_DEFLATED)
    shutil.rmtree(stage)
    print("OK KINDLE ->", out, f"({out.stat().st_size // 1024} KB)")
    return out


if __name__ == "__main__":
    convert(sys.argv[1] if len(sys.argv) > 1 else "en")
