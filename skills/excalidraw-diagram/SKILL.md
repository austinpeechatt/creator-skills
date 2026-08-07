---
name: excalidraw-diagram
description: Use when someone asks to draw a diagram, make an Excalidraw diagram, or build an editable diagram. Default for all diagram requests.
---

## Workflow

### Step 1: Understand the request
Before generating anything, make sure you know:
- What concept or system are they diagramming?
- What are the major components or sections?
- What is the flow or relationship between them?

If the request is vague (e.g., "make a diagram of Docker"), ask 1-2 clarifying questions:
- What specific aspect? (architecture, networking, volumes, etc.)
- What level of detail? (high-level overview vs. detailed internals)

### Step 2: Research if needed
If you're not confident about the technical accuracy of the concept, research it before diagramming. Verify:
- Correct component names and relationships
- Proper hierarchy and nesting
- Accurate data flow direction

### Step 3: Plan the layout
Before writing any JSON, sketch the layout mentally:
- What are the major sections? (left-to-right or top-to-bottom)
- What is nested inside what?
- What arrows connect what?

Write down the section plan:
```
[Section A: w=170] --40px gap-- [Section B: w=170] --40px gap-- [Section C: w=640]
```

### Step 4: Generate elements
Build elements in order:
1. Outer boxes / containers first
2. Section header text
3. Nested elements (top to bottom within each section)
4. Arrows and arrow labels last

### Step 5: Save and deliver
1. Save to `output/diagrams/[concept-slug].excalidraw` (default — whatever folder you open from Excalidraw.com). **Exception:** if the diagram is for a specific YouTube video, save it to that video's bundle instead — `~/Documents/content/long-form/<slug>/diagrams.excalidraw` (or `short-form/<slug>/`; active projects sit at the top level, `Archive/<slug>/` once shipped). Legacy locations: `content/projects/<slug>/` and the SSD.
2. Show the full JSON in a code block so the user can copy it directly
3. Briefly describe what the diagram shows and what each color zone represents
4. Tell the user how to use the file:

> **How to view and edit your diagram:**
> - Go to excalidraw.com (free, no account needed)
> - Option A: Click the menu (top-left hamburger icon) > "Open" > select the `.excalidraw` file
> - Option B: Copy the JSON code block above, open excalidraw.com, and paste it with Ctrl+V / Cmd+V
> - Every element is fully editable -- drag to move, grab handles to resize, double-click to edit text

### Step 6: Handle feedback
If the user asks for changes:
- Shifting an element = update x/y on that element + all elements that depend on it
- Changing text = update both `text` and `originalText` fields
- Adding a zone = assign it a new color from the palette, keep spacing consistent
- If a diagram gets complex (20+ elements), build it section by section to avoid coordinate errors

---

## Critical Rule: Text Contrast

Text inside colored shapes must be readable. Use `#1e1e1e` (near-black) or `#343a40` (dark charcoal) for all text inside filled shapes. Never use the zone's stroke color for text sitting on that zone's background (e.g., yellow text on a yellow card is unreadable). Reserve the zone's strokeColor for shape borders and arrows only.

---

## Design Principles

**Color tells the story:** One color per logical zone. Everything in the "input" zone is blue. Everything in the "output" zone is green. The viewer should understand structure before reading a word.

**Nesting shows containment:** If X lives inside Y, X's box is drawn inside Y's box with consistent padding. Coordinates are absolute, not relative: `child_x = parent_x + padding`.

**Labels are short:** 2-5 words per label. Longer explanations become annotations with smaller fontSize and muted color (`#868e96`).

**White space is structure:** 15px minimum gap between siblings. 40px minimum between major sections.

**Arrows carry intent:** Color arrows to match purpose. Label every non-obvious arrow.

---

## Layout System

Always plan coordinates before writing JSON.

1. Identify major sections (left-to-right or top-to-bottom)
2. Assign fixed width and starting x to each section
3. Calculate gaps: 40-60px between major sections, 15-25px between siblings
4. Work top-to-bottom within sections: `next_y = current_y + current_height + gap`

