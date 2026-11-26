#!/usr/bin/env python3
"""check-resilience - the session survives what goes wrong around it, on a running REMOTIX box, with real browsers (Chrome).
SPECS 5.1 (one session per user), 5.2 (the session survives the client; the service's restart closes it, §11.56), 5.3 (the three clocks).

    python3 check-resilience.py [--box xfce] [--only a,b] [--reps 5]

Runs ON THE DEV SERVER (lib.py; the nft rule of network-drop needs `sudo` on the host, empty password). Own users rs1..rs5 and
rs10..rs14, made here; a login with a user that may not exist is never tried (a wrong login counts for the ban).
One line per check:  PASS|FAIL|BLOCKED <name> - evidence ;  exit 0 only if all PASS.
  service-restart          rs1 attached, a test window holds text; `systemctl restart remotix`; the page is told / goes back to the
                           form; the desktop was CLOSED with the service (DECISIONS-11 §11.56): no logind session of the service,
                           the old window pid gone, the root side says «no orphan desktops: … the service stops clean»; log in
                           again: a NEW session ("new") with a working desktop (shell up, picture settled)
  network-drop             rs2 attached; all UDP of the box's port is dropped (own nft table) for longer than the silence clock
                           (spec 30 s; code 10 s "dead-line"); the rule is removed (always); at once rs2 logs in again: not refused
                           (the slot is free), "resumed", same window pid, same text
  simultaneous-first-login the SAME fresh user logs in from two browsers at the same instant (threads, delta reported), 5 times
                           (rs10..rs14): exactly one admitted with a working desktop (picture, mouse, keys); the other refused
                           with the 0x0F sentence (SPECS 5.1 second row); every rep is told in the evidence
  login-after-other-logout rs3 and rs4 attached; rs3 does the desktop's Log Out: rs4 untouched (same window pid, session good,
                           input works); rs3 logs in again: a NEW session, a new window
  clocks                   SPECS 5.3: the start-up line of the service gives the clocks in force (30 s fixed, 1800 s, 3600 s);
                           then the MECHANISM at short values (--inactivity-s 30 --abandon-s 90 through a drop-in that is
                           ALWAYS removed): the client is told at ~30 s without input and the programs stay; at ~90 s the
                           session is closed (programs gone, no logind session) and a new login is NEW
FAIL = the product did not do it.  BLOCKED = the tool could not look.  Pictures: <prove>/shots/resil-*.png."""
import argparse
import importlib.util
import os
import re
import socket
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402
from lib import PASS, FAIL, Fail, ToolError  # noqa: E402

_spec = importlib.util.spec_from_file_location("check_lifecycle", os.path.join(lib.HERE, "check-lifecycle.py"))
LC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(LC)  # the helpers of check-lifecycle (enter, probe, judge_back, Ctx, LOGOUT...): not copied

PW = "rs-pass-2026"
NAMES = ("service-restart", "network-drop", "simultaneous-first-login", "login-after-other-logout", "clocks")
DROP_S = 40            # longer than the 30 s of the silence clock of SPECS 5.1/5.3
CLOCKS_DROPIN = "/etc/remotix/remotix.conf.d/90-resil-clocks.conf"
RACE_REPS = ("rs10", "rs11", "rs12", "rs13", "rs14")


# ------------------------------------------------------------------------------------------------ small helpers
def reset_user(box, u):
    """Only my own users: a session left by an earlier run is ended, so that the first login is a NEW one."""
    box.end_users([u], cap=25)


def really_gone(box, u):
    """A session of u left by an earlier run must be GONE (processes and logind), else the first login is a "resumed" one: SIGKILL what is left."""
    if box.end_users([u]):  # a user that does not exist has no session: nothing to end
        raise ToolError("cannot get rid of the earlier session of %s" % u)


def wait_port(boxname, cap=40):
    """The service answers on its page port (again, after a restart)."""
    end = time.time() + cap
    while time.time() < end:
        try:
            socket.create_connection(("127.0.0.1", lib.PORTS[boxname]), timeout=3).close()
            return True
        except OSError:
            time.sleep(1)
    return False


def jlog(box, since, grep, n=8):
    return box.journal(grep, since="@%d" % int(since), n=n)


def alive(box, pid):
    return box.run("kill -0 %s 2>/dev/null && echo alive; true" % pid)[1].strip() == "alive"


