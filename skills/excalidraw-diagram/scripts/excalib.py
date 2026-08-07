"""
excalib — Excalidraw scene builder for Axiom diagrams.

Enhanced 2026-06-25: logo/image embedding + richer shape vocabulary
(hexagon, polygon, pill, banner, ring) on top of the original
rect/oval/diamond/arrow helpers. Pair with render.py to self-QA a scene
to PNG before delivery.

Coordinate convention: every shape's `points` are RELATIVE to the element
x,y. Logos are uniform 24x24 viewBox SVGs in ../assets/logos.
"""
import json, math, base64, os, time

LOGO_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "logos")

# ---- brand colors for the logos we ship (for chips / accents) ----
BRAND = {
    "youtube": "#FF0000", "tiktok": "#000000", "instagram": "#E4405F",
    "x": "#000000", "linkedin": "#0A66C2", "supabase": "#3FCF8E",
    "netlify": "#00C7B7", "nextdotjs": "#000000", "notion": "#000000",
    "claude": "#D97757", "buffer": "#231F20",
}

# ---- AIW-leaning zone palette (stroke, fill) ----
PALETTE = {
    "blue":   ("#1971c2", "#e7f5ff"),
    "indigo": ("#3b5bdb", "#dbe4ff"),
    "green":  ("#2f9e44", "#d3f9d8"),
    "teal":   ("#0c8599", "#e3fafc"),
    "violet": ("#7950f2", "#f3d9fa"),
    "amber":  ("#e67700", "#fff9db"),
    "red":    ("#c92a2a", "#ffe3e3"),
    "gray":   ("#495057", "#f1f3f5"),
    "navy":   ("#0d1b3d", "#e7ebf5"),
    "slate":  ("#5c677d", "#f8f9fa"),
}
INK = "#1e1e1e"     # text on light fills
MUTE = "#868e96"    # annotations


def _base(id, type, x, y, w, h, **kw):
    return {
        "id": id, "type": type,
        "x": x, "y": y, "width": w, "height": h,
        "angle": kw.get("angle", 0),
        "strokeColor": kw.get("sc", INK),
        "backgroundColor": kw.get("bg", "transparent"),
        "fillStyle": kw.get("fs", "solid"),
        "strokeWidth": kw.get("sw", 2),
        "strokeStyle": kw.get("ss", "solid"),
        "roughness": kw.get("rough", 1),
        "opacity": kw.get("op", 100),
        "groupIds": kw.get("groupIds", []), "frameId": None,
        "roundness": kw.get("rnd", None),
        "boundElements": [], "updated": 1, "link": kw.get("link", None),
        "locked": False, "seed": kw.get("seed", 1),
    }


def txt(id, x, y, w, h, text, fs=16, **kw):
    e = _base(id, "text", x, y, w, h, **kw)
    e.update({"text": text, "fontSize": fs, "fontFamily": kw.get("ff", 1),
              "textAlign": kw.get("ta", "center"),
              "verticalAlign": kw.get("va", "top"),
              "containerId": None, "originalText": text, "lineHeight": 1.25})
    return e


def rect(id, x, y, w, h, **kw): return _base(id, "rectangle", x, y, w, h, **kw)
def oval(id, x, y, w, h, **kw): return _base(id, "ellipse",   x, y, w, h, **kw)
def dmd(id, x, y, w, h, **kw):  return _base(id, "diamond",   x, y, w, h, **kw)


def pill(id, x, y, w, h, **kw):
    kw.setdefault("rnd", {"type": 3})
    return _base(id, "rectangle", x, y, w, h, **kw)


def card(id, x, y, w, h, **kw):
    """Rounded container card."""
    kw.setdefault("rnd", {"type": 3})
    return _base(id, "rectangle", x, y, w, h, **kw)


def arr(id, x, y, pts, **kw):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    w = max(abs(max(xs) - min(xs)), 2); h = max(abs(max(ys) - min(ys)), 2)
    e = _base(id, "arrow", x, y, w, h, **kw)
    e.update({"points": pts, "lastCommittedPoint": None,
              "startBinding": None, "endBinding": None,
              "startArrowhead": kw.get("shead", None),
              "endArrowhead": kw.get("head", "arrow"),
              "roundness": kw.get("crnd", {"type": 2})})
    return e


def seg(id, x, y, pts, **kw):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    w = max(abs(max(xs) - min(xs)), 2); h = max(abs(max(ys) - min(ys)), 2)
    e = _base(id, "line", x, y, w, h, **kw)
    e.update({"points": pts, "lastCommittedPoint": None,
              "startBinding": None, "endBinding": None,
              "startArrowhead": None, "endArrowhead": None,
              "roundness": kw.get("crnd", None)})
    return e


