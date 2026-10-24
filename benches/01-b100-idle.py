#!/usr/bin/env python3
"""01-b100-idle.py — B100: the user clocks of SPECS §5.3 count ONLY the five user gestures of RCP.md §7.3
(DECISIONS §11.43, option A; commits 496b6dbd / 24f99518: rcp.c `last_input`, main.c `presence_mark`).

    python3 01-b100-idle.py --address 127.0.0.1 --port 7451 --user-prefix rxidle --password-file pw \\
        --inactivity-s 20 --abandon-s 40 --cases a,b,c --server-log /idle/server.log --output b100.jsonl

⭐ The server under test runs with SHORT clocks (--inactivity-s / --abandon-s), the same numbers are
   given to this bench, and every check is judged against them.  Each case logs in as its OWN user
   (<prefix><case>: one desktop per user, I2), from its own 127.0.0.x source, and all the cases of a
   run go in PARALLEL — each one is read in the server log by its own user name.

The cases (each one a line {"type": "check", ...} in the JSONL, plus {"type": "event"} lines):

  a   «the page talks, the user does not»: after SESSION the client sends ONLY what the page sends on
      its own — REQUEST_KEY, PACE (when video.pace is negotiated) and CLIPBOARD_ANNOUNCE — every
      --chatter-s (2 s).  ⚠ PACE needs video.pace on both sides: the launcher starts the server
      with --decoder-pace, and without it PACE is left out (it would be a PROTOCOL_ERROR).
      Expected: FAREWELL 0x02 INACTIVITY at --inactivity-s from the connection's
      birth (rcp_open: the clock starts there), and the server's «§5.3 — ABANDONMENT» line for that
      user at --abandon-s from its child's birth (main.c presence_mark at the spawn).
  b   «the user touches»: a POINTER move or a LETTER every --gesture-s (5 s), nothing else, for
      --hold-s (65 s).  Expected: no FAREWELL, the connection alive at the end, and neither an
      INACTIVITY nor an ABANDONMENT line for that user.
  c   «the line drops»: one POINTER, then the line goes DARK in both directions (every datagram in
      or out is dropped, QUIC included) for --drop-s (25 s, past the inactivity ceiling); then the
      line comes back and the client sends what a page sends first after a hole, a REQUEST_KEY, and
      watches --after-s (6 s).  Then a NEW connection tries ATTACH right after HERE_I_AM, with no
      CREDENTIALS (expected: refused), then a full login with the password (expected: ADMITTED
      and SESSION).  §11.43 A: «the password is always needed».  ⚠ [M] 15 Oct 2026: with the line
      dark it is the DEAD LINE (webtransport.c, 10 s without a client packet) that closes the QUIC
      connection first, before the inactivity ceiling — the old connection is gone and only a new
      login gets back in.  Last, that new login only watches (QUIC pings): the desktop is closed
      (0x03) at --abandon-s from the last gesture BEFORE the drop — a login is not a gesture.
  f   «the tab is frozen»: one POINTER, then the QUIC connection stays alive (our PINGs every 4 s)
      but NO RCP byte leaves, as a browser that froze the page's JS.  Meant for a server with
      --inactivity-s LONGER than rcp.c's SILENCE (30 s), e.g. 40, the product's order of the two.
      Expected, and [M] 15 Oct 2026: NO «DETACHED for silence» — every QUIC packet is a sign of
      life (webtransport.c → rcp_sign_of_life()), so the frozen tab stays ATTACHED — and FAREWELL
      0x02 at the ceiling counted from the POINTER.  ⚠ So the reconnection road DECISIONS §11.43
      describes (speak_again() after a detach for silence) is not reached with the live client
      either way: a frozen tab is never detached for silence (its stack ACKs), and a dark line
      loses the connection (dead line 10 s, QUIC idle 30 s) — back means a NEW login (case c).

Exit: 0 every check passed · 1 a check failed · 2 blind (no login reached SESSION).
"""
import argparse
import asyncio
import datetime
import importlib.util
import json
import os
import re
import socket
import ssl
import struct
import sys
import time

from aioquic.h3.connection import H3_ALPN
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection
from aioquic.quic.events import ConnectionTerminated

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("b3cliente", os.path.join(HERE, "01-b3-client.py"))
b3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b3)
b3.print = lambda *a, **k: None

