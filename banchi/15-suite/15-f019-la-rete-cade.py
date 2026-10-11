#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f019 — F-019 NETWORK LOSS AND RE-ENTRY · paths P-B and P-D

    python3 15-f019-la-rete-cade.py --box gnome --browser firefox --fault --port 8611

⛔ A SERVER OF ITS OWN: it runs against the box's SECOND product server
   (`15-g7-server.sh`, ports 8611-8614, DEFAULT clocks) — the line that
   drops is simulated with nftables and on the 851x everybody would see it.

⛔ THE SIMULATION, declared (decision taken for the suite): the line dies
   ON THE SERVER'S NETWORK — an nftables table of ours (`inet remotix_g7_<port>`)
   drops ALL the UDP of our server's port (QUIC/WebTransport), in both
   directions, for DROP_S seconds; then it is removed (always: even if the test falls over).
   ⚠ It is not the real path from the tablet (Wi-Fi, `wondershaper`): browser and
   server are on the same machine, and the HTTPS page (TCP) stays reachable.

THE REAL EXPECTATION, read in the code (not in the intentions):
  · the SERVER declares the line dead after 10 s without a packet
    (`--dead-line-silence-s`, default 10: `webtransport.c`
    `dead_line_judge`, line `dead-line … cause=silence`), closes the
    connection and FREES THE SLOT; the graphical session stays (I4);
  · re-entry is BY HAND (the user's decision of 23 Aug 2026, `main.c`
    `--no-dead-line`: «the wire drops and you come back in by hand»): the page does NOT
    reconnect by itself — there is no code that does it;
  · the PAGE must SAY IT (SPECIFICHE §8.2 and §3.2 of the page: «a mute wait
    is a fault»; `back_to_form()` for every farewell): a visible sentence or the
    form back in view.  ⚠ In today's code the closing of the transport
    WITHOUT `FAREWELL` (that of the dead line: the `FAREWELL` cannot arrive on
    a line that does not carry) ends up in `nota()` — the hidden log — and that's all.

F-019  expected: the server writes `dead-line` for the tenant; the page says it
       within OBSERVE_S of the line coming back (with a mouse movement, as
       whoever is in front would do); we come back in (from the form if it is there, otherwise
       by reloading: it is «by hand»); and the programs
       of the session are the SAME (pid).  ⚠ The sentence
       «resumed session» is not demanded: `rcp.c` ALWAYS sends `1 = NEW` in `SESSION`
       (line ~3051), so the page says «new session» even when it
       finds it again — it is written in the observed, and the judgment comes from the pids.
P-B    creation → activity → loss → re-entry → activity: after the re-entry the
       moving scene (weston-simple-egl) moves in the PHOTOS, and it is the
       same process as before.
P-D    creation → video/audio → loss → re-entry: with the scene AND a real tone
       (pw-play 440 Hz on the «remotix» sink) on during the drop, after the
       re-entry the photo moves AND the sound the page PLAYS is not silence
       (RMS of the samples passed to `AudioBufferSourceNode.start`, not a counter).

FAULT (second drop, same session): during the dead line the scene and the
       tone are KILLED (the state is lost) and the re-entry is attempted with the line
       STILL dead ⇒ F-019 must see «no getting back in»; then the line comes back, we
       come back in, and P-B must see the scene still/gone and P-D the silence.