def polygon(id, cx, cy, pts, **kw):
    """Closed filled polygon from points relative to (cx,cy). First point is
    repeated at the end so Excalidraw fills it. Use for hexagons/banners/chevrons."""
    closed = list(pts) + [pts[0]]
    xs = [p[0] for p in closed]; ys = [p[1] for p in closed]
    minx, miny = min(xs), min(ys)
    # normalize so element x,y = top-left of bbox, points relative to it
    rel = [[p[0] - minx, p[1] - miny] for p in closed]
    w = max(max(xs) - minx, 2); h = max(max(ys) - miny, 2)
    e = _base(id, "line", cx + minx, cy + miny, w, h, **kw)
    e.update({"points": rel, "lastCommittedPoint": None,
              "startBinding": None, "endBinding": None,
              "startArrowhead": None, "endArrowhead": None,
              "roundness": kw.get("crnd", None)})
    return e


def hexagon(id, cx, cy, r, **kw):
    """Pointy-top hexagon centered at (cx,cy), circumradius r."""
    pts = [(r * math.cos(math.radians(60 * i - 90)),
            r * math.sin(math.radians(60 * i - 90))) for i in range(6)]
    return polygon(id, cx, cy, pts, **kw)


def chevron(id, x, y, w, h, **kw):
    """Right-pointing chevron banner, top-left at (x,y)."""
    t = h * 0.5
    pts = [(0, 0), (w - t, 0), (w, h / 2), (w - t, h), (0, h), (t, h / 2)]
    return polygon(id, x, y, pts, **kw)


def ring(id, cx, cy, r, **kw):
    kw.setdefault("bg", "transparent")
    return _base(id, "ellipse", cx - r, cy - r, 2 * r, 2 * r, **kw)


_MIME = {".svg": "image/svg+xml", ".png": "image/png",
         ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def img(id, x, y, w, logo, files, h=None, **kw):
    """Embed a logo (svg/png/jpg) as an image element; registers it in `files`.
    `w` = width px; `h` defaults to `w` (square). `logo` = filename stem in
    assets/logos (extension auto-detected)."""
    h = h or w
    path, ext = None, None
    for e_ in (".svg", ".png", ".jpg", ".jpeg"):
        p = os.path.join(LOGO_DIR, f"{logo}{e_}")
        if os.path.exists(p):
            path, ext = p, e_
            break
    if path is None:
        raise FileNotFoundError(f"no logo asset for '{logo}' in {LOGO_DIR}")
    with open(path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    fid = f"logo-{logo}"
    if fid not in files:
        ts = int(time.time() * 1000)
        files[fid] = {"mimeType": _MIME[ext], "id": fid,
                      "dataURL": f"data:{_MIME[ext]};base64,{b64}",
                      "created": ts, "lastRetrieved": ts}
    el = _base(id, "image", x, y, w, h, **kw)
    el.update({"fileId": fid, "status": "saved", "scale": [1, 1],
               "crop": None})
    el["strokeColor"] = "transparent"
    el["backgroundColor"] = "transparent"
    return el


def logo_chip(idp, x, y, logo, files, label, w=150, h=58, accent=None,
              sub=None, ff=1, ss="solid", op=100, sw=2, bg="#ffffff"):
    """A white rounded chip: logo on the left, label (+optional sub) on right.
    Returns a list of elements. accent defaults to the brand color.
    Pass ss='dashed'/op=70 for a 'parked/future' state.
    accent defaults to a soft neutral border (premium look — the logo carries
    the color); pass a brand hex when you want color-coded borders."""
    accent = accent or "#b9c4db"
    els = [card(f"{idp}-bx", x, y, w, h, sc=accent, bg=bg,
                rnd={"type": 3}, sw=sw, ss=ss, op=op)]
    s = h - 26
    els.append(img(f"{idp}-lg", x + 14, y + (h - s) / 2, s, logo, files, op=op))
    tx = x + 14 + s + 10
    tw = w - (14 + s + 10) - 8
    if sub:
        els.append(txt(f"{idp}-t", tx, y + h / 2 - 17, tw, 20, label, fs=15,
                       ta="left", sc=INK, ff=ff, op=op))
        els.append(txt(f"{idp}-s", tx, y + h / 2 + 3, tw, 16, sub, fs=11,
                       ta="left", sc=MUTE, ff=ff, op=op))
    else:
        els.append(txt(f"{idp}-t", tx, y + h / 2 - 10, tw, 20, label, fs=15,
                       ta="left", sc=INK, ff=ff, op=op))
    return els


def save(elements, files, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({"type": "excalidraw", "version": 2,
                   "source": "https://excalidraw.com",
                   "elements": elements,
                   "appState": {"gridSize": None,
                                "viewBackgroundColor": "#ffffff"},
                   "files": files}, f, indent=2)
    print(f"✓ {path}  ({len(elements)} elements, {len(files)} images)")


def off(elements, ox, oy):
    out = []
    for e in elements:
        e = {**e, "x": e["x"] + ox, "y": e["y"] + oy}
        out.append(e)
    return out