T_FAREWELL = 0x000C
T_SESSION = 0x0007
T_REQUEST_KEY = 0x000D
T_PACE = 0x0012
T_LETTER = 0x0104
REASONS = {0x02: "INACTIVITY", 0x03: "SESSION_ABANDONED", 0x0B: "PROTOCOL_ERROR", 0x10: "SESSION_TERMINATED"}
SILENCE_S = 30.0          # rcp.c SILENCE (30000 ms) — the detach for silence
RESULTS = []


def now():
    return time.monotonic()


def wall():
    return time.time()


def out(rec):
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    if ARGS.output:
        with open(ARGS.output, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def check(case, name, ok, why="", **extra):
    rec = {"type": "check", "case": case, "name": name, "ok": bool(ok), "why": why}
    rec.update(extra)
    out(rec)
    RESULTS.append(rec)
    return ok


# ---------------------------------------------------------------------------------------------
# the server log: «HH:MM:SS.mmm category text»; the containers share the host clock and the image
# (so the time zone), and every interval below is server time minus server time when it can be.
# ---------------------------------------------------------------------------------------------
LINE = re.compile(r"^(\d\d):(\d\d):(\d\d)\.(\d{3}) (.*)$")


def log_lines():
    if not ARGS.server_log:
        return []
    try:
        with open(ARGS.server_log, "rb") as f:
            text = f.read().decode("utf-8", "replace")
    except OSError:
        return []
    res = []
    for ln in text.splitlines():
        m = LINE.match(ln)
        if m:
            h, mi, s, ms, rest = m.groups()
            res.append((int(h) * 3600 + int(mi) * 60 + int(s) + int(ms) / 1000.0, rest))
    return res


def tod(epoch):
    """Seconds of the day of a wall-clock instant, in the local zone (the server's)."""
    d = datetime.datetime.fromtimestamp(epoch)
    return d.hour * 3600 + d.minute * 60 + d.second + d.microsecond / 1e6


def first(lines, pred, after=None):
    for t, txt in lines:
        if (after is None or t >= after - 0.002) and pred(txt):
            return t, txt
    return None, None


def mine(user):
    """A line about this user: «[user]» from rcp/wt/child, or «user» in quotes."""
    a, b = "[%s]" % user, "«%s»" % user
    return lambda txt: a in txt or b in txt


# ---------------------------------------------------------------------------------------------
# one connection, from a chosen source, with a switch that makes the line DARK
# ---------------------------------------------------------------------------------------------
class DarkTransport:
    """The datagram transport, with a switch: while `dark`, every outgoing datagram is dropped."""

    def __init__(self, inner):
        self.inner = inner
        self.dark = False
        self.dropped = 0

    def sendto(self, data, addr=None):
        if self.dark:
            self.dropped += 1
            return
        self.inner.sendto(data, addr)

    def __getattr__(self, k):
        return getattr(self.inner, k)


class Cli(b3.Client):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.born = now()
        self.handshake_done = False
        self.term_code = None
        self.term_reason = ""
        self.term_at = None
        self.dark_in = 0
        self.dark = False

    def datagram_received(self, data, addr):
        if self.dark:
            self.dark_in += 1
            return
        super().datagram_received(data, addr)

    def quic_event_received(self, event):
        if type(event).__name__ == "HandshakeCompleted":
            self.handshake_done = True
        if isinstance(event, ConnectionTerminated):
            if self.term_at is None:
                self.term_code = event.error_code
                self.term_reason = event.reason_phrase or ""
                self.term_at = now()
            self._cade("connection TERMINATED (%s)" % (event.reason_phrase or "no reason"))
            self.messages.put_nowait(None)
            return
        super().quic_event_received(event)


class Conn:
    def __init__(self, case, src):
        self.case, self.src = case, src
        self.cli = None
        self.tr = None
        self.pinger = None
        self.reader = None
        self.got = []            # [(monotonic, name, body)]
        self.farewell = None     # (monotonic, reason)
        self.closed_at = None
        self.session_at = None
        self.pace_ok = False
        self.inp = 0

    async def open(self, timeout=8.0):
        loop = asyncio.get_running_loop()
        conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN, max_datagram_frame_size=65536,
                                 idle_timeout=120.0)
        conf.verify_mode = ssl.CERT_NONE
        conf.server_name = ARGS.address
        quic = QuicConnection(configuration=conf)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.src, 0))
        transport, self.cli = await loop.create_datagram_endpoint(lambda: Cli(quic), sock=sock)
        self.tr = DarkTransport(transport)
        self.cli._transport = self.tr
        self.cli.connect((ARGS.address, ARGS.port), transmit=True)
        try:
            await asyncio.wait_for(self.cli.wait_connected(), timeout)
        except Exception:  # noqa: BLE001
            pass
        if not self.cli.handshake_done:
            return False
        self.cli.open_session("%s:%d" % (ARGS.address, ARGS.port), "/rcp/1")
        st = await asyncio.wait_for(self.cli.accepted, timeout)
        if st != "200":
            return False
        self.cli.open_control()
        self.cli.transmit()
        self.wt_at = now()
        self.wt_wall = wall()
        self.reader = asyncio.ensure_future(self._read())
        return True

    async def _read(self):
        while True:
            m = await self.cli.messages.get()
            if m is None:
                if self.closed_at is None:
                    self.closed_at = now()
                self.got.append((now(), "CLOSED", self.cli.drop))
                return
            kind, body, raw = m
            name = b3.NAME.get(kind, "%#06x" % kind)
            self.got.append((now(), name, body))
            if kind == T_FAREWELL and self.farewell is None:
                self.farewell = (now(), body[0] if body else None)
                out({"type": "event", "case": self.case, "what": "FAREWELL", "reason": self.farewell[1],
                     "reason_name": REASONS.get(self.farewell[1], "?"),
                     "s_since_connect": round(self.farewell[0] - self.wt_at, 2)})
            if kind == T_SESSION and self.session_at is None:
                self.session_at = now()

    async def wait_for(self, name, timeout):
        """The first message `name` from index 0 on; a FAREWELL/CLOSED first is an exception."""
        end = now() + timeout
        i = 0
        while now() < end:
            while i < len(self.got):
                _, n, body = self.got[i]
                i += 1
                if n == name:
                    return body
                if n in ("FAREWELL", "CLOSED", "REJECTED"):
                    raise RuntimeError("%s instead of %s (%s)" % (
                        n, name, body.hex() if isinstance(body, bytes) else body))
            await asyncio.sleep(0.05)
        raise asyncio.TimeoutError("no %s within %.0f s" % (name, timeout))

    def send(self, kind, body):
        self.cli.send_msg(b3.wrap(kind, body))

    def hello(self):
        entries = [("video.codec", "hevc,av1,h264"), ("video.depth", "8,10"), ("audio.codec", "opus,pcm"),
                   ("clipboard.text", "yes"), ("video.pace", "yes"), ("client.name", "bench-b100 0.1.0")]
        body = struct.pack("!HH", 1, len(entries))
        for n, v in entries:
            body += b3.s(n) + b3.s(v)
        self.send(0x0001, body)

    async def login(self, user, password, attach=True):
        """HELLO → HERE_I_AM → CREDENTIALS → ADMITTED (→ ATTACH → SESSION).  Returns a text or raises."""
        self.hello()
        hi = await self.wait_for("HERE_I_AM", 10)
        self.pace_ok = b"video.pace" in hi and b"yes" in hi.split(b"video.pace", 1)[1][:8]
        self.send(0x0003, b3.s(user) + b3.s(password))
        await self.wait_for("ADMITTED", 25)
        self.admitted_at, self.admitted_wall = now(), wall()
        if not attach:
            return "ADMITTED"
        self.send(0x0006, struct.pack("!IIII", 1920, 1080, 1920, 1080) + b3.s("it"))
        await self.wait_for("SESSION", 20)
        return "SESSION"

    # what the PAGE sends on its own (never a gesture)
    def request_key(self):
        self.send(T_REQUEST_KEY, struct.pack("!I", 0))

    def pace(self, fps=30):
        if self.pace_ok:
            self.send(T_PACE, struct.pack("!H", fps))

    def announce(self, text):
        self.cli.clipboard_announce(text)

    # the user's gestures (§7.3)
    def pointer(self, x, y):
        self.cli.send_pointer(x, y)
        self.last_gesture = now()

    def letter(self, ch):
        sid = self.cli.open_input()
        self.cli.inp_id += 1
        b = b3.wrap(T_LETTER, struct.pack("!IQI", self.cli.inp_id, int(now() * 1e6), ord(ch)))
        self.cli._quic.send_stream_data(sid, b, end_stream=False)
        self.cli.transmit()
        self.last_gesture = now()

    def keep_alive(self, every=4.0):
        async def ping():
            uid = 1
            while self.alive():
                await asyncio.sleep(every)
                if self.tr.dark:
                    continue
                try:
                    self.cli._quic.send_ping(uid)
                    self.cli.transmit()
                except Exception:  # noqa: BLE001
                    return
                uid += 1
        self.pinger = asyncio.ensure_future(ping())

    def go_dark(self, on):
        self.tr.dark = on
        self.cli.dark = on
        if not on:
            self.cli.transmit()

    def alive(self):
        return self.cli is not None and self.cli.term_at is None and self.closed_at is None

    async def close(self):
        if self.pinger:
            self.pinger.cancel()
        if self.cli is not None and self.cli.term_at is None:
            self.cli.closed_by_us = True
            try:
                self.cli.close()
                await asyncio.wait_for(self.cli.wait_closed(), 2)
            except Exception:  # noqa: BLE001
                pass
        if self.reader:
            self.reader.cancel()
        if self.tr is not None:
            self.tr.inner.close()


