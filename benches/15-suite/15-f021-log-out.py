#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f021 — F-021 «EXIT» FROM THE MENU: the session ends, the programs close,
          the page goes back to the form, no rebirth; and whoever comes back in opens
          a NEW, clean one

    python3 15-f021-log-out.py --box lxqt --browser chrome [--fault]

⭐ WHAT IT DOES, in a single session (tenant c15021u<n>), like the user:
   1  logs in from the real browser; inside the session opens a real PROGRAM
      (firefox-esr with C20's scene, its process is the witness)
   2  the «Exit» gesture (see GESTO, below) and the guard:
        F  the product declares the session ended (`C20.FINISHED_LINES`)
        M  the PAGE goes back to the form (field `#signin-form` visible) and the
           `#outcome` line says «the session has ended» (`page.html` 0x10)
        P  the tenant's processes: none, except those in EXEMPT
           (`ps -u`), and the program opened at point 1 is no longer there
        N  ⛔ for GUARD_S seconds after the end, in the server log
           no birth for this tenant («I AM MAKING IT BE BORN»,
           «negotiated format»): no rebirth
   3  a new login FROM THE SAME PAGE (if the form is not there: reload,
      and say so) ⇒ first frame, and
        R  NEW: the log says «I AM MAKING IT BE BORN» after the re-entry (a
           resumed session does not say it: the child finds it alive)
        C  CLEAN: the program of point 1 is not there
   Outcome: PASS only if F M P N R C.  A gesture that does not answer, a page
   that does not open ⇒ BLOCKED.

⚠ GESTURE — declared.  Not the click on the menu with the browser's mouse: it is the
  METHOD the «Exit» menu entry reaches, C20's table
  (`DESKTOPS_AND_GESTURES`, the same as `12-c20-real.py`, imported):
     GNOME  org.gnome.SessionManager.Logout(1)
     KDE    org.kde.Shutdown.logout
     XFCE   xfce4-session-logout --logout --fast
     LXQt   org.lxqt.session.logout
  Why: the menu is different in the four desktops (GNOME: three clicks and a
  dialog with a countdown; KDE: launcher, «Exit», confirmation; XFCE and
  LXQt: classic menu), and at 3840x2160 the entries would have to be FOUND in the
  photo — an image-recognition test, not an exit test.
  What the product sees (the compositor going away, the session
  manager closing) is the same: defect 6 of phase 14 (the
  rebirth on LXQt) was reproduced with this gesture (C24, 16 out of 20).

⛔ THE INJECTED FAULT (in the same session, after the healthy pass) — two, and
   BOTH must be seen:
   G1 «empty Exit»: instead of the gesture a harmless D-Bus call (GetId of the
      session bus, answers 0 and does nothing) ⇒ the session does NOT end
      ⇒ the judge MUST say FAIL (F, M, P red).
   G2 «re-entry inside the guard»: real «Exit», and as soon as the page is back
      at the form the bench comes back in AT ONCE ⇒ a session is born inside the
      GUARD_S window ⇒ the judge MUST say FAIL for rebirth (N).
      ⚠ It proves that the judge READS a birth after the end and calls it
      red; in the healthy pass the bench never comes back in inside the window
      ⇒ every birth that appears there is the product's.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

FUNCTIONS = ("F-021",)


C20 = S.C20V.C20
FINISHED_LINES = [p for p, _d in C20.FINISHED_LINES]
BIRTHS = ("I AM MAKING IT BE BORN", "negotiated format")
PAGE_SENTENCE = "has ended"                       # page.html, MESSAGGI[0x10]
GUARD_S = 25.0
CAP_FINISHED = 60.0
CAP_PROCESSES = 30.0
# ⭐ The tenant's processes that may remain after «Exit», and why —
#   judged by the CONTROL GROUP (/proc/<pid>/cgroup), not by the name:
#   remotix        the product's CHILD (runs with its uid, in the server's
#                  group): by design it stays, and the re-entry is born in it (I2;
#                  C24: «the second login is born in the surviving child»).
#   user@<uid>.service/…/*.service and init.scope   systemd's USER MANAGER
#                  and its services (dbus, pipewire, wireplumber…):
#                  they live as long as the user manager, which stays as long as logind
#                  has a session of the user — the child's.  The user did not
#                  open them and they are not the graphical session.
#   ⛔ THEY COUNT: everything in a `session-N.scope` (the desktop and the
#      programs it opened, LXQt/XFCE) and in an `app-*.scope` (the programs
#      opened by GNOME and KDE), and every other place.  The whole list is
#      in the «observed».
EXEMPT = ("remotix",)


def exempt(entry):
    """`entry` = «name|cgroup».  See EXEMPT above — pure."""
    name, _, cg = entry.partition("|")
    if name in EXEMPT:
        return True
    if "/user@" not in cg:
        return False
    leaf = cg.rstrip("/").rsplit("/", 1)[-1]
    return leaf == "init.scope" or (leaf.endswith(".service")
                                       and not leaf.startswith("app-"))


PROGRAM = "firefox-esr"
# ⚠ The server lines saying «the page's wire dropped» (rcp.c,
#   webtransport.c): with ten benches on the same server the parent's loop
#   stopped for up to 17 s (24 Sep, «fell behind by … ms»), and Chrome
#   closed the transport BEFORE «Exit» arrived.
WIRE_DROPPED = ("the page CLOSED the WebTransport session", "DETACHED for silence")
NOOP_GESTURE = ("busctl --user call org.freedesktop.DBus /org/freedesktop/DBus "
                 "org.freedesktop.DBus GetId")


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES — pure
# ═══════════════════════════════════════════════════════════════════════════
def e_di(line, chi):
    return ("[%s]" % chi) in line or ("«%s»" % chi) in line


def births_in(lines, chi):
    if lines is None:
        return None
    return [r for r in lines if e_di(r, chi) and any(n in r for n in BIRTHS)]


def leftovers(entries):
    if entries is None:
        return None
    return sorted(v for v in entries if not exempt(v))


def judge_exit(d):
    """⭐ (outcome, reason) of the exit from the measured fields:
         finita   the FINISHED_LINES form seen, or None
         modulo   the form is visible in the page
         frase    the text of #outcome
         remaining  the tenant's non-exempt processes (list, or None)
         program  the program of point 1 is still there
         births  the birth lines after the end (list, or None)
    ⛔ The rebirth is looked at BEFORE everything: in defect 6 the product says
       «it is over» and then makes it be born, and a green read on the end would be the
       defect slipping through."""
    if not d.get("finished") and d.get("wire_dropped") and not d.get("births"):
        # ⚠ the page's wire dropped BEFORE the end arrived: the
        #   product had nobody to tell it to, and the page could not
        #   hear it ⇒ I could not look (never a FAIL, never a PASS)
        return S.BLOCKED, ("the page's wire dropped before the end («%s»): "
                           "I could not look at the exit" % d["wire_dropped"][:140])
    gone_mute = d.get("page_read") is False and not d.get("births")
    troubles = []
    if d.get("births"):
        troubles.append("after «Exit» the session IS REBORN (%d lines; the first: %s)"
                    % (len(d["births"]), d["births"][0].strip()[:120]))
    if not d.get("finished"):
        troubles.append("the product does not declare the session ended")
    if gone_mute and d.get("finished") and not d.get("remaining") and not d.get("program"):
        return S.BLOCKED, ("the end is declared and the programs are closed, but the page "
                           "never answered the bench: I could not look at it")
    if not d.get("form"):
        troubles.append("the page does NOT go back to the form")
    if PAGE_SENTENCE not in (d.get("sentence") or ""):
        troubles.append("the page does not say «the session has ended» (it says «%s»)"
                    % (d.get("sentence") or "")[:80])
    if d.get("program"):
        troubles.append("the program opened in the session (%s) is still alive" % PROGRAM)
    if d.get("remaining"):
        troubles.append("tenant's processes remain: %s" % " ".join(d["remaining"])[:160])
    if troubles:
        return S.FAIL, " · ".join(troubles)
    if d.get("remaining") is None or d.get("births") is None:
        return S.BLOCKED, "I could not read the processes or the log"
    return S.PASS, ("ended («%s»), the page at the form with «%s», no process "
                    "of the tenant (exempt: %s), no birth in %.0f s"
                    % (d["finished"], (d.get("sentence") or "")[:60], "/".join(EXEMPT),
                       d.get("guard", GUARD_S)))


def judge_reentry(d):
    """(outcome, reason) of the re-entry: got in, new (birth seen), clean."""
    if not d.get("entered"):
        return S.FAIL, "after «Exit» you do NOT get back in: %s" % d.get("why", "")
    troubles = []
    if not d.get("nuova"):
        troubles.append("the re-entry does not make a new session be born (no «I AM MAKING IT "
                    "BE BORN»: resumed?)")
    if d.get("program"):
        troubles.append("the re-entry's session is NOT clean: %s is still there%s" % (
            PROGRAM, (" — " + d["chi_lo_riapre"].splitlines()[0][:160])
            if d.get("chi_lo_riapre") else ""))
    if troubles:
        return S.FAIL, " · ".join(troubles)
    return S.PASS, "re-entry: NEW session («I AM MAKING IT BE BORN») and clean"


def certify():
    troubles = 0

    def p(name, obtained, expected):
        nonlocal troubles
        ok = obtained == expected
        troubles += not ok
        print("  %s %-62s %s (expected %s)" % ("OK " if ok else "NO ", name, obtained, expected))

    good_one = {"finished": "IS OVER", "form": True,
             "sentence": "the session has ended: the programs were closed",
             "remaining": [], "program": False, "births": []}
    g = lambda **k: judge_exit(dict(good_one, **k))[0]           # noqa: E731
    p("⭐ everything in order ⇒ PASS", g(), S.PASS)
    p("⛔ ended AND then reborn ⇒ FAIL", g(births=["child [c15021u1] I AM MAKING IT BE BORN"]),
      S.FAIL)
    p("⛔ not ended (empty Exit) ⇒ FAIL", g(finished=None, form=False, sentence="Admitted",
                                             program=True), S.FAIL)
    p("⛔ the page stays on the desktop ⇒ FAIL", g(form=False), S.FAIL)
    p("⛔ at the form but without the sentence ⇒ FAIL", g(sentence="network error"), S.FAIL)
    p("⛔ a process left ⇒ FAIL", g(remaining=["pcmanfm-qt"]), S.FAIL)
    p("⚠ wire dropped before the end ⇒ BLOCKED",
      g(finished=None, form=False, sentence="", wire_dropped="the page CLOSED the WebTransport session"),
      S.BLOCKED)
    p("⛔ wire dropped BUT reborn ⇒ FAIL",
      g(finished=None, wire_dropped="x", births=["[c15021u1] I AM MAKING IT BE BORN"]), S.FAIL)
    p("⚠ the page does not answer the bench ⇒ BLOCKED",
      g(form=False, sentence="", page_read=False), S.BLOCKED)
    p("⛔ the page answers and is not at the form ⇒ FAIL",
      g(form=False, sentence="", page_read=True), S.FAIL)
    p("⚠ processes not read ⇒ BLOCKED, never PASS", g(remaining=None), S.BLOCKED)
    p("⚠ log not read ⇒ BLOCKED, never PASS", g(births=None), S.BLOCKED)
    U = "0::/user.slice/user-4013.slice/user@4013.service"
    p("⭐ the child and the user manager do not count",
      leftovers(["remotix|0::/system.slice/rete11-server.service", "systemd|%s/init.scope" % U,
               "pipewire|%s/session.slice/pipewire.service" % U]), [])
    p("⛔ the desktop in the session scope counts",
      leftovers(["lxqt-panel|0::/user.slice/user-4013.slice/session-5.scope"]),
      ["lxqt-panel|0::/user.slice/user-4013.slice/session-5.scope"])
    p("⛔ a program opened by GNOME (app-*.scope) counts",
      len(leftovers(["firefox|%s/app.slice/app-gnome-firefox-12.scope" % U])), 1)
    p("⛔ a process without a readable group counts", leftovers(["x|"]), ["x|"])
    fin = ["child  [c15021u1] ⭐ ... I AM MAKING IT BE BORN (canvas 3840x2160)",
           "child  [c15021u10] I AM MAKING IT BE BORN", "capture [c15021u1] negotiated format"]
    p("⚠ the births of c15021u10 are not c15021u1's", len(births_in(fin, "c15021u1")), 2)
    p("⭐ new and clean re-entry ⇒ PASS",
      judge_reentry({"entered": True, "nuova": True, "program": False})[0], S.PASS)
    p("⛔ resumed re-entry ⇒ FAIL",
      judge_reentry({"entered": True, "nuova": False, "program": False})[0], S.FAIL)
    p("⛔ re-entry with the previous program ⇒ FAIL",
      judge_reentry({"entered": True, "nuova": True, "program": True})[0], S.FAIL)
    p("⛔ does not get back in ⇒ FAIL", judge_reentry({"entered": False})[0], S.FAIL)
    p("⭐ the forms of the end come from C20", len(FINISHED_LINES), 2)

    # ⭐ reading the log: EMPTY is not NOT READ (round 1, gnome/firefox)
    class Fake:
        def __init__(self, output):
            self.output = output

        def inside(self, _line, _seconds=60):
            return (None, self.output) if self.output.startswith("(no answer") else (1, self.output)

    class FakeSession:
        chi = "c15021u1"

        def __init__(self, output):
            self.sc = Fake(output)
    p("⭐ log read and empty (GNOME after «Exit») ⇒ [] and not None",
      log(FakeSession("@@fine"), 10), [])
    p("⭐ one line ⇒ the line", log(FakeSession(
        "x [c15021u1] I AM MAKING IT BE BORN\n@@fine"), 10), ["x [c15021u1] I AM MAKING IT BE BORN"])
    p("⚠ log not read ⇒ None", log(FakeSession("(no answer in 60 s)"), 10),
      None)
    d = dict(good_one, births=births_in([], "c15021u1"))
    p("⭐ ⇒ and with the empty slice the exit is judgeable (PASS)", judge_exit(d)[0], S.PASS)
    print("⛔ %d wrong cases" % troubles if troubles else "⭐ the judges say what they must")
    return 1 if troubles else 0


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def _retry(f, times=3):
    """⚠ The server belongs to ten benches: a read that does not answer is redone."""
    for _ in range(times):
        v = f()
        if v is not None:
            return v
        time.sleep(2)
    return None


def log(s, sign):
    """⭐ The tenant's lines from `sign` onwards: a LIST (even empty) if
    the log was read, None if not.

    ⛔ Not `s.log_from(…) or None`: on GNOME, after «Exit», the child goes
       away and NOTHING more is written for the tenant ⇒ the slice is EMPTY, and
       it is an answer, not a silence.  As long as `Scatola.dentro` went through
       ssh the slice was never empty (there was sshpw's «password:» line) and
       the bench defect could not be seen; with the local `podman exec` (25 Sep)
       it could ⇒ BLOCKED on gnome/firefox in round 1 and in the clean-up.
       ⇒ The @@fine marker says the command got to the end."""
    def una():
        c, t = s.sc.inside("tail -n +%d %s | grep -a -F -- '%s'; echo @@fine"
                           % (int(sign) + 1, S.C20V.LOG, s.chi), 60)
        if "@@fine" not in (t or ""):
            return None
        return [r for r in t.split("@@fine")[0].splitlines()
                if r.strip() and "password:" not in r]
    return _retry(una)


def wait_bus(s, cap=30):
    """⭐ The tenant's session bus is there (the socket /run/user/<uid>/bus):
    the «Exit» gesture talks to it.  ⛔ Right after a re-entry on GNOME the user
    manager may not have it yet ⇒ «Failed to connect to user scope bus»."""
    fine = time.time() + cap
    while time.time() < fine:
        c, _t = s.sc.inside("test -S /run/user/$(id -u %s)/bus" % s.chi, 20)
        if c == 0:
            return True
        time.sleep(1)
    return False


def do_gesture(s, gesture, cap=30):
    """(code, output) of the gesture; if the bus or the service are not there YET
    (session just born) it is retried up to `cap`."""
    wait_bus(s, cap)
    fine = time.time() + cap
    while True:
        c, t = s.sc.as_user(s.chi, gesture)
        if c == 0 or time.time() >= fine or not re.search(
                r"Failed to connect|No such file|ServiceUnknown|not provided|"
                r"was not provided by any \.service", t or ""):
            return c, t
        time.sleep(2)


def processes(s):
    """«name|cgroup» for every process of the tenant, or None."""
    def una():
        c, t = s.sc.inside(
            "for p in $(pgrep -u %s); do printf '@@p %%s|%%s\\n' \"$(cat /proc/$p/comm "
            "2>/dev/null)\" \"$(head -1 /proc/$p/cgroup 2>/dev/null)\"; done; echo @@fine"
            % s.chi, 40)
        if "@@fine" not in (t or ""):
            return None
        return [x[4:].strip() for x in t.splitlines() if x.startswith("@@p ")
                and x[4:].strip() != "|"]
    return _retry(una)


def program_alive(s):
    c, _t = s.sc.inside("pgrep -u %s -x %s >/dev/null" % (s.chi, PROGRAM), 30)
    return c == 0


def open_program(s):
    """firefox-esr with C20's scene, INSIDE the session (like C20)."""
    ok, t = s.sc.turn_on_scene(s.chi)
    if not ok:
        return False, "the program does not open in the session: %s" % t[-160:]
    fine = time.time() + 20
    while time.time() < fine:
        if program_alive(s):
            time.sleep(3)                  # the window draws itself
            return True, "%s opened" % PROGRAM
        time.sleep(1)
    return False, "%s is not among the tenant's processes after 20 s" % PROGRAM


def read_page(s, cap):
    """(form visible, sentence of #outcome, read) waiting up to `cap`.
    `was_read` is False if the page NEVER answered the bench (browser
    stalled: `[M]` 25 Sep, Chrome under load 50, CDP «timed out»)."""
    fine = time.time() + cap
    form, sentence, was_read = False, "", False
    while time.time() < fine:
        try:
            m = s.g.js(S.VERI.JS_MODULE)
            form = bool(m and m.get("form") and m.get("visible"))
            st = s.state()
            if "⛔" not in st:
                was_read = True
                sentence = st.get("outcome") or ""
        except Exception:                        # noqa: BLE001
            form = False
        if form and PAGE_SENTENCE in sentence:
            break
        time.sleep(0.5)
    return form, sentence, was_read


def wait_finished(s, sign, cap):
    fine = time.time() + cap
    while time.time() < fine:
        for r in log(s, sign) or []:
            for f in FINISHED_LINES:
                if f in r and e_di(r, s.chi):
                    return f, r
        time.sleep(1)
    return None, None


def exit_and_look(s, gesture, cap_finished=CAP_FINISHED, reenter_immediately=False, name="esci"):
    """The gesture and the four guards F M P N.  Returns (data, evidence) or
    raises Bloccata."""
    sign = _retry(s.log_mark)
    if sign is None:
        raise S.Blocked("I cannot read the server log")
    c, t = do_gesture(s, gesture)
    if c != 0:
        raise S.Blocked("the «Exit» gesture did not answer (code %s): %s" % (c, t[-200:]))
    t0 = time.time()
    finished, _r = wait_finished(s, sign, cap_finished)
    d = {"finished": finished}
    if finished:
        d["finita_s"] = round(time.time() - t0, 1)
    mark_end = (_retry(s.log_mark) if finished else None) or sign
    d["form"], d["sentence"], d["page_read"] = read_page(s, 30 if finished else 5)
    if reenter_immediately and d["form"]:
        # ⛔ G2: the bench comes back in INSIDE the guard
        e, m, _st = s.pr.enter(s.password)
        d["rientro_guasto"] = "%s: %s" % ({S.GREEN: "admitted"}.get(e, "not admitted"), m[:80])
    # P — the processes: wait for them to go away, up to CAP_PROCESSES
    fine = time.time() + (CAP_PROCESSES if finished else 3)
    while True:
        names = processes(s)
        d["remaining"] = leftovers(names)
        d["tutti"] = names
        d["program"] = program_alive(s)
        if (d["remaining"] == [] and not d["program"]) or time.time() >= fine:
            break
        time.sleep(2)
    # N — the guard: ALL of it (the green is an absence)
    rest = GUARD_S - (time.time() - t0)
    if rest > 0:
        time.sleep(rest)
    d["guard"] = time.time() - t0
    if not finished:
        whole = log(s, sign) or []
        d["wire_dropped"] = next((r.strip() for r in whole if e_di(r, s.chi) and any(
            k in r for k in WIRE_DROPPED)), None)
    chunk = log(s, mark_end)       # [] = read and empty (GNOME), None = not read
    d["births"] = births_in(chunk, s.chi)
    print("      [%s] mark %s→%s · slice %s lines · processes %s · births %s" % (
        name, sign, mark_end, None if chunk is None else len(chunk),
        None if d["remaining"] is None else len(d["remaining"]),
        None if d["births"] is None else len(d["births"])), flush=True)
    ev = [s.save_text("server-%s.txt" % name, log(s, sign) or ["(not read)"])]
    return d, ev


def reenter(s):
    """The new login from the same page: (data, evidence)."""
    sign = _retry(s.log_mark)
    if sign is None:
        return {"entered": False, "why": "I cannot read the server log"}, []
    d = {"ricaricata": False}
    m = s.g.js(S.VERI.JS_MODULE)
    if not (m and m.get("form") and m.get("visible")):
        d["ricaricata"] = True
        s.g.reload()
        ok, why = s.pr.open_after_reload()
        if not ok:
            return dict(d, entered=False, why="after the reload: " + why), []
    ok, m = s.enter(do_open=False)
    d["entered"], d["why"] = ok, m
    if not ok:
        return d, [s.save_text("server-rientro.txt", log(s, sign) or [])]
    chunk = log(s, sign) or []
    d["nuova"] = any("I AM MAKING IT BE BORN" in r and e_di(r, s.chi) for r in chunk)
    time.sleep(3)
    d["program"] = program_alive(s)
    png, dove = s.photo("rientro")
    ev = [s.save_text("server-rientro.txt", chunk)] + ([dove] if dove else [])
    if d["program"]:
        # ⭐ who reopened it?  the parent of the process and the desktop's
        #   session saving (KDE: ksmserverrc)
        _c, t = s.sc.inside(
            "for p in $(pgrep -u %(c)s -x %(p)s); do pp=$(awk '{print $4}' /proc/$p/stat); "
            "echo \"$p padre $pp $(cat /proc/$pp/comm) · $(tr '\\0' ' ' < /proc/$p/cmdline "
            "| cut -c1-160)\"; done; echo ---; "
            "grep -A12 -i 'Session: saved' /home/%(c)s/.config/ksmserverrc 2>/dev/null "
            "| head -40" % {"c": s.chi, "p": PROGRAM}, 40)
        d["chi_lo_riapre"] = (t or "").strip()
        ev.append(s.save_text("rientro-programma-riaperto.txt", t or ""))
        print("   ⚠ %s reopened at the re-entry:\n%s" % (PROGRAM, (t or "")[:900]), flush=True)
    return d, ev


def bring_back_up(s):
    """A live session with the program open, to redo an exit."""
    r, _ev = reenter(s)
    if not r.get("entered"):
        return False, "not getting back in: %s" % r.get("why")
    return open_program(s)


def output(s, gesture, name, **k):
    """An exit watched and judged; if the wire dropped before the end
    (BLOCKED), it is redone ONCE from a new session."""
    for attempt in (1, 2):
        d, ev = exit_and_look(s, gesture, name="%s-%d" % (name, attempt), **k)
        e, p = judge_exit(d)
        if not (e == S.BLOCKED and d.get("wire_dropped")) or attempt == 2:
            break
        print("   ⚠ %s: %s — redoing it" % (name, p), flush=True)
        ok, m = bring_back_up(s)
        if not ok:
            return d, ev, S.BLOCKED, p + " · and I could not redo it: " + m
    return d, ev, e, p


def body(o, E):
    with S.Session(o, "021", E) as s:
        desktop, gesture = s.sc.exit_gesture()
        if o.gesture:
            desktop, gesture = "%s (gesture given by hand)" % o.box, o.gesture
        if not gesture:
            raise S.Blocked("I do not know how to say «Exit» in %s" % s.sc.container)
        print("   «Exit» (%s): %s" % (desktop, gesture), flush=True)
        ok, m = s.enter()
        if not ok:
            raise S.Blocked(m)
        ok, m = open_program(s)
        if not ok:
            raise S.Blocked(m)
        png, dove = s.photo("prima-di-esci")
        ev0 = [dove] if dove else []

        # ── the healthy pass ───────────────────────────────────────────────
        d, ev, outcome, why = output(s, gesture, "esci")
        oss = ("ended=%s after %s s · form=%s · «%s» · processes after: %s · births=%d"
               % (d.get("finished"), d.get("finita_s"), d.get("form"),
                  (d.get("sentence") or "")[:70],
                  " ".join(v.split("|")[0] for v in d.get("tutti") or []) or "none",
                  len(d.get("births") or [])))
        print("   exit: %s — %s" % (outcome, oss), flush=True)
        ev.append(s.save_text("processi-dopo-esci.txt", d.get("tutti") or ["(none)"]))
        viva = False
        if outcome == S.PASS:
            r, ev2 = reenter(s)
            viva = bool(r.get("entered"))
            outcome, p2 = judge_reentry(r)
            why = why + " · " + p2 + (" (⚠ the form was not there: reloaded)"
                                             if r.get("ricaricata") else "")
            ev += ev2
            oss += " · re-entry: %s" % p2
        E.put("F-021", outcome, why,
                expected="«Exit» ⇒ ended, programs closed, page at the form with «the session "
                       "has ended», no birth in %.0f s; the re-entry opens a "
                       "NEW and clean session" % GUARD_S,
                observed=oss, evidence=ev0 + ev + [s.save_console()],
                gesture=gesture)

        if not o.fault:
            return
        # a live session to start from is needed.  ⛔ Not from the page's field
        #   (`R.screen.session` can remain after the farewell): if the re-entry
        #   of the healthy pass did not happen, we come back in.  `[M]` 25 Sep, round 1
        #   and clean-up on gnome/firefox: without re-entry G1 talked to a bus
        #   that was no longer there ⇒ BLOCKED.
        if not viva:
            r, _ev = reenter(s)
            if not r.get("entered"):
                E.fault("F-021", None, "no live session for the fault: %s"
                         % r.get("why"))
                return
        # ── G1 «empty Exit» ───────────────────────────────────────────────
        d1, _ev = exit_and_look(s, NOOP_GESTURE, cap_finished=15, name="guasto-a-vuoto")
        e1, p1 = judge_exit(d1)
        print("   G1 empty: %s — %s" % (e1, p1[:200]), flush=True)
        # ── G2 «re-entry inside the guard» ────────────────────────────────
        d2, _ev, e2, p2 = output(s, gesture, "guasto-rientro", reenter_immediately=True)
        reborn = e2 == S.FAIL and bool(d2.get("births"))
        print("   G2 immediate re-entry (%s): %s — %s" % (d2.get("rientro_guasto"), e2, p2[:200]),
              flush=True)
        if not d2.get("finished") or "rientro_guasto" not in d2:
            E.fault("F-021", None, "G2 not injected: the real exit did not end or "
                     "the page did not go back to the form (%s)" % p2[:200])
            return
        E.fault("F-021", e1 == S.FAIL and reborn,
                 "G1 empty Exit ⇒ %s (%s) · G2 re-entry inside the guard ⇒ %s (%s)"
                 % (e1, p1[:120], e2, p2[:120]))


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify, extra=lambda a: a.add_argument(
        "--gesture", default="", help="another «Exit» gesture (diagnosis: e.g. XFCE without "
        "--fast, which saves the session like the menu dialog)")))
