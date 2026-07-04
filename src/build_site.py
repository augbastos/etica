# -*- coding: utf-8 -*-
"""
build_site.py — monta o SITE multilíngue (só samples + página comprar).

Estrutura gerada em ../site-amostra/:
  index.html            -> landing com seletor de idioma (6)
  <lang>/index.html     -> sample (Prefácio + Parte I) + CTA -> buy
  <lang>/buy.html       -> página "comprar" (botões de loja, "em breve")

Self-contained (CSS + SVG + capa inline). Estética navy/dourado dos livros.
Sem nenhuma associação com outras marcas (livro independente/laico).
"""
import sys, json, base64, re, shutil
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
ASSETS = ROOT / "assets"
BUILD = ROOT / "build"
SITE = ROOT / "site-amostra"
sys.path.insert(0, str(SRC))
from build_lang import load_meta, parts_dir, font_style

LANGS = ["pt", "en", "es", "ru", "zh", "ja"]
LANG_NAME = {"pt": "Português", "en": "English", "es": "Español", "ru": "Русский", "zh": "中文", "ja": "日本語"}
UI = json.loads((ROOT / "i18n" / "ui_strings.json").read_text(encoding="utf-8"))
EPUB_CSS = (SRC / "epub.css").read_text(encoding="utf-8")

STORES = ["Amazon Kindle", "Apple Books", "Kobo", "Google Play Books", "Gumroad"]


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def svg_uri(name: str, code: str = "pt") -> str:
    loc = ROOT / "i18n" / code / "assets" / name
    p = loc if loc.exists() else (ASSETS / name)
    return ("data:image/svg+xml;base64," + b64(p)) if p.exists() else ""


def inline_svgs(html: str, code: str = "pt") -> str:
    return re.sub(r'(\.\./assets/|images/)([A-Za-z0-9_-]+\.svg)',
                  lambda m: svg_uri(m.group(2), code) or m.group(0), html)


def frag(code, name):
    f = parts_dir(code) / name
    return inline_svgs(f.read_text(encoding="utf-8"), code) if f.exists() else ""


# --- KDP Select: sample externo deve ficar <=10% do livro -----------------
# Mostramos Prefácio + abertura da Parte I + um trecho TRUNCADO da Parte I,
# cortado em fronteira de bloco de topo (nunca no meio de uma proposição),
# de modo que o total de prosa fique <= ~9,2% do livro inteiro.
_BOOK_FILES = ["preface.html", "parte-1.html", "parte-2.html", "parte-3.html",
               "parte-4.html", "parte-5.html", "posface.html", "glossary.html", "closing.html"]
_VOID = {"img", "br", "hr", "meta", "col", "input", "source"}
_SAMPLE_FRAC = 0.092  # margem de segurança sob o limite de 10%


def _wc(html: str) -> int:
    return len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", html), re.UNICODE))


def book_total_words(code: str) -> int:
    d = parts_dir(code)
    return sum(_wc((d / f).read_text(encoding="utf-8")) for f in _BOOK_FILES if (d / f).exists())


def _best_cut(html: str, budget: int) -> int:
    """Maior índice de corte em fronteira de bloco de topo (depth 0) com palavras <= budget."""
    depth = 0
    words = 0
    best = 0
    for m in re.finditer(r"<(/?)([A-Za-z0-9]+)([^>]*?)(/?)>|([^<]+)", html):
        if m.group(5) is not None:
            words += len(re.findall(r"\w+", m.group(5), re.UNICODE))
            continue
        closing = m.group(1) == "/"
        name = m.group(2).lower()
        selfclose = m.group(4) == "/" or name in _VOID
        if closing:
            depth = max(0, depth - 1)
        elif not selfclose:
            depth += 1
        if depth == 0:
            if words <= budget:
                best = m.end()
            else:
                break
    return best


