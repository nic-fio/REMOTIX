#!/usr/bin/env python3
"""02-filo-fotogramma.py — ⛔ F2.4: the frame judged against `RCP.md`, byte by byte.

    python3 02-filo-fotogramma.py --elenco              the predictions, without measuring
    python3 02-filo-fotogramma.py                       the whole round
    python3 02-filo-fotogramma.py --solo numero-zero    a single case
    python3 02-filo-fotogramma.py --guasto G1           with a fault injected into the JUDGE
    python3 02-filo-fotogramma.py --certifica           healthy -> G1 -> G2 -> G3 -> healed
    python3 02-filo-fotogramma.py --uscita 02-filo-esiti.jsonl

⚠ It runs ANYWHERE: it does not touch the network, does not want aioquic, does not want a server.
  ⛔ And this is NOT a convenience: it is the reason it exists today.  The
  phase 2 product is not there — `grep -c '0x0301\\|0x0302' src/*` gives **0**
  on all three files, `[M]` 12 Aug 2026 — and `PIANO.md` §0.4 moment 1
  wants the bench **before** the product.  A bench that required the product
  in order to exist would be written after, that is it would be written **knowing what the
  product does**, which is precisely the silent defect `RCP.md` §0
  exists against.

===========================================================================
⛔ WHY THIS BENCH EXISTS, AND WHICH WRONG MEASUREMENT IT PREVENTS

Phase 2 delivers **one frame**.  The natural way of testing it is:
switch on the server, open the page, see whether the desktop appears.

  ⛔ *That test is green even if server and page understood `RCP.md`
     in the same wrong way.*

It is `PIANO.md` §0.4: in v1 the referee was **mstsc**, and when we misunderstood
the specification someone else's client protested for free.  Now client and server
are ours, ⛔ **and the pixel on the screen does not tell a protocol understood
from a protocol understood the same way by both**.  An `istante` read little-endian by
both sides paints a perfect desktop.

This program is the **third reader** of the video chapter: it judges
a frame reading **only** `RCP.md` §2.5, §5.1, §5.2, §6.0 and §6.2 —
⛔ and whoever grows it **does not look at `src/rcp.c` or `src/pagina.html`**.  Whoever
wrote it counted the occurrences of `0x0301` in `src/` to know that they are
zero, and did not open those files.

===========================================================================
⛔ THE FOUR THINGS EVERY CASE CHECKS, AND THE FOURTH IS NEW

  1. ⛔ **the right outcome**, and the outcomes are **THREE**, not two.  `RCP.md` asks
     the client for three different behaviours and confusing them is form **E8**:

       ACCETTATO           it is handed to the decoder
       SCARTATO            ⛔ it is THROWN AWAY and NOT handed over — and treated as a
                           gap (§6.2, §5.2).  The session **stays alive**
       ERRORE_PROTOCOLLO   the connection drops, with the reason (§3)

     ⚠ A two-outcome bench passes `SCARTATO` off as `ERRORE_PROTOCOLLO`:
     that is it promotes to a session drop a frame abandoned by the
     server **on purpose**, which is the normal case of §5.1;

  2. ⛔ **which byte**, not only that it is red.  `FASI.md` §01-filo-nudo B4: a
     referee that says the right thing accusing the wrong byte sends the
     diagnosis to read the wrong message.  Every verdict carries the
     offset inside the header and the line of `RCP.md` that backs it;

  3. ⛔ **the rule cited**, and it is compared.  A red with the wrong
     section next to it is green for whoever looks at the colour (finding R7.12 of
     `FASI.md` §01-filo-nudo);

  4. ⭐⛔ **AND THE FOURTH OUTCOME: `AMBIGUO`.**

     `FASI.md` §01-filo-nudo §«The twelve points where `RCP.md` allows two
     readings» is the most precious outcome of B9, and no bench produced it: they
     were found by a program written on purpose, **afterwards**.  Here the fourth outcome is
     inside the bench that runs every day.

     ⛔ An `AMBIGUO` case **is not a case to fix in the product**: it is a
     place where `RCP.md` does not decide, and two conforming implementations
     diverge.  ⚠ It does not make the round fail — nobody made a mistake — ⛔ **but it
     is printed at the end, counted, and ends up in the log**, because a silenced
     ambiguity is indistinguishable from a rule.

===========================================================================
⭐⛔ AND ON 12 AUG 2026 THE FOUR AMBIGUITIES WERE CLOSED — this file
    WAS REWRITTEN ACCORDINGLY

*On 12 Aug 2026 the coordinator applied to `RCP.md` the seven lines that
this bench proposed (§2.5, §5.2, §6.2, §11.1).  ⛔ From that moment the four
`AMBIGUO` this file printed are **normative rules**, and a judge that
went on calling them ambiguities would be judging yesterday's document.*

  | line that entered `RCP.md` | where | here it was | here it is now |
  |---|---|---|---|
  | **P2** `numero` starts from 1, 0 is reserved | §6.2 | `AMBIGUO` | `ERRORE_PROTOCOLLO` |
  | **P6** the first frame after `SESSIONE` MUST be a keyframe | §5.2 | `AMBIGUO` | `ERRORE_PROTOCOLLO` |
  | **P5** `largh.`/`altezza` MUST match the granted canvas | §6.2 | `AMBIGUO` | `ERRORE_PROTOCOLLO` |
  | **P3** a `0x03` on the control channel | §2.5 | `AMBIGUO` | `ERRORE_PROTOCOLLO` |
  | **P1** no video stream before `SESSIONE` | §2.5 | derived from §3+§1 | **cited**: §2.5 |
  | **P4** FIN before the 28 bytes | §6.2 | derived from §3 | **cited**: §6.2 |

⛔ **And every line has TWO cases, not one: the one that violates it and the one that
   respects it.**  A referee that knows a rule and does not have the input that makes it
   trigger does not enforce it, and the green it gives is the one that gives confidence
   (`CODER.md` §4.6).  ⚠ And the case that **respects** it is not an extra: without it,
   a rule written too broadly — «every size other than 1920x1080 is
   `ERRORE_PROTOCOLLO`» instead of «other than the **granted** canvas» —
   would stay green on the whole bench.  The `REGOLE_NUOVE` table keeps the two
   names next to the tag, and the round **counts** how many rules have both:
   a count written by hand would be the number nobody recomputes.

⭐ **And the `AMBIGUO` outcome stays in the code, with zero cases requiring it** —
   ⛔ and it is **declared at the end of every round** instead of letting it be discovered:
   «no ambiguity printed» and «the branch that prints them is exercised by no
   case» are two different facts, and it is form **E8** turned against the
   bench itself.  It stays for two reasons: `RCP.md` will go back to allowing two
   readings — it allowed **twelve** in phase 1 alone
   (`FASI.md` §01-filo-nudo B9) — and fault **G5**, *«the judge of the morning
   of 12 Aug»*, makes the judge produce `AMBIGUO` at every certification.
   ⚠ What G5 exercises is the **judge**'s branch, not the one that prints them:
   with the four cases requiring `ERRORE_PROTOCOLLO`, an `AMBIGUO` is a
   **red**, and that is exactly what it must be.

===========================================================================
⛔⛔ AND ON THE EVENING OF 12 AUG 2026 THE P5 CURE OPENED ANOTHER ONE — **D14**

*`RCP.md` §6.2 was corrected twice the same day.  The second cure —
«the size of the frame must match the **canvas in force**» — made **the
canvas change midway through the session legal** (§7.1, `ADATTA_TELA` -> `TELA(ADATTATA)`).
⛔ And every time something new is made legal, what that new
thing carries with it opens up.*

  ⛔ §6.2 makes whoever receives a size other than the canvas in force close
     with `ERRORE_PROTOCOLLO`, **but §6.2 also says** — seven lines further down —
     that *«streams are independent, so frames can arrive
     out of order»*.  ⇒ After a `TELA(ADATTATA)` the frames **already in flight**
     **legitimately** carry the previous size, and a client conforming to
     §6.2 **kills a healthy session**.

  ⚠ It is the same form as **P5**, the line that on the morning of 12 Aug
    stayed two hours in the document written wrong: *a server conforming to
    §7.1 killed by a client conforming to §6.2*.  ⛔ But it is not the same
    family: P5 was a **double reading** — two conforming implementations
    produced different bytes.  Here two conforming and careful implementations
    produce **the same byte**, and that byte is the closing of the session.
    ⇒ It is an **internal contradiction**: a rule that punishes a case the
    document itself makes legal — the form already named twice in
    `RCP.md` (§5.5, the hidden cursor of finding R11.11; §9, the seven words
    of §2.2 found by B5).

  ⭐ **And the cure already exists in the document, for another field**: §7.1 protects
     the very same scene for the **input coordinates** with a **one-second
     grace** — *«it is the only moment in which the two sides
     legitimately have two different truths»*, third declared exception of §3.
     For frames that grace is not there.  Proposal **P8** is that
     line, written for the direction where it is missing: the good road already existed
     in the house.

⭐⛔ **AND THE SAME EVENING THE COORDINATOR APPLIED THE TWO CURES: FROM HERE ON
    THIS JUDGE ENFORCES THEM, AND NO LONGER SAYS `AMBIGUO` IN THAT
    SCENE.**  The lines that went in are two, and they are **P8** and **P9**:

     **P8** §6.2 at the end + §3 exception **6** — after a `TELA(ADATTATA)` the
            client **MUST** accept for **one second** the frames that
            carry the **previous** size, painting them rescaled and
            **writing it in the log**; outside the second they are
            `ERRORE_PROTOCOLLO`, and so is **at once** a size that is neither
            the one in force nor the previous one;
     **P9** §5.2 — the first frame at the **new size** after a
            `TELA(ADATTATA)` **MUST** be a **real** keyframe (with its
            parameter sets), and the client **MUST NOT** hand to the
            decoder a frame whose size is not the one the
            decoder is configured for (defect **D13**, `[M]`).

⛔ **And the scene that kills is not enough: P8 needs THREE**, because a
   grace written too broadly is as much a defect as a rule written too
   narrowly — and that is exactly how P5 ended up wrong the first time:

     `p8-in-volo-dopo-adatta-tela`      a size in force since the queue
                                        started draining ->
                                        **ACCETTATO**, and the round checks that
                                        the tolerance is **declared** (§3,
                                        last line)
     `p13-vecchia-dopo-la-chiave-nuova` the same size, but **the keyframe at the
                                        new size has arrived** ->
                                        `ERRORE_PROTOCOLLO`.  ⛔ The tolerance
                                        is not a permanent permit
     `p8-misura-di-nessuna-tela`        a size that in that window was
                                        **never** in force ->
                                        `ERRORE_PROTOCOLLO` **at once**

⭐ **AND THIS BENCH HAS NO CLOCK — AND SINCE THE P13 CURE IT NO LONGER NEEDS
   ONE.**  The tolerance ended «after one second», which is a fact that is not on the
   wire: the case had to **declare** it, and a referee reading a
   recording could not see it at all.  ⇒ Now it ends at the **first
   keyframe at the new size**, which is a **frame** — and frames can be
   seen.  ⚠ Time stays declarable (`secondo_passato`) and no longer decides
   anything: only fault **G10** puts it back in charge, and it is the case
   `p13-linea-lenta` that proves the cure is there.

===========================================================================
⭐⛔⛔ AND THE TWO CURES OF THAT EVENING, READ WITH A HOSTILE EYE, DID NOT HOLD
     IN TWO POINTS — **P10** and **P11**, found BY APPLYING THEM, and ENTERED IN THE
     DOCUMENT IN THE NEXT ROUND

*What happened this morning happened again, when two of the seven
lines turned out to be wrong: what found them was not a rereading, it was
**whoever had to enforce them**.  ⛔ Neither of the two was a defect of the
product: they were two points where `RCP.md`, a few hours after the cure, did not decide
— and the coordinator closed them in the following round.*

  ⭐ **P10 — §5.2, the line before the client's one**: *«the client
     reconfigures the decoder on the first **KEYFRAME** at the new size,
     not on the `TELA`»*, and the client's line now says *«nor the one tolerated
     by §6.2»*.  ⛔ Before, the two cures contradicted each other on the **same
     frame**: §6.2 «accept it and paint it», §5.2 «throw it away», and the document
     said nowhere **when** to reconfigure — two conforming
     readings that diverged on the wire.  ⇒ Here the pair of cases is
     `p10-decodificatore-al-tela` (the client out of place: it is ACCEPTED anyway,
     ⛔ **with the finding**) and `p10-decodificatore-alla-chiave` (the client where it
     should be: it is accepted, **without** finding).

  ⭐ **P11 — §6.2**: *«a canvas that was in force within the **second
     just passed**»* instead of *«the previous canvas»*, and
     `ERRORE_PROTOCOLLO` at once for *«a size that was never in force
     in that window»*.  ⛔ In the singular the line killed a healthy session
     **one step further on**: `ADATTA_TELA` is sent by the user dragging a
     window, and dragging sends two in one second — 1920x1080 ->
     `TELA(1600,900)` -> `TELA(1280,720)` — and the keyframe opened before everything
     (the biggest, the slowest, the one §5.2 forbids abandoning)
     carried a size that was neither the one in force nor the previous one.
     ⇒ Pair: `p11-due-tele-nella-finestra` and `p11-misura-mai-in-vigore`.

===========================================================================
⛔⛔ AND AT THE THIRD REREADING TWO ARE LEFT, DECLARED AND NOT CURED — **P12** and
    **P13**.  Neither is touched from here: `RCP.md` belongs to the coordinator.

  ⛔ **P12 — §3 exception 6 stayed in the SINGULAR while §6.2 moved to the
     window.**  §6.2 now says *«a canvas that was in force within the
     second just passed»*; line 6 of the §3 table still says *«the
     frames carrying the **previous** size»*.  ⛔ And §3 is not a
     summary: it declares *«the exceptions are six, and they are all here.  Outside
     this list none are invented»*, that is it **forbids** the broader
     tolerance §6.2 commands.
     ⇒ Concrete case, and it is a case this bench already carries:
     `p11-due-tele-nella-finestra`.  A client written reading §3 **closes**;
     one written reading §6.2 **accepts and paints**.  Two conforming
     implementations, two different bytes, and one of the two kills a healthy session — the
     **same** scene P11 has just closed, surviving in the table that
     declares itself complete.  ⚠ Here the bench follows §6.2, which is the
     normative section of the field, and **declares** it instead of choosing it silently.

  ⛔ **P13 — the grace second is a time, and what must drain is a
     QUEUE.**  `[?]` not measured.  §6.2 tolerates the old size for **one
     second** from the `TELA`; but the frames in flight are QUIC streams already
     open, and how long they take to arrive **depends on bandwidth**, not
     on the clock.  ⇒ Scene: canvas 1920x1080, the user drags, `TELA(ADATTATA,
     1280, 720)`; the 1920x1080 **keyframe** opened an instant before weighs a few
     MiB — §6.2 allows up to **16** — and the line is bad (the minimum of
     `CODER.md` §1 is 480p25: bad lines are **inside** the model).  The
     stream takes **more than one second** to arrive, and the client closes with
     `ERRORE_PROTOCOLLO` a frame the server sent when it was
     still legal, and which §5.2 forbade it to abandon.
     ⛔ And here it is not only a healthy session that drops: it is invariant **I1** —
     *«never to cut off», «an ugly session is worth more than a closed
     session»* — broken **because the line is slow**, which is exactly the
     condition I1 exists to protect.  ⚠ The cure is not lengthening the
     second (a bigger number moves the defect, it does not remove it): the
     client knows when the queue has drained, because §5.2 guarantees it a
     **keyframe at the new size**, and from that one on the old size has no
     more excuses.  ⛔ But the line belongs to the coordinator, and this bench has no
     clock: here it is declared.

⚠ **And a `[?]` that P9 opens and does NOT close — declared, not closed for
  symmetry**: §6.2 says frames arrive **out of order**, so a
  delta at the new size can arrive **before** the keyframe the server
  sent first.  §5.2 constrains whoever **sends**, and this judge — as
  for P6 since this morning — applies it to whoever **receives**: it is the strict reading.
  ⚠ And since the P10 line the document now carries a **candidate** answer
  for the other reading — *«the client … does not hand to the decoder a
  frame whose size is not the one it is configured for … it throws it away and
  treats it as a gap»*, which would give `SCARTATO` instead of the closing — ⛔ but
  **candidate is not decided**, and the two readings still produce different bytes
  (`RICHIEDI_CHIAVE` against `CONGEDO`).  ⛔ Closing it needs a **measurement**
  — how often a delta overtakes its keyframe on the real wire — and nobody
  has it: it stays `[?]`.

===========================================================================
⭐⛔⛔ AND ON 13 AUG 2026 THE HOSTILE REREADING FOUND ONE **INSIDE §6.2
     AGAINST ITSELF** — **P21**, the seventh of the family

*P8 -> P11 -> P13 -> P14 -> P19 -> P20 -> **P21**.  ⛔ Six lines of the same
family by now live together in the same section, and this one came out
by lining them up: **two paragraphs of §6.2, eight lines apart,
command the opposite on the same frame.**  ⚠ It is not a defect of the
product: it is the document.*

  ⛔ The paragraph of **P19**: a frame at the **new** size can arrive
     **before** the `TELA` that grants it, and the client *«MUST NOT close:
     it holds back»*.
  ⛔ The tolerance paragraph (**P11** + **P13**), eight lines below: a
     size *«that was never in force in that window»* is
     `ERRORE_PROTOCOLLO` **at once**.
  ⇒ Scene: `SESSIONE` 1920x1080 -> `TELA(ADATTATA, 1600, 900)`; the client sends
    `ADATTA_TELA(1280, 720)` and the 1280x720 frame arrives **before** the
    answer.  Two conforming implementations, **two different bytes**.

⭐ **The cure, and the real quantity**: hold back while there is an
   `ADATTA_TELA` that **the client itself sent** and that no `TELA` has
   answered — local, monotonic, independent of delivery, like `ATTACCA` for
   P20 and like `numero` for P14.  §7.1 guarantees that the answer arrives (*«to
   every `ADATTA_TELA` the server MUST answer with a `TELA`, successful or
   not»*), and §4.2 that the channel is ordered ⇒ the n-th `TELA` answers
   the n-th request.  ⛔ And it closes the `[?]` of P19 — *«until when
   it holds back»*, which in the product was **eight frames**: an observable bottom,
   but a substitute nonetheless.

⛔⛔ **And the first draft of the cure was still a substitute**, rejected by the
    case and not by a rereading: it said *«hold back the SIZE the client
    named»*, and §4.5 says **the granted canvas can differ from
    the requested one** — on KWin < 6.8 it is the normal road (`SPECIFICHE.md`
    §6.3).  ⇒ The client asking for 1366x768 and receiving the 1280x720 the
    compositor is about to grant would have closed a healthy session **one step
    further on**: the eighth draft, avoided.  Case
    `p21-concessa-diversa-da-chiesta`, fault **G14**.

⇒ Three cases, as for P8, because a cure can be wrong in **two** directions:
  `p21-nominata-e-in-volo` (shows it) · `p21-concessa-diversa-da-chiesta`
  (prevents writing it too narrowly, **G14**) · `p11-misura-mai-in-vigore`
  (prevents writing it too broadly, **G15**).

===========================================================================
⛔ WHAT THIS BENCH DOES **NOT** TEST, AND IT MUST BE SAID

| | why it is not here |
|---|---|
| that the server really **sends** a frame | the product does not exist (§0 of this file).  `02-filo-cliente.py` tests it on **7514**, when there is one |
| that the decoded **pixels** are the captured ones | it is sub-phase **F2.6**, and it is not a protocol measurement |
| that the **decoder** accepts the bytes | it is **F2.5**: `VideoDecoder` and the canvas |
| that the keyframe at the new size is a **real** keyframe — §5.2 wants the VPS/SPS/PPS in front of the IDR | ⛔ this judge **does not keep the data** of the frame, so of P9 it sees the half in the header (`tipo = 0x0301`) and not the one in the payload.  `02-codifica-nal.py` and `02-pagina-tela-*` measure it |
| the **credit** of the streams beyond the first 256 frames (§2.3) | phase 2 delivers **one** still frame; it is **phase 3** |
| the real **abandonment** with `RESET_STREAM` on the wire | here a reset stream is judged, not provoked.  The bench that provokes it belongs to **phase 3** (`RCP.md` §11, «the abandoned frame») |

⚠ Writing it here is not modesty: a bench that keeps silent about what it does not cover is
read as if it covered everything, and that is how a green becomes an acquittal.
"""
import argparse
import json
import os
import struct
import sys
import time

# ---------------------------------------------------------------------------
# ⛔ THE NUMBERS OF `RCP.md`, IN ONE PLACE AND WITH THE SECTION NEXT TO THEM.
#
#    A number copied in three places is a number that sooner or later diverges in
#    one of the three, and nobody notices until it produces a distant
#    symptom.  ⚠ `INTESTAZIONE` in particular is the number `RCP.md` §6.2
#    already had to correct once, on 9 Aug 2026: the drawing gave
#    `… 24 │ 32`, that is four padding bytes never declared.
INTESTAZIONE = 28                 # §6.2, «exactly 28 bytes, no padding»
TETTO_FOTOGRAMMA = 16 * 1024 * 1024   # §6.2, «MUST NOT produce a frame
                                      # longer than 16 MiB»
CHIAVE, DELTA = 0x0301, 0x0302    # §5.2, §6.2
CODEC = {1: "hevc", 2: "av1"}     # §6.2
CANALE_VIDEO = 0x03               # §2.5
CANALI = {0x00: "controllo", 0x01: "input", 0x02: "appunti",
          0x03: "video", 0x04: "audio"}   # §2.5

# ⛔ The outcomes, and they are FOUR.  See point 1 and point 4 of the header.
ACCETTATO = "ACCETTATO"
SCARTATO = "SCARTATO"
ERRORE_PROTOCOLLO = "ERRORE_PROTOCOLLO"
AMBIGUO = "AMBIGUO"


class Verdetto:
    """What was decided, with the line of `RCP.md` that backs it.

    ⛔ `scostamento` is inside the frame header, not inside the
       file: there is no file here.  Whoever reads a recording uses
       `02-filo-validatore.py`, which has the two offsets of §11.1.
    """

    def __init__(self, esito, regola="", dice="", scostamento=None,
                 propone="", tollerato="", rilievo=None):
        self.esito = esito
        self.regola = regola
        self.dice = dice
        self.scostamento = scostamento
        self.propone = propone      # ⛔ only for AMBIGUO: the cure, not the complaint
        # ⛔ §3, last line: *«every tolerance must be written in the log.  A
        #    silent tolerance is indistinguishable from a defect»*.  ⇒ A
        #    frame accepted **through an exception** does not look the same
        #    as one accepted because it was in order, and the round checks it.
        self.tollerato = tollerato
        # ⛔ P10 — a finding on the **client's state**, which is not a judgement
        #    on the wire and does not change the outcome.  ⚠ Keeping them apart is not tidiness:
        #    a finding promoted to outcome would drop a session in which the
        #    server got nothing wrong, and it is the form this chapter
        #    has already paid for three times today.
        self.rilievo = rilievo

    def __str__(self):
        p = [self.esito]
        if self.regola:
            p.append(f"[{self.regola}]")
        if self.dice:
            p.append(self.dice)
        if self.scostamento is not None:
            p.append(f"(byte {self.scostamento} of the header)")
        if self.rilievo:
            p.append(f"— FINDING ON THE CLIENT: {self.rilievo}")
        return " ".join(p)

    def come_dizionario(self):
        return {"esito": self.esito, "regola": self.regola, "dice": self.dice,
                "scostamento": self.scostamento, "tollerato": self.tollerato,
                "rilievo": self.rilievo}


