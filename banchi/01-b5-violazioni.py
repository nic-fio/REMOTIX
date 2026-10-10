#!/usr/bin/env python3
"""01-b5-violazioni.py — ⛔ B5: strictness towards the server, tested by violating it.

    python3 01-b5-violazioni.py --address 192.168.0.2 --port 7447
    python3 01-b5-violazioni.py --solo tela-1921          (a single case)
    python3 01-b5-violazioni.py --listing                  (the predictions, without measuring)

⚠ It runs INSIDE the container: aioquic lives there.

===========================================================================
⛔ WHY THIS BENCH EXISTS

`RCP.md` §3 is the **strictness rule**: what is not understood is not ignored,
the connection drops, with the reason.  ⭐ But a strictness rule **is not tested
by doing the right things**: a server that checks nothing passes all the B3
benches and falls only the day someone sends it a crooked byte — and that day
there is no bench watching.

⛔ *A bench that does not try to violate the protocol does not test the protocol.*

===========================================================================
⛔ THE FIVE THINGS EVERY CASE VERIFIES, AND THE LAST TWO GET FORGOTTEN

  1. ⛔ **that the violation REALLY left.**  A case whose *preparation* fails —
     the fixed `ATTACH` refused, the `HERE_I_AM` that does not arrive — has tested
     nothing, and as long as the reason was scraped from the exception text it
     became **green** precisely because of that (finding R7.1).  Here every
     case carries `caused`, and without it it is red;
  2. **the right reason**, read FROM THE RECEIVING SIDE (§8.1) — not from the
     server log, which is the same hand that wrote the code, and ⛔ **not from
     the text of an exception**: `collect` takes it from a message that arrived
     on the wire, or does not take it;
  3. ⛔ **in which MESSAGE** it arrived.  §11 says it in full:
     `WRONG_CREDENTIALS` and `TOO_MANY_ATTEMPTS` travel in `REJECTED`, all the
     others in `FAREWELL`, and §4.4 forbids sending both.  They are **two
     different state machines** — after `REJECTED` the client cannot retry —
     and counting them under the same label is form E3 (finding R7.9);
  4. **the two roads of §3.1**, and ⛔ **they are not optional in the same way**:
     **point 2** (the `FAREWELL`) is conditional — *«if the control channel is
     still usable»* — **point 3** (the reason code in the closing of the
     WebTransport session) is an **unconditional MUST**, and it is the one §3.1
     calls *«the one that saves the diagnoses»*.
     ⚠ Finding R3.3 said that always demanding both would give red on the
     right code: it holds for point 2, **not** for point 3, and having swapped
     them had made optional precisely the last foothold (finding R7.3).
     Here point 3 is **counted**, with its denominator, instead of being
     printed;
  5. ⛔ **and that the server is still there afterwards** (B0.5).  A server
     killed by the kernel *«drops the connection»* exactly like one that says
     farewell — and it takes away **all the other users' sessions**.  After every
     case a new connection is opened and it gets as far as `HERE_I_AM`: it is the
     half of the bench nobody writes, and it is the one that tells strictness
     from collapse.

===========================================================================
⭐ AND THE CASES THAT MUST PASS

The cases with `expected_val = None` are ⭐ **expected greens**, and they are not
filler: they are the control that says *no* to «this server closes everything».

  nome-con-trattino-basso    `video.max_size`: the `_` is LAWFUL (§4.3)
  capacita-sconosciuta       a NAME that does not exist is ignored (§3, exception 1)
  hevc-e-vp9                 an unknown entry INSIDE a list is DISCARDED
  vista-300x801              the view does not have the canvas constraints (§7.1, R4.10)
  vista-1x1                  likewise, at the limit
  disposizione-con-variante  `de(neo)`: the variant in parentheses is lawful
  banco-spento               ⛔ `BENCH_OUTCOME(RIFIUTATA, FUNCTION_OFF)`, not
                             a closing and not a silence (§7.5 rule 2)
  banco-ritardo-20000        `DELAY_OUT_OF_LIMITS`, and the session STAYS OPEN

⛔ **AND HOW MANY THERE ARE IS NOT WRITTEN HERE.**  The number is counted by
`tally()` and printed by `--listing` and by the final line, each with its
denominator.  A number written by hand in a comment is the number nobody
recomputes: finding R7.14 found **three** of them — «five cases in here»,
«thirty-five greens out of thirty-five», «44 violations out of 44» — and **none
of the three matched the file**.  ⚠ The third, what is more, counted among the
violations also the cases that MUST pass, on which «the right reason every
time» is false by construction: on those no reason must arrive.

===========================================================================
⛔ WHAT THIS BENCH DOES NOT TEST, AND IT MUST BE SAID — finding R7.8

`RCP.md` §3 declares **five** exceptions to the strictness rule and says that
«outside this list none are invented».  Here **one** is tested: the first, with
`capacita-sconosciuta` and `hevc-e-vp9`.  The other four are **tolerances** —
places where the server MUST *not* close — and a server that closed at every
surprise would pass this bench in full.

| exception of §3 | the missing case | why it is not here |
|---|---|---|
| 2 (§6.3) | a 4-byte datagram, or one with `kind` != `0x0401`, is **discarded** | audio does not exist before **phase 7** |
| 3 (§7.1) | the **grace second** on the old coordinates after `CANVAS(ADAPTED)` | `FIT_CANVAS` and input do not exist before **phase 6** |
| 4 (§7.1) | a size **out of bounds** in `FIT_CANVAS` → `CANVAS(RIFIUTATA, SIZE_OUT_OF_LIMITS)` **with the session still open** | ⭐ **no longer true since 15 Aug 2026**: `FIT_CANVAS` is served, and the case is tested by `banchi/04-b31-tela.c` (cases 5 and 17). ⚠ And the example that was here — `1921×1081` — **was wrong**: it is WITHIN the limits of §4.5 and odd, so it is truncated to `1920×1080` and granted. Out of bounds is, for example, `1600×230` (the minimum height is 240) |
| 5 (§5.2, §7.4) | two `REQUEST_KEY` less than 200 ms apart: the second **may be ignored** | `REQUEST_KEY` does not exist before **phase 3** |

⚠ **Writing them here today would give red on a message nobody has written
yet**, that is on a rule the server never had the chance to apply — the
defect `01-b5-lancia.sh` declares it fears for the graft.  They go into the
benches of phases 3, 6 and 7, and this table is the place to pick them up
from.
"""
import argparse
import asyncio
import importlib.util
import os
import ssl
import struct
import sys

from aioquic.h3.connection import H3_ALPN
from aioquic.quic.configuration import QuicConfiguration
from aioquic.asyncio import connect

HERE = os.path.dirname(os.path.abspath(__file__))

# ⛔ The B3 client is IMPORTED, not copied.  Inside it is the line that
#    prevents it from handing the control-channel events to aioquic's HTTP/3
#    layer — without which the connection dies at the hand of the CLIENT (10
#    Aug 2026), and a diverging copy would bring that defect back in here
#    disguised as a server defect.
_spec = importlib.util.spec_from_file_location(
    "b3cliente", os.path.join(HERE, "01-b3-cliente.py"))
b3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b3)

# ⛔ And the TARGET's profile, for the same reason: the differences between the
#    two servers are in a single file, and four benches read them instead of
#    discovering them all over again — or, worse, not discovering them and
#    giving red.
_spec_b0 = importlib.util.spec_from_file_location(
    "b0bersaglio", os.path.join(HERE, "01-b0-bersaglio.py"))
