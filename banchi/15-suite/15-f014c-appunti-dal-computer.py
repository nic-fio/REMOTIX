#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f014c — THE CLIPBOARD AS A PERSON USES IT: WITH THE COMPUTER, NOT WITH THE BENCH

    python3 15-f014c-appunti-dal-computer.py --container_box gnome --browser chrome [--fault]
    python3 15-f014c-appunti-dal-computer.py --certify

WHY IT EXISTS (2 Oct 2026, the user's manual test: «Ctrl+C / Ctrl+V do not
work, or not always», Firefox AND Chrome, all the desktops).  `15-f014` is
green but does not see what the person sees: it makes courtesy clicks, reads the
clipboard from the page with `readText()`, GIVES Chrome the permission, never reuses
a text and never copies OUTSIDE the browser.  This test does as the person does:

  - the COMPUTER's clipboard (not the page's) is written and read with
    `wl-copy` / `wl-paste` in the browser's Wayland session (the desktop's
    headless labwc, the one of 15-compositori.sh: the same WAYLAND_DISPLAY
    the round gives the browser);
  - NO courtesy click: only the click the person really makes (one on the
    canvas before pasting);
  - Chrome WITHOUT the clipboard permission (no `Browser.grantPermissions`);
  - one `Ctrl+V` at a time, never typed again: the first is the one that counts.

The scene and the gestures are those of `15-f014` (imported, not copied): a
`firefox-esr --kiosk` in the session with an always-focused <textarea>, which
writes down every value; the judgment is the FIELD VALUE of the session's
application, or the text in the computer's clipboard.

F-015C  (P1) session → computer, without recent gestures.  The text in the scene's
        field, selected; 6 s still (no click: the browser's activation
        expires); REAL `Ctrl+C` on the page ⇒ within 3 s `wl-paste` must be
        EXACTLY that text.
F-014C  (P2, the main one) the text copied OUTSIDE the browser.  `Ctrl+C` in the
        scene (text Z: now the session's clipboard belongs to a remote
        application), then `wl-copy X` outside the browser, ONE click on the canvas, ONE
        `Ctrl+V` ⇒ the scene's field must be X.  Five times, new texts
        each time; green only if all five.
F-014D  (P1b) the SAME text copied twice.  `wl-copy X`, click, `Ctrl+V` ⇒
        X; then a copy in the session (text W), then `wl-copy X` again
        (identical), click, `Ctrl+V` ⇒ X.

FAULT (same session, after the healthy pass):
  F-015C  «copy not made»: the text in the field, 6 s, NO `Ctrl+C` ⇒
          `wl-paste` does not see it ⇒ RED.  And the healthy value judged against
          the same text without accents ⇒ RED.
  F-014C  «outside copy not made»: `Ctrl+C` in the scene, NO `wl-copy X`,
          click, `Ctrl+V` ⇒ the field is not X ⇒ RED.  And the expectation without accents.
  F-014D  «the second copy is another text»: the second `wl-copy` puts Y,
          the expectation stays X ⇒ RED.  And the expectation without accents.

