#!/usr/bin/env python3
"""04-b28-gesti.py — ⭐ THE BENCH FOR TOUCH MODE (link A8 of phase 4).

    python3 banchi/04-b28-gesti.py --certifica     ⭐ without a browser: can the
                                                      judge see the defect?
    python3 banchi/04-b28-gesti.py --gira --porta 7671 --diagnosi 7672
    python3 banchi/04-b28-gesti.py --verdetto banchi/04-b28-registro.jsonl

===========================================================================
⛔ WHAT IT MEASURES, AND WHICH SIDE IT STANDS ON

Two DISTINCT questions, and they are judged separately:

  ⒜ **the seven gestures** (`SPECIFICHE.md` §7.2): a synthetic sequence of
     `Touch` events for each one ⇒ the expected message of `RCP.md` §7.3;
  ⒝ **the automatic switch** (`DECISIONI.md` §5-bis.0-bis): the context is
     declared and it is checked **which layout is IN FORCE** — by reading
     `body[data-disposizione]`, which the product writes, and by proving that
     the other half is really OFF.  ⛔ Not «there is a function that changes
     it»: a function that changes nothing can exist just fine.

⛔ The bytes are decoded with a reader written HERE, from the table of
   `RCP.md` §7.3, without looking at the page's JavaScript.  If one day the
   two disagree, **that disagreement is the gift**.

===========================================================================
⛔⛔ THE BENCH IS CERTIFIED ON THE CONFUSIONS, NOT ON THE CLEAN GESTURES

This is the most important line in this file.  A bench that tests the seven
clean gestures says **green** on a recogniser that gets every edge case wrong:
the clean gestures are easy, and no real defect lives there.

  G1..G7   the seven clean gestures  — they serve as POSITIVE control
  C1..C8   ⭐ the CONFUSIONS         — this is where the verdict is decided
  D1..D4   the automatic switch
  S1       ⭐ the SEAM between the two anchors, which in phase 3 no bench
           looked at (`fasi/rapporti/F5-desktop-vero.md`)

⛔ And `--certifica` injects FIVE faults, one per family of confusion, and
   demands **green → red → green** on each.  A judge that cannot say red
   cannot say green (`CODER.md` §3.3, §3.10, §4.6).

===========================================================================
⚠ THE SCENE, DECLARED — and the stage is verified from the other end

The browser opens on the user's REAL desktop: that is what the mandate
asks, and ⛔ **it is not moved to a fake screen to make the numbers add up**.
What the scene really was is written by the collector in every line of
`04-b28-esiti.jsonl` — `XDG_SESSION_TYPE`, the `userAgent`, and the layout
that the PRODUCT wrote into the document.

⛔ And touch is declared by the bench, not by the environment: `Emulation.setTouchEmulation
   Enabled` turns on the contact points, and ⚠ **what comes out of it is
   the emulation, not a finger** (`LEZIONI.md` §1.11).  ⇒ NO number comes out
   of here on how a real hand behaves: what comes out are the boundaries of the
   RECOGNISER, which are deterministic and measure well even this way.
   ⭐ The judgement on the gestures stays with Nic, with a finger, and it is
   written in the report.
"""

import argparse
import http.server
import importlib.util
import json
import os
import socketserver
import struct
import sys
import threading
import time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)

# `RCP.md` §7.3 — the types of the input channel and the evdev codes.
PUNTATORE, PULSANTE, ROTELLA = 0x0101, 0x0102, 0x0103
SINISTRO, DESTRO, CENTRALE = 0x110, 0x111, 0x112
NOMI = {PUNTATORE: "PUNTATORE", PULSANTE: "PULSANTE", ROTELLA: "ROTELLA"}
NOMI_BTN = {SINISTRO: "sinistro", DESTRO: "destro", CENTRALE: "centrale"}

TELA = (1920, 1080)


class Violazione(Exception):
    pass


# ---------------------------------------------------------------------------
# THE BYTE READER — written from the table of `RCP.md` §7.3.
#
# ⛔ Framing of §6.1: u16 type, u32 length, body.  Body of §7.3:
#    u32 id (increasing, never 0) + u64 instant (microseconds) + the type's fields.
# ---------------------------------------------------------------------------
def decodifica(byte):
    fuori, o = [], 0
    while o < len(byte):
        if len(byte) - o < 6:
            raise Violazione("truncated framing: %d bytes left" % (len(byte) - o))
        tipo, lung = struct.unpack_from(">HI", byte, o)
        o += 6
        if len(byte) - o < lung:
            raise Violazione("truncated body: %d declared, %d present"
                             % (lung, len(byte) - o))
        corpo = byte[o:o + lung]
        o += lung
        if tipo >> 8 != 0x01:
            raise Violazione("type 0x%04X: not on the input channel (§2.5)" % tipo)
        if lung < 12:
            raise Violazione("body of %d bytes: id and instant do not fit" % lung)
        mid, istante = struct.unpack_from(">IQ", corpo, 0)
        if mid == 0:
            raise Violazione("id 0: §7.3 reserves it for «no input»")
        m = {"tipo": tipo, "nome": NOMI.get(tipo, "?"), "id": mid, "istante": istante}
        if tipo == PUNTATORE:
            if lung != 20:
                raise Violazione("PUNTATORE of %d bytes, it wants 20" % lung)
            m["x"], m["y"] = struct.unpack_from(">II", corpo, 12)
        elif tipo == PULSANTE:
            if lung != 15:
                raise Violazione("PULSANTE of %d bytes, it wants 15" % lung)
            m["codice"], m["premuto"] = struct.unpack_from(">HB", corpo, 12)
        elif tipo == ROTELLA:
            if lung != 20:
                raise Violazione("ROTELLA of %d bytes, it wants 20" % lung)
            m["asse_x"], m["asse_y"] = struct.unpack_from(">ii", corpo, 12)
        else:
            raise Violazione("unknown type 0x%04X on the input channel" % tipo)
        fuori.append(m)
    return fuori


# ---------------------------------------------------------------------------
# THE JUDGE.  Each case is a function that receives the messages of its phase and
# returns (green: bool, why: str).
#
# ⛔ Expectations are written as PROPERTIES, not as strings to compare:
#    «no PULSANTE» is a property that survives a different id or one extra
#    PUNTATORE; «these exact bytes» would be green only on the run that
#    produced them (`LEZIONI.md` §2.3 — v1's wheel bench, red with the
#    correct code, because of a badly searched string).
# ---------------------------------------------------------------------------
def _pul(ms):
    return [m for m in ms if m["tipo"] == PULSANTE]


def _clic(ms, codice):
    """The pressed/released pair of a button, counted as a CLICK."""
    p, n = None, 0
    for m in _pul(ms):
        if m["codice"] != codice:
            continue
        if m["premuto"] == 1:
            p = m
        elif p is not None:
            n += 1
            p = None
    return n


def _punt(ms):
    return [m for m in ms if m["tipo"] == PUNTATORE]


def _rot(ms):
    return [m for m in ms if m["tipo"] == ROTELLA]


def _solo(ms, codice):
    """A single click, of that button, and nothing else on the wire."""
    if _rot(ms):
        return False, "there is a ROTELLA: it was not a tap"
    if _clic(ms, codice) != 1:
        return False, ("%s clicks expected 1, counted %d (buttons: %s)"
                       % (NOMI_BTN.get(codice, codice), _clic(ms, codice),
                          [(NOMI_BTN.get(m["codice"], m["codice"]), m["premuto"])
                           for m in _pul(ms)]))
    altri = [m for m in _pul(ms) if m["codice"] != codice]
    if altri:
        return False, ("there are other buttons on the wire too: %s"
                       % [(NOMI_BTN.get(m["codice"], m["codice"]), m["premuto"])
                          for m in altri])
    return True, "one %s click and nothing else" % NOMI_BTN.get(codice, codice)


def c_G1(ms):
    """1 finger drags = moves the pointer, and presses NOTHING."""
    if _pul(ms):
        return False, "a drag produced a button"
    p = _punt(ms)
    if len(p) < 3:
        return False, "only %d PUNTATORE for a 200 px drag" % len(p)
    if p[-1]["x"] <= p[0]["x"]:
        return False, ("the finger went right and the pointer did not: from %d to %d"
                       % (p[0]["x"], p[-1]["x"]))
    return True, "%d PUNTATORE, from x=%d to x=%d, no button" % (
        len(p), p[0]["x"], p[-1]["x"])


