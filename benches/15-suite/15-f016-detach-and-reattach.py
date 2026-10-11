#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f016 — F-016 DETACH · F-017 REATTACH AT THE SAME SIZE · paths P-A and P-F

    python3 15-f016-detach-and-reattach.py --box kde --browser chrome [--fault]

The scene (15-g6-common): in the session a firefox-esr with a cyan background, a
text field and the STRIP that shows in colours what is written in it; the
program writes down every 2 s its state (token, value, screen) in a file.

  P-A/P-F  creation → desktop → application open → REAL INPUT (click on the
           scene and letters written by the browser) → DETACH (the browser closes,
           with its farewell) → WAIT 35 s (beyond the silence clock, §5.3)
           → REATTACH (new browser, same user and password) → STATE → INPUT.

F-016  expected: after the detach and the wait the session stays and the programs stay.
       fields: the PID of the scene's firefox-esr and that of the compositor are
       the SAME as before; the logind session is there; the scene keeps
       beating (new lines in the notebook AFTER the wait, with the SAME token and
       the same text); the server log does not say the session dies.
F-017  expected: coming back in ⇒ admitted, and the STATE is found again — from the PHOTO: the
       cyan window is there and the strip reads the text written before; from the
       FIELD: same token (the page was not reborn), same value.
       ⚠ The page's sentence («Admitted, new|resumed session») is looked at:
       `RCP.md` §4 (`SESSION`, state 1 = NEW, 2 = RESUMED).
P-A    expected: the input AFTER the reattach arrives too (new letters read in the photo).
P-F    expected: F-016 and F-017 together (application open, wait, state).

FAULT (real, in the scene): we detach again and during the detach we KILL the
       scene's program (kill -9 of the tenant's firefox-esr) — that is
       «the programs do not stay».  The same tests must give RED: F-016
       (PID gone, beats stopped), F-017 (neither window nor text), P-A, P-F.
