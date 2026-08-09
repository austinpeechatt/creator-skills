# Creator Skills for Claude Code

Seven Claude Code skills that run a YouTube channel: idea capture, diagrams,
editing, shorts, carousels, thumbnails, and scheduling.

These are the actual skills behind [@austinpeechatt](https://www.youtube.com/@austinpeechatt) —
not a demo repo. They're published as-is so you can read them, run them, and
rip out the parts you want.

## The pipeline

```
idea  →  diagram  →  record  →  edit  →  clip  →  repurpose  →  package  →  publish
  │         │                    │        │          │            │           │
notion-  excalidraw-          video-  finish-   graphic-     youtube-    buffer-
 brain     diagram            editor   shorts   carousel    thumbnail  scheduler
```

| Skill | What it does |
|---|---|
| [`notion-brain`](skills/notion-brain) | Ramble at it, get a structured video idea in a Notion database. Ideas die when they don't have a home. |
| [`excalidraw-diagram`](skills/excalidraw-diagram) | Generates editable Excalidraw diagrams from a prompt. Ask for eight concepts, delete six — recognising the right one is faster than describing it. |
| [`video-editor`](skills/video-editor) | Transcribes a talking-head take, cuts filler and dead air, then places motion-graphic overlays on exact phrases. Knows when you're on camera versus sharing a screen, and never covers your face. |
| [`finish-shorts`](skills/finish-shorts) | Takes a finished long-form and batches out vertical shorts — picks the moments, plans the graphics, renders each one. |
| [`graphic-carousel`](skills/graphic-carousel) | Turns a topic or a video into a designed Instagram carousel — three house styles, brand palette and voice baked in, exported as post-ready 1080×1350 PNGs. Needs [open-carrusel](https://github.com/FrancescoXX/open-carrusel) for rendering. |
| [`youtube-thumbnail`](skills/youtube-thumbnail) | Four thumbnail directions per run, plus a comparison grid. Built around style references rather than from scratch. |
| [`buffer-scheduler`](skills/buffer-scheduler) | Schedules shorts to YouTube, Instagram and TikTok through Buffer, and health-checks the queue so failures don't sit unnoticed. |

## Install

Skills live in a `skills/` folder that Claude Code reads. Drop in the whole set:

```bash
git clone https://github.com/austinpeechatt/creator-skills.git
mkdir -p ~/.claude/skills
cp -R creator-skills/skills/* ~/.claude/skills/
```

Or per project, in `.claude/skills/` inside the repo you're working in.

Then copy the env template for any skill you plan to use:

```bash
cd ~/.claude/skills/notion-brain
cp .env.example .env      # then fill it in
```

## What you'll need

Nothing here needs all of it — set up only the skills you want.

| Skill | Requires |
|---|---|
| `notion-brain` | Notion integration token + a database, shared with the integration |
| `excalidraw-diagram` | Python 3, Playwright (for PNG rendering) |
| `video-editor` | Python 3, FFmpeg, Playwright, an ElevenLabs key for Scribe |
| `finish-shorts` | Same as `video-editor` |
| `graphic-carousel` | Node 18+, Python 3, and a local [open-carrusel](https://github.com/FrancescoXX/open-carrusel) checkout — it does the rendering and PNG export |
| `youtube-thumbnail` | Python 3, a Google AI Studio key. Renders cost about 4 cents each. |
| `buffer-scheduler` | Node 18+, a Buffer account, and somewhere permanent to host video |

## Honest notes

**Thumbnails don't nail your face.** Image models still can't reproduce a
specific person reliably. Treat the generated face as a layout placeholder and
composite your real photo in afterwards. Judge these on composition, type and
colour. Keeping the person description in your prompt *short* helps
measurably — long descriptions of facial features push the model toward a
generic face.

**Buffer re-fetches media at publish time.** A post scheduled for next week
downloads its video next week. Temporary file hosts expire and your post fails
quietly. Host somewhere permanent. This bites `graphic-carousel` specifically:
its upload path still targets catbox.moe, which Buffer began rejecting in July
2026. Repoint it at hosting you control before using the posting phase —
generating and exporting slides is unaffected.

**The carousel skill is brand-locked to mine.** Palette, fonts and logo marks
are AI Waterside's. The three styles are the reusable part; swap the palette
constants at the top of `seed_graphic_carousel.py` and the files in `assets/`
for your own. It also doesn't render slides itself — it drives
[open-carrusel](https://github.com/FrancescoXX/open-carrusel), which you'll need
running locally.

**Transcription uses two different tools on purpose.** A local Whisper build
(`brew install whisper-cpp`) is fine for a fast transcript. The video editor
uses ElevenLabs Scribe because it returns *word-level* timestamps, and that
granularity is what lets it cut filler precisely and land graphics on the right
phrase.

**The diagram skill defaults to eight concepts, not one.** That feels wasteful
and isn't. Six get deleted every time — that's the mechanism, not a failure of
it.

## Credit

The `youtube-thumbnail` skill was built by
[Tyler Germain](https://twitter.com/itstylergermain) at Friday Labs. That credit
line stays in the skill file.

## License

MIT. Use them, change them, ship them in your own stack.