class Contesto:
    """What the client already knows when a frame arrives.

    ⛔ It is not a convenience: **half of the rules of §6.2 apply only with
       this at hand**.  `codec` «MUST be the one negotiated in §4.3»;
       `largh.`/`altezza` are compared with the **granted canvas** of §4.5; the
       `numero` is compared with the last one delivered.  A judge without
       context can only say whether the 28 bytes are well formed, which is
       a third of the rules and not the most precious one.
    """

    def __init__(self, tela=(1920, 1080), codec_negoziato=1,
                 sessione_aperta=True):
        # ⛔ THE CANVAS IS THE ONE **IN FORCE**, AND IT CAN CHANGE MIDWAY THROUGH THE SESSION.
        #
        #    §6.2, corrected on 12 Aug 2026: *«they MUST match the canvas in
        #    force — the one granted in `SESSIONE` (§4.5), **or** the last
        #    one granted by `TELA` if meanwhile it has been adapted (§7.1)»*.
        #    ⚠ The previous line said «the canvas granted in `SESSIONE`», and
        #      **killed a healthy session**: after an `ADATTA_TELA` the server
        #      captures at the new size, and a client still comparing
        #      with `SESSIONE` would close — the scene §7.1 protects with
        #      its exception 4.  Found by propagating the rule to these referees.
        self.tela_larghezza, self.tela_altezza = tela
        # ⛔ And it keeps WHERE it comes from, because it is the half the verdict must
        #    be able to say: «other than the canvas of `SESSIONE`» and «other than the
        #    canvas in force» send you looking in two different places.
        self.tela_da = "SESSIONE (§4.5)"
        # ⛔⭐ AND THE TWO TRUTHS IN FLIGHT — defect **D14**, proposal **P8**.
        #
        #    §7.1 lets the canvas change midway through the session; §6.2 says that «the
        #    streams are independent, so frames can arrive
        #    out of order».  ⇒ Right after a `TELA(ADATTATA)` the client has in
        #    flight frames that **legitimately** carry the previous size,
        #    and §6.2 to the letter makes it close the session.
        #    ⚠ `tela_precedente` is `None` as long as nothing has ever changed:
        #      `None` is «there is no previous one», and it is NOT a size.
        self.tela_precedente = None
        # ⛔⛔ AND THE CANVASES THAT WERE IN FORCE **SINCE THE QUEUE
        #    STARTED DRAINING**, not a single one.  §6.2 named «the
        #    **previous** canvas» in the singular, ⚠ but `ADATTA_TELA` is sent by the user
        #    dragging a window, and dragging sends several:
        #    the canvas can change twice while a frame is still in
        #    flight (finding **P11**, cured on 12 Aug 2026).
        self.tele_recenti = []
        # ⛔⭐ D13, §5.2: after a `TELA(ADATTATA)` the first frame at the
        #    NEW size MUST be a real keyframe.  ⚠ `True` by default means
        #    «there is no pending canvas change»: at the start of the session
        #    the line in command is P6's, not this one.
        #
        # ⛔⭐⭐ AND SINCE THE **P13** CURE THIS FIELD DOES **TWO** JOBS, and it is
        #    the point of the whole cure: it is also **the end of the tolerance**.
        #    §6.2: *«the tolerance does not end by the clock: it ends when the
        #    first keyframe at the new size arrives»*.  ⇒ The queue is draining
        #    as long as this is `False`, and there is no second to measure —
        #    ⭐ **the end is an observable fact on the wire**, and that is why the
        #    bench no longer needs a clock it never had.
        self.chiave_alla_tela_nuova = True
        # ⛔ AND THE SECOND STAYS HERE, DECLARED AND **INERT** — it no longer decides
        #    anything.  ⚠ It is not a leftover: it is the lever of fault **G10**, «the
        #    judge with the clock», that is the line as it was two hours before.  A
        #    field that does not decide and that no fault exercises should be removed;
        #    this one exercises it, and proves that the P13 cure is **tested** and
        #    not told.
        self.secondo_passato = False
        # ⛔⛔ AND WHICH SIZE THE DECODER IS CONFIGURED AT — `None` = «not
        #    declared», and it is NOT «at the canvas in force».
        #
        #    §5.2 (evening of 12 Aug) says the client **MUST NOT** hand
        #    to the decoder a frame whose size is not the one
        #    the decoder is configured for; §6.2 (the same evening) says it
        #    **MUST** accept and **paint** the frames in flight at the previous
        #    size.  ⇒ The two lines meet on the same frame,
        #    and whoever reads them must know **when the client reconfigures**: at the
        #    `TELA`, or at the first keyframe at the new size.  ⛔ `RCP.md` does not
        #    say it anywhere — see proposal **P10**.
        self.decodificatore_a = None
        self.codec_negoziato = codec_negoziato
        # ⛔⛔ AND THESE TWO ARE NOT THE SAME THING — proposal **P20**.
        #
        #    `sessione_aperta` says *«I have already seen the bytes of `SESSIONE`»*,
        #    and ⛔ **it is a substitute quantity**: the control channel and the
        #    frame stream are two independent QUIC streams, and
        #    RFC 9000 does not order their delivery — §6.2 writes it twice
        #    (P14, P19).  ⇒ It is enough for the packet carrying
        #    `SESSIONE` to be lost for this field to be `False` while the server has
        #    done **exactly** what §2.5 and §5.2 require of it.
        #
        # ⭐ `attacca_spedito` is the **real** quantity, and it is what `numero`
        #    was for P14: a fact that is **local, monotonic and independent
        #    of the delivery order**.  §4.5 makes `SESSIONE` the answer to
        #    `ATTACCA` ⇒ a server that has not received `ATTACCA` **cannot**
        #    have sent `SESSIONE`, and the client knows with no margin of error whether
        #    it sent it, because it sent it itself.
        #    ⚠ And it covers the invariant the line defends: the client that has
        #      sent `ATTACCA` has already gone through `AMMESSO` (§1), that is **through the
        #      validator** — which is all I3 asks.
        self.sessione_aperta = sessione_aperta
        self.attacca_spedito = True
        # ⛔ `None` is «none», and it is NOT zero: §6.0 forbids implicit sentinel
        #    values, and zero is a `numero` the document does not exclude —
        #    see the case `numero-zero`, which is ambiguity A1.
        self.ultimo_consegnato = None
        self.chiave_consegnata = False
        self.chiedi_chiave = False    # §5.2: the client MUST ask for it on a gap
        # ⛔ «Does this reader apply exception 6 of §3?» — and it is NOT «the
        #    second has not passed yet»: the second is no longer there (P13).
        self.grazia_concessa = True
        # ⛔⛔⭐ AND THE CANVAS CHANGE REQUESTS THE CLIENT SENT AND THAT
        #     NO `TELA` HAS ANSWERED YET — proposal **P21**, 13 Aug 2026.
        #
        #     ⚠ **It is not a list of sizes: it is a count of requests in flight**,
        #       and the difference is the whole cure.  The real quantity of the phenomenon
        #       *«this frame belongs to a world I asked for and that
        #       has not been answered yet»* is **the message sent**, not
        #       the numbers it carries — exactly as for **P20** it is `ATTACCA` and
        #       not the canvas `ATTACCA` asks for.  ⛔ The sizes are kept for the
        #       **log** and for fault **G14**, never to decide: §4.5 says
        #       that *«the granted canvas can differ from the requested one»*, and
        #       a discriminant written on the numbers would close a healthy session
        #       the day the compositor grants a nearby size instead
        #       of the requested one (`SPECIFICHE.md` §6.3 and §6.4).
        #     ⭐ Local, monotonic, independent of delivery: the client knows
        #       how many `ADATTA_TELA` it sent because it sent them itself, and knows
        #       that to each a `TELA` will arrive because §7.1 requires it.
        #     ⛔ Empty by default: whoever declares nothing has yesterday's judge, and
        #       no reader importing this file (`01-b4-validatore.py`,
        #       `02-filo-validatore.py`) changes verdict without knowing — I6.
        self.adatta_in_volo = []

    def adatta_spedito(self, lar, alt):
        """⭐⛔ **The client has sent an `ADATTA_TELA(lar, alt)`** — §7.1, and the
        answer has not arrived yet.

        ⛔ It is a fact **of the client**, not of the wire the client receives: it sits here
           for the same reason `attacca_spedito` does (P20).  A
           referee reading a **recording** sees it anyway, because
           §11.1 records both directions.
        """
        self.adatta_in_volo.append((lar, alt))

    def risponde_il_tela(self):
        """⛔ A `TELA` has arrived: **one** request in flight has been answered.

        ⭐ Which one?  **The oldest**, and it is not a choice of convenience: the control
           channel is **a single one, reliable and ordered** (§4.2, §2.5) and
           §7.1 requires **one** `TELA` for **every** `ADATTA_TELA` ⇒ the n-th `TELA`
           answers the n-th `ADATTA_TELA`.  ⚠ Without this line the cure of
           P21 would not be written at all in the scene P11 has already paid for —
           whoever drags a window sends **two**.

        ⚠ It holds for both outcomes: a `TELA(RIFIUTATA)` answers as much as a
          `TELA(ADATTATA)` (§7.1, *«successful or not»*).
        """
        if self.adatta_in_volo:
            self.adatta_in_volo.pop(0)

    def adatta_tela(self, lar, alt, precedente=None, grazia=True):
        """§7.1 — a `TELA(ADATTATA, lar, alt)` has arrived.

        ⛔ From this moment the canvas **in force** is another one, and §6.2 ties to it
           `largh.`/`altezza` of every following frame.  ⚠ Whoever calls
           this method does so because they **saw** the message on the wire: the
           frame judge cannot know it on its own, and in fact the canvas
           is always declared to it from outside.

        ⛔⭐ And **the previous one** is kept, because it is half of defect D14:
           the frames already in flight carry it **legitimately**, and without
           having it at hand the client cannot tell «an old size
           that is still arriving» from «a size that has never belonged to
           any canvas» — that is it cannot do what §7.1 already does for the
           input coordinates.  ⚠ `precedente` can be passed from outside: whoever
           reads a **recording** rebuilds the canvases by scanning the file,
           and reuses the context from one stream to the next.

        ⛔⛔ **AND THE DRAINING QUEUE NO LONGER HAS A TIME SWITCH** —
           **P13** cure, 12 Aug 2026.  §6.2: *«the tolerance does not end
           by the clock: it ends when the first keyframe at the new size
           arrives»*.  ⇒ Here no second is opened: a **debt** is opened
           (`chiave_alla_tela_nuova = False`), and what closes it is a frame,
           not a stopwatch.  ⭐ Which makes judgeable from a `.rcpreg` a
           thing that before was not.

        ⛔⛔ **AND `grazia` IS ON BY DEFAULT SINCE THE EVENING OF 12 AUG 2026 —
           changed, and the choice must be declared.**

           Until that evening it was **off**, and rightly so: the grace was
           proposal **P8**, not a line of the document, and switching on a
           proposal by default would have silently changed the verdict of
           `01-b4-validatore.py`, which imports it and knows nothing of D14 — that is
           invariant **I6** applied to a bench.

           ⭐ Now `RCP.md` §6.2 carries it, and it is the **sixth exception** of §3.
           ⇒ The switch has changed job: off by default, the default
           would be **yesterday's document**, and every reader that does not know D14
           — B4 included — would drop a healthy session without anybody
           having asked it to.  ⛔ I6 protects *«what changes what is
           seen»* from an **unwatched** change: here the change was
           watched, it is in the document, and the default that betrays is no
           longer the on one but the off one.
           ⚠ The parameter **stays**, and it serves fault **G6**: it is switched off to
             prove that the bench can see the difference between tonight's
             judge and last night's.

        ⛔ AND A `TELA` THAT REPEATS THE SIZE IN FORCE IS NOT A CHANGE: it does not
           leave anything in flight, and resetting the state here would turn
           into `ERRORE_PROTOCOLLO` the legitimate delta that follows the new keyframe
           when the two arrive on **two different streams** (that is how
           `02-filo-validatore.py` and `01-b4-validatore.py` set the context
           back stream by stream).
        """
        # ⛔ P21 — AND A `TELA` ANSWERS A REQUEST, BEFORE ANY
        #    OTHER THING: even the one repeating the size in force, even
        #    the one refusing.  ⚠ Putting it after the early return here
        #    below would leave in flight forever a request the server
        #    has answered — that is a client holding back without end.
        self.risponde_il_tela()
        if (lar, alt) == (self.tela_larghezza, self.tela_altezza):
            # ⛔ Nothing has changed: there is no «new size» that requires
            #    a keyframe (§5.2) and nothing in flight to pardon (§6.2).
            #    ⚠ And the case really exists: §7.1 makes `TELA` answer **every**
            #      `ADATTA_TELA`, even one that asks for the size already
            #      there.  Opening a keyframe debt there would drop the
            #      legitimate delta that follows — a red on a healthy session.
            self.tela_da = "TELA(ADATTATA) (§7.1)"
            return
        prec = (precedente if precedente is not None
                else (self.tela_larghezza, self.tela_altezza))
        # ⛔ The list keeps the previous one **and** those before, if the queue
        #    was already draining: two `TELA`s in a row are the normal scene of
        #    whoever drags a window (P11).
        self.tele_recenti = ([prec] + self.tele_recenti
                             if self.coda_da_svuotare() else [prec])
        self.tela_precedente = prec
        # ⚠ `grazia` no longer opens a time: it only says **whether this reader
        #   applies exception 6 of §3**.  Off (fault G6) the queue is not
        #   tolerated at all, and it is the judge from before the cure.
        self.grazia_concessa = bool(grazia)
        self.chiave_alla_tela_nuova = False
        self.tela_larghezza, self.tela_altezza = lar, alt
        self.tela_da = "TELA(ADATTATA) (§7.1)"

    def coda_da_svuotare(self):
        """⭐⛔ **Is the queue still draining?** — §6.2, **P13** cure.

        It is `True` between a `TELA(ADATTATA)` and **the first keyframe at the new
        size**, which §5.2 guarantees will exist.  ⛔ There is no clock, and
        it is not a convenience of the bench: it was the line that was wrong.

        ⚠ *The second was the wrong quantity.*  What must drain is
          a **queue**, and how long a frame already in flight takes depends
          on **bandwidth**: a 1920x1080 keyframe of a few MiB (§6.2 allows
          16) on a bad line — which is **inside** the model, the minimum is
          480p at 25 — arrives **after** the second.  ⇒ The client would have closed
          a frame sent when it was legal, and which §5.2 forbade the server
          to abandon: invariant **I1** («never to cut off») broken
          **because the line is slow**, that is in the exact condition I1
          exists to protect.  ⭐ And lengthening the second would have **moved**
          the defect instead of removing it.
        """
        return (self.grazia_concessa and not self.chiave_alla_tela_nuova
                and bool(self.tele_recenti))

    def arriva_la_chiave_nuova(self):
        """⛔ The first keyframe at the new size has arrived: **the queue has
           drained**, and from here on an old size is
           `ERRORE_PROTOCOLLO` like any other (§6.2).

        ⚠ Until the **P13** cure this method was called
          `scade_la_grazia()` and said *«the second has passed»* — a fact that
          **does not travel on the wire** and that the case had to declare.  ⭐ Now
          the fact is a **frame**, and it can be seen: it is the difference between a
          rule a mechanical referee can enforce and one it has to
          guess.
        """
        self.chiave_alla_tela_nuova = True
        # ⛔ And with the queue the old sizes go away: they are no longer «in
        #    flight», they are sizes that are worth nothing any more (§6.2).
        self.tele_recenti = []


