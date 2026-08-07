---
name: video-editor
description: Auto-generate AI Waterside-branded motion graphics overlays for a pre-trimmed talking-head video, synced to word-level transcript timestamps. Pipeline is plan-first — Claude reads the transcript, authors a 10–14 beat plan, user approves in plan mode, then beats render to PNG sequences via Playwright and composite onto the raw video via FFmpeg. Triggers when the user runs `/video-editor <path/to/raw.mp4>` or asks to add motion graphics to a talking-head video.
---

# video-editor

Produce premium, brand-native motion graphics overlays for a pre-trimmed talking-head video. First-pass target: ~70% polish; iterate per-beat.

> **Routing:** If Austin wants a FINISHED long-form export taken all the way to a final render — overlays PLUS cutting ums/filler/dead-space, hands-off — use the **`finish-video`** skill (project-local) instead. It wraps this pipeline in a plan → one-approval → background-Opus-executor flow. Use this `video-editor` skill directly only for overlay-only work where Austin wants to iterate in the same session.

## Required inputs

- `$ARGUMENTS`: absolute or relative path to the raw video (must already be trimmed — do NOT split).

## Project layout

From the video path, derive the project root as `dirname(dirname(video_path))`. Expect (or create):

```
<project>/
├── assets/
│   ├── raw.mp4                  # the input (do not modify)
│   ├── audio.mp3                # produced if missing
│   ├── transcript.json          # produced if missing
│   ├── beats-context.md         # produced every run (planning input)
│   ├── beats.yaml               # the plan, user-editable
│   └── beats-snapshots/beat_NN/frame_*.png
├── brand/
│   ├── brand.json               # optional; overrides skill defaults
│   └── logo.png                 # optional; used by end-card
└── renders/vN/final.mp4
```

## Pipeline

> **4K NATIVE long-form?** (talking-head overlays on a finished YouTube export, e.g. 3840×2160 or other non-1080p source) — do NOT use the stock `render_beat.py` / `composite.py` below. They render at 1080p and animate on wall-clock, which downscales 4K and drifts at high resolution. Instead use the **deterministic 4K pipeline** in `output/geo-audit-v2/` (`render_scenes.py` + project-local scenes whose animation is a pure function of `window.__APPLY__(t_ms)`), adjusting `VIEW_W, VIEW_H, DSF` to the source resolution (16:9 4K = `1920, 1080, 2`; **vertical 9:16 4K shorts = `1080, 1920, 2`**). See memory `project_longform_overlay_pipeline` (3 confirmed reuses: GEO audit, skills-showcase, claydream short). The stock scene-library HTML is still a useful markup/CSS reference to port from. The rest of this doc (transcript → beat plan → preview gate → verify-from-MP4) still applies.
>
> **Vertical shorts specifically** — read `~/Documents/content/assets/notes/vertical-short-overlays.md` and `captions-and-title-cards.md` FIRST. They carry the reusable pieces: measuring what's already baked into the export before planning beats, the head/hand safe-zone scan, per-beat cropped canvases (`view` + `offset_y`, ~12× cheaper for the caption band), the approved caption + full-screen-title specs, and the converge/stitch animation. Copy-forward implementation lives at `~/Documents/content/short-form/clay-dream/overlay-work/`.

Execute the pipeline step-by-step. Stop and report clearly if any step fails.

### 1. Preflight

- Verify FFmpeg is on PATH (`ffmpeg -version`).
- Verify Playwright chromium is installed; if the first render fails, run `python -m playwright install chromium`.
- Verify `~/.claude/.env` contains `ELEVENLABS_API_KEY`.

### 2. Extract audio (skip if exists)

```bash
python ~/.claude/skills/video-editor/scripts/extract_audio.py \
  <project>/assets/raw.mp4 <project>/assets/audio.mp3
```

### 3. Transcribe (skip if exists)

```bash
python ~/.claude/skills/video-editor/scripts/transcribe.py \
  <project>/assets/audio.mp3 <project>/assets/transcript.json
```

### 4. Produce planning context

```bash
python ~/.claude/skills/video-editor/scripts/plan_beats.py \
  <project>/assets/transcript.json <project>/assets/beats-context.md
```

