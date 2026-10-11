#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f025 — F-025 THE SAME USER FROM TWO BROWSERS: the refusal, the ghost, the eviction

    python3 15-f025-stesso-utente-due-schede.py --box gnome --browser chrome --base-port 4900 [--fault]

Normal server of the box (85xx): no wrong password.  Two REAL browsers
of the same type, two profiles, two 4K windows (A on porte-base, B on
porte-base+50), the same tenant `c15025u<n>`.

THE REAL EXPECTATION, from the code (src/rcp.c `handle_attach`, `evict_ghost`,
`speak_again`, `DEFAULT_EVICTION` = 15 000 ms) and from SPECIFICHE §5.1:
  1  A is in and ALIVE (the pointer moves) ⇒ B, with RIGHT user and
     password, is REFUSED: B's page says «this session's slot shows
     as taken by another client…» (REASON_TEXT 0x0F ALREADY_ACTIVE_REMOTELY), the
     server writes «slot DENIED to <who>», and A stays in: its canvas still
     shows the scene (photo) and its page has not been sent away.
  2  A becomes a GHOST: its browser stops (SIGSTOP to the whole tree of
     processes — attached, but it no longer sends a packet).
     2a at once (A mute for ~2 s, below the threshold) ⇒ B still REFUSED with 0x0F;
     2b after 17 s of silence (beyond the 15 s of the eviction, before the 30 of
        silence) ⇒ B GETS IN: the page says «Admitted», the server writes
        «EVICTION for silence», and B FINDS A'S SESSION AGAIN: its canvas shows
        the scene of known colour that A had started (photo) — not a
        new desktop.
  3  A wakes up (SIGCONT) ⇒ there are NOT two clients attached: A's page
     says the farewell («taken by another client», 0x0F — «this time it is
     true») or at least is no longer in session; the server writes «speaks again
     after the silence, but their slot belongs to another client».

FAULTS (after the healthy pass, same session, with roles reversed: B is in):
  1  the premise «the other is alive» is FALSE: B says farewell (about:blank)
     before A knocks ⇒ A gets in ⇒ the judge of point 1 must say red.
  2  the ghost is not there: A is in, it is stopped and woken up at once, and
     its pointer keeps moving for 17 s ⇒ B knocks ⇒ the judge of
     point 2b («gets in after the silence») must say red.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._load("g8", os.path.join(S.HERE, "15-g8-comune.py"))
FUNCTIONS = ("F-025",)
CYAN = (0, 200, 200)
COLORS = {"scene": CYAN}
SCENE_THRESHOLD = 0.5
EVICTION_S = 15
AFTER_S = 17
WAKEUP_S = 60     # how long to wait for A, woken up, to know it is no longer in


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES — pure
# ═══════════════════════════════════════════════════════════════════════════
def judge_refused(admitted, outcome, lines, chi, page_a, fr_a):
    """Point 1 / 2a: B refused with the clear reason, A still in."""
    if admitted is True:
        return S.FAIL, "B GOT IN while A was alive (expected 0x0F): «%s»" % outcome
    if admitted is None:
        return S.BLOCKED, "no verdict in B's page: «%s»" % outcome
    if G.SENTENCE[0x0F] not in (outcome or ""):
        return S.FAIL, "B refused but not with reason 0x0F: «%s»" % outcome
    if not any("slot DENIED to %s" % chi in r for r in lines):
        return S.FAIL, "the page says 0x0F but the server does not write «slot DENIED»"
    if page_a is not None and (page_a.get("class") == "bad" or not page_a.get("session")):
        return S.FAIL, "B's refusal threw A out: «%s»" % page_a.get("outcome")
    if fr_a is not None and fr_a.get("scene", 0) < SCENE_THRESHOLD:
        return S.FAIL, "A is still in session but its canvas does not show the scene (%.1f%%)" % (
            100 * fr_a.get("scene", 0))
    return S.PASS, "B refused: «%s»; A stays in" % (outcome or "")[:70]