# ---------------------------------------------------------------------------
class Giudice:
    """Judges ONE frame while it arrives, not after it has arrived.

    ⛔ **And the «while» is normative, not an engineering whim.**  §6.2:
       *«Whoever receives a longer one closes with `ERRORE_PROTOCOLLO` **instead
       of continuing to accumulate**»*.  A judge that takes the whole
       frame in hand and then measures its length has already done the thing
       that line forbids — and on a 7680x4320 canvas the frame it wants to
       stop is precisely the one that does not fit in memory.

    ⛔ **And it does not keep the data.**  It counts the bytes and lets them go: a bench that
       kept them to «look at them better» would be measuring its own memory.
    """

    def __init__(self, contesto, dove="uni", guasti=()):
        self.c = contesto
        self.dove = dove              # "uni" | "controllo"
        self.guasti = set(guasti)
        self.grezzo = bytearray()     # ONLY the header, never the data
        self.byte_dati = 0
        self.verdetto = None          # the first verdict wins
        self.letta = False
        self.campi = {}

        # ── the injectable faults, and each one breaks ONE property ──────────
        # ⛔ They sit here and not in a copy of the file because what must be
        #    broken is **the judgement**, not the scoring: a switch that
        #    turned off a check would make the bench red without
        #    proving that the bench can see that fault.  See `--elenco`.
        self.intestazione = 32 if "G1" in self.guasti else INTESTAZIONE
        self.tipi_leciti = ({CHIAVE, DELTA, 0x0300} if "G2" in self.guasti
                            else {CHIAVE, DELTA})
        self.reset_come_fin = "G3" in self.guasti
        # ⛔ G5 — «the judge of the morning of 12 Aug 2026», that is BEFORE
        #    the four lines entered `RCP.md`.  See the header.
        self.regole_12_agosto = "G5" not in self.guasti
        # ⛔ G6 and G7 — «the judge of the EVENING of 12 Aug», before the two
        #    cures of D13 and D14.  Each switches off a single line.
        self.grazia_di_6_2 = "G6" not in self.guasti      # D14, §6.2 + §3 exc. 6
        self.chiave_di_5_2 = "G7" not in self.guasti      # D13, §5.2
        # ⛔ G8 and G9 — «the judge of two hours ago», that is between the two
        #    cures of the evening and the two that put them back on their feet (P11 and P10).
        self.finestra_di_6_2 = "G8" not in self.guasti    # P11: the window
        self.rilievo_di_5_2 = "G9" not in self.guasti     # P10: the finding
        # ⛔ G10 — «the judge with the clock»: the tolerance goes back to ending by
        #    time, that is the line as it was before the **P13** cure.
        self.orologio_tolto = "G10" not in self.guasti
        # ⛔ G11 — «the judge of an hour ago»: the size looked at BEFORE
        #    the order, that is §6.2 without the precedence of P14.
        self.ordine_prima = "G11" not in self.guasti
        # ⛔⛔ G12 and G13 — THE TWO WAYS OF WRITING **P20** BADLY, one per direction.
        #
        #    G12 «the substitute quantity»: §2.5 is measured on the arrival of
        #        `SESSIONE` instead of on the departure of `ATTACCA` — that is the
        #        judge of **today**, and the test client at its first live
        #        round (`P2-6` §5.2).  ⇒ The healthy session drops.
        #    G13 «the cure written too broadly»: it **never** closes before
        #        `SESSIONE`.  ⇒ I3 disappears, and a server that has not received
        #        `ATTACCA` can push pixels onto whoever has not attached yet.
        #        ⚠ It is the form in which **P5** ended up wrong:
        #        a cure that saves the case that motivated it and opens the other.
        self.sessione_come_grandezza = "G12" in self.guasti
        self.chiude_prima_di_attacca = "G13" not in self.guasti
        # ⛔⛔ G14 and G15 — THE TWO WAYS OF WRITING **P21** BADLY, one per direction, and
        #     the first is not invented: it is **the cure as it was proposed**.
        #
        #     G14 «the discriminant written on the named SIZE»: only a frame
        #         whose size the client itself named in an `ADATTA_TELA`
        #         is held back.  ⛔ Too NARROW: §4.5 says the granted
        #         canvas can differ from the requested one, and on KWin < 6.8
        #         (`SPECIFICHE.md` §6.3) it is the normal road ⇒ the healthy session
        #         drops **one step further on**, which is the signature of this
        #         family from P8 onwards.
        #     G15 «always holds back»: every size never in force is held back,
        #         even without any request in flight.  ⛔ Too BROAD: it takes
        #         away the P11 line — the one that closes **at once** on a size
        #         nobody ever asked for — that is right where the server is
        #         most likely to err.
        self.p21_sulla_misura = "G14" in self.guasti
        self.p21_trattiene_sempre = "G15" in self.guasti
        # ⛔ The size tolerated by the grace is KEPT, not decided at once:
        #    a frame in flight stays subject to all the other lines of
        #    §6.2 — the order of the `numero`s, the ceiling, the FIN — and deciding here
        #    would skip `_giudica_completo`, that is it would acquit a stream that
        #    never closed.
        self.misura_tollerata = None
        # ⛔ The finding on the **client's state** (P10), which is not the outcome:
        #    see point 8-bis.  `None` = «there was nothing to say», and it is not
        #    «I did not look»: the decoder is declared from outside, and
        #    when it is not declared the bench does not invent where it is.
        self.rilievo_cliente = None

    # -- the outcome is written only once: the first verdict is the cause, the
    #    following ones are consequences (like `_cade` in `01-b3-cliente.py`).
    def _decidi(self, v):
        if self.verdetto is None:
            self.verdetto = v
        return self.verdetto

    def _chiuso_il_12_agosto(self, sigla, scostamento, regola, dice,
                             regola_prima, dice_prima):
        """One of the four double readings `RCP.md` closed on 12 Aug.

        ⛔ The two halves sit **in the same function** on purpose: today's line
           and yesterday's are read one under the other, and whoever rereads
           this file in a month sees at once **what changed and
           why**.  ⚠ Keeping them in two distant points is the way one
           of the two ages on its own.

        With fault **G5** injected it goes back to yesterday's reading: the verdict
        is `AMBIGUO` instead of `ERRORE_PROTOCOLLO`, and the four cases that must
        drop turn red with the mark `nome: ERRORE_PROTOCOLLO -> AMBIGUO`.
        """
        if not self.regole_12_agosto:
            return self._decidi(Verdetto(AMBIGUO, regola_prima, dice_prima,
                                         scostamento=scostamento,
                                         propone=sigla))
        return self._decidi(Verdetto(ERRORE_PROTOCOLLO, regola, dice,
                                     scostamento=scostamento))

    def arrivano(self, pezzo):
        """A piece of the stream arrives.  It may already be enough to decide."""
        if self.verdetto is not None:
            return
        if not self.letta:
            manca = self.intestazione - len(self.grezzo)
            self.grezzo += pezzo[:manca]
            pezzo = pezzo[manca:]
            if len(self.grezzo) == self.intestazione:
                self.letta = True
                self._leggi_intestazione()
                if self.verdetto is not None:
                    return
        self.byte_dati += len(pezzo)
        # ⛔ THE CEILING IS CHECKED HERE, WHILE THE BYTES FLOW — §6.2.
        if self.intestazione + self.byte_dati > TETTO_FOTOGRAMMA:
            self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §6.2",
                f"the frame exceeded {TETTO_FOTOGRAMMA} bytes "
                f"({self.intestazione + self.byte_dati} so far): it closes "
                f"«instead of continuing to accumulate»"))

    def finisce(self, come):
        """`come` is «fin» or «reset».  ⛔ And the difference is all of §6.2."""
        if come not in ("fin", "reset"):
            raise ValueError(f"a stream ends with «fin» or «reset», not {come!r}")
        # ⛔ THE RESET IS LOOKED AT FIRST, AND EVEN BEFORE THE HEADER.
        #
        #    §6.2, finding R1.7: *«a reset stream carries an
        #    INCOMPLETE frame: the client MUST throw away what it received, MUST NOT
        #    hand it to the decoder, and MUST treat it as a gap»*.
        #    ⚠ A judge that read the header first would say
        #    `ERRORE_PROTOCOLLO` on a wrong `tipo` inside a frame that
        #    **does not exist**: the server abandoned it midway, and the bytes of
        #    that header can be anything.  It would drop
        #    the session for an abandonment, which is the normal case of §5.1.
        if come == "reset" and not self.reset_come_fin:
            self.c.chiedi_chiave = True
            return self._decidi(Verdetto(
                SCARTATO, "RCP.md §6.2",
                "reset stream: INCOMPLETE frame — it is thrown away, not "
                "handed to the decoder, and treated as a gap (§5.2)"))
        if self.verdetto is not None:
            return self.verdetto
        if not self.letta:
            # ⛔ P4 — FIN BEFORE THE 28 BYTES, and since 12 Aug 2026 it is **cited**.
            #
            #    §6.2, third line of «⛔ The rule, in two lines:»: *«a stream
            #    closed with FIN before the 28 bytes of the header is
            #    ERRORE_PROTOCOLLO: it is not a short frame, it is a
            #    length that does not add up (§3)»*.
            #    ⚠ Until 11 Aug the rule was **derived** from §3, and §6.2 —
            #      the place where whoever implements looks for it — did not write it:
            #      read to the letter, *«the end of the stream is the end of the
            #      frame»* made a 12-byte stream a frame
            #      with **minus sixteen** bytes of data.
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §6.2",
                f"the stream ends with FIN after {len(self.grezzo)} bytes: "
                f"the header wants exactly {self.intestazione}",
                scostamento=len(self.grezzo)))
        return self._decidi(self._giudica_completo())

    # -- the header, field by field, in the order of §6.2 -------------------
    def _leggi_intestazione(self):
        g = bytes(self.grezzo[:INTESTAZIONE])
        tipo, codec, lar, alt, num, ist, inp = struct.unpack("!HHIIIQI", g)
        self.campi = {"tipo": tipo, "codec": codec, "larghezza": lar,
                      "altezza": alt, "numero": num, "istante": ist,
                      "input": inp}

        # 1. ⛔ THE CHANNEL, FROM THE HIGH BYTE — §2.5, and NEVER from the stream number.
        alto = tipo >> 8
        if alto != CANALE_VIDEO:
            nome = CANALI.get(alto)
            if nome is None:
                return self._decidi(Verdetto(
                    ERRORE_PROTOCOLLO, "RCP.md §2.5",
                    f"the high byte of the type is {alto:#04x}: outside the five "
                    f"channels", scostamento=0))
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §2.5",
                f"on this stream the «{nome}» channel ({alto:#04x}) arrives "
                f"from the server: it is the wrong channel, or the wrong direction",
                scostamento=0))

        # 2. ⭐⛔ P3 — WHERE IT ARRIVED.  Closed on 12 Aug 2026.
        #
        #    §2.5, line `0x03`: *«the 28-byte header of §6.2, without
        #    framing — ⛔ and ONLY on a unidirectional stream opened by the
        #    server: a `0x03` on the control channel is ERRORE_PROTOCOLLO,
        #    as is a `0x00` on a unidirectional stream»*.
        #    ⚠ Until 11 Aug the same table closed the case for two
        #      channels out of five and **not for video**, and the client read those
        #      28 bytes with the framing of §6.1 — an invented message of
        #      64 KiB.  The server does not open bidirectional streams (§2.5), so
        #      the only place where it can write a misplaced `0x03` is the
        #      control channel, which the client opened for it.
        if self.dove == "controllo":
            return self._chiuso_il_12_agosto(
                "P3", 0, "RCP.md §2.5",
                "a frame on the CONTROL channel: §2.5 wants video "
                "«only on a unidirectional stream opened by the server», and a "
                "`0x03` on the control channel is ERRORE_PROTOCOLLO",
                "RCP.md §2.5",
                "a frame on the CONTROL channel: §2.5 forbids by name "
                "control on a unidirectional stream and audio on a "
                "stream, and for video it says nothing")

        # 3. ⛔ P1 — THE STATE, and since 12 Aug 2026 it is **cited**.
        #
        #    §2.5, «video» line of the table: *«one per frame, ⛔ and
        #    none before sending `SESSIONE`: whoever receives one before
        #    closes with ERRORE_PROTOCOLLO»*.
        #    ⚠ Until 11 Aug for whoever RECEIVES the rule was derived from §1
        #      («the order of the five steps admits no permutations») plus §3, and for
        #      whoever SENDS it was derived from nowhere: it was invariant
        #      **I3** — *whoever does not go through the validator does not receive a pixel* —
        #      left without a line on the wire, while §2.5 wrote it for the
        #      input channel two lines above.
        #
        # ⛔⛔ AND SINCE 13 AUG 2026 THE LINE IS READ IN TWO PIECES — proposal
        #     **P20**, and they are two different phenomena under the same word.
        #
        #     3a. ⭐ **The certainty**: the client has not yet sent `ATTACCA`.
        #         §4.5 makes `SESSIONE` the **answer** to `ATTACCA` ⇒ the
        #         server cannot have sent it, and no hypothesis is needed
        #         on the delivery order.  Here it closes, and it is I3.
        #     3b. ⛔ **The undecidable**: `ATTACCA` has left and the bytes of
        #         `SESSIONE` have not arrived yet.  §2.5 to the letter makes it
        #         close; ⚠ but the frame and the control channel are
        #         **two independent QUIC streams** and nothing orders their
        #         delivery — losing the packet that carries `SESSIONE` is enough.
        #         ⇒ Today the case comes out `AMBIGUO` with the cure next to it: it belongs to the
        #         coordinator, not to this bench.
        if not self.c.attacca_spedito and self.chiude_prima_di_attacca:
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §2.5",
                "a frame before `SESSIONE`: §2.5 forbids the server to "
                "open a video stream before having sent it — it is "
                "invariant I3 on the wire, whoever does not go through the validator does not "
                "receive a pixel",
                scostamento=0))
        if not self.c.sessione_aperta:
            if self.sessione_come_grandezza:
                # ⛔ TODAY's reading, to the letter: it closes.  It is the
                #    substitute quantity, and it is what the test client
                #    did at its first live round (`P2-6` §5.2).
                return self._decidi(Verdetto(
                    ERRORE_PROTOCOLLO, "RCP.md §2.5",
                    "a frame before `SESSIONE`: §2.5 forbids the server "
                    "to open a video stream before having sent it",
                    scostamento=0))
            return self._decidi(Verdetto(
                AMBIGUO, "RCP.md §2.5",
                "`ATTACCA` has left and the bytes of `SESSIONE` have not yet "
                "arrived: §2.5 to the letter makes it close, ⛔ but the measurement is "
                "taken on the delivery order of **two independent QUIC "
                "streams** — the server may have done everything "
                "§2.5 and §5.2 require of it and the `SESSIONE` packet "
                "may have been lost.  ⇒ Whoever applies the line to the letter closes "
                "a session in which nobody made a mistake",
                scostamento=0, propone="P20"))

        # 4. ⛔ THE TYPE — §6.2: «Other values: ERRORE_PROTOCOLLO».
        if tipo not in self.tipi_leciti:
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §6.2",
                f"type {tipo:#06x}: RCP/1 defines two, {CHIAVE:#06x} "
                f"keyframe and {DELTA:#06x} delta", scostamento=0))

        # 5. ⛔ THE CODEC — §6.2: «MUST be the one negotiated in §4.3».
        if codec not in CODEC:
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §6.2",
                f"codec {codec}: RCP/1 defines two, 1 = HEVC and 2 = AV1",
                scostamento=2))
        if codec != self.c.codec_negoziato:
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §6.2",
                f"codec {codec} = {CODEC[codec]}, but in §4.3 what was negotiated was "
                f"{self.c.codec_negoziato} = {CODEC[self.c.codec_negoziato]}",
                scostamento=2))

        # 6. ⭐⛔ THE `numero` ZERO — ambiguity A2, and it is an internal
        #    CONTRADICTION, not a gap.
        #
        #    §6.2: `numero` is «counter of the captured frames, which grows
        #    by one for every frame the server decides to send» — and
        #    **does not say where it starts from**.
        #    §7.1: `RICHIEDI_CHIAVE.ultimo_numero` is «the last decoded
        #    frame, **0 if none**».
        #    §6.0: «⛔ Every integer has a single meaning of *absent*, and it must be
        #    declared where needed: **there are no implicit sentinel
        #    values**».
        #    ⇒ If the first frame carries `numero = 0`, `RICHIEDI_CHIAVE(0)`
        #      means both things, and the server cannot know which.
        #    ⭐ Closed on 12 Aug 2026: §6.2 now carries *«the first
        #      frame of a session carries `numero = 1`, and 0 is
        #      reserved»*, which is the same convention as the input `id`
        #      (§7.3).
        if num == 0:
            return self._chiuso_il_12_agosto(
                "P2", 12, "RCP.md §6.2",
                "`numero = 0`: §6.2 reserves zero — «the first frame of "
                "a session carries `numero = 1`», and «when the counter wraps "
                "0 is skipped» — because 0 means «no frame», the "
                "meaning §7.1 gives it in `RICHIEDI_CHIAVE`",
                "RCP.md §6.2 against §7.1, by §6.0",
                "`numero = 0`: §7.1 uses zero as «none» in "
                "`RICHIEDI_CHIAVE`, §6.2 does not say where the counter starts, "
                "and §6.0 forbids implicit sentinels")

        # 7. ⭐⛔⛔ **THE ORDER, AND IT COMES BEFORE THE SIZE** — §6.2, cure of
        #    **P14**, 12 Aug 2026: *«the order rule is applied BEFORE
        #    the size rule: a frame whose `numero` precedes
        #    the last one already delivered is discarded, and its size is not even
        #    looked at»*.
        #
        #    ⛔ **And the precedence is not a detail of code order: it is the
        #    line that holds up the other three.**  Without it, the two lines of
        #    this same section contradict each other and the stricter one wins on
        #    a scene in which nobody made a mistake: the keyframe that closes the
        #    tolerance **overtakes** the frames in flight — not by chance, but
        #    because the old one is **the biggest** (§5.2 forbids
        #    abandoning a keyframe) and the new one is smaller.
        #    ⚠ Until this cure the size judgement sat up here, and
        #      this case came out `ERRORE_PROTOCOLLO`: the session dropped.
        #
        #    ⚠ The modulo is not pedantry: at 60 frames per second the
        #      counter wraps after two years and two months, and a session can
        #      last longer (§6.2).  A direct `<` comparison would make it
        #      discard **every** frame after the wrap, forever.
        #    ⛔ With fault **G11** the order goes back AFTER the size, that is the
        #       judge of an hour ago: it is the same line, moved two steps
        #       in the file, and it is enough to drop a healthy session.
        if self.ordine_prima:
            fuori = self._ordine(num)
            if fuori is not None:
                return fuori

        # 8. ⭐⛔ P5 — THE SIZE.  Closed on 12 Aug 2026, and **corrected the
        #    same day** because the first draft killed a healthy session.
        #
        #    §6.2: *«the size of THIS frame.  ⛔ In RCP/1 they MUST match
        #    the **canvas in force** — the one granted in `SESSIONE` (§4.5),
        #    **or** the last one granted by `TELA` if meanwhile it has been
        #    adapted (§7.1) — and whoever receives others closes with
        #    ERRORE_PROTOCOLLO: the client rescales to the VIEW, not to the canvas»*.
        #    ⚠ Until 11 Aug the line said *«it is always that of the canvas,
        #      and the client rescales»* — which **describes** and does not command (§0
        #      declares normative only MUST / MUST NOT / MAY) — and no line
        #      said what whoever receives a different size does.
        #    ⛔ And for two hours it said «the canvas granted in `SESSIONE`», which
        #      after an `ADATTA_TELA` made the client close in front of a
        #      conforming server: the two right words are **in force**.
        #    ⛔ The comparison is with the canvas THAT WAS DECLARED, never with a
        #      number written here: the two cases
        #      `misura-uguale-a-una-tela-diversa` and `misura-dopo-adatta-tela` keep it honest.
        if (lar, alt) != (self.c.tela_larghezza, self.c.tela_altezza):
            # 8-bis. ⭐⛔ **D14 — THE FRAMES IN FLIGHT.  ENTERED IN `RCP.md` ON THE
            #        EVENING OF 12 AUG 2026**, §6.2 at the end and **sixth
            #        exception** of §3.
            #
            #        *«After receiving a `TELA(ADATTATA)` (§7.1) the client
            #        MUST accept for one second the frames whose size
            #        matches the previous canvas, painting them rescaled to the view
            #        and writing it in the log; once that second has passed they are
            #        ERRORE_PROTOCOLLO, and so is at once a size that is neither
            #        the one in force nor the previous one.»*
            #        ⚠ Until that evening it was proposal **P8** and here it came out
            #          `AMBIGUO`: §6.2 made the client close in front of a
            #          frame opened **before** the `ADATTA_TELA` reached
            #          the server — and §5.2 forbids the server to clear the pipe,
            #          because a **keyframe** is not abandoned.
            # ⭐⛔ **P11 — THE WINDOW, NOT «THE PREVIOUS ONE».**  §6.2, corrected
            #    on the evening of 12 Aug 2026: *«the frames whose size matches
            #    **a canvas that was in force since the queue
            #    started draining**»*, and `ERRORE_PROTOCOLLO` **at once**
            #    for a size «that was never in force in that
            #    window».
            #    ⚠ It said «the previous canvas», in the singular, and whoever drags
            #      a window sends two: 1920x1080 -> `TELA(1600,900)` ->
            #      `TELA(1280,720)`, and the **keyframe** opened before everything — the
            #      biggest, the slowest, and the one §5.2 forbids the server
            #      to abandon — carried a size that was neither the one in
            #      force nor the previous one.  ⛔ The healthy session dropped
            #      anyway, **one step further on** from the scene the cure
            #      had just closed.
            # ⛔ With fault **G8** the window goes back to being «the previous one»
            #    alone, that is the line of two hours ago.
            finestra = (self.c.tele_recenti if self.finestra_di_6_2
                        else self.c.tele_recenti[:1])
            # ⭐⛔ **P13 — THE TOLERANCE ENDS AT THE KEYFRAME, NOT BY THE CLOCK.**
            #    §6.2: *«the tolerance does not end by the clock: it ends when
            #    the first keyframe at the new size arrives»*.  ⇒ The condition is
            #    `coda_da_svuotare()`, and it does **not** look at `secondo_passato`: that
            #    field exists only so that fault **G10** — «the judge with
            #    the clock», the line of two hours ago — can put it back in charge and
            #    the session can be seen dropping on the slow line.
            coda = self.c.coda_da_svuotare()
            if not self.orologio_tolto and self.c.secondo_passato:
                coda = False
            if (coda and self.grazia_di_6_2 and (lar, alt) in finestra):
                # ⛔ It is NOT decided here: the tolerance is marked and it goes on.
                #    A frame in flight stays subject to the order of the
                #    `numero`s, to the ceiling and to the FIN.
                self.misura_tollerata = (lar, alt)
                # ⭐⛔ **P10 — AND HERE WE LOOK AT WHERE THE DECODER IS.**
                #
                #    §5.2, line entered on the evening of 12 Aug: *«the client
                #    reconfigures the decoder on the first KEYFRAME at the
                #    new size, not on the `TELA`»*, and the client's line now
                #    says *«nor the one tolerated by §6.2»*.  ⇒ The frame
                #    is delivered anyway — the two lines no longer command the
                #    opposite — ⛔ but a client that had reconfigured on the
                #    `TELA` is **outside §5.2**, and the bench says so instead of
                #    letting it pass: `[M]` a decoder at the new
                #    size receiving the old one raises no errors and **paints
                #    a wrecked image** (Chrome, HEVC, 12 Aug 2026).
                #    ⚠ The finding is NOT the outcome: the outcome talks about the wire, where
                #      nobody made a mistake; the finding talks about the **client's
                #      state**, which is declared from outside because it is not on the
                #      wire.
                if (self.rilievo_di_5_2
                        and self.c.decodificatore_a is not None
                        and self.c.decodificatore_a != (lar, alt)):
                    self.rilievo_cliente = (
                        f"⛔ the decoder is configured at "
                        f"{self.c.decodificatore_a[0]}x"
                        f"{self.c.decodificatore_a[1]} while a "
                        f"{lar}x{alt} frame tolerated by §6.2 arrives: whoever "
                        f"reconfigured it on the `TELA` did what §5.2 "
                        f"forbids — it is reconfigured on the first KEYFRAME at the "
                        f"new size.  `[M]` configured like this the "
                        f"decoder paints a wrecked image without "
                        f"raising an error")
            # 8-quater. ⭐⛔⛔ **P21 — THE TWO LINES OF §6.2 COMMAND THE
            #           OPPOSITE ON THE SAME FRAME**, eight lines
            #           apart.  Proposal opened on 13 Aug 2026.
            #
            #           §6.2, paragraph of **P19**: a frame at the **new**
            #           size can arrive **before** the `TELA` that
            #           grants it, and the client ⛔ **MUST NOT close: it holds back**.
            #           §6.2, tolerance paragraph (**P11** + **P13**),
            #           eight lines below: a size *«that was never in
            #           force in that window»* is `ERRORE_PROTOCOLLO`
            #           ⛔ **at once**.
            #           ⇒ On the scene `SESSIONE` 1920x1080 -> `TELA(1600,900)`
            #             -> `ADATTA_TELA(1280,720)` unanswered, with the
            #             1280x720 frame arriving before the `TELA`, the
            #             two lines give **two different bytes**: `CONGEDO` on one
            #             side, nothing on the other.  It is the form of **P10** —
            #             ⛔ but there it was two sections, here it is **the same one**.
            #
            #     ⭐ The discriminant this bench proposes is what
            #        **the client itself sent**, that is the same quantity as
            #        P20 and the general form of the `numero` of P14: local,
            #        monotonic, independent of delivery.  ⛔ And it is NOT «the
            #        size the client named» — see `adatta_in_volo` and
            #        fault G14: §4.5 allows the server to grant a
            #        canvas **different from the requested one**, and the discriminant
            #        written on the numbers would kill the healthy session one step
            #        further on.
            #     ⛔ And nothing is cured here: `RCP.md` belongs to the coordinator.
            #        As long as the document carries the two lines, the honest outcome is
            #        `AMBIGUO` — two conforming implementations diverge.
            in_volo = (self.p21_trattiene_sempre
                       or ((lar, alt) in self.c.adatta_in_volo
                           if self.p21_sulla_misura
                           else bool(self.c.adatta_in_volo)))
            if self.misura_tollerata is None and in_volo:
                return self._decidi(Verdetto(
                    AMBIGUO, "RCP.md §6.2",
                    f"the frame is {lar}x{alt}, the canvas in force is "
                    f"{self.c.tela_larghezza}x{self.c.tela_altezza} and that "
                    f"size was never in force in this window — "
                    f"⛔ but the client has {len(self.c.adatta_in_volo)} "
                    f"`ADATTA_TELA` sent and unanswered: §6.2 says "
                    f"«hold back» in the paragraph of the frames in flight and "
                    f"`ERRORE_PROTOCOLLO` **at once** eight lines below.  Two "
                    f"conforming implementations, two different bytes",
                    scostamento=4, propone="P21"))
            if self.misura_tollerata is None:
                return self._chiuso_il_12_agosto(
                    "P5", 4, "RCP.md §6.2",
                    f"the frame is {lar}x{alt} and the canvas IN FORCE is "
                    f"{self.c.tela_larghezza}x{self.c.tela_altezza}, from "
                    f"{self.c.tela_da}: §6.2 wants them to coincide",
                    "RCP.md §6.2",
                    f"the frame is {lar}x{alt} and the granted canvas is "
                    f"{self.c.tela_larghezza}x{self.c.tela_altezza}: «it is always "
                    f"that of the canvas» does not say what whoever receives does")

        # 8-ter. ⛔ And with fault **G11** the order is looked at HERE, after the
        #        size: the frame in flight overtaken by the keyframe has already
        #        dropped two steps above, and the session with it.
        if not self.ordine_prima:
            fuori = self._ordine(num)
            if fuori is not None:
                return fuori

        # 9. ⭐⛔ P6 — THE FIRST FRAME IS A DELTA.  Closed on 12 Aug
        #    2026, and it is the line that bites in THIS phase.
        #
        #    §5.2, first point of «The rules:»: *«⛔ the first frame
        #    the server sends after `SESSIONE` MUST be a keyframe
        #    (`0x0301`)»*.
        #    ⚠ Until 11 Aug an opening delta **conformed to every
        #      line of the document**, and phase 2 — which delivers a still
        #      frame — would have shown garbage without anybody being
        #      wrong.  ⛔ And the client had no way of noticing: §5.2
        #      makes it ask for a keyframe on a **gap** in the `numero`s, and here there are
        #      no gaps (it is the first); and §5.2 itself declares `[S]` that at
        #      a missing delta the decoder **raises no error**.
        if tipo == DELTA and not self.c.chiave_consegnata:
            return self._chiuso_il_12_agosto(
                "P6", 0, "RCP.md §5.2",
                "the first frame of the session is a DELTA: §5.2 wants "
                "the first frame after `SESSIONE` to be a keyframe "
                "(0x0301)",
                "RCP.md §5.2",
                "the first frame of the session is a DELTA: no line "
                "obliges the server to start with a keyframe, and the client "
                "has no gap from which to notice")

        # 10. ⭐⛔ **P9 — THE FIRST FRAME AT THE NEW SIZE.  Entered in
        #     `RCP.md` §5.2 on the evening of 12 Aug 2026, defect D13.**
        #
        #     *«And the same holds at every canvas change: the first frame
        #     sent at the new size, after a `TELA(ADATTATA…)` (§7.1), MUST
        #     be a keyframe (`0x0301`) — and MUST be a real keyframe,
        #     that is carry with it everything needed to decode it on its
        #     own: for HEVC its VPS/SPS/PPS in front of the IDR.»*
        #     ⛔ And the line is not caution: `[M]` 12 Aug 2026, bench
        #     `02-pagina-tela-*` — with only deltas at the new size **Chrome on
        #     HEVC emits five frames, all declared at the OLD
        #     size, painted, and zero errors**.  The symptom is «the desktop
        #     tears when I resize the window», and it names neither the
        #     protocol nor the canvas.
        #
        #     ⚠ **AND HERE THE BENCH JUDGES LESS THAN WHAT THE LINE SAYS**, and it must be
        #       written instead of discovered: this judge **does not keep the
        #       data** of the frame (see the class), so it sees that the
        #       first at the new size is `0x0301` and ⛔ **cannot see whether
        #       it really carries its VPS/SPS/PPS in front of the IDR** — the
        #       «*real* keyframe» half stays with the encoding bench
        #       (`02-codifica-nal.py`) and with the page (`02-pagina-tela-*`).
        #     ⚠ `[?]` **And a question this line opens and does not close**:
        #       §6.2 says frames arrive **out of order**, so a
        #       delta at the new size can arrive **before** the keyframe
        #       the server sent first.  The line constrains whoever **sends**
        #       and this judge applies it to whoever **receives**: it is the strict
        #       reading, and it is the same P6 has had since this morning.  A gap in the
        #       `numero`s tells the two cases apart, and no line says to look at it.
        if (self.chiave_di_5_2
                and self.c.tela_da.startswith("TELA")
                and not self.c.chiave_alla_tela_nuova
                and self.misura_tollerata is None
                and tipo == DELTA):
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §5.2",
                f"the first frame at the NEW size ({lar}x{alt}, from a "
                f"`TELA(ADATTATA)`) is a DELTA: §5.2 wants a keyframe "
                f"({CHIAVE:#06x}) at every canvas change, and a real one — with its "
                f"parameter sets.  Without it, `[M]` Chrome on HEVC paints five "
                f"frames at the old size without raising an error",
                scostamento=0))

    def _ordine(self, num):
        """⛔ §6.2 — a `numero` **preceding** the last one already
           delivered is discarded, with modulo 2^32 arithmetic and signed differences.

        ⚠ It sits in a method of its own because fault **G11** must be able to
          move it **after** the size without the line changing by a comma:
          what P14 cured is not the text of the rule, it is **the place where
          it is applied** — and a fault that rewrote the text too
          would prove something else.
        """
        if self.c.ultimo_consegnato is None:
            return None
        d = (num - self.c.ultimo_consegnato) & 0xFFFFFFFF
        if d >= 0x80000000 or d == 0:
            return self._decidi(Verdetto(
                SCARTATO, "RCP.md §6.2",
                f"`numero` {num} does not follow "
                f"{self.c.ultimo_consegnato} (signed difference "
                f"{d - 0x100000000 if d >= 0x80000000 else d}): it is discarded, "
                f"and ⛔ **its size is not even looked at** — the streams are "
                f"independent and frames arrive out of order",
                scostamento=12))
        return None

    def _giudica_completo(self):
        """The stream ended with FIN and the header was good."""
        num = self.campi["numero"]
        # ⛔ THE GAP — §5.2: «the client MUST send `RICHIEDI_CHIAVE` when it
        #    notices a gap in the succession of the `numero`s».  ⚠ And the gap
        #    is **normal**: §6.2 says the counter grows also for the
        #    frames the server then abandons.
        if (self.c.ultimo_consegnato is not None
                and num != ((self.c.ultimo_consegnato + 1) & 0xFFFFFFFF)):
            self.c.chiedi_chiave = True
        self.c.ultimo_consegnato = num
        if self.campi["tipo"] == CHIAVE:
            self.c.chiave_consegnata = True
            self.c.chiedi_chiave = False
            # ⛔ P9 — and the keyframe counts for the new canvas **only if it carries it**:
            #    a keyframe in flight at the old size does not pay the debt that
            #    §5.2 opens at every `TELA(ADATTATA)`.
            # ⭐⛔ And P13: this **is also the end of the tolerance**.  §6.2:
            #    *«it ends when the first keyframe at the new size arrives»* ⇒
            #    from here on an old size is `ERRORE_PROTOCOLLO`, and it is not
            #    a clock that says so but a frame that was seen.
            if self.misura_tollerata is None:
                self.c.arriva_la_chiave_nuova()
        se = (f"{'keyframe' if self.campi['tipo'] == CHIAVE else 'delta'} "
              f"no. {num}, {self.campi['larghezza']}x{self.campi['altezza']}, "
              f"{self.byte_dati} bytes of data")
        if self.misura_tollerata is not None:
            # ⛔ §3, last line: the tolerance IS WRITTEN IN THE LOG.  A
            #    silent tolerance is indistinguishable from a defect.
            return Verdetto(
                ACCETTATO, "RCP.md §6.2",
                f"{se} — ⚠ TOLERATED: it carries the **previous** canvas and the "
                f"`TELA(ADATTATA)` has just passed, so it was already in flight. "
                f"It is painted **rescaled to the view** and it is the sixth exception "
                f"of §3, which must be written in the log",
                tollerato=(f"canvas {self.misura_tollerata[0]}x"
                           f"{self.misura_tollerata[1]}, in force within the "
                           f"second just passed (§6.2, §3 exception 6)"),
                rilievo=self.rilievo_cliente)
        return Verdetto(ACCETTATO, "RCP.md §6.2", se)


