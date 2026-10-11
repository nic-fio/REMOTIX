#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f030 — F-030 THE SCREEN DOES NOT TURN OFF AND DOES NOT LOCK BY ITSELF

    python3 15-f030-screen-always-on.py --box lxqt --browser chrome [--fault]
        [--wait-s 450] [--every-s 45]

EXPECTED: a STILL session, without input, for minutes: the screen stays the
desktop — it does not turn off (DPMS, screensaver), does not dim, does not lock, the
machine does not suspend.

⛔ THE FORM, DECLARED (the plan says 11 minutes, the cap per test is 10):
   · a REAL WAIT of `--wait-s` (450 s = 7 min 30 s) without a single input
     event, with a PHOTO every `--every-s` (45 s): it covers all the standard
     5-minute times — GNOME idle-delay 300 s (dims and locks), LXQt/labwc's swayidle
     (`timeout 300 wlopm --off`), Plasma's kscreenlocker 5 min;
   · and the 10-minute times — XFCE DPMS (xfce4-power-manager, 10 min), Plasma
     powerdevil «turn off the screen after 10 min» — which the wait does not reach,
     are judged from the VALUE OF THE FIELDS read INSIDE the
     tenant's session: they must be off or > 600 s (on KDE: KWin with
     `--no-lockscreen` and REMOTIX's inhibition of powerdevil in force);
   · and no locker/dimmer running as the tenant (swayidle,
     swaylock, xscreensaver, xfce4-screensaver, light-locker, hypridle).
   PASS = photos all «still the desktop» + LIVE image + right fields.

⭐ THE LIVE IMAGE: a photo equal to the start is not enough — if the capture dies
   (on wlroots a turned-off output gives `failed` to the capture) the canvas stays
   FROZEN on the last frame and looks on.  ⇒ In the session runs
   a known window (GTK4, 30% of the desktop) that changes colour BY ITSELF every 7
   s, cyan ⇄ yellow, without input; the photos must see it, and see it CHANGE.

Every photo is judged against the starting one: the known window is there (cyan or
yellow, at least half of the starting area), the mean luminance within 25
levels, the non-black pixels at least half (a turned-off screen is black even on
XFCE, which is born with a black background).

This test does not depend on the browser (one pass per desktop) and can
run in parallel with the others of its desktop: a tenant of its own (c15030u<n>).

FAULT (two, both must give red):
  A) a time read that is 300 s (substituted in the value read from the desktop:
     GNOME idle-delay, KDE inhibition removed and turn-off at 300 s, XFCE DPMS
     on at 5 min, LXQt watcher on at 300 s) ⇒ fields judge RED;
  B) a BLACK canvas of the same size instead of the last photo ⇒ photos
     judge RED.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G1B = S._load("g1b", os.path.join(S.HERE, "15-g1b-common.py"))
FUNCTIONS = ("F-030",)
PER_BROWSER = False
LONG = True

CAP_S = 600           # a time above 10 minutes is not «by itself, in a hurry»
YELLOW = (255, 255, 0)
BLOCKERS = r"swayidle|swaylock|xscreensaver|xfce4-screensaver|light-locker|hypridle|gtklock"


def extra(a):
    a.add_argument("--wait-s", type=int, default=450)
    a.add_argument("--every-s", type=int, default=45)


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES (pure functions)
# ═══════════════════════════════════════════════════════════════════════════
def _off_or_long(v, scale_factor=1):
    """None (not read) · True if 0 (off) or > CAP_S."""
    if v is None:
        return None
    return v == 0 or v * scale_factor > CAP_S


