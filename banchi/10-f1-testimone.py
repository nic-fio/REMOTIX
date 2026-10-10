#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
10-f1-testimone — ⭐⭐ THE WITNESS THAT SHOWS THE REMOTE DESKTOP.
                     An IMAGE, not a counter.
===========================================================================

    python3 banchi/10-f1-testimone.py scatta --utente provanic1 \\
            --fuori /tmp/desktop.png
    python3 banchi/10-f1-testimone.py scatta --utente provanic1 \\
            --fuori /tmp/desktop.png --marca f1-taratura
    python3 banchi/10-f1-testimone.py --certifica

Exits **0** if it looked and the judgement asked for holds · **1** if it looked
and the judgement does NOT hold (red) · ⛔ **3** if it **could not look** — and
the third outcome is not a red: it is *"I did not look"*, which in this project
is a different thing and must be said with different words (`LEZIONI.md` §1.9,
and rule 5 of the preamble: **`None` is not zero**).

===========================================================================
⛔⛔ WHY IT EXISTS — four routes tried, and no picture
===========================================================================

Until 25 Aug 2026 phase 10 would not close for one reason only: ⛔ **nobody
could LOOK at the remote desktop.**  The coordination had tried:

  1. the **child's snapshot** — `SIGUSR1` to the child with `--rilievo` on:
     `cattura.bgrx` stayed **at zero bytes**;
  2. the **screenshot** of the laptop — `grim` answers
     *"compositor doesn't support wlr-screencopy-unstable-v1"*: GNOME does not give it;
  3. the **canvas read from the page** (`canvas.toDataURL`) via Marionette — ⛔ every
     reattach made the WebDriver session expire, and reopening it **brought
     down the RCP session**: the server logged *"nobody is watching it any more"*
     a few moments later;
  4. the **frame count** — it says **how many**, ⛔ not **what**.

===========================================================================
⭐ THE ROUTE CHOSEN, AND WHY — "the client that decodes"
===========================================================================

This witness takes the **third way of the assignment's frame**: it attaches
to the session with the **test client** (`banchi/01-b3-cliente.py`), gets the
frames **from the wire** with `--video-scrivi`, and hands them to **`ffmpeg`**,
which is on the test machine.  ⇒ Out comes a **PNG**.

⭐ The three reasons why this is the route, and not the others:

  · ⛔ **It has no browser inside.**  The canvas route died on WebDriver's
    fragility, not on the pixels: every reattach reopened the session
    and detached the client.  Here there is nothing to reattach — **one single
    process, which opens, looks and closes**.
  · ⭐⭐ **It does not break the session it is watching**, and it is `[M]` on the
    server log, not believed — ⚠ **but not in the way I wrote here the first
    time, and the correction is worth more than the sentence**.  I believed two
    clients of the same user could coexist (I4, "occupied now: N").  ⛔ **They do
    not coexist**: `[M]` 25 Aug 2026, 15:31 — with a viewer already attached
    to `provanic1`, the witness was **REFUSED**:
        `slot DENIED to provanic1 …: another client of this same user holds it
         (taken: 1) — that occupant gave a sign of life 916 ms ago, and the
         eviction did NOT trigger` · `congedo motivo=0x0f`
    ⇒ ⭐ **And this is the right outcome**: the product **does not evict whoever is
      watching to make room for whoever arrives**, and the witness — instead of
      making up an image — says **"I DID NOT LOOK"** and exits **3**.  `[M]` The
      viewer stayed attached: in the log, in that stretch, **no**
      line "the last session is leaving" and **no** "nobody is watching it any
      more".
    ⛔ **And the limit is declared**: as long as someone watches that session, the
      witness **cannot look at it**.  ⚠ It is not a fallback to add: eviction
      already exists and triggers on the **mute** client (threshold 15 000 ms) —
      forcing it here would mean detaching the user to photograph them.
  · ⭐ **It runs on its own**, with no terminal and nobody watching: it is the
    condition set by the assignment.

⭐ And one thing the product already does well, and that this witness exploits:
   on attach to a **still** desktop the child forces itself to deliver —
   `[M]` *"a KEYFRAME is due and the scene has been still for 400 ms: restarting
   the stream to make myself deliver a frame"*.  ⇒ One single frame is enough,
   and on a motionless desktop the witness sees all the same.  ⚠ Without that
   line `--sveglia` would be needed, which instead remains the last resort.

⚠ **And it is declared where it looks**, because it is not the last link: the
witness sees the pixels **AFTER the wire and BEFORE the browser's decoder** — that
is, exactly the bytes Firefox would receive.  ⛔ What this witness **cannot**
see is a defect born **inside** the page's canvas (a wrong `drawImage`, a
crooked `bitmaprenderer`).  ⇒ For those the canvas is needed, and this tool
does not replace it: **it comes before it**.

===========================================================================
⛔⛔ HOW ONE PROVES THE WITNESS SEES — and it is the half that counts
===========================================================================

