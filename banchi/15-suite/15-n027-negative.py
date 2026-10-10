#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-n027 — THE NEGATIVE TESTS (fasi/15 §«Negative tests», adapted)

    python3 15-n027-negative.py --container_box lxqt --browser firefox --base-ports 4930 [--fault]

N-1  nonexistent user .............. lives in 15-f027 (on the G8 server: it counts as an error)
N-2  wrong password ................ is F-027 (15-f027)
N-3  session already closed with «Exit» ⇒ the new login makes a NEW and CLEAN
     session be born.  Normal server (85xx).  The tenant logs in, opens a scene
     of known colour (YELLOW), exits with their desktop's «Exit» gesture (the same as
     C20/C24: the D-Bus method the menu reaches).  Expected: the product says
     the session ended, the page goes back to the form, the session's programs
     are no longer there; coming back in, the server MAKES a session BE BORN («I AM
     MAKING IT BE BORN») and the canvas — real desktop, not degenerate — does NOT show the yellow.
N-4  network not available.  On the G8 server (port 862x): the page is loaded,
     then the server is TURNED OFF, and the user presses «Connect».  Expected: within 40 s
     the page says it cannot connect (outcome «male», a sentence), no
     «Admitted», it does not stay hung.  And the page reloaded with the server off: what
     the browser says (it is recorded; the product's page is not there).  At the
     end the G8 server is started again.
N-5  same user already active from another device ... is F-025 (15-f025).

FAULTS:
  N-3  instead of «Exit», a DETACH (the page goes to about:blank: the wire
       drops, the session stays) and we come back in ⇒ the yellow scene is still there and
       no session is born ⇒ the judge must say red.
  N-4  the server is NOT turned off ⇒ «Admitted» ⇒ the judge must say red.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._load("g8", os.path.join(S.HERE, "15-g8-comune.py"))
FUNCTIONS = ("N-3", "N-4")
PER_BROWSER = False
SERVER = "15-g8-server.sh"
YELLOW = (220, 200, 30)
COLORS = {"yellow": YELLOW}
BIRTH = "I AM MAKING IT BE BORN"
FINISHED = [p for p, _d in S.C20V.C20.FINISHED_LINES]


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES — pure
# ═══════════════════════════════════════════════════════════════════════════
def judge_reentry(ended, page_module, processes_after, reentry_lines, entered, fr):
    """N-3: (outcome, reason)."""
    if not ended:
        return S.BLOCKED, "the product did not declare the session ended: «Exit» not observable"
    if not entered:
        return S.FAIL, "after «Exit» you do not get back in"
    if fr is None:
        return S.BLOCKED, "back in, but the canvas cannot be photographed"
    troubles = []
    if not any(BIRTH in r for r in reentry_lines):
        troubles.append("at the re-entry the server does NOT make a session be born")
    if fr.get("yellow", 0) > 0.01:
        troubles.append("the closed session's scene is still there (yellow %.1f%%)" % (100 * fr["yellow"]))
    if processes_after:
        troubles.append("after «Exit» %d processes of the scene remain" % processes_after)
    if troubles:
        return S.FAIL, "; ".join(troubles)
    return S.PASS, ("ended, form %s, no program left, at the re-entry session BORN and canvas "
                    "clean (yellow %.2f%%)" % ("visible" if page_module else "after reload",
                                                100 * fr.get("yellow", 0)))


def judge_without_network(admitted, state, wait_s):
    """N-4: (outcome, reason)."""
    outcome = (state or {}).get("outcome") or ""
    if admitted is True:
        return S.FAIL, "server off and the page says «%s»" % outcome
    if (state or {}).get("esito_classe") == "male" and outcome.strip():
        return S.PASS, "in %.0f s the page says «%s»" % (wait_s, outcome[:120])
    return S.FAIL, ("server off: after %.0f s the page stays hung without saying anything clear "
                    "(outcome «%s»)" % (wait_s, outcome[:120]))


def certify():
    ok = True

    def prova(what, real):
        nonlocal ok
        ok &= bool(real)
        print("%s %s" % ("⭐" if real else "⛔", what))
    born = ["[c] ⭐ no graphical session for «c»: I AM MAKING IT BE BORN (canvas 1x1)"]
    prova("clean re-entry ⇒ PASS", judge_reentry(True, True, 0, born, True, {"yellow": 0.0})[0] == S.PASS)
    prova("scene still there ⇒ FAIL", judge_reentry(True, True, 0, born, True, {"yellow": 0.8})[0] == S.FAIL)
    prova("no birth ⇒ FAIL", judge_reentry(True, True, 0, [], True, {"yellow": 0.0})[0] == S.FAIL)
    prova("programs left ⇒ FAIL", judge_reentry(True, True, 2, born, True, {"yellow": 0.0})[0] == S.FAIL)
    prova("not ended ⇒ BLOCKED", judge_reentry(False, True, 0, born, True, {"yellow": 0.0})[0] == S.BLOCKED)
    prova("without network, sentence ⇒ PASS", judge_without_network(
        False, {"esito_classe": "male", "outcome": "the server does not answer"}, 5)[0] == S.PASS)
    prova("without network, admitted ⇒ FAIL", judge_without_network(True, {"outcome": "Admitted"}, 5)[0] == S.FAIL)
    prova("without network, hung ⇒ FAIL", judge_without_network(
        None, {"esito_classe": "", "outcome": "Connecting…"}, 40)[0] == S.FAIL)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def scene_processes(sc, chi):
    # ⚠ only the session's APPLICATION: the scene's server was
    #   launched by the bench outside the session (runuser), and «Exit» does not see it
    c, t = G.inside(sc, "pgrep -u %s -x firefox-esr 2>/dev/null | wc -l; true" % chi, 30)
    try:
        return int(t.split()[-1])
    except (ValueError, IndexError):
        return None


def yellow_scene(o, s):
    S.C21.wake(s.g, s.geometry())
    ok, t = G.turn_on_scene(s.sc, s.chi, o.base_ports + G.MOVE_SCENE, YELLOW)
    if not ok:
        return None, "the yellow scene does not start: %s" % " | ".join(t.splitlines()[-5:])[-300:]
    fr, dove, reason_text = G.wait_color(s, "scena-gialla", COLORS, "yellow", 0.5, 40)
    if not fr or fr["yellow"] < 0.5:
        return None, "the yellow scene does not cover the canvas: %s %s" % (G.fr_text(fr), reason_text)
    return fr, dove


def reenter_and_look(s, sign, pause_v=8):
    """Comes back in (from the form if it is there, otherwise by reloading) and photographs after `pause_v` s.
    Returns (got in, fractions, server lines from the mark, photo)."""
    p = G.read_page(s.g)
    if p.get("module"):
        e, m, st = s.pr.enter(s.password)
        ok = e == S.GREEN
        if ok:
            e, m, st = s.pr.first_frame()
            e, m = S.C20V.desktop_dark_but_alive(e, m, st)
            ok = e == S.GREEN
    else:
        ok, m = s.enter()
    if not ok:
        return False, None, s.log_from(sign), m
    time.sleep(pause_v)
    png, dove = s.picture("reentry")
    fr = G.fractions(png, COLORS) if png else None
    return True, fr, s.log_from(sign), dove


def n3(o, E):
    with S.Session(o, "027", E) as s:
        ok, m = s.enter()
        if not ok:
            raise S.Blocked("the tenant does not get in: " + m)
        fr, dove = yellow_scene(o, s)
        if fr is None:
            raise S.Blocked(dove)
        ev = [dove]
        desk, gesture = s.sc.exit_gesture()
        if not gesture:
            raise S.Blocked("I do not know how to say «Exit» in this box")
        sign = s.log_mark()
        c, t = s.as_user(gesture)
        shape, _r = S.C20V.wait_line(s.sc, sign, s.chi, FINISHED, 60)
        module = False
        fine = time.time() + 30
        while time.time() < fine:
            if G.read_page(s.g).get("module"):
                module = True
                break
            time.sleep(1)
        page_map = G.read_page(s.g)
        proc = None
        fine = time.time() + 20
        while time.time() < fine:
            proc = scene_processes(s.sc, s.chi)
            if proc == 0:
                break
            time.sleep(2)
        sign2 = s.log_mark()
        entered, fr2, line_list, dove2 = reenter_and_look(s, sign2)
        ev.append(dove2 if entered else "")
        e, r = judge_reentry(bool(shape), module, proc, line_list, entered, fr2)
        ev.append(s.save_text("n3-server.txt", s.log_from(sign)))
        E.put("N-3", e, r, expected_val="«Exit» (%s) ⇒ session ended, form, no program; at the "
                "re-entry a NEW and clean session" % desk,
                observed="%s · the product: «%s» · the page after «Exit»: «%s»" % (
                    r, shape, (page_map.get("outcome") or "")[:80]), evidence=[x for x in ev if x])

        if o.fault:
            fr, dove = yellow_scene(o, s)
            if fr is None:
                E.fault("N-3", None, "the yellow scene does not start again: " + dove)
                return
            s.g.go_to("about:blank")                     # ⛔ the fault: detach, not «Exit»
            time.sleep(4)
            sign3 = s.log_mark()
            entered, fr3, line_list, _d = reenter_and_look(s, sign3)
            eg, rg = judge_reentry(True, True, 0, line_list, entered, fr3)
            E.fault("N-3", eg == S.FAIL if eg != S.BLOCKED else None,
                     "detach instead of «Exit» ⇒ the judge says %s: %s" % (eg, rg))


def n4(o, E):
    srv = G.MyServer(o.container_box)
    if not srv.lit():
        ok, t = srv.turn_on()
        if not ok:
            E.put("N-4", S.BLOCKED, "the G8 server does not start: " + t)
            return
    o4 = G.o_per(o, 1)
    o4.port = srv.port
    o4.url = "https://%s:%d/" % (o.host, srv.port)
    srv.unblock()
    try:
        with S.Session(o4, "027", E) as s:
            ok, m = s.pr.open_it()
            if not ok:
                E.put("N-4", S.BLOCKED, "the G8 server's page does not open: " + m)
                return
            off, t = srv.turn_off()
            time.sleep(1)
            t0 = time.time()
            accepted, st = G.try_without_reload(s, s.chi, s.password, 40)
            wait = time.time() - t0
            e, r = judge_without_network(accepted, st, wait)
            reloaded = G.load(s.g, o4.url, 30)
            browser_says = " ".join((reloaded.get("body_text") or reloaded.get("failure")
                                     or reloaded.get("non_aperta") or "").split())[:160]
            ev = [s.save_text("n4-pagina.txt", [str(st.get("logbook") or "")[-3000:],
                                                  "---", str(reloaded)])]
            E.put("N-4", e, r, expected_val="server off ⇒ within 40 s a clear sentence, no "
                    "«Admitted», the page does not stay hung",
                    observed="%s · reloaded with the server off the browser says: «%s» (%s)" % (
                        r, browser_says, t.splitlines()[-1] if t else "?"), evidence=ev)
            ok, t = srv.turn_on()
            if o.fault:
                if not ok:
                    E.fault("N-4", None, "the G8 server does not start again: " + t)
                else:
                    t0 = time.time()
                    accepted, st = G.attempt(s, s.chi, s.password, 40)
                    eg, rg = judge_without_network(accepted, st, time.time() - t0)
                    E.fault("N-4", eg == S.FAIL if accepted is not None else None,
                             "server on instead of off ⇒ the judge says %s: %s" % (eg, rg))
    finally:
        if not srv.lit():
            print("   G8 server restarted: %s" % (srv.turn_on(),), flush=True)


def body_el(o, E):
    try:
        n3(o, E)
    except S.Blocked as b:
        E.blocked(["N-3"], str(b))
        if o.fault:
            E.blocked(["N-3"], str(b), passed="fault")
    n4(o, E)


if __name__ == "__main__":
    sys.exit(S.execute(__doc__, FUNCTIONS, body_el, certify))
