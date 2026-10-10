#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f012b — F-012B AUDIO AFTER «EXIT»: you exit, you come back in at once, and a PulseAudio
           program is still heard in the browser

    python3 15-f012b-audio-dopo-esci.py --container_box gnome --browser firefox [--fault]

THE DEFECT IT LOOKS AT (the user's report, 2 Oct 2026, GNOME on the Radeon,
Firefox).  After «Exit» and a new login — the systemd USER MANAGER is
still alive (it stays as long as the logind session of the `remotix` child exists) — the
previous session stops pipewire, wireplumber and filter-chain but NOT
`pipewire-pulse`; the new session starts a new pipewire, and the old
`pipewire-pulse` stays attached to nothing ⇒ the programs that speak
PulseAudio (firefox-esr inside the session) are mute, and our sink captures
only digital silence.  The cure is in `src/sessione.c` («THE `pipewire-pulse`
LEFT OVER FROM THE PREVIOUS SESSION»).

⛔ WHY NOT `pw-play` (F-012's): it is a NATIVE PipeWire client, it talks
   to the new pipewire and is heard even with the defect.  Here a REAL
   PulseAudio client plays: `libpulse-simple` (the same library the
   PulseAudio programs use) called from python3 with ctypes — in the four
   boxes there is no `paplay` (pulseaudio-utils is not installed) and ffmpeg is
   compiled without the pulse output.  The tone is F-012's (440 Hz,
   amplitude 0.5, DEFAULT sink, no target).

THE SCENE (one tenant, c15912u<n>):
  1  login with F-012's ear (`15-g4-comune.py`), the pulse client
     plays ⇒ the tone MUST arrive (if not, the test has no base: BLOCKED);
  2  «Exit» with F-021's gesture (the method the menu entry reaches):
     the product declares the end, the page goes back to the form;
  3  AT ONCE a new login (page reloaded, ear put back): the
     log says «I AM MAKING IT BE BORN» (new session) and the user manager
     is the SAME as before (same pid of `systemd --user`) — otherwise the
     scene of the defect is not there and I have looked at nothing (BLOCKED);
  4  the pulse client plays again ⇒ the tone MUST reach the browser.

F-012B  expected: at point 4, F-012's judge (>= 80 % of the samples
        audible, peak at 440 ± 12 Hz over 6 s) says PASS, AND `pipewire-pulse`
        is not older than `pipewire` (start read from /proc/<pid>/stat,
        tolerance 2 s; pid and start time of pipewire, pipewire-pulse,
        wireplumber and of the user manager are written in the evidence at the
        four moments: plays, after «Exit», after the re-entry, plays again).

FAULT (same session, after the healthy pass): at point 4 NOTHING plays
  g1  the pulse client killed ⇒ the same reading of the ear MUST say FAIL;
  g2  the real samples of point 4 against a WRONG EXPECTATION (660 Hz) ⇒ FAIL;
  g3  the pid rule on a FAKE photo of the defect (pulse born before
      pipewire) ⇒ FAIL.
  Seen = all three red.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

F12 = S._load("f012", os.path.join(S.HERE, "15-f012-audio.py"))
F21 = S._load("f021", os.path.join(S.HERE, "15-f021-esci.py"))
G4 = F12.G4

FUNCTIONS = ("F-012B",)
CLIENT = "c15pulse.py"
CLIENT_MARKER = "c15pulse"
TOL_START_S = 2.0
# the units of the user manager that are photographed; `systemd` in the init.scope
# is the manager itself
UNIT = ("pipewire.service", "pipewire-pulse.service", "wireplumber.service",
         "filter-chain.service")

