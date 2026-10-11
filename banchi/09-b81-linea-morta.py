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
  exist as a frame around it.  If `bad-home` — `[M]` 1.71 % loss, 7.8-10.2
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
    · the DECLARED one — rebuilt from the `quic-net` lines, which carry
      `lost_d`, `sent_d` and `since_ms`, that is exactly the three numbers with which
      `dead_line_judge()` decides.  ⇒ ITS guards are applied
      (`sent_d >= 200`, `since_ms >= 1000`) and we count whether two windows in a row
      would ever have broken through 50‰.
  ⛔ If the DECLARED one breaks the threshold on a line that HOLDS, the threshold is
     wrong **and it must be said**, not worked around: it is predicate `p1b`.
  ⚠ `[?]` The reconstruction is a declared APPROXIMATION, and on the wrong
    cautious side: the `quic-net` lines are silent when nothing changes,
    so one of their windows can be LONGER than a second — and a
    longer window averages more, that is it **lowers** the peak.  ⇒ On its own it
    is not enough, and next to it goes the calibration (further below).

⭐ THE CALIBRATION, which closes the hole of the reconstruction: a short run on the
   SAME `bad-home` with `--linea-morta-permille 1`.  At that threshold the
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

⛔⛔ **TEST 1 — ZERO FIRINGS IN TEN MINUTES.**  `bad-home`, `--linea-morta`
     on: 9.71 frames/s, coverage **1.00** (600 s out of 600), largest gap
     **0.479 s**, client still attached at 599.88 s, no farewell.
     ⭐ And in the same run the WITNESS says `permille` median **529‰** with 392
        windows out of 392 above the old 50‰: **the old cure would have killed
        this very session**, the new one does not touch it.  It is the cleanest
        comparison this phase has — same profile, same bench, same
        ten minutes, and only the quantity the decision rests on changes.

⭐⭐ THE FOUR MAXIMUM STALLS AGAINST THE 5 000 ms THRESHOLD — and they are MEASURED, not
    «it did not fire»: the line comes out only on firing, so the same
    profile is rerun with lower and lower thresholds until one fires (`stall_ladder()`).

      profile          maximum stall         margin      gap at the CLIENT
      `delay-30`     < 500 ms (no firing)   > 10×       0.157-0.175 s
       (healthy)
      `bad-home`   < 500 ms (no firing)   > 10×       0.359-0.479 s
      `burst-1`      **1 001 ms** MEASURED  **5.0×**    0.52-3.73 s
      STILL scene      count does not start   —           (1 and 3 frames
                                                           in 90 s)

    ⭐ `burst-1` confirms the derivation with an independent number: the
       narrow side is **1.00 s**, which is exactly what the box of
       `WT_LM_STALL_MS` had used — and the margin is the declared 5.0×.

⚠ AND ONE THING TO SAY: the STALL (server, video bytes gone out) and the GAP (client,
  frames arrived) are NOT the same quantity, and the threshold is derived from the
  second while the cure measures the first.  `[M]` on `burst-1` one run gave
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
    2 · `burst-heavy` (13.19 % injected): fires at **18.95 s**,
        `cause=stall stall_ms=5008 offered=198 bytes_out=0
        video_queue=31146` — both halves true — and the wire drops.
        ⚠ The witness said `permille=133`: LOWER than `bad-home`, and
          it is yesterday's refutation seen from the other side.
    3 · silence: `silence_ms=10006`, `unanswered=12`, 10.24 s after the `kill -9`, and
        in the line `stall_ms=8 offered=0` — that is, the two causes stay separate.
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
        bad-home      1.86 - 2.15 %       **512‰** (51.2 %)   HOLDS 10 minutes
        burst-heavy    12.28 - 14.00 %      **123‰** (12.3 %)   does NOT hold

      ⇒ The one that WORKS declared four times more loss than the one that
        does not work: no threshold separates them.  ⭐ The cause: `bad-home`
        reorders **93.5 %** of the packets, and ngtcp2 counts an overtake as
        a loss.  ⚠ And it was not the connection start-up: with the first
        ten windows removed, 399 out of 399 stayed above threshold.
      ⇒ The cure was REDONE, not retuned, and `--linea-morta-permille` was
        removed.  `permille=` stays in the line as a WITNESS of the reordering.

═══ WHAT IS MEASURED, AND WITH WHAT ═══

⛔ Not one line of what already exists is rewritten.  This bench is almost entirely
   made of other people's pieces, and it DECLARES them:

     `09-b76-rete-cattiva.py`  the profiles (`bad-home`, `burst-heavy`), the
                               PROBE of the injected loss, the `netem`
                               discipline, the qdisc counters, the witnesses
                               of the connection, the reduction of delivery,
                               and through it all of `09-b70-ritmo.py`
                               (`giro()`, the §11.1 trace, the five numbers).
     `09-b78-apertura.py`      the session opening timed phase by
                               phase, and ⭐ `--retry-0f`, which **times the
                               denied slot instead of counting it** — that is, it is already
                               the tool of test 4.
     `07-b64-rete.py`          ⛔ `log_settled()`, brought in here: see
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
    (`09-b81-terreno.sh ship`, step 3).

EXIT CODES
    0   CONFORMING · 1 NOT CONFORMING (there is a red) · 2 usage/ground/network
    3   ⛔ I HAVE NOTHING TO JUDGE — a run or a predicate refused

Usage (from the laptop):
    python3 banchi/09-b81-linea-morta.py --certify     ⭐ without a machine
    python3 banchi/09-b81-linea-morta.py terrain
    python3 banchi/09-b81-linea-morta.py p1     # ⛔⛔ the false positive
    python3 banchi/09-b81-linea-morta.py p2     # the real firing
    python3 banchi/09-b81-linea-morta.py p3     # silence, and the PINGs
    python3 banchi/09-b81-linea-morta.py p4     # the eviction
    python3 banchi/09-b81-linea-morta.py p5     # ⛔ two different users
    python3 banchi/09-b81-linea-morta.py p6     # ⛔ the defaults do not change
    python3 banchi/09-b81-linea-morta.py all
    python3 banchi/09-b81-linea-morta.py restore          ⛔ and it is checked
