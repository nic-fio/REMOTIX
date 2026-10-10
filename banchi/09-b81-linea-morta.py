#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b81 — THE TWO CURES THAT NEVER RAN: the DEAD LINE and the GHOST
         EVICTION.

⛔⛔ WHY THIS BENCH EXISTS, and the reason is not «to prove they work».
    Of the two cures, one THROWS A SESSION OUT.  ⇒ The question that drives
    everything else is not *«does it fire when it should?»* but **«does it fire when it
    should NOT?»** — because the two errors do not cost the same, and whoever wrote the
    cure declares it in its own box: erring high means
    a few more seconds of frozen image, erring low means
    **throwing out someone who was working**, and that cannot be undone.

⇒ TEST 1 IS THE ONE THAT CAN MAKE THE CURE BE WITHDRAWN, and the other five
  exist as a frame around it.  If `casa-cattiva` — `[M]` 1.71 % loss, 7.8-10.2
  frames/s, live session — makes the dead line fire even once
  in ten minutes, the cure is not switched on and the report says so first.

═══ THE FALSIFIER OF TEST 1, DECLARED BY WHOEVER WROTE THE CURE ═══

⚠ `[?]` The threshold is on the fraction **DECLARED BY NGTCP2** (`pkt_lost /
  pkt_sent`), while the 1.71 % that holds is the loss **INJECTED** by
  `netem`.  And the two may not coincide: with jitter and reordering the
  declared one can be HIGHER, because a packet that overtakes is
  mistaken for a lost packet — and it is the central fact of this phase
  (`09-b76`, «disorder is NOT loss»).

⇒ HERE BOTH ARE MEASURED, and reported side by side:
    · the INJECTED one — the probe of `09-b76`, which crosses the same `netem`;
    · the DECLARED one — rebuilt from the `rete-quic` lines, which carry
      `persi_d`, `spediti_d` and `da_ms`, that is exactly the three numbers with which
      `linea_morta_giudica()` decides.  ⇒ ITS guards are applied
      (`spediti_d >= 200`, `da_ms >= 1000`) and we count whether two windows in a row
      would ever have broken through 50‰.
  ⛔ If the DECLARED one breaks the threshold on a line that HOLDS, the threshold is
     wrong **and it must be said**, not worked around: it is predicate `p1b`.
  ⚠ `[?]` The reconstruction is a declared APPROXIMATION, and on the wrong
    cautious side: the `rete-quic` lines are silent when nothing changes,
    so one of their windows can be LONGER than a second — and a
    longer window averages more, that is it **lowers** the peak.  ⇒ On its own it
    is not enough, and next to it goes the calibration (further below).

⭐ THE CALIBRATION, which closes the hole of the reconstruction: a short run on the
   SAME `casa-cattiva` with `--linea-morta-permille 1`.  At that threshold the
   cure fires for sure, and firing **prints the `permille=` that it
   computed itself**, on its own window, with its own arithmetic.  ⇒ It is the only way to
   read the declared fraction without redoing it by hand, and it serves to check
   the reconstruction against the product's true number.

═══ `[M]` 24 AUGUST 2026 — THE CURE REDONE: IT CAN BE SWITCHED ON ═══

⭐ Binary `md5 0a6fc21a4719a8122980eb6f827820cf`, working tree = HEAD
   `64db391`.  ⛔ And the ground also checks an ABSENCE: `--linea-morta-permille`
   must be REFUSED by the binary (exit 2).  ⚠ Not with a `grep`: the string
   is there all right, in the help text — and the first round of that check gave
   red on a correct binary (⇒ `09-b81-terreno.sh`, step 3).

⛔⛔ **TEST 1 — ZERO FIRINGS IN TEN MINUTES.**  `casa-cattiva`, `--linea-morta`
     on: 9.71 frames/s, coverage **1.00** (600 s out of 600), largest gap
     **0.479 s**, client still attached at 599.88 s, no farewell.
     ⭐ And in the same run the WITNESS says `permille` median **529‰** with 392
        windows out of 392 above the old 50‰: **the old cure would have killed
        this very session**, the new one does not touch it.  It is the cleanest
        comparison this phase has — same profile, same bench, same
        ten minutes, and only the quantity the decision rests on changes.

⭐⭐ THE FOUR MAXIMUM STALLS AGAINST THE 5 000 ms THRESHOLD — and they are MEASURED, not
    «it did not fire»: the line comes out only on firing, so the same
    profile is rerun with lower and lower thresholds until one fires (`scala_stallo()`).

      profile          maximum stall         margin      gap at the CLIENT
      `ritardo-30`     < 500 ms (no firing)   > 10×       0.157-0.175 s
       (healthy)
      `casa-cattiva`   < 500 ms (no firing)   > 10×       0.359-0.479 s
      `raffica-1`      **1 001 ms** MEASURED  **5.0×**    0.52-3.73 s
      STILL scene      count does not start   —           (1 and 3 frames
                                                           in 90 s)

    ⭐ `raffica-1` confirms the derivation with an independent number: the
       narrow side is **1.00 s**, which is exactly what the box of
       `WT_LM_STALLO_MS` had used — and the margin is the declared 5.0×.

⚠ AND ONE THING TO SAY: the STALL (server, video bytes gone out) and the GAP (client,
  frames arrived) are NOT the same quantity, and the threshold is derived from the
  second while the cure measures the first.  `[M]` on `raffica-1` one run gave
  a 3.73 s gap with the stall not firing even at 1 000 ms: **the server's stall
  is SMALLER than the client's gap**, because the bytes leave and what is
  missing is the retransmission.  ⇒ The error goes the good way (it fires later,
  never earlier), but the derivation's number is cautious and not
  exact.

⛔⛔ **THE STILL SCENE — the worst way in which the cure could fail — HOLDS.**
     90 s of desktop that does not change, zero firings at the threshold in force **and at
     1 000 ms**, that is five times narrower; client attached to the
     end.  ⭐ And the scene was really still, checked and not hoped: the server's final
     count says **1 and 3 frames in 90 s**, all sent.
     ⇒ The stall count does not start when there is nothing to send.

⭐ THE OTHERS:
    2 · `raffica-forte` (13.19 % injected): fires at **18.95 s**,
        `causa=stallo stallo_ms=5008 offerti=198 usciti_byte=0
        coda_video=31146` — both halves true — and the wire drops.
        ⚠ The witness said `permille=133`: LOWER than `casa-cattiva`, and
          it is yesterday's refutation seen from the other side.
    3 · silence: `silenzio_ms=10006`, `prove=12`, 10.24 s after the `kill -9`, and
        in the line `stallo_ms=8 offerti=0` — that is, the two causes stay separate.
        With the cure off, zero firings.  ⚠ The price of the PINGs stays NOT JUDGEABLE:
        a «still» session costs 2 463 kbit/s of PCM audio.
    6 · I6: with the defaults zero firings, and the two profiles stay within the grid of
        `09-b76`.
    4 and 5 (eviction, two users) were NOT rerun: `src/rcp.c` and
        `src/rcp.h` have an `md5` IDENTICAL to yesterday (`8a0e30d2…`, `439af0b8…`) and the
        ghost cure lives there — there is nothing that could have moved them.

═══ `[M]` 23 AUGUST 2026 — THE OLD CURE, AND WHY IT WAS WITHDRAWN ═══

⛔⛔⛔ **THE LOSS FRACTION ORDERED THE TWO CASES THE WRONG WAY ROUND.**  `[M]` same
      bench, binary `md5 d8c2c4461df7319fb40f33d1f96df4de`:

        profile         INJECTED (probe)    DECLARED (ngtcp2)     the line…
        casa-cattiva      1.86 - 2.15 %       **512‰** (51.2 %)   HOLDS 10 minutes
        raffica-forte    12.28 - 14.00 %      **123‰** (12.3 %)   does NOT hold

      ⇒ The one that WORKS declared four times more loss than the one that
        does not work: no threshold separates them.  ⭐ The cause: `casa-cattiva`
        reorders **93.5 %** of the packets, and ngtcp2 counts an overtake as
        a loss.  ⚠ And it was not the connection start-up: with the first
        ten windows removed, 399 out of 399 stayed above threshold.
      ⇒ The cure was REDONE, not retuned, and `--linea-morta-permille` was
        removed.  `permille=` stays in the line as a WITNESS of the reordering.

═══ WHAT IS MEASURED, AND WITH WHAT ═══

⛔ Not one line of what already exists is rewritten.  This bench is almost entirely
   made of other people's pieces, and it DECLARES them:

     `09-b76-rete-cattiva.py`  the profiles (`casa-cattiva`, `raffica-forte`), the
                               PROBE of the injected loss, the `netem`
                               discipline, the qdisc counters, the witnesses
                               of the connection, the reduction of delivery,
                               and through it all of `09-b70-ritmo.py`
                               (`giro()`, the §11.1 trace, the five numbers).
     `09-b78-apertura.py`      the session opening timed phase by
                               phase, and ⭐ `--riprova-0f`, which **times the
                               denied slot instead of counting it** — that is, it is already
                               the tool of test 4.
     `07-b64-rete.py`          ⛔ `registro_posato()`, brought in here: see
                               the box above the function.
     `09-lucchetto.py`         the `netem` on `lo` is only one for the whole
                               machine.

⛔ ISOLATION: port **7960**, user **`provanr6`** (uid 1060) and — only for
   test 5 — **`provanr6b`** (uid 1061), tree
   `/media/REMOTIX/src/09nr6-src`, work `/media/REMOTIX/tmp/09nr6`, unit
   `remotix-7960`.  ⛔ Ports 7900, 7910 and 7920 are not touched; `enp7s0` is
   NEVER touched; the `netem` sits on `lo` and the `u32` filters on 7960 only.

⛔⛔ AND THE BINARY IS BUILT FROM THE WORKING TREE, not from `git archive`: the
    two cures are not in any existing binary, and a binary that lacks them
    would pass off as MEASURED a cure that never ran.  The fingerprint is declared
    (`09-b81-terreno.sh porta`, step 3).

EXIT CODES
    0   CONFORMING · 1 NOT CONFORMING (there is a red) · 2 usage/ground/network
    3   ⛔ I HAVE NOTHING TO JUDGE — a run or a predicate refused

Usage (from the laptop):
    python3 banchi/09-b81-linea-morta.py --certifica     ⭐ without a machine
    python3 banchi/09-b81-linea-morta.py terreno
    python3 banchi/09-b81-linea-morta.py p1     # ⛔⛔ the false positive
    python3 banchi/09-b81-linea-morta.py p2     # the real firing
    python3 banchi/09-b81-linea-morta.py p3     # silence, and the PINGs
    python3 banchi/09-b81-linea-morta.py p4     # the eviction
    python3 banchi/09-b81-linea-morta.py p5     # ⛔ two different users
    python3 banchi/09-b81-linea-morta.py p6     # ⛔ the defaults do not change
    python3 banchi/09-b81-linea-morta.py tutte
    python3 banchi/09-b81-linea-morta.py rimetti          ⛔ and it is checked