# ⭐ The PulseAudio client: libpulse-simple, the tone in a loop until it is
#   killed.  If the pulse server does not answer (or the write falls over) it says so and
#   retries, like a real player.
CLIENT_PY = r'''
import ctypes, sys, time, wave
pa = ctypes.CDLL("libpulse-simple.so.0")
class Spec(ctypes.Structure):
    _fields_ = [("format", ctypes.c_int), ("rate", ctypes.c_uint32), ("channels", ctypes.c_uint8)]
pa.pa_simple_new.restype = ctypes.c_void_p
pa.pa_simple_new.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
                             ctypes.c_char_p, ctypes.POINTER(Spec), ctypes.c_void_p,
                             ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
pa.pa_simple_write.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t,
                               ctypes.POINTER(ctypes.c_int)]
pa.pa_simple_free.argtypes = [ctypes.c_void_p]
w = wave.open(sys.argv[1])
assert w.getsampwidth() == 2
spec = Spec(3, w.getframerate(), w.getnchannels())          # PA_SAMPLE_S16LE
data_v = w.readframes(w.getnframes())
piece = w.getframerate() * w.getnchannels() * 2 // 10       # 100 ms
while True:
    err = ctypes.c_int(0)
    h = pa.pa_simple_new(None, b"c15pulse", 1, None, b"tone 440", ctypes.byref(spec),
                         None, None, ctypes.byref(err))      # 1 = PA_STREAM_PLAYBACK
    if not h:
        print("pa_simple_new: error %d" % err.value, flush=True)
        time.sleep(1)
        continue
    print("connected to the pulse server", flush=True)
    alive = True
    while alive:
        for i in range(0, len(data_v), piece):
            b = data_v[i:i + piece]
            if pa.pa_simple_write(h, b, len(b), ctypes.byref(err)) < 0:
                print("pa_simple_write: error %d" % err.value, flush=True)
                alive = False
                break
    pa.pa_simple_free(h)
    time.sleep(1)
'''


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES — pure
# ═══════════════════════════════════════════════════════════════════════════
def read_photo(body_text):
    """The lines `@@p <comm> <pid> <start_tick> <unit>` and `@@hz <n>` ⇒
    {"hz": n, "proc": [{"comm", "pid", "inizio_s", "unit"}]} — pure."""
    hz, proc = None, []
    for r in (body_text or "").splitlines():
        p = r.split()
        if len(p) == 2 and p[0] == "@@hz" and p[1].isdigit():
            hz = int(p[1])
        elif len(p) >= 4 and p[0] == "@@p" and p[2].isdigit() and p[3].isdigit():
            proc.append({"comm": p[1], "pid": int(p[2]), "tick": int(p[3]),
                         "unit": p[4] if len(p) > 4 else ""})
    for x in proc:
        x["inizio_s"] = round(x.pop("tick") / float(hz or 100), 2)
    return {"hz": hz, "proc": proc}


def di(picture, unit):
    """The unit's process (or the manager, `unit="init.scope"`), or None.
    If there is more than one: the OLDEST (it is the one left over)."""
    v = [x for x in (picture or {}).get("proc", []) if x["unit"] == unit
         and (unit != "init.scope" or x["comm"] == "systemd")]
    return min(v, key=lambda x: x["inizio_s"]) if v else None


def summary(picture):
    pieces = []
    for u in ("init.scope",) + UNIT:
        x = di(picture, u)
        if x:
            pieces.append("%s pid %d since %.1f s" % (u.replace(".service", "").replace(
                "init.scope", "manager"), x["pid"], x["inizio_s"]))
    return ", ".join(pieces) or "(none)"