b0 = importlib.util.module_from_spec(_spec_b0)
_spec_b0.loader.exec_module(b0)

s, wrap, REASONS = b3.s, b3.wrap, b3.REASONS

PROTOCOL_ERROR = 0x0B
NOTHING_IN_COMMON = 0x09
INCOMPATIBLE_VERSION = 0x0A
SESSION_UNSERVABLE = 0x0E
TOO_MANY_ATTEMPTS = 0x08
WRONG_CREDENTIALS = 0x07
FAREWELL, REJECTED, BENCH_OUTCOME = 0x000C, 0x0005, 0x0010

# ⛔ IN WHICH MESSAGE THE REASON MUST ARRIVE — `RCP.md` §11, line «the
#    farewell»: «`CREDENZIALI_ERRATE` and `TROPPI_TENTATIVI` travel in
#    `RESPINTO`», all the others in `FAREWELL`, and §4.4 forbids following
#    `REJECTED` with a `FAREWELL`.  ⚠ It is not a formality: after `REJECTED` the
#    client MUST NOT retry on the same connection (§4.4), after a `FAREWELL` the
#    connection is simply over — two different state machines under the same
#    number (finding R7.9).
CARRIER = {WRONG_CREDENTIALS: "REJECTED", TOO_MANY_ATTEMPTS: "REJECTED"}