"""
import argparse, importlib.util, json, os, re, subprocess, sys, time

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ ISOLATION, WRITTEN BEFORE ANY IMPORT THAT READS IT
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `setdefault` and not `=`: the modules I import read the environment at import,
#    and they must read MINE.  ⚠ And after the import we CHECK that they have
#    read it (`importa()`), because a module that took another
#    agent's environment would break another bench's port — and the network is the only thing
#    that, if wrong, hurts those who have nothing to do with it.
PORTA = int(os.environ.setdefault("PORTA", "7960"))
UTENTE = os.environ.setdefault("UTENTE", "provanr6")
UID_B = int(os.environ.setdefault("UID_B", "1060"))
UTENTE2 = os.environ.setdefault("UTENTE2", "provanr6b")
UID_B2 = int(os.environ.setdefault("UID_B2", "1061"))
MACCHINA = os.environ.setdefault("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.setdefault("PAROLA_SUDO", "nicfio")
IND = os.environ.setdefault("IND", "192.168.0.2")
LAV = os.environ.setdefault("LAV", "/media/REMOTIX/tmp/09nr6")
ALB = os.environ.setdefault("ALBERO", "/media/REMOTIX/src/09nr6-src")
DENTRO_ALB = os.environ.setdefault("DENTRO_ALB", "/srv/src/09nr6-src")
DENTRO_LAV = os.environ.setdefault("DENTRO_LAV", "/srv/remotix/tmp/09nr6")
# ⛔ The probe's ports are MINE and are chosen on the fly (see `09-b76`): another
#    agent may start a server while I run.
os.environ.setdefault("PORTE_SONDA", "7969,7968,7967,7966,7965")
os.environ.setdefault("SHM", "/09nr6")
QUI = os.path.dirname(os.path.abspath(__file__))
FUORI = os.environ.setdefault(
    "FUORI", "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX/"
             "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad/09-b81")
UNITA = os.environ.get("UNITA", "remotix-%d" % PORTA)

VIETATA = "enp7s0"     # ⛔ ssh and the user's session go through it: NEVER
DEV = "lo"
# ⛔ The ports that are NOT mine: they are COUNTED and not touched.
VICINE = ("7900", "7910", "7920", "7700", "7730")

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)


def _carica(nome, percorso):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE CONSTANTS OF THE TWO CURES — READ IN THE CODE, not guessed
# ═══════════════════════════════════════════════════════════════════════════
#
# `[R]` `src/webtransport.h` and `src/webtransport.c`, 23 August 2026.  ⚠ They are
# here because the predicates rest on them; if the product changes them, the bench
# must give red — and for this reason the value IN FORCE is reread from the startup
# line (`stato_delle_cure()`) and compared with these.
LM_STALLO_MS = 5000         # `WT_LM_STALLO_MS`  — 5.0 s of frozen image
LM_SILENZIO_S = 10          # `WT_LM_SILENZIO_S`
LM_MIN_PACCHETTI = 200      # `WT_LM_MIN_PACCHETTI` — guard of the WITNESS
LM_FINESTRA_MS = 1000       # `WT_LM_FINESTRA_MS`   — ditto
LM_MIN_PROVE = 2            # `WT_LM_MIN_PROVE`
# ⛔⛔ AND `WT_LM_PERMILLE` NO LONGER EXISTS, neither the constant nor the option: the
#     loss fraction was refuted by this very bench on 23 August
#     2026 (⇒ the box at the top) and went down from JUDGE to WITNESS.
#     ⚠ `permille=` stays in the firing line, but it no longer has a threshold:
#       whoever looked for `soglia_permille=` would not find it, and that is right.
SFRATTO_CONSIGLIATO_MS = 15000   # `SFRATTO_PREDEFINITO` = `SILENZIO / 2`
SILENZIO_MS = 30000              # `SILENZIO` of `rcp.c` — the clock of §5.3

# ── the BENCH's thresholds, in one place only and each with its reason ────
#
# ⛔ «The line HOLDS» is not an opinion: it is the number below which test 1
#    has proved nothing, because I would no longer have a user who was
#    working NOT to throw out.  ⚠ *Sufficient, not exact*: `[M]` 23 Aug
#    `casa-cattiva` gives 7.8-10.2 frames/s and 1.48 % gives 5.5 with coverage
#    1.00 — 5.0 sits below both, and below that the line no longer carries.
FPS_LINEA_CHE_REGGE = 5.0
# ⛔ Below this number of valid windows the reconstruction of the declared fraction is not
#    a measurement: ten minutes at one window per second give ~600.
#    ⚠ Now it serves only DIAGNOSIS: the fraction no longer judges anything.
MIN_FINESTRE_VALIDE = 60
# ⛔⭐ THE MINIMUM STALL MARGIN — how far the threshold must sit above the
#    worst stall observed on a line that HOLDS.
#    ⚠ *Sufficient, not exact*: the cure declares itself 5.0× above the empty
#      second of `raffica-1` and 10× above the 0.50 s of `casa-cattiva`.  Two is
#      half the narrower of those two, and it is the point below which the
#      threshold begins to look like a lucky number — and erring
#      low means throwing out someone who is working, which cannot be undone.
MARGINE_STALLO_MINIMO = 2.0
# ⚠ AND THESE TWO SERVE ONLY DIAGNOSIS, not a judgement: the reconstruction
#   of the DECLARED fraction stays in the bench because it is the number that
#   REFUTED the old cure, and continuing to print it next to the stall is the
#   way to show that the reordering is still there and that it now decides
#   nothing.  ⛔ The 50‰ here is no longer «the threshold»: it is the yardstick with which we
#   look at the same number as back then, so as to compare it with that run.
PERMILLE_DIAGNOSI = 50
FINESTRE_DIAGNOSI = 2
# ⭐ The scale with which the maximum stall is TRACKED DOWN when the cure does NOT fire:
#    the `linea-morta` line comes out only on firing, so «it did not fire»
#    alone does not say BY HOW MUCH it did not fire.  ⇒ We retry with lower and lower
#    thresholds until one fires, and the number that comes out is a true `stallo_ms`
#    measured by the product.  ⛔ Between the lowest that does NOT fire and the highest
#    that fires, the maximum stall is pinned.
SCALA_STALLO_MS = [2000, 1000, 500]
# ⭐ How many windows count as «the connection START-UP»: ten, that is
#   the first ~10 s, which is the stretch where `cwnd` opens and ngtcp2 does the bulk
#   of its loss detection with a small window.  ⚠ The number is chosen,
#   not measured: it serves to SEPARATE two stretches, not to judge one.
PRIME_FINESTRE = 10
# ⭐ The HEALTHY profile on which the reference stall is measured: `ritardo-30` is
#   the denominator of all of `09-b76`'s comparisons — late but IN ORDER, zero
#   loss, zero disorder.  ⚠ Not `liscio`: a profile without even a
#   delay has no RTT, and without RTT the congestion window does not fill
#   and the pacer has nothing to do — that is, it is not a line, it is a short circuit.
RIFERIMENTO_SANO = "ritardo-30"
# ⚠ The dead line's judgement is taken ONCE PER SECOND (`rete_ciclo`),
#   so a firing cannot come BEFORE the threshold and must not come
#   much after.  Three seconds cover the loop, the pacer queue and the `ssh`.
TOLLERANZA_SILENZIO_MS = 3000
# ⭐ The declared cost of the PINGs: ~130 B per round every threshold/2 seconds.
COSTO_PING_DICHIARATO_KBIT_S = 0.21
# ⚠ The eviction is a big number: we accept the delay of one retry round of the
#   client (1 s) plus the server's loop.
TOLLERANZA_SFRATTO_MS = 4000

# ⭐ The grid of `09-b76`, `[M]` 23 August 2026 — it is the denominator of
#    test 6: «the defaults change nothing» means *identical to this*.
GRIGLIA_B76 = {
    "casa-cattiva": {"fps_min": 7.0, "fps_max": 11.0, "copertura_min": 0.90,
                     "perche": "`[M]` 7.8-10.2 frames/s, live session, "
                               "delivery that does not stop"},
    # ⭐ `raffica-1` — the exact twin of `perdita-1`: same average loss,
    #   but in CLUSTERS.  `[M]` it delivers 23.94 frames/s and still had a
    #   WHOLE EMPTY SECOND: it is the case the narrow side of the
    #   stall threshold rests on, and for this reason it must be tested on its own.
    "raffica-1": {"fps_min": 15.0, "fps_max": 45.0, "copertura_min": 0.90,
                  "perche": "`[M]` 23.94 frames/s with a full 1.00 s "
                            "gap — it holds, and must NOT be declared dead"},
    "raffica-forte": {"consegna_si_ferma": True,
                      "perche": "`[M]` delivery STOPS — 7 seconds out of 25 "
                                "saw a frame, gap 14.26 s"},
}


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ OTHER PEOPLE'S MODULES — they are imported, and THEN we check they took MY
#   environment
# ═══════════════════════════════════════════════════════════════════════════
B76 = None
B70 = None
B78 = None
RETE = None
LUC = None


def importa():
    global B76, B70, B78, RETE, LUC
    if B76 is not None:
        return B76
    B76 = _carica("b76rete", os.path.join(QUI, "09-b76-rete-cattiva.py"))
    guai = []
    for nome, mio, suo in (("porta", PORTA, B76.PORTA), ("utente", UTENTE, B76.UTENTE),
                           ("uid", UID_B, B76.UID_B), ("lavoro", LAV, B76.LAV),
                           ("albero", ALB, B76.ALB), ("dev", DEV, B76.DEV),
                           ("vietata", VIETATA, B76.VIETATA),
                           ("dentro_lav", DENTRO_LAV, B76.DENTRO_LAV)):
        if mio != suo:
            guai.append("09-b76 %s: has «%s», mine is «%s»" % (nome, suo, mio))
    if guai:
        raise SystemExit("⛔ I DO NOT MEASURE: the import of 09-b76 did not take my "
                         "environment — " + " · ".join(guai))
    # ⛔ And its `importa()` does the rest: it loads b70, hooks the network to it with
    #    ITS checks (guardian, four-band `prio`, two `u32` filters
    #    on the port only, a `rimetti` that checks itself) and the lock.
    B70 = B76.importa()
    RETE, LUC = B76.RETE, B76.LUC
    if RETE.PORTA != PORTA or RETE.DEV != DEV or RETE.VIETATA != VIETATA:
        raise SystemExit("⛔ I DO NOT TOUCH THE NETWORK: the network module has port %d, "
                         "dev «%s», forbidden «%s»"
                         % (RETE.PORTA, RETE.DEV, RETE.VIETATA))
    B78 = _carica("b78apertura", os.path.join(QUI, "09-b78-apertura.py"))
    guai = []
    for nome, mio, suo in (("porta", PORTA, B78.PORTA), ("utente", UTENTE, B78.UTENTE),
                           ("lavoro", LAV, B78.LAV), ("albero", ALB, B78.ALB),
                           ("dentro_lav", DENTRO_LAV, B78.DENTRO_LAV)):
        if mio != suo:
            guai.append("09-b78 %s: has «%s», mine is «%s»" % (nome, suo, mio))
    if guai:
        raise SystemExit("⛔ I DO NOT MEASURE: the import of 09-b78 did not take my "
                         "environment — " + " · ".join(guai))
    return B76


def root(comando, tetto=300):
    return RETE.root(comando, tetto)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ `registro_posato()` — BROUGHT FROM `07-b64-rete.py`, and that file is not
#     touched
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ THE DEFECT IT AVOIDS, `[M]` 23 August 2026 (`07-b64-rete.py:497`): the
#    closing of a session is SLOW when the pacer has a queue — that bench
#    measured **29 s** of delay on the «final count» of the profile that lost
#    the most.  ⇒ Whoever takes `riga0` right after a run takes a line BEFORE
#    the previous run has finished writing itself, and reads the log of the
#    previous run believing it is theirs.
#
# ⛔⛔ AND HERE IT HURTS TWICE AS MUCH, because what I read is not a count: it is whether
#     the cure FIRED.  A `linea-morta` line of the previous run read inside
#     this run's window would give *«it fired»* to a run in which nothing
#     fired — that is, test 1's false positive would be
#     MANUFACTURED BY THE BENCH.  ⚠ And the opposite direction is just as bad:
#     test 6 (the defaults) would give red on a product that behaves well.
#
# ⚠ And the second fault that box tells about holds identically here: until the
#   previous session has closed, §4.4-bis refuses the new one with
#   `0x0F GIA_ATTIVA_REMOTA` — which in test 4 is PRECISELY THE PHENOMENON I
#   MEASURE.  Measuring the previous run's lock in place of mine would give a
#   true number and a made-up cause.
def conta_conti_finali():
    """How many «audio of …, final count» lines there are NOW in the log."""
    rc, out, _ = root("bash -c \"grep -ac 'audio of .*final count' "
                      "%s/registro.log || true\"" % LAV)
    try:
        return int(out.strip())
    except Exception:
        return -1


def registro_posato(tetto=90.0, quiete=3.0):
    """We wait until the count of «final count» lines stays STILL for
       `quiete` seconds, and that count is returned — see the box above."""
    n = conta_conti_finali()
    fermo, scade = 0.0, time.time() + tetto
    while time.time() < scade and fermo < quiete:
        time.sleep(1.0)
        m = conta_conti_finali()
        fermo = (fermo + 1.0) if m == n else 0.0
        n = m
    return n


def righe_registro():
    """⛔ No `< file` at the end of a `sudo -S`: that redirect STEALS its
       stdin and the password does not arrive — and the count returns 0 silently, that is the
       bench reads the log from the server's start believing it is reading
       its own run (`09-b76`, the box above `righe_registro`)."""
    return B76.righe_registro()


def riga0_pulita(tetto=90.0):
    """⭐ The line from which to read THIS run, taken when the previous run has
       finished writing itself."""
    registro_posato(tetto=tetto)
    return righe_registro()


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE LOG — the clock, and the three lines this bench reads
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Log lines begin with `HH:MM:SS.mmm ` (`src/registro.c`), and
#    it is the only clock that is right for these numbers: it is the SERVER's.
#    ⚠ A stopwatch on the laptop would also measure the `ssh`, the container and
#      the difference between two clocks — on a 10 s threshold that is half
#      the error I am looking for.
_OROLOGIO = re.compile(r"^(\d\d):(\d\d):(\d\d)\.(\d\d\d)\s")


def t_registro(riga):
    """The seconds since midnight of a log line, or `None`.

    ⚠ It returns `None` and not `0` when there is no time: a zero here would mean
      «midnight» and would be a plausible and false number (`LEZIONI.md` §1.9).
    """
    m = _OROLOGIO.match(riga or "")
    if not m:
        return None
    return (int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
            + int(m.group(4)) / 1000.0)


def dt_registro(dopo, prima):
    """`dopo - prima` in seconds, with midnight stepped over.

    ⚠ It returns `None` if one of the two is missing: «I do not know» must not look
      the same as «zero seconds», which here would mean «it fired at once».
    """
    a, b = t_registro(dopo), t_registro(prima)
    if a is None or b is None:
        return None
    d = a - b
    return d + 86400.0 if d < -43200.0 else d


def leggi_registro(riga0, filtro, quante=400):
    """The lines of THIS run that contain `filtro` (a `grep -e … -e …`).

    ⛔ `tail -n +riga0+1` and not the whole log: the farewells, the firings and the
       denied slots of whoever ran before are not mine.
    """
    pezzi = " ".join("-e '%s'" % f for f in filtro)
    rc, out, _ = root("bash -c \"tail -n +%d %s/registro.log | grep -a %s | "
                      "tail -%d\"" % (riga0 + 1, LAV, pezzi, quante))
    return [r for r in out.splitlines() if r.strip()]


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE `linea-morta` LINE — a contract on the TEXT, and it is read as such
# ═══════════════════════════════════════════════════════════════════════════
#
# `src/webtransport.c`, `linea_morta_scatta()`, fixes the format as a contract:
#   1. the prefix `linea-morta` is STABLE and is the first word of the body;
#   2. the second field is the origin (IND:PORTA), without `=`;
#   3. every field is `nome=valore` with no spaces in the value;
#   4. ⛔ `giudizio=` IS THE LAST and runs to the end of the line, spaces included;
#   5. ⛔ the fields are ALWAYS ALL there, even those the cause does not use: what
#      says which one decided is `causa=`, which is the first.
#
# ⛔ The reduction stands apart because it is the one `--certifica` exercises on
#    MANUFACTURED lines: a contract on the text is tested on the text.
def riduci_linea_morta(righe, letto=True):
    """From the raw lines to the numbers of the FIRINGS.  ⛔ It does not judge: it reduces.

    ⛔⛔ And «zero firings» is NOT «I did not read», and it is the distinction on which
        all of test 1 depends: zero `linea-morta` lines is **the result
        test 1 expects**, while a log not read is a blind bench.
        ⇒ `letto` is stated by the caller, who knows whether the `grep` went
          well, and without it this function refuses.
    """
    if not letto:
        return {"esito": "⛔ NON HO LETTO IL REGISTRO — «zero firings» and «I did not "
                         "look» must not look the same"}
    righe = [r for r in righe if "linea-morta " in r]
    n = {"esito": "letto", "scatti": len(righe), "righe": []}
    for r in righe:
        corpo = r.split("linea-morta ", 1)[1]
        giud = ""
        if "giudizio=" in corpo:
            corpo, giud = corpo.split("giudizio=", 1)
        pezzi = corpo.split()
        d = {"provenienza": pezzi[0] if pezzi and "=" not in pezzi[0] else None}
        for p in pezzi:
            if "=" in p:
                k, v = p.split("=", 1)
                d[k] = v
        d["giudizio"] = giud.strip()
        d["ora"] = t_registro(r)
        d["riga"] = r
        n["righe"].append(d)
    if righe:
        p = n["righe"][0]

        def num(k):
            try:
                return int(p.get(k))
            except (TypeError, ValueError):
                return None

        n["causa"] = p.get("causa")
        # ⭐ The three numbers on which the stall is proved or disproved: how many
        #   frames the stage gave us, how many video bytes really went
        #   out, and how many stayed at home with us.
        n["stallo_ms"] = num("stallo_ms")
        n["soglia_stallo_ms"] = num("soglia_stallo_ms")
        n["offerti"] = num("offerti")
        n["usciti_byte"] = num("usciti_byte")
        n["coda_video"] = num("coda_video")
        n["cwnd_left"] = num("cwnd_left")
        # ⚠ And the WITNESS, which no longer judges: `permille` without `soglia_`.
        n["persi"] = num("persi")
        n["spediti"] = num("spediti")
        n["permille"] = num("permille")
        n["finestra_ms"] = num("finestra_ms")
        n["silenzio_ms"] = num("silenzio_ms")
        n["soglia_silenzio_ms"] = num("soglia_silenzio_ms")
        n["prove"] = num("prove")
        n["cwnd"] = num("cwnd")
        n["srtt_us"] = num("srtt_us")
        n["giudizio"] = p.get("giudizio", "")
        n["ora_primo"] = p.get("ora")
        n["cause"] = [x.get("causa") for x in n["righe"]]
    return n


def leggi_linea_morta(riga0):
    """The firings of THIS run, and the transport line that carries them out.

    ⚠ `DEAD LINE — the QUIC connection is closing` is read too: it is the half
      belonging to `trasporto.c`, and a decision taken without the wire dropping would
      be something other than what the user chose.
    """
    righe = leggi_registro(riga0, ["linea-morta ", "DEAD LINE"])
    n = riduci_linea_morta([r for r in righe if "linea-morta " in r], letto=True)
    n["chiuse_dal_trasporto"] = len([r for r in righe if "DEAD LINE" in r])
    return n


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE EVICTION — the three greppable marks, as `src/rcp.c` declares them
# ═══════════════════════════════════════════════════════════════════════════
def riduci_sfratto(righe, letto=True):
    """`EVICTION for silence:` · `⛔ EVICTION DENIED:` · `slot DENIED`.

    ⛔ Here too «zero» is not «I did not read» — see `riduci_linea_morta`.
    """
    if not letto:
        return {"esito": "⛔ NON HO LETTO IL REGISTRO"}
    sfratti = [r for r in righe if "EVICTION for silence:" in r]
    negati = [r for r in righe if "EVICTION DENIED:" in r]
    rifiuti = [r for r in righe if "slot DENIED" in r]
    presi = [r for r in righe if "slot TAKEN" in r]
    n = {"esito": "letto", "sfratti": len(sfratti), "negati": len(negati),
         "rifiuti": len(rifiuti), "presi": len(presi),
         "righe_sfratto": sfratti[:4], "righe_negato": negati[:4],
         "righe_rifiuto": rifiuti[:4], "righe_preso": presi[:4]}
    if sfratti:
        m = re.search(r"EVICTION for silence: (\d+) ms", sfratti[0])
        n["muto_ms"] = int(m.group(1)) if m else None
        n["ora_sfratto"] = t_registro(sfratti[0])
        # ⭐ Who was evicted: it serves test 5, where evicting the wrong
        #    user would not be a convenience but a security hole.
        m = re.search(r"the slot of (\S+) goes to the client", sfratti[0])
        n["sfrattato"] = m.group(1) if m else None
    # ⭐ The silence declared inside the REFUSAL line: it is the number that
    #    whoever reads the log was missing to know whether the slot belonged to a live
    #    client or a corpse, and it comes out even with the eviction OFF.
    if rifiuti:
        m = re.search(r"sign of life (\d+) ms ago", rifiuti[-1])
        n["ultimo_rifiuto_muto_ms"] = int(m.group(1)) if m else None
        n["sfratto_dice"] = ("SPENTO" if "is switched OFF" in rifiuti[-1]
                             else "NON e' scattato" if "did NOT fire" in rifiuti[-1]
                             else None)
    # ⛔ Who took the slot LAST, and at what time: it is the number of
    #    test 4 — «at which second it gets in», and on the server's clock.
    if presi:
        m = re.search(r"slot TAKEN by (\S+)", presi[-1])
        n["ultimo_preso_da"] = m.group(1) if m else None
        n["ora_ultimo_preso"] = t_registro(presi[-1])
    return n


def leggi_sfratto(riga0):
    righe = leggi_registro(riga0, ["EVICTION", "slot DENIED", "slot TAKEN"])
    return riduci_sfratto(righe, letto=True)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE **DECLARED** FRACTION, rebuilt from the `rete-quic` lines
# ═══════════════════════════════════════════════════════════════════════════
#
# ⇒ It is the falsifier of test 1 (⇒ the box at the top).  The
#   `rete-quic` lines carry `da_ms`, `persi_d` and `spediti_d`, which are exactly the
#   three numbers with which `linea_morta_giudica()` decides.  ⇒ ITS
#   guards are applied and we count whether two windows in a row would ever have broken the threshold.
#
# ⚠ `[?]` The approximation is declared and sits on the wrong cautious side: the
#   `rete-quic` lines are silent when nothing has changed, so one of their
#   windows can be longer than a second — and averaging over more time
#   LOWERS the peak.  ⇒ On its own it does not close the question: next to it goes the
#   calibration at `--linea-morta-permille 1`, which makes the product print the
#   `permille=` it computed itself.
def finestre_dichiarate(righe, soglia_permille=PERMILLE_DIAGNOSI):
    """From the `rete-quic` lines to the dead line's judgement windows."""
    righe = [r for r in righe if "rete-quic " in r]
    if not righe:
        return {"esito": "NIENTE DA LEGGERE — no «rete-quic» line in this "
                         "run (⚠ binary older than 23 Aug 2026?)"}
    valide, tutte = [], []
    for r in righe:
        corpo = r.split("rete-quic ", 1)[1].split("giudizio=", 1)[0]
        d = dict(p.split("=", 1) for p in corpo.split() if "=" in p)
        try:
            da, persi, sped = (int(d["da_ms"]), int(d["persi_d"]),
                               int(d["spediti_d"]))
        except (KeyError, ValueError):
            continue
        pm = (persi * 1000 // sped) if sped else None
        tutte.append({"da_ms": da, "persi_d": persi, "spediti_d": sped,
                      "permille": pm})
        # ⛔ The cure's two guards, to the letter: below the minimum number of
        #    packets nothing is decided, and the window must be at least
        #    the minimum one.
        if sped >= LM_MIN_PACCHETTI and da >= LM_FINESTRA_MS:
            valide.append(pm)
    n = {"esito": "letto", "righe": len(tutte), "finestre_valide": len(valide)}
    if not valide:
        n["esito"] = ("NON GIUDICO — no window passed the cure's "
                      "guards (%d packets sent, %d ms): over %d "
                      "`rete-quic` lines the cure would NEVER have decided anything"
                      % (LM_MIN_PACCHETTI, LM_FINESTRA_MS, len(tutte)))
        return n
    ordinate = sorted(valide)
    n["permille_max"] = ordinate[-1]
    n["permille_p95"] = ordinate[int(0.95 * (len(ordinate) - 1))]
    n["permille_mediano"] = ordinate[len(ordinate) // 2]
    n["permille_medio"] = round(sum(valide) / float(len(valide)), 2)
    n["sopra_soglia"] = len([x for x in valide if x >= soglia_permille])
    # ⚠ Two IN A ROW was the firing condition of the OLD cure; it stays here
    #    because it is the count with which the refutation was written, and it serves to
    #    compare with that run.  ⛔ It is no longer the condition of anything.
    fila, massima, coppie = 0, 0, 0
    for x in valide:
        if x >= soglia_permille:
            fila += 1
            massima = max(massima, fila)
            if fila >= FINESTRE_DIAGNOSI:
                coppie += 1
        else:
            fila = 0
    n["fila_massima_sopra_soglia"] = massima
    n["coppie_sopra_soglia"] = coppie
    n["soglia_permille"] = soglia_permille
    # ⭐⭐ AND THE QUESTION THE FIRST RUN GAVE RISE TO: is the high fraction
    #    only the connection START-UP, or does it last the whole session?
    #    `[M]` 23 Aug 2026: the cure fired at the fourth second, inside the
    #    first windows — when `cwnd` is still opening and every packet
    #    that overtakes is worth, proportionally, much more.
    # ⇒ The two halves are counted apart: if the tail is low and only the start is
    #   high, the defect is not the THRESHOLD, it is the MOMENT at which one judges.
    primi = valide[:PRIME_FINESTRE]
    dopo = valide[PRIME_FINESTRE:]
    n["prime_finestre"] = len(primi)
    n["permille_max_prime"] = max(primi) if primi else None
    n["permille_max_dopo"] = max(dopo) if dopo else None
    n["permille_mediano_dopo"] = (sorted(dopo)[len(dopo) // 2] if dopo else None)
    n["sopra_soglia_dopo"] = len([x for x in dopo if x >= soglia_permille])
    fila, massima_d, coppie_d = 0, 0, 0
    for x in dopo:
        if x >= soglia_permille:
            fila += 1
            massima_d = max(massima_d, fila)
            if fila >= FINESTRE_DIAGNOSI:
                coppie_d += 1
        else:
            fila = 0
    n["fila_massima_dopo"] = massima_d
    n["coppie_sopra_soglia_dopo"] = coppie_d
    # ⭐ And the CUMULATIVE one, which is another quantity and must be stated alongside: it is the
    #    fraction over the whole session, not over one window.
    tot_p = sum(x["persi_d"] for x in tutte)
    tot_s = sum(x["spediti_d"] for x in tutte)
    n["cumulativa_permille"] = round(1000.0 * tot_p / tot_s, 2) if tot_s else None
    n["persi_totali"] = tot_p
    n["spediti_totali"] = tot_s
    return n


def leggi_finestre(riga0, soglia_permille=PERMILLE_DIAGNOSI):
    righe = leggi_registro(riga0, ["rete-quic "], quante=2000)
    return finestre_dichiarate(righe, soglia_permille)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE WIRE CLOCK — «how much does a still session really cost?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ It runs ON THE MACHINE and reads the `netem` counters, not a `tcpdump`: it is
#    the same counter `09-b76` uses for the qdisc, and reading it from here
#    would cost one `ssh` round per sample — that is 200 ms of error on a
#    measurement that must tell 5 s from 10 s.
OROLOGIO = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09-b81-orologio — the netem counters sampled ON THE SPOT.

⛔ It neither reduces nor judges: it prints the samples.  The reduction lives in the bench, and
   it is the one the positive control exercises on manufactured samples.
"""
import json, re, subprocess, sys, time

def principale():
    dev, secondi, passo = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    campioni = []
    t0 = time.monotonic()
    while time.monotonic() - t0 < secondi:
        out = subprocess.run(["/usr/sbin/tc", "-s", "qdisc", "show", "dev", dev],
                             capture_output=True).stdout.decode("utf-8", "replace")
        pezzi = out.split("qdisc netem 40:")
        if len(pezzi) > 1:
            m = re.search(r"Sent (\d+) bytes (\d+) pkt", pezzi[1])
            if m:
                campioni.append([round(time.monotonic() - t0, 3),
                                 int(m.group(1)), int(m.group(2))])
        time.sleep(passo)
    print(json.dumps({"campioni": campioni}))

if __name__ == "__main__":
    principale()
'''


def riduci_orologio(campioni, quiete_s=0.6):
    """From the counter samples to the numbers of the TRAFFIC AT REST.

    · **kbit_s** and **pacchetti_s** — what a still session REALLY costs;
    · **eventi** — the groups of samples in which the counter rose, separated
      by at least `quiete_s` of silence: ⭐ it is the way to see the PINGs without a
      `tcpdump`, because on a still line a PING and its acknowledgement are
      the only thing that moves the counter;
    · **intervallo_mediano_s** — the period between two events, and it is the number that
      says whether the PINGs went from 10 s to 5.

    ⛔ It does not judge: it reduces.  ⚠ And if the counter NEVER stops, the events
      are only one and the interval is `None` — which means «this session
      is not still», not «zero seconds».
    """
    n = {"campioni": len(campioni or [])}
    if not campioni or len(campioni) < 3:
        n["esito"] = ("NON GIUDICO — %d samples: without at least three there is no "
                      "interval to measure" % len(campioni or []))
        return n
    t0, b0, p0 = campioni[0]
    t1, b1, p1 = campioni[-1]
    durata = t1 - t0
    if durata <= 0:
        n["esito"] = "NON GIUDICO — the window of the samples is zero long"
        return n
    n["esito"] = "misurato"
    n["secondi"] = round(durata, 2)
    n["byte"] = b1 - b0
    n["pacchetti"] = p1 - p0
    n["kbit_s"] = round(8.0 * (b1 - b0) / durata / 1000.0, 4)
    n["pacchetti_s"] = round((p1 - p0) / durata, 3)
    eventi, prec_t, prec_p, aperto = [], t0, p0, None
    for t, b, p in campioni[1:]:
        if p > prec_p:
            if aperto is None:
                aperto = t
            prec_t = t
        elif aperto is not None and t - prec_t >= quiete_s:
            eventi.append([round(aperto, 3), round(prec_t, 3),
                           p - _pkt_a(campioni, aperto)])
            aperto = None
        prec_p = p
    if aperto is not None:
        eventi.append([round(aperto, 3), round(prec_t, 3), None])
    n["eventi"] = len(eventi)
    n["eventi_primi"] = eventi[:6]
    if len(eventi) >= 2:
        inter = [round(eventi[i][0] - eventi[i - 1][0], 3)
                 for i in range(1, len(eventi))]
        inter_ord = sorted(inter)
        n["intervalli_s"] = inter[:12]
        n["intervallo_mediano_s"] = inter_ord[len(inter_ord) // 2]
        n["intervallo_min_s"] = inter_ord[0]
        n["intervallo_max_s"] = inter_ord[-1]
        # ⭐ The bytes per round: the count the PING box declares at ~130 B.
        n["byte_per_evento"] = round((b1 - b0) / float(len(eventi)), 1)
    else:
        n["intervallo_mediano_s"] = None
        n["perche_niente_intervallo"] = (
            "the counter never stopped for %.1f s in a row: this "
            "session is NOT still, and an interval between two events does not exist"
            % quiete_s)
    return n


def _pkt_a(campioni, t):
    for x in campioni:
        if x[0] >= t:
            return x[2]
    return campioni[-1][2]


def orologio_gira(secondi=60.0, passo=0.1):
    rc, out, err = root("python3 %s/09-b81-orologio.py %s %g %g"
                        % (LAV, DEV, secondi, passo), int(secondi) + 120)
    try:
        d = json.loads(out)
    except Exception as e:
        _dub("the clock did not answer: %s — %s" % (e, (out + err)[-200:]))
        return {"esito": "NON GIUDICO — the wire clock did not answer"}
    return riduci_orologio(d.get("campioni") or [])


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE STATE OF THE TWO CURES — it is REREAD from the startup line, not assumed
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔⛔ IT IS THE GUARD ALL OF TEST 1 DEPENDS ON.  «Zero firings» holds only if
#     the cure was ON: with the cure off zero firings is yesterday's
#     behaviour, and calling it «no false positive» would mean declaring
#     proven a cure that did not even run — ⚠ and with an option typed by
#     hand inside three levels of `ssh` and `systemd-run` it is not a theoretical
#     hypothesis.
#
# ⭐ And it can be done only because `main.c` calls `wt_linea_morta()` ALWAYS, and
#    `rcp_sfratto()` prints itself on AND off: the startup line comes out in both
#    cases by construction, and it is half the value of the two cures.
def stato_delle_cure():
    """What the server says about itself, at the LAST startup."""
    rc, out, _ = root("bash -c \"grep -a -n -e 'DEAD LINE is' -e 'ghost "
                      "eviction: threshold' %s/registro.log | tail -6\"" % LAV)
    righe = [r for r in out.splitlines() if r.strip()]
    n = {"esito": "letto" if righe else "⛔ NON HO LETTO any startup line "
                                        "of the two cures",
         "linea_morta": None, "stallo_ms": None, "silenzio_s": None,
         "sfratto_ms": None, "righe": righe[-2:]}
    for r in righe:
        if "DEAD LINE is ON" in r:
            n["linea_morta"] = "accesa"
            m = re.search(r"\(1\) STALL: (\d+) ms", r)
            n["stallo_ms"] = int(m.group(1)) if m else None
            m = re.search(r"\(2\) SILENCE: (\d+) s", r)
            n["silenzio_s"] = int(m.group(1)) if m else None
        elif "DEAD LINE is OFF" in r:
            n["linea_morta"] = "spenta"
            n["stallo_ms"], n["silenzio_s"] = None, None
        if "ghost eviction: threshold" in r:
            m = re.search(r"threshold (\d+) ms", r)
            n["sfratto_ms"] = int(m.group(1)) if m else None
    return n


def cure_come_voglio(stato, linea_morta=None, stallo_ms=None, silenzio_s=None,
                     sfratto_ms=None):
    """(va_bene, perche') — is the server configured as this test demands?

    ⛔ Called BEFORE every test: a predicate running on a configuration
       other than the one it believes does not give red, it gives a plausible number.
    """
    if stato.get("esito") != "letto":
        return _muto(stato.get("esito"))
    guai = []
    if linea_morta is not None and stato["linea_morta"] != linea_morta:
        guai.append("the dead line is «%s» and I wanted it «%s»"
                    % (stato["linea_morta"], linea_morta))
    if stallo_ms is not None and stato["stallo_ms"] != stallo_ms:
        guai.append("the STALL threshold is %s ms and I wanted %d"
                    % (stato["stallo_ms"], stallo_ms))
    if silenzio_s is not None and stato["silenzio_s"] != silenzio_s:
        guai.append("the silence threshold is %s s and I wanted %d"
                    % (stato["silenzio_s"], silenzio_s))
    if sfratto_ms is not None and stato["sfratto_ms"] != sfratto_ms:
        guai.append("the eviction is at %s ms and I wanted it at %d"
                    % (stato["sfratto_ms"], sfratto_ms))
    if guai:
        return _muto("⛔ I DO NOT MEASURE: the server is not configured as this "
                     "test demands — " + " · ".join(guai))
    return _si("the server says of itself: dead line %s (stall %s ms, silence "
               "%s s) · eviction %s ms"
               % (stato["linea_morta"], stato["stallo_ms"], stato["silenzio_s"],
                  stato["sfratto_ms"]))


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE SIX PREDICATES, WRITTEN FIRST — «(numbers) -> (passa, perche')»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `PIANO.md` §0.3.4: a bench that cannot see the defect it looks for has no
#    right to green.  ⇒ Each of these can give GREEN, RED and MUTE, and
#    `--certifica` proves it on manufactured numbers.  A predicate never seen
#    failing is not a predicate.

def p1_niente_falso_positivo(lm, testimoni, n, minuti):
    """⛔⛔ **THE TEST THAT CAN MAKE THE CURE BE WITHDRAWN.**

    On `casa-cattiva` — the line that HOLDS — the dead line when on must not
    fire EVEN ONCE in ten minutes.  A firing here means
    throwing out someone who was working, and it is the error that cannot be undone.

    ⚠ And the green holds only if the line really held: if the session did not
      open, or dropped for other reasons, or the rate is below `FPS_LINEA_CHE_REGGE`
      (5.0 frames/s), here there was no user at work NOT to throw
      out — and then this predicate KEEPS QUIET instead of giving a green it has not
      earned.
    """
    if not lm or lm.get("esito") != "letto":
        return _muto((lm or {}).get("esito", "I did not read the firings"))
    if lm["scatti"] > 0:
        p = lm["righe"][0]
        return _no("⛔⛔ FALSE POSITIVE: the dead line fired %d time(s) "
                   "in %g minutes on a line the product was serving — "
                   "causa=%s stallo_ms=%s (threshold %s) offerti=%s "
                   "usciti_byte=%s coda_video=%s · witness of the reordering: "
                   "permille=%s.  ⇒ Switching it on would mean throwing out a "
                   "user at work: THE CURE IS NOT SWITCHED ON"
                   % (lm["scatti"], minuti, p.get("causa"), p.get("stallo_ms"),
                      p.get("soglia_stallo_ms"), p.get("offerti"),
                      p.get("usciti_byte"), p.get("coda_video"),
                      p.get("permille")))
    if not testimoni:
        return _muto("no firing, but I did not question the witnesses of the "
                     "connection: without them, I do not know whether there was a user at "
                     "work not to throw out")
    if testimoni.get("aperta") is False:
        return _muto("⚠ no firing, but the session does not appear to have "
                     "OPENED: «it never opened» looks the same as «nothing "
                     "fired», and it is not the same thing")
    if testimoni.get("cliente_staccato"):
        return _muto("⚠ no firing of the dead line, but the client "
                     "dropped anyway: «%s» — the line did not hold, and this "
                     "test proved nothing"
                     % (testimoni.get("caduta") or "")[:140])
    fps = (n or {}).get("fps")
    if fps is None:
        return _muto("no firing, but I do not have the delivered rate: without it, "
                     "I do not know whether the line held")
    if fps < FPS_LINEA_CHE_REGGE:
        return _muto("⚠ ZERO firings, but the rate is %.2f frames/s (below "
                     "%.1f): this line was not serving anyone, and not "
                     "having thrown anyone out is no merit"
                     % (fps, FPS_LINEA_CHE_REGGE))
    c = (n or {}).get("consegna") or {}
    return _si("⭐ ZERO firings in %g minutes on a line that HOLDS: %.2f "
               "frames/s, coverage %s, ⭐ longest gap **%s s** "
               "(the quantity the threshold is derived from), client still "
               "attached and no farewell in the log"
               % (minuti, fps, c.get("copertura"), c.get("buco_max_s")))


def p1c_la_linea_regge_a_cura_spenta(testimoni, n, minuti, scatti_accesa):
    """⛔⛔ **THE CONTROL OF TEST 1, AND WITHOUT IT ITS RED DOES NOT COUNT.**

    When the cure fires, the session DIES — and from a run in which the session
    died at 4 s one cannot say whether the line was holding: «the cure threw out
    someone who was working» and «the line was finished anyway» look the same.
    ⚠ It is the form of `LEZIONI.md` §1.9 applied to a judgement instead of a
      number.

    ⇒ Same line, same duration, **cures OFF**: if the session holds all the
      minutes at more than `FPS_LINEA_CHE_REGGE` frames per second, then the
      difference between the two runs is **a switch**, and what the cure
      threw out was a user at work.  If instead it does not hold even with the cure
      off, this predicate gives RED — because then the red of test 1
      is not a false positive, and the bench must say so.
    """
    if not testimoni:
        return _muto("I did not question the witnesses of the connection")
    if testimoni.get("aperta") is False:
        return _muto("the session does not appear to have opened: the question belongs to "
                     "`09-b78-apertura.py`, and I do not judge")
    if testimoni.get("cliente_staccato"):
        return _no("⛔ WITH THE CURE OFF THE SESSION DROPPED ANYWAY: «%s» — "
                   "so the firing of test 1 is not a false positive, and "
                   "this line is not the one that HOLDS"
                   % (testimoni.get("caduta") or "")[:160])
    fps = (n or {}).get("fps")
    c = (n or {}).get("consegna") or {}
    if fps is None or c.get("esito") != "misurato":
        return _muto("I do not have the rate or the delivery of this run: without them, I cannot "
                     "say the line held")
    coda = ("%.2f frames/s · coverage %.2f · longest gap %.2f s · "
            "last frame at %.2f s over %g minutes"
            % (fps, c["copertura"], c["buco_max_s"], c["consegna_fino_a_s"],
               minuti))
    if fps < FPS_LINEA_CHE_REGGE:
        return _no("⛔ with the cure off the line gives %.2f frames/s (below %.1f): "
                   "it was not serving anyone even like this, and the firing of "
                   "test 1 cannot be called a false positive.  %s"
                   % (fps, FPS_LINEA_CHE_REGGE, coda))
    if c["copertura"] < B76.COPERTURA_MINIMA:
        return _no("⛔ with the cure off the delivery stopped anyway "
                   "(coverage %.2f < %.2f): %s"
                   % (c["copertura"], B76.COPERTURA_MINIMA, coda))
    return _si("⭐ WITH THE CURE OFF THE SAME LINE HOLDS %g whole minutes: %s — "
               "⇒ between the two runs ONE SWITCH changes, and with it on the "
               "session was closed %d time(s).  What the cure throws "
               "out is a user at work" % (minuti, coda, scatti_accesa))


def p1b_il_margine_dello_stallo(scala, soglia_ms, nome):
    """⭐⭐ **THE TRUE MARGIN, and not «it did not fire».**

    ⛔ The `linea-morta` line comes out ONLY on firing: from a run in which the cure does not
       fire one cannot read **by how much** it did not fire — and a green without that
       number does not say whether the margin is tenfold or three per cent.
       ⚠ It is the same form as the defect this bench has already paid for: «nothing
         happened» passing itself off as a measurement.

    ⇒ The same profile is rerun with LOWER and lower thresholds, until one
      fires.  Then the line comes out and carries a `stallo_ms` **measured by the
      product**, with its own arithmetic.  Between the lowest threshold that does NOT fire
      and the stall the product printed, the maximum is pinned.

    Green if the margin (threshold / maximum observed stall) sits above %.1f×.
    ⛔ Red if it drops below: below that point the threshold begins to look like
       a lucky number, and erring low means throwing out someone who
       was working.
    """ % MARGINE_STALLO_MINIMO
    if not scala:
        return _muto("I did not try any lower threshold: without the scale "
                     "I have no margin, only «it did not fire»")
    scattate = [x for x in scala if x.get("scattata")]
    non_scattate = [x for x in scala if x.get("scattata") is False]
    if not scattate and not non_scattate:
        return _muto("no step of the scale gave a readable outcome")
    # ⛔ A firing at the TRUE threshold (or above) is not a narrow margin: it is the
    #    false positive, and P1 judges it.  Here we keep quiet, or I would say the
    #    same thing twice with two different words.
    if any(x["soglia_ms"] >= soglia_ms for x in scattate):
        return _muto("⚠ the cure already fired at the threshold in force (%d ms): "
                     "there is no margin to measure, and P1 states the "
                     "fact" % soglia_ms)
    if not scattate:
        piu_bassa = min(x["soglia_ms"] for x in non_scattate)
        margine = soglia_ms / float(piu_bassa)
        coda = ("not even at %d ms — the scale tried is %s"
                % (piu_bassa, [x["soglia_ms"] for x in scala]))
        if margine < MARGINE_STALLO_MINIMO:
            return _muto("⚠ it did not fire at any of the thresholds tried, but "
                         "the lowest (%d ms) gives only %.1f× of margin: to "
                         "say the margin is ≥ %.1f× one must go further "
                         "down" % (piu_bassa, margine, MARGINE_STALLO_MINIMO))
        return _si("⭐ «%s»: the maximum stall sits BELOW %d ms — the cure does not "
                   "fire %s ⇒ the margin of the threshold (%d ms) is **more than "
                   "%.1f×**" % (nome, piu_bassa, coda, soglia_ms, margine))
    # ⭐ There is at least one firing below the true threshold: that is a `stallo_ms`
    #   MEASURED, and it is the best number one can have.
    peggiore = max(x.get("stallo_ms") or 0 for x in scattate)
    if not peggiore:
        return _muto("the cure fired but the line does not carry `stallo_ms`: the "
                     "contract on the text does not hold, and I do not have the number")
    margine = soglia_ms / float(peggiore)
    coda = ("maximum stall MEASURED %d ms (at threshold %d ms) · threshold in force "
            "%d ms · scale tried %s"
            % (peggiore, min(x["soglia_ms"] for x in scattate), soglia_ms,
               [(x["soglia_ms"], x.get("stallo_ms")) for x in scala]))
    if margine < MARGINE_STALLO_MINIMO:
        return _no("⛔ THE MARGIN IS NARROW on a line that HOLDS: %.2f× "
                   "(minimum %.1f×) — %s.  ⇒ The threshold sits too close to a "
                   "stall that a good line produces on its own, and erring "
                   "low means throwing out someone who is working"
                   % (margine, MARGINE_STALLO_MINIMO, coda))
    return _si("⭐ «%s»: the margin is **%.1f×** — %s" % (nome, margine, coda))


def p_non_deve_scattare(nome, lm, testimoni, n, minuti, atteso):
    """⛔ **THIS LINE HOLDS, AND MUST NOT BE DECLARED DEAD.**  It is the general
    form of test 1, applied to any profile of the grid of
    `09-b76` — it serves `raffica-1`, which is the case the narrow
    side of the threshold rests on: `[M]` it delivers 23.94 frames/s and still had
    **a whole empty second**.

    ⚠ The green holds only if the line really held: outside the grid
      this predicate KEEPS QUIET, instead of giving a green it has not earned.
    """
    if not lm or lm.get("esito") != "letto":
        return _muto((lm or {}).get("esito", "I did not read the firings"))
    if lm["scatti"] > 0:
        p = lm["righe"][0]
        return _no("⛔⛔ «%s» was declared DEAD, and it HOLDS: causa=%s "
                   "stallo_ms=%s (threshold %s) offerti=%s usciti_byte=%s "
                   "coda_video=%s — %s"
                   % (nome, p.get("causa"), p.get("stallo_ms"),
                      p.get("soglia_stallo_ms"), p.get("offerti"),
                      p.get("usciti_byte"), p.get("coda_video"),
                      atteso.get("perche", "")))
    if not testimoni or testimoni.get("aperta") is False:
        return _muto("no firing, but I have no witnesses that the session "
                     "opened")
    if testimoni.get("cliente_staccato"):
        return _muto("⚠ no firing of the dead line, but the client "
                     "dropped anyway: «%s»"
                     % (testimoni.get("caduta") or "")[:140])
    fps = (n or {}).get("fps")
    c = (n or {}).get("consegna") or {}
    if fps is None or c.get("esito") != "misurato":
        return _muto("no firing, but I have no rate and delivery: without them, I do not know "
                     "whether the line held")
    coda = ("%.2f frames/s · coverage %.2f · ⭐ longest gap **%.2f s**"
            % (fps, c["copertura"], c["buco_max_s"]))
    if not (atteso["fps_min"] <= fps <= atteso["fps_max"]):
        return _muto("⚠ ZERO firings, but «%s» gave %.2f frames/s, outside "
                     "the grid of 09-b76 (%.1f-%.1f): it is not the case I "
                     "believe I tested — %s"
                     % (nome, fps, atteso["fps_min"], atteso["fps_max"], coda))
    if c["copertura"] < atteso["copertura_min"]:
        return _muto("⚠ ZERO firings, but the coverage is %.2f against %.2f of the "
                     "grid: this line was not serving anyone — %s"
                     % (c["copertura"], atteso["copertura_min"], coda))
    return _si("⭐ ZERO firings in %g minutes on «%s», which HOLDS: %s (grid "
               "09-b76: %s)" % (minuti, nome, coda, atteso["perche"]))


def p_scena_ferma_non_scatta(lm, testimoni, secondi, soglia_ms):
    """⛔⛔ **THE WORST WAY IN WHICH THIS CURE COULD FAIL.**

    `[M]` in this phase the still scene delivers **one frame in 30 s and then
    zero**: Mutter's `RecordVirtual` delivers only on CHANGE, and waking up
    costs 13 ms.  ⇒ A still desktop is a desktop that sends nothing **and has
    nothing to send**, and it is exactly the normal case of someone
    reading a page.

    ⛔ If the stall count started there, the cure would throw out **whoever
       looks at a still desktop** — and not with a delay, with certainty: after
       `soglia` seconds, every time.  ⇒ Zero firings, and it must be tested on purpose
       instead of hoped for.

    ⭐ And it is tested holding the knife by the handle: the same still scene with
       a threshold MUCH lower than the one in force.  If the count does not start,
       it does not start at any threshold; if it did start, with the low threshold one sees it
       at once instead of in five seconds.
    """
    if not lm or lm.get("esito") != "letto":
        return _muto((lm or {}).get("esito", "I did not read the firings"))
    if lm["scatti"] > 0:
        p = lm["righe"][0]
        return _no("⛔⛔ THE STILL SCENE WAS DECLARED DEAD — the cure "
                   "throws out whoever looks at a desktop that does not change: causa=%s "
                   "stallo_ms=%s (threshold %s) offerti=%s usciti_byte=%s "
                   "coda_video=%s.  ⚠ If `offerti` and `coda_video` are ZERO, the "
                   "count started without there being anything to send, and it is "
                   "precisely the half that was supposed to prevent it"
                   % (p.get("causa"), p.get("stallo_ms"),
                      p.get("soglia_stallo_ms"), p.get("offerti"),
                      p.get("usciti_byte"), p.get("coda_video")))
    if not testimoni or testimoni.get("aperta") is False:
        return _muto("no firing, but it does not appear that the session "
                     "opened: without that, I proved nothing")
    if testimoni.get("cliente_staccato"):
        return _muto("⚠ no firing of the dead line, but the client "
                     "dropped anyway: «%s» — it is not the case I wanted to test"
                     % (testimoni.get("caduta") or "")[:140])
    if testimoni.get("cliente_attaccato") is not True:
        return _muto("the client did not say «still attached»: I do not have the "
                     "witness I need")
    return _si("⭐ %g s of STILL SCENE with the stall threshold at **%d ms** "
               "(that is %.1f times narrower than the one in force): ZERO "
               "firings, and the client stayed attached to the end.  ⇒ The "
               "count does not start when there is nothing to send"
               % (secondi, soglia_ms, LM_STALLO_MS / float(soglia_ms or 1)))


def p2_scatta_sullo_stallo(lm, sonda, secondi_a_scatto):
    """**The real firing.**  On `raffica-forte` — `[M]` 11.10 % loss in
    bursts, `cwnd` median 8 948 B against 105 616 of the reference, delivery
    that stops — the cure MUST fire, and with `causa=perdita`.

    ⚠ If the probe says the fault was not put in place, here we KEEP QUIET: measuring
      a profile that does not exist is worse than not measuring it, because the number is
      true and the cause is made up.
    """
    if not sonda or sonda.get("esito") != "misurato":
        return _muto("the probe did not measure: without it, I do not know whether the burst was "
                     "put in place, and a firing without a fault is not a firing")
    if sonda["persi_pc"] < 5.0:
        return _muto("⚠ the probe saw %.2f %% loss: it is not "
                     "`raffica-forte` (`[M]` 11.10 %%), and I do not judge a "
                     "profile that does not exist" % sonda["persi_pc"])
    if not lm or lm.get("esito") != "letto":
        return _muto((lm or {}).get("esito", "I did not read the firings"))
    if lm["scatti"] == 0:
        return _no("⛔ the cure did NOT fire on a line the product cannot "
                   "serve: the probe saw %.2f %% in bursts of "
                   "%.2f, and `[M]` at this loss the image either freezes "
                   "(14.26 s out of 25) or arrives 4.5 s late"
                   % (sonda["persi_pc"], sonda["raffica_media"]))
    if lm.get("causa") != "stallo":
        return _no("⛔ it fired, but for the WRONG reason: causa=%s on a "
                   "line that loses %.2f %% and on which the image STOPS — "
                   "a silence of the client is not an output stall, and the "
                   "two causes send one looking for the cause in two different places"
                   % (lm.get("causa"), sonda["persi_pc"]))
    if lm.get("chiuse_dal_trasporto", 0) < 1:
        return _no("⛔ the decision was taken (`linea-morta` line) but the "
                   "wire did NOT drop: the `trasporto.c` line «DEAD "
                   "LINE — the QUIC connection is closing» is missing.  ⚠ The user "
                   "chose that the wire drops, not that the server writes it")
    return _si("⭐ fired %s s after the slot was taken: causa=stallo "
               "stallo_ms=%s (threshold %s) offerti=%s usciti_byte=%s "
               "coda_video=%s cwnd=%s cwnd_left=%s srtt_us=%s · the wire "
               "dropped (%d line(s) of `trasporto.c`) · the probe: %.2f %% in "
               "bursts of %.2f · ⚠ the WITNESS of the reordering said "
               "permille=%s (and decided nothing)"
               % (("%.2f" % secondi_a_scatto) if secondi_a_scatto is not None
                  else "?", lm.get("stallo_ms"), lm.get("soglia_stallo_ms"),
                  lm.get("offerti"), lm.get("usciti_byte"),
                  lm.get("coda_video"), lm.get("cwnd"), lm.get("cwnd_left"),
                  lm.get("srtt_us"), lm.get("chiuse_dal_trasporto", 0),
                  sonda["persi_pc"], sonda["raffica_media"],
                  lm.get("permille")))


def p3_scatta_sul_silenzio(lm, soglia_ms):
    """**Silence.**  Client killed with `kill -9` — that is a goodbye NEVER
    SAID, which for the server is identical to a lost goodbye — and the cure must
    fire with `causa=silenzio` at its threshold.

    ⛔ AND THE TWO DIRECTIONS DO NOT COST THE SAME, as for test 1: firing
       LATE means a few more seconds of ghost; firing BEFORE the
       threshold means throwing out a live client that was keeping quiet — ⇒ below
       the threshold it is red with no discount, above it %.1f s is granted (the judgement is
       taken once per second, and there is the pacer queue).
    """ % (TOLLERANZA_SILENZIO_MS / 1000.0)
    if not lm or lm.get("esito") != "letto":
        return _muto((lm or {}).get("esito", "I did not read the firings"))
    if lm["scatti"] == 0:
        return _no("⛔ the client died without saying goodbye and the cure did NOT "
                   "fire: the slot stays with a ghost until the 30 s of "
                   "§5.3, which is precisely what this cure was supposed to "
                   "remove")
    if lm.get("causa") != "silenzio":
        return _no("⛔ it fired with causa=%s and not «silenzio»: the client was "
                   "killed, and what the server must see is that no packet "
                   "comes back any more" % lm.get("causa"))
    s = lm.get("silenzio_ms")
    if s is None:
        return _muto("the line does not carry `silenzio_ms`: the contract on the text "
                     "does not hold, and I do not have the number to judge on")
    if s < soglia_ms:
        return _no("⛔⛔ FIRED BEFORE ITS THRESHOLD: %d ms of silence "
                   "against %d declared — a live and idle client would be "
                   "thrown out, and it is the regression already paid for on 16 "
                   "August 2026" % (s, soglia_ms))
    if s > soglia_ms + TOLLERANZA_SILENZIO_MS:
        return _no("⛔ fired at %d ms against %d declared (+%d of "
                   "tolerance): the number written and the one in force "
                   "diverge, and it is form E1"
                   % (s, soglia_ms, TOLLERANZA_SILENZIO_MS))
    if lm.get("chiuse_dal_trasporto", 0) < 1:
        return _no("⛔ the decision was taken but the wire did NOT drop: "
                   "the `trasporto.c` line is missing")
    return _si("⭐ fired at %d ms of silence (threshold %d) with causa=silenzio, "
               "prove=%s (minimum %s) — and the wire dropped"
               % (s, soglia_ms, lm.get("prove"), lm.get("minimo_prove")
                  or LM_MIN_PROVE))


def p3b_costo_dei_ping(acceso, spento, dichiarato=COSTO_PING_DICHIARATO_KBIT_S):
    """⚠ **THE DECLARED PRICE OF THE PINGs.**  The box of `webtransport.c`
    declares ~130 B per round every HALF of the threshold, that is **%.2f kbit/s** per
    session.  ⇒ The REAL traffic of a still session is measured, on and
    off, and the difference cannot exceed the declared cost — if it
    exceeds it, it is a number to correct.

    ⛔ AND THIS PREDICATE REFUSES WHEN THE NOISE IS BIGGER THAN THE
       TARGET, which is the only honest thing to do: a «green» obtained
       by measuring %.2f kbit/s inside a background a thousand times higher does not
       prove anything, and it would be form E1 in reverse.
    """ % (COSTO_PING_DICHIARATO_KBIT_S, COSTO_PING_DICHIARATO_KBIT_S)
    if not acceso or acceso.get("esito") != "misurato":
        return _muto("I did not measure the traffic with the cure ON")
    if not spento or spento.get("esito") != "misurato":
        return _muto("I did not measure the traffic with the cure OFF")
    delta = acceso["kbit_s"] - spento["kbit_s"]
    fondo = min(acceso["kbit_s"], spento["kbit_s"])
    coda = ("on %.3f kbit/s (%d packets in %.1f s) · off %.3f kbit/s "
            "(%d in %.1f s) · difference %+.3f kbit/s · declared %.2f"
            % (acceso["kbit_s"], acceso["pacchetti"], acceso["secondi"],
               spento["kbit_s"], spento["pacchetti"], spento["secondi"],
               delta, dichiarato))
    # ⛔ The background must be small compared with the target, or one is not
    #    measuring the target.  Ten times is generous and it is declared.
    if fondo > 10.0 * dichiarato:
        return _muto("⛔ NON GIUDICO — a «still» session of this product "
                     "is not still: it costs %.1f kbit/s, that is %d times the "
                     "declared cost of the PINGs (%.2f).  ⭐ It is the PCM audio of §4.3, "
                     "which CANNOT be turned off (`[M]` a CIAO without an audio codec "
                     "in common gets `0x09 NIENTE_IN_COMUNE`).  ⇒ Inside "
                     "this background the cost of the PINGs cannot be isolated, and a green "
                     "here would prove nothing.  %s"
                     % (fondo, int(fondo / dichiarato), dichiarato, coda))
    if delta > 2.0 * dichiarato:
        return _no("⛔ the PINGs cost more than declared: %s" % coda)
    return _si("the cost of the PINGs is within the declared one: %s" % coda)


def p4_lo_sfratto_libera_il_posto(sf, soglia_ms, secondi_a_entrare, riferimento_s):
    """**The eviction.**  Same user, client killed with `-9`, a second
    client asking for the slot.  `[M]` today it takes **30.5 s** and **11 refusals**;
    with `--sfratto-ms %d` the slot must be free again at **~%.0f s**.

    ⚠ And here too the direction counts: evicting TOO EARLY means taking the
      slot from a live and idle client, that is switching off I2 — so below the
      threshold it is red.
    """ % (SFRATTO_CONSIGLIATO_MS, SFRATTO_CONSIGLIATO_MS / 1000.0)
    if not sf or sf.get("esito") != "letto":
        return _muto((sf or {}).get("esito", "I did not read the log"))
    if secondi_a_entrare is None:
        return _muto("I do not have the time at which the slot was taken back: without it, "
                     "«it got in» and «it did not get in» look the same")
    if sf["sfratti"] == 0:
        return _no("⛔ no EVICTION: the slot became free again after %.2f s "
                   "with %d refusals, that is at the silence clock of §5.3 — "
                   "the cure did nothing"
                   % (secondi_a_entrare, sf["rifiuti"]))
    muto = sf.get("muto_ms")
    if muto is None:
        return _muto("the eviction line does not carry the milliseconds of "
                     "silence: the contract on the text does not hold")
    if muto < soglia_ms:
        return _no("⛔⛔ EVICTED BEFORE THE THRESHOLD: the occupant had been silent for %d "
                   "ms and the threshold is %d — a live and idle client (`[M]` the "
                   "keep-alive of a browser is silent for 15 s) would be thrown out, "
                   "and that switches off invariant I2" % (muto, soglia_ms))
    if secondi_a_entrare > (soglia_ms + TOLLERANZA_SFRATTO_MS) / 1000.0:
        return _no("⛔ the slot became free again after %.2f s with the threshold at "
                   "%.1f s (+%.1f of tolerance): the cure fired but did not "
                   "shorten what it was supposed to"
                   % (secondi_a_entrare, soglia_ms / 1000.0,
                      TOLLERANZA_SFRATTO_MS / 1000.0))
    guadagno = ("from %.1f s to %.2f s (%.0f %% less)"
                % (riferimento_s, secondi_a_entrare,
                   100.0 * (1.0 - secondi_a_entrare / riferimento_s))
                if riferimento_s else "without a reference measured in this run")
    return _si("⭐ the slot became free again after %.2f s with %d refusals — "
               "the occupant had been silent for %d ms (threshold %d), evicted «%s» · %s"
               % (secondi_a_entrare, sf["rifiuti"], muto, soglia_ms,
                  sf.get("sfrattato"), guadagno))


def p5_fra_utenti_diversi_non_si_sfratta(sf, entrato, utente_a, utente_b):
    """⛔ **THE CASE THAT MUST NOT BREAK.**  An eviction between different users would not
    be a convenience: it would be a security hole — anyone could make
    another person's desktop drop simply by knocking.

    ⇒ Two things together, and the first is the one that counts:
      a) NO eviction that takes the slot from the first user while the one asking
         is a DIFFERENT user;
      b) the second user gets in all the same, on THEIR OWN slot (`MAX_ATTACCATE`
         = 16): denying them entry would be a different and equally
         real defect.
    """
    if not sf or sf.get("esito") != "letto":
        return _muto((sf or {}).get("esito", "I did not read the log"))
    if sf["sfratti"] > 0:
        return _no("⛔⛔ SECURITY HOLE: there was an EVICTION while the one "
                   "asking for the slot was a DIFFERENT user — evicted «%s», "
                   "line: «%s»"
                   % (sf.get("sfrattato"), (sf.get("righe_sfratto") or [""])[0][:200]))
    if entrato is not True:
        return _muto("no eviction (and that is what I wanted), but «%s» does not "
                     "appear to have got in: without their entry I have not "
                     "proved that the first one's slot stayed theirs — I have only "
                     "proved that nothing happened" % utente_b)
    return _si("⭐ no eviction between «%s» and «%s», and the second user "
               "got in all the same on their own slot: %d slots taken, %d refusals"
               % (utente_a, utente_b, sf["presi"], sf["rifiuti"]))


def p5b_la_riga_del_negato(sf):
    """⚠ **AND DOES THE `⛔ EVICTION DENIED` LINE COME OUT?**  The prediction is written FIRST
    and goes the uncomfortable way: `[R]` 23 August 2026, reading `src/rcp.c`, **NO**.

    The slot registry is indexed BY NAME (`posto_occupato(utente)`),
    so `POSTO_OCCUPATO` already implies «same user» and two different users
    take two different slots: the branch with that line is NEVER walked.
    ⇒ Whoever wrote it declares so in its own comment — *«redundant by
    construction, not by design»*, and it serves the day the registry
    became the session table of a real server.

    ⛔ So this predicate does NOT give red if the line is missing: it would give red to
       correct code.  It gives red if the line COMES OUT, because then my
       reading was wrong and the branch is reachable — that is, there is a way to
       reach `POSTO_OCCUPATO` with two different names, and THAT must be looked at.
    """
    if not sf or sf.get("esito") != "letto":
        return _muto((sf or {}).get("esito", "I did not read the log"))
    if sf["negati"] > 0:
        return _no("⛔ the «EVICTION DENIED» line DID COME OUT, and `[R]` I had read "
                   "that it could not: it means one reaches POSTO_OCCUPATO "
                   "with two different names — «%s»"
                   % (sf.get("righe_negato") or [""])[0][:200])
    return _si("no «EVICTION DENIED» line, as predicted `[R]`: the slot registry "
               "is by NAME, so the branch is not reachable — the "
               "protection comes from the structure, and the explicit check stays "
               "as a net for the day the structure changes")


def p6_i_predefiniti_non_cambiano_niente(lm, sf, stato, n, nome_profilo):
    """⛔ **INVARIANT I6.**  Without `--linea-morta` and with `--sfratto-ms 0` —
    that is **as the product ships today** — everything must be identical to
    yesterday: no firing, no eviction, and the profile behaves as in the
    grid of `09-b76`.

    ⭐ And it is also the proof that the two cures are really OFF, not only
       written: two startup lines saying so, and zero firing lines.
    """
    va, perche = cure_come_voglio(stato, linea_morta="spenta", sfratto_ms=0)
    if va is not True:
        return _muto("⚠ I do not judge I6 on a configuration that is not the "
                     "default one — %s" % perche)
    if not lm or lm.get("esito") != "letto":
        return _muto((lm or {}).get("esito", "I did not read the firings"))
    if lm["scatti"] > 0 or lm.get("chiuse_dal_trasporto", 0) > 0:
        return _no("⛔ I6 VIOLATED: with the cure OFF %d `linea-morta` "
                   "lines and %d closures by the transport came out"
                   % (lm["scatti"], lm.get("chiuse_dal_trasporto", 0)))
    if not sf or sf.get("esito") != "letto":
        return _muto((sf or {}).get("esito", "I did not read the eviction"))
    if sf["sfratti"] > 0:
        return _no("⛔ I6 VIOLATED: with the eviction OFF there was an "
                   "eviction — «%s»" % (sf.get("righe_sfratto") or [""])[0][:180])
    atteso = GRIGLIA_B76.get(nome_profilo)
    if not atteso:
        return _si("no firing and no eviction with the cures off "
                   "(⚠ «%s» is not in the grid of 09-b76: nothing to "
                   "compare)" % nome_profilo)
    c = (n or {}).get("consegna") or {}
    fps = (n or {}).get("fps")
    if c.get("esito") != "misurato" or fps is None:
        return _muto("no firing and no eviction, but I do not have the numbers of the "
                     "run: without them, I cannot say it behaves as in the "
                     "grid of 09-b76")
    coda = ("%.2f frames/s · coverage %.2f · longest gap %.2f s "
            "(grid 09-b76: %s)"
            % (fps, c["copertura"], c["buco_max_s"], atteso["perche"]))
    if atteso.get("consegna_si_ferma"):
        # ⛔ On `raffica-forte` the grid says delivery STOPS: if here it
        #    did not stop, the product would have changed — it is a red for I6
        #    as much as a firing.
        ferma = (c["copertura"] < B76.COPERTURA_MINIMA
                 or c["buco_max_s"] >= B76.BUCO_SCHERMO_FERMO_S)
        if not ferma:
            return _no("⛔ I6: with the cures off «%s» does NOT behave as "
                       "in the grid of 09-b76 — there delivery stops, here "
                       "it does not.  %s" % (nome_profilo, coda))
        return _si("⭐ cures off: zero firings, zero evictions, and «%s» "
                   "behaves as in the grid — %s" % (nome_profilo, coda))
    if not (atteso["fps_min"] <= fps <= atteso["fps_max"]):
        return _no("⛔ I6: with the cures off «%s» gives %.2f frames/s, outside "
                   "the grid of 09-b76 (%.1f-%.1f).  %s"
                   % (nome_profilo, fps, atteso["fps_min"], atteso["fps_max"],
                      coda))
    if c["copertura"] < atteso["copertura_min"]:
        return _no("⛔ I6: with the cures off «%s» has coverage %.2f against %.2f "
                   "of the grid.  %s"
                   % (nome_profilo, c["copertura"], atteso["copertura_min"], coda))
    return _si("⭐ cures off: zero firings, zero evictions, and «%s» sits within the "
               "grid of 09-b76 — %s" % (nome_profilo, coda))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE POSITIVE CONTROL — «how does this bench know that it can see?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `PIANO.md` §0.3.4: *«a bench that cannot see the defect it looks for has no
#    right to green»*.  ⇒ Here lines and numbers are manufactured and we check that
#    the six predicates give what is written FIRST — green, red **and mute**.
#
# ⭐ And the cases do not pass ready-made numbers: they manufacture the TEXT OF THE LOG and
#    run it through the SAME reductions that run on the real runs.  A
#    deception living in the reduction would be seen.

# ⛔ The format is that of `src/webtransport.c`, `linea_morta_scatta()`, field
#    by field and IN ORDER: `_certifica_contratto()` rereads it from the source and
#    compares, so the day the product changes the line the bench says so
#    instead of reading the wrong field in silence.
# ⛔⛔ THE CONTRACT CHANGED ON 23 AUGUST 2026, and the two vanished fields are
#     declared instead of vanishing in silence:
#       · `soglia_permille=` — there is no longer any threshold on loss;
#       · `finestre=N/M`     — there are no longer bad windows to count in
#                              a row: the stall is a continuous duration.
#     ⭐ And five came in: `stallo_ms` `soglia_stallo_ms` `offerti`
#        `usciti_byte` `coda_video` (plus `cwnd_left`).
# ⛔ AND IT CHANGED AGAIN ON 25 AUGUST 2026 (phase 10 cures, c808342): seven
#    fields came in between `srtt_us` and `giudizio` — `fermo_ms` `giri_fermi`
#    `saltati` `ritmo_giu` `ritmo_arretrato` `ritmo_posti` `ritmo_scesi`.  This
#    bench reads none of them, but step 0 rereads the order and gave red until
#    they were written here too.
CAMPI_LM = ["causa", "stallo_ms", "soglia_stallo_ms", "offerti", "usciti_byte",
            "coda_video", "silenzio_ms", "soglia_silenzio_ms", "prove",
            "minimo_prove", "persi", "spediti", "permille", "finestra_ms",
            "minimo_pacchetti", "cwnd", "cwnd_left", "srtt_us", "fermo_ms",
            "giri_fermi", "saltati", "ritmo_giu", "ritmo_arretrato", "ritmo_posti",
            "ritmo_scesi", "giudizio"]


def _fab_lm(ora="21:14:02.123", causa="stallo", stallo_ms=5004,
            soglia_stallo=LM_STALLO_MS, offerti=41, usciti=0, coda_video=61240,
            silenzio_ms=1300, prove=9, persi=31, spediti=412, permille=75,
            finestra_ms=1004, cwnd=8948, cwnd_left=0, srtt_us=61230,
            giudizio="⛔ the line is DEAD: for too long no frame has gone out while "
                     "having some to send"):
    """A `linea-morta` line as the product writes it FROM TODAY, field by
       field and in order.  ⛔ `soglia_permille=` and `finestre=N/M` are no longer
       there: if they reappeared, `_certifica_contratto()` would give red.
       The seven fields of 25 Aug (`fermo_ms` … `ritmo_scesi`) are written with
       neutral values: no predicate of this bench reads them."""
    return ("%s wt      linea-morta [192.168.0.2]:50875 causa=%s stallo_ms=%d "
            "soglia_stallo_ms=%d offerti=%d usciti_byte=%d coda_video=%d "
            "silenzio_ms=%d soglia_silenzio_ms=%d prove=%d minimo_prove=%d "
            "persi=%d spediti=%d permille=%d finestra_ms=%d "
            "minimo_pacchetti=%d cwnd=%d cwnd_left=%d srtt_us=%d fermo_ms=0 "
            "giri_fermi=0 saltati=0 ritmo_giu=0 ritmo_arretrato=0 ritmo_posti=0 "
            "ritmo_scesi=0 giudizio=%s"
            % (ora, causa, stallo_ms, soglia_stallo, offerti, usciti,
               coda_video, silenzio_ms, LM_SILENZIO_S * 1000, prove,
               LM_MIN_PROVE, persi, spediti, permille, finestra_ms,
               LM_MIN_PACCHETTI, cwnd, cwnd_left, srtt_us, giudizio))


def _fab_chiusa(ora="21:14:02.124"):
    return ("%s quic    ⛔ [192.168.0.2]:50875: DEAD LINE — the QUIC connection "
            "is closing (one single CONNECTION_CLOSE, sent)." % ora)


def _fab_rq(da_ms=1002, persi_d=3, spediti_d=410):
    return ("21:14:00.000 wt      rete-quic [192.168.0.2]:50875 da_ms=%d "
            "persi=7 persi_d=%d byte_persi=9856 byte_persi_d=4224 spediti=48210 "
            "spediti_d=%d byte_spediti=59284410 ricevuti=3011 ricevuti_d=61 "
            "scartati=0 scartati_d=0 cwnd=48000 cwnd_left=0 ssthresh=32000 "
            "involo=47180 srtt_us=41230 latest_us=52980 rttvar_us=11400 "
            "min_rtt_us=22100 coda_rete_us=19130 pto_us=132000 dgram_persi=0 "
            "dgram_persi_d=0 dgram_ok=99 dgram_falsi=1 dgram_falsi_d=0 "
            "giudizio=-- nothing to report" % (da_ms, persi_d, spediti_d))


def _fab_sfratto(ora="21:14:31.500", muto=15412, chi=UTENTE):
    return ("%s rcp     ⭐ EVICTION for silence: %d ms without a PACKET from "
            "[192.168.0.2]:50875 (threshold 15000 ms) — the slot of %s goes to the "
            "client arriving from [192.168.0.2]:50999 (§4.4: whoever is silent is "
            "detached; §8.2 is NOT violated) (slots taken now: 0)"
            % (ora, muto, chi))


def _fab_rifiuto(ora="21:14:20.100", muto=4020, acceso=True):
    return ("%s rcp     slot DENIED to %s from [192.168.0.2]:50999: another "
            "client of this same user holds it (taken: 1) — that occupant "
            "gave a sign of life %d ms ago, and the eviction %s"
            % (ora, UTENTE, muto,
               "did NOT fire (threshold in force)" if acceso else "is switched OFF by hand (--sfratto-ms 0)"))


def _fab_preso(ora="21:14:31.510", chi=UTENTE):
    return ("%s rcp     slot TAKEN by %s via [192.168.0.2]:50999 "
            "(taken now: 1)" % (ora, chi))


def _fab_negato(ora="21:14:20.100"):
    return ("%s rcp     ⛔ EVICTION DENIED: the slot belongs to «%s» and the one asking "
            "is «%s» — between different users there is NEVER an eviction, and this registry "
            "should not even be able to propose it" % (ora, UTENTE, UTENTE2))


def _fab_campioni(secondi=60.0, passo=0.1, periodo=5.0, byte_giro=130,
                  pacchetti_giro=2, fondo_byte_s=0.0, fondo_pkt_s=0.0):
    """Counter samples: one «round» of PINGs every `periodo` seconds.

    ⭐ Manufacturing the samples and not the numbers is what makes the control real:
       the reduction must be able to find the EVENTS inside a counter that rises in
       steps, and it is the only thing that can say whether the PINGs went to 5 s.
    """
    campioni, b, p, t, resto = [], 1000, 10, 0.0, 0.0
    prossimo = periodo
    while t < secondi:
        if t >= prossimo:
            b += byte_giro
            p += pacchetti_giro
            prossimo += periodo
        # ⛔ The background moves the packets TOO, or it is not a background: it is precisely
        #    what makes the events invisible, and it is the case to test.
        b += int(fondo_byte_s * passo)
        resto += fondo_pkt_s * passo
        p += int(resto)
        resto -= int(resto)
        campioni.append([round(t, 3), b, p])
        t += passo
    return campioni


def _certifica_contratto():
    """⛔⛔ THE CONTRACT ON THE TEXT IS TESTED ON THE TEXT — and against the SOURCE.

    The `linea-morta` line is a contract: if the product changes the order of its
    fields, a bench doing `split('=')` would read the wrong field
    **without noticing**.  ⇒ Here the order of the fields is reread from
    `src/webtransport.c` and compared with what this bench expects.

    ⚠ If the source is not there (the bench runs elsewhere), this check KEEPS QUIET:
      «I did not look» is not «it is fine».
    """
    perc = os.path.join(os.path.dirname(QUI), "src", "webtransport.c")
    if not os.path.exists(perc):
        return None, "⚠ «%s» is not there: I did not reread the contract from the source" % perc
    testo = open(perc, encoding="utf-8", errors="replace").read()
    i = testo.find('"linea-morta %s causa=')
    if i < 0:
        return (False, "⛔ in `webtransport.c` I no longer find the format line "
                       "that begins with «linea-morta %s causa=»: the contract "
                       "has changed, and this bench would read fields that are no "
                       "longer there")
    # ⛔ The format is split over several adjacent C literals: they are stitched back.
    pezzi, j = [], i
    while True:
        a = testo.find('"', j)
        if a < 0:
            break
        b = testo.find('"', a + 1)
        if b < 0:
            break
        pezzo = testo[a + 1:b]
        pezzi.append(pezzo)
        j = b + 1
        # the end of the format: the literal that contains `giudizio=`
        if "giudizio=" in pezzo:
            break
        # and if between one literal and the next there is anything but spaces, it is over
        if testo[b + 1:testo.find('"', b + 1) if testo.find('"', b + 1) > 0
                 else b + 1].strip() not in ("",):
            break
    fmt = "".join(pezzi)
    nomi = [x.split("=")[0] for x in fmt.split() if "=" in x]
    if nomi != CAMPI_LM:
        return (False, "⛔ THE CONTRACT HAS CHANGED: the source writes the fields "
                       "%s, this bench expects %s" % (nomi, CAMPI_LM))
    if not fmt.rstrip().endswith("giudizio=%s"):
        return (False, "⛔ `giudizio=` is no longer the LAST field: the value "
                       "contains spaces, and a field after it would be read "
                       "inside the judgement")
    return (True, "⭐ the contract is that one: %d fields in order, and `giudizio=` "
                  "last — reread from `src/webtransport.c`" % len(nomi))


def importa_finto():
    """⛔ The positive control does not touch the machine, but it needs the
       THRESHOLDS of `09-b76` (`COPERTURA_MINIMA`, `BUCO_SCHERMO_FERMO_S`): those
       are the yardstick with which test 6 says «it behaves as in the grid».

    ⚠ The module is just imported, **without** hooking the network to it: `RETE` stays
      `None` and no function that talks to the machine is reachable from
      here — it is the same form as `09-b76.importa_finto()`.
    ⛔ And the two thresholds are REREAD from there instead of copied: two copies of the
       same threshold in two files are two thresholds that diverge.
    """
    global B76
    if B76 is None:
        B76 = _carica("b76rete", os.path.join(QUI, "09-b76-rete-cattiva.py"))


def certifica():
    print("⭐ CERTIFICATION OF THE BENCH OF THE TWO CURES — the expected outcome is written FIRST\n")
    print("   ⛔ No contact with the test machine: here the TOOL is tested, "
          "\n      not the product.\n")
    importa_finto()
    verde = True
    casi = []

    def caso(nome, atteso, avuto):
        """`atteso` is `True`/`False`/`None` — green, red, mute."""
        passa, perche = avuto
        ok = (passa is atteso)
        casi.append({"caso": nome, "atteso": atteso, "avuto": passa,
                     "perche": perche})
        (_ok if ok else _ko)("%s → expected %s, got %s%s"
                             % (nome, atteso, passa,
                                "" if ok else "  ⛔ «%s»" % perche[:150]))
        return ok

    # ── 0 · the contract on the text, reread from the source ───────────────
    _log("0 · THE CONTRACT OF THE `linea-morta` LINE, reread from `src/`")
    passa, perche = _certifica_contratto()
    (_ok if passa else (_dub if passa is None else _ko))(perche)
    if passa is False:
        verde = False

    # ── 1 · the reductions, on manufactured TEXT ─────────────────────
    _log("1 · THE REDUCTIONS — manufactured text inside the same functions as the "
         "real runs")
    lm = riduci_linea_morta([_fab_lm()])
    ok = (lm["esito"] == "letto" and lm["scatti"] == 1
          and lm["causa"] == "stallo" and lm["stallo_ms"] == 5004
          and lm["soglia_stallo_ms"] == LM_STALLO_MS and lm["offerti"] == 41
          and lm["usciti_byte"] == 0 and lm["coda_video"] == 61240
          and lm["permille"] == 75 and lm["spediti"] == 412
          and lm["cwnd_left"] == 0
          and lm["giudizio"].startswith("⛔ the line is DEAD")
          and abs(lm["ora_primo"] - (21 * 3600 + 14 * 60 + 2.123)) < 1e-6)
    (_ok if ok else _ko)("the `linea-morta` line is read field by field, "
                         "`giudizio=` included (with its spaces): %s"
                         % json.dumps({k: lm.get(k) for k in
                                       ("causa", "stallo_ms", "offerti",
                                        "usciti_byte", "coda_video", "permille",
                                        "silenzio_ms", "prove")},
                                      ensure_ascii=False))
    verde = verde and ok

    # ⛔⛔ AND THE TWO REMOVED FIELDS MUST STAY REMOVED: a bench that kept on
    #     reading `soglia_permille=` on a line that no longer has it would not
    #     give an error — it would read `None` and judge on it.
    ok = (lm.get("soglia_permille") is None
          and (lm["righe"][0].get("finestre") is None))
    (_ok if ok else _ko)("⛔ `soglia_permille=` and `finestre=N/M` are NO longer "
                         "in the line, and the bench does not look for them: the threshold "
                         "on loss does not exist (soglia_permille=%s, "
                         "finestre=%s)"
                         % (lm.get("soglia_permille"),
                            lm["righe"][0].get("finestre")))
    verde = verde and ok

    lm0 = riduci_linea_morta([])
    lmx = riduci_linea_morta([], letto=False)
    ok = (lm0["esito"] == "letto" and lm0["scatti"] == 0
          and lmx["esito"] != "letto")
    (_ok if ok else _ko)("⛔⛔ «zero firings» and «I did not read» do NOT look "
                         "the same: «%s» against «%s»"
                         % (lm0["esito"], lmx["esito"][:60]))
    verde = verde and ok

    sf = riduci_sfratto([_fab_rifiuto(), _fab_rifiuto(), _fab_sfratto(),
                         _fab_preso()])
    ok = (sf["sfratti"] == 1 and sf["rifiuti"] == 2 and sf["presi"] == 1
          and sf["muto_ms"] == 15412 and sf["sfrattato"] == UTENTE
          and sf["negati"] == 0 and sf["ultimo_rifiuto_muto_ms"] == 4020
          and sf["sfratto_dice"] == "NON e' scattato")
    (_ok if ok else _ko)("the three eviction marks are read: %d evictions, "
                         "%d refusals, silent %s ms, evicted «%s», the refusal "
                         "line says «%s»"
                         % (sf["sfratti"], sf["rifiuti"], sf.get("muto_ms"),
                            sf.get("sfrattato"), sf.get("sfratto_dice")))
    verde = verde and ok

    sf2 = riduci_sfratto([_fab_rifiuto(acceso=False), _fab_negato()])
    ok = (sf2["negati"] == 1 and sf2["sfratti"] == 0
          and sf2["sfratto_dice"] == "SPENTO")
    (_ok if ok else _ko)("the «EVICTION DENIED» line and the refusal with the eviction OFF "
                         "are told apart: denied %d, says «%s»"
                         % (sf2["negati"], sf2.get("sfratto_dice")))
    verde = verde and ok

    # ⭐ The declared windows: two windows in a row above threshold inside a
    #    heap of good windows, and the cure's guards discarding those
    #    too short or too empty.
    righe = ([_fab_rq(persi_d=2, spediti_d=400)] * 20
             + [_fab_rq(persi_d=30, spediti_d=400)] * 2
             + [_fab_rq(persi_d=2, spediti_d=400)] * 20
             + [_fab_rq(persi_d=90, spediti_d=100)]      # ⛔ few packets
             + [_fab_rq(persi_d=90, spediti_d=400, da_ms=400)])  # ⛔ short window
    fin = finestre_dichiarate(righe)
    ok = (fin["esito"] == "letto" and fin["finestre_valide"] == 42
          and fin["permille_max"] == 75 and fin["sopra_soglia"] == 2
          and fin["coppie_sopra_soglia"] == 1
          and fin["fila_massima_sopra_soglia"] == 2)
    (_ok if ok else _ko)("⛔ the cure's GUARDS apply: 44 lines, %d "
                         "valid windows (the two below %d packets / below %d "
                         "ms are discarded), max %d‰, %d pairs in a row above "
                         "threshold" % (fin["finestre_valide"], LM_MIN_PACCHETTI,
                                     LM_FINESTRA_MS, fin["permille_max"],
                                     fin["coppie_sopra_soglia"]))
    verde = verde and ok

    fin0 = finestre_dichiarate([_fab_rq(persi_d=1, spediti_d=10)] * 30)
    ok = fin0["esito"].startswith("NON GIUDICO")
    (_ok if ok else _ko)("⭐ and if NO window passes the guards, the "
                         "reconstruction REFUSES instead of saying «zero»: «%s»"
                         % fin0["esito"][:110])
    verde = verde and ok

    oro = riduci_orologio(_fab_campioni(periodo=5.0))
    ok = (oro["esito"] == "misurato" and abs(oro["intervallo_mediano_s"] - 5.0) < 0.3
          and oro["eventi"] >= 10)
    (_ok if ok else _ko)("the wire clock finds the PING rounds inside the "
                         "counter: %d events, median interval %s s, %.4f "
                         "kbit/s, %s bytes per round"
                         % (oro["eventi"], oro.get("intervallo_mediano_s"),
                            oro["kbit_s"], oro.get("byte_per_evento")))
    verde = verde and ok

    oro10 = riduci_orologio(_fab_campioni(periodo=10.0))
    ok = (oro10["esito"] == "misurato"
          and abs(oro10["intervallo_mediano_s"] - 10.0) < 0.3)
    (_ok if ok else _ko)("⭐ and it can tell 10 s from 5: median interval %s s"
                         % oro10.get("intervallo_mediano_s"))
    verde = verde and ok

    oroF = riduci_orologio(_fab_campioni(periodo=5.0, fondo_byte_s=180000,
                                         fondo_pkt_s=190.0))
    ok = (oroF["esito"] == "misurato" and oroF["intervallo_mediano_s"] is None
          and "is NOT still" in oroF.get("perche_niente_intervallo", ""))
    (_ok if ok else _ko)("⛔ and on a session that is NOT still (audio background) it "
                         "refuses to give an interval instead of inventing "
                         "one: «%s»" % oroF.get("perche_niente_intervallo", "")[:90])
    verde = verde and ok

    ok = (abs(dt_registro("00:00:01.500 x", "23:59:59.500 x") - 2.0) < 1e-6
          and dt_registro("nessuna ora", "23:59:59.500 x") is None)
    (_ok if ok else _ko)("the log clock steps over midnight, and "
                         "«I do not know» is not «zero seconds»")
    verde = verde and ok

    # ── 2 · the six predicates: GREEN, RED and MUTE ───────────────────────
    _log("2 · THE SIX PREDICATES — and each must be able to give red, not only green")

    testimone_vivo = {"aperta": True, "cliente_attaccato": True,
                      "cliente_staccato": False, "congedi": []}
    testimone_caduto = {"aperta": True, "cliente_attaccato": False,
                        "cliente_staccato": True, "caduta": "the session dropped",
                        "congedi": []}
    giro_buono = {"fps": 9.1, "consegna": {"esito": "misurato", "copertura": 1.0,
                                           "buco_max_s": 0.37}}
    giro_fiacco = {"fps": 1.2, "consegna": {"esito": "misurato", "copertura": 0.4,
                                            "buco_max_s": 6.0}}

    _inf("P1 · ⛔⛔ the false positive")
    verde &= caso("P1 green · zero firings on a line that holds", True,
                  p1_niente_falso_positivo(lm0, testimone_vivo, giro_buono, 10))
    verde &= caso("P1 RED · one firing on a line that holds", False,
                  p1_niente_falso_positivo(lm, testimone_vivo, giro_buono, 10))
    verde &= caso("P1 mute · zero firings but the line was not holding", None,
                  p1_niente_falso_positivo(lm0, testimone_vivo, giro_fiacco, 10))
    verde &= caso("P1 mute · zero firings but the client dropped for other reasons", None,
                  p1_niente_falso_positivo(lm0, testimone_caduto, giro_buono, 10))
    verde &= caso("P1 mute · I did not read the log", None,
                  p1_niente_falso_positivo(lmx, testimone_vivo, giro_buono, 10))

    _inf("P1c · ⛔⛔ the CONTROL: the same line with the cures off")
    giro_regge = {"fps": 9.1, "consegna": {"esito": "misurato", "copertura": 0.99,
                                           "buco_max_s": 0.42,
                                           "consegna_fino_a_s": 599.8}}
    giro_non_regge = {"fps": 1.1, "consegna": {"esito": "misurato",
                                               "copertura": 0.30,
                                               "buco_max_s": 40.0,
                                               "consegna_fino_a_s": 22.0}}
    giro_si_ferma = {"fps": 8.0, "consegna": {"esito": "misurato",
                                              "copertura": 0.40,
                                              "buco_max_s": 30.0,
                                              "consegna_fino_a_s": 240.0}}
    verde &= caso("P1c green · with the cures off the same line holds 10 minutes",
                  True, p1c_la_linea_regge_a_cura_spenta(testimone_vivo,
                                                         giro_regge, 10, 1))
    verde &= caso("P1c RED · ⛔ it drops even with the cures off: the red of test 1 is "
                  "not a false positive", False,
                  p1c_la_linea_regge_a_cura_spenta(testimone_caduto,
                                                   giro_regge, 10, 1))
    verde &= caso("P1c RED · with the cures off the rate is below the bench's "
                  "floor", False,
                  p1c_la_linea_regge_a_cura_spenta(testimone_vivo,
                                                   giro_non_regge, 10, 1))
    verde &= caso("P1c RED · with the cures off delivery stops anyway",
                  False, p1c_la_linea_regge_a_cura_spenta(testimone_vivo,
                                                          giro_si_ferma, 10, 1))
    verde &= caso("P1c mute · I do not have the numbers of the control run", None,
                  p1c_la_linea_regge_a_cura_spenta(testimone_vivo,
                                                   {"fps": None}, 10, 1))

    _inf("P1b · ⭐⭐ the TRUE MARGIN — the scale that tracks down the maximum stall")
    sonda_casa = {"esito": "misurato", "persi_pc": 1.86, "raffica_media": 1.02}
    scala_larga = [{"soglia_ms": 2000, "scattata": False},
                   {"soglia_ms": 1000, "scattata": False},
                   {"soglia_ms": 500, "scattata": False}]
    scala_stretta = [{"soglia_ms": 2000, "scattata": False},
                     {"soglia_ms": 1000, "scattata": True, "stallo_ms": 1043}]
    scala_strettissima = [{"soglia_ms": 3000, "scattata": True,
                           "stallo_ms": 3120}]
    scala_gia_scattata = [{"soglia_ms": LM_STALLO_MS, "scattata": True,
                           "stallo_ms": 5300}]
    scala_poco_giu = [{"soglia_ms": 4000, "scattata": False}]
    verde &= caso("P1b green · it does not fire even at 500 ms ⇒ margin > 10×",
                  True, p1b_il_margine_dello_stallo(scala_larga, LM_STALLO_MS,
                                                    "casa-cattiva"))
    verde &= caso("P1b green · fires at 1000 with stall 1043 ms ⇒ margin 4.8×",
                  True, p1b_il_margine_dello_stallo(scala_stretta, LM_STALLO_MS,
                                                    "raffica-1"))
    verde &= caso("P1b RED · ⛔ stall 3120 ms on a line that holds: "
                  "margin 1.6×", False,
                  p1b_il_margine_dello_stallo(scala_strettissima, LM_STALLO_MS,
                                              "casa-cattiva"))
    verde &= caso("P1b mute · it already fired at the threshold in force: it is the "
                  "false positive, and P1 says so", None,
                  p1b_il_margine_dello_stallo(scala_gia_scattata, LM_STALLO_MS,
                                              "casa-cattiva"))
    verde &= caso("P1b mute · the scale did not go down enough to give a "
                  "margin", None,
                  p1b_il_margine_dello_stallo(scala_poco_giu, LM_STALLO_MS,
                                              "casa-cattiva"))
    verde &= caso("P1b mute · no scale tried", None,
                  p1b_il_margine_dello_stallo([], LM_STALLO_MS, "casa-cattiva"))

    _inf("P-raffica1 · ⭐ the line that delivers 24/s with an empty second")
    att_r1 = GRIGLIA_B76["raffica-1"]
    giro_r1 = {"fps": 23.94, "consegna": {"esito": "misurato", "copertura": 0.96,
                                          "buco_max_s": 1.00}}
    giro_r1_fuori = {"fps": 3.0, "consegna": {"esito": "misurato",
                                              "copertura": 0.5,
                                              "buco_max_s": 8.0}}
    lm_stallo = riduci_linea_morta([_fab_lm(causa="stallo")])
    lm_stallo["chiuse_dal_trasporto"] = 1
    verde &= caso("P-raffica1 green · zero firings and the line is within the grid",
                  True, p_non_deve_scattare("raffica-1", lm0, testimone_vivo,
                                            giro_r1, 1, att_r1))
    verde &= caso("P-raffica1 RED · ⛔⛔ declared dead a line that "
                  "delivers 24 frames/s", False,
                  p_non_deve_scattare("raffica-1", lm_stallo, testimone_vivo,
                                      giro_r1, 1, att_r1))
    verde &= caso("P-raffica1 mute · the run is not the grid's one", None,
                  p_non_deve_scattare("raffica-1", lm0, testimone_vivo,
                                      giro_r1_fuori, 1, att_r1))
    verde &= caso("P-raffica1 mute · the client dropped for other reasons", None,
                  p_non_deve_scattare("raffica-1", lm0, testimone_caduto,
                                      giro_r1, 1, att_r1))

    _inf("P-scena-ferma · ⛔⛔ the worst way in which the cure could fail")
    lm_scena = riduci_linea_morta([_fab_lm(causa="stallo", stallo_ms=1004,
                                           soglia_stallo=1000, offerti=0,
                                           usciti=0, coda_video=0)])
    lm_scena["chiuse_dal_trasporto"] = 1
    verde &= caso("P-scena-ferma green · 120 s of still desktop at threshold 1000, "
                  "zero firings", True,
                  p_scena_ferma_non_scatta(lm0, testimone_vivo, 120, 1000))
    verde &= caso("P-scena-ferma RED · ⛔⛔ throws out whoever looks at a still "
                  "desktop (offerti=0, coda_video=0)", False,
                  p_scena_ferma_non_scatta(lm_scena, testimone_vivo, 120, 1000))
    verde &= caso("P-scena-ferma mute · the client dropped for other reasons", None,
                  p_scena_ferma_non_scatta(lm0, testimone_caduto, 120, 1000))
    verde &= caso("P-scena-ferma mute · I did not read the log", None,
                  p_scena_ferma_non_scatta(lmx, testimone_vivo, 120, 1000))

    _inf("P2 · the real firing")
    sonda_raffica = {"esito": "misurato", "persi_pc": 11.10, "raffica_media": 5.5}
    lm_p = riduci_linea_morta([_fab_lm(causa="stallo")])
    lm_p["chiuse_dal_trasporto"] = 1
    lm_p_senza_filo = riduci_linea_morta([_fab_lm(causa="stallo")])
    lm_p_senza_filo["chiuse_dal_trasporto"] = 0
    lm_s = riduci_linea_morta([_fab_lm(causa="silenzio", stallo_ms=800,
                                       silenzio_ms=10004, prove=3)])
    lm_s["chiuse_dal_trasporto"] = 1
    lm0["chiuse_dal_trasporto"] = 0
    verde &= caso("P2 green · fired with causa=stallo and the wire dropped", True,
                  p2_scatta_sullo_stallo(lm_p, sonda_raffica, 18.4))
    verde &= caso("P2 RED · it did not fire on a line that cannot be served",
                  False, p2_scatta_sullo_stallo(lm0, sonda_raffica, None))
    verde &= caso("P2 RED · fired for silence instead of stall", False,
                  p2_scatta_sullo_stallo(lm_s, sonda_raffica, 12.0))
    verde &= caso("P2 RED · decided but the wire did NOT drop", False,
                  p2_scatta_sullo_stallo(lm_p_senza_filo, sonda_raffica, 18.4))
    verde &= caso("P2 mute · the fault was not put in place", None,
                  p2_scatta_sullo_stallo(lm_p, sonda_casa, 18.4))
    verde &= caso("P2 mute · the probe did not measure", None,
                  p2_scatta_sullo_stallo(lm_p, None, 18.4))

    _inf("P3 · silence")
    lm_presto = riduci_linea_morta([_fab_lm(causa="silenzio", silenzio_ms=6100)])
    lm_presto["chiuse_dal_trasporto"] = 1
    lm_tardi = riduci_linea_morta([_fab_lm(causa="silenzio", silenzio_ms=21000)])
    lm_tardi["chiuse_dal_trasporto"] = 1
    verde &= caso("P3 green · fired at 10.0 s with causa=silenzio", True,
                  p3_scatta_sul_silenzio(lm_s, LM_SILENZIO_S * 1000))
    verde &= caso("P3 RED · it did not fire: the ghost stays until 30 s", False,
                  p3_scatta_sul_silenzio(lm0, LM_SILENZIO_S * 1000))
    verde &= caso("P3 RED · ⛔ fired BEFORE the threshold (a live and idle "
                  "client would be thrown out)", False,
                  p3_scatta_sul_silenzio(lm_presto, LM_SILENZIO_S * 1000))
    verde &= caso("P3 RED · fired long after the threshold (form E1)", False,
                  p3_scatta_sul_silenzio(lm_tardi, LM_SILENZIO_S * 1000))
    verde &= caso("P3 RED · fired for stall and not for silence", False,
                  p3_scatta_sul_silenzio(lm_p, LM_SILENZIO_S * 1000))
    verde &= caso("P3 mute · I did not read the log", None,
                  p3_scatta_sul_silenzio(lmx, LM_SILENZIO_S * 1000))

    _inf("P3b · the declared price of the PINGs")
    fermo_acceso = {"esito": "misurato", "kbit_s": 0.21, "pacchetti": 24,
                    "secondi": 60.0}
    fermo_spento = {"esito": "misurato", "kbit_s": 0.10, "pacchetti": 12,
                    "secondi": 60.0}
    fermo_caro = {"esito": "misurato", "kbit_s": 1.30, "pacchetti": 160,
                  "secondi": 60.0}
    audio_acceso = {"esito": "misurato", "kbit_s": 1412.0, "pacchetti": 11800,
                    "secondi": 60.0}
    audio_spento = {"esito": "misurato", "kbit_s": 1409.0, "pacchetti": 11790,
                    "secondi": 60.0}
    verde &= caso("P3b green · the difference is within the declared one", True,
                  p3b_costo_dei_ping(fermo_acceso, fermo_spento))
    verde &= caso("P3b RED · the PINGs cost more than declared", False,
                  p3b_costo_dei_ping(fermo_caro, fermo_spento))
    verde &= caso("P3b mute · ⛔ the background is bigger than the target", None,
                  p3b_costo_dei_ping(audio_acceso, audio_spento))
    verde &= caso("P3b mute · one of the two measurements is missing", None,
                  p3b_costo_dei_ping(fermo_acceso, {"esito": "NON GIUDICO"}))

    _inf("P4 · the eviction")
    sf_ok = riduci_sfratto([_fab_rifiuto(), _fab_sfratto(), _fab_preso()])
    sf_presto = riduci_sfratto([_fab_sfratto(muto=9000), _fab_preso()])
    sf_niente = riduci_sfratto([_fab_rifiuto()] * 11 + [_fab_preso()])
    verde &= caso("P4 green · the slot becomes free again at ~15 s", True,
                  p4_lo_sfratto_libera_il_posto(sf_ok, SFRATTO_CONSIGLIATO_MS,
                                                15.6, 30.5))
    verde &= caso("P4 RED · no eviction, the silence of §5.3 is waited for",
                  False,
                  p4_lo_sfratto_libera_il_posto(sf_niente, SFRATTO_CONSIGLIATO_MS,
                                                30.5, 30.5))
    verde &= caso("P4 RED · ⛔ evicted BEFORE the threshold (I2 off)", False,
                  p4_lo_sfratto_libera_il_posto(sf_presto, SFRATTO_CONSIGLIATO_MS,
                                                9.2, 30.5))
    verde &= caso("P4 RED · evicted, but the slot still takes 28 s",
                  False,
                  p4_lo_sfratto_libera_il_posto(sf_ok, SFRATTO_CONSIGLIATO_MS,
                                                28.0, 30.5))
    verde &= caso("P4 mute · I do not know when the slot was taken back", None,
                  p4_lo_sfratto_libera_il_posto(sf_ok, SFRATTO_CONSIGLIATO_MS,
                                                None, 30.5))

    _inf("P5 · ⛔ two different users")
    sf_due_ok = riduci_sfratto([_fab_preso(chi=UTENTE), _fab_preso(chi=UTENTE2)])
    sf_buco = riduci_sfratto([_fab_sfratto(chi=UTENTE), _fab_preso(chi=UTENTE2)])
    verde &= caso("P5 green · no eviction and the second user gets in", True,
                  p5_fra_utenti_diversi_non_si_sfratta(sf_due_ok, True,
                                                       UTENTE, UTENTE2))
    verde &= caso("P5 RED · ⛔⛔ eviction between different users = security hole",
                  False,
                  p5_fra_utenti_diversi_non_si_sfratta(sf_buco, True,
                                                       UTENTE, UTENTE2))
    verde &= caso("P5 mute · no eviction, but the second did not get in", None,
                  p5_fra_utenti_diversi_non_si_sfratta(sf_due_ok, False,
                                                       UTENTE, UTENTE2))
    verde &= caso("P5b green · the «EVICTION DENIED» line does NOT come out (predicted `[R]`)",
                  True, p5b_la_riga_del_negato(sf_due_ok))
    verde &= caso("P5b RED · the line COMES OUT, that is my reading was wrong",
                  False, p5b_la_riga_del_negato(riduci_sfratto([_fab_negato()])))

    _inf("P6 · ⛔ the defaults change nothing (I6)")
    spento = {"esito": "letto", "linea_morta": "spenta", "stallo_ms": None,
              "silenzio_s": None, "sfratto_ms": 0, "righe": []}
    acceso = {"esito": "letto", "linea_morta": "accesa", "stallo_ms": LM_STALLO_MS,
              "silenzio_s": LM_SILENZIO_S, "sfratto_ms": SFRATTO_CONSIGLIATO_MS,
              "righe": []}
    sf_vuoto = riduci_sfratto([_fab_preso()])
    giro_casa = {"fps": 9.1, "consegna": {"esito": "misurato", "copertura": 0.96,
                                          "buco_max_s": 0.42}}
    giro_casa_fuori = {"fps": 22.0, "consegna": {"esito": "misurato",
                                                 "copertura": 1.0,
                                                 "buco_max_s": 0.1}}
    giro_raffica = {"fps": 2.1, "consegna": {"esito": "misurato", "copertura": 0.28,
                                             "buco_max_s": 14.26}}
    giro_raffica_sana = {"fps": 30.0, "consegna": {"esito": "misurato",
                                                   "copertura": 1.0,
                                                   "buco_max_s": 0.2}}
    verde &= caso("P6 green · cures off, «casa-cattiva» as in the b76 grid",
                  True, p6_i_predefiniti_non_cambiano_niente(
                      lm0, sf_vuoto, spento, giro_casa, "casa-cattiva"))
    verde &= caso("P6 green · cures off, «raffica-forte» stops as it does there",
                  True, p6_i_predefiniti_non_cambiano_niente(
                      lm0, sf_vuoto, spento, giro_raffica, "raffica-forte"))
    verde &= caso("P6 RED · ⛔ I6: the cure is off and fired anyway",
                  False, p6_i_predefiniti_non_cambiano_niente(
                      lm_p, sf_vuoto, spento, giro_casa, "casa-cattiva"))
    verde &= caso("P6 RED · ⛔ I6: the eviction is off and there was an eviction",
                  False, p6_i_predefiniti_non_cambiano_niente(
                      lm0, sf_ok, spento, giro_casa, "casa-cattiva"))
    verde &= caso("P6 RED · the profile leaves the grid of 09-b76", False,
                  p6_i_predefiniti_non_cambiano_niente(
                      lm0, sf_vuoto, spento, giro_casa_fuori, "casa-cattiva"))
    verde &= caso("P6 RED · «raffica-forte» NO longer stops: the product has "
                  "changed", False, p6_i_predefiniti_non_cambiano_niente(
                      lm0, sf_vuoto, spento, giro_raffica_sana, "raffica-forte"))
    verde &= caso("P6 mute · the server was NOT on the defaults", None,
                  p6_i_predefiniti_non_cambiano_niente(
                      lm0, sf_vuoto, acceso, giro_casa, "casa-cattiva"))

    # ── 3 · the configuration guard ────────────────────────────────────
    _log("3 · THE GUARD — «is the server configured as this test believes?»")
    verde &= caso("cures ON as I want them", True,
                  cure_come_voglio(acceso, linea_morta="accesa",
                                   stallo_ms=LM_STALLO_MS,
                                   sfratto_ms=SFRATTO_CONSIGLIATO_MS))
    verde &= caso("⛔ mute if the dead line turns out OFF when I wanted it "
                  "on", None,
                  cure_come_voglio(spento, linea_morta="accesa"))
    verde &= caso("⛔ mute if the STALL threshold is not the one I believe", None,
                  cure_come_voglio(acceso, linea_morta="accesa", stallo_ms=1))
    verde &= caso("⛔ mute if I did not read the startup line", None,
                  cure_come_voglio({"esito": "⛔ NON HO LETTO nessuna riga"},
                                   linea_morta="accesa"))

    os.makedirs(FUORI, exist_ok=True)
    with open(os.path.join(FUORI, "09-b81-certifica.json"), "w") as f:
        json.dump(casi, f, ensure_ascii=False, indent=1)
    _log("OUTCOME OF THE CERTIFICATION")
    _inf("%d cases, %d wrong · details in %s/09-b81-certifica.json"
         % (len(casi), len([c for c in casi if c["avuto"] is not c["atteso"]]),
            FUORI))
    if verde:
        _ok("⭐ all the predicates did what was written beforehand — and "
            "each one gave red at least once")
        return 0
    _ko("⛔ the bench can NOT see what it looks for: it has no right to green")
    return 1


# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT TALKS TO THE TEST MACHINE
# ═══════════════════════════════════════════════════════════════════════════
import contextlib   # noqa: E402  (it is here because only this half needs it)

CHI = "09-b81-linea-morta"
AFFITTO = 900        # ⛔ SHORT leases, renewed: other agents are queued


def vicine():
    """⛔ The ports that are NOT mine: they are COUNTED before and after, not touched."""
    fuori = []
    for p in VICINE:
        rc, o, _ = root("bash -c \"ss -uln 2>/dev/null | grep -c ':%s ' || true\"" % p)
        fuori.append("%s:%s" % (p, o.strip()))
    return " ".join(fuori)


def preparati():
    """The scripts on the machine, and the probe's port chosen NOW.

    ⛔ The probe's port cannot be fixed: while I run, another agent
       may start a server on the one I had seen free (`09-b76`).
    """
    if not B76.spedisci_sonda():
        _ko("the scripts of the probe / of the reader were not written in %s" % LAV)
        return False
    if not B76.scrivi_sulla_macchina("09-b81-orologio.py", OROLOGIO):
        _ko("the wire clock was not written in %s" % LAV)
        return False
    if B76.scegli_porta_sonda() is None:
        _ko("⛔ none of my ports for the probe is free: I do NOT measure, "
            "because without a probe I do not know whether the fault was put in place")
        return False
    impronte = B78.spedisci()
    if impronte is None:
        _ko("`09-b78-apertura.py` / `01-b3-cliente.py` did not arrive in the tree")
        return False
    _ok("scripts ready · probe on port %d · %s"
        % (B76.PORTA_SONDA, " · ".join(impronte)))
    _inf("ports NOT mine (counted, not touched): %s" % vicine())
    return True


def accendi_server(opzioni, perche):
    """⛔ Restarts MY server (unit `%s`) with those options, and THEN
       rereads from the startup line that it really took them.

    ⚠ An option typed through `ssh` → `sudo` → `systemd-run` → `bash -lc`
      has four ways of getting lost on the way, and none of the four gives an error:
      it gives a server running on the defaults while the bench believes it is measuring
      a cure that is on.
    """ % UNITA
    _log("THE SERVER IS RESTARTED — %s" % perche)
    _inf("options: %s" % (opzioni or "(none: the defaults, that is I6)"))
    amb = dict(os.environ)
    amb["OPZIONI_SERVER"] = opzioni
    amb["UNITA"] = UNITA
    p = subprocess.run(["bash", os.path.join(QUI, "09-b81-terreno.sh"), "accendi"],
                       env=amb, capture_output=True, timeout=420)
    testo = (p.stdout + p.stderr).decode("utf-8", "replace")
    for r in testo.splitlines():
        if re.search(r"server \d+ on port|NO |the server did not start", r):
            _inf(r.strip()[:180])
    if p.returncode != 0:
        _ko("⛔ the server did not restart: %s" % testo[-400:])
        return False
    stato = stato_delle_cure()
    _inf("the server says of itself: dead line %s (stall %s ms, silence %s s) · "
         "eviction %s ms"
         % (stato["linea_morta"], stato["stallo_ms"], stato["silenzio_s"],
            stato["sfratto_ms"]))
    # ⛔ The stage and the monitor are born with the FIRST client: without it, the scene would not
    #    know where to draw (`09-b70.innesca_sessione`).
    if not B70.innesca_sessione():
        _ko("the priming session does not open: the stage is not there")
        return False
    _ok("server restarted and stage primed")
    return True


@contextlib.contextmanager
def rete_guasta(regole, previsti_s, attesa=1800):
    """⛔ The lock, the guardian and the `netem`, taken and given back TOGETHER.

    · the lock because the `netem` on `lo` is only one for the whole machine,
      and two benches breaking it together do not give a red: they give a
      plausible number (`LEZIONI.md` §1.26);
    · the guardian because the network must go back as it was **even if I die**;
    · the `u32` filters on %d only, and `enp7s0` is NEVER touched.
    """ % PORTA
    LUC.prendi(CHI, secondi=AFFITTO, attesa=attesa)
    RETE.guardiano_arma(min(3600, previsti_s + 600))
    messa = False
    try:
        ok, q = RETE.stringi(regole)
        if not ok:
            raise SystemExit("⛔ tc refused the rule: %s" % q)
        messa = True
        B76.filtri_sonda()
        riletta = B76.regola_riletta()
        # ⛔ The rule is REREAD: `tc qdisc change` is sticky, and `[M]` 23
        #    Aug 2026 it dragged a `reorder` along for four profiles.
        passa, perche = B76.controlla_regola([x for x in regole if x != "limit"
                                              and not x.isdigit()], riletta)
        (_ok if passa else _ko)("the rule: %s" % perche)
        if not passa:
            raise SystemExit("⛔ the installed rule is not the one requested")
        yield riletta
    finally:
        _log("⛔ THE NETWORK IS PUT BACK AS IT WAS")
        if not RETE.rimetti():
            _ko("⛔ the network did NOT go back as it was: put it back by hand with «rimetti»")
        LUC.molla(CHI)
        if messa:
            _inf("ports NOT mine after the run: %s" % vicine())


def profilo(nome):
    """The `netem` rules of a profile of `09-b76`, taken from there and not copied."""
    for p in B76.PROFILI:
        if p[0] == nome:
            return p
    raise SystemExit("⛔ profile «%s» is not in 09-b76" % nome)


def sonda(nome):
    """The probe of `09-b76`, and its verdict «was the fault put in place?»."""
    s = B76.sonda_gira()
    B76.stampa_sonda(s)
    p = profilo(nome)
    passa, perche = B76.p_guasto_messo(nome, p[6], s)
    (_ok if passa else (_dub if passa is None else _ko))(
        "THE FAULT WAS PUT IN PLACE: %s" % perche)
    return s, (passa, perche)


def cliente_in_sottofondo(utente, parola_dentro, secondi, marca):
    """⛔ The client INSIDE the chroot, detached from my `ssh`: it must be
       still alive when I kill it, and `enter.sh` is a `chroot` — so the
       process is seen and killed from the HOST with its real pid."""
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s --audio-codec pcm --video-codec h264 "
              "--adatta 1920x1080 --resta %d"
              % (DENTRO_ALB, IND, PORTA, utente, parola_dentro, secondi))
    root("bash /media/REMOTIX/enter.sh --root 'setsid nohup %s > %s/%s.log 2>&1 & "
         "sleep 0.5; echo lanciato'" % (dentro, DENTRO_LAV, marca), 180)


def cliente_pid(utente):
    """⛔ TWO guards in the pattern, and both are against the same error —
       killing the wrong process:

       1. the `[.]` breaks the literal, so `pgrep` does not find ITSELF (its
          pattern is inside its own command line);
       2. the anchor `^python3` excludes the `bash -lc` that LAUNCHED the client and
          that carries the same line inside its own: ⚠ that one lasts half a
          second, and if I took it I would kill an already dead shell and
          believe I had killed the client — which would instead stay alive, and
          the silence test would measure a silence that is not there.
    """
    rc, out, _ = root("bash -c \"pgrep -f '^python3 .*b3-cliente[.]py .*--utente "
                      "%s ' | head -1\"" % utente)
    t = out.strip().splitlines()
    return int(t[0]) if t and t[0].isdigit() else None


def uccidi(pid):
    """⛔ `kill -9`, so that the goodbye does NOT leave: for the server it is identical to a
       LOST goodbye, and it is the real case — the user whose wire drops.

    ⭐ And it returns the time ON THE SERVER, not on the laptop: it is the only clock that can
       be subtracted from the log's without bringing in the `ssh`, the
       container and the difference between two machines.
    """
    if pid is None:
        return None
    rc, out, _ = root("bash -c \"kill -9 %d; date +'%%H:%%M:%%S.%%3N'\"" % pid)
    t = out.strip().splitlines()
    return (t[-1] + " x") if t else None


def ripulisci_clienti():
    """⚠ Between one test and the next: a client left alive would keep the slot, and
       the next test would measure the previous run's lock."""
    root("bash -c \"pkill -9 -f '^python3 .*b3-cliente[.]py .*--porta %d ' ; "
         "true\"" % PORTA)


def aspetta_riga(riga0, filtro, tetto=45.0, passo=1.0):
    scade = time.time() + tetto
    while True:
        r = leggi_registro(riga0, filtro)
        if r or time.time() >= scade:
            return r
        time.sleep(passo)


def stampa_finestre(fin):
    if fin.get("esito") != "letto":
        _dub("DECLARED  %s" % fin.get("esito"))
        return
    _inf("DECLARED  %d valid windows over %d `rete-quic` lines · max %d‰ · "
         "p95 %d‰ · median %d‰ · mean %.2f‰"
         % (fin["finestre_valide"], fin["righe"], fin["permille_max"],
            fin["permille_p95"], fin["permille_mediano"], fin["permille_medio"]))
    _inf("            above the threshold of %d‰: %d windows · longest run %d · "
         "pairs (= the firing condition) %d · cumulative %.2f‰ (%d lost out of "
         "%d sent)"
         % (fin["soglia_permille"], fin["sopra_soglia"],
            fin["fila_massima_sopra_soglia"], fin["coppie_sopra_soglia"],
            fin["cumulativa_permille"], fin["persi_totali"],
            fin["spediti_totali"]))
    _inf("            ⭐ the START-UP apart: first %d windows max %s‰ · after: "
         "max %s‰, median %s‰, %s above threshold, longest run %s, pairs %s"
         % (fin["prime_finestre"], fin["permille_max_prime"],
            fin["permille_max_dopo"], fin["permille_mediano_dopo"],
            fin["sopra_soglia_dopo"], fin["fila_massima_dopo"],
            fin["coppie_sopra_soglia_dopo"]))


def stampa_scatti(lm):
    if lm.get("esito") != "letto":
        _dub("FIRINGS  %s" % lm.get("esito"))
        return
    _inf("FIRINGS  %d `linea-morta` line(s) · %d closures by the transport%s"
         % (lm["scatti"], lm.get("chiuse_dal_trasporto", 0),
            ("  ⇒ causa=%s stallo_ms=%s (threshold %s) offerti=%s usciti_byte=%s "
             "coda_video=%s · witness permille=%s"
             % (lm.get("causa"), lm.get("stallo_ms"),
                lm.get("soglia_stallo_ms"), lm.get("offerti"),
                lm.get("usciti_byte"), lm.get("coda_video"),
                lm.get("permille"))) if lm["scatti"] else ""))
    for r in lm.get("righe", [])[:3]:
        _inf("        %s" % r["riga"][:240])


def stampa_sfratto(sf):
    if sf.get("esito") != "letto":
        _dub("EVICTION %s" % sf.get("esito"))
        return
    _inf("EVICTION %d evictions · %d DENIED · %d refusals («slot DENIED») · %d "
         "slots taken · the last refusal said «sign of life %s ms ago» and the "
         "eviction «%s»"
         % (sf["sfratti"], sf["negati"], sf["rifiuti"], sf["presi"],
            sf.get("ultimo_rifiuto_muto_ms"), sf.get("sfratto_dice")))
    for r in (sf.get("righe_sfratto") or [])[:2]:
        _inf("        %s" % r[:240])
    for r in (sf.get("righe_negato") or [])[:2]:
        _inf("        %s" % r[:240])


def stampa_orologio(o, come):
    if o.get("esito") != "misurato":
        _dub("WIRE %s  %s" % (come, o.get("esito")))
        return
    _inf("WIRE %s  %.3f kbit/s (%d bytes, %d packets in %.1f s) · %d events · "
         "median interval %s s (min %s, max %s) · %s bytes per round"
         % (come, o["kbit_s"], o["byte"], o["pacchetti"], o["secondi"],
            o["eventi"], o.get("intervallo_mediano_s"),
            o.get("intervallo_min_s"), o.get("intervallo_max_s"),
            o.get("byte_per_evento")))
    if o.get("perche_niente_intervallo"):
        _inf("        ⚠ %s" % o["perche_niente_intervallo"])


def fps_del_giro(n):
    """⭐ The rate, and from TWO witnesses: the §11.1 trace if it was read, and the
       count the CLIENT prints by itself otherwise.

    ⛔ The second is not a convenient fallback: over a ten-minute window the
       trace is big, and *«the reader did not answer»* looks identical
       to *«the session delivered nothing»* (`09-b70`, the third face of
       §1.9).  ⇒ With two witnesses, that fault cannot disguise itself as a measurement.
    """
    if B70._ha_misurato(n) and n.get("fps"):
        return n["fps"], "§11.1 trace"
    d, sec = n.get("dal_cliente"), n.get("secondi_veri")
    if d and sec:
        return round(d["fotogrammi"] / float(sec), 2), "the CLIENT's count"
    return None, "no witness of the rate"


def _fuori(nome):
    return os.path.join(FUORI, "09-b81-%s.json" % nome)


def salva(nome, roba):
    os.makedirs(FUORI, exist_ok=True)
    with open(_fuori(nome), "w") as f:
        json.dump(roba, f, ensure_ascii=False, indent=1)


def carica(nome):
    try:
        with open(_fuori(nome)) as f:
            return json.load(f)
    except Exception:
        return None


def _voci(titolo, **k):
    v = {"prova": titolo, "predicati": []}
    v.update(k)
    return v


def _predica(voci, etichetta, esito):
    passa, perche = esito
    voci["predicati"].append({"predicato": etichetta, "passa": passa,
                              "perche": perche})
    (_ok if passa else (_dub if passa is None else _ko))("%s: %s"
                                                         % (etichetta, perche))
    return voci


# ═══════════════════════════════════════════════════════════════════════════
# TEST 1 · ⛔⛔ THE FALSE POSITIVE
# ═══════════════════════════════════════════════════════════════════════════
def prova1(a):
    _log("TEST 1 · ⛔⛔ THE FALSE POSITIVE — the test that can make the cure be WITHDRAWN")
    print("   `casa-cattiva` (delay 40ms 20ms distribution normal loss 2%), dead")
    print("   line ON, for %g minutes: the expectation is ZERO firings." % (a.secondi / 60.0))
    print("   ⛔ That line HOLDS (`[M]` 7.8-10.2 frames/s): declaring it")
    print("      dead would mean throwing out someone who was working.")
    v = _voci("1 · the false positive", profilo="casa-cattiva", secondi=a.secondi)
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    va, perche = cure_come_voglio(stato, linea_morta="accesa",
                                  stallo_ms=LM_STALLO_MS,
                                  silenzio_s=LM_SILENZIO_S)
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "P1 · ⛔⛔ no false positive", _muto(perche))
    p = profilo("casa-cattiva")
    with rete_guasta(B76._regole(p[1]), a.secondi + 400) as riletta:
        v["regola"] = riletta
        s, (pg, perche_g) = sonda("casa-cattiva")
        v["sonda"], v["guasto"] = s, {"passa": pg, "perche": perche_g}
        usc = B76.scena_accendi("barra")
        if not usc:
            _ko("the scene does not start: I do NOT judge this run")
            return _predica(v, "P1 · ⛔⛔ no false positive",
                            _muto("the scene did not start: without a moving "
                                  "scene there is no user at work "
                                  "not to throw out"))
        _inf("«barra» scene on monitor %s" % usc)
        riga0 = riga0_pulita()
        B76.rinnova(CHI, AFFITTO)
        _inf("⏳ %g minutes of session — starting now" % (a.secondi / 60.0))
        n = B70.giro("p1-casa-cattiva", "barra", B70.TELA_PIENA, a.secondi)
        n["testimoni"] = B76.testimoni_connessione(riga0, n)
        lm = leggi_linea_morta(riga0)
        fin = leggi_finestre(riga0)
        B76.scena_spegni()
    B70.stampa_giro(n)
    B76.stampa_consegna(n)
    B76.stampa_testimoni(n["testimoni"])
    stampa_scatti(lm)
    stampa_finestre(fin)
    fps, da_dove = fps_del_giro(n)
    _inf("RATE    %s frames/s (%s)" % (fps, da_dove))
    n2 = dict(n)
    n2["fps"] = fps
    v["giro"] = {k: n.get(k) for k in ("fps", "esito", "dal_cliente",
                                       "secondi_veri", "consegna", "server",
                                       "testimoni")}
    v["fps"], v["fps_da"] = fps, da_dove
    v["scatti"], v["dichiarata"] = lm, fin
    salva("p1", v)
    _predica(v, "P1 · ⛔⛔ NO FALSE POSITIVE in %g minutes" % (a.secondi / 60.0),
             p1_niente_falso_positivo(lm, n["testimoni"], n2, a.secondi / 60.0))
    # ⚠ The DECLARED fraction stays printed as DIAGNOSIS: it is the witness
    #   of the reordering, and it is the number that refuted the old cure.  ⛔ But
    #   it no longer judges anything, and indeed here there is no predicate looking
    #   at it: the margin is measured by the SCALE, with `p1b`.
    return v


def prova1_controllo(a):
    """⛔⛔ THE CONTROL OF TEST 1 — same line, same duration, cures OFF.

    ⇒ It serves two things, and neither of them is an extra:
      1. **making the red of test 1 valid**: when the cure fires the
         session dies, and from a run dead at 4 s one cannot read whether the line
         was holding (⇒ `p1c`);
      2. **giving `P1b` its windows**: the reconstruction of the DECLARED
         fraction needs hundreds of windows, and with the cure on
         there are five because the session lasted four seconds.
    """
    _log("TEST 1 · THE CONTROL — same line, same duration, cures OFF")
    print("   ⛔ Without this run the red of test 1 does not count: when the cure")
    print("      fires the session dies, and «it threw out someone who was working»")
    print("      would look the same as «the line was finished anyway».")
    v = _voci("1-controllo · the same line with the cures OFF",
              profilo="casa-cattiva", secondi=a.secondi)
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    va, perche = cure_come_voglio(stato, linea_morta="spenta", sfratto_ms=0)
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "P1c · the control", _muto(perche))
    accesa = carica("p1") or {}
    scatti_accesa = ((accesa.get("scatti") or {}).get("scatti"))
    p = profilo("casa-cattiva")
    with rete_guasta(B76._regole(p[1]), a.secondi + 400) as riletta:
        v["regola"] = riletta
        s, (pg, perche_g) = sonda("casa-cattiva")
        v["sonda"], v["guasto"] = s, {"passa": pg, "perche": perche_g}
        usc = B76.scena_accendi("barra")
        if not usc:
            return _predica(v, "P1c · the control",
                            _muto("the scene did not start"))
        _inf("«barra» scene on monitor %s" % usc)
        riga0 = riga0_pulita()
        B76.rinnova(CHI, AFFITTO)
        _inf("⏳ %g minutes of session with the cures OFF — starting now"
             % (a.secondi / 60.0))
        n = B70.giro("p1c-casa-cattiva", "barra", B70.TELA_PIENA, a.secondi)
        n["testimoni"] = B76.testimoni_connessione(riga0, n)
        lm = leggi_linea_morta(riga0)
        fin = leggi_finestre(riga0)
        B76.scena_spegni()
    B70.stampa_giro(n)
    B76.stampa_consegna(n)
    B76.stampa_testimoni(n["testimoni"])
    stampa_scatti(lm)
    stampa_finestre(fin)
    fps, da_dove = fps_del_giro(n)
    _inf("RATE    %s frames/s (%s)" % (fps, da_dove))
    n2 = dict(n)
    n2["fps"] = fps
    v["giro"] = {k: n.get(k) for k in ("fps", "esito", "dal_cliente",
                                       "secondi_veri", "consegna")}
    v["fps"], v["scatti"], v["dichiarata"] = fps, lm, fin
    salva("p1-controllo", v)
    _predica(v, "P1c · ⛔⛔ with the cures OFF the same line HOLDS %g minutes"
             % (a.secondi / 60.0),
             p1c_la_linea_regge_a_cura_spenta(n["testimoni"], n2,
                                              a.secondi / 60.0, scatti_accesa))
    # ⛔ AND HERE the threshold is judged, not in the run with the cure on: it is the only run that
    #    has enough windows for «it never broke through» to be a measurement.
    return v


def scala_stallo(a, nome, secondi, soglie=None):
    """⭐⭐ THE SCALE THAT TRACKS DOWN THE MAXIMUM STALL — ⇒ the box of `p1b`.

    ⛔ The `linea-morta` line comes out ONLY on firing: «it did not fire» does not say
       **by how much**.  ⇒ The same profile is rerun with lower and lower
       thresholds until one fires, and then the product PRINTS its `stallo_ms`.

    ⭐ And one goes down, not up: the first step that fires is the one that gives the
       BIGGEST measurable stall, and there is no need to go below.  ⚠ Every step
       costs a server restart, so the scale is short on purpose.

    ⚠ AND THE WINDOW IS SHORTER THAN THAT OF TEST 1, and it must be said: here one
      measures the maximum stall within %g s, not within ten minutes.  The maximum
      over ten minutes cannot be SMALLER than this, so the margin
      that comes out is an UPPER BOUND — and the only number that really closes
      test 1 remains the zero firings over the ten minutes.
    """ % secondi
    soglie = soglie or SCALA_STALLO_MS
    gradini = []
    p = profilo(nome)
    for soglia in soglie:
        if not accendi_server("--linea-morta --linea-morta-stallo-ms %d" % soglia,
                              "stall scale on «%s» — threshold %d ms"
                              % (nome, soglia)):
            gradini.append({"soglia_ms": soglia, "scattata": None,
                            "perche": "the server did not restart"})
            break
        stato = stato_delle_cure()
        va, perche = cure_come_voglio(stato, linea_morta="accesa",
                                      stallo_ms=soglia)
        if va is not True:
            _dub(perche)
            gradini.append({"soglia_ms": soglia, "scattata": None,
                            "perche": perche})
            continue
        with rete_guasta(B76._regole(p[1]), secondi + 400):
            s_sonda, (pg, perche_g) = sonda(nome)
            usc = B76.scena_accendi("barra")
            if not usc:
                gradini.append({"soglia_ms": soglia, "scattata": None,
                                "perche": "the scene did not start"})
                continue
            riga0 = riga0_pulita()
            n = B70.giro("scala-%s-%d" % (nome, soglia), "barra",
                         B70.TELA_PIENA, secondi)
            n["testimoni"] = B76.testimoni_connessione(riga0, n)
            lm = leggi_linea_morta(riga0)
            B76.scena_spegni()
        fps, da_dove = fps_del_giro(n)
        c = (n.get("consegna") or {})
        stampa_scatti(lm)
        # ⛔⛔ AND A STEP IN WHICH THE FAULT WAS NOT PUT IN PLACE IS NOT A
        #     TEST — `[M]` 24 August 2026, found while running: on `raffica-1` one
        #     step had 0.28 % loss instead of 1 %, and without
        #     this line it would have ended up in the scale as *«at 2000 ms it does not
        #     fire»* — that is, a margin proved on a profile MILDER than
        #     the one I believe.  ⚠ It is the same form as `p_guasto_messo`: a
        #     true number with a made-up cause.
        #     ⇒ `scattata=None` — «I do not know» — and `p1b` skips it.
        g = {"soglia_ms": soglia,
             "scattata": (lm["scatti"] > 0) if pg is True else None,
             "stallo_ms": lm.get("stallo_ms"), "causa": lm.get("causa"),
             "offerti": lm.get("offerti"), "usciti_byte": lm.get("usciti_byte"),
             "coda_video": lm.get("coda_video"), "permille": lm.get("permille"),
             "fps": fps, "buco_max_s": c.get("buco_max_s"),
             "copertura": c.get("copertura"),
             "sonda_persi_pc": (s_sonda or {}).get("persi_pc"),
             "guasto": perche_g}
        gradini.append(g)
        _inf("STEP threshold %d ms → %s · stallo_ms=%s · %s frames/s · client "
             "gap %s s"
             % (soglia,
                "FIRED" if g["scattata"] else
                ("nothing" if g["scattata"] is False else
                 "⛔ DOES NOT COUNT (the fault was not put in place)"),
                g["stallo_ms"], fps, g["buco_max_s"]))
        if g["scattata"]:
            # ⭐ Found the step that fires: its `stallo_ms` is the biggest
            #   measurable number, and going further down would give only smaller
            #   numbers.
            break
    return gradini


def prova_margine(a, nome, soglie=None, etichetta=None):
    """⭐⭐ THE TRUE MARGIN — and without it the green does not say how close it
       came.  ⇒ The box above `p1b_il_margine_dello_stallo`."""
    _log("THE MARGIN — the scale that tracks down the stall of «%s»" % nome)
    v = _voci("%s · the maximum stall of %s" % (etichetta or "margine", nome),
              profilo=nome, finestra_s=a.scala_s)
    v["scala"] = scala_stallo(a, nome, a.scala_s, soglie)
    salva("margine-%s" % nome, v)
    _predica(v, "P1b · ⭐⭐ the MARGIN of the stall threshold on «%s»" % nome,
             p1b_il_margine_dello_stallo(v["scala"], LM_STALLO_MS, nome))
    return v


def prova1_margine(a):
    return prova_margine(a, "casa-cattiva", etichetta="1-margine")


def prova_raffica1(a):
    """⭐ THE CASE THAT KEEPS THE THRESHOLD HONEST — and before, it was not there.

    `raffica-1` is the exact twin of `perdita-1`: same average loss, but in
    CLUSTERS.  `[M]` it delivers **23.94 frames/s** — that is, it is a
    perfectly usable session — and still had **a whole empty second**.
    ⇒ It is the number the narrow side of the stall threshold rests on, and
      if the cure fired here the threshold would be written on nothing.
    """
    _log("TEST 3-nuova · ⭐ `raffica-1` — 24 frames/s with an empty second")
    print("   ⛔ It must NOT fire.  It is the case that keeps the threshold honest: a")
    print("      perfectly usable line that still has a second at zero.")
    v = _voci("3-nuova · raffica-1, the case that keeps the threshold honest",
              profilo="raffica-1", secondi=a.corti)
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    va, perche = cure_come_voglio(stato, linea_morta="accesa",
                                  stallo_ms=LM_STALLO_MS)
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "P-raffica1", _muto(perche))
    p = profilo("raffica-1")
    with rete_guasta(B76._regole(p[1]), a.corti + 400) as riletta:
        v["regola"] = riletta
        s_sonda, (pg, perche_g) = sonda("raffica-1")
        v["sonda"], v["guasto"] = s_sonda, {"passa": pg, "perche": perche_g}
        usc = B76.scena_accendi("barra")
        _inf("«barra» scene on monitor %s" % usc)
        riga0 = riga0_pulita()
        n = B70.giro("p3n-raffica-1", "barra", B70.TELA_PIENA, a.corti)
        n["testimoni"] = B76.testimoni_connessione(riga0, n)
        lm = leggi_linea_morta(riga0)
        fin = leggi_finestre(riga0)
        B76.scena_spegni()
    B70.stampa_giro(n)
    B76.stampa_consegna(n)
    B76.stampa_testimoni(n["testimoni"])
    stampa_scatti(lm)
    stampa_finestre(fin)
    fps, da_dove = fps_del_giro(n)
    _inf("RATE    %s frames/s (%s)" % (fps, da_dove))
    n2 = dict(n)
    n2["fps"] = fps
    v["fps"], v["scatti"], v["dichiarata"] = fps, lm, fin
    v["giro"] = {k: n.get(k) for k in ("fps", "esito", "dal_cliente",
                                       "secondi_veri", "consegna")}
    salva("p3n-raffica1", v)
    _predica(v, "P-raffica1 · ⭐ «raffica-1» HOLDS and must not be declared dead",
             p_non_deve_scattare("raffica-1", lm, n["testimoni"], n2,
                                 a.corti / 60.0, GRIGLIA_B76["raffica-1"]))
    # ⭐ And the margin here too: it is the NARROW side of the threshold, so it is the
    #   place where a thin margin would hurt most.
    v["scala"] = scala_stallo(a, "raffica-1", a.corti)
    salva("p3n-raffica1", v)
    _predica(v, "P1b · ⭐⭐ the MARGIN of the threshold on «raffica-1» (narrow side)",
             p1b_il_margine_dello_stallo(v["scala"], LM_STALLO_MS, "raffica-1"))
    return v


