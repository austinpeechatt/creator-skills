# AI Waterside — Design System

Single source of truth for the AIW brand look used across `/graphic-carousel`. The seed script's palette/font constants mirror this file. Visual board: [design-system.html](design-system.html) (open in a browser).

---

## Colors

| Token | Hex | Usage |
|---|---|---|
| `PALE` | `#b5d0f4` | Blueprint background, light tints |
| `OFFWHITE` | `#f9f8fd` | Editorial background, light panels, text on dark |
| `BLUE_LIGHT` | `#8baeeb` | soft fills, secondary tints |
| `BLUE_MID` | `#618de2` | secondary accent, gradients |
| `BLUE` | `#386cda` | **primary** — accents, fills, highlights, active states |
| `INK` | `#0d1b3d` | deep navy — body text, line work, dark panels |

Contrast rules: navy `INK` on light (`PALE`/`OFFWHITE`), `OFFWHITE` on `BLUE`/`INK`. Primary `BLUE` is the one accent that carries across all styles — keep it consistent so mixed decks stay coherent.

## Typography

- **Display / headlines:** `Space Grotesk` (600–700) — geometric, modern, AI-native.
- **Body:** `Inter` (400–600) — clean, legible.
- **Labels / counter:** `JetBrains Mono` (400–500) — the `01 / 05` counter and small uppercase labels.

Type scale (carousel, 1080×1350): hero 180–200px · section heading 96–120px · proof stat 220–260px · body 34–40px · label/counter 22–26px. Tight tracking on display (`-0.02em`), generous line-height on body (1.4).

All families are Google Fonts, auto-inlined by open-carrusel on export — **family names must be unquoted before a comma** (`font-family:Space Grotesk,sans-serif`). The seed script normalizes `font-family:'X'` → unquoted via `re.sub`; keep it.

## Spacing

Base unit 8px. Scale: `4 / 8 / 16 / 24 / 40 / 80px`. Slide padding 80px (editorial 96px). Section gaps in multiples of 8.

## Components

- **Button / pill:** `BLUE` fill, `OFFWHITE` text, 8px radius, Space Grotesk 600. (Squared-modern, not fully rounded.)
- **Card / panel:** `OFFWHITE` or `INK` block, 16px radius optional, generous internal padding.
- **Mono label:** `JetBrains Mono`, uppercase, `0.12em` tracking, muted navy or `BLUE`.
- **Counter:** `01 / 05` in `JetBrains Mono`, corner-pinned, muted — the only orientation indicator (no beat strip).

---

## Carousel styles (the 3 graphic-carousel layouts)

1. **Blueprint** — `PALE` bg + subtle navy grid texture, `INK` ink, `BLUE` accents, Space Grotesk + mono labels. Line/grid motif. Best for systems/technical takes.
2. **Bold block** — color-blocked panels rotating `[BLUE, OFFWHITE, INK]`, auto-contrasting text, giant Space Grotesk display. Best for punchy hooks/proof.
3. **Editorial clean** — `OFFWHITE` bg, `INK` ink, whitespace, centered one-idea slides, `BLUE` underline/highlight accent. Best for thoughtful/principle pieces.

All three share the `BLUE` accent + the `01 / 05` mono counter. Edit the look in `render_A/B/C` in `scripts/seed_graphic_carousel.py`.