def judge_pid(before, after):
    """(outcome, reason) of the rule: pipewire-pulse not older than
    pipewire in the new session, with the user manager survived.
    `before` = photo of session 1, `after` = photo of session 2 that plays."""
    g1, g2 = di(before, "init.scope"), di(after, "init.scope")
    if not g1 or not g2:
        return S.BLOCKED, "I do not see the user manager (before %s, after %s)" % (g1, g2)
    if g1["pid"] != g2["pid"]:
        return S.BLOCKED, ("the user manager did NOT survive the exit (pid %d ⇒ %d): "
                           "the scene of the defect is not there" % (g1["pid"], g2["pid"]))
    pw, pp = di(after, "pipewire.service"), di(after, "pipewire-pulse.service")
    if not pw:
        return S.FAIL, "in the new session there is no pipewire"
    if not pp:
        return S.FAIL, "in the new session, with the pulse client playing, there is no pipewire-pulse"
    if pp["inizio_s"] < pw["inizio_s"] - TOL_START_S:
        prior = di(before, "pipewire-pulse.service")
        return S.FAIL, ("pipewire-pulse (pid %d, since %.1f s) is OLDER than pipewire "
                        "(pid %d, since %.1f s)%s" % (
                            pp["pid"], pp["inizio_s"], pw["pid"],
                            pw["inizio_s"], " — it is the one from the previous session"
                            if prior and prior["pid"] == pp["pid"] else ""))
    return S.PASS, ("manager alive (pid %d); pipewire-pulse pid %d since %.1f s, pipewire pid %d "
                    "since %.1f s" % (g2["pid"], pp["pid"], pp["inizio_s"], pw["pid"],
                                   pw["inizio_s"]))


def judge(e_tone, d_tone, e_pid, d_pid):
    """The outcome of F-012B: the tone at point 4 and the pid rule."""
    if e_pid == S.BLOCKED:
        return S.BLOCKED, d_pid
    troubles = []
    if e_tone != "PASS":
        troubles.append("after «Exit» and the re-entry the PulseAudio program is NOT heard in the "
                    "browser: %s" % d_tone)
    if e_pid != S.PASS:
        troubles.append(d_pid)
    if troubles:
        if e_tone == "BLOCKED" and e_pid == S.PASS:
            return S.BLOCKED, " · ".join(troubles)
        return S.FAIL, " · ".join(troubles)
    return S.PASS, "after «Exit» and the re-entry the tone is heard: %s · %s" % (d_tone, d_pid)


