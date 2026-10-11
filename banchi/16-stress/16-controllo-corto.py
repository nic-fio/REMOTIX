#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
16-controllo-corto — THE SHORT FUNCTIONAL CHECK OF A LEVEL (phase 16, §7)
===========================================================================

    (on the server, as nicfio, in the environment of 15-una.sh: WAYLAND_DISPLAY of
     ITS OWN compositor — 16-compositori.sh u00 — and REMOTIX_ON_SERVER=1)
    python3 16-controllo-corto.py --box lxqt --level 4 \\
        --dir /media/REMOTIX/misure/fase16/<campagna>/level-04 \\
        --browser chrome --base-port 9900 [--width 3840 --height 2160]

WHAT IT DOES — a NEW SESSION, its own, inside the loaded level:
  tenant `c16<livello>u99` (born here, cleared out on exit), a real
  browser (the one asked for: the climb alternates them between levels), and in a row, like
  a user who arrives:
    birth    access → first frame, timed (§7 «birth of a
             new user», §9: ≤ 5 s GREEN, 5–15 DEGRADED, > 15 or refusal FAIL)
    F-004    the mouse, REDUCED: movement, left click, drag
             (the scene of 15-g2-scena.py, the judges of 15-f004)
    F-007    the special keys: the sequence of 15-f007 (Enter, Backspace,
             arrows, Tab, Esc) in the same scene
    F-003    the image, REDUCED: the test window OPENS and its
             counter CHANGES (photos no older than 1 s for 6 s) — the
             judges of 15-f003; no drag and no judged closing
    F-014    the clipboard browser → session: the scene and the judge of 15-f014
  ⇒ writes DIR/short-check.json and the evidence in DIR/short-check/.

  --fault  (the test of the check, §13.2; NOT in the climb) after the healthy
            pass, in the same session, every judge receives FALSE evidence
            and must give red: F-004 gestures into nothing · F-007 the sequence without
            Esc · F-003 the photo from BEFORE (opening and counter) · F-014 copy
            not done + expected without accents.  In controllo-corto.json:
            «guasti» and «esito_guasto» (PASS = all seen); «esiti» stays the
            healthy pass only.

⭐ WHY A SESSION OF ITS OWN, and not an actor's (proposal, fasi/16 §7):
  - every actor has ITS OWN browser (Marionette/CDP on a single port): getting into it
    from outside would mean two masters on the same browser, and the gesture of one
    would spoil the work of the other — the level's measurement would get dirty;
  - the phase 15 tests are written for a `suite.Sessione`: with a
    session of its own they are REUSED as they are (scenes, judges, retries), without
    rewriting them against the work of an actor who meanwhile clicks elsewhere;
  - it is also the measurement that §7 asks for separately: the BIRTH of a new user
    with the server already loaded with N users;
  - the price: for a few minutes the level has N+1 sessions.  It is declared
    (`sessioni_durante`), and it is within the cap (16) up to step 15.
    ⚠ At step 16 the check is the 17th: the climb raises the cap to 17
    for the campaign's box (16-salita.py --cap), and says so.

