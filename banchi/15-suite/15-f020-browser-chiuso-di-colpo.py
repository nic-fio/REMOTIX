#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f020 — F-020 THE BROWSER KILLED ABRUPTLY, THEN A NEW BROWSER · path P-E

    python3 15-f020-browser-chiuso-di-colpo.py --box lxqt --browser chrome [--fault]

The scene is that of 15-f016 (15-g6-comune): firefox-esr in the session, a
text written with real keys and read in colours in the photo; the program writes down
its state (token, value) every 2 s.

  P-E  creation → application open, text written → the browser KILLED
       (kill -9 of the process and of ALL its children: no farewell, the wire
       just goes silent) → a NEW browser (new profile) → same user and password
       → state found again → input.

F-020  expected (`SPECIFICHE.md` §5.1, §5.3; `src/rcp.c` ~265-350):
       - the old wire did not say farewell: for the server it is a client that
         IS SILENT.  As long as it has been silent for less than 15 s the slot is its own (the «ghost
         eviction», `DEFAULT_EVICTION` = SILENZIO/2) and the new login may
         be refused with `0x0F` («this session's slot shows as
         taken… try again in a few seconds»): it is the DECLARED
         behaviour, not a defect — we retry every 3 s, like the user;
       - within SILENZIO (30 s) + margin (CAP_S = 40 s from the kill) one must
         GET IN, and find the SAME session again: same PID of the compositor and
         of the scene (field), same token and text (field), window and
         strip in the photo.
P-E    expected: F-020 and, afterwards, the input arrives (new letters read in the photo).

FAULT (real, in the scene): the browser is killed again and meanwhile the tenant's
       SESSION is killed (loginctl terminate-user + kill -9 of their
       processes) — that is «the session does not survive the client».  The re-entry makes
       a NEW session be born: F-020 and P-E must give RED (token,
       PID, window: nothing matches).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._load("g6", os.path.join(S.HERE, "15-g6-comune.py"))
F16 = S._load("f016", os.path.join(S.HERE, "15-f016-stacco-e-riattacco.py"))
FUNCTIONS = ("F-020", "P-E")
CAP_S = 40.0           # SILENCE (30 s, §5.3) + the margin of the 3 s between one attempt and the next
GHOST_S = 15.0        # DEFAULT_EVICTION: below it, a 0x0F refusal is the expectation


def judge_reentry(ok, seconds, refusals, before, after, vista, state, text, token):
    """F-020.  Returns (outcome, reason)."""
    if not ok:
        return S.FAIL, ("no re-entry in %.0f s from the browser's kill (cap %d s = "
                        "silence + margin); refusals: %s" % (seconds, CAP_S,
                                                               " | ".join(refusals)[:400]))
    probs = []
    out_of_time = [r for r in refusals if "taken" not in r]
    if out_of_time:
        probs.append("refusals that are NOT the ghost's taken slot: %s"
                     % " | ".join(out_of_time)[:300])
    pf0, pf1 = G.scene_pid(before), G.scene_pid(after)
    if pf0 is None:
        return S.BLOCKED, "before the kill the scene was not there"
    if pf1 != pf0:
        probs.append("the scene's program was %s, after %s" % (pf0, pf1))
    for comp in ("gnome-shell", "kwin_wayland", "labwc"):
        if before.get(comp) and sorted(before[comp]) != sorted(after.get(comp) or []):
            probs.append("the compositor %s was %s, after %s" % (comp, before[comp],
                                                               after.get(comp)))
    e, r = F16.judge_finding_again(text, vista, state, token)
    if e != S.PASS:
        probs.append(r)
    if probs:
        return S.FAIL, "; ".join(probs)
    return S.PASS, ("back in %.1f s after the kill (%d refusals from the ghost before): "
                    "same session, same PIDs, %s" % (seconds, len(refusals), r))


def certify():
    ok = True

    def prova(what, real):
        nonlocal ok
        ok &= bool(real)
        print("%s %s" % ("⭐" if real else "⛔", what))
    pr = {"firefox-esr": ["100"], "labwc": ["90"]}
    vista = G.look_scene(F16._Fake(F16.fake_scene("abc")), "x")
    st = {"g": "x", "v": "abc"}
    e, m = judge_reentry(True, 17.0, ["3.0s the login: the page says: «this session's slot "
                                        "shows as taken by another client»"], pr, pr, vista, st, "abc", "x")
    prova("re-entry after the ghost ⇒ PASS (%s)" % m[:60], e == S.PASS)
    e, _ = judge_reentry(False, 41.0, ["taken"] * 12, pr, pr, vista, st, "abc", "x")
    prova("never back in ⇒ FAIL", e == S.FAIL)
    blank = G.look_scene(F16._Fake(F16.fake_scene(None)), "x")
    e, _ = judge_reentry(True, 5.0, [], pr, {"labwc": ["300"]}, blank,
                           {"g": "new", "v": ""}, "abc", "x")
    prova("session reborn ⇒ FAIL", e == S.FAIL)
    e, _ = judge_reentry(True, 5.0, ["3.0s the login: no admission"], pr, pr, vista, st,
                           "abc", "x")
    prova("a refusal that is not the ghost ⇒ FAIL", e == S.FAIL)
    return 0 if ok else 1


