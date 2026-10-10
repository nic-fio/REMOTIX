#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f024b — F-024b: A SESSION OPENED AND NEVER TOUCHED EXPIRES BY ABANDONMENT (§5.3)

    python3 15-f024b-sessione-mai-toccata.py --container_box kde --browser firefox --fault --port 8612

⭐ IT WATCHES DEFECT D-004.  The abandonment clock (`--abandon-s`,
   default 3600) fed ONLY on the five input gestures: `main.c`
   `input_to_child` → `presence_mark`.  A session in which nobody ever
   moved the mouse or pressed a key did not enter the presence table,
   and ⛔ never expired — against `SPECIFICHE.md` §5.3, «60 minutes without input ⇒
   the session closes».  F-024 (in `15-f022-orologi.py`) does not see it: it makes a
   click to unblock the audio, and the click puts the user in the table.
   The cure (clean-up D-004): the clock starts at the stage's BIRTH.

⛔ A SERVER OF ITS OWN (`15-g7-server.sh`, ports 8611-8614), like F-022/23/24: the clock
   is shortened from the command line.  At the end the server stays with the DEFAULTS.

F-024b (server with `--abandon-s 60`, default inactivity) you log in with the
       real browser and DO NOTHING: no click, no key, no
       scene launched ⇒ expected: within ABANDON_S + MARGIN_S of the login the
       tenant's «§5.3 — ABANDONMENT» line, and then the session DISAPPEARS: the
       compositor (gnome-shell / kwin_wayland / labwc) is no longer there, and of the
       tenant's processes only the exempt ones of F-021's rule remain
       (the `remotix` child and systemd's user manager with its services).
       FAULT: the LONG clock (the default, 3600 s), same sequence ⇒
       no ABANDONMENT in the same window and the session alive ⇒ the judge
       must say red.

⛔⛔ «NO GESTURE» IS VERIFIED, not presumed.  The bench makes none: the login
     (`Test.enter`) fills in and sends the form from JavaScript, the first
     frame is judged with photos (`snapshot_canvas`), and the photos do not
     go through the pointer.  ⚠ But a browser can generate pointer events
     by itself (a synthetic `mousemove` after a layout change, with
     labwc's pointer still over the window), and the page would forward them to the
     server as `POINTER` — that is as a gesture, which renews the clock.
     ⇒ The tenant's `input id=` lines in the server log are COUNTED
       (`rcp.c`, one for every message of the five types of the input channel,
       the same set that feeds `presence_mark`).  If there is even ONE the
       premise has fallen and the outcome is BLOCKED with the line — not a FAIL of the
       product and not a PASS.
"""
import importlib.util as _iu
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

_s = _iu.spec_from_file_location("g7comune", os.path.join(S.HERE, "15-g7-comune.py"))
G7 = _iu.module_from_spec(_s)
_s.loader.exec_module(G7)
G7.local_box(S)
_f = _iu.spec_from_file_location("f019", os.path.join(S.HERE, "15-f019-la-rete-cade.py"))
F019 = _iu.module_from_spec(_f)
_f.loader.exec_module(F019)

FUNCTIONS = ("F-024b",)
SERVER = "15-g7-server.sh"
PER_BROWSER = False
ABANDON_S = 60
MARGIN_S = 30          # the clock's turn + the stage's birth before the login
CLOSING_S = 40         # the closing of the graphical session is not instantaneous
ABANDON_MARK = "§5.3 — ABANDONMENT"
GESTURE_MARK = "input id="
# ⭐ The HEART of the session: the compositor.  ⚠ F-021's rule alone is not
#   enough: on GNOME the Shell is a service of the user manager
#   (`org.gnome.Shell@wayland.service`), that is EXEMPT for that rule ⇒ the
#   live session would have zero non-exempt processes, and «closed» would be true
#   by force.  The compositor is there on all four (the same list as F-016).
CORE_PROCESSES = ("gnome-shell", "kwin_wayland", "labwc")


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES (pure: --certify tests them)
# ═══════════════════════════════════════════════════════════════════════════
def lines_of(line_list, chi):
    """The lines naming the tenant.  ⛔ The name is looked for whole: a
    tenant c15024u11 must not take the lines of c15024u111."""
    outside = []
    for r in line_list:
        i = r.find(chi)
        while i >= 0:
            if not r[i + len(chi):i + len(chi) + 1].isdigit():
                outside.append(r)
                break
            i = r.find(chi, i + 1)
    return outside


def find_abandon(line_list, chi):
    for r in lines_of(line_list, chi):
        if ABANDON_MARK in r:
            return r
    return None


def gestures(line_list, chi):
    return [r for r in lines_of(line_list, chi) if GESTURE_MARK in r]


def heart(ps):
    """«name pid» of the compositors among the processes {pid: name}; None if unreadable."""
    if ps is None:
        return None
    return ["%s %d" % (n, p) for p, n in sorted(ps.items()) if n in CORE_PROCESSES]


def judge(d):
    """(outcome, reason) from the measured fields:
         born      the tenant's compositor AFTER the first frame
                   («name pid», list; empty = the session was not seen being born)
         gestures     the tenant's `input id=` lines (list)
         abandon the ABANDONMENT line, or None
         heart     the compositor at the end (list, or None = unreadable)
         remaining   the non-exempt processes at the end (list, or None = unreadable)
    ⛔ The order matters: first the premise (session born, no gesture), then the
       product's facts."""
    if not d.get("born"):
        return S.BLOCKED, ("the session was not seen being born (no %s compositor "
                           "of the tenant after the first frame): there is nothing that "
                           "can expire" % "/".join(CORE_PROCESSES))
    if d.get("gestures"):
        return S.BLOCKED, ("the premise has fallen: %d gestures that the bench did not make "
                           "reached the server (the first: %s) — they renew the clock"
                           % (len(d["gestures"]), d["gestures"][0][:160]))
    if d.get("remaining") is None or d.get("heart") is None:
        return S.BLOCKED, "I could not read the tenant's processes"
    if not d.get("abandon"):
        return S.FAIL, ("no ABANDONMENT within %d s of a login without any gesture "
                        "(compositor at the end: %s)"
                        % (ABANDON_S + MARGIN_S, ", ".join(d["heart"]) or "gone"))
    if d["heart"] or d["remaining"]:
        return S.FAIL, ("ABANDONMENT written, but the session did not close: compositor "
                        "%s · non-exempt %s" % (", ".join(d["heart"]) or "gone",
                                                ", ".join(d["remaining"])[:180] or "none"))
    return S.PASS, ("abandonment without any gesture: compositor gone, no non-exempt "
                    "process left")


def certify():
    ok = True

    def prova(label_name, real):
        nonlocal ok
        if not real:
            print("⛔ " + label_name)
            ok = False

    chi = "c15024u111"
    ab = "21:00 startup ⭐ §5.3 — ABANDONMENT: «%s» has touched nothing for 61000 ms (ceiling 60000)"
    gesture = "21:00 rcp [%s] input id=3 (was 2) POINTER 10,10 · client instant 1 us"
    prova("the tenant's ABANDONMENT is seen", find_abandon([ab % chi], chi))
    prova("the ABANDONMENT of ANOTHER tenant does not count",
          find_abandon([ab % "c15024u222"], chi) is None)
    prova("the ABANDONMENT of a longer name does not count",
          find_abandon([ab % "c15024u1110"], chi) is None)
    prova("a gesture of the tenant is counted", len(gestures([gesture % chi], chi)) == 1)
    prova("a gesture of another is not counted", not gestures([gesture % "c15024u222"], chi))
    prova("the heart is read from the processes",
          heart({1: "bash", 9: "kwin_wayland"}) == ["kwin_wayland 9"]
          and heart({1: "bash"}) == [] and heart(None) is None)
    viva = ["labwc 4242"]
    base = {"born": viva, "gestures": [], "abandon": ab % chi, "heart": [], "remaining": []}
    prova("abandonment, compositor gone, nothing left ⇒ PASS",
          judge(base)[0] == S.PASS)
    prova("no abandonment ⇒ FAIL (the defect D-004)",
          judge(dict(base, abandon=None, heart=viva))[0] == S.FAIL)
    prova("no abandonment on GNOME (zero non-exempt, the Shell is a service) ⇒ FAIL",
          judge(dict(base, abandon=None, heart=["gnome-shell 7"]))[0] == S.FAIL)
    prova("abandonment but compositor alive ⇒ FAIL", judge(dict(base, heart=viva))[0] == S.FAIL)
    prova("abandonment but non-exempt processes left ⇒ FAIL",
          judge(dict(base, remaining=["xfce4-panel|0::/user.slice/x/session-5.scope"]))[0]
          == S.FAIL)
    prova("a gesture not made by the bench ⇒ BLOCKED, neither PASS nor FAIL",
          judge(dict(base, gestures=[gesture % chi]))[0] == S.BLOCKED)
    prova("session never born ⇒ BLOCKED (it would be «closed» by force)",
          judge(dict(base, born=[]))[0] == S.BLOCKED)
    prova("unreadable processes ⇒ BLOCKED",
          judge(dict(base, remaining=None))[0] == S.BLOCKED
          and judge(dict(base, heart=None))[0] == S.BLOCKED)
    prova("the short clock and the wait stay below the default",
          ABANDON_S + MARGIN_S + CLOSING_S < 3600)
    print("%s F-024b judges" % ("⭐" if ok else "⛔"))
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def _f021():
    sp = _iu.spec_from_file_location("f021", os.path.join(S.HERE, "15-f021-esci.py"))
    m = _iu.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def turn_on(o, *opt):
    ok, t = G7.server("turn_on", o.container_box, *opt)
    if not ok:
        raise S.Blocked("our server does not start (%s): %s" % (" ".join(opt), t[-300:]))
    idle, aband, _r = G7.clocks_in_effect(o.container_box)
    print("   our server: inactivity %s s · abandonment %s s" % (idle, aband), flush=True)
    return aband


def passed(o, E, reg, short):
    """short=True: the healthy pass; False: the FAULT (the long clock)."""
    F021 = _f021()
    with S.Session(o, "024", E) as s:
        sign = reg.line_list()
        # ⛔ NO GESTURE: no `click_canvas`, no scene, no keys.  You
        #    just log in (form filled in from JavaScript, first frame
        #    judged with photos).
        ok, m = s.enter()
        if not ok:
            raise S.Blocked("you cannot get in: " + m)
        t_access = time.time()
        born = heart(G7.tenant_processes(o.container_box, s.chi)) or []
        # the wait: the ABANDONMENT line, within abandonment + margin of the login
        shape, row, _d = reg.wait_for(sign, [ABANDON_MARK], s.chi,
                                      ceiling=ABANDON_S + MARGIN_S, step=2.0)
        after = time.time() - t_access
        # the closing: the compositor and the non-exempt processes must disappear
        fine = time.time() + (CLOSING_S if shape else 0)
        while True:
            heart_now = heart(G7.tenant_processes(o.container_box, s.chi))
            remaining = F021.leftovers(F021.processes(s))
            if (not heart_now and not remaining) or time.time() >= fine:
                break
            time.sleep(2)
        line_list = reg.da(sign, s.chi)
        page_map = G7.page_v(s.g)
        d = {"born": born, "gestures": gestures(line_list, s.chi),
             "abandon": find_abandon(line_list, s.chi), "heart": heart_now,
             "remaining": remaining}
        outcome, rationale = judge(d)
        if not short:
            if outcome == S.BLOCKED:
                E.blocked(["F-024b"], "pass with the fault: " + rationale, passed="fault")
                return
            red = outcome == S.FAIL and not d["abandon"]
            E.fault("F-024b", red,
                     "LONG clock ⇒ the judge %s" % (
                         "sees no ABANDONMENT in %d s and the session is alive (red)"
                         % (ABANDON_S + MARGIN_S) if red
                         else "says %s: %s" % (outcome, rationale[:150])))
            return
        ev = [s.save_text("server-f024b.txt", line_list),
              s.save_text("processi-f024b.txt",
                            "compositor at birth:\n%s\ncompositor at the end:\n%s\n"
                            "non-exempt at the end:\n%s"
                            % ("\n".join(born), "\n".join(heart_now or ["(none)"]),
                               "\n".join(remaining or ["(none or unreadable)"]))),
              s.save_text("pagina-f024b.txt",
                            "\n".join("%s: %s" % kv for kv in page_map.items()))]
        expected_val = ("login and then NO gesture ⇒ within %d s the «§5.3 — ABANDONMENT» line and the "
                  "session closes (compositor gone, non-exempt gone: rule of "
                  "F-021)" % (ABANDON_S + MARGIN_S))
        oss = ("line: %s · %.0f s after the login · gestures that reached the server %d · compositor "
               "at birth %s, at the end %s · non-exempt at the end %s · page: «%s»"
               % ((row or "NONE")[:140], after, len(d["gestures"]), ", ".join(born),
                  ", ".join(heart_now or []) or "gone",
                  "?" if remaining is None else len(remaining), (page_map.get("outcome") or "")[:80]))
        E.put("F-024b", outcome, rationale, expected_val=expected_val, observed=oss, evidence=ev)


def body_el(o, E):
    if not o.port:
        o.port = G7.PORTS_G7[o.container_box]
        o.url = "https://%s:%d/" % (o.host, o.port)
    if o.port != G7.PORTS_G7[o.container_box]:
        raise S.Blocked("port %d is not our server's (%d)"
                         % (o.port, G7.PORTS_G7[o.container_box]))
    before_8511 = F019.healthy_8511(o)
    reg = G7.Log(o.container_box)
    try:
        if turn_on(o, "--abandon-s", str(ABANDON_S)) != ABANDON_S:
            raise S.Blocked("the abandonment clock is not the one requested (%d s)"
                             % ABANDON_S)
        passed(o, E, reg, short=True)
        if o.fault:
            try:
                turn_on(o)                            # the LONG one: the default
                passed(o, E, reg, short=False)
            except S.Blocked as b:
                E.blocked(["F-024b"], str(b), passed="fault")
    finally:
        idle, aband, _r = G7.clocks_in_effect(o.container_box)
        if (idle, aband) != (1800, 3600):
            G7.server("turn_on", o.container_box)           # left with the defaults
        after_8511 = F019.healthy_8511(o)
        print("   851x server before «%s» after «%s»%s" % (
            before_8511, after_8511, "" if before_8511 == after_8511 else "  ⛔ CHANGED"), flush=True)


if __name__ == "__main__":
    sys.exit(S.execute(__doc__, FUNCTIONS, body_el, certify))
