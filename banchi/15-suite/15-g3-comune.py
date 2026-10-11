#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-g3-comune — the common helper of the three tests of group G3 (F-005, F-006,
F-008): the meshes C21, C22, C23 of phase 14 inside the suite.

⛔ The meshes are IMPORTED, not copied: their observation and
   judgment functions (`C21.osserva`, `C22.test_browser`, `C22.scansiona`,
   `C23.manda`, `C23.snapshot_and_read`, …) run as they are.  Only one
   thing must change: `osserva` and `test_browser` start the browser BY THEMSELVES
   (`VERI.turn_on_driver`) and close it at the end; in the suite the browser and
   the tenant are held by `suite.Sessione`.  ⇒ `borrowed_driver()` lends the
   mesh the session's browser, with a `chiudi()` that does not close: the
   session stays alive for the fault pass and for the extra observations.
"""
import contextlib
import glob
import importlib.util as _iu
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


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
sys.path.insert(0, HERE)
import suite as S                                                     # noqa: E402

SCATOLE = os.path.join(S.BENCHES, "11-scatole")


def patience_ssh(box_cls):
    """⚠ `[M]` 24 Sep 2026, 10 agents on the server: `Box.dentro` goes through an
    ssh from the server to itself, and sshd (MaxStartups 10:30:100) randomly closes
    the not yet authenticated connections («Connection closed by … port
    22»).  The command in that case did NOT start (it closes before
    the login) ⇒ it can be repeated.  It is retried up to 12 times (about two minutes)."""
    if getattr(box_cls, "_g3_patience", False):
        return
    original = box_cls.inside

    def inside(self, line, seconds=90):
        for i in range(12):
            c, t = original(self, line, seconds)
            if c is not None or "Connection closed by" not in (t or "") \
                    and "Connection reset" not in (t or ""):
                return c, t
            time.sleep(1 + 2 * min(i, 8) + 2 * random.random())
        return c, t
    box_cls.inside = inside
    box_cls._g3_patience = True


patience_ssh(S.C20V.Box)


def load_mesh(name, file):
    s = _iu.spec_from_file_location(name, os.path.join(SCATOLE, file))
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    patience_ssh(m.C20V.Box)
    return m


class Loan:
    """The session's browser, lent to a mesh: everything goes through, except
    `close()` (the Sessione closes it, on exit)."""

    def __init__(self, g):
        self.__dict__["_g"] = g

    def close(self):
        return None

    def __getattr__(self, name):
        return getattr(self.__dict__["_g"], name)


@contextlib.contextmanager
def borrowed_driver(genuine, g):
    """Inside the block `genuine.turn_on_driver(...)` returns the session's browser `g`
    (on loan).  ⚠ `genuine` is the `12-client-veri` module THAT THE
    MESH USES: every loaded mesh carries its own."""
    old = genuine.turn_on_driver
    genuine.turn_on_driver = lambda name, o: Loan(g)
    try:
        yield
    finally:
        genuine.turn_on_driver = old


def cache_fix(sc, chi):
    """⭐ The REAL `~/.cache` for the tenant — the cure of `src/provisiona.sh`, with
    the lines of `11-c8….applica_la_cura` (which runs INSIDE the box: here it is
    sent with `sc.dentro`), and the write test of `sa_scrivere_nella_cache`.

    `[M]` 24 Sep 2026, rete11-gnome: `/etc/skel/.cache -> /tmp` (the user's
    choice, `DECISIONI.md` §4.6-undecies, reproduced in the box) ⇒ the
    first tenant that opens `firefox-esr` takes `/tmp/mozilla` with mode 0700
    and all the others see «Your Firefox profile cannot be loaded».  C21-C23
    did not do it: in phase 14 they ran alone.  With ten agents on the
    same box the test window is no longer born ⇒ bench BLOCKED."""
    c = "/home/%s/.cache" % chi
    cod, t = sc.inside(
        "[ -L %s ] && rm -f %s; mkdir -p %s; chown %s:%s %s; chmod 700 %s; "
        "su -s /bin/sh -c 'mkdir -p ~/.cache/mozilla/.prova-g3 && "
        "rmdir ~/.cache/mozilla/.prova-g3' %s && echo scrive"
        % (c, c, c, chi, chi, c, c, chi), 60)
    return cod == 0 and "scrive" in (t or ""), (t or "")[-200:]


def prepare_o(o, s):
    """The fields the meshes read from `o` and that `suite.argomenti` does not set;
    ⚠ the real `~/.cache` for the tenant is now given by `suite.Sessione` (25 Sep):
    `cache_fix` remains only as a diagnosis, it is no longer called."""
    o.password = s.password
    o.user = s.chi
    o.save = o.evidence or ""
    if not hasattr(o, "wait_window"):
        o.wait_window = 60


def new_evidence(o, before):
    """The files that appeared in the evidence after `before` (a set of paths)."""
    if not o.evidence:
        return []
    return sorted(set(glob.glob(os.path.join(o.evidence, "*"))) - set(before))


def evidence_now(o):
    return set(glob.glob(os.path.join(o.evidence, "*"))) if o.evidence else set()


FAULT_FROM_OUTCOME = {S.GREEN: True, S.RED: False, S.BLIND: None}


def arguments_g3(a):
    # ⚠ `[M]` 25 Sep: with Chrome a photo at scale 1 in 4K (+ the search for the
    #   cyan) costs 10-20 s under load: in 60 s two STILL photos in a row do not
    #   always fit ⇒ BLOCKED «the window is not seen» with the window there.
    a.add_argument("--wait-window", type=int, default=150,
                   help="how long to wait for the test window to appear still")


# ─────────────────────────────────────────────────────────────────────────────
#  IS THE SCENE STILL ALIVE?  (so as not to blame the product for the server)
# ─────────────────────────────────────────────────────────────────────────────
# `[M]` 24 Sep 2026, evening: ten agents on the server, 31 GB, no swap ⇒
#   the server's OOM-killer killed processes; in the same minute the
#   `firefox-esr` windows of two scenes vanished (F-006 and F-008, gnome).  A
#   red case with the scene dead is NOT a red of the product: it is BLOCKED.
def scene_alive(sc, chi):
    c, t = sc.inside("pgrep -u %s -f '[f]irefox-esr' >/dev/null && echo viva || echo morta"
                     % chi, 30)
    return "alive" in (t or "")


def killed_by_server():
    """The «Killed process» lines of the kernel log of the server (where the
    test runs): they are compared before and after.  [] if they cannot be read."""
    import subprocess
    try:
        r = subprocess.run(["sudo", "-S", "-p", "", "dmesg"], input=_sudo_password(),
                           capture_output=True, text=True, timeout=20)
        return [x for x in r.stdout.splitlines() if "Killed process" in x]
    except Exception:                            # noqa: BLE001
        return []


def new_killed(before):
    after = killed_by_server()
    return after[len(before):] if len(after) >= len(before) else after


def explain_blind(before_oom):
    """One more sentence for a BLOCKED: did the OOM-killer work in the meantime?"""
    n = new_killed(before_oom)
    if not n:
        return ""
    return (" — ⚠ during the test the SERVER's OOM-killer killed %d processes (%s)"
            % (len(n), "; ".join(x.split("Killed process")[-1].split(" total-vm")[0].strip()
                                 for x in n[-3:])))


def trace_search(c21):
    """Diagnosis: every outcome of `find_window` printed (cyan rectangle and
    right edge), to understand why two photos in a row do not come back still."""
    if getattr(c21, "_g3_trace", False):
        return
    orig = c21.find_window

    def find(*a, **k):
        t0 = time.time()
        f, why = orig(*a, **k)
        print("      [search %.1fs] %s" % (time.time() - t0, ("cyan %s right %s" % (
            f["ciano"], f["destro"])) if f else why), flush=True)
        return f, why
    c21.find_window = find
    c21._g3_trace = True
