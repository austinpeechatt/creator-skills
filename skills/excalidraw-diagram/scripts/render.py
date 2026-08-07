#!/usr/bin/env python
"""
render.py — rasterize a .excalidraw file to PNG using Excalidraw's own
exportToSvg (loaded headless via esm.sh). Lets us self-QA a diagram's
layout, logos, color and contrast before handing it to Austin.

Usage:  render.py <scene.excalidraw> <out.png> [scale=2]

Note: text renders in a fallback sans (Excalifont isn't loaded headless),
so word-wrap width is approximate — leave a little slack in box widths.
Shapes, colors, logos and layout are faithful.
"""
import sys, json, threading, http.server, socketserver, tempfile, functools
from pathlib import Path
from playwright.sync_api import sync_playwright

EXCALIDRAW_VER = "0.18.0"

HTML = """<!doctype html><html><head><meta charset="utf-8">
<style>html,body{margin:0;padding:0;background:#fff}</style></head>
<body><div id="root"></div>
<script type="module">
  window.__err = null;
  try {
    const m = await import("https://esm.sh/@excalidraw/excalidraw@%s");
    window.__exportToSvg = m.exportToSvg;
    window.__ready = true;
  } catch (e) { window.__err = String(e); }
</script></body></html>""" % EXCALIDRAW_VER


def _serve(html):
    """Serve HTML over a real http origin (localStorage works there, unlike
    about:blank). Returns (url, shutdown_fn)."""
    d = tempfile.mkdtemp()
    Path(d, "index.html").write_text(html)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=d)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}/index.html", httpd.shutdown


def render(src, out, scale=2):
    out = str(Path(out).resolve())
    scene = json.loads(Path(src).read_text())
    payload = {
        "elements": scene["elements"],
        "files": scene.get("files", {}),
        "appState": {
            "exportBackground": True,
            "viewBackgroundColor": "#ffffff",
            "exportWithDarkMode": False,
            "exportPadding": 32,
        },
    }
    url, shutdown = _serve(HTML)
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(device_scale_factor=scale)
        logs = []
        page.on("console", lambda m: logs.append(m.text))
        page.on("pageerror", lambda e: logs.append("PAGEERR " + str(e)))
        page.goto(url, wait_until="load")
        try:
            page.wait_for_function("window.__ready === true || window.__err",
                                   timeout=45000)
        except Exception:
            pass
        err = page.evaluate("window.__err")
        if err:
            print("IMPORT ERROR:", err, file=sys.stderr)
            print("\n".join(logs[-10:]), file=sys.stderr)
            b.close(); sys.exit(2)
        dim = page.evaluate(
            """async (d) => {
                const svg = await window.__exportToSvg(d);
                svg.style.display = 'block';
                document.getElementById('root').appendChild(svg);
                const w = svg.width.baseVal.value || svg.viewBox.baseVal.width;
                const h = svg.height.baseVal.value || svg.viewBox.baseVal.height;
                return {w, h};
            }""", payload)
        page.wait_for_timeout(500)  # let svg <image> logos decode
        el = page.query_selector("#root svg")
        el.screenshot(path=out)
        b.close()
    shutdown()
    print(f"rendered {out}  ({dim['w']:.0f}x{dim['h']:.0f} @ {scale}x)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    render(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 2)
