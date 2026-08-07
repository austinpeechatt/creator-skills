"""
Timeline editor server for the video-editor skill.

Serves a single-page editor UI against a project directory containing:
  assets/raw.mp4, assets/beats.yaml, renders/vN/final.mp4

Endpoints:
  GET  /                         -> editor HTML (from editor/index.html)
  GET  /api/state                -> {beats: [...], videos: {raw, final}, duration}
  POST /api/beats                -> save beats.yaml (body: {beats: [...]})
  POST /api/render               -> run render_beat.py --only <ids> + composite
  GET  /media/raw.mp4            -> raw video (Range supported)
  GET  /media/final.mp4          -> latest composited video (Range supported)

Usage:
  python editor_server.py <project_dir> [--port 7878]
"""
import argparse, io, json, os, re, shutil, subprocess, sys, threading, time, pathlib
import http.server, socketserver
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    print("pyyaml required: pip install pyyaml", file=sys.stderr); sys.exit(1)

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
EDITOR_HTML = SKILL_DIR / "editor" / "index.html"
RENDER_SCRIPT = SKILL_DIR / "scripts" / "render_beat.py"
COMPOSITE_SCRIPT = SKILL_DIR / "scripts" / "composite.py"

state_lock = threading.Lock()
render_log = []  # most recent render output
render_lock = threading.Lock()


def latest_final(project):
    renders = project / "renders"
    if not renders.exists():
        return None
    versions = sorted([p for p in renders.iterdir() if p.is_dir() and re.match(r"v\d+$", p.name)],
                      key=lambda p: int(p.name[1:]))
    for v in reversed(versions):
        f = v / "final.mp4"
        if f.exists():
            return f
    return None


def load_beats(project):
    p = project / "assets" / "beats.yaml"
    if not p.exists():
        return {"version": 1, "beats": []}
    return yaml.safe_load(p.read_text())


def save_beats(project, data):
    p = project / "assets" / "beats.yaml"
    backup = project / "assets" / f"beats.yaml.bak-{int(time.time())}"
    if p.exists():
        shutil.copy2(p, backup)
    # preserve yaml style as much as possible
    p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=1000))


def probe_duration(path):
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path)
        ]).decode().strip()
        return float(out)
    except Exception:
        return None


def range_response(handler, path):
    """Serve file with HTTP Range support for <video> scrubbing."""
    file_size = os.path.getsize(path)
    range_header = handler.headers.get("Range")
    ctype = "video/mp4"

    if range_header:
        m = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if not m:
            handler.send_error(416); return
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else file_size - 1
        end = min(end, file_size - 1)
        length = end - start + 1
        handler.send_response(206)
        handler.send_header("Content-Type", ctype)
        handler.send_header("Accept-Ranges", "bytes")
        handler.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        handler.send_header("Content-Length", str(length))
        handler.end_headers()
        with open(path, "rb") as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                try:
                    handler.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    return
                remaining -= len(chunk)
    else:
        handler.send_response(200)
        handler.send_header("Content-Type", ctype)
        handler.send_header("Accept-Ranges", "bytes")
        handler.send_header("Content-Length", str(file_size))
        handler.end_headers()
        with open(path, "rb") as f:
            shutil.copyfileobj(f, handler.wfile)


