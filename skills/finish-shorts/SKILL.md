---
name: finish-shorts
description: Use when Austin wants to batch shorts from a finished long-form — "make shorts from this video", "run the shorts editor on the long-form", "cut this into shorts", "repurpose into shorts", or "take it from here on shorts". The auto-routed orchestrator for branded Remotion shorts: Fable scans the long-form, picks + plans the best short-worthy moments (graphics, cutaways, logos, cuts) with ONE plan approval, then fans out MULTIPLE parallel Opus subagents (one per short) that build/frame/render/verify, with a single batched face-check gate before finalize. Each short returns when done. NOT for Vizard auto-clips (use youtube-shorts-generator for those).
argument-hint: <finished long-form MP4 path OR bundle slug>
---

# finish-shorts

Batch-produce branded vertical Shorts from a finished long-form, in the parallel-agent shape: **Fable plans all of them** (moments + fresh graphics + treatments), Austin gives **one plan approval**, then **one Opus subagent per short** runs in parallel and each returns when done — with a single **batched face-check gate** between v1 and finalize.

**Read `~/my-video/aiwshorts-data/SHORTS-PLAYBOOK.md` first** — it's the locked engine + format + face-framing recipe + graphics bar. This skill orchestrates that playbook across many shorts; it does not replace it.

## Do not hijack an in-flight execution

If this session was directly told to execute a specific shorts plan (or is mid-render under explicit instructions), that instruction wins — continue as told; do NOT restart planning/approval or re-fan-out. Direct user instructions outrank skill auto-invocation.

## Division of labor (this is what makes the parallelism safe)

The shorts engine (`~/my-video/src/aiwshorts/`) is a **single shared Remotion project** — parallel subagents CANNOT each rewrite `registry.tsx` / `templates/*.tsx` without colliding. So:

- **Fable (planning session) is the SOLE author of engine code** — all fresh graphics templates + every per-short beat JSON are written during planning, serially, by one writer. The graphics are the crown jewel (playbook §2): design fresh per short, beat the obsidian bar, don't stamp the same visuals.
- **Subagents are READ-ONLY on engine code.** Each one only: rebuilds its own portrait source clip, still-checks framing, renders `out/<NAME>.mp4` from its own `<NAME>.json`, and verifies. Unique output names, no shared writes → safe in parallel.

## Phase 0 — Resolve the source long-form

`$1` = a finished long-form MP4 path or a bundle slug. Prefer the **final, overlaid** long-form (a `finish-video` output if one exists), not the raw export. Resolve a slug across `~/Documents/content/long-form/<slug>/` (+ short-form / Archive) per CLAUDE.md. `ffprobe` it. Read the bundle `STATUS.md` for shorts count hints / posting cadence.

## Phase 1 — Plan every short (Fable, autonomous)

1. **Transcript** — reuse `<bundle>/assets/transcript.json` if the long-form already has one (finish-video leaves it); else Scribe via the video-editor `transcribe.py`. Word-level. Never Whisper.
2. **Find moments** — scan the transcript for self-contained beats with a real hook + payoff (setup/how-to, a punchy claim, a surprising number). **Count is content-driven** — as many as there are genuinely strong moments, not a quota. Note each moment's clip window.
3. **Per short, design the build** following the playbook: ~12 sparse premium beats, a template picked by MEANING per beat (invent fresh graphics for this short's content — treat obsidian as the FLOOR), 1–2 full-frame cutaways in transcript gaps, caption emphasis words, real brand logos where a tool/LLM is named. List which beats want a **real screenshot** and **proactively ask Austin for those** at the checkpoint (can't capture his private apps).
4. **Author the engine code** — write any fresh templates into `registry.tsx` / `templates/*.tsx` and each short's beat JSON into `~/my-video/aiwshorts-data/<slug>-short-N.json`. Single writer, sequential.
5. **Write the plan file** `~/.claude/plans/finish-shorts-<slug>.md`: the moment list (windows + one-line hook each), per-short beat plan (template + purpose per beat, cutaway gaps, screenshots-needed), the source-clip prep spec per short, and the face-framing target (head ≈55–57% of card width, centered x=608 — playbook §4). This is each subagent's complete brief.

## Phase 2 — CHECKPOINT 1 (plan approval + hybrid moment input)

Proactively surface Austin's calls, then get the go:
1. `AskUserQuestion` for: any **must-have moments to add** (hybrid — Fable proposed, he can add/cut/swap), and request the **screenshots** the plan needs (list them; he drops into `~/Downloads/axiom-inbox/`).
2. Present the short list (N shorts, one-line hook + treatment each) and get a clear go/no-go. Apply edits to the plan file. **Do not fan out until approved.**

