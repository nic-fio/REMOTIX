#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f022 — THE THREE CLOCKS OF §5.3: F-022 silence · F-023 inactivity · F-024 abandonment

    python3 15-f022-orologi.py --box kde --browser chrome --fault --port 8612

⛔ A SERVER OF ITS OWN (`15-g7-server.sh`, ports 8611-8614): the clocks are shortened
   from the command line and the server is RESTARTED between one phase and the next — on the
   851x it cannot be done.  At the end the server stays on with the DEFAULTS.

THE REAL NAMES AND VALUES (read in the code, not in SPECIFICHE):
  · client silence: 30 s FIXED (`rcp.c` `#define SILENZIO 30000`, not
    configurable) — ⚠ but first the DEAD LINE fires at 10 s without a packet
    (`--dead-line-silence-s`, default 10, `webtransport.c`): it is the one that
    detaches a mute client, and frees the slot.  ⇒ the expectation of F-022 is «detached
    WITHIN 30 s», whichever of the two does it, and the line says so;
  · user inactivity: `--inactivity-s` (default 1800), in SECONDS;
    it resets on EVERY RCP byte from the client (`rcp.c` ~7523), fires with
    `FAREWELL 0x02` and the line «§5.3 — INACTIVITY»; the graphical session STAYS;
  · session abandonment: `--abandon-s` (default 3600); it feeds on the
    ONLY five input gestures (`main.c` `input_to_child` → `presence_mark`),
    fires with the line «§5.3 — ABANDONMENT» and closes the graphical session with its
    programs (`children_terminate_session`).

F-022  (default server) the browser STOPS (SIGSTOP to the whole tree of
       processes: the client goes silent, like a laptop switching off) ⇒ expected: within
       30 s the server detaches it (line `dead-line`/`DETACHED`/`slot LEFT`),
       the session stays (the tenant's programs alive), and with the browser resumed
       you come back in with user and password finding the same programs.
       FAULT: the browser does NOT stop ⇒ no detach in 35 s ⇒ the judge must
       say «not detached» (red).
F-023  (server with `--inactivity-s 12 --abandon-s 45`) one click and then nothing ⇒
       expected: between 12 and 12+15 s the INACTIVITY line, the page SAYS it (red
       sentence, form in view, no reconnecting by itself), the programs stay,
       and you come back in ONLY with user and password.
F-024  (same session) no gesture since that click ⇒ expected: within 45+15 s the
       ABANDONMENT line, and the processes of the tenant's session (the scene
       included) DISAPPEAR.
       FAULT F-023/F-024: the LONG clocks (the defaults) instead of the
       short ones, same sequence ⇒ no INACTIVITY in 12+15 s, no ABANDONMENT
       in 45+15 s, scene alive ⇒ the two judges must say red.
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

FUNCTIONS = ("F-022", "F-023", "F-024")
SERVER = "15-g7-server.sh"
SILENCE_S = 30
MARGIN_S = 15
# ⚠ 25 and not 12: `[M]` 25 Sep 2026 (D-011) the inactivity clock counts from the last
#   byte of the client, that is from the ATTACH, even while the session IS BEING BORN; on XFCE
#   in 4K the birth exceeds 12 s ⇒ FAREWELL 0x02 one second after the first
#   frame.  With the real values (1800 s) it does not bite; here the clock must be kept
#   longer than the slowest birth.
INACTIVITY_S = 25
ABANDON_S = 60
DETACH_MARKS = ("dead-line", "DETACHED for silence", "slot LEFT")


def certify():
    ok = True
    # the detach judge: a line of ANOTHER tenant does not count
    lines = ["21:00 rcp [c15022u111] slot LEFT by c15022u111 via x (taken now: 0)"]
    if judge_detach(lines, "c15022u222")[0]:
        print("⛔ the detach of another tenant counts as mine")
        ok = False
    if not judge_detach(lines, "c15022u111")[0]:
        print("⛔ the tenant's detach is not seen")
        ok = False
    for idle, abandoned in ((12, 45), (1800, 3600)):
        if not (idle + MARGIN_S < abandoned):
            print("⛔ the clocks tread on each other: inactivity %d, abandonment %d" % (idle, abandoned))
            ok = False
    print("%s clock judges" % ("⭐" if ok else "⛔"))
    return 0 if ok else 1


