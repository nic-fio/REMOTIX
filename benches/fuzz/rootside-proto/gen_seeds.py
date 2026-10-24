#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_seeds.py — the seed corpus of the `rootside-proto` fuzz target.   python3 gen_seeds.py <out-dir>  → <out-dir>/rootside-proto/seed-NN
A seed = ops `op, u16 length (big-endian), argument` (common.h); the op stream of fuzz_rootside_proto.c (op & 7).
Moved here from the abandoned attempt's benches/runner/fuzz/gen_seeds.py (this tree has one folder per target).
"""
import os
import struct
import sys


def op(code, arg=b""):
    return struct.pack("!BH", code, len(arg)) + arg


def ms(n):  # the harnesses count time in units of 4 ms
    return struct.pack("!H", n // 4)


def rootside_proto():
    good = [op(1, bytes([k, 0]) + bytes(8)) for k in range(4)]          # the four requests, well formed
    return [
        b"".join(good),
        b"".join(op(1, bytes([k, m]) + bytes(8)) for k in range(11) for m in range(6)),
        op(0, b"\x01" + bytes(16)) + op(0, b"\x00" + bytes(64)),
        b"".join([op(2)] * 25) + op(6, ms(1000)) + b"".join([op(2)] * 12),   # the burst, then the rate
        b"".join([op(2), op(3)] * 20),
        op(4, b"nic\x00192.168.0.2") + op(5, b"\x00") + op(5, b"\x00"),        # single use
        op(4, b"nic\x00") + op(6, b"\x0e\xa6") + op(5, b"\x00"),               # 3750 × 8 = 30 s
        b"".join(op(4, b"u%d\x00h" % i) for i in range(40)) + b"".join(op(5, bytes([i])) for i in range(40)),
    ]

def main(out):
    d = os.path.join(out, "rootside-proto")
    os.makedirs(d, exist_ok=True)
    for i, b in enumerate(rootside_proto()):
        with open(os.path.join(d, "seed-%02d" % i), "wb") as fh:
            fh.write(b)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "seeds"))
