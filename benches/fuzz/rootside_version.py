#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rootside_version.py — the closed list's VERSION for the rootside-* fuzz targets, read from the contract (src/rootside_proto.h `#define RXR_VERSION n`)
and never typed again.  Repeatable: run it again after every RXR_VERSION bump.

  python3 rootside_version.py            print the version
  python3 rootside_version.py sync       rewrite the version bytes in rootside-proto/rootside-proto.dict and rootside-dispatch/rootside-dispatch.dict
                                         (the little-endian u16 after the magic «RXR1»); the seeds need no rewriting: gen_seeds.py of rootside-dispatch calls
                                         version() when it builds its header, and the rootside-proto seeds are ops that the harness turns into packets with RXR_VERSION.

(rilettura-fix: RXR_VERSION went 2 -> 3 with the canonical name in the VERDICT; the dictionaries still said 1 and the dispatch seed's header said 1.)
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HEADER = os.path.join(HERE, "..", "..", "src", "rootside_proto.h")


def version(header=HEADER):
    with open(header, encoding="utf-8") as fh:
        m = re.search(r"^#define\s+RXR_VERSION\s+(\d+)", fh.read(), re.M)
    if not m:
        raise SystemExit("rootside_version: no RXR_VERSION in %s" % header)
    return int(m.group(1))


def le16(n):
    return "\\x%02x\\x%02x" % (n & 0xFF, (n >> 8) & 0xFF)


def sync():
    v = version()
    changed = 0
    # rootside-proto.dict: version="\xVV\x00"
    p = os.path.join(HERE, "rootside-proto", "rootside-proto.dict")
    s = open(p, encoding="utf-8").read()
    n = re.sub(r'^version="[^"]*"', lambda m: 'version="%s"' % le16(v), s, flags=re.M)
    if n != s:
        open(p, "w", encoding="utf-8").write(n)
        changed += 1
    # rootside-dispatch.dict: after "RXR1" come the version alone and version+kind pairs (kind 1-4, 0x65)
    p = os.path.join(HERE, "rootside-dispatch", "rootside-dispatch.dict")
    s = open(p, encoding="utf-8").read()
    lines = s.split("\n")
    out = []
    after_magic = False
    for ln in lines:
        if ln == '"RXR1"':
            after_magic = True
        elif after_magic:
            m = re.fullmatch(r'"\\x[0-9a-f]{2}\\x00((?:\\x(?:01|02|03|04|65)\\x00)?)"', ln)
            if m:
                ln = '"%s%s"' % (le16(v), m.group(1))
            else:
                after_magic = False
        out.append(ln)
    n = "\n".join(out)
    n = re.sub(r"version \d+, the kinds", "version %d, the kinds" % v, n)
    if n != s:
        open(p, "w", encoding="utf-8").write(n)
        changed += 1
    print("rootside_version: RXR_VERSION %d; %d dictionary file(s) rewritten" % (v, changed))
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sync":
        sys.exit(sync())
    print(version())
