#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b76-rete-cattiva — THE PRODUCT ON A LINE THAT **LOSES, REORDERS AND
                      FLICKERS**, which is not a NARROW line.

    port 7930 · probe 7931 · user `provanr1` (uid 1030)
    tree `/media/REMOTIX/src/09nr1-src` · work `/media/REMOTIX/tmp/09nr1`
    unit `remotix-7930` · its own ban-file and socket

═══════════════════════════════════════════════════════════════════════════════
⛔ WHERE IT COMES FROM — the phase's target changed on 23 August 2026
═══════════════════════════════════════════════════════════════════════════════

The director: *«30 Mbit/s is a mid-nineties connection»*.  ⇒ Bandwidth has
stopped being the question.  ⭐ The question is **the network that loses packets,
delivers them out of sequence or jitters**, which is what a distant WiFi, a
mobile radio or a home router under load does — and which a *narrow* line does
not reproduce at all.

⛔ And the two things do not resemble each other.  A narrow line queues; a
   bad line queues **and lies to the sender**: QUIC sees a gap in the
   sequence of packets and does not know whether it is a loss or an overtake.  If it
   takes it for a loss, it shrinks the congestion window **for no reason** — and
   the product slows down for a fault that never happened.
   ⚠ And today the product **has never chosen** a congestion algorithm
     (`src/webtransport.c` line ~2730): it takes whatever ngtcp2 gives it.  ⇒ A
     drop seen only on the disorder profiles would be **ours**, not
     the network's.

═══════════════════════════════════════════════════════════════════════════════
⭐ WHAT IT CAN SEE — the five quantities of `09-b70-ritmo.py`, PLUS ONE
═══════════════════════════════════════════════════════════════════════════════

The five are read with the **same** machinery as `09-b70-ritmo.py`, which is
IMPORTED and not copied (§«WHAT IS NOT REWRITTEN» of that file):

  1. delivered frames/s **average** and **minimum over a one-second window**;
  2. keyframes against deltas (§3.3: we degrade **in time**, not in keyframes);
  3. bytes on the wire (from the `qdisc` counter) next to the payload bytes;
  4. the **drift** of the delay — ⚠ not the round trip: `RCP.md` §6.2 forbids
     comparing the server's clock with the client's;
  5. server abandonments (video and audio) **and** gaps in the sequence of
     `nr` — the second leg, which does not go through the server's log.

⭐⭐ AND THE SIXTH, WHICH BELONGS TO THIS BENCH: **HOW MUCH `netem` REALLY LOST,
    REORDERED AND DUPLICATED**, measured and not hoped.

    ⛔ Without this number one does not know whether the fault one meant to put in
       was put in, and it is the difference between a measurement and a hope.  It is read
       from TWO independent legs:

      a) **the `qdisc` counter** — `tc -s qdisc show dev lo`.
         `[M]` 23 Aug 2026: the `dropped` field of the `netem 40:` block counts
         **exactly** the packets `netem` threw away — 2 000 sent
         with `loss 5%`, `dropped 101`, and the probe saw 101 missing.
         Two tools, the same number.
         ⛔⛔ BUT `tc` **HAS NO `reordered` COUNTER**: `[M]` the `netem`
             block prints only `Sent / dropped / overlimits / requeues /
             backlog`, and with `reorder 25% 50%` on the only field that
             moved is `requeues` (127), which **is not reordering**.  ⇒
             Reordering, jitter and duplication are NOT readable from the
             `qdisc`, and asking `tc` for them would give zero on a fault that is there.

      b) ⭐ **THE PROBE** (further down): 8 000 numbered UDP packets of 1 452
         bytes sent **through the same `netem`**, on my port 7931,
         right before the run.  It says, by measuring them: how many lost, in how many
         **bursts** and how long, how many duplicated, how many **out of
         order**, and the median delay and its spread.

    ⛔ And there is a THIRD check, which is the dumbest and has already caught a
       real trap: **the installed rule is read back** and checked not to
       carry verbs I did not ask for.  `[M]` 23 Aug: `tc qdisc change` is
       STICKY — a `reorder 25% 50%` set for one profile stayed on
       in the **four following profiles**, which would have measured a network that
       nobody had asked for.  ⇒ Every profile is installed with `qdisc del root` +
       `add` (which is what `tighten()` of `07-b65` does), and then **read back**.

═══════════════════════════════════════════════════════════════════════════════
⭐ THE PROFILES — and there is no bandwidth, by choice
═══════════════════════════════════════════════════════════════════════════════

⛔ **No profile carries `rate`.**  Bandwidth is the question of `09-b70-ritmo.py`
   and is already measured there.  Here the pipe is wide and the fault is another: if there
   were also a throttle, every number would be attributable to two causes
   at once, which is the politest way in which a grid lies
   (`LEZIONI.md` §1.26).

⛔ **And for the same reason the queue is declared the opposite way from b70.**  There the
   `limit` was worth 50 ms *at the step's bandwidth*, because there was a bandwidth.  Here
   there is none: the `limit` must be BIG enough never to throw anything away
   of its own, or it would add an undeclared loss on top of the declared one.
   ⇒ `limit 20000` packets, and the `liscio` profile **checks it**: if
   `dropped` is not zero at zero loss, it is my queue that loses and **every other
   number on this page is contaminated**.

| profile | `netem` | why | requirement |
|---|---|---|---|
| `liscio` | (only `limit`) | ⛔ the denominator. `netem` is there all the same because it is what carries the byte counter: a blind denominator cannot be compared with anything (it is b70's choice, and it is kept) | full |
| ⭐ `ritardo-30` | `delay 30ms` | ⭐⭐ **THE CONTROL THAT SEPARATES DELAY FROM DISORDER**: it arrives late but **in order** (`[M]` 0 out of order out of 2 000). If something gets worse already here, it is not the reordering — and it is the term of comparison of all comparisons | full |
| `perdita-0,5` … `perdita-3` | `delay 15ms loss X%` | ⛔ the delay is always there: without a network round trip the congestion window does not fill and the pacer notices nothing (b70 line ~322) | does not detach · no keyframe spiral · the yield |
| ⚠ `perdita-5` | `delay 15ms loss 5%` | beyond 3 %: **diagnosis**, we look at HOW it gives way | only «does not detach» |
| ⭐ `raffica-1` | `delay 15ms loss gemodel 0.2% 20% 100% 0%` | ⭐⭐ **THE EXACT TWIN OF `perdita-1`**: the same average loss, but in **clusters**. `[M]` 23 Aug: 0.60 % in bursts of **4.4 packets** (max 13), against bursts of 1.00 for independent loss. A radio's loss is not independent, and this is the only pair that isolates it | as `perdita-1` |
| ⚠ `raffica-forte` | `delay 15ms loss gemodel 3% 20% 100% 0%` | `[M]` **14.35 %** in bursts of 5.5: really distant WiFi — **diagnosis** | only «does not detach» |
| ⭐ `riordino-25` | `delay 10ms reorder 25% 50%` | **explicit reordering**, which is not jitter: one packet in four jumps the queue. `[M]` 33.5 % out of order, and **zero loss**. ⛔ `reorder` without `delay` does nothing | does not detach · spiral · ⭐ **it is not loss** |
| `jitter-5/15/30` | `delay 20ms Xms distribution normal` | ⚠ `[M]` and here there is a fact to declare: at 15 and 30 ms of flicker the normal goes **below zero**, `netem` cuts at 0, and the profile becomes jitter **plus massive reordering** (`[M]` `delay 20ms 15ms`: minimum 0.02 ms, p95 45 ms, **81 % out of order**). It is not a bench defect: it is what jitter IS when it exceeds the distance between two packets | as `riordino-25` |
| `duplicazione-1` | `delay 15ms duplicate 1%` | the case nobody ever tests. QUIC must ignore them; if our code counted a packet twice it would show here | does not detach · spiral · it is not loss |
| ⭐ `casa-cattiva` | `delay 40ms 20ms distribution normal loss 2%` | the mix: a home with distant WiFi. ⭐ It is the only profile run **in a PAIR** (moving scene and still scene) for invariant I1 | everything, plus I1 |

⛔⛔ AND SINCE 23 AUGUST 2026 «does not detach», IN THIS COLUMN, IS READ AS TWO:
    **«the connection did not drop»** *and* **«the delivery did not stop»**.
    They were one predicate, and they are two different facts with two different causes —
    ⇒ §«THE DEFECT OF THIS BENCH WAS OF **NAME**».  ⚠ On a diagnosis
    step both count: §3.1-bis exempts from the SCALE, not from delivering.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ THE PREDICATES — WRITTEN FIRST, and they return `(pass_on, reason_text)`
═══════════════════════════════════════════════════════════════════════════════

`07-b64-rete.py` carries finding **R13**: nine «expected» printed and never
compared.  A bench like that cannot give red.  ⇒ Here every expectation is a
function, and `pass_on` is `None` when the bench **refuses to judge** — which
is a third outcome, not a polite green (`CODER.md` §3.10).

  **G · THE FAULT WAS PUT IN** (⭐ and it comes BEFORE all the others).  Every profile
  carries its check on the probe's numbers, written next to the profile.  If
  the fault cannot be seen, the profile **is not judged**: measuring a profile that
  does not exist is worse than not measuring it.

  **S · DOES NOT DETACH** — ⛔⛔ AND ON 23 AUGUST 2026 THIS PREDICATE SPLIT
  IN TWO, because it was ONE and the facts were TWO.  The § that follows is the reason.

  **Q · THE THIRD LEG — the congestion window and the not-sent.**  They are
  read and printed, not judged: they are the two numbers that, on the
  bench's line, say by themselves *«nothing dropped, it is the pacer refusing»* and
  save the next diagnosis run (⇒ § further down).

═══════════════════════════════════════════════════════════════════════════════
⛔⛔⛔ THE DEFECT OF THIS BENCH WAS OF **NAME**, NOT OF NUMBER — 23 Aug 2026
═══════════════════════════════════════════════════════════════════════════════

The red of `raffica-forte` said: *«the session detached after 0.3 s out of
25»*.  ⛔ **Nobody detached.**  `banchi/09-b79-cure.py` (by another
agent) verified it with four independent witnesses, `[M]` 23 Aug 2026:

  · the client prints *«⭐ still attached after 25.0 s: nothing dropped»*
    (`01-b3-cliente.py:1979`) and closes **itself**, at the end of the window;
  · the audio arrives for the **whole** run: 696 datagrams, purity 1.0000;
  · the server log carries **no** `FAREWELL`, no `slot
    DENIED`, no ban;
  · the session had opened normally (`ADMITTED after 1 837 ms`) ⇒ the hypothesis
    «the handshake does not complete» is ruled out (`09-b78-apertura.py`).

What stopped was **only the delivery of frames**: `[M]` 121 out of 981
captured, **860 NOT SENT**, `cwnd` nailed at ~10 KB and the pacer
refusing.

⇒ `B70.p_nothing_detach` measures **how long the delivery lasted** (`vissuto_s`
  against `requested_s`) and calls it **detachment**.  ⛔ The number is right, the word
  is wrong — and a wrong word on a red is **worse than a missed
  red**, because it sends one looking for the cause in the wrong place: here it sent one
  looking for a farewell that is not there.

⚠ And the fact is NOT downgraded: a session **alive and mute** is a frozen screen,
  and for whoever is watching it is indistinguishable from a disconnection.  ⇒ The red is not
  removed: it is given the right name and measured for what it is.

  ⭐ **S1 · THE CONNECTION DID NOT DROP** — `DECISIONI.md` §3.3 / §8.3
     (*«never detach»*), and it holds **everywhere, even below the floor**
     (§3.1-bis: *«it is not a refusal: the ban on detaching stays whole»*).
     ⛔ It is measured on the **witnesses of the connection**, not on the frames:
     is the client still attached at the end of the window?  does the log carry a
     `FAREWELL` (and with what reason)?  ⇒ `p_connection_alive()`.
     ⚠ And the third possibility — *«it never opened»* — is ruled out
       EXPLICITLY, because it looks like a detachment and is not one:
       there the bench STAYS SILENT and refers to `09-b78-apertura.py`.

  ⭐⭐ **S2 · THE DELIVERY DID NOT STOP** — and it is the true fact of
     `raffica-forte`, which until tonight had no name in this bench.
     Two legs, two thresholds, each with its reason (⇒
     `p_delivery_never_stops()`):

       a) **the coverage** — how many seconds of the window saw **at least
          one** frame.  Threshold **0.90**.  ⚠ And it is not a new threshold: it is
          **the same** one `p_nothing_detach` used (`lived < 0.90 ×
          requested`).  The number does not change, the word changes — which is the whole
          cure.  `[M]` raffica-forte: 1 second out of 25.
       b) ⭐ **the longest gap** without even one frame.  Threshold
          **1.0 s**, and the reason is the floor of the scale: `DECISIONI.md`
          §2.1 asks for **25 frames per second**, so a whole second at
          **zero** is not «a low rate», it is **off the scale** — and it is also the
          width of the sliding window of `09-b70` (`_min_window`),
          so the two measurements look at the same grain and do not contradict each other.
          ⚠ Below a second it is not judged: at 40/s a 300 ms gap is a
            retransmission, not a frozen screen.

  ⚠ **THE PRICE, DECLARED**: the two legs count on **all** the profiles,
    diagnoses included — exactly as `p_nothing_detach` counted, whose
    place they take.  ⛔ §3.1-bis exempts a diagnosis step from the SCALE
    (§2.1), not from **delivering**: «only does not detach» today means «the
    connection does not drop **and** the screen does not freeze», which are the two ways in
    which the user sees the same thing.  ⇒ A diagnosis profile can give red
    here and not elsewhere, and it is intended.

  ⚠ And the old `B70.p_nothing_detach` **runs all the same**, marked «diagnosis»:
    its number stays in the bench's line next to the two new ones, so whoever
    rereads yesterday's grid sees by themselves what was renamed.
    ⛔ And b70's file **is not touched**: another agent is working on it.

  **K · NO KEYFRAME SPIRAL** — §3.3, imported from b70
  (`p_degrades_over_time`): the share of deltas stays ≥ 0.90 on all the profiles with
  loss ≤ 3 %.  `[M]` 21 Aug 2026, and it is the face of the defect: on the narrow
  runs there were **144 keyframes out of 144 frames**.  Every abandonment of §5.1 switches on
  the debt of §5.2, the debt asks for a keyframe, the keyframe fills the window,
  and it starts again.

  ⭐⭐ **R · JITTER AND REORDERING ARE NOT LOSS.**  It is the question this
  bench exists for.  On the profiles `riordino-25`, `jitter-*` and `duplicazione-1`
  the probe measures **zero loss**: every packet arrives.  ⇒ The delivered
  frames/s must not drop appreciably compared with `ritardo-30`,
  which has the same order of delay and no disorder.
  ⛔ If they drop, **it is not the network's**: it is ours, or the congestion algorithm's
     that we never chose.
  ⚠ The threshold is 0.90 — 10 % is *sufficient, not right*: it is more than the noise
    between two runs of the same machine (b70 estimates it at 5 %) and less than any
    drop the user would notice.
  ⛔ And it refuses to judge if the probe saw loss above 0.2 % on the
     profile, because then the comparison would no longer isolate the disorder.

  **P · LOSS IS PAID IN DELAY, NOT IN FRAMES THROWN AWAY.**  The video goes
  on QUIC **streams** (`RCP.md` §6.2), and a stream retransmits: a lost packet
  is not a lost frame, it is a **late** frame.
  ⇒ At `perdita-1` the yield in frames/s must be ≥ 0.90 of `ritardo-30`, and what
    pays must be the **drift**.
  ⚠ ⛔ And for this reason b70's drift predicate (250 ms) here is **NOT a
    requirement** on the profiles with loss: demanding at once «the frames do not
    drop» and «the delay does not grow» would mean forbidding the product the only
    way it has to pay for a loss.  It runs all the same and is WRITTEN, marked
    «diagnosis».

  **I1 · THE RATE DOES NOT DROP BECAUSE THE SCENE IS STILL** (`SPECIFICHE.md` §8.2) —
  imported from b70 (`p_I1`), with its two guards that refuse to
  judge when the difference is upstream of us.  ⭐ It is run on
  `casa-cattiva`, which is the profile closest to a real home.