def c_G2(ms):
    return _solo(ms, SINISTRO)


def c_G3(ms):
    return _solo(ms, DESTRO)


def c_G4(ms):
    """2 fingers drag = wheel.  ⛔ The SIGN and the grain of 60 (§7.3)."""
    if _pul(ms):
        return False, "a two-finger scroll produced a button"
    r = _rot(ms)
    if not r:
        return False, "no ROTELLA"
    for m in r:
        if m["asse_y"] % 60 or m["asse_x"] % 60:
            return False, ("ROTELLA not a multiple of 60 (§7.3, the half notch): "
                           "%d, %d" % (m["asse_x"], m["asse_y"]))
    tot = sum(m["asse_y"] for m in r)
    if tot <= 0:
        return False, ("the fingers went down and the vertical axis is not positive "
                       "(%d): `RCP.md` §7.3 wants +120 for the wheel UP, and "
                       "two fingers going down push the sheet down" % tot)
    return True, "%d ROTELLA, vertical sum +%d, all multiples of 60" % (len(r), tot)


def c_G5(ms):
    """⭐ TAP-AND-A-HALF: tap, then press and drag.  On the wire:
       click · pressed · moving PUNTATORE · released.
       ⛔ And the PUNTATORE must sit BETWEEN pressed and released, or it is not
          a drag: it is a double click."""
    p = _pul(ms)
    sin = [m for m in p if m["codice"] == SINISTRO]
    if len(sin) != 4:
        return False, "expected 4 left-button events (down,up,down,up), counted %d" % len(sin)
    if [m["premuto"] for m in sin] != [1, 0, 1, 0]:
        return False, "the order is not down,up,down,up: %s" % [m["premuto"] for m in sin]
    # The PUNTATORE between the THIRD and the FOURTH event: that is where the drag lives.
    i3 = ms.index(sin[2])
    i4 = ms.index(sin[3])
    dentro = [m for m in ms[i3 + 1:i4] if m["tipo"] == PUNTATORE]
    if len(dentro) < 2:
        return False, ("only %d PUNTATORE between pressed and released: the "
                       "button stayed down without dragging anything" % len(dentro))
    if dentro[-1]["y"] == dentro[0]["y"] and dentro[-1]["x"] == dentro[0]["x"]:
        return False, "the pointer did not move while the button was down"
    return True, ("click, then pressed + %d PUNTATORE + released — "
                  "the drag is there" % len(dentro))


def c_G6(ms):
    return _solo(ms, CENTRALE)


def c_G7(ms, zoom=None):
    """Pinch = zooms the client's VIEW.  ⛔ ZERO bytes on the wire."""
    if ms:
        return False, ("the pinch sent %d messages: §7.2 says it "
                       "zooms the VIEW, not the application" % len(ms))
    if zoom is None:
        return True, "no message on the wire (zoom not read)"
    if zoom <= 1.05:
        return False, "no message on the wire, but the view did not zoom in (zoom %.2f)" % zoom
    return True, "zero bytes on the wire, and the view is at %.2fx" % zoom


# ── ⭐ THE CONFUSIONS ───────────────────────────────────────────────────────
def c_C1(ms):
    """The tap that lasts a bit too long (400 ms, still) ⇒ NOT a click.
       Declared threshold: `T_TAP` = 180 ms."""
    if _pul(ms):
        return False, ("a still 400 ms contact produced a click: the "
                       "180 ms threshold is not checked")
    return True, "400 ms still, no click (T_TAP = 180 ms)"


def c_C2(ms):
    """The tap that slides (120 ms but 30 px) ⇒ NOT a click, it is a movement.
       Declared threshold: `D_TAP` = 9 CSS px."""
    if _pul(ms):
        return False, "a contact that slid 30 px produced a click (D_TAP = 9 px)"
    if not _punt(ms):
        return False, "slid 30 px and the pointer did not move at all"
    return True, "30 px of sliding: %d PUNTATORE, no click" % len(_punt(ms))


def c_C3(ms):
    """⭐⭐ THE TWO FINGERS THAT LAND 30 ms APART.
       It is the case the mandate names.  A recogniser that counts the fingers
       at the start of the gesture sees ONE finger here and sends a LEFT click."""
    if _clic(ms, SINISTRO):
        return False, ("LEFT click: the two fingers were 30 ms apart and the "
                       "count did not look at the maximum of simultaneous fingers")
    return _solo(ms, DESTRO)


def c_C4(ms):
    """⛔ THE DECLARED DEFECT, and the bench demands it exactly as it is.

    Two fingers that NEVER overlap (A 0→100 ms, B 130→230 ms, 60 px
    apart) come out as TWO LEFT CLICKS, not as one right click.
    ⛔ It is not a defect to fix here: the same sequence is also «I click
    here, then I click right there», and the only cure would be to delay EVERY
    left click by 300 ms — the price that `CODER.md` §1-bis forbids.
    ⇒ The bench pins the DECLARED behaviour: the day it changes,
      this line turns red and the report is reread."""
    if _clic(ms, DESTRO):
        return False, ("a right click came out of two contacts that do not "
                       "overlap: the behaviour has changed from "
                       "what the A8 report declares — reread the report")
    n = _clic(ms, SINISTRO)
    if n != 2:
        return False, "expected 2 left clicks (the declared defect), counted %d" % n
    return True, ("2 left clicks: it is the DECLARED defect — below an "
                  "overlap of one sample a right click comes out as a "
                  "double left click")


def c_C5a(ms):
    """⭐ Still double tap, same spot ⇒ DOUBLE CLICK (4 events, 0 PUNTATORE)."""
    sin = [m for m in _pul(ms) if m["codice"] == SINISTRO]
    if [m["premuto"] for m in sin] != [1, 0, 1, 0]:
        return False, "they are not four events down,up,down,up: %s" % [
            (NOMI_BTN.get(m["codice"], m["codice"]), m["premuto"]) for m in _pul(ms)]
    if _punt(ms):
        return False, ("there are %d PUNTATORE inside a still double click: the "
                       "remote desktop would read it as a drag"
                       % len(_punt(ms)))
    return True, "four left-button events, zero PUNTATORE — it is a double click"


def c_C5b(ms):
    """⭐ And the SAME opening that then drags ⇒ DRAG.  They are the same
       gesture up to the second contact: it is the refutation, and it is tested here."""
    return c_G5(ms)


def c_C6(ms):
    """The two-finger drag that starts STILL (350 ms of waiting).
       ⛔ A recogniser that decided «tap» when T_TAP is exceeded and
          stopped there would send no wheel."""
    if _pul(ms):
        return False, "350 ms still and then scrolling: a button came out"
    if not _rot(ms):
        return False, "350 ms still and then scrolling: no ROTELLA"
    return True, "%d ROTELLA after 350 ms of still fingers, no click" % len(_rot(ms))


def c_C7a(ms, zoom=None):
    """⭐ WHEEL VERSUS PINCH — the fingers move APART: zoom only."""
    if _rot(ms):
        return False, ("two fingers moving apart produced %d ROTELLA: "
                       "pinch and wheel are confused" % len(_rot(ms)))
    if zoom is not None and zoom <= 1.05:
        return False, "no wheel, but the zoom did not change either (%.2f)" % zoom
    return True, "zero ROTELLA, zoom %s" % ("%.2f" % zoom if zoom else "not read")


def c_C7b(ms, zoom=None):
    """⭐ And the PARALLEL fingers: wheel only, and the view does NOT zoom in."""
    if not _rot(ms):
        return False, "two parallel fingers and no ROTELLA"
    if zoom is not None and zoom > 1.05:
        return False, ("two parallel fingers zoomed the view to %.2fx: "
                       "it was read as a pinch" % zoom)
    return True, "%d ROTELLA, view still at %s" % (
        len(_rot(ms)), "%.2f" % zoom if zoom else "?")


