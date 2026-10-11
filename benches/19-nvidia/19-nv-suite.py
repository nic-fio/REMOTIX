#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
19-nv-suite — THE SUBSET OF THE PHASE 15 SUITE ON THE NVIDIA MACHINE

    (from `19-nv-machine.sh suite`, as the bench user `rxbanco`)
    python3 19-nv-suite.py --log R.jsonl --evidence DIR --port 7447 --mode window|headless

The tests are the suite's, IDENTICAL (benches/15-suite/15-f*.py, not copied):
    F-001 F-002 (15-f001) · F-003 (15-f003) · F-011 (15-f011) · F-013 (15-f013)
    F-016 (15-f016) · F-018 (15-f018)
with the two browsers (Firefox with Marionette, Chrome with CDP), healthy + fault, cap 10 minutes
each, like `15-round.py`.  ⭐ The only difference is where things are:

  - NO BOX: on the home server the product runs in `rete11-xfce` and the suite enters
    with `sudo podman exec`; here the product is INSTALLED on the machine (with its
    installer) and "inside the box" means `sudo -n sh -c` on the machine itself.
    ⇒ `Scatola.dentro` is replaced (the same graft that `suite.py` already does for
    REMOTIX_ON_SERVER), and the server log is the file where the unit writes stderr;
  - one desktop only, XFCE (under labwc: the product starts it, on the card);
  - the browsers in THE BROWSERS' headless labwc (pixman, 3840x2160) like
    `15-compositors.sh`; if that one is not born, HEADLESS — and the line says so.

The log has the lines of `15-round.py` (run "19-nvidia"): `15-report.py` makes the
report as for the other runs.  Exit: 0 all PASS · 1 at least one FAIL · 3 BLOCKED.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import runpy
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ALBERO = os.path.dirname(os.path.dirname(HERE))
SUITE = os.path.join(ALBERO, "benches", "15-suite")
PROVE = ("15-f001-login-and-first-image.py", "15-f003-the-screen-updates.py",
         "15-f011-the-canvas-on-attach.py", "15-f013-video.py",
         "15-f016-detach-and-reattach.py", "15-f018-reattach-at-a-different-size.py")
DESKTOP = "xfce"
BROWSER = ("firefox", "chrome")
CAP_S = 600
ROUND = "19-nvidia"
CHROME_OPTIONS = ("--ozone-platform=wayland --disable-backgrounding-occluded-windows "
                  "--disable-renderer-backgrounding --disable-background-timer-throttling")


# ═══════════════════════════════════════════════════════════════════════════
#  INSIDE A TEST (child process): the graft, then the real test
# ═══════════════════════════════════════════════════════════════════════════
def internal(file, rest):
    sys.path.insert(0, SUITE)
    import suite as S                                              # noqa: E402

    def inside(self, line, seconds=90):
        """(code, output) of `line` as root ON THE MACHINE (the "box" is the machine)."""
        try:
            r = subprocess.run(["sudo", "-n", "sh", "-c", line], capture_output=True,
                               text=True, errors="replace", timeout=seconds)
        except subprocess.TimeoutExpired:
            return None, "(no answer within %d s)" % seconds
        return r.returncode, (r.stdout + r.stderr).strip()

    S.C20V.Box.inside = inside
    S.C20V.LOG = os.environ["RXNV_LOG"]
    sys.argv = [file] + rest
    runpy.run_path(file, run_name="__main__")


# ═══════════════════════════════════════════════════════════════════════════
#  THE RUN
# ═══════════════════════════════════════════════════════════════════════════
def load(file):
    text = open(file, encoding="utf-8").read()
    m = re.search(r"^FUNZIONI\s*=\s*\(([^)]*)\)", text, re.M)
    functions = re.findall(r"[\"']([A-Z]-[0-9A-Z-]+)[\"']", m.group(1)) if m else []
    per_browser = not re.search(r"^PER_BROWSER\s*=\s*False", text, re.M)
    return functions, per_browser


def md5(fpath):
    try:
        return hashlib.md5(open(fpath, "rb").read()).hexdigest()[:8]
    except OSError:
        return "?"


