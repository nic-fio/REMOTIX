#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
15-giro — ONE ROUND OF THE FUNCTIONAL SUITE (phase 15)
===========================================================================

    (on the server, as nicfio — the real browsers are there)
    python3 15-giro.py --lap 1
    python3 15-giro.py --lap bonifica --desktop kde --browser chrome --prove f018
    python3 15-giro.py --lap 1 --technical-layer          # + C7 C9 C18 C19 C14
    python3 15-giro.py --listing                           # what it would do

    (from the tablet)  bash banchi/15-suite/15-porta.sh && \
                  ssh nicfio@192.168.0.2 'python3 /media/REMOTIX/src/controllo/banchi/15-suite/15-giro.py --lap 1'

WHAT IT DOES
  - finds the tests `15-f*.py` / `15-n*.py` of this folder and reads their
    declarations (lines of text, not imports):
        FUNCTIONS = ("F-004", …)        what it looks at (mandatory)
        PER_BROWSER = False            runs only once (with Firefox)
        LONG = True                   runs IN PARALLEL with the others of its desktop
        SERVER = "15-g7-server.sh"     a server of its own to start/stop
  - ⭐ the FOUR desktops in parallel, one queue per desktop; in the queue the two
    browsers one after the other; different debug ports per desktop;
  - every test with `--fault` (healthy + fault in the same session), cap
    10 minutes (beyond: BLOCKED «over 10 minutes», and the process is killed);
  - ⭐ EVERY run leaves lines in the REGISTER (append only):
        /media/REMOTIX/misure/fase15/registro.jsonl
    with lap, test, function, desktop, browser, version_v, system_wide, binary,
    page_v, commit, start, duration, outcome, rationale, expected_val, observed,
    fault_seen, evidence, defect;
  - the evidence in /media/REMOTIX/misure/fase15/giro<N>/<desktop>/<browser>/<prova>/
    (the whole output of the test in `uscita.log`, the photos and the consoles inside).

⛔ BEFORE STARTING it checks whether in the boxes there is a session of a person
   (nictest or anyone who is not a bench tenant `c<n>u<n>`): if there is, it
   stops — the user's manual test is not interrupted (24 Sep 2026).