# ---------------------------------------------------------------------------
def intestazione(tipo=CHIAVE, codec=1, lar=1920, alt=1080, num=1, ist=0, inp=0):
    """The 28 bytes of §6.2, in network order and without one byte of padding."""
    return struct.pack("!HHIIIQI", tipo, codec, lar, alt, num, ist, inp)


# ===========================================================================
# ⛔ THE LINES THAT ENTERED `RCP.md` ON 12 AUG 2026, AND THE TWO CASES OF EACH.
#    ⚠ Six in the morning (P1-P6) and **two in the evening** (P8 from D14, P9 from D13): the
#      count is not written here, `regole_coperte()` computes it.
#
#    ⚠ Until 11 Aug this table was called `PROPOSTE` and was a
#      list of things **to ask** the coordinator.  Now the lines are
#      **normative** — they sit in `RCP.md` §2.5, §5.2, §6.2 — and this table
#      says two things a list of proposals did not say:
#
#      ⛔ **where the line is**, to go and reread it instead of trusting;
#      ⛔ **which case violates it and which respects it**, by name.
#
#    ⭐ And the two names are not documentation: `regole_coperte()` **looks them up**
#       among the cases and the round prints the count.  A rule that lost one of the
#       two cases — or cited a renamed one — turns red here, and not
#       six months from now when somebody notices.
REGOLE_NUOVE = {
    "P1": {
        "dove": "RCP.md §2.5, «video» line of the table",
        "dice": "The server MUST NOT open a video stream before having "
                "sent `SESSIONE`; whoever receives one before closes with "
                "`ERRORE_PROTOCOLLO`.",
        "era": "derived from §1 + §3 for whoever receives, and from NOTHING for whoever sends",
        "viola": "prima-di-sessione",
        "rispetta": "dopo-sessione",
    },
    "P2": {
        "dove": "RCP.md §6.2, field `numero`",
        "dice": "The first frame of a session carries `numero = 1`; ⛔ **0 "
                "is reserved** and means «no frame», which is the "
                "meaning §7.1 gives it in `RICHIEDI_CHIAVE`.  ⛔ And when the "
                "counter wraps 0 **is skipped**: from `0xFFFFFFFF` it "
                "goes to `1`.",
        "era": "double reading — §6.2 did not say where the counter starts; and "
               "the cure itself lasted two hours before it was seen that when the "
               "counter wraps the reserved `0` came back into circulation by itself",
        "viola": "numero-zero",
        "rispetta": "numero-uno",
    },
    "P3": {
        "dove": "RCP.md §2.5, line `0x03` of the channel table",
        "dice": "Video lives **only** on a unidirectional stream opened by the "
                "server: a `0x03` on the control channel is "
                "`ERRORE_PROTOCOLLO`.",
        "era": "double reading — §2.5 closed the case for 0x00 and 0x04 and not "
               "for video",
        "viola": "video-sul-controllo",
        "rispetta": "video-su-unidirezionale",
    },
    "P4": {
        "dove": "RCP.md §6.2, third line of «The rule, in two lines»",
        "dice": "A video stream closed with **FIN before the 28 bytes** "
                "of the header is `ERRORE_PROTOCOLLO`: it is not a "
                "short frame, it is a length that does not add up (§3).",
        "era": "derived from §3, and §6.2 — where whoever implements looks for it — was silent",
        "viola": "intestazione-27-byte",
        "rispetta": "chiave-senza-dati",
    },
    "P5": {
        "dove": "RCP.md §6.2, fields `largh.` and `altezza`",
        "dice": "In RCP/1 `largh.` and `altezza` **MUST** match the **canvas in "
                "force** — the one of `SESSIONE` (§4.5), or the last one "
                "granted by `TELA` if it has been adapted (§7.1); whoever receives "
                "a different size closes with `ERRORE_PROTOCOLLO`.",
        "era": "double reading — «it is always that of the canvas» describes and does not "
               "command, and no line said what whoever receives does.  ⛔ And "
               "for two hours the cure itself was wrong: it said «the canvas "
               "granted in `SESSIONE`», which after an `ADATTA_TELA` kills a "
               "healthy session.  Corrected on 12 Aug 2026: «the canvas IN FORCE»",
        "viola": "misura-diversa-dalla-tela",
        "rispetta": "misura-dopo-adatta-tela",
    },
    "P6": {
        "dove": "RCP.md §5.2, first point of «The rules:»",
        "dice": "The first frame the server sends after `SESSIONE` "
                "**MUST** be a keyframe (`0x0301`).",
        "era": "double reading — an opening delta conformed to every line, "
               "and the client had no way of noticing",
        "viola": "primo-fotogramma-delta",
        "rispetta": "primo-fotogramma-chiave",
    },
    # ── ⭐⛔ AND THE TWO ENTERED ON THE **EVENING** OF 12 AUG, FROM D13 AND D14 ─
    #    ⚠ Until that evening they sat in the `PROPOSTE_APERTE` table here
    #      below, and their cases came out `AMBIGUO`.  ⛔ The day a
    #      proposal becomes a line, its cases change **expectation**: leaving them
    #      where they were would mean judging yesterday's document, which is what
    #      fault **G5** exists to show.
    "P8": {
        "dove": "RCP.md §6.2, at the end («The canvas change and the frames in "
                "flight»), and §3 exception 6",
        "dice": "After a `TELA(ADATTATA)` the client **MUST** accept for **one "
                "second** the frames carrying the **previous** size, "
                "painting them rescaled to the view and **writing it in the "
                "log**; outside the second they are `ERRORE_PROTOCOLLO`, and so "
                "is **at once** a size that is neither the one in force nor "
                "the previous one.",
        "era": "⛔ **internal contradiction** — not a double reading: §6.2 "
               "made whoever receives a size other than the canvas in "
               "force close, and §6.2 itself says frames arrive out of "
               "order.  Two conforming implementations produced the **same** "
               "byte — the closing — and killed a healthy session",
        # ⛔ TWO cases violate it, and both are needed: one keeps the grace
        #    inside **the second**, the other inside **one size**.  A grace
        #    written too broadly is as much a defect as a rule too
        #    narrow, and that is how P5 ended up wrong this morning.
        "viola": ("p13-vecchia-dopo-la-chiave-nuova",
                  "p8-misura-di-nessuna-tela"),
        "rispetta": "p8-in-volo-dopo-adatta-tela",
    },
    "P9": {
        "dove": "RCP.md §5.2, second point of «The rules:»",
        "dice": "The first frame sent at the **new size**, after a "
                "`TELA(ADATTATA…)`, **MUST** be a keyframe (`0x0301`) — and "
                "a **real** keyframe, with its VPS/SPS/PPS in front of the IDR.  ⛔ "
                "And the client **MUST NOT** hand to the decoder a "
                "frame whose size is not the one the "
                "decoder is configured for.",
        "era": "⛔ **defect D13, `[M]`**: with only deltas at the new size "
               "Chrome on HEVC emits 5 frames, all declared at the "
               "OLD size, paints them and raises **no** error — "
               "while AV1 protests in all four cells.  The rule "
               "is needed because on the main codec the symptom is **silent**",
        "viola": "d13-delta-alla-misura-nuova",
        "rispetta": "d13-chiave-alla-misura-nuova",
    },
    "P11": {
        "dove": "RCP.md §6.2, at the end — the window instead of the singular",
        "dice": "The grace covers the frames whose size matches **a canvas "
                "that was in force within the second just passed**; ⛔ and "
                "`ERRORE_PROTOCOLLO` **at once** is for a size that in that "
                "window **was never in force**.",
        "era": "⛔ the D14 cure named «the **previous** canvas», in the "
               "singular, ⚠ and whoever drags a window sends two: "
               "1920x1080 -> `TELA(1600,900)` -> `TELA(1280,720)`, and the keyframe "
               "opened before everything — the biggest, the slowest, and the one "
               "§5.2 forbids the server to abandon — dropped anyway.  "
               "**One step further on from the scene the cure had just "
               "closed**",
        "viola": "p11-misura-mai-in-vigore",
        "rispetta": "p11-due-tele-nella-finestra",
    },
    "P13": {
        "dove": "RCP.md §6.2, at the end — and §3, line 6, which says the same thing",
        "dice": "The tolerance **does not end by the clock: it ends when "
                "the first keyframe at the new size arrives** (§5.2).  From that "
                "frame on an old size is `ERRORE_PROTOCOLLO`.",
        "era": "⛔ it said «for **one second**», and the second was the wrong "
               "quantity: what must drain is a **queue**, and how long "
               "a frame already in flight takes depends on **bandwidth**.  A "
               "1920x1080 keyframe of a few MiB on a bad line — which is "
               "**inside** the model, the minimum is 480p at 25 — arrives **after** "
               "the second, and the client closed a frame sent when it "
               "was legal and which §5.2 forbade abandoning.  ⛔ It was not only "
               "a healthy session dropping: it was invariant **I1** («never to "
               "cut off») broken **because the line is slow**, that is in the "
               "exact condition I1 exists to protect.  ⭐ And lengthening "
               "the second would have **moved** the defect instead of removing it",
        "viola": "p13-vecchia-dopo-la-chiave-nuova",
        "rispetta": "p13-linea-lenta",
    },
    "P14": {
        "dove": "RCP.md §6.2, right before the box on the frames in flight",
        "dice": "⛔ **The order rule is applied BEFORE the size "
                "rule**: a frame whose `numero` precedes "
                "the last one already delivered **is discarded**, and its size is not "
                "even looked at.",
        "era": "⛔ two lines of the **same section** contradicting each other, and "
               "the stricter one won on a scene in which nobody had "
               "made a mistake: the keyframe that closes the tolerance **overtakes** the "
               "frames in flight — not by chance, but because the old one is "
               "the biggest (§5.2 forbids abandoning it) and the new one is "
               "smaller.  ⚠ Fourth time the same family moves "
               "by one step: **P8 -> P11 -> P13 -> P14**",
        # ⛔ AND HERE THE PAIR IS NOT «closes / accepts», and it is the point of the
        #    line: it is «discarded / really closes».  ⚠ Without the second, the
        #    new precedence becomes a **hole that swallows the real cases too** —
        #    a frame at the wrong size would pass for «arrived
        #    late» and the size rule would no longer bite anything.
        "viola": "p13-vecchia-dopo-la-chiave-nuova",
        "rispetta": "p14-in-volo-scavalcato-dalla-chiave",
        "esito_viola": ERRORE_PROTOCOLLO,
        "esito_rispetta": SCARTATO,
        "etichetta_viola": "keeps it TIGHT (order fine, wrong size "
                           "-> it really closes)",
        "etichetta_rispetta": "EXERCISES it (preceding number -> it is discarded)",
    },
}


# ===========================================================================
# ⛔ AND A LINE THAT DOES NOT TALK ABOUT THE WIRE BUT ABOUT THE **CLIENT'S STATE** — P10.
#
#    §5.2: *«the client reconfigures the decoder on the first KEYFRAME at the
#    new size, not on the `TELA`»*.  ⛔ That size **is not on the wire**: a
#    referee reading the bytes cannot see it, and this bench has it
#    **declared** by the case (`decodificatore_a`).
#
#    ⚠ It sits in a table of its own and not among the rules above for one reason
#      only, and it is the same that keeps `SCARTATO` and
#      `ERRORE_PROTOCOLLO` apart: the pair has a **different form**.  A wire
#      rule has one case that comes out `ERRORE_PROTOCOLLO` and one that comes out `ACCETTATO`;
#      here both come out `ACCETTATO` — on the wire nobody made a mistake — and what
#      changes is the **finding on the client**, which is there in one and not in the other.
#      ⛔ Putting them together would mean requiring that a client defect
#      drop the session, that is the error this chapter has already
#      paid for three times in one day.
REGOLE_DI_STATO = {
    "P10": {
        "dove": "RCP.md §5.2, the line before the client's one",
        "dice": "The client **reconfigures the decoder on the first KEYFRAME "
                "at the new size, not on the `TELA`** — and does not hand to the "
                "decoder a frame of a size other than the one it "
                "is configured for **nor the one tolerated by §6.2**.",
        "era": "⛔⛔ **the two cures of 12 Aug contradicted each other on the "
               "same frame**: §6.2 «accept it and paint it», §5.2 "
               "«throw it away», and the document said nowhere **when** "
               "the client reconfigures.  Two conforming readings that diverged "
               "on the wire — one sent `RICHIEDI_CHIAVE`, the other did not",
        "viola": "p10-decodificatore-al-tela",
        "rispetta": "p10-decodificatore-alla-chiave",
    },
}


# ===========================================================================
# ⛔⛔ AND THE PROPOSALS STILL **OPEN** — what `RCP.md` does NOT say yet.
#
#    ⚠ They sit in a table **separate** from `REGOLE_NUOVE`, and the separation is
#      the most important thing of this block: there are **normative** lines
#      that one goes to reread in the document, here is a cure the
#      coordinator has not applied yet.  ⛔ Mixing them would mean that
#      in a month nobody knows any more which of the two a bench is
#      enforcing — and it is form **E5** («a "fact" that was a deduction
#      never measured») applied to the document instead of the code.
#
#    ⛔ And every proposal carries **its own** cases with TODAY's expectation: the one that
#       shows it, and those that prevent writing it too broadly.
#
# ⭐⛔ **AND ON THE EVENING OF 12 AUG 2026 THIS TABLE EMPTIED.**  P8 and P9
#    entered the document, and the two points where **they did not hold** — P10 and
#    P11, found by applying them — entered in the next round.  ⛔ It stays empty, and
#    it is declared empty instead of being removed: the day this bench
#    finds the next point, the place to write it already exists — and
#    `proposte_coperte()` keeps counting «0 of 0», which is a number, not a
#    silence.
#
# ⭐⛔ **AND ON 13 AUG 2026 IT FILLED UP AGAIN, WITH A SINGLE ENTRY: P20.**
#    ⚠ It was not found by a rereading: it was found by the **test client** at
#      its first round against a server that really sends (`P2-6` §5.2), and the
#      cure of that round cured the **bench** — not the line.
PROPOSTE_APERTE = {
    "P20": {
        "dove": "RCP.md §2.5, «video» line of the table",
        "dice":
            "⛔ The ban constrains **whoever sends**, and whoever receives cannot "
            "measure it: «before `SESSIONE`» is an order between **two independent "
            "QUIC streams**, and RFC 9000 does not order their delivery.  ⭐ The "
            "real quantity is a **local fact of the client**: if it has not "
            "yet sent `ATTACCA`, the server cannot have sent "
            "`SESSIONE` (§4.5 makes it the answer) — and the client knows this "
            "without hypotheses about the network, because it sent `ATTACCA` itself.",
        "era":
            "⛔ *«one per frame, and none before sending "
            "`SESSIONE`: whoever receives one before closes with "
            "`ERRORE_PROTOCOLLO`»* — and **«whoever receives one before»** is a "
            "substitute quantity: whoever receives has nothing else to measure than "
            "the order in which its own network layer delivers the "
            "events, and the two streams are independent.  ⚠ And it is the **sixth** "
            "of the family P8 -> P11 -> P13 -> P14 -> P19 -> P20 "
            "(`LEZIONI.md` §1.13).  ⛔ Even the first cure proposed — *«only "
            "if, when the frame arrives, the bytes of `SESSIONE` have not "
            "arrived yet»* — remains a substitute: it moves the measurement from the "
            "waking of the coroutine to the bytes, and the bytes are delayed by **the "
            "network** (a lost packet, a retransmission).  ⇒ It would be the "
            "seventh draft, and it would move by one step at the first "
            "hostile rereading.",
        # ⛔ And the ready-to-paste text sits here, not in a report: a
        #    bench that names a cure without carrying it is a complaint (§«the four
        #    outcomes»).  ⚠ It does not touch §9: no new type, no new field, no new
        #    value — `ATTACCA` and `SESSIONE` have been there since §4.5.
        "testo":
            "| **video** — unidirectional | the server | one **per "
            "frame**, ⛔ and **none before sending `SESSIONE`**. "
            "⚠ The ban constrains **whoever sends**: whoever receives cannot "
            "measure it on the order in which things arrive, because the "
            "control channel and the frame stream are **two independent "
            "QUIC streams** and nothing orders their delivery (§6.2).  ⇒ The "
            "client declares `ERRORE_PROTOCOLLO` **only** if it has not yet "
            "sent `ATTACCA`: §4.5 makes `SESSIONE` the answer to "
            "`ATTACCA`, so there the server **cannot** have sent it, and the "
            "client knows it without looking at the network.  ⛔ If `ATTACCA` has left "
            "and `SESSIONE` has not arrived yet the client **MUST NOT "
            "close**: it **holds back** the frame and writes it in the log, "
            "as for the size never in force of §6.2, and judges it when "
            "`SESSIONE` arrives — which arrives necessarily, because the control "
            "channel is reliable and ordered and §4.5 forbids the server to "
            "answer with a silence.  ⚠ And invariant **I3** stays "
            "whole: whoever has sent `ATTACCA` has already gone through `AMMESSO`, "
            "that is through the validator |",
        "casi": {
            "p20-sessione-in-ritardo": AMBIGUO,
            "p20-prima-di-attacca": ERRORE_PROTOCOLLO,
        },
    },
    # ⭐⛔⛔ AND THE **SEVENTH** OF THE FAMILY, FOUND BY THE HOSTILE REREADING OF
    #     13 AUG 2026 by lining up again the six that by now live together:
    #     P8 -> P11 -> P13 -> P14 -> P19 -> P20 -> **P21**.
    #     ⚠ On 13 Aug it was born as a finding **declared and not cured**
    #       (`RILIEVI_DICHIARATI`), without a case.  ⛔ It stayed there one round
    #       only: a finding that has a cure, three cases and a fault per direction
    #       **is no longer a finding, it is a proposal** — and the table it is
    #       written in is half of what it says.
    "P21": {
        "dove": "RCP.md §6.2 — **two paragraphs of the same section**, eight "
                "lines apart",
        "dice":
            "⛔ The frame at the size never in force **is held back** as long as "
            "there is an `ADATTA_TELA` that the client **itself sent** and that "
            "no `TELA` has answered yet; when that `TELA` arrives, the "
            "frame is **judged again** against the canvas the `TELA` declares. "
            "⛔ And if there is no request in flight nothing is held "
            "back: `ERRORE_PROTOCOLLO` **at once**, as §6.2 already says.  "
            "⭐ The quantity is **a request in flight**, not **the size "
            "requested**: §4.5 allows a granted canvas different from the one "
            "requested.",
        "era":
            "⛔ **Internal contradiction, and the two paragraphs are in the same "
            "section**: the one of **P19** says that a frame at the "
            "new size arrived **before** its `TELA` does not make it close — "
            "*«it holds back»* — and the tolerance one (**P11** + **P13**), "
            "eight lines below, says that a size *«that was never in "
            "force in that window»* is `ERRORE_PROTOCOLLO` **at once**.  "
            "⇒ On the same scene two conforming implementations send two different "
            "bytes: one `CONGEDO`, the other nothing.  ⚠ It is the form of **P10** "
            "— there however it was §5.2 against §6.2, **two sections**; here it is §6.2 "
            "against itself, ⛔ and the second line arrived **after** the first. "
            "⭐ And it differs from **D14/P8** in a point that counts: there the two "
            "implementations **converged** on the wrong byte and no "
            "comparison could disprove them, here they **diverge** — a "
            "comparison between two clients finds this one, and would find it in production.  "
            "⛔ And the first cure proposed was **the size the client "
            "named**, which is still a substitute: §4.5 says *«the granted canvas "
            "can differ from the requested one»* — on KWin < 6.8 "
            "it is the normal road (`SPECIFICHE.md` §6.3) and the PipeWire "
            "negotiation of §6.4 grants the mode the compositor **has** — and a "
            "client that held back only the numbers it named would close "
            "the session **one step further on**, which is the signature of this "
            "family from P8 onwards.  ⇒ It would have been the eighth draft.",
        # ⛔ The ready-to-paste text, and it **does not touch §9**: no new type,
        #    no new field, no new value — `ADATTA_TELA` and `TELA` have been there
        #    since §7.1, and the §9 clause has been used up since 10 Aug 2026.
        #    ⚠ They are TWO pieces, because the paragraphs that contradict each other are
        #      two: curing only one would leave the contradiction standing, which
        #      is the error P12 has already made us pay for (§3 in the singular while
        #      §6.2 had moved to the window).
        "testo":
            "⛔ **[1] Instead of the paragraph «The client MUST NOT close» and "
            "of the whole `[?]` box «until when it holds back»:**\n"
            "\n"
            "⛔ **The client MUST NOT close: it holds back the frame**, and "
            "writes it in the log.  ⭐ **And until when it holds it back is not a "
            "number: it is a condition** — as long as there is an `ADATTA_TELA` that "
            "**the client sent** and that no `TELA` has answered yet. "
            "Once that `TELA` has arrived, the held-back frame **is judged again** "
            "against the canvas that `TELA` declares in force, and from there it is a "
            "frame like all the others: first the order rule, then "
            "the size rule.  ⛔ **And if no `ADATTA_TELA` is without an "
            "answer nothing is held back**: a size the client has "
            "no reason to expect is `ERRORE_PROTOCOLLO` at once, as "
            "the tolerance paragraph below says.\n"
            "\n"
            "⚠ **And the `TELA` necessarily arrives**, which is the reason why "
            "this is an end and not an open wait: §7.1 requires *«to every "
            "`ADATTA_TELA` the server MUST answer with a `TELA`, successful or "
            "not»*, and the control channel is **a single one, reliable and "
            "ordered** (§4.2) ⇒ the n-th `TELA` answers the n-th "
            "`ADATTA_TELA`, and whoever drags a window sends two without "
            "the count getting lost.  ⛔ A `TELA(RIFIUTATA)` ends the wait as much as "
            "a `TELA(ADATTATA)`: the held-back frame is judged again against "
            "the canvas that stayed in force, and as a rule **it is `ERRORE_PROTOCOLLO`** — "
            "the server sent a size it never had.\n"
            "\n"
            "⭐ **And the quantity is «a request in flight», not «the size "
            "the client asked for»**: §4.5 says that *«the granted canvas can "
            "differ from the requested one»* — on KWin < 6.8 it is the "
            "normal road (`SPECIFICHE.md` §6.3) and the negotiation of §6.4 grants "
            "the mode the compositor **has**.  ⇒ A client that held back "
            "only the numbers it named would close a session in which the "
            "server did exactly what §7.1 allows it.  ⚠ It is the "
            "same quantity as **P20** — *what the client itself sent*: "
            "local, monotonic, independent of delivery.\n"
            "\n"
            "⛔ **[2] At the end of the paragraph «The canvas change and the frames in "
            "flight», instead of «and so is at once a size that was never "
            "in force in that window»:**\n"
            "\n"
            "and so is **at once** a size that was never in force in "
            "that window ⛔ **and that no unanswered `ADATTA_TELA` "
            "can still grant**: if there is one, the frame **is held "
            "back** instead of making it close (the paragraph above).",
        "casi": {
            "p21-nominata-e-in-volo": AMBIGUO,
            "p21-concessa-diversa-da-chiesta": AMBIGUO,
            "p11-misura-mai-in-vigore": ERRORE_PROTOCOLLO,
        },
    },
}

