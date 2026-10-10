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
  `07-b65 --scena no` does.  With the scene off the compositor delivers very little, and
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
    by `07-b65`: here the tone is **off** unless `--tono si`, so the step
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
    two `u32` filters on the port only, `rimetti` that checks itself) is that of
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

 1. ⛔ **`sudo -S` covers only the FIRST link of the chain** (see `catena_root()`
    and `root()`).  `[M]` the §11.1 trace reader **was not written** on the
    machine, and the bench did not notice.  ⇒ A single `sudo`, and the whole
    chain inside `bash -c`.
 2. ⛔⛔ **A trailing `< file` STEALS stdin from `sudo -S`** (same place).  `[M]`
    `righe_registro()` returned **0** silently, and then `conti_del_server()`
    read the log **from the server's startup**: `[M]` 23 Aug, on the
    still-scene run there would have been **4 041** empty waits instead of the **1 604**
    of the run.  ⇒ Redirection inside root's shell, `righe_registro()` that
    returns `None` instead of 0, a guard in `conti_del_server()` and a predicate that
    says so out loud (`p_registro_letto`).
 3. ⛔ **The implicit premise of I1** (see `p_I1` and `RESA_FERMA`).  *«With a still
    scene there is no congestion that justifies an abandonment»* holds **only on a
    line without loss**: `[M]` on `casa-cattiva` (2 %) the abandonment leg
    gave a red that was not the product's.  ⇒ Conditioned leg: it refuses
    to judge where the premise is missing, and gives red where it holds.
 4. ⛔ **The empty journal because I did not read it** (see `giro()` and
    `p_niente_stacco`).  `[M]` 23 Aug: the §11.1 reader did not start —
    `01-b4-validatore.py` was missing from the tree — and the bench gave RED to «does not drop»
    on a session alive with **797** frames.  ⇒ The unread trace is
    declared, `terreno_controlla()` checks the referee before measuring, and the
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
    python3 banchi/09-b70-ritmo.py --certifica     ⭐ HERE, without the machine
    python3 banchi/09-b70-ritmo.py terreno
    python3 banchi/09-b70-ritmo.py sonda [--secondi 30] [--solo g4]
    python3 banchi/09-b70-ritmo.py sonda --controllo-testimone
    python3 banchi/09-b70-ritmo.py rimetti         ⛔ and it is checked