class Client(b3.Client):
    """The B3 client, plus what is needed to violate (§2.5)."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        # ⛔ THE STREAMS THIS BENCH OPENS, and they must be kept away from
        #    aioquic's HTTP/3 layer: see `quic_event_received`.
        self.my_streams = set()
        self.echo = {}

    def open_uni(self):
        # aioquic writes by itself the header of the WebTransport
        # unidirectional stream: the type 0x54 and the session identifier.
        s_id = self._http.create_webtransport_stream(
            self.session_v, is_unidirectional=True)
        self.my_streams.add(s_id)
        return s_id

    def open_bidi(self):
        s_id = self._http.create_webtransport_stream(
            self.session_v, is_unidirectional=False)
        self.my_streams.add(s_id)
        return s_id

    def send_on(self, stream, data_v, fine=False):
        self._quic.send_stream_data(stream, data_v, end_stream=fine)
        self.transmit()

    def quic_event_received(self, event):
        # ⛔⭐ WHAT COMES BACK ON THE STREAMS WE OPENED MUST NOT BE GIVEN TO
        #     AIOQUIC — and it is a defect OF THE BENCH, measured `[M]` on 10
        #     Aug 2026 on the server log.
        #
        #     The case `secondo-bidirezionale` gave «chiusura-wt=(absent)»
        #     while the server did everything right.  The log, at lines
        #     32355-32359 of `b5-server.log`:
        #
        #       REMOTIX B5: ⛔ two bidirectional streams from the client inside
        #                     the session: control is 4, and 8 is one too many
        #       REMOTIX B3: farewell motivo=0x0b …
        #       REMOTIX B3: session closure DEFERRED, code 0x0b
        #                   (queued: 1; keep-alive at 100 ms …)
        #       frm tx … STREAM id=0x4 len=71   ← the FAREWELL
        #       frm tx … STREAM id=0x8 len=30   ← B2's echo on the extra stream
        #       frm rx … CONNECTION_CLOSE error_code=0x105
        #                reason=[DATA frame is not allowed in this state]
        #       ngtcp2_conn_read_pkt: ERR_DRAINING
        #
        # ⛔ The `CONNECTION_CLOSE` is RECEIVED by the server: it is the CLIENT
        #    that leaves, one packet after the `FAREWELL` and half a second
        #    before the five passes let the capsule mature.  Code 0x105 is
        #    aioquic's `H3_FRAME_UNEXPECTED`: the 30 bytes that came back on
        #    stream 8 ended up in `self._http.handle_event`, which knows nothing
        #    of a WebTransport stream opened by us and reads them as a `DATA`
        #    frame on a request stream.  ⚠ It is the same asymmetry already
        #    measured in `01-b3-cliente.py` — aioquic 1.2 can CREATE a
        #    WebTransport stream and cannot RECOGNISE it when it answers us —
        #    cured there for the control channel and never for the streams B5
        #    opens.
        #
        # ⭐ So the bench was measuring its own hurry, not the server: a real
        #    browser hands those bytes to the page and stays connected.
        #    Here they are discarded, DECLARING THEM (§3: no silent tolerance).
        if (type(event).__name__ == "StreamDataReceived"
                and event.stream_id in self.my_streams):
            if event.data and event.stream_id not in self.echo:
                self.echo[event.stream_id] = len(event.data)
                print(f"   [wt]   ⚠ {len(event.data)} bytes came back from the server "
                      f"on stream {event.stream_id}, the one opened to "
                      f"violate: it is B2's echo on the bytes already in flight while "
                      f"the session drops.  The bench discards them without giving them "
                      f"to aioquic's HTTP/3 layer, which would kill the "
                      f"connection with 0x105 before the closing capsule")
            return
        super().quic_event_received(event)


# ---------------------------------------------------------------------------
# The bodies, written by hand because they go crooked on purpose.
def capabilities(entries, version_v=1):
    out = struct.pack("!HH", version_v, len(entries))
    for n, v in entries:
        out += s(n) + s(v)
    return out


GOOD = [("video.codec", "hevc,av1"), ("video.bit_depth", "8,10"),
         ("audio.codec", "opus,pcm"), ("client.label_name", "banco-b5 0.1.0")]

# ⛔ `GOOD` without `client.label_name`, for the cases that must violate **a single
#    rule** on that name.  `GOOD + [("client.label_name", ...)]` carries `client.label_name`
#    TWICE, and §4.3 gives two distinct reasons to close — the duplicate and
#    the value — so a server that implemented only the first gave green
#    without ever having looked at the length of a value (finding R7.6).
WITHOUT_NAME = [v for v in GOOD if v[0] != "client.label_name"]


def ciao(entries=None, version_v=1):
    return wrap(0x0001, capabilities(GOOD if entries is None else entries, version_v))


def attach(tl=1920, ta=1080, vl=1920, va=1080, avail="it"):
    return wrap(0x0006, struct.pack("!IIII", tl, ta, vl, va) + s(avail))


def bench_mark(id_=1, color=0x00FF0000, delay=0):
    return wrap(0x000F, struct.pack("!III", id_, color, delay))


async def bench_outcome(cli, es, id_, outcome, motivo):
    """⛔ §7.5: `BENCH_OUTCOME` is verified FIELD BY FIELD.

    A server that answered `BENCH_OUTCOME(ACCEPTED)` with the function off
    would pass a bench that only looks at «an answer arrived and the session
    holds» — and it would paint little squares on someone's desktop.
    """
    label_name, body_el, _ = await b3.should_wait(cli, None, wait=6)
    if label_name != "0x0010":
        raise RuntimeError(f"expected BENCH_OUTCOME, arrived {label_name}")
    if len(body_el) < 14:
        raise RuntimeError(f"BENCH_OUTCOME of {len(body_el)} bytes: §7.5 wants 14")
    v_id, v_outcome, v_reason = struct.unpack("!IBB", body_el[:6])
    v_instant = struct.unpack("!Q", body_el[6:14])[0]
    es.bench = f"id={v_id} outcome={v_outcome} motivo={v_reason} instant={v_instant}"
    if (v_id, v_outcome, v_reason) != (id_, outcome, motivo):
        raise RuntimeError(
            f"BENCH_OUTCOME {es.bench}, expected id={id_} outcome={outcome} "
            f"motivo={motivo}")
    # ⛔ «`istante`: 0 if refused, and it is the only meaning of *absent*
    #    for this field» (§7.5, §6.0).
    if v_outcome == 2 and v_instant != 0:
        raise RuntimeError(f"refused, but `instant` is {v_instant} and not 0")


# ---------------------------------------------------------------------------
class Outcome:
    """What happened, from the receiving side."""

    def __init__(self):
        self.motivo = None        # from the FAREWELL / REJECTED — NEVER deduced
        self.reason_type = None   # ⛔ IN WHICH message it arrived (§11, §4.4)
        self.detail = ""
        self.code_wt = None     # from the closing of the session (§3.1 point 3)
        self.http_status = None    # for the path case
        self.messages = []        # the types that arrived, in order
        self.viva = False         # the session is still open at the end
        # ⛔ Did the violation really leave?  See point 1 of the docstring:
        #    without this mark a case that falls in the PREPARATION counts as
        #    green (finding R7.1).
        self.caused = False
        self.phase = "opening"     # where it stopped, if it stopped
        self.failure = None

    def __str__(self):
        p = []
        if self.http_status and self.http_status != "200":
            p.append(f":status={self.http_status}")
        if not self.caused:
            p.append(f"⛔ violation NEVER SENT (stopped in «{self.phase}»)")
        if self.motivo is not None:
            p.append(f"motivo={self.motivo:#04x}={REASONS.get(self.motivo, '?')}"
                     f" in {self.reason_type}")
        elif self.reason_type is not None:
            p.append(f"{self.reason_type} without a readable reason")
        p.append("chiusura-wt=" + ("(absent)" if self.code_wt is None
                                   else f"{self.code_wt:#04x}"))
        if self.viva:
            p.append("session ALIVE")
        if self.failure:
            p.append(f"failure={self.failure}")
        return "  ".join(p) if p else "nothing"


async def collect(cli, es, wait, grace=1.5):
    """Waits for the farewell, or for the end of the wait if the session holds.

    ⛔ **This is the only place where `es.motivo` is written**, and it writes it
       from a message that arrived on the wire (§8.1: from the receiving side).
    """
    expiry = asyncio.get_event_loop().time() + wait
    while True:
        stays = expiry - asyncio.get_event_loop().time()
        if stays <= 0:
            break
        try:
            m = await asyncio.wait_for(cli.messages.get(), timeout=stays)
        except asyncio.TimeoutError:
            break
        if m is None:
            break
        kind, body_el, _ = m
        es.messages.append(kind)
        if kind in (FAREWELL, REJECTED):
            # ⛔ It remembers WHICH of the two, because §4.4 and §11 tell them
            #    apart and the verdict asks for it (finding R7.9).
            es.reason_type = "FAREWELL" if kind == FAREWELL else "REJECTED"
            # ⛔ And an EMPTY body is not «no reason»: §7.1 wants `u8
            #    motivo` (plus `string detail` in the `FAREWELL`) and §3.1
            #    forbids code 0.  With `body_el[0] if body_el else None` a server that
            #    closes BADLY was easier to let through than one that closes
            #    well, because it left `motivo = None` (finding R7.2).
            if not body_el:
                es.failure = (f"{es.reason_type} with an EMPTY body: §7.1 wants "
                             "at least the reason byte")
                break
            es.motivo = body_el[0]
            if kind == FAREWELL and len(body_el) >= 3:
                n = struct.unpack("!H", body_el[1:3])[0]
                es.detail = body_el[3:3 + n].decode("utf-8", "replace")
            break
        if kind == BENCH_OUTCOME:
            break
    # ⛔ §3.1 POINT 3, AND WHY ONE WAITS.
    #
    #    The `FAREWELL` travels on the control channel, the closing of the
    #    session is a capsule on the session stream: they are two different
    #    roads and they arrive at two different moments.  Reading
    #    `close_code` at the exact instant the `FAREWELL` was read would
    #    measure «the second road did not arrive» every time the server sends
    #    it a millisecond later — that is it would measure our hurry.
    #    ⚠ The window is DECLARED and bounded: if it expires, the value stays
    #      `None` and the verdict counts it as missed, it does not hide it.
    if es.motivo is not None or es.failure is not None:
        fine = asyncio.get_event_loop().time() + grace
        while (cli.close_code is None and not cli.finished
               and asyncio.get_event_loop().time() < fine):
            await asyncio.sleep(0.02)
    es.code_wt = cli.close_code
    # ⛔ «Alive» means alive.  Before, it was enough that no reason had
    #    arrived, and a server that sent `HERE_I_AM` and then CLOSED the session
    #    without a farewell gave the line «the session holds» while it was dead
    #    (finding R7.2): the WebTransport closing and the `FIN` on the control
    #    channel enter the judgement, not only the printout.
    es.viva = (not cli.finished and es.motivo is None
               and es.code_wt is None and es.failure is None)


async def open_it(a, fpath="/rcp/1"):
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    authority = f"{a.address}:{a.port}"
    handler = connect(a.address, a.port, configuration=conf,
                      create_protocol=Client)
    cli = await handler.__aenter__()
    await asyncio.wait_for(cli.wait_connected(), timeout=8)
    cli.open_session(authority, fpath)
    state = await asyncio.wait_for(cli.accepted, timeout=8)
    return handler, cli, state


async def until_here_i_am(cli, body_el=None):
    cli.open_control()
    cli.send_it(body_el if body_el is not None else ciao())
    return await b3.should_wait(cli, "HERE_I_AM")


async def until_admitted(cli, a):
    await until_here_i_am(cli)
    cli.send_it(wrap(0x0003, s(a.username) + s(a.password)))
    return await b3.should_wait(cli, "ADMITTED", wait=20)


async def until_session(cli, a):
    await until_admitted(cli, a)
    cli.send_it(attach())
    return await b3.should_wait(cli, "SESSION")


# ===========================================================================
# THE CASES.  ⛔ Each declares its EXPECTATION before measuring (§1.11): the
#             «expected» column is a PREDICTION written in the file, not a
#             comment on the result.
# ===========================================================================
CASES = []


def case_v(label_name, expected_val, explain, dove="before"):
    def dec(f):
        CASES.append((label_name, expected_val, explain, dove, f))
        return f
    return dec


# ── The framing (§6.1) ─────────────────────────────────────────────────────
@case_v("tipo-sconosciuto", PROTOCOL_ERROR,
      "a type that does not exist on the control channel: §3 forbids ignoring it")
async def _(cli, a, es):
    await until_here_i_am(cli)
    cli.send_it(wrap(0x00FF, b""))


@case_v("tipo-del-server", PROTOCOL_ERROR,
      "HERE_I_AM sent BY THE CLIENT: known type, wrong direction (§7.1)")
async def _(cli, a, es):
    await until_here_i_am(cli)
    cli.send_it(wrap(0x0002, capabilities(GOOD)))


@case_v("lunghezza-in-piu", PROTOCOL_ERROR,
      "a good HELLO with four bytes of padding at the end (§6.0: no "
      "padding)")
async def _(cli, a, es):
    body_el = capabilities(GOOD) + b"\x00\x00\x00\x00"
    cli.open_control()
    cli.send_it(wrap(0x0001, body_el))


@case_v("lunghezza-in-meno", PROTOCOL_ERROR,
      "a length shorter than the fields the type expects")
async def _(cli, a, es):
    body_el = capabilities(GOOD)
    cli.open_control()
    # half the body is declared, and only those bytes are sent: the list of
    # capabilities is truncated halfway through a string
    cli.send_it(struct.pack("!HI", 0x0001, len(body_el) // 2) + body_el[:len(body_el) // 2])


@case_v("lunghezza-4gib", PROTOCOL_ERROR,
      "⛔ an announced length of 4 GiB: §6.1 forbids allocating before "
      "checking, and a server killed by the kernel «drops the connection» "
      "all the same — taking away everyone else's sessions (R3.3)")
async def _(cli, a, es):
    cli.open_control()
    cli.send_it(struct.pack("!HI", 0x0001, 0xFFFFFFFF))


@case_v("lunghezza-oltre-1mib", PROTOCOL_ERROR,
      "a message announcing more than 1 MiB (§6.1)")
async def _(cli, a, es):
    cli.open_control()
    cli.send_it(struct.pack("!HI", 0x0001, 2 * 1024 * 1024))


@case_v("stato-sbagliato", PROTOCOL_ERROR,
      "CREDENTIALS as the first message, before HELLO")
async def _(cli, a, es):
    cli.open_control()
    cli.send_it(wrap(0x0003, s(a.username) + s(a.password)))


@case_v("ciao-due-volte", PROTOCOL_ERROR,
      "a second HELLO after HERE_I_AM: the same message, the wrong state")
async def _(cli, a, es):
    await until_here_i_am(cli)
    cli.send_it(ciao())


# ── The version (§2.4, §9) ─────────────────────────────────────────────────
@case_v("versione-2", INCOMPATIBLE_VERSION,
      "⛔ HELLO(version_v=2) on /rcp/1: §2.4 says the two MUST coincide. "
      "⚠ §9 alone would say HERE_I_AM(1) — it is a contradiction of RCP.md")
async def _(cli, a, es):
    cli.open_control()
    cli.send_it(ciao(version_v=2))


@case_v("versione-0", INCOMPATIBLE_VERSION,
      "HELLO(version_v=0) on /rcp/1: on the other side of the same boundary")
async def _(cli, a, es):
    cli.open_control()
    cli.send_it(ciao(version_v=0))


# ── The capabilities (§4.3) ────────────────────────────────────────────────
@case_v("nome-maiuscolo", PROTOCOL_ERROR,
      "a capability name with capitals: §4.3 allows a-z 0-9 . _")
async def _(cli, a, es):
    cli.open_control()
    cli.send_it(ciao(GOOD + [("Video.Codec", "hevc")]))


@case_v("nome-65-byte", PROTOCOL_ERROR,
      "a 65-byte name: the limit of §4.3 is 64")
async def _(cli, a, es):
    cli.open_control()
    cli.send_it(ciao(GOOD + [("x" * 65, "si")]))


@case_v("nome-con-trattino-basso", None,
      "⭐ `video.max_size`: the underscore is LAWFUL, and it is the "
      "contradiction the B4 validator found in §4.3 on 10 August")
async def _(cli, a, es):
    cli.open_control()
    cli.send_it(ciao(GOOD + [("video.max_size", "3840x2160")]))
    await b3.should_wait(cli, "HERE_I_AM")


@case_v("valore-vuoto", PROTOCOL_ERROR,
      "an empty value: «whoever has nothing to say does not send the capability».  "
      "⛔ ONE violation only: `client.label_name` appears once and that is it")
async def _(cli, a, es):
    cli.open_control()
    cli.send_it(ciao(WITHOUT_NAME + [("client.label_name", "")]))


@case_v("valore-257-byte", PROTOCOL_ERROR,
      "a 257-byte value: the limit of §4.3 is 256.  ⛔ ONE violation "
      "only, for the same reason as the case above")
async def _(cli, a, es):
    cli.open_control()
    cli.send_it(ciao(WITHOUT_NAME + [("client.label_name", "x" * 257)]))


@case_v("capacita-ripetuta", PROTOCOL_ERROR,
      "`video.codec` twice: «the last one wins» and «the first one wins» are two "
      "implementations of the same document")
async def _(cli, a, es):
    cli.open_control()
    cli.send_it(ciao(GOOD + [("video.codec", "av1")]))


@case_v("capacita-del-lato-sbagliato", PROTOCOL_ERROR,
      "`bench.mark` sent BY THE CLIENT: §4.3 declares it the server's, and the "
      "name is known — the exception for unknown names does not cover it")
async def _(cli, a, es):
    cli.open_control()
    cli.send_it(ciao(GOOD + [("bench.mark", "si")]))


@case_v("capacita-sconosciuta", None,
      "⭐ a NAME that does not exist: it is ignored and one carries on — exception 1 of §3")
async def _(cli, a, es):
    cli.open_control()
    cli.send_it(ciao(GOOD + [("questa.non.path_exists", "dunno")]))
    await b3.should_wait(cli, "HERE_I_AM")


@case_v("solo-vp9", NOTHING_IN_COMMON,
      "`video.codec = vp9` and nothing else: it did not misspell, it has nothing "
      "to talk about — and the reason is NOT PROTOCOL_ERROR")
async def _(cli, a, es):
    cli.open_control()
    cli.send_it(ciao([("video.codec", "vp9"), ("video.bit_depth", "8"),
                    ("audio.codec", "pcm")]))


@case_v("hevc-e-vp9", None,
      "⭐ `video.codec = hevc,vp9`: `hevc` is read and one carries on, and the "
      "DISCARD is written in the server log (§4.3)")
async def _(cli, a, es):
    cli.open_control()
    cli.send_it(ciao([("video.codec", "hevc,vp9"), ("video.bit_depth", "8"),
                    ("audio.codec", "pcm")]))
    await b3.should_wait(cli, "HERE_I_AM")


@case_v("senza-pcm", NOTHING_IN_COMMON,
      "`audio.codec = opus` without `pcm`: §4.3 requires it of both, and whoever "
      "does not declare it takes leave with NOTHING_IN_COMMON — not with PROTOCOL_ERROR")
async def _(cli, a, es):
    cli.open_control()
    cli.send_it(ciao([("video.codec", "hevc"), ("video.bit_depth", "8"),
                    ("audio.codec", "opus")]))


@case_v("senza-8", NOTHING_IN_COMMON,
      "`video.bit_depth = 10` without `8`: likewise")
async def _(cli, a, es):
    cli.open_control()
    cli.send_it(ciao([("video.codec", "hevc"), ("video.bit_depth", "10"),
                    ("audio.codec", "pcm")]))


# ── The credentials (§4.4) ─────────────────────────────────────────────────
@case_v("utente-vuoto", PROTOCOL_ERROR,
      "⛔ zero-byte user: legal for §6.0, out of range for §4.4 — and "
      "without this check an attacker moves no counter")
async def _(cli, a, es):
    await until_here_i_am(cli)
    cli.send_it(wrap(0x0003, s("") + s(a.password)))


@case_v("parola-vuota", PROTOCOL_ERROR,
      "zero-byte password: likewise")
async def _(cli, a, es):
    await until_here_i_am(cli)
    cli.send_it(wrap(0x0003, s(a.username) + s("")))


@case_v("utente-257-byte", PROTOCOL_ERROR,
      "257-byte user: the limit of §4.4 is 256")
async def _(cli, a, es):
    await until_here_i_am(cli)
    cli.send_it(wrap(0x0003, s("u" * 257) + s(a.password)))


@case_v("parola-1025-byte", PROTOCOL_ERROR,
      "1025-byte password: the limit of §4.4 is 1024")
async def _(cli, a, es):
    await until_here_i_am(cli)
    cli.send_it(wrap(0x0003, s(a.username) + s("p" * 1025)))


@case_v("credenziali-due-volte", PROTOCOL_ERROR,
      "§4.4: a single attempt per connection")
async def _(cli, a, es):
    await until_admitted(cli, a)
    cli.send_it(wrap(0x0003, s(a.username) + s(a.password)))


# ── ATTACH (§4.5, §7.1) ───────────────────────────────────────────────────
@case_v("tela-1921x1080", PROTOCOL_ERROR,
      "odd canvas: the encoder would round it silently — two different sizes "
      "under the same label, error form E2")
async def _(cli, a, es):
    await until_admitted(cli, a)
    cli.send_it(attach(tl=1921))


@case_v("tela-319x240", PROTOCOL_ERROR, "canvas below the minimum of §4.5")
async def _(cli, a, es):
    await until_admitted(cli, a)
    cli.send_it(attach(tl=319, ta=240))


@case_v("tela-7682x4320", PROTOCOL_ERROR, "canvas above the maximum of §4.5")
async def _(cli, a, es):
    await until_admitted(cli, a)
    cli.send_it(attach(tl=7682, ta=4320))


@case_v("vista-300x801", None,
      "⭐ MUST PASS: §7.1 says the view does not have the canvas constraints — "
      "«any size from 1x1 up is legal, odd included» (R1.17)")
async def _(cli, a, es):
    await until_admitted(cli, a)
    cli.send_it(attach(vl=300, va=801))
    await b3.should_wait(cli, "SESSION")


@case_v("vista-1x1", None,
      "⭐ MUST PASS: the lower limit declared by §7.1, to the letter")
async def _(cli, a, es):
    await until_admitted(cli, a)
    cli.send_it(attach(vl=1, va=1))
    await b3.should_wait(cli, "SESSION")


@case_v("disposizione-malformata", PROTOCOL_ERROR,
      "`it!!` is not an XKB name: it misspelled")
async def _(cli, a, es):
    await until_admitted(cli, a)
    cli.send_it(attach(avail="it!!"))


@case_v("disposizione-sconosciuta", SESSION_UNSERVABLE,
      "⛔ `zz` is WELL FORMED and the machine does not have it: §4.5 wants TWO "
      "different faults, and the detail MUST be in the body (§8.2)")
async def _(cli, a, es):
    await until_admitted(cli, a)
    cli.send_it(attach(avail="zz"))


@case_v("disposizione-con-variante", None,
      "⭐ `de(neo)`: the form with the variant in parentheses is lawful (§4.5)")
async def _(cli, a, es):
    await until_admitted(cli, a)
    cli.send_it(attach(avail="de(neo)"))
    await b3.should_wait(cli, "SESSION")


# ── The bench function (§7.5) ──────────────────────────────────────────────
@case_v("banco-spento", None,
      "⛔ `BENCH_MARK` with the function off: there MUST arrive "
      "`BENCH_OUTCOME(RIFIUTATA, FUNCTION_OFF)` — not a silence and not a "
      "closing.  It is the DEFAULT state of every server")
async def _(cli, a, es):
    await until_session(cli, a)
    cli.send_it(bench_mark(id_=1, delay=0))
    await bench_outcome(cli, es, id_=1, outcome=2, motivo=1)  # RIFIUTATA, SPENTA


@case_v("banco-ritardo-20000", None,
      "`delay_ms = 20000`: `DELAY_OUT_OF_LIMITS`, and ⛔ **not** "
      "PROTOCOL_ERROR — dropping the session of the bench being calibrated "
      "is the bad idea §7.1 avoids for out-of-bounds sizes")
async def _(cli, a, es):
    await until_session(cli, a)
    cli.send_it(bench_mark(id_=7, delay=20000))
    await bench_outcome(cli, es, id_=7, outcome=2, motivo=2)  # RIFIUTATA, DELAY


@case_v("banco-id-zero", PROTOCOL_ERROR,
      "`id = 0`, which §7.5 declares reserved.  ⚠ The document does not say the outcome: "
      "here the drop is chosen, because it is a malformed message and not a "
      "wrong bench parameter")
async def _(cli, a, es):
    await until_session(cli, a)
    cli.send_it(bench_mark(id_=0))


@case_v("banco-prima-di-sessione", PROTOCOL_ERROR,
      "`BENCH_MARK` before `SESSION`: there is no frame to "
      "paint on")
async def _(cli, a, es):
    await until_admitted(cli, a)
    cli.send_it(bench_mark())


# ── The streams (§2.5) ─────────────────────────────────────────────────────
#
# ⛔ IN HERE THE PAYLOAD IS WELL FORMED ON PURPOSE, and it is not a detail.
#
#    The violation these four cases test is **the stream**: how many there
#    are, in which direction the channel goes, on which kind of stream it lives.
#    If a crooked message is also put inside — a `HELLO` with a zero-byte body,
#    a `kind` that does not exist — a server that does not count the streams
#    takes leave all the same, for the other reason, and the case is **green
#    without having tested anything** (finding R7.7).  Every payload below is
#    legal *in itself* and in the state in which it is sent: the only crooked
#    thing is the stream.
@case_v("secondo-bidirezionale", PROTOCOL_ERROR,
      "⛔ «the client MUST NOT open bidirectional streams beyond 0»: the "
      "control channel is ONE ONLY for the whole session.  The payload is "
      "a well-formed CREDENTIALS, which after HERE_I_AM is the right message: "
      "the only violation is the extra stream")
async def _(cli, a, es):
    await until_here_i_am(cli)
    other_one = cli.open_bidi()
    cli.send_on(other_one, wrap(0x0003, s(a.username) + s(a.password)))


@case_v("uni-controllo", PROTOCOL_ERROR,
      "the CONTROL channel (high byte 0x00) on a unidirectional stream: "
      "«control lives only on stream 0» (§2.5).  ⚠ CREDENTIALS and not "
      "HELLO: a second HELLO would also be a wrong state, that is a "
      "second reason to take leave")
async def _(cli, a, es):
    await until_here_i_am(cli)
    u = cli.open_uni()
    cli.send_on(u, wrap(0x0003, s(a.username) + s(a.password)))


@case_v("uni-video", PROTOCOL_ERROR,
      "the VIDEO channel (0x03) FROM THE CLIENT: wrong direction — video goes from "
      "server to client (§2.5).  ⛔ `0x0301` = key frame, which §6.2 "
      "declares LEGAL: with `0x0300` the only applicable rule was «other "
      "values: PROTOCOL_ERROR», and the direction was never put to the test")
async def _(cli, a, es):
    await until_here_i_am(cli)
    u = cli.open_uni()
    # the exact 28-byte header of §6.2: type, codec, width, height,
    # number, instant, input — all values within the limits
    cli.send_on(u, struct.pack("!HHIIIQI", 0x0301, 1, 1920, 1080, 1, 0, 0))


@case_v("uni-audio", PROTOCOL_ERROR,
      "the AUDIO channel (0x04) on a STREAM: audio lives only on datagrams "
      "(§2.5, §6.3).  The payload is the well-formed header of §6.3 — "
      "`kind = 0x0401`, `codec = 2` (PCM): the only violation is the stream")
async def _(cli, a, es):
    await until_here_i_am(cli)
    u = cli.open_uni()
    cli.send_on(u, struct.pack("!HHQ", 0x0401, 2, 0))


@case_v("uni-byte-alto-ignoto", PROTOCOL_ERROR,
      "a high byte that is none of the five of §2.5")
async def _(cli, a, es):
    await until_here_i_am(cli)
    u = cli.open_uni()
    cli.send_on(u, struct.pack("!HI", 0x0900, 0))


# ===========================================================================
async def run_case(a, label_name, expected_val, explain, f):
    es = Outcome()
    handler = None
    try:
        handler, cli, state = await open_it(a)
        es.http_status = state
        if state != "200":
            es.failure = f"the extended CONNECT answered {state}"
            return es
        es.phase = "preparation+violation"
        await f(cli, a, es)
        # ⛔ HERE, AND NOT BEFORE.  All the cases with an `expected_val` end with
        #    sending the crooked byte and wait for nothing afterwards: if `f`
        #    returns, the violation really left.  If instead it stopped earlier —
        #    the fixed `ATTACH` refused, the `HERE_I_AM` that does not arrive, PAM
        #    saying no — the case tested nothing and `caused` stays false,
        #    which is what the verdict looks at (finding R7.1).
        es.caused = True
        es.phase = "collection"
        # ⚠ On the cases that MUST pass one waits anyway: «it did not drop
        #   immediately» is not «it did not drop».
        await collect(cli, es, wait=3.0 if expected_val is None else 12.0)
    except Exception as e:  # noqa: BLE001 — the error type IS the measurement
        es.failure = f"{type(e).__name__}: {e}"
        # ⛔ AND THE REASON IS NOT SCRAPED FROM THE EXCEPTION TEXT.
        #
        #    Here there was a loop over `REASONS` that looked for the name of a
        #    §8.2 reason inside `str(e)` and took it as «reason arrived».  The
        #    defect: `b3.attendi` raises `RuntimeError("CONGEDO invece di
        #    SESSION: motivo 0x0b = PROTOCOL_ERROR")` even when what drops
        #    is the PREPARATION — and that string contains exactly the name of
        #    the expected reason.  R7.1 counted **twelve** that could be green
        #    with the crooked byte never sent, and ⚠ **it closed in on
        #    itself**: the more broken the server was upstream, the more those
        #    cases became green (finding R7.1, forms E6 and E7).
        #
        # ⭐ The reason is read by `collect`, from a message that arrived on the
        #    wire.  The exception text stays what it is: a diagnosis to print,
        #    not a verdict.
    finally:
        if handler is not None:
            try:
                await handler.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass
    return es


async def path(a):
    """⛔ §2.2: a WebTransport session on a different path is a 404.

    It stands apart because it is not an RCP violation: it is §3 applied **to
    the first byte**, before RCP begins — and in fact there is no FAREWELL to
    wait for, because there is no control channel.
    """
    outside = []
    for fpath, expected_val in (("/rcp/2", "404"), ("/", "404"),
                             ("/rcp/1", "200")):
        handler = None
        try:
            handler, cli, state = await open_it(a, fpath)
        except Exception as e:  # noqa: BLE001
            state = f"error {type(e).__name__}"
        finally:
            if handler is not None:
                try:
                    await handler.__aexit__(None, None, None)
                except Exception:  # noqa: BLE001
                    pass
        outside.append((fpath, expected_val, state, state == expected_val))
    return outside


async def still_alive(a):
    """⛔ B0.5 — the half nobody writes.

    It is not enough that the connection dropped: **it must be the connection
    that dropped, not the server**.  Here a new connection is opened and it
    gets as far as `HERE_I_AM`.
    ⚠ Not as far as `SESSION`: it would cost the fixed second of §4.4-bis at
      every case, that is forty seconds of bench for a property the full run
      at the end verifies once and well.
    """
    handler = None
    try:
        handler, cli, state = await open_it(a)
        if state != "200":
            return False, f":status {state}"
        await until_here_i_am(cli)
        return True, ""
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"
    finally:
        if handler is not None:
            try:
                await handler.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass


async def full_round(a):
    """The good handshake, whole: the check that says the server did not stay
    standing but useless."""
    handler = None
    try:
        handler, cli, state = await open_it(a)
        if state != "200":
            return False, f":status {state}"
        await until_session(cli, a)
        return True, ""
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"
    finally:
        if handler is not None:
            try:
                await handler.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass


async def limiter(a):
    """⛔ §4.4-bis, and the two halves that get forgotten.

    a) MALFORMED messages move no counter: six out-of-range `CREDENTIALS`,
       and then a good one that MUST pass;
    b) the **per-address** counter really exists: six failed attempts with
       SIX DIFFERENT NAMES from the same address, and the seventh — again a new
       name — must receive `TOO_MANY_ATTEMPTS`.

    ⚠ **Prediction written before measuring**: (b) will be RED.  The key of
      the per-address counter is the `provenance`, which contains **the port** —
      and with a single attempt per connection (§4.4) the port changes every
      time, so that counter is always 1 and never blocks anyone.  It is the
      worst shape: code present, that looks right, and that does
      nothing.
    """
    outside = {}
    # (a) six malformed, then a good one
    for i in range(6):
        handler, cli, _ = await open_it(a)
        try:
            await until_here_i_am(cli)
            cli.send_it(wrap(0x0003, s("") + s("x")))
            await asyncio.sleep(0.2)
        except Exception:  # noqa: BLE001
            pass
        finally:
            await handler.__aexit__(None, None, None)
    ok, reason_text = await full_round(a)
    outside["malformati-non-contano"] = (ok, reason_text)

    # (b) seven failed with SEVEN DIFFERENT NAMES, from the same address
    reasons = []
    for i in range(7):
        handler, cli, _ = await open_it(a)
        es = Outcome()
        try:
            await until_here_i_am(cli)
            cli.send_it(wrap(0x0003, s(f"nobody{i}") + s("wrong")))
            # ⚠ The answer is AWAITED instead of sleeping for a time chosen by
            #   eye: PAM has its own delay on failures, and a `sleep` that is
            #   too short would measure a counter that has not been
            #   incremented yet.
            await collect(cli, es, wait=15)
        except Exception:  # noqa: BLE001
            pass
        finally:
            await handler.__aexit__(None, None, None)
        reasons.append(es.motivo)
    # The first five are WRONG_CREDENTIALS; from the sixth on the threshold of
    # §4.4-bis has passed, and the PER-ADDRESS counter must speak.
    outside["contatore-per-indirizzo"] = (
        reasons[-1] == TOO_MANY_ATTEMPTS,
        "reasons: " + " ".join(
            REASONS.get(m, str(m)) if m is not None else "-" for m in reasons))

    # ⛔ AND THE CHECK THAT TELLS A COUNTER FROM A BLOCK: now the RIGHT
    #    password, from the same address, MUST receive TOO_MANY_ATTEMPTS all
    #    the same.  A server that counted without blocking would give the same
    #    line as above and let in anyone who guessed at the sixth try.
    handler, cli, _ = await open_it(a)
    es = Outcome()
    try:
        await until_here_i_am(cli)
        cli.send_it(wrap(0x0003, s(a.username) + s(a.password)))
        await collect(cli, es, wait=15)
    except Exception:  # noqa: BLE001
        pass
    finally:
        await handler.__aexit__(None, None, None)
    outside["blocca-anche-la-parola-giusta"] = (
        es.motivo == TOO_MANY_ATTEMPTS,
        f"with the GOOD credentials: {REASONS.get(es.motivo, es.motivo)}")
    return outside


GREEN, RED, GRAY = "\033[1;32m", "\033[1;31m", "\033[0m"


def row(ok, label_name, body_text):
    print(f"    {GREEN if ok else RED}{'OK' if ok else 'NO'}{GRAY}  "
          f"{label_name:26s} {body_text}")


def final_outcome(counts, faults, partial, reg=None):
    """⛔ Every count with its denominator, and the denominator COMPUTED.

    The old line printed `N su N` — the same expression twice — and only when
    `faults == 0`, that is it carried no information the colour did not already
    carry (finding R7.14).  ⚠ And a denominator of **zero** is said, not
    hidden: «0 out of 0» is not a green.
    """
    print()
    print("    == what this run really looked at")
    for desc, (good_n, tot) in counts.items():
        if tot == 0:
            # ⛔ A zero denominator is DECLARED: «nobody looked» and «all
            #    passed» look the same if one keeps quiet.
            print(f"    --  {desc:44s} no case triggered it")
            continue
        clr = GREEN if good_n == tot else RED
        print(f"    {clr}{good_n:3d} out of {tot:3d}{GRAY}  {desc}")
    print()
    # ⛔ And the verdict goes into the log with the target inside, or in six
    #    months «B5 passes» will not say against which of the two servers.
    if reg is not None:
        reg.put_out({"kind": "verdict", "faults": faults, "partial": partial,
                    "counts": {k: v for k, v in counts.items()}})
        print(f"    --  {reg.summary()}")
    if faults:
        print(f"    {RED}⛔ B5: {faults} points do not pass against "
              f"«{reg.target if reg else '?'}»{GRAY}")
        return 1
    if partial:
        print(f"    {GREEN}⭐ the selected cases pass{GRAY} — ⚠ and this "
              f"is NOT «B5 passes»: the run was partial")
        return 0
    print(f"    {GREEN}⭐ B5 passes against «{reg.target if reg else '?'}», and the "
          f"numbers above say on what{GRAY}")
    print(f"    ⚠ and it is not «B5 passes»: the other target is another program, "
          f"and this run says nothing about it")
    return 0


def tally(cases):
    """⛔ The two numbers, COMPUTED — and they are two, not one.

    «44 violations out of 44» printed the same expression as numerator and as
    denominator, and counted in it also the eight cases that MUST pass, on
    which «the right reason every time» is false by construction (finding
    R7.14).  From here on the number is produced by this function, and no
    comment rewrites it by hand.
    """
    violations = sum(1 for c in cases if c[1] is not None)
    return violations, len(cases) - violations


async def primary(a):
    cases = [c for c in CASES if not a.solo or a.solo in c[0]]
    tot_v, total_green = tally(CASES)
    if a.listing:
        print(f"== B5: {len(CASES)} cases — {tot_v} violations and {total_green} "
              f"⭐ expected greens.  Every line is a PREDICTION\n")
        for label_name, expected_val, explain, dove, _ in CASES:
            expect = (f"{expected_val:#04x} {REASONS.get(expected_val, '?')}" if expected_val
                   else "⭐ MUST PASS")
            print(f"  {label_name:26s} {expect}")
            print(f"  {'':26s}   {explain}")
        return 0

    # ⛔ ZERO CASES IS NOT «ALL PASSED».
    #
    #    `--solo pippo` matched no name, the loop did not run, and the bench
    #    printed «0 violations out of 0» and exited 0: a typo in the filter was
    #    indistinguishable from a green bench (finding R7.15).  ⭐ They are THREE
    #    outcomes — nothing to measure, does not pass, passes — and they want
    #    three different exit codes.
    if not cases:
        print(f"    {RED}⛔ «--solo {a.solo}» selected ZERO cases out of "
              f"{len(CASES)}: there is nothing to measure{GRAY}")
        print("       This is NOT a green.  The names are read with --listing.")
        return 2

    sel_v, sel_green = tally(cases)

    # ⛔ THE RUN'S LOG, AND THE FIRST LINE SAYS AGAINST WHAT ONE MEASURES.
    #
    #    Until 11 Aug 2026 B5 had **no** log: it ran, and the output was on
    #    screen.  ⚠ Which means that none of its forty-four outcomes is
    #    re-verifiable today, and that the day two runs say different things
    #    there will be no way of knowing which server answered which.
    a.reg = b0.Log(a.out_dir, a.target, a.port, a.lap or None,
                        a.md5 or None)
    prof = a.reg.profile_v
    a.reg.open_round(
        "B5", "violations sent on a new connection per case; the "
              "server is started by 01-b5-lancia.sh and no moving scene "
              "is needed",
        extra={"casi_selezionati": len(cases), "total_cases": len(CASES),
               "filter": a.solo, "violations": sel_v, "verdi_attesi": sel_green,
               # ⛔ THE ECHO: on the product it is not there, and the difference
               #    is written BEFORE measuring.  `src/webtransport.c`
               #    `discard_extra_stream()`: «the bytes are thrown away, and
               #    NOT sent back».  ⚠ A bench that waited for it would stay
               #    hanging, and on 10 Aug 2026 that red was diagnosed for
               #    hours as a «certificate defect».  B5 does not wait for it:
               #    it discards it if it arrives, and here declares whether it
               #    was supposed to arrive.
               "expected_echo": prof["echo"]})
    print(f"== B5 — the violation tests against the server")
    print(f"   ⛔ TARGET: {a.target} · port {a.port} · binary md5 "
          f"{(a.md5 or 'unknown')[:12]}…")
    print(f"      {prof['executable']}")
    print(f"   ⚠ B2's echo on the streams opened by the bench: "
          f"{'expected' if prof['echo'] else '⛔ NOT expected on this target'}")
    print(f"   this run's log: {a.out_dir or '⛔ NONE'}")
    print(f"   {len(cases)} cases out of {len(CASES)} selected: {sel_v} violations "
          f"and {sel_green} ⭐ expected greens")
    print("   ⛔ every case: the violation really sent, the right reason in the "
          "right message,")
    print("      the two roads of §3.1, and the server still alive afterwards\n")
    if a.solo:
        print(f"    ⚠ PARTIAL RUN.  The path (§2.2), the full run and the")
        print(f"      limiter (§4.4-bis) are NOT run: they do not depend on the")
        print(f"      selected cases, and running them here would say «passes» on a")
        print(f"      part of the bench nobody asked to measure.\n")

    # ⛔ EVERY COUNT WITH ITS DENOMINATOR, and the denominators are different
    #    because the measured properties are different.
    counts = {
        "violations with the expected reason": [0, 0],
        "⭐ expected greens, session alive": [0, 0],
        "§3.1 point 3 — reason in the WT closing": [0, 0],
        "§11 — reason in the right message": [0, 0],
    }
    faults, dead = 0, False
    for label_name, expected_val, explain, dove, f in cases:
        es = await run_case(a, label_name, expected_val, explain, f)
        if expected_val is None:
            counts["⭐ expected greens, session alive"][1] += 1
            # ⛔ `viva` was COMPUTED and not looked at: it was enough that no
            #    reason had arrived, so a server that sends HERE_I_AM and then
            #    closes the WebTransport session gave the line «the session
            #    holds» while the session was dead (finding R7.2).
            ok = es.viva and es.failure is None
            body_text = ("the session holds" if ok else str(es))
            counts["⭐ expected greens, session alive"][0] += int(ok)
        else:
            counts["violations with the expected reason"][1] += 1
            expected_in = CARRIER.get(expected_val, "FAREWELL")
            # §11: «at least one of the two roads» must have carried the reason.
            routes = []
            if es.motivo == expected_val and es.reason_type == expected_in:
                routes.append(expected_in)
            if es.code_wt == expected_val:
                routes.append("chiusura-WT")
            ok = es.caused and bool(routes)
            counts["violations with the expected reason"][0] += int(ok)
            body_text = str(es)
        row(ok, label_name, body_text)
        # ⛔ And the fact goes to the log BEFORE any conclusion: a case that
        #    brings the bench down (the server dying) must have left its own
        #    line, or the log would only tell about the runs that went well.
        a.reg.put_out({"kind": "case_v", "label_name": label_name, "outcome": bool(ok),
                      "expected_val": expected_val, "motivo": es.motivo,
                      "reason_type": es.reason_type, "code_wt": es.code_wt,
                      "caused": es.caused, "phase": es.phase,
                      "failure": es.failure, "detail": es.detail,
                      "viva": es.viva})
        if not ok:
            faults += 1
            print(f"        expected: "
                  + (f"{expected_val:#04x} {REASONS.get(expected_val, '?')}" if expected_val
                     else "⭐ no drop"))
            print(f"        {explain}")
            if expected_val is not None and not es.caused:
                print(f"        ⛔ and the violation NEVER LEFT: the case "
                      f"stopped in «{es.phase}».  It is not a failed test, "
                      f"it is a test not done")
        if es.detail:
            print(f"        detail from the body: «{es.detail}»")
        if getattr(es, "bench", None):
            print(f"        BENCH_OUTCOME: {es.bench}")
        if expected_val is not None and es.caused:
            # ⛔ §3.1 POINT 3 IS COUNTED, NOT PRINTED.
            #
            #    Here there was a line that said «the reason arrived via
            #    CONGEDO» even when the second road had not arrived at all —
            #    true, and capable of making one believe the opposite — and
            #    `faults` was not touched in any of the three branches: R7.3
            #    showed that ALL the violations stayed green with point 3
            #    never implemented.
            #    Point 3 is an **unconditional** MUST: the condition of §3.1
            #    is on point 2, and it is point 3 that the document calls
            #    «the one that saves the diagnoses».
            counts["§3.1 point 3 — reason in the WT closing"][1] += 1
            if es.code_wt == expected_val:
                counts["§3.1 point 3 — reason in the WT closing"][0] += 1
            else:
                faults += 1
                seen_v = ("absent" if es.code_wt is None
                         else f"{es.code_wt:#04x}")
                row(False, "", f"   §3.1 point 3 on «{label_name}»: the closing "
                                f"of the session carries {seen_v}, expected "
                                f"{expected_val:#04x}")
            # ⛔ AND IN WHICH MESSAGE (§11, §4.4).
            if es.motivo is not None:
                counts["§11 — reason in the right message"][1] += 1
                if es.reason_type == CARRIER.get(expected_val, "FAREWELL"):
                    counts["§11 — reason in the right message"][0] += 1
                else:
                    faults += 1
                    row(False, "", f"   §11 on «{label_name}»: the reason arrived "
                                    f"in {es.reason_type}, and §11 wants it in "
                                    f"{CARRIER.get(expected_val, 'FAREWELL')} — they are "
                                    f"two different state machines")
        # ⛔ and the server afterwards?
        alive, reason_text = await still_alive(a)
        if not alive:
            row(False, "", f"⛔ THE SERVER NO LONGER ANSWERS after «{label_name}»: {reason_text}")
            faults += 1
            dead = True
            break

    if dead:
        print(f"\n    {RED}⛔ the bench stops: without a server there is "
              f"nothing to measure{GRAY}")
        # ⚠ And what had been looked at UP TO THERE is printed anyway: a bench
        #   that stops without saying how much it had covered lets one believe
        #   it had covered everything.
        return final_outcome(counts, faults, partial=True, reg=a.reg)

    # ⛔ UNDER A FILTER THESE THREE SECTIONS ARE NOT RUN, and it is declared.
    #
    #    They do not depend on the selected cases: running them on a partial
    #    selection passes off as «B5 passes» a measurement nobody asked for —
    #    and in the case of the limiter it blocks the address for thirty seconds
    #    for someone who was only retrying a case.  It is the twin of
    #    R7.15(b), which in the launch script gave red on a rule never triggered.
    if a.solo:
        print(f"\n    ⚠ partial run: path, full run and limiter "
              f"skipped (see above)")
        return final_outcome(counts, faults, partial=True, reg=a.reg)

    print("\n== ⛔ The session path (§2.2), which comes before RCP")
    for fpath, expected_val, state, ok in await path(a):
        row(ok, fpath, f":status = {state}   (expected {expected_val})")
        if not ok:
            faults += 1

    # ⛔ THE FULL RUN COMES BEFORE THE LIMITER, and the order is a measurement.
    #
    #    The limiter of §4.4-bis, when it works, **blocks the address** — and
    #    from that moment even the right password receives
    #    TOO_MANY_ATTEMPTS, for a window that starts at thirty seconds.  ⚠ A
    #    bench that put the good handshake AFTER would read that refusal as
    #    «the server is broken», that is it would give red precisely when the
    #    rule works.
    print("\n== ⭐ The good handshake, whole")
    ok, reason_text = await full_round(a)
    row(ok, "giro-completo", reason_text or "HELLO → CREDENTIALS → ATTACH → SESSION")
    if not ok:
        faults += 1

    print("\n== ⛔ The attempt limiter (§4.4-bis) — last, and it says why")
    print(f"   ⚠ and on this target the ban lives in «{a.target}»: the ban")
    print(f"     file belongs to B5 only, and the final unblock is done by the launch")
    print(f"     script, AFTER this section and declaring it (B0.3)")
    print("   ⚠ from here on this address stays BLOCKED for at least thirty")
    print("     seconds: it is the rule working, not a fault of the bench")
    for label_name, (ok, reason_text) in (await limiter(a)).items():
        row(ok, label_name, reason_text)
        if not ok:
            faults += 1

    return final_outcome(counts, faults, partial=False, reg=a.reg)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="B5 — the violations against the server")
    p.add_argument("--address", default="192.168.0.2")
    # ⛔ The port NO LONGER has a default that names a target: 7447 is the
    #    graft and 7448 the product, and a default here would mean that
    #    `--target product` without `--port` measures the graft while
    #    declaring the product.  It is passed by `01-b0-bersaglio.sh`, which is
    #    the only place where the two ports are written.
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--username", default="prova")
    p.add_argument("--password", default="parola-di-prova")
    p.add_argument("--solo", default="", help="run only the cases that contain this")
    p.add_argument("--listing", action="store_true",
                   help="print the predictions without measuring")
    b0.add_arguments(p)
    # ⚠ `--listing` measures nothing and does not need a port: it is checked
    #   before demanding it, or printing the predictions would require having
    #   already chosen a server.
    import sys as _s
    if "--listing" in _s.argv:
        for _i, _az in enumerate(p._actions):
            if _az.dest == "port":
                _az.required = False
    sys.exit(asyncio.run(primary(p.parse_args())))