⚠ Only Firefox and Chrome on the server (the phone has no `wl-copy`: BLOCKED).
"""
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

FUNCTIONS = ("F-015C", "F-014C", "F-014D")

# ⭐ the scene, the gestures and the judge of 15-f014 (its local `inside` too)
F14 = S._load("f014", os.path.join(S.HERE, "15-f014-appunti.py"))

ROUNDS_P2 = 5
STILL_P1_S = 6.0          # no gestures: the transient activation (5 s) expires
CAP_P1_S = 3.0          # within how long the text must be in the computer's clipboard
WAIT_FIELD_S = 12.0


# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def judge_rounds(rounds, how_many):
    """(outcome, why) on the P2 rounds: [{"expected_val", "seen_v", "gesture"}].
    The rounds without the Ctrl+V keydown do not count (it is the keyboard)."""
    valid = [g for g in rounds if g.get("gesture")]
    wrong = [g for g in valid if g.get("seen_v") != g.get("expected_val")]
    if wrong:
        stale = sum(1 for g in wrong if g.get("seen_v") and g.get("seen_v") == g.get("remote"))
        return S.FAIL, ("%d rounds of %d: at the first Ctrl+V the field is NOT the text copied "
                        "outside the browser (%d times it is the OLD text copied in the "
                        "session)" % (len(wrong), len(valid), stale))
    if len(valid) < how_many:
        return S.BLOCKED, ("only %d valid rounds of %d: the Ctrl+V did not reach "
                           "the application in the others" % (len(valid), how_many))
    return S.PASS, "%d rounds of %d: the field is the text copied outside" % (len(valid), how_many)


def certify():
    t = F14.unique_text("X")
    z = F14.unique_text("Z")
    rounds_ok = [{"expected_val": t, "seen_v": t, "gesture": True}] * ROUNDS_P2
    cases = [
        ("f014's judge: identical ⇒ PASS", F14.judge_text(t, t)[0] == S.PASS),
        ("without accents ⇒ FAIL", F14.judge_text(t, F14.strip_accents(t))[0] == S.FAIL),
        ("five right rounds ⇒ PASS", judge_rounds(rounds_ok, ROUNDS_P2)[0] == S.PASS),
        ("one round with the old text ⇒ FAIL", judge_rounds(
            rounds_ok[:4] + [{"expected_val": t, "seen_v": z, "remote": z, "gesture": True}],
            ROUNDS_P2)[0] == S.FAIL),
        ("the old text is counted", "1 times" in judge_rounds(
            [{"expected_val": t, "seen_v": z, "remote": z, "gesture": True}], 1)[1]),
        ("one wrong round is enough even with few valid ones", judge_rounds(
            [{"expected_val": t, "seen_v": None, "gesture": True},
             {"expected_val": t, "seen_v": None, "gesture": False}], ROUNDS_P2)[0] == S.FAIL),
        ("rounds without gesture ⇒ BLOCKED", judge_rounds(
            [{"expected_val": t, "seen_v": None, "gesture": False}] * ROUNDS_P2, ROUNDS_P2)[0] == S.BLOCKED),
        ("four valid right out of five ⇒ BLOCKED", judge_rounds(
            rounds_ok[:4], ROUNDS_P2)[0] == S.BLOCKED),
    ]
    ok = True
    for label_name, real in cases:
        print("%s %s" % ("⭐" if real else "⛔", label_name))
        ok = ok and real
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE COMPUTER'S CLIPBOARD (the browser's Wayland session)
# ═══════════════════════════════════════════════════════════════════════════
def wl_copy(body_text):
    """`wl-copy` as another application of the computer would do it.  ⚠ wl-copy
    stays alive in the background serving the text: the outputs do NOT go into a pipe."""
    r = subprocess.run(["wl-copy"], input=body_text.encode("utf-8"), stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=10)
    return r.returncode == 0


def wl_read():
    """The text in the computer's clipboard, or None."""
    try:
        r = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, timeout=5)
    except subprocess.TimeoutExpired:
        return None
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", "replace")