A witness that returns a **black** PNG and one that returns the desktop
**look the same** from the code's side.  ⇒ It is calibrated, like every gauge
of this phase (`LEZIONI.md` §1.33):

  1. ⭐ **the positive control**: a **machine-readable** mark is painted on the
     remote desktop (`04-b30-scena --movimento marca --giro NOME`) and it is
     verified that the witness **finds it again** — with the **certified reader**
     `banchi/03-marca.py`, which is not part of this bench and is not touched.  ⭐ The
     mark carries the **round name** inside the pixels: it is not enough that *a*
     mark is there, it must be **mine**.  A witness that looked at another
     tenant's desktop would give **red** here.
  2. ⛔ **the negative control**: with a **black** desktop the witness must say
     so, not return any image passing it off as the desktop.  ⭐ A PNG
     that exists **is not** a PNG that shows something.
     `[M]` Done on the real thing, 25 Aug 2026: `provanic3`'s background set to
     `#000000` ⇒ **QUASI-NERO**, mean **0.28**, lit **0.00121**.  ⭐ And below
     the GNOME bar the frame is black **byte for byte** (lit
     0.00000000, max luma 1): the gauge is not blind, it is **sensitive to one
     pixel in eight hundred**.  ⛔ A GNOME desktop is never "all black" —
     the clock at the top does not go off — and that is why "quasi-nero" exists.
  3. ⛔ **and if it could not look it returns `None`**: zero frames taken from
     the wire, `ffmpeg` not decoding, the session not opening — they are
     all *"I did not look"*, and **none of them is "it is black"**.

===========================================================================
⛔⛔ THE ESC TRAP — whoever uses this witness will meet it
===========================================================================

To see windows as windows one must **leave GNOME's overview**, and it is done
by sending **ESC** (`banchi/09-b72-tasto.py --tasti 1`, phase 9).
⛔ **But ESC is also the key that closes a modal dialog.**

`[M]` 25 Aug 2026: Firefox in the remote session stops on the dialog
*"Profile Missing — Your Firefox profile cannot be loaded"*.  Sending ESC before
the snapshot, the dialog **disappeared** and the snapshot showed an **empty**
desktop — that is, exactly the symptom the phase had got stuck on: *"the process
is alive and something draws, but nobody has ever seen its window"*.
⇒ ⭐ **The snapshot is taken FIRST without ESC, and only afterwards, if needed,
  ESC is sent and the snapshot retaken.**  Two snapshots, not one — and the
  difference between the two is a fact, not a nuisance.

===========================================================================
⚠ WHAT RUNS WHERE, and why it is split in two
===========================================================================

  · the **grab** (client + `ffmpeg`) runs **on the test machine, inside the
    container**: `aioquic` is there, and on the host it is not;
  · the **pixel reading** runs **here**, on the laptop: `numpy` and `Pillow`
    are here and in the container they are not.  ⚠ It is the same boundary that
    `03-marca.py` declares by itself in `np_o_muori()`.

⇒ The PNG travels back with `scp`.  ⛔ And if `numpy` is not here either, the
  witness **does not pretend**: it returns "I could not judge", which is `None`.
