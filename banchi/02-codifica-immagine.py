#!/usr/bin/env python3
"""02-codifica-immagine.py — the known image of F2.3, and the tools that judge it.

    python3 02-codifica-immagine.py --generate <folder>
    python3 02-codifica-immagine.py --levels <file.yuv> [--row N]
    python3 02-codifica-immagine.py --compare <a.yuv> <b.yuv>
    python3 02-codifica-immagine.py --selftest <folder>   ⛔ the positive control

===========================================================================
⛔ WHY IT EXISTS — and it is not «a test image was needed»

Sub-phase F2.3 must prove that out of the captured frame comes a
**Main10** HEVC stream a browser can decode.  ⚠ And the real trap of 10
bits is that **nobody notices by looking at the pixels**:

  ⛔ *if the encoder accepts 10 bits but the chain delivers it 8, the
     decoded frame comes out FINE anyway.*  The banding on the gradients
     is there, but it is the same banding an eye would blame on the bitrate.

It is exactly form **E1** of `REVIEWER.md` §2 — necessary mistaken for
sufficient — applied to colour: «`ffprobe` says Main 10» is **necessary**
for the 10 bits to be there, and it is not at all **sufficient**.  A label is
written by the encoder reading its own arguments; the **pixel values** are not.

⭐ Hence the image this file generates is not decorative: it is built
   so that a single number, read on the decoded pixels, tells
   **«real 10 bits»** from **«declared 10 bits»**.

===========================================================================
⛔ THE NUMBER THAT DISTINGUISHES, AND THE OPPOSITE CASE WRITTEN BEFOREHAND

`LEZIONI.md` §1.11 rule 1: *for every indirect test write what the
opposite case would show.  If one cannot say what the opposite would look like,
the test does not distinguish and must be changed.*

The **ramp** occupies the first 256 rows: luma rises by **exactly 1
LSB at 10 bits** every time the abscissa advances enough, from 64 to 940 (the two
ends of the limited range at 10 bits).  Over 1920 columns **all 877
integer levels** are touched, none excluded.

    | quantity, read on row 128 of the Y plane     | real 10 bits | disguised 8 bits |
    |---|---|---|
    | distinct levels                              | **877**      | **220**          |
    | fraction of values that are multiples of 4   | **~0.251**   | **1.000**        |

⭐ The reason for the second row: an 8-bit sample promoted to 10 is worth
   `v << 2`, that is it is **always** a multiple of 4.  On a real 10-bit ramp the
   multiples of 4 instead happen by chance, one in four.  ⛔ **1.000 against
   0.251 is not a nuance: it is a switch**, and it does not need an
   eye to be read.

⚠ And the opposite case is not a reasoning: this file **produces** it.
`sorgente-8in10.yuv` is the very same image passed through 8 bits and
put back in a 10-bit container (`(v >> 2) << 2`).  If the bench cannot
tell that file from the real one, the bench **is not measuring the 10 bits** — and
then the green of the whole round is worth nothing (`REVIEWER.md` §1 point 3).

===========================================================================
⛔ WHY THE BIT TEST IS DONE LOSSLESS, AND NOT AT THE REAL BITRATE

At a realistic bitrate HEVC **destroys a 1-LSB ramp** by construction:
it is the last bit of a detail nobody sees, and it is the first one the
quantiser throws away.  A bench that measured distinct levels at CRF 20
would find few levels **even on a perfect 10-bit chain**, and the red
would not tell *«the chain is 8-bit»* from *«the bitrate was low»* — two
opposite diagnoses under the same label, that is **E2**.

⇒ Two rounds, declared and separate:

  **round A — the chain** (`lossless=1`): it must come back **identical byte by
  byte**.  Here the 10 bits are measured without ambiguity, because there is no
  loss to blame.
  **round B — the rendering** (real CRF): here *how much* is lost is measured.  The banding
  seen here belongs to the bitrate, not to the depth, and it is round A that
  lets one say so.

===========================================================================
WHAT IS IN THE IMAGE, AND WHICH DEFECT EACH PIECE UNMASKS

    rows    0- 255  ⭐ the 1-LSB ramp, grey                → the 10 bits, and the banding
    rows  256- 511  soft colour gradients                 → the banding, for the eye
    rows  512- 767  ⭐ saturated red text on saturated blue → fringed text (4:2:0)
    rows  768-1023  checkerboards and 1, 2, 3 px bars     → the chroma cut
    rows 1024-1079  flat reference patches                → noise on a still background

⚠ The text is drawn with a 5x7 font **written in here**, not taken from the
  system: a system font is a dependency that changes from machine to
  machine, and two rounds with two different fonts cannot be compared.

⚠ **And the fringing of the text is NOT the encoder's fault.** It is born earlier,
  when the full-resolution chroma is reduced to 4:2:0 — which is the choice
  of `DECISIONI.md` §2.3.  Lossless round A serves this too: it proves
  that the encoder is **transparent**, and therefore that all the fringing
  measured is the price of 4:2:0.  ⭐ It is a number given to whoever one day
  reopens the `[?]` of 4:4:4.

===========================================================================
THE COLOUR, DECLARED

BT.709, **limited range**, 10 bits: Y in [64, 940], chroma in [64, 960] around
512.  It is not a detail: whoever compares pixels must know which one is
black, or `LEZIONI.md` §1.9 becomes «the bench measured something else».
"""