def user_of(case):
    return ARGS.user_prefix + case


async def logged_in(case, src):
    c = Conn(case, src)
    try:
        if not await c.open():
            out({"type": "event", "case": case, "what": "no connection",
                 "code": c.cli.term_code if c.cli else None})
            return None
        text = await c.login(user_of(case), ARGS.password)
    except Exception as e:  # noqa: BLE001
        out({"type": "event", "case": case, "what": "login failed", "error": "%s: %s" % (type(e).__name__, e)})
        await c.close()
        return None
    out({"type": "event", "case": case, "what": text, "user": user_of(case), "pace": c.pace_ok,
         "s_connect_to_session": round(c.session_at - c.wt_at, 2)})
    c.keep_alive()
    return c


def server_reading(case, c, lines):
    """What the server log says about this case's user: the instants of the lines that matter,
    relative to the server's own ADMITTED verdict for that user (child born just before it)."""
    u = user_of(case)
    is_u = mine(u)
    t_adm, _ = first(lines, lambda x: "verdict for «%s»: ⭐ ADMITTED" % u in x)
    t_spawn, _ = first(lines, lambda x: "child spawned for «%s»" % u in x)
    t_ina, l_ina = first(lines, lambda x: is_u(x) and "§5.3 — INACTIVITY" in x)
    t_aba, l_aba = first(lines, lambda x: "ABANDONMENT: «%s»" % u in x)
    t_sil, l_sil = first(lines, lambda x: is_u(x) and "DETACHED for silence" in x)
    t_dead, l_dead = first(lines, lambda x: is_u(x) and "dead-line" in x)
    t_again, l_again = first(lines, lambda x: is_u(x) and ("speaks again" in x.lower() or "slot taken back" in x
                                                           or "TAKEN BACK" in x or "taken back" in x),
                             after=t_sil)
    ms = lambda txt, pat: int(re.search(pat, txt).group(1)) if txt and re.search(pat, txt) else None  # noqa: E731
    rel = lambda t: None if (t is None or t_adm is None) else round(t - t_adm, 2)  # noqa: E731
    after = []
    if t_aba is not None:
        after = [txt[:240] for t, txt in lines if t_aba <= t <= t_aba + 8 and is_u(txt)][:12]
    return {
        "user": u,
        "admitted_tod": t_adm, "spawn_tod": t_spawn,
        "inactivity_s_after_admitted": rel(t_ina),
        "inactivity_server_ms": ms(l_ina, r"INACTIVITY: (\d+) ms without user input"),
        "abandon_s_after_admitted": rel(t_aba),
        "abandon_s_after_spawn": None if (t_aba is None or t_spawn is None) else round(t_aba - t_spawn, 2),
        "abandon_server_ms": ms(l_aba, r"has touched nothing for (\d+) ms"),
        "silence_detach_s_after_admitted": rel(t_sil),
        "silence_line": (l_sil or "")[:240] or None,
        "dead_line_s_after_admitted": rel(t_dead),
        "dead_line": (l_dead or "")[:300] or None,
        "taken_back_line": (l_again or "")[:240] or None,
        "taken_back_s_after_admitted": rel(t_again),
        "after_abandonment": after,
    }


