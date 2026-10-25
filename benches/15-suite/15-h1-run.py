#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-h1-run — launches 15-h1-browser-net-hardening.py on the server for one or both browsers,
with the environment of 15-round.py (the desktop's own headless labwc, Chrome options),
and prints ONE table of verdicts.

    python3 15-h1-run.py --box xfce --browser chrome,firefox [--case a,b,c,d,e,f] [--users 8]
                         [--no-fault] [--out DIR] [--prova] [--dry-run] [--preflight]

  --box        gnome|kde|xfce|lxqt (one).  For d (N desktop sessions at once) xfce or lxqt are lighter.
  --browser    chrome, firefox or both (run one after the other)
  --case       the cases (default all); see the header of 15-h1-browser-net-hardening.py
  --users      case d: how many tenants/browsers (default 8, the 1.5 maximum)
  --no-fault   skip the fault passes (default: with them)
  --prova      SHORT TRIAL, ~12 min per browser: all cases, d with 3 users, no faults
  --out        folder of the results (default /media/REMOTIX-15/misure/h1-<date>-<box>)
  --dry-run    prints the commands and checks the files and the compositor, starts NOTHING
  --preflight  before: preflight.sh suite --ripara --desktop <box> (not needed as a hook of
               suite-ramo.sh, which has just done it)

⛔ The product to prove must already be in the box (suite-ramo.sh --hook installs it and puts the
   1.0 back at the end).  The cases use the box's SECOND server (rete15-g7, port 861x), never the 851x.
Exit: 0 all PASS (and the faults seen) · 1 at least one FAIL · 3 at least one BLOCKED and no FAIL · 2 usage.
Results: <out>/<browser>.log (the test's output), <out>/riepilogo.txt (the table), photos in <out>/<browser>/.
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TEST = os.path.join(HERE, "15-h1-browser-net-hardening.py")
PREFLIGHT = "/media/REMOTIX-15/lavori/notti/preflight.sh"
DESKTOP = ("gnome", "kde", "xfce", "lxqt")
CAP_S = 3 * 3600


def compositor(d, u):
    """The desktop's own headless labwc (15-compositors.sh), as 15-round.py does."""
    common = os.environ.get("REMOTIX_REAL_WAYLAND", "wayland-0")
    try:
        s = open("/run/user/%d/15-compositors/%s" % (u, d)).read().strip()
        if s and os.path.exists("/run/user/%d/%s" % (u, s)):
            return s
    except OSError:
        pass
    return common


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--box", choices=DESKTOP, required=True)
    a.add_argument("--browser", default="chrome,firefox")
    a.add_argument("--case", default="a,b,c,d,e,f")
    a.add_argument("--users", type=int, default=8)
    a.add_argument("--no-fault", action="store_true")
    a.add_argument("--prova", action="store_true")
    a.add_argument("--out", default="")
    a.add_argument("--dry-run", action="store_true")
    a.add_argument("--preflight", action="store_true")
    o = a.parse_args()
    brs = [b for b in o.browser.split(",") if b]
    if not brs or any(b not in ("chrome", "firefox") for b in brs):
        a.error("--browser: chrome, firefox")
    if any(c not in "abcdef" or len(c) != 1 for c in o.case.split(",")):
        a.error("--case: letters a..f separated by commas")
    if o.prova:
        o.users, o.no_fault = min(o.users, 3), True
    if not 1 <= o.users <= 8:
        a.error("--users: from 1 to 8")
    u = os.getuid()
    out = o.out or "/media/REMOTIX-15/misure/h1-%s-%s" % (datetime.datetime.now().strftime("%Y%m%d-%H%M%S"), o.box)
    wl = compositor(o.box, u)
    env = dict(os.environ, XDG_RUNTIME_DIR="/run/user/%d" % u, WAYLAND_DISPLAY=wl,
               REMOTIX_NESTED_SCREEN="1", REMOTIX_ON_SERVER="1",
               REMOTIX_CHROME_OPTIONS="--ozone-platform=wayland --disable-backgrounding-occluded-windows "
                                      "--disable-renderer-backgrounding --disable-background-timer-throttling",
               MOZ_ENABLE_WAYLAND="1")
    cmds = {}
    for b in brs:
        cmd = [sys.executable, TEST, "--box", o.box, "--browser", b, "--case", o.case, "--users", str(o.users),
               "--evidence", os.path.join(out, b)]
        if not o.no_fault:
            cmd.append("--fault")
        cmds[b] = cmd
    print("box %s · compositor %s · cases %s · users %d · faults %s · out %s" % (
        o.box, wl, o.case, o.users, "no" if o.no_fault else "yes", out))
    for b, c in cmds.items():
        print("  %s: %s" % (b, " ".join(c)))
    if o.dry_run:
        ok = os.path.isfile(TEST)
        print("test present: %s · compositor socket present: %s · preflight present: %s" % (
            ok, os.path.exists("/run/user/%d/%s" % (u, wl)), os.path.isfile(PREFLIGHT)))
        r = subprocess.run([sys.executable, TEST, "--certify"], capture_output=True, text=True)
        print("--certify of the judges: rc=%d (%d lines)" % (r.returncode, len(r.stdout.splitlines())))
        return 0 if ok and r.returncode == 0 else 2
    if o.preflight:
        r = subprocess.run(["bash", PREFLIGHT, "suite", "--ripara", "--desktop", o.box])
        if r.returncode != 0:
            print("=== PREFLIGHT KO")
            return 2
    os.makedirs(out, exist_ok=True)
    rows, rc_all = [], []
    for b, cmd in cmds.items():
        t0 = time.time()
        os.makedirs(os.path.join(out, b), exist_ok=True)
        with open(os.path.join(out, b + ".log"), "w") as log:
            try:
                p = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, env=env, cwd=HERE, timeout=CAP_S)
                rc = p.returncode
            except subprocess.TimeoutExpired:
                rc = 124
        rc_all.append(rc)
        for line in open(os.path.join(out, b + ".log"), errors="replace"):
            if line.startswith("SUITE "):
                try:
                    r = json.loads(line[6:])
                except ValueError:
                    continue
                rows.append((r["function"], b, r["pass"], r["outcome"], r["rationale"]))
        print("%s: rc=%d in %.0f s" % (b, rc, time.time() - t0), flush=True)
    outcomes = [r[3] for r in rows]
    # a case that gave no line at all is a hole, not a pass
    verdict = "FAIL" if ("FAIL" in outcomes or any(c in (1, 124) for c in rc_all)) else (
        "BLOCKED" if ("BLOCKED" in outcomes or not rows or any(c not in (0,) for c in rc_all)) else "PASS")
    with open(os.path.join(out, "riepilogo.txt"), "w") as f:
        f.write("# h1 · box %s · cases %s · %s\n" % (o.box, o.case, datetime.datetime.now().isoformat(timespec="seconds")))
        for fn, b, ps, oc, why in sorted(rows):
            f.write("%-9s %-8s %-8s %-8s %s\n" % (fn, b, ps, oc, why[:200]))
        f.write("RISULTATO: %s\n" % verdict)
    print(open(os.path.join(out, "riepilogo.txt")).read())
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 3}[verdict]


if __name__ == "__main__":
    sys.exit(main())