"""

import argparse
import base64
import glob
import importlib.util
import json
import os
import shlex
import struct
import subprocess
import sys
import tempfile
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ── the test machine's defaults (all overridable from the command line:
#    ⛔ `CODER.md` §2-bis, one single route and no environment variable that
#    changes the measured quantity) ──────────────────────────────────────────
MACCHINA = "nicfio@192.168.0.2"
PAROLA_SUDO = "nicfio"
ENTRA = "/media/REMOTIX/enter.sh"
INDIRIZZO = "192.168.0.2"
PORTA = 8400
ALBERO = "/media/REMOTIX/src/10fin-src"
LAV = "/media/REMOTIX/tmp/10f1"
PAROLA_FILE = "/media/REMOTIX/tmp/10nic/parola"

# ⚠ Inside the container the two mounts show up under other names (`enter.sh`).
def _dentro(percorso):
    if percorso.startswith("/media/REMOTIX/src/"):
        return "/srv/src/" + percorso[len("/media/REMOTIX/src/"):]
    if percorso.startswith("/media/REMOTIX/"):
        return "/srv/remotix/" + percorso[len("/media/REMOTIX/"):]
    return percorso


# ═══════════════════════════════════════════════════════════════════════════
# THE JUDGEMENT THRESHOLDS — ⛔ declared here and printed in every outcome, because
# "black" and "drawn" are a verdict, and a verdict without its gauge is
# an opinion.
# ═══════════════════════════════════════════════════════════════════════════
LUMA_NERO = 16.0       # below this luma a pixel is "off"
FRAZIONE_NERO = 0.001  # less than 0.1 % of pixels lit ⇒ the screen is BLACK
# ⛔ "FLAT COLOUR" IS MEASURED ON HOW MUCH OF THE SCREEN IS THE MOST COMMON COLOUR,
#    not on the number of distinct colours — and the first draft got exactly this wrong.
#    `[M]` 25 Aug 2026, fault G8 of `--certifica`: a **black screen with
#    the mark on it** has only **two** colours (black and white) and was
#    declared "flat colour".  ⚠ That is, the witness threw away the only proof
#    that it had really looked, and did so with a plausible verdict.
#    ⇒ The right criterion is **how much of the screen is NOT the background**.
FRAZIONE_PIATTO = 0.001
# ⭐⭐ "NEARLY BLACK" — and the threshold is MEASURED, not chosen.  `[M]` 25 Aug 2026,
#    the negative control on the real thing: `provanic3`'s desktop with the background set to
#    `#000000`, captured from the wire.  Below the GNOME bar (y ≥ 40) the
#    frame is **black byte for byte**: lit 0.00000000, max luma **1**.
#    ⛔ But the bar at the top — 40 rows out of 1080 — carries the clock and the icons, and
#    with those the whole screen makes lit **0.00121**: just ABOVE the black
#    threshold, that is, a GNOME desktop is NEVER "all black".
#    ⚠ A witness that stopped at "drawn" would tell the truth and be of
#      no use: that screen has nothing on it.
#    ⇒ The pixel mean separates the two worlds by a factor of a hundred:
#         black desktop + bar    mean **0.28**
#         real desktop           mean **34.3** (empty) … **106.9** (with the scene)
#      The threshold is set at **2.0**, that is, in the middle of the gap between the two.
MEDIA_QUASI_NERO = 2.0

# BT.709, the same matrix `03-marca.py` declares: here it only serves to make
# ONE number out of three channels.
PESI_LUMA = (0.2126, 0.7152, 0.0722)


def _marca_modulo():
    """⭐ The certified reader is IMPORTED, not rewritten.

    ⛔ `03-marca.py` is the only thing in the chain that is not touched: it is the one
       that decides whether the mark is there.  Rewriting its geometry here would mean
       having two readers that can diverge in silence — and the day they
       diverge, the red would be given by the wrong one.
    """
    perc = os.path.join(QUI, "03-marca.py")
    if not os.path.exists(perc):
        return None
    spec = importlib.util.spec_from_file_location("marca03", perc)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _numpy_o_niente():
    """⛔ Returns `None` if it is not there, and the caller must say "I did not judge".

    ⚠ The temptation was a pure-Python fallback that says "more or less" whether it
      is black.  It would be a different gauge from the one it was calibrated with, that is the
      error form the assignment asks not to commit: a number in place of
      a measurement.
    """
    try:
        import numpy
        return numpy
    except ImportError:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE JUDGEMENT ON THE PIXELS — "there is a PNG" is not "the PNG shows something"
# ═══════════════════════════════════════════════════════════════════════════
def giudica(percorso):
    """Given a PNG, it says **what is inside**.

    Returns a dictionary, or ⛔ **`None`** if it could not look (file
    not there, unreadable file, `numpy`/`Pillow` missing).

    The keys:
      verdetto   «nero» · «tinta-unita» · «disegnato»
      larghezza, altezza, media, dev, minimo, massimo
      colori     how many distinct colours
      accesi     fraction of pixels with luma > LUMA_NERO
      diversi    fraction of pixels that differ from the most common colour
    """
    if not percorso or not os.path.exists(percorso):
        return None
    if os.path.getsize(percorso) == 0:
        return None
    np = _numpy_o_niente()
    if np is None:
        return None
    try:
        from PIL import Image
        img = np.asarray(Image.open(percorso).convert("RGB"))
    except Exception:
        # ⛔ A truncated PNG or a non-PNG is "I did not look", not "it is black":
        #    it is exactly the wound the preamble calls rule 5.
        return None
    if img.ndim != 3 or img.shape[2] != 3 or img.size == 0:
        return None

    h, w = img.shape[0], img.shape[1]
    f = img.astype("float32")
    luma = (f[:, :, 0] * PESI_LUMA[0] + f[:, :, 1] * PESI_LUMA[1]
            + f[:, :, 2] * PESI_LUMA[2])
    accesi = float((luma > LUMA_NERO).mean())

    piatto = img.reshape(-1, 3)
    # ⚠ On 1920x1080 `np.unique` on the rows is costly; 1 pixel in 4 is sampled in
    #   each direction.  ⛔ And it is SAID, because "distinct colours" here means
    #   "distinct in the sample", and on an image with very few colours —
    #   which is the case that decides "flat colour" — the sample sees them all.
    campione = img[::4, ::4].reshape(-1, 3)
    colori = int(len(np.unique(campione, axis=0)))
    # the most common colour, and how much of the screen is NOT that one
    vista = np.ascontiguousarray(campione).view(
        np.dtype((np.void, campione.dtype.itemsize * 3)))
    _u, conti = np.unique(vista, return_counts=True)
    diversi = float(1.0 - conti.max() / float(len(campione)))

    media = float(f.mean())
    if accesi < FRAZIONE_NERO:
        verdetto = "nero"
    elif media < MEDIA_QUASI_NERO:
        # ⭐ "there is a screen, and there is nothing on it" — and it must be said with
        #    its own words, because it is the outcome the negative control must produce on
        #    a GNOME desktop, where the bar at the top never goes off.
        verdetto = "quasi-nero"
    elif diversi < FRAZIONE_PIATTO:
        verdetto = "tinta-unita"
    else:
        verdetto = "disegnato"

    return {
        "verdetto": verdetto,
        "larghezza": w, "altezza": h,
        "media": round(media, 3),
        "dev": round(float(f.std()), 3),
        "minimo": int(img.min()), "massimo": int(img.max()),
        "colori": colori,
        "accesi": round(accesi, 6),
        "diversi": round(diversi, 6),
        "soglie": {"luma_nero": LUMA_NERO, "frazione_nero": FRAZIONE_NERO,
                   "media_quasi_nero": MEDIA_QUASI_NERO,
                   "frazione_piatto": FRAZIONE_PIATTO},
    }


def leggi_la_marca(percorso, giri):
    """⭐ The positive control: is the mark there, and is it **mine**?

    `giri` is the list of round names I ran myself.  ⛔ The inversion
    is a LIST and not a guess: the mark carries 32 bits of FNV-1a, which cannot
    be inverted (it is the rule `03-marca.py` writes by itself).

    Returns:
      `None`                          ⛔ I could not look (no numpy,
                                      no reader, frame too small
                                      for the mark to fit)
      {"c_e": False, "perche": …}     the mark is NOT there — and it is a red, not an
                                      "I don't know"
      {"c_e": True, "giro": …, "mio": bool, "disegno": …, "istante_us": …}
    """
    np = _numpy_o_niente()
    m = _marca_modulo()
    if np is None or m is None:
        return None
    if not percorso or not os.path.exists(percorso) \
            or os.path.getsize(percorso) == 0:
        return None
    try:
        img = m.carica(percorso)
    except Exception:
        return None
    r = m.leggi_marca(img)
    if not r.get("c_e"):
        # ⛔ THE DISTINCTION THAT COSTS DEARLY IF LOST: "the mark would not
        #    fit" (frame too small) is **I did not look**;
        #    "the mark is not there" is a red.  `03-marca.py` already keeps them
        #    apart by putting the key `serve` only in the first.
        if "serve" in r:
            return None
        return {"c_e": False, "perche": r.get("perche"),
                "contrasto": r.get("contrasto")}
    numero = r.get("giro")
    nomi = {m.fnv1a32(g): g for g in giri}
    return {"c_e": True,
            "giro_numero": numero,
            "giro": nomi.get(numero),
            "mio": numero in nomi,
            "disegno": r.get("disegno"),
            "istante_us": r.get("istante_us"),
            "contrasto": r.get("contrasto")}


# ═══════════════════════════════════════════════════════════════════════════
# THE GRAB — on the test machine, inside the container
# ═══════════════════════════════════════════════════════════════════════════
def _ssh(comando, secondi=180, macchina=MACCHINA):
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o",
                        "ConnectTimeout=15", macchina, comando],
                       capture_output=True, timeout=secondi)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def _nel_contenitore(script, secondi=180, macchina=MACCHINA,
                     parola_sudo=PAROLA_SUDO, lav=LAV):
    """Runs a bash script **inside** the container, as administrator.

    ⛔ The script travels in **base64** and not inside quotes: two levels
       of shell (ssh and `enter.sh -lc`) eat the quotes, and a crooked
       command here would give a "zero frames" that looks in every way like a
       mute server.  ⚠ It is error form E2 of the bench catalogue.
    ⛔ And the sudo password goes through `printf`, which is a builtin: it does not appear in
       the `argv` of any process (`FASE10-PREAMBOLO` §"the test machine").
    """
    b64 = base64.b64encode(script.encode("utf-8")).decode("ascii")
    riga = ("printf '%%s' '%s' | base64 -d > %s/passo.sh && "
            "printf '%%s\\n' %s | bash %s --root "
            "\"bash %s/passo.sh\""
            % (b64, lav, parola_sudo, ENTRA, _dentro(lav)))
    return _ssh(riga, secondi=secondi, macchina=macchina)


def _leggi_esito_cliente(testo):
    """From the client log: **how many frames ARRIVED**.

    ⛔ Returns `None` when nothing arrived — and not zero.  `LEZIONI.md`
       §1.30 says to count how much stimulus ARRIVED before
       judging: here the stimulus **is** the frame, and a bench that
       decoded an empty file would say "black screen" about a server that never
       had a chance to send anything.
    """
    fotogrammi = None
    chiavi = None
    misura = None
    sessione = None
    for r in testo.splitlines():
        if "SESSIONE:" in r:
            sessione = r.strip()
        if "[vid]" not in r:
            continue
        if "no frame" in r:
            continue
        # «   [vid]  12 frames (2 keys), 1920x1080, written to …»
        pezzi = r.split("[vid]", 1)[1].strip().split()
        try:
            fotogrammi = int(pezzi[0])
            chiavi = int(pezzi[2].lstrip("("))
            misura = pezzi[4].rstrip(",")
        except Exception:
            continue
    if not fotogrammi:
        return None
    return {"fotogrammi": fotogrammi, "chiavi": chiavi, "misura": misura,
            "sessione": sessione}


SCRIPT_PRESA = r"""
set -u
LAV=%(lav_dentro)s
CLIENTE=%(cliente)s
TUTTI=%(tutti)s
rm -f "$LAV/flusso.264" "$LAV/scatto.png" "$LAV/cliente.log"
rm -f "$LAV"/scatto-[0-9][0-9][0-9].png
timeout %(tetto)d python3 -u "$CLIENTE" \
    --indirizzo %(indirizzo)s --porta %(porta)d \
    --utente %(utente)s --parola-file %(parola)s \
    --video-scrivi "$LAV/flusso.264" --resta %(resta).1f %(altro)s \
    > "$LAV/cliente.log" 2>&1
