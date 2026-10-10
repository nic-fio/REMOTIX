#!/usr/bin/env python3
"""02-filo-validatore.py — ⛔ F2.4: the mechanical referee learns the VIDEO CHANNEL.

    python3 02-filo-validatore.py registrazione.rcpreg
    python3 02-filo-validatore.py --fabbrica       builds the test recordings
    python3 02-filo-validatore.py --certifica      healthy -> G4 -> healed
    python3 02-filo-validatore.py --uscita 02-filo-esiti.jsonl reg.rcpreg

    exit 0  the video channel is conforming — and it says ON HOW MANY frames
    exit 1  it is not conforming — and it says WHICH byte and WHICH rule
    exit 2  the RECORDING is broken, or cannot be read (it is not a judgement on the wire)
    exit 3  ⛔ there is NOTHING TO JUDGE: zero blocks on the video channel

===========================================================================
⛔ WHY IT EXISTS, AND IT IS NOT A DUPLICATE OF `01-b4-validatore.py`

`PIANO.md` §0.4 lists **three** substitutes for the referee we lost with
`mstsc`, and the wire validator is the **mechanical** one: *«it sees the non-
conforming bytes, but only those»*.

⛔ **And today it does not see the video.**  `01-b4-validatore.py`, line 521:

    if canale != 0x00:
        print(f"   blocco {nb}: canale {CANALI[canale]} dal {chi}, "
              f"{lung} byte — non giudicato da questo validatore")
        continue

⚠ It is an honest line — it **declares** it does not judge, which is the opposite of
acquitting — but the consequence is that from the first frame on the most
voluminous chapter of the wire goes back to being validated by **a single**
implementation, written by the same hand that writes the server.  ⛔ It is the
state `RCP.md` §0 describes as the silent defect: *«if the server emits
nonsense, our client will gladly accept it»*.

⭐ **And the precedent says it is not theoretical**: of the two internal contradictions
of `RCP.md` found in phase 1, **one was found by this tool** — the
underscore of §4.3, at the first run, before a byte of
server existed (`RCP.md` §4.3, box of 10 Aug 2026).  ⛔ Both were
found by programs that read **only that document**, and **neither of the
two** by whoever reread it.

===========================================================================
⛔ AND THIS FILE DOES NOT TOUCH `01-b4-validatore.py`

The phase 2 mandate (§2): *«nobody writes outside their own files»*.  B4 belongs
to phase 1.  ⭐ Here the video channel is judged **next to** B4, with the same
format and the same exit codes, and the proposal to merge them is in the
report `fasi/rapporti/F2-4-filo.md`: it is a decision of the coordinator, not
of a sub-agent.

⚠ **And the judgement is not rewritten twice**: it imports `02-filo-fotogramma.py`,
which is the judge written by reading `RCP.md` §6.2.  Two copies of the judgement
would be two implementations of the same reading, that is precisely what
this tool exists to prevent.

===========================================================================
⛔⭐ THE HOLE THIS TOOL FOUND IN THE FORMAT — P7, AND IT IS CLOSED

*Found on 12 Aug 2026 by this file, **trying to judge a
conforming recording** and failing to say whether the frame was
complete.  Applied to `RCP.md` §11.1 the same day by the coordinator.*

The block of §11.1 **carried no field saying how the
stream ended**.  And for video that is the most important distinction the
document has: §6.2, finding **R1.7** of the evening of 9 Aug 2026, added
four words — *«but only if the stream ended with a FIN»* — because without
them

  ⛔ *«an abandoned frame and a complete one looked the same»*,

which the document itself classifies as error form **E8**.  ⭐ The cure had
been written **on the wire**, and the recording reopened it: looking at a
`.rcpreg` file, the referee could not tell a frame truncated because the
server had **abandoned it on purpose** (§5.1, legal, and the session
holds) from one truncated because the server **had got it wrong** (§3, the
connection drops).

⛔ **Now the block carries `fine`**, right after `canale`:

    0 = the stream continues · 1 = closed with FIN · 2 = reset with RESET_STREAM

⛔⛔ **AND THE MAGIC MOVED TO `"RCPREG" 0x00 0x02`, which is the point.**  §11.1:
   *«an old validator must **refuse** the new format, not read it
   askew»*.  ⚠ And the symmetry holds this way too: this validator
   **refuses** `0x00 0x01` with a sentence that says so, and does not try to read it.
   The old block was 16 bytes and the new one is 17: read askew, the
   `canale` would end up inside the `stream`, and ⛔ a judgement would come out — that is
   a red, or worse a green, on bytes nobody wrote.  A format that
   changes size without changing version is the error form §11.1 names
   in full.

⚠ And it was the same hole B9 had grazed on the control channel — reading
**L3**, *«the FIN bit of the STREAM frame carrying the `CONGEDO`: the
same payload bytes, one transport bit more»* — without saying that the
recording format could not write it.

⛔ **And the «completeness unknown» denominator did NOT disappear with the cure**, and it is
important that it did not: now it counts the streams whose last block
carries `fine = 0`, that is the streams that in the recording **never
closed** — a trace cut in the middle, or a server still in the middle of the
frame.  ⚠ «I did not look at it» and «I looked at it and it is fine» remain two
different facts (`LEZIONI.md` §1.9); what changes is **whose fault it is**: before
it was the format's, now it is the recording's.

===========================================================================
⛔ THE SIX LINES OF 12 AUG, JUDGED HERE ON THE RECORDINGS

Four of the six are applied by the imported judge (`02-filo-fotogramma.py`), and
here they come for free: P2 (`numero` starts from 1, and when the counter wraps the `0`
is skipped), P4 (FIN before the 28 bytes), P5 (the size is that of the **canvas in
force**), P6 (the first frame is a keyframe).

⛔ **Two instead this file must judge by itself, and they are the two that talk
   about STREAMS** — a judge that sees one frame at a time cannot
   see them, because it does not know **on which stream** it arrived nor **what had
   already passed**:

  **P3** a `0x03` on the **control channel**.  Here it is recognised like this: the
        control channel is the stream the `0x00` blocks travel on
        (§4.2, the first bidirectional), and a video block **on that same
        stream** is `ERRORE_PROTOCOLLO`.

  **P1** no video stream **before `SESSIONE`**.  Here it is recognised
        by reading the control channel in file order and marking when
        `SESSIONE` passes (`0x0007`, from the server): a video stream whose **first
        block** appears before that point violates §2.5.
        ⚠ And if the control channel could not be read, P1 **is not
          judged and it is declared**: `01-b4-validatore.py` is the referee of that
          channel, and guessing here would be form **E8**.

⭐⛔ **And P5 was CORRECTED in `RCP.md` on 12 Aug 2026**, a few hours after
    going in, because propagating it here showed that it killed a
    healthy session: it said *«the canvas granted in `SESSIONE`»*, and after a
    `TELA(ADATTATA, 1280, 720)` (§7.1) a client conforming to §6.2 closed
    in front of a server conforming to §7.1.  Now it says **«the canvas in force»**,
    and this file follows it: it scans the control channel for `TELA`s too,
    not only for `SESSIONE`.  ⛔ The two tests that keep it honest are
    `p5-misura-diversa` (different size **without** a `TELA` before: it closes) and
    `p5-misura-dopo-adatta-tela` (**the same bytes**, after a `TELA` that
    granted it: it is accepted).

===========================================================================
⭐⛔ AND ON THE EVENING OF 12 AUG TWO MORE WENT IN — **P8** (from D14) and
    **P9** (from D13)

*The P5 cure had made the canvas change midway through the session legal, and with it
two things no line covered.  The coordinator applied them the same
evening, and this referee enforces them from the start.*

  **P8** §6.2 at the end + §3 exception **6** — after a `TELA(ADATTATA)` the
         frames carrying the **previous** size are accepted for one
         second, painted rescaled and **written in the log**; outside the
         second, and for a size that has never been in force, it closes.
  **P9** §5.2 — the first frame at the **new size** MUST be a
         **real** keyframe.  ⚠ Of this the referee judges the half that sits
         in the header: that it is `0x0301`.  The VPS/SPS/PPS sit in the **data**
         and the judge does not keep the data — it is declared instead of pretending.

  ⛔ **Here it shows better than elsewhere**, and it is the reason the tests of
     P8 are also in this file and not only in the judge: in a
     recording the order of the blocks is the order of **arrival**, and a video
     stream whose first block appears **after** the `TELA(ADATTATA)` is
     exactly the frame in flight.

  ⭐⛔ **AND A HALF THIS REFEREE COULD NOT JUDGE IT NOW
     JUDGES — and not because it improved, but because the
     rule changed.**  As long as the tolerance ended **by the clock**, from a `.rcpreg`
     «inside the second» and «outside» looked the same: §11.1 carries
     **no instant**, and the denominator was called `grazia_ignota` because
     guessing would have been form **E8**.
     ⭐ Since the **P13** cure the tolerance ends at the **first keyframe at the
     new size** — a frame, and frames are in a recording.
     ⇒ The denominator is now called `tollerati`, and it counts because §3
     wants every tolerance **written**, not because something is left to
     guess.  ⛔ The test that before could not even be written is
     `p13-vecchia-dopo-la-chiave-nuova`.
     ⚠ **And it stays blind on another grace**, and it must be said: the one §7.1 gives
     to the **input coordinates** still ends by the clock, and that one no
     mechanical referee judges by reading a `.rcpreg`.

===========================================================================
⭐⛔⛔ AND THE TWO CURES OF THAT EVENING, APPLIED HERE, DID NOT HOLD IN TWO POINTS —
     CURED IN THE NEXT ROUND

*What happened this morning with P5 happened again: what found the hole
was not a rereading, it was the referee that had to enforce the
line.  ⭐ And this time the distance between the finding and the cure was one round.*

  ⭐ **P11 — §6.2 now says «a canvas that was in force within the second
     just passed»**, and no longer «the **previous** canvas».  ⛔ In the singular
     the line killed a healthy session one step further on: `ADATTA_TELA` is
     sent by the user dragging a window, and dragging sends more
     than one per second — `TELA(1600,900)` and then `TELA(1280,720)` — and the
     frame opened before everything (a **keyframe**, which §5.2 forbids
     abandoning) carried the canvas of two rounds ago.  ⇒ The two tests:
     `p11-due-tele-nella-finestra` (exits **0**, tolerance declared) and
     `p11-misura-mai-in-vigore` (**1**, and it must exit 1 — without it, the window gets
     written broad and switches off P5 right where the server errs the most).

  ⭐ **P10 — §5.2 now says WHEN the client reconfigures** (*«on the first
     KEYFRAME at the new size, not on the `TELA`»*), and the client's line exempts
     *«nor the one tolerated by §6.2»*: the two cures no longer command the
     opposite on the same frame.  ⛔ But from here **it is not judged**: which
     size the decoder is configured at **is not on the wire**, and a
     recording carries the wire.  ⇒ The item sits in the
     `FUORI_PORTATA` table, and the two cases live in `02-filo-fotogramma.py`, where the
     client's state is declared.

  ⛔ **And the tests that keep the cures TIGHT are worth as much as those that
     show them**: `p8-misura-di-nessuna-tela` exits **1** and must exit 1 —
     a grace written «after a `TELA` the size is not checked» would pass
     all the others and switch off P5 right where the server errs the most.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import struct
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ The judge is IMPORTED, not copied.  See the header.
_spec = importlib.util.spec_from_file_location(
    "f24", os.path.join(QUI, "02-filo-fotogramma.py"))
f24 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(f24)

# ⛔ THE MAGIC, AND THE ONE THAT IS NO LONGER READ — §11.1, 12 Aug 2026.
#
#    ⛔ `MAGIA_VECCHIA` is not a leftover: it is the only way of giving the old
#       file the sentence it deserves.  Without it, a `.rcpreg` of 10 Aug
#       would fall into the «does not start with the magic» branch, which sends you looking for a
#       corrupt file — and the file is not corrupt, it is of **another version**.
#       They are two different cures: regenerate it, or go and see who broke it.
MAGIA = b"RCPREG\x00\x03"
MAGIA_V1 = b"RCPREG\x00\x01"
MAGIA_V2 = b"RCPREG\x00\x02"
MAGIA_VECCHIA = MAGIA_V1     # ⚠ the old name stays: the tests below use it
RIEMPIMENTO = 0x2A          # §11.1
CLIENT, SERVER = 1, 2
CANALI = {0x00: "controllo", 0x01: "input", 0x02: "appunti",
          0x03: "video", 0x04: "audio"}
VIDEO = 0x03
CONTROLLO = 0x00

# ⛔ `fine` — «how the stream closed AFTER this block» (§11.1).
CONTINUA, FIN, RESET = 0, 1, 2
FINE = {CONTINUA: "continua", FIN: "FIN", RESET: "RESET_STREAM"}

# The block of §11.1: direction, channel, end, instant_ms, stream, length,
# masked_count.
# ⛔ Twenty-one bytes.  Sixteen were those of 10 Aug; `fine` brought them to
#    seventeen (magic `0x00 0x02`); ⭐ `istante_ms` brings them to twenty-one on **21
#    Aug 2026** (magic `0x00 0x03`), and the header gains `orologio`.
# ⛔ Every time the magic changes because the SIZE changes: a reader that did not
#    know would read every block shifted, and give a judgement on bytes that
#    nobody wrote.
BLOCCO = "!BBBIQIH"
BLOCCO_BYTE = struct.calcsize(BLOCCO)

SESSIONE = 0x0007           # §7.1, from the server
TELA = 0x000E               # §7.1, from the server — the outcome of `ADATTA_TELA`
ADATTATA = 1                # §7.1, `TELA.esito`

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


class NonConforme(Exception):
    def __init__(self, regola, dice, ass, rel):
        super().__init__(dice)
        self.regola, self.dice, self.ass, self.rel = regola, dice, ass, rel


class Malformata(Exception):
    """The RECORDING is broken: it is not a judgement on the wire."""


class NienteDaGiudicare(Exception):
    """⛔ There is no video block in the file.  It is not «conforming»."""


# ---------------------------------------------------------------------------
def leggi_blocchi(d):
    """The blocks of §11.1, with the checks the format imposes.

    ⛔ The FORMAT checks sit here and raise `Malformata`, not
       `NonConforme`: *«a malformed recording and a non-conforming wire
       are two different things, and must be said with two different sentences»* (§11.1).
    """
    # ⛔ THE OLD FORMAT IS REFUSED, AND WITH ITS OWN SENTENCE — §11.1.
    #
    #    *«an old validator must REFUSE the new format, not read it
    #    askew»*, and it holds both ways.  The old block was 16 bytes
    #    and the new one is 17: reading a `0x00 0x01` file with this reader,
    #    the `canale` would fall into the first byte of the `stream` and every block
    #    would shift by one.  ⛔ A JUDGEMENT would come out — a red on a byte
    #    nobody wrote, or a worse green — instead of «this file is
    #    of another version».
    if len(d) >= 8 and d[:8] == MAGIA_V1:
        raise Malformata(
            "it is a recording in the OLD format, «RCPREG 0x00 0x01»: the "
            "block carries neither `fine` nor `istante_ms`, and measures 16 bytes "
            "instead of 21.  ⛔ It is not read askew — §11.1, 12 Aug "
            "2026 — and it is not a broken file: REGENERATE it with today's "
            "recorder")
    if len(d) >= 8 and d[:8] == MAGIA_V2:
        raise Malformata(
            "it is a recording in the format of 12 Aug, «RCPREG 0x00 "
            "0x02»: the block does not carry `istante_ms` and measures 17 bytes instead "
            "of 21, and the header does not declare WHOSE the clock is.  ⛔ "
            "Read askew, every block would shift by four bytes.  "
            "REGENERATE it with `02-filo-cliente.py`")
    if len(d) < 16 or d[:8] != MAGIA:
        raise Malformata("it does not start with the magic of RCP.md §11.1")
    quanti, orologio, r1, r2, r3 = struct.unpack("!IBBBB", d[8:16])
    if (r1, r2, r3) != (0, 0, 0):
        raise Malformata(
            f"the three reserved bytes are {r1},{r2},{r3}: §11.1 wants them 0")
    # ⛔ «Whose clock it is» is not guessed — §11.1.  ⚠ This referee does not
    #    judge any rule with time inside (that is
    #    `01-b4-validatore.py`), ⛔ but the field is CHECKED anyway: a file
    #    that does not declare it is malformed for anyone, and letting it pass
    #    here would mean that the project's two referees give two different
    #    verdicts on the same file — which is the thing §0 forbids.
    if orologio not in (1, 2):
        raise Malformata(
            f"the `orologio` field is {orologio}: §11.1 defines two — "
            f"1 = the times are the client's, 2 = the server's")
    p, fuori = 16, []
    ultimo_istante = 0
    for nb in range(quanti):
        if p + BLOCCO_BYTE > len(d):
            raise Malformata(f"block {nb} starts beyond the end of the file")
        verso, canale, fine, istante, stream, lung, nosc = struct.unpack(
            BLOCCO, d[p:p + BLOCCO_BYTE])
        p += BLOCCO_BYTE
        # ⛔ The clock does not go backwards: §11.1 wants the milliseconds since the FIRST
        #    block, and the blocks are in wire order.
        if istante < ultimo_istante:
            raise Malformata(
                f"block {nb}: `istante_ms` = {istante}, and the block before "
                f"said {ultimo_istante}: §11.1 wants a MONOTONIC clock")
        ultimo_istante = istante
        if fine not in FINE:
            raise Malformata(
                f"block {nb}: `fine` is {fine}, and §11.1 defines three — "
                f"0 continues, 1 FIN, 2 RESET_STREAM")
        oscurati = []
        for _ in range(nosc):
            if p + 40 > len(d):
                raise Malformata(f"block {nb}: masked interval truncated")
            ini, qua = struct.unpack("!II", d[p:p + 8])
            p += 40
            if ini + qua > lung:
                raise Malformata(
                    f"block {nb}: masked interval [{ini},{ini + qua}) "
                    f"outside the payload of {lung} bytes")
            for o, q in oscurati:
                if not (ini + qua <= o or ini >= o + q):
                    raise Malformata(
                        f"block {nb}: two masked intervals overlap")
            oscurati.append((ini, qua))
        if p + lung > len(d):
            raise Malformata(f"block {nb}: the payload is truncated")
        if verso not in (CLIENT, SERVER):
            raise Malformata(f"block {nb}: direction {verso}, expected 1 or 2")
        for o, q in oscurati:
            if any(b != RIEMPIMENTO for b in d[p + o:p + o + q]):
                raise Malformata(
                    f"block {nb}: a masked interval is not made of 0x2A")
        fuori.append({"n": nb, "verso": verso, "canale": canale, "fine": fine,
                      "stream": stream, "base": p, "lung": lung,
                      "carico": d[p:p + lung], "oscurati": oscurati})
        p += lung
    if p != len(d):
        raise Malformata(
            f"{len(d) - p} bytes remain after the {quanti} declared blocks: either "
            f"`quanti_blocchi` is under-declared — and then there is wire that "
            f"nobody judged — or there is a tail that is not part of the format")
    return fuori


# ---------------------------------------------------------------------------
class ControlloIlleggibile(Exception):
    """⛔ The control channel cannot be scanned: P1 is not judged, it is DECLARED.

    ⚠ It is not `NonConforme`: the referee of that channel is
       `01-b4-validatore.py`, and giving a protocol red from here would
       mean accusing a defect another tool can name better.
       ⛔ And it is not silence either: the stream ends up in the
       «order unknown» denominator, which is printed.
    """


def tipi_di_controllo(carico):
    """The `tipo`s of the §6.1 messages inside a control channel block.

    ⛔ It serves **two things only**: knowing when `SESSIONE` passed (half of
       P1, §2.5) and when a `TELA` changed the **canvas in force** (half of
       P5, §6.2 corrected on 12 Aug 2026).  It judges nothing — the judgement
       of that channel belongs to `01-b4-validatore.py` — and that is why it stops at the
       first thing that does not add up instead of raising a red.

    ⛔ Returns `(tipo, corpo)`, not the type alone: of `TELA` the body is needed,
       and going back to read it a second time would mean scanning the same
       framing twice with two different readers.
    """
    tipi, i = [], 0
    while i < len(carico):
        if i + 6 > len(carico):
            raise ControlloIlleggibile(
                f"{len(carico) - i} bytes remain, and the framing of §6.1 "
                f"wants 6")
        tipo, lung = struct.unpack("!HI", carico[i:i + 6])
        if i + 6 + lung > len(carico):
            raise ControlloIlleggibile(
                f"the message {tipo:#06x} declares {lung} bytes of body and there "
                f"are {len(carico) - i - 6}")
        tipi.append((tipo, carico[i + 6:i + 6 + lung]))
        i += 6 + lung
    return tipi


def valida(percorso, guasti=(), tela=(1920, 1080), codec=1, stampa=True):
    with open(percorso, "rb") as f:
        d = f.read()
    blocchi = leggi_blocchi(d)

    if stampa:
        print(f"== the VIDEO channel referee — {percorso}")
        print(f"   blocks: {len(blocchi)}   bytes: {len(d)}")
        print(f"   ⛔ declared context: canvas {tela[0]}x{tela[1]}, codec "
              f"negotiated {codec}")
        print(f"      ⚠ and it must be DECLARED from outside: half of the rules of §6.2 "
              f"cannot")
        print(f"        be applied without it — «MUST be the one "
              f"negotiated in §4.3»,")
        print(f"        «is always that of the canvas».  A referee that "
              f"guessed them")
        print(f"        would be judging its own defaults")

    # ⛔ THE DENOMINATORS, AND THEY ARE FIVE BECAUSE THE THINGS ONE CAN HAVE FAILED TO
    #    LOOK AT ARE FIVE.  ⭐ `ordine_ignoto` was born with the `fine` field:
    #    it is the number of streams for which **P1 could not be judged**.
    # ⛔⛔ `tollerati` is from 12 Aug 2026 — defect **D14**: it is the number of
    #    streams that passed through the **sixth exception** of §3, that is those that
    #    carry a size in force since the queue started
    #    draining.  ⚠ It was called `grazia_ignota`, and it was the right name
    #    as long as the tolerance ended **by the clock**: §11.1 carries no instants,
    #    so «inside the second» and «outside» looked the same in a
    #    recording and the referee could only declare itself blind.  ⭐ Since the
    #    **P13** cure the tolerance ends at the **first keyframe at the new
    #    size** — a frame, not a time — and ⛔ **that blind half is
    #    gone**: not because the referee improved, but because the rule
    #    changed.  The number stays because §3 wants every tolerance
    #    **written**, not because there is something that could not be seen.
    conta = {"blocchi": len(blocchi), "video": 0, "flussi": 0,
             "giudicati": 0, "completezza_ignota": 0, "ordine_ignoto": 0,
             "tollerati": 0, "non_decide": 0}
    ctx = f24.Contesto(tela=tela, codec_negoziato=codec, sessione_aperta=True)

    # The video blocks are grouped by `stream`: one stream, one frame
    # (§6.2).  ⛔ And the order inside a stream is the file's, not that
    # of the `stream`: streams are independent and blocks interleave.
    #
    # ⛔⭐ AND WHILE SCANNING TWO THINGS ARE KEPT THAT A JUDGE OF THE SINGLE
    #     FRAME CANNOT HAVE — they are the two rules of 12 Aug that
    #     talk about **streams** instead of bytes:
    #
    #       `su_controllo`      P3 — which streams the control
    #                           channel lives on (§4.2: the first bidirectional).  A
    #                           video block on one of those is a `0x03` on the
    #                           control channel;
    #       `prima_di_sessione` P1 — which video streams start **before**
    #                           `SESSIONE` has passed.
    flussi, ordine, tele = {}, [], {}
    su_controllo, prima_di_sessione = set(), set()
    controllo_stream = {b["stream"] for b in blocchi if b["canale"] == CONTROLLO}
    sessione_vista, controllo_leggibile, perche_illeggibile = False, True, ""
    # ⛔⭐ THE CANVAS **IN FORCE**, AND IT CHANGES MIDWAY THROUGH THE SESSION — §6.2, corrected on
    #     12 Aug 2026.  It starts from the one declared from outside (which is the
    #     canvas of `SESSIONE`) and a `TELA(ADATTATA, …)` moves it.
    #     ⚠ The value is kept **at the moment each stream opens**, not
    #       the end-of-file one: judging a frame with a canvas granted
    #       after it would be reading the wire backwards.
    #     ⛔⛔ AND THE **PREVIOUS** ONE IS KEPT TOO — defect D14: the frames
    #        already in flight when the `TELA` passed carry it legitimately,
    #        and without having it at hand the referee cannot tell «an old
    #        size that is still arriving» from «a size that has never
    #        belonged to any canvas».  ⚠ `None` = nothing has ever changed.
    #     ⛔⛔ AND THE PREVIOUS ONES ARE A **LIST**, not a single one: §6.2 names «the
    #        previous canvas» in the singular, ⚠ but `ADATTA_TELA` is sent by the user
    #        dragging a window, and in one second they send several.  The
    #        list serves to **show** that hole (test
    #        `p8-due-tele-in-un-secondo`), not to plug it: the stream there comes out
    #        `AMBIGUO` with proposal P11, not ACCETTATO.
    tela_ora, tela_da_tela, tele_prec = tuple(tela), False, []
    for b in blocchi:
        if b["canale"] not in CANALI:
            raise NonConforme("RCP.md §2.5",
                              f"block {b['n']}: the high byte is "
                              f"{b['canale']:#04x}, outside the five channels",
                              b["base"], 0)
        if b["canale"] == CONTROLLO:
            # ⛔ It is read ONLY to know when `SESSIONE` passes (P1).  A
            #    masked interval does not get in the way: §11.1 uses it for the
            #    password (§4.4), which sits in the **body** of `CREDENZIALI`, and here
            #    the six bytes of the framing are looked at.
            try:
                for tipo, corpo in tipi_di_controllo(b["carico"]):
                    if b["verso"] != SERVER:
                        continue        # §7.1: both arrive from the server
                    if tipo == SESSIONE:
                        sessione_vista = True
                    elif tipo == TELA and len(corpo) >= 10:
                        # ⛔ §7.1: `tela_larghezza`/`tela_altezza` are «the canvas
                        #    in force AFTER this message» — and they are so even
                        #    when the outcome is RIFIUTATA, where they report the
                        #    previous one.  ⇒ the field is taken, not deduced
                        #    from the outcome: it is the field that is defined that way.
                        nuova = struct.unpack("!II", corpo[2:10])
                        # ⛔ The previous one is kept only if the canvas **really**
                        #    changes: a `TELA` reporting the same size —
                        #    which is what a `RIFIUTATA` does — leaves
                        #    nothing in flight, and recording it as a change
                        #    would open a grace that serves nobody.
                        if nuova != tela_ora:
                            tele_prec = [tela_ora] + tele_prec
                        tela_ora = nuova
                        tela_da_tela = corpo[0] == ADATTATA
            except ControlloIlleggibile as e:
                controllo_leggibile, perche_illeggibile = False, str(e)
            continue
        if b["canale"] != VIDEO:
            continue
        conta["video"] += 1
        # ⛔ G4 — THE FAULT THAT IS TODAY'S STATE OF `01-b4-validatore.py`.
        #
        #    Its line 521 declares it does not judge channels other than
        #    `0x00` and moves on.  Injected here, the video channel goes back to being
        #    looked at by nobody, and the file exits **3** — «nothing to
        #    judge» — which is exactly the honest verdict of a
        #    blind tool.  ⭐ If it exited **0** this fault would be
        #    invisible, and it is the reason code 3 exists.
        if "G4" in guasti:
            continue
        # ⛔ THE DIRECTION — §2.5: «a channel used in the wrong direction».  Video
        #    goes from the server to the client, and that is all.
        if b["verso"] != SERVER:
            raise NonConforme("RCP.md §2.5",
                              f"block {b['n']}: a frame FROM THE CLIENT — "
                              f"video goes from the server to the client",
                              b["base"], 0)
        if b["oscurati"]:
            # ⛔ §11.1: «the validator MUST NOT read inside a masked
            #    interval».  On a frame there are no secrets to hide
            #    — §4.4 talks about the password — so a masking here
            #    is a defect of the RECORDER, and it is said as such.
            raise Malformata(
                f"block {b['n']}: a masked interval on a VIDEO block. "
                f"§11.1 exists for the password (§4.4); a frame has "
                f"nothing to mask, and the validator cannot judge "
                f"what it is not allowed to read")
        if b["stream"] not in flussi:
            flussi[b["stream"]] = []
            ordine.append(b["stream"])
            # ⛔ The two stream rules are decided on the FIRST block of the
            #    stream, not on the last: it is the moment the stream
            #    opens, and it is the one §2.5 constrains.
            if b["stream"] in controllo_stream:
                su_controllo.add(b["stream"])
            if not sessione_vista:
                prima_di_sessione.add(b["stream"])
            tele[b["stream"]] = (tela_ora, tela_da_tela, list(tele_prec))
        flussi[b["stream"]].append(b)

    if not flussi:
        raise NienteDaGiudicare(
            f"{conta['blocchi']} blocks, {conta['video']} on the video channel, "
            f"ZERO streams to judge")

    conta["flussi"] = len(flussi)
    for sid in ordine:
        pezzi = flussi[sid]
        b0 = pezzi[0]

        # ── P3 — §2.5: «a `0x03` on the control channel is ERRORE_PROTOCOLLO»
        if sid in su_controllo:
            raise NonConforme(
                "RCP.md §2.5",
                f"stream {sid}: a frame on the CONTROL CHANNEL — the "
                f"same stream the `0x00` blocks travel on.  §2.5 wants "
                f"video «only on a unidirectional stream opened by the "
                f"server»",
                b0["base"], 0)

        # ── P1 — §2.5: «none before sending `SESSIONE`»
        if not controllo_leggibile:
            # ⛔ E8 the other way round: it does not conclude «so it was after».  It counts.
            conta["ordine_ignoto"] += 1
        elif sid in prima_di_sessione:
            raise NonConforme(
                "RCP.md §2.5",
                f"stream {sid}: a video stream opens BEFORE `SESSIONE` "
                f"has passed on the control channel — the client receives a "
                f"frame of which it knows neither the size nor the codec.  "
                f"It is invariant I3 on the wire",
                b0["base"], 0)

        # ── P5 — §6.2: the size MUST be that of the **canvas in force**, which is
        #    the one of `SESSIONE` or the last one granted by a `TELA` (§7.1).
        #    ⛔ The context is set back to the canvas that was in force WHEN
        #       this stream opened: it is the judge that applies the
        #       rule, but only the referee knows what had passed before.
        tela_fl, da_tela, prec_fl = tele.get(sid, (tuple(tela), False, []))
        if da_tela:
            # ⛔⛔ And the **draining queue** of D14 opens, with the previous
            #    canvases at hand.  ⭐ Since the **P13** cure the queue no longer ends
            #    by the clock but at the **first keyframe at the new size** —
            #    ⛔ and this changes the job of this file: the end of the
            #    tolerance has become **a fact that sits in the
            #    recording**.  Before it was one second, that is the only thing
            #    §11.1 does not carry, and the referee had to declare it could not
            #    judge it.
            ctx.adatta_tela(*tela_fl,
                            precedente=prec_fl[0] if prec_fl else None)
            # ⛔ And the previous ones are set **all**, not only the last: the
            #    judge reads the P11 window from them, and without them a
            #    session with two `TELA`s in a row would exit **1** — that is
            #    the referee would certify a healthy session killed.
            #    ⛔⭐ But **only while the queue is open**: if the keyframe at the
            #       new size has already passed in an earlier stream, putting
            #       the old canvases back here **would reopen** a tolerance §6.2
            #       has just closed — and the test `p13-vecchia-dopo-la-chiave-
            #       nuova` would exit 0 instead of 1.
            if not ctx.chiave_alla_tela_nuova:
                ctx.tele_recenti = list(prec_fl)
        else:
            ctx.tela_larghezza, ctx.tela_altezza = tela_fl
            # ⛔ And the context is RESET between one stream and the next: it is the same
            #    object for the whole recording, and a queue left open
            #    by an earlier stream would acquit the next stream.
            ctx.tela_precedente = None
            ctx.chiave_alla_tela_nuova = True
            ctx.tele_recenti = []

        # ── and the other four are applied by the judge, one byte at a time
        g = f24.Giudice(ctx, dove="uni", guasti=guasti)
        chiusura = pezzi[-1]["fine"]
        for b in pezzi[:-1]:
            if b["fine"] != CONTINUA:
                raise Malformata(
                    f"block {b['n']}: declares `fine = {b['fine']}` "
                    f"({FINE[b['fine']]}) but on stream {sid} more blocks "
                    f"arrive after.  ⛔ It is a defect of the RECORDER: a "
                    f"stream closes only once")

        # ⛔⭐ AND THE RESET WINS OVER THE HEADER — §6.2, finding R1.7.
        #
        #    *«a reset stream carries an INCOMPLETE frame: the client
        #    MUST throw away what it received»*, and the bytes of a truncated
        #    header **can be anything**.  ⛔ Reading it first
        #    would give `ERRORE_PROTOCOLLO` — that is it would drop the session —
        #    on a frame the server abandoned **on purpose**,
        #    which is the normal case of §5.1.
        #    ⚠ Fault **G3** lives right here, and to stay visible it must
        #      go through this branch: with `reset_come_fin` injected the reset
        #      stream is read as one closed with FIN, and that is what we
        #      want to see.
        if chiusura == RESET and not g.reset_come_fin:
            v = g.finisce("reset")
        else:
            for b in pezzi:
                g.arrivano(b["carico"])
                if g.verdetto is not None:
                    break
            if g.verdetto is not None:
                v = g.verdetto
            elif chiusura == CONTINUA:
                # ⛔ IT IS NO LONGER A HOLE IN THE FORMAT — it is a hole in the
                #    RECORDING.  Since 12 Aug 2026 §11.1 carries `fine`, and
                #    `fine = 0` on the last block of a stream means that
                #    the stream, **in this file**, never closed: the
                #    trace is cut in the middle, or the server was still in the
                #    middle of the frame.  ⚠ It is declared, not guessed: the
                #    completeness is precisely what §6.2 ties to the FIN.
                conta["completezza_ignota"] += 1
                conta["giudicati"] += 1
                if stampa:
                    print(f"   {GIALLO}?? stream {sid}: {g.byte_dati} bytes of "
                          f"data and `fine = 0` on the last block — ⛔ the stream "
                          f"does not close inside this recording, so "
                          f"completeness is NOT judged (§6.2){GRIGIO}")
                continue
            else:
                v = g.finisce("fin" if chiusura == FIN else "reset")
        conta["giudicati"] += 1
        if v.esito in (f24.ERRORE_PROTOCOLLO,):
            b0 = pezzi[0]
            rel = v.scostamento if v.scostamento is not None else 0
            raise NonConforme(v.regola, f"stream {sid}: {v.dice}",
                              b0["base"] + rel, rel)
        # ⭐⛔ D14 — the stream carries the **previous** canvas right after a
        #    `TELA(ADATTATA)`, and since the evening of 12 Aug 2026 §6.2 says it is
        #    ACCEPTED: it is the sixth exception of §3.  ⛔ But the grace
        #    **second** cannot be judged from a `.rcpreg` — §11.1 carries no instants —
        #    so the referee **counts** the streams acquitted by the exception instead
        #    of letting them be mixed up with those that were in order.  ⚠ It is the
        #    same line of §3: *«every tolerance must be written in the log»*.
        if v.tollerato:
            conta["tollerati"] += 1
        # ⛔⛔ AND THE TWO POINTS WHERE TONIGHT'S CURES DO NOT HOLD — P10 and P11.
        #    The referee neither condemns nor acquits: it declares.
        if v.esito == f24.AMBIGUO:
            conta["non_decide"] += 1
        if stampa:
            col = {f24.ACCETTATO: VERDE, f24.SCARTATO: GIALLO,
                   f24.AMBIGUO: GIALLO}[v.esito]
            extra = (f"   ⇒ proposal {v.propone}" if v.esito == f24.AMBIGUO
                     else "")
            print(f"   {col}{v.esito:18s}{GRIGIO} stream {sid}: {v.dice}{extra}")

    if stampa:
        print(f"\n   watched: {conta['blocchi']} blocks, of which "
              f"{conta['video']} on the video channel · {conta['flussi']} streams · "
              f"{conta['giudicati']} judged")
        if conta["completezza_ignota"]:
            print(f"   {GIALLO}⛔ and for {conta['completezza_ignota']} out of "
                  f"{conta['flussi']} the completeness could NOT be "
                  f"judged{GRIGIO}")
            print(f"      `fine = 0` on the last block: the stream does not "
                  f"close inside this")
            print(f"      file.  ⛔ It is NOT a defect of the wire, it is a "
                  f"defect of the")
            print(f"      RECORDING — since 12 Aug 2026 the format can ask "
                  f"the question")
        if conta["tollerati"]:
            print(f"   {GIALLO}⭐⛔ and {conta['tollerati']} streams out of "
                  f"{conta['flussi']} passed through the **SIXTH EXCEPTION** "
                  f"of §3{GRIGIO}")
            print(f"      they carry a size in force **since the queue started "
                  f"to")
            print(f"      drain**: they were already in flight when the "
                  f"`TELA(ADATTATA)` passed,")
            print(f"      and §6.2 says they are accepted and painted "
                  f"rescaled.  ⛔ And §3 wants")
            print(f"      the tolerance to be **written**: a silent tolerance "
                  f"is")
            print(f"      indistinguishable from a defect")
            print(f"      ⭐ And from here **where it ends** is judged too: it is no "
                  f"longer a second")
            print(f"        — which §11.1 does not carry — but the first **keyframe at the "
                  f"new size**,")
            print(f"        which is a frame and is in the recording "
                  f"(P13 cure)")
        if conta["non_decide"]:
            # ⛔ The counter stays at zero since P10 and P11 went into the
            #    document, and it stays **in the code**: the day `RCP.md`
            #    goes back to allowing two readings — it allowed twelve in
            #    phase 1 alone — this referee declares them instead of choosing
            #    one of the two silently.
            print(f"   {GIALLO}⛔⛔ and on {conta['non_decide']} streams `RCP.md` "
                  f"DOES NOT DECIDE{GRIGIO}")
            print(f"      ⚠ The referee neither condemns nor acquits: it declares, "
                  f"as it did for")
            print(f"        the eight double readings of 12 Aug 2026 before "
                  f"they became lines")
        if conta["ordine_ignoto"]:
            print(f"   {GIALLO}⛔ and for {conta['ordine_ignoto']} streams out of "
                  f"{conta['flussi']} it could NOT be judged whether they came "
                  f"before `SESSIONE`{GRIGIO}")
            print(f"      the control channel cannot be scanned: "
                  f"{perche_illeggibile}")
            print(f"      ⚠ and the one judging THAT channel is "
                  f"`01-b4-validatore.py`, not this one")
        print(f"   ⭐ conforming: no violation in {conta['giudicati']} "
              f"streams")
    return 0, conta


# ===========================================================================
# ⛔ THE TEST RECORDINGS — and they serve to certify the referee, not the wire.
#
#    §11: *«before concluding that the validator finds no errors, it is given
#    a recording WITH AN ERROR INSIDE and it is checked that it sees it.  A
#    tool that has never found anything is not a clean tool: it is
#    an uncertified tool»*.
def scrivi_reg(percorso, blocchi, magia=MAGIA, orologio=1):
    """⛔ `magia` is a parameter for ONE reason only: the test that must be
       refused.  A format that can write only its own version cannot
       certify that it can refuse the others."""
    # ⛔ `orologio = 1`: these tests are written from the client side, like the
    #    real traces of `02-filo-cliente.py`.  ⚠ Declaring another one would make
    #    the tests different from the traces the referee really judges.
    if magia == MAGIA_V1 or magia == MAGIA_V2:
        out = bytearray(magia + struct.pack("!II", len(blocchi), 0))
    else:
        out = bytearray(magia + struct.pack("!IBBBB", len(blocchi), orologio,
                                            0, 0, 0))
    for i, (verso, canale, fine, stream, carico) in enumerate(blocchi):
        if magia == MAGIA_V1:
            # the block of 10 Aug: 16 bytes, without `fine` and without instant
            out += struct.pack("!BBQIH", verso, canale, stream, len(carico), 0)
        elif magia == MAGIA_V2:
            # the block of 12 Aug: 17 bytes, with `fine` and without instant
            out += struct.pack("!BBBQIH", verso, canale, fine, stream,
                               len(carico), 0)
        else:
            # ⚠ The instant of a BUILT test is zero for all blocks, and it
            #   must be said: no time is measured here — the shape of the
            #   file is tested.  Zero is monotonic, so legal, and does not trigger
            #   any rule with time inside.
            out += struct.pack(BLOCCO, verso, canale, fine, 0, stream,
                               len(carico), 0)
        out += carico
    with open(percorso, "wb") as f:
        f.write(bytes(out))
    return percorso


def msg(tipo, corpo=b""):
    """A control message in the framing of §6.1."""
    return struct.pack("!HI", tipo, len(corpo)) + corpo


def apre_la_sessione(stream=0):
    """⛔ The block that makes LEGAL all the video that follows — P1.

    ⚠ The body of `SESSIONE` is empty, and it must be said: this referee reads of the
      control channel **only** the framing of §6.1, to know
      when that message passed.  Judging its body is
      `01-b4-validatore.py`'s job, and rewriting its judgement here would be the double
      reading `RCP.md` §0 exists to prevent.
    """
    return (SERVER, CONTROLLO, CONTINUA, stream, msg(SESSIONE))


def adatta_la_tela(lar, alt, esito=ADATTATA, stream=0):
    """⛔ `TELA` — §7.1: *«the canvas in force AFTER this message»*.

    It is the message that corrected `RCP.md`: without it P5 said «the canvas
    granted in `SESSIONE`», and a user dragging a window lost the
    session (§7.1, exception 4 of §3).
    """
    return (SERVER, CONTROLLO, CONTINUA, stream,
            msg(TELA, struct.pack("!BBII", esito, 0, lar, alt)))


def chiave(stream=8, coda=64, **campi):
    return [apre_la_sessione(),
            (SERVER, VIDEO, FIN, stream, f24.intestazione(**campi) + b"\x00" * coda)]


# ⛔ Every test declares its own exit code BEFORE being run, and
#    `tela` sits here and not in the defaults because P5 is tested **by changing it**.
PROVE = {
    "buona": {
        "spiega": "⭐ a conforming keyframe in three blocks on the same "
                  "stream, after `SESSIONE`: it is the case phase 2 exists "
                  "to produce, ⛔ and it is the case that RESPECTS all six "
                  "lines of 12 Aug in one go",
        "uscita": 0,
        "blocchi": lambda: [
            apre_la_sessione(),
            (SERVER, VIDEO, CONTINUA, 8, f24.intestazione()),
            (SERVER, VIDEO, CONTINUA, 8, b"\x00" * 2048),
            (SERVER, VIDEO, FIN, 8, b"\x00" * 2048)],
    },
    "abbandonato": {
        "spiega": "⭐⛔ a stream RESET midway — §5.1, the server abandons "
                  "a frame **on purpose**.  ⛔ It exits **0**: the "
                  "frame is thrown away and **the session holds**.  ⚠ Without the "
                  "`fine` field this recording was indistinguishable from "
                  "one truncated by mistake, and it is the E8 form P7 was "
                  "written for",
        "uscita": 0,
        "blocchi": lambda: [
            apre_la_sessione(),
            (SERVER, VIDEO, CONTINUA, 8, f24.intestazione()),
            (SERVER, VIDEO, RESET, 8, b"\x00" * 10240)],
    },
    "stream-non-chiuso": {
        "spiega": "⛔ the last block of the stream carries `fine = 0`: the stream "
                  "does not close inside the file.  It exits **0** — there is "
                  "no violation — ⛔ but completeness is declared NOT "
                  "judged, which is a different fact from «judged and fine»",
        "uscita": 0,
        "blocchi": lambda: [
            apre_la_sessione(),
            (SERVER, VIDEO, CONTINUA, 8, f24.intestazione() + b"\x00" * 64)],
    },
    "formato-vecchio": {
        "spiega": "⛔⛔ a «RCPREG 0x00 0x01» recording, yesterday's "
                  "format.  §11.1: *«an old validator must REFUSE the "
                  "new format, not read it askew»* — and it holds both "
                  "ways.  ⛔ It exits **2**: it is a defect of the FILE, not of the wire, "
                  "and the cure is to regenerate it",
        "uscita": 2,
        "magia": MAGIA_VECCHIA,
        "blocchi": lambda: chiave(),
    },
    "formato-del-12-agosto": {
        "spiega": "⛔⛔ a «RCPREG 0x00 0x02» recording: the block carries "
                  "`fine` but NOT `istante_ms`, and measures 17 bytes instead of 21.  "
                  "⚠ Refusing `0x01` is not enough: that is another line, and "
                  "without this test it could be deleted and the bench "
                  "would stay green.  ⛔ It is exactly the form in which the "
                  "12 Aug defect lived for four days",
        "uscita": 2,
        "magia": MAGIA_V2,
        "blocchi": lambda: chiave(),
    },
    "orologio-non-dichiarato": {
        "spiega": "⛔ `orologio` = 0 in the header: §11.1 defines two "
                  "(1 = the times are the client's, 2 = the server's).  ⚠ This "
                  "referee does not judge time, but a file that does not declare "
                  "WHOSE the clock is is malformed for anyone — and the two "
                  "referees of the project must not give two different verdicts "
                  "on the same file",
        "uscita": 2,
        "orologio": 0,
        "blocchi": lambda: chiave(),
    },
    "tipo-storto": {
        "spiega": "`tipo = 0x0300` in the header: §6.2 «Other values: "
                  "ERRORE_PROTOCOLLO»",
        "uscita": 1,
        "blocchi": lambda: chiave(tipo=0x0300),
    },
    "verso-sbagliato": {
        "spiega": "a frame FROM THE CLIENT: §2.5, the channel in the wrong "
                  "direction",
        "uscita": 1,
        "blocchi": lambda: [apre_la_sessione(),
                            (CLIENT, VIDEO, FIN, 9,
                             f24.intestazione() + b"\x00" * 64)],
    },
    # ── ⭐⛔ THE SIX LINES OF 12 AUG, ONE TEST EACH ───────────────────────
    "p1-prima-di-sessione": {
        "spiega": "⭐⛔ **P1 violated** — a video stream opens and in the file "
                  "`SESSIONE` has not passed yet.  ⛔ And the test that "
                  "RESPECTS it is `buona`: the same bytes, with the "
                  "`SESSIONE` block in front",
        "uscita": 1,
        "blocchi": lambda: [(SERVER, VIDEO, FIN, 8,
                             f24.intestazione() + b"\x00" * 64)],
    },
    "p2-numero-zero": {
        "spiega": "⭐⛔ **P2 violated** — `numero = 0`, which §6.2 reserves for "
                  "«no frame» since 12 Aug 2026",
        "uscita": 1,
        "blocchi": lambda: chiave(num=0),
    },
    "p3-video-sul-controllo": {
        "spiega": "⭐⛔ **P3 violated** — the 28-byte header written "
                  "on the **same stream** the control channel "
                  "travels on.  ⛔ It is the only place where the server can "
                  "get the stream wrong: §2.5 forbids it from opening bidirectional ones",
        "uscita": 1,
        "blocchi": lambda: [apre_la_sessione(),
                            (SERVER, VIDEO, FIN, 0,
                             f24.intestazione() + b"\x00" * 64)],
    },
    "p4-fin-prima-dei-28": {
        "spiega": "⭐⛔ **P4 violated** — the stream closes with **FIN** after "
                  "12 bytes: it is not a short frame, it is a length that "
                  "does not add up (§6.2, third line)",
        "uscita": 1,
        "blocchi": lambda: [apre_la_sessione(),
                            (SERVER, VIDEO, FIN, 8,
                             f24.intestazione()[:12])],
    },
    "p5-misura-diversa": {
        "spiega": "⭐⛔ **P5 violated** — a 1280x720 frame on a granted "
                  "1920x1080 canvas",
        "uscita": 1,
        "blocchi": lambda: chiave(lar=1280, alt=720),
    },
    "p5-misura-dopo-adatta-tela": {
        "spiega": "⭐⛔ **P5 respected, and it is the test that corrected "
                  "`RCP.md`** — the **very same bytes** as "
                  "`p5-misura-diversa`, but between `SESSIONE` and the frame "
                  "a `TELA(ADATTATA, 1280, 720)` passes (§7.1).  ⛔ With the "
                  "first draft of P5 — «the canvas granted in `SESSIONE`» — "
                  "this recording exited **1**: the client killed the "
                  "session because the user had dragged a window.  "
                  "⚠ Without this test the new rule would be as strict as "
                  "the wrong one before, and no bench would say so",
        "uscita": 0,
        "blocchi": lambda: [
            apre_la_sessione(),
            adatta_la_tela(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.intestazione(lar=1280, alt=720) + b"\x00" * 64)],
    },
    "p5-misura-uguale-a-una-tela-diversa": {
        "spiega": "⭐ **P5 respected, and NOT with the default canvas** — the "
                  "**same bytes** as the test above, with the canvas granted "
                  "at 1280x720.  ⛔ Without this test, a referee that "
                  "compared with a 1920x1080 written by hand would be green "
                  "on all the others",
        "uscita": 0,
        "tela": (1280, 720),
        "blocchi": lambda: chiave(lar=1280, alt=720),
    },
    # ── ⛔⛔ D14 — THE FRAMES IN FLIGHT, and proposal **P8** ─────────────────
    "p8-in-volo-dopo-adatta-tela": {
        "spiega": "⭐⛔ **P8 RESPECTED — AND IT IS THE RECORDING OF A "
                  "HEALTHY SESSION THAT UNTIL TONIGHT DROPPED** — `SESSIONE` at "
                  "1920x1080, then a `TELA(ADATTATA, 1280, 720)` (§7.1), and "
                  "**then** the video stream arrives still carrying 1920x1080: "
                  "it is the frame opened **before** the `ADATTA_TELA` "
                  "reached the server.  ⛔ Until tonight §6.2 to the letter "
                  "made it exit **1** — the session dropped without anybody "
                  "having made a mistake — and this test exited 0 with an `AMBIGUO`. "
                  "⭐ Now §6.2 carries a one-second grace (sixth "
                  "exception of §3): it exits **0** and the stream is ACCEPTED with the "
                  "**tolerance declared**.  ⚠ And the **second** cannot be "
                  "judged from here: §11.1 carries no instants, and the referee declares it "
                  "instead of guessing it",
        "uscita": 0,
        "blocchi": lambda: [
            apre_la_sessione(),
            adatta_la_tela(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.intestazione(lar=1920, alt=1080, num=41) + b"\x00" * 64)],
    },
    "p11-due-tele-nella-finestra": {
        "spiega": "⭐⛔ **P11 respected — and it is the scene that killed a "
                  "healthy session ONE STEP FURTHER ON** — `SESSIONE` at "
                  "1920x1080, `TELA(ADATTATA, 1600, 900)`, `TELA(ADATTATA, "
                  "1280, 720)`, and then the video stream carrying 1920x1080: the "
                  "**keyframe** opened before everything, which §5.2 forbids the server "
                  "to abandon.  ⛔ With «the **previous** canvas» in the "
                  "singular it was neither the one in force nor the previous one, and "
                  "§6.2 said `ERRORE_PROTOCOLLO` **at once**: the healthy session "
                  "dropped anyway.  ⭐ Now the grace covers «a canvas that "
                  "was in force within the second just passed»: it exits "
                  "**0**, with the tolerance declared.  ⚠ Whoever drags a "
                  "window sends more than one `ADATTA_TELA` per second: this "
                  "is not the rare scene, it is the normal one",
        "uscita": 0,
        "blocchi": lambda: [
            apre_la_sessione(),
            adatta_la_tela(1600, 900),
            adatta_la_tela(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.intestazione(lar=1920, alt=1080, num=41) + b"\x00" * 64)],
    },
    "p13-vecchia-dopo-la-chiave-nuova": {
        "spiega": "⭐⛔ **P13 violated — and this test could not be written "
                  "BEFORE** — `SESSIONE` at 1920x1080, `TELA(ADATTATA, 1280, "
                  "720)`, then the **keyframe at 1280x720** on stream 8 (the queue "
                  "has drained: §5.2 guarantees it and §6.2 uses it as the end "
                  "of the tolerance), and **then** a frame at 1920x1080 on "
                  "stream 9.  ⛔ It exits **1**: from that keyframe on the old "
                  "size is no longer a frame in flight, it is a server that "
                  "captures at a canvas no longer in force.  ⭐ And the point "
                  "is that **the end of the tolerance sits in the recording**: "
                  "as long as it was «after one second» this referee could not "
                  "judge it at all — §11.1 carries no instants — and had to "
                  "declare itself blind.  The P13 cure did not only save a "
                  "session on the slow line: it made the line **verifiable "
                  "by a mechanical referee**",
        "uscita": 1,
        "blocchi": lambda: [
            apre_la_sessione(),
            adatta_la_tela(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.intestazione(lar=1280, alt=720, num=41) + b"\x00" * 64),
            # ⛔ `numero` 42, that is captured AFTER the keyframe at the new size:
            #    it is not a frame in flight, it is a server that went on
            #    capturing at the old canvas.  ⚠ With number **40** it would be the
            #    scene of finding **P14**, and it is not the same thing.
            (SERVER, VIDEO, FIN, 9,
             f24.intestazione(lar=1920, alt=1080, num=42) + b"\x00" * 64)],
    },
    "p14-in-volo-scavalcato-dalla-chiave": {
        "spiega": "⭐⛔⛔ **P14 — and until an hour ago this recording exited "
                  "1** — the keyframe at 1280x720 (`numero` 41) arrives **before** "
                  "the frame in flight at 1920x1080, which carries `numero` **40** "
                  "because it was captured before the `TELA`.  ⚠ It is the "
                  "normal scene: the old frame is the biggest (§5.2 "
                  "forbids abandoning a keyframe) and the streams are "
                  "independent, so the new keyframe **overtakes** it.  ⛔ The "
                  "tolerance ended on that keyframe, and the old size "
                  "made the session drop.  ⭐ Now §6.2 says that "
                  "**order is applied before size**: the stream is "
                  "DISCARDED — «and its size is not even looked at» — and the "
                  "recording exits **0**, because a discard is not a "
                  "violation of the wire (§5.1)",
        "uscita": 0,
        "blocchi": lambda: [
            apre_la_sessione(),
            adatta_la_tela(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.intestazione(lar=1280, alt=720, num=41) + b"\x00" * 64),
            (SERVER, VIDEO, FIN, 9,
             f24.intestazione(lar=1920, alt=1080, num=40) + b"\x00" * 64)],
    },
    "p11-misura-mai-in-vigore": {
        "spiega": "⭐⛔ **P11 violated, and it is the test that keeps the window "
                  "TIGHT** — **the same two-`TELA` recording**, but the "
                  "frame carries 800x600: ⛔ a size that in that "
                  "window was **never** in force — not 1920x1080, "
                  "not 1600x900, not 1280x720.  It exits **1**, and it must exit 1.  "
                  "⚠ Without this test, a window written «during the "
                  "second the size is not checked» would pass the test "
                  "above and switch off P5 right where the server is most "
                  "likely to err",
        "uscita": 1,
        "blocchi": lambda: [
            apre_la_sessione(),
            adatta_la_tela(1600, 900),
            adatta_la_tela(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.intestazione(lar=800, alt=600, num=41) + b"\x00" * 64)],
    },
    # ── ⭐⛔ D13 — THE KEYFRAME AT EVERY CANVAS CHANGE (§5.2), tonight's line ─
    "p9-delta-alla-misura-nuova": {
        "spiega": "⭐⛔ **P9 violated** — after a `TELA(ADATTATA, 1280, 720)` the "
                  "first frame at the **new** size is a **delta**.  ⛔ "
                  "`[M]` 12 Aug 2026: with only deltas at the new size "
                  "Chrome on HEVC paints 5 frames at the OLD size "
                  "without raising any error — the symptom would be «the "
                  "desktop tears when I resize the window»",
        "uscita": 1,
        "blocchi": lambda: [
            apre_la_sessione(),
            (SERVER, VIDEO, FIN, 7, f24.intestazione(num=1) + b"\x00" * 64),
            adatta_la_tela(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.intestazione(tipo=0x0302, lar=1280, alt=720, num=2)
             + b"\x00" * 64)],
    },
    "p9-chiave-alla-misura-nuova": {
        "spiega": "⭐ **P9 respected** — the **very same bytes**, with "
                  "`tipo = 0x0301`.  ⛔ Without this test a rule written "
                  "«after a `TELA` nothing is accepted» would stay green on "
                  "the one that violates it.  ⚠ And the referee judges **less** than "
                  "what §5.2 says: it sees that it is a keyframe, not that it is a "
                  "**real** keyframe — the parameter sets sit in the data, and the judge "
                  "does not keep the data",
        "uscita": 0,
        "blocchi": lambda: [
            apre_la_sessione(),
            (SERVER, VIDEO, FIN, 7, f24.intestazione(num=1) + b"\x00" * 64),
            adatta_la_tela(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.intestazione(tipo=0x0301, lar=1280, alt=720, num=2)
             + b"\x00" * 64)],
    },
    "p9-delta-dopo-la-chiave-nuova": {
        "spiega": "⭐⛔ **P9, the second face: the debt is paid ONCE** "
                  "— keyframe at 1280x720 on stream 8, **then** a delta at "
                  "1280x720 on stream 9.  ⛔ Without this test, a referee "
                  "that had understood §5.2 as «after a `TELA` deltas are not "
                  "accepted» would stop the video **after every "
                  "resize**, and that is where phase 3 lives.  ⚠ And it also tests "
                  "something of this file: the context is set back "
                  "**stream by stream**, and a `TELA` repeating the "
                  "size in force must not reopen the debt",
        "uscita": 0,
        "blocchi": lambda: [
            apre_la_sessione(),
            (SERVER, VIDEO, FIN, 7, f24.intestazione(num=1) + b"\x00" * 64),
            adatta_la_tela(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.intestazione(tipo=0x0301, lar=1280, alt=720, num=2)
             + b"\x00" * 64),
            (SERVER, VIDEO, FIN, 9,
             f24.intestazione(tipo=0x0302, lar=1280, alt=720, num=3)
             + b"\x00" * 64)],
    },
    "p8-misura-di-nessuna-tela": {
        "spiega": "⭐⛔ **P8 covers ONE size, not «everything after a `TELA`»** — "
                  "same recording, but the frame carries 800x600: ⛔ neither "
                  "the canvas in force (1280x720) nor the previous one (1920x1080). "
                  "It was not in flight, it is a wrong field — it exits **1**, and it must "
                  "exit 1.  ⚠ **It is the test that counts**: without it, a cure "
                  "written «after a `TELA` the size is not checked» "
                  "would pass the test above and switch off P5 right in the "
                  "window where the server is most likely to err — and "
                  "it is exactly how P5 ended up wrong the first "
                  "time",
        "uscita": 1,
        "blocchi": lambda: [
            apre_la_sessione(),
            adatta_la_tela(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.intestazione(lar=800, alt=600, num=41) + b"\x00" * 64)],
    },
    "p6-primo-delta": {
        "spiega": "⭐⛔ **P6 violated** — the first frame after `SESSIONE` is "
                  "a delta (`0x0302`).  ⚠ Until 11 Aug it conformed to "
                  "every line, and the symptom would have been «the desktop appears in "
                  "pieces»",
        "uscita": 1,
        "blocchi": lambda: chiave(tipo=0x0302),
    },
    "p6-delta-dopo-la-chiave": {
        "spiega": "⭐ **P6 respected from the hard side** — keyframe on "
                  "stream 8, **then** a delta on stream 9.  ⛔ Without this "
                  "test, a referee that had understood «deltas are not "
                  "accepted» would stay green on everything and stop the video "
                  "from phase 3 on",
        "uscita": 0,
        "blocchi": lambda: [
            apre_la_sessione(),
            (SERVER, VIDEO, FIN, 8, f24.intestazione(num=1) + b"\x00" * 64),
            (SERVER, VIDEO, FIN, 9,
             f24.intestazione(tipo=0x0302, num=2) + b"\x00" * 64)],
    },
    # ── the three outcomes that are not a judgement on the wire ─────────────
    "solo-controllo": {
        "spiega": "⛔ a handshake-only recording: ZERO video "
                  "blocks.  «I have nothing to judge» and «I judged everything "
                  "and it is fine» are two different facts",
        "uscita": 3,
        "blocchi": lambda: [(CLIENT, CONTROLLO, CONTINUA, 0, msg(0x0001))],
    },
    "coda-di-troppo": {
        "spiega": "⛔ `quanti_blocchi` under-declared: wire that nobody "
                  "judges.  It is a defect of the FILE, not of the wire",
        "uscita": 2,
        "blocchi": None,
    },
    "canale-ignoto": {
        "spiega": "a high byte that is none of the five of §2.5",
        "uscita": 1,
        "blocchi": lambda: [apre_la_sessione(),
                            (SERVER, 0x09, FIN, 8, b"\x00" * 28)],
    },
    "controllo-illeggibile": {
        "spiega": "⛔ the control channel cannot be scanned — a message that "
                  "declares more body than there is — and there is a conforming "
                  "video stream.  ⭐ It exits **0**, ⛔ but P1 is declared NOT "
                  "judged: «so it was after `SESSIONE`» would be form "
                  "**E8**.  ⚠ And the one judging that channel is "
                  "`01-b4-validatore.py`, not this one",
        "uscita": 0,
        "blocchi": lambda: [
            (SERVER, CONTROLLO, CONTINUA, 0, struct.pack("!HI", SESSIONE, 99)),
            (SERVER, VIDEO, FIN, 8, f24.intestazione() + b"\x00" * 64)],
    },
    "fine-fuori-intervallo": {
        "spiega": "⛔ `fine = 7`, and §11.1 defines **three**.  ⚠ It tests that the "
                  "new field is read and not just skipped: without it, a "
                  "recorder that wrote garbage in that byte "
                  "would pass, and with it every completeness judgement",
        "uscita": 2,
        "blocchi": lambda: [(SERVER, VIDEO, 7, 8, f24.intestazione())],
    },
}

# ⛔ WHICH TEST TRIGGERS WHICH LINE, AND WHICH ONE RESPECTS IT — and the count is
#    computed by `regole_coperte()`, which **looks them up** in `PROVE`.
REGOLE_NUOVE = {
    "P1": ("RCP.md §2.5", "p1-prima-di-sessione", "buona"),
    "P2": ("RCP.md §6.2", "p2-numero-zero", "buona"),
    "P3": ("RCP.md §2.5", "p3-video-sul-controllo", "buona"),
    "P4": ("RCP.md §6.2", "p4-fin-prima-dei-28", "buona"),
    "P5": ("RCP.md §6.2", "p5-misura-diversa", "p5-misura-dopo-adatta-tela"),
    "P6": ("RCP.md §5.2", "p6-primo-delta", "p6-delta-dopo-la-chiave"),
    "P7": ("RCP.md §11.1", "formato-vecchio", "abbandonato"),
    # ── ⭐⛔ AND THE TWO OF THE **EVENING** OF 12 AUG — D14 and D13 ───────────
    #    ⚠ Until that evening P8 sat in `PROPOSTE_APERTE` and its test
    #      exited 0 **declaring**; now it exits 0 **accepting**, and it is a
    #      different fact that can be read in the printed line.
    "P8": ("RCP.md §6.2 in coda, §3 eccezione 6",
           "p8-misura-di-nessuna-tela", "p8-in-volo-dopo-adatta-tela"),
    "P9": ("RCP.md §5.2, the canvas change",
           "p9-delta-alla-misura-nuova", "p9-chiave-alla-misura-nuova"),
    # ── ⭐⛔ AND THE TENTH, BORN FROM THE EIGHTH AND APPLIED IN THE NEXT ROUND ─
    "P11": ("RCP.md §6.2 — the window instead of «the previous one»",
            "p11-misura-mai-in-vigore", "p11-due-tele-nella-finestra"),
    # ⭐⛔ And P13, which this referee **could not judge at all before**: the
    #    tolerance ended by the clock, and §11.1 carries no instants.  Now
    #    it ends at the first keyframe at the new size, which is a frame —
    #    and frames are in the recording.
    "P13": ("RCP.md §6.2 — the tolerance ends at the KEYFRAME, not by the clock",
            "p13-vecchia-dopo-la-chiave-nuova", "p8-in-volo-dopo-adatta-tela"),
    # ⭐⛔ P14 — and the pair here has the same form as the others only by chance:
    #    the one that «respects» it exits **0** because the stream is DISCARDED, not
    #    because it is conforming.  ⚠ A discard and a good frame have the
    #    same exit code, and the printed line tells them apart: it is the same
    #    reason this referee counts streams instead of counting
    #    codes.
    "P14": ("RCP.md §6.2 — order is applied BEFORE size",
            "p13-vecchia-dopo-la-chiave-nuova",
            "p14-in-volo-scavalcato-dalla-chiave"),
}


# ⛔⛔ AND THE PROPOSALS STILL OPEN, IN A SEPARATE TABLE — what `RCP.md`
#    does NOT say yet.  ⚠ The separation is the important thing: above there are
#    normative lines to reread in the document, here a cure the
#    coordinator has not applied.  ⛔ And the pair has a different form: the
#    test that SHOWS it exits **0** (the referee declares, it does not condemn) and
#    the one that keeps the cure tight exits **1**.
# ⭐ EMPTY since the evening of 12 Aug 2026, and it declares itself empty instead of disappearing:
#    the two cures that sat here — P10 and P11 — went into `RCP.md` the round
#    after being found, and their cases moved to verdict.  ⛔ The
#    place stays because the next point where the document does not decide will have
#    somewhere to sit, and `proposte_coperte()` keeps saying «0 of 0» — which is a
#    number, not a silence.
PROPOSTE_APERTE = {}

# ⛔⛔ AND WHAT CANNOT BE JUDGED FROM A RECORDING AT ALL — it is declared, not
#    faked.  ⚠ A proposal without a test put together with those that have the test
#    would inflate the count, and it is the same reason
#    `REGOLE_NUOVE` and `PROPOSTE_APERTE` sit in two tables.
FUORI_PORTATA = {
    "P10": ("§5.2 says **when** the client reconfigures the decoder — "
            "*«on the first KEYFRAME at the new size, not on the `TELA`»* — and it is "
            "the line that reconciled the two cures of 12 Aug, which "
            "on the same frame commanded the opposite.  ⛔ From a "
            "`.rcpreg` it is not judged: the recording carries the wire, and **which "
            "size the decoder is configured at is not on the wire**.  "
            "The two cases sit in `02-filo-fotogramma.py` "
            "(`p10-decodificatore-al-tela` and `p10-decodificatore-alla-"
            "chiave`), where the client's state is **declared** — and there it does not "
            "change the outcome, it changes the **finding**"),
}


def proposte_coperte():
    """⛔ Like `regole_coperte()`, for the cures the document does not have yet."""
    coperte, mancanti = [], []
    for sigla, (_, stretta, vede) in PROPOSTE_APERTE.items():
        buchi = []
        if stretta not in PROVE:
            buchi.append(f"the test that keeps it TIGHT is missing («{stretta}»)")
        elif PROVE[stretta]["uscita"] != 1:
            buchi.append(f"«{stretta}» does not require exit 1: a cure without "
                         f"this test gets written too broad")
        if vede not in PROVE:
            buchi.append(f"the test that SHOWS it is missing («{vede}»)")
        elif PROVE[vede]["uscita"] != 0:
            buchi.append(f"«{vede}» does not require exit 0")
        (mancanti if buchi else coperte).append(
            (sigla, "; ".join(buchi)) if buchi else sigla)
    return coperte, mancanti


def regole_coperte():
    """⛔ How many lines REALLY have the test that violates them and the one that
       respects them, **looked up in `PROVE`** — never a number written by hand."""
    coperte, mancanti = [], []
    for sigla, (_, viola, rispetta) in REGOLE_NUOVE.items():
        buchi = []
        if viola not in PROVE:
            buchi.append(f"the test that VIOLATES it is missing («{viola}»)")
        elif PROVE[viola]["uscita"] not in (1, 2):
            buchi.append(f"«{viola}» does not require a refusal")
        if rispetta not in PROVE:
            buchi.append(f"the test that RESPECTS it is missing («{rispetta}»)")
        elif PROVE[rispetta]["uscita"] != 0:
            buchi.append(f"«{rispetta}» does not require exit 0")
        (mancanti if buchi else coperte).append(
            (sigla, "; ".join(buchi)) if buchi else sigla)
    return coperte, mancanti


def fabbrica(cartella):
    fatti = []
    for nome, v in PROVE.items():
        p = os.path.join(cartella, f"02-filo-prova-{nome}.rcpreg")
        magia = v.get("magia", MAGIA)
        if v["blocchi"] is None:
            # the garbage tail is built by hand
            scrivi_reg(p, chiave())
            with open(p, "ab") as fh:
                fh.write(b"spazzatura")
        else:
            scrivi_reg(p, v["blocchi"](), magia=magia,
                       orologio=v.get("orologio", 1))
        fatti.append((nome, p, v["uscita"], v["spiega"],
                      v.get("tela", (1920, 1080))))
        print(f"   {os.path.basename(p):50s} expected exit {v['uscita']}")
        print(f"   {'':50s} {v['spiega']}")
    return fatti


def gira_prove(cartella, guasti=(), stampa=True):
    """⛔ Every test declares its own exit code BEFORE being run."""
    fatti = fabbrica(cartella) if stampa else _fabbrica_muta(cartella)
    guastati, righe = 0, []
    if stampa:
        print()
    for nome, p, atteso, spiega, tela in fatti:
        try:
            visto, _ = valida(p, guasti=guasti, tela=tela, stampa=False)
        except NonConforme:
            visto = 1
        except Malformata:
            visto = 2
        except NienteDaGiudicare:
            visto = 3
        except OSError:
            visto = 2
        ok = visto == atteso
        guastati += int(not ok)
        righe.append({"prova": nome, "atteso": atteso, "visto": visto,
                      "esito": bool(ok)})
        if stampa:
            print(f"    {VERDE if ok else ROSSO}{'OK' if ok else 'NO'}{GRIGIO}  "
                  f"{nome:36s} exit {visto} (expected {atteso})")
            if not ok:
                print(f"        {spiega}")
    return guastati, righe


def _fabbrica_muta(cartella):
    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        return fabbrica(cartella)


P7 = (
    "§11.1, the recording block — how the stream ended",
    "⭐ APPLIED TO `RCP.md` ON 12 AUG 2026.  The block carries, after "
    "`canale`, a `u8 fine`: `0` = the stream continues, `1` = closed with "
    "**FIN**, `2` = reset with **RESET_STREAM**; and the magic moved to "
    "`\"RCPREG\" 0x00 0x02` because the block changes size — 17 bytes instead "
    "of 16 — and an old validator MUST refuse the new format instead of "
    "reading it askew.  Without that field an abandoned frame (§5.1, "
    "legal) and one truncated by mistake (§3, the connection drops) looked the "
    "same in the recording, that is the referee could not apply "
    "the line §6.2 added on purpose on 9 Aug 2026.")


def scrivi_esito(percorso, rec):
    if not percorso:
        print("    ⚠ no --uscita: this round leaves NO log")
        return False
    fuori = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "banco": "F2.4-validatore",
             "scena": "recordings built by this same file, in the "
                      "format of RCP.md §11.1: no network and no server",
             "macchina": os.uname().nodename}
    fuori.update(rec)
    try:
        with open(percorso, "a") as f:
            f.write(json.dumps(fuori, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except OSError as e:
        print(f"    {ROSSO}⛔ the log «{percorso}» cannot be written: {e}{GRIGIO}")
        return False
    return True


def certifica(a):
    """⛔ healthy -> G4 -> healed.  And G4 IS TODAY'S STATE OF `01-b4`.

    The fault to inject is not invented: it is *«the validator skips the video
    channel»*, that is line 521 of `01-b4-validatore.py`.  ⭐ Certifying against
    that fault is the only way of proving that this file **adds**
    something instead of repeating B4 in other words.
    """
    print("\n== ⛔ THE CERTIFICATION — healthy -> G4 -> healed")
    print("   G4: «the referee skips the video channel», which is what")
    print("       `01-b4-validatore.py` does today (its line 521).")
    print("   expected healthy: 0 wrong tests")
    print("   expected fault:   the tests that must exit 1 exit 3 —")
    print("                     «nothing to judge» — because the video channel")
    print("                     is not looked at.  ⛔ And they do NOT exit 0: a")
    print("                     referee that skips everything does not acquit, it declares")
    print("                     it did not look.  If it exited 0 the fault")
    print("                     would have passed for a green\n")
    sano, righe_sane = gira_prove(a.cartella, guasti=())
    print()
    rotto, righe_rotte = gira_prove(a.cartella, guasti=("G4",))
    print()
    # ⛔ THE MARK, WITH ITS TWO HALVES (R12-A.3): the faulty round must say it
    #    and the healthy round must NOT already say it.
    marca_rotto = sum(1 for r in righe_rotte
                      if r["atteso"] == 1 and r["visto"] == 3)
    marca_sano = sum(1 for r in righe_sane
                     if r["atteso"] == 1 and r["visto"] == 3)
    risanato, _ = gira_prove(a.cartella, guasti=(), stampa=False)
    ok = (sano == 0 and rotto > 0 and marca_rotto > 0 and marca_sano == 0
          and risanato == 0)
    print(f"    {VERDE if ok else ROSSO}{'OK' if ok else 'NO'}{GRIGIO}  G4  "
          f"healthy {sano} -> fault {rotto} -> healed {risanato}   "
          f"mark «exit 3 where 1 was needed»: {marca_rotto} times with the "
          f"fault, {marca_sano} times when healthy")
    scrivi_esito(a.uscita, {"tipo": "certificazione", "guasto": "G4",
                            "sano": sano, "guasto_conta": rotto,
                            "risanato": risanato, "marca_col_guasto": marca_rotto,
                            "marca_da_sano": marca_sano, "esito": bool(ok),
                            "prove_sane": righe_sane, "prove_rotte": righe_rotte})
    print()
    if ok:
        print(f"    {VERDE}⭐ 02-filo-validatore.py IS CERTIFIED{GRIGIO}")
        return 0
    print(f"    {ROSSO}⛔ NOT certified{GRIGIO}")
    return 1


def principale(a):
    if a.elenco:
        print("== the test recordings, and the expected exit code of "
              "each")
        print("   ⛔ Every line is a PREDICTION, written before the round\n")
        for nome, v in PROVE.items():
            print(f"  {nome:36s} exit {v['uscita']}"
                  + (f"   canvas {v['tela'][0]}x{v['tela'][1]}"
                     if "tela" in v else ""))
            print(f"  {'':36s}   {v['spiega']}")
        print(f"\n== ⭐⛔ THE LINES OF 12 AUG, AND THE TWO TESTS OF EACH")
        coperte, mancanti = regole_coperte()
        for sigla, (dove, viola, rispetta) in REGOLE_NUOVE.items():
            print(f"  {sigla}  {dove}")
            print(f"      VIOLATES it:  {viola}")
            print(f"      RESPECTS it:  {rispetta}")
        print(f"\n  ⛔ lines with BOTH tests: {len(coperte)} of "
              f"{len(REGOLE_NUOVE)} — {', '.join(coperte) or '—'}")
        for sigla, perche in mancanti:
            print(f"     {ROSSO}⛔ {sigla}: {perche}{GRIGIO}")
        print(f"\n== ⛔⛔ THE PROPOSALS STILL OPEN — `RCP.md` does not carry them")
        print(f"      ⚠ The pair has a different form: the test that "
              f"SHOWS it exits 0")
        print(f"        (the referee declares, it does not condemn) and the one that keeps "
              f"the cure")
        print(f"        TIGHT exits 1 — and it is the second one that counts")
        ap_coperte, ap_mancanti = proposte_coperte()
        for sigla, (dove, stretta, vede) in PROPOSTE_APERTE.items():
            print(f"  {sigla}  {dove}")
            print(f"      SHOWS it:       {vede}")
            print(f"      keeps it TIGHT: {stretta}")
        print(f"\n  ⛔ proposals with BOTH tests: {len(ap_coperte)} of "
              f"{len(PROPOSTE_APERTE)} — {', '.join(ap_coperte) or '—'}")
        for sigla, perche in ap_mancanti:
            print(f"     {ROSSO}⛔ {sigla}: {perche}{GRIGIO}")
        print(f"\n== ⛔⛔ AND WHAT CANNOT BE JUDGED FROM A RECORDING")
        print(f"      ⚠ It sits in a table of its own: a cure without a test put "
              f"together with those")
        print(f"        that have the test would inflate the count")
        for sigla, perche in FUORI_PORTATA.items():
            print(f"  {sigla}  {perche}")
        print(f"\n== ⭐ P7 — {P7[0]}")
        print(f"      «{P7[1]}»")
        return 0
    if a.fabbrica:
        print("== the test recordings, in the format of RCP.md §11.1\n")
        fabbrica(a.cartella)
        return 0
    if a.certifica:
        return certifica(a)
    if not a.registrazione:
        # ⛔ Without a file it does not run silently: it says there is nothing
        #    to judge, with the code that fact has.
        print("== ⛔ no recording to judge.")
        print("   The tests are built with --fabbrica, the round with "
              "--certifica.")
        return 3

    # ⛔ THE POSITIVE CONTROL, BEFORE the verdict and not after: it is checked that
    #    this tool can find an error that is surely there, and only
    #    afterwards is it pointed at the unknown (`LEZIONI.md` §1.2).
    print("== ⛔ the positive control, BEFORE pointing the referee "
          "at the unknown")
    guastati, _ = gira_prove(a.cartella)
    if guastati:
        print(f"\n    {ROSSO}⛔ the referee gets {guastati} known recordings "
              f"wrong: it is not the case to believe it on a new one{GRIGIO}")
        return 2
    print(f"\n    {VERDE}⭐ the referee agrees on all the known tests"
          f"{GRIGIO}\n")

    try:
        codice, conta = valida(a.registrazione, tela=(a.tela_larghezza,
                                                      a.tela_altezza),
                               codec=a.codec)
    except NonConforme as e:
        print(f"\n   {ROSSO}⛔ NOT CONFORMING — {e.regola}{GRIGIO}")
        print(f"      {e.dice}")
        print(f"      byte {e.ass} in the file · offset {e.rel} in the payload "
              f"of the block")
        scrivi_esito(a.uscita, {"tipo": "giudizio", "file": a.registrazione,
                                "uscita": 1, "regola": e.regola, "dice": e.dice,
                                "byte": e.ass})
        return 1
    except Malformata as e:
        print(f"\n   ⚠ MALFORMED RECORDING: {e}")
        print("      ⛔ It is not a judgement on the wire: it is a defect of the file.")
        scrivi_esito(a.uscita, {"tipo": "giudizio", "file": a.registrazione,
                                "uscita": 2, "dice": str(e)})
        return 2
    except NienteDaGiudicare as e:
        print(f"\n   ⛔ NOTHING TO JUDGE: {e}")
        print("      It is not «conforming»: it is the absence of the object of "
              "judgement.")
        print("      Look at the recorder — whoever had to write those "
              "bytes.")
        scrivi_esito(a.uscita, {"tipo": "giudizio", "file": a.registrazione,
                                "uscita": 3, "dice": str(e)})
        return 3
    except OSError as e:
        # ⛔ E8: «empty» and «forbidden» look the same.
        print(f"\n   ⚠ THE RECORDING CANNOT BE READ: {e}")
        print("      ⛔ It is not a judgement on the wire, and it is not «the file is "
              "broken»:")
        print("         it is that it could not be opened.  Look at permissions,")
        print("         path and volume — not at RCP.md.")
        return 2
    scrivi_esito(a.uscita, {"tipo": "giudizio", "file": a.registrazione,
                            "uscita": 0, **conta})
    return codice


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="F2.4 — the mechanical referee of the video channel")
    p.add_argument("registrazione", nargs="?")
    p.add_argument("--fabbrica", action="store_true",
                   help="builds the test recordings")
    p.add_argument("--certifica", action="store_true",
                   help="healthy -> G4 -> healed")
    p.add_argument("--elenco", action="store_true",
                   help="the predictions and proposal P7, without measuring")
    p.add_argument("--cartella", default=os.path.join(QUI, "02-filo-prove"),
                   help="where the test recordings are")
    p.add_argument("--tela-larghezza", type=int, default=1920)
    p.add_argument("--tela-altezza", type=int, default=1080)
    p.add_argument("--codec", type=int, default=1, help="1 = HEVC, 2 = AV1")
    p.add_argument("--uscita", default="", help="the round's log, in JSONL")
    a = p.parse_args()
    os.makedirs(a.cartella, exist_ok=True)
    sys.exit(principale(a))