# ---------------------------------------------------------------------------------------------
# the cases
# ---------------------------------------------------------------------------------------------
async def case_a(src):
    c = await logged_in("a", src)
    if c is None:
        return "blind"
    n = 0
    end = c.wt_at + ARGS.inactivity_s + 15
    while c.alive() and c.farewell is None and now() < end:
        n += 1
        c.request_key()
        c.pace(30 if n % 2 else 45)
        c.announce("b100 chatter %d" % n)
        await asyncio.sleep(ARGS.chatter_s)
    sent = n
    # stay until the abandonment ceiling has passed, then read the log
    await asyncio.sleep(max(0.0, c.admitted_at + ARGS.abandon_s + 6 - now()))
    lines = log_lines()
    srv = server_reading("a", c, lines)
    out({"type": "server", "case": "a", **srv})
    fw = c.farewell
    t_fw = None if fw is None else round(fw[0] - c.wt_at, 2)
    lo, hi = ARGS.inactivity_s - 0.5, ARGS.inactivity_s + 3.0
    check("a", "page messages only (REQUEST_KEY%s, CLIPBOARD_ANNOUNCE every %.0f s): FAREWELL 0x02 at the "
          "%.0f s inactivity ceiling" % (", PACE" if c.pace_ok else "", ARGS.chatter_s, ARGS.inactivity_s),
          fw is not None and fw[1] == 0x02 and t_fw is not None and lo <= t_fw <= hi,
          why="" if fw else "no FAREWELL (connection alive %s)" % c.alive(),
          farewell_reason=None if fw is None else fw[1], s_since_connect=t_fw, page_rounds_sent=sent,
          wt_close_code=c.cli.close_code, server_inactivity_ms=srv["inactivity_server_ms"])
    if ARGS.abandon_s:
        t = srv["abandon_s_after_spawn"]
        lo, hi = ARGS.abandon_s - 0.5, ARGS.abandon_s + 4.0
        check("a", "no gesture at all: the server's ABANDONMENT line (desktop closed) at the %.0f s ceiling "
              "from the child's birth" % ARGS.abandon_s,
              t is not None and lo <= t <= hi,
              why="" if t is not None else "no «§5.3 — ABANDONMENT» line for %s" % srv["user"],
              s_after_spawn=t, server_ms=srv["abandon_server_ms"], after=srv["after_abandonment"])
    await c.close()
    return "done"


