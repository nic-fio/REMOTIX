#!/usr/bin/env python3
"""02-wire-client.py — ⛔ F2.4: the test client RECEIVES the frame, and judges it.

    python3 02-wire-client.py --port 7514 --user prova --password X
    python3 02-wire-client.py --port 7514 --record t.rcpreg --wait 20
    python3 02-wire-client.py --port 7514 --violations      the tests against the server
    python3 02-wire-client.py --list                       the predictions, without network

⚠ It runs INSIDE the container: `aioquic` lives there.  ⛔ And the port is **7514**,
  which is F2.4's: 7448 is the house product and 7501 the target
  of P5, both on on purpose (mandate §4).

⏳ **IT HAS NOT BEEN RUN YET, and it must be said.**  The phase 2 product does not
   exist — `grep -c '0x0301\\|0x0302' src/rcp.c src/webtransport.c
   src/page.html` gives **0 · 0 · 0**, `[M]` 12 Aug 2026 — so there is
   no server that sends a frame.  ⛔ This file is the bench
   **written before the product** that `PLAN.md` §0.4 moment 1 requires, and its
   first round is the first measurement of phase 2.

===========================================================================
⛔ WHY THE SECOND READER IS WORTH DOUBLE HERE, AND IT IS NOT A REPETITION

`PLAN.md` §1.1.  The server is in **C**, the page is in **JavaScript**, and
both are written by the same hand.  If the server wrote `istante` in
little-endian and the page read it in little-endian, ⛔ **the desktop
would appear perfect** and no bench of ours would notice: the two
agreed on something `RCP.md` does not say.

This program is the **third reader**, in a third language, and ⛔ whoever
grows it **does not look at `src/`**.  Its value is not the green: it is that whoever
writes it **must choose** where `RCP.md` allows two readings — and those
choices are the most precious outcome of the phase, not a side effect.
`PHASES.md` §01-filo-nudo collected **twelve** of them for the handshake; the
video chapter adds **seven**, and it is honest to separate them: ⛔ **four
are true double readings** — two conforming implementations produce different
bytes for the same input — and ⚠ **three are DERIVED rules**, that is they
follow from §3 and §1 but no line writes them.  The first are kept by
`02-wire-frame.py` with the `AMBIGUO` outcome; the second are choices of the
bench, declared next to the case.  ⭐ Confusing them would inflate the count:
a derived rule does not make two careful implementations diverge, a double
reading does.

===========================================================================
⛔ WHAT IT LOOKS AT, AND THE FIRST TWO GET FORGOTTEN

  1. ⛔ **that the frame REALLY ARRIVED**, and with the denominator.
     `LESSONS.md` §1.9: a count without a denominator is not a measurement.
     ⚠ *«no violation»* is true even on zero frames, and it is the
     easiest way to declare green a phase that delivered nothing —
     finding **R7.4** of `01-b4-validator.py`.  ⛔ Here zero frames has
     an **exit code of its own** (`5`), and it is not a green;

  2. ⛔ **FROM THE RECEIVING SIDE** (`CODER.md` §3.8, error form **E7**).  The
     server's log says it called a function, not that the byte
     arrived.  In v1 the server wrote «farewelling the client» and the client, at the
     same time, «network error» — **for three phases** (`LESSONS.md` §1.7);

  3. **on which STREAM** it arrived: a new unidirectional one, opened by the
     server, one per frame (§2.5, §5.1).  ⛔ And the channel is recognised by the
     **high byte of `tipo`**, never by the stream number — it is the cure of
     finding R11.9;

  4. ⛔ **how the stream ended**: FIN or `RESET_STREAM`, and they are two different
     things (§6.2, finding R1.7).  ⭐ **Only a live client can do
     this**: the recording of §11.1 does not have that field, and
     `02-wire-validator.py` declares it not judgeable.  See proposal
     **P7**;

  5. ⛔ **what the client MUST do next**: on a gap or an abandonment,
     `REQUEST_KEY` (§5.2); on a violation, `FAREWELL` **and** the reason in the
     error code of the closing (§3.1 points 2 and 3).  ⚠ A test client
     that limited itself to judging and staying silent would exercise **none** of the
     obligations §5.2 puts on the client — and it is the half of the protocol that
     no server bench can see.

===========================================================================
⛔ AND IT RECORDS, IN THE FORMAT OF §11.1

Every byte that arrives ends up in a recording that `02-wire-validator.py`
can judge.  ⭐ This way the frame is read **twice by two
programs**: here live, and afterwards by the mechanical referee.  ⚠ And if the two
said different things it would be a measurement, not an accident.

⛔ **The password is masked**, as in phase 1: real length, bytes
replaced with `0x2A`, fingerprint of what was there (§11.1).

===========================================================================
⛔ THE EXIT CODES, AND THEY ARE SIX BECAUSE THE FACTS ARE SIX

  0  ⭐ at least one frame arrived and every frame is conforming
  1  ⛔ a frame is NOT conforming — and it says which byte and which rule
  2  the handshake did not reach `SESSION` (nothing was tested)
  3  ⛔ `RCP.md` allows two readings of what arrived: it is not a green
     and it is not a red.  See `02-wire-frame.py --list`
  4  the connection or the session dropped before the end of the wait
  5  ⛔ ZERO frames.  «I have nothing to judge» is not «all is well»
"""
import argparse
import asyncio
import hashlib
import importlib.util
import json
import os
import ssl
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def _port(name, file):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, file))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ⛔ THEY ARE IMPORTED, NOT COPIED.
#
#    In `01-b3-client.py` there is the line that prevents giving the events of the
#    control channel to the HTTP/3 layer of `aioquic`: without it, the connection
#    dies at the CLIENT's hand with `0x105 — DATA frame is not allowed in this
#    state` (`[M]` 10 Aug 2026).  A diverging copy would bring that
#    defect back in here disguised as a server defect.
#    ⚠ And the frame judgement sits in a single file, or two copies of the
#      same reading would always agree with themselves.
#
# ⛔ And `01-b3-client.py` IS IMPORTED LATE, not here at the top.
#
#    That file imports `aioquic`, which lives **only inside the container**.
#    Importing it at the top, `--list` — which does not touch the network and serves to read
#    the predictions **before** the round — died with `ModuleNotFoundError` on
#    CHUWI.  ⚠ And the predictions are precisely the thing to be read by whoever
#    does not have the container: whoever reviews the bench before the product exists.
#    ⭐ `02-wire-frame.py` instead has no dependencies, and it is intended: the
#    frame judgement must be able to run anywhere.
f24 = _port("f24", "02-wire-frame.py")
b3 = None


