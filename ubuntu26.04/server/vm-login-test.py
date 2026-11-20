#!/usr/bin/env python3
"""vm-login-test - open the page of the REMOTIX in the real-system VM (127.0.0.1:8901) with the real Chromium of prove/lib.py
(imported, never modified) and log in as `prova`. It touches NO box: the Rig's `box` is replaced by a stub (lib's Box would run
commands in the test containers).  Usage: vm-login-test.py [--bad] ; prints facts, exit 0 if the login reached a session."""
import sys, time
sys.path.insert(0, "/media/REMOTIX-UBUNTU/prove")
import lib

lib.PORTS["xfce"] = 8901          # the Rig takes its port from this table

class NoBox:
    name = "vm"
    def run(self, *a, **k): return 1, "(no box: VM test)"
    def journal(self, *a, **k): return "(see the VM's journal)"
    def x_shortage(self, *a, **k): return ""

bad = "--bad" in sys.argv
r = lib.Rig("xfce", "chrome", "prova", "wrong-password-x" if bad else "prova", "vm")
r.box = NoBox()
try:
    print("browser:", r.start(make_user=False))
    print("page form:", r.open_page())
    ok, s = r.try_login(real=False)
    print("admitted:", ok)
    print("outcome:", repr((s.get("outcome") or "").strip()), "class:", s.get("cls"), "painted:", s.get("painted"), "session:", s.get("session"))
    print("page log tail:", " | ".join((s.get("log") or "").strip().splitlines()[-6:]))
    sys.exit(0 if ok else 1)
finally:
    r.stop()