def focus_to_browser():
    """The compositor's KEYBOARD focus to the browser.  ⚠ `[M]` 2 Oct 2026,
    round `cure-intel-2`: the keys of `wtype` reached nobody — the bench's
    browser receives clicks and keys from Marionette/CDP, which do not go through the
    compositor, so labwc never gave it the focus.  The person gives the focus
    by clicking on the window; here it is requested with `wlrctl` (wlroots'
    foreign-toplevel protocol).  Returns the focused app_id, or None."""
    if not shutil.which("wlrctl"):
        return None
    try:
        r = subprocess.run(["wlrctl", "toplevel", "list"], capture_output=True, timeout=5)
    except subprocess.TimeoutExpired:
        return None
    for row in r.stdout.decode("utf-8", "replace").splitlines():
        app = row.split(":", 1)[0].strip()
        if "firefox" in app.lower() or "chrom" in app.lower():
            subprocess.run(["wlrctl", "toplevel", "focus", "app_id:" + app],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            time.sleep(0.2)
            return app
    return None


def ctrl_from_system(g, letter):
    """`Ctrl+<letter>` typed BY THE GRAPHICAL SYSTEM (`wtype`, Wayland's virtual
    keyboard), not injected into the browser.  ⛔ Why it is needed: `[M]` 2 Oct 2026, round
    `f014c-prima` — with the injected `Ctrl+C` (Marionette / `Input.dispatchKeyEvent`)
    Firefox AND Chrome say they wrote to the clipboard (`written` 1, nothing
    pending) and `wl-paste` sees nothing: a Wayland client takes the selection
    only with the serial number of a REAL input event of the compositor, and a
    key injected into the browser has none.  The person types the keys on the
    keyboard: this is the road that resembles it.  Without `wtype` we go back to the
    injected key, and it is declared."""
    # ⛔ But the combination is NOT typed with `wtype`: `[M]` round `cure-intel-3`,
    #   BLOCKED — `wtype` loads a key map of ITS OWN, with invented codes, and
    #   the page sends the desktop the POSITION (`KeyboardEvent.code`): the
    #   Ctrl+C arrived as another key.  ⇒ Only a Shift goes through the graphical system
    #   (the page does not send it: «on their own they are not sent»), which gives the
    #   browser the keyboard focus and a fresh serial number; the
    #   combination stays injected, with the right positions.
    via = "injected"
    if shutil.which("wtype") and focus_to_browser():
        r = subprocess.run(["wtype", "-k", "Shift_L"], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=10)
        if r.returncode == 0:
            via = "serial from the system + injected"
            time.sleep(0.1)
    F14.ctrl(g, letter)
    return via


def wl_clear():
    try:
        subprocess.run(["wl-copy", "--clear"], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=10)
    except Exception:                            # noqa: BLE001
        pass


def state(g):
    try:
        return g.js(F14.CLIPBOARD_STATE) or {}
    except Exception as e:                       # noqa: BLE001
        return {"failure": str(e)[:200]}


def counts(st):
    return dict((st or {}).get("counts") or {})


# ═══════════════════════════════════════════════════════════════════════════
#  THE PERSON'S GESTURES
# ═══════════════════════════════════════════════════════════════════════════
def point_field(geo):
    return S.C21.desktop_to_glass(geo, geo["tl"] * 0.5, geo["ta"] * 0.3)


def copy_into_session(g, scene, body_text, copia=True):
    """The text in the scene's field, selected, and REAL `Ctrl+C` on the page.
    No click.  Returns the details (gesture arrived or not)."""
    q = scene.in_charge(put=body_text)
    if F14.last_value(q) != body_text:
        raise S.Blocked("the scene did not take the text to copy: %r" % (F14.last_value(q),))
    det = {"copia_fatta": copia, "state_before": state(g)}
    da = len(q)
    if copia:
        det["key"] = ctrl_from_system(g, "c")
        fine = time.time() + 5
        while time.time() < fine and not F14.key_seen(scene.notebook()[da:], "c"):
            time.sleep(0.5)
        det["gesto_arrivato"] = F14.key_seen(scene.notebook()[da:], "c")
    return det, da


def paste_once(g, scene, geo, expected_val):
    """ONE click on the canvas (on the remote field), ONE Ctrl+V.  Never typed again.
    Returns (value of the field, details)."""
    da = len(scene.notebook())
    x, y = point_field(geo)
    det = {}
    g.click(x, y)
    time.sleep(1.0)
    det["computer_al_ctrl_v"] = wl_read()
    det["state_before"] = state(g)
    det["key"] = ctrl_from_system(g, "v")
    seen_v, q = scene.wait_value(expected_val, da, WAIT_FIELD_S)
    det["gesto_arrivato"] = F14.key_seen(q, "v")
    det["incollato_dalla_scena"] = [v for t, v in q if t == "P"]
    det["notebook"] = q[-10:]
    det["state_after"] = state(g)
    det["announcements"] = counts(det["state_after"]).get("announced", 0) - \
        counts(det["state_before"]).get("announced", 0)
    det["computer_dopo"] = wl_read()
    return seen_v, det


# ═══════════════════════════════════════════════════════════════════════════
#  THE THREE TESTS
# ═══════════════════════════════════════════════════════════════════════════
def p1(g, scene, body_text, copia=True):
    """F-015C: returns (text in the computer's clipboard within 3 s, details)."""
    wl_copy("prima-di-P1 " + F14.unique_text("S"))
    q = scene.in_charge(put=body_text)
    if F14.last_value(q) != body_text:
        raise S.Blocked("the scene did not take the text: %r" % (F14.last_value(q),))
    time.sleep(STILL_P1_S)                       # ⭐ still: no recent gesture
    det = {"copia_fatta": copia, "state_before": state(g)}
    da = len(scene.notebook())
    if copia:
        det["key"] = ctrl_from_system(g, "c")
    t0 = time.time()
    read, readings = None, []
    while time.time() - t0 < CAP_P1_S:
        read = wl_read()
        readings.append((round(time.time() - t0, 2), (read or "")[:60]))
        if read == body_text:
            break
        time.sleep(0.2)
    det["entro_s"] = round(time.time() - t0, 2) if read == body_text else None
    det["readings"] = readings[-6:]
    det["gesto_arrivato"] = F14.key_seen(scene.notebook()[da:], "c") if copia else None
    det["state_after"] = state(g)
    det["computer_dopo_5s"] = None
    if read != body_text:
        time.sleep(2.0)
        det["computer_dopo_5s"] = wl_read()      # diagnosis: is it only late?
        det["stato_dopo_5s"] = state(g)
    det["diary"] = g.js(F14.DIARY)
    return read, det


def p2_round(g, scene, geo, code_tag, copy_out=True):
    """F-014C, one round.  Returns {"expected_val", "seen_v", "remote", "gesture", ...}."""
    z = F14.unique_text(code_tag + "Z")
    x = F14.unique_text(code_tag + "X")
    dc, _da = copy_into_session(g, scene, z)
    time.sleep(2.0)                              # the person switches to another window
    st_copy = state(g)
    scene.in_charge(clean=True)
    if copy_out:
        wl_copy(x)
    outside = wl_read()
    time.sleep(1.0)                              # and comes back to the browser
    seen_v, di = paste_once(g, scene, geo, x)
    r = {"expected_val": x, "seen_v": seen_v, "remote": z, "copy_out": copy_out,
         "gesture": di["gesto_arrivato"], "ctrl_c_arrivato": dc.get("gesto_arrivato"),
         "computer_dopo_wl_copy": outside, "stato_dopo_copia": st_copy}
    r.update(di)
    return r


def p1b(g, scene, geo, x, second):
    """F-014D: (first value, second value, details)."""
    det = {}
    scene.in_charge(clean=True)
    wl_copy(x)
    time.sleep(1.0)
    v1, det["first"] = paste_once(g, scene, geo, x)
    w = F14.unique_text("P1bW")
    det["copia_remota"], _ = copy_into_session(g, scene, w)
    time.sleep(2.0)
    det["stato_dopo_copia_remota"] = state(g)
    scene.in_charge(clean=True)
    wl_copy(second)
    det["computer_seconda"] = wl_read()
    time.sleep(1.0)
    v2, det["second"] = paste_once(g, scene, geo, x)
    det["remote"] = w
    det["diary"] = g.js(F14.DIARY)
    return v1, v2, det


def judge_p1b(x, v1, v2, det):
    e1, p1_ = F14.judge_text(x, v1)
    e2, p2_ = F14.judge_text(x, v2)
    if e1 == S.PASS and e2 == S.PASS:
        return S.PASS, "both times the field is the copied text (even the second, identical one)"
    parts = []
    if e1 != S.PASS:
        parts.append("first time: " + p1_)
    if e2 != S.PASS:
        which = "the text of the REMOTE copy" if v2 == det.get("remote") else p2_
        parts.append("second time (same text copied again): %s · announcements sent at the "
                     "Ctrl+V: %s" % (which, det.get("second", {}).get("announcements")))
    gestures = [det.get(k, {}).get("gesto_arrivato") for k in ("first", "second")]
    if not all(gestures):
        return S.BLOCKED, ("the Ctrl+V did not reach the application (%s): it is the keyboard "
                           "— " % gestures) + " · ".join(parts)
    return S.FAIL, " · ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
def body_el(o, E):
    if o.browser == "phone":
        raise S.Blocked("the phone has no `wl-copy`: the computer's clipboard is looked at "
                         "only on the server")
    wd = os.environ.get("WAYLAND_DISPLAY", "")
    rd = os.environ.get("XDG_RUNTIME_DIR", "")
    if not wd or not os.path.exists(os.path.join(rd, wd)):
        raise S.Blocked("no Wayland session of the browser (WAYLAND_DISPLAY=%r, "
                         "XDG_RUNTIME_DIR=%r): it is launched from the round or from 15-una.sh" % (wd, rd))
    prova = F14.unique_text("WL")
    if not wl_copy(prova) or wl_read() != prova:
        raise S.Blocked("the computer's clipboard cannot be written/read with wl-copy/"
                         "wl-paste on %s" % wd)
    print("   computer's clipboard: %s (wl-copy/wl-paste)" % wd, flush=True)
    scene_port = o.base_ports + 6
    try:
        with S.Session(o, "914", E) as s:
            # ⛔ NO clipboard permission to Chrome: like the user who has
            #   never clicked «Allow»
            inside(o, E, s, scene_port)
    finally:
        wl_clear()


def inside(o, E, s, scene_port):
    g = s.g
    sign = s.log_mark()
    ok, m = s.enter()
    if not ok:
        raise S.Blocked(m)
    geo = s.geometry()
    if not geo:
        raise S.Blocked("the canvas geometry is not there")
    st = state(g)
    print("   page clipboard: %s" % json.dumps(st, ensure_ascii=False), flush=True)
    if not st or not st.get("lit"):
        for f in FUNCTIONS:
            E.put(f, S.FAIL, "the page's clipboard is not on: %s" % st)
        return
    print("   wake-up: %s" % S.C21.wake(g, geo), flush=True)
    scene = F14.Scene(s, scene_port)
    try:
        set_up_scene(o, E, s, g, geo, scene)
    finally:
        try:
            s.save_text("server-f014c.txt", s.log_from(sign) if sign is not None else [])
            s.save_console()
        finally:
            scene.turn_off()


def set_up_scene(o, E, s, g, geo, scene):
    ok, t = scene.turn_on()
    print("   scene: %s" % ((t or "?").splitlines() or ["?"])[-1], flush=True)
    if not ok:
        print(t, flush=True)
        s.picture("scena-non-accesa")
        raise S.Blocked("the scene does not start: %s" % (t or "")[-300:])
    time.sleep(3)
    # ⛔ poor man's check: does the keyboard reach the remote field?
    x, y = point_field(geo)
    g.click(x, y)
    time.sleep(1.0)
    scene.in_charge(clean=True)
    da = len(scene.notebook())
    F14.letter(g, "q")
    v, _q = scene.wait_value("q", da, 8)
    if v != "q":
        raise S.Blocked("the keyboard does not reach the scene's field (a «q» typed ⇒ %r)"
                         % (v,))
    scene.in_charge(clean=True)
    store = lambda label_name, d: s.save_text(label_name, json.dumps(d, ensure_ascii=False, indent=1))  # noqa: E731

    # ── P1 · F-015C ────────────────────────────────────────────────────────
    t1 = F14.unique_text("P1")
    read1, d1 = p1(g, scene, t1)
    ev1 = [store("p1-sana.json", d1)]
    e, reason_text = F14.judge_text(t1, read1)
    if e == S.PASS:
        reason_text += " · in the computer's clipboard after %.2f s" % d1["entro_s"]
    else:
        reason_text = "within %.0f s of the Ctrl+C (still for %.0f s, no click) the computer's " \
                 "clipboard does not have the text: %s" % (CAP_P1_S, STILL_P1_S, reason_text)
        if d1.get("computer_dopo_5s") == t1:
            reason_text += " · it arrives AFTER the 3 s"
        if (d1.get("state_after") or {}).get("waiting"):
            reason_text += " · the page keeps it «waiting for a gesture»"
        if not d1.get("gesto_arrivato"):
            e, reason_text = S.BLOCKED, ("the Ctrl+C did not reach the session's "
                                    "application: it is the keyboard — " + reason_text)
    E.put("F-015C", e, reason_text, expected_val=t1, observed=read1, evidence=ev1)

    # ── P2 · F-014C ────────────────────────────────────────────────────────
    rounds = []
    for i in range(ROUNDS_P2 + 3):
        if sum(1 for r in rounds if r["gesture"]) >= ROUNDS_P2:
            break
        r = p2_round(g, scene, geo, "P2%d" % i)
        rounds.append(r)
        print("   P2 round %d: %s (Ctrl+V %s, announcements %s)" % (
            i + 1, "right" if r["seen_v"] == r["expected_val"] else
            ("OLD TEXT of the session" if r["seen_v"] == r["remote"] else
             "wrong: %r" % (r["seen_v"] or "")[:40]),
            "arrived" if r["gesture"] else "NOT arrived", r.get("announcements")), flush=True)
        if r["seen_v"] != r["expected_val"] and not any(x.get("picture") for x in rounds):
            r["picture"] = s.picture("p2-giro%d-sbagliato" % (i + 1))[1]
    _png, photo2 = s.picture("p2-fine")
    ev2 = [store("p2-sana.json", {"rounds": rounds, "diary": g.js(F14.DIARY)})]
    ev2 += [x for x in [photo2] + [r.get("picture") for r in rounds] if x]
    e, reason_text = judge_rounds(rounds, ROUNDS_P2)
    E.put("F-014C", e, reason_text, expected_val=" | ".join(r["expected_val"] for r in rounds),
            observed=" | ".join(repr(r["seen_v"]) for r in rounds), evidence=ev2)

    # ── P1b · F-014D ───────────────────────────────────────────────────────
    xb = F14.unique_text("P1b")
    v1, v2, db = p1b(g, scene, geo, xb, xb)
    evb = [store("p1b-sana.json", db)]
    e, reason_text = judge_p1b(xb, v1, v2, db)
    E.put("F-014D", e, reason_text, expected_val=xb, observed="%r | %r" % (v1, v2), evidence=evb)

    if not o.fault:
        return
    # ── THE FAULTS ─────────────────────────────────────────────────────────
    ad1 = F14.judge_text(F14.strip_accents(t1), read1)[0] == S.FAIL
    g1 = F14.unique_text("P1G")
    lg1, dg1 = p1(g, scene, g1, copia=False)
    store("p1-guasto.json", dg1)
    r1 = F14.judge_text(g1, lg1)[0] == S.FAIL
    E.fault("F-015C", r1 and ad1,
             "Ctrl+C not made ⇒ the computer's clipboard is %r (%s); expected without "
             "accents ⇒ %s" % ((lg1 or "")[:50], "RED" if r1 else "GREEN",
                               "RED" if ad1 else "GREEN"), expected_val=g1, observed=lg1)

    ad2 = all(F14.judge_text(F14.strip_accents(r["expected_val"]), r["seen_v"])[0] == S.FAIL
              for r in rounds)
    rg = p2_round(g, scene, geo, "P2G", copy_out=False)
    store("p2-guasto.json", rg)
    r2 = rg["seen_v"] != rg["expected_val"]
    E.fault("F-014C", (r2 and ad2) if rg["gesture"] else None,
             "wl-copy not made ⇒ the field is %r (%s); expected without accents ⇒ %s"
             % ((rg["seen_v"] or "")[:50], "RED" if r2 else "GREEN",
                "RED" if ad2 else "GREEN"), expected_val=rg["expected_val"], observed=rg["seen_v"])

    adb = F14.judge_text(F14.strip_accents(xb), v2)[0] == S.FAIL
    xg = F14.unique_text("P1bG")
    yg = F14.unique_text("P1bY")
    gv1, gv2, dgb = p1b(g, scene, geo, xg, yg)
    store("p1b-guasto.json", dgb)
    rb = judge_p1b(xg, gv1, gv2, dgb)[0] != S.PASS
    gestures = dgb["first"]["gesto_arrivato"] and dgb["second"]["gesto_arrivato"]
    E.fault("F-014D", (rb and adb) if gestures else None,
             "the second copy is another text ⇒ the field is %r (%s); expected without "
             "accents ⇒ %s" % ((gv2 or "")[:50], "RED" if rb else "GREEN",
                               "RED" if adb else "GREEN"), expected_val=xg, observed=gv2)


if __name__ == "__main__":
    sys.exit(S.execute(__doc__, FUNCTIONS, body_el, certify))
