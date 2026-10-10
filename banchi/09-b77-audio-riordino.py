#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b77-audio-riordino — THE AUDIO REORDERING CURE, PAIRED.

⛔⭐ THE FACT TO CLOSE.  On 23 August 2026 `src/pagina.html` changed its
    reading of `RCP.md` §6.3.  Before: a PCM block arriving **behind a newer
    one** was thrown away, full stop (`istante <= ultimo_istante` ⇒ `scartati_vecchi`).
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
   `--audio-regola vecchia|nuova`.
   ⛔ A single run with the cure on would prove nothing: it would look
      the same as a profile that does not reorder at all.  It is the reason
      `09-riavvia-7920.sh` exists, written for audio.

⛔ THE SWITCH BELONGS TO THE CLIENT, and it is not mine: it is in `banchi/01-b3-cliente.py`
   (`--audio-regola vecchia|nuova`, default `vecchia`).  This bench is
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

⛔⛔ THE `[M]` «purezza 0,175» OF `pagina.html` LINE 6474 **IS NOT THE TERM OF
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
    python3 banchi/09-b77-audio-riordino.py --certifica     # ⛔ first of all
    python3 banchi/09-b77-audio-riordino.py terreno
    python3 banchi/09-b77-audio-riordino.py misura [--secondi 25] [--solo jitter-2]
    python3 banchi/09-b77-audio-riordino.py rimetti
"""
import argparse, base64, importlib.util, json, math, os, re, struct, subprocess, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ ISOLATION, and it is written BEFORE importing anything: the modules
#    below read the environment at import time, not at call time.
#    ⚠ Putting it after the import would give a bench that runs on someone else's port
#      and does not notice — `LEZIONI.md` §1.26.
# ═══════════════════════════════════════════════════════════════════════════
PORTA = int(os.environ.get("PORTA", "7931"))
UTENTE = os.environ.get("UTENTE", "provanr2")
UID_B = int(os.environ.get("UID_B", "1031"))
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/09nr2-src")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/09nr2")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/09nr2-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/09nr2")
UNITA = os.environ.get("UNITA", "remotix-%d" % PORTA)
PAROLA_UTENTE = os.environ.get("PAROLA_UTENTE", "nr2-riordino-2026")
MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
IND = os.environ.get("IND", "192.168.0.2")
FUORI = os.environ.get("FUORI", os.path.join(
    "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX/"
    "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad", "b77"))

# ⛔ The ports that are NOT mine.  They are counted, not touched.
VIETATE = ("7900", "7910", "7920")
VIETATA_IFACE = "enp7s0"

for k, v in (("PORTA", str(PORTA)), ("UTENTE", UTENTE), ("UID_B", str(UID_B)),
             ("ALBERO", ALB), ("LAV", LAV), ("DENTRO_ALB", DENTRO_ALB),
             ("DENTRO_LAV", DENTRO_LAV), ("FUORI", FUORI), ("IND", IND),
             ("MACCHINA", MACCHINA)):
    os.environ[k] = v


def _carica(nome, file_):
    sp = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file_))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


RETE = _carica("b64rete", "07-b64-rete.py")      # root(), guasta(), tono_*, guardiano_*
LUCCHETTO = _carica("lucchetto", "09-lucchetto.py")
G42 = _carica("g42", "07-b42-giudice.py")        # the tone judge, certified

FREQUENZA = 48000
CANALI = 2
PASSO_PCM_US = 5000          # §5.3: the PCM block is 5 ms
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
#      reading».  ⇒ Here every expectation is `(v, u) -> (passa, perche)` — `v` are the
#      numbers of the OLD rule, `u` those of the NEW one — and `passa=None` means
#      «I refuse to judge», which is an outcome of ITS OWN and not a green.
#
# ⛔⛔⛔ AND THE QUANTITY IS DECLARED, BECAUSE THERE ARE TWO «PURITIES» AND THEY ARE NOT THE
#       SAME THING:
#
#         · `purezza`      = **`consegnati / sul_filo`**, and the client counts it.
#           ⭐ `sul_filo` is counted BEFORE the screening: it is how many blocks the network
#           delivered; `consegnati` is how many came out of the §6.3 screening.
#           ⇒ The network's loss does not even enter the denominator, and this
#           is the quantity the cure is judged on.
#         · `purezza_tono` = how much energy sits in the 440 Hz line, and I count it
#           MYSELF from the rebuilt samples (`07-b42`, certified).  ⚠ It is the
#           second leg, independent of the client's arithmetic, and on a
#           profile with loss **it cannot go back to 1**.
#
# ⛔⛔ AND THE `[M]` «purezza 0,175» OF `pagina.html` LINE 6474 **IS NOT A
#      REFERENCE**: its definition is not known (with the denominator the page
#      benches use — `suonati/ricevuti`, `09-b74:300` — that ratio
#      is ~1.000 with both rules, because the discard does `continue`
#      BEFORE `ricevuti++`).  ⇒ Comparing a number whose
#      definition is unknown with one whose definition is known would be the most polite way of
#      manufacturing a triumph.  Here the expectation is a BOUND, not that point.
# ═══════════════════════════════════════════════════════════════════════════
def _p(cond, perche):
    return (bool(cond), perche)


def _muto(perche):
    return (None, perche)


def _c(n, chiave):
    """⛔ `CODER.md` §3.10: «I did not read» is not «zero».  A missing number
       returns `None` and makes the predicate KEEP SILENT, it does not make it pass."""
    return n.get(chiave)


# ── the positive control: without it the bench has no right to green ───────
def a_crolla_con_vecchia(tetto, min_vecchi):
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
       was not made.  ⚠ But it is not a green either: `passa=None` stops
       the whole profile, and that is what it must do.

    ⭐ THE REAL RED EXISTS ALL THE SAME, and it is the contradiction: many blocks
       thrown away AND a high purity.  They are the same quantity seen twice, and
       if they contradict each other one of the two counts is wrong.
    """
    def f(v, u):
        pv, ve = _c(v, "purezza"), _c(v, "vecchi")
        sf = _c(v, "sul_filo")
        if pv is None or ve is None:
            return _muto("the old rule gave no purezza/scartati_vecchi: "
                         "I do not judge")
        if ve >= min_vecchi and pv > tetto:
            return _p(False,
                      "⛔ CONTRADICTION: the old rule says it threw away "
                      "%d blocks but the purity stays %.4f (sul_filo %s) — they are "
                      "the same quantity seen twice, and one of the two counts "
                      "is wrong" % (ve, pv, sf))
        if pv > tetto or ve < min_vecchi:
            return _muto("⛔ THE PROFILE DOES NOT BITE: with the old rule the "
                         "purity had to collapse below %.2f (seen %.4f) and the "
                         "blocks thrown away be >= %d (seen %d).  ⇒ I do NOT "
                         "JUDGE: a green here would not be a measurement, it would be "
                         "chance" % (tetto, pv, min_vecchi, ve))
        return _p(True,
                  "OLD: the profile BITES — purity %.4f <= %.2f and %d blocks "
                  "thrown away (>= %d) out of %s arrived on the wire"
                  % (pv, tetto, ve, min_vecchi, sf))
    return f


def a_risale_con_nuova(min_purezza=0.95):
    """The cure must restore the delivered fraction, and without moving
       the damage onto `scartati_tardivi`.

    ⚠ And `scartati_tardivi` is NOT `scartati_vecchi`: a block arriving too
      late **on the wire** ends up in `scartati_vecchi`; `scartati_tardivi` is the
      safety net AFTER the decoder.  They are two different cases, and
      confusing them would make this predicate blind to the second.
    """
    def f(v, u):
        pu, ta = _c(u, "purezza"), _c(u, "tardivi")
        sf = _c(u, "sul_filo")
        if pu is None:
            return _muto("the new rule gave no purity: I do not judge")
        if ta is None:
            return _muto("the new rule gave no scartati_tardivi: I do not judge")
        tetto = max(20, int(0.01 * (sf or 0)))
        return _p(pu >= min_purezza and ta <= tetto,
                  "NEW: purity >= %.2f (seen %.4f) and scartati_tardivi <= %d "
                  "(seen %d) — the safety net after the decoder did not "
                  "take the damage" % (min_purezza, pu, tetto, ta))
    return f


def a_il_tono_conferma(guadagno=0.05):
    """⭐ THE SECOND LEG, FROM THE SAMPLES AND NOT FROM THE CLIENT'S ARITHMETIC.

    `purezza` is computed by the client, which is also the object of the measurement: that is
    where the cure lives.  ⇒ A number taken ELSEWHERE is needed.  Here the blocks are
    put back in their place in time (`base + istante`, as the page's anchor
    does) and two things are measured on the SAMPLES:
      · `copertura`    = how much of the timeline really has sound;
      · `purezza_tono` = how much energy sits in the 440 Hz line (`07-b42`).
    ⛔ If the client says «I delivered everything» and the samples say that half
       the timeline is silence, one of the two is lying.
    """
    def f(v, u):
        cv, cu = _c(v, "copertura"), _c(u, "copertura")
        tv, tu = _c(v, "purezza_tono"), _c(u, "purezza_tono")
        if cv is None or cu is None:
            return _muto("the coverage was not measured: I do not judge")
        if tv is None or tu is None:
            return _p(cu - cv >= guadagno,
                      "⚠ without purezza_tono: the coverage rises by >= %.2f "
                      "(%.4f → %.4f)" % (guadagno, cv, cu))
        return _p(cu - cv >= guadagno and tu > tv,
                  "THE TONE CONFIRMS: coverage %.4f → %.4f (+%.4f, required "
                  "%.2f) and purezza_tono %.3f → %.3f"
                  % (cv, cu, cu - cv, guadagno, tv, tu))
    return f