def certify():
    troubles = 0

    def p(label_name, obtained, expected_val):
        nonlocal troubles
        ok = obtained == expected_val
        troubles += not ok
        print("  %s %-62s %s (expected %s)" % ("OK " if ok else "NO ", label_name, obtained, expected_val))

    U = "user@4013.service"
    t1 = ("@@hz 100\n@@p systemd 700 1000 init.scope\n@@p pipewire 710 1100 pipewire.service\n"
          "@@p pipewire 711 1100 filter-chain.service\n"
          "@@p pipewire-pulse 712 1110 pipewire-pulse.service\n")
    before = read_photo(t1)
    p("⭐ the photo reads (4 processes, hz 100)", (before["hz"], len(before["proc"])), (100, 4))
    p("⭐ the pipewire is pipewire.service's, not filter-chain",
      di(before, "pipewire.service")["pid"], 710)
    sana = read_photo("@@hz 100\n@@p systemd 700 1000 init.scope\n"
                      "@@p pipewire 810 9000 pipewire.service\n"
                      "@@p pipewire-pulse 812 9050 pipewire-pulse.service\n")
    p("⭐ new session, pulse born after pipewire ⇒ PASS", judge_pid(before, sana)[0], S.PASS)
    defect = read_photo("@@hz 100\n@@p systemd 700 1000 init.scope\n"
                         "@@p pipewire 810 9000 pipewire.service\n"
                         "@@p pipewire-pulse 712 1110 pipewire-pulse.service\n")
    p("⛔ the pulse of the previous session stays ⇒ FAIL", judge_pid(before, defect)[0], S.FAIL)
    p("⛔ ⇒ and it says so", "previous session" in judge_pid(before, defect)[1], True)
    p("⭐ pulse born 1 s earlier (socket activation) ⇒ PASS, tolerance",
      judge_pid(before, read_photo("@@hz 100\n@@p systemd 700 1000 init.scope\n"
                                    "@@p pipewire 810 9000 pipewire.service\n"
                                    "@@p pipewire-pulse 812 8900 pipewire-pulse.service\n"))[0],
      S.PASS)
    p("⚠ manager reborn ⇒ BLOCKED (the scene is not there)",
      judge_pid(before, read_photo("@@hz 100\n@@p systemd 900 8000 init.scope\n"
                                    "@@p pipewire 810 9000 pipewire.service\n"
                                    "@@p pipewire-pulse 812 9050 pipewire-pulse.service\n"))[0],
      S.BLOCKED)
    p("⚠ photo not read ⇒ BLOCKED, never PASS", judge_pid(before, read_photo(""))[0], S.BLOCKED)
    p("⛔ pulse absent with the client playing ⇒ FAIL",
      judge_pid(before, read_photo("@@hz 100\n@@p systemd 700 1000 init.scope\n"
                                    "@@p pipewire 810 9000 pipewire.service\n"))[0], S.FAIL)
    p("⛔ a systemd not in the init.scope is not the manager",
      di(read_photo("@@p systemd 5 1 %s\n" % U), "init.scope"), None)
    p("⭐ tone PASS and pid PASS ⇒ PASS", judge("PASS", "x", S.PASS, "y")[0], S.PASS)
    p("⛔ tone FAIL (silence) ⇒ FAIL", judge("FAIL", "x", S.PASS, "y")[0], S.FAIL)
    p("⛔ tone PASS but old pulse ⇒ FAIL", judge("PASS", "x", S.FAIL, "y")[0], S.FAIL)
    p("⚠ manager reborn ⇒ BLOCKED even with the tone", judge("PASS", "x", S.BLOCKED, "y")[0],
      S.BLOCKED)
    p("⚠ few samples and pids in order ⇒ BLOCKED", judge("BLOCKED", "x", S.PASS, "y")[0],
      S.BLOCKED)
    print("⛔ %d wrong cases" % troubles if troubles else "⭐ the judges say what they must")
    return 1 if troubles else 0


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def snapshot(s):
    """Pid, start and unit of the tenant's processes that matter (pipewire,
    pipewire-pulse, wireplumber, the manager) ⇒ (photo, raw text)."""
    def una():
        c, t = s.sc.inside(
            "echo \"@@hz $(getconf CLK_TCK)\"; for p in $(pgrep -u %s); do "
            "n=$(cat /proc/$p/comm 2>/dev/null); case \"$n\" in systemd|pipewire*|wireplumber) "
            "st=$(awk '{print $22}' /proc/$p/stat 2>/dev/null); "
            "u=$(head -1 /proc/$p/cgroup 2>/dev/null | awk -F/ '{print $NF}'); "
            "echo \"@@p $n $p $st $u\";; esac; done; echo @@fine; "
            "echo \"@@ora_s $(cut -d' ' -f1 /proc/uptime)\"; "
            "ps -o pid,lstart,etimes,args -u %s | grep -E 'systemd --user|pipewire|wireplumber' "
            "| grep -v grep" % (s.chi, s.chi), 40)
        return t if "@@fine" in (t or "") else None
    t = F21._retry(una) or ""
    return read_photo(t), t


def prepare_client(s):
    h = "/home/%s/%s" % (s.chi, CLIENT)
    c, t = s.sc.inside("cat > %s <<'@@FINE@@'\n%s\n@@FINE@@\nchown %s: %s && ls -l %s"
                       % (h, CLIENT_PY, s.chi, h, h), 30)
    return c == 0, (t or "").strip()[-200:]


def plays_pulse(s):
    return s.in_session("exec python3 /home/%s/%s /home/%s/%s # %s"
                            % (s.chi, CLIENT, s.chi, F12.WAV, CLIENT_MARKER))


def silence_pulse(s):
    s.sc.inside("pkill -u %s -f '[c]15pulse'; sleep 0.3; pgrep -u %s -f '[c]15pulse' || "
                "echo quiet" % (s.chi, s.chi), 30)


def diary_client(s):
    _c, t = s.sc.inside("tail -n 20 /home/%s/.c15-exec.log 2>/dev/null" % s.chi, 30)
    return (t or "").strip()