"""
import argparse, base64, importlib.util, json, os, re, shlex, statistics, struct
import subprocess, sys, time

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ ISOLATION, WRITTEN BEFORE ANY IMPORT THAT READS IT
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ 7900 belongs to another agent, 7801/7802 belong to phase 7, 7730 is
#    the user's and it is ON.  Mine is 7809.
PORTA = int(os.environ.get("PORTA", "7809"))
UTENTE = os.environ.get("UTENTE", "provan9")
UID_B = int(os.environ.get("UID_B", "1029"))
MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
IND = os.environ.get("IND", "192.168.0.2")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/09-r")
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/09-r-src")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/09-r-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/09-r")
SCENA_BIN = os.environ.get("SCENA_BIN",
                           "/media/REMOTIX/src/04-b30-scena-lav/04-b30-scena")
QUI = os.path.dirname(os.path.abspath(__file__))
FUORI = os.environ.get("FUORI", "/tmp/09-b70")

VIETATA = "enp7s0"     # ⛔ ssh and the user's 7730 go through it: never
DEV = "lo"

# ⛔ The ports that are NOT mine: they are counted first, and never touched.
VICINE = ["7700", "7710", "7720", "7730", "7801", "7802", "7900"]

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE NETWORK DISCIPLINE IS IMPORTED FROM 07-b65, AND THEN CHECKED
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `07-b65-datagram.py` binds its constants to the environment **at import**.  ⇒
#    The environment is set up here above and passed BEFORE importing it, so the
#    module is born with my port and the guardian writes the pid into my LAV.
# ⛔⛔ And then it is CHECKED.  Importing a module that configures itself from the environment and
#      taking for granted that it has read it is exactly how one
#      ends up throttling someone else's port believing one is throttling
#      one's own — and the network is the only thing in this bench that, when wrong, hurts
#      those who have nothing to do with it.
def _importa_rete():
    for chiave, valore in (("PORTA", str(PORTA)), ("UTENTE", UTENTE),
                           ("UID_B", str(UID_B)), ("MACCHINA", MACCHINA),
                           ("PAROLA_SUDO", PAROLA_SUDO), ("IND", IND),
                           ("LAV", LAV), ("ALBERO", ALB),
                           ("DENTRO_ALB", DENTRO_ALB), ("DENTRO_LAV", DENTRO_LAV),
                           ("FUORI", FUORI)):
        os.environ[chiave] = valore
    perc = os.path.join(QUI, "07-b65-datagram.py")
    spec = importlib.util.spec_from_file_location("b65rete", perc)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    guai = []
    if m.PORTA != PORTA:
        guai.append("the module's port is %d, mine is %d" % (m.PORTA, PORTA))
    if m.DEV != DEV:
        guai.append("the module's device is «%s», mine is «%s»" % (m.DEV, DEV))
    if m.VIETATA != VIETATA:
        guai.append("the module's forbidden interface is «%s»" % m.VIETATA)
    if m.LAV != LAV:
        guai.append("the guardian would write the pid in «%s», not in «%s»" % (m.LAV, LAV))
    if guai:
        raise SystemExit("⛔ I DO NOT TOUCH THE NETWORK: the import of 07-b65 did not take "
                         "my environment — " + " · ".join(guai))
    return m


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE STEPS — and the expectation of each is a PREDICATE, further down
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ There is always a delay: without RTT the congestion window has no way to
#    fill up and the pacer notices nothing.  15 ms per side = 30 ms of
#    round trip, which is a home fibre line.
RITARDO_MS = int(os.environ.get("RITARDO_MS", "15"))
CUSCINO_MS = int(os.environ.get("CUSCINO_MS", "50"))   # ⛔ the wire's queue, declared
PACCHETTO = 1452                                        # the typical QUIC packet


def _limite(mbit):
    """The queue packets worth `CUSCINO_MS` at that bandwidth."""
    return max(8, int(mbit * 1e6 * (CUSCINO_MS / 1000.0) / 8.0 / PACCHETTO))


def _regole(mbit, ritardo_ms):
    """⛔ EVEN THE WIDE STEP CARRIES A `netem`, and the reason is quantity 3.

    The real bytes on the wire are read from the qdisc counter (`tc -s`).  A
    step without a qdisc does not have that counter ⇒ the **denominator** would be
    the only run without the bytes on the wire, that is the only run that cannot be
    compared with the others on the quantity that decides whether the line is full.
    ⇒ `g0` carries a `netem` **without bandwidth and without delay**: it serves only to
    count.  ⚠ And its price is declared — one more qdisc in the path —
    instead of leaving the denominator blind.
    """
    regole = ["limit", str(_limite(mbit)) if mbit else "100000"]
    if ritardo_ms:
        regole += ["delay", "%dms" % ritardo_ms]
    if mbit:
        regole += ["rate", "%dmbit" % mbit]
    return regole


#  (name, mbit, delay_ms, requirement, why)
#
# ⭐⭐ AND THE DELAY HAS A STEP OF ITS OWN.  If `g0` had no delay and `g1` had
#     delay **and** bandwidth, TWO things would change together between them, and any
#     difference would be attributable to both — which is the politest way
#     in which a grid of steps can lie (`LEZIONI.md` §1.26: *«every
#     number must be attributed on its own»*).  ⇒ `g0b` carries the 15 ms **and nothing else**.
GRADINI = [
    ("g0-largo",   None, 0, True,
     "no limit and no delay: the denominator. The netem is there only to "
     "count the bytes"),
    ("g0b-ritardo", None, RITARDO_MS, True,
     "⭐ only the %d ms per side, free bandwidth: isolates the effect of the ROUND TRIP "
     "from that of the bandwidth" % RITARDO_MS),
    ("g1-40mbit",  40, RITARDO_MS, True,
     "twice the floor — and the boundary of the declared H.264 level (5.0)"),
    ("g2-30mbit",  30, RITARDO_MS, True,
     "the «good fixed line» of §3.1-bis: aiming at the desired"),
    ("g3-25mbit",  25, RITARDO_MS, True,
     "just above the floor: the first step where something may give way"),
    ("g4-20mbit",  20, RITARDO_MS, True,
     "⭐ THE FLOOR (§3.1-bis). It is the step that decides the phase"),
    ("g5-15mbit",  15, RITARDO_MS, False,
     "⚠ BELOW THE PROMISE — declared diagnosis: we look, we do not demand"),
    ("g6-10mbit",  10, RITARDO_MS, False,
     "⚠ half the floor — diagnosis: what matters is HOW it gives way, not whether"),
]

# ⭐ The canvas.  The grid runs at 1080p, which is the real desktop and the one the
#    user looks at.  ⛔ But the floor of §2.1 is written **at 480p**, and adaptive
#    resolution is out of the product by decision (§5.0-ter): the
#    product serves the canvas the client asks for, and that is all.  ⇒ At the floor
#    step only, the pair is also redone at **768x480**, which is the number
#    the project already writes for «the minimum of §2.1» (`DECISIONI.md:1133`).
TELA_PIENA = os.environ.get("TELA", "1920x1080")
TELA_MINIMA = os.environ.get("TELA_MINIMA", "768x480")

# ⭐ The codec is declared and CHECKED on the wire.  The server offers «hevc,h264»
#    (`rcp.c:1674`); the client's default is «hevc,av1», which would negotiate
#    **HEVC** — that is an operating point that is not the product's, because
#    Firefox on Android has neither HEVC nor AV1.  ⇒ We ask for h264, and the bench
#    reads from the wire which codec really arrived: a silent fallback to
#    another codec would change every number on this page without saying so.
CODEC_CHIESTO = os.environ.get("CODEC", "h264")
CODEC_NUMERO = {1: "hevc", 2: "av1", 3: "h264"}


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE THRESHOLDS, IN ONE PLACE ONLY, AND EACH WITH ITS REASON
# ═══════════════════════════════════════════════════════════════════════════
PAVIMENTO_FPS = 25.0        # `DECISIONI.md` §2.1: 480p · 25 fps, the bottom of the scale
PAVIMENTO_FINESTRA = 20.0   # ⚠ *sufficient, not right*: 80 % of the floor, and
                            #   it serves only not to give red to a window that
                            #   falls across a single hiccup.  The first
                            #   run that lands between 20 and 25 must be looked at, not
                            #   retuned.
QUOTA_DELTA = 0.90          # §3.3: we degrade IN TIME.  A stream that loses more
                            #   than one delta in ten is degenerating into keyframes —
                            #   `[M]` 21 Aug: on the narrow runs they were 144/144.
DERIVA_FINE_MS = 250.0      # ⭐ anchored to a measured number, not chosen: the whole
                            #   loop of phase 8 is worth `[M]` 55.20 ms.  A drift
                            #   worth FOUR loops is no longer a delay, it is
                            #   a queue.
DERIVA_MAX_MS = 400.0
I1_TOLLERANZA = 0.05        # ⚠ the noise between two runs on the same machine
I1_CONSEGNATI = 0.25        # beyond it, the difference is UPSTREAM and is not judged
RESA_FERMA = 0.98           # ⛔⛔ AND ITS PREMISE IS CONDITIONAL, not general:
                            #   «with a still scene there is no congestion that
                            #   justifies an abandonment» holds **only on a
                            #   line that does not lose**.  `[M]` 23 Aug 2026: on the
                            #   `casa-cattiva` profile (2 % loss) the
                            #   premise is FALSE and this leg gave a red
                            #   that was not a product defect — while the
                            #   frames/s leg passed (still 10.13/s
                            #   against moving 7.78/s: the still one went FASTER).
                            #   ⇒ The leg is not removed: it is conditioned on the fact
                            #     that justifies it (see `p_I1`).
SCALDATA_S = 3.0            # ⛔ the first seconds are session opening and first
                            #   keyframe: they are declared and removed, and the whole
                            #   number is printed alongside all the same
MINIMO_FOTOGRAMMI = 30      # below this, there is nothing to reduce


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE TRACE READER — it runs ON THE MACHINE, because the trace is heavy
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ No new tool is invented to know when a frame
#    arrived: `01-b3-cliente.py --registra` already writes the trace of
#    `RCP.md` §11.1, which carries for every block the `istante_ms` of the client's
#    **monotonic clock** and the bytes, and the first block of every video stream
#    carries the 28 header bytes of §6.2 — `numero`, `tipo` (keyframe or delta),
#    `codec` and the **server's** monotonic `istante` at capture.
#    ⇒ Everything needed is already on disk: here we reduce, we do not measure.
#
# ⚠ The grain is the millisecond (§11.1 writes `istante_ms`).  On an interval
#   of 40 ms that is 2.5 %: enough for the rate and for the drift, it would **not** be enough
#   for a loop — and it is another reason why the loop does not belong here.
#
# ⛔ And the trace is reduced **on the machine**: at 20 Mbit/s for 30 s that is ~75 MB,
#    and carrying them over ssh at every run would be an hour of network for an 80 KB JSON.
LETTORE = r'''#!/usr/bin/env python3
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

CANALE_VIDEO = 0x03


def arbitro(percorso):
    spec = importlib.util.spec_from_file_location("b4arbitro", percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def principale():
    traccia, validatore = sys.argv[1], sys.argv[2]
    A = arbitro(validatore)
    MAGIA, BLOCCO, BLOCCO_BYTE = A.MAGIA, A.BLOCCO, A.BLOCCO_BYTE
    SERVER, FIN, RESET = A.SERVER, A.FIN, A.RESET
    with open(traccia, "rb") as f:
        d = f.read()
    if len(d) < 16 or d[:8] != MAGIA:
        print(json.dumps({"esito": "NON HO NIENTE DA GIUDICARE — the trace does not "
                                   "carry the magic of §11.1",
                          "primi8": d[:8].hex()}))
        return 3
    quanti, orologio, r1, r2, r3 = struct.unpack("!IBBBB", d[8:16])
    if A.OROLOGIO.get(orologio) != "client":
        # ⛔ Without knowing WHOSE the times are, the drift cannot even be
        #    stated: we do not guess.
        print(json.dumps({"esito": "NON GIUDICO — the trace's clock is not "
                                   "the client's", "orologio": orologio}))
        return 3
    p, letti = 16, 0
    flussi, ordine = {}, []
    for _ in range(quanti):
        if p + BLOCCO_BYTE > len(d):
            break
        verso, canale, fine, ist, stream, lung, nosc = struct.unpack(
            BLOCCO, d[p:p + BLOCCO_BYTE])
        p += BLOCCO_BYTE
        p += nosc * 40                       # (ini u32, quanti u32, fingerprint 32 B)
        carico = d[p:p + lung]
        p += lung
        letti += 1
        if verso != SERVER or canale != CANALE_VIDEO:
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
    giornale, azzerati, monchi = [], 0, 0
    for sid in ordine:
        f = flussi[sid]
        if f["azzerato"]:
            azzerati += 1
            continue
        if f["fine_ms"] is None or len(f["testa"]) < 28:
            # ⚠ A stream the recording did not see finish: it is not a
            #   delivered frame and it is not an abandonment.  It is counted apart,
            #   instead of vanishing inside one of the two.
            monchi += 1
            continue
        tipo, codec, l, a, numero, istante, inp = struct.unpack("!HHIIIQI", f["testa"])
        giornale.append({"numero": numero, "chiave": tipo == 0x0301,
                         "tipo": tipo, "codec": codec, "l": l, "a": a,
                         "byte": max(0, f["byte"] - 28),
                         "istante_us": istante, "arrivo_ms": f["fine_ms"]})
    giornale.sort(key=lambda x: x["arrivo_ms"])
    print(json.dumps({"esito": "letto", "blocchi": letti, "flussi": len(ordine),
                      "azzerati": azzerati, "monchi": monchi,
                      "giornale": giornale}))
    return 0


if __name__ == "__main__":
    sys.exit(principale())
'''


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE REDUCTION — and it is THE SAME CODE that `--certifica` exercises
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ The positive control of this file does not test the predicates on numbers already
#    prepared: it builds JOURNALS and passes them through here.  ⇒ If the deception lives
#    in the reduction — and it is the case of the mean that hides the gap — the
#    control sees it.  A control that skipped this function would certify
#    half of the tool.
def _mediana(v):
    return statistics.median(v) if v else None


def misura(giornale, chiesto_s, server=None, filo=None, azzerati=None,
           scaldata_s=SCALDATA_S):
    """From a journal of frames to the numbers of the run.  All five."""
    n = {"chiesto_s": chiesto_s, "fotogrammi_grezzi": len(giornale),
         "scaldata_s": scaldata_s, "server": server or {},
         "azzerati_sul_filo": azzerati}
    if not giornale:
        n["esito"] = ("NON HO NIENTE DA GIUDICARE — no frame in the "
                      "trace")
        return n
    a0 = giornale[0]["arrivo_ms"]
    vissuto = (giornale[-1]["arrivo_ms"] - a0) / 1000.0
    n["vissuto_s"] = round(vissuto, 3)
    # ⛔ The warm-up is REMOVED and SAID: session opening, first keyframe and
    #    first canvas sit in there, and mixing them with steady state is like measuring
    #    a car's acceleration counting also the time to start the engine.
    #    ⚠ And the whole number is printed alongside all the same: whoever removes data
    #      must show what they removed.
    a_regime = [f for f in giornale if (f["arrivo_ms"] - a0) / 1000.0 >= scaldata_s]
    n["fotogrammi_scaldata"] = len(giornale) - len(a_regime)
    if len(a_regime) < MINIMO_FOTOGRAMMI:
        n["esito"] = ("NON HO NIENTE DA GIUDICARE — %d frames at steady state, "
                      "fewer than the minimum of %d" % (len(a_regime), MINIMO_FOTOGRAMMI))
        n["fotogrammi"] = len(a_regime)
        return n
    r0 = a_regime[0]["arrivo_ms"]
    durata = (a_regime[-1]["arrivo_ms"] - r0) / 1000.0
    if durata <= 0:
        n["esito"] = "NON HO NIENTE DA GIUDICARE — zero steady-state duration"
        return n
    n["fotogrammi"] = len(a_regime)
    n["durata_s"] = round(durata, 3)
    # 1 · THE RATE, and they are TWO numbers: the mean and the window minimum.
    n["fps"] = round(len(a_regime) / durata, 2)
    n["fps_intero"] = round(len(giornale) / vissuto, 2) if vissuto > 0 else None
    n["fps_finestra_min"], n["finestre"] = _finestra_minima(a_regime)
    intervalli = [(a_regime[i]["arrivo_ms"] - a_regime[i - 1]["arrivo_ms"])
                  for i in range(1, len(a_regime))]
    n["intervallo_mediano_ms"] = _mediana(intervalli)
    n["intervallo_p95_ms"] = (sorted(intervalli)[int(0.95 * (len(intervalli) - 1))]
                              if intervalli else None)
    # 2 · KEYFRAMES AND DELTAS — §3.3 lives here.
    chiavi = sum(1 for f in a_regime if f["chiave"])
    n["chiavi"] = chiavi
    n["delta"] = len(a_regime) - chiavi
    n["quota_delta"] = round(n["delta"] / len(a_regime), 4)
    # ⭐ The REAL codec, read from the wire: not the one requested.
    codici = sorted({f.get("codec") for f in a_regime})
    n["codec_sul_filo"] = [CODEC_NUMERO.get(c, "?%s" % c) for c in codici]
    misure = sorted({"%dx%d" % (f.get("l"), f.get("a")) for f in a_regime})
    n["tela_sul_filo"] = misure
    # 3 · THE BYTES — payload here, wire from the qdisc (further down).
    byte = sum(f["byte"] for f in a_regime)
    n["byte_carico"] = byte
    n["mbit_s_carico"] = round(byte * 8 / durata / 1e6, 3)
    n["byte_per_fotogramma"] = int(byte / len(a_regime))
    if filo and filo.get("byte") is not None and filo.get("secondi"):
        n["mbit_s_filo"] = round(filo["byte"] * 8 / filo["secondi"] / 1e6, 3)
        n["byte_per_pacchetto"] = filo.get("byte_per_pacchetto")
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
    #     §6.2: `numero` grows by one for every frame the server
    #     DECIDES to send, abandoned ones included, and NOT for those it does not
    #     send at all.  ⇒ A gap = a frame that left and did not arrive.
    numeri = sorted(f["numero"] for f in a_regime)
    buchi = 0
    for i in range(1, len(numeri)):
        salto = numeri[i] - numeri[i - 1]
        if salto > 1:
            buchi += salto - 1
    n["buchi_numero"] = buchi
    n["esito"] = "misurato"
    return n


def _finestra_minima(fotogrammi, larghezza_ms=1000):
    """⛔⛔ THE NUMBER THE MEAN HIDES.

    Thirty seconds made of ten at 45/s and twenty at 17.5/s give a mean of
    **26.7/s** — above the floor — and twenty seconds in which the desktop
    stutters.  ⇒ The mean alone acquits, and it must be accompanied by the **worst** that
    was seen in one second.  ⚠ The window is SLIDING, not in blocks: in
    blocks the gap can sit across two windows and vanish from both.
    """
    if len(fotogrammi) < 2:
        return None, 0
    t = [f["arrivo_ms"] for f in fotogrammi]
    peggio, quante, i = None, 0, 0
    for j in range(len(t)):
        if t[j] - t[0] < larghezza_ms:
            continue
        while t[j] - t[i] > larghezza_ms:
            i += 1
        # frames in the window (t[i], t[j]]
        conto = j - i
        quante += 1
        if peggio is None or conto < peggio:
            peggio = conto
    if peggio is None:
        return None, 0
    return float(peggio), quante


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE PREDICATES — WRITTEN FIRST, and they return (passa, perche)
# ═══════════════════════════════════════════════════════════════════════════
#
#   passa = True    the expectation held
#   passa = False   ⛔ red
#   passa = None    ⚠ I DO NOT JUDGE — and it is not a polite green: it is an outcome of its own,
#                   and makes the bench exit 3.
def _si(perche):    return (True, perche)
def _no(perche):    return (False, perche)
def _muto(perche):  return (None, perche)


def _ha_misurato(n):
    return n.get("esito") == "misurato"


def p_registro_letto(n):
    """⛔⛔ THE PREDICATE THAT LOOKS AT THE TOOL, NOT THE PRODUCT — and it is here because
       the defect it covers is MUTE.

    `LEZIONI.md` §1.9: *«a zero that means "I did not read" and a zero that
    means "nothing happened" must not have the same face»*.
    `[M]` 23 August 2026: `righe_registro()` returned 0 because a trailing `< file`
    stole stdin from `sudo -S` (see `catena_root()`), and from then on
    **every** number on the server side was cumulative from startup — including
    `attese_a_vuoto`, which is the column with which `p_I1` decides whether to refuse.
    ⇒ A bench that goes straight on with that zero is not a bench: it gives a green to
      a measurement it did not make.

    ⚠ It applies at EVERY step, even the diagnosis ones: it is not a promise of the
      product, it is the condition for the numbers to belong to this run.
    """
    s = n.get("server") or {}
    if s.get("registro_non_letto"):
        return _muto("%s ⇒ I do NOT JUDGE this run on the server side"
                     % s["registro_non_letto"])
    if not s:
        return _muto("this run does not carry the server-side counts")
    if "riga0" in s:
        return _si("the log was read from line %d on: the server's counts "
                   "belong TO THIS RUN, not to the time since startup" % s["riga0"])
    return _si("the server-side counts are there")


def p_niente_stacco(n):
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
        return _muto("%s — the journal is empty because I DID NOT READ IT, not "
                     "because the session died: I DO NOT JUDGE"
                     % n["traccia_non_letta"])
    vissuto, chiesto = n.get("vissuto_s"), n.get("chiesto_s")
    if not chiesto:
        return _muto("I do not know how much was requested")
    if not n.get("fotogrammi_grezzi"):
        return _no("no frame in %.0f s: the session delivered "
                   "nothing" % chiesto)
    if vissuto is None:
        return _muto("I do not know how long delivery lasted")
    if vissuto < 0.90 * chiesto:
        return _no("delivery lasted %.1f s out of %.0f requested: it dropped"
                   % (vissuto, chiesto))
    return _si("it delivered for %.1f s out of %.0f requested: it did not drop"
               % (vissuto, chiesto))


def p_pavimento_ritmo(n):
    """⭐ `DECISIONI.md` §2.1 + §3.1-bis, together: **on a 20 Mbit/s line
       a rate below 25 per second is a DEFECT**, not a successful
       degradation.

    ⛔ And they are TWO legs, because a single one can be fooled:
       · the steady-state **mean**;
       · the **minimum over a one-second window**, which is the only one that sees the
         gap inside a good mean.
    """
    if not _ha_misurato(n):
        return _muto(n.get("esito", "I did not measure"))
    fps, fin = n["fps"], n["fps_finestra_min"]
    if fin is None:
        return _muto("less than one whole window: the minimum does not exist")
    if fps < PAVIMENTO_FPS:
        return _no("mean %.2f/s below the floor of %.0f/s (§2.1)"
                   % (fps, PAVIMENTO_FPS))
    if fin < PAVIMENTO_FINESTRA:
        return _no("mean %.2f/s is fine, ⛔ but there is a second with %.0f "
                   "frames: the mean was hiding the gap" % (fps, fin))
    return _si("mean %.2f/s and worst second %.0f/s, above the floor of "
               "%.0f/s" % (fps, fin, PAVIMENTO_FPS))


def p_degrada_nel_tempo(n):
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
    if not _ha_misurato(n):
        return _muto(n.get("esito", "I did not measure"))
    if n["chiavi"] + n["delta"] == 0:
        return _muto("no frame classified")
    q = n["quota_delta"]
    if q < QUOTA_DELTA:
        return _no("deltas %.1f %% (%d keyframes out of %d): the stream is degenerating "
                   "into keyframes — it is the spiral of §5.2"
                   % (q * 100, n["chiavi"], n["chiavi"] + n["delta"]))
    return _si("deltas %.1f %% (%d keyframes out of %d): it degrades in time, not into keyframes"
               % (q * 100, n["chiavi"], n["chiavi"] + n["delta"]))


def p_ritardo_non_scappa(n):
    """⛔ `SPECIFICHE.md:128`: *«every intermediate buffer buys smoothness and sells
       responsiveness»*, and delay weighs more than frames.

    ⚠ Here the **drift** is measured (see the header), not the loop.  The
      threshold is anchored to a measurement, not chosen: the whole loop of phase 8
      is worth `[M]` **55.20 ms**; a drift of 250 ms is worth **four loops**, and at
      that point it is no longer a delay, it is a queue.
    """
    if not _ha_misurato(n):
        return _muto(n.get("esito", "I did not measure"))
    fine, mas = n["deriva_fine_ms"], n["deriva_max_ms"]
    if fine > DERIVA_FINE_MS:
        return _no("delivery fell behind capture by %.0f ms "
                   "(ceiling %.0f)" % (fine, DERIVA_FINE_MS))
    if mas > DERIVA_MAX_MS:
        return _no("the drift touched %.0f ms (ceiling %.0f), though it came back to "
                   "%.0f" % (mas, DERIVA_MAX_MS, fine))
    return _si("final drift %.0f ms, maximum %.0f: the queue did not run away"
               % (fine, mas))


def _perdita_dichiarata(*giri, **kw):
    """The loss of the line under these runs, in %, or `None` if I DO NOT KNOW.

    ⛔ It is not assumed: it is read from what the run carries with it — and the one who
       writes it is `giro()`, which gets it from the **installed qdisc** (see
       `_linea_del_giro()`).  ⚠ So it holds even when the run was run by
       someone else with a `netem` of their own: `09-b76-rete-cattiva.py` calls
       `B70.giro()` with `loss` on, and this function sees it all the same.

    ⭐ And `None` is NOT zero: if I do not know whether the line loses, the premise of the
       abandonment leg is not verified, and an unverified premise does not give
       the right to give red.
    """
    esplicita = kw.get("perdita_pc")
    if esplicita is not None:
        return float(esplicita), "declared by whoever called me"
    for g in giri:
        for dove, chiave in (("linea", "perdita_pc"), ("sonda", "persi_pc")):
            v = ((g or {}).get(dove) or {}).get(chiave)
            if v is not None:
                return float(v), "read from «%s.%s» of the run" % (dove, chiave)
    return None, ("no run of the pair declares the loss of the line")


def p_I1(ferma, mossa, perdita_pc=None):
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
        lose**.  On a line that loses 2 % (`casa-cattiva`, `[M]` 23 Aug)
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
    if not (_ha_misurato(ferma) and _ha_misurato(mossa)):
        return _muto("one of the two runs of the pair did not measure: "
                     "still «%s», moving «%s»"
                     % (ferma.get("esito"), mossa.get("esito")))
    cf = (ferma.get("server") or {}).get("consegnati")
    cm = (mossa.get("server") or {}).get("consegnati")
    if not cf or not cm:
        return _muto("the log did not give the «delivered to RCP» of the two runs: "
                     "without a denominator the pair is not comparable")
    scarto = abs(cf - cm) / float(max(cf, cm))
    if scarto > I1_CONSEGNATI:
        return _muto("the compositor delivered %d frames with the scene still "
                     "against %d with the scene moving (%.0f %% apart): the difference "
                     "is UPSTREAM of us and I do NOT judge it as I1" % (cf, cm, scarto * 100))
    # ⭐⭐ THE BEST GUARD, and it does not deduce: the child's EMPTY WAITS.
    #     If with a still scene we asked for a frame and there was none, the
    #     lower rate is the compositor's and the product has nothing to do with it.  ⛔ It is
    #     the distinction `04-b32-ritmo.py` exists to make, and the line
    #     `figlio.c:2669` records the time it was made the other way round:
    #     *«the thesis was false: Mutter had the frames, and we were not there
    #     to take them»*.
    vf = ((ferma.get("server") or {}).get("cattura") or {}).get("attese_a_vuoto")
    vm = ((mossa.get("server") or {}).get("cattura") or {}).get("attese_a_vuoto")
    if vf is not None and vm is not None and vf > max(20, 3 * (vm + 1)):
        return _muto("with the scene still the child waited EMPTY %d times "
                     "(against %d with the scene moving): the frame was not there, and the "
                     "lower rate belongs to the COMPOSITOR — I do not judge it "
                     "as I1" % (vf, vm))
    # ── FIRST LEG: the rate.  It holds on any line (see the docstring) ───────
    guai = []
    if ferma["fps"] < mossa["fps"] * (1.0 - I1_TOLLERANZA):
        guai.append("the rate with the scene STILL is %.2f/s against %.2f/s with the scene "
                    "moving: it drops when it must not" % (ferma["fps"], mossa["fps"]))
    # ── SECOND LEG: the abandonments.  ⛔ And FIRST its premise ──────────────
    buttati = []
    ab = (ferma.get("server") or {}).get("abbandonati")
    if ab:
        buttati.append("with the scene still the server abandoned %d frames" % ab)
    sp = (ferma.get("server") or {}).get("spediti")
    if sp is not None and cf:
        resa = sp / float(cf)
        if resa < RESA_FERMA:
            buttati.append("with the scene still %d frames went out out of %d "
                           "delivered to RCP (yield %.3f, below %.2f)"
                           % (sp, cf, resa, RESA_FERMA))
    perdita, da_dove = _perdita_dichiarata(ferma, mossa, perdita_pc=perdita_pc)
    premessa = (perdita == 0.0)
    if buttati and not premessa:
        motivo = ("the premise of this leg — «with a still scene there is no "
                  "congestion that justifies an abandonment» — holds ONLY on a "
                  "line without loss, and here %s (%s)"
                  % ("the line loses %.2f %%" % perdita if perdita is not None
                     else "I do NOT KNOW whether the line loses", da_dove))
        if guai:
            # ⚠ The red of the rate stays: loss explains the abandonments, it does not
            #   explain a rate that drops when the scene stops.
            return _no("%s · ⚠ and the abandonments I do NOT judge (%s): %s"
                       % (" · ".join(guai), motivo, "; ".join(buttati)))
        return _muto("%s, but %s ⇒ I do NOT JUDGE the abandonments. ⭐ The "
                     "frames/s leg held: still %.2f/s against moving %.2f/s"
                     % ("; ".join(buttati), motivo, ferma["fps"], mossa["fps"]))
    guai += ["%s, and on a line without loss there is no congestion that "
             "justifies them" % b for b in buttati]
    if guai:
        return _no(" · ".join(guai))
    return _si("still scene %.2f/s against moving %.2f/s, delivered %d against %d, "
               "zero abandonments with the scene still (line %s): I1 holds"
               % (ferma["fps"], mossa["fps"], cf, cm,
                  "without loss" if premessa else
                  "with loss %s — but there was nothing to justify"
                  % ("%.2f %%" % perdita if perdita is not None else "unknown")))


# The predicates that apply to a single run, in order.
PREDICATI_GIRO = [
    # ⛔ First, because if this one refuses the three server-side numbers
    #    that follow do not belong to this run.  And it applies everywhere (`False`).
    ("the log belongs to THIS run (§1.9)", p_registro_letto, False),
    ("does not drop (§3.1-bis, holds even below the floor)", p_niente_stacco, False),
    ("the rate floor (§2.1: 25/s)", p_pavimento_ritmo, True),
    ("degrades in time, not into keyframes (§3.3)", p_degrada_nel_tempo, True),
    ("the delay does not run away (the drift)", p_ritardo_non_scappa, True),
]


def giudica_giro(n, requisito):
    """⛔ At the diagnosis steps we MEASURE everything and DEMAND one thing only.

    Calling red a low rate at 10 Mbit/s would mean measuring a
    promise the product does not make (§3.1-bis) — that is repeating mistake 2 of v1
    with the sign reversed.  ⇒ The predicates that are not a requirement at that step
    run all the same and their outcome is WRITTEN, marked «diagnosis».
    """
    fuori = []
    for nome, f, solo_se_requisito in PREDICATI_GIRO:
        passa, perche = f(n)
        conta = requisito or not solo_se_requisito
        fuori.append({"predicato": nome, "passa": passa, "perche": perche,
                      "conta": conta})
    return fuori


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE POSITIVE CONTROL — «how does this bench know it can see?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ On the model of `banchi/07-b64-orecchio.py --certifica`, and for the same
#    reason: *«a bench that cannot see the defect it looks for has no right
#    to green»* (`PIANO.md` §0.3.4).
#
# ⭐ And the cases do NOT pass ready-made numbers to the predicates: they build
#    JOURNALS and pass them through `misura()`, which is the same function that
#    runs on the real runs.  ⇒ A deception that lives in the REDUCTION — and it is case
#    2, the mean that hides the gap — is seen.  Certifying the predicates
#    alone would certify half of the tool.
def _fab(tratti, byte=25000, chiave_ogni=0, deriva_ms_per_fotogramma=0.0,
         numero_da=1, salta_ogni=0):
    """Builds a journal.  `tratti` = [(fps, seconds), ...].

    ⛔ `arrivo_ms` is the CLIENT's clock, `istante_us` the SERVER's: the
       drift is built by moving the second away from the first, which is what
       happens when the queue grows.
    """
    g, t_arr, t_cat, numero, i = [], 0.0, 0.0, numero_da, 0
    for fps, secondi in tratti:
        passo = 1000.0 / fps
        for _ in range(int(round(fps * secondi))):
            chiave = (chiave_ogni and i % chiave_ogni == 0) or i == 0
            salta = salta_ogni and i and i % salta_ogni == 0
            if salta:
                numero += 1          # ⭐ the gap in the sequence: §6.2
            g.append({"numero": numero, "chiave": bool(chiave), "tipo":
                      0x0301 if chiave else 0x0302, "codec": 3,
                      "l": 1920, "a": 1080, "byte": byte,
                      "istante_us": int(t_cat * 1000.0),
                      "arrivo_ms": int(round(t_arr))})
            numero += 1
            i += 1
            t_arr += passo
            t_cat += passo - deriva_ms_per_fotogramma
    return g


def _con_linea(n, perdita_pc):
    """Sticks onto a fake run the line `giro()` would write for it from the qdisc."""
    n["linea"] = {"perdita_pc": perdita_pc,
                  "come": "netem with «loss %s%%»" % perdita_pc if perdita_pc
                          else "netem without `loss`"}
    return n


def certifica():
    """⛔ The expectation is written FIRST, and cases 2, 4, 5 and 6 are the ones that
       make a false green credible."""
    print("⭐ CERTIFICATION OF THE RATE BENCH — the expectation is written FIRST\n")
    print("   ⛔ No contact with the test machine: here the "
          "TOOL is tested,\n      not the product.\n")

    SRV = {"consegnati": 900, "non_spediti": 0, "spediti": 900,
           "abbandonati": 0, "annunci_tela": 0}
    FILO = {"byte": 90 * 1000 * 1000, "secondi": 30.0, "byte_per_pacchetto": 1452.0}

    casi = []

    # 0 · THE DENOMINATOR.  If this is not green, no red is worth anything.
    g = _fab([(60, 33)], chiave_ogni=0)
    casi.append(("0-healthy — 60/s for 33 s, one keyframe only",
                 misura(g, 33, SRV, FILO),
                 {"the log": True, "no drop": True, "the floor": True,
                  "degrades in time": True, "the delay": True}))
    # 1 · THE BARE DEFECT: the rate below the floor.
    g = _fab([(18, 33)])
    casi.append(("1-⛔ uniform rate 18/s: below the floor of 25",
                 misura(g, 33, SRV, FILO),
                 {"the log": True, "no drop": True, "the floor": False,
                  "degrades in time": True, "the delay": True}))

    # 2 · ⛔⛔ THE MEAN THAT HIDES THE GAP.
    #     10 s at 45/s + 20 s at 17.5/s = 800 frames in 30 s = **26.7/s**,
    #     that is ABOVE the floor.  A bench that looked at the mean alone
    #     would write «green» on twenty seconds of stuttering desktop.
    #     ⇒ It must give red, and because of the WINDOW.
    g = _fab([(45, 13), (17.5, 20)])
    casi.append(("2-⛔⛔ the mean that hides the gap: 45/s then 17.5/s "
                 "(mean above the floor)",
                 misura(g, 33, SRV, FILO),
                 {"the log": True, "no drop": True, "the floor": False,
                  "degrades in time": True, "the delay": True}))

    # 3 · ⛔ THE KEYFRAME-ONLY STREAM AT A GOOD RATE.
    #     30/s: the floor is happy.  But they are all keyframes — it is the spiral
    #     of §5.2 measured on 21 August (144/144).  Only §3.3 sees it.
    g = _fab([(30, 33)], chiave_ogni=1)
    casi.append(("3-⛔ 30/s but ALL KEYFRAMES: the rate acquits, §3.3 does not",
                 misura(g, 33, SRV, FILO),
                 {"the log": True, "no drop": True, "the floor": True,
                  "degrades in time": False, "the delay": True}))

    # 4 · ⛔⛔ THE RATE STANDS AND THE DELAY IS DESTROYED.
    #     It is `LEZIONI.md` §6.2 in its nastiest form: 30 frames per
    #     second delivered on time, and each is 4 ms older than the
    #     previous one.  After 30 s delivery is ~3.6 s behind.
    #     ⇒ A bench that counted frames only would give green.
    g = _fab([(30, 33)], deriva_ms_per_fotogramma=4.0)
    casi.append(("4-⛔⛔ 30/s on time and the drift running away (+4 ms per "
                 "frame): the rate acquits, the delay does not",
                 misura(g, 33, SRV, FILO),
                 {"the log": True, "no drop": True, "the floor": True,
                  "degrades in time": True, "the delay": False}))

    # 5 · ⛔ THE DROP HALFWAY.  Twelve seconds of excellent frames out of thirty
    #     requested: every «per second» quantity is good, and the session is
    #     dead.  ⇒ It is the only predicate that holds even below the floor.
    g = _fab([(60, 12)])
    casi.append(("5-⛔ the session dies at 12 s out of 33 requested: all the means "
                 "are good",
                 misura(g, 33, SRV, FILO),
                 {"the log": True, "no drop": False, "the floor": True,
                  "degrades in time": True, "the delay": True}))

    # 6 · ⛔⛔ THE EMPTINESS.  It is case R7a of the ear judge, carried over: a bench that
    #     answered «zero abandonments, zero keyframes, no violation» on a
    #     run without frames would give **top marks to silence**.
    #     ⇒ Every predicate must REFUSE, except «does not drop», which here is a
    #       true red: nothing arrived.
    casi.append(("6-⛔⛔ the EMPTINESS: zero frames (top marks to silence)",
                 misura([], 33, SRV, FILO),
                 {"the log": True, "no drop": False, "the floor": None,
                  "degrades in time": None, "the delay": None}))

    # 6b · ⛔⛔ THE ZERO THAT MEANS «I DID NOT READ» — `LEZIONI.md` §1.9, and
    #      cure 2 of 23 August 2026.  If `righe_registro()` returns 0 (the `< file`
    #      that stole the password from `sudo -S`), `conti_del_server()` would read the
    #      log FROM THE SERVER'S STARTUP: `attese_a_vuoto` would become
    #      cumulative, and with it the column on which `p_I1` decides whether to refuse.
    #      ⇒ The bench must REFUSE, not go straight on.  ⭐ And the refusal is
    #        tested on the REAL function — `conti_del_server(0)` — not on a dictionary
    #        written by hand: it is the guard on the path the real run takes.
    casi.append(("6b-⛔⛔ the log NOT read (righe_registro() → 0): the server's "
                 "counts would be cumulative from startup",
                 misura(_fab([(30, 33)]), 33, conti_del_server(0), FILO),
                 {"the log": None, "no drop": True, "the floor": True,
                  "degrades in time": True, "the delay": True}))

    # 6c · ⛔⛔ THE THIRD FACE OF THE ZERO, and the REAL run of
    #      23 August 2026 found it: the §11.1 reader does not start (it was missing
    #      `01-b4-validatore.py` in the tree), the journal stays empty, and an
    #      empty journal is identical to «the session delivered nothing».
    #      `[M]` that evening the bench gave RED to «does not drop» on a run in
    #      which the server had sent **797** frames and the client had
    #      taken them.  ⇒ «I did not read it» must refuse, not accuse the product.
    #      ⚠ And the comparison with case 6 is the point: **same empty journal**,
    #        opposite outcomes, because the reason for the emptiness is different.
    n_muta = misura([], 33, SRV, FILO)
    n_muta["traccia_non_letta"] = "⛔ THE §11.1 TRACE WAS NOT READ: test"
    n_muta["esito"] = "NON HO NIENTE DA GIUDICARE — trace not read"
    casi.append(("6c-⛔⛔ the journal empty because I DID NOT READ IT (against "
                 "case 6, empty because nothing arrived)",
                 n_muta,
                 {"the log": True, "no drop": None, "the floor": None,
                  "degrades in time": None, "the delay": None}))

    verde = True
    for nome, n, atteso in casi:
        print("  %s" % nome)
        for etichetta, f, _s in PREDICATI_GIRO:
            corto = etichetta.split(" (")[0]
            chiave = ("the log" if corto.startswith("the log") else
                      "no drop" if corto.startswith("does not drop") else
                      "the floor" if corto.startswith("the rate floor") else
                      "degrades in time" if corto.startswith("degrades") else
                      "the delay")
            passa, perche = f(n)
            att = atteso[chiave]
            bene = (passa is att)
            verde = verde and bene
            segno = ("OK " if bene else "⛔ ")
            print("      %s%-22s expected %-5s seen %-5s — %s"
                  % (segno, chiave, att, passa, perche[:96]))
        print()

    # ── THE I1 PAIR, which needs two runs and not one ───────────────────────
    print("  ── I1, and it needs the PAIR: still scene / moving scene ──\n")
    srv = lambda cons, sped, abb=0: {"consegnati": cons, "spediti": sped,
                                     "abbandonati": abb, "non_spediti": cons - sped,
                                     "annunci_tela": 0}
    coppie = [
        # 7 · ⭐ I1 HEALTHY: same cadence, no abandonments.
        ("7-⭐ I1 healthy: still 30/s and moving 30/s, delivered comparable",
         misura(_fab([(30, 33)]), 33, srv(1000, 1000), FILO),
         misura(_fab([(30, 33)]), 33, srv(1010, 1010), FILO),
         True),
        # 8 · ⛔ THE DEFECT THE PHASE EXISTS TO FIND: with the scene still the
        #     rate drops, and the compositor delivered to us all the same.
        ("8-⛔⛔ I1 broken: still 18/s against moving 30/s, delivered equal",
         misura(_fab([(18, 33)]), 33, srv(1000, 620, 40), FILO),
         misura(_fab([(30, 33)]), 33, srv(1010, 1010), FILO),
         False),
        # 9 · ⭐⭐ THE FALSE RED, and it is the case without which this bench
        #     would accuse the product of a defect of the COMPOSITOR.  Same
        #     rates as case 8 — but with the scene still Mutter delivered 550
        #     frames against 1 010.  ⇒ I DO NOT JUDGE, and not «red».
        ("9-⭐⭐ the false red: same rates, but with the scene still the compositor "
         "delivered 550 against 1 010",
         misura(_fab([(18, 33)]), 33, srv(550, 550), FILO),
         misura(_fab([(30, 33)]), 33, srv(1010, 1010), FILO),
         None),
        # 10 · ⛔ THE MUTE PAIR: one of the two runs did not measure.
        ("10-⛔ the incomplete pair: the still-scene run has no frames",
         misura([], 33, srv(1000, 1000), FILO),
         misura(_fab([(30, 33)]), 33, srv(1010, 1010), FILO),
         None),
        # 10b · ⭐⭐ THE SECOND FALSE RED, and this time the «delivered»
        #      look alike — the first guard would let it through.  What says so is
        #      the column the child writes by itself: **900 empty waits**
        #      with the scene still against 3 with the scene moving.  ⇒ I DO NOT JUDGE.
        ("10b-⭐⭐ the false red the «delivered» do not see: 900 EMPTY "
         "waits with the scene still (the frame was not there)",
         misura(_fab([(18, 33)]), 33,
                dict(srv(950, 950), cattura={"catturati": 950, "chiavi": 1,
                                             "attese_a_vuoto": 900}), FILO),
         misura(_fab([(30, 33)]), 33,
                dict(srv(1010, 1010), cattura={"catturati": 1010, "chiavi": 1,
                                               "attese_a_vuoto": 3}), FILO),
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
         _con_linea(misura(_fab([(10.13, 33)]), 33, srv(1000, 960, 40), FILO), 0.0),
         _con_linea(misura(_fab([(7.78, 33)]), 33, srv(1010, 1010), FILO), 0.0),
         False),
        # 10d · ⭐⭐ THE CASE MEASURED ON 23 AUGUST 2026 on `casa-cattiva` (2 %
        #      loss): **the very same numbers** as 10c.  The premise
        #      *«with a still scene there is no congestion that justifies them»* here is
        #      FALSE — the abandonments are justified by the loss.  ⇒ I DO NOT JUDGE.
        #      ⛔ And the red this case removes is not a red of the product.
        ("10d-⭐⭐ the SAME numbers on a line that loses 2 %: the premise "
         "is false and the bench must REFUSE, not give red",
         _con_linea(misura(_fab([(10.13, 33)]), 33, srv(1000, 960, 40), FILO), 2.0),
         _con_linea(misura(_fab([(7.78, 33)]), 33, srv(1010, 1010), FILO), 2.0),
         None),
        # 10e · ⛔ And «I do not know whether it loses» is NOT «it does not lose»: an
        #      unverified premise does not give the right to give red (§1.9, again).
        ("10e-⛔ the same numbers on a line of which I do NOT KNOW whether it loses: "
         "an unverified premise does not authorise a red",
         misura(_fab([(10.13, 33)]), 33, srv(1000, 960, 40), FILO),
         misura(_fab([(7.78, 33)]), 33, srv(1010, 1010), FILO),
         None),
        # 10f · ⛔⛔ AND THE CURE MUST NOT BECOME AN AMNESTY.  Line losing
        #      2 %, but this time the rate with the scene still DROPS (5.0/s against 7.78):
        #      loss explains the abandonments, it does not explain that.  ⇒ RED.
        ("10f-⛔⛔ line losing 2 % BUT the rate with the scene still drops "
         "(5.00/s against 7.78/s): loss does not justify it — RED",
         _con_linea(misura(_fab([(5.0, 33)]), 33, srv(1000, 960, 40), FILO), 2.0),
         _con_linea(misura(_fab([(7.78, 33)]), 33, srv(1010, 1010), FILO), 2.0),
         False),
    ]
    for nome, ferma, mossa, att in coppie:
        passa, perche = p_I1(ferma, mossa)
        bene = (passa is att)
        verde = verde and bene
        print("  %s%s\n      expected %-5s seen %-5s — %s"
              % ("OK  " if bene else "⛔  ", nome, att, passa, perche[:150]))
    print()

    # 11 · ⛔ THE WIRE NOT READ — `CODER.md` §3.10.  If the qdisc counter
    #      could not be read, the bench must say «not read», not «0».
    n = misura(_fab([(30, 33)]), 33, SRV, None)
    bene = (n.get("mbit_s_filo") is None and "filo_non_letto" in n)
    verde = verde and bene
    print("  %s11-⛔ the wire counter not read: it says «not read», not "
          "«0 Mbit/s» — seen mbit_s_filo=%s"
          % ("OK  " if bene else "⛔  ", n.get("mbit_s_filo")))

    # 12 · ⭐ THE SECOND LEG OF THE ABANDONMENTS: the gaps in `numero`, which are
    #      read from the RECEIVING side and do not go through the server's log.
    n = misura(_fab([(30, 33)], salta_ogni=25), 33, SRV, FILO)
    atteso_buchi = (n["fotogrammi"] // 25)
    bene = n["buchi_numero"] >= atteso_buchi - 2
    verde = verde and bene
    print("  %s12-⭐ the gaps in the `numero` sequence (§6.2): expected ~%d, "
          "seen %d" % ("OK  " if bene else "⛔  ", atteso_buchi, n["buchi_numero"]))

    # 13 · ⭐⭐ THE WHOLE LOOP OF THE TOOL: from the trace to the journal.
    #      Cases 0-12 test the REDUCTION on ready-made journals; this one tests
    #      the piece that builds them — the §11.1 reader — and tests it **on the
    #      code that will be sent to the machine**, not on a copy.
    #      ⛔ And the format of the fake trace is not written by me: I take it
    #        from the REFEREE (`01-b4-validatore.py`), which is the only place where
    #        §11.1 is written.  A test in which I write and reread MY format
    #        would prove nothing about the real format.
    bene, perche = _certifica_lettore()
    verde = verde and bene
    print("  %s13-⭐⭐ from the §11.1 TRACE to the journal, with the real reader: %s"
          % ("OK  " if bene else "⛔  ", perche))

    # 14-15 · ⛔⛔ THE TWO CURES OF `sudo -S`'s STDIN, tested FOR REAL.
    verde = _certifica_stdin_di_sudo() and verde

    print("\n== %s" % ("⭐ THE BENCH CAN SEE THE DEFECTS IT LOOKS FOR"
                       if verde else
                       "⛔⛔ THE BENCH CANNOT SEE WHAT IT LOOKS FOR: none of "
                       "its greens is to be believed"))
    return 0 if verde else 1


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
SUDO_FINTO = r'''#!/bin/sh
# ⛔ The fake `sudo`: it gives no privileges, it imitates only the stdin of `-S`.
while [ "$1" = "-S" ] || [ "$1" = "-p" ]; do
  if [ "$1" = "-p" ]; then shift 2; else shift; fi
done
printf '%s\n' "$*" >> "$FINTO_CHIAMATE"
IFS= read -r parola || parola=""
if [ "$parola" != "$FINTO_PAROLA" ]; then
  echo "sudo: 3 incorrect password attempts" >&2
  exit 1
fi
exec "$@"
'''


def _certifica_stdin_di_sudo():
    """Cases 14 and 15: the two forms in which `sudo -S` loses the password."""
    import shutil, tempfile
    d = tempfile.mkdtemp(prefix="09-b70-sudo-")
    bidone = os.path.join(d, "bidone")
    os.makedirs(bidone)
    with open(os.path.join(bidone, "sudo"), "w") as f:
        f.write(SUDO_FINTO)
    os.chmod(os.path.join(bidone, "sudo"), 0o755)
    chiamate = os.path.join(d, "chiamate")

    def gira(riga):
        open(chiamate, "w").close()
        amb = dict(os.environ, PATH=bidone + ":" + os.environ.get("PATH", ""),
                   FINTO_CHIAMATE=chiamate, FINTO_PAROLA=PAROLA_SUDO)
        p = subprocess.run(["bash", "-c", riga], capture_output=True, env=amb)
        return (p.returncode, p.stdout.decode("utf-8", "replace"),
                open(chiamate).read().strip().splitlines())

    def vecchia(comando):
        """The form of `07-b65-datagram.py:147`: a single `sudo`, and the chain OUTSIDE."""
        return "printf '%%s\\n' '%s' | sudo -S -p '' %s" % (PAROLA_SUDO, comando)

    verde = True

    # ── 14 · THE CHAIN — `sudo` covers only the FIRST link ──────────────────
    dentro = os.path.join(d, "dentro")
    catena = ("mkdir -p %s && printf '%%s' 'CIAO' > %s/f && wc -c < %s/f"
              % (dentro, dentro, dentro))
    _rc, out_v, ch_v = gira(vecchia(catena))
    shutil.rmtree(dentro, ignore_errors=True)
    _rc, out_n, ch_n = gira(catena_root(catena))
    # ⛔ The old form: `sudo` received ONLY the `mkdir`; the `printf`, the
    #    `>` and the `wc` ran as a normal user — and on the machine, where
    #    `LAV` belongs to root, that is where the §11.1 reader was not written.
    rotta = (len(ch_v) == 1 and "mkdir" in ch_v[0] and "printf" not in ch_v[0])
    # ⭐ The new form: a single `sudo`, and the WHOLE chain inside its shell.
    curata = (len(ch_n) == 1 and ch_n[0].startswith("bash -c ")
              and "mkdir" in ch_n[0] and "printf" in ch_n[0] and "wc" in ch_n[0]
              and out_n.strip() == "4")
    bene = rotta and curata
    verde = verde and bene
    print("  %s14-⛔ CURE 1 · the CHAIN: the old form sends to root only "
          "«%s…» (the rest runs as user); the new one sends a single one, with "
          "the whole chain inside — and prints «%s» (expected «4»)"
          % ("OK  " if bene else "⛔  ",
             (ch_v[0] if ch_v else "(nothing)")[:24], out_n.strip()))

    # ── 15 · THE TRAILING `< file` — it steals stdin from `sudo`, and KEEPS QUIET ─
    reg = os.path.join(d, "registro.log")
    with open(reg, "w") as f:
        f.write("prima riga\nseconda\nterza\nquarta\n")
    comando = "wc -l < %s 2>/dev/null || echo 0" % reg
    rc_v, out_v, _ch = gira(vecchia(comando))
    rc_n, out_n, _ch = gira(catena_root(comando))
    # ⛔⛔ The old form prints «0» — not «error»: it is the MUTE defect, and it is
    #     the one that made `attese_a_vuoto` cumulative from startup.
    rotta = (out_v.strip() == "0")
    curata = (out_n.strip() == "4")
    bene = rotta and curata
    verde = verde and bene
    print("  %s15-⛔⛔ CURE 2 · the trailing «< file» on a 4-line log: "
          "the old form answers «%s» (stdin stolen from sudo, and it KEEPS QUIET), the "
          "new one «%s»"
          % ("OK  " if bene else "⛔  ", out_v.strip(), out_n.strip()))

    # ── 15b · THE GUARD: a zero must not have the face of a measurement ─────
    vero_root = globals()["root"]
    try:
        prove = [
            ("zero lines with the server on", (0, "0\n", ""), None),
            ("sudo refusing the password", (1, "", "sudo: 3 incorrect password "
                                                   "attempts"), None),
            ("an answer that is not a number", (0, "boh\n", ""), None),
            ("a real log of 12 345 lines", (0, "12345\n", ""), 12345),
        ]
        esiti = []
        for etichetta, risposta, atteso in prove:
            globals()["root"] = lambda c, tetto=300, r=risposta: r
            visto = righe_registro()
            esiti.append((etichetta, atteso, visto, visto == atteso))
    finally:
        globals()["root"] = vero_root
    bene = all(e[3] for e in esiti)
    verde = verde and bene
    print("  %s15b-⭐ the guard of `righe_registro()`: %s"
          % ("OK  " if bene else "⛔  ",
             " · ".join("%s → %s%s" % (e[0], e[2], "" if e[3] else
                                       " ⛔ EXPECTED %s" % e[1]) for e in esiti)))
    shutil.rmtree(d, ignore_errors=True)
    return verde


def _certifica_lettore():
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
            "b4cert", os.path.join(QUI, "01-b4-validatore.py"))
        A = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(A)
    except Exception as e:
        return False, "the §11.1 referee could not be imported: %s" % e

    blocchi = []      # (direction, channel, end, instant, stream, payload, redacted)

    def testa(numero, chiave, istante_us):
        return struct.pack("!HHIIIQI", 0x0301 if chiave else 0x0302, 3,
                           1920, 1080, numero, istante_us, 0)

    # noise that is NOT video: control channel, and a block from the client
    blocchi.append((A.CLIENT, 0x00, A.CONTINUA, 0, 0, b"\x00" * 12, []))
    blocchi.append((A.SERVER, 0x00, A.CONTINUA, 1, 0, b"\x00" * 12, []))

    atteso = []
    stream, istante_ms = 4, 10
    for k in range(6):
        chiave = (k == 0)
        cat = k * 33000                       # µs, the server's clock
        t = testa(k + 1, chiave, cat)
        if k == 3:
            # ⛔ ABANDONED (§5.1 form A): it is not a delivered frame.
            blocchi.append((A.SERVER, 0x03, A.CONTINUA, istante_ms, stream,
                            t + b"\x11" * 50, []))
            blocchi.append((A.SERVER, 0x03, A.RESET, istante_ms + 1, stream,
                            b"", []))
        else:
            # ⭐ the header across TWO blocks
            blocchi.append((A.SERVER, 0x03, A.CONTINUA, istante_ms, stream,
                            t[:12], []))
            corpo = b"\x22" * 500
            osc = []
            if k == 2:
                # a redacted interval: 40 bytes in the middle of the file
                osc = [(0, 8, hashlib.sha256(b"\x22" * 8).digest())]
            blocchi.append((A.SERVER, 0x03, A.CONTINUA, istante_ms, stream,
                            t[12:] + corpo[:200], osc))
            blocchi.append((A.SERVER, 0x03, A.FIN, istante_ms + 2, stream,
                            corpo[200:], []))
            atteso.append({"numero": k + 1, "chiave": chiave,
                           "byte": 500, "arrivo_ms": istante_ms + 2,
                           "istante_us": cat})
        stream += 4
        istante_ms += 33

    out = bytearray(A.MAGIA + struct.pack("!IBBBB", len(blocchi), 1, 0, 0, 0))
    for verso, canale, fine, ist, sid, carico, osc in blocchi:
        out += struct.pack(A.BLOCCO, verso, canale, fine, ist, sid,
                           len(carico), len(osc))
        for ini, qua, imp in osc:
            out += struct.pack("!II", ini, qua) + imp
        out += carico

    d = tempfile.mkdtemp(prefix="09-b70-")
    tr, le = os.path.join(d, "t.rcpreg"), os.path.join(d, "leggi.py")
    with open(tr, "wb") as f:
        f.write(bytes(out))
    with open(le, "w") as f:
        f.write(LETTORE)
    p = subprocess.run([sys.executable, le, tr,
                        os.path.join(QUI, "01-b4-validatore.py")],
                       capture_output=True)
    import shutil
    shutil.rmtree(d, ignore_errors=True)
    try:
        letto = json.loads(p.stdout.decode())
    except Exception as e:
        return False, "the reader did not answer: %s — %s" % (
            e, (p.stdout + p.stderr).decode("utf-8", "replace")[-200:])
    g = letto.get("giornale") or []
    if letto.get("azzerati") != 1:
        return False, ("the abandonment with RESET_STREAM was not counted "
                       "apart: azzerati = %s" % letto.get("azzerati"))
    if len(g) != len(atteso):
        return False, ("%d frames in the journal, I expected %d "
                       "(the RESET is not a delivered frame)"
                       % (len(g), len(atteso)))
    for visto, att in zip(g, atteso):
        for chiave, valore in att.items():
            if visto.get(chiave) != valore:
                return False, ("frame %s: «%s» is %s, I expected %s"
                               % (att["numero"], chiave, visto.get(chiave), valore))
    # ⭐ And the tail of the run: five frames are FEW, and the reduction must
    #    SAY so instead of computing a rate on a handful of samples.
    n = misura(g, 1, None, None, scaldata_s=0.0)
    if n.get("esito") == "misurato":
        return False, ("the reduction measured a rate on %d frames, "
                       "below the minimum of %d: it should have refused"
                       % (len(g), MINIMO_FOTOGRAMMI))
    return True, ("%d frames read (1 keyframe, %d deltas), 1 abandonment with "
                  "RESET counted apart, redacted and non-video blocks skipped; "
                  "and the reduction refuses to compute a rate with so few"
                  % (len(g), len(atteso) - 1))


# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT TALKS TO THE TEST MACHINE
# ═══════════════════════════════════════════════════════════════════════════
RETE = None       # the 07-b65 module, imported in `principale()`


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔⛔ THE TRAP OF `sudo -S`'s STDIN, AND THIS PROJECT HAS ALREADY PAID FOR IT
#       THREE TIMES — it is written here so the fourth is not paid
# ═══════════════════════════════════════════════════════════════════════════
#
# `07-b65-datagram.py:147` builds, and it is perfectly fine for ONE command only:
#
#       printf '%s\n' 'PAROLA' | sudo -S -p '' <comando>
#
# ⛔ **FIRST FORM — the chain.**  The command that arrives in there is not a
#    command: it is a CHAIN (`a && b | c > d`).  The remote shell splits it
#    **outside** `sudo`, and `sudo` covers only the FIRST link.  The following
#    links run as a normal user — and if they write in `LAV`, which belongs to
#    root, they fail.  ⚠ And they fail **in silence**, because the `|| echo 0`
#    or the `; true` that goes with them turns the error into a plausible number.
#    `[M]` 23 August 2026: `spedisci_lettore()` did not write `09-b70-leggi.py`
#    on the machine, and §11.1 stayed without a reader.
#
# ⛔⛔ **SECOND FORM — and the worst, because it is MUTE.**  A trailing `< file`
#      is not taken by the command: it is taken by **`sudo`**, which is the last command
#      of the pipeline.  ⇒ The password no longer reaches `sudo`'s stdin,
#      the file does; `sudo` answers *«3 incorrect password attempts»* on
#      stderr, exits 1, and the trailing `|| echo 0` prints **0**.
#      ⚠ It is written in black and white in `07-b64-terreno.sh` (~line 240) — *«no
#        trailing `</dev/null`: that redirect wins over `sudo -S`»* — and it came back
#        here all the same: `[M]` 23 August 2026, `righe_registro()` returned **0** on
#        a log of thousands of lines, and then `conti_del_server()` read
#        **from the server's startup** instead of from this run.  The «final
#        count» lines were saved (there is a `tail -1`), the `ciclo:` lines were not:
#        `catturati` and **`attese a vuoto`** became CUMULATIVE — that is the
#        column on which `p_I1` decides whether to refuse to judge.
#
# ⇒ **THE CURE, and it is a single one for both**: a single `sudo`, and the whole
#   chain inside ITS shell.  `sudo` stays the only command of the `printf`
#   pipeline, so the password reaches it; and every `|`, `&&`, `<` and `>` of the
#   chain lives inside `bash -c`, that is inside root.
#
#       printf '%s\n' 'PAROLA' | sudo -S -p '' bash -c '<whole chain>'
#
# ⚠ And the price is declared: inside the single quotes of `shlex.quote` the `$`
#   is NO longer expanded by the remote shell.  No command in this file
#   relies on that expansion, and whoever added one must know it.
def catena_root(comando):
    """The line that leaves over ssh: **one** `sudo`, and the chain inside its shell."""
    return ("printf '%%s\\n' '%s' | sudo -S -p '' bash -c %s"
            % (PAROLA_SUDO, shlex.quote(comando)))


def root(comando, tetto=300):
    """⛔ It is NOT `RETE.root`: that one covers only the first link of the chain.

    ⚠ And whoever replaces this function from outside to transcribe (as
      `09-b79-cure.py:415` does) must wrap **this one**, not `RETE.root`, or
      both the defects cured above come back in.
    """
    return RETE.rem(catena_root(comando), tetto)


def spedisci_lettore():
    """⛔ The reader is sent in base64: the quotes of a heredoc inside
       a `sudo -S` inside an `ssh` are three levels of quoting, and a wrong one
       does not give an error — it gives a truncated file.

    ⛔⛔ And the chain is ONE SINGLE call to `root()`: `mkdir`, `printf`,
        `base64 -d` and the `>` all live inside the same root shell (see
        the trap written above).  `[M]` 23 Aug 2026: in the old form
        the `>` belonged to the user's shell and the file was never written.
    """
    b = base64.b64encode(LETTORE.encode("utf-8")).decode("ascii")
    root("mkdir -p %s && printf '%%s' '%s' | base64 -d > %s/09-b70-leggi.py"
         % (LAV, b, LAV))
    # ⛔ `wc -c < file` is fine ONLY because the redirect is now inside the
    #    root shell: it is root that opens the file, and `sudo`'s stdin stays the
    #    password.  In the old form this `<` stole the password and the bench
    #    said «it was not written» of a file that was there (2 198 bytes measured).
    rc, out, _ = root("wc -c < %s/09-b70-leggi.py" % LAV)
    return out.strip().isdigit() and int(out.strip()) > 1000


def terreno_controlla():
    """⛔ The bench refuses to measure on a ground that is not its own.

    ⚠ And it counts the listeners NOT its own without touching them: `LEZIONI.md` §1.26 —
      two benches on the same machine do not give a red, they give **a plausible
      number**.
    """
    _log("THE GROUND — port %d · user %s (uid %d) · tree %s"
         % (PORTA, UTENTE, UID_B, ALB))
    guai = []
    rc, out, _ = root("id %s >/dev/null 2>&1 && echo si || echo no" % UTENTE)
    if "si" not in out:
        guai.append("the user «%s» does not exist: "
                    "PORTA=%d UTENTE=%s UID_B=%d ALBERO=%s LAV=%s "
                    "bash banchi/07-b64-terreno.sh utente"
                    % (UTENTE, PORTA, UTENTE, UID_B, ALB, LAV))
    rc, out, _ = root("test -s %s/parola && echo si || echo no" % LAV)
    if "si" not in out:
        guai.append("%s/parola (0600) is missing: D12 forbids the password in argv" % LAV)
    rc, out, _ = root("test -d %s/banchi && echo si || echo no" % ALB)
    if "si" not in out:
        guai.append("the tree «%s» is not there: it is aligned with "
                    "banchi/attrezzi-allinea-innesto.sh" % ALB)
    # ⛔⛔ THE §11.1 REFEREE, and it is checked BEFORE measuring.  `[M]` 23 August
    #     2026: `07-b64-terreno.sh porta` carries only a handful of `banchi/`, and
    #     `01-b4-validatore.py` was not among them — the trace reader
    #     died at every run, the journal stayed empty, and the bench gave RED to
    #     «does not drop» on a session alive with 797 frames.  ⇒ A missing file
    #     is said here, where it costs one line, not when the run is over.
    rc, out, _ = root("test -s %s/banchi/01-b4-validatore.py && echo si || echo no"
                      % ALB)
    if "si" not in out:
        guai.append("the §11.1 referee «%s/banchi/01-b4-validatore.py» is missing: "
                    "without it, the trace reader does not start and every run "
                    "looks like a dead session — copy it with "
                    "«scp banchi/01-b4-validatore.py» into the tree" % ALB)
    rc, out, _ = root("test -x %s && echo si || echo no" % SCENA_BIN)
    if "si" not in out:
        guai.append("the scene «%s» is not executable: 04-b30-scena must be "
                    "built" % SCENA_BIN)
    rc, out, _ = root("ss -tuln 2>/dev/null | grep -c ':%d ' || true" % PORTA)
    mio = out.strip()
    rc, out, _ = root("uptime")
    _inf("load: %s" % out.strip()[-40:])
    conto = []
    for p in VICINE:
        rc, o, _ = root("ss -tuln 2>/dev/null | grep -c ':%s ' || true" % p)
        conto.append("%s:%s" % (p, o.strip()))
    _inf("listeners NOT mine (counted, not touched): %s" % " ".join(conto))
    _inf("my server on %d: %s listener(s)" % (PORTA, mio))
    if mio == "0":
        guai.append("nobody is listening on %d: "
                    "PORTA=%d UTENTE=%s UID_B=%d ALBERO=%s LAV=%s "
                    "bash banchi/07-b64-terreno.sh accendi" % (PORTA, PORTA, UTENTE,
                                                               UID_B, ALB, LAV))
    if not spedisci_lettore():
        guai.append("the trace reader was not written in %s" % LAV)
    for g in guai:
        _ko(g)
    if not guai:
        _ok("the ground is there, and it is mine")
    return not guai


def righe_registro():
    """How many lines the server log has NOW — or `None` if I did not read it.

    ⛔⛔ **A ZERO THAT MEANS «I DID NOT READ» AND A ZERO THAT MEANS «NOTHING
        HAPPENED» MUST NOT HAVE THE SAME FACE** (`LEZIONI.md` §1.9).
        Here the face was the same and the price was the one written above
        `catena_root()`: the number came back 0, `conti_del_server()` read the
        log **from the server's startup**, and `attese_a_vuoto` — the column
        with which `p_I1` decides whether to refuse — became cumulative.

    ⇒ Three outcomes, not two:
        · an integer > 0  — I read it;
        · `None`         — ⛔ I DID NOT READ IT (the command failed, or the
          answer is not a number);
        · `None` also at **zero lines**: the server is on (`terreno_controlla()`
          checks it before measuring) and a server that is on has necessarily already
          written.  A zero, here, is a failed read disguised as a measurement.

    ⚠ And no trailing `|| echo 0`: that fallback is precisely the piece that
      turned the error into a plausible number.  If it fails, it must show.
    """
    rc, out, err = root("wc -l < %s/registro.log" % LAV)
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


def conti_del_server(riga0):
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
          `righe_registro()`: so it holds even when someone else replaces
          that function with one that returns 0 instead of `None`
          (`09-b76-rete-cattiva.py:1126` does).
    """
    if riga0 is None or riga0 <= 0:
        return {"registro_non_letto":
                "⛔ the server log was not read (starting line "
                "«%s»): without the starting line the counts would be CUMULATIVE "
                "from startup, not of this run" % riga0}
    # ⚠ Since 23 August 2026 the server also writes a `rete-quic …
    #   giudizio=…` line once per second (`src/webtransport.c:3986`).  ⭐ It does not
    #   confuse any of the `grep`s below — it carries no «final count», nor
    #   «figlio  loop:», nor the four sentences of the spiral — and since the
    #   start is a LINE NUMBER, new lines in the log move
    #   nothing.  Whoever adds a `grep` here must check again.
    fuori = {"riga0": riga0}
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -a 'video of .*final "
                      "count' | tail -1" % (riga0 + 1, LAV))
    m = re.search(r"(\d+) frames delivered.*?(\d+) NOT SENT.*?"
                  r"(\d+) sent on the wire.*?(\d+) abandoned.*?and (\d+) ANNOUNCEMENTS",
                  out.strip())
    if m:
        fuori.update({"consegnati": int(m.group(1)), "non_spediti": int(m.group(2)),
                      "spediti": int(m.group(3)), "abbandonati": int(m.group(4)),
                      "annunci_tela": int(m.group(5))})
    else:
        # ⛔ `CODER.md` §3.10: «I did not read» is not «zero».
        fuori["esito_video"] = "NIENTE DA LEGGERE — no video «final count»"
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -a 'audio of .*final "
                      "count' | tail -1" % (riga0 + 1, LAV))
    m = re.search(r"(\d+) blocks sent, (\d+) dropped.*?(\d+) refused.*?"
                  r"(\d+) DEFERRED", out.strip())
    if m:
        # ⚠ They are read and printed, but NOT judged: the sound judge
        #   is `07-b64-orecchio.py`, and the question «who pays between audio and video»
        #   is already closed by `07-b65`.
        fuori["audio"] = {"spediti": int(m.group(1)), "buttati": int(m.group(2)),
                          "rifiutati": int(m.group(3)), "rimandati": int(m.group(4))}
    # ⭐⭐ AND THE CAPTURE SIDE, which is the column WITHOUT WHICH I1 CANNOT BE JUDGED.
    #
    # ⛔ The child's `loop:` line (`figlio.c:6842`) carries, cumulative and once
    #    per second, «N frames delivered (K keyframes), M **empty
    #    waits**» — and the product itself explains what it means: *«still
    #    scene: Mutter delivers only when something changes»*.
    #
    # ⭐ This column was taught to me by `banchi/09-b68-ritmo.py`, by another
    #    agent, on 23 August: it is a **better** discriminator than the
    #    `spediti/consegnati` ratio I had written first, because it does not deduce —
    #    it says that we ASKED for a frame and there was none.  ⇒ «Mutter
    #    does not deliver» and «we were not lowering the rate» stop having the same
    #    look, which is exactly the trap of `04-b32-ritmo.py`.
    r = re.compile(r"loop: (\d+) frames delivered \((\d+) keyframes\), "
                   r"(\d+) empty waits")
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -a 'figlio  loop:'"
                      % (riga0 + 1, LAV))
    righe = r.findall(out)
    if len(righe) >= 2:
        p0, p1 = righe[0], righe[-1]
        fuori["cattura"] = {"catturati": int(p1[0]) - int(p0[0]),
                            "chiavi": int(p1[1]) - int(p0[1]),
                            "attese_a_vuoto": int(p1[2]) - int(p0[2]),
                            "righe_ciclo": len(righe)}
    else:
        fuori["cattura"] = {"esito": "NIENTE DA LEGGERE — fewer than two "
                                     "«loop:» lines in this run"}
    # ⭐ AND THE LINES OF THE SPIRAL, counted: they are the bridge between the numbers of this
    #    page and the cause named in `fasi/09...` §0.3.
    for etichetta, aco in (
            ("chiave_aspetta", "§5.2 forbids abandoning it"),
            ("delta_non_spedito", "FRAME NOT SENT"),
            ("abbandonato_in_coda", "ABANDONED IN THE QUEUE"),
            ("involo_pieno", "can NOT be abandoned")):
        rc, out, _ = root("tail -n +%d %s/registro.log | grep -ac '%s' || true"
                          % (riga0 + 1, LAV, aco))
        fuori.setdefault("spirale", {})[etichetta] = (
            int(out.strip()) if out.strip().isdigit() else None)
    return fuori


