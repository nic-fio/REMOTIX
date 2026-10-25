#!/usr/bin/env python3
"""01-b10-flood.py — B10: the QUIC connection caps and the eviction, against a RUNNING server
(DECISIONS §11.40, RELEASE-CHECKLIST B1.10; commits 2f671726, a723eb6b, f4201ee6).

    python3 01-b10-flood.py --address 127.0.0.1 --address6 ::1 --port 7451 --user rxflood --password-file pw \
        --v4-sources 127.0.0.100-127.0.0.139 --legit-source 127.0.0.50 \
        --v6-prefix fd5a:f100:d000 --server-log /flood/server.log --output b10.jsonl

⭐ The server under test runs with SMALL caps by default, so the test is quick and the numbers are ours:
     --max-pending 16 --max-pending-per-address 4 --max-pending-per-48 8
   (the defaults of the product are 128 / 8 / 32; the rule is the same, only the numbers change; 01-b10-launch.sh
   takes B10_PENDING / B10_ADDRESS / B10_48 / B10_NFLOOD for them).  The bench is told the caps with --cap-pending /
   --cap-address / --cap-48 and checks against them: every number of a check is derived from them (the «5th from one
   address» is cap-address + 1, the /64s of c-48 are cap-48 / 2 + 1, the flood is n-flood x cap-address workers).
   `--plan` (no network, no aioquic needed) prints that derivation and the problems of a combination.
⭐ The client needs SEVERAL SOURCE ADDRESSES that route back to it: extra IPv4/IPv6 addresses on
   its interface (01-b10-launch.sh puts IPv6 ones on `lo` of a private namespace), and 127.0.0.x on
   loopback (every 127/8 address is local on Linux, no setup).

The five checks, each one line of JSONL ({"type": "check", "name", "ok", "why", ...}):

  c-address   from ONE address, cap-address sessions open (WebTransport 200, no HELLO); the next
              one from the same address is REFUSED during the handshake with CONNECTION_REFUSED
              (0x2) — it never completes, so the server kept no connection for it; one more from
              ANOTHER address is accepted at the same moment (the refusal is per address).
  c-48        (IPv6 only, --v6-prefix) cap-48 sessions from cap-48/2 different /64s of ONE /48,
              two per /64 (under the per-address cap); the next from a new /64 of the same /48 is
              REFUSED with 0x2 during the handshake.
  b-age       two connections that never log in and are kept alive by OUR PINGs — one with no
              WebTransport session at all, one with a session that never says HELLO (it gets
              TIMED_OUT at 5 s and stays alive): both are closed by the server with
              CONNECTION_REFUSED at 90 s from their birth (UNLOGGED_MAX_S), not before 89 s and
              not after 95 s.
  a-flood     n-flood addresses × cap-address workers open sessions and never say HELLO (half
              with the control channel, half without); when the server closes one, it reconnects
              at once.  Pending places are far fewer than the flood: the server must EVICT flood
              connections (CONNECTION_REFUSED after the handshake), and evictions must happen.
  d-login     during the flood, from an address the flood does not use, --logins full logins
              (HELLO → HERE_I_AM → CREDENTIALS → ADMITTED), one after the other: ALL must reach
              ADMITTED.  The connection of a real user is never the victim: its place has 1
              pending connection, the flood's have cap-address.

  And with --server-log (a file this process can read): the server's own lines are counted —
  «new connection from» for each accepted one, «EVICTED», «not logged in after 90 s», and the
  10 s summary «SERVER UNDER PRESSURE» with its refusals per address and per /48.

Exit: 0 every check passed · 1 a check failed · 2 blind (the server is not there, or a login
BEFORE the flood already fails: the scene cannot be exercised).
"""
import argparse
import asyncio
import importlib.util
import ipaddress
import json
import os
import random
import re
import socket
import ssl
import sys
import time