def client_seen(s):
    """Is the pulse client seen by the session's pipewire? (diagnosis)"""
    _c, t = s.as_user("pw-cli ls Client 2>&1 | grep -c c15pulse", 30)
    return (t or "").strip()


def enter_and_listen(s, label_name, ev, note):
    """The client plays and the ear listens for WINDOW_S ⇒ (outcome, descr, numbers, r)."""
    c, t = plays_pulse(s)
    if c != 0:
        raise S.Blocked("the pulse client does not start in the session: " + (t or "")[-200:])
    if not F12.wake(s, note):
        return "FAIL", "no AudioContext in the page in 30 s", {}, {}
    time.sleep(1.0)
    e, d, num, r = F12.listen(s, F12.WINDOW_S)
    ev.append(G4.save_json(s.o, "f012b-orecchio-%s.json" % label_name, r))
    note.append("%s: client «%s», seen by pipewire: %s" % (
        label_name, diary_client(s).replace("\n", " | ")[-160:], client_seen(s)))
    return e, d, num, r


def body_el(o, E):
    sess = S.Session(o, "912", E)
    G4.robust(sess.sc)
    with sess as s:
        desktop, gesture = s.sc.exit_gesture()
        if not gesture:
            raise S.Blocked("I do not know how to say «Exit» in %s" % s.sc.container)
        print("   «Exit» (%s): %s" % (desktop, gesture), flush=True)
        ok, m = F12.enter_with_ear(s)
        if not ok:
            raise S.Blocked(m)
        ok, m = F12.prepare_tone_ffmpeg(s)
        if not ok:
            print("   ⚠ the tone with ffmpeg: %s — the bench writes it" % m, flush=True)
            ok, m = F12.prepare_tone(s)
        if not ok:
            raise S.Blocked("the tone does not get ready in the box: " + m)
        ok, m = prepare_client(s)
        if not ok:
            raise S.Blocked("the pulse client cannot be written in the box: " + m)
        sign = s.log_mark()
        ev, note, picture = [], [], {}

        def fires(label_name):
            f, t = snapshot(s)
            picture[label_name] = f
            ev.append(s.save_text("f012b-processi-%s.txt" % label_name, t))
            print("      [%s] %s" % (label_name, summary(f)), flush=True)
            return f

        # 1 ── the first session plays ──────────────────────────────────────
        e1, d1, _n1, _r1 = enter_and_listen(s, "1-prima", ev, note)
        fires("1-suona")
        print("   1 before «Exit»: %s — %s" % (e1, d1), flush=True)
        if e1 != "PASS":
            ev.append(s.save_text("server-f012b.txt", s.log_from(sign) if sign else []))
            raise S.Blocked("already BEFORE «Exit» the pulse client is not heard (%s): it is not "
                             "the scene of this test (see F-012)" % d1)
        silence_pulse(s)

        # 2 ── «Exit» like the user ──────────────────────────────────────────
        sign_exit = F21._retry(s.log_mark)
        c, t = F21.do_gesture(s, gesture)
        if c != 0:
            raise S.Blocked("the «Exit» gesture did not answer (code %s): %s" % (c, t[-200:]))
        t0 = time.time()
        ended, _r = F21.wait_finished(s, sign_exit, F21.CAP_FINISHED)
        if not ended:
            raise S.Blocked("after «Exit» the product does not declare the session ended in %.0f s"
                             % F21.CAP_FINISHED)
        module, sentence, _read = F21.read_page(s, 30)
        exit = "ended («%s») after %.1f s, page at the form=%s «%s»" % (
            ended, time.time() - t0, module, sentence[:60])
        print("   2 %s" % exit, flush=True)
        fires("2-dopo-esci")

        # 3 ── inside again AT ONCE ─────────────────────────────────────────
        sign_reentry = F21._retry(s.log_mark)
        t1 = time.time()
        ok, m = F12.enter_with_ear(s)
        if not ok:
            raise S.Blocked("the re-entry after «Exit» does not succeed: %s" % m)
        slice = F21.logbook(s, sign_reentry) or []
        new_one = any("I AM MAKING IT BE BORN" in r and F21.e_di(r, s.chi) for r in slice)
        reentry = "re-entry %.1f s after the form, session %s" % (
            t1 - t0, "NEW («I AM MAKING IT BE BORN»)" if new_one else "NOT new (resumed?)")
        print("   3 %s" % reentry, flush=True)
        fires("3-dopo-rientro")
        if not new_one:
            ev.append(s.save_text("server-f012b.txt", s.log_from(sign) if sign else []))
            raise S.Blocked("the re-entry did not make a new session be born: the scene "
                             "of the defect is not there (%s)" % reentry)

        # 4 ── the pulse client plays again ─────────────────────────────────
        e4, d4, num4, r4 = enter_and_listen(s, "4-dopo-esci", ev, note)
        samples4 = r4.get("samples") or []
        after = fires("4-risuona")
        e_pid, d_pid = judge_pid(picture["1-suona"], after)
        label_name, _v, _m, tv = F12.volume(s)
        outcome, reason_text = judge(e4, d4, e_pid, d_pid)
        ev.append(s.save_text("server-f012b.txt", s.log_from(sign) if sign else []))
        ev.append(s.save_console())
        _png, dove = s.picture("f012b-fine")
        if dove:
            ev.append(dove)
        oss = " · ".join([
            "1: %s" % d1, "2: %s" % exit, "3: %s" % reentry, "4: %s" % d4,
            "default sink «%s», %s" % (label_name, tv),
            "pid 1: %s" % summary(picture["1-suona"]),
            "pid 2: %s" % summary(picture["2-dopo-esci"]),
            "pid 3: %s" % summary(picture["3-dopo-rientro"]),
            "pid 4: %s" % summary(after), "; ".join(note)])
        print("   4 %s — %s" % (outcome, reason_text), flush=True)
        E.put("F-012B", outcome, reason_text,
                expected_val="after «Exit» and an immediate re-entry (user manager alive) a PulseAudio "
                       "client plays and the browser hears the 440 Hz tone (>=80%% audible, "
                       "peak 440±12 Hz); pipewire-pulse not older than pipewire "
                       "(tolerance %.0f s)" % TOL_START_S,
                observed=oss, evidence=ev, numbers=num4, gesture=gesture)

        if not o.fault:
            return
        # ── the fault: at point 4 nothing plays ────────────────────────────
        silence_pulse(s)
        time.sleep(1.5)
        eg1, dg1, _x, rg1 = F12.listen(s, 4.0)
        evg = [G4.save_json(o, "f012b-orecchio-guasto.json", rg1)]
        if not samples4:
            E.fault("F-012B", None, "no healthy sample at point 4 for the wrong expectation")
            return
        eg2, dg2, _y = G4.judge_sound(samples4, 660)
        fake = read_photo("@@hz 100\n@@p systemd 1 10 init.scope\n"
                           "@@p pipewire 3 900 pipewire.service\n"
                           "@@p pipewire-pulse 2 20 pipewire-pulse.service\n")
        eg3, dg3 = judge_pid(read_photo("@@hz 100\n@@p systemd 1 10 init.scope\n"
                                          "@@p pipewire-pulse 2 20 pipewire-pulse.service\n"),
                               fake)
        seen_v = eg1 == "FAIL" and eg2 == "FAIL" and eg3 == S.FAIL
        E.fault("F-012B", seen_v,
                 "at point 4 no sound ⇒ %s «%s» · 660 Hz expectation on the real samples ⇒ %s "
                 "«%s» · pulse older than pipewire (fake photo) ⇒ %s «%s»"
                 % (eg1, dg1, eg2, dg2, eg3, dg3), evidence=evg)


if __name__ == "__main__":
    sys.exit(S.execute(__doc__, FUNCTIONS, body_el, certify))