"""
import importlib.util as _iu
import os
import signal
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

_s = _iu.spec_from_file_location("g7comune", os.path.join(S.HERE, "15-g7-comune.py"))
G7 = _iu.module_from_spec(_s)
_s.loader.exec_module(G7)
G7.local_box(S)

FUNCTIONS = ("F-019", "P-B", "P-D")
SERVER = "15-g7-server.sh"
DROP_S = 20          # the dead line; the server declares it at 10 s
OBSERVE_S = 60         # after the line comes back: how long to wait for the page to say it
CAP_REENTRY_S = 40


def extra(a):
    a.add_argument("--drop-s", type=int, default=DROP_S)
    a.add_argument("--observe-s", type=int, default=OBSERVE_S)


def certify():
    ok = True
    lm = G7.DeadLine(8611)
    r = lm.rules()
    for expected in ("table inet remotix_g7_8611", "udp dport 8611 counter drop",
                   "udp sport 8611 counter drop", "hook input", "hook output"):
        if expected not in r:
            print("⛔ the rule does not have «%s»" % expected)
            ok = False
    try:
        G7.DeadLine(8511)
        print("⛔ the dead line accepts 8511 (everybody's)")
        ok = False
    except AssertionError:
        print("⭐ the dead line refuses the ports that are not ours")
    cases = [({"esito_visibile": True, "outcome_class": "bad", "vestita": "on"}, True),
            ({"esito_visibile": False, "modulo_visibile": True, "vestita": None}, True),
            ({"esito_visibile": False, "modulo_visibile": False, "vestita": "on"}, False),
            ({"esito_visibile": True, "outcome_class": "good", "vestita": "on"}, False),
            ({"error": "x"}, None)]
    for st, expect in cases:
        v = G7.page_says(st)
        if v is not expect:
            print("⛔ page_says(%s) = %s, expected %s" % (st, v, expect))
            ok = False
    print("%s nft rules and page judge" % ("⭐" if ok else "⛔"))
    return 0 if ok else 1


# ─────────────────────────────────────────────────────────────────────────────
def server_ready(o):
    """Our server on and with the DEFAULT clocks; if not, it starts it."""
    idle, abandoned, line = G7.clocks_in_effect(o.box)
    c, t = G7.inside(o.box, "systemctl is-active rete15-g7", 30)
    if (t or "").strip() == "active" and idle == 1800 and abandoned == 3600:
        return "our server already on, default clocks"
    ok, t = G7.server("start", o.box)
    if not ok:
        raise S.Blocked("our server does not start: %s" % t[-300:])
    return t.splitlines()[0] if t else "on"


def healthy_8511(o):
    """⛔ Everybody's server (851x) must stay the previous one: pid and active."""
    c, t = G7.inside(o.box, "systemctl is-active rete11-server; "
                     "systemctl show -p MainPID --value rete11-server", 30)
    return " ".join((t or "").split())


def click_canvas(s):
    """A click at the centre of the canvas: it is the user's gesture that unblocks
    the browser's audio (autoplay) — without it, the AudioContext stays suspended."""
    st = s.state()
    x, y = s.pr.center(st, 0.5, 0.5)
    s.g.click(x, y)
    time.sleep(0.5)
    return x, y


def enter_with_ear(s):
    ok, m = s.pr.do_open()
    if not ok:
        return False, "the page does not open: " + m
    G7.ear(s.g)
    ok, m = s.enter(do_open=False)
    return ok, m


def reenter(s, cap):
    """The re-entry «by hand»: from the form if the page put it back in view,
    otherwise by reloading (what whoever looks at a frozen desktop would do).
    Returns (ok, how, outcome)."""
    st = G7.page(s.g)
    come = "from the form back in view"
    if not (st.get("modulo_visibile") and not st.get("vestita")):
        come = "by reloading the page (the form was not there)"
        ok, m = s.pr.do_open()
        if not ok:
            return False, come, "the page does not reopen: " + m
    G7.ear(s.g)
    old = s.o.cap_s
    s.o.cap_s = cap
    try:
        e, m, st2 = s.pr.enter(s.password)
        # ⚠ `[M]` 24 Sep 2026, server with load ~50: the server's loop falls
        #   behind by up to 13 s and the HELLO expires (0x0D «timed out during the
        #   handshake»).  Whoever is in front retries: we retry ONCE, and
        #   it is written.
        if e != S.GREEN and "handshake" in (m or ""):
            come += " (retried once after «%s»)" % m[:60]
            ok, m0 = s.pr.do_open()
            G7.ear(s.g)
            e, m, st2 = s.pr.enter(s.password)
    finally:
        s.o.cap_s = old
    if e != S.GREEN:
        return False, come, m
    e2, m2, _ = s.pr.first_frame()
    e2, m2 = S.C20V.desktop_dark_but_alive(e2, m2, _)
    return e2 == S.GREEN, come, "%s · %s" % (m, m2)


