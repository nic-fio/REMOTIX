#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FAKE of 16-attore.py — only to test 16-salita.py: it keeps the contract
(arguments, DIR/user-NN/state.jsonl every 5 s, birth.json, SIGUSR1 = a
«photo», SIGTERM = clean exit) but opens NO browser and no sessions.
FAKE_DIES=N: user N exits by itself after 20 s (to see the event)."""
import argparse, json, os, signal, sys, time
a = argparse.ArgumentParser()
for k in ("--box", "--wayland", "--dir", "--video"):
    a.add_argument(k, default="")
for k in ("--user", "--seed", "--width", "--height", "--base-port"):
    a.add_argument(k, type=int, default=0)
o = a.parse_args()
d = os.path.join(o.dir, "user-%02d" % o.user)
os.makedirs(d, exist_ok=True)
fine, foto = [False], [0]
signal.signal(signal.SIGTERM, lambda *_: fine.__setitem__(0, True))
def fires(*_):
    foto[0] += 1
    open(os.path.join(d, "foto-%d-%d.txt" % (int(time.time()), foto[0])), "w").write("fake photo\n")
signal.signal(signal.SIGUSR1, fires)
time.sleep(2)
json.dump({"t": time.time(), "user": o.user, "birth_s": 2.0, "wayland": o.wayland,
           "fake": True}, open(os.path.join(d, "birth.json"), "w"))
t0 = time.time()
while not fine[0]:
    with open(os.path.join(d, "state.jsonl"), "a") as f:
        f.write(json.dumps({"t": time.time(), "user": o.user, "painted": 1}) + "\n")
    for _ in range(50):
        if fine[0]:
            break
        time.sleep(0.1)
    if os.environ.get("FAKE_DIES") == str(o.user) and time.time() - t0 > 20:
        sys.exit(7)
print("fake actor %d: clearing out" % o.user, flush=True)