def judge_detach(lines, chi):
    for r in lines:
        if chi not in r:
            continue
        for f in DETACH_MARKS:
            if f in r:
                return True, r
    return False, None


def turn_on(o, *opt):
    ok, t = G7.server("start", o.box, *opt)
    if not ok:
        raise S.Blocked("our server does not start (%s): %s" % (" ".join(opt), t[-300:]))
    idle, abandoned, line = G7.clocks_in_effect(o.box)
    print("   our server: inactivity %s s · abandonment %s s" % (idle, abandoned), flush=True)
    return idle, abandoned


JS_GEO = r"""
const t = document.getElementById('viewer');
const r = t ? t.getBoundingClientRect() : null;
const cs = t ? getComputedStyle(t) : null;
const reg = document.getElementById('logbook');
return { rect: r ? [r.left, r.top, r.width, r.height] : null,
         display: cs ? cs.display : null, visibility: cs ? cs.visibility : null,
         buffer: t ? [t.width, t.height] : null,
         viewer: document.body.dataset.viewer || null,
         visibilita: document.visibilityState, fuoco: document.hasFocus(),
         finestra: [innerWidth, innerHeight, outerWidth, outerHeight, screenX, screenY],
         registro: reg ? reg.textContent.split('\n').filter(x => x.indexOf('audio:') !== 0).slice(-40) : [] };
"""


def _trace(s):
    """G7_TRACE=1: every call to the browser with its time (diagnosis D-011)."""
    if os.environ.get("G7_TRACE") != "1" or getattr(s.g, "_traced", False):
        return
    s.g._traced = True
    for name in ("js", "snapshot_canvas"):
        real = getattr(s.g, name)

        def wrapped(*a, _v=real, _n=name):
            t0 = time.time()
            try:
                r = _v(*a)
                outcome = "ok"
                return r
            except Exception as e:               # noqa: BLE001
                outcome = "EXCEPTION %s" % str(e)[:80]
                raise
            finally:
                print("   ⏱ %s %s %.2f s %s · %s" % (time.strftime("%H:%M:%S"), _n,
                      time.time() - t0, outcome, (str(a[0])[:50] if a else "")), flush=True)
        setattr(s.g, name, wrapped)


def session_with_scene(s, reg=None, photo_cap=None):
    sign = reg.lines() if reg else None
    _trace(s)
    # ⛔⭐ D-011, the cause (25 Sep 2026, measured with G7_TRACE=1): on XFCE the
    #    background is BLACK and in 4K the pixel judge calls it «degenerate» ⇒
    #    `Test.first_frame()` photographs for the WHOLE cap (45 s) and only
    #    at the end `desktop_dark_but_alive` saves it.  With the inactivity
    #    clock shortened to 25 s, during those 45 s without a gesture the
    #    server says farewell (0x02, rightly), the page goes back to the form (canvas 16x16,
    #    display:none) and the next photo fails: the BLOCKED was the BENCH's.
    #    ⇒ In the short-clock phases the first frame is looked at with a
    #    cap shorter than the clock (`photo_cap`), and the click arrives at once.
    old = s.o.cap_s
    if photo_cap:
        s.o.cap_s = min(old, photo_cap)
    try:
        ok, m = F019.enter_with_ear(s)
    finally:
        s.o.cap_s = old
    # ⚠ D-011, second reading (25 Sep 2026): on XFCE the photo of the first
    #   frame ~1 s after entering fails (Firefox: TakeScreenshot
    #   «Failure»; Chrome: canvas of area 0) — labwc's output is born 1280x720 and
    #   resizes AFTER the birth.  The FAREWELL 0x02 seen in the page was
    #   a CONSEQUENCE (the bench, having given up, touched nothing more for 25 s).
    #   ⇒ The canvas is looked at again for 15 s before giving up.
    retries = 0
    if not ok:
        try:
            g0 = s.g.js(JS_GEO)
            g0.pop("log", None)
        except Exception as e:                   # noqa: BLE001
            g0 = str(e)[:150]
        print("   ⚠ first frame not observable, the page AT ONCE: %s · %s"
              % (g0, str(G7.page(s.g).get("outcome"))[:100]), flush=True)
    while not ok and "could not look at the" in m and retries < 5:
        retries += 1
        time.sleep(3)
        e, m2, st = s.pr.first_frame()
        e, m2 = S.C20V.desktop_dark_but_alive(e, m2, st)
        ok, m = (e == S.GREEN), "the first frame (retry %d): %s" % (retries, m2)
    if not ok:
        # ⛔ D-011 (25 Sep 2026): here the round said only «the canvas has no visible
        #    area» and the evidence of why vanished with the server restart.
        #    ⇒ Before giving up we photograph the STATE OF THE PAGE (what it
        #    says, whether it is still dressed as a desktop, its log) and the lines
        #    of the server for this tenant, and the page's sentence enters the
        #    reason of the BLOCKED.
        time.sleep(1)
        page_map = G7.page(s.g)
        try:
            geo = s.g.js(JS_GEO)
        except Exception as e:                   # noqa: BLE001
            geo = {"error": str(e)[:200]}
        page_map["geometria"] = geo
        s.save_text("pagina-ingresso-fallito.txt",
                      "\n".join("%s: %s" % kv for kv in page_map.items()))
        print("   ⚠ login failed, the page: %s" % geo, flush=True)
        if reg is not None and sign is not None:
            s.save_text("server-ingresso-fallito.txt", reg.da(sign, s.chi))
        s.save_console()
        raise S.Blocked("you cannot get in: %s · the page: outcome «%s», dressed=%s, form=%s"
                         % (m, (page_map.get("outcome") or "")[:120], page_map.get("vestita"),
                            page_map.get("modulo_visibile")))
    F019.click_canvas(s)                 # ⭐ the FIRST gesture: the abandonment clock starts
    t_gesture = time.time()
    pid, t = G7.launch_scene(s)
    if not pid:
        raise S.Blocked("the scene does not start: " + t)
    vista, t = G7.wait_scene(s, S)
    if not vista:
        raise S.Blocked(t)
    return pid, t_gesture


