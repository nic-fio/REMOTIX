#!/usr/bin/env python3
"""01-b3-cliente.py — the test client: the RCP handshake, written a second time.

    python3 01-b3-cliente.py --user prova --password X [--record t.rcpreg]
    python3 01-b3-cliente.py --certify     ⭐ HERE, with no network and no machine

---------------------------------------------------------------------------
⭐⭐ PHASE 9 — THE TWO AUDIO RULES, AND THE SWITCH BETWEEN THEM

The reorder cure — the one that stops throwing away blocks that arrived out of
sequence — was written **only in `src/pagina.html`**.  ⇒ No bench could
measure whether it bites, because the client the benches use did not have it.
Now it has it, behind `--audio-rule old|new`.

⛔⛔ **The default is `vecchia`, and it changes only by the user's decision.**
     Dozens of already-measured benches use this program: with the new rule
     as the default, every number already written would stop being
     comparable — and the «before / after the cure» comparison is exactly
     what we want to be able to make.  ⭐ `--certify` case 6 checks it against a
     LITERAL transcription of the code of 22 August, not against an opinion.

⚠ The translation from the page to here is NOT identical, and the five differences
  are written out in full above `class AudioSieve` (T1..T5).  The most
  important one: **here decoding costs zero**, and with `--audio-decode-ms 0`
  the `scartati_tardivi` counter is not a measurement, it is a blind zero.

---------------------------------------------------------------------------
⛔ ITS JOB, WHICH IS NOT «WORKING»

`PIANO.md` §1.1: this is **the second reader of `RCP.md`**, in a language
different from the server's.  ⛔ **Whoever grows it does not look at the C**: if
they looked they would inherit its misunderstandings, and two programs written by
the same hand that agree confirm nothing.

⭐ Its value is not the green: it is that whoever writes it **must choose** where
   the specification allows two readings, and those choices go in «what did
   NOT work» — they are defects of the document, and this is the phase in which
   they cost least.

---------------------------------------------------------------------------
⭐ AND IT RECORDS, IN THE FORMAT OF §11.1

Every byte that passes on the control channel ends up in a recording that
**the B4 validator can judge**.  ⛔ Not the password: it is
obscured as §11.1 requires — true length, bytes replaced with `0x2A`,
fingerprint of what was there.  So the validator sees the whole framing and
the password does not end up in a file.

⛔ **And it records even when the handshake does NOT succeed.**  A
`FAREWELL(ALREADY_ACTIVE_REMOTELY)` is the object the third round of B3 exists to
produce: if the trace were written only along the path that succeeds, the only
bench of invariant I2 would deliver nothing to the arbiter (finding R8.9).

⛔ **And the exit code says WHAT happened to the connection**: `0` I
stayed attached for the whole time asked, `4` the connection or the session
dropped earlier — and the log says which of the two (findings R8.2, R8.4).
`5` no `CANVAS` arrived (§7.1, the silence).  ⭐ `6` — 22 August 2026 —
**the requested scene cannot be exercised**: it is the case of `--old-pointer`
when there is no previous canvas, or when the new canvas is not
smaller.  ⛔ It is not `1` and it is not `0`: a bench that read «all fine» from a
scene that did not happen would be green by construction, and a bench that
read «the product got it wrong» would give the red to the wrong defendant.
"""
import argparse
import asyncio
import hashlib
import json
import os
import ssl
import struct
import sys
import time

# ⛔⭐ AND `aioquic` MAY NOT BE THERE — 23 August 2026, phase 9.
#
#     `aioquic` lives INSIDE the container, not on the laptop.  ⚠ As long as this
#     program could do only one thing — attach to a server — a
#     `ModuleNotFoundError` at the top of the file was the right diagnosis.  ⛔ But
#     `--certify` does not touch the network: it is a self-test of the audio screening, and
#     it must be able to run WHERE THE CODE IS WRITTEN.  With the import at the top it
#     did not even start.
#
# ⇒ We try to import, and if it is missing we carry on with placeholders: whoever
#   asks for the NETWORK finds out at once and with a line that says what to do, whoever
#   asks for `--certify` runs anyway.  ⚠ And the placeholder RAISES: an
#   import silently faked that let a real round start would be the worst form
#   of error, «it works and measures nothing».
try:
    from aioquic.asyncio import connect
    from aioquic.asyncio.protocol import QuicConnectionProtocol
    from aioquic.h3.connection import H3_ALPN, H3Connection
    from aioquic.h3.events import HeadersReceived
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.quic.events import QuicEvent
    AIOQUIC = None
except ModuleNotFoundError as _e:          # noqa: N816 — the name states the fact
    AIOQUIC = str(_e)

    class QuicConnectionProtocol:          # placeholder
        def __init__(self, *a, **kw):
            raise RuntimeError(f"⛔ without `aioquic` there is no network at all: {AIOQUIC}")

    class QuicEvent:                       # placeholder (needed by the annotation)
        pass

    class HeadersReceived:                 # placeholder (needed by `isinstance`)
        pass

    H3_ALPN = H3Connection = QuicConfiguration = connect = None

CLIENT, SERVER = 1, 2
T = {"HELLO": 0x0001, "HERE_I_AM": 0x0002, "CREDENTIALS": 0x0003, "ADMITTED": 0x0004,
     "REJECTED": 0x0005, "ATTACH": 0x0006, "SESSION": 0x0007,
     # ⭐ The CANVAS path, entered here on 16 August 2026 (sub-phase 6.6).
     #    ⛔ `fasi/06-la-tela-e-la-vista.md` §0 point 6: they had been in the protocol for
     #    a week and this client **did not send even one of them**.
     "VIEW": 0x0008, "LAYOUT": 0x0009, "CURSOR_SHAPE": 0x000A,
     "FIT_CANVAS": 0x000B, "FAREWELL": 0x000C, "REQUEST_KEY": 0x000D,
     "CANVAS": 0x000E, "TERMINATE_SESSION": 0x0011}
NAME = {v: k for k, v in T.items()}
# ⛔ THE INPUT CHANNEL LIVES IN A DICTIONARY OF ITS OWN, and it is not pedantry: `NAME`
#    is the inverse map of `T` and `_browse()` uses it to give a name to the
#    messages that arrive **on the control channel**.  A `0x0101` in there
#    would make the word «POINTER» appear in the log for a malformed control
#    message — that is, a diagnosis that sends you to look at the wrong
#    channel.  ⚠ And the channels really are two: §2.5, high byte `0x00` versus
#    `0x01`.
T_POINTER = 0x0101            # §7.3
T_BUTTON = 0x0102             # §7.3
LEFT_BUTTON = 0x110        # evdev BTN_LEFT
# The two outcomes and the three reasons of `CANVAS` — §7.1.
CANVAS_OUTCOME = {1: "FITTED", 2: "REFUSED"}
CANVAS_REASON = {0: "-", 1: "COMPOSITOR_UNABLE", 2: "SIZE_OUT_OF_RANGE",
               3: "NOT_NOW"}
REASONS = {0x07: "WRONG_CREDENTIALS", 0x08: "TOO_MANY_ATTEMPTS",
          0x09: "NOTHING_IN_COMMON", 0x0A: "INCOMPATIBLE_VERSION",
          0x0B: "PROTOCOL_ERROR", 0x0D: "TIMED_OUT",
          0x0E: "SESSION_UNSERVABLE", 0x0F: "ALREADY_ACTIVE_REMOTELY"}


def s(t):
    b = t.encode("utf-8") if isinstance(t, str) else t
    return struct.pack("!H", len(b)) + b


def wrap(kind, body):
    return struct.pack("!HI", kind, len(body)) + body


def _varint(d, i):
    """Reads a QUIC variable-length integer from `d` starting at `i`.

    Returns (value, next index), or (None, i) if the bytes are not
    enough.  ⚠ The length is in the two high bits of the first byte, and the value
    is what remains: reading the first byte whole is the mistake that makes
    0x40 0x41 look like two frames."""
    if i >= len(d):
        return None, i
    n = 1 << (d[i] >> 6)
    if i + n > len(d):
        return None, i
    v = d[i] & 0x3F
    for k in range(1, n):
        v = (v << 8) | d[i + k]
    return v, i + n


def _closing_capsule(d):
    """Looks for `CLOSE_WEBTRANSPORT_SESSION` (0x2843) and returns its code.

    ⛔ On the CONNECT wire capsules travel **inside DATA frames**
       (RFC 9297), so the normal case is `DATA(0x00) → capsule`.  The case
       in which the capsule arrives **naked** is a server defect — a browser
       would read `0x2843` as an unknown HTTP/3 frame type and would
       throw it away (RFC 9114 §9) — and this reader recognises it in order to
       SAY it, not to forgive it.

    Returns (code, naked) or (None, False)."""
    def inside(b):
        i = 0
        while i < len(b):
            kind, j = _varint(b, i)
            if kind is None:
                return None
            lung, j = _varint(b, j)
            if lung is None or j + lung > len(b):
                return None
            if kind == 0x2843 and lung >= 4:
                return b[j + 3]      # the four bytes of the code, the lowest
            i = j + lung
        return None

    # 1. the right form: one or more DATA frames, and the capsules inside
    i = 0
    while i < len(d):
        kind, j = _varint(d, i)
        if kind is None:
            break
        lung, j = _varint(d, j)
        if lung is None or j + lung > len(d):
            break
        if kind == 0x00:             # DATA
            c = inside(d[j:j + lung])
            if c is not None:
                return c, False
        i = j + lung
    # 2. the wrong form: the capsule without the frame that carries it
    c = inside(d)
    return (c, True) if c is not None else (None, False)


class Recorder:
    """The format of RCP.md §11.1, written once only.

    ⛔⛔ THE MAGIC IS `RCPREG 0x00 0x02`, AND UNTIL 16 AUGUST 2026 IT WAS NOT.

    ⭐ **It is the biggest defect found by sub-phase 6.6, and it was not in the
       product: it was between two benches.**  On 12 August 2026 the format of §11.1
    moved to `0x00 0x02` — the block carries the `fine` field and grows from 16 to 17
    bytes — and `01-b4-validatore.py` learned to **refuse** the old
    format, as §11.1 requires of it: *«an old validator must REFUSE the
    new format, not read it askew»*.

    ⛔ But this recorder kept on writing `0x00 0x01`.  ⇒ From that
       day **every B3 trace came out 2 from the arbiter** — «malformed
    recording» — and the five `valida` calls of `01-b3-lancia.sh` all
    failed, ⛔ making the whole bench exit **1**.  ⚠ Neither of the two
    programs was broken on its own: the validator did **exactly** what
    the specification asks of it, and the recorder wrote a format that had
    been valid until four days earlier.  It is the form of error that is born
    between two files, where no unit test looks.

    ⚠ **And the red was not mute: it was unreadable.**  «The trace is malformed»
      on a handshake bench sends you looking for a defect of the
    *recorder* — which indeed was there — but only after ruling out the server, the
    network and the protocol.  ⭐ The bench that keeps this door shut is
    `06-b38-registratore.py`, and it does not test the wire: it tests that the two benches
    speak the same language.

    ⭐⭐ **AND FROM 21 AUGUST 2026 THE MAGIC IS `0x00 0x03`: the block carries
       `instant_ms`.**

    §11.1 did not record **time**, and without time the rule of the *«grace
    second after `CANVAS(FITTED)`»* of §7.1 was not testable from any
    `.rcpreg` — it was the `[?]` of `fasi/06-la-tela-e-la-vista.md` §7.2.

    ⛔ **And the instant is MONOTONIC and RELATIVE to the first block, never a
       wall-clock time.**  §4.4 forbids secrets in the file, and an absolute date is not a
    secret by chance: it says **when** and — together with the address the
    recording already carries — **from where** a user connected.  The first
    block is 0, and whoever reads learns nothing about who recorded.

    ⛔ **And the `orologio` field in the header says WHOSE times they are**
       (1 = client, 2 = server), because the second rule belongs to the **server**
    and a trace taken at the client measures a **shorter** interval: half a
    network round trip per side.  ⇒ From here the arbiter concludes **in one direction only**, and
    declares it.  The line is in `01-b4-validatore.py`.
    """

    MAGIC = b"RCPREG\x00\x03"
    # ⛔ Yesterday's two magics are kept HERE and not only in the arbiter: the
    #    bench that refuses them (`01-b4-registrazioni.py`) writes them, and two
    #    lists of versions in two files are two lists that diverge.
    MAGIC_V1 = b"RCPREG\x00\x01"
    MAGIC_V2 = b"RCPREG\x00\x02"
    CONTINUE, FIN, RESET = 0, 1, 2
    CLOCK_CLIENT, CLOCK_SERVER = 1, 2

    def __init__(self):
        self.blocks = []
        self.written = False
        # ⛔ This program is the CLIENT: the times are its own, and it says so.
        #    ⚠ Writing `2` here would mean making the arbiter believe it has
        #      the server's clock, and then the «one direction only» conclusion
        #      would become a two-direction conclusion — wrong.
        self.clock = self.CLOCK_CLIENT
        self.t0 = None
        # ⛔ The control channel stream, the REAL one.  §4.2: it is the first
        #    bidirectional stream of the session, and ⚠ **it is not 0** — in
        #    HTTP/3 stream 0 is already the CONNECT one (finding R1.5).  Here we
        #    used to write a fixed `0`: a number that was never the right one, and that
        #    the arbiter uses for P3 (§2.5, «a frame on the control channel
        #    stream»).
        self.stream = 0

    def instant(self):
        """⛔ Milliseconds since the FIRST block, from a monotonic clock — §11.1.

        ⚠ `time.monotonic()` and not `time.time()`, and it is not pedantry: an
          NTP adjustment in the middle of a session would make the instants **go
          backwards**, and the arbiter would read a `POINTER`
          arrived *before* the `CANVAS` that precedes it on the wire.
        """
        t_now = time.monotonic()
        if self.t0 is None:
            self.t0 = t_now
        ms = int((t_now - self.t0) * 1000.0)
        # ⛔ The field is u32: 49 days.  It saturates instead of wrapping, because
        #    an instant that restarts from zero is worse than an instant standing still.
        return min(ms, 0xFFFFFFFF)

    def add(self, which_way, load, obscured=(), channel=0x00, stream=None,
                 fine=CONTINUE, instant=None):
        self.blocks.append([which_way, channel, fine,
                             self.stream if stream is None else stream,
                             load, list(obscured),
                             self.instant() if instant is None else instant])

    def mark_end(self, which_way, fine, stream=None):
        """⛔ How the stream closed, and from WHICH side — §11.1.

        ⭐ It is not a format detail: it is the only byte that lets
           the arbiter tell **«the server did not answer»** from **«the
        recording ends here»**.  §7.1 requires a `CANVAS` for every
        `FIT_CANVAS`, and without this field a trace that ends with a
        request in flight looks the same in both cases — the form of error
        **E8**, and this time on the rule with the worst symptom:
        *«the application has hung»*.

        ⚠ If the last block is already of that direction it is marked; otherwise a
          block with **zero** payload is added, which is the honest way of saying
          «from this side nothing else arrived, and then it closed».
        """
        if self.blocks and self.blocks[-1][0] == which_way:
            self.blocks[-1][2] = fine
            return
        self.add(which_way, b"", stream=stream, fine=fine)

    def write(self, fpath):
        # ⛔ The header of §11.1: magic · u32 block_count · u8 clock ·
        #    3 reserved bytes that MUST be 0.
        out = bytearray(self.MAGIC + struct.pack("!IBBBB", len(self.blocks),
                                                 self.clock, 0, 0, 0))
        for which_way, channel, fine, stream, load, osc, ist in self.blocks:
            out += struct.pack("!BBBIQIH", which_way, channel, fine, ist, stream,
                               len(load), len(osc))
            for ini, here, imp in osc:
                out += struct.pack("!II", ini, here) + imp
            out += load
        with open(fpath, "wb") as f:
            f.write(bytes(out))