def scena_accendi(movimento):
    """⭐ «Still scene» = `--movimento marca`, NOT the scene off.

    ⛔ With the scene off the compositor delivers very little, and the two runs of the
       pair are not comparable: a low rate upstream looks in every way like
       a rate lowered by us.  With `marca` only the mark changes — the capture
       cadence stays that of the moving run, and what changes is the COST, which is
       the only thing I1 wants to isolate.
    """
    scena_spegni()
    rc, out, _ = root("grep -ao 'monitor «[^»]*»' %s/registro.log | tail -1" % LAV)
    m = re.findall("monitor «([^»]*)»", out)
    usc = m[-1] if m and m[-1] else None
    if not usc:
        return None
    root("setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
         "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
         "XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 "
         "%s --uscita %s --movimento %s --shm /09-b70 --giro b70 "
         ">/dev/null 2>&1 & echo acceso"
         % (UID_B, UID_B, UTENTE, UTENTE, UID_B, SCENA_BIN, usc, movimento))
    time.sleep(1.5)
    rc, out, _ = root("pgrep -u %d -f '04-b30-scena --uscita' | head -1" % UID_B)
    return usc if out.strip() else None


def scena_spegni():
    root("pkill -u %d -f 04-b30-scena; true" % UID_B)


def innesca_sessione(secondi=8):
    """⛔ The stage and the monitor are born with the FIRST client: on a freshly
       started server the log does not yet carry the monitor name, and the scene would not
       know where to draw.  ⇒ A short session is opened on purpose; the stage
       outlives it (I4)."""
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s/parola --audio-codec pcm "
              "--video-codec %s --adatta %s --resta %d"
              % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, CODEC_CHIESTO,
                 TELA_PIENA, secondi))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro,
                        secondi + 180)
    return "SESSIONE" in (out + err)


