#!/usr/bin/env python3
"""FAKE of 16-resources.py: one row per second in DIR/resources.jsonl until SIGTERM."""
import argparse, json, os, signal, time
a = argparse.ArgumentParser(); a.add_argument("--box"); a.add_argument("--dir")
o = a.parse_args()
fine = [False]
signal.signal(signal.SIGTERM, lambda *_: fine.__setitem__(0, True))
while not fine[0]:
    with open(os.path.join(o.dir, "resources.jsonl"), "a") as f:
        f.write(json.dumps({"t": time.time(), "load": os.getloadavg()[0]}) + "\n")
    time.sleep(1)