def judge_times(d, v):
    """v = the values read.  Returns [defects]; a missing value is a defect
    (I could not read what I had to judge)."""
    troubles = []

    def needs(k):
        if v.get(k) is None:
            troubles.append("%s not read" % k)
            return False
        return True

    if d == "gnome":
        if needs("idle-delay") and not _off_or_long(v["idle-delay"]):
            troubles.append("idle-delay=%d s (dims and locks)" % v["idle-delay"])
        if needs("sleep-inactive-ac-type") and v["sleep-inactive-ac-type"] != "nothing":
            if not _off_or_long(v.get("sleep-inactive-ac-timeout")):
                troubles.append("suspend «%s» after %s s" % (
                    v["sleep-inactive-ac-type"], v.get("sleep-inactive-ac-timeout")))
    elif d == "kde":
        if needs("no-lockscreen") and not v["no-lockscreen"]:
            troubles.append("KWin WITHOUT --no-lockscreen (kscreenlocker locks)")
        if needs("inibito") and not v["inibito"]:
            s = v.get("spegni-schermo-s")
            if not _off_or_long(s):
                troubles.append("powerdevil NOT inhibited and screen off after %s s" % s)
    elif d == "xfce":
        if needs("dpms-enabled") and v["dpms-enabled"]:
            for k in ("dpms-on-ac-sleep", "dpms-on-ac-off"):
                if not _off_or_long(v.get(k), 60):
                    troubles.append("DPMS on, %s=%s min" % (k, v.get(k)))
        if needs("inactivity-on-ac") and not _off_or_long(v["inactivity-on-ac"], 60):
            troubles.append("inactivity-on-ac=%d min" % v["inactivity-on-ac"])
        if v.get("blank-on-ac") is not None and not _off_or_long(v["blank-on-ac"], 60):
            troubles.append("blank-on-ac=%d min" % v["blank-on-ac"])
    elif d == "lxqt":
        if needs("enableIdlenessWatcher") and v["enableIdlenessWatcher"]:
            troubles.append("LXQt's inactivity watcher is ON (%s s)"
                        % v.get("idle-s", "?"))
    if v.get("blockers"):
        troubles.append("lockers running as the tenant: %s" % v["blockers"])
    return troubles


def with_fault_300(d, v):
    """FAULT A: the desktop's main time brought to 300 s."""
    v = dict(v)
    if d == "gnome":
        v["idle-delay"] = 300
    elif d == "kde":
        v.update({"inibito": False, "no-lockscreen": False, "spegni-schermo-s": 300})
    elif d == "xfce":
        v.update({"dpms-enabled": True, "dpms-on-ac-sleep": 5, "dpms-on-ac-off": 5})
    elif d == "lxqt":
        v.update({"enableIdlenessWatcher": True, "idle-s": 300})
    return v


def measure(png):
    k = G1B.count_colors(png, (G1B.CYAN, YELLOW))
    return {"ciano": k[G1B.CYAN], "giallo": k[YELLOW],
            "lum": G1B.mean_luminance(png), "living": G1B.living(png)}


def judge_photo(ref, m):
    """(ok, sentence) of ONE photo against the starting one."""
    troubles = []
    area0 = ref["ciano"] + ref["giallo"]
    area = m["ciano"] + m["giallo"]
    if area < 0.5 * area0:
        troubles.append("known window %.3f → %.3f" % (area0, area))
    if abs(m["lum"] - ref["lum"]) > 25:
        troubles.append("luminance %.0f → %.0f" % (ref["lum"], m["lum"]))
    if m["living"] < 0.5 * ref["living"]:
        troubles.append("non-black pixels %.3f → %.3f" % (ref["living"], m["living"]))
    sentence = "c %.3f y %.3f lum %.0f live %.3f" % (m["ciano"], m["giallo"], m["lum"], m["living"])
    return (not troubles), (sentence if not troubles else "; ".join(troubles))


def color_of(m):
    if m["ciano"] > 2 * m["giallo"] and m["ciano"] > 0.005:
        return "ciano"
    if m["giallo"] > 2 * m["ciano"] and m["giallo"] > 0.005:
        return "giallo"
    return None


def judge_series(ref, serial):
    """serie = [(t, measurement)].  Returns (outcome, sentence)."""
    bad = []
    colors = set()
    for t, m in serial:
        ok, f = judge_photo(ref, m)
        if not ok:
            bad.append("at %d s: %s" % (t, f))
        c = color_of(m)
        if c:
            colors.add(c)
    if bad:
        return S.RED, "the screen is NO longer the desktop — " + " · ".join(bad)
    if len(colors) < 2:
        return S.RED, ("FROZEN image: the known window never changed colour "
                         "(seen: %s)" % (sorted(colors) or "none"))
    return S.GREEN, "%d photos, all the desktop, live image (%s)" % (
        len(serial), "⇄".join(sorted(colors)))