═══════════════════════════════════════════════════════════════════════════════
⭐ THE THIRD LEG — «and THEN why did the delivery stop?»
═══════════════════════════════════════════════════════════════════════════════

The two new predicates say **what** happened and **what did not**.  They do not
say *why*, and without the why the next run starts from scratch.  ⇒ Into the
bench's line go the two numbers that at `raffica-forte` closed the
diagnosis by themselves:

  · **`non_spediti` / `delta_non_spedito`** — the server captured the
    frame and **never put it on the wire**.  `[M]` 860 out of 981.  ⛔ It is the
    distinction that a bench breaking the network on purpose needs to make more
    than any other: «the network threw it away» and «the server never sent it»
    give the same count on the client's side.  It is read from the server counts
    of `09-b70` (`server_counts`), which already carries them.
  · ⭐ **`cwnd` / `cwnd_left`** — ngtcp2's congestion window, from the
    `network-quic` line the server writes since 23 August 2026
    (`src/webtransport.c:3772`, and it is a **contract on the text**: stable
    prefix, `name=value` fields without spaces, `judgment=` last and up to the end
    of the line).  `[M]` nailed at ~10 KB.  ⇒ With `cwnd` at 10 KB and 860 not sent,
    «nothing dropped, it is the pacer refusing» is **read**, not deduced.

⚠ THE PRICE, DECLARED — THREE.
  1. The `network-quic` line exists only if the binary is built **from today's
     HEAD**: on an older tree the reading returns *«NOTHING TO READ»* and
     the bench **says so**, instead of printing zeros (`CODER.md` §3.10).
  2. This reduction also exists in `banchi/09-b79-cure.py`, by another
     agent.  ⛔ It is not imported: b79 imports **this** file, and importing it back
     would be a loop.  ⇒ The two read the **same contract written
     in `src/webtransport.c`**, which is where the truth lives; if the
     contract changes, it changes there and both are updated.
  3. ⛔ **Nothing is judged on these numbers.**  They are diagnosis: a threshold
     on `cwnd` would be a promise the product never made.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔⛔ WHAT THIS BENCH CANNOT SEE
═══════════════════════════════════════════════════════════════════════════════

 1. ⛔ **THE IMAGE.**  It counts frames, keyframes, bytes and delay.  It cannot say
    «it looks worse»: that verdict belongs to the user on the real desktop, and in v1 the
    corresponding phase was reset precisely because it had been validated with PSNR and SSIM.
 2. ⛔ **THE REAL NETWORK.**  `netem` runs on `lo`: no radio, no router
    queue, no third-party traffic, no path migration.  ⭐ The
    fault is *a model* of the bad network, and the model is written above
    line by line on purpose: whoever disagrees can argue with the model instead
    of guessing what was measured.
 3. ⛔ **THE BROWSER.**  The client is `01-b3-cliente.py`: it takes the bytes off the wire
    and **does not decode and does not paint**.  The frames/s here are a **ceiling**.
 4. ⚠ **THE `distribution normal` CANNOT BE READ BACK.**  `[M]` `tc qdisc show`
    does not print it: the reread rule says `delay 20ms 15ms` and nothing more.  ⇒ The shape
    of the distribution is the only thing about the fault this bench declares and
    does not verify; what it verifies is the **spread measured** by the probe.
 5. ⚠ **WHO ELSE IS ON THE MACHINE.**  The `netem` lock guarantees that
    no other bench is breaking the network; it does not guarantee that nobody is
    using the CPU.  The load is printed.

THE EXIT CODES
    0   CONFORMING · 1 NOT CONFORMING (there is a red) · 2 usage/ground/network
    3   ⛔ I HAVE NOTHING TO JUDGE — a run or a predicate refused

Usage (from the laptop):
    python3 banchi/09-b76-rete-cattiva.py --certify    ⭐ without a machine
    python3 banchi/09-b76-rete-cattiva.py terrain
    python3 banchi/09-b76-rete-cattiva.py probe [--seconds 25] [--solo riordino]
    python3 banchi/09-b76-rete-cattiva.py restore        ⛔ and it is checked
"""
import argparse, base64, importlib.util, json, math, os, re, statistics
import subprocess, sys, time

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ ISOLATION, WRITTEN BEFORE ANY IMPORT THAT READS IT
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ 7900, 7910, 7920 are already measured terms of comparison and are NOT
#    touched; 7809 belongs to the rate bench, 7730 belongs to the user.  Mine are
#    **7930** (the server) and **7931** (the probe, which listens to nobody).
PORT = os.environ.setdefault("PORT", "7930")
PORT = int(PORT)
# ⛔⭐ THE PROBE'S PORT CANNOT BE FIXED, and I learned it by losing a
#     run: I had chosen 7931 after seeing it free, and **while I was running**
#     another agent started its server on it (`09nr2`).  The probe said
#     «Address already in use» at every profile, and the bench — rightly —
#     refused to judge the whole grid.
#     ⇒ Among my candidates we pick the one that at THAT moment nobody is
#       listening on, and if there is none the bench stops instead of measuring
#       a network it has not verified.
PROBE_PORTS = [int(x) for x in
               os.environ.get("PROBE_PORTS", "7939,7938,7937,7936,7935").split(",")]
PROBE_PORT = PROBE_PORTS[0]
ACCOUNT = os.environ.setdefault("ACCOUNT", "provanr1")
UID_B = int(os.environ.setdefault("UID_B", "1030"))
MACHINE = os.environ.setdefault("MACHINE", "nicfio@192.168.0.2")
SUDO_PASSWORD = os.environ.setdefault("SUDO_PASSWORD", "nicfio")
ADDR = os.environ.setdefault("ADDR", "192.168.0.2")
LAV = os.environ.setdefault("LAV", "/media/REMOTIX/tmp/09nr1")
TREE = os.environ.setdefault("TREE", "/media/REMOTIX/src/09nr1-src")
INSIDE_TREE = os.environ.setdefault("INSIDE_TREE", "/srv/src/09nr1-src")
INSIDE_WORK = os.environ.setdefault("INSIDE_WORK", "/srv/remotix/tmp/09nr1")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.setdefault("OUT", "/tmp/09-b76")
SHM = os.environ.get("SHM", "/09nr1")     # ⛔ not «/09-b70»: see scene_turn_on()

FORBIDDEN = "enp7s0"     # ⛔ ssh and the user's session go through it: NEVER
DEV = "lo"

GREEN, RED, YELLOW, GRAY = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (GREEN, GRAY, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (RED, GRAY, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (YELLOW, GRAY, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


def _load(label_name, fpath):
    spec = importlib.util.spec_from_file_location(label_name, fpath)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE RATE MACHINERY IS IMPORTED FROM `09-b70-ritmo.py`, AND THEN CHECKED
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Not one line is copied: the §11.1 trace reader, the reduction to the
#    five numbers, the minimum window, the server counts and the four predicates
#    of the single run are **its own**, they are certified **there**, and two copies of the
#    same reduction in two files are two reductions that diverge (it is the wound
#    of 16 August, `09-b70` line ~430).
#
# ⛔⛔ AND THEN WE CHECK IT TOOK MY ENVIRONMENT.  `09-b70` binds its
#      constants to the environment **at import**: importing it and taking for granted that
#      it read mine would mean writing the trace into another agent's work
#      directory and breaking another bench's port — and the network is the only
#      thing that, when wrong, hurts those who have nothing to do with it.
B70 = None
NETWORK = None
LUC = None


def import_it():
    global B70, NETWORK, LUC
    B70 = _load("b70ritmo", os.path.join(HERE, "09-b70-ritmo.py"))
    troubles = []
    for label_name, my, its in (("port", PORT, B70.PORT), ("username", ACCOUNT, B70.ACCOUNT),
                           ("uid", UID_B, B70.UID_B), ("work", LAV, B70.LAV),
                           ("tree", TREE, B70.TREE), ("dev", DEV, B70.DEV),
                           ("dentro_lav", INSIDE_WORK, B70.INSIDE_WORK)):
        if my != its:
            troubles.append("%s: the module has «%s», mine is «%s»" % (label_name, its, my))
    if troubles:
        raise SystemExit("⛔ I DO NOT MEASURE: the import of 09-b70 did not take my "
                         "environment — " + " · ".join(troubles))
    # ⛔ And the network qdisc is taken by b70 itself, with its check
    #    (detached guardian, four-band `prio`, two `u32` filters on the
    #    port only, `restore` that checks itself).  Here we hook onto the module.
    NETWORK = B70._import_network()
    B70.NETWORK = NETWORK
    if NETWORK.PORT != PORT or NETWORK.DEV != DEV or NETWORK.FORBIDDEN != FORBIDDEN:
        raise SystemExit("⛔ I DO NOT TOUCH THE NETWORK: the network module has port %d, "
                         "dev «%s», forbidden «%s»"
                         % (NETWORK.PORT, NETWORK.DEV, NETWORK.FORBIDDEN))
    LUC = _load("lock", os.path.join(HERE, "09-lucchetto.py"))
    # ⛔ The two b70 functions the redirect made mute are replaced
    #    HERE, without touching its file (another agent is working on it).
    B70.log_line_list = log_line_list
    B70.ship_reader = (lambda:
                            write_on_machine("09-b70-leggi.py", B70.READER))
    B70.root = _transcribing_root     # ⛔ see `_transcribing_root`
    _hook_delivery()
    return B70


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE CLIENT MUST BE LISTENED TO IN FULL — and without this the cure is not
#     MEASURABLE, it is only written
# ═══════════════════════════════════════════════════════════════════════════
#
# `09-b70.lap()` keeps `coda_cliente = body_text[-400:]`, which is enough for the five
# numbers and **not** for the first witness of the connection: `[M]` 23 August 2026, in
# those 400 bytes there are the three final audio lines and **not** the line
# that answers — *«⭐ still attached after 25.0 s: nothing dropped»*
# (`01-b3-cliente.py:1979`).  ⇒ A `p_connection_alive` that read only the tail
# would refuse to judge while holding the answer, cut off.
#
# ⛔ And it is remedied **without touching b70's file** (another agent is working on it):
#    its `root` is replaced with one that passes the ball on and transcribes.
#    ⚠ The same remedy, with the same words, is in `09-b79-cure.py`: it is a
#      defect of b70, and the real cure belongs there.
LAST_CLIENT = {"body_text": ""}


def _transcribing_root(command, ceiling=300):
    rc, out, err = NETWORK.root(command, ceiling)
    if "01-b3-cliente.py" in command:
        LAST_CLIENT["body_text"] = out + err
    return rc, out, err


# ⛔⛔ AND THE SECOND SEAM: `09-b70.gauge()` **throws the journal away** (it reduces it
#     to the five numbers and lets it go), and without the arrival instants the
#     question «for how many seconds was the screen frozen?» cannot even be
#     stated.  ⇒ The DELIVERY reduction is hooked right after its own,
#     on the same journal, without copying one line of it.
#     ⭐ And it is hooked in `--certify` too: so the fabricated cases go
#       through the SAME `gauge()` and the SAME `reduce_delivery()` as the real runs.
_REAL_MEASURE = None


def _measure_seeing_delivery(journal, requested_s, *r, **k):
    n = _REAL_MEASURE(journal, requested_s, *r, **k)
    n["delivery"] = reduce_delivery([f["arrivo_ms"] for f in (journal or [])],
                                    requested_s)
    return n


def _hook_delivery():
    global _REAL_MEASURE
    if _REAL_MEASURE is not None:      # ⚠ only once: b79 imports this file
        return
    _REAL_MEASURE = B70.gauge
    B70.gauge = _measure_seeing_delivery


def root(command, ceiling=300):
    return NETWORK.root(command, ceiling)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE PROBE — «was the fault I meant to put in actually put in?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ It runs ON THE TEST MACHINE and crosses **the same `netem`** as the run:
#    it is the only thing that makes it a check and not another measurement.
#    ⇒ Two more `u32` filters on my port 7931, inside the same band
#      1:4, and off it goes.
#
# ⛔ It sends and receives on `127.0.0.1`, which on this machine goes through `lo`
#    exactly like the traffic towards 192.168.0.2 (the client runs in a
#    container on the same machine: it is the reason the whole bench
#    works on `lo`).
#
# ⚠ The packet is **1 452 bytes**, the size of the QUIC packet: a fault
#   depending on length would show at the same grain as the product.
#
# ⭐ And the probe **does not judge**: it prints the raw arrivals, and reducing them is the
#    job of `reduce_probe()` on the laptop — which is the SAME one that
#    `--certify` exercises on fabricated arrivals.  A probe that reduced on
#    its own would certify half of the tool.
PROBE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09-b76-sonda — numbered packets through the netem, and it prints the ARRIVALS.

⛔ It does not reduce and does not judge: the reduction lives in the bench, and it is the one the
   positive control exercises.  Here we send, receive and write.
"""
import json, socket, struct, sys, threading, time


