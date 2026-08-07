#!/usr/bin/env python3
"""Transcribe audio via ElevenLabs Scribe with word-level timestamps. Skips if output exists."""
import os, sys, json, pathlib
from dotenv import load_dotenv
import requests

def main():
    if len(sys.argv) != 3:
        print("Usage: transcribe.py <audio_in.mp3> <transcript_out.json>")
        sys.exit(2)
    audio_path, out_path = sys.argv[1], sys.argv[2]
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        print(f"[transcribe] exists, skipping → {out_path}")
        return

    load_dotenv(os.path.expanduser("~/.claude/.env"))
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not set in ~/.claude/.env")
        sys.exit(1)

    print(f"[transcribe] uploading {audio_path} → ElevenLabs Scribe...")
    with open(audio_path, "rb") as f:
        r = requests.post(
            "https://api.elevenlabs.io/v1/speech-to-text",
            headers={"xi-api-key": api_key},
            data={"model_id": "scribe_v1", "timestamps_granularity": "word"},
            files={"file": f},
            timeout=600,
        )
    if r.status_code != 200:
        print(f"ERROR {r.status_code}: {r.text[:600]}")
        sys.exit(1)
    data = r.json()
    pathlib.Path(os.path.dirname(out_path) or ".").mkdir(parents=True, exist_ok=True)
    pathlib.Path(out_path).write_text(json.dumps(data, indent=2))
    words = data.get("words", [])
    print(f"[transcribe] {len(words)} word tokens → {out_path}")

if __name__ == "__main__":
    main()
