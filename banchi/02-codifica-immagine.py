#!/usr/bin/env python3
"""02-codifica-immagine.py — the known image of F2.3, and the tools that judge it.

    python3 02-codifica-immagine.py --genera <cartella>
    python3 02-codifica-immagine.py --livelli <file.yuv> [--riga N]
    python3 02-codifica-immagine.py --confronta <a.yuv> <b.yuv>
    python3 02-codifica-immagine.py --autoprova <cartella>   ⛔ the positive control

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
LARGHEZZA = 1920
ALTEZZA = 1080

# The bands, in rows.  They are INCLUSIVE on the left and EXCLUSIVE on the right.
FASCIA_RAMPA = (0, 256)
FASCIA_SFUMATURE = (256, 512)
FASCIA_TESTO = (512, 768)
FASCIA_FINE = (768, 1024)
FASCIA_TOPPE = (1024, 1080)

# ⛔ The row on which the 10-bit test is read.  It is inside the ramp, and it is
#    declared here because the bench and the report must cite THE SAME one.
RIGA_RAMPA = 128

# The limited range at 10 bits.
Y_MIN, Y_MAX = 64, 940
CROMA_ZERO = 512

# The expectations, written BEFORE the round (PIANO.md §0.3 rule 4).
ATTESO_LIVELLI_VERI = 877          # 940 - 64 + 1
ATTESO_LIVELLI_8IN10 = 220         # from 64 to 940 in steps of 4
ATTESO_M4_8IN10 = 1.0
SOGLIA_M4_VERI = 0.50              # ⛔ above this threshold we shout «disguised 8 bits»


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
FRASE = "REMOTIX 10 bit 4:2:0"


def rgb_a_ycbcr(r, g, b):
    """BT.709, limited range, 10 bits.  r/g/b in [0,1].  Returns integers."""
    yf = 0.2126 * r + 0.7152 * g + 0.0722 * b
    cb = (b - yf) / 1.8556
    cr = (r - yf) / 1.5748
    y = int(round(64 + 876 * yf))
    u = int(round(CROMA_ZERO + 896 * cb))
    v = int(round(CROMA_ZERO + 896 * cr))
    limita = lambda x: max(4, min(1019, x))
    return limita(y), limita(u), limita(v)


def costruisci():
    """The image, in three full-resolution planes (the chroma is subsampled afterwards).

    It works at 4:4:4 and reduces to 4:2:0 at the end, with the average of the 2x2 block.
    ⚠ It is that average that produces the fringing of the text: it is done here, in
      the open, instead of leaving it to a tool — so whoever reads knows
      exactly where the defect they then measure is born.
    """
    Y = [[0] * LARGHEZZA for _ in range(ALTEZZA)]
    U = [[CROMA_ZERO] * LARGHEZZA for _ in range(ALTEZZA)]
    V = [[CROMA_ZERO] * LARGHEZZA for _ in range(ALTEZZA)]

    # ── the 1-LSB ramp ─────────────────────────────────────────────────────
    riga_rampa = [Y_MIN + (c * (Y_MAX - Y_MIN)) // (LARGHEZZA - 1)
                  for c in range(LARGHEZZA)]
    for r in range(*FASCIA_RAMPA):
        Y[r] = list(riga_rampa)

    # ── soft colour gradients: blue → cyan, and green → yellow ─────────────
    a, b_ = FASCIA_SFUMATURE
    meta = (a + b_) // 2
    for r in range(a, b_):
        verso_giallo = r >= meta
        for c in range(LARGHEZZA):
            t = c / (LARGHEZZA - 1)
            if verso_giallo:
                y, u, v = rgb_a_ycbcr(t * 0.85, 0.85, 0.05)
            else:
                y, u, v = rgb_a_ycbcr(0.05, t * 0.85, 0.85)
            Y[r][c], U[r][c], V[r][c] = y, u, v

    # ── the text: saturated red on saturated blue, at three magnifications ─
    a, b_ = FASCIA_TESTO
    fondo = rgb_a_ycbcr(0.05, 0.05, 0.90)
    inchiostro = rgb_a_ycbcr(0.90, 0.06, 0.06)
    for r in range(a, b_):
        for c in range(LARGHEZZA):
            Y[r][c], U[r][c], V[r][c] = fondo
    riga = a + 8
    for scala in (1, 2, 3, 4):
        disegna_frase(Y, U, V, FRASE, 8, riga, scala, inchiostro)
        riga += 7 * scala + 10

    # ── the fine detail: checkerboards and 1, 2, 3 px bars ────────────────
    a, b_ = FASCIA_FINE
    nero = rgb_a_ycbcr(0.02, 0.02, 0.02)
    bianco = rgb_a_ycbcr(0.95, 0.95, 0.95)
    rosso = rgb_a_ycbcr(0.90, 0.05, 0.05)
    blu = rgb_a_ycbcr(0.05, 0.05, 0.90)
    quarto = (b_ - a) // 4
    for r in range(a, b_):
        i = (r - a) // quarto
        for c in range(LARGHEZZA):
            if i == 0:                       # 1px white/black checkerboard
                p = bianco if (r + c) % 2 == 0 else nero
            elif i == 1:                     # 1px red/blue checkerboard ⭐
                p = rosso if (r + c) % 2 == 0 else blu
            elif i == 2:                     # vertical bars 1,2,3 px
                per = 12
                x = c % per
                p = rosso if x in (0, 2, 3, 5, 6, 7) else blu
            else:                            # horizontal bars 1,2,3 px
                per = 12
                x = (r - a) % per
                p = bianco if x in (0, 2, 3, 5, 6, 7) else nero
            Y[r][c], U[r][c], V[r][c] = p

    # ── the flat reference patches ────────────────────────────────────────
    a, b_ = FASCIA_TOPPE
    toppe = [rgb_a_ycbcr(x, x, x) for x in (0.0, 0.18, 0.5, 0.75, 1.0)]
    largo = LARGHEZZA // len(toppe)
    for r in range(a, b_):
        for c in range(LARGHEZZA):
            Y[r][c], U[r][c], V[r][c] = toppe[min(c // largo, len(toppe) - 1)]

    return Y, U, V


def disegna_frase(Y, U, V, frase, x0, y0, scala, colore):
    for k, ch in enumerate(frase):
        g = FONT.get(ch)
        if g is None:
            continue
        bx = x0 + k * 6 * scala
        for gy in range(7):
            for gx in range(5):
                if g[gy][gx] != "#":
                    continue
                for dy in range(scala):
                    for dx in range(scala):
                        y, x = y0 + gy * scala + dy, bx + gx * scala + dx
                        if 0 <= y < ALTEZZA and 0 <= x < LARGHEZZA:
                            Y[y][x], U[y][x], V[y][x] = colore


def sottocampiona(P):
    """4:4:4 → 4:2:0 with the average of the 2x2 block.  ⚠ Here the fringing is born."""
    fuori = []
    for r in range(0, ALTEZZA, 2):
        riga = []
        for c in range(0, LARGHEZZA, 2):
            riga.append((P[r][c] + P[r][c + 1] + P[r + 1][c] + P[r + 1][c + 1] + 2) // 4)
        fuori.append(riga)
    return fuori


def in_byte(piano):
    b = bytearray()
    for riga in piano:
        for v in riga:
            b += int(v).to_bytes(2, "little")
    return bytes(b)


def scrivi_yuv(percorso, Y, U, V):
    with open(percorso, "wb") as f:
        f.write(in_byte(Y))
        f.write(in_byte(U))
        f.write(in_byte(V))


def a_8_bit(dati):
    """(v >> 2) << 2 on every 16-bit little-endian sample.

    ⛔ It is the OPPOSITE CASE, produced and not reasoned: the same image passed
       through 8 bits and put back in a 10-bit container.  An eye cannot tell it apart.
    """
    fuori = bytearray(dati)
    for i in range(0, len(fuori), 2):
        v = fuori[i] | (fuori[i + 1] << 8)
        v = (v >> 2) << 2
        fuori[i] = v & 0xFF
        fuori[i + 1] = (v >> 8) & 0xFF
    return bytes(fuori)


# ── The judging tools ──────────────────────────────────────────────────────

def leggi_riga_y(percorso, riga):
    """Row `riga` of the Y plane.  ⛔ It checks the file SIZE first.

    A short file read with `seek` gives no error: it gives bytes of another row, or
    nothing.  «Empty» and «forbidden» look the same (`LEZIONI.md` §1.9).
    """
    atteso = LARGHEZZA * ALTEZZA * 2 + 2 * (LARGHEZZA // 2) * (ALTEZZA // 2) * 2
    vero = os.path.getsize(percorso)
    if vero != atteso:
        raise SystemExit(
            f"⛔ {percorso} measures {vero} bytes and should measure {atteso}: "
            f"it is not a yuv420p10le {LARGHEZZA}x{ALTEZZA} frame")
    with open(percorso, "rb") as f:
        f.seek(riga * LARGHEZZA * 2)
        crudo = f.read(LARGHEZZA * 2)
    if len(crudo) != LARGHEZZA * 2:
        raise SystemExit(f"⛔ short read on {percorso}: {len(crudo)} bytes")
    return [crudo[i] | (crudo[i + 1] << 8) for i in range(0, len(crudo), 2)]


def misura_bit(percorso, riga):
    valori = leggi_riga_y(percorso, riga)
    livelli = len(set(valori))
    m4 = sum(1 for v in valori if v % 4 == 0) / len(valori)
    verdetto = "8-bit-travestiti" if m4 > SOGLIA_M4_VERI else "10-bit-veri"
    return {
        "file": os.path.basename(percorso), "riga": riga,
        "livelli_distinti": livelli, "frazione_multipli_4": round(m4, 4),
        "minimo": min(valori), "massimo": max(valori), "verdetto": verdetto,
    }


def confronta(a, b):
    """The comparison on the PIXELS, plane by plane.  Not «the files are equal»: where."""
    da, db = open(a, "rb").read(), open(b, "rb").read()
    if len(da) != len(db):
        return {"confrontabili": False, "byte_a": len(da), "byte_b": len(db),
                "identici": False}
    ny = LARGHEZZA * ALTEZZA * 2
    nc = (LARGHEZZA // 2) * (ALTEZZA // 2) * 2
    tagli = {"Y": (0, ny), "U": (ny, ny + nc), "V": (ny + nc, ny + 2 * nc)}
    esito = {"confrontabili": True, "byte_totali": len(da), "identici": da == db}
    for nome, (i0, i1) in tagli.items():
        pa, pb = da[i0:i1], db[i0:i1]
        diversi = 0
        massimo = 0
        somma2 = 0
        for i in range(0, len(pa), 2):
            va = pa[i] | (pa[i + 1] << 8)
            vb = pb[i] | (pb[i + 1] << 8)
            d = abs(va - vb)
            if d:
                diversi += 1
                if d > massimo:
                    massimo = d
            somma2 += d * d
        n = len(pa) // 2
        esito[nome] = {"campioni": n, "campioni_diversi": diversi,
                       "differenza_massima": massimo,
                       "errore_quadratico_medio": round(somma2 / n, 4)}
    return esito


# ── ⛔ The positive control of the tools themselves ────────────────────────

def autoprova(cartella):
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
    vero = os.path.join(cartella, "sorgente-10bit.yuv")
    finto = os.path.join(cartella, "sorgente-8in10.yuv")
    for p in (vero, finto):
        if not os.path.exists(p):
            raise SystemExit(f"⛔ {p} is missing: generate it first, with --genera")

    guasti = []

    # 1 — the comparator
    graffiato = os.path.join(cartella, "autoprova-graffiato.yuv")
    dati = bytearray(open(vero, "rb").read())
    dove = LARGHEZZA * 2 * RIGA_RAMPA + 100
    dati[dove] ^= 0xFF
    open(graffiato, "wb").write(bytes(dati))
    c1 = confronta(vero, graffiato)
    ok1 = (not c1["identici"]) and c1["Y"]["campioni_diversi"] >= 1
    if not ok1:
        guasti.append("⛔ the comparator does not see a flipped byte: it compares nothing")

    c0 = confronta(vero, vero)
    ok0 = c0["identici"] and c0["Y"]["campioni_diversi"] == 0
    if not ok0:
        guasti.append("⛔ the comparator says DIFFERENT for a file against itself")

    # 2 and 3 — the bit meter, both ways
    m_vero = misura_bit(vero, RIGA_RAMPA)
    m_finto = misura_bit(finto, RIGA_RAMPA)
    ok2 = m_vero["verdetto"] == "10-bit-veri" and m_vero["livelli_distinti"] == ATTESO_LIVELLI_VERI
    ok3 = m_finto["verdetto"] == "8-bit-travestiti" and m_finto["livelli_distinti"] == ATTESO_LIVELLI_8IN10
    if not ok2:
        guasti.append(f"⛔ on the REAL source the meter says {m_vero}")
    if not ok3:
        guasti.append(f"⛔ 10 BITS NOT DISTINGUISHABLE FROM 8: on the opposite case the "
                      f"meter says {m_finto}")

    os.remove(graffiato)
    esito = {"controllo_positivo": ok0 and ok1 and ok2 and ok3,
             "comparatore_identita": ok0, "comparatore_un_byte": ok1,
             "misura_vero": m_vero, "misura_opposto": m_finto,
             "guasti": guasti}
    print(json.dumps(esito, ensure_ascii=False, indent=2))
    return 0 if esito["controllo_positivo"] else 1


def genera(cartella):
    os.makedirs(cartella, exist_ok=True)
    Y, U, V = costruisci()
    Us, Vs = sottocampiona(U), sottocampiona(V)
    vero = os.path.join(cartella, "sorgente-10bit.yuv")
    scrivi_yuv(vero, Y, Us, Vs)
    crudo = open(vero, "rb").read()
    open(os.path.join(cartella, "sorgente-8in10.yuv"), "wb").write(a_8_bit(crudo))

    scheda = {
        "larghezza": LARGHEZZA, "altezza": ALTEZZA,
        "formato": "yuv420p10le", "colore": "BT.709 range limitato",
        "riga_della_rampa": RIGA_RAMPA,
        "atteso_livelli_veri": ATTESO_LIVELLI_VERI,
        "atteso_livelli_8in10": ATTESO_LIVELLI_8IN10,
        "atteso_m4_8in10": ATTESO_M4_8IN10,
        "soglia_m4_veri": SOGLIA_M4_VERI,
        "fasce": {"rampa": FASCIA_RAMPA, "sfumature": FASCIA_SFUMATURE,
                  "testo": FASCIA_TESTO, "fine": FASCIA_FINE,
                  "toppe": FASCIA_TOPPE},
        "byte_per_fotogramma": len(crudo),
    }
    with open(os.path.join(cartella, "sorgente.json"), "w") as f:
        json.dump(scheda, f, ensure_ascii=False, indent=2)
    print(json.dumps(scheda, ensure_ascii=False))
    return 0


def main():
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--genera", metavar="CARTELLA")
    p.add_argument("--autoprova", metavar="CARTELLA")
    p.add_argument("--livelli", metavar="FILE")
    p.add_argument("--riga", type=int, default=RIGA_RAMPA)
    p.add_argument("--confronta", nargs=2, metavar=("A", "B"))
    a = p.parse_args()

    if a.genera:
        return genera(a.genera)
    if a.autoprova:
        return autoprova(a.autoprova)
    if a.livelli:
        print(json.dumps(misura_bit(a.livelli, a.riga), ensure_ascii=False))
        return 0
    if a.confronta:
        print(json.dumps(confronta(*a.confronta), ensure_ascii=False))
        return 0
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
