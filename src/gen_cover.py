"""Rasteriza cover.html para build/cover.png (1600x2560, padrão capa Kindle)."""
import threading, functools, http.server, socketserver
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def main():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), h)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    out = ROOT / "build" / "cover.png"
    out.parent.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1600, "height": 2560})
        pg.goto(f"http://127.0.0.1:{port}/src/cover.html", wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(700)
        pg.locator(".cover").screenshot(path=str(out))
        b.close()
    httpd.shutdown()
    print("OK ->", out)


if __name__ == "__main__":
    main()
