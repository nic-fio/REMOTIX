#!/usr/bin/env python3
"""check-prelocal - a LOCAL graphical login closes the user's remote desktop FIRST (DECISIONS-11 §11.57), with a real browser (Chrome).

    python3 check-prelocal.py [--box xfce]

Runs ON THE DEV SERVER (lib.py). Uses its own users pl1 (P1-P3, one remote desktop carried through) and pl2 (P4, P5: no desktop).
The boxes are systemd containers with no display manager, so the LOCAL login is SIMULATED: the PAM hook is run as root inside the
box, with the environment pam_exec would give it:
    env -i PAM_TYPE=open_session PAM_SERVICE=prova-dm PAM_USER=<user> XDG_SEAT=seat0 XDG_SESSION_CLASS=user XDG_SESSION_TYPE=wayland
        /usr/libexec/remotix/remotix-local-login
One line per check:  PASS|FAIL|BLOCKED name - evidence.  Exit 0 only if all six PASS.
  P1 hook-closes-desktop  a remote desktop of pl1 is open: the hook returns 0 within 15 s and afterwards nothing of the user is left
                          (no logind session of the service, no program, no unit of the desktop in the user manager), the page
                          was told (0x04), the journal has the request
  P2 new-desktop-after    12 s later (births are refused for 10 s after a request) a new remote login of pl1 gets a working desktop
  P3 hook-ignores         five calls that are not a local graphical login (no seat, close_session, greeter, tty, service remotix):
                          each returns 0 in under 1 s and the desktop of pl1 is still there and alive
  P4 no-desktop           pl2 has no remote desktop: the hook returns 0 in under 2 s
  P5 service-stopped      `systemctl stop remotix`: the hook returns 0 in under 2 s; the service is started again at the end
  P6 pam-line-order       /etc/pam.d/common-session has the pam_exec line of remotix-local-login AFTER the pam_systemd line
Everything is seen from INSIDE the box. FAIL = product (also: page or login refused). BLOCKED = the tool could not look."""
import argparse
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402
from lib import PASS, FAIL, BLOCKED, Fail, ToolError  # noqa: E402

PW = "pl-pass-2026"
NAMES = ("P1-hook-closes-desktop", "P2-new-desktop-after", "P3-hook-ignores", "P4-no-desktop", "P5-service-stopped", "P6-pam-line-order")
HOOK = "/usr/libexec/remotix/remotix-local-login"
FULL = {"PAM_TYPE": "open_session", "PAM_SERVICE": "prova-dm", "XDG_SEAT": "seat0", "XDG_SESSION_CLASS": "user", "XDG_SESSION_TYPE": "wayland"}
# the sessions of a user with the service that opened them (Service=remotix is ours)
SESS = ("for i in $(loginctl list-sessions --no-legend | awk -v u=%(u)s '$3==u{print $1}'); do echo \"@@ $i $(loginctl show-session $i "
        "-p State -p Service -p Seat | tr '\\n' ' ')\"; done; true")
# what the user manager still runs of a desktop (empty when the user manager is gone)
UNITS = ("u=$(id -u %(u)s); systemctl is-active user@$u.service >/dev/null 2>&1 || exit 0; "
         "systemctl --user -M $u@ list-units --state=active --no-legend --no-pager 2>/dev/null "
         "| awk '{print $1}' | grep -E '^(graphical-session\\.target|app-|org\\.gnome\\.|plasma-|xfce|lxqt)' | head -8; "
         "ls /run/user/$u/systemd/user.control 2>/dev/null | head -5; true")
KWIN = "u=$(id -u %(u)s); systemctl --user -M $u@ is-active plasma-kwin_wayland.service 2>&1 | head -1; true"


