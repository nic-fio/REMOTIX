#!/usr/bin/env python3
"""t9-rete.py — phase 17, T9 (R22): what the "no network" VM sent.

    python3 t9-rete.py rete.pcap [DAL HH:MM:SS AL HH:MM:SS]

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
dal = al = None
if len(sys.argv) >= 6:
    dal, al = sys.argv[3], sys.argv[5]
if len(b) < 24:
    print("empty capture")
    sys.exit()
e = "<" if b[:4] == b"\xd4\xc3\xb2\xa1" else ">"
i, n = 24, 0
entrata = collections.Counter()
tentativi = {}
ospite = None
while i + 16 <= len(b):
    ts, us, incl, _ = struct.unpack(e + "IIII", b[i:i + 16])
    i += 16
    f = b[i:i + incl]
    i += incl
    n += 1
    if len(f) < 14:
        continue
    src = f[6:12].hex(":")
    tipo = struct.unpack(">H", f[12:14])[0]
    if ospite is None and src.startswith("52:54:00:12"):
        ospite = src
    dalla_vm = src == ospite
    ora = time.strftime("%H:%M:%S", time.gmtime(ts))
    chiave = None
    p = f[14:]
    if tipo == 0x0800 and len(p) >= 20:
        ihl = (p[0] & 15) * 4
        proto = p[9]
        s, d = ".".join(map(str, p[12:16])), ".".join(map(str, p[16:20]))
        sp = dp = 0
        if proto in (6, 17) and len(p) >= ihl + 4:
            sp, dp = struct.unpack(">HH", p[ihl:ihl + 4])
        if proto == 6:
            flag = p[ihl + 13] if len(p) > ihl + 13 else 0
            servizio = sp if dalla_vm else dp
            if servizio in (22, 7447):
                entrata["TCP %d (bench forward)" % servizio] += 1
                continue
            if dalla_vm and flag & 0x02 and not flag & 0x10:
                chiave = "TCP %s → %s:%d" % (s, d, dp)
            elif dalla_vm:
                chiave = "TCP %s → %s:%d (follow-up)" % (s, d, dp)
            else:
                entrata["TCP from %s:%d" % (s, sp)] += 1
                continue
        elif proto == 17:
            if (dalla_vm and sp == 7447) or (not dalla_vm and dp == 7447):
                entrata["UDP 7447 (bench forward, QUIC)"] += 1
                continue
            if not dalla_vm:
                entrata["UDP from %s:%d" % (s, sp)] += 1
                continue
            chiave = "UDP %s:%d → %s:%d" % (s, sp, d, dp)
        else:
            if not dalla_vm:
                continue
            chiave = "IP proto %d %s → %s" % (proto, s, d)
    elif dalla_vm:
        chiave = {0x0806: "ARP", 0x86DD: "IPv6 (neighbour, multicast)"}.get(tipo, "ethertype %04x" % tipo)
    if chiave:
        t = tentativi.setdefault(chiave, [ora, ora, 0])
        t[1] = ora
        t[2] += 1

print("%d packets on the VM's interface (MAC %s)" % (n, ospite))
print("INCOMING (the bench's forwards, and the VM's replies):")
for k, c in entrata.most_common():
    print("  %7d  %s" % (c, k))
print("STARTED by the VM (first · last · packets):")
nella = []
for k, (a, z, c) in sorted(tentativi.items(), key=lambda x: x[1][0]):
    dentro = dal is not None and not (z < dal or a > al)
    if dentro:
        nella.append(k)
    print("  %s · %s  %6d  %s%s" % (a, z, c, k, "   ← in the installation window" if dentro else ""))
if dal is not None:
    fuori = [k for k in nella if not k.startswith(("ARP", "IPv6", "UDP 0.0.0.0:68"))
             and "224.0.0." not in k and "239.255." not in k and "255.255.255.255" not in k]
    print("installation window %s-%s UTC: %d attempts towards the outside%s" %
          (dal, al, len(fuori), (": " + "; ".join(fuori)) if fuori else " — NO network access"))
