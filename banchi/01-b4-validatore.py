#!/usr/bin/env python3
"""01-b4-validatore.py — the wire validator: which byte is not compliant with RCP.md.

    python3 01-b4-validatore.py recording.rcpreg

    exit 0  the recording is compliant — and it says ON HOW MANY messages
    exit 1  it is not compliant — and it says WHICH byte and WHICH rule
    exit 2  the RECORDING is broken, or cannot be read (not a judgement on the wire)
    exit 3  ⛔ there is NOTHING TO JUDGE (not a judgement on the wire)

---------------------------------------------------------------------------
⛔ WHAT IT IS, AND WHY IT IS A THIRD PROGRAM

`RCP.md` §11: *«client and server are NOT tested against each other: they are
tested against this document»*.  This is **the only mechanical arbiter** we
will have, and it is worth something only if it is written **by reading the
specification** — not the server, not the page.  Whoever grows it must not look
at the C: if they looked they would inherit its misunderstandings, and two
programs written by the same hand that agree confirm nothing (`README.md`).

---------------------------------------------------------------------------
⛔ FOUR OUTCOMES, AND THREE OF THEM SAY «IT IS NOT A JUDGEMENT ON THE WIRE»

  0  compliant — ⛔ and with the DENOMINATOR: how many blocks, how many on the
     control channel and how many on the video, how many messages read, how
     many with the body actually judged, how many video streams
  1  NOT compliant — with the offset of the byte and the violated rule
  2  ⛔ the RECORDING is broken, **or cannot be read**, ⛔ **or is from another
     version of the format**, ⛔ **or the tool to look at it is missing**
  3  ⛔ there is NOTHING TO JUDGE: zero control messages **and** zero
     video streams — ⚠ and the second half is from 12 Aug 2026

The **2** exists because «the file is broken» and «the wire was not compliant»
are two different facts with two different cures, and a validator that
confused them would send one looking for a protocol defect inside a bench
defect.

⛔ **And the file that does not open ends up there too** — 10 Aug 2026, finding
R7.5.  An `OSError` bubbled up out of `main` and the process exited **1**, that
is it said *«the wire is not compliant»* for a file that did not exist or that
one had no permissions for.  This validator also runs **inside the container**,
on recordings written by a server launched as root: the day the permissions do
not add up, the arbiter sent the diagnosis off to read the protocol.  It is
error form **E8** to the letter: «empty» and «forbidden» look the same.

⛔ **And the 3 is new, from the same finding (R7.4)**, and it cures the opposite
side: a recording with **zero blocks**, or made only of video blocks, exited
**0** with the sentence *«⭐ compliant: 0 blocks, no violation»*.  «I have
nothing to judge» and «I judged everything and it is fine» are two different
facts with the same colour, and it is `LEZIONI.md` §1.9: *a count without a
denominator*.  ⚠ An arbiter that acquits without having looked is worse than
an arbiter that is wrong: people build on top of its green.

---------------------------------------------------------------------------
⛔ AND IT REPORTS **WHICH** BYTE, NOT ONLY THAT IT IS RED

`FASI.md` §01-filo-nudo B4: on the recording with padding, a validator that
does not know §6.0 does not see the extra byte: it misreads the NEXT message
and declares that one non-compliant.  **Right red, wrong byte** — and on a real
trace it sends the diagnosis off to read the wrong message.  That is why every
verdict carries two offsets (absolute and inside the block) and the line of
RCP.md that supports the judgement.

---------------------------------------------------------------------------
⭐⛔ ON 12 AUG 2026 THIS VALIDATOR LEARNED THE **VIDEO CHANNEL**

Until 11 August line 521 said:

    if channel != 0x00:
        print(... "not judged by this validator")
        continue

⚠ It was an **honest** line — it declared it did not judge, which is the
opposite of acquitting — but from the first frame on the most voluminous
chapter of the wire would have gone back to being validated by **a single**
implementation, written by the same hand that writes the server: the state
that `RCP.md` §0 calls the silent defect.

⛔ And on 12 Aug 2026 **six normative lines** entered `RCP.md`, all about the
video (§2.5, §5.2, §6.2), and neither of the two arbiters knew how to judge
them.  Now:

  **P1** §2.5   no video stream before having sent `SESSION`
  **P2** §6.2   `nr` starts at **1**, and `0` is reserved
  **P3** §2.5   a `0x03` on the **control channel** is `PROTOCOL_ERROR`
  **P4** §6.2   **FIN before the 28 bytes** is `PROTOCOL_ERROR`
  **P5** §6.2   `width`/`height` **MUST** equal the granted canvas
  **P6** §5.2   the first frame after `SESSION` **MUST** be a key frame

⛔⛔ **AND THE FRAME JUDGEMENT IS NOT REWRITTEN HERE: IT IS IMPORTED.**
`02-filo-fotogramma.py` is the judge written by reading `RCP.md` §6.2, and two
copies of the same reading would be two implementations by the same hand —
that is precisely what an external arbiter exists to prevent.  ⚠ If it is not
found, this validator **does not guess and does not skip**: it exits **2**,
which is «I could not look», and says so.

⚠ ⛔ **AND A HOLE THAT MUST BE DECLARED, because curing it is not this file's
job.**  `01-b12-guasti.py` lists in `FILE_CHE_CONTANO["B4"]` the three files the
B4 certification rests on, and `02-filo-fotogramma.py` **is not among them**:
from today one can rewrite the frame judge and the line «B4 certified» stays
valid at sight while the certified bench is no longer the same.  It is exactly
the shape of finding **R12-A.5**, come back in through another door.
⇒ The cure is an entry in `FILE_CHE_CONTANO` and one in `CORREDO`, and that file
belongs to whoever looks after **D10**.  Here it is declared.

---------------------------------------------------------------------------
⭐⛔ ON 16 AUG 2026 THIS VALIDATOR LEARNED THE **CANVAS** — sub-phase 6.6

`fasi/06-la-tela-e-la-vista.md` §0 point 6: *«the RCP/1 benches do not exercise
the new road: `01-b3-cliente.py` and `01-b4-validatore.py` stay green because
the wire has not changed, ⛔ but **neither of the two sends an `FIT_CANVAS`»*.

⛔ And not sending it was not the worst hole: the hole was that **neither of the
   two knew how to JUDGE it**.  `FIT_CANVAS` and `CANVAS` both sat in
`AFTER_SESSION`, that is they were allowed in any order and in any number, and
the three rules that §7.1 writes in capital letters were enforced by nobody:

  **T1** §7.1  an **unsolicited** `CANVAS` — §6.2 gives the client a single way
               of accepting an unexpected size (holding while a request is
               unanswered) ⇒ a `CANVAS` that answers nothing **makes a healthy
               session close**
  **T2** §6.2  **two** `CANVAS` for a single `FIT_CANVAS` — *«the n-th `CANVAS`
               answers the n-th `FIT_CANVAS`»*, and the count gets lost
  **T3** §7.1  an **unanswered** `FIT_CANVAS`: *«a silence leaves the
               client waiting forever for an answer that will not come,
               and the symptom is "the application froze"»*
  **T5** §7.1  the **canvas in force** that contradicts the message: the two
               fields are *«the canvas in force AFTER this message»*, and a
               refusal changes nothing
  **T6** §4.5  a **granted** canvas with an odd side or out of bounds
  **V1** §7.1  a `VIEW` **0** on one side: *«any size from 1x1 up»*
  **V3** §7.1  a `VIEW` that **changes the canvas**: it is forbidden, and on
               the wire it shows up as a `CANVAS` answering a `VIEW`

⚠⛔ **AND THREE THINGS THIS ARBITER DECLARES IT CANNOT DO**, because a check
    that cannot be done must be declared, not simulated:

  1. ⛔ **the in-flight coordinates of §7.1 ARE NOT JUDGED, and not out of
     laziness: the format of §11.1 does not record TIME.**  §7.1 requires that
     after a `CANVAS(ADAPTED)` the server accept *«for one second»* coordinates
     valid on the previous canvas, and *«once that second has passed, they are
     `PROTOCOL_ERROR`»*.  ⇒ A normative rule with a clock inside it,
     against a recording format that carries no instant: **no validator
     reading an `.rcpreg` will ever be able to arbitrate it**.  It is a hole in
     `RCP.md` §11.1, not in this file, and it is written here so that whoever
     reads «13 out of 13» does not believe that line is covered;
  2. the **requested size** and the **granted** one need not match — §4.5:
     *«the granted canvas may differ from the requested one»* — so a
     `CANVAS(ADAPTED)` that grants something else **is not accused**;
  3. an `FIT_CANVAS` **outside the limits of §4.5 is LAWFUL**: §7.1 devotes a
     refusal reason to it, `SIZE_OUT_OF_LIMITS`.  ⛔ An arbiter that rejected
     it would make unreachable a branch the specification names.

---------------------------------------------------------------------------
⛔ THE RECORDING FORMAT IS `RCPREG 0x00 0x03`, AND THE OLD ONES ARE REJECTED

§11.1, 12 Aug 2026: the block carries `fine` — *0 continues · 1 FIN · 2
RESET_STREAM* — and goes from **16 to 17 bytes**.  ⛔ *«The magic moves to 0x00
0x02 because the block changes size: an old validator must REJECT the new
format, not misread it»*, and it holds in both directions: an `.rcpreg` of 10
August read with this reader would have the `channel` inside the `stream` and
every block slipped by one byte — out would come a **judgement** on bytes
nobody wrote.

⭐⭐ AND SINCE **21 AUG 2026** THE MAGIC IS `0x00 0x03`: the block carries
`instant_ms` (u32, monotonic, from the FIRST block) and goes from **17 to 21
bytes**; the header carries `clock_v` — 1 = the times are the client's, 2 = the
server's.  ⛔ The magics `0x01` and `0x02` are both rejected, **with two
different sentences**: they send one to look at two different places (a file
of 10 August and one of 12).

⛔⛔ AND TIME DOES NOT MAKE THE ARBITER OMNISCIENT: the conclusion goes **in one
direction only**.  The grace-second rule (§7.1) belongs to the **server** — it
measures from when IT sent `CANVAS(ADAPTED)` to when IT received the
`POINTER`.  A recording taken at the **client** sees *«when the CANVAS
arrived»* and *«when the POINTER left»*, that is an interval **shorter** than
the server's: half a network round trip per side.  ⇒
  · if the client's interval is **> 1000 ms**, the server's was so **all the
    more** ⇒ the server HAD to refuse, and if it kept serving it is
    `NOT COMPLIANT`;
  · if it is **<= 1000 ms**, ⛔ **nothing is concluded**, and the validator
    **SAYS SO**.  An arbiter that keeps quiet about what it does not know is an
    arbiter that acquits.
"""
import hashlib
import importlib.util
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

MAGIC = b"RCPREG\x00\x03"
# ⛔ The old ones are ALL kept, each with its own sentence: «it is not of the
#    format» and «it is of another version» send one looking in two places, and
#    so do two different old versions.
MAGIC_V1 = b"RCPREG\x00\x01"
MAGIC_V2 = b"RCPREG\x00\x02"
OLD_MAGIC = MAGIC_V1        # ⚠ the old name stays: 01-b12 imports it
FILL = 0x2A  # the byte of the obscured intervals (RCP.md §11.1)

# The block of §11.1: direction, channel, end, instant_ms, stream, length,
# quanti_oscurati.  ⭐ `instant_ms` since 21 Aug 2026: 21 bytes, no longer 17.
BLOCK = "!BBBIQIH"
BLOCK_BYTES = struct.calcsize(BLOCK)
CONTINUE, FIN, RESET = 0, 1, 2
FINE = {CONTINUE: "go_on", FIN: "FIN", RESET: "RESET_STREAM"}