# ══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE AUDIO SCREENING — §6.3, and the reorder cure of phase 9
#
# ⛔⛔ WHY THIS CLASS EXISTS, AND THE HOLE IT CLOSES — 23 August 2026.
#
#      The reorder cure was written **only in `src/pagina.html`**
#      (`audio_slot_past`, `discarded_late`, `out_of_order`, `duplicates`,
#      `recovered`, `ist_max_us`).  This client — which is the second reader
#      of `RCP.md` and the one ALL the benches use — still had the rule of
#      before: `instant <= last ⇒ throw away`.  ⇒ **No bench could measure whether
#      the cure bites**, because the client the benches use does not have it.
#
# ⛔⛔ AND THE DEFAULT STAYS `old`, by the user's decision.
#      `01-b3-cliente.py` is used by dozens of already-measured benches: changing the
#      default behaviour would make every number already written stop being
#      comparable.  ⭐ With `--audio-rule old` the counters
#      `received` and `stale` and the list of delivered blocks are IDENTICAL to
#      those of before — and `--certify` case 6 checks it against a
#      literal transcription of the code of before, not against an opinion.
#
# ── THE PAGE'S RULE, IN FOUR CASES ────────────────────────────────────────
#   `[R]` src/pagina.html:6497-6572 (the wire) and 5889-6186 (`plays()`).
#
#   1. `instant == last`  ⇒ **duplicate**: thrown away.  Playing it twice
#      would double the signal, which is the worst way to fail.
#      ⛔ Zero is the expected number: QUIC discards repeated packets by itself.
#   2. `instant < last` (BEHIND) and its place in time has ALREADY PASSED
#      ⇒ `discarded_old`: it is truly consumed, §6.3 to the letter.
#   3. `instant < last` but its place **is still there** ⇒ `out_of_order`:
#      ⭐ IT IS KEPT, and that is the whole cure.  The anchor gives it an absolute place:
#      it does not need to arrive in order to land in it.  And the
#      debt of `missed` is repaid (`recovered`), or every cured overtaking would
#      show up as a loss — the cure would accusations itself.
#   4. `instant > last` (THE NEWEST) ⇒ it is NEVER screened, the hole is counted
#      (`missed`) and `last` advances.  ⛔ Screening the newest too
#      would leave the anchor adrift with no possible rearm: session mute for
#      ever with all counters green (`LEZIONI.md` §2.2).
#
#   And then there is the SECOND DOOR, which in the page lives inside `plays()`: a
#   block that has passed the wire may have lost its place **while we were
#   decoding it**.  There the cases are two and not one:
#     · it is the newest we have ⇒ it is the WHOLE playback that is late:
#       the anchor is rearmed (`rearms`), as it always has been;
#     · it is an OVERTAKEN one (`ist_max_us > instant`) ⇒ only it is late:
#       `discarded_late`, and the anchor is NOT touched.  ⛔ Treating them the same
#       would cost a rearm for every overtaking, that is 250 ms of delay
#       given away for a 5 ms block.
#
# ── ⚠ THE TRANSLATION, AND WHERE IT IS **NOT** IDENTICAL TO THE PAGE ──────
#
#   The page measures «the place has passed» with `a.base + instant < ctx.currentTime`,
#   that is with the playhead of a real `AudioContext`.  Here there is neither an
#   `AudioContext` nor a decoder.  ⇒ The DECLARED differences are
#   five, and whoever reads a number from this client must know them:
#
#   T1 · **The playback clock is SIMULATED**: `now` comes from the monotonic one
#        (or from the fake clock of `--certify`), not from `ctx.currentTime`.
#        ⚠ A real `AudioContext` can drift from the monotonic clock by a few parts
#        per million; here the two clocks are the SAME clock, so this
#        client **cannot see the drift** between sound card and system.
#   T2 · **There is no «suspended» state**: the page, with `ctx.state !== "running"`,
#        answers «no» to the passed place and throws into `pending`.  Here the clock
#        always runs ⇒ `pending` does not exist and cannot be measured from here.
#   T3 · **Decoding costs zero**: in the page, between the wire and `plays()` there is
#        a real `AudioDecoder`, and `discarded_late` is born PRECISELY from that
#        delay.  ⇒ Here the second door opens at the same instant as the
#        first and `discarded_late` would stay **zero by construction** — which
#        would be a false green.  ⭐ That is why there is `decode_delay_s`: the
#        time we pretend to spend decoding.  At zero (the default
#        on the network) `discarded_late` **is not a measurement, it is a blind zero**.
#   T4 · **`step_us` does not come from a decoder**: for PCM it is COMPUTED
#        from the payload — `[S]` `RCP.md`:1299, «480 samples, 960 bytes, 5 ms per
#        datagram» — which is exact and not circular.  ⚠ For Opus we cannot
#        decode: `step_us` stays 0 (and then, as in the page, the count
#        of `missed` IS OFF) until it is declared with
#        `--audio-step-us`.
#   T5 · **`Math.round` versus `round()`**: JS rounds the half upwards,
#        Python to even.  Here we write `int(x + 0.5)` by hand, or on a
#        jump of exactly 1.5 steps the two programs would count different
#        `missed` — and it would be a difference invisible until the wrong day.
#
# ── PURITY, AND WHY THERE ARE TWO ─────────────────────────────────────────
#
#   `purity` = **delivered at the output / arrived on the wire** — where «arrived
#   on the wire» are the conforming datagrams (right prefix, ≥12 bytes, type 0x0401)
#   and «delivered» those that end up in `a_blocks`, that is what the
#   sound judge will be able to listen to.  ⭐ It is the definition needed here.
#
#   ⛔ And it is **NOT** the formula the page benches use
#   (`09-b74-audio-firefox.py`:300, `played / received`): there `received` is
#   incremented **after** the screening (`src/pagina.html`:6574), so the datagrams
#   thrown away on the wire **are neither in the numerator nor in the denominator** — and
#   that fraction is BLIND precisely to the damage this cure repairs.  It is
#   printed anyway, as `page_purity`, because it is the number with which the
#   rounds on the page are compared; ⚠ in this client it is 1.000 by
#   construction with the old rule, and whoever read it alone would conclude
#   «all healthy» from a destroyed sequence.
AUDIO_CUSHION_MS = 250          # `[R]` src/pagina.html:5550
# ⛔⛔ THE DEFAULT IS `old`, and it changes ONLY by the user's decision.
AUDIO_RULE = "old"
AUDIO_STEP_US = 0              # 0 = derived from the PCM (T4)
AUDIO_DECODE_S = 0.0        # ⚠ T3: at zero `discarded_late` is blind


class AudioSieve:
    """§6.3 and the reorder cure, with the switch between the two rules.

    ⛔ `rule="old"` is the DEFAULT and is not changed from here: it is what
       keeps the already-measured numbers comparable.
    """

    RULES = ("old", "new")

    def __init__(self, rule="old", cushion_ms=AUDIO_CUSHION_MS,
                 clock=time.monotonic, step_us=0,
                 decode_delay_s=0.0):
        if rule not in self.RULES:
            raise ValueError(f"audio rule «{rule}»: the rules are {self.RULES}")
        self.rule = rule
        self.cushion_s = cushion_ms / 1000.0
        self._clock = clock
        self.decode_delay_s = decode_delay_s
        # ⚠ T4: 0 = I do not know, and then the count of `missed` is OFF —
        #   as in the page, which writes `if (a.step_us > 0)`.
        self.step_us = step_us
        self.step_declared = step_us > 0
        # ── the counters, with the page's names ───────────────────────────
        self.on_wire = 0            # conforming datagrams arrived (denominator)
        self.received = 0            # passed the wire screening
        self.delivered = 0          # the page's `played`: actually output
        self.discarded_old = 0     # behind, and its place has passed
        self.discarded_late = 0    # overtaken, and the place passed afterwards
        self.out_of_order = 0        # ⭐ behind AND KEPT: the cure
        self.duplicates = 0            # the same `instant` twice
        self.recovered = 0          # `missed` repaid by an out-of-order one
        self.missed = 0             # never arrived: the hole on the wire
        self.missed_times = 0
        self.rearms = 0              # the anchor moved (the «HOLES»)
        self.ist_max_us = 0          # the maximum PUT IN THE SCHEDULE
        self.last_instant = None   # the maximum ACCEPTED ON THE WIRE
        self.base = None             # the anchor: seconds to add to `instant`

    # ── the frontier «its place has already passed» ───────────────────────
    def _past_slot(self, ist_us, now):
        """`[R]` `audio_slot_past`, src/pagina.html:5889.

        ⛔ Two cases in which the answer is «no» and not «I do not know»: `instant`
           null, and anchor not yet hooked — there NOTHING has been consumed.
        ⚠ T2: the page's third case (suspended context) is missing, because here
          the clock never stops.
        """
        if not ist_us > 0 or self.base is None:
            return False
        return self.base + ist_us / 1e6 < now

    def _count_missed(self, instant):
        """`[R]` src/pagina.html:6550.  ⚠ T5: `int(x + 0.5)`, not `round()`."""
        if self.last_instant is None or self.step_us <= 0:
            return
        jump = instant - self.last_instant
        amount = int(jump / self.step_us + 0.5) - 1
        # ⚠ The threshold is 1.5 steps and not «more than one step»: the `instant` comes
        #   from the capture and not from a metronome.
        if amount >= 1 and jump > self.step_us * 1.5:
            self.missed += amount
            self.missed_times += 1

    def arrival(self, instant, codec=0, payload_bytes=0):
        """A conforming datagram has arrived.  Returns `(delivered, reason)`.

        ⛔ The count of `on_wire` is HERE and not earlier: datagrams discarded for
           prefix, length or type are not audio blocks, and putting them in the
           denominator of purity would confuse «the network reorders» with «the
           server sends garbage».
        """
        self.on_wire += 1
        new_one = self.rule == "new_one"

        if self.last_instant is not None and instant == self.last_instant:
            # ⚠ With the OLD rule `duplicates` is a SUB-COUNT of
            #   `discarded_old`, not a separate item: the code of before
            #   counted them in there (`instant <= last`), and removing them
            #   would change every number already measured.  ⭐ Counting them anyway
            #   costs zero and says something that was not known before.
            self.duplicates += 1
            if not new_one:
                self.discarded_old += 1
            return (False, "duplicate: the same `instant` twice")

        if self.last_instant is not None and instant < self.last_instant:
            if not new_one:
                # The rule of before, to the letter: behind ⇒ thrown away.
                self.discarded_old += 1
                return (False, "istante no longer the most recent (old rule)")
            now = self._clock()
            if self._past_slot(instant, now):
                self.discarded_old += 1
                return (False, "its place in time has already passed (§6.3)")
            # ⭐ OUT OF ORDER BUT STILL PLAYABLE: that is the whole cure.
            self.out_of_order += 1
            if self.missed > 0:
                self.missed -= 1
                self.recovered += 1
        else:
            self._count_missed(instant)
            # ⛔ ONLY FORWARDS: `last_instant` is a MAXIMUM.  Bringing it
            #    back on an out-of-order one would make the next datagram
            #    look like a huge jump, and the count of `missed` would
            #    fill up with fake losses.
            self.last_instant = instant

        self.received += 1
        return self._delivery(instant, codec, payload_bytes)

    def _delivery(self, ist_us, codec, payload_bytes):
        """The second door: in the page it is inside `plays()`.

        ⚠ T3: here decoding costs `decode_delay_s`, which on the network is
          zero — and with zero `discarded_late` is not a measurement, it is a blind
          zero.  `--certify` exercises it with a declared delay.
        """
        now = self._clock() + self.decode_delay_s
        t = ist_us / 1e6
        if self.base is None:
            self.base = now + self.cushion_s - t
        when = self.base + t
        if when < now + 0.001:
            if self.rule == "new" and self.ist_max_us > ist_us:
                # ⛔ IT IS AN OVERTAKEN ONE, and only it is late: it is thrown away
                #    and the anchor stays where it is.
                self.discarded_late += 1
                return (False, "overtaken, and the place passed while we were "
                               "decoding it")
            # It is the newest we have: it is the WHOLE playback that is
            # late ⇒ the anchor moves.  ⚠ It is the only thing that RAISES the
            # queue again, and it is audible.
            self.rearms += 1
            self.base = now + self.cushion_s - t
        if ist_us > self.ist_max_us:
            self.ist_max_us = ist_us
        # ⚠ T4: the step from the PCM payload, not from a decoder.
        if not self.step_declared and codec == 2 and payload_bytes > 0:
            self.step_us = int(payload_bytes * 5000 / 960 + 0.5)
        self.delivered += 1
        return (True, "")

    # ── the two numbers that get printed ──────────────────────────────────
    @property
    def purity(self):
        """Delivered at the output / arrived on the wire.  `None` = nothing to say."""
        if self.on_wire == 0:
            return None
        return self.delivered / self.on_wire

    @property
    def page_purity(self):
        """`suonati / ricevuti`, the formula of `09-b74`.  ⚠ Blind to the screening."""
        if self.received == 0:
            return None
        return self.delivered / self.received

    def line(self):
        """The counters, ALWAYS, with both rules and even at zero."""
        p, pp = self.purity, self.page_purity
        return (f"rule {self.rule} · on wire {self.on_wire} · "
                f"received {self.received} · delivered {self.delivered} · "
                f"PURITY {'?' if p is None else format(p, '.4f')} "
                f"(page {'?' if pp is None else format(pp, '.4f')})")

    def counts_line(self):
        return (f"late {self.discarded_late} · out {self.out_of_order} · "
                f"rec {self.recovered} · dup {self.duplicates} · "
                f"missed {self.missed} times {self.missed_times} · "
                f"rearms {self.rearms} · step {self.step_us}us")