def load_b3():
    global b3
    if b3 is None:
        b3 = _port("b3", "01-b3-client.py")
    return b3

CLIENT, SERVER = 1, 2

# ⛔ THE RECORDING FORMAT IS `RCPREG 0x00 0x03` — §11.1.
#
#    `0x02`, 12 Aug 2026, proposal P7 (which this very bench had
#    found): the block carries `fine`, and goes from 16 to 17 bytes.
#    ⚠ Without that field, what this client records and what it saw
#      on the wire are not the same thing: **it** knows whether the stream ended with
#      FIN or was reset — QUIC tells it — and the recording could
#      not write it.  The referee reading it had to guess.
#
# ⭐⭐ `0x03`, **21 Aug 2026**: the block carries `instant_ms` and goes to 21
#    bytes, the header declares `clock` (1 = the times are the client's).
#    Without time, §7.1 — the grace second — could not be tested from
#    any `.rcpreg`, and T4 («a server that says `CANVAS(FITTED)` and does not touch
#    the stage») could not be written at all.
#
# ⛔⛔ AND THIS FILE WAS THE SECOND ONE OF THE `0x02` ISLAND: `02-wire-validator.py`
#    read it, `04-b20-desktop-vero.py` too, and the three agreed with each
#    other while `01-b3`/`01-b4` had moved to `0x03`.  ⚠ Two live formats
#    under a single specification are the exact condition of the 12 Aug
#    defect, only bigger — and none of the three files was broken on its own.
MAGIC = b"RCPREG\x00\x03"
BLOCK = "!BBBIQIH"
CONTINUE, FIN, RESET = 0, 1, 2
CLOCK_CLIENT = 1        # §11.1: this program is the client

# ⛔ The instant is MONOTONIC and RELATIVE to the first block, never a wall-clock time:
#    §4.4 forbids secrets in the file, and an absolute date says **when** and —
#    with the address the trace already carries — **from where** a user
#    connected.  ⚠ `time.monotonic()` and not `time.time()`: an NTP adjustment
#    in the middle would make the instants go backwards, and the referee
#    would read a frame that arrived «before» the `CANVAS` preceding it.
_t0 = None


def instant():
    global _t0
    t_now = time.monotonic()
    if _t0 is None:
        _t0 = t_now
    return min(int((t_now - _t0) * 1000.0), 0xFFFFFFFF)

T_REQUEST_KEY = 0x000D
T_FAREWELL = 0x000C
PROTOCOL_ERROR = 0x0B      # §8.2
CLOSED_BY_USER = 0x01

GREEN, RED, YELLOW, GRAY = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


