#!/usr/bin/env python3
# ⭐ UPDATED 25 Oct 2026 (D4b of DECISIONS-11.md §11.50) FOR TODAY'S TREE — THREE SCENES, chosen with `--wait`:
#   free       HEALTHY: as always — A inside (SESSION), a third party with WRONG credentials (must be 0x07 and the PAM is really asked),
#              the marks of A never stop (< 150 ms) and a second handshake B stays < 300 ms.  (The old «blocked» expectation is gone:
#              the synchronous PAM fallback it described no longer exists.)
#   unchecked  FAULT «no helper»: against a target built with `02-pam-start.sh fault` (asynchronous hook not connected).  20 attempts in
#              a row from one address, the first with the RIGHT password: every answer must be REJECTED 0x0E (never 0x07, never the
#              ban's 0x08 — nothing is counted) and a handshake started during each stays < 300 ms (the wire never stuck).
#   restart    REPAIRED: against a healthy target, `02-pam-start.sh kill-helper` (SIGKILL), then: a login attempt while the helper is down
#              gets 0x0E (not counted), and within `--restart-wait` s a login with the right password is ADMITTED again — the helper was
#              started again by itself (1 s pause); a handshake ruler runs the whole time and never exceeds 300 ms; the target's log
#              (`--log`) must carry the «RESTART» line.
#   No desktop is needed for `unchecked` and `restart` (they stop at ADMITTED/REJECTED); `free` needs a machine where `prova` gets a SESSION.
# HOW TO RUN (as root, on a box with /etc/pam.d/remotix, the account `prova`, ss, aioquic, and the product's build dependencies):
#   export TMPDIR=/media/REMOTIX-15/tmp   # anywhere writable
#   bash benches/02-pam-start.sh copy && bash benches/02-pam-start.sh start      # healthy target on :7531
#   printf '%s\n' 'THE-PASSWORD-OF-prova' > $TMPDIR/pam-pw && chmod 600 $TMPDIR/pam-pw
#   python3 benches/02-pam-standstill.py --address 127.0.0.1 --port 7531 --user prova --password-file $TMPDIR/pam-pw \
#       --socket $TMPDIR/02-pam-tmp/pam2-7531.sock --wait free --rounds 5                  # scene 1
#   python3 benches/02-pam-standstill.py ... --wait restart --log $TMPDIR/02-pam-tmp/pam2-7531.log   # scene 3 (kills and heals)
#   bash benches/02-pam-start.sh stop; bash benches/02-pam-start.sh copy && bash benches/02-pam-start.sh fault && bash benches/02-pam-start.sh start
#   python3 benches/02-pam-standstill.py ... --wait unchecked                           # scene 2
#   bash benches/02-pam-start.sh stop
# Exit: 0 expectation met · 1 not met · 2 cannot run · 3 not measured.
"""02-pam-standstill.py — ⛔ HOW LONG WHOEVER IS **NOT** AUTHENTICATING STANDS STILL.

    python3 02-pam-standstill.py --port 7531 --password-file F --rounds 5

===========================================================================
⛔ WHY THIS BENCH EXISTS, AND WHY ONE ALREADY WRITTEN WAS NOT ENOUGH

`DECISIONS.md` §1.10, 11 Aug 2026, from the user: the PAM check blocks
the server's single `poll` loop, and it is cured **before phase 2**.  ⛔ And the
line that orders this file is the last one of that decision:

    «The property to prove is NOT "PAM still works": it is "while one is
     authenticating, the others do not notice" — and today there is no
     bench that looks at it.  Without that bench the cure is a hope.»

⛔ **B8 cannot do it, and it is not an oversight of its own**: B8 times the answer
   to `CREDENTIALS`, that is **the time of whoever is getting in**.  That number is governed
   by PAM (`[M]` 11 Aug: +1034 ms beyond the fixed second on the rejected ones,
   the signature of `pam_faildelay`) and ⭐ **after the cure it must stay what it
   is**.  Whoever measured only that would see a successful cure as a
   failure, or — worse — would see nothing and call the hope
   green.

⇒ Here **the other number** is measured: how long whoever has already
  authenticated, or whoever is doing something else entirely, stands still WHILE a third party presents
  wrong credentials (the slow case, the one with `pam_faildelay`).

===========================================================================
⛔ THE SCENE, DECLARED — three connections, and each has a job

    A   «already inside»    full handshake up to `SESSION`, user
                            `prova`.  ⭐ **It is the ruler**: once attached it sends
                            `BENCH_MARK` (§7.5) every 50 ms and times the
                            `BENCH_OUTCOME` that comes back.  It is the only
                            request/response pair RCP grants an
                            ACTIVE session in phase 1 — from phase 2 a frame
                            will take its place, and the number will mean the
                            same thing: **how long the screen of whoever is
                            already working stands still**;

    C   «the slow case»     opens, reaches `wait-credentials`, and sends
                            `CREDENTIALS` with the **WRONG** password.  ⛔ The
                            reason of the `REJECTED` is read and required to be
                            `0x07 WRONG_CREDENTIALS`: a `0x08
                            TOO_MANY_ATTEMPTS` means the address was
                            banned and ⛔ **PAM was not even
                            queried** — that is the sample would measure a
                            server that did not do the slow thing.  That
                            sample is THROWN AWAY, and the reason is said;

    B   «the second one     is born the instant C sends `CREDENTIALS`, and
        doing the handshake» times **from zero to `HERE_I_AM`**.  It is the second
                            ruler, the one the mandate names first:
                            any user who opens the page while
                            another gets the password wrong.

⛔ **The denominator that makes everything readable**: before the window,
   20 marks are timed on a quiet loop.  ⭐ If the quiet median were not
   small, the ruler would be broken and there would be nothing to
   compare — and the bench says so instead of dividing by a number it has not
   looked at (`LESSONS.md` §1.9: a denominator is read where the thing happens).

===========================================================================
⭐ THE POSITIVE CONTROL, AND HERE IT IS STRONGER THAN USUAL

«Can the tool find something that is surely there?»  ⛔ Yes, and it is **the round
of BEFORE**: the phase 1 server has the blocking, measured, and this bench
**must see it**.  A «before» round that did not find the pause would not prove
that the server is healthy: it would prove that this file cannot measure — and
any green «after» would be the worst of proofs (`CODER.md` §4.6).

⇒ **The expectation, written before the round** (and repeated by `--prediction`):

  | | BEFORE (phase 1) | AFTER (the cure) |
  |---|---|---|
  | the peak of the mark during the window | ⛔ **≥ 900 ms**, and close to the time PAM takes (1.0-2.2 s) | ⭐ **< 150 ms**, that is the order of magnitude of the quiet loop |
  | A's stalled time (sum of the excesses) | ⛔ ≈ the duration of PAM | ⭐ ≈ 0 |
  | B's handshake | ⛔ **≥ 900 ms** | ⭐ **< 300 ms** |
  | ⚠ C's time (whoever authenticates) | 1.0-2.2 s | ⭐ **THE SAME**, and that is fine |

⛔ **And the opposite case, that is what a cure that does NOT work would look like**:
   the peak of the mark stays ≥ 900 ms and B's handshake stays ≥ 900 ms,
   **while C's time does not change** — that is exactly the same
   picture as the «before», with the new code inside.  ⭐ It is the case that
   `--fault` of `02-pam-launch.sh` injects on purpose, and that this bench MUST
   colour red.

===========================================================================
⛔ WHAT THIS BENCH DOES **NOT** MEASURE, so that nobody appropriates it

  · the fixed second of §4.4-bis and the address ban: they are **B8's**, and
    this file does not judge them.  ⚠ It only OBSERVES them as much as needed to
    throw away the dirty samples (reason `0x08`);
  · the correctness of PAM: if `prova` does not get in, this bench stops and says
    so — ⛔ it does not go on measuring a scene in which A is not inside, which
    would give a green number because there was nothing to block (E1).

===========================================================================
⛔ ZERO AND FAILURE ARE TWO DIFFERENT THINGS (`REVIEWER.md` §1 point 4)

Every outcome carries `valido: true//false` and, when it is false, **why**.  A
round that could not measure does not write «0 ms»: it writes that it did not measure.
"""
import argparse
import asyncio
import json
import os
import socket
import ssl
import statistics
import struct
import subprocess
import sys
import time
from contextlib import AsyncExitStack

