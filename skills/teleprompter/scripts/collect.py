#!/usr/bin/env python3
"""Collect the newest teleprompter take, clean it, and report whether it fits.

Usage:
  collect.py --out DIR [--target 45] [--match-lufs -17.5] [--exact-dur 85.085]

Does, in order:
  1. finds the newest vo-take.* / *vo*.webm in ~/Downloads
  2. measures duration, speech span, noise floor, loudness
  3. mutes the space-bar click at the head (detected, not assumed)
  4. mono / highpass 80 / gentle compression / two-pass loudnorm / fades
  5. optionally pads or trims to an exact length (for picture-locked inserts)
  6. re-verifies the output and prints a fit verdict

Never denoises: if the floor is clean that only adds artifacts, and if the floor
is bad the right fix is re-recording, not smearing it.
"""
import argparse, json, re, shutil, subprocess, sys
from pathlib import Path

DL = Path.home() / "Downloads"


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stderr


def ffprobe_dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    return float(r.stdout.strip())


def vol(p, ss=None, t=None):
    cmd = ["ffmpeg", "-nostdin"]
    if ss is not None: cmd += ["-ss", str(ss)]
    if t is not None:  cmd += ["-t", str(t)]
    cmd += ["-i", str(p), "-af", "volumedetect", "-f", "null", "/dev/null"]
    err = sh(cmd)
    m = dict(re.findall(r"(mean_volume|max_volume): (-?[\d.]+) dB", err))
    return {k: float(v) for k, v in m.items()}


def loudness(p):
    err = sh(["ffmpeg", "-nostdin", "-i", str(p), "-af",
              "loudnorm=print_format=summary", "-f", "null", "/dev/null"])
    out = {}
    for key, label in (("I", "Input Integrated"), ("TP", "Input True Peak"), ("LRA", "Input LRA")):
        m = re.search(rf"{label}:\s+(-?[\d.]+)", err)
        if m: out[key] = float(m.group(1))
    return out


def quiet_gap(p, gate=-40, mind=0.5):
    """Find a silent gap in the MIDDLE of the take for a true noise-floor read.
    The head gap contains the space-bar click, so measuring there reports the
    click, not the floor."""
    err = sh(["ffmpeg", "-nostdin", "-i", str(p), "-af",
              f"silencedetect=noise={gate}dB:d={mind}", "-f", "null", "/dev/null"])
    pairs = list(zip([float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)],
                     [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]))
    mids = [(a, b) for a, b in pairs if a > 2.0]
    if not mids:
        return None
    a, b = max(mids, key=lambda ab: ab[1] - ab[0])
    return (a + 0.15, max(0.2, (b - a) - 0.3))