def prova_scena_ferma(a, soglia_ms):
    """⛔⛔ THE STILL SCENE WITH THE CURE ON — the worst way in which this
       cure could fail.  ⇒ The box above `p_scena_ferma_non_scatta`.

    ⛔ No `netem`: here the fault has nothing to do with it: the case is a desktop that does not
       change, that is the NORMAL case of someone reading a page.  ⇒ The
       lock is not needed, and it is not taken: it belongs to the machine, not to me.
    """
    _log("TEST 4-nuova · ⛔⛔ THE STILL SCENE with the cure on (threshold %d ms)"
         % soglia_ms)
    print("   `[M]` the still scene delivers 1 frame in 30 s and then zero:")
    print("   Mutter's `RecordVirtual` delivers only on CHANGE.  ⛔ If the stall")
    print("   count started there, the cure would throw out whoever looks at a")
    print("   still desktop — and not sometimes: after the threshold, every time.")
    v = _voci("4-nuova · the still scene (threshold %d ms)" % soglia_ms,
              soglia_stallo_ms=soglia_ms, secondi=a.scena_s)
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    va, perche = cure_come_voglio(stato, linea_morta="accesa",
                                  stallo_ms=soglia_ms)
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "P-scena-ferma", _muto(perche))
    # ⛔ The scene is SWITCHED OFF, and we check it is off: a scene left
    #    on would make this test pass for the wrong reason.
    B76.scena_spegni()
    rc, out, _ = root("bash -c \"pgrep -u %d -f '04-b30-scena --uscita' | wc -l\""
                      % UID_B)
    v["scene_vive"] = out.strip()
    if out.strip() not in ("0", ""):
        return _predica(v, "P-scena-ferma",
                        _muto("⚠ there is still a live scene (%s): this run "
                              "is not «still scene»" % out.strip()))
    _ok("no live scene: the desktop does not change")
    riga0 = riga0_pulita()
    _inf("⏳ %g s of session with a STILL SCENE" % a.scena_s)
    # ⛔ Without a trace: here there is nothing to reduce — the point is precisely that
    #    no frames arrive — and a reader that refuses would give the
    #    test the look of a fault.
    n = B70.giro("p4n-scena-ferma-%d" % soglia_ms, "ferma", B70.TELA_PIENA,
                 a.scena_s, con_traccia=False)
    n["testimoni"] = B76.testimoni_connessione(riga0, n)
    lm = leggi_linea_morta(riga0)
    B76.stampa_testimoni(n["testimoni"])
    stampa_scatti(lm)
    _inf("CLIENT %s · %s real s"
         % (json.dumps(n.get("dal_cliente"), ensure_ascii=False),
            n.get("secondi_veri")))
    v["scatti"] = lm
    v["giro"] = {k: n.get(k) for k in ("dal_cliente", "secondi_veri",
                                       "testimoni")}
    salva("p4n-scena-ferma-%d" % soglia_ms, v)
    _predica(v, "P-scena-ferma · ⛔⛔ %g s of STILL desktop, threshold %d ms"
             % (a.scena_s, soglia_ms),
             p_scena_ferma_non_scatta(lm, n["testimoni"], a.scena_s, soglia_ms))
    return v


