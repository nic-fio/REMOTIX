#!/usr/bin/env python3
"""
07-b42 — the audio judge: it LISTENS, it does not count blocks.

⛔ `LEZIONI.md` §2.2, first row of the table: «the bench counted frames
   sent and blocks acknowledged; the defect changed **the samples** — the audio
   was full-scale noise».  ⇒ Here we measure the SIGNAL:

     hz        the dominant frequency (Goertzel, 1 Hz step)
     rms       the amplitude
     purity   how much energy sits in the dominant line — ⭐ it is the only number
               that tells a TONE from NOISE, and it is the one the judge
               of the probe `07-b40` has already certified on six cases

⭐ And on top of that it measures something the probe could not: **the rhythm**.  The
   `instant` of §6.3 are the server's clock, so gaps are counted
   where they were born instead of being deduced from silence.

Reads the JSONL that `01-b3-cliente.py --audio-write` produces.

Usage:  python3 07-b42-giudice.py blocchi.jsonl [--hz 440] [--seconds 3]
"""
import argparse
import base64
import json
import math
import sys

FREQUENCY = 48000
CHANNELS = 2
BLOCK_US = {1: 20000, 2: 5000}  # Opus 20 ms, PCM 5 ms (§5.3)


def judge(samples):
    """The dominant frequency, the amplitude and the purity.

    ⛔ «Nothing to judge» is an outcome of ITS OWN and not a zero: `CODER.md` §3.10.
    """
    m = len(samples)
    if m == 0:
        return {"outcome": "NOTHING TO JUDGE", "samples": 0}
    rms = math.sqrt(sum(x * x for x in samples) / m)
    peak, hz, total_sum = 0.0, 0, 0.0
    for f in range(100, 2001):
        w = 2.0 * math.cos(2.0 * math.pi * f / FREQUENCY)
        s1 = s2 = 0.0
        for x in samples:
            s1, s2 = w * s1 - s2 + x, s1
        p = max(0.0, s1 * s1 + s2 * s2 - w * s1 * s2)
        total_sum += p
        if p > peak:
            peak, hz = p, f
    return {"outcome": "GIUDICATO", "samples": m, "hz": hz,
            "rms": round(rms, 4),
            "purity": round(peak / total_sum, 4) if total_sum > 0 else None}


def pcm_samples(data_v):
    """s16 LITTLE-endian, interleaved (§5.3) — the left channel is taken.

    ⛔ Little-endian is the only declared exception to network order, and
       reading it big-endian does NOT give an error: it gives full-scale noise.  It is
       case 2 of the positive control of `07-b40`.
    """
    outside = []
    for i in range(0, len(data_v) - 3, 2 * CHANNELS):
        v = int.from_bytes(data_v[i:i + 2], "little", signed=True)
        outside.append(v / 32768.0)
    return outside


def main():
    p = argparse.ArgumentParser()
    p.add_argument("file")
    p.add_argument("--hz", type=int, default=440, help="the expected tone")
    p.add_argument("--tolerance-hz", type=int, default=2)
    p.add_argument("--minimum-purity", type=float, default=0.80)
    p.add_argument("--seconds", type=float, default=0,
                   help="how many wall-clock seconds the capture lasted: without it, "
                        "the rhythm is not judged (and it SAYS it is not judged)")
    a = p.parse_args()

    blocks = []
    with open(a.file) as f:
        for row in f:
            row = row.strip()
            if row:
                blocks.append(json.loads(row))

    if not blocks:
        print("⛔ NOTHING TO JUDGE: the file has no blocks.")
        print("   ⚠ And it is not «the audio does not arrive»: it is «I have nothing")
        print("     to look at».  The two cases have two different outcomes on purpose.")
        return 2

    codec = blocks[0]["codec"]
    if any(b["codec"] != codec for b in blocks):
        print("⛔ the codec CHANGES mid-capture: §4.3 negotiates it only once.")
        return 1

    # ── the RHYTHM, from the server's `instant` ─────────────────────────────
    expected_us = BLOCK_US.get(codec)
    instants = [b["instant"] for b in blocks]
    jumps, steps = [], []
    for i in range(1, len(instants)):
        d = instants[i] - instants[i - 1]
        steps.append(d)
        if expected_us and d != expected_us:
            jumps.append((i, d))
    duration_s = (instants[-1] - instants[0] + (expected_us or 0)) / 1e6

    # ── the CONTENT ─────────────────────────────────────────────────────────
    if codec == 2:
        samples = []
        for b in blocks:
            samples.extend(pcm_samples(base64.b64decode(b["byte"])))
        # ⚠ 100 ms of start-up discarded: `CODER.md` §3.5, «a sample taken
        #   at startup says nothing about steady state».
        skip = min(4800, len(samples) // 4)
        g = judge(samples[skip:])
    else:
        g = {"outcome": "NOT JUDGEABLE HERE",
             "reason_text": "Opus packets are judged by the BROWSER, which has the "
                       "decoder: here they would be judged with a different one "
                       "from the user's (error form E10)"}

    print(f"== 07-b42 · {len(blocks)} blocks · codec {codec} "
          f"({'Opus' if codec == 1 else 'PCM'})")
    print(f"   duration according to the SERVER: {duration_s:.3f} s")
    if a.seconds:
        rendered = duration_s / a.seconds
        print(f"   wall clock: {a.seconds:.3f} s  ⇒  yield {rendered * 100:.1f} %")
    else:
        print("   ⚠ the rhythm is NOT judged: `--seconds` is missing, that is how long "
              "the capture lasted")
    print(f"   step between blocks: expected {expected_us} µs · "
          f"minimum {min(steps) if steps else '-'} · "
          f"maximum {max(steps) if steps else '-'} · off step {len(jumps)}")
    if jumps[:5]:
        print(f"   the first jumps: {jumps[:5]}")
    print(f"   signal judgement: {json.dumps(g, ensure_ascii=False)}")

    # ── the VERDICT, and every red line names its rule ──────────────────────
    rossi = []
    if g["outcome"] == "GIUDICATO":
        if abs(g["hz"] - a.hz) > a.tolerance_hz:
            rossi.append(f"the frequency is {g['hz']} Hz and not {a.hz}: "
                         f"§5.3 mandates 48 000 Hz at both ends")
        if g["purity"] is None or g["purity"] < a.minimum_purity:
            rossi.append(f"purity {g['purity']} below {a.minimum_purity}: "
                         f"it is not a tone, it is noise — the v1 defect")
        if g["rms"] < 0.05:
            rossi.append(f"amplitude {g['rms']}: silence, or lost gain")
    if jumps:
        rossi.append(f"{len(jumps)} steps off the {expected_us} µs of §5.3")
    if a.seconds and duration_s / a.seconds < 0.95:
        rossi.append(f"yield {duration_s / a.seconds * 100:.1f} %: the server does NOT "
                     f"produce the audio in real time")

    if rossi:
        print("\n⛔ RED:")
        for r in rossi:
            print(f"   · {r}")
        return 1
    print("\n⭐ GREEN — and it holds for what it looked at: content"
          + (" and rhythm" if a.seconds else ", NOT the rhythm"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
