#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_seeds.py — the seed corpus of the `rootside-dispatch` fuzz target.   python3 gen_seeds.py <out-dir>  → <out-dir>/rootside-dispatch/seed-NN
A seed = ops `op, u16 length (big-endian), argument` (common.h); the op stream of fuzz_rootside_dispatch.c (op & 7).
Moved here from the abandoned attempt's benches/runner/fuzz/gen_seeds.py (this tree has one folder per target).
"""
import os
import struct
import sys


def op(code, arg=b""):
    return struct.pack("!BH", code, len(arg)) + arg


def ms(n):  # the harnesses count time in units of 4 ms
    return struct.pack("!H", n // 4)


def rootside_dispatch():
    def req(kind, user=1, rhost=0, pick=0, idx=0, extra=b""):
        return op(1, bytes([kind, user, rhost, pick, idx]) + extra)

    def pam(idx=0, outcome=1):
        return op(2, bytes([idx, outcome]))

    def t(n):
        return op(3, struct.pack(">H", min(n // 16, 65535)))  # units of 16 ms

    hdr = struct.pack("<IHHQ", 0x31525852, 1, 2, 5)
    return [
        # the good road: AUTH anna, PAM yes, SPAWN with that grant, SIGNAL it, it dies
        req(0) + pam(0, 1) + req(1) + req(3, pick=0, idx=0, extra=b"\x02") + op(4, b"\x00"),
        # a grant from another address, a reused one, an expired one
        req(0, 1, 1) + pam(0, 1) + req(1, rhost=0) + req(1) + req(1) + req(0) + pam(0, 1) + t(31000)
        + req(1),
        # CLOSE_ORPHAN without and with logind's session, then a second child refused
        req(2, 3) + op(6, b"\x03\x01") + req(2, 3) + req(2, 3),
        # names refused before PAM: root, bruno (denied), nss (fails), an unknown
        req(0, 0) + req(0, 2) + req(0, 4) + op(1, b"\x00\x09"),
        # 25 AUTH at once: the bounds; then time, then more
        b"".join(req(0, 1 + i % 3) for i in range(25)) + t(1000) + req(0) + pam(3, 0) + pam(0, 3),
        # malformed: a short packet, a right header with the wrong length, wrong credentials,
        # a descriptor attached; then a new network side
        op(0, b"\x01abc") + op(5) + op(0, b"\x01" + hdr + bytes(10)) + op(5)
        + op(0, b"\x09" + hdr) + op(5) + op(0, b"\x21" + hdr) + op(5) + req(0),
        # the network side dies with a child alive: EOF grace, SIGTERM, SIGKILL (kids_hurry), a
        # new network side, CHILD_EXITED not sent to it
        req(0) + pam(0, 1) + req(1) + op(8) + op(10) + t(6000) + op(10) + t(6000) + op(10) + op(5)
        + op(4, b"\x00") + req(0),
        # sends that fail: a SPAWNED that cannot leave (the child killed), a CHILD_EXITED kept in
        # the outbox and flushed
        req(0) + pam(0, 1) + op(9, b"\x01") + req(1) + op(4, b"\x00") + req(0, 3) + pam(0, 1) + req(1)
        + op(9, b"\x03") + op(4, b"\x00") + op(10) + op(10),
        # lane 1's pre-release review: a grant of a dead network side, used by the next one
        req(0) + pam(0, 1) + op(8) + op(5) + req(1, pick=0, idx=0),
        # … and a SIGNAL by the next network side to the previous one's child
        req(0) + pam(0, 1) + req(1) + op(8) + op(5) + req(3, pick=0, idx=0, extra=b"\x02"),
        # births that fail, a full table
        req(0) + pam(0, 1) + op(7, b"\x01") + req(1) + b"".join(req(0, u) + pam(0, 1) + req(1)
        for u in (1, 3)) + op(4, b"\x00") + op(4, b"\x00"),
    ]

def main(out):
    d = os.path.join(out, "rootside-dispatch")
    os.makedirs(d, exist_ok=True)
    for i, b in enumerate(rootside_dispatch()):
        with open(os.path.join(d, "seed-%02d" % i), "wb") as fh:
            fh.write(b)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "seeds"))
