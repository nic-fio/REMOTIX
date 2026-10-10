#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
19-nv-suite — THE SUBSET OF THE PHASE 15 SUITE ON THE NVIDIA MACHINE

    (from `19-nv-macchina.sh suite`, as the bench user `rxbanco`)
    python3 19-nv-suite.py --logbook R.jsonl --evidence DIR --port 7447 --manner win|headless

The tests are the suite's, IDENTICAL (banchi/15-suite/15-f*.py, not copied):
    F-001 F-002 (15-f001) · F-003 (15-f003) · F-011 (15-f011) · F-013 (15-f013)
    F-016 (15-f016) · F-018 (15-f018)
with the two browsers (Firefox with Marionette, Chrome with CDP), healthy + fault, cap 10 minutes
each, like `15-giro.py`.  ⭐ The only difference is where things are:

  - NO BOX: on the home server the product runs in `rete11-xfce` and the suite enters
    with `sudo podman exec`; here the product is INSTALLED on the machine (with its
    installer) and "inside the box" means `sudo -n sh -c` on the machine itself.
    ⇒ `Box.inside` is replaced (the same graft that `suite.py` already does for
    REMOTIX_ON_SERVER), and the server log is the file where the unit writes stderr;
  - one desktop only, XFCE (under labwc: the product starts it, on the card);
  - the browsers in THE BROWSERS' headless labwc (pixman, 3840x2160) like
    `15-compositori.sh`; if that one is not born, HEADLESS — and the line says so.