def prova1_taratura(a):
    """⭐ THE CALIBRATION — and it closes the hole of the reconstruction (⇒ the box at
       the top).  Same `casa-cattiva`, but with `--linea-morta-permille 1`: at
       that threshold the cure fires for sure, and firing **prints the
       `permille=` that it computed itself**, on its own window, with its own
       arithmetic.  ⇒ It is the only way to read the DECLARED fraction without
       redoing it by hand.

    ⛔ It does not judge: it MEASURES and reports.  The judgement on the threshold belongs to `P1b`.
    """
    _log("TEST 1 · THE CALIBRATION — how much the DECLARED fraction is worth, told by the "
         "PRODUCT")
    v = _voci("1-taratura · the declared fraction, read from the product",
              profilo="casa-cattiva")
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    va, perche = cure_come_voglio(stato, linea_morta="accesa", stallo_ms=1)
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "calibration", _muto(perche))
    p = profilo("casa-cattiva")
    with rete_guasta(B76._regole(p[1]), 240) as riletta:
        v["regola"] = riletta
        s, _g = sonda("casa-cattiva")
        v["sonda"] = s
        usc = B76.scena_accendi("barra")
        _inf("«barra» scene on monitor %s" % usc)
        riga0 = riga0_pulita()
        n = B70.giro("p1-taratura", "barra", B70.TELA_PIENA, a.taratura_s)
        lm = leggi_linea_morta(riga0)
        fin = leggi_finestre(riga0, soglia_permille=1)
        B76.scena_spegni()
    stampa_scatti(lm)
    stampa_finestre(fin)
    v["scatti"], v["dichiarata"] = lm, fin
    if lm.get("esito") == "letto" and lm["scatti"]:
        _ok("⭐ THE PRODUCT HAS ITS SAY: on the window in which it decided, the "
            "DECLARED fraction was **%s‰** (%s lost out of %s sent in %s "
            "ms) — and my reconstruction from the `rete-quic` lines gave max %s‰, "
            "median %s‰"
            % (lm.get("permille"), lm.get("persi"), lm.get("spediti"),
               lm.get("finestra_ms"), fin.get("permille_max"),
               fin.get("permille_mediano")))
        v["permille_dal_prodotto"] = lm.get("permille")
    else:
        _dub("⚠ at 1‰ the cure did not fire: the calibration did not produce the "
             "product's number, and only the reconstruction remains")
    salva("p1-taratura", v)
    return v


