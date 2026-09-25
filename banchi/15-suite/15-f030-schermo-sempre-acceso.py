#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f030 — F-030 LO SCHERMO NON SI SPEGNE E NON SI BLOCCA DA SOLO

    python3 15-f030-schermo-sempre-acceso.py --scatola lxqt --browser chrome [--guasto]
        [--attesa-s 450] [--ogni-s 45]

ATTESO: una sessione FERMA, senza input, per minuti: lo schermo resta il
desktop — non si spegne (DPMS, salvaschermo), non si oscura, non si blocca, la
macchina non si sospende.

⛔ LA FORMA, DICHIARATA (il piano dice 11 minuti, il tetto per prova e' 10):
   · ATTESA VERA di `--attesa-s` (450 s = 7 min 30 s) senza un solo evento
     d'input, con una FOTO ogni `--ogni-s` (45 s): copre tutti i tempi di 5
     minuti di serie — GNOME idle-delay 300 s (oscura e blocca), il swayidle
     di LXQt/labwc (`timeout 300 wlopm --off`), kscreenlocker di Plasma 5 min;
   · e i tempi di 10 minuti — XFCE DPMS (xfce4-power-manager, 10 min), Plasma
     powerdevil «spegni lo schermo dopo 10 min» — che l'attesa non raggiunge,
     si giudicano dal VALORE DEI CAMPI letti DENTRO la sessione
     dell'inquilino: devono essere spenti o > 600 s (su KDE: KWin con
     `--no-lockscreen` e l'inibizione di REMOTIX a powerdevil in vigore);
   · e nessun bloccatore/oscuratore acceso come l'inquilino (swayidle,
     swaylock, xscreensaver, xfce4-screensaver, light-locker, hypridle).
   PASS = foto tutte «ancora il desktop» + immagine VIVA + campi giusti.

⭐ L'IMMAGINE VIVA: una foto uguale all'inizio non basta — se la cattura muore
   (su wlroots un'uscita spenta da' `failed` alla cattura) la tela resta
   CONGELATA sull'ultimo fotogramma e sembra accesa.  ⇒ Nella sessione gira
   una finestra nota (GTK4, 30% del desktop) che cambia colore DA SOLA ogni 7
   s, ciano ⇄ giallo, senza input; le foto devono vederla, e vederla CAMBIARE.

Ogni foto si giudica contro quella d'inizio: la finestra nota c'e' (ciano o
giallo, almeno meta' dell'area d'inizio), la luminanza media entro 25
livelli, i pixel non neri almeno meta' (uno schermo spento e' nero anche su
XFCE, che nasce con lo sfondo nero).

Questa prova non dipende dal browser (una passata per desktop) e puo'
girare in parallelo alle altre del suo desktop: inquilino suo (c15030u<n>).

GUASTO (due, tutt'e due devono dare rosso):
  A) un tempo letto che vale 300 s (sostituito nel valore letto dal desktop:
     GNOME idle-delay, KDE inibizione tolta e spegnimento a 300 s, XFCE DPMS
     acceso a 5 min, LXQt sorvegliante acceso a 300 s) ⇒ giudice dei campi ROSSO;
  B) una tela NERA della stessa misura al posto dell'ultima foto ⇒ giudice
     delle foto ROSSO.
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

TETTO_S = 600           # un tempo sopra i 10 minuti non e' «da solo, in fretta»
GIALLO = (255, 255, 0)
BLOCCATORI = r"swayidle|swaylock|xscreensaver|xfce4-screensaver|light-locker|hypridle|gtklock"


def extra(a):
    a.add_argument("--attesa-s", type=int, default=450)
    a.add_argument("--ogni-s", type=int, default=45)


# ═══════════════════════════════════════════════════════════════════════════
#  I GIUDICI (funzioni pure)
# ═══════════════════════════════════════════════════════════════════════════
def _spento_o_lungo(v, scala=1):
    """None (non letto) · True se 0 (spento) o > TETTO_S."""
    if v is None:
        return None
    return v == 0 or v * scala > TETTO_S


