#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f030 — F-030 THE SCREEN DOES NOT TURN OFF AND DOES NOT LOCK BY ITSELF

    python3 15-f030-schermo-sempre-acceso.py --scatola lxqt --browser chrome [--guasto]
        [--attesa-s 450] [--ogni-s 45]

EXPECTED: a STILL session, without input, for minutes: the screen stays the
desktop — it does not turn off (DPMS, screensaver), does not dim, does not lock, the
machine does not suspend.

⛔ THE FORM, DECLARED (the plan says 11 minutes, the cap per test is 10):
   · a REAL WAIT of `--attesa-s` (450 s = 7 min 30 s) without a single input
     event, with a PHOTO every `--ogni-s` (45 s): it covers all the standard
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

G1B = S._carica("g1b", os.path.join(S.QUI, "15-g1b-comune.py"))
FUNZIONI = ("F-030",)
PER_BROWSER = False
LUNGA = True

TETTO_S = 600           # a time above 10 minutes is not «by itself, in a hurry»
GIALLO = (255, 255, 0)
BLOCCATORI = r"swayidle|swaylock|xscreensaver|xfce4-screensaver|light-locker|hypridle|gtklock"


def extra(a):
    a.add_argument("--attesa-s", type=int, default=450)
    a.add_argument("--ogni-s", type=int, default=45)


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES (pure functions)
# ═══════════════════════════════════════════════════════════════════════════
def _spento_o_lungo(v, scala=1):
    """None (not read) · True if 0 (off) or > TETTO_S."""
    if v is None:
        return None
    return v == 0 or v * scala > TETTO_S


def giudica_tempi(d, v):
    """v = the values read.  Returns [defects]; a missing value is a defect
    (I could not read what I had to judge)."""
    guai = []

    def serve(k):
        if v.get(k) is None:
            guai.append("%s not read" % k)
            return False
        return True

    if d == "gnome":
        if serve("idle-delay") and not _spento_o_lungo(v["idle-delay"]):
            guai.append("idle-delay=%d s (dims and locks)" % v["idle-delay"])
        if serve("sleep-inactive-ac-type") and v["sleep-inactive-ac-type"] != "nothing":
            if not _spento_o_lungo(v.get("sleep-inactive-ac-timeout")):
                guai.append("suspend «%s» after %s s" % (
                    v["sleep-inactive-ac-type"], v.get("sleep-inactive-ac-timeout")))
    elif d == "kde":
        if serve("no-lockscreen") and not v["no-lockscreen"]:
            guai.append("KWin WITHOUT --no-lockscreen (kscreenlocker locks)")
        if serve("inibito") and not v["inibito"]:
            s = v.get("spegni-schermo-s")
            if not _spento_o_lungo(s):
                guai.append("powerdevil NOT inhibited and screen off after %s s" % s)
    elif d == "xfce":
        if serve("dpms-enabled") and v["dpms-enabled"]:
            for k in ("dpms-on-ac-sleep", "dpms-on-ac-off"):
                if not _spento_o_lungo(v.get(k), 60):
                    guai.append("DPMS on, %s=%s min" % (k, v.get(k)))
        if serve("inactivity-on-ac") and not _spento_o_lungo(v["inactivity-on-ac"], 60):
            guai.append("inactivity-on-ac=%d min" % v["inactivity-on-ac"])
        if v.get("blank-on-ac") is not None and not _spento_o_lungo(v["blank-on-ac"], 60):
            guai.append("blank-on-ac=%d min" % v["blank-on-ac"])
    elif d == "lxqt":
        if serve("enableIdlenessWatcher") and v["enableIdlenessWatcher"]:
            guai.append("LXQt's inactivity watcher is ON (%s s)"
                        % v.get("idle-s", "?"))
    if v.get("bloccatori"):
        guai.append("lockers running as the tenant: %s" % v["bloccatori"])
    return guai


def col_guasto_300(d, v):
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


def misura(png):
    k = G1B.conta_colori(png, (G1B.CIANO, GIALLO))
    return {"ciano": k[G1B.CIANO], "giallo": k[GIALLO],
            "lum": G1B.luminanza_media(png), "vivi": G1B.vivi(png)}