# ⭐ AND THE TWO THIS TABLE HOSTED FOR ONE ROUND ONLY, with the date:
#    **P10** and **P11**, born `AMBIGUO` on the evening of 12 Aug 2026 and turned
#    into lines of `RCP.md` a few hours later — §5.2 (the client reconfigures on the first
#    KEYFRAME) and §6.2 (the window instead of «the previous one»).  ⛔ Their cases
#    now sit in `REGOLE_NUOVE` and in `REGOLE_DI_STATO`, with today's
#    expectation: a case that stayed here would be judging yesterday's document.


# ===========================================================================
# ⛔⛔ THE **DECLARED** FINDINGS: points where `RCP.md` decides, and the decision
#     does not hold — or is not the same in two sections.
#
#     ⚠ They are not `AMBIGUO` and they are not proposals with a case that triggers them:
#       the document **has** an answer, and the bench applies it.  ⛔ But
#       applying it and keeping silent about the fact that it kills a healthy session would be
#       form **E8** turned against whoever reads the bench.  ⇒ They are printed at
#       the end of every round, with the concrete scene and the case that shows them —
#       or with «no case», declared.
#     ⛔ And nothing is cured here: `RCP.md` belongs to the coordinator, and on the evening of
#       12 Aug 2026 three lines applied in a hurry cost three rounds.
RILIEVI_DICHIARATI = {
    "P15": {
        "dove": "RCP.md §7.1 — the grace on the **input coordinates**, which "
                "stayed «for one second»",
        "dice": "The same wrong quantity that P13 removed from §6.2 is "
                "still in §7.1 for the opposite direction of the wire: the server "
                "tolerates **for one second** the coordinates valid on the previous "
                "canvas, and then closes.",
        "scena": "the uplink is the weak direction (ADSL, mobile) and the QUIC "
                 "streams share the congestion window: an input sent "
                 "before the `TELA` can arrive **after** the second, and the "
                 "server closes a session in which the client made no mistake "
                 "— invariant **I1** again.  ⚠ `[?]` **and the P13 cure "
                 "does NOT carry over**: for frames the end is an observable "
                 "fact (the keyframe at the new size), for coordinates "
                 "there is nothing equivalent — a coordinate can be "
                 "valid on both canvases, and the server cannot tell it apart",
        "caso": None,
        "marca": "[?] not measured, and **not of this chapter**: §7.1 is "
                 "input, and this bench judges the video channel",
    },
    # ⭐⛔⛔ AND THIS ONE WAS FOUND BY THE HOSTILE REREADING OF 13 AUG 2026, the one
    #     that lined up again the SEVEN lines of the family — P8, P11, P13,
    #     P14, P19, P20, P21 — to see whether an eighth was left.  ⛔ One
    #     was left, and it is not inside §6.2: it is in §3, and it is **the exact form
    #     of P12**, one step further on.
    #     ⚠ **Declared and not cured, and the cure is NOT tried here**: two cures in
    #       one round are the hurry that on 12 Aug cost three rounds, and
    #       this round already carries one (P21).
    "P22": {
        "dove": "RCP.md §3 — the list of exceptions, against §2.5 and §6.2",
        "dice":
            "§3 declares *«the exceptions are **six**, and they are all here.  Outside "
            "this list none are invented»* ⛔ and **HOLDING BACK is not "
            "among the six**.  But §2.5 (**P20** cure, 13 Aug) says that a "
            "frame arrived before `SESSIONE` *«MUST NOT»* make it close: "
            "**it is held back**; and §6.2 (**P19** cure, 12 Aug) says the "
            "same thing of the frame at the size never in force.  ⇒ They are "
            "**two tolerances commanded by two normative sections** and absent "
            "from the list that declares itself complete.  ⚠ Exception 6 does not "
            "cover them: it talks about the frames carrying *«a size that WAS "
            "in force»*, that is the opposite case.",
        "scena": "a client written reading §3 — *«outside this list none "
                 "are invented»* — closes with `ERRORE_PROTOCOLLO` the "
                 "frame §2.5 and §6.2 order it to hold back; one "
                 "written reading §2.5 holds it back.  ⛔ Two conforming "
                 "implementations, two different bytes, and the one that closes kills "
                 "**precisely the healthy session** P19 and P20 were written "
                 "to save.  ⭐ It is the form of **P12** — §3 left behind "
                 "while §6.2 went ahead — with a difference that makes it "
                 "worse: there §3 was NARROWER than the same tolerance, "
                 "here the tolerance in §3 **is not there at all**.  ⛔ And the cure "
                 "of **P21**, when it goes in, adds a third one to the "
                 "same list: applying it without touching §3 leaves the wound "
                 "open exactly as on 12 Aug",
        "caso": None,
        "marca": "[R] contradiction confirmed by two lines already written (§3 "
                 "against §2.5 and §6.2).  ⛔ **No case**: this bench judges "
                 "the frame with the reading of §6.2, and a case that "
                 "required the reading of §3 would judge an imaginary "
                 "client — it is declared instead of fabricated",
    },
}

# ⭐⛔ AND THIS TABLE HOSTED ONE FOR ONE ROUND ONLY: **P21**, born here on
#    13 Aug 2026 — «§6.2 commands the opposite of itself eight lines
#    apart» — and moved to `PROPOSTE_APERTE` the round after, with the text
#    ready, three cases and two faults.  ⛔ The move is not bookkeeping: a
#    finding is a **reading**, a proposal is a **cure with the cases that
#    keep it honest**, and this bench says which of the two it is delivering
#    (`REVIEWER.md` §4).  ⚠ And the discriminant the finding proposed —
#    *«the size the client named»* — the check with the concrete case
#    **rejected**: §4.5 allows a granted canvas different from the one
#    requested.  See `p21-concessa-diversa-da-chiesta` and fault **G14**.

# ⭐ AND THIS TABLE EMPTIED ON 12 AUG 2026, like the proposals
#    one: **P12** (§3 line 6 left in the singular while §6.2 had moved
#    to the window) and **P13** (the grace second, which was the wrong
#    quantity) were cured in the round after being written here.
#    ⛔ It stays, empty and declared: a round that prints nothing and a round that
#    has nothing to print are two different facts, and it is form E8
#    turned against the bench.

def rilievi_col_caso(casi):
    """⛔ Which declared findings have a case that shows them, and which do not.

    ⚠ «It has no case» is not «it does not count»: it is a fact that is printed.  A
      finding without a case stays a reading, and this bench says which of the two
      things it is delivering (`REVIEWER.md` §4: a finding without «how it is
      proved» is a hypothesis).
    """
    per_nome = {c["nome"] for c in casi}
    con, senza = [], []
    for sigla, r in RILIEVI_DICHIARATI.items():
        if r["caso"] and r["caso"] in per_nome:
            con.append(sigla)
        else:
            senza.append(sigla)
    return con, senza


def proposte_coperte(casi):
    """⛔ Like `regole_coperte`, for the proposals the document does not have yet.

    ⚠ The difference lies in the **form of the pair**: a line already entered
      has a case that violates it (`ERRORE_PROTOCOLLO`) and one that respects it
      (`ACCETTATO`); an open proposal has the case that **shows** it —
      today `AMBIGUO`, because the document has not decided yet — and those that
      prevent writing it **too broadly**.  ⛔ Requiring here the same
      form as there would mean pretending the cure is already applied.
    """
    per_nome = {c["nome"]: c for c in casi}
    coperte, mancanti = [], []
    for sigla, p in PROPOSTE_APERTE.items():
        buchi = []
        for nome, atteso in p["casi"].items():
            c = per_nome.get(nome)
            if c is None:
                buchi.append(f"the case «{nome}» is missing")
            elif c["atteso"] != atteso:
                buchi.append(f"«{nome}» does not require {atteso} but {c['atteso']}")
        if buchi:
            mancanti.append((sigla, "; ".join(buchi)))
        else:
            coperte.append(sigla)
    return coperte, mancanti


def regole_di_stato_coperte(casi):
    """⛔ Like `regole_coperte`, for the lines that talk about the **client's
       state** instead of the bytes — today only **P10**.

    ⚠ The pair has a different form, and it is the point: both cases come out
      `ACCETTATO`, because on the wire nobody made a mistake.  What changes is the
      **finding**: the case that violates the line must carry it, ⛔ and the one that
      respects it **must not carry it** — which is the same rule of the two
      halves of the mark (R12-A.3), applied to a finding instead of a
      fault.
    """
    per_nome = {c["nome"]: c for c in casi}
    coperte, mancanti = [], []
    for sigla, r in REGOLE_DI_STATO.items():
        buchi = []
        for chi, nome in (("VIOLATES", r["viola"]), ("RESPECTS", r["rispetta"])):
            c = per_nome.get(nome)
            if c is None:
                buchi.append(f"the case that {chi} it is missing («{nome}»)")
            elif c["atteso"] != ACCETTATO:
                buchi.append(f"«{nome}» does not require ACCETTATO but {c['atteso']}"
                             f": a CLIENT defect does not make the wire drop")
        if buchi:
            mancanti.append((sigla, "; ".join(buchi)))
        else:
            coperte.append(sigla)
    return coperte, mancanti


def regole_coperte(casi):
    """⛔ How many of the entered lines REALLY have a case that triggers them.

    ⛔ The count is **computed** by this function by looking up the names among the cases: a
       number written by hand in a comment is the number nobody recomputes
       (`01-b5-violazioni.py`, finding R7.14 — three numbers in the comments and
       none of the three matched the file).

    Returns (covered, missing), where `mancanti` carries the tag and **which
    of the two halves** is missing: ⚠ «the rule is there but the case that respects it is not»
    and «the rule is not tested at all» are two different defects, and the first
    is the one that lets a rule written too broadly pass.
    """
    per_nome = {c["nome"]: c for c in casi}
    coperte, mancanti = [], []
    for sigla, r in REGOLE_NUOVE.items():
        # ⛔ «viola» can be ONE or MORE THAN ONE, and the difference is not one of
        #    convenience: **P8** has two halves to keep tight — the grace
        #    second and the size — and a rule that tested only one
        #    would stay green with the other written too broadly.
        nomi_viola = (r["viola"] if isinstance(r["viola"], (tuple, list))
                      else (r["viola"],))
        # ⛔ AND THE EXPECTED OUTCOME OF THE TWO HALVES IS DECLARED, not taken for
        #    granted: **P14** has the pair «discarded / really closes», and
        #    requiring `ERRORE_PROTOCOLLO` and `ACCETTATO` here would have meant
        #    that a rule with a different form cannot be counted —
        #    that is counting it wrong, or not counting it at all.
        att_v = r.get("esito_viola", ERRORE_PROTOCOLLO)
        att_s = r.get("esito_rispetta", ACCETTATO)
        s = per_nome.get(r["rispetta"])
        buchi = []
        for nome_v in nomi_viola:
            v = per_nome.get(nome_v)
            if v is None:
                buchi.append(f"the case that VIOLATES it is missing («{nome_v}»)")
            elif v["atteso"] != att_v:
                buchi.append(f"«{nome_v}» does not require {att_v} but "
                             f"{v['atteso']}")
        if s is None:
            buchi.append(f"the case that RESPECTS it is missing («{r['rispetta']}»)")
        elif s["atteso"] != att_s:
            buchi.append(f"«{r['rispetta']}» does not require {att_s} but "
                         f"{s['atteso']}")
        if buchi:
            mancanti.append((sigla, "; ".join(buchi)))
        else:
            coperte.append(sigla)
    return coperte, mancanti


# ===========================================================================
# THE CASES.  ⛔ Each one declares its EXPECTATION **before** measuring: the
#             «expected» column is a PREDICTION written in the file, not a comment on the
#             result (`LEZIONI.md` §1.11, `PIANO.md` §0.3 rule 4).
# ===========================================================================
CASI = []


def caso(nome, atteso, spiega, regola="", contesto=None, dove="uni"):
    def dec(f):
        CASI.append({"nome": nome, "atteso": atteso, "spiega": spiega,
                     "regola": regola, "contesto": contesto, "dove": dove,
                     "fabbrica": f})
        return f
    return dec


# ── The channel framing (§2.5) ─────────────────────────────────────────────
@caso("canale-controllo-su-uni", ERRORE_PROTOCOLLO,
      "the CONTROL channel (0x00) on a unidirectional stream of the server: "
      "«control lives only on the first bidirectional stream»",
      "RCP.md §2.5")
def _():
    return [struct.pack("!HI", 0x0001, 0) + b"\x00" * 22], "fin"


@caso("canale-audio-su-stream", ERRORE_PROTOCOLLO,
      "the AUDIO channel (0x04) on a stream: audio lives only on datagrams.  "
      "⚠ The payload is the well-formed header of §6.3 — the only wrong thing "
      "is the stream",
      "RCP.md §2.5, §6.3")
def _():
    return [struct.pack("!HHQ", 0x0401, 2, 0) + b"\x00" * 16], "fin"


@caso("canale-ignoto", ERRORE_PROTOCOLLO,
      "a high byte that is none of the five of §2.5",
      "RCP.md §2.5")
def _():
    return [intestazione(tipo=0x0901)], "fin"


@caso("video-sul-controllo", ERRORE_PROTOCOLLO,
      "⭐⛔ **P3, the case that VIOLATES it** — a WELL-FORMED frame written on the "
      "control channel.  ⛔ It is the only place where the server can "
      "get the stream wrong: §2.5 forbids it from opening bidirectional streams, and the "
      "control channel was opened for it by the client.  ⚠ Without the line of 12 "
      "Aug the client read those 28 bytes with the framing of §6.1 and "
      "derived an invented 64 KiB message from them",
      "RCP.md §2.5", dove="controllo")
def _():
    return [intestazione() + b"\x00" * 64], "fin"


@caso("video-su-unidirezionale", ACCETTATO,
      "⭐ **P3, the case that RESPECTS it** — the **very same bytes** of the "
      "case above, on a unidirectional stream of the server.  ⛔ Without "
      "this case, a judge that refused video **everywhere** — that is "
      "that had understood P3 as «video is not accepted» instead of «video "
      "only over there» — would stay green on the case that violates it",
      "RCP.md §6.2", dove="uni")
def _():
    return [intestazione() + b"\x00" * 64], "fin"


# ── The type and the codec (§6.2) ──────────────────────────────────────────
@caso("tipo-0x0300", ERRORE_PROTOCOLLO,
      "`tipo = 0x0300`: right channel, undefined value — §6.2 says «Other "
      "values: ERRORE_PROTOCOLLO»",
      "RCP.md §6.2")
def _():
    return [intestazione(tipo=0x0300) + b"\x00" * 64], "fin"


@caso("tipo-0x0303", ERRORE_PROTOCOLLO,
      "`tipo = 0x0303`: the value right after the two defined ones.  ⚠ It is the case "
      "that an `if (tipo >= 0x0301)` written in a hurry lets through",
      "RCP.md §6.2")
def _():
    return [intestazione(tipo=0x0303) + b"\x00" * 64], "fin"


@caso("codec-3", ERRORE_PROTOCOLLO,
      "`codec = 3`: RCP/1 defines two, 1 = HEVC and 2 = AV1",
      "RCP.md §6.2")
def _():
    return [intestazione(codec=3) + b"\x00" * 64], "fin"


@caso("codec-non-negoziato", ERRORE_PROTOCOLLO,
      "`codec = 2` (AV1) on a session where §4.3 had negotiated HEVC.  "
      "⛔ The field is well formed: the only violation is that it contradicts the "
      "negotiation, and it is the only rule a judge without context "
      "cannot apply",
      "RCP.md §6.2, §4.3")
def _():
    return [intestazione(codec=2) + b"\x00" * 64], "fin"


# ── The length, and FIN against RESET (§6.2) ───────────────────────────────
@caso("intestazione-27-byte", ERRORE_PROTOCOLLO,
      "⛔ **P4, the case that VIOLATES it** — FIN after 27 bytes: one fewer than the 28.  "
      "Read to the letter, «the end of the stream is the end of the frame» makes "
      "this a frame with **minus one** byte of data.  ⭐ Since 12 Aug "
      "2026 the rule is no longer derived from §3: §6.2 writes it",
      "RCP.md §6.2")
def _():
    return [intestazione()[:27]], "fin"


@caso("stream-vuoto", ERRORE_PROTOCOLLO,
      "FIN at zero bytes.  ⚠ It is the case where «zero» and «failure» "
      "look most alike: a stream opened and closed at once",
      "RCP.md §6.2")
def _():
    return [], "fin"


@caso("reset-a-meta", SCARTATO,
      "⭐ stream RESET after 10 KB: it is thrown away, ⛔ **not** handed to the "
      "decoder, and treated as a gap.  ⛔ And the session STAYS ALIVE: "
      "abandonment is the normal case of §5.1, not a violation",
      "RCP.md §6.2, §5.1, §5.2")
def _():
    return [intestazione(), b"\x00" * 10240], "reset"


@caso("reset-prima-dell-intestazione", SCARTATO,
      "stream reset after only 4 bytes.  ⛔ The judgement MUST look at the "
      "reset **before** the header: those four bytes can be "
      "anything, and reading them would give `ERRORE_PROTOCOLLO` on a frame "
      "the server abandoned on purpose",
      "RCP.md §6.2")
def _():
    return [b"\xff\xff\xff\xff"], "reset"


@caso("oltre-16-mib", ERRORE_PROTOCOLLO,
      "a frame of 16 MiB + 1 byte.  ⛔ And the judgement must arrive "
      "**while** the bytes flow, «instead of continuing to accumulate»",
      "RCP.md §6.2")
def _():
    def pezzi():
        yield intestazione()
        rimane = TETTO_FOTOGRAMMA - INTESTAZIONE + 1
        blocco = b"\x00" * (1 << 20)
        while rimane > 0:
            n = min(rimane, len(blocco))
            yield blocco[:n]
            rimane -= n
    return pezzi(), "fin"


@caso("16-mib-esatti", ACCETTATO,
      "⭐ a frame **exactly** 16 MiB long: the ceiling is a maximum, "
      "not a strict upper bound.  ⚠ Without this case «> 16 MiB» and "
      "«>= 16 MiB» give the same green on all the rest of the bench",
      "RCP.md §6.2")
def _():
    def pezzi():
        yield intestazione()
        rimane = TETTO_FOTOGRAMMA - INTESTAZIONE
        blocco = b"\x00" * (1 << 20)
        while rimane > 0:
            n = min(rimane, len(blocco))
            yield blocco[:n]
            rimane -= n
    return pezzi(), "fin"


# ── The state (§1, §3, I3) ─────────────────────────────────────────────────
@caso("prima-di-sessione", ERRORE_PROTOCOLLO,
      "⭐⛔ **P1, the case that VIOLATES it** — a well-formed frame **before "
      "`SESSIONE`**, that is before the canvas is agreed: the client "
      "would receive a frame of which it knows neither the size nor the "
      "codec.  It is invariant **I3** on the wire — *whoever does not go through the validator "
      "does not receive a pixel* — and since 12 Aug 2026 §2.5 writes it also for "
      "whoever **sends**",
      "RCP.md §2.5",
      # ⛔ THE CONTEXT BECAME EXPLICIT ON 13 AUG 2026, and the expectation did NOT
      #    change.  The case has always said *«before the canvas is
      #    agreed»*: the canvas is requested by the client with `ATTACCA` (§4.5),
      #    so the scene this case describes is the one **before**
      #    `ATTACCA`.  ⚠ Until today the field was not there and the case did not
      #    distinguish the two scenes — because nobody had seen that they were
      #    two.  ⭐ The verdict is `ERRORE_PROTOCOLLO` with today's line **and**
      #    with the P20 cure: it is the case on which the two readings
      #    agree, and that is why it stays here unchanged.
      contesto={"sessione_aperta": False, "attacca_spedito": False})
def _():
    return [intestazione() + b"\x00" * 64], "fin"


@caso("dopo-sessione", ACCETTATO,
      "⭐ **P1, the case that RESPECTS it** — the **very same bytes**, with "
      "`SESSIONE` already sent.  ⛔ Without this case the bench would not "
      "distinguish «video before `SESSIONE` drops» from «video drops», "
      "and the second reading makes phase 2 fail entirely",
      "RCP.md §6.2",
      contesto={"sessione_aperta": True})
def _():
    return [intestazione() + b"\x00" * 64], "fin"


# ── ⛔⛔ P20 — «before `SESSIONE`» measured by whoever RECEIVES ─────────────
#
#    ⭐ The sixth of the family P8 -> P11 -> P13 -> P14 -> P19 -> P20, and the
#      form is always that of `LEZIONI.md` §1.13: the line describes the
#      phenomenon with a **substitute quantity**.  Here the substitute is
#      *«the order in which the two streams reach me»*, and the real phenomenon is
#      *«the server had already sent `SESSIONE` when it opened this
#      stream»*.
#    ⛔ The two cases below are the pair, and the second is the one that counts:
#      a cure written too broadly passes the first and opens the second, and that is
#      how **P5** ended up wrong.
@caso("p20-sessione-in-ritardo", AMBIGUO,
      "⭐⛔ **P20, the case that RESPECTS it** — the **very same bytes** of "
      "`dopo-sessione`, and a server that did **everything** §2.5 and "
      "§5.2 require of it: it sent `SESSIONE` on the control channel and "
      "opened the stream of the first frame in the next line.  ⛔ The "
      "packet carrying `SESSIONE` is lost, the frame arrives whole, and a "
      "client applying §2.5 to the letter **closes a session in which "
      "nobody made a mistake** — invariant **I1** broken because the line "
      "loses packets, that is the condition I1 exists to protect.  "
      "⚠ §6.2 says twice that the streams are independent and that nothing "
      "orders their delivery (P14, P19): the same sentence §2.5 ignores here.  "
      "⭐⛔ **And the family is the INTERNAL CONTRADICTION, not the double "
      "reading**: whoever receives has no other quantity to measure than its "
      "own arrival order, so two careful implementations "
      "**converge on the same byte** — `CONGEDO(ERRORE_PROTOCOLLO)` on a "
      "healthy session — and no comparison between clients finds it.  ⚠ `[M]` 12 "
      "Aug 2026 it happened: the test client accused the server, and what "
      "disproved it was the referee of the **recording**, which has the wire "
      "order written inside and a live client does not",
      "RCP.md §2.5",
      contesto={"sessione_aperta": False, "attacca_spedito": True})
def _():
    return [intestazione() + b"\x00" * 64], "fin"


@caso("p20-prima-di-attacca", ERRORE_PROTOCOLLO,
      "⭐⛔ **P20, the case that VIOLATES it, and the one that prevents writing the "
      "cure TOO BROADLY** — the same frame, but the client **has not "
      "yet sent `ATTACCA`**.  §4.5 makes `SESSIONE` the **answer** to "
      "`ATTACCA` ⇒ a server that has not received it cannot have sent it, and "
      "the client knows it **without looking at the delivery order**: it sent it "
      "itself.  ⛔ Without this case, a cure in the form «the client never closes "
      "for a frame before `SESSIONE`» would stay green and "
      "would take away invariant **I3** — *whoever does not go through the validator does not "
      "receive a pixel* — which is the only reason the line exists",
      "RCP.md §2.5",
      contesto={"sessione_aperta": False, "attacca_spedito": False})
def _():
    return [intestazione() + b"\x00" * 64], "fin"