def judge_eviction(admitted, outcome, lines, chi, fr_b):
    """Point 2b: after the silence B gets in and finds A's session again."""
    if admitted is not True:
        return S.FAIL, "A has been silent for %d s and B does NOT get in: «%s»" % (AFTER_S, outcome)
    eviction = any("EVICTION for silence" in r for r in lines)
    released = any("slot LEFT" in r for r in lines)
    if not (eviction or released):
        return S.FAIL, ("B got in but the server does not say how the ghost's slot was "
                        "freed (neither «EVICTION for silence» nor «slot LEFT»)")
    come = ("EVICTION for silence" if eviction else
            "slot LEFT by the ghost earlier (the dead line closed its wire)")
    if fr_b is None:
        return S.BLOCKED, "B got in but its canvas cannot be photographed"
    if fr_b.get("scene", 0) < SCENE_THRESHOLD:
        return S.FAIL, ("B got in but does NOT find A's session again: the scene covers %.1f%% "
                        "of the canvas" % (100 * fr_b.get("scene", 0)))
    return S.PASS, "after %d s of A's silence, B gets in (%s) and finds the scene again (%.0f%%)" % (
        AFTER_S, come, 100 * fr_b["scene"])


def judge_wakeup(page_a, lines, chi):
    """Point 3: A woken up must NOT make the user believe it is still
    in: the page says a farewell (outcome «male») or puts the form back."""
    if page_a.get("error") or page_a.get("class") is None:
        return S.BLOCKED, "A's page cannot be read after the wake-up: %s" % (
            page_a.get("error") or page_a)
    if page_a.get("class") == "bad":
        return S.PASS, "A woken up: the page says «%s»" % (page_a.get("outcome") or "")[:90]
    if page_a.get("form"):
        return S.PASS, "A woken up: the page puts the sign-in form back"
    return S.FAIL, ("A woken up: its wire is already closed by the server, but the page still says "
                    "«%s» (session=%s, form hidden) — the user sees a frozen desktop and "
                    "no warning" % (page_a.get("outcome"), page_a.get("session")))


def certify():
    ok = True

    def prova(what, real):
        nonlocal ok
        ok &= bool(real)
        print("%s %s" % ("⭐" if real else "⛔", what))
    ch = "c15025u1"
    f0f = "this session's slot shows as " + G.SENTENCE[0x0F]
    neg = ["slot DENIED to %s from [192.168.0.2]:1" % ch]
    pa = {"class": "good", "session": True, "outcome": "Admitted"}
    prova("0x0F refusal, A in ⇒ PASS",
          judge_refused(False, f0f, neg, ch, pa, {"scene": 0.9})[0] == S.PASS)
    prova("B admitted ⇒ FAIL", judge_refused(True, "Admitted", [], ch, pa, None)[0] == S.FAIL)
    prova("different reason ⇒ FAIL",
          judge_refused(False, "user or password", neg, ch, pa, None)[0] == S.FAIL)
    prova("A thrown out ⇒ FAIL", judge_refused(
        False, f0f, neg, ch, {"class": "bad", "session": False, "outcome": "x"}, None)[0] == S.FAIL)
    prova("eviction with the scene ⇒ PASS", judge_eviction(
        True, "Admitted", ["⭐ EVICTION for silence: 17000 ms"], ch, {"scene": 0.8})[0] == S.PASS)
    prova("eviction without the scene ⇒ FAIL", judge_eviction(
        True, "Admitted", ["⭐ EVICTION for silence"], ch, {"scene": 0.0})[0] == S.FAIL)
    prova("no eviction ⇒ FAIL", judge_eviction(False, f0f, [], ch, None)[0] == S.FAIL)
    prova("wake-up in session ⇒ FAIL",
          judge_wakeup({"class": "good", "session": True, "form": False}, [], ch)[0] == S.FAIL)
    prova("wake-up with the form ⇒ PASS",
          judge_wakeup({"class": "good", "session": False, "form": True}, [], ch)[0] == S.PASS)
    prova("wake-up sent away ⇒ PASS",
          judge_wakeup({"class": "bad", "session": False, "outcome": f0f}, [], ch)[0] == S.PASS)
    from PIL import Image
    import io
    im = Image.new("RGB", (40, 20), (20, 20, 20))
    im.paste(CYAN, (0, 0, 30, 20))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    fr = G.fractions(buf.getvalue(), COLORS, reduce=1)
    prova("fractions: 75%% cyan (%s)" % G.fr_text(fr), fr and abs(fr["scene"] - 0.75) < 0.01)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def wait_page(g, cap=25):
    fine = time.time() + cap
    p = {}
    while time.time() < fine:
        p = G.read_page(g)
        if p.get("class") == "bad":
            return p
        time.sleep(1)
    return p