def one_round(o, E, s, text, passed, fault=False):
    put = (lambda f, e, r, **k: E.fault(f, e == S.FAIL, "fault (session killed): " + r, **k)) \
        if fault else (lambda f, e, r, **k: E.put(f, e, r, passed=passed, **k))
    q0 = G.notebook(s)
    token = next((r.get("g") for r in reversed(q0) if r.get("v") == text), None)
    before = G.processes(s)
    sign = s.log_mark()
    print("   before: %s · token %s" % (before, token), flush=True)
    # ── THE BROWSER KILLED: kill -9 of the whole tree, no farewell
    n = G.kill_browser(s)
    t_kill = time.time()
    print("   ⛔ browser killed: %d processes (kill -9)" % n, flush=True)
    if fault:
        c, t = s.sc.inside("loginctl terminate-user %s >/dev/null 2>&1; sleep 1; "
                           "pkill -KILL -u %s; sleep 2; pgrep -u %s -x firefox-esr || "
                           "echo 'session killed'" % (s.chi, s.chi, s.chi), 60)
        print("   ⛔ FAULT: %s" % t.strip()[-60:], flush=True)
    # ── A NEW BROWSER, at once: if the ghost holds the slot, we retry
    s.turn_on_browser()
    ok, m, refusals, _sec = G.enter_with_retry(s, cap_s=CAP_S - (time.time() - t_kill))
    seconds = time.time() - t_kill
    reg = s.log_from(sign) if sign is not None else []
    ev = [s.save_text("server-%s.txt" % passed, reg)]
    evic = [r for r in reg if "evict" in r.lower() or "ghost" in r.lower()]
    vista, state, after = {"window": None, "why": "not back in"}, None, {}
    if ok:
        vista = G.wait_text(s, text, "rientro-%s" % passed,
                                cap=12 if not fault else 20)
        state = G.last_state(s)
        after = G.processes(s)
    e20, r20 = judge_reentry(ok, seconds, refusals, before, after, vista, state, text, token)
    put("F-020", e20, r20,
          expected="within %d s of the kill: admitted (before the %d s a «slot "
                 "taken» refusal is the expectation), same session, state found again" % (CAP_S, GHOST_S),
          observed="%s · re-entry at %.1f s · refusals %d · ghost log: %s · PID %s → %s"
          % (m[:120], seconds, len(refusals), (evic[-1].split("] ", 1)[-1][:160] if evic else "—"),
             G.scene_pid(before), G.scene_pid(after)),
          evidence=ev + [vista.get("photo", "")])
    # ── P-E: the input afterwards
    in_ok, r_in = False, "no window to write on"
    if ok and vista.get("window"):
        add = F16.random_text(2)
        cl = G.click_on_scene(s, vista)
        G.write(s, add)
        v2 = G.wait_text(s, text + add, "input-dopo-%s" % passed, cap=10)
        in_ok = v2.get("read") == text + add
        r_in = "written «%s» (%s): the photo reads «%s»" % (add, cl, v2.get("read"))
        if in_ok:
            text = text + add
    ee = S.PASS if (e20 == S.PASS and in_ok) else S.FAIL
    put("P-E", ee, "re-entry %s · input after: %s" % (e20, r_in),
          expected="creation→browser killed→new connection→state→input",
          observed=r_in, evidence=ev)
    return text


def body(o, E):
    with S.Session(o, "020", E) as s:
        try:
            ok, m = s.enter()
            if not ok:
                raise S.Blocked("without login there is nothing to kill: " + m)
            ok, t = G.turn_on_scene(s)
            if not ok:
                raise S.Blocked("the scene does not start in the session: " + t[-200:])
            G.wake(s)
            v = F16.find_scene(s)
            if not v.get("window"):
                raise S.Blocked("the scene's window is not seen in the photo: %s"
                                 % v.get("why"))
            text = F16.random_text(4)
            v, note = G.write_base(s, v, text)
            if v.get("read") != text:
                raise S.Blocked("the PREPARATION input does not reach the scene (it is F-004/F-007, "
                                 "not this function): %s" % " | ".join(note))
            text = one_round(o, E, s, text, "healthy")
            if o.fault:
                if s.g is None:
                    s.turn_on_browser()
                one_round(o, E, s, text, "fault", fault=True)
        finally:
            if s.g:
                s.save_console()
            G.turn_off_server(s)


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify))