def primary():
    port = int(sys.argv[1])
    how_many = int(sys.argv[2])
    passo_ms = float(sys.argv[3])
    gauge = int(sys.argv[4]) if len(sys.argv) > 4 else 1452
    ric = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ric.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16 * 1024 * 1024)
    ric.bind(("127.0.0.1", port))
    ric.settimeout(0.3)
    arrivals = []
    fine = threading.Event()

    def receive():
        # ⛔ The receiver lives in its own thread: sending everything and THEN receiving
        #    would overflow the socket's queue and I would call «lost» stuff
        #    the network had delivered.
        while True:
            try:
                d, _ = ric.recvfrom(4096)
            except socket.timeout:
                if fine.is_set():
                    return
                continue
            t = time.monotonic_ns()
            if len(d) >= 16:
                seq, part = struct.unpack("!Qq", d[:16])
                arrivals.append([seq, round((t - part) / 1e6, 3)])

    th = threading.Thread(target=receive, daemon=True)
    th.start()
    sp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    fill = b"\x5a" * (gauge - 16)
    t0 = time.monotonic()
    for i in range(how_many):
        sp.sendto(struct.pack("!Qq", i, time.monotonic_ns()) + fill,
                  ("127.0.0.1", port))
        d = t0 + (i + 1) * passo_ms / 1000.0 - time.monotonic()
        if d > 0:
            time.sleep(d)
    # ⚠ We wait for the netem queue to empty: with `delay 40ms 20ms` the
    #   last packets arrive after the end of sending, and I would close
    #   declaring them lost.
    time.sleep(2.0)
    fine.set()
    th.join(timeout=3)
    print(json.dumps({"how_many": how_many, "passo_ms": passo_ms,
                      "gauge": gauge, "arrivals": arrivals}))


if __name__ == "__main__":
    primary()