VIDEO = 0x03
CHECK = 0x00
INPUT = 0x01
T_POINTER = 0x0101            # §7.3
CLOCK = {1: "client", 2: "server"}
# §7.1: «for one second».  The same number as `rcp.c` (`CANVAS_GRACE`).
GRACE_MS = 1000
# ⛔ The T4 cap, and where it comes from: §7.1 grants the server `RCP_CANVAS_WAIT_MS`
#    = 3000 ms to get a frame at the new size delivered **before**
#    answering.  ⇒ After a `CANVAS(ADAPTED)` that frame already exists, and three
#    seconds are generous.  ⚠ It is a READING, not a line of RCP.md: if it is
#    wrong the place to fix is §7.1, not this file.
T4_CAP_MS = 3000


def search_upward(label_name, da):
    """The file `label_name` walking up the folders from `da`.  ⛔ (None) if it is not there.

    ⚠ It is needed because `01-b12-guasti.py` runs this validator from a
      **copy** (`01-b12-copie/`) that contains only the B4 kit: the frame
      judge is not there, and it must be looked for where it really is.  It is
      the same road `01-b9-letture.py` uses to find `RCP.md`.
    """
    d = da
    for _ in range(6):
        p = os.path.join(d, label_name)
        if os.path.exists(p):
            return p
        su = os.path.dirname(d)
        if su == d:
            break
        d = su
    return None