def giudica_tempi(d, v):
    """v = i valori letti.  Torna [difetti]; un valore che manca e' un difetto
    (non ho potuto leggere quel che dovevo giudicare)."""
    guai = []

    def serve(k):
        if v.get(k) is None:
            guai.append("%s non letto" % k)
            return False
        return True

    if d == "gnome":
        if serve("idle-delay") and not _spento_o_lungo(v["idle-delay"]):
            guai.append("idle-delay=%d s (oscura e blocca)" % v["idle-delay"])
        if serve("sleep-inactive-ac-type") and v["sleep-inactive-ac-type"] != "nothing":
            if not _spento_o_lungo(v.get("sleep-inactive-ac-timeout")):
                guai.append("sospensione «%s» dopo %s s" % (
                    v["sleep-inactive-ac-type"], v.get("sleep-inactive-ac-timeout")))
    elif d == "kde":
        if serve("no-lockscreen") and not v["no-lockscreen"]:
            guai.append("KWin SENZA --no-lockscreen (kscreenlocker blocca)")
        if serve("inibito") and not v["inibito"]:
            s = v.get("spegni-schermo-s")
            if not _spento_o_lungo(s):
                guai.append("powerdevil NON inibito e schermo spento dopo %s s" % s)
    elif d == "xfce":
        if serve("dpms-enabled") and v["dpms-enabled"]:
            for k in ("dpms-on-ac-sleep", "dpms-on-ac-off"):
                if not _spento_o_lungo(v.get(k), 60):
                    guai.append("DPMS acceso, %s=%s min" % (k, v.get(k)))
        if serve("inactivity-on-ac") and not _spento_o_lungo(v["inactivity-on-ac"], 60):
            guai.append("inactivity-on-ac=%d min" % v["inactivity-on-ac"])
        if v.get("blank-on-ac") is not None and not _spento_o_lungo(v["blank-on-ac"], 60):
            guai.append("blank-on-ac=%d min" % v["blank-on-ac"])
    elif d == "lxqt":
        if serve("enableIdlenessWatcher") and v["enableIdlenessWatcher"]:
            guai.append("il sorvegliante d'inattivita' di LXQt e' ACCESO (%s s)"
                        % v.get("idle-s", "?"))
    if v.get("bloccatori"):
        guai.append("bloccatori accesi come l'inquilino: %s" % v["bloccatori"])
    return guai


def col_guasto_300(d, v):
    """Il GUASTO A: il tempo principale del desktop portato a 300 s."""
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
    """(ok, frase) di UNA foto contro quella d'inizio."""
    guai = []
    area0 = rif["ciano"] + rif["giallo"]
    area = m["ciano"] + m["giallo"]
    if area < 0.5 * area0:
        guai.append("finestra nota %.3f → %.3f" % (area0, area))
    if abs(m["lum"] - rif["lum"]) > 25:
        guai.append("luminanza %.0f → %.0f" % (rif["lum"], m["lum"]))
    if m["vivi"] < 0.5 * rif["vivi"]:
        guai.append("pixel non neri %.3f → %.3f" % (rif["vivi"], m["vivi"]))
    frase = "c %.3f g %.3f lum %.0f vivi %.3f" % (m["ciano"], m["giallo"], m["lum"], m["vivi"])
    return (not guai), (frase if not guai else "; ".join(guai))


def colore_di(m):
    if m["ciano"] > 2 * m["giallo"] and m["ciano"] > 0.005:
        return "ciano"
    if m["giallo"] > 2 * m["ciano"] and m["giallo"] > 0.005:
        return "giallo"
    return None