**Padding rules:**
- Outer box to inner label: 8-10px top offset
- Outer box to nested box: 10-15px offset on all sides
- Sibling elements: 10-15px gap

**Text width trick:** Set text width = parent box width. Text centers automatically when `textAlign: "center"`.

**Arrow labels:** Position as separate text elements, 20-25px above the arrow's midpoint y, with width and x matching the arrow.

**Coordinate math example:**
```
Section A: x=30,  w=170  -> right edge = 200
Gap:                        40px
Section B: x=240, w=170  -> right edge = 410
Gap:                        40px
Section C: x=450, w=600  -> right edge = 1050
```

---

## Color System

| Zone | Use for | strokeColor | backgroundColor |
|------|---------|-------------|-----------------|
| Blue | Input, source, external services | `#1971c2` | `#e7f5ff` |
| Yellow | Processing, transformation | `#f59f00` | `#fff9db` |
| Green | Output, containers, success | `#2f9e44` | `#d3f9d8` |
| Purple | Shared layers, infrastructure | `#862e9c` | `#f3d9fa` |
| Red | Host OS, warnings, errors | `#c92a2a` | `#ffe3e3` |
| Gray | Hardware, neutral containers | `#495057` | `#f8f9fa` |

For nested elements, vary the fill intensity:
- Outer: lightest (e.g., `#d3f9d8`)
- Inner: medium (e.g., `#8ce99a`)
- Deep inner: light-medium (e.g., `#b2f2bb`)

---

## Typography Scale

| Role | fontSize | fontFamily |
|------|----------|------------|
| Diagram title | 32-36 | 1 (Virgil) |
| Section header | 20-24 | 1 |
| Element label | 16-18 | 1 |
| Annotation | 14-15 | 1 |
| Small note | 12-13 | 1 |
| Code label | 14-16 | 3 (Cascadia) |

Text width = parent box width. Text x/y offset ~8-10px from box x/y for padding.

---

## Element Schema

Every element needs these base fields. Do not omit any.

### Base fields (all types)
```json
{
  "id": "unique-string",
  "type": "rectangle|ellipse|diamond|arrow|line|text|freedraw",
  "x": 0, "y": 0,
  "width": 100, "height": 50,
  "angle": 0,
  "strokeColor": "#1e1e1e",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 1,
  "opacity": 100,
  "groupIds": [],
  "frameId": null,
  "roundness": null,
  "boundElements": [],
  "updated": 1,
  "link": null,
  "locked": false
}
```

### Text fields (add to base)
```json
{
  "text": "Label text",
  "fontSize": 16,
  "fontFamily": 1,
  "textAlign": "center",
  "verticalAlign": "top",
  "containerId": null,
  "originalText": "Label text",
  "lineHeight": 1.25
}
```

### Arrow fields (add to base)
```json
{
  "points": [[0, 0], [100, 0]],
  "lastCommittedPoint": null,
  "startBinding": null,
  "endBinding": null,
  "startArrowhead": null,
  "endArrowhead": "arrow"
}
```

### Key values
- **fontFamily:** 1 = Virgil (handwritten, default), 2 = Helvetica, 3 = Cascadia (monospace)
- **roughness:** 0 = smooth, 1 = slightly rough (default Excalidraw feel), 2 = very rough
- **fillStyle:** `"solid"` for clean diagrams, `"hachure"` for classic Excalidraw hatching
- **roundness:** `null` = sharp corners, `{"type": 3}` = rounded rectangles, `{"type": 2}` = curved arrows
- **strokeStyle:** `"solid"`, `"dashed"` (optional connections), `"dotted"`

---

## Common Patterns

### Labeled box
```
[Rect: x, y, w, h]
[Title text: x, y+10, w, fontSize=18]
[Subtitle: x, y+38, w, fontSize=14, strokeColor=#868e96]
```

### Nested container
```
[Host rect: x=0, y=0, w=640, h=500]
[Host label: x=0, y=10, w=640]
[Item 1: x=15, y=50, w=190, h=200]
[Item 2: x=225, y=50, w=190, h=200]
[Item 3: x=435, y=50, w=190, h=200]
```