"""
import argparse, importlib.util, json, os, re, subprocess, sys, time

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ ISOLATION, WRITTEN BEFORE ANY IMPORT THAT READS IT
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `setdefault` and not `=`: the modules I import read the environment at import,
#    and they must read MINE.  ⚠ And after the import we CHECK that they have
#    read it (`do_import()`), because a module that took another
#    agent's environment would break another bench's port — and the network is the only thing
#    that, if wrong, hurts those who have nothing to do with it.
PORT = int(os.environ.setdefault("PORT", "7960"))
ACCOUNT = os.environ.setdefault("ACCOUNT", "provanr6")
UID_B = int(os.environ.setdefault("UID_B", "1060"))
ACCOUNT2 = os.environ.setdefault("ACCOUNT2", "provanr6b")
UID_B2 = int(os.environ.setdefault("UID_B2", "1061"))
MACHINE = os.environ.setdefault("MACHINE", "nicfio@192.168.0.2")
SUDO_PASSWORD = os.environ.setdefault("SUDO_PASSWORD", "nicfio")
ADDR = os.environ.setdefault("ADDR", "192.168.0.2")
WORKDIR = os.environ.setdefault("WORKDIR", "/media/REMOTIX/tmp/09nr6")
TREE_DIR = os.environ.setdefault("TREE", "/media/REMOTIX/src/09nr6-src")
INSIDE_TREE = os.environ.setdefault("INSIDE_TREE", "/srv/src/09nr6-src")
INSIDE_WORK = os.environ.setdefault("INSIDE_WORK", "/srv/remotix/tmp/09nr6")
# ⛔ The probe's ports are MINE and are chosen on the fly (see `09-b76`): another
#    agent may start a server while I run.
os.environ.setdefault("PROBE_PORTS", "7969,7968,7967,7966,7965")
os.environ.setdefault("SHM", "/09nr6")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.setdefault(
    "OUT", "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX/"
             "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad/09-b81")
UNIT = os.environ.get("UNIT", "remotix-%d" % PORT)

VIETATA = "enp7s0"     # ⛔ ssh and the user's session go through it: NEVER
DEV = "lo"
# ⛔ The ports that are NOT mine: they are COUNTED and not touched.
NEARBY_PORTS = ("7900", "7910", "7920", "7700", "7730")

GREEN, RED, YELLOW, GRAY = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (GREEN, GRAY, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (RED, GRAY, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (YELLOW, GRAY, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _mute(p): return (None, p)


def _load(name, fpath):
    spec = importlib.util.spec_from_file_location(name, fpath)
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
# line (`fixes_state()`) and compared with these.
LM_STALL_MS = 5000         # `WT_LM_STALL_MS`  — 5.0 s of frozen image
LM_SILENCE_S = 10          # `WT_LM_SILENCE_S`
LM_MIN_PACKETS = 200      # `WT_LM_MIN_PACKETS` — guard of the WITNESS
LM_WINDOW_MS = 1000       # `WT_LM_WINDOW_MS`   — ditto
LM_MIN_PROVE = 2            # `WT_LM_MIN_PROVE`
# ⛔⛔ AND `WT_LM_PERMILLE` NO LONGER EXISTS, neither the constant nor the option: the
#     loss fraction was refuted by this very bench on 23 August
#     2026 (⇒ the box at the top) and went down from JUDGE to WITNESS.
#     ⚠ `permille=` stays in the firing line, but it no longer has a threshold:
#       whoever looked for `threshold_permille=` would not find it, and that is right.
RECOMMENDED_EVICTION_MS = 15000   # `DEFAULT_EVICTION` = `SILENCE / 2`
SILENCE_MS = 30000              # `SILENCE` of `rcp.c` — the clock of §5.3

# ── the BENCH's thresholds, in one place only and each with its reason ────
#
# ⛔ «The line HOLDS» is not an opinion: it is the number below which test 1
#    has proved nothing, because I would no longer have a user who was
#    working NOT to throw out.  ⚠ *Sufficient, not exact*: `[M]` 23 Aug
#    `bad-home` gives 7.8-10.2 frames/s and 1.48 % gives 5.5 with coverage
#    1.00 — 5.0 sits below both, and below that the line no longer carries.
HOLDING_LINE_FPS = 5.0
# ⛔ Below this number of valid windows the reconstruction of the declared fraction is not
#    a measurement: ten minutes at one window per second give ~600.
#    ⚠ Now it serves only DIAGNOSIS: the fraction no longer judges anything.
MIN_VALID_WINDOWS = 60
# ⛔⭐ THE MINIMUM STALL MARGIN — how far the threshold must sit above the
#    worst stall observed on a line that HOLDS.
#    ⚠ *Sufficient, not exact*: the cure declares itself 5.0× above the empty
#      second of `burst-1` and 10× above the 0.50 s of `bad-home`.  Two is
#      half the narrower of those two, and it is the point below which the
#      threshold begins to look like a lucky number — and erring
#      low means throwing out someone who is working, which cannot be undone.
MIN_STALL_MARGIN = 2.0
# ⚠ AND THESE TWO SERVE ONLY DIAGNOSIS, not a judgement: the reconstruction
#   of the DECLARED fraction stays in the bench because it is the number that
#   REFUTED the old cure, and continuing to print it next to the stall is the
#   way to show that the reordering is still there and that it now decides
#   nothing.  ⛔ The 50‰ here is no longer «the threshold»: it is the yardstick with which we
#   look at the same number as back then, so as to compare it with that run.
PERMILLE_DIAGNOSIS = 50
DIAGNOSIS_WINDOWS = 2
# ⭐ The scale with which the maximum stall is TRACKED DOWN when the cure does NOT fire:
#    the `dead-line` line comes out only on firing, so «it did not fire»
#    alone does not say BY HOW MUCH it did not fire.  ⇒ We retry with lower and lower
#    thresholds until one fires, and the number that comes out is a true `stall_ms`
#    measured by the product.  ⛔ Between the lowest that does NOT fire and the highest
#    that fires, the maximum stall is pinned.
STALL_LADDER_MS = [2000, 1000, 500]
# ⭐ How many windows count as «the connection START-UP»: ten, that is
#   the first ~10 s, which is the stretch where `cwnd` opens and ngtcp2 does the bulk
#   of its loss detection with a small window.  ⚠ The number is chosen,
#   not measured: it serves to SEPARATE two stretches, not to judge one.
FIRST_WINDOWS = 10
# ⭐ The HEALTHY profile on which the reference stall is measured: `delay-30` is
#   the denominator of all of `09-b76`'s comparisons — late but IN ORDER, zero
#   loss, zero disorder.  ⚠ Not `smooth`: a profile without even a
#   delay has no RTT, and without RTT the congestion window does not fill
#   and the pacer has nothing to do — that is, it is not a line, it is a short circuit.
HEALTHY_REFERENCE = "delay-30"
# ⚠ The dead line's judgement is taken ONCE PER SECOND (`network_cycle`),
#   so a firing cannot come BEFORE the threshold and must not come
#   much after.  Three seconds cover the loop, the pacer queue and the `ssh`.
SILENCE_TOLERANCE_MS = 3000
# ⭐ The declared cost of the PINGs: ~130 B per round every threshold/2 seconds.
COST_PING_DECLARED_KBIT_S = 0.21
# ⚠ The eviction is a big number: we accept the delay of one retry round of the
#   client (1 s) plus the server's loop.
EVICTION_TOLERANCE_MS = 4000

# ⭐ The grid of `09-b76`, `[M]` 23 August 2026 — it is the denominator of
#    test 6: «the defaults change nothing» means *identical to this*.
GRID_B76 = {
    "bad-home": {"fps_min": 7.0, "fps_max": 11.0, "copertura_min": 0.90,
                     "why": "`[M]` 7.8-10.2 frames/s, live session, "
                               "delivery that does not stop"},
    # ⭐ `burst-1` — the exact twin of `loss-1`: same average loss,
    #   but in CLUSTERS.  `[M]` it delivers 23.94 frames/s and still had a
    #   WHOLE EMPTY SECOND: it is the case the narrow side of the
    #   stall threshold rests on, and for this reason it must be tested on its own.
    "burst-1": {"fps_min": 15.0, "fps_max": 45.0, "copertura_min": 0.90,
                  "why": "`[M]` 23.94 frames/s with a full 1.00 s "
                            "gap — it holds, and must NOT be declared dead"},
    "burst-heavy": {"consegna_si_ferma": True,
                      "why": "`[M]` delivery STOPS — 7 seconds out of 25 "
                                "saw a frame, gap 14.26 s"},
}


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ OTHER PEOPLE'S MODULES — they are imported, and THEN we check they took MY
#   environment
# ═══════════════════════════════════════════════════════════════════════════
B76 = None
B70 = None
B78 = None
NETWORK = None
LUC = None


def do_import():
    global B76, B70, B78, NETWORK, LUC
    if B76 is not None:
        return B76
    B76 = _load("b76rete", os.path.join(HERE, "09-b76-rete-cattiva.py"))
    troubles = []
    for name, my, its in (("port", PORT, B76.PORT), ("user", ACCOUNT, B76.ACCOUNT),
                           ("uid", UID_B, B76.UID_B), ("work", WORKDIR, B76.WORKDIR),
                           ("tree", TREE_DIR, B76.TREE_DIR), ("dev", DEV, B76.DEV),
                           ("forbidden", VIETATA, B76.VIETATA),
                           ("dentro_lav", INSIDE_WORK, B76.INSIDE_WORK)):
        if my != its:
            troubles.append("09-b76 %s: has «%s», mine is «%s»" % (name, its, my))
    if troubles:
        raise SystemExit("⛔ I DO NOT MEASURE: the import of 09-b76 did not take my "
                         "environment — " + " · ".join(troubles))
    # ⛔ And its `do_import()` does the rest: it loads b70, hooks the network to it with
    #    ITS checks (guardian, four-band `prio`, two `u32` filters
    #    on the port only, a `restore` that checks itself) and the lock.
    B70 = B76.do_import()
    NETWORK, LUC = B76.NETWORK, B76.LUC
    if NETWORK.PORT != PORT or NETWORK.DEV != DEV or NETWORK.VIETATA != VIETATA:
        raise SystemExit("⛔ I DO NOT TOUCH THE NETWORK: the network module has port %d, "
                         "dev «%s», forbidden «%s»"
                         % (NETWORK.PORT, NETWORK.DEV, NETWORK.VIETATA))
    B78 = _load("b78apertura", os.path.join(HERE, "09-b78-apertura.py"))
    troubles = []
    for name, my, its in (("port", PORT, B78.PORT), ("user", ACCOUNT, B78.ACCOUNT),
                           ("work", WORKDIR, B78.WORKDIR), ("tree", TREE_DIR, B78.TREE_DIR),
                           ("dentro_lav", INSIDE_WORK, B78.INSIDE_WORK)):
        if my != its:
            troubles.append("09-b78 %s: has «%s», mine is «%s»" % (name, its, my))
    if troubles:
        raise SystemExit("⛔ I DO NOT MEASURE: the import of 09-b78 did not take my "
                         "environment — " + " · ".join(troubles))
    return B76


def root(command, cap=300):
    return NETWORK.root(command, cap)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ `log_settled()` — BROUGHT FROM `07-b64-rete.py`, and that file is not
#     touched
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ THE DEFECT IT AVOIDS, `[M]` 23 August 2026 (`07-b64-rete.py:497`): the
#    closing of a session is SLOW when the pacer has a queue — that bench
#    measured **29 s** of delay on the «final count» of the profile that lost
#    the most.  ⇒ Whoever takes `line0` right after a run takes a line BEFORE
#    the previous run has finished writing itself, and reads the log of the
#    previous run believing it is theirs.
#
# ⛔⛔ AND HERE IT HURTS TWICE AS MUCH, because what I read is not a count: it is whether
#     the cure FIRED.  A `dead-line` line of the previous run read inside
#     this run's window would give *«it fired»* to a run in which nothing
#     fired — that is, test 1's false positive would be
#     MANUFACTURED BY THE BENCH.  ⚠ And the opposite direction is just as bad:
#     test 6 (the defaults) would give red on a product that behaves well.
#
# ⚠ And the second fault that box tells about holds identically here: until the
#   previous session has closed, §4.4-bis refuses the new one with
#   `0x0F ALREADY_ACTIVE_REMOTELY` — which in test 4 is PRECISELY THE PHENOMENON I
#   MEASURE.  Measuring the previous run's lock in place of mine would give a
#   true number and a made-up cause.
def count_final_counts():
    """How many «audio of …, final count» lines there are NOW in the log."""
    rc, out, _ = root("bash -c \"grep -ac 'audio of .*final count' "
                      "%s/registro.log || true\"" % WORKDIR)
    try:
        return int(out.strip())
    except Exception:
        return -1


def log_settled(cap=90.0, quiet=3.0):
    """We wait until the count of «final count» lines stays STILL for
       `quiet` seconds, and that count is returned — see the box above."""
    n = count_final_counts()
    stopped, expires = 0.0, time.time() + cap
    while time.time() < expires and stopped < quiet:
        time.sleep(1.0)
        m = count_final_counts()
        stopped = (stopped + 1.0) if m == n else 0.0
        n = m
    return n


def log_line_list():
    """⛔ No `< file` at the end of a `sudo -S`: that redirect STEALS its
       stdin and the password does not arrive — and the count returns 0 silently, that is the
       bench reads the log from the server's start believing it is reading
       its own run (`09-b76`, the box above `log_line_list`)."""
    return B76.log_line_list()


def line0_clean(cap=90.0):
    """⭐ The line from which to read THIS run, taken when the previous run has
       finished writing itself."""
    log_settled(cap=cap)
    return log_line_list()


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE LOG — the clock, and the three lines this bench reads
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Log lines begin with `HH:MM:SS.mmm ` (`src/registro.c`), and
#    it is the only clock that is right for these numbers: it is the SERVER's.
#    ⚠ A stopwatch on the laptop would also measure the `ssh`, the container and
#      the difference between two clocks — on a 10 s threshold that is half
#      the error I am looking for.
_CLOCK = re.compile(r"^(\d\d):(\d\d):(\d\d)\.(\d\d\d)\s")


def t_log(line):
    """The seconds since midnight of a log line, or `None`.

    ⚠ It returns `None` and not `0` when there is no time: a zero here would mean
      «midnight» and would be a plausible and false number (`LEZIONI.md` §1.9).
    """
    m = _CLOCK.match(line or "")
    if not m:
        return None
    return (int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
            + int(m.group(4)) / 1000.0)


def dt_log(after, before):
    """`dopo - prima` in seconds, with midnight stepped over.

    ⚠ It returns `None` if one of the two is missing: «I do not know» must not look
      the same as «zero seconds», which here would mean «it fired at once».
    """
    a, b = t_log(after), t_log(before)
    if a is None or b is None:
        return None
    d = a - b
    return d + 86400.0 if d < -43200.0 else d


def read_log(line0, pattern, how_many=400):
    """The lines of THIS run that contain `pattern` (a `grep -e … -e …`).

    ⛔ `tail -n +riga0+1` and not the whole log: the farewells, the firings and the
       denied slots of whoever ran before are not mine.
    """
    pieces = " ".join("-e '%s'" % f for f in pattern)
    rc, out, _ = root("bash -c \"tail -n +%d %s/registro.log | grep -a %s | "
                      "tail -%d\"" % (line0 + 1, WORKDIR, pieces, how_many))
    return [r for r in out.splitlines() if r.strip()]


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE `dead-line` LINE — a contract on the TEXT, and it is read as such
# ═══════════════════════════════════════════════════════════════════════════
#
# `src/webtransport.c`, `dead_line_fires()`, fixes the format as a contract:
#   1. the prefix `dead-line` is STABLE and is the first word of the body;
#   2. the second field is the origin (ADDR:PORT), without `=`;
#   3. every field is `name=value` with no spaces in the value;
#   4. ⛔ `judgement=` IS THE LAST and runs to the end of the line, spaces included;
#   5. ⛔ the fields are ALWAYS ALL there, even those the cause does not use: what
#      says which one decided is `cause=`, which is the first.
#
# ⛔ The reduction stands apart because it is the one `--certify` exercises on
#    MANUFACTURED lines: a contract on the text is tested on the text.
def reduce_dead_line(lines, read=True):
    """From the raw lines to the numbers of the FIRINGS.  ⛔ It does not judge: it reduces.

    ⛔⛔ And «zero firings» is NOT «I did not read», and it is the distinction on which
        all of test 1 depends: zero `dead-line` lines is **the result
        test 1 expects**, while a log not read is a blind bench.
        ⇒ `letto` is stated by the caller, who knows whether the `grep` went
          well, and without it this function refuses.
    """
    if not read:
        return {"outcome": "⛔ I DID NOT READ THE LOG — «zero firings» and «I did not "
                         "look» must not look the same"}
    lines = [r for r in lines if "dead-line " in r]
    n = {"outcome": "read", "notches": len(lines), "lines": []}
    for r in lines:
        body = r.split("dead-line ", 1)[1]
        judge = ""
        if "judgement=" in body:
            body, judge = body.split("judgement=", 1)
        pieces = body.split()
        d = {"provenance": pieces[0] if pieces and "=" not in pieces[0] else None}
        for p in pieces:
            if "=" in p:
                k, v = p.split("=", 1)
                d[k] = v
        d["judgement"] = judge.strip()
        d["time"] = t_log(r)
        d["line"] = r
        n["lines"].append(d)
    if lines:
        p = n["lines"][0]

        def num(k):
            try:
                return int(p.get(k))
            except (TypeError, ValueError):
                return None

        n["cause"] = p.get("cause")
        # ⭐ The three numbers on which the stall is proved or disproved: how many
        #   frames the stage gave us, how many video bytes really went
        #   out, and how many stayed at home with us.
        n["stall_ms"] = num("stall_ms")
        n["stall_threshold_ms"] = num("stall_threshold_ms")
        n["offered"] = num("offered")
        n["bytes_out"] = num("bytes_out")
        n["video_queue"] = num("video_queue")
        n["cwnd_left"] = num("cwnd_left")
        # ⚠ And the WITNESS, which no longer judges: `permille` without `soglia_`.
        n["lost"] = num("lost")
        n["sent"] = num("sent")
        n["permille"] = num("permille")
        n["window_ms"] = num("window_ms")
        n["silence_ms"] = num("silence_ms")
        n["silence_threshold_ms"] = num("silence_threshold_ms")
        n["unanswered"] = num("unanswered")
        n["cwnd"] = num("cwnd")
        n["srtt_us"] = num("srtt_us")
        n["judgement"] = p.get("judgement", "")
        n["ora_primo"] = p.get("time")
        n["cause"] = [x.get("cause") for x in n["lines"]]
    return n


def read_dead_line(line0):
    """The firings of THIS run, and the transport line that carries them out.

    ⚠ `DEAD LINE — the QUIC connection is closing` is read too: it is the half
      belonging to `trasporto.c`, and a decision taken without the wire dropping would
      be something other than what the user chose.
    """
    lines = read_log(line0, ["dead-line ", "DEAD LINE"])
    n = reduce_dead_line([r for r in lines if "dead-line " in r], read=True)
    n["chiuse_dal_trasporto"] = len([r for r in lines if "DEAD LINE" in r])
    return n


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE EVICTION — the three greppable marks, as `src/rcp.c` declares them
# ═══════════════════════════════════════════════════════════════════════════
def reduce_eviction(lines, read=True):
    """`EVICTION for silence:` · `⛔ EVICTION DENIED:` · `slot DENIED`.

    ⛔ Here too «zero» is not «I did not read» — see `reduce_dead_line`.
    """
    if not read:
        return {"outcome": "⛔ I DID NOT READ THE LOG"}
    evictions = [r for r in lines if "EVICTION for silence:" in r]
    denied = [r for r in lines if "EVICTION DENIED:" in r]
    refusals = [r for r in lines if "slot DENIED" in r]
    grabbed = [r for r in lines if "slot TAKEN" in r]
    n = {"outcome": "read", "evictions": len(evictions), "denied": len(denied),
         "refusals": len(refusals), "grabbed": len(grabbed),
         "righe_sfratto": evictions[:4], "righe_negato": denied[:4],
         "righe_rifiuto": refusals[:4], "righe_preso": grabbed[:4]}
    if evictions:
        m = re.search(r"EVICTION for silence: (\d+) ms", evictions[0])
        n["muto_ms"] = int(m.group(1)) if m else None
        n["ora_sfratto"] = t_log(evictions[0])
        # ⭐ Who was evicted: it serves test 5, where evicting the wrong
        #    user would not be a convenience but a security hole.
        m = re.search(r"the slot of (\S+) goes to the client", evictions[0])
        n["sfrattato"] = m.group(1) if m else None
    # ⭐ The silence declared inside the REFUSAL line: it is the number that
    #    whoever reads the log was missing to know whether the slot belonged to a live
    #    client or a corpse, and it comes out even with the eviction OFF.
    if refusals:
        m = re.search(r"sign of life (\d+) ms ago", refusals[-1])
        n["ultimo_rifiuto_muto_ms"] = int(m.group(1)) if m else None
        n["sfratto_dice"] = ("SPENTO" if "is switched OFF" in refusals[-1]
                             else "did NOT fire" if "did NOT fire" in refusals[-1]
                             else None)
    # ⛔ Who took the slot LAST, and at what time: it is the number of
    #    test 4 — «at which second it gets in», and on the server's clock.
    if grabbed:
        m = re.search(r"slot TAKEN by (\S+)", grabbed[-1])
        n["ultimo_preso_da"] = m.group(1) if m else None
        n["ora_ultimo_preso"] = t_log(grabbed[-1])
    return n


def read_eviction(line0):
    lines = read_log(line0, ["EVICTION", "slot DENIED", "slot TAKEN"])
    return reduce_eviction(lines, read=True)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE **DECLARED** FRACTION, rebuilt from the `quic-net` lines
# ═══════════════════════════════════════════════════════════════════════════
#
# ⇒ It is the falsifier of test 1 (⇒ the box at the top).  The
#   `quic-net` lines carry `since_ms`, `lost_d` and `sent_d`, which are exactly the
#   three numbers with which `dead_line_judge()` decides.  ⇒ ITS
#   guards are applied and we count whether two windows in a row would ever have broken the threshold.
#
# ⚠ `[?]` The approximation is declared and sits on the wrong cautious side: the
#   `quic-net` lines are silent when nothing has changed, so one of their
#   windows can be longer than a second — and averaging over more time
#   LOWERS the peak.  ⇒ On its own it does not close the question: next to it goes the
#   calibration at `--linea-morta-permille 1`, which makes the product print the
#   `permille=` it computed itself.
def declared_windows(lines, threshold_permille=PERMILLE_DIAGNOSIS):
    """From the `quic-net` lines to the dead line's judgement windows."""
    lines = [r for r in lines if "quic-net " in r]
    if not lines:
        return {"outcome": "NOTHING TO READ — no «quic-net» line in this "
                         "run (⚠ binary older than 23 Aug 2026?)"}
    valid, all_rows = [], []
    for r in lines:
        body = r.split("quic-net ", 1)[1].split("judgement=", 1)[0]
        d = dict(p.split("=", 1) for p in body.split() if "=" in p)
        try:
            da, lost, sped = (int(d["since_ms"]), int(d["lost_d"]),
                               int(d["sent_d"]))
        except (KeyError, ValueError):
            continue
        pm = (lost * 1000 // sped) if sped else None
        all_rows.append({"since_ms": da, "lost_d": lost, "sent_d": sped,
                      "permille": pm})
        # ⛔ The cure's two guards, to the letter: below the minimum number of
        #    packets nothing is decided, and the window must be at least
        #    the minimum one.
        if sped >= LM_MIN_PACKETS and da >= LM_WINDOW_MS:
            valid.append(pm)
    n = {"outcome": "read", "lines": len(all_rows), "finestre_valide": len(valid)}
    if not valid:
        n["outcome"] = ("I DO NOT JUDGE — no window passed the cure's "
                      "guards (%d packets sent, %d ms): over %d "
                      "`quic-net` lines the cure would NEVER have decided anything"
                      % (LM_MIN_PACKETS, LM_WINDOW_MS, len(all_rows)))
        return n
    in_order = sorted(valid)
    n["permille_max"] = in_order[-1]
    n["permille_p95"] = in_order[int(0.95 * (len(in_order) - 1))]
    n["permille_mediano"] = in_order[len(in_order) // 2]
    n["permille_medio"] = round(sum(valid) / float(len(valid)), 2)
    n["sopra_soglia"] = len([x for x in valid if x >= threshold_permille])
    # ⚠ Two IN A ROW was the firing condition of the OLD cure; it stays here
    #    because it is the count with which the refutation was written, and it serves to
    #    compare with that run.  ⛔ It is no longer the condition of anything.
    streak, max_dims, pairs = 0, 0, 0
    for x in valid:
        if x >= threshold_permille:
            streak += 1
            max_dims = max(max_dims, streak)
            if streak >= DIAGNOSIS_WINDOWS:
                pairs += 1
        else:
            streak = 0
    n["fila_massima_sopra_soglia"] = max_dims
    n["coppie_sopra_soglia"] = pairs
    n["threshold_permille"] = threshold_permille
    # ⭐⭐ AND THE QUESTION THE FIRST RUN GAVE RISE TO: is the high fraction
    #    only the connection START-UP, or does it last the whole session?
    #    `[M]` 23 Aug 2026: the cure fired at the fourth second, inside the
    #    first windows — when `cwnd` is still opening and every packet
    #    that overtakes is worth, proportionally, much more.
    # ⇒ The two halves are counted apart: if the tail is low and only the start is
    #   high, the defect is not the THRESHOLD, it is the MOMENT at which one judges.
    first = valid[:FIRST_WINDOWS]
    after = valid[FIRST_WINDOWS:]
    n["prime_finestre"] = len(first)
    n["permille_max_prime"] = max(first) if first else None
    n["permille_max_dopo"] = max(after) if after else None
    n["permille_mediano_dopo"] = (sorted(after)[len(after) // 2] if after else None)
    n["sopra_soglia_dopo"] = len([x for x in after if x >= threshold_permille])
    streak, maximum_d, pairs_d = 0, 0, 0
    for x in after:
        if x >= threshold_permille:
            streak += 1
            maximum_d = max(maximum_d, streak)
            if streak >= DIAGNOSIS_WINDOWS:
                pairs_d += 1
        else:
            streak = 0
    n["fila_massima_dopo"] = maximum_d
    n["coppie_sopra_soglia_dopo"] = pairs_d
    # ⭐ And the CUMULATIVE one, which is another quantity and must be stated alongside: it is the
    #    fraction over the whole session, not over one window.
    tot_p = sum(x["lost_d"] for x in all_rows)
    tot_s = sum(x["sent_d"] for x in all_rows)
    n["cumulativa_permille"] = round(1000.0 * tot_p / tot_s, 2) if tot_s else None
    n["persi_totali"] = tot_p
    n["spediti_totali"] = tot_s
    return n


def read_windows(line0, threshold_permille=PERMILLE_DIAGNOSIS):
    lines = read_log(line0, ["quic-net "], how_many=2000)
    return declared_windows(lines, threshold_permille)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE WIRE CLOCK — «how much does a still session really cost?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ It runs ON THE MACHINE and reads the `netem` counters, not a `tcpdump`: it is
#    the same counter `09-b76` uses for the qdisc, and reading it from here
#    would cost one `ssh` round per sample — that is 200 ms of error on a
#    measurement that must tell 5 s from 10 s.
CLOCK = r'''#!/usr/bin/env python3
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
    print(json.dumps({"samples": samples}))

if __name__ == "__main__":
    principale()
'''


def reduce_clock(samples, quiet_s=0.6):
    """From the counter samples to the numbers of the TRAFFIC AT REST.

    · **kbit_s** and **pacchetti_s** — what a still session REALLY costs;
    · **eventi** — the groups of samples in which the counter rose, separated
      by at least `quiet_s` of silence: ⭐ it is the way to see the PINGs without a
      `tcpdump`, because on a still line a PING and its acknowledgement are
      the only thing that moves the counter;
    · **intervallo_mediano_s** — the period between two events, and it is the number that
      says whether the PINGs went from 10 s to 5.

    ⛔ It does not judge: it reduces.  ⚠ And if the counter NEVER stops, the events
      are only one and the interval is `None` — which means «this session
      is not still», not «zero seconds».
    """
    n = {"samples": len(samples or [])}
    if not samples or len(samples) < 3:
        n["outcome"] = ("I DO NOT JUDGE — %d samples: without at least three there is no "
                      "interval to measure" % len(samples or []))
        return n
    t0, b0, p0 = samples[0]
    t1, b1, p1 = samples[-1]
    duration = t1 - t0
    if duration <= 0:
        n["outcome"] = "I DO NOT JUDGE — the window of the samples is zero long"
        return n
    n["outcome"] = "measured"
    n["seconds"] = round(duration, 2)
    n["byte"] = b1 - b0
    n["packets"] = p1 - p0
    n["kbit_s"] = round(8.0 * (b1 - b0) / duration / 1000.0, 4)
    n["pacchetti_s"] = round((p1 - p0) / duration, 3)
    events, prev_t, prev_p, is_opened = [], t0, p0, None
    for t, b, p in samples[1:]:
        if p > prev_p:
            if is_opened is None:
                is_opened = t
            prev_t = t
        elif is_opened is not None and t - prev_t >= quiet_s:
            events.append([round(is_opened, 3), round(prev_t, 3),
                           p - _pkt_a(samples, is_opened)])
            is_opened = None
        prev_p = p
    if is_opened is not None:
        events.append([round(is_opened, 3), round(prev_t, 3), None])
    n["events"] = len(events)
    n["eventi_primi"] = events[:6]
    if len(events) >= 2:
        inter = [round(events[i][0] - events[i - 1][0], 3)
                 for i in range(1, len(events))]
        inter_ord = sorted(inter)
        n["intervalli_s"] = inter[:12]
        n["intervallo_mediano_s"] = inter_ord[len(inter_ord) // 2]
        n["intervallo_min_s"] = inter_ord[0]
        n["intervallo_max_s"] = inter_ord[-1]
        # ⭐ The bytes per round: the count the PING box declares at ~130 B.
        n["byte_per_evento"] = round((b1 - b0) / float(len(events)), 1)
    else:
        n["intervallo_mediano_s"] = None
        n["perche_niente_intervallo"] = (
            "the counter never stopped for %.1f s in a row: this "
            "session is NOT still, and an interval between two events does not exist"
            % quiet_s)
    return n


def _pkt_a(samples, t):
    for x in samples:
        if x[0] >= t:
            return x[2]
    return samples[-1][2]


def clock_runs(seconds=60.0, step=0.1):
    rc, out, err = root("python3 %s/09-b81-orologio.py %s %g %g"
                        % (WORKDIR, DEV, seconds, step), int(seconds) + 120)
    try:
        d = json.loads(out)
    except Exception as e:
        _dub("the clock did not answer: %s — %s" % (e, (out + err)[-200:]))
        return {"outcome": "I DO NOT JUDGE — the wire clock did not answer"}
    return reduce_clock(d.get("samples") or [])


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
# ⭐ And it can be done only because `main.c` calls `wt_dead_line()` ALWAYS, and
#    `rcp_eviction()` prints itself on AND off: the startup line comes out in both
#    cases by construction, and it is half the value of the two cures.
def fixes_state():
    """What the server says about itself, at the LAST startup."""
    rc, out, _ = root("bash -c \"grep -a -n -e 'DEAD LINE is' -e 'ghost "
                      "eviction: threshold' %s/registro.log | tail -6\"" % WORKDIR)
    lines = [r for r in out.splitlines() if r.strip()]
    n = {"outcome": "read" if lines else "⛔ I DID NOT READ any startup line "
                                        "of the two cures",
         "dead_line": None, "stall_ms": None, "silence_s": None,
         "eviction_ms": None, "lines": lines[-2:]}
    for r in lines:
        if "DEAD LINE is ON" in r:
            n["dead_line"] = "enabled"
            m = re.search(r"\(1\) STALL: (\d+) ms", r)
            n["stall_ms"] = int(m.group(1)) if m else None
            m = re.search(r"\(2\) SILENCE: (\d+) s", r)
            n["silence_s"] = int(m.group(1)) if m else None
        elif "DEAD LINE is OFF" in r:
            n["dead_line"] = "spenta"
            n["stall_ms"], n["silence_s"] = None, None
        if "ghost eviction: threshold" in r:
            m = re.search(r"threshold (\d+) ms", r)
            n["eviction_ms"] = int(m.group(1)) if m else None
    return n


def fixes_as_wanted(status, dead_line=None, stall_ms=None, silence_s=None,
                     eviction_ms=None):
    """(va_bene, perche') — is the server configured as this test demands?

    ⛔ Called BEFORE every test: a predicate running on a configuration
       other than the one it believes does not give red, it gives a plausible number.
    """
    if status.get("outcome") != "read":
        return _mute(status.get("outcome"))
    troubles = []
    if dead_line is not None and status["dead_line"] != dead_line:
        troubles.append("the dead line is «%s» and I wanted it «%s»"
                    % (status["dead_line"], dead_line))
    if stall_ms is not None and status["stall_ms"] != stall_ms:
        troubles.append("the STALL threshold is %s ms and I wanted %d"
                    % (status["stall_ms"], stall_ms))
    if silence_s is not None and status["silence_s"] != silence_s:
        troubles.append("the silence threshold is %s s and I wanted %d"
                    % (status["silence_s"], silence_s))
    if eviction_ms is not None and status["eviction_ms"] != eviction_ms:
        troubles.append("the eviction is at %s ms and I wanted it at %d"
                    % (status["eviction_ms"], eviction_ms))
    if troubles:
        return _mute("⛔ I DO NOT MEASURE: the server is not configured as this "
                     "test demands — " + " · ".join(troubles))
    return _si("the server says of itself: dead line %s (stall %s ms, silence "
               "%s s) · eviction %s ms"
               % (status["dead_line"], status["stall_ms"], status["silence_s"],
                  status["eviction_ms"]))


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE SIX PREDICATES, WRITTEN FIRST — «(numbers) -> (passes, why')»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `PIANO.md` §0.3.4: a bench that cannot see the defect it looks for has no
#    right to green.  ⇒ Each of these can give GREEN, RED and MUTE, and
#    `--certify` proves it on manufactured numbers.  A predicate never seen
#    failing is not a predicate.

def p1_no_false_positive(lm, witnesses, n, minutes):
    """⛔⛔ **THE TEST THAT CAN MAKE THE CURE BE WITHDRAWN.**

    On `bad-home` — the line that HOLDS — the dead line when on must not
    fire EVEN ONCE in ten minutes.  A firing here means
    throwing out someone who was working, and it is the error that cannot be undone.

    ⚠ And the green holds only if the line really held: if the session did not
      open, or dropped for other reasons, or the rate is below `HOLDING_LINE_FPS`
      (5.0 frames/s), here there was no user at work NOT to throw
      out — and then this predicate KEEPS QUIET instead of giving a green it has not
      earned.
    """
    if not lm or lm.get("outcome") != "read":
        return _mute((lm or {}).get("outcome", "I did not read the firings"))
    if lm["notches"] > 0:
        p = lm["lines"][0]
        return _no("⛔⛔ FALSE POSITIVE: the dead line fired %d time(s) "
                   "in %g minutes on a line the product was serving — "
                   "cause=%s stall_ms=%s (threshold %s) offered=%s "
                   "bytes_out=%s video_queue=%s · witness of the reordering: "
                   "permille=%s.  ⇒ Switching it on would mean throwing out a "
                   "user at work: THE CURE IS NOT SWITCHED ON"
                   % (lm["notches"], minutes, p.get("cause"), p.get("stall_ms"),
                      p.get("stall_threshold_ms"), p.get("offered"),
                      p.get("bytes_out"), p.get("video_queue"),
                      p.get("permille")))
    if not witnesses:
        return _mute("no firing, but I did not question the witnesses of the "
                     "connection: without them, I do not know whether there was a user at "
                     "work not to throw out")
    if witnesses.get("is_open") is False:
        return _mute("⚠ no firing, but the session does not appear to have "
                     "OPENED: «it never opened» looks the same as «nothing "
                     "fired», and it is not the same thing")
    if witnesses.get("cliente_staccato"):
        return _mute("⚠ no firing of the dead line, but the client "
                     "dropped anyway: «%s» — the line did not hold, and this "
                     "test proved nothing"
                     % (witnesses.get("drop") or "")[:140])
    fps = (n or {}).get("fps")
    if fps is None:
        return _mute("no firing, but I do not have the delivered rate: without it, "
                     "I do not know whether the line held")
    if fps < HOLDING_LINE_FPS:
        return _mute("⚠ ZERO firings, but the rate is %.2f frames/s (below "
                     "%.1f): this line was not serving anyone, and not "
                     "having thrown anyone out is no merit"
                     % (fps, HOLDING_LINE_FPS))
    c = (n or {}).get("delivery") or {}
    return _si("⭐ ZERO firings in %g minutes on a line that HOLDS: %.2f "
               "frames/s, coverage %s, ⭐ longest gap **%s s** "
               "(the quantity the threshold is derived from), client still "
               "attached and no farewell in the log"
               % (minutes, fps, c.get("coverage"), c.get("buco_max_s")))


def p1c_line_holds_with_fix_off(witnesses, n, minutes, shots_on):
    """⛔⛔ **THE CONTROL OF TEST 1, AND WITHOUT IT ITS RED DOES NOT COUNT.**

    When the cure fires, the session DIES — and from a run in which the session
    died at 4 s one cannot say whether the line was holding: «the cure threw out
    someone who was working» and «the line was finished anyway» look the same.
    ⚠ It is the form of `LEZIONI.md` §1.9 applied to a judgement instead of a
      number.

    ⇒ Same line, same duration, **cures OFF**: if the session holds all the
      minutes at more than `HOLDING_LINE_FPS` frames per second, then the
      difference between the two runs is **a switch**, and what the cure
      threw out was a user at work.  If instead it does not hold even with the cure
      off, this predicate gives RED — because then the red of test 1
      is not a false positive, and the bench must say so.
    """
    if not witnesses:
        return _mute("I did not question the witnesses of the connection")
    if witnesses.get("is_open") is False:
        return _mute("the session does not appear to have opened: the question belongs to "
                     "`09-b78-apertura.py`, and I do not judge")
    if witnesses.get("cliente_staccato"):
        return _no("⛔ WITH THE CURE OFF THE SESSION DROPPED ANYWAY: «%s» — "
                   "so the firing of test 1 is not a false positive, and "
                   "this line is not the one that HOLDS"
                   % (witnesses.get("drop") or "")[:160])
    fps = (n or {}).get("fps")
    c = (n or {}).get("delivery") or {}
    if fps is None or c.get("outcome") != "measured":
        return _mute("I do not have the rate or the delivery of this run: without them, I cannot "
                     "say the line held")
    queue = ("%.2f frames/s · coverage %.2f · longest gap %.2f s · "
            "last frame at %.2f s over %g minutes"
            % (fps, c["coverage"], c["buco_max_s"], c["consegna_fino_a_s"],
               minutes))
    if fps < HOLDING_LINE_FPS:
        return _no("⛔ with the cure off the line gives %.2f frames/s (below %.1f): "
                   "it was not serving anyone even like this, and the firing of "
                   "test 1 cannot be called a false positive.  %s"
                   % (fps, HOLDING_LINE_FPS, queue))
    if c["coverage"] < B76.MIN_COVERAGE:
        return _no("⛔ with the cure off the delivery stopped anyway "
                   "(coverage %.2f < %.2f): %s"
                   % (c["coverage"], B76.MIN_COVERAGE, queue))
    return _si("⭐ WITH THE CURE OFF THE SAME LINE HOLDS %g whole minutes: %s — "
               "⇒ between the two runs ONE SWITCH changes, and with it on the "
               "session was closed %d time(s).  What the cure throws "
               "out is a user at work" % (minutes, queue, shots_on))


def p1b_stall_margin(scale_factor, soglia_ms, name):
    """⭐⭐ **THE TRUE MARGIN, and not «it did not fire».**

    ⛔ The `dead-line` line comes out ONLY on firing: from a run in which the cure does not
       fire one cannot read **by how much** it did not fire — and a green without that
       number does not say whether the margin is tenfold or three per cent.
       ⚠ It is the same form as the defect this bench has already paid for: «nothing
         happened» passing itself off as a measurement.

    ⇒ The same profile is rerun with LOWER and lower thresholds, until one
      fires.  Then the line comes out and carries a `stall_ms` **measured by the
      product**, with its own arithmetic.  Between the lowest threshold that does NOT fire
      and the stall the product printed, the maximum is pinned.

    Green if the margin (threshold / maximum observed stall) sits above %.1f×.
    ⛔ Red if it drops below: below that point the threshold begins to look like
       a lucky number, and erring low means throwing out someone who
       was working.
    """ % MIN_STALL_MARGIN
    if not scale_factor:
        return _mute("I did not try any lower threshold: without the scale "
                     "I have no margin, only «it did not fire»")
    triggered = [x for x in scale_factor if x.get("scattata")]
    not_triggered = [x for x in scale_factor if x.get("scattata") is False]
    if not triggered and not not_triggered:
        return _mute("no step of the scale gave a readable outcome")
    # ⛔ A firing at the TRUE threshold (or above) is not a narrow margin: it is the
    #    false positive, and P1 judges it.  Here we keep quiet, or I would say the
    #    same thing twice with two different words.
    if any(x["soglia_ms"] >= soglia_ms for x in triggered):
        return _mute("⚠ the cure already fired at the threshold in force (%d ms): "
                     "there is no margin to measure, and P1 states the "
                     "fact" % soglia_ms)
    if not triggered:
        lowest = min(x["soglia_ms"] for x in not_triggered)
        margin = soglia_ms / float(lowest)
        queue = ("not even at %d ms — the scale tried is %s"
                % (lowest, [x["soglia_ms"] for x in scale_factor]))
        if margin < MIN_STALL_MARGIN:
            return _mute("⚠ it did not fire at any of the thresholds tried, but "
                         "the lowest (%d ms) gives only %.1f× of margin: to "
                         "say the margin is ≥ %.1f× one must go further "
                         "down" % (lowest, margin, MIN_STALL_MARGIN))
        return _si("⭐ «%s»: the maximum stall sits BELOW %d ms — the cure does not "
                   "fire %s ⇒ the margin of the threshold (%d ms) is **more than "
                   "%.1f×**" % (name, lowest, queue, soglia_ms, margin))
    # ⭐ There is at least one firing below the true threshold: that is a `stall_ms`
    #   MEASURED, and it is the best number one can have.
    worst = max(x.get("stall_ms") or 0 for x in triggered)
    if not worst:
        return _mute("the cure fired but the line does not carry `stall_ms`: the "
                     "contract on the text does not hold, and I do not have the number")
    margin = soglia_ms / float(worst)
    queue = ("maximum stall MEASURED %d ms (at threshold %d ms) · threshold in force "
            "%d ms · scale tried %s"
            % (worst, min(x["soglia_ms"] for x in triggered), soglia_ms,
               [(x["soglia_ms"], x.get("stall_ms")) for x in scale_factor]))
    if margin < MIN_STALL_MARGIN:
        return _no("⛔ THE MARGIN IS NARROW on a line that HOLDS: %.2f× "
                   "(minimum %.1f×) — %s.  ⇒ The threshold sits too close to a "
                   "stall that a good line produces on its own, and erring "
                   "low means throwing out someone who is working"
                   % (margin, MIN_STALL_MARGIN, queue))
    return _si("⭐ «%s»: the margin is **%.1f×** — %s" % (name, margin, queue))


def p_must_not_fire(name, lm, witnesses, n, minutes, expected):
    """⛔ **THIS LINE HOLDS, AND MUST NOT BE DECLARED DEAD.**  It is the general
    form of test 1, applied to any profile of the grid of
    `09-b76` — it serves `burst-1`, which is the case the narrow
    side of the threshold rests on: `[M]` it delivers 23.94 frames/s and still had
    **a whole empty second**.

    ⚠ The green holds only if the line really held: outside the grid
      this predicate KEEPS QUIET, instead of giving a green it has not earned.
    """
    if not lm or lm.get("outcome") != "read":
        return _mute((lm or {}).get("outcome", "I did not read the firings"))
    if lm["notches"] > 0:
        p = lm["lines"][0]
        return _no("⛔⛔ «%s» was declared DEAD, and it HOLDS: cause=%s "
                   "stall_ms=%s (threshold %s) offered=%s bytes_out=%s "
                   "video_queue=%s — %s"
                   % (name, p.get("cause"), p.get("stall_ms"),
                      p.get("stall_threshold_ms"), p.get("offered"),
                      p.get("bytes_out"), p.get("video_queue"),
                      expected.get("why", "")))
    if not witnesses or witnesses.get("is_open") is False:
        return _mute("no firing, but I have no witnesses that the session "
                     "opened")
    if witnesses.get("cliente_staccato"):
        return _mute("⚠ no firing of the dead line, but the client "
                     "dropped anyway: «%s»"
                     % (witnesses.get("drop") or "")[:140])
    fps = (n or {}).get("fps")
    c = (n or {}).get("delivery") or {}
    if fps is None or c.get("outcome") != "measured":
        return _mute("no firing, but I have no rate and delivery: without them, I do not know "
                     "whether the line held")
    queue = ("%.2f frames/s · coverage %.2f · ⭐ longest gap **%.2f s**"
            % (fps, c["coverage"], c["buco_max_s"]))
    if not (expected["fps_min"] <= fps <= expected["fps_max"]):
        return _mute("⚠ ZERO firings, but «%s» gave %.2f frames/s, outside "
                     "the grid of 09-b76 (%.1f-%.1f): it is not the case I "
                     "believe I tested — %s"
                     % (name, fps, expected["fps_min"], expected["fps_max"], queue))
    if c["coverage"] < expected["copertura_min"]:
        return _mute("⚠ ZERO firings, but the coverage is %.2f against %.2f of the "
                     "grid: this line was not serving anyone — %s"
                     % (c["coverage"], expected["copertura_min"], queue))
    return _si("⭐ ZERO firings in %g minutes on «%s», which HOLDS: %s (grid "
               "09-b76: %s)" % (minutes, name, queue, expected["why"]))


def p_still_scene_no_fire(lm, witnesses, seconds, soglia_ms):
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
    if not lm or lm.get("outcome") != "read":
        return _mute((lm or {}).get("outcome", "I did not read the firings"))
    if lm["notches"] > 0:
        p = lm["lines"][0]
        return _no("⛔⛔ THE STILL SCENE WAS DECLARED DEAD — the cure "
                   "throws out whoever looks at a desktop that does not change: cause=%s "
                   "stall_ms=%s (threshold %s) offered=%s bytes_out=%s "
                   "video_queue=%s.  ⚠ If `offered` and `video_queue` are ZERO, the "
                   "count started without there being anything to send, and it is "
                   "precisely the half that was supposed to prevent it"
                   % (p.get("cause"), p.get("stall_ms"),
                      p.get("stall_threshold_ms"), p.get("offered"),
                      p.get("bytes_out"), p.get("video_queue")))
    if not witnesses or witnesses.get("is_open") is False:
        return _mute("no firing, but it does not appear that the session "
                     "opened: without that, I proved nothing")
    if witnesses.get("cliente_staccato"):
        return _mute("⚠ no firing of the dead line, but the client "
                     "dropped anyway: «%s» — it is not the case I wanted to test"
                     % (witnesses.get("drop") or "")[:140])
    if witnesses.get("cliente_attaccato") is not True:
        return _mute("the client did not say «still attached»: I do not have the "
                     "witness I need")
    return _si("⭐ %g s of STILL SCENE with the stall threshold at **%d ms** "
               "(that is %.1f times narrower than the one in force): ZERO "
               "firings, and the client stayed attached to the end.  ⇒ The "
               "count does not start when there is nothing to send"
               % (seconds, soglia_ms, LM_STALL_MS / float(soglia_ms or 1)))


def p2_fires_on_stall(lm, probe, seconds_to_fire):
    """**The real firing.**  On `burst-heavy` — `[M]` 11.10 % loss in
    bursts, `cwnd` median 8 948 B against 105 616 of the reference, delivery
    that stops — the cure MUST fire, and with `cause=perdita`.

    ⚠ If the probe says the fault was not put in place, here we KEEP QUIET: measuring
      a profile that does not exist is worse than not measuring it, because the number is
      true and the cause is made up.
    """
    if not probe or probe.get("outcome") != "measured":
        return _mute("the probe did not measure: without it, I do not know whether the burst was "
                     "put in place, and a firing without a fault is not a firing")
    if probe["persi_pc"] < 5.0:
        return _mute("⚠ the probe saw %.2f %% loss: it is not "
                     "`burst-heavy` (`[M]` 11.10 %%), and I do not judge a "
                     "profile that does not exist" % probe["persi_pc"])
    if not lm or lm.get("outcome") != "read":
        return _mute((lm or {}).get("outcome", "I did not read the firings"))
    if lm["notches"] == 0:
        return _no("⛔ the cure did NOT fire on a line the product cannot "
                   "needs: the probe saw %.2f %% in bursts of "
                   "%.2f, and `[M]` at this loss the image either freezes "
                   "(14.26 s out of 25) or arrives 4.5 s late"
                   % (probe["persi_pc"], probe["raffica_media"]))
    if lm.get("cause") != "stall":
        return _no("⛔ it fired, but for the WRONG reason: cause=%s on a "
                   "line that loses %.2f %% and on which the image STOPS — "
                   "a silence of the client is not an output stall, and the "
                   "two causes send one looking for the cause in two different places"
                   % (lm.get("cause"), probe["persi_pc"]))
    if lm.get("chiuse_dal_trasporto", 0) < 1:
        return _no("⛔ the decision was taken (`dead-line` line) but the "
                   "wire did NOT drop: the `trasporto.c` line «DEAD "
                   "LINE — the QUIC connection is closing» is missing.  ⚠ The user "
                   "chose that the wire drops, not that the server writes it")
    return _si("⭐ fired %s s after the slot was taken: cause=stall "
               "stall_ms=%s (threshold %s) offered=%s bytes_out=%s "
               "video_queue=%s cwnd=%s cwnd_left=%s srtt_us=%s · the wire "
               "dropped (%d line(s) of `trasporto.c`) · the probe: %.2f %% in "
               "bursts of %.2f · ⚠ the WITNESS of the reordering said "
               "permille=%s (and decided nothing)"
               % (("%.2f" % seconds_to_fire) if seconds_to_fire is not None
                  else "?", lm.get("stall_ms"), lm.get("stall_threshold_ms"),
                  lm.get("offered"), lm.get("bytes_out"),
                  lm.get("video_queue"), lm.get("cwnd"), lm.get("cwnd_left"),
                  lm.get("srtt_us"), lm.get("chiuse_dal_trasporto", 0),
                  probe["persi_pc"], probe["raffica_media"],
                  lm.get("permille")))


def p3_fires_on_silence(lm, soglia_ms):
    """**Silence.**  Client killed with `kill -9` — that is a goodbye NEVER
    SAID, which for the server is identical to a lost goodbye — and the cure must
    fire with `cause=silence` at its threshold.

    ⛔ AND THE TWO DIRECTIONS DO NOT COST THE SAME, as for test 1: firing
       LATE means a few more seconds of ghost; firing BEFORE the
       threshold means throwing out a live client that was keeping quiet — ⇒ below
       the threshold it is red with no discount, above it %.1f s is granted (the judgement is
       taken once per second, and there is the pacer queue).
    """ % (SILENCE_TOLERANCE_MS / 1000.0)
    if not lm or lm.get("outcome") != "read":
        return _mute((lm or {}).get("outcome", "I did not read the firings"))
    if lm["notches"] == 0:
        return _no("⛔ the client died without saying goodbye and the cure did NOT "
                   "fire: the slot stays with a ghost until the 30 s of "
                   "§5.3, which is precisely what this cure was supposed to "
                   "remove")
    if lm.get("cause") != "silence":
        return _no("⛔ it fired with cause=%s and not «silenzio»: the client was "
                   "killed, and what the server must see is that no packet "
                   "comes back any more" % lm.get("cause"))
    s = lm.get("silence_ms")
    if s is None:
        return _mute("the line does not carry `silence_ms`: the contract on the text "
                     "does not hold, and I do not have the number to judge on")
    if s < soglia_ms:
        return _no("⛔⛔ FIRED BEFORE ITS THRESHOLD: %d ms of silence "
                   "against %d declared — a live and idle client would be "
                   "thrown out, and it is the regression already paid for on 16 "
                   "August 2026" % (s, soglia_ms))
    if s > soglia_ms + SILENCE_TOLERANCE_MS:
        return _no("⛔ fired at %d ms against %d declared (+%d of "
                   "tolerance): the number written and the one in force "
                   "diverge, and it is form E1"
                   % (s, soglia_ms, SILENCE_TOLERANCE_MS))
    if lm.get("chiuse_dal_trasporto", 0) < 1:
        return _no("⛔ the decision was taken but the wire did NOT drop: "
                   "the `trasporto.c` line is missing")
    return _si("⭐ fired at %d ms of silence (threshold %d) with cause=silence, "
               "unanswered=%s (minimum %s) — and the wire dropped"
               % (s, soglia_ms, lm.get("unanswered"), lm.get("min_unanswered")
                  or LM_MIN_PROVE))


def p3b_ping_cost(on, off, claimed=COST_PING_DECLARED_KBIT_S):
    """⚠ **THE DECLARED PRICE OF THE PINGs.**  The box of `webtransport.c`
    declares ~130 B per round every HALF of the threshold, that is **%.2f kbit/s** per
    session.  ⇒ The REAL traffic of a still session is measured, on and
    off, and the difference cannot exceed the declared cost — if it
    exceeds it, it is a number to correct.

    ⛔ AND THIS PREDICATE REFUSES WHEN THE NOISE IS BIGGER THAN THE
       TARGET, which is the only honest thing to do: a «green» obtained
       by measuring %.2f kbit/s inside a background a thousand times higher does not
       prove anything, and it would be form E1 in reverse.
    """ % (COST_PING_DECLARED_KBIT_S, COST_PING_DECLARED_KBIT_S)
    if not on or on.get("outcome") != "measured":
        return _mute("I did not measure the traffic with the cure ON")
    if not off or off.get("outcome") != "measured":
        return _mute("I did not measure the traffic with the cure OFF")
    delta = on["kbit_s"] - off["kbit_s"]
    background = min(on["kbit_s"], off["kbit_s"])
    queue = ("on %.3f kbit/s (%d packets in %.1f s) · off %.3f kbit/s "
            "(%d in %.1f s) · difference %+.3f kbit/s · declared %.2f"
            % (on["kbit_s"], on["packets"], on["seconds"],
               off["kbit_s"], off["packets"], off["seconds"],
               delta, claimed))
    # ⛔ The background must be small compared with the target, or one is not
    #    measuring the target.  Ten times is generous and it is declared.
    if background > 10.0 * claimed:
        return _mute("⛔ I DO NOT JUDGE — a «still» session of this product "
                     "is not still: it costs %.1f kbit/s, that is %d times the "
                     "declared cost of the PINGs (%.2f).  ⭐ It is the PCM audio of §4.3, "
                     "which CANNOT be turned off (`[M]` a HELLO without an audio codec "
                     "in common gets `0x09 NOTHING_IN_COMMON`).  ⇒ Inside "
                     "this background the cost of the PINGs cannot be isolated, and a green "
                     "here would prove nothing.  %s"
                     % (background, int(background / claimed), claimed, queue))
    if delta > 2.0 * claimed:
        return _no("⛔ the PINGs cost more than declared: %s" % queue)
    return _si("the cost of the PINGs is within the declared one: %s" % queue)


def p4_eviction_frees_slot(sf, soglia_ms, seconds_to_enter, reference_s):
    """**The eviction.**  Same user, client killed with `-9`, a second
    client asking for the slot.  `[M]` today it takes **30.5 s** and **11 refusals**;
    with `--eviction-ms %d` the slot must be free again at **~%.0f s**.

    ⚠ And here too the direction counts: evicting TOO EARLY means taking the
      slot from a live and idle client, that is switching off I2 — so below the
      threshold it is red.
    """ % (RECOMMENDED_EVICTION_MS, RECOMMENDED_EVICTION_MS / 1000.0)
    if not sf or sf.get("outcome") != "read":
        return _mute((sf or {}).get("outcome", "I did not read the log"))
    if seconds_to_enter is None:
        return _mute("I do not have the time at which the slot was taken back: without it, "
                     "«it got in» and «it did not get in» look the same")
    if sf["evictions"] == 0:
        return _no("⛔ no EVICTION: the slot became free again after %.2f s "
                   "with %d refusals, that is at the silence clock of §5.3 — "
                   "the cure did nothing"
                   % (seconds_to_enter, sf["refusals"]))
    mute = sf.get("muto_ms")
    if mute is None:
        return _mute("the eviction line does not carry the milliseconds of "
                     "silence: the contract on the text does not hold")
    if mute < soglia_ms:
        return _no("⛔⛔ EVICTED BEFORE THE THRESHOLD: the occupant had been silent for %d "
                   "ms and the threshold is %d — a live and idle client (`[M]` the "
                   "keep-alive of a browser is silent for 15 s) would be thrown out, "
                   "and that switches off invariant I2" % (mute, soglia_ms))
    if seconds_to_enter > (soglia_ms + EVICTION_TOLERANCE_MS) / 1000.0:
        return _no("⛔ the slot became free again after %.2f s with the threshold at "
                   "%.1f s (+%.1f of tolerance): the cure fired but did not "
                   "shorten what it was supposed to"
                   % (seconds_to_enter, soglia_ms / 1000.0,
                      EVICTION_TOLERANCE_MS / 1000.0))
    gain = ("from %.1f s to %.2f s (%.0f %% less)"
                % (reference_s, seconds_to_enter,
                   100.0 * (1.0 - seconds_to_enter / reference_s))
                if reference_s else "without a reference measured in this run")
    return _si("⭐ the slot became free again after %.2f s with %d refusals — "
               "the occupant had been silent for %d ms (threshold %d), evicted «%s» · %s"
               % (seconds_to_enter, sf["refusals"], mute, soglia_ms,
                  sf.get("sfrattato"), gain))


def p5_no_eviction_across_users(sf, entered, utente_a, utente_b):
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
    if not sf or sf.get("outcome") != "read":
        return _mute((sf or {}).get("outcome", "I did not read the log"))
    if sf["evictions"] > 0:
        return _no("⛔⛔ SECURITY HOLE: there was an EVICTION while the one "
                   "asking for the slot was a DIFFERENT user — evicted «%s», "
                   "line: «%s»"
                   % (sf.get("sfrattato"), (sf.get("righe_sfratto") or [""])[0][:200]))
    if entered is not True:
        return _mute("no eviction (and that is what I wanted), but «%s» does not "
                     "appear to have got in: without their entry I have not "
                     "proved that the first one's slot stayed theirs — I have only "
                     "proved that nothing happened" % utente_b)
    return _si("⭐ no eviction between «%s» and «%s», and the second user "
               "got in all the same on their own slot: %d slots taken, %d refusals"
               % (utente_a, utente_b, sf["grabbed"], sf["refusals"]))


def p5b_denied_line(sf):
    """⚠ **AND DOES THE `⛔ EVICTION DENIED` LINE COME OUT?**  The prediction is written FIRST
    and goes the uncomfortable way: `[R]` 23 August 2026, reading `src/rcp.c`, **NO**.

    The slot registry is indexed BY NAME (`slot_occupied(utente)`),
    so `SLOT_OCCUPIED` already implies «same user» and two different users
    take two different slots: the branch with that line is NEVER walked.
    ⇒ Whoever wrote it declares so in its own comment — *«redundant by
    construction, not by design»*, and it serves the day the registry
    became the session table of a real server.

    ⛔ So this predicate does NOT give red if the line is missing: it would give red to
       correct code.  It gives red if the line COMES OUT, because then my
       reading was wrong and the branch is reachable — that is, there is a way to
       reach `SLOT_OCCUPIED` with two different names, and THAT must be looked at.
    """
    if not sf or sf.get("outcome") != "read":
        return _mute((sf or {}).get("outcome", "I did not read the log"))
    if sf["denied"] > 0:
        return _no("⛔ the «EVICTION DENIED» line DID COME OUT, and `[R]` I had read "
                   "that it could not: it means one reaches SLOT_OCCUPIED "
                   "with two different names — «%s»"
                   % (sf.get("righe_negato") or [""])[0][:200])
    return _si("no «EVICTION DENIED» line, as predicted `[R]`: the slot registry "
               "is by NAME, so the branch is not reachable — the "
               "protection comes from the structure, and the explicit check stays "
               "as a net for the day the structure changes")


def p6_defaults_change_nothing(lm, sf, status, n, profile_name):
    """⛔ **INVARIANT I6.**  Without `--linea-morta` and with `--eviction-ms 0` —
    that is **as the product ships today** — everything must be identical to
    yesterday: no firing, no eviction, and the profile behaves as in the
    grid of `09-b76`.

    ⭐ And it is also the proof that the two cures are really OFF, not only
       written: two startup lines saying so, and zero firing lines.
    """
    va, why = fixes_as_wanted(status, dead_line="spenta", eviction_ms=0)
    if va is not True:
        return _mute("⚠ I do not judge I6 on a configuration that is not the "
                     "default one — %s" % why)
    if not lm or lm.get("outcome") != "read":
        return _mute((lm or {}).get("outcome", "I did not read the firings"))
    if lm["notches"] > 0 or lm.get("chiuse_dal_trasporto", 0) > 0:
        return _no("⛔ I6 VIOLATED: with the cure OFF %d `dead-line` "
                   "lines and %d closures by the transport came out"
                   % (lm["notches"], lm.get("chiuse_dal_trasporto", 0)))
    if not sf or sf.get("outcome") != "read":
        return _mute((sf or {}).get("outcome", "I did not read the eviction"))
    if sf["evictions"] > 0:
        return _no("⛔ I6 VIOLATED: with the eviction OFF there was an "
                   "eviction — «%s»" % (sf.get("righe_sfratto") or [""])[0][:180])
    expected = GRID_B76.get(profile_name)
    if not expected:
        return _si("no firing and no eviction with the cures off "
                   "(⚠ «%s» is not in the grid of 09-b76: nothing to "
                   "compare)" % profile_name)
    c = (n or {}).get("delivery") or {}
    fps = (n or {}).get("fps")
    if c.get("outcome") != "measured" or fps is None:
        return _mute("no firing and no eviction, but I do not have the numbers of the "
                     "run: without them, I cannot say it behaves as in the "
                     "grid of 09-b76")
    queue = ("%.2f frames/s · coverage %.2f · longest gap %.2f s "
            "(grid 09-b76: %s)"
            % (fps, c["coverage"], c["buco_max_s"], expected["why"]))
    if expected.get("consegna_si_ferma"):
        # ⛔ On `burst-heavy` the grid says delivery STOPS: if here it
        #    did not stop, the product would have changed — it is a red for I6
        #    as much as a firing.
        halt = (c["coverage"] < B76.MIN_COVERAGE
                 or c["buco_max_s"] >= B76.FROZEN_SCREEN_GAP_S)
        if not halt:
            return _no("⛔ I6: with the cures off «%s» does NOT behave as "
                       "in the grid of 09-b76 — there delivery stops, here "
                       "it does not.  %s" % (profile_name, queue))
        return _si("⭐ cures off: zero firings, zero evictions, and «%s» "
                   "behaves as in the grid — %s" % (profile_name, queue))
    if not (expected["fps_min"] <= fps <= expected["fps_max"]):
        return _no("⛔ I6: with the cures off «%s» gives %.2f frames/s, outside "
                   "the grid of 09-b76 (%.1f-%.1f).  %s"
                   % (profile_name, fps, expected["fps_min"], expected["fps_max"],
                      queue))
    if c["coverage"] < expected["copertura_min"]:
        return _no("⛔ I6: with the cures off «%s» has coverage %.2f against %.2f "
                   "of the grid.  %s"
                   % (profile_name, c["coverage"], expected["copertura_min"], queue))
    return _si("⭐ cures off: zero firings, zero evictions, and «%s» sits within the "
               "grid of 09-b76 — %s" % (profile_name, queue))


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

# ⛔ The format is that of `src/webtransport.c`, `dead_line_fires()`, field
#    by field and IN ORDER: `_certify_contract()` rereads it from the source and
#    compares, so the day the product changes the line the bench says so
#    instead of reading the wrong field in silence.
# ⛔⛔ THE CONTRACT CHANGED ON 23 AUGUST 2026, and the two vanished fields are
#     declared instead of vanishing in silence:
#       · `threshold_permille=` — there is no longer any threshold on loss;
#       · `windows=N/M`     — there are no longer bad windows to count in
#                              a row: the stall is a continuous duration.
#     ⭐ And five came in: `stall_ms` `stall_threshold_ms` `offered`
#        `bytes_out` `video_queue` (plus `cwnd_left`).
# ⛔ AND IT CHANGED AGAIN ON 25 AUGUST 2026 (phase 10 cures, c808342): seven
#    fields came in between `srtt_us` and `judgement` — `loop_gap_ms` `loop_gaps`
#    `skipped` `rate_down` `rate_backlog` `rate_slots` `rate_dropped`.  This
#    bench reads none of them, but step 0 rereads the order and gave red until
#    they were written here too.
FIELDS_LM = ["cause", "stall_ms", "stall_threshold_ms", "offered", "bytes_out",
            "video_queue", "silence_ms", "silence_threshold_ms", "unanswered",
            "min_unanswered", "lost", "sent", "permille", "window_ms",
            "min_packets", "cwnd", "cwnd_left", "srtt_us", "loop_gap_ms",
            "loop_gaps", "skipped", "rate_dropping", "rate_backlog", "rate_slots",
            "rate_dropped", "judgement"]


def _fab_lm(now="21:14:02.123", cause="stall", stall_ms=5004,
            stall_threshold=LM_STALL_MS, offered=41, exited=0, video_queue=61240,
            silence_ms=1300, unanswered=9, lost=31, sent=412, permille=75,
            window_ms=1004, cwnd=8948, cwnd_left=0, srtt_us=61230,
            judgement="⛔ the line is DEAD: for too long no frame has gone out while "
                     "having some to send"):
    """A `dead-line` line as the product writes it FROM TODAY, field by
       field and in order.  ⛔ `soglia_permille=` and `finestre=N/M` are no longer
       there: if they reappeared, `_certify_contract()` would give red.
       The seven fields of 25 Aug (`loop_gap_ms` … `rate_dropped`) are written with
       neutral values: no predicate of this bench reads them."""
    return ("%s wt      dead-line [192.168.0.2]:50875 cause=%s stall_ms=%d "
            "stall_threshold_ms=%d offered=%d bytes_out=%d video_queue=%d "
            "silence_ms=%d silence_threshold_ms=%d unanswered=%d min_unanswered=%d "
            "lost=%d sent=%d permille=%d window_ms=%d "
            "min_packets=%d cwnd=%d cwnd_left=%d srtt_us=%d loop_gap_ms=0 "
            "loop_gaps=0 skipped=0 rate_dropping=0 rate_backlog=0 rate_slots=0 "
            "rate_dropped=0 judgement=%s"
            % (now, cause, stall_ms, stall_threshold, offered, exited,
               video_queue, silence_ms, LM_SILENCE_S * 1000, unanswered,
               LM_MIN_PROVE, lost, sent, permille, window_ms,
               LM_MIN_PACKETS, cwnd, cwnd_left, srtt_us, judgement))


def _make_closed(now="21:14:02.124"):
    return ("%s quic    ⛔ [192.168.0.2]:50875: DEAD LINE — the QUIC connection "
            "is closing (one single CONNECTION_CLOSE, sent)." % now)


def _fab_rq(since_ms=1002, lost_d=3, sent_d=410):
    return ("21:14:00.000 wt      quic-net [192.168.0.2]:50875 since_ms=%d "
            "lost=7 lost_d=%d bytes_lost=9856 bytes_lost_d=4224 sent=48210 "
            "sent_d=%d bytes_sent=59284410 received=3011 received_d=61 "
            "discarded=0 discarded_d=0 cwnd=48000 cwnd_left=0 ssthresh=32000 "
            "in_flight=47180 srtt_us=41230 latest_us=52980 rttvar_us=11400 "
            "min_rtt_us=22100 net_queue_us=19130 pto_us=132000 dgram_lost=0 "
            "dgram_lost_d=0 dgram_ok=99 dgram_spurious=1 dgram_spurious_d=0 "
            "judgement=-- nothing to report" % (since_ms, lost_d, sent_d))


def _make_eviction(now="21:14:31.500", mute=15412, chi=ACCOUNT):
    return ("%s rcp     ⭐ EVICTION for silence: %d ms without a PACKET from "
            "[192.168.0.2]:50875 (threshold 15000 ms) — the slot of %s goes to the "
            "client arriving from [192.168.0.2]:50999 (§4.4: whoever is silent is "
            "detached; §8.2 is NOT violated) (slots taken now: 0)"
            % (now, mute, chi))


def _make_refusal(now="21:14:20.100", mute=4020, on=True):
    return ("%s rcp     slot DENIED to %s from [192.168.0.2]:50999: another "
            "client of this same user holds it (taken: 1) — that occupant "
            "gave a sign of life %d ms ago, and the eviction %s"
            % (now, ACCOUNT, mute,
               "did NOT fire (threshold in force)" if on else "is switched OFF by hand (--eviction-ms 0)"))


def _make_taken(now="21:14:31.510", chi=ACCOUNT):
    return ("%s rcp     slot TAKEN by %s via [192.168.0.2]:50999 "
            "(taken now: 1)" % (now, chi))


def _make_denied(now="21:14:20.100"):
    return ("%s rcp     ⛔ EVICTION DENIED: the slot belongs to «%s» and the one asking "
            "is «%s» — between different users there is NEVER an eviction, and this registry "
            "should not even be able to propose it" % (now, ACCOUNT, ACCOUNT2))


def _make_samples(seconds=60.0, step=0.1, period=5.0, byte_round=130,
                  packets_per_round=2, background_byte_s=0.0, background_pkt_s=0.0):
    """Counter samples: one «round» of PINGs every `period` seconds.

    ⭐ Manufacturing the samples and not the numbers is what makes the control real:
       the reduction must be able to find the EVENTS inside a counter that rises in
       steps, and it is the only thing that can say whether the PINGs went to 5 s.
    """
    samples, b, p, t, rest = [], 1000, 10, 0.0, 0.0
    upcoming = period
    while t < seconds:
        if t >= upcoming:
            b += byte_round
            p += packets_per_round
            upcoming += period
        # ⛔ The background moves the packets TOO, or it is not a background: it is precisely
        #    what makes the events invisible, and it is the case to test.
        b += int(background_byte_s * step)
        rest += background_pkt_s * step
        p += int(rest)
        rest -= int(rest)
        samples.append([round(t, 3), b, p])
        t += step
    return samples


def _certify_contract():
    """⛔⛔ THE CONTRACT ON THE TEXT IS TESTED ON THE TEXT — and against the SOURCE.

    The `dead-line` line is a contract: if the product changes the order of its
    fields, a bench doing `split('=')` would read the wrong field
    **without noticing**.  ⇒ Here the order of the fields is reread from
    `src/webtransport.c` and compared with what this bench expects.

    ⚠ If the source is not there (the bench runs elsewhere), this check KEEPS QUIET:
      «I did not look» is not «it is fine».
    """
    path = os.path.join(os.path.dirname(HERE), "src", "webtransport.c")
    if not os.path.exists(path):
        return None, "⚠ «%s» is not there: I did not reread the contract from the source" % path
    text = open(path, encoding="utf-8", errors="replace").read()
    i = text.find('"dead-line %s cause=')
    if i < 0:
        return (False, "⛔ in `webtransport.c` I no longer find the format line "
                       "that begins with «dead-line %s cause=»: the contract "
                       "has changed, and this bench would read fields that are no "
                       "longer there")
    # ⛔ The format is split over several adjacent C literals: they are stitched back.
    pieces, j = [], i
    while True:
        a = text.find('"', j)
        if a < 0:
            break
        b = text.find('"', a + 1)
        if b < 0:
            break
        piece = text[a + 1:b]
        pieces.append(piece)
        j = b + 1
        # the end of the format: the literal that contains `judgement=`
        if "judgement=" in piece:
            break
        # and if between one literal and the next there is anything but spaces, it is over
        if text[b + 1:text.find('"', b + 1) if text.find('"', b + 1) > 0
                 else b + 1].strip() not in ("",):
            break
    fmt = "".join(pieces)
    names = [x.split("=")[0] for x in fmt.split() if "=" in x]
    if names != FIELDS_LM:
        return (False, "⛔ THE CONTRACT HAS CHANGED: the source writes the fields "
                       "%s, this bench expects %s" % (names, FIELDS_LM))
    if not fmt.rstrip().endswith("judgement=%s"):
        return (False, "⛔ `judgement=` is no longer the LAST field: the value "
                       "contains spaces, and a field after it would be read "
                       "inside the judgement")
    return (True, "⭐ the contract is that one: %d fields in order, and `judgement=` "
                  "last — reread from `src/webtransport.c`" % len(names))


def import_fake():
    """⛔ The positive control does not touch the machine, but it needs the
       THRESHOLDS of `09-b76` (`MIN_COVERAGE`, `FROZEN_SCREEN_GAP_S`): those
       are the yardstick with which test 6 says «it behaves as in the grid».

    ⚠ The module is just imported, **without** hooking the network to it: `NETWORK` stays
      `None` and no function that talks to the machine is reachable from
      here — it is the same form as `09-b76.import_fake()`.
    ⛔ And the two thresholds are REREAD from there instead of copied: two copies of the
       same threshold in two files are two thresholds that diverge.
    """
    global B76
    if B76 is None:
        B76 = _load("b76rete", os.path.join(HERE, "09-b76-rete-cattiva.py"))


def certify():
    print("⭐ CERTIFICATION OF THE BENCH OF THE TWO CURES — the expected outcome is written FIRST\n")
    print("   ⛔ No contact with the test machine: here the TOOL is tested, "
          "\n      not the product.\n")
    import_fake()
    green = True
    cases = []

    def test_case(name, expected, got):
        """`expected` is `True`/`False`/`None` — green, red, mute."""
        passes, why = got
        ok = (passes is expected)
        cases.append({"case": name, "expected": expected, "got": passes,
                     "why": why})
        (_ok if ok else _ko)("%s → expected %s, got %s%s"
                             % (name, expected, passes,
                                "" if ok else "  ⛔ «%s»" % why[:150]))
        return ok

    # ── 0 · the contract on the text, reread from the source ───────────────
    _log("0 · THE CONTRACT OF THE `dead-line` LINE, reread from `src/`")
    passes, why = _certify_contract()
    (_ok if passes else (_dub if passes is None else _ko))(why)
    if passes is False:
        green = False

    # ── 1 · the reductions, on manufactured TEXT ─────────────────────
    _log("1 · THE REDUCTIONS — manufactured text inside the same functions as the "
         "real runs")
    lm = reduce_dead_line([_fab_lm()])
    ok = (lm["outcome"] == "read" and lm["notches"] == 1
          and lm["cause"] == "stall" and lm["stall_ms"] == 5004
          and lm["stall_threshold_ms"] == LM_STALL_MS and lm["offered"] == 41
          and lm["bytes_out"] == 0 and lm["video_queue"] == 61240
          and lm["permille"] == 75 and lm["sent"] == 412
          and lm["cwnd_left"] == 0
          and lm["judgement"].startswith("⛔ the line is DEAD")
          and abs(lm["ora_primo"] - (21 * 3600 + 14 * 60 + 2.123)) < 1e-6)
    (_ok if ok else _ko)("the `dead-line` line is read field by field, "
                         "`judgement=` included (with its spaces): %s"
                         % json.dumps({k: lm.get(k) for k in
                                       ("cause", "stall_ms", "offered",
                                        "bytes_out", "video_queue", "permille",
                                        "silence_ms", "unanswered")},
                                      ensure_ascii=False))
    green = green and ok

    # ⛔⛔ AND THE TWO REMOVED FIELDS MUST STAY REMOVED: a bench that kept on
    #     reading `threshold_permille=` on a line that no longer has it would not
    #     give an error — it would read `None` and judge on it.
    ok = (lm.get("threshold_permille") is None
          and (lm["lines"][0].get("windows") is None))
    (_ok if ok else _ko)("⛔ `soglia_permille=` and `finestre=N/M` are NO longer "
                         "in the line, and the bench does not look for them: the threshold "
                         "on loss does not exist (threshold_permille=%s, "
                         "windows=%s)"
                         % (lm.get("threshold_permille"),
                            lm["lines"][0].get("windows")))
    green = green and ok

    lm0 = reduce_dead_line([])
    dlx = reduce_dead_line([], read=False)
    ok = (lm0["outcome"] == "read" and lm0["notches"] == 0
          and dlx["outcome"] != "read")
    (_ok if ok else _ko)("⛔⛔ «zero firings» and «I did not read» do NOT look "
                         "the same: «%s» against «%s»"
                         % (lm0["outcome"], dlx["outcome"][:60]))
    green = green and ok

    sf = reduce_eviction([_make_refusal(), _make_refusal(), _make_eviction(),
                         _make_taken()])
    ok = (sf["evictions"] == 1 and sf["refusals"] == 2 and sf["grabbed"] == 1
          and sf["muto_ms"] == 15412 and sf["sfrattato"] == ACCOUNT
          and sf["denied"] == 0 and sf["ultimo_rifiuto_muto_ms"] == 4020
          and sf["sfratto_dice"] == "did NOT fire")
    (_ok if ok else _ko)("the three eviction marks are read: %d evictions, "
                         "%d refusals, silent %s ms, evicted «%s», the refusal "
                         "line says «%s»"
                         % (sf["evictions"], sf["refusals"], sf.get("muto_ms"),
                            sf.get("sfrattato"), sf.get("sfratto_dice")))
    green = green and ok

    sf2 = reduce_eviction([_make_refusal(on=False), _make_denied()])
    ok = (sf2["denied"] == 1 and sf2["evictions"] == 0
          and sf2["sfratto_dice"] == "SPENTO")
    (_ok if ok else _ko)("the «EVICTION DENIED» line and the refusal with the eviction OFF "
                         "are told apart: denied %d, says «%s»"
                         % (sf2["denied"], sf2.get("sfratto_dice")))
    green = green and ok

    # ⭐ The declared windows: two windows in a row above threshold inside a
    #    heap of good windows, and the cure's guards discarding those
    #    too short or too empty.
    lines = ([_fab_rq(lost_d=2, sent_d=400)] * 20
             + [_fab_rq(lost_d=30, sent_d=400)] * 2
             + [_fab_rq(lost_d=2, sent_d=400)] * 20
             + [_fab_rq(lost_d=90, sent_d=100)]      # ⛔ few packets
             + [_fab_rq(lost_d=90, sent_d=400, since_ms=400)])  # ⛔ short window
    fin = declared_windows(lines)
    ok = (fin["outcome"] == "read" and fin["finestre_valide"] == 42
          and fin["permille_max"] == 75 and fin["sopra_soglia"] == 2
          and fin["coppie_sopra_soglia"] == 1
          and fin["fila_massima_sopra_soglia"] == 2)
    (_ok if ok else _ko)("⛔ the cure's GUARDS apply: 44 lines, %d "
                         "valid windows (the two below %d packets / below %d "
                         "ms are discarded), max %d‰, %d pairs in a row above "
                         "threshold" % (fin["finestre_valide"], LM_MIN_PACKETS,
                                     LM_WINDOW_MS, fin["permille_max"],
                                     fin["coppie_sopra_soglia"]))
    green = green and ok

    fin0 = declared_windows([_fab_rq(lost_d=1, sent_d=10)] * 30)
    ok = fin0["outcome"].startswith("I DO NOT JUDGE")
    (_ok if ok else _ko)("⭐ and if NO window passes the guards, the "
                         "reconstruction REFUSES instead of saying «zero»: «%s»"
                         % fin0["outcome"][:110])
    green = green and ok

    gold = reduce_clock(_make_samples(period=5.0))
    ok = (gold["outcome"] == "measured" and abs(gold["intervallo_mediano_s"] - 5.0) < 0.3
          and gold["events"] >= 10)
    (_ok if ok else _ko)("the wire clock finds the PING rounds inside the "
                         "counter: %d events, median interval %s s, %.4f "
                         "kbit/s, %s bytes per round"
                         % (gold["events"], gold.get("intervallo_mediano_s"),
                            gold["kbit_s"], gold.get("byte_per_evento")))
    green = green and ok

    gold10 = reduce_clock(_make_samples(period=10.0))
    ok = (gold10["outcome"] == "measured"
          and abs(gold10["intervallo_mediano_s"] - 10.0) < 0.3)
    (_ok if ok else _ko)("⭐ and it can tell 10 s from 5: median interval %s s"
                         % gold10.get("intervallo_mediano_s"))
    green = green and ok

    goldF = reduce_clock(_make_samples(period=5.0, background_byte_s=180000,
                                         background_pkt_s=190.0))
    ok = (goldF["outcome"] == "measured" and goldF["intervallo_mediano_s"] is None
          and "is NOT still" in goldF.get("perche_niente_intervallo", ""))
    (_ok if ok else _ko)("⛔ and on a session that is NOT still (audio background) it "
                         "refuses to give an interval instead of inventing "
                         "one: «%s»" % goldF.get("perche_niente_intervallo", "")[:90])
    green = green and ok

    ok = (abs(dt_log("00:00:01.500 x", "23:59:59.500 x") - 2.0) < 1e-6
          and dt_log("nessuna ora", "23:59:59.500 x") is None)
    (_ok if ok else _ko)("the log clock steps over midnight, and "
                         "«I do not know» is not «zero seconds»")
    green = green and ok

    # ── 2 · the six predicates: GREEN, RED and MUTE ───────────────────────
    _log("2 · THE SIX PREDICATES — and each must be able to give red, not only green")

    witness_alive = {"is_open": True, "cliente_attaccato": True,
                      "cliente_staccato": False, "congedi": []}
    witness_dropped = {"is_open": True, "cliente_attaccato": False,
                        "cliente_staccato": True, "drop": "the session dropped",
                        "congedi": []}
    good_round = {"fps": 9.1, "delivery": {"outcome": "measured", "coverage": 1.0,
                                           "buco_max_s": 0.37}}
    sluggish_round = {"fps": 1.2, "delivery": {"outcome": "measured", "coverage": 0.4,
                                            "buco_max_s": 6.0}}

    _inf("P1 · ⛔⛔ the false positive")
    green &= test_case("P1 green · zero firings on a line that holds", True,
                  p1_no_false_positive(lm0, witness_alive, good_round, 10))
    green &= test_case("P1 RED · one firing on a line that holds", False,
                  p1_no_false_positive(lm, witness_alive, good_round, 10))
    green &= test_case("P1 mute · zero firings but the line was not holding", None,
                  p1_no_false_positive(lm0, witness_alive, sluggish_round, 10))
    green &= test_case("P1 mute · zero firings but the client dropped for other reasons", None,
                  p1_no_false_positive(lm0, witness_dropped, good_round, 10))
    green &= test_case("P1 mute · I did not read the log", None,
                  p1_no_false_positive(dlx, witness_alive, good_round, 10))

    _inf("P1c · ⛔⛔ the CONTROL: the same line with the cures off")
    round_holds = {"fps": 9.1, "delivery": {"outcome": "measured", "coverage": 0.99,
                                           "buco_max_s": 0.42,
                                           "consegna_fino_a_s": 599.8}}
    round_does_not_hold = {"fps": 1.1, "delivery": {"outcome": "measured",
                                               "coverage": 0.30,
                                               "buco_max_s": 40.0,
                                               "consegna_fino_a_s": 22.0}}
    round_stops = {"fps": 8.0, "delivery": {"outcome": "measured",
                                              "coverage": 0.40,
                                              "buco_max_s": 30.0,
                                              "consegna_fino_a_s": 240.0}}
    green &= test_case("P1c green · with the cures off the same line holds 10 minutes",
                  True, p1c_line_holds_with_fix_off(witness_alive,
                                                         round_holds, 10, 1))
    green &= test_case("P1c RED · ⛔ it drops even with the cures off: the red of test 1 is "
                  "not a false positive", False,
                  p1c_line_holds_with_fix_off(witness_dropped,
                                                   round_holds, 10, 1))
    green &= test_case("P1c RED · with the cures off the rate is below the bench's "
                  "floor", False,
                  p1c_line_holds_with_fix_off(witness_alive,
                                                   round_does_not_hold, 10, 1))
    green &= test_case("P1c RED · with the cures off delivery stops anyway",
                  False, p1c_line_holds_with_fix_off(witness_alive,
                                                          round_stops, 10, 1))
    green &= test_case("P1c mute · I do not have the numbers of the control run", None,
                  p1c_line_holds_with_fix_off(witness_alive,
                                                   {"fps": None}, 10, 1))

    _inf("P1b · ⭐⭐ the TRUE MARGIN — the scale that tracks down the maximum stall")
    home_probe = {"outcome": "measured", "persi_pc": 1.86, "raffica_media": 1.02}
    wide_ladder = [{"soglia_ms": 2000, "scattata": False},
                   {"soglia_ms": 1000, "scattata": False},
                   {"soglia_ms": 500, "scattata": False}]
    tight_ladder = [{"soglia_ms": 2000, "scattata": False},
                     {"soglia_ms": 1000, "scattata": True, "stall_ms": 1043}]
    tightest_ladder = [{"soglia_ms": 3000, "scattata": True,
                           "stall_ms": 3120}]
    ladder_already_fired = [{"soglia_ms": LM_STALL_MS, "scattata": True,
                           "stall_ms": 5300}]
    slightly_lower_ladder = [{"soglia_ms": 4000, "scattata": False}]
    green &= test_case("P1b green · it does not fire even at 500 ms ⇒ margin > 10×",
                  True, p1b_stall_margin(wide_ladder, LM_STALL_MS,
                                                    "bad-home"))
    green &= test_case("P1b green · fires at 1000 with stall 1043 ms ⇒ margin 4.8×",
                  True, p1b_stall_margin(tight_ladder, LM_STALL_MS,
                                                    "burst-1"))
    green &= test_case("P1b RED · ⛔ stall 3120 ms on a line that holds: "
                  "margin 1.6×", False,
                  p1b_stall_margin(tightest_ladder, LM_STALL_MS,
                                              "bad-home"))
    green &= test_case("P1b mute · it already fired at the threshold in force: it is the "
                  "false positive, and P1 says so", None,
                  p1b_stall_margin(ladder_already_fired, LM_STALL_MS,
                                              "bad-home"))
    green &= test_case("P1b mute · the scale did not go down enough to give a "
                  "margin", None,
                  p1b_stall_margin(slightly_lower_ladder, LM_STALL_MS,
                                              "bad-home"))
    green &= test_case("P1b mute · no scale tried", None,
                  p1b_stall_margin([], LM_STALL_MS, "bad-home"))

    _inf("P-raffica1 · ⭐ the line that delivers 24/s with an empty second")
    expected_r1 = GRID_B76["burst-1"]
    round_r1 = {"fps": 23.94, "delivery": {"outcome": "measured", "coverage": 0.96,
                                          "buco_max_s": 1.00}}
    round_r1_out = {"fps": 3.0, "delivery": {"outcome": "measured",
                                              "coverage": 0.5,
                                              "buco_max_s": 8.0}}
    lm_stall = reduce_dead_line([_fab_lm(cause="stall")])
    lm_stall["chiuse_dal_trasporto"] = 1
    green &= test_case("P-raffica1 green · zero firings and the line is within the grid",
                  True, p_must_not_fire("burst-1", lm0, witness_alive,
                                            round_r1, 1, expected_r1))
    green &= test_case("P-raffica1 RED · ⛔⛔ declared dead a line that "
                  "delivers 24 frames/s", False,
                  p_must_not_fire("burst-1", lm_stall, witness_alive,
                                      round_r1, 1, expected_r1))
    green &= test_case("P-raffica1 mute · the run is not the grid's one", None,
                  p_must_not_fire("burst-1", lm0, witness_alive,
                                      round_r1_out, 1, expected_r1))
    green &= test_case("P-raffica1 mute · the client dropped for other reasons", None,
                  p_must_not_fire("burst-1", lm0, witness_dropped,
                                      round_r1, 1, expected_r1))

    _inf("P-scena-ferma · ⛔⛔ the worst way in which the cure could fail")
    lm_scene = reduce_dead_line([_fab_lm(cause="stall", stall_ms=1004,
                                           stall_threshold=1000, offered=0,
                                           exited=0, video_queue=0)])
    lm_scene["chiuse_dal_trasporto"] = 1
    green &= test_case("P-scena-ferma green · 120 s of still desktop at threshold 1000, "
                  "zero firings", True,
                  p_still_scene_no_fire(lm0, witness_alive, 120, 1000))
    green &= test_case("P-scena-ferma RED · ⛔⛔ throws out whoever looks at a still "
                  "desktop (offered=0, video_queue=0)", False,
                  p_still_scene_no_fire(lm_scene, witness_alive, 120, 1000))
    green &= test_case("P-scena-ferma mute · the client dropped for other reasons", None,
                  p_still_scene_no_fire(lm0, witness_dropped, 120, 1000))
    green &= test_case("P-scena-ferma mute · I did not read the log", None,
                  p_still_scene_no_fire(dlx, witness_alive, 120, 1000))

    _inf("P2 · the real firing")
    probe_burst = {"outcome": "measured", "persi_pc": 11.10, "raffica_media": 5.5}
    lm_p = reduce_dead_line([_fab_lm(cause="stall")])
    lm_p["chiuse_dal_trasporto"] = 1
    lm_p_without_wire = reduce_dead_line([_fab_lm(cause="stall")])
    lm_p_without_wire["chiuse_dal_trasporto"] = 0
    lm_s = reduce_dead_line([_fab_lm(cause="silence", stall_ms=800,
                                       silence_ms=10004, unanswered=3)])
    lm_s["chiuse_dal_trasporto"] = 1
    lm0["chiuse_dal_trasporto"] = 0
    green &= test_case("P2 green · fired with cause=stall and the wire dropped", True,
                  p2_fires_on_stall(lm_p, probe_burst, 18.4))
    green &= test_case("P2 RED · it did not fire on a line that cannot be served",
                  False, p2_fires_on_stall(lm0, probe_burst, None))
    green &= test_case("P2 RED · fired for silence instead of stall", False,
                  p2_fires_on_stall(lm_s, probe_burst, 12.0))
    green &= test_case("P2 RED · decided but the wire did NOT drop", False,
                  p2_fires_on_stall(lm_p_without_wire, probe_burst, 18.4))
    green &= test_case("P2 mute · the fault was not put in place", None,
                  p2_fires_on_stall(lm_p, home_probe, 18.4))
    green &= test_case("P2 mute · the probe did not measure", None,
                  p2_fires_on_stall(lm_p, None, 18.4))

    _inf("P3 · silence")
    lm_early = reduce_dead_line([_fab_lm(cause="silence", silence_ms=6100)])
    lm_early["chiuse_dal_trasporto"] = 1
    lm_late = reduce_dead_line([_fab_lm(cause="silence", silence_ms=21000)])
    lm_late["chiuse_dal_trasporto"] = 1
    green &= test_case("P3 green · fired at 10.0 s with cause=silence", True,
                  p3_fires_on_silence(lm_s, LM_SILENCE_S * 1000))
    green &= test_case("P3 RED · it did not fire: the ghost stays until 30 s", False,
                  p3_fires_on_silence(lm0, LM_SILENCE_S * 1000))
    green &= test_case("P3 RED · ⛔ fired BEFORE the threshold (a live and idle "
                  "client would be thrown out)", False,
                  p3_fires_on_silence(lm_early, LM_SILENCE_S * 1000))
    green &= test_case("P3 RED · fired long after the threshold (form E1)", False,
                  p3_fires_on_silence(lm_late, LM_SILENCE_S * 1000))
    green &= test_case("P3 RED · fired for stall and not for silence", False,
                  p3_fires_on_silence(lm_p, LM_SILENCE_S * 1000))
    green &= test_case("P3 mute · I did not read the log", None,
                  p3_fires_on_silence(dlx, LM_SILENCE_S * 1000))

    _inf("P3b · the declared price of the PINGs")
    idle_on = {"outcome": "measured", "kbit_s": 0.21, "packets": 24,
                    "seconds": 60.0}
    idle_off = {"outcome": "measured", "kbit_s": 0.10, "packets": 12,
                    "seconds": 60.0}
    idle_costly = {"outcome": "measured", "kbit_s": 1.30, "packets": 160,
                  "seconds": 60.0}
    audio_on = {"outcome": "measured", "kbit_s": 1412.0, "packets": 11800,
                    "seconds": 60.0}
    audio_off = {"outcome": "measured", "kbit_s": 1409.0, "packets": 11790,
                    "seconds": 60.0}
    green &= test_case("P3b green · the difference is within the declared one", True,
                  p3b_ping_cost(idle_on, idle_off))
    green &= test_case("P3b RED · the PINGs cost more than declared", False,
                  p3b_ping_cost(idle_costly, idle_off))
    green &= test_case("P3b mute · ⛔ the background is bigger than the target", None,
                  p3b_ping_cost(audio_on, audio_off))
    green &= test_case("P3b mute · one of the two measurements is missing", None,
                  p3b_ping_cost(idle_on, {"outcome": "I DO NOT JUDGE"}))

    _inf("P4 · the eviction")
    sf_ok = reduce_eviction([_make_refusal(), _make_eviction(), _make_taken()])
    sf_early = reduce_eviction([_make_eviction(mute=9000), _make_taken()])
    sf_nothing = reduce_eviction([_make_refusal()] * 11 + [_make_taken()])
    green &= test_case("P4 green · the slot becomes free again at ~15 s", True,
                  p4_eviction_frees_slot(sf_ok, RECOMMENDED_EVICTION_MS,
                                                15.6, 30.5))
    green &= test_case("P4 RED · no eviction, the silence of §5.3 is waited for",
                  False,
                  p4_eviction_frees_slot(sf_nothing, RECOMMENDED_EVICTION_MS,
                                                30.5, 30.5))
    green &= test_case("P4 RED · ⛔ evicted BEFORE the threshold (I2 off)", False,
                  p4_eviction_frees_slot(sf_early, RECOMMENDED_EVICTION_MS,
                                                9.2, 30.5))
    green &= test_case("P4 RED · evicted, but the slot still takes 28 s",
                  False,
                  p4_eviction_frees_slot(sf_ok, RECOMMENDED_EVICTION_MS,
                                                28.0, 30.5))
    green &= test_case("P4 mute · I do not know when the slot was taken back", None,
                  p4_eviction_frees_slot(sf_ok, RECOMMENDED_EVICTION_MS,
                                                None, 30.5))

    _inf("P5 · ⛔ two different users")
    sf_due_ok = reduce_eviction([_make_taken(chi=ACCOUNT), _make_taken(chi=ACCOUNT2)])
    sf_hole = reduce_eviction([_make_eviction(chi=ACCOUNT), _make_taken(chi=ACCOUNT2)])
    green &= test_case("P5 green · no eviction and the second user gets in", True,
                  p5_no_eviction_across_users(sf_due_ok, True,
                                                       ACCOUNT, ACCOUNT2))
    green &= test_case("P5 RED · ⛔⛔ eviction between different users = security hole",
                  False,
                  p5_no_eviction_across_users(sf_hole, True,
                                                       ACCOUNT, ACCOUNT2))
    green &= test_case("P5 mute · no eviction, but the second did not get in", None,
                  p5_no_eviction_across_users(sf_due_ok, False,
                                                       ACCOUNT, ACCOUNT2))
    green &= test_case("P5b green · the «EVICTION DENIED» line does NOT come out (predicted `[R]`)",
                  True, p5b_denied_line(sf_due_ok))
    green &= test_case("P5b RED · the line COMES OUT, that is my reading was wrong",
                  False, p5b_denied_line(reduce_eviction([_make_denied()])))

    _inf("P6 · ⛔ the defaults change nothing (I6)")
    off = {"outcome": "read", "dead_line": "spenta", "stall_ms": None,
              "silence_s": None, "eviction_ms": 0, "lines": []}
    on = {"outcome": "read", "dead_line": "enabled", "stall_ms": LM_STALL_MS,
              "silence_s": LM_SILENCE_S, "eviction_ms": RECOMMENDED_EVICTION_MS,
              "lines": []}
    sf_empty = reduce_eviction([_make_taken()])
    round_home = {"fps": 9.1, "delivery": {"outcome": "measured", "coverage": 0.96,
                                          "buco_max_s": 0.42}}
    round_home_out = {"fps": 22.0, "delivery": {"outcome": "measured",
                                                 "coverage": 1.0,
                                                 "buco_max_s": 0.1}}
    burst_round = {"fps": 2.1, "delivery": {"outcome": "measured", "coverage": 0.28,
                                             "buco_max_s": 14.26}}
    healthy_burst_round = {"fps": 30.0, "delivery": {"outcome": "measured",
                                                   "coverage": 1.0,
                                                   "buco_max_s": 0.2}}
    green &= test_case("P6 green · cures off, «bad-home» as in the b76 grid",
                  True, p6_defaults_change_nothing(
                      lm0, sf_empty, off, round_home, "bad-home"))
    green &= test_case("P6 green · cures off, «burst-heavy» stops as it does there",
                  True, p6_defaults_change_nothing(
                      lm0, sf_empty, off, burst_round, "burst-heavy"))
    green &= test_case("P6 RED · ⛔ I6: the cure is off and fired anyway",
                  False, p6_defaults_change_nothing(
                      lm_p, sf_empty, off, round_home, "bad-home"))
    green &= test_case("P6 RED · ⛔ I6: the eviction is off and there was an eviction",
                  False, p6_defaults_change_nothing(
                      lm0, sf_ok, off, round_home, "bad-home"))
    green &= test_case("P6 RED · the profile leaves the grid of 09-b76", False,
                  p6_defaults_change_nothing(
                      lm0, sf_empty, off, round_home_out, "bad-home"))
    green &= test_case("P6 RED · «burst-heavy» NO longer stops: the product has "
                  "changed", False, p6_defaults_change_nothing(
                      lm0, sf_empty, off, healthy_burst_round, "burst-heavy"))
    green &= test_case("P6 mute · the server was NOT on the defaults", None,
                  p6_defaults_change_nothing(
                      lm0, sf_empty, on, round_home, "bad-home"))

    # ── 3 · the configuration guard ────────────────────────────────────
    _log("3 · THE GUARD — «is the server configured as this test believes?»")
    green &= test_case("cures ON as I want them", True,
                  fixes_as_wanted(on, dead_line="enabled",
                                   stall_ms=LM_STALL_MS,
                                   eviction_ms=RECOMMENDED_EVICTION_MS))
    green &= test_case("⛔ mute if the dead line turns out OFF when I wanted it "
                  "on", None,
                  fixes_as_wanted(off, dead_line="enabled"))
    green &= test_case("⛔ mute if the STALL threshold is not the one I believe", None,
                  fixes_as_wanted(on, dead_line="enabled", stall_ms=1))
    green &= test_case("⛔ mute if I did not read the startup line", None,
                  fixes_as_wanted({"outcome": "⛔ I DID NOT READ any line"},
                                   dead_line="enabled"))

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "09-b81-certifica.json"), "w") as f:
        json.dump(cases, f, ensure_ascii=False, indent=1)
    _log("OUTCOME OF THE CERTIFICATION")
    _inf("%d cases, %d wrong · details in %s/09-b81-certifica.json"
         % (len(cases), len([c for c in cases if c["got"] is not c["expected"]]),
            OUT))
    if green:
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
LEASE = 900        # ⛔ SHORT leases, renewed: other agents are queued


def near():
    """⛔ The ports that are NOT mine: they are COUNTED before and after, not touched."""
    report = []
    for p in NEARBY_PORTS:
        rc, o, _ = root("bash -c \"ss -uln 2>/dev/null | grep -c ':%s ' || true\"" % p)
        report.append("%s:%s" % (p, o.strip()))
    return " ".join(report)


def get_ready():
    """The scripts on the machine, and the probe's port chosen NOW.

    ⛔ The probe's port cannot be fixed: while I run, another agent
       may start a server on the one I had seen free (`09-b76`).
    """
    if not B76.ship_probe():
        _ko("the scripts of the probe / of the reader were not written in %s" % WORKDIR)
        return False
    if not B76.write_on_machine("09-b81-orologio.py", CLOCK):
        _ko("the wire clock was not written in %s" % WORKDIR)
        return False
    if B76.choose_probe_port() is None:
        _ko("⛔ none of my ports for the probe is free: I do NOT measure, "
            "because without a probe I do not know whether the fault was put in place")
        return False
    fingerprints = B78.ship_sources()
    if fingerprints is None:
        _ko("`09-b78-apertura.py` / `01-b3-cliente.py` did not arrive in the tree")
        return False
    _ok("scripts ready · probe on port %d · %s"
        % (B76.PROBE_PORT, " · ".join(fingerprints)))
    _inf("ports NOT mine (counted, not touched): %s" % near())
    return True


def turn_on_server(options, why):
    """⛔ Restarts MY server (unit `%s`) with those options, and THEN
       rereads from the startup line that it really took them.

    ⚠ An option typed through `ssh` → `sudo` → `systemd-run` → `bash -lc`
      has four ways of getting lost on the way, and none of the four gives an error:
      it gives a server running on the defaults while the bench believes it is measuring
      a cure that is on.
    """ % UNIT
    _log("THE SERVER IS RESTARTED — %s" % why)
    _inf("options: %s" % (options or "(none: the defaults, that is I6)"))
    env = dict(os.environ)
    env["SERVER_OPTIONS"] = options
    env["UNIT"] = UNIT
    p = subprocess.run(["bash", os.path.join(HERE, "09-b81-terreno.sh"), "start"],
                       env=env, capture_output=True, timeout=420)
    text = (p.stdout + p.stderr).decode("utf-8", "replace")
    for r in text.splitlines():
        if re.search(r"server \d+ on port|NO |the server did not start", r):
            _inf(r.strip()[:180])
    if p.returncode != 0:
        _ko("⛔ the server did not restart: %s" % text[-400:])
        return False
    status = fixes_state()
    _inf("the server says of itself: dead line %s (stall %s ms, silence %s s) · "
         "eviction %s ms"
         % (status["dead_line"], status["stall_ms"], status["silence_s"],
            status["eviction_ms"]))
    # ⛔ The stage and the monitor are born with the FIRST client: without it, the scene would not
    #    know where to draw (`09-b70.trigger_session`).
    if not B70.trigger_session():
        _ko("the priming session does not open: the stage is not there")
        return False
    _ok("server restarted and stage primed")
    return True


@contextlib.contextmanager
def broken_network(rules, expected_s, wait=1800):
    """⛔ The lock, the guardian and the `netem`, taken and given back TOGETHER.

    · the lock because the `netem` on `lo` is only one for the whole machine,
      and two benches breaking it together do not give a red: they give a
      plausible number (`LEZIONI.md` §1.26);
    · the guardian because the network must go back as it was **even if I die**;
    · the `u32` filters on %d only, and `enp7s0` is NEVER touched.
    """ % PORT
    LUC.take(CHI, seconds=LEASE, wait=wait)
    NETWORK.guardian_arm(min(3600, expected_s + 600))
    placed = False
    try:
        ok, q = NETWORK.tighten(rules)
        if not ok:
            raise SystemExit("⛔ tc refused the rule: %s" % q)
        placed = True
        B76.probe_filters()
        reread = B76.rule_reread()
        # ⛔ The rule is REREAD: `tc qdisc change` is sticky, and `[M]` 23
        #    Aug 2026 it dragged a `reorder` along for four profiles.
        passes, why = B76.check_rule([x for x in rules if x != "limit"
                                              and not x.isdigit()], reread)
        (_ok if passes else _ko)("the rule: %s" % why)
        if not passes:
            raise SystemExit("⛔ the installed rule is not the one requested")
        yield reread
    finally:
        _log("⛔ THE NETWORK IS PUT BACK AS IT WAS")
        if not NETWORK.restore():
            _ko("⛔ the network did NOT go back as it was: put it back by hand with «restore»")
        LUC.release(CHI)
        if placed:
            _inf("ports NOT mine after the run: %s" % near())


def profile(name):
    """The `netem` rules of a profile of `09-b76`, taken from there and not copied."""
    for p in B76.PROFILES:
        if p[0] == name:
            return p
    raise SystemExit("⛔ profile «%s» is not in 09-b76" % name)


def probe(name):
    """The probe of `09-b76`, and its verdict «was the fault put in place?»."""
    s = B76.run_probe()
    B76.print_probe(s)
    p = profile(name)
    passes, why = B76.p_fault_set(name, p[6], s)
    (_ok if passes else (_dub if passes is None else _ko))(
        "THE FAULT WAS PUT IN PLACE: %s" % why)
    return s, (passes, why)


def background_client(user, password_inside, seconds, mark):
    """⛔ The client INSIDE the chroot, detached from my `ssh`: it must be
       still alive when I kill it, and `enter.sh` is a `chroot` — so the
       process is seen and killed from the HOST with its real pid."""
    inside = ("python3 -u %s/banchi/01-b3-cliente.py --address %s --port %d "
              "--user %s --password-file %s --audio-codec pcm --video-codec h264 "
              "--fit 1920x1080 --stay %d"
              % (INSIDE_TREE, ADDR, PORT, user, password_inside, seconds))
    root("bash /media/REMOTIX/enter.sh --root 'setsid nohup %s > %s/%s.log 2>&1 & "
         "sleep 0.5; echo lanciato'" % (inside, INSIDE_WORK, mark), 180)


def client_pid(user):
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
    rc, out, _ = root("bash -c \"pgrep -f '^python3 .*b3-cliente[.]py .*--user "
                      "%s ' | head -1\"" % user)
    t = out.strip().splitlines()
    return int(t[0]) if t and t[0].isdigit() else None


def kill(pid):
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


def clean_up_clients():
    """⚠ Between one test and the next: a client left alive would keep the slot, and
       the next test would measure the previous run's lock."""
    root("bash -c \"pkill -9 -f '^python3 .*b3-cliente[.]py .*--port %d ' ; "
         "true\"" % PORT)


def wait_line(line0, pattern, cap=45.0, step=1.0):
    expires = time.time() + cap
    while True:
        r = read_log(line0, pattern)
        if r or time.time() >= expires:
            return r
        time.sleep(step)


def print_windows(fin):
    if fin.get("outcome") != "read":
        _dub("DECLARED  %s" % fin.get("outcome"))
        return
    _inf("DECLARED  %d valid windows over %d `quic-net` lines · max %d‰ · "
         "p95 %d‰ · median %d‰ · mean %.2f‰"
         % (fin["finestre_valide"], fin["lines"], fin["permille_max"],
            fin["permille_p95"], fin["permille_mediano"], fin["permille_medio"]))
    _inf("            above the threshold of %d‰: %d windows · longest run %d · "
         "pairs (= the firing condition) %d · cumulative %.2f‰ (%d lost out of "
         "%d sent)"
         % (fin["threshold_permille"], fin["sopra_soglia"],
            fin["fila_massima_sopra_soglia"], fin["coppie_sopra_soglia"],
            fin["cumulativa_permille"], fin["persi_totali"],
            fin["spediti_totali"]))
    _inf("            ⭐ the START-UP apart: first %d windows max %s‰ · after: "
         "max %s‰, median %s‰, %s above threshold, longest run %s, pairs %s"
         % (fin["prime_finestre"], fin["permille_max_prime"],
            fin["permille_max_dopo"], fin["permille_mediano_dopo"],
            fin["sopra_soglia_dopo"], fin["fila_massima_dopo"],
            fin["coppie_sopra_soglia_dopo"]))


def print_shots(lm):
    if lm.get("outcome") != "read":
        _dub("FIRINGS  %s" % lm.get("outcome"))
        return
    _inf("FIRINGS  %d `dead-line` line(s) · %d closures by the transport%s"
         % (lm["notches"], lm.get("chiuse_dal_trasporto", 0),
            ("  ⇒ cause=%s stall_ms=%s (threshold %s) offered=%s bytes_out=%s "
             "video_queue=%s · witness permille=%s"
             % (lm.get("cause"), lm.get("stall_ms"),
                lm.get("stall_threshold_ms"), lm.get("offered"),
                lm.get("bytes_out"), lm.get("video_queue"),
                lm.get("permille"))) if lm["notches"] else ""))
    for r in lm.get("lines", [])[:3]:
        _inf("        %s" % r["line"][:240])


def print_eviction(sf):
    if sf.get("outcome") != "read":
        _dub("EVICTION %s" % sf.get("outcome"))
        return
    _inf("EVICTION %d evictions · %d DENIED · %d refusals («slot DENIED») · %d "
         "slots taken · the last refusal said «sign of life %s ms ago» and the "
         "eviction «%s»"
         % (sf["evictions"], sf["denied"], sf["refusals"], sf["grabbed"],
            sf.get("ultimo_rifiuto_muto_ms"), sf.get("sfratto_dice")))
    for r in (sf.get("righe_sfratto") or [])[:2]:
        _inf("        %s" % r[:240])
    for r in (sf.get("righe_negato") or [])[:2]:
        _inf("        %s" % r[:240])


def print_clock(o, come):
    if o.get("outcome") != "measured":
        _dub("WIRE %s  %s" % (come, o.get("outcome")))
        return
    _inf("WIRE %s  %.3f kbit/s (%d bytes, %d packets in %.1f s) · %d events · "
         "median interval %s s (min %s, max %s) · %s bytes per round"
         % (come, o["kbit_s"], o["byte"], o["packets"], o["seconds"],
            o["events"], o.get("intervallo_mediano_s"),
            o.get("intervallo_min_s"), o.get("intervallo_max_s"),
            o.get("byte_per_evento")))
    if o.get("perche_niente_intervallo"):
        _inf("        ⚠ %s" % o["perche_niente_intervallo"])


def round_fps(n):
    """⭐ The rate, and from TWO witnesses: the §11.1 trace if it was read, and the
       count the CLIENT prints by itself otherwise.

    ⛔ The second is not a convenient fallback: over a ten-minute window the
       trace is big, and *«the reader did not answer»* looks identical
       to *«the session delivered nothing»* (`09-b70`, the third face of
       §1.9).  ⇒ With two witnesses, that fault cannot disguise itself as a measurement.
    """
    if B70._has_measured(n) and n.get("fps"):
        return n["fps"], "§11.1 trace"
    d, sec = n.get("from_client"), n.get("secondi_veri")
    if d and sec:
        return round(d["frames"] / float(sec), 2), "the CLIENT's count"
    return None, "no witness of the rate"


def _out(name):
    return os.path.join(OUT, "09-b81-%s.json" % name)


def save(name, stuff):
    os.makedirs(OUT, exist_ok=True)
    with open(_out(name), "w") as f:
        json.dump(stuff, f, ensure_ascii=False, indent=1)


def load(name):
    try:
        with open(_out(name)) as f:
            return json.load(f)
    except Exception:
        return None


def _entries(title, **k):
    v = {"prova": title, "predicates": []}
    v.update(k)
    return v


def _predicate(entries, label, outcome):
    passes, why = outcome
    entries["predicates"].append({"predicate": label, "passes": passes,
                              "why": why})
    (_ok if passes else (_dub if passes is None else _ko))("%s: %s"
                                                         % (label, why))
    return entries


# ═══════════════════════════════════════════════════════════════════════════
# TEST 1 · ⛔⛔ THE FALSE POSITIVE
# ═══════════════════════════════════════════════════════════════════════════
def prova1(a):
    _log("TEST 1 · ⛔⛔ THE FALSE POSITIVE — the test that can make the cure be WITHDRAWN")
    print("   `bad-home` (delay 40ms 20ms distribution normal loss 2%), dead")
    print("   line ON, for %g minutes: the expectation is ZERO firings." % (a.seconds / 60.0))
    print("   ⛔ That line HOLDS (`[M]` 7.8-10.2 frames/s): declaring it")
    print("      dead would mean throwing out someone who was working.")
    v = _entries("1 · the false positive", profile="bad-home", seconds=a.seconds)
    status = fixes_state()
    v["stato_cure"] = status
    va, why = fixes_as_wanted(status, dead_line="enabled",
                                  stall_ms=LM_STALL_MS,
                                  silence_s=LM_SILENCE_S)
    (_ok if va else _dub)(why)
    if va is not True:
        return _predicate(v, "P1 · ⛔⛔ no false positive", _mute(why))
    p = profile("bad-home")
    with broken_network(B76._rules(p[1]), a.seconds + 400) as reread:
        v["rule"] = reread
        s, (pg, why_g) = probe("bad-home")
        v["probe"], v["fault"] = s, {"passes": pg, "why": why_g}
        usc = B76.scene_turn_on("bar")
        if not usc:
            _ko("the scene does not start: I do NOT judge this run")
            return _predicate(v, "P1 · ⛔⛔ no false positive",
                            _mute("the scene did not start: without a moving "
                                  "scene there is no user at work "
                                  "not to throw out"))
        _inf("«barra» scene on monitor %s" % usc)
        line0 = line0_clean()
        B76.renew(CHI, LEASE)
        _inf("⏳ %g minutes of session — starting now" % (a.seconds / 60.0))
        n = B70.cur_round("p1-casa-cattiva", "bar", B70.FULL_CANVAS, a.seconds)
        n["witnesses"] = B76.connection_witnesses(line0, n)
        lm = read_dead_line(line0)
        fin = read_windows(line0)
        B76.scene_turn_off()
    B70.print_round(n)
    B76.print_delivery(n)
    B76.print_witnesses(n["witnesses"])
    print_shots(lm)
    print_windows(fin)
    fps, da_dove = round_fps(n)
    _inf("RATE    %s frames/s (%s)" % (fps, da_dove))
    n2 = dict(n)
    n2["fps"] = fps
    v["round"] = {k: n.get(k) for k in ("fps", "outcome", "from_client",
                                       "secondi_veri", "delivery", "server",
                                       "witnesses")}
    v["fps"], v["fps_da"] = fps, da_dove
    v["notches"], v["declared"] = lm, fin
    save("p1", v)
    _predicate(v, "P1 · ⛔⛔ NO FALSE POSITIVE in %g minutes" % (a.seconds / 60.0),
             p1_no_false_positive(lm, n["witnesses"], n2, a.seconds / 60.0))
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
    v = _entries("1-controllo · the same line with the cures OFF",
              profile="bad-home", seconds=a.seconds)
    status = fixes_state()
    v["stato_cure"] = status
    va, why = fixes_as_wanted(status, dead_line="spenta", eviction_ms=0)
    (_ok if va else _dub)(why)
    if va is not True:
        return _predicate(v, "P1c · the control", _mute(why))
    enabled = load("p1") or {}
    shots_on = ((enabled.get("notches") or {}).get("notches"))
    p = profile("bad-home")
    with broken_network(B76._rules(p[1]), a.seconds + 400) as reread:
        v["rule"] = reread
        s, (pg, why_g) = probe("bad-home")
        v["probe"], v["fault"] = s, {"passes": pg, "why": why_g}
        usc = B76.scene_turn_on("bar")
        if not usc:
            return _predicate(v, "P1c · the control",
                            _mute("the scene did not start"))
        _inf("«barra» scene on monitor %s" % usc)
        line0 = line0_clean()
        B76.renew(CHI, LEASE)
        _inf("⏳ %g minutes of session with the cures OFF — starting now"
             % (a.seconds / 60.0))
        n = B70.cur_round("p1c-casa-cattiva", "bar", B70.FULL_CANVAS, a.seconds)
        n["witnesses"] = B76.connection_witnesses(line0, n)
        lm = read_dead_line(line0)
        fin = read_windows(line0)
        B76.scene_turn_off()
    B70.print_round(n)
    B76.print_delivery(n)
    B76.print_witnesses(n["witnesses"])
    print_shots(lm)
    print_windows(fin)
    fps, da_dove = round_fps(n)
    _inf("RATE    %s frames/s (%s)" % (fps, da_dove))
    n2 = dict(n)
    n2["fps"] = fps
    v["round"] = {k: n.get(k) for k in ("fps", "outcome", "from_client",
                                       "secondi_veri", "delivery")}
    v["fps"], v["notches"], v["declared"] = fps, lm, fin
    save("p1-controllo", v)
    _predicate(v, "P1c · ⛔⛔ with the cures OFF the same line HOLDS %g minutes"
             % (a.seconds / 60.0),
             p1c_line_holds_with_fix_off(n["witnesses"], n2,
                                              a.seconds / 60.0, shots_on))
    # ⛔ AND HERE the threshold is judged, not in the run with the cure on: it is the only run that
    #    has enough windows for «it never broke through» to be a measurement.
    return v


def stall_ladder(a, name, seconds, thresholds=None):
    """⭐⭐ THE SCALE THAT TRACKS DOWN THE MAXIMUM STALL — ⇒ the box of `p1b`.

    ⛔ The `dead-line` line comes out ONLY on firing: «it did not fire» does not say
       **by how much**.  ⇒ The same profile is rerun with lower and lower
       thresholds until one fires, and then the product PRINTS its `stall_ms`.

    ⭐ And one goes down, not up: the first step that fires is the one that gives the
       BIGGEST measurable stall, and there is no need to go below.  ⚠ Every step
       costs a server restart, so the scale is short on purpose.

    ⚠ AND THE WINDOW IS SHORTER THAN THAT OF TEST 1, and it must be said: here one
      measures the maximum stall within %g s, not within ten minutes.  The maximum
      over ten minutes cannot be SMALLER than this, so the margin
      that comes out is an UPPER BOUND — and the only number that really closes
      test 1 remains the zero firings over the ten minutes.
    """ % seconds
    thresholds = thresholds or STALL_LADDER_MS
    rungs = []
    p = profile(name)
    for threshold in thresholds:
        if not turn_on_server("--linea-morta --dead-line-stall-ms %d" % threshold,
                              "stall scale on «%s» — threshold %d ms"
                              % (name, threshold)):
            rungs.append({"soglia_ms": threshold, "scattata": None,
                            "why": "the server did not restart"})
            break
        status = fixes_state()
        va, why = fixes_as_wanted(status, dead_line="enabled",
                                      stall_ms=threshold)
        if va is not True:
            _dub(why)
            rungs.append({"soglia_ms": threshold, "scattata": None,
                            "why": why})
            continue
        with broken_network(B76._rules(p[1]), seconds + 400):
            s_probe, (pg, why_g) = probe(name)
            usc = B76.scene_turn_on("bar")
            if not usc:
                rungs.append({"soglia_ms": threshold, "scattata": None,
                                "why": "the scene did not start"})
                continue
            line0 = line0_clean()
            n = B70.cur_round("scala-%s-%d" % (name, threshold), "bar",
                         B70.FULL_CANVAS, seconds)
            n["witnesses"] = B76.connection_witnesses(line0, n)
            lm = read_dead_line(line0)
            B76.scene_turn_off()
        fps, da_dove = round_fps(n)
        c = (n.get("delivery") or {})
        print_shots(lm)
        # ⛔⛔ AND A STEP IN WHICH THE FAULT WAS NOT PUT IN PLACE IS NOT A
        #     TEST — `[M]` 24 August 2026, found while running: on `burst-1` one
        #     step had 0.28 % loss instead of 1 %, and without
        #     this line it would have ended up in the scale as *«at 2000 ms it does not
        #     fire»* — that is, a margin proved on a profile MILDER than
        #     the one I believe.  ⚠ It is the same form as `p_fault_set`: a
        #     true number with a made-up cause.
        #     ⇒ `scattata=None` — «I do not know» — and `p1b` skips it.
        g = {"soglia_ms": threshold,
             "scattata": (lm["notches"] > 0) if pg is True else None,
             "stall_ms": lm.get("stall_ms"), "cause": lm.get("cause"),
             "offered": lm.get("offered"), "bytes_out": lm.get("bytes_out"),
             "video_queue": lm.get("video_queue"), "permille": lm.get("permille"),
             "fps": fps, "buco_max_s": c.get("buco_max_s"),
             "coverage": c.get("coverage"),
             "sonda_persi_pc": (s_probe or {}).get("persi_pc"),
             "fault": why_g}
        rungs.append(g)
        _inf("STEP threshold %d ms → %s · stall_ms=%s · %s frames/s · client "
             "gap %s s"
             % (threshold,
                "FIRED" if g["scattata"] else
                ("nothing" if g["scattata"] is False else
                 "⛔ DOES NOT COUNT (the fault was not put in place)"),
                g["stall_ms"], fps, g["buco_max_s"]))
        if g["scattata"]:
            # ⭐ Found the step that fires: its `stall_ms` is the biggest
            #   measurable number, and going further down would give only smaller
            #   numbers.
            break
    return rungs


def test_margin(a, name, thresholds=None, label=None):
    """⭐⭐ THE TRUE MARGIN — and without it the green does not say how close it
       came.  ⇒ The box above `p1b_stall_margin`."""
    _log("THE MARGIN — the scale that tracks down the stall of «%s»" % name)
    v = _entries("%s · the maximum stall of %s" % (label or "margin", name),
              profile=name, window_s=a.scale_s)
    v["scale_factor"] = stall_ladder(a, name, a.scale_s, thresholds)
    save("margine-%s" % name, v)
    _predicate(v, "P1b · ⭐⭐ the MARGIN of the stall threshold on «%s»" % name,
             p1b_stall_margin(v["scale_factor"], LM_STALL_MS, name))
    return v


def prova1_margine(a):
    return test_margin(a, "bad-home", label="1-margine")


def test_burst1(a):
    """⭐ THE CASE THAT KEEPS THE THRESHOLD HONEST — and before, it was not there.

    `burst-1` is the exact twin of `loss-1`: same average loss, but in
    CLUSTERS.  `[M]` it delivers **23.94 frames/s** — that is, it is a
    perfectly usable session — and still had **a whole empty second**.
    ⇒ It is the number the narrow side of the stall threshold rests on, and
      if the cure fired here the threshold would be written on nothing.
    """
    _log("TEST 3-nuova · ⭐ `burst-1` — 24 frames/s with an empty second")
    print("   ⛔ It must NOT fire.  It is the case that keeps the threshold honest: a")
    print("      perfectly usable line that still has a second at zero.")
    v = _entries("3-nuova · burst-1, the case that keeps the threshold honest",
              profile="burst-1", seconds=a.short)
    status = fixes_state()
    v["stato_cure"] = status
    va, why = fixes_as_wanted(status, dead_line="enabled",
                                  stall_ms=LM_STALL_MS)
    (_ok if va else _dub)(why)
    if va is not True:
        return _predicate(v, "P-raffica1", _mute(why))
    p = profile("burst-1")
    with broken_network(B76._rules(p[1]), a.short + 400) as reread:
        v["rule"] = reread
        s_probe, (pg, why_g) = probe("burst-1")
        v["probe"], v["fault"] = s_probe, {"passes": pg, "why": why_g}
        usc = B76.scene_turn_on("bar")
        _inf("«barra» scene on monitor %s" % usc)
        line0 = line0_clean()
        n = B70.cur_round("p3n-raffica-1", "bar", B70.FULL_CANVAS, a.short)
        n["witnesses"] = B76.connection_witnesses(line0, n)
        lm = read_dead_line(line0)
        fin = read_windows(line0)
        B76.scene_turn_off()
    B70.print_round(n)
    B76.print_delivery(n)
    B76.print_witnesses(n["witnesses"])
    print_shots(lm)
    print_windows(fin)
    fps, da_dove = round_fps(n)
    _inf("RATE    %s frames/s (%s)" % (fps, da_dove))
    n2 = dict(n)
    n2["fps"] = fps
    v["fps"], v["notches"], v["declared"] = fps, lm, fin
    v["round"] = {k: n.get(k) for k in ("fps", "outcome", "from_client",
                                       "secondi_veri", "delivery")}
    save("p3n-raffica1", v)
    _predicate(v, "P-raffica1 · ⭐ «burst-1» HOLDS and must not be declared dead",
             p_must_not_fire("burst-1", lm, n["witnesses"], n2,
                                 a.short / 60.0, GRID_B76["burst-1"]))
    # ⭐ And the margin here too: it is the NARROW side of the threshold, so it is the
    #   place where a thin margin would hurt most.
    v["scale_factor"] = stall_ladder(a, "burst-1", a.short)
    save("p3n-raffica1", v)
    _predicate(v, "P1b · ⭐⭐ the MARGIN of the threshold on «burst-1» (narrow side)",
             p1b_stall_margin(v["scale_factor"], LM_STALL_MS, "burst-1"))
    return v


def test_still_scene(a, soglia_ms):
    """⛔⛔ THE STILL SCENE WITH THE CURE ON — the worst way in which this
       cure could fail.  ⇒ The box above `p_still_scene_no_fire`.

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
    v = _entries("4-nuova · the still scene (threshold %d ms)" % soglia_ms,
              stall_threshold_ms=soglia_ms, seconds=a.scene_s)
    status = fixes_state()
    v["stato_cure"] = status
    va, why = fixes_as_wanted(status, dead_line="enabled",
                                  stall_ms=soglia_ms)
    (_ok if va else _dub)(why)
    if va is not True:
        return _predicate(v, "P-scena-ferma", _mute(why))
    # ⛔ The scene is SWITCHED OFF, and we check it is off: a scene left
    #    on would make this test pass for the wrong reason.
    B76.scene_turn_off()
    rc, out, _ = root("bash -c \"pgrep -u %d -f '04-b30-scena --uscita' | wc -l\""
                      % UID_B)
    v["scene_vive"] = out.strip()
    if out.strip() not in ("0", ""):
        return _predicate(v, "P-scena-ferma",
                        _mute("⚠ there is still a live scene (%s): this run "
                              "is not «still scene»" % out.strip()))
    _ok("no live scene: the desktop does not change")
    line0 = line0_clean()
    _inf("⏳ %g s of session with a STILL SCENE" % a.scene_s)
    # ⛔ Without a trace: here there is nothing to reduce — the point is precisely that
    #    no frames arrive — and a reader that refuses would give the
    #    test the look of a fault.
    n = B70.cur_round("p4n-scena-ferma-%d" % soglia_ms, "halt", B70.FULL_CANVAS,
                 a.scene_s, with_trace=False)
    n["witnesses"] = B76.connection_witnesses(line0, n)
    lm = read_dead_line(line0)
    B76.print_witnesses(n["witnesses"])
    print_shots(lm)
    _inf("CLIENT %s · %s real s"
         % (json.dumps(n.get("from_client"), ensure_ascii=False),
            n.get("secondi_veri")))
    v["notches"] = lm
    v["round"] = {k: n.get(k) for k in ("from_client", "secondi_veri",
                                       "witnesses")}
    save("p4n-scena-ferma-%d" % soglia_ms, v)
    _predicate(v, "P-scena-ferma · ⛔⛔ %g s of STILL desktop, threshold %d ms"
             % (a.scene_s, soglia_ms),
             p_still_scene_no_fire(lm, n["witnesses"], a.scene_s, soglia_ms))
    return v


def prova1_taratura(a):
    """⭐ THE CALIBRATION — and it closes the hole of the reconstruction (⇒ the box at
       the top).  Same `bad-home`, but with `--linea-morta-permille 1`: at
       that threshold the cure fires for sure, and firing **prints the
       `permille=` that it computed itself**, on its own window, with its own
       arithmetic.  ⇒ It is the only way to read the DECLARED fraction without
       redoing it by hand.

    ⛔ It does not judge: it MEASURES and reports.  The judgement on the threshold belongs to `P1b`.
    """
    _log("TEST 1 · THE CALIBRATION — how much the DECLARED fraction is worth, told by the "
         "PRODUCT")
    v = _entries("1-taratura · the declared fraction, read from the product",
              profile="bad-home")
    status = fixes_state()
    v["stato_cure"] = status
    va, why = fixes_as_wanted(status, dead_line="enabled", stall_ms=1)
    (_ok if va else _dub)(why)
    if va is not True:
        return _predicate(v, "calibration", _mute(why))
    p = profile("bad-home")
    with broken_network(B76._rules(p[1]), 240) as reread:
        v["rule"] = reread
        s, _g = probe("bad-home")
        v["probe"] = s
        usc = B76.scene_turn_on("bar")
        _inf("«barra» scene on monitor %s" % usc)
        line0 = line0_clean()
        n = B70.cur_round("p1-taratura", "bar", B70.FULL_CANVAS, a.calibration_s)
        lm = read_dead_line(line0)
        fin = read_windows(line0, threshold_permille=1)
        B76.scene_turn_off()
    print_shots(lm)
    print_windows(fin)
    v["notches"], v["declared"] = lm, fin
    if lm.get("outcome") == "read" and lm["notches"]:
        _ok("⭐ THE PRODUCT HAS ITS SAY: on the window in which it decided, the "
            "DECLARED fraction was **%s‰** (%s lost out of %s sent in %s "
            "ms) — and my reconstruction from the `quic-net` lines gave max %s‰, "
            "median %s‰"
            % (lm.get("permille"), lm.get("lost"), lm.get("sent"),
               lm.get("window_ms"), fin.get("permille_max"),
               fin.get("permille_mediano")))
        v["permille_dal_prodotto"] = lm.get("permille")
    else:
        _dub("⚠ at 1‰ the cure did not fire: the calibration did not produce the "
             "product's number, and only the reconstruction remains")
    save("p1-taratura", v)
    return v


# ═══════════════════════════════════════════════════════════════════════════
# TEST 2 · THE REAL FIRING
# ═══════════════════════════════════════════════════════════════════════════
def prova2(a):
    _log("TEST 2 · THE REAL FIRING — `burst-heavy`, and it MUST fire")
    print("   `[M]` 11.10 % loss in bursts: with the cure off the screen stays")
    print("   frozen 14.26 s out of 25 (grid of 09-b76).  ⇒ The cure must fire,")
    print("   with cause=stall, and the wire must drop.")
    v = _entries("2 · the real firing", profile="burst-heavy", seconds=a.short)
    status = fixes_state()
    v["stato_cure"] = status
    va, why = fixes_as_wanted(status, dead_line="enabled",
                                  stall_ms=LM_STALL_MS)
    (_ok if va else _dub)(why)
    if va is not True:
        return _predicate(v, "P2 · the real firing", _mute(why))
    p = profile("burst-heavy")
    with broken_network(B76._rules(p[1]), a.short + 400) as reread:
        v["rule"] = reread
        s, (pg, why_g) = probe("burst-heavy")
        v["probe"], v["fault"] = s, {"passes": pg, "why": why_g}
        usc = B76.scene_turn_on("bar")
        _inf("«barra» scene on monitor %s" % usc)
        line0 = line0_clean()
        n = B70.cur_round("p2-raffica-forte", "bar", B70.FULL_CANVAS, a.short)
        n["witnesses"] = B76.connection_witnesses(line0, n)
        lm = read_dead_line(line0)
        fin = read_windows(line0)
        sf = read_eviction(line0)
        B76.scene_turn_off()
    B70.print_round(n)
    B76.print_delivery(n)
    print_shots(lm)
    print_windows(fin)
    # ⭐ From when the slot was taken to when the cure decided: it is
    #   the SERVER's clock, and the two instants are in the same log.
    seconds = None
    if lm.get("outcome") == "read" and lm["notches"] and sf.get("righe_preso"):
        seconds = dt_log(lm["lines"][0]["line"], sf["righe_preso"][0])
    v["seconds_to_fire"] = seconds
    _inf("WHEN    fired %s s after the slot had been taken"
         % (("%.2f" % seconds) if seconds is not None else "?"))
    v["notches"], v["declared"] = lm, fin
    v["round"] = {k: n.get(k) for k in ("fps", "outcome", "from_client",
                                       "secondi_veri", "delivery")}
    save("p2", v)
    _predicate(v, "P2 · the cure FIRES on the burst, with cause=stall",
             p2_fires_on_stall(lm, s, seconds))
    return v


# ═══════════════════════════════════════════════════════════════════════════
# TEST 3 · SILENCE, AND THE PRICE OF THE PINGs
# ═══════════════════════════════════════════════════════════════════════════
def prova3(a, on):
    come = "ON" if on else "OFF"
    _log("TEST 3 · SILENCE — client killed with `kill -9`, cure %s" % come)
    print("   ⛔ `-9` and not a farewell: the goodbye does NOT leave, and for the server it is")
    print("      identical to a LOST goodbye — that is, it is the real case.")
    v = _entries("3 · silence (cure %s)" % come, on=on)
    status = fixes_state()
    v["stato_cure"] = status
    va, why = fixes_as_wanted(
        status, dead_line=("enabled" if on else "spenta"),
        silence_s=(LM_SILENCE_S if on else None))
    (_ok if va else _dub)(why)
    if va is not True:
        return _predicate(v, "P3 · silence", _mute(why))
    clean_up_clients()
    # ⛔ The `netem` is there even without a fault: it is what carries the byte
    #    COUNTER, and without a counter «the real traffic of a still session» cannot be
    #    measured.  ⚠ `limit 20000` and nothing else — and the `smooth` profile of 09-b76
    #    checks that that queue drops nothing of its own.
    with broken_network(B76._rules([]), 400) as reread:
        v["rule"] = reread
        # ⭐ Scene OFF: «with a still session» means the desktop does not
        #   move, or what I measure is the video.
        B76.scene_turn_off()
        line0 = line0_clean()
        background_client(ACCOUNT, INSIDE_WORK + "/parola", 400,
                              "p3-%s" % ("on" if on else "off"))
        taken = wait_line(line0, ["slot TAKEN by %s " % ACCOUNT], 120)
        if not taken:
            clean_up_clients()
            return _predicate(v, "P3 · silence",
                            _mute("the session did not open in 120 s: I have "
                                  "nothing to kill"))
        _ok("session open: %s" % taken[-1][:120])
        _inf("⏳ %g s of wire clock with a STILL session" % a.clock_s)
        gold = clock_runs(a.clock_s)
        print_clock(gold, come)
        v["clock"] = gold
        save("p3-orologio-%s" % ("on" if on else "off"), gold)
        pid = client_pid(ACCOUNT)
        _inf("the client is pid %s on the host (⛔ `enter.sh` is a chroot)" % pid)
        t_kill = kill(pid)
        _inf("KILLED  with -9 at %s (SERVER clock)" % (t_kill or "?"))
        v["t_kill"] = t_kill
        lines = wait_line(line0, ["dead-line "],
                             cap=(a.wait_shot if on else 25.0))
        lm = read_dead_line(line0)
        # ⭐ AND RIGHT AFTER: is the slot free again?  It is the other half of the
        #   ghost, and the answer of the DEAD LINE (not of the eviction).
        slot = None
        if on:
            lines_p, queue = B78.measure(rounds=1, until="session", cap=20,
                                       retry=a.retry_s)
            v["apertura_dopo_scatto"] = lines_p
            if lines_p:
                r = lines_p[0]
                slot = (r.get("attesa_posto_ms") if r.get("attesa_posto_ms")
                         is not None else 0)
                _inf("SLOT    after the firing: outcome «%s», wait for the slot %s ms"
                     % (r.get("outcome"), r.get("attesa_posto_ms")))
        sf = read_eviction(line0)
        clean_up_clients()
    print_shots(lm)
    print_eviction(sf)
    if lm.get("outcome") == "read" and lm["notches"] and t_kill:
        v["secondi_dal_kill"] = dt_log(lm["lines"][0]["line"], t_kill)
        _inf("WHEN    fired %.2f s after the `kill -9` (server clock) · "
             "the line says silence_ms=%s"
             % (v["secondi_dal_kill"] or -1, lm.get("silence_ms")))
    v["notches"], v["eviction"] = lm, sf
    save("p3-%s" % ("on" if on else "off"), v)
    if on:
        _predicate(v, "P3 · the cure fires on SILENCE at its threshold",
                 p3_fires_on_silence(lm, LM_SILENCE_S * 1000))
    else:
        # ⛔ With the cure off the firing must NOT be there: it is half of I6, and it is
        #    judged with the predicate of I6, not with this one.
        _predicate(v, "P3/I6 · with the cure OFF silence closes nothing",
                 p6_defaults_change_nothing(lm, sf, status, None,
                                                      "(no profile)"))
    acc = load("p3-orologio-acceso")
    off_run = load("p3-orologio-spento")
    if acc and off_run:
        _predicate(v, "P3b · ⚠ the DECLARED price of the PINGs (%.2f kbit/s)"
                 % COST_PING_DECLARED_KBIT_S, p3b_ping_cost(acc, off_run))
    else:
        _dub("P3b · the price of the PINGs: I have only one of the two measurements "
             "(on=%s, off=%s) — it is judged when both are there"
             % (bool(acc), bool(off_run)))
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
#     ⇒ Tests 4 and 5 run with `--eviction-ms 15000` and the DEAD LINE OFF.
def _ghost(a, who_asks, password_inside_dir, wait_before=0.0):
    """The common piece: a client of `%s` takes the slot, dies of `-9`, and then
       someone asks for that slot.  It returns the numbers, not the judgements.""" % ACCOUNT
    clean_up_clients()
    line0 = line0_clean()
    background_client(ACCOUNT, INSIDE_WORK + "/parola", 400, "p4-vittima")
    taken = wait_line(line0, ["slot TAKEN by %s " % ACCOUNT], 120)
    if not taken:
        clean_up_clients()
        return {"outcome": "⛔ the victim's session did not open in 120 s"}
    _ok("the slot belongs to %s: %s" % (ACCOUNT, taken[-1][:120]))
    pid = client_pid(ACCOUNT)
    t_kill = kill(pid)
    _inf("KILLED  pid %s with -9 at %s (SERVER clock)" % (pid, t_kill))
    if wait_before:
        _inf("⏳ I wait %g s before knocking: so the occupant is already past "
             "the eviction threshold, and if the eviction could fire "
             "it would fire" % wait_before)
        time.sleep(wait_before)
    # ⛔ `09-b78-apertura.py --retry-0f`: it TIMES the denied slot instead of
    #    counting it — `ALREADY_ACTIVE_REMOTELY` is a state that PASSES, and a yes/no would
    #    make it look like a permanent fault.
    usr, dl = B78.ACCOUNT, B78.INSIDE_WORK
    try:
        B78.ACCOUNT, B78.INSIDE_WORK = who_asks, password_inside_dir
        lines, queue = B78.measure(rounds=1, until="session", cap=20,
                                 retry=a.retry_s)
    finally:
        B78.ACCOUNT, B78.INSIDE_WORK = usr, dl
    sf = read_eviction(line0)
    n = {"outcome": "measured", "t_kill": t_kill, "aperture": lines,
         "queue": queue[-400:], "eviction": sf, "who_asks": who_asks}
    r = lines[0] if lines else {}
    n["esito_apertura"] = r.get("outcome")
    n["attesa_posto_ms"] = r.get("attesa_posto_ms")
    n["entered"] = bool(r.get("outcome", "").startswith("is_open"))
    # ⭐ «At which second it gets in», on the SERVER's clock: the last `slot TAKEN`
    #   after `line0` is that of whoever knocked.
    if sf.get("grabbed", 0) >= 2 and t_kill:
        n["seconds_to_enter"] = dt_log(sf["righe_preso"][-1], t_kill)
    clean_up_clients()
    return n


def prova4(a, eviction_ms):
    come = ("--eviction-ms %d" % eviction_ms) if eviction_ms else "eviction OFF"
    _log("TEST 4 · THE GHOST EVICTION — %s" % come)
    print("   `[M]` today it takes 30.5 s and 11 refusals: the wire drops, the user")
    print("   retries, and for half a minute is told «you already have an active session")
    print("   elsewhere» — which for them is FALSE: that session is theirs.")
    v = _entries("4 · the eviction (%s)" % come, eviction_ms=eviction_ms)
    status = fixes_state()
    v["stato_cure"] = status
    # ⛔ The dead line must be OFF: see the box above `_fantasma`.
    va, why = fixes_as_wanted(status, dead_line="spenta",
                                  eviction_ms=eviction_ms)
    (_ok if va else _dub)(why)
    if va is not True:
        return _predicate(v, "P4 · the eviction", _mute(why))
    n = _ghost(a, ACCOUNT, INSIDE_WORK)
    v["fantasma"] = n
    if n.get("outcome") != "measured":
        return _predicate(v, "P4 · the eviction", _mute(n.get("outcome")))
    print_eviction(n["eviction"])
    _inf("SCALE   %d refusals («slot DENIED») · outcome «%s» · the slot became "
         "free again after %s s (server clock) · the client waited %s ms"
         % (n["eviction"]["refusals"], n.get("esito_apertura"),
            ("%.2f" % n["seconds_to_enter"]) if n.get("seconds_to_enter")
            is not None else "?", n.get("attesa_posto_ms")))
    save("p4-%d" % eviction_ms, v)
    if not eviction_ms:
        # ⛔ It is the REFERENCE, not a test: here there is no cure to
        #    judge, there is the number against which the gain is measured.
        _inf("⭐ this is the REFERENCE (cure off): %s s and %d refusals"
             % (("%.2f" % n["seconds_to_enter"]) if n.get("seconds_to_enter")
                is not None else "?", n["eviction"]["refusals"]))
        # ⚠ Here the dead line is off by construction (`fixes_as_wanted`
        #   already demanded it), and in this run there is no `netem`: there is
        #   nothing that could have made it fire.  ⇒ An EMPTY and READ
        #   reduction is passed, and only the eviction is left to judge.
        _predicate(v, "P4/I6 · with the eviction OFF there is no eviction",
                 p6_defaults_change_nothing(
                     {"outcome": "read", "notches": 0, "lines": [],
                      "chiuse_dal_trasporto": 0},
                     n["eviction"], status, None, "(no profile)"))
        return v
    ref = load("p4-0")
    ref_s = ((ref or {}).get("fantasma") or {}).get("seconds_to_enter")
    _predicate(v, "P4 · the EVICTION frees the slot at the threshold",
             p4_eviction_frees_slot(n["eviction"], eviction_ms,
                                           n.get("seconds_to_enter"), ref_s))
    return v


def prova5(a):
    _log("TEST 5 · ⛔ THE CASE THAT MUST NOT BREAK — two different users")
    print("   An eviction between different users would not be a convenience: it would be")
    print("   a security hole — anyone could make another person's desktop")
    print("   drop simply by knocking.")
    v = _entries("5 · two different users", utente_a=ACCOUNT, utente_b=ACCOUNT2)
    status = fixes_state()
    v["stato_cure"] = status
    va, why = fixes_as_wanted(status, dead_line="spenta",
                                  eviction_ms=RECOMMENDED_EVICTION_MS)
    (_ok if va else _dub)(why)
    if va is not True:
        return _predicate(v, "P5 · two different users", _mute(why))
    # ⛔ The SECOND user's password sits in a separate file, and it is put where
    #    `09-b78` looks for it (`<INSIDE_WORK>/password`) without touching a line of it: so
    #    the second user's opening goes through the SAME tool as test 4.
    root("bash -c \"mkdir -p %s/u2 && cp %s/parola2 %s/u2/parola && "
         "chmod 600 %s/u2/parola\"" % (WORKDIR, WORKDIR, WORKDIR, WORKDIR))
    rc, out, _ = root("bash -c \"test -s %s/u2/parola && echo si || echo no\"" % WORKDIR)
    if "yes" not in out:
        return _predicate(v, "P5 · two different users",
                        _mute("the second user's password is not in %s/u2/parola: "
                              "without it, I would open two sessions of the SAME user "
                              "believing I had opened two of different users" % WORKDIR))
    # ⭐ We wait BEYOND the eviction threshold before knocking: if the eviction
    #   could fire between different users, at that point it would fire.
    n = _ghost(a, ACCOUNT2, INSIDE_WORK + "/u2",
                  wait_before=RECOMMENDED_EVICTION_MS / 1000.0 + 3.0)
    v["fantasma"] = n
    if n.get("outcome") != "measured":
        return _predicate(v, "P5 · two different users", _mute(n.get("outcome")))
    print_eviction(n["eviction"])
    _inf("OUTCOME «%s» for «%s» · %d refusals · %d slots taken"
         % (n.get("esito_apertura"), ACCOUNT2, n["eviction"]["refusals"],
            n["eviction"]["grabbed"]))
    save("p5", v)
    _predicate(v, "P5 · ⛔ between different users there is NO eviction",
             p5_no_eviction_across_users(n["eviction"], n.get("entered"),
                                                  ACCOUNT, ACCOUNT2))
    _predicate(v, "P5b · ⚠ and the «EVICTION DENIED» line? (prediction `[R]`: it does not come out)",
             p5b_denied_line(n["eviction"]))
    return v


# ═══════════════════════════════════════════════════════════════════════════
# TEST 6 · ⛔ THE DEFAULTS CHANGE NOTHING (I6)
# ═══════════════════════════════════════════════════════════════════════════
def prova6(a, name):
    _log("TEST 6 · ⛔ THE DEFAULTS — «%s» with the product AS IT SHIPS TODAY" % name)
    print("   Without `--linea-morta` and with `--eviction-ms 0`: no firing,")
    print("   no eviction, and the profile behaves as in the grid of")
    print("   09-b76.  ⛔ It is invariant I6, and it is also the proof that the two")
    print("   cures are really OFF, not only written.")
    v = _entries("6 · the defaults (%s)" % name, profile=name, seconds=a.short)
    status = fixes_state()
    v["stato_cure"] = status
    va, why = fixes_as_wanted(status, dead_line="spenta", eviction_ms=0)
    (_ok if va else _dub)(why)
    if va is not True:
        return _predicate(v, "P6 · I6 on «%s»" % name, _mute(why))
    p = profile(name)
    with broken_network(B76._rules(p[1]), a.short + 400) as reread:
        v["rule"] = reread
        s, (pg, why_g) = probe(name)
        v["probe"], v["fault"] = s, {"passes": pg, "why": why_g}
        usc = B76.scene_turn_on("bar")
        _inf("«barra» scene on monitor %s" % usc)
        line0 = line0_clean()
        n = B70.cur_round("p6-%s" % name, "bar", B70.FULL_CANVAS, a.short)
        n["witnesses"] = B76.connection_witnesses(line0, n)
        lm = read_dead_line(line0)
        sf = read_eviction(line0)
        fin = read_windows(line0)
        B76.scene_turn_off()
    B70.print_round(n)
    B76.print_delivery(n)
    B76.print_witnesses(n["witnesses"])
    print_shots(lm)
    print_eviction(sf)
    print_windows(fin)
    fps, da_dove = round_fps(n)
    _inf("RATE    %s frames/s (%s)" % (fps, da_dove))
    n2 = dict(n)
    n2["fps"] = fps
    v["round"] = {k: n.get(k) for k in ("fps", "outcome", "from_client",
                                       "secondi_veri", "delivery")}
    v["fps"], v["notches"], v["eviction"], v["declared"] = fps, lm, sf, fin
    save("p6-%s" % name, v)
    _predicate(v, "P6 · ⛔ I6: with the defaults «%s» is identical to before" % name,
             p6_defaults_change_nothing(lm, sf, status, n2, name))
    return v


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE FOUR SERVER CONFIGURATIONS — and why there are four
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ It is not a convenience: **the two cures overlap**, and turning them on together
#    would make one measure the first calling it the second (⇒ the box above
#    `_fantasma`).  ⇒ Every test runs on the configuration that ISOLATES the cure it
#    measures, and `fixes_as_wanted()` refuses if the server is not on it.
CONFIGURATIONS = {
    "A": ("--linea-morta",
          "the DEAD LINE on with the defaults (stall 5 000 ms, silence 10 s) "
          "and the eviction OFF — tests 1, 2, 3, burst-1 and still scene"),
    "C": ("--eviction-ms %d" % RECOMMENDED_EVICTION_MS,
          "the EVICTION on and the dead line OFF — tests 4 and 5, and the dead "
          "line must be off or the ghost would vanish at 10 s because of the other "
          "cure and the eviction would never fire"),
    "D": ("--eviction-ms 0",
          "⛔ THE DEFAULTS, that is the product as it ships today — test 6, "
          "the reference of test 4 and the off half of test 3"),
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("step", nargs="?",
                   choices=["terrain", "p1", "p1m", "p1c", "p1t", "p2", "p3",
                            "pr1", "psf", "phealthy", "p4", "p5", "p6",
                            "all", "restore", "status"])
    p.add_argument("--certify", action="store_true",
                   help="⭐ the positive control: proves that the bench can see "
                        "the defects it looks for. It does not touch the test machine")
    p.add_argument("--seconds", type=int, default=600,
                   help="the window of test 1 — ⛔ ten minutes, and it is the "
                        "number the user asked for")
    p.add_argument("--short", type=int, default=60,
                   help="the window of the short runs (tests 2 and 6)")
    p.add_argument("--calibration-s", type=int, default=40)
    p.add_argument("--scale-s", type=int, default=120,
                   help="the window of the steps of the stall scale — ⚠ "
                        "shorter than that of test 1, and the ratio must be "
                        "stated")
    p.add_argument("--scene-s", type=float, default=90.0,
                   help="how long the STILL SCENE session lasts")
    p.add_argument("--scene-tight-threshold-ms", type=int, default=1000,
                   help="⭐ the stall threshold with which the still scene is "
                        "retried: if the count does not start at 1 s, it never starts")
    p.add_argument("--clock-s", type=float, default=60.0,
                   help="how long the measurement of traffic with a still session lasts")
    p.add_argument("--wait-shot", type=float, default=45.0,
                   help="how many seconds I wait for the `dead-line` line after the -9")
    p.add_argument("--retry-s", type=float, default=75.0,
                   help="how long the second client keeps knocking at the slot "
                        "(09-b78 `--retry-0f`)")
    p.add_argument("--wait", type=int, default=1800,
                   help="how many seconds I wait for the netem lock")
    p.add_argument("--skip-restart", action="store_true",
                   help="⚠ does not restart the server: use it ONLY when it is already "
                        "in the right configuration, and `fixes_as_wanted()` "
                        "checks it all the same")
    a = p.parse_args()

    if a.certify:
        return certify()
    if not a.step:
        p.error("a step is needed, or --certify")

    os.makedirs(OUT, exist_ok=True)
    do_import()

    if a.step in ("restore", "status"):
        _log("the test machine's network — dev «%s», port %d" % (DEV, PORT))
        ok = NETWORK.restore()
        _inf("ports NOT mine: %s" % near())
        _inf("the cures, as the server declares them: %s"
             % json.dumps(fixes_state(), ensure_ascii=False)[:400])
        return 0 if ok else 2

    _log("09-b81 · THE TWO CURES — port %d · user %s (uid %d) · dev «%s»"
         % (PORT, ACCOUNT, UID_B, DEV))
    print("   ⛔ «%s» (ssh + the user's session) is NOT touched" % VIETATA)
    print("   ⛔ ports 7900, 7910 and 7920 are counted and not touched")
    print("   --  «%s» before: %s" % (DEV, NETWORK.qdisc() or "(none)"))
    if not get_ready():
        return 2
    if not B70.terrain_check():
        return 2
    if a.step == "terrain":
        _ok("the ground is there, and it is mine")
        return 0

    def configure_stall(ms):
        """⛔ An off-catalogue configuration, and for one case only: the still
           scene with the narrow threshold.  ⚠ `fixes_as_wanted()` rechecks it
           inside the test, like all the others."""
        if a.skip_restart:
            _dub("⚠ I do NOT restart the server (--skip-restart)")
            return True
        return turn_on_server(
            "--linea-morta --dead-line-stall-ms %d" % ms,
            "the dead line with the stall threshold NARROWED to %d ms — the "
            "still scene holding the knife by the handle" % ms)

    def configure(key):
        if a.skip_restart:
            _dub("⚠ I do NOT restart the server (--skip-restart): I trust "
                 "`fixes_as_wanted()`, which will refuse if it is not %s" % key)
            return True
        opt, why = CONFIGURATIONS[key]
        return turn_on_server(opt, "configuration %s — %s" % (key, why))

    outcomes = []
    try:
        # ⛔⛔ THE ORDER IS NOT A CONVENIENCE: every test runs on the
        #     configuration that ISOLATES the cure it measures, and the tests that
        #     share the same configuration are kept together, or one
        #     would pay for a restart (and a priming session) for nothing.
        #     ⚠ And `fixes_as_wanted()` rechecks all the same, inside every test:
        #       the order is a saving, not a guarantee.
        tutte = (a.step == "tutte")
        # ── configuration A: the dead line on with the defaults ─────────────
        if a.step in ("p1", "p2", "p3", "pr1", "psf", "all"):
            if configure("A"):
                if a.step in ("p1", "all"):
                    outcomes.append(prova1(a))
                if a.step in ("p2", "all"):
                    outcomes.append(prova2(a))
                if a.step in ("pr1", "all"):
                    outcomes.append(test_burst1(a))
                if a.step in ("psf", "all"):
                    # ⛔ The still scene at the threshold IN FORCE…
                    outcomes.append(test_still_scene(a, LM_STALL_MS))
                if a.step in ("p3", "all"):
                    outcomes.append(prova3(a, on=True))
        # ── and the still scene holding the knife by the handle: the same
        #    test with a MUCH narrower threshold.  If the count does not start
        #    there, it does not start at any threshold.
        if a.step in ("psf", "all"):
            if configure_stall(a.scene_tight_threshold_ms):
                outcomes.append(test_still_scene(a, a.scene_tight_threshold_ms))
        # ── the MARGIN of test 1: the scale that tracks down the maximum stall ─
        if a.step in ("p1m", "all"):
            outcomes.append(prova1_margine(a))
        # ── ⭐ and the fourth number of the report: the stall of the HEALTHY profiles.
        #    ⛔ It is not deduced from `bad-home`: «a healthy line cannot do
        #    worse» is a reasoning, and the report asks for a measurement.
        if a.step in ("phealthy", "all"):
            outcomes.append(test_margin(a, HEALTHY_REFERENCE, [1000, 500],
                                       label="healthy_runs"))
        if a.step == "p1t":
            if configure("A"):
                outcomes.append(prova1_taratura(a))
        # ── configuration C: the eviction on, the dead line OFF ─────────────
        if a.step in ("p4", "p5", "all"):
            if configure("C"):
                if a.step in ("p4", "all"):
                    outcomes.append(prova4(a, RECOMMENDED_EVICTION_MS))
                if a.step in ("p5", "all"):
                    outcomes.append(prova5(a))
        # ── configuration D: ⛔ the defaults, the product as it ships today ──
        if a.step in ("p6", "p3", "p4", "p1c", "all"):
            if configure("D"):
                # ⛔ FIRST the control of test 1: it is the one that makes valid (or
                #    withdraws) the red of test 1, and it must be read together with it.
                if a.step in ("p1c", "all"):
                    outcomes.append(prova1_controllo(a))
                if a.step in ("p6", "all"):
                    for name in ("bad-home", "burst-heavy"):
                        outcomes.append(prova6(a, name))
                if a.step in ("p3", "all"):
                    outcomes.append(prova3(a, on=False))
                if a.step in ("p4", "all"):
                    outcomes.append(prova4(a, 0))
        # ⛔ And the gain is counted at the end: («how much did the
        #    ghost drop») needs both numbers, and when test 4 with the
        #    cure ran the reference was not there yet.
        if tutte:
            ref, cur = load("p4-0"), load("p4-%d" % RECOMMENDED_EVICTION_MS)
            if ref and cur:
                _log("THE GAIN — «how much did the ghost drop»")
                rs = (ref.get("fantasma") or {}).get("seconds_to_enter")
                cs = (cur.get("fantasma") or {}).get("seconds_to_enter")
                rr = ((ref.get("fantasma") or {}).get("eviction") or {}).get("refusals")
                cr = ((cur.get("fantasma") or {}).get("eviction") or {}).get("refusals")
                _inf("eviction OFF: %s s and %s refusals · eviction at %d ms: %s s "
                     "and %s refusals" % (rs, rr, RECOMMENDED_EVICTION_MS, cs, cr))
                outcomes.append({"prova": "the gain", "predicates": [],
                              "reference_s": rs, "con_cura_s": cs,
                              "rifiuti_riferimento": rr, "rifiuti_con_cura": cr})
    finally:
        clean_up_clients()
        B76.scene_turn_off()
        restored = NETWORK.restore()
        try:
            LUC.release(CHI, report_it=False)
        except Exception:
            pass

    save("outcomes", outcomes)
    _log("THE VERDICT")
    rossi, silent = [], []
    for v in outcomes:
        for d in v["predicates"]:
            if d["passes"] is False:
                rossi.append("%s · %s — %s" % (v["prova"], d["predicate"],
                                               d["why"][:120]))
            elif d["passes"] is None:
                silent.append("%s · %s — %s" % (v["prova"], d["predicate"],
                                              d["why"][:120]))
    _inf("%d tests run · %d red · %d not judged · outcomes in %s"
         % (len(outcomes), len(rossi), len(silent), _out("outcomes")))
    for r in rossi:
        _ko(r)
    for m in silent:
        _dub(m)
    if not restored:
        _ko("⛔ the network did NOT go back as it was: put it back by hand with «restore»")
        return 2
    if rossi:
        return 1
    if silent:
        return 3
    _ok("⭐ all the predicates did what was written beforehand")
    return 0


if __name__ == "__main__":
    sys.exit(main())
