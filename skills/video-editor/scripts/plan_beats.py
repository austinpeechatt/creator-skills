#!/usr/bin/env python3
"""
Condense a word-level transcript.json into a token-efficient context file
for Claude to author beats.yaml from.

Output: beats-context.md with sentence-grouped lines like:
  [4.20 → 8.60] "We just hit two hundred forty-eight percent retention."

Also emits a small summary block (duration, word count) and the YAML schema
for beats.yaml so the orchestrating Claude writes valid YAML on the first try.
"""
import sys, json, pathlib, re

SCHEMA = '''\
# beats.yaml schema
# version: 1
# beats:
#   - id: 1                          # int, 1-based, sequential
#     start: 4.2                     # seconds, float
#     end: 8.6                       # seconds, float (must be > start)
#     template: stat-callout         # one of: stat-callout, text-callout,
#                                    #   list-build, quote-card, code-beat,
#                                    #   comparison, end-card
#     layout: A                      # A = face-center + floating card(s)
#                                    # B = face-PIP (bottom-right) + full-stage content
#     props:                         # template-specific, see SKILL.md
#       number: "+248%"
#       label: "retention"
#     rationale: "reinforce the number Austin just said"
'''

SENTENCE_END = re.compile(r'[.!?]+$')

def group_sentences(words, max_gap=0.6, max_dur=6.0):
    """Cluster word tokens into sentence-ish groups for readable context."""
    groups, cur = [], []
    for w in words:
        text = w.get("text", "")
        start = float(w.get("start", 0.0))
        end = float(w.get("end", start))
        if not text.strip():
            continue
        if cur:
            last_end = cur[-1]["end"]
            prev_text = cur[-1]["text"]
            gap = start - last_end
            dur = end - cur[0]["start"]
            if (SENTENCE_END.search(prev_text.strip())
                    or gap > max_gap
                    or dur > max_dur):
                groups.append(cur)
                cur = []
        cur.append({"text": text, "start": start, "end": end})
    if cur:
        groups.append(cur)
    return groups

def render(groups):
    lines = []
    for g in groups:
        start = g[0]["start"]
        end = g[-1]["end"]
        text = " ".join(w["text"].strip() for w in g if w["text"].strip())
        text = re.sub(r'\s+', ' ', text).strip()
        lines.append(f"[{start:6.2f} → {end:6.2f}]  {text}")
    return "\n".join(lines)

def main():
    if len(sys.argv) != 3:
        print("Usage: plan_beats.py <transcript.json> <beats-context.md>")
        sys.exit(2)
    tpath, opath = sys.argv[1], sys.argv[2]
    data = json.loads(pathlib.Path(tpath).read_text())
    words = data.get("words", [])
    words = [w for w in words if w.get("type", "word") == "word"]
    if not words:
        print("ERROR: transcript has no word tokens")
        sys.exit(1)
    groups = group_sentences(words)
    duration = words[-1].get("end", 0.0)

    out = []
    out.append("# Beat Planning Context\n")
    out.append(f"- Total duration: {duration:.2f}s")
    out.append(f"- Word tokens: {len(words)}")
    out.append(f"- Sentence groups: {len(groups)}\n")
    out.append("## Transcript (timestamped sentence groups)\n")
    out.append("```")
    out.append(render(groups))
    out.append("```\n")
    out.append("## Beat density target")
    out.append("- 10–14 beats total for the full video")
    out.append("- ~1 beat every 25–35s on average")
    out.append("- Premium/sparse, NOT dense. Each beat should reinforce a specific spoken moment.\n")
    out.append("## Schema")
    out.append("```yaml")
    out.append(SCHEMA)
    out.append("```")
    pathlib.Path(opath).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(opath).write_text("\n".join(out))
    print(f"[plan_beats] wrote {opath} ({len(groups)} sentence groups, {duration:.1f}s)")

if __name__ == "__main__":
    main()