def giudica_serie(rif, serie):
    """serie = [(t, misura)].  Torna (esito, frase)."""
    cattive = []
    colori = set()
    for t, m in serie:
        ok, f = giudica_foto(rif, m)
        if not ok:
            cattive.append("a %d s: %s" % (t, f))
        c = colore_di(m)
        if c:
            colori.add(c)
    if cattive:
        return S.ROSSO, "lo schermo NON e' piu' il desktop — " + " · ".join(cattive)
    if len(colori) < 2:
        return S.ROSSO, ("immagine CONGELATA: la finestra nota non ha mai cambiato colore "
                         "(visti: %s)" % (sorted(colori) or "nessuno"))
    return S.VERDE, "%d foto, tutte il desktop, immagine viva (%s)" % (
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
        prova("%s: i valori della cura ⇒ niente difetti" % d, not giudica_tempi(d, v))
        prova("%s: GUASTO A (300 s) ⇒ difetto" % d, bool(giudica_tempi(d, col_guasto_300(d, v))))
        prova("%s: un campo non letto ⇒ difetto" % d,
              bool(giudica_tempi(d, {"bloccatori": ""})))
    prova("gnome: idle-delay 900 s ⇒ va bene", not giudica_tempi(
        "gnome", dict(buoni["gnome"], **{"idle-delay": 900})))
    prova("bloccatore acceso ⇒ difetto", bool(giudica_tempi(
        "lxqt", dict(buoni["lxqt"], bloccatori="swayidle"))))
    rif = {"ciano": 0.08, "giallo": 0.0, "lum": 90, "vivi": 0.9}
    g = {"ciano": 0.0, "giallo": 0.08, "lum": 95, "vivi": 0.9}
    prova("serie viva ⇒ VERDE", giudica_serie(rif, [(45, rif), (90, g)])[0] == S.VERDE)
    prova("serie congelata ⇒ ROSSO", giudica_serie(rif, [(45, rif), (90, rif)])[0] == S.ROSSO)
    nero = misura(G1B.png_nero(64, 36))
    prova("GUASTO B: tela nera in fondo ⇒ ROSSO",
          giudica_serie(rif, [(45, rif), (90, g), (135, nero)])[0] == S.ROSSO)
    xfce = {"ciano": 0.08, "giallo": 0.0, "lum": 22, "vivi": 0.12}
    prova("XFCE (sfondo nero): lo schermo spento si vede dai pixel non neri",
          not giudica_foto(xfce, dict(nero))[0])
    print("⛔ %d guai" % len(guai) if guai else "⭐ CERTIFICATO")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
#  I CAMPI, dentro la sessione
# ═══════════════════════════════════════════════════════════════════════════
def _num(t):
    m = re.search(r"-?\d+", t or "")
    return int(m.group(0)) if m else None


def _ultima(t):
    # ⚠ `[M]` 25 set 2026, kde: qdbus6/kreadconfig6 scrivono DOPO la risposta
    #   l'avviso della località («Detected locale "C"…»): non e' il valore
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
        grezzo.append("$ cmdline di kwin_wayland\n" + t)
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
        v["kscreenlocker (solo nota)"] = t
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
#  LA PROVA
# ═══════════════════════════════════════════════════════════════════════════
def corpo(o, E):
    d = o.scatola
    t_inizio = time.time()
    with S.Sessione(o, "030", E) as s:
        G1B.passo("inquilino e browser pronti")
        ok, m = s.entra()
        G1B.passo("dentro: %s" % m[:80])
        if not ok:
            raise S.Bloccata(m)
        time.sleep(6 if d != "kde" else 10)
        geo = s.geometria()
        W, H = geo["tl"], geo["ta"]
        c, t = G1B.metti_finestra(s)
        if c != 0:
            raise S.Bloccata("il programma della finestra non si scrive: " + t[-200:])
        c, t = G1B.apri_finestra(s, "orologio", "#00ffff", int(W * 0.3), int(H * 0.3),
                                 altro="#ffff00", periodo=7)
        if c != 0:
            raise S.Bloccata("la finestra nota non parte: " + t[-200:])
        time.sleep(5)
        if d == "gnome":
            G1B.fuoco_sulla_tela(s, geo)
            G1B.combinazione(s.g, ["Escape"])    # ⚠ GNOME nasce nella panoramica
            time.sleep(2)
        # ⛔ da qui NESSUN input: solo fotografie (CDP/Marionette non muovono niente)
        png0, p0 = G1B.foto(s, "inizio", scala=0.5)
        if not png0:
            raise S.Bloccata("nessuna foto d'inizio: " + p0)
        rif = misura(png0)
        for _ in range(6):                       # la finestra puo' tardare a nascere
            if rif["ciano"] + rif["giallo"] >= 0.01:
                break
            time.sleep(4)
            png0, p0 = G1B.foto(s, "inizio", scala=0.5)
            rif = misura(png0) if png0 else rif
        if rif["ciano"] + rif["giallo"] < 0.01:
            c, t = s.sc.dentro("cat /home/%s/.c15-python3.log 2>&1 | tail -5" % s.chi, 30)
            G1B.passo("registro della finestra: %s" % t[-400:])
            raise S.Bloccata("la finestra nota non si vede nella foto d'inizio (%s)" % rif)
        ev = [p0]
        v, grezzo = leggi_tempi(s, d)
        # l'attesa: il tetto e' di 10 minuti per TUTTA la prova
        attesa = min(o.attesa_s, max(60, 480 - int(time.time() - t_inizio)))
        print("   attesa senza input: %d s (foto ogni %d s)" % (attesa, o.ogni_s), flush=True)
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
        # ⭐ LA PROVA DI VITA, in fondo all'attesa: la finestra nota cambia colore
        #   ogni 7 s (era 30: `[M]` 24 set 2026, gnome, foto ogni ~60 s cadevano
        #   sulla stessa fase (`[M]` 24 set 2026, gnome: otto foto tutte gialle).
        #   ⇒ Si fotografa ogni 4 s, fino a 40 s, finche' il colore CAMBIA.
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
                print("   %4d s: prova di vita, %s → %s" % (trascorso, ultimo, colore_di(mm)),
                      flush=True)
                break
        v_fine, grezzo_fine = leggi_tempi(s, d)
        e_foto, f_foto = giudica_serie(rif, serie)
        guai = giudica_tempi(d, v)
        guai_fine = giudica_tempi(d, v_fine)
        ev.append(s.salva_testo("f030-campi.txt",
                                ["all'inizio: %s" % v, "alla fine: %s" % v_fine, ""]
                                + grezzo + ["", "--- alla fine ---"] + grezzo_fine))
        oss = "foto: %s · campi: %s" % (f_foto, v)
        atteso = ("%d s fermi senza input: ogni foto e' ancora il desktop, l'immagine e' viva; "
                  "inattivita'/DPMS/blocco spenti o > %d s" % (attesa, TETTO_S))
        if e_foto == S.ROSSO:
            E.metti("F-030", S.FAIL, f_foto, atteso=atteso, osservato=oss, evidenze=ev)
        elif guai or guai_fine:
            E.metti("F-030", S.FAIL, "le foto vanno, ma i campi no: %s"
                    % "; ".join(guai or guai_fine), atteso=atteso, osservato=oss, evidenze=ev)
        else:
            E.metti("F-030", S.PASS, "%s; campi giusti (%s)" % (f_foto, d), atteso=atteso,
                    osservato=oss, evidenze=ev)

        if o.guasto:
            ga = giudica_tempi(d, col_guasto_300(d, v))
            w, h = G1B.misura_png(png_ultima)
            serie_b = serie[:-1] + [(serie[-1][0] if serie else 0,
                                     misura(G1B.png_nero(w, h)))]
            eb, fb = giudica_serie(rif, serie_b)
            E.guasto("F-030", bool(ga) and eb == S.ROSSO,
                     "A) tempo a 300 s ⇒ %s · B) ultima foto nera ⇒ %s"
                     % ("ROSSO (%s)" % "; ".join(ga) if ga else "verde (NON visto)",
                        "ROSSO" if eb == S.ROSSO else "verde (NON visto)"))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica, extra=extra))
