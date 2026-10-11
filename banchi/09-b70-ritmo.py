#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b70-ritmo — THE RATE WHEN THE LINE NARROWS, and the first thing it asks
               is not «how well it degrades»: it is **whether it degrades when it must not**.

    port 7809 · user `provan9` (uid 1029) · tree `/media/REMOTIX/src/09-r-src`
    work `/media/REMOTIX/tmp/09-r` · unit `remotix-7809` · its own ban-file and socket

═══════════════════════════════════════════════════════════════════════════════
⛔ WHERE IT COMES FROM — and they are three facts, not an intention
═══════════════════════════════════════════════════════════════════════════════

 1. ⛔⛔ **In v1 the corresponding phase (phase 10) was WIPED OUT**, and not for a technical
    defect (`fondamenta/documenti/PIANO.md:1418`): it was validated with PSNR, SSIM and a
    frame looked at by eye by the developer, and the user's judgement
    on the real desktop was *«we have gone backwards»*.  ⇒ **This bench does not
    produce a verdict on the image and is not allowed to produce one.**
    It produces numbers on the RATE; the image is judged by the user.

 2. ⛔ **The second mistake of v1 was optimising in the wrong direction**:
    *«spending less bandwidth»* was counted as a gain, and for the product
    bandwidth is a **floor**, not a budget.  ⇒ ⭐ Here **no predicate
    rewards bandwidth saved**.  Green is earned by delivering frames.

 3. ⭐⭐ **The operating point changed on 23 August 2026** — `DECISIONI.md`
    §3.1-bis: *«I believe a minimum connection must be 20 mbps: below
    this limit the user cannot even browse»*.  ⇒ The old steps
    of `07-b65` — 3, 2, 1, 0.5 Mbit/s — **measured a promise the
    product no longer makes**, and here they do not come back as a requirement.

═══════════════════════════════════════════════════════════════════════════════
⭐ WHAT IT CAN SEE — five quantities, and ALL FIVE are written
═══════════════════════════════════════════════════════════════════════════════

`LEZIONI.md` §6.2: *«a table with a single column is not a short measurement:
it is a **slanted** measurement»*.  ⇒ Every run always carries, even when they
are not needed for the question of the moment:

  1. **frames delivered per second** — the steady-state mean **and** the minimum over a
     one-second window.  ⛔ The mean alone is the deception the positive
     control of this file reproduces on purpose (case 2);
  2. **how many KEYFRAMES and how many DELTAS** — because §3.3 mandates degrading **in
     time**, and a stream of keyframes only degrades in space *and* in time
     together, which is the defect measured on 21 August (144/144, 149/149);
  3. **the bytes per second on the wire** — read from the `qdisc` counter, not
     deduced — next to the **payload** bytes, because the difference between
     the two is padding, retransmissions, acknowledgements and audio;
  4. **the delay** — ⚠ and its exact nature is written further down: it is the
     **drift**, not the loop;
  5. **the server's abandonment counters** — video and audio — plus ⭐ **the
     gaps in the `numero` sequence**, which are the *second leg*: the
     count of abandonments measured from the receiving side, independent of the
     server's log (§6.2: *«a gap in the sequence is normal and
     means something»*).

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ THE TWO PREDICATES THAT DECIDE, AND THEY ARE WRITTEN FIRST — not prose
═══════════════════════════════════════════════════════════════════════════════

`07-b64-rete.py` carries finding **R13**: nine «expected» printed, archived and
**never compared**.  A bench like that cannot give red.  ⇒ Here every expectation is
a function that receives the numbers and returns `(passa, perche)`, and `passa` is
`None` when the bench **refuses to judge** — which is a third outcome, not a
polite green (`CODER.md` §3.10).

  **I1 — the rate does not drop because the scene is still** (`SPECIFICHE.md` §8.2).
  ⛔ It is the first predicate, and for this reason every step is run **in pairs**:
  still scene and moving scene, same step, same canvas, same everything.

  ⭐⭐ **And «still scene» here does NOT mean «scene off»**, which is what
  `07-b65 --scene no` does.  With the scene off the compositor delivers very little, and
  the frames per second of the two runs **are not comparable**: a low rate
  upstream looks in every way like a rate lowered by us.  ⇒ The still scene is
  `04-b30-scena --movimento marca`: **only the mark** changes, so the capture
  cadence stays that of the moving run and what changes is the **cost**, which is
  the only thing I1 wants to isolate.
  ⛔ And the predicate **refuses to judge** if the `delivered to RCP` of the two
  runs differ by more than 25 %: that difference is **upstream of us**, and
  attributing it to us would be the wound of `LEZIONI.md` §1.26 (*«a measured
  candidate is not a licence to attribute»*).

  **The image floor — 480p · 25 fps** (`DECISIONI.md` §2.1,
  reconfirmed on 23 August).  ⛔ And its reason has changed: it is no longer the
  level a poor line forces, it is **the bottom of the scale** — the
  point beyond which the regulator is not allowed to go down.
  ⇒ ⭐ **On a 20 Mbit/s line a rate below 25 per second is a
  DEFECT**, not a successful degradation.  It is a predicate, not a sentence.

═══════════════════════════════════════════════════════════════════════════════
⭐ THE STEPS — chosen around the floor, and two are DECLARED DIAGNOSIS
═══════════════════════════════════════════════════════════════════════════════

| step | what it is | the predicates |
|---|---|---|
| `g0-largo` | no limit and no delay: the denominator | requirement |
| ⭐ `g0b-ritardo` | only the 15 ms per side, free bandwidth. ⛔ **It exists because between `g0` and `g1` TWO things would change together** — the bandwidth and the round trip — and a difference attributable to both is attributed to nothing (`LEZIONI.md` §1.26) | requirement |
| `g1-40mbit` | twice the floor. ⚠ It is also the boundary of the declared H.264 level: `avc1.640032` is High **5.0**, and above 40 it would need 5.1 (`SPECIFICHE.md` §6.4) — we do not go higher here | requirement |
| `g2-30mbit` | the «good fixed line» of §3.1-bis | requirement |
| `g3-25mbit` | just above the floor: the first step where something may have to give way | requirement |
| ⭐ `g4-20mbit` | ⛔ **THE FLOOR. It is the step that decides the phase** | requirement |
| ⚠ `g5-15mbit` | **below the promise** — diagnosis | only «does not drop» |
| ⚠ `g6-10mbit` | half the floor — diagnosis: we watch **how** it gives way | only «does not drop» |

⛔ **Below the floor only one obligation remains in force**, and §3.1-bis says it
   in these words: *«it is not a refusal: the ban on dropping stays
   whole»*.  ⇒ At the diagnosis steps the bench measures everything and **demands one
   thing only: that the session does not die**.  Calling «red» a low rate at
   10 Mbit/s would mean measuring a promise the product does not make — that is
   repeating mistake 2 of v1 with the sign reversed.

⛔ **And the steps of `07-b65` (3 · 2 · 1 · 0.5 Mbit/s) do NOT come back**: they sit from
   seven to forty times below the floor, and the question they answered —
   *«who pays when the pipe is narrow»* — already has a measured answer
   (the audio, and because of the spiral of §5.2).  Redoing them here would give true numbers to a
   question that is no longer asked.

⛔ **THE WIRE'S QUEUE IS DECLARED, and it is not a detail.**  The default of
   `netem` is `limit 1000` packets: at 20 Mbit/s with 1452-byte packets
   that is **580 ms of cushion**, which by themselves would dominate the delay measurement and
   hide it inside the bench.  ⇒ Every step carries its own `limit`,
   calculated to be worth **50 ms** at its bandwidth, and the number is printed.
   ⚠ 50 ms is *sufficient, not right*: it is the order of magnitude of a home
   queue, and it is chosen here, not by a tool's default.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔⛔ WHAT THIS BENCH **CANNOT** SEE — and it is declared at the top
═══════════════════════════════════════════════════════════════════════════════

 1. ⛔⛔ **THE IMAGE.**  It counts frames, keyframes, bytes and delay.  It cannot say
    *«it looks worse»*.  ⚠ PSNR and SSIM do not appear in this file **by
    choice**: in v1 they were the verdict, and the verdict belongs to the user on the
    real desktop.  A green from this bench **does not authorise shipping anything
    that changes what is seen** (I6: switch off until they have
    looked at it).

 2. ⛔ **THE REAL DELAY.**  `RCP.md` §6.2: *«the `istante` is the server's monotonic
    clock; the client MUST NOT compare it with its own»*.  ⇒ Here the
    loop delay is NOT measured.  What is measured is the **DRIFT**:

        deriva(n) = (arrivo(n) − arrivo(0)) − (istante(n) − istante(0))

    that is **how far delivery has fallen behind capture since
    the run began**.  It is a difference of differences between two
    monotonic clocks **of the same kernel** (the client runs in a container
    on the same machine), so the two time bases cancel out and the two
    speeds are the same.  ⚠ The drift **starts from zero by construction**:
    it says how much the queue has GROWN, not what it is worth.  ⭐ The absolute value is
    measured by the loop of phase 8 — `[M]` 55.20 ms paired — and it needs a browser.

 3. ⛔ **THE REAL NETWORK.**  `netem` runs on `lo`: MTU 65536, no WiFi, no
    router queue, no third-party traffic, no migration.  ⭐ The
    20 Mbit/s floor **at the user's home** is throttled with
    `wondershaper` on the tablet, and **this bench does not do it**.  ⚠ The bench prints
    the **bytes per packet** read from the qdisc on purpose: if they are not ~1452 the
    grain of the throttling is not that of a network and the number must be reread.

 4. ⛔ **THE BROWSER.**  The client is `01-b3-cliente.py`: it takes the bytes from the wire
    and **does not decode and does not paint**.  «Delivered on the wire» is not
    «painted»: `[M]` phase 8, the worker paints more on the real chain and
    **73 % less** at saturation.  ⇒ The frames per second here are a
    **ceiling**, not what the user sees.

 5. ⛔ **THE QUALITY AT EACH STEP.**  Today the product **has no bitrate
    control** (`grep bit_rate|maxrate|bufsize codificatore.c` → zero) and the QP is
    fixed at 26 (`figlio.c:4052`, `rc_mode = CQP`).  ⇒ This bench measures what
    a product **without a regulator** does: it is the snapshot of the *before*.

 6. ⚠ **THE AUDIO.**  It reads its counters and prints them, but **does not judge it**: the
    sound judge is `banchi/07-b64-orecchio.py`, certified, and it is not
    rewritten here.  ⭐ And the question *«who pays between audio and video»* is already closed
    by `07-b65`: here the tone is **off** unless `--tone yes`, so the step
    measures the video and not a race.

 7. ⚠ **WHO ELSE IS ON THE MACHINE** (`LEZIONI.md` §1.26 — *«it does not give a red,
    it gives a plausible number»*).  The bench counts the listeners that are not its own and the
    load, and prints them; it cannot guarantee exclusivity.

 8. ⛔ **ITS OWN WEIGHT.**  The §11.1 trace is written by the client in memory: at
    20 Mbit/s for 30 s that is ~75 MB.  ⇒ The bench **always** compares the
    frames the client took with the server's `spediti`: if the
    client has fewer, the bottleneck may be the witness.  ⭐ And `--controllo-
    testimone` reruns the floor step **without a trace**, which is the
    direct proof.

═══════════════════════════════════════════════════════════════════════════════
⭐ WHAT IS NOT REWRITTEN — it is imported
═══════════════════════════════════════════════════════════════════════════════

  · the **network discipline** (detached guardian, four-band `prio`,
    two `u32` filters on the port only, `restore` that checks itself) is that of
    `banchi/07-b65-datagram.py`, **imported**, not copied: the environment is
    set BEFORE the import and then we **check** that the module took the right
    port and device, or the bench does not start;
  · the **magic numbers** of the §11.1 format are read from `banchi/01-b4-validatore.py`:
    two lists of versions in two files are two lists that diverge;
  · the **ground** is `banchi/07-b64-terreno.sh`, driven by the environment on
    MY ports — as `08-b67` does with `04-b32-terreno.sh`.

⛔⛔ AND THERE IS A SIBLING BENCH, `banchi/09-b68-ritmo.py`, FROM THE SAME DAY —
    port **7900**, user `prova`, by another agent.  It is declared here because
    two benches that ignore each other end up redoing the same measurement with
    different numbers.

    | | `09-b68` | ⭐ this one |
    |---|---|---|
    | the question | I1 **on a wide line**, one only | I1 **at every step** around the floor |
    | «still scene» | the scene **off** | ⭐ `--movimento marca`: alive, same cadence, different cost |
    | the expectation | prose plus a positive control (the `pieno` scene) | ⛔ **predicates written first** that return `(passa, perche)` |
    | the delay | does not measure it | the **drift**, from the §11.1 trace |
    | keyframes/deltas | from the «SPEDITO» lines of the log | **from the wire**, plus the gaps in `numero` |
    | the wire's bytes | `/proc/net/dev` (⭐ `[M]` `lo` at rest does **0 bytes in 5 s**) | the qdisc counter, **restricted to my port** |

    ⭐⭐ **And I took one thing from it, and it is the better of the two**: the
    **«empty waits»** of the child (`figlio.c:6842`).  My first guard of
    I1 compared the `delivered to RCP`; that one says *«we asked for a
    frame and there was none»*, which is the same distinction without deduction.
    ⇒ Now the guard is double, and the positive control has a case on purpose
    (10b) in which the `delivered` look alike and **only** the empty waits
    save the product from an accusation that is not its own.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ THE FOUR CURES OF 23 AUGUST 2026 — and they all have the same form
═══════════════════════════════════════════════════════════════════════════════

Four defects, one defect only: **silence instead of red**, that is a zero
that means *«I did not read»* with the face of one that means *«nothing
happened»* (`LEZIONI.md` §1.9).  They are written here because the project has
already paid for them several times, and next time let them be read first.

 1. ⛔ **`sudo -S` covers only the FIRST link of the chain** (see `chain_root()`
    and `root()`).  `[M]` the §11.1 trace reader **was not written** on the
    machine, and the bench did not notice.  ⇒ A single `sudo`, and the whole
    chain inside `bash -c`.
 2. ⛔⛔ **A trailing `< file` STEALS stdin from `sudo -S`** (same place).  `[M]`
    `log_line_list()` returned **0** silently, and then `server_counts()`
    read the log **from the server's startup**: `[M]` 23 Aug, on the
    still-scene run there would have been **4 041** empty waits instead of the **1 604**
    of the run.  ⇒ Redirection inside root's shell, `log_line_list()` that
    returns `None` instead of 0, a guard in `server_counts()` and a predicate that
    says so out loud (`p_log_read`).
 3. ⛔ **The implicit premise of I1** (see `p_I1` and `STILL_YIELD`).  *«With a still
    scene there is no congestion that justifies an abandonment»* holds **only on a
    line without loss**: `[M]` on `bad-home` (2 %) the abandonment leg
    gave a red that was not the product's.  ⇒ Conditioned leg: it refuses
    to judge where the premise is missing, and gives red where it holds.
 4. ⛔ **The empty journal because I did not read it** (see `giro()` and
    `p_nothing_detach`).  `[M]` 23 Aug: the §11.1 reader did not start —
    `01-b4-validatore.py` was missing from the tree — and the bench gave RED to «does not drop»
    on a session alive with **797** frames.  ⇒ The unread trace is
    declared, `terrain_check()` checks the referee before measuring, and the
    predicates that live on the journal refuse instead of accusing.

