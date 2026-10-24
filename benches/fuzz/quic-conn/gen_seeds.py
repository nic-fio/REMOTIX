#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_seeds.py — the seed corpus of the `quic-conn` fuzz target (reduced from the 1.5-scartata tag: only
`quic_conn()` and the helpers it uses).

    python3 gen_seeds.py <out-dir>       → <out-dir>/quic-conn/seed-NN

The seeds are the op streams of `fuzz_quic_conn.c` (format in its header comment): byte 0 = configuration,
then ops `kind | sel << 5`, u16 length, arguments.
"""
import os
import socket
import struct
import sys

def ms(n):  # the harnesses count time in units of 4 ms
    return struct.pack("!H", n // 4)

# ── QUIC on an ESTABLISHED connection, `fuzz_quic_conn.c` (the played ngtcp2 of `stubs_quic.c`) ──
def qop(kind, arg=b"", sel=0):
    return bytes([kind | (sel << 5)]) + struct.pack("!H", len(arg)) + arg

class Ev:
    """What the played ngtcp2 «finds» in a packet (`stubs_quic.c`): one byte of flags, then events."""
    @staticmethod
    def tx(onertt):
        return bytes([1 | (int(onertt) << 4)])
    HS = b"\x02"

    @staticmethod
    def data(sid, payload, fin=False):
        return bytes([3 | (int(fin) << 4), sid, len(payload)]) + payload

    @staticmethod
    def close(idx, code=0, p=0):
        return bytes([4 | (p << 4), idx, code])

    @staticmethod
    def reset(idx, code=1):
        return bytes([5, idx, code])

    @staticmethod
    def stop(idx, code=1):
        return bytes([6, idx, code])

    @staticmethod
    def acked(idx, n=100):
        return bytes([7, idx, n])

    @staticmethod
    def max_bidi(n=10):
        return bytes([8, n])

    @staticmethod
    def max_data(idx, n=4):
        return bytes([9, idx, n])

    @staticmethod
    def dgram(payload):
        return bytes([10, len(payload)]) + payload

    @staticmethod
    def fate(i, lost=False):
        return bytes([11 | (int(lost) << 4), i])

    @staticmethod
    def new_cid(k=1):
        return bytes([12 | ((k - 1) << 4)])

    @staticmethod
    def retire(i):
        return bytes([13, i])

    @staticmethod
    def path_result(failed=False):
        return bytes([14 | (int(failed) << 4)])

    @staticmethod
    def local(a0):
        return bytes([15 | (1 << 4), a0])
    RAND = bytes([15 | (2 << 4), 0])

    @staticmethod
    def end(rv):
        return bytes([rv << 4])

def q_new(addr=0, events=b"", flags=0, token=0, fail=8, hold=0, dcid=4, local=0):
    return qop(0, bytes([addr, dcid, token, fail, hold | (local << 1), flags]) + events)

def q_pkt(events=b"", sel=0, addr=0, cid=1, long=False, hold=False, local=0, flags=0):
    f = int(long) | (int(hold) << 1) | (local << 2)
    return qop(1, bytes([addr, cid, f, flags]) + events, sel)

def q_time(ms, sel=0):
    return qop(3, struct.pack("!H", ms), sel)

def quic_conn(graft=False):
    """Seeds of `quic-conn`: byte 0 = configuration (bit 0 IPv6), then ops.
    ⛔ `graft=True` leaves out every seed that MIGRATES: the fault check must find the way
       there by itself (`build.sh`, `quic-conn-graft`)."""
    E = Ev
    up = q_new(events=E.tx(0) + E.tx(1)) + q_pkt(E.HS + E.new_cid(3), long=True, cid=0)
    up2 = q_new(addr=3, events=E.tx(0) + E.tx(1), dcid=12) + \
        q_pkt(E.HS + E.new_cid(2), sel=1, addr=3, long=True, cid=0)
    def streams_from(addr):
        return q_pkt(E.data(0, b"\x01\x04CONNECT") + E.data(2, b"\x00\x04\x41") + E.data(6, b"x")
                     + E.dgram(b"\x04\x01" + bytes(14)) + E.fate(0) + E.fate(1, True)
                     + E.local(0) + E.local(2) + E.acked(3) + E.max_data(3) + E.max_bidi(20),
                     addr=addr)
    streams = streams_from(0)
    lifecycle = q_pkt(E.stop(3) + E.reset(1) + E.close(0, 7, 1) + E.close(1, 0, 2)
                      + E.data(4, b"fin", True) + E.close(0) + E.RAND)
    retire = q_pkt(E.retire(1) + E.retire(2)) + q_time(250) + q_pkt(b"", cid=1) + q_pkt(b"", cid=3)
    out = [
        b"\x00" + up + streams + q_time(100) + qop(7),
        b"\x00" + up + streams + lifecycle + q_time(50) + qop(7),
        b"\x00" + up + retire + q_pkt(E.new_cid(2), cid=4),
        # errors on a live connection, and the end of each
        b"\x00" + up + q_pkt(E.end(2)) + q_pkt(b"", cid=2),                    # CRYPTO
        b"\x00" + up + q_pkt(E.end(3)),                                       # PROTO
        b"\x00" + up + q_pkt(E.end(1)) + q_time(10),                           # DRAINING
        b"\x00" + q_new(events=E.end(5)),                                      # DROP_CONN, first
        b"\x00" + q_new(events=E.tx(0) + E.end(6)),                            # RETRY
        b"\x00" + up + qop(4, bytes([0, 1, 1, 4, 176, 0, 0, 0, 0, 0, 0])) + q_pkt(E.data(0, b"x")),
        b"\x00" + up + qop(4, bytes([0, 0, 2, 4, 176, 2, 0, 0, 0, 0, 0])) + q_time(10),  # dead line
        b"\x00" + up + q_time(31000) + q_time(1000),                          # §2.2: 30 s
        b"\x00" + up + qop(9, bytes([0, 1, 0, 0, 0, 0, 0])) + q_pkt(b""),      # write fails
        b"\x00" + up + qop(9, bytes([0, 0, 1, 2, 5, 3, 1])) + q_pkt(E.end(3)) + q_time(30),
        b"\x00" + up + qop(4, bytes([0, 0, 3, 4, 176, 8, 25, 0, 0, 0, 9]))
        + q_time(120) + qop(5, b"\x00\x00\x00\x09\x01") + qop(5, b"\x00\x00\x00\x07\x00"),
        b"\x00" + up + up2 + qop(6, b"\x0c") + qop(7) + q_time(5),
        # many packets in one round (MAX_PACKETS_PER_ROUND), then the rest
        b"\x00" + up + b"".join(q_pkt(b"", hold=True) for _ in range(70)) + qop(10) + qop(10),
        # accept: every step that can fail, and the tokens
        b"\x00" + b"".join(q_new(fail=f) for f in range(1, 8)),
        b"\x00" + q_new(token=1) + q_new(token=2) + q_new(token=0x10) + q_new(token=0x20)
        + q_new() + q_new(token=0x40) + qop(2, b"\x00\x40" + bytes(30))
        + qop(2, b"\x00\xc3\x1a\x2a\x3a\x4a\x08" + bytes(8) + b"\x08" + bytes(8) + bytes(1200)),
        # the socket
        b"\x00" + qop(8, bytes([0x0a, 3, 1])) + up + q_pkt(b"") + qop(8, bytes([0x02, 0, 2]))
        + q_pkt(b"") + qop(11),
        b"\x01" + up2 + streams_from(3) + q_time(100),
    ]
    # ⭐ the connection caps (15 Oct 2026): full with every RCP state (op 4 a5 bits 5-7:
    #    none · hello · credentials · verdict · attach · active · finished), eviction,
    #    refusal and a failing accept; and a connection kept alive by its packets past the
    #    age limit (UNLOGGED_MAX_S, 90 s) in each state
    for v6 in (0, 1):
        b = bytes([v6])
        for k in range(7):
            b += q_new(addr=k % 4, events=E.tx(0) + E.tx(1), dcid=k)
            b += qop(4, bytes([0, 0, 0, 0, 0, (k % 7) << 5, 0, 0, 0, 0, 0]), k)
        b += q_new(addr=2, fail=3) + q_new(addr=2) + q_new(addr=1) + q_new(addr=0)
        out.append(b)
    for st in range(7):
        b = b"\x00" + up + qop(4, bytes([0, 0, 0, 0, 0, st << 5, 0, 0, 0, 0, 0]))
        for k in range(6):
            b += q_pkt(E.tx(1)) + q_time(20000)
        out.append(b)
    out += quic_conn_gaps(up)
    out += quic_conn_ring(up, graft)
    # ⭐ wait-verdict refused WITHOUT PAM (banned, a full table: op 4 a2 bit 5) is evictable,
    #    the one PAM judges is not: a full server of both, then newcomers
    for v6 in (0, 1):
        b = bytes([v6])
        for k in range(6):
            b += q_new(addr=k % 3, events=E.tx(0) + E.tx(1), dcid=k)
            b += qop(4, bytes([0, 0, 0x20 if k % 2 else 0, 0, 0, 3 << 5, 0, 0, 0, 0, 0]), k)
        b += q_new(addr=3) + q_new(addr=3, dcid=9) + q_new(addr=3, dcid=10) + q_new(addr=3, dcid=11)
        out.append(b)
    # ⭐ single-use Retry tokens (15 Oct 2026): a connection dies (a protocol error, or
    #    evicted on a full server), and its Initial comes again with the same token —
    #    within the 10 s (INVALID_TOKEN, no connection) and after them
    for gap in (0, 5000, 11000):
        out.append(b"\x00" + q_new(events=E.tx(0) + E.tx(1)) + q_pkt(E.end(3)) + qop(7)
                   + q_time(gap) + q_new(token=0x42, events=E.tx(0) + E.tx(1)))
    b = b"\x00" + qop(12, bytes([3, 3, 3, 3]))
    for k in range(3):
        b += q_new(addr=k, events=E.tx(0) + E.tx(1), dcid=k)
    b += q_new(addr=3, events=E.tx(0) + E.tx(1)) + q_new(addr=3, token=0x42)
    out.append(b)
    # and a churn: twelve connections born in one second (the «new connection» lines)
    out.append(b"\x00" + qop(12, bytes([19, 19, 9, 9])) + b"".join(
        q_new(addr=k % 4, events=E.tx(0) + E.tx(1), dcid=k) + q_pkt(E.end(3), sel=0) + qop(7)
        for k in range(12)))
    if not graft:
        out += [
            # ⭐ migration (b207ad85): NAT rebinding, a new network, a probe, a failed validation
            b"\x00" + up + q_pkt(b"", addr=1) + q_pkt(E.data(0, b"moved"), addr=2)
            + q_pkt(E.path_result(True)) + qop(7),
            # ⭐ a SUCCESSFUL migration: a packet from a new remote, the validation succeeds (path_result(True)),
            #    then traffic on the new path; then the same remote on ANOTHER local address and a second success
            b"\x00" + up + q_pkt(b"", addr=2) + q_pkt(E.path_result(True)) + q_pkt(E.data(0, b"after"), addr=2)
            + q_pkt(b"", addr=2, local=1) + q_pkt(E.path_result(True)) + qop(7),
            b"\x00" + up + q_pkt(b"", addr=2, flags=0x40) + qop(9, bytes([1, 0, 0, 0, 0, 0, 0]))
            + qop(7) + q_pkt(b"", addr=2, local=1) + q_pkt(E.end(3), addr=3),
            b"\x01" + up2 + q_pkt(b"", sel=1, addr=1) + q_pkt(b"", sel=1, addr=3) + qop(7),
            b"\x00" + q_new(events=E.tx(0) + E.tx(1)) + q_pkt(b"", addr=2),  # during the handshake
        ]
    return out

def q_wt(sel, st, pkts=0, beat=False):
    """Op 4: the played `wt` of `sel` in RCP state `st` (`RXQ_STATE_NAMES`), `pkts` to write,
    and no heartbeat unless `beat` (a5 bit 4)."""
    return qop(4, bytes([0, 0, pkts, 4, 176, (st << 5) | (0 if beat else 16), 0, 0, 0, 0, 0]), sel)

def q_limits(conns, pending, per_addr, per_48):
    return qop(12, bytes([conns, pending, per_addr, per_48]))

def q_burst(count, addr=0, gap_ms=0, rand_fails=False, vn=False, extra=0):
    return qop(13, bytes([count - 1, addr, gap_ms, int(rand_fails) | (int(vn) << 1), extra]))

def q_flood(count, step_10us=0, addr=0):
    """Op 14: `count` Retry-validated births, each dead at once, `step_10us` × 10 µs apart."""
    return qop(14, struct.pack("!H", count - 1) + bytes([step_10us, addr]))

def q_replay(last=False, addr=0, events=b""):
    """Op 0 with a2 bit 7: the first (or last) flood birth's Initial again, dcid and token."""
    return q_new(addr=addr, dcid=int(last), token=0x80, events=events)