# ===========================================================================
class Stream:
    """A unidirectional stream of the server: one stream, one frame (§6.2)."""

    def __init__(self, sid, ctx):
        self.sid = sid
        self.referee = f24.Judge(ctx, where="uni")
        self.byte = 0
        self.is_opened = time.monotonic()
        self.closed = None
        self.verdict = None


def client_factory():
    """The phase 1 client, which learns to receive the video streams.

    ⛔ **It inherits, it does not rewrite**: the handshake is already the second reader
       of `RCP.md`, and rewriting it here would give two second readers that can
       diverge — that is two referees.

    ⚠ It is a factory and not a file-level class because the base
      class sits inside `01-b3-client.py`, which imports `aioquic`: see the
      box at the top.
    """
    class Client(load_b3().Client):

        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.context = None       # set after `SESSION`
            # ⛔ The streams we recognised as VIDEO: the set is kept
            #    and not recomputed, because the WebTransport preamble
            #    arrives only once, in the first event.
            self.video_seen = set()
            self.streams = {}
            self.finished = []
            self.keys_requested = 0
            # (direction, channel, stream, payload, masked, end) — §11.1
            self.reg_video = []
            self.first_byte = None     # ⛔ when the FIRST video byte arrived
            # ⚠ The codec negotiated in §4.3.  The driver sets it BEFORE the
            #   handshake, because `_browse` may need it already
            #   in the first packet that carries `SESSION`.
            self.expected_codec = 1

        # ⛔⛔ THE CONTEXT IS SET **HERE**, AND NOT IN THE COROUTINE THAT WAITS —
        #     bench defect found by the FIRST round against a server that
        #     really sends, `[M]` 12 Aug 2026, phase 2 assembly.
        #
        #     The server sends `SESSION` on the control channel and RIGHT
        #     AFTER opens the stream of the first frame (§5.2: «the first after
        #     `SESSION` MUST be a keyframe»).  On the wire the order is
        #     right, and the two arrive in the same flight of packets.
        #
        # ⛔ But `cli.context` was set by the driver **after**
        #    `await should_wait(cli, "SESSION")`, that is when `asyncio` resumes
        #    the coroutine — which is **after** all the events of that flight
        #    have been dispatched.  ⇒ `_arrive()` found `context is None`,
        #    concluded *«a frame before SESSION»* and printed
        #    `PROTOCOL_ERROR` — ⛔ **a red pointed at the server, which had
        #    done exactly what §2.5 requires of it**.
        #
        # ⭐ Who said whose fault it was: `02-wire-validator.py`, the
        #    second reader, on the SAME recording — *«ACCEPTED, stream
        #    15: keyframe no. 1, 1920x1080, 11923 bytes, conforming»*, exit 0.  ⚠ And
        #    that the two referees of the same bench said opposite things about the
        #    same bytes is a MEASUREMENT, not an accident (`P2-4-filo.md` §4).
        #
        # ⛔ And the cure is not «wait a little»: it is looking at the buffer of the
        #    control channel **before** `_browse` consumes it, that is
        #    at the same synchronous instant the bytes arrived.  This way
        #    «before `SESSION`» becomes again a question about BYTES, and not
        #    about the order in which `asyncio` wakes the coroutines.
        def _browse(self):
            if self.context is None:
                data = bytes(self.incoming)
                i = 0
                while len(data) - i >= 6:
                    kind, lung = struct.unpack("!HI", data[i:i + 6])
                    if len(data) - i < 6 + lung:
                        break
                    # body: 1 byte of state, then width and height (§4.5)
                    if kind == load_b3().T["SESSION"] and lung >= 9:
                        lar, h = struct.unpack("!II", data[i + 7:i + 15])
                        self.context = f24.Context(
                            canvas=(lar, h),
                            negotiated_codec=self.expected_codec,
                            session_open=True)
                        break
                    i += 6 + lung
            super()._browse()

        def quic_event_received(self, event):
            name = type(event).__name__
            # ⛔ The server's unidirectional streams are intercepted BEFORE
            #    passing the event to the phase 1 chain: that one does not know
            #    them and would give them to the HTTP/3 layer of `aioquic`, which would
            #    read them as HTTP/3 frames and close the connection —
            #    **by our own hand**.  ⚠ It is the same asymmetry paid for on 10
            #    Aug 2026 on the control channel (`01-b3-client.py`).
            if name == "StreamDataReceived" and self._dispatch(event):
                return
            if name == "StreamReset" and event.stream_id in self.video_seen:
                # ⛔ `RESET_STREAM`: the frame is INCOMPLETE (§6.2).
                self._zeroed(event.stream_id)
                return
            super().quic_event_received(event)

        # ⛔⛔ THE WEBTRANSPORT PREAMBLE, AND THE FIRST ROUND PAID FOR IT
        #
        # ⚠ `[M]` 12 Aug 2026, FIRST LIVE ROUND of this client against
        #   7514.  The previous line said: *«a unidirectional stream
        #   opened by the server is recognised by the two low bits
        #   of the QUIC identifier»* — and it also took **the three
        #   unidirectional streams of HTTP/3** (the control stream and the two of QPACK, which
        #   `aioquic` opens by itself and which have the same two bits).  ⇒ The
        #   HTTP/3 layer was left without its bytes, the extended CONNECT never
        #   reached `:status 200`, the control channel did not open, and the
        #   server closed with `TIMED_OUT` after 5 s (§4.6).
        #   ⛔ The symptom was **a red pointed at the server**, which had done
        #      exactly its job: the positive control —
        #      `01-b3-client.py` against the **same** server, in the same
        #      minute — reached `SESSION` in 1003 ms.
        #
        # ⭐ And the cure carries a discovery about `RCP.md`, which is in the
        #    report as **P18**: §2.5 says *«the first two bytes of the
        #    stream are read, which are in any case a `kind` field»*, ⛔ and on
        #    WebTransport **it is not true**: a unidirectional stream of the server
        #    starts with type `0x54` as a varint (two bytes, `40 54`) and with the
        #    session number, and the 28 bytes of §6.2 start after.
        WT_UNI = 0x54  # draft-ietf-webtrans-http3: the type of the uni stream

        @staticmethod
        def _varint(b, i):
            """The QUIC varint (RFC 9000 §16).  `None` = it is not all here."""
            if i >= len(b):
                return None, i
            n = 1 << (b[i] >> 6)
            if i + n > len(b):
                return None, i
            v = b[i] & 0x3F
            for k in range(1, n):
                v = (v << 8) | b[i + k]
            return v, i + n

        def _dispatch(self, event):
            """Is this stream a frame?  ⛔ And if it is not, **not one byte of it
            is consumed**: those bytes belong to HTTP/3, and taking them is
            the defect the first round paid for."""
            sid = event.stream_id
            if sid in self.video_seen:
                self._arrive(sid, event.data, event.end_stream)
                return True
            # 0b11 = unidirectional, opened by the server
            if (sid & 0x03) != 0x03 or sid == self.session:
                return False
            d = event.data
            # ⛔ The decision is made on the FIRST event and the first two bytes, and if they
            #    are not enough it is dropped instead of holding them back: «I did not
            #    understand» and «it is mine» are two different things.
            if len(d) < 2 or d[0] != 0x40 or d[1] != self.WT_UNI:
                return False
            kind, i = self._varint(d, 0)
            session, i = self._varint(d, i)
            if kind != self.WT_UNI or session is None:
                return False
            self.video_seen.add(sid)
            self._arrive(sid, bytes(d[i:]), event.end_stream)
            return True

        def _arrive(self, sid, data, fine):
            if self.context is None:
                # ⛔ A frame before `SESSION`: the context is not there
                #    yet, and the judge MUST be able to say so — invariant I3.
                self.context = f24.Context(session_open=False)
            f = self.streams.get(sid)
            if f is None:
                f = self.streams[sid] = Stream(sid, self.context)
                if self.first_byte is None:
                    self.first_byte = time.monotonic()
            f.byte += len(data)
            self.reg_video.append([SERVER, 0x03, sid, bytes(data), [],
                                   FIN if fine else CONTINUE, instant()])
            f.referee.arrive(data)
            if fine:
                f.closed = "fin"
                self._close(f)

        def _zeroed(self, sid):
            # ⛔ AND IT IS WRITTEN IN THE RECORDING — §11.1, field `fine`.
            #
            #    The `RESET_STREAM` carries no bytes, so it has no block of its own:
            #    it marks the LAST block of that stream.  ⚠ And if there is
            #    none — a stream reset before delivering a byte
            #    — an **empty** one is written: «zero bytes, reset» and «it never
            #    existed» are two different facts, and it is the E8 form.
            last = None
            for b in self.reg_video:
                if b[2] == sid:
                    last = b
            if last is None:
                self.reg_video.append([SERVER, 0x03, sid, b"", [], RESET,
                                       instant()])
            else:
                last[5] = RESET
            f = self.streams.get(sid)
            if f is None:
                f = self.streams[sid] = Stream(
                    sid, self.context or f24.Context())
            f.closed = "reset"
            self._close(f)

        def _close(self, f):
            if f.verdict is not None:
                return
            f.verdict = (f.referee.verdict
                          if f.referee.verdict is not None
                          else f.referee.ends(f.closed))
            self.finished.append(f)
            del self.streams[f.sid]

        # -- the obligations §5.2 puts on the CLIENT -----------------------
        def ask_key(self, last):
            """§5.2: the client MUST ask for a keyframe on a gap or an
            abandonment.

            ⛔ And `last_number` is «the last decoded frame, 0 if
               none» (§7.1) — which is ambiguity **A2**: if the counter of
               §6.2 could start from 0, this field would say two things.  Here
               what the document says is sent, and the ambiguity is flagged
               instead of being resolved by hand by the bench.
            """
            self.send_msg(struct.pack("!HII", T_REQUEST_KEY, 4,
                                   last if last is not None else 0))
            self.keys_requested += 1

    return Client


