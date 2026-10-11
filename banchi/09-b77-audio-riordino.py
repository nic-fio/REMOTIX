#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b77-audio-riordino — THE AUDIO REORDERING CURE, PAIRED.

⛔⭐ THE FACT TO CLOSE.  On 23 August 2026 `src/pagina.html` changed its
    reading of `RCP.md` §6.3.  Before: a PCM block arriving **behind a newer
    one** was thrown away, full stop (`istante <= last_instant` ⇒ `scartati_vecchi`).
    Now two cases are told apart:

      · «my place in time has ALREADY PASSED»  ⇒ it is really consumed, it is
        thrown away  (`scartati_vecchi`, and in `suona()` `scartati_tardivi`);
      · «I arrived behind a newer one but my place is STILL there»
        ⇒ it is kept and played at its absolute place  (`fuori_ordine`).

    ⛔⛔ AND THE HALF THAT MATTERS HAD NEVER BEEN VERIFIED.  For the cure
        to bite a network **that reorders** was needed, and it was never set up:
        there was a single number, the BEFORE, written in `src/pagina.html` line ~6474
        — `[M]` with `netem`, jitter ±2 ms ⇒ **purity 0.175, 1 004 blocks
        discarded out of ~5 000**.  This bench is the one that makes it bite.

⭐ PAIRED MEANS TWO RUNS IDENTICAL IN EVERYTHING EXCEPT THE RULE.  Same
   `netem` (set ONCE and left standing for both), same duration,
   same scene, same tone, same server.  The only thing that changes is
   `--audio-rule old|new`.
   ⛔ A single run with the cure on would prove nothing: it would look
      the same as a profile that does not reorder at all.  It is the reason
      `09-riavvia-7920.sh` exists, written for audio.

⛔ THE SWITCH BELONGS TO THE CLIENT, and it is not mine: it is in `banchi/01-b3-cliente.py`
   (`--audio-rule old|new`, default `old`).  This bench is
   written **against that interface**, and at startup it CHECKS that it is there: if
   not, it stops.  ⚠ Without the check, the two runs would use the same
   rule and the bench would report «no difference» — which looks the same
   as «the cure is not needed», and is the opposite conclusion.

⛔ THE `netem` ON `lo` IS ONLY ONE FOR THE WHOLE MACHINE: lock
   `banchi/09-lucchetto.py`, short lease, released in a `finally`.
   ⛔ `enp7s0` is NEVER touched; the `u32` filters are on **port 7931 only**;
   the guardian removes the qdisc even if this script dies.