def sample_part1(code: str) -> str:
    """Parte I truncada p/ manter o sample <= ~9,2% do livro (KDP Select-safe)."""
    raw = frag(code, "parte-1.html")
    if not raw.strip():
        return ""
    total = book_total_words(code)
    pref = _wc(frag(code, "preface.html"))
    budget = int(_SAMPLE_FRAC * total) - pref - 25  # 25 ~ epígrafe do opener
    if budget < 60:
        return ""  # CJK: prefácio já perto do limite -> só a abertura (opener) serve de teaser
    m = re.match(r"^(\s*<section[^>]*>)(.*)(</section>\s*)$", raw, re.S)
    if not m:
        return raw if _wc(raw) <= budget else ""
    open_tag, inner, close_tag = m.group(1), m.group(2), m.group(3)
    cut = _best_cut(inner, budget)
    if cut == 0:
        return ""
    more = '<p class="lead" style="text-align:center;opacity:.45;letter-spacing:.3em">⋯</p>'
    return open_tag + inner[:cut] + more + close_tag


WEB_CSS = """
:root{--maxw:720px}
html,body{margin:0;background:#ece3d4}
.topbar{position:sticky;top:0;z-index:30;background:rgba(22,38,61,.98);color:#f3ece0;
 display:flex;align-items:center;justify-content:space-between;gap:12px;padding:11px 20px;
 font-family:Georgia,serif;border-bottom:1px solid #a9853f}
.topbar .t{font-weight:bold;font-size:16px}
.topbar .right{display:flex;align-items:center;gap:12px}
.topbar a.home{color:#bfae86;text-decoration:none;font-size:13px;font-family:system-ui,sans-serif}
.topbar .badge{font-size:11px;letter-spacing:1.2px;text-transform:uppercase;color:#16263d;background:#a9853f;
 padding:5px 12px;border-radius:999px;font-family:system-ui,sans-serif;font-weight:700;white-space:nowrap}
.progress{position:fixed;top:0;left:0;height:3px;background:#a9853f;width:0;z-index:40}
.reader{max-width:var(--maxw);margin:0 auto;padding:40px 26px 90px;background:#faf6ec;
 box-shadow:0 0 70px rgba(0,0,0,.10);font-size:19px;line-height:1.72}
.reader img{max-width:100%;height:auto}
.titlepage{text-align:center;padding:24px 0 6px;border:0}
.titlepage .coverimg{max-width:300px;width:64%;border-radius:6px;box-shadow:0 18px 50px rgba(0,0,0,.32);margin-bottom:26px}
.titlepage h1{font-size:60px;margin:.1em 0}
.sample-badge{display:inline-block;margin:14px 0 6px;font-family:system-ui,sans-serif;font-size:13px;font-weight:700;
 letter-spacing:1.5px;text-transform:uppercase;color:#a9853f;border:1px solid #a9853f;padding:7px 16px;border-radius:999px}
.cta{margin:54px auto 0;max-width:640px;border:1.5px solid #a9853f;border-radius:16px;padding:34px 30px;
 background:#fff;text-align:center;font-family:Georgia,serif}
.cta h3{margin:0 0 12px;color:#16263d;font-size:26px}
.cta p{text-indent:0;text-align:center;color:#3c3a34;margin:8px 0;font-size:18px;line-height:1.6}
.cta .meta{font-family:system-ui,sans-serif;font-size:14px;color:#6c6555;margin:16px 0 22px;letter-spacing:.3px}
.btn{display:inline-block;background:#16263d;color:#f3ece0;text-decoration:none;font-family:system-ui,sans-serif;
 font-weight:700;font-size:17px;padding:15px 30px;border-radius:12px;border:1px solid #a9853f}
.btn:hover{background:#1d3252}
@media(max-width:600px){.reader{font-size:17px;padding:26px 16px 64px}.titlepage h1{font-size:46px}}
"""

PROGRESS_JS = ("<script>(function(){var b=document.getElementById('pg');function u(){var h="
               "document.documentElement,s=h.scrollTop||document.body.scrollTop,m=(h.scrollHeight-h.clientHeight)||1;"
               "b.style.width=(100*s/m)+'%';}document.addEventListener('scroll',u,{passive:true});"
               "window.addEventListener('resize',u);u();})();</script>")

