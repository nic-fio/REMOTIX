#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_seeds.py — the seed corpus of the `rcp-msg` fuzz target.

    python3 gen_seeds.py <out-dir>       → <out-dir>/rcp-msg/seed-NN

A seed = byte 0 (configuration, see fuzz_rcp_msg.c) + ops `op, u16 length, argument` (common.h).
Wire format of RCP (src/rcp.c): u16 type · u32 body length, big-endian; strings = u16 length + bytes.
"""
import os
import struct
import sys

def op(n, arg=b""):
    return bytes([n]) + struct.pack("!H", len(arg)) + arg

def msg(kind, body=b""):
    return struct.pack("!HI", kind, len(body)) + body

def s(x):
    x = x.encode() if isinstance(x, str) else x
    return struct.pack("!H", len(x)) + x

def hello(extra=()):
    caps = [("video.codec", "h264"), ("video.depth", "8"), ("audio.codec", "pcm"),
            ("clipboard.text", "yes"), ("video.max_size", "3840x2160"), ("video.level", "5.1"),
            ("client.name", "fuzz")] + list(extra)
    b = struct.pack("!HH", 1, len(caps))
    for k, v in caps:
        b += s(k) + s(v)
    return msg(0x0001, b)

def cred(u="user", p="pw1"):
    return msg(0x0003, s(u) + s(p))

def attach(w=1920, h=1080, lay="it"):
    return msg(0x0006, struct.pack("!IIII", w, h, w, h) + s(lay))

def T(ms):
    return op(3, struct.pack("!I", ms))

def input_msg(kind, idn, fields):
    return msg(kind, struct.pack("!IQ", idn, idn * 16) + fields)

def inp(stream, m):
    return op(1, bytes([stream]) + m)

def clip(stream, m, fin=0):
    return op(2, bytes([stream, fin]) + m)

def pointer(i, x=100, y=100): return input_msg(0x0101, i, struct.pack("!II", x, y))
def button(i, c=1, p=1): return input_msg(0x0102, i, struct.pack("!HB", c, p))
def wheel(i, x=0, y=-120): return input_msg(0x0103, i, struct.pack("!ii", x, y))
def letter(i, c=0x41): return input_msg(0x0104, i, struct.pack("!I", c))
def keypos(i, c=30, p=1): return input_msg(0x0105, i, struct.pack("!HB", c, p))

# byte 0: configuration, bit0 ask_verify · bit1 clipboard · bit2 input · bit3 stage_canvas
# byte 1: the failure mask (which hooks answer «no», see fuzz_rcp_msg.c; op 13 changes it)
CFG = 0b0111
def prologue(cfg=CFG, att=None, fail=0):
    # HELLO · CREDENTIALS · PAM says yes · the fixed second passes · ATTACH
    return bytes([cfg, fail]) + op(0, hello()) + op(0, cred()) + op(4, b"\x01") + T(1500) + op(0, att or attach())

seeds = []
seeds.append(prologue())
seeds.append(prologue() + inp(0, pointer(1) + button(2) + wheel(3) + letter(4) + keypos(5)))
# the same bytes in dribbles: the control channel in two halves
a = hello()
seeds.append(bytes([CFG, 0]) + op(0, a[:7]) + op(0, a[7:]) + op(0, cred()) + op(4, b"\x01") + T(1500) + op(0, attach()))
# clipboard: client announces, session pastes (ask), client sends the text
seeds.append(prologue() + clip(0, msg(0x0201, struct.pack("!II", 1, 5))) + op(9, struct.pack("!I", 7))
             + clip(4, msg(0x0203, struct.pack("!I", 1) + b"hello")))
# the session copies, the client asks for it
seeds.append(prologue() + op(8, b"copied text") + clip(8, msg(0x0202, struct.pack("!I", 1))))
# the declared length beyond the data: a clipboard text cut in two streams' pieces
seeds.append(prologue() + clip(0, msg(0x0201, struct.pack("!II", 1, 4)))
             + op(9, struct.pack("!I", 1)) + clip(4, msg(0x0203, struct.pack("!I", 1) + b"abcd")[:8], 0)
             + clip(4, b"cd", 1))
# control messages once active
seeds.append(prologue() + op(0, msg(0x000D, struct.pack("!I", 0))) + op(0, msg(0x000B, struct.pack("!II", 1280, 720)))
             + op(0, msg(0x0008, struct.pack("!II", 800, 600))) + op(0, msg(0x0009, b"")))
seeds.append(prologue() + op(0, msg(0x0011)))                       # TERMINATE_SESSION
seeds.append(prologue() + op(0, msg(0x000C, bytes([1]) + s("bye"))))  # FAREWELL
# wrong password: synchronous verify (no ask_verify) and a refused verdict
seeds.append(bytes([0b0110, 0]) + op(0, hello()) + op(0, cred("u", "pw0")) + T(1500))
seeds.append(bytes([CFG, 0]) + op(0, hello()) + op(0, cred()) + op(4, b"\x00") + T(1500))
# silence, the slot left and taken back; the second session
seeds.append(prologue() + T(40000) + op(0, msg(0x000D, struct.pack("!I", 0))) + op(15) + op(0, hello()))
# a very large declared length, and a header only
seeds.append(bytes([CFG, 0]) + op(0, struct.pack("!HI", 0x0001, 0x000FFFFA)))
seeds.append(bytes([CFG, 0]) + op(0, struct.pack("!HI", 0x0001, 0xFFFFFFFF)))
# clipboard: announcement with the cap, and the announced text length mismatching
seeds.append(prologue() + clip(0, msg(0x0201, struct.pack("!II", 1, 1000000))))
seeds.append(prologue() + clip(0, struct.pack("!HI", 0x0203, 1000004)))
# the session copies while a paste is waiting, announce arrives during the backlog
seeds.append(prologue() + op(8, b"x") + op(9, struct.pack("!I", 1)) + op(9, struct.pack("!I", 2))
             + clip(0, msg(0x0201, struct.pack("!II", 2, 3))) + op(13, b"\x01" + msg(0x0201, struct.pack("!II", 3, 1))))

def setfail(m): return op(13, struct.pack("!H", m))
def vopen(key=1, length=100, ins=0, piece=b""):
    return op(16, bytes([key]) + struct.pack("!H", length) + struct.pack("!I", 1234) + struct.pack("!I", ins) + piece)

# the failure paths of the hooks (mask bits: see fuzz_rcp_msg.c)
seeds.append(prologue(fail=0x01))                                            # ask_verify fails: REJECTED, not a failed attempt
seeds.append(prologue(fail=0x04) + inp(0, pointer(1) + button(2) + letter(3) + wheel(4)))   # input answers -1
seeds.append(prologue(fail=0x08) + inp(0, letter(1)))                       # a letter the layout cannot produce
seeds.append(prologue(fail=0x10) + op(0, msg(0x000B, struct.pack("!II", 1280, 720))))    # recanvas fails
seeds.append(bytes([CFG, 0x20]) + op(0, hello()) + op(0, cred()) + op(4, b"\x01") + T(1500) + op(0, attach()))  # layout fails
seeds.append(prologue(fail=0x40) + op(8, b"copied") + clip(8, msg(0x0202, struct.pack("!I", 1))))   # clipboard_write fails
seeds.append(prologue(fail=0x80) + clip(0, msg(0x0201, struct.pack("!II", 1, 5))))                    # clipboard_offer fails
seeds.append(prologue(fail=0x80) + op(9, struct.pack("!I", 1)) + clip(0, msg(0x0201, struct.pack("!II", 1, 5)))
             + clip(4, msg(0x0203, struct.pack("!I", 1) + b"hello")) + setfail(0))       # the postponed offer fails
seeds.append(prologue() + op(8, b"ab\x00cd") + clip(8, msg(0x0202, struct.pack("!I", 1))))           # a NUL inside the session's text
# the video path of the server: a frame written whole, one that breaks, one over the ceiling
seeds.append(prologue() + vopen(1, 4, 1, b"abcd") + op(18))
seeds.append(prologue(fail=0x02) + vopen(1, 8, 1, b"abcd") + op(17, b"efgh") + op(18))     # video_write fails
seeds.append(prologue() + op(16, bytes([3]) + b"\x00\x10" + b"\0" * 8))                    # 17 MiB declared
seeds.append(prologue() + op(19, b"\x01" + b"frame") + op(20, b"\x01\x00\x00\x00\x05"))

if __name__ == "__main__":
    out = os.path.join(sys.argv[1], "rcp-msg")
    os.makedirs(out, exist_ok=True)
    for i, d in enumerate(seeds):
        with open(os.path.join(out, "seed-%02d" % i), "wb") as f:
            f.write(d)
    print("%d seeds in %s" % (len(seeds), out))