def run_render(project, only_ids):
    """Run render_beat.py --only and then composite.py. Stream logs to render_log."""
    with render_lock:
        render_log.clear()
        render_log.append(f"[{time.strftime('%H:%M:%S')}] starting render for beats: {only_ids or 'all'}")

        only_args = []
        if only_ids:
            only_args = ["--only", *[str(i) for i in only_ids]]

        cmd1 = [
            sys.executable, str(RENDER_SCRIPT), "all",
            "--beats", str(project / "assets" / "beats.yaml"),
            "--out-dir", str(project / "assets" / "beats-snapshots"),
            "--fps", "30",
            *only_args,
        ]
        render_log.append("$ " + " ".join(cmd1))
        try:
            p = subprocess.run(cmd1, capture_output=True, text=True, check=False)
            if p.stdout: render_log.extend(p.stdout.splitlines())
            if p.stderr: render_log.extend(p.stderr.splitlines())
            if p.returncode != 0:
                render_log.append(f"[render_beat FAILED rc={p.returncode}]")
                return
        except Exception as e:
            render_log.append(f"[render_beat exception] {e}")
            return

        cmd2 = [
            sys.executable, str(COMPOSITE_SCRIPT),
            "--raw", str(project / "assets" / "raw.mp4"),
            "--beats", str(project / "assets" / "beats.yaml"),
            "--snapshots-dir", str(project / "assets" / "beats-snapshots"),
            "--out-dir", str(project / "renders"),
        ]
        if only_ids:
            prev = latest_final(project)
            if prev:
                cmd2 += ["--beats-filter", ",".join(str(i) for i in only_ids),
                         "--base-from", prev.parent.name]
        render_log.append("$ " + " ".join(cmd2))
        try:
            p = subprocess.run(cmd2, capture_output=True, text=True, check=False)
            if p.stdout: render_log.extend(p.stdout.splitlines())
            if p.stderr: render_log.extend(p.stderr.splitlines())
            if p.returncode != 0:
                render_log.append(f"[composite FAILED rc={p.returncode}]")
                return
            render_log.append(f"[done] {time.strftime('%H:%M:%S')}")
        except Exception as e:
            render_log.append(f"[composite exception] {e}")


def make_handler(project):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            return  # quiet

        def _json(self, code, body):
            data = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            u = urlparse(self.path)
            path = u.path
            if path == "/" or path == "/index.html":
                if not EDITOR_HTML.exists():
                    self.send_error(500, "editor/index.html not found"); return
                data = EDITOR_HTML.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)
                return

            if path == "/api/state":
                with state_lock:
                    beats = load_beats(project)
                raw = project / "assets" / "raw.mp4"
                final = latest_final(project)
                self._json(200, {
                    "beats": beats.get("beats", []),
                    "version": beats.get("version", 1),
                    "videos": {
                        "raw": "/media/raw.mp4" if raw.exists() else None,
                        "final": "/media/final.mp4" if final else None,
                        "finalVersion": final.parent.name if final else None,
                    },
                    "duration": probe_duration(raw) if raw.exists() else None,
                })
                return

            if path == "/api/render/log":
                with render_lock:
                    self._json(200, {"log": list(render_log)})
                return

            if path == "/media/raw.mp4":
                f = project / "assets" / "raw.mp4"
                if not f.exists(): self.send_error(404); return
                range_response(self, f); return

            if path == "/media/final.mp4":
                f = latest_final(project)
                if not f: self.send_error(404); return
                range_response(self, f); return

            self.send_error(404)

        def do_POST(self):
            u = urlparse(self.path)
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b""

            if u.path == "/api/beats":
                try:
                    data = json.loads(body)
                    if "beats" not in data or not isinstance(data["beats"], list):
                        raise ValueError("missing beats[]")
                    with state_lock:
                        save_beats(project, {"version": data.get("version", 1), "beats": data["beats"]})
                    self._json(200, {"ok": True})
                except Exception as e:
                    self._json(400, {"error": str(e)})
                return

            if u.path == "/api/render":
                try:
                    data = json.loads(body) if body else {}
                    only_ids = data.get("only") or []
                    # run in background thread so POST returns fast
                    t = threading.Thread(target=run_render, args=(project, only_ids), daemon=True)
                    t.start()
                    self._json(200, {"ok": True, "started": True})
                except Exception as e:
                    self._json(400, {"error": str(e)})
                return

            self.send_error(404)

    return Handler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", help="path to video project dir")
    ap.add_argument("--port", type=int, default=7878)
    ap.add_argument("--open", action="store_true")
    args = ap.parse_args()

    project = pathlib.Path(args.project).resolve()
    if not (project / "assets" / "beats.yaml").exists():
        print(f"error: {project}/assets/beats.yaml not found", file=sys.stderr); sys.exit(1)

    handler = make_handler(project)
    class TS(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True
    httpd = TS(("127.0.0.1", args.port), handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"[editor] serving {project.name} at {url}")
    if args.open:
        try:
            subprocess.run(["open", url], check=False)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[editor] shutting down")


if __name__ == "__main__":
    main()
