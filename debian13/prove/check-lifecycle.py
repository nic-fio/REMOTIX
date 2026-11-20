#!/usr/bin/env python3
"""check-lifecycle - the session life cycle of a running REMOTIX box, with a real browser (Chrome).

    python3 check-lifecycle.py [--box xfce] [--wait 30]

Runs ON THE DEV SERVER (lib.py). Uses its own users lc1 (checks 1-3, one session carried through) and lc2 (check 4), made in the box.
One line per check:  PASS|FAIL|BLOCKED name - evidence.  Exit 0 only if all four PASS.
  1 detach-reattach      clean close, 30 s, log in again: "resumed", same window, same text, mouse and keys work
  2 kill-reattach        kill -9 of the browser, log in again: same as 1
  3 reattach-other-size  reattach with a smaller browser window: the canvas and the desktop take the new size, picture right
  4 logout               the desktop's own Log Out: the client is told, nothing of the user is left in the box,
                         a new login gives a NEW session
Everything is seen from INSIDE the box: a fullscreen GTK window (window.py) logs the events it gets, with its size.
FAIL = product (also: page or login refused).  BLOCKED = the tool could not look.  Facts about logind are always printed."""
import argparse
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402
from lib import PASS, FAIL, BLOCKED, Fail, ToolError  # noqa: E402

PW = "lc-pass-2026"
NAMES = ("detach-reattach", "kill-reattach", "reattach-other-size", "logout")
# the desktop's own "Log Out", as a D-Bus method / command run in the user's session (as in the old bench, XFCE without --fast)
LOGOUT = {"xfce": "xfce4-session-logout --logout",
          "lxqt": "busctl --user --expect-reply=no call org.lxqt.session /LXQtSession org.lxqt.session logout",
          "gnome": "busctl --user call org.gnome.SessionManager /org/gnome/SessionManager org.gnome.SessionManager Logout u 1",
          "kde": "busctl --user call org.kde.Shutdown /Shutdown org.kde.Shutdown logout"}
LOGIND = ("for i in $(loginctl list-sessions --no-legend | awk -v u=%(u)s '$3==u{print $1}'); do echo \"@@ $i $(loginctl show-session $i "
          "-p State -p Class -p Type -p Seat -p Remote -p Leader | tr '\\n' ' ')\"; done; true")


class Ctx:
    def __init__(self, rig):
        self.rig, self.box, self.t0 = rig, rig.box, time.time()

    def sessions(self, user):
        return [l[3:].strip() for l in self.box.run(LOGIND % {"u": user})[1].splitlines() if l.startswith("@@ ")]

    def procs(self, user):
        t = self.box.run("ps -u %s -o pid=,comm= | sort -n | head -40; true" % user)[1]
        return [" ".join(l.split()) for l in t.splitlines() if l.strip()]

    def journal(self, user, n=8):
        return self.box.journal(user, since="@%d" % self.t0, n=n)


def enter(ctx, retry=0):
    """Open the page and sign in; with `retry` seconds, a refusal is tried again (the old client may still hold the slot).
    Returns (state, tries, seconds); the caller judges."""
    ctx.rig.open_page()
    t0 = time.time()
    ok, s = ctx.rig.try_login(retry=retry)
    return s, ctx.rig.tries, time.time() - t0


def probe(ctx, typed, fx, fy):
    """Mouse and keys through the browser; returns (new events, picture of the canvas)."""
    rig = ctx.rig
    g, n0 = rig.g, len(rig.events())
    t_m = time.time()
    while time.time() - t_m < 20 and not [e for e in rig.events()[n0:] if e["ev"] == "click"]:  # as check-base: pointer tried every 2 s
        g.move(*rig.px(0.2, 0.2))
        time.sleep(0.3)
        g.click(*rig.px(fx, fy))
        time.sleep(1.5)
    g.type_text(typed)
    end = time.time() + 10
    while time.time() < end and not any(e["ev"] == "text" for e in rig.events()[n0:]):
        time.sleep(0.5)
    time.sleep(1)
    return rig.events()[n0:], rig.canvas_png()