def speech_span(p, gate=-40, mind=0.4):
    err = sh(["ffmpeg", "-nostdin", "-i", str(p), "-af",
              f"silencedetect=noise={gate}dB:d={mind}", "-f", "null", "/dev/null"])
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    dur = ffprobe_dur(p)
    first = ends[0] if ends else 0.0
    last = starts[-1] if starts and starts[-1] > first else dur
    return first, last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="directory to write vo-raw.* and vo-clean.wav")
    ap.add_argument("--target", type=float, help="intended read length, for the fit verdict")
    ap.add_argument("--match-lufs", type=float, default=-17.0,
                    help="target integrated LUFS; match the neighbouring segments, not a generic number")
    ap.add_argument("--exact-dur", type=float, help="pad/trim output to exactly this many seconds")
    ap.add_argument("--src", help="explicit source file instead of newest in Downloads")
    a = ap.parse_args()

    if a.src:
        src = Path(a.src)
    else:
        cands = [p for p in DL.glob("*") if p.suffix.lower() in (".webm", ".mp4", ".m4a", ".wav")
                 and ("vo" in p.name.lower() or "take" in p.name.lower())]
        if not cands:
            sys.exit(f"no vo-take.* found in {DL} — did the browser save it?")
        src = max(cands, key=lambda p: p.stat().st_mtime)

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    raw = out / f"vo-raw{src.suffix}"
    if src.resolve() != raw.resolve():
        shutil.copy2(src, raw)

    dur = ffprobe_dur(raw)
    sp0, sp1 = speech_span(raw)
    gap = quiet_gap(raw)
    floor = vol(raw, gap[0], gap[1]) if gap else {}
    ld = loudness(raw)

    print(f"source      : {src.name}")
    print(f"duration    : {dur:.2f}s")
    print(f"speech span : {sp0:.2f}s -> {sp1:.2f}s  ({sp1-sp0:.2f}s of read)")
    print(f"loudness    : {ld.get('I','?')} LUFS   true peak {ld.get('TP','?')} dBTP")
    if floor:
        print(f"noise floor : {floor.get('mean_volume','?')} dB mean "
              f"(measured in a mid-take gap at {gap[0]:.1f}s)")
        if floor.get("mean_volume", -99) > -45:
            print("  ** noisy room — consider re-recording; do NOT denoise **")
    if ld.get("TP", -99) > -0.5:
        print("  ** WARNING: true peak near/over 0 — input was clipping, re-record hotter-safe **")

    if a.target:
        read = sp1 - sp0
        slack = max(1.0, a.target * 0.02)
        if read <= a.target:
            verdict = f"FITS with {a.target-read:.1f}s to spare"
        elif read <= a.target + slack:
            verdict = f"fits (over by {read-a.target:.1f}s, inside {slack:.1f}s tolerance)"
        else:
            verdict = f"** OVER by {read-a.target:.1f}s — trim or re-read faster **"
        print(f"fit         : {read:.2f}s read vs {a.target:.2f}s target -> {verdict}")

    # mute the space-bar click: silence up to just before first speech
    mute_to = max(0.0, sp0 - 0.30)
    fade_in = f"afade=t=in:st={mute_to:.3f}:d=0.25" if mute_to > 0.05 else "anull"
    fade_out = f"afade=t=out:st={max(0.0, dur-0.35):.3f}:d=0.30"
    chain = ("pan=mono|c0=0.5*c0+0.5*c1,highpass=f=80,"
             "acompressor=threshold=-24dB:ratio=3:attack=5:release=120")

    err = sh(["ffmpeg", "-nostdin", "-i", str(raw), "-af",
              f"{chain},loudnorm=I={a.match_lufs}:TP=-1.5:LRA=7:print_format=json",
              "-f", "null", "/dev/null"])
    m = re.search(r"\{[^{}]*input_i[^{}]*\}", err, re.S)
    if not m:
        sys.exit("loudnorm measure pass failed:\n" + err[-800:])
    d = json.loads(m.group(0))
    ln = (f"loudnorm=I={a.match_lufs}:TP=-1.5:LRA=7:measured_I={d['input_i']}:"
          f"measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:"
          f"measured_thresh={d['input_thresh']}:offset={d['target_offset']}:linear=true")

    clean = out / "vo-clean.wav"
    sh(["ffmpeg", "-nostdin", "-v", "error", "-i", str(raw), "-af",
        f"{chain},{ln},aresample=48000,{fade_in},{fade_out}",
        "-c:a", "pcm_s24le", "-ar", "48000", "-ac", "1", str(clean), "-y"])

    if a.exact_dur:
        # two passes: atrim can't extend a non-zero-PTS decode, apad on a clean WAV can.
        tmp = out / ".tmp.wav"
        sh(["ffmpeg", "-nostdin", "-v", "error", "-i", str(clean), "-af",
            f"atrim=0:{a.exact_dur},asetpts=N/SR/TB", "-c:a", "pcm_s24le", str(tmp), "-y"])
        sh(["ffmpeg", "-nostdin", "-v", "error", "-i", str(tmp), "-af",
            f"apad=whole_dur={a.exact_dur}", "-c:a", "pcm_s24le", "-ar", "48000",
            "-ac", "1", str(clean), "-y"])
        tmp.unlink(missing_ok=True)

    cl, cd = loudness(clean), ffprobe_dur(clean)
    head = vol(clean, 0, max(0.2, mute_to)) if mute_to > 0.05 else {}
    print(f"\nwrote {clean}")
    print(f"  duration  : {cd:.3f}s" + (f"   (target {a.exact_dur}, delta {(cd-a.exact_dur)*1000:+.1f} ms)"
                                        if a.exact_dur else ""))
    print(f"  loudness  : {cl.get('I','?')} LUFS   true peak {cl.get('TP','?')} dBTP")
    if head: print(f"  head muted: {head.get('max_volume','?')} dB max over 0-{mute_to:.2f}s")
    if cl.get("TP", -99) > -0.9:
        print("  ** true peak too hot — lower --match-lufs **")


if __name__ == "__main__":
    main()