def body(o, E):
    sc = None
    with S.Session(o, "025", E) as A:
        chi = A.chi
        sc = A.sc
        ok, m = A.enter()
        if not ok:
            raise S.Blocked("A does not get in: " + m)
        print("   ⭐ A in: %s" % m[:90], flush=True)
        S.C21.wake(A.g, A.geometry())
        ok, t = G.turn_on_scene(sc, chi, o.base_port + G.MOVE_SCENE, CYAN)
        if not ok:
            raise S.Blocked("the colour scene does not start: %s" % " | ".join(t.splitlines()[-14:])[-900:])
        fr_a, photo_a, why = G.wait_color(A, "A-scena", COLORS, "scene", SCENE_THRESHOLD)
        if not fr_a or fr_a["scene"] < SCENE_THRESHOLD:
            raise S.Blocked("the scene does not cover A's canvas: %s %s" % (G.fr_text(fr_a), why))
        print("   scene in A: %s" % G.fr_text(fr_a), flush=True)

        with S.Session(G.o_per(o, 1), "025", E, tenant=False, chi=chi,
                        password=A.password) as B:
            ev = [photo_a]
            # ── 1: A alive ⇒ B refused ──────────────────────────────────────
            sign = A.log_mark()
            G.nudge(A)
            adm, st, env = G.try_hard(B, chi, B.password)
            lines = A.log_from(sign)
            pa = G.read_page(A.g)
            fr, dove, _ = G.wait_color(A, "A-dopo-rifiuto", COLORS, "scene", SCENE_THRESHOLD, 6)
            ev.append(dove)
            e1, r1 = judge_refused(adm, st.get("outcome"), lines, chi, pa, fr)
            if env:
                r1 += " (retried after %s)" % env
            print("   1 (A alive): %s — %s" % (e1, r1), flush=True)

            # ── 2: the ghost ────────────────────────────────────────────────
            G.nudge(A)
            sign_f = A.log_mark()
            n = G.halt(A.g)
            t0 = time.time()
            print("   A STOPPED (%d processes)" % n, flush=True)
            e2a = e2b = e3 = S.BLOCKED
            r2a = r2b = r3 = "not looked at"
            try:
                sign = A.log_mark()
                time.sleep(1.5)
                adm, st, env = G.try_hard(B, chi, B.password)
                mute = time.time() - t0
                lines = A.log_from(sign)
                e2a, r2a = judge_refused(adm, st.get("outcome"), lines, chi, None, None)
                r2a = "(A mute for %.1f s) %s" % (mute, r2a)
                if mute >= EVICTION_S - 2:
                    e2a, r2a = S.BLOCKED, "attempt 2a arrived late (%.1f s)" % mute
                print("   2a: %s — %s" % (e2a, r2a), flush=True)
                time.sleep(max(0.0, t0 + AFTER_S - time.time()))
                adm, st, env = G.try_hard(B, chi, B.password)
                mute = time.time() - t0
                fr_b = None
                if adm:
                    e, m2, s2 = B.pr.first_frame()
                    fr_b, dove, _ = G.wait_color(B, "B-dopo-sfratto", COLORS, "scene",
                                                     SCENE_THRESHOLD, 20)
                    ev.append(dove)
                lines = A.log_from(sign_f)
                e2b, r2b = judge_eviction(adm, st.get("outcome"), lines, chi, fr_b)
                r2b = "(A mute for %.1f s) %s · B's page says «%s»%s" % (
                    mute, r2b, (st.get("outcome") or "")[:60],
                    " (retried after %s)" % env if env else "")
                print("   2b: %s — %s" % (e2b, r2b), flush=True)
            finally:
                G.resume(A.g)
            # ── 3: the wake-up ──────────────────────────────────────────────
            t_sv = time.time()
            G.nudge(A)
            pa = wait_page(A.g, WAKEUP_S)
            after_sv = time.time() - t_sv
            lines = A.log_from(sign_f)
            e3, r3 = judge_wakeup(pa, lines, chi)
            reg_a = [x for x in (A.state().get("log") or "").splitlines() if x.strip()][-6:]
            said = [r for r in lines if "speaks again after the silence" in r]
            r3 += " · server: %s" % ("«speaks again… their slot belongs to another»" if said
                                     else "(no «speaks again» line)")
            r3 += " · dead line on A's wire: %s · A's page diary: %s" % (
                "YES" if any("DEAD LINE" in r or "dead-line" in r for r in lines) else "no",
                " | ".join(reg_a)[-300:])
            r3 = "(after %.0f s) %s" % (after_sv, r3)
            print("   3: %s — %s" % (e3, r3), flush=True)

            all_items = [e1, e2a, e2b, e3]
            outcome = S.FAIL if S.FAIL in all_items else (S.BLOCKED if S.BLOCKED in all_items else S.PASS)
            ev.append(A.save_text("f025-server.txt", lines))
            E.put("F-025", outcome, "1 %s · 2a %s · 2b %s · 3 %s" % (e1, e2a, e2b, e3),
                    expected="A alive ⇒ B refused with 0x0F and A stays; A mute >15 s ⇒ B gets in "
                           "(eviction) and finds the scene again; A woken up sent away",
                    observed="1: %s | 2a: %s | 2b: %s | 3: %s" % (r1, r2a, r2b, r3),
                    evidence=[x for x in ev if x])

            if o.fault:
                gv = []
                # 1: B (in) says farewell before A knocks
                B.g.navigate("about:blank")
                time.sleep(3)
                sign = A.log_mark()
                adm, st, env = G.try_hard(A, chi, A.password)
                lines = A.log_from(sign)
                eg1, rg1 = judge_refused(adm, st.get("outcome"), lines, chi, None, None)
                gv.append(eg1 == S.FAIL if adm is not None else None)
                print("   fault 1 (the other is NOT alive): the judge says %s — %s" % (eg1, rg1),
                      flush=True)
                # 2: no ghost: A stopped and woken up at once, and alive
                eg2, rg2 = S.BLOCKED, "A did not get back in"
                if adm:
                    A.pr.first_frame()
                    n = G.halt(A.g)
                    G.resume(A.g)
                    t0 = time.time()
                    B.pr.do_open()
                    while time.time() < t0 + AFTER_S:
                        G.nudge(A, 2)
                        time.sleep(1.5)
                    sign = A.log_mark()
                    admitted2, st2, env = G.try_hard(B, chi, B.password)
                    lines = A.log_from(sign)
                    eg2, rg2 = judge_eviction(admitted2, st2.get("outcome"), lines, chi, None)
                    gv.append(eg2 == S.FAIL if admitted2 is not None else None)
                else:
                    gv.append(None)
                print("   fault 2 (A alive, no ghost): the judge says %s — %s" % (eg2, rg2),
                      flush=True)
                seen = None if None in gv else all(gv)
                E.fault("F-025", seen, "the other sent away ⇒ %s (%s) · A alive for %d s ⇒ %s (%s)"
                         % (eg1, rg1[:80], AFTER_S, eg2, rg2[:80]))


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify))