def giudica_foto(rif, m):
    """(ok, sentence) of ONE photo against the starting one."""
    guai = []
    area0 = rif["ciano"] + rif["giallo"]
    area = m["ciano"] + m["giallo"]
    if area < 0.5 * area0:
        guai.append("known window %.3f → %.3f" % (area0, area))
    if abs(m["lum"] - rif["lum"]) > 25:
        guai.append("luminance %.0f → %.0f" % (rif["lum"], m["lum"]))
    if m["vivi"] < 0.5 * rif["vivi"]:
        guai.append("non-black pixels %.3f → %.3f" % (rif["vivi"], m["vivi"]))
    frase = "c %.3f y %.3f lum %.0f live %.3f" % (m["ciano"], m["giallo"], m["lum"], m["vivi"])
    return (not guai), (frase if not guai else "; ".join(guai))


def colore_di(m):
    if m["ciano"] > 2 * m["giallo"] and m["ciano"] > 0.005:
        return "ciano"
    if m["giallo"] > 2 * m["ciano"] and m["giallo"] > 0.005:
        return "giallo"
    return None


def giudica_serie(rif, serie):
    """serie = [(t, measurement)].  Returns (outcome, sentence)."""
    cattive = []
    colori = set()
    for t, m in serie:
        ok, f = giudica_foto(rif, m)
        if not ok:
            cattive.append("at %d s: %s" % (t, f))
        c = colore_di(m)
        if c:
            colori.add(c)
    if cattive:
        return S.ROSSO, "the screen is NO longer the desktop — " + " · ".join(cattive)
    if len(colori) < 2:
        return S.ROSSO, ("FROZEN image: the known window never changed colour "
                         "(seen: %s)" % (sorted(colori) or "none"))
    return S.VERDE, "%d photos, all the desktop, live image (%s)" % (
        len(serie), "⇄".join(sorted(colori)))


def certifica():
    guai = []

    def prova(cosa, vero):
        print("%s %s" % ("⭐" if vero else "⛔", cosa))
        if not vero:
            guai.append(cosa)

    buoni = {
        "gnome": {"idle-delay": 0, "sleep-inactive-ac-type": "nothing", "bloccatori": ""},
        "kde": {"no-lockscreen": True, "inibito": True, "spegni-schermo-s": None,
                "bloccatori": ""},
        "xfce": {"dpms-enabled": False, "inactivity-on-ac": 0, "blank-on-ac": None,
                 "bloccatori": ""},
        "lxqt": {"enableIdlenessWatcher": False, "bloccatori": ""},
    }
    for d, v in buoni.items():
        prova("%s: the cure's values ⇒ no defects" % d, not giudica_tempi(d, v))
        prova("%s: FAULT A (300 s) ⇒ defect" % d, bool(giudica_tempi(d, col_guasto_300(d, v))))
        prova("%s: a field not read ⇒ defect" % d,
              bool(giudica_tempi(d, {"bloccatori": ""})))
    prova("gnome: idle-delay 900 s ⇒ fine", not giudica_tempi(
        "gnome", dict(buoni["gnome"], **{"idle-delay": 900})))
    prova("locker running ⇒ defect", bool(giudica_tempi(
        "lxqt", dict(buoni["lxqt"], bloccatori="swayidle"))))
    rif = {"ciano": 0.08, "giallo": 0.0, "lum": 90, "vivi": 0.9}
    g = {"ciano": 0.0, "giallo": 0.08, "lum": 95, "vivi": 0.9}
    prova("live series ⇒ VERDE", giudica_serie(rif, [(45, rif), (90, g)])[0] == S.VERDE)
    prova("frozen series ⇒ ROSSO", giudica_serie(rif, [(45, rif), (90, rif)])[0] == S.ROSSO)
    nero = misura(G1B.png_nero(64, 36))
    prova("FAULT B: black canvas at the end ⇒ ROSSO",
          giudica_serie(rif, [(45, rif), (90, g), (135, nero)])[0] == S.ROSSO)
    xfce = {"ciano": 0.08, "giallo": 0.0, "lum": 22, "vivi": 0.12}
    prova("XFCE (black background): the turned-off screen is seen from the non-black pixels",
          not giudica_foto(xfce, dict(nero))[0])
    print("⛔ %d problems" % len(guai) if guai else "⭐ CERTIFIED")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
#  THE FIELDS, inside the session
# ═══════════════════════════════════════════════════════════════════════════
def _num(t):
    m = re.search(r"-?\d+", t or "")
    return int(m.group(0)) if m else None