"""
import argparse
import datetime
import fcntl
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH_ROOT = os.path.dirname(HERE)
MEASURES = os.environ.get("REMOTIX_MEASURES_15", "/media/REMOTIX/misure/fase15")
LOG = os.path.join(MEASURES, "registro.jsonl")
NETWORK11 = "/media/REMOTIX/rete11"
DESKTOP = ("gnome", "kde", "xfce", "lxqt")
BROWSER = ("firefox", "chrome")
CAP_S = 600
# ⚠ the phone (phase 19 §5) declares its own: `banchi/19-android/19-android.py`
SYSTEM = os.environ.get("REMOTIX_SYSTEM_15") or \
    "Debian 13 · headless labwc 3840x2160 · i5-13500T, Intel UHD 770"
TENANT = re.compile(r"^c[0-9]+b?u[0-9]+$")
_lock = threading.Lock()


def _sudo_password():
    """The server's sudo password: from REMOTIX_SUDO_PASSWORD, or from the «pass:» line of
    ~/SERVER.ssh (the same file as fondamenta/strumenti/sshpw.py). ⛔ Never written
    in the benches: they are in the repository."""
    p = os.environ.get("REMOTIX_SUDO_PASSWORD")
    if p is None:
        try:
            for r in open(os.path.expanduser("~/SERVER.ssh")):
                if r.startswith("pass:"):
                    p = r.split(":", 1)[1].strip()
                    break
        except OSError:
            pass
    return (p or "") + "\n"


# ═══════════════════════════════════════════════════════════════════════════
#  THE TESTS AND THEIR DECLARATIONS
# ═══════════════════════════════════════════════════════════════════════════
def read_tests(filter=""):
    prove = []
    for f in sorted(glob.glob(os.path.join(HERE, "15-[fn][0-9]*.py"))):
        body_text = open(f, encoding="utf-8").read()
        m = re.search(r"^FUNCTIONS\s*=\s*\(([^)]*)\)", body_text, re.M)
        if not m:
            continue
        functions = re.findall(r"[\"']([A-Z]-[0-9A-Z-]+)[\"']", m.group(1))
        label_name = os.path.basename(f)[:-3]
        short_v = label_name.split("-")[1]                       # f004
        if filter and not any(x.strip() and x.strip() in label_name for x in filter.split(",")):
            continue
        per_browser = not re.search(r"^PER_BROWSER\s*=\s*False", body_text, re.M)
        long = bool(re.search(r"^LONG\s*=\s*True", body_text, re.M))
        # ⭐ PHONE_ONLY = True: the test makes sense only with the real phone (F-031, touch)
        solo_tel = bool(re.search(r"^PHONE_ONLY\s*=\s*True", body_text, re.M))
        s = re.search(r"^SERVER\s*=\s*[\"']([^\"']+)[\"']", body_text, re.M)
        prove.append({"file": f, "label_name": label_name, "short_v": short_v, "functions": functions,
                      "per_browser": per_browser, "long": long, "solo_telefono": solo_tel,
                      "server": s.group(1) if s else ""})
    return prove


# ═══════════════════════════════════════════════════════════════════════════
#  THE MACHINE: boxes, binary, page, commit
# ═══════════════════════════════════════════════════════════════════════════
def sudo(command, seconds=120):
    r = subprocess.run(["sudo", "-S", "-p", "", "sh", "-c", command], input=_sudo_password(),
                       capture_output=True, text=True, errors="replace", timeout=seconds)
    return r.returncode, (r.stdout + r.stderr).strip()


def in_box(d, command, seconds=60):
    return sudo("podman exec rete11-%s sh -c %s" % (d, _q(command)), seconds)


def _q(s):
    return "'" + s.replace("'", "'\"'\"'") + "'"


def fingerprints(d):
    _c, t = in_box(d, "md5sum /opt/remotix/remotix /opt/remotix/pagina.html")
    v = {}
    for row in t.splitlines():
        p = row.split()
        if len(p) == 2:
            v["binary" if p[1].endswith("remotix") else "page_v"] = p[0][:8]
    return v


def people_inside(d):
    """The users with a session who are NOT bench tenants."""
    _c, t = in_box(d, "loginctl list-users --no-legend 2>/dev/null | awk '{print $2}'")
    return [u for u in t.split() if u and not TENANT.match(u) and u not in ("root", "provanic")]


def commit():
    p = os.path.join(BENCH_ROOT, "..", "VER")
    try:
        return open(p).read().strip()
    except OSError:
        return "?"


# ⛔ THE BOXES BELONG TO ONE BENCH AT A TIME (29 Sep 2026, «user unknown» of phase 16):
#   the hook (even the pre-push one, on its own) clears out ALL the tenants
#   `c<n>u<n>` before every mesh ⇒ a push during a round deleted the tenants
#   born 7 s earlier (`[M]` 04:28, 04:40, 04:42 of 29 Sep = the 4 FAIL and 36 BLOCKED).
#   The same lock in 15-giro.py, 16-salita.py and 11-gancio.sh; whoever is launched by
#   one of them inherits REMOTIX_KEPT_BOXES and does not take it again.
#   ⚠ NOT in /run/lock: the folder is «sticky» and with fs.protected_regular root does not
#   reopen the file created by nicfio (and the hook says «held» for free boxes, `[M]`).
BOX_LOCK = "/media/REMOTIX/rete11/.scatole.lock"


def keep_boxes(chi):
    """None if the boxes are ours (the lock stays taken until exit),
    otherwise the sentence saying who holds them."""
    if os.environ.get("REMOTIX_KEPT_BOXES"):
        return None
    fd = os.open(BOX_LOCK, os.O_RDWR | os.O_CREAT, 0o666)
    try:
        os.fchmod(fd, 0o666)
    except OSError:
        pass
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        try:
            holds = os.pread(fd, 200, 0).decode(errors="replace").strip()
        except OSError:
            holds = ""
        os.close(fd)
        return "the boxes are already held by another bench (%s)" % (holds or "?")
    os.ftruncate(fd, 0)
    os.pwrite(fd, ("%s pid %d" % (chi, os.getpid())).encode(), 0)
    os.environ["REMOTIX_KEPT_BOXES"] = chi
    globals()["_fd_scatole"] = fd
    return None


# ═══════════════════════════════════════════════════════════════════════════
#  THE REGISTER
# ═══════════════════════════════════════════════════════════════════════════
def put_out(line_list):
    os.makedirs(MEASURES, exist_ok=True)
    with _lock, open(LOG, "a", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        for r in line_list:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        fcntl.flock(f, fcntl.LOCK_UN)


# ═══════════════════════════════════════════════════════════════════════════
#  ONE TEST
# ═══════════════════════════════════════════════════════════════════════════
def compositor(d, u, long):
    """⭐ The headless labwc OF the desktop (15-compositori.sh): four desktops
    in parallel in the same compositor cover Chrome's windows, and a covered
    Chrome cannot be photographed.  The LONG tests (a browser idle for minutes)
    go into the «common» labwc (started by 15-compositori.sh with its own name, not
    «wayland-0»: after a reboot that number may belong to a desktop)."""
    common = os.environ.get("REMOTIX_REAL_WAYLAND", "wayland-0")
    try:
        s = open("/run/user/%d/15-compositori/%s" % (u, "common" if long else d)).read().strip()
        if s and os.path.exists("/run/user/%d/%s" % (u, s)):
            return s
    except OSError:
        pass
    return common


def one_test(o, p, d, b, base, meta):
    ev = os.path.join(MEASURES, "lap%s" % o.lap, d, b, p["short_v"])
    os.makedirs(ev, exist_ok=True)
    u = os.getuid()
    amb = dict(os.environ, XDG_RUNTIME_DIR="/run/user/%d" % u,
               WAYLAND_DISPLAY=compositor(d, u, p["long"]),
               REMOTIX_NESTED_SCREEN="1", REMOTIX_ON_SERVER="1",
               REMOTIX_CHROME_OPTIONS="--ozone-platform=wayland --disable-backgrounding-occluded-windows --disable-renderer-backgrounding --disable-background-timer-throttling", MOZ_ENABLE_WAYLAND="1")
    cmd = [sys.executable, p["file"], "--container_box", d, "--browser", b,
           "--base-ports", str(base), "--evidence", ev]
    if not o.no_fault:
        cmd.append("--fault")
    start = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    t0 = time.time()
    line_list, outside = [], ""
    with open(os.path.join(ev, "uscita.log"), "w") as log:
        try:
            pr = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, errors="replace", env=amb, cwd=HERE,
                                  start_new_session=True)
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
        except Exception as e:                   # noqa: BLE001
            outside = "the round could not launch the test: %r" % e
    duration = round(time.time() - t0)
    past = ("sana",) if o.no_fault else ("sana", "fault")
    views = {(r.get("function"), r.get("passed")) for r in line_list}
    for f in p["functions"]:
        for ps in past:
            if (f, ps) not in views:
                line_list.append({"function": f, "passed": ps, "outcome": "BLOCKED",
                              "rationale": outside or "the test gave no judgment for %s "
                              "(see uscita.log)" % f, "fault_seen": None, "evidence": []})
    out_dir = []
    for r in line_list:
        f = r.get("function", "?")
        out_dir.append({
            "lap": o.lap,
            "test": "T-%s-%s-%s%s" % (f[2:] if f.startswith("F-") else f, d, b,
                                       "-fault" if r.get("passed") == "fault" else ""),
            "function": f, "passed": r.get("passed", "sana"), "prova": p["label_name"],
            "desktop": d, "browser": b, "version_v": r.get("version_v", ""),
            "system_wide": SYSTEM, "binary": meta.get(d, {}).get("binary", "?"),
            "page_v": meta.get(d, {}).get("page_v", "?"), "commit": meta.get("commit", "?"),
            "start": start, "duration_s": duration, "outcome": r.get("outcome"),
            "rationale": r.get("rationale", ""), "expected_val": r.get("expected_val", ""),
            "observed": r.get("observed", ""), "fault_seen": r.get("fault_seen"),
            "evidence": [os.path.join(ev, "uscita.log")] + [x for x in r.get("evidence") or [] if x],
            "defect": None})
    put_out(out_dir)
    count = {}
    for r in out_dir:
        count[r["outcome"]] = count.get(r["outcome"], 0) + 1
    print("[%s %s] %-40s %4d s  %s" % (d, b, p["label_name"], duration,
                                        " ".join("%s=%d" % kv for kv in sorted(count.items()))),
          flush=True)
    return out_dir


def streak(o, d, prove, meta, outcomes):
    base = 3100 + 10 * DESKTOP.index(d)
    long_tests = [p for p in prove if p["long"]]
    short = [p for p in prove if not p["long"]]
    threads = []
    for i, p in enumerate(long_tests):
        b = o.browser[0]
        t = threading.Thread(target=lambda p=p, b=b, i=i: outcomes.extend(
            one_test(o, p, d, b, 3500 + 10 * DESKTOP.index(d) + 2 * i, meta)))
        t.start()
        threads.append(t)
    for b in o.browser:
        for p in short:
            if not p["per_browser"] and b != o.browser[0]:
                continue
            if p["solo_telefono"] and b != "phone":
                continue
            outcomes.extend(one_test(o, p, d, b, base, meta))
    for t in threads:
        t.join()


def test_server(prove, desktop, action):
    for s in sorted({p["server"] for p in prove if p["server"]}):
        for d in desktop:
            c, t = subprocess.run(["bash", os.path.join(HERE, s), action, d],
                                  capture_output=True, text=True).returncode, ""
            print("   server %s %s %s: code %s" % (s, action, d, c), flush=True)


# ═══════════════════════════════════════════════════════════════════════════
#  THE SHORT TECHNICAL LAYER: C7 C9 C18 C19 (per desktop) and C14 (all together)
# ═══════════════════════════════════════════════════════════════════════════
MESHES = [("C7", "c7", [], False), ("C7", "c7", ["--leave-a-process", "--wait-closing", "10"], True),
          ("C9", "c9", [], False), ("C9", "c9", ["--remove-name", "overall"], True),
          ("C18", "c18", [], False), ("C18", "c18", ["--no-usermod"], True),
          ("C19", "c19", [], False), ("C19", "c19", ["--leave-a-tenant"], True)]


CLEAROUT = r"""
for u in $(awk -F: '$1 ~ /^c[0-9]+b?u[0-9]+$/ {print $1}' /etc/passwd); do
  id=$(id -u "$u" 2>/dev/null)
  m="runuser -u [$(printf %s "$u" | cut -c1)]$(printf %s "$u" | cut -c2-) "
  loginctl terminate-user "$u" >/dev/null 2>&1
  pkill -CONT -f "$m" >/dev/null 2>&1; pkill -CONT -u "$u" >/dev/null 2>&1
  pkill -KILL -f "$m" >/dev/null 2>&1; pkill -KILL -u "$u" >/dev/null 2>&1
  sleep 0.2
  userdel -r "$u" >/dev/null 2>&1 || userdel "$u" >/dev/null 2>&1
  [ -n "$id" ] && systemctl reset-failed "user@$id.service" >/dev/null 2>&1
  [ -n "$id" ] && find /tmp -maxdepth 1 -uid "$id" -exec rm -rf {} + 2>/dev/null
