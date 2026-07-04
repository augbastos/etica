"""
Monta o HTML mestre da edição PDF (paginada via Paged.js) e o salva em
src/book-full.html. Depois rode: python render.py src/book-full.html build/etica-spinoza-2026.pdf
"""
from pathlib import Path
import book_meta as M
from _gates import run_gates

SRC = Path(__file__).resolve().parent
PARTS_DIR = SRC / "parts"


def frag(name: str) -> str:
    f = PARTS_DIR / name
    return f.read_text(encoding="utf-8") if f.exists() else f'<section class="chapter"><h2>[faltando: {name}]</h2></section>'


def opener(n, title, epi, ref, svg) -> str:
    return f'''
<section class="part-opener">
  <div class="art"><img src="../assets/{svg}" alt="" style="width:100%;height:100%;object-fit:cover;"></div>
  <div class="inner">
    <div class="part-kicker">Parte {_roman(n)}</div>
    <h1>{title}</h1>
    <hr class="rule-gold">
    <p class="epigraph">“{epi}”</p>
    <p class="epigraph" style="font-size:9pt;letter-spacing:.2em;font-style:normal;margin-top:8mm;color:#c8a868;">{ref.upper()}</p>
  </div>
</section>'''


def _roman(n):
    return {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}[n]


def build():
    # Validation barrier: aborts (SystemExit 1) before writing book-full.html
    # if a hard gate fails. Override only via SPINOZA_GATES env knobs.
    run_gates()

    parts_html = []
    parts_html.append(frag("preface.html"))
    for (n, title, epi, ref, svg) in M.PARTS:
        parts_html.append(opener(n, title, epi, ref, svg))
        parts_html.append(frag(f"parte-{n}.html"))
    parts_html.append(frag("posface.html"))
    parts_html.append(frag("glossary.html"))

    body = "\n".join(parts_html)
    html = f'''<!DOCTYPE html>
<html lang="{M.LANG}">
<head>
<meta charset="utf-8">
<title>{M.TITLE} — Spinoza 2026</title>
<link rel="stylesheet" href="book.css">
<script>window.PagedConfig = {{ auto: true, after: () => {{ window.__pagedDone = true; }} }};</script>
<script src="https://unpkg.com/pagedjs/dist/paged.polyfill.js"></script>
</head>
<body>

<section class="titlepage">
  <img class="mark" src="../assets/mark.svg" alt="">
  <h1>{M.TITLE}</h1>
  <p class="sub">{M.SUBTITLE}</p>
  <div class="author">{M.AUTHOR}</div>
  <div class="edition">{M.EDITION}</div>
</section>

{body}

</body>
</html>'''
    out = SRC / "book-full.html"
    out.write_text(html, encoding="utf-8")
    print("OK ->", out, f"({len(html)} chars)")


if __name__ == "__main__":
    build()