def bring_up(a, box, rig, user, typed):
    """Fresh user, first login (NEW), desktop settled, test window, `typed` in it. Returns (ctx, text0, pid0)."""
    reset_user(box, user)
    box.ensure_user(user, PW)
    rig.user, rig.password = user, PW
    if rig.env is None:
        rig.start(make_user=False)
    else:
        rig.new_browser()
    ctx = LC.Ctx(rig)
    s, tries, dt = LC.enter(ctx)
    if not (s["session"] and s["cls"] == "good"):
        raise Fail("first login of %s not admitted: \"%s\" (%s); journal: %s" % (user, s["outcome"].strip(), s["cls"], ctx.journal(user)))
    if "new" not in s["outcome"]:
        raise Fail("first login of %s is not \"new\": \"%s\"" % (user, s["outcome"].strip()))
    rig.settle(still=1)
    rig.start_window()
    ev, png = LC.probe(ctx, typed, 0.5, 0.5)
    text0 = ([e["text"] for e in ev if e["ev"] == "text"] or [""])[-1]
    pid0 = rig.win_pid()
    if text0 != typed or not pid0:
        raise Fail("base failed: typed \"%s\", the window of %s holds \"%s\" (pid %s)" % (typed, user, text0, pid0))
    return ctx, text0, pid0


def back_in(ctx, text0, pid0, typed, retry=0, fxy=(0.4, 0.4), shot=None):
    """New browser, log in again as the same user: (bad, ok, tries, seconds). Not admitted = a Fail."""
    rig = ctx.rig
    rig.new_browser()
    s, tries, dt = LC.enter(ctx, retry=retry)
    if not (s["session"] and s["cls"] == "good"):
        raise Fail("login again of %s not admitted after %d try(ies), %.0f s: \"%s\" (%s); remotix journal: %s" % (
            rig.user, tries, dt, s["outcome"].strip(), s["cls"], ctx.journal(rig.user)))
    d = rig.settle(still=1, shell=False)
    s = d["s"]
    s["outcome"] = rig.state()["outcome"]
    ev, png = LC.probe(ctx, typed, fxy[0], fxy[1])
    bad, ok, txt = LC.judge_back(ctx, s, ev, png, pid0, text0, typed, fxy[0], fxy[1])
    if shot:
        lib.save_png(shot, png)
    return bad, ok, tries, dt


def page_told(rig, cap, match=None):
    """Wait until the page says a farewell sentence (matching `match`; form back or class bad): (seconds, form, outcome) or None."""
    t0 = time.time()
    while time.time() - t0 < cap:
        try:
            st, f = rig.state(), rig.g.js(lib.JS_FORM)
        except Exception:  # noqa: BLE001 - a page that is gone is not a page that tells
            time.sleep(1)
            continue
        out = (st["outcome"] or "").strip()
        # told = the page says a sentence in the "bad" colour or is back at the form (the page keeps `session` set after a farewell)
        if (f.get("form") or st["cls"] == "bad") and out and (match is None or re.search(match, out)):
            return time.time() - t0, bool(f.get("form")), out
        time.sleep(1)
    return None


class DeadLine:
    """An nft table of OURS that drops all UDP from/to the box's REMOTIX port (browser and server share the host, so the packets
    cross `lo`): the client's traffic is cut without a close, the TCP page stays. Always removed (finally; also at start, for a
    leftover of a run that was killed)."""

    def __init__(self, boxname):
        self.port = lib.PORTS[boxname]
        self.table = "rx_resil_%d" % self.port

    def _sudo(self, *args):
        r = subprocess.run(["sudo", "-S", "-p", ""] + list(args), input="\n", capture_output=True, text=True, timeout=30)
        return r.returncode, (r.stdout + r.stderr).strip()

    def remove(self):
        self._sudo("nft", "delete", "table", "inet", self.table)
        return self.table not in self._sudo("nft", "list", "tables")[1]

    def put(self):
        self.remove()
        p = self.port
        rules = ("table inet %s {\n chain i { type filter hook input priority -10; policy accept;\n  udp dport %d drop\n  udp sport %d drop\n }\n"
                 " chain o { type filter hook output priority -10; policy accept;\n  udp dport %d drop\n  udp sport %d drop\n }\n}\n" % (self.table, p, p, p, p))
        os.makedirs(lib.WORK, exist_ok=True)
        path = os.path.join(lib.WORK, "resil-%d.nft" % p)
        open(path, "w").write(rules)
        c, t = self._sudo("nft", "-f", path)  # from a FILE: with sudo already authenticated stdin is not consumed
        if c:
            raise ToolError("cannot place the nft rule: %s" % t[-150:])


