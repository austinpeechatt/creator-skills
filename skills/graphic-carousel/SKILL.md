---
name: graphic-carousel
description: Use when Austin wants a premium graphic-design Instagram carousel — "make a graphic carousel", "design carousel", "make a blueprint/bold/editorial carousel for IG", or to turn a topic, thought, or YouTube summary into a designed multi-slide post. Designs use the AI Waterside brand palette. Generates designed slides in the local open-carrusel app and opens it for review/export.
argument-hint: <topic, raw thought, or YouTube-summary title/URL>
disable-model-invocation: true
---

## What This Skill Does

Turns a topic / thought / YouTube-summary into a **premium graphic-design carousel** — clean, modern, brand-consistent, rendered as 1080×1350 PNGs. Slides are authored as styled HTML, seeded into the local **open-carrusel** app via API, opened for review, exported as PNGs, and (Phase 2, opt-in) posted via Buffer.

### You need open-carrusel

This skill does not render slides itself — it authors HTML and seeds it into
[open-carrusel](https://github.com/FrancescoXX/open-carrusel), a local Next.js carousel
builder, then uses that app's export endpoint to get PNGs. Clone it somewhere and set
`OPEN_CARRUSEL_DIR` in `.env` to its path. Without it, nothing in the workflow below runs.

The split is deliberate: the app owns rendering and preview, this skill owns the design
system and the copy.

> **Not for video-repurpose decks.** The A/B/C card styles below are built for topic and
> brand decks. A carousel repurposing a long-form video wants full-canvas showpiece
> slides — every slide filled edge to edge, real logos in the flows, real artifacts —
> which is a different renderer, not a variation on these three.

## Brand palette (AI Waterside)

`PALE #b5d0f4` · `OFFWHITE #f9f8fd` · `BLUE_LIGHT #8baeeb` · `BLUE_MID #618de2` · `BLUE #386cda` (primary accent) · `INK #0d1b3d` (navy). Fonts: Space Grotesk (display), Inter (body), JetBrains Mono (labels/counter). Full spec: [brand/design-system.md](brand/design-system.md); visual board: [brand/design-system.html](brand/design-system.html).

## Three styles (auto-picked, override or mix)

Defined in `scripts/seed_graphic_carousel.py` as `render_A/B/C`. Full reference in [styles.md](styles.md). All three share the `BLUE` accent + a minimal `01 / 05` mono counter (top-right). **No beat-label strip.**

- **A — Blueprint:** pale-blue bg + subtle navy grid, Space Grotesk headlines, blue accents/numerals. Technical blueprint feel. Best for systems/technical breakdowns.
- **B — Bold block:** full-bleed color-blocked panels (blue/off-white/navy), auto-contrasting text, giant display type. Best for punchy hooks, big stats, contrarian one-liners.
- **C — Editorial clean:** off-white, centered, lots of whitespace, blue underline accent. Best for thoughtful/principle pieces, founder POV.

**Style selection (default = auto-pick + explain):** Claude reads the topic tone, picks the best-fit style, states the pick + a one-line reason in the handoff, and the user can override. If the user names a style ("make it blueprint / bold / editorial"), use it. Set `style:"mix"` to vary per slide (each slide may carry its own `style`); the shared `BLUE` accent keeps mixes coherent — mixing is off by default.

## Content framework (internal — not rendered)

Author copy in Austin's voice (direct, technical authority, AI-automation focus; never generic). Use this arc to **structure** the deck — but the beat names are NOT shown on the slides (only the `01 / 05` counter is):

| Beat | `type` |
|---|---|
| Hook | `cover` |
| Problem | `problem` |
| System | `system` |
| Proof | `proof` |
| CTA | `cta` |

Optional per-slide `kicker` = a small mono label; keep it content-flavored (e.g. `THE REALITY`, `THE PROCESS`), never the psychological beat names.

Extra slides = more `problem`/`system`/`proof`. **Never fabricate the proof stat** — it must trace to the source.

## Workflow

1. **Get the source** from `$ARGUMENTS` (topic / thought; or fetch a YouTube summary from a Notion summaries DB via direct API — set `NOTION_API_KEY` and `NOTION_SUMMARIES_DB_ID` in `.env`. Optional; skip it and just pass a topic).
2. **Pick the style** (auto), or honor a named style. Decide slide count (5 default).
3. **Ensure open-carrusel is running:** `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000` → if not 200, `cd "$OPEN_CARRUSEL_DIR" && PORT=3000 npm run dev > /tmp/open-carrusel-dev.log 2>&1 &`, poll to 200.
4. **Write the config JSON** to `/tmp/gc_config.json` (shape below), authoring the slide copy.
6. **Seed:** `cd "$OPEN_CARRUSEL_DIR" && python3 <path-to-this-skill>/scripts/seed_graphic_carousel.py /tmp/gc_config.json` → capture `CAROUSEL_URL:`.
7. **Open + verify:** `open "<url>"`. Strongly recommended: also `POST /api/carousels/<id>/export` → unzip → Read 1–2 slide PNGs to visually confirm before handing off (fonts/overflow). Your eyes are the final check, not the model's.
8. **Hand off:** summarize the style pick + arc; note it can be tweaked via the app chat or re-run with an edited config, and Export gives post-ready PNGs.
9. **(Phase 2 — only on an explicit "post it" / "schedule it")** `scripts/post_to_buffer.js --images <export dir> --config <gc.json> [--now | --at "YYYY-MM-DD HH:MM"] [--dry-run]`. Hosts each `slide-*.png`, then creates the Buffer post. **Always `--dry-run` first** to confirm caption + slide order; NEVER auto-post on a normal generate run. Read the image-hosting warning under Notes before using this. Confirm timing before firing — it's outward and irreversible.

## Config JSON shape

```json
{
  "name": "...", "aspectRatio": "4:5",
  "style": "A|B|C|auto|mix",
  "caption": "<short casual IG caption, max 3 hashtags>", "hashtags": ["aiautomation","..."],
  "slides": [
    {"type":"cover","kicker":"AI AUTOMATION AGENCY","hero":"99% can't implement AI.","subline":"..."},
    {"type":"problem","kicker":"THE GAP","heading":"Why it stalls","items":["...","..."]},
    {"type":"system","kicker":"WHAT WE DO","heading":"How we fix it","steps":["...","..."]},
    {"type":"who","kicker":"WHO IT'S FOR","heading":"Who it's for","items":["Agencies","E-commerce brands","Professional services","SaaS & startups"]},
    {"type":"image","kicker":"THE SHIFT","heading":"Buyers ask AI first now","body":"Search didn't die — it moved.","image":"diag-market-shift.png","footer":"aiwaterside.com"},
    {"type":"cta_image","heading":"See the full breakdown.","body":"Comment WAVE and I'll send it over.","image":"landing-shot.png","footer":"@austinpeechatt"},
    {"type":"cta","heading":"See if AIW can help.","keyword":"WAVE","handle":"@austinpeechatt"}
  ]
}
```
Field notes: `hero` (cover) = a short headline — **keep it short for Style B** (≤~24 chars, it wraps at 150px); `kicker` (optional, all types) = small mono label, content-flavored not beat-name; `who.items` ≤4 (icons map by index: building/cart/briefcase/saas); `keyword` = comment-to-DM keyword; any slide may add `"style":"A|B|C"` (used with `style:"mix"`).

**Framed-image slides (`image` / `cta_image`):** kicker/heading/short body + a big white rounded card holding a diagram or screenshot + optional mono footer line. Always render in Style A (Blueprint) regardless of carousel style. `image` = bare filename — **copy the PNG into `$OPEN_CARRUSEL_DIR/public/uploads/` before seeding**. Build a custom pure-visual graphic per *concept* slide (Playwright HTML→PNG); use real screenshots only for tool-showcase slides; never crop a dense diagram down into a card — it becomes unreadable at phone size.

**Default arc for an AIW pinned/intro post:** `cover → problem → system → who → cta` (what · why · how · who · CTA). The AIW logo mark auto-renders bottom-right on every slide; covers/CTAs get a wave motif; `who` renders icon cards; `system` renders a node-rail in B/C. Use `proof` only when there's a **real** stat.

## Notes / guardrails

- **Don't re-author the card markup** — the 3 style generators own all CSS. Author only the config (copy + structure). To change a style's look, edit `render_A/B/C` in the seed script (and [styles.md](styles.md)).
- **Font gotcha (already handled):** open-carrusel's font extractor fails on quoted family names before a comma; the seed script normalizes `font-family:'X'` → unquoted before posting so Space Grotesk / Inter / JetBrains Mono inline on export. Keep that `re.sub` if editing.
- **Keep the Bold-block (B) hero short** (≤~24 chars) — it renders at 150px and wraps; long phrases get tall. Blueprint/Editorial heroes tolerate full headlines.
- **Python 3.9 compatible:** the seed script avoids nested-quote/backslash f-strings (build sub-strings into a variable first). Keep it that way.
- **Cap 10 slides** (open-carrusel max); 5–8 is the sweet spot.
- **Posting (Phase 2, opt-in):** `.env` holds `BUFFER_ACCESS_TOKEN` + `BUFFER_IG_CHANNEL` (your own Instagram channel id — Buffer accounts usually have several, so double-check you grabbed the right one). `post_to_buffer.js` handles image hosting + the Buffer `createPost` mutation.
- ⚠ **Known issue — the image host in `post_to_buffer.js` is dead.** It uploads to catbox.moe, and Buffer began rejecting catbox URLs in July 2026. Buffer also re-fetches media at *publish* time, not at schedule time, so whatever you swap in has to still be live on the post's actual publish date — a temporary file host will fail quietly days later. Point `upload()` at permanent hosting you control (S3, a static site, anything with a stable URL) before using Phase 2. Generating and exporting slides is unaffected.
- Uses the AI Waterside brand palette throughout. Swap the palette constants at the top of `seed_graphic_carousel.py` and the marks in `assets/` for your own brand.