# shared page-shell pieces (navy/gold, geometry) for landing + buy
SHELL_CSS = """
*{margin:0;box-sizing:border-box}
body{font-family:'Cormorant Garamond',Georgia,serif;color:#f4f1e8;min-height:100vh;
 background:radial-gradient(120% 95% at 50% -8%,#1d2c52 0%,#131e3c 46%,#0a1228 100%);
 display:flex;flex-direction:column;align-items:center;justify-content:center;padding:60px 22px;position:relative;overflow-x:hidden}
.geo{position:fixed;left:50%;top:46%;transform:translate(-50%,-50%);width:min(1100px,150vw);height:min(1100px,150vw);
 border-radius:50%;border:1px solid rgba(201,169,106,.12);box-shadow:0 0 0 120px rgba(201,169,106,.035);pointer-events:none}
.kick{font-family:'Inter',system-ui,sans-serif;color:#c9a96a;font-weight:700;letter-spacing:5px;
 text-transform:uppercase;font-size:15px;margin-bottom:18px;text-align:center}
h1.big{font-size:64px;font-weight:600;letter-spacing:1px;text-align:center;line-height:1.05}
.sub{font-style:italic;color:#cdd6ea;font-size:22px;text-align:center;margin-top:14px;max-width:680px}
.rule{width:80px;height:4px;background:#c9a96a;border-radius:2px;margin:34px auto}
a{color:inherit}
"""

FONT_IMPORT = ("@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;"
               "1,500&family=Inter:wght@400;600;700&display=swap');")
CJK_STACK = ("'Noto Serif SC','Noto Serif JP','Source Han Serif SC','Songti SC','Yu Mincho','MS Mincho',serif")


def sample_page(code) -> str:
    m = load_meta(code)
    ui = UI[code]
    cover = BUILD / code / "cover.png"
    cover_uri = "data:image/png;base64," + b64(cover) if cover.exists() else ""
    p1 = m["PARTS"][0]
    # Part I opener (epub style) + content
    opener = (f'<div class="epub-opener"><div class="kick">{("第一部" if code in ("zh","ja") else ("Часть I" if code=="ru" else ("Part I" if code=="en" else "Parte I")))}</div>'
              f'<img src="{svg_uri(p1["svg"], code)}" alt=""/>'
              f'<p class="epigraph">“{p1["epi"]}”<span class="ref">{p1["ref"]}</span></p></div>')
    body_reader = (
        f'<section class="titlepage">'
        f'<img class="coverimg" src="{cover_uri}" alt=""/>'
        f'<h1>{m["TITLE"]}</h1><p class="sub">{m["SUBTITLE"]}</p>'
        f'<div class="author">{m["AUTHOR"]}</div><div class="edition">{m["EDITION"]}</div>'
        f'<div class="sample-badge">{ui["sample_badge"]}</div></section>'
        f'{frag(code, "preface.html")}'
        f'{opener}{sample_part1(code)}'
        f'<div class="cta"><h3>{ui["end_title"]}</h3>'
        f'<p>{ui["end_p1"]}</p><p>{ui["end_p2"]}</p>'
        f'<div class="meta">{ui["meta_line"]}</div>'
        f'<a class="btn" href="buy.html">{ui["get_book"]} →</a></div>')
    fs = font_style(code)
    fs_tag = f"\n/* lang font */\n{fs}" if fs else ""
    return (f'<!DOCTYPE html><html lang="{m["LANG"]}"><head><meta charset="utf-8"/>'
            f'<meta name="viewport" content="width=device-width, initial-scale=1"/>'
            f'<title>{m["TITLE"]} — {ui["free_sample"]}</title>'
            f'<style>{EPUB_CSS}\n/* web */\n{WEB_CSS}{fs_tag}</style></head><body>'
            f'<div class="progress" id="pg"></div>'
            f'<div class="topbar"><span class="t">{m["TITLE"]}</span>'
            f'<span class="right"><a class="home" href="../index.html">{ui["choose_language"]} ▾</a>'
            f'<span class="badge">{ui["free_sample"]}</span></span></div>'
            f'<div class="reader">{body_reader}</div>{PROGRESS_JS}</body></html>')


