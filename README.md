# Ética — a multi-agent book production pipeline

An automated, agent-orchestrated pipeline that turns a public-domain source text
(the Elwes translation of Spinoza's *Ethics*) into a modern, typeset book —
print-ready PDF, EPUB3/Kindle, generative cover art, and a multi-language build —
with quality gates between stages.

This repo is the **engineering**, not the book. The full adapted prose is a
separate commercial edition (on Kindle); here you get the pipeline and a Part I
sample so the system is inspectable end to end.

## What it does

```
source text ──▶ structure ──▶ typeset ──▶ art ──▶ package ──▶ gate
 (Gutenberg)     parts/CSS      Paged.js    SVG      EPUB/PDF   _gates.py
```

- **Typesetting** — `build_pdf.py` + `render.py` drive Paged.js over `book.css`
  to produce a print-ready PDF (running heads, page breaks, apparatus).
- **EPUB/Kindle** — `build_epub.py`, `epub_kindle.py`, `build_fxl_epub.py`
  package validated EPUB3 and Kindle outputs from the same source.
- **Generative art** — `gen_art.py`, `gen_cover.py`, `gen_covers.py`,
  `localize_svgs.py` produce covers and figures, sized to the current page count.
- **Multi-language** — `build_lang.py` orchestrates per-language builds from one
  source; `make_kdp_guides.py` emits the KDP metadata guides per edition.
- **Quality gates** — `_gates.py` blocks a stage from shipping if the previous
  stage's output fails its checks (the "agent that says no").
- **Web sample** — `build_sample_web.py` / `build_site.py` render the public
  sample (Preface + Part I).

## Run the sample

```bash
python src/build_sample_web.py   # renders the Part I web sample
python src/build_pdf.py          # print-ready PDF of the included sample
```

## What's included vs. not

**Included:** the full pipeline (`src/*.py`), templates/CSS, generative art
(`assets/`), the public-domain source (`fontes/`), and a **Part I sample**
(`src/parts/preface.html`, `parte-1.html`, plus glossary/closing).

**Not included (by design):** the complete adapted prose (Parts II–V), the
translated editions, and the compiled PDF/EPUB — those are the paid product.
`.gitignore` hard-denies them; `git ls-files` was verified clean before the first
commit.

## License

Pipeline: [MIT](./LICENSE). Source text (Elwes/Spinoza): public domain.
Adapted prose of the full book: © Augusto Bastos, not in this repo.