class Client(QuicConnectionProtocol):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._http = H3Connection(self._quic, enable_webtransport=True)
        self.accepted = asyncio.get_event_loop().create_future()
        self.session = None
        self.check = None
        self.incoming = bytearray()
        self.messages = asyncio.Queue()
        self.finished = False
        # ⛔⛔ THE RECORDER LIVES HERE, AND NOT IN THE QUEUE — 21 August 2026.
        #
        #    Until today every server message ended up in the trace **at the
        #    moment someone pulled it out of the queue** (`should_wait()`
        #    and `ask_canvas()`).  ⇒ A message that arrives when nobody is
        #    waiting — that is, during `--stay`, which is almost the whole life of
        #    a session — did NOT enter the trace at all.
        #
        # ⛔ And the two rules that fell into that hole are exactly the two that
        #    §7.1 entrusts to the arbiter:
        #      · **T1** — an UNSOLICITED `CANVAS`;
        #      · **V3** — a `CANVAS` after a `VIEW`.
        #    The arbiter knows how to accusations them (`01-b4-registrazioni.py` cases 22 and 30,
        #    `06-b38-mutazioni.py`), but on **built** recordings: from a
        #    trace of this client they could never come out.  ⇒ Round 5 of
        #    `06-b38-tela.sh` — *«no CANVAS after the VIEW»* — was **green by
        #    construction**, which `LEZIONI.md` says is worse than no case at all.
        #
        # ⭐ The cure is one of place, not of logic: we record where the bytes
        #    ARRIVE (`_browse`), not where they are consumed.  ⚠ And this way
        #    the order of the blocks is the wire's, which is what §11.1
        #    asks for.  Found with `06-b40-lancia.sh`, cases 6 and 9.
        self.reg = None
        # ⛔ §3.1 point 3: the reason ALSO travels in the application error
        #    code with which the WebTransport session is closed.  It is
        #    kept, because it is the second of the two paths — and on the day
        #    the `FAREWELL` does not arrive it is the only one.
        self.close_code = None
        # ⛔ WHAT DROPPED, AND WHEN — findings R8.2 and R8.4 of 10 August 2026.
        #
        #    B3 asks twice «is the first one still attached?», and both
        #    times it read it from the EXISTENCE OF THE PROCESS or from its exit
        #    code.  ⚠ But this program, after SESSION, just slept:
        #    the connection could die from QUIC's idle cap, or
        #    the session could be closed by the server, and the process stayed
        #    alive and exited 0 all the same.  The bench read «alive» from a fact it
        #    had not observed (E7: verify from the sending side).
        #
        # ⭐ Here we observe from the receiving side: whoever drops says so, with the name
        #    of WHAT dropped — and the two cases are not confused, because
        #    «QUIC closed by itself» and «the server closed the session» are the
        #    two defendants the fourth round exists to separate.
        self.drop = None
        # ═══ THE AUDIO — phase 7 ══════════════════════════════════════════
        # ⛔ The counters are SIX and not one, and each names a different rule
        #    of §6.3: whoever summed them would get a number that never says
        #    where to look (`LEZIONI.md` §2.2).
        self.a_received = 0      # datagrams arrived and conforming
        self.a_short = 0         # < 12 bytes: §6.3 has them discarded
        self.a_type = 0          # `kind` != 0x0401
        self.a_prefix = 0      # the RFC 9297 prefix is not our session
        self.a_stale = 0        # `instant` no longer the most recent: §6.3
        self.a_codec = None      # the codec declared in the datagrams
        self.a_byte = 0
        # ⭐ THE SCREENING — phase 9.  ⛔ The rule comes from a module
        #    variable and not from the constructor because `create_protocol=Client`
        #    passes no arguments; the default is `old` in two places (here
        #    and in `--audio-rule`), and they agree on purpose.
        self.a_screening = AudioSieve(rule=AUDIO_RULE, step_us=AUDIO_STEP_US,
                                    decode_delay_s=AUDIO_DECODE_S)
        # The blocks as they arrived, for the judge of `07-b42`.
        self.a_blocks = []
        self.dropped = asyncio.Event()
        # ⛔ AND THE THIRD CAUSE: THAT WE CLOSED THE CONNECTION OURSELVES.
        #
        #    `[M]` 10 August 2026, third round: the `--stay` window expires,
        #    this program exits 0, and `connect()` closes the connection
        #    leaving its context — aioquic raises `ConnectionTerminated`
        #    code 0 with no reason, and the line below ended up in the log
        #    IDENTICAL to that of a server that ousts you.  The bench
        #    found it with a grep over the whole file and gave the red to the server,
        #    which had just kept the session alive with PINGs for 25 s.
        #
        # ⭐ «Terminated by us» and «terminated by someone else» are two different
        #    facts and now they have two different lines (CODER.md §3.9, §4.2).
        self.closed_by_us = False
        # ═══ THE CLIPBOARD — phase 7, §7.4 ════════════════════════════════
        # ⛔ THIS CLIENT IS THE SECOND READER OF `RCP.md` (`PIANO.md` §1.1),
        #    and the three messages of §7.4 come in here because otherwise the clipboard
        #    wire would be validated by ONE SINGLE implementation — the
        #    page, written by the same hand as the server.
        #
        # ⚠ Assembly is PER STREAM, not a single one: §2.5 says «one stream per
        #   transfer», so there is more than one alive at once.  ⛔ With a
        #   single accumulator two interleaved transfers would get mixed, and that is
        #   exactly the defect the identifier of §7.4 exists to
        #   remove — finding it here would mean never finding it.
        self.app_in = {}          # stream_id -> bytearray, the assembly
        self.app_my_id = 0       # §7.4: each side numbers its OWN, from 1
        self.app_my_text = ""
        self.app_peer_id = 0       # the server's last announcement
        self.app_peer_len = 0
        self.app_received = None  # the last text the server sent us
        self.app_announcements = []     # [(id, bytes)] all the server's announcements
        self.app_asked = []     # [id] the transfers the server asked us for
        self.app_served = 0
        self.app_violations = []  # what does NOT match §7.4, with its name
        self.app_event = asyncio.Event()
        # The preamble of the server's unidirectional streams, per stream:
        # `0x40 0x54` plus the session varint.  `None` = not ours.
        self.uni_pref = {}
        self.uni_kind = {}
        # ═══ THE VIDEO TAKEN FROM THE WIRE — phase 3/7, 17 August 2026 ════
        # ⛔ NOT to paint it: to SEPARATE our stream from the
        #    browser's decoder.  «The artefacts are ours» and «they are
        #    its» look the same when watching the screen, and they are told apart in
        #    one way only — by giving the SAME BYTES to a third decoder that
        #    is neither of the two (`ffmpeg`/`dav1d`).
        # ⚠ And the bytes are those of the WIRE, not those of the survey: between the
        #   encoder and the browser there is the whole transport, and a defect there
        #   in the middle the survey would not see.
        self.v_in = {}          # stream_id -> bytearray being assembled
        # ⛔ The streams already recorded: the §6.2 header is written ONCE
        #    per stream, or a single canvas would appear ten times and the
        #    denominator of T4 would count frames that are not there.
        self.v_reg = set()
        self.v_frames = []  # [(number, key, width, height, data)]
        # ═══ THE INPUT CHANNEL — §2.5, §7.3, and 22 August 2026 ═══════════
        # ⛔ `RCP.md` §2.5: «**only one**, opened after receiving `SESSION`
        #    and kept open».  ⚠ It is NOT like the clipboard, where every
        #    transfer has its own stream: here one stream per message
        #    would be **another protocol**, and the server that counts the `id`s
        #    «over the whole channel» (§7.3) would no longer have a channel on which to
        #    count them.
        self.inp_stream = None
        # §7.3: «increasing, starts from 1.  ⛔ 0 is reserved».
        self.inp_id = 0
        # ⭐ THE **RECORDED** INSTANT OF THE LAST `CANVAS`, and not the time of
        #    now: the grace second is arbitrated by §11.1 on `instant_ms`, and
        #    a delay counted on a clock different from the one that ends up
        #    in the file would give a `dt` that is not the one the arbiter reads.
        self.last_canvas_ms = None

    def _cade(self, why: str) -> None:
        """The first cause wins: the following ones are consequences, not causes."""
        if self.drop is None:
            self.drop = why
            self.dropped.set()

    def open_session(self, authority, fpath):
        sid = self._quic.get_next_available_stream_id(is_unidirectional=False)
        self.session = sid
        self._http.send_headers(sid, [
            (b":method", b"CONNECT"), (b":protocol", b"webtransport"),
            (b":scheme", b"https"), (b":authority", authority.encode()),
            (b":path", fpath.encode()),
            (b"origin", f"https://{authority}".encode()),
        ])
        self.transmit()

    def open_control(self):
        # ⛔ RCP.md §4.2: the control channel is the FIRST bidirectional
        #    stream of the session.  ⚠ And it is NOT «stream 0»: in
        #    HTTP/3 stream 0 is already the CONNECT one that establishes the
        #    session, and the API exposes no number (finding R1.5).
        self.check = self._http.create_webtransport_stream(
            self.session, is_unidirectional=False)
        return self.check

    def send_msg(self, data):
        self._quic.send_stream_data(self.check, data, end_stream=False)
        self.transmit()

    # ══════════════════════════════════════════════════════════════════════
    # THE INPUT — §7.3, and the single channel of §2.5
    # ══════════════════════════════════════════════════════════════════════

    def open_input(self):
        """The input channel stream: **only one**, and it is kept open.

        ⛔ It is opened the first time it is needed, and not at every message: §2.5
           says «only one … and kept open», and §7.3 counts the `id`s «over the whole
           channel».  ⚠ Opening it and not closing it is not an oversight: closing it
           with FIN would tell the server «the client sends no more input», which is
           a different thing from what this bench wants to say.
        """
        if self.inp_stream is None:
            self.inp_stream = self._http.create_webtransport_stream(
                self.session, is_unidirectional=True)
        return self.inp_stream

    def send_pointer(self, x, y):
        """⭐ `POINTER(x, y)` — §7.3, coordinates on the **canvas**.

        ⛔ And it is recorded with channel `0x01` and with the REAL stream: §11.1
           defines the `channel` field as «the high byte of `tipo`», and
           the arbiter **refuses** a block in which the two do not match — a
           recording that declared `0x00` would make these bytes be read
           as if they were control, and the second rule would never come out
           of this trace.
        """
        sid = self.open_input()
        self.inp_id += 1
        # ⛔ §7.3: «microseconds of the CLIENT's monotonic clock», and «the
        #    client writes TRUE microseconds and MUST NOT suggest a
        #    precision it does not have» (finding R1.27).  ⚠ Here the grain is that
        #    of CPython's `time.monotonic()` — nanoseconds on the Linux kernel —
        #    so nothing is multiplied by a thousand.
        ist_us = int(time.monotonic() * 1_000_000)
        b = wrap(T_POINTER,
                     struct.pack("!IQII", self.inp_id, ist_us, x, y))
        self._quic.send_stream_data(sid, b, end_stream=False)
        self.transmit()
        ms = None
        if self.reg is not None:
            self.reg.add(CLIENT, b, channel=0x01, stream=sid)
            ms = self.reg.blocks[-1][6]
        return self.inp_id, ms

    def send_button(self, pressed, code=LEFT_BUTTON):
        """⭐ `BUTTON` — §7.3, **evdev** code, pressed/released.

        ⛔ It serves one reason only and it must be written down: **giving FOCUS to a
           window of the remote desktop**.  `[M]` 20 Sep 2026, `gnome` box:
           on Mutter the clipboard is granted to whoever has the active window, and in
           a remote session nobody clicks ⇒ neither `wl-copy` nor `wl-paste` nor
           a GTK application manage to touch the clipboard, and the clipboard mesh
           could not judge.  ⭐ With the click, sent from here —
           through the product, not bypassing it — focus arrives and the
           clipboard behaves as it does for a person.
        """
        sid = self.open_input()
        self.inp_id += 1
        ist_us = int(time.monotonic() * 1_000_000)
        b = wrap(T_BUTTON,
                     struct.pack("!IQHB", self.inp_id, ist_us, code,
                                 1 if pressed else 0))
        self._quic.send_stream_data(sid, b, end_stream=False)
        self.transmit()
        if self.reg is not None:
            self.reg.add(CLIENT, b, channel=0x01, stream=sid)
        return self.inp_id

    # ══════════════════════════════════════════════════════════════════════
    # THE CLIPBOARD — §7.4, and the three messages read from `RCP.md` and not from the C
    # ══════════════════════════════════════════════════════════════════════

    def clipboard_send(self, kind, body):
        """A clipboard channel message, on its unidirectional stream.

        ⛔ One stream per message, and it is closed with FIN.  §2.5 says «one per
           transfer» and this client chose the strictest reading —
           the same as the server's — because what binds the messages of a
           transfer is the `transfer` field (§7.4), not the stream.
           ⚠ If the two implementations had read §2.5 differently, the
             wire would work all the same: it is the proof that the line is ambiguous and
             that the ambiguity does not bite.  It goes in the phase document.
        """
        sid = self._http.create_webtransport_stream(
            self.session, is_unidirectional=True)
        self._quic.send_stream_data(sid, wrap(kind, body), end_stream=True)
        self.transmit()
        return sid

    def clipboard_announce(self, text):
        """«I have new text» — §7.4, `CLIPBOARD_ANNOUNCE`."""
        d = text.encode("utf-8")
        self.app_my_id = 1 if self.app_my_id >= 0xFFFFFFFF else self.app_my_id + 1
        self.app_my_text = text
        self.clipboard_send(0x0201, struct.pack("!II", self.app_my_id, len(d)))
        print(f"   [app]  announced transfer {self.app_my_id}, "
              f"{len(d)} bytes")
        return self.app_my_id

    def clipboard_ask(self, transfer=None):
        """«Send it to me» — §7.4, `CLIPBOARD_ASK`."""
        t = self.app_peer_id if transfer is None else transfer
        self.clipboard_send(0x0202, struct.pack("!I", t))
        print(f"   [app]  asked for transfer {t}")
        return t

    def _clipboard_one(self, kind, body):
        """A whole clipboard channel message, already unrolled from §6.1."""
        if kind == 0x0201:                                   # ANNOUNCE
            if len(body) != 8:
                self.app_violations.append(
                    f"CLIPBOARD_ANNOUNCE with {len(body)} bytes: §7.4 wants 8")
                return
            t, n = struct.unpack("!II", body)
            self.app_peer_id, self.app_peer_len = t, n
            self.app_announcements.append((t, n))
            print(f"   [app]  ⭐ the server announces transfer {t}, {n} bytes")
            self.app_event.set()
            return
        if kind == 0x0202:                                   # ASK
            if len(body) != 4:
                self.app_violations.append(
                    f"CLIPBOARD_ASK with {len(body)} bytes: §7.4 wants 4")
                return
            (t,) = struct.unpack("!I", body)
            self.app_asked.append(t)
            print(f"   [app]  ⭐ the server asks for transfer {t}")
            # ⛔ §7.4: «an identifier that matches no live announcement
            #    is PROTOCOL_ERROR».  ⚠ Here the session is NOT closed:
            #    this is a bench, and its job is to RECORD that the
            #    server got it wrong, not to punish it — if it closed, the round
            #    would end and nobody would read anything any more.
            if t == 0 or t > self.app_my_id:
                self.app_violations.append(
                    f"CLIPBOARD_ASK for transfer {t}, and I have "
                    f"announced {self.app_my_id} (§7.4)")
                return
            d = self.app_my_text.encode("utf-8")
            self.clipboard_send(0x0203, struct.pack("!I", t) + d)
            self.app_served += 1
            print(f"   [app]  served {len(d)} bytes to the server (transfer {t})")
            self.app_event.set()
            return
        if kind == 0x0203:                                   # TEXT
            if len(body) < 4:
                self.app_violations.append(
                    f"CLIPBOARD_TEXT with {len(body)} bytes: §7.4 wants >= 4")
                return
            (t,) = struct.unpack("!I", body[:4])
            d = body[4:]
            if t != self.app_peer_id:
                self.app_violations.append(
                    f"CLIPBOARD_TEXT for transfer {t}, and the live announcement "
                    f"is {self.app_peer_id} (§7.4)")
            if len(d) != self.app_peer_len:
                self.app_violations.append(
                    f"CLIPBOARD_TEXT carries {len(d)} bytes and the announcement "
                    f"declared {self.app_peer_len} (§7.4)")
            # ⛔ §5.4: «the text MUST be UTF-8».  It is decoded STRICTLY: a
            #    lenient decoder would put replacement characters
            #    in place of an error, and the bench would say green on a text that
            #    is not the one that had been copied.
            try:
                self.app_received = d.decode("utf-8")
            except UnicodeDecodeError as e:
                self.app_violations.append(f"CLIPBOARD_TEXT is not UTF-8: {e}")
                self.app_received = None
            print(f"   [app]  ⭐ {len(d)} bytes arrived from the server "
                  f"(transfer {t})")
            self.app_event.set()
            return
        self.app_violations.append(
            f"type {kind:#06x} on the clipboard channel: §7.4 defines THREE")

    def _decide_channel(self, sid, load, fine):
        """The high byte of `kind` gives the channel (§2.5), and now it is here."""
        self.uni_pref.pop(sid, None)
        if load[0] == 0x02:
            self.uni_kind[sid] = "wt"
            self._clipboard_stream(sid, load, fine)
        elif load[0] == 0x03:
            self.uni_kind[sid] = "video"
            self._video_stream(sid, load, fine)
        else:
            # ⚠ A channel this client does not needs: it SAYS so instead of
            #   keeping quiet — «received and not used» and «never arrived» must not
            #   look the same.
            self.uni_kind[sid] = "altro"
            print(f"   [wt]   ⚠ uni stream {sid}, channel 0x{load[0]:02x}: "
                  f"legitimate and not served by this client (§2.5)")

    def _video_stream(self, sid, data, fine):
        """A stream of the VIDEO channel (§6.2): one stream, one frame.

        ⛔ And the end of the stream IS the end of the frame — but **only with a
           FIN**: a reset stream carries an incomplete frame, which §6.2
           requires to be THROWN AWAY and not handed to the decoder.
        ⚠ Here `aioquic` does not tell the two cases apart on this path, so we
          record what we saw and declare it: whoever reads the file knows that
          the frames are those finished with FIN.
        """
        b = self.v_in.setdefault(sid, bytearray())
        b += data
        # ⛔⛔ AND FROM 21 AUGUST 2026 THE 28 BYTES OF §6.2 END UP IN THE TRACE.
        #
        #    Until this morning the recording carried **only the control
        #    channel**, and on a trace without video the arbiter cannot
        #    conclude anything about **T4** — *«a server that answers
        #    `CANVAS(FITTED)` without touching the stage»*, which is the declared
        #    crack of all of 6.6.  ⚠ `[M]` the first real round against the
        #    product, 21 August: five traces, and on all of them the arbiter
        #    wrote *«after it the recording carries NO
        #    frame: NOT judged»*.  A rule that never has an
        #    input is a rule that is not there.
        #
        # ⛔⛔ AND THE **WHOLE** STREAM IS RECORDED, not just the 28 bytes —
        #     and the first draft did the other thing, for an hour.
        #
        #  It seemed clever: the arbiter judges size, number and codec, which are
        #  all in the header, and the pixels are megabytes nobody reads.
        #  ⛔ **But a 28-byte block marked `fine = 0` tells the arbiter a
        #  false thing**: it says «of this stream I recorded everything that
        #  passed, and it was not finished».  ⇒ The frame judge never
        #  consumed those streams, and the next frame — a legitimate delta —
        #  reached it as **the first of the session**.
        #
        #  `[M]` 21 August 2026, real round on 7721: *«stream 23: the first
        #  frame of the session is a DELTA — §5.2»*.  ⛔ **An accusation against the
        #  PRODUCT born from an incomplete recording of mine**, and it is the worst
        #  thing a bench can do: §11.1 wants the bytes, and a trace
        #  that carries a piece of them while declaring itself whole is no longer an arbiter.
        #
        # ⚠ The price is the size of the file, and it is paid: whoever wants small
        #   traces shortens `--stay`, not the wire.
        if self.reg is not None:
            self.v_reg.add(sid)
            self.reg.add(SERVER, bytes(data), channel=0x03, stream=sid,
                              fine=Recorder.FIN if fine
                              else Recorder.CONTINUE)
        if not fine:
            return
        del self.v_in[sid]
        if len(b) < 28:
            print(f"   [vid]  ⛔ stream {sid} finished with {len(b)} bytes: §6.2 "
                  f"wants 28 of header")
            return
        kind, codec, l, a, nr, instant, inp = struct.unpack("!HHIIIQI", bytes(b[:28]))
        self.v_frames.append((nr, kind == 0x0301, l, a, bytes(b[28:])))

    def _clipboard_stream(self, sid, data, fine):
        """The bytes of a unidirectional SERVER stream, clipboard channel.

        ⛔ The WebTransport preamble is consumed here: `0x40 0x54` plus the
           session varint.  ⚠ And it is kept per stream, because a
           packet can cut it in the middle.
        """
        b = self.app_in.setdefault(sid, bytearray())
        b += data
        while True:
            if len(b) < 6:
                break
            kind, lung = struct.unpack("!HI", b[:6])
            if len(b) < 6 + lung:
                break
            body = bytes(b[6:6 + lung])
            del b[:6 + lung]
            self._clipboard_one(kind, body)
        if fine:
            if b:
                self.app_violations.append(
                    f"clipboard stream {sid} finished with {len(b)} bytes "
                    "that do not make a message (§6.1)")
            self.app_in.pop(sid, None)

    def _audio_datagram(self, d: bytes) -> None:
        """A WebTransport datagram: RFC 9297 prefix, then §6.3.

        ⛔ Every discard has its OWN counter.  «I heard nothing» must be able to
           say *why*: the wrong prefix, the wrong type, the short block
           and the old block are four different defects with the same
           symptom, and without four counters one searches for hours on the wrong
           side.
        """
        # The prefix: a quarter of the identifier of the session stream.
        q, i = _varint(d, 0)
        if q is None:
            self.a_prefix += 1
            return
        if self.session is not None and q != self.session // 4:
            # ⛔ It is not a wrapper detail: a wrong prefix makes the
            #    BROWSER discard the datagram, with no error anywhere
            #    — that is, «the audio does not arrive» and that is all.
            self.a_prefix += 1
            return
        c = d[i:]
        if len(c) < 12:
            self.a_short += 1
            return
        kind = int.from_bytes(c[0:2], "big")
        if kind != 0x0401:
            self.a_type += 1
            return
        codec = int.from_bytes(c[2:4], "big")
        instant = int.from_bytes(c[4:12], "big")
        # §6.3: «the receiver discards datagrams that arrive late compared to
        # those already consumed» — and WHAT «already consumed» means is decided by
        # `--audio-rule`.  ⛔ The default is `old`: with it, these
        # lines do exactly what they did before 23 August 2026.
        was_delivered, _why = self.a_screening.arrival(instant, codec, len(c) - 12)
        self.a_stale = self.a_screening.discarded_old
        self.a_received = self.a_screening.received
        if not was_delivered:
            return
        self.a_byte += len(c) - 12
        if self.a_codec is None:
            self.a_codec = codec
            print(f"   [audio] ⭐ first datagram: codec {codec} "
                  f"({'Opus' if codec == 1 else 'PCM' if codec == 2 else '⛔ unknown'}), "
                  f"{len(c) - 12} bytes of payload, prefix {q} "
                  f"(session {self.session})")
        elif self.a_codec != codec:
            # ⚠ The codec does not change mid-session: §4.3 negotiates it once.
            print(f"   [audio] ⛔ the codec has CHANGED: {self.a_codec} → {codec}")
            self.a_codec = codec
        self.a_blocks.append({"instant": instant, "codec": codec,
                               "byte": bytes(c[12:])})

    def quic_event_received(self, event: QuicEvent) -> None:
        name = type(event).__name__
        # ═══ THE AUDIO — phase 7, `RCP.md` §6.3 ═══════════════════════════
        #
        # ⛔ The datagram is read HERE, before anything else, and is NOT passed
        #    to aioquic's H3 layer: it is a WebTransport datagram, not a pure
        #    HTTP/3 one, and its first field is the RFC 9297 prefix.
        #
        # ⚠ And what this reader does beyond the browser is the REASON
        #   it exists (`PIANO.md` §1.1): the browser says «I hear nothing»;
        #   this one says WHICH rule of §6.3 was violated and at which byte.
        if name == "DatagramFrameReceived":
            self._audio_datagram(event.data)
            return
        # ⛔ THE END OF THE CONNECTION IS PRINTED, ALWAYS.
        #
        #    It is the only line that tells «QUIC's idle cap
        #    closed» from «the server freed the slot leaving the
        #    connection open».  Without it, the fourth round of B3 concluded the second
        #    by looking at /proc, which only says that a sleeping process is
        #    not dead (R8.2).
        if name == "ConnectionTerminated":
            from_us = " — CLOSED BY US, window over" if self.closed_by_us else ""
            print(f"   [quic] connection TERMINATED: code "
                  f"{getattr(event, 'error_code', '?')} · "
                  f"{getattr(event, 'reason_phrase', '') or '(no reason)'}"
                  f"{from_us}")
            self._cade(f"connection TERMINATED ({getattr(event, 'reason_phrase', '') or 'no reason'})")
            self.messages.put_nowait(None)
            return
        if name == "StreamDataReceived" and event.stream_id == self.check:
            self.incoming += event.data
            self._browse()
            if event.end_stream:
                self.finished = True
                self._cade("the control channel has closed")
                self.messages.put_nowait(None)
            # ⛔ AND the event is NOT passed to `aioquic`'s H3 layer.
            #
            #    `[M]` 10 August 2026: passing it on, the first handshake
            #    died with `CONNECTION_CLOSE 0x105 — DATA frame is not
            #    allowed in this state`, that is the CLIENT killing the
            #    connection while the server was working well.
            #
            # ⚠ It is the asymmetry already seen on 9 August: `aioquic` 1.2 can
            #   CREATE a WebTransport stream and cannot RECOGNISE it when
            #   it answers — so its HTTP/3 layer reads `HERE_I_AM` as a
            #   DATA frame on a request stream.  The B2 bench had not
            #   noticed because the echo was four bytes; one hundred and sixteen
            #   are enough to bring everything down.
            return
        # ⛔⭐ THE SERVER'S UNIDIRECTIONAL STREAMS — §2.5, and through here pass the
        #     video (0x03) and the clipboard (0x02).  ⚠ Not all of them are ours: among
        #     the server's unidirectional ones there are the HTTP/3 control channel
        #     and the two QPACK ones, which belong to `aioquic`.  A
        #     WebTransport stream is recognised by its type, `0x54` — which like `0x41`
        #     does not fit in a byte: on the wire they are `0x40 0x54`.
        # ⛔⭐ THE SERVER'S UNIDIRECTIONAL STREAMS — §2.5: through here pass the
        #     video (0x03) and the clipboard (0x02).  ⚠ Not all of them are ours: among
        #     the server's unidirectional ones there are the HTTP/3 control channel
        #     and the two QPACK ones, which belong to `aioquic`.
        #
        # ⛔⛔ AND WE DECIDE ONLY WHEN THERE IS SOMETHING TO DECIDE — three times in one evening
        #      the defect was the same, and it is worth writing down once
        #      and for all: **classifying on bytes that have not arrived yet**.
        #
        #      1. TWO bytes were expected to recognise the preamble, and the
        #         QPACK streams carry ONE ⇒ swallowed, and the server
        #         dismissed us for `TIMED_OUT`;
        #      2. the «other» verdict had no branch of its own ⇒ the video bytes
        #         ended up in the HTTP/3 layer;
        #      3. `[M]` **the first packet of a video stream carries only the
        #         preamble — `40 54 00`, three bytes, payload ZERO** ⇒ we decided
        #         «it is neither clipboard nor video» on a stream that was video, and
        #         threw away all the rest.
        #
        # ⇒ The rule: until the deciding byte has arrived, the state is
        #   «I know it is ours and I do not know yet what it is» — which is a
        #   TRUE state, not a verdict.  ⛔ `LEZIONI.md` §1.9: «I do not know» and «it is
        #   not» must not look the same.
        if name == "StreamDataReceived" and (event.stream_id & 0x03) == 0x03:
            sid = event.stream_id
            if os.environ.get("B3_SPY"):
                print(f"   [spia] uni {sid} genere={self.uni_kind.get(sid)} "
                      f"len={len(event.data)} fin={event.end_stream} "
                      f"primi={bytes(event.data[:6]).hex()}")
            g = self.uni_kind.get(sid)
            if g == "h3":
                pass                       # it belongs to `aioquic`: left to it
            elif g == "wt":
                self._clipboard_stream(sid, event.data, event.end_stream)
                return
            elif g == "video":
                self._video_stream(sid, event.data, event.end_stream)
                return
            elif g == "altro":
                return                     # ours, and this client does not needs it
            elif g == "wt-attesa":
                # The preamble is already here: the byte that gives the channel is missing.
                p = self.uni_pref.setdefault(sid, bytearray())
                p += event.data
                if p:
                    self._decide_channel(sid, bytes(p), event.end_stream)
                return
            else:
                # ⛔ We decide on the FIRST byte: a WebTransport stream starts
                #    with `0x40` (the varint of type 0x54 does not fit in a byte);
                #    any other first byte belongs to `aioquic`, and its bytes
                #    must not pass through here even for one round.
                if not event.data:
                    return
                if event.data[0] != 0x40:
                    self.uni_kind[sid] = "h3"
                else:
                    p = self.uni_pref.setdefault(sid, bytearray())
                    p += event.data
                    if len(p) < 2:
                        return
                    if p[1] != 0x54:
                        self.uni_kind[sid] = "altro"
                        self.uni_pref.pop(sid, None)
                        print(f"   [wt]   ⚠ uni stream {sid} starts with 0x40 "
                              f"0x{p[1]:02x}: it is not WebTransport, and its bytes "
                              f"have been held back")
                        return
                    q, i = _varint(bytes(p), 2)
                    if q is None:
                        return         # the session varint is not all here
                    rest = bytes(p[i:])
                    self.uni_kind[sid] = "wt-attesa"
                    self.uni_pref[sid] = bytearray(rest)
                    if rest:
                        self._decide_channel(sid, rest, event.end_stream)
                    return
        if name == "StreamDataReceived" and event.stream_id == self.session:
            # the session close capsule (§3.1 point 3)
            code, bare = _closing_capsule(event.data)
            if code is not None:
                if bare:
                    # ⛔ The NAKED capsule, without the DATA frame that carries it.
                    #
                    #    It is what this server did until 10 August 2026
                    #    (finding R10.1): on the CONNECT wire capsules
                    #    travel INSIDE DATA frames (RFC 9297), and a browser
                    #    that reads `0x2843` as an HTTP/3 frame type finds it
                    #    unknown and **ignores** it (RFC 9114 §9).  The reason
                    #    did not arrive, and only the FIN remained — that is `code 0`.
                    #
                    # ⭐ The bench reads it anyway, but DECLARES it: a lenient
                    #    client that accepted both forms without saying
                    #    which it saw would hide that defect again, and
                    #    that is the leniency `REVIEWER.md` §5 forbids.
                    print("   [wt]   ⛔ NAKED close capsule, without a DATA "
                          "frame: a browser would ignore it (RFC 9297)")
                self.close_code = code
                print(f"   [wt]   session closed by the server, code {code:#04x}"
                      f" = {REASONS.get(code, '?')}")
                self._cade(f"session closed by the server, code {code:#04x}"
                           f" = {REASONS.get(code, '?')}")
            if event.end_stream:
                self.finished = True
                self._cade("the WebTransport session has closed")
                self.messages.put_nowait(None)
        for ev in self._http.handle_event(event):
            if isinstance(ev, HeadersReceived) and not self.accepted.done():
                self.accepted.set_result(
                    dict(ev.headers).get(b":status", b"?").decode())

    def _browse(self):
        while len(self.incoming) >= 6:
            kind, lung = struct.unpack("!HI", self.incoming[:6])
            if len(self.incoming) < 6 + lung:
                return
            body = bytes(self.incoming[6:6 + lung])
            raw = bytes(self.incoming[:6 + lung])
            del self.incoming[:6 + lung]
            # ⛔ RECORDED HERE, on arrival: see the box on `self.reg`.
            if self.reg is not None:
                self.reg.add(SERVER, raw)
                # ⭐ The instant the arbiter will read in the file, taken where the
                #    file takes it.  ⛔ Not `time.monotonic()` of now: the
                #    `dt` of the grace second is counted between TWO `instant_ms`
                #    of §11.1, and counting it on a different clock would mean
                #    that the delay declared by the bench and the one read
                #    by the arbiter are two different numbers — that is exactly
                #    the error the boundary of the second does not forgive.
                if NAME.get(kind) == "CANVAS":
                    self.last_canvas_ms = self.reg.blocks[-1][6]
                if NAME.get(kind) in ("CANVAS", "CURSOR_SHAPE") \
                        and self.messages.qsize() > 0:
                    # ⚠ «It arrived while there were already others in the queue» is not
                    #   a violation: it is a fact, and whoever watches must
                    #   be able to read it without opening the trace.
                    print(f"   ·  [filo] {NAME.get(kind)} arrived with "
                          f"{self.messages.qsize()} messages already in the queue")
            self.messages.put_nowait((kind, body, raw))


