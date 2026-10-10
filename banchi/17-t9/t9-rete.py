#!/usr/bin/env python3
"""t9-rete.py — phase 17, T9 (R22): what the "no network" VM sent.

    python3 t9-rete.py net.pcap [DAL HH:MM:SS AL HH:MM:SS]

Reads the QEMU capture (filter-dump on the VM's interface, both directions) and separates:
  - what COMES IN through the bench's forwards (ssh on 22, REMOTIX on 7447) and its replies;
  - the attempts the VM STARTS by itself: a TCP SYN, a UDP datagram that is not a reply
    (source port other than 7447), ARP, DHCP, multicast; with the time (UTC) of the first and the last.
With DAL/AL (UTC) it says which attempts fall in the installation window: the proof of R22 is that
there are NONE towards the outside there (restrict=on would drop them anyway: here we see whether there are any).
"""
import collections
import struct
import sys
import time

b = open(sys.argv[1], "rb").read()
from_ = al = None
if len(sys.argv) >= 6:
    from_, al = sys.argv[3], sys.argv[5]
if len(b) < 24:
    print("empty capture")
    sys.exit()
e = "<" if b[:4] == b"\xd4\xc3\xb2\xa1" else ">"
i, n = 24, 0
entry = collections.Counter()
attempts = {}
guest = None
while i + 16 <= len(b):
    ts, us, incl, _ = struct.unpack(e + "IIII", b[i:i + 16])
    i += 16
    f = b[i:i + incl]
    i += incl
    n += 1
    if len(f) < 14:
        continue
    src = f[6:12].hex(":")
    kind = struct.unpack(">H", f[12:14])[0]
    if guest is None and src.startswith("52:54:00:12"):
        guest = src
    from_vm = src == guest
    now = time.strftime("%H:%M:%S", time.gmtime(ts))
    key_id = None
    p = f[14:]
    if kind == 0x0800 and len(p) >= 20:
        ihl = (p[0] & 15) * 4
        proto = p[9]
        s, d = ".".join(map(str, p[12:16])), ".".join(map(str, p[16:20]))
        sp = dp = 0
        if proto in (6, 17) and len(p) >= ihl + 4:
            sp, dp = struct.unpack(">HH", p[ihl:ihl + 4])
        if proto == 6:
            flag = p[ihl + 13] if len(p) > ihl + 13 else 0
            service = sp if from_vm else dp
            if service in (22, 7447):
                entry["TCP %d (bench forward)" % service] += 1
                continue
            if from_vm and flag & 0x02 and not flag & 0x10:
                key_id = "TCP %s → %s:%d" % (s, d, dp)
            elif from_vm:
                key_id = "TCP %s → %s:%d (follow-up)" % (s, d, dp)
            else:
                entry["TCP from %s:%d" % (s, sp)] += 1
                continue
        elif proto == 17:
            if (from_vm and sp == 7447) or (not from_vm and dp == 7447):
                entry["UDP 7447 (bench forward, QUIC)"] += 1
                continue
            if not from_vm:
                entry["UDP from %s:%d" % (s, sp)] += 1
                continue
            key_id = "UDP %s:%d → %s:%d" % (s, sp, d, dp)
        else:
            if not from_vm:
                continue
            key_id = "IP proto %d %s → %s" % (proto, s, d)
    elif from_vm:
        key_id = {0x0806: "ARP", 0x86DD: "IPv6 (neighbour, multicast)"}.get(kind, "ethertype %04x" % kind)
    if key_id:
        t = attempts.setdefault(key_id, [now, now, 0])
        t[1] = now
        t[2] += 1

print("%d packets on the VM's interface (MAC %s)" % (n, guest))
print("INCOMING (the bench's forwards, and the VM's replies):")
for k, c in entry.most_common():
    print("  %7d  %s" % (c, k))
print("STARTED by the VM (first · last · packets):")
inside_of = []
for k, (a, z, c) in sorted(attempts.items(), key=lambda x: x[1][0]):
    inside = from_ is not None and not (z < from_ or a > al)
    if inside:
        inside_of.append(k)
    print("  %s · %s  %6d  %s%s" % (a, z, c, k, "   ← in the installation window" if inside else ""))
if from_ is not None:
    outside = [k for k in inside_of if not k.startswith(("ARP", "IPv6", "UDP 0.0.0.0:68"))
             and "224.0.0." not in k and "239.255." not in k and "255.255.255.255" not in k]
    print("installation window %s-%s UTC: %d attempts towards the outside%s" %
          (from_, al, len(outside), (": " + "; ".join(outside)) if outside else " — NO network access"))