# ═══════════════════════════════════════════════════════════════════════════
# TEST 2 · THE REAL FIRING
# ═══════════════════════════════════════════════════════════════════════════
def prova2(a):
    _log("TEST 2 · THE REAL FIRING — `raffica-forte`, and it MUST fire")
    print("   `[M]` 11.10 % loss in bursts: with the cure off the screen stays")
    print("   frozen 14.26 s out of 25 (grid of 09-b76).  ⇒ The cure must fire,")
    print("   with causa=stallo, and the wire must drop.")
    v = _voci("2 · the real firing", profilo="raffica-forte", secondi=a.corti)
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    va, perche = cure_come_voglio(stato, linea_morta="accesa",
                                  stallo_ms=LM_STALLO_MS)
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "P2 · the real firing", _muto(perche))
    p = profilo("raffica-forte")
    with rete_guasta(B76._regole(p[1]), a.corti + 400) as riletta:
        v["regola"] = riletta
        s, (pg, perche_g) = sonda("raffica-forte")
        v["sonda"], v["guasto"] = s, {"passa": pg, "perche": perche_g}
        usc = B76.scena_accendi("barra")
        _inf("«barra» scene on monitor %s" % usc)
        riga0 = riga0_pulita()
        n = B70.giro("p2-raffica-forte", "barra", B70.TELA_PIENA, a.corti)
        n["testimoni"] = B76.testimoni_connessione(riga0, n)
        lm = leggi_linea_morta(riga0)
        fin = leggi_finestre(riga0)
        sf = leggi_sfratto(riga0)
        B76.scena_spegni()
    B70.stampa_giro(n)
    B76.stampa_consegna(n)
    stampa_scatti(lm)
    stampa_finestre(fin)
    # ⭐ From when the slot was taken to when the cure decided: it is
    #   the SERVER's clock, and the two instants are in the same log.
    secondi = None
    if lm.get("esito") == "letto" and lm["scatti"] and sf.get("righe_preso"):
        secondi = dt_registro(lm["righe"][0]["riga"], sf["righe_preso"][0])
    v["secondi_a_scatto"] = secondi
    _inf("WHEN    fired %s s after the slot had been taken"
         % (("%.2f" % secondi) if secondi is not None else "?"))
    v["scatti"], v["dichiarata"] = lm, fin
    v["giro"] = {k: n.get(k) for k in ("fps", "esito", "dal_cliente",
                                       "secondi_veri", "consegna")}
    salva("p2", v)
    _predica(v, "P2 · the cure FIRES on the burst, with causa=stallo",
             p2_scatta_sullo_stallo(lm, s, secondi))
    return v