⭐ THE QUANTITIES, AND THERE ARE THREE, BECAUSE ONE ALONE WOULD NOT BE ENOUGH:

   1. **`purezza` = `consegnati / sul_filo`**, and the CLIENT counts it.
      `sul_filo` are the conforming datagrams the network delivered, counted
      **before** the §6.3 screening; `consegnati` are those that came out of it.
      ⭐ It is the quantity the cure is judged on: the network's loss does not
      even enter the denominator, so what remains is **only** what
      the receiver decided to throw away.
      ⛔ It is NOT `purezza_pagina` (`consegnati/ricevuti`, the one the page
      benches measured with): there the discard does `continue` **before**
      `ricevuti++`, so the ratio is ~1.000 **with both rules**
      even on a destroyed sequence.  It is printed alongside, declared blind.

   2. **`copertura`** — how much of the timeline (from the first to the last
      `istante`) really received samples, and **I** count it from the blocks.
   3. **`purezza_tono`** — how much energy sits in the 440 Hz line, with the
      certified judge of `07-b42`, after putting the blocks back **in their place**
      (`base + istante`, as the page's anchor does).

   ⛔⭐ The last two are THE SECOND LEG, and it is not a luxury: `purezza` is
      computed by the client, which is also **the object of the measurement** — the cure lives
      there.  Coverage and tone come from the SAMPLES, and if the client said «I
      delivered everything» while half the timeline is silence, one of the
      two would be lying and it would show.

⛔⛔ THE `[M]` «purity 0.175» OF `pagina.html` LINE 6474 **IS NOT THE TERM OF
     COMPARISON**, and this bench does not lean on it: its definition is not
     known, and comparing a number whose definition is unknown with one
     whose definition is known is the most polite way of manufacturing a triumph.
     ⇒ The term of comparison is **the twin run**, measured the same day
     under the same `netem` with the same scene — and the expectation is a declared
     BOUND, not that point.

⛔ THE `reordered` COUNTER OF `tc` DOES NOT EXIST ON THIS MACHINE — `[M]` 23
   August 2026: `grep -ac reordered /usr/sbin/tc` ⇒ **0** (iproute2 6.15.0).
   ⇒ The proof that the profile REALLY reorders is taken in two ways, both
   better than the counter because they look at the REAL traffic:
     · the packets the netem saw pass (`Sent … pkt` of node `40:`),
       which says whether the `u32` filter bites — ⛔ at zero I would have measured a healthy
       network believing it broken;
     · the client's `fuori_ordine` and the overtakes counted on the JSONL, which say whether
       what passed really arrived out of sequence.

Usage (from the laptop):
    python3 banchi/09-b77-audio-riordino.py --certify     # ⛔ first of all
    python3 banchi/09-b77-audio-riordino.py terrain
    python3 banchi/09-b77-audio-riordino.py measure [--seconds 25] [--only jitter-2]
    python3 banchi/09-b77-audio-riordino.py restore
"""
import argparse, base64, importlib.util, json, math, os, re, struct, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ ISOLATION, and it is written BEFORE importing anything: the modules
#    below read the environment at import time, not at call time.
#    ⚠ Putting it after the import would give a bench that runs on someone else's port
#      and does not notice — `LEZIONI.md` §1.26.
# ═══════════════════════════════════════════════════════════════════════════
PORT = int(os.environ.get("PORT", "7931"))
ACCOUNT = os.environ.get("ACCOUNT", "provanr2")
UID_B = int(os.environ.get("UID_B", "1031"))
TREE_DIR = os.environ.get("TREE", "/media/REMOTIX/src/09nr2-src")
WORKDIR = os.environ.get("WORKDIR", "/media/REMOTIX/tmp/09nr2")
INSIDE_TREE = os.environ.get("INSIDE_TREE", "/srv/src/09nr2-src")
INSIDE_WORK = os.environ.get("INSIDE_WORK", "/srv/remotix/tmp/09nr2")
UNIT = os.environ.get("UNIT", "remotix-%d" % PORT)
USER_PASSWORD = os.environ.get("USER_PASSWORD", "nr2-riordino-2026")
MACHINE = os.environ.get("MACHINE", "nicfio@192.168.0.2")
ADDR = os.environ.get("ADDR", "192.168.0.2")
OUT = os.environ.get("OUT", os.path.join(
    "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX/"
    "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad", "b77"))

# ⛔ The ports that are NOT mine.  They are counted, not touched.
FORBIDDEN = ("7900", "7910", "7920")
FORBIDDEN_IFACE = "enp7s0"

for k, v in (("PORT", str(PORT)), ("ACCOUNT", ACCOUNT), ("UID_B", str(UID_B)),
             ("TREE", TREE_DIR), ("WORKDIR", WORKDIR), ("INSIDE_TREE", INSIDE_TREE),
             ("INSIDE_WORK", INSIDE_WORK), ("OUT", OUT), ("ADDR", ADDR),
             ("MACHINE", MACHINE)):
    os.environ[k] = v


def _load(name, file_):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, file_))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


NETWORK = _load("b64rete", "07-b64-rete.py")      # root(), broken(), tono_*, guardiano_*
LOCK = _load("lucchetto", "09-lucchetto.py")
G42 = _load("g42", "07-b42-giudice.py")        # the tone judge, certified

FREQUENCY = 48000
CHANNELS = 2
STEP_PCM_US = 5000          # §5.3: the PCM block is 5 ms
HZ = 440
CHI = "09-b77"

def log(t):  print("\n\033[1m== %s\033[0m" % t)
def ok(t):   print("    \033[1;32mOK\033[0m  %s" % t)
def ko(t):   print("    \033[1;31mNO\033[0m  %s" % t)
def inf(t):  print("    --  %s" % t)


# ═══════════════════════════════════════════════════════════════════════════
# THE PREDICATES — WRITTEN FIRST, AND THEY ARE FUNCTIONS, NOT PROSE
#
# ⛔⛔ R13: nine expectations in prose, printed and never compared.  A bench like that cannot
#      give red: whatever number comes out, the sentence next to it stays true «on
#      reading».  ⇒ Here every expectation is `(v, u) -> (passes, why)` — `v` are the
#      numbers of the OLD rule, `u` those of the NEW one — and `passes=None` means
#      «I refuse to judge», which is an outcome of ITS OWN and not a green.
#
# ⛔⛔⛔ AND THE QUANTITY IS DECLARED, BECAUSE THERE ARE TWO «PURITIES» AND THEY ARE NOT THE
#       SAME THING:
#
#         · `purity`      = **`delivered / on_wire`**, and the client counts it.
#           ⭐ `on_wire` is counted BEFORE the screening: it is how many blocks the network
#           delivered; `delivered` is how many came out of the §6.3 screening.
#           ⇒ The network's loss does not even enter the denominator, and this
#           is the quantity the cure is judged on.
#         · `tone_purity` = how much energy sits in the 440 Hz line, and I count it
#           MYSELF from the rebuilt samples (`07-b42`, certified).  ⚠ It is the
#           second leg, independent of the client's arithmetic, and on a
#           profile with loss **it cannot go back to 1**.
#
# ⛔⛔ AND THE `[M]` «purity 0.175» OF `pagina.html` LINE 6474 **IS NOT A
#      REFERENCE**: its definition is not known (with the denominator the page
#      benches use — `played/received`, `09-b74:300` — that ratio
#      is ~1.000 with both rules, because the discard does `continue`
#      BEFORE `received++`).  ⇒ Comparing a number whose
#      definition is unknown with one whose definition is known would be the most polite way of
#      manufacturing a triumph.  Here the expectation is a BOUND, not that point.
# ═══════════════════════════════════════════════════════════════════════════
def _p(cond, why):
    return (bool(cond), why)


def _mute(why):
    return (None, why)


def _c(n, key):
    """⛔ `CODER.md` §3.10: «I did not read» is not «zero».  A missing number
       returns `None` and makes the predicate KEEP SILENT, it does not make it pass."""
    return n.get(key)


# ── the positive control: without it the bench has no right to green ───────
def a_collapses_with_old(cap, min_old):
    """⛔⭐ THE POSITIVE CONTROL — «DOES THE PROFILE BITE?».

    With the OLD rule, every block arriving behind a newer one is thrown
    away.  ⇒ `purezza = consegnati/sul_filo` must **collapse below a declared
    bound**, and the blocks thrown away must be many.

    ⭐ THE BOUND, AND ITS REASON.  A PCM block is **5 ms** (§5.3).  A
       `purezza` of 0.90 means one block in ten does not play: at 200
       blocks per second that is **twenty gaps per second**, that is a continuous
       chirping, not an occasional defect.  ⇒ Below 0.90 the damage is
       audible beyond discussion, and that is where the bound of the mildest
       profile goes; the nastier profiles have lower bounds, written alongside.
       ⛔ It is not a point: it is a bound.  Under `netem` the exact value is not
       predictable — a synthetic reordering in groups of k would give exactly
       `1/(k+1)`, but jitter does not make regular groups.

    ⛔ AND IF IT DOES NOT COLLAPSE, THE BENCH DOES NOT GIVE RED: IT REFUSES TO JUDGE.  A
       profile that does not bite is not a defect of the cure — it is a measurement that
       was not made.  ⚠ But it is not a green either: `passes=None` stops
       the whole profile, and that is what it must do.

    ⭐ THE REAL RED EXISTS ALL THE SAME, and it is the contradiction: many blocks
       thrown away AND a high purity.  They are the same quantity seen twice, and
       if they contradict each other one of the two counts is wrong.
    """
    def f(v, u):
        pv, ve = _c(v, "purity"), _c(v, "stale")
        sf = _c(v, "on_wire")
        if pv is None or ve is None:
            return _mute("the old rule gave no purezza/discarded_old: "
                         "I do not judge")
        if ve >= min_old and pv > cap:
            return _p(False,
                      "⛔ CONTRADICTION: the old rule says it threw away "
                      "%d blocks but the purity stays %.4f (sul_filo %s) — they are "
                      "the same quantity seen twice, and one of the two counts "
                      "is wrong" % (ve, pv, sf))
        if pv > cap or ve < min_old:
            return _mute("⛔ THE PROFILE DOES NOT BITE: with the old rule the "
                         "purity had to collapse below %.2f (seen %.4f) and the "
                         "blocks thrown away be >= %d (seen %d).  ⇒ I do NOT "
                         "JUDGE: a green here would not be a measurement, it would be "
                         "chance" % (cap, pv, min_old, ve))
        return _p(True,
                  "OLD: the profile BITES — purity %.4f <= %.2f and %d blocks "
                  "thrown away (>= %d) out of %s arrived on the wire"
                  % (pv, cap, ve, min_old, sf))
    return f


def a_rises_with_new(min_purity=0.95):
    """The cure must restore the delivered fraction, and without moving
       the damage onto `discarded_late`.

    ⚠ And `discarded_late` is NOT `discarded_old`: a block arriving too
      late **on the wire** ends up in `discarded_old`; `discarded_late` is the
      safety net AFTER the decoder.  They are two different cases, and
      confusing them would make this predicate blind to the second.
    """
    def f(v, u):
        pu, ta = _c(u, "purity"), _c(u, "late_audio")
        sf = _c(u, "on_wire")
        if pu is None:
            return _mute("the new rule gave no purity: I do not judge")
        if ta is None:
            return _mute("the new rule gave no discarded_late: I do not judge")
        cap = max(20, int(0.01 * (sf or 0)))
        return _p(pu >= min_purity and ta <= cap,
                  "NEW: purity >= %.2f (seen %.4f) and scartati_tardivi <= %d "
                  "(seen %d) — the safety net after the decoder did not "
                  "take the damage" % (min_purity, pu, cap, ta))
    return f


def a_tone_confirms(gain=0.05):
    """⭐ THE SECOND LEG, FROM THE SAMPLES AND NOT FROM THE CLIENT'S ARITHMETIC.

    `purity` is computed by the client, which is also the object of the measurement: that is
    where the cure lives.  ⇒ A number taken ELSEWHERE is needed.  Here the blocks are
    put back in their place in time (`base + istante`, as the page's anchor
    does) and two things are measured on the SAMPLES:
      · `copertura`    = how much of the timeline really has sound;
      · `purezza_tono` = how much energy sits in the 440 Hz line (`07-b42`).
    ⛔ If the client says «I delivered everything» and the samples say that half
       the timeline is silence, one of the two is lying.
    """
    def f(v, u):
        cv, cu = _c(v, "coverage"), _c(u, "coverage")
        tv, tu = _c(v, "tone_purity"), _c(u, "tone_purity")
        if cv is None or cu is None:
            return _mute("the coverage was not measured: I do not judge")
        if tv is None or tu is None:
            return _p(cu - cv >= gain,
                      "⚠ without tone_purity: the coverage rises by >= %.2f "
                      "(%.4f → %.4f)" % (gain, cv, cu))
        return _p(cu - cv >= gain and tu > tv,
                  "THE TONE CONFIRMS: coverage %.4f → %.4f (+%.4f, required "
                  "%.2f) and purezza_tono %.3f → %.3f"
                  % (cv, cu, cu - cv, gain, tv, tu))
    return f


def a_out_positive(v, u):
    """⭐⛔ THE PREDICATE THAT KEEPS THE CURE HONEST.

       `out_of_order` must be GREATER THAN ZERO in the profiles that reorder.
       If it were zero and the purity high, the cure is not «recovering the
       reordered ones»: it is simply **not seeing the reordering**, and the good
       number would be chance — the same face as a network that does not break."""
    fu = _c(u, "out")
    if fu is None:
        return _mute("the client did not say `out_of_order`: I do not judge")
    return _p(fu > 0,
              "NEW: fuori_ordine > 0 (seen %d) — the cure is looking at "
              "REAL reorderings, not a quiet network" % fu)


def a_zero_duplicates(v, u):
    """⛔ Zero with both rules.  If they rise, someone counts twice —
       and a block delivered twice would double the signal, which §6.3 does not
       allow and is the worst way of failing."""
    dv, du = _c(v, "dup"), _c(u, "dup")
    if du is None:
        return _mute("the client did not say `duplicates`: I do not judge")
    return _p(du == 0 and (dv in (0, None)),
              "duplicates 0 with both (old %s, new %s)"
              % ("-" if dv is None else dv, du))


def a_both_coincide(tolerance=0.01, min_purity=0.98):
    """⛔ The denominator.  On a line that does NOT reorder the two rules must
       give the same result: if they already differ here, the cure has a defect
       on the easy case and none of its other greens counts."""
    def f(v, u):
        pv, pu = _c(v, "purity"), _c(u, "purity")
        if pv is None or pu is None:
            return _mute("one of the two purities is missing: I do not judge")
        return _p(abs(pv - pu) <= tolerance and pv >= min_purity and pu >= min_purity,
                  "SMOOTH: |%.4f - %.4f| <= %.2f and both >= %.2f"
                  % (pv, pu, tolerance, min_purity))
    return f


def a_no_reorder_on_smooth(v, u):
    """⛔ On `lo` without a qdisc packets do not overtake each other.  If here
       `out_of_order` rises, something else is reordering — and then not even the
       numbers of the broken profiles can be attributed to `netem`."""
    fu, ve = _c(u, "out"), _c(v, "stale")
    if fu is None:
        return _mute("the client did not say `out_of_order`: I do not judge")
    return _p(fu == 0 and (ve or 0) == 0,
              "SMOOTH: fuori_ordine 0 (seen %d) and scartati_vecchi 0 (seen %s)"
              % (fu, ve))



def a_declared_loss(fraction, tolerance=0.6):
    """⚠ WHERE THERE IS ALSO LOSS, THE LOST PART IS DECLARED — AND FROM BOTH ENDS.

    `purity` does not see it, and must not: `on_wire` counts what the network
    DELIVERED, so what is lost does not even enter the denominator.  ⇒ If it were not
    declared separately, a profile with 2 % loss would pass for
    «clean» only because the right number is being looked at.

    ⛔⛔ AND THE CLIENT'S `mancati` IS NOT USED — `[M]` 23 August 2026, and it is a
         red the bench gave itself.  On `bad-home` the client
         said **2183 missed out of 4996, 43.7 %**, with `netem` set to
         2 %: it looked as if `netem` removed twenty times what it had
         been asked.

    ⭐ It was not `netem`.  The SERVER's count said
       «2879 sent, 0 dropped, **2134 refused**»: with 40 ms of delay and
       2 % loss ngtcp2's congestion window closes, and the
       server **does not put** those datagrams **on the wire**.  `mancati` counts them all
       the same, because it is built on the jumps of `istante` and a block never
       sent leaves the same jump as a lost one.
       ⇒ «the network lost it» and «the server never sent it» gave the
         same number — which is exactly R13, and in a bench that breaks the
         NETWORK on purpose it is the distinction that matters more than any other.

    ⇒ The true loss is measured between the TWO ENDS:
           lost on the wire = (sent by the server) − (client's on_wire)
       ⚠ And `rifiutati` is reported separately: it is not a `netem` defect, it is
         the price the transport pays on that network — and it must be said.
    """
    def f(v, u):
        sp, sf = _c(u, "shipped_server"), _c(u, "on_wire")
        if sp is None or not sf:
            return _mute("the server's «spediti» or the client's «sul filo» were not "
                         "read: the loss cannot be attributed")
        lost = sp - sf
        if lost < 0:
            return _p(False,
                      "⛔ the client says it saw MORE blocks on the wire than "
                      "the server sent (%d > %d): one of the two "
                      "counts is wrong" % (sf, sp))
        vista = lost / float(sp)
        return _p(abs(vista - fraction) <= tolerance * fraction + 0.005,
                  "THE LOSS IS DECLARED, FROM BOTH ENDS: the server sent "
                  "%d, the client saw %d on the wire ⇒ **%d lost on the "
                  "network, %.2f%%** (netem removes %.0f%%).  ⚠ And separately: "
                  "%s REFUSED by ngtcp2, that is never put on the wire — those "
                  "do not belong to netem, and the client's `missed` (%s) counts them "
                  "together with the lost ones"
                  % (sp, sf, lost, vista * 100, fraction * 100,
                     _c(u, "server_refused"), _c(u, "missed")))
    return f


def a_tone_does_not_return_to_one(cap=0.98):
    """⚠ AND HERE THE TONE PURITY **MUST NOT** GO BACK TO 1, and it is an expectation
       like the others: with 2 % loss gaps remain that no rule of the
       receiver can fill.  ⛔ If it went back to 1 it would be the judge that is
       blind, not the network that is healed."""
    def f(v, u):
        tu = _c(u, "tone_purity")
        if tu is None:
            return _mute("purezza_tono was not measured: I do not judge")
        return _p(tu <= cap,
                  "the tone does NOT go back to 1 (%.3f <= %.2f), and must not: the loss "
                  "leaves gaps the receiver cannot fill" % (tu, cap))
    return f


def a_reorder_from_both_ends(v, u):
    """⭐⭐⭐ THE SECOND LEG OF THE POSITIVE CONTROL, FROM THE OTHER END OF THE WIRE.

    ⛔ THE DEFECT IT CURES.  The purity and the count of overtakes both come
       from the RECEIVER's side — which is also the object of the measurement, because
       the cure lives there.  ⇒ «the cure recovers the reordered ones» and «the profile does not
       reorder, and there is nothing to recover» look **the same** from
       that side alone.

    ⭐ Since 23 August 2026 the SERVER can state the fact on its own, and it knows
       nothing of the cure.  `[S]` `ngtcp2.h:3442` on the `lost_datagram` callback:
       *«the loss might be spurious, and DATAGRAM frame might be acknowledged
       later»*.  ⇒ The same `dgram_id` first **lost** and then **acknowledged**
       is a datagram **arrived out of sequence**: it is `dgram_spurious`, on the
       `quic-net` line of the log.

    ⚠ AND THE PRICE IS DECLARED, or this predicate would give false reds.
      `dgram_spurious` can be zero while reordering really exists: ngtcp2
      declares a packet lost only after **three** newer packets
      acknowledged, and a swap between neighbours — which is what a 2 ms jitter
      does on 5 ms blocks — does not reach three.  ⇒ The server's witness is
      **sufficient, not necessary**.

    ⇒ The rule: it is enough that ONE of the three ends sees the reordering for the profile
      to exist; if NOBODY sees it, the bench **refuses to judge** — a
      green there would be chance, not a measurement.
    """
    srv = _c(u, "dgram_spurious")
    srv_v = _c(v, "dgram_spurious")
    cli = _c(u, "out")            # the cure's counter
    my = _c(u, "arrival_out_of_order")     # the overtakes I counted on the JSONL
    vec = _c(v, "stale")           # what the OLD rule threw away
    tot_srv = None
    if srv is not None or srv_v is not None:
        tot_srv = (srv or 0) + (srv_v or 0)
    seen_items = [x for x in (cli, my, vec) if x]
    if tot_srv is None and not seen_items and cli is None and my is None:
        return _mute("no reordering witness was read: I do not judge")
    if tot_srv:
        return _p(True,
                  "THE SERVER confirms it: %d datagrams given up as lost and then "
                  "ACKNOWLEDGED (= out of sequence), and the server knows nothing "
                  "of the cure · receiver: fuori %s, overtakes on the JSONL %s, "
                  "vecchi %s" % (tot_srv, cli, my, vec))
    if seen_items:
        return _p(True,
                  "⚠ the server's witness is silent (dgram_spurious 0: ngtcp2 "
                  "declares lost only after 3 newer packets, and a "
                  "swap between neighbours does not get there), ⭐ but the reordering shows "
                  "in the DATA: fuori %s, overtakes on the JSONL %s, vecchi %s"
                  % (cli, my, vec))
    return _mute("NONE of the three ends sees reordering (server 0, fuori %s, "
                 "overtakes on the JSONL %s, vecchi %s): the profile DOES NOT BITE, and "
                 "a green here would be chance" % (cli, my, vec))


def a_ends_do_not_contradict(v, u):
    """⛔ And if the two ends contradict each other, it is a fact worth more than
       both: the server saw packets go from lost to
       acknowledged, and the receiver did not see even one out of sequence.
       One of the two is wrong, and until we know which no number counts."""
    srv = _c(u, "dgram_spurious")
    cli, my = _c(u, "out"), _c(u, "arrival_out_of_order")
    if srv is None or (cli is None and my is None):
        return _mute("a witness is missing: I do not compare the two ends")
    if srv > 0 and (cli or 0) == 0 and (my or 0) == 0:
        return _p(False,
                  "⛔ THE TWO ENDS CONTRADICT EACH OTHER: the server saw %d "
                  "datagrams go from lost to acknowledged, the receiver "
                  "ZERO out of sequence (fuori %s, overtakes on the JSONL %s)"
                  % (srv, cli, my))
    return _p(True, "the two ends agree (server %s · receiver fuori %s, "
                    "overtakes on the JSONL %s)" % (srv, cli, my))


def a_netem_has_seen(v, u):
    """⛔ If the `u32` filter does not bite, the traffic does not go through `netem`: I would have
       measured a HEALTHY network believing it broken, and written that the cure is needed
       where there was nothing to cure.  ⚠ It is not a red: it is an «I did not
       measure», which is an outcome of its own."""
    pv, pu = _c(v, "netem_pkt"), _c(u, "netem_pkt")
    if pv is None or pu is None:
        return _mute("the netem packet count was not read")
    if (pv + pu) <= 0:
        return _mute("the netem saw NO packet: the u32 filter "
                     "on port %d does not bite, and this profile does not exist" % PORT)
    return _p(True, "the netem saw %d + %d packets (the filter bites)" % (pv, pu))


def a_server_has_sent(v, u):
    """⛔ The client knows how many datagrams it received; it does not know how many
       left.  Without this, a SERVER defect would be attributed to
       `netem` (R13)."""
    sv, su = _c(v, "shipped_server"), _c(u, "shipped_server")
    if sv is None or su is None:
        return _mute("the server's «final count» was not read")
    return _p(sv > 0 and su > 0,
              "the server sent %s and %s blocks in the two runs" % (sv, su))


# ═══════════════════════════════════════════════════════════════════════════
# THE PROFILES — THOSE THAT REORDER, NOT THOSE THAT SQUEEZE
#
# ⛔ The target of phase 9 is not bandwidth («30 Mbit/s is a mid-90s
#    connection»): it is the network that loses, reorders and jitters.  ⇒ Here there
#    is not even a `rate`.
# ⛔ `netem reorder` WITHOUT `delay` does nothing — the `delay 10ms` line is not
#    decorative: without it, the reordering percentage is ignored by the kernel.
# ═══════════════════════════════════════════════════════════════════════════
PROFILES = [
    ("smooth", [],
     "the denominator: no fault, and the two rules must coincide",
     [a_both_coincide(), a_no_reorder_on_smooth, a_zero_duplicates,
      a_server_has_sent, a_ends_do_not_contradict]),

    ("jitter-2", ["delay", "20ms", "2ms", "distribution", "normal"],
     "jitter ±2 ms, less than one PCM block (5 ms): it is the MILDEST profile that "
     "reorders, and the bound of its positive control is 0.90 — one block in "
     "ten thrown away is twenty gaps per second",
     [a_netem_has_seen, a_server_has_sent, a_reorder_from_both_ends,
      a_ends_do_not_contradict, a_collapses_with_old(0.90, 100),
      a_rises_with_new(0.95), a_tone_confirms(), a_out_positive,
      a_zero_duplicates]),

    ("jitter-5", ["delay", "20ms", "5ms", "distribution", "normal"],
     "jitter ±5 ms = one whole block: overtakes grow, and the bound drops "
     "to 0.80",
     [a_netem_has_seen, a_server_has_sent, a_reorder_from_both_ends,
      a_ends_do_not_contradict, a_collapses_with_old(0.80, 300),
      a_rises_with_new(0.95), a_tone_confirms(), a_out_positive,
      a_zero_duplicates]),

    ("jitter-15", ["delay", "30ms", "15ms", "distribution", "normal"],
     "jitter ±15 ms = three blocks: with the old rule listening is broken, and "
     "the bound drops to 0.60",
     [a_netem_has_seen, a_server_has_sent, a_reorder_from_both_ends,
      a_ends_do_not_contradict, a_collapses_with_old(0.60, 800),
      a_rises_with_new(0.95), a_tone_confirms(), a_out_positive,
      a_zero_duplicates]),

    ("reorder-25", ["delay", "10ms", "reorder", "25%", "50%"],
     "⭐ EXPLICIT REORDERING, which is NOT jitter: one packet in four "
     "jumps the queue and leaves at once.  ⛔ The `delay 10ms` is mandatory, or "
     "`reorder` does nothing",
     [a_netem_has_seen, a_server_has_sent, a_reorder_from_both_ends,
      a_ends_do_not_contradict, a_collapses_with_old(0.90, 300),
      a_rises_with_new(0.95), a_tone_confirms(), a_out_positive,
      a_zero_duplicates]),

    ("bad-home", ["delay", "40ms", "20ms", "distribution", "normal",
                      "loss", "2%"],
     "⚠ HERE THERE IS ALSO LOSS.  `purity` does not see it — `on_wire` counts what "
     "the network DELIVERED — so the lost part is declared separately "
     "(`missed`), and the TONE purity must not go back to 1",
     [a_netem_has_seen, a_server_has_sent, a_reorder_from_both_ends,
      a_ends_do_not_contradict, a_collapses_with_old(0.80, 500),
      a_rises_with_new(0.95), a_declared_loss(0.02),
      a_tone_does_not_return_to_one(), a_out_positive, a_zero_duplicates]),
]

RULES = ("old", "new")


# ═══════════════════════════════════════════════════════════════════════════
# THE JUDGE — THE BLOCKS IN THEIR PLACE, AS THE PAGE'S ANCHOR DOES
# ═══════════════════════════════════════════════════════════════════════════
def tone_purity(samples):
    """⭐⭐ THE PURITY OF `07-b42`, BUT IN A TIME ONE CAN AFFORD.

    `07-b42.giudica()` does **1901 Goertzels** (100…2000 Hz) on 48 000 samples:
    91 million loop iterations in pure Python, that is ~one minute **per
    window**.  ⚠ With eight windows per run and twelve runs it would be four
    hours, and the `netem` lock lasts fifteen minutes.

    ⭐ AND NO APPROXIMATION IS NEEDED, BECAUSE THEY ARE THE SAME THING.  A Goertzel
       at WHOLE frequency `f` on **exactly 48 000 samples** is term
       `f` of the 48 000-point DFT: the bin spacing is 48000/48000 = **1 Hz**,
       so bin `f` falls exactly on `f` Hz.  ⇒ An `rfft` gives the
       same 1901 squared magnitudes in milliseconds.
    ⛔ And this equality is not taken on trust: `--certify`
       COMPARES it with `07-b42.giudica()` on a real case and demands that
       they coincide to four decimals.  If numpy is missing or they do not coincide, we
       fall back on `07-b42` and DECLARE it (one window only).
    """
    m = len(samples)
    if m != FREQUENCY:
        return G42.judge([x / 32768.0 for x in samples])
    try:
        import numpy as _np
    except ImportError:
        return G42.judge([x / 32768.0 for x in samples])
    x = _np.asarray(samples, dtype=_np.float64) / 32768.0
    X = _np.fft.rfft(x)
    p = _np.abs(X[100:2001]) ** 2
    total_sum = float(p.sum())
    if total_sum <= 0:
        return {"outcome": "GIUDICATO", "samples": m, "hz": 0, "purity": None,
                "rms": 0.0}
    k = int(p.argmax())
    return {"outcome": "GIUDICATO", "samples": m, "hz": 100 + k,
            "rms": round(float(_np.sqrt((x * x).mean())), 4),
            "purity": round(float(p[k] / total_sum), 4)}


def ladder(fpath, windows=8, window_s=1):
    """⭐ The canvas of silence and the blocks placed at `base + istante`.

    ⛔ They are NOT pasted in arrival order: that would be the wrong judgement for
       the new rule, which KEEPS the late blocks — pasting them wherever they
       happen to fall would put the past in the middle of the present and accuse the cure
       of a defect that belongs to the judge.

    ⚠ The gaps stay SILENCE, and they must: a gap is what one hears, and
      stitching the edges would make it invisible to the tone judge.
    """
    if not os.path.exists(fpath) or os.path.getsize(fpath) == 0:
        return {"outcome": "NOTHING TO JUDGE — the JSONL is missing or empty"}
    blocks, seen_items, dup = [], set(), 0
    arrival_out_of_order, maximum = 0, None
    for r in open(fpath):
        r = r.strip()
        if not r:
            continue
        d = json.loads(r)
        if d.get("codec") != 2:
            continue                     # ⛔ PCM only: Opus is not judged this way
        ist = int(d["instant"])
        if ist in seen_items:
            dup += 1
            continue
        seen_items.add(ist)
        # ⭐ The overtakes counted on the DATA, not on the client's counter: it is the
        #    second leg of the proof that the profile really reorders.
        if maximum is not None and ist < maximum:
            arrival_out_of_order += 1
        maximum = ist if maximum is None else max(maximum, ist)
        blocks.append((ist, base64.b64decode(d["byte"])))
    if len(blocks) < 200:
        return {"outcome": "NOTHING TO JUDGE — %d blocks" % len(blocks),
                "blocks": len(blocks)}
    base = min(i for i, _ in blocks)
    fine = max(i for i, _ in blocks)
    n_tot = int(round((fine - base) / 1e6 * FREQUENCY)) + (FREQUENCY * STEP_PCM_US // 1000000)
    if n_tot <= 0 or n_tot > FREQUENCY * 3600:
        return {"outcome": "NOTHING TO JUDGE — absurd timeline (%d)" % n_tot}
    canvas = [0] * n_tot
    full = bytearray(n_tot)
    for ist, b in blocks:
        off = int(round((ist - base) / 1e6 * FREQUENCY))
        n = len(b) // (2 * CHANNELS)
        if n <= 0 or off < 0 or off + n > n_tot:
            continue
        v = struct.unpack("<%dh" % (n * CHANNELS), b[:n * CHANNELS * 2])
        sx = v[0::CHANNELS]
        for k in range(n):
            canvas[off + k] = sx[k]
            full[off + k] = 1
    covered = sum(full)
    coverage = covered / float(n_tot)
    # ⭐ The purity over SEVERAL windows, and the median is taken: a single window
    #   catches chance.  ⚠ The windows are equally spaced, not chosen.
    n = window_s * FREQUENCY
    purities, seen_hz = [], []
    if n_tot >= n:
        slots = ([0] if windows <= 1 else
                 [int(k * (n_tot - n) / (windows - 1)) for k in range(windows)])
        for i in slots:
            g = tone_purity(canvas[i:i + n])
            if g.get("purity") is not None:
                purities.append(g["purity"])
                seen_hz.append(g.get("hz"))
    sorted_purities = sorted(purities)
    med = (sorted_purities[len(sorted_purities) // 2] if sorted_purities else None)
    return {"outcome": "GIUDICATO", "blocks": len(blocks),
            "doppioni_scaletta": dup, "arrival_out_of_order": arrival_out_of_order,
            "duration_s": round(n_tot / float(FREQUENCY), 3),
            "campioni_scritti": covered, "campioni_totali": n_tot,
            "coverage": round(coverage, 5),
            "tone_purity": None if med is None else round(med, 4),
            "purezza_tono_min": None if not sorted_purities else round(sorted_purities[0], 4),
            "purezza_tono_max": None if not sorted_purities else round(sorted_purities[-1], 4),
            "windows": len(sorted_purities),
            "hz": seen_hz[len(seen_hz) // 2] if seen_hz else None}


# ⛔⛔ THERE WAS A THIRD JUDGEMENT HERE, AND IT WAS REMOVED — 23 August 2026.
#
#      `07-b64-orecchio.py` pastes the blocks in ARRIVAL order and measures their
#      tone purity.  It served to stay comparable with the `[M]` of
#      `pagina.html` line 6474 (purity 0.175).  ⇒ Two reasons to remove it, and
#      the first alone is enough:
#
#        1. ⛔ that `[M]` is not a valid reference: its definition is not
#           known (see the predicates box), and comparing oneself with a number
#           whose definition is unknown manufactures triumphs;
#        2. ⚠ it costs **one minute per run** (1901 Goertzels in pure Python on
#           48 000 samples), that is twelve minutes INSIDE the `netem`
#           lock — which lasts fifteen and has two other agents queued.
#
# ⭐ And pasting in arrival order would on top of that be the WRONG judgement for
#    the new rule, which KEEPS the late blocks: it would put the past in
#    the middle of the present and accusations the cure of a defect of the judge.


# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT TALKS TO THE TEST MACHINE
# ═══════════════════════════════════════════════════════════════════════════
def root(command, cap=300):
    return NETWORK.root(command, cap)


def netem_packets():
    """The packets the `netem` node REALLY saw pass.

    ⛔ It is the substitute for the `reordered` counter, which on this machine does not
       exist (`[M]`: iproute2 6.15.0, `grep -ac reordered /usr/sbin/tc` = 0).
       ⚠ It does not say «how many it reordered»; it says «the u32 filter bites», which is
       the condition without which the profile does not exist at all.
    """
    rc, out, _ = root("/usr/sbin/tc -s qdisc show dev lo")
    inside, last = False, None
    for line in out.split("\n"):
        s = line.strip()
        if s.startswith("qdisc"):
            inside = ("netem" in s)
            continue
        if inside:
            m = re.search(r"Sent\s+(\d+)\s+bytes\s+(\d+)\s+pkt", s)
            if m:
                last = int(m.group(2))
                inside = False
    return last


def log_line_list():
    rc, out, _ = root("wc -l < %s/registro.log 2>/dev/null || echo 0" % WORKDIR)
    try:
        return int(out.strip())
    except Exception:
        return 0


def server_counts(line0):
    """⛔ «the network lost it» and «the server never sent it» give the same
       number on the client's side.  Here the SERVER's count is read, and only
       from `line0` on, so it belongs to THIS run."""
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -a 'audio of .*final "
                      "count' | tail -1" % (line0 + 1, WORKDIR))
    r = out.strip()
    if not r:
        return {"outcome": "NOTHING TO READ — no «final count» in this run"}
    m = re.search(r"(\d+) blocks sent, (\d+) dropped.*?(\d+) refused.*?"
                  r"(\d+) DEFERRED", r)
    if not m:
        return {"outcome": "line found but unreadable", "line": r[:160]}
    return {"sent": int(m.group(1)), "dropped": int(m.group(2)),
            "refused": int(m.group(3)), "rimandati": int(m.group(4))}


def server_witness(line0):
    """⭐⭐ THE REORDERING WITNESS THAT KNOWS NOTHING OF THE CURE.

    The `quic-net` line of the log carries, since 23 August 2026:
        dgram_lost= dgram_lost_d= dgram_ok= dgram_spurious= dgram_spurious_d=
    ⛔ It is read only from `riga0` on, so it belongs to THIS run; and the counters
       are cumulative PER CONNECTION, so the maximum of the
       window is taken — not the sum, which would count every line from scratch.
    ⚠ If the binary is older than the witness, the fields are not there: we
      return `None`, not zero (`CODER.md` §3.10)."""
    rc, out, _ = root("tail -n +%d %s/registro.log 2>/dev/null | grep -a "
                      "'quic-net ' | tail -40" % (line0 + 1, WORKDIR))
    lines = [r for r in out.split("\n") if "quic-net " in r]
    if not lines:
        return {"outcome": "NOTHING TO READ — no «quic-net» line in "
                         "this run", "lines": 0}
    report = {"lines": len(lines)}
    for field in ("dgram_lost", "dgram_ok", "dgram_spurious"):
        values = []
        for r in lines:
            m = re.search(r"\b%s=(\d+)" % field, r)
            if m:
                values.append(int(m.group(1)))
        report[field] = max(values) if values else None
    for field in ("dgram_lost_d", "dgram_spurious_d"):
        values = []
        for r in lines:
            m = re.search(r"\b%s=(\d+)" % field, r)
            if m:
                values.append(int(m.group(1)))
        # ⚠ The `_d` are differences between one line and the next: here they are SUMMED.
        report[field] = sum(values) if values else None
    if report.get("dgram_spurious") is None:
        report["outcome"] = ("the binary does NOT have the datagram witness "
                          "(no `dgram_spurious=` on the quic-net line)")
    return report


# ⛔⛔ THE NAMES ARE COPIED FROM HOW THE CLIENT PRINTS THEM, NOT FROM HOW THEY ARE CALLED
#      INSIDE.  `01-b3-cliente.py:606` prints:
#
#        [audio] discarded — short 0 · type 0 · prefix 0 · old 1900
#        [audio] reorder — rule new_one · on wire 5001 · received 5001 ·
#                          delivered 4991 · PURITY 0.9980 (page 0.9980)
#        [audio] reorder — late 6 · out 812 · rec 790 · dup 0 ·
#                          missed 1 times 1 · rearms 0 · step 5000us
#
#      ⚠ «on wire» has a SPACE, `PURITY` is upper case, and the four of
#        phase 9 are called `late/out/rec/dup`, not with the page's long
#        names.  (The client's text was translated on 10 Oct 2026: these
#        regexes follow it.)  ⛔ A regex built on the internal names would not have given an
#        error: it would have given `None` on everything, that is a bench that KEEPS SILENT on every
#        predicate and gives neither green nor red.

TO_READ = {
    "on_wire":       r"\bon wire\s+(\d+)",
    "received":       r"·\s*received\s+(\d+)\s*·",
    "delivered":     r"\bdelivered\s+(\d+)",
    "stale":         r"\bold\s+(\d+)",
    "short":          r"\bshort\s+(\d+)",
    "type":           r"\btype\s+(\d+)",
    "prefix":       r"\bprefix\s+(\d+)",
    "late_audio":        r"\blate\s+(\d+)",
    "out":          r"\bout\s+(\d+)",
    "rec":            r"\brec\s+(\d+)",
    "dup":            r"\bdup\s+(\d+)",
    "missed":        r"\bmissed\s+(\d+)",
    "missed_times":  r"\bmissed\s+\d+\s+times\s+(\d+)",
    "rearms":         r"\brearms\s+(\d+)",
    "step_us":       r"\bstep\s+(\d+)us",
}
TO_READ_DEC = {
    "purity":        r"PURITY\s+([0-9]+\.[0-9]+)",
    "page_purity": r"\(page\s+([0-9]+\.[0-9]+)\)",
}


def _num(text, name):
    """⛔ The LAST occurrence is taken — the counts line comes after all
       the others — and a `None` means «I did not read it», not «zero»."""
    found = None
    for m in re.finditer(TO_READ.get(name, r"\b%s\b\s+(\d+)" % re.escape(name)),
                         text):
        found = int(m.group(1))
    return found


def _dec(text, name):
    found = None
    for m in re.finditer(TO_READ_DEC.get(name, r"\b%s\b\s+([0-9.]+)" % re.escape(name)),
                         text):
        found = float(m.group(1))
    return found


def _declared_rule(text):
    """⭐⭐ THE PROOF THAT THE RULE WAS IN FORCE IN THIS RUN.

    ⛔ `LEZIONI.md` E1: «written is not in force».  That `--audio-rule` exists
       in the help does not say the client USED it — an argument accepted
       and ignored would give two identical runs, and the bench would report «no
       difference», which looks the same as «the cure is not needed» and is the
       opposite conclusion.  ⇒ The client prints `rule <nome>` on the counts
       line, and HERE we check it is the one I asked for."""
    found_at = None
    for m in re.finditer(r"\brule\s+(old|new)\b", text):
        found_at = m.group(1)
    return found_at


def client_has_switch():
    """⛔ THE CHECK THAT AVOIDS THIS BENCH'S MOST LIKELY FALSE GREEN.

       If `--audio-rule` is not there yet, the two runs would use the same
       rule: the bench would see two equal numbers and report «no
       difference».  ⚠ It looks the same as «the cure is not needed» — and is the
       opposite conclusion.  ⇒ It is checked, and if it is not there we STOP.

       ⭐ And the copy THAT RUNS (inside the container) is checked, not the
          laptop's: «I wrote it» is not «it is in force» (`LEZIONI.md` E1).
    """
    outcome = {}
    local = os.path.join(HERE, "01-b3-cliente.py")
    try:
        t = open(local, encoding="utf-8", errors="replace").read()
        outcome["portable"] = "--audio-rule" in t
    except Exception as e:
        outcome["portable"] = False
        outcome["portatile_perche"] = str(e)
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root "
                        "'python3 %s/banchi/01-b3-cliente.py --help 2>&1 | "
                        "grep -c -- --audio-rule'" % INSIDE_TREE, 180)
    count = 0
    for r in (out + err).split("\n"):
        if r.strip().isdigit():
            count = int(r.strip())
    outcome["dentro_aiuto"] = count > 0
    outcome["inside"] = count > 0
    return outcome


def terrain_check():
    """⛔ The bench refuses to measure on a ground that is not its own."""
    log("THE GROUND — port %d · user %s (uid %d) · tree %s" % (PORT, ACCOUNT, UID_B, TREE_DIR))
    troubles = []
    rc, out, _ = root("id %s >/dev/null 2>&1 && echo si || echo no" % ACCOUNT)
    if "yes" not in out:
        troubles.append("the user «%s» does not exist — PORT=%d ACCOUNT=%s UID_B=%d "
                    "USER_PASSWORD=%s TREE=%s WORKDIR=%s bash banchi/07-b64-terreno.sh user"
                    % (ACCOUNT, PORT, ACCOUNT, UID_B, USER_PASSWORD, TREE_DIR, WORKDIR))
    rc, out, _ = root("test -s %s/parola && echo si || echo no" % WORKDIR)
    if "yes" not in out:
        troubles.append("%s/parola (0600) is missing: D12 forbids the password in argv" % WORKDIR)
    rc, out, _ = root("test -x %s/src/remotix && echo si || echo no" % TREE_DIR)
    if "yes" not in out:
        troubles.append("the tree «%s» has no binary: `... bash banchi/07-b64-terreno.sh ship`" % TREE_DIR)
    rc, out, _ = root("ss -uln 2>/dev/null | grep -c ':%d ' || true" % PORT)
    my = out.strip()
    if my == "0":
        troubles.append("nobody is listening on %d: `... bash banchi/07-b64-terreno.sh start`" % PORT)
    # ⛔ The other agents' ports are COUNTED, not touched.
    tally = []
    for p in FORBIDDEN:
        rc, o, _ = root("ss -uln 2>/dev/null | grep -c ':%s ' || true" % p)
        tally.append("%s:%s" % (p, o.strip()))
    inf("FORBIDDEN ports (counted, not touched): %s" % " ".join(tally))
    inf("my server on %d: %s listener(s)" % (PORT, my))
    rc, out, _ = root("/usr/sbin/tc qdisc show dev %s" % FORBIDDEN_IFACE)
    inf("%s (ssh + the user's 7730) — NOT touched: %s"
        % (FORBIDDEN_IFACE, out.strip().split("\n")[0]))
    rc, out, _ = root("uptime")
    inf("load: %s" % out.strip()[-42:])

    sw = client_has_switch()
    if sw.get("inside"):
        ok("the client has `--audio-rule` (in the container, read from `--help`)")
    else:
        troubles.append("⛔⛔ THE CLIENT DOES NOT HAVE `--audio-rule` (laptop: %s, "
                    "container: %s).  I do NOT measure: two runs with the same "
                    "rule would give «no difference», which looks the same "
                    "as «the cure is not needed» and is the opposite conclusion"
                    % (sw.get("portable"), sw.get("inside")))
    for g in troubles:
        ko(g)
    if not troubles:
        ok("the ground is there, and it is mine")
    return not troubles


def cur_round(profile, rule, seconds):
    """One client run, with the chosen rule.  Returns the numbers, or `None`."""
    name = "%s-%s" % (profile, rule)
    j_out = os.path.join(OUT, name + ".jsonl")
    t_out = os.path.join(OUT, name + ".txt")
    for f in (j_out, t_out):
        try: os.remove(f)
        except Exception: pass
    line0 = log_line_list()
    pkt0 = netem_packets()
    t0 = time.time()
    inside = ("python3 -u %s/banchi/01-b3-cliente.py --address %s --port %d "
              "--user %s --password-file %s/parola --audio-codec pcm "
              "--audio-rule %s --audio-out %s/b77-%s.jsonl --stay %d"
              % (INSIDE_TREE, ADDR, PORT, ACCOUNT, INSIDE_WORK, rule,
                 INSIDE_WORK, name, seconds))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % inside,
                        seconds + 240)
    output = out + err
    open(t_out, "w").write(output)
    subprocess.run("ssh -o BatchMode=yes %s \"printf '%%s\\n' '%s' | sudo -S -p '' "
                   "cat %s/b77-%s.jsonl\" > %s"
                   % (NETWORK.MACHINE, NETWORK.SUDO_PASSWORD, WORKDIR, name, j_out),
                   shell=True)
    pkt1 = netem_packets()
    sv = server_counts(line0)
    wit = server_witness(line0)

    # ⛔ If the client refused `--audio-rule`, its numbers would be
    #    those of the OTHER rule: it is declared and not judged.
    if "unrecognized arguments" in output or "invalid choice" in output:
        return {"outcome": "THE CLIENT REFUSED --audio-rule %s" % rule,
                "queue": output[-600:]}
    # ⛔⛔ AND THE RULE MUST BE THE ONE I ASKED FOR, AS STATED BY THE CLIENT.
    #     «I passed it» is not «it used it» (`LEZIONI.md` E1): an argument
    #     accepted and ignored would give two identical runs under two names.
    said_line = _declared_rule(output)
    if said_line != rule:
        return {"outcome": "⛔⛔ I ASKED FOR «%s» AND THE CLIENT SAYS «%s»: the two "
                         "runs would not be paired, they would be the same run "
                         "twice" % (rule, said_line), "queue": output[-600:]}

    sc = ladder(j_out)
    n = {
        "profile": profile, "rule": rule, "seconds": round(time.time() - t0, 1),
        # ⭐ THE PAGE'S NAMES, which are the interface agreed with the client.
        #   ⛔ `on_wire` is counted BEFORE the screening and `delivered` AFTER: it is the
        #      pair that makes `purity` a fraction with a denominator that
        #      does not move with the rule.
        "on_wire": _num(output, "on_wire"),
        "delivered": _num(output, "delivered"),
        "received": _num(output, "received"),
        "stale": _num(output, "stale"),
        "short": _num(output, "short"),
        "type": _num(output, "type"),
        "prefix": _num(output, "prefix"),
        "late_audio": _num(output, "late_audio"),
        "out": _num(output, "out"),
        "dup": _num(output, "dup"),
        "rec": _num(output, "rec"),
        "missed": _num(output, "missed"),
        # ⛔ `purity` = delivered/on_wire, and the client counts it.
        #   ⚠ `page_purity` (played/received) is BLIND — the discard does
        #     `continue` before `received++`, so it is ~1 with both
        #     rules: it is reported only for comparison, and declared as such.
        "purity": _dec(output, "purity"),
        "page_purity": _dec(output, "page_purity"),
        "rearms": _num(output, "rearms"),
        "regola_dichiarata": _declared_rule(output),
        "shipped_server": sv.get("sent"),
        # ⛔ `refused` = ngtcp2 did not put them on the wire (window closed).
        #    ⚠ They are not network loss, and confusing them with it is R13.
        "server_refused": sv.get("refused"),
        "buttati_server": sv.get("dropped"),
        "server": sv,
        # ⭐ The witness at the OTHER end of the wire, which knows nothing of the cure.
        "dgram_spurious": wit.get("dgram_spurious"),
        "dgram_spurious_d": wit.get("dgram_spurious_d"),
        "dgram_lost": wit.get("dgram_lost"),
        "dgram_ok": wit.get("dgram_ok"),
        "witness": wit,
        "netem_pkt": (None if (pkt0 is None or pkt1 is None) else max(0, pkt1 - pkt0)),
        "ladder": sc,
        "jsonl": j_out,
    }
    # ⭐ And the SECOND LEG, taken from the samples and not from the client's
    #   arithmetic: the coverage of the timeline and the TONE purity.
    n["tone_purity"] = sc.get("tone_purity")
    n["coverage"] = sc.get("coverage")
    n["blocks"] = sc.get("blocks")
    n["arrival_out_of_order"] = sc.get("arrival_out_of_order")
    # ⛔ AND IF THE CLIENT DID NOT STATE THE PURITY, it is REBUILT from its
    #    counters with the same definition — and declared as rebuilt.
    #    ⚠ We do not fall back on the tone purity: it is another quantity, and
    #      swapping them would give a plausible number with the wrong name.
    if n["purity"] is None and n.get("delivered") and n.get("on_wire"):
        n["purity"] = round(n["delivered"] / float(n["on_wire"]), 5)
        n["purezza_ricostruita"] = True
    # ⛔⛔ AND HERE WE CHECK THAT THE NUMBERS THE PREDICATES WILL READ ARE REALLY
    #     THERE — on the dictionary's keys, not on those I believed I was
    #     reading.  ⚠ `[M]` 23 August 2026: the first run printed `stale -
    #     tard - report - rec - dup -` and the bench did NOT stop, because the
    #     check queried `_num(output, "stale")` (right) while the
    #     dictionary asked for `discarded_old` (wrong).  ⇒ A check that
    #     does not look at the same thing as the code it protects protects nothing.
    MANDATORY = ("on_wire", "delivered", "stale", "late_audio", "out",
                   "rec", "dup", "missed", "purity")
    missing = [k for k in MANDATORY if n.get(k) is None]
    if missing:
        return {"outcome": "⛔ THE CLIENT'S COUNTERS WERE NOT READ (%s): the "
                         "TO_READ regexes no longer hook its output"
                         % ", ".join(missing), "queue": output[-900:]}
    return n


def numbers_line(n):
    def q(x, f="%s"):
        return "-" if x is None else (f % x)
    return ("%-8s PUREZZA %s  (tono %s · cop %s · pagina %s) | filo %s cons %s "
            "vecchi %s tard %s fuori %s (jsonl %s) rec %s dop %s manc %s | "
            "netem %s pkt | srv %s spediti, dgram_spurious %s"
            % (n["rule"], q(n.get("purity"), "%.4f"),
               q(n.get("tone_purity"), "%.3f"), q(n.get("coverage"), "%.4f"),
               q(n.get("page_purity"), "%.3f"),
               q(n.get("on_wire")), q(n.get("delivered")), q(n.get("stale")),
               q(n.get("late_audio")), q(n.get("out")), q(n.get("arrival_out_of_order")),
               q(n.get("rec")), q(n.get("dup")), q(n.get("missed")),
               q(n.get("netem_pkt")), q(n.get("shipped_server")),
               q(n.get("dgram_spurious"))) + " rifiut %s" % q(n.get("server_refused")))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE SELF-TEST: THE PREDICATES MUST BE ABLE TO GIVE RED
#
# ⛔ «A predicate never seen failing is not a predicate.»  Here the
#    numbers are manufactured — the good ones and the bad ones — and every predicate is
#    required to give the verdict written next to it.  If the self-test is not green, no
#    number of this bench is to be believed.
# ═══════════════════════════════════════════════════════════════════════════
def _n(**kw):
    base = {"purity": None, "tone_purity": None, "page_purity": None,
            "coverage": None, "on_wire": None, "delivered": None,
            "stale": None, "late_audio": None, "out": None, "arrival_out_of_order": None,
            "dup": None, "rec": None, "missed": None, "received": None,
            "netem_pkt": None, "shipped_server": None,
            "dgram_spurious": None, "dgram_spurious_d": None}
    base.update(kw)
    return base


def certify():
    print("⭐ SELF-TEST OF THE PREDICATES — the expectation is written FIRST, and the numbers")
    print("   are MANUFACTURED: what is tested here is that they can give RED.\n")

    # An «old» run on a profile that bites, and its cured twin.
    v_broken = _n(purity=0.62, on_wire=5000, delivered=3100, stale=1900,
                 coverage=0.62, tone_purity=0.41, netem_pkt=12000,
                 shipped_server=5000, dgram_spurious=31, missed=1)
    u_healthy = _n(purity=0.9982, on_wire=5000, delivered=4991, stale=3,
                late_audio=6, out=812, arrival_out_of_order=810, dup=0, rec=790,
                missed=1, coverage=0.9985, tone_purity=0.997,
                netem_pkt=12100, shipped_server=5000, dgram_spurious=29)

    cases = [
        # ── the positive control: «does the profile bite?» ─────────────────
        ("positive control · the profile BITES (purity 0.62 · 1900 thrown away)",
         a_collapses_with_old(0.90, 100), v_broken, u_healthy, True),
        ("⚠ MUTE  · the profile does NOT bite (purity 0.991 · 3 thrown away) ⇒ I do NOT "
         "judge, and it is not a green",
         a_collapses_with_old(0.90, 100),
         _n(purity=0.991, stale=3, on_wire=5000), u_healthy, None),
        ("⚠ MUTE  · bites little: purity 0.45 but only 20 thrown away",
         a_collapses_with_old(0.90, 100),
         _n(purity=0.45, stale=20, on_wire=5000), u_healthy, None),
        ("⛔ RED · CONTRADICTION: 1900 thrown away AND purity 0.99",
         a_collapses_with_old(0.90, 100),
         _n(purity=0.99, stale=1900, on_wire=5000), u_healthy, False),
        ("⚠ MUTE  · the old rule's purity was not read",
         a_collapses_with_old(0.90, 100), _n(stale=1900), u_healthy, None),

        # ── the cure brings it back up ─────────────────────────────────────
        ("the cure brings it back up (purity 0.9982 · late 6 out of 5000 on the wire)",
         a_rises_with_new(), v_broken, u_healthy, True),
        ("⛔ RED · the cure does NOT bring it back up (purity 0.31)",
         a_rises_with_new(), v_broken,
         _n(purity=0.31, late_audio=4, on_wire=5000), False),
        ("⛔ RED · back up but the damage moved onto the late ones (900/5000)",
         a_rises_with_new(), v_broken,
         _n(purity=0.99, late_audio=900, on_wire=5000), False),
        ("⚠ MUTE  · the new rule did not state scartati_tardivi",
         a_rises_with_new(), v_broken, _n(purity=0.99, on_wire=5000), None),

        # ── the second leg: the samples, not the client's arithmetic ────────
        ("⭐ the TONE confirms (cov 0.62 → 0.9985 · tone 0.41 → 0.997)",
         a_tone_confirms(), v_broken, u_healthy, True),
        ("⛔ RED · the client says 0.998 but the SAMPLES say the "
         "coverage did not rise",
         a_tone_confirms(), _n(coverage=0.62, tone_purity=0.41),
         _n(coverage=0.63, tone_purity=0.42), False),
        ("⛔ RED · the coverage rises but the tone gets WORSE",
         a_tone_confirms(), _n(coverage=0.62, tone_purity=0.90),
         _n(coverage=0.99, tone_purity=0.55), False),
        ("⚠ MUTE  · the coverage was not measured",
         a_tone_confirms(), _n(), _n(), None),

        # ── the honesty of the cure ────────────────────────────────────────
        ("⭐ the honesty of the cure: fuori_ordine 812 > 0",
         a_out_positive, v_broken, u_healthy, True),
        ("⛔⭐ RED · purity 0.999 BUT fuori_ordine 0: it is not curing, "
         "it is not seeing the reordering",
         a_out_positive, v_broken,
         _n(purity=0.999, out=0, late_audio=0, on_wire=5000), False),
        ("⚠ MUTE  · the client did not state fuori_ordine",
         a_out_positive, v_broken, _n(purity=0.999), None),

        ("duplicates 0 with both", a_zero_duplicates, v_broken, u_healthy, True),
        ("⛔ RED · 7 duplicates with the new rule", a_zero_duplicates, v_broken,
         _n(dup=7), False),
        ("⛔ RED · 2 duplicates with the old rule", a_zero_duplicates,
         _n(dup=2), _n(dup=0), False),

        # ── the denominator ────────────────────────────────────────────────
        ("smooth · the two rules coincide (0.9990 / 0.9992)",
         a_both_coincide(), _n(purity=0.9990), _n(purity=0.9992), True),
        ("⛔ RED · on the easy case the two rules DIVERGE (0.999 / 0.60)",
         a_both_coincide(), _n(purity=0.999), _n(purity=0.60), False),
        ("⛔ RED · they coincide but both are low (0.40 / 0.41)",
         a_both_coincide(), _n(purity=0.40), _n(purity=0.41), False),
        ("smooth · no reordering on `lo` without a qdisc",
         a_no_reorder_on_smooth, _n(stale=0), _n(out=0), True),
        ("⛔ RED · on the smooth line there are 40 overtakes: something else reorders",
         a_no_reorder_on_smooth, _n(stale=0), _n(out=40), False),

        # ── the loss is declared, and the tone does not go back to 1 ────────
        ("bad home · the loss from BOTH ENDS (2879 sent, 2813 on the wire "
         "= 2.29 %)", a_declared_loss(0.02), v_broken,
         _n(shipped_server=2879, on_wire=2813, server_refused=2134,
            missed=2183), True),
        ("⭐⛔ RED · the REAL case of 23 August read with the WRONG number: "
         "`missed` 2183 out of 4996 would be 43.7 %",
         a_declared_loss(0.437), v_broken,
         _n(shipped_server=2879, on_wire=2813, server_refused=2134,
            missed=2183), False),
        ("⛔ RED · «2 % loss» but EVERYTHING arrived on the wire",
         a_declared_loss(0.02), v_broken,
         _n(shipped_server=5000, on_wire=5000), False),
        ("⛔ RED · the client saw MORE than the server sent",
         a_declared_loss(0.02), v_broken,
         _n(shipped_server=4000, on_wire=4200), False),
        ("⚠ MUTE  · the server's «spediti» was not read",
         a_declared_loss(0.02), v_broken, _n(on_wire=5000), None),
        ("with 2 % loss the tone does NOT go back to 1 (0.93)",
         a_tone_does_not_return_to_one(), v_broken, _n(tone_purity=0.93), True),
        ("⛔ RED · with 2 % loss the tone goes back to 0.999: the judge is blind, "
         "the network is not healed",
         a_tone_does_not_return_to_one(), v_broken, _n(tone_purity=0.999), False),

        # ── the two ends of the wire ───────────────────────────────────────
        ("⭐ the two ends: the SERVER confirms the reordering (29+31 dgram_spurious)",
         a_reorder_from_both_ends, v_broken, u_healthy, True),
        ("⭐ the server is silent but the DATA see the reordering (fuori 812): green, "
         "with the price declared",
         a_reorder_from_both_ends, _n(stale=1004, dgram_spurious=0),
         _n(dgram_spurious=0, out=812, arrival_out_of_order=810), True),
        ("⚠ MUTE  · NONE of the three ends sees reordering: the profile does not bite",
         a_reorder_from_both_ends, _n(stale=0, dgram_spurious=0),
         _n(dgram_spurious=0, out=0, arrival_out_of_order=0, purity=0.999), None),
        ("the two ends agree", a_ends_do_not_contradict, v_broken, u_healthy, True),
        ("⛔ RED · the server sees 29 reorderings, the receiver ZERO",
         a_ends_do_not_contradict, v_broken,
         _n(dgram_spurious=29, out=0, arrival_out_of_order=0), False),
        ("smooth: neither of the two sees reordering", a_ends_do_not_contradict,
         _n(dgram_spurious=0), _n(dgram_spurious=0, out=0, arrival_out_of_order=0), True),
        ("⚠ MUTE  · the binary does not have the datagram witness",
         a_ends_do_not_contradict, _n(), _n(out=5), None),

        # ── the ground of the measurement ──────────────────────────────────
        ("the netem saw the traffic (12000 + 12100 pkt)",
         a_netem_has_seen, v_broken, u_healthy, True),
        ("⚠ MUTE  · the netem saw NOTHING: the u32 filter does not bite",
         a_netem_has_seen, _n(netem_pkt=0), _n(netem_pkt=0), None),
        ("the server sent in both runs", a_server_has_sent, v_broken, u_healthy, True),
        ("⛔ RED · the server did not send: the red is not the network's",
         a_server_has_sent, _n(shipped_server=0), _n(shipped_server=0), False),
        ("⚠ MUTE  · the server's «final count» was not read",
         a_server_has_sent, _n(), _n(), None),
    ]

    green, rossi, silent = True, 0, 0
    for name, pred, v, u, expected in cases:
        passes, why = pred(v, u)
        good = (passes is expected) if (expected is None or passes is None) else (passes == expected)
        green = green and good
        if expected is False:
            rossi += 1
        if expected is None:
            silent += 1
        print("  %-4s %-70s expected %-5s · seen %-5s"
              % ("OK" if good else "⛔NO", name[:70], expected, passes))
        if not good:
            print("        why: %s" % why)

    # ═══ THE SAMPLE JUDGE IS CERTIFIED TOO ═════════════════════════════════
    print()
    print("⭐ THE SAMPLE JUDGE, on MANUFACTURED audio:")
    import random, tempfile
    amp = 0.5 * 32767
    tmp = tempfile.mkdtemp(prefix="b77-cert-")
    camp = FREQUENCY * STEP_PCM_US // 1000000

    def factory(fpath, drop_prob, shuffle, seed=77):
        """5 ms PCM blocks of a 440 Hz tone, `instant` every 5000 us."""
        random.seed(seed)
        lines = []
        for k in range(1400):                 # 7 s
            if drop_prob and random.random() < drop_prob:
                continue                      # ⛔ the block does NOT go in: it is a gap
            n0 = k * camp
            b = bytearray()
            for i in range(camp):
                x = int(amp * math.sin(2 * math.pi * HZ * (n0 + i) / FREQUENCY))
                b += struct.pack("<hh", x, x)
            lines.append({"instant": 1000000 + k * STEP_PCM_US, "codec": 2,
                          "byte": base64.b64encode(bytes(b)).decode()})
        if shuffle:
            # ⭐ The ARRIVAL reordering: the lines are swapped in pairs, and the
            #   judge must stay INDIFFERENT — it puts the blocks where the
            #   `instant` says, not where they are written.  ⛔ If it were not
            #   indifferent, it would accusations the cure of a defect of its own.
            for i in range(0, len(lines) - 1, 2):
                lines[i], lines[i + 1] = lines[i + 1], lines[i]
        with open(fpath, "w") as f:
            for r in lines:
                f.write(json.dumps(r) + "\n")
        return fpath

    #  (name, thrown away, shuffle, expected coverage ±0.02, expected tone [min,max])
    prove = [
        ("0-healthy — all blocks, in order", 0.0, False, 1.00, (0.95, 1.0)),
        ("1-⭐ shuffled — same blocks, ARRIVAL out of sequence",
         0.0, True, 1.00, (0.95, 1.0)),
        ("2-⛔ 5 % of blocks thrown away", 0.05, False, 0.95, (0.0, 0.99)),
        ("3-⛔ 20 % thrown away (the old rule under jitter)",
         0.20, False, 0.80, (0.0, 0.90)),
        ("4-⛔ 50 % thrown away", 0.50, False, 0.50, (0.0, 0.70)),
    ]
    healthy_runs = {}
    for name, drop, shuffle, cov, (pmin, pmax) in prove:
        f = factory(os.path.join(tmp, name.split(" ")[0] + ".jsonl"), drop, shuffle)
        s = ladder(f, windows=5)
        pt, cp = s.get("tone_purity"), s.get("coverage")
        good = (pt is not None and pmin <= pt <= pmax
                 and cp is not None and abs(cp - cov) <= 0.02)
        green = green and good
        if pmax < 0.95:
            rossi += 1
        healthy_runs[name[0]] = (pt, cp)
        print("  %-4s %-56s expected cov %.2f (seen %s) · expected tone [%.2f,%.2f] "
              "(seen %s)" % ("OK" if good else "⛔NO", name[:56], cov, cp,
                              pmin, pmax, pt))
    # ⭐⭐ AND THE CASE THAT MATTERS MOST OF ALL: shuffling the ARRIVAL must
    #    change NOTHING.  If it did, the judge would punish the new rule
    #    merely for keeping the late blocks.
    ug = (healthy_runs.get("0") == healthy_runs.get("1"))
    green = green and ug
    print("  %-4s %-56s %s"
          % ("OK" if ug else "⛔NO",
             "5-⭐⭐ the judge is INDIFFERENT to arrival order",
             "healthy %s == shuffled %s" % (healthy_runs.get("0"), healthy_runs.get("1"))))

    # ═══ AND THE JUDGE'S SHORTCUT IS COMPARED WITH `07-b42` ════════════════
    #  ⛔ `tone_purity()` uses an `rfft` instead of 1901 Goertzels.  They are the
    #     same thing only if the bin falls on the whole Hz — and it is not taken
    #     on trust: it is compared.
    print()
    samples = [int(amp * math.sin(2 * math.pi * HZ * k / FREQUENCY))
                + int(0.05 * amp * math.sin(2 * math.pi * 997 * k / FREQUENCY))
                for k in range(FREQUENCY)]
    fast = tone_purity(samples)
    slow = G42.judge([x / 32768.0 for x in samples])
    equal = (fast.get("hz") == slow.get("hz")
              and fast.get("purity") is not None
              and abs(fast["purity"] - slow["purity"]) <= 1e-4)
    green = green and equal
    print("  %-4s %-56s rfft %s Hz / %s  ·  07-b42 %s Hz / %s"
          % ("OK" if equal else "⛔NO",
             "6-⭐ the rfft shortcut == the 1901 Goertzels of 07-b42",
             fast.get("hz"), fast.get("purity"),
             slow.get("hz"), slow.get("purity")))

    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)

    # ═══ ⛔⛔ AND THE REGEXES ARE TESTED ON THE CLIENT'S REAL OUTPUT ════════
    #   A regex that does not hook does NOT give an error: it gives `None` on everything,
    #   that is a bench that keeps silent on every predicate.  ⚠ It really happened on
    #   23 August 2026: the first draft looked for `on_wire`, `discarded_old`,
    #   `out_of_order` — the INTERNAL names — and the client prints `sul wire`,
    #   `stale`, `report`.  No red: silence.
    print()
    print("⭐ THE REGEXES, ON THE CLIENT'S REAL OUTPUT (01-b3-cliente.py:606):")
    fake = (
        "   [audio] received 5001 · 1200240 bytes of payload · codec 2\n"
        "   [audio] discarded — short 0 · type 0 · prefix 0 · old 1900\n"
        "   [audio] reorder — rule new · on wire 5001 · received 5001 · "
        "delivered 4991 · PURITY 0.9980 (page 0.9980)\n"
        "   [audio] reorder — late 6 · out 812 · rec 790 · dup 0 · "
        "missed 1 times 3 · rearms 2 · step 5000us\n"
        "   [audio] blocks written to /srv/remotix/tmp/09nr2/b77.jsonl (4991)\n")
    expected_vals = [("on_wire", 5001), ("delivered", 4991), ("stale", 1900),
              ("late_audio", 6), ("out", 812), ("rec", 790), ("dup", 0),
              ("missed", 1), ("missed_times", 3), ("rearms", 2),
              ("short", 0), ("type", 0), ("prefix", 0), ("step_us", 5000)]
    for name, expected in expected_vals:
        seen = _num(fake, name)
        good = (seen == expected)
        green = green and good
        if not good:
            print("  ⛔NO  %-16s expected %-8s seen %s" % (name, expected, seen))
    for name, expected in (("purity", 0.9980), ("page_purity", 0.9980)):
        seen = _dec(fake, name)
        good = (seen == expected)
        green = green and good
        if not good:
            print("  ⛔NO  %-16s expected %-8s seen %s" % (name, expected, seen))
    reg = _declared_rule(fake)
    green = green and (reg == "new")
    print("  %-4s all %d counters hooked, and the rule in force "
          "is «%s»" % ("OK" if reg == "new" else "⛔NO",
                       len(expected_vals) + 2, reg))
    # ⛔ And the negative case: an output that does NOT carry the counters must be
    #   recognised as such, not mistaken for «all at zero».
    blank = "   [audio] received 0 · 0 bytes of payload · codec (none)\n"
    blind = (_num(blank, "on_wire") is None and _dec(blank, "purity") is None
             and _declared_rule(blank) is None)
    green = green and blind
    rossi += 1
    print("  %-4s ⛔ and an output WITHOUT the counters returns `None`, not zero"
          % ("OK" if blind else "⛔NO"))

    print()
    if green:
        print("⭐ SELF-TEST GREEN — %d cases, of which %d that MUST give RED and "
              "%d that must KEEP SILENT." % (len(cases) + len(prove) + 4, rossi, silent))
        print("   ⇒ the predicates can fail and can refuse, and their")
        print("     greens can be believed.")
    else:
        print("⛔ SELF-TEST RED: the predicates do NOT do what they say.")
        print("   ⇒ no number of this bench is to be believed.")
    return 0 if green else 3


# ═══════════════════════════════════════════════════════════════════════════
def measure(a):
    log("09-b77 · THE AUDIO REORDERING CURE, PAIRED")
    inf("port %d · user %s (uid %d) · tree %s" % (PORT, ACCOUNT, UID_B, TREE_DIR))
    inf("⛔ «%s» (ssh + the 7730) is NOT touched · netem ONLY on `lo`, u32 filters "
        "on port %d only" % (FORBIDDEN_IFACE, PORT))
    inf("the two runs are identical in everything except `--audio-rule`")
    os.makedirs(OUT, exist_ok=True)

    if not terrain_check():
        ko("⛔ I do NOT measure: the ground is not ready (what is missing is above)")
        return 2

    profiles = [p for p in PROFILES if not a.only or a.only in p[0]]
    if not profiles:
        ko("no profile is called «%s»" % a.only)
        return 2

    # ⛔ THE LOCK: the `netem` on `lo` is only one for the whole machine.
    log("THE netem LOCK")
    try:
        LOCK.take(CHI, seconds=a.lease, wait=a.wait)
    except LOCK.NotMine as e:
        ko(str(e))
        return 2

    expiry = time.time() + a.lease
    outcomes = []
    try:
        # The guardian: the network goes back as it was even if this script dies.
        NETWORK.guardian_arm(min(a.lease, (a.seconds + 90) * 2 * len(profiles) + 300))

        log("THE SCENE — a short session to bring the stage and the sink to life, "
            "then the tone")
        if not NETWORK.trigger_session():
            ko("the session does not open: I do NOT measure")
            return 2
        if not NETWORK.tone_turn_on():
            ko("the tone is NOT playing inside the session: I stop, instead of "
               "measuring silence and calling it network")
            return 2
        ok("the tone plays: the graph has incoming links to the sink")

        for name, rules, text, predicates in profiles:
            log("%s · %s" % (name, text))
            if time.time() > expiry - (a.seconds + 90) * 2:
                ko("the lock lease is about to expire: I do NOT start «%s» "
                   "— better a profile not measured than one measured under "
                   "someone else's netem" % name)
                outcomes.append({"profile": name, "passes": None,
                              "outcome": "NON MISURATO — lock lease running out"})
                break
            g_ok, q = NETWORK.broken(rules)
            if not g_ok:
                ko(q)
                outcomes.append({"profile": name, "passes": None,
                              "outcome": "tc refused the rule: %s" % q})
                break
            inf("tc: %s" % " ".join(q.split("\n")[:3])[:200])
            # ⛔ M3 is rechecked at EVERY profile: «the tone was playing at the start»
            #    is not «the tone is playing now».
            rc, out, _ = root("env ACCOUNT=%s UID_B=%d WORKDIR=%s python3 "
                              "%s/banchi/07-b64-scena.py graph"
                              % (ACCOUNT, UID_B, WORKDIR, TREE_DIR))
            try:
                leg = json.loads(out).get("incoming_links", 0)
            except Exception:
                leg = -1
            inf("M3: incoming links to the sink = %s" % leg)
            if leg <= 0:
                ko("the tone no longer plays: I do NOT judge this profile")
                outcomes.append({"profile": name, "passes": None,
                              "outcome": "NOTHING TO JUDGE — the tone was silent"})
                continue

            rounds = {}
            for rule in RULES:
                n = cur_round(name, rule, a.seconds)
                rounds[rule] = n
                if n.get("outcome"):
                    ko("%s: %s" % (rule, n["outcome"]))
                else:
                    print("    %s" % numbers_line(n))
            v, u = rounds["old"], rounds["new"]
            if v.get("outcome") or u.get("outcome"):
                outcomes.append({"profile": name, "passes": None, "rounds": rounds,
                              "outcome": "a run produced no numbers"})
                continue

            # ⭐ AND HERE THE EXPECTATIONS STOP BEING PROSE.
            verdicts = []
            for pred in predicates:
                passes, why = pred(v, u)
                verdicts.append({"passes": passes, "why": why})
                print("    %s %s" % ("OK " if passes else ("⚠  " if passes is None
                                                          else "⛔ NO"), why))
            rossi = [x for x in verdicts if x["passes"] is False]
            silent = [x for x in verdicts if x["passes"] is None]
            passes = None if (silent and not rossi) else (not rossi)
            outcomes.append({"profile": name, "rules": rules, "text": text,
                          "rounds": rounds, "verdicts": verdicts, "passes": passes})
    finally:
        log("⛔ THE NETWORK IS PUT BACK AS IT WAS, and CHECKED")
        try:
            NETWORK.tone_turn_off()
        except Exception as e:
            ko("the tone did not stop: %s" % e)
        try:
            NETWORK.guardian_disarm()
            NETWORK.restore()
        except Exception as e:
            ko("⛔ the network was NOT put back: %s" % e)
        LOCK.release(CHI)

    with open(os.path.join(OUT, "b77-esiti.json"), "w") as f:
        json.dump(outcomes, f, ensure_ascii=False, indent=1)

    # ═══ THE PAIRED TABLE ══════════════════════════════════════════════════
    log("THE PAIRED TABLE — profile × rule")
    print("    %-13s %-8s %8s %7s %7s %8s %8s %7s %6s %7s %6s %6s %7s"
          % ("profile", "rule", "PURITY", "tone", "cov.", "on_wire",
             "deliv.", "stale", "tard", "out", "rec", "dup", "srv:fal"))
    for e in outcomes:
        for rule in RULES:
            n = (e.get("rounds") or {}).get(rule)
            if not n or n.get("outcome"):
                print("    %-13s %-8s   (no numbers)" % (e["profile"], rule))
                continue
            def q(x, f="%s"):
                return "-" if x is None else (f % x)
            print("    %-13s %-8s %8s %7s %7s %8s %8s %7s %6s %7s %6s %6s %7s"
                  % (e["profile"], rule, q(n.get("purity"), "%.4f"),
                     q(n.get("tone_purity"), "%.3f"), q(n.get("coverage"), "%.4f"),
                     q(n.get("on_wire")), q(n.get("delivered")),
                     q(n.get("stale")), q(n.get("late_audio")), q(n.get("out")),
                     q(n.get("rec")), q(n.get("dup")), q(n.get("dgram_spurious"))))

    rossi = [e for e in outcomes if e.get("passes") is False]
    silent = [e for e in outcomes if e.get("passes") is None]
    log("THE VERDICT — %d profiles, %d red, %d not judged"
        % (len(outcomes), len(rossi), len(silent)))
    for e in rossi:
        for x in e.get("verdicts", []):
            if x["passes"] is False:
                ko("%s: %s" % (e["profile"], x["why"]))
    for e in silent:
        inf("⚠ %s: %s" % (e["profile"], e.get("outcome") or "an expectation refused to judge"))
    inf("the outcomes in full: %s" % os.path.join(OUT, "b77-esiti.json"))
    if rossi:
        return 1
    if silent:
        return 2      # ⚠ «I did not measure» is an outcome of ITS OWN, not a green
    ok("⭐ all the profiles did what was written beforehand")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("step", nargs="?", default="measure",
                   choices=["measure", "terrain", "restore", "status"])
    p.add_argument("--certify", action="store_true",
                   help="⭐ the self-test of the predicates, with manufactured numbers: "
                        "it shows they can give RED")
    p.add_argument("--seconds", type=int, default=25,
                   help="how long EACH run lasts (and there are two runs per profile)")
    p.add_argument("--only", default="", help="one profile only, by name")
    p.add_argument("--lease", type=int, default=900,
                   help="⛔ how long I hold the netem lock: short, there are "
                        "other agents queued")
    p.add_argument("--wait", type=int, default=2400,
                   help="how many seconds I wait for my turn")
    a = p.parse_args()
    if a.certify:
        return certify()
    if a.step == "terrain":
        return 0 if terrain_check() else 2
    if a.step in ("restore", "status"):
        log("THE TEST MACHINE'S NETWORK")

        return 0 if NETWORK.restore() else 2
    return measure(a)


if __name__ == "__main__":
    sys.exit(main())
