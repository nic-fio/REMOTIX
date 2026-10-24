#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_seeds.py — the seed corpus of the `page` fuzz target.   python3 gen_seeds.py <out-dir>  → <out-dir>/page/seed-NN
A seed = byte 0 (configuration: bit 0 the page is ~200 KB · bit 1 TCP_INFO unavailable · bit 2 every connection trickles one byte at
a time) + ops `op, u16 length (big-endian), argument` (common.h); the ops are described in the header of fuzz_page.c.
"""
import os
import struct
import sys

def op(n, *args):
    a = b"".join(args)
    return bytes([n]) + struct.pack("!H", len(a)) + a

def connect(pal=0, hs=0, hello=1, half=0, rchunk=0, canned=1, extra=b""):
    return op(0, bytes([pal, hs | (hello << 3) | (half << 4), rchunk, canned]), extra)
def send(which=0, hello=0, half=0, data=b""):
    return op(1, bytes([which, hello | (half << 1)]), data)
def move(flags=0): return op(2, bytes([flags]))
def time_ms(ms, seconds=False): return op(3, struct.pack("!H", ms), bytes([1 if seconds else 0]))
def ack(which=0, n=0xFFFFFFFF): return op(4, bytes([which]), struct.pack("!I", n))
def window(which=0, n=0xFFFFFFFF, piece=0): return op(5, bytes([which]), struct.pack("!I", n), bytes([piece]))
def knob(alloc=0, accept=0, tcp=0, sslnew=0, banned=0, rnd=0, name=0, rotate=0):
    return op(6, bytes([alloc, accept, tcp, sslnew]), struct.pack("!H", banned), bytes([rnd, name, rotate]))
def peer(which=0): return op(7, bytes([which]))
def burst(n=1, pal=0, bits=0): return op(8, bytes([n - 1, pal, bits]))
def finish(moves=1): return op(9, bytes([0, moves - 1]))

seeds = []
def seed(cfg, *ops): seeds.append(bytes([cfg]) + b"".join(ops))

# a whole life: connect, accept, read, answer, drain
seed(0, connect(), move(), move(), window(), ack(), move(), finish(2))
seed(0, connect(canned=2), move(), move(), window(), move(), ack(), move(), finish(2))            # gzip
seed(0, connect(canned=3), move(), move(), finish(3))                                              # /fingerprint
seed(4, connect(canned=1), move(), move(), move(), move(), finish(3))                              # trickle
seed(0, connect(canned=5), move(), move(), finish(3))                                              # two requests pipelined
for canned in (4, 6, 7, 8, 9, 10, 11, 12, 13, 14):
    seed(0, connect(canned=canned), move(), move(), finish(3))
seed(0, connect(canned=2, rchunk=3), move(), move(), move(), finish(3))                            # gzip, small reads
# the handshake modes: wants a write, fails, partial hello, replied-never-done
for hs in (1, 2, 3, 4):
    seed(0, connect(hs=hs), move(), move(), move(), finish(2), time_ms(12, True))
seed(0, connect(hs=0, hello=0), move(), time_ms(2, True), send(0, hello=1, data=b"GET / HTTP/1.1\r\n\r\n"), move(), move(), finish(3))
# slow writers on the big page: a small window, tiny acks, then time
seed(1, connect(canned=2), move(), move(), window(0, 3000), move(), ack(0, 1000), time_ms(30, True), move(), ack(0, 2000), time_ms(40, True))
seed(1, connect(canned=1), move(), move(), window(0, 20000, 8), move(), time_ms(25, True), move(), window(0), ack(), move())
seed(3, connect(canned=1), move(), move(), window(0, 5000), move(), time_ms(70, True))          # TCP_INFO unavailable
seed(1, knob(tcp=1), connect(canned=1), move(), move(), window(0, 9000), move(), time_ms(30, True))
seed(1, knob(tcp=2), connect(canned=1), move(), move(), window(0, 9000), move(), time_ms(30, True))
seed(1, knob(tcp=3), connect(canned=1), move(), move(), window(0, 9000), ack(), move(), time_ms(30, True))
# the caps: one address, one /64, one /48, the accept rate, the table
seed(0, burst(10, 0, 3), time_ms(4, True), move())
seed(0, burst(12, 4, 3 | 1), time_ms(4, True), burst(8, 5, 3))                                    # IPv6 /48
seed(0, burst(64, 0, 2), burst(64, 3, 2), burst(64, 4, 6), move(), time_ms(2, True), move())       # fill the table, evictions
seed(0, burst(40, 0, 0), time_ms(3, True), move(), time_ms(5, True), move())                      # parked, 503
seed(0, burst(64, 2, 2), burst(64, 7, 6), burst(40, 9, 2), connect(pal=3), move(), move())
# banned visitors, with and without gzip
seed(0, knob(banned=0xFFFF), connect(canned=1), connect(pal=3, canned=2), move(), move(), finish(3))
seed(1, knob(banned=0xFFFF), connect(canned=2), move(), move(), window(), move(), time_ms(15, True), connect(canned=2), move(), finish(3))
# the certificate rotates between requests; allocations fail; accept errors; SSL_new fails; RAND fails
seed(0, connect(canned=2), move(), move(), finish(2), knob(rotate=1), connect(canned=2), move(), move(), finish(2))
for k in (1, 2, 3, 5, 8, 12, 20):
    seed(0, knob(alloc=k), connect(canned=2), move(), move(), finish(3), time_ms(12, True))
seed(0, knob(accept=2), connect(), move(), knob(accept=0), move(), move(), finish(2))
seed(0, knob(sslnew=1), connect(), move(), move(), finish(2))
seed(0, knob(rnd=1), burst(64, 0, 2), burst(64, 2, 2), connect(pal=3), move(), move())
seed(0, knob(name=1), connect(), move(), move(), finish(2))
# peers that reset, close halfway, stop reading
seed(0, connect(canned=1), move(), move(), window(0, 100), peer(0), move(), move(), finish(2))
seed(0, connect(canned=1, half=1), move(), move(), finish(2))
seed(0, connect(canned=0), move(), send(0, 1, 1, b"GET / HT"), move(), move(), finish(2))
seed(0, connect(canned=1), move(4), move(16), move(1), move(2), move(8), finish(2))                # spurious events, reused descriptors
if __name__ == "__main__":
    out = os.path.join(sys.argv[1], "page")
    os.makedirs(out, exist_ok=True)
    for i, d in enumerate(seeds):
        with open(os.path.join(out, "seed-%02d" % i), "wb") as f:
            f.write(d)
    print("%d seeds in %s" % (len(seeds), out))
