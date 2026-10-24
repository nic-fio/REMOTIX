#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_seeds.py — the seed corpus of the `child-msg` fuzz target.   python3 gen_seeds.py <out-dir>  → <out-dir>/child-msg/seed-NN
A seed = byte 0 (configuration, see fuzz_child_msg.c) + ops `op, u16 length (big-endian), argument` (common.h).
Op 0 MESSAGE: a0-1 = type (u16 LE), then the body as child.c's structs lay it out (native little-endian, no padding games:
the structs are naturally aligned).  Op 1 PIECES: the child cutting a big message.  Op 2 NEWCHILD.
"""
import os
import struct
import sys

FRAME, CURSOR, CANVAS, FINISHED, BLOCK, CLIP, CLIPREQ, INTRO, STAGE = 12, 13, 14, 15, 16, 17, 18, 10, 11

def op(n, arg=b""):
    return bytes([n]) + struct.pack("!H", len(arg)) + arg

def msg(kind, body=b""):
    return op(0, struct.pack("<H", kind) + body)

def pieces(kind, total, piece, count, bits=0, codec=1, w=1920, h=1080):
    return op(1, bytes([kind]) + struct.pack("<IHBB", total, piece, count, bits) + bytes([codec]) + struct.pack("<HH", w, h))

ALL = 0b01111111   # every hook connected, the child not yet showed_up
seeds = []
def seed(cfg, *ops): seeds.append(bytes([cfg]) + b"".join(ops))

# whole messages
whoami = struct.pack("<11I", 1000, 1000, 1000, 1000, 1000, 1000, 1, 1, 5, 1, 1) + b"fuzz".ljust(64, b"\0") + b"/run/user/1000".ljust(160, b"\0")
seed(ALL | 128, msg(INTRO, whoami))
seed(ALL, msg(INTRO, whoami), msg(INTRO, whoami))
seed(ALL, msg(INTRO, struct.pack("<11I", 1, 1, 1, 1, 1, 1, 1, 1, 5, 1, 1) + b"\0" * 224))   # a uid that is not the stamped one
seed(ALL, msg(STAGE, struct.pack("<10I", 1, 0, 1, 0, 0, 1920, 1080, 7680, 32, 2) + b"HDMI".ljust(64, b"\0") + b"".ljust(224, b"\0")))
seed(ALL, msg(CANVAS, struct.pack("<5I", 1920, 1080, 1912, 1044, 0)), msg(CANVAS, struct.pack("<5I", 1920, 1080, 0, 0, 1)))
seed(ALL, msg(FINISHED))
seed(ALL, msg(CLIPREQ, struct.pack("<HHIII", 0, 0, 0, 0, 7)[:20].ljust(16, b"\0")))
seed(ALL & ~1, msg(CLIPREQ, b"\0" * 16))                                  # nobody serves the clipboard: «I don't have it»
seed(ALL, msg(BLOCK, struct.pack("<B3xIQ", 1, 5, 99) + b"abcde"), msg(BLOCK, struct.pack("<B3xIQ", 9, 1, 0) + b"z"))
# the child cutting big messages
seed(ALL, pieces(0, 100000, 32768, 4))                                    # a frame in four pieces, delivered
seed(ALL, pieces(0, 70000, 32768, 6, bits=1))                             # a hole
seed(ALL, pieces(0, 70000, 32768, 6, bits=4))                             # the codec changes midway
seed(ALL, pieces(0, 16777217, 100, 1))                                    # over the 16 MiB cap
seed(ALL, pieces(0, 16777216, 32768, 3))                                  # at the cap
seed(ALL, pieces(0, 9000, 32769, 1))                                      # a piece over MAX_PIECE
seed(ALL, pieces(1, 4 * 64 * 64, 4096, 4, w=64, h=64))                    # a cursor 64x64
seed(ALL, pieces(1, 4 * 256 * 256, 32768, 8, w=256, h=256))               # the cursor's cap
seed(ALL, pieces(1, 4 * 256 * 256 + 1, 100, 1))
seed(ALL, pieces(1, 0, 0, 1, w=0, h=0))                                   # hidden
seed(ALL, pieces(2, 1000000, 32768, 31))                                  # the clipboard at its cap
seed(ALL, pieces(2, 1000001, 100, 1))
seed(ALL, pieces(2, 70000, 32768, 4, bits=8))                             # pieces at offset 0 each time
seed(ALL, pieces(2, 10, 5, 2), pieces(2, 10, 5, 2, bits=1))               # a text then a hole
seed(ALL, pieces(2, 0, 0, 1))                                             # the clipboard emptied
seed(ALL, pieces(3, 200, 200, 1, codec=2), pieces(3, 5, 5, 1, codec=0))
seed(ALL, pieces(0, 70000, 32768, 3), op(2, b"\0"), pieces(0, 70000, 32768, 3))   # the child dies half way
seed(ALL, pieces(0, 5, 5, 1, bits=16))

if __name__ == "__main__":
    out = os.path.join(sys.argv[1], "child-msg")
    os.makedirs(out, exist_ok=True)
    for i, d in enumerate(seeds):
        with open(os.path.join(out, "seed-%02d" % i), "wb") as f:
            f.write(d)
    print("%d seeds in %s" % (len(seeds), out))
