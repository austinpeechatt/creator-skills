---
name: teleprompter
description: "Use when Austin is recording a scripted voiceover — for a Short, a Reel, a B-roll sequence, or a montage insert in a long-form. Triggered by '/teleprompter', 'I want to record a VO for this', 'set up the teleprompter', 'let me read this', 'record a voiceover for the b-roll'. Generates a paced, self-recording read page (space bar = record + timer), serves it on localhost, then collects the take, cleans it, and reports whether it fits the target length. NOT for on-camera A-roll reads — see the eyeline warning."
argument-hint: "[script path or slug] [target seconds]"
---

# Teleprompter — paced VO recording

One page that paces the read **and** captures the audio. Space starts both, space
stops and saves. Built after a version that only ran a timer, where Austin hit
space twice, assumed he'd recorded, and had nothing — **if it looks like it
records, it must record.**

## When this applies

**Yes — voiceover over B-roll.** Faceless shorts, desk time-lapses, screen
recordings, gym/lifestyle sequences, montage inserts in a long-form. His mouth
isn't on camera, so the read can be written and performed after the fact.

**No — on-camera A-roll.** Reading a script while framed means eyeline: text on a
monitor pulls his eyes off the lens and it reads as shifty. If he wants a scripted
on-camera take, say so and talk about bullet points near the lens instead of
running this.

## Step 1 — Get or write the script

If he's handing you a script, use it. If you're writing it, and it's going over
**existing footage**, do these first — all three changed real decisions on the
TRASH montage:

1. **Read the pixels.** `ffmpeg -ss <t> -i <clip> -frames:v 1` at 10–20 points and
   actually Read them. Build notes and beat maps are a lossy secondary source.
2. **Grep the transcript** of the surrounding cut. Don't spend a beat a
   neighbouring chapter already owns.
3. **Anchor each line to a shot**, not to a stopwatch.

Script format — blank-line-separated blocks, `> ` prefix optional, `( beat )` for
a deliberate pause:

```markdown
> First line he says.

( beat )

> Second line.
```

## Step 2 — Build the page

```bash
S=~/.claude/skills/teleprompter/scripts
python3 $S/build.py SCRIPT.md --duration 45 --out /tmp/tp/teleprompter.html
```

Line start times are distributed proportional to word count, so long lines get
more room. It prints the **required pace in wpm** — over 165 means the script is
too long for the slot and should be trimmed before he records, not after.

**Picture-locked work** (the read must land on specific shots) — pass explicit
beats instead of a duration:

```bash
python3 $S/build.py SCRIPT.md --beats beats.json --out /tmp/tp/teleprompter.html
# beats.json: [[1.5,"First line."],[8.0,"Second line."]]
```

## Step 3 — Serve it on localhost and open it

**Required — `file://` pages are denied microphone access and fail silently.**

```bash
cd /tmp/tp && (python3 -m http.server 8787 --bind 127.0.0.1 >/dev/null 2>&1 &)
sleep 1 && open "http://127.0.0.1:8787/teleprompter.html"
```

Tell him: Chrome asks for mic permission the first time — allow it. The **REC lamp
turns red and the level meter moves** when it's live; that's the confirmation.
Space again saves `vo-take.webm` to Downloads.

⭐ **Mic: match the A-roll, don't default to convenience.** If this VO drops into a
video that already has Austin on camera, record it on **the same mic that video was
shot with — normally the DJI**. Level-matching does NOT fix a mic mismatch: the TRASH
montage VO was clean and neighbour-matched at −17.5 LUFS and he still heard it
(2026-09-23): *"the voiceover sound quality feels so off compared to when it switches
from the DJI mic to the Fifine mic… let's just stick with the same mic, definitely,
and preferably the DJI."* → [[feedback_vo_mic_consistency]]

**Ask which mic before generating the page**, and set it explicitly — the page
auto-selects the fifine, so leaving it alone silently reproduces the mismatch.
The **fifine USB desk mic is permanently wired** (no clothing rustle, fuller tone, no
transfer step) and is the right pick only for a **standalone** read with no on-camera
A-roll to match. Whichever you use, verify it's passing signal first:

```bash
ffmpeg -nostdin -v error -f avfoundation -i ":2" -t 3 -c:a pcm_s16le /tmp/lvl.wav -y
ffmpeg -nostdin -i /tmp/lvl.wav -af volumedetect -f null /dev/null 2>&1 | grep volume
rm -f /tmp/lvl.wav
```

Don't tell him to watch a clock while reading — it makes him rush. The page is the
pacing; a second or two of drift is absorbed by the gaps.

## Step 4 — Collect and clean the take

```bash
python3 $S/collect.py --out <bundle>/vo --target 45
```

Reports duration, speech span, noise floor, loudness and a fit verdict; mutes the
space-bar click at the head (detected, not assumed); then mono / highpass 80 /
gentle compression / two-pass loudnorm / fades → `vo-clean.wav`.

For a picture-locked insert add `--exact-dur 85.085` to land sample-exact.

**`--match-lufs` is the one flag to think about.** Default −17.0 is a reasonable
standalone VO. **If this is going into an existing cut, measure the neighbouring
segments first and match them** — a generic target is meaningless inside a concat:

```bash
ffmpeg -i segB.mp4 -af loudnorm=print_format=summary -f null /dev/null 2>&1 | grep Input
```

On TRASH, aiming at a generic −16 produced −14.6 LUFS / **+0.5 dBTP (clipping)**,
3 LU louder than its neighbours. Matching them gave −17.5 / −2.5.

It never denoises. A clean floor doesn't need it; a bad floor needs a re-record.

## Step 5 — Verify before claiming it's done

- **Every line lands in its intended shot**, if there is picture. Take line starts
  from `silencedetect` on the take and interval-match them against the shot
  boundaries. Total duration fitting is not the same as each line landing.
- Probe head / mid / tail levels of the output.
- If mixing into a finished build: find the **smallest correct target** (usually
  one concat segment, not the whole film), check `pgrep -lf ffmpeg` for another
  session's renders first, preserve the pre-edit original, write atomically, and
  confirm all segments still match codec/rate/channels/resolution/fps.

## Cleanup

```bash
pkill -f "http.server 8787"
```

Related memory: `project_vo_teleprompter`, `feedback_verify_from_final_mp4`,
`feedback_ffmpeg_silent_timing_traps`, `feedback_video_agent_orchestration`.