def c_C8(ms):
    """The leftover: two fingers scroll, one lifts, the other still moves.
       ⛔ The pointer must NOT jump — it is the most visible defect,
          because at the end of a scroll one finger always lifts a moment earlier."""
    if _punt(ms):
        return False, ("the finger left after a scroll moved the "
                       "pointer (%d PUNTATORE): at the end of the scroll the "
                       "pointer jumps" % len(_punt(ms)))
    return True, "the leftover finger did not move the pointer"


CASI = {
    "G1-un-dito-trascina": c_G1,
    "G2-un-dito-tap": c_G2,
    "G3-due-dita-tap": c_G3,
    "G4-due-dita-trascina": c_G4,
    "G5-tap-e-mezzo": c_G5,
    "G6-tre-dita-tap": c_G6,
    "G7-pizzico": c_G7,
    "C1-tap-troppo-lungo": c_C1,
    "C2-tap-che-scivola": c_C2,
    "C3-due-dita-a-30ms": c_C3,
    "C4-due-dita-senza-sovrapposizione": c_C4,
    "C5a-doppio-clic": c_C5a,
    "C5b-tap-e-mezzo-che-trascina": c_C5b,
    "C6-trascinamento-che-comincia-fermo": c_C6,
    "C7a-pizzico-non-rotella": c_C7a,
    "C7b-rotella-non-pizzico": c_C7b,
    "C8-il-dito-residuo": c_C8,
}

# Which cases also want the zoom read from the page.
VOGLIONO_ZOOM = {"G7-pizzico", "C7a-pizzico-non-rotella", "C7b-rotella-non-pizzico"}


def giudica(righe):
    """righe: [{"fase":…, "hex":…} | {"fase":…, "marca":True} | {"fase":…, "zoom":…}]"""
    per_fase, zoom = {}, {}
    for r in righe:
        f = r.get("fase", "?")
        if "hex" in r:
            per_fase.setdefault(f, b"")
            per_fase[f] += bytes.fromhex(r["hex"])
        elif "zoom" in r:
            zoom[f] = r["zoom"]
        else:
            per_fase.setdefault(f, b"")
    esiti = []
    for nome, fn in CASI.items():
        dati = per_fase.get(nome)
        if dati is None:
            esiti.append({"caso": nome, "verde": False,
                          "perche": "⛔ the phase was not recorded at all"})
            continue
        try:
            ms = decodifica(dati)
        except Violazione as e:
            esiti.append({"caso": nome, "verde": False,
                          "perche": "⛔ violation of RCP.md §7.3: %s" % e})
            continue
        if nome in VOGLIONO_ZOOM:
            verde, perche = fn(ms, zoom.get(nome))
        else:
            verde, perche = fn(ms)
        esiti.append({"caso": nome, "verde": bool(verde), "perche": perche,
                      "messaggi": len(ms)})
    # ⛔ The id grows over the WHOLE channel, not per type (§7.3): it is checked
    #    once, over all the messages of all the phases, in order of arrival.
    # ⚠ Only the gesture phases: after the switch measurement the page is
    #   RELOADED, and on a new page the counter restarts from 1 — which is
    #   correct, and it is a different session.  Counting them together would
    #   measure the bench, not the product.
    tutti = []
    for r in righe:
        if "hex" in r and r.get("fase") in CASI:
            try:
                tutti += decodifica(bytes.fromhex(r["hex"]))
            except Violazione:
                pass
    ids = [m["id"] for m in tutti]
    cresce = all(b > a for a, b in zip(ids, ids[1:]))
    esiti.append({"caso": "R1-identificatore-crescente", "verde": bool(ids) and cresce,
                  "perche": ("%d messages, id from %d to %d, increasing over the whole channel"
                             % (len(ids), ids[0], ids[-1])) if ids and cresce
                            else "the identifiers do not increase over the whole channel: %s"
                                 % ids[:20]})
    return esiti


# ---------------------------------------------------------------------------
# ⭐ THE CERTIFICATION — green → red → green, on FIVE faults, one per
#    family of confusion.  ⛔ `CODER.md` §3.3: the bench is certified before
#    the measurement, or a red is ambiguous between «it does not work» and «the
#    bench was not working».
# ---------------------------------------------------------------------------
def _b(tipo, mid, ist, resto):
    corpo = struct.pack(">IQ", mid, ist) + resto
    return struct.pack(">HI", tipo, len(corpo)) + corpo


class Penna:
    def __init__(self):
        self.n = 0
        self.t = 1000
        self.righe = []

    def _id(self):
        self.n += 1
        self.t += 5
        return self.n, self.t * 1000

    def punt(self, fase, x, y):
        i, t = self._id()
        self.righe.append({"fase": fase, "hex": _b(PUNTATORE, i, t,
                                                   struct.pack(">II", x, y)).hex()})

    def puls(self, fase, cod, giu):
        i, t = self._id()
        self.righe.append({"fase": fase, "hex": _b(PULSANTE, i, t,
                                                   struct.pack(">HB", cod, giu)).hex()})

    def rot(self, fase, ax, ay):
        i, t = self._id()
        self.righe.append({"fase": fase, "hex": _b(ROTELLA, i, t,
                                                   struct.pack(">ii", ax, ay)).hex()})

    def zoom(self, fase, z):
        self.righe.append({"fase": fase, "zoom": z})

    def vuota(self, fase):
        self.righe.append({"fase": fase, "marca": True})


def registrazione(guasto=None):
    """A HEALTHY recording, with an optional injected fault."""
    p = Penna()

    def clic(fase, cod):
        p.puls(fase, cod, 1)
        p.puls(fase, cod, 0)

    f = "G1-un-dito-trascina"
    for x in range(1000, 1210, 50):
        p.punt(f, x, 540)

    clic("G2-un-dito-tap", SINISTRO)
    clic("G3-due-dita-tap", DESTRO)

    f = "G4-due-dita-trascina"
    for _ in range(3):
        p.rot(f, 0, 120 if guasto != "rotella-al-contrario" else -120)

    f = "G5-tap-e-mezzo"
    clic(f, SINISTRO)
    p.puls(f, SINISTRO, 1)
    if guasto != "tap-e-mezzo-non-trascina":
        for y in range(540, 620, 20):
            p.punt(f, 900, y)
    p.puls(f, SINISTRO, 0)

    clic("G6-tre-dita-tap", CENTRALE)

    f = "G7-pizzico"
    p.vuota(f)
    if guasto == "pizzico-manda-rotella":
        p.rot(f, 0, 120)
    p.zoom(f, 2.0)

    f = "C1-tap-troppo-lungo"
    p.vuota(f)
    if guasto == "tap-lungo-clicca":
        clic(f, SINISTRO)

    f = "C2-tap-che-scivola"
    for x in range(900, 960, 20):
        p.punt(f, x, 540)

    f = "C3-due-dita-a-30ms"
    if guasto == "trenta-ms-diventa-doppio-sinistro":
        clic(f, SINISTRO)
        clic(f, SINISTRO)
    else:
        clic(f, DESTRO)

    f = "C4-due-dita-senza-sovrapposizione"
    clic(f, SINISTRO)
    clic(f, SINISTRO)

    f = "C5a-doppio-clic"
    clic(f, SINISTRO)
    clic(f, SINISTRO)

    f = "C5b-tap-e-mezzo-che-trascina"
    clic(f, SINISTRO)
    p.puls(f, SINISTRO, 1)
    for y in range(540, 620, 20):
        p.punt(f, 900, y)
    p.puls(f, SINISTRO, 0)

    f = "C6-trascinamento-che-comincia-fermo"
    for _ in range(2):
        p.rot(f, 0, 120)

    f = "C7a-pizzico-non-rotella"
    p.vuota(f)
    p.zoom(f, 1.8)

    f = "C7b-rotella-non-pizzico"
    for _ in range(2):
        p.rot(f, 0, 120)
    p.zoom(f, 1.0)

    p.vuota("C8-il-dito-residuo")
    return p.righe


