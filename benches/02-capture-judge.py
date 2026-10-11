#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02-capture-judge.py — the judge of the PIXELS of sub-phase F2.2.

⛔ WHY IT EXISTS — and it is not «one more check»

The phase 0 tool, `misura-cattura`, is certified and reproduces Mutter's 36 ± 2
frames.  ⛔ But it never looks at the pixels: `on_process` reads
`type`, `fd`, `chunk->stride`, the damage and the sequence, and puts the buffer back in
the queue without touching `piano->data`.

⇒ **A BLACK AND VALID frame would pass phase 0 with full marks.**
  36 per second, four recycled buffers, partial damage, zero skips: all
  green, and on the screen nothing.  ⛔ And the black is not theoretical — `STUDIES.md` §gnome §3.1:
  in headless mode `needs_outputs=false`, so without `--virtual-monitor` the session
  starts **alive, complete and black**; `PLAN.md`, phase 2: *«a black and
  perfectly alive session is the thing that gets mistaken for a capture defect, and
  you search for half a day on the wrong side»*.

This program is the only thing in the project that opens the frame and looks.

---------------------------------------------------------------------------
⛔ WHY IT SITS IN A FILE SEPARATE FROM WHOEVER CAPTURES

So that the fault can be injected **into the pixels**.  The producer writes a
`.raw` and a manifest; the judge reads them.  Between the two one can slip a
black frame of the very same size, with the very same manifest —
which is exactly the worst fault of this sub-phase — without touching either
the producer or the judge.  ⭐ A bench that cannot be broken cannot be
certified (`PLAN.md` §0.3 point 4).

---------------------------------------------------------------------------
⛔ THE SCENE IS DECLARED, AND THE SIGNATURE IS CHOSEN TO SURVIVE COLOUR

`CODER.md` §3.2: the scene is declared and always moves.  Phase 0 used
`weston-simple-egl -f -o` — which moves very well but **is not
recognisable in the pixels**: a spinning triangle has no signature, and F2.6 (the pixel
comparison) would have nothing to compare.

The F2.2 scene is therefore **«bandiera»**: the seven SMPTE bars full screen,
still, plus a white block that slides along the bottom at every frame.

  | why the seven bars     | a **still** signature, which lives in the pixels and not in
  |                        | time: a still image is judged on it
  | why the sliding        | Mutter delivers a frame **only if something
  | block                  | changes** (`LESSONS.md` §4 trap 8). Without the
  |                        | block, on a still desktop nothing would arrive
  |                        | and zero would be legitimate — but useless
  | why the block sits     | so the signature **does not depend on the instant** at which
  | in a corner            | the frame was taken, and two different rounds can
  |                        | be compared

⭐ AND THE SIGNATURE IS NOT A LIST OF ABSOLUTE COLOURS, on purpose.  Between ffmpeg,
mpv, 4:2:0 and the colour matrix (601 against 709) the absolute RGB values
shift by tens of units, and a judge that required `(191,191,0)` would be
red on a perfect scene.  Instead **three properties that no
colour matrix can invert** are checked:

  F1  seven bands, each one **uniform inside**
  F2  the **luma decreases** from left to right on all seven — it is the very
      design of the SMPTE bars, and it holds both with the 601 and with the 709 weights
  F3  the **channel signature** of each band (which channel dominates): grey,
      yellow, cyan, green, magenta, red, blue

⛔ A black frame fails all three.  A uniform grey fails F2 and F3
   but **passes F1**: and that is on purpose, because that is how «black» is told from
   «it is not the scene» from «it is the scene».  Three outcomes, not two.

---------------------------------------------------------------------------
⛔ ZERO IS NOT FAILURE (`REVIEWER.md` §1 point 4)

  exit 0  green: the frame is there, it is the one requested, and it contains the scene
  exit 1  red: there is a frame and something does not add up. The mark says what
  exit 3  ⭐ there is nothing to judge — zero frames, declared as such
          by the producer. It is a result, not a fault
  exit 2  the JUDGE failed: unreadable file, crooked manifest, or
          ⛔ **the positive control at the end did not pass** — in which case
          this program declares itself NOT CERTIFIED and judges nothing

---------------------------------------------------------------------------
⛔ THE POSITIVE CONTROL RUNS AT EVERY EXECUTION, AT THE END

`LESSONS.md` §1.9, second rule: *«can this tool find something that is surely
there?»*.  A tool that has never found anything is not clean: it is
uncertified.  At the end of every round the judge builds three frames by itself and
looks at itself:

  the synthetic flag     → must say VERDE
  the full black         → must say ROSSO with the mark BLACK FRAME
  the uniform grey       → must say ROSSO with the mark SCENE NOT RECOGNISED
                            (⛔ and **not** BLACK FRAME: if a judge called
                             a grey black, its worst diagnosis would be
                             wrong precisely in the case where it is needed)

If even one of the three does not answer as written above, the verdict on the
real frame **is not issued**: it exits 2.

---------------------------------------------------------------------------
usage:
  02-capture-judge.py --manifest PREFISSO.json [--which first|regime|tutti]
                        [--scene bandiera|ignota] [--json USCITA.json]
  02-capture-judge.py --positive-check-only