# ------------------------------------------------------------------------------------------------ the checks
REMOTE_SESS = ("for i in $(loginctl list-sessions --no-legend | awk -v u=%s '$3==u{print $1}'); do "
               "[ \"$(loginctl show-session $i -p Service --value)\" = remotix ] && echo $i; done; true")


def check_restart(a, box, tag):
    """§11.56: the desktops are closed with the service. After the restart: told, nothing orphaned, a NEW session on login."""
    rig = lib.Rig(a.box, "chrome", "rs1", PW, tag, cap=a.cap)
    try:
        ctx, text0, pid0 = bring_up(a, box, rig, "rs1", "resil")
        t0 = time.time()
        # the restart's own stderr is kept apart (RXERR) so that a FAIL can show it; only systemd's «changed on disk» warning is taken out of the text
        c, t = box.run("systemctl restart remotix 2>/tmp/rx-restart.err; sleep 2; echo RXERR; grep -v 'changed on disk' /tmp/rx-restart.err; rm -f /tmp/rx-restart.err; "
                       "echo RXSTATE; systemctl is-active remotix 2>/dev/null", timeout=90)
        state = t.split("RXSTATE")[-1].strip().splitlines()[-1:]
        if state != ["active"]:
            raise Fail("the service is not active after the restart: state %s; restart error: %s" % (state, " ".join(t.split("RXERR")[-1].split("RXSTATE")[0].split())[:200] or "(none)"))
        told = page_told(rig, 45)
        up = wait_port(a.box)
        if not told:
            st = rig.state()
            return FAIL, "the client was NOT told after the restart in 45 s (session=%s, outcome \"%s\"); service port back: %s; journal: %s" % (
                st["session"], st["outcome"].strip(), up, jlog(box, t0, "rs1|client|dead-line", 6))
        if not up:
            raise Fail("the page port does not answer 40 s after the restart")
        bad, ok = [], []
        ok.append("restart: client told after %.0f s with \"%s\" (form %s)" % (told[0], told[2][:80], "back" if told[1] else "NOT shown"))
        if not told[1]:
            bad.append("the sign-in form did not come back after the farewell")
        # nothing orphaned: no REMOTIX session of rs1 and the old window process gone (a few seconds are allowed)
        t1 = time.time()
        while True:
            sess = box.run(REMOTE_SESS % "rs1")[1].split()
            old = alive(box, pid0)
            if (not sess and not old) or time.time() - t1 > 10:
                break
            time.sleep(1)
        if sess:
            bad.append("logind session(s) %s of rs1 with Service=remotix still there %.0f s after the restart (orphaned desktop)" % (sess, time.time() - t1))
        if old:
            bad.append("the old window process %s is still alive after the restart (the desktop was not closed with the service)" % pid0)
        if not sess and not old:
            ok.append("%.0f s after the restart rs1 has no session of the service and the old window pid %s is gone" % (time.time() - t1, pid0))
        # the root side's verdict
        c, jl = box.run("journalctl -u remotix --no-pager -o cat --since '@%d' | grep -F 'no orphan desktops' | tail -3 | cut -c1-240; true" % int(t0))
        jl = jl.strip()
        if "still have processes" in jl:
            bad.append("the root side found orphan desktops: %s" % jl.replace("\n", " | "))
        elif "the service stops clean" in jl:
            ok.append("journal: " + jl.replace("\n", " | "))
        else:
            bad.append("no root-side line «no orphan desktops: … the service stops clean» in the journal since the restart (got: %s)" % (jl or "nothing"))
        # a NEW session with a working desktop
        rig.new_browser()
        s, tries, dt = LC.enter(ctx, retry=60)
        if not (s["session"] and s["cls"] == "good"):
            raise Fail("login again of rs1 not admitted after %d try(ies), %.0f s: \"%s\" (%s); remotix journal: %s" % (
                tries, dt, s["outcome"].strip(), s["cls"], ctx.journal("rs1")))
        out = rig.state()["outcome"].strip()
        if "new" not in out or "resumed" in out:
            bad.append("login again is not a NEW session: \"%s\"" % out)
        try:
            d = rig.settle(still=1)
            ok.append("login again: \"%s\", %d try(ies), %.0f s; shell up after %.0f s, picture settled (%s)" % (out, tries, dt, d["shell_s"], d["desc"]))
            lib.save_png("resil-%s-restart.png" % a.box, d["png"])
        except Fail as e:
            bad.append("the new desktop did not come up: %s" % e)
        return (FAIL if bad else PASS), "; ".join(bad + ["--"] + ok if bad else ok) + (" | remotix journal: " + jlog(box, t0, "rs1", 8) if bad else "")
    finally:
        rig.stop()