GUASTI = [
    ("tap-lungo-clicca", "C1-tap-troppo-lungo",
     "a still 400 ms contact that sends a click (the T_TAP threshold not checked)"),
    ("trenta-ms-diventa-doppio-sinistro", "C3-due-dita-a-30ms",
     "two fingers 30 ms apart that come out as two left clicks instead of one right"),
    ("rotella-al-contrario", "G4-due-dita-trascina",
     "the wheel sign inverted (`RCP.md` §7.3, form E11)"),
    ("tap-e-mezzo-non-trascina", "G5-tap-e-mezzo",
     "the tap-and-a-half that presses and releases without dragging — that is, a double click"),
    ("pizzico-manda-rotella", "G7-pizzico",
     "the pinch that sends a wheel instead of zooming the view"),
]


def certifica():
    print("⭐ CERTIFICATION OF THE JUDGE — green → red → green, on five")
    print("   faults, one per family of confusion.\n")
    sano = giudica(registrazione())
    rossi = [e for e in sano if not e["verde"]]
    if rossi:
        print("⛔ the HEALTHY recording is not green: the judge is broken.")
        for e in rossi:
            print("     %-40s %s" % (e["caso"], e["perche"]))
        return 1
    print("  ✅ HEALTHY recording: %d cases, all green" % len(sano))

    ok = True
    for guasto, caso, testo in GUASTI:
        esiti = giudica(registrazione(guasto))
        mio = [e for e in esiti if e["caso"] == caso][0]
        altri = [e["caso"] for e in esiti if not e["verde"] and e["caso"] != caso]
        if mio["verde"]:
            print("  ⛔ fault «%s»: the judge does NOT see it." % guasto)
            print("       %s" % testo)
            ok = False
        elif altri:
            print("  ⚠ fault «%s»: seen, but it also turned %s red"
                  % (guasto, altri))
            print("       (a judge that bleeds cannot say WHERE the defect is)")
            ok = False
        else:
            print("  ✅ %-36s red only on %s" % (guasto, caso))
            print("       ↳ %s" % testo)

    risanato = giudica(registrazione())
    if [e for e in risanato if not e["verde"]]:
        print("⛔ the HEALED recording does not turn green again.")
        return 1
    print("  ✅ HEALED recording: green again")
    print("\n%s" % ("⭐ the judge is certified." if ok
                    else "⛔ the judge is NOT certified: nothing is measured."))
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# THE SERVER AND THE SEAM — the same shape as `04-b27-classico.py`.
# ---------------------------------------------------------------------------
class Raccolta:
    def __init__(self):
        self.righe = []
        self.fase = "F-nessuna"
        self.blocco = threading.Lock()
        self.byte = 0

    def marca(self, fase):
        with self.blocco:
            self.fase = fase
            self.righe.append({"t": time.time(), "fase": fase, "marca": True})

    def aggiungi(self, dati):
        with self.blocco:
            self.byte += len(dati)
            self.righe.append({"t": time.time(), "fase": self.fase, "hex": dati.hex()})

    def zoom(self, fase, z):
        with self.blocco:
            self.righe.append({"t": time.time(), "fase": fase, "zoom": z})