'''


def reduce_probe(arrivals, how_many):
    """⭐ From the raw arrivals to the numbers of the FAULT.  ⛔ And it is the same function
       that `--certify` exercises on fabricated arrivals.

    · **lost**    = the numbers that never arrived;
    · **bursts** = how long they are on average, ⭐ which is the only thing that
      tells an independent loss from a radio's.  `[M]` 23 Aug:
      `loss 1%` gives bursts of **1.00**; `loss gemodel` of **4.4**;
    · **duplicates** = arrived more than once;
    · **outside order** = arrived AFTER one with a higher number.  ⛔ It is the only
      measure of reordering that exists: `tc` has no `reordered` counter;
    · **the delay** and its **spread** (p95 − minimum), which is the
      flicker measured instead of declared.
    """
    n = {"how_many": how_many, "received_n": len(arrivals)}
    if not how_many:
        n["outcome"] = "I DO NOT JUDGE — the probe sent nothing"
        return n
    numbers = [a[0] for a in arrivals]
    unique = set(numbers)
    missing_n = [i for i in range(how_many) if i not in unique]
    bursts = []
    for i in missing_n:
        if bursts and i == bursts[-1][-1] + 1:
            bursts[-1].append(i)
        else:
            bursts.append([i])
    maximum, outside = -1, 0
    for q in numbers:
        if q < maximum:
            outside += 1
        else:
            maximum = q
    n["lost"] = len(missing_n)
    n["persi_pc"] = round(100.0 * len(missing_n) / how_many, 3)
    n["bursts"] = len(bursts)
    n["raffica_media"] = (round(len(missing_n) / float(len(bursts)), 2)
                          if bursts else 0.0)
    n["raffica_max"] = max((len(x) for x in bursts), default=0)
    n["duplicates"] = len(arrivals) - len(unique)
    n["duplicati_pc"] = round(100.0 * (len(arrivals) - len(unique)) / how_many, 3)
    n["out_of_order"] = outside
    n["fuori_ordine_pc"] = round(100.0 * outside / max(1, len(arrivals)), 2)
    if arrivals:
        r = sorted(a[1] for a in arrivals)
        n["ritardo_min_ms"] = r[0]
        n["ritardo_mediano_ms"] = round(statistics.median(r), 3)
        n["ritardo_p95_ms"] = r[int(0.95 * (len(r) - 1))]
        n["ritardo_max_ms"] = r[-1]
        n["dispersione_ms"] = round(n["ritardo_p95_ms"] - r[0], 3)
    n["outcome"] = "measured"
    return n


def _has_probed(s):
    return bool(s) and s.get("outcome") == "measured"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE DELIVERY REDUCTION — «for how many seconds was the screen
#     frozen?», which is the question that on 23 August had no name
# ═══════════════════════════════════════════════════════════════════════════
def reduce_delivery(arrivals_ms, requested_s):
    """From the arrival instants of the frames to the numbers of the DELIVERY.

    ⛔ It does not judge: it reduces.  Judging is the job of `p_delivery_never_stops()`, and the two
       are certified together on fabricated journals.

    · **coverage**  = how many seconds of the window saw AT LEAST ONE
      frame, out of how many seconds the window has.  ⚠ The cells are one
      second wide and start from the FIRST frame;
    · **buco_max_s** = the longest stretch without even one frame —
      ⭐ **tail included**: if the delivery stops at 0.3 s and the window is
      25, the gap is 24.7 s, and without counting the tail it would be zero, which is
      exactly the way this number would lie;
    · **consegna_fino_a_s** = the last frame inside the window.

    ⛔ THE WINDOW STARTS AT THE FIRST FRAME, and it is not a convenience: the
       client counts its `--stays N` seconds **after** the session is
       open (`01-b3-cliente.py:1924`), so the opening — `[M]` 1 837 ms on
       `raffica-forte` — sits OUTSIDE.  ⚠ And it shows in the numbers: `[M]` 23 Aug 2026,
       on all the healthy profiles `vissuto_s` sits between 24.75 and 25.00 out of 25 requested.
       If the opening were inside, the tail would be worth ~1.8 s on every run and this
       tool would give red everywhere.
    """
    n = {"requested_s": requested_s}
    if not requested_s:
        n["outcome"] = "I DO NOT JUDGE — I do not know how long the window was requested to be"
        return n
    cells = int(math.ceil(requested_s))
    n["secondi_finestra"] = cells
    if not arrivals_ms:
        # ⛔ Zero frames is not «I did not read»: it is the whole window at zero.
        n.update({"outcome": "measured", "frames": 0, "secondi_visti": 0,
                  "coverage": 0.0, "buco_max_s": round(float(requested_s), 3),
                  "buco_da_s": 0.0, "consegna_fino_a_s": 0.0})
        return n
    t = sorted(arrivals_ms)
    rel = [(x - t[0]) / 1000.0 for x in t]
    inside = [x for x in rel if x <= requested_s]
    n["frames"] = len(inside)
    n["fotogrammi_oltre_finestra"] = len(rel) - len(inside)
    hole, da, prev = 0.0, 0.0, 0.0
    for x in inside:
        if x - prev > hole:
            hole, da = x - prev, prev
        prev = x
    last = inside[-1] if inside else 0.0
    if requested_s - last > hole:            # ⭐ THE TAIL, and it is the one that counts
        hole, da = requested_s - last, last
    views = {int(x) for x in inside if x < cells}
    n["secondi_visti"] = len(views)
    n["coverage"] = round(len(views) / float(cells), 4)
    n["buco_max_s"] = round(hole, 3)
    n["buco_da_s"] = round(da, 3)
    n["consegna_fino_a_s"] = round(last, 3)
    n["outcome"] = "measured"
    return n


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE PROFILES — and the expectation of EACH is a function, not a sentence
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `limit 20000`: here there is no bandwidth, so the queue must NEVER be the one
#    throwing away.  The `liscio` profile checks it, and if it does not hold everything else is
#    contaminated.
QUEUE = int(os.environ.get("QUEUE", "20000"))
PROBE_PACKETS = int(os.environ.get("PROBE_PACKETS", "8000"))
PROBE_STEP_MS = float(os.environ.get("PROBE_STEP_MS", "0.4"))

# ── the thresholds, in one place only, and each with its reason ────────────
MIN_YIELD = 0.90      # ⚠ *sufficient, not right*: more than the noise between two
                        #   runs (b70 estimates it at 5 %), less than any drop
                        #   the user would notice.
NEGLIGIBLE_LOSS = 0.2   # % — above it, a «lossless» profile no longer isolates
                             #     the disorder and the comparison keeps quiet
OWN_QUEUE_MAX_PC = 0.10       # % — `dropped` at zero nominal loss: above it,
                             #     it is my `limit` throwing away
MIN_FAULT = 0.30    # the measured fault must be at least 30 % of the
                        # nominal, or it was not put in
MAX_FAULT = 3.0    # ⚠ and no more than three times: a `loss 1%` that loses
                        # 6 % is not the profile I declared

# ── ⭐⭐ the two DELIVERY thresholds (⇒ §«THE DEFECT WAS OF NAME») ──────────
MIN_COVERAGE = 0.90   # ⚠ it is NOT a new threshold: it is **the same** one
                          #   `B70.p_nothing_detach` used (`lived < 0.90 ×
                          #   requested`).  The word changes, not the number — which
                          #   is the whole cure of 23 August.
FROZEN_SCREEN_GAP_S = 1.0
# ⛔ The reason for the threshold, and it is not chosen: `DECISIONI.md` §2.1 puts the
#    floor of the scale at **25 frames per second**.  ⇒ A whole second at
#    **zero** is not «a low rate», it is **off the scale**: it is a frozen screen.
#    ⭐ And it is also the width of the sliding window of `09-b70`
#      (`_min_window`, 1 000 ms): the two measurements look at the same grain,
#      so they cannot contradict each other.
# ⚠ Below a second it is NOT judged: at 40/s a 300 ms gap is a
#   retransmission that did its job, not a frozen screen.


def _v_smooth(s):
    """⛔⛔ THE PROFILE THAT CHECKS THE BENCH, NOT THE PRODUCT.

    At zero nominal loss the probe must see zero: if it sees something, it is
    **my** queue (`limit %d`) throwing away, and every number of every other profile
    carries inside it a loss I did not declare.
    """ % QUEUE
    if s["persi_pc"] > OWN_QUEUE_MAX_PC:
        return (False, "at ZERO nominal loss the probe lost %d of %d "
                       "(%.2f %%): it is MY queue throwing away, and every other "
                       "profile is contaminated"
                % (s["lost"], s["how_many"], s["persi_pc"]))
    if s["fuori_ordine_pc"] > 0.5:
        return (False, "on a smooth network %.1f %% of the packets arrived "
                       "out of order: the denominator is not smooth"
                % s["fuori_ordine_pc"])
    return (True, "zero loss (%d of %d), zero disorder, median delay "
                  "%.2f ms: the denominator is clean"
            % (s["lost"], s["how_many"], s.get("ritardo_mediano_ms", -1)))


def _v_delay(s):
    """⭐⭐ THE REFERENCE: late but IN ORDER.  If it were not in order, none of the
       comparisons of this bench would separate anything any more."""
    med = s.get("ritardo_mediano_ms", 0)
    if not (25.0 <= med <= 40.0):
        return (None, "the measured median delay is %.2f ms, and I had asked for "
                      "30: I do NOT use as reference a profile that is not "
                      "the one I believe" % med)
    if s["fuori_ordine_pc"] > 0.5:
        return (False, "the delay-only profile has %.1f %% of packets "
                       "out of order: it no longer separates delay from disorder"
                % s["fuori_ordine_pc"])
    if s["persi_pc"] > OWN_QUEUE_MAX_PC:
        return (False, "the reference lost %.2f %%: it is not a "
                       "lossless reference" % s["persi_pc"])
    return (True, "median delay %.2f ms, ZERO out of order, ZERO lost: "
                  "late but in order, and it is the reference" % med)


def _v_loss(nominal, independent=True):
    def verify(s):
        if s["persi_pc"] < MIN_FAULT * nominal:
            return (None, "I had asked for %.2f %% loss and the probe "
                          "saw %.2f %%: the fault was NOT put in, and I do not "
                          "judge a profile that does not exist"
                    % (nominal, s["persi_pc"]))
        if s["persi_pc"] > MAX_FAULT * nominal:
            return (None, "I had asked for %.2f %% and the probe saw "
                          "%.2f %%: it is not the profile I declared"
                    % (nominal, s["persi_pc"]))
        if independent and s["raffica_media"] > 1.6:
            return (None, "the independent loss arrived in bursts of "
                          "%.2f packets: it is not independent"
                    % s["raffica_media"])
        if not independent and s["raffica_media"] < 2.0:
            return (None, "⛔ the BURST loss arrived in bursts of "
                          "%.2f packets, that is like the independent one: the "
                          "profile that makes this run different from «perdita-1» "
                          "was NOT put in" % s["raffica_media"])
        return (True, "lost %d of %d = %.2f %% (requested %.2f) in %d bursts "
                      "of average length %.2f (max %d)"
                % (s["lost"], s["how_many"], s["persi_pc"], nominal,
                   s["bursts"], s["raffica_media"], s["raffica_max"]))
    return verify


def _v_reorder(s):
    """⛔ `netem reorder` without `delay` does NOTHING, and does not say so.  ⇒
       The reordering is measured, or a profile that does not exist was measured."""
    if s["fuori_ordine_pc"] < 5.0:
        return (None, "%.1f %% of packets out of order: the reordering was NOT "
                      "put in (⛔ `reorder` without `delay` does nothing), and "
                      "I do not judge a profile that does not exist"
                % s["fuori_ordine_pc"])
    if s["persi_pc"] > NEGLIGIBLE_LOSS:
        return (None, "the reordering profile lost %.2f %%: it no longer isolates "
                      "disorder from loss" % s["persi_pc"])
    return (True, "%d packets of %d out of order (%.1f %%) and ZERO lost: it is "
                  "pure disorder" % (s["out_of_order"], s["received_n"],
                                      s["fuori_ordine_pc"]))


def _v_jitter(nominal_ms):
    def verify(s):
        avail = s.get("dispersione_ms", 0)
        if avail < 0.5 * nominal_ms:
            return (None, "the measured flicker (p95 − minimum) is %.1f ms and "
                          "I had asked for %d: the fault was not put in"
                    % (avail, nominal_ms))
        if s["persi_pc"] > NEGLIGIBLE_LOSS:
            return (None, "the flicker profile lost %.2f %%: it no longer "
                          "isolates the disorder" % s["persi_pc"])
        return (True, "median delay %.1f ms, spread p95−min %.1f ms "
                      "(requested %d), %.1f %% out of order, ZERO lost"
                % (s.get("ritardo_mediano_ms", -1), avail, nominal_ms,
                   s["fuori_ordine_pc"]))
    return verify


def _v_duplication(s):
    if s["duplicati_pc"] < MIN_FAULT * 1.0:
        return (None, "duplicates %.2f %% out of 1 %% requested: the fault was not "
                      "put in" % s["duplicati_pc"])
    if s["persi_pc"] > NEGLIGIBLE_LOSS:
        return (None, "the duplication profile lost %.2f %%"
                % s["persi_pc"])
    return (True, "%d packets duplicated of %d (%.2f %%) and ZERO lost: QUIC "
                  "must ignore them" % (s["duplicates"], s["how_many"],
                                     s["duplicati_pc"]))


def _v_home(s):
    if s["persi_pc"] < MIN_FAULT * 2.0:
        return (None, "I had asked for 2 %% loss and the probe saw "
                      "%.2f %%: the fault was not put in" % s["persi_pc"])
    if s.get("dispersione_ms", 0) < 10.0:
        return (None, "the measured flicker is %.1f ms out of 20 requested: the "
                      "fault was not put in" % s.get("dispersione_ms", 0))
    return (True, "lost %.2f %%, median delay %.1f ms, spread %.1f ms, "
                  "%.1f %% out of order: it is a home with distant WiFi"
            % (s["persi_pc"], s.get("ritardo_mediano_ms", -1),
               s.get("dispersione_ms", -1), s["fuori_ordine_pc"]))


#  (name, netem rules, requisito_pieno, spirale_e_resa, without_loss, why, check)
#
#   requisito_pieno   the rate floor and the drift are a REQUIREMENT
#                     (only the denominator and the reference: they are the two lines
#                      that have no fault to pay for)
#   spirale_e_resa    §3.3 (delta share) and the yield in frames are a REQUIREMENT
#                     ⛔ it holds on the profiles with loss ≤ 3 %, as asked
#   without_loss     ⭐ the profile does NOT lose: the yield is compared with
#                     `ritardo-30` and a drop is OURS, not the network's
PROFILES = [
    ("liscio", [], True, True, True,
     "⛔ the denominator. The netem is there all the same because it is what carries the "
     "byte counter, and it checks that MY queue throws nothing away of its own",
     _v_smooth),
    ("ritardo-30", ["delay", "30ms"], True, True, True,
     "⭐⭐ THE CONTROL THAT SEPARATES DELAY FROM DISORDER: late but IN ORDER. "
     "It is the reference of all the comparisons",
     _v_delay),
    ("perdita-0,5", ["delay", "15ms", "loss", "0.5%"], False, True, False,
     "the first loss: half a packet in a hundred", _v_loss(0.5)),
    ("perdita-1", ["delay", "15ms", "loss", "1%"], False, True, False,
     "⭐ THE PROFILE ON WHICH THE PREDICATE IS WRITTEN «loss is paid in "
     "delay, not in frames thrown away»", _v_loss(1.0)),
    ("perdita-3", ["delay", "15ms", "loss", "3%"], False, True, False,
     "the declared boundary: up to here the keyframe spiral is a REQUIREMENT",
     _v_loss(3.0)),
    ("perdita-5", ["delay", "15ms", "loss", "5%"], False, False, False,
     "⚠ beyond the boundary — DIAGNOSIS: we look at HOW it gives way, not whether it does",
     _v_loss(5.0)),
    ("raffica-1", ["delay", "15ms", "loss", "gemodel", "0.2%", "20%", "100%", "0%"],
     False, True, False,
     "⭐⭐ THE EXACT TWIN OF «perdita-1»: same average loss, but in "
     "CLUSTERS (`[M]` bursts of 4.4 against 1.0). It is the only pair that isolates "
     "the STRUCTURE of the loss from its quantity",
     _v_loss(1.0, independent=False)),
    ("raffica-forte", ["delay", "15ms", "loss", "gemodel", "3%", "20%", "100%", "0%"],
     False, False, False,
     "⚠ `[M]` 14.35 % in bursts of 5.5: really distant WiFi — DIAGNOSIS",
     _v_loss(14.0, independent=False)),
    ("riordino-25", ["delay", "10ms", "reorder", "25%", "50%"], False, True, True,
     "⭐⭐ EXPLICIT REORDERING, which is not jitter: one packet in four "
     "jumps the queue, and NONE is lost",
     _v_reorder),
    ("jitter-5", ["delay", "20ms", "5ms", "distribution", "normal"], False, True, True,
     "the small flicker: 20 ± 5 ms", _v_jitter(5)),
    ("jitter-15", ["delay", "20ms", "15ms", "distribution", "normal"], False, True, True,
     "⚠ `[M]` at 15 ms the normal goes below zero and netem cuts: it becomes "
     "flicker PLUS massive reordering (81 % out of order). It is not a defect "
     "of the bench: it is what jitter IS", _v_jitter(15)),
    ("jitter-30", ["delay", "20ms", "30ms", "distribution", "normal"], False, True, True,
     "flicker wider than the average delay: the worst case of disorder",
     _v_jitter(30)),
    ("duplicazione-1", ["delay", "15ms", "duplicate", "1%"], False, True, True,
     "⭐ the case nobody ever tests. QUIC must ignore them; if our code "
     "counted a packet twice it would show here", _v_duplication),
    ("casa-cattiva", ["delay", "40ms", "20ms", "distribution", "normal",
                      "loss", "2%"], False, True, False,
     "⭐ THE MIX: a home with distant WiFi. It is the only profile run in a "
     "PAIR (moving scene and still scene) for invariant I1", _v_home),
]

REFERENCE = "ritardo-30"

# ⛔ The `netem` verbs that change the network.  If one appears that I did NOT
#    ask for, the rule is not mine: `[M]` 23 Aug 2026, `tc qdisc change` is
#    sticky and carried along a `reorder 25% 50%` for four
#    profiles.
VERBS = ["loss", "reorder", "duplicate", "corrupt", "rate", "slot", "ecn"]


def _rules(profile_v):
    return ["limit", str(QUEUE)] + list(profile_v)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE `qdisc` COUNTERS — the first leg, and it is read, not deduced
# ═══════════════════════════════════════════════════════════════════════════
def qdisc_counts():
    """`[M]` 23 Aug 2026: the `dropped` of the `netem 40:` block counts EXACTLY
       the packets thrown away by netem (2 000 sent with `loss 5%` → `dropped
       101`, and the probe saw 101 missing).

    ⛔⛔ And there is no `reordered`: the block prints only
        `Sent / dropped / overlimits / requeues / backlog`.  Whoever looked there for
        reordering would read zero on a fault that is there.
    """
    rc, out, _ = root("/usr/sbin/tc -s qdisc show dev %s" % DEV)
    pieces = out.split("qdisc netem 40:")
    if len(pieces) < 2:
        return None
    m = re.search(r"Sent (\d+) bytes (\d+) pkt \(dropped (\d+), "
                  r"overlimits (\d+) requeues (\d+)\)", pieces[1])
    if not m:
        return None
    return {"byte": int(m.group(1)), "packets": int(m.group(2)),
            "dropped": int(m.group(3)), "beyond": int(m.group(4)),
            "restored": int(m.group(5))}


def rule_reread():
    """⛔ The third check, and it is the dumbest of the three: the rule is READ BACK.

    ⚠ `distribution normal` is NOT printed back by `tc`: it is the only part of the
      fault that is declared and not read back (its proof is the spread
      measured by the probe).
    """
    rc, out, _ = root("/usr/sbin/tc qdisc show dev %s" % DEV)
    for row in out.splitlines():
        if "netem 40:" in row:
            return re.sub(r"\s*seed \d+", "", row).strip()
    return ""


def check_rule(asks, reread):
    """(pass_on, reason_text) — the installed fault is that one and ONLY that one."""
    if not reread:
        return _no("I did not read back any `netem 40:` on «%s»: the rule is not "
                   "there" % DEV)
    troubles = []
    for verb in VERBS:
        requested = verb in asks
        c_e = re.search(r"\b%s\b" % verb, reread) is not None
        if c_e and not requested:
            troubles.append("«%s» is there and I did NOT ask for it" % verb)
        if requested and not c_e:
            troubles.append("I asked for «%s» and it is not there" % verb)
    if "delay" in asks and "delay" not in reread:
        troubles.append("I asked for a delay and it is not there")
    if troubles:
        return _no("⛔ THE INSTALLED RULE IS NOT MINE — %s · read back: «%s»"
                   % (" · ".join(troubles), reread))
    return _si("rule read back: «%s»" % reread)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE PREDICATES THAT BELONG TO THIS BENCH — written FIRST
# ═══════════════════════════════════════════════════════════════════════════
def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _mute(p): return (None, p)


def p_fault_set(profile_name, verify, probe):
    """⭐ IT COMES BEFORE ALL: measuring a profile that does not exist is worse than
       not measuring it, because the number is true and the cause is made up."""
    if not _has_probed(probe):
        return _mute("the probe did not measure: without it, I do not know whether the fault of "
                     "«%s» was put in" % profile_name)
    return verify(probe)


def p_connection_alive(t):
    """⛔⛔ **DID THE CONNECTION DROP?** — and it is asked of the WITNESSES OF THE
       CONNECTION, not of the frames.

    `DECISIONI.md` §3.3 / §8.3: *«never detach»*.  It is the obligation that holds
    **everywhere, even below the floor** (§3.1-bis: *«it is not a refusal: the
    ban on detaching stays whole»*), so it counts on ALL the profiles,
    diagnoses included.

    ⛔ And the frames have nothing to do with it here.  On 23 August 2026 this predicate did not
       exist and in its place there was `B70.p_nothing_detach`, which looks at how long the
       delivery LASTED: on `raffica-forte` it said *«it detached after
       0.3 s»* while the client was attached, the audio was arriving and the log
       carried no farewell.  ⇒ Two witnesses, and neither of them is a
       frame:

      1. **the client**, which says it by itself (`01-b3-cliente.py:1979`):
         *«⭐ still attached after N s: nothing dropped»* ⇒ it did not drop;
         *«⛔ I did NOT stay attached: …»* ⇒ it dropped, **and it says why**;
      2. **the server log**: a `farewell motivo=`, a `slot DENIED`,
         a ban.  ⛔ The reason is printed: «it dropped» without the reason sends one
         looking for the cause at random, which is the defect this cure repairs.

    ⚠ AND THE THIRD POSSIBILITY IS RULED OUT EXPLICITLY.  *«It never
      opened»* looks the same as *«it detached»* and is not the same thing:
      there this predicate KEEPS SILENT and the question belongs to `09-b78-apertura.py`.
    """
    if not t:
        return _mute("I did not question any witness of the connection")
    if t.get("is_open") is False:
        return _mute("⚠ the session does not appear to have OPENED in this run: "
                     "«it never opened» looks the same as «it "
                     "detached» and is not the same thing — the question belongs to "
                     "`09-b78-apertura.py`, and I do not judge")
    farewells = t.get("farewells") or []
    if t.get("cliente_staccato"):
        return _no("⛔ THE CLIENT DROPPED, and it says so itself: «%s»%s"
                   % ((t.get("drop") or "").strip()[:160],
                      (" · the log: «%s»" % farewells[0][:160]) if farewells
                      else " · ⚠ and the log carries NO farewell"))
    if farewells:
        return _no("⛔ THE SERVER SAID FAREWELL: «%s»%s"
                   % (farewells[0][:180],
                      "" if t.get("cliente_attaccato") is not True else
                      " — ⚠ and the client said it was still attached: the two "
                      "witnesses do not agree"))
    if t.get("cliente_attaccato"):
        return _si("⭐ NOBODY DETACHED: the client stayed attached until "
                   "the end of the window and the log carries no farewell, "
                   "no denied slot, no ban")
    return _mute("the client said neither «still attached» nor «I did NOT "
                 "stay attached», and the log is silent: I have no witnesses")


def p_delivery_never_stops(n):
    """⭐⭐ **DID THE DELIVERY STOP?** — and it is the true fact of
       `raffica-forte`, which until 23 August 2026 had no name here.

    ⚠ A session **alive and mute** is a frozen screen, and for whoever is watching it is
      indistinguishable from a disconnection.  ⇒ It is not downgraded: it is measured.

    Two legs, and each with its declared threshold:

      a) **the coverage** — how many seconds of the window saw at least one
         frame.  Threshold %.2f, which is **the same** as `p_nothing_detach`:
         the number does not change, the word changes.
      b) **the longest gap** without even one frame, tail included.
         Threshold %.1f s, and the reason is §2.1: with the floor at 25 frames/s,
         a whole second at zero is **off the scale**, not «a low rate».

    ⛔ And it does NOT run on `_has_measured(n)`: when the delivery really stops,
       `09-b70.gauge()` refuses to reduce (fewer than the minimum of frames) and
       a predicate hooked to that flag would keep silent **precisely where
       it is needed**.  Here we look at `n["delivery"]`, which is always there.
    """ % (MIN_COVERAGE, FROZEN_SCREEN_GAP_S)
    c = (n or {}).get("delivery")
    if not c or c.get("outcome") != "measured":
        return _mute((c or {}).get("outcome", "I do not have the delivery reduction "
                                            "for this run"))
    queue = ("%d seconds out of %d saw at least one frame (%.0f %%) · longest "
            "gap %.2f s (from %.2f s) · last frame at %.2f s"
            % (c["secondi_visti"], c["secondi_finestra"], c["coverage"] * 100,
               c["buco_max_s"], c["buco_da_s"], c["consegna_fino_a_s"]))
    if c["coverage"] < MIN_COVERAGE:
        return _no("⛔ THE DELIVERY STOPPED: %s — ⚠ the connection may "
                   "well be alive, but the screen is frozen, and for whoever "
                   "is watching it is the same thing" % queue)
    if c["buco_max_s"] >= FROZEN_SCREEN_GAP_S:
        return _no("⛔ THE SCREEN FROZE for %.2f s in a row (from %.2f s): "
                   "with the floor at 25 frames/s (§2.1) a second at ZERO is "
                   "off the scale, not a low rate — %s"
                   % (c["buco_max_s"], c["buco_da_s"], queue))
    return _si("the delivery never stopped: %s" % queue)


def p_not_loss(n, n_ref, probe, label_name):
    """⭐⭐ THE PREDICATE THIS BENCH EXISTS FOR.

    `SPECIFICHE.md` does not write it because nobody had thought of it: **reordering
    and jitter are NOT loss**.  On these profiles the probe measures
    ZERO loss — every packet arrives, only in a different order or at a different
    time.  ⇒ The delivered rate must not drop compared with `ritardo-30`,
    which has the same order of delay and no disorder.

    ⛔ If it drops, the network lost nothing and the drop is **ours**: either from
       QUIC's loss detection mistaking an overtake for a gap, or from
       the congestion algorithm we never chose
       (`src/webtransport.c` ~2730).
    """
    if not B70._has_measured(n):
        return _mute(n.get("outcome", "I did not measure this profile"))
    if not B70._has_measured(n_ref or {}):
        return _mute("the reference «%s» did not measure: without it there is no "
                     "comparison, and a number without a denominator does not judge"
                     % REFERENCE)
    if _has_probed(probe) and probe["persi_pc"] > NEGLIGIBLE_LOSS:
        return _mute("on «%s» the probe saw %.2f %% of real loss: the "
                     "comparison would no longer isolate the disorder"
                     % (label_name, probe["persi_pc"]))
    ratio = n["fps"] / n_ref["fps"] if n_ref["fps"] else 0.0
    queue = ("%.2f/s against %.2f/s of the reference «%s» (%.0f %%), worst "
            "second %s against %s"
            % (n["fps"], n_ref["fps"], REFERENCE, ratio * 100,
               n["fps_finestra_min"], n_ref["fps_finestra_min"]))
    if ratio < MIN_YIELD:
        return _no("⛔ the rate drops on a network that LOSES NOTHING: %s — the "
                   "disorder was mistaken for loss, and it is not the "
                   "network's" % queue)
    return _si("the disorder was not mistaken for loss: %s" % queue)


def p_late_loss(n, n_ref, probe, label_name):
    """**Loss is paid in DELAY, not in frames thrown away.**

    The video goes on QUIC **streams** (`RCP.md` §6.2), and a stream retransmits: a
    lost packet is not a lost frame, it is a **late** frame.
    ⇒ The yield in frames/s stays ≥ %.2f of the reference, and what pays is the
      drift — which here is PRINTED and not judged, because demanding at once
      «the frames do not drop» and «the delay does not grow» would mean forbidding
      the product the only way it has to pay for a loss.
    """ % MIN_YIELD
    if not B70._has_measured(n):
        return _mute(n.get("outcome", "I did not measure this profile"))
    if not B70._has_measured(n_ref or {}):
        return _mute("the reference «%s» did not measure" % REFERENCE)
    ratio = n["fps"] / n_ref["fps"] if n_ref["fps"] else 0.0
    loss_pct = ("%.2f %%" % probe["persi_pc"]) if _has_probed(probe) else "?"
    queue = ("%.2f/s against %.2f/s (%.0f %%) with %s of real loss · the drift "
            "ended at %s ms (maximum %s)"
            % (n["fps"], n_ref["fps"], ratio * 100, loss_pct,
               n["deriva_fine_ms"], n["deriva_max_ms"]))
    if ratio < MIN_YIELD:
        return _no("⛔ the loss was paid in FRAMES and not in delay: "
                   "%s — on QUIC streams that retransmit it should not be" % queue)
    return _si("the loss was paid in delay, not in frames: %s" % queue)


def p_my_queue(profile_name, without_loss, delta):
    """⛔ This bench's `limit` must NEVER throw anything away of its own: here there
       is no bandwidth, so every packet thrown away at zero nominal loss is a
       fault I added without declaring it."""
    if not delta:
        return _mute("I did not read the qdisc counters around the run")
    if not delta["packets"]:
        return _mute("zero packets in the qdisc around the run")
    pc = 100.0 * delta["dropped"] / float(delta["packets"] + delta["dropped"])
    if without_loss and pc > OWN_QUEUE_MAX_PC:
        return _no("⛔ the qdisc threw away %d packets of %d (%.2f %%) on a "
                   "LOSSLESS profile: it is my `limit %d` throwing away, and the "
                   "number of this run is contaminated"
                   % (delta["dropped"], delta["packets"], pc, QUEUE))
    return _si("the qdisc sent %d packets (%.1f MB) and threw away %d "
               "(%.2f %%)" % (delta["packets"], delta["byte"] / 1e6,
                              delta["dropped"], pc))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE POSITIVE CONTROL — «how does this bench know it can see?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `PIANO.md` §0.3.4: *«a bench that cannot see the defect it looks for has no
#    right to green»*.  ⇒ Here numbers are fabricated and we check that the
#    predicates give what is written FIRST — green, red **and mute**.
#
# ⭐ And the cases do not pass ready-made numbers: they fabricate ARRIVALS and make them
#    go through `reduce_probe()`, which is the same function that runs on the real
#    runs.  A deception living in the reduction would be seen.
def _make_arrivals(how_many, lost=(), duplicates=(), swaps=(), delay=15.0,
                flicker=0.0):
    """Fabricates the probe's arrivals.  `swaps` = pairs (i, j) to swap
       in the ARRIVAL ORDER, which is what an overtaking packet does."""
    lost = set(lost)
    order = [i for i in range(how_many) if i not in lost]
    for i, j in swaps:
        if i < len(order) and j < len(order):
            order[i], order[j] = order[j], order[i]
    arrivals = []
    for k, nr in enumerate(order):
        r = delay + (flicker if k % 2 else -flicker)
        arrivals.append([nr, round(r, 3)])
        if nr in duplicates:
            arrivals.append([nr, round(r + 0.05, 3)])
    return arrivals


def _make_round(fps, seconds=25, key_every=0, drift=0.0, cons=1000, sped=1000,
              aband=0, empty=3):
    """A fake run, reduced by the SAME `gauge()` that runs on the real runs."""
    g = B70._fab([(fps, seconds + 3)], key_every=key_every,
                 drift_ms_per_frame=drift)
    srv = {"delivered": cons, "shipped": sped, "abandoned": aband,
           "non_spediti": cons - sped, "annunci_tela": 0,
           "capture_v": {"catturati": cons, "keys": 1, "attese_a_vuoto": empty}}
    wire = {"byte": 90 * 1000 * 1000, "seconds": float(seconds),
            "byte_per_pacchetto": 1452.0}
    return B70.gauge(g, seconds, srv, wire)


def _make_round_in_stretches(pieces, requested=25, fps=40.0):
    """⭐ A RUN WITH GAPS INSIDE.  `pieces` = [(seconds of delivery,
       seconds of silence), ...].

    ⛔ `B70._fab` cannot fabricate a gap — its stretches are attached one
       to the other — and *a helper that cannot fabricate the defect cannot
       certify the predicate that looks for it* (it is the lesson of case 25).
       ⇒ One piece at a time is fabricated and SHIFTED in time, and then it goes
         through the SAME `gauge()` as the real runs, which carries along
         `reduce_delivery()`.
    ⚠ `arrivo_ms` is in milliseconds and `instant_us` in microseconds: two units
      on the same line, and getting them wrong would give a fake drift of hours.
    """
    g, t, nr = [], 0.0, 1
    for delivery, silence in pieces:
        piece = B70._fab([(fps, delivery)], number_from=nr) if delivery > 0 else []
        for f in piece:
            f["arrivo_ms"] += int(round(t * 1000.0))
            f["instant_us"] += int(round(t * 1e6))
        g += piece
        if piece:
            nr = piece[-1]["nr"] + 1
        t += delivery + silence
    srv = {"delivered": len(g), "shipped": len(g), "abandoned": 0,
           "non_spediti": 0, "annunci_tela": 0}
    return B70.gauge(g, requested, srv, None)


def certify():
    print("⭐ CERTIFICATION OF THE BAD-NETWORK BENCH — the expected outcome is written "
          "FIRST\n")
    print("   ⛔ No contact with the test machine: here we test the "
          "TOOL,\n      not the product.\n")
    import_fake()
    green_v = True

    def outcome(label_name, seen_v, expected_val, reason_text):
        nonlocal green_v
        all_ok = (seen_v is expected_val)
        green_v = green_v and all_ok
        print("  %s%-62s expected %-5s seen %-5s\n        %s"
              % ("OK  " if all_ok else "⛔  ", label_name, expected_val, seen_v, reason_text[:150]))

    # ── 1 · THE PROBE REDUCTION, which is half of the tool ─────────────────
    print("  ── the probe reduction: from the arrivals to the numbers of the fault ──\n")
    s = reduce_probe(_make_arrivals(1000), 1000)
    outcome("1-⭐ smooth probe: 1 000 out of 1 000, in order",
          (s["lost"] == 0 and s["duplicates"] == 0 and s["out_of_order"] == 0),
          True, "lost %d · dup %d · out of order %d" % (s["lost"],
                s["duplicates"], s["out_of_order"]))

    s = reduce_probe(_make_arrivals(1000, lost=[10, 11, 12, 500]), 1000)
    outcome("2-⭐ BURST loss: 3 in a row plus 1 alone → 2 bursts, average 2.0",
          (s["lost"] == 4 and s["bursts"] == 2 and s["raffica_media"] == 2.0
           and s["raffica_max"] == 3),
          True, "lost %d in %d bursts, average %.2f, max %d"
          % (s["lost"], s["bursts"], s["raffica_media"], s["raffica_max"]))

    s = reduce_probe(_make_arrivals(1000, duplicates=[3, 7, 9]), 1000)
    outcome("3-⭐ duplicates: 3 packets arrived twice, and ZERO lost",
          (s["duplicates"] == 3 and s["lost"] == 0), True,
          "duplicates %d · lost %d · received %d"
          % (s["duplicates"], s["lost"], s["received_n"]))

    # ⭐⭐ AND HERE THERE IS SOMETHING NOT OBVIOUS, and the first expectation I had
    #    written was WRONG: **a single long overtake makes many packets arrive
    #    late**.  The swap (10,11) makes 1 arrive late; the
    #    swap (20,25) makes 5 arrive late — number 25 moves ahead and the
    #    four in between plus 20 all stay behind a higher number.
    #    ⇒ 6, not 2.  ⚠ It is also the reason why `[M]` `delay 20ms 15ms` gives
    #      81 % «out of order» with a fault that moves few packets: the
    #      quantity counts those DISPLACED BY, not those displaced.
    s = reduce_probe(_make_arrivals(1000, swaps=[(10, 11), (20, 25)]), 1000)
    outcome("4-⭐ reordering: a short overtake (1 late) plus a long one (5) = 6",
          (s["out_of_order"] == 6 and s["lost"] == 0), True,
          "out of order %d (%.2f %%) · lost %d"
          % (s["out_of_order"], s["fuori_ordine_pc"], s["lost"]))

    # ── 2 · «WAS THE FAULT PUT IN?», and the right answer is often MUTE ────
    print("\n  ── was the fault put in? (⭐ and «I do not know» is an outcome) ──\n")
    p, q = p_fault_set("liscio", _v_smooth, reduce_probe(_make_arrivals(8000), 8000))
    outcome("5-⭐ clean smooth line", p, True, q)

    p, q = p_fault_set("liscio", _v_smooth,
                          reduce_probe(_make_arrivals(8000, lost=range(0, 8000, 50)), 8000))
    outcome("6-⛔⛔ smooth line losing 2 %: it is MY queue, and it contaminates everything",
          p, False, q)

    p, q = p_fault_set("perdita-1", _v_loss(1.0),
                          reduce_probe(_make_arrivals(8000, lost=range(0, 8000, 100)), 8000))
    outcome("7-⭐ perdita-1: the probe sees 1 %", p, True, q)

    p, q = p_fault_set("perdita-3", _v_loss(3.0),
                          reduce_probe(_make_arrivals(8000), 8000))
    outcome("8-⛔⛔ perdita-3 REQUESTED and NEVER PUT IN: the bench must KEEP SILENT, not give "
          "green", p, None, q)

    # ⛔ The case that really happened on 23 August: `tc qdisc change`
    #    carried along the previous profile's `reorder`.
    p, q = p_fault_set("riordino-25", _v_reorder, reduce_probe(_make_arrivals(8000), 8000))
    outcome("9-⛔⛔ reordering requested and not put in (⚠ `reorder` without `delay` does "
          "nothing): SILENT", p, None, q)

    swaps = [(i, i + 1) for i in range(0, 6000, 4)]
    p, q = p_fault_set("riordino-25", _v_reorder,
                          reduce_probe(_make_arrivals(8000, swaps=swaps), 8000))
    outcome("10-⭐ reordering really put in: one packet in four overtakes",
          p, True, q)

    p, q = p_fault_set("raffica-1", _v_loss(1.0, independent=False),
                          reduce_probe(_make_arrivals(8000, lost=range(0, 8000, 100)), 8000))
    outcome("11-⛔⛔ «burst» that loses 1 % but ONE AT A TIME: it is «perdita-1» "
          "in disguise, and the bench KEEPS SILENT", p, None, q)

    a_burst = [i for base in range(0, 8000, 500) for i in range(base, base + 5)]
    p, q = p_fault_set("raffica-1", _v_loss(1.0, independent=False),
                          reduce_probe(_make_arrivals(8000, lost=a_burst), 8000))
    outcome("12-⭐ real burst: 1 % in clusters of 5", p, True, q)

    p, q = p_fault_set("jitter-15", _v_jitter(15),
                          reduce_probe(_make_arrivals(8000, delay=20.0,
                                                   flicker=0.2), 8000))
    outcome("13-⛔ jitter requested 15 ms, measured 0.4: SILENT", p, None, q)

    p, q = p_fault_set("duplicazione-1", _v_duplication,
                          reduce_probe(_make_arrivals(8000), 8000))
    outcome("14-⛔ duplication requested and no duplicate: SILENT", p, None, q)

    # ── 3 · ⭐⭐ THE PREDICATE THE BENCH EXISTS FOR ────────────────────────
    print("\n  ── ⭐⭐ «disorder is not loss»: does the rate drop where "
          "nothing is lost? ──\n")
    ref = _make_round(60)
    clean = reduce_probe(_make_arrivals(8000, swaps=swaps), 8000)
    p, q = p_not_loss(_make_round(59), ref, clean, "riordino-25")
    outcome("15-⭐ reordering, rate intact (59 against 60)", p, True, q)

    p, q = p_not_loss(_make_round(40), ref, clean, "riordino-25")
    outcome("16-⛔⛔ THE DEFECT THE BENCH EXISTS TO FIND: 40/s against 60/s "
          "on a network that LOSES NOTHING", p, False, q)

    p, q = p_not_loss(_make_round(40), ref,
                           reduce_probe(_make_arrivals(8000, lost=range(0, 8000, 100),
                                                    swaps=swaps), 8000),
                           "riordino-25")
    outcome("17-⭐⭐ THE FALSE RED: same drop, but the probe saw 1 % of "
          "real loss — then the comparison isolates nothing and the bench KEEPS SILENT",
          p, None, q)

    p, q = p_not_loss(_make_round(40), {"outcome": "nothing"}, clean, "riordino-25")
    outcome("18-⛔ without a reference there is no comparison: SILENT", p, None, q)

    p, q = p_not_loss(B70.gauge([], 25, None, None), ref, clean, "jitter-30")
    outcome("19-⛔ the profile delivered nothing: SILENT", p, None, q)

    # ── 4 · «loss is paid in delay» ────────────────────────────────────────
    print("\n  ── «loss is paid in delay, not in frames» ──\n")
    lossy = reduce_probe(_make_arrivals(8000, lost=range(0, 8000, 100)), 8000)
    p, q = p_late_loss(_make_round(58, drift=1.5), ref, lossy, "perdita-1")
    outcome("20-⭐ at perdita-1 the rate holds and what pays is the drift", p, True, q)

    p, q = p_late_loss(_make_round(30), ref, lossy, "perdita-1")
    outcome("21-⛔⛔ at perdita-1 the rate halves: the loss was paid in "
          "FRAMES, and on streams that retransmit it should not be", p, False, q)

    # ── 4-bis · ⭐⭐ THE TWO PREDICATES THAT ON 23 AUGUST WERE ONE ──────────
    #
    # ⛔ It is the § that makes the cure credible: if these cases did not give what
    #    is written here, the renaming would only have been changing a sentence.
    print("\n  ── ⭐⭐ «the connection dropped» AND «the delivery stopped»: "
          "two facts, two predicates ──\n")

    ATTACHED = {"cliente_attaccato": True, "cliente_staccato": False,
                 "farewells": [], "is_open": True}

    # (a) the delivery REDUCTION, which is half of the tool
    healthy = _make_round_in_stretches([(25.0, 0.0)])
    c = healthy["delivery"]
    outcome("32-⭐ healthy delivery: 25 full s → coverage 25/25, no gap",
          (c["secondi_visti"] == 25 and c["buco_max_s"] < 0.5), True,
          "coverage %d/%d · gap %.2f s" % (c["secondi_visti"],
                                             c["secondi_finestra"], c["buco_max_s"]))

    # ⛔ THE REAL CASE OF 23 AUGUST: the delivery dies at 0.3 s of the 25.
    dead_run = _make_round_in_stretches([(0.3, 24.7)])
    c = dead_run["delivery"]
    outcome("33-⛔⛔ THE REAL CASE: the delivery stops at 0.3 s → 1 s out of 25 and a "
          "TAIL gap of 24.7 s (⚠ without counting the tail the gap would be ZERO)",
          (c["secondi_visti"] == 1 and 24.0 < c["buco_max_s"] < 25.0), True,
          "coverage %d/%d · gap %.2f s from %.2f" % (c["secondi_visti"],
          c["secondi_finestra"], c["buco_max_s"], c["buco_da_s"]))

    # ⭐ And the gap IN THE MIDDLE, which coverage alone would not see as red.
    holed = _make_round_in_stretches([(10.0, 3.0), (12.0, 0.0)])
    c = holed["delivery"]
    outcome("34-⭐ a 3 s gap IN THE MIDDLE: coverage 22/25 and gap 3.0 s",
          (2.9 < c["buco_max_s"] < 3.2 and c["secondi_visti"] == 22), True,
          "coverage %d/%d · gap %.2f s from %.2f" % (c["secondi_visti"],
          c["secondi_finestra"], c["buco_max_s"], c["buco_da_s"]))

    # (b) THE DELIVERY PREDICATE — red, green and mute
    p, q = p_delivery_never_stops(healthy)
    outcome("35-⭐ healthy delivery: the delivery did not stop", p, True, q)

    p, q = p_delivery_never_stops(dead_run)
    outcome("36-⛔⛔ THE RED THE BENCH EXISTS TO GIVE: delivery stopped at 0.3 s "
          "out of 25", p, False, q)

    p, q = p_delivery_never_stops(holed)
    outcome("37-⛔ the screen frozen for 3 s IN THE MIDDLE of a live session: red, and "
          "coverage alone (88 %) would barely say it", p, False, q)

    short_v = _make_round_in_stretches([(12.0, 0.4), (12.6, 0.0)])
    p, q = p_delivery_never_stops(short_v)
    outcome("38-⭐ a 0.4 s gap: BELOW the %.1f s threshold — at 40/s it is a "
          "retransmission, not a frozen screen" % FROZEN_SCREEN_GAP_S,
          p, True, q)

    p, q = p_delivery_never_stops({"outcome": "measured"})
    outcome("39-⛔ no delivery reduction: SILENT", p, None, q)

    p, q = p_delivery_never_stops(B70.gauge([], 0, None, None))
    outcome("40-⛔ window of ZERO seconds: I do not even know what I had "
          "asked for — SILENT", p, None, q)

    # (c) THE CONNECTION PREDICATE — and the case that fooled the bench
    p, q = p_connection_alive(ATTACHED)
    outcome("41-⭐⭐ THE SAME RUN AS CASE 36, asked of the WITNESSES OF THE "
          "CONNECTION: client attached, no farewell → GREEN", p, True, q)

    p, q = p_connection_alive({"cliente_attaccato": False, "cliente_staccato": True,
                               "drop": "idle timeout", "farewells": [],
                               "is_open": True})
    outcome("42-⛔ the client says it dropped, AND SAYS WHY", p, False, q)

    p, q = p_connection_alive({"cliente_attaccato": True, "cliente_staccato": False,
                               "farewells": ["18:22:07 wt  farewell motivo=0x0F "
                                           "SILENCE"], "is_open": True})
    outcome("43-⛔⛔ the log carries a FAREWELL while the client said it was "
          "attached: red, and it says the two witnesses do not agree",
          p, False, q)

    p, q = p_connection_alive({"cliente_attaccato": False, "cliente_staccato": False,
                               "farewells": [], "is_open": True})
    outcome("44-⛔ no witness spoke: SILENT (⛔ it is not a polite green)",
          p, None, q)

    p, q = p_connection_alive({"cliente_attaccato": False, "cliente_staccato": True,
                               "drop": "the handshake did not close",
                               "farewells": [], "is_open": False})
    outcome("45-⭐⭐ THE FALSE RED: the session NEVER OPENED — it looks "
          "the same as a detachment and is not one, so it KEEPS SILENT", p, None, q)

    p, q = p_connection_alive(None)
    outcome("46-⛔ no witness questioned: SILENT", p, None, q)

    # (d) ⛔⛔ AND THE PAIR, which is the point of the whole cure: THE SAME RUN
    #     must give RED on the delivery and GREEN on the connection.
    pc, qc = p_delivery_never_stops(dead_run)
    ps, qs = p_connection_alive(ATTACHED)
    outcome("47-⭐⭐⭐ THE CASE THAT FOOLED THE BENCH — delivery stopped WITH "
          "connection alive: red on one, GREEN on the other, and never again a "
          "farewell to look for that is not there",
          (pc is False and ps is True), True,
          "delivery → %s · connection → %s" % (pc, ps))

    # ── 4-ter · ⭐ THE THIRD LEG: a contract on the text is tested on the TEXT ─
    print("\n  ── ⭐ the `network-quic` lines: `cwnd`, `cwnd_left` and the not-sent ──\n")
    LINE = ("18:22:07.412 wt  network-quic 192.168.0.2:52344 da_ms=1002 lost=7 "
            "lost_d=3 byte_lost=9856 shipped=48210 shipped_d=812 "
            "cwnd=%d cwnd_left=0 ssthresh=32000 inflight=9800 srtt_us=41230 "
            "rttvar_us=11400 pto_us=132000 dgram_lost=4 dgram_ok=696 "
            "dgram_false=11 judgment=⛔ the line is losing")
    q = reduce_quic_network([LINE % 48000, LINE % 10240, LINE % 10240])
    outcome("48-⭐ three lines read: cwnd min 10 240, end 10 240, and the «judgment» "
          "reaches the end of the line spaces included",
          (q["line_list"] == 3 and q["cwnd_min"] == 10240 and q["cwnd_fine"] == 10240
           and q["dgram_false"] == 11
           and list(q["judgments"]) == ["⛔ the line is losing"]), True,
          json.dumps({k: q[k] for k in ("line_list", "cwnd_min", "cwnd_fine",
                                        "cwnd_left_mediana", "dgram_false")},
                     ensure_ascii=False))

    q = reduce_quic_network(["18:22:07 wt  any other line of the log"])
    outcome("49-⛔ binary older than the `network-quic` line: «NOTHING TO "
          "READ», ⛔ not zeros (`CODER.md` §3.10)",
          q.get("outcome", "").startswith("NOTHING TO READ"), True,
          q.get("outcome"))

    # ── 5 · MY queue, and the predicates imported from b70 ─────────────────
    print("\n  ── my queue, and the predicates imported from 09-b70 ──\n")
    p, q = p_my_queue("liscio", True, {"packets": 500000, "dropped": 0, "byte": 700e6})
    outcome("22-⭐ my queue throws nothing away", p, True, q)

    p, q = p_my_queue("riordino-25", True,
                      {"packets": 500000, "dropped": 5000, "byte": 700e6})
    outcome("23-⛔⛔ my queue throws away 1 % on a lossless profile: every "
          "number is contaminated", p, False, q)

    p, q = B70.p_degrades_over_time(_make_round(30, key_every=1))
    outcome("24-⛔ the KEYFRAME SPIRAL (§3.3): 30/s but all keyframes", p, False, q)

    # ⛔ «Dies halfway» = delivered 10 s of the 25 requested.  ⚠ And the run is
    #    fabricated by hand, not with `_make_round`, because that one ALWAYS delivers
    #    the whole requested time: a helper that cannot fabricate the defect cannot
    #    certify the predicate that looks for it.
    dead = B70.gauge(B70._fab([(60, 10)]), 25,
                       {"delivered": 600, "shipped": 600, "abandoned": 0,
                        "non_spediti": 0, "annunci_tela": 0}, None)
    p, q = B70.p_nothing_detach(dead)
    outcome("25-⚠ THE OLD PREDICATE, and we prove it still does what it did: "
          "the delivery lasts 10 s out of the 25 requested and it says «it detached» — "
          "⛔ the number is right and the word is not (⇒ cases 36 and 41)",
          p, False, q)

    p, q = B70.p_I1(_make_round(18, cons=1000, sped=620, aband=40), _make_round(30))
    outcome("26-⛔⛔ I1 broken: with the scene STILL the rate drops and the delivered are "
          "equal", p, False, q)

    p, q = B70.p_I1(_make_round(18, cons=550, sped=550), _make_round(30))
    outcome("27-⭐⭐ the false red of I1: with the scene still the compositor "
          "delivered half — it is UPSTREAM of us, and the bench KEEPS SILENT", p, None, q)

    # ── 6 · reading the rule back: the real trap of 23 August ──────────────
    print("\n  ── ⛔ the rule read back: `tc qdisc change` is STICKY ──\n")
    p, q = check_rule(["delay", "15ms", "loss", "1%"],
                            "qdisc netem 40: parent 1:4 limit 20000 delay 15ms loss 1%")
    outcome("28-⭐ the rule read back is the one requested", p, True, q)

    p, q = check_rule(["delay", "15ms", "loss", "1%"],
                            "qdisc netem 40: parent 1:4 limit 20000 delay 15ms "
                            "loss 1% reorder 25% 50% gap 1")
    outcome("29-⛔⛔ THE REAL CASE: a `reorder` left over from the previous profile — and "
          "I would have measured a network nobody asked for", p, False, q)

    p, q = check_rule(["delay", "10ms", "reorder", "25%", "50%"],
                            "qdisc netem 40: parent 1:4 limit 20000 delay 10ms")
    outcome("30-⛔ I asked for reordering and the rule does not have it", p, False, q)

    p, q = check_rule(["delay", "30ms"], "")
    outcome("31-⛔ no netem read back: the rule is not there", p, False, q)

    print("\n== %s" % ("⭐ THE BENCH CAN SEE THE DEFECTS IT LOOKS FOR — and can KEEP SILENT "
                       "where it cannot judge"
                       if green_v else
                       "⛔⛔ THE BENCH CANNOT SEE WHAT IT LOOKS FOR: none of its greens "
                       "is to be believed"))
    return 0 if green_v else 1


def import_fake():
    """⛔ The positive control does not touch the machine, but it needs b70's
       REDUCTION (`gauge`, `_fab`, the four predicates).  ⇒ The module is
       imported and that is all, **without** hooking the network to it: `NETWORK` stays `None` and
       no function that talks to the machine is reachable from here."""
    global B70
    if B70 is None:
        B70 = _load("b70ritmo", os.path.join(HERE, "09-b70-ritmo.py"))
    # ⭐ …but the DELIVERY reduction is hooked all the same: it is half of the
    #    cure of 23 August, and a positive control that did not exercise it
    #    would certify a bench different from the one that runs.
    _hook_delivery()


# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT TALKS TO THE TEST MACHINE
# ═══════════════════════════════════════════════════════════════════════════
def write_on_machine(label_name, body_text):
    """⛔ In base64: the quotes of a heredoc inside a `sudo -S` inside an
       `ssh` are three levels of quoting, and a wrong one does not give an error —
       it gives a truncated file.

    ⛔⛔ AND THE WHOLE CHAIN GOES INSIDE A `bash -c`, and it is a FINDING made here
        on 23 August 2026 — it also applies to `09-b70-ritmo.py`
        (`ship_reader()`, line ~1300), which suffers from it:

          printf … | sudo -S -p '' mkdir -p LAV && printf '…' | base64 -d > LAV/x

        `sudo` covers **only the `mkdir`**.  The second half of the chain runs
        as `nicfio`, and `LAV` belongs to `root` with permissions 755 ⇒
        *«Permission denied»*, the file is not written, and the bench says «the
        reader was not written» without knowing why.
        ⚠ And on the tree of whoever already has that file from a previous run the
          defect is **invisible**: `wc -c` finds the old file and gives green.
        ⇒ Here the whole chain sits inside a `bash -c "…"`, so `sudo` covers
          everything.  ⭐ And **b70's reader** is written too, with the same
          remedy, because without it the §11.1 trace is not reduced.
    """
    b = base64.b64encode(body_text.encode("utf-8")).decode("ascii")
    root("bash -c \"mkdir -p %s && printf '%%s' '%s' | base64 -d > %s/%s\""
         % (LAV, b, LAV, label_name))
    rc, out, _ = root("bash -c \"wc -c < %s/%s\"" % (LAV, label_name))
    return out.strip().isdigit() and int(out.strip()) > 800


# ⛔⛔ AND THE SECOND FINDING OF THE SAME DAY, WORSE THAN THE FIRST BECAUSE IT IS
#     MUTE: **a trailing `< file` steals stdin from `sudo -S`**, which then does not
#     receive the password and answers *«3 incorrect password attempts»*.
#     ⚠ It is written in black and white in `07-b64-terreno.sh` line ~240 — *«no
#       `</dev/null` at the end: that redirect wins over `sudo -S`»* — and it came back
#       all the same in `09-b70-ritmo.py`, twice:
#         · `ship_reader()`  → `wc -c < …` : the file **was there** (2 198 bytes
#           measured) and the bench said «it was not written»;
#         · `log_line_list()`    → `wc -l < …` : returns **0** silently, and
#           then `server_counts()` reads the log **from the beginning** instead
#           of from this run.  ⛔ The «final count» lines survive (there is a
#           `tail -1`), but the `cycle:` lines do not: `catturati` and **`waits a
#           blank`** become cumulative since the server was started — that is
#           the column on which I1 decides whether to refuse to judge.
#     ⇒ Here it is fixed **without touching b70's file**: its function is
#       replaced with one that puts the redirect inside a `bash -c`.
def log_line_list():
    rc, out, _ = root("bash -c \"wc -l < %s/registro.log 2>/dev/null || echo 0\""
                      % LAV)
    try:
        return int(out.strip())
    except Exception:
        return 0
# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE WITNESSES OF THE CONNECTION — and we ASK, we do not deduce
# ═══════════════════════════════════════════════════════════════════════════
def connection_witnesses(line0, n):
    """⛔ It collects, it does not judge: judging is the job of `p_connection_alive()`, and the two
       are certified on fabricated witnesses.

    ⚠ The client is read IN FULL (`LAST_CLIENT`), not from the 400 bytes of
      `coda_cliente`: the line that answers sits further up.
    """
    queue = LAST_CLIENT["body_text"] or (n.get("coda_cliente") or "")
    t = {"cliente_attaccato": "still attached after" in queue,
         "cliente_staccato": "I did NOT stay attached" in queue}
    if t["cliente_staccato"]:
        for r in queue.splitlines():
            if "I did NOT stay attached" in r:
                t["drop"] = r.split(":", 1)[-1].strip()[:200]
    rc, out, _ = root("bash -c \"tail -n +%d %s/registro.log | grep -a -i "
                      "'farewell motivo=\\|the client takes its farewell\\|slot DENIED"
                      "\\|BANNED\\|GIA_ATTIVA' | tail -5\"" % (line0 + 1, LAV))
    t["farewells"] = [x[:200] for x in out.splitlines() if x.strip()]
    # ⚠ THE THIRD POSSIBILITY: «it never opened» looks the same as a
    #   detachment.  It is ruled out by reading the opening, not the frames.
    rc, out, _ = root("bash -c \"tail -n +%d %s/registro.log | grep -a "
                      "'ADMITTED\\|session open username=\\|monitor «' | head -3\""
                      % (line0 + 1, LAV))
    t["opening"] = [x[:180] for x in out.splitlines() if x.strip()]
    t["is_open"] = bool(t["opening"]) or bool(n.get("fotogrammi_grezzi"))
    return t


def print_witnesses(t):
    _inf("DETACH  client: %s · farewells in the log: %s · opened: %s"
         % ("⭐ still attached" if t.get("cliente_attaccato") else
            ("⛔ dropped — %s" % t.get("drop")) if t.get("cliente_staccato")
            else "did not say",
            len(t.get("farewells") or []) or "NONE", t.get("is_open")))
    for r in (t.get("farewells") or [])[:3]:
        _inf("        farewell: %s" % r)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE THIRD LEG — the `network-quic` lines (⇒ §«THE THIRD LEG» at the top)
# ═══════════════════════════════════════════════════════════════════════════
def read_quic_network(line0):
    """⭐ `src/webtransport.c:3772` fixes the format as a **contract on the
       text**: stable `network-quic` prefix, `name=value` fields without spaces in the
       value, and `judgment=` LAST with the value running to the end of the line.
       ⇒ `split()` and `split('=', 1)` are enough, and `judgment` is taken apart.

    ⛔ It does not judge: it reads and prints.  A threshold on `cwnd` would be a promise
       the product never made.
    ⚠ And if the binary is older than the line, it returns «NOTHING TO READ» —
       which is not «zero» (`CODER.md` §3.10).
    """
    rc, out, _ = root("bash -c \"tail -n +%d %s/registro.log | grep -a "
                      "'network-quic ' | tail -400\"" % (line0 + 1, LAV))
    return reduce_quic_network(out.splitlines())


def reduce_quic_network(line_list):
    """⛔ The reduction lives apart because it is the one `--certify` exercises
       on fabricated lines: a contract on the text is tested on the TEXT."""
    line_list = [r for r in line_list if "network-quic " in r]
    if not line_list:
        return {"outcome": "NOTHING TO READ — no «network-quic» line in this "
                         "run (⚠ binary older than 23 Aug 2026?)"}
    fields = []
    for r in line_list:
        body_el, judge = r.split("network-quic ", 1)[1], ""
        if "judgment=" in body_el:
            body_el, judge = body_el.split("judgment=", 1)
        d = dict(p.split("=", 1) for p in body_el.split() if "=" in p)
        d["judgment"] = judge.strip()
        fields.append(d)

    def num(d, k):
        try:
            return int(d.get(k))
        except (TypeError, ValueError):
            return None

    def listing(k):
        return [x for x in (num(d, k) for d in fields) if x is not None]

    latest, judgments = fields[-1], {}
    for d in fields:
        judgments[d["judgment"]] = judgments.get(d["judgment"], 0) + 1
    cwnd, left, srtt = listing("cwnd"), listing("cwnd_left"), listing("srtt_us")
    return {"outcome": "read", "line_list": len(fields),
            "persi_tot": num(latest, "lost"),
            "spediti_tot": num(latest, "shipped"),
            "cwnd_min": min(cwnd) if cwnd else None,
            "cwnd_mediana": sorted(cwnd)[len(cwnd) // 2] if cwnd else None,
            "cwnd_fine": num(latest, "cwnd"),
            "cwnd_left_min": min(left) if left else None,
            "cwnd_left_mediana": sorted(left)[len(left) // 2] if left else None,
            "srtt_us_mediana": sorted(srtt)[len(srtt) // 2] if srtt else None,
            "srtt_us_max": max(srtt) if srtt else None,
            "pto_us_fine": num(latest, "pto_us"),
            "dgram_lost": num(latest, "dgram_lost"),
            "dgram_ok": num(latest, "dgram_ok"),
            "dgram_false": num(latest, "dgram_false"),
            "judgments": judgments}


def print_third_leg(n, q):
    """⭐ The two numbers that at `raffica-forte` closed the diagnosis by themselves:
       `[M]` 860 not sent out of 981 and `cwnd` at ~10 KB ⇒ «nothing dropped,
       it is the pacer refusing»."""
    s = (n.get("server") or {})
    sp = (s.get("spiral") or {})
    _inf("WHY     not sent %s out of %s delivered (%s sent on the wire) · "
         "«FRAME NOT SENT» lines %s · «keyframe waits» %s"
         % (s.get("non_spediti"), s.get("delivered"), s.get("shipped"),
            sp.get("delta_non_spedito"), sp.get("chiave_aspetta")))
    if q.get("outcome") != "read":
        _dub("QUIC    %s" % q.get("outcome"))
        return
    _inf("QUIC    %d lines · cwnd min %s / median %s / end %s bytes · "
         "cwnd_left median %s · lost %s out of %s sent"
         % (q["line_list"], q["cwnd_min"], q["cwnd_mediana"], q["cwnd_fine"],
            q["cwnd_left_mediana"], q["persi_tot"], q["spediti_tot"]))
    _inf("        median srtt %s us (max %s) · final pto %s us · datagrams: "
         "lost %s, acknowledged %s, ⭐ FALSE %s (= reordering seen by the server)"
         % (q["srtt_us_mediana"], q["srtt_us_max"], q["pto_us_fine"],
            q["dgram_lost"], q["dgram_ok"], q["dgram_false"]))
    _inf("        server judgements: %s"
         % json.dumps(q["judgments"], ensure_ascii=False))


def choose_probe_port():
    """⛔ The port is chosen NOW, not yesterday: on this machine there are other
       agents starting servers while I run."""
    global PROBE_PORT
    for port in PROBE_PORTS:
        rc, out, _ = root("bash -c \"ss -uln | grep -c ':%d ' || true\"" % port)
        if out.strip() == "0":
            PROBE_PORT = port
            return port
    return None


def ship_probe():
    ok_s = write_on_machine("09-b76-sonda.py", PROBE)
    ok_l = write_on_machine("09-b70-leggi.py", B70.READER)
    if not ok_l:
        _ko("the §11.1 trace reader was not written in %s" % LAV)
    return ok_s and ok_l


def probe_filters():
    """⛔ Two more `u32` filters, on **my** port 7931 and in the same band
       1:4: it is the only way for the probe to cross the SAME `netem` as the
       run.  ⚠ If it went through the default band it would measure a smooth
       network and say «the fault is not there» on every profile."""
    for which_way in ("sport", "dport"):
        root("/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
             "match ip protocol 17 0xff match ip %s %d 0xffff flowid 1:4"
             % (DEV, which_way, PROBE_PORT))


def run_probe():
    rc, out, err = root("python3 %s/09-b76-sonda.py %d %d %s 1452"
                        % (LAV, PROBE_PORT, PROBE_PACKETS, PROBE_STEP_MS),
                        180)
    try:
        d = json.loads(out)
    except Exception as e:
        _dub("the probe did not answer: %s — %s" % (e, (out + err)[-200:]))
        return None
    return reduce_probe(d.get("arrivals") or [], d.get("how_many") or 0)


def scene_turn_on(motion):
    """⛔⛔ It is the ONLY thing of `09-b70` that cannot be imported, and the reason is
       isolation: `09-b70.scene_turn_on()` writes the shared memory in
       `/09-b70`, and today on the same machine there is b70's agent with
       user `provan9`.  `shm_open(..., 0644)` of a file that belongs to another
       user gives EACCES and the scene **dies at startup** — a fault that
       looks in every way like «the compositor does not deliver».
       ⇒ Same line, my own shared memory: `%s`.

    ⭐ And «still scene» stays `--motion mark`, not the scene turned off: only
       the mark changes, so the capture cadence is that of the moving run and what
       changes is the COST, which is the only thing I1 wants to isolate.
    """ % SHM
    scene_turn_off()
    rc, out, _ = root("grep -ao 'monitor «[^»]*»' %s/registro.log | tail -1" % LAV)
    m = re.findall("monitor «([^»]*)»", out)
    usc = m[-1] if m and m[-1] else None
    if not usc:
        return None
    root("setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
         "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
         "XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 "
         "%s --out_dir %s --motion %s --shm %s --lap b76 "
         ">/dev/null 2>&1 & echo lit"
         % (UID_B, UID_B, ACCOUNT, ACCOUNT, UID_B, B70.SCENE_BIN, usc, motion, SHM))
    time.sleep(1.5)
    rc, out, _ = root("pgrep -u %d -f '04-b30-scena --out_dir' | head -1" % UID_B)
    return usc if out.strip() else None


def scene_turn_off():
    root("pkill -u %d -f 04-b30-scena; true" % UID_B)


def renew(chi, seconds):
    """⛔ Leases are taken SHORT and renewed: there are other agents in
       the queue, and a long lease stops them even when I have finished.
       ⚠ And it is renewed only if the lock is still MINE: if I was
         broken open, renewing would mean stealing it from whoever took over."""
    other_one, _ = LUC.state()
    if other_one != chi:
        return False
    LUC._root("bash -c \"printf '%%s %%s\\n' %d '%s' > %s/chi\""
              % (int(time.time() + seconds), chi, LUC.SLOT))
    return True


def print_delivery(n):
    """⭐ The line that was missing on 23 August: not «how long it lasted», but **for
       how many seconds the screen saw something** and **how long it was frozen
       in a row**."""
    c = (n or {}).get("delivery") or {}
    if c.get("outcome") != "measured":
        _dub("DELIVERY %s" % c.get("outcome", "not reduced"))
        return
    _inf("DELIV.  %d s out of %d saw at least one frame (%.0f %%) · longest "
         "gap %.2f s (from %.2f) · last frame at %.2f s · %d "
         "frames in the window"
         % (c["secondi_visti"], c["secondi_finestra"], c["coverage"] * 100,
            c["buco_max_s"], c["buco_da_s"], c["consegna_fino_a_s"],
            c["frames"]))


def print_probe(s):
    if not _has_probed(s):
        _dub("PROBE  %s" % (s or {}).get("outcome", "did not measure"))
        return
    _inf("PROBE   lost %d/%d = %.2f %% in %d bursts (average %.2f, max %d) · "
         "duplicates %d (%.2f %%) · out of order %d (%.1f %%)"
         % (s["lost"], s["how_many"], s["persi_pc"], s["bursts"],
            s["raffica_media"], s["raffica_max"], s["duplicates"],
            s["duplicati_pc"], s["out_of_order"], s["fuori_ordine_pc"]))
    _inf("        delay min %.2f · median %.2f · p95 %.2f · max %.2f ms "
         "(spread p95−min %.2f)"
         % (s["ritardo_min_ms"], s["ritardo_mediano_ms"], s["ritardo_p95_ms"],
            s["ritardo_max_ms"], s["dispersione_ms"]))


# ═══════════════════════════════════════════════════════════════════════════
def primary():
    p = argparse.ArgumentParser()
    p.add_argument("step", nargs="?", choices=["terrain", "probe", "restore", "state"])
    p.add_argument("--certify", action="store_true",
                   help="⭐ the positive control: proves that the bench can see "
                        "the defects it looks for. It does not touch the test machine")
    p.add_argument("--seconds", type=int, default=25)
    p.add_argument("--solo", default="",
                   help="one or more profiles, by piece of name, separated by "
                        "commas (⚠ «perdita-0,5» has the comma in its name: "
                        "write «perdita-0»)")
    p.add_argument("--wait", type=int, default=2400,
                   help="how many seconds I wait for the netem lock")
    p.add_argument("--no-pair", action="store_true",
                   help="skips the I1 pair on «casa-cattiva»")
    a = p.parse_args()

    if a.certify:
        return certify()
    if not a.step:
        p.error("a step is needed, or --certify")

    os.makedirs(OUT, exist_ok=True)
    import_it()

    if a.step in ("restore", "state"):
        _log("the test machine's network — dev «%s», port %d" % (DEV, PORT))
        return 0 if NETWORK.restore() else 2

    if a.step == "terrain":
        # ⛔ FIRST the two scripts, THEN the check: b70's `terrain_check()`
        #    looks for the reader and cannot write it (see `write_on_machine`).
        ok = ship_probe()
        return 0 if (B70.terrain_check() and ok) else 2

    _log("09-b76 · THE BAD NETWORK — port %d · dev «%s»" % (PORT, DEV))
    print("   ⛔ «%s» (ssh + the user's session) is NOT touched" % FORBIDDEN)
    print("   ⛔ no profile carries `rate`: here the pipe is wide and the fault is")
    print("      LOSS, REORDERING and FLICKER — bandwidth belongs to 09-b70")
    print("   --  «%s» before: %s" % (DEV, NETWORK.qdisc() or "(none)"))
    if not ship_probe():
        _ko("the scripts were not written in %s" % LAV)
        return 2
    if choose_probe_port() is None:
        _ko("⛔ none of my probe ports (%s) is free: I do NOT measure, "
            "because without the probe I do not know whether the fault was put in"
            % ",".join(str(x) for x in PROBE_PORTS))
        return 2
    _ok("the probe and the trace reader are in %s · the probe will use "
        "port %d" % (LAV, PROBE_PORT))
    if not B70.terrain_check():
        return 2

    # ⛔ `--solo` takes a comma-separated LIST, and it is not a convenience:
    #    the `netem` lock is only one for the whole machine and there are
    #    other agents queued.  ⇒ Being able to run four profiles instead of
    #    fourteen is the difference between holding the lock six minutes and
    #    holding it half an hour.
    desired = [x.strip() for x in (a.solo or "").split(",") if x.strip()]
    chosen = [p for p in PROFILES if not desired or any(v in p[0] for v in desired)]
    if not chosen:
        _ko("no profile matches «%s»" % a.solo)
        return 2
    # ⚠ And the REFERENCE must be there: without it «disorder is not loss»
    #   and «loss is paid in delay» have no denominator and KEEP SILENT —
    #   which is an honest but useless outcome, and better said before running.
    if desired and not any(x[0] == REFERENCE for x in chosen):
        _dub("⚠ «%s» is not among the chosen profiles: the comparisons will keep silent for "
             "lack of a denominator" % REFERENCE)
    how_many = len(chosen) + (1 if (not a.no_pair and
                                  any(x[0] == "casa-cattiva" for x in chosen)) else 0)

    # ═══ ⛔ THE LOCK — the netem on `lo` is ONLY ONE for the whole machine ═
    #
    # ⛔ Whoever does not manage STOPS, does not measure anyway: another bench that
    #    breaks the same `lo` does not give a red, it gives a plausible and
    #    false number (`LEZIONI.md` §1.26).
    CHI = "09-b76-rete-cattiva"
    LEASE = 900
    try:
        LUC.take(CHI, seconds=LEASE, wait=a.wait)
    except Exception as e:
        _ko("⛔ I DO NOT MEASURE: %s" % e)
        return 2
    expiry = time.time() + LEASE

    outcomes, rossi, muted = [], [], []
    reference = None
    NETWORK.guardian_arm(min(3600, how_many * (a.seconds + 130) + 600))
    try:
        _inf("opening a short session to bring the stage and the monitor to life")
        if not B70.trigger_session():
            _ko("the session does not open: I do not measure")
            return 2

        for label_name, rules, full, spiral, without_loss, reason_text, verify in chosen:
            if time.time() > expiry - 400:
                if renew(CHI, LEASE):
                    expiry = time.time() + LEASE
                    _inf("⛔ lock lease renewed for %d s (the queue "
                         "must move: other agents are waiting)" % LEASE)
                else:
                    _ko("⛔ the lock is no longer mine: I STOP")
                    break
            _log("%s · %s" % (label_name, reason_text))
            ok, q = NETWORK.tighten(_rules(rules))
            if not ok:
                _ko(q)
                rossi.append("%s · tc refused the rule" % label_name)
                break
            probe_filters()
            reread = rule_reread()
            pass_r, why_r = check_rule(rules, reread)
            (_ok if pass_r else _ko)("the rule: %s" % why_r)
            if not pass_r:
                rossi.append("%s · the installed rule is not the one requested" % label_name)
                continue

            # ⭐ FIRST the probe, THEN the run: so the qdisc counters I
            #   read around the run do not include the probe's packets.
            s = run_probe()
            print_probe(s)
            pass_g, why_g = p_fault_set(label_name, verify, s)
            (_ok if pass_g else (_dub if pass_g is None else _ko))(
                "THE FAULT WAS PUT IN: %s" % why_g)

            entries = {"profile_v": label_name, "rules": " ".join(_rules(rules)),
                    "rule_reread": reread, "requisito_pieno": full,
                    "spirale_e_resa": spiral, "without_loss": without_loss,
                    "reason_text": reason_text, "probe": s,
                    "fault": {"pass_on": pass_g, "reason_text": why_g},
                    "predicates": []}
            if pass_g is False:
                rossi.append("%s · the fault: %s" % (label_name, why_g[:90]))
            elif pass_g is None:
                muted.append("%s · the fault was not put in — %s"
                            % (label_name, why_g[:90]))

            pair = {}
            directions = [("move", "bar")]
            if label_name == "casa-cattiva" and not a.no_pair:
                directions.append(("halt", "mark"))
            before = qdisc_counts()
            for label, motion in directions:
                usc = scene_turn_on(motion)
                if not usc:
                    _ko("the scene «%s» does not start: I do NOT judge this run" % motion)
                    pair[label] = {"outcome": "I HAVE NOTHING TO JUDGE — "
                                                  "the scene did not start"}
                    continue
                _inf("scene «%s» on monitor %s" % (motion, usc))
                # ⛔ The line from which to read the log is taken BEFORE the run:
                #    the farewells and the `network-quic` lines of this run are those
                #    that come AFTER, and reading from the start of the log
                #    would attribute to me the farewells of whoever ran before.
                line0 = log_line_list()
                n = B70.lap("%s-%s" % (label_name, label), motion,
                             B70.FULL_CANVAS, a.seconds)
                n["witnesses"] = connection_witnesses(line0, n)
                n["quic"] = read_quic_network(line0)
                print("   [%s]" % label)
                B70.print_round(n)
                print_delivery(n)
                print_witnesses(n["witnesses"])
                print_third_leg(n, n["quic"])
                pair[label] = n
                scene_turn_off()
            after = qdisc_counts()
            delta = None
            if before and after:
                delta = {k: after[k] - before[k] for k in before}
            entries["qdisc"] = delta
            _inf("QDISC   around the run: %s" % json.dumps(delta))

            n = pair.get("move") or {}
            if label_name == REFERENCE and B70._has_measured(n) and pass_g:
                reference = n
                _ok("⭐ «%s» becomes the REFERENCE of all the comparisons "
                    "(%.2f frames/s)" % (label_name, n["fps"]))

            # ── the predicates, and each says whether it COUNTS for this profile ─
            listing = []
            # ⭐⭐ THE TWO PREDICATES THAT ON 23 AUGUST 2026 WERE ONE — and they are
            #    two different facts with two different causes (⇒ § at the top).
            pass_on, why2 = p_connection_alive(n.get("witnesses"))
            listing.append(("⛔ the CONNECTION did not drop (§3.3/§8.3: «never "
                           "detach» — it holds everywhere)", pass_on, why2, True))
            pass_on, why2 = p_delivery_never_stops(n)
            listing.append(("⭐⭐ the DELIVERY did not stop (coverage ≥ %.2f "
                           "· no gap ≥ %.1f s)"
                           % (MIN_COVERAGE, FROZEN_SCREEN_GAP_S),
                           pass_on, why2, True))
            # ⚠ And the old one runs all the same, marked «diagnosis»: its number
            #   stays next to the two new ones, so whoever rereads yesterday's grid
            #   sees by themselves what was renamed and what was not.
            pass_on, why2 = B70.p_nothing_detach(n)
            listing.append(("⚠ b70's old «does not detach» — it measures the DURATION "
                           "of the delivery and calls it detachment: here it is diagnosis",
                           pass_on, why2, False))
            pass_on, why2 = B70.p_degrades_over_time(n)
            listing.append(("no keyframe spiral (§3.3)", pass_on, why2, spiral))
            pass_on, why2 = B70.p_rate_floor(n)
            listing.append(("the rate floor (§2.1: 25/s)", pass_on, why2, full))
            pass_on, why2 = B70.p_delay_no_runaway(n)
            listing.append(("the drift does not run away", pass_on, why2, full))
            pass_on, why2 = p_my_queue(label_name, without_loss, delta)
            listing.append(("⛔ MY queue throws nothing away of its own", pass_on,
                           why2, without_loss))
            if without_loss and label_name not in ("liscio", REFERENCE):
                pass_on, why2 = p_not_loss(n, reference, s, label_name)
                listing.append(("⭐⭐ disorder is NOT loss", pass_on, why2, True))
            if not without_loss:
                pass_on, why2 = p_late_loss(n, reference, s, label_name)
                listing.append(("loss is paid in DELAY, not in frames",
                               pass_on, why2, spiral))

            for label, pass_on, why2, tally in listing:
                entries["predicates"].append({"predicate": label, "pass_on": pass_on,
                                          "reason_text": why2, "tally": tally})
                if not tally:
                    _inf("⚠ diagnosis · %s → %s (%s)"
                         % (label, pass_on, why2[:90]))
                    continue
                (_ok if pass_on else (_dub if pass_on is None else _ko))(
                    "%s: %s" % (label, why2))
                if pass_on is False:
                    rossi.append("%s · %s" % (label_name, label))
                elif pass_on is None:
                    muted.append("%s · %s — %s" % (label_name, label, why2[:90]))

            if "halt" in pair:
                pass_i1, why_i1 = B70.p_I1(pair.get("halt", {}),
                                               pair.get("move", {}))
                (_ok if pass_i1 else (_dub if pass_i1 is None else _ko))(
                    "I1 — the rate does not drop with the scene still: %s" % why_i1)
                entries["I1"] = {"pass_on": pass_i1, "reason_text": why_i1}
                if pass_i1 is False:
                    rossi.append("%s · I1" % label_name)
                elif pass_i1 is None:
                    muted.append("%s · I1 — %s" % (label_name, why_i1[:90]))
            entries["rounds"] = pair
            outcomes.append(entries)
    finally:
        scene_turn_off()
        _log("⛔ THE NETWORK IS PUT BACK AS IT WAS")
        restored = NETWORK.restore()
        LUC.release(CHI)

    with open(os.path.join(OUT, "09-b76-esiti.json"), "w") as f:
        json.dump(outcomes, f, ensure_ascii=False, indent=1)
    _inf("outcomes in %s/09-b76-esiti.json" % OUT)

    _log("THE VERDICT — %d profiles run · %d red · %d not judged"
         % (len(outcomes), len(rossi), len(muted)))
    for r in rossi:
        _ko(r)
    for m in muted:
        _dub(m)
    if not restored:
        _ko("⛔ the network did NOT go back as it was: put it back by hand with «restore»")
        return 2
    if rossi:
        return 1
    if muted:
        return 3
    _ok("⭐ all the predicates did what was written beforehand")
    return 0


if __name__ == "__main__":
    sys.exit(primary())