def a_fuori_positivo(v, u):
    """⭐⛔ THE PREDICATE THAT KEEPS THE CURE HONEST.

       `fuori_ordine` must be GREATER THAN ZERO in the profiles that reorder.
       If it were zero and the purity high, the cure is not «recovering the
       reordered ones»: it is simply **not seeing the reordering**, and the good
       number would be chance — the same face as a network that does not break."""
    fu = _c(u, "fuori")
    if fu is None:
        return _muto("the client did not say `fuori_ordine`: I do not judge")
    return _p(fu > 0,
              "NEW: fuori_ordine > 0 (seen %d) — the cure is looking at "
              "REAL reorderings, not a quiet network" % fu)


def a_doppioni_zero(v, u):
    """⛔ Zero with both rules.  If they rise, someone counts twice —
       and a block delivered twice would double the signal, which §6.3 does not
       allow and is the worst way of failing."""
    dv, du = _c(v, "dop"), _c(u, "dop")
    if du is None:
        return _muto("the client did not say `doppioni`: I do not judge")
    return _p(du == 0 and (dv in (0, None)),
              "duplicates 0 with both (old %s, new %s)"
              % ("-" if dv is None else dv, du))


def a_le_due_coincidono(tolleranza=0.01, min_purezza=0.98):
    """⛔ The denominator.  On a line that does NOT reorder the two rules must
       give the same result: if they already differ here, the cure has a defect
       on the easy case and none of its other greens counts."""
    def f(v, u):
        pv, pu = _c(v, "purezza"), _c(u, "purezza")
        if pv is None or pu is None:
            return _muto("one of the two purities is missing: I do not judge")
        return _p(abs(pv - pu) <= tolleranza and pv >= min_purezza and pu >= min_purezza,
                  "SMOOTH: |%.4f - %.4f| <= %.2f and both >= %.2f"
                  % (pv, pu, tolleranza, min_purezza))
    return f


def a_niente_riordino_sul_liscio(v, u):
    """⛔ On `lo` without a qdisc packets do not overtake each other.  If here
       `fuori_ordine` rises, something else is reordering — and then not even the
       numbers of the broken profiles can be attributed to `netem`."""
    fu, ve = _c(u, "fuori"), _c(v, "vecchi")
    if fu is None:
        return _muto("the client did not say `fuori_ordine`: I do not judge")
    return _p(fu == 0 and (ve or 0) == 0,
              "SMOOTH: fuori_ordine 0 (seen %d) and scartati_vecchi 0 (seen %s)"
              % (fu, ve))



def a_perdita_dichiarata(frazione, tolleranza=0.6):
    """⚠ WHERE THERE IS ALSO LOSS, THE LOST PART IS DECLARED — AND FROM BOTH ENDS.

    `purezza` does not see it, and must not: `sul_filo` counts what the network
    DELIVERED, so what is lost does not even enter the denominator.  ⇒ If it were not
    declared separately, a profile with 2 % loss would pass for
    «clean» only because the right number is being looked at.

    ⛔⛔ AND THE CLIENT'S `mancati` IS NOT USED — `[M]` 23 August 2026, and it is a
         red the bench gave itself.  On `casa-cattiva` the client
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
           lost on the wire = (sent by the server) − (client's sul_filo)
       ⚠ And `rifiutati` is reported separately: it is not a `netem` defect, it is
         the price the transport pays on that network — and it must be said.
    """
    def f(v, u):
        sp, sf = _c(u, "spediti_server"), _c(u, "sul_filo")
        if sp is None or not sf:
            return _muto("the server's «spediti» or the client's «sul filo» were not "
                         "read: the loss cannot be attributed")
        perduti = sp - sf
        if perduti < 0:
            return _p(False,
                      "⛔ the client says it saw MORE blocks on the wire than "
                      "the server sent (%d > %d): one of the two "
                      "counts is wrong" % (sf, sp))
        vista = perduti / float(sp)
        return _p(abs(vista - frazione) <= tolleranza * frazione + 0.005,
                  "THE LOSS IS DECLARED, FROM BOTH ENDS: the server sent "
                  "%d, the client saw %d on the wire ⇒ **%d lost on the "
                  "network, %.2f%%** (netem removes %.0f%%).  ⚠ And separately: "
                  "%s REFUSED by ngtcp2, that is never put on the wire — those "
                  "do not belong to netem, and the client's `mancati` (%s) counts them "
                  "together with the lost ones"
                  % (sp, sf, perduti, vista * 100, frazione * 100,
                     _c(u, "rifiutati_server"), _c(u, "mancati")))
    return f


def a_il_tono_non_torna_a_uno(tetto=0.98):
    """⚠ AND HERE THE TONE PURITY **MUST NOT** GO BACK TO 1, and it is an expectation
       like the others: with 2 % loss gaps remain that no rule of the
       receiver can fill.  ⛔ If it went back to 1 it would be the judge that is
       blind, not the network that is healed."""
    def f(v, u):
        tu = _c(u, "purezza_tono")
        if tu is None:
            return _muto("purezza_tono was not measured: I do not judge")
        return _p(tu <= tetto,
                  "the tone does NOT go back to 1 (%.3f <= %.2f), and must not: the loss "
                  "leaves gaps the receiver cannot fill" % (tu, tetto))
    return f


