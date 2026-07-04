import threading, functools, http.server, socketserver
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parent.parent
h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
httpd = socketserver.TCPServer(("127.0.0.1",0), h); port=httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()
outdir = ROOT/"build"/"preview"; outdir.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":1240,"height":1860}, device_scale_factor=2)
    pg.goto(f"http://127.0.0.1:{port}/src/sample-part1.html", wait_until="networkidle", timeout=60000)
    pg.wait_for_function("window.__pagedDone === true", timeout=120000)
    pages = pg.query_selector_all(".pagedjs_page")
    for i,el in enumerate(pages,1):
        el.screenshot(path=str(outdir/f"p{i:02d}.png"))
    print("shots:", len(pages))
    b.close()
httpd.shutdown()