async def case_b(src):
    c = await logged_in("b", src)
    if c is None:
        return "blind"
    n = 0
    end = c.admitted_at + ARGS.hold_s
    while c.alive() and now() < end:
        n += 1
        if n % 2:
            c.pointer(100 + (n * 37) % 1700, 100 + (n * 53) % 900)
        else:
            c.letter("x")
        await asyncio.sleep(ARGS.gesture_s)
    held = round(now() - c.admitted_at, 1)
    lines = log_lines()
    srv = server_reading("b", c, lines)
    out({"type": "server", "case": "b", **srv})
    ok = c.alive() and c.farewell is None and srv["inactivity_s_after_admitted"] is None \
        and srv["abandon_s_after_admitted"] is None
    check("b", "a gesture every %.0f s: still attached after %.0f s (past both ceilings %.0f/%.0f s)"
          % (ARGS.gesture_s, ARGS.hold_s, ARGS.inactivity_s, ARGS.abandon_s), ok,
          why="" if ok else "alive %s · FAREWELL %s · inactivity line at %s · abandonment line at %s" % (
              c.alive(), c.farewell and c.farewell[1], srv["inactivity_s_after_admitted"],
              srv["abandon_s_after_admitted"]),
          held_s=held, gestures=n)
    await c.close()
    return "done"


async def try_attach_without_password(case, src):
    """A NEW connection: HELLO → HERE_I_AM → ATTACH, no CREDENTIALS."""
    c = Conn(case, src)
    res = {}
    try:
        if not await c.open():
            return {"outcome": "no connection"}
        c.hello()
        await c.wait_for("HERE_I_AM", 10)
        c.send(0x0006, struct.pack("!IIII", 1920, 1080, 1920, 1080) + b3.s("it"))
        t0 = now()
        while now() < t0 + 6 and c.alive() and not any(n in ("SESSION", "FAREWELL") for _, n, _ in c.got):
            await asyncio.sleep(0.05)
        names = [n for _, n, _ in c.got]
        res = {"outcome": "SESSION" if "SESSION" in names else ("FAREWELL" if c.farewell else "no answer"),
               "farewell_reason": c.farewell and c.farewell[1], "messages": names,
               "wt_close_code": c.cli.close_code, "quic_code": c.cli.term_code}
    except Exception as e:  # noqa: BLE001
        res = {"outcome": "error", "error": "%s: %s" % (type(e).__name__, e)}
    finally:
        await c.close()
    return res