done; true
"""


def clear_out(d):
    """The net's tenants (`c<n>[b]u<n>`) out of the box: the same line
    as 11-gancio.sh, in the same namespace (nictest and provanic stay)."""
    in_box(d, CLEAROUT, 120)


def technical_layer(o, desktop, meta):
    line_list = []

    def una(d, label_name, below, arg, fault):
        # ⛔ the net's CLEAR-OUT (11-gancio.sh clear_out_tenants), before
        #   every mesh: the meshes delete their tenant BEFORE creating it,
        #   not after ⇒ without it, C19 sees C9's tenants and says red.
        #   `[M]` round 1, 25 Sep 2026 (D-013, class C).
        clear_out(d)
        t0 = time.time()
        c, t = sudo("bash %s/11-accendi.sh %s %s %s" % (NETWORK11, below, d, " ".join(arg)), 900)
        # ⛔ the fault reads the other way round (11-gancio.sh run_mesh): 0 = seen
        if fault:
            outcome = {0: "PASS", 1: "FAIL"}.get(c, "BLOCKED")
        else:
            outcome = {0: "PASS", 1: "FAIL"}.get(c, "BLOCKED")
        ev = os.path.join(MEASURES, "lap%s" % o.lap, d, "tecnico", label_name + ("-fault" if fault else ""))
        os.makedirs(ev, exist_ok=True)
        with open(os.path.join(ev, "uscita.log"), "w") as f:
            f.write(t)
        queue = [x for x in t.splitlines() if x.strip()][-1:] or [""]
        line_list.append({"lap": o.lap, "test": "T-%s-%s%s" % (label_name, d, "-fault" if fault else ""),
                      "function": label_name, "passed": "fault" if fault else "sana",
                      "prova": "11-accendi.sh %s" % below, "desktop": d, "browser": "-",
                      "version_v": "", "system_wide": SYSTEM,
                      "binary": meta.get(d, {}).get("binary", "?"),
                      "page_v": meta.get(d, {}).get("page_v", "?"), "commit": meta.get("commit"),
                      "start": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                      "duration_s": round(time.time() - t0), "outcome": outcome,
                      "rationale": "code %s · %s" % (c, queue[0][:200]),
                      "expected_val": "", "observed": "", "fault_seen": (c == 0) if fault else None,
                      "evidence": [os.path.join(ev, "uscita.log")], "defect": None})
        print("[%s technical] %s%s → %s" % (d, label_name, " (fault)" if fault else "", outcome), flush=True)

    threads = []
    for d in desktop:
        def streak_t(d=d):
            for label_name, below, arg, fault in MESHES:
                una(d, label_name, below, arg, fault)
        t = threading.Thread(target=streak_t)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    if set(desktop) == set(DESKTOP):
        c14 = glob.glob(os.path.join(NETWORK11, "11-c14-*.py"))
        if c14:
            t0 = time.time()
            c, t = sudo("cd %s && python3 %s" % (NETWORK11, c14[0]), 1800)
            line_list.append({"lap": o.lap, "test": "T-C14-tutte", "function": "C14",
                          "passed": "sana", "prova": os.path.basename(c14[0]),
                          "desktop": "all_of", "browser": "-", "system_wide": SYSTEM,
                          "commit": meta.get("commit"), "duration_s": round(time.time() - t0),
                          "start": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                          "outcome": {0: "PASS", 1: "FAIL"}.get(c, "BLOCKED"),
                          "rationale": "code %s" % c, "fault_seen": None,
                          "evidence": [], "defect": None})
    put_out(line_list)
    return line_list


# ═══════════════════════════════════════════════════════════════════════════
def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--lap", default="prova")
    a.add_argument("--desktop", default=",".join(DESKTOP))
    a.add_argument("--browser", default=",".join(BROWSER))
    a.add_argument("--prove", default="", help="filter: parts of the name, separated by commas")
    a.add_argument("--no-fault", action="store_true")
    a.add_argument("--technical-layer", action="store_true")
    a.add_argument("--technical-layer-only", action="store_true")
    a.add_argument("--listing", action="store_true")
    a.add_argument("--even-if-someone-is-inside", action="store_true")
    o = a.parse_args()
    o.desktop = [x for x in o.desktop.split(",") if x]
    o.browser = [x for x in o.browser.split(",") if x]
    prove = read_tests(o.prove)
    if o.listing:
        for p in prove:
            print("%-44s %-28s %s%s%s" % (p["label_name"], ",".join(p["functions"]),
                                          "per browser" if p["per_browser"] else "once",
                                          " · LONG" if p["long"] else "",
                                          " · server " + p["server"] if p["server"] else ""))
        return 0
    trouble = keep_boxes("15-giro %s" % o.lap)
    if trouble:
        print("⛔ %s: the round does not start (a hook or a climb would clear out its "
              "tenants, or it theirs)" % trouble)
        return 3
    meta = {"commit": commit()}
    for d in o.desktop:
        meta[d] = fingerprints(d)
        chi = people_inside(d)
        if chi and not o.even_if_someone_is_inside:
            print("⛔ in rete11-%s there is a session of %s: the manual test is not interrupted. "
                  "I stop the round." % (d, ", ".join(chi)))
            return 3
    print("⭐ ROUND %s · %s · %s · %d tests · commit %s · %s" % (
        o.lap, ",".join(o.desktop), ",".join(o.browser), len(prove), meta["commit"],
        " ".join("%s=%s/%s" % (d, meta[d].get("binary"), meta[d].get("page_v"))
                 for d in o.desktop)), flush=True)
    t0 = time.time()
    outcomes = []
    if not o.technical_layer_only:
        test_server(prove, o.desktop, "turn_on")
        try:
            threads = [threading.Thread(target=streak, args=(o, d, prove, meta, outcomes))
                    for d in o.desktop]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        finally:
            test_server(prove, o.desktop, "turn_off")
    if o.technical_layer or o.technical_layer_only:
        outcomes.extend(technical_layer(o, o.desktop, meta))
    count = {}
    for r in outcomes:
        count[r["outcome"]] = count.get(r["outcome"], 0) + 1
    print("\n⏱ round %s: %.0f min · %s" % (o.lap, (time.time() - t0) / 60,
                                         " ".join("%s=%d" % kv for kv in sorted(count.items()))))
    return 1 if count.get("FAIL") else (3 if count.get("BLOCKED") else 0)


if __name__ == "__main__":
    sys.exit(main())