echo "=== CLIENTE rc=$? ==="
cat "$LAV/cliente.log"
echo "=== FFMPEG ==="
if [ -s "$LAV/flusso.264" ]; then
    # ⛔ `-update 1` ALWAYS rewrites the same file: the LAST decoded frame wins,
    #    which is the one the desktop shows now.  Taking the
    #    first would give the opening keyframe, that is the screen of a second ago.
    ffmpeg -hide_banner -loglevel error -i "$LAV/flusso.264" \
           -vsync 0 -update 1 -y "$LAV/scatto.png"
    echo "rc=$?"
    ls -l "$LAV/scatto.png" 2>/dev/null || echo "⛔ no snapshot"
    # ⭐⭐ AND THE SEQUENCE, when asked for (`--tutti`) — 25 Aug 2026.
    #
    # ⛔ It is not a luxury: **the last frame alone lies by omission.**
    #    `[M]` Firefox's "Profile Missing" dialog was found this way —
    #    it appeared halfway through the grab and vanished before the end, and on the last
    #    snapshot it was not there.  ⇒ A desktop that PASSES THROUGH a state does not show it
    #    at the final instant, and whoever looks only at that concludes "there is
    #    nothing" — which is a `[?]` passed off as an `[M]`.
    if [ -n "$TUTTI" ] && [ -s "$LAV/flusso.264" ]; then
        echo "=== FFMPEG TUTTI ==="
        ffmpeg -hide_banner -loglevel error -i "$LAV/flusso.264" \
               -vsync 0 -y "$LAV/scatto-%%03d.png"
        echo "rc=$?"
        ls "$LAV"/scatto-*.png 2>/dev/null | wc -l
    fi
else
    echo "⛔ the stream is empty or missing: nothing to decode"
