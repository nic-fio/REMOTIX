#!/usr/bin/env python3
"""02-wire-validator.py — ⛔ F2.4: the mechanical referee learns the VIDEO CHANNEL.

    python3 02-wire-validator.py registrazione.rcpreg
    python3 02-wire-validator.py --build       builds the test recordings
    python3 02-wire-validator.py --certify      healthy -> G4 -> healed
    python3 02-wire-validator.py --output 02-wire-outcomes.jsonl reg.rcpreg

    exit 0  the video channel is conforming — and it says ON HOW MANY frames
    exit 1  it is not conforming — and it says WHICH byte and WHICH rule
    exit 2  the RECORDING is broken, or cannot be read (it is not a judgement on the wire)
    exit 3  ⛔ there is NOTHING TO JUDGE: zero blocks on the video channel

===========================================================================
⛔ WHY IT EXISTS, AND IT IS NOT A DUPLICATE OF `01-b4-validator.py`

`PLAN.md` §0.4 lists **three** substitutes for the referee we lost with
`mstsc`, and the wire validator is the **mechanical** one: *«it sees the non-
conforming bytes, but only those»*.

⛔ **And today it does not see the video.**  `01-b4-validator.py`, line 521:

    if canale != 0x00:
        print(f"   block {nb}: channel {CHANNELS[canale]} from the {chi}, "
              f"{lung} bytes — not judged by this validator")
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
⛔ AND THIS FILE DOES NOT TOUCH `01-b4-validator.py`

The phase 2 mandate (§2): *«nobody writes outside their own files»*.  B4 belongs
to phase 1.  ⭐ Here the video channel is judged **next to** B4, with the same
format and the same exit codes, and the proposal to merge them is in the
report `fasi/rapporti/F2-4-filo.md`: it is a decision of the coordinator, not
of a sub-agent.

⚠ **And the judgement is not rewritten twice**: it imports `02-wire-frame.py`,
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
**L3**, *«the FIN bit of the STREAM frame carrying the `FAREWELL`: the
same payload bytes, one transport bit more»* — without saying that the
recording format could not write it.

⛔ **And the «completeness unknown» denominator did NOT disappear with the cure**, and it is
important that it did not: now it counts the streams whose last block
carries `fine = 0`, that is the streams that in the recording **never
closed** — a trace cut in the middle, or a server still in the middle of the
frame.  ⚠ «I did not look at it» and «I looked at it and it is fine» remain two
different facts (`LESSONS.md` §1.9); what changes is **whose fault it is**: before
it was the format's, now it is the recording's.

===========================================================================
⛔ THE SIX LINES OF 12 AUG, JUDGED HERE ON THE RECORDINGS

Four of the six are applied by the imported judge (`02-wire-frame.py`), and
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
        stream** is `PROTOCOL_ERROR`.

  **P1** no video stream **before `SESSION`**.  Here it is recognised
        by reading the control channel in file order and marking when
        `SESSION` passes (`0x0007`, from the server): a video stream whose **first
        block** appears before that point violates §2.5.
        ⚠ And if the control channel could not be read, P1 **is not
          judged and it is declared**: `01-b4-validator.py` is the referee of that
          channel, and guessing here would be form **E8**.

⭐⛔ **And P5 was CORRECTED in `RCP.md` on 12 Aug 2026**, a few hours after
    going in, because propagating it here showed that it killed a
    healthy session: it said *«the canvas granted in `SESSION`»*, and after a
    `CANVAS(FITTED, 1280, 720)` (§7.1) a client conforming to §6.2 closed
    in front of a server conforming to §7.1.  Now it says **«the canvas in force»**,
    and this file follows it: it scans the control channel for `CANVAS`s too,
    not only for `SESSION`.  ⛔ The two tests that keep it honest are
    `p5-misura-diversa` (different size **without** a `CANVAS` before: it closes) and
    `p5-misura-dopo-adatta-tela` (**the same bytes**, after a `CANVAS` that
    granted it: it is accepted).

===========================================================================
⭐⛔ AND ON THE EVENING OF 12 AUG TWO MORE WENT IN — **P8** (from D14) and
    **P9** (from D13)

*The P5 cure had made the canvas change midway through the session legal, and with it
two things no line covered.  The coordinator applied them the same
evening, and this referee enforces them from the start.*

  **P8** §6.2 at the end + §3 exception **6** — after a `CANVAS(FITTED)` the
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
     stream whose first block appears **after** the `CANVAS(FITTED)` is
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
     the line killed a healthy session one step further on: `FIT_CANVAS` is
     sent by the user dragging a window, and dragging sends more
     than one per second — `CANVAS(1600,900)` and then `CANVAS(1280,720)` — and the
     frame opened before everything (a **keyframe**, which §5.2 forbids
     abandoning) carried the canvas of two rounds ago.  ⇒ The two tests:
     `p11-due-tele-nella-finestra` (exits **0**, tolerance declared) and
     `p11-misura-mai-in-vigore` (**1**, and it must exit 1 — without it, the window gets
     written broad and switches off P5 right where the server errs the most).

  ⭐ **P10 — §5.2 now says WHEN the client reconfigures** (*«on the first
     KEYFRAME at the new size, not on the `CANVAS`»*), and the client's line exempts
     *«nor the one tolerated by §6.2»*: the two cures no longer command the
     opposite on the same frame.  ⛔ But from here **it is not judged**: which
     size the decoder is configured at **is not on the wire**, and a
     recording carries the wire.  ⇒ The item sits in the
     `OUT_OF_REACH` table, and the two cases live in `02-wire-frame.py`, where the
     client's state is declared.

  ⛔ **And the tests that keep the cures TIGHT are worth as much as those that
     show them**: `p8-misura-di-nessuna-tela` exits **1** and must exit 1 —
     a grace written «after a `CANVAS` the size is not checked» would pass
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

HERE = os.path.dirname(os.path.abspath(__file__))

# ⛔ The judge is IMPORTED, not copied.  See the header.
_spec = importlib.util.spec_from_file_location(
    "f24", os.path.join(HERE, "02-wire-frame.py"))
f24 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(f24)

# ⛔ THE MAGIC, AND THE ONE THAT IS NO LONGER READ — §11.1, 12 Aug 2026.
#
#    ⛔ `OLD_MAGIC` is not a leftover: it is the only way of giving the old
#       file the sentence it deserves.  Without it, a `.rcpreg` of 10 Aug
#       would fall into the «does not start with the magic» branch, which sends you looking for a
#       corrupt file — and the file is not corrupt, it is of **another version**.
#       They are two different cures: regenerate it, or go and see who broke it.
MAGIC = b"RCPREG\x00\x03"
MAGIC_V1 = b"RCPREG\x00\x01"
MAGIC_V2 = b"RCPREG\x00\x02"
OLD_MAGIC = MAGIC_V1     # ⚠ the old name stays: the tests below use it
FILL = 0x2A          # §11.1
CLIENT, SERVER = 1, 2
CHANNELS = {0x00: "check", 0x01: "input", 0x02: "clipboard",
          0x03: "video", 0x04: "audio"}
VIDEO = 0x03
CONTROL = 0x00

# ⛔ `fine` — «how the stream closed AFTER this block» (§11.1).
CONTINUE, FIN, RESET = 0, 1, 2
FINE = {CONTINUE: "ongoing", FIN: "FIN", RESET: "RESET_STREAM"}

# The block of §11.1: direction, channel, end, instant_ms, stream, length,
# masked_count.
# ⛔ Twenty-one bytes.  Sixteen were those of 10 Aug; `fine` brought them to
#    seventeen (magic `0x00 0x02`); ⭐ `instant_ms` brings them to twenty-one on **21
#    Aug 2026** (magic `0x00 0x03`), and the header gains `orologio`.
# ⛔ Every time the magic changes because the SIZE changes: a reader that did not
#    know would read every block shifted, and give a judgement on bytes that
#    nobody wrote.
BLOCK = "!BBBIQIH"
BLOCK_BYTES = struct.calcsize(BLOCK)

SESSION = 0x0007           # §7.1, from the server
CANVAS = 0x000E               # §7.1, from the server — the outcome of `FIT_CANVAS`
FITTED = 1                # §7.1, `TELA.outcome`

GREEN, RED, YELLOW, GRAY = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


class NotCompliant(Exception):
    def __init__(self, rule, says, ass, rel):
        super().__init__(says)
        self.rule, self.says, self.ass, self.rel = rule, says, ass, rel


class Malformed(Exception):
    """The RECORDING is broken: it is not a judgement on the wire."""


class NothingToJudge(Exception):
    """⛔ There is no video block in the file.  It is not «conforming»."""


# ---------------------------------------------------------------------------
def read_blocks(d):
    """The blocks of §11.1, with the checks the format imposes.

    ⛔ The FORMAT checks sit here and raise `Malformed`, not
       `NotCompliant`: *«a malformed recording and a non-conforming wire
       are two different things, and must be said with two different sentences»* (§11.1).
    """
    # ⛔ THE OLD FORMAT IS REFUSED, AND WITH ITS OWN SENTENCE — §11.1.
    #
    #    *«an old validator must REFUSE the new format, not read it
    #    askew»*, and it holds both ways.  The old block was 16 bytes
    #    and the new one is 17: reading a `0x00 0x01` file with this reader,
    #    the `channel` would fall into the first byte of the `stream` and every block
    #    would shift by one.  ⛔ A JUDGEMENT would come out — a red on a byte
    #    nobody wrote, or a worse green — instead of «this file is
    #    of another version».
    if len(d) >= 8 and d[:8] == MAGIC_V1:
        raise Malformed(
            "it is a recording in the OLD format, «RCPREG 0x00 0x01»: the "
            "block carries neither `fine` nor `instant_ms`, and measures 16 bytes "
            "instead of 21.  ⛔ It is not read askew — §11.1, 12 Aug "
            "2026 — and it is not a broken file: REGENERATE it with today's "
            "recorder")
    if len(d) >= 8 and d[:8] == MAGIC_V2:
        raise Malformed(
            "it is a recording in the format of 12 Aug, «RCPREG 0x00 "
            "0x02»: the block does not carry `instant_ms` and measures 17 bytes instead "
            "of 21, and the header does not declare WHOSE the clock is.  ⛔ "
            "Read askew, every block would shift by four bytes.  "
            "REGENERATE it with `02-wire-client.py`")
    if len(d) < 16 or d[:8] != MAGIC:
        raise Malformed("it does not start with the magic of RCP.md §11.1")
    amount, orologio, r1, r2, r3 = struct.unpack("!IBBBB", d[8:16])
    if (r1, r2, r3) != (0, 0, 0):
        raise Malformed(
            f"the three reserved bytes are {r1},{r2},{r3}: §11.1 wants them 0")
    # ⛔ «Whose clock it is» is not guessed — §11.1.  ⚠ This referee does not
    #    judge any rule with time inside (that is
    #    `01-b4-validator.py`), ⛔ but the field is CHECKED anyway: a file
    #    that does not declare it is malformed for anyone, and letting it pass
    #    here would mean that the project's two referees give two different
    #    verdicts on the same file — which is the thing §0 forbids.
    if orologio not in (1, 2):
        raise Malformed(
            f"the `orologio` field is {orologio}: §11.1 defines two — "
            f"1 = the times are the client's, 2 = the server's")
    p, report = 16, []
    last_instant = 0
    for nb in range(amount):
        if p + BLOCK_BYTES > len(d):
            raise Malformed(f"block {nb} starts beyond the end of the file")
        which_way, channel, end, instant, stream, lung, nosc = struct.unpack(
            BLOCK, d[p:p + BLOCK_BYTES])
        p += BLOCK_BYTES
        # ⛔ The clock does not go backwards: §11.1 wants the milliseconds since the FIRST
        #    block, and the blocks are in wire order.
        if instant < last_instant:
            raise Malformed(
                f"block {nb}: `instant_ms` = {instant}, and the block before "
                f"said {last_instant}: §11.1 wants a MONOTONIC clock")
        last_instant = instant
        if end not in FINE:
            raise Malformed(
                f"block {nb}: `end` is {end}, and §11.1 defines three — "
                f"0 continues, 1 FIN, 2 RESET_STREAM")
        obscured = []
        for _ in range(nosc):
            if p + 40 > len(d):
                raise Malformed(f"block {nb}: masked interval truncated")
            ini, here = struct.unpack("!II", d[p:p + 8])
            p += 40
            if ini + here > lung:
                raise Malformed(
                    f"block {nb}: masked interval [{ini},{ini + here}) "
                    f"outside the payload of {lung} bytes")
            for o, q in obscured:
                if not (ini + here <= o or ini >= o + q):
                    raise Malformed(
                        f"block {nb}: two masked intervals overlap")
            obscured.append((ini, here))
        if p + lung > len(d):
            raise Malformed(f"block {nb}: the payload is truncated")
        if which_way not in (CLIENT, SERVER):
            raise Malformed(f"block {nb}: direction {which_way}, expected 1 or 2")
        for o, q in obscured:
            if any(b != FILL for b in d[p + o:p + o + q]):
                raise Malformed(
                    f"block {nb}: a masked interval is not made of 0x2A")
        report.append({"n": nb, "which_way": which_way, "channel": channel, "end": end,
                      "stream": stream, "base": p, "lung": lung,
                      "load": d[p:p + lung], "obscured": obscured})
        p += lung
    if p != len(d):
        raise Malformed(
            f"{len(d) - p} bytes remain after the {amount} declared blocks: either "
            f"`block_count` is under-declared — and then there is wire that "
            f"nobody judged — or there is a tail that is not part of the format")
    return report


# ---------------------------------------------------------------------------
class ControlUnreadable(Exception):
    """⛔ The control channel cannot be scanned: P1 is not judged, it is DECLARED.

    ⚠ It is not `NotCompliant`: the referee of that channel is
       `01-b4-validator.py`, and giving a protocol red from here would
       mean accusing a defect another tool can name better.
       ⛔ And it is not silence either: the stream ends up in the
       «order unknown» denominator, which is printed.
    """


def check_types(load):
    """The `kind`s of the §6.1 messages inside a control channel block.

    ⛔ It serves **two things only**: knowing when `SESSION` passed (half of
       P1, §2.5) and when a `CANVAS` changed the **canvas in force** (half of
       P5, §6.2 corrected on 12 Aug 2026).  It judges nothing — the judgement
       of that channel belongs to `01-b4-validator.py` — and that is why it stops at the
       first thing that does not add up instead of raising a red.

    ⛔ Returns `(kind, corpo)`, not the type alone: of `CANVAS` the body is needed,
       and going back to read it a second time would mean scanning the same
       framing twice with two different readers.
    """
    types, i = [], 0
    while i < len(load):
        if i + 6 > len(load):
            raise ControlUnreadable(
                f"{len(load) - i} bytes remain, and the framing of §6.1 "
                f"wants 6")
        kind, lung = struct.unpack("!HI", load[i:i + 6])
        if i + 6 + lung > len(load):
            raise ControlUnreadable(
                f"the message {kind:#06x} declares {lung} bytes of body and there "
                f"are {len(load) - i - 6}")
        types.append((kind, load[i + 6:i + 6 + lung]))
        i += 6 + lung
    return types


def valid(fpath, faults=(), canvas=(1920, 1080), codec=1, show=True):
    with open(fpath, "rb") as f:
        d = f.read()
    blocks = read_blocks(d)

    if show:
        print(f"== the VIDEO channel referee — {fpath}")
        print(f"   blocks: {len(blocks)}   bytes: {len(d)}")
        print(f"   ⛔ declared context: canvas {canvas[0]}x{canvas[1]}, codec "
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
    count = {"blocks": len(blocks), "video": 0, "streams": 0,
             "judged": 0, "unknown_completeness": 0, "unknown_order": 0,
             "tolerated_count": 0, "undecided": 0}
    ctx = f24.Context(canvas=canvas, negotiated_codec=codec, session_open=True)

    # The video blocks are grouped by `stream`: one stream, one frame
    # (§6.2).  ⛔ And the order inside a stream is the file's, not that
    # of the `stream`: streams are independent and blocks interleave.
    #
    # ⛔⭐ AND WHILE SCANNING TWO THINGS ARE KEPT THAT A JUDGE OF THE SINGLE
    #     FRAME CANNOT HAVE — they are the two rules of 12 Aug that
    #     talk about **streams** instead of bytes:
    #
    #       `on_check`      P3 — which streams the control
    #                           channel lives on (§4.2: the first bidirectional).  A
    #                           video block on one of those is a `0x03` on the
    #                           control channel;
    #       `before_session` P1 — which video streams start **before**
    #                           `SESSION` has passed.
    streams, order, canvases = {}, [], {}
    on_check, before_session = set(), set()
    check_stream = {b["stream"] for b in blocks if b["channel"] == CONTROL}
    session_seen, readable_check, why_unreadable = False, True, ""
    # ⛔⭐ THE CANVAS **IN FORCE**, AND IT CHANGES MIDWAY THROUGH THE SESSION — §6.2, corrected on
    #     12 Aug 2026.  It starts from the one declared from outside (which is the
    #     canvas of `SESSION`) and a `CANVAS(FITTED, …)` moves it.
    #     ⚠ The value is kept **at the moment each stream opens**, not
    #       the end-of-file one: judging a frame with a canvas granted
    #       after it would be reading the wire backwards.
    #     ⛔⛔ AND THE **PREVIOUS** ONE IS KEPT TOO — defect D14: the frames
    #        already in flight when the `CANVAS` passed carry it legitimately,
    #        and without having it at hand the referee cannot tell «an old
    #        size that is still arriving» from «a size that has never
    #        belonged to any canvas».  ⚠ `None` = nothing has ever changed.
    #     ⛔⛔ AND THE PREVIOUS ONES ARE A **LIST**, not a single one: §6.2 names «the
    #        previous canvas» in the singular, ⚠ but `FIT_CANVAS` is sent by the user
    #        dragging a window, and in one second they send several.  The
    #        list serves to **show** that hole (test
    #        `p8-due-tele-in-un-secondo`), not to plug it: the stream there comes out
    #        `AMBIGUOUS` with proposal P11, not ACCEPTED.
    canvas_now, canvas_from_canvas, prev_canvases = tuple(canvas), False, []
    for b in blocks:
        if b["channel"] not in CHANNELS:
            raise NotCompliant("RCP.md §2.5",
                              f"block {b['n']}: the high byte is "
                              f"{b['channel']:#04x}, outside the five channels",
                              b["base"], 0)
        if b["channel"] == CONTROL:
            # ⛔ It is read ONLY to know when `SESSION` passes (P1).  A
            #    masked interval does not get in the way: §11.1 uses it for the
            #    password (§4.4), which sits in the **body** of `CREDENTIALS`, and here
            #    the six bytes of the framing are looked at.
            try:
                for kind, body in check_types(b["load"]):
                    if b["which_way"] != SERVER:
                        continue        # §7.1: both arrive from the server
                    if kind == SESSION:
                        session_seen = True
                    elif kind == CANVAS and len(body) >= 10:
                        # ⛔ §7.1: `canvas_width`/`canvas_height` are «the canvas
                        #    in force AFTER this message» — and they are so even
                        #    when the outcome is REFUSED, where they report the
                        #    previous one.  ⇒ the field is taken, not deduced
                        #    from the outcome: it is the field that is defined that way.
                        new_one = struct.unpack("!II", body[2:10])
                        # ⛔ The previous one is kept only if the canvas **really**
                        #    changes: a `CANVAS` reporting the same size —
                        #    which is what a `REFUSED` does — leaves
                        #    nothing in flight, and recording it as a change
                        #    would open a grace that serves nobody.
                        if new_one != canvas_now:
                            prev_canvases = [canvas_now] + prev_canvases
                        canvas_now = new_one
                        canvas_from_canvas = body[0] == FITTED
            except ControlUnreadable as e:
                readable_check, why_unreadable = False, str(e)
            continue
        if b["channel"] != VIDEO:
            continue
        count["video"] += 1
        # ⛔ G4 — THE FAULT THAT IS TODAY'S STATE OF `01-b4-validator.py`.
        #
        #    Its line 521 declares it does not judge channels other than
        #    `0x00` and moves on.  Injected here, the video channel goes back to being
        #    looked at by nobody, and the file exits **3** — «nothing to
        #    judge» — which is exactly the honest verdict of a
        #    blind tool.  ⭐ If it exited **0** this fault would be
        #    invisible, and it is the reason code 3 exists.
        if "G4" in faults:
            continue
        # ⛔ THE DIRECTION — §2.5: «a channel used in the wrong direction».  Video
        #    goes from the server to the client, and that is all.
        if b["which_way"] != SERVER:
            raise NotCompliant("RCP.md §2.5",
                              f"block {b['n']}: a frame FROM THE CLIENT — "
                              f"video goes from the server to the client",
                              b["base"], 0)
        if b["obscured"]:
            # ⛔ §11.1: «the validator MUST NOT read inside a masked
            #    interval».  On a frame there are no secrets to hide
            #    — §4.4 talks about the password — so a masking here
            #    is a defect of the RECORDER, and it is said as such.
            raise Malformed(
                f"block {b['n']}: a masked interval on a VIDEO block. "
                f"§11.1 exists for the password (§4.4); a frame has "
                f"nothing to mask, and the validator cannot judge "
                f"what it is not allowed to read")
        if b["stream"] not in streams:
            streams[b["stream"]] = []
            order.append(b["stream"])
            # ⛔ The two stream rules are decided on the FIRST block of the
            #    stream, not on the last: it is the moment the stream
            #    opens, and it is the one §2.5 constrains.
            if b["stream"] in check_stream:
                on_check.add(b["stream"])
            if not session_seen:
                before_session.add(b["stream"])
            canvases[b["stream"]] = (canvas_now, canvas_from_canvas, list(prev_canvases))
        streams[b["stream"]].append(b)

    if not streams:
        raise NothingToJudge(
            f"{count['blocks']} blocks, {count['video']} on the video channel, "
            f"ZERO streams to judge")

    count["streams"] = len(streams)
    for sid in order:
        pieces = streams[sid]
        b0 = pieces[0]

        # ── P3 — §2.5: «a `0x03` on the control channel is PROTOCOL_ERROR»
        if sid in on_check:
            raise NotCompliant(
                "RCP.md §2.5",
                f"stream {sid}: a frame on the CONTROL CHANNEL — the "
                f"same stream the `0x00` blocks travel on.  §2.5 wants "
                f"video «only on a unidirectional stream opened by the "
                f"server»",
                b0["base"], 0)

        # ── P1 — §2.5: «none before sending `SESSION`»
        if not readable_check:
            # ⛔ E8 the other way round: it does not conclude «so it was after».  It counts.
            count["unknown_order"] += 1
        elif sid in before_session:
            raise NotCompliant(
                "RCP.md §2.5",
                f"stream {sid}: a video stream opens BEFORE `SESSION` "
                f"has passed on the control channel — the client receives a "
                f"frame of which it knows neither the size nor the codec.  "
                f"It is invariant I3 on the wire",
                b0["base"], 0)

        # ── P5 — §6.2: the size MUST be that of the **canvas in force**, which is
        #    the one of `SESSION` or the last one granted by a `CANVAS` (§7.1).
        #    ⛔ The context is set back to the canvas that was in force WHEN
        #       this stream opened: it is the judge that applies the
        #       rule, but only the referee knows what had passed before.
        canvas_fl, from_canvas, prev_fl = canvases.get(sid, (tuple(canvas), False, []))
        if from_canvas:
            # ⛔⛔ And the **draining queue** of D14 opens, with the previous
            #    canvases at hand.  ⭐ Since the **P13** cure the queue no longer ends
            #    by the clock but at the **first keyframe at the new size** —
            #    ⛔ and this changes the job of this file: the end of the
            #    tolerance has become **a fact that sits in the
            #    recording**.  Before it was one second, that is the only thing
            #    §11.1 does not carry, and the referee had to declare it could not
            #    judge it.
            ctx.fit_canvas(*canvas_fl,
                            previous=prev_fl[0] if prev_fl else None)
            # ⛔ And the previous ones are set **all**, not only the last: the
            #    judge reads the P11 window from them, and without them a
            #    session with two `CANVAS`s in a row would exit **1** — that is
            #    the referee would certify a healthy session killed.
            #    ⛔⭐ But **only while the queue is open**: if the keyframe at the
            #       new size has already passed in an earlier stream, putting
            #       the old canvases back here **would reopen** a tolerance §6.2
            #       has just closed — and the test `p13-vecchia-dopo-la-chiave-
            #       new_one` would exit 0 instead of 1.
            if not ctx.key_on_new_canvas:
                ctx.recent_canvases = list(prev_fl)
        else:
            ctx.canvas_width, ctx.canvas_height = canvas_fl
            # ⛔ And the context is RESET between one stream and the next: it is the same
            #    object for the whole recording, and a queue left open
            #    by an earlier stream would acquit the next stream.
            ctx.previous_canvas = None
            ctx.key_on_new_canvas = True
            ctx.recent_canvases = []

        # ── and the other four are applied by the judge, one byte at a time
        g = f24.Judge(ctx, where="uni", faults=faults)
        closing = pieces[-1]["end"]
        for b in pieces[:-1]:
            if b["end"] != CONTINUE:
                raise Malformed(
                    f"block {b['n']}: declares `end = {b['end']}` "
                    f"({FINE[b['end']]}) but on stream {sid} more blocks "
                    f"arrive after.  ⛔ It is a defect of the RECORDER: a "
                    f"stream closes only once")

        # ⛔⭐ AND THE RESET WINS OVER THE HEADER — §6.2, finding R1.7.
        #
        #    *«a reset stream carries an INCOMPLETE frame: the client
        #    MUST throw away what it received»*, and the bytes of a truncated
        #    header **can be anything**.  ⛔ Reading it first
        #    would give `PROTOCOL_ERROR` — that is it would drop the session —
        #    on a frame the server abandoned **on purpose**,
        #    which is the normal case of §5.1.
        #    ⚠ Fault **G3** lives right here, and to stay visible it must
        #      go through this branch: with `reset_come_fin` injected the reset
        #      stream is read as one closed with FIN, and that is what we
        #      want to see.
        if closing == RESET and not g.reset_come_fin:
            v = g.ends("reset")
        else:
            for b in pieces:
                g.arrive(b["load"])
                if g.verdict is not None:
                    break
            if g.verdict is not None:
                v = g.verdict
            elif closing == CONTINUE:
                # ⛔ IT IS NO LONGER A HOLE IN THE FORMAT — it is a hole in the
                #    RECORDING.  Since 12 Aug 2026 §11.1 carries `fine`, and
                #    `fine = 0` on the last block of a stream means that
                #    the stream, **in this file**, never closed: the
                #    trace is cut in the middle, or the server was still in the
                #    middle of the frame.  ⚠ It is declared, not guessed: the
                #    completeness is precisely what §6.2 ties to the FIN.
                count["unknown_completeness"] += 1
                count["judged"] += 1
                if show:
                    print(f"   {YELLOW}?? stream {sid}: {g.byte_data} bytes of "
                          f"data and `fine = 0` on the last block — ⛔ the stream "
                          f"does not close inside this recording, so "
                          f"completeness is NOT judged (§6.2){GRAY}")
                continue
            else:
                v = g.ends("fin" if closing == FIN else "reset")
        count["judged"] += 1
        if v.outcome in (f24.PROTOCOL_ERROR,):
            b0 = pieces[0]
            rel = v.deviation if v.deviation is not None else 0
            raise NotCompliant(v.rule, f"stream {sid}: {v.says}",
                              b0["base"] + rel, rel)
        # ⭐⛔ D14 — the stream carries the **previous** canvas right after a
        #    `CANVAS(FITTED)`, and since the evening of 12 Aug 2026 §6.2 says it is
        #    ACCEPTED: it is the sixth exception of §3.  ⛔ But the grace
        #    **second** cannot be judged from a `.rcpreg` — §11.1 carries no instants —
        #    so the referee **counts** the streams acquitted by the exception instead
        #    of letting them be mixed up with those that were in order.  ⚠ It is the
        #    same line of §3: *«every tolerance must be written in the log»*.
        if v.tolerated:
            count["tolerated_count"] += 1
        # ⛔⛔ AND THE TWO POINTS WHERE TONIGHT'S CURES DO NOT HOLD — P10 and P11.
        #    The referee neither condemns nor acquits: it declares.
        if v.outcome == f24.AMBIGUOUS:
            count["undecided"] += 1
        if show:
            clr = {f24.ACCEPTED: GREEN, f24.DISCARDED: YELLOW,
                   f24.AMBIGUOUS: YELLOW}[v.outcome]
            extra = (f"   ⇒ proposal {v.proposes}" if v.outcome == f24.AMBIGUOUS
                     else "")
            print(f"   {clr}{v.outcome:18s}{GRAY} stream {sid}: {v.says}{extra}")

    if show:
        print(f"\n   watched: {count['blocks']} blocks, of which "
              f"{count['video']} on the video channel · {count['streams']} streams · "
              f"{count['judged']} judged")
        if count["unknown_completeness"]:
            print(f"   {YELLOW}⛔ and for {count['unknown_completeness']} out of "
                  f"{count['streams']} the completeness could NOT be "
                  f"judged{GRAY}")
            print(f"      `fine = 0` on the last block: the stream does not "
                  f"close inside this")
            print(f"      file.  ⛔ It is NOT a defect of the wire, it is a "
                  f"defect of the")
            print(f"      RECORDING — since 12 Aug 2026 the format can ask "
                  f"the question")
        if count["tolerated_count"]:
            print(f"   {YELLOW}⭐⛔ and {count['tolerated_count']} streams out of "
                  f"{count['streams']} passed through the **SIXTH EXCEPTION** "
                  f"of §3{GRAY}")
            print(f"      they carry a size in force **since the queue started "
                  f"to")
            print(f"      drain**: they were already in flight when the "
                  f"`CANVAS(FITTED)` passed,")
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
        if count["undecided"]:
            # ⛔ The counter stays at zero since P10 and P11 went into the
            #    document, and it stays **in the code**: the day `RCP.md`
            #    goes back to allowing two readings — it allowed twelve in
            #    phase 1 alone — this referee declares them instead of choosing
            #    one of the two silently.
            print(f"   {YELLOW}⛔⛔ and on {count['undecided']} streams `RCP.md` "
                  f"DOES NOT DECIDE{GRAY}")
            print(f"      ⚠ The referee neither condemns nor acquits: it declares, "
                  f"as it did for")
            print(f"        the eight double readings of 12 Aug 2026 before "
                  f"they became lines")
        if count["unknown_order"]:
            print(f"   {YELLOW}⛔ and for {count['unknown_order']} streams out of "
                  f"{count['streams']} it could NOT be judged whether they came "
                  f"before `SESSION`{GRAY}")
            print(f"      the control channel cannot be scanned: "
                  f"{why_unreadable}")
            print(f"      ⚠ and the one judging THAT channel is "
                  f"`01-b4-validator.py`, not this one")
        print(f"   ⭐ conforming: no violation in {count['judged']} "
              f"streams")
    return 0, count


# ===========================================================================
# ⛔ THE TEST RECORDINGS — and they needs to certify the referee, not the wire.
#
#    §11: *«before concluding that the validator finds no errors, it is given
#    a recording WITH AN ERROR INSIDE and it is checked that it sees it.  A
#    tool that has never found anything is not a clean tool: it is
#    an uncertified tool»*.
def write_log(fpath, blocks, magic=MAGIC, orologio=1):
    """⛔ `magic` is a parameter for ONE reason only: the test that must be
       refused.  A format that can write only its own version cannot
       certify that it can refuse the others."""
    # ⛔ `orologio = 1`: these tests are written from the client side, like the
    #    real traces of `02-wire-client.py`.  ⚠ Declaring another one would make
    #    the tests different from the traces the referee really judges.
    if magic == MAGIC_V1 or magic == MAGIC_V2:
        out = bytearray(magic + struct.pack("!II", len(blocks), 0))
    else:
        out = bytearray(magic + struct.pack("!IBBBB", len(blocks), orologio,
                                            0, 0, 0))
    for i, (which_way, channel, fine, stream, load) in enumerate(blocks):
        if magic == MAGIC_V1:
            # the block of 10 Aug: 16 bytes, without `fine` and without instant
            out += struct.pack("!BBQIH", which_way, channel, stream, len(load), 0)
        elif magic == MAGIC_V2:
            # the block of 12 Aug: 17 bytes, with `fine` and without instant
            out += struct.pack("!BBBQIH", which_way, channel, fine, stream,
                               len(load), 0)
        else:
            # ⚠ The instant of a BUILT test is zero for all blocks, and it
            #   must be said: no time is measured here — the shape of the
            #   file is tested.  Zero is monotonic, so legal, and does not trigger
            #   any rule with time inside.
            out += struct.pack(BLOCK, which_way, channel, fine, 0, stream,
                               len(load), 0)
        out += load
    with open(fpath, "wb") as f:
        f.write(bytes(out))
    return fpath


def msg(kind, body=b""):
    """A control message in the framing of §6.1."""
    return struct.pack("!HI", kind, len(body)) + body


def opens_session(stream=0):
    """⛔ The block that makes LEGAL all the video that follows — P1.

    ⚠ The body of `SESSION` is empty, and it must be said: this referee reads of the
      control channel **only** the framing of §6.1, to know
      when that message passed.  Judging its body is
      `01-b4-validator.py`'s job, and rewriting its judgement here would be the double
      reading `RCP.md` §0 exists to prevent.
    """
    return (SERVER, CONTROL, CONTINUE, stream, msg(SESSION))


def fit_canvas(lar, h, outcome=FITTED, stream=0):
    """⛔ `CANVAS` — §7.1: *«the canvas in force AFTER this message»*.

    It is the message that corrected `RCP.md`: without it P5 said «the canvas
    granted in `SESSION`», and a user dragging a window lost the
    session (§7.1, exception 4 of §3).
    """
    return (SERVER, CONTROL, CONTINUE, stream,
            msg(CANVAS, struct.pack("!BBII", outcome, 0, lar, h)))


def key(stream=8, queue=64, **fields):
    return [opens_session(),
            (SERVER, VIDEO, FIN, stream, f24.header(**fields) + b"\x00" * queue)]


# ⛔ Every test declares its own exit code BEFORE being run, and
#    `canvas` sits here and not in the defaults because P5 is tested **by changing it**.
PROVE = {
    "good": {
        "explain": "⭐ a conforming keyframe in three blocks on the same "
                  "stream, after `SESSION`: it is the case phase 2 exists "
                  "to produce, ⛔ and it is the case that RESPECTS all six "
                  "lines of 12 Aug in one go",
        "exit": 0,
        "blocks": lambda: [
            opens_session(),
            (SERVER, VIDEO, CONTINUE, 8, f24.header()),
            (SERVER, VIDEO, CONTINUE, 8, b"\x00" * 2048),
            (SERVER, VIDEO, FIN, 8, b"\x00" * 2048)],
    },
    "abandoned": {
        "explain": "⭐⛔ a stream RESET midway — §5.1, the server abandons "
                  "a frame **on purpose**.  ⛔ It exits **0**: the "
                  "frame is thrown away and **the session holds**.  ⚠ Without the "
                  "`fine` field this recording was indistinguishable from "
                  "one truncated by mistake, and it is the E8 form P7 was "
                  "written for",
        "exit": 0,
        "blocks": lambda: [
            opens_session(),
            (SERVER, VIDEO, CONTINUE, 8, f24.header()),
            (SERVER, VIDEO, RESET, 8, b"\x00" * 10240)],
    },
    "stream-not-closed": {
        "explain": "⛔ the last block of the stream carries `fine = 0`: the stream "
                  "does not close inside the file.  It exits **0** — there is "
                  "no violation — ⛔ but completeness is declared NOT "
                  "judged, which is a different fact from «judged and fine»",
        "exit": 0,
        "blocks": lambda: [
            opens_session(),
            (SERVER, VIDEO, CONTINUE, 8, f24.header() + b"\x00" * 64)],
    },
    "old-format": {
        "explain": "⛔⛔ a «RCPREG 0x00 0x01» recording, yesterday's "
                  "format.  §11.1: *«an old validator must REFUSE the "
                  "new format, not read it askew»* — and it holds both "
                  "ways.  ⛔ It exits **2**: it is a defect of the FILE, not of the wire, "
                  "and the cure is to regenerate it",
        "exit": 2,
        "magic": OLD_MAGIC,
        "blocks": lambda: key(),
    },
    "formato-del-12-agosto": {
        "explain": "⛔⛔ a «RCPREG 0x00 0x02» recording: the block carries "
                  "`fine` but NOT `instant_ms`, and measures 17 bytes instead of 21.  "
                  "⚠ Refusing `0x01` is not enough: that is another line, and "
                  "without this test it could be deleted and the bench "
                  "would stay green.  ⛔ It is exactly the form in which the "
                  "12 Aug defect lived for four days",
        "exit": 2,
        "magic": MAGIC_V2,
        "blocks": lambda: key(),
    },
    "orologio-non-dichiarato": {
        "explain": "⛔ `orologio` = 0 in the header: §11.1 defines two "
                  "(1 = the times are the client's, 2 = the server's).  ⚠ This "
                  "referee does not judge time, but a file that does not declare "
                  "WHOSE the clock is is malformed for anyone — and the two "
                  "referees of the project must not give two different verdicts "
                  "on the same file",
        "exit": 2,
        "orologio": 0,
        "blocks": lambda: key(),
    },
    "type-malformed": {
        "explain": "`tipo = 0x0300` in the header: §6.2 «Other values: "
                  "PROTOCOL_ERROR»",
        "exit": 1,
        "blocks": lambda: key(kind=0x0300),
    },
    "wrong-direction": {
        "explain": "a frame FROM THE CLIENT: §2.5, the channel in the wrong "
                  "direction",
        "exit": 1,
        "blocks": lambda: [opens_session(),
                            (CLIENT, VIDEO, FIN, 9,
                             f24.header() + b"\x00" * 64)],
    },
    # ── ⭐⛔ THE SIX LINES OF 12 AUG, ONE TEST EACH ───────────────────────
    "p1-before-session": {
        "explain": "⭐⛔ **P1 violated** — a video stream opens and in the file "
                  "`SESSION` has not passed yet.  ⛔ And the test that "
                  "RESPECTS it is `good_one`: the same bytes, with the "
                  "`SESSION` block in front",
        "exit": 1,
        "blocks": lambda: [(SERVER, VIDEO, FIN, 8,
                             f24.header() + b"\x00" * 64)],
    },
    "p2-number-zero": {
        "explain": "⭐⛔ **P2 violated** — `numero = 0`, which §6.2 reserves for "
                  "«no frame» since 12 Aug 2026",
        "exit": 1,
        "blocks": lambda: key(num=0),
    },
    "p3-video-on-control": {
        "explain": "⭐⛔ **P3 violated** — the 28-byte header written "
                  "on the **same stream** the control channel "
                  "travels on.  ⛔ It is the only place where the server can "
                  "get the stream wrong: §2.5 forbids it from opening bidirectional ones",
        "exit": 1,
        "blocks": lambda: [opens_session(),
                            (SERVER, VIDEO, FIN, 0,
                             f24.header() + b"\x00" * 64)],
    },
    "p4-fin-before-28": {
        "explain": "⭐⛔ **P4 violated** — the stream closes with **FIN** after "
                  "12 bytes: it is not a short frame, it is a length that "
                  "does not add up (§6.2, third line)",
        "exit": 1,
        "blocks": lambda: [opens_session(),
                            (SERVER, VIDEO, FIN, 8,
                             f24.header()[:12])],
    },
    "p5-size-differs": {
        "explain": "⭐⛔ **P5 violated** — a 1280x720 frame on a granted "
                  "1920x1080 canvas",
        "exit": 1,
        "blocks": lambda: key(lar=1280, h=720),
    },
    "p5-size-after-fit-canvas": {
        "explain": "⭐⛔ **P5 respected, and it is the test that corrected "
                  "`RCP.md`** — the **very same bytes** as "
                  "`p5-misura-diversa`, but between `SESSION` and the frame "
                  "a `CANVAS(FITTED, 1280, 720)` passes (§7.1).  ⛔ With the "
                  "first draft of P5 — «the canvas granted in `SESSION`» — "
                  "this recording exited **1**: the client killed the "
                  "session because the user had dragged a window.  "
                  "⚠ Without this test the new rule would be as strict as "
                  "the wrong one before, and no bench would say so",
        "exit": 0,
        "blocks": lambda: [
            opens_session(),
            fit_canvas(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.header(lar=1280, h=720) + b"\x00" * 64)],
    },
    "p5-size-equal-to-another-canvas": {
        "explain": "⭐ **P5 respected, and NOT with the default canvas** — the "
                  "**same bytes** as the test above, with the canvas granted "
                  "at 1280x720.  ⛔ Without this test, a referee that "
                  "compared with a 1920x1080 written by hand would be green "
                  "on all the others",
        "exit": 0,
        "canvas": (1280, 720),
        "blocks": lambda: key(lar=1280, h=720),
    },
    # ── ⛔⛔ D14 — THE FRAMES IN FLIGHT, and proposal **P8** ─────────────────
    "p8-in-flight-after-fit-canvas": {
        "explain": "⭐⛔ **P8 RESPECTED — AND IT IS THE RECORDING OF A "
                  "HEALTHY SESSION THAT UNTIL TONIGHT DROPPED** — `SESSION` at "
                  "1920x1080, then a `CANVAS(FITTED, 1280, 720)` (§7.1), and "
                  "**then** the video stream arrives still carrying 1920x1080: "
                  "it is the frame opened **before** the `FIT_CANVAS` "
                  "reached the server.  ⛔ Until tonight §6.2 to the letter "
                  "made it exit **1** — the session dropped without anybody "
                  "having made a mistake — and this test exited 0 with an `AMBIGUOUS`. "
                  "⭐ Now §6.2 carries a one-second grace (sixth "
                  "exception of §3): it exits **0** and the stream is ACCEPTED with the "
                  "**tolerance declared**.  ⚠ And the **second** cannot be "
                  "judged from here: §11.1 carries no instants, and the referee declares it "
                  "instead of guessing it",
        "exit": 0,
        "blocks": lambda: [
            opens_session(),
            fit_canvas(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.header(lar=1920, h=1080, num=41) + b"\x00" * 64)],
    },
    "p11-two-canvases-in-window": {
        "explain": "⭐⛔ **P11 respected — and it is the scene that killed a "
                  "healthy session ONE STEP FURTHER ON** — `SESSION` at "
                  "1920x1080, `CANVAS(FITTED, 1600, 900)`, `CANVAS(FITTED, "
                  "1280, 720)`, and then the video stream carrying 1920x1080: the "
                  "**keyframe** opened before everything, which §5.2 forbids the server "
                  "to abandon.  ⛔ With «the **previous** canvas» in the "
                  "singular it was neither the one in force nor the previous one, and "
                  "§6.2 said `PROTOCOL_ERROR` **at once**: the healthy session "
                  "dropped anyway.  ⭐ Now the grace covers «a canvas that "
                  "was in force within the second just passed»: it exits "
                  "**0**, with the tolerance declared.  ⚠ Whoever drags a "
                  "window sends more than one `FIT_CANVAS` per second: this "
                  "is not the rare scene, it is the normal one",
        "exit": 0,
        "blocks": lambda: [
            opens_session(),
            fit_canvas(1600, 900),
            fit_canvas(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.header(lar=1920, h=1080, num=41) + b"\x00" * 64)],
    },
    "p13-old-after-new-key": {
        "explain": "⭐⛔ **P13 violated — and this test could not be written "
                  "BEFORE** — `SESSION` at 1920x1080, `CANVAS(FITTED, 1280, "
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
        "exit": 1,
        "blocks": lambda: [
            opens_session(),
            fit_canvas(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.header(lar=1280, h=720, num=41) + b"\x00" * 64),
            # ⛔ `nr` 42, that is captured AFTER the keyframe at the new size:
            #    it is not a frame in flight, it is a server that went on
            #    capturing at the old canvas.  ⚠ With number **40** it would be the
            #    scene of finding **P14**, and it is not the same thing.
            (SERVER, VIDEO, FIN, 9,
             f24.header(lar=1920, h=1080, num=42) + b"\x00" * 64)],
    },
    "p14-in-flight-overtaken-by-key": {
        "explain": "⭐⛔⛔ **P14 — and until an hour ago this recording exited "
                  "1** — the keyframe at 1280x720 (`nr` 41) arrives **before** "
                  "the frame in flight at 1920x1080, which carries `nr` **40** "
                  "because it was captured before the `CANVAS`.  ⚠ It is the "
                  "normal scene: the old frame is the biggest (§5.2 "
                  "forbids abandoning a keyframe) and the streams are "
                  "independent, so the new keyframe **overtakes** it.  ⛔ The "
                  "tolerance ended on that keyframe, and the old size "
                  "made the session drop.  ⭐ Now §6.2 says that "
                  "**order is applied before size**: the stream is "
                  "DISCARDED — «and its size is not even looked at» — and the "
                  "recording exits **0**, because a discard is not a "
                  "violation of the wire (§5.1)",
        "exit": 0,
        "blocks": lambda: [
            opens_session(),
            fit_canvas(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.header(lar=1280, h=720, num=41) + b"\x00" * 64),
            (SERVER, VIDEO, FIN, 9,
             f24.header(lar=1920, h=1080, num=40) + b"\x00" * 64)],
    },
    "p11-size-never-in-effect": {
        "explain": "⭐⛔ **P11 violated, and it is the test that keeps the window "
                  "TIGHT** — **the same two-`CANVAS` recording**, but the "
                  "frame carries 800x600: ⛔ a size that in that "
                  "window was **never** in force — not 1920x1080, "
                  "not 1600x900, not 1280x720.  It exits **1**, and it must exit 1.  "
                  "⚠ Without this test, a window written «during the "
                  "second the size is not checked» would pass the test "
                  "above and switch off P5 right where the server is most "
                  "likely to err",
        "exit": 1,
        "blocks": lambda: [
            opens_session(),
            fit_canvas(1600, 900),
            fit_canvas(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.header(lar=800, h=600, num=41) + b"\x00" * 64)],
    },
    # ── ⭐⛔ D13 — THE KEYFRAME AT EVERY CANVAS CHANGE (§5.2), tonight's line ─
    "p9-delta-at-new-size": {
        "explain": "⭐⛔ **P9 violated** — after a `CANVAS(FITTED, 1280, 720)` the "
                  "first frame at the **new** size is a **delta**.  ⛔ "
                  "`[M]` 12 Aug 2026: with only deltas at the new size "
                  "Chrome on HEVC paints 5 frames at the OLD size "
                  "without raising any error — the symptom would be «the "
                  "desktop tears when I resize the window»",
        "exit": 1,
        "blocks": lambda: [
            opens_session(),
            (SERVER, VIDEO, FIN, 7, f24.header(num=1) + b"\x00" * 64),
            fit_canvas(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.header(kind=0x0302, lar=1280, h=720, num=2)
             + b"\x00" * 64)],
    },
    "p9-key-at-new-size": {
        "explain": "⭐ **P9 respected** — the **very same bytes**, with "
                  "`tipo = 0x0301`.  ⛔ Without this test a rule written "
                  "«after a `CANVAS` nothing is accepted» would stay green on "
                  "the one that violates it.  ⚠ And the referee judges **less** than "
                  "what §5.2 says: it sees that it is a keyframe, not that it is a "
                  "**real** keyframe — the parameter sets sit in the data, and the judge "
                  "does not keep the data",
        "exit": 0,
        "blocks": lambda: [
            opens_session(),
            (SERVER, VIDEO, FIN, 7, f24.header(num=1) + b"\x00" * 64),
            fit_canvas(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.header(kind=0x0301, lar=1280, h=720, num=2)
             + b"\x00" * 64)],
    },
    "p9-delta-after-new-key": {
        "explain": "⭐⛔ **P9, the second face: the debt is paid ONCE** "
                  "— keyframe at 1280x720 on stream 8, **then** a delta at "
                  "1280x720 on stream 9.  ⛔ Without this test, a referee "
                  "that had understood §5.2 as «after a `CANVAS` deltas are not "
                  "accepted» would stop the video **after every "
                  "resize**, and that is where phase 3 lives.  ⚠ And it also tests "
                  "something of this file: the context is set back "
                  "**stream by stream**, and a `CANVAS` repeating the "
                  "size in force must not reopen the debt",
        "exit": 0,
        "blocks": lambda: [
            opens_session(),
            (SERVER, VIDEO, FIN, 7, f24.header(num=1) + b"\x00" * 64),
            fit_canvas(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.header(kind=0x0301, lar=1280, h=720, num=2)
             + b"\x00" * 64),
            (SERVER, VIDEO, FIN, 9,
             f24.header(kind=0x0302, lar=1280, h=720, num=3)
             + b"\x00" * 64)],
    },
    "p8-size-of-no-canvas": {
        "explain": "⭐⛔ **P8 covers ONE size, not «everything after a `CANVAS`»** — "
                  "same recording, but the frame carries 800x600: ⛔ neither "
                  "the canvas in force (1280x720) nor the previous one (1920x1080). "
                  "It was not in flight, it is a wrong field — it exits **1**, and it must "
                  "exit 1.  ⚠ **It is the test that counts**: without it, a cure "
                  "written «after a `CANVAS` the size is not checked» "
                  "would pass the test above and switch off P5 right in the "
                  "window where the server is most likely to err — and "
                  "it is exactly how P5 ended up wrong the first "
                  "time",
        "exit": 1,
        "blocks": lambda: [
            opens_session(),
            fit_canvas(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.header(lar=800, h=600, num=41) + b"\x00" * 64)],
    },
    "p6-first-delta": {
        "explain": "⭐⛔ **P6 violated** — the first frame after `SESSION` is "
                  "a delta (`0x0302`).  ⚠ Until 11 Aug it conformed to "
                  "every line, and the symptom would have been «the desktop appears in "
                  "pieces»",
        "exit": 1,
        "blocks": lambda: key(kind=0x0302),
    },
    "p6-delta-after-key": {
        "explain": "⭐ **P6 respected from the hard side** — keyframe on "
                  "stream 8, **then** a delta on stream 9.  ⛔ Without this "
                  "test, a referee that had understood «deltas are not "
                  "accepted» would stay green on everything and stop the video "
                  "from phase 3 on",
        "exit": 0,
        "blocks": lambda: [
            opens_session(),
            (SERVER, VIDEO, FIN, 8, f24.header(num=1) + b"\x00" * 64),
            (SERVER, VIDEO, FIN, 9,
             f24.header(kind=0x0302, num=2) + b"\x00" * 64)],
    },
    # ── the three outcomes that are not a judgement on the wire ─────────────
    "control-only": {
        "explain": "⛔ a handshake-only recording: ZERO video "
                  "blocks.  «I have nothing to judge» and «I judged everything "
                  "and it is fine» are two different facts",
        "exit": 3,
        "blocks": lambda: [(CLIENT, CONTROL, CONTINUE, 0, msg(0x0001))],
    },
    "excess-tail": {
        "explain": "⛔ `block_count` under-declared: wire that nobody "
                  "judges.  It is a defect of the FILE, not of the wire",
        "exit": 2,
        "blocks": None,
    },
    "unknown-channel": {
        "explain": "a high byte that is none of the five of §2.5",
        "exit": 1,
        "blocks": lambda: [opens_session(),
                            (SERVER, 0x09, FIN, 8, b"\x00" * 28)],
    },
    "control-unreadable": {
        "explain": "⛔ the control channel cannot be scanned — a message that "
                  "declares more body than there is — and there is a conforming "
                  "video stream.  ⭐ It exits **0**, ⛔ but P1 is declared NOT "
                  "judged: «so it was after `SESSION`» would be form "
                  "**E8**.  ⚠ And the one judging that channel is "
                  "`01-b4-validator.py`, not this one",
        "exit": 0,
        "blocks": lambda: [
            (SERVER, CONTROL, CONTINUE, 0, struct.pack("!HI", SESSION, 99)),
            (SERVER, VIDEO, FIN, 8, f24.header() + b"\x00" * 64)],
    },
    "end-out-of-range": {
        "explain": "⛔ `fine = 7`, and §11.1 defines **three**.  ⚠ It tests that the "
                  "new field is read and not just skipped: without it, a "
                  "recorder that wrote garbage in that byte "
                  "would pass, and with it every completeness judgement",
        "exit": 2,
        "blocks": lambda: [(SERVER, VIDEO, 7, 8, f24.header())],
    },
}

# ⛔ WHICH TEST TRIGGERS WHICH LINE, AND WHICH ONE RESPECTS IT — and the count is
#    computed by `covered_rules()`, which **looks them up** in `PROVE`.
NEW_RULES = {
    "P1": ("RCP.md §2.5", "p1-before-session", "good"),
    "P2": ("RCP.md §6.2", "p2-number-zero", "good"),
    "P3": ("RCP.md §2.5", "p3-video-on-control", "good"),
    "P4": ("RCP.md §6.2", "p4-fin-before-28", "good"),
    "P5": ("RCP.md §6.2", "p5-size-differs", "p5-size-after-fit-canvas"),
    "P6": ("RCP.md §5.2", "p6-first-delta", "p6-delta-after-key"),
    "P7": ("RCP.md §11.1", "old-format", "abandoned"),
    # ── ⭐⛔ AND THE TWO OF THE **EVENING** OF 12 AUG — D14 and D13 ───────────
    #    ⚠ Until that evening P8 sat in `OPEN_PROPOSALS` and its test
    #      exited 0 **declaring**; now it exits 0 **accepting**, and it is a
    #      different fact that can be read in the printed line.
    "P8": ("RCP.md §6.2 in coda, §3 eccezione 6",
           "p8-size-of-no-canvas", "p8-in-flight-after-fit-canvas"),
    "P9": ("RCP.md §5.2, the canvas change",
           "p9-delta-at-new-size", "p9-key-at-new-size"),
    # ── ⭐⛔ AND THE TENTH, BORN FROM THE EIGHTH AND APPLIED IN THE NEXT ROUND ─
    "P11": ("RCP.md §6.2 — the window instead of «the previous one»",
            "p11-size-never-in-effect", "p11-two-canvases-in-window"),
    # ⭐⛔ And P13, which this referee **could not judge at all before**: the
    #    tolerance ended by the clock, and §11.1 carries no instants.  Now
    #    it ends at the first keyframe at the new size, which is a frame —
    #    and frames are in the recording.
    "P13": ("RCP.md §6.2 — the tolerance ends at the KEYFRAME, not by the clock",
            "p13-old-after-new-key", "p8-in-flight-after-fit-canvas"),
    # ⭐⛔ P14 — and the pair here has the same form as the others only by chance:
    #    the one that «respects» it exits **0** because the stream is DISCARDED, not
    #    because it is conforming.  ⚠ A discard and a good frame have the
    #    same exit code, and the printed line tells them apart: it is the same
    #    reason this referee counts streams instead of counting
    #    codes.
    "P14": ("RCP.md §6.2 — order is applied BEFORE size",
            "p13-old-after-new-key",
            "p14-in-flight-overtaken-by-key"),
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
#    somewhere to sit, and `covered_proposals()` keeps saying «0 of 0» — which is a
#    number, not a silence.
OPEN_PROPOSALS = {}

# ⛔⛔ AND WHAT CANNOT BE JUDGED FROM A RECORDING AT ALL — it is declared, not
#    faked.  ⚠ A proposal without a test put together with those that have the test
#    would inflate the count, and it is the same reason
#    `NEW_RULES` and `OPEN_PROPOSALS` sit in two tables.
OUT_OF_REACH = {
    "P10": ("§5.2 says **when** the client reconfigures the decoder — "
            "*«on the first KEYFRAME at the new size, not on the `CANVAS`»* — and it is "
            "the line that reconciled the two cures of 12 Aug, which "
            "on the same frame commanded the opposite.  ⛔ From a "
            "`.rcpreg` it is not judged: the recording carries the wire, and **which "
            "size the decoder is configured at is not on the wire**.  "
            "The two cases sit in `02-wire-frame.py` "
            "(`p10-decodificatore-al-tela` and `p10-decodificatore-alla-"
            "chiave`), where the client's state is **declared** — and there it does not "
            "change the outcome, it changes the **finding**"),
}


def covered_proposals():
    """⛔ Like `covered_rules()`, for the cures the document does not have yet."""
    covered, missing_list = [], []
    for tag, (_, tight, sees) in OPEN_PROPOSALS.items():
        holes = []
        if tight not in PROVE:
            holes.append(f"the test that keeps it TIGHT is missing («{tight}»)")
        elif PROVE[tight]["exit"] != 1:
            holes.append(f"«{tight}» does not require exit 1: a cure without "
                         f"this test gets written too broad")
        if sees not in PROVE:
            holes.append(f"the test that SHOWS it is missing («{sees}»)")
        elif PROVE[sees]["exit"] != 0:
            holes.append(f"«{sees}» does not require exit 0")
        (missing_list if holes else covered).append(
            (tag, "; ".join(holes)) if holes else tag)
    return covered, missing_list


def covered_rules():
    """⛔ How many lines REALLY have the test that violates them and the one that
       respects them, **looked up in `PROVE`** — never a number written by hand."""
    covered, missing_list = [], []
    for tag, (_, viola, respects) in NEW_RULES.items():
        holes = []
        if viola not in PROVE:
            holes.append(f"the test that VIOLATES it is missing («{viola}»)")
        elif PROVE[viola]["exit"] not in (1, 2):
            holes.append(f"«{viola}» does not require a refusal")
        if respects not in PROVE:
            holes.append(f"the test that RESPECTS it is missing («{respects}»)")
        elif PROVE[respects]["exit"] != 0:
            holes.append(f"«{respects}» does not require exit 0")
        (missing_list if holes else covered).append(
            (tag, "; ".join(holes)) if holes else tag)
    return covered, missing_list


def factory(folder):
    done_ones = []
    for name, v in PROVE.items():
        p = os.path.join(folder, f"02-filo-prova-{name}.rcpreg")
        magic = v.get("magic", MAGIC)
        if v["blocks"] is None:
            # the garbage tail is built by hand
            write_log(p, key())
            with open(p, "ab") as fh:
                fh.write(b"spazzatura")
        else:
            write_log(p, v["blocks"](), magic=magic,
                       orologio=v.get("orologio", 1))
        done_ones.append((name, p, v["exit"], v["explain"],
                      v.get("canvas", (1920, 1080))))
        print(f"   {os.path.basename(p):50s} expected exit {v['exit']}")
        print(f"   {'':50s} {v['explain']}")
    return done_ones


def run_tests(folder, faults=(), show=True):
    """⛔ Every test declares its own exit code BEFORE being run."""
    done_ones = factory(folder) if show else _quiet_factory(folder)
    faulted, lines = 0, []
    if show:
        print()
    for name, p, expected, explain, canvas in done_ones:
        try:
            seen, _ = valid(p, faults=faults, canvas=canvas, show=False)
        except NotCompliant:
            seen = 1
        except Malformed:
            seen = 2
        except NothingToJudge:
            seen = 3
        except OSError:
            seen = 2
        ok = seen == expected
        faulted += int(not ok)
        lines.append({"prova": name, "expected": expected, "seen": seen,
                      "outcome": bool(ok)})
        if show:
            print(f"    {GREEN if ok else RED}{'OK' if ok else 'NO'}{GRAY}  "
                  f"{name:36s} exit {seen} (expected {expected})")
            if not ok:
                print(f"        {explain}")
    return faulted, lines


def _quiet_factory(folder):
    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        return factory(folder)


P7 = (
    "§11.1, the recording block — how the stream ended",
    "⭐ APPLIED TO `RCP.md` ON 12 AUG 2026.  The block carries, after "
    "`channel`, a `u8 fine`: `0` = the stream continues, `1` = closed with "
    "**FIN**, `2` = reset with **RESET_STREAM**; and the magic moved to "
    "`\"RCPREG\" 0x00 0x02` because the block changes size — 17 bytes instead "
    "of 16 — and an old validator MUST refuse the new format instead of "
    "reading it askew.  Without that field an abandoned frame (§5.1, "
    "legal) and one truncated by mistake (§3, the connection drops) looked the "
    "same in the recording, that is the referee could not apply "
    "the line §6.2 added on purpose on 9 Aug 2026.")


def write_outcome(fpath, rec):
    if not fpath:
        print("    ⚠ no --output: this round leaves NO log")
        return False
    report = {"when": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "bench": "F2.4-validatore",
             "scene": "recordings built by this same file, in the "
                      "format of RCP.md §11.1: no network and no server",
             "machine": os.uname().nodename}
    report.update(rec)
    try:
        with open(fpath, "a") as f:
            f.write(json.dumps(report, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except OSError as e:
        print(f"    {RED}⛔ the log «{fpath}» cannot be written: {e}{GRAY}")
        return False
    return True


def certify(a):
    """⛔ healthy -> G4 -> healed.  And G4 IS TODAY'S STATE OF `01-b4`.

    The fault to inject is not invented: it is *«the validator skips the video
    channel»*, that is line 521 of `01-b4-validator.py`.  ⭐ Certifying against
    that fault is the only way of proving that this file **adds**
    something instead of repeating B4 in other words.
    """
    print("\n== ⛔ THE CERTIFICATION — healthy -> G4 -> healed")
    print("   G4: «the referee skips the video channel», which is what")
    print("       `01-b4-validator.py` does today (its line 521).")
    print("   expected healthy: 0 wrong tests")
    print("   expected fault:   the tests that must exit 1 exit 3 —")
    print("                     «nothing to judge» — because the video channel")
    print("                     is not looked at.  ⛔ And they do NOT exit 0: a")
    print("                     referee that skips everything does not acquit, it declares")
    print("                     it did not look.  If it exited 0 the fault")
    print("                     would have passed for a green\n")
    healthy, healthy_lines = run_tests(a.folder, faults=())
    print()
    broken, broken_lines = run_tests(a.folder, faults=("G4",))
    print()
    # ⛔ THE MARK, WITH ITS TWO HALVES (R12-A.3): the faulty round must say it
    #    and the healthy round must NOT already say it.
    mark_broken = sum(1 for r in broken_lines
                      if r["expected"] == 1 and r["seen"] == 3)
    mark_healthy = sum(1 for r in healthy_lines
                     if r["expected"] == 1 and r["seen"] == 3)
    healed, _ = run_tests(a.folder, faults=(), show=False)
    ok = (healthy == 0 and broken > 0 and mark_broken > 0 and mark_healthy == 0
          and healed == 0)
    print(f"    {GREEN if ok else RED}{'OK' if ok else 'NO'}{GRAY}  G4  "
          f"healthy {healthy} -> fault {broken} -> healed {healed}   "
          f"mark «exit 3 where 1 was needed»: {mark_broken} times with the "
          f"fault, {mark_healthy} times when healthy")
    write_outcome(a.output, {"type": "certification", "fault": "G4",
                            "healthy": healthy, "fault_count": broken,
                            "healed": healed, "mark_with_fault": mark_broken,
                            "mark_from_healthy": mark_healthy, "outcome": bool(ok),
                            "healthy_tests": healthy_lines, "broken_tests": broken_lines})
    print()
    if ok:
        print(f"    {GREEN}⭐ 02-wire-validator.py IS CERTIFIED{GRAY}")
        return 0
    print(f"    {RED}⛔ NOT certified{GRAY}")
    return 1


def main(a):
    if a.list:
        print("== the test recordings, and the expected exit code of "
              "each")
        print("   ⛔ Every line is a PREDICTION, written before the round\n")
        for name, v in PROVE.items():
            print(f"  {name:36s} exit {v['exit']}"
                  + (f"   canvas {v['canvas'][0]}x{v['canvas'][1]}"
                     if "canvas" in v else ""))
            print(f"  {'':36s}   {v['explain']}")
        print(f"\n== ⭐⛔ THE LINES OF 12 AUG, AND THE TWO TESTS OF EACH")
        covered, missing_list = covered_rules()
        for tag, (dove, viola, respects) in NEW_RULES.items():
            print(f"  {tag}  {dove}")
            print(f"      VIOLATES it:  {viola}")
            print(f"      RESPECTS it:  {respects}")
        print(f"\n  ⛔ lines with BOTH tests: {len(covered)} of "
              f"{len(NEW_RULES)} — {', '.join(covered) or '—'}")
        for tag, why in missing_list:
            print(f"     {RED}⛔ {tag}: {why}{GRAY}")
        print(f"\n== ⛔⛔ THE PROPOSALS STILL OPEN — `RCP.md` does not carry them")
        print(f"      ⚠ The pair has a different form: the test that "
              f"SHOWS it exits 0")
        print(f"        (the referee declares, it does not condemn) and the one that keeps "
              f"the cure")
        print(f"        TIGHT exits 1 — and it is the second one that counts")
        ap_covered, ap_missing = covered_proposals()
        for tag, (dove, tight, sees) in OPEN_PROPOSALS.items():
            print(f"  {tag}  {dove}")
            print(f"      SHOWS it:       {sees}")
            print(f"      keeps it TIGHT: {tight}")
        print(f"\n  ⛔ proposals with BOTH tests: {len(ap_covered)} of "
              f"{len(OPEN_PROPOSALS)} — {', '.join(ap_covered) or '—'}")
        for tag, why in ap_missing:
            print(f"     {RED}⛔ {tag}: {why}{GRAY}")
        print(f"\n== ⛔⛔ AND WHAT CANNOT BE JUDGED FROM A RECORDING")
        print(f"      ⚠ It sits in a table of its own: a cure without a test put "
              f"together with those")
        print(f"        that have the test would inflate the count")
        for tag, why in OUT_OF_REACH.items():
            print(f"  {tag}  {why}")
        print(f"\n== ⭐ P7 — {P7[0]}")
        print(f"      «{P7[1]}»")
        return 0
    if a.build:
        print("== the test recordings, in the format of RCP.md §11.1\n")
        factory(a.folder)
        return 0
    if a.certify:
        return certify(a)
    if not a.recording:
        # ⛔ Without a file it does not run silently: it says there is nothing
        #    to judge, with the code that fact has.
        print("== ⛔ no recording to judge.")
        print("   The tests are built with --build, the round with "
              "--certify.")
        return 3

    # ⛔ THE POSITIVE CONTROL, BEFORE the verdict and not after: it is checked that
    #    this tool can find an error that is surely there, and only
    #    afterwards is it pointed at the unknown (`LESSONS.md` §1.2).
    print("== ⛔ the positive control, BEFORE pointing the referee "
          "at the unknown")
    faulted, _ = run_tests(a.folder)
    if faulted:
        print(f"\n    {RED}⛔ the referee gets {faulted} known recordings "
              f"wrong: it is not the case to believe it on a new one{GRAY}")
        return 2
    print(f"\n    {GREEN}⭐ the referee agrees on all the known tests"
          f"{GRAY}\n")

    try:
        code, count = valid(a.recording, canvas=(a.canvas_width,
                                                      a.canvas_height),
                               codec=a.codec)
    except NotCompliant as e:
        print(f"\n   {RED}⛔ NOT CONFORMING — {e.rule}{GRAY}")
        print(f"      {e.says}")
        print(f"      byte {e.ass} in the file · offset {e.rel} in the payload "
              f"of the block")
        write_outcome(a.output, {"type": "judgement", "file": a.recording,
                                "exit": 1, "rule": e.rule, "says": e.says,
                                "byte": e.ass})
        return 1
    except Malformed as e:
        print(f"\n   ⚠ MALFORMED RECORDING: {e}")
        print("      ⛔ It is not a judgement on the wire: it is a defect of the file.")
        write_outcome(a.output, {"type": "judgement", "file": a.recording,
                                "exit": 2, "says": str(e)})
        return 2
    except NothingToJudge as e:
        print(f"\n   ⛔ NOTHING TO JUDGE: {e}")
        print("      It is not «conforming»: it is the absence of the object of "
              "judgement.")
        print("      Look at the recorder — whoever had to write those "
              "bytes.")
        write_outcome(a.output, {"type": "judgement", "file": a.recording,
                                "exit": 3, "says": str(e)})
        return 3
    except OSError as e:
        # ⛔ E8: «empty» and «forbidden» look the same.
        print(f"\n   ⚠ THE RECORDING CANNOT BE READ: {e}")
        print("      ⛔ It is not a judgement on the wire, and it is not «the file is "
              "broken»:")
        print("         it is that it could not be opened.  Look at permissions,")
        print("         path and volume — not at RCP.md.")
        return 2
    write_outcome(a.output, {"type": "judgement", "file": a.recording,
                            "exit": 0, **count})
    return code


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="F2.4 — the mechanical referee of the video channel")
    p.add_argument("recording", nargs="?")
    p.add_argument("--build", action="store_true",
                   help="builds the test recordings")
    p.add_argument("--certify", action="store_true",
                   help="healthy -> G4 -> healed")
    p.add_argument("--list", action="store_true",
                   help="the predictions and proposal P7, without measuring")
    p.add_argument("--folder", default=os.path.join(HERE, "02-filo-prove"),
                   help="where the test recordings are")
    p.add_argument("--canvas-width", type=int, default=1920)
    p.add_argument("--canvas-height", type=int, default=1080)
    p.add_argument("--codec", type=int, default=1, help="1 = HEVC, 2 = AV1")
    p.add_argument("--output", default="", help="the round's log, in JSONL")
    a = p.parse_args()
    os.makedirs(a.folder, exist_ok=True)
    sys.exit(main(a))
