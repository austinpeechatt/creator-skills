#!/usr/bin/env python3
"""Extract mono 16kHz MP3 audio from a video via FFmpeg. Skips if output exists."""
import sys, os, subprocess, pathlib

def main():
    if len(sys.argv) != 3:
        print("Usage: extract_audio.py <video_in> <audio_out.mp3>")
        sys.exit(2)
    src, dst = sys.argv[1], sys.argv[2]
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        print(f"[extract_audio] exists, skipping → {dst}")
        return
    pathlib.Path(os.path.dirname(dst) or ".").mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-i", src, "-ac", "1", "-ar", "16000", "-vn", "-q:a", "4", dst]
    print("[extract_audio] " + " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-1200:])
        sys.exit(1)
    print(f"[extract_audio] wrote {dst}")

if __name__ == "__main__":
    main()