def una(o, file, browser, base):
    name = os.path.basename(file)[:-3]
    too_short = name.split("-")[1]
    functions, _ = load(file)
    ev = os.path.join(o.evidence, DESKTOP, browser, too_short)
    os.makedirs(ev, exist_ok=True)
    env = dict(os.environ, MOZ_ENABLE_WAYLAND="1")
    cmd = [sys.executable, os.path.abspath(__file__), "--internal", file,
           "--box", DESKTOP, "--browser", browser, "--host", "127.0.0.1",
           "--port", str(o.port), "--base-port", str(base), "--evidence", ev, "--fault"]
    if o.mode == "window":
        env.update(REMOTIX_NESTED_SCREEN="1", REMOTIX_CHROME_OPTIONS=CHROME_OPTIONS)
    else:
        cmd.append("--headless")
        env.pop("WAYLAND_DISPLAY", None)
        env.pop("REMOTIX_NESTED_SCREEN", None)
    started = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    t0 = time.time()
    lines, report = [], ""
    with open(os.path.join(ev, "uscita.log"), "w") as log:
        try:
            pr = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                  errors="replace", env=env, cwd=SUITE, start_new_session=True)
            expired = []

            def halt():
                expired.append(1)
                try:
                    os.killpg(pr.pid, 9)
                except OSError:
                    pass
            cane = threading.Timer(CAP_S, halt)
            cane.start()
            try:
                for line in pr.stdout:
                    log.write(line)
                    log.flush()
                    if line.startswith("SUITE "):
                        try:
                            lines.append(json.loads(line[6:]))
                        except ValueError:
                            pass
                pr.wait()
            finally:
                cane.cancel()
            if expired:
                report = "over %d minutes: the test was stopped" % (CAP_S // 60)
        except Exception as e:                                       # noqa: BLE001
            report = "the bench could not launch the test: %r" % e
    duration = round(time.time() - t0)
    views = {(r.get("function"), r.get("pass")) for r in lines}
    for f in functions:
        for ps in ("healthy", "fault"):
            if (f, ps) not in views:
                lines.append({"function": f, "pass": ps, "outcome": "BLOCKED",
                              "rationale": report or "the test gave no verdict for %s "
                              "(see uscita.log)" % f, "fault_seen": None, "evidence": []})
    output = []
    for r in lines:
        f = r.get("function", "?")
        output.append({
            "round": ROUND,
            "test": "T-%s-%s-%s%s" % (f[2:] if f.startswith("F-") else f, DESKTOP, browser,
                                       "-fault" if r.get("pass") == "fault" else ""),
            "function": f, "pass": r.get("pass", "healthy"), "prova": name,
            "desktop": DESKTOP, "browser": browser, "version": r.get("version", ""),
            "system": os.environ.get("RXNV_SYSTEM", "?") + (" · HEADLESS" if o.mode != "window" else ""),
            "binary": md5("/usr/libexec/remotix/remotix"),
            "page": md5("/usr/share/remotix/page.html"),
            "commit": os.environ.get("RXNV_VERSION", "?"),
            "started": started, "duration_s": duration, "outcome": r.get("outcome"),
            "rationale": r.get("rationale", ""), "expected": r.get("expected", ""),
            "observed": r.get("observed", ""), "fault_seen": r.get("fault_seen"),
            "evidence": [os.path.join(ev, "uscita.log")] + [x for x in r.get("evidence") or [] if x],
            "defect": None})
    with open(o.log, "a", errors="backslashreplace") as reg:
        for r in output:
            reg.write(json.dumps(r, ensure_ascii=False) + "\n")
    tally = {}
    for r in output:
        tally[r["outcome"]] = tally.get(r["outcome"], 0) + 1
    print("[%s %s] %-40s %4d s  %s" % (DESKTOP, browser, name, duration,
                                        " ".join("%s=%d" % kv for kv in sorted(tally.items()))),
          flush=True)
    return output


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--internal":
        return internal(sys.argv[2], sys.argv[3:])
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--log", required=True)
    a.add_argument("--evidence", required=True)
    a.add_argument("--port", type=int, default=7447)
    a.add_argument("--mode", choices=("window", "headless"), default="window")
    a.add_argument("--tests", default="", help="only these (e.g. f001,f018)")
    a.add_argument("--browser", default=",".join(BROWSER))
    a.add_argument("--desktop", default="xfce", choices=("gnome", "kde", "xfce", "lxqt"))
    o = a.parse_args()
    if "RXNV_LOG" not in os.environ:
        a.error("RXNV_LOG is missing (the file the server writes to)")
    os.makedirs(o.evidence, exist_ok=True)
    all_items = []
    globals()["DESKTOP"] = o.desktop
    # the desktop's debug ports as in 15-round.py
    base = 3100 + 10 * ("gnome", "kde", "xfce", "lxqt").index(o.desktop)
    print("⭐ 19-nv-suite · %s · %s · browser %s · port %d" % (
        o.desktop, o.mode, o.browser, o.port), flush=True)
    # ⭐ 6 Oct 2026: with --tests one chooses among ALL the phase 15 tests (e.g. f012 for
    #    sound without video), not only among the six of the run; "-f012-" does not pick f012b
    choices = PROVE
    if o.tests:
        wanted_flags = ["-%s-" % x.strip() for x in o.tests.split(",") if x.strip()]
        choices = [f for f in sorted(os.listdir(SUITE))
                  if f.startswith("15-f") and f.endswith(".py") and any(v in f for v in wanted_flags)]
    for p in choices:
        file = os.path.join(SUITE, p)
        _, per_browser = load(file)
        for b in o.browser.split(","):
            if not per_browser and b != "firefox":
                continue
            all_items += una(o, file, b, base)
    tally = {}
    for r in all_items:
        tally[r["outcome"]] = tally.get(r["outcome"], 0) + 1
    summary = " ".join("%s=%d" % kv for kv in sorted(tally.items()))
    print("END %s" % summary, flush=True)
    if tally.get("FAIL"):
        return 1
    return 3 if tally.get("BLOCKED") or not all_items else 0


if __name__ == "__main__":
    sys.exit(main())