# ═══════════════════════════════════════════════════════════════════════════
# TEST 3 · SILENCE, AND THE PRICE OF THE PINGs
# ═══════════════════════════════════════════════════════════════════════════
def prova3(a, acceso):
    come = "ON" if acceso else "OFF"
    _log("TEST 3 · SILENCE — client killed with `kill -9`, cure %s" % come)
    print("   ⛔ `-9` and not a farewell: the goodbye does NOT leave, and for the server it is")
    print("      identical to a LOST goodbye — that is, it is the real case.")
    v = _voci("3 · silence (cure %s)" % come, acceso=acceso)
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    va, perche = cure_come_voglio(
        stato, linea_morta=("accesa" if acceso else "spenta"),
        silenzio_s=(LM_SILENZIO_S if acceso else None))
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "P3 · silence", _muto(perche))
    ripulisci_clienti()
    # ⛔ The `netem` is there even without a fault: it is what carries the byte
    #    COUNTER, and without a counter «the real traffic of a still session» cannot be
    #    measured.  ⚠ `limit 20000` and nothing else — and the `liscio` profile of 09-b76
    #    checks that that queue drops nothing of its own.
    with rete_guasta(B76._regole([]), 400) as riletta:
        v["regola"] = riletta
        # ⭐ Scene OFF: «with a still session» means the desktop does not
        #   move, or what I measure is the video.
        B76.scena_spegni()
        riga0 = riga0_pulita()
        cliente_in_sottofondo(UTENTE, DENTRO_LAV + "/parola", 400,
                              "p3-%s" % ("acceso" if acceso else "spento"))
        preso = aspetta_riga(riga0, ["slot TAKEN by %s " % UTENTE], 120)
        if not preso:
            ripulisci_clienti()
            return _predica(v, "P3 · silence",
                            _muto("the session did not open in 120 s: I have "
                                  "nothing to kill"))
        _ok("session open: %s" % preso[-1][:120])
        _inf("⏳ %g s of wire clock with a STILL session" % a.orologio_s)
        oro = orologio_gira(a.orologio_s)
        stampa_orologio(oro, come)
        v["orologio"] = oro
        salva("p3-orologio-%s" % ("acceso" if acceso else "spento"), oro)
        pid = cliente_pid(UTENTE)
        _inf("the client is pid %s on the host (⛔ `enter.sh` is a chroot)" % pid)
        t_kill = uccidi(pid)
        _inf("KILLED  with -9 at %s (SERVER clock)" % (t_kill or "?"))
        v["t_kill"] = t_kill
        righe = aspetta_riga(riga0, ["linea-morta "],
                             tetto=(a.attesa_scatto if acceso else 25.0))
        lm = leggi_linea_morta(riga0)
        # ⭐ AND RIGHT AFTER: is the slot free again?  It is the other half of the
        #   ghost, and the answer of the DEAD LINE (not of the eviction).
        posto = None
        if acceso:
            righe_p, coda = B78.misura(giri=1, fino="sessione", tetto=20,
                                       riprova=a.riprova_s)
            v["apertura_dopo_scatto"] = righe_p
            if righe_p:
                r = righe_p[0]
                posto = (r.get("attesa_posto_ms") if r.get("attesa_posto_ms")
                         is not None else 0)
                _inf("SLOT    after the firing: outcome «%s», wait for the slot %s ms"
                     % (r.get("esito"), r.get("attesa_posto_ms")))
        sf = leggi_sfratto(riga0)
        ripulisci_clienti()
    stampa_scatti(lm)
    stampa_sfratto(sf)
    if lm.get("esito") == "letto" and lm["scatti"] and t_kill:
        v["secondi_dal_kill"] = dt_registro(lm["righe"][0]["riga"], t_kill)
        _inf("WHEN    fired %.2f s after the `kill -9` (server clock) · "
             "the line says silenzio_ms=%s"
             % (v["secondi_dal_kill"] or -1, lm.get("silenzio_ms")))
    v["scatti"], v["sfratto"] = lm, sf
    salva("p3-%s" % ("acceso" if acceso else "spento"), v)
    if acceso:
        _predica(v, "P3 · the cure fires on SILENCE at its threshold",
                 p3_scatta_sul_silenzio(lm, LM_SILENZIO_S * 1000))
    else:
        # ⛔ With the cure off the firing must NOT be there: it is half of I6, and it is
        #    judged with the predicate of I6, not with this one.
        _predica(v, "P3/I6 · with the cure OFF silence closes nothing",
                 p6_i_predefiniti_non_cambiano_niente(lm, sf, stato, None,
                                                      "(no profile)"))
    acc = carica("p3-orologio-acceso")
    spe = carica("p3-orologio-spento")
    if acc and spe:
        _predica(v, "P3b · ⚠ the DECLARED price of the PINGs (%.2f kbit/s)"
                 % COSTO_PING_DICHIARATO_KBIT_S, p3b_costo_dei_ping(acc, spe))
    else:
        _dub("P3b · the price of the PINGs: I have only one of the two measurements "
             "(on=%s, off=%s) — it is judged when both are there"
             % (bool(acc), bool(spe)))
    return v


