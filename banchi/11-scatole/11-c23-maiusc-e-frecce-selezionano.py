#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c23 — ⭐⭐ «SHIFT AND ARROWS SELECT»
===========================================================================

    python3 11-c23-maiusc-e-frecce-selezionano.py --scatola gnome [--browser firefox,chrome]
    python3 11-c23-maiusc-e-frecce-selezionano.py --scatola lxqt --porta 8524 \\
            --contenitore rete14-lxqt            # a development box
    python3 11-c23-maiusc-e-frecce-selezionano.py --scatola gnome --senza-maiusc
    python3 11-c23-maiusc-e-frecce-selezionano.py --certifica

    what must be true         : Shift+arrows SELECT in the remote desktop,
                                and Shift does not stay stuck — on GNOME,
                                KDE, XFCE and LXQt (the user, 24 Sep 2026:
                                «one last check remains: that selection
                                with Shift+arrows is implemented on all the
                                DEs»)
    where it starts from      : ⛔ from scratch, a NEW tenant (`c23u<n>`)
    what it looks at          : ⛔ **THE PHOTOGRAPH** of the remote field: the value
                                is read from the canvas pixels, not from an
                                event counter
    how I know it can give red: `--senza-maiusc` (the same sequences without ever
                                pressing Shift: no selection) ⇒ RED

⛔⛔ WHY IT EXISTS.
   `[M]` 24 Sep 2026, on all four desktops: Shift+Left left
   the page as `105↓ 105↑` — the Shift already down was recovered only if
   there was also Ctrl/Alt/Super ⇒ the arrow moved the cursor and did NOT
   select.  And after a letter typed with Shift down the page believed
   Shift still pressed while the server had already released it.  The cure
   is in `src/pagina.html` (`cl_su_keydown`, commit 694f77f, two halves); this
   mesh is the test that remains, on the four desktops.
   ⚠ With the REAL BROWSERS (the user, 23 Sep 2026: *«the tests must be done with the
     real browsers, not with emulators»*): the defect was precisely in the way
     the page reads THE BROWSER's events (`getModifierState`, `ev.code`), and
     the Python client does not have those events.

⭐ WHAT IT DOES, for each browser (Firefox with Marionette, Chrome with CDP: the
   drivers are those of `banchi/12-client-veri.py`, the box that of
   `banchi/12-c20-veri.py`, the wake-up and the geometry those of
   `11-c21-sul-bordo-la-forma-cambia.py` — ⛔ imported, not copied):
     1  creates the tenant `c23u<n>`, logs in, waits for the first frame
     2  C21's WAKE-UP (a real ESC: on GNOME the session is born in the
        overview)
     3  in the session starts a small server (`python3`) and
        `firefox-esr --kiosk` on the SCENE: an <input> always focused
     4  for each case (`CASI`): cleans the field (Ctrl+A, Backspace),
        types the BASE, and then the sequence to test — with REAL KEYS given to the
        browser (`WebDriver:PerformActions`, `Input.dispatchKeyEvent`)
     5  photographs the canvas and READS the value of the field from the pixels