# ⛔ THE IMPORT IS INSIDE A `try`, AND NOT OUT OF LENIENCY — `--prediction` must
#    be able to run on the documents machine, where `aioquic` is not there.  ⚠ But
#    «the library is not there» does NOT become «the round went fine»: without `aioquic`
#    any real round stops with a message that names the library,
#    instead of a traceback that names a random line.
try:
    from aioquic.asyncio import connect
    from aioquic.asyncio.protocol import QuicConnectionProtocol
    from aioquic.h3.connection import H3_ALPN, H3Connection
    from aioquic.h3.events import HeadersReceived
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.quic.events import QuicEvent
    AIOQUIC = None
except ImportError as _e:            # noqa: N816
    AIOQUIC = str(_e)
    QuicConnectionProtocol = object
    QuicEvent = object

T = {"HELLO": 0x0001, "HERE_I_AM": 0x0002, "CREDENTIALS": 0x0003, "ADMITTED": 0x0004,
     "REJECTED": 0x0005, "ATTACH": 0x0006, "SESSION": 0x0007, "FAREWELL": 0x000C,
     "BENCH_MARK": 0x000F, "BENCH_OUTCOME": 0x0010}
NAME = {v: k for k, v in T.items()}
REASONS = {0x01: "CLOSED_BY_USER", 0x07: "WRONG_CREDENTIALS",
          0x08: "TOO_MANY_ATTEMPTS", 0x09: "NOTHING_IN_COMMON",
          0x0A: "INCOMPATIBLE_VERSION", 0x0B: "PROTOCOL_ERROR",
          0x0C: "SERVER_CLOSING", 0x0D: "TIMED_OUT",
          0x0E: "SESSION_UNSERVABLE", 0x0F: "ALREADY_ACTIVE_REMOTELY"}

# ⛔ The thresholds sit HERE, at the top and with a name, so that the expectation
#    is not adjusted once the round is over.  They are those written in the box above.
BLOCKED_PEAK_MS = 900.0   # above: the loop stopped (the «before»)
FREE_PEAK_MS = 150.0     # below: the loop did not stop (the «after»)
TIGHT_FREE_MS = 300.0
BASE_MAX_MS = 60.0          # the quiet loop: above, the ruler is broken


