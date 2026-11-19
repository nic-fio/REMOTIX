#!/usr/bin/env python3
"""vm-login-test - open the page of the REMOTIX in the Radeon VM (ubuntu) (127.0.0.1:<port of the VM>, default ubuntu 8841) with the real Chromium of prove/lib.py
(imported, never modified) and log in as `prova`. It touches NO box: the Rig's `box` is replaced by a stub (lib's Box would run
commands in the test containers).  Usage: vm-radeon-login-test.py [ubuntu|kubuntu|xubuntu|lubuntu|<port>] [--bad] [--user NAME] [--png FILE] ; prints facts, exit 0 if the login reached a session."""
import sys, time
sys.path.insert(0, "/media/REMOTIX-UBUNTU/albero/prove")
import lib

PORTS = {"ubuntu": 8841, "kubuntu": 8842, "xubuntu": 8843, "lubuntu": 8844}
import argparse
ap = argparse.ArgumentParser()
ap.add_argument("vm", nargs="?", default="ubuntu")     # VM name or port; default ubuntu / 8841
ap.add_argument("--bad", action="store_true")
ap.add_argument("--user", default="prova")             # the user to log in as (password prova2026)
ap.add_argument("--png", default="")                   # save the settled picture of the canvas here
opt = ap.parse_args()
port = int(opt.vm) if opt.vm.isdigit() else PORTS[opt.vm]
lib.PORTS["xfce"] = port          # the Rig takes its port from this table

class NoBox:
    name = "vm"
    def run(self, *a, **k): return 1, "(no box: VM test)"
    def journal(self, *a, **k): return "(see the VM's journal)"
    def x_shortage(self, *a, **k): return ""

bad = opt.bad
r = lib.Rig("xfce", "chrome", opt.user, "wrong-password-x" if bad else "prova2026", "vm")
r.box = NoBox()
try:
    print("browser:", r.start(make_user=False))
    print("page form:", r.open_page())
    ok, s = r.try_login(real=False)
    print("admitted:", ok)
    print("outcome:", repr((s.get("outcome") or "").strip()), "class:", s.get("cls"), "painted:", s.get("painted"), "session:", s.get("session"))
    if ok and not bad:
        f = r.settle(cap=90, shell=False)   # painted frames and a settled, non-uniform picture (shell check needs a box: skipped)
        print("picture:", f["desc"], "| settled after %.1f s" % f["settle_s"])
        if opt.png:
            open(opt.png, "wb").write(f["png"]); print("picture saved:", opt.png)
    print("page log tail:", " | ".join((s.get("log") or "").strip().splitlines()[-6:]))
    sys.exit(0 if ok else 1)
finally:
    r.stop()