## Phase 3 — WAVE 1: parallel framing pass (autonomous fan-out)

Dispatch **one background Opus subagent per short**, in parallel (`Agent`, `model: "opus"`, `run_in_background: true`, `subagent_type: "general-purpose"`). Each subagent prompt (fill `<PLAN_PATH>`, `<SHORT_ID>`, `<NAME>`):

> Read `~/my-video/aiwshorts-data/SHORTS-PLAYBOOK.md` and the plan at `<PLAN_PATH>`. You own short `<SHORT_ID>` (`<NAME>`) ONLY. Engine code + your beat JSON are already authored — treat `src/aiwshorts/` as READ-ONLY; touch only your source clip and `out/<NAME>.*`.
> Do the face-framing source rebuild per playbook §4: cut your clip window, rebuild to a physical 1216×2160 source (`crop=1216:1642:0:259` → scale ~0.85 → `pad` with the SAMPLED wall hex, never offwhite), MEASURE the head (extract a frame, find center-x + width px), target head ≈55–57% of card width centered at x=608, and set `objectPosition`. Encode to a UNIQUE temp name then `mv` (never two `-y` writers on one path).
> Render ONE framing still on a talking beat (`remotion still`) and extract that same frame from your rebuilt source. Return: the still path, measured head center-x + width %, your chosen `objectPosition`, and any framing risk. **STOP — do not full-render yet.**

## Phase 4 — CHECKPOINT 2 (batched v1 face-check gate)

When all Wave-1 subagents return, Read every framing still and present them to Austin **together, in one look** — face centered? seam/halo? crop right? Collect per-short nudges (objectPosition Y, wall hex, etc.). This is the one face gate his history calls for (memory `feedback_shorts_face_framing`) — batched, not per-short interrupts. Fold nudges into each short's JSON/source spec.

## Phase 5 — WAVE 2: parallel finalize (autonomous fan-out)

Re-dispatch one background Opus subagent per short to finish. Prompt:

> Apply the framing nudge for `<NAME>` from the plan/checkpoint, then full render: `npx remotion render ShortsMaster out/<NAME>.mp4 --props=aiwshorts-data/<NAME>.json`. **Verify FROM THE MP4** — `ffmpeg -ss <t> -i out/<NAME>.mp4 -frames:v 1` at early/mid/LATE + both cutaways, Read them (never trust `remotion still` as proof — playbook §4, memory `feedback_verify_from_final_mp4`). Confirm face framing, caption sync, cutaway zoom/whoosh, end-card. Then ship: copy a QT-safe MP4 to `~/Downloads/`, archive to the SSD `renders/` + `youtube/shorts/`. Return: final path, a one-line QC result, and any defect you couldn't fix. **STOP at the shipped MP4 — do NOT publish, caption for Buffer, or schedule.**

Guard disk: renders need ~1.5GB+ free EACH and copy public/ (~900MB) per invocation — keep effective parallelism to ~2–3 (the Agent cap helps); if `df` is tight, dispatch in smaller batches.

## Phase 6 — Report (autonomous)

As each short returns (they finish independently), and once all are in: relay a per-short summary to Austin (final path, QC, any flagged defect), and `open` the shipped MP4s. For any short a subagent couldn't get clean, name the defect and offer a targeted re-render of just that one. Remind him these are shipped but NOT posted — Buffer scheduling is a separate deliberate step (`buffer-scheduler`). Bundle stays ACTIVE until all shorts/repurposes post.

## Guardrails

- **Two checkpoints only:** plan approval (Phase 2) + batched face-check (Phase 4). Everything else is autonomous.
- **Fable is the sole engine-code writer; subagents are read-only on `src/aiwshorts/`** — this is what prevents parallel `registry.tsx` collisions. If a short genuinely needs engine code changed mid-flight, the ORCHESTRATOR makes the edit serially between waves, not a subagent.
- **Face framing is a hard, measured rule** — not a per-video guess. The gate is a confirm, not a hunt; subagents do the measurement first.
- **Stops at shipped MP4s** — no publishing/scheduling/Buffer. Separate step.
- **Source clips MUST be physically 1216×2160** (OffthreadVideo black-frames other sizes); never let the video element overhang the comp's right edge; unique temp names + `mv` for every ffmpeg encode (memory `feedback_ffmpeg_background_encodes`); never off the exFAT SSD for render/playback (memory `feedback_exfat_venv`).
- **Ask for screenshots up front** (Phase 2) — can't capture his private apps.
- Don't rebuild the engine or re-derive the locked format — extend it (playbook §1–2).
