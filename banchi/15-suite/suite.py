#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
15-suite — THE COMMON BASE OF THE FUNCTIONAL SUITE TESTS (phase 15)
===========================================================================

Each test of the suite is a script `15-fNNN-<name>.py` in this folder.
It can look at ONE function or a group (one session, several functions in a row,
like a real user).  They all speak the same language:

  command line (`call_args()`):
      --container_box gnome|kde|xfce|lxqt   --browser firefox|chrome   (ONE only)
      --fault        after the healthy pass, the pass with the INJECTED FAULT
                      in the same session (outcome reversed: seen = good)
      --certify     only the pure functions (no box, no browser)
      --evidence DIR  where to put photos, console, log (creates it)
      --base-ports N  debug ports of the browsers (Firefox N, Chrome N+1):
                      ⛔ different for each desktop running in parallel
      --host, --largo, --alto (4K by default: the specifications are 4K)

  output: one line per function looked at, which the round collects in the register

      SUITE {"function": "F-004", "passed": "sana"|"fault",
             "outcome": "PASS"|"FAIL"|"BLOCKED", "rationale": "...",
             "expected_val": "...", "observed": "...", "fault_seen": true|false|null,
             "evidence": ["fpath", ...], "version_v": "Firefox 140.x"}

  exit code: 0 all PASS (and the faults seen) · 1 at least one FAIL
                   (or a fault NOT seen) · 3 at least one BLOCKED and no FAIL

⛔ THE RULES OF THE SUITE (fasi/15-suite-funzionale.md):
  - REAL BROWSERS (Firefox with Marionette, Chrome with CDP), real windows in
    the server's screenless labwc at 3840x2160; the Python client does not certify;
  - the judgment comes from the PHOTO or from the value of a FIELD, never from a
    counter («a wrong frame counts as a right one»);
  - BLOCKED = I could not look, WITH THE REASON: a BLOCKED is not a PASS;
  - every test has its INJECTED FAULT: a test that has never given red
    is not a test;
  - every test < 10 minutes;
  - the tenant is named `c15<nnn>u<n>` (C19 and the clear-out recognise it:
    `^c[0-9]+b?u[0-9]+$`) and is ALWAYS cleared out, even if the test falls over.