def buy_page(code) -> str:
    m = load_meta(code)
    ui = UI[code]
    cjk = code in ("zh", "ja")
    title_font = CJK_STACK if cjk else "'Cormorant Garamond',Georgia,serif"
    btns = "".join(
        f'<div class="store"><span class="nm">{s}</span><span class="soon">{ui["coming_soon"]}</span></div>'
        for s in STORES)
    extra = f"""
.wrap{{position:relative;z-index:2;max-width:680px;width:100%;text-align:center}}
h1.big{{font-family:{title_font}}}
.stores{{display:flex;flex-direction:column;gap:14px;margin:30px auto 0;max-width:460px}}
.store{{display:flex;align-items:center;justify-content:space-between;background:rgba(255,255,255,.05);
 border:1px solid rgba(201,169,106,.35);border-radius:14px;padding:18px 22px;font-family:'Inter',system-ui,sans-serif;opacity:.85}}
.store .nm{{font-weight:600;font-size:18px;color:#eef2fb}}
.store .soon{{font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#0a1228;
 background:#c9a96a;padding:5px 12px;border-radius:999px}}
.notice{{margin-top:26px;color:#9fb0d0;font-family:'Inter',system-ui,sans-serif;font-size:15px}}
.back{{display:inline-block;margin-top:30px;color:#c9a96a;text-decoration:none;font-family:'Inter',system-ui,sans-serif;font-size:15px}}
"""
    return (f'<!DOCTYPE html><html lang="{m["LANG"]}"><head><meta charset="utf-8"/>'
            f'<meta name="viewport" content="width=device-width, initial-scale=1"/>'
            f'<title>{ui["buy_title"]} — {m["TITLE"]}</title>'
            f'<style>{FONT_IMPORT}{SHELL_CSS}{extra}</style></head><body>'
            f'<div class="geo"></div><div class="wrap">'
            f'<div class="kick">{m["TITLE"]} · {m["AUTHOR"]}</div>'
            f'<h1 class="big">{ui["buy_title"]}</h1><div class="rule"></div>'
            f'<p class="sub" style="margin:0 auto">{ui["buy_sub"]}</p>'
            f'<div class="stores">{btns}</div>'
            f'<div class="notice">{ui["not_available"]}</div>'
            f'<a class="back" href="index.html">{ui["back_to_sample"]}</a>'
            f'</div></body></html>')


def landing() -> str:
    cards = ""
    for code in LANGS:
        m = load_meta(code)
        cjk = code in ("zh", "ja")
        tf = CJK_STACK if cjk else "'Cormorant Garamond',Georgia,serif"
        cards += (f'<a class="card" href="{code}/index.html">'
                  f'<span class="ttl" style="font-family:{tf}">{m["TITLE"]}</span>'
                  f'<span class="ln">{LANG_NAME[code]}</span></a>')
    extra = """
.wrap{position:relative;z-index:2;max-width:900px;width:100%;text-align:center}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:40px}
@media(max-width:680px){.cards{grid-template-columns:repeat(2,1fr)}}
.card{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;
 background:rgba(255,255,255,.05);border:1px solid rgba(201,169,106,.30);border-radius:16px;
 padding:30px 16px;text-decoration:none;transition:.15s}
.card:hover{background:rgba(201,169,106,.12);border-color:#c9a96a;transform:translateY(-2px)}
.card .ttl{font-size:38px;font-weight:600;color:#f4f1e8;line-height:1}
.card .ln{font-family:'Inter',system-ui,sans-serif;font-size:14px;letter-spacing:1px;color:#bfae86;text-transform:uppercase}
.free{font-family:'Inter',system-ui,sans-serif;font-size:13px;color:#9fb0d0;margin-top:30px;letter-spacing:.5px}
"""
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>'
            f'<meta name="viewport" content="width=device-width, initial-scale=1"/>'
            f'<title>Ethics — Spinoza · free sample in 6 languages</title>'
            f'<style>{FONT_IMPORT}{SHELL_CSS}{extra}</style></head><body>'
            f'<div class="geo"></div><div class="wrap">'
            f'<div class="kick">Benedictus de Spinoza · 2026</div>'
            f'<h1 class="big">Ethics</h1>'
            f'<p class="sub" style="margin:14px auto 0">A modern reading of Spinoza\'s Ethics — free sample</p>'
            f'<div class="rule"></div>'
            f'<div class="cards">{cards}</div>'
            f'<div class="free">Choose your language · 选择语言 · 言語を選択 · Выберите язык</div>'
            f'</div></body></html>')


def build():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    (SITE / "index.html").write_text(landing(), encoding="utf-8")
    for code in LANGS:
        d = SITE / code
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(sample_page(code), encoding="utf-8")
        (d / "buy.html").write_text(buy_page(code), encoding="utf-8")
        print("OK site ->", code)
    print("SITE ready ->", SITE)


if __name__ == "__main__":
    build()