def a_riordino_dai_due_capi(v, u):
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
       is a datagram **arrived out of sequence**: it is `dgram_falsi`, on the
       `rete-quic` line of the log.

    ⚠ AND THE PRICE IS DECLARED, or this predicate would give false reds.
      `dgram_falsi` can be zero while reordering really exists: ngtcp2
      declares a packet lost only after **three** newer packets
      acknowledged, and a swap between neighbours — which is what a 2 ms jitter
      does on 5 ms blocks — does not reach three.  ⇒ The server's witness is
      **sufficient, not necessary**.

    ⇒ The rule: it is enough that ONE of the three ends sees the reordering for the profile
      to exist; if NOBODY sees it, the bench **refuses to judge** — a
      green there would be chance, not a measurement.
    """
    srv = _c(u, "dgram_falsi")
    srv_v = _c(v, "dgram_falsi")
    cli = _c(u, "fuori")            # the cure's counter
    mio = _c(u, "fuori_arrivo")     # the overtakes I counted on the JSONL
    vec = _c(v, "vecchi")           # what the OLD rule threw away
    tot_srv = None
    if srv is not None or srv_v is not None:
        tot_srv = (srv or 0) + (srv_v or 0)
    visti = [x for x in (cli, mio, vec) if x]
    if tot_srv is None and not visti and cli is None and mio is None:
        return _muto("no reordering witness was read: I do not judge")
    if tot_srv:
        return _p(True,
                  "THE SERVER confirms it: %d datagrams given up as lost and then "
                  "ACKNOWLEDGED (= out of sequence), and the server knows nothing "
                  "of the cure · receiver: fuori %s, overtakes on the JSONL %s, "
                  "vecchi %s" % (tot_srv, cli, mio, vec))
    if visti:
        return _p(True,
                  "⚠ the server's witness is silent (dgram_falsi 0: ngtcp2 "
                  "declares lost only after 3 newer packets, and a "
                  "swap between neighbours does not get there), ⭐ but the reordering shows "
                  "in the DATA: fuori %s, overtakes on the JSONL %s, vecchi %s"
                  % (cli, mio, vec))
    return _muto("NONE of the three ends sees reordering (server 0, fuori %s, "
                 "overtakes on the JSONL %s, vecchi %s): the profile DOES NOT BITE, and "
                 "a green here would be chance" % (cli, mio, vec))


def a_capi_non_si_contraddicono(v, u):
    """⛔ And if the two ends contradict each other, it is a fact worth more than
       both: the server saw packets go from lost to
       acknowledged, and the receiver did not see even one out of sequence.
       One of the two is wrong, and until we know which no number counts."""
    srv = _c(u, "dgram_falsi")
    cli, mio = _c(u, "fuori"), _c(u, "fuori_arrivo")
    if srv is None or (cli is None and mio is None):
        return _muto("a witness is missing: I do not compare the two ends")
    if srv > 0 and (cli or 0) == 0 and (mio or 0) == 0:
        return _p(False,
                  "⛔ THE TWO ENDS CONTRADICT EACH OTHER: the server saw %d "
                  "datagrams go from lost to acknowledged, the receiver "
                  "ZERO out of sequence (fuori %s, overtakes on the JSONL %s)"
                  % (srv, cli, mio))
    return _p(True, "the two ends agree (server %s · receiver fuori %s, "
                    "overtakes on the JSONL %s)" % (srv, cli, mio))


def a_netem_ha_visto(v, u):
    """⛔ If the `u32` filter does not bite, the traffic does not go through `netem`: I would have
       measured a HEALTHY network believing it broken, and written that the cure is needed
       where there was nothing to cure.  ⚠ It is not a red: it is an «I did not
       measure», which is an outcome of its own."""
    pv, pu = _c(v, "netem_pkt"), _c(u, "netem_pkt")
    if pv is None or pu is None:
        return _muto("the netem packet count was not read")
    if (pv + pu) <= 0:
        return _muto("the netem saw NO packet: the u32 filter "
                     "on port %d does not bite, and this profile does not exist" % PORTA)
    return _p(True, "the netem saw %d + %d packets (the filter bites)" % (pv, pu))


def a_server_ha_spedito(v, u):
    """⛔ The client knows how many datagrams it received; it does not know how many
       left.  Without this, a SERVER defect would be attributed to
       `netem` (R13)."""
    sv, su = _c(v, "spediti_server"), _c(u, "spediti_server")
    if sv is None or su is None:
        return _muto("the server's «final count» was not read")
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
PROFILI = [
    ("liscio", [],
     "the denominator: no fault, and the two rules must coincide",
     [a_le_due_coincidono(), a_niente_riordino_sul_liscio, a_doppioni_zero,
      a_server_ha_spedito, a_capi_non_si_contraddicono]),

    ("jitter-2", ["delay", "20ms", "2ms", "distribution", "normal"],
     "jitter ±2 ms, less than one PCM block (5 ms): it is the MILDEST profile that "
     "reorders, and the bound of its positive control is 0.90 — one block in "
     "ten thrown away is twenty gaps per second",
     [a_netem_ha_visto, a_server_ha_spedito, a_riordino_dai_due_capi,
      a_capi_non_si_contraddicono, a_crolla_con_vecchia(0.90, 100),
      a_risale_con_nuova(0.95), a_il_tono_conferma(), a_fuori_positivo,
      a_doppioni_zero]),

    ("jitter-5", ["delay", "20ms", "5ms", "distribution", "normal"],
     "jitter ±5 ms = one whole block: overtakes grow, and the bound drops "
     "to 0.80",
     [a_netem_ha_visto, a_server_ha_spedito, a_riordino_dai_due_capi,
      a_capi_non_si_contraddicono, a_crolla_con_vecchia(0.80, 300),
      a_risale_con_nuova(0.95), a_il_tono_conferma(), a_fuori_positivo,
      a_doppioni_zero]),

    ("jitter-15", ["delay", "30ms", "15ms", "distribution", "normal"],
     "jitter ±15 ms = three blocks: with the old rule listening is broken, and "
     "the bound drops to 0.60",
     [a_netem_ha_visto, a_server_ha_spedito, a_riordino_dai_due_capi,
      a_capi_non_si_contraddicono, a_crolla_con_vecchia(0.60, 800),
      a_risale_con_nuova(0.95), a_il_tono_conferma(), a_fuori_positivo,
      a_doppioni_zero]),

    ("riordino-25", ["delay", "10ms", "reorder", "25%", "50%"],
     "⭐ EXPLICIT REORDERING, which is NOT jitter: one packet in four "
     "jumps the queue and leaves at once.  ⛔ The `delay 10ms` is mandatory, or "
     "`reorder` does nothing",
     [a_netem_ha_visto, a_server_ha_spedito, a_riordino_dai_due_capi,
      a_capi_non_si_contraddicono, a_crolla_con_vecchia(0.90, 300),
      a_risale_con_nuova(0.95), a_il_tono_conferma(), a_fuori_positivo,
      a_doppioni_zero]),

    ("casa-cattiva", ["delay", "40ms", "20ms", "distribution", "normal",
                      "loss", "2%"],
     "⚠ HERE THERE IS ALSO LOSS.  `purezza` does not see it — `sul_filo` counts what "
     "the network DELIVERED — so the lost part is declared separately "
     "(`mancati`), and the TONE purity must not go back to 1",
     [a_netem_ha_visto, a_server_ha_spedito, a_riordino_dai_due_capi,
      a_capi_non_si_contraddicono, a_crolla_con_vecchia(0.80, 500),
      a_risale_con_nuova(0.95), a_perdita_dichiarata(0.02),
      a_il_tono_non_torna_a_uno(), a_fuori_positivo, a_doppioni_zero]),
]

REGOLE = ("vecchia", "nuova")


# ═══════════════════════════════════════════════════════════════════════════
# THE JUDGE — THE BLOCKS IN THEIR PLACE, AS THE PAGE'S ANCHOR DOES
# ═══════════════════════════════════════════════════════════════════════════
def purezza_tono(campioni):
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
    ⛔ And this equality is not taken on trust: `--certifica`
       COMPARES it with `07-b42.giudica()` on a real case and demands that
       they coincide to four decimals.  If numpy is missing or they do not coincide, we
       fall back on `07-b42` and DECLARE it (one window only).
    """
    m = len(campioni)
    if m != FREQUENZA:
        return G42.giudica([x / 32768.0 for x in campioni])
    try:
        import numpy as _np
    except ImportError:
        return G42.giudica([x / 32768.0 for x in campioni])
    x = _np.asarray(campioni, dtype=_np.float64) / 32768.0
    X = _np.fft.rfft(x)
    p = _np.abs(X[100:2001]) ** 2
    somma = float(p.sum())
    if somma <= 0:
        return {"esito": "GIUDICATO", "campioni": m, "hz": 0, "purezza": None,
                "rms": 0.0}
    k = int(p.argmax())
    return {"esito": "GIUDICATO", "campioni": m, "hz": 100 + k,
            "rms": round(float(_np.sqrt((x * x).mean())), 4),
            "purezza": round(float(p[k] / somma), 4)}