async def should_wait(cli, which, wait=10.0, reg=None):
    m = await asyncio.wait_for(cli.messages.get(), timeout=wait)
    if m is None:
        raise RuntimeError(f"the control channel has closed: {cli.drop}")
    kind, body, raw = m
    name = NAME.get(kind, f"{kind:#06x}")
    # ⛔ WHAT ARRIVES IS RECORDED, NOT WHAT WAS HOPED FOR — finding R8.9.
    #
    #    The recording was written only along the path that succeeds: a
    #    `FAREWELL(ALREADY_ACTIVE_REMOTELY)` made the exception below be raised
    #    BEFORE being put in the trace, and `b3-terza.rcpreg` — that is
    #    the only object the third round exists to produce — never reached
    #    the B4 arbiter.  ⭐ The refusal is a measurement, not an accident.
    #    ⭐ And from 21 August 2026 the `reg.add()` line is NO longer here: it
    #       records on ARRIVAL, inside `Client._browse()`, or the messages that
    #       nobody waits for do not enter the trace (box in `__init__`).
    #       ⚠ `reg` stays in the signature because the callers pass it, and
    #         removing it would be a wider change than needed.
    if which and name != which:
        if name == "FAREWELL":
            reason = body[0] if body else 0
            raise RuntimeError(
                f"FAREWELL instead of {which}: reason {reason:#04x} = "
                f"{REASONS.get(reason, '?')}")
        if name == "REJECTED":
            reason = body[0] if body else 0
            raise RuntimeError(
                f"REJECTED: reason {reason:#04x} = {REASONS.get(reason, '?')}")
        raise RuntimeError(f"expected {which}, arrived {name}")
    return name, body, raw