def _ultima(t):
    # ⚠ `[M]` 25 Sep 2026, kde: qdbus6/kreadconfig6 write AFTER the answer
    #   the locale warning («Detected locale "C"…»): it is not the value
    rumore = re.compile(r"password|Detected locale|Qt depends on a UTF-8|reconfigure your "
                        r"locale|See the locale|Gtk-WARNING")
    righe = [r for r in (t or "").splitlines() if r.strip() and not rumore.search(r)]
    return righe[-1].strip() if righe else ""


def leggi_tempi(s, d):
    v, grezzo = {}, []

    def sess(cmd):
        c, t = G1B.nella_sessione(s, cmd, 60)
        grezzo.append("$ %s\n%s" % (cmd, t))
        return c, _ultima(t)

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
        c, t = s.sc.dentro("p=$(pgrep -u %s -x kwin_wayland | head -1); [ -n \"$p\" ] && "
                           "tr '\\0' ' ' < /proc/$p/cmdline" % s.chi, 30)
        grezzo.append("$ cmdline of kwin_wayland\n" + t)
        v["no-lockscreen"] = ("--no-lockscreen" in t) if "kwin" in t else None
        _c, t = sess("qdbus6 org.kde.Solid.PowerManagement "
                     "/org/kde/Solid/PowerManagement/PolicyAgent "
                     "org.kde.Solid.PowerManagement.PolicyAgent.HasInhibition 4")
        _c, tt = G1B.nella_sessione(s, "qdbus6 org.kde.Solid.PowerManagement "
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
        c, t = s.sc.dentro("cat /home/%s/.config/lxqt/lxqt-powermanagement.conf" % s.chi, 30)
        grezzo.append("$ lxqt-powermanagement.conf\n" + t)
        m = re.search(r"^enableIdlenessWatcher\s*=\s*(\w+)", t, re.M)
        v["enableIdlenessWatcher"] = (m.group(1) == "true") if m else None
        m = re.search(r"^idlenessTime\w*\s*=\s*(\S+)", t, re.M)
        v["idle-s"] = m.group(1) if m else None
    c, t = s.sc.dentro("pgrep -u %s -a -f '%s' | grep -v pgrep || true" % (s.chi, BLOCCATORI),
                       30)
    t = "\n".join(r for r in t.splitlines() if r.strip() and "password" not in r)
    grezzo.append("$ bloccatori\n" + t)
    v["bloccatori"] = ", ".join(r.split(None, 1)[-1][:60] for r in t.splitlines())
    return v, grezzo


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def corpo(o, E):
    d = o.scatola
    t_inizio = time.time()
    with S.Sessione(o, "030", E) as s:
        G1B.passo("tenant and browser ready")
        ok, m = s.entra()
        G1B.passo("inside: %s" % m[:80])
        if not ok:
            raise S.Bloccata(m)
        time.sleep(6 if d != "kde" else 10)
        geo = s.geometria()
        W, H = geo["tl"], geo["ta"]
        c, t = G1B.metti_finestra(s)
        if c != 0:
            raise S.Bloccata("the window's program cannot be written: " + t[-200:])
        c, t = G1B.apri_finestra(s, "orologio", "#00ffff", int(W * 0.3), int(H * 0.3),
                                 altro="#ffff00", periodo=7)
        if c != 0:
            raise S.Bloccata("the known window does not start: " + t[-200:])
        time.sleep(5)
        if d == "gnome":
            G1B.fuoco_sulla_tela(s, geo)
            G1B.combinazione(s.g, ["Escape"])    # ⚠ GNOME is born in the overview
            time.sleep(2)
        # ⛔ from here NO input: only photos (CDP/Marionette move nothing)
        png0, p0 = G1B.foto(s, "inizio", scala=0.5)
        if not png0:
            raise S.Bloccata("no starting photo: " + p0)
        rif = misura(png0)
        for _ in range(6):                       # the window can be late being born
            if rif["ciano"] + rif["giallo"] >= 0.01:
                break
            time.sleep(4)
            png0, p0 = G1B.foto(s, "inizio", scala=0.5)
            rif = misura(png0) if png0 else rif
        if rif["ciano"] + rif["giallo"] < 0.01:
            c, t = s.sc.dentro("cat /home/%s/.c15-python3.log 2>&1 | tail -n 5" % s.chi, 30)
            G1B.passo("the window's log: %s" % t[-400:])
            raise S.Bloccata("the known window is not seen in the starting photo (%s)" % rif)
        ev = [p0]
        v, grezzo = leggi_tempi(s, d)
        # the wait: the cap is 10 minutes for the WHOLE test
        attesa = min(o.attesa_s, max(60, 480 - int(time.time() - t_inizio)))
        print("   wait without input: %d s (photo every %d s)" % (attesa, o.ogni_s), flush=True)
        serie, t0 = [], time.time()
        png_ultima = png0
        while True:
            dorme = min(o.ogni_s, attesa - (time.time() - t0))
            if dorme <= 0:
                break
            time.sleep(dorme)
            trascorso = int(time.time() - t0)
            png, p = G1B.foto(s, "ferma-%03ds" % trascorso, scala=0.5)
            if not png:
                serie.append((trascorso, {"ciano": 0, "giallo": 0, "lum": 0, "vivi": 0}))
                continue
            png_ultima = png
            mm = misura(png)
            print("   %4d s: %s" % (trascorso, giudica_foto(rif, mm)[1]), flush=True)
            serie.append((trascorso, mm))
            ev.append(p)
        # ⭐ THE PROOF OF LIFE, at the end of the wait: the known window changes colour
        #   every 7 s (it was 30: `[M]` 24 Sep 2026, gnome, photos every ~60 s fell
        #   on the same phase (`[M]` 24 Sep 2026, gnome: eight photos all yellow).
        #   ⇒ A photo every 4 s, up to 40 s, until the colour CHANGES.
        ultimo = colore_di(serie[-1][1]) if serie else colore_di(rif)
        fine_vita = time.time() + 40
        while time.time() < fine_vita:
            time.sleep(4)
            trascorso = int(time.time() - t0)
            png, p = G1B.foto(s, "vita-%03ds" % trascorso, scala=0.5)
            if not png:
                continue
            png_ultima = png
            mm = misura(png)
            serie.append((trascorso, mm))
            if colore_di(mm) and colore_di(mm) != ultimo:
                ev.append(p)
                print("   %4d s: proof of life, %s → %s" % (trascorso, ultimo, colore_di(mm)),
                      flush=True)
                break
        v_fine, grezzo_fine = leggi_tempi(s, d)
        e_foto, f_foto = giudica_serie(rif, serie)
        guai = giudica_tempi(d, v)
        guai_fine = giudica_tempi(d, v_fine)
        ev.append(s.salva_testo("f030-campi.txt",
                                ["at the start: %s" % v, "at the end: %s" % v_fine, ""]
                                + grezzo + ["", "--- at the end ---"] + grezzo_fine))
        oss = "photos: %s · fields: %s" % (f_foto, v)
        atteso = ("%d s still without input: every photo is still the desktop, the image is live; "
                  "inactivity/DPMS/lock off or > %d s" % (attesa, TETTO_S))
        if e_foto == S.ROSSO:
            E.metti("F-030", S.FAIL, f_foto, atteso=atteso, osservato=oss, evidenze=ev)
        elif guai or guai_fine:
            E.metti("F-030", S.FAIL, "the photos are fine, but the fields are not: %s"
                    % "; ".join(guai or guai_fine), atteso=atteso, osservato=oss, evidenze=ev)
        else:
            E.metti("F-030", S.PASS, "%s; right fields (%s)" % (f_foto, d), atteso=atteso,
                    osservato=oss, evidenze=ev)

        if o.guasto:
            ga = giudica_tempi(d, col_guasto_300(d, v))
            w, h = G1B.misura_png(png_ultima)
            serie_b = serie[:-1] + [(serie[-1][0] if serie else 0,
                                     misura(G1B.png_nero(w, h)))]
            eb, fb = giudica_serie(rif, serie_b)
            E.guasto("F-030", bool(ga) and eb == S.ROSSO,
                     "A) time at 300 s ⇒ %s · B) last photo black ⇒ %s"
                     % ("ROSSO (%s)" % "; ".join(ga) if ga else "verde (NOT seen)",
                        "ROSSO" if eb == S.ROSSO else "verde (NOT seen)"))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica, extra=extra))
