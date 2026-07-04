# -*- coding: utf-8 -*-
"""Gera capas LOCALIZADAS (1600x2560) por idioma -> build/<lang>/cover.png."""
import sys, base64, functools, http.server, socketserver, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
ASSETS = ROOT / "assets"
BUILD = ROOT / "build"
sys.path.insert(0, str(SRC))
from build_lang import load_meta

LANGS = ["pt", "en", "es", "ru", "zh", "ja"]

LATIN = "'Cormorant Garamond', Georgia, serif"
CJK = {
    "zh": "'Noto Serif SC','Source Han Serif SC','Songti SC','SimSun',serif",
    "ja": "'Noto Serif JP','Source Han Serif','Yu Mincho','MS Mincho',serif",
}


def title_font(code):
    if code in CJK:
        return CJK[code]
    return LATIN  # ru falls back to Georgia (Cyrillic) inside the stack


def edition_font(code):
    return CJK[code] if code in CJK else "'Inter',sans-serif"


def title_size(title):
    t = title.replace(" ", "")
    n = len(t)
    if n <= 3:
        return 340
    if n == 4:
        return 320
    if n == 5:
        return 290
    if n == 6:
        return 250
    return 210


def bg_datauri():
    b = (ASSETS / "part-opener-1.svg").read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(b).decode()


HTML = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700&family=Inter:wght@400;500;600&display=swap');
*{{margin:0;box-sizing:border-box}}
html,body{{width:1600px;height:2560px}}
.cover{{width:1600px;height:2560px;position:relative;overflow:hidden;background:#16263d;color:#faf6ec;
 display:flex;flex-direction:column;align-items:center;justify-content:center}}
.bg{{position:absolute;inset:0;opacity:.5}}
.bg img{{width:100%;height:100%;object-fit:cover}}
.inner{{position:relative;z-index:2;text-align:center;padding:0 150px}}
.kick{{font-family:'Inter',sans-serif;font-size:34px;letter-spacing:18px;text-transform:uppercase;color:#c8a868;margin-bottom:80px}}
h1{{font-family:{tfont};font-size:{tsize}px;font-weight:600;line-height:.92;color:#faf6ec;letter-spacing:2px}}
.rule{{width:120px;height:3px;background:#a9853f;margin:70px auto}}
.sub{{font-family:{tfont};font-style:italic;font-size:50px;line-height:1.4;color:#e7dcc3;max-width:1150px;margin:0 auto}}
.author{{font-family:'Inter',sans-serif;font-size:38px;letter-spacing:10px;text-transform:uppercase;position:absolute;bottom:300px;left:0;right:0;text-align:center;z-index:2}}
.edition{{font-family:{efont};font-size:26px;letter-spacing:8px;text-transform:uppercase;color:#c8a868;position:absolute;bottom:225px;left:0;right:0;text-align:center;z-index:2}}
</style></head><body>
<div class="cover">
  <div class="bg"><img src="{bg}" alt=""></div>
  <div class="inner">
    <div class="kick">Spinoza · 2026</div>
    <h1>{title}</h1>
    <div class="rule"></div>
    <p class="sub">{sub}</p>
  </div>
  <div class="author">{author}</div>
  <div class="edition">{edition}</div>
</div></body></html>"""


def main():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), h)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    bg = bg_datauri()
    tmp = SRC / "_cover_tmp.html"
    with sync_playwright() as p:
        b = p.chromium.launch()
        for code in LANGS:
            m = load_meta(code)
            title = (m["TITLE"] or "").strip()
            html = HTML.format(tfont=title_font(code), efont=edition_font(code),
                               tsize=title_size(title), bg=bg, title=title,
                               sub=m["SUBTITLE"], author=m["AUTHOR"], edition=m["EDITION"])
            tmp.write_text(html, encoding="utf-8")
            out = BUILD / code
            out.mkdir(parents=True, exist_ok=True)
            pg = b.new_page(viewport={"width": 1600, "height": 2560})
            pg.goto(f"http://127.0.0.1:{httpd.server_address[1]}/src/_cover_tmp.html", wait_until="networkidle", timeout=60000)
            pg.wait_for_timeout(900)
            pg.locator(".cover").screenshot(path=str(out / "cover.png"))
            pg.close()
            print("OK cover ->", code, title)
        b.close()
    tmp.unlink(missing_ok=True)
    httpd.shutdown()


if __name__ == "__main__":
    main()