def _linea_del_giro():
    """⭐ The loss of the line is READ from the installed qdisc, not assumed.

    ⛔ Assuming it would be worse than the defect it cures: `09-b76-rete-cattiva.py`
       calls this same `giro()` with a `netem` that **loses**, and a
       «loss 0» written by hand here would put back on its feet exactly the false
       red of `p_I1` that is being removed.  ⇒ We look at what is really there.

    ⚠ And if the qdisc cannot be read, `None` is written — which means «I do not know»,
      and `p_I1` then refuses instead of giving red.
    """
    try:
        testo = RETE.qdisc() or ""
    except Exception as e:
        return {"perdita_pc": None, "come": "the qdisc was not read: %s" % e}
    if "netem" not in testo:
        return {"perdita_pc": None, "come": "no netem on the device: the "
                                            "line is not the one I think",
                "qdisc": testo[:200]}
    # `loss 1%` (independent) or `loss gemodel p 0.2% r 20% …` (bursty)
    m = re.search(r"loss\s+(?:gemodel\s+p\s+)?([\d.]+)%", testo)
    return {"perdita_pc": float(m.group(1)) if m else 0.0,
            "come": ("netem with «%s»" % m.group(0)) if m else
                    "netem without `loss`: the only possible loss is the queue "
                    "overflowing",
            "qdisc": testo[:200]}