═══════════════════════════════════════════════════════════════════════════════
THE EXIT CODES
═══════════════════════════════════════════════════════════════════════════════

    0   COMPLIANT — all the predicates did what was written beforehand
    1   NOT COMPLIANT — there is at least one red
    2   wrong usage, ground missing, or the network could not be put back
    3   ⛔ I HAVE NOTHING TO JUDGE — a run produced no numbers, or
        a predicate refused to judge.  ⚠ It is not a green.

Usage (from the laptop):
    python3 banchi/09-b70-ritmo.py --certify     ⭐ HERE, without the machine
    python3 banchi/09-b70-ritmo.py terrain
    python3 banchi/09-b70-ritmo.py probe [--seconds 30] [--only g4]
    python3 banchi/09-b70-ritmo.py probe --witness-check
    python3 banchi/09-b70-ritmo.py restore         ⛔ and it is checked
"""
import argparse, base64, importlib.util, json, os, re, shlex, statistics, struct
import subprocess, sys, time

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ ISOLATION, WRITTEN BEFORE ANY IMPORT THAT READS IT
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ 7900 belongs to another agent, 7801/7802 belong to phase 7, 7730 is
#    the user's and it is ON.  Mine is 7809.
PORT = int(os.environ.get("PORT", "7809"))
ACCOUNT = os.environ.get("ACCOUNT", "provan9")
UID_B = int(os.environ.get("UID_B", "1029"))
MACHINE = os.environ.get("MACHINE", "nicfio@192.168.0.2")
SUDO_PASSWORD = os.environ.get("SUDO_PASSWORD", "nicfio")
ADDR = os.environ.get("ADDR", "192.168.0.2")
WORKDIR = os.environ.get("WORKDIR", "/media/REMOTIX/tmp/09-r")
TREE_DIR = os.environ.get("TREE", "/media/REMOTIX/src/09-r-src")
INSIDE_TREE = os.environ.get("INSIDE_TREE", "/srv/src/09-r-src")
INSIDE_WORK = os.environ.get("INSIDE_WORK", "/srv/remotix/tmp/09-r")
SCENE_BIN = os.environ.get("SCENE_BIN",
                           "/media/REMOTIX/src/04-b30-scena-lav/04-b30-scena")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("OUT", "/tmp/09-b70")

VIETATA = "enp7s0"     # ⛔ ssh and the user's 7730 go through it: never
DEV = "lo"

# ⛔ The ports that are NOT mine: they are counted first, and never touched.
NEARBY_PORTS = ["7700", "7710", "7720", "7730", "7801", "7802", "7900"]

GREEN, RED, YELLOW, GRAY = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (GREEN, GRAY, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (RED, GRAY, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (YELLOW, GRAY, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE NETWORK DISCIPLINE IS IMPORTED FROM 07-b65, AND THEN CHECKED
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `07-b65-datagram.py` binds its constants to the environment **at import**.  ⇒
#    The environment is set up here above and passed BEFORE importing it, so the
#    module is born with my port and the guardian writes the pid into my WORKDIR.
# ⛔⛔ And then it is CHECKED.  Importing a module that configures itself from the environment and
#      taking for granted that it has read it is exactly how one
#      ends up throttling someone else's port believing one is throttling
#      one's own — and the network is the only thing in this bench that, when wrong, hurts
#      those who have nothing to do with it.
def _import_network():
    for key, value in (("PORT", str(PORT)), ("ACCOUNT", ACCOUNT),
                           ("UID_B", str(UID_B)), ("MACHINE", MACHINE),
                           ("SUDO_PASSWORD", SUDO_PASSWORD), ("ADDR", ADDR),
                           ("WORKDIR", WORKDIR), ("TREE", TREE_DIR),
                           ("INSIDE_TREE", INSIDE_TREE), ("INSIDE_WORK", INSIDE_WORK),
                           ("OUT", OUT)):
        os.environ[key] = value
    path = os.path.join(HERE, "07-b65-datagram.py")
    spec = importlib.util.spec_from_file_location("b65rete", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    troubles = []
    if m.PORT != PORT:
        troubles.append("the module's port is %d, mine is %d" % (m.PORT, PORT))
    if m.DEV != DEV:
        troubles.append("the module's device is «%s», mine is «%s»" % (m.DEV, DEV))
    if m.VIETATA != VIETATA:
        troubles.append("the module's forbidden interface is «%s»" % m.VIETATA)
    if m.WORKDIR != WORKDIR:
        troubles.append("the guardian would write the pid in «%s», not in «%s»" % (m.WORKDIR, WORKDIR))
    if troubles:
        raise SystemExit("⛔ I DO NOT TOUCH THE NETWORK: the import of 07-b65 did not take "
                         "my environment — " + " · ".join(troubles))
    return m


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE STEPS — and the expectation of each is a PREDICATE, further down
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ There is always a delay: without RTT the congestion window has no way to
#    fill up and the pacer notices nothing.  15 ms per side = 30 ms of
#    round trip, which is a home fibre line.
DELAY_MS = int(os.environ.get("DELAY_MS", "15"))
CUSHION_MS = int(os.environ.get("CUSHION_MS", "50"))   # ⛔ the wire's queue, declared
PACKAGE = 1452                                        # the typical QUIC packet


def _limit(mbit):
    """The queue packets worth `CUSHION_MS` at that bandwidth."""
    return max(8, int(mbit * 1e6 * (CUSHION_MS / 1000.0) / 8.0 / PACKAGE))


def _rules(mbit, delay_ms):
    """⛔ EVEN THE WIDE STEP CARRIES A `netem`, and the reason is quantity 3.

    The real bytes on the wire are read from the qdisc counter (`tc -s`).  A
    step without a qdisc does not have that counter ⇒ the **denominator** would be
    the only run without the bytes on the wire, that is the only run that cannot be
    compared with the others on the quantity that decides whether the line is full.
    ⇒ `g0` carries a `netem` **without bandwidth and without delay**: it serves only to
    count.  ⚠ And its price is declared — one more qdisc in the path —
    instead of leaving the denominator blind.
    """
    rules = ["limit", str(_limit(mbit)) if mbit else "100000"]
    if delay_ms:
        rules += ["delay", "%dms" % delay_ms]
    if mbit:
        rules += ["rate", "%dmbit" % mbit]
    return rules


#  (name, mbit, delay_ms, requirement, why)
#
# ⭐⭐ AND THE DELAY HAS A STEP OF ITS OWN.  If `g0` had no delay and `g1` had
#     delay **and** bandwidth, TWO things would change together between them, and any
#     difference would be attributable to both — which is the politest way
#     in which a grid of steps can lie (`LEZIONI.md` §1.26: *«every
#     number must be attributed on its own»*).  ⇒ `g0b` carries the 15 ms **and nothing else**.
RUNGS = [
    ("g0-largo",   None, 0, True,
     "no limit and no delay: the denominator. The netem is there only to "
     "count the bytes"),
    ("g0b-ritardo", None, DELAY_MS, True,
     "⭐ only the %d ms per side, free bandwidth: isolates the effect of the ROUND TRIP "
     "from that of the bandwidth" % DELAY_MS),
    ("g1-40mbit",  40, DELAY_MS, True,
     "twice the floor — and the boundary of the declared H.264 level (5.0)"),
    ("g2-30mbit",  30, DELAY_MS, True,
     "the «good fixed line» of §3.1-bis: aiming at the desired"),
    ("g3-25mbit",  25, DELAY_MS, True,
     "just above the floor: the first step where something may give way"),
    ("g4-20mbit",  20, DELAY_MS, True,
     "⭐ THE FLOOR (§3.1-bis). It is the step that decides the phase"),
    ("g5-15mbit",  15, DELAY_MS, False,
     "⚠ BELOW THE PROMISE — declared diagnosis: we look, we do not demand"),
    ("g6-10mbit",  10, DELAY_MS, False,
     "⚠ half the floor — diagnosis: what matters is HOW it gives way, not whether"),
]

# ⭐ The canvas.  The grid runs at 1080p, which is the real desktop and the one the
#    user looks at.  ⛔ But the floor of §2.1 is written **at 480p**, and adaptive
#    resolution is out of the product by decision (§5.0-ter): the
#    product serves the canvas the client asks for, and that is all.  ⇒ At the floor
#    step only, the pair is also redone at **768x480**, which is the number
#    the project already writes for «the minimum of §2.1» (`DECISIONI.md:1133`).
FULL_CANVAS = os.environ.get("CANVAS", "1920x1080")
MIN_CANVAS = os.environ.get("MIN_CANVAS", "768x480")

# ⭐ The codec is declared and CHECKED on the wire.  The server offers «hevc,h264»
#    (`rcp.c:1674`); the client's default is «hevc,av1», which would negotiate
#    **HEVC** — that is an operating point that is not the product's, because
#    Firefox on Android has neither HEVC nor AV1.  ⇒ We ask for h264, and the bench
#    reads from the wire which codec really arrived: a silent fallback to
#    another codec would change every number on this page without saying so.
REQUESTED_CODEC = os.environ.get("CODEC", "h264")
CODEC_NUMBER = {1: "hevc", 2: "av1", 3: "h264"}


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE THRESHOLDS, IN ONE PLACE ONLY, AND EACH WITH ITS REASON
# ═══════════════════════════════════════════════════════════════════════════
FLOOR_FPS = 25.0        # `DECISIONI.md` §2.1: 480p · 25 fps, the bottom of the scale
WINDOW_FLOOR = 20.0   # ⚠ *sufficient, not right*: 80 % of the floor, and
                            #   it serves only not to give red to a window that
                            #   falls across a single hiccup.  The first
                            #   run that lands between 20 and 25 must be looked at, not
                            #   retuned.
QUOTA_DELTA = 0.90          # §3.3: we degrade IN TIME.  A stream that loses more
                            #   than one delta in ten is degenerating into keyframes —
                            #   `[M]` 21 Aug: on the narrow runs they were 144/144.
DRIFT_END_MS = 250.0      # ⭐ anchored to a measured number, not chosen: the whole
                            #   loop of phase 8 is worth `[M]` 55.20 ms.  A drift
                            #   worth FOUR loops is no longer a delay, it is
                            #   a queue.
DRIFT_MAX_MS = 400.0
I1_TOLERANCE = 0.05        # ⚠ the noise between two runs on the same machine
I1_DELIVERED = 0.25        # beyond it, the difference is UPSTREAM and is not judged
STILL_YIELD = 0.98           # ⛔⛔ AND ITS PREMISE IS CONDITIONAL, not general:
                            #   «with a still scene there is no congestion that
                            #   justifies an abandonment» holds **only on a
                            #   line that does not lose**.  `[M]` 23 Aug 2026: on the
                            #   `bad-home` profile (2 % loss) the
                            #   premise is FALSE and this leg gave a red
                            #   that was not a product defect — while the
                            #   frames/s leg passed (still 10.13/s
                            #   against moving 7.78/s: the still one went FASTER).
                            #   ⇒ The leg is not removed: it is conditioned on the fact
                            #     that justifies it (see `p_I1`).
WARMUP_S = 3.0            # ⛔ the first seconds are session opening and first
                            #   keyframe: they are declared and removed, and the whole
                            #   number is printed alongside all the same
MIN_FRAMES = 30      # below this, there is nothing to reduce


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE TRACE READER — it runs ON THE MACHINE, because the trace is heavy
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ No new tool is invented to know when a frame
#    arrived: `01-b3-cliente.py --record` already writes the trace of
#    `RCP.md` §11.1, which carries for every block the `instant_ms` of the client's
#    **monotonic clock** and the bytes, and the first block of every video stream
#    carries the 28 header bytes of §6.2 — `number`, `kind` (keyframe or delta),
#    `codec` and the **server's** monotonic `instant` at capture.
#    ⇒ Everything needed is already on disk: here we reduce, we do not measure.
#
# ⚠ The grain is the millisecond (§11.1 writes `instant_ms`).  On an interval
#   of 40 ms that is 2.5 %: enough for the rate and for the drift, it would **not** be enough
#   for a loop — and it is another reason why the loop does not belong here.
#
# ⛔ And the trace is reduced **on the machine**: at 20 Mbit/s for 30 s that is ~75 MB,
#    and carrying them over ssh at every run would be an hour of network for an 80 KB JSON.
READER = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09-b70-leggi — reduces an RCP.md §11.1 trace to the JOURNAL of frames.

⛔⛔ THE FORMAT IS NOT REWRITTEN HERE.  Magic, block layout, `fine`
    codes and direction are read from `01-b4-validatore.py`, which is **the referee** of
    §11.1.  Two descriptions of the same format in two files are two
    descriptions that diverge, ⚠ and it has already cost a whole run: on 16 August
    2026 the recorder still wrote `0x00 0x01` while the referee had moved
    to `0x00 0x02`, and **every** trace came out «malformed» — a defect born between
    two files, where no unit test looks.
"""
import importlib.util, json, struct, sys

VIDEO_CHANNEL = 0x03