Exit code: 0 all PASS · 1 at least one FAIL · 3 at least one BLOCKED and
no FAIL.  One `SUITE {...}` line per function, like the suite.
"""
import datetime
import json
import os
import re
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE = os.path.join(os.path.dirname(HERE), "15-suite")
sys.path.insert(0, SUITE)
import suite as S                                                     # noqa: E402

# ⭐ the phase 15 tests, IMPORTED (not copied)
F003 = S._load("f003", os.path.join(SUITE, "15-f003-lo-schermo-si-aggiorna.py"))
F004 = S._load("f004", os.path.join(SUITE, "15-f004-il-mouse.py"))
F007 = S._load("f007", os.path.join(SUITE, "15-f007-tasti-speciali.py"))
F014 = S._load("f014", os.path.join(SUITE, "15-f014-appunti.py"))
G2 = F004.G2
C21 = S.C21

# ⛔ the phase 16 tenants are called c16<nnn>u<n>: the suite accepts only
#   its own (c15…).  The network clear-out (`^c[0-9]+b?u[0-9]+$`) recognises them.
S.TENANT_PATTERN = re.compile(r"^c1[56][0-9]{3}u[0-9]+$")

FUNCTIONS = ("F-004", "F-007", "F-003", "F-014")
REDUCED_GESTURES = ("movimento", "clic-sinistro", "trascinamento")
CONTROL_USER = 99
CAP_BIRTH_S = 90            # beyond: FAIL «no first frame» (§9: > 15 s is already FAIL)


def t_now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def extra(a):
    a.add_argument("--dir", required=True, help="the level folder (level-NN)")
    a.add_argument("--level", type=int, required=True)
    a.add_argument("--user", type=int, default=CONTROL_USER,
                   help="the number of the tenant c16<livello>u<utente> (99)")
    a.add_argument("--only", default="", help="only these functions (F-004,F-003…): tests of the bench")


# ═══════════════════════════════════════════════════════════════════════════
#  THE BIRTH, timed
# ═══════════════════════════════════════════════════════════════════════════
def bring_up(s, o):
    """Page → form → admission → first frame, with the times.
    Returns (ok, reason, times)."""
    t = {}
    t0 = time.time()
    ok, m = s.pr.do_open()
    t["page_s"] = round(time.time() - t0, 2)
    if not ok:
        return False, "the page does not open: " + m, t
    t1 = time.time()
    e, m, _st = s.pr.enter(s.password)
    t["admission_s"] = round(time.time() - t1, 2)
    if e != S.GREEN:
        t["refusal"] = bool(s.pr.refusal)
        return False, "the access: " + m, t
    # ⭐ access → first PAINTED frame: the page's counter, read
    #   closely; then the (non-degenerate) photograph is taken by `first_frame`.
    fine = t1 + CAP_BIRTH_S
    while time.time() < fine:
        st = s.pr.state() or {}
        if (st.get("painted") or 0) > 0:
            t["birth_s"] = round(time.time() - t1, 2)
            break
        time.sleep(0.2)
    if "birth_s" not in t:
        return False, "no painted frame %d s after the access" % CAP_BIRTH_S, t
    e, m, st = s.pr.first_frame()
    e, m = S.C20V.desktop_dark_but_alive(e, m, st)
    t["first_non_degenerate_s"] = round(time.time() - t1, 2)
    if e != S.GREEN:
        return False, "the first frame: " + m, t
    return True, m, t


def wait_canvas(s):
    """The canvas of the wanted size (the rule of F-011), as in 15-f003."""
    cw, ch, dpr = s.g.js("const d=document.documentElement; "
                         "return [d.clientWidth, d.clientHeight, devicePixelRatio||1];")
    wait = F003.F011.canvas_wait(cw, ch, dpr)
    fine = time.time() + 40
    geo = None
    while time.time() < fine:
        geo = s.geometry()
        if geo and [geo.get("tl"), geo.get("ta")] == wait:
            return geo, ""
        time.sleep(1)
    if not geo:
        return None, "`REMOTIX_PUNTATORE.geometry` is not there"
    return None, "the canvas is %sx%s and not %dx%d after 40 s" % (geo.get("tl"), geo.get("ta"),
                                                           wait[0], wait[1])


def via_le_scene(s):
    """The session's test applications go away (the scene of G2, the
    window of F-003): the next function starts from a clean desktop."""
    s.sc.inside("pkill -KILL -u %s -f '[f]irefox-esr' 2>/dev/null; "
                "pkill -KILL -u %s -f '[g]2-servitore' 2>/dev/null; sleep 1; true"
                % (s.chi, s.chi), 30)


# ═══════════════════════════════════════════════════════════════════════════
#  THE FOUR FUNCTIONS, reduced — the judges are those of phase 15
# ═══════════════════════════════════════════════════════════════════════════
def f004_f007(o, E, s, t_birth):
    """The scene of G2 only once, then the reduced gestures and the keys."""
    ok_n, m_n = True, "already entered"
    real_enter = s.enter
    s.enter = lambda *a, **k: (ok_n, m_n)          # G2.prepare does not re-enter: we are inside
    try:
        sc, mp, _geo, dove = G2.prepare(s, o.base_port + 5)
    finally:
        s.enter = real_enter
    ev0 = [dove] if dove else []
    if "F-004" in o.functions:
        F004.GESTURES = REDUCED_GESTURES
        lines = F004.passed(s, sc, mp, False)
        es = [r[1] for r in lines]
        oss = " · ".join("%s: %s %s" % (n, e, m) for n, e, m, _ in lines)
        ev = ev0 + [x for r in lines for x in r[3]]
        expected = "movement on the BLUE block where it points, click on the GREEN counted, box moved"
        if S.FAIL in es:
            E.put("F-004", S.FAIL, "red gestures: " + ", ".join(
                n for n, e, _m, _ in lines if e == S.FAIL), expected=expected, observed=oss,
                evidence=ev + [s.save_console()])
        elif S.BLOCKED in es:
            E.put("F-004", S.BLOCKED, "gestures not looked at: " + ", ".join(
                "%s (%s)" % (n, m) for n, e, m, _ in lines if e == S.BLOCKED),
                expected=expected, observed=oss, evidence=ev)
        else:
            E.put("F-004", S.PASS, "%d gestures of %d (reduced): the effect is there "
                    "in the application" % (len(lines), len(lines)), expected=expected,
                    observed=oss, evidence=ev)
        if o.fault:
            # ⭐ the fault of 15-f004: every gesture INTO NOTHING, same judge ⇒ all red
            lines = F004.passed(s, sc, mp, True)
            seen = F004.outcome_with_fault([r[1] for r in lines])
            E.fault("F-004", seen, {True: "every gesture into nothing gave red",
                                      False: "gestures into nothing GREEN anyway: " + ", ".join(
                                          n for n, e, _m, _ in lines if e == S.PASS),
                                      None: "a gesture into nothing could not be looked at"}[seen],
                     observed=" · ".join("%s: %s %s" % (n, e, m) for n, e, m, _ in lines))
    if "F-007" in o.functions:
        st, photo, why = F007.beat(s, sc, mp, F007.SEQUENCE, "keys")
        if why:
            E.put("F-007", S.BLOCKED, why)
        else:
            e, m = F007.judge(st, F007.ATTESO)
            if e == S.FAIL:
                print("   ⚠ red (%s): doing it again to confirm it" % m, flush=True)
                st2, photo2, why2 = F007.beat(s, sc, mp, F007.SEQUENCE, "tasti-bis")
                e2, m2 = F007.judge(st2, F007.ATTESO) if not why2 else (S.BLOCKED, why2)
                if e2 == S.PASS:
                    e, m = S.PASS, "⚠ RED at the first attempt (%s), green at the second" % m
                else:
                    m = "red twice: %s · %s" % (m, m2)
                photo = photo2 or photo
            E.put("F-007", e, m, expected="a=%r b=%r" % F007.ATTESO, observed=m,
                    evidence=[x for x in (photo,) if x])
        if o.fault:
            # ⭐ the fault of 15-f007: the same sequence WITHOUT the Esc ⇒ «b» does not empty
            steps = F007.without(F007.SEQUENCE, F007.FAULT_REMOVES)
            st, photo, why = F007.beat(s, sc, mp, steps, "tasti-guasto")
            if why:
                E.fault("F-007", None, why)
            else:
                eg, mg = F007.judge(st, F007.ATTESO)
                E.fault("F-007", None if eg == S.BLOCKED else eg == S.FAIL,
                         "without %s: %s" % (F007.FAULT_REMOVES, mg), observed=mg,
                         evidence=[photo] if photo else [])


def f003(o, E, s):
    """Opens and changes, from the PHOTOGRAPH (the judges of 15-f003)."""
    geo, why = wait_canvas(s)
    if not geo:
        raise S.Blocked(why)
    time.sleep(1.5)
    _p, im0, _a, _b = F003.photo_im(s, "f003-prima")
    if im0 is None:
        raise S.Blocked("the canvas cannot be photographed")
    q0 = F003.cyan_fraction(im0)
    if q0 >= F003.CYAN_ABSENT:
        raise S.Blocked("before opening there is already some cyan (%.2f %%)" % (100 * q0))
    largo_f, alto_f = geo["tl"] * 0.45, geo["ta"] * 0.55
    c, t = F003.prepare_home(s, largo_f, alto_f)
    if c != 0:
        raise S.Blocked("the home cannot be prepared: %s" % (t or "")[-200:])
    ok, t = C21.turn_on_window(s.sc, s.chi)
    if not ok:
        raise S.Blocked("firefox-esr does not start: %s" % (t or "")[-200:])
    t_ap = time.time()
    f1, im1 = F003.wait_still(s, F003.OPENING_S, "f003-aperta")
    parts, faults = [], []
    if not f1:
        _p, im_x, _a, _b = F003.photo_im(s, "f003-apertura-non-vista")
        fresh = F003.changed(im0, im_x) if im_x is not None else 0.0
        if not F003.process_alive(s):
            parts.append(("apre", S.BLOCKED, "firefox-esr did not stay alive: %s" % im1))
        elif fresh > F003.CHANGED_MIN:
            parts.append(("apre", S.BLOCKED, "the photo changed (%.1f %%) but does not show the "
                          "test page" % (100 * fresh)))
        else:
            parts.append(("apre", S.FAIL, "firefox-esr alive for %.0f s and the photo is IDENTICAL to "
                          "the one before: the screen does not update" % (time.time() - t_ap)))
    else:
        pw, _ph = f1["photo"]
        wide_photo = largo_f * geo["sx"] * pw / geo["bw"]
        e, m = F003.judge_opening(f1, wide_photo)
        if e == S.FAIL:
            e, m = S.BLOCKED, "the cyan is not as wide as the requested window: a preview?"
        parts.append(("apre", e, m + " (in %.1f s)" % (time.time() - t_ap)))
        # ⭐ fault «opens»: the photo from BEFORE the opening given to the judge
        f0, _ = F003.find(im0)
        faults.append(("apre", F003.judge_opening(f0, wide_photo)))
        if e == S.PASS:
            v0, mv = F003.read_counter(im1, f1["rett"])
            if v0 is None:
                parts.append(("cambia", S.BLOCKED, "the counter cannot be read: %s" % mv))
            else:
                serial = []
                for cur_round in range(2):               # a red is confirmed, as in 15-f003
                    readings, first_im = [], None
                    t_via = time.time()
                    while (time.time() - t_via < F003.QUICK_S or len(readings) < F003.PHOTO_MIN) \
                            and time.time() - t_via < F003.QUICK_MAX_S:
                        _png, im, tp, td = F003.photo_im(s)
                        if im is None:
                            continue
                        n, mn = F003.read_counter(im, f1["rett"])
                        readings.append((tp, td, n, mn))
                        first_im = first_im or im
                    e, m, lines = F003.judge_quick(readings)
                    s.save_text("f003-rapide-%d.txt" % cur_round, lines)
                    serial.append((e, m, readings, first_im))
                    print("   fast changes, series %d: %s %s" % (cur_round + 1, e, m), flush=True)
                    if e == S.PASS:
                        break
                e, m, readings, first_im = serial[-1]
                if readings and first_im is not None:
                    # ⭐ fault «change» (15-f003): the FIRST photo for all, with the real instants
                    n0, m0 = F003.read_counter(first_im, f1["rett"])
                    ge, gm, _ = F003.judge_quick([(tp, td, n0, m0)
                                                     for tp, td, _n, _m in readings])
                    faults.append(("cambia", (ge, gm)))
                if len(serial) > 1:
                    m = "series 1: %s %s · series 2: %s" % (serial[0][0], serial[0][1], m)
                parts.append(("cambia", e, m))
    via_le_scene(s)
    es = F003.overall(parts)
    text = " · ".join("%s %s: %s" % p for p in parts)
    E.put("F-003", es, text if es != S.PASS else "opens and changes: the photos follow the "
            "screen (reduced: no drag)", expected="the window opens in the photo; "
            "counter ≤ %.0f ms in every photo for %d s" % (F003.CAP_MS, F003.QUICK_S),
            observed=text, evidenze=[o.evidenze], parts={p: [e, m] for p, e, m in parts})
    if o.fault:
        if es != S.PASS:
            E.fault("F-003", None, "the healthy pass is not green: the fault is judged only "
                     "on a healthy pass")
        else:
            seen_items = {p: r[0] == S.FAIL for p, r in faults}
            E.fault("F-003", len(seen_items) == 2 and all(seen_items.values()),
                     "photo from BEFORE ⇒ " + " · ".join("%s %s" % (p, "red" if r[0] == S.FAIL
                                                              else r[0]) for p, r in faults),
                     observed=" | ".join("%s: %s" % (p, r[1]) for p, r in faults))


def f014(o, E, s):
    geo = s.geometry()
    if not geo:
        raise S.Blocked("the canvas geometry is not there")
    g = s.g
    st = g.js(F014.CLIPBOARD_STATE)
    if not st or not st.get("on"):
        E.put("F-014", S.FAIL, "the page's clipboard is not on: %s" % st)
        return
    scene = F014.Scene(s, o.base_port + 5)
    try:
        ok, t = scene.turn_on()
        if not ok:
            raise S.Blocked("the clipboard scene does not start: %s" % (t or "")[-300:])
        time.sleep(3)
        x, y = C21.desktop_to_glass(geo, geo["tl"] * 0.5, geo["ta"] * 0.3)
        g.click(x, y)
        time.sleep(1.0)
        scene.in_charge(clean=True)
        da = len(scene.notebook())
        F014.letter(g, "q")
        v, _q = scene.wait_value("q", da, 8)
        if v != "q":
            raise S.Blocked("the keyboard does not reach the scene's field (a «q» ⇒ %r)" % (v,))
        text = F014.unique_text("F014")
        seen, det = F014.browser_to_session(s, scene, geo, text)
        _png, dove = s.photo("f014")
        ev = [x for x in (dove, s.save_text("f014.json", json.dumps(
            det, ensure_ascii=False, indent=1))) if x]
        e, why = F014.judge_text(text, seen)
        if e == S.FAIL and not det.get("gesture_arrived"):
            e, why = S.BLOCKED, ("the Ctrl+V did not reach the application: it is the "
                                    "keyboard, not the clipboard — " + why)
        if det.get("riprova_ctrl_v"):
            why += " · (Ctrl+V typed again once)"
        E.put("F-014", e, why, expected=text, observed=seen, evidence=ev)
        if o.fault:
            # ⭐ the two faults of 15-f014: «different expected» (the true value against the text
            #   without accents) and «copy not done» (no Ctrl+C in the browser)
            ad = F014.judge_text(F014.strip_accents(text), seen)[0] == S.FAIL
            tg = F014.unique_text("F014G")
            vg, dg = F014.browser_to_session(s, scene, geo, tg, copied=False)
            s.save_text("f014-guasto.json", json.dumps(dg, ensure_ascii=False, indent=1))
            rg = F014.judge_text(tg, vg)[0] == S.FAIL
            E.fault("F-014", (rg and ad) if dg.get("gesture_arrived") else None,
                     "copy not done ⇒ the remote field is %r (%s); expected without accents ⇒ %s"
                     % ((vg or "")[:50], "RED" if rg else "GREEN", "RED" if ad else "GREEN"),
                     expected=tg, observed=vg)
    finally:
        scene.turn_off()


# ═══════════════════════════════════════════════════════════════════════════
def main():
    o = S.call_args(__doc__, extra)
    o.cap_s = max(o.cap_s, CAP_BIRTH_S)
    o.functions = [f for f in FUNCTIONS if not o.only or f in o.only.split(",")]
    os.makedirs(o.dir, exist_ok=True)
    o.evidenze = o.evidenze or os.path.join(o.dir, "short-check")
    os.makedirs(o.evidenze, exist_ok=True)
    E = S.Outcomes(o)
    nnn = "%03d" % o.level
    chi = "c16%su%d" % (nnn, o.user)
    started, t0 = t_now(), time.time()
    # ⭐ the schema that 16-classifica.py reads: «user» is the NUMBER (99: no
    #   actor has that number ⇒ the entry goes to the level), «outcomes» {F-NNN: outcome}
    ratio = {"level": o.level, "user": o.user, "tenant": chi, "browser": o.browser,
                "box": o.box,
                "size": "%dx%d" % (o.largo, o.alto), "started": started,
                "wayland": os.environ.get("WAYLAND_DISPLAY", ""), "functions": {},
                "birth": {}, "evidence": o.evidence}
    print("⭐ short check · %s · level %d · %s · %s · %s" % (
        o.box, o.level, chi, o.browser, o.url), flush=True)
    sign = None
    try:
        with S.Session(o, nnn, E, chi=chi) as s:
            ratio["version"] = E.version
            if o.browser == "chrome" and "F-014" in o.functions:
                # ⭐ the clipboard permission, as the user would give it (15-f014)
                try:
                    s.g.cdp.call("Browser.grantPermissions", origin=o.url.rstrip("/"),
                                   permissions=["clipboardReadWrite", "clipboardSanitizedWrite"])
                except Exception as e:           # noqa: BLE001
                    print("   ⚠ clipboard permission NOT granted: %s" % e, flush=True)
            sign = s.log_mark()
            try:
                ratio["sessions_during"] = live_sessions(s)
            except Exception:                    # noqa: BLE001
                pass
            ok, m, times = bring_up(s, o)
            ratio["birth"] = dict(times, outcome="PASS" if ok else "FAIL", rationale=m)
            print("   birth: %s · %s" % (json.dumps(times), m), flush=True)
            if not ok:
                raise S.Blocked("the check's session was not born: %s" % m)
            geo = s.geometry()
            if geo:
                print("   wake-up: %s" % C21.wake(s.g, geo), flush=True)
            for f, step in (("F-004", None), ("F-003", f003), ("F-014", f014)):
                if f == "F-004":
                    if "F-004" in o.functions or "F-007" in o.functions:
                        try:
                            f004_f007(o, E, s, times)
                        except S.Blocked as b:
                            for ps in ("healthy", "fault") if o.fault else ("healthy",):
                                E.blocked([x for x in ("F-004", "F-007") if x in o.functions],
                                           str(b), passed=ps)
                        except Exception as e:   # noqa: BLE001
                            traceback.print_exc()
                            E.blocked([x for x in ("F-004", "F-007") if x in o.functions],
                                       "the bench crashed: %r" % e)
                        via_le_scene(s)
                    continue
                if f not in o.functions:
                    continue
                try:
                    step(o, E, s)
                except S.Blocked as b:
                    for ps in ("healthy", "fault") if o.fault else ("healthy",):
                        E.blocked([f], str(b), passed=ps)
                except Exception as e:           # noqa: BLE001
                    traceback.print_exc()
                    E.blocked([f], "the bench crashed: %r" % e)
                via_le_scene(s)
            s.save_console()
            if sign is not None:
                s.save_text("server-controllo.txt", s.log_from(sign))
    except S.Blocked as b:
        E.blocked(o.functions, str(b))
        if o.fault:
            E.blocked(o.functions, str(b), passed="fault")
    except Exception as e:                       # noqa: BLE001
        traceback.print_exc()
        E.blocked(o.functions, "the bench crashed: %r" % e)
    E.blocked(o.functions, "the test gave no judgement (defect of the bench)")
    if o.fault:
        E.blocked(o.functions, "the pass with the fault gave no judgement", passed="fault")
    ratio["faults"] = {}
    for r in E.lines:
        dove = ratio["faults"] if r["pass"] == "fault" else ratio["functions"]
        dove[r["function"]] = {k: r.get(k) for k in (
            "outcome", "rationale", "expected", "observed", "evidence", "fault_seen")}
    # ⚠ «outcomes» (read by 16-classifica.py) is ONLY the healthy pass
    ratio["outcomes"] = {f: v["outcome"] for f, v in ratio["functions"].items()}
    def total_sum(es):
        return S.FAIL if S.FAIL in es else (S.BLOCKED if S.BLOCKED in es or not es else S.PASS)
    ratio["outcome"] = total_sum([r["outcome"] for r in E.lines if r["pass"] == "healthy"])
    if o.fault:
        # PASS = every grafted fault was SEEN (the judge gave red)
        ratio["fault_outcome"] = total_sum([r["outcome"] for r in E.lines if r["pass"] == "fault"])
    if ratio["birth"].get("outcome") == "FAIL" and ratio["birth"].get("refusal"):
        ratio["outcome"] = S.FAIL                # §9: refusal ⇒ FAIL
    ratio["duration_s"] = round(time.time() - t0)
    ratio["end"] = t_now()
    p = os.path.join(o.dir, "short-check.json")
    with open(p + ".tmp", "w") as f:
        json.dump(ratio, f, ensure_ascii=False, indent=1)
    os.replace(p + ".tmp", p)
    print("⏱ %d s · %s · %s" % (ratio["duration_s"], ratio["outcome"], p), flush=True)
    fin = [ratio["outcome"], ratio.get("fault_outcome", S.PASS)]
    return 1 if S.FAIL in fin else (3 if S.BLOCKED in fin else 0)


def live_sessions(s):
    """How many graphical sessions there are in the box now (to declare N+1)."""
    _c, t = s.sc.inside("loginctl list-sessions --no-legend 2>/dev/null | awk '{print $3}' "
                        "| grep -cE '^c[0-9]+b?u[0-9]+$'", 30)
    try:
        return int((t or "").split()[-1])
    except (ValueError, IndexError):
        return None


if __name__ == "__main__":
    sys.exit(main())