def q_sock(fails=0, errno_i=0, recv=0, no_pktinfo=False, gsn_fail=False, refuse=0, einval=False):
    """Op 8; `refuse`: the kernel refuses the forced source of the next `refuse` sends
    (EINVAL or EADDRNOTAVAIL)."""
    return qop(8, bytes([fails | (errno_i << 3), recv, int(no_pktinfo) | (int(gsn_fail) << 1),
                         refuse | (int(einval) << 3)]))

def quic_conn_ring(up, graft):
    """⭐ The second coverage run of 15 Oct 2026 (transport.c ~1157 and ~717-730):
       · the ring of used Retry tokens (d0e56764, TOKENS_KEPT = 4096): 4097 births within 10 s
         push the first token out early — counted, in the summary line, and its Initial again
         may make a second connection; the last one's again is still INVALID_TOKEN; at
         2.44 ms apart the 4097th is born 9.99 s after the first (forgotten), at 2.45 ms
         10.04 s after (its 10 s were over: nothing forgotten);
       · a link-local local address (fe80::1, ifindex 3): the answers leave from it ON its
         interface (IPV6_PKTINFO's ifindex);
       · the kernel refusing the source address (EINVAL / EADDRNOTAVAIL): the packet goes
         again without it — for a connection's packets, a Retry, a Stateless Reset."""
    E = Ev
    tx = E.tx(0) + E.tx(1)
    out = [
        b"\x00" + q_flood(4097, 20) + q_replay(events=tx) + q_replay(last=True, events=tx)
        + q_time(10001) + qop(11),
        b"\x01" + q_flood(4097, 244, addr=2) + q_replay(addr=2, events=tx) + q_time(10001),
        b"\x00" + q_flood(4097, 245, addr=3) + q_replay(addr=3, events=tx) + q_time(10001),
        b"\x00" + up + q_flood(2048, 5, addr=1) + q_time(3) + q_new(addr=2, events=tx, dcid=9)
        + q_flood(2050, 5, addr=2) + q_replay(addr=1, events=tx)
        + q_replay(last=True, addr=2, events=tx) + q_time(5000) + q_time(5001),
    ]
    for v6 in (0, 1):
        c = bytes([v6])
        # born and living on the third local address (IPv6: link-local)
        out.append(c + q_new(local=2, events=tx)
                   + q_pkt(E.HS + E.new_cid(2), long=True, cid=0, local=2)
                   + q_pkt(E.data(0, b"\x01\x04CONNECT") + E.dgram(b"\x04\x01" + bytes(14)),
                           local=2)
                   + qop(7) + q_time(100) + q_burst(3, addr=1))
        # the kernel refuses the source: a connection's packets (EADDRNOTAVAIL, then an EINTR
        # on the packet sent again), a Retry (EINVAL), Stateless Resets
        out.append(c + up + q_sock(refuse=3) + q_pkt(E.data(0, b"x") + E.max_bidi(5))
                   + qop(7) + q_time(10))
        # five refusals in one input: the 4th and 5th are not written (the 1st-3rd and every
        # 256th of the process are)
        out.append(c + up + q_sock(refuse=5)
                   + b"".join(q_pkt(E.data(0, b"x")) + qop(7) for _ in range(6)))
        out.append(c + q_sock(fails=1, errno_i=1, refuse=2, einval=True) + up
                   + q_pkt(E.data(0, b"x")))
        out.append(c + q_sock(refuse=1, einval=True) + q_new(token=0x10)
                   + q_sock(refuse=2) + q_burst(2, addr=3))
        # with no PKTINFO nothing is forced, so nothing is refused
        out.append(c + q_sock(no_pktinfo=True, refuse=7) + up + q_pkt(b"") + qop(7))
    if not graft:
        # the local end MOVES to the link-local address, and back (a migration of the local end)
        out.append(b"\x01" + up + q_pkt(b"", local=2) + qop(7) + q_sock(refuse=1)
                   + q_pkt(b"", local=0) + qop(7))
    return out