# ─────────────────────────────────────────────────────────────────────────────
def phase_silence(o, E, reg):
    with S.Session(o, "022", E) as s:
        pid, _t = session_with_scene(s, reg)
        sign = reg.lines()
        n_stopped = G7.stop_browser(s.g)
        t0 = time.time()
        try:
            shape, line, after = reg.wait_until(sign, DETACH_MARKS, s.chi,
                                            cap=SILENCE_S + 5, step=1.0)
            living = G7.tenant_processes(o.box, s.chi)
        finally:
            G7.resume_browser(s.g)
        print("   F-022: %d browser processes stopped · detach: %s after %.0f s"
              % (len(n_stopped), shape, after), flush=True)
        time.sleep(2)
        ok_r, come, mr = F019.reenter(s, 40)
        ps1 = G7.tenant_processes(o.box, s.chi)
        ev = [s.save_text("server-f022.txt", reg.da(sign, s.chi)), s.save_console()]
        expected = ("browser stopped ⇒ detached within %d s (line dead-line/DETACHED/slot "
                  "LEFT), session alive, you come back in with the previous programs" % SILENCE_S)
        oss = ("detach: %s · programs alive during: %s · re-entry %s: %s (%s) · previous scene "
               "alive after: %s" % ((line or "NONE")[:180], pid in living, come,
                                   "succeeded" if ok_r else "FAILED", mr[:100], pid in ps1))
        if not n_stopped:
            E.put("F-022", S.BLOCKED, "I could not stop the browser (no pid)",
                    evidence=ev)
        elif not shape:
            E.put("F-022", S.FAIL, "the client has been silent for %d s and the server does NOT detach it"
                    % (SILENCE_S + 5), expected=expected, observed=oss, evidence=ev)
        elif pid not in living or not ok_r or pid not in ps1:
            E.put("F-022", S.FAIL, "detached, but the session is not found again: " + oss,
                    expected=expected, observed=oss, evidence=ev)
        else:
            E.put("F-022", S.PASS, "detached after %.0f s by «%s», session found again"
                    % (after, shape), expected=expected, observed=oss, evidence=ev)
        if o.fault:
            # FAULT: the browser does NOT stop — the judge must say «not detached»
            mark2 = reg.lines()
            shape2, line2, after2 = reg.wait_until(mark2, DETACH_MARKS, s.chi,
                                               cap=SILENCE_S + 5, step=2.0)
            E.fault("F-022", shape2 is None,
                     "browser alive ⇒ the judge %s" % ("sees no detach in %d s (red)"
                                                      % (SILENCE_S + 5) if shape2 is None
                                                      else "sees a DETACH: " + line2[:150]))