def drop(s, o, reg, lm, observe_s, remove=True, during=None):
    """The line dies for `o.drop_s`; `during()` is called halfway.
    Returns a dictionary with the facts seen."""
    f = {"linea_morta": None, "detto": None, "detto_dopo_s": None, "discarded": 0}
    sign = reg.lines()
    lm.put()
    t0 = time.time()
    try:
        called = False
        while time.time() - t0 < o.drop_s:
            if during and not called and time.time() - t0 > o.drop_s / 3:
                during()
                called = True
            st = G7.page(s.g)
            if f["detto"] is None and G7.page_says(st):
                f["detto"], f["detto_dopo_s"] = st, time.time() - t0
            time.sleep(2)
        f["discarded"] = lm.counted()
        shape, line, _ = reg.wait_until(sign, ["dead-line"], s.chi, cap=2)
        f["linea_morta"] = line
    finally:
        if remove:
            f["tolta"] = lm.remove()
    if not remove:
        return f
    # the line came back: whoever is in front moves the mouse and looks
    t1 = time.time()
    moved = 0
    while time.time() - t1 < observe_s and f["detto"] is None:
        try:
            st0 = s.state()
            x, y = s.pr.center(st0, 0.3 + 0.1 * (moved % 4), 0.5)
            s.g.move_to(x, y)
            moved += 1
        except Exception:                        # noqa: BLE001
            pass
        st = G7.page(s.g)
        if G7.page_says(st):
            f["detto"], f["detto_dopo_s"] = st, time.time() - t0
            break
        time.sleep(3)
    f["ultima_pagina"] = G7.page(s.g)
    f["mossi"] = moved
    if f["linea_morta"] is None:
        _f, line, _ = reg.wait_until(sign, ["dead-line"], s.chi, cap=2)
        f["linea_morta"] = line
    f["segno"] = sign
    return f