# ── The numbers (§6.2, §6.0, §7.1) ─────────────────────────────────────────
@caso("numero-zero", ERRORE_PROTOCOLLO,
      "⭐⛔ **P2, the case that VIOLATES it** — `numero = 0` on the first frame.  "
      "Since 12 Aug 2026 §6.2 reserves zero: **the first carries 1**.  ⚠ The "
      "concrete case the line closes: the client decodes frame 0, "
      "then sends `RICHIEDI_CHIAVE(ultimo_numero = 0)` — and the server cannot "
      "know whether it means «I decoded frame 0» or «I have not "
      "decoded any» (§7.1), that is the implicit sentinel that §6.0 "
      "forbids",
      "RCP.md §6.2")
def _():
    return [intestazione(num=0) + b"\x00" * 64], "fin"


@caso("numero-zero-al-giro", ERRORE_PROTOCOLLO,
      "⭐⛔ **P2 from the other side: the `0` that COMES BACK** — the frame after "
      "4294967295 carries `numero = 0`.  ⛔ It is the flaw P2 had left "
      "open for two hours: it reserved `0` and did not say that when the "
      "counter wraps it must be **skipped**, so the reserved value came back into circulation "
      "by itself after two years and two months of session.  ⚠ The symptom would have "
      "arrived **only once in the life of a session**, and nobody "
      "would have connected it to `RICHIEDI_CHIAVE`.  Closed by §6.2 on 12 Aug "
      "2026: from `0xFFFFFFFF` it goes to `1`",
      "RCP.md §6.2",
      contesto={"ultimo_consegnato": 0xFFFFFFFF, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=0) + b"\x00" * 64], "fin"


@caso("numero-uno", ACCETTATO,
      "⭐ **P2, the case that RESPECTS it** — `numero = 1` on the first frame, "
      "which is the value §6.2 requires.  ⛔ It is also the case that keeps "
      "the comparison honest: a judge that refused **every** low `numero` "
      "would look very strict and would be broken",
      "RCP.md §6.2")
def _():
    return [intestazione(num=1) + b"\x00" * 64], "fin"


@caso("misura-diversa-dalla-tela", ERRORE_PROTOCOLLO,
      "⭐⛔ **P5, the case that VIOLATES it** — a 1280x720 frame on a canvas in "
      "force of 1920x1080, and ⛔ **no `ADATTA_TELA` before**.  Since 12 Aug "
      "2026 §6.2 says that `largh.` and `altezza` **MUST** match the canvas in "
      "force, and that whoever receives others closes.  ⚠ Before, the two readings were "
      "both defensible — close by §3, or rescale as the client already "
      "does for the **view**",
      "RCP.md §6.2")
def _():
    return [intestazione(lar=1280, alt=720) + b"\x00" * 64], "fin"


@caso("misura-dopo-adatta-tela", ACCETTATO,
      "⭐⛔ **P5, the case that RESPECTS it, and it corrected `RCP.md`** — the "
      "**very same bytes** of the case above, but before it a "
      "`TELA(ADATTATA, 1280, 720)` passed on the control channel (§7.1).  ⛔ For two "
      "hours §6.2 said «the canvas granted in `SESSIONE`», and with that line "
      "this case would be `ERRORE_PROTOCOLLO`: the client would have killed the "
      "session because the user dragged a window — which is "
      "**exactly** the scene §7.1 protects with its exception 4.  "
      "⚠ Without this case the new rule would be as strict as the "
      "wrong one before, and no bench would say so",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720)})
def _():
    return [intestazione(lar=1280, alt=720) + b"\x00" * 64], "fin"


@caso("misura-uguale-a-una-tela-diversa", ACCETTATO,
      "⭐⛔ **P5, the case that RESPECTS it, and it is not the default frame** "
      "— 1280x720 on a **granted** 1280x720 canvas.  ⛔ They are the **same "
      "bytes** of the case that violates it: only the canvas agreed in "
      "`SESSIONE` changes.  ⚠ Without this case, a judge that had written "
      "`if (lar, alt) != (1920, 1080)` — that is the default size instead "
      "of the granted canvas — would be green on all twenty-seven other "
      "cases, and red on the first 720p session",
      "RCP.md §6.2",
      contesto={"tela": (1280, 720)})
def _():
    return [intestazione(lar=1280, alt=720) + b"\x00" * 64], "fin"


# ── ⛔⛔ D14 — THE FRAMES IN FLIGHT, and proposal **P8** ────────────────────
#    The three cases must be read together: the first shows the healthy session killed,
#    the second and the third prevent curing it with a rule too broad.
@caso("p8-in-volo-dopo-adatta-tela", ACCETTATO,
      "⭐⛔ **P8, THE CASE THAT RESPECTS IT — AND IT IS THE SCENE THAT KILLED A "
      "HEALTHY SESSION** — the canvas was 1920x1080, a `TELA(ADATTATA, "
      "1280, 720)` passed (§7.1), and now the frame **opened before** arrives, which "
      "carries 1920x1080.  ⛔ Until tonight §6.2 to the letter said "
      "`ERRORE_PROTOCOLLO` — while §6.2 **itself** says that «the streams are "
      "independent, so frames can arrive out of order» — and "
      "this case came out `AMBIGUO` because neither of the two sides had "
      "made a mistake.  ⭐ Since the evening of 12 Aug 2026 the one-second grace is "
      "a line of §6.2 and the **sixth exception** of §3: it is ACCEPTED, painted "
      "**rescaled**, ⛔ and §3 requires the tolerance to be **written in the "
      "log** — this case checks that too, because «a silent tolerance "
      "is indistinguishable from a defect»",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720)})
def _():
    return [intestazione(lar=1920, alt=1080, num=41) + b"\x00" * 64], "fin"


@caso("p13-vecchia-dopo-la-chiave-nuova", ERRORE_PROTOCOLLO,
      "⭐⛔ **P13, the case that VIOLATES it — and the tolerance is not a permanent "
      "permit** — the **very same bytes** of the case above, but the "
      "**keyframe at the new size has already arrived**: the queue has drained.  "
      "⛔ From there on a frame at the old size is no longer one in "
      "flight: it is a server that goes on capturing at a canvas no longer "
      "in force, and it is §6.2 without discounts.  ⭐ And the end of the tolerance is an "
      "**observable fact on the wire**, not a declared time: until the "
      "P13 cure this case had to announce «the second has passed», that is a "
      "thing that is not on the wire — and that a referee reading a "
      "recording could not see",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720),
                "chiave_alla_tela_nuova": True, "ultimo_consegnato": 41,
                "chiave_consegnata": True})
def _():
    # ⛔ `numero` **42**, that is AFTER the keyframe at the new size: it is not a
    #    frame in flight — those were captured before and carry lower
    #    numbers — it is a server that went on capturing at the old
    #    canvas.  ⚠ The number here is half of the case, and without it it would be the
    #    scene of finding **P14**, which is another thing.
    return [intestazione(lar=1920, alt=1080, num=42) + b"\x00" * 64], "fin"


@caso("p14-in-volo-scavalcato-dalla-chiave", SCARTATO,
      "⭐⛔⛔ **P14, THE CASE THAT EXERCISES IT — and until an hour ago the "
      "session dropped here** — the keyframe at the new size (`numero` 41) has already "
      "arrived, and now the frame **in flight** arrives carrying the old "
      "size and ⛔ **a LOWER number** (40): it was captured **before** "
      "the `TELA`.  ⚠ It is the normal scene, not the rare one: the old "
      "frame is the biggest — §5.2 forbids the server to abandon a "
      "keyframe — and the streams are independent, so the new keyframe, "
      "smaller, **overtakes it**.  ⛔ Before the cure the size was looked at "
      "first and the verdict was `ERRORE_PROTOCOLLO`: a session dropped in which "
      "nobody had made a mistake.  ⭐ Now §6.2 says that **order comes before "
      "size**: it is DISCARDED, «and its size is not even looked at» — and "
      "the session stays alive, which is what §5.1 asks for a frame "
      "arrived late",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720),
                "chiave_alla_tela_nuova": True, "ultimo_consegnato": 41,
                "chiave_consegnata": True})
def _():
    return [intestazione(lar=1920, alt=1080, num=40) + b"\x00" * 64], "fin"


@caso("p13-linea-lenta", ACCETTATO,
      "⭐⛔⛔ **P13, THE CASE THE CURE EXISTS FOR — the slow line** — the "
      "**very same bytes** of the frame in flight, and the case declares one "
      "thing more: ⛔ **the second passed long ago**.  The 1920x1080 "
      "keyframe opened an instant before the `TELA` weighs a few MiB (§6.2 "
      "allows 16) and the line carries little — and bad lines are **inside** "
      "the model: the minimum of `CODER.md` §1 is 480p at 25.  ⛔ With the line "
      "by the clock the client closed a frame sent when it was legal, and "
      "which §5.2 forbade the server to abandon: it is not only a healthy session "
      "dropping, it is invariant **I1** — «never to cut off» — broken "
      "**because the line is slow**, that is in the exact condition I1 "
      "exists to protect.  ⭐ Now the tolerance ends at the **keyframe**, "
      "and the keyframe has not arrived yet: it is ACCEPTED.  ⚠ The time declared "
      "here **no longer decides anything** — only fault "
      "**G10**, «the judge with the clock», puts it back in charge, and then this case turns red again: "
      "that is how the cure proves itself instead of telling itself",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720),
                "secondo_passato": True})
def _():
    return [intestazione(lar=1920, alt=1080, num=41) + b"\x00" * 64], "fin"


@caso("p8-misura-di-nessuna-tela", ERRORE_PROTOCOLLO,
      "⭐⛔ **P8 covers ONE size, not «everything for one second»** — same scene "
      "and same grace open, but the frame carries 800x600: ⛔ neither the canvas "
      "in force (1280x720) nor the previous one (1920x1080).  It is not a "
      "frame in flight, it is a wrong field — §6.2 closes, and it must "
      "close.  ⚠ Without this case a grace written «during the canvas "
      "change the size is not checked» would pass the case that kills and "
      "switch off P5 in the window where the server is most likely to "
      "err.  ⭐ It is the second half the first draft of P5 was missing",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720)})
def _():
    return [intestazione(lar=800, alt=600, num=41) + b"\x00" * 64], "fin"


# ── ⭐⛔ P10 AND P11 — THE TWO CURES OF THE **SECOND** ROUND OF THAT EVENING ──
#    ⚠ These four cases were born `AMBIGUO`, on the evening of 12 Aug: they were the two
#      points where the cures of D13 and D14, just applied, did not hold.  ⛔ The
#      coordinator applied both cures in the next round, and here the cases
#      **moved to verdict** — which is the only thing that closes the circle.
@caso("p10-decodificatore-al-tela", ACCETTATO,
      "⭐⛔ **P10, the case that VIOLATES it — and the violation is the CLIENT's, not "
      "the wire's** — same scene as the frame in flight, with **one more thing "
      "declared**: the client reconfigured the decoder to "
      "1280x720 when the `TELA` arrived.  ⛔ Until tonight's line here "
      "§6.2 said «accept it and paint it» and §5.2 «throw it away», and this case "
      "came out `AMBIGUO`.  ⭐ Now §5.2 says two things that close it: the "
      "client reconfigures **on the first KEYFRAME at the new size, not on the "
      "`TELA`**, and does not hand over a frame of the wrong size «**nor the one "
      "tolerated by §6.2**».  ⇒ The frame is ACCEPTED — on the wire nobody "
      "made a mistake — ⛔ and the bench prints a **FINDING ON THE CLIENT**: that "
      "decoder is where §5.2 forbids it to be, and `[M]` paints "
      "a wrecked image without raising an error.  ⚠ The finding is not "
      "the outcome: promoting it would drop a session in which the server is "
      "conforming",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720),
                "decodificatore_a": (1280, 720)})
def _():
    return [intestazione(lar=1920, alt=1080, num=41) + b"\x00" * 64], "fin"


@caso("p10-decodificatore-alla-chiave", ACCETTATO,
      "⭐ **P10, the case that RESPECTS it** — the **very same bytes**, and the "
      "client is where §5.2 wants it: the decoder is still at 1920x1080 "
      "because the keyframe at the new size has not arrived yet.  ⛔ The "
      "size of the frame and that of the decoder **coincide**, so "
      "there is nothing to report — and the bench checks it: the finding of the "
      "case above **must not appear** here.  ⚠ Without this half, a "
      "bench that always printed the finding would be green on both and would not "
      "tell the conforming client from the one that is not",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720),
                "decodificatore_a": (1920, 1080)})
def _():
    return [intestazione(lar=1920, alt=1080, num=41) + b"\x00" * 64], "fin"


@caso("p11-due-tele-nella-finestra", ACCETTATO,
      "⭐⛔ **P11, the case that RESPECTS it — and the scene is the one that killed "
      "a healthy session one step further on** — 1920x1080, `TELA(ADATTATA, "
      "1600, 900)`, and 200 ms later `TELA(ADATTATA, 1280, 720)`: whoever drags "
      "a window sends two.  The **keyframe** opened before everything arrives, "
      "carrying 1920x1080: ⛔ it is not the canvas in force and it is not **the** "
      "previous one, and §6.2 in the singular said `ERRORE_PROTOCOLLO` **at once**.  "
      "⭐ Since tonight's line the grace covers «a canvas that was in "
      "force within the **second just passed**», and this one was: it is "
      "ACCEPTED, with the tolerance declared.  ⚠ And it is precisely the keyframe that "
      "stays in flight longest — it is the biggest, and §5.2 forbids the server "
      "to abandon it",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080),
                "adatta_tela": [(1600, 900), (1280, 720)]})
def _():
    return [intestazione(lar=1920, alt=1080, num=41) + b"\x00" * 64], "fin"


@caso("p11-misura-mai-in-vigore", ERRORE_PROTOCOLLO,
      "⭐⛔ **P11, the case that VIOLATES it, and without it the cure is broad** — "
      "**same two-`TELA` scene** as the case above, but the frame carries "
      "800x600: ⛔ a size that **in that window was never in "
      "force** — not 1920x1080, not 1600x900, not 1280x720.  §6.2 says "
      "`ERRORE_PROTOCOLLO` **at once**, and it must say it.  ⚠ Without this case, a "
      "window written «during the second the size is not checked» "
      "would pass the case above and switch off P5 **right** where the server "
      "is most likely to err.  ⛔ It is the second half the first "
      "draft of P5 was missing, and that cost P8 two rounds",
      "RCP.md §6.2",
      # ⛔ THE CONTEXT BECAME EXPLICIT ON 13 AUG 2026 — proposal
      #    **P21** — and the expectation did NOT change.  ⭐ The field that decides is
      #    `adatta_in_volo`, and here it is **empty**: both `TELA`s have
      #    arrived, so there is no request of the client that 800x600
      #    could still grant.  ⇒ It is the case that keeps the P21 cure TIGHT:
      #    without it, *«always hold back»* would stay green on the whole
      #    bench and would take away the P11 line, that is the defence right where
      #    the server is most likely to err.  Fault **G15**.
      contesto={"tela": (1920, 1080),
                "adatta_tela": [(1600, 900), (1280, 720)],
                "adatta_spedito": []})
def _():
    return [intestazione(lar=800, alt=600, num=41) + b"\x00" * 64], "fin"


# ── ⭐⛔⛔ P21 — THE TWO LINES OF §6.2 THAT COMMAND THE OPPOSITE ────────────
#    ⚠ The P21 pair is made of **three** cases, like that of P8, and for the same
#      reason: a cure can be wrong in two directions, and the scene that
#      motivated it passes both.  The third case is the one against which the
#      cure **as it was proposed** broke.
@caso("p21-nominata-e-in-volo", AMBIGUO,
      "⭐⛔ **P21, THE CASE THAT SHOWS IT** — `SESSIONE` 1920x1080, a "
      "`TELA(ADATTATA, 1600, 900)` passed, the client sends `ADATTA_TELA(1280, 720)` "
      "and ⛔ **the 1280x720 frame arrives BEFORE the answer**: the streams "
      "are independent and §6.2 says it twice.  ⇒ Eight lines of §6.2 "
      "command the opposite on the same frame — the paragraph of **P19** "
      "says *«MUST NOT close: hold back»*, the tolerance one (**P11** "
      "+ **P13**) says `ERRORE_PROTOCOLLO` **at once** for a size never in "
      "force in that window.  ⛔ Two conforming implementations, two different "
      "bytes, and one of the two kills a session in which **nobody** made a "
      "mistake: the server captured at the size it is about to grant, "
      "as §5.2 requires it to (the keyframe at every canvas change).  ⭐ And the "
      "cure is not an open wait: §7.1 requires a `TELA` for **every** "
      "`ADATTA_TELA`, «successful or not»",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1600, 900),
                "adatta_spedito": (1280, 720)})
def _():
    return [intestazione(lar=1280, alt=720, num=41) + b"\x00" * 64], "fin"


@caso("p21-concessa-diversa-da-chiesta", AMBIGUO,
      "⭐⛔⛔ **P21, THE CASE THAT PREVENTS WRITING THE CURE TOO NARROWLY — "
      "and it rejected the discriminant as it had been proposed** — same scene, "
      "but the client asked for `ADATTA_TELA(1366, 768)` and the frame that "
      "arrives before the answer carries **1280x720**, which is the size the "
      "compositor will grant.  ⛔ The client never **named** that number: "
      "the cure written *«hold back the size the client "
      "named»* closes the session here, and §4.5 says plainly that *«the "
      "granted canvas can differ from the requested one»* — on KWin < 6.8 it is "
      "**the normal road** (`SPECIFICHE.md` §6.3), and the negotiation of §6.4 "
      "grants the mode the compositor **has**, not the one that was asked for. "
      "⇒ The defect moves by one step, which is the signature of this family "
      "from P8 onwards (`LEZIONI.md` §1.13): the real quantity is not **the size "
      "requested**, it is **a request in flight**.  ⭐ And it is the same form as "
      "P20, where the quantity is `ATTACCA` and not the canvas `ATTACCA` asks for",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1600, 900),
                "adatta_spedito": (1366, 768)})
def _():
    return [intestazione(lar=1280, alt=720, num=41) + b"\x00" * 64], "fin"


# ── ⭐⛔ D13 — THE KEYFRAME AT EVERY CANVAS CHANGE (§5.2), tonight's line ────
@caso("d13-delta-alla-misura-nuova", ERRORE_PROTOCOLLO,
      "⭐⛔ **P9, the case that VIOLATES it** — after a `TELA(ADATTATA, 1280, 720)` "
      "the first frame at the **new** size is a **delta**.  ⛔ `[M]` 12 "
      "Aug 2026, bench `02-pagina-tela-*`: with only deltas at the new size "
      "**Chrome on HEVC emits 5 frames, all declared at the OLD "
      "size, paints them, and raises NO error** — torn "
      "image, 7/8 on the old pattern.  ⚠ AV1 protests (`EncodingError`) "
      "in all four cells: ⇒ the rule is needed because **on the main "
      "codec the symptom is silent**, and the symptom would be «the desktop "
      "tears when I resize the window»",
      "RCP.md §5.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720),
                "ultimo_consegnato": 40, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, lar=1280, alt=720, num=41)
            + b"\x00" * 64], "fin"


@caso("d13-chiave-alla-misura-nuova", ACCETTATO,
      "⭐ **P9, the case that RESPECTS it** — the **very same bytes**, with "
      "`tipo = 0x0301`.  ⛔ Without this case a rule written «after a "
      "`TELA` nothing is accepted» would stay green on the one that violates it.  "
      "⚠ And this bench judges **less** than what §5.2 says: it sees that it is "
      "a keyframe, ⛔ **it cannot see whether it is a *real* keyframe** — the "
      "VPS/SPS/PPS in front of the IDR sit in the data, and this judge does not keep "
      "the data.  That half is measured by `02-codifica-nal.py` and "
      "`02-pagina-tela-*`, and it is written here so as not to make it look covered",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720),
                "ultimo_consegnato": 40, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=CHIAVE, lar=1280, alt=720, num=41)
            + b"\x00" * 64], "fin"


@caso("d13-tela-che-non-cambia", ACCETTATO,
      "⭐⛔ **P9, the third face: a `TELA` that does NOT change the size opens "
      "no debt** — §7.1 makes `TELA` answer **every** `ADATTA_TELA`, "
      "including the one asking for the size already there; here the canvas stays "
      "1920x1080 and a delta at 1920x1080 arrives.  ⛔ Without this case, a "
      "judge that opened the keyframe debt at every `TELA(ADATTATA)` "
      "instead of at every **change** of size would be green on the whole bench "
      "and red on the first session in which the user drags a window and puts it "
      "back where it was.  ⚠ And it is a red on a **healthy** session, that is the "
      "family that has already broken P5 and D14",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1920, 1080),
                "ultimo_consegnato": 40, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, lar=1920, alt=1080, num=41)
            + b"\x00" * 64], "fin"


@caso("d13-delta-dopo-la-chiave-nuova", ACCETTATO,
      "⭐⛔ **P9, the second face: the debt is paid ONCE** — the keyframe "
      "at the new size has already been delivered, and now a delta at "
      "1280x720 arrives.  ⛔ Without this case, a judge that had understood §5.2 as "
      "«after a `TELA` deltas are not accepted» would be green on the whole "
      "bench and would stop the video **after every resize**, that is "
      "exactly where phase 3 lives",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720),
                "ultimo_consegnato": 40, "chiave_consegnata": True,
                "chiave_alla_tela_nuova": True})
def _():
    return [intestazione(tipo=DELTA, lar=1280, alt=720, num=41)
            + b"\x00" * 64], "fin"


@caso("primo-fotogramma-delta", ERRORE_PROTOCOLLO,
      "⭐⛔ **P6, the case that VIOLATES it, and it bites right in this phase** — the "
      "FIRST frame of the session is a delta.  Since 12 Aug 2026 §5.2 "
      "wants a keyframe.  ⚠ Before, it conformed to **every line** of the document, "
      "and the client had no way of noticing: no gap in the `numero`s "
      "(it is the first) and the decoder raises no errors on an orphan delta "
      "— the symptom would have been *«the desktop appears in pieces»*, which "
      "names neither the protocol nor the keyframe",
      "RCP.md §5.2")
def _():
    return [intestazione(tipo=DELTA) + b"\x00" * 64], "fin"


@caso("primo-fotogramma-chiave", ACCETTATO,
      "⭐ **P6, the case that RESPECTS it** — the first frame of the session "
      "is a keyframe (`0x0301`).  ⛔ It is the frame phase 2 exists to "
      "deliver, and it is here with its name so that the line of §5.2 has two "
      "faces and not one",
      "RCP.md §6.2")
def _():
    return [intestazione(tipo=CHIAVE) + b"\x00" * 64], "fin"


@caso("delta-dopo-la-chiave", ACCETTATO,
      "⭐⛔ **P6, the second face: a delta that is NOT the first** — keyframe 4 "
      "already delivered, delta 5 arrives.  ⚠ Without this case, a judge "
      "that had understood §5.2 as «deltas are not accepted» instead of «the "
      "FIRST must be a keyframe» would stay green on the whole bench — and "
      "would stop the video from phase 3 on, where deltas are 99 % of the "
      "frames",
      "RCP.md §6.2",
      contesto={"ultimo_consegnato": 4, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=5) + b"\x00" * 64], "fin"


@caso("fuori-ordine", SCARTATO,
      "frame 7 arrives after 9 has been delivered: it is discarded.  "
      "⛔ And it is DISCARDED, not closed: the streams are independent and "
      "frames out of order are the normal case of §5.1",
      "RCP.md §6.2",
      contesto={"ultimo_consegnato": 9, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=7) + b"\x00" * 64], "fin"


@caso("ripetuto", SCARTATO,
      "the same `numero` twice: the signed difference is zero, which "
      "is not «following».  ⚠ Without this case a `d < 0x80000000` lets "
      "the duplicate through and the decoder receives the same "
      "frame twice",
      "RCP.md §6.2",
      contesto={"ultimo_consegnato": 9, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=9) + b"\x00" * 64], "fin"


@caso("modulo-2-32", ACCETTATO,
      "⭐ frame **1** after 4294967295: it is **following**, not "
      "preceding.  §6.2 wants modulo 2^32 arithmetic with signed "
      "differences, ⛔ and a direct `<` comparison would make it discard **every** "
      "frame after the wrap, forever — at 60 per second the counter wraps "
      "after two years and two months, and a session can last longer.  ⭐⛔ And "
      "that after `0xFFFFFFFF` comes **1 and not 0** is now a LINE of §6.2 — "
      "*«when the counter wraps 0 is skipped»*, added on 12 Aug 2026 — "
      "while until that day it was a choice of this bench: P2 reserved "
      "`0` and no line prevented the counter from passing over it again by itself",
      "RCP.md §6.2",
      contesto={"ultimo_consegnato": 0xFFFFFFFF, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=1) + b"\x00" * 64], "fin"