It relies on (imported, not copied) `12-client-veri.py` (the browser
drivers, `Test`: open_it/enter/first_frame), `12-c20-veri.py` (`Box`:
commands inside the box, server log, create/clear out tenants) and
`11-c21-…` (full-resolution photo, known window, coordinate conversions).
"""
import argparse
import importlib.util as _iu
import json
import os
import random
import re
import secrets
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
BENCHES = os.path.dirname(HERE)


def _load(label_name, file):
    s = _iu.spec_from_file_location(label_name, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


C21 = _load("c21", os.path.join(BENCHES, "11-scatole", "11-c21-sul-bordo-la-forma-cambia.py"))
C20V, REAL = C21.C20V, C21.REAL
GREEN, RED, BLIND = C21.GREEN, C21.RED, C21.BLIND
PORTS = dict(C20V.PORTS)


# ⭐ ON THE SERVER the commands inside the boxes go with LOCAL `sudo podman exec`,
#   not over ssh to the server itself: `[M]` 24 Sep 2026, ten agents together,
#   sshd cut off some of them («Connection closed … port 22») ⇒ tenants not
#   created, BLOCKED that were not the product's (finding of group G7).
def _inside_local(self, row, seconds=90):
    import subprocess
    try:
        r = subprocess.run(["sudo", "-S", "-p", "", "podman", "exec", self.container,
                            "sh", "-c", row], input=_sudo_password(), capture_output=True,
                           text=True, errors="replace", timeout=seconds)
    except subprocess.TimeoutExpired:
        return None, "(no answer in %d s)" % seconds
    return r.returncode, (r.stdout + r.stderr).strip()


if os.environ.get("REMOTIX_ON_SERVER") == "1":
    C20V.Box.inside = _inside_local
DESKTOP = ("gnome", "kde", "xfce", "lxqt")
TENANT_PATTERN = re.compile(r"^c15[0-9]{3}u[0-9]+$")
PASS, FAIL, BLOCKED = "PASS", "FAIL", "BLOCKED"
FROM_CODE = {GREEN: PASS, RED: FAIL, BLIND: BLOCKED}


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
#  THE COMMAND LINE
# ═══════════════════════════════════════════════════════════════════════════
def call_args(doc, extra=None):
    """The common options.  `extra(a)` adds those of the test."""
    a = argparse.ArgumentParser(description=doc,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--container_box", choices=DESKTOP)
    # ⭐ «telefono» = Chrome on the user's REAL phone (phase 19 §5), driven from the
    #   laptop: `banchi/19-android/` (the driver is `telefono.py`)
    a.add_argument("--browser", choices=("firefox", "chrome", "phone"), default="firefox")
    a.add_argument("--fault", action="store_true",
                   help="also the pass with the injected fault, in the same session")
    a.add_argument("--certify", action="store_true",
                   help="only the pure functions: no box, no browser")
    a.add_argument("--evidence", default="")
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--port", type=int, default=0,
                   help="a server other than the box's (short clocks, ban)")
    a.add_argument("--base-ports", type=int, default=0)
    a.add_argument("--is_visible", action="store_true", default=True)
    a.add_argument("--headless", dest="is_visible", action="store_false")
    a.add_argument("--cap-s", type=int, default=45)
    a.add_argument("--largo", type=int, default=3840)
    a.add_argument("--alto", type=int, default=2160)
    if extra:
        extra(a)
    o = a.parse_args()
    if not o.certify and not o.container_box:
        a.error("--container_box is needed (or --certify)")
    if not o.base_ports:
        # ⛔ one pair of ports per desktop: the four run together
        o.base_ports = 3100 + 10 * DESKTOP.index(o.container_box or "gnome")
    if o.evidence:
        os.makedirs(o.evidence, exist_ok=True)
    # the fields that the drivers and `Test` of 12-client-veri expect
    o.url = "https://%s:%d/" % (o.host, o.port or PORTS.get(o.container_box or "gnome"))
    o.scene, o.continuity_s, o.log_cmd = "viva", 8, ""
    o.leave_on = False
    o.store = ""
    if o.browser == "phone":
        o.largo = 0          # the phone does the sizing: no window to size
    return o


# ═══════════════════════════════════════════════════════════════════════════
#  THE OUTCOMES
# ═══════════════════════════════════════════════════════════════════════════
class Outcomes:
    """Collects and prints the SUITE lines; gives the exit code."""

    def __init__(self, o):
        self.o = o
        self.line_list = []
        self.version_v = ""

    def put(self, function, outcome, rationale, expected_val="", observed="",
              evidence=None, passed="sana", fault_seen=None, **other_one):
        if outcome in FROM_CODE:
            outcome = FROM_CODE[outcome]
        assert outcome in (PASS, FAIL, BLOCKED), outcome
        if outcome in (FAIL, BLOCKED) and not rationale:
            rationale = "(no reason given: bench defect)"
        r = {"function": function, "passed": passed, "outcome": outcome,
             "rationale": rationale, "expected_val": expected_val, "observed": observed,
             "fault_seen": fault_seen, "evidence": list(evidence or []),
             "version_v": self.version_v}
        r.update(other_one)
        self.line_list.append(r)
        sign = {PASS: "⭐ PASS", FAIL: "⛔ FAIL", BLOCKED: "⚠ BLOCKED"}[outcome]
        print("   %s %s [%s] %s" % (function, sign, passed, rationale), flush=True)
        print("SUITE " + json.dumps(r, ensure_ascii=False), flush=True)
        return r

    def fault(self, function, seen_v, rationale, **k):
        """⭐ The fault pass: `seen_v` True = the test gave red on the
        fault (good) ⇒ PASS; False ⇒ FAIL (the test cannot give red);
        None ⇒ BLOCKED (it could not be injected or looked at)."""
        outcome = BLOCKED if seen_v is None else (PASS if seen_v else FAIL)
        return self.put(function, outcome, rationale, passed="fault",
                          fault_seen=seen_v, **k)

    def blocked(self, functions, rationale, passed="sana"):
        """All the functions not yet judged become BLOCKED."""
        done = {(r["function"], r["passed"]) for r in self.line_list}
        for f in functions:
            if (f, passed) not in done:
                self.put(f, BLOCKED, rationale, passed=passed)

    def code_v(self):
        e = [r["outcome"] for r in self.line_list]
        if not e:
            return 3
        return 1 if FAIL in e else (3 if BLOCKED in e else 0)


# ═══════════════════════════════════════════════════════════════════════════
#  THE SESSION: tenant, browser, login, first frame
# ═══════════════════════════════════════════════════════════════════════════
class Session:
    """
        with Session(o, "004", outcomes) as s:      # creates c15004u<n>, starts the browser
            ok, reason_text = s.enter()                # page, form, admission, 1st image
            ...  s.g (driver), s.pr (Test), s.sc (Box), s.chi, s.password
    On exit it closes the browser and CLEARS OUT the tenant (even if the test falls over).
    `tenant=False` creates nobody (negative tests: nonexistent user).
    """

    def __init__(self, o, nnn, outcomes, tenant=True, chi=None, password=None):
        # ⚠ REMOTIX_NNN: the tenant's three digits imposed from outside, for the
        #   agents running in parallel on the same box (c15<nnn>u<n>).
        nnn = os.environ.get("REMOTIX_NNN") or nnn
        self.o, self.nnn, self.outcomes = o, nnn, outcomes
        self.sc = C20V.Box(o.container_box)
        self.chi = chi or "c15%su%d" % (nnn, random.randint(100, 999))
        assert TENANT_PATTERN.match(self.chi), self.chi
        self.password = password or "c15-" + secrets.token_hex(6)
        self.create_tenant = tenant
        self.g = None
        self.pr = None
        self._photo = 0

    # -- life cycle -----------------------------------------------------------
    def __enter__(self):
        self.o.username = self.chi
        if self.create_tenant:
            self.sc.clear_out(self.chi)
            c, t = self.sc.create(self.chi, self.password)
            if c != 0:
                raise Blocked("I could not create the tenant %s: %s" % (self.chi, t[-200:]))
            # ⛔ the REAL `~/.cache` (src/provisiona.sh, 25 Aug 2026): in the gnome
            #   box `/etc/skel/.cache` points to /tmp, and the first tenant that opens
            #   firefox-esr takes /tmp/mozilla with mode 0700 ⇒ for the others
            #   «Your Firefox profile cannot be loaded» (finding G5, 25 Sep 2026)
            self.sc.inside("h=/home/%s; [ -L $h/.cache ] && rm -f $h/.cache; "
                           "install -d -o %s -g %s -m 700 $h/.cache" % (
                               self.chi, self.chi, self.chi), 30)
        self.turn_on_browser()
        return self

    def __exit__(self, kind, val, tb):
        self.turn_off_browser()
        if self.create_tenant:
            try:
                self.sc.clear_out(self.chi)
            except Exception as e:               # noqa: BLE001
                print("   ⚠ clear-out of %s: %s" % (self.chi, e))
        return False

    def turn_on_browser(self):
        try:
            if self.o.browser == "phone":
                self.g = phone().PhoneDriver(self.o)
            else:
                self.g = REAL.turn_on_driver(self.o.browser, self.o)
        except Exception as e:                   # noqa: BLE001
            raise Blocked("the browser did not start: %s" % str(e)[:300])
        try:
            self.outcomes.version_v = self.g.stage()
        except Exception:                        # noqa: BLE001
            self.outcomes.version_v = self.o.browser
        if self.o.largo:
            try:
                print("   %s" % C20V.resize_to(self.g, self.o.browser, self.o.largo,
                                               self.o.alto), flush=True)
            except Exception as e:               # noqa: BLE001
                print("   ⚠ resize_to: %s" % e)
        self.pr = REAL.Test(self.g, self.o, self.o.url, self.password)

    def turn_off_browser(self):
        if self.g is not None:
            try:
                self.g.shut()
            except Exception as e:               # noqa: BLE001
                print("   ⚠ closing the browser: %s" % e)
            self.g = None

    # -- the login ------------------------------------------------------------
    def enter(self, password=None, open_it=True):
        """(True, reason) if: page open, form, admitted, first frame
        not degenerate.  Otherwise (False, reason)."""
        if open_it:
            ok, m = self.pr.open_it()
            if not ok:
                return False, "the page does not open: " + m
        e, m, _s = self.pr.enter(password or self.password)
        if e != GREEN:
            return False, "the login: " + m
        e, m, s = self.pr.first_frame()
        e, m = C20V.desktop_dark_but_alive(e, m, s)
        if e != GREEN:
            return False, "the first frame: " + m
        return True, m

    def state(self):
        return self.pr.state()

    # -- the photos -----------------------------------------------------------
    def picture(self, label_name):
        """⭐ The canvas at FULL resolution: (png | None, path | reason).
        Saved in the evidence if there is any."""
        try:
            png = C21.full_photo(self.g)
        except Exception as e:                   # noqa: BLE001
            return None, "photo failed: %s" % str(e)[:200]
        if not png:
            return None, "the canvas is not there or has no visible area"
        self._photo += 1
        fpath = ""
        if self.o.evidence:
            fpath = os.path.join(self.o.evidence, "%02d-%s.png" % (self._photo, label_name))
            with open(fpath, "wb") as f:
                f.write(png)
        return png, fpath

    def geometry(self):
        """The geometry of the canvas in the glass (C21.JS_GEOMETRY)."""
        return self.g.js(C21.JS_GEOMETRY)

    # -- the server -----------------------------------------------------------
    def log_mark(self):
        return self.sc.log_line_list()

    def log_from(self, sign):
        return self.sc.log_from(sign or 0, self.chi)

    def save_text(self, label_name, line_list):
        if not self.o.evidence:
            return ""
        p = os.path.join(self.o.evidence, label_name)
        with open(p, "w") as f:
            f.write("\n".join(line_list) if isinstance(line_list, (list, tuple)) else str(line_list))
        return p

    def save_console(self):
        """The browser's JS and network errors, in the evidence."""
        try:
            js, net, _ = self.g.errors_out()
        except Exception as e:                   # noqa: BLE001
            js, net = ["(not read: %s)" % e], []
        return self.save_text("console-%s.txt" % self.o.browser, js + net)

    def as_user(self, command, seconds=60):
        return self.sc.as_user(self.chi, command, seconds)

    def in_session(self, command, seconds=60, background=True):
        """Runs `command` as the tenant INSIDE their graphical session
        (WAYLAND_DISPLAY of their compositor, session bus).  `background` detaches
        it (setsid … &) and returns at once."""
        amb = ("u=$(id -u %(c)s); d=$(ls /run/user/$u 2>/dev/null | grep -E '^wayland-[0-9]+$' "
               "| head -1); [ -n \"$d\" ] || { echo 'no wayland socket'; exit 2; }; "
               % {"c": self.chi})
        body_el = ("runuser -u %(c)s -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
                 "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
                 "XDG_SESSION_TYPE=wayland HOME=/home/%(c)s sh -c %(q)s"
                 % {"c": self.chi, "q": _q(command)})
        if background:
            body_el = "setsid %s < /dev/null > /home/%s/.c15-%s.log 2>&1 & echo launched" % (
                body_el, self.chi, re.sub(r"\W", "", command.split()[0])[:20])
        return self.sc.inside(amb + body_el, seconds)