def frame_judge():
    """⛔ The judge is IMPORTED, not copied — see the header.

    Returns (module, why_not).  ⚠ A failed import **is not a compliant
    frame**: the caller exits 2.
    """
    p = search_upward("02-filo-fotogramma.py", HERE)
    if p is None:
        return None, ("`02-filo-fotogramma.py` cannot be found walking up from "
                      f"{HERE}: it is the judge that applies §6.2, and without it "
                      f"the video channel is not judged")
    try:
        spec = importlib.util.spec_from_file_location("f24_b4", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as e:                      # noqa: BLE001
        return None, f"«{p}» cannot be imported: {type(e).__name__}: {e}"
    return mod, ""

# ---------------------------------------------------------------------------
# The message types of the control channel — RCP.md §7.1
CLIENT, SERVER = 1, 2
TYPES = {
    0x0001: ("HELLO", CLIENT),
    0x0002: ("HERE_I_AM", SERVER),
    0x0003: ("CREDENTIALS", CLIENT),
    0x0004: ("ADMITTED", SERVER),
    0x0005: ("REJECTED", SERVER),
    0x0006: ("ATTACH", CLIENT),
    0x0007: ("SESSION", SERVER),
    0x0008: ("VIEW", CLIENT),
    0x0009: ("LAYOUT", CLIENT),
    0x000A: ("CURSOR_SHAPE", SERVER),
    0x000B: ("FIT_CANVAS", CLIENT),
    0x000C: ("FAREWELL", None),  # ↔ both directions
    0x000D: ("REQUEST_KEY", CLIENT),
    0x000E: ("CANVAS", SERVER),
    0x000F: ("BENCH_MARK", CLIENT),
    0x0010: ("BENCH_OUTCOME", SERVER),
    # ⛔ 0x0011 WAS MISSING, and it is from 15 Aug 2026 (§7.6).  An arbiter that
    #    does not know a type the specification defines does not «not judge
    #    it»: it accuses it as an **unknown type** (§7.1) and closes the
    #    recording at the first message with which the user leaves the desktop.
    #    ⚠ It is a false red that was just waiting for the first trace with an
    #    exit inside it.
    0x0011: ("TERMINATE_SESSION", CLIENT),
}

CHANNELS = {0x00: "check", 0x01: "input", 0x02: "clipboard_text",
          0x03: "video", 0x04: "audio"}

# The reasons of §8.2, to say them by name instead of by number.
REASONS = {
    0x01: "CLOSED_BY_USER", 0x02: "INACTIVITY", 0x03: "SESSION_ABANDONED",
    0x04: "LOCAL_SESSION_PREVAILED", 0x05: "ALREADY_ACTIVE_LOCAL", 0x06: "BUDGET_FULL",
    0x07: "WRONG_CREDENTIALS", 0x08: "TOO_MANY_ATTEMPTS", 0x09: "NOTHING_IN_COMMON",
    0x0A: "INCOMPATIBLE_VERSION", 0x0B: "PROTOCOL_ERROR", 0x0C: "SERVER_SHUTTING_DOWN",
    0x0D: "TIMED_OUT", 0x0E: "SESSION_UNSERVABLE", 0x0F: "ALREADY_ACTIVE_REMOTELY",
    # ⛔ And 0x10 is from 15 Aug 2026, together with `TERMINATE_SESSION` (§7.6,
    #    §8.2): it is the **mandatory** answer to that message.  ⚠ Without
    #    this line the arbiter accused «unknown reason» precisely on the
    #    farewell the specification requires — that is it gave red to the
    #    server doing the only thing §7.6 allows it.
    0x10: "SESSION_TERMINATED",
}

# The capabilities of §4.3, with the side that may declare them.
CAPABILITIES = {
    "video.codec": None, "video.bit_depth": None, "audio.codec": None,
    "clipboard_text.body_text": None,
    "video.level": CLIENT, "video.max_size": CLIENT,
    "input.tap": CLIENT, "client.label_name": CLIENT,
    "bench.mark": SERVER,
}
# ⛔ The underscore is there since 10 Aug 2026: the first run of this
#    validator found that §4.3 forbade a character that §4.3 itself uses in
#    `video.max_size`.  The cure is in RCP.md.
ALLOWED_NAME_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789._")

MAX_MESSAGE_LEN = 1024 * 1024  # §6.1


class NotCompliant(Exception):
    """The wire does not respect RCP.md.  It carries the byte and the rule."""

    def __init__(self, rule_v, says, ass, rel):
        super().__init__(says)
        self.rule_v, self.says, self.ass, self.rel = rule_v, says, ass, rel


class Malformed(Exception):
    """The RECORDING is broken: it is not a judgement on the wire."""


class NothingToJudge(Exception):
    """⛔ In the file there is nothing this validator knows how to judge.

    It is not «compliant» and it is not «non-compliant»: it is the absence of
    the object of the judgement, and it has its own exit code because the cure
    is another — one looks at the recorder, not at the protocol (finding R7.4).

    ⚠ **And since 12 Aug 2026 it means two things together**: zero control
      messages **and** zero video streams.  Before, the first was enough,
      because nobody looked at the video; a recording of frames only exited 3
      and it was true.  Today that same recording has an object of judgement,
      and saying «nothing to judge» would be **acquitting without having
      looked**.
    """


class CouldNotLook(Exception):
    """⛔ The tool is missing, not the judgement — and they are two different things.

    ⚠ It has the same exit code as `Malformed` (**2**) because neither of the
      two is a judgement on the wire, but **not the same sentence**: there one
      looks at the file, here at the installation.  Confusing them would send
      one looking for a recording defect inside a failed import.
    """


# ---------------------------------------------------------------------------
class Reader:
    """Reads fields from the payload of a block, and knows where it must NOT look.

    ⛔ Every read checks it has the bytes before taking them: reading past the
       end and saying «non-compliant» would be saying the right thing for the
       wrong reason — the defect would be a truncation, not a field.
    """

    def __init__(self, load, base_ass, obscured):
        self.b, self.i, self.base = load, 0, base_ass
        self.obscured = obscured  # [(start, count)]

    def ass(self, rel=None):
        return self.base + (self.i if rel is None else rel)

    def stays(self):
        return len(self.b) - self.i

    def _take(self, n, desc, admit_obscured=False):
        if self.stays() < n:
            raise NotCompliant(
                "RCP.md §6.1",
                f"the body ends before {desc}: {n} bytes were needed, there are {self.stays()}",
                self.ass(), self.i)
        # ⛔⛔ ONE DOES NOT READ INSIDE AN OBSCURED INTERVAL — §11.1, and until
        #     16 Aug 2026 this guard was **only** in `string()`.
        #
        # ⭐ The defect came out the very day it was born, by refuting: an
        #    obscured interval placed over `canvas_width` of a `CANVAS` made it
        #    accusations *«grants tela_larghezza = 707406378, outside 320..7680»* —
        #    and **707406378 is `0x2A2A2A2A`**, that is the padding of §11.1
        #    read as a size.
        #
        # ⛔ A protocol red on bytes the format declares it has replaced is the
        #    worst of false reds: it sends one looking for a server defect
        #    inside a choice of the recorder, and §11.1 asks for two different
        #    sentences for *«a malformed recording»* and *«a non-compliant
        #    wire»*.  ⇒ it is outcome **2**.
        # ⚠ `admit_obscured` is passed only by `string()` for the DATA of the
        #   string, which are the only thing §11.1 exists to hide (§4.4, the
        #   password).  Its LENGTH is not: obscuring it would make the body
        #   unreadable, which is the perpetual false red §11.1 was written
        #   against.
        if not admit_obscured and self.is_obscured(self.i, n):
            raise Malformed(
                f"an obscured interval covers {desc}, at offset "
                f"{self.i} of the payload (byte {self.ass()} in the file).  ⛔ §11.1 "
                f"exists for the password of §4.4: a recorder that "
                f"obscures a NUMERIC field makes that field unjudgeable, and "
                f"reading it would give a verdict on the 0x2A padding bytes")
        v = self.b[self.i:self.i + n]
        self.i += n
        return v

    def u8(self, desc):
        return self._take(1, desc)[0]

    def u16(self, desc):
        return struct.unpack("!H", self._take(2, desc))[0]

    def u32(self, desc):
        return struct.unpack("!I", self._take(4, desc))[0]

    def is_obscured(self, start, how_many):
        """Does the interval [start, start+how_many) touch an obscured zone?"""
        return any(not (start + how_many <= o or start >= o + q)
                   for o, q in self.obscured)

    def string(self, desc, minimum=0, maximum=None, rule_v="RCP.md §4.4"):
        """RCP.md §6.0: u16 length + that length of UTF-8, without terminator.

        ⛔ `rule_v` is passed from outside.  The ranges of the user and of the
           password are in §4.4, those of the capability names and values in
           §4.3 — and here §4.4 was cited for all of them.  A red with the
           wrong section next to it passes the check of `01-b4-lancia.py`
           without anybody noticing, because the colour is the right one
           (finding R7.12).
        """
        field_start = self.i
        n = self.u16(f"the length of {desc}")
        data_start = self.i
        b = self._take(n, desc, admit_obscured=True)
        if n < minimum:
            raise NotCompliant(rule_v,
                              f"{desc} is {n} bytes long, the minimum is {minimum}",
                              self.base + field_start, field_start)
        if maximum is not None and n > maximum:
            raise NotCompliant(rule_v,
                              f"{desc} is {n} bytes long, the maximum is {maximum}",
                              self.base + field_start, field_start)
        # ⛔ Inside an obscured interval one does NOT look: those bytes are
        #    padding, and judging them would be judging the bench.
        if self.is_obscured(data_start, n):
            return None
        try:
            return b.decode("utf-8")
        except UnicodeDecodeError as e:
            raise NotCompliant(
                "RCP.md §6.0",
                f"{desc} is not valid UTF-8 ({e.reason}) at byte {e.start} of the string",
                self.base + data_start + e.start, data_start + e.start) from None

    def fine(self, label_name):
        """⛔ Not one byte more: §6.0 forbids alignment and padding."""
        if self.stays():
            raise NotCompliant(
                "RCP.md §6.0",
                f"{label_name}: {self.stays()} extra bytes after the expected fields — "
                "no field is aligned and no padding is allowed",
                self.ass(), self.i)


# ---------------------------------------------------------------------------
def read_capabilities(le, message_name, side):
    """RCP.md §4.3 — the list of capabilities, with all its rules."""
    how_many_n = le.u16("the number of capabilities")
    seen_items, values = {}, {}
    for k in range(how_many_n):
        start = le.i
        label_name = le.string(f"the name of capability {k}", minimum=1, maximum=64,
                          rule_v="RCP.md §4.3")
        value_v = le.string(f"the value of capability {k}", maximum=256,
                            rule_v="RCP.md §4.3")
        if label_name is None:
            continue  # obscured: not judged
        if not label_name or any(c not in ALLOWED_NAME_CHARS for c in label_name):
            raise NotCompliant("RCP.md §4.3",
                              f"the capability name {label_name!r} is not made of a-z, 0-9 and dot",
                              le.base + start, start)
        # ⛔ A repeated name is PROTOCOL_ERROR: «the last one wins» and «the
        #    first one wins» are two implementations of the same document.
        if label_name in seen_items:
            raise NotCompliant("RCP.md §4.3",
                              f"the capability {label_name!r} appears twice "
                              f"(the first at offset {seen_items[label_name]})",
                              le.base + start, start)
        seen_items[label_name] = start
        values[label_name] = value_v
        if value_v is not None and value_v == "":
            raise NotCompliant("RCP.md §4.3",
                              f"the capability {label_name!r} has an empty value: "
                              "whoever has nothing to say does not send the capability",
                              le.base + start, start)
        # ⛔ A KNOWN name from the wrong side is not covered by the exception
        #    for unknown names.
        expected_val = CAPABILITIES.get(label_name)
        if expected_val is not None and expected_val != side:
            chi = "client" if side == CLIENT else "server"
            raise NotCompliant("RCP.md §4.3",
                              f"the capability {label_name!r} cannot come from the {chi}",
                              le.base + start, start)
    # ⛔ The VALUES are returned, not the offsets: from here `body_el()` takes the
    #    codec negotiated in `HERE_I_AM`, which §6.2 ties to the `codec` field of
    #    every frame.  ⚠ The offsets stay internal — they were only needed for
    #    the repeated-name message.
    return values


def declared_size(value_v):
    """`3840x2160` -> (3840, 2160).  ⛔ (None) if it does not have that shape.

    ⚠ §4.3 does not dictate the syntax of `video.max_size`, and this arbiter
      **does not invent it**: a value that cannot be read counts as «not
      declared», not «zero».  Deducing a limit from a string one does not
      understand would be judging the server against a number nobody wrote.
    """
    if not value_v:
        return None
    parts = value_v.lower().split("x")
    if len(parts) != 2 or not all(p.strip().isdigit() for p in parts):
        return None
    return int(parts[0]), int(parts[1])


def within_maximum(max_dims, lar, alt_h):
    """Is the size within the one declared by the client?  (None) = not declared."""
    return max_dims is None or (lar <= max_dims[0] and alt_h <= max_dims[1])


def body_el(kind, label_name, le, side, state=None):
    """Reads the body according to the type.  §4.3, §4.4, §4.5, §7.1.

    ⛔ `state` is there since 12 Aug 2026: the VIDEO channel cannot be judged
       without the **granted canvas** (§4.5, for P5) and without the
       **negotiated codec** (§4.3, for §6.2), and both travel here.  ⚠ Taking
       them from one's own defaults would be judging oneself.
    """
    if label_name in ("HELLO", "HERE_I_AM"):
        le.u16("the version")
        cap = read_capabilities(le, label_name, side)
        # ⛔ §4.5: *«The granted canvas MUST respect `video.misura_massima` if
        #    the client declared it»*.  ⚠ It is in the **same sentence** as the
        #    limits and the parity, and until 16 Aug 2026 the arbiter applied
        #    two thirds of that sentence: a `SESSION` that granted 7680x4320
        #    to a client that had declared `3840x2160` came out ⭐ compliant.
        #    Found by refuting, not by rereading.
        if state is not None and label_name == "HELLO":
            state.max_size = declared_size(cap.get("video.max_size"))
        if state is not None and label_name == "HERE_I_AM":
            # §4.3: `HERE_I_AM` carries the server's choice, a single one.
            state.codec = {"hevc": 1, "av1": 2}.get(
                (cap.get("video.codec") or "").split(",")[0].strip())
    elif label_name == "CREDENTIALS":
        le.string("the user", minimum=1, maximum=256, rule_v="RCP.md §4.4")
        le.string("the password", minimum=1, maximum=1024, rule_v="RCP.md §4.4")
    elif label_name in ("ADMITTED", "TERMINATE_SESSION"):
        # ⛔ §7.6: «(empty body)», and §6.0 forbids padding ⇒ `le.fine()` at the
        #    bottom of this function does the rest.  ⚠ Declaring it «not
        #    judged» would have been more convenient and false: an empty body
        #    is a body that gets judged, and one extra byte is the shape of §6.0.
        pass
    elif label_name == "REJECTED":
        m = le.u8("the reason")
        if m not in REASONS:
            raise NotCompliant("RCP.md §8.2", f"unknown reason {m:#04x}",
                              le.ass(-1) if False else le.base + le.i - 1, le.i - 1)
    elif label_name == "ATTACH":
        # ⛔ THE OFFSET OF THE FIELD IS TAKEN BEFORE READING IT.
        #
        #    These four `raise` passed `le.base, 0`: the start of the BODY as
        #    absolute and ZERO as relative, that is **two different bytes**.
        #    §11.1 asks for two ways of saying the **same** byte — «absolute in
        #    the file, and relative to the block's payload» — and whoever opened
        #    the file with an editor and whoever read the specification ended up
        #    looking at two different points.  And on `canvas_height` the accused
        #    byte was the width's anyway (finding R7.12).
        off_lar = le.i
        lar = le.u32("canvas_width")
        off_height = le.i
        alt_h = le.u32("canvas_height")
        le.u32("vista_larghezza")
        le.u32("vista_altezza")
        le.string("the layout", maximum=64, rule_v="RCP.md §4.5")
        # ⛔ The limits are normative, and parity is not pedantry: an odd
        #    size gets rounded by the encoder, silently.
        # ⭐ since 1 Oct 2026 the maximum is 4096x2304 (`RCP.md` §4.5); ⚠ here one
        #    judges the canvas REQUESTED in ATTACH: above the maximum the server
        #    reduces it and grants it, so it is NOT a client violation —
        #    the minimum and the parity are checked, and the maximum stays with
        #    the GRANTED canvas (SESSION and CANVAS)
        for lbl, v, off, mi, ma in (("canvas_width", lar, off_lar, 320, None),
                                    ("canvas_height", alt_h, off_height, 240, None)):
            if v < mi:
                raise NotCompliant("RCP.md §4.5",
                                  f"{lbl} = {v}, below the minimum {mi}",
                                  le.base + off, off)
            if v % 2:
                raise NotCompliant("RCP.md §4.5", f"{lbl} = {v} is odd",
                                  le.base + off, off)
    elif label_name == "SESSION":
        st = le.u8("the state")
        if st not in (1, 2):
            raise NotCompliant("RCP.md §4.5",
                              f"state {st}: expected 1 = NEW or 2 = RESUMED",
                              le.base + le.i - 1, le.i - 1)
        off_lar = le.i
        lar = le.u32("canvas_width")
        alt_h = le.u32("canvas_height")
        le.string("the desktop", maximum=64, rule_v="RCP.md §4.5")
        # ⛔ THE GRANTED CANVAS — it is this one that §6.2 ties to `width`/`height`.
        if state is not None and lar is not None and alt_h is not None:
            # ⛔ §4.5, the third part of the sentence: *«The granted canvas MUST
            #    respect `video.misura_massima` if the client declared it»*.
            #    ⚠ The client that declares a cap declares it because beyond it
            #    **it does not decode**: a bigger canvas is not an extra
            #    convenience, it is a session that cannot be seen.
            if not within_maximum(state.max_size, lar, alt_h):
                m = state.max_size
                raise NotCompliant(
                    "RCP.md §4.5",
                    f"SESSION grants a {lar}x{alt_h} canvas while the client "
                    f"had declared video.max_size = {m[0]}x{m[1]} "
                    f"in HELLO (§4.3)",
                    le.base + off_lar, off_lar)
            state.canvas_size = (lar, alt_h)
    elif label_name == "FAREWELL":
        m = le.u8("the reason")
        if m not in REASONS:
            raise NotCompliant("RCP.md §8.2",
                              f"unknown reason {m:#04x} — and code 0 "
                              "MUST NOT be used (§3.1)",
                              le.base + le.i - 1, le.i - 1)
        le.string("the detail", rule_v="RCP.md §7.1")
    elif label_name == "VIEW":
        # ⛔ V1 — §7.1: *«any size from 1x1 up is legal, odd
        #    included»*.  ⚠ So here ONE thing only is checked, and the others
        #    are NOT checked: the limits 320x240..4096x2304 and the parity belong
        #    to the CANVAS, and §7.1 took them away from the view on the evening
        #    of 9 Aug 2026 (finding R1.17) because *«the user shrinks the browser
        #    window to 300 pixels»* and with the old line the client had three
        #    choices, all bad.  ⛔ An arbiter that put them back would
        #    resurrect R1.17 from the arbiter's side.
        off_lar = le.i
        lar = le.u32("width_px")
        off_height = le.i
        alt_h = le.u32("height_px")
        for lbl, v, off in (("width_px", lar, off_lar),
                            ("height_px", alt_h, off_height)):
            if v == 0:
                raise NotCompliant(
                    "RCP.md §7.1",
                    f"VIEW with {lbl} = 0: §7.1 says «any size from 1x1 "
                    f"up is legal» — zero is not «up», and there is "
                    f"no «absent» value declared for this field "
                    f"(§6.0)",
                    le.base + off, off)
    elif label_name == "FIT_CANVAS":
        # ⛔ AND HERE NOTHING IS CHECKED, AND IT IS A DECISION.
        #
        #    §4.5 imposes on the canvas the limits and the parity, but those hold
        #    for `ATTACH` and for the GRANTED canvas.  A request out of bounds
        #    is **lawful**: §7.1 devotes a refusal reason to it by name —
        #    `SIZE_OUT_OF_LIMITS` — and a reason exists to be reached.
        #    ⛔ An arbiter that rejected the request would make unreachable
        #       a branch the specification names, and the bench that exercises
        #       it (`23-adatta-fuori-limiti`) would become impossible to write.
        #    ⚠ It is the same shape as R1.17: applying to one message the limits
        #      of another because the fields have the same name.
        le.u32("width_px")
        le.u32("height_px")
    elif label_name == "LAYOUT":
        le.string("the layout", maximum=64, rule_v="RCP.md §4.5")
    elif label_name == "REQUEST_KEY":
        le.u32("ultimo_numero")
    elif label_name == "CANVAS":
        # ⛔ JUDGED SINCE 12 AUG 2026, and not for completeness: §6.2 ties
        #    `width`/`height` of every frame to the **canvas in force**, and
        #    the only message that changes it is this one.  ⚠ Until yesterday it
        #    ended up in the branch «bodies this validator does not serve yet»,
        #    that is the video channel could not have been judged at all after
        #    an `FIT_CANVAS`.
        es = le.u8("the outcome")
        if es not in (1, 2):
            raise NotCompliant("RCP.md §7.1",
                              f"outcome {es}: expected 1 = ADAPTED or "
                              f"2 = RIFIUTATA",
                              le.base + le.i - 1, le.i - 1)
        rsn = le.u8("the reason")
        if es == 1 and rsn != 0:
            raise NotCompliant("RCP.md §7.1",
                              f"CANVAS(ADAPTED) with reason {rsn}: §7.1 wants "
                              f"0 when the outcome is ADAPTED",
                              le.base + le.i - 1, le.i - 1)
        if es == 2 and rsn not in (1, 2, 3):
            raise NotCompliant("RCP.md §7.1",
                              f"reason {rsn}: §7.1 defines three — 1 = "
                              f"COMPOSITOR_UNABLE, 2 = SIZE_OUT_OF_LIMITS, "
                              f"3 = NOT_NOW",
                              le.base + le.i - 1, le.i - 1)
        off_lar = le.i
        lar = le.u32("canvas_width")
        off_height = le.i
        alt_h = le.u32("canvas_height")
        # ⛔ §7.1: these two fields are «the canvas in force AFTER this
        #    message» — and they are so **also** when the outcome is RIFIUTATA,
        #    where they report the previous one.  ⇒ the field is taken, not
        #    deduced from the outcome: it is the field that is defined that way.
        #
        # ⭐⛔ T5 — AND FROM HERE ON IT IS CHECKED THAT THE FIELD DOES NOT
        #     CONTRADICT THE MESSAGE CARRYING IT (16 Aug 2026, sub-phase 6.6).
        #
        #     Until yesterday the field was simply taken.  ⚠ But «the canvas in
        #     force AFTER this message» after a **REFUSAL** is necessarily the
        #     PREVIOUS one: a refusal that changed the canvas would be an
        #     adaptation with the wrong label, that is error form **E2** — and
        #     the damage is not theoretical, because §6.2 ties `width`/`height`
        #     of every frame exactly to this field: the client would start
        #     **throwing away the good frames as non-compliant**, or accepting
        #     wrong ones, without anybody having sent a malformed message.
        if state is not None and lar is not None and alt_h is not None:
            before = state.canvas_size
            # ⛔ The PREVIOUS canvas is kept: it is half of defect D14 —
            #    the frames already in flight carry it **legitimately**, and
            #    `02-filo-fotogramma.py` wants it to open the grace of §6.2.
            state.prev_canvas = before
            if es == 2 and before is not None and (lar, alt_h) != before:
                raise NotCompliant(
                    "RCP.md §7.1",
                    f"CANVAS(RIFIUTATA) declares the canvas in force {lar}x{alt_h}, "
                    f"but the one in force was {before[0]}x{before[1]} and a "
                    f"refusal does not change it: §7.1 defines the two fields as "
                    f"«the canvas in force AFTER this message», and §6.2 ties "
                    f"the size of every frame to them",
                    le.base + off_lar, off_lar)
            # ⛔ T6 — the GRANTED canvas respects §4.5: limits and parity.
            #
            #    ⚠ **It is a reading, and it must be said**: §7.1 does not
            #      repeat the limits for `CANVAS`.  They apply anyway because §4.5
            #      declares them *«normative»* for the canvas and gives the
            #      reason — *«video encoders work on blocks, and an odd size
            #      gets rounded by whoever encodes, silently»* — and that reason
            #      holds identically for a canvas granted by `CANVAS`: §6.2 sends
            #      all the following frames at that size.  ⇒ If they held only
            #      in `ATTACH`, `FIT_CANVAS` would be the door through which
            #      exactly the defect §4.5 closes comes back in.
            #    ⛔ If this reading were wrong, the place to fix is
            #       `RCP.md` §7.1 — one line — not this file.
            if es == 1 and not within_maximum(state.max_size, lar, alt_h):
                # ⛔ The same sentence of §4.5 holds here: a **granted** canvas
                #    is a granted canvas, whether it comes from `SESSION` or
                #    from `CANVAS`.  ⚠ If it did not hold, `FIT_CANVAS` would be
                #    the door through which one exceeds a cap the client
                #    declared so as not to be left in the dark.
                m = state.max_size
                raise NotCompliant(
                    "RCP.md §4.5",
                    f"CANVAS(ADAPTED) grants {lar}x{alt_h} while the client "
                    f"had declared video.max_size = {m[0]}x{m[1]}",
                    le.base + off_lar, off_lar)
            if es == 1:
                for lbl, v, off, mi, ma in (
                        ("canvas_width", lar, off_lar, 320, 4096),
                        ("canvas_height", alt_h, off_height, 240, 2304)):
                    if not (mi <= v <= ma):
                        raise NotCompliant(
                            "RCP.md §4.5",
                            f"CANVAS(ADAPTED) grants {lbl} = {v}, outside "
                            f"{mi}..{ma}: §4.5 declares the limits «normative» "
                            f"for the canvas, and §6.2 sends every frame at "
                            f"this size",
                            le.base + off, off)
                    if v % 2:
                        raise NotCompliant(
                            "RCP.md §4.5",
                            f"CANVAS(ADAPTED) grants {lbl} = {v}, odd: "
                            f"«an odd size gets rounded by whoever "
                            f"encodes, silently» — and the refusal must be said "
                            f"here, where one can say why",
                            le.base + off, off)
            state.canvas_size = (lar, alt_h)
            if es == 1:
                state.canvas_from = "CANVAS(ADAPTED) (§7.1)"
                # ⭐ The instant of the `CANVAS(ADAPTED)`: it is the start date of
                #    the grace second (§7.1) and the point from which T4 counts.
                state.canvas_adapted_ms = state.instant
                state.adapted.append((le.base + off_lar, (lar, alt_h),
                                       state.instant))
    else:
        # The bodies that RCP/1 defines and this validator does not needs yet
        # (CURSOR_SHAPE, BANCO_*): it declares it does not judge them.
        # ⚠ `CANVAS` was here until 11 Aug 2026, and it came out because the
        #   video channel needs the canvas in force (§6.2).
        return False
    le.fine(label_name)
    return True


# ---------------------------------------------------------------------------
# The state machine of the handshake — RCP.md §1 and §4.
ORDER = ["HELLO", "HERE_I_AM", "CREDENTIALS", "ADMITTED", "ATTACH", "SESSION"]

# ⛔ The messages that live AFTER `SESSION`, and they are these and no others (§7.1).
#    The handshake is not inside: §1 says that «the order of the five steps
#    allows no permutations», and not that after the fifth everything is allowed.
AFTER_SESSION = {"VIEW", "LAYOUT", "CURSOR_SHAPE", "FIT_CANVAS",
                 "REQUEST_KEY", "CANVAS", "BENCH_MARK", "BENCH_OUTCOME",
                 # ⛔ §7.6: «only with the session **attached**.  Before ATTACCA
                 #    there is no session to terminate, and §3 makes no
                 #    discounts».  ⇒ it sits in here, and outside of here the
                 #    state machine already rejects it by itself.
                 "TERMINATE_SESSION"}


class State:
    """The handshake machine — RCP.md §1, §4, §4.4.

    ⛔ It had **three** holes in the same function (finding R7.10), and on the
       biggest one the project's two arbiters contradicted each other:

       1. `REJECTED` was not **recorded**, so after a refusal the machine
          still believed it was waiting for `ADMITTED`.  ⇒ `HELLO · HERE_I_AM ·
          CREDENTIALS · REJECTED · REJECTED · ADMITTED · ATTACH · SESSION`
          was declared **compliant**: a server that refuses the credentials,
          repeats it, then admits the user and opens the session;
       2. with the session open `admits` said yes to **any** name, so a
          second `CREDENTIALS` passed — and it is the violation that §4.4
          names in full and that B5 tests with `credenziali-due-volte`.  ⛔ The
          two arbiters gave opposite verdicts on the same rule;
       3. the comment said *«with the session open the order is no longer
          constrained»*, which `RCP.md` does not authorise — a comment that
          explains why a line is right is not a proof that it is.
    """

    def __init__(self):
        self.done_ones = []
        self.live = False
        self.rejected = False
        # ⛔ What the control channel says and what is needed to judge the
        #    VIDEO: the granted canvas (§4.5) and the negotiated codec (§4.3).
        #    ⚠ `None` is «I have not read it», and it is NOT a default value.
        self.canvas_size = None
        self.prev_canvas = None
        self.canvas_from = "SESSION (§4.5)"
        self.codec = None
        # ⭐⛔ THE COUNT OF THE REQUESTS IN FLIGHT — 16 Aug 2026, sub-phase 6.6.
        #
        #    §6.2 says it in a line that holds for both sides: *«the control
        #    channel is a single one, reliable and ordered (§4.2) ⇒ the n-th
        #    `TELA` answers the n-th `ADATTA_TELA`, and whoever drags a window
        #    sends two of them without the count getting lost»*.
        #    ⇒ Here the count is a QUEUE, not a counter: the offset of the
        #      unanswered request is needed to be able to accusations it.
        # ⛔ §4.5: the cap the client declares in `HELLO`, and that §4.5 ties
        #    to the GRANTED canvas — from `SESSION` and from `CANVAS`.
        self.max_size = None
        # ⛔ §8.1: whoever has already sent their own `FAREWELL` speaks no more.
        self.dismissed_from = set()
        self.in_flight = []           # [(nb, ass, rel, gauge)] the FIT_CANVAS
        self.canvases = 0             # how many CANVAS have answered
        self.last_consumed = None  # the FIT_CANVAS the last CANVAS closed
        self.last_from_client = None  # to tell «it answered VISTA»
        self.farewell = None         # (nb, ass) of the FAREWELL, if it has passed
        # ⭐⛔ WHAT TIME MAKES POSSIBLE — 21 Aug 2026, magic 0x03.
        self.instant = 0            # the `instant_ms` of the block being read
        self.clock_v = 1           # 1 = client, 2 = server (§11.1)
        self.canvas_adapted_ms = None   # when the last CANVAS(ADAPTED) passed
        self.adapted = []          # [(ass, (W,H), instant)] — needed by T4
        self.late = []             # [(nb, ass, dt)] the POINTER beyond the grace
        self.still_needed = None    # did the server speak AFTER a late POINTER?
        self.farewell_reason = None

    def asks_canvas(self, nb, ass, rel, gauge):
        self.in_flight.append((nb, ass, rel, gauge))

    def canvas_reply(self, nb, ass, rel):
        """⛔ T1 and T2: a `CANVAS` that answers nothing.

        The two sentences are different on purpose, because they send one to
        look at two different places: the **second answer** is a server that
        lost count (§6.2), the **spontaneous** `CANVAS` is a server that changed
        the canvas by itself — and it is the line that `RCP.md` §7.1 declares
        ⏳ **still to be written**, so the red has an extra value: it says the
        product has got where the specification has not got yet.
        """
        if self.in_flight:
            self.last_consumed = self.in_flight.pop(0)
            self.canvases += 1
            return
        # ── T2: there has already been a CANVAS that consumed a request, and
        #    since then the client has not sent any others.
        if self.last_consumed is not None:
            prior = self.last_consumed
            raise NotCompliant(
                "RCP.md §6.2",
                f"second CANVAS for a single FIT_CANVAS: the request of "
                f"block {prior[0]} (byte {prior[1]}) had already been "
                f"closed by a previous CANVAS, and §6.2 wants «the n-th "
                f"CANVAS to answer the n-th FIT_CANVAS».  ⛔ One CANVAS too many "
                f"shifts all the following answers by one, and the client "
                f"holds or throws away the frames against the wrong canvas",
                ass, rel)
        # ── T1: no request was ever made.
        after_view = (" ⚠ and it arrived right after a VIEW: §7.1 says that "
                      "«VIEW MUST NOT change the canvas», and «the only "
                      "message that changes the canvas is FIT_CANVAS»"
                      if self.last_from_client == "VIEW" else "")
        raise NotCompliant(
            "RCP.md §7.1",
            f"unsolicited CANVAS: no FIT_CANVAS is unanswered."
            f"{after_view}  ⛔ §6.2 gives the client a single way of accepting an "
            f"unexpected size — holding «as long as an FIT_CANVAS the "
            f"client sent remains» — and «if no FIT_CANVAS is "
            f"unanswered nothing is held»: this CANVAS makes a healthy "
            f"session close",
            ass, rel)

    def admits(self, label_name, which_way=None):
        """Can the message arrive now?  Returns None or the reason why not.

        ⛔⛔ AND SINCE 16 AUG 2026 IT ALSO LOOKS AT **WHO** SPEAKS AFTER THEIR OWN
            `FAREWELL` — §8.1, and the gap was found by refuting.

        The arbiter accused an **unanswered** `FIT_CANVAS` followed by a
        `FAREWELL` (T3) and at the same moment acquitted the sequence
        `FIT_CANVAS · FAREWELL · CANVAS`, that is it said at once that the answer
        **could no longer arrive** and that **it had arrived**.  ⚠ Two
        opposite verdicts on the same fact, and neither of them wrong alone.

        ⭐ The line that resolves it is §8.1: *«Whoever closes MUST send `FAREWELL`
           with a reason **before** closing the session»*.  ⇒ the `FAREWELL` is
        the **last** message from that side; whoever speaks after their own
        farewell has declared they are closing and has carried on.  ⚠ And it
        binds **only the side that sent it**: §4.2 says that the FIN closes the
        session, but a `FAREWELL` is not a FIN, and the other side still has its
        own to send.
        """
        if which_way is not None and which_way in self.dismissed_from:
            chi = "client" if which_way == CLIENT else "server"
            return (f"the {chi} has already sent its FAREWELL, and §8.1 wants it "
                    f"«before closing the session»: after that it sends "
                    f"nothing more, {label_name} included")
        # ⛔ After `REJECTED` the client has only one thing left it can say, and
        #    it is `FAREWELL` (§4.4).  Any other message — «and in particular
        #    a second `CREDENZIALI`» — is the violation that §4.4 forbids.
        if self.rejected:
            return None if label_name == "FAREWELL" else \
                f"after REJECTED the client has only FAREWELL left, {label_name} arrived"
        if label_name == "FAREWELL":
            return None  # ↔ at any moment
        if label_name == "REJECTED":
            return None if self.done_ones[-1:] == ["CREDENTIALS"] else \
                "REJECTED answers CREDENTIALS"
        if self.live:
            # ⛔ With the session open the order of the SESSION messages is free;
            #    that of the handshake ones is not: repeating them is a
            #    permutation of the five steps, which §1 forbids.
            if label_name in AFTER_SESSION:
                return None
            return f"{label_name} belongs to the handshake, already concluded"
        if label_name not in ORDER:
            return f"{label_name} is not part of the handshake"
        expected_val = ORDER[len(self.done_ones)] if len(self.done_ones) < len(ORDER) else None
        if label_name != expected_val:
            return f"expected {expected_val}, arrived {label_name}"
        return None

    def mark(self, label_name):
        if label_name == "REJECTED":
            self.rejected = True
            return
        if label_name in ORDER and not self.live:
            self.done_ones.append(label_name)
            if self.done_ones == ORDER:
                self.live = True


# ---------------------------------------------------------------------------
# ⛔ THE FINGERPRINT OF §11.1: WHAT CAN BE VERIFIED, AND WHAT CANNOT.
#
#    Thirty-two bytes per obscured interval travel in the format to tie what
#    the recorder declares it hid to what was there.  Here they were read into
#    a variable and deleted with `del` on the next line, and `hashlib` was
#    imported and never used (finding R7.11).
#
# ⛔ **But verifying it against the true bytes is impossible from this side, by
#    construction**: the true bytes are precisely those the format exists to
#    NOT let get this far.  The only one who can do it is whoever has them — the
#    recorder, with a bench of its own.  Saying so is part of an arbiter's
#    trade: a check that cannot be done must be declared, not simulated.
#
# ⭐ What can be verified, and from here on is verified, is that the
#    fingerprint is not one of the **fake fingerprints** a wrong recorder
#    produces by itself:
#      · thirty-two zeros — the field never filled;
#      · SHA-256 of the `0x2A` padding × count — it fingerprinted the PADDING
#        instead of the true bytes, that is it certified its own substitution;
#      · SHA-256 of the empty string — it fingerprinted a string it did not have.
#    ⚠ They are defects of the RECORDER, not of the wire: they exit with outcome 2.
FAKE = {
    b"\x00" * 32: "thirty-two zeros: the field was never filled",
    hashlib.sha256(b"").digest(): "SHA-256 of the empty string",
}


def check_fingerprint(nb, ini, here, fingerprint):
    reason_text = FAKE.get(fingerprint)
    if reason_text is None and fingerprint == hashlib.sha256(
            bytes([FILL]) * here).digest():
        reason_text = ("SHA-256 of the 0x2A PADDING: the recorder fingerprinted "
                  "what it put in, not what it took out")
    if reason_text:
        raise Malformed(
            f"block {nb}: the obscured interval [{ini},{ini + here}) carries "
            f"a fake fingerprint — {reason_text}")


# ---------------------------------------------------------------------------
def valid(fpath):
    with open(fpath, "rb") as f:
        d = f.read()

    # ⛔ THE OLD FORMAT IS REJECTED, AND WITH ITS OWN SENTENCE — §11.1.
    #
    #    «It is not of the format» and «it is of another version» are two facts
    #    with two different cures: the first sends one looking for whoever broke
    #    the file, the second to regenerate it.  ⛔ And misreading it is not an
    #    option: the old block is 16 bytes, this reader wants 17.
    if len(d) >= 8 and d[:8] == MAGIC_V1:
        raise Malformed(
            "it is a recording in the OLD format, «RCPREG 0x00 0x01»: the "
            "block carries neither `fine` nor `instant_ms`, and is 16 bytes "
            "instead of 21.  ⛔ It is not misread — §11.1, 12 Aug "
            "2026 — and it is not a broken file: it is REGENERATED with "
            "`01-b4-registrazioni.py`")
    if len(d) >= 8 and d[:8] == MAGIC_V2:
        raise Malformed(
            "it is a recording in the format of 12 August, «RCPREG 0x00 "
            "0x02»: the block does not carry `instant_ms` and is 17 bytes instead "
            "of 21, and the header does not declare WHOSE the clock is.  ⛔ "
            "§11.1: «an old validator must REJECT the new format, "
            "not misread it», and it holds in both directions — misread, "
            "every block would slip by four bytes and out would come "
            "a JUDGEMENT on bytes nobody wrote.  It is REGENERATED with "
            "`01-b4-registrazioni.py`")
    if len(d) < 16 or d[:8] != MAGIC:
        raise Malformed("it does not start with the magic of RCP.md §11.1")
    how_many, clock_v, r1, r2, r3 = struct.unpack("!IBBBB", d[8:16])
    if (r1, r2, r3) != (0, 0, 0):
        raise Malformed(
            f"the three reserved bytes are {r1},{r2},{r3}: §11.1 wants them 0")
    # ⛔ And «whose clock it is» is NOT guessed: without that byte the
    #    conclusion «in one direction only» cannot even be formulated, and an
    #    arbiter that assumed «it must be the client's» would be acquitting a
    #    server on the basis of its own hypothesis.
    if clock_v not in CLOCK:
        raise Malformed(
            f"the `clock_v` field is {clock_v}: §11.1 defines two — "
            f"1 = the times are the client's, 2 = the server's.  ⛔ Without it, the rule "
            f"of the grace second (§7.1) is not judgeable at all")

    print(f"== the wire validator — {fpath}")
    print(f"   declared blocks: {how_many}   bytes: {len(d)}   "
          f"clock: {CLOCK[clock_v]}")

    p = 16
    state = State()
    # ⛔ THE DENOMINATORS OF THE VERDICT, and since 12 Aug 2026 they are SIX: the
    #    things one may NOT have looked at grew with the video channel.
    #    «No violation» without them was true even on a file of zero
    #    blocks (finding R7.4).
    seen_items = 0        # blocks read
    control_blocks = 0  # blocks on channel 0x00
    messages = 0     # control messages read
    judged = 0    # ... of which with the body actually judged
    di_video = 0     # blocks on channel 0x03
    video_streams = 0  # ... grouped by stream: one stream, one frame
    # ⛔ The two rules of 12 August that speak of STREAMS and not of bytes: they
    #    are decided here, while leafing through, because a single-frame judge
    #    knows neither which stream it arrived on nor what had already passed.
    session_seen = False          # P1 — §2.5
    control_stream = set()     # P3 — §2.5
    check_closed_by_server = None   # T3 — §7.1
    check_closed_by_client = None   # T3 — §4.2, and the contradiction
    flows, order = {}, []
    last_instant = 0
    # ⭐ The two lists that time makes possible — see at the bottom.
    state.clock_v = clock_v
    for nb in range(how_many):
        if p + BLOCK_BYTES > len(d):
            raise Malformed(f"block {nb} starts beyond the end of the file")
        which_way, channel, fine, instant, stream, lung, nosc = struct.unpack(
            BLOCK, d[p:p + BLOCK_BYTES])
        p += BLOCK_BYTES
        # ⛔ Time does not go backwards: §11.1 says «milliseconds from the FIRST
        #    block», and the blocks are in wire order.  An instant that goes
        #    down means a NON-monotonic clock (`time.time()` instead of
        #    `time.monotonic()`), and on such a file no rule with time inside
        #    it can be judged — it is said, and one does not go on guessing.
        if instant < last_instant:
            raise Malformed(
                f"block {nb}: `instant_ms` = {instant}, and the block before "
                f"said {last_instant}.  ⛔ §11.1 wants a "
                f"MONOTONIC clock: here it went back by "
                f"{last_instant - instant} ms")
        last_instant = instant
        state.instant = instant
        if fine not in FINE:
            raise Malformed(
                f"block {nb}: `fine` is {fine}, and §11.1 defines three — "
                f"0 continues, 1 FIN, 2 RESET_STREAM")
        obscured = []
        for _ in range(nosc):
            if p + 40 > len(d):
                raise Malformed(f"block {nb}: truncated obscured interval")
            ini, here = struct.unpack("!II", d[p:p + 8])
            fingerprint = d[p + 8:p + 40]
            p += 40
            if ini + here > lung:
                raise Malformed(
                    f"block {nb}: obscured interval [{ini},{ini + here}) "
                    f"outside the payload of {lung} bytes")
            for o, q in obscured:
                if not (ini + here <= o or ini >= o + q):
                    raise Malformed(f"block {nb}: two obscured intervals overlap")
            obscured.append((ini, here))
            check_fingerprint(nb, ini, here, fingerprint)
        if p + lung > len(d):
            raise Malformed(f"block {nb}: the payload is truncated")
        load, base = d[p:p + lung], p
        p += lung
        seen_items += 1

        if which_way not in (CLIENT, SERVER):
            raise Malformed(f"block {nb}: direction {which_way}, expected 1 or 2")
        # ⛔ The padding of the obscured intervals is 0x2A, not zero: it is the
        #    format that requires it, and an interval of zeros «by chance»
        #    legitimate would be an obscuring that cannot be seen.
        for o, q in obscured:
            if any(b != FILL for b in load[o:o + q]):
                raise Malformed(
                    f"block {nb}: an obscured interval is not made of 0x2A")

        chi = "client" if which_way == CLIENT else "server"
        if channel not in CHANNELS:
            raise NotCompliant("RCP.md §2.5",
                              f"the high byte of the type is {channel:#04x}: "
                              "outside the five channels",
                              base, 0)
        if channel == VIDEO:
            # ⛔ The video blocks are COLLECTED and judged afterwards, per stream:
            #    one stream, one frame (§6.2), and blocks of different streams
            #    interleave.  ⚠ And the **moment** the stream starts is kept —
            #    before or after `SESSION` — because it is P1, and after the
            #    leafing through that information is lost.
            di_video += 1
            if stream not in flows:
                flows[stream] = {"pieces": [], "base": base,
                                  # ⭐ when the stream opens: it is half of T4
                                  "instant": instant,
                                  # ⛔ HOW MANY canvas changes had passed when
                                  #    this stream opened.  It is needed NOT to
                                  #    replay the same change for every
                                  #    frame that follows — see the box
                                  #    in the judgement loop.
                                  "tela_n": len(state.adapted),
                                  "dopo_sessione": session_seen,
                                  "sul_controllo": stream in control_stream,
                                  # ⛔ the canvas IN FORCE when the stream
                                  #    opens, not the end-of-file one: judging
                                  #    a frame with a canvas granted after
                                  #    it would be reading the wire
                                  #    backwards.
                                  "canvas_size": state.canvas_size,
                                  "canvas_from": state.canvas_from,
                                  # ⭐⛔ THE REQUESTS IN FLIGHT WHEN THE STREAM
                                  #     OPENS — §6.2, and without them the arbiter
                                  #     killed healthy sessions.
                                  #
                                  #  §6.2: *«a frame at the NEW size may
                                  #  arrive BEFORE the `TELA` that grants it …
                                  #  the client MUST NOT close: it holds the
                                  #  frame»*, and the condition is *«as long
                                  #  as an `ADATTA_TELA` the client
                                  #  sent remains»*.
                                  #  ⛔ `02-filo-fotogramma.py` has
                                  #  `fit_sent()` and `fit_in_flight`
                                  #  written on purpose for this — and it names
                                  #  in full *«no reader that imports
                                  #  this file (01-b4-validatore.py …)»* —
                                  #  but B4 never told it: it built the
                                  #  context and declared no
                                  #  request in flight.  ⇒ The grace of §6.2
                                  #  was written, imported and **unreachable**,
                                  #  and every frame that arrived before its
                                  #  `CANVAS` was PROTOCOL_ERROR: the scene that
                                  #  §6.2 describes as the one in which «nobody
                                  #  made a mistake».
                                  "in_flight": [m for _, _, _, m in state.in_flight
                                              if m],
                                  "prev_canvas": state.prev_canvas}
                order.append(stream)
            flows[stream]["pieces"].append((nb, which_way, load, fine, obscured))
            continue
        if channel != CHECK:
            # ⛔⛔ THE DECLARED `channel` IS COMPARED WITH THE BYTES, and until 16
            #     Aug 2026 it was taken at its word.
            #
            #     §11.1 does not describe that field: it **defines** it — *«canale:
            #     the high byte of `tipo` (§2.5)»*.  ⇒ A block that carries a
            #     control message while declaring itself «clipboard» is not a
            #     clipboard block: it is wire that **vanishes from the judgement**
            #     with a file valid for every other line of §11.1.  ⚠ It is the
            #     same shape as `11-quanti-sotto-dichiarato`, where the outcome
            #     is **2**.
            #
            # ⭐ Found by refuting: the same bytes as the recording of the
            #    unsolicited `CANVAS`, with the `channel` written `0x02`, came out
            #    ⭐ compliant.  Two bytes were enough to make a violation
            #    invisible.
            if lung >= 2:
                alto = struct.unpack("!H", load[:2])[0] >> 8
                if alto != channel:
                    raise Malformed(
                        f"block {nb}: declares `channel = {channel:#04x}` "
                        f"({CHANNELS[channel]}) but the payload starts with a type "
                        f"whose high byte is {alto:#04x}.  ⛔ §11.1 defines "
                        f"`channel` AS «the high byte of kind»: here the two do "
                        f"not match, and a block declared as a channel the "
                        f"validator does not judge is wire that vanishes from the "
                        f"judgement")
            # ═══════════════════════════════════════════════════════════
            # ⭐⛔ THE GRACE SECOND OF §7.1 — the `[?]` that the
            #     `instant_ms` field exists to close, and **in one direction only**.
            #
            # §7.1: after a `CANVAS(ADAPTED)` the server MUST accept **for one
            # second** the coordinates valid on the PREVIOUS canvas, saturate
            # them and write it in the log; ⛔ once that second has passed they
            # are `PROTOCOL_ERROR`.
            #
            # ⛔ And the only arbitrable half is that of LENIENCY: a server that
            #    keeps accepting the old coordinates forever.  The other — a
            #    server that is too strict — stays out, because the client's
            #    interval is SHORTER than the server's and a `<= 1000` here
            #    could be a `> 1000` there.
            # ═══════════════════════════════════════════════════════════
            if (channel == INPUT and which_way == CLIENT and lung >= 26
                    and state.canvas_size is not None and state.prev_canvas is not None
                    and state.canvas_adapted_ms is not None):
                type_i = struct.unpack("!H", load[:2])[0]
                if type_i == T_POINTER:
                    x, y = struct.unpack("!II", load[18:26])
                    outside = x >= state.canvas_size[0] or y >= state.canvas_size[1]
                    inside_before = (x < state.prev_canvas[0]
                                    and y < state.prev_canvas[1])
                    dt = instant - state.canvas_adapted_ms
                    if outside and inside_before:
                        if state.clock_v == CLIENT and dt > GRACE_MS:
                            state.late.append((nb, base, dt, x, y))
                            state.still_needed = False
                        else:
                            # ⛔ NOT JUDGEABLE, and it is SAID.  An arbiter that
                            #    keeps quiet about what it does not know is an
                            #    arbiter that acquits.
                            print(f"   block {nb}: ⚠ POINTER at ({x},{y}) "
                                  f"{dt} ms after the CANVAS(ADAPTED), inside the "
                                  f"previous canvas and outside the one in "
                                  f"force — ⛔ the grace second of §7.1 "
                                  f"is NOT judgeable from this "
                                  f"recording: "
                                  + (f"the times are the "
                                     f"{CLOCK[state.clock_v]}'s and "
                                     f"{dt} <= {GRACE_MS} ms, and the server's "
                                     f"true interval is LONGER than this"
                                     if state.clock_v == CLIENT else
                                     f"the clock is the server's and this "
                                     f"validator concludes only from the "
                                     f"client's times"))
            print(f"   block {nb}: channel {CHANNELS[channel]} from the {chi}, "
                  f"{lung} bytes — not judged by this validator")
            continue
        control_blocks += 1
        control_stream.add(stream)
        # ⛔ «The server kept serving» is measured HERE: a control block from
        #    the server after a `POINTER` beyond the grace.  ⚠ A `FAREWELL`
        #    does not count — that is the refusal — and it is removed further
        #    down, when the type is read.
        if state.late and which_way == SERVER:
            state.still_needed = (nb, base)

        # The control channel lives only on stream 0 of the session (§2.5).
        le = Reader(load, base, obscured)
        while le.stays():
            msg_start = le.i
            kind = le.u16("the type")
            lung_msg = le.u32("the length")
            if lung_msg > MAX_MESSAGE_LEN:
                raise NotCompliant("RCP.md §6.1",
                                  f"length {lung_msg} beyond the 1 MiB cap",
                                  base + msg_start + 2, msg_start + 2)
            if le.stays() < lung_msg:
                raise NotCompliant(
                    "RCP.md §6.1",
                    f"declares {lung_msg} bytes of body and there are {le.stays()}",
                    base + msg_start + 2, msg_start + 2)
            if (kind >> 8) != 0x00:
                raise NotCompliant("RCP.md §2.5",
                                  f"type {kind:#06x}: high byte {kind >> 8:#04x}, "
                                  "the control channel wants 0x00",
                                  base + msg_start, msg_start)
            if kind not in TYPES:
                raise NotCompliant("RCP.md §7.1", f"unknown type {kind:#06x}",
                                  base + msg_start, msg_start)
            label_name, expected_direction = TYPES[kind]
            if expected_direction is not None and expected_direction != which_way:
                raise NotCompliant("RCP.md §7.1",
                                  f"{label_name} cannot come from the {chi}",
                                  base + msg_start, msg_start)
            reason_text = state.admits(label_name, which_way)
            if reason_text:
                raise NotCompliant("RCP.md §4 (the handshake order)",
                                  f"{label_name} in the wrong state: {reason_text}",
                                  base + msg_start, msg_start)

            # ⭐⛔ THE CANVAS COUNT — and it is done BEFORE reading the body.
            #
            #    T1 and T2 do not depend on a single byte of the body: a `CANVAS`
            #    that answers nothing is wrong **whatever it carries
            #    inside**, and the byte to show is the first of the message.
            #    ⚠ Reading the body first would give precedence to a lesser
            #      defect — a reason outside the list — and would send the
            #      diagnosis to look at the field instead of the sequence.
            if label_name == "FIT_CANVAS":
                gauge = (struct.unpack("!II", load[le.i:le.i + 8])
                          if lung_msg >= 8 else None)
                state.asks_canvas(nb, base + msg_start, msg_start, gauge)
            elif label_name == "CANVAS":
                state.canvas_reply(nb, base + msg_start, msg_start)

            below = Reader(load[le.i:le.i + lung_msg], base + le.i,
                            [(o - le.i, q) for o, q in obscured
                             if o + q > le.i and o < le.i + lung_msg])
            assessed = body_el(kind, label_name, below, which_way, state)
            messages += 1
            judged += int(bool(assessed))
            print(f"   block {nb}: {label_name:<14s} from {chi:<6s} {lung_msg:>5} bytes"
                  + ("" if assessed else "   (body not judged)"))
            state.mark(label_name)
            # ⛔ P1 — §2.5: from here on the video is lawful, and before it is not.
            if label_name == "SESSION" and which_way == SERVER:
                session_seen = True
            if which_way == CLIENT:
                state.last_from_client = label_name
            if label_name == "FAREWELL":
                state.farewell = (nb, base + msg_start)
                state.dismissed_from.add(which_way)   # §8.1: from here on it is silent
                # ⛔ A FAREWELL is NOT «the server kept serving»: it is the
                #    refusal.  ⇒ the mark set above is removed, or the server
                #    would be accused precisely for having done the right thing
                #    — a red to the opposite defendant.
                if which_way == SERVER and state.late:
                    state.still_needed = False
                    state.farewell_reason = (load[le.i] if lung_msg >= 1
                                            else None)
            le.i += lung_msg
        # ⛔ HOW THE CONTROL CHANNEL WAS CLOSED, AND FROM WHICH SIDE.
        #
        #    It is needed by T3 and by nothing else: an unanswered `FIT_CANVAS`
        #    is a violation **only if the answer can no longer arrive**.  If the
        #    stream continues, the file simply ended earlier — and declaring it
        #    instead of accusing is the same choice §6.2 imposes on the video
        #    with `fine = 0`.
        if fine in (FIN, RESET):
            if which_way == SERVER:
                check_closed_by_server = (nb, fine)
            else:
                # ⛔⛔ THE **CLIENT'S** FIN DOES NOT ACCUSE THE SERVER, AND NOT
                #     because it is a lesser end: because there `RCP.md`
                #     **contradicts itself**, and an arbiter that silently chose
                #     one of the two readings would give a verdict on the
                #     document passing it off as a verdict on the wire.
                #
                #  · §7.1: *«To every `ADATTA_TELA` the server MUST answer with
                #    a `TELA`, successful or not»*;
                #  · §4.2: *«a FIN on that stream, **from either of the two
                #    parties**, closes the session.  Whoever receives it … MUST
                #    NOT keep sending on any channel, **including the control
                #    one**»*.
                #
                #  ⇒ A client that sends `FIT_CANVAS` and then closes puts the
                #    server between two `MUST`s that exclude each other:
                #    answering violates §4.2, keeping quiet violates §7.1.
                #    ⛔ **It is not a lab case**: it is the user who resizes the
                #    window and closes the tab in the same gesture.
                #  ⭐ `RCP.md` has already resolved the twin case for the
                #     `FAREWELL` — §8.1, the box of 11 August, *«whoever receives
                #     a FIN is not "whoever closes"»* — and **has not done it for
                #     the `CANVAS`**.  It is the missing line, and this verdict
                #     names it instead of filling it in.
                check_closed_by_client = (nb, fine)

    # ⛔ THE CHECK THAT WAS THERE COULD NOT FAIL, AND THE ONE NEEDED WAS MISSING.
    #
    #    Here there was `if seen_items != how_many: raise Malformed(...)`.  `seen_items` is
    #    incremented once per iteration of a `for nb in range(how_many)` that
    #    either completes or raises: it was **dead code**, standing in place of
    #    the check that covers the two real ways of making bytes vanish from
    #    the judgement (finding R7.4):
    #      · `quanti_blocchi` under-declared — 4 is written where they are 6 and
    #        the two offending blocks are never read;
    #      · a garbage tail after the last declared block.
    #    In both cases the file came out «⭐ compliant».
    if p != len(d):
        raise Malformed(
            f"{len(d) - p} bytes remain after the {how_many} declared blocks: "
            f"either `quanti_blocchi` is under-declared — and then there is wire "
            f"that nobody judged — or there is a tail that is not of the format")

    # =======================================================================
    # ⭐⛔ T3 — THE `FIT_CANVAS` THAT NO `CANVAS` EVER CLOSED (§7.1)
    #
    #    *«To every `ADATTA_TELA` the server MUST answer with a `TELA`,
    #    successful or not.  A silence leaves the client waiting forever for
    #    an answer that will not come, and the symptom is "the application
    #    froze"»*.
    #
    # ⛔⛔ AND HERE LIES THE MOST DELICATE DECISION OF THE WHOLE SUB-PHASE,
    #     because getting it wrong produces a **perpetual false red**: a
    #     recording that ends while the session is still alive is not a server
    #     keeping quiet — it is a file that ends.  ⚠ Every trace of
    #     `01-b3-cliente.py` is of that kind: the client detaches by itself
    #     when `--stays` expires.
    #
    # ⭐ The distinction is read in the bytes, and the `fine` field of §11.1
    #    carries it — the same field that entered on 12 August to tell an
    #    abandoned frame from a truncated one.  The answer **can no longer
    #    arrive** when:
    #      · the control channel has closed **from the server side** (FIN or
    #        RESET_STREAM on a server block), or
    #      · a `FAREWELL` has passed, which §8 makes end the session.
    #    Outside these two cases completeness **is not judged**, and it is
    #    declared — as §6.2 imposes on the video with `fine = 0`.
    #
    # ⚠⛔ **And the FAREWELL is a reading, not a line of `RCP.md`.**  §7.1 says
    #     «MUST answer» without exceptions, and the server has `CANVAS(RIFIUTATA,
    #     NOT_NOW)` available even while closing: so taking leave without
    #     answering **is accused**.  The opposite reading — «the farewell also
    #     closes the wait» — is defensible, and that is why the verdict names
    #     it: if it is the right one, `RCP.md` §7.1 is fixed with one line, not
    #     this file.
    if state.in_flight:
        nb0, ass0, rel0, gauge = state.in_flight[0]
        desc = (f"{gauge[0]}x{gauge[1]}" if gauge else "size not read")
        if check_closed_by_server is not None or state.farewell is not None:
            how_to = ("the control channel was closed from the server side "
                      f"({FINE[check_closed_by_server[1]]} on block "
                      f"{check_closed_by_server[0]})"
                      if check_closed_by_server is not None else
                      f"a FAREWELL passed (block {state.farewell[0]}, byte "
                      f"{state.farewell[1]}) — ⚠ and the server had "
                      f"CANVAS(RIFIUTATA, NOT_NOW) available even while "
                      f"closing")
            raise NotCompliant(
                "RCP.md §7.1",
                f"FIT_CANVAS({desc}) of block {nb0} without any CANVAS "
                f"answering it, and {how_to}: the answer can no longer arrive.  "
                f"⛔ «A silence leaves the client waiting forever, and "
                f"the symptom is \"the application froze\"».  "
                f"⚠ {len(state.in_flight)} are still in flight",
                ass0, rel0)
        if check_closed_by_client is not None:
            print(f"   ⚠⛔ {len(state.in_flight)} unanswered FIT_CANVAS (the "
                  f"first at byte {ass0}), and the channel was closed by the "
                  f"**CLIENT** (block {check_closed_by_client[0]}).")
            print("      ⛔ HERE RCP.md CONTRADICTS ITSELF, and this arbiter does NOT "
                  "choose:")
            print("        · §7.1 — «to every FIT_CANVAS the server MUST "
                  "answer, successful or not»;")
            print("        · §4.2 — «a FIN from either of the two parties "
                  "closes the session;")
            print("          whoever receives it MUST NOT keep sending, "
                  "including on control».")
            print("      ⇒ answering violates §4.2, keeping quiet violates §7.1.  ⭐ §8.1 has "
                  "already resolved")
            print("        the twin case for the FAREWELL and has not done it for "
                  "the CANVAS: it is a")
            print("        line missing from RCP.md, not a defect of the wire.")
        else:
            print(f"   ⚠ {len(state.in_flight)} unanswered FIT_CANVAS, the "
                  f"first at byte {ass0} — ⛔ but the control channel did NOT "
                  f"close and no FAREWELL passed: the recording "
                  f"ends while the session is alive, and §7.1 is NOT judged "
                  f"on this trace")

    # =======================================================================
    # ⭐⛔ THE VIDEO CHANNEL — the six lines of 12 Aug 2026
    #
    #    It is judged AFTER the leafing through because two of the six speak of
    #    **what had already passed** (P1) and of **on which stream** (P3), and a
    #    single-frame judge cannot know that.
    # =======================================================================
    if flows:
        f24, why_no = frame_judge()
        if f24 is None:
            # ⛔ E8: «I do not have the tool» is NOT «it is fine».  A `continue`
            #    here would put line 521 back on its feet, with the difference
            #    that this time the file declares it judges the video.
            raise CouldNotLook(
                f"there are {len(flows)} video streams to judge and the judge "
                f"is not there: {why_no}")
        # ⛔ The canvas and the codec are NOT guessed: they are taken from
        #    `SESSION` and from `HERE_I_AM`, that is from the wire itself.  An
        #    arbiter that compared with its own defaults would be judging
        #    itself — and it is case `17-video-misura-diversa` that keeps it
        #    honest.
        #
        # ⭐ AND THE CANVAS IS THE ONE **IN FORCE**, NOT THAT OF `SESSION` —
        #    §6.2, **corrected on 12 Aug 2026** a few hours after being
        #    written, because propagating it this far showed that it killed a
        #    healthy session: after a `CANVAS(ADAPTED, 1280, 720)` (§7.1) the
        #    server captures at the new size, and a client that still compared
        #    with `SESSION` would close — the scene that §7.1 protects
        #    with its exception 4.  ⇒ `state.canvas_size` is updated on `SESSION`
        #    **and** on `CANVAS`, and every video stream is judged with the canvas
        #    that was in force when it opened.
        ctx = f24.Context(canvas_size=state.canvas_size or (1920, 1080),
                           negotiated_codec=state.codec or 1,
                           session_open=True)
        # ⛔⛔⛔ THE CANVAS CHANGE IS REPLAYED ONCE ONLY — 21 Aug 2026,
        #      and it was found by the first run with VIDEO in the trace.
        #
        #  Until this morning the branch below reset the context to the
        #  PREVIOUS canvas and called `fit_canvas()` again **for every stream**
        #  opened while the canvas in force came from a `CANVAS(ADAPTED)`.  ⇒ The
        #  key-frame debt of §5.2 reopened at every frame, and the **second**
        #  frame after a resize — a perfectly legal delta — was accused as
        #  *«the first at the new size is a DELTA»*.
        #
        #  `[M]` 21 Aug 2026, port 7721, real product: `CANVAS(ADAPTED,
        #  1600x900)` · stream 19 **key** 1600x900 (the debt is paid) ·
        #  stream 23 delta 1600x900 ⇒ ⛔ NOT COMPLIANT.  **The server had done
        #  exactly what §5.2 asks.**
        #
        # ⚠ And nobody could notice: no recording in the repository carried
        #   TWO video streams after the same `CANVAS`, and the test client did
        #   not record the video channel at all.  ⛔ The arbiter would have
        #   declared **every real session** non-compliant as soon as the trace
        #   contained video — that is at the first useful run.
        last_canvas_n = None
        for sid in order:
            fl = flows[sid]
            video_streams += 1
            # ⛔ P5 — the canvas IN FORCE when THIS stream opened.
            if fl["canvas_size"] is not None:
                if (fl["canvas_from"].startswith("CANVAS")
                        and fl["tela_n"] != last_canvas_n):
                    # ⛔⛔ ONE STARTS FROM THE **PREVIOUS** CANVAS AND THEN JUMPS,
                    #     and it is not a roundabout way of saying it:
                    #     `fit_canvas` has an early return when the size does
                    #     not change — written on purpose, because §7.1 makes
                    #     `CANVAS` answer even whoever asks for the size that is
                    #     already there.
                    #
                    #  ⚠ B4 built the context with the **end-of-file** canvas
                    #    and then called `fit_canvas` on it with the **same**
                    #    size: for the judge nothing had happened.  ⇒
                    #    `recent_canvases` stayed empty, `queue_to_drain()`
                    #    false, and the grace of **D14** — the frames at the
                    #    old size still in flight — **never opened**.
                    #  ⛔ A canvas change the arbiter did not see as a
                    #     change: the sixth exception of §3 was imported,
                    #     documented and dead.
                    if fl["prev_canvas"] is not None:
                        ctx.canvas_width, ctx.canvas_height = fl["prev_canvas"]
                    ctx.fit_canvas(*fl["canvas_size"], previous=fl["prev_canvas"])
                elif not fl["canvas_from"].startswith("CANVAS"):
                    ctx.canvas_width, ctx.canvas_height = fl["canvas_size"]
                # ⚠ and if it is a CANVAS already replayed NOTHING is touched: the
                #   context is already at the new size, and the key-frame debt
                #   was already paid by the previous stream.
                last_canvas_n = fl["tela_n"]
            # ⛔ And the requests in flight, which are the other half of §6.2: the
            #    frame at the new size that arrived BEFORE its `CANVAS` is held,
            #    and holding it «is not a number: it is a condition».
            ctx.fit_in_flight = list(fl["in_flight"])
            b0 = fl["pieces"][0]
            base0 = fl["base"]

            # ── P3 — §2.5: a `0x03` on the control channel
            if fl["sul_controllo"]:
                raise NotCompliant(
                    "RCP.md §2.5",
                    f"stream {sid}: a frame on the stream of the CONTROL "
                    f"CHANNEL.  §2.5 wants the video «only on a unidirectional "
                    f"stream opened by the server»", base0, 0)

            # ── P1 — §2.5: no video stream before `SESSION`
            if not fl["dopo_sessione"]:
                raise NotCompliant(
                    "RCP.md §2.5",
                    f"stream {sid}: a video stream opens BEFORE "
                    f"`SESSION` — the client receives a frame of which it "
                    f"knows neither the size nor the codec.  It is invariant I3 "
                    f"on the wire", base0, 0)

            # ── and the direction, §2.5: the video goes from the server to the client
            if any(v != SERVER for _, v, _, _, _ in fl["pieces"]):
                raise NotCompliant(
                    "RCP.md §2.5",
                    f"stream {sid}: a frame FROM THE CLIENT — the video goes from "
                    f"the server to the client", base0, 0)
            if any(osc for _, _, _, _, osc in fl["pieces"]):
                raise Malformed(
                    f"stream {sid}: an obscured interval on a VIDEO block. "
                    f"§11.1 exists for the password (§4.4); a "
                    f"frame has nothing to obscure, and the validator "
                    f"cannot judge what it is not allowed to read")

            closure = fl["pieces"][-1][3]
            for nbx, _, _, fx, _ in fl["pieces"][:-1]:
                if fx != CONTINUE:
                    raise Malformed(
                        f"block {nbx}: declares `fine = {fx}` ({FINE[fx]}) but "
                        f"other blocks arrive on stream {sid} afterwards.  "
                        f"⛔ A stream closes only once")

            g = f24.Judge(ctx, dove="uni")
            # ⛔ THE RESET WINS OVER THE HEADER — §6.2, finding R1.7: the bytes
            #    of a truncated header can be anything, and reading them would
            #    give `PROTOCOL_ERROR` on a legal abandonment.
            if closure == RESET:
                v = g.ends("reset")
            else:
                for _, _, car, _, _ in fl["pieces"]:
                    g.arrive(car)
                    if g.verdict is not None:
                        break
                if g.verdict is not None:
                    v = g.verdict
                elif closure == CONTINUE:
                    # ⛔ `fine = 0` on the last block: the stream does not close
                    #    inside the file, so COMPLETENESS is not judged —
                    #    and it is declared instead of being taken as good.
                    print(f"   stream {sid}: {g.byte_data} bytes of data and "
                          f"`fine = 0` on the last block — ⛔ completeness "
                          f"is NOT judged (§6.2)")
                    continue
                else:
                    v = g.ends("fin")
            if v.outcome == f24.PROTOCOL_ERROR:
                rel = v.deviation if v.deviation is not None else 0
                raise NotCompliant(v.rule_v, f"stream {sid}: {v.says}",
                                  base0 + rel, rel)
            print(f"   stream {sid}: {v.outcome:<18s} {v.says}")

    # =======================================================================
    # ⭐⛔ THE VERDICT ON THE GRACE SECOND — §7.1, and in ONE DIRECTION ONLY
    # =======================================================================
    if state.late:
        nb_t, ass_t, dt_t, x_t, y_t = state.late[0]
        if state.still_needed:
            nb_s, ass_s = state.still_needed
            raise NotCompliant(
                "RCP.md §7.1",
                f"block {nb_t} carries a POINTER at ({x_t},{y_t}) — valid "
                f"on the PREVIOUS canvas, outside the one in force — "
                f"{dt_t} ms after the CANVAS(ADAPTED), that is beyond the grace "
                f"second; and at block {nb_s} the server is still serving the "
                f"session instead of having closed it.  ⛔ §7.1: «once that "
                f"second has passed, they are PROTOCOL_ERROR».  ⚠ And the {dt_t} ms are "
                f"measured on the CLIENT's clock: the SERVER's interval was "
                f"longer than this, not shorter — that is why the "
                f"conclusion holds",
                ass_t, 0)
        if state.farewell is not None and state.still_needed is False:
            m = state.farewell_reason
            print(f"   ⭐ §7.1: the POINTER of block {nb_t} was {dt_t} ms "
                  f"after the CANVAS(ADAPTED) — beyond the second — and the server "
                  f"SENT A FAREWELL"
                  + (f" with reason {m:#04x}" if m is not None else "")
                  + ".  It is the right road.")
        elif state.still_needed is False:
            print(f"   ⚠ §7.1: the POINTER of block {nb_t} was {dt_t} ms "
                  f"after the CANVAS(ADAPTED), beyond the second — ⛔ but after "
                  f"it the server says nothing more and the recording "
                  f"ends: whether it closed or kept quiet is NOT judged")

    # =======================================================================
    # ⭐⛔ T4 — «COMPLIANT IS NOT WORKS», and now the arbiter has a grip on it
    #
    # `fasi/06-la-tela-e-la-vista.md` §7.2: *«a server that answered
    # `TELA(ADATTATA)` without touching the stage would pass all five
    # rounds»*.  ⭐ Not any more, if the recording also carries the VIDEO: §5.2
    # wants the first frame at the new size to be a KEY frame, and §6.2 ties the
    # 28 bytes to the canvas in force.  ⇒ If after a `CANVAS(ADAPTED, WxH)` frames
    # pass for more than `T4_CAP_MS` and **none** declares `WxH`, the
    # server answered without touching the stage.
    #
    # ⛔ AND NOT «the first»: §6.2 explicitly allows the frame **already in
    #    flight** at the old size (`01-b4-registrazioni.py` case 44, the scene
    #    in which «nobody made a mistake»).  ⇒ a cap in TIME is needed, not a
    #    count — and it is the reason T4 could not be written before
    #    `instant_ms`.
    # =======================================================================
    video_measures = []
    for sid in order:
        fl = flows[sid]
        car0 = fl["pieces"][0][2]
        if len(car0) >= 12:
            video_measures.append((fl["instant"],
                                 struct.unpack("!II", car0[4:12]), fl["base"]))
    for ass_a, size_h, ist_a in state.adapted:
        after = [m for m in video_measures if m[0] >= ist_a]
        if any(m[1] == size_h for m in after):
            continue
        if not after:
            print(f"   ⚠ T4 §7.1: CANVAS(ADAPTED, {size_h[0]}x{size_h[1]}) "
                  f"at byte {ass_a} — ⛔ after it the recording carries "
                  f"NO frame: «was the stage touched?» is NOT "
                  f"judged on this trace")
            continue
        win = max(m[0] for m in after) - ist_a
        if win > T4_CAP_MS:
            views = ", ".join(f"{m[1][0]}x{m[1][1]}" for m in after[:5])
            raise NotCompliant(
                "RCP.md §7.1",
                f"T4 — CANVAS(ADAPTED, {size_h[0]}x{size_h[1]}) and then "
                f"{len(after)} frames in {win} ms, NONE at the granted "
                f"size (seen: {views}).  ⛔ §5.2 wants a KEY frame at the "
                f"new size and §6.2 ties the 28 bytes to the canvas in force: a "
                f"server that answers ADAPTED and does not touch the stage is "
                f"compliant on every other rule, and this is the only one that "
                f"sees it.  ⚠ The {T4_CAP_MS} ms cap is a READING of §7.1 "
                f"(the FIT_CANVAS deadline), not a line of RCP.md",
                ass_a, 0)
        print(f"   ⚠ T4 §7.1: CANVAS(ADAPTED, {size_h[0]}x{size_h[1]}) and "
              f"{len(after)} frames in {win} ms, none at the granted "
              f"size — ⛔ below the {T4_CAP_MS} ms cap: it is NOT "
              f"judged, the recording is too short")

    # ⛔ AND «COMPLIANT» IS SAID WITH THE DENOMINATOR, OR IT IS NOT SAID.
    print(f"\n   looked at: {seen_items} blocks, of which {control_blocks} on the "
          f"control channel and {di_video} on the video channel · {messages} messages "
          f"read, {judged} with the body judged · {video_streams} video "
          f"streams")
    # ⛔ AND THE DENOMINATOR OF THE CANVAS, since 16 Aug 2026.  «Compliant» on a
    #    trace with **zero** FIT_CANVAS says nothing about the seven canvas
    #    rules: it respected them all for lack of occasions.  ⚠ It is
    #    `LEZIONI.md` §1.9 applied to the new chapter — the same reason the
    #    video streams are counted.
    print(f"   the canvas: {state.canvases} FIT_CANVAS/CANVAS pairs closed · "
          f"{len(state.in_flight)} requests still in flight · canvas in force at the "
          f"end: "
          + (f"{state.canvas_size[0]}x{state.canvas_size[1]} from {state.canvas_from}"
             if state.canvas_size else "never declared"))
    # ⛔ AND SINCE 12 AUG 2026 «NOTHING TO JUDGE» WANTS **TWO** ZEROS.
    #
    #    Before, `messages == 0` was enough, because nobody looked at the
    #    video: a recording of frames only exited 3 and it was the
    #    truth.  ⛔ Today those frames are the object of the judgement, and
    #    exiting 3 would be acquitting without having looked — the very thing
    #    code 3 exists to prevent.
    if messages == 0 and video_streams == 0:
        raise NothingToJudge(
            f"{seen_items} blocks, {control_blocks} on the control channel and "
            f"{di_video} on the video channel, ZERO control messages and ZERO "
            f"video streams")
    print(f"   ⭐ compliant: no violation in {messages} messages and "
          f"{video_streams} video streams")
    return 0


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    try:
        return valid(sys.argv[1])
    except NotCompliant as e:
        print(f"\n   ⛔ NOT COMPLIANT — {e.rule_v}")
        print(f"      {e.says}")
        print(f"      byte {e.ass} in the file · offset {e.rel} in the block's payload")
        return 1
    except Malformed as e:
        print(f"\n   ⚠ MALFORMED RECORDING: {e}")
        print("      ⛔ It is not a judgement on the wire: it is a defect of the file.")
        return 2
    except CouldNotLook as e:
        # ⛔ Same code as the malformed one — neither of the two is a judgement
        #    on the wire — but another sentence: there one looks at the file,
        #    here at the tool.
        print(f"\n   ⚠ I COULD NOT LOOK: {e}")
        print("      ⛔ It is not a judgement on the wire and it is not «the file is broken»:")
        print("         the TOOL is missing.  ⚠ And it is not «it is fine»: it is form")
        print("         E8, «empty» and «forbidden» looking the same.")
        return 2
    except OSError as e:
        # ⛔ E8: «empty» and «forbidden» look the same.  Before, this bubbled
        #    up out of `main` and the process exited **1**, that is «the wire
        #    is not compliant», on a file that had not even been opened —
        #    and the diagnosis started from the protocol (finding R7.5).
        print(f"\n   ⚠ THE RECORDING CANNOT BE READ: {e}")
        print("      ⛔ It is not a judgement on the wire, and it is not «the file is broken»:")
        print("         it could not be opened.  One looks at permissions,")
        print("         path and volume — not at RCP.md.")
        return 2
    except NothingToJudge as e:
        print(f"\n   ⛔ NOTHING TO JUDGE: {e}")
        print("      It is not «compliant»: it is the absence of the object of the judgement.")
        print("      One looks at the recorder — whoever was supposed to write those bytes.")
        return 3


if __name__ == "__main__":
    sys.exit(main())