fi
"""


def scatta(utente, fuori, resta=6.0, porta=PORTA, indirizzo=INDIRIZZO,
           albero=ALBERO, lav=LAV, parola_file=PAROLA_FILE,
           macchina=MACCHINA, parola_sudo=PAROLA_SUDO, sveglia=None,
           loquace=False, tutti=False):
    """⭐ Pulls down a PNG of `utente`'s remote desktop, and writes it to `fuori`.

    Returns a dictionary with `png` and the grab's counts, or ⛔ **`None`** if
    it **could not look**.  ⚠ `None` is not "the screen was black".
    """
    altro = ""
    if sveglia:
        # ⭐ THE WAKE-UP, and it is needed for a measured reason: `[M]` the
        #    child's log says "idle waits (still scene: Mutter delivers only
        #    when something changes)".  On a **motionless** desktop the stage may
        #    deliver nothing after the opening keyframe.  ⇒ A canvas change
        #    forces the chain to redo a whole frame.
        # ⚠ But it changes what the desktop SEES (it resizes), so it is
        #   OFF by default and whoever turns it on declares it.
        altro = "--adatta %s@1.0 --adatta %dx%d@2.0" % (
            sveglia, 1920, 1080)

    script = SCRIPT_PRESA % {
        "lav_dentro": _dentro(lav),
        "cliente": _dentro(albero) + "/banchi/01-b3-cliente.py",
        "tetto": int(resta) + 60,
        "indirizzo": indirizzo, "porta": porta, "utente": utente,
        "parola": _dentro(parola_file), "resta": resta, "altro": altro,
        "tutti": "1" if tutti else "",
    }
    rc, out, err = _nel_contenitore(script, secondi=int(resta) + 120,
                                    macchina=macchina,
                                    parola_sudo=parola_sudo, lav=lav)
    if loquace:
        sys.stderr.write(out + err)
    conti = _leggi_esito_cliente(out)
    if conti is None:
        return {"png": None, "conti": None,
                "perche": ("⛔ I DID NOT LOOK: no frame arrived "
                           "from the wire.  ⚠ It is not \"the screen was black\": it is that "
                           "the stage delivered nothing, or the session "
                           "did not open"),
                "registro": (out + err)[-1500:]}
    if "⛔ no snapshot" in out or "rc=0" not in out.split("=== FFMPEG ===")[-1]:
        return {"png": None, "conti": conti,
                "perche": ("⛔ I DID NOT LOOK: %d frames arrived but "
                           "`ffmpeg` did not produce the snapshot"
                           % conti["fotogrammi"]),
                "registro": (out + err)[-1500:]}

    os.makedirs(os.path.dirname(os.path.abspath(fuori)) or ".", exist_ok=True)
    if os.path.exists(fuori):
        os.unlink(fuori)          # ⛔ never judge the file of an earlier round
    p = subprocess.run(["scp", "-o", "BatchMode=yes", "-q",
                        "%s:%s/scatto.png" % (macchina, lav), fuori],
                       capture_output=True, timeout=120)
    if p.returncode != 0 or not os.path.exists(fuori):
        return {"png": None, "conti": conti,
                "perche": "⛔ I DID NOT LOOK: the snapshot did not arrive here (%s)"
                          % p.stderr.decode("utf-8", "replace").strip()[:200],
                "registro": (out + err)[-1500:]}
    sequenza = []
    if tutti:
        # ⭐ The sequence sits NEXT TO the snapshot, with the same name plus the
        #   number: whoever looks at a folder understands by themselves they are the same
        #   round.  ⚠ And if it does not arrive, the snapshot's outcome is NOT soiled: the
        #   snapshot arrived, and this is a declared extra.
        radice = os.path.splitext(os.path.abspath(fuori))[0]
        for vecchio in glob.glob(radice + "-[0-9][0-9][0-9].png"):
            os.unlink(vecchio)
        q = subprocess.run(["bash", "-c",
                            "scp -o BatchMode=yes -q '%s:%s/scatto-[0-9][0-9][0-9].png' %s"
                            % (macchina, lav, shlex.quote(
                                os.path.dirname(radice) or "."))],
                           capture_output=True, timeout=300)
        if q.returncode == 0:
            for f in sorted(glob.glob(os.path.join(
                    os.path.dirname(radice) or ".", "scatto-[0-9][0-9][0-9].png"))):
                nuovo = radice + "-" + os.path.basename(f).split("-")[1]
                os.replace(f, nuovo)
                sequenza.append(nuovo)
    return {"png": fuori, "conti": conti, "perche": None,
            "sequenza": sequenza, "registro": (out + err)[-1500:]}


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE CHECK THAT CANNOT BE SKIPPED: does the witness DISTURB the session?
# ═══════════════════════════════════════════════════════════════════════════
def guarda_il_registro(righe_prima, macchina=MACCHINA,
                       parola_sudo=PAROLA_SUDO,
                       registro="/media/REMOTIX/tmp/10nic/registro.log"):
    """⭐ The server lines written FROM `righe_prima` ONWARDS, filtered on what
       someone else's detach would say.

    ⛔ It serves the predicate *"the witness does not break the session it is
       observing"*: the server writes it by itself — *"the LAST session of X is
       leaving"*, *"nobody is watching it any more"*.  ⇒ If those lines appear
       while another client is still attached, the witness did damage.
    """
    rc, out, _ = _ssh("printf '%%s\\n' %s | sudo -S -p '' tail -n +%d %s"
                      % (parola_sudo, righe_prima + 1, registro),
                      macchina=macchina)
    if rc != 0:
        return None
    return out


def quante_righe(macchina=MACCHINA, parola_sudo=PAROLA_SUDO,
                 registro="/media/REMOTIX/tmp/10nic/registro.log"):
    # ⛔ NOT `wc -l < file`: the redirection STEALS standard input from `sudo -S`,
    #    which then asks for the password on a terminal that is not there and — after three
    #    attempts — ⚠ **triggers sudo's failure count**.
    #    `[M]` 25 Aug 2026, learnt by getting it wrong.
    rc, out, _ = _ssh("printf '%%s\\n' %s | sudo -S -p '' wc -l %s"
                      % (parola_sudo, registro), macchina=macchina)
    try:
        return int(out.strip().split()[0])
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE CERTIFICATION — healthy → faulty → healed, and the faults are RUN
# ═══════════════════════════════════════════════════════════════════════════
def _dipingi(dove, larghezza, altezza, fondo, giro=None, disegno=7,
             istante_us=123456):
    """Builds a fake frame, with the certified reader.

    ⚠ It is the only place where this bench PAINTS: the mark is painted by
      `03-marca.py`, that is the same file that then reads it — which is how
      a reader is certified without having to turn the machine on.
    """
    np = _numpy_o_niente()
    m = _marca_modulo()
    if np is None or m is None:
        return False
    from PIL import Image
    if fondo == "nero":
        img = np.zeros((altezza, larghezza, 3), np.uint8)
    elif fondo == "grigio-pieno":
        img = np.full((altezza, larghezza, 3), 128, np.uint8)
    elif fondo == "rumore":
        img = np.random.RandomState(7).randint(
            0, 256, (altezza, larghezza, 3), dtype=np.uint8)
    else:                                   # "desktop": a gradient
        yy = np.linspace(0, 1, altezza)[:, None]
        xx = np.linspace(0, 1, larghezza)[None, :]
        g = ((yy + xx) / 2 * 200 + 30).astype(np.uint8)
        img = np.repeat(g[:, :, None], 3, axis=2)
    if giro is not None:
        img = img.copy()
        m.dipingi_marca(img, disegno, istante_us, m.fnv1a32(giro))
    Image.fromarray(img).save(dove)
    return True


def certifica():
    """⛔ A bench is not finished until it has been seen giving ROSSO.

    Every predicate of this witness has its fault here, and the fault **runs**:
    healthy → faulty → healed, counted and printed.
    """
    np = _numpy_o_niente()
    if np is None or _marca_modulo() is None:
        print("⛔ I COULD NOT CERTIFY: without `numpy`/`Pillow` and without "
              "`03-marca.py` next to me, the pixel reading cannot be done.\n"
              "   ⚠ And this is NOT a green: it is the third outcome.")
        return 3

    tmp = tempfile.mkdtemp(prefix="10-f1-certifica-")
    buoni = rossi = risanati = 0
    guasti = []

    def prova(nome, che, atteso, ottenuto):
        ok = (atteso == ottenuto)
        print("   %s %-42s expected %-28s got %s"
              % ("✅" if ok else "⛔", nome + " · " + che,
                 repr(atteso), repr(ottenuto)))
        return ok

    print("═══ 10-f1-testimone --certifica ═══")
    print("  ⭐ HEALTHY → ⛔ FAULTY → ⭐ HEALED, on each predicate\n")

    # ── P1 · "zero frames" is I DID NOT LOOK, not "black" ──────────────────
    print("  P1 · the client log: how many frames ARRIVED")
    sano = ("   ⭐ SESSIONE: stato=1 tela=1920x1080\n"
            "   [vid]  12 frames (2 keys), 1920x1080, written to /x.264\n")
    g1 = "   ⭐ SESSIONE: stato=1\n   [vid]  ⛔ no frame taken from the wire\n"
    g2 = "   ⛔ the client died before opening the session\n"
    a = _leggi_esito_cliente(sano)
    ok0 = prova("P1", "healthy: 12 frames", 12, (a or {}).get("fotogrammi"))
    ok1 = prova("P1", "fault G1 «no frame» ⇒ None",
                None, _leggi_esito_cliente(g1))
    ok2 = prova("P1", "fault G2 «client dead» ⇒ None",
                None, _leggi_esito_cliente(g2))
    ok3 = prova("P1", "healed: 12 frames", 12,
                (_leggi_esito_cliente(sano) or {}).get("fotogrammi"))
    buoni += ok0; rossi += (ok1 + ok2); risanati += ok3
    if not (ok0 and ok1 and ok2 and ok3): guasti.append("P1")

    # ── P2 · the PNG that is not there, or cannot be read, is I DID NOT LOOK ─
    print("\n  P2 · the snapshot: «I did not read it» is not «it is black»")
    vero = os.path.join(tmp, "vero.png")
    _dipingi(vero, 640, 480, "desktop")
    ok0 = prova("P2", "healthy: a real PNG is judged", "disegnato",
                (giudica(vero) or {}).get("verdetto"))
    ok1 = prova("P2", "fault G3 file that does not exist ⇒ None",
                None, giudica(os.path.join(tmp, "non-c-e.png")))
    vuoto = os.path.join(tmp, "vuoto.png")
    open(vuoto, "wb").close()
    ok2 = prova("P2", "fault G4 0-byte file ⇒ None", None, giudica(vuoto))
    rotto = os.path.join(tmp, "rotto.png")
    with open(rotto, "wb") as f:
        f.write(open(vero, "rb").read()[:400])   # ⛔ PNG truncated halfway
    ok3 = prova("P2", "fault G5 truncated PNG ⇒ None", None, giudica(rotto))
    ok4 = prova("P2", "healed", "disegnato", (giudica(vero) or {}).get("verdetto"))
    buoni += ok0; rossi += (ok1 + ok2 + ok3); risanati += ok4
    if not (ok0 and ok1 and ok2 and ok3 and ok4): guasti.append("P2")

    # ── P3 · the verdict on the pixels: black, flat colour, drawn ───────────
    print("\n  P3 · the verdict: ⛔ «a PNG that exists» is not «a PNG that shows»")
    nero = os.path.join(tmp, "nero.png"); _dipingi(nero, 640, 480, "nero")
    grigio = os.path.join(tmp, "grigio.png"); _dipingi(grigio, 640, 480, "grigio-pieno")
    ok0 = prova("P3", "healthy: the gradient is «disegnato»", "disegnato",
                (giudica(vero) or {}).get("verdetto"))
    ok1 = prova("P3", "fault G6 black screen ⇒ «nero»", "nero",
                (giudica(nero) or {}).get("verdetto"))
    ok2 = prova("P3", "fault G7 flat colour ⇒ «tinta-unita»", "tinta-unita",
                (giudica(grigio) or {}).get("verdetto"))
    # ⭐ G8 is the case that separates the two opposite mistakes: a BLACK screen with
    #    the mark on it is NOT black — and a witness that said "black" here
    #    would throw away the only proof that it really looked.
    nero_marca = os.path.join(tmp, "nero-marca.png")
    _dipingi(nero_marca, 640, 480, "nero", giro="f1-t")
    ok3 = prova("P3", "fault G8 black + mark ⇒ «disegnato»", "disegnato",
                (giudica(nero_marca) or {}).get("verdetto"))
    # ⭐ G12 — THE NEGATIVE CONTROL OF THE REAL THING, redone here in miniature: a
    #    black screen with ONLY a light bar at the top on it (which is what
    #    GNOME never turns off).  ⛔ It is not "black" — no GNOME desktop is —
    #    but it is not "drawn" either: there is nothing on it.
    quasi = os.path.join(tmp, "quasi-nero.png")
    # ⚠ And the fake bar is CALIBRATED ON THE REAL ONE, not drawn by eye: `[M]`
    #   in the GNOME bar (40 rows) **3.3 %** of the pixels are lit, and over the
    #   whole screen they make a mean of **0.279**.  Here: 16x160 white px =
    #   2 560 px = mean 0.315.  ⛔ A fake bar bigger than the real one would make
    #   the fault pass for the wrong reason — and it happened in the first
    #   draft, with a 500x40 block that gave a mean of 2.46.
    _img = np.zeros((1080, 1920, 3), np.uint8)
    _img[8:24, 860:1020] = 255          # ⇐ the bar's clock
    from PIL import Image as _Immagine
    _Immagine.fromarray(_img).save(quasi)
    ok5 = prova("P3", "fault G12 black + bar at the top ⇒ «quasi-nero»",
                "quasi-nero", (giudica(quasi) or {}).get("verdetto"))
    ok4 = prova("P3", "healed", "nero", (giudica(nero) or {}).get("verdetto"))
    buoni += ok0; rossi += (ok1 + ok2 + ok3 + ok5); risanati += ok4
    if not ok5: guasti.append("P3")
    if not (ok0 and ok1 and ok2 and ok3 and ok4): guasti.append("P3")

    # ── P4 · the mark: it is there, and above all it is MINE ────────────────
    print("\n  P4 · the calibration: the mark is there, and it is from MY round")
    con = os.path.join(tmp, "con-marca.png")
    _dipingi(con, 1280, 720, "desktop", giro="f1-taratura", disegno=41)
    r = leggi_la_marca(con, ["f1-taratura"])
    ok0 = prova("P4", "healthy: mark found, and it is mine",
                (True, True, 41),
                ((r or {}).get("c_e"), (r or {}).get("mio"), (r or {}).get("disegno")))
    senza = os.path.join(tmp, "senza-marca.png")
    _dipingi(senza, 1280, 720, "desktop")
    r1 = leggi_la_marca(senza, ["f1-taratura"])
    ok1 = prova("P4", "fault G9 no mark ⇒ red (not None)",
                (True, False), (r1 is not None, (r1 or {}).get("c_e")))
    # ⛔ G10: the mark is there but from ANOTHER round — that is, I am looking at
    #    someone else's desktop.  It is the fault no frame count
    #    could ever give.
    altrui = os.path.join(tmp, "altrui.png")
    _dipingi(altrui, 1280, 720, "desktop", giro="di-un-altro")
    r2 = leggi_la_marca(altrui, ["f1-taratura"])
    ok2 = prova("P4", "fault G10 mark from ANOTHER round ⇒ «not mine»",
                (True, False), ((r2 or {}).get("c_e"), (r2 or {}).get("mio")))
    # ⛔ G11: the frame is too small for the mark to fit.  Here
    #    "the mark is not there" would be FALSE: I could not look.
    minuscolo = os.path.join(tmp, "minuscolo.png")
    _dipingi(minuscolo, 200, 100, "desktop")
    ok3 = prova("P4", "fault G11 frame too small ⇒ None",
                None, leggi_la_marca(minuscolo, ["f1-taratura"]))
    r3 = leggi_la_marca(con, ["f1-taratura"])
    ok4 = prova("P4", "healed", (True, True),
                ((r3 or {}).get("c_e"), (r3 or {}).get("mio")))
    buoni += ok0; rossi += (ok1 + ok2 + ok3); risanati += ok4
    if not (ok0 and ok1 and ok2 and ok3 and ok4): guasti.append("P4")

    print("\n───────────────────────────────────────────────────────────────")
    print("  healthy %d · faulty %d · healed %d" % (buoni, rossi, risanati))
    if guasti:
        print("  ⛔ NOT CERTIFIED: %s" % ", ".join(guasti))
        return 1
    print("  ✅ certified: 4 predicates, 12 faults grafted, all of them bit")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser(
        description="the witness that shows the remote desktop")
    p.add_argument("che", nargs="?", default="scatta", choices=("scatta",))
    p.add_argument("--utente", default="provanic1")
    p.add_argument("--fuori", default="", help="where to write the PNG, HERE")
    p.add_argument("--resta", type=float, default=6.0,
                   help="how many seconds to stay attached watching")
    p.add_argument("--porta", type=int, default=PORTA)
    p.add_argument("--indirizzo", default=INDIRIZZO)
    p.add_argument("--albero", default=ALBERO)
    p.add_argument("--lav", default=LAV)
    p.add_argument("--parola-file", default=PAROLA_FILE)
    p.add_argument("--macchina", default=MACCHINA)
    p.add_argument("--parola-sudo", default=PAROLA_SUDO)
    p.add_argument("--marca", default="",
                   help="⭐ the round name I expect INSIDE the pixels: "
                        "without it, the witness only says what it sees; with it, "
                        "it also says whether it is looking at the RIGHT desktop")
    p.add_argument("--sveglia", default="",
                   help="⚠ WxH — changes the canvas to force the stage to "
                        "redo a frame on a motionless desktop.  "
                        "⛔ It changes what the desktop sees: off by "
                        "default, and whoever turns it on declares it")
    p.add_argument("--tutti", action="store_true",
                   help="⭐ also pulls down ALL the frames of the grab, "
                        "next to the snapshot and with the same name plus the "
                        "number.  ⛔ It is needed when the desktop PASSES THROUGH a "
                        "state instead of staying in it: `[M]` Firefox's «Profile "
                        "Missing» dialog appeared halfway through the grab and "
                        "was no longer there on the last frame")
    p.add_argument("--json", default="", help="where to write the outcome as JSON")
    p.add_argument("--loquace", action="store_true")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        return certifica()

    if not a.fuori:
        print("⛔ without `--fuori` I do not know where to put the image")
        return 2

    t0 = time.time()
    e = scatta(a.utente, a.fuori, resta=a.resta, porta=a.porta,
               indirizzo=a.indirizzo, albero=a.albero, lav=a.lav,
               parola_file=a.parola_file, macchina=a.macchina,
               parola_sudo=a.parola_sudo, sveglia=a.sveglia or None,
               loquace=a.loquace, tutti=a.tutti)
    fuori = {"utente": a.utente, "porta": a.porta, "resta": a.resta,
             "durata_s": round(time.time() - t0, 1),
             "sveglia": a.sveglia or None}

    if e["png"] is None:
        # ⛔ THE THIRD OUTCOME.  It is not a red and it is not a green.
        print("⛔ I DID NOT LOOK — and this is not «the screen was black».")
        print("   %s" % e["perche"])
        if a.loquace:
            print(e.get("registro", ""))
        fuori.update({"guardato": False, "perche": e["perche"],
                      "conti": e["conti"], "giudizio": None, "marca": None})
        if a.json:
            open(a.json, "w").write(json.dumps(fuori, ensure_ascii=False, indent=1))
        return 3

    g = giudica(e["png"])
    if g is None:
        print("⛔ I DID NOT JUDGE: the snapshot is there (%s) but I could not "
              "read its pixels (`numpy`/`Pillow` missing here?)." % e["png"])
        fuori.update({"guardato": True, "png": e["png"], "conti": e["conti"],
                      "giudizio": None, "marca": None})
        if a.json:
            open(a.json, "w").write(json.dumps(fuori, ensure_ascii=False, indent=1))
        return 3

    c = e["conti"]
    print("⭐ I LOOKED AT «%s» on port %d" % (a.utente, a.porta))
    print("   from the wire  %d frames (%d keys), %s"
          % (c["fotogrammi"], c["chiavi"], c["misura"]))
    print("   the snapshot   %s  (%dx%d)" % (e["png"], g["larghezza"], g["altezza"]))
    print("   the picture    ⇒ %s   mean %.1f · dev %.1f · colours %d · "
          "lit %.4f · different from background %.4f"
          % (g["verdetto"].upper(), g["media"], g["dev"], g["colori"],
             g["accesi"], g["diversi"]))
    print("   the thresholds black luma %.0f · black below %.4f lit · nearly "
          "black below mean %.1f · flat colour below %.4f different"
          % (LUMA_NERO, FRAZIONE_NERO, MEDIA_QUASI_NERO, FRAZIONE_PIATTO))
    fuori.update({"guardato": True, "png": e["png"], "conti": c, "giudizio": g})

    esito = 0
    if a.marca:
        giri = [x for x in a.marca.split(",") if x]
        m = leggi_la_marca(e["png"], giri)
        fuori["marca"] = m
        if m is None:
            print("   ⛔ THE MARK: I could not read it (frame too "
                  "small, or the reader is missing).  ⚠ It is not «it is not there»")
            esito = 3
        elif not m["c_e"]:
            print("   ⛔ THE MARK IS NOT THERE — %s" % m["perche"])
            esito = 1
        elif not m["mio"]:
            print("   ⛔ THE MARK IS THERE BUT IT IS NOT MINE: round 0x%08x, and mine "
                  "were %s.  ⚠ I am looking at someone else's desktop"
                  % (m["giro_numero"], giri))
            esito = 1
        else:
            print("   ⭐ THE MARK IS THERE AND IT IS MINE: round «%s», drawing %d, "
                  "contrast %.3f  ⇒ **the witness is looking at THAT desktop**"
                  % (m["giro"], m["disegno"], m["contrasto"] or 0.0))
    else:
        fuori["marca"] = None

    if a.json:
        open(a.json, "w").write(json.dumps(fuori, ensure_ascii=False, indent=1))
    return esito


if __name__ == "__main__":
    sys.exit(main())