def phase_clocks(o, E, reg, short):
    """short=True: the healthy pass (F-023, F-024); False: the FAULT (long clocks)."""
    passed = "healthy" if short else "fault"
    with S.Session(o, "022", E) as s:
        sign = reg.lines()
        # the first frame is looked at for less than the inactivity clock
        pid, t_gesture = session_with_scene(s, reg, photo_cap=max(8, INACTIVITY_S - 10))
        # — F-023 —
        shape, line, _d = reg.wait_until(sign, ["INACTIVITY"], s.chi,
                                      cap=max(1, INACTIVITY_S + MARGIN_S - (time.time() - t_gesture)),
                                      step=1.0)
        after = time.time() - t_gesture
        # the page has up to 10 s to say it (the FAREWELL arrives, then the form)
        page_map = G7.page(s.g)
        for _ in range(10):
            if not shape or G7.page_says(page_map):
                break
            time.sleep(1)
            page_map = G7.page(s.g)
        living = G7.tenant_processes(o.box, s.chi)
        said = G7.page_says(page_map)
        if not short:
            E.fault("F-023", shape is None,
                     "LONG clock ⇒ the judge %s" % (
                         "sees no INACTIVITY in %d s (red)" % (INACTIVITY_S + MARGIN_S)
                         if shape is None else "sees INACTIVITY: " + line[:150]))
        else:
            ok_r, come, mr = (False, "", "not attempted")
            if shape:
                # you come back in ONLY with user and password: the page must not have
                # reconnected by itself
                da_se = bool(page_map.get("session")) and page_map.get("vestita") == "on" \
                    and not page_map.get("modulo_visibile")
                ok_r, come, mr = F019.reenter(s, 40)
            ps1 = G7.tenant_processes(o.box, s.chi)
            ev = [s.save_text("server-f023.txt", reg.da(sign, s.chi)),
                  s.save_text("pagina-f023.txt", "\n".join("%s: %s" % kv for kv in page_map.items()))]
            expected = ("one click, then nothing ⇒ between %d and %d s FAREWELL 0x02 (INACTIVITY line), the "
                      "page says it and goes back to the form, the programs stay, you come back in with "
                      "user and password" % (INACTIVITY_S, INACTIVITY_S + MARGIN_S))
            oss = ("line: %s · %.0f s after the click · page: outcome «%s» form %s dressed %s · "
                   "scene alive %s · re-entry %s: %s · scene alive after %s"
                   % ((line or "NONE")[:120], after, (page_map.get("outcome") or "")[:90],
                      page_map.get("modulo_visibile"), page_map.get("vestita"), pid in living, come,
                      "succeeded" if ok_r else mr[:80], pid in ps1))
            if not shape:
                E.put("F-023", S.FAIL, "no INACTIVITY within %d s of the last gesture"
                        % (INACTIVITY_S + MARGIN_S), expected=expected, observed=oss, evidence=ev)
            elif not said:
                E.put("F-023", S.FAIL, "detached for inactivity, but the page does not say it: "
                        + oss, expected=expected, observed=oss, evidence=ev)
            elif pid not in living or not ok_r or pid not in ps1:
                E.put("F-023", S.FAIL, "after the inactivity the session is not found again: " + oss,
                        expected=expected, observed=oss, evidence=ev)
            elif da_se:
                E.put("F-023", S.FAIL, "the page reconnected by itself (it should not have)",
                        expected=expected, observed=oss, evidence=ev)
            else:
                E.put("F-023", S.PASS, "detached at %.0f s, page at the form with «%s», back in "
                        "with the password, scene found again" % (after, (page_map.get("outcome") or "")[:60]),
                        expected=expected, observed=oss, evidence=ev)
        # — F-024 — no gesture since the click: the abandonment
        stays = ABANDON_S + MARGIN_S - (time.time() - t_gesture)
        shape4, line4, _d = reg.wait_until(sign, ["ABANDONMENT"], s.chi,
                                        cap=max(1, stays), step=2.0)
        after4 = time.time() - t_gesture
        time.sleep(4)
        ps4 = {}
        for _ in range(8):                        # the closing is not instantaneous
            ps4 = G7.tenant_processes(o.box, s.chi)
            if pid not in ps4 and not (shape4 and ps4):
                break
            time.sleep(2)
        if not short:
            red = shape4 is None and pid in ps4
            E.fault("F-024", red,
                     "LONG clock ⇒ the judge %s" % (
                         "sees no ABANDONMENT in %d s and the scene is alive (red)"
                         % (ABANDON_S + MARGIN_S) if red
                         else "sees an ABANDONMENT (%s) or the scene gone (%s)"
                         % ((line4 or "")[:100], pid not in ps4)))
            return
        ev = [s.save_text("server-f024.txt", reg.da(sign, s.chi)),
              s.save_text("processi-f024.txt", "\n".join("%d %s" % kv for kv in sorted(ps4.items())))]
        expected = ("no gesture since the click ⇒ within %d s ABANDONMENT line and the session closes "
                  "with its programs (the tenant's processes gone)" % (ABANDON_S + MARGIN_S))
        oss = ("line: %s · %.0f s after the click · scene alive %s · tenant's processes left "
               "%d: %s" % ((line4 or "NONE")[:120], after4, pid in ps4, len(ps4),
                           ", ".join(sorted(set(ps4.values())))[:200]))
        if not shape4:
            E.put("F-024", S.FAIL, "no ABANDONMENT within %d s of the last gesture"
                    % (ABANDON_S + MARGIN_S), expected=expected, observed=oss, evidence=ev)
        elif pid in ps4 or _leftovers(s):
            oss += " · non-exempt (F-021's rule): %s" % ", ".join(_leftovers(s) or [])[:200]
            E.put("F-024", S.FAIL, "ABANDONMENT written, but processes of the session remain: "
                    + oss, expected=expected, observed=oss, evidence=ev)
        else:
            E.put("F-024", S.PASS, "abandonment at %.0f s after the click, no tenant process "
                    "left" % after4, expected=expected, observed=oss, evidence=ev)