# ===========================================================================
async def look(cli, a, ctx):
    """Keeps listening, and does what §5.2 requires of the client.

    ⛔ **With eyes open, not asleep** — findings R8.2/R8.4 of phase 1.
       An `asyncio.sleep` notices nothing: the connection can drop
       because of QUIC's idle ceiling, or the session can be closed by the
       server, and this program would exit 0 saying «I looked».
    """
    expiry = asyncio.get_event_loop().time() + a.wait
    seen_items = 0
    while asyncio.get_event_loop().time() < expiry:
        if cli.drop is not None:
            return seen_items, f"dropped: {cli.drop}"
        while len(cli.finished) > seen_items:
            f = cli.finished[seen_items]
            seen_items += 1
            v = f.verdict
            clr = {f24.ACCEPTED: GREEN, f24.DISCARDED: YELLOW,
                   f24.AMBIGUOUS: YELLOW, f24.PROTOCOL_ERROR: RED}[v.outcome]
            print(f"   {clr}{v.outcome:18s}{GRAY} stream {f.sid}, {f.byte} "
                  f"bytes, ended with {f.closed}: {v.says}")
            if v.outcome == f24.PROTOCOL_ERROR:
                # ⛔ §3.1, and the points are THREE and in this order: in the log,
                #    the `FAREWELL` on the channel if the channel is usable, and the
                #    reason in the error code of the session's closing.
                print(f"      ⛔ {v.rule} — byte {v.deviation} "
                      f"of the header")
                cli.send_msg(struct.pack("!HIB", T_FAREWELL, 3, PROTOCOL_ERROR)
                          + struct.pack("!H", 0))
                return seen_items, f"NOT CONFORMING: {v.says}"
            # ⛔ And the obligations of §5.2, which are the CLIENT's and which no
            #    server bench can exercise in its place.
            if ctx.ask_key:
                cli.ask_key(ctx.last_delivered)
                print(f"      ⇒ `REQUEST_KEY(last_number="
                      f"{ctx.last_delivered or 0})` — §5.2")
                ctx.ask_key = False
        await asyncio.sleep(0.02)
    return seen_items, None