def scaletta(percorso, finestre=8, finestra_s=1):
    """⭐ The canvas of silence and the blocks placed at `base + istante`.

    ⛔ They are NOT pasted in arrival order: that would be the wrong judgement for
       the new rule, which KEEPS the late blocks — pasting them wherever they
       happen to fall would put the past in the middle of the present and accuse the cure
       of a defect that belongs to the judge.

    ⚠ The gaps stay SILENCE, and they must: a gap is what one hears, and
      stitching the edges would make it invisible to the tone judge.
    """
    if not os.path.exists(percorso) or os.path.getsize(percorso) == 0:
        return {"esito": "NIENTE DA GIUDICARE — the JSONL is missing or empty"}
    blocchi, visti, dop = [], set(), 0
    fuori_arrivo, massimo = 0, None
    for r in open(percorso):
        r = r.strip()
        if not r:
            continue
        d = json.loads(r)
        if d.get("codec") != 2:
            continue                     # ⛔ PCM only: Opus is not judged this way
        ist = int(d["istante"])
        if ist in visti:
            dop += 1
            continue
        visti.add(ist)
        # ⭐ The overtakes counted on the DATA, not on the client's counter: it is the
        #    second leg of the proof that the profile really reorders.
        if massimo is not None and ist < massimo:
            fuori_arrivo += 1
        massimo = ist if massimo is None else max(massimo, ist)
        blocchi.append((ist, base64.b64decode(d["byte"])))
    if len(blocchi) < 200:
        return {"esito": "NIENTE DA GIUDICARE — %d blocks" % len(blocchi),
                "blocchi": len(blocchi)}
    base = min(i for i, _ in blocchi)
    fine = max(i for i, _ in blocchi)
    n_tot = int(round((fine - base) / 1e6 * FREQUENZA)) + (FREQUENZA * PASSO_PCM_US // 1000000)
    if n_tot <= 0 or n_tot > FREQUENZA * 3600:
        return {"esito": "NIENTE DA GIUDICARE — absurd timeline (%d)" % n_tot}
    tela = [0] * n_tot
    pieno = bytearray(n_tot)
    for ist, b in blocchi:
        off = int(round((ist - base) / 1e6 * FREQUENZA))
        n = len(b) // (2 * CANALI)
        if n <= 0 or off < 0 or off + n > n_tot:
            continue
        v = struct.unpack("<%dh" % (n * CANALI), b[:n * CANALI * 2])
        sx = v[0::CANALI]
        for k in range(n):
            tela[off + k] = sx[k]
            pieno[off + k] = 1
    coperti = sum(pieno)
    copertura = coperti / float(n_tot)
    # ⭐ The purity over SEVERAL windows, and the median is taken: a single window
    #   catches chance.  ⚠ The windows are equally spaced, not chosen.
    n = finestra_s * FREQUENZA
    purezze, hz_visti = [], []
    if n_tot >= n:
        posti = ([0] if finestre <= 1 else
                 [int(k * (n_tot - n) / (finestre - 1)) for k in range(finestre)])
        for i in posti:
            g = purezza_tono(tela[i:i + n])
            if g.get("purezza") is not None:
                purezze.append(g["purezza"])
                hz_visti.append(g.get("hz"))
    purezze_ord = sorted(purezze)
    med = (purezze_ord[len(purezze_ord) // 2] if purezze_ord else None)
    return {"esito": "GIUDICATO", "blocchi": len(blocchi),
            "doppioni_scaletta": dop, "fuori_arrivo": fuori_arrivo,
            "durata_s": round(n_tot / float(FREQUENZA), 3),
            "campioni_scritti": coperti, "campioni_totali": n_tot,
            "copertura": round(copertura, 5),
            "purezza_tono": None if med is None else round(med, 4),
            "purezza_tono_min": None if not purezze_ord else round(purezze_ord[0], 4),
            "purezza_tono_max": None if not purezze_ord else round(purezze_ord[-1], 4),
            "finestre": len(purezze_ord),
            "hz": hz_visti[len(hz_visti) // 2] if hz_visti else None}


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
#    the middle of the present and accuse the cure of a defect of the judge.


# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT TALKS TO THE TEST MACHINE
# ═══════════════════════════════════════════════════════════════════════════
def root(comando, tetto=300):
    return RETE.root(comando, tetto)


def netem_pacchetti():
    """The packets the `netem` node REALLY saw pass.

    ⛔ It is the substitute for the `reordered` counter, which on this machine does not
       exist (`[M]`: iproute2 6.15.0, `grep -ac reordered /usr/sbin/tc` = 0).
       ⚠ It does not say «how many it reordered»; it says «the u32 filter bites», which is
       the condition without which the profile does not exist at all.
    """
    rc, out, _ = root("/usr/sbin/tc -s qdisc show dev lo")
    dentro, ultimo = False, None
    for riga in out.split("\n"):
        s = riga.strip()
        if s.startswith("qdisc"):
            dentro = ("netem" in s)
            continue
        if dentro:
            m = re.search(r"Sent\s+(\d+)\s+bytes\s+(\d+)\s+pkt", s)
            if m:
                ultimo = int(m.group(2))
                dentro = False
    return ultimo


def righe_registro():
    rc, out, _ = root("wc -l < %s/registro.log 2>/dev/null || echo 0" % LAV)
    try:
        return int(out.strip())
    except Exception:
        return 0


def conti_del_server(riga0):
    """⛔ «the network lost it» and «the server never sent it» give the same
       number on the client's side.  Here the SERVER's count is read, and only
       from `riga0` on, so it belongs to THIS run."""
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -a 'audio of .*final "
                      "count' | tail -1" % (riga0 + 1, LAV))
    r = out.strip()
    if not r:
        return {"esito": "NIENTE DA LEGGERE — no «final count» in this run"}
    m = re.search(r"(\d+) blocks sent, (\d+) dropped.*?(\d+) refused.*?"
                  r"(\d+) DEFERRED", r)
    if not m:
        return {"esito": "line found but unreadable", "riga": r[:160]}
    return {"spediti": int(m.group(1)), "buttati": int(m.group(2)),
            "rifiutati": int(m.group(3)), "rimandati": int(m.group(4))}


def testimone_del_server(riga0):
    """⭐⭐ THE REORDERING WITNESS THAT KNOWS NOTHING OF THE CURE.

    The `rete-quic` line of the log carries, since 23 August 2026:
        dgram_persi= dgram_persi_d= dgram_ok= dgram_falsi= dgram_falsi_d=
    ⛔ It is read only from `riga0` on, so it belongs to THIS run; and the counters
       are cumulative PER CONNECTION, so the maximum of the
       window is taken — not the sum, which would count every line from scratch.
    ⚠ If the binary is older than the witness, the fields are not there: we
      return `None`, not zero (`CODER.md` §3.10)."""
    rc, out, _ = root("tail -n +%d %s/registro.log 2>/dev/null | grep -a "
                      "'rete-quic ' | tail -40" % (riga0 + 1, LAV))
    righe = [r for r in out.split("\n") if "rete-quic " in r]
    if not righe:
        return {"esito": "NIENTE DA LEGGERE — no «rete-quic» line in "
                         "this run", "righe": 0}
    fuori = {"righe": len(righe)}
    for campo in ("dgram_persi", "dgram_ok", "dgram_falsi"):
        valori = []
        for r in righe:
            m = re.search(r"\b%s=(\d+)" % campo, r)
            if m:
                valori.append(int(m.group(1)))
        fuori[campo] = max(valori) if valori else None
    for campo in ("dgram_persi_d", "dgram_falsi_d"):
        valori = []
        for r in righe:
            m = re.search(r"\b%s=(\d+)" % campo, r)
            if m:
                valori.append(int(m.group(1)))
        # ⚠ The `_d` are differences between one line and the next: here they are SUMMED.
        fuori[campo] = sum(valori) if valori else None
    if fuori.get("dgram_falsi") is None:
        fuori["esito"] = ("the binary does NOT have the datagram witness "
                          "(no `dgram_falsi=` on the rete-quic line)")
    return fuori


# ⛔⛔ THE NAMES ARE COPIED FROM HOW THE CLIENT PRINTS THEM, NOT FROM HOW THEY ARE CALLED
#      INSIDE.  `01-b3-cliente.py:606` prints:
#
#        [audio] discarded — short 0 · type 0 · prefix 0 · old 1900
#        [audio] reorder — rule nuova · on wire 5001 · received 5001 ·
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

DA_LEGGERE = {
    "sul_filo":       r"\bon wire\s+(\d+)",
    "ricevuti":       r"·\s*received\s+(\d+)\s*·",
    "consegnati":     r"\bdelivered\s+(\d+)",
    "vecchi":         r"\bold\s+(\d+)",
    "corti":          r"\bshort\s+(\d+)",
    "tipo":           r"\btype\s+(\d+)",
    "prefisso":       r"\bprefix\s+(\d+)",
    "tardivi":        r"\blate\s+(\d+)",
    "fuori":          r"\bout\s+(\d+)",
    "rec":            r"\brec\s+(\d+)",
    "dop":            r"\bdup\s+(\d+)",
    "mancati":        r"\bmissed\s+(\d+)",
    "mancati_volte":  r"\bmissed\s+\d+\s+times\s+(\d+)",
    "riarmi":         r"\brearms\s+(\d+)",
    "passo_us":       r"\bstep\s+(\d+)us",
}
DA_LEGGERE_DEC = {
    "purezza":        r"PURITY\s+([0-9]+\.[0-9]+)",
    "purezza_pagina": r"\(page\s+([0-9]+\.[0-9]+)\)",
}


def _num(testo, nome):
    """⛔ The LAST occurrence is taken — the counts line comes after all
       the others — and a `None` means «I did not read it», not «zero»."""
    trovato = None
    for m in re.finditer(DA_LEGGERE.get(nome, r"\b%s\b\s+(\d+)" % re.escape(nome)),
                         testo):
        trovato = int(m.group(1))
    return trovato


def _dec(testo, nome):
    trovato = None
    for m in re.finditer(DA_LEGGERE_DEC.get(nome, r"\b%s\b\s+([0-9.]+)" % re.escape(nome)),
                         testo):
        trovato = float(m.group(1))
    return trovato


def _regola_dichiarata(testo):
    """⭐⭐ THE PROOF THAT THE RULE WAS IN FORCE IN THIS RUN.

    ⛔ `LEZIONI.md` E1: «written is not in force».  That `--audio-regola` exists
       in the help does not say the client USED it — an argument accepted
       and ignored would give two identical runs, and the bench would report «no
       difference», which looks the same as «the cure is not needed» and is the
       opposite conclusion.  ⇒ The client prints `rule <nome>` on the counts
       line, and HERE we check it is the one I asked for."""
    trovata = None
    for m in re.finditer(r"\brule\s+(vecchia|nuova)\b", testo):
        trovata = m.group(1)
    return trovata


def cliente_ha_interruttore():
    """⛔ THE CHECK THAT AVOIDS THIS BENCH'S MOST LIKELY FALSE GREEN.

       If `--audio-regola` is not there yet, the two runs would use the same
       rule: the bench would see two equal numbers and report «no
       difference».  ⚠ It looks the same as «the cure is not needed» — and is the
       opposite conclusion.  ⇒ It is checked, and if it is not there we STOP.

       ⭐ And the copy THAT RUNS (inside the container) is checked, not the
          laptop's: «I wrote it» is not «it is in force» (`LEZIONI.md` E1).
    """
    esito = {}
    locale = os.path.join(QUI, "01-b3-cliente.py")
    try:
        t = open(locale, encoding="utf-8", errors="replace").read()
        esito["portatile"] = "--audio-regola" in t
    except Exception as e:
        esito["portatile"] = False
        esito["portatile_perche"] = str(e)
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root "
                        "'python3 %s/banchi/01-b3-cliente.py --help 2>&1 | "
                        "grep -c -- --audio-regola'" % DENTRO_ALB, 180)
    conta = 0
    for r in (out + err).split("\n"):
        if r.strip().isdigit():
            conta = int(r.strip())
    esito["dentro_aiuto"] = conta > 0
    esito["dentro"] = conta > 0
    return esito


def terreno_controlla():
    """⛔ The bench refuses to measure on a ground that is not its own."""
    log("THE GROUND — port %d · user %s (uid %d) · tree %s" % (PORTA, UTENTE, UID_B, ALB))
    guai = []
    rc, out, _ = root("id %s >/dev/null 2>&1 && echo si || echo no" % UTENTE)
    if "si" not in out:
        guai.append("the user «%s» does not exist — PORTA=%d UTENTE=%s UID_B=%d "
                    "PAROLA_UTENTE=%s ALBERO=%s LAV=%s bash banchi/07-b64-terreno.sh utente"
                    % (UTENTE, PORTA, UTENTE, UID_B, PAROLA_UTENTE, ALB, LAV))
    rc, out, _ = root("test -s %s/parola && echo si || echo no" % LAV)
    if "si" not in out:
        guai.append("%s/parola (0600) is missing: D12 forbids the password in argv" % LAV)
    rc, out, _ = root("test -x %s/src/remotix && echo si || echo no" % ALB)
    if "si" not in out:
        guai.append("the tree «%s» has no binary: `... bash banchi/07-b64-terreno.sh porta`" % ALB)
    rc, out, _ = root("ss -uln 2>/dev/null | grep -c ':%d ' || true" % PORTA)
    mio = out.strip()
    if mio == "0":
        guai.append("nobody is listening on %d: `... bash banchi/07-b64-terreno.sh accendi`" % PORTA)
    # ⛔ The other agents' ports are COUNTED, not touched.
    conto = []
    for p in VIETATE:
        rc, o, _ = root("ss -uln 2>/dev/null | grep -c ':%s ' || true" % p)
        conto.append("%s:%s" % (p, o.strip()))
    inf("FORBIDDEN ports (counted, not touched): %s" % " ".join(conto))
    inf("my server on %d: %s listener(s)" % (PORTA, mio))
    rc, out, _ = root("/usr/sbin/tc qdisc show dev %s" % VIETATA_IFACE)
    inf("%s (ssh + the user's 7730) — NOT touched: %s"
        % (VIETATA_IFACE, out.strip().split("\n")[0]))
    rc, out, _ = root("uptime")
    inf("load: %s" % out.strip()[-42:])

    interr = cliente_ha_interruttore()
    if interr.get("dentro"):
        ok("the client has `--audio-regola` (in the container, read from `--help`)")
    else:
        guai.append("⛔⛔ THE CLIENT DOES NOT HAVE `--audio-regola` (laptop: %s, "
                    "container: %s).  I do NOT measure: two runs with the same "
                    "rule would give «no difference», which looks the same "
                    "as «the cure is not needed» and is the opposite conclusion"
                    % (interr.get("portatile"), interr.get("dentro")))
    for g in guai:
        ko(g)
    if not guai:
        ok("the ground is there, and it is mine")
    return not guai


def giro(profilo, regola, secondi):
    """One client run, with the chosen rule.  Returns the numbers, or `None`."""
    nome = "%s-%s" % (profilo, regola)
    j_fuori = os.path.join(FUORI, nome + ".jsonl")
    t_fuori = os.path.join(FUORI, nome + ".txt")
    for f in (j_fuori, t_fuori):
        try: os.remove(f)
        except Exception: pass
    riga0 = righe_registro()
    pkt0 = netem_pacchetti()
    t0 = time.time()
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s/parola --audio-codec pcm "
              "--audio-regola %s --audio-scrivi %s/b77-%s.jsonl --resta %d"
              % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, regola,
                 DENTRO_LAV, nome, secondi))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro,
                        secondi + 240)
    uscita = out + err
    open(t_fuori, "w").write(uscita)
    subprocess.run("ssh -o BatchMode=yes %s \"printf '%%s\\n' '%s' | sudo -S -p '' "
                   "cat %s/b77-%s.jsonl\" > %s"
                   % (RETE.MACCHINA, RETE.PAROLA_SUDO, LAV, nome, j_fuori),
                   shell=True)
    pkt1 = netem_pacchetti()
    sv = conti_del_server(riga0)
    tst = testimone_del_server(riga0)

    # ⛔ If the client refused `--audio-regola`, its numbers would be
    #    those of the OTHER rule: it is declared and not judged.
    if "unrecognized arguments" in uscita or "invalid choice" in uscita:
        return {"esito": "THE CLIENT REFUSED --audio-regola %s" % regola,
                "coda": uscita[-600:]}
    # ⛔⛔ AND THE RULE MUST BE THE ONE I ASKED FOR, AS STATED BY THE CLIENT.
    #     «I passed it» is not «it used it» (`LEZIONI.md` E1): an argument
    #     accepted and ignored would give two identical runs under two names.
    detta = _regola_dichiarata(uscita)
    if detta != regola:
        return {"esito": "⛔⛔ I ASKED FOR «%s» AND THE CLIENT SAYS «%s»: the two "
                         "runs would not be paired, they would be the same run "
                         "twice" % (regola, detta), "coda": uscita[-600:]}

    sc = scaletta(j_fuori)
    n = {
        "profilo": profilo, "regola": regola, "secondi": round(time.time() - t0, 1),
        # ⭐ THE PAGE'S NAMES, which are the interface agreed with the client.
        #   ⛔ `sul_filo` is counted BEFORE the screening and `consegnati` AFTER: it is the
        #      pair that makes `purezza` a fraction with a denominator that
        #      does not move with the rule.
        "sul_filo": _num(uscita, "sul_filo"),
        "consegnati": _num(uscita, "consegnati"),
        "ricevuti": _num(uscita, "ricevuti"),
        "vecchi": _num(uscita, "vecchi"),
        "corti": _num(uscita, "corti"),
        "tipo": _num(uscita, "tipo"),
        "prefisso": _num(uscita, "prefisso"),
        "tardivi": _num(uscita, "tardivi"),
        "fuori": _num(uscita, "fuori"),
        "dop": _num(uscita, "dop"),
        "rec": _num(uscita, "rec"),
        "mancati": _num(uscita, "mancati"),
        # ⛔ `purezza` = consegnati/sul_filo, and the client counts it.
        #   ⚠ `purezza_pagina` (suonati/ricevuti) is BLIND — the discard does
        #     `continue` before `ricevuti++`, so it is ~1 with both
        #     rules: it is reported only for comparison, and declared as such.
        "purezza": _dec(uscita, "purezza"),
        "purezza_pagina": _dec(uscita, "purezza_pagina"),
        "riarmi": _num(uscita, "riarmi"),
        "regola_dichiarata": _regola_dichiarata(uscita),
        "spediti_server": sv.get("spediti"),
        # ⛔ `rifiutati` = ngtcp2 did not put them on the wire (window closed).
        #    ⚠ They are not network loss, and confusing them with it is R13.
        "rifiutati_server": sv.get("rifiutati"),
        "buttati_server": sv.get("buttati"),
        "server": sv,
        # ⭐ The witness at the OTHER end of the wire, which knows nothing of the cure.
        "dgram_falsi": tst.get("dgram_falsi"),
        "dgram_falsi_d": tst.get("dgram_falsi_d"),
        "dgram_persi": tst.get("dgram_persi"),
        "dgram_ok": tst.get("dgram_ok"),
        "testimone": tst,
        "netem_pkt": (None if (pkt0 is None or pkt1 is None) else max(0, pkt1 - pkt0)),
        "scaletta": sc,
        "jsonl": j_fuori,
    }
    # ⭐ And the SECOND LEG, taken from the samples and not from the client's
    #   arithmetic: the coverage of the timeline and the TONE purity.
    n["purezza_tono"] = sc.get("purezza_tono")
    n["copertura"] = sc.get("copertura")
    n["blocchi"] = sc.get("blocchi")
    n["fuori_arrivo"] = sc.get("fuori_arrivo")
    # ⛔ AND IF THE CLIENT DID NOT STATE THE PURITY, it is REBUILT from its
    #    counters with the same definition — and declared as rebuilt.
    #    ⚠ We do not fall back on the tone purity: it is another quantity, and
    #      swapping them would give a plausible number with the wrong name.
    if n["purezza"] is None and n.get("consegnati") and n.get("sul_filo"):
        n["purezza"] = round(n["consegnati"] / float(n["sul_filo"]), 5)
        n["purezza_ricostruita"] = True
    # ⛔⛔ AND HERE WE CHECK THAT THE NUMBERS THE PREDICATES WILL READ ARE REALLY
    #     THERE — on the dictionary's keys, not on those I believed I was
    #     reading.  ⚠ `[M]` 23 August 2026: the first run printed `vecchi -
    #     tard - fuori - rec - dop -` and the bench did NOT stop, because the
    #     check queried `_num(uscita, "vecchi")` (right) while the
    #     dictionary asked for `scartati_vecchi` (wrong).  ⇒ A check that
    #     does not look at the same thing as the code it protects protects nothing.
    OBBLIGATORI = ("sul_filo", "consegnati", "vecchi", "tardivi", "fuori",
                   "rec", "dop", "mancati", "purezza")
    manca = [k for k in OBBLIGATORI if n.get(k) is None]
    if manca:
        return {"esito": "⛔ THE CLIENT'S COUNTERS WERE NOT READ (%s): the "
                         "DA_LEGGERE regexes no longer hook its output"
                         % ", ".join(manca), "coda": uscita[-900:]}
    return n


