#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02-cattura-giudica.py — the judge of the PIXELS of sub-phase F2.2.

⛔ WHY IT EXISTS — and it is not «one more check»

The phase 0 tool, `misura-cattura`, is certified and reproduces Mutter's 36 ± 2
frames.  ⛔ But it never looks at the pixels: `su_processo` reads
`type`, `fd`, `chunk->stride`, the damage and the sequence, and puts the buffer back in
the queue without touching `piano->data`.

⇒ **A BLACK AND VALID frame would pass phase 0 with full marks.**
  36 per second, four recycled buffers, partial damage, zero skips: all
  green, and on the screen nothing.  ⛔ And the black is not theoretical — `STUDI.md` §gnome §3.1:
  in headless mode `needs_outputs=false`, so without `--virtual-monitor` the session
  starts **alive, complete and black**; `PIANO.md`, phase 2: *«a black and
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
certified (`PIANO.md` §0.3 point 4).

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
  | block                  | changes** (`LEZIONI.md` §4 trap 8). Without the
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

`LEZIONI.md` §1.9, second rule: *«can this tool find something that is surely
there?»*.  A tool that has never found anything is not clean: it is
uncertified.  At the end of every round the judge builds three frames by itself and
looks at itself:

  the synthetic flag     → must say VERDE
  the full black         → must say ROSSO with the mark FOTOGRAMMA NERO
  the uniform grey       → must say ROSSO with the mark SCENA NON RICONOSCIUTA
                            (⛔ and **not** FOTOGRAMMA NERO: if a judge called
                             a grey black, its worst diagnosis would be
                             wrong precisely in the case where it is needed)

If even one of the three does not answer as written above, the verdict on the
real frame **is not issued**: it exits 2.

---------------------------------------------------------------------------
usage:
  02-cattura-giudica.py --manifesto PREFISSO.json [--quale primo|regime|tutti]
                        [--scena bandiera|ignota] [--json USCITA.json]
  02-cattura-giudica.py --solo-controllo-positivo