def judge_back(ctx, s, ev, png, pid0, text0, typed, fx, fy):
    """Problems (list) and facts (list) of a re-entry: resumed, same window, same text, mouse, keys, picture."""
    bad, ok = [], []
    if "resumed" in s["outcome"]:
        ok.append("outcome \"%s\"" % s["outcome"].strip())
    else:
        bad.append("outcome is not \"resumed\": \"%s\"" % s["outcome"].strip())
    pid = ctx.rig.win_pid()
    if pid and pid == pid0:
        ok.append("same window process pid %s" % pid)
    else:
        bad.append("the window process of the user is %s, before it was %s (the programs were lost)" % (pid, pid0))
    cl = [e for e in ev if e["ev"] == "click"]
    if cl and abs(cl[0]["fx"] - fx) < 0.08 and abs(cl[0]["fy"] - fy) < 0.08:
        ok.append("click (%.2f,%.2f) arrived, %d motions" % (cl[0]["fx"], cl[0]["fy"], len([e for e in ev if e["ev"] == "motion"])))
    else:
        bad.append("click sent at (%.2f,%.2f), the window got %s" % (fx, fy, cl[:1] or "none"))
    tx = [e["text"] for e in ev if e["ev"] == "text"]
    if tx and tx[-1] == text0 + typed:
        ok.append("text kept and extended: \"%s\"" % tx[-1])
    else:
        bad.append("expected text \"%s\", the window holds %s" % (text0 + typed, repr(tx[-1]) if tx else "no key event"))
    y = lib.frac(png, (240, 224, 96), tol=(45, 45, 60))  # the test window's entry colour (#f0e060)
    (ok if y >= 0.3 else bad).append("picture: test window fills %.0f%% of the canvas" % (100 * y))
    return bad, ok, (tx[-1] if tx else text0)


CPU = ("t() { s=0; for p in $(pgrep -u %(u)s); do v=$(awk '{print $14+$15}' /proc/$p/stat 2>/dev/null); s=$((s+${v:-0})); done; echo $s; }; "
       "a=$(t); sleep 3; b=$(t); echo $((b-a))")


def wait_idle(ctx, user, cap=60):
    """A fresh desktop is still starting its own programs for a while after the panel is up (under load: much longer), and
    a Log Out asked of a session that is still starting can be dropped. Wait until the user's processes use less than 15% of one
    CPU over 3 s (clock ticks) - what a person's pause before clicking Log Out is - or `cap` seconds. Returns (waited, last ticks)."""
    t0, ticks = time.time(), None
    while time.time() - t0 < cap:
        t = ctx.box.run(CPU % {"u": user})[1].split()
        ticks = int(t[-1]) if t and t[-1].lstrip("-").isdigit() else None
        if ticks is not None and ticks < 45:
            break
    return time.time() - t0, ticks