async def ask_canvas(cli, reg, lar, h, cap):
    """⭐ `FIT_CANVAS(lar, alt)` and the wait for `CANVAS` — RCP.md §7.1.

    Returns `(esito, motivo, tela_lar, tela_alt, ms)`, or `None` if the
    cap expires **with no answer at all**.

    ⛔⛔ THE CAP IS THE MEASUREMENT, NOT A CONVENIENCE.

    §7.1: *«To every `FIT_CANVAS` the server MUST answer with a `CANVAS`,
    successful or not.  A silence leaves the client waiting for ever for an
    answer that will not come, and the symptom is "the application has
    hung"»*.  ⇒ A test client that waited **without a cap**
    would reproduce the symptom instead of measuring it: the bench would stay hung, and
    whoever watches would say «the bench has hung» — which is the same sentence, from the
    wrong side.

    ⚠ And the cap is NOT a protocol rule: §7.1 does not say **within
      how long**.  ⛔ So the expiry is not recorded as a violation by the
      client: what is recorded is the **silence**, and the one to judge it is the arbiter, which
      reads the bytes and the `fine` field of §11.1.  The client measures; the verdict
      belongs to `01-b4-validatore.py`.

    ⚠ And whatever arrives IN THE MEANTIME is recorded — `CURSOR_SHAPE` and the
      frames arrive when they like — because a trace with holes
      cannot be judged: §11.1 wants the bytes, not the ones we were expecting.
    """
    b = wrap(T["FIT_CANVAS"], struct.pack("!II", lar, h))
    cli.send_msg(b)
    reg.add(CLIENT, b)
    print(f"   → FIT_CANVAS {lar}x{h}")
    t0 = time.monotonic()
    expires = t0 + cap
    while True:
        stays = expires - time.monotonic()
        if stays <= 0:
            ms = (time.monotonic() - t0) * 1000
            print(f"   ⛔ NO CANVAS after {ms:.0f} ms: §7.1 wants an answer "
                  f"«successful or not».  ⚠ It is the silence that «leaves the client "
                  f"waiting for ever»")
            return None
        try:
            m = await asyncio.wait_for(cli.messages.get(), timeout=stays)
        except asyncio.TimeoutError:
            continue
        if m is None:
            print(f"   ⛔ the channel closed while I was waiting for the CANVAS: "
                  f"{cli.drop}")
            return None
        kind, body, raw = m
        # ⭐ (recorded on arrival by `Client._browse()`, not here)
        name = NAME.get(kind, f"{kind:#06x}")
        if name != "CANVAS":
            print(f"   ·  in the meantime: {name} ({len(body)} bytes)")
            if name == "FAREWELL":
                rsn = body[0] if body else 0
                print(f"   ⛔ FAREWELL instead of the CANVAS: reason {rsn:#04x} = "
                      f"{REASONS.get(rsn, '?')}")
                return None
            continue
        ms = (time.monotonic() - t0) * 1000
        if len(body) < 10:
            print(f"   ⛔ CANVAS with a body of {len(body)} bytes: §7.1 wants "
                  f"10 (u8, u8, u32, u32) — the bytes are in the trace")
            return None
        es, rsn = body[0], body[1]
        tl, ta = struct.unpack("!II", body[2:10])
        print(f"   ← CANVAS {CANVAS_OUTCOME.get(es, es)}"
              f"/{CANVAS_REASON.get(rsn, rsn)} canvas in force {tl}x{ta} "
              f"after {ms:.0f} ms")
        return es, rsn, tl, ta, ms


def write_video(a, cli):
    """The frames taken from the wire, for a THIRD decoder.

    ⛔ And it is called AFTER the `--stay` wait, not before: at the line where the
       session opens no frame has arrived yet, and an
       empty file would say «the server sends no video» about a server that sends it.
       ⚠ It cost a round, on 17 August 2026 — a bench defect with the
         face of a product defect, the third of the day.
    """
    if not a.video_out or not cli.v_frames:
        if a.video_out:
            print("   [vid]  ⛔ no frame taken from the wire: no file")
        return
    # ⛔ The frames are concatenated IN THE ORDER OF THE NUMBER (§6.2): the streams
    #    are independent and can arrive out of order, and a stream put back
    #    in line badly would give artefacts that would be OURS, the bench's — that is
    #    the wrong answer to the question this file exists to ask.
    in_order = sorted(cli.v_frames, key=lambda f: f[0])
    with open(a.video_out, "wb") as f:
        for _, _, _, _, d in in_order:
            f.write(d)
    keys = sum(1 for x in in_order if x[1])
    print(f"   [vid]  {len(in_order)} frames ({keys} keys), "
          f"{in_order[0][2]}x{in_order[0][3]}, written to {a.video_out}")


def write_clipboard(a, cli):
    """The clipboard outcome, in JSON, for the bench's judge.

    ⛔ And ALL the facts are written, even those not needed for this round:
       «no announcement», «announcement without text» and «text different from the one
       copied» are three defects with the same symptom, and a file that carried
       only the verdict would make them indistinguishable (`LEZIONI.md` §1.9).

    ⛔ And the VIOLATIONS of §7.4 are written even when the round is green: a
       server that delivers the right text while violating the protocol along the
       way is a server the bench must fail — «it works» is not
       «it conforms».
    """
    if not a.clipboard_out:
        return
    outcome = {
        "annunci_dal_server": cli.app_announcements,
        "chiesti_dal_server": cli.app_asked,
        "serviti_al_server": cli.app_served,
        "own_id": cli.app_my_id,
        "mio_testo": cli.app_my_text,
        # ⛔ `None` = nothing arrived, `""` = an empty string arrived.
        #    They are two different facts, and JSON keeps them apart.
        "ricevuto": cli.app_received,
        "violazioni": cli.app_violations,
    }
    with open(a.clipboard_out, "w") as f:
        json.dump(outcome, f, ensure_ascii=False, indent=1)
    print(f"   [app]  outcome written to {a.clipboard_out} "
          f"({len(cli.app_violations)} violations of §7.4)")


def write_audio(a, cli):
    """The audio blocks on disk, and the six counters on screen.

    ⛔ The counters are printed ALWAYS, even at zero: `CODER.md` §3.10 — «a
       denied reading is not a reading that says zero».  A round that
       prints nothing and one that received zero datagrams must look
       different.
    """
    if cli is None:
        return
    print(f"   [audio] received {cli.a_received} · {cli.a_byte} bytes of payload · "
          f"codec {cli.a_codec if cli.a_codec is not None else '(none)'}")
    # ⛔ `stale {n}` STAYS WHERE IT WAS AND AS IT WAS: `07-b64-rete.py` read it
    #    with the regex `stale (\d+)` on this line (that bench was retired on
    #    11 Oct 2026, DECISIONI §10.44, but old logs are still read the same way).  The four of phase 9
    #    are added AT THE END, where no regex of before meets them.
    print(f"   [audio] discarded — short {cli.a_short} · type {cli.a_type} · "
          f"prefix {cli.a_prefix} · old {cli.a_stale}")
    # ⛔ The phase 9 counters are printed ALWAYS and with BOTH
    #    rules, even all at zero: «a denied reading is not a reading that
    #    says zero» (`CODER.md` §3.10).  ⚠ With the old rule `late`,
    #    `report` and `rec` are zero BY CONSTRUCTION — it is not health, it is that
    #    that rule cannot produce them.
    print(f"   [audio] reorder — {cli.a_screening.line()}")
    print(f"   [audio] reorder — {cli.a_screening.counts_line()}")
    if not a.audio_out:
        return
    import base64
    with open(a.audio_out, "w") as f:
        for b in cli.a_blocks:
            f.write(json.dumps({"instant": b["instant"], "codec": b["codec"],
                                "byte": base64.b64encode(b["byte"]).decode()}) + "\n")
    print(f"   [audio] blocks written to {a.audio_out} ({len(cli.a_blocks)})")


def write_trace(a, reg, cli=None):
    """The recording is written early, and REWRITTEN at every stage.

    ⛔ «I have nothing to judge» and «conforming» are two different things: an empty
       file is not written, so whoever looks for it sees that it is not there instead of
       judging zero blocks.

    ⚠⛔ **And from 16 August 2026 it is REWRITTEN, where before it was written once
        only.**  The `scritta` guard was right as long as after `SESSION` this
    program recorded nothing more: now it records the `FIT_CANVAS`, the
    `CANVAS`, the `VIEW` and the closing of the channel — ⛔ and with the guard standing
    **the interesting half of the trace did not reach the file**.  A bench
    that closes the file before doing the thing it must measure hands
    the arbiter a conforming and empty recording.

    ⭐ And the FIN is marked HERE, not in the event that receives it: the server's
       messages go through a queue, and marking the end from the event handler
    would write the closing **before** messages that come after it in the
    trace.  ⛔ It would be a false byte precisely in the field that §11.1 added in order
    not to confuse an end with an interruption.
    """
    if not (a.record and reg.blocks):
        return
    if cli is not None and cli.finished and not getattr(reg, "end_marked", False):
        reg.mark_end(SERVER, Recorder.FIN)
        reg.end_marked = True
    reg.write(a.record)
    reg.written = True
    print(f"   recording: {a.record} ({len(reg.blocks)} blocks)")


def body_hello(audio="opus,pcm", video="h264", prof="8,10"):
    # ⛔ `audio` can be narrowed from the command line, and it is NOT a trick:
    #    it is what a client that cannot do Opus declares.  §4.3 requires
    #    `pcm` on both sides precisely for this — it is «the base always available»,
    #    and the positive control of Opus.  ⇒ `--audio-codec pcm` exercises the
    #    negotiation, it does not bypass it.
    # ⛔ And the VIDEO can be narrowed too, since 17 August 2026: it serves to
    #    exercise the fallback branch without a browser in between.  ⚠ It is not a
    #    trick — it is what a client that cannot decode HEVC
    #    declares, that is **exactly Firefox**.  §4.3 has the server choose
    #    within the intersection, and narrowing the intersection is a use
    #    of the protocol, not a workaround.
    #
    # ⛔⛔⛔ I CHANGED THE YARDSTICK — 23 August 2026, evening (`fasi/09` §14.1).
    #    The default was **`hevc,av1`** and it stayed so when AV1
    #    left the product (20 August, `DECISIONI.md` §1.13-ter): the server
    #    therefore chose **HEVC** in every bench round, while `pagina.html`
    #    (`PREFERENCE = ["hevc", "h264"]`, line 818) declares **only the codecs that
    #    have really PAINTED the probe** — and on Firefox HEVC does not paint.
    #    ⇒ The bench measured a codec the user never receives.
    #    `[M]` same scene, same canvas, same QP 26: **21.18 Mbit/s in HEVC
    #    against 7.92 in H.264**, a factor of **2.7** (`fasi/09` §13.5.1).
    #    ⇒ ⛔ **The bandwidth numbers taken before this line are NOT comparable
    #      with those taken after.**  The old yardstick is redone with
    #      `--video-codec hevc`, and it must be said every time it is used.
    entries = [("video.codec", video), ("video.depth", prof),
            ("audio.codec", audio), ("video.level", "5.1"),
            ("video.max_size", "3840x2160"), ("clipboard.text", "yes"),
            ("input.touch", "no"), ("client.name", "test-client 0.1.0")]
    out = struct.pack("!HH", 1, len(entries))
    for n, v in entries:
        out += s(n) + s(v)
    return out