⭐⭐ THE SCENE — the value shows, twice.
   · IN LARGE, in the field itself: it is for whoever looks at the saved photographs
     (`--salva`), that is for the user.
   · AND AS A STRIP OF COLOURS under the field: one box per character, of the
     colour `ALFABETO` gives to that character (and grey `VUOTO` where the
     value has ended), between two white MARK boxes.  ⇒ The mesh reads
     the value from the photograph without recognising the letters: it takes the colour
     at the centre of each box and looks for the nearest in the palette.
     ⛔ The palette is written ONCE, here, and put into the page: the
       colour the page paints and the one the judge looks for cannot
       diverge (the same reason as C4's scene).
     ⚠ The colours are the 27 vertices and midpoints of the RGB cube (0, 128, 255 per
       channel): two colours are at least 127 apart, and the tolerance is 60 — the
       chain goes through H.264 4:2:0, which subsamples the chroma (§4.3 of phase
       11), but on boxes of ~270 px the chroma at the centre arrives whole.
   · The server also writes, in a file of the tenant, every keydown of the
     remote page and every value of the field: ⛔ it does NOT judge — it is the diagnosis
     of the red (which key arrived, with which Shift).

⭐ THE CASES — those of the cure, measured on 24 Sep 2026 on rete14-lxqt:
     1  «abcdef», Shift+Left×3, Y                     ⇒ «abcY»
     2  «uno due», Ctrl+Shift+Left, z                  ⇒ «uno z»
     3  «abcdef», Shift down, Left, A, Shift up, b
                                                      ⇒ «abcdeAb»
        (the risky case: after the letter Shift does NOT stay stuck,
         and the «b» comes out lowercase)
     4  «abcdef», Shift down, Left, A, Left×2, X, Shift up, q
                                                      ⇒ «abcdXq»
        (the second half of the cure: AFTER the letter, with Shift still down,
         the arrows still select.  `[M]` without that half ⇒ «abcdXqeA»)
   ⭐ The expected value is not only written by hand: `simula()` applies the sequence to a
     fake text field, and `--certifica` checks that it gives the expected value — and that
     the same sequence WITHOUT Shift gives something else (the fault shows).

⛔ THE THREE POOR CHECKS, for each case:
     1  after the cleaning the strip is there and is EMPTY  — if not, 3: the scene is not
        in force (or the field does not clean) and does not bear witness
     2  after the base the strip says THE BASE          — if not, 3: if
        plain typing does not arrive it is C4's, not C23's; and so a red
        here comes ONLY from the selection
     3  after the sequence the strip says THE EXPECTED VALUE — if not, RED, with the
        value seen and the tail of the remote keydowns
   ⚠ It photographs several times until `ATTESA_S`: here latency is not measured,
     and a late frame is not a selection defect.

⛔ HOW I KNOW IT CAN GIVE RED — `--senza-maiusc`.
   The same sequences, with the «Shift down» and «Shift up» removed: the letters
   keep their form (the «Y» is still «Y»), ⇒ the only difference is
   that the arrows move instead of selecting, and every case must give RED.
   ⛔ It reads THE OTHER WAY ROUND, like every fault of the net (`11-gancio.sh`,
     `esegui_maglia`): 0 = the fault was SEEN (all cases red),
     1 = NOT seen (a case came out right anyway), 3 = I could not look.

⚠ OUTCOMES: 0 green · 1 red · 3 «I could not look», with the reason.

⚠ WHERE IT RUNS: like C21, on the host with the real browsers (`REMOTIX_SUL_SERVER=1`,
  screenless `labwc`), and in the box with `podman exec`.  The tenant is
  `c23u<n>` (C19's pattern `^c[0-9]+b?u[0-9]+$`): if the bench died
  half-way, the hook clears it out.
"""
import argparse
import base64
import importlib.util as _iu
import io
import json
import os
import random
import re
import secrets
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
BANCHI = os.path.dirname(QUI)


def _carica(nome, file):
    s = _iu.spec_from_file_location(nome, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ⛔ Imported, not copied: C21 brings `12-c20-veri` (the box) and
#   `12-client-veri` (the browsers) along — only one in memory, and the ESC already in the table.
C21 = _carica("c21", os.path.join(QUI, "11-c21-sul-bordo-la-forma-cambia.py"))
C20V = C21.C20V
VERI = C21.VERI
VERDE, ROSSO, CIECO = VERI.VERDE, VERI.ROSSO, VERI.CIECO
PORTE = C20V.PORTE
NOME_ESITO = C21.NOME_ESITO

MODELLO_INQUILINO = re.compile(r"^c23u[0-9]+$")

# ---------------------------------------------------------------------------
# ⛔ THE NUMBERS — each with its reason.
# ---------------------------------------------------------------------------
# Between one event and the next: more than a human's shortest repeat, and
# enough for every key to travel on its own (`[M]` c95: 90 ms are enough).
PAUSA_MS = 90
# How long we wait for the photograph to say the value: it is not a latency, it is
# a ceiling beyond which the value no longer arrives.
ATTESA_S = 6.0
FOTO_OGNI_S = 0.7
# The tolerance on a box's colour: half the minimum distance between two
# colours of the palette (127) minus a margin.
TOLLERANZA = 60
# ⭐ The strip, in fractions of the kiosk window (= the desktop): wide and
#   in the middle, far from bars and drawers even if the kiosk did not cover them.
CASELLE = 14
STRISCIA_X0, STRISCIA_X1 = 0.04, 0.96      # from the left mark to the right one
STRISCIA_Y0, STRISCIA_Y1 = 0.55, 0.75
# The sample at the centre of each box: +/- this fraction of the box.
CAMPIONE = 0.2

# ⭐ THE PALETTE.  Reserved: VUOTO (box without a character), ALTRO (a
#   character outside the alphabet, or the value too long), MARCA (the two
#   ends of the strip).  The letters take the other colours in order.
VUOTO = (128, 128, 128)
ALTRO = (0, 0, 0)
MARCA = (255, 255, 255)
ALFABETO = "abcdefnoquxyzAXY "


def _cubo():
    livelli = (0, 128, 255)
    return [(r, g, b) for r in livelli for g in livelli for b in livelli]


COLORI = {}
for _c in [c for c in _cubo() if c not in (VUOTO, ALTRO, MARCA)][:len(ALFABETO)]:
    COLORI[ALFABETO[len(COLORI)]] = _c
assert len(COLORI) == len(ALFABETO)

# ---------------------------------------------------------------------------
# ⭐ THE KEYS.  A step is («giu»|«su», name).  The letters are written ALREADY
#   in the form the browser reports (`ev.key`): «Y», not «y» + Shift.
#   ⇒ The fault can remove Shift without changing the letters.
# ---------------------------------------------------------------------------
SPECIALI = {
    #  name        key          code          vk  WebDriver   CDP bit
    "Shift":     ("Shift",     "ShiftLeft",   16, "", 8),
    "Control":   ("Control",   "ControlLeft", 17, "", 2),
    "ArrowLeft": ("ArrowLeft", "ArrowLeft",   37, "", 0),
    "Backspace": ("Backspace", "Backspace",    8, "", 0),
}


def premi(nome):
    return [("giu", nome), ("su", nome)]


def scrivi(testo):
    p = []
    for c in testo:
        p += premi(c)
    return p


def col(mod, passi):
    """`passi` with the modifier `mod` held down."""
    return [("giu", mod)] + passi + [("su", mod)]


PULISCI = col("Control", premi("a")) + premi("Backspace")

# (title, base, sequence, expected)
CASI = [
    ("1 Shift+Left×3, Y", "abcdef",
     col("Shift", premi("ArrowLeft") * 3 + premi("Y")), "abcY"),
    ("2 Ctrl+Shift+Left, z", "uno due",
     col("Control", col("Shift", premi("ArrowLeft"))) + premi("z"), "uno z"),
    ("3 RISK Shift down, Left, A, Shift up, b", "abcdef",
     col("Shift", premi("ArrowLeft") + premi("A")) + premi("b"), "abcdeAb"),
    ("4 RISK+ Shift down, Left, A, Left×2, X, Shift up, q", "abcdef",
     col("Shift", premi("ArrowLeft") + premi("A") + premi("ArrowLeft") * 2 + premi("X"))
     + premi("q"), "abcdXq"),
]


def senza_maiusc(passi):
    """⛔ THE FAULT: the same sequences without ever pressing Shift."""
    return [p for p in passi if p[1] != "Shift"]


# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def simula(passi, valore=""):
    """⭐ A fake text field: applies the steps and returns the value.

    The semantics is that of a Firefox/GTK <input>: the letter replaces
    the selection; Left without Shift with a selection closes it at its
    start; Ctrl+Left jumps to the start of the word; Ctrl+A selects
    everything; Backspace deletes the selection or the character before."""
    ancora = fuoco = len(valore)
    giu = set()
    for tipo, nome in passi:
        if tipo == "su":
            giu.discard(nome)
            continue
        if nome in ("Shift", "Control"):
            giu.add(nome)
            continue
        a, b = min(ancora, fuoco), max(ancora, fuoco)
        if nome == "ArrowLeft":
            if "Control" in giu:
                i = fuoco
                while i > 0 and valore[i - 1] == " ":
                    i -= 1
                while i > 0 and valore[i - 1] != " ":
                    i -= 1
                nuovo = i
            elif "Shift" not in giu and a != b:
                nuovo = a
            else:
                nuovo = max(0, fuoco - 1)
            fuoco = nuovo
            if "Shift" not in giu:
                ancora = fuoco
        elif nome == "Backspace":
            if a != b:
                valore = valore[:a] + valore[b:]
                ancora = fuoco = a
            elif a > 0:
                valore = valore[:a - 1] + valore[a:]
                ancora = fuoco = a - 1
        elif "Control" in giu:
            if nome.lower() == "a":
                ancora, fuoco = 0, len(valore)
        else:
            valore = valore[:a] + nome + valore[b:]
            ancora = fuoco = a + len(nome)
    return valore


def centri_caselle():
    """[(fx, fy)] of the centres: mark, CASELLE boxes, mark — in fractions."""
    passo = (STRISCIA_X1 - STRISCIA_X0) / (CASELLE + 2)
    fy = (STRISCIA_Y0 + STRISCIA_Y1) / 2
    return [(STRISCIA_X0 + (i + 0.5) * passo, fy) for i in range(CASELLE + 2)]


def _dist(a, b):
    return max(abs(x - y) for x, y in zip(a, b))


def nome_colore(c):
    """(name, distance) of the nearest palette colour."""
    tutti = [("MARCA", MARCA), ("VUOTO", VUOTO), ("ALTRO", ALTRO)] + \
        [(k, v) for k, v in COLORI.items()]
    k, v = min(tutti, key=lambda kv: _dist(kv[1], c))
    return k, _dist(v, c)


def leggi_striscia(campiona):
    """⭐ The value of the field from the photograph.

    `campiona(fx, fy, rx, ry)` returns the (median) colour of the rectangle
    centred in (fx, fy) with half-width (rx, ry), in fractions of the desktop.
    Returns (value or None, why)."""
    cc = centri_caselle()
    passo = (STRISCIA_X1 - STRISCIA_X0) / (CASELLE + 2)
    rx, ry = passo * CAMPIONE, (STRISCIA_Y1 - STRISCIA_Y0) * CAMPIONE
    nomi = []
    for i, (fx, fy) in enumerate(cc):
        c = campiona(fx, fy, rx, ry)
        k, d = nome_colore(c)
        if d > TOLLERANZA:
            return None, "box %d unreadable: %s is %d away from the nearest (%s)" % (
                i, c, d, k)
        nomi.append(k)
    if nomi[0] != "MARCA" or nomi[-1] != "MARCA":
        return None, "the strip does not show: at the ends %s and %s instead of the marks" % (
            nomi[0], nomi[-1])
    corpo = nomi[1:-1]
    if "MARCA" in corpo:
        return None, "a mark in the middle of the strip: %s" % corpo
    v = ""
    fine = False
    for k in corpo:
        if k == "VUOTO":
            fine = True
            continue
        if fine:
            return None, "a character after an empty box: %s" % corpo
        v += "�" if k == "ALTRO" else k
    return v, ""


def campionatore(im, geo):
    """`campiona()` on a PIL image of the canvas, with C21's geometry:
    fraction of the desktop ⇒ desktop pixel ⇒ photograph pixel."""
    pw, ph = im.size

    def al_pixel(fx, fy):
        X, Y = fx * geo["tl"], fy * geo["ta"]
        return ((geo["bx0"] + X * geo["sx"]) * pw / geo["bw"],
                (geo["by0"] + Y * geo["sy"]) * ph / geo["bh"])

    def campiona(fx, fy, rx, ry):
        vals = []
        for i in range(5):
            for j in range(5):
                x, y = al_pixel(fx + rx * (i - 2) / 2, fy + ry * (j - 2) / 2)
                x = min(pw - 1, max(0, int(x)))
                y = min(ph - 1, max(0, int(y)))
                vals.append(im.getpixel((x, y))[:3])
        return tuple(sorted(v[k] for v in vals)[len(vals) // 2] for k in range(3))
    return campiona


def giudica_caso(titolo, base, atteso, vuoto, visto_base, visto):
    """(outcome, reason) of a case, from the three values read in the photographs."""
    if vuoto != "":
        return CIECO, "%s: after the cleaning the strip is not empty (%r): the scene does not " \
            "bear witness" % (titolo, vuoto)
    if visto_base != base:
        return CIECO, "%s: the base %r did not arrive (seen %r): plain typing " \
            "is C4's, the selection is not judged" % (titolo, base, visto_base)
    if visto == atteso:
        return VERDE, "%s: %r ⇒ %r" % (titolo, base, visto)
    return ROSSO, "%s: %r ⇒ %r instead of %r" % (titolo, base, visto, atteso)


def esito_complessivo(esiti):
    return ROSSO if ROSSO in esiti else (CIECO if CIECO in esiti else VERDE)


def esito_col_guasto(esiti):
    """⛔ The other way round: 0 if EVERY case is red (the fault shows everywhere)."""
    if CIECO in esiti:
        return CIECO
    return VERDE if all(e == ROSSO for e in esiti) else ROSSO


# ═══════════════════════════════════════════════════════════════════════════
#  THE CERTIFICATION OF THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def _foto_finta(valore, geo, spost=(0, 0), rumore=25, seme=7):
    """A canvas painted like the scene, with a shift (a bar the
    kiosk does not cover) and some noise (the encoding)."""
    from PIL import Image, ImageDraw
    rnd = random.Random(seme)
    im = Image.new("RGB", (geo["bw"], geo["bh"]), (32, 32, 32))
    d = ImageDraw.Draw(im)
    passo = (STRISCIA_X1 - STRISCIA_X0) / (CASELLE + 2)
    colori = [MARCA] + [COLORI.get(c, ALTRO) for c in valore[:CASELLE]] + \
        [VUOTO] * (CASELLE - len(valore[:CASELLE])) + [MARCA]
    for i, c in enumerate(colori):
        x0 = (STRISCIA_X0 + i * passo) * geo["bw"] + spost[0]
        x1 = (STRISCIA_X0 + (i + 1) * passo) * geo["bw"] + spost[0] - 3
        c = tuple(min(255, max(0, v + rnd.randint(-rumore, rumore))) for v in c)
        d.rectangle([x0, STRISCIA_Y0 * geo["bh"] + spost[1], x1,
                     STRISCIA_Y1 * geo["bh"] + spost[1]], fill=c)
    return im


def certifica():
    print("⭐ 11-c23 · CERTIFICATION OF THE PURE FUNCTIONS")
    guai, fatte = [], []

    def prova(cosa, vero, dettaglio=""):
        fatte.append(cosa)
        print("   %s %s%s" % ("⭐ ok  " if vero else "⛔ NO  ", cosa,
                              (" — " + dettaglio) if dettaglio else ""))
        if not vero:
            guai.append(cosa)

    # 1. the palette: colours distinct well beyond twice the tolerance
    tutti = [MARCA, VUOTO, ALTRO] + list(COLORI.values())
    dmin = min(_dist(a, b) for i, a in enumerate(tutti) for b in tutti[i + 1:])
    prova("palette: %d colours, minimum distance %d > 2×%d" % (len(tutti), dmin, TOLLERANZA),
          dmin > 2 * TOLLERANZA)
    prova("every character of the cases is in the alphabet",
          all(c in ALFABETO for _t, b, s, a in CASI for c in b + a
              + "".join(n for _x, n in s if len(n) == 1)))
    # 2. the fake field: the expected value written by hand is what the sequence gives
    for t, base, seq, atteso in CASI:
        v = simula(scrivi(base) + seq)
        prova("simula %s ⇒ %r" % (t.split()[0], atteso), v == atteso, "gives %r" % v)
        vg = simula(scrivi(base) + senza_maiusc(seq))
        prova("simula %s WITHOUT Shift ⇒ something else" % t.split()[0], vg != atteso,
              "gives %r" % vg)
    prova("simula: the cleaning empties the field", simula(PULISCI, "abc") == "")
    # ⭐ case 4 with only the first half of the cure: after the letter Shift
    #   is UP for the server ⇒ the two Lefts move.  `[M]` c95: «abcdXqeA».
    vecchia = scrivi("abcdef") + col("Shift", premi("ArrowLeft") + premi("A")) \
        + premi("ArrowLeft") * 2 + premi("X") + premi("q")
    prova("simula case 4 as it was before half 2 ⇒ «abcdXqeA» (the [M] of c95)",
          simula(vecchia) == "abcdXqeA", "gives %r" % simula(vecchia))
    # 3. the strip is read from the pixels
    try:
        from PIL import Image                     # noqa: F401
    except ImportError:
        print("⛔ PIL is not there: I cannot certify the reading ⇒ 3")
        return 3
    geo = {"tl": 1920, "ta": 1080, "bw": 1920, "bh": 1080, "bx0": 0, "by0": 0,
           "sx": 1.0, "sy": 1.0}
    for v in ("", "abcY", "uno z", "abcdeAb", "abcdXqeA", "abcdefabcdefab"):
        for sp in ((0, 0), (0, 40), (-30, 25)):
            letto, perche = leggi_striscia(campionatore(_foto_finta(v, geo, sp), geo))
            prova("strip %r shifted %s ⇒ it reads back" % (v, sp), letto == v,
                  "read %r %s" % (letto, perche))
    letto, perche = leggi_striscia(campionatore(_foto_finta("abc@", geo), geo))
    prova("a character outside the alphabet ⇒ the replacement sign", letto == "abc�",
          "read %r %s" % (letto, perche))
    # the canvas bigger than the photo (Chrome shrinks it) and with black margins
    geo2 = {"tl": 3840, "ta": 2160, "bw": 1920, "bh": 1200, "bx0": 0, "by0": 60,
            "sx": 0.5, "sy": 0.5}
    from PIL import Image
    tela = Image.new("RGB", (1920, 1200), (0, 0, 0))
    tela.paste(_foto_finta("abcY", {"bw": 1920, "bh": 1080}), (0, 60))
    letto, perche = leggi_striscia(campionatore(tela, geo2))
    prova("4K canvas in a buffer with margins ⇒ it reads back", letto == "abcY",
          "read %r %s" % (letto, perche))
    letto, perche = leggi_striscia(campionatore(Image.new("RGB", (1920, 1080), (90, 60, 30)),
                                                geo))
    prova("without a strip ⇒ None (no judgement)", letto is None, perche)
    # 4. the judges
    prova("giudica: expected ⇒ GREEN",
          giudica_caso("t", "abcdef", "abcY", "", "abcdef", "abcY")[0] == VERDE)
    prova("giudica: Shift does not select ⇒ RED",
          giudica_caso("t", "abcdef", "abcY", "", "abcdef", "abcYdef")[0] == ROSSO)
    prova("giudica: the base does not arrive ⇒ 3",
          giudica_caso("t", "abcdef", "abcY", "", "abc", "abcY")[0] == CIECO)
    prova("giudica: the cleaning does not empty ⇒ 3",
          giudica_caso("t", "abcdef", "abcY", "xx", "abcdef", "abcY")[0] == CIECO)
    prova("with the fault: all red ⇒ 0 (seen)", esito_col_guasto([ROSSO] * 4) == VERDE)
    prova("with the fault: one green ⇒ 1 (not seen)",
          esito_col_guasto([ROSSO, VERDE, ROSSO, ROSSO]) == ROSSO)
    prova("with the fault: one blind ⇒ 3", esito_col_guasto([ROSSO, CIECO]) == CIECO)
    print()
    if guai:
        print("⛔ CERTIFICATION FAILED: %d tests out of %d" % (len(guai), len(fatte)))
        return 1
    print("⭐ CERTIFIED (%d tests): the expected value is what a field does with those keys, "
          "without Shift\n   something else comes out, and the value reads back from the pixels even "
          "shifted and dirtied." % len(fatte))
    return 0


# ═══════════════════════════════════════════════════════════════════════════
#  INSIDE THE BOX — the scene
# ═══════════════════════════════════════════════════════════════════════════
def pagina_scena():
    """⭐ The page, with THIS program's palette put inside."""
    tav = {k: "rgb(%d,%d,%d)" % v for k, v in COLORI.items()}
    passo = (STRISCIA_X1 - STRISCIA_X0) / (CASELLE + 2) * 100
    return """<!doctype html><meta charset=utf-8><title>REMOTIX C23</title>
<style>
 html,body{margin:0;height:100%%;background:#202020;overflow:hidden}
 #f{position:fixed;left:4vw;top:8vh;width:92vw;height:36vh;font:18vh/1 monospace;
    border:0;padding:0 2vw;box-sizing:border-box;background:#fff;color:#000;outline:0}
 .k{position:fixed;top:%(y0)fvh;height:%(h)fvh;width:calc(%(w)fvw - 6px)}
</style>
<input id=f autocomplete=off spellcheck=false>
<div id=s></div>
<script>
const TAV=%(tav)s, VUOTO='rgb(%(vu)s)', ALTRO='rgb(%(al)s)', MARCA='rgb(%(ma)s)', N=%(n)d;
const f=document.getElementById('f'), s=document.getElementById('s'), k=[];
for (let i=0;i<N+2;i++){const d=document.createElement('div');d.className='k';
  d.style.left=(%(x0)f+i*%(w)f)+'vw';s.appendChild(d);k.push(d);}
const m=(t)=>fetch('/l',{method:'POST',body:t}).catch(()=>0);
function dipingi(){const v=f.value;k[0].style.background=MARCA;k[N+1].style.background=MARCA;
  for(let i=0;i<N;i++){k[i+1].style.background = i<v.length ? (TAV[v[i]]||ALTRO) : VUOTO;}
  if(v.length>N) k[N].style.background=ALTRO;}
dipingi(); f.focus(); m('caricata');
addEventListener('keydown',e=>m('K '+e.key+' shift='+e.shiftKey+' ctrl='+e.ctrlKey));
f.addEventListener('input',()=>{dipingi();m('V '+JSON.stringify(f.value));});
setInterval(()=>{ if(document.activeElement!==f) f.focus(); dipingi(); },300);
</script>""" % {"tav": json.dumps(tav), "vu": "%d,%d,%d" % VUOTO, "al": "%d,%d,%d" % ALTRO,
                "ma": "%d,%d,%d" % MARCA, "n": CASELLE, "x0": STRISCIA_X0 * 100,
                "w": passo, "y0": STRISCIA_Y0 * 100, "h": (STRISCIA_Y1 - STRISCIA_Y0) * 100}


# The scene's server: it serves the page and notes what the page says.
SERVITORE = r'''
import http.server, sys
PAG = open(sys.argv[2], "rb").read()
LOG = sys.argv[3]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers(); self.wfile.write(PAG)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        t = self.rfile.read(n).decode("utf-8", "replace")
        with open(LOG, "a") as f: f.write(t + "\n")
        self.send_response(204); self.end_headers()
http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
'''


def accendi_la_scena(sc, chi, porta):
    """Server + `firefox-esr --kiosk` in the session; waits for «caricata»."""
    b = lambda s: base64.b64encode(s.encode()).decode()     # noqa: E731
    c, t = sc.dentro(
        "set -e; h=/home/{c}; mkdir -p $h/.c23-profilo; "
        "echo {srv} | base64 -d > $h/c23-servitore.py; echo {pag} | base64 -d > $h/c23.html; "
        "echo {pref} | base64 -d > $h/.c23-profilo/user.js; : > $h/c23.log; "
        "chown -R {c}: $h/.c23-profilo $h/c23-servitore.py $h/c23.html $h/c23.log; set +e; "
        "u=$(id -u {c}); "
        "setsid runuser -u {c} -- python3 $h/c23-servitore.py {p} $h/c23.html $h/c23.log "
        "</dev/null >/dev/null 2>&1 & "
        "d=''; for i in $(seq 1 40); do d=$(ls /run/user/$u 2>/dev/null | "
        "grep -E '^wayland-[0-9]+$' | head -1); [ -n \"$d\" ] && break; sleep 0.5; done; "
        "[ -n \"$d\" ] || {{ echo 'no wayland socket'; exit 2; }}; sleep 1; "
        "setsid runuser -u {c} -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
        "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
        "XDG_SESSION_TYPE=wayland HOME=$h firefox-esr --no-remote --new-instance "
        "--profile $h/.c23-profilo --kiosk http://127.0.0.1:{p}/ "
        "</dev/null >$h/.c23-firefox.log 2>&1 & "
        "for i in $(seq 1 80); do grep -q caricata $h/c23.log && {{ echo started; exit 0; }}; "
        "sleep 0.5; done; echo 'the scene did not say «caricata»'; tail -5 $h/.c23-firefox.log; "
        "exit 1".format(c=chi, p=porta, srv=b(SERVITORE), pag=b(pagina_scena()),
                        pref=b(C21.PREFERENZE)), 90)
    return c == 0, t


def leggi_il_quaderno(sc, chi):
    _c, t = sc.dentro("cat /home/%s/c23.log 2>/dev/null" % chi, 30)
    return [r for r in t.splitlines() if r.strip()]


# ═══════════════════════════════════════════════════════════════════════════
#  THE REAL KEYS
# ═══════════════════════════════════════════════════════════════════════════
def manda(g, passi):
    """⭐ REAL keys given to the browser: `Input.dispatchKeyEvent` or the W3C actions."""
    if hasattr(g, "cdp"):
        mod = 0
        for tipo, nome in passi:
            if nome in SPECIALI:
                key, code, vk, _w, bit = SPECIALI[nome]
                if tipo == "giu":
                    mod |= bit
                g.cdp.chiama("Input.dispatchKeyEvent",
                             type="rawKeyDown" if tipo == "giu" else "keyUp",
                             key=key, code=code, windowsVirtualKeyCode=vk, modifiers=mod)
                if tipo == "su":
                    mod &= ~bit
            else:
                code = "Space" if nome == " " else "Key" + nome.upper()
                vk = 32 if nome == " " else ord(nome.upper())
                p = dict(type="keyDown" if tipo == "giu" else "keyUp", key=nome, code=code,
                         windowsVirtualKeyCode=vk, modifiers=mod)
                if tipo == "giu" and not (mod & 2):
                    p["text"] = p["unmodifiedText"] = nome
                g.cdp.chiama("Input.dispatchKeyEvent", **p)
            time.sleep(PAUSA_MS / 1000.0)
        return
    az = []
    for tipo, nome in passi:
        v = SPECIALI[nome][3] if nome in SPECIALI else nome
        az.append({"type": "keyDown" if tipo == "giu" else "keyUp", "value": v})
        az.append({"type": "pause", "duration": PAUSA_MS})
    g.m.chiama("WebDriver:PerformActions",
               {"actions": [{"type": "key", "id": "tastiera", "actions": az}]})
    g.m.chiama("WebDriver:ReleaseActions")


def fotografa_e_leggi(g, geo, voluto, salva, nome):
    """Photographs until the strip says `voluto` or `ATTESA_S` runs out.
    Returns (value read or None, why)."""
    from PIL import Image
    fine = time.time() + ATTESA_S
    letto, perche, png = None, "no photograph", None
    while True:
        try:
            png = C21.foto_piena(g)
        except Exception as e:                   # noqa: BLE001
            png, perche = None, "photograph failed: %s" % str(e)[:120]
        if png:
            im = Image.open(io.BytesIO(png)).convert("RGB")
            letto, perche = leggi_striscia(campionatore(im, geo))
            if letto == voluto:
                break
        if time.time() >= fine:
            break
        time.sleep(FOTO_OGNI_S)
    if salva and png:
        with open(os.path.join(salva, "%s.png" % nome), "wb") as fh:
            fh.write(png)
    return letto, perche


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST OF ONE BROWSER
# ═══════════════════════════════════════════════════════════════════════════
def osserva(nome, o, sc, chi):
    """Returns the browser's row, with the cases' `esiti` (or `esito` CIECO)."""
    print("\n══ %s ══════════════════════════════" % nome.upper(), flush=True)
    riga = {"browser": nome}
    g = VERI.accendi_guida(nome, o)
    try:
        print("   stage: %s" % g.palco(), flush=True)
        if o.largo:
            print("   %s" % C20V.dimensiona(g, nome, o.largo, o.alto), flush=True)
        pr = VERI.Prova(g, o, o.url, o.parola)
        ok, m = pr.apri()
        if not ok:
            return dict(riga, esito=CIECO, perche="the page does not open: " + m)
        e, m, s = pr.entra(o.parola)
        if e != VERDE:
            return dict(riga, esito=CIECO, perche="the login: " + m)
        e, m, s = pr.primo_fotogramma()
        e, m = C20V.desktop_scuro_ma_vivo(e, m, s)
        print("   ⭐ first frame: %s" % m, flush=True)
        if e != VERDE:
            return dict(riga, esito=CIECO, perche="without an image there is no looking: " + m)
        geo = g.js(C21.JS_GEOMETRIA)
        if not geo:
            return dict(riga, esito=CIECO, perche="`REMOTIX_PUNTATORE.geometria` is not there")
        print("   canvas %sx%s · buffer %sx%s" % (geo["tl"], geo["ta"], geo["bw"], geo["bh"]),
              flush=True)
        # ⭐ C21's wake-up: on GNOME the session is born in the overview
        print("   wake-up: %s" % C21.sveglia(g, geo), flush=True)
        ok, t = accendi_la_scena(sc, chi, o.porta_scena)
        print("   scene: %s" % ((t or "?").splitlines() or ["?"])[-1], flush=True)
        if not ok:
            return dict(riga, esito=CIECO, perche="the scene does not start: %s" % t[-300:])
        time.sleep(3)
        # ⚠ A click in the remote field: the new window takes the keyboard
        #   focus even where the desktop does not give it by itself.
        x, y = C21.dal_desktop_al_vetro(geo, geo["tl"] * 0.5, geo["ta"] * 0.26)
        g.clic(x, y)
        time.sleep(1.0)
        esiti, casi = [], []
        for titolo, base, seq, atteso in CASI:
            if o.senza_maiusc:
                seq = senza_maiusc(seq)
            corto = titolo.split()[0]
            manda(g, PULISCI)
            vuoto, pv = fotografa_e_leggi(g, geo, "", o.salva, "%s-c%s-0vuoto" % (nome, corto))
            manda(g, scrivi(base))
            vb, pb = fotografa_e_leggi(g, geo, base, o.salva, "%s-c%s-1base" % (nome, corto))
            n0 = len(leggi_il_quaderno(sc, chi))
            manda(g, seq)
            visto, pvi = fotografa_e_leggi(g, geo, atteso, o.salva,
                                           "%s-c%s-2dopo" % (nome, corto))
            es, msg = giudica_caso(titolo, base, atteso, vuoto, vb, visto)
            if es == CIECO and (vuoto is None or vb is None):
                msg += " — %s" % (pv or pb)
            elif visto is None:
                es, msg = CIECO, "%s: the strip cannot be read after the sequence: %s" % (
                    titolo, pvi)
            quad = leggi_il_quaderno(sc, chi)[n0:]
            tasti = [r[2:] for r in quad if r.startswith("K ")]
            print("   %s %s" % ({VERDE: "⭐ 0", ROSSO: "⛔ 1", CIECO: "⚠ 3"}[es], msg),
                  flush=True)
            if es != VERDE:
                print("        remote keydowns: %s" % " | ".join(tasti)[:400], flush=True)
            esiti.append(es)
            casi.append({"caso": corto, "esito": es, "visto": visto, "atteso": atteso,
                         "keydown_remoti": tasti})
            if es == CIECO:
                break
        try:
            st = g.js("return REMOTIX.input_classico.stato().tasti_premuti")
        except Exception as ex:                  # noqa: BLE001
            st = "? (%s)" % str(ex)[:80]
        print("   keys pressed for the page, at the end: %s" % (st,), flush=True)
        return dict(riga, esiti=esiti, casi=casi, tasti_premuti_alla_fine=st)
    finally:
        try:
            g.chiudi()
        except Exception as ex:                  # noqa: BLE001
            print("   ⚠ closing the browser: %s" % ex)


def giudica_browser(riga, guasto):
    if "esiti" not in riga:
        return riga
    es = riga["esiti"]
    if not guasto:
        e = esito_complessivo(es)
        perche = {VERDE: "all %d cases come out right" % len(es),
                  ROSSO: "%d cases out of %d do not come out right" % (es.count(ROSSO), len(es)),
                  CIECO: "one case could not be looked at"}[e]
        return dict(riga, esito=e, perche=perche)
    e = esito_col_guasto(es)
    perche = {VERDE: "⭐ FAULT SEEN: without Shift all %d cases are red" % len(es),
              ROSSO: "⛔ FAULT NOT SEEN: without Shift %d cases come out right all the same"
                     % es.count(VERDE),
              CIECO: "with the fault one case could not be looked at"}[e]
    return dict(riga, esito=e, perche=perche)


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--scatola", choices=sorted(PORTE))
    a.add_argument("--porta", type=int, help="the product's port (normally that "
                   "of the net's box)")
    a.add_argument("--contenitore", default="", help="the podman container, if it is not "
                   "rete11-<scatola> (the development boxes rete14-*)")
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--browser", default="firefox,chrome")
    a.add_argument("--visibile", action="store_true",
                   help="real windows (in the nested compositor) instead of headless")
    a.add_argument("--salva", default="", help="folder for the photographs")
    a.add_argument("--senza-maiusc", action="store_true",
                   help="INJECTED FAULT: the same sequences without ever pressing Shift")
    a.add_argument("--certifica", action="store_true")
    a.add_argument("--tetto-s", type=int, default=45)
    a.add_argument("--porte-base", type=int, default=3231)
    a.add_argument("--largo", type=int, default=3840)
    a.add_argument("--alto", type=int, default=2160)
    o = a.parse_args()
    if o.certifica:
        return certifica()
    if not o.scatola and o.porta:
        o.scatola = {p: s for s, p in PORTE.items()}.get(o.porta)
    if not o.scatola:
        print("⛔ --scatola is needed, or a --porta of the net (%s)" % PORTE)
        return 3
    porta = o.porta or PORTE[o.scatola]
    o.url = "https://%s:%d/" % (o.host, porta)
    o.parola = "c23-" + secrets.token_hex(6)
    o.scena, o.continuita_s, o.registro_cmd = "viva", 8, ""
    o.lascia_acceso = False
    o.porta_scena = random.randint(39000, 39899)
    if o.salva:
        os.makedirs(o.salva, exist_ok=True)
    sc = C20V.Scatola(o.scatola)
    if o.contenitore:
        sc.contenitore = o.contenitore
    chi = "c23u%03d" % random.randint(0, 999)
    assert MODELLO_INQUILINO.match(chi)
    o.utente = chi
    print("⭐ 11-c23 · %s · %s · inquilino %s · browser %s · %s%s"
          % (sc.contenitore, o.url, chi, o.browser,
             "real windows" if o.visibile else "HEADLESS",
             " · ⛔ INJECTED FAULT --senza-maiusc" if o.senza_maiusc else ""))
    righe = []
    for b in [x.strip() for x in o.browser.split(",") if x.strip()]:
        sc.sgombera(chi)
        c, t = sc.crea(chi, o.parola)
        if c != 0:
            print("⛔ I could not create %s: %s" % (chi, t[-200:]))
            return 3
        try:
            r = giudica_browser(osserva(b, o, sc, chi), o.senza_maiusc)
        except Exception as e:                   # noqa: BLE001
            r = {"browser": b, "esito": CIECO, "perche": "the bench fell over: %r" % e}
        finally:
            sc.sgombera(chi)
        print("   ▶ %s: %s — %s" % (b, NOME_ESITO.get(r["esito"], r["esito"]),
                                   r.get("perche")))
        print("RIGA " + json.dumps(r, ensure_ascii=False), flush=True)
        righe.append(r)
    v = [r["esito"] for r in righe]
    esito = ROSSO if ROSSO in v else (CIECO if CIECO in v else VERDE)
    print()
    if o.senza_maiusc:
        print({VERDE: "⭐ THE INJECTED FAULT WAS SEEN (outcome 0: the other way round, "
                      "like every fault of the net)",
               ROSSO: "⛔⛔ THE INJECTED FAULT WAS NOT SEEN",
               CIECO: "⚠ with the injected fault I could NOT look ⇒ 3"}[esito])
    else:
        print("%s C23(%s): %s" % ({VERDE: "⭐", ROSSO: "⛔⛔", CIECO: "⚠"}[esito],
                                  o.scatola, NOME_ESITO[esito]))
    return esito


if __name__ == "__main__":
    sys.exit(main())