def write_recording(fpath, blocks):
    """The format of §11.1, with the video blocks next to the control ones.

    ⛔ `fine` defaults to CONTINUA: the control channel lives on **a single
       stream for the whole session** (§2.5), and inside the recording that
       stream does not close.  ⚠ Writing `FIN` at every message would say that the
       session closes and reopens at every line.
    """
    # ⛔⛔ AND THE BLOCKS ARE PUT BACK IN TIME ORDER, and it is not cosmetic.
    #
    #    The caller passes `blocks + cli.reg_video`: the CONTROL blocks
    #    all first, the VIDEO ones all after.  ⚠ But a `REQUEST_KEY`
    #    sent midway through the session ended up **in front of** the first frame, which
    #    had passed on the wire much earlier.  ⛔ With `0x02` it did not show: without
    #    time, a wrong order and a right one look the same.
    #    With `0x03` the referee requires a monotonic clock and would say so —
    #    «broken recording» — on a trace of a perfectly healthy wire.
    #
    # ⭐ `sorted` is STABLE: two blocks with the same millisecond stay
    #    in the order in which they were recorded, which is what is known about
    #    them.  Inventing an order among equals would be worse than not having one.
    def _when(b):
        return b[6] if len(b) > 6 else 0

    blocks = sorted(blocks, key=_when)
    out = bytearray(MAGIC + struct.pack("!IBBBB", len(blocks),
                                        CLOCK_CLIENT, 0, 0, 0))
    for which_way, channel, stream, load, *rest in blocks:
        obscured = rest[0] if rest else []
        fine = rest[1] if len(rest) > 1 else CONTINUE
        ist = rest[2] if len(rest) > 2 else 0
        out += struct.pack(BLOCK, which_way, channel, fine, ist, stream,
                           len(load), len(obscured))
        for ini, here, imp in obscured:
            out += struct.pack("!II", ini, here) + imp
        out += load
    with open(fpath, "wb") as f:
        f.write(bytes(out))
    return len(blocks)