def riga_numeri(n):
    def q(x, f="%s"):
        return "-" if x is None else (f % x)
    return ("%-8s PUREZZA %s  (tono %s · cop %s · pagina %s) | filo %s cons %s "
            "vecchi %s tard %s fuori %s (jsonl %s) rec %s dop %s manc %s | "
            "netem %s pkt | srv %s spediti, dgram_falsi %s"
            % (n["regola"], q(n.get("purezza"), "%.4f"),
               q(n.get("purezza_tono"), "%.3f"), q(n.get("copertura"), "%.4f"),
               q(n.get("purezza_pagina"), "%.3f"),
               q(n.get("sul_filo")), q(n.get("consegnati")), q(n.get("vecchi")),
               q(n.get("tardivi")), q(n.get("fuori")), q(n.get("fuori_arrivo")),
               q(n.get("rec")), q(n.get("dop")), q(n.get("mancati")),
               q(n.get("netem_pkt")), q(n.get("spediti_server")),
               q(n.get("dgram_falsi"))) + " rifiut %s" % q(n.get("rifiutati_server")))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE SELF-TEST: THE PREDICATES MUST BE ABLE TO GIVE RED
#
# ⛔ «A predicate never seen failing is not a predicate.»  Here the
#    numbers are manufactured — the good ones and the bad ones — and every predicate is
#    required to give the verdict written next to it.  If the self-test is not green, no
#    number of this bench is to be believed.
# ═══════════════════════════════════════════════════════════════════════════
def _n(**kw):
    base = {"purezza": None, "purezza_tono": None, "purezza_pagina": None,
            "copertura": None, "sul_filo": None, "consegnati": None,
            "vecchi": None, "tardivi": None, "fuori": None, "fuori_arrivo": None,
            "dop": None, "rec": None, "mancati": None, "ricevuti": None,
            "netem_pkt": None, "spediti_server": None,
            "dgram_falsi": None, "dgram_falsi_d": None}
    base.update(kw)
    return base


