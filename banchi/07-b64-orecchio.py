#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07-b64-orecchio — THE JUDGE THAT HEARS THE CRACKLES.

⛔ `07-b42` can tell whether what arrives is **a tone** (frequency, amplitude,
   purity).  ⚠ It cannot tell whether that tone has a **gap** inside: half a second
   of signal skipped in the middle of eight seconds moves the purity by a trifle, and
   the verdict stays green.  ⇒ It is exactly the defect R26 describes —
   *«audio that crackles when the desktop works»* — and no tool of the
   project could see it.

⭐ HOW A CRACKLE IS HEARD, and it is not a count.

   A pure sine obeys an EXACT second-order recurrence:

        x[n] = 2·cos(ω)·x[n-1] − x[n-2]          ω = 2π·f/48000

   ⇒ The **residual** r[n] = x[n] − 2cos(ω)x[n-1] + x[n-2] is zero on a perfect
   tone, and is nonzero **only** where the waveform breaks: a phase jump
   (samples lost and stitched back), a silence that begins, a zero fill.
   ⛔ It does not count blocks and does not count bytes: it looks at the SAMPLES, which is rule
   (a) of `07-b43` and the first row of `LEZIONI.md` §2.2.

   ⚠ 16-bit quantisation noise gives |r| of a few LSB — with amplitude
   0.5 (peak 16383) that is ~0.00025 of the amplitude.  The threshold is at **0.02**,
   eighty times above: it does not fire on noise, and it fires on a phase jump
   of little more than one degree.

⛔ AND THE POSITIVE CONTROL LIVES INSIDE THIS FILE (`--certify`): we build
   a perfect tone, remove 137 samples from the middle, and demand that
   the judge sees **that** gap and **only** that.  A judge that cannot
   see the defect it looks for has no right to green (`PIANO.md` §0.3.4).

Usage:
    python3 07-b64-orecchio.py --certify
    python3 07-b64-orecchio.py giro.jsonl [--ref lap.ref.wav] [--hz 440]