async def main(a):
    from aioquic.h3.connection import H3_ALPN
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.asyncio import connect
    b3 = load_b3()
    Client = client_factory()

    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    authority = f"{a.address}:{a.port}"
    blocks = []

    print(f"== F2.4 — the test client RECEIVES the frame")
    print(f"   ⛔ TARGET: https://{authority}{a.path}")
    print(f"   ⛔ SCENE: session just opened, no input, no "
          f"movement —")
    print(f"      phase 2 delivers **a still image** (`PLAN.md` "
          f"«Phase 2»).")
    print(f"      ⚠ And it must be declared: `CODER.md` §3.2 wants a scene always in")
    print(f"        motion, and here the still scene **is the subject**, not "
          f"a")
    print(f"        distraction.  From phase 3 onwards that rule applies "
          f"again.")
    print(f"   wait: {a.wait} s\n")

    async with connect(a.address, a.port, configuration=conf,
                       create_protocol=Client) as cli:
        await asyncio.wait_for(cli.wait_connected(), timeout=8)
        cli.open_session(authority, a.path)
        state = await asyncio.wait_for(cli.accepted, timeout=8)
        print(f"   extended CONNECT: :status = {state}")
        if state != "200":
            return 2
        cli.open_control()
        # ⛔ BEFORE the handshake: `_browse` may need the
        #    codec already in the packet that carries `SESSION`, and a value set
        #    after would be set too late — it is the same ordering defect
        #    the box of `_browse` describes.
        cli.expected_codec = a.codec
        try:
            b = b3.wrap(b3.T["HELLO"], b3.body_hello())
            cli.send_msg(b)
            blocks.append((CLIENT, 0x00, 0, b, [], CONTINUE, instant()))
            _, body, raw = await b3.should_wait(cli, "HERE_I_AM")
            blocks.append((SERVER, 0x00, 0, raw, [], CONTINUE, instant()))

            body_c = b3.s(a.user) + b3.s(a.password)
            b = b3.wrap(b3.T["CREDENTIALS"], body_c)
            ini = 6 + 2 + len(a.user.encode()) + 2
            here = len(a.password.encode())
            cli.send_msg(b)
            blocks.append((CLIENT, 0x00, 0,
                            b[:ini] + bytes([0x2A]) * here + b[ini + here:],
                            [(ini, here, hashlib.sha256(a.password.encode()).digest())],
                            CONTINUE, instant()))
            _, body, raw = await b3.should_wait(cli, "ADMITTED", wait=20)
            blocks.append((SERVER, 0x00, 0, raw, [], CONTINUE, instant()))

            b = b3.wrap(b3.T["ATTACH"],
                            struct.pack("!IIII", a.width, a.height,
                                        a.width, a.height)
                            + b3.s(a.layout))
            cli.send_msg(b)
            blocks.append((CLIENT, 0x00, 0, b, [], CONTINUE, instant()))
            _, body, raw = await b3.should_wait(cli, "SESSION")
            blocks.append((SERVER, 0x00, 0, raw, [], CONTINUE, instant()))
        except Exception as e:      # noqa: BLE001 — the error type IS the measurement
            print(f"   ⛔ the handshake did not reach SESSION: "
                  f"{type(e).__name__}: {e}")
            print(f"      ⚠ This is NOT a video red: nothing was "
                  f"tested")
            return 2

        lar, h = struct.unpack("!II", body[1:9])
        print(f"   ⭐ SESSION: canvas granted {lar}x{h}")
        # ⛔ THE CONTEXT IS TAKEN FROM `SESSION`, NOT FROM THE DEFAULTS.
        #
        #    §6.2 ties `w.`/`height` to the **granted canvas** — which can
        #    differ from the requested one (§4.5, the fallback on KDE) — and
        #    `codec` to what §4.3 negotiated.  A judge that used its
        #    own defaults would be judging itself.
        # ⚠ `_browse` may have set it already, on the same bytes and with the
        #   same values: then it is not redone.  ⛔ Redoing it here would erase
        #   a context already used by the streams arrived in the same flight — and their
        #   `Stream` would keep the old object, that is two truths
        #   about the same session.
        if cli.context is None:
            cli.context = f24.Context(canvas=(lar, h),
                                        negotiated_codec=a.codec,
                                        session_open=True)
        ctx = cli.context

        seen_items, why = await look(cli, a, ctx)

    if a.record:
        n = write_recording(a.record, blocks + cli.reg_video)
        print(f"\n   recording: {a.record} ({n} blocks) — "
              f"⛔ and it must be given to `02-wire-validator.py`, which is the other reader")

    outcomes = [f.verdict.outcome for f in cli.finished]
    compliant = sum(1 for e in outcomes if e == f24.ACCEPTED)
    ambiguous = sum(1 for e in outcomes if e == f24.AMBIGUOUS)
    print(f"\n   watched: {len(cli.finished)} video streams · {compliant} "
          f"conforming · {ambiguous} ambiguous · {cli.keys_requested} "
          f"`REQUEST_KEY` sent")

    if a.output:
        with open(a.output, "a") as f:
            f.write(json.dumps({
                "when": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "bench": "F2.4-cliente", "port": a.port,
                "scene": "session just opened, no input, still image",
                "streams": len(cli.finished), "compliant": compliant,
                "ambiguous": ambiguous, "keys_requested": cli.keys_requested,
                "outcomes": outcomes, "drop": cli.drop}, ensure_ascii=False) + "\n")

    # ⛔ AND ZERO HAS A CODE OF ITS OWN — see point 1 of the header.
    if not cli.finished:
        print(f"\n   {RED}⛔ ZERO frames in {a.wait} s.{GRAY}")
        print(f"      This is NOT «conforming»: it is the absence of the object of "
              f"judgement.")
        print(f"      Look at whoever had to send them — not at `RCP.md`.")
        return 5
    if f24.PROTOCOL_ERROR in outcomes:
        print(f"\n   {RED}⛔ a frame is NOT conforming{GRAY}")
        return 1
    if why:
        print(f"\n   {RED}⛔ {why}{GRAY}")
        return 4
    if ambiguous:
        print(f"\n   {YELLOW}⭐⛔ `RCP.md` allows two readings of what "
              f"arrived{GRAY}")
        print(f"      It is not a green and it is not a red: it is a defect of the "
              f"DOCUMENT.")
        print(f"      The proposals: `python3 02-wire-frame.py --list`")
        return 3
    print(f"\n   {GREEN}⭐ {compliant} frames, all conforming to `RCP.md`"
          f"{GRAY}")
    print(f"   ⚠ and it is NOT «the user sees their desktop»: here the "
          f"BYTES are judged.")
    print(f"     The pixels are compared by F2.6, and the yardstick is the user (I8).")
    return 0