def certifica():
    print("⭐ SELF-TEST OF THE PREDICATES — the expectation is written FIRST, and the numbers")
    print("   are MANUFACTURED: what is tested here is that they can give RED.\n")

    # An «old» run on a profile that bites, and its cured twin.
    v_rotto = _n(purezza=0.62, sul_filo=5000, consegnati=3100, vecchi=1900,
                 copertura=0.62, purezza_tono=0.41, netem_pkt=12000,
                 spediti_server=5000, dgram_falsi=31, mancati=1)
    u_sano = _n(purezza=0.9982, sul_filo=5000, consegnati=4991, vecchi=3,
                tardivi=6, fuori=812, fuori_arrivo=810, dop=0, rec=790,
                mancati=1, copertura=0.9985, purezza_tono=0.997,
                netem_pkt=12100, spediti_server=5000, dgram_falsi=29)

    casi = [
        # ── the positive control: «does the profile bite?» ─────────────────
        ("positive control · the profile BITES (purity 0.62 · 1900 thrown away)",
         a_crolla_con_vecchia(0.90, 100), v_rotto, u_sano, True),
        ("⚠ MUTE  · the profile does NOT bite (purity 0.991 · 3 thrown away) ⇒ I do NOT "
         "judge, and it is not a green",
         a_crolla_con_vecchia(0.90, 100),
         _n(purezza=0.991, vecchi=3, sul_filo=5000), u_sano, None),
        ("⚠ MUTE  · bites little: purity 0.45 but only 20 thrown away",
         a_crolla_con_vecchia(0.90, 100),
         _n(purezza=0.45, vecchi=20, sul_filo=5000), u_sano, None),
        ("⛔ RED · CONTRADICTION: 1900 thrown away AND purity 0.99",
         a_crolla_con_vecchia(0.90, 100),
         _n(purezza=0.99, vecchi=1900, sul_filo=5000), u_sano, False),
        ("⚠ MUTE  · the old rule's purity was not read",
         a_crolla_con_vecchia(0.90, 100), _n(vecchi=1900), u_sano, None),

        # ── the cure brings it back up ─────────────────────────────────────
        ("the cure brings it back up (purity 0.9982 · late 6 out of 5000 on the wire)",
         a_risale_con_nuova(), v_rotto, u_sano, True),
        ("⛔ RED · the cure does NOT bring it back up (purity 0.31)",
         a_risale_con_nuova(), v_rotto,
         _n(purezza=0.31, tardivi=4, sul_filo=5000), False),
        ("⛔ RED · back up but the damage moved onto the late ones (900/5000)",
         a_risale_con_nuova(), v_rotto,
         _n(purezza=0.99, tardivi=900, sul_filo=5000), False),
        ("⚠ MUTE  · the new rule did not state scartati_tardivi",
         a_risale_con_nuova(), v_rotto, _n(purezza=0.99, sul_filo=5000), None),

        # ── the second leg: the samples, not the client's arithmetic ────────
        ("⭐ the TONE confirms (cov 0.62 → 0.9985 · tone 0.41 → 0.997)",
         a_il_tono_conferma(), v_rotto, u_sano, True),
        ("⛔ RED · the client says 0.998 but the SAMPLES say the "
         "coverage did not rise",
         a_il_tono_conferma(), _n(copertura=0.62, purezza_tono=0.41),
         _n(copertura=0.63, purezza_tono=0.42), False),
        ("⛔ RED · the coverage rises but the tone gets WORSE",
         a_il_tono_conferma(), _n(copertura=0.62, purezza_tono=0.90),
         _n(copertura=0.99, purezza_tono=0.55), False),
        ("⚠ MUTE  · the coverage was not measured",
         a_il_tono_conferma(), _n(), _n(), None),

        # ── the honesty of the cure ────────────────────────────────────────
        ("⭐ the honesty of the cure: fuori_ordine 812 > 0",
         a_fuori_positivo, v_rotto, u_sano, True),
        ("⛔⭐ RED · purity 0.999 BUT fuori_ordine 0: it is not curing, "
         "it is not seeing the reordering",
         a_fuori_positivo, v_rotto,
         _n(purezza=0.999, fuori=0, tardivi=0, sul_filo=5000), False),
        ("⚠ MUTE  · the client did not state fuori_ordine",
         a_fuori_positivo, v_rotto, _n(purezza=0.999), None),

        ("duplicates 0 with both", a_doppioni_zero, v_rotto, u_sano, True),
        ("⛔ RED · 7 duplicates with the new rule", a_doppioni_zero, v_rotto,
         _n(dop=7), False),
        ("⛔ RED · 2 duplicates with the old rule", a_doppioni_zero,
         _n(dop=2), _n(dop=0), False),

        # ── the denominator ────────────────────────────────────────────────
        ("smooth · the two rules coincide (0.9990 / 0.9992)",
         a_le_due_coincidono(), _n(purezza=0.9990), _n(purezza=0.9992), True),
        ("⛔ RED · on the easy case the two rules DIVERGE (0.999 / 0.60)",
         a_le_due_coincidono(), _n(purezza=0.999), _n(purezza=0.60), False),
        ("⛔ RED · they coincide but both are low (0.40 / 0.41)",
         a_le_due_coincidono(), _n(purezza=0.40), _n(purezza=0.41), False),
        ("smooth · no reordering on `lo` without a qdisc",
         a_niente_riordino_sul_liscio, _n(vecchi=0), _n(fuori=0), True),
        ("⛔ RED · on the smooth line there are 40 overtakes: something else reorders",
         a_niente_riordino_sul_liscio, _n(vecchi=0), _n(fuori=40), False),

        # ── the loss is declared, and the tone does not go back to 1 ────────
        ("bad home · the loss from BOTH ENDS (2879 sent, 2813 on the wire "
         "= 2.29 %)", a_perdita_dichiarata(0.02), v_rotto,
         _n(spediti_server=2879, sul_filo=2813, rifiutati_server=2134,
            mancati=2183), True),
        ("⭐⛔ RED · the REAL case of 23 August read with the WRONG number: "
         "`mancati` 2183 out of 4996 would be 43.7 %",
         a_perdita_dichiarata(0.437), v_rotto,
         _n(spediti_server=2879, sul_filo=2813, rifiutati_server=2134,
            mancati=2183), False),
        ("⛔ RED · «2 % loss» but EVERYTHING arrived on the wire",
         a_perdita_dichiarata(0.02), v_rotto,
         _n(spediti_server=5000, sul_filo=5000), False),
        ("⛔ RED · the client saw MORE than the server sent",
         a_perdita_dichiarata(0.02), v_rotto,
         _n(spediti_server=4000, sul_filo=4200), False),
        ("⚠ MUTE  · the server's «spediti» was not read",
         a_perdita_dichiarata(0.02), v_rotto, _n(sul_filo=5000), None),
        ("with 2 % loss the tone does NOT go back to 1 (0.93)",
         a_il_tono_non_torna_a_uno(), v_rotto, _n(purezza_tono=0.93), True),
        ("⛔ RED · with 2 % loss the tone goes back to 0.999: the judge is blind, "
         "the network is not healed",
         a_il_tono_non_torna_a_uno(), v_rotto, _n(purezza_tono=0.999), False),

        # ── the two ends of the wire ───────────────────────────────────────
        ("⭐ the two ends: the SERVER confirms the reordering (29+31 dgram_falsi)",
         a_riordino_dai_due_capi, v_rotto, u_sano, True),
        ("⭐ the server is silent but the DATA see the reordering (fuori 812): green, "
         "with the price declared",
         a_riordino_dai_due_capi, _n(vecchi=1004, dgram_falsi=0),
         _n(dgram_falsi=0, fuori=812, fuori_arrivo=810), True),
        ("⚠ MUTE  · NONE of the three ends sees reordering: the profile does not bite",
         a_riordino_dai_due_capi, _n(vecchi=0, dgram_falsi=0),
         _n(dgram_falsi=0, fuori=0, fuori_arrivo=0, purezza=0.999), None),
        ("the two ends agree", a_capi_non_si_contraddicono, v_rotto, u_sano, True),
        ("⛔ RED · the server sees 29 reorderings, the receiver ZERO",
         a_capi_non_si_contraddicono, v_rotto,
         _n(dgram_falsi=29, fuori=0, fuori_arrivo=0), False),
        ("smooth: neither of the two sees reordering", a_capi_non_si_contraddicono,
         _n(dgram_falsi=0), _n(dgram_falsi=0, fuori=0, fuori_arrivo=0), True),
        ("⚠ MUTE  · the binary does not have the datagram witness",
         a_capi_non_si_contraddicono, _n(), _n(fuori=5), None),

        # ── the ground of the measurement ──────────────────────────────────
        ("the netem saw the traffic (12000 + 12100 pkt)",
         a_netem_ha_visto, v_rotto, u_sano, True),
        ("⚠ MUTE  · the netem saw NOTHING: the u32 filter does not bite",
         a_netem_ha_visto, _n(netem_pkt=0), _n(netem_pkt=0), None),
        ("the server sent in both runs", a_server_ha_spedito, v_rotto, u_sano, True),
        ("⛔ RED · the server did not send: the red is not the network's",
         a_server_ha_spedito, _n(spediti_server=0), _n(spediti_server=0), False),
        ("⚠ MUTE  · the server's «final count» was not read",
         a_server_ha_spedito, _n(), _n(), None),
    ]

    verde, rossi, muti = True, 0, 0
    for nome, pred, v, u, atteso in casi:
        passa, perche = pred(v, u)
        buono = (passa is atteso) if (atteso is None or passa is None) else (passa == atteso)
        verde = verde and buono
        if atteso is False:
            rossi += 1
        if atteso is None:
            muti += 1
        print("  %-4s %-70s expected %-5s · seen %-5s"
              % ("OK" if buono else "⛔NO", nome[:70], atteso, passa))
        if not buono:
            print("        why: %s" % perche)

    # ═══ THE SAMPLE JUDGE IS CERTIFIED TOO ═════════════════════════════════
    print()
    print("⭐ THE SAMPLE JUDGE, on MANUFACTURED audio:")
    import random, tempfile
    amp = 0.5 * 32767
    tmp = tempfile.mkdtemp(prefix="b77-cert-")
    camp = FREQUENZA * PASSO_PCM_US // 1000000

    def fabbrica(percorso, buttane, mescola, seme=77):
        """5 ms PCM blocks of a 440 Hz tone, `istante` every 5000 us."""
        random.seed(seme)
        righe = []
        for k in range(1400):                 # 7 s
            if buttane and random.random() < buttane:
                continue                      # ⛔ the block does NOT go in: it is a gap
            n0 = k * camp
            b = bytearray()
            for i in range(camp):
                x = int(amp * math.sin(2 * math.pi * HZ * (n0 + i) / FREQUENZA))
                b += struct.pack("<hh", x, x)
            righe.append({"istante": 1000000 + k * PASSO_PCM_US, "codec": 2,
                          "byte": base64.b64encode(bytes(b)).decode()})
        if mescola:
            # ⭐ The ARRIVAL reordering: the lines are swapped in pairs, and the
            #   judge must stay INDIFFERENT — it puts the blocks where the
            #   `istante` says, not where they are written.  ⛔ If it were not
            #   indifferent, it would accuse the cure of a defect of its own.
            for i in range(0, len(righe) - 1, 2):
                righe[i], righe[i + 1] = righe[i + 1], righe[i]
        with open(percorso, "w") as f:
            for r in righe:
                f.write(json.dumps(r) + "\n")
        return percorso

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
    sani = {}
    for nome, butta, mescola, cop, (pmin, pmax) in prove:
        f = fabbrica(os.path.join(tmp, nome.split(" ")[0] + ".jsonl"), butta, mescola)
        s = scaletta(f, finestre=5)
        pt, cp = s.get("purezza_tono"), s.get("copertura")
        buono = (pt is not None and pmin <= pt <= pmax
                 and cp is not None and abs(cp - cop) <= 0.02)
        verde = verde and buono
        if pmax < 0.95:
            rossi += 1
        sani[nome[0]] = (pt, cp)
        print("  %-4s %-56s expected cov %.2f (seen %s) · expected tone [%.2f,%.2f] "
              "(seen %s)" % ("OK" if buono else "⛔NO", nome[:56], cop, cp,
                              pmin, pmax, pt))
    # ⭐⭐ AND THE CASE THAT MATTERS MOST OF ALL: shuffling the ARRIVAL must
    #    change NOTHING.  If it did, the judge would punish the new rule
    #    merely for keeping the late blocks.
    ug = (sani.get("0") == sani.get("1"))
    verde = verde and ug
    print("  %-4s %-56s %s"
          % ("OK" if ug else "⛔NO",
             "5-⭐⭐ the judge is INDIFFERENT to arrival order",
             "healthy %s == shuffled %s" % (sani.get("0"), sani.get("1"))))

    # ═══ AND THE JUDGE'S SHORTCUT IS COMPARED WITH `07-b42` ════════════════
    #  ⛔ `purezza_tono()` uses an `rfft` instead of 1901 Goertzels.  They are the
    #     same thing only if the bin falls on the whole Hz — and it is not taken
    #     on trust: it is compared.
    print()
    campioni = [int(amp * math.sin(2 * math.pi * HZ * k / FREQUENZA))
                + int(0.05 * amp * math.sin(2 * math.pi * 997 * k / FREQUENZA))
                for k in range(FREQUENZA)]
    veloce = purezza_tono(campioni)
    lento = G42.giudica([x / 32768.0 for x in campioni])
    uguali = (veloce.get("hz") == lento.get("hz")
              and veloce.get("purezza") is not None
              and abs(veloce["purezza"] - lento["purezza"]) <= 1e-4)
    verde = verde and uguali
    print("  %-4s %-56s rfft %s Hz / %s  ·  07-b42 %s Hz / %s"
          % ("OK" if uguali else "⛔NO",
             "6-⭐ the rfft shortcut == the 1901 Goertzels of 07-b42",
             veloce.get("hz"), veloce.get("purezza"),
             lento.get("hz"), lento.get("purezza")))

    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)

    # ═══ ⛔⛔ AND THE REGEXES ARE TESTED ON THE CLIENT'S REAL OUTPUT ════════
    #   A regex that does not hook does NOT give an error: it gives `None` on everything,
    #   that is a bench that keeps silent on every predicate.  ⚠ It really happened on
    #   23 August 2026: the first draft looked for `sul_filo`, `scartati_vecchi`,
    #   `fuori_ordine` — the INTERNAL names — and the client prints `sul filo`,
    #   `vecchi`, `fuori`.  No red: silence.
    print()
    print("⭐ THE REGEXES, ON THE CLIENT'S REAL OUTPUT (01-b3-cliente.py:606):")
    finta = (
        "   [audio] received 5001 · 1200240 bytes of payload · codec 2\n"
        "   [audio] discarded — short 0 · type 0 · prefix 0 · old 1900\n"
        "   [audio] reorder — rule nuova · on wire 5001 · received 5001 · "
        "delivered 4991 · PURITY 0.9980 (page 0.9980)\n"
        "   [audio] reorder — late 6 · out 812 · rec 790 · dup 0 · "
        "missed 1 times 3 · rearms 2 · step 5000us\n"
        "   [audio] blocks written to /srv/remotix/tmp/09nr2/b77.jsonl (4991)\n")
    attesi = [("sul_filo", 5001), ("consegnati", 4991), ("vecchi", 1900),
              ("tardivi", 6), ("fuori", 812), ("rec", 790), ("dop", 0),
              ("mancati", 1), ("mancati_volte", 3), ("riarmi", 2),
              ("corti", 0), ("tipo", 0), ("prefisso", 0), ("passo_us", 5000)]
    for nome, atteso in attesi:
        visto = _num(finta, nome)
        buono = (visto == atteso)
        verde = verde and buono
        if not buono:
            print("  ⛔NO  %-16s expected %-8s seen %s" % (nome, atteso, visto))
    for nome, atteso in (("purezza", 0.9980), ("purezza_pagina", 0.9980)):
        visto = _dec(finta, nome)
        buono = (visto == atteso)
        verde = verde and buono
        if not buono:
            print("  ⛔NO  %-16s expected %-8s seen %s" % (nome, atteso, visto))
    reg = _regola_dichiarata(finta)
    verde = verde and (reg == "nuova")
    print("  %-4s all %d counters hooked, and the rule in force "
          "is «%s»" % ("OK" if reg == "nuova" else "⛔NO",
                       len(attesi) + 2, reg))
    # ⛔ And the negative case: an output that does NOT carry the counters must be
    #   recognised as such, not mistaken for «all at zero».
    vuota = "   [audio] received 0 · 0 bytes of payload · codec (none)\n"
    cieca = (_num(vuota, "sul_filo") is None and _dec(vuota, "purezza") is None
             and _regola_dichiarata(vuota) is None)
    verde = verde and cieca
    rossi += 1
    print("  %-4s ⛔ and an output WITHOUT the counters returns `None`, not zero"
          % ("OK" if cieca else "⛔NO"))

    print()
    if verde:
        print("⭐ SELF-TEST GREEN — %d cases, of which %d that MUST give RED and "
              "%d that must KEEP SILENT." % (len(casi) + len(prove) + 4, rossi, muti))
        print("   ⇒ the predicates can fail and can refuse, and their")
        print("     greens can be believed.")
    else:
        print("⛔ SELF-TEST RED: the predicates do NOT do what they say.")
        print("   ⇒ no number of this bench is to be believed.")
    return 0 if verde else 3