class Ctx:
    def __init__(self, rig):
        self.rig, self.box, self.t0 = rig, rig.box, int(time.time()) - 5

    def sessions(self, user):
        return [l[3:].strip() for l in self.box.run(SESS % {"u": user})[1].splitlines() if l.startswith("@@ ")]

    def remote_sessions(self, user):
        return [s for s in self.sessions(user) if "Service=remotix" in s]

    def procs(self, user):
        t = self.box.run("ps -u %s -o pid=,comm= | sort -n | head -40; true" % user)[1]
        return [" ".join(l.split()) for l in t.splitlines() if l.strip()]

    def journal(self, grep, n=6):
        return self.box.journal(grep, since="@%d" % self.t0, n=n)

    def hook(self, user, env=None, drop=(), timeout=60):
        """Run the hook as root with exactly that environment; returns (exit status, seconds measured inside the box)."""
        e = dict(FULL if env is None else env)
        e["PAM_USER"] = user
        for k in drop:
            e.pop(k, None)
        args = " ".join("%s=%s" % kv for kv in sorted(e.items()))
        c, t = self.box.run("s=$(date +%%s.%%N); env -i %s %s; rc=$?; e=$(date +%%s.%%N); "
                            "echo \"rc=$rc t=$(awk -v a=$s -v b=$e 'BEGIN{printf \"%%.2f\", b-a}')\"" % (args, HOOK), timeout=timeout)
        m = re.search(r"rc=(\d+) t=([\d.]+)", t)
        if not m:
            raise ToolError("the hook gave no answer line: %s" % t[-150:])
        return int(m.group(1)), float(m.group(2))


# generic helpers of the user manager that a normal Log Out also leaves for a moment (the manager then exits with the last session:
# check-lifecycle waits up to 40 s for NO process and NO logind session at all) — they get the same grace here, a desktop does not
HELPERS = ("remotix", "systemd", "(sd-pam)", "dbus-daemon", "dbus-broker", "pipewire", "wireplumber", "pipewire-pulse", "mpris-proxy", "obexd",
           "gvfsd", "gvfs", "at-spi", "dconf-service", "gpg-agent", "ssh-agent", "gcr-ssh-agent", "gnome-keyring-d", "xdg-desktop-por",
           "xdg-document-po", "xdg-permission-", "tumblerd", "xfconfd", "kded6", "kdeconnectd", "kactivitymanage", "xdg-desktop-portal")


def is_helper(comm):
    return any(comm.startswith(h) for h in HELPERS)


def nothing_left_first(ctx, user, de):
    """The «nothing left» facts after a full close. The FIRST sample, taken at once, must already show no logind session of the
    service, no process of a desktop (only the helpers above), no drop-in of ours in the user manager and, on KDE, plasma-kwin_wayland
    not active. The helpers get `grace` s to go (as check-lifecycle: no process and no session of the user at all 40 s later); desktop
    units of the user manager that are still listed at the first sample are told in the evidence and must be gone within `grace` too.
    Returns (problems, facts)."""
    sess = ctx.remote_sessions(user)
    left = ctx.procs(user)
    progs = [x for x in left if not is_helper(x.split()[-1])]
    units = [x for x in ctx.box.run(UNITS % {"u": user})[1].splitlines() if x.strip()]
    dropins = [x for x in units if not re.match(r"^(graphical-session\.target|app-|org\.gnome\.|plasma-|xfce|lxqt)", x)]
    kwin = ctx.box.run(KWIN % {"u": user})[1].strip() if de == "kde" else ""
    bad = []
    if sess:
        bad.append("at the first sample the logind session(s) of the service were still there: %s" % sess)
    if progs:
        bad.append("at the first sample %d program(s) of the desktop were left: %s" % (len(progs), progs[:10]))
    if dropins:
        bad.append("at the first sample drop-ins left in the user manager: %s" % dropins)
    if kwin == "active":
        bad.append("at the first sample plasma-kwin_wayland.service was still active")
    first = "first sample: %d process(es) (%d helper(s)), %d desktop unit(s) %s" % (
        len(left), len(left) - len(progs), len(units) - len(dropins), [x for x in units if x not in dropins][:6])
    return bad, [first] + (["plasma-kwin_wayland.service \"%s\"" % (kwin or "not there")] if de == "kde" else [])