class Blocked(Exception):
    """The test could not look: it becomes BLOCKED with this reason."""


_PHONE = []


def phone():
    """The module of the real phone's driver (`banchi/19-android/telefono.py`),
    loaded only once and only by whoever uses it."""
    if not _PHONE:
        _PHONE.append(_load("phone", os.path.join(BENCHES, "19-android", "telefono.py")))
    return _PHONE[0]


def _q(s):
    return "'" + s.replace("'", "'\"'\"'") + "'"


# ═══════════════════════════════════════════════════════════════════════════
#  THE BODY OF EVERY TEST
# ═══════════════════════════════════════════════════════════════════════════
def execute(doc, functions, body_el, certify=None, extra=None):
    """The `main` of every test.

    functions   the F-NNN the test looks at (for the automatic BLOCKEDs)
    body_el(o, outcomes)       the real test: puts the outcomes with `outcomes.put`
    certify()           the pure functions: returns 0 if all right
    """
    o = call_args(doc, extra)
    if o.certify:
        if not certify:
            print("⚠ this test has no pure functions to certify")
            return 0
        return certify()
    outcomes = Outcomes(o)
    t0 = time.time()
    print("⭐ %s · %s · %s · %s%s" % (os.path.basename(sys.argv[0]), o.container_box, o.browser,
                                      o.url, " · + FAULT" if o.fault else ""), flush=True)
    try:
        body_el(o, outcomes)
    except Blocked as b:
        outcomes.blocked(functions, str(b))
        if o.fault:
            outcomes.blocked(functions, str(b), passed="fault")
    except Exception as e:                       # noqa: BLE001
        tb = traceback.format_exc()
        print(tb)
        outcomes.blocked(functions, "the bench fell over: %r" % e)
        if o.fault:
            outcomes.blocked(functions, "the bench fell over: %r" % e, passed="fault")
    outcomes.blocked(functions, "the test gave no judgment (bench defect)")
    if o.fault:
        outcomes.blocked(functions, "the fault pass gave no judgment",
                       passed="fault")
    print("⏱ %.0f s · code_v %d" % (time.time() - t0, outcomes.code_v()), flush=True)
    return outcomes.code_v()