def quic_conn_gaps(up):
    """⭐ The gaps of the coverage run of 15 Oct 2026 (transport.c), each with its oracle:
       a logged-in or wait-verdict connection never evicted, the age close only for one not
       logged in, the 100 resets per second, `transport_wait_ms()` never past an age deadline.
       States: 0 none · 1 hello · 2 credentials · 3 verdict · 4 attach · 5 active · 6 finished
       · 7 detached-by-silence."""
    E = Ev
    tx = E.tx(0) + E.tx(1)
    out = []
    for v6 in (0, 1):
        c = bytes([v6])
        # a LOGGED-IN connection in the list of a full server (6 / 5 / 3 / 4): it is walked by
        # the victim's choice and never chosen; then the six again with every unlogged one in
        # wait-verdict and one detached: nobody evictable, the newcomer is refused
        b = c + q_new(addr=0, events=tx, dcid=0) + q_wt(0, 5) + q_time(1)
        for k, a in enumerate((2, 3, 0, 2, 3)):
            b += q_new(addr=a, events=tx, dcid=k + 1)
        b += q_new(addr=0, events=tx, dcid=7) + q_time(1)
        out.append(b)
        b = c + q_new(addr=0, events=tx, dcid=0) + q_wt(0, 5) + q_time(1)
        for k, a in enumerate((2, 3, 0, 2, 3)):
            b += q_new(addr=a, events=tx, dcid=k + 1) + q_wt(k + 1, 3 if k < 4 else 7)
        b += q_new(addr=2, events=tx, dcid=7) + q_time(1) + q_new(addr=3, events=tx, dcid=8)
        out.append(b)
        # two newcomers in ONE read round on a full server: the second walks the first's
        # victim, already closed (dead) and not yet reaped
        b = c + q_limits(6, 6, 3, 9)
        for k, a in enumerate((0, 2, 3, 0, 2, 3)):
            b += q_new(addr=a, events=tx, dcid=k) + q_wt(k, (0, 1, 2, 6, 1, 2)[k])
        b += q_new(addr=2, events=tx, dcid=9, hold=1) + q_new(addr=3, events=tx, dcid=10, hold=1)
        b += qop(10) + q_new(addr=0, events=tx, dcid=11, hold=1) + qop(10)
        out.append(b)
        # the caps LOWERED under what is open: a victim exists, one is not enough
        b = c
        for k, a in enumerate((0, 2, 3, 0, 2)):
            b += q_new(addr=a, events=tx, dcid=k)
        b += q_limits(2, 2, 3, 4) + q_new(addr=3, events=tx, dcid=6) + q_limits(2, 1, 1, 1) \
            + q_new(addr=1, events=tx, dcid=7)
        out.append(b)
    # the AGE deadline as the next timer: no heartbeat, nothing to write, packets every 20 s
    # keep the idle timer (30 s) past born + 90 s; in every state (attach, active, detached:
    # logged in, never aged)
    for st in range(8):
        b = b"\x00" + up + q_wt(0, st)
        for _ in range(4):
            b += q_pkt(E.tx(1)) + q_time(20000)
        b += q_pkt(E.tx(1)) + q_time(1) + qop(11) + q_time(9000) + qop(11) + q_time(998) \
            + qop(11) + q_time(1) + q_time(1) + qop(11)
        out.append(b)
    # the refusal line as the next timer (two refusals inside REFUSAL_LOG_S)
    b = b"\x00"
    for k in range(3):
        b += q_new(addr=0, events=tx, dcid=k) + q_wt(k, 1)
    b += q_new(addr=1, events=tx, dcid=4) + q_new(addr=0, events=tx, dcid=5) + q_time(1) + qop(11)
    out.append(b)
    b = b"\x01"  # the same with the IPv6 /48 full (remotes 0 and 2 share it, not their /64)
    for k, a in enumerate((0, 2, 0, 2)):
        b += q_new(addr=a, events=tx, dcid=k) + q_wt(k, 2)
    b += q_new(addr=2, events=tx, dcid=5) + q_new(addr=0, events=tx, dcid=6) + q_time(1) + qop(11)
    out.append(b)
    # STATELESS RESETS: 150 in one second (100 go out), then across seconds, a RAND failure;
    # version negotiation, and its RAND failure
    out += [
        b"\x00" + q_burst(150) + q_burst(10, rand_fails=True),
        b"\x01" + q_burst(160, addr=1, gap_ms=7, extra=9),
        b"\x00" + up + q_burst(120, addr=2, gap_ms=1) + q_time(1000) + q_burst(105, addr=3),
        b"\x00" + q_burst(3, vn=True) + q_burst(2, vn=True, rand_fails=True),
        b"\x01" + q_burst(2, addr=3, vn=True) + q_burst(2, addr=1, rand_fails=True),
    ]
    return out


def main(out):
    d = os.path.join(out, "quic-conn")
    os.makedirs(d, exist_ok=True)
    for i, b in enumerate(quic_conn()):
        with open(os.path.join(d, "seed-%02d" % i), "wb") as fh:
            fh.write(b)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "seeds"))