The log has the lines of `15-giro.py` (run "19-nvidia"): `15-rapporto.py` makes the
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
TREE = os.path.dirname(os.path.dirname(HERE))
SUITE = os.path.join(TREE, "benches", "15-suite")
PROVE = ("15-f001-accesso-e-prima-immagine.py", "15-f003-lo-schermo-si-aggiorna.py",
         "15-f011-la-tela-all-attacco.py", "15-f013-video.py",
         "15-f016-stacco-e-riattacco.py", "15-f018-riattacco-a-misura-diversa.py")
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

    def inside(self, row, seconds=90):
        """(code, output) of `row` as root ON THE MACHINE (the "box" is the machine)."""
        try:
            r = subprocess.run(["sudo", "-n", "sh", "-c", row], capture_output=True,
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
def read_it(file):
    body_text = open(file, encoding="utf-8").read()
    m = re.search(r"^FUNCTIONS\s*=\s*\(([^)]*)\)", body_text, re.M)
    functions = re.findall(r"[\"']([A-Z]-[0-9A-Z-]+)[\"']", m.group(1)) if m else []
    per_browser = not re.search(r"^PER_BROWSER\s*=\s*False", body_text, re.M)
    return functions, per_browser


def md5(fpath):
    try:
        return hashlib.md5(open(fpath, "rb").read()).hexdigest()[:8]
    except OSError:
        return "?"


def una(o, file, browser, base):
    label_name = os.path.basename(file)[:-3]
    short_v = label_name.split("-")[1]
    functions, _ = read_it(file)
    ev = os.path.join(o.evidence, DESKTOP, browser, short_v)
    os.makedirs(ev, exist_ok=True)
    amb = dict(os.environ, MOZ_ENABLE_WAYLAND="1")
    cmd = [sys.executable, os.path.abspath(__file__), "--internal", file,
           "--container_box", DESKTOP, "--browser", browser, "--host", "127.0.0.1",
           "--port", str(o.port), "--base-ports", str(base), "--evidence", ev, "--fault"]
    if o.manner == "win":
        amb.update(REMOTIX_NESTED_SCREEN="1", REMOTIX_CHROME_OPTIONS=CHROME_OPTIONS)
    else:
        cmd.append("--headless")
        amb.pop("WAYLAND_DISPLAY", None)
        amb.pop("REMOTIX_NESTED_SCREEN", None)
    start = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    t0 = time.time()
    line_list, outside = [], ""
    with open(os.path.join(ev, "uscita.log"), "w") as log:
        try:
            pr = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                  errors="replace", env=amb, cwd=SUITE, start_new_session=True)
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
                for row in pr.stdout:
                    log.write(row)
                    log.flush()
                    if row.startswith("SUITE "):
                        try:
                            line_list.append(json.loads(row[6:]))
                        except ValueError:
                            pass
                pr.wait()
            finally:
                cane.cancel()
            if expired:
                outside = "over %d minutes: the test was stopped" % (CAP_S // 60)
        except Exception as e:                                       # noqa: BLE001
            outside = "the bench could not launch the test: %r" % e
    duration = round(time.time() - t0)
    views = {(r.get("function"), r.get("passed")) for r in line_list}
    for f in functions:
        for ps in ("sana", "fault"):
            if (f, ps) not in views:
                line_list.append({"function": f, "passed": ps, "outcome": "BLOCKED",
                              "rationale": outside or "the test gave no verdict for %s "
                              "(see uscita.log)" % f, "fault_seen": None, "evidence": []})
    out_dir = []
    for r in line_list:
        f = r.get("function", "?")
        out_dir.append({
            "lap": ROUND,
            "test": "T-%s-%s-%s%s" % (f[2:] if f.startswith("F-") else f, DESKTOP, browser,
                                       "-fault" if r.get("passed") == "fault" else ""),
            "function": f, "passed": r.get("passed", "sana"), "prova": label_name,
            "desktop": DESKTOP, "browser": browser, "version_v": r.get("version_v", ""),
            "system_wide": os.environ.get("RXNV_SYSTEM", "?") + (" · HEADLESS" if o.manner != "win" else ""),
            "binary": md5("/usr/libexec/remotix/remotix"),
            "page_v": md5("/usr/share/remotix/pagina.html"),
            "commit": os.environ.get("RXNV_VERSION", "?"),
            "start": start, "duration_s": duration, "outcome": r.get("outcome"),
            "rationale": r.get("rationale", ""), "expected_val": r.get("expected_val", ""),
            "observed": r.get("observed", ""), "fault_seen": r.get("fault_seen"),
            "evidence": [os.path.join(ev, "uscita.log")] + [x for x in r.get("evidence") or [] if x],
            "defect": None})
    with open(o.logbook, "a", errors="backslashreplace") as reg:
        for r in out_dir:
            reg.write(json.dumps(r, ensure_ascii=False) + "\n")
    count = {}
    for r in out_dir:
        count[r["outcome"]] = count.get(r["outcome"], 0) + 1
    print("[%s %s] %-40s %4d s  %s" % (DESKTOP, browser, label_name, duration,
                                        " ".join("%s=%d" % kv for kv in sorted(count.items()))),
          flush=True)
    return out_dir


def primary():
    if len(sys.argv) > 2 and sys.argv[1] == "--internal":
        return internal(sys.argv[2], sys.argv[3:])
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--logbook", required=True)
    a.add_argument("--evidence", required=True)
    a.add_argument("--port", type=int, default=7447)
    a.add_argument("--manner", choices=("win", "headless"), default="win")
    a.add_argument("--prove", default="", help="only these (e.g. f001,f018)")
    a.add_argument("--browser", default=",".join(BROWSER))
    a.add_argument("--desktop", default="xfce", choices=("gnome", "kde", "xfce", "lxqt"))
    o = a.parse_args()
    if "RXNV_LOG" not in os.environ:
        a.error("RXNV_LOG is missing (the file the server writes to)")
    os.makedirs(o.evidence, exist_ok=True)
    all_v = []
    globals()["DESKTOP"] = o.desktop
    # the desktop's debug ports as in 15-giro.py
    base = 3100 + 10 * ("gnome", "kde", "xfce", "lxqt").index(o.desktop)
    print("⭐ 19-nv-suite · %s · %s · browser %s · port %d" % (
        o.desktop, o.manner, o.browser, o.port), flush=True)
    # ⭐ 6 Oct 2026: with --prove one chooses among ALL the phase 15 tests (e.g. f012 for
    #    sound without video), not only among the six of the run; "-f012-" does not pick f012b
    choices = PROVE
    if o.prove:
        desired = ["-%s-" % x.strip() for x in o.prove.split(",") if x.strip()]
        choices = [f for f in sorted(os.listdir(SUITE))
                  if f.startswith("15-f") and f.endswith(".py") and any(v in f for v in desired)]
    for p in choices:
        file = os.path.join(SUITE, p)
        _, per_browser = read_it(file)
        for b in o.browser.split(","):
            if not per_browser and b != "firefox":
                continue
            all_v += una(o, file, b, base)
    count = {}
    for r in all_v:
        count[r["outcome"]] = count.get(r["outcome"], 0) + 1
    summary = " ".join("%s=%d" % kv for kv in sorted(count.items()))
    print("END %s" % summary, flush=True)
    if count.get("FAIL"):
        return 1
    return 3 if count.get("BLOCKED") or not all_v else 0


if __name__ == "__main__":
    sys.exit(primary())