# ===========================================================================
# ⛔ THE VIOLATIONS TOWARDS THE SERVER, and they are those phase 2 adds.
#
#    `01-b5-violations.py` tests forty-four of them on the handshake, and
#    declares at the top which ones it does NOT test because the message does not exist yet:
#    among these, *«two `REQUEST_KEY` less than 200 ms apart»*, postponed to
#    phase 3.  ⭐ Here are added those born with the first frame.
#
# ⚠ And one already in B5 is REDONE, and it is not a duplicate: `uni-video`
#   sent `0x0301` to a server that did **not know** the video channel
#   at all — it fell into the `default` branch.  Against a server that knows it,
#   the same input exercises a **different** code path, and a case
#   that passes against the first says nothing about the second.
VIOLATIONS = [
    ("video-dal-client", PROTOCOL_ERROR,
     "a WELL-FORMED keyframe on a unidirectional stream of the "
     "client: §2.5, «a `0x03` that arrives from the client».  ⛔ The payload is legal "
     "in itself: the only wrong thing is the direction"),
    ("richiedi-chiave-prima-di-sessione", PROTOCOL_ERROR,
     "`REQUEST_KEY` between `ADMITTED` and `SESSION`: there is no "
     "frame whose keyframe could be asked for (§1, §3)"),
    ("richiedi-chiave-corta", PROTOCOL_ERROR,
     "`REQUEST_KEY` with three bytes of body instead of four: §6.1, «a "
     "length inconsistent with what the type expects»"),
    ("richiedi-chiave-zero", None,
     "⭐ `REQUEST_KEY(last_number = 0)`: §7.1 declares it legal — «0 if "
     "none» — and it is what a just-attached client sends.  ⛔ The "
     "session MUST stay alive"),
    ("richiedi-chiave-due-volte", None,
     "⏳ two `REQUEST_KEY` less than 200 ms apart: the server **MAY** ignore the "
     "second (§3 exception 5, §5.2) — and in both cases the session "
     "MUST stay alive.  ⚠ The real measurement belongs to **phase 3**, where the "
     "keyframes are counted: here it is only proved that the session holds"),
]