def certify():
    troubles = []

    def prova(what, real):
        print("%s %s" % ("⭐" if real else "⛔", what))
        if not real:
            troubles.append(what)

    good_n = {
        "gnome": {"idle-delay": 0, "sleep-inactive-ac-type": "nothing", "blockers": ""},
        "kde": {"no-lockscreen": True, "inibito": True, "spegni-schermo-s": None,
                "blockers": ""},
        "xfce": {"dpms-enabled": False, "inactivity-on-ac": 0, "blank-on-ac": None,
                 "blockers": ""},
        "lxqt": {"enableIdlenessWatcher": False, "blockers": ""},
    }
    for d, v in good_n.items():
        prova("%s: the cure's values ⇒ no defects" % d, not judge_times(d, v))
        prova("%s: FAULT A (300 s) ⇒ defect" % d, bool(judge_times(d, with_fault_300(d, v))))
        prova("%s: a field not read ⇒ defect" % d,
              bool(judge_times(d, {"blockers": ""})))
    prova("gnome: idle-delay 900 s ⇒ fine", not judge_times(
        "gnome", dict(good_n["gnome"], **{"idle-delay": 900})))
    prova("locker running ⇒ defect", bool(judge_times(
        "lxqt", dict(good_n["lxqt"], blockers="swayidle"))))
    ref = {"ciano": 0.08, "giallo": 0.0, "lum": 90, "living": 0.9}
    g = {"ciano": 0.0, "giallo": 0.08, "lum": 95, "living": 0.9}
    prova("live series ⇒ GREEN", judge_series(ref, [(45, ref), (90, g)])[0] == S.GREEN)
    prova("frozen series ⇒ RED", judge_series(ref, [(45, ref), (90, ref)])[0] == S.RED)
    nero = measure(G1B.png_nero(64, 36))
    prova("FAULT B: black canvas at the end ⇒ ROSSO",
          judge_series(ref, [(45, ref), (90, g), (135, nero)])[0] == S.RED)
    xfce = {"ciano": 0.08, "giallo": 0.0, "lum": 22, "living": 0.12}
    prova("XFCE (black background): the turned-off screen is seen from the non-black pixels",
          not judge_photo(xfce, dict(nero))[0])
    print("⛔ %d problems" % len(troubles) if troubles else "⭐ CERTIFIED")
    return 1 if troubles else 0


# ═══════════════════════════════════════════════════════════════════════════
#  THE FIELDS, inside the session
# ═══════════════════════════════════════════════════════════════════════════
def _num(t):
    m = re.search(r"-?\d+", t or "")
    return int(m.group(0)) if m else None


def _last(t):
    # ⚠ `[M]` 25 Sep 2026, kde: qdbus6/kreadconfig6 write AFTER the answer
    #   the local warning («Detected local "C"…»): it is not the value
    noise = re.compile(r"password|Detected locale|Qt depends on a UTF-8|reconfigure your "
                        r"locale|See the locale|Gtk-WARNING")
    lines = [r for r in (t or "").splitlines() if r.strip() and not noise.search(r)]
    return lines[-1].strip() if lines else ""


