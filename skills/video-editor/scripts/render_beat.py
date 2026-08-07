#!/usr/bin/env python3
"""
Render beat HTML templates to PNG frame sequences using Playwright (Chromium).

Two modes:

  Single beat:
    render_beat.py single \
      --template stat-callout --layout A --side right \
      --duration-ms 4400 --fps 30 \
      --props-json '{"number":"+248%","label":"retention"}' \
      --out-dir path/to/beat_01

  All beats from beats.yaml:
    render_beat.py all --beats beats.yaml --out-dir path/to/beats-snapshots --fps 30

Output structure (all mode):
    <out-dir>/beat_01/frame_00000.png ... frame_NNNNN.png
"""
import argparse, base64, json, mimetypes, os, pathlib, sys, time
import yaml

def _to_data_uri(path):
    mt, _ = mimetypes.guess_type(path)
    mt = mt or "application/octet-stream"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mt};base64,{b64}"

def _normalize_paths(props):
    """Props ending in _src or _path pointing to a local file are inlined as
    data: URIs so Chromium can load them regardless of file:// restrictions."""
    if not isinstance(props, dict):
        return props
    out = {}
    for k, v in props.items():
        if isinstance(v, str) and (k.endswith("_src") or k.endswith("_path")):
            if v.startswith(("http://", "https://", "data:")):
                out[k] = v
            elif os.path.exists(v):
                out[k] = _to_data_uri(v)
            else:
                out[k] = v
        elif isinstance(v, dict):
            out[k] = _normalize_paths(v)
        elif isinstance(v, list):
            out[k] = [_normalize_paths(x) if isinstance(x, dict) else x for x in v]
        else:
            out[k] = v
    return out

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
SCENE_DIR = SKILL_DIR / "scene-library"

TEMPLATES = {
    "stat-callout", "text-callout", "list-build",
    "quote-card", "code-beat", "comparison", "end-card",
    "dual-card", "subtitle-bar", "feature-list", "process-flow",
}

def template_path(name):
    p = SCENE_DIR / f"{name}.html"
    if not p.exists():
        raise FileNotFoundError(f"scene template not found: {p}")
    return p

def render_one(pw_browser, template, layout, side, props, duration_ms, fps, out_dir):
    from playwright.sync_api import Error as PWError
    out_dir = pathlib.Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    page = pw_browser.new_page(viewport={"width": 1920, "height": 1080})
    full_props = {**_normalize_paths(props or {}), "layout": layout, "side": side, "beat_start_ms": 0}
    page.add_init_script(f"window.__PROPS__ = {json.dumps(full_props)};")
    page.goto(template_path(template).as_uri(), wait_until="load")
    try:
        page.wait_for_function("window.__READY__ === true", timeout=8000)
    except PWError:
        print(f"[render] WARNING: {template} did not set __READY__ in time, proceeding", file=sys.stderr)
    # Force transparent page background.
    page.evaluate("document.documentElement.style.background='transparent'; document.body.style.background='transparent';")

    total_frames = max(1, int(round(duration_ms / 1000.0 * fps)))
    step_ms = 1000.0 / fps
    t0 = time.time()
    for i in range(total_frames):
        t_ms = int(round(i * step_ms))
        # drive time deterministically via a CSS var (not required, but keeps animations moving)
        page.evaluate(f"window.__FRAME_MS__ = {t_ms};")
        # Let the page run for one animation frame of simulated time
        page.wait_for_timeout(step_ms)
        png = page.screenshot(omit_background=True, type="png", full_page=False,
                              clip={"x": 0, "y": 0, "width": 1920, "height": 1080})
        (out_dir / f"frame_{i:05d}.png").write_bytes(png)
    page.close()
    print(f"[render] {template}/{layout}/{side} → {out_dir} ({total_frames} frames, {time.time()-t0:.1f}s)")

def cmd_single(args):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--disable-web-security", "--allow-file-access-from-files",
                  "--force-color-profile=srgb", "--enable-features=NetworkService"]
        )
        props = json.loads(args.props_json) if args.props_json else {}
        render_one(browser, args.template, args.layout, args.side,
                   props, args.duration_ms, args.fps, args.out_dir)
        browser.close()

def cmd_all(args):
    from playwright.sync_api import sync_playwright
    beats_path = pathlib.Path(args.beats)
    data = yaml.safe_load(beats_path.read_text())
    beats = data.get("beats", [])
    out_root = pathlib.Path(args.out_dir); out_root.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--disable-web-security", "--allow-file-access-from-files",
                  "--force-color-profile=srgb"]
        )
        for b in beats:
            bid = int(b["id"])
            if args.only and bid not in args.only:
                continue
            start = float(b["start"]); end = float(b["end"])
            dur_ms = int((end - start) * 1000)
            layout = b.get("layout", "A")
            side   = b.get("side", "right")
            props  = dict(b.get("props", {}))
            props["beat_start_ms"] = 0
            tmpl   = b["template"]
            if tmpl not in TEMPLATES:
                print(f"[render] skipping beat {bid}: unknown template '{tmpl}'"); continue
            render_one(browser, tmpl, layout, side, props, dur_ms, args.fps,
                       out_root / f"beat_{bid:02d}")
        browser.close()

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)

    s = sub.add_parser("single")
    s.add_argument("--template", required=True, choices=sorted(TEMPLATES))
    s.add_argument("--layout",   default="A", choices=["A", "B"])
    s.add_argument("--side",     default="right", choices=["left", "right"])
    s.add_argument("--duration-ms", type=int, required=True)
    s.add_argument("--fps", type=int, default=30)
    s.add_argument("--props-json", default="{}")
    s.add_argument("--out-dir", required=True)
    s.set_defaults(func=cmd_single)

    a = sub.add_parser("all")
    a.add_argument("--beats", required=True)
    a.add_argument("--out-dir", required=True)
    a.add_argument("--fps", type=int, default=30)
    a.add_argument("--only", nargs="*", type=int, default=None,
                   help="only render beats with these ids")
    a.set_defaults(func=cmd_all)

    args = ap.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