def _leftovers(s):
    """⭐ The tenant's processes that must NOT remain, with the same rule
    as F-021 (control group): the `remotix` child stays by design (the
    re-entry is born in it) and systemd's user manager with its services
    (dbus, pipewire, wireplumber) lives as long as the child's logind session.
    `[M]` 25 Sep 2026, LXQt: exactly those remained ⇒ a BENCH FAIL."""
    import importlib.util as _iu
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "15-f021-esci.py")
    sp = _iu.spec_from_file_location("f021", f)
    m = _iu.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m.leftovers(m.processes(s))


def body(o, E):
    if not o.port:
        o.port = G7.PORTS_G7[o.box]
        o.url = "https://%s:%d/" % (o.host, o.port)
    if o.port != G7.PORTS_G7[o.box]:
        raise S.Blocked("port %d is not our server's (%d)"
                         % (o.port, G7.PORTS_G7[o.box]))
    before_8511 = F019.healthy_8511(o)
    reg = G7.Log(o.box)
    try:
        print("   %s" % F019.server_ready(o), flush=True)
        try:
            phase_silence(o, E, reg)
        except S.Blocked as b:
            E.blocked(["F-022"], str(b))
            if o.fault:
                E.blocked(["F-022"], str(b), passed="fault")
        turn_on(o, "--inactivity-s", str(INACTIVITY_S), "--abandon-s", str(ABANDON_S))
        phase_clocks(o, E, reg, short=True)
        if o.fault:
            turn_on(o)                                # the LONG ones: the defaults
            try:
                phase_clocks(o, E, reg, short=False)
            except S.Blocked as b:
                E.blocked(["F-023", "F-024"], str(b), passed="fault")
    finally:
        idle, abandoned, _r = G7.clocks_in_effect(o.box)
        if (idle, abandoned) != (1800, 3600):
            G7.server("start", o.box)           # left with the defaults
        after_8511 = F019.healthy_8511(o)
        print("   851x server before «%s» after «%s»%s" % (
            before_8511, after_8511, "" if before_8511 == after_8511 else "  ⛔ CHANGED"), flush=True)


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify))