# ═══════════════════════════════════════════════════════════════════════════
# TEST 4 · THE EVICTION   ·   TEST 5 · TWO DIFFERENT USERS
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔⛔ AND HERE THERE IS ONE THING TO SAY BEFORE MEASURING, or the two tests would measure
#     the wrong cure: **the two cures overlap**.  With the dead line
#     on the ghost vanishes at 10 s (the connection closes, and closing
#     leaves the slot); the eviction is recommended at 15 s.  ⇒ With both
#     on the eviction would NEVER fire in this scenario, and a bench that
#     turned them on together would measure the dead line calling it eviction.
#     ⇒ Tests 4 and 5 run with `--sfratto-ms 15000` and the DEAD LINE OFF.
def _fantasma(a, chi_chiede, parola_dentro_dir, attesa_prima=0.0):
    """The common piece: a client of `%s` takes the slot, dies of `-9`, and then
       someone asks for that slot.  It returns the numbers, not the judgements.""" % UTENTE
    ripulisci_clienti()
    riga0 = riga0_pulita()
    cliente_in_sottofondo(UTENTE, DENTRO_LAV + "/parola", 400, "p4-vittima")
    preso = aspetta_riga(riga0, ["slot TAKEN by %s " % UTENTE], 120)
    if not preso:
        ripulisci_clienti()
        return {"esito": "⛔ the victim's session did not open in 120 s"}
    _ok("the slot belongs to %s: %s" % (UTENTE, preso[-1][:120]))
    pid = cliente_pid(UTENTE)
    t_kill = uccidi(pid)
    _inf("KILLED  pid %s with -9 at %s (SERVER clock)" % (pid, t_kill))
    if attesa_prima:
        _inf("⏳ I wait %g s before knocking: so the occupant is already past "
             "the eviction threshold, and if the eviction could fire "
             "it would fire" % attesa_prima)
        time.sleep(attesa_prima)
    # ⛔ `09-b78-apertura.py --riprova-0f`: it TIMES the denied slot instead of
    #    counting it — `GIA_ATTIVA_REMOTA` is a state that PASSES, and a yes/no would
    #    make it look like a permanent fault.
    ute, dl = B78.UTENTE, B78.DENTRO_LAV
    try:
        B78.UTENTE, B78.DENTRO_LAV = chi_chiede, parola_dentro_dir
        righe, coda = B78.misura(giri=1, fino="sessione", tetto=20,
                                 riprova=a.riprova_s)
    finally:
        B78.UTENTE, B78.DENTRO_LAV = ute, dl
    sf = leggi_sfratto(riga0)
    n = {"esito": "misurato", "t_kill": t_kill, "aperture": righe,
         "coda": coda[-400:], "sfratto": sf, "chi_chiede": chi_chiede}
    r = righe[0] if righe else {}
    n["esito_apertura"] = r.get("esito")
    n["attesa_posto_ms"] = r.get("attesa_posto_ms")
    n["entrato"] = bool(r.get("esito", "").startswith("aperta"))
    # ⭐ «At which second it gets in», on the SERVER's clock: the last `slot TAKEN`
    #   after `riga0` is that of whoever knocked.
    if sf.get("presi", 0) >= 2 and t_kill:
        n["secondi_a_entrare"] = dt_registro(sf["righe_preso"][-1], t_kill)
    ripulisci_clienti()
    return n