def s(t):
    b = t.encode("utf-8") if isinstance(t, str) else t
    return struct.pack("!H", len(b)) + b


def wrap(kind, body):
    return struct.pack("!HI", kind, len(body)) + body


def body_hello():
    entries = [("video.codec", "hevc,av1"), ("video.depth", "8,10"),
            ("audio.codec", "opus,pcm"), ("video.level", "5.1"),
            ("video.max_size", "3840x2160"), ("clipboard.text", "yes"),
            ("input.touch", "no"), ("client.name", "02-pam-standstill 0.1.0")]
    out = struct.pack("!HH", 1, len(entries))
    for n, v in entries:
        out += s(n) + s(v)
    return out


class Drop(RuntimeError):
    pass


class Client(QuicConnectionProtocol):
    """⚠ Written looking at `RCP.md`, not `src/rcp.c`: two programs that
    agree because the same hand wrote them confirm nothing
    (`PLAN.md` §1.1).  ⛔ What is copied here from `01-b3-client.py` are the
    TWO `aioquic` traps already paid for on 10 Aug 2026, and they are copied
    on purpose: do not pass the WebTransport stream events to its H3 layer,
    and do not read `0` as «no stream»."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._http = H3Connection(self._quic, enable_webtransport=True)
        self.accepted = asyncio.get_event_loop().create_future()
        self.session = None
        self.check = None
        self.incoming = bytearray()
        self.messages = asyncio.Queue()
        self.drop = None

    def _cade(self, why):
        if self.drop is None:
            self.drop = why
            self.messages.put_nowait(None)

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
        self.check = self._http.create_webtransport_stream(
            self.session, is_unidirectional=False)
        return self.check

    def send_msg(self, data):
        self._quic.send_stream_data(self.check, data, end_stream=False)
        self.transmit()

    def quic_event_received(self, event: QuicEvent) -> None:
        name = type(event).__name__
        if name == "ConnectionTerminated":
            self._cade(f"connection TERMINATED: code "
                       f"{getattr(event, 'error_code', '?')}")
            return
        if name == "StreamDataReceived" and event.stream_id == self.check:
            # ⛔ And it is NOT passed to aioquic's H3 layer: it would read it as a
            #    DATA frame and kill the connection (`[M]` 10 Aug 2026).
            self.incoming += event.data
            while len(self.incoming) >= 6:
                kind, lung = struct.unpack("!HI", self.incoming[:6])
                if len(self.incoming) < 6 + lung:
                    break
                body = bytes(self.incoming[6:6 + lung])
                del self.incoming[:6 + lung]
                self.messages.put_nowait((kind, body))
            if event.end_stream:
                self._cade("the control channel closed")
            return
        if name == "StreamDataReceived" and event.stream_id == self.session:
            if event.end_stream:
                self._cade("the WebTransport session closed")
        for ev in self._http.handle_event(event):
            if isinstance(ev, HeadersReceived) and not self.accepted.done():
                self.accepted.set_result(
                    dict(ev.headers).get(b":status", b"?").decode())


async def should_wait(cli, which, wait=25.0):
    """Waits for ONE message and requires it to be that one. Returns (name, body).

    ⛔ A `FAREWELL` or a `REJECTED` are not «another message»: they are the
       measurement, and must be named with their reason or the diagnosis points at
       nothing."""
    m = await asyncio.wait_for(cli.messages.get(), timeout=wait)
    if m is None:
        raise Drop(f"the session dropped: {cli.drop}")
    kind, body = m
    name = NAME.get(kind, f"{kind:#06x}")
    if which and name != which:
        reason = body[0] if body else 0
        if name in ("FAREWELL", "REJECTED"):
            raise Drop(f"{name} instead of {which}: reason {reason:#04x} = "
                         f"{REASONS.get(reason, '?')}")
        raise Drop(f"expected {which}, got {name}")
    return name, body


async def do_open(stack, address, port, fpath):
    """Opens QUIC + the WebTransport session + the control channel."""
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    authority = f"{address}:{port}"
    cli = await stack.enter_async_context(
        connect(address, port, configuration=conf, create_protocol=Client))
    await asyncio.wait_for(cli.wait_connected(), timeout=10)
    cli.open_session(authority, fpath)
    state = await asyncio.wait_for(cli.accepted, timeout=10)
    if state != "200":
        raise Drop(f"the extended CONNECT answered {state}, not 200")
    cli.open_control()
    return cli


async def until_here_i_am(cli):
    cli.send_msg(wrap(T["HELLO"], body_hello()))
    await should_wait(cli, "HERE_I_AM")


async def until_session(cli, user, password, width=1920, height=1080):
    await until_here_i_am(cli)
    cli.send_msg(wrap(T["CREDENTIALS"], s(user) + s(password)))
    t0 = time.monotonic()
    await should_wait(cli, "ADMITTED", wait=30)
    ms_admitted = (time.monotonic() - t0) * 1000
    cli.send_msg(wrap(T["ATTACH"],
                       struct.pack("!IIII", width, height, width,
                                   height) + s("it")))
    await should_wait(cli, "SESSION")
    return ms_admitted


# ---------------------------------------------------------------------------
# ⛔ THE RULER: `BENCH_MARK` -> `BENCH_OUTCOME`, and the return is timed.
#
# §7.5 rule 2: with the bench function OFF the server MUST answer
# `BENCH_OUTCOME(REFUSED, FEATURE_OFF)` — «it must not stay silent and must not
# close».  ⭐ That is what makes this message a usable ruler: the
# answer always arrives, does not change state, and paints nothing on anybody's
# desktop (the function is off, invariant I6).
async def probe(cli, period, halt, samples):
    n = 0
    while not halt.is_set():
        n += 1
        t0 = time.monotonic()
        cli.send_msg(wrap(T["BENCH_MARK"], struct.pack("!III", n, 0x00FF00FF, 0)))
        try:
            _, body = await should_wait(cli, "BENCH_OUTCOME", wait=30)
        except (Drop, asyncio.TimeoutError) as e:
            samples.append({"n": n, "t0": t0, "ms": None, "drop": str(e)})
            return
        t1 = time.monotonic()
        # ⛔ It is checked that the outcome is OF THE MARK SENT: a ruler that
        #    paired an answer with the wrong stopwatch would measure
        #    real numbers of another question.
        echo = struct.unpack("!I", body[:4])[0] if len(body) >= 4 else 0
        samples.append({"n": n, "t0": t0, "ms": (t1 - t0) * 1000,
                         "echo": echo, "combacia": echo == n})
        rest = period - (t1 - t0)
        if rest > 0:
            await asyncio.sleep(rest)


async def timed_handshake(stack, address, port, fpath, report):
    """Connection B: from zero to `HERE_I_AM`, timed."""
    t0 = time.monotonic()
    try:
        cli = await do_open(stack, address, port, fpath)
        await until_here_i_am(cli)
        report["ms"] = (time.monotonic() - t0) * 1000
    except Exception as e:  # noqa: BLE001 — the error type IS the measurement
        report["ms"] = None
        report["drop"] = f"{type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
def unblock(fpath, address):
    """§4.4-bis, the unblock command. ⛔ And it is always DECLARED: «the ban did not
    trigger» and «someone removed it» look the same (rule B0.3).

    ⚠ Here the unblock is never a tool to let a measurement pass: this
      bench does NOT test the ban.  It serves to bring the address to a KNOWN state
      before starting, and not to leave the field dirty for whoever comes next."""
    if not fpath:
        return "no socket declared: I did NOT unblock, and it is not «it was free»"
    try:
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        c.settimeout(5)
        c.connect(fpath)
        c.sendall(f"UNBLOCK {address}\n".encode())
        r = c.recv(256).decode(errors="replace").strip()
        c.close()
        return r or "(empty answer)"
    except OSError as e:
        return f"⛔ I talked to nobody: {e}"


def ping(fpath):
    """⛔ The denominator of the unblock (rule B0.3): without it, «there was no ban»
    and «the unblock never reached anybody» look the same."""
    if not fpath:
        return "—"
    try:
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        c.settimeout(5)
        c.connect(fpath)
        c.sendall(b"PING\n")
        r = c.recv(64).decode(errors="replace").strip()
        c.close()
        return r or "(empty)"
    except OSError as e:
        return f"⛔ {e}"


# ---------------------------------------------------------------------------
async def one_round(a, password, n):
    outcome = {"round": n, "valid": False, "why": None}
    async with AsyncExitStack() as stack:
        # ── A: already inside ─────────────────────────────────────────────
        A = await do_open(stack, a.address, a.port, a.path)
        outcome["ms_admitted_A"] = await until_session(A, a.user, password)

        samples = []
        halt = asyncio.Event()
        ruler = asyncio.create_task(probe(A, a.period, halt, samples))

        # ── the quiet loop: the denominator ───────────────────────────────
        await asyncio.sleep(a.idle)
        base = [c["ms"] for c in samples if c.get("ms") is not None]
        if len(base) < 5:
            halt.set()
            await ruler
            outcome["why"] = (f"only {len(base)} marks on a quiet loop: the "
                               f"ruler measured nothing")
            return outcome
        outcome["base_median_ms"] = statistics.median(base)
        outcome["base_n"] = len(base)
        how_many_before = len(samples)

        # ── C: the wrong credentials, and B at the same instant ───────────
        C = await do_open(stack, a.address, a.port, a.path)
        await until_here_i_am(C)

        b_out = {}
        t_cred = time.monotonic()
        C.send_msg(wrap(T["CREDENTIALS"], s(a.bad_user) + s(a.bad_password)))
        second = asyncio.create_task(
            timed_handshake(stack, a.address, a.port, a.path, b_out))

        try:
            name_C, body = await should_wait(C, None, wait=40)
            t_resp = time.monotonic()
        except (Drop, asyncio.TimeoutError) as e:
            halt.set()
            await ruler
            await second
            outcome["why"] = f"C received no answer: {e}"
            return outcome
        await second

        reason = body[0] if body else 0
        outcome["response_C"] = name_C
        outcome["reason_C"] = reason
        outcome["reason_C_name"] = REASONS.get(reason, "?")
        outcome["ms_C"] = (t_resp - t_cred) * 1000

        # ── the tail: probing goes on after the window ────────────────────
        await asyncio.sleep(a.tail)
        halt.set()
        await ruler

        # ⛔ THE DIRTY SAMPLE IS THROWN AWAY, AND THE REASON IS SAID.
        if name_C != "REJECTED":
            outcome["why"] = (
                f"to wrong CREDENTIALS the server answered «{name_C}», not "
                f"REJECTED: the scene is not the declared one")
            return outcome
        if reason != 0x07:
            outcome["why"] = (
                f"the REJECTED carries {reason:#04x} = {REASONS.get(reason, '?')}, "
                f"not 0x07 WRONG_CREDENTIALS: ⛔ with {REASONS.get(reason, '?')} "
                f"the server refuses WITHOUT querying PAM (§4.4-bis), that is the "
                f"slow thing did not happen and there was nothing to block")
            return outcome

        # ── the count ─────────────────────────────────────────────────────
        # The window: the marks SENT between the `CREDENTIALS` and the `REJECTED`.
        inside = [c for c in samples[how_many_before:]
                  if c.get("ms") is not None and t_cred <= c["t0"] <= t_resp]
        # ⚠ And also the mark sent BEFORE and returned AFTER: it is precisely the one
        #   the blocking eats, and excluding it would mean measuring everything
        #   except the fact (`LESSONS.md` §1.9).
        a_straddle = [c for c in samples
                     if c.get("ms") is not None and c["t0"] < t_cred
                     and c["t0"] + c["ms"] / 1000 > t_cred]
        window = a_straddle + inside
        if not window:
            outcome["why"] = ("no mark was sent inside the window: the "
                               "window lasted "
                               f"{outcome['ms_C']:.0f} ms and the period is "
                               f"{a.period * 1000:.0f} ms")
            return outcome

        peak = max(c["ms"] for c in window)
        stopped = sum(max(0.0, c["ms"] - outcome["base_median_ms"]) for c in window)
        outcome.update({
            "valid": True,
            "n_window": len(window),
            "peak_ms": peak,
            "stalled_ms": stopped,
            "ms_tight_B": b_out.get("ms"),
            "drop_B": b_out.get("drop"),
            "scrambled_marks": sum(1 for c in samples
                                     if c.get("combacia") is False),
        })
        return outcome


# ---------------------------------------------------------------------------
# ⭐ D4b (25 Oct 2026): THE TWO SCENES WITHOUT A SYNCHRONOUS FALLBACK.

async def login_attempt(a, user, password):
    """One connection: HELLO -> HERE_I_AM (timed), CREDENTIALS, the first answer.  Never raises: a failure is IN the result."""
    r = {"user": user}
    async with AsyncExitStack() as stack:
        try:
            cli = await do_open(stack, a.address, a.port, a.path)
            t0 = time.monotonic()
            await until_here_i_am(cli)
            r["ms_hi"] = (time.monotonic() - t0) * 1000
            t1 = time.monotonic()
            cli.send_msg(wrap(T["CREDENTIALS"], s(user) + s(password)))
            name, body = await should_wait(cli, None, wait=40)
            r["answer"] = name
            r["reason"] = body[0] if body else None
            r["ms_answer"] = (time.monotonic() - t1) * 1000
        except Exception as e:  # noqa: BLE001 — the error type IS the measurement
            r["drop"] = f"{type(e).__name__}: {e}"
    return r


async def handshake_ruler(a, period, halt, samples):
    """A ruler that needs NO session: connects and times HELLO -> HERE_I_AM, again and again."""
    while not halt.is_set():
        t0 = time.monotonic()
        rep = {}
        async with AsyncExitStack() as stack:
            await timed_handshake(stack, a.address, a.port, a.path, rep)
        samples.append(rep)
        rest = period - (time.monotonic() - t0)
        if rest > 0:
            await asyncio.sleep(rest)


def _ruler_ok(samples):
    """(ok, text): every handshake answered and none slower than TIGHT_FREE_MS."""
    ms = [x["ms"] for x in samples if x.get("ms") is not None]
    bad = [x for x in samples if x.get("ms") is None]
    if not ms:
        return None, "no handshake measured"
    peak = max(ms)
    return (not bad and peak < TIGHT_FREE_MS), (f"{len(ms)} handshakes, peak {peak:.0f} ms (limit {TIGHT_FREE_MS:.0f}), "
                                                f"{len(bad)} dropped")


async def scene_unchecked(a, password):
    """FAULT «no helper»: 20 refusals in a row, all 0x0E, nothing counted, the wire never stuck."""
    print(f"   scene «unchecked»: {a.attempts} attempts in a row from one address (the first with the RIGHT password)")
    results = []
    for i in range(a.attempts):
        user, pw = (a.user, password) if i == 0 else (a.bad_user, a.bad_password)
        b = {}

        async def later(b=b):
            await asyncio.sleep(0.3)   # inside the fixed second of the attempt
            async with AsyncExitStack() as st2:
                await timed_handshake(st2, a.address, a.port, a.path, b)

        tb = asyncio.create_task(later())
        r = await login_attempt(a, user, pw)
        await tb
        r["ms_B"] = b.get("ms")
        results.append(r)
        print(f"     {i + 1:2d}. {user:8s} -> {r.get('answer', '—')} "
              f"{REASONS.get(r.get('reason'), r.get('reason'))}"
              f"{'  DROP ' + r['drop'] if 'drop' in r else ''}   handshake B "
              f"{'%.0f ms' % r['ms_B'] if r.get('ms_B') is not None else 'DROPPED'}")
    n_0e = sum(1 for r in results if r.get("answer") == "REJECTED" and r.get("reason") == 0x0E)
    n_07 = sum(1 for r in results if r.get("reason") == 0x07)
    n_08 = sum(1 for r in results if r.get("reason") == 0x08)
    n_drop = sum(1 for r in results if "drop" in r)
    ms_b = [r["ms_B"] for r in results if r.get("ms_B") is not None]
    b_ok = len(ms_b) == len(results) and max(ms_b) < TIGHT_FREE_MS
    ok = (n_0e == len(results) and n_07 == 0 and n_08 == 0 and n_drop == 0 and b_ok)
    print(f"\n   0x0E {n_0e}/{len(results)} · 0x07 {n_07} · 0x08 {n_08} · dropped {n_drop} · "
          f"B peak {max(ms_b) if ms_b else float('nan'):.0f} ms (limit {TIGHT_FREE_MS:.0f})")
    print(f"   {'⭐ OK' if ok else '⛔ NO'}  expected «unchecked»: every answer REJECTED 0x0E (nothing counted, no ban), the wire never stuck")
    if n_07:
        print("      ⛔ a 0x07 means PAM was ASKED and said no: this target HAS a helper — it is not the faulty copy")
    if n_08:
        print("      ⛔ a 0x08 means the refusals were COUNTED and the address was banned")
    write(a, [{"scene": "unchecked", "results": results}], {"ok": ok, "n_0e": n_0e, "n_07": n_07, "n_08": n_08})
    return 0 if ok else 1


async def scene_restart(a, password):
    """REPAIRED: kill the helper, see 0x0E, see the logins work again after the restart, the wire never stuck."""
    if not a.log:
        print("   ⛔ --log (the target's log) is needed: «restarted» is read there, not guessed")
        return 2
    kill_cmd = a.kill_cmd or f"bash {os.path.join(os.path.dirname(os.path.abspath(__file__)), '02-pam-start.sh')} kill-helper"
    log_before = open(a.log, errors="replace").read().count("RESTART") if os.path.exists(a.log) else 0
    samples = []
    halt = asyncio.Event()
    ruler = asyncio.create_task(handshake_ruler(a, 0.2, halt, samples))
    await asyncio.sleep(1.0)       # the ruler's denominator on a quiet, healthy loop
    healthy = await login_attempt(a, a.user, password)
    print(f"   healthy first: {healthy.get('answer', '—')} "
          f"{REASONS.get(healthy.get('reason'), healthy.get('reason'))}  (must be ADMITTED)")
    t_kill = time.monotonic()
    k = await asyncio.to_thread(subprocess.run, kill_cmd, shell=True, capture_output=True, text=True)
    print(f"   kill-helper rc={k.returncode}: {(k.stdout or '').strip().splitlines()[-1:] or k.stderr.strip()[-200:]}")
    if k.returncode != 0:
        halt.set()
        await ruler
        print("   ⛔ NOT MEASURED: the helper was not killed (it is not «it recovered», it is «I did not break it»)")
        return 3
    await asyncio.sleep(0.3)       # the server has seen the EOF (one round of its loop), the pause of 1 s is running
    down = await login_attempt(a, a.bad_user, a.bad_password)
    print(f"   while the helper is down: {down.get('answer', '—')} {REASONS.get(down.get('reason'), down.get('reason'))}"
          f"  (must be REJECTED 0x0E, not counted)")
    t_back = None
    polls = 0
    last = None
    while time.monotonic() - t_kill < a.restart_wait:
        polls += 1
        last = await login_attempt(a, a.user, password)
        if last.get("answer") == "ADMITTED":
            t_back = time.monotonic()
            break
        if not (last.get("answer") == "REJECTED" and last.get("reason") == 0x0E):
            break                  # something else than «still down»: stop and say it
        await asyncio.sleep(0.5)
    halt.set()
    await ruler
    ruler_ok, ruler_text = _ruler_ok(samples)
    text = open(a.log, errors="replace").read() if os.path.exists(a.log) else ""
    restarts = text.count("RESTART") - log_before
    healthy_ok = healthy.get("answer") == "ADMITTED"
    down_ok = down.get("answer") == "REJECTED" and down.get("reason") == 0x0E
    back_ok = t_back is not None
    log_ok = restarts >= 1
    print(f"\n   back after {('%.1f s' % (t_back - t_kill)) if back_ok else 'NEVER'} ({polls} polls) · "
          f"RESTART lines in the log: {restarts} · wire: {ruler_text}")
    checks = [("healthy before: ADMITTED", healthy_ok), ("down: REJECTED 0x0E", down_ok),
              (f"ADMITTED again within {a.restart_wait:.0f} s", back_ok), ("the log says RESTART", log_ok),
              ("the wire never stuck", bool(ruler_ok))]
    for name, ok in checks:
        print(f"   {'⭐ OK' if ok else '⛔ NO'}  {name}")
    ok = all(ok for _, ok in checks)
    write(a, [{"scene": "restart", "healthy": healthy, "down": down, "last": last,
               "back_s": (t_back - t_kill) if back_ok else None, "restarts": restarts}], {"ok": ok})
    return 0 if ok else 1


def prediction():
    print("""