import argparse
import json
import os
import sys

# ── The geometry, declared once only ───────────────────────────────────────
WIDTH = 1920
HEIGHT = 1080

# The bands, in rows.  They are INCLUSIVE on the left and EXCLUSIVE on the right.
BAND_RAMP = (0, 256)
BAND_GRADIENTS = (256, 512)
BAND_TEXT = (512, 768)
BAND_END = (768, 1024)
BAND_PATCHES = (1024, 1080)

# ⛔ The row on which the 10-bit test is read.  It is inside the ramp, and it is
#    declared here because the bench and the report must cite THE SAME one.
RAMP_LINE = 128

# The limited range at 10 bits.
Y_MIN, Y_MAX = 64, 940
CHROMA_ZERO = 512

# The expectations, written BEFORE the round (PIANO.md §0.3 rule 4).
EXPECTED_REAL_LEVELS = 877          # 940 - 64 + 1
EXPECTED_LEVELS_8IN10 = 220         # from 64 to 940 in steps of 4
EXPECTED_M4_8IN10 = 1.0
THRESHOLD_M4_TRUE = 0.50              # ⛔ above this threshold we shout «disguised 8 bits»


# ── The 5x7 font, written here so that it does not change from one machine to another ───
FONT = {
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "i": ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#..#", "..##."),
    ":": (".....", "..#..", "..#..", ".....", "..#..", "..#..", "....."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}
SENTENCE = "REMOTIX 10 bit 4:2:0"


def rgb_a_ycbcr(r, g, b):
    """BT.709, limited range, 10 bits.  r/g/b in [0,1].  Returns integers."""
    yf = 0.2126 * r + 0.7152 * g + 0.0722 * b
    cb = (b - yf) / 1.8556
    cr = (r - yf) / 1.5748
    y = int(round(64 + 876 * yf))
    u = int(round(CHROMA_ZERO + 896 * cb))
    v = int(round(CHROMA_ZERO + 896 * cr))
    limit = lambda x: max(4, min(1019, x))
    return limit(y), limit(u), limit(v)


def build():
    """The image, in three full-resolution planes (the chroma is subsampled afterwards).

    It works at 4:4:4 and reduces to 4:2:0 at the end, with the average of the 2x2 block.
    ⚠ It is that average that produces the fringing of the text: it is done here, in
      the open, instead of leaving it to a tool — so whoever reads knows
      exactly where the defect they then measure is born.
    """
    Y = [[0] * WIDTH for _ in range(HEIGHT)]
    U = [[CHROMA_ZERO] * WIDTH for _ in range(HEIGHT)]
    V = [[CHROMA_ZERO] * WIDTH for _ in range(HEIGHT)]

    # ── the 1-LSB ramp ─────────────────────────────────────────────────────
    ramp_line = [Y_MIN + (c * (Y_MAX - Y_MIN)) // (WIDTH - 1)
                  for c in range(WIDTH)]
    for r in range(*BAND_RAMP):
        Y[r] = list(ramp_line)

    # ── soft colour gradients: blue → cyan, and green → yellow ─────────────
    a, b_ = BAND_GRADIENTS
    meta = (a + b_) // 2
    for r in range(a, b_):
        towards_yellow = r >= meta
        for c in range(WIDTH):
            t = c / (WIDTH - 1)
            if towards_yellow:
                y, u, v = rgb_a_ycbcr(t * 0.85, 0.85, 0.05)
            else:
                y, u, v = rgb_a_ycbcr(0.05, t * 0.85, 0.85)
            Y[r][c], U[r][c], V[r][c] = y, u, v

    # ── the text: saturated red on saturated blue, at three magnifications ─
    a, b_ = BAND_TEXT
    background = rgb_a_ycbcr(0.05, 0.05, 0.90)
    ink = rgb_a_ycbcr(0.90, 0.06, 0.06)
    for r in range(a, b_):
        for c in range(WIDTH):
            Y[r][c], U[r][c], V[r][c] = background
    row = a + 8
    for scale_v in (1, 2, 3, 4):
        draw_sentence(Y, U, V, SENTENCE, 8, row, scale_v, ink)
        row += 7 * scale_v + 10

    # ── the fine detail: checkerboards and 1, 2, 3 px bars ────────────────
    a, b_ = BAND_END
    nero = rgb_a_ycbcr(0.02, 0.02, 0.02)
    white = rgb_a_ycbcr(0.95, 0.95, 0.95)
    red = rgb_a_ycbcr(0.90, 0.05, 0.05)
    blue = rgb_a_ycbcr(0.05, 0.05, 0.90)
    fourth = (b_ - a) // 4
    for r in range(a, b_):
        i = (r - a) // fourth
        for c in range(WIDTH):
            if i == 0:                       # 1px white/black checkerboard
                p = white if (r + c) % 2 == 0 else nero
            elif i == 1:                     # 1px red/blue checkerboard ⭐
                p = red if (r + c) % 2 == 0 else blue
            elif i == 2:                     # vertical bars 1,2,3 px
                per = 12
                x = c % per
                p = red if x in (0, 2, 3, 5, 6, 7) else blue
            else:                            # horizontal bars 1,2,3 px
                per = 12
                x = (r - a) % per
                p = white if x in (0, 2, 3, 5, 6, 7) else nero
            Y[r][c], U[r][c], V[r][c] = p

    # ── the flat reference patches ────────────────────────────────────────
    a, b_ = BAND_PATCHES
    patches = [rgb_a_ycbcr(x, x, x) for x in (0.0, 0.18, 0.5, 0.75, 1.0)]
    largo = WIDTH // len(patches)
    for r in range(a, b_):
        for c in range(WIDTH):
            Y[r][c], U[r][c], V[r][c] = patches[min(c // largo, len(patches) - 1)]

    return Y, U, V


def draw_sentence(Y, U, V, sentence, x0, y0, scale_v, color):
    for k, ch in enumerate(sentence):
        g = FONT.get(ch)
        if g is None:
            continue
        bx = x0 + k * 6 * scale_v
        for gy in range(7):
            for gx in range(5):
                if g[gy][gx] != "#":
                    continue
                for dy in range(scale_v):
                    for right in range(scale_v):
                        y, x = y0 + gy * scale_v + dy, bx + gx * scale_v + right
                        if 0 <= y < HEIGHT and 0 <= x < WIDTH:
                            Y[y][x], U[y][x], V[y][x] = color


def subsamples(P):
    """4:4:4 → 4:2:0 with the average of the 2x2 block.  ⚠ Here the fringing is born."""
    outside = []
    for r in range(0, HEIGHT, 2):
        row = []
        for c in range(0, WIDTH, 2):
            row.append((P[r][c] + P[r][c + 1] + P[r + 1][c] + P[r + 1][c + 1] + 2) // 4)
        outside.append(row)
    return outside


def in_byte(piano):
    b = bytearray()
    for row in piano:
        for v in row:
            b += int(v).to_bytes(2, "little")
    return bytes(b)


def write_yuv(fpath, Y, U, V):
    with open(fpath, "wb") as f:
        f.write(in_byte(Y))
        f.write(in_byte(U))
        f.write(in_byte(V))


def a_8_bit(data_v):
    """(v >> 2) << 2 on every 16-bit little-endian sample.

    ⛔ It is the OPPOSITE CASE, produced and not reasoned: the same image passed
       through 8 bits and put back in a 10-bit container.  An eye cannot tell it apart.
    """
    outside = bytearray(data_v)
    for i in range(0, len(outside), 2):
        v = outside[i] | (outside[i + 1] << 8)
        v = (v >> 2) << 2
        outside[i] = v & 0xFF
        outside[i + 1] = (v >> 8) & 0xFF
    return bytes(outside)


# ── The judging tools ──────────────────────────────────────────────────────

def read_y_row(fpath, row):
    """Row `row` of the Y plane.  ⛔ It checks the file SIZE first.

    A short file read with `seek` gives no error: it gives bytes of another row, or
    nothing.  «Empty» and «forbidden» look the same (`LEZIONI.md` §1.9).
    """
    expected_val = WIDTH * HEIGHT * 2 + 2 * (WIDTH // 2) * (HEIGHT // 2) * 2
    real = os.path.getsize(fpath)
    if real != expected_val:
        raise SystemExit(
            f"⛔ {fpath} measures {real} bytes and should measure {expected_val}: "
            f"it is not a yuv420p10le {WIDTH}x{HEIGHT} frame")
    with open(fpath, "rb") as f:
        f.seek(row * WIDTH * 2)
        raw = f.read(WIDTH * 2)
    if len(raw) != WIDTH * 2:
        raise SystemExit(f"⛔ short read on {fpath}: {len(raw)} bytes")
    return [raw[i] | (raw[i + 1] << 8) for i in range(0, len(raw), 2)]


def measure_bit(fpath, row):
    values = read_y_row(fpath, row)
    levels = len(set(values))
    m4 = sum(1 for v in values if v % 4 == 0) / len(values)
    verdict = "8-bit-travestiti" if m4 > THRESHOLD_M4_TRUE else "10-bit-veri"
    return {
        "file": os.path.basename(fpath), "row": row,
        "distinct_levels": levels, "frazione_multipli_4": round(m4, 4),
        "minimum": min(values), "maximum": max(values), "verdict": verdict,
    }


def compare(a, b):
    """The comparison on the PIXELS, plane by plane.  Not «the files are equal»: where."""
    da, db = open(a, "rb").read(), open(b, "rb").read()
    if len(da) != len(db):
        return {"confrontabili": False, "byte_a": len(da), "byte_b": len(db),
                "identici": False}
    ny = WIDTH * HEIGHT * 2
    nc = (WIDTH // 2) * (HEIGHT // 2) * 2
    cuts = {"Y": (0, ny), "U": (ny, ny + nc), "V": (ny + nc, ny + 2 * nc)}
    outcome = {"confrontabili": True, "total_bytes": len(da), "identici": da == db}
    for label_name, (i0, i1) in cuts.items():
        pa, pb = da[i0:i1], db[i0:i1]
        different = 0
        maximum = 0
        sum2 = 0
        for i in range(0, len(pa), 2):
            va = pa[i] | (pa[i + 1] << 8)
            vb = pb[i] | (pb[i + 1] << 8)
            d = abs(va - vb)
            if d:
                different += 1
                if d > maximum:
                    maximum = d
            sum2 += d * d
        n = len(pa) // 2
        outcome[label_name] = {"samples": n, "campioni_diversi": different,
                       "differenza_massima": maximum,
                       "errore_quadratico_medio": round(sum2 / n, 4)}
    return outcome


# ── ⛔ The positive control of the tools themselves ────────────────────────

def selftest(folder):
    """«Can this tool find something that is surely there?» (`CODER.md` §3.10)

    Three questions, and they are the three where a measuring tool lies silently:

      1. can the **comparator** say DIFFERENT?  It is given the source and a copy
         with **a single byte flipped**.  A comparator that answered «equal»
         would make every future round green, forever;
      2. can the **bit meter** say «real 10 bits» on the real file?
      3. ⛔ and can it say «disguised 8 bits» on the opposite case?  It is the half that
         gets forgotten: a tool that always says «10 bits» would pass 2 and
         would measure nothing.
    """
    real = os.path.join(folder, "sorgente-10bit.yuv")
    fake = os.path.join(folder, "sorgente-8in10.yuv")
    for p in (real, fake):
        if not os.path.exists(p):
            raise SystemExit(f"⛔ {p} is missing: generate it first, with --generate")

    faults = []

    # 1 — the comparator
    scratched = os.path.join(folder, "autoprova-graffiato.yuv")
    data_v = bytearray(open(real, "rb").read())
    dove = WIDTH * 2 * RAMP_LINE + 100
    data_v[dove] ^= 0xFF
    open(scratched, "wb").write(bytes(data_v))
    c1 = compare(real, scratched)
    ok1 = (not c1["identici"]) and c1["Y"]["campioni_diversi"] >= 1
    if not ok1:
        faults.append("⛔ the comparator does not see a flipped byte: it compares nothing")

    c0 = compare(real, real)
    ok0 = c0["identici"] and c0["Y"]["campioni_diversi"] == 0
    if not ok0:
        faults.append("⛔ the comparator says DIFFERENT for a file against itself")

    # 2 and 3 — the bit meter, both ways
    m_real = measure_bit(real, RAMP_LINE)
    m_fake = measure_bit(fake, RAMP_LINE)
    ok2 = m_real["verdict"] == "10-bit-veri" and m_real["distinct_levels"] == EXPECTED_REAL_LEVELS
    ok3 = m_fake["verdict"] == "8-bit-travestiti" and m_fake["distinct_levels"] == EXPECTED_LEVELS_8IN10
    if not ok2:
        faults.append(f"⛔ on the REAL source the meter says {m_real}")
    if not ok3:
        faults.append(f"⛔ 10 BITS NOT DISTINGUISHABLE FROM 8: on the opposite case the "
                      f"meter says {m_fake}")

    os.remove(scratched)
    outcome = {"positive_check": ok0 and ok1 and ok2 and ok3,
             "comparatore_identita": ok0, "comparatore_un_byte": ok1,
             "misura_vero": m_real, "misura_opposto": m_fake,
             "faults": faults}
    print(json.dumps(outcome, ensure_ascii=False, indent=2))
    return 0 if outcome["positive_check"] else 1


def generate(folder):
    os.makedirs(folder, exist_ok=True)
    Y, U, V = build()
    Us, Vs = subsamples(U), subsamples(V)
    real = os.path.join(folder, "sorgente-10bit.yuv")
    write_yuv(real, Y, Us, Vs)
    raw = open(real, "rb").read()
    open(os.path.join(folder, "sorgente-8in10.yuv"), "wb").write(a_8_bit(raw))

    gpu_card = {
        "width_px": WIDTH, "height_px": HEIGHT,
        "schema": "yuv420p10le", "color": "BT.709 range limitato",
        "riga_della_rampa": RAMP_LINE,
        "atteso_livelli_veri": EXPECTED_REAL_LEVELS,
        "atteso_livelli_8in10": EXPECTED_LEVELS_8IN10,
        "atteso_m4_8in10": EXPECTED_M4_8IN10,
        "soglia_m4_veri": THRESHOLD_M4_TRUE,
        "bands": {"rampa": BAND_RAMP, "sfumature": BAND_GRADIENTS,
                  "body_text": BAND_TEXT, "fine": BAND_END,
                  "patches": BAND_PATCHES},
        "byte_per_fotogramma": len(raw),
    }
    with open(os.path.join(folder, "sorgente.json"), "w") as f:
        json.dump(gpu_card, f, ensure_ascii=False, indent=2)
    print(json.dumps(gpu_card, ensure_ascii=False))
    return 0


def main():
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--generate", metavar="FOLDER")
    p.add_argument("--selftest", metavar="FOLDER")
    p.add_argument("--levels", metavar="FILE")
    p.add_argument("--row", type=int, default=RAMP_LINE)
    p.add_argument("--compare", nargs=2, metavar=("A", "B"))
    a = p.parse_args()

    if a.generate:
        return generate(a.generate)
    if a.selftest:
        return selftest(a.selftest)
    if a.levels:
        print(json.dumps(measure_bit(a.levels, a.row), ensure_ascii=False))
        return 0
    if a.compare:
        print(json.dumps(compare(*a.compare), ensure_ascii=False))
        return 0
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