def servitore(porta, raccolta, pagina_html):
    class H(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def _corpo(self, tipo, dati, stato=200):
            self.send_response(stato)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(dati)))
            self.end_headers()
            self.wfile.write(dati)

        def do_GET(self):
            p = self.path.split("?")[0].split("#")[0]
            if p == "/":
                self._corpo("text/html; charset=utf-8", pagina_html)
            else:
                self._corpo("text/plain", b"not here", 404)

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            dati = self.rfile.read(n)
            p = self.path.split("?")[0]
            if p == "/byte":
                raccolta.aggiungi(dati)
            elif p == "/fase":
                raccolta.marca(dati.decode("utf-8", "replace"))
            self._corpo("text/plain", b"ok")

    # ⛔ `allow_reuse_address` must be set on the CLASS: `TCPServer.__init__` binds
    #    the port at once, and `server_bind()` reads the attribute BEFORE it can be
    #    written on the instance.  ⚠ Written afterwards, it has no effect — and the
    #    symptom is «Address already in use» on the next run, with the port that
    #    `ss` declares free because it is only in TIME_WAIT.
    class _Servitore(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    s = _Servitore(("127.0.0.1", porta), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


# ---------------------------------------------------------------------------
# ⛔⭐ THE BROWSER DRIVER, WITH RECONNECTION.
#
# `[M]` 14 Aug 2026, Chrome 151.0.7922.137: `Input.dispatchTouchEvent`
# **does not return** under some conditions (after a mouse event, and after a
# recycled contact identifier).  ⇒ The first run of this bench died
# halfway and threw away sixteen good measurements for a defect of the driver.
#
# ⛔ And we do not pretend it did not happen: every reconnection ends up in `guasti`,
#    which goes into the outcomes log — so a red can be attributed to the
#    tool instead of to the product (`CODER.md` §3.10, §3.11).
# ---------------------------------------------------------------------------
class Guida:
    def __init__(self, modulo, url, timeout=20):
        self._m = modulo
        self._url = url
        self._t = timeout
        self.c = modulo.Cdp(url, timeout)
        self.guasti = []

    def riaggancia(self, perche):
        self.guasti.append(perche)
        try:
            self.c.chiudi()
        except Exception:                      # noqa: BLE001
            pass
        time.sleep(0.6)
        self.c = self._m.Cdp(self._url, self._t)
        self.c.chiama("Runtime.enable")
        try:
            self.c.chiama("Emulation.setTouchEmulationEnabled",
                          enabled=True, maxTouchPoints=5)
        except Exception:                      # noqa: BLE001
            pass

    def chiama(self, metodo, **p):
        return self.c.chiama(metodo, **p)

    def valuta(self, e, attendi=True):
        return self.c.valuta(e, attendi)


def _cdp():
    p = os.path.join(QUI, "02-pagina-misura-cdp.py")
    spec = importlib.util.spec_from_file_location("cdpmod", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ⛔ The seam that the `F4-TOCCO` anchor asks for, put in by the bench.  It is the same
#    as in `04-b27-classico.py`: the coordinator will write it in `collega()` on the
#    unidirectional stream of §2.5, here it sends to this process.
#    ⚠ It is the only difference between bench and product, and it is declared: the
#      TRANSPORT is not measured here.
PROLOGO = r"""
(function () {
  var n = 0, coda = Promise.resolve();
  window.__b28 = { spediti: 0, errori: [] };
  window.REMOTIX_INPUT = {
    prossimo_id: function () { n = (n >= 4294967295) ? 1 : n + 1; return n; },
    manda: function (tipo, corpo) {
      var m = new Uint8Array(6 + corpo.length);
      var v = new DataView(m.buffer);
      v.setUint16(0, tipo); v.setUint32(2, corpo.length); m.set(corpo, 6);
      window.__b28.spediti++;
      coda = coda.then(function () { return fetch("/byte", { method: "POST", body: m }); })
                 .catch(function (e) { window.__b28.errori.push(String(e)); });
    },
  };
  window.__b28.fase = function (nome) {
    coda = coda.then(function () { return fetch("/fase", { method: "POST", body: nome }); })
               .catch(function (e) { window.__b28.errori.push(String(e)); });
    return coda;
  };
  window.__b28.attendi = function () { return coda.then(function () { return true; }); };
  /* ⛔⭐ THE SPY — `CODER.md` §3.7: «the sender is not deduced: it is asked».
     It records what the BROWSER really delivered to the page, so a
     red of the automatic switch can be attributed — to the product, or to the bench
     that did not deliver the event it believed it had sent.
     ⚠ These are the bench's observations on Chrome: no verdict is built on
       these fields, they serve to say WHERE to look. */
})()
"""

# ⛔⭐ THE SPY OF THE SWITCH TAB — `CODER.md` §3.7: «the sender is not
#     deduced: it is asked of the core».  It records what the BROWSER
#     really delivered to the page, so a red of the switch can be
#     attributed: to the product, or to the bench that did not deliver the event.
# ⚠ It is PASSIVE: a non-passive listener on `touchstart` blocks
#   `Input.dispatchTouchEvent` — measured on 14 Aug 2026.
SPIA = r"""
(function () {
  window.__spia = [];
  var p = { capture: true, passive: true };
  addEventListener("pointerdown", function (e) {
    window.__spia.push(["pointerdown", e.pointerType]); }, p);
  addEventListener("touchstart", function (e) {
    window.__spia.push(["touchstart", e.touches.length]); }, p);
  addEventListener("mousedown", function () {
    window.__spia.push(["mousedown", 0]); }, p);
})()
"""

# ⛔ The page's scene: the canvas is switched on and given a KNOWN frame, or
#    we would not know where to touch.  ⚠ It is what `04-b27` does for the classic one.
SCENA = r"""
(function () {
  document.body.dataset.schermo = "acceso";
  const t = document.getElementById("schermo");
  t.width = %d; t.height = %d;
  t.style.width = "960px"; t.style.height = "540px";
  const s = window.REMOTIX && window.REMOTIX.tocco;
  if (!s) return JSON.stringify({errore: "⛔ REMOTIX.tocco does not exist"});
  const r = t.getBoundingClientRect();
  return JSON.stringify({ disposizione: document.body.dataset.disposizione,
                          perche: s.perche(), contesto: s.contesto(),
                          soglie: s.soglie, stato: s.stato(),
                          cornice: [r.left, r.top, r.width, r.height] });
})()
"""


def gira(porta, diagnosi, esiti_f, registro_f, attesa=30):
    cdp = _cdp()
    with open(os.path.join(RADICE, "src", "pagina.html"), "rb") as f:
        html = f.read()
    for chiave, valore in ((b"__IMPRONTA__", b""), (b"__AVVISO__", b""),
                           (b"__BANNATO__", b"no"), (b"__RESTANO_MS__", b"0")):
        html = html.replace(chiave, valore)
    raccolta = Raccolta()
    s = servitore(porta, raccolta, html)
    print("  server on http://127.0.0.1:%d — the PRODUCT's page, %d bytes"
          % (porta, len(html)))

    b = cdp.pagina(diagnosi, attesa)
    c = Guida(cdp, b["webSocketDebuggerUrl"], timeout=20)
    c.chiama("Page.enable")
    c.chiama("Runtime.enable")
    c.chiama("Page.addScriptToEvaluateOnNewDocument", source=PROLOGO)
    # ⛔ Touch is DECLARED: without it, a desktop Chrome delivers no
    #    `Touch` event and the bench would measure its own silence.
    c.chiama("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=5)
    # ⛔⭐ THE WINDOW MUST BE IN FRONT AND ACTIVE, AND IT IS NOT A WHIM.
    #  `[M]` 14 Aug 2026: `Input.dispatchTouchEvent` **does not return**
    #  intermittently, in different phases on every run.  The bench runs on the
    #  user's REAL desktop (that is what the mandate asks): when the window
    #  ends up behind another one, the renderer stops producing frames — it is the
    #  same fact that `STUDI.md` §web §6.2 measures on Xvfb, «without a screen there is no
    #  scanout» — and the acknowledgement of the input event never arrives.
    #  ⇒ The page is told that it has the focus, and the window is brought
    #    to the front.  ⚠ It is a declaration about the SCENE, not a cure of the
    #    product: the stage is declared, not moved.
    try:
        c.chiama("Emulation.setFocusEmulationEnabled", enabled=True)
    except Exception:                          # noqa: BLE001
        print("  ⚠ this Chrome does not have `setFocusEmulationEnabled`")
    try:
        c.chiama("Page.bringToFront")
    except Exception:                          # noqa: BLE001
        pass
    c.chiama("Page.navigate",
             url="http://127.0.0.1:%d/?disposizione=tocco" % porta)
    time.sleep(2.0)

    scena = {
        "macchina": os.uname().nodename,
        "sessione": os.environ.get("XDG_SESSION_TYPE"),
        "wayland": os.environ.get("WAYLAND_DISPLAY"),
        "display": os.environ.get("DISPLAY"),
        "browser": c.valuta("navigator.userAgent"),
        "tela": list(TELA),
        "quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    acceso = c.valuta(SCENA % TELA)
    if not acceso:
        print("  ⛔ the page did not answer the scene")
        s.shutdown()
        return 3, scena, []
    pag = json.loads(acceso)
    scena["pagina"] = pag
    print("  scena:", json.dumps(scena, ensure_ascii=False)[:600])
    if pag.get("errore"):
        print("  " + pag["errore"])
        s.shutdown()
        return 3, scena, []
    if pag.get("disposizione") != "tocco":
        print("  ⛔ the layout in force is «%s», not «tocco»: the bench "
              "would measure the other half of the page" % pag.get("disposizione"))
        s.shutdown()
        return 3, scena, []

    cx, cy, cw, ch = pag["cornice"]
    ox, oy = cx + cw / 2, cy + ch / 2      # the centre of the canvas, in CSS px

    # ── THE SYNTHETIC HAND ─────────────────────────────────────────────────
    # ⛔ CDP wants the ACTIVE points at every event: at `touchEnd` the ones
    #    that REMAIN are sent, and the released one is omitted.  Getting it wrong
    #    means measuring a hand that nobody ever made.
    #
    # ⛔⭐ AND EVERY NEW CONTACT TAKES A NEW IDENTIFIER — `[M]` 14 Aug
    #     2026, and the line was born from a HANG of the bench, not from reasoning.
    #
    #  Reusing identifier `1` for the second contact of the tap-and-a-half,
    #  `Input.dispatchTouchEvent` **no longer returned**: the CDP call timed out
    #  at the first `touchMove` after the finger landed again, reproducibly (case C5b,
    #  two runs out of two).  ⛔ It is a defect of the TOOL, not of the product.
    #
    # ⭐ And the new identifier is also truer to reality: a touch
    #    panel assigns a NEW `tracking id` to every new contact, and does not
    #    recycle the one just released.  ⇒ The bench now tests the tap-and-a-half
    #    with two DIFFERENT identifiers, which is what happens with a real
    #    finger — and it necessarily proves that the recogniser links it on SPACE
    #    (40 px) and TIME (300 ms), never on the identity of the contact.
    attivi = {}
    posti = {}
    prossimo = [100]

    def _manda(tipo):
        c.chiama("Input.dispatchTouchEvent", type=tipo,
                 touchPoints=[{"x": float(v[0]), "y": float(v[1]), "id": k}
                              for k, v in attivi.items()])

    def giu(i, x, y):
        prossimo[0] += 1
        posti[i] = prossimo[0]
        attivi[posti[i]] = (ox + x, oy + y)
        _manda("touchStart")

    def muovi(punti):
        for i, x, y in punti:
            if i in posti:
                attivi[posti[i]] = (ox + x, oy + y)
        _manda("touchMove")

    def su(i):
        attivi.pop(posti.pop(i, None), None)
        _manda("touchEnd")

    def dorme(ms):
        time.sleep(ms / 1000.0)

    def fase(nome):
        c.valuta("window.__b28.attendi()")
        c.valuta("window.__b28.fase(%s)" % json.dumps(nome))
        c.valuta("window.__b28.attendi()")

    def zoom_azzera():
        # ⚠ It is not a product switch: it is a reversed PINCH,
        #   made with the same synthetic fingers, to bring the view back to 1x.
        giu(80, -150, 0)
        giu(81, 150, 0)
        for k in range(1, 7):
            muovi([(80, -150 + 24 * k, 0), (81, 150 - 24 * k, 0)])
            dorme(16)
        su(80)
        su(81)
        dorme(60)

    def leggi_zoom(nome):
        z = c.valuta("window.REMOTIX.tocco.stato().zoom")
        raccolta.zoom(nome, z if isinstance(z, (int, float)) else 0)

    def riposa():
        # ⛔ Beyond `T_SEQUENZA` (300 ms), or the next gesture would link as a
        #    tap-and-a-half to the previous one: it is exactly the trap the bench
        #    must avoid walking into by itself.
        dorme(450)

    # ══════════════════════════════════════════════════════════════════════
    # THE SCENES, ONE FUNCTION PER GESTURE.
    #
    # ⛔ AND EVERY SCENE IS PROTECTED: a fault of the TOOL (the CDP call
    #    that does not return) must not throw away the other sixteen measurements, and ⛔ it
    #    must not pass for an outcome either.  ⇒ We reconnect, cancel the
    #    touch in progress, the phase stays WITHOUT bytes — and the judge declares it
    #    red with «the phase was not recorded at all», which is the truth.
    #    ⚠ `CODER.md` §3.10: «a denied reading is not a reading that says
    #      zero».  The faults end up in `04-b28-esiti.jsonl` under `guasti`,
    #      so a red can be attributed to the bench instead of to the product.
    # ══════════════════════════════════════════════════════════════════════

    def f_G1():
        giu(1, -200, 0)
        for k in range(1, 11):
            muovi([(1, -200 + 20 * k, 0)])
            dorme(16)
        su(1)

    def f_G2():
        giu(1, 0, 0)
        dorme(80)
        su(1)

    def f_G3():
        giu(1, -30, 0)
        giu(2, 30, 0)
        dorme(80)
        su(1)
        su(2)

    def _due_dita_scendono():
        giu(1, -30, -100)
        giu(2, 30, -100)
        for k in range(1, 9):
            muovi([(1, -30, -100 + 25 * k), (2, 30, -100 + 25 * k)])
            dorme(16)
        su(1)
        su(2)

    def f_G4():
        # The fingers go DOWN ⇒ `RCP.md` §7.3 wants the vertical axis POSITIVE.
        _due_dita_scendono()

    def f_G5():
        giu(1, 0, 0)
        dorme(80)
        su(1)
        dorme(90)            # within the 300 ms of T_SEQUENZA
        giu(1, 3, 3)         # and within the 40 px of D_STESSO_DITO
        dorme(30)
        for k in range(1, 9):
            muovi([(1, 3, 3 + 20 * k)])
            dorme(16)
        su(1)

    def f_G6():
        # ⛔⭐ HERE IT IS HELD DOWN 20 ms AND NOT 80, AND THE REASON IS MEASURED.
        #
        # `[M]` 14 Aug 2026: with 80 ms of waiting the three-finger tap came out
        # **without a middle click**, and the recogniser was correct.  Direct
        # probe: `durata_max` = **147 ms** against a threshold of 180 — that is, the
        # SYNTHETIC HAND alone costs ~120 ms, because three fingers down and three up
        # are SIX CDP round trips at ~20 ms each.
        #
        # ⇒ The bench was measuring the latency of its own tool, not the
        #   gesture (`LEZIONI.md` §1.11).  The wait is removed, and the time that
        #   remains is the real one of the six trips.
        # ⭐ And a question remains for Nic, which no bench closes: **are 180 ms per
        #    contact enough for a three-finger tap made with a real hand?**
        #    Three fingers do not lift together, and this is exactly the case in
        #    which the threshold is judged by using it.
        giu(1, -40, 0)
        giu(2, 0, 0)
        giu(3, 40, 0)
        dorme(20)
        su(1)
        su(2)
        su(3)

    def _allontana():
        giu(1, -60, 0)
        giu(2, 60, 0)
        for k in range(1, 9):
            muovi([(1, -60 - 15 * k, 0), (2, 60 + 15 * k, 0)])
            dorme(16)
        su(1)
        su(2)
        dorme(60)

    def f_G7():
        _allontana()
        leggi_zoom("G7-pizzico")
        zoom_azzera()

    def f_C1():
        # The tap that lasts a bit too long: 400 ms, and STILL.  T_TAP = 180 ms.
        giu(1, 0, 0)
        dorme(400)
        su(1)

    def f_C2():
        # The tap that slides: 120 ms, but 30 px.  D_TAP = 9 CSS px.
        giu(1, 0, 0)
        for k in range(1, 4):
            muovi([(1, 10 * k, 0)])
            dorme(30)
        su(1)

    def f_C3():
        # ⭐ The two fingers that land 30 ms apart — BUT they
        #    overlap: it is the declared threshold.
        giu(1, -30, 0)
        dorme(30)
        giu(2, 30, 0)
        dorme(70)
        su(1)
        dorme(20)
        su(2)

    def f_C4():
        # ⛔ And the two fingers that NEVER overlap: the declared defect.
        giu(1, -30, 0)
        dorme(90)
        su(1)
        dorme(40)
        giu(2, 30, 0)
        dorme(90)
        su(2)

    def f_C5a():
        # Still double tap, same spot ⇒ DOUBLE CLICK.
        giu(1, 0, 0)
        dorme(70)
        su(1)
        dorme(90)
        giu(1, 2, 2)
        dorme(70)
        su(1)

    def f_C5b():
        # ⭐ The SAME opening, and then it drags ⇒ DRAG.
        giu(1, 0, 0)
        dorme(70)
        su(1)
        dorme(90)
        giu(1, 2, 2)
        dorme(40)
        for k in range(1, 9):
            muovi([(1, 2 + 18 * k, 2)])
            dorme(16)
        su(1)

    def f_C6():
        # The two-finger drag that starts STILL.
        giu(1, -30, -100)
        giu(2, 30, -100)
        dorme(350)
        for k in range(1, 9):
            muovi([(1, -30, -100 + 25 * k), (2, 30, -100 + 25 * k)])
            dorme(16)
        su(1)
        su(2)

    def f_C7a():
        _allontana()
        leggi_zoom("C7a-pizzico-non-rotella")
        zoom_azzera()

    def f_C7b():
        _due_dita_scendono()
        dorme(60)
        leggi_zoom("C7b-rotella-non-pizzico")

    def f_C8():
        # The leftover finger: two scroll, one lifts, the other carries on.
        giu(1, -30, -100)
        giu(2, 30, -100)
        for k in range(1, 5):
            muovi([(1, -30, -100 + 25 * k), (2, 30, -100 + 25 * k)])
            dorme(16)
        su(1)
        for k in range(1, 5):
            muovi([(2, 30 + 20 * k, 0)])
            dorme(16)
        su(2)

    SCENE = [
        ("G1-un-dito-trascina", f_G1),
        ("G2-un-dito-tap", f_G2),
        ("G3-due-dita-tap", f_G3),
        ("G4-due-dita-trascina", f_G4),
        ("G5-tap-e-mezzo", f_G5),
        ("G6-tre-dita-tap", f_G6),
        ("G7-pizzico", f_G7),
        ("C1-tap-troppo-lungo", f_C1),
        ("C2-tap-che-scivola", f_C2),
        ("C3-due-dita-a-30ms", f_C3),
        ("C4-due-dita-senza-sovrapposizione", f_C4),
        ("C5a-doppio-clic", f_C5a),
        ("C5b-tap-e-mezzo-che-trascina", f_C5b),
        ("C6-trascinamento-che-comincia-fermo", f_C6),
        ("C7a-pizzico-non-rotella", f_C7a),
        ("C7b-rotella-non-pizzico", f_C7b),
        ("C8-il-dito-residuo", f_C8),
    ]
    assert sorted(n for n, _ in SCENE) == sorted(CASI), \
        "the scenes and the judge's cases do not match"

    verdetti = {}
    guasti_di_fase = []
    for nome, fn in SCENE:
        # ⛔ ONE ATTEMPT ONLY, and the second is NOT made.  On a retry, the bytes of the
        #    half-successful attempt stay in the phase and add up to those
        #    of the second: the judge read «three left-button events out of
        #    four» on a gesture the product had done right twice.
        #    ⇒ A fault of the tool is DECLARED, not hidden with a
        #      repetition (`CODER.md` §3.10: «a denied reading is not a
        #      reading that says zero»).
        for tentativo in (1,):
            try:
                fase(nome)
                fn()                # ⛔ The verdict the PAGE gave to the gesture, with its numbers:
                #    when a case is red, it says which condition gave way —
                #    duration, smear or decision — instead of leaving it to be deduced.
                try:
                    verdetti[nome] = json.loads(c.valuta(
                        "JSON.stringify(window.REMOTIX.tocco.stato().ultimo_gesto)")
                        or "null")
                except Exception:              # noqa: BLE001
                    pass
                break
            except (TimeoutError, OSError, RuntimeError) as e:
                print("  ⚠ TOOL FAULT in phase %s (%s)"
                      % (nome, type(e).__name__))
                guasti_di_fase.append(nome)
                c.riaggancia("phase %s: %s" % (nome, type(e).__name__))
                attivi.clear()
                posti.clear()
                try:
                    c.chiama("Input.dispatchTouchEvent", type="touchCancel",
                             touchPoints=[])
                except Exception:              # noqa: BLE001
                    pass
                dorme(400)
        riposa()

    fase("F-fine")

    c.valuta("window.__b28.attendi()")
    time.sleep(0.5)

    # ── ⒝ THE AUTOMATIC SWITCH, and S1 the seam ─────────────────────────────
    passaggio = misura_passaggio(c, cdp, porta, ox, oy, diagnosi)
    scena["passaggio"] = passaggio
    scena["verdetti_della_pagina"] = verdetti
    scena["guasti_dello_strumento"] = list(c.guasti)
    if c.guasti:
        print("  ⚠ %d tool faults, reconnected: %s"
              % (len(c.guasti), c.guasti))

    with raccolta.blocco:
        righe = list(raccolta.righe)
    s.shutdown()

    with open(registro_f, "w", encoding="utf-8") as f:
        for r in righe:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    esiti = giudica(righe)
    esiti += passaggio["esiti"]
    # ⛔ The phases in which the TOOL failed are not counted among the product's
    #    reds — and they are not counted among the greens either.  They stay NOT
    #    MEASURED, with a mark all their own, and the bench exits with a different
    #    code: «to be redone», not «the product is broken».
    for e in esiti:
        if e["caso"] in guasti_di_fase:
            e["strumento"] = True
    return 0, scena, esiti


# ⛔ The switch is measured on WHICH LAYOUT IS IN FORCE, read from the
#    document — not «there is a function that changes it».
def misura_passaggio(c_vecchia, cdp, porta, ox, oy, diagnosi):
    """⛔⭐ THE SWITCH IS MEASURED IN A NEW TAB, AND IT IS NOT A CONVENIENCE.

    `[M]` 14 Aug 2026, Chrome 151.0.7922.137.  Measuring the switch in the
    **same** tab as the gestures — that is, after a second `Page.navigate` and after
    a mouse event — ⛔ `Input.dispatchTouchEvent` **no longer delivers
    anything to the page**: the prologue's spy records neither a `touchstart`
    nor a `pointerdown` of type `touch`, and the CDP call returns without error.
    ⇒ The bench read «after a FINGER: classico» and blamed the PRODUCT.

    ⭐ In a freshly opened tab the same sequence works, and the switch
       is measured in full: start → **tocco**, mouse → **classico**, finger →
       **tocco**.  ⚠ `CODER.md` §3.11: suspicion goes first to the measurement.
    """
    import urllib.request
    esiti, note = [], {}

    # A new tab, its own, closed at the end.
    with urllib.request.urlopen(urllib.request.Request(
            "http://127.0.0.1:%d/json/new?about:blank" % diagnosi,
            method="PUT"), timeout=10) as r:
        scheda = json.loads(r.read().decode())
    c = Guida(cdp, scheda["webSocketDebuggerUrl"], timeout=20)
    c.chiama("Page.enable")
    c.chiama("Runtime.enable")
    c.chiama("Page.addScriptToEvaluateOnNewDocument", source=SPIA)
    c.chiama("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=5)

    # ⛔⭐ A DEFECT OF THE TOOL, MEASURED AND WORKED AROUND — `[M]` 14 Aug 2026,
    #     Chrome 151.0.7922.137 on CHUWI.
    #
    # After an `Input.dispatchMouseEvent`, the following `Input.dispatchTouchEvent`
    # **never returns**: the CDP call times out waiting for an answer that never
    # arrives.  ⇒ The first run of this bench read «after a TOUCH: classico»
    # and blamed the PRODUCT for not going back to touch.
    #
    # ⚠ `CODER.md` §3.11 — «when code read and measurement contradict each other, the
    #   suspicion goes FIRST to the measurement».  Here the code said the switch
    #   was there and the measurement said no: the code was right.
    #
    # ⭐ The cure: touch emulation is switched on again after every mouse event.
    #    Measured: start «tocco» → finger «tocco» → mouse «classico» → finger
    #    «tocco».  ⛔ And it is declared here instead of hidden in a line.
    def mouse():
        c.chiama("Input.dispatchMouseEvent", type="mousePressed", x=ox, y=oy,
                 button="left", clickCount=1, buttons=1)
        c.chiama("Input.dispatchMouseEvent", type="mouseReleased", x=ox, y=oy,
                 button="left", clickCount=1, buttons=0)
        time.sleep(0.3)
        c.chiama("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=5)

    # ⚠ A NEW identifier at every contact, as in the synthetic hand: a recycled
    #   id blocks `Input.dispatchTouchEvent` (measured, see above).
    dito_id = [200]

    def dito(pt=None):
        dito_id[0] += 1
        # ⛔ Touch emulation is switched ON AGAIN before every contact — `[M]`
        #    14 Aug 2026, and the page's spy is the one that said so:
        #    after the second navigation and after a mouse event the
        #    `touchStart` events NO LONGER reached the page (no `touchstart`
        #    and no `pointerdown` of type touch in the spy), and the bench
        #    blamed the PRODUCT for not going back to touch.  ⚠ `CODER.md` §3.7:
        #    the sender is not deduced, it is asked.
        c.chiama("Emulation.setTouchEmulationEnabled", enabled=True,
                 maxTouchPoints=5)
        c.chiama("Input.dispatchTouchEvent", type="touchStart",
                 touchPoints=[{"x": pt[0] if pt else ox, "y": pt[1] if pt else oy,
                               "id": dito_id[0]}])
        c.chiama("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])
        time.sleep(0.3)

    def disposizione():
        return c.valuta("document.body.dataset.disposizione")

    def stato():
        v = c.valuta("JSON.stringify(window.REMOTIX.tocco.stato())")
        return json.loads(v) if v else {}

    def spediti():
        return c.valuta("window.__b28.spediti") or 0

    # ── D1 · the forced layout is really in force, and touch speaks ────────
    #    ⚠ It is read on the GESTURES tab, not on the new one.
    d = c_vecchia.valuta("document.body.dataset.disposizione")
    esiti.append({"caso": "D1-disposizione-in-vigore", "verde": d == "tocco",
                  "perche": "`body[data-disposizione]` = «%s» (the PRODUCT "
                            "wrote it, not the bench)" % d})

    # ── D2 · ⭐ THE REAL SWITCH, on REAL events ──────────────────────────
    # The forcing is removed by reloading without `?disposizione`, then the
    # mouse is used (⇒ classico) and then the finger (⇒ tocco).  ⛔ No hardware
    # is emulated: events are sent that the browser delivers like any other.
    c.chiama("Page.navigate", url="http://127.0.0.1:%d/" % porta)
    time.sleep(2.0)
    c.valuta(SCENA % TELA)
    d0 = disposizione()
    note["allavvio"] = {"disposizione": d0,
                        "perche": c.valuta("window.REMOTIX.tocco.perche()"),
                        "contesto": json.loads(
                            c.valuta("JSON.stringify(window.REMOTIX.tocco.contesto())"))}

    dito()
    d_dito0 = disposizione()
    mouse()
    d_mouse = disposizione()
    dito()
    d_dito = disposizione()

    note["spia"] = json.loads(c.valuta("JSON.stringify(window.__spia)") or "[]")
    verde = (d_dito0 == "tocco" and d_mouse == "classico" and d_dito == "tocco")
    esiti.append({"caso": "D2-passaggio-automatico", "verde": verde,
                  "perche": ("at start «%s»; after a FINGER «%s»; after a mouse "
                             "CLICK «%s»; after another FINGER «%s»"
                             % (d0, d_dito0, d_mouse, d_dito))
                            + ("" if verde else
                               "  ⛔ expected tocco → classico → tocco; the spy says: %s"
                               % note["spia"][-8:])})

    # ── D3 · ⭐ «in force» means the OTHER ONE IS OFF ────────────────
    # In classic, a complete touch must NOT produce any touch
    # message: the handlers are really detached, not just declared detached.
    mouse()
    if disposizione() != "classico":
        esiti.append({"caso": "D3-l-altra-e-spenta", "verde": False,
                      "perche": "could not get back into classic"})
    else:
        # ⛔ Before: in CLASSIC the touch one must be off and the classic one on.
        t_prima = json.loads(c.valuta("JSON.stringify(window.REMOTIX.tocco.stato())"))
        cl_prima = json.loads(c.valuta(
            "JSON.stringify(window.REMOTIX.input_classico.stato())"))
        prima = c.valuta("window.REMOTIX.tocco.spediti.length")
        c.chiama("Input.dispatchTouchEvent", type="touchStart",
                 touchPoints=[{"x": ox - 100, "y": oy, "id": 7}])
        for k in range(1, 6):
            c.chiama("Input.dispatchTouchEvent", type="touchMove",
                     touchPoints=[{"x": ox - 100 + 30 * k, "y": oy, "id": 7}])
            time.sleep(0.02)
        c.chiama("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])
        time.sleep(0.3)
        dopo = c.valuta("window.REMOTIX.tocco.spediti.length")
        cl = json.loads(c.valuta(
            "JSON.stringify(window.REMOTIX.input_classico.stato())"))
        nuovi = json.loads(c.valuta(
            "JSON.stringify(window.REMOTIX.tocco.spediti.slice(%d))" % prima) or "[]")
        d_fin = disposizione()
        # ⛔⭐ «IN FORCE» MEANS THE OTHER ONE IS OFF, and it is proven on three
        #    observable facts, not on a variable that says so:
        #
        #   1. before the gesture, in CLASSIC: touch is off and classic
        #      on — the two halves are never on together;
        #   2. after the gesture, in TOUCH: classic is off;
        #   3. ⛔ and the drag started IN THE OTHER layout produces
        #      **no ghost click**: it may move the pointer (the
        #      contact is what switches to touch, and it is right that the
        #      gesture is not lost), but a PULSANTE in there would mean
        #      that half a gesture was taken for a whole gesture.
        clic = [m for m in nuovi if m.get("nome") == "PULSANTE"]
        verde = (t_prima.get("in_vigore") is False
                 and cl_prima.get("in_vigore") is True
                 and d_fin == "tocco" and not cl.get("in_vigore")
                 and not clic)
        esiti.append({"caso": "D3-l-altra-e-spenta", "verde": verde,
                      "perche": ("in classic: touch in force %s, classic in "
                                 "force %s; after the gesture: layout «%s», "
                                 "classic in force %s; the gesture produced %d "
                                 "messages, of which %d PULSANTE (ghost click)"
                                 % (t_prima.get("in_vigore"),
                                    cl_prima.get("in_vigore"), d_fin,
                                    cl.get("in_vigore"), dopo - prima, len(clic)))})

    # ── S1 · ⭐ THE SEAM between the two anchors ────────────────────────────
    c.chiama("Input.dispatchTouchEvent", type="touchStart",
             touchPoints=[{"x": ox, "y": oy, "id": 5}])
    for k in range(1, 6):
        c.chiama("Input.dispatchTouchEvent", type="touchMove",
                 touchPoints=[{"x": ox + 25 * k, "y": oy, "id": 5}])
        time.sleep(0.02)
    c.chiama("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])
    time.sleep(0.3)
    st = stato()
    visibile = c.valuta(r"""
      (function () {
        const nomi = ["puntatore", "puntatore-di-ripiego"];
        for (const n of nomi) {
          const e = document.getElementById(n);
          if (e && getComputedStyle(e).display !== "none"
                && e.getBoundingClientRect().width > 0) return n;
        }
        return null;
      })()""")
    # ⛔ TWO DISTINCT THINGS, and confusing them would hide the more important one:
    #   S1a  the user SEES a pointer while dragging            (invariant I8)
    #   S1b  and sees it without FALLBACK, i.e. the seam holds  (the F5 lesson)
    esiti.append({"caso": "S1a-il-puntatore-si-vede", "verde": bool(visibile),
                  "perche": "in touch layout the visible pointer is «%s»"
                            % visibile})
    esiti.append({"caso": "S1b-cucitura-senza-ripiego",
                  "verde": bool(st.get("puntatore_cucito"))
                           and not st.get("puntatore_cucitura_rotta"),
                  "perche": ("`REMOTIX_PUNTATORE` is there: %s; seam broken: %s"
                             % (st.get("puntatore_cucito"),
                                st.get("puntatore_cucitura_rotta")))
                            + ("" if not st.get("puntatore_cucitura_rotta") else
                               "  ⛔ `muovi()` does not turn on `cl_noto`: in touch the "
                               "shared pointer stays invisible — a cure of ONE "
                               "line in the F4-INPUT-CLASSICO anchor (link A7)")})
    esiti.append({"caso": "S2-cucitura-classico",
                  "verde": bool(st.get("classico_cucito")),
                  "perche": "`REMOTIX_CLASSICO` (F4-INPUT-CLASSICO anchor, link A7): %s"
                            % st.get("classico_cucito")})

    # ── D4 · the context is NOT the operating system ──────────────────────
    with open(os.path.join(RADICE, "src", "pagina.html"), encoding="utf-8") as f:
        testo = f.read()
    a = testo.split("ANCORA F4-TOCCO — INIZIO")[-1].split("ANCORA F4-TOCCO — FINE")[0]
    # ⛔ Comments are removed BEFORE searching, and it is not a nicety: the first
    #    run of this check was red on a comment line that said
    #    «`navigator.userAgent` does not appear here».  A check that reads its
    #    own explanations measures the prose, not the code.
    import re as _re
    codice = _re.sub(r"/\*.*?\*/", "", a, flags=_re.S)
    codice = _re.sub(r"^\s*//.*$", "", codice, flags=_re.M)
    colpevoli = [s for s in ("userAgent", "navigator.platform", "userAgentData")
                 if s in codice]
    esiti.append({"caso": "D4-il-contesto-non-e-il-sistema", "verde": not colpevoli,
                  "perche": ("in the F4-TOCCO anchor nothing appears that comes from the "
                             "operating system" if not colpevoli
                             else "⛔ they appear: %s" % colpevoli)})

    try:
        urllib.request.urlopen(
            "http://127.0.0.1:%d/json/close/%s" % (diagnosi, scheda["id"]),
            timeout=5).read()
    except Exception:                          # noqa: BLE001
        pass
    note["guasti_della_scheda"] = list(c.guasti)
    return {"esiti": esiti, "note": note}


# ---------------------------------------------------------------------------
def stampa(esiti):
    guasti = [e for e in esiti if e.get("strumento")]
    misurati = [e for e in esiti if not e.get("strumento")]
    verdi = sum(1 for e in misurati if e["verde"])
    rossi = [e for e in misurati if not e["verde"]]
    for e in esiti:
        segno = "⚠ " if e.get("strumento") else ("✅" if e["verde"] else "⛔")
        print("  %s %-38s %s" % (segno, e["caso"], e["perche"]))
    print("\n  %d green out of %d measured" % (verdi, len(misurati)))
    if guasti:
        print("  ⚠ %d NOT MEASURED because of a tool fault: %s"
              % (len(guasti), [e["caso"] for e in guasti]))
        print("    (⛔ they are neither green nor red: the run is redone)")
    if rossi:
        return 1
    return 2 if guasti else 0


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--certifica", action="store_true")
    a.add_argument("--gira", action="store_true")
    a.add_argument("--verdetto")
    a.add_argument("--porta", type=int, default=7671)
    a.add_argument("--diagnosi", type=int, default=7672)
    a.add_argument("--esiti", default=os.path.join(QUI, "04-b28-esiti.jsonl"))
    a.add_argument("--registro", default=os.path.join(QUI, "04-b28-registro.jsonl"))
    o = a.parse_args()

    if o.certifica:
        return certifica()
    if o.verdetto:
        righe = [json.loads(r) for r in open(o.verdetto, encoding="utf-8") if r.strip()]
        return stampa(giudica(righe))
    if o.gira:
        codice, scena, esiti = gira(o.porta, o.diagnosi, o.esiti, o.registro)
        if codice:
            return codice
        with open(o.esiti, "a", encoding="utf-8") as f:
            f.write(json.dumps({"scena": scena, "esiti": esiti},
                               ensure_ascii=False) + "\n")
        return stampa(esiti)
    a.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
