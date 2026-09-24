#!/usr/bin/env python3
"""Build a recording teleprompter page from a script.

Usage:
  build.py SCRIPT.md --duration 45 [--lead 1.2] [--tail 1.0] [--out page.html]
  build.py SCRIPT.md --beats beats.json [--out page.html]

Script format: blank-line-separated blocks. A block starting with "> " is spoken
(the "> " is stripped). A block wrapped in parentheses, e.g. "( beat )", is a
pause marker — displayed, never spoken, and given its own slice of time.
Lines starting with # are ignored (headings).

Timing: line start times are distributed across (duration - lead - tail)
proportional to each line's word count, so long lines get more room. A pause
marker is weighted as 3 words.

--beats takes a JSON list of [start_seconds, "text"] for frame-accurate work
where the read must land on specific picture (see the Axiom TRASH montage).
"""
import argparse, html, json, re, sys
from pathlib import Path

PAUSE_W = 3          # a "( beat )" costs this many words of time
TEMPLATE = Path(__file__).with_name("page.html.tmpl")


def parse_script(text):
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        block = " ".join(l.strip() for l in block.splitlines() if l.strip())
        if not block or block.startswith("#") or block.startswith("---"):
            continue
        if block.startswith(">"):
            block = block.lstrip("> ").strip()
        if not block:
            continue
        is_pause = bool(re.fullmatch(r"\(.*\)", block))
        out.append((block, is_pause))
    return out


def distribute(lines, duration, lead, tail):
    span = duration - lead - tail
    if span <= 0:
        sys.exit(f"duration {duration}s is too short for lead {lead}s + tail {tail}s")
    weights = [PAUSE_W if p else max(1, len(t.split())) for t, p in lines]
    total = sum(weights)
    starts, acc = [], 0.0
    for w in weights:
        starts.append(round(lead + span * acc / total, 2))
        acc += w
    return starts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--duration", type=float, help="target read length in seconds")
    ap.add_argument("--beats", help="JSON file of [[start,text],...] for picture-locked reads")
    ap.add_argument("--lead", type=float, default=1.2, help="silence before the first word")
    ap.add_argument("--tail", type=float, default=1.0, help="silence after the last word")
    ap.add_argument("--title", default="Teleprompter")
    ap.add_argument("--out", default="teleprompter.html")
    a = ap.parse_args()

    if a.beats:
        beats = json.loads(Path(a.beats).read_text())
        entries = [(float(s), str(t), bool(re.fullmatch(r"\(.*\)", str(t).strip()))) for s, t in beats]
        end = max(s for s, _, _ in entries) + 4.0
    else:
        if not a.duration:
            sys.exit("need --duration or --beats")
        lines = parse_script(Path(a.script).read_text())
        if not lines:
            sys.exit("no spoken lines found in script")
        starts = distribute(lines, a.duration, a.lead, a.tail)
        entries = [(s, t, p) for s, (t, p) in zip(starts, lines)]
        end = a.duration - a.tail

    words = sum(len(t.split()) for _, t, p in entries if not p)
    js = json.dumps([[s, t, 1 if p else 0] for s, t, p in entries], ensure_ascii=False)

    page = TEMPLATE.read_text()
    page = (page.replace("__LINES__", js)
                .replace("__END__", f"{end:.2f}")
                .replace("__TITLE__", html.escape(a.title)))
    Path(a.out).write_text(page)

    spoken = sum(1 for _, _, p in entries if not p)
    wpm = words / (end / 60) if end else 0
    print(f"wrote {a.out}")
    print(f"  {spoken} spoken lines, {words} words, target {end:.1f}s")
    print(f"  required pace: {wpm:.0f} wpm", end="")
    print("  ** TIGHT — trim the script **" if wpm > 165 else "  (comfortable)" if wpm >= 120 else "  (very relaxed)")


if __name__ == "__main__":
    main()
