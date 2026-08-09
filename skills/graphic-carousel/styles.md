# graphic-carousel — design system reference

Three AIW-branded styles, each a `render_X(slide, idx, eff_idx)` function in `scripts/seed_graphic_carousel.py`. All output body-level HTML at 1080×1350 with inline styles, on the **AI Waterside palette** (full spec: [brand/design-system.md](brand/design-system.md), visual board: [brand/design-system.html](brand/design-system.html)).

Fonts are Google Fonts referenced by family name (open-carrusel auto-inlines them on export — family names must be **unquoted before a comma**; the seed script normalizes this). Fonts: **Space Grotesk** (display), **Inter** (body), **JetBrains Mono** (labels + counter).

Palette tokens: `PALE #b5d0f4` · `OFFWHITE #f9f8fd` · `BLUE_LIGHT #8baeeb` · `BLUE_MID #618de2` · `BLUE #386cda` (primary accent) · `INK #0d1b3d` (navy).

All three share: the `BLUE` accent, a minimal `01 / 05` mono counter (top-right), and the **AIW logo mark bottom-right** (white on dark panels, blue on light — always present per Austin's rule; files `assets/aiw-logo-{white,blue}.png`, served from open-carrusel `public/uploads/`). **No beat-label strip.**

Visual elements (to keep the eye moving): `who` slides render **icon cards** (inline SVG: building/cart/briefcase/cloud), `system` slides render a **numbered node-rail** in B/C (connected circles), and covers/CTAs carry a small **AIW wave motif** under the headline.

---

## Style A — Blueprint

- **Look:** `PALE` background with a subtle navy CSS grid texture, `INK` text, `BLUE` accents (short rule under headings, blue numerals/arrows/keyword pill). Technical blueprint feel echoing the AIW reference illustration.
- **Type:** Space Grotesk 700 headlines/stat, Inter body, JetBrains Mono kicker + counter.
- **Sizes:** cover hero 104px · heading 72px · proof stat 200px (blue) · body 36–38px.
- **Best for:** systems/technical takes, "how it works" breakdowns.

## Style B — Bold block

- **Look:** full-bleed color-blocked panels rotating `[BLUE, OFFWHITE, INK]` by slide index; text auto-contrasts (off-white on blue/ink, navy on off-white); accent flips per panel (`OFFWHITE`/`BLUE`/`BLUE_LIGHT`). Punchy, high-contrast.
- **Type:** giant Space Grotesk 700 display, Inter body, mono counter.
- **Sizes:** cover hero 150px · heading 110px · proof stat 240px.
- **Rule:** `hero` should be short (≤~24 chars) — it wraps at 150px; longer phrases get tall.
- **Best for:** bold hooks, contrarian one-liners, big stats.

## Style C — Editorial clean

- **Look:** `OFFWHITE` background, `INK` text, centered, lots of whitespace, one idea per slide. `BLUE` underline accent (90px rule under headlines) + blue highlight on keywords. Calm, premium.
- **Type:** Space Grotesk 600 headlines, Inter body (muted `#54618a`), mono counter.
- **Sizes:** cover headline 88px · heading 72px · proof stat 200px (blue) · body 34px.
- **Note:** problem/system lists are left-aligned inside a centered max-width block so multi-line items read cleanly.
- **Best for:** thoughtful/principle pieces, essays, founder POV.

---

## Slide types (all styles)

| type | fields | renders |
|---|---|---|
| `cover` | `hero`, `subline`, `kicker`(opt) | hero headline + wave motif + subline |
| `problem` | `heading`, `items[]`, `kicker`(opt) | heading + arrow list |
| `system` | `heading`, `steps[]`, `kicker`(opt) | A: numbered list · B/C: numbered node-rail diagram |
| `who` | `heading`, `items[]` (≤4), `kicker`(opt) | heading + 2×2 icon cards (agencies/e-com/services/SaaS) |
| `proof` | `stat`, `statlabel`, `checks[]`, `kicker`(opt) | big stat + checkmark outcomes (use only with a real stat) |
| `cta` | `heading`, `keyword`, `handle` | heading + wave + comment-keyword CTA + follow |
| `image` | `heading`, `image`, `body`(opt), `footer`(opt), `kicker`(opt) | **Blueprint-only** — top-anchored heading + big white rounded card framing an uploaded diagram/screenshot + mono footer line bottom-left |
| `cta_image` | `heading`, `image`, `body`(opt), `footer`(opt) | **Blueprint-only** closer — heading + wave + body + framed image card (e.g. product/landing screenshot) |

`who` icons map to items by index: `building, cart, briefcase, saas`. For the AIW pinned-post arc use **cover → problem → system → who → cta** (proof is optional and needs a real number).

`image`/`cta_image` always render in Style A regardless of the carousel style — only `render_A` implements them. `image` = a bare filename that must already exist in open-carrusel's `public/uploads/` (copy it there before seeding). Build custom pure-visual graphics for concept slides and use real screenshots only for tool-showcase slides.

Shared config keys: `style` (`A`/`B`/`C`/`auto`/`mix`), `caption`, `hashtags`. Per-slide `style` override enables `style:"mix"`. Optional per-slide `kicker` = a small mono label — keep it **content-flavored** (e.g. `THE REALITY`, `THE PROCESS`), not the old psychological beat names.

## Tuning tips
- Overflowing Bold-block hero → shorten the word/phrase or drop the font-size in `render_B` cover.
- New palette → edit the palette constants block at the top of the seed script (mirror [brand/design-system.md](brand/design-system.md)).
- The `BLUE` accent is shared across A/B/C on purpose — keep it so mixed carousels stay coherent.
