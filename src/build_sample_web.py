"""Monta uma AMOSTRA web single-file (Prefácio + Parte I) self-contained.
Tudo inline (CSS + SVG + capa em data-URI) -> abre local ou hospeda em qualquer lugar.
Saída: build/etica-amostra.html
"""
import base64, re
from pathlib import Path
import book_meta as M

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
PARTS = SRC / "parts"
ASSETS = ROOT / "assets"
BUILD = ROOT / "build"
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}


def svg_datauri(name: str) -> str:
    p = ASSETS / name
    if not p.exists():
        return ""
    b = p.read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(b).decode()


def inline_svgs(html: str) -> str:
    def repl(m):
        return svg_datauri(m.group(2)) or m.group(0)
    return re.sub(r'(\.\./assets/|images/)([A-Za-z0-9_-]+\.svg)', repl, html)


def opener(n, title, epi, ref, svg) -> str:
    return (f'<div class="epub-opener"><div class="kick">Parte {ROMAN[n]}</div>'
            f'<img src="{svg_datauri(svg)}" alt=""/>'
            f'<p class="epigraph">“{epi}”<span class="ref">{ref}</span></p></div>')


WEB_CSS = """
:root{--maxw:720px}
html,body{margin:0;background:#ece3d4}
.topbar{position:sticky;top:0;z-index:30;background:rgba(22,38,61,.98);color:#f3ece0;
 display:flex;align-items:center;justify-content:space-between;gap:12px;padding:11px 20px;
 font-family:Georgia,serif;border-bottom:1px solid #a9853f}
.topbar .t{font-weight:bold;letter-spacing:.3px;font-size:17px}
.topbar .badge{font-size:11px;letter-spacing:1.5px;text-transform:uppercase;color:#16263d;background:#a9853f;
 padding:5px 12px;border-radius:999px;font-family:system-ui,sans-serif;font-weight:700;white-space:nowrap}
.progress{position:fixed;top:0;left:0;height:3px;background:#a9853f;width:0;z-index:40}
.reader{max-width:var(--maxw);margin:0 auto;padding:40px 26px 90px;background:#faf6ec;
 box-shadow:0 0 70px rgba(0,0,0,.10);font-size:19px;line-height:1.72}
.reader img{max-width:100%;height:auto}
.titlepage{text-align:center;padding:24px 0 6px;border:0}
.titlepage .coverimg{max-width:300px;width:64%;border-radius:6px;box-shadow:0 18px 50px rgba(0,0,0,.32);margin-bottom:26px}
.titlepage h1{font-size:64px;margin:.1em 0}
.sample-badge{display:inline-block;margin:14px 0 6px;font-family:system-ui,sans-serif;font-size:13px;font-weight:700;
 letter-spacing:2px;text-transform:uppercase;color:#a9853f;border:1px solid #a9853f;padding:7px 16px;border-radius:999px}
.cta{margin:54px auto 0;max-width:640px;border:1.5px solid #a9853f;border-radius:16px;padding:34px 30px;
 background:#fff;text-align:center;font-family:Georgia,serif}
.cta h3{margin:0 0 12px;color:#16263d;font-size:26px}
.cta p{text-indent:0;text-align:center;color:#3c3a34;margin:8px 0;font-size:18px;line-height:1.6}
.cta .meta{font-family:system-ui,sans-serif;font-size:14px;color:#6c6555;margin-top:18px;letter-spacing:.3px}
@media(max-width:600px){.reader{font-size:17px;padding:26px 16px 64px}.titlepage h1{font-size:46px}}
"""

PROGRESS_JS = """
<script>
(function(){var bar=document.getElementById('pg');
function upd(){var h=document.documentElement;var s=h.scrollTop||document.body.scrollTop;
var max=(h.scrollHeight-h.clientHeight)||1;bar.style.width=(100*s/max)+'%';}
document.addEventListener('scroll',upd,{passive:true});window.addEventListener('resize',upd);upd();})();
</script>
"""


def build():
    epub_css = (SRC / "epub.css").read_text(encoding="utf-8")
    preface = inline_svgs((PARTS / "preface.html").read_text(encoding="utf-8"))
    p1 = M.PARTS[0]
    part1 = opener(*p1) + "\n" + inline_svgs((PARTS / "parte-1.html").read_text(encoding="utf-8"))
    cover_uri = "data:image/png;base64," + base64.b64encode((BUILD / "cover.png").read_bytes()).decode()

    titlepage = (
        f'<section class="titlepage">'
        f'<img class="coverimg" src="{cover_uri}" alt="Capa"/>'
        f'<h1>{M.TITLE}</h1>'
        f'<p class="sub">{M.SUBTITLE}</p>'
        f'<div class="author">{M.AUTHOR}</div>'
        f'<div class="edition">{M.EDITION}</div>'
        f'<div class="sample-badge">Amostra · Prefácio + Parte I de V</div>'
        f'</section>')

    cta = (
        '<div class="cta"><h3>Fim da amostra</h3>'
        '<p>Você leu o Prefácio e a Parte I — <em>Deus, ou a Natureza</em>.</p>'
        '<p>A edição completa traz as cinco partes (a Mente, os Afetos, a Servidão e a Liberdade), '
        'além do posfácio sobre Spinoza na era da IA e do glossário.</p>'
        '<div class="meta">Edição completa · 84 páginas · PDF + Kindle EPUB · ~20.900 palavras</div>'
        '</div>')

    body = (
        '<div class="progress" id="pg"></div>'
        f'<div class="topbar"><span class="t">{M.TITLE} — Spinoza para o século XXI</span>'
        '<span class="badge">Amostra grátis</span></div>'
        f'<div class="reader">{titlepage}{preface}{part1}{cta}</div>'
        + PROGRESS_JS)

    doc = (
        '<!DOCTYPE html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8"/>\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1"/>\n'
        f'<title>{M.TITLE} — Amostra | Spinoza para o século XXI</title>\n'
        '<meta name="description" content="Amostra grátis: Prefácio e Parte I da Ética de Spinoza, edição moderna PT-BR."/>\n'
        f'<style>{epub_css}\n/* ---- web reader ---- */\n{WEB_CSS}</style>\n</head>\n<body>\n{body}\n</body>\n</html>\n')

    out = BUILD / "etica-amostra.html"
    out.write_text(doc, encoding="utf-8")
    print("OK ->", out, f"({len(doc)//1024} KB)")


if __name__ == "__main__":
    build()