async def main(a) -> int:
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                            max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    reg = Recorder()
    authority = f"{a.address}:{a.port}"

    print(f"== RCP test client -> https://{authority}{a.path}")
    async with connect(a.address, a.port, configuration=conf,
                       create_protocol=Client) as cli:
        await asyncio.wait_for(cli.wait_connected(), timeout=8)
        cli.open_session(authority, a.path)
        state = await asyncio.wait_for(cli.accepted, timeout=8)
        print(f"   extended CONNECT: :status = {state}")
        if state != "200":
            return 1
        # ⛔ The REAL stream of the control channel ends up in the trace: §11.1
        #    asks for it, and §2.5 rests P3 on it — «a frame on the
        #    control channel stream».  With the `0` written by hand that
        #    check of the arbiter looked at an invented number.
        reg.stream = cli.open_control()
        # ⛔ And the recorder is handed to the CLIENT, because from here on the
        #    server's bytes are recorded where they arrive (box in
        #    `Client.__init__`).  ⚠ Before this line nothing can have
        #    arrived: the control channel did not exist.
        cli.reg = reg

        # ⛔ THE TRACE IS WRITTEN EVEN WHEN THE HANDSHAKE DOES NOT SUCCEED.
        #
        #    Finding R8.9: the third round of B3 exists to produce ONE object —
        #    the recording of whoever received the `FAREWELL(0x0F)` — and that
        #    recording was never written, because the exception went off
        #    earlier.  ⭐ The B4 validator is the arbiter of the refusal too.
        try:
            # ── HELLO ────────────────────────────────────────────────────────
            b = wrap(T["HELLO"], body_hello(a.audio_codec, a.video_codec, a.video_depth))
            cli.send_msg(b)
            reg.add(CLIENT, b)
            name, body, raw = await should_wait(cli, "HERE_I_AM", reg=reg)
            version = struct.unpack("!H", body[:2])[0]
            print(f"   HERE_I_AM: version {version}")

            # ── CREDENTIALS ─────────────────────────────────────────────────
            body_c = s(a.user) + s(a.password)
            b = wrap(T["CREDENTIALS"], body_c)
            # §11.1: the password is obscured, the length stays true
            ini = 6 + 2 + len(a.user.encode()) + 2
            here = len(a.password.encode())
            imp = hashlib.sha256(a.password.encode()).digest()
            cli.send_msg(b)
            reg.add(CLIENT,
                         b[:ini] + bytes([0x2A]) * here + b[ini + here:],
                         [(ini, here, imp)])
            t0 = time.monotonic()
            name, body, raw = await should_wait(cli, "ADMITTED", wait=20, reg=reg)
            ms = (time.monotonic() - t0) * 1000
            # ⭐ §4.4-bis: the fixed delay applies TO ADMITTED TOO.  It is
            #    timed here because no other bench sees it, and a
            #    regression that removed it would make nothing fail.
            print(f"   ADMITTED after {ms:.0f} ms"
                  + ("   ⭐ the fixed second is there" if ms >= 1000 else
                     "   ⛔ LESS THAN ONE SECOND: §4.4-bis violated"))
            if ms < 1000:
                write_trace(a, reg, cli); write_audio(a, cli); write_video(a, cli)
                return 1

            # ── ATTACH ─────────────────────────────────────────────────────
            b = wrap(T["ATTACH"],
                         struct.pack("!IIII", a.width, a.height,
                                     a.width, a.height) + s(a.layout))
            cli.send_msg(b)
            reg.add(CLIENT, b)
            name, body, raw = await should_wait(cli, "SESSION", reg=reg)
        except Exception:
            write_trace(a, reg, cli); write_audio(a, cli); write_video(a, cli)
            raise
        state_s = body[0]
        lar, h = struct.unpack("!II", body[1:9])
        n = struct.unpack("!H", body[9:11])[0]
        desktop = body[11:11 + n].decode()
        print(f"   ⭐ SESSION: state={state_s} canvas={lar}x{h} desktop={desktop}")

        # ═══════════════════════════════════════════════════════════════════
        # ⭐⛔ THE CANVAS PATH — sub-phase 6.6, 16 August 2026
        #
        #    ⛔ *«Neither of the two sends an `FIT_CANVAS`»*: from here on it is no
        #       longer true.  And there is one more reason to do it **at attach**,
        #       and it dates from 15 August: `DECISIONI.md` §5.0-sexies has the
        #       client ask for *«the canvas of its own window at the attach of every
        #       session, by itself»* — so this is not a laboratory
        #       test, it is what the real client does every time.
        #
        # ⚠ And the in-flight count is kept HERE TOO, not only in the arbiter: §6.2
        #   ties to the count the way the client treats frames, and a
        #   test client that did not keep it could not notice a
        #   `CANVAS` it did not ask for.
        canvas_alive = (lar, h)
        # ⭐ The canvas in force **BEFORE** the last `CANVAS(FITTED)`: it is the one
        #    on which the in-flight coordinates of §7.1 are still valid, and it is
        #    the only number from which the grace-second case can be built
        #    without making it up.  ⛔ `None` as long as no adaptation has
        #    succeeded: then the scene does not exist, and we say so instead of faking it.
        canvas_prev_adapted = None
        outcomes_canvas = []
        if a.fit:
            for al, aa, when in a.fit:
                if when:
                    # ⭐ It is the **live** resize: the session is already
                    #    alive and frames pass in between.  ⚠ We wait with
                    #    our eyes open — a `sleep` would not notice that
                    #    the session dropped in the meantime, and the measurement
                    #    of the `FIT_CANVAS` would be taken on a dead connection
                    #    (findings R8.2, R8.4).
                    print(f"   ·  waiting {when} s with the session alive")
                    try:
                        await asyncio.wait_for(cli.dropped.wait(), timeout=when)
                        print(f"   ⛔ dropped before the canvas could be asked for: "
                              f"{cli.drop}")
                        write_trace(a, reg, cli); write_audio(a, cli); write_video(a, cli)
                        return 4
                    except asyncio.TimeoutError:
                        pass
                before_this = canvas_alive
                r = await ask_canvas(cli, reg, al, aa, a.wait_canvas)
                outcomes_canvas.append(r)
                if r is not None and r[0] == 1:
                    canvas_prev_adapted = before_this
                if r is None:
                    # ⛔ The silence is RECORDED and we exit with a code of its own: it is
                    #    the scene of §7.1, and it must be told apart from «the session
                    #    dropped» (4) and from «all fine» (0).
                    write_trace(a, reg, cli); write_audio(a, cli); write_video(a, cli)
                    return 5
                canvas_alive = (r[2], r[3])
        # ═══════════════════════════════════════════════════════════════════
        # ⭐⛔ THE GRACE SECOND OF §7.1, AIMED AT THE SERVER
        #     — 22 August 2026, and until this morning it had never been done.
        #
        # §7.1: *«After sending `CANVAS(FITTED)` the server MUST accept
        # for **one second** valid input coordinates on the
        # **previous** canvas, saturating them to the new one and writing it in the log;
        # once that second has passed, they are `PROTOCOL_ERROR`»*.
        #
        # ⛔⛔ THE TRAP, AND IT MUST BE DEFUSED BEFORE CHOOSING THE DELAY.
        #
        #     The rule belongs to the **SERVER**; the recording is taken by the
        #     **CLIENT**.  The interval seen here is SHORTER than the true one
        #     by half a network round trip per side (§11.1, *«the recorded time is
        #     WHOEVER RECORDS'»*).  ⇒ A case «inside the second» set at 0.95 s
        #     could be 1.02 s for the server, and the bench would accusations the
        #     product of a defect it does not have — or, worse, would acquit itself
        #     on its own.
        #
        # ⭐ The cure is not a calculation: it is **staying away from the boundary**, and
        #    declaring why.  Whoever calls this client chooses the delay;
        #    here the margin is printed, so a badly chosen delay shows
        #    instead of producing a verdict.
        #
        # ⛔ AND THE COORDINATE IS NOT MADE UP: it is **the last pixel of the
        #    previous canvas**, `(prec_l - 1, prec_a - 1)`.  Two reasons, and the
        #    second is worth more than the first:
        #      · it is valid on the previous canvas **by definition** (§7.3: «0 <=
        #        x < canvas_width»), so the case is that of §7.1 and not
        #        «a wrong coordinate» — which §7.1 does NOT cover, and the server
        #        has a line on purpose to say so;
        #      · saturated, it must land **exactly** on `(new_w - 1,
        #        new_h - 1)`, that is on a KNOWN point.  ⭐ It is the check that
        #        crosses the conversion: a server that refused the
        #        coordinate *saying so in the log* but applied it anyway
        #        would pass the arbiter, and would not pass this.
        if a.old_pointer is not None:
            if canvas_prev_adapted is None:
                print("   ⛔ --old-pointer, but no CANVAS(FITTED) "
                      "succeeded: there is no «previous canvas», and a "
                      "coordinate chosen at random would test ANOTHER rule "
                      "(§7.3 «outside the canvas»), not the grace second")
                write_trace(a, reg, cli); write_audio(a, cli); write_video(a, cli)
                return 6
            px = canvas_prev_adapted[0] - 1
            py = canvas_prev_adapted[1] - 1
            if px < canvas_alive[0] and py < canvas_alive[1]:
                print(f"   ⛔ ({px},{py}) is INSIDE the canvas in force "
                      f"{canvas_alive[0]}x{canvas_alive[1]}: the scene of §7.1 is not "
                      f"exercised at all — what is needed is a new canvas smaller "
                      f"than the previous {canvas_prev_adapted[0]}x"
                      f"{canvas_prev_adapted[1]}")
                write_trace(a, reg, cli); write_audio(a, cli); write_video(a, cli)
                return 6
            # The expected saturation, computed as §7.1 describes it: «to the last
            # valid pixel».
            sx = px if px < canvas_alive[0] else canvas_alive[0] - 1
            sy = py if py < canvas_alive[1] else canvas_alive[1] - 1
            delay_ms = int(round(a.old_pointer * 1000))
            print(f"   ⛔ EXPECTED, declared BEFOREHAND: POINTER ({px},{py}) — "
                  f"valid on the previous canvas {canvas_prev_adapted[0]}x"
                  f"{canvas_prev_adapted[1]}, outside the one in force "
                  f"{canvas_alive[0]}x{canvas_alive[1]} — at {delay_ms} ms from the "
                  f"CANVAS(FITTED)")
            if delay_ms > 1000:
                print(f"      ⇒ beyond the grace second, and the margin is "
                      f"{delay_ms - 1000} ms.  ⛔ The server MUST refuse: "
                      f"ITS interval is even longer than this")
            else:
                print(f"      ⇒ inside the second, and the margin is "
                      f"{1000 - delay_ms} ms — that is how much network round trip it "
                      f"would take to push it beyond.  ⛔ The server MUST "
                      f"saturate to ({sx},{sy}) and write it in the log")
            if cli.last_canvas_ms is None:
                print("   ⛔ no instant recorded for the CANVAS: I do not know from "
                      "when to count")
                write_trace(a, reg, cli); write_audio(a, cli); write_video(a, cli)
                return 6
            target = cli.last_canvas_ms + delay_ms
            # ⛔ WE WAIT WITH OUR EYES OPEN — findings R8.2/R8.4.  A
            #    `sleep` would not notice that the session died in the
            #    meantime, and the `POINTER` would leave on an already
            #    closed connection: the bench would measure itself.
            dropped_before = False
            while True:
                stays = (target - reg.instant()) / 1000.0
                if stays <= 0:
                    break
                try:
                    await asyncio.wait_for(cli.dropped.wait(), timeout=stays)
                    dropped_before = True
                    break
                except asyncio.TimeoutError:
                    pass
            if dropped_before:
                print(f"   ⛔ the session dropped BEFORE the POINTER: "
                      f"{cli.drop} — the second rule was not "
                      f"exercised")
                write_trace(a, reg, cli); write_audio(a, cli); write_video(a, cli)
                return 4
            pid, pms = cli.send_pointer(px, py)
            dt = None if pms is None else pms - cli.last_canvas_ms
            print(f"   → POINTER id={pid} ({px},{py}) — recorded dt "
                  f"{dt} ms from the CANVAS(FITTED).  ⚠ It is the number the arbiter "
                  f"will read: the SERVER's interval is longer than this")

            # ═══════════════════════════════════════════════════════════════
            # ⭐⛔ THE THIRD WITNESS: A FRAME IS ASKED FOR, BECAUSE A
            #     STILL DESKTOP DOES NOT SEND ANY.
            #
            # `[M]` 22 August 2026, first real round on 7721: after the
            # `POINTER` the trace carries **zero** frames — the
            # monitorless GNOME session has nothing that moves, and the server
            # ships only what changes.  ⇒ The `input` field of §6.2 —
            # *«the identifier of the last INJECTED input»*, the only
            # witness of the injection that lives **on the wire** — could not say
            # anything, and «it did not inject» and «no
            # frame passed» looked the same (`LEZIONI.md` §1.9).
            #
            # ⛔ And it is asked for AFTER the pointer, with a delay: the input
            #    channel and the control one are **two independent streams**
            #    (§2.5) and nothing orders their delivery.  Without waiting, the key
            #    could be captured BEFORE the input is injected, and
            #    an `input = 0` would mean «I do not know», not «not injected».
            #
            # ⚠ And if the session has already dropped nothing is sent: in the round
            #   «beyond the second» that is the RIGHT path, and insisting on
            #   a dead connection would produce a bench error instead
            #   of a measurement.
            if a.key_after:
                try:
                    await asyncio.wait_for(cli.dropped.wait(),
                                           timeout=a.key_after)
                    print(f"   ·  no REQUEST_KEY: the session has already "
                          f"dropped ({cli.drop}) — ⭐ after a POINTER beyond "
                          f"the second it is what §7.1 wants")
                except asyncio.TimeoutError:
                    last = max((f[0] for f in cli.v_frames), default=0)
                    b = wrap(T["REQUEST_KEY"],
                                 struct.pack("!I", last))
                    cli.send_msg(b)
                    reg.add(CLIENT, b)
                    print(f"   → REQUEST_KEY({last}) — ⚠ it is not the scene "
                          f"of §5.2: it serves to let ONE frame through, so that "
                          f"the `input` field of §6.2 can bear witness")

        if a.view:
            # ⚠ `VIEW` MUST NOT change the canvas (§7.1).  If after this one
            #   a `CANVAS` arrives, the wire says so and the arbiter accuses it: here we do not
            #   judge, we record.
            vl, va = a.view
            b = wrap(T["VIEW"], struct.pack("!II", vl, va))
            cli.send_msg(b)
            reg.add(CLIENT, b)
            print(f"   → VIEW {vl}x{va}   ⚠ must not change the canvas")

        write_trace(a, reg, cli); write_audio(a, cli); write_video(a, cli)

        # ⛔ THE «ATTACHED» SIGNAL, AND WHY A PRINTED LINE IS NOT ENOUGH.
        #
        #    On 10 August 2026 the third round of B3 waited for the word
        #    «SESSION» in the log of this program — and Python **buffers
        #    stdout when it is redirected to a file**: that line appeared
        #    only at process exit, that is **at the exact instant the
        #    client detached**.
        #
        # ⚠ The bench said «the first is attached» by reading a truth that had just
        #   expired, and the second connection always arrived to a free slot.
        #   ⛔ A check that looks right and measures the wrong instant: the
        #      red ended up on the server, which had nothing to do with it.
        #
        # ⭐ A file written and closed is a fact; a printed line is a
        #    hope about the moment someone will see it.
        if a.signal:
            with open(a.signal, "w") as f:
                f.write("attaccato\n")

        # ═══ THE CLIPBOARD — §7.4 ═════════════════════════════════════════
        #
        # ⛔ And is the `device → session` direction announced BEFORE writing
        #    the signal?  NO, and the reason is the order of the two sides of the bench:
        #    the signal says «I am attached», and the side that copies with `xclip`
        #    waits precisely for that.  Announcing before would mean announcing
        #    when the other side is not yet ready to look.
        if a.click:
            # ⛔ We wait: the window must already be on the screen, or the click
            #    lands on the background and nobody takes the focus.
            px, _, py = a.click.partition(",")
            print(f"   [clic] waiting {a.click_after} s, then clicking at ({px},{py})")
            await asyncio.sleep(a.click_after)
            cli.send_pointer(int(px), int(py))
            await asyncio.sleep(0.2)
            cli.send_button(True)
            await asyncio.sleep(0.12)
            cli.send_button(False)
            print("   [clic] ⭐ done: that window now has the focus")

            if a.click_every > 0:
                async def still():
                    while True:
                        await asyncio.sleep(a.click_every)
                        cli.send_pointer(int(px), int(py))
                        await asyncio.sleep(0.15)
                        cli.send_button(True)
                        await asyncio.sleep(0.1)
                        cli.send_button(False)

                asyncio.ensure_future(still())
                print(f"   [clic] and I redo it every {a.click_every} s")

        if a.clipboard_copy:
            cli.clipboard_announce(a.clipboard_copy)

        if a.clipboard_wait:
            # ⛔ WE WAIT FOR AN ANNOUNCEMENT, AND THEN ASK FOR IT — §7.4: «one announces
            #    and one asks, instead of pushing».  ⚠ And the two steps are counted
            #    separately: «no announcement arrived» and «the announcement
            #    arrived and the text did not» are two different defects with the same
            #    symptom (`LEZIONI.md` §1.9).
            print(f"   [app]  waiting for an announcement from the server, up to "
                  f"{a.clipboard_wait} s")
            fine = time.monotonic() + a.clipboard_wait
            while not cli.app_announcements and time.monotonic() < fine:
                cli.app_event.clear()
                try:
                    await asyncio.wait_for(cli.app_event.wait(),
                                           timeout=max(0.1, fine - time.monotonic()))
                except asyncio.TimeoutError:
                    break
            if not cli.app_announcements:
                print("   [app]  ⛔ no announcement from the server in time")
            else:
                cli.clipboard_ask()
                fine = time.monotonic() + a.clipboard_wait
                while cli.app_received is None and time.monotonic() < fine:
                    cli.app_event.clear()
                    try:
                        await asyncio.wait_for(cli.app_event.wait(),
                                               timeout=max(0.1, fine - time.monotonic()))
                    except asyncio.TimeoutError:
                        break
                if cli.app_received is None:
                    print("   [app]  ⛔ the announcement arrived and the text did NOT")
                else:
                    print(f"   [app]  ⭐ received {len(cli.app_received)} "
                          f"characters: «{cli.app_received[:60]}»")
        write_clipboard(a, cli)
        if a.stay:
            # ⛔ WE STAY WITH OUR EYES OPEN, NOT SLEEPING — findings R8.2/R8.4.
            #
            #    An `asyncio.sleep` notices nothing: the connection
            #    could drop from QUIC's idle cap, or the session
            #    could be closed by the server to make room for another, and
            #    this program exited 0 saying «I stayed attached».
            #    On that exit code the third round concluded «no live client
            #    is ousted», which is invariant I2 to the letter.
            #
            # ⚠ Nothing is sent to make sure: the fourth round measures
            #   the SILENCE clock, and one byte would reset it.  We just listen
            #   — which is precisely the receiving side.
            print(f"   staying attached for {a.stay} s"
                  + (f", making myself heard every {a.alive} s" if a.alive else ""))
            try:
                if a.alive:
                    # ⛔⛔ AND THIS OPTION IS A TRAP — 16 August 2026.
                    #
                    #    `VIEW` (0x0008) is in the protocol, ⛔ but THIS server
                    #    does not needs it yet: it answers `PROTOCOL_ERROR` and
                    #    CLOSES.  `[M]` Over twenty measurement rounds, three sessions
                    #    died at 8 seconds because of this line, and the
                    #    times came out as «10.4 s» — a number of the bench, not
                    #    of the product.
                    #
                    # ⭐ The lesson, which the user put better: *«for tests
                    #    use the browser, not the bench — it is the only way to
                    #    measure what really happens»*.  A test client
                    #    that sends what the real client does not send does not
                    #    measure the product: it measures itself.
                    raise SystemExit(
                        "⛔ --alive sends VIEW (0x0008), which this server does not "
                        "serve: it would close the session with PROTOCOL_ERROR. "
                        "To measure times, use the BROWSER.")
                    # ⭐ `--alive`: an IDENTICAL `VIEW` is sent every so often, only
                    #    so as not to be detached by the silence clock (§5.3).
                    #
                    # ⛔ OFF BY DEFAULT, and that is the point: the default
                    #    behaviour — keeping quiet — serves to MEASURE that clock, and
                    #    the comment above has said so since 10 August.  ⚠ Whoever
                    #    turns it on is measuring something else: the scene in which the
                    #    client is there and working, which is that of the real browser.
                    #
                    # ⚠ And `VIEW` with the same numbers is a semantic no-op: it
                    #   changes nothing, it is legitimate with an active session (§7.1), and it
                    #   asks nothing of the stage — unlike `REQUEST_KEY`,
                    #   which would make it redo a key and would distort the measurement.
                    expired = asyncio.get_event_loop().time() + a.stay
                    while asyncio.get_event_loop().time() < expired:
                        how_much = min(a.alive, expired - asyncio.get_event_loop().time())
                        try:
                            await asyncio.wait_for(cli.dropped.wait(), timeout=how_much)
                            break
                        except asyncio.TimeoutError:
                            pass
                        cli.send_msg(wrap(0x0008,
                                           struct.pack("!II", a.width,
                                                       a.height)))
                    if not cli.dropped.is_set():
                        raise asyncio.TimeoutError
                else:
                    await asyncio.wait_for(cli.dropped.wait(), timeout=a.stay)
            except asyncio.TimeoutError:
                # ⛔ The flag is raised BEFORE leaving: leaving here
                #    `connect()` closes the connection, and the event that follows
                #    must already be recognisable as ours.
                cli.closed_by_us = True
                print(f"   ⭐ still attached after {a.stay} s: nothing dropped")
                write_trace(a, reg, cli); write_audio(a, cli); write_video(a, cli)
                return 0
            print(f"   ⛔ I did NOT stay attached: {cli.drop}")
            write_trace(a, reg, cli); write_audio(a, cli); write_video(a, cli)
            return 4
        write_trace(a, reg, cli); write_audio(a, cli); write_video(a, cli)
        return 0