"""
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._load("g6", os.path.join(S.HERE, "15-g6-common.py"))
FUNCTIONS = ("F-016", "F-017", "P-A", "P-F")
WAIT_S = 35          # beyond the 30 s of silence (§5.3): the session must stay
# ⛔ the log lines that would mean «the session died with the client»
# ⚠ (10 Oct 2026) «la session e' dead_run» was removed: the product never wrote it
#   in a log line (only in a comment of child.c); the death of the graphical
#   session reaches the log as «the graphical session is over» (main.c, §7.6).
DEATH = ("a NEW one will be born", "the graphical session is over", "SESSION_TERMINATED")


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES (pure)
# ═══════════════════════════════════════════════════════════════════════════
def judge_detach(before, after, q_after, t_wait_end_ms, text, log):
    """F-016.  prima/dopo: {name: [pid]} (G.processi); q_dopo: notebook;
    returns (outcome, reason)."""
    probs = []
    pf0, pf1 = G.scene_pid(before), G.scene_pid(after)
    if pf0 is None:
        return S.BLOCKED, "before the detach the scene was not there: nothing to compare"
    if pf1 != pf0:
        probs.append("the scene's program (firefox-esr %s) after the detach %s"
                     % (pf0, "IS NO LONGER THERE" if pf1 is None else "is ANOTHER one (%s)" % pf1))
    for comp in ("gnome-shell", "kwin_wayland", "labwc"):
        if before.get(comp):
            if sorted(before[comp]) != sorted(after.get(comp) or []):
                probs.append("the compositor %s was %s, after %s"
                             % (comp, before[comp], after.get(comp)))
    if before.get("session") and not after.get("session"):
        probs.append("the logind session %s is no longer there" % before["session"])
    beats = [r for r in q_after if r.get("t", 0) >= t_wait_end_ms]
    g0 = None
    for r in q_after:
        if r.get("t", 0) < t_wait_end_ms and r.get("v") == text:
            g0 = r.get("g")
    if not beats:
        probs.append("the scene no longer beats after the wait (no new line in the notebook)")
    elif g0 and any(r.get("g") != g0 for r in beats):
        probs.append("the scene has a NEW token: the page was reborn")
    elif beats[-1].get("v") != text:
        probs.append("the scene's text is «%s», not «%s»" % (beats[-1].get("v"), text))
    death = [r for r in log if any(m in r for m in DEATH)]
    vive = [r for r in log if "(I4)" in r or "invariant I4" in r]
    if not vive:
        probs.append("the server log (%d lines since the detach) does not say the stage "
                     "stays (no «I4» line)" % len(log))
    if death:
        probs.append("the server log says the session ends: «%s»" % death[0][-200:])
    if probs:
        return S.FAIL, "; ".join(probs)
    return S.PASS, ("log: «%s» · after %d s detached: firefox-esr %s and compositor alive, same PIDs; "
                    "session %s; the scene still beats (%d lines after the wait, same "
                    "token, text «%s»)" % (vive[0].split("] ", 1)[-1][:90], WAIT_S, pf0, (after.get("session") or ["?"])[0],
                                              len(beats), text))


def judge_finding_again(text, vista, state_after, token_before):
    """F-017 (the state).  vista: G.look_scene; stato_dopo: last line of the
    notebook.  Returns (outcome, reason)."""
    probs = []
    blind = vista.get("png") is None and "window" in vista and vista.get("photo") is not None
    if blind:
        pass                     # the photo could not be taken: the fields decide, or BLOCKED
    elif not vista.get("window"):
        probs.append("in the photo the scene's window is NOT there (%s)" % vista.get("why"))
    elif vista.get("read") != text:
        probs.append("in the photo the strip says «%s» (raw %s), written before «%s»"
                     % (vista.get("read"), vista.get("raw"), text))
    if not state_after:
        probs.append("the scene no longer writes its state")
    else:
        if token_before and state_after.get("g") != token_before:
            probs.append("the scene's token changed (%s → %s): it was reborn"
                         % (token_before, state_after.get("g")))
        if state_after.get("v") != text:
            probs.append("the scene's field is «%s», not «%s»" % (state_after.get("v"), text))
    if probs:
        return S.FAIL, "; ".join(probs) + (" (the photo could not be taken: %s)"
                                           % vista.get("why") if blind else "")
    if blind:
        return S.BLOCKED, "the fields add up, but the photo could not be taken: %s" % vista.get("why")
    return S.PASS, ("found again: window in the photo, strip «%s», token %s unchanged"
                    % (text, token_before))


def judge_sentence(outcome):
    """The sentence the user reads at reattach (RCP §4: 2 = RESUMED)."""
    e = outcome or ""
    if "resumed session" in e:
        return True, "the page says «%s»" % e
    return False, ("the page says «%s» to a RESUMED session (RCP.md §4: state 2 = "
                   "RESUMED; src/rcp.c always sends 1 = NEW)" % e)


def certify():
    ok = True

    def prova(what, real):
        nonlocal ok
        ok &= bool(real)
        print("%s %s" % ("⭐" if real else "⛔", what))
    pr = {"firefox-esr": ["100", "120"], "labwc": ["90"], "session": ["c7"]}
    q = [{"g": "x", "v": "abc", "t": 1000}, {"g": "x", "v": "abc", "t": 5000}]
    I4 = ["x child [u] the stage stays up (I4)"]
    e, m = judge_detach(pr, pr, q, 3000, "abc", I4)
    prova("healthy detach ⇒ PASS (%s)" % m[:50], e == S.PASS)
    e, _ = judge_detach(pr, pr, q, 3000, "abc", [])
    prova("log without I4 ⇒ FAIL", e == S.FAIL)
    e, m = judge_detach(pr, {"labwc": ["90"], "session": ["c7"]}, q[:1], 3000, "abc", I4)
    prova("program killed ⇒ FAIL (%s)" % m[:60], e == S.FAIL)
    e, _ = judge_detach(pr, pr, q + [{"g": "y", "v": "", "t": 6000}], 3000, "abc", I4)
    prova("page reborn ⇒ FAIL", e == S.FAIL)
    e, _ = judge_detach(pr, pr, q, 3000, "abc", I4 + ["... a NEW one will be born"])
    prova("death log ⇒ FAIL", e == S.FAIL)
    # the photo: a synthetic scene with «abc» in the strip
    png = fake_scene("abc")
    v = G.look_scene(_Fake(png), "x")
    prova("fake photo: strip read «%s»" % v.get("read"), v.get("read") == "abc")
    e, _ = judge_finding_again("abc", v, {"g": "x", "v": "abc"}, "x")
    prova("healthy finding again ⇒ PASS", e == S.PASS)
    v2 = G.look_scene(_Fake(fake_scene(None)), "x")
    e, _ = judge_finding_again("abc", v2, None, "x")
    prova("without window ⇒ FAIL", e == S.FAIL)
    v3 = {"window": None, "read": None, "photo": "", "why": "timed out", "png": None}
    e, _ = judge_finding_again("abc", v3, {"g": "x", "v": "abc"}, "x")
    prova("photo failed, good fields ⇒ BLOCKED", e == S.BLOCKED)
    prova("sentence «new» ⇒ no", not judge_sentence("Admitted, new session, canvas")[0])
    return 0 if ok else 1


def fake_scene(text, w=1920, h=1080):
    """A dark grey desktop with the scene's window (for --certify)."""
    import io
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), (40, 40, 60))
    d = ImageDraw.Draw(im)
    if text is not None:
        x0, y0, x1, y1 = 100, 120, 1300, 900
        d.rectangle([x0, y0, x1, y1], fill=G.CYAN)
        W, H = x1 - x0 + 1, y1 - y0 + 1
        step = (G.STR_X1 - G.STR_X0) / G.CELLS
        for i in range(G.CELLS):
            c = G.PALETTE[text[i]] if i < len(text) else G.EMPTY
            a = x0 + W * (G.STR_X0 + i * step)
            b = a + W * step - W * 0.014
            d.rectangle([a, y0 + H * G.STR_Y0, b, y0 + H * G.STR_Y1], fill=c)
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