"""
import argparse, base64, json, math, os, struct, sys, wave

FREQUENCY = 48000
CHANNELS = 2
STEP_PCM_US = 5000          # §5.3: the PCM block is 5 ms
THRESHOLD = 0.02                # fraction of the peak amplitude

# ⛔⛔ THE MINIMUM PEAK, AND IT IS THE CURE FOR FINDING R7 — 22 August 2026.
#
#      The line was `peak = max(abs(x) ...) or 1.0`, and on samples that were **all
#      zero** the peak became **1.0**: the threshold dropped to 0.02, the residuals
#      were zero, and the judge answered `crackles 0`.
#      ⇒ **The ear judge gave top marks to silence**, which is
#      the error form this phase exists not to commit
#      (`LEZIONI.md` §2.2: the bench stayed green while the audio was broken).
#
# ⭐ The cure is not a smarter `or`: it is that below a certain signal the judge
#    **refuses to judge**.  The quantisation residual of a 16-bit signal
#    is ~4 LSB; for the threshold (2 % of the peak) to sit above that noise
#    a peak of at least ~400 is needed.  Below it, the detector can no longer tell
#    nothing from nothing, and saying so is the only honest answer (`CODER.md` §3.10).
MIN_PEAK = 400           # ~1.2 % of 16-bit full scale

# ⛔⛔⛔ THE BLIND GAP, AND IT IS DECLARED HERE BECAUSE IT CANNOT BE REMOVED.
#
#       A cut of N samples stitches back **in phase** — that is, invisible to the
#       residual — when N x f / 48000 is a whole number of cycles.  With the
#       tone at **440 Hz** and PCM blocks of **240 samples** (5 ms):
#
#           1200 samples = 5 blocks = **11.000 exact cycles** → invisible
#           2400 samples = 10 blocks = 22.000 cycles          → invisible
#           1201 samples                = 11.009 cycles       → seen
#
#       `[M]` 22 August 2026, reproduced on yesterday's judge: 25 ms and 50 ms of
#       vanished audio give **crackles 0**.
#
# ⭐ It is not cured inside the detector — on a perfect sine that cut **leaves
#    no trace in the samples**, and no algorithm can see it.  It is cured
#    with a SECOND LEG that does not look at the waveform but at the **count**: the
#    samples arrived against those expected.  ⇒ `crackles()` accepts
#    `expected_vals`, and the combined verdict looks at both.
#
# ⭐⭐ AND FOR FUTURE SCENES THERE IS A CURE THAT COSTS ONE DIGIT: a tone that
#     never comes to a whole number with the block.  At **443 Hz** a cut of k blocks
#     is 2.215 k cycles, and the first whole number comes at **200 blocks = 1 second**
#     instead of five.  ⚠ The 440 stays as long as the old measurements needs for
#     comparison: changing it now would make yesterday's numbers incomparable.
BLOCK_PCM_SAMPLES = 240    # 5 ms on one channel


# ══════════════════════════════════════════════════════════════════════════
def leftovers(samples, hz):
    """The second-order recurrence.  Returns the residual, sample by sample."""
    w = 2.0 * math.cos(2.0 * math.pi * hz / FREQUENCY)
    outside = [0.0, 0.0]
    for n in range(2, len(samples)):
        outside.append(samples[n] - w * samples[n - 1] + samples[n - 2])
    return outside


def crackles(samples, hz, threshold=THRESHOLD, expected_vals=None):
    """⛔ The events, not the samples: a tear lasts a few samples and
       would count for three or four.  What lies within 5 ms is grouped.

    ⛔ `expected_vals` is the SECOND LEG (R7): how many samples there should have
       been.  The residual does not see a cut that is a multiple of 1200 samples; the
       count does.  ⚠ If it is not passed, the judgement holds only for what the
       waveform can tell, and this outcome declares it."""
    if len(samples) < 64:
        return {"outcome": "NOTHING TO JUDGE", "samples": len(samples)}
    peak = max(abs(x) for x in samples)
    if peak < MIN_PEAK:
        # ⛔ R7: here `crackles 0` used to come out, that is top marks.
        return {"outcome": "SILENCE OR NEARLY — I DO NOT JUDGE",
                "reason_text": "peak %d below the minimum of %d: the detector's "
                          "threshold would end up below the quantisation "
                          "noise, and every answer would be made up"
                          % (peak, MIN_PEAK),
                "samples": len(samples), "peak": peak}
    r = leftovers(samples, hz)
    lim = threshold * peak
    events, last = [], None
    for n, v in enumerate(r):
        if abs(v) > lim:
            if last is not None and n - last["fine"] <= 240:
                last["fine"] = n
                last["jump"] = max(last["jump"], abs(v) / peak)
            else:
                last = {"sample": n, "fine": n, "ms": round(n * 1000.0 / FREQUENCY, 1),
                          "jump": abs(v) / peak}
                events.append(last)
    for e in events:
        e["jump"] = round(e["jump"], 4)
        del e["fine"]
    # ⭐ The typical residual, which tells whether the threshold is far or stuck close
    ordered = sorted(abs(v) for v in r)
    # ⭐ THE SECOND LEG: the count, which sees what the residual cannot.
    missing = None
    blind = None
    if expected_vals:
        missing = int(expected_vals) - len(samples)
        if missing > 0:
            # ⚠ And we say whether that gap would have been invisible to the residual: it is
            #   the information that explains a «zero crackles» next to a
            #   real shortfall, instead of letting them contradict each other in silence.
            blind = abs(missing * hz / FREQUENCY
                        - round(missing * hz / FREQUENCY)) < 0.01
    return {"outcome": "GIUDICATO", "samples": len(samples),
            "campioni_attesi": expected_vals,
            "campioni_mancanti": missing,
            "ammanco_invisibile_al_residuo": blind,
            "peak": round(peak, 1),
            "residuo_mediano_rel": round(ordered[len(ordered) // 2] / peak, 6),
            "residuo_99_rel": round(ordered[int(len(ordered) * 0.99)] / peak, 6),
            "soglia_rel": threshold,
            "crackles": len(events),
            "al_secondo": round(len(events) / (len(samples) / FREQUENCY), 3),
            "dove": events[:40]}


# ══════════════════════════════════════════════════════════════════════════
def da_jsonl(fpath):
    """The client's PCM blocks → the samples of the left channel, and the GAPS
       declared by the `instant` (§6.3: the server's clock, not ours)."""
    samples, instants = [], []
    for r in open(fpath):
        r = r.strip()
        if not r:
            continue
        d = json.loads(r)
        if d.get("codec") != 2:
            continue                       # ⛔ PCM only: Opus is judged by the browser
        b = base64.b64decode(d["byte"])
        n = len(b) // (2 * CHANNELS)
        v = struct.unpack("<%dh" % (n * CHANNELS), b[:n * CHANNELS * 2])
        samples.extend(v[0::CHANNELS])
        instants.append(d["instant"])
    holes = []
    for i in range(1, len(instants)):
        dt = instants[i] - instants[i - 1]
        if dt != STEP_PCM_US:
            holes.append({"block": i, "step_us": dt})
    declared_duration = (instants[-1] - instants[0] + STEP_PCM_US) / 1e6 if instants else 0.0
    return {"samples": samples, "blocks": len(instants), "buchi_istante": holes,
            "durata_dichiarata_s": round(declared_duration, 3),
            "durata_campioni_s": round(len(samples) / FREQUENCY, 3)}


def da_wav(fpath):
    w = wave.open(fpath, "rb")
    n = w.getnframes(); ch = w.getnchannels()
    d = w.readframes(n)
    v = struct.unpack("<%dh" % (len(d) // 2), d)
    return {"samples": list(v[0::ch]), "blocks": None, "buchi_istante": [],
            "durata_dichiarata_s": round(n / w.getframerate(), 3),
            "durata_campioni_s": round(n / w.getframerate(), 3)}


# ══════════════════════════════════════════════════════════════════════════
def full_judgment(data_v, hz, window_s):
    """⛔ The Goertzel window must be a WHOLE number of seconds, or the
       judge of `07-b42` fails a perfect tone (§2.1, the box)."""
    c = data_v["samples"]
    r = {"blocks": data_v["blocks"],
         "durata_dichiarata_s": data_v["durata_dichiarata_s"],
         "durata_campioni_s": data_v["durata_campioni_s"],
         "buchi_istante": len(data_v["buchi_istante"]),
         "buchi_istante_dove": data_v["buchi_istante"][:20]}
    # ⭐ The drift: how many samples are MISSING relative to the declared time.  If the
    #    graph skips a cycle, the samples do not arrive at all and the `instant`
    #    do not notice — this number does.
    if data_v["durata_dichiarata_s"]:
        expected_val = data_v["durata_dichiarata_s"] * FREQUENCY
        r["campioni_mancanti"] = int(expected_val - len(c))
        r["resa_campioni"] = round(len(c) / expected_val, 5) if expected_val else None
    # ⛔ `expected_vals` comes from the server's `instant` (§6.3), not from our
    #    clock: it is the only number that says how many samples there should have been.
    expected_vals = (int(round(data_v["durata_dichiarata_s"] * FREQUENCY))
              if data_v["durata_dichiarata_s"] else None)
    r.update({"crackles": crackles(c, hz, expected_vals=expected_vals)})
    # The certified judge of 07-b42, on a whole window in the middle.
    n = window_s * FREQUENCY
    if len(c) >= n:
        i = (len(c) - n) // 2
        here = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, here)
        import importlib.util
        sp = importlib.util.spec_from_file_location(
            "g42", os.path.join(here, "07-b42-giudice.py"))
        g42 = importlib.util.module_from_spec(sp); sp.loader.exec_module(g42)
        r["tone"] = g42.judge([x / 32768.0 for x in c[i:i + n]])
    else:
        r["tone"] = {"outcome": "NOTHING TO JUDGE",
                     "reason_text": "less than %d s of samples" % window_s}
    return r


# ══════════════════════════════════════════════════════════════════════════
def certify(hz=440):
    """⛔ The positive control, and now there are SEVEN cases.

    ⛔⛔ The two that were missing were found by the reviewer (R7), not me, and they are
         exactly the two that made a false green credible:

           · **silence**, which got top marks;
           · **the 1200-sample cut**, invisible to the residual because it is
             a whole number of cycles (exactly 11.000 at 440 Hz).

    ⭐ And the blind case is NOT declared green because the residual is quiet: it is
       declared green only if the SECOND LEG — the sample count — sees
       it.  A bench that cannot see the defect it looks for has no right to
       green (`PIANO.md` §0.3.4), and a bench that can see it only with another
       tool must say which.
    """
    import random
    amp = 0.5 * 32767

    def sine(n0, n, f=hz):
        return [int(amp * math.sin(2 * math.pi * f * (n0 + k) / FREQUENCY))
                for k in range(n)]

    healthy = sine(0, FREQUENCY * 4)
    cases = []

    def trim(how_many):
        return healthy[:FREQUENCY * 2] + sine(FREQUENCY * 2 + how_many,
                                           FREQUENCY * 2 - how_many)

    #  (name, samples, expected, expected crackles, who must see it)
    cases.append(("0-healthy — a perfect 4 s tone", healthy, None, 0, "nobody: it is healthy"))
    cases.append(("1-gap — 137 samples (2.9 ms) removed and stitched back",
                 trim(137), None, 1, "the residual"))
    cases.append(("2-silence in the middle — 10 ms of zeros",
                 healthy[:FREQUENCY * 2] + [0] * 480 + healthy[FREQUENCY * 2 + 480:],
                 None, 2, "the residual"))

    random.seed(7)
    slots = sorted(random.sample(range(FREQUENCY // 2, FREQUENCY * 7 // 2), 10))
    many, before, jump = [], 0, 0
    for p in slots:
        many += sine(before + jump, p - before)
        before, jump = p, jump + 61
    many += sine(before + jump, len(healthy) - before)
    cases.append(("3-ten tears of 61 samples", many, None, 10, "the residual"))

    # ⛔ R7a — SILENCE.  It used to give `crackles 0`, that is top marks.
    cases.append(("4-⛔ R7a: four seconds of ZEROS", [0] * (FREQUENCY * 4),
                 None, "SILENCE OR NEARLY — I DO NOT JUDGE", "the refusal"))

    # ⛔ R7b — THE BLIND GAP.  The residual does not see it and cannot see it: 1200
    #    samples are exactly 11.000 cycles.  THE COUNT must see it.
    cases.append(("5-⛔ R7b: 1200 samples removed (25 ms = 11.000 cycles)",
                 trim(1200), FREQUENCY * 4, 0, "⭐ the COUNT (1200 missing)"))
    cases.append(("6-⛔ R7b: 2400 samples removed (50 ms = 22.000 cycles)",
                 trim(2400), FREQUENCY * 4, 0, "⭐ the COUNT (2400 missing)"))

    print("⭐ CERTIFICATION OF THE JUDGE — the expected outcome is written FIRST\n")
    green_v = True
    for label_name, c, expected_vals, expected_val, chi in cases:
        e = crackles(c, hz, expected_vals=expected_vals)
        if isinstance(expected_val, str):
            seen_v = e.get("outcome")
            good = seen_v.startswith(expected_val[:12])
        else:
            seen_v = e.get("crackles")
            good = (seen_v == expected_val)
            # ⛔ And for the two blind cases it is not enough for green that the residual
            #    is quiet: the count MUST say how much is missing, or the bench is blind.
            if expected_vals is not None:
                missing = e.get("campioni_mancanti")
                if not missing or missing != expected_vals - len(c):
                    good = False
                    seen_v = "%s (count: %s)" % (seen_v, missing)
                else:
                    seen_v = "%s, and the count sees %d missing (invisible to the "\
                            "residual: %s)" % (seen_v, missing,
                                              e.get("ammanco_invisibile_al_residuo"))
        green_v = green_v and good
        print("  %-52s expected %-6s · %s\n      %s  who sees it: %s"
              % (label_name, expected_val, seen_v, "OK" if good else "⛔ NO", chi))
    print()
    # ⭐ And the control of the CONTROL: at 443 Hz the blind gap is gone.
    #    ⚠ It is not a cure to apply today (it would make yesterday's measurements
    #    incomparable): it is the proof that the diagnosis of the blind gap is right.
    broken443 = ([int(amp * math.sin(2 * math.pi * 443 * k / FREQUENCY))
                 for k in range(FREQUENCY * 2)]
                + [int(amp * math.sin(2 * math.pi * 443 * (k + FREQUENCY * 2 + 1200)
                                      / FREQUENCY))
                   for k in range(FREQUENCY * 2 - 1200)])
    e443 = crackles(broken443, 443)
    ok443 = e443.get("crackles") == 1
    green_v = green_v and ok443
    print("  %-52s expected %-6s · %s  %s"
          % ("7-⭐ the same cut at 443 Hz (11.075 cycles)", 1,
             e443.get("crackles"), "OK" if ok443 else "⛔ NO"))
    print("      ⇒ the blind gap belongs to the TONE, not to the detector: at 443 Hz it disappears")
    print()
    if green_v:
        print("⭐ seven cases out of seven: the judge can see the defect it looks for,")
        print("   and where it CANNOT see it, it says which other tool sees it.")
    else:
        print("⛔ THE JUDGE IS BLIND: none of its greens is to be believed.")
    return 0 if green_v else 3


def primary():
    p = argparse.ArgumentParser()
    p.add_argument("jsonl", nargs="?")
    p.add_argument("--ref", default="", help="the wav of the independent referee (pw-record)")
    p.add_argument("--hz", type=int, default=440)
    p.add_argument("--win", type=int, default=1)
    p.add_argument("--certify", action="store_true")
    a = p.parse_args()
    if a.certify:
        return certify(a.hz)
    if not a.jsonl:
        print("⛔ the JSONL is needed, or --certify", file=sys.stderr); return 2
    outside = {"file": a.jsonl}
    if not os.path.exists(a.jsonl) or os.path.getsize(a.jsonl) == 0:
        # ⛔ CODER.md §3.10: «I read nothing» is an outcome of ITS OWN, not a zero.
        outside["outcome"] = "NOTHING TO JUDGE — the JSONL is missing or empty"
        print(json.dumps(outside, ensure_ascii=False, indent=1)); return 2
    outside["our"] = full_judgment(da_jsonl(a.jsonl), a.hz, a.win)
    if a.ref and os.path.exists(a.ref) and os.path.getsize(a.ref) > 1000:
        outside["arbitro_pw_record"] = full_judgment(da_wav(a.ref), a.hz, a.win)
    elif a.ref:
        outside["arbitro_pw_record"] = "NOTHING TO JUDGE — the wav is missing or empty"
    print(json.dumps(outside, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(primary())