def nothing_left_wait(ctx, user, grace=40):
    """Then, as check-lifecycle: nothing of the user at all (no process, no logind session, no unit) within `grace` s."""
    bad = []
    t0, end = time.time(), time.time() + grace
    while True:  # the same end as a normal Log Out: nothing of the user at all, unit lists empty
        left, sess = ctx.procs(user), ctx.sessions(user)
        units = [x for x in ctx.box.run(UNITS % {"u": user})[1].splitlines() if x.strip()]
        if (not left and not sess) or time.time() > end:
            break
        time.sleep(2)
    if left or sess or units:
        bad.append("%d s after the hook: %d process(es) %s, logind session(s) %s, unit(s) %s still there" % (grace, len(left), left[:8], sess, units[:6]))
    return bad, ["all gone after %.0f s (no process, no session, no unit)" % (time.time() - t0)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--box", default="xfce", choices=sorted(lib.PORTS))
    a = ap.parse_args()
    res, rig = lib.Results(NAMES), lib.Rig(a.box, "chrome", "pl1", PW, "prelocal")
    ctx = Ctx(rig)
    st = {}

    def login_new(retry=20):
        """Open the page, sign in as pl1, wait for a desktop that shows frames. Returns the page state."""
        rig.open_page()
        ok, s = rig.try_login(retry=retry)
        if not (ok and s["session"] and s["cls"] == "good"):
            raise Fail("pl1 not admitted: \"%s\" (%s); journal: %s" % ((s.get("outcome") or "").strip(), s.get("cls"), ctx.journal("pl1")))
        d = rig.settle(still=1)
        s = rig.state()
        return s, d

    def setup():
        for u in ("pl1", "pl2"):
            ctx.box.ensure_user(u, PW)
        for u in ("pl1", "pl2"):  # an earlier run's session is ended, so that the first login is a NEW one
            ctx.box.run("loginctl terminate-user %s; for i in $(seq 25); do pgrep -u %s >/dev/null || break; sleep 1; done; true" % (u, u), timeout=60)
        if ctx.box.run("test -x %s" % HOOK)[0] != 0:
            raise Fail("%s is not installed in the box" % HOOK)
        rig.start(make_user=False)
        s, d = login_new()
        if "new" not in s["outcome"]:
            raise Fail("base failed: first login of pl1 is not \"new\": \"%s\"" % s["outcome"].strip())
        st["up_t"] = time.time()
        print("setup %s: pl1 desktop up (\"%s\"), logind sessions: %s" % (a.box, s["outcome"].strip(), ctx.sessions("pl1")), flush=True)

    def p1():
        sess0 = ctx.remote_sessions("pl1")
        if not sess0:
            raise Fail("no logind session of the service for pl1 before the hook: %s" % ctx.sessions("pl1"))
        # boxes only: RealtimeKit cannot start in a container and holds a young child's exit for 25 s
        age = time.time() - st["up_t"]
        waited = max(0.0, 31 - age)
        time.sleep(waited)
        t_start = int(time.time()) - 1
        rc, secs = ctx.hook("pl1")
        t_end = st["hook_end"] = time.time()
        bad, ok = [], ["waited %.0f s before the hook (boxes only: RealtimeKit cannot start in a container and holds a young child's exit for 25 s; "
                       "the desktop was %.0f s old)" % (waited, age + waited), "hook exit %d in %.1f s" % (rc, secs)]
        if rc != 0:
            bad.append("the hook exited %d (it must ALWAYS exit 0)" % rc)
        if secs > 15:
            bad.append("the hook took %.1f s (ceiling 15 s)" % secs)
        left_bad, left_ok = nothing_left_first(ctx, "pl1", a.box)
        bad += left_bad
        ok += left_ok
        g, end, f, s = rig.g, time.time() + 20, {}, {}
        while time.time() < end:
            s, f = rig.state(), g.js(lib.JS_FORM)
            if f.get("form") and (s["outcome"] or "").strip():
                break
            time.sleep(1)
        out = (s.get("outcome") or "").strip()
        if not f.get("form"):
            bad.append("the page was NOT told: the sign-in form did not come back in 20 s (outcome \"%s\")" % out)
        elif "precedence" not in out:
            bad.append("the page was told, but not with 0x04 (\"the local session ... took precedence\"): \"%s\"" % out)
        else:
            ok.append("page told with 0x04: \"%s\"" % out)
        # no early login here: a login inside the root side's 10 s refusal gets the page's generic «try again» and a page that
        # retries by itself would get in late (review note 2) — the refusal is in the root side's journal, not judged here
        st["early"] = (None, "not tried")
        # ⚠ evidence only: after a local login's hold the user manager is EXPECTED to stay (the local session is about to use it);
        #    «no process and no session at all» is the criterion of a Log Out with nobody coming, not of this case
        wb, wo = nothing_left_wait(ctx, "pl1", grace=15)
        ok += ["(evidence, not judged) 15 s later: " + "; ".join(wb or wo)]
        # the root side's answer lines for this request
        c, jl = ctx.box.run("journalctl -u remotix --no-pager -o cat --since @%d | grep -E 'scope ended by the root side|nothing of its REMOTIX desktop is left' | tail -4 | cut -c1-260; true" % t_start)
        jl = jl.strip()
        if not jl:
            bad.append("the journal of remotix has no root-side answer line (\"nothing of its REMOTIX desktop is left (N ms\") for the request")
        else:
            if "scope ended by the root side" in jl:
                bad.append("the root side had to end the scope itself (the close was not the child's own full close): %s" % jl.replace("\n", " | "))
            m = re.findall(r"is left \((\d+) ms", jl)
            if m:
                ms = int(m[-1])
                ok.append("root side measured %d ms" % ms)
                if ms > 10000:
                    bad.append("the root side measured %d ms (fail above 10 s; expected under 5 s)" % ms)
                elif ms > 5000:
                    ok.append("(above the 5 s expected)")
            else:
                bad.append("the root side's line has no measured time: %s" % jl.replace("\n", " | "))
            ok.append("journal: " + jl.replace("\n", " | ")[:300])
        jr = ctx.journal("prelocal|local login")
        if jr.startswith("(no remotix journal line"):
            bad.append("the journal of remotix has no line for the request")
        st["p1_ok"] = not bad
        if bad:
            return FAIL, "; ".join(bad) + " | " + "; ".join(ok) + " | sessions of pl1: %s" % ctx.sessions("pl1")
        return PASS, "; ".join(ok)

    def p2():
        if not st.get("p1_ok"):
            raise ToolError("P1 did not close the desktop: nothing to start again from")
        ok_early, early = st.get("early", (None, "not tried"))
        if ok_early:
            raise Fail("a login of pl1 %s: it GOT IN although the root side refuses births of that user for 10 s after the request" % early)
        time.sleep(max(0.0, 12 - (time.time() - st["hook_end"])))  # the root side refuses births for that user for 10 s after a request
        s, d = login_new(retry=30)
        if "new" not in s["outcome"]:
            raise Fail("the desktop after the hook is not a NEW one: \"%s\"" % s["outcome"].strip())
        sess = ctx.remote_sessions("pl1")
        if not sess:
            raise Fail("frames shown but no logind session of the service for pl1")
        return PASS, "early login: " + early + "; 12 s after the hook a new login of pl1 got \"%s\"; shell up %.0f s, picture settled (%s), logind: %s" % (
            s["outcome"].strip(), d["shell_s"], d["desc"], sess)

    def alive(s_before):
        """pl1's desktop is still there: the session of the service, the shell, the page attached."""
        s = rig.state()
        bad = []
        if not ctx.remote_sessions("pl1"):
            bad.append("no logind session of the service for pl1")
        if ctx.box.run(lib.SHELL_UP[a.box] % {"u": "pl1"})[0] != 0:
            bad.append("the desktop shell is gone")
        if not s["session"] or "precedence" in (s["outcome"] or "") or "ended" in (s["outcome"] or ""):
            bad.append("the page lost its session (\"%s\")" % (s["outcome"] or "").strip())
        return bad

    def p3():
        cases = (("no XDG_SEAT", None, ("XDG_SEAT",)),
                 ("PAM_TYPE=close_session", dict(FULL, PAM_TYPE="close_session"), ()),
                 ("XDG_SESSION_CLASS=greeter", dict(FULL, XDG_SESSION_CLASS="greeter"), ()),
                 ("XDG_SESSION_TYPE=tty", dict(FULL, XDG_SESSION_TYPE="tty"), ()),
                 ("PAM_SERVICE=remotix", dict(FULL, PAM_SERVICE="remotix"), ()))
        if not ctx.remote_sessions("pl1"):
            raise ToolError("no desktop of pl1 to leave alone (P2 did not bring one)")
        bad, ok = [], []
        for label, env, drop in cases:
            rc, secs = ctx.hook("pl1", env=env, drop=drop)
            b = []
            if rc != 0:
                b.append("exit %d" % rc)
            if secs >= 1:
                b.append("%.1f s (must be under 1 s)" % secs)
            b += alive(None)
            (bad if b else ok).append("%s: %s" % (label, "; ".join(b) if b else "0 in %.2f s, desktop alive" % secs))
        return (FAIL, "; ".join(bad) + " | ok: " + "; ".join(ok)) if bad else (PASS, "; ".join(ok))

    def p4():
        rc, secs = ctx.hook("pl2")
        if ctx.remote_sessions("pl2"):
            raise ToolError("pl2 has a REMOTIX session: the case is not «no desktop»")
        if rc != 0 or secs >= 2:
            return FAIL, "pl2 has no desktop: the hook exited %d in %.1f s (expected 0 in under 2 s)" % (rc, secs)
        gone = alive(None)
        if gone:
            return FAIL, "pl2's hook touched pl1's desktop: " + "; ".join(gone)
        return PASS, "pl2 without a desktop: hook exit 0 in %.2f s; pl1's desktop still alive" % secs

    def p5():
        try:
            c, t = ctx.box.run("systemctl stop remotix; systemctl is-active remotix", timeout=90)
            if "active" in t.splitlines()[-1:] and "inactive" not in t.splitlines()[-1:]:
                raise ToolError("the service did not stop: %s" % t[-80:])
            rc, secs = ctx.hook("pl2")
        finally:
            ctx.box.run("systemctl start remotix; for i in $(seq 40); do systemctl is-active --quiet remotix && break; sleep 1; done; systemctl is-active remotix", timeout=90)
        c, t = ctx.box.run("systemctl is-active remotix")
        if t.strip() != "active":
            raise ToolError("the service is not active again: \"%s\"" % t.strip())
        if rc != 0 or secs >= 2:
            return FAIL, "service stopped: the hook exited %d in %.1f s (expected 0 in under 2 s)" % (rc, secs)
        return PASS, "service stopped: hook exit 0 in %.2f s; service started again and active" % secs

    def p6():
        c, t = ctx.box.run("grep -nE '^[[:space:]]*session[[:space:]]+[^#]*pam_systemd\\.so' /etc/pam.d/common-session | head -3; echo ---; "
                           "grep -nE '^[[:space:]]*session[[:space:]]+[^#]*pam_exec\\.so.*remotix-local-login' /etc/pam.d/common-session | head -3")
        sd, ex = t.split("---", 1)
        n_sd = [int(l.split(":")[0]) for l in sd.strip().splitlines() if l.strip()]
        n_ex = [int(l.split(":")[0]) for l in ex.strip().splitlines() if l.strip()]
        if not n_ex:
            return FAIL, "common-session has no pam_exec line of remotix-local-login (pam_systemd at line %s)" % (n_sd or "none")
        if not n_sd:
            raise ToolError("common-session has no pam_systemd line to compare with (pam_exec at line %d)" % n_ex[0])
        if n_ex[0] <= n_sd[0]:
            return FAIL, "pam_exec of remotix-local-login (line %d) is NOT after pam_systemd (line %d)" % (n_ex[0], n_sd[0])
        return PASS, "pam_systemd line %d, pam_exec remotix-local-login line %d (after it)" % (n_sd[0], n_ex[0])

    lib.guard(900)
    try:
        try:
            setup()
        except Exception as e:  # noqa: BLE001
            res.rest(FAIL if isinstance(e, Fail) else BLOCKED, str(e) if isinstance(e, Fail) else lib.tool_error(e))
            return 1
        for name, fn in zip(NAMES, (p1, p2, p3, p4, p5, p6)):
            res.attempt(name, fn)
        return res.code()
    finally:
        rig.stop()
        ctx.box.run("systemctl is-active --quiet remotix || systemctl start remotix; true", timeout=60)


if __name__ == "__main__":
    sys.exit(main())