== ⛔ THE EXPECTATION, WRITTEN BEFORE THE ROUND  (02-pam-standstill.py, 25 Oct 2026)

   The synchronous PAM fallback is GONE (D4b): there is no longer a «blocked» server to see.
   What is checked is that the others NEVER stand still, in three scenes (--wait):

   | scene     | target                  | what happens                                         | expectation |
   |-----------|-------------------------|------------------------------------------------------|-------------|
   | free      | healthy                 | a third party with WRONG credentials                 | A's peak < %.0f ms, B < %.0f ms, C = REJECTED 0x07 |
   | unchecked | built with `fault`      | %s attempts in a row, the first with the RIGHT password | every answer 0x0E; never 0x07, never 0x08; B < %.0f ms |
   | restart   | healthy + kill-helper   | helper killed, then logins                           | down: 0x0E · ADMITTED again within the restart wait · log says RESTART · wire < %.0f ms |

   ⛔ THE BLIND-RULER CASE: `unchecked` run on a HEALTHY target gives 0x07, not 0x0E, and goes red; `restart` with a
      helper that is never started again goes red on «ADMITTED again».  Both MUST be seen red once.

   ⛔ And if the quiet loop (the base median of `free`) were above %.0f ms, the ruler is broken and the round is
      declared invalid.
