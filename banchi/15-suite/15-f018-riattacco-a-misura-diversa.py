#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f018 — F-018 REATTACH AT A DIFFERENT SIZE · path P-C

    python3 15-f018-riattacco-a-misura-diversa.py --container_box xfce --browser firefox [--fault]

  P-C  creation at 4K (browser window 3840x2160) → application open and
       text written → DETACH → reattach with the window at 2560x1440 → DETACH
       → reattach BACK at 4K.  At every reattach: the canvas, the desktop, the
       state.  (Live resolution change does not exist: the size changes ONLY
       by reattaching — `DECISIONI.md` §5.1-bis.)

F-018  expected (`SPECIFICHE.md` §6.1-§6.3, `src/rcp.c` ~2998, `src/figlio.c`
       `stage_size`):
   GNOME, XFCE, LXQt — the CANVAS takes the new size and the DESKTOP follows it:
       · field: the page's canvas (`#display_screen` width×height) is that of the
         new view (± 16 px: the page truncates it to multiples of 16);
       · field: inside the session a program sees the SCREEN of that
         size (screen.width×height of firefox-esr in the session = the
         compositor's output);
       · photo: the scene's window is there and the text can be read; the edges of the
         photo (the rows at the top and bottom, where the panels are) are the ones
         from before; no new BLACK band on the right or at the bottom (full background).
   ⭐ KDE — EXCEPTION DECLARED by the user (KWin < 6.8, SPECIFICHE ~851,
       §6.3): the canvas STAYS the previous one and the browser RESCALES:
       · field: canvas equal to before; the canvas rectangle in the browser is
         inside the new view and fills one side of it (≥ 90 %);
       · field: the screen seen from inside is the one from before;
       · photo: as above (window, text, edges).
       ⇒ on KDE THIS is the PASS.
P-C    expected: the two reattaches (at 2560x1440 and back at 4K) both right.

FAULT: the judge receives the reattach BACK (size equal to the starting
       one) as if it were at 2560x1440 — «the reattach at the same size
       judged as if it had changed» — and then the reattach at 2560x1440 with
       the expectation of the OTHER family (KDE judged as GNOME and vice versa).
       Both must give RED, on real observations.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._load("g6", os.path.join(S.HERE, "15-g6-comune.py"))
F16 = S._load("f016", os.path.join(S.HERE, "15-f016-stacco-e-riattacco.py"))
FUNCTIONS = ("F-018", "P-C")
NEW_SIZE = (2560, 1440)
TOL_CANVAS = 16            # the page truncates the canvas to multiples of 16 (fc0fbff)
TOL_EDGE = 40           # mean colour of the edge rows
FILLS = 0.90            # on KDE the rescaled canvas fills at least one side


def family(desktop):
    return "kde" if desktop == "kde" else "follows"


# the side of the panel that runs along the WHOLE width (seen in the photos of 24-25 Sep)
PANEL = {"gnome": "alto", "kde": "low", "xfce": "alto", "lxqt": "low"}


def compare_panel(bp, bd, side):
    """Maximum distance between the slices of the panel side, before and after, outside
    the slices covered by the window in either photo.  (d, how many)."""
    fp, fd = bp.get(side + "_f"), bd.get(side + "_f")
    if not fp or not fd:
        return G.distance(bp[side], bd[side]), 1
    via = set(bp.get("covered") or []) | set(bd.get("covered") or [])
    ks = [k for k in range(len(fp)) if k not in via]
    if not ks:
        return None, 0
    # the MEDIAN of the slices: the panel's icons and clock sit at fixed
    # pixels and change slice when the width changes; the missing panel
    # changes ALL the slices
    d = sorted(G.distance(fp[k], fd[k]) for k in ks)
    return d[len(d) // 2], len(ks)


def judge_measure(fam, before, after, view_wait, body_text, panel="alto"):
    """⭐ F-018 for one reattach.  before/after: the observations (see `observe`).
    `view_wait` [w, h]: the view the browser draws in now.
    Returns (outcome, reason)."""
    probs, all_ok = [], []
    b0, b1 = before.get("buffer"), after.get("buffer")
    if not b0 or not b1:
        return S.BLOCKED, "the page's canvas cannot be read (before %s, after %s)" % (b0, b1)
    vl, va = view_wait[0], view_wait[1]
    scr = after.get("display_screen")
    if fam == "follows":
        # ⚠ the view is in CSS pixels; the canvas in DEVICE pixels (the page:
        #   `view_size()` = view × devicePixelRatio, truncated).  On the computer dpr 1 and
        #   the two coincide; on the phone (phase 19 §5, dpr 3.375) not.
        k = after.get("dpr") or 1
        tl, ta = int(vl * k), int(va * k)
        stated = "%dx%d" % (vl, va) if k == 1 else "%dx%d (%dx%d CSS × dpr %g)" % (tl, ta, vl, va, k)
        if abs(b1[0] - tl) > TOL_CANVAS or abs(b1[1] - ta) > TOL_CANVAS:
            probs.append("the canvas is %dx%d, the view %s: the canvas did NOT take the size "
                         "of the window" % (b1[0], b1[1], stated))
        else:
            all_ok.append("canvas %dx%d for the view %s" % (b1[0], b1[1], stated))
        if not scr:
            probs.append("the screen seen from inside the session cannot be read")
        elif abs(scr[0] - b1[0]) > 2 or abs(scr[1] - b1[1]) > 2:
            probs.append("inside the session the screen is %dx%d, the canvas %dx%d: the desktop "
                         "did NOT follow" % (scr[0], scr[1], b1[0], b1[1]))
        else:
            all_ok.append("inside, the screen is %dx%d" % tuple(scr))
    else:
        if list(b1) != list(b0):
            probs.append("on KDE the canvas had to stay %dx%d (KWin < 6.8), it is %dx%d"
                         % (b0[0], b0[1], b1[0], b1[1]))
        else:
            all_ok.append("canvas kept %dx%d (KWin < 6.8, declared exception)" % tuple(b1))
        r = after.get("tela_rett") or [0, 0, 0, 0]
        if r[2] > vl + 1 or r[3] > va + 1:
            probs.append("the canvas in the browser is %dx%d, larger than the view %dx%d: the "
                         "browser does NOT rescale" % (r[2], r[3], vl, va))
        elif max(r[2] / max(1, vl), r[3] / max(1, va)) < FILLS:
            probs.append("the canvas in the browser is %dx%d in the view %dx%d: it does not fill it"
                         % (r[2], r[3], vl, va))
        else:
            all_ok.append("rescaled to %dx%d in the view %dx%d" % (r[2], r[3], vl, va))
        s0 = before.get("display_screen")
        if scr and s0 and list(scr) != list(s0):
            probs.append("on KDE the screen inside had to stay %s, it is %s" % (s0, scr))
    # the photo: window, text, edges
    if after.get("blind"):
        if probs:
            return S.FAIL, "; ".join(probs) + " (and the photo could not be taken)"
        return S.BLOCKED, ("the fields add up (%s) but the photo could not be taken: %s"
                           % (" · ".join(all_ok), after.get("reason_text")))
    if not after.get("win"):
        probs.append("in the photo the scene's window is not there (%s)" % after.get("reason_text"))
    elif after.get("read") != body_text:
        probs.append("in the photo the strip says «%s», written «%s»" % (after.get("read"), body_text))
    else:
        all_ok.append("window and text «%s» in the photo" % body_text)
    bp, bd = before.get("borders"), after.get("borders")
    if bp and bd:
        d, n = compare_panel(bp, bd, panel)
        if d is None:
            probs.append("the panel edge (%s) is entirely covered by the window" % panel)
        elif d > TOL_EDGE:
            probs.append("the panel edge (%s) changed (median deviation %d over %d free "
                         "slices): the panel is not at the new edge" % (panel, d, n))
        else:
            all_ok.append("panel at the %s edge (%d slices, deviation %d)" % (panel, n, d))
        for side in ("black_right", "nero_basso"):
            if bd[side] > bp[side] + 0.5:
                probs.append("a new BLACK band (%s %.0f %%, before %.0f %%): the background is not "
                             "full" % (side, 100 * bd[side], 100 * bp[side]))
    else:
        probs.append("the edges of the photo cannot be read")
    if probs:
        return S.FAIL, "; ".join(probs)
    return S.PASS, " · ".join(all_ok)


# ═══════════════════════════════════════════════════════════════════════════
def _oss(buffer, vista, rect, display_screen, borders, win=True, read="abc"):
    return {"buffer": buffer, "vista": vista, "tela_rett": rect, "display_screen": display_screen,
            "borders": borders, "win": [0, 0, 1, 1] if win else None, "read": read}


def certify():
    ok = True

    def prova(what, real):
        nonlocal ok
        ok &= bool(real)
        print("%s %s" % ("⭐" if real else "⛔", what))
    bo = {"alto": [0, 0, 0], "low": [30, 30, 40], "black_right": 0.0, "nero_basso": 0.0}
    A = _oss([3776, 2016], [3788, 2023, 1], [0, 0, 3776, 2016], [3776, 2016], bo)
    B = _oss([2544, 1344], [2548, 1350, 1], [0, 0, 2544, 1344], [2544, 1344], bo)
    C = _oss([3776, 2016], [3788, 2023, 1], [0, 0, 3776, 2016], [3776, 2016], bo)
    e, m = judge_measure("follows", A, B, B["vista"], "abc")
    prova("gnome: new canvas and screen ⇒ PASS (%s)" % m[:50], e == S.PASS)
    e, _ = judge_measure("follows", A, C, B["vista"], "abc")
    prova("fault: same size judged as changed ⇒ FAIL", e == S.FAIL)
    Bs = dict(B, display_screen=[3776, 2016])
    e, _ = judge_measure("follows", A, Bs, B["vista"], "abc")
    prova("new canvas but desktop still ⇒ FAIL", e == S.FAIL)
    Bn = dict(B, borders=dict(bo, black_right=0.9))
    e, _ = judge_measure("follows", A, Bn, B["vista"], "abc")
    prova("new black band ⇒ FAIL", e == S.FAIL)
    K = _oss([3776, 2016], [2548, 1350, 1], [0, 3, 2548, 1360], [3776, 2016], bo)
    K["tela_rett"] = [0, 0, 2528, 1350]
    e, m = judge_measure("kde", A, K, K["vista"], "abc")
    prova("kde: canvas kept and rescaled ⇒ PASS (%s)" % m[:50], e == S.PASS)
    e, _ = judge_measure("follows", A, K, K["vista"], "abc")
    prova("fault: kde judged as gnome ⇒ FAIL", e == S.FAIL)
    e, _ = judge_measure("kde", A, B, B["vista"], "abc")
    prova("fault: gnome judged as kde ⇒ FAIL", e == S.FAIL)
    e, _ = judge_measure("kde", A, C, B["vista"], "abc")
    prova("kde fault: same size as changed ⇒ FAIL", e == S.FAIL)
    e, _ = judge_measure("follows", A, dict(B, read="ab"), B["vista"], "abc")
    prova("text lost ⇒ FAIL", e == S.FAIL)
    e, _ = judge_measure("follows", A, dict(B, blind=True, win=None), B["vista"], "abc")
    prova("photo failed, good fields ⇒ BLOCKED", e == S.BLOCKED)
    e, _ = judge_measure("follows", A, dict(C, blind=True), B["vista"], "abc")
    prova("photo failed, wrong fields ⇒ FAIL", e == S.FAIL)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def observe(s, body_text, label_name, wanted_screen=None):
    """Canvas (fields), screen from inside (field), photo (window, text, edges)."""
    ob = G.wait_canvas_still(s)
    try:
        ob["dpr"] = float(s.g.js("return window.devicePixelRatio || 1;") or 1)
    except Exception:                            # noqa: BLE001
        ob["dpr"] = 1
    v = G.wait_text(s, body_text, label_name, ceiling=12)
    # the screen seen from inside: the last fresh line; if we are waiting for a size,
    # it is given a few seconds (the desktop follows after the canvas)
    scr = None
    fine = time.time() + 12
    while True:
        st = G.last_state(s)
        if st:
            scr = [st.get("sw"), st.get("sh")]
        if wanted_screen is None or (scr and abs(scr[0] - wanted_screen[0]) <= 2
                                      and abs(scr[1] - wanted_screen[1]) <= 2) \
                or time.time() > fine:
            break
        time.sleep(1.5)
    ob.update({"display_screen": scr, "win": v.get("win"), "read": v.get("read"),
               "reason_text": v.get("reason_text"), "picture": v.get("picture"), "blind": v.get("png") is None})
    ob["borders"] = G.borders(G.bitmap(v["png"]), v.get("win")) if v.get("png") else None
    return ob


def brief(ob):
    return ("canvas %s · view %s · rect %s · screen inside %s · read «%s» · edges %s"
            % (ob.get("buffer"), (ob.get("vista") or [None])[:2],
               [round(x) for x in (ob.get("tela_rett") or [])], ob.get("display_screen"),
               ob.get("read"), {k: v for k, v in (ob.get("borders") or {}).items()
                                  if not k.endswith("_f")}))


def reattach(s, largo, alto, body_text, label_name, fam):
    """Detach (browser closed) and reattach with the window at largo x alto."""
    s.turn_off_browser()
    time.sleep(2)
    mis = G.turn_on_at_size(s, largo, alto)
    print("   browser restarted at %dx%d: view %s" % (largo, alto, mis), flush=True)
    ok, m, refusals, sec = G.enter_with_retry(s, cap_s=40)
    if not ok:
        return None, "the reattach at %dx%d does not get in: %s" % (largo, alto, m)
    G.wake(s)
    ob0 = G.observe_canvas(s)
    ob = observe(s, body_text, label_name, wanted_screen=None)
    if fam == "follows" and ob.get("buffer") and ob.get("display_screen") != ob.get("buffer"):
        ob = observe(s, body_text, label_name + "-bis", wanted_screen=ob.get("buffer"))
    ob["outcome"] = ob0.get("outcome")
    print("   %s: %s" % (label_name, brief(ob)), flush=True)
    return ob, ""


def body_el(o, E):
    fam = family(o.container_box)
    with S.Session(o, "018", E) as s:
        try:
            ok, m = s.enter()
            if not ok:
                raise S.Blocked("without login there is nothing to reattach: " + m)
            ok, t = G.turn_on_scene(s)
            if not ok:
                raise S.Blocked("the scene does not start in the session: " + t[-200:])
            G.wake(s)
            v = F16.find_scene(s)
            if not v.get("win"):
                raise S.Blocked("the scene's window is not seen in the photo: %s"
                                 % v.get("reason_text"))
            body_text = F16.random_text(4)
            v, note = G.write_base(s, v, body_text)
            if v.get("read") != body_text:
                raise S.Blocked("the PREPARATION input does not reach the scene (it is F-004/F-007, "
                                 "not this function): %s" % " | ".join(note))
            A = observe(s, body_text, "A-4k")
            print("   A (creation): %s" % brief(A), flush=True)
            if not A.get("buffer"):
                raise S.Blocked("the starting canvas cannot be read")

            B, reason_text = reattach(s, NEW_SIZE[0], NEW_SIZE[1], body_text, "B-2560", fam)
            if B is None:
                E.put("F-018", S.FAIL, reason_text)
                E.put("P-C", S.FAIL, reason_text)
                raise S.Blocked("the reattach at a different size did not get in")
            if abs(B["vista"][0] - A["buffer"][0]) < 64:
                raise S.Blocked("the browser did not change size (view %s, previous canvas %s):"
                                 " the reattach is not «at a different size»" % (B["vista"], A["buffer"]))
            pan = PANEL[o.container_box]
            eB, rB = judge_measure(fam, A, B, B["vista"][:2], body_text, pan)
            ev = [x for x in (A.get("picture"), B.get("picture")) if x]
            E.put("F-018", eB, rB,
                    expected_val=("canvas and desktop at the new size" if fam == "follows" else
                            "⭐ KDE: previous canvas, rescaled by the browser (declared exception)"),
                    observed="A: %s || B: %s" % (brief(A), brief(B)), evidence=ev)

            C, reason_text = reattach(s, 3840, 2160, body_text, "C-4k", fam)
            if C is None:
                E.put("P-C", S.FAIL, "at 2560x1440 %s; " % eB + reason_text)
                return
            eC, rC = judge_measure(fam, B, C, C["vista"][:2], body_text, pan)
            eP = S.PASS if (eB == S.PASS and eC == S.PASS) else S.FAIL
            E.put("P-C", eP, "at 2560x1440: %s · back at 4K: %s — %s"
                    % (eB, eC, rC if eC != S.PASS else rC[:200]),
                    expected_val="creation → reattach at a different size → reattach back, "
                           "each time like its family (%s)" % fam,
                    observed="B: %s || C: %s" % (brief(B), brief(C)),
                    evidence=ev + [C.get("picture")])

            if o.fault:
                # 1. the same size (C = A) judged as if it had changed to B
                g1, r1 = judge_measure(fam, A, C, B["vista"][:2], body_text, pan)
                # 2. the reattach at 2560x1440 with the other family's expectation
                the_other = "follows" if fam == "kde" else "kde"
                g2, r2 = judge_measure(the_other, A, B, B["vista"][:2], body_text, pan)
                seen_v = g1 == S.FAIL and g2 == S.FAIL
                E.fault("F-018", seen_v, "same size as changed ⇒ %s (%s) · expectation "
                         "«%s» on %s ⇒ %s (%s)" % (g1, r1[:140], the_other, o.container_box, g2, r2[:140]))
                E.fault("P-C", g1 == S.FAIL, "the path with the wrong expectation on the way back "
                         "⇒ %s" % g1)
        finally:
            if s.g:
                s.save_console()
            G.turn_off_server(s)


if __name__ == "__main__":
    sys.exit(S.execute(__doc__, FUNCTIONS, body_el, certify))
