"""
Renderiza um HTML (paginado via Paged.js) para PDF de qualidade de livro.
Uso: python render.py <input.html relativo a src/> <output.pdf>

Serve o projeto via HTTP local (evita o bloqueio de CORS do file:// que
impede o Paged.js de ler o CSS), carrega no Chromium headless, espera a
paginação e exporta page.pdf() honrando o @page CSS (6x9").
"""
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent  # raiz do projeto


def _serve(directory: str):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=directory)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, port


def render(html_rel: str, pdf_path: str) -> None:
    httpd, port = _serve(str(ROOT))
    rel = Path(html_rel).resolve().relative_to(ROOT).as_posix()
    url = f"http://127.0.0.1:{port}/{rel}"
    out = str(Path(pdf_path).resolve())
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_function("window.__pagedDone === true", timeout=120000)
            pages = page.evaluate("document.querySelectorAll('.pagedjs_page').length")
            page.pdf(
                path=out,
                prefer_css_page_size=True,
                print_background=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            )
            browser.close()
        print(f"OK -> {out}  ({pages} páginas)")
        if errors:
            print("avisos:", errors[:3])
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("uso: python render.py <input.html> <output.pdf>")
        sys.exit(1)
    render(sys.argv[1], sys.argv[2])