def read_times(s, d):
    v, raw = {}, []

    def sess(cmd):
        c, t = G1B.in_session(s, cmd, 60)
        raw.append("$ %s\n%s" % (cmd, t))
        return c, _last(t)

    if d == "gnome":
        _c, t = sess("gsettings get org.gnome.desktop.session idle-delay")
        v["idle-delay"] = _num(t.replace("uint32", "")) if "uint32" in t else None
        _c, t = sess("gsettings get org.gnome.desktop.screensaver lock-enabled")
        v["lock-enabled"] = t
        _c, t = sess("gsettings get org.gnome.settings-daemon.plugins.power "
                     "sleep-inactive-ac-type")
        v["sleep-inactive-ac-type"] = t.strip("'") or None
        _c, t = sess("gsettings get org.gnome.settings-daemon.plugins.power "
                     "sleep-inactive-ac-timeout")
        v["sleep-inactive-ac-timeout"] = _num(t)
    elif d == "kde":
        c, t = s.sc.inside("p=$(pgrep -u %s -x kwin_wayland | head -1); [ -n \"$p\" ] && "
                           "tr '\\0' ' ' < /proc/$p/cmdline" % s.chi, 30)
        raw.append("$ cmdline of kwin_wayland\n" + t)
        v["no-lockscreen"] = ("--no-lockscreen" in t) if "kwin" in t else None
        _c, t = sess("qdbus6 org.kde.Solid.PowerManagement "
                     "/org/kde/Solid/PowerManagement/PolicyAgent "
                     "org.kde.Solid.PowerManagement.PolicyAgent.HasInhibition 4")
        _c, tt = G1B.in_session(s, "qdbus6 org.kde.Solid.PowerManagement "
                                    "/org/kde/Solid/PowerManagement/PolicyAgent "
                                    "org.kde.Solid.PowerManagement.PolicyAgent."
                                    "HasInhibition 4 2>/dev/null", 60)
        m = re.search(r"^(true|false)\s*$", tt, re.M)
        v["inibito"] = (m.group(1) == "true") if m else None
        _c, t = sess("kreadconfig6 --file powerdevilrc --group AC --group Display "
                     "--key TurnOffDisplayIdleTimeoutSec --default 600")
        v["spegni-schermo-s"] = _num(t)
        _c, t = sess("kreadconfig6 --file kscreenlockerrc --group Daemon --key Autolock "
                     "--default true; kreadconfig6 --file kscreenlockerrc --group Daemon "
                     "--key Timeout --default 5")
        v["kscreenlocker (note only)"] = t
    elif d == "xfce":
        for k in ("dpms-enabled", "dpms-on-ac-sleep", "dpms-on-ac-off", "inactivity-on-ac",
                  "blank-on-ac"):
            c, t = sess("xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/%s" % k)
            if c != 0 or "does not exist" in t or "non esiste" in t:
                v[k] = None
            elif t in ("true", "false"):
                v[k] = t == "true"
            else:
                v[k] = _num(t)
    elif d == "lxqt":
        c, t = s.sc.inside("cat /home/%s/.config/lxqt/lxqt-powermanagement.conf" % s.chi, 30)
        raw.append("$ lxqt-powermanagement.conf\n" + t)
        m = re.search(r"^enableIdlenessWatcher\s*=\s*(\w+)", t, re.M)
        v["enableIdlenessWatcher"] = (m.group(1) == "true") if m else None
        m = re.search(r"^idlenessTime\w*\s*=\s*(\S+)", t, re.M)
        v["idle-s"] = m.group(1) if m else None
    c, t = s.sc.inside("pgrep -u %s -a -f '%s' | grep -v pgrep || true" % (s.chi, BLOCKERS),
                       30)
    t = "\n".join(r for r in t.splitlines() if r.strip() and "password" not in r)
    raw.append("$ bloccatori\n" + t)
    v["blockers"] = ", ".join(r.split(None, 1)[-1][:60] for r in t.splitlines())
    return v, raw


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def body(o, E):
    d = o.box
    t_start = time.time()
    with S.Session(o, "030", E) as s:
        G1B.step("tenant and browser ready")
        ok, m = s.enter()
        G1B.step("inside: %s" % m[:80])
        if not ok:
            raise S.Blocked(m)
        time.sleep(6 if d != "kde" else 10)
        geo = s.geometry()
        W, H = geo["tl"], geo["ta"]
        c, t = G1B.put_window(s)
        if c != 0:
            raise S.Blocked("the window's program cannot be written: " + t[-200:])
        c, t = G1B.open_window(s, "orologio", "#00ffff", int(W * 0.3), int(H * 0.3),
                                 other="#ffff00", period=7)
        if c != 0:
            raise S.Blocked("the known window does not start: " + t[-200:])
        time.sleep(5)
        if d == "gnome":
            G1B.focus_on_canvas(s, geo)
            G1B.combination(s.g, ["Escape"])    # ⚠ GNOME is born in the overview
            time.sleep(2)
        # ⛔ from here NO input: only photos (CDP/Marionette move nothing)
        png0, p0 = G1B.photo(s, "start", scale_factor=0.5)
        if not png0:
            raise S.Blocked("no starting photo: " + p0)
        ref = measure(png0)
        for _ in range(6):                       # the window can be late being born
            if ref["ciano"] + ref["giallo"] >= 0.01:
                break
            time.sleep(4)
            png0, p0 = G1B.photo(s, "start", scale_factor=0.5)
            ref = measure(png0) if png0 else ref
        if ref["ciano"] + ref["giallo"] < 0.01:
            c, t = s.sc.inside("cat /home/%s/.c15-python3.log 2>&1 | tail -n 5" % s.chi, 30)
            G1B.step("the window's log: %s" % t[-400:])
            raise S.Blocked("the known window is not seen in the starting photo (%s)" % ref)
        ev = [p0]
        v, raw = read_times(s, d)
        # the wait: the cap is 10 minutes for the WHOLE test
        wait = min(o.wait_s, max(60, 480 - int(time.time() - t_start)))
        print("   wait without input: %d s (photo every %d s)" % (wait, o.every_s), flush=True)
        serial, t0 = [], time.time()
        png_last = png0
        while True:
            sleep_ms = min(o.every_s, wait - (time.time() - t0))
            if sleep_ms <= 0:
                break
            time.sleep(sleep_ms)
            elapsed = int(time.time() - t0)
            png, p = G1B.photo(s, "ferma-%03ds" % elapsed, scale_factor=0.5)
            if not png:
                serial.append((elapsed, {"ciano": 0, "giallo": 0, "lum": 0, "living": 0}))
                continue
            png_last = png
            mm = measure(png)
            print("   %4d s: %s" % (elapsed, judge_photo(ref, mm)[1]), flush=True)
            serial.append((elapsed, mm))
            ev.append(p)
        # ⭐ THE PROOF OF LIFE, at the end of the wait: the known window changes colour
        #   every 7 s (it was 30: `[M]` 24 Sep 2026, gnome, photos every ~60 s fell
        #   on the same phase (`[M]` 24 Sep 2026, gnome: eight photos all yellow).
        #   ⇒ A photo every 4 s, up to 40 s, until the colour CHANGES.
        last = color_of(serial[-1][1]) if serial else color_of(ref)
        fine_vita = time.time() + 40
        while time.time() < fine_vita:
            time.sleep(4)
            elapsed = int(time.time() - t0)
            png, p = G1B.photo(s, "vita-%03ds" % elapsed, scale_factor=0.5)
            if not png:
                continue
            png_last = png
            mm = measure(png)
            serial.append((elapsed, mm))
            if color_of(mm) and color_of(mm) != last:
                ev.append(p)
                print("   %4d s: proof of life, %s → %s" % (elapsed, last, color_of(mm)),
                      flush=True)
                break
        v_fine, raw_end = read_times(s, d)
        e_photo, f_photo = judge_series(ref, serial)
        troubles = judge_times(d, v)
        end_troubles = judge_times(d, v_fine)
        ev.append(s.save_text("f030-campi.txt",
                                ["at the start: %s" % v, "at the end: %s" % v_fine, ""]
                                + raw + ["", "--- at the end ---"] + raw_end))
        oss = "photos: %s · fields: %s" % (f_photo, v)
        expected = ("%d s still without input: every photo is still the desktop, the image is live; "
                  "inactivity/DPMS/lock off or > %d s" % (wait, CAP_S))
        if e_photo == S.RED:
            E.put("F-030", S.FAIL, f_photo, expected=expected, observed=oss, evidence=ev)
        elif troubles or end_troubles:
            E.put("F-030", S.FAIL, "the photos are fine, but the fields are not: %s"
                    % "; ".join(troubles or end_troubles), expected=expected, observed=oss, evidence=ev)
        else:
            E.put("F-030", S.PASS, "%s; right fields (%s)" % (f_photo, d), expected=expected,
                    observed=oss, evidence=ev)

        if o.fault:
            ga = judge_times(d, with_fault_300(d, v))
            w, h = G1B.png_size(png_last)
            series_b = serial[:-1] + [(serial[-1][0] if serial else 0,
                                     measure(G1B.png_nero(w, h)))]
            eb, fb = judge_series(ref, series_b)
            E.fault("F-030", bool(ga) and eb == S.RED,
                     "A) time at 300 s ⇒ %s · B) last photo black ⇒ %s"
                     % ("ROSSO (%s)" % "; ".join(ga) if ga else "verde (NOT seen)",
                        "RED" if eb == S.RED else "verde (NOT seen)"))


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify, extra=extra))
