#!/usr/bin/env python3
"""
Composite beat PNG sequences onto the base video with FFmpeg.

Usage:
  composite.py \
    --raw video-projects/foo/assets/raw.mp4 \
    --beats video-projects/foo/assets/beats.yaml \
    --snapshots-dir video-projects/foo/assets/beats-snapshots \
    --out-dir video-projects/foo/renders \
    [--version v1] [--fps 30] [--width 1920] [--height 1080] \
    [--beats-filter 3,7] [--base-from v2]

The script scales the base video to width×height, then overlays each
beat's PNG sequence (RGBA frames) onto the base with an enable window
matching beat.start → beat.end, and uses the raw video's audio unchanged.

If --base-from is passed, the previous render's final.mp4 is used as the
base instead of the raw video (useful when re-rendering only specific beats).
"""
import argparse, os, pathlib, subprocess, sys
import yaml

def next_version(out_root):
    out_root = pathlib.Path(out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    n = 1
    while (out_root / f"v{n}").exists():
        n += 1
    return f"v{n}"

def parse_filter(s):
    if not s: return None
    return set(int(x.strip()) for x in s.split(",") if x.strip())

def build_filter_complex(beats, width, height, fps, n_inputs_offset=1, tail_hold=0.0):
    """Return (filter_str, last_label). Base is [0:v], overlays are [1:v]..[n:v].
    If tail_hold > 0, the base video holds its last frame for that many seconds
    (via tpad=stop_mode=clone) so overlays can extend past raw duration."""
    tail_clause = f",tpad=stop_mode=clone:stop_duration={tail_hold}" if tail_hold > 0 else ""
    parts = [f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
             f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}{tail_clause}[base]"]
    prev = "base"
    for i, b in enumerate(beats):
        stream_idx = n_inputs_offset + i
        start = float(b["start"]); end = float(b["end"])
        # PNG sequence is already 1920x1080 RGBA but we scale defensively
        parts.append(f"[{stream_idx}:v]scale={width}:{height},format=rgba,setpts=PTS-STARTPTS+{start}/TB[ov{i}]")
        nxt = f"v{i}"
        parts.append(f"[{prev}][ov{i}]overlay=enable='between(t,{start},{end})':x=0:y=0:shortest=0[{nxt}]")
        prev = nxt
    return ";".join(parts), prev

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--beats", required=True)
    ap.add_argument("--snapshots-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--version", default=None)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--width",  type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--beats-filter", default=None,
                    help="comma-separated beat ids to include (default: all)")
    ap.add_argument("--base-from", default=None,
                    help="version dir to use as base instead of raw (e.g. v1)")
    args = ap.parse_args()

    data = yaml.safe_load(pathlib.Path(args.beats).read_text())
    beats = data.get("beats", [])
    keep = parse_filter(args.beats_filter)
    if keep is not None:
        beats = [b for b in beats if int(b["id"]) in keep]
    if not beats:
        print("[composite] no beats to composite"); sys.exit(0)

    version = args.version or next_version(args.out_dir)
    out_dir = pathlib.Path(args.out_dir) / version
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "final.mp4"

    if args.base_from:
        base = pathlib.Path(args.out_dir) / args.base_from / "final.mp4"
        if not base.exists():
            print(f"[composite] base video not found: {base}"); sys.exit(1)
    else:
        base = pathlib.Path(args.raw)

    cmd = ["ffmpeg", "-y", "-i", str(base)]
    snaps = pathlib.Path(args.snapshots_dir)
    for b in beats:
        bid = int(b["id"])
        seq = snaps / f"beat_{bid:02d}" / "frame_%05d.png"
        if not (snaps / f"beat_{bid:02d}").exists():
            print(f"[composite] missing snapshots for beat {bid}: {seq.parent}"); sys.exit(1)
        cmd += ["-framerate", str(args.fps), "-i", str(seq)]

    # Detect base video duration so we can hold the last frame for any beats
    # that extend past it (e.g. end-card stays on screen after audio ends).
    try:
        base_dur = float(subprocess.check_output([
            "ffprobe","-v","error","-show_entries","format=duration",
            "-of","default=noprint_wrappers=1:nokey=1", str(base)
        ]).decode().strip())
    except Exception:
        base_dur = None
    max_end = max(float(b["end"]) for b in beats)
    tail_hold = 0.0
    if base_dur is not None and max_end > base_dur:
        tail_hold = max_end - base_dur + 0.2  # small pad

    fc, last = build_filter_complex(beats, args.width, args.height, args.fps, tail_hold=tail_hold)
    cmd += [
        "-filter_complex", fc,
        "-map", f"[{last}]",
        "-map", "0:a?",
    ]
    if tail_hold > 0:
        # hold audio silent for the same duration so streams stay aligned
        cmd += ["-af", f"apad=pad_dur={tail_hold}"]
    cmd += [
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        "-shortest",
        str(out_path),
    ]
    print("[composite] running ffmpeg...")
    print("  " + " ".join(cmd[:8]) + f" ... (+{len(beats)} beat inputs)")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print("[composite] ffmpeg failed"); sys.exit(r.returncode)
    print(f"[composite] wrote {out_path}")

if __name__ == "__main__":
    main()