"""

import argparse
import json
import math
import os
import sys
import time

GREEN, RED, YELLOW, GRAY = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

# ── The thresholds, all in one place and all with the reason next to them ──
#
# ⛔ They are written here and not scattered in the code because a threshold chosen after
#    seeing the number is a widened expectation as long as it holds — the dishonest road
#    that `01-b12-guasti.py` taught us not to take.
THRESHOLDS = {
    # Below this average luma (0-255) the frame is called BLACK.  Real
    # black is 0; margin is left for a black that is not perfectly black (a
    # session that draws a very dark background stays a fault to be seen).
    "nero_luma_media": 8.0,
    # …and together: no sampled pixel beyond this threshold.  Two conditions,
    # not one: a black frame with a single white pointer is not «black»,
    # and it is a different piece of information.
    "nero_luma_massima": 24.0,
    # Below this standard deviation over the whole sampled frame,
    # the image is UNIFORM (a flat tint).  Black and uniform are two
    # different marks.
    "uniforme_scarto": 3.0,
    # Inside a band: maximum deviation allowed on each channel.  4:2:0 and
    # encoding noise dirty things, but inside a full band few
    # levels remain.
    "banda_scarto": 12.0,
    # Between two adjacent bands: luma must drop at least this much.  The
    # smallest jump in the SMPTE bars is green→magenta, ~33 levels with the
    # 601 weights and ~82 with the 709; 8 is broad and stays well below.
    "salto_luma": 8.0,
    # The channel signature: how much a «dominant» channel must stand out from an
    # «off» one for it to be said that it dominates.
    "canale_stacco": 40.0,
    # Between `first` and `regime`: how many sampled pixels must differ for it
    # to be said that the buffer really changed.
    "cambiato_frazione": 0.02,
}

# ⛔ THE SIGNATURE OF THE SEVEN SMPTE BARS, written BEFORE looking at the frame.
#
#    For each band: which channels must be HIGH and which LOW.  They are the
#    75 % bars: grey, yellow, cyan, green, magenta, red, blue.
#    ⚠ Grey has neither highs nor lows: it is the band in which the three channels
#      must be CLOSE TO EACH OTHER, and it is a constraint, not an absence.
BANDS = [
    ("grigio",  [],           [],          True),
    ("giallo",  ["R", "G"],   ["B"],       False),
    ("ciano",   ["G", "B"],   ["R"],       False),
    ("green",   ["G"],        ["R", "B"],  False),
    ("magenta", ["R", "B"],   ["G"],       False),
    ("red",   ["R"],        ["G", "B"],  False),
    ("blu",     ["B"],        ["R", "G"],  False),
]

# The pixel is 32-bit BGRx/BGRA — the only format Mutter delivers
# (`STUDIES.md` §gnome §8.3: «Only BGRx and BGRA», R32 confirmed line by line).
BYTE_PER_PIXEL = 4

# ===========================================================================
# ⛔ WHICH MARKS ARE RED ON WHICH FRAME — and it is not leniency
#
# The `first` frame is taken BEFORE the scene exists: it is the bare desktop,
# just after mounting the virtual monitor.  Requiring the declared scene there — or
# even just requiring that it not be a flat tint — would mean writing a
# test that gives RED on a perfectly healthy bench.  It is item 2 of
# `PHASES.md` §00-ambiente: *«the headless test looked for a sentence that, if everything
# goes well, never appears»* — on a healthy session it would have given red
# forever.  A solid-colour GNOME background is plausible, and it is not a defect.
#
# ⭐ BUT BLACK ON `first` STAYS RED, and it is the point: a BLACK bare desktop is
#    the exact signature of the session without a virtual monitor — alive, complete and
#    black (`STUDIES.md` §gnome §3.1, test M9 of §13).  It is the fault this sub-phase
#    exists to see, and on `first` it shows earlier than elsewhere.
RED_MARKS = {
    "first":  {"BLACK FRAME", "BYTES DO NOT ADD UP",
               "SIZE DIFFERENT FROM THE ONE REQUESTED", "FILE MISSING"},
    # On `regime` the scene is declared alive: there everything counts.
    "steady": None,   # None = all
}


# ===========================================================================
#  The reading: little is read, and by rows
# ===========================================================================
def luma(r, g, b):
    """Rec.601.  ⚠ The choice of matrix does NOT matter for what is checked:
    the decreasing order of the seven bars holds both with the 601 and with the
    709 weights — it is precisely the design of the bars.  One is chosen and declared."""
    return 0.299 * r + 0.587 * g + 0.114 * b


class Frame:
    """A `.raw` as PipeWire delivered it: rows of `stride` bytes, BGRx."""

    def __init__(self, fpath, width, height, stride, color):
        self.fpath = fpath
        self.width = width
        self.height = height
        self.stride = stride
        self.color = color
        self.byte = os.path.getsize(fpath)
        self.f = open(fpath, "rb")
        self._lines = {}

    def close(self):
        self.f.close()

    def line(self, y):
        if y not in self._lines:
            self.f.seek(y * self.stride)
            self._lines[y] = self.f.read(self.stride)
        return self._lines[y]

    def pixel(self, x, y):
        """Returns (R, G, B).  ⛔ The byte order is BGRx: B, G, R, x."""
        r = self.line(y)
        i = x * BYTE_PER_PIXEL
        if i + 3 > len(r):
            return None
        return (r[i + 2], r[i + 1], r[i])


def sample_grid(fg, stride_x=24, stride_y=24):
    """A grid over the whole frame: it serves black and uniform.

    ⚠ It samples instead of reading everything: at 1920×1080 the file is 8 MB, and
      reading it whole in Python at every round would make the bench slow without
      answering one more question.  The grid of ~3600 points covers every
      24×24 px square: a black frame has nowhere to
      hide."""
    points = []
    y = 0
    while y < fg.height:
        x = 0
        line = fg.line(y)
        while x < fg.width:
            i = x * BYTE_PER_PIXEL
            if i + 3 <= len(line):
                points.append((line[i + 2], line[i + 1], line[i]))
            x += stride_x
        y += stride_y
    return points


def mean_and_dev(values):
    if not values:
        return 0.0, 0.0
    m = sum(values) / len(values)
    v = sum((x - m) ** 2 for x in values) / len(values)
    return m, math.sqrt(v)


# ===========================================================================
#  The checks
# ===========================================================================
def check_black(fg, findings, measurements):
    points = sample_grid(fg)
    if not points:
        findings.append(("BYTES DO NOT ADD UP",
                        "the grid did not find even one readable pixel: "
                        "stride or height do not match the bytes of the file"))
        return
    lumas = [luma(*p) for p in points]
    media, gap = mean_and_dev(lumas)
    max_dims = max(lumas)
    measurements["luma_media"] = round(media, 2)
    measurements["luma_massima"] = round(max_dims, 2)
    measurements["luma_scarto"] = round(gap, 2)
    measurements["punti_campionati"] = len(points)

    if media <= THRESHOLDS["nero_luma_media"] and max_dims <= THRESHOLDS["nero_luma_massima"]:
        findings.append(("BLACK FRAME",
                        "average luma %.2f (threshold %.1f) and maximum %.2f (threshold %.1f) "
                        "over %d points: the frame is valid and contains nothing. "
                        "It is the worst fault of F2.2 — STUDIES.md §gnome §3.1, alive, "
                        "complete and black session"
                        % (media, THRESHOLDS["nero_luma_media"], max_dims,
                           THRESHOLDS["nero_luma_massima"], len(points))))
        return
    if gap <= THRESHOLDS["uniforme_scarto"]:
        findings.append(("UNIFORM FRAME",
                        "luma deviation %.2f (threshold %.1f) over %d points: a flat "
                        "tint, not black. ⚠ It is not «black», and it is a different diagnosis: "
                        "a buffer never painted, or filled with grey"
                        % (gap, THRESHOLDS["uniforme_scarto"], len(points))))


def measure_depth(fg, measurements):
    """⛔ REAL BITS ARE COUNTED, not read on the label.

    Asked by F2.3 (encoding) as a **seam**, and the fault behind it
    is the one F2.3 calls **F2.3-A**:

      *if capture delivers 8 bits, the whole chain stays green and the label
      keeps saying Main10.*  ⛔ Nobody notices by looking at the image,
      because it comes out fine anyway.

    The number that unmasks it, `[M]` from F2.3: **877 distinct levels and 0.25 of
    multiples of 4** on a real 10-bit frame, against **220 levels and
    1.000** on one passed through 8 bits.

    ⭐ Here the count is done **already at capture**, so the defect has a defendant
       BEFORE entering the encoder.  ⚠ And with a difference that must be said:
       Mutter's buffer is BGRx at **8 bits per channel** (`STUDIES.md` §gnome §8.3 `[R]`),
       so the levels here are counted out of 256 and not out of 1024.  The question
       this count answers is not «is it ten bits?» — the answer is no by
       construction — but **«is it at least eight real bits, or a poorer path
       promoted?»**.  A channel that took only 64 distinct values,
       all multiples of 4, would be a 6-bit path under an 8-bit label.
    """
    points = sample_grid(fg, 8, 8)
    if not points:
        return
    for i, channel in enumerate(("R", "G", "B")):
        v = [p[i] for p in points]
        distinct = sorted(set(v))
        measurements.setdefault("profondita", {})[channel] = {
            "minimum": min(v),
            "maximum": max(v),
            "distinct_levels": len(distinct),
            "possible_levels": 256,
            "fraction_multiples_of_2": round(sum(1 for x in v if x % 2 == 0) / len(v), 3),
            "fraction_multiples_of_4": round(sum(1 for x in v if x % 4 == 0) / len(v), 3),
            "fraction_multiples_of_8": round(sum(1 for x in v if x % 8 == 0) / len(v), 3),
        }
    measurements["profondita"]["samples"] = len(points)
    measurements["profondita"]["⚠ come si legge"] = (
        "the count of distinct levels over the WHOLE frame depends on the scene: "
        "seven flat bars have about twenty by construction, and there a "
        "low number says nothing about the bits. The count that means something is the one "
        "on the GRADIENT (profondita_sfumatura), which crosses all 256 levels.")
    # ⛔ AND THE RANGE IS MEASURED, not assumed — even when the producer
    #    declares it.  If all three channels stayed within 16-235 on a scene
    #    that reaches 0 and 255, someone along the road would have applied a
    #    limited range without saying so.  ⚠ It is not a red: it is a measurement, and
    #    it depends on the scene.  It is written, and whoever reads it knows what they are looking at.
    mn = min(measurements["profondita"][c]["minimum"] for c in "RGB")
    mx = max(measurements["profondita"][c]["maximum"] for c in "RGB")
    measurements["profondita"]["measured_range"] = (
        "suspected LIMITED (no channel below 16 nor above 235)"
        if mn >= 16 and mx <= 235 else "compatible with FULL (min %d, max %d)" % (mn, mx))


def measure_gradient_depth(fg, measurements):
    """⭐ THE BIT COUNT IS DONE WHERE THE BITS SHOW: on the gradient.

    The «bandiera» scene carries, under the bars, a **ramp from black to white as wide
    as the screen**: 1920 px for 256 levels, that is every level repeated ~7.5
    times.  ⛔ It is the only part of the image on which «how many distinct levels» is
    a question about the BITS and not about the scene.

    The fault this number unmasks is **F2.3-A**: if the chain goes through 8
    bits and the label says Main10, the image comes out fine anyway and everything stays
    green.  The F2.3 number, `[M]`: **877 distinct levels and 0.25 of multiples of
    4** at real 10 bits, against **220 and 1.000** after a passage through 8 bits.

    ⚠ Here the full scale is 256 and not 1024, because Mutter's buffer is BGRx
      (`STUDIES.md` §gnome §8.3 `[R]`).  So the question this count answers is
      **«is it at least eight real bits?»** — the expectation is ~256 distinct levels and a
      fraction of multiples of 4 close to 0.25.  ⛔ A fraction of multiples of 4
      equal to 1.000 would say that someone along the road went through 6 bits.
    """
    y0 = int(fg.height) - 240
    y1 = int(fg.height) - 150
    if y0 < 0:
        return
    v = {"R": [], "G": [], "B": []}
    y = y0
    while y < y1 and y < fg.height:
        line = fg.line(y)
        x = 0
        while x < fg.width:
            i = x * BYTE_PER_PIXEL
            if i + 3 <= len(line):
                v["R"].append(line[i + 2])
                v["G"].append(line[i + 1])
                v["B"].append(line[i])
            x += 2
        y += 10
    if not v["R"]:
        return
    d = {"line_from": y0, "line_a": y1, "samples": len(v["R"])}
    for c in "RGB":
        d[c] = {
            "minimum": min(v[c]), "maximum": max(v[c]),
            "distinct_levels": len(set(v[c])),
            "possible_levels": 256,
            "fraction_multiples_of_4": round(
                sum(1 for x in v[c] if x % 4 == 0) / len(v[c]), 3),
        }
    d["⚠ per F2.3"] = (
        "expected on 8 real bits: distinct levels close to 256 and multiples of 4 "
        "close to 0.25. A fraction of 1.000 would say that the road went "
        "through fewer bits than the label declares — it is F2.3-A seen "
        "already at capture.")
    measurements["gradient_depth"] = d


def check_byte(fg, expected_width, expected_height, findings, measurements):
    """⛔ The bytes must add up with the DECLARED stride, not with width*4.

    v1's `capture.h`, first line: *«the stride is read from the buffer chunk, never
    computed as width*4. The producer aligns the rows as it pleases,
    and deducing it produces slanted images»*.  Here nothing is deduced: what
    the producer declared is compared with the bytes that are there."""
    minimum = fg.width * BYTE_PER_PIXEL
    expected = fg.stride * fg.height
    measurements["byte_nel_file"] = fg.byte
    measurements["byte_attesi_stride_per_altezza"] = expected
    measurements["stride_dichiarato"] = fg.stride
    measurements["stride_minimo_larghezza_per_4"] = minimum

    if fg.stride < minimum:
        findings.append(("BYTES DO NOT ADD UP",
                        "declared stride %d, but at least %d bytes are needed for a row of "
                        "%d pixels at 32 bits" % (fg.stride, minimum, fg.width)))
    if fg.byte < expected:
        findings.append(("BYTES DO NOT ADD UP",
                        "the file has %d bytes, %d are needed (stride %d × height %d): "
                        "the frame is TRUNCATED" % (fg.byte, expected, fg.stride, fg.height)))
    elif fg.byte > expected:
        measurements["byte_in_piu"] = fg.byte - expected

    if expected_width and (fg.width != expected_width or fg.height != expected_height):
        findings.append(("SIZE DIFFERENT FROM THE ONE REQUESTED",
                        "requested %d×%d, negotiated %d×%d. ⛔ On Mutter it is a fault: the "
                        "virtual monitor is requested and it makes it of the requested size "
                        "(capture.h, `misura_negoziabile` FALSE). On KWin it would be the "
                        "normal answer — and that is why the two columns stay "
                        "separate instead of being compared mentally"
                        % (expected_width, expected_height, fg.width, fg.height)))


def read_bands(fg):
    """Reads the seven bands on the signature row and returns their measurements."""
    y = int(fg.height * 0.25)          # inside the zone of the seven bars
    stripe_width = fg.width / 7.0
    bands = []
    for i in range(7):
        # ⛔ The CORE of the band is sampled, not the edge: 4:2:0 blurs the
        #    transitions over two pixels per side, and a sample on the edge would measure
        #    the blur instead of the band.
        x0 = int(i * stripe_width + stripe_width * 0.25)
        x1 = int(i * stripe_width + stripe_width * 0.75)
        ri, gi, bi = [], [], []
        for x in range(x0, x1, 3):
            p = fg.pixel(x, y)
            if p:
                ri.append(p[0])
                gi.append(p[1])
                bi.append(p[2])
        mr, sr = mean_and_dev(ri)
        mg, sg = mean_and_dev(gi)
        mb, sb = mean_and_dev(bi)
        bands.append({
            "line": y, "da_x": x0, "a_x": x1, "samples": len(ri),
            "R": round(mr, 1), "G": round(mg, 1), "B": round(mb, 1),
            "scarto_max": round(max(sr, sg, sb), 2),
            "luma": round(luma(mr, mg, mb), 1),
        })
    return bands


def check_signature(fg, findings, measurements):
    bands = read_bands(fg)
    measurements["bands"] = bands
    if any(b["samples"] == 0 for b in bands):
        findings.append(("SCENE NOT RECOGNISED",
                        "a band has not even one sample: the signature row cannot be read"))
        return

    # F1 — each band uniform inside
    dirty = [(i, b["scarto_max"]) for i, b in enumerate(bands)
               if b["scarto_max"] > THRESHOLDS["banda_scarto"]]
    # F2 — luma decreases from left to right
    jumps = [round(bands[i]["luma"] - bands[i + 1]["luma"], 1) for i in range(6)]
    measurements["salti_luma"] = jumps
    not_decreasing = [i for i, s in enumerate(jumps) if s < THRESHOLDS["salto_luma"]]
    # F3 — the channel signature
    wrong = []
    for i, (name, high, low, neighbors) in enumerate(BANDS):
        b = bands[i]
        val = {"R": b["R"], "G": b["G"], "B": b["B"]}
        if neighbors:
            if max(val.values()) - min(val.values()) > THRESHOLDS["canale_stacco"]:
                wrong.append((name, "the three channels should be close: %s" % val))
            continue
        lowest_high = min(val[c] for c in high)
        highest_low = max(val[c] for c in low)
        if lowest_high - highest_low < THRESHOLDS["canale_stacco"]:
            wrong.append((name, "%s should dominate over %s, and instead %s"
                              % ("+".join(high), "+".join(low), val)))

    if dirty or not_decreasing or wrong:
        reasons = []
        if dirty:
            reasons.append("F1 — bands not uniform: %s" % dirty)
        if not_decreasing:
            reasons.append("F2 — luma does not decrease between bands %s (jumps %s, threshold %.1f)"
                          % ([(i, i + 1) for i in not_decreasing], jumps, THRESHOLDS["salto_luma"]))
        if wrong:
            reasons.append("F3 — channel signature: %s" % wrong)
        findings.append(("SCENE NOT RECOGNISED",
                        "the frame is not black but it is not the declared «bandiera» scene. "
                        + " · ".join(reasons)))


def check_changed(a, b, findings, measurements):
    """⛔ `first` and `regime` must be DIFFERENT.

    If they were identical, the producer would be giving us the same buffer
    twice — and it is the exact form of trap 8 of `LESSONS.md` §4: whoever
    connects to a still desktop stays on black until something moves, and the
    old screen looks the same as a new one."""
    pa = sample_grid(a)
    pb = sample_grid(b)
    n = min(len(pa), len(pb))
    if n == 0:
        return
    different = sum(1 for i in range(n) if pa[i] != pb[i])
    fraction = different / n
    measurements["punti_campionati"] = n
    measurements["punti_diversi_fra_primo_e_regime"] = different
    measurements["frazione_diversa"] = round(fraction, 4)
    if fraction < THRESHOLDS["cambiato_frazione"]:
        findings.append(("THE BUFFER DID NOT CHANGE",
                        "between `first` and `regime` only %d points out of %d differ (%.2f %%, "
                        "threshold %.2f %%): the producer might have given us back the same "
                        "buffer, and an old screen looks the same as a new one"
                        % (different, n, fraction * 100, THRESHOLDS["cambiato_frazione"] * 100)))


# ===========================================================================
#  The judgement of a frame
# ===========================================================================
def judge_one(fpath, width, height, stride, color, scene,
                requested_width, requested_height):
    findings, measurements = [], {}
    if not os.path.exists(fpath):
        return [("FILE MISSING", "there is no file to judge: %s" % fpath)], measurements, None
    fg = Frame(fpath, width, height, stride, color)
    check_byte(fg, requested_width, requested_height, findings, measurements)
    measure_depth(fg, measurements)
    if scene == "flag":
        measure_gradient_depth(fg, measurements)
    check_black(fg, findings, measurements)
    # ⛔ The signature is checked ONLY if the frame is not already black or uniform:
    #    on a black one it would fail too, and three marks for a single cause make
    #    what is one defect look like three.
    marks = [m for m, _ in findings]
    if scene == "flag" and "BLACK FRAME" not in marks:
        check_signature(fg, findings, measurements)
    elif scene != "flag":
        measurements["firma"] = "not checked: scene «%s», no signature declared" % scene
    return findings, measurements, fg


# ===========================================================================
#  ⛔ THE POSITIVE CONTROL — runs at the end of EVERY execution
# ===========================================================================
def factory(fpath, width, height, stride, desc):
    """Builds a BGRx `.raw`: «bandiera», «nero» or «grigio»."""
    colors = [(191, 191, 191), (191, 191, 0), (0, 191, 191), (0, 191, 0),
              (191, 0, 191), (191, 0, 0), (0, 0, 191)]
    with open(fpath, "wb") as f:
        for y in range(height):
            line = bytearray(stride)
            for x in range(width):
                if desc == "nero":
                    r = g = b = 0
                elif desc == "grigio":
                    r = g = b = 128
                else:
                    r, g, b = colors[min(6, x * 7 // width)]
                i = x * BYTE_PER_PIXEL
                line[i] = b
                line[i + 1] = g
                line[i + 2] = r
                line[i + 3] = 255
            f.write(line)


def positive_check(folder, lines):
    """⛔ Can the tool find something that is surely there, and can it NOT find it?

    Three tests, and the expectation of each is written up here, not after the round.
    ⚠ A small frame is used (280×140): the factory is pure Python and at
      1920×1080 it would cost seconds at every execution, without answering one
      more question — the signature lies in the proportions, not in the size."""
    L, A = 280, 140
    S = L * BYTE_PER_PIXEL
    #  name                what       REQUIRED marks          FORBIDDEN marks
    prove = [
        ("synthetic flag",     "flag", [],                        ["BLACK FRAME",
                                                                       "SCENE NOT RECOGNISED",
                                                                       "UNIFORM FRAME",
                                                                       "BYTES DO NOT ADD UP"]),
        ("full black",         "nero",     ["BLACK FRAME"],           []),
        # ⛔ THE TEST THAT COUNTS DOUBLE, and the «forbidden» column is the half that
        #    counts: a judge that called a grey BLACK would get its
        #    worst diagnosis wrong precisely in the case where it is needed.  Requiring only
        #    «it says something red» would not tell it apart.
        ("uniform grey",       "grigio",   ["SCENE NOT RECOGNISED",
                                            "UNIFORM FRAME"],       ["BLACK FRAME"]),
    ]
    all_well = True
    for name, desc, claims, forbidden in prove:
        p = os.path.join(folder, "controllo-positivo-%s.raw" % desc)
        factory(p, L, A, S, desc)
        findings, measurements, fg = judge_one(p, L, A, S, "BGRx", "flag", L, A)
        if fg:
            fg.close()
        os.unlink(p)
        marks = [m for m, _ in findings]
        missing = [m for m in claims if m not in marks]
        unwanted = [m for m in forbidden if m in marks]
        ok = not missing and not unwanted
        said = "said %s" % (marks or "green")
        if missing:
            said += " ⛔ missing %s" % missing
        if unwanted:
            said += " ⛔ extra %s" % unwanted
        lines.append(("  positive control — %s" % name,
                      "expected %s / forbidden %s, %s"
                      % (claims or "green", forbidden or "—", said), ok))
        all_well = all_well and ok
    return all_well


# ===========================================================================
def main():
    a = argparse.ArgumentParser(add_help=True)
    a.add_argument("--manifest")
    a.add_argument("--which", default="all", choices=["first", "steady", "all"])
    a.add_argument("--scene", default="flag")
    a.add_argument("--json")
    a.add_argument("--positive-check-only", action="store_true")
    o = a.parse_args()

    folder = os.path.dirname(os.path.abspath(o.manifest)) if o.manifest else "."
    lines_cp = []

    if o.positive_check_only:
        ok = positive_check(folder, lines_cp)
        for t, d, good in lines_cp:
            print("%s%s%s  %s — %s" % (GREEN if good else RED, "OK" if good else "NO",
                                       GRAY, t.strip(), d))
        return 0 if ok else 2

    if not o.manifest:
        print("⛔ --manifest PREFISSO.json is needed", file=sys.stderr)
        return 2

    try:
        with open(o.manifest) as f:
            man = json.load(f)
    except Exception as e:
        print("⛔ the manifest cannot be read: %s" % e, file=sys.stderr)
        return 2

    verdict = {
        "giudice": "02-capture-judge.py",
        "when_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "manifest": o.manifest,
        "label": man.get("label"),
        "scene": o.scene,
        "esito_del_produttore": man.get("outcome"),
        "frames": {},
    }

    print("\n\033[1m== the judgement of the pixels — %s ==\033[0m" % man.get("label"))
    print("   producer: %s (exit %s)" % (man.get("outcome"), man.get("exit")))

    # ⛔ ZERO IS NOT FAILURE, and here is the point where they part.
    if man.get("exit") == 3 or man.get("outcome") in ("ZERO FRAMES", "ZERO FOTOGRAMMI"):
        print("%s--%s  ZERO FRAMES: there is nothing to judge, and it is not a red.\n"
              "      The stream was active for the whole take and the desktop did not\n"
              "      change: on Mutter it is the declared behaviour (LESSONS.md §4\n"
              "      trap 8), not a fault. ⚠ But with a scene declared ALIVE it is\n"
              "      heavy information: it means the scene was not painting."
              % (YELLOW, GRAY))
        verdict["verdict"] = "ZERO FRAMES"
        code = 3
        all_findings = []
    elif str(man.get("outcome", "")).startswith(("TYPE DECLARED", "TYPE DICHIARATO")):
        print("%s--%s  DMA-BUF road: the buffer type is declared, the pixels are NOT\n"
              "      read from here (the descriptor lives on the card). This round\n"
              "      answers «what type is the buffer», not «what is inside»."
              % (YELLOW, GRAY))
        verdict["verdict"] = "ONLY THE TYPE"
        code = 3
        all_findings = []
    else:
        neg = man.get("negotiated", {})
        chi = man.get("requested", {})
        width = neg.get("width") or chi.get("width")
        height = neg.get("height") or chi.get("height")
        color = neg.get("color", "?")

        # ⛔ THE BUFFER TYPE IS REPORTED WITH WHOEVER SAYS IT, never deduced.
        buf = man.get("buffer", {})
        print("   buffer:     types seen %s · distinct recycled %s"
              % (buf.get("types_seen"), buf.get("distinct_recycled")))
        print("               who says it: %s" % buf.get("claimed_by"))
        print("   negotiated: %s×%s %s, modifier %s"
              % (width, height, color, neg.get("modifier")))
        print("   requested:  %s×%s %s, road %s"
              % (chi.get("width"), chi.get("height"), chi.get("color"), chi.get("route")))
        # ⛔ THE THREE THINGS F2.3 ASKS TO BE DECLARED are printed BEFORE the
        #    pixels: whoever reads this round must see them without looking for them.
        cons = man.get("delivery_to_F2_3", {})
        if cons:
            print("\n   \033[1m── what is handed to F2.3, declared ──\033[0m")
            print("      bits per channel: %s   (%s)"
                  % (cons.get("bits_per_channel"), cons.get("bits_per_channel_claimed_by")))
            print("      range:          %s" % cons.get("range"))
            print("      matrix:         %s" % cons.get("matrix"))
            print("      transfer:       %s" % cons.get("transfer"))
            print("      primaries:      %s" % cons.get("primaries"))
            print("      %s" % cons.get("⛔ F2.3-A"))
            print("      %s" % cons.get("⚠ sulla matrice"))
        for av in man.get("avvertenze", []):
            print("   %s" % av)

        all_findings = []
        which_ones = ["first", "steady"] if o.which == "all" else [o.which]
        readings = {}
        for q in which_ones:
            f = man.get(q)
            if not f and q == "steady" and o.scene == "still":
                # ⭐ ON THE «stopped» SCENE THE EXPECTATION IS REVERSED, and it must be said here.
                #
                # `stopped` is the declared OPPOSITE CASE: nobody paints, and on
                # Mutter a frame arrives **only if something changes**
                # (`LESSONS.md` §4 trap 8).  ⇒ Here the absence of `regime` is
                # the right answer, not a finding: calling it red would
                # mean writing a test that gives red on a healthy bench — item
                # 2 of `PHASES.md` §00-ambiente.
                #
                # ⛔ And the reverse is a real finding: if on the `stopped` scene
                #    a steady-state frame ARRIVED, it would mean that on the
                #    screen something moves that we did not declare — and
                #    every measurement made on that screen would measure
                #    that too.
                print("%s--%s  ⭐ «fermo» scene: the «regime» is NOT there, and it is the EXPECTATION.\n"
                      "      Nobody was painting, and Mutter delivers only when something\n"
                      "      changes. It is the legitimate zero of trap 8, not a red."
                      % (YELLOW, GRAY))
                verdict["zero_legittimo_confermato"] = True
                continue
            if f and q == "steady" and o.scene == "still":
                all_findings.append((q, "SOMETHING WAS MOVING AND WE DID NOT DECLARE IT",
                                      "on the «fermo» scene no steady-state "
                                      "frame should have arrived, and one did: on the "
                                      "screen something moves that the bench does not know, "
                                      "and every measurement on that screen measures that too"))
                print("%sNO%s  ⛔ on the «fermo» scene a steady-state frame arrived"
                      % (RED, GRAY))
            if not f:
                # ⛔ «IT IS NOT THERE» IS NOT «FINE» — and this judge fell for it.
                #
                # On 12 Aug 2026, at the first real round, the producer took
                # only the `first` frame (the scene was painting on another
                # screen) and this judge printed a yellow line and
                # concluded **GREEN**.  A green bench with the defect alive is the
                # worst of proofs, because it gives confidence (`CODER.md` §4.6).
                #
                # It is form E8: silence mistaken for zero.  The frame
                # that is missing is the one that ANSWERS the question of F2.2 — and
                # without it there is no green to give.
                all_findings.append((q, "THE FRAME IS MISSING",
                                      "the producer did not take «%s». If the "
                                      "«regime» is missing, there is no frame with the scene "
                                      "inside: no green is given" % q))
                print("%sNO%s  ⛔ «%s» IS NOT in the manifest, and it is not a harmless absence: "
                      "it is the question of F2.2 left unanswered" % (RED, GRAY, q))
                continue
            fpath = f["file"]
            if not os.path.isabs(fpath):
                fpath = os.path.join(folder, fpath)
            findings, measurements, fg = judge_one(fpath, width, height, f["stride"], color,
                                              o.scene if q == "steady" else "unknown",
                                              chi.get("width"), chi.get("height"))
            # ⚠ The signature is required only on the STEADY-STATE frame.  The `first`
            #   is taken BEFORE the scene exists — requiring the flag there
            #   would be red on a bench that works, which is item 2 of
            #   `PHASES.md` §00-ambiente (a test that looks for a sentence that, if
            #   everything goes well, never appears).
            measurements["damage"] = f.get("damage")
            measurements["seq"] = f.get("seq")
            measurements["indice_fra_gli_arrivati"] = f.get("indice_fra_gli_arrivati")
            red_q = RED_MARKS.get(q)
            verdict["frames"][q] = {
                "findings": [{"mark": m, "why": d,
                             "red": red_q is None or m in red_q}
                            for m, d in findings],
                "measurements": measurements}
            readings[q] = fg
            print("\n   ── %s ── (damage %s, seq %s, frame no. %s among those arrived)"
                  % (q, f.get("damage"), f.get("seq"), f.get("indice_fra_gli_arrivati")))
            print("      average luma %s · maximum %s · deviation %s over %s points"
                  % (measurements.get("luma_media"), measurements.get("luma_massima"),
                     measurements.get("luma_scarto"), measurements.get("punti_campionati")))
            print("      bytes %s (expected %s = stride %s × height %s)"
                  % (measurements.get("byte_nel_file"), measurements.get("byte_attesi_stride_per_altezza"),
                     measurements.get("stride_dichiarato"), height))
            pr = measurements.get("profondita")
            if pr:
                print("      depth measured on %d samples — %s"
                      % (pr["samples"], pr["measured_range"]))
                for c in "RGB":
                    d = pr[c]
                    print("        %s  min %-4d max %-4d distinct levels %-4d/256"
                          "  multiples of 2 %.3f · of 4 %.3f · of 8 %.3f"
                          % (c, d["minimum"], d["maximum"], d["distinct_levels"],
                             d["fraction_multiples_of_2"], d["fraction_multiples_of_4"],
                             d["fraction_multiples_of_8"]))
            sf = measurements.get("gradient_depth")
            if sf:
                print("      ⭐ on the GRADIENT (rows %d-%d, %d samples) — the count that"
                      " means something about the bits:" % (sf["line_from"], sf["line_a"],
                                                        sf["samples"]))
                for c in "RGB":
                    print("        %s  distinct levels %-4d/256   multiples of 4 %.3f"
                          "   (expected on 8 real bits: ~256 and ~0.250)"
                          % (c, sf[c]["distinct_levels"], sf[c]["fraction_multiples_of_4"]))
            if "bande" in measurements:
                for name, b in zip([n for n, _, _, _ in BANDS], measurements["bande"]):
                    print("      %-8s R%-6.1f G%-6.1f B%-6.1f  luma %-6.1f  scarto %.2f"
                          % (name, b["R"], b["G"], b["B"], b["luma"], b["scarto_max"]))
            red_marks = RED_MARKS.get(q)
            for m, d in findings:
                # ⛔ A warning is NOT a red, and the difference is printed: two
                #    outcomes under the same colour would be two measurements under the
                #    same label (form E2).
                if red_marks is None or m in red_marks:
                    print("      %sNO%s  %s — %s" % (RED, GRAY, m, d))
                    all_findings.append((q, m, d))
                else:
                    print("      %s⚠%s   %s — %s" % (YELLOW, GRAY, m, d))
                    print("            (warning, not red: on the «%s» the scene is not there"
                          " yet — see RED_MARKS)" % q)
            if not findings:
                print("      %sOK%s  no finding" % (GREEN, GRAY))

        # ⛔ And the comparison between the two, which neither of the two alone can give.
        if readings.get("first") and readings.get("steady"):
            rc, mc = [], {}
            check_changed(readings["first"], readings["steady"], rc, mc)
            verdict["confronto_primo_regime"] = {
                "findings": [{"mark": m, "why": d} for m, d in rc], "measurements": mc}
            print("\n   ── primo against regime ──")
            print("      differing points %s out of %s (%s %%)"
                  % (mc.get("punti_diversi_fra_primo_e_regime"),
                     mc.get("punti_campionati", "—"),
                     round((mc.get("frazione_diversa") or 0) * 100, 2)))
            for m, d in rc:
                print("      %sNO%s  %s — %s" % (RED, GRAY, m, d))
                all_findings.append(("confronto", m, d))
            if not rc:
                print("      %sOK%s  the buffer changed: it is not an old screen"
                      % (GREEN, GRAY))

        # ⭐ And the answer to the question the documents contradict each other on:
        #    is a frame with PARTIAL damage nevertheless WHOLE?
        reg = man.get("steady") or {}
        if reg.get("damage") == "partial":
            signature_ok = not any(q == "steady" and m == "SCENE NOT RECOGNISED"
                               for q, m, _ in all_findings)
            nero = any(q == "steady" and m == "BLACK FRAME" for q, m, _ in all_findings)
            verdict["partial_damage_but_whole"] = bool(signature_ok and not nero)
            print("\n   ⭐ the steady-state frame carries PARTIAL damage and the scene %s"
                  % ("IS SEEN WHOLE ⇒ the buffer is whole (STUDIES.md §gnome §8.1: blit of the whole "
                     "framebuffer), not a diff (v1's capture.h)"
                     if signature_ok and not nero else
                     "is NOT seen whole ⇒ suspicion falls on the diff of capture.h"))

        for fg in readings.values():
            if fg:
                fg.close()
        code = 1 if all_findings else 0
        verdict["verdict"] = "RED" if all_findings else "GREEN"

    # ── ⛔ THE POSITIVE CONTROL, AT THE END OF EVERY EXECUTION ─────────────
    print("\n\033[1m== the positive control of the tool ==\033[0m")
    ok_cp = positive_check(folder, lines_cp)
    for t, d, good in lines_cp:
        print("%s%s%s%s — %s" % (GREEN if good else RED, t, GRAY, " OK" if good else " NO", d))
    verdict["positive_control"] = {"passato": ok_cp,
                                      "prove": [{"prova": t.strip(), "outcome": d, "ok": b}
                                                for t, d, b in lines_cp]}
    if not ok_cp:
        print("\n%s⛔ THE JUDGE IS NOT CERTIFIED%s: the positive control did not pass.\n"
              "   The verdict on the real frame is NOT issued — a tool that cannot\n"
              "   find what is surely there is not clean, it is uncertified\n"
              "   (LESSONS.md §1.9, second rule)." % (RED, GRAY))
        verdict["verdict"] = "JUDGE NOT CERTIFIED"
        code = 2

    if o.json:
        with open(o.json, "w") as f:
            json.dump(verdict, f, ensure_ascii=False, indent=1)

    print("\n\033[1mVERDICT: %s\033[0m (exit %d)" % (verdict["verdict"], code))
    return code


if __name__ == "__main__":
    sys.exit(main())
