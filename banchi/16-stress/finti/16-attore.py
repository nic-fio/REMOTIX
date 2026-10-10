#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FAKE of 16-attore.py — only to test 16-salita.py: it keeps the contract
(arguments, DIR/utente-NN/stato.jsonl every 5 s, nascita.json, SIGUSR1 = a
«photo», SIGTERM = clean exit) but opens NO browser and no sessions.
FINTO_MUORE=N: user N exits by itself after 20 s (to see the event)."""
import argparse, json, os, signal, sys, time
a = argparse.ArgumentParser()
for k in ("--scatola", "--wayland", "--dir", "--video"):
    a.add_argument(k, default="")
for k in ("--utente", "--seme", "--largo", "--alto", "--porte-base"):
    a.add_argument(k, type=int, default=0)
o = a.parse_args()
d = os.path.join(o.dir, "utente-%02d" % o.utente)
os.makedirs(d, exist_ok=True)
fine, foto = [False], [0]
signal.signal(signal.SIGTERM, lambda *_: fine.__setitem__(0, True))
def scatta(*_):
    foto[0] += 1
    open(os.path.join(d, "foto-%d-%d.txt" % (int(time.time()), foto[0])), "w").write("fake photo\n")
signal.signal(signal.SIGUSR1, scatta)
time.sleep(2)
json.dump({"t": time.time(), "utente": o.utente, "nascita_s": 2.0, "wayland": o.wayland,
           "finto": True}, open(os.path.join(d, "nascita.json"), "w"))
t0 = time.time()
while not fine[0]:
    with open(os.path.join(d, "stato.jsonl"), "a") as f:
        f.write(json.dumps({"t": time.time(), "utente": o.utente, "dipinti": 1}) + "\n")
    for _ in range(50):
        if fine[0]:
            break
        time.sleep(0.1)
    if os.environ.get("FINTO_MUORE") == str(o.utente) and time.time() - t0 > 20:
        sys.exit(7)
print("fake actor %d: clearing out" % o.utente, flush=True)