async def case_c(src, src2):
    c = await logged_in("c", src)
    if c is None:
        return "blind"
    c.pointer(400, 300)
    await asyncio.sleep(0.3)
    t_dark = now()
    c.go_dark(True)
    out({"type": "event", "case": "c", "what": "line DARK (both ways)", "for_s": ARGS.drop_s})
    await asyncio.sleep(ARGS.drop_s)
    c.go_dark(False)
    t_back = now()
    out({"type": "event", "case": "c", "what": "line BACK", "dropped_out": c.tr.dropped, "dropped_in": c.cli.dark_in})
    if c.alive():
        try:
            c.request_key()
        except Exception as e:  # noqa: BLE001
            out({"type": "event", "case": "c", "what": "REQUEST_KEY not sent", "error": str(e)})
    await asyncio.sleep(ARGS.after_s)
    old = {"alive": c.alive(), "farewell_reason": c.farewell and c.farewell[1],
           "farewell_s_after_back": None if c.farewell is None else round(c.farewell[0] - t_back, 2),
           "quic_code": c.cli.term_code, "quic_reason": c.cli.term_reason,
           "quic_end_s_after_back": None if c.cli.term_at is None else round(c.cli.term_at - t_back, 2),
           "wt_close_code": c.cli.close_code, "messages_after_back": [n for t, n, _ in c.got if t >= t_back]}
    out({"type": "event", "case": "c", "what": "the old connection after the line came back", **old})
    await c.close()
    nopw = await try_attach_without_password("c", src2)
    out({"type": "event", "case": "c", "what": "new connection, ATTACH without CREDENTIALS", **nopw})
    again = await logged_in("c", src2)
    relogin = "SESSION" if again is not None and again.session_at else "failed"
    # the new connection only watches (QUIC pings, no RCP byte): a login is not a gesture, so the
    # abandonment clock still counts from the POINTER before the drop
    if again is not None and ARGS.abandon_s:
        until = c.last_gesture + ARGS.abandon_s + 5
        while now() < until and again.alive() and again.farewell is None:
            await asyncio.sleep(0.25)
    fw2 = again.farewell if again is not None else None
    fw2_g = None if fw2 is None else round(fw2[0] - c.last_gesture, 2)
    if again:
        await again.close()
    lines = log_lines()
    srv = server_reading("c", c, lines)
    out({"type": "server", "case": "c", **srv})
    still_attached = old["alive"] and old["farewell_reason"] is None
    check("c", "line dark %.0f s (past the %.0f s ceiling), then back: the old connection does NOT resume "
          "attached" % (ARGS.drop_s, ARGS.inactivity_s), not still_attached,
          why="" if not still_attached else "the old connection is still attached after the line came back",
          old=old, dark_s=round(t_back - t_dark, 1),
          server_dead_line_s_after_admitted=srv["dead_line_s_after_admitted"],
          server_inactivity_s_after_admitted=srv["inactivity_s_after_admitted"],
          server_silence_detach_s_after_admitted=srv["silence_detach_s_after_admitted"])
    check("c", "a new connection cannot ATTACH without CREDENTIALS", nopw.get("outcome") != "SESSION",
          why="" if nopw.get("outcome") != "SESSION" else "SESSION without a password", **nopw)
    check("c", "with the password again: ADMITTED and SESSION", relogin == "SESSION", why=relogin)
    if ARGS.abandon_s and relogin == "SESSION":
        lo, hi = ARGS.abandon_s - 0.5, ARGS.abandon_s + 4.0
        ok = fw2 is not None and fw2[1] == 0x03 and lo <= fw2_g <= hi
        check("c", "the new login only watches: the desktop is closed (0x03) at the %.0f s ceiling counted from "
              "the last gesture BEFORE the drop — the login does not renew it" % ARGS.abandon_s, ok,
              why="" if ok else "FAREWELL %s at %s s after the last gesture" % (fw2 and fw2[1], fw2_g),
              farewell_s_after_gesture=fw2_g, server_abandon_ms=srv["abandon_server_ms"])
    return "done"


