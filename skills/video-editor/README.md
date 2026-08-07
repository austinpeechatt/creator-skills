# /video-editor

Auto-generate AI Waterside-branded motion graphics overlays for a pre-trimmed talking-head video.

## Dependencies

- Python 3.9+ with `pyyaml`, `playwright`, `python-dotenv`, `requests`
- Playwright Chromium: `python -m playwright install chromium`
- FFmpeg on PATH
- `ELEVENLABS_API_KEY` in `~/.claude/.env` (Scribe access)

Install:
```bash
pip install pyyaml playwright python-dotenv requests
python -m playwright install chromium
```

## Usage

```
/video-editor <path/to/raw.mp4>
```

The skill expects `raw.mp4` to already be trimmed to final length. It will:

1. Extract audio (skip if `audio.mp3` exists next to raw.mp4)
2. Transcribe to word-level timestamps via ElevenLabs Scribe
3. Produce `beats-context.md` — the token-efficient planning input
4. Author `beats.yaml` (10–14 beats, 25–35s average spacing)
5. Present plan for your approval, apply any edits
6. Render PNG sequences per beat (Playwright headless Chromium)
7. Composite via FFmpeg → `renders/vN/final.mp4`

## Project layout

```
video-projects/<slug>/
├── assets/
│   ├── raw.mp4
│   ├── audio.mp3
│   ├── transcript.json
│   ├── beats-context.md
│   ├── beats.yaml
│   └── beats-snapshots/beat_NN/frame_*.png
├── brand/
│   ├── brand.json     (optional)
│   └── logo.png       (optional, used by end-card)
└── renders/vN/final.mp4
```

## Scene templates

7 templates — see `SKILL.md` for full prop schemas:

- `stat-callout` — big number + label
- `text-callout` — karaoke-synced phrase
- `list-build` — checklist items appearing in sync
- `quote-card` — pulled quote on dark glass
- `code-beat` — terminal-style progress rows
- `comparison` — before/after cards
- `end-card` — logo + CTA

Every template supports two layouts:
- **Layout A** — face-center full-frame + floating card(s) on left/right
- **Layout B** — face-PIP bottom-right + large full-stage content

## Adding a new scene template

1. Create `scene-library/<name>.html` that:
   - Loads `../brand/tokens.css`
   - Reads `window.__PROPS__` (injected by render_beat.py)
   - Sets `window.__READY__ = true` after fonts load
   - Honors `layout` (A or B) and optional `side` (left/right)
2. Add the template name to `TEMPLATES` in `scripts/render_beat.py`.
3. Document the prop schema in `SKILL.md`.

## Re-render only changed beats

```bash
python scripts/render_beat.py all --beats ... --out-dir ... --only 3 7
python scripts/composite.py --beats-filter 3,7 --base-from v1 ...
```