@caso("buco-nella-successione", ACCETTATO,
      "⭐ frame 12 after 9: it is ACCEPTED — a gap is normal, §6.2 "
      "says the counter grows also for abandoned frames — ⛔ and "
      "the client MUST ask for a keyframe.  ⚠ It is the case where «accepted» on "
      "its own is not enough: `chiedi_chiave` is looked at too",
      "RCP.md §6.2, §5.2",
      contesto={"ultimo_consegnato": 9, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=12) + b"\x00" * 64], "fin"


# ── The expected greens: what MUST pass ────────────────────────────────────
@caso("chiave-buona", ACCETTATO,
      "⭐ the frame phase 2 exists to deliver: keyframe, HEVC, "
      "1920x1080, number 1.  ⛔ Without this case the bench could refuse "
      "everything and look very strict",
      "RCP.md §6.2")
def _():
    return [intestazione() + b"\x00" * 4096], "fin"


@caso("chiave-senza-dati", ACCETTATO,
      "⭐ exactly 28 bytes and FIN: a frame with **zero** bytes of data.  "
      "⚠ No line of `RCP.md` forbids it, and this case is here to "
      "declare it instead of discovering it: it is legal, and will go to the "
      "decoder which will refuse it itself.  ⛔ If one day it were decided that "
      "it is an error, the line goes in `RCP.md`, not in an `if` of the client",
      "RCP.md §6.2")
def _():
    return [intestazione()], "fin"


@caso("istante-zero", ACCETTATO,
      "⭐ `istante = 0`.  §6.2: «it is not a time of day, it is a monotonic clock that "
      "starts from an arbitrary point» — and zero is an arbitrary point.  ⚠ A "
      "judge that refused it would be inventing a sentinel that §6.0 "
      "forbids",
      "RCP.md §6.2")
def _():
    return [intestazione(ist=0) + b"\x00" * 64], "fin"


@caso("input-zero", ACCETTATO,
      "⭐ `input = 0`, which §6.2 declares to be «none».  It is the value "
      "**every** frame of phase 2 carries, where no input exists",
      "RCP.md §6.2")
def _():
    return [intestazione(inp=0) + b"\x00" * 64], "fin"


@caso("dati-a-pezzetti", ACCETTATO,
      "⭐ the header split into seven four-byte pieces.  ⛔ A "
      "QUIC stream arrives in pieces of any size, and a judge that "
      "read the 28 bytes from a single `recv` would be green on every bench and "
      "red on the first real network",
      "RCP.md §6.2")
def _():
    g = intestazione()
    return [g[i:i + 4] for i in range(0, 28, 4)] + [b"\x00" * 64], "fin"


# ===========================================================================
# ⛔ THE FAULTS, AND EACH ONE BREAKS A SINGLE PROPERTY — `PIANO.md` §0.3 rule 4.
#
#    «A bench that has never turned red is not clean: it is NOT
#    CERTIFIED» (`01-b12-guasti.py`).  ⛔ And the mark has TWO halves: the faulty
#    round must say it **and the healthy round must NOT already say it** — the criterion
#    that on 11 Aug 2026 was missing precisely from the bench that certifies the other
#    eleven (finding R12-A.3).
GUASTI = {
    "G1": {
        "titolo": "the header read as 32 bytes instead of 28",
        "rompe": "the size of the header (§6.2)",
        "dimostra":
            "⛔ It is the **historical** defect of this field: `RCP.md` §6.2 was "
            "corrected on 9 Aug 2026 because the drawing gave «… 24 │ "
            "32», that is four padding bytes never declared.  With 32, "
            "the judge eats four data bytes inside the header: "
            "every short frame becomes «short header» and every "
            "long frame shifts by four bytes.  ⭐ A bench that did not "
            "have a case of exactly 28 bytes (`chiave-senza-dati`) would NOT "
            "see this fault.",
        # ⭐ This mark is stronger than the other two, and it must be said: it does not say
        #    «a case is red», it says **the wrong number**.  It tells the
        #    red of the fault from the red of a bench that collapses.
        "marca": "the header wants exactly 32",
    },
    "G2": {
        "titolo": "the judge also accepts `tipo = 0x0300`",
        "rompe": "the strictness rule on the type (§3, §6.2)",
        "dimostra":
            "⛔ It is the leniency `RCP.md` §3 exists to remove, in its "
            "most harmless form: one value more in a `set`.  ⭐ The fault "
            "**breaks nothing visible** — all the good frames "
            "keep passing — and it shows only from the case that must fail.  "
            "A bench made only of expected greens would stay green.",
        "marca": "tipo-0x0300: ERRORE_PROTOCOLLO -> ACCETTATO",
    },
    "G3": {
        "titolo": "a RESET stream treated as one closed with FIN",
        "rompe": "the distinction between abandonment and complete frame (§6.2)",
        "dimostra":
            "⛔ It is **exactly** the defect finding R1.7 found in "
            "`RCP.md` on the evening of 9 Aug 2026: without the words «but only "
            "if the stream ended with a FIN», *«an abandoned frame and "
            "a complete one looked the same»* — error form **E8**. "
            "⭐ With the fault, the 10 KB of an abandoned frame end up at the "
            "decoder: half an image, or a refusal nobody connects "
            "to the abandonment.",
        "marca": "reset-a-meta: SCARTATO -> ACCETTATO",
    },
    # ⭐⛔ G5 — AND THIS FAULT IS NOT INVENTED: IT IS YESTERDAY MORNING'S JUDGE.
    "G5": {
        "titolo": "the four lines of 12 Aug go back to being ambiguities",
        "rompe": "the four double readings closed by `RCP.md` on 12 Aug "
                 "2026 (P2 §6.2, P3 §2.5, P5 §6.2, P6 §5.2)",
        "dimostra":
            "⛔ It is **the state of this very file on the morning of 12 Aug "
            "2026**, before the coordinator applied the seven lines — "
            "as **G4** is today's state of `01-b4-validatore.py`.  ⭐ A "
            "fault taken from real history is worth more than an invented one: "
            "it proves that the bench can tell today's document from "
            "yesterday's, which is precisely the way a "
            "certification expires without anybody noticing.  ⚠ And the "
            "fault **drops nothing**: the four cases become "
            "`AMBIGUO`, that is *«nobody made a mistake»* — the most "
            "lenient outcome this bench has.  A bench that counted only the "
            "reds would let it pass.",
        # ⛔ Four cases change, and the mark cites **one**: it is more than enough,
        #    because the second half of the criterion (R12-A.3) asks that the healthy
        #    round NOT say it — and when healthy `numero-zero` comes out ERRORE_PROTOCOLLO
        #    expected and ERRORE_PROTOCOLLO seen.
        "marca": "numero-zero: ERRORE_PROTOCOLLO -> AMBIGUO",
    },
    # ⭐⛔ G6 and G7 — AND NOT EVEN THESE TWO ARE INVENTED: THEY ARE THE JUDGE OF
    #    YESTERDAY **EVENING**, before the cures of D13 and D14 entered `RCP.md`.
    "G6": {
        "titolo": "the one-second grace on the frames in flight is not there",
        "rompe": "the sixth exception of §3 and the line at the end of §6.2 (D14)",
        "dimostra":
            "⛔ It is the state of this file **until the evening of 12 Aug "
            "2026**, when the grace was proposal P8 and not a line.  ⭐ With the "
            "fault injected the frame already in flight after a "
            "`TELA(ADATTATA)` goes back to being `ERRORE_PROTOCOLLO`: that is **the "
            "client kills a healthy session** because the user dragged "
            "a window.  ⚠ It is the same form as the first draft of P5, "
            "the one that stayed two hours in the document — a bench that "
            "could not see this fault would certify that "
            "line again.",
        "marca": "p8-in-volo-dopo-adatta-tela: ACCETTATO -> ERRORE_PROTOCOLLO",
    },
    "G7": {
        "titolo": "the first frame at the new size can be a delta",
        "rompe": "the line of §5.2 on the canvas change (D13)",
        "dimostra":
            "⛔ It is defect **D13** put back inside the judge, and it is the one "
            "that `[M]` makes Chrome paint five frames at the old "
            "size **without an error**.  ⭐ The fault breaks nothing "
            "visible — every good frame keeps passing — and it shows "
            "only from the case that must fail: a bench made only of expected "
            "greens would stay green, and it is precisely how phase 2 was "
            "until tonight.",
        "marca": "d13-delta-alla-misura-nuova: ERRORE_PROTOCOLLO -> ACCETTATO",
    },
    # ⭐⛔ G8 and G9 — THE JUDGE OF **TWO HOURS AGO**: between the two cures of the evening and
    #    the two that put them back on their feet.  ⚠ The history of this chapter
    #    is made of real faults hours apart, and each stays here because
    #    that is how one proves that the bench can tell the document of
    #    now from the one of a little earlier.
    "G8": {
        "titolo": "the grace covers «the previous canvas» alone, not the window",
        "rompe": "the line of §6.2 corrected by P11",
        "dimostra":
            "⛔ It is the D14 cure **as it had been written the first time**, in the "
            "singular.  ⭐ With the fault, the scene of whoever drags a window — "
            "two `TELA(ADATTATA)` in one second — makes the session "
            "drop again: the keyframe opened before everything carries a size that "
            "is neither the one in force nor the previous one, and nobody made a "
            "mistake.  ⚠ It is **the same form** as P5 and D14: a defect "
            "that sits one step further on from the scene just cured, and that shows "
            "only if the bench carries the case with **two** canvas changes.",
        "marca": "p11-due-tele-nella-finestra: ACCETTATO -> ERRORE_PROTOCOLLO",
    },
    "G9": {
        "titolo": "the finding on the client's state is no longer printed",
        "rompe": "the line of §5.2 on WHEN the client reconfigures (P10)",
        "dimostra":
            "⛔ It is leniency in its most silent form: the outcome stays "
            "`ACCETTATO` — on the wire nobody really made a mistake — and only "
            "the line saying that the decoder is where §5.2 "
            "forbids it to be **disappears**.  ⭐ A bench that counted only the outcomes "
            "would stay green, and it is precisely the defect that `[M]` makes "
            "Chrome paint a wrecked image without raising an "
            "error.  ⚠ The fault **drops no outcome**: it shows only "
            "from the check that requires the finding.",
        "marca": "p10-decodificatore-al-tela: ACCETTATO -> ACCETTATO    "
                 "accepted, but without the FINDING",
    },
    "G10": {
        "titolo": "the tolerance goes back to ending BY THE CLOCK, after one second",
        "rompe": "the line of §6.2 corrected by P13",
        "dimostra":
            "⛔ It is the D14 cure **as it was written two hours earlier**, with "
            "a second inside.  ⭐ With the fault, the case `p13-linea-lenta` "
            "goes back to `ERRORE_PROTOCOLLO`: the client closes a frame the "
            "server sent when it was legal and which §5.2 forbade it to "
            "abandon — **because the line is slow**.  ⛔ It is invariant "
            "**I1** («never to cut off») broken in the exact condition I1 "
            "exists to protect, and it is the fault that proves that the cure of "
            "P13 is not just told: without the slow-line case, «the "
            "tolerance ends at the keyframe» and «the tolerance ends after one "
            "second» give the same green on all the rest of the bench.",
        "marca": "p13-linea-lenta: ACCETTATO -> ERRORE_PROTOCOLLO",
    },
    "G11": {
        "titolo": "the size is looked at BEFORE the order",
        "rompe": "the precedence of §6.2 cured by P14",
        "dimostra":
            "⛔ It is the judge of **an hour ago**, and the fault rewrites "
            "no rule: it moves **the place** where a rule is applied, "
            "which is exactly what P14 cured.  ⭐ With the fault, the "
            "frame in flight overtaken by the new keyframe — lower `numero`, "
            "old size — goes back to `ERRORE_PROTOCOLLO` instead of "
            "`SCARTATO`: the session drops, and neither of the two sides made a "
            "mistake.  ⚠ It is the fourth form of the same family (P8 -> P11 "
            "-> P13 -> P14), and it is the one that shows worst: two lines "
            "**of the same section**, both right, and what decides is "
            "the order in which they are read.",
        "marca": "p14-in-volo-scavalcato-dalla-chiave: SCARTATO -> "
                 "ERRORE_PROTOCOLLO",
    },
    # ⭐⛔ G12 and G13 — THE TWO WAYS OF GETTING **P20** WRONG, one per direction.  ⚠ And the
    #    first is not invented: it is **this morning's** judge, and it is what
    #    `02-filo-cliente.py` did at its first live round.
    "G12": {
        "titolo": "§2.5 measured on the arrival of `SESSIONE` instead of on the "
                  "departure of `ATTACCA`",
        "rompe": "the real quantity of the phenomenon of §2.5 (proposal P20, "
                 "`LEZIONI.md` §1.13)",
        "dimostra":
            "⛔ It is the judge of **today**, before proposal P20, and it is "
            "exactly what the test client did at its first "
            "round against a real server (`P2-6` §5.2): "
            "*«[ERRORE_PROTOCOLLO] a frame before `SESSIONE`»* on a "
            "server that had done everything §2.5 and §5.2 require of it.  "
            "⭐ With the fault the healthy session drops, and the cause is not in the "
            "product: it is **the network**, which lost the `SESSIONE` "
            "packet.  ⚠ The cure of that round moved the measurement by an "
            "instant — from the waking of the coroutine to the bytes of the channel — that is "
            "it cured the **bench** and not the line: the quantity remained "
            "a substitute, and this fault is the proof that the bench can "
            "tell the two things apart.",
        "marca": "p20-sessione-in-ritardo: AMBIGUO -> ERRORE_PROTOCOLLO",
    },
    "G13": {
        "titolo": "the P20 cure written TOO BROADLY: it never closes "
                  "before `SESSIONE`",
        "rompe": "invariant **I3** on the wire (§2.5)",
        "dimostra":
            "⛔ It is the form in which **P5** ended up wrong, and the lesson "
            "is in this round's mandate: a rule too strict kills "
            "the healthy session, one too broad lets through what the "
            "line existed to stop — and **both pass the case that "
            "motivated the cure**.  ⭐ With the fault, a server can open a video "
            "stream onto a client that has not even sent "
            "`ATTACCA`, that is push pixels onto whoever has not attached: I3 "
            "disappears, and none of the 49 greens of the bench notices.  ⚠ It is "
            "the fault that proves that the **second** case of the pair "
            "earns its place: without it, «always hold back» and «hold back "
            "only after `ATTACCA`» give the same green on all the rest.",
        "marca": "p20-prima-di-attacca: ERRORE_PROTOCOLLO -> AMBIGUO",
    },
    # ⭐⛔⛔ G14 and G15 — THE TWO WAYS OF GETTING **P21** WRONG, one per direction.  ⚠ And the
    #     first is not invented either: it is **the cure as it was
    #     proposed**, on the morning of 13 Aug, before somebody put in front of it
    #     a compositor that grants a size different from the one
    #     requested.
    "G14": {
        "titolo": "the P21 discriminant written on the SIZE the client "
                  "named, instead of on the request in flight",
        "rompe": "the real quantity of the phenomenon of §6.2 (proposal P21, "
                 "`LEZIONI.md` §1.13)",
        "dimostra":
            "⛔ It is the P21 cure **as it was proposed**, and the check "
            "rejected it in a single case: §4.5 says that *«the granted canvas "
            "can differ from the requested one»*, on KWin < 6.8 it is the "
            "normal road (`SPECIFICHE.md` §6.3) and the negotiation of §6.4 "
            "grants the mode the compositor **has**.  ⭐ With the fault, the "
            "client that asked for 1366x768 and receives — before the answer — "
            "the 1280x720 frame the compositor is about to grant "
            "**closes the session**: nobody made a mistake, and the defect "
            "moved by one step instead of disappearing.  ⚠ It is the eighth draft "
            "of the same line, avoided because the bench carries the case **just "
            "outside** the scene the cure told about.",
        "marca": "p21-concessa-diversa-da-chiesta: AMBIGUO -> ERRORE_PROTOCOLLO",
    },
    "G15": {
        "titolo": "the P21 cure written TOO BROADLY: every size never in "
                  "force is held back, even without any request in flight",
        "rompe": "the line of §6.2 cured by P11 — `ERRORE_PROTOCOLLO` **at once** "
                 "for a size never in force in that window",
        "dimostra":
            "⛔ It is the form in which **P5** ended up wrong, and in which P8 "
            "cost two rounds: a cure that saves the case that motivated it and "
            "takes away the defence on the other side.  ⭐ With the fault, the frame "
            "at 800x600 in the middle of a canvas change — a size that **nobody "
            "ever asked for**, that is the wrong field P11 exists to "
            "stop — stops making it close: the bench no longer tells «the "
            "`TELA` is still in flight» from «the server is sending a size "
            "it does not have».  ⚠ It is the fault that proves that the **third** case "
            "of the triple earns its place: without it, «always hold "
            "back» and «hold back as long as there is a request in flight» give "
            "the same green on all the rest of the bench.",
        "marca": "p11-misura-mai-in-vigore: ERRORE_PROTOCOLLO -> AMBIGUO",
    },
}


# ===========================================================================
VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def riga(colore, segno, nome, testo):
    print(f"    {colore}{segno}{GRIGIO}  {nome:30s} {testo}")


def gira_caso(c, guasti):
    """⛔ Returns (seen_outcome, verdict, context), and does not judge: judging
       belongs to the caller, who holds the expectation.  Keeping the two things together
       makes you write `if visto != atteso: atteso = visto` without noticing."""
    campi = dict(c["contesto"] or {})
    ctx = Contesto(tela=campi.pop("tela", (1920, 1080)),
                   codec_negoziato=campi.pop("codec_negoziato", 1),
                   sessione_aperta=campi.pop("sessione_aperta", True))
    # ⛔ `adatta_tela` is NOT a field: it is a message arrived on the wire
    #    (§7.1), and it must go through the method — so the context carries
    #    along also WHERE the canvas in force comes from, which is half of the
    #    P5 verdict.  ⚠ A direct `setattr` would have changed the numbers
    #    leaving `tela_da` saying «SESSIONE», that is a verdict that names
    #    the wrong section.
    adatta = campi.pop("adatta_tela", None)
    # ⛔ Time passing is NOT a field of the wire, and it is inert since the
    #    **P13** cure: it is declared because the **scene** says so (the slow line),
    #    not because it decides anything.  ⚠ Only fault G10 puts it back in
    #    charge, and that is where one sees that the cure is really there.
    secondo_passato = campi.pop("secondo_passato", False)
    # ⚠ And the keyframe at the new size is declared **after** the `TELA`, because it is
    #    what closes the queue: see `arriva_la_chiave_nuova()`.
    chiave_nuova = campi.pop("chiave_alla_tela_nuova", None)
    if adatta is not None:
        # ⛔ One or MORE THAN ONE: whoever drags a window sends more than one
        #    `ADATTA_TELA` per second, and it is the scene of the case
        #    `p8-due-tele-in-un-secondo`.  ⚠ A single tuple stays a single
        #    tuple: `(1280, 720)` and `[(1280, 720)]` do the same thing.
        passi = adatta if isinstance(adatta, list) else [adatta]
        for lar, alt in passi:
            # ⚠ The grace is on by default since the evening of 12 Aug 2026 —
            #   §6.2 carries it — and it is no longer asked for: see `adatta_tela`.
            ctx.adatta_tela(lar, alt)
    # ⛔⭐ AND THE `ADATTA_TELA` SENT AND NOT YET ANSWERED — proposal **P21**.
    #
    #    ⚠ They are set **after** the `TELA`s, and the order is the scene: a `TELA` that
    #      arrived after would answer this request and take it out of
    #      flight — that is the case would say one thing and the context another.
    #    ⛔ And it is not a field of the wire the client receives: it is what the
    #      client **itself sent**, like `attacca_spedito` for P20.  A
    #      direct `setattr` on the list would have bypassed the method, which is
    #      the place where it is written **why** that fact counts.
    spedite = campi.pop("adatta_spedito", None)
    if spedite is not None:
        for lar, alt in (spedite if isinstance(spedite, list) else [spedite]):
            ctx.adatta_spedito(lar, alt)
    # ⛔ And the fields are set AFTER the `TELA`, not before: they are the state of the
    #    client **at the moment the frame arrives**, and a
    #    `chiave_alla_tela_nuova` written before would be reset by
    #    `adatta_tela` — that is the case would say one thing and the context another.
    for k, v in campi.items():
        setattr(ctx, k, v)
    ctx.secondo_passato = secondo_passato
    if chiave_nuova:
        ctx.arriva_la_chiave_nuova()
    elif chiave_nuova is False:
        ctx.chiave_alla_tela_nuova = False
    g = Giudice(ctx, dove=c["dove"], guasti=guasti)
    pezzi, come = c["fabbrica"]()
    for p in pezzi:
        g.arrivano(p)
        if g.verdetto is not None:
            break          # ⛔ whoever has already decided stops reading: it is §6.2
    v = g.finisce(come) if g.verdetto is None else g.verdetto
    return v.esito, v, ctx


def sezione_principale(r):
    """The FIRST section cited, which is the one backing the verdict.

    ⛔ This function was born from a red on a right judgement, at the first round
       of the bench — 12 Aug 2026.  The comparison was
       `v.regola.split(" (")[0] == c["regola"].split(" (")[0]`, that is it
       required the verdict to cite **all** the sections the
       prediction lists: `«RCP.md §6.2»` against `«RCP.md §6.2, §5.1, §5.2»`
       gave **red**, and the outcome was ACCETTATO against ACCETTATO.

    ⚠ Four cases out of twenty-seven, all with the exact judgement: it is the form
      this project pays most often — **the bench accusing the
      product** — and this time it cost ten minutes because the bench
      printed «right outcome, wrong RULE» instead of «red».  ⛔ A
      check that does not say WHY it is red sends you looking on the wrong
      side: that line stayed, and did its job.

    ⭐ The right rule: the verdict MUST cite the **load-bearing** section; the
       others the prediction lists are the surroundings, and requiring them would be
       requiring a wording, not a judgement.
    """
    return r.split(",")[0].split(" (")[0].strip()


def conta(casi):
    """⛔ The numbers are COMPUTED by this function — never a comment.

    `01-b5-violazioni.py` finding R7.14: three numbers written by hand in the
    comments, and **none of the three matched the file**.
    """
    return {
        "violazioni": sum(1 for c in casi if c["atteso"] == ERRORE_PROTOCOLLO),
        "scarti": sum(1 for c in casi if c["atteso"] == SCARTATO),
        "verdi": sum(1 for c in casi if c["atteso"] == ACCETTATO),
        "ambigui": sum(1 for c in casi if c["atteso"] == AMBIGUO),
    }