class _Fake:
    """A fake Sessione that «photographs» a given png."""
    def __init__(self, png):
        self.png = png

    def photo(self, name):
        return self.png, ""


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def random_text(n):
    """DIFFERENT letters: a strip «bbbb» would say little about the order."""
    return "".join(random.sample(G.ALPHABET, n))


def find_scene(s, cap=30.0):
    fine = time.time() + cap
    v = {}
    while time.time() < fine:
        v = G.look_scene(s, "scene")
        if v.get("window"):
            return v
        time.sleep(2)
    return v


def one_round(o, E, s, text, passed, fault=False):
    """Detach → wait → reattach → state → input.  Puts F-016, F-017, P-A, P-F."""
    put = (lambda f, e, r, **k: E.fault(f, e == S.FAIL, "fault (scene killed): " + r, **k)) \
        if fault else (lambda f, e, r, **k: E.put(f, e, r, passed=passed, **k))
    q0 = G.notebook(s)
    token = next((r.get("g") for r in reversed(q0) if r.get("v") == text), None)
    before = G.processes(s)
    sign = s.log_mark()
    print("   before the detach: %s · token %s" % (before, token), flush=True)
    # ── DETACH: the browser closes (the driver navigates to about:blank ⇒ farewell, then exits)
    s.turn_off_browser()
    t_detach = time.time()
    if fault:
        c, t = s.sc.inside("pkill -KILL -u %s -x firefox-esr; sleep 1; pgrep -u %s -x "
                           "firefox-esr || echo uccisa" % (s.chi, s.chi), 30)
        print("   ⛔ FAULT: the scene killed during the detach: %s" % t.strip()[-80:], flush=True)
    time.sleep(max(0, WAIT_S - (time.time() - t_detach)))
    t_fine = time.time()
    time.sleep(3)                                 # at least one beat after the wait
    after = G.processes(s)
    q1 = G.notebook(s)
    reg = s.log_from(sign) if sign is not None else []
    ev = [s.save_text("server-%s-stacco.txt" % passed, reg)]
    e16, r16 = judge_detach(before, after, q1, int(t_fine * 1000), text, reg)
    put("F-016", e16, r16, expected="after %d s detached: same PIDs, session alive, the scene "
          "beats with its text" % WAIT_S,
          observed="before %s · after %s · %d notebook lines" % (before, after, len(q1)),
          evidence=ev)

    # ── REATTACH: a new browser, same user and password
    sign = s.log_mark()
    s.turn_on_browser()
    ok, m, refusals, sec = G.enter_with_retry(s, cap_s=40)
    reg = s.log_from(sign) if sign is not None else []
    ev = [s.save_text("server-%s-riattacco.txt" % passed, reg)]
    if not ok:
        for f in ("F-017", "P-A", "P-F"):
            put(f, S.FAIL, "the reattach does not get in in %.0f s: %s (refusals: %s)"
                  % (sec, m, refusals), evidence=ev)
        return
    ob = G.observe_canvas(s)
    sentence_ok, sentence = judge_sentence(ob.get("outcome"))
    v = G.wait_text(s, text, "riattacco-%s" % passed, cap=12)
    st = G.last_state(s)
    e17, r17 = judge_finding_again(text, v, st, token)
    e17_state = e17                  # the paths look at the STATE, not at the sentence
    if e17 == S.PASS and not sentence_ok and not fault:
        e17, r17 = S.FAIL, "state found again (%s) BUT %s" % (r17, sentence)
    ev17 = ev + [v.get("photo")]
    put("F-017", e17, r17, expected="admitted with «resumed session»; photo: window and "
          "strip «%s»; field: same token and value" % text,
          observed="%s · %s · back in after %.1f s (%d refusals) · state %s"
          % (sentence, v.get("raw"), sec, len(refusals), st), evidence=ev17)

    # ── INPUT AFTER THE REATTACH (P-A)
    add = random_text(2)
    if v.get("window"):
        cl = G.click_on_scene(s, v)
        G.write(s, add)
        v2 = G.wait_text(s, text + add, "input-dopo-%s" % passed, cap=10)
        in_ok = v2.get("read") == text + add
        r_in = "written «%s» after the reattach (%s): the photo reads «%s»" % (
            add, cl, v2.get("read"))
        ev_in = [v2.get("photo")]
    else:
        in_ok, r_in, ev_in = False, "no window to write on after the reattach", []
    ea = S.PASS if (e16 == S.PASS and e17_state == S.PASS and in_ok) else S.FAIL
    put("P-A", ea, "detach %s · state at reattach %s · input after: %s" % (e16, e17_state, r_in),
          expected="creation→desktop→input→detach→reattach→input, all seen",
          observed=r_in, evidence=ev17 + ev_in)
    ef = S.PASS if (e16 == S.PASS and e17_state == S.PASS) else S.FAIL
    put("P-F", ef, "application open, detach, %d s, reattach: F-016 %s · state %s"
          % (WAIT_S, e16, e17_state), expected="the application's state found again",
          observed="%s | %s" % (r16[:200], r17[:200]), evidence=ev17)
    return text + add if in_ok else None


def body(o, E):
    with S.Session(o, "016", E) as s:
        try:
            ok, m = s.enter()
            if not ok:
                raise S.Blocked("without login there is nothing to detach: " + m)
            ok, t = G.turn_on_scene(s)
            if not ok:
                raise S.Blocked("the scene does not start in the session: " + t[-200:])
            G.wake(s)
            v = find_scene(s)
            if not v.get("window"):
                raise S.Blocked("the scene's window is not seen in the photo: %s"
                                 % v.get("why"))
            text = random_text(4)
            v, note = G.write_base(s, v, text)
            if v.get("read") != text:
                raise S.Blocked("the PREPARATION input does not reach the scene (it is F-004/F-007, "
                                 "not this function): %s" % " | ".join(note))
            print("   written «%s» and read in the photo" % text, flush=True)
            fresh = one_round(o, E, s, text, "healthy")
            if o.fault:
                if s.g is None:
                    s.turn_on_browser()
                one_round(o, E, s, fresh or text, "fault", fault=True)
        finally:
            s.save_console() if s.g else None
            G.turn_off_server(s)


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify))