def check_drop(a, box, tag):
    rig = lib.Rig(a.box, "chrome", "rs2", PW, tag, cap=a.cap)
    nft = DeadLine(a.box)
    try:
        ctx, text0, pid0 = bring_up(a, box, rig, "rs2", "drop")
        t0 = time.time()
        try:
            nft.put()
            t_cut = time.time()
            time.sleep(DROP_S)
        finally:
            gone = nft.remove()
        if not gone:
            raise ToolError("the nft table %s is STILL THERE: remove it by hand (sudo nft delete table inet %s)" % (nft.table, nft.table))
        dead = box.run("journalctl -u remotix --no-pager -o short-unix --since '@%d' | grep -iE 'dead-line|silen' | grep -v 'rate of' | head -3 | cut -c1-200; true" % t0)[1]
        m = re.search(r"^(\d+)\.\d+ .*dead-line", dead, re.M)
        when = ("%.0f s after the cut" % (int(m.group(1)) - t_cut)) if m else "NO dead-line line in the journal"
        try:
            bad, ok, tries, dt = back_in(ctx, text0, pid0, "ping", retry=0, shot="resil-%s-drop.png" % a.box)
        except Fail as e:
            raise Fail("%s (the line had been cut %d s, the server's own verdict: %s; the slot should be free after the silence clock)" % (e, DROP_S, when))
        ok.append("line cut %d s (UDP port %d), server's own verdict: %s; login right after the cut: %d try(ies), %.0f s" % (DROP_S, nft.port, when, tries, dt))
        return (FAIL if bad else PASS), "; ".join(bad + ["--"] + ok if bad else ok) + ("; journal: " + dead.replace("\n", " | ") if bad else "")
    finally:
        nft.remove()
        rig.stop()


def _enter_when(rig, barrier, out, k, user):
    barrier.wait()
    out[k] = time.time()
    try:
        rig.g.js(lib.JS_ENTER, user, PW)
    except Exception as e:  # noqa: BLE001
        out[k + "err"] = repr(e)