def arbitro(percorso):
    spec = importlib.util.spec_from_file_location("b4arbitro", percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def principale():
    traccia, validatore = sys.argv[1], sys.argv[2]
    A = arbitro(validatore)
    MAGIC, BLOCK, BLOCK_BYTES = A.MAGIC, A.BLOCK, A.BLOCK_BYTES
    SERVER, FIN, RESET = A.SERVER, A.FIN, A.RESET
    with open(traccia, "rb") as f:
        d = f.read()
    if len(d) < 16 or d[:8] != MAGIC:
        print(json.dumps({"outcome": "I HAVE NOTHING TO JUDGE — the trace does not "
                                   "carry the magic of §11.1",
                          "primi8": d[:8].hex()}))
        return 3
    quanti, orologio, r1, r2, r3 = struct.unpack("!IBBBB", d[8:16])
    if A.CLOCK.get(orologio) != "client":
        # ⛔ Without knowing WHOSE the times are, the drift cannot even be
        #    stated: we do not guess.
        print(json.dumps({"outcome": "I DO NOT JUDGE — the trace's clock is not "
                                   "the client's", "orologio": orologio}))
        return 3
    p, letti = 16, 0
    flussi, ordine = {}, []
    for _ in range(quanti):
        if p + BLOCK_BYTES > len(d):
            break
        verso, canale, fine, ist, stream, lung, nosc = struct.unpack(
            BLOCK, d[p:p + BLOCK_BYTES])
        p += BLOCK_BYTES
        p += nosc * 40                       # (ini u32, quanti u32, fingerprint 32 B)
        carico = d[p:p + lung]
        p += lung
        letti += 1
        if verso != SERVER or canale != VIDEO_CHANNEL:
            continue
        f = flussi.get(stream)
        if f is None:
            f = flussi[stream] = {"testa": b"", "byte": 0, "fine_ms": None,
                                  "azzerato": False}
            ordine.append(stream)
        if len(f["testa"]) < 28:
            f["testa"] += carico[:28 - len(f["testa"])]
        f["byte"] += lung
        if fine == FIN:
            f["fine_ms"] = ist
        elif fine == RESET:
            # ⭐ §5.1 form A: the server ABANDONED this frame, and it
            #    shows from the receiving side.  It is not a delivered frame.
            f["azzerato"] = True
            f["fine_ms"] = ist
    giornale, zeroed, monchi = [], 0, 0
    for sid in ordine:
        f = flussi[sid]
        if f["azzerato"]:
            zeroed += 1
            continue
        if f["fine_ms"] is None or len(f["testa"]) < 28:
            # ⚠ A stream the recording did not see finish: it is not a
            #   delivered frame and it is not an abandonment.  It is counted apart,
            #   instead of vanishing inside one of the two.
            monchi += 1
            continue
        type, codec, l, a, number, istante, inp = struct.unpack("!HHIIIQI", f["testa"])
        giornale.append({"number": number, "key": type == 0x0301,
                         "type": type, "codec": codec, "l": l, "a": a,
                         "byte": max(0, f["byte"] - 28),
                         "istante_us": istante, "arrivo_ms": f["fine_ms"]})
    giornale.sort(key=lambda x: x["arrivo_ms"])
    print(json.dumps({"outcome": "letto", "blocks": letti, "streams": len(ordine),
                      "zeroed": zeroed, "monchi": monchi,
                      "giornale": giornale}))
    return 0


if __name__ == "__main__":
    sys.exit(principale())
'''


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE REDUCTION — and it is THE SAME CODE that `--certify` exercises
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ The positive control of this file does not test the predicates on numbers already
#    prepared: it builds JOURNALS and passes them through here.  ⇒ If the deception lives
#    in the reduction — and it is the case of the mean that hides the gap — the
#    control sees it.  A control that skipped this function would certify
#    half of the tool.
def _median(v):
    return statistics.median(v) if v else None


def measure(giornale, requested_s, server=None, wire=None, zeroed=None,
           warmup_s=WARMUP_S):
    """From a journal of frames to the numbers of the run.  All five."""
    n = {"requested_s": requested_s, "fotogrammi_grezzi": len(giornale),
         "warmup_s": warmup_s, "server": server or {},
         "azzerati_sul_filo": zeroed}
    if not giornale:
        n["outcome"] = ("I HAVE NOTHING TO JUDGE — no frame in the "
                      "trace")
        return n
    a0 = giornale[0]["arrivo_ms"]
    lived = (giornale[-1]["arrivo_ms"] - a0) / 1000.0
    n["vissuto_s"] = round(lived, 3)
    # ⛔ The warm-up is REMOVED and SAID: session opening, first keyframe and
    #    first canvas sit in there, and mixing them with steady state is like measuring
    #    a car's acceleration counting also the time to start the engine.
    #    ⚠ And the whole number is printed alongside all the same: whoever removes data
    #      must show what they removed.
    a_regime = [f for f in giornale if (f["arrivo_ms"] - a0) / 1000.0 >= warmup_s]
    n["fotogrammi_scaldata"] = len(giornale) - len(a_regime)
    if len(a_regime) < MIN_FRAMES:
        n["outcome"] = ("I HAVE NOTHING TO JUDGE — %d frames at steady state, "
                      "fewer than the minimum of %d" % (len(a_regime), MIN_FRAMES))
        n["frames"] = len(a_regime)
        return n
    r0 = a_regime[0]["arrivo_ms"]
    duration = (a_regime[-1]["arrivo_ms"] - r0) / 1000.0
    if duration <= 0:
        n["outcome"] = "I HAVE NOTHING TO JUDGE — zero steady-state duration"
        return n
    n["frames"] = len(a_regime)
    n["duration_s"] = round(duration, 3)
    # 1 · THE RATE, and they are TWO numbers: the mean and the window minimum.
    n["fps"] = round(len(a_regime) / duration, 2)
    n["fps_intero"] = round(len(giornale) / lived, 2) if lived > 0 else None
    n["fps_finestra_min"], n["finestre"] = _min_window(a_regime)
    intervals = [(a_regime[i]["arrivo_ms"] - a_regime[i - 1]["arrivo_ms"])
                  for i in range(1, len(a_regime))]
    n["intervallo_mediano_ms"] = _median(intervals)
    n["intervallo_p95_ms"] = (sorted(intervals)[int(0.95 * (len(intervals) - 1))]
                              if intervals else None)
    # 2 · KEYFRAMES AND DELTAS — §3.3 lives here.
    keys = sum(1 for f in a_regime if f["key"])
    n["keys"] = keys
    n["delta"] = len(a_regime) - keys
    n["quota_delta"] = round(n["delta"] / len(a_regime), 4)
    # ⭐ The REAL codec, read from the wire: not the one requested.
    codes = sorted({f.get("codec") for f in a_regime})
    n["codec_sul_filo"] = [CODEC_NUMBER.get(c, "?%s" % c) for c in codes]
    measures = sorted({"%dx%d" % (f.get("l"), f.get("a")) for f in a_regime})
    n["tela_sul_filo"] = measures
    # 3 · THE BYTES — payload here, wire from the qdisc (further down).
    byte = sum(f["byte"] for f in a_regime)
    n["byte_carico"] = byte
    n["mbit_s_carico"] = round(byte * 8 / duration / 1e6, 3)
    n["bytes_per_frame"] = int(byte / len(a_regime))
    if wire and wire.get("byte") is not None and wire.get("seconds"):
        n["mbit_s_filo"] = round(wire["byte"] * 8 / wire["seconds"] / 1e6, 3)
        n["byte_per_pacchetto"] = wire.get("byte_per_pacchetto")
    else:
        # ⛔ `CODER.md` §3.10: «I did not read» is not «zero».  A 0.0 Mbit/s here
        #    would say «nothing goes over the wire» of a line that carries.
        n["mbit_s_filo"] = None
        n["byte_per_pacchetto"] = None
        n["filo_non_letto"] = "the qdisc counter was not read"
    # 4 · THE DRIFT — and it is NOT the loop delay (see the header).
    s0 = a_regime[0]["istante_us"]
    d0 = 0.0
    derive = []
    for f in a_regime:
        d = ((f["arrivo_ms"] - r0) - (f["istante_us"] - s0) / 1000.0)
        derive.append(d)
    n["deriva_fine_ms"] = round(derive[-1] - d0, 1)
    n["deriva_max_ms"] = round(max(derive) - d0, 1)
    n["deriva_min_ms"] = round(min(derive) - d0, 1)
    # 5 · THE ABANDONMENTS, and the SECOND LEG that does not go through the log.
    #     §6.2: `number` grows by one for every frame the server
    #     DECIDES to send, abandoned ones included, and NOT for those it does not
    #     send at all.  ⇒ A gap = a frame that left and did not arrive.
    numbers = sorted(f["number"] for f in a_regime)
    holes = 0
    for i in range(1, len(numbers)):
        jump = numbers[i] - numbers[i - 1]
        if jump > 1:
            holes += jump - 1
    n["buchi_numero"] = holes
    n["outcome"] = "measured"
    return n


def _min_window(frames, width_ms=1000):
    """⛔⛔ THE NUMBER THE MEAN HIDES.

    Thirty seconds made of ten at 45/s and twenty at 17.5/s give a mean of
    **26.7/s** — above the floor — and twenty seconds in which the desktop
    stutters.  ⇒ The mean alone acquits, and it must be accompanied by the **worst** that
    was seen in one second.  ⚠ The window is SLIDING, not in blocks: in
    blocks the gap can sit across two windows and vanish from both.
    """
    if len(frames) < 2:
        return None, 0
    t = [f["arrivo_ms"] for f in frames]
    worse, how_many, i = None, 0, 0
    for j in range(len(t)):
        if t[j] - t[0] < width_ms:
            continue
        while t[j] - t[i] > width_ms:
            i += 1
        # frames in the window (t[i], t[j]]
        tally = j - i
        how_many += 1
        if worse is None or tally < worse:
            worse = tally
    if worse is None:
        return None, 0
    return float(worse), how_many


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE PREDICATES — WRITTEN FIRST, and they return (passes, why)
# ═══════════════════════════════════════════════════════════════════════════
#
#   passes = True    the expectation held
#   passes = False   ⛔ red
#   passes = None    ⚠ I DO NOT JUDGE — and it is not a polite green: it is an outcome of its own,
#                   and makes the bench exit 3.
def _si(why):    return (True, why)
def _no(why):    return (False, why)
def _mute(why):  return (None, why)


def _has_measured(n):
    return n.get("outcome") == "measured"


def p_log_read(n):
    """⛔⛔ THE PREDICATE THAT LOOKS AT THE TOOL, NOT THE PRODUCT — and it is here because
       the defect it covers is MUTE.

    `LEZIONI.md` §1.9: *«a zero that means "I did not read" and a zero that
    means "nothing happened" must not have the same face»*.
    `[M]` 23 August 2026: `log_line_list()` returned 0 because a trailing `< file`
    stole stdin from `sudo -S` (see `chain_root()`), and from then on
    **every** number on the server side was cumulative from startup — including
    `attese_a_vuoto`, which is the column with which `p_I1` decides whether to refuse.
    ⇒ A bench that goes straight on with that zero is not a bench: it gives a green to
      a measurement it did not make.

    ⚠ It applies at EVERY step, even the diagnosis ones: it is not a promise of the
      product, it is the condition for the numbers to belong to this run.
    """
    s = n.get("server") or {}
    if s.get("registro_non_letto"):
        return _mute("%s ⇒ I do NOT JUDGE this run on the server side"
                     % s["registro_non_letto"])
    if not s:
        return _mute("this run does not carry the server-side counts")
    if "riga0" in s:
        return _si("the log was read from line %d on: the server's counts "
                   "belong TO THIS RUN, not to the time since startup" % s["riga0"])
    return _si("the server-side counts are there")


def p_nothing_detach(n):
    """⛔ The ONLY obligation that holds EVEN below the floor — §3.1-bis:
       *«it is not a refusal: the ban on dropping stays whole»*.

    ⚠ And «some frames arrived» is not enough: a run that dies halfway
      delivers perfectly good frames for half the time.  ⇒ We look at
      how long it LASTED against how long was requested.
    """
    # ⛔⛔ FIRST OF ALL: a journal empty because I DID NOT READ IT is not a
    #     journal empty because nothing arrived (`LEZIONI.md` §1.9).
    #     `[M]` 23 Aug 2026: this predicate gave red to a live session
    #     — 797 frames sent and taken — only because the §11.1 reader
    #     had not started.  ⇒ Here we refuse, and the reason is the true one.
    if n.get("traccia_non_letta"):
        return _mute("%s — the journal is empty because I DID NOT READ IT, not "
                     "because the session died: I DO NOT JUDGE"
                     % n["traccia_non_letta"])
    lived, requested = n.get("vissuto_s"), n.get("requested_s")
    if not requested:
        return _mute("I do not know how much was requested")
    if not n.get("fotogrammi_grezzi"):
        return _no("no frame in %.0f s: the session delivered "
                   "nothing" % requested)
    if lived is None:
        return _mute("I do not know how long delivery lasted")
    if lived < 0.90 * requested:
        return _no("delivery lasted %.1f s out of %.0f requested: it dropped"
                   % (lived, requested))
    return _si("it delivered for %.1f s out of %.0f requested: it did not drop"
               % (lived, requested))


def p_rate_floor(n):
    """⭐ `DECISIONI.md` §2.1 + §3.1-bis, together: **on a 20 Mbit/s line
       a rate below 25 per second is a DEFECT**, not a successful
       degradation.

    ⛔ And they are TWO legs, because a single one can be fooled:
       · the steady-state **mean**;
       · the **minimum over a one-second window**, which is the only one that sees the
         gap inside a good mean.
    """
    if not _has_measured(n):
        return _mute(n.get("outcome", "I did not measure"))
    fps, fin = n["fps"], n["fps_finestra_min"]
    if fin is None:
        return _mute("less than one whole window: the minimum does not exist")
    if fps < FLOOR_FPS:
        return _no("mean %.2f/s below the floor of %.0f/s (§2.1)"
                   % (fps, FLOOR_FPS))
    if fin < WINDOW_FLOOR:
        return _no("mean %.2f/s is fine, ⛔ but there is a second with %.0f "
                   "frames: the mean was hiding the gap" % (fps, fin))
    return _si("mean %.2f/s and worst second %.0f/s, above the floor of "
               "%.0f/s" % (fps, fin, FLOOR_FPS))


def p_degrades_over_time(n):
    """⛔ §3.3: *«FRAMES are dropped. Never blur, never drop the session»* — and the
       worst form of degradation is not blurring: it is **the stream of keyframes
       only**.

    `[M]` 21 August 2026: on the narrow runs the delivered frames were
    **144/144, 149/149** all keyframes, against **2 out of 1 019** at 15 Mbit/s.  Every
    abandonment of §5.1 switches on the debt of §5.2, the debt makes us ask for a
    keyframe, the keyframe fills the window, and it starts again.  ⇒ The stream degrades
    **in space AND in time together**, which is the opposite of what §3.3
    asks.
    """
    if not _has_measured(n):
        return _mute(n.get("outcome", "I did not measure"))
    if n["keys"] + n["delta"] == 0:
        return _mute("no frame classified")
    q = n["quota_delta"]
    if q < QUOTA_DELTA:
        return _no("deltas %.1f %% (%d keyframes out of %d): the stream is degenerating "
                   "into keyframes — it is the spiral of §5.2"
                   % (q * 100, n["keys"], n["keys"] + n["delta"]))
    return _si("deltas %.1f %% (%d keyframes out of %d): it degrades in time, not into keyframes"
               % (q * 100, n["keys"], n["keys"] + n["delta"]))


def p_delay_no_runaway(n):
    """⛔ `SPECIFICHE.md:128`: *«every intermediate buffer buys smoothness and sells
       responsiveness»*, and delay weighs more than frames.

    ⚠ Here the **drift** is measured (see the header), not the loop.  The
      threshold is anchored to a measurement, not chosen: the whole loop of phase 8
      is worth `[M]` **55.20 ms**; a drift of 250 ms is worth **four loops**, and at
      that point it is no longer a delay, it is a queue.
    """
    if not _has_measured(n):
        return _mute(n.get("outcome", "I did not measure"))
    fine, mas = n["deriva_fine_ms"], n["deriva_max_ms"]
    if fine > DRIFT_END_MS:
        return _no("delivery fell behind capture by %.0f ms "
                   "(ceiling %.0f)" % (fine, DRIFT_END_MS))
    if mas > DRIFT_MAX_MS:
        return _no("the drift touched %.0f ms (ceiling %.0f), though it came back to "
                   "%.0f" % (mas, DRIFT_MAX_MS, fine))
    return _si("final drift %.0f ms, maximum %.0f: the queue did not run away"
               % (fine, mas))


def _declared_loss(*rounds, **kw):
    """The loss of the line under these runs, in %, or `None` if I DO NOT KNOW.

    ⛔ It is not assumed: it is read from what the run carries with it — and the one who
       writes it is `cur_round()`, which gets it from the **installed qdisc** (see
       `_round_line()`).  ⚠ So it holds even when the run was run by
       someone else with a `netem` of their own: `09-b76-rete-cattiva.py` calls
       `B70.cur_round()` with `loss` on, and this function sees it all the same.

    ⭐ And `None` is NOT zero: if I do not know whether the line loses, the premise of the
       abandonment leg is not verified, and an unverified premise does not give
       the right to give red.
    """
    explicit = kw.get("loss_pc")
    if explicit is not None:
        return float(explicit), "declared by whoever called me"
    for g in rounds:
        for dove, key in (("linea", "loss_pc"), ("probe", "persi_pc")):
            v = ((g or {}).get(dove) or {}).get(key)
            if v is not None:
                return float(v), "read from «%s.%s» of the run" % (dove, key)
    return None, ("no run of the pair declares the loss of the line")


def p_I1(halt, move, loss_pc=None):
    """⛔⛔ INVARIANT I1, AND IT IS THE FIRST PREDICATE OF THE PHASE.

    `SPECIFICHE.md` §8.2: *«The rate never drops out of caution, to save, or
    because the scene is still»*.  It is the wound from which the whole phase is born: in v1
    the bitrate control *«on a little-moving desktop went down to 2-6 Mbit/s,
    happy to save»*.

    ⛔ **The first thing this predicate does is refuse to judge**
       when the two runs are not comparable.  If the compositor
       delivered far fewer frames to the server in the still run, the lower
       rate is **upstream of us**: attributing it to I1 would be exactly
       the mistake of `LEZIONI.md` §1.26, where a true number was given to the
       wrong cause because the cause was convenient.

    ⭐ And then they are TWO legs, because neither is enough:
       · **the frames per second** — the quantity the user feels.  ⚠ It always
         holds: it is a comparison between two runs on the **same** line, so
         any fault of the line is in both and cancels out;
       · **the `spediti/consegnati` yield and the abandonments** — because the cadence
         can be identical while we throw away: with a still scene there is
         no congestion that justifies an abandonment, so **zero** are
         enough.

    ⛔⛔ AND THE SECOND LEG HAS A PREMISE, which until 23 August 2026 was
        implicit and for this reason **false without saying so**: *«with a still scene there is no
        congestion that justifies an abandonment»* holds on a line that **does not
        lose**.  On a line that loses 2 % (`bad-home`, `[M]` 23 Aug)
        the abandonments are justified by the loss, and that evening this leg
        gave a red that was not a product defect — with the
        frames/s leg passing (still **10.13/s** against moving **7.78/s**: the
        still one went faster).
    ⇒ The leg is NOT removed and not widened: it is CONDITIONED.  On a line without
      loss it gives red as before; on a line that loses — or on a line of which
      I do not know whether it loses — **it refuses to judge it** and writes so.  ⚠ And if
      meanwhile the first leg is red, the red stays: loss explains the
      abandonments, it does not explain a rate that drops when the scene stops.
    """
    if not (_has_measured(halt) and _has_measured(move)):
        return _mute("one of the two runs of the pair did not measure: "
                     "still «%s», moving «%s»"
                     % (halt.get("outcome"), move.get("outcome")))
    cf = (halt.get("server") or {}).get("delivered")
    cm = (move.get("server") or {}).get("delivered")
    if not cf or not cm:
        return _mute("the log did not give the «delivered to RCP» of the two runs: "
                     "without a denominator the pair is not comparable")
    gap = abs(cf - cm) / float(max(cf, cm))
    if gap > I1_DELIVERED:
        return _mute("the compositor delivered %d frames with the scene still "
                     "against %d with the scene moving (%.0f %% apart): the difference "
                     "is UPSTREAM of us and I do NOT judge it as I1" % (cf, cm, gap * 100))
    # ⭐⭐ THE BEST GUARD, and it does not deduce: the child's EMPTY WAITS.
    #     If with a still scene we asked for a frame and there was none, the
    #     lower rate is the compositor's and the product has nothing to do with it.  ⛔ It is
    #     the distinction `04-b32-ritmo.py` exists to make, and the line
    #     `figlio.c:2669` records the time it was made the other way round:
    #     *«the thesis was false: Mutter had the frames, and we were not there
    #     to take them»*.
    vf = ((halt.get("server") or {}).get("capture") or {}).get("attese_a_vuoto")
    vm = ((move.get("server") or {}).get("capture") or {}).get("attese_a_vuoto")
    if vf is not None and vm is not None and vf > max(20, 3 * (vm + 1)):
        return _mute("with the scene still the child waited EMPTY %d times "
                     "(against %d with the scene moving): the frame was not there, and the "
                     "lower rate belongs to the COMPOSITOR — I do not judge it "
                     "as I1" % (vf, vm))
    # ── FIRST LEG: the rate.  It holds on any line (see the docstring) ───────
    troubles = []
    if halt["fps"] < move["fps"] * (1.0 - I1_TOLERANCE):
        troubles.append("the rate with the scene STILL is %.2f/s against %.2f/s with the scene "
                    "moving: it drops when it must not" % (halt["fps"], move["fps"]))
    # ── SECOND LEG: the abandonments.  ⛔ And FIRST its premise ──────────────
    dropped = []
    ab = (halt.get("server") or {}).get("abbandonati")
    if ab:
        dropped.append("with the scene still the server abandoned %d frames" % ab)
    sp = (halt.get("server") or {}).get("sent")
    if sp is not None and cf:
        yield_ratio = sp / float(cf)
        if yield_ratio < STILL_YIELD:
            dropped.append("with the scene still %d frames went out out of %d "
                           "delivered to RCP (yield %.3f, below %.2f)"
                           % (sp, cf, yield_ratio, STILL_YIELD))
    loss, da_dove = _declared_loss(halt, move, loss_pc=loss_pc)
    premise = (loss == 0.0)
    if dropped and not premise:
        reason = ("the premise of this leg — «with a still scene there is no "
                  "congestion that justifies an abandonment» — holds ONLY on a "
                  "line without loss, and here %s (%s)"
                  % ("the line loses %.2f %%" % loss if loss is not None
                     else "I do NOT KNOW whether the line loses", da_dove))
        if troubles:
            # ⚠ The red of the rate stays: loss explains the abandonments, it does not
            #   explain a rate that drops when the scene stops.
            return _no("%s · ⚠ and the abandonments I do NOT judge (%s): %s"
                       % (" · ".join(troubles), reason, "; ".join(dropped)))
        return _mute("%s, but %s ⇒ I do NOT JUDGE the abandonments. ⭐ The "
                     "frames/s leg held: still %.2f/s against moving %.2f/s"
                     % ("; ".join(dropped), reason, halt["fps"], move["fps"]))
    troubles += ["%s, and on a line without loss there is no congestion that "
             "justifies them" % b for b in dropped]
    if troubles:
        return _no(" · ".join(troubles))
    return _si("still scene %.2f/s against moving %.2f/s, delivered %d against %d, "
               "zero abandonments with the scene still (line %s): I1 holds"
               % (halt["fps"], move["fps"], cf, cm,
                  "without loss" if premise else
                  "with loss %s — but there was nothing to justify"
                  % ("%.2f %%" % loss if loss is not None else "unknown")))


# The predicates that apply to a single run, in order.
ROUND_PREDICATES = [
    # ⛔ First, because if this one refuses the three server-side numbers
    #    that follow do not belong to this run.  And it applies everywhere (`False`).
    ("the log belongs to THIS run (§1.9)", p_log_read, False),
    ("does not drop (§3.1-bis, holds even below the floor)", p_nothing_detach, False),
    ("the rate floor (§2.1: 25/s)", p_rate_floor, True),
    ("degrades in time, not into keyframes (§3.3)", p_degrades_over_time, True),
    ("the delay does not run away (the drift)", p_delay_no_runaway, True),
]


def judge_round(n, requirement):
    """⛔ At the diagnosis steps we MEASURE everything and DEMAND one thing only.

    Calling red a low rate at 10 Mbit/s would mean measuring a
    promise the product does not make (§3.1-bis) — that is repeating mistake 2 of v1
    with the sign reversed.  ⇒ The predicates that are not a requirement at that step
    run all the same and their outcome is WRITTEN, marked «diagnosis».
    """
    report = []
    for name, f, only_if_requirement in ROUND_PREDICATES:
        passes, why = f(n)
        count = requirement or not only_if_requirement
        report.append({"predicato": name, "passes": passes, "why": why,
                      "count": count})
    return report


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE POSITIVE CONTROL — «how does this bench know it can see?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ On the model of `banchi/07-b64-orecchio.py --certify`, and for the same
#    reason: *«a bench that cannot see the defect it looks for has no right
#    to green»* (`PIANO.md` §0.3.4).
#
# ⭐ And the cases do NOT pass ready-made numbers to the predicates: they build
#    JOURNALS and pass them through `measure()`, which is the same function that
#    runs on the real runs.  ⇒ A deception that lives in the REDUCTION — and it is case
#    2, the mean that hides the gap — is seen.  Certifying the predicates
#    alone would certify half of the tool.
def _fab(stretches, byte=25000, key_every=0, drift_ms_per_frame=0.0,
         number_from=1, skip_every=0):
    """Builds a journal.  `stretches` = [(fps, seconds), ...].

    ⛔ `arrivo_ms` is the CLIENT's clock, `instant_us` the SERVER's: the
       drift is built by moving the second away from the first, which is what
       happens when the queue grows.
    """
    g, t_arr, t_cat, number, i = [], 0.0, 0.0, number_from, 0
    for fps, seconds in stretches:
        step = 1000.0 / fps
        for _ in range(int(round(fps * seconds))):
            key = (key_every and i % key_every == 0) or i == 0
            skip = skip_every and i and i % skip_every == 0
            if skip:
                number += 1          # ⭐ the gap in the sequence: §6.2
            g.append({"number": number, "key": bool(key), "type":
                      0x0301 if key else 0x0302, "codec": 3,
                      "l": 1920, "a": 1080, "byte": byte,
                      "istante_us": int(t_cat * 1000.0),
                      "arrivo_ms": int(round(t_arr))})
            number += 1
            i += 1
            t_arr += step
            t_cat += step - drift_ms_per_frame
    return g


def _with_line(n, loss_pc):
    """Sticks onto a fake run the line `cur_round()` would write for it from the qdisc."""
    n["linea"] = {"loss_pc": loss_pc,
                  "come": "netem with «loss %s%%»" % loss_pc if loss_pc
                          else "netem without `loss`"}
    return n


def certify():
    """⛔ The expectation is written FIRST, and cases 2, 4, 5 and 6 are the ones that
       make a false green credible."""
    print("⭐ CERTIFICATION OF THE RATE BENCH — the expectation is written FIRST\n")
    print("   ⛔ No contact with the test machine: here the "
          "TOOL is tested,\n      not the product.\n")

    SRV = {"delivered": 900, "non_spediti": 0, "sent": 900,
           "abbandonati": 0, "annunci_tela": 0}
    WIRE = {"byte": 90 * 1000 * 1000, "seconds": 30.0, "byte_per_pacchetto": 1452.0}

    cases = []

    # 0 · THE DENOMINATOR.  If this is not green, no red is worth anything.
    g = _fab([(60, 33)], key_every=0)
    cases.append(("0-healthy — 60/s for 33 s, one keyframe only",
                 measure(g, 33, SRV, WIRE),
                 {"the log": True, "no drop": True, "the floor": True,
                  "degrades in time": True, "the delay": True}))
    # 1 · THE BARE DEFECT: the rate below the floor.
    g = _fab([(18, 33)])
    cases.append(("1-⛔ uniform rate 18/s: below the floor of 25",
                 measure(g, 33, SRV, WIRE),
                 {"the log": True, "no drop": True, "the floor": False,
                  "degrades in time": True, "the delay": True}))

    # 2 · ⛔⛔ THE MEAN THAT HIDES THE GAP.
    #     10 s at 45/s + 20 s at 17.5/s = 800 frames in 30 s = **26.7/s**,
    #     that is ABOVE the floor.  A bench that looked at the mean alone
    #     would write «green» on twenty seconds of stuttering desktop.
    #     ⇒ It must give red, and because of the WINDOW.
    g = _fab([(45, 13), (17.5, 20)])
    cases.append(("2-⛔⛔ the mean that hides the gap: 45/s then 17.5/s "
                 "(mean above the floor)",
                 measure(g, 33, SRV, WIRE),
                 {"the log": True, "no drop": True, "the floor": False,
                  "degrades in time": True, "the delay": True}))

    # 3 · ⛔ THE KEYFRAME-ONLY STREAM AT A GOOD RATE.
    #     30/s: the floor is happy.  But they are all keyframes — it is the spiral
    #     of §5.2 measured on 21 August (144/144).  Only §3.3 sees it.
    g = _fab([(30, 33)], key_every=1)
    cases.append(("3-⛔ 30/s but ALL KEYFRAMES: the rate acquits, §3.3 does not",
                 measure(g, 33, SRV, WIRE),
                 {"the log": True, "no drop": True, "the floor": True,
                  "degrades in time": False, "the delay": True}))

    # 4 · ⛔⛔ THE RATE STANDS AND THE DELAY IS DESTROYED.
    #     It is `LEZIONI.md` §6.2 in its nastiest form: 30 frames per
    #     second delivered on time, and each is 4 ms older than the
    #     previous one.  After 30 s delivery is ~3.6 s behind.
    #     ⇒ A bench that counted frames only would give green.
    g = _fab([(30, 33)], drift_ms_per_frame=4.0)
    cases.append(("4-⛔⛔ 30/s on time and the drift running away (+4 ms per "
                 "frame): the rate acquits, the delay does not",
                 measure(g, 33, SRV, WIRE),
                 {"the log": True, "no drop": True, "the floor": True,
                  "degrades in time": True, "the delay": False}))

    # 5 · ⛔ THE DROP HALFWAY.  Twelve seconds of excellent frames out of thirty
    #     requested: every «per second» quantity is good, and the session is
    #     dead.  ⇒ It is the only predicate that holds even below the floor.
    g = _fab([(60, 12)])
    cases.append(("5-⛔ the session dies at 12 s out of 33 requested: all the means "
                 "are good",
                 measure(g, 33, SRV, WIRE),
                 {"the log": True, "no drop": False, "the floor": True,
                  "degrades in time": True, "the delay": True}))

    # 6 · ⛔⛔ THE EMPTINESS.  It is case R7a of the ear judge, carried over: a bench that
    #     answered «zero abandonments, zero keyframes, no violation» on a
    #     run without frames would give **top marks to silence**.
    #     ⇒ Every predicate must REFUSE, except «does not drop», which here is a
    #       true red: nothing arrived.
    cases.append(("6-⛔⛔ the EMPTINESS: zero frames (top marks to silence)",
                 measure([], 33, SRV, WIRE),
                 {"the log": True, "no drop": False, "the floor": None,
                  "degrades in time": None, "the delay": None}))

    # 6b · ⛔⛔ THE ZERO THAT MEANS «I DID NOT READ» — `LEZIONI.md` §1.9, and
    #      cure 2 of 23 August 2026.  If `log_line_list()` returns 0 (the `< file`
    #      that stole the password from `sudo -S`), `server_counts()` would read the
    #      log FROM THE SERVER'S STARTUP: `attese_a_vuoto` would become
    #      cumulative, and with it the column on which `p_I1` decides whether to refuse.
    #      ⇒ The bench must REFUSE, not go straight on.  ⭐ And the refusal is
    #        tested on the REAL function — `server_counts(0)` — not on a dictionary
    #        written by hand: it is the guard on the path the real run takes.
    cases.append(("6b-⛔⛔ the log NOT read (log_line_list() → 0): the server's "
                 "counts would be cumulative from startup",
                 measure(_fab([(30, 33)]), 33, server_counts(0), WIRE),
                 {"the log": None, "no drop": True, "the floor": True,
                  "degrades in time": True, "the delay": True}))

    # 6c · ⛔⛔ THE THIRD FACE OF THE ZERO, and the REAL run of
    #      23 August 2026 found it: the §11.1 reader does not start (it was missing
    #      `01-b4-validatore.py` in the tree), the journal stays empty, and an
    #      empty journal is identical to «the session delivered nothing».
    #      `[M]` that evening the bench gave RED to «does not drop» on a run in
    #      which the server had sent **797** frames and the client had
    #      taken them.  ⇒ «I did not read it» must refuse, not accusations the product.
    #      ⚠ And the comparison with case 6 is the point: **same empty journal**,
    #        opposite outcomes, because the reason for the emptiness is different.
    n_mute = measure([], 33, SRV, WIRE)
    n_mute["traccia_non_letta"] = "⛔ THE §11.1 TRACE WAS NOT READ: test"
    n_mute["outcome"] = "I HAVE NOTHING TO JUDGE — trace not read"
    cases.append(("6c-⛔⛔ the journal empty because I DID NOT READ IT (against "
                 "case 6, empty because nothing arrived)",
                 n_mute,
                 {"the log": True, "no drop": None, "the floor": None,
                  "degrades in time": None, "the delay": None}))

    green = True
    for name, n, expected in cases:
        print("  %s" % name)
        for label, f, _s in ROUND_PREDICATES:
            too_short = label.split(" (")[0]
            key = ("the log" if too_short.startswith("the log") else
                      "no drop" if too_short.startswith("does not drop") else
                      "the floor" if too_short.startswith("the rate floor") else
                      "degrades in time" if too_short.startswith("degrades") else
                      "the delay")
            passes, why = f(n)
            expect = expected[key]
            all_ok = (passes is expect)
            green = green and all_ok
            sign = ("OK " if all_ok else "⛔ ")
            print("      %s%-22s expected %-5s seen %-5s — %s"
                  % (sign, key, expect, passes, why[:96]))
        print()

    # ── THE I1 PAIR, which needs two runs and not one ───────────────────────
    print("  ── I1, and it needs the PAIR: still scene / moving scene ──\n")
    srv = lambda cons, sped, abandoned=0: {"delivered": cons, "sent": sped,
                                     "abbandonati": abandoned, "non_spediti": cons - sped,
                                     "annunci_tela": 0}
    pairs = [
        # 7 · ⭐ I1 HEALTHY: same cadence, no abandonments.
        ("7-⭐ I1 healthy: still 30/s and moving 30/s, delivered comparable",
         measure(_fab([(30, 33)]), 33, srv(1000, 1000), WIRE),
         measure(_fab([(30, 33)]), 33, srv(1010, 1010), WIRE),
         True),
        # 8 · ⛔ THE DEFECT THE PHASE EXISTS TO FIND: with the scene still the
        #     rate drops, and the compositor delivered to us all the same.
        ("8-⛔⛔ I1 broken: still 18/s against moving 30/s, delivered equal",
         measure(_fab([(18, 33)]), 33, srv(1000, 620, 40), WIRE),
         measure(_fab([(30, 33)]), 33, srv(1010, 1010), WIRE),
         False),
        # 9 · ⭐⭐ THE FALSE RED, and it is the case without which this bench
        #     would accusations the product of a defect of the COMPOSITOR.  Same
        #     rates as case 8 — but with the scene still Mutter delivered 550
        #     frames against 1 010.  ⇒ I DO NOT JUDGE, and not «red».
        ("9-⭐⭐ the false red: same rates, but with the scene still the compositor "
         "delivered 550 against 1 010",
         measure(_fab([(18, 33)]), 33, srv(550, 550), WIRE),
         measure(_fab([(30, 33)]), 33, srv(1010, 1010), WIRE),
         None),
        # 10 · ⛔ THE MUTE PAIR: one of the two runs did not measure.
        ("10-⛔ the incomplete pair: the still-scene run has no frames",
         measure([], 33, srv(1000, 1000), WIRE),
         measure(_fab([(30, 33)]), 33, srv(1010, 1010), WIRE),
         None),
        # 10b · ⭐⭐ THE SECOND FALSE RED, and this time the «delivered»
        #      look alike — the first guard would let it through.  What says so is
        #      the column the child writes by itself: **900 empty waits**
        #      with the scene still against 3 with the scene moving.  ⇒ I DO NOT JUDGE.
        ("10b-⭐⭐ the false red the «delivered» do not see: 900 EMPTY "
         "waits with the scene still (the frame was not there)",
         measure(_fab([(18, 33)]), 33,
                dict(srv(950, 950), capture={"catturati": 950, "keys": 1,
                                             "attese_a_vuoto": 900}), WIRE),
         measure(_fab([(30, 33)]), 33,
                dict(srv(1010, 1010), capture={"catturati": 1010, "keys": 1,
                                               "attese_a_vuoto": 3}), WIRE),
         None),
        # ══ CURE 3, and they are FOUR cases because a conditioned leg is
        #    tested in both directions: it must keep quiet where the premise is missing, and
        #    it must be able to GIVE RED where the premise holds.
        #
        # 10c · ⛔ THE LEG THAT MUST BITE.  Line WITHOUT loss, the rate with the
        #      scene still stands (in fact it runs faster), and the server throws away
        #      all the same: it is I1 broken in the form frames/s do not see.
        ("10c-⛔ line WITHOUT loss and the server throws away with the scene still: the "
         "abandonment leg must give RED",
         _with_line(measure(_fab([(10.13, 33)]), 33, srv(1000, 960, 40), WIRE), 0.0),
         _with_line(measure(_fab([(7.78, 33)]), 33, srv(1010, 1010), WIRE), 0.0),
         False),
        # 10d · ⭐⭐ THE CASE MEASURED ON 23 AUGUST 2026 on `bad-home` (2 %
        #      loss): **the very same numbers** as 10c.  The premise
        #      *«with a still scene there is no congestion that justifies them»* here is
        #      FALSE — the abandonments are justified by the loss.  ⇒ I DO NOT JUDGE.
        #      ⛔ And the red this case removes is not a red of the product.
        ("10d-⭐⭐ the SAME numbers on a line that loses 2 %: the premise "
         "is false and the bench must REFUSE, not give red",
         _with_line(measure(_fab([(10.13, 33)]), 33, srv(1000, 960, 40), WIRE), 2.0),
         _with_line(measure(_fab([(7.78, 33)]), 33, srv(1010, 1010), WIRE), 2.0),
         None),
        # 10e · ⛔ And «I do not know whether it loses» is NOT «it does not lose»: an
        #      unverified premise does not give the right to give red (§1.9, again).
        ("10e-⛔ the same numbers on a line of which I do NOT KNOW whether it loses: "
         "an unverified premise does not authorise a red",
         measure(_fab([(10.13, 33)]), 33, srv(1000, 960, 40), WIRE),
         measure(_fab([(7.78, 33)]), 33, srv(1010, 1010), WIRE),
         None),
        # 10f · ⛔⛔ AND THE CURE MUST NOT BECOME AN AMNESTY.  Line losing
        #      2 %, but this time the rate with the scene still DROPS (5.0/s against 7.78):
        #      loss explains the abandonments, it does not explain that.  ⇒ RED.
        ("10f-⛔⛔ line losing 2 % BUT the rate with the scene still drops "
         "(5.00/s against 7.78/s): loss does not justify it — RED",
         _with_line(measure(_fab([(5.0, 33)]), 33, srv(1000, 960, 40), WIRE), 2.0),
         _with_line(measure(_fab([(7.78, 33)]), 33, srv(1010, 1010), WIRE), 2.0),
         False),
    ]
    for name, halt, move, expect in pairs:
        passes, why = p_I1(halt, move)
        all_ok = (passes is expect)
        green = green and all_ok
        print("  %s%s\n      expected %-5s seen %-5s — %s"
              % ("OK  " if all_ok else "⛔  ", name, expect, passes, why[:150]))
    print()

    # 11 · ⛔ THE WIRE NOT READ — `CODER.md` §3.10.  If the qdisc counter
    #      could not be read, the bench must say «not read», not «0».
    n = measure(_fab([(30, 33)]), 33, SRV, None)
    all_ok = (n.get("mbit_s_filo") is None and "filo_non_letto" in n)
    green = green and all_ok
    print("  %s11-⛔ the wire counter not read: it says «not read», not "
          "«0 Mbit/s» — seen mbit_s_filo=%s"
          % ("OK  " if all_ok else "⛔  ", n.get("mbit_s_filo")))

    # 12 · ⭐ THE SECOND LEG OF THE ABANDONMENTS: the gaps in `number`, which are
    #      read from the RECEIVING side and do not go through the server's log.
    n = measure(_fab([(30, 33)], skip_every=25), 33, SRV, WIRE)
    expected_holes = (n["frames"] // 25)
    all_ok = n["buchi_numero"] >= expected_holes - 2
    green = green and all_ok
    print("  %s12-⭐ the gaps in the `number` sequence (§6.2): expected ~%d, "
          "seen %d" % ("OK  " if all_ok else "⛔  ", expected_holes, n["buchi_numero"]))

    # 13 · ⭐⭐ THE WHOLE LOOP OF THE TOOL: from the trace to the journal.
    #      Cases 0-12 test the REDUCTION on ready-made journals; this one tests
    #      the piece that builds them — the §11.1 reader — and tests it **on the
    #      code that will be sent to the machine**, not on a copy.
    #      ⛔ And the format of the fake trace is not written by me: I take it
    #        from the REFEREE (`01-b4-validatore.py`), which is the only place where
    #        §11.1 is written.  A test in which I write and reread MY format
    #        would prove nothing about the real format.
    all_ok, why = _certify_reader()
    green = green and all_ok
    print("  %s13-⭐⭐ from the §11.1 TRACE to the journal, with the real reader: %s"
          % ("OK  " if all_ok else "⛔  ", why))

    # 14-15 · ⛔⛔ THE TWO CURES OF `sudo -S`'s STDIN, tested FOR REAL.
    green = _certify_sudo_stdin() and green

    print("\n== %s" % ("⭐ THE BENCH CAN SEE THE DEFECTS IT LOOKS FOR"
                       if green else
                       "⛔⛔ THE BENCH CANNOT SEE WHAT IT LOOKS FOR: none of "
                       "its greens is to be believed"))
    return 0 if green else 1


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE TEST OF CURES 1 AND 2 — and it is NOT a string comparison
# ═══════════════════════════════════════════════════════════════════════════
#
# A bench that merely compared the built line with an expected line
# would prove that I write it as I thought it, not that it WORKS.  ⇒ Here the chain
# is actually run, locally, with a **fake** `sudo` that behaves
# like the real one in the only thing that matters: it reads the password from **stdin** and
# then runs what is left.  If the password does not reach it, it fails
# exactly as on the test machine — *«3 incorrect password attempts»*.
#
# ⭐ And every cure is tested in TWO directions: the old form must FAIL (a cure
#    that has never been seen failing is not tested) and the new one must hold.
FAKE_SUDO = r'''#!/bin/sh
# ⛔ The fake `sudo`: it gives no privileges, it imitates only the stdin of `-S`.
while [ "$1" = "-S" ] || [ "$1" = "-p" ]; do
  if [ "$1" = "-p" ]; then shift 2; else shift; fi
done
printf '%s\n' "$*" >> "$FAKE_CALLS"
IFS= read -r parola || parola=""
if [ "$parola" != "$FAKE_PASSWORD" ]; then
  echo "sudo: 3 incorrect password attempts" >&2
  exit 1
fi
exec "$@"
'''


def _certify_sudo_stdin():
    """Cases 14 and 15: the two forms in which `sudo -S` loses the password."""
    import shutil, tempfile
    d = tempfile.mkdtemp(prefix="09-b70-sudo-")
    bucket = os.path.join(d, "bucket")
    os.makedirs(bucket)
    with open(os.path.join(bucket, "sudo"), "w") as f:
        f.write(FAKE_SUDO)
    os.chmod(os.path.join(bucket, "sudo"), 0o755)
    calls = os.path.join(d, "calls")

    def runs(line):
        open(calls, "w").close()
        env = dict(os.environ, PATH=bucket + ":" + os.environ.get("PATH", ""),
                   FAKE_CALLS=calls, FAKE_PASSWORD=SUDO_PASSWORD)
        p = subprocess.run(["bash", "-c", line], capture_output=True, env=env)
        return (p.returncode, p.stdout.decode("utf-8", "replace"),
                open(calls).read().strip().splitlines())

    def old(command):
        """The form of `07-b65-datagram.py:147`: a single `sudo`, and the chain OUTSIDE."""
        return "printf '%%s\\n' '%s' | sudo -S -p '' %s" % (SUDO_PASSWORD, command)

    green = True

    # ── 14 · THE CHAIN — `sudo` covers only the FIRST link ──────────────────
    inside = os.path.join(d, "inside")
    chain = ("mkdir -p %s && printf '%%s' 'CIAO' > %s/f && wc -c < %s/f"
              % (inside, inside, inside))
    _rc, out_v, ch_v = runs(old(chain))
    shutil.rmtree(inside, ignore_errors=True)
    _rc, out_n, ch_n = runs(chain_root(chain))
    # ⛔ The old form: `sudo` received ONLY the `mkdir`; the `printf`, the
    #    `>` and the `wc` ran as a normal user — and on the machine, where
    #    `WORKDIR` belongs to root, that is where the §11.1 reader was not written.
    broken = (len(ch_v) == 1 and "mkdir" in ch_v[0] and "printf" not in ch_v[0])
    # ⭐ The new form: a single `sudo`, and the WHOLE chain inside its shell.
    cured = (len(ch_n) == 1 and ch_n[0].startswith("bash -c ")
              and "mkdir" in ch_n[0] and "printf" in ch_n[0] and "wc" in ch_n[0]
              and out_n.strip() == "4")
    all_ok = broken and cured
    green = green and all_ok
    print("  %s14-⛔ CURE 1 · the CHAIN: the old form sends to root only "
          "«%s…» (the rest runs as user); the new one sends a single one, with "
          "the whole chain inside — and prints «%s» (expected «4»)"
          % ("OK  " if all_ok else "⛔  ",
             (ch_v[0] if ch_v else "(nothing)")[:24], out_n.strip()))

    # ── 15 · THE TRAILING `< file` — it steals stdin from `sudo`, and KEEPS QUIET ─
    reg = os.path.join(d, "registro.log")
    with open(reg, "w") as f:
        f.write("prima riga\nseconda\nterza\nquarta\n")
    command = "wc -l < %s 2>/dev/null || echo 0" % reg
    rc_v, out_v, _ch = runs(old(command))
    rc_n, out_n, _ch = runs(chain_root(command))
    # ⛔⛔ The old form prints «0» — not «error»: it is the MUTE defect, and it is
    #     the one that made `attese_a_vuoto` cumulative from startup.
    broken = (out_v.strip() == "0")
    cured = (out_n.strip() == "4")
    all_ok = broken and cured
    green = green and all_ok
    print("  %s15-⛔⛔ CURE 2 · the trailing «< file» on a 4-line log: "
          "the old form answers «%s» (stdin stolen from sudo, and it KEEPS QUIET), the "
          "new one «%s»"
          % ("OK  " if all_ok else "⛔  ", out_v.strip(), out_n.strip()))

    # ── 15b · THE GUARD: a zero must not have the face of a measurement ─────
    real_root = globals()["root"]
    try:
        prove = [
            ("zero lines with the server on", (0, "0\n", ""), None),
            ("sudo refusing the password", (1, "", "sudo: 3 incorrect password "
                                                   "attempts"), None),
            ("an answer that is not a number", (0, "boh\n", ""), None),
            ("a real log of 12 345 lines", (0, "12345\n", ""), 12345),
        ]
        outcomes = []
        for label, response, expected in prove:
            globals()["root"] = lambda c, cap=300, r=response: r
            seen = log_line_list()
            outcomes.append((label, expected, seen, seen == expected))
    finally:
        globals()["root"] = real_root
    all_ok = all(e[3] for e in outcomes)
    green = green and all_ok
    print("  %s15b-⭐ the guard of `log_line_list()`: %s"
          % ("OK  " if all_ok else "⛔  ",
             " · ".join("%s → %s%s" % (e[0], e[2], "" if e[3] else
                                       " ⛔ EXPECTED %s" % e[1]) for e in outcomes)))
    shutil.rmtree(d, ignore_errors=True)
    return green


def _certify_reader():
    """⛔ The fake trace is built with THE REFEREE's constants, and carries
       inside on purpose the three things a naive reader trips over:

         · a frame split into **several blocks** (and the 28-byte header
           across two of them);
         · a block with a **redacted** interval (§11.1 allows it, and they are
           40 bytes in the middle of the file that must be skipped or everything shifts);
         · a stream closed with **RESET_STREAM**, which is form A
           of the abandonment of §5.1 and is **not** a delivered frame.

       ⚠ And there is also a block of the control channel and one from the CLIENT, which
         must not end up in the video journal.
    """
    import hashlib, tempfile
    try:
        spec = importlib.util.spec_from_file_location(
            "b4cert", os.path.join(HERE, "01-b4-validatore.py"))
        A = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(A)
    except Exception as e:
        return False, "the §11.1 referee could not be imported: %s" % e

    blocks = []      # (direction, channel, end, instant, stream, payload, redacted)

    def head(number, key, instant_us):
        return struct.pack("!HHIIIQI", 0x0301 if key else 0x0302, 3,
                           1920, 1080, number, instant_us, 0)

    # noise that is NOT video: control channel, and a block from the client
    blocks.append((A.CLIENT, 0x00, A.CONTINUE, 0, 0, b"\x00" * 12, []))
    blocks.append((A.SERVER, 0x00, A.CONTINUE, 1, 0, b"\x00" * 12, []))

    expected = []
    stream, instant_ms = 4, 10
    for k in range(6):
        key = (k == 0)
        cat = k * 33000                       # µs, the server's clock
        t = head(k + 1, key, cat)
        if k == 3:
            # ⛔ ABANDONED (§5.1 form A): it is not a delivered frame.
            blocks.append((A.SERVER, 0x03, A.CONTINUE, instant_ms, stream,
                            t + b"\x11" * 50, []))
            blocks.append((A.SERVER, 0x03, A.RESET, instant_ms + 1, stream,
                            b"", []))
        else:
            # ⭐ the header across TWO blocks
            blocks.append((A.SERVER, 0x03, A.CONTINUE, instant_ms, stream,
                            t[:12], []))
            body = b"\x22" * 500
            osc = []
            if k == 2:
                # a redacted interval: 40 bytes in the middle of the file
                osc = [(0, 8, hashlib.sha256(b"\x22" * 8).digest())]
            blocks.append((A.SERVER, 0x03, A.CONTINUE, instant_ms, stream,
                            t[12:] + body[:200], osc))
            blocks.append((A.SERVER, 0x03, A.FIN, instant_ms + 2, stream,
                            body[200:], []))
            expected.append({"number": k + 1, "key": key,
                           "byte": 500, "arrivo_ms": instant_ms + 2,
                           "istante_us": cat})
        stream += 4
        instant_ms += 33

    out = bytearray(A.MAGIC + struct.pack("!IBBBB", len(blocks), 1, 0, 0, 0))
    for which_way, channel, fine, ist, sid, load, osc in blocks:
        out += struct.pack(A.BLOCK, which_way, channel, fine, ist, sid,
                           len(load), len(osc))
        for ini, here, imp in osc:
            out += struct.pack("!II", ini, here) + imp
        out += load

    d = tempfile.mkdtemp(prefix="09-b70-")
    tr, le = os.path.join(d, "t.rcpreg"), os.path.join(d, "leggi.py")
    with open(tr, "wb") as f:
        f.write(bytes(out))
    with open(le, "w") as f:
        f.write(READER)
    p = subprocess.run([sys.executable, le, tr,
                        os.path.join(HERE, "01-b4-validatore.py")],
                       capture_output=True)
    import shutil
    shutil.rmtree(d, ignore_errors=True)
    try:
        read = json.loads(p.stdout.decode())
    except Exception as e:
        return False, "the reader did not answer: %s — %s" % (
            e, (p.stdout + p.stderr).decode("utf-8", "replace")[-200:])
    g = read.get("giornale") or []
    if read.get("zeroed") != 1:
        return False, ("the abandonment with RESET_STREAM was not counted "
                       "apart: zeroed = %s" % read.get("zeroed"))
    if len(g) != len(expected):
        return False, ("%d frames in the journal, I expected %d "
                       "(the RESET is not a delivered frame)"
                       % (len(g), len(expected)))
    for seen, expect in zip(g, expected):
        for key, value in expect.items():
            if seen.get(key) != value:
                return False, ("frame %s: «%s» is %s, I expected %s"
                               % (expect["number"], key, seen.get(key), value))
    # ⭐ And the tail of the run: five frames are FEW, and the reduction must
    #    SAY so instead of computing a rate on a handful of samples.
    n = measure(g, 1, None, None, warmup_s=0.0)
    if n.get("outcome") == "measured":
        return False, ("the reduction measured a rate on %d frames, "
                       "below the minimum of %d: it should have refused"
                       % (len(g), MIN_FRAMES))
    return True, ("%d frames read (1 keyframe, %d deltas), 1 abandonment with "
                  "RESET counted apart, redacted and non-video blocks skipped; "
                  "and the reduction refuses to compute a rate with so few"
                  % (len(g), len(expected) - 1))


# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT TALKS TO THE TEST MACHINE
# ═══════════════════════════════════════════════════════════════════════════
NETWORK = None       # the 07-b65 module, imported in `main()`


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔⛔ THE TRAP OF `sudo -S`'s STDIN, AND THIS PROJECT HAS ALREADY PAID FOR IT
#       THREE TIMES — it is written here so the fourth is not paid
# ═══════════════════════════════════════════════════════════════════════════
#
# `07-b65-datagram.py:147` builds, and it is perfectly fine for ONE command only:
#
#       printf '%s\n' 'PASSWORD' | sudo -S -p '' <command>
#
# ⛔ **FIRST FORM — the chain.**  The command that arrives in there is not a
#    command: it is a CHAIN (`a && b | c > d`).  The remote shell splits it
#    **outside** `sudo`, and `sudo` covers only the FIRST link.  The following
#    links run as a normal user — and if they write in `WORKDIR`, which belongs to
#    root, they fail.  ⚠ And they fail **in silence**, because the `|| echo 0`
#    or the `; true` that goes with them turns the error into a plausible number.
#    `[M]` 23 August 2026: `ship_reader()` did not write `09-b70-leggi.py`
#    on the machine, and §11.1 stayed without a reader.
#
# ⛔⛔ **SECOND FORM — and the worst, because it is MUTE.**  A trailing `< file`
#      is not taken by the command: it is taken by **`sudo`**, which is the last command
#      of the pipeline.  ⇒ The password no longer reaches `sudo`'s stdin,
#      the file does; `sudo` answers *«3 incorrect password attempts»* on
#      stderr, exits 1, and the trailing `|| echo 0` prints **0**.
#      ⚠ It is written in black and white in `07-b64-terreno.sh` (~line 240) — *«no
#        trailing `</dev/null`: that redirect wins over `sudo -S`»* — and it came back
#        here all the same: `[M]` 23 August 2026, `log_line_list()` returned **0** on
#        a log of thousands of lines, and then `server_counts()` read
#        **from the server's startup** instead of from this run.  The «final
#        count» lines were saved (there is a `tail -1`), the `cycle:` lines were not:
#        `catturati` and **`waits a empty`** became CUMULATIVE — that is the
#        column on which `p_I1` decides whether to refuse to judge.
#
# ⇒ **THE CURE, and it is a single one for both**: a single `sudo`, and the whole
#   chain inside ITS shell.  `sudo` stays the only command of the `printf`
#   pipeline, so the password reaches it; and every `|`, `&&`, `<` and `>` of the
#   chain lives inside `bash -c`, that is inside root.
#
#       printf '%s\n' 'PASSWORD' | sudo -S -p '' bash -c '<whole chain>'
#
# ⚠ And the price is declared: inside the single quotes of `shlex.quote` the `$`
#   is NO longer expanded by the remote shell.  No command in this file
#   relies on that expansion, and whoever added one must know it.
def chain_root(command):
    """The line that leaves over ssh: **one** `sudo`, and the chain inside its shell."""
    return ("printf '%%s\\n' '%s' | sudo -S -p '' bash -c %s"
            % (SUDO_PASSWORD, shlex.quote(command)))


def root(command, cap=300):
    """⛔ It is NOT `NETWORK.root`: that one covers only the first link of the chain.

    ⚠ And whoever replaces this function from outside to transcribe (as
      `09-b79-cure.py:415` does) must wrap **this one**, not `NETWORK.root`, or
      both the defects cured above come back in.
    """
    return NETWORK.rem(chain_root(command), cap)


def ship_reader():
    """⛔ The reader is sent in base64: the quotes of a heredoc inside
       a `sudo -S` inside an `ssh` are three levels of quoting, and a wrong one
       does not give an error — it gives a truncated file.

    ⛔⛔ And the chain is ONE SINGLE call to `root()`: `mkdir`, `printf`,
        `base64 -d` and the `>` all live inside the same root shell (see
        the trap written above).  `[M]` 23 Aug 2026: in the old form
        the `>` belonged to the user's shell and the file was never written.
    """
    b = base64.b64encode(READER.encode("utf-8")).decode("ascii")
    root("mkdir -p %s && printf '%%s' '%s' | base64 -d > %s/09-b70-leggi.py"
         % (WORKDIR, b, WORKDIR))
    # ⛔ `wc -c < file` is fine ONLY because the redirect is now inside the
    #    root shell: it is root that opens the file, and `sudo`'s stdin stays the
    #    password.  In the old form this `<` stole the password and the bench
    #    said «it was not written» of a file that was there (2 198 bytes measured).
    rc, out, _ = root("wc -c < %s/09-b70-leggi.py" % WORKDIR)
    return out.strip().isdigit() and int(out.strip()) > 1000


def terrain_check():
    """⛔ The bench refuses to measure on a ground that is not its own.

    ⚠ And it counts the listeners NOT its own without touching them: `LEZIONI.md` §1.26 —
      two benches on the same machine do not give a red, they give **a plausible
      number**.
    """
    _log("THE GROUND — port %d · user %s (uid %d) · tree %s"
         % (PORT, ACCOUNT, UID_B, TREE_DIR))
    troubles = []
    rc, out, _ = root("id %s >/dev/null 2>&1 && echo si || echo no" % ACCOUNT)
    if "yes" not in out:
        troubles.append("the user «%s» does not exist: "
                    "PORT=%d ACCOUNT=%s UID_B=%d TREE=%s WORKDIR=%s "
                    "bash banchi/07-b64-terreno.sh user"
                    % (ACCOUNT, PORT, ACCOUNT, UID_B, TREE_DIR, WORKDIR))
    rc, out, _ = root("test -s %s/parola && echo si || echo no" % WORKDIR)
    if "yes" not in out:
        troubles.append("%s/parola (0600) is missing: D12 forbids the password in argv" % WORKDIR)
    rc, out, _ = root("test -d %s/banchi && echo si || echo no" % TREE_DIR)
    if "yes" not in out:
        troubles.append("the tree «%s» is not there: it is aligned with "
                    "banchi/attrezzi-allinea-innesto.sh" % TREE_DIR)
    # ⛔⛔ THE §11.1 REFEREE, and it is checked BEFORE measuring.  `[M]` 23 August
    #     2026: `07-b64-terreno.sh ship` carries only a handful of `banchi/`, and
    #     `01-b4-validatore.py` was not among them — the trace reader
    #     died at every run, the journal stayed empty, and the bench gave RED to
    #     «does not drop» on a session alive with 797 frames.  ⇒ A missing file
    #     is said here, where it costs one line, not when the run is over.
    rc, out, _ = root("test -s %s/banchi/01-b4-validatore.py && echo si || echo no"
                      % TREE_DIR)
    if "yes" not in out:
        troubles.append("the §11.1 referee «%s/banchi/01-b4-validatore.py» is missing: "
                    "without it, the trace reader does not start and every run "
                    "looks like a dead session — copy it with "
                    "«scp banchi/01-b4-validatore.py» into the tree" % TREE_DIR)
    rc, out, _ = root("test -x %s && echo si || echo no" % SCENE_BIN)
    if "yes" not in out:
        troubles.append("the scene «%s» is not executable: 04-b30-scena must be "
                    "built" % SCENE_BIN)
    rc, out, _ = root("ss -tuln 2>/dev/null | grep -c ':%d ' || true" % PORT)
    my = out.strip()
    rc, out, _ = root("uptime")
    _inf("load: %s" % out.strip()[-40:])
    tally = []
    for p in NEARBY_PORTS:
        rc, o, _ = root("ss -tuln 2>/dev/null | grep -c ':%s ' || true" % p)
        tally.append("%s:%s" % (p, o.strip()))
    _inf("listeners NOT mine (counted, not touched): %s" % " ".join(tally))
    _inf("my server on %d: %s listener(s)" % (PORT, my))
    if my == "0":
        troubles.append("nobody is listening on %d: "
                    "PORT=%d ACCOUNT=%s UID_B=%d TREE=%s WORKDIR=%s "
                    "bash banchi/07-b64-terreno.sh start" % (PORT, PORT, ACCOUNT,
                                                               UID_B, TREE_DIR, WORKDIR))
    if not ship_reader():
        troubles.append("the trace reader was not written in %s" % WORKDIR)
    for g in troubles:
        _ko(g)
    if not troubles:
        _ok("the ground is there, and it is mine")
    return not troubles


def log_line_list():
    """How many lines the server log has NOW — or `None` if I did not read it.

    ⛔⛔ **A ZERO THAT MEANS «I DID NOT READ» AND A ZERO THAT MEANS «NOTHING
        HAPPENED» MUST NOT HAVE THE SAME FACE** (`LEZIONI.md` §1.9).
        Here the face was the same and the price was the one written above
        `chain_root()`: the number came back 0, `server_counts()` read the
        log **from the server's startup**, and `attese_a_vuoto` — the column
        with which `p_I1` decides whether to refuse — became cumulative.

    ⇒ Three outcomes, not two:
        · an integer > 0  — I read it;
        · `None`         — ⛔ I DID NOT READ IT (the command failed, or the
          answer is not a number);
        · `None` also at **zero lines**: the server is on (`terrain_check()`
          checks it before measuring) and a server that is on has necessarily already
          written.  A zero, here, is a failed read disguised as a measurement.

    ⚠ And no trailing `|| echo 0`: that fallback is precisely the piece that
      turned the error into a plausible number.  If it fails, it must show.
    """
    rc, out, err = root("wc -l < %s/registro.log" % WORKDIR)
    t = out.strip()
    if rc != 0 or not t.isdigit():
        _dub("⛔ the server log was NOT read (rc=%s): «%s»"
             % (rc, (t + " " + err.strip())[:120]))
        return None
    n = int(t)
    if n <= 0:
        _dub("⛔ the server log has ZERO lines with the server on: it is "
             "a failed read, not a measurement — I do NOT take it as good")
        return None
    return n


def server_counts(line0):
    """⛔ The client can say how many frames it TOOK; it cannot say how many
       left.  Without these numbers «the network threw it away» and «the server never
       sent it» would give the same count — and in a bench that throttles the
       network on purpose it is the distinction that matters more than any other (R13).

    ⛔⛔ AND THE FIRST THING IT DOES IS REFUSE, if `riga0` is not a good number.
        With `riga0` missing the `tail -n +1` would read the **whole** log:
        the «final count» lines would be saved (there is a `tail -1`), the `ciclo:` lines
        would not, and `catturati`/`attese_a_vuoto` would become cumulative
        from the server's startup.  ⇒ True numbers given to the wrong run, which
        is the wound of `LEZIONI.md` §1.26 in its most invisible form.
        ⚠ The guard sits HERE, at the point where the number is CONSUMED, and not inside
          `log_line_list()`: so it holds even when someone else replaces
          that function with one that returns 0 instead of `None`
          (`09-b76-rete-cattiva.py:1126` does).
    """
    if line0 is None or line0 <= 0:
        return {"registro_non_letto":
                "⛔ the server log was not read (starting line "
                "«%s»): without the starting line the counts would be CUMULATIVE "
                "from startup, not of this run" % line0}
    # ⚠ Since 23 August 2026 the server also writes a `quic-net …
    #   judgement=…` line once per second (`src/webtransport.c:3986`).  ⭐ It does not
    #   confuse any of the `grep`s below — it carries no «final count», nor
    #   «child  loop:», nor the four sentences of the spiral — and since the
    #   start is a LINE NUMBER, new lines in the log move
    #   nothing.  Whoever adds a `grep` here must check again.
    report = {"line0": line0}
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -a 'video of .*final "
                      "count' | tail -1" % (line0 + 1, WORKDIR))
    m = re.search(r"(\d+) frames delivered.*?(\d+) NOT SENT.*?"
                  r"(\d+) sent on the wire.*?(\d+) abandoned.*?and (\d+) ANNOUNCEMENTS",
                  out.strip())
    if m:
        report.update({"delivered": int(m.group(1)), "non_spediti": int(m.group(2)),
                      "sent": int(m.group(3)), "abbandonati": int(m.group(4)),
                      "annunci_tela": int(m.group(5))})
    else:
        # ⛔ `CODER.md` §3.10: «I did not read» is not «zero».
        report["esito_video"] = "NOTHING TO READ — no video «final count»"
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -a 'audio of .*final "
                      "count' | tail -1" % (line0 + 1, WORKDIR))
    m = re.search(r"(\d+) blocks sent, (\d+) dropped.*?(\d+) refused.*?"
                  r"(\d+) DEFERRED", out.strip())
    if m:
        # ⚠ They are read and printed, but NOT judged: the sound judge
        #   is `07-b64-orecchio.py`, and the question «who pays between audio and video»
        #   is already closed by `07-b65`.
        report["audio"] = {"sent": int(m.group(1)), "buttati": int(m.group(2)),
                          "refused": int(m.group(3)), "rimandati": int(m.group(4))}
    # ⭐⭐ AND THE CAPTURE SIDE, which is the column WITHOUT WHICH I1 CANNOT BE JUDGED.
    #
    # ⛔ The child's `loop:` line (`figlio.c:6842`) carries, cumulative and once
    #    per second, «N frames delivered (K keyframes), M **empty
    #    waits**» — and the product itself explains what it means: *«still
    #    scene: Mutter delivers only when something changes»*.
    #
    # ⭐ This column was taught to me by `banchi/09-b68-ritmo.py`, by another
    #    agent, on 23 August: it is a **better** discriminator than the
    #    `shipped/delivered` ratio I had written first, because it does not deduce —
    #    it says that we ASKED for a frame and there was none.  ⇒ «Mutter
    #    does not deliver» and «we were not lowering the rate» stop having the same
    #    look, which is exactly the trap of `04-b32-ritmo.py`.
    r = re.compile(r"loop: (\d+) frames delivered \((\d+) keyframes\), "
                   r"(\d+) empty waits")
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -a 'child  loop:'"
                      % (line0 + 1, WORKDIR))
    lines = r.findall(out)
    if len(lines) >= 2:
        p0, p1 = lines[0], lines[-1]
        report["capture"] = {"catturati": int(p1[0]) - int(p0[0]),
                            "keys": int(p1[1]) - int(p0[1]),
                            "attese_a_vuoto": int(p1[2]) - int(p0[2]),
                            "righe_ciclo": len(lines)}
    else:
        report["capture"] = {"outcome": "NOTHING TO READ — fewer than two "
                                     "«loop:» lines in this run"}
    # ⭐ AND THE LINES OF THE SPIRAL, counted: they are the bridge between the numbers of this
    #    page and the cause named in `fasi/09...` §0.3.
    for label, aco in (
            ("chiave_aspetta", "§5.2 forbids abandoning it"),
            ("delta_non_spedito", "FRAME NOT SENT"),
            ("abbandonato_in_coda", "ABANDONED IN THE QUEUE"),
            ("involo_pieno", "can NOT be abandoned")):
        rc, out, _ = root("tail -n +%d %s/registro.log | grep -ac '%s' || true"
                          % (line0 + 1, WORKDIR, aco))
        report.setdefault("spirale", {})[label] = (
            int(out.strip()) if out.strip().isdigit() else None)
    return report


def scene_turn_on(motion):
    """⭐ «Still scene» = `--movimento marca`, NOT the scene off.

    ⛔ With the scene off the compositor delivers very little, and the two runs of the
       pair are not comparable: a low rate upstream looks in every way like
       a rate lowered by us.  With `marca` only the mark changes — the capture
       cadence stays that of the moving run, and what changes is the COST, which is
       the only thing I1 wants to isolate.
    """
    scene_turn_off()
    rc, out, _ = root("grep -ao 'monitor «[^»]*»' %s/registro.log | tail -1" % WORKDIR)
    m = re.findall("monitor «([^»]*)»", out)
    usc = m[-1] if m and m[-1] else None
    if not usc:
        return None
    root("setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
         "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
         "XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 "
         "%s --uscita %s --movimento %s --shm /09-b70 --giro b70 "
         ">/dev/null 2>&1 & echo acceso"
         % (UID_B, UID_B, ACCOUNT, ACCOUNT, UID_B, SCENE_BIN, usc, motion))
    time.sleep(1.5)
    rc, out, _ = root("pgrep -u %d -f '04-b30-scena --uscita' | head -1" % UID_B)
    return usc if out.strip() else None


def scene_turn_off():
    root("pkill -u %d -f 04-b30-scena; true" % UID_B)


def trigger_session(seconds=8):
    """⛔ The stage and the monitor are born with the FIRST client: on a freshly
       started server the log does not yet carry the monitor name, and the scene would not
       know where to draw.  ⇒ A short session is opened on purpose; the stage
       outlives it (I4)."""
    inside = ("python3 -u %s/banchi/01-b3-cliente.py --address %s --port %d "
              "--user %s --password-file %s/parola --audio-codec pcm "
              "--video-codec %s --fit %s --stay %d"
              % (INSIDE_TREE, ADDR, PORT, ACCOUNT, INSIDE_WORK, REQUESTED_CODEC,
                 FULL_CANVAS, seconds))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % inside,
                        seconds + 180)
    return "SESSION" in (out + err)


def _round_line():
    """⭐ The loss of the line is READ from the installed qdisc, not assumed.

    ⛔ Assuming it would be worse than the defect it cures: `09-b76-rete-cattiva.py`
       calls this same `cur_round()` with a `netem` that **loses**, and a
       «loss 0» written by hand here would put back on its feet exactly the false
       red of `p_I1` that is being removed.  ⇒ We look at what is really there.

    ⚠ And if the qdisc cannot be read, `None` is written — which means «I do not know»,
      and `p_I1` then refuses instead of giving red.
    """
    try:
        text = NETWORK.qdisc() or ""
    except Exception as e:
        return {"loss_pc": None, "come": "the qdisc was not read: %s" % e}
    if "netem" not in text:
        return {"loss_pc": None, "come": "no netem on the device: the "
                                            "line is not the one I think",
                "qdisc": text[:200]}
    # `loss 1%` (independent) or `loss gemodel p 0.2% r 20% …` (bursty)
    m = re.search(r"loss\s+(?:gemodel\s+p\s+)?([\d.]+)%", text)
    return {"loss_pc": float(m.group(1)) if m else 0.0,
            "come": ("netem with «%s»" % m.group(0)) if m else
                    "netem without `loss`: the only possible loss is the queue "
                    "overflowing",
            "qdisc": text[:200]}


def cur_round(name, motion, canvas, seconds, with_trace=True):
    """One run: the client inside the container, the trace reduced on the spot."""
    root("rm -f %s/%s.rcpreg %s/%s.json; true" % (WORKDIR, name, WORKDIR, name))
    # ⛔ `None` (or 0) here means «I did not read the log», and from then on
    #    the server's counts would be cumulative from startup: the guard sits
    #    inside `server_counts()`, which refuses instead of reading everything.
    line0 = log_line_list()
    text_line = _round_line()
    before = NETWORK.byte_on_wire()
    t0 = time.time()
    inside = ("python3 -u %s/banchi/01-b3-cliente.py --address %s --port %d "
              "--user %s --password-file %s/parola --audio-codec pcm "
              "--video-codec %s --fit %s %s--resta %d"
              % (INSIDE_TREE, ADDR, PORT, ACCOUNT, INSIDE_WORK, REQUESTED_CODEC, canvas,
                 ("--record %s/%s.rcpreg " % (INSIDE_WORK, name)) if with_trace else "",
                 seconds))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % inside,
                        seconds + 300)
    after = NETWORK.byte_on_wire()
    real = time.time() - t0
    text = out + err
    # ⭐ The count the CLIENT prints by itself, which is independent of the
    #    trace: it is with this one that the witness's weight is unmasked.
    from_client = None
    for x in text.splitlines():
        m = re.search(r"\[vid\]\s+(\d+) frames \((\d+) keys\)", x)
        if m:
            from_client = {"frames": int(m.group(1)), "keys": int(m.group(2))}
    wire = None
    if before and after:
        b, pk = after[0] - before[0], after[1] - before[1]
        wire = {"byte": b, "packets": pk, "seconds": real,
                "byte_per_pacchetto": round(b / pk, 1) if pk else None}
    server = server_counts(line0)
    giornale, read, gone_mute = [], {"outcome": "without trace"}, None
    if with_trace:
        rc, out2, err2 = root("python3 %s/09-b70-leggi.py %s/%s.rcpreg "
                              "%s/banchi/01-b4-validatore.py"
                              % (WORKDIR, WORKDIR, name, TREE_DIR), 600)
        try:
            read = json.loads(out2)
            giornale = read.pop("giornale", [])
        except Exception as e:
            read = {"outcome": "the reader did not answer: %s — %s"
                             % (e, (out2 + err2)[-200:])}
            # ⛔⛔ AND THIS IS THE THIRD FACE OF THE SAME DEFECT (§1.9), and
            #     the real run of 23 August 2026 found it: if the reader
            #     does not answer, the journal is EMPTY — and an empty journal has
            #     a face identical to *«the session delivered nothing»*.
            #     ⇒ `[M]` that evening the bench gave RED to «does not drop» on
            #       a run in which the server had sent **797** frames and
            #       the client had taken them: a red on the product for a file
            #       that was missing in MY tree (`01-b4-validatore.py`).
            #     ⇒ The unread trace is DECLARED, and the predicates that live
            #       on the journal refuse instead of accusing.
            gone_mute = ("⛔ THE §11.1 TRACE WAS NOT READ: %s" % read["outcome"])
    n = measure(giornale, seconds, server, wire,
               zeroed=read.get("zeroed"))
    if gone_mute:
        n["traccia_non_letta"] = gone_mute
        n["outcome"] = "I HAVE NOTHING TO JUDGE — " + gone_mute
    n["name"] = name
    n["motion"] = motion
    n["text_line"] = text_line          # ⭐ the premise of the second leg of I1
    n["tela_chiesta"] = canvas
    n["from_client"] = from_client
    n["lettore"] = read
    n["secondi_veri"] = round(real, 1)
    n["coda_cliente"] = text[-400:]
    return n


def print_round(n):
    """⛔ §6.2: ALL the quantities are printed, even those not needed
       for the question of the moment.  A table with a single column is not a
       short measurement: it is a SLANTED measurement."""
    if not _has_measured(n):
        _dub("%s · %s" % (n.get("name"), n.get("outcome")))
        return
    _inf("RATE    mean %6.2f/s   worst second %s/s   whole %s/s   "
         "median %s ms   p95 %s ms"
         % (n["fps"], n["fps_finestra_min"], n["fps_intero"],
            n["intervallo_mediano_ms"], n["intervallo_p95_ms"]))
    _inf("SHAPE   %d frames (%d keyframes · %d deltas = %.1f %% deltas)   "
         "codec on the wire %s   canvas %s"
         % (n["frames"], n["keys"], n["delta"], n["quota_delta"] * 100,
            ",".join(n["codec_sul_filo"]), ",".join(n["tela_sul_filo"])))
    _inf("BYTES   payload %s Mbit/s (%d B/frame)   wire %s Mbit/s   "
         "%s B/packet"
         % (n["mbit_s_carico"], n["bytes_per_frame"],
            n["mbit_s_filo"] if n["mbit_s_filo"] is not None else "NOT READ",
            n["byte_per_pacchetto"]))
    _inf("DELAY   final drift %s ms   maximum %s ms   minimum %s ms   "
         "⚠ it is the DRIFT, not the loop"
         % (n["deriva_fine_ms"], n["deriva_max_ms"], n["deriva_min_ms"]))
    if n.get("linea"):
        _inf("LINE    loss declared by the qdisc: %s   (%s)"
             % ("%.2f %%" % n["linea"]["loss_pc"]
                if n["linea"].get("loss_pc") is not None else "⛔ I DO NOT KNOW",
                n["linea"].get("come")))
    s = n.get("server") or {}
    if s.get("registro_non_letto"):
        _dub("SERVER  %s" % s["registro_non_letto"])
        return
    _inf("SERVER  delivered %s · not sent %s · sent %s · ABANDONED %s "
         "· canvas announcements %s   (log from line %s)"
         % (s.get("delivered"), s.get("non_spediti"), s.get("sent"),
            s.get("abbandonati"), s.get("annunci_tela"), s.get("riga0")))
    _inf("CAPTURE %s   ⭐ «empty waits» = we asked and there was nothing: it is the "
         "column that separates Mutter from us"
         % json.dumps(s.get("capture"), ensure_ascii=False))
    _inf("        second leg: gaps in `number` %s · streams reset in the "
         "trace %s · audio %s"
         % (n["buchi_numero"], n.get("azzerati_sul_filo"), s.get("audio")))
    _inf("        spiral (§5.2/§5.1): %s" % json.dumps(s.get("spirale"),
                                                       ensure_ascii=False))
    # ⛔ THE WITNESS'S WEIGHT, and it is looked at on EVERY run.
    dc, sp = n.get("from_client"), s.get("sent")
    if dc and sp:
        missing = sp - dc["frames"]
        if missing > max(5, 0.05 * sp):
            _dub("⚠ the server sent %d and the client took %d "
                 "(%d fewer): the bottleneck may be the WITNESS, not the line"
                 % (sp, dc["frames"], missing))


# ═══════════════════════════════════════════════════════════════════════════
def main():
    global NETWORK
    p = argparse.ArgumentParser()
    p.add_argument("step", nargs="?",
                   choices=["terrain", "probe", "restore", "status"])
    p.add_argument("--certify", action="store_true",
                   help="⭐ the positive control: proves the bench can see "
                        "the defects it looks for.  It does not touch the test machine")
    p.add_argument("--seconds", type=int, default=30)
    p.add_argument("--only", default="", help="one step only, by name")
    p.add_argument("--tone", default="no", choices=["yes", "no"],
                   help="⚠ turns on 1.56 Mbit/s of PCM: the question «who pays between "
                        "audio and video» is already closed by 07-b65, here the "
                        "default is OFF so the step measures the video")
    p.add_argument("--witness-check", action="store_true",
                   help="⭐ reruns the floor step WITHOUT a trace: it is the "
                        "direct proof that the witness does not weigh on the number")
    p.add_argument("--no-min-canvas", action="store_true",
                   help="skips the 768x480 pair of the floor step")
    a = p.parse_args()

    if a.certify:
        return certify()
    if not a.step:
        p.error("a step is needed, or --certify")

    os.makedirs(OUT, exist_ok=True)
    NETWORK = _import_network()

    if a.step in ("restore", "status"):
        _log("the test machine's network — dev «%s», port %d" % (DEV, PORT))
        return 0 if NETWORK.restore() else 2

    if a.step == "terrain":
        return 0 if terrain_check() else 2

    _log("09-b70 · THE RATE — port %d · dev «%s» · codec requested «%s»"
         % (PORT, DEV, REQUESTED_CODEC))
    print("   ⛔ «%s» (ssh + the user's 7730) is NOT touched" % VIETATA)
    print("   ⛔ the floor is 20 Mbit/s (§3.1-bis) and 25 frames/s (§2.1):")
    print("      below 20 we LOOK, we do not demand")
    print("   --  «%s» before: %s" % (DEV, NETWORK.qdisc() or "(none)"))
    if not terrain_check():
        return 2

    chosen = [g for g in RUNGS if not a.only or a.only in g[0]]
    if not chosen:
        _ko("no step matches «%s»" % a.only)
        return 2
    # still scene + moving scene for every step, plus the pair at minimum canvas
    amount = 2 * len(chosen) + (2 if (not a.no_min_canvas and
                                      any(g[0].startswith("g4") for g in chosen)) else 0)
    total = (a.seconds + 170) * amount + 400
    NETWORK.guardian_arm(total)

    outcomes, rossi, silent = [], [], []
    try:
        _inf("opening a short session to bring the stage and the monitor to life")
        if not trigger_session():
            _ko("the session does not open: I do not measure")
            return 2
        if a.tone == "yes":
            NETWORK.tone_turn_on()
            _inf("⚠ the tone is ON: the step does not measure the video alone")

        work = []
        for name, mbit, delay, requirement, why in chosen:
            work.append((name, mbit, delay, requirement, why, FULL_CANVAS, ""))
            if name.startswith("g4") and not a.no_min_canvas:
                work.append((name, mbit, delay, requirement,
                               "⭐ the same step at the FLOOR CANVAS: "
                               "§2.1 is written at 480p, and adaptive "
                               "resolution is out of the product (§5.0-ter)",
                               MIN_CANVAS, "-480"))

        for name, mbit, delay, requirement, why, canvas, ver_suffix in work:
            _log("%s%s · %s" % (name, ver_suffix, why))
            reg = _rules(mbit, delay)
            ok, q = NETWORK.tighten(reg)
            if not ok:
                _ko(q)
                outcomes.append({"rung": name + ver_suffix, "passes": False,
                              "why": "tc refused the rule"})
                rossi.append(name + ver_suffix)
                break
            if mbit:
                _inf("tc: %s  (queue %d packets = %d ms at %d Mbit/s — the "
                     "netem default would be 1000, that is %d ms)"
                     % (" ".join(reg), _limit(mbit), CUSHION_MS, mbit,
                        int(1000 * PACKAGE * 8 * 1000 / (mbit * 1e6))))
            else:
                _inf("tc: %s  (no bandwidth limit: the netem only counts)"
                     % " ".join(reg))
            _inf("canvas %s" % canvas)

            pair = {}
            for label, motion in (("mossa", "barra"), ("ferma", "mark")):
                usc = scene_turn_on(motion)
                if not usc:
                    _ko("the «%s» scene does not start: I do NOT judge this step"
                        % motion)
                    pair[label] = {"outcome": "I HAVE NOTHING TO JUDGE — "
                                                 "the scene did not start"}
                    continue
                _inf("scene «%s» on monitor %s" % (motion, usc))
                n = cur_round("%s%s-%s" % (name, ver_suffix, label), motion, canvas,
                         a.seconds)
                print("   [%s]" % label)
                print_round(n)
                pair[label] = n
                scene_turn_off()

            # ⛔ I1 FIRST, and it is the reason why the step is run twice.
            pass_i1, why_i1 = p_I1(pair.get("ferma", {}),
                                       pair.get("mossa", {}))
            (_ok if pass_i1 else (_dub if pass_i1 is None else _ko))(
                "I1 — the rate does not drop with the scene still: %s" % why_i1)

            entries = {"rung": name + ver_suffix, "mbit": mbit, "delay_ms": delay,
                    "coda_pacchetti": _limit(mbit) if mbit else None,
                    "canvas": canvas, "requirement": requirement, "why": why,
                    "I1": {"passes": pass_i1, "why": why_i1},
                    "ferma": pair.get("ferma"), "mossa": pair.get("mossa"),
                    "predicati": {}}
            if pass_i1 is False:
                rossi.append("%s%s · I1" % (name, ver_suffix))
            elif pass_i1 is None:
                silent.append("%s%s · I1 — %s" % (name, ver_suffix, why_i1))

            # Then the single-run predicates, on the MOVING run (which is the case
            # on which the floor is written) and on the STILL one.
            for label in ("mossa", "ferma"):
                n = pair.get(label) or {}
                entries["predicati"][label] = judge_round(n, requirement)
                for entry in entries["predicati"][label]:
                    mark = "%s%s · %s · %s" % (name, ver_suffix, label,
                                                entry["predicato"])
                    if not entry["conta"]:
                        _inf("⚠ diagnosis · %s · %s → %s (%s)"
                             % (label, entry["predicato"].split(" (")[0],
                                entry["passes"], entry["why"][:80]))
                        continue
                    (_ok if entry["passes"] else
                     (_dub if entry["passes"] is None else _ko))(
                        "%s · %s: %s" % (label,
                                         entry["predicato"].split(" (")[0],
                                         entry["why"]))
                    if entry["passes"] is False:
                        rossi.append(mark)
                    elif entry["passes"] is None:
                        silent.append("%s — %s" % (mark, entry["why"]))
            outcomes.append(entries)

        # ⭐ THE WITNESS CONTROL — the direct proof that the trace is not
        #    the bottleneck.  Same step, same scene, without `--record`.
        if a.witness_check:
            _log("⭐ WITNESS CONTROL — the same step WITHOUT a trace")
            NETWORK.tighten(_rules(20, DELAY_MS))
            usc = scene_turn_on("barra")
            if usc:
                without = cur_round("controllo-senza-traccia", "barra", FULL_CANVAS,
                             a.seconds, with_trace=False)
                scene_turn_off()
                _inf("without a trace — the client says: %s · the server: %s"
                     % (without.get("from_client"),
                        (without.get("server") or {}).get("sent")))
                outcomes.append({"rung": "controllo-testimone", "without": without})
                _inf("⛔ compare it with the «g4-20mbit-mossa» run above: "
                     "if the client takes noticeably more WITHOUT a "
                     "trace, the grid's number belongs to the witness")
    finally:
        scene_turn_off()
        if a.tone == "yes":
            NETWORK.tone_turn_off()
        _log("⛔ THE NETWORK IS PUT BACK AS IT WAS")
        restored = NETWORK.restore()

    with open(os.path.join(OUT, "09-b70-esiti.json"), "w") as f:
        json.dump(outcomes, f, ensure_ascii=False, indent=1)
    _inf("outcomes in %s/09-b70-esiti.json" % OUT)

    _log("THE VERDICT — %d steps run · %d red · %d not judged"
         % (len(outcomes), len(rossi), len(silent)))
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
        # ⚠ «I did not measure» is an outcome of ITS OWN, not a green.
        return 3
    _ok("⭐ all the predicates did what was written beforehand")
    return 0


if __name__ == "__main__":
    sys.exit(main())
