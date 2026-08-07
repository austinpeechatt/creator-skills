---
name: notion-brain
description: Adds a YouTube video idea to Austin's Notion database. Takes a raw ramble, structures it into a titled entry with difficulty, tags, form, status, and organized page content — then pushes it to Notion.
argument-hint: <your video idea ramble>
user-invocable: true
allowed-tools: Bash(python3 scripts/create_video_idea.py *), Bash(source ~/.zshrc *), Write
---

# Notion Brain — YouTube Video Ideas

Austin will give you a raw, unfiltered ramble about a video idea. Your job is to structure it into a clean Notion entry and push it to his YouTube Video Ideas database.

## Input

Austin's raw ramble: $ARGUMENTS

If $ARGUMENTS is empty or the user didn't provide a ramble inline, ask: "What's the video idea?"

## Step 1 — Parse the Ramble

Extract or infer the following from Austin's ramble:

| Field | How to determine | Default |
|-------|-----------------|---------|
| **Title** | Craft a concise, descriptive title (not clickbait — working title for the database) | Required — always generate one |
| **Difficulty** | `Easy`, `Medium`, or `Hard` — based on production complexity, not topic complexity | `Medium` |
| **Tags** | One or more from: `Tutorial`, `Case Study`, `Commentary`, `Tips`, `Story`, `Tool Review`, `Vlog`, `Claude Code`, `AI Tools` | Infer from content |
| **Status** | Almost always `Not started` unless Austin says otherwise | `Not started` |
| **Form** | `Long` or `Short` — based on whether this is a full video or a short | `Long` |
| **Page content** | The meat of the idea — structured into sections with bullets and paragraphs | See Step 2 |

If Austin explicitly states any of these values (e.g., "difficulty is easy", "tag it as tutorial"), use exactly what he said. Only infer what he doesn't specify.

## Step 2 — Structure the Page Content

Organize Austin's ramble into clear sections. Use your judgment on section names — they should reflect the actual content, not a generic template.

**Rules:**
- Keep 80–90% of what Austin said. He rambles with intent — most of it is gold. Tighten sentence structure but don't cut substance.
- Organize into logical sections with clear headings. Use sub-headings (H3) within sections when there are distinct parts.
- Bullets for action items, talking points, tools to mention, specific things to show on camera.
- Paragraphs for narrative sections, thesis statements, closing thoughts — things that need to flow.
- Preserve Austin's voice. Don't sanitize his language into corporate-speak. If he says "mind-fuck" or "touching grass", keep it.
- If he mentions specific tools, people, products, or prices — keep them. Details matter.
- Don't add content he didn't mention. Don't pad with generic advice. Only structure what's there.

## Step 3 — Write the JSON

Write the structured data to `/tmp/notion_video_idea.json` using the Write tool:

```json
{
  "title": "Working Title for the Video",
  "difficulty": "Easy",
  "tags": ["Tutorial"],
  "status": "Not started",
  "form": "Long",
  "sections": [
    {
      "heading": "Section Name",
      "type": "sub_sections",
      "content": [
        {
          "heading": "Sub-section Name",
          "content": [
            "Bullet point one",
            "Bullet point two"
          ]
        }
      ]
    },
    {
      "heading": "Another Section",
      "type": "paragraphs",
      "content": [
        "First paragraph of narrative text.",
        "Second paragraph continuing the thought."
      ]
    },
    {
      "heading": "Bullet Section",
      "type": "bullets",
      "content": [
        "Point one",
        "Point two"
      ]
    }
  ]
}
```

**Section types:**
- `"sub_sections"` — section with H3 sub-headings, each containing bullets. Use for multi-part video structures.
- `"bullets"` — flat list of bullet points under an H2.
- `"paragraphs"` — sequential paragraphs under an H2. Use for narrative/thesis content.

**Rules:**
- All values must be plain strings — no markdown, no leading dashes.
- Tags must match existing options exactly (case-sensitive).
- `/tmp/notion_video_idea.json` is overwritten on every run — that's expected.

## Step 4 — Push to Notion

Run:

```bash
source ~/.zshrc && python3 scripts/create_video_idea.py /tmp/notion_video_idea.json
```

**If output starts with `SUCCESS:`** — report the title and Notion URL to Austin.
**If output starts with `ERROR:`** — show the error verbatim. Common fixes: check NOTION_API_KEY in `~/.claude/.env`.

## Step 5 — Confirm to Austin

Short confirmation. Include:
- The title you chose
- The tags, difficulty, and form you set
- Notion URL
- One-line summary of what's in the page

Don't repeat the full content back. Austin can click through to Notion to review.

## Step 6 — Ingest the Raw Ramble into the Personal-Brand Vault

**Default, not optional.** Notion holds the *structured idea*; it does NOT capture Austin's raw voice. After a successful push, ingest the **verbatim** ramble into the personal-brand vault so his voice/tonality/energy accumulates as source material for future scripting.

- Invoke `/vault-ingest` with the raw ramble (his exact words — filler, profanity, and all — not the cleaned-up Notion version).
- Don't ask permission — this is the standing default (Austin, 2026-07-02: "I hope you're taking down the raw thoughts... ingesting all this into the Obsidian Vault... it might help when we script ideas").
- The ramble lands verbatim in `raw/notion-ideas/` and the wiki layer (frameworks/topics/tools/ideas + voice-fingerprint samples) gets built out. See `feedback_ramble_to_vault` memory.
- **Skip only if** Austin explicitly says not to, or the "ramble" was really just a terse one-liner with no voice signal worth capturing.

---

## Notes

- **Multiple ideas in one ramble:** If Austin clearly describes multiple distinct video ideas, ask if he wants them as separate entries or one combined entry.
- **Updating existing entries:** This skill only creates new entries. If Austin wants to update an existing idea, do it via direct Notion API calls (PATCH to the page ID).
- **New tags:** If Austin mentions a topic that doesn't fit existing tags, use the closest match. Don't create new tag options without asking.
- **Short-form ideas:** If Austin says "this could be a Short" or "quick 60-second thing", set Form to `Short` and keep the page content minimal — just the hook and key points.