def race_once(a, box, rigs, user, n):
    """One rep: (ok, text). A product failure is (False, evidence)."""
    t_rep = time.time()
    really_gone(box, user)
    box.ensure_user(user, PW)
    for r in rigs:
        r.user, r.password = user, PW
        if r.env is None:
            r.start(make_user=False)
        else:
            r.new_browser()
        r.open_page()
    barrier, stamp = threading.Barrier(2), {}
    th = [threading.Thread(target=_enter_when, args=(r, barrier, stamp, k, user)) for r, k in zip(rigs, "AB")]
    for t in th:
        t.start()
    for t in th:
        t.join(30)
    if "Aerr" in stamp or "Berr" in stamp:
        raise ToolError("a submit failed: %s" % {k: v for k, v in stamp.items() if k.endswith("err")})
    delta = abs(stamp["A"] - stamp["B"]) * 1000
    t_sub, sts = time.time(), {}
    while time.time() - t_sub < a.cap:
        sts = {k: r.state() for r, k in zip(rigs, "AB")}
        # settled = the page said its sentence (the class "good" alone is the transient "checking" state)
        done = {k: bool(s["outcome"].strip()) and (s["session"] or s["cls"] == "bad") for k, s in sts.items()}
        if all(done.values()):
            break
        if any(s["session"] and s["cls"] == "good" and s["outcome"].strip() for s in sts.values()) and time.time() - t_sub > 10:
            break
        time.sleep(0.3)
    sts = {k: r.state() for r, k in zip(rigs, "AB")}
    adm = [k for k, s in sts.items() if s["session"] and s["cls"] == "good" and s["outcome"].strip()]
    ref = [k for k in "AB" if k not in adm]
    head = "rep %d (%s, submits %.2f ms apart)" % (n, user, delta)
    if len(adm) != 1:
        return False, "%s: %d admitted (A \"%s\" B \"%s\"); journal: %s" % (
            head, len(adm), sts["A"]["outcome"].strip()[:70], sts["B"]["outcome"].strip()[:70], jlog(box, t_rep, user, 8))
    win = dict(zip("AB", rigs))[adm[0]]
    lose = sts[ref[0]]
    if "taken by another client" not in lose["outcome"]:
        return False, "%s: the second is not refused with the 0x0F sentence but \"%s\" (%s); journal: %s" % (
            head, lose["outcome"].strip()[:90], lose["cls"], jlog(box, t_rep, user, 8))
    # the user is fresh (really_gone), so a "resumed" winner is the attempt that found the session the OTHER attempt had begun to
    # create: the sentence is noted in the evidence, not judged (SPECS 5.1 asks for one admitted and one refused)
    ctx = LC.Ctx(win)
    try:
        win.settle(still=1)
        win.start_window()
        ev, png = LC.probe(ctx, "race", 0.5, 0.5)
    except Fail as e:
        try:
            lib.save_png("resil-%s-race%d.png" % (a.box, n), win.canvas_png())
        except Exception:  # noqa: BLE001
            pass
        return False, "%s: winner %s admitted (\"%s\") but %s; journal: %s; picture shots/resil-%s-race%d.png" % (
            head, adm[0], sts[adm[0]]["outcome"].strip()[:60], e, jlog(box, t_rep, "ScreenCast|RemoteDesktop|Mutter|error|fail|refus", 6), a.box, n)
    lib.save_png("resil-%s-race%d.png" % (a.box, n), png)
    cl = [e for e in ev if e["ev"] == "click"]
    tx = ([e["text"] for e in ev if e["ev"] == "text"] or [""])[-1]
    if not cl or tx != "race":
        return False, "%s: desktop of the winner up but input broken: %d click event(s), text \"%s\"" % (head, len(cl), tx)
    return True, "%s: %s in (\"%s\"), %s refused, picture+click+text ok" % (head, adm[0], sts[adm[0]]["outcome"].strip()[:30], ref[0])


def check_race(a, box, tag):
    rigs = [lib.Rig(a.box, "chrome", "x", PW, "%s-%s" % (tag, k), cap=a.cap) for k in "AB"]
    good, notes = 0, []
    try:
        for n, u in enumerate(RACE_REPS[:a.reps], 1):
            try:
                ok, txt = race_once(a, box, rigs, u, n)
            except Fail as e:
                ok, txt = False, "rep %d (%s): %s" % (n, u, e)
            except ToolError as e:
                ok, txt = False, "rep %d (%s) NOT VALID (tool): %s" % (n, u, e)
            good += ok
            notes.append(txt)
            print("NOTE race - %s" % txt, flush=True)
            for r in rigs:
                try:
                    if r.g:
                        r.g.close()
                except Exception:  # noqa: BLE001
                    pass
                r.g = None
            really_gone(box, u)
        if good == a.reps:
            return PASS, "%d of %d reps: one admitted with a working desktop, the other refused with the 0x0F sentence; %s" % (good, a.reps, " | ".join(notes))
        return FAIL, "%d of %d reps OK; %s" % (good, a.reps, " | ".join(x for x in notes if "picture+click+text ok" not in x))
    finally:
        for r in rigs:
            r.stop()


def logout_gesture(box, user, de):
    cmd = ("u=$(id -u %(u)s); setsid sh -c \"runuser -u %(u)s -- env XDG_RUNTIME_DIR=/run/user/$u DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus LC_ALL=C "
           "timeout 60 %(c)s; echo rc=\\$?\" </dev/null >/tmp/rs-logout-%(u)s.out 2>&1 & sleep 3; head -c 200 /tmp/rs-logout-%(u)s.out; echo started" % {"u": user, "c": LC.LOGOUT[de]})
    return box.run(cmd)[1].strip().replace("\n", " ")[-80:]