"""

import argparse
import json
import math
import os
import sys
import time

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

# ── The thresholds, all in one place and all with the reason next to them ──
#
# ⛔ They are written here and not scattered in the code because a threshold chosen after
#    seeing the number is a widened expectation as long as it holds — the dishonest road
#    that `01-b12-guasti.py` taught us not to take.
SOGLIE = {
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
    # Between `primo` and `regime`: how many sampled pixels must differ for it
    # to be said that the buffer really changed.
    "cambiato_frazione": 0.02,
}

# ⛔ THE SIGNATURE OF THE SEVEN SMPTE BARS, written BEFORE looking at the frame.
#
#    For each band: which channels must be HIGH and which LOW.  They are the
#    75 % bars: grey, yellow, cyan, green, magenta, red, blue.
#    ⚠ Grey has neither highs nor lows: it is the band in which the three channels
#      must be CLOSE TO EACH OTHER, and it is a constraint, not an absence.
BANDE = [
    ("grigio",  [],           [],          True),
    ("giallo",  ["R", "G"],   ["B"],       False),
    ("ciano",   ["G", "B"],   ["R"],       False),
    ("verde",   ["G"],        ["R", "B"],  False),
    ("magenta", ["R", "B"],   ["G"],       False),
    ("rosso",   ["R"],        ["G", "B"],  False),
    ("blu",     ["B"],        ["R", "G"],  False),
]

# The pixel is 32-bit BGRx/BGRA — the only format Mutter delivers
# (`STUDI.md` §gnome §8.3: «Only BGRx and BGRA», R32 confirmed line by line).
BYTE_PER_PIXEL = 4

# ===========================================================================
# ⛔ WHICH MARKS ARE RED ON WHICH FRAME — and it is not leniency
#
# The `primo` frame is taken BEFORE the scene exists: it is the bare desktop,
# just after mounting the virtual monitor.  Requiring the declared scene there — or
# even just requiring that it not be a flat tint — would mean writing a
# test that gives RED on a perfectly healthy bench.  It is item 2 of
# `FASI.md` §00-ambiente: *«the headless test looked for a sentence that, if everything
# goes well, never appears»* — on a healthy session it would have given red
# forever.  A solid-colour GNOME background is plausible, and it is not a defect.
#
# ⭐ BUT BLACK ON `primo` STAYS RED, and it is the point: a BLACK bare desktop is
#    the exact signature of the session without a virtual monitor — alive, complete and
#    black (`STUDI.md` §gnome §3.1, test M9 of §13).  It is the fault this sub-phase
#    exists to see, and on `primo` it shows earlier than elsewhere.
MARCHE_ROSSE = {
    "primo":  {"FOTOGRAMMA NERO", "BYTE NON TORNANO",
               "MISURA DIVERSA DA QUELLA CHIESTA", "FILE ASSENTE"},
    # On `regime` the scene is declared alive: there everything counts.
    "regime": None,   # None = all
}


# ===========================================================================
#  The reading: little is read, and by rows
# ===========================================================================
def luma(r, g, b):
    """Rec.601.  ⚠ The choice of matrix does NOT matter for what is checked:
    the decreasing order of the seven bars holds both with the 601 and with the
    709 weights — it is precisely the design of the bars.  One is chosen and declared."""
    return 0.299 * r + 0.587 * g + 0.114 * b


class Fotogramma:
    """A `.raw` as PipeWire delivered it: rows of `stride` bytes, BGRx."""

    def __init__(self, percorso, larghezza, altezza, stride, colore):
        self.percorso = percorso
        self.larghezza = larghezza
        self.altezza = altezza
        self.stride = stride
        self.colore = colore
        self.byte = os.path.getsize(percorso)
        self.f = open(percorso, "rb")
        self._righe = {}

    def chiudi(self):
        self.f.close()

    def riga(self, y):
        if y not in self._righe:
            self.f.seek(y * self.stride)
            self._righe[y] = self.f.read(self.stride)
        return self._righe[y]

    def pixel(self, x, y):
        """Returns (R, G, B).  ⛔ The byte order is BGRx: B, G, R, x."""
        r = self.riga(y)
        i = x * BYTE_PER_PIXEL
        if i + 3 > len(r):
            return None
        return (r[i + 2], r[i + 1], r[i])


def campiona_griglia(fg, passo_x=24, passo_y=24):
    """A grid over the whole frame: it serves black and uniform.

    ⚠ It samples instead of reading everything: at 1920×1080 the file is 8 MB, and
      reading it whole in Python at every round would make the bench slow without
      answering one more question.  The grid of ~3600 points covers every
      24×24 px square: a black frame has nowhere to
      hide."""
    punti = []
    y = 0
    while y < fg.altezza:
        x = 0
        riga = fg.riga(y)
        while x < fg.larghezza:
            i = x * BYTE_PER_PIXEL
            if i + 3 <= len(riga):
                punti.append((riga[i + 2], riga[i + 1], riga[i]))
            x += passo_x
        y += passo_y
    return punti


def media_e_scarto(valori):
    if not valori:
        return 0.0, 0.0
    m = sum(valori) / len(valori)
    v = sum((x - m) ** 2 for x in valori) / len(valori)
    return m, math.sqrt(v)


# ===========================================================================
#  The checks
# ===========================================================================
def controlla_nero(fg, rilievi, misure):
    punti = campiona_griglia(fg)
    if not punti:
        rilievi.append(("BYTE NON TORNANO",
                        "the grid did not find even one readable pixel: "
                        "stride or height do not match the bytes of the file"))
        return
    lume = [luma(*p) for p in punti]
    media, scarto = media_e_scarto(lume)
    massima = max(lume)
    misure["luma_media"] = round(media, 2)
    misure["luma_massima"] = round(massima, 2)
    misure["luma_scarto"] = round(scarto, 2)
    misure["punti_campionati"] = len(punti)

    if media <= SOGLIE["nero_luma_media"] and massima <= SOGLIE["nero_luma_massima"]:
        rilievi.append(("FOTOGRAMMA NERO",
                        "average luma %.2f (threshold %.1f) and maximum %.2f (threshold %.1f) "
                        "over %d points: the frame is valid and contains nothing. "
                        "It is the worst fault of F2.2 — STUDI.md §gnome §3.1, alive, "
                        "complete and black session"
                        % (media, SOGLIE["nero_luma_media"], massima,
                           SOGLIE["nero_luma_massima"], len(punti))))
        return
    if scarto <= SOGLIE["uniforme_scarto"]:
        rilievi.append(("FOTOGRAMMA UNIFORME",
                        "luma deviation %.2f (threshold %.1f) over %d points: a flat "
                        "tint, not black. ⚠ It is not «black», and it is a different diagnosis: "
                        "a buffer never painted, or filled with grey"
                        % (scarto, SOGLIE["uniforme_scarto"], len(punti))))


def misura_profondita(fg, misure):
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
       Mutter's buffer is BGRx at **8 bits per channel** (`STUDI.md` §gnome §8.3 `[R]`),
       so the levels here are counted out of 256 and not out of 1024.  The question
       this count answers is not «is it ten bits?» — the answer is no by
       construction — but **«is it at least eight real bits, or a poorer path
       promoted?»**.  A channel that took only 64 distinct values,
       all multiples of 4, would be a 6-bit path under an 8-bit label.
    """
    punti = campiona_griglia(fg, 8, 8)
    if not punti:
        return
    for i, canale in enumerate(("R", "G", "B")):
        v = [p[i] for p in punti]
        distinti = sorted(set(v))
        misure.setdefault("profondita", {})[canale] = {
            "minimo": min(v),
            "massimo": max(v),
            "livelli_distinti": len(distinti),
            "livelli_possibili": 256,
            "frazione_multipli_di_2": round(sum(1 for x in v if x % 2 == 0) / len(v), 3),
            "frazione_multipli_di_4": round(sum(1 for x in v if x % 4 == 0) / len(v), 3),
            "frazione_multipli_di_8": round(sum(1 for x in v if x % 8 == 0) / len(v), 3),
        }
    misure["profondita"]["campioni"] = len(punti)
    misure["profondita"]["⚠ come si legge"] = (
        "the count of distinct levels over the WHOLE frame depends on the scene: "
        "seven flat bars have about twenty by construction, and there a "
        "low number says nothing about the bits. The count that means something is the one "
        "on the GRADIENT (profondita_sfumatura), which crosses all 256 levels.")
    # ⛔ AND THE RANGE IS MEASURED, not assumed — even when the producer
    #    declares it.  If all three channels stayed within 16-235 on a scene
    #    that reaches 0 and 255, someone along the road would have applied a
    #    limited range without saying so.  ⚠ It is not a red: it is a measurement, and
    #    it depends on the scene.  It is written, and whoever reads it knows what they are looking at.
    mn = min(misure["profondita"][c]["minimo"] for c in "RGB")
    mx = max(misure["profondita"][c]["massimo"] for c in "RGB")
    misure["profondita"]["range_misurato"] = (
        "suspected LIMITED (no channel below 16 nor above 235)"
        if mn >= 16 and mx <= 235 else "compatible with FULL (min %d, max %d)" % (mn, mx))