### Arrow with label
```
[Arrow: x=start_x, y=mid_y, width=gap_width, points=[[0,0],[gap_width,0]]]
[Label: x=start_x, y=mid_y-25, width=gap_width, textAlign=center]
```

---

## Premium mode — logos, shapes & self-render (added 2026-06-25)

For video B-roll / anything shown on camera, build with the Python toolkit in
`scripts/` instead of hand-writing JSON. It embeds **real brand logos** and
gives a **shape vocabulary beyond rectangles**, then **renders to PNG so you
can self-QA before delivery** (the old output was "not presentable" precisely
because it was logo-less plain blocks — see Axiom memory).

**Files:**
- `scripts/excalib.py` — scene builder. Helpers: `txt rect oval dmd pill card
  arr seg polygon hexagon chevron ring img logo_chip save off`. Palette in
  `PALETTE`, brand hexes in `BRAND`.
- `scripts/render.py` — `render.py <scene.excalidraw> <out.png> [scale]`. Uses
  Excalidraw's own `exportToSvg` headless (Playwright + esm.sh) → faithful to
  shapes/colors/logos. Text uses a fallback sans, so leave a little slack in
  box widths.
- `scripts/axiom_diagrams.py` — worked example (3 diagrams + a combined file).
- `assets/logos/` — uniform 24×24 brand SVGs: youtube, tiktok, instagram, x,
  linkedin, supabase, netlify, nextdotjs, notion, claude, buffer + `aiw.png`
  (AI Waterside wordmark for the bottom-right brand stamp). Add more from
  `https://cdn.simpleicons.org/<slug>` (or jsdelivr for misses like linkedin).

**Embedding a logo:** `img(id, x, y, w, "youtube", files)` registers the SVG in
the scene's `files` dict and returns an image element. `logo_chip(...)` builds a
white rounded card with logo + label (+ optional `sub`, `ss="dashed"`, `op` for
a parked/future state). Always thread one `files` dict through the build and
pass it to `save(elements, files, path)`.

**Look that reads as premium (learned 2026-06-25):**
- Neutral chip borders (`#b9c4db`), let the **logo** carry the color — not loud
  full-brand borders (those look sticker-y).
- Mix shapes for interest: hexagon for a process node, a browser-window motif
  (rounded card + dark header strip + 3 traffic-light dots) for "the app",
  funnel/trapezoid via `polygon` for filtering, depth-meter bars, a rotated
  outlined "stamp" (rect + text at `angle`) for blocked/owned.
- Soft zone backdrops (`zone(...)`), color per logical column.
- Stamp the AI Waterside wordmark small bottom-right (`aiw.png`, ~158px wide,
  `op=85`) — standing brand rule for published visuals.
- Combine related diagrams into ONE file (`build_combined` pattern: offset each
  by a vertical BAND, namespace element ids by diagram). Keep B-roll PNGs per
  diagram; stash per-diagram `.excalidraw` intermediates in `output/diagrams/old/`.

**Always** render each diagram to PNG and Read it back, then iterate until clean
before showing Austin.

## Concept buffet — explore before committing (Austin's video workflow)