def check_other_logout(a, box, tag):
    rA = lib.Rig(a.box, "chrome", "rs3", PW, tag + "-A", cap=a.cap)
    rB = lib.Rig(a.box, "chrome", "rs4", PW, tag + "-B", cap=a.cap)
    try:
        ctxA, textA, pidA = bring_up(a, box, rA, "rs3", "alfa")
        ctxB, textB, pidB = bring_up(a, box, rB, "rs4", "bravo")
        sessA = ctxA.sessions("rs3")
        LC.wait_idle(ctxA, "rs3")
        t0 = time.time()
        gesture = logout_gesture(box, "rs3", a.box)
        told = page_told(rA, 60, match="ended")
        end, left, sess = time.time() + 40, [], []
        while time.time() < end:
            left, sess = ctxA.procs("rs3"), ctxA.sessions("rs3")
            if not left and not sess:
                break
            time.sleep(2)
        bad = []
        if not told:
            bad.append("the client of rs3 was NOT told \"ended\" in 60 s after the Log Out gesture (%s)" % gesture)
        sB = rB.state()
        pidB2 = rB.win_pid()
        if not (sB["session"] and sB["cls"] == "good"):
            bad.append("rs4's client is no longer in: \"%s\" (%s)" % (sB["outcome"].strip(), sB["cls"]))
        if pidB2 != pidB:
            bad.append("rs4's window pid was %s, now %s (its programs were lost)" % (pidB, pidB2))
        ev, png = LC.probe(ctxB, "x", 0.4, 0.6)
        tx = ([e["text"] for e in ev if e["ev"] == "text"] or [""])[-1]
        cl = [e for e in ev if e["ev"] == "click"]
        if tx != textB + "x" or not cl:
            bad.append("rs4's input after rs3's logout: text \"%s\" (expected \"%s\"), %d click(s)" % (tx, textB + "x", len(cl)))
        lib.save_png("resil-%s-other-B.png" % a.box, png)
        if bad:
            return FAIL, "; ".join(bad) + "; rs3 left: %d proc(s), logind %s; journal: %s" % (len(left), sess, jlog(box, t0, "rs3|rs4", 8))
        rA.new_browser()
        s, tries, dt = LC.enter(ctxA, retry=10)
        if not (s["session"] and s["cls"] == "good"):
            return FAIL, "rs3 does not get in again after its Log Out: \"%s\"; journal: %s" % (s["outcome"].strip(), jlog(box, t0, "rs3", 6))
        rA.settle(still=1)
        rA.start_window()
        pidA2, sessA2 = rA.win_pid(), ctxA.sessions("rs3")
        if "new" not in s["outcome"] or "resumed" in s["outcome"]:
            return FAIL, "rs3's login after its Log Out is not \"new\": \"%s\"" % s["outcome"].strip()
        if pidA2 == pidA:
            return FAIL, "rs3's window pid is the old one (%s) after a Log Out" % pidA
        ev, png = LC.probe(ctxB, "y", 0.6, 0.4)
        tx2 = ([e["text"] for e in ev if e["ev"] == "text"] or [""])[-1]
        if tx2 != textB + "xy" or rB.win_pid() != pidB:
            return FAIL, "rs4 disturbed by rs3's new session: text \"%s\", window pid %s (was %s)" % (tx2, rB.win_pid(), pidB)
        return PASS, "rs3 Log Out (%s): client told \"%s\" after %.0f s, nothing of rs3 left; rs4 untouched (window pid %s, typed on to \"%s\"); rs3 again: \"%s\", new window pid %s (was %s), logind %s -> %s" % (
            LC.LOGOUT[a.box].split()[0], told[2][:40], told[0], pidB, tx2, s["outcome"].strip(), pidA2, pidA, sessA, sessA2)
    finally:
        rA.stop()
        rB.stop()


def in_force(box):
    """The last start-up line of the three clocks: (silence, inactivity, abandonment) in seconds, or None."""
    t = box.run("journalctl -u remotix --no-pager -o cat | grep 'clocks in force' | tail -1; true")[1]
    m = re.search(r"client silence (\d+) s .* inactivity (\d+) s.* abandonment (\d+) s", t)
    return tuple(int(x) for x in m.groups()) if m else None