def prova4(a, sfratto_ms):
    come = ("--sfratto-ms %d" % sfratto_ms) if sfratto_ms else "eviction OFF"
    _log("TEST 4 · THE GHOST EVICTION — %s" % come)
    print("   `[M]` today it takes 30.5 s and 11 refusals: the wire drops, the user")
    print("   retries, and for half a minute is told «you already have an active session")
    print("   elsewhere» — which for them is FALSE: that session is theirs.")
    v = _voci("4 · the eviction (%s)" % come, sfratto_ms=sfratto_ms)
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    # ⛔ The dead line must be OFF: see the box above `_fantasma`.
    va, perche = cure_come_voglio(stato, linea_morta="spenta",
                                  sfratto_ms=sfratto_ms)
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "P4 · the eviction", _muto(perche))
    n = _fantasma(a, UTENTE, DENTRO_LAV)
    v["fantasma"] = n
    if n.get("esito") != "misurato":
        return _predica(v, "P4 · the eviction", _muto(n.get("esito")))
    stampa_sfratto(n["sfratto"])
    _inf("SCALE   %d refusals («slot DENIED») · outcome «%s» · the slot became "
         "free again after %s s (server clock) · the client waited %s ms"
         % (n["sfratto"]["rifiuti"], n.get("esito_apertura"),
            ("%.2f" % n["secondi_a_entrare"]) if n.get("secondi_a_entrare")
            is not None else "?", n.get("attesa_posto_ms")))
    salva("p4-%d" % sfratto_ms, v)
    if not sfratto_ms:
        # ⛔ It is the REFERENCE, not a test: here there is no cure to
        #    judge, there is the number against which the gain is measured.
        _inf("⭐ this is the REFERENCE (cure off): %s s and %d refusals"
             % (("%.2f" % n["secondi_a_entrare"]) if n.get("secondi_a_entrare")
                is not None else "?", n["sfratto"]["rifiuti"]))
        # ⚠ Here the dead line is off by construction (`cure_come_voglio`
        #   already demanded it), and in this run there is no `netem`: there is
        #   nothing that could have made it fire.  ⇒ An EMPTY and READ
        #   reduction is passed, and only the eviction is left to judge.
        _predica(v, "P4/I6 · with the eviction OFF there is no eviction",
                 p6_i_predefiniti_non_cambiano_niente(
                     {"esito": "letto", "scatti": 0, "righe": [],
                      "chiuse_dal_trasporto": 0},
                     n["sfratto"], stato, None, "(no profile)"))
        return v
    rif = carica("p4-0")
    rif_s = ((rif or {}).get("fantasma") or {}).get("secondi_a_entrare")
    _predica(v, "P4 · the EVICTION frees the slot at the threshold",
             p4_lo_sfratto_libera_il_posto(n["sfratto"], sfratto_ms,
                                           n.get("secondi_a_entrare"), rif_s))
    return v


def prova5(a):
    _log("TEST 5 · ⛔ THE CASE THAT MUST NOT BREAK — two different users")
    print("   An eviction between different users would not be a convenience: it would be")
    print("   a security hole — anyone could make another person's desktop")
    print("   drop simply by knocking.")
    v = _voci("5 · two different users", utente_a=UTENTE, utente_b=UTENTE2)
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    va, perche = cure_come_voglio(stato, linea_morta="spenta",
                                  sfratto_ms=SFRATTO_CONSIGLIATO_MS)
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "P5 · two different users", _muto(perche))
    # ⛔ The SECOND user's password sits in a separate file, and it is put where
    #    `09-b78` looks for it (`<DENTRO_LAV>/parola`) without touching a line of it: so
    #    the second user's opening goes through the SAME tool as test 4.
    root("bash -c \"mkdir -p %s/u2 && cp %s/parola2 %s/u2/parola && "
         "chmod 600 %s/u2/parola\"" % (LAV, LAV, LAV, LAV))
    rc, out, _ = root("bash -c \"test -s %s/u2/parola && echo si || echo no\"" % LAV)
    if "si" not in out:
        return _predica(v, "P5 · two different users",
                        _muto("the second user's password is not in %s/u2/parola: "
                              "without it, I would open two sessions of the SAME user "
                              "believing I had opened two of different users" % LAV))
    # ⭐ We wait BEYOND the eviction threshold before knocking: if the eviction
    #   could fire between different users, at that point it would fire.
    n = _fantasma(a, UTENTE2, DENTRO_LAV + "/u2",
                  attesa_prima=SFRATTO_CONSIGLIATO_MS / 1000.0 + 3.0)
    v["fantasma"] = n
    if n.get("esito") != "misurato":
        return _predica(v, "P5 · two different users", _muto(n.get("esito")))
    stampa_sfratto(n["sfratto"])
    _inf("OUTCOME «%s» for «%s» · %d refusals · %d slots taken"
         % (n.get("esito_apertura"), UTENTE2, n["sfratto"]["rifiuti"],
            n["sfratto"]["presi"]))
    salva("p5", v)
    _predica(v, "P5 · ⛔ between different users there is NO eviction",
             p5_fra_utenti_diversi_non_si_sfratta(n["sfratto"], n.get("entrato"),
                                                  UTENTE, UTENTE2))
    _predica(v, "P5b · ⚠ and the «EVICTION DENIED» line? (prediction `[R]`: it does not come out)",
             p5b_la_riga_del_negato(n["sfratto"]))
    return v


# ═══════════════════════════════════════════════════════════════════════════
# TEST 6 · ⛔ THE DEFAULTS CHANGE NOTHING (I6)
# ═══════════════════════════════════════════════════════════════════════════
def prova6(a, nome):
    _log("TEST 6 · ⛔ THE DEFAULTS — «%s» with the product AS IT SHIPS TODAY" % nome)
    print("   Without `--linea-morta` and with `--sfratto-ms 0`: no firing,")
    print("   no eviction, and the profile behaves as in the grid of")
    print("   09-b76.  ⛔ It is invariant I6, and it is also the proof that the two")
    print("   cures are really OFF, not only written.")
    v = _voci("6 · the defaults (%s)" % nome, profilo=nome, secondi=a.corti)
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    va, perche = cure_come_voglio(stato, linea_morta="spenta", sfratto_ms=0)
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "P6 · I6 on «%s»" % nome, _muto(perche))
    p = profilo(nome)
    with rete_guasta(B76._regole(p[1]), a.corti + 400) as riletta:
        v["regola"] = riletta
        s, (pg, perche_g) = sonda(nome)
        v["sonda"], v["guasto"] = s, {"passa": pg, "perche": perche_g}
        usc = B76.scena_accendi("barra")
        _inf("«barra» scene on monitor %s" % usc)
        riga0 = riga0_pulita()
        n = B70.giro("p6-%s" % nome, "barra", B70.TELA_PIENA, a.corti)
        n["testimoni"] = B76.testimoni_connessione(riga0, n)
        lm = leggi_linea_morta(riga0)
        sf = leggi_sfratto(riga0)
        fin = leggi_finestre(riga0)
        B76.scena_spegni()
    B70.stampa_giro(n)
    B76.stampa_consegna(n)
    B76.stampa_testimoni(n["testimoni"])
    stampa_scatti(lm)
    stampa_sfratto(sf)
    stampa_finestre(fin)
    fps, da_dove = fps_del_giro(n)
    _inf("RATE    %s frames/s (%s)" % (fps, da_dove))
    n2 = dict(n)
    n2["fps"] = fps
    v["giro"] = {k: n.get(k) for k in ("fps", "esito", "dal_cliente",
                                       "secondi_veri", "consegna")}
    v["fps"], v["scatti"], v["sfratto"], v["dichiarata"] = fps, lm, sf, fin
    salva("p6-%s" % nome, v)
    _predica(v, "P6 · ⛔ I6: with the defaults «%s» is identical to before" % nome,
             p6_i_predefiniti_non_cambiano_niente(lm, sf, stato, n2, nome))
    return v


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE FOUR SERVER CONFIGURATIONS — and why there are four
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ It is not a convenience: **the two cures overlap**, and turning them on together
#    would make one measure the first calling it the second (⇒ the box above
#    `_fantasma`).  ⇒ Every test runs on the configuration that ISOLATES the cure it
#    measures, and `cure_come_voglio()` refuses if the server is not on it.
CONFIGURAZIONI = {
    "A": ("--linea-morta",
          "the DEAD LINE on with the defaults (stall 5 000 ms, silence 10 s) "
          "and the eviction OFF — tests 1, 2, 3, raffica-1 and still scene"),
    "C": ("--sfratto-ms %d" % SFRATTO_CONSIGLIATO_MS,
          "the EVICTION on and the dead line OFF — tests 4 and 5, and the dead "
          "line must be off or the ghost would vanish at 10 s because of the other "
          "cure and the eviction would never fire"),
    "D": ("--sfratto-ms 0",
          "⛔ THE DEFAULTS, that is the product as it ships today — test 6, "
          "the reference of test 4 and the off half of test 3"),
}


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", nargs="?",
                   choices=["terreno", "p1", "p1m", "p1c", "p1t", "p2", "p3",
                            "pr1", "psf", "psani", "p4", "p5", "p6",
                            "tutte", "rimetti", "stato"])
    p.add_argument("--certifica", action="store_true",
                   help="⭐ the positive control: proves that the bench can see "
                        "the defects it looks for. It does not touch the test machine")
    p.add_argument("--secondi", type=int, default=600,
                   help="the window of test 1 — ⛔ ten minutes, and it is the "
                        "number the user asked for")
    p.add_argument("--corti", type=int, default=60,
                   help="the window of the short runs (tests 2 and 6)")
    p.add_argument("--taratura-s", type=int, default=40)
    p.add_argument("--scala-s", type=int, default=120,
                   help="the window of the steps of the stall scale — ⚠ "
                        "shorter than that of test 1, and the ratio must be "
                        "stated")
    p.add_argument("--scena-s", type=float, default=90.0,
                   help="how long the STILL SCENE session lasts")
    p.add_argument("--scena-soglia-stretta-ms", type=int, default=1000,
                   help="⭐ the stall threshold with which the still scene is "
                        "retried: if the count does not start at 1 s, it never starts")
    p.add_argument("--orologio-s", type=float, default=60.0,
                   help="how long the measurement of traffic with a still session lasts")
    p.add_argument("--attesa-scatto", type=float, default=45.0,
                   help="how many seconds I wait for the `linea-morta` line after the -9")
    p.add_argument("--riprova-s", type=float, default=75.0,
                   help="how long the second client keeps knocking at the slot "
                        "(09-b78 `--riprova-0f`)")
    p.add_argument("--attesa", type=int, default=1800,
                   help="how many seconds I wait for the netem lock")
    p.add_argument("--salta-riaccensione", action="store_true",
                   help="⚠ does not restart the server: use it ONLY when it is already "
                        "in the right configuration, and `cure_come_voglio()` "
                        "checks it all the same")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if not a.passo:
        p.error("a step is needed, or --certifica")

    os.makedirs(FUORI, exist_ok=True)
    importa()

    if a.passo in ("rimetti", "stato"):
        _log("the test machine's network — dev «%s», port %d" % (DEV, PORTA))
        ok = RETE.rimetti()
        _inf("ports NOT mine: %s" % vicine())
        _inf("the cures, as the server declares them: %s"
             % json.dumps(stato_delle_cure(), ensure_ascii=False)[:400])
        return 0 if ok else 2

    _log("09-b81 · THE TWO CURES — port %d · user %s (uid %d) · dev «%s»"
         % (PORTA, UTENTE, UID_B, DEV))
    print("   ⛔ «%s» (ssh + the user's session) is NOT touched" % VIETATA)
    print("   ⛔ ports 7900, 7910 and 7920 are counted and not touched")
    print("   --  «%s» before: %s" % (DEV, RETE.qdisc() or "(none)"))
    if not preparati():
        return 2
    if not B70.terreno_controlla():
        return 2
    if a.passo == "terreno":
        _ok("the ground is there, and it is mine")
        return 0

    def configura_stallo(ms):
        """⛔ An off-catalogue configuration, and for one case only: the still
           scene with the narrow threshold.  ⚠ `cure_come_voglio()` rechecks it
           inside the test, like all the others."""
        if a.salta_riaccensione:
            _dub("⚠ I do NOT restart the server (--salta-riaccensione)")
            return True
        return accendi_server(
            "--linea-morta --linea-morta-stallo-ms %d" % ms,
            "the dead line with the stall threshold NARROWED to %d ms — the "
            "still scene holding the knife by the handle" % ms)

    def configura(chiave):
        if a.salta_riaccensione:
            _dub("⚠ I do NOT restart the server (--salta-riaccensione): I trust "
                 "`cure_come_voglio()`, which will refuse if it is not %s" % chiave)
            return True
        opz, perche = CONFIGURAZIONI[chiave]
        return accendi_server(opz, "configuration %s — %s" % (chiave, perche))

    esiti = []
    try:
        # ⛔⛔ THE ORDER IS NOT A CONVENIENCE: every test runs on the
        #     configuration that ISOLATES the cure it measures, and the tests that
        #     share the same configuration are kept together, or one
        #     would pay for a restart (and a priming session) for nothing.
        #     ⚠ And `cure_come_voglio()` rechecks all the same, inside every test:
        #       the order is a saving, not a guarantee.
        tutte = (a.passo == "tutte")
        # ── configuration A: the dead line on with the defaults ─────────────
        if a.passo in ("p1", "p2", "p3", "pr1", "psf", "tutte"):
            if configura("A"):
                if a.passo in ("p1", "tutte"):
                    esiti.append(prova1(a))
                if a.passo in ("p2", "tutte"):
                    esiti.append(prova2(a))
                if a.passo in ("pr1", "tutte"):
                    esiti.append(prova_raffica1(a))
                if a.passo in ("psf", "tutte"):
                    # ⛔ The still scene at the threshold IN FORCE…
                    esiti.append(prova_scena_ferma(a, LM_STALLO_MS))
                if a.passo in ("p3", "tutte"):
                    esiti.append(prova3(a, acceso=True))
        # ── and the still scene holding the knife by the handle: the same
        #    test with a MUCH narrower threshold.  If the count does not start
        #    there, it does not start at any threshold.
        if a.passo in ("psf", "tutte"):
            if configura_stallo(a.scena_soglia_stretta_ms):
                esiti.append(prova_scena_ferma(a, a.scena_soglia_stretta_ms))
        # ── the MARGIN of test 1: the scale that tracks down the maximum stall ─
        if a.passo in ("p1m", "tutte"):
            esiti.append(prova1_margine(a))
        # ── ⭐ and the fourth number of the report: the stall of the HEALTHY profiles.
        #    ⛔ It is not deduced from `casa-cattiva`: «a healthy line cannot do
        #    worse» is a reasoning, and the report asks for a measurement.
        if a.passo in ("psani", "tutte"):
            esiti.append(prova_margine(a, RIFERIMENTO_SANO, [1000, 500],
                                       etichetta="sani"))
        if a.passo == "p1t":
            if configura("A"):
                esiti.append(prova1_taratura(a))
        # ── configuration C: the eviction on, the dead line OFF ─────────────
        if a.passo in ("p4", "p5", "tutte"):
            if configura("C"):
                if a.passo in ("p4", "tutte"):
                    esiti.append(prova4(a, SFRATTO_CONSIGLIATO_MS))
                if a.passo in ("p5", "tutte"):
                    esiti.append(prova5(a))
        # ── configuration D: ⛔ the defaults, the product as it ships today ──
        if a.passo in ("p6", "p3", "p4", "p1c", "tutte"):
            if configura("D"):
                # ⛔ FIRST the control of test 1: it is the one that makes valid (or
                #    withdraws) the red of test 1, and it must be read together with it.
                if a.passo in ("p1c", "tutte"):
                    esiti.append(prova1_controllo(a))
                if a.passo in ("p6", "tutte"):
                    for nome in ("casa-cattiva", "raffica-forte"):
                        esiti.append(prova6(a, nome))
                if a.passo in ("p3", "tutte"):
                    esiti.append(prova3(a, acceso=False))
                if a.passo in ("p4", "tutte"):
                    esiti.append(prova4(a, 0))
        # ⛔ And the gain is counted at the end: («how much did the
        #    ghost drop») needs both numbers, and when test 4 with the
        #    cure ran the reference was not there yet.
        if tutte:
            rif, cur = carica("p4-0"), carica("p4-%d" % SFRATTO_CONSIGLIATO_MS)
            if rif and cur:
                _log("THE GAIN — «how much did the ghost drop»")
                rs = (rif.get("fantasma") or {}).get("secondi_a_entrare")
                cs = (cur.get("fantasma") or {}).get("secondi_a_entrare")
                rr = ((rif.get("fantasma") or {}).get("sfratto") or {}).get("rifiuti")
                cr = ((cur.get("fantasma") or {}).get("sfratto") or {}).get("rifiuti")
                _inf("eviction OFF: %s s and %s refusals · eviction at %d ms: %s s "
                     "and %s refusals" % (rs, rr, SFRATTO_CONSIGLIATO_MS, cs, cr))
                esiti.append({"prova": "the gain", "predicati": [],
                              "riferimento_s": rs, "con_cura_s": cs,
                              "rifiuti_riferimento": rr, "rifiuti_con_cura": cr})
    finally:
        ripulisci_clienti()
        B76.scena_spegni()
        rimessa = RETE.rimetti()
        try:
            LUC.molla(CHI, dillo=False)
        except Exception:
            pass

    salva("esiti", esiti)
    _log("THE VERDICT")
    rossi, muti = [], []
    for v in esiti:
        for d in v["predicati"]:
            if d["passa"] is False:
                rossi.append("%s · %s — %s" % (v["prova"], d["predicato"],
                                               d["perche"][:120]))
            elif d["passa"] is None:
                muti.append("%s · %s — %s" % (v["prova"], d["predicato"],
                                              d["perche"][:120]))
    _inf("%d tests run · %d red · %d not judged · outcomes in %s"
         % (len(esiti), len(rossi), len(muti), _fuori("esiti")))
    for r in rossi:
        _ko(r)
    for m in muti:
        _dub(m)
    if not rimessa:
        _ko("⛔ the network did NOT go back as it was: put it back by hand with «rimetti»")
        return 2
    if rossi:
        return 1
    if muti:
        return 3
    _ok("⭐ all the predicates did what was written beforehand")
    return 0


if __name__ == "__main__":
    sys.exit(principale())