# ═══════════════════════════════════════════════════════════════════════════
def misura(a):
    log("09-b77 · THE AUDIO REORDERING CURE, PAIRED")
    inf("port %d · user %s (uid %d) · tree %s" % (PORTA, UTENTE, UID_B, ALB))
    inf("⛔ «%s» (ssh + the 7730) is NOT touched · netem ONLY on `lo`, u32 filters "
        "on port %d only" % (VIETATA_IFACE, PORTA))
    inf("the two runs are identical in everything except `--audio-regola`")
    os.makedirs(FUORI, exist_ok=True)

    if not terreno_controlla():
        ko("⛔ I do NOT measure: the ground is not ready (what is missing is above)")
        return 2

    profili = [p for p in PROFILI if not a.solo or a.solo in p[0]]
    if not profili:
        ko("no profile is called «%s»" % a.solo)
        return 2

    # ⛔ THE LOCK: the `netem` on `lo` is only one for the whole machine.
    log("THE netem LOCK")
    try:
        LUCCHETTO.prendi(CHI, secondi=a.affitto, attesa=a.attesa)
    except LUCCHETTO.NonMio as e:
        ko(str(e))
        return 2

    scadenza = time.time() + a.affitto
    esiti = []
    try:
        # The guardian: the network goes back as it was even if this script dies.
        RETE.guardiano_arma(min(a.affitto, (a.secondi + 90) * 2 * len(profili) + 300))

        log("THE SCENE — a short session to bring the stage and the sink to life, "
            "then the tone")
        if not RETE.innesca_sessione():
            ko("the session does not open: I do NOT measure")
            return 2
        if not RETE.tono_accendi():
            ko("the tone is NOT playing inside the session: I stop, instead of "
               "measuring silence and calling it network")
            return 2
        ok("the tone plays: the graph has incoming links to the sink")

        for nome, regole, testo, predicati in profili:
            log("%s · %s" % (nome, testo))
            if time.time() > scadenza - (a.secondi + 90) * 2:
                ko("the lock lease is about to expire: I do NOT start «%s» "
                   "— better a profile not measured than one measured under "
                   "someone else's netem" % nome)
                esiti.append({"profilo": nome, "passa": None,
                              "esito": "NON MISURATO — lock lease running out"})
                break
            g_ok, q = RETE.guasta(regole)
            if not g_ok:
                ko(q)
                esiti.append({"profilo": nome, "passa": None,
                              "esito": "tc refused the rule: %s" % q})
                break
            inf("tc: %s" % " ".join(q.split("\n")[:3])[:200])
            # ⛔ M3 is rechecked at EVERY profile: «the tone was playing at the start»
            #    is not «the tone is playing now».
            rc, out, _ = root("env UTENTE=%s UID_B=%d LAV=%s python3 "
                              "%s/banchi/07-b64-scena.py grafo"
                              % (UTENTE, UID_B, LAV, ALB))
            try:
                leg = json.loads(out).get("legami_in_ingresso", 0)
            except Exception:
                leg = -1
            inf("M3: incoming links to the sink = %s" % leg)
            if leg <= 0:
                ko("the tone no longer plays: I do NOT judge this profile")
                esiti.append({"profilo": nome, "passa": None,
                              "esito": "NIENTE DA GIUDICARE — the tone was silent"})
                continue

            giri = {}
            for regola in REGOLE:
                n = giro(nome, regola, a.secondi)
                giri[regola] = n
                if n.get("esito"):
                    ko("%s: %s" % (regola, n["esito"]))
                else:
                    print("    %s" % riga_numeri(n))
            v, u = giri["vecchia"], giri["nuova"]
            if v.get("esito") or u.get("esito"):
                esiti.append({"profilo": nome, "passa": None, "giri": giri,
                              "esito": "a run produced no numbers"})
                continue

            # ⭐ AND HERE THE EXPECTATIONS STOP BEING PROSE.
            verdetti = []
            for pred in predicati:
                passa, perche = pred(v, u)
                verdetti.append({"passa": passa, "perche": perche})
                print("    %s %s" % ("OK " if passa else ("⚠  " if passa is None
                                                          else "⛔ NO"), perche))
            rossi = [x for x in verdetti if x["passa"] is False]
            muti = [x for x in verdetti if x["passa"] is None]
            passa = None if (muti and not rossi) else (not rossi)
            esiti.append({"profilo": nome, "regole": regole, "testo": testo,
                          "giri": giri, "verdetti": verdetti, "passa": passa})
    finally:
        log("⛔ THE NETWORK IS PUT BACK AS IT WAS, and CHECKED")
        try:
            RETE.tono_spegni()
        except Exception as e:
            ko("the tone did not stop: %s" % e)
        try:
            RETE.guardiano_disarma()
            RETE.rimetti()
        except Exception as e:
            ko("⛔ the network was NOT put back: %s" % e)
        LUCCHETTO.molla(CHI)

    with open(os.path.join(FUORI, "b77-esiti.json"), "w") as f:
        json.dump(esiti, f, ensure_ascii=False, indent=1)

    # ═══ THE PAIRED TABLE ══════════════════════════════════════════════════
    log("THE PAIRED TABLE — profile × rule")
    print("    %-13s %-8s %8s %7s %7s %8s %8s %7s %6s %7s %6s %6s %7s"
          % ("profile", "rule", "PURITY", "tone", "cov.", "sul_filo",
             "deliv.", "vecchi", "tard", "fuori", "rec", "dop", "srv:fal"))
    for e in esiti:
        for regola in REGOLE:
            n = (e.get("giri") or {}).get(regola)
            if not n or n.get("esito"):
                print("    %-13s %-8s   (no numbers)" % (e["profilo"], regola))
                continue
            def q(x, f="%s"):
                return "-" if x is None else (f % x)
            print("    %-13s %-8s %8s %7s %7s %8s %8s %7s %6s %7s %6s %6s %7s"
                  % (e["profilo"], regola, q(n.get("purezza"), "%.4f"),
                     q(n.get("purezza_tono"), "%.3f"), q(n.get("copertura"), "%.4f"),
                     q(n.get("sul_filo")), q(n.get("consegnati")),
                     q(n.get("vecchi")), q(n.get("tardivi")), q(n.get("fuori")),
                     q(n.get("rec")), q(n.get("dop")), q(n.get("dgram_falsi"))))

    rossi = [e for e in esiti if e.get("passa") is False]
    muti = [e for e in esiti if e.get("passa") is None]
    log("THE VERDICT — %d profiles, %d red, %d not judged"
        % (len(esiti), len(rossi), len(muti)))
    for e in rossi:
        for x in e.get("verdetti", []):
            if x["passa"] is False:
                ko("%s: %s" % (e["profilo"], x["perche"]))
    for e in muti:
        inf("⚠ %s: %s" % (e["profilo"], e.get("esito") or "an expectation refused to judge"))
    inf("the outcomes in full: %s" % os.path.join(FUORI, "b77-esiti.json"))
    if rossi:
        return 1
    if muti:
        return 2      # ⚠ «I did not measure» is an outcome of ITS OWN, not a green
    ok("⭐ all the profiles did what was written beforehand")
    return 0


def principale():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("passo", nargs="?", default="misura",
                   choices=["misura", "terreno", "rimetti", "stato"])
    p.add_argument("--certifica", action="store_true",
                   help="⭐ the self-test of the predicates, with manufactured numbers: "
                        "it shows they can give RED")
    p.add_argument("--secondi", type=int, default=25,
                   help="how long EACH run lasts (and there are two runs per profile)")
    p.add_argument("--solo", default="", help="one profile only, by name")
    p.add_argument("--affitto", type=int, default=900,
                   help="⛔ how long I hold the netem lock: short, there are "
                        "other agents queued")
    p.add_argument("--attesa", type=int, default=2400,
                   help="how many seconds I wait for my turn")
    a = p.parse_args()
    if a.certifica:
        return certifica()
    if a.passo == "terreno":
        return 0 if terreno_controlla() else 2
    if a.passo in ("rimetti", "stato"):
        log("THE TEST MACHINE'S NETWORK")

        return 0 if RETE.rimetti() else 2
    return misura(a)


if __name__ == "__main__":
    sys.exit(principale())