### 5. Author beats.yaml

Read `<project>/assets/beats-context.md`, `<project>/brand/brand.json` (if present), and the scene prop schemas below. Write `<project>/assets/beats.yaml` with **10–14 beats** for a ~5–6 minute video (roughly one every 25–35 seconds — premium/sparse, not dense).

**Authoring rules:**
- Every beat's `start`/`end` must fall on real word boundaries in the transcript.
- Minimum beat duration: 2.5s. Maximum: 8s. Prefer 3–5s.
- Don't stack beats on top of each other (no overlap).
- Mix templates — don't use the same one twice in a row.
- Mix layouts — roughly half layout A (face-center + floating cards), half layout B (face-PIP + full-stage) so the viewer's eye moves.
- Every beat must reinforce something Austin actually says at that timestamp. Include `rationale` quoting the line.
- First beat: not before 0:04. Last beat: reserve last 4–6s for `end-card` if this is a content piece that wraps up with a CTA.

### 6. Present plan and wait for approval

Use ExitPlanMode (plan mode) to show the user the beats.yaml contents as a readable table. Wait for approval or edits. Apply edits to `beats.yaml` before continuing.

### 7. Render beat PNG sequences

```bash
python ~/.claude/skills/video-editor/scripts/render_beat.py all \
  --beats <project>/assets/beats.yaml \
  --out-dir <project>/assets/beats-snapshots \
  --fps 30
```

If Playwright errors with "Executable doesn't exist", run `python -m playwright install chromium` once, then retry.

### 8. Spot-check frames

For each beat, Read the first PNG frame (`beats-snapshots/beat_NN/frame_00000.png`) and quickly verify it looks right (correct template, readable text, brand palette). If a beat looks broken, fix the beats.yaml props and re-render just that beat with `--only NN`.

### 9. Composite

```bash
python ~/.claude/skills/video-editor/scripts/composite.py \
  --raw <project>/assets/raw.mp4 \
  --beats <project>/assets/beats.yaml \
  --snapshots-dir <project>/assets/beats-snapshots \
  --out-dir <project>/renders
```

Output: `<project>/renders/vN/final.mp4` (1920×1080, H.264, original audio).

### 10. Report and offer iteration

Tell the user the output path. Offer:
- Timestamped feedback → edit beats.yaml → re-render only those beats:
  ```bash
  python .../render_beat.py all --beats ... --out-dir ... --only 3 7
  python .../composite.py --beats-filter 3,7 --base-from v1 ...
  ```

## Scene template prop schemas

All templates accept these universal props:
- `layout`: `"A"` (face-center + floating cards) or `"B"` (face-PIP bottom-right + full-stage)
- `side`: `"left"` or `"right"` (only for layout A — picks which side the card sits on)

### stat-callout
Big number + label card.
```yaml
props:
  eyebrow: "retention lift"     # optional, small uppercase above number
  number:  "+248%"
  label:   "customer retention"
  sub:     "after switching to AI-assisted outreach"   # optional
```

### text-callout
Karaoke-style phrase; words highlight in time with speech.
```yaml
props:
  # Either provide full words array with per-word timing (preferred):
  words:
    - {text: "Word", start_ms: 12300, end_ms: 12520}
    - {text: "by",   start_ms: 12520, end_ms: 12680, emph: true}
    - {text: "word.", start_ms: 12680, end_ms: 12980}
  # Or just `text:` and it will render without karaoke:
  text: "This changes everything."
```

### list-build
Checklist items appear one at a time.
```yaml
props:
  title: "What we automated"
  items:
    - {text: "Lead enrichment",   appear_ms: 0}
    - {text: "Outbound sequences", appear_ms: 900}
    - {text: "CRM hygiene",       appear_ms: 1800}
```
(appear_ms is offset from beat start.)

### quote-card
Full-screen (layout B) or side card (layout A).
```yaml
props:
  quote: "We hit payback in under 30 days."
  attribution: "Mia Chen, VP Growth"     # optional
```

