#!/usr/bin/env python3
"""FAKE of 16-risorse.py: one row per second in DIR/risorse.jsonl until SIGTERM."""
import argparse, json, os, signal, time
a = argparse.ArgumentParser(); a.add_argument("--scatola"); a.add_argument("--dir")
o = a.parse_args()
fine = [False]
signal.signal(signal.SIGTERM, lambda *_: fine.__setitem__(0, True))
while not fine[0]:
    with open(os.path.join(o.dir, "risorse.jsonl"), "a") as f:
        f.write(json.dumps({"t": time.time(), "carico": os.getloadavg()[0]}) + "\n")
    time.sleep(1)