""" % (FREE_PEAK_MS, TIGHT_FREE_MS, "20", TIGHT_FREE_MS, TIGHT_FREE_MS, BASE_MAX_MS))


async def main(a, password):
    print(f"== 02-pam-standstill — https://{a.address}:{a.port}{a.path}"
          f"  ·  {a.rounds} rounds  ·  expectation «{a.wait}»")
    print(f"   PING to the command socket: {ping(a.socket)}")
    print(f"   ⚠ unblock DECLARED, before starting: "
          f"{unblock(a.socket, a.address)}")
    print(f"   ⚠ and for the other address this machine sees itself with: "
          f"{unblock(a.socket, '127.0.0.1')}")

    if a.wait == "unchecked":
        return await scene_unchecked(a, password)
    if a.wait == "restart":
        return await scene_restart(a, password)

    outcomes = []
    for n in range(1, a.rounds + 1):
        try:
            e = await one_round(a, password, n)
        except Exception as ex:  # noqa: BLE001
            e = {"round": n, "valid": False,
                 "why": f"{type(ex).__name__}: {ex}"}
        e["when"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        e["wait"] = a.wait
        e["port"] = a.port
        outcomes.append(e)
        if e["valid"]:
            b = e["ms_tight_B"]
            how_much_b = (f"{b:.0f} ms" if b is not None
                        else f"DROPPED ({e.get('drop_B')})")
            print(f"   round {n}: base {e['base_median_ms']:.1f} ms · "
                  f"⛔ peak {e['peak_ms']:.0f} ms · stalled {e['stalled_ms']:.0f} ms · "
                  f"handshake B {how_much_b}")
            print(f"            and whoever was authenticating (C): {e['ms_C']:.0f} ms "
                  f"[{e['reason_C_name']}]  ·  A had got in in "
                  f"{e['ms_admitted_A']:.0f} ms")
        else:
            print(f"   round {n}: ⛔ NOT VALID — {e['why']}")
        # ⛔ Between one round and the next it is given room to breathe: A detaches and the slot
        #    (§8.2 reason 0x0F, invariant I2) must be free for the next round.
        await asyncio.sleep(1.0)

    good_n = [e for e in outcomes if e["valid"]]
    print(f"\n== the count: {len(good_n)} valid rounds out of {len(outcomes)}")
    if not good_n:
        print("   ⛔ NOTHING TO CONCLUDE: no valid round.  ⚠ It is not «zero "
              "milliseconds»: it is «I did not measure» (`LESSONS.md` §1.9).")
        write(a, outcomes, None)
        return 3

    peaks = sorted(e["peak_ms"] for e in good_n)
    stills = sorted(e["stalled_ms"] for e in good_n)
    tight = sorted(e["ms_tight_B"] for e in good_n
                     if e["ms_tight_B"] is not None)
    cc = sorted(e["ms_C"] for e in good_n)
    bases = sorted(e["base_median_ms"] for e in good_n)
    summary = {
        "valid_rounds": len(good_n), "rounds": len(outcomes),
        "base_median_ms": statistics.median(bases),
        "peak_median_ms": statistics.median(peaks),
        "peak_max_ms": peaks[-1],
        "stopped_median_ms": statistics.median(stills),
        "tight_B_median_ms": statistics.median(tight) if tight else None,
        "C_median_ms": statistics.median(cc),
        "wait": a.wait,
    }
    print(f"   quiet loop (base)            median  {summary['base_median_ms']:8.1f} ms")
    print(f"   ⛔ peak of the mark          median  {summary['peak_median_ms']:8.1f} ms"
          f"   (maximum {summary['peak_max_ms']:.0f})")
    print(f"   ⛔ A's stalled time          median  {summary['stopped_median_ms']:8.1f} ms")
    if tight:
        print(f"   ⛔ B's handshake             median  {summary['tight_B_median_ms']:8.1f} ms")
    print(f"   ⚠ who was authenticating (C) median  {summary['C_median_ms']:8.1f} ms"
          f"   ← ⭐ this must NOT change")

    # ── the verdict, against the expectation written beforehand ───────────
    verdict = 0
    if summary["base_median_ms"] > BASE_MAX_MS:
        print(f"\n   ⛔ THE RULER IS BROKEN: the quiet loop measures "
              f"{summary['base_median_ms']:.0f} ms, above the {BASE_MAX_MS:.0f} "
              f"expected.  No comparison is readable.")
        verdict = 3
    elif a.wait == "free":
        ok = (summary["peak_median_ms"] < FREE_PEAK_MS)
        ok_b = bool(tight) and summary["tight_B_median_ms"] < TIGHT_FREE_MS
        print(f"\n   {'⭐ OK' if ok else '⛔ NO'}  expected «libero»: the peak "
              f"had to be < {FREE_PEAK_MS:.0f} ms and it is "
              f"{summary['peak_median_ms']:.0f}")
        if tight:
            print(f"   {'⭐ OK' if ok_b else '⛔ NO'}  and B's handshake < "
                  f"{TIGHT_FREE_MS:.0f} ms: it is "
                  f"{summary['tight_B_median_ms']:.0f}")
        else:
            print("   ⛔ NO  no handshake of B measured: it is not «it was "
                  "fast», it is «I did not measure»")
        verdict = 0 if (ok and ok_b) else 1
    else:
        print("\n   ⚠ no expectation declared (--wait): the round measures and does not "
              "judge")

    write(a, outcomes, summary)
    return verdict


def write(a, outcomes, summary):
    if not a.outcomes:
        return
    line = {"when": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "machine": os.uname().nodename,
            "scene": {"port": a.port, "address": a.address,
                      "user": a.user, "bad_user": a.bad_user,
                      "period_ms": a.period * 1000,
                      "quiet_s": a.idle, "queue_s": a.tail},
            "wait": a.wait, "rounds": outcomes, "summary": summary,
            "note": a.note}
    with open(a.outcomes, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
    print(f"   outcomes: {a.outcomes}")


def password_from_file(fpath):
    """⛔ D12: the password does not go through the command line —
    anyone can read `/proc/<pid>/cmdline`."""
    try:
        mode = os.stat(fpath).st_mode & 0o077
    except OSError as e:
        print(f"   ⛔ the password file «{fpath}» cannot be read: {e}")
        sys.exit(2)
    if mode:
        print(f"   ⚠ «{fpath}» is readable by others (bits {mode:o})")
    with open(fpath, encoding="utf-8") as f:
        password = f.read().strip("\n")
    if not password:
        print(f"   ⛔ «{fpath}» is EMPTY: it is not «the password is empty», it is "
              f"«the launcher did not write it»")
        sys.exit(2)
    return password


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="how long whoever is NOT authenticating stands still")
    p.add_argument("--address", default="192.168.0.2")
    p.add_argument("--port", type=int, default=7531)
    p.add_argument("--path", default="/rcp/1")
    p.add_argument("--user", default="prova")
    p.add_argument("--password-file", default="")
    p.add_argument("--bad-user", default="prova2")
    p.add_argument("--bad-password", default="questa-non-e-la-parola-giusta")
    p.add_argument("--socket", default="")
    p.add_argument("--rounds", type=int, default=5)
    p.add_argument("--period", type=float, default=0.05,
                   help="how often a mark is sent, in seconds")
    p.add_argument("--idle", type=float, default=1.2,
                   help="how long probing goes on with the loop idle, for the denominator")
    p.add_argument("--tail", type=float, default=0.7)
    p.add_argument("--wait", choices=["free", "unchecked", "restart", "none"],
                   default="none",
                   help="the scene and its expectation, DECLARED BEFORE the round (see the head of the file)")
    p.add_argument("--attempts", type=int, default=20, help="scene unchecked: how many attempts in a row")
    p.add_argument("--log", default="", help="scene restart: the target's log (02-pam-start.sh writes it)")
    p.add_argument("--kill-cmd", default="", help="scene restart: how to kill the helper (default: 02-pam-start.sh kill-helper)")
    p.add_argument("--restart-wait", type=float, default=30.0, help="scene restart: seconds to wait for the logins to work again")
    p.add_argument("--outcomes", default="")
    p.add_argument("--note", default="")
    p.add_argument("--prediction", action="store_true")
    a = p.parse_args()
    if a.prediction:
        prediction()
        sys.exit(0)
    if AIOQUIC:
        print(f"   ⛔ «aioquic» is not on this machine ({AIOQUIC}): this "
              f"bench runs INSIDE the NIC-OS container.\n"
              f"      ⚠ It is not «the round went fine»: it is «I did not measure».")
        sys.exit(2)
    if not a.password_file:
        print("   ⛔ --password-file is needed (D12: the password does not go through argv)")
        sys.exit(2)
    password = password_from_file(a.password_file)
    try:
        sys.exit(asyncio.run(main(a, password)))
    except Exception as e:  # noqa: BLE001 — the error type IS the measurement
        print(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