### code-beat
Terminal-style rows; each row appears, then gets a green ✓.
```yaml
props:
  rows:
    - {cmd: "analyze_transcript.py", appear_ms: 0,    done_ms: 800}
    - {cmd: "cluster_insights.py",   appear_ms: 900,  done_ms: 1900}
    - {cmd: "publish_report.py",     appear_ms: 2000, done_ms: 3000}
```

### comparison
Before/after or A-vs-B.
```yaml
props:
  before_label: "Before"          # optional override
  after_label:  "After"
  before: {headline: "Manual QA, 4 hrs/day", detail: "2 analysts, inconsistent"}
  after:  {headline: "Automated QA, 6 min",  detail: "1 agent, 98% accuracy"}
```

### end-card
Logo + CTA. Logo renders at 240px tall.
```yaml
props:
  logo_src: "/abs/path/to/brand/logo.png"   # plain fs path, NOT file:// URL
  headline: "Let\u2019s build your AI automation."
  cta: "Book a call"
  url: "yourdomain.com"
```
Any beat whose `end` exceeds the raw video's duration will cause `composite.py` to tpad-hold the last frame + silent-pad the audio by `(max_end - raw_dur + 0.2)` seconds. Use this to let the end-card breathe past the last spoken word without modifying raw.mp4.

### dual-card
Two glass cards simultaneously (left + right) around the face. Staggered entry via `appear_ms`.
```yaml
props:
  left:
    eyebrow: "THE WORKFLOW"
    title: "Property"
    accent: "research by hand"      # rendered in gradient blue
    appear_ms: 0
  right:
    eyebrow: "THE COST"
    title: "~10 min"
    accent: "per deal"
    appear_ms: 2500
```

### subtitle-bar
Frosted bottom pill — reinforces a spoken punchline. Use `segments[]` to mix styles within one line.
```yaml
props:
  # plain form:
  text: "Zero manual research."
  # OR styled segments:
  segments:
    - {text: "Zero manual research.",  style: "normal"}
    - {text: "Instant summary.",       style: "hl"}   # hl | dim | normal
```

### feature-list
Dark full-stage (layout B) with eyebrow, big bold items, and glowing blue ✓ checks appearing one at a time.
```yaml
props:
  eyebrow: "THE PLAYBOOK"
  items:
    - {text: "Spot a manual task",        appear_ms: 0}
    - {text: "Hand it to Claude Cowork",  appear_ms: 700}
  footer: "repeat weekly"        # optional small uppercase footer
```

### process-flow
Dark full-stage (layout B) with eyebrow + up to 4 icon-node boxes connected by arrows. Nodes fade in in sequence.
```yaml
props:
  eyebrow: "HOW IT WORKS"
  nodes:
    - {icon: "&#9783;",  label: "SAVED SEARCH", appear_ms: 0}
    - {icon: "&#9993;",  label: "EMAIL ALERT",  appear_ms: 900}
    - {icon: "&#10022;", label: "AI ANALYSIS",  appear_ms: 1800}
```
`icon` accepts any HTML entity or emoji.

## Timeline editor (review UI)

For reviewing/iterating on beats visually instead of re-rendering blind:
```bash
python3 ~/.claude/skills/video-editor/scripts/editor_server.py <project_dir> --port 7878 --open
```
Opens a browser UI at `http://127.0.0.1:7878/`:
- Video player (toggle between `raw.mp4` and latest `final.mp4`)
- Timeline with color-coded beat blocks — drag to retime, edge-handle to resize
- Side panel: edit start/end, template, layout, side, and props JSON
- **save beats.yaml** (auto-backup `.bak-<timestamp>`)
- **re-render selected** — incremental via `--beats-filter <id> --base-from vN` (fast)
- **re-render all** — full pipeline
- Live render logs stream into the status panel; video auto-reloads when done

## Rules of thumb

- Don't over-pack. 10–14 beats for 5:45 is plenty. Silence between beats is a feature.
- Karaoke `text-callout` is powerful but expensive — use ≤3 per video.
- `end-card` always uses layout B (full-stage), ignores layout hint.
- If `brand/logo.png` is missing, `end-card` hides the image and shows only the wordmark — don't block on it.