def plan(cap_pending, cap_address, cap_48, n_flood, v4_given=40, v6_64s_given=10):
    """What the checks will ask of the scene for these caps; (lines, problems).  Pure: also run by --plan."""
    workers = n_flood * cap_address
    lines = ["c-address: %d sessions from one address, the %d-th must be refused" % (cap_address, cap_address + 1),
             "c-48: %d sessions in %d /64s (two each), the %d-th, from /64 #%x, must be refused"
             % (cap_48, (cap_48 + 1) // 2, cap_48 + 1, cap_48 // 2 + 1),
             "a-flood: %d addresses x %d workers = %d against %d pending places (live after warm-up >= %d)"
             % (n_flood, cap_address, workers, cap_pending, cap_pending - 1),
             "IPv4 sources needed: %d (4 + n-flood) · IPv6 /64s needed: %d" % (4 + n_flood, cap_48 // 2 + 1)]
    problems = []
    if cap_address < 2:
        problems.append("cap-address < 2: c-48 puts two sessions in each /64")
    if cap_48 > cap_pending:
        problems.append("cap-48 > cap-pending: the total cap would bite before the /48 cap")
    if cap_address > cap_pending:
        problems.append("cap-address > cap-pending: the total cap would bite before the address cap")
    if workers <= cap_pending:
        problems.append("flood workers (%d) <= pending places (%d): the server never has to evict" % (workers, cap_pending))
    if workers < cap_pending * 3 // 2:
        problems.append("flood workers (%d) < 1.5 x places (%d): 'live after warm-up >= places-1' may fail by churn" % (workers, cap_pending))
    if 4 + n_flood > v4_given:
        problems.append("%d IPv4 sources given, %d needed" % (v4_given, 4 + n_flood))
    if cap_48 // 2 + 1 > v6_64s_given:
        problems.append("%d /64s on lo given, %d needed" % (v6_64s_given, cap_48 // 2 + 1))
    return lines, problems


if "--plan" in sys.argv:
    _p = argparse.ArgumentParser()
    _p.add_argument("--plan", action="store_true")
    _p.add_argument("--cap-pending", type=int, default=16)
    _p.add_argument("--cap-address", type=int, default=4)
    _p.add_argument("--cap-48", type=int, default=8)
    _p.add_argument("--n-flood", type=int, default=10)
    _p.add_argument("--v4-given", type=int, default=40)
    _p.add_argument("--v6-64s-given", type=int, default=10)
    _a = _p.parse_args()
    _l, _pr = plan(_a.cap_pending, _a.cap_address, _a.cap_48, _a.n_flood, _a.v4_given, _a.v6_64s_given)
    print("\n".join("  " + x for x in _l))
    print("\n".join("  PROBLEM: " + x for x in _pr) if _pr else "  no problems")
    sys.exit(1 if _pr else 0)

from aioquic.h3.connection import H3_ALPN
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection
from aioquic.quic.events import ConnectionTerminated

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("b3cliente", os.path.join(HERE, "01-b3-client.py"))
b3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b3)
# ⚠ The b3 client prints a line for every closed connection: a flood would bury ours.
b3.print = lambda *a, **k: None

CONNECTION_REFUSED = 0x2
UNLOGGED_MAX_S = 90


def out(rec):
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    if ARGS.output:
        with open(ARGS.output, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def now():
    return time.monotonic()


class Cli(b3.Client):
    """b3's client, plus: the error code of the CONNECTION_CLOSE, whether the handshake ever
    completed, and the instant of the end."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.born = now()
        self.handshake_done = False
        self.term_code = None
        self.term_reason = ""
        self.term_at = None

    def quic_event_received(self, event):
        n = type(event).__name__
        if n == "HandshakeCompleted":
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
    """One QUIC connection from a chosen SOURCE address (aioquic's connect() binds only '::')."""

    def __init__(self, src, dst, port, idle_s=60.0):
        self.src, self.dst, self.port = src, dst, port
        self.idle_s = idle_s
        self.cli = None
        self.transport = None
        self.pinger = None

    async def open(self, timeout=8.0):
        loop = asyncio.get_running_loop()
        conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN, max_datagram_frame_size=65536,
                                 idle_timeout=self.idle_s)
        conf.verify_mode = ssl.CERT_NONE
        conf.server_name = self.dst
        quic = QuicConnection(configuration=conf)
        v6 = ":" in self.src or ":" in self.dst
        sock = socket.socket(socket.AF_INET6 if v6 else socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.src, 0, 0, 0) if v6 else (self.src, 0))
        self.transport, self.cli = await loop.create_datagram_endpoint(lambda: Cli(quic), sock=sock)
        addr = (self.dst, self.port, 0, 0) if v6 else (self.dst, self.port)
        self.cli.connect(addr, transmit=True)
        try:
            await asyncio.wait_for(self.cli.wait_connected(), timeout)
        except Exception:  # noqa: BLE001 — the outcome is in self.cli.term_code
            pass
        return self.cli.handshake_done

    async def session(self, control=True, timeout=8.0):
        self.cli.open_session("%s:%d" % (self.dst, self.port), "/rcp/1")
        st = await asyncio.wait_for(self.cli.accepted, timeout)
        if control:
            self.cli.open_control()
            self.cli.transmit()
        return st

    def keep_alive(self, every=4.0):
        async def ping():
            uid = 1
            while self.cli and self.cli.term_at is None:
                await asyncio.sleep(every)
                try:
                    self.cli._quic.send_ping(uid)
                    self.cli.transmit()
                except Exception:  # noqa: BLE001
                    return
                uid += 1
        self.pinger = asyncio.ensure_future(ping())

    def alive(self):
        return self.cli is not None and self.cli.term_at is None

    async def close(self):
        if self.pinger:
            self.pinger.cancel()
        if self.cli is not None:
            if self.cli.term_at is None:
                self.cli.closed_by_us = True
                self.cli.close()
                try:
                    await asyncio.wait_for(self.cli.wait_closed(), 2)
                except Exception:  # noqa: BLE001
                    pass
        if self.transport is not None:
            self.transport.close()


def check(name, ok, why="", **extra):
    rec = {"type": "check", "round": ARGS.round, "name": name, "ok": bool(ok), "why": why}
    rec.update(extra)
    out(rec)
    RESULTS.append(rec)
    return ok


def log_text():
    if not ARGS.server_log:
        return None
    try:
        with open(ARGS.server_log, "rb") as f:
            return f.read().decode("utf-8", "replace")
    except OSError:
        return None


def log_since(mark):
    t = log_text()
    return None if t is None else t[mark:]


def log_mark():
    t = log_text()
    return 0 if t is None else len(t)


def dst_for(src):
    """The server's address in the family of the source."""
    return ARGS.address6 if ":" in src else ARGS.address


def parse_sources(spec):
    """'a-b' (IPv4 range) or 'a,b,c'."""
    if "-" in spec and "," not in spec and ":" not in spec:
        a, b = spec.split("-")
        a, b = ipaddress.IPv4Address(a), ipaddress.IPv4Address(b)
        return [str(ipaddress.IPv4Address(i)) for i in range(int(a), int(b) + 1)]
    return [s.strip() for s in spec.split(",") if s.strip()]


async def pending_session(src, control=True):
    """A connection from `src` that opens its session and never says HELLO, kept alive by PINGs.
    Returns (Conn, outcome) — outcome: 'open' (200), 'refused-handshake' (0x2 before the
    handshake), 'closed:<code>' or 'error:...'."""
    c = Conn(src, dst_for(src), ARGS.port)
    try:
        done = await c.open()
    except Exception as e:  # noqa: BLE001
        return c, "error:%s" % type(e).__name__
    if not done:
        code = c.cli.term_code
        if code == CONNECTION_REFUSED:
            return c, "refused-handshake"
        return c, "no-handshake:%s" % code
    try:
        st = await c.session(control=control)
    except Exception as e:  # noqa: BLE001
        return c, "closed:%s" % (c.cli.term_code if c.cli.term_code is not None else type(e).__name__)
    if st != "200":
        return c, "status:%s" % st
    c.keep_alive()
    return c, "open"


async def login(src, why=""):
    """A full login from `src`: (ok, text, seconds)."""
    c = Conn(src, dst_for(src), ARGS.port)
    t0 = now()
    try:
        if not await c.open():
            return False, "no handshake (code %s %s)" % (c.cli.term_code, c.cli.term_reason), now() - t0
        st = await c.session(control=True)
        if st != "200":
            return False, "CONNECT :status=%s" % st, now() - t0
        c.cli.send_msg(B6.good_hello())
        await b3.should_wait(c.cli, "HERE_I_AM", wait=10)
        c.cli.send_msg(b3.wrap(0x0003, b3.s(ARGS.user) + b3.s(ARGS.password)))
        try:
            await b3.should_wait(c.cli, "ADMITTED", wait=25)
        except RuntimeError as e:
            # ⭐ No desktop where the server runs (01-b10-launch.sh): PAM says yes, the stage is
            #   spawned and ends at once, and the server says FAREWELL(0x10 SESSION_TERMINATED) while
            #   the verdict is still held by the fixed second.  The server spawns a stage ONLY after
            #   PAM's yes (main.c, delivery_verdict), so 0x10 after CREDENTIALS = admitted; the
            #   server's own «PAM answered … admitted» lines are counted apart (--server-log).
            if ARGS.stage_less and "reason 0x10" in str(e):
                return True, "HELLO → HERE_I_AM → CREDENTIALS → admitted by PAM (FAREWELL 0x10: no desktop)", \
                    now() - t0
            raise
        return True, "HELLO → HERE_I_AM → CREDENTIALS → ADMITTED", now() - t0
    except Exception as e:  # noqa: BLE001
        code = c.cli.term_code if c.cli else None
        return False, "%s: %s (connection code %s %s)" % (type(e).__name__, e, code,
                                                         c.cli.term_reason if c.cli else ""), now() - t0
    finally:
        await c.close()


async def close_all(conns):
    await asyncio.gather(*(c.close() for c in conns), return_exceptions=True)
    # the server reaps a closed connection on its next pass; give it a moment
    await asyncio.sleep(1.5)


# ── c-address ───────────────────────────────────────────────────────────────
async def t_address(srcs):
    a, b = srcs[0], srcs[1]
    conns, outcomes = [], []
    for i in range(ARGS.cap_address):
        c, o = await pending_session(a, control=(i % 2 == 0))
        conns.append(c)
        outcomes.append(o)
    c, over = await pending_session(a)
    conns.append(c)
    over_hs = c.cli.handshake_done if c.cli else None
    c, other = await pending_session(b)
    conns.append(c)
    ok = all(o == "open" for o in outcomes) and over == "refused-handshake" and other == "open"
    check("c-address: the %d-th pending from one address is refused, statelessly" % (ARGS.cap_address + 1), ok,
          why="" if ok else "first %d: %s · the next from %s: %s (handshake completed: %s) · from %s: %s"
          % (ARGS.cap_address, outcomes, a, over, over_hs, b, other),
          first=outcomes, over=over, over_handshake_completed=over_hs, other_address=other)
    await close_all(conns)


# ── c-48 ────────────────────────────────────────────────────────────────────
async def t_48():
    p = ARGS.v6_prefix
    srcs = ["%s:%x::10" % (p, i // 2 + 1) if i % 2 == 0 else "%s:%x::11" % (p, i // 2 + 1)
            for i in range(ARGS.cap_48)]
    conns, outcomes = [], []
    for i, s in enumerate(srcs):
        c, o = await pending_session(s, control=(i % 2 == 0))
        conns.append(c)
        outcomes.append(o)
    new64 = "%s:%x::10" % (p, ARGS.cap_48 // 2 + 1)
    SEEN["over48"] = new64
    c, over = await pending_session(new64)
    conns.append(c)
    over_hs = c.cli.handshake_done if c.cli else None
    ok = all(o == "open" for o in outcomes) and over == "refused-handshake"
    check("c-48: the %d-th pending from one IPv6 /48 (a new /64) is refused, statelessly" % (ARGS.cap_48 + 1), ok,
          why="" if ok else "first %d (%s…): %s · the next from %s: %s (handshake completed: %s)"
          % (ARGS.cap_48, srcs[0], outcomes, new64, over, over_hs),
          first=outcomes, over=over, over_handshake_completed=over_hs, sources=srcs + [new64])
    await close_all(conns)


# ── b-age ───────────────────────────────────────────────────────────────────
async def t_age_start(src_none, src_wt):
    """Starts the two aged connections; t_age_end() judges them."""
    c1 = Conn(src_none, dst_for(src_none), ARGS.port)
    ok1 = await c1.open()
    if ok1:
        c1.keep_alive()
    c2, o2 = await pending_session(src_wt, control=True)
    return (c1, ok1), (c2, o2)


async def t_age_end(age):
    (c1, ok1), (c2, o2) = age
    deadline = max(c1.cli.born, c2.cli.born) + UNLOGGED_MAX_S + 15
    while now() < deadline and (c1.alive() or c2.alive()):
        await asyncio.sleep(0.25)
    for label, c, ready in (("no WebTransport session", c1, ok1), ("session, never HELLO", c2, o2 == "open")):
        cli = c.cli
        life = (cli.term_at - cli.born) if cli.term_at else None
        ok = ready and life is not None and cli.term_code == CONNECTION_REFUSED and \
            UNLOGGED_MAX_S - 1 <= life <= UNLOGGED_MAX_S + 5
        check("b-age: a connection that never logs in (%s) is closed at %d s" % (label, UNLOGGED_MAX_S), ok,
              why="" if ok else "ready %s · lived %s s · code %s %s" % (ready, None if life is None else round(life, 2),
                                                                      cli.term_code, cli.term_reason),
              lived_s=None if life is None else round(life, 2), code=cli.term_code, reason=cli.term_reason,
              wt_close=cli.close_code)
        await c.close()


# ── a-flood + d-login ───────────────────────────────────────────────────────
async def t_flood(flood_srcs, legit):
    stats = {"opened": 0, "evicted": 0, "evicted_before_session": 0, "refused_handshake": 0, "other_end": 0,
             "errors": 0}
    ends = {}
    stop = asyncio.Event()
    live = set()

    async def worker(src, k):
        while not stop.is_set():
            c, o = await pending_session(src, control=(k % 2 == 0))
            if o == "open":
                stats["opened"] += 1
                live.add(c)
                while c.alive() and not stop.is_set():
                    await asyncio.sleep(0.1)
                live.discard(c)
                if not stop.is_set():
                    code = c.cli.term_code
                    if code == CONNECTION_REFUSED:
                        stats["evicted"] += 1
                    else:
                        stats["other_end"] += 1
                        ends[str(code)] = ends.get(str(code), 0) + 1
            elif o == "refused-handshake":
                stats["refused_handshake"] += 1
            elif o == "closed:%d" % CONNECTION_REFUSED:
                # evicted after the handshake, before its session was accepted: state «(none)»
                stats["evicted_before_session"] += 1
            else:
                stats["errors"] += 1
                ends[o] = ends.get(o, 0) + 1
            await c.close()
            # ⭐ R4: the pause between two births of a worker.  The default (0.2-0.5 s) is faster than the server's handshake rate
            #    (4 a second per address): most of the flood is then refused for RATE (CONNECTION_REFUSED too).  --flood-gap S sets
            #    it, so the births can be slowed under the rate, or the rate left to work.
            await asyncio.sleep(ARGS.flood_gap if ARGS.flood_gap is not None else 0.2 + random.random() * 0.3)

    tasks = [asyncio.ensure_future(worker(s, k)) for s in flood_srcs for k in range(ARGS.cap_address)]
    # let the flood fill every place first
    await asyncio.sleep(ARGS.flood_warmup if ARGS.flood_warmup is not None
                        else max(8.0, len(flood_srcs) * ARGS.cap_address / 8.0))
    filled = len(live)
    logins = []
    for i in range(ARGS.logins):
        ok, text, secs = await login(legit)
        logins.append({"ok": ok, "text": text, "seconds": round(secs, 2), "flood_live": len(live)})
        out({"type": "login", "round": ARGS.round, "n": i + 1, "ok": ok, "text": text, "seconds": round(secs, 2),
             "flood_live": len(live), "flood": dict(stats)})
        await asyncio.sleep(ARGS.login_gap)
    stop.set()
    await asyncio.gather(*tasks, return_exceptions=True)
    await close_all(list(live))
    wanted = len(flood_srcs) * ARGS.cap_address
    ok_a = stats["evicted"] > 0 and filled >= ARGS.cap_pending - 1 and stats["errors"] == 0
    check("a-flood: %d never-HELLO workers from %d addresses against %d pending places — the server evicts "
          "the flood" % (wanted, len(flood_srcs), ARGS.cap_pending), ok_a,
          why="" if ok_a else "evicted %d, live flood connections after warm-up %d" % (stats["evicted"], filled),
          flood=stats, other_ends=ends, live_after_warmup=filled)
    # ⭐ A real ADMITTED, not the old stage-less tolerance: the session child now starts (its libs
    #   are in /usr/local/lib and it is in the card's group — 01-b10-launch.sh), so a right password
    #   reaches ADMITTED.  A FAREWELL 0x10 before ADMITTED is NO LONGER counted as admitted.
    def admitted(x):
        return x["ok"] and x["text"].rstrip().endswith("ADMITTED")
    good = sum(1 for x in logins if admitted(x))
    ok_d = good == len(logins) and len(logins) > 0
    check("d-login: a real login during the flood is ADMITTED (%d of %d)" % (good, len(logins)), ok_d,
          why="" if ok_d else "; ".join(x["text"] for x in logins if not admitted(x)), logins=logins)


async def main():
    srcs = parse_sources(ARGS.v4_sources)
    need = 2 + 2 + ARGS.n_flood
    if len(srcs) < need:
        out({"type": "end", "exit": 2, "why": "%d sources given, %d needed" % (len(srcs), need)})
        return 2
    addr_srcs, age_srcs, flood_srcs = srcs[:2], srcs[2:4], srcs[4:4 + ARGS.n_flood]
    SEEN["addr"], SEEN["flood"] = addr_srcs[0], flood_srcs
    out({"type": "start", "round": ARGS.round, "server": "%s:%d" % (ARGS.address, ARGS.port),
         "caps": {"pending": ARGS.cap_pending, "per_address": ARGS.cap_address, "per_48": ARGS.cap_48},
         "flood_sources": flood_srcs, "legit": ARGS.legit_source, "v6_prefix": ARGS.v6_prefix})
    mark = log_mark()
    # 0. the scene: a login works with no flood (otherwise every red below is a false red)
    ok, text, secs = await login(ARGS.legit_source)
    out({"type": "login", "round": ARGS.round, "n": 0, "ok": ok, "text": text, "seconds": round(secs, 2),
         "flood_live": 0})
    if not ok:
        out({"type": "end", "exit": 2, "why": "blind: a login with NO flood already fails: " + text})
        return 2
    # 1. the two aged connections run in the background while the caps are tested (they hold 2
    #    pending places from 2 addresses of their own: under every cap)
    age = None
    if not ARGS.no_age:
        age = await t_age_start(*age_srcs)
    await t_address(addr_srcs)
    if ARGS.v6_prefix:
        await t_48()
    if age:
        await t_age_end(age)
    await t_flood(flood_srcs, ARGS.legit_source)
    # 2. the server's own words
    t = log_since(mark)
    if t is not None:
        await asyncio.sleep(0)
        summ = re.findall(r"SERVER UNDER PRESSURE[^\n]*", t)
        def total(rx):
            return sum(int(m) for m in re.findall(rx, "\n".join(summ)))
        counts = {
            "new_connection_lines": len(re.findall(r"new connection from", t)),
            "pam_admitted_lines": len(re.findall(r"PAM answered \(request \d+\): admitted", t)),
            "evicted_lines": len(re.findall(r"EVICTED \(", t)),
            "aged_lines": len(re.findall(r"not logged in after %d s" % UNLOGGED_MAX_S, t)),
            "pressure_lines": len(summ),
            "handshake_rate_lines": len(re.findall(r"HANDSHAKE RATE", t)),
            "handshake_rate_refused": sum(int(m) for m in re.findall(r"(\d+) new handshakes refused for coming too fast", t)),
            "summary_aged": total(r"(\d+) connections closed for not logging in"),
            "summary_evicted": total(r"(\d+) EVICTED to make room"),
            "summary_refused_full": total(r"REFUSED: (\d+) full"),
            "summary_refused_address": total(r"(\d+) over \d+ pending\s+from one address"),
            "summary_refused_48": total(r"(\d+) over \d+ pending from one IPv6 /48"),
        }
        want_aged = 0 if ARGS.no_age else 2
        # ⭐ «statelessly»: the refused newcomer was never BORN — the server writes «new connection
        #   from» for every connection it accepts, and from the full address there are exactly cap.
        def born_from(a):
            return len(re.findall(r"new connection from \[(?:::ffff:)?%s\]:" % re.escape(a), t))
        born_a = born_from(SEEN["addr"])
        born_48 = born_from(SEEN.get("over48", "-")) if ARGS.v6_prefix else 0
        ok = born_a == ARGS.cap_address and born_48 == 0
        check("log: the refused newcomers were never born (from the full address %d «new connection» lines, "
              "from the new /64 of the full /48 %d)" % (ARGS.cap_address, 0), ok,
              why="" if ok else "from %s: %d, from %s: %d" % (SEEN["addr"], born_a, SEEN.get("over48"), born_48),
              born_full_address=born_a, born_over_48=born_48)
        # ⭐ «a flood evicts itself»: every EVICTED line names a flood address, never the real user's
        ev = re.findall(r"\[(?:::ffff:)?([0-9a-f.:]+)\]:\d+ EVICTED \(([^)]*\)?)\)", t)
        not_flood = sorted({a for a, _ in ev if a not in SEEN["flood"]})
        states = {}
        for _, s in ev:
            states[s] = states.get(s, 0) + 1
        ok = len(ev) > 0 and not not_flood
        check("log: every evicted connection is the flood's — the real user's address %s never" % ARGS.legit_source,
              ok, why="" if ok else "evicted from outside the flood: %s (of %d)" % (not_flood, len(ev)),
              evicted=len(ev), evicted_states=states, evicted_not_flood=not_flood)
        ok = (counts["summary_refused_address"] >= 1 and (counts["summary_refused_48"] >= 1 or not ARGS.v6_prefix)
              and counts["aged_lines"] >= want_aged and counts["evicted_lines"] >= 1 and counts["pressure_lines"] >= 1)
        check("log: the server says it — refusals per address%s, %d age closes, evictions, in the 10 s summary"
              % (" and per /48" if ARGS.v6_prefix else "", want_aged), ok,
              why="" if ok else json.dumps(counts), counts=counts, summaries=summ[-6:])
    bad = [r["name"] for r in RESULTS if not r["ok"]]
    code = 1 if bad else 0
    out({"type": "end", "round": ARGS.round, "exit": code, "failed": bad,
         "passed": sum(1 for r in RESULTS if r["ok"]), "checks": len(RESULTS)})
    return code


def args():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--address", required=True)
    p.add_argument("--address6", default="::1", help="the server's IPv6 address, for the IPv6 sources")
    p.add_argument("--port", type=int, default=7451)
    p.add_argument("--user", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--password")
    g.add_argument("--password-file")
    p.add_argument("--v4-sources", required=True, help="a-b IPv4 range or a,b,c (4 + --n-flood needed)")
    p.add_argument("--legit-source", required=True)
    p.add_argument("--v6-prefix", default="", help="the first 48 bits, e.g. fd5a:f100:d000 (empty: no /48 test)")
    p.add_argument("--cap-pending", type=int, default=16)
    p.add_argument("--cap-address", type=int, default=4)
    p.add_argument("--cap-48", type=int, default=8)
    p.add_argument("--n-flood", type=int, default=10)
    p.add_argument("--logins", type=int, default=5)
    p.add_argument("--login-gap", type=float, default=2.0)
    p.add_argument("--flood-warmup", type=float, default=None,
                   help="seconds to let the flood fill the places (default: 8, or n-flood x cap-address / 8 if more)")
    p.add_argument("--flood-gap", type=float, default=None,
                   help="seconds a flood worker waits between two births (default: 0.2-0.5, random). The server limits new "
                        "handshakes to 4 a second per address (burst 16): a worker per address that reconnects faster is refused for "
                        "RATE (the same CONNECTION_REFUSED as a cap); with --cap-address workers per address use a gap of "
                        "cap-address / 4 s or more to stay under it")
    p.add_argument("--no-age", action="store_true", help="skip the 90 s test")
    p.add_argument("--stage-less", action="store_true",
                   help="the server has no desktop: FAREWELL 0x10 right after CREDENTIALS counts as admitted")
    p.add_argument("--server-log", default="")
    p.add_argument("--output", default="")
    p.add_argument("--round", default=time.strftime("%Y%m%d-%H%M%S"))
    a = p.parse_args()
    if a.password_file:
        with open(a.password_file) as f:
            a.password = f.read().strip()
    return a


if __name__ == "__main__":
    ARGS = args()
    RESULTS = []
    SEEN = {}
    _s6 = importlib.util.spec_from_file_location("b6caps", os.path.join(HERE, "01-b6-caps.py"))
    B6 = importlib.util.module_from_spec(_s6)
    _s6.loader.exec_module(B6)
    sys.exit(asyncio.run(main()))