def canvas_of(outcome):
    m = re.search(r"canvas (\d+)×(\d+)", outcome)
    return (int(m.group(1)), int(m.group(2))) if m else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--box", default="xfce", choices=sorted(lib.PORTS))
    ap.add_argument("--wait", type=int, default=30, help="seconds between the clean close and the login again")
    a = ap.parse_args()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    res, rig = lib.Results(NAMES), lib.Rig(a.box, "chrome", "lc1", PW, "life")
    ctx = Ctx(rig)
    st = {}  # what the checks carry from one to the next

    def setup():
        for u in ("lc1", "lc2"):
            ctx.box.ensure_user(u, PW)
        for u in ("lc1", "lc2"):  # my own users only: a session left by an earlier run is ended, so that the first login is a NEW one
            ctx.box.run("pkill -u %s -f rx-window; loginctl terminate-user %s; for i in $(seq 25); do pgrep -u %s >/dev/null || break; sleep 1; done; true" % (u, u, u), timeout=60)
        rig.start(make_user=False)
        s, tries, dt = enter(ctx)
        if not (s["session"] and s["cls"] == "good"):
            raise Fail("base failed: lc1 not admitted: \"%s\" journal: %s" % (s["outcome"].strip(), ctx.journal("lc1")))
        if "new" not in s["outcome"]:
            raise Fail("base failed: first login of lc1 is not \"new\": \"%s\"" % s["outcome"].strip())
        s = rig.settle(still=1)["s"]
        rig.start_window()
        ev, png = probe(ctx, "lifecycle", 0.5, 0.5)
        text0 = ([e["text"] for e in ev if e["ev"] == "text"] or [""])[-1]
        pid0 = rig.win_pid()
        if text0 != "lifecycle" or not pid0:
            raise Fail("base failed: typed \"lifecycle\", the window holds \"%s\" (pid %s)" % (text0, pid0))
        sess0 = ctx.sessions("lc1")
        lg = ctx.box.run("journalctl -u systemd-logind --no-pager -o short-precise --since '@%d' | grep -i 'lc1' | head -3 | cut -c1-140; true" % ctx.t0)[1]
        print("setup %s: lc1 new session \"%s\", window pid %s text \"%s\"; logind sessions of lc1: %s" % (a.box, s["outcome"].strip(), pid0, text0, sess0), flush=True)
        print("NOTE logind-state - lc1 sessions %s; systemd-logind journal: %s" % (sess0, " | ".join(lg.splitlines())), flush=True)
        st.update(text0=text0, pid0=pid0, canvas=canvas_of(s["outcome"]))

    def reattach(name, how, size):
        def run():
            g = rig.g
            if how == "kill":
                g.kill()
            g.close()
            rig.g = None
            wait = a.wait if name == NAMES[0] else (a.wait + 5 if how == "kill" else 5)
            mid = ctx.sessions("lc1"), rig.win_pid()
            time.sleep(wait)
            rig.new_browser(size)
            s, tries, dt = enter(ctx, retry=70 if how == "kill" else 20)
            if not (s["session"] and s["cls"] == "good"):
                st["gone"] = True
                raise Fail("login again not admitted after %d tries, %.0f s: \"%s\" (%s); remotix journal: %s" % (tries, dt, s["outcome"].strip(), s["cls"], ctx.journal("lc1")))
            d = rig.settle(still=1, shell=False)
            s, g = d["s"], rig.g
            s["outcome"] = rig.state()["outcome"]
            fx, fy = (0.4, 0.4) if name == NAMES[0] else (0.65, 0.35) if name == NAMES[1] else (0.7, 0.3)
            vb = g.js("const v=document.getElementById('viewer'); return [v.width,v.height];")
            typed = {NAMES[0]: "one", NAMES[1]: "two", NAMES[2]: "three"}[name]
            ev, png = probe(ctx, typed, fx, fy)
            bad, ok, st["text0"] = judge_back(ctx, s, ev, png, st["pid0"], st["text0"], typed, fx, fy)
            ok.append("viewer buffer %sx%s, window inside the box %s; %s close, %d s later; while away logind had %d session(s) of lc1 and window pid %s alive; login took %d try(ies)"
                      % (vb[0], vb[1], ["%dx%d" % (e["w"], e["h"]) for e in ev if e["ev"] == "click"][:1], how, wait, len(mid[0]), mid[1], tries))
            if name == NAMES[2]:
                cw, ch = vb  # the canvas buffer
                ok.append("outcome line says canvas %s" % (canvas_of(s["outcome"]),))
                cl = [e for e in ev if e["ev"] == "click"]
                dpr = g.js("return devicePixelRatio") or 1
                vw, vh = s["rect"][2] * dpr, s["rect"][3] * dpr
                prev = st["canvas"]
                if prev and (cw, ch) != prev and cw and abs(cw - vw) <= 32 and abs(ch - vh) <= 32:
                    ok.append("canvas %dx%d (was %dx%d) for the window %dx%d" % (cw, ch, prev[0], prev[1], vw, vh))
                else:
                    bad.append("canvas %s, before %s, the browser window is %dx%d: the canvas did not take the new size" % ((cw, ch), prev, vw, vh))
                if cl and abs(cl[0]["w"] - cw) <= 32 and abs(cl[0]["h"] - ch) <= 32:
                    ok.append("inside the box the desktop window is %dx%d" % (cl[0]["w"], cl[0]["h"]))
                else:
                    bad.append("inside the box the desktop window is %s, the canvas %dx%d: the desktop did not take the size" % (
                        "%dx%d" % (cl[0]["w"], cl[0]["h"]) if cl else "unreadable", cw, ch))
            lib.save_png("lifecycle-%s-%s-%s.png" % (a.box, name, stamp), png)
            ok.append("logind of lc1 now: %s" % (ctx.sessions("lc1"),))
            st["canvas"] = canvas_of(s["outcome"]) or st["canvas"]
            return (FAIL if bad else PASS), "; ".join(bad + ["--"] + ok if bad else ok) + (" | remotix journal: " + ctx.journal("lc1") if bad else "")
        return run

    def logout():
        """With lc2, in the same compositor, a new browser."""
        user = rig.user = "lc2"
        if rig.g is None:
            rig.new_browser()
        s, tries, dt = enter(ctx, retry=10)
        if not (s["session"] and s["cls"] == "good"):
            raise Fail("lc2 not admitted: \"%s\"; journal: %s" % (s["outcome"].strip(), ctx.journal(user)))
        rig.settle(still=1)
        rig.start_window()
        idle_s, ticks = wait_idle(ctx, user)
        pidA, sessA = rig.win_pid(), ctx.sessions(user)
        g = rig.g
        def gesture_cmd():
            return ("u=$(id -u lc2); setsid sh -c \"runuser -u lc2 -- env XDG_RUNTIME_DIR=/run/user/$u DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus LC_ALL=C "
                    "timeout 60 %s; echo rc=\\$?\" </dev/null >/tmp/lc-logout.out 2>&1 & sleep 3; head -c 200 /tmp/lc-logout.out; echo started" % LOGOUT[a.box])
        c, t = ctx.box.run(gesture_cmd())
        gesture = t.strip().replace("\n", " ")[-80:]
        end, stt, f = time.time() + 60, {}, {}
        t_l = time.time()
        while time.time() < end:
            stt, f = rig.state(), g.js(lib.JS_FORM)
            if f.get("form") and "ended" in (stt["outcome"] or ""):
                break
            time.sleep(1)
        shell_gone = ctx.box.run(lib.SHELL_UP[a.box] % {"u": user})[0] != 0
        told = bool(f.get("form")) and "ended" in (stt["outcome"] or "")
        told_s = time.time() - t_l
        end, left, sess = time.time() + 40, [], []
        while time.time() < end:
            left, sess = ctx.procs(user), ctx.sessions(user)
            if not left and not sess:
                break
            time.sleep(2)
        infra = ("remotix", "systemd", "(sd-pam)", "dbus-daemon", "pipewire", "wireplumber", "pipewire-pulse", "mpris-proxy")
        progs = [x for x in left if x.split()[-1] not in infra]  # what is not the child / user manager / audio plumbing
        bad, bad_end = [], []
        if not told:
            bad.append("the client was NOT told in 60 s (form=%s, outcome \"%s\")" % (f.get("form"), (stt["outcome"] or "").strip()))
        if progs:
            bad_end.append("%d program(s) of the user left: %s" % (len(progs), progs[:10]))
        if left or sess:
            bad_end.append("%d process(es) in all (%d of them the child, user manager and audio plumbing) and logind session(s) %s still there 40 s later"
                           % (len(left), len(left) - len(progs), sess))
        bad += ["desktop shell %s after the gesture" % ("GONE (the logout itself worked)" if shell_gone else "STILL UP (the logout did not complete)")] * bool(bad_end or bad)
        bad += bad_end
        nb, bad_new = [], ""
        if told:  # the new login must be a NEW session whatever the leftovers were
            s, tries, dt = enter(ctx, retry=10)
            if not (s["session"] and s["cls"] == "good"):
                nb.append("a new login of lc2 is not admitted: \"%s\"" % s["outcome"].strip())
            else:
                rig.settle(still=1)
                rig.start_window()  # a program of the NEW session
                pidB, sessB = rig.win_pid(), ctx.sessions(user)
                old = ctx.box.run("kill -0 %s 2>/dev/null && echo alive; true" % pidA)[1]
                if "new" not in s["outcome"] or "resumed" in s["outcome"]:
                    nb.append("the new login is not \"new\": \"%s\"" % s["outcome"].strip())
                if old.strip() == "alive":
                    nb.append("the old window pid %s is still alive" % pidA)
                if sessB and sessB == sessA:
                    nb.append("logind sessions did not change: %s" % sessB)
                if not nb:
                    bad_new = "new login \"%s\", logind before %s now %s" % (s["outcome"].strip(), sessA, sessB)
        if bad or nb:
            diag = ""
            if not told:  # DIAGNOSIS only, the verdict stays FAIL: is the same gesture, sent again, obeyed? (a dropped first request = a race)
                ctx.box.run(gesture_cmd())
                end2 = time.time() + 30
                while time.time() < end2 and not (lib.JS_FORM and g.js(lib.JS_FORM).get("form") and "ended" in (rig.state()["outcome"] or "")):
                    time.sleep(1)
                diag = "; DIAGNOSIS: the gesture sent AGAIN after the failure was %s within 30 s" % ("OBEYED (the client was told)" if "ended" in (rig.state()["outcome"] or "") else "NOT obeyed")
            if not told:  # what the desktop did with the gesture: its own output, the helper still running, the user's journal, the picture
                diag += "; diag: " + ctx.box.run("echo \"logout output: $(head -c 300 /tmp/lc-logout.out)\"; echo \"helper: $(pgrep -a -u lc2 -f logout | head -3)\"; "
                                                "journalctl _UID=$(id -u lc2) --no-pager -n 12 -o cat | cut -c1-140; true")[1].replace("\n", " | ")
                try:
                    lib.save_png("lifecycle-%s-logout-%s.png" % (a.box, stamp), rig.canvas_png())
                    diag += "; picture saved shots/lifecycle-%s-logout-%s.png" % (a.box, stamp)
                except Exception:  # noqa: BLE001
                    pass
            return FAIL, "; ".join(bad + nb) + ("; (new login otherwise fine: %s)" % bad_new if told and not nb else "") + diag \
                + "; session idle check: %d ticks/3 s after %.0f s" % (ticks if ticks is not None else -1, idle_s) \
                + "; gesture: %s; remotix journal: %s" % (gesture, ctx.journal(user))
        return PASS, "gesture \"%s\" -> %s; client told after %.0f s (\"%s\"), form back; no process and no logind session of lc2 left; %s; session idle (%d ticks/3 s) after %.0f s" \
            % (LOGOUT[a.box].split()[0], gesture, told_s, stt["outcome"].strip(), bad_new, ticks if ticks is not None else -1, idle_s)

    lib.guard(1500)
    try:
        try:
            setup()
        except Exception as e:  # noqa: BLE001
            res.rest(FAIL if isinstance(e, Fail) else BLOCKED, str(e) if isinstance(e, Fail) else lib.tool_error(e))
            return 1
        for name, how, size in ((NAMES[0], "clean", (1400, 900)), (NAMES[1], "kill", (1400, 900)), (NAMES[2], "clean", (1000, 640))):
            if st.get("gone"):  # a check that could not even log in again leaves nothing to look at
                res.say(BLOCKED, name, "no session to look at")
            else:
                res.attempt(name, reattach(name, how, size))
        res.attempt(NAMES[3], logout)
        return res.code()
    finally:
        rig.stop()
        rig.box.run("pkill -u lc1 -f rx-window; true", timeout=20)


if __name__ == "__main__":
    sys.exit(main())