async def case_frozen(case, src):
    c = await logged_in(case, src)
    if c is None:
        return "blind"
    c.pointer(500, 500)
    t_g = c.last_gesture
    out({"type": "event", "case": case, "what": "last gesture, then the tab FREEZES (QUIC pings only)"})
    until = t_g + ARGS.inactivity_s + 6
    while now() < until and c.alive() and c.farewell is None:
        await asyncio.sleep(0.25)
    lines = log_lines()
    srv = server_reading(case, c, lines)
    out({"type": "server", "case": case, **srv})
    fw = c.farewell
    fw_g = None if fw is None else round(fw[0] - t_g, 2)
    sil = srv["silence_detach_s_after_admitted"] is not None
    lo, hi = ARGS.inactivity_s - 0.5, ARGS.inactivity_s + 3.0
    ok = not sil and fw is not None and fw[1] == 0x02 and lo <= fw_g <= hi
    check(case, "tab frozen (QUIC alive, no RCP byte) past SILENCE %.0f s: NOT detached for silence, FAREWELL "
          "0x02 at the %.0f s ceiling from the last gesture" % (SILENCE_S, ARGS.inactivity_s), ok,
          why="" if ok else "silence detach %s · FAREWELL %s at %s s after the gesture" % (sil, fw and fw[1], fw_g),
          farewell_s_after_gesture=fw_g, silence_line=srv["silence_line"],
          server_inactivity_ms=srv["inactivity_server_ms"])
    await c.close()
    return "done"


async def main():
    cases = [x.strip() for x in ARGS.cases.split(",") if x.strip()]
    srcs = ["127.0.0.%d" % (51 + i * 2) for i in range(len(cases))]
    out({"type": "start", "server": "%s:%d" % (ARGS.address, ARGS.port), "cases": cases,
         "inactivity_s": ARGS.inactivity_s, "abandon_s": ARGS.abandon_s})
    jobs = []
    for i, k in enumerate(cases):
        s, s2 = srcs[i], "127.0.0.%d" % (52 + i * 2)
        if k == "a":
            jobs.append(case_a(s))
        elif k == "b":
            jobs.append(case_b(s))
        elif k == "c":
            jobs.append(case_c(s, s2))
        elif k == "f":
            jobs.append(case_frozen(k, s))
        else:
            out({"type": "end", "exit": 2, "why": "unknown case %s" % k})
            return 2
    res = await asyncio.gather(*jobs, return_exceptions=True)
    for k, r in zip(cases, res):
        if isinstance(r, Exception):
            out({"type": "event", "case": k, "what": "case crashed", "error": "%s: %s" % (type(r).__name__, r)})
    blind = [k for k, r in zip(cases, res) if r != "done"]
    failed = [r for r in RESULTS if not r["ok"]]
    if len(blind) == len(cases):
        ex, why = 2, "blind: no case reached SESSION"
    elif failed or blind:
        ex, why = 1, "failed: %s; blind/crashed: %s" % ([r["case"] + ": " + r["name"][:60] for r in failed], blind)
    else:
        ex, why = 0, ""
    out({"type": "end", "exit": ex, "checks": len(RESULTS), "passed": len(RESULTS) - len(failed),
         "blind": blind, "why": why})
    return ex


def args():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--address", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7451)
    p.add_argument("--user-prefix", required=True, help="each case logs in as <prefix><case>")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--password")
    g.add_argument("--password-file")
    p.add_argument("--cases", default="a,b,c")
    p.add_argument("--inactivity-s", type=float, required=True, help="the server's --inactivity-s")
    p.add_argument("--abandon-s", type=float, required=True, help="the server's --abandon-s (0 = off)")
    p.add_argument("--chatter-s", type=float, default=2.0)
    p.add_argument("--gesture-s", type=float, default=5.0)
    p.add_argument("--hold-s", type=float, default=65.0)
    p.add_argument("--drop-s", type=float, default=25.0)
    p.add_argument("--after-s", type=float, default=6.0)
    p.add_argument("--server-log", default="")
    p.add_argument("--output", default="")
    a = p.parse_args()
    if a.password_file:
        with open(a.password_file) as f:
            a.password = f.read().strip()
    return a


if __name__ == "__main__":
    ARGS = args()
    sys.exit(asyncio.run(main()))