Austin's go-to for **video diagrams**: don't commit to one idea — spin up
**~8 concept diagrams in ONE file**, each a *different outlook* on the same
build, then he eliminates down to ~3 and we refine those. He explicitly wants
this pattern reused for future videos ("create eight just like this regarding
whatever topic"). Default to 8; deliver the single `.excalidraw` and **do NOT
auto-open** — he opens it and narrows it down.

**Outlooks to draw from** (pick what fits the topic): ideation / origin ·
vs-competitors (feature matrix) · why it's easy to use (UI anatomy) ·
brandability (tokens → themed UI) · extensibility (plug-in sockets) ·
cost / build-vs-buy · tech stack (layered) · architecture (data-flow spine) ·
data-asymmetry comparison · timeline.

**How:** one generator; each concept a function returning `(elements, files)`
in local 0-origin coords (~1480×820); tile into a **2-col grid** via the combine
pattern (offset each by a cell BAND, namespace element ids, share/dedupe
`files`). Every cell gets a **numbered title badge + faint frame** so it's
scannable zoomed out, and a **distinct shape metaphor** (matrix · funnel ·
hexagon sockets · browser-window · timeline · swatches) so elimination is easy.
Self-QA the whole sheet with `render.py`, fix overlaps, then deliver.

**Prime example:** `scripts/axiom_concepts.py` — copy its structure for the next
video. Lessons baked in: keep competitor comparisons **fair** (give them their
real wins, not all-red); final order/count is Austin's call after he scans it.

**No AIW logo as a corner stamp on video B-roll diagrams** — Austin finds it
unnecessary here. `aiw.png` is only for AIW-*branded published* content
(carousels/posts) or as in-diagram *content* (e.g. a brand-kit illustration),
never a bottom-right stamp on these.

## Free-flowing dense maps — the "skills-map" look (added 2026-07-15)

Austin's reaction to this style: "phenomenal, mind-blowingly good." It is now the
**preferred look for hero/B-roll maps**, and it beats the bordered-zone style.
Worked example: `scripts/skills_map_2026-07.py` (bundle original:
`~/Documents/content/long-form/skills-showcase/build_diagrams.py`) — copy its
structure. What actually makes it work (any capable model can reproduce this by
following these rules; none of it is model magic):

1. **No containers, no borders.** Hierarchy comes from position + connector
   lines only. Delete every zone box you're tempted to draw. Free-floating
   clusters read as "organic + complicated"; boxes read as "slide."
2. **The mesh IS the aesthetic.** Many thin curved links at low opacity
   (`sw 1.3, op 40-50`, `crnd {"type": 2}`, midpoint at `[dx*0.5, dy*0.15]`)
   from a parent to every child. 12 dashed amber fan lines from a universal
   row to 3 agent heads is what makes the map look alive. One thick arrow =
   boring; thirty faint curves = "whoa."
3. **Draw links FIRST, nodes after.** Lines pass behind cards — collisions
   stop mattering. Same trick for a weaving "attention path" over a timeline.
4. **Every node earns a 2-line description in the user's voice.** Lowercase,
   concrete, specific ("a week of posts queued in one command", "because
   yes."). Generic labels ("scheduling tool") kill the premium feel. Density
   of *real* detail is the point — Austin explicitly wants maps that reward
   pausing the video, not decoration behind narration.
5. **Encode frequency/status as color temperature.** Featured = white card,
   colored stroke (agent palette), mono `ff=3` slash-names, 2-line desc.
   Standby/rare = gray minis (`sc #adb5bd, bg #f8f9fa`, name + 4-word hint).
   Amber = the meta-layer everywhere: universal skills, `★ MOST-USED` badges,
   "simultaneous" highlight bands. Reserve it — that's what makes it pop.
6. **Honest data only.** Count real things on disk before claiming a number;
   never invent a node to round out a grid. (The reveal "I guessed 30-50, the
   disk says 65" came from actually counting — that beat became the hook.)
7. **Timelines: duration bars, not event cards.** Bars on a real time axis
   (px-per-hour), two sub-rows per lane for overlaps, min bar width ~150 so
   text fits, translucent amber bands over the simultaneous windows, and a
   navy polyline weaving lane-to-lane ("my attention") with dots at each stop.
8. **Self-QA loop is mandatory, in this exact shape:** render the full sheet →
   `ffmpeg -vf crop=...` each region → Read every crop → fix collisions
   (badge-vs-time-label, min widths, label placement) → re-render. Two passes
   minimum; the first render always has 2-3 collisions.
9. **Multi-concept sheets:** one file, vertical bands, numbered oval badge +
   title per concept, NO cell frames. Namespace element ids per concept.

## JSON Wrapper

Every diagram uses this shell:
```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [ ... ],
  "appState": {
    "gridSize": null,
    "viewBackgroundColor": "#ffffff"
  },
  "files": {}
}
```
