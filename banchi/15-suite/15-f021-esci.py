#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f021 — F-021 «EXIT» FROM THE MENU: the session ends, the programs close,
          the page goes back to the form, no rebirth; and whoever comes back in opens
          a NEW, clean one

    python3 15-f021-esci.py --scatola lxqt --browser chrome [--guasto]

⭐ WHAT IT DOES, in a single session (tenant c15021u<n>), like the user:
   1  logs in from the real browser; inside the session opens a real PROGRAM
      (firefox-esr with C20's scene, its process is the witness)
   2  the «Exit» gesture (see GESTO, below) and the guard:
        F  the product declares the session ended (`C20.RIGHE_FINITA`)
        M  the PAGE goes back to the form (field `#modulo` visible) and the
           `#esito` line says «the session has ended» (`pagina.html` 0x10)
        P  the tenant's processes: none, except those in ESENTI
           (`ps -u`), and the program opened at point 1 is no longer there
        N  ⛔ for GUARDIA_S seconds after the end, in the server log
           no birth for this tenant («I AM MAKING IT BE BORN»,
           «negotiated format»): no rebirth
   3  a new login FROM THE SAME PAGE (if the form is not there: reload,
      and say so) ⇒ first frame, and
        R  NEW: the log says «I AM MAKING IT BE BORN» after the re-entry (a
           resumed session does not say it: the child finds it alive)
        C  CLEAN: the program of point 1 is not there
   Outcome: PASS only if F M P N R C.  A gesture that does not answer, a page
   that does not open ⇒ BLOCKED.

⚠ GESTURE — declared.  Not the click on the menu with the browser's mouse: it is the
  METHOD the «Exit» menu entry reaches, C20's table
  (`DESKTOP_E_GESTO`, the same as `12-c20-veri.py`, imported):
     GNOME  org.gnome.SessionManager.Logout(1)
     KDE    org.kde.Shutdown.logout
     XFCE   xfce4-session-logout --logout --fast
     LXQt   org.lxqt.session.logout
  Why: the menu is different in the four desktops (GNOME: three clicks and a
  dialog with a countdown; KDE: launcher, «Exit», confirmation; XFCE and
  LXQt: classic menu), and at 3840x2160 the entries would have to be FOUND in the
  photo — an image-recognition test, not an exit test.
  What the product sees (the compositor going away, the session
  manager closing) is the same: defect 6 of phase 14 (the
  rebirth on LXQt) was reproduced with this gesture (C24, 16 out of 20).

⛔ THE INJECTED FAULT (in the same session, after the healthy pass) — two, and
   BOTH must be seen:
   G1 «empty Exit»: instead of the gesture a harmless D-Bus call (GetId of the
      session bus, answers 0 and does nothing) ⇒ the session does NOT end
      ⇒ the judge MUST say FAIL (F, M, P red).
   G2 «re-entry inside the guard»: real «Exit», and as soon as the page is back
      at the form the bench comes back in AT ONCE ⇒ a session is born inside the
      GUARDIA_S window ⇒ the judge MUST say FAIL for rebirth (N).
      ⚠ It proves that the judge READS a birth after the end and calls it
      red; in the healthy pass the bench never comes back in inside the window
      ⇒ every birth that appears there is the product's.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

FUNZIONI = ("F-021",)


C20 = S.C20V.C20
RIGHE_FINITA = [p for p, _d in C20.RIGHE_FINITA]
NASCITE = ("I AM MAKING IT BE BORN", "negotiated format")
FRASE_PAGINA = "has ended"                       # pagina.html, MESSAGGI[0x10]
GUARDIA_S = 25.0
TETTO_FINITA = 60.0
TETTO_PROCESSI = 30.0
# ⭐ The tenant's processes that may remain after «Exit», and why —
#   judged by the CONTROL GROUP (/proc/<pid>/cgroup), not by the name:
#   remotix        the product's CHILD (runs with its uid, in the server's
#                  group): by design it stays, and the re-entry is born in it (I2;
#                  C24: «the second login is born in the surviving child»).
#   user@<uid>.service/…/*.service and init.scope   systemd's USER MANAGER
#                  and its services (dbus, pipewire, wireplumber…):
#                  they live as long as the user manager, which stays as long as logind
#                  has a session of the user — the child's.  The user did not
#                  open them and they are not the graphical session.
#   ⛔ THEY COUNT: everything in a `session-N.scope` (the desktop and the
#      programs it opened, LXQt/XFCE) and in an `app-*.scope` (the programs
#      opened by GNOME and KDE), and every other place.  The whole list is
#      in the «observed».
ESENTI = ("remotix",)


def esente(voce):
    """`voce` = «name|cgroup».  See ESENTI above — pure."""
    nome, _, cg = voce.partition("|")
    if nome in ESENTI:
        return True
    if "/user@" not in cg:
        return False
    foglia = cg.rstrip("/").rsplit("/", 1)[-1]
    return foglia == "init.scope" or (foglia.endswith(".service")
                                       and not foglia.startswith("app-"))


PROGRAMMA = "firefox-esr"
# ⚠ The server lines saying «the page's wire dropped» (rcp.c,
#   webtransport.c): with ten benches on the same server the parent's loop
#   stopped for up to 17 s (24 Sep, «fell behind by … ms»), and Chrome
#   closed the transport BEFORE «Exit» arrived.
FILO_CADUTO = ("the page CLOSED the WebTransport session", "DETACHED for silence")
GESTO_A_VUOTO = ("busctl --user call org.freedesktop.DBus /org/freedesktop/DBus "
                 "org.freedesktop.DBus GetId")


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES — pure
# ═══════════════════════════════════════════════════════════════════════════
def e_di(riga, chi):
    return ("[%s]" % chi) in riga or ("«%s»" % chi) in riga


def nascite_in(righe, chi):
    if righe is None:
        return None
    return [r for r in righe if e_di(r, chi) and any(n in r for n in NASCITE)]


def residui(voci):
    if voci is None:
        return None
    return sorted(v for v in voci if not esente(v))


def giudica_uscita(d):
    """⭐ (outcome, reason) of the exit from the measured fields:
         finita   the RIGHE_FINITA form seen, or None
         modulo   the form is visible in the page
         frase    the text of #esito
         rimasti  the tenant's non-exempt processes (list, or None)
         programma  the program of point 1 is still there
         nascite  the birth lines after the end (list, or None)
    ⛔ The rebirth is looked at BEFORE everything: in defect 6 the product says
       «it is over» and then makes it be born, and a green read on the end would be the
       defect slipping through."""
    if not d.get("finita") and d.get("filo_caduto") and not d.get("nascite"):
        # ⚠ the page's wire dropped BEFORE the end arrived: the
        #   product had nobody to tell it to, and the page could not
        #   hear it ⇒ I could not look (never a FAIL, never a PASS)
        return S.BLOCKED, ("the page's wire dropped before the end («%s»): "
                           "I could not look at the exit" % d["filo_caduto"][:140])
    muta = d.get("pagina_letta") is False and not d.get("nascite")
    guai = []
    if d.get("nascite"):
        guai.append("after «Exit» the session IS REBORN (%d lines; the first: %s)"
                    % (len(d["nascite"]), d["nascite"][0].strip()[:120]))
    if not d.get("finita"):
        guai.append("the product does not declare the session ended")
    if muta and d.get("finita") and not d.get("rimasti") and not d.get("programma"):
        return S.BLOCKED, ("the end is declared and the programs are closed, but the page "
                           "never answered the bench: I could not look at it")
    if not d.get("modulo"):
        guai.append("the page does NOT go back to the form")
    if FRASE_PAGINA not in (d.get("frase") or ""):
        guai.append("the page does not say «the session has ended» (it says «%s»)"
                    % (d.get("frase") or "")[:80])
    if d.get("programma"):
        guai.append("the program opened in the session (%s) is still alive" % PROGRAMMA)
    if d.get("rimasti"):
        guai.append("tenant's processes remain: %s" % " ".join(d["rimasti"])[:160])
    if guai:
        return S.FAIL, " · ".join(guai)
    if d.get("rimasti") is None or d.get("nascite") is None:
        return S.BLOCKED, "I could not read the processes or the log"
    return S.PASS, ("ended («%s»), the page at the form with «%s», no process "
                    "of the tenant (exempt: %s), no birth in %.0f s"
                    % (d["finita"], (d.get("frase") or "")[:60], "/".join(ESENTI),
                       d.get("guardia", GUARDIA_S)))


def giudica_rientro(d):
    """(outcome, reason) of the re-entry: got in, new (birth seen), clean."""
    if not d.get("entrato"):
        return S.FAIL, "after «Exit» you do NOT get back in: %s" % d.get("perche", "")
    guai = []
    if not d.get("nuova"):
        guai.append("the re-entry does not make a new session be born (no «I AM MAKING IT "
                    "BE BORN»: resumed?)")
    if d.get("programma"):
        guai.append("the re-entry's session is NOT clean: %s is still there%s" % (
            PROGRAMMA, (" — " + d["chi_lo_riapre"].splitlines()[0][:160])
            if d.get("chi_lo_riapre") else ""))
    if guai:
        return S.FAIL, " · ".join(guai)
    return S.PASS, "re-entry: NEW session («I AM MAKING IT BE BORN») and clean"


def certifica():
    guai = 0

    def p(nome, ottenuto, atteso):
        nonlocal guai
        ok = ottenuto == atteso
        guai += not ok
        print("  %s %-62s %s (expected %s)" % ("OK " if ok else "NO ", nome, ottenuto, atteso))

    buona = {"finita": "IS OVER", "modulo": True,
             "frase": "the session has ended: the programs were closed",
             "rimasti": [], "programma": False, "nascite": []}
    g = lambda **k: giudica_uscita(dict(buona, **k))[0]           # noqa: E731
    p("⭐ everything in order ⇒ PASS", g(), S.PASS)
    p("⛔ ended AND then reborn ⇒ FAIL", g(nascite=["figlio [c15021u1] I AM MAKING IT BE BORN"]),
      S.FAIL)
    p("⛔ not ended (empty Exit) ⇒ FAIL", g(finita=None, modulo=False, frase="Admitted",
                                             programma=True), S.FAIL)
    p("⛔ the page stays on the desktop ⇒ FAIL", g(modulo=False), S.FAIL)
    p("⛔ at the form but without the sentence ⇒ FAIL", g(frase="network error"), S.FAIL)
    p("⛔ a process left ⇒ FAIL", g(rimasti=["pcmanfm-qt"]), S.FAIL)
    p("⚠ wire dropped before the end ⇒ BLOCKED",
      g(finita=None, modulo=False, frase="", filo_caduto="the page CLOSED the WebTransport session"),
      S.BLOCKED)
    p("⛔ wire dropped BUT reborn ⇒ FAIL",
      g(finita=None, filo_caduto="x", nascite=["[c15021u1] I AM MAKING IT BE BORN"]), S.FAIL)
    p("⚠ the page does not answer the bench ⇒ BLOCKED",
      g(modulo=False, frase="", pagina_letta=False), S.BLOCKED)
    p("⛔ the page answers and is not at the form ⇒ FAIL",
      g(modulo=False, frase="", pagina_letta=True), S.FAIL)
    p("⚠ processes not read ⇒ BLOCKED, never PASS", g(rimasti=None), S.BLOCKED)
    p("⚠ log not read ⇒ BLOCKED, never PASS", g(nascite=None), S.BLOCKED)
    U = "0::/user.slice/user-4013.slice/user@4013.service"
    p("⭐ the child and the user manager do not count",
      residui(["remotix|0::/system.slice/rete11-server.service", "systemd|%s/init.scope" % U,
               "pipewire|%s/session.slice/pipewire.service" % U]), [])
    p("⛔ the desktop in the session scope counts",
      residui(["lxqt-panel|0::/user.slice/user-4013.slice/session-5.scope"]),
      ["lxqt-panel|0::/user.slice/user-4013.slice/session-5.scope"])
    p("⛔ a program opened by GNOME (app-*.scope) counts",
      len(residui(["firefox|%s/app.slice/app-gnome-firefox-12.scope" % U])), 1)
    p("⛔ a process without a readable group counts", residui(["x|"]), ["x|"])
    fin = ["figlio  [c15021u1] ⭐ ... I AM MAKING IT BE BORN (canvas 3840x2160)",
           "figlio  [c15021u10] I AM MAKING IT BE BORN", "cattura [c15021u1] negotiated format"]
    p("⚠ the births of c15021u10 are not c15021u1's", len(nascite_in(fin, "c15021u1")), 2)
    p("⭐ new and clean re-entry ⇒ PASS",
      giudica_rientro({"entrato": True, "nuova": True, "programma": False})[0], S.PASS)
    p("⛔ resumed re-entry ⇒ FAIL",
      giudica_rientro({"entrato": True, "nuova": False, "programma": False})[0], S.FAIL)
    p("⛔ re-entry with the previous program ⇒ FAIL",
      giudica_rientro({"entrato": True, "nuova": True, "programma": True})[0], S.FAIL)
    p("⛔ does not get back in ⇒ FAIL", giudica_rientro({"entrato": False})[0], S.FAIL)
    p("⭐ the forms of the end come from C20", len(RIGHE_FINITA), 2)

    # ⭐ reading the log: EMPTY is not NOT READ (round 1, gnome/firefox)
    class Finta:
        def __init__(self, uscita):
            self.uscita = uscita

        def dentro(self, _riga, _secondi=60):
            return (None, self.uscita) if self.uscita.startswith("(no answer") else (1, self.uscita)

    class FintaSessione:
        chi = "c15021u1"

        def __init__(self, uscita):
            self.sc = Finta(uscita)
    p("⭐ log read and empty (GNOME after «Exit») ⇒ [] and not None",
      registro(FintaSessione("@@fine"), 10), [])
    p("⭐ one line ⇒ the line", registro(FintaSessione(
        "x [c15021u1] I AM MAKING IT BE BORN\n@@fine"), 10), ["x [c15021u1] I AM MAKING IT BE BORN"])
    p("⚠ log not read ⇒ None", registro(FintaSessione("(no answer in 60 s)"), 10),
      None)
    d = dict(buona, nascite=nascite_in([], "c15021u1"))
    p("⭐ ⇒ and with the empty slice the exit is judgeable (PASS)", giudica_uscita(d)[0], S.PASS)
    print("⛔ %d wrong cases" % guai if guai else "⭐ the judges say what they must")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def _ritenta(f, volte=3):
    """⚠ The server belongs to ten benches: a read that does not answer is redone."""
    for _ in range(volte):
        v = f()
        if v is not None:
            return v
        time.sleep(2)
    return None


def registro(s, segno):
    """⭐ The tenant's lines from `segno` onwards: a LIST (even empty) if
    the log was read, None if not.

    ⛔ Not `s.registro_da(…) or None`: on GNOME, after «Exit», the child goes
       away and NOTHING more is written for the tenant ⇒ the slice is EMPTY, and
       it is an answer, not a silence.  As long as `Scatola.dentro` went through
       ssh the slice was never empty (there was sshpw's «password:» line) and
       the bench defect could not be seen; with the local `podman exec` (25 Sep)
       it could ⇒ BLOCKED on gnome/firefox in round 1 and in the clean-up.
       ⇒ The @@fine marker says the command got to the end."""
    def una():
        c, t = s.sc.dentro("tail -n +%d %s | grep -a -F -- '%s'; echo @@fine"
                           % (int(segno) + 1, S.C20V.REGISTRO, s.chi), 60)
        if "@@fine" not in (t or ""):
            return None
        return [r for r in t.split("@@fine")[0].splitlines()
                if r.strip() and "password:" not in r]
    return _ritenta(una)


def aspetta_il_bus(s, tetto=30):
    """⭐ The tenant's session bus is there (the socket /run/user/<uid>/bus):
    the «Exit» gesture talks to it.  ⛔ Right after a re-entry on GNOME the user
    manager may not have it yet ⇒ «Failed to connect to user scope bus»."""
    fine = time.time() + tetto
    while time.time() < fine:
        c, _t = s.sc.dentro("test -S /run/user/$(id -u %s)/bus" % s.chi, 20)
        if c == 0:
            return True
        time.sleep(1)
    return False


def fai_il_gesto(s, gesto, tetto=30):
    """(code, output) of the gesture; if the bus or the service are not there YET
    (session just born) it is retried up to `tetto`."""
    aspetta_il_bus(s, tetto)
    fine = time.time() + tetto
    while True:
        c, t = s.sc.come_utente(s.chi, gesto)
        if c == 0 or time.time() >= fine or not re.search(
                r"Failed to connect|No such file|ServiceUnknown|not provided|"
                r"was not provided by any \.service", t or ""):
            return c, t
        time.sleep(2)


def processi(s):
    """«name|cgroup» for every process of the tenant, or None."""
    def una():
        c, t = s.sc.dentro(
            "for p in $(pgrep -u %s); do printf '@@p %%s|%%s\\n' \"$(cat /proc/$p/comm "
            "2>/dev/null)\" \"$(head -1 /proc/$p/cgroup 2>/dev/null)\"; done; echo @@fine"
            % s.chi, 40)
        if "@@fine" not in (t or ""):
            return None
        return [x[4:].strip() for x in t.splitlines() if x.startswith("@@p ")
                and x[4:].strip() != "|"]
    return _ritenta(una)


def programma_vivo(s):
    c, _t = s.sc.dentro("pgrep -u %s -x %s >/dev/null" % (s.chi, PROGRAMMA), 30)
    return c == 0


def apri_programma(s):
    """firefox-esr with C20's scene, INSIDE the session (like C20)."""
    ok, t = s.sc.accendi_scena(s.chi)
    if not ok:
        return False, "the program does not open in the session: %s" % t[-160:]
    fine = time.time() + 20
    while time.time() < fine:
        if programma_vivo(s):
            time.sleep(3)                  # the window draws itself
            return True, "%s opened" % PROGRAMMA
        time.sleep(1)
    return False, "%s is not among the tenant's processes after 20 s" % PROGRAMMA


def leggi_pagina(s, tetto):
    """(form visible, sentence of #esito, read) waiting up to `tetto`.
    `letta` is False if the page NEVER answered the bench (browser
    stalled: `[M]` 25 Sep, Chrome under load 50, CDP «timed out»)."""
    fine = time.time() + tetto
    modulo, frase, letta = False, "", False
    while time.time() < fine:
        try:
            m = s.g.js(S.VERI.JS_MODULO)
            modulo = bool(m and m.get("modulo") and m.get("visibile"))
            st = s.stato()
            if "⛔" not in st:
                letta = True
                frase = st.get("esito") or ""
        except Exception:                        # noqa: BLE001
            modulo = False
        if modulo and FRASE_PAGINA in frase:
            break
        time.sleep(0.5)
    return modulo, frase, letta


def aspetta_finita(s, segno, tetto):
    fine = time.time() + tetto
    while time.time() < fine:
        for r in registro(s, segno) or []:
            for f in RIGHE_FINITA:
                if f in r and e_di(r, s.chi):
                    return f, r
        time.sleep(1)
    return None, None


def esci_e_guarda(s, gesto, tetto_finita=TETTO_FINITA, rientra_subito=False, nome="esci"):
    """The gesture and the four guards F M P N.  Returns (data, evidence) or
    raises Bloccata."""
    segno = _ritenta(s.segno_registro)
    if segno is None:
        raise S.Bloccata("I cannot read the server log")
    c, t = fai_il_gesto(s, gesto)
    if c != 0:
        raise S.Bloccata("the «Exit» gesture did not answer (code %s): %s" % (c, t[-200:]))
    t0 = time.time()
    finita, _r = aspetta_finita(s, segno, tetto_finita)
    d = {"finita": finita}
    if finita:
        d["finita_s"] = round(time.time() - t0, 1)
    segno_fine = (_ritenta(s.segno_registro) if finita else None) or segno
    d["modulo"], d["frase"], d["pagina_letta"] = leggi_pagina(s, 30 if finita else 5)
    if rientra_subito and d["modulo"]:
        # ⛔ G2: the bench comes back in INSIDE the guard
        e, m, _st = s.pr.entra(s.parola)
        d["rientro_guasto"] = "%s: %s" % ({S.VERDE: "admitted"}.get(e, "not admitted"), m[:80])
    # P — the processes: wait for them to go away, up to TETTO_PROCESSI
    fine = time.time() + (TETTO_PROCESSI if finita else 3)
    while True:
        nomi = processi(s)
        d["rimasti"] = residui(nomi)
        d["tutti"] = nomi
        d["programma"] = programma_vivo(s)
        if (d["rimasti"] == [] and not d["programma"]) or time.time() >= fine:
            break
        time.sleep(2)
    # N — the guard: ALL of it (the green is an absence)
    resto = GUARDIA_S - (time.time() - t0)
    if resto > 0:
        time.sleep(resto)
    d["guardia"] = time.time() - t0
    if not finita:
        tutta = registro(s, segno) or []
        d["filo_caduto"] = next((r.strip() for r in tutta if e_di(r, s.chi) and any(
            k in r for k in FILO_CADUTO)), None)
    fetta = registro(s, segno_fine)       # [] = read and empty (GNOME), None = not read
    d["nascite"] = nascite_in(fetta, s.chi)
    print("      [%s] mark %s→%s · slice %s lines · processes %s · births %s" % (
        nome, segno, segno_fine, None if fetta is None else len(fetta),
        None if d["rimasti"] is None else len(d["rimasti"]),
        None if d["nascite"] is None else len(d["nascite"])), flush=True)
    ev = [s.salva_testo("server-%s.txt" % nome, registro(s, segno) or ["(not read)"])]
    return d, ev


def rientra(s):
    """The new login from the same page: (data, evidence)."""
    segno = _ritenta(s.segno_registro)
    if segno is None:
        return {"entrato": False, "perche": "I cannot read the server log"}, []
    d = {"ricaricata": False}
    m = s.g.js(S.VERI.JS_MODULO)
    if not (m and m.get("modulo") and m.get("visibile")):
        d["ricaricata"] = True
        s.g.ricarica()
        ok, perche = s.pr.apri_dopo_ricarica()
        if not ok:
            return dict(d, entrato=False, perche="after the reload: " + perche), []
    ok, m = s.entra(apri=False)
    d["entrato"], d["perche"] = ok, m
    if not ok:
        return d, [s.salva_testo("server-rientro.txt", registro(s, segno) or [])]
    fetta = registro(s, segno) or []
    d["nuova"] = any("I AM MAKING IT BE BORN" in r and e_di(r, s.chi) for r in fetta)
    time.sleep(3)
    d["programma"] = programma_vivo(s)
    png, dove = s.foto("rientro")
    ev = [s.salva_testo("server-rientro.txt", fetta)] + ([dove] if dove else [])
    if d["programma"]:
        # ⭐ who reopened it?  the parent of the process and the desktop's
        #   session saving (KDE: ksmserverrc)
        _c, t = s.sc.dentro(
            "for p in $(pgrep -u %(c)s -x %(p)s); do pp=$(awk '{print $4}' /proc/$p/stat); "
            "echo \"$p padre $pp $(cat /proc/$pp/comm) · $(tr '\\0' ' ' < /proc/$p/cmdline "
            "| cut -c1-160)\"; done; echo ---; "
            "grep -A12 -i 'Session: saved' /home/%(c)s/.config/ksmserverrc 2>/dev/null "
            "| head -40" % {"c": s.chi, "p": PROGRAMMA}, 40)
        d["chi_lo_riapre"] = (t or "").strip()
        ev.append(s.salva_testo("rientro-programma-riaperto.txt", t or ""))
        print("   ⚠ %s reopened at the re-entry:\n%s" % (PROGRAMMA, (t or "")[:900]), flush=True)
    return d, ev


def rimetti_in_piedi(s):
    """A live session with the program open, to redo an exit."""
    r, _ev = rientra(s)
    if not r.get("entrato"):
        return False, "not getting back in: %s" % r.get("perche")
    return apri_programma(s)


def uscita(s, gesto, nome, **k):
    """An exit watched and judged; if the wire dropped before the end
    (BLOCKED), it is redone ONCE from a new session."""
    for tentativo in (1, 2):
        d, ev = esci_e_guarda(s, gesto, nome="%s-%d" % (nome, tentativo), **k)
        e, p = giudica_uscita(d)
        if not (e == S.BLOCKED and d.get("filo_caduto")) or tentativo == 2:
            break
        print("   ⚠ %s: %s — redoing it" % (nome, p), flush=True)
        ok, m = rimetti_in_piedi(s)
        if not ok:
            return d, ev, S.BLOCKED, p + " · and I could not redo it: " + m
    return d, ev, e, p


def corpo(o, E):
    with S.Sessione(o, "021", E) as s:
        desktop, gesto = s.sc.gesto_esci()
        if o.gesto:
            desktop, gesto = "%s (gesture given by hand)" % o.scatola, o.gesto
        if not gesto:
            raise S.Bloccata("I do not know how to say «Exit» in %s" % s.sc.contenitore)
        print("   «Exit» (%s): %s" % (desktop, gesto), flush=True)
        ok, m = s.entra()
        if not ok:
            raise S.Bloccata(m)
        ok, m = apri_programma(s)
        if not ok:
            raise S.Bloccata(m)
        png, dove = s.foto("prima-di-esci")
        ev0 = [dove] if dove else []

        # ── the healthy pass ───────────────────────────────────────────────
        d, ev, esito, perche = uscita(s, gesto, "esci")
        oss = ("ended=%s after %s s · form=%s · «%s» · processes after: %s · births=%d"
               % (d.get("finita"), d.get("finita_s"), d.get("modulo"),
                  (d.get("frase") or "")[:70],
                  " ".join(v.split("|")[0] for v in d.get("tutti") or []) or "none",
                  len(d.get("nascite") or [])))
        print("   exit: %s — %s" % (esito, oss), flush=True)
        ev.append(s.salva_testo("processi-dopo-esci.txt", d.get("tutti") or ["(none)"]))
        viva = False
        if esito == S.PASS:
            r, ev2 = rientra(s)
            viva = bool(r.get("entrato"))
            esito, p2 = giudica_rientro(r)
            perche = perche + " · " + p2 + (" (⚠ the form was not there: reloaded)"
                                             if r.get("ricaricata") else "")
            ev += ev2
            oss += " · re-entry: %s" % p2
        E.metti("F-021", esito, perche,
                atteso="«Exit» ⇒ ended, programs closed, page at the form with «the session "
                       "has ended», no birth in %.0f s; the re-entry opens a "
                       "NEW and clean session" % GUARDIA_S,
                osservato=oss, evidenze=ev0 + ev + [s.salva_console()],
                gesto=gesto)

        if not o.guasto:
            return
        # a live session to start from is needed.  ⛔ Not from the page's field
        #   (`R.schermo.sessione` can remain after the farewell): if the re-entry
        #   of the healthy pass did not happen, we come back in.  `[M]` 25 Sep, round 1
        #   and clean-up on gnome/firefox: without re-entry G1 talked to a bus
        #   that was no longer there ⇒ BLOCKED.
        if not viva:
            r, _ev = rientra(s)
            if not r.get("entrato"):
                E.guasto("F-021", None, "no live session for the fault: %s"
                         % r.get("perche"))
                return
        # ── G1 «empty Exit» ───────────────────────────────────────────────
        d1, _ev = esci_e_guarda(s, GESTO_A_VUOTO, tetto_finita=15, nome="guasto-a-vuoto")
        e1, p1 = giudica_uscita(d1)
        print("   G1 empty: %s — %s" % (e1, p1[:200]), flush=True)
        # ── G2 «re-entry inside the guard» ────────────────────────────────
        d2, _ev, e2, p2 = uscita(s, gesto, "guasto-rientro", rientra_subito=True)
        rinata = e2 == S.FAIL and bool(d2.get("nascite"))
        print("   G2 immediate re-entry (%s): %s — %s" % (d2.get("rientro_guasto"), e2, p2[:200]),
              flush=True)
        if not d2.get("finita") or "rientro_guasto" not in d2:
            E.guasto("F-021", None, "G2 not injected: the real exit did not end or "
                     "the page did not go back to the form (%s)" % p2[:200])
            return
        E.guasto("F-021", e1 == S.FAIL and rinata,
                 "G1 empty Exit ⇒ %s (%s) · G2 re-entry inside the guard ⇒ %s (%s)"
                 % (e1, p1[:120], e2, p2[:120]))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica, extra=lambda a: a.add_argument(
        "--gesto", default="", help="another «Exit» gesture (diagnosis: e.g. XFCE without "
        "--fast, which saves the session like the menu dialog)")))