def check_clocks(a, box, tag):
    rig = lib.Rig(a.box, "chrome", "rs5", PW, tag, cap=a.cap)
    try:
        d = in_force(box)
        if d != (30, 1800, 3600):
            return FAIL, "the clocks in force at start-up are %s, SPECS 5.3 says (30, 1800, 3600)" % (d,)
        box.run("printf 'REMOTIX_OPTIONS=--inactivity-s 30 --abandon-s 90\\n' > %s; systemctl restart remotix; sleep 2" % CLOCKS_DROPIN, timeout=60)
        if not wait_port(a.box):
            raise Fail("the service does not answer after the restart with short clocks")
        short = in_force(box)
        if short != (30, 30, 90):
            raise ToolError("the short clocks did not take (start-up line says %s): the mechanism cannot be tested" % (short,))
        ctx, text0, pid0 = bring_up(a, box, rig, "rs5", "idle")
        t_in = time.time()  # the last input of the user is the end of bring_up's probe
        told = page_told(rig, 70, match="touching|half an hour|inactiv")
        bad, ok = [], []
        if not told:
            st = rig.state()
            bad.append("the client was NOT told anything about inactivity within 70 s of its last input (session=%s, outcome \"%s\")" % (st["session"], st["outcome"].strip()[:80]))
        else:
            at = time.time() - t_in
            (ok if 25 <= at <= 50 else bad).append("client told \"%s\" %.0f s after its last input (ceiling 30 s, form %s)" % (told[2][:60], at, "back" if told[1] else "not shown"))
            up = alive(box, pid0)
            (ok if up else bad).append("programs %s after the inactivity farewell (spec: they stay)" % ("stayed" if up else "were LOST"))
        gone_at = None
        while time.time() - t_in < 150:
            if not alive(box, pid0):
                gone_at = time.time() - t_in
                break
            time.sleep(3)
        if gone_at is None:
            bad.append("the session was NOT closed 150 s after the last input (abandonment ceiling 90 s)")
        else:
            (ok if 80 <= gone_at <= 130 else bad).append("session closed %.0f s after the last input (ceiling 90 s)" % gone_at)
            end, left, sess = time.time() + 40, [], []
            infra = ("remotix", "systemd", "(sd-pam)", "dbus-daemon", "pipewire", "wireplumber", "pipewire-pulse", "mpris-proxy")
            while time.time() < end:
                left, sess = ctx.procs("rs5"), ctx.sessions("rs5")
                if not [x for x in left if x.split()[-1] not in infra] and not sess:
                    break
                time.sleep(2)
            progs = [x for x in left if x.split()[-1] not in infra]
            (bad if progs or sess else ok).append("after the abandonment: %d program(s) %s, logind %s" % (len(progs), progs[:5], sess))
        ab = jlog(box, t_in - 60, "ABANDONMENT|INACTIVITY", 3)
        if not bad:
            rig.new_browser()
            s, tries, dt = LC.enter(ctx, retry=10)
            if not (s["session"] and s["cls"] == "good" and "new" in s["outcome"]):
                bad.append("login after the abandonment: \"%s\" (%s), expected a NEW session" % (s["outcome"].strip(), s["cls"]))
            else:
                ok.append("login after the abandonment: \"%s\"" % s["outcome"].strip())
        return (FAIL if bad else PASS), "; ".join(bad + ["--"] + ok if bad else ok) + "; defaults at start-up %s, short %s; journal: %s" % (d, short, ab)
    finally:
        rig.stop()
        box.run("rm -f %s; systemctl restart remotix; sleep 2; pkill -u rs5 -f rx-window; loginctl terminate-user rs5; true" % CLOCKS_DROPIN, timeout=90)
        back = wait_port(a.box)
        print("NOTE clocks-restore - drop-in removed, service restarted, port %s, clocks in force %s (defaults expected (30, 1800, 3600))" % (
            "up" if back else "DOWN", in_force(box)), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--box", default="xfce", choices=sorted(lib.PORTS))
    ap.add_argument("--cap", type=int, default=60, help="seconds allowed for a login or a picture")
    ap.add_argument("--reps", type=int, default=5, help="repetitions of simultaneous-first-login (max 5)")
    ap.add_argument("--only", default="", help="comma list of checks to run")
    a = ap.parse_args()
    a.reps = min(a.reps, len(RACE_REPS))
    box, stamp = lib.Box(a.box), time.strftime("%H%M%S") + "-" + a.box
    names = [n for n in NAMES if not a.only or n in a.only.split(",")]
    res = lib.Results(names)
    fns = {"service-restart": check_restart, "network-drop": check_drop, "simultaneous-first-login": check_race,
           "login-after-other-logout": check_other_logout, "clocks": check_clocks}
    lib.guard(2400)
    nft = DeadLine(a.box)
    try:
        nft.remove()  # a leftover table of a killed run would cut the box
        for n in names:
            res.attempt(n, lambda n=n: fns[n](a, box, "%s-%s" % (stamp, n[:6])))
    finally:
        if not nft.remove():
            print("NOTE nft - the table %s is STILL THERE, remove it by hand" % nft.table, flush=True)
    return res.code()


if __name__ == "__main__":
    sys.exit(main())