# ---------------------------------------------------------------------------
# ⛔ THE PASSWORD MUST NOT PASS THROUGH THE COMMAND LINE — defect **D12**,
#    cured on 12 August 2026.
#
# ⛔ `--password` ends up in the process `argv`, that is in `/proc/<pid>/cmdline`,
#    which on Linux is **readable by anyone**: a `ps` run by another
#    user during the round prints it in full.
#
# ⭐ The good path already existed in house and this is its extension, not a
#    second way: `01-b10-secondo-utente.py` takes `--parola-file`, a `0600`
#    file that the launcher writes with `printf` — a shell **builtin**,
#    so not even the writing goes through a process with the password in `argv` —
#    and deletes with a `trap`.
#
# ⚠ And `--password` has NOT been removed, and not out of laziness: some callers not
#   yet cured still pass it, and breaking them **silently** would be worse
#   than the defect.  ⛔ But the fallback is DECLARED (`CODER.md` §4.2): a silent
#   fallback produces two behaviours under the same label, which is the
#   form **E2** — and here the two behaviours are «the secret is protected» and
#   «the secret is public».  ⇒ whoever passes `--password` gets told.
#
# ⚠ And the warning looks at `sys.argv`, not at the value: the default written in the
#   code is in no command line, and telling it the opposite would be an
#   alarm one learns to ignore.
# ══════════════════════════════════════════════════════════════════════════
# ⭐⭐ `--certify` — THE SELF-TEST OF THE SCREENING, WITH NO NETWORK AND NO MACHINE
#
# ⛔⛔ R13 — EVERY EXPECTATION IS A PREDICATE WRITTEN BEFOREHAND.  Not a sentence printed
#      next to the numbers (that stays true «when read» whatever comes out),
#      but a function `(numbers) -> (passes, why)`.  `passes=None` is the third
#      outcome: **the bench refuses to judge**, and it is not a green.
#
# ⛔ And the clock is FAKE, for two reasons that both hold:
#    · the screening depends on time (the cushion is 250 ms), and with the
#      real clock this test would last minutes and be different every time;
#    · a bench that sleeps also measures the load of the machine hosting it.
PCM_BYTE = 960                  # `[S]` RCP.md:1299 — 480 samples, 5 ms
PCM_STEP_US = 5000


class FakeClock:
    """Time is moved by the bench, not by the system."""

    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


def _p(cond, why):
    return (bool(cond), why)


def _round(rule, arrivals, decode_delay_s=0.0):
    """`arrivals` = [(seconds from the start, istante_us)].  Returns `(vaglio, exited)`.

    ⛔ `exited` is the LIST of the delivered `instant`s, not the count: it serves to
       verify that neither of the two rules **fabricates** a block that was not on
       the wire, and that a duplicate does not come out twice.
    """
    clk = FakeClock()
    t0 = clk.t
    v = AudioSieve(rule=rule, clock=clk,
                    decode_delay_s=decode_delay_s)
    exited = []
    for when, ist in arrivals:
        clk.t = t0 + when
        ok, _why = v.arrival(ist, 2, PCM_BYTE)
        if ok:
            exited.append(ist)
    return v, exited


def _counts(v):
    return {"on_wire": v.on_wire, "received": v.received,
            "delivered": v.delivered, "stale": v.discarded_old,
            "late_audio": v.discarded_late, "out": v.out_of_order,
            "duplicates": v.duplicates, "recovered": v.recovered,
            "missed": v.missed, "volte": v.missed_times,
            "rearms": v.rearms,
            "purity": None if v.purity is None else round(v.purity, 4)}


def _sorted(n):
    """n PCM blocks of 5 ms, in order, with no losses: the denominator."""
    return [(i * 0.005, i * PCM_STEP_US) for i in range(n)]


def _reordered(n, k):
    """Reorder by `k` places: groups of `k+1` reversed.

    ⭐ It is the reorder on which the OLD rule has a COMPUTABLE purity, not
       one measured afterwards: within each reversed group only the first
       to arrive is the newest, the other `k` are behind and the old
       rule throws them all away ⇒ **expected purity = 1/(k+1) exactly**.
    ⛔ This is the expectation written beforehand, and it is stronger than a magic number:
       if the count does not add up, either the reorder is not what I believe or the old
       rule is not what I believe.
    """
    report = []
    for i in range(0, n, k + 1):
        report += list(range(i, min(i + k + 1, n)))[::-1]
    return [(p * 0.005, j * PCM_STEP_US) for p, j in enumerate(report)]


def _with_duplicates(n, every):
    """In order, but every `every`-th block arrives TWICE.

    ⚠ The twin arrives 1 ms later and **does not consume a slot**: if it did,
      the real blocks would slip by 5 ms each and after 50 duplicates the
      accumulated delay would exceed the cushion ⇒ a rearm of the anchor, and the case would
      no longer measure the duplicates but the drift the bench itself fabricated.
    """
    a = []
    for i in range(n):
        a.append((i * 0.005, i * PCM_STEP_US))
        if i and i % every == 0:
            a.append((i * 0.005 + 0.001, i * PCM_STEP_US))
    return a


def _with_holes(n, every):
    """REAL holes: the blocks do not arrive at all, and those present stay in their place.

    ⛔ Block 0 is ALWAYS there, and it is a choice of the bench: a hole **at the head**
       cannot be counted — there is no `last_instant` from which to measure the
       jump — and mixing it with the holes in the middle would give an expectation off by 1.
       ⭐ The blind spot has a case of its own (4-blind).
    """
    return [(i * 0.005, i * PCM_STEP_US)
            for i in range(n) if i == 0 or i % every]


def _old_literal(instants):
    """⛔ THE CODE OF BEFORE, TRANSCRIBED TO THE LETTER from `_audio_datagram`
       as it was until 22 August 2026.  It serves one thing only: proving that
       `--audio-rule old` has changed NOTHING.  Not to be touched."""
    ric = stale = 0
    prev = None
    exited = []
    for ist in instants:
        if prev is not None and ist <= prev:
            stale += 1
            continue
        prev = ist
        ric += 1
        exited.append(ist)
    return ric, stale, exited


def certify():
    outcomes = []

    def test_case(name, passes, why, numbers=None):
        outcomes.append({"case": name, "passes": passes, "why": why,
                      "numbers": numbers})
        sign = "OK " if passes else ("-- " if passes is None else "⛔ NO")
        print(f"  {sign} {name}")
        print(f"      expected: {why}")
        if numbers:
            print(f"      seen:     {numbers}")

    print("== ⭐ `01-b3-cliente.py --certify` — the audio screening, "
          "with no network and no test machine")
    print(f"   PCM of {PCM_BYTE} bytes = {PCM_STEP_US} us (RCP.md:1299), "
          f"cushion {AUDIO_CUSHION_MS} ms, fake clock")

    # ── 1 · in order: the two rules must be INDISTINGUISHABLE ──────────────
    print("\n  ── 1 · sequence in order ──")
    av, uv = _round("old", _sorted(840))
    an, un = _round("new", _sorted(840))
    test_case("1 · in order ⇒ the two rules give the SAME result",
         _counts(av) == _counts(an) and uv == un and av.purity == 1.0,
         "every counter equal, same list of outputs, purity 1.0000 "
         "(⛔ if they differ, the new rule has a defect on the easy case)",
         {"old": _counts(av), "new": _counts(an)})

    # ── 2 · reorder by 1, 2, 3 (and 7) places ──────────────────────────────
    print("\n  ── 2 · reordered sequence ──")
    for k in (1, 2, 3, 7):
        av, uv = _round("old", _reordered(840, k))
        an, un = _round("new", _reordered(840, k))
        expected_v = 1.0 / (k + 1)
        backlog = 840 - 840 // (k + 1)
        passes = (abs(av.purity - expected_v) <= 0.005
                 and an.purity >= 0.95
                 and an.out_of_order == backlog
                 and an.discarded_old == 0 and an.duplicates == 0
                 and sorted(un) == [i * PCM_STEP_US for i in range(840)])
        test_case(f"2.{k} · reorder by {k} places ⇒ the old one throws away, the new one keeps",
             passes,
             f"old purity = 1/(k+1) = {expected_v:.4f} (±0.005) · "
             f"new purity ≥ 0.95 · fuori_ordine = {backlog} · "
             f"vecchi 0 · and the output contains ALL 840 `instant`s",
             {"purezza_vecchia": round(av.purity, 4),
              "purezza_nuova": round(an.purity, 4),
              "old": _counts(av), "new": _counts(an)})

    # ── 3 · duplicates: counted, and never played twice ────────────────────
    print("\n  ── 3 · duplicates ──")
    arrivals = _with_duplicates(840, 10)
    expected_dup = len(arrivals) - 840
    for rule in ("old", "new"):
        v, u = _round(rule, arrivals)
        passes = (v.duplicates == expected_dup and len(u) == len(set(u))
                 and len(u) == 840)
        test_case(f"3.{rule} · {expected_dup} duplicates ⇒ counted, and never twice "
             "at the output",
             passes,
             f"doppioni = {expected_dup} · no repeated `instant` at the output · "
             f"840 delivered (⛔ a duplicate played twice doubles the "
             "signal, which §6.3 does not allow)",
             _counts(v))

    # ── 4 · real holes: neither of the two must FABRICATE audio ────────────
    print("\n  ── 4 · real holes ──")
    arrivals = _with_holes(840, 7)
    shipped = [ist for _q, ist in arrivals]
    expected_missed = 840 - len(shipped)
    for rule in ("old", "new"):
        v, u = _round(rule, arrivals)
        passes = (v.missed == expected_missed and u == shipped
                 and v.delivered == len(shipped)
                 and v.recovered == 0)
        test_case(f"4.{rule} · {expected_missed} blocks NEVER arrived ⇒ `missed` "
             "rises and nothing is fabricated",
             passes,
             f"mancati = {expected_missed} · consegnati = {len(shipped)} · "
             "at the output ONLY the `instant`s that were on the wire · recuperati 0",
             _counts(v))
    # ⛔⭐ THE BLIND SPOT, AND IT IS DECLARED INSTEAD OF HIDDEN — found by
    #     this bench on 23 August 2026, and it was a red that was right.
    #     The datagrams lost BEFORE the first one that arrives cannot be counted:
    #     `missed` measures the distance between two `instant`s, and without the first there
    #     is no distance.  ⚠ It is a limit of the PAGE, not of the
    #     translation (`src/pagina.html`:6550, `a.last_instant !== undefined`).
    #     ⇒ A bench that asked «missed == all the holes» on a sequence
    #     that starts with a hole would give red to the product for a defect of its own.
    blind = [(i * 0.005, i * PCM_STEP_US) for i in range(3, 200)]
    v, u = _round("new", blind)
    test_case("4-blind · ⚠ the 3 holes AT THE HEAD are not counted, and it is not a defect",
         v.missed == 0 and v.delivered == len(blind),
         "mancati 0 (⛔ there is no earlier `instant` from which to measure the "
         "jump: it is a declared limit, not a fault) · all delivered",
         _counts(v))

    # ── 5 · and the block that arrived REALLY too late ─────────────────────
    #
    # ⛔⛔ THIS IS THE CASE THAT PROVES THE CURE IS NOT «I KEEP EVERYTHING».
    #     If the new rule kept this one too, it would not be a cure: it would be
    #     the removal of a check.
    #
    # ⚠ And the cases are TWO, because in the page the counters are two and fall
    #   at different points of the path:
    #     5a · the place passed ALREADY ON THE WIRE ⇒ `discarded_old`
    #          (`src/pagina.html`:5999-6001 is in `plays()`; the twin on the wire
    #          is :6514, and there the counter is `discarded_old`);
    #     5b · the place passed WHILE WE WERE DECODING IT ⇒ `discarded_late`.
    #   ⛔ Calling them both «late» would be convenient and wrong: the first
    #     is §6.3 to the letter, the second is the safety net after the
    #     decoder, and if one day they were confused nobody would know any more
    #     whether what throws away is the wire or the machine.
    # ⭐ AND THE MARGIN CALCULATION, written here because without it the case goes wrong.
    #    The anchor hooks INSIDE `_delivery`, that is **after** decoding:
    #    `base = now + delay + cuscino - t`.  ⇒ A block that arrives `Δ`
    #    late on its own place is discarded
    #      · ON THE WIRE   if  Δ > cushion + delay   (the screening looks at `now`);
    #      · AT DELIVERY   if  Δ > cushion           (the screening looks at `now + delay`).
    #    ⇒ The window of `discarded_late` is exactly
    #      `cushion < Δ ≤ cushion + delay`, and with no decoding delay it is
    #      EMPTY — which is T3 said in numbers.
    print("\n  ── 5 · the block really too late ──")
    n, i_late = 200, 195
    base = _sorted(n)
    its_slot = i_late * 0.005          # when it should have arrived
    last_arrival = base[-1][0]
    cushion = AUDIO_CUSHION_MS / 1000.0
    # 5a · Δ = 300 ms > cushion 250 and delay 0 ⇒ it passed ALREADY ON THE WIRE.
    belated = [(its_slot + 0.300, i_late * PCM_STEP_US)]
    assert belated[0][0] > last_arrival    # it must be the last to arrive
    av, uv = _round("old", base + belated)
    an, un = _round("new", base + belated)
    test_case(f"5a · Δ = 300 ms > cushion {AUDIO_CUSHION_MS} ⇒ the place passed "
         "ON THE WIRE, and the new one DISCARDS it",
         (an.discarded_old == 1 and an.out_of_order == 0
          and an.delivered == n and un == [i * PCM_STEP_US for i in range(n)]
          and av.discarded_old == 1 and av.delivered == n),
         "new: vecchi 1 · fuori 0 · consegnati 200, and the late one is NOT "
         "in the output — old: vecchi 1 · consegnati 200",
         {"old": _counts(av), "new": _counts(an)})
    # 5b · Δ = 280 ms: it lies in the window `250 < Δ ≤ 250+50` ⇒ it passes the wire and
    #      loses its place during the 50 ms of declared decoding.
    dec = 0.050
    delta = cushion + dec / 2                # 275 ms: in the middle of the window
    nearly = [(its_slot + delta, i_late * PCM_STEP_US)]
    assert nearly[0][0] > last_arrival
    an2, un2 = _round("new", base + nearly, decode_delay_s=dec)
    av2, uv2 = _round("old", base + nearly, decode_delay_s=dec)
    test_case(f"5b · Δ = {delta * 1000:.0f} ms, that is inside the window "
         f"({AUDIO_CUSHION_MS} < Δ ≤ {AUDIO_CUSHION_MS + dec * 1000:.0f}) ⇒ "
         "`discarded_late`",
         (an2.discarded_late == 1 and an2.out_of_order == 1
          and an2.delivered == n and an2.rearms == 0
          and av2.delivered == n and av2.discarded_old == 1),
         "new: tardivi 1 · fuori 1 (the wire let it through) · "
         "consegnati 200 · riarmi 0 (⛔ the anchor is NOT touched for an "
         "overtaken one: a rearm would cost 250 ms of delay for a 5 ms "
         "block) — old: vecchi 1 · consegnati 200",
         {"old": _counts(av2), "new": _counts(an2)})
    # 5c · and the counter-check: the cure is NOT «I keep everything».
    an3, un3 = _round("new", _reordered(840, 3))
    test_case("5c · ⭐ the counter-check: on the reorder the new one keeps 840/840, on the "
         "late one it throws away 1 ⇒ it is not «I keep everything»",
         an3.delivered == 840 and an.delivered == n and an.discarded_old == 1,
         "the same rule, two opposite outcomes on the two cases (⛔ if it threw away zero "
         "in both it would be the removal of a check)",
         {"riordino": an3.delivered, "tardivo_scartati": an.discarded_old})

    # ── 6 · the regression: the default has NOT changed ────────────────────
    print("\n  ── 6 · the old rule against the code of before ──")
    test_benches = {
        "in order": _sorted(840),
        "reordered by 3": _reordered(840, 3),
        "with duplicates": _with_duplicates(840, 10),
        "with holes": _with_holes(840, 7),
        "mixed": _reordered(400, 2) + _with_duplicates(200, 5) + _with_holes(200, 9),
    }
    faults = []
    for name, arrivals in test_benches.items():
        v, u = _round("old", arrivals)
        ric, stale, exited = _old_literal([i for _q, i in arrivals])
        if (v.received, v.discarded_old, u) != (ric, stale, exited):
            faults.append(f"{name}: new ({v.received}, {v.discarded_old}, "
                          f"{len(u)} out) against old ({ric}, {stale}, "
                          f"{len(exited)} out)")
    test_case("6 · ⛔⛔ `--audio-rule old` == the code of 22 August, to the "
         "letter, on 5 sequences",
         not faults,
         "ricevuti, vecchi and the LIST of outputs identical in all five "
         "(⛔ if not, every number already measured by the benches stops being "
         "comparable)",
         {"faults": faults or "none",
          "predefinito": AUDIO_RULE,
          "predefinito_del_vaglio": AudioSieve().rule})
    test_case("6-bis · the DEFAULT is still `old` in both places",
         AUDIO_RULE == "old" and AudioSieve().rule == "old",
         "the module variable and the constructor both say «vecchia»",
         {"form": AUDIO_RULE, "costruttore": AudioSieve().rule})

    rossi = [e for e in outcomes if e["passes"] is False]
    silent = [e for e in outcomes if e["passes"] is None]
    print(f"\n== {len(outcomes)} cases · {len(rossi)} red · {len(silent)} «not "
          f"judged»")
    for e in rossi:
        print(f"   ⛔ {e['case']}")
        print(f"      expected {e['why']}")
        print(f"      seen     {e['numbers']}")
    if not rossi:
        print("== ⭐ THE SCREENING DOES WHAT THE PAGE DOES, AND THE DEFAULT HAS NOT "
              "CHANGED")
    return 1 if rossi else 0