def listing():
    print("== F2.4 — the test client: what it tests, and against what")
    print("   ⏳ NOT RUN YET: the phase 2 product does not exist\n")
    print("== ⛔ from the RECEIVING side — the cases are in 02-wire-frame.py")
    print("   `python3 02-wire-frame.py --list`\n")
    print("== ⛔ towards the SERVER — the violations phase 2 adds")
    print("   ⛔ Every line is a PREDICTION, written before the round\n")
    for name, expected, explain in VIOLATIONS:
        expect = (f"{expected:#04x} PROTOCOL_ERROR" if expected
               else "⭐ MUST PASS, and the session MUST stay alive")
        print(f"  {name:36s} {expect}")
        print(f"  {'':36s}   {explain}")
    print(f"\n  {len(VIOLATIONS)} cases: "
          f"{sum(1 for v in VIOLATIONS if v[1])} violations and "
          f"{sum(1 for v in VIOLATIONS if not v[1])} ⭐ expected greens")
    return 0


# ---------------------------------------------------------------------------
# ⛔ THE PASSWORD MUST NOT GO THROUGH THE COMMAND LINE — defect **D12**,
#    cured on 12 Aug 2026.
#
# ⛔ `--password` ends up in the process's `argv`, that is in `/proc/<pid>/cmdline`,
#    which on Linux is **readable by anyone**: a `ps` launched by another
#    user during the round prints it in full.
#
# ⭐ The good road already existed in the house and this is its extension, not a
#    second way: `01-b10-secondo-utente.py` takes `--parola-file`, a `0600`
#    file the launcher writes with `printf` — a shell **builtin**,
#    so not even the writing goes through a process with the password in `argv` —
#    and deletes with a `trap`.
#
# ⚠ And `--password` was NOT removed, and not out of laziness: some callers not
#   yet cured still pass it, and breaking them **silently** would be worse
#   than the defect.  ⛔ But the fallback is DECLARED (`CODER.md` §4.2): a silent
#   fallback produces two behaviours under the same label, which is the
#   **E2** form — and here the two behaviours are «the secret is protected» and
#   «the secret is public».  ⇒ whoever passes `--password` gets told.
#
# ⚠ And the warning looks at `sys.argv`, not at the value: the default written in the
#   code is on no command line, and telling it otherwise would be an
#   alarm one learns to ignore.
def password_from_args(a):
    """The password: from `--password-file` if present, from `--password` otherwise.

    ⛔ And the three ways of failing are kept apart: «cannot be read», «is readable by
    others» and «is empty» have three different cures, and an empty file is NOT an
    empty password — it is «the launcher did not write it» (`LESSONS.md` §1.9).
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
        print("     COMMAND LINE: it is in `/proc/<pid>/cmdline` and anyone who runs")
        print("     `ps` on this machine sees it.  The round goes on — the caller")
        print("     has not been cured — but it is not a private round.")
        print("     ⭐ The cure: `--password-file <0600 file>`, as in B10.")
    return a.password


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="F2.4 — the test client that receives the frame")
    p.add_argument("--address", default="192.168.0.2")
    # ⛔ The port has NO default naming a target: 7448 is the
    #    house product and 7501 the P5 target, both on on purpose.
    #    The F2.4 port is **7514**, and it is passed by hand.
    p.add_argument("--port", type=int, help="⛔ 7514, for F2.4")
    p.add_argument("--path", default="/rcp/1")
    p.add_argument("--user", default="prova")
    p.add_argument("--password", default="parola-di-prova")
    # ⛔ D12: the road that does NOT go through `ps`.  It wins over `--password` if both
    #    are there — a file written on purpose is always more recent than a
    #    default.
    p.add_argument("--password-file", default="",
                   help="0600 file with only the password (⭐ D12: this way "
                        "it does not end up in `ps`)")
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--layout", default="it")
    p.add_argument("--codec", type=int, default=1, help="1 = HEVC, 2 = AV1")
    p.add_argument("--wait", type=float, default=15.0,
                   help="how many seconds to keep listening")
    p.add_argument("--record", help="the trace, in the format of §11.1")
    p.add_argument("--output", default="", help="the round's log, in JSONL")
    p.add_argument("--list", action="store_true",
                   help="the predictions, without network")
    p.add_argument("--violations", action="store_true",
                   help="⏳ the tests against the server (needs a server)")
    a = p.parse_args()
    a.password = password_from_args(a)
    if a.list:
        sys.exit(listing())
    if not a.port:
        print("⛔ --port is needed.  For F2.4 it is 7514: 7448 and 7501 are")
        print("   on on purpose and are not touched (mandate §4).")
        sys.exit(2)
    try:
        sys.exit(asyncio.run(main(a)))
    except Exception as e:  # noqa: BLE001 — the error type IS the measurement
        print(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