def misura_profondita_sfumatura(fg, misure):
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
      (`STUDI.md` §gnome §8.3 `[R]`).  So the question this count answers is
      **«is it at least eight real bits?»** — the expectation is ~256 distinct levels and a
      fraction of multiples of 4 close to 0.25.  ⛔ A fraction of multiples of 4
      equal to 1.000 would say that someone along the road went through 6 bits.
    """
    y0 = int(fg.altezza) - 240
    y1 = int(fg.altezza) - 150
    if y0 < 0:
        return
    v = {"R": [], "G": [], "B": []}
    y = y0
    while y < y1 and y < fg.altezza:
        riga = fg.riga(y)
        x = 0
        while x < fg.larghezza:
            i = x * BYTE_PER_PIXEL
            if i + 3 <= len(riga):
                v["R"].append(riga[i + 2])
                v["G"].append(riga[i + 1])
                v["B"].append(riga[i])
            x += 2
        y += 10
    if not v["R"]:
        return
    d = {"riga_da": y0, "riga_a": y1, "campioni": len(v["R"])}
    for c in "RGB":
        d[c] = {
            "minimo": min(v[c]), "massimo": max(v[c]),
            "livelli_distinti": len(set(v[c])),
            "livelli_possibili": 256,
            "frazione_multipli_di_4": round(
                sum(1 for x in v[c] if x % 4 == 0) / len(v[c]), 3),
        }
    d["⚠ per F2.3"] = (
        "expected on 8 real bits: distinct levels close to 256 and multiples of 4 "
        "close to 0.25. A fraction of 1.000 would say that the road went "
        "through fewer bits than the label declares — it is F2.3-A seen "
        "already at capture.")
    misure["profondita_sfumatura"] = d


def controlla_byte(fg, atteso_larghezza, atteso_altezza, rilievi, misure):
    """⛔ The bytes must add up with the DECLARED stride, not with width*4.

    v1's `cattura.h`, first line: *«the stride is read from the buffer chunk, never
    computed as width*4. The producer aligns the rows as it pleases,
    and deducing it produces slanted images»*.  Here nothing is deduced: what
    the producer declared is compared with the bytes that are there."""
    minimo = fg.larghezza * BYTE_PER_PIXEL
    atteso = fg.stride * fg.altezza
    misure["byte_nel_file"] = fg.byte
    misure["byte_attesi_stride_per_altezza"] = atteso
    misure["stride_dichiarato"] = fg.stride
    misure["stride_minimo_larghezza_per_4"] = minimo

    if fg.stride < minimo:
        rilievi.append(("BYTE NON TORNANO",
                        "declared stride %d, but at least %d bytes are needed for a row of "
                        "%d pixels at 32 bits" % (fg.stride, minimo, fg.larghezza)))
    if fg.byte < atteso:
        rilievi.append(("BYTE NON TORNANO",
                        "the file has %d bytes, %d are needed (stride %d × height %d): "
                        "the frame is TRUNCATED" % (fg.byte, atteso, fg.stride, fg.altezza)))
    elif fg.byte > atteso:
        misure["byte_in_piu"] = fg.byte - atteso

    if atteso_larghezza and (fg.larghezza != atteso_larghezza or fg.altezza != atteso_altezza):
        rilievi.append(("MISURA DIVERSA DA QUELLA CHIESTA",
                        "requested %d×%d, negotiated %d×%d. ⛔ On Mutter it is a fault: the "
                        "virtual monitor is requested and it makes it of the requested size "
                        "(cattura.h, `misura_negoziabile` FALSE). On KWin it would be the "
                        "normal answer — and that is why the two columns stay "
                        "separate instead of being compared mentally"
                        % (atteso_larghezza, atteso_altezza, fg.larghezza, fg.altezza)))


def leggi_bande(fg):
    """Reads the seven bands on the signature row and returns their measurements."""
    y = int(fg.altezza * 0.25)          # inside the zone of the seven bars
    larghezza_banda = fg.larghezza / 7.0
    bande = []
    for i in range(7):
        # ⛔ The CORE of the band is sampled, not the edge: 4:2:0 blurs the
        #    transitions over two pixels per side, and a sample on the edge would measure
        #    the blur instead of the band.
        x0 = int(i * larghezza_banda + larghezza_banda * 0.25)
        x1 = int(i * larghezza_banda + larghezza_banda * 0.75)
        erre, gi, bi = [], [], []
        for x in range(x0, x1, 3):
            p = fg.pixel(x, y)
            if p:
                erre.append(p[0])
                gi.append(p[1])
                bi.append(p[2])
        mr, sr = media_e_scarto(erre)
        mg, sg = media_e_scarto(gi)
        mb, sb = media_e_scarto(bi)
        bande.append({
            "riga": y, "da_x": x0, "a_x": x1, "campioni": len(erre),
            "R": round(mr, 1), "G": round(mg, 1), "B": round(mb, 1),
            "scarto_max": round(max(sr, sg, sb), 2),
            "luma": round(luma(mr, mg, mb), 1),
        })
    return bande


def controlla_firma(fg, rilievi, misure):
    bande = leggi_bande(fg)
    misure["bande"] = bande
    if any(b["campioni"] == 0 for b in bande):
        rilievi.append(("SCENA NON RICONOSCIUTA",
                        "a band has not even one sample: the signature row cannot be read"))
        return

    # F1 — each band uniform inside
    sporche = [(i, b["scarto_max"]) for i, b in enumerate(bande)
               if b["scarto_max"] > SOGLIE["banda_scarto"]]
    # F2 — luma decreases from left to right
    salti = [round(bande[i]["luma"] - bande[i + 1]["luma"], 1) for i in range(6)]
    misure["salti_luma"] = salti
    non_cala = [i for i, s in enumerate(salti) if s < SOGLIE["salto_luma"]]
    # F3 — the channel signature
    sbagliate = []
    for i, (nome, alti, bassi, vicini) in enumerate(BANDE):
        b = bande[i]
        val = {"R": b["R"], "G": b["G"], "B": b["B"]}
        if vicini:
            if max(val.values()) - min(val.values()) > SOGLIE["canale_stacco"]:
                sbagliate.append((nome, "the three channels should be close: %s" % val))
            continue
        piu_basso_alto = min(val[c] for c in alti)
        piu_alto_basso = max(val[c] for c in bassi)
        if piu_basso_alto - piu_alto_basso < SOGLIE["canale_stacco"]:
            sbagliate.append((nome, "%s should dominate over %s, and instead %s"
                              % ("+".join(alti), "+".join(bassi), val)))

    if sporche or non_cala or sbagliate:
        motivi = []
        if sporche:
            motivi.append("F1 — bands not uniform: %s" % sporche)
        if non_cala:
            motivi.append("F2 — luma does not decrease between bands %s (jumps %s, threshold %.1f)"
                          % ([(i, i + 1) for i in non_cala], salti, SOGLIE["salto_luma"]))
        if sbagliate:
            motivi.append("F3 — channel signature: %s" % sbagliate)
        rilievi.append(("SCENA NON RICONOSCIUTA",
                        "the frame is not black but it is not the declared «bandiera» scene. "
                        + " · ".join(motivi)))


def controlla_cambiato(a, b, rilievi, misure):
    """⛔ `primo` and `regime` must be DIFFERENT.

    If they were identical, the producer would be giving us the same buffer
    twice — and it is the exact form of trap 8 of `LEZIONI.md` §4: whoever
    connects to a still desktop stays on black until something moves, and the
    old screen looks the same as a new one."""
    pa = campiona_griglia(a)
    pb = campiona_griglia(b)
    n = min(len(pa), len(pb))
    if n == 0:
        return
    diversi = sum(1 for i in range(n) if pa[i] != pb[i])
    frazione = diversi / n
    misure["punti_campionati"] = n
    misure["punti_diversi_fra_primo_e_regime"] = diversi
    misure["frazione_diversa"] = round(frazione, 4)
    if frazione < SOGLIE["cambiato_frazione"]:
        rilievi.append(("IL BUFFER NON E' CAMBIATO",
                        "between `primo` and `regime` only %d points out of %d differ (%.2f %%, "
                        "threshold %.2f %%): the producer might have given us back the same "
                        "buffer, and an old screen looks the same as a new one"
                        % (diversi, n, frazione * 100, SOGLIE["cambiato_frazione"] * 100)))


# ===========================================================================
#  The judgement of a frame
# ===========================================================================
def giudica_uno(percorso, larghezza, altezza, stride, colore, scena,
                chiesto_larghezza, chiesto_altezza):
    rilievi, misure = [], {}
    if not os.path.exists(percorso):
        return [("FILE ASSENTE", "there is no file to judge: %s" % percorso)], misure, None
    fg = Fotogramma(percorso, larghezza, altezza, stride, colore)
    controlla_byte(fg, chiesto_larghezza, chiesto_altezza, rilievi, misure)
    misura_profondita(fg, misure)
    if scena == "bandiera":
        misura_profondita_sfumatura(fg, misure)
    controlla_nero(fg, rilievi, misure)
    # ⛔ The signature is checked ONLY if the frame is not already black or uniform:
    #    on a black one it would fail too, and three marks for a single cause make
    #    what is one defect look like three.
    marche = [m for m, _ in rilievi]
    if scena == "bandiera" and "FOTOGRAMMA NERO" not in marche:
        controlla_firma(fg, rilievi, misure)
    elif scena != "bandiera":
        misure["firma"] = "not checked: scene «%s», no signature declared" % scena
    return rilievi, misure, fg


# ===========================================================================
#  ⛔ THE POSITIVE CONTROL — runs at the end of EVERY execution
# ===========================================================================
def fabbrica(percorso, larghezza, altezza, stride, che):
    """Builds a BGRx `.raw`: «bandiera», «nero» or «grigio»."""
    colori = [(191, 191, 191), (191, 191, 0), (0, 191, 191), (0, 191, 0),
              (191, 0, 191), (191, 0, 0), (0, 0, 191)]
    with open(percorso, "wb") as f:
        for y in range(altezza):
            riga = bytearray(stride)
            for x in range(larghezza):
                if che == "nero":
                    r = g = b = 0
                elif che == "grigio":
                    r = g = b = 128
                else:
                    r, g, b = colori[min(6, x * 7 // larghezza)]
                i = x * BYTE_PER_PIXEL
                riga[i] = b
                riga[i + 1] = g
                riga[i + 2] = r
                riga[i + 3] = 255
            f.write(riga)


def controllo_positivo(cartella, righe):
    """⛔ Can the tool find something that is surely there, and can it NOT find it?

    Three tests, and the expectation of each is written up here, not after the round.
    ⚠ A small frame is used (280×140): the factory is pure Python and at
      1920×1080 it would cost seconds at every execution, without answering one
      more question — the signature lies in the proportions, not in the size."""
    L, A = 280, 140
    S = L * BYTE_PER_PIXEL
    #  name                what       REQUIRED marks          FORBIDDEN marks
    prove = [
        ("synthetic flag",     "bandiera", [],                        ["FOTOGRAMMA NERO",
                                                                       "SCENA NON RICONOSCIUTA",
                                                                       "FOTOGRAMMA UNIFORME",
                                                                       "BYTE NON TORNANO"]),
        ("full black",         "nero",     ["FOTOGRAMMA NERO"],       []),
        # ⛔ THE TEST THAT COUNTS DOUBLE, and the «forbidden» column is the half that
        #    counts: a judge that called a grey BLACK would get its
        #    worst diagnosis wrong precisely in the case where it is needed.  Requiring only
        #    «it says something red» would not tell it apart.
        ("uniform grey",       "grigio",   ["SCENA NON RICONOSCIUTA",
                                            "FOTOGRAMMA UNIFORME"],   ["FOTOGRAMMA NERO"]),
    ]
    tutto_bene = True
    for nome, che, pretese, vietate in prove:
        p = os.path.join(cartella, "controllo-positivo-%s.raw" % che)
        fabbrica(p, L, A, S, che)
        rilievi, misure, fg = giudica_uno(p, L, A, S, "BGRx", "bandiera", L, A)
        if fg:
            fg.chiudi()
        os.unlink(p)
        marche = [m for m, _ in rilievi]
        mancano = [m for m in pretese if m not in marche]
        di_troppo = [m for m in vietate if m in marche]
        ok = not mancano and not di_troppo
        detto = "said %s" % (marche or "green")
        if mancano:
            detto += " ⛔ missing %s" % mancano
        if di_troppo:
            detto += " ⛔ extra %s" % di_troppo
        righe.append(("  positive control — %s" % nome,
                      "expected %s / forbidden %s, %s"
                      % (pretese or "green", vietate or "—", detto), ok))
        tutto_bene = tutto_bene and ok
    return tutto_bene


# ===========================================================================
def main():
    a = argparse.ArgumentParser(add_help=True)
    a.add_argument("--manifesto")
    a.add_argument("--quale", default="tutti", choices=["primo", "regime", "tutti"])
    a.add_argument("--scena", default="bandiera")
    a.add_argument("--json")
    a.add_argument("--solo-controllo-positivo", action="store_true")
    o = a.parse_args()

    cartella = os.path.dirname(os.path.abspath(o.manifesto)) if o.manifesto else "."
    righe_cp = []

    if o.solo_controllo_positivo:
        ok = controllo_positivo(cartella, righe_cp)
        for t, d, buono in righe_cp:
            print("%s%s%s  %s — %s" % (VERDE if buono else ROSSO, "OK" if buono else "NO",
                                       GRIGIO, t.strip(), d))
        return 0 if ok else 2

    if not o.manifesto:
        print("⛔ --manifesto PREFISSO.json is needed", file=sys.stderr)
        return 2

    try:
        with open(o.manifesto) as f:
            man = json.load(f)
    except Exception as e:
        print("⛔ the manifest cannot be read: %s" % e, file=sys.stderr)
        return 2

    verdetto = {
        "giudice": "02-cattura-giudica.py",
        "quando_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "manifesto": o.manifesto,
        "etichetta": man.get("etichetta"),
        "scena": o.scena,
        "esito_del_produttore": man.get("esito"),
        "fotogrammi": {},
    }

    print("\n\033[1m== the judgement of the pixels — %s ==\033[0m" % man.get("etichetta"))
    print("   producer: %s (exit %s)" % (man.get("esito"), man.get("uscita")))

    # ⛔ ZERO IS NOT FAILURE, and here is the point where they part.
    if man.get("uscita") == 3 or man.get("esito") == "ZERO FOTOGRAMMI":
        print("%s--%s  ZERO FRAMES: there is nothing to judge, and it is not a red.\n"
              "      The stream was active for the whole take and the desktop did not\n"
              "      change: on Mutter it is the declared behaviour (LEZIONI.md §4\n"
              "      trap 8), not a fault. ⚠ But with a scene declared ALIVE it is\n"
              "      heavy information: it means the scene was not painting."
              % (GIALLO, GRIGIO))
        verdetto["verdetto"] = "ZERO FOTOGRAMMI"
        codice = 3
        rilievi_tutti = []
    elif str(man.get("esito", "")).startswith("TIPO DICHIARATO"):
        print("%s--%s  DMA-BUF road: the buffer type is declared, the pixels are NOT\n"
              "      read from here (the descriptor lives on the card). This round\n"
              "      answers «what type is the buffer», not «what is inside»."
              % (GIALLO, GRIGIO))
        verdetto["verdetto"] = "SOLO IL TIPO"
        codice = 3
        rilievi_tutti = []
    else:
        neg = man.get("negoziato", {})
        chi = man.get("chiesto", {})
        larghezza = neg.get("larghezza") or chi.get("larghezza")
        altezza = neg.get("altezza") or chi.get("altezza")
        colore = neg.get("colore", "?")

        # ⛔ THE BUFFER TYPE IS REPORTED WITH WHOEVER SAYS IT, never deduced.
        buf = man.get("buffer", {})
        print("   buffer:     types seen %s · distinct recycled %s"
              % (buf.get("tipi_visti"), buf.get("distinti_riciclati")))
        print("               who says it: %s" % buf.get("chi_lo_dice"))
        print("   negotiated: %s×%s %s, modifier %s"
              % (larghezza, altezza, colore, neg.get("modificatore")))
        print("   requested:  %s×%s %s, road %s"
              % (chi.get("larghezza"), chi.get("altezza"), chi.get("colore"), chi.get("strada")))
        # ⛔ THE THREE THINGS F2.3 ASKS TO BE DECLARED are printed BEFORE the
        #    pixels: whoever reads this round must see them without looking for them.
        cons = man.get("consegna_a_F2_3", {})
        if cons:
            print("\n   \033[1m── what is handed to F2.3, declared ──\033[0m")
            print("      bits per channel: %s   (%s)"
                  % (cons.get("bit_per_canale"), cons.get("bit_per_canale_chi_lo_dice")))
            print("      range:          %s" % cons.get("range"))
            print("      matrix:         %s" % cons.get("matrice"))
            print("      transfer:       %s" % cons.get("trasferimento"))
            print("      primaries:      %s" % cons.get("primari"))
            print("      %s" % cons.get("⛔ F2.3-A"))
            print("      %s" % cons.get("⚠ sulla matrice"))
        for av in man.get("avvertenze", []):
            print("   %s" % av)

        rilievi_tutti = []
        quali = ["primo", "regime"] if o.quale == "tutti" else [o.quale]
        letti = {}
        for q in quali:
            f = man.get(q)
            if not f and q == "regime" and o.scena == "fermo":
                # ⭐ ON THE «fermo» SCENE THE EXPECTATION IS REVERSED, and it must be said here.
                #
                # `fermo` is the declared OPPOSITE CASE: nobody paints, and on
                # Mutter a frame arrives **only if something changes**
                # (`LEZIONI.md` §4 trap 8).  ⇒ Here the absence of `regime` is
                # the right answer, not a finding: calling it red would
                # mean writing a test that gives red on a healthy bench — item
                # 2 of `FASI.md` §00-ambiente.
                #
                # ⛔ And the reverse is a real finding: if on the `fermo` scene
                #    a steady-state frame ARRIVED, it would mean that on the
                #    screen something moves that we did not declare — and
                #    every measurement made on that screen would measure
                #    that too.
                print("%s--%s  ⭐ «fermo» scene: the «regime» is NOT there, and it is the EXPECTATION.\n"
                      "      Nobody was painting, and Mutter delivers only when something\n"
                      "      changes. It is the legitimate zero of trap 8, not a red."
                      % (GIALLO, GRIGIO))
                verdetto["zero_legittimo_confermato"] = True
                continue
            if f and q == "regime" and o.scena == "fermo":
                rilievi_tutti.append((q, "QUALCOSA SI MUOVEVA E NON L'ABBIAMO DICHIARATO",
                                      "on the «fermo» scene no steady-state "
                                      "frame should have arrived, and one did: on the "
                                      "screen something moves that the bench does not know, "
                                      "and every measurement on that screen measures that too"))
                print("%sNO%s  ⛔ on the «fermo» scene a steady-state frame arrived"
                      % (ROSSO, GRIGIO))
            if not f:
                # ⛔ «IT IS NOT THERE» IS NOT «FINE» — and this judge fell for it.
                #
                # On 12 Aug 2026, at the first real round, the producer took
                # only the `primo` frame (the scene was painting on another
                # screen) and this judge printed a yellow line and
                # concluded **VERDE**.  A green bench with the defect alive is the
                # worst of proofs, because it gives confidence (`CODER.md` §4.6).
                #
                # It is form E8: silence mistaken for zero.  The frame
                # that is missing is the one that ANSWERS the question of F2.2 — and
                # without it there is no green to give.
                rilievi_tutti.append((q, "IL FOTOGRAMMA MANCA",
                                      "the producer did not take «%s». If the "
                                      "«regime» is missing, there is no frame with the scene "
                                      "inside: no green is given" % q))
                print("%sNO%s  ⛔ «%s» IS NOT in the manifest, and it is not a harmless absence: "
                      "it is the question of F2.2 left unanswered" % (ROSSO, GRIGIO, q))
                continue
            percorso = f["file"]
            if not os.path.isabs(percorso):
                percorso = os.path.join(cartella, percorso)
            rilievi, misure, fg = giudica_uno(percorso, larghezza, altezza, f["stride"], colore,
                                              o.scena if q == "regime" else "ignota",
                                              chi.get("larghezza"), chi.get("altezza"))
            # ⚠ The signature is required only on the STEADY-STATE frame.  The `primo`
            #   is taken BEFORE the scene exists — requiring the flag there
            #   would be red on a bench that works, which is item 2 of
            #   `FASI.md` §00-ambiente (a test that looks for a sentence that, if
            #   everything goes well, never appears).
            misure["danno"] = f.get("danno")
            misure["seq"] = f.get("seq")
            misure["indice_fra_gli_arrivati"] = f.get("indice_fra_gli_arrivati")
            rosse_q = MARCHE_ROSSE.get(q)
            verdetto["fotogrammi"][q] = {
                "rilievi": [{"marca": m, "perche": d,
                             "rosso": rosse_q is None or m in rosse_q}
                            for m, d in rilievi],
                "misure": misure}
            letti[q] = fg
            print("\n   ── %s ── (damage %s, seq %s, frame no. %s among those arrived)"
                  % (q, f.get("danno"), f.get("seq"), f.get("indice_fra_gli_arrivati")))
            print("      average luma %s · maximum %s · deviation %s over %s points"
                  % (misure.get("luma_media"), misure.get("luma_massima"),
                     misure.get("luma_scarto"), misure.get("punti_campionati")))
            print("      bytes %s (expected %s = stride %s × height %s)"
                  % (misure.get("byte_nel_file"), misure.get("byte_attesi_stride_per_altezza"),
                     misure.get("stride_dichiarato"), altezza))
            pr = misure.get("profondita")
            if pr:
                print("      depth measured on %d samples — %s"
                      % (pr["campioni"], pr["range_misurato"]))
                for c in "RGB":
                    d = pr[c]
                    print("        %s  min %-4d max %-4d distinct levels %-4d/256"
                          "  multiples of 2 %.3f · of 4 %.3f · of 8 %.3f"
                          % (c, d["minimo"], d["massimo"], d["livelli_distinti"],
                             d["frazione_multipli_di_2"], d["frazione_multipli_di_4"],
                             d["frazione_multipli_di_8"]))
            sf = misure.get("profondita_sfumatura")
            if sf:
                print("      ⭐ on the GRADIENT (rows %d-%d, %d samples) — the count that"
                      " means something about the bits:" % (sf["riga_da"], sf["riga_a"],
                                                        sf["campioni"]))
                for c in "RGB":
                    print("        %s  distinct levels %-4d/256   multiples of 4 %.3f"
                          "   (expected on 8 real bits: ~256 and ~0.250)"
                          % (c, sf[c]["livelli_distinti"], sf[c]["frazione_multipli_di_4"]))
            if "bande" in misure:
                for nome, b in zip([n for n, _, _, _ in BANDE], misure["bande"]):
                    print("      %-8s R%-6.1f G%-6.1f B%-6.1f  luma %-6.1f  scarto %.2f"
                          % (nome, b["R"], b["G"], b["B"], b["luma"], b["scarto_max"]))
            rosse = MARCHE_ROSSE.get(q)
            for m, d in rilievi:
                # ⛔ A warning is NOT a red, and the difference is printed: two
                #    outcomes under the same colour would be two measurements under the
                #    same label (form E2).
                if rosse is None or m in rosse:
                    print("      %sNO%s  %s — %s" % (ROSSO, GRIGIO, m, d))
                    rilievi_tutti.append((q, m, d))
                else:
                    print("      %s⚠%s   %s — %s" % (GIALLO, GRIGIO, m, d))
                    print("            (warning, not red: on the «%s» the scene is not there"
                          " yet — see MARCHE_ROSSE)" % q)
            if not rilievi:
                print("      %sOK%s  no finding" % (VERDE, GRIGIO))

        # ⛔ And the comparison between the two, which neither of the two alone can give.
        if letti.get("primo") and letti.get("regime"):
            rc, mc = [], {}
            controlla_cambiato(letti["primo"], letti["regime"], rc, mc)
            verdetto["confronto_primo_regime"] = {
                "rilievi": [{"marca": m, "perche": d} for m, d in rc], "misure": mc}
            print("\n   ── primo against regime ──")
            print("      differing points %s out of %s (%s %%)"
                  % (mc.get("punti_diversi_fra_primo_e_regime"),
                     mc.get("punti_campionati", "—"),
                     round((mc.get("frazione_diversa") or 0) * 100, 2)))
            for m, d in rc:
                print("      %sNO%s  %s — %s" % (ROSSO, GRIGIO, m, d))
                rilievi_tutti.append(("confronto", m, d))
            if not rc:
                print("      %sOK%s  the buffer changed: it is not an old screen"
                      % (VERDE, GRIGIO))

        # ⭐ And the answer to the question the documents contradict each other on:
        #    is a frame with PARTIAL damage nevertheless WHOLE?
        reg = man.get("regime") or {}
        if reg.get("danno") == "parziale":
            firma_ok = not any(q == "regime" and m == "SCENA NON RICONOSCIUTA"
                               for q, m, _ in rilievi_tutti)
            nero = any(q == "regime" and m == "FOTOGRAMMA NERO" for q, m, _ in rilievi_tutti)
            verdetto["danno_parziale_ma_intero"] = bool(firma_ok and not nero)
            print("\n   ⭐ the steady-state frame carries PARTIAL damage and the scene %s"
                  % ("IS SEEN WHOLE ⇒ the buffer is whole (STUDI.md §gnome §8.1: blit of the whole "
                     "framebuffer), not a diff (v1's cattura.h)"
                     if firma_ok and not nero else
                     "is NOT seen whole ⇒ suspicion falls on the diff of cattura.h"))

        for fg in letti.values():
            if fg:
                fg.chiudi()
        codice = 1 if rilievi_tutti else 0
        verdetto["verdetto"] = "ROSSO" if rilievi_tutti else "VERDE"

    # ── ⛔ THE POSITIVE CONTROL, AT THE END OF EVERY EXECUTION ─────────────
    print("\n\033[1m== the positive control of the tool ==\033[0m")
    ok_cp = controllo_positivo(cartella, righe_cp)
    for t, d, buono in righe_cp:
        print("%s%s%s%s — %s" % (VERDE if buono else ROSSO, t, GRIGIO, " OK" if buono else " NO", d))
    verdetto["controllo_positivo"] = {"passato": ok_cp,
                                      "prove": [{"prova": t.strip(), "esito": d, "ok": b}
                                                for t, d, b in righe_cp]}
    if not ok_cp:
        print("\n%s⛔ THE JUDGE IS NOT CERTIFIED%s: the positive control did not pass.\n"
              "   The verdict on the real frame is NOT issued — a tool that cannot\n"
              "   find what is surely there is not clean, it is uncertified\n"
              "   (LEZIONI.md §1.9, second rule)." % (ROSSO, GRIGIO))
        verdetto["verdetto"] = "GIUDICE NON CERTIFICATO"
        codice = 2

    if o.json:
        with open(o.json, "w") as f:
            json.dump(verdetto, f, ensure_ascii=False, indent=1)

    print("\n\033[1mVERDICT: %s\033[0m (exit %d)" % (verdetto["verdetto"], codice))
    return codice


if __name__ == "__main__":
    sys.exit(main())