def giro(a, guasti=(), silenzioso=False):
    """A whole round.  Returns (faulty, ambiguous, marks, lines)."""
    casi = [c for c in CASI if not a.solo or a.solo in c["nome"]]
    if not casi:
        # ⛔ ZERO CASES IS NOT «ALL PASSED» — finding R7.15.
        print(f"    {ROSSO}⛔ «--solo {a.solo}» selected ZERO cases out of "
              f"{len(CASI)}: there is nothing to measure{GRIGIO}")
        print("       This is NOT a green.  The names are read with --elenco.")
        return None
    guastati, ambigui, righe = 0, [], []
    testo_intero = []
    for c in casi:
        try:
            visto, v, ctx = gira_caso(c, guasti)
            errore = None
        except Exception as e:   # noqa: BLE001 — the error type IS the measurement
            visto, v, ctx, errore = None, None, None, f"{type(e).__name__}: {e}"
        atteso = c["atteso"]
        ok = (errore is None and visto == atteso)
        # ⛔ AND THE CITED RULE IS COMPARED, not just printed: a red
        #    with the wrong section next to it passes for a right red.
        regola_ok = (errore is None and c["regola"]
                     and sezione_principale(v.regola)
                     == sezione_principale(c["regola"]))
        if ok and c["regola"] and not regola_ok:
            ok = False
            errore = (f"right outcome, but the LOAD-BEARING SECTION does not match: the "
                      f"verdict cites «{sezione_principale(v.regola)}», the "
                      f"prediction «{sezione_principale(c['regola'])}»")
        # ⛔ and the cases that ask for something more than the outcome alone
        if ok and c["nome"] == "buco-nella-successione" and not ctx.chiedi_chiave:
            ok, errore = False, ("accepted, but the client did not note that it "
                                 "must ask for a keyframe (§5.2)")
        if ok and c["nome"] == "reset-a-meta" and not ctx.chiedi_chiave:
            ok, errore = False, ("discarded, but not treated as a gap: "
                                 "§6.2 requires it (§5.2)")
        # ⛔ AND THE TOLERANCE IS WRITTEN IN THE LOG — §3, last line: *«a
        #    silent tolerance is indistinguishable from a defect, and it is
        #    precisely the leniency this section exists to remove»*.
        #    ⚠ Without this check a judge that accepted the frame in
        #      flight **silently** would be green here and would have taken from whoever
        #      reads the log the only way of telling the exception from the
        #      defect.
        if (ok and c["nome"] in ("p8-in-volo-dopo-adatta-tela",
                                 "p11-due-tele-nella-finestra")
                and not v.tollerato):
            ok, errore = False, ("accepted, but without declaring the "
                                 "tolerance: §3 wants every exception "
                                 "to be written in the log")
        # ⛔ P10 — AND THE FINDING ON THE CLIENT HAS ITS TWO HALVES, like a mark:
        #    the case that violates the line must **carry** it, the one that
        #    respects it **must not carry** it.  ⚠ Without the second half, a
        #    bench that always printed the finding would be green on both
        #    and would not tell the conforming client from the one that is not —
        #    it is finding R12-A.3 applied to a finding instead of a
        #    fault.
        if ok:
            for _s, _r in REGOLE_DI_STATO.items():
                if c["nome"] == _r["viola"] and not (v and v.rilievo):
                    ok, errore = False, (
                        f"accepted, but without the FINDING that {_s} requires: the "
                        f"client's state contradicts §5.2 and the bench is silent")
                if c["nome"] == _r["rispetta"] and (v and v.rilievo):
                    ok, errore = False, (
                        f"accepted, but with a FINDING on it: here the client "
                        f"is where {_s} wants it, and a finding that always appears "
                        f"distinguishes nothing")
        testo = (errore if errore else str(v))
        righe.append({"nome": c["nome"], "atteso": atteso, "visto": visto,
                      "esito": bool(ok), "regola_vista": v.regola if v else None,
                      "dice": v.dice if v else None, "errore": errore})
        # ⛔ THE OUTPUT THE MARK IS SEARCHED IN CARRIES `nome: atteso -> visto`.
        #
        #    At the first certification the marks of G2 and G3 were the NAMES of the
        #    cases (`tipo-0x0300`, `reset-a-meta`), and they did not appear: the name
        #    of the case is in the printed line, not in the verdict text, and
        #    `--certifica` runs silently.  ⛔ But the cure is not «let us search
        #    the printed line too»: a mark that is the name of the case
        #    appears **also in the healthy round**, where that case passes — that is
        #    it would fail the second half of the criterion (R12-A.3).
        # ⭐ `nome: atteso -> visto` is a real mark: in the healthy round expected and
        #    seen always coincide, so `X: A -> B` with A != B exists
        #    **only** when something is broken.
        testo_intero.append(f"{c['nome']}: {atteso} -> {visto}    {testo}")
        if atteso == AMBIGUO:
            # ⛔ AN AMBIGUOUS ONE IS NOT A FAULT, AND IT IS NOT A GREEN.
            #    The case is green if the judge **recognises** the ambiguity;
            #    what stays red is `RCP.md`, and it is counted separately.
            if ok:
                ambigui.append((c["nome"], v.propone, v.dice))
                if not silenzioso:
                    riga(GIALLO, "??", c["nome"],
                         f"⭐ RCP.md allows two readings — proposal "
                         f"{v.propone or '?'}")
                continue
        if not silenzioso:
            riga(VERDE if ok else ROSSO, "OK" if ok else "NO", c["nome"], testo)
        if not ok:
            guastati += 1
            if not silenzioso:
                print(f"        expected {atteso}, seen {visto}")
                print(f"        {c['spiega']}")
    return guastati, ambigui, righe, "\n".join(testo_intero)


def scrivi_esito(a, rec):
    """⛔ One line per round, with the time and the scene, and it is synced at once.

    ⚠ An absent log and an empty log must not look the
      same: without `--uscita` it is said, not kept silent.
    """
    if not a.uscita:
        print(f"    ⚠ no --uscita: this round leaves NO log")
        return False
    fuori = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "banco": "F2.4",
             "scena": "no network and no server: the frames are built by "
                      "the bench, and the judge reads them as it would read them from "
                      "a QUIC stream (in pieces, without keeping the data)",
             "macchina": os.uname().nodename, "python": sys.version.split()[0]}
    fuori.update(rec)
    try:
        with open(a.uscita, "a") as f:
            f.write(json.dumps(fuori, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except OSError as e:
        print(f"    {ROSSO}⛔ the log «{a.uscita}» cannot be written: {e}{GRIGIO}")
        return False
    return True


def controllo_positivo():
    """⛔ AT THE END OF EVERY RUN: can the tool find something that is there?

    `LEZIONI.md` §1.9, second rule.  Here the question has an exact answer
    at zero cost: **G2** is injected — a fault that breaks nothing
    visible — and it is checked that the case `tipo-0x0300` turns red.

    ⚠ If this check passed **also with a healthy judge**, it would mean that
      that case is always red, that is that the green of a moment ago was not a
      green.  Both rounds are looked at, not one.
    """
    class Finto:
        solo, uscita = "tipo-0x0300", ""
    sano = giro(Finto(), guasti=(), silenzioso=True)
    guasto = giro(Finto(), guasti=("G2",), silenzioso=True)
    if sano is None or guasto is None:
        return False, "the case of the positive control no longer exists"
    if sano[0] != 0:
        return False, (f"⛔ `tipo-0x0300` is red even with a HEALTHY judge: the "
                       f"green of this round is worth nothing")
    if guasto[0] != 1:
        return False, (f"⛔ with fault G2 injected `tipo-0x0300` stays GREEN: "
                       f"this bench cannot see the fault it is looking for")
    return True, ("G2 injected -> `tipo-0x0300` red; G2 removed -> green.  "
                  "The tool can find what is there")


def certifica(a):
    """⛔ healthy N -> fault M -> healed N, and they are THREE runs per fault.

    `01-b12-guasti.py`: *«"it turned red" means nothing if it was not
    green before»*, and the third step is the most insidious to lose — without it,
    «the bench sees the fault» and «the bench stayed broken» look the
    same.
    """
    print(f"\n== ⛔ THE CERTIFICATION — healthy -> fault -> healed, "
          f"{len(GUASTI)} faults")
    print(f"   ⛔ The expectations are written in `--elenco`, BEFORE this round\n")
    tutto_bene, righe = True, []
    sano = giro(a, guasti=(), silenzioso=True)
    if sano is None:
        return 2
    n_sano, _, _, testo_sano = sano
    print(f"    healthy: {n_sano} faulty")
    for sigla, g in GUASTI.items():
        rotto = giro(a, guasti=(sigla,), silenzioso=True)
        n_rotto, _, _, testo_rotto = rotto
        marca = g["marca"]
        # ⛔ THE MARK HAS TWO HALVES, and the second gets forgotten — R12-A.3.
        vista = marca in testo_rotto
        gia = marca in testo_sano
        risanato = giro(a, guasti=(), silenzioso=True)[0]
        ok = (n_sano == 0 and n_rotto > n_sano and vista and not gia
              and risanato == n_sano)
        tutto_bene &= ok
        riga(VERDE if ok else ROSSO, "OK" if ok else "NO", sigla,
             f"healthy {n_sano} -> fault {n_rotto} -> healed {risanato}   "
             f"mark «{marca}»: {'seen' if vista else '⛔ NOT seen'}"
             + ("  ⛔ but already present in the healthy round" if gia else ""))
        if not ok:
            print(f"        {g['titolo']}")
        righe.append({"guasto": sigla, "titolo": g["titolo"], "sano": n_sano,
                      "guasto_conta": n_rotto, "risanato": risanato,
                      "marca": marca, "marca_vista": vista,
                      "marca_gia_nel_sano": gia, "esito": bool(ok)})
    scrivi_esito(a, {"tipo": "certificazione", "guasti": righe,
                     "esito": bool(tutto_bene)})
    print()
    if tutto_bene:
        print(f"    {VERDE}⭐ 02-filo-fotogramma.py IS CERTIFIED: "
              f"{len(GUASTI)} faults out of {len(GUASTI)}{GRIGIO}")
        return 0
    print(f"    {ROSSO}⛔ NOT certified{GRIGIO}")
    return 1


def principale(a):
    n = conta(CASI)
    if a.elenco:
        print(f"== F2.4 — the frame against `RCP.md`: {len(CASI)} cases")
        print(f"   {n['violazioni']} violations · {n['scarti']} discards · "
              f"{n['verdi']} ⭐ expected greens · {n['ambigui']} ⭐ ambiguities "
              f"of `RCP.md`")
        print(f"   ⛔ Every line is a PREDICTION, written before the round\n")
        for c in CASI:
            print(f"  {c['nome']:30s} {c['atteso']}")
            print(f"  {'':30s}   {c['spiega']}")
            if c["regola"]:
                print(f"  {'':30s}   expected rule: {c['regola']}")
        print(f"\n== ⛔ THE FAULTS, and the expectation of each — written BEFOREHAND")
        for sigla, g in GUASTI.items():
            print(f"  {sigla}  {g['titolo']}")
            print(f"      breaks:   {g['rompe']}")
            print(f"      expected healthy: 0 faulty out of {len(CASI)} cases")
            print(f"      expected fault:   > 0 faulty, and in the output the mark "
                  f"«{g['marca']}»")
            print(f"      ⛔ and the mark must NOT appear in the healthy round")
        print(f"\n== ⭐⛔ THE {len(REGOLE_NUOVE)} LINES THAT ENTERED `RCP.md` ON 12 AUG 2026,")
        print(f"      and the TWO cases of each")
        coperte, mancanti = regole_coperte(CASI)
        for sigla, r in REGOLE_NUOVE.items():
            print(f"  {sigla}  {r['dove']}")
            print(f"      «{r['dice']}»")
            print(f"      was:      {r['era']}")
            viola = (", ".join(r["viola"])
                     if isinstance(r["viola"], (tuple, list)) else r["viola"])
            print(f"      {r.get('etichetta_viola', 'VIOLATES it')}:  {viola}")
            print(f"      {r.get('etichetta_rispetta', 'RESPECTS it')}: "
                  f"{r['rispetta']}")
        print(f"\n  ⛔ rules with BOTH cases: {len(coperte)} of "
              f"{len(REGOLE_NUOVE)} — {', '.join(coperte) or '—'}")
        for sigla, perche in mancanti:
            print(f"     {ROSSO}⛔ {sigla}: {perche}{GRIGIO}")
        # ⛔⛔ AND THE OPEN PROPOSALS, SEPARATE: what the document does NOT say.
        print(f"\n== ⛔⛔ THE PROPOSALS STILL OPEN — `RCP.md` does not carry them")
        print(f"      ⚠ They are not rules: they are cures with the text ready, and the "
              f"document")
        print(f"        is touched by the coordinator.  Here is TODAY's expectation, "
              f"not tomorrow's")
        ap_coperte, ap_mancanti = proposte_coperte(CASI)
        for sigla, p in PROPOSTE_APERTE.items():
            print(f"  {sigla}  {p['dove']}")
            print(f"      «{p['dice']}»")
            print(f"      is:       {p['era']}")
            # ⛔ AND THE READY TEXT IS PRINTED, not named.  A proposal
            #    cited without the text is a complaint, and it is the half that
            #    `F2-4-filo.md` §«What I propose» requires of every line.
            if p.get("testo"):
                print(f"      ready-to-paste text:")
                print(f"        {p['testo']}")
            for nome, atteso in p["casi"].items():
                # ⛔ «(today)» at the end is not decoration: without it, this line
                #    would end with `AMBIGUO` and `02-filo-lancia.sh` — which looks for
                #    ambiguities with `grep 'AMBIGUO$'` — would print
                #    the same case twice, once from the table and once
                #    from the list.  ⚠ A bench that duplicates its own
                #    lines makes whoever reads the output count wrong.
                print(f"      {nome:32s} expected {atteso} (today)")
        print(f"\n  ⛔ proposals with ALL their cases: {len(ap_coperte)} of "
              f"{len(PROPOSTE_APERTE)} — {', '.join(ap_coperte) or '—'}")
        for sigla, perche in ap_mancanti:
            print(f"     {ROSSO}⛔ {sigla}: {perche}{GRIGIO}")
        return 0

    if a.certifica:
        return certifica(a)

    print(f"== F2.4 — the frame judged against `RCP.md`")
    print(f"   ⛔ SCENE: no network, no server.  The frames are built by")
    print(f"      this bench and the judge reads them **in pieces**, as "
          f"they would arrive")
    print(f"      from a QUIC stream.  The phase 2 product does not exist: "
          f"`grep -c`")
    print(f"      of `0x0301` in `src/` gives 0 on all three files `[M]`")
    if a.guasto:
        print(f"   {GIALLO}⚠ FAULT INJECTED: {a.guasto} — "
              f"{GUASTI[a.guasto]['titolo']}{GRIGIO}")
    print(f"   {len(CASI)} cases: {n['violazioni']} violations · {n['scarti']} "
          f"discards · {n['verdi']} greens · {n['ambigui']} ambiguities")
    print(f"   log: {a.uscita or '⛔ NONE'}\n")

    r = giro(a, guasti=(a.guasto,) if a.guasto else ())
    if r is None:
        return 2
    guastati, ambigui, righe, _ = r

    print(f"\n    == what this round really looked at")
    sel = conta([c for c in CASI if not a.solo or a.solo in c["nome"]])
    for che, tot in sel.items():
        if tot == 0:
            print(f"    --  {che:36s} no case exercised it")
        else:
            print(f"    {tot:3d}      {che}")

    # ⭐⛔ THE NEW LINES: HOW MANY REALLY HAVE THE TWO CASES.
    #
    #    ⛔ This count sits **inside the round**, not in a comment and not in the
    #       report: a rule that lost the case that triggers it
    #       would go back to being a rule nobody enforces, and the
    #       bench would stay green — which is the worst form of green.
    coperte, mancanti = regole_coperte(CASI)
    print(f"\n    == ⭐⛔ the {len(REGOLE_NUOVE)} lines that entered `RCP.md` on 12 "
          f"Aug 2026 — six in the morning, two in the evening")
    riga(VERDE if not mancanti else ROSSO, "OK" if not mancanti else "NO",
         "regole-con-i-due-casi",
         f"{len(coperte)} of {len(REGOLE_NUOVE)} have the case that VIOLATES them and "
         f"the one that RESPECTS them: {', '.join(coperte) or '—'}")
    for sigla, perche in mancanti:
        print(f"        ⛔ {sigla}: {perche}")

    # ⛔⛔ AND THE PROPOSALS STILL OPEN, COUNTED THE SAME WAY.
    #
    #    ⚠ The count sits next to that of the entered rules and **not together**:
    #      «the lines the document carries» and «a cure the document does not
    #      have yet» are two different facts, and adding them up would give a number that
    #      means nothing.
    # ⛔ AND THE LINE THAT TALKS ABOUT THE CLIENT'S STATE, COUNTED SEPARATELY — P10.
    st_coperte, st_mancanti = regole_di_stato_coperte(CASI)
    print(f"\n    == ⭐⛔ the lines that talk about the CLIENT'S STATE, not the "
          f"wire")
    riga(VERDE if not st_mancanti else ROSSO, "OK" if not st_mancanti else "NO",
         "stato-con-i-due-casi",
         f"{len(st_coperte)} of {len(REGOLE_DI_STATO)} have the case that carries "
         f"the FINDING and the one that does not: "
         f"{', '.join(st_coperte) or '—'}")
    for sigla, perche in st_mancanti:
        print(f"        ⛔ {sigla}: {perche}")

    ap_coperte, ap_mancanti = proposte_coperte(CASI)
    print(f"\n    == ⛔⛔ the OPEN proposals — `RCP.md` does not carry them yet")
    riga(VERDE if not ap_mancanti else ROSSO, "OK" if not ap_mancanti else "NO",
         "proposte-con-i-loro-casi",
         f"{len(ap_coperte)} of {len(PROPOSTE_APERTE)} have all their "
         f"cases: {', '.join(ap_coperte) or '—'}")
    for sigla, perche in ap_mancanti:
        print(f"        ⛔ {sigla}: {perche}")

    # ⭐⛔ THE AMBIGUITIES OF `RCP.md`, AT THE END AND WITH THE CURE NEXT TO THEM.
    if ambigui:
        print(f"\n    {GIALLO}⭐⛔ `RCP.md` DOES NOT DECIDE WELL IN "
              f"{len(ambigui)} POINT{'' if len(ambigui) == 1 else 'S'}"
              f"{GRIGIO}")
        print(f"       ⚠ It is not a fault of the product and it does not make this")
        print(f"         round fail: it is a defect of the DOCUMENT, and §0 says that the")
        print(f"         defects of that file belong to that file.")
        # ⛔ And the two families are named, because they are not the same thing and
        #    confusing them inflates the count (`F2-4-filo.md`, «What I propose»):
        #      double reading -> two conforming implementations produce
        #                        DIFFERENT bytes for the same input;
        #      contradiction  -> two conforming implementations produce the
        #                        SAME byte, and that byte is wrong.
        print(f"       ⚠ And they are two families: a **double reading** makes "
              f"two careful")
        print(f"         implementations diverge; an **internal "
              f"contradiction** makes them")
        print(f"         converge on the same wrong byte — and the second "
              f"is worse,")
        print(f"         because no comparison between two implementations "
              f"finds it.")
        for nome, prop, dice in ambigui:
            # ⛔ The cure is looked up in both tables: a proposal still
            #    open is not among the entered rules, and printing it as «?»
            #    would turn a finding with the cure ready into a complaint.
            r = REGOLE_NUOVE.get(prop) or PROPOSTE_APERTE.get(prop, {})
            print(f"\n       {nome}")
            print(f"         {dice}")
            print(f"         ⇒ {prop} — {r.get('dove', '?')}")
            print(f"           «{r.get('dice', '?')}»")
    elif not a.solo:
        # ⛔ AND THE ZERO IS DECLARED, not kept silent: «no ambiguity printed»
        #    and «the branch that prints them is exercised by no case» are
        #    two different facts, and it is form E8 applied to the bench itself.
        print(f"\n    --  ⭐ `RCP.md` no longer allows two readings in any "
              f"of the {len(CASI)} cases:")
        print(f"        the **ten** this bench found all entered "
              f"the document")
        print(f"        on 12 Aug 2026, in four rounds: four in the "
              f"morning (P2 · P3 ·")
        print(f"        P5 · P6), two in the evening (P8 §6.2 · P9 §5.2), ⛔ **two "
              f"born from the two of the")
        print(f"        evening** (P10 §5.2 · P11 §6.2) and ⛔ **two born from "
              f"those** (P12 §3 · P13")
        print(f"        §6.2) — each found **by applying** the previous one, "
              f"not by rereading it.")
        print(f"        ⚠ Hence: **no case** requires `AMBIGUO` today, and the "
              f"branch that")
        print(f"        prints them is not exercised by this round.  The branch of the "
              f"JUDGE that")
        print(f"        produces `AMBIGUO` is exercised by fault **G5**, at every "
              f"certification.")

    # ⛔⛔ THE DECLARED FINDINGS — where the document decides, and the decision does not
    #    hold.  ⚠ They do not make the round fail: it is not the bench that cures them.
    con, senza = rilievi_col_caso(CASI)
    if RILIEVI_DICHIARATI:
        n = len(RILIEVI_DICHIARATI)
        print(f"\n    {GIALLO}⛔⛔ AND {n} FINDING{'' if n == 1 else 'S'} "
              f"DECLARED{'' if n == 1 else ''} on `RCP.md`, which this round "
              f"does NOT cure{GRIGIO}")
        print(f"       ⚠ Here the document **decides**, and the bench applies its "
              f"decision:")
        print(f"         they are not `AMBIGUO`.  ⛔ But applying it and keeping silent that "
              f"it kills a")
        print(f"         healthy session would be form E8 turned against whoever "
              f"reads the bench.")
        print(f"       --  with a case that shows them: "
              f"{', '.join(con) or '—'} · without: {', '.join(senza) or '—'}")
        for sigla, r in RILIEVI_DICHIARATI.items():
            print(f"\n       {sigla}  {r['dove']}   {r['marca']}")
            print(f"         {r['dice']}")
            print(f"         scene: {r['scena']}")
            senza_caso = "⛔ none — it stays a reading, and it is declared"
            print(f"         case: {r['caso'] or senza_caso}")

    # ⛔ THE POSITIVE CONTROL, AT THE END OF EVERY RUN.
    print(f"\n    == ⛔ the positive control")
    ok_cp, perche = controllo_positivo()
    riga(VERDE if ok_cp else ROSSO, "OK" if ok_cp else "NO",
         "controllo-positivo", perche)

    scritto = scrivi_esito(a, {
        "tipo": "giro", "guasto_innestato": a.guasto or None,
        "filtro": a.solo or None, "casi": len(righe), "guastati": guastati,
        "ambigui": [x[0] for x in ambigui], "proposte": [x[1] for x in ambigui],
        "controllo_positivo": bool(ok_cp), "righe": righe})
    print(f"    --  log: {'one line written to ' + a.uscita if scritto else 'NONE'}")

    print()
    if guastati or not ok_cp:
        print(f"    {ROSSO}⛔ F2.4-fotogramma: {guastati} cases do not pass"
              f"{'' if ok_cp else ', and the positive control does not hold'}{GRIGIO}")
        return 1
    if a.solo:
        print(f"    {VERDE}⭐ the selected cases pass{GRIGIO} — ⚠ and this "
              f"is NOT «the bench passes»: the round was partial")
        return 0
    print(f"    {VERDE}⭐ the frame judge agrees with `RCP.md` "
          f"on {len(righe)} cases{GRIGIO}")
    print(f"    ⚠ and it is NOT «the frame arrives»: here not one byte went "
          f"over the network.")
    print(f"      That is measured by `02-filo-cliente.py`, against a server that "
          f"does not exist yet.")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="F2.4 — the frame judged against RCP.md")
    p.add_argument("--solo", default="",
                   help="run only the cases that contain this")
    p.add_argument("--elenco", action="store_true",
                   help="print the predictions and the faults, without measuring")
    p.add_argument("--guasto", choices=sorted(GUASTI),
                   help="inject a fault INTO THE JUDGE")
    p.add_argument("--certifica", action="store_true",
                   help="healthy -> fault -> healed, for every fault")
    p.add_argument("--uscita", default="",
                   help="the round's log, in JSONL")
    # ⛔ AND WHOEVER READS THIS OUTPUT CLOSES IT HALFWAY: `02-filo-lancia.sh` does
    #    `--elenco | grep -q 'AMBIGUO$'`, and `grep -q` exits **at the first hit**
    #    closing the pipe.  ⚠ Until 13 Aug 2026 it did not show, because
    #    no case required `AMBIGUO` and `grep` read to the end: at the
    #    first open proposal the script printed a `BrokenPipeError` in
    #    the middle of the verdict.  ⛔ A pipe closed by the reader is not a defect
    #    of this bench, and must not look like one — but **it is declared
    #    and not kept silent**, which is form E8 applied to oneself.
    try:
        _codice = principale(p.parse_args())
    except BrokenPipeError:
        # ⚠ Descriptor 1 is redirected, not `sys.stdout`: closing
        #   the Python object makes the final flush fail too, and the
        #   second error hides the first.
        os.dup2(os.open(os.devnull, os.O_WRONLY), 1)
        _codice = 0
    sys.exit(_codice)