def giro(nome, movimento, tela, secondi, con_traccia=True):
    """One run: the client inside the container, the trace reduced on the spot."""
    root("rm -f %s/%s.rcpreg %s/%s.json; true" % (LAV, nome, LAV, nome))
    # ⛔ `None` (or 0) here means «I did not read the log», and from then on
    #    the server's counts would be cumulative from startup: the guard sits
    #    inside `conti_del_server()`, which refuses instead of reading everything.
    riga0 = righe_registro()
    linea = _linea_del_giro()
    prima = RETE.byte_sul_filo()
    t0 = time.time()
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s/parola --audio-codec pcm "
              "--video-codec %s --adatta %s %s--resta %d"
              % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, CODEC_CHIESTO, tela,
                 ("--registra %s/%s.rcpreg " % (DENTRO_LAV, nome)) if con_traccia else "",
                 secondi))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro,
                        secondi + 300)
    dopo = RETE.byte_sul_filo()
    vero = time.time() - t0
    testo = out + err
    # ⭐ The count the CLIENT prints by itself, which is independent of the
    #    trace: it is with this one that the witness's weight is unmasked.
    dal_cliente = None
    for x in testo.splitlines():
        m = re.search(r"\[vid\]\s+(\d+) frames \((\d+) keys\)", x)
        if m:
            dal_cliente = {"fotogrammi": int(m.group(1)), "chiavi": int(m.group(2))}
    filo = None
    if prima and dopo:
        b, pk = dopo[0] - prima[0], dopo[1] - prima[1]
        filo = {"byte": b, "pacchetti": pk, "secondi": vero,
                "byte_per_pacchetto": round(b / pk, 1) if pk else None}
    server = conti_del_server(riga0)
    giornale, letto, muta = [], {"esito": "senza traccia"}, None
    if con_traccia:
        rc, out2, err2 = root("python3 %s/09-b70-leggi.py %s/%s.rcpreg "
                              "%s/banchi/01-b4-validatore.py"
                              % (LAV, LAV, nome, ALB), 600)
        try:
            letto = json.loads(out2)
            giornale = letto.pop("giornale", [])
        except Exception as e:
            letto = {"esito": "the reader did not answer: %s — %s"
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
            muta = ("⛔ THE §11.1 TRACE WAS NOT READ: %s" % letto["esito"])
    n = misura(giornale, secondi, server, filo,
               azzerati=letto.get("azzerati"))
    if muta:
        n["traccia_non_letta"] = muta
        n["esito"] = "NON HO NIENTE DA GIUDICARE — " + muta
    n["nome"] = nome
    n["movimento"] = movimento
    n["linea"] = linea          # ⭐ the premise of the second leg of I1
    n["tela_chiesta"] = tela
    n["dal_cliente"] = dal_cliente
    n["lettore"] = letto
    n["secondi_veri"] = round(vero, 1)
    n["coda_cliente"] = testo[-400:]
    return n


def stampa_giro(n):
    """⛔ §6.2: ALL the quantities are printed, even those not needed
       for the question of the moment.  A table with a single column is not a
       short measurement: it is a SLANTED measurement."""
    if not _ha_misurato(n):
        _dub("%s · %s" % (n.get("nome"), n.get("esito")))
        return
    _inf("RATE    mean %6.2f/s   worst second %s/s   whole %s/s   "
         "median %s ms   p95 %s ms"
         % (n["fps"], n["fps_finestra_min"], n["fps_intero"],
            n["intervallo_mediano_ms"], n["intervallo_p95_ms"]))
    _inf("SHAPE   %d frames (%d keyframes · %d deltas = %.1f %% deltas)   "
         "codec on the wire %s   canvas %s"
         % (n["fotogrammi"], n["chiavi"], n["delta"], n["quota_delta"] * 100,
            ",".join(n["codec_sul_filo"]), ",".join(n["tela_sul_filo"])))
    _inf("BYTES   payload %s Mbit/s (%d B/frame)   wire %s Mbit/s   "
         "%s B/packet"
         % (n["mbit_s_carico"], n["byte_per_fotogramma"],
            n["mbit_s_filo"] if n["mbit_s_filo"] is not None else "NOT READ",
            n["byte_per_pacchetto"]))
    _inf("DELAY   final drift %s ms   maximum %s ms   minimum %s ms   "
         "⚠ it is the DRIFT, not the loop"
         % (n["deriva_fine_ms"], n["deriva_max_ms"], n["deriva_min_ms"]))
    if n.get("linea"):
        _inf("LINE    loss declared by the qdisc: %s   (%s)"
             % ("%.2f %%" % n["linea"]["perdita_pc"]
                if n["linea"].get("perdita_pc") is not None else "⛔ I DO NOT KNOW",
                n["linea"].get("come")))
    s = n.get("server") or {}
    if s.get("registro_non_letto"):
        _dub("SERVER  %s" % s["registro_non_letto"])
        return
    _inf("SERVER  delivered %s · not sent %s · sent %s · ABANDONED %s "
         "· canvas announcements %s   (log from line %s)"
         % (s.get("consegnati"), s.get("non_spediti"), s.get("spediti"),
            s.get("abbandonati"), s.get("annunci_tela"), s.get("riga0")))
    _inf("CAPTURE %s   ⭐ «empty waits» = we asked and there was nothing: it is the "
         "column that separates Mutter from us"
         % json.dumps(s.get("cattura"), ensure_ascii=False))
    _inf("        second leg: gaps in `numero` %s · streams reset in the "
         "trace %s · audio %s"
         % (n["buchi_numero"], n.get("azzerati_sul_filo"), s.get("audio")))
    _inf("        spiral (§5.2/§5.1): %s" % json.dumps(s.get("spirale"),
                                                       ensure_ascii=False))
    # ⛔ THE WITNESS'S WEIGHT, and it is looked at on EVERY run.
    dc, sp = n.get("dal_cliente"), s.get("spediti")
    if dc and sp:
        manca = sp - dc["fotogrammi"]
        if manca > max(5, 0.05 * sp):
            _dub("⚠ the server sent %d and the client took %d "
                 "(%d fewer): the bottleneck may be the WITNESS, not the line"
                 % (sp, dc["fotogrammi"], manca))


# ═══════════════════════════════════════════════════════════════════════════
def principale():
    global RETE
    p = argparse.ArgumentParser()
    p.add_argument("passo", nargs="?",
                   choices=["terreno", "sonda", "rimetti", "stato"])
    p.add_argument("--certifica", action="store_true",
                   help="⭐ the positive control: proves the bench can see "
                        "the defects it looks for.  It does not touch the test machine")
    p.add_argument("--secondi", type=int, default=30)
    p.add_argument("--solo", default="", help="one step only, by name")
    p.add_argument("--tono", default="no", choices=["si", "no"],
                   help="⚠ turns on 1.56 Mbit/s of PCM: the question «who pays between "
                        "audio and video» is already closed by 07-b65, here the "
                        "default is OFF so the step measures the video")
    p.add_argument("--controllo-testimone", action="store_true",
                   help="⭐ reruns the floor step WITHOUT a trace: it is the "
                        "direct proof that the witness does not weigh on the number")
    p.add_argument("--senza-tela-minima", action="store_true",
                   help="skips the 768x480 pair of the floor step")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if not a.passo:
        p.error("a step is needed, or --certifica")

    os.makedirs(FUORI, exist_ok=True)
    RETE = _importa_rete()

    if a.passo in ("rimetti", "stato"):
        _log("the test machine's network — dev «%s», port %d" % (DEV, PORTA))
        return 0 if RETE.rimetti() else 2

    if a.passo == "terreno":
        return 0 if terreno_controlla() else 2

    _log("09-b70 · THE RATE — port %d · dev «%s» · codec requested «%s»"
         % (PORTA, DEV, CODEC_CHIESTO))
    print("   ⛔ «%s» (ssh + the user's 7730) is NOT touched" % VIETATA)
    print("   ⛔ the floor is 20 Mbit/s (§3.1-bis) and 25 frames/s (§2.1):")
    print("      below 20 we LOOK, we do not demand")
    print("   --  «%s» before: %s" % (DEV, RETE.qdisc() or "(none)"))
    if not terreno_controlla():
        return 2

    scelti = [g for g in GRADINI if not a.solo or a.solo in g[0]]
    if not scelti:
        _ko("no step matches «%s»" % a.solo)
        return 2
    # still scene + moving scene for every step, plus the pair at minimum canvas
    quanti = 2 * len(scelti) + (2 if (not a.senza_tela_minima and
                                      any(g[0].startswith("g4") for g in scelti)) else 0)
    totale = (a.secondi + 170) * quanti + 400
    RETE.guardiano_arma(totale)

    esiti, rossi, muti = [], [], []
    try:
        _inf("opening a short session to bring the stage and the monitor to life")
        if not innesca_sessione():
            _ko("the session does not open: I do not measure")
            return 2
        if a.tono == "si":
            RETE.tono_accendi()
            _inf("⚠ the tone is ON: the step does not measure the video alone")

        lavoro = []
        for nome, mbit, rit, requisito, perche in scelti:
            lavoro.append((nome, mbit, rit, requisito, perche, TELA_PIENA, ""))
            if nome.startswith("g4") and not a.senza_tela_minima:
                lavoro.append((nome, mbit, rit, requisito,
                               "⭐ the same step at the FLOOR CANVAS: "
                               "§2.1 is written at 480p, and adaptive "
                               "resolution is out of the product (§5.0-ter)",
                               TELA_MINIMA, "-480"))

        for nome, mbit, rit, requisito, perche, tela, suff in lavoro:
            _log("%s%s · %s" % (nome, suff, perche))
            reg = _regole(mbit, rit)
            ok, q = RETE.stringi(reg)
            if not ok:
                _ko(q)
                esiti.append({"gradino": nome + suff, "passa": False,
                              "perche": "tc refused the rule"})
                rossi.append(nome + suff)
                break
            if mbit:
                _inf("tc: %s  (queue %d packets = %d ms at %d Mbit/s — the "
                     "netem default would be 1000, that is %d ms)"
                     % (" ".join(reg), _limite(mbit), CUSCINO_MS, mbit,
                        int(1000 * PACCHETTO * 8 * 1000 / (mbit * 1e6))))
            else:
                _inf("tc: %s  (no bandwidth limit: the netem only counts)"
                     % " ".join(reg))
            _inf("canvas %s" % tela)

            coppia = {}
            for etichetta, movimento in (("mossa", "barra"), ("ferma", "marca")):
                usc = scena_accendi(movimento)
                if not usc:
                    _ko("the «%s» scene does not start: I do NOT judge this step"
                        % movimento)
                    coppia[etichetta] = {"esito": "NON HO NIENTE DA GIUDICARE — "
                                                 "the scene did not start"}
                    continue
                _inf("scene «%s» on monitor %s" % (movimento, usc))
                n = giro("%s%s-%s" % (nome, suff, etichetta), movimento, tela,
                         a.secondi)
                print("   [%s]" % etichetta)
                stampa_giro(n)
                coppia[etichetta] = n
                scena_spegni()

            # ⛔ I1 FIRST, and it is the reason why the step is run twice.
            passa_i1, perche_i1 = p_I1(coppia.get("ferma", {}),
                                       coppia.get("mossa", {}))
            (_ok if passa_i1 else (_dub if passa_i1 is None else _ko))(
                "I1 — the rate does not drop with the scene still: %s" % perche_i1)

            voci = {"gradino": nome + suff, "mbit": mbit, "ritardo_ms": rit,
                    "coda_pacchetti": _limite(mbit) if mbit else None,
                    "tela": tela, "requisito": requisito, "perche": perche,
                    "I1": {"passa": passa_i1, "perche": perche_i1},
                    "ferma": coppia.get("ferma"), "mossa": coppia.get("mossa"),
                    "predicati": {}}
            if passa_i1 is False:
                rossi.append("%s%s · I1" % (nome, suff))
            elif passa_i1 is None:
                muti.append("%s%s · I1 — %s" % (nome, suff, perche_i1))

            # Then the single-run predicates, on the MOVING run (which is the case
            # on which the floor is written) and on the STILL one.
            for etichetta in ("mossa", "ferma"):
                n = coppia.get(etichetta) or {}
                voci["predicati"][etichetta] = giudica_giro(n, requisito)
                for voce in voci["predicati"][etichetta]:
                    marca = "%s%s · %s · %s" % (nome, suff, etichetta,
                                                voce["predicato"])
                    if not voce["conta"]:
                        _inf("⚠ diagnosis · %s · %s → %s (%s)"
                             % (etichetta, voce["predicato"].split(" (")[0],
                                voce["passa"], voce["perche"][:80]))
                        continue
                    (_ok if voce["passa"] else
                     (_dub if voce["passa"] is None else _ko))(
                        "%s · %s: %s" % (etichetta,
                                         voce["predicato"].split(" (")[0],
                                         voce["perche"]))
                    if voce["passa"] is False:
                        rossi.append(marca)
                    elif voce["passa"] is None:
                        muti.append("%s — %s" % (marca, voce["perche"]))
            esiti.append(voci)

        # ⭐ THE WITNESS CONTROL — the direct proof that the trace is not
        #    the bottleneck.  Same step, same scene, without `--registra`.
        if a.controllo_testimone:
            _log("⭐ WITNESS CONTROL — the same step WITHOUT a trace")
            RETE.stringi(_regole(20, RITARDO_MS))
            usc = scena_accendi("barra")
            if usc:
                senza = giro("controllo-senza-traccia", "barra", TELA_PIENA,
                             a.secondi, con_traccia=False)
                scena_spegni()
                _inf("without a trace — the client says: %s · the server: %s"
                     % (senza.get("dal_cliente"),
                        (senza.get("server") or {}).get("spediti")))
                esiti.append({"gradino": "controllo-testimone", "senza": senza})
                _inf("⛔ compare it with the «g4-20mbit-mossa» run above: "
                     "if the client takes noticeably more WITHOUT a "
                     "trace, the grid's number belongs to the witness")
    finally:
        scena_spegni()
        if a.tono == "si":
            RETE.tono_spegni()
        _log("⛔ THE NETWORK IS PUT BACK AS IT WAS")
        rimessa = RETE.rimetti()

    with open(os.path.join(FUORI, "09-b70-esiti.json"), "w") as f:
        json.dump(esiti, f, ensure_ascii=False, indent=1)
    _inf("outcomes in %s/09-b70-esiti.json" % FUORI)

    _log("THE VERDICT — %d steps run · %d red · %d not judged"
         % (len(esiti), len(rossi), len(muti)))
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
        # ⚠ «I did not measure» is an outcome of ITS OWN, not a green.
        return 3
    _ok("⭐ all the predicates did what was written beforehand")
    return 0


if __name__ == "__main__":
    sys.exit(principale())