def body(o, E):
    if not o.port:
        o.port = G7.PORTS_G7[o.box]
        o.url = "https://%s:%d/" % (o.host, o.port)
    if o.port != G7.PORTS_G7[o.box]:
            raise S.Blocked("port %d is not our server's (%d)"
                         % (o.port, G7.PORTS_G7[o.box]))
    print("   %s" % server_ready(o), flush=True)
    before_8511 = healthy_8511(o)
    reg = G7.Log(o.box)
    lm = G7.DeadLine(o.port)
    lm.remove()
    ev_srv = []
    try:
        with S.Session(o, "019", E) as s:
            mark0 = reg.lines()
            ok, m = enter_with_ear(s)
            if not ok:
                raise S.Blocked("you cannot get in even with a healthy line: " + m)
            print("   in: %s" % m, flush=True)
            click_canvas(s)
            scene_pid, t = G7.launch_scene(s)
            print("   %s" % t, flush=True)
            if not scene_pid:
                raise S.Blocked("the scene does not start: " + t)
            c, t = G7.launch_tone(s)
            vista, t = G7.wait_scene(s, S)
            if not vista:
                raise S.Blocked("before the drop: " + t)
            time.sleep(3)
            ps0 = G7.tenant_processes(o.box, s.chi)
            tone_pid = [p for p, n in ps0.items() if n.startswith("pw-play")]
            rms0, d0 = G7.listen(s.g, 3)
            move0, dm0, ev0 = G7.scene_moves(s, "before")
            print("   before: scene %s (%s) · sound RMS %s %s · %d processes"
                  % (move0, dm0, rms0, d0, len(ps0)), flush=True)

            # ═══ THE HEALTHY DROP ═════════════════════════════════════════
            f = drop(s, o, reg, lm, o.observe_s)
            print("   drop: %d packets dropped · dead-line: %s · said: %s"
                  % (f["discarded"], bool(f["linea_morta"]),
                     ("after %.0f s" % f["detto_dopo_s"]) if f["detto"] else "NO"), flush=True)
            if f["discarded"] == 0:
                raise S.Blocked("the nft rule dropped nothing: the line did not die")
            ok_r, come, mr = reenter(s, CAP_REENTRY_S)
            print("   re-entry %s: %s — %s" % (come, ok_r, mr[:200]), flush=True)
            if ok_r:
                click_canvas(s)
            time.sleep(4)
            ps1 = G7.tenant_processes(o.box, s.chi)
            move1, dm1, ev1 = G7.scene_moves(s, "after")
            rms1, d1 = G7.listen(s.g, 3)
            ev_srv.append(s.save_text("server-f019-sana.txt", reg.da(mark0, s.chi)))
            ev_page = s.save_text("pagina-dopo-caduta.txt", "\n".join(
                "%s: %s" % (k, v) for k, v in (f.get("ultima_pagina") or {}).items()))
            # ⚠ pw-play's pid changes at every turn of the loop (a 5 s file):
            #   the session's state is judged on the scene's pid.
            same = scene_pid in ps1
            resumed = "resumed" in mr
            ev = ev0 + ev1 + ev_srv + [ev_page, s.save_console()]

            # F-019
            observed = ("dead-line from the server: %s · the page: %s · re-entry %s: %s · "
                         "the page writes «resumed session»: %s (⚠ rcp.c always sends "
                         "1=NEW) · previous programs alive: %s"
                         % ("yes" if f["linea_morta"] else "NO",
                            ("it says so after %.0f s: «%s»" % (f["detto_dopo_s"],
                                                           (f["detto"].get("outcome") or "")[:100]))
                            if f["detto"] else
                            ("it does NOT say so: %d s after the line came back (and %d mouse "
                             "movements) the page is still dressed as a desktop, frozen, outcome "
                             "«%s»" % (o.observe_s, f.get("mossi", 0),
                                      (f["ultima_pagina"].get("outcome") or "")[:80])),
                            come, "succeeded" if ok_r else "FAILED", resumed, same))
            expected = ("dead-line in the log; the page says it (sentence or form) within "
                      "%d s of the return; you come back in by hand; «resumed session» with the "
                      "previous programs" % o.observe_s)
            if not f["linea_morta"]:
                E.put("F-019", S.FAIL, "the server did not declare the line dead in %d s"
                        % o.drop_s, expected=expected, observed=observed, evidence=ev)
            elif not ok_r or not same:
                E.put("F-019", S.FAIL, "after the drop the session is not found again: " + observed,
                        expected=expected, observed=observed, evidence=ev)
            elif not f["detto"]:
                E.put("F-019", S.FAIL, "the wire drops and the page does NOT say it: frozen desktop "
                        "without a word (you come back in only by reloading on your own initiative)",
                        expected=expected, observed=observed, evidence=ev)
            else:
                E.put("F-019", S.PASS, observed, expected=expected, observed=observed,
                        evidence=ev)

            # P-B
            expected_b = "after the re-entry the scene moves in the photos, same process as before"
            if not ok_r:
                E.put("P-B", S.FAIL, "no getting back in: " + mr[:200], expected=expected_b,
                        observed=mr[:200], evidence=ev)
            elif move1 is None:
                E.put("P-B", S.BLOCKED, "photos not judgeable: " + dm1, evidence=ev)
            elif move1 and scene_pid in ps1:
                E.put("P-B", S.PASS, "scene alive after the re-entry (%s), pid %d" % (dm1, scene_pid),
                        expected=expected_b, observed=dm1, evidence=ev)
            else:
                E.put("P-B", S.FAIL, "after the re-entry the scene is still or gone (%s, pid alive %s)"
                        % (dm1, scene_pid in ps1), expected=expected_b, observed=dm1, evidence=ev)

            # P-D
            expected_d = "after the re-entry moving photos AND sound played not silence (RMS > %.2f)" \
                % G7.RMS_THRESHOLD
            if rms0 is None or rms0 < G7.RMS_THRESHOLD:
                E.put("P-D", S.BLOCKED, "the sound was not arriving even BEFORE the drop "
                        "(RMS %s, %s): I have no «before» to find again" % (rms0, d0), evidence=ev)
            elif not ok_r:
                E.put("P-D", S.FAIL, "no getting back in: " + mr[:200], expected=expected_d, evidence=ev)
            elif move1 and rms1 is not None and rms1 >= G7.RMS_THRESHOLD:
                E.put("P-D", S.PASS, "after the re-entry video alive (%s) and sound RMS %.3f (before %.3f)"
                        % (dm1, rms1, rms0), expected=expected_d,
                        observed="RMS %.3f · %s" % (rms1, d1), evidence=ev)
            else:
                E.put("P-D", S.FAIL, "after the re-entry: video %s (%s), sound RMS %s (%s)"
                        % (move1, dm1, rms1, d1), expected=expected_d, evidence=ev)

            if not o.fault:
                return
            # ═══ THE FAULT: the state is lost AND the line stays dead ═════
            if not ok_r:
                E.fault("F-019", None, "the healthy pass did not come back in: nothing to break")
                E.fault("P-B", None, "same")
                E.fault("P-D", None, "same")
                return
            victims = [scene_pid] + tone_pid

            def kill():
                G7.inside(o.box, "pkill -KILL -u %s -f 'pw-play|weston-simple-egl'; "
                          "kill -KILL %s 2>/dev/null; true"
                          % (s.chi, " ".join(str(p) for p in victims)), 30)
            f2 = drop(s, o, reg, lm, 0, remove=False, during=kill)
            try:
                ok_g, come_g, mg = reenter(s, 30)          # line STILL dead
            finally:
                lm.remove()
            E.fault("F-019", not ok_g, "re-entry with the line still dead ⇒ %s (%s)"
                     % ("NO getting back in: " + mg[:120] if not ok_g else "BACK IN?!", come_g))
            ok_r2, come2, mr2 = reenter(s, CAP_REENTRY_S)
            if not ok_r2:
                E.fault("P-B", None, "after the fault you can no longer get back in: " + mr2[:150])
                E.fault("P-D", None, "same")
                return
            click_canvas(s)
            time.sleep(4)
            ps2 = G7.tenant_processes(o.box, s.chi)
            move2, dm2, _e = G7.scene_moves(s, "fault")
            rms2, d2 = G7.listen(s.g, 3)
            s.save_text("server-f019-guasto.txt", reg.da(f2.get("segno") or mark0, s.chi))
            alive = scene_pid in ps2
            pb_red = not (move2 and alive)
            E.fault("P-B", pb_red if move2 is not None else None,
                     "scene killed during the drop ⇒ P-B's judge says %s (%s, pid alive %s)"
                     % ("red" if pb_red else "GREEN", dm2, alive))
            pd_red = not (move2 and rms2 is not None and rms2 >= G7.RMS_THRESHOLD)
            E.fault("P-D", pd_red, "scene and tone killed ⇒ P-D's judge says %s "
                     "(video %s, RMS %s)" % ("red" if pd_red else "GREEN", move2, rms2))
    finally:
        removed = lm.remove()
        after_8511 = healthy_8511(o)
        print("   nft rule removed: %s · 851x server before «%s» after «%s»%s"
              % (removed, before_8511, after_8511,
                 "" if before_8511 == after_8511 else "  ⛔ CHANGED"), flush=True)


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify, extra=extra))