def password_from_args(a):
    """The password: from `--password-file` if present, from `--password` otherwise.

    ⛔ And the three ways of failing are told apart: «cannot be read», «is readable by
    others» and «is empty» have three different cures, and an empty file is NOT an
    empty password — it is «the launcher did not write it» (`LEZIONI.md` §1.9).
    """
    fpath = getattr(a, "password_file", "") or ""
    if fpath:
        try:
            mode = os.stat(fpath).st_mode & 0o077
        except OSError as e:
            print(f"   ⛔ the password file «{fpath}» cannot be read: {e}")
            sys.exit(2)
        if mode:
            print(f"   ⚠ «{fpath}» is readable by others (bits {mode:o}): the "
                  f"secret is not protected")
        try:
            with open(fpath, encoding="utf-8") as f:
                password = f.read().strip("\n")
        except OSError as e:
            print(f"   ⛔ the password cannot be read from «{fpath}»: {e}")
            sys.exit(2)
        if not password:
            print(f"   ⛔ the password file «{fpath}» is EMPTY.  It is not")
            print("      «the password is empty»: it is «the launcher did not write it».")
            sys.exit(2)
        return password
    if any(x == "--password" or x.startswith("--password=") for x in sys.argv[1:]):
        print("   ⚠ D12: the password arrived from `--password`, that is from the")
        print("     COMMAND LINE: it sits in `/proc/<pid>/cmdline` and anyone who")
        print("     runs `ps` on this machine sees it.  The round goes on — the caller")
        print("     has not been cured — but it is not a private round.")
        print("     ⭐ The cure: `--password-file <0600 file>`, as in B10.")
    return a.password


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="the RCP handshake, from the client side")
    p.add_argument("--address", default="192.168.0.2")
    p.add_argument("--port", type=int, default=7447)
    p.add_argument("--path", default="/rcp/1")
    p.add_argument("--user", default="prova")
    p.add_argument("--password", default="prova")
    # ⛔ D12: the path that does NOT go through `ps`.  It wins over `--password` if both
    #    are there — a file written on purpose is always more recent than a
    #    default.
    p.add_argument("--password-file", default="",
                   help="0600 file holding only the password (⭐ D12: this way "
                        "it does not end up in `ps`)")
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--layout", default="it")
    p.add_argument("--record")
    # ⭐ THE CANVAS PATH — sub-phase 6.6.
    #
    # ⛔ `--fit WxH` or `WxH@S`: sends `FIT_CANVAS` and waits for the `CANVAS`
    #    that §7.1 requires.  Repeatable, and with `@S` it waits S seconds BEFORE
    #    sending it — ⭐ so the same option covers the two scenes of phase
    #    6: the request **at attach** (`DECISIONI.md` §5.0-sexies, the client
    #    asks for the canvas of its own window by itself) and the **live
    #    resize** with the session started.
    p.add_argument("--fit", action="append", default=[], metavar="WxH[@S]",
                   help="FIT_CANVAS (0x000B), repeatable; @S = seconds of "
                        "waiting before sending it")
    p.add_argument("--view", metavar="WxH",
                   help="VIEW (0x0008) after attach — ⚠ §7.1: it must NOT "
                        "change the canvas")
    # ⭐⛔ THE GRACE SECOND OF §7.1 — 22 August 2026.
    #
    # ⛔ The delay is passed in SECONDS and has no default: the rule lives on
    #    a boundary, and a value chosen by the program instead of by the bench
    #    would be a boundary chosen by someone who does not declare why.
    p.add_argument("--old-pointer", type=float, default=None,
                   metavar="DELAY",
                   help="§7.1: sends a POINTER to the LAST PIXEL of the "
                        "PREVIOUS canvas, RITARDO seconds after the CANVAS(FITTED).  "
                        "⚠ The time is the CLIENT's: the "
                        "SERVER's interval is LONGER, so stay away from the "
                        "second on both sides")
    p.add_argument("--key-after", type=float, default=0, metavar="SECONDS",
                   help="after the POINTER, wait SECONDI and send a "
                        "REQUEST_KEY: it serves to let a frame through "
                        "on a still desktop, so that the `input` field of §6.2 "
                        "can say whether the input was INJECTED.  ⚠ Not "
                        "sent if the session has already dropped")
    # ⚠ The cap is NOT an RCP rule: §7.1 requires the answer, not a
    #   time.  It serves not to reproduce the symptom we want to measure.
    p.add_argument("--wait-canvas", type=float, default=5.0,
                   help="how long to wait for a CANVAS before declaring the "
                        "silence (⚠ it is not a rule of RCP.md)")
    # ═══ THE AUDIO — phase 7 ══════════════════════════════════════════════
    p.add_argument("--video-out", default="",
                   help="where to write the frames taken FROM THE WIRE, just as "
                        "they are — to give them to a third decoder and separate "
                        "our stream from the browser's")
    p.add_argument("--video-codec", default="h264",
                   help="what to declare in `video.codec` (§4.3).  "
                        "⭐ The default is **what Firefox declares**: "
                        "`pagina.html` sends only the codecs that have PAINTED the "
                        "probe, and there HEVC does not paint.  ⛔ `hevc` redoes the "
                        "old yardstick (until 23 August 2026), and the two "
                        "sets of numbers are NOT comparable: `fasi/09` §14.1")
    p.add_argument("--video-depth", default="8,10",
                   help="what to declare in `video.depth` (§4.3)")
    p.add_argument("--audio-codec", default="opus,pcm",
                   help="what to declare in `audio.codec` (§4.3).  "
                        "⛔ `pcm` alone is legitimate and is the positive "
                        "control of Opus, not a workaround")
    # ⛔⛔ THE DEFAULT IS `old`, AND IT DOES NOT CHANGE WITHOUT THE USER.
    #     `01-b3-cliente.py` is used by dozens of already-measured benches: with the
    #     new rule as the default, every number already written would stop
    #     being comparable — and the «before / after the cure» comparison would be
    #     exactly what gets lost.
    p.add_argument("--audio-rule", default="old",
                   choices=list(AudioSieve.RULES),
                   help="`old` = §6.3 as the code read it until 22 "
                        "August 2026 (behind ⇒ thrown away); `new_one` = the reorder "
                        "cure of `src/pagina.html` (behind ⇒ thrown "
                        "away ONLY if its place has already passed).  "
                        "⛔ The default is `old` on purpose")
    p.add_argument("--audio-step-us", type=int, default=0,
                   help="how long a block lasts, in us.  0 = I derive it from the "
                        "PCM payload (⚠ for Opus I cannot decode: without "
                        "this the count of `missed` stays OFF)")
    p.add_argument("--audio-decode-ms", type=float, default=0.0,
                   help="the time we pretend to spend decoding.  "
                        "⚠ At 0 `discarded_late` is not a measurement: it is a "
                        "blind zero (T3)")
    p.add_argument("--certify", action="store_true",
                   help="⭐ the self-test of the audio screening: it does NOT touch the "
                        "network and the test machine is not needed")
    p.add_argument("--audio-out", default="",
                   help="where to write the received audio blocks, in JSONL — "
                        "the judge of `07-b42` reads this")
    # ═══ THE CLIPBOARD — phase 7, §7.4 ════════════════════════════════════
    p.add_argument("--clipboard-copy", default="",
                   help="announce this text to the server (direction device → "
                        "session) and then stay to serve it when it asks")
    p.add_argument("--clipboard-wait", type=float, default=0,
                   help="wait up to N seconds for an announcement from the server, "
                        "ask for it, and write the text that arrives (direction session → "
                        "device)")
    p.add_argument("--clipboard-out", default="",
                   help="where to write the clipboard outcome, in JSON — the "
                        "bench `07-b45` reads this")
    p.add_argument("--stay", type=float, default=0)
    # ⭐ Every how many seconds to make oneself heard (0 = never, and it is the default:
    #    keeping quiet is what is needed to measure the silence clock).
    p.add_argument("--alive", type=float, default=0)
    p.add_argument("--signal",
                   help="file to write when the session is open")
    # ⭐ The click that gives focus — see `send_button()`.
    p.add_argument("--click", default="", metavar="X,Y",
                   help="after `--click-after` seconds, moves the pointer there and "
                        "does a left click: it serves to give FOCUS to a "
                        "window of the remote desktop (without it, on GNOME the "
                        "session clipboard cannot be touched)")
    p.add_argument("--click-after", type=float, default=10.0,
                   help="how long to wait before the click, because the window "
                        "must already be there")
    p.add_argument("--click-every", type=float, default=0.0,
                   help="every how many seconds to REDO the click (0 = once "
                        "only).  ⛔ Needed when the windows to focus "
                        "are more than one, one after the other: focus goes to "
                        "the one that is there at that moment")
    a = p.parse_args()

    # ⭐ `--certify` exits HERE: it does not touch the network, does not ask for the
    #    password and does not want the test machine.
    if a.certify:
        sys.exit(certify())

    if AIOQUIC:
        print(f"   ⛔ without `aioquic` this client cannot attach to "
              f"anything: {AIOQUIC}")
        print("      ⭐ run it INSIDE the container (`enter.sh`), or ask for "
              "`--certify`, which does not touch the network.")
        sys.exit(2)

    # ⛔ The three audio choices become module variables because
    #    `create_protocol=Client` passes no arguments to the constructor.
    #    ⚠ This block runs at module level: the assignment is already
    #    global, and `Client.__init__` reads these three lines.
    AUDIO_RULE = a.audio_rule
    AUDIO_STEP_US = a.audio_step_us
    AUDIO_DECODE_S = a.audio_decode_ms / 1000.0
    if AUDIO_RULE != "old":
        # ⛔ AND IT IS SAID, loudly: a round with the new rule is NOT comparable
        #    with the numbers of the benches of before, and whoever reads the log afterwards must
        #    know it without having to find the command line again.
        print(f"   ⚠ `--audio-rule {AUDIO_RULE}`: this round does NOT use the "
              "rule with which the benches of before were measured")

    a.password = password_from_args(a)

    def measure(text, dove):
        """`WxH` or `WxH@S`.  ⛔ A crooked argument is reported, not guessed.

        ⚠ A bench that accepted `1264-800` interpreting it as best it could would give
          a size different from the one the launcher believes they asked for, and
          the number would end up in a report: the form of error **E2**.
        """
        when = 0.0
        if "@" in text:
            text, _, s = text.partition("@")
            try:
                when = float(s)
            except ValueError:
                print(f"   ⛔ {dove}: «{s}» is not a number of seconds")
                sys.exit(2)
        parts = text.lower().split("x")
        if len(parts) != 2 or not all(x.isdigit() for x in parts):
            print(f"   ⛔ {dove}: «{text}» does not have the form WxH (e.g. 1264x800)")
            sys.exit(2)
        return int(parts[0]), int(parts[1]), when

    a.fit = [measure(x, "--fit") for x in a.fit]
    a.view = measure(a.view, "--view")[:2] if a.view else None
    try:
        sys.exit(asyncio.run(main(a)))
    except Exception as e:  # noqa: BLE001 — the error type IS the measurement
        print(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
