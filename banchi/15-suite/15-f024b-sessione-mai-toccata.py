#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f024b — F-024b: A SESSION OPENED AND NEVER TOUCHED EXPIRES BY ABANDONMENT (§5.3)

    python3 15-f024b-sessione-mai-toccata.py --scatola kde --browser firefox --guasto --porta 8612

⭐ IT WATCHES DEFECT D-004.  The abandonment clock (`--abbandono-s`,
   default 3600) fed ONLY on the five input gestures: `main.c`
   `input_al_figlio` → `presenza_segna`.  A session in which nobody ever
   moved the mouse or pressed a key did not enter the presence table,
   and ⛔ never expired — against `SPECIFICHE.md` §5.3, «60 minutes without input ⇒
   the session closes».  F-024 (in `15-f022-orologi.py`) does not see it: it makes a
   click to unblock the audio, and the click puts the user in the table.
   The cure (clean-up D-004): the clock starts at the stage's BIRTH.

⛔ A SERVER OF ITS OWN (`15-g7-server.sh`, ports 8611-8614), like F-022/23/24: the clock
   is shortened from the command line.  At the end the server stays with the DEFAULTS.

F-024b (server with `--abbandono-s 60`, default inactivity) you log in with the
       real browser and DO NOTHING: no click, no key, no
       scene launched ⇒ expected: within ABBANDONO_S + MARGINE_S of the login the
       tenant's «§5.3 — ABANDONMENT» line, and then the session DISAPPEARS: the
       compositor (gnome-shell / kwin_wayland / labwc) is no longer there, and of the
       tenant's processes only the exempt ones of F-021's rule remain
       (the `remotix` child and systemd's user manager with its services).
       FAULT: the LONG clock (the default, 3600 s), same sequence ⇒
       no ABANDONMENT in the same window and the session alive ⇒ the judge
       must say red.

⛔⛔ «NO GESTURE» IS VERIFIED, not presumed.  The bench makes none: the login
     (`Prova.entra`) fills in and sends the form from JavaScript, the first
     frame is judged with photos (`fotografa_tela`), and the photos do not
     go through the pointer.  ⚠ But a browser can generate pointer events
     by itself (a synthetic `mousemove` after a layout change, with
     labwc's pointer still over the window), and the page would forward them to the
     server as `PUNTATORE` — that is as a gesture, which renews the clock.
     ⇒ The tenant's `input id=` lines in the server log are COUNTED
       (`rcp.c`, one for every message of the five types of the input channel,
       the same set that feeds `presenza_segna`).  If there is even ONE the
       premise has fallen and the outcome is BLOCKED with the line — not a FAIL of the
       product and not a PASS.
"""
import importlib.util as _iu
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

_s = _iu.spec_from_file_location("g7comune", os.path.join(S.QUI, "15-g7-comune.py"))
G7 = _iu.module_from_spec(_s)
_s.loader.exec_module(G7)
G7.scatola_locale(S)
_f = _iu.spec_from_file_location("f019", os.path.join(S.QUI, "15-f019-la-rete-cade.py"))
F019 = _iu.module_from_spec(_f)
_f.loader.exec_module(F019)

FUNZIONI = ("F-024b",)
SERVER = "15-g7-server.sh"
PER_BROWSER = False
ABBANDONO_S = 60
MARGINE_S = 30          # the clock's turn + the stage's birth before the login
CHIUSURA_S = 40         # the closing of the graphical session is not instantaneous
FORMA_ABBANDONO = "§5.3 — ABANDONMENT"
FORMA_GESTO = "input id="
# ⭐ The HEART of the session: the compositor.  ⚠ F-021's rule alone is not
#   enough: on GNOME the Shell is a service of the user manager
#   (`org.gnome.Shell@wayland.service`), that is EXEMPT for that rule ⇒ the
#   live session would have zero non-exempt processes, and «closed» would be true
#   by force.  The compositor is there on all four (the same list as F-016).
CUORI = ("gnome-shell", "kwin_wayland", "labwc")


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES (pure: --certifica tests them)
# ═══════════════════════════════════════════════════════════════════════════
def righe_di(righe, chi):
    """The lines naming the tenant.  ⛔ The name is looked for whole: a
    tenant c15024u11 must not take the lines of c15024u111."""
    fuori = []
    for r in righe:
        i = r.find(chi)
        while i >= 0:
            if not r[i + len(chi):i + len(chi) + 1].isdigit():
                fuori.append(r)
                break
            i = r.find(chi, i + 1)
    return fuori


def trova_abbandono(righe, chi):
    for r in righe_di(righe, chi):
        if FORMA_ABBANDONO in r:
            return r
    return None


def gesti(righe, chi):
    return [r for r in righe_di(righe, chi) if FORMA_GESTO in r]


def cuore(ps):
    """«name pid» of the compositors among the processes {pid: name}; None if unreadable."""
    if ps is None:
        return None
    return ["%s %d" % (n, p) for p, n in sorted(ps.items()) if n in CUORI]


def giudica(d):
    """(outcome, reason) from the measured fields:
         nati      the tenant's compositor AFTER the first frame
                   («name pid», list; empty = the session was not seen being born)
         gesti     the tenant's `input id=` lines (list)
         abbandono the ABANDONMENT line, or None
         cuore     the compositor at the end (list, or None = unreadable)
         rimasti   the non-exempt processes at the end (list, or None = unreadable)
    ⛔ The order matters: first the premise (session born, no gesture), then the
       product's facts."""
    if not d.get("nati"):
        return S.BLOCKED, ("the session was not seen being born (no %s compositor "
                           "of the tenant after the first frame): there is nothing that "
                           "can expire" % "/".join(CUORI))
    if d.get("gesti"):
        return S.BLOCKED, ("the premise has fallen: %d gestures that the bench did not make "
                           "reached the server (the first: %s) — they renew the clock"
                           % (len(d["gesti"]), d["gesti"][0][:160]))
    if d.get("rimasti") is None or d.get("cuore") is None:
        return S.BLOCKED, "I could not read the tenant's processes"
    if not d.get("abbandono"):
        return S.FAIL, ("no ABANDONMENT within %d s of a login without any gesture "
                        "(compositor at the end: %s)"
                        % (ABBANDONO_S + MARGINE_S, ", ".join(d["cuore"]) or "gone"))
    if d["cuore"] or d["rimasti"]:
        return S.FAIL, ("ABANDONMENT written, but the session did not close: compositor "
                        "%s · non-exempt %s" % (", ".join(d["cuore"]) or "gone",
                                                ", ".join(d["rimasti"])[:180] or "none"))
    return S.PASS, ("abandonment without any gesture: compositor gone, no non-exempt "
                    "process left")


def certifica():
    ok = True

    def prova(nome, vero):
        nonlocal ok
        if not vero:
            print("⛔ " + nome)
            ok = False

    chi = "c15024u111"
    ab = "21:00 avvio ⭐ §5.3 — ABANDONMENT: «%s» has touched nothing for 61000 ms (ceiling 60000)"
    gesto = "21:00 rcp [%s] input id=3 (was 2) PUNTATORE 10,10 · client instant 1 us"
    prova("the tenant's ABANDONMENT is seen", trova_abbandono([ab % chi], chi))
    prova("the ABANDONMENT of ANOTHER tenant does not count",
          trova_abbandono([ab % "c15024u222"], chi) is None)
    prova("the ABANDONMENT of a longer name does not count",
          trova_abbandono([ab % "c15024u1110"], chi) is None)
    prova("a gesture of the tenant is counted", len(gesti([gesto % chi], chi)) == 1)
    prova("a gesture of another is not counted", not gesti([gesto % "c15024u222"], chi))
    prova("the heart is read from the processes",
          cuore({1: "bash", 9: "kwin_wayland"}) == ["kwin_wayland 9"]
          and cuore({1: "bash"}) == [] and cuore(None) is None)
    viva = ["labwc 4242"]
    base = {"nati": viva, "gesti": [], "abbandono": ab % chi, "cuore": [], "rimasti": []}
    prova("abandonment, compositor gone, nothing left ⇒ PASS",
          giudica(base)[0] == S.PASS)
    prova("no abandonment ⇒ FAIL (the defect D-004)",
          giudica(dict(base, abbandono=None, cuore=viva))[0] == S.FAIL)
    prova("no abandonment on GNOME (zero non-exempt, the Shell is a service) ⇒ FAIL",
          giudica(dict(base, abbandono=None, cuore=["gnome-shell 7"]))[0] == S.FAIL)
    prova("abandonment but compositor alive ⇒ FAIL", giudica(dict(base, cuore=viva))[0] == S.FAIL)
    prova("abandonment but non-exempt processes left ⇒ FAIL",
          giudica(dict(base, rimasti=["xfce4-panel|0::/user.slice/x/session-5.scope"]))[0]
          == S.FAIL)
    prova("a gesture not made by the bench ⇒ BLOCKED, neither PASS nor FAIL",
          giudica(dict(base, gesti=[gesto % chi]))[0] == S.BLOCKED)
    prova("session never born ⇒ BLOCKED (it would be «closed» by force)",
          giudica(dict(base, nati=[]))[0] == S.BLOCKED)
    prova("unreadable processes ⇒ BLOCKED",
          giudica(dict(base, rimasti=None))[0] == S.BLOCKED
          and giudica(dict(base, cuore=None))[0] == S.BLOCKED)
    prova("the short clock and the wait stay below the default",
          ABBANDONO_S + MARGINE_S + CHIUSURA_S < 3600)
    print("%s F-024b judges" % ("⭐" if ok else "⛔"))
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def _f021():
    sp = _iu.spec_from_file_location("f021", os.path.join(S.QUI, "15-f021-esci.py"))
    m = _iu.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def accendi(o, *opz):
    ok, t = G7.server("accendi", o.scatola, *opz)
    if not ok:
        raise S.Bloccata("our server does not start (%s): %s" % (" ".join(opz), t[-300:]))
    inatt, abb, _r = G7.orologi_in_vigore(o.scatola)
    print("   our server: inactivity %s s · abandonment %s s" % (inatt, abb), flush=True)
    return abb


def passata(o, E, reg, corta):
    """corta=True: the healthy pass; False: the FAULT (the long clock)."""
    F021 = _f021()
    with S.Sessione(o, "024", E) as s:
        segno = reg.righe()
        # ⛔ NO GESTURE: no `clic_tela`, no scene, no keys.  You
        #    just log in (form filled in from JavaScript, first frame
        #    judged with photos).
        ok, m = s.entra()
        if not ok:
            raise S.Bloccata("you cannot get in: " + m)
        t_accesso = time.time()
        nati = cuore(G7.processi_inquilino(o.scatola, s.chi)) or []
        # the wait: the ABANDONMENT line, within abandonment + margin of the login
        forma, riga, _d = reg.aspetta(segno, [FORMA_ABBANDONO], s.chi,
                                      tetto=ABBANDONO_S + MARGINE_S, passo=2.0)
        dopo = time.time() - t_accesso
        # the closing: the compositor and the non-exempt processes must disappear
        fine = time.time() + (CHIUSURA_S if forma else 0)
        while True:
            cuore_ora = cuore(G7.processi_inquilino(o.scatola, s.chi))
            rimasti = F021.residui(F021.processi(s))
            if (not cuore_ora and not rimasti) or time.time() >= fine:
                break
            time.sleep(2)
        righe = reg.da(segno, s.chi)
        pag = G7.pagina(s.g)
        d = {"nati": nati, "gesti": gesti(righe, s.chi),
             "abbandono": trova_abbandono(righe, s.chi), "cuore": cuore_ora,
             "rimasti": rimasti}
        esito, ragione = giudica(d)
        if not corta:
            if esito == S.BLOCKED:
                E.bloccate(["F-024b"], "pass with the fault: " + ragione, passata="guasto")
                return
            rosso = esito == S.FAIL and not d["abbandono"]
            E.guasto("F-024b", rosso,
                     "LONG clock ⇒ the judge %s" % (
                         "sees no ABANDONMENT in %d s and the session is alive (red)"
                         % (ABBANDONO_S + MARGINE_S) if rosso
                         else "says %s: %s" % (esito, ragione[:150])))
            return
        ev = [s.salva_testo("server-f024b.txt", righe),
              s.salva_testo("processi-f024b.txt",
                            "compositor at birth:\n%s\ncompositor at the end:\n%s\n"
                            "non-exempt at the end:\n%s"
                            % ("\n".join(nati), "\n".join(cuore_ora or ["(none)"]),
                               "\n".join(rimasti or ["(none or unreadable)"]))),
              s.salva_testo("pagina-f024b.txt",
                            "\n".join("%s: %s" % kv for kv in pag.items()))]
        atteso = ("login and then NO gesture ⇒ within %d s the «§5.3 — ABANDONMENT» line and the "
                  "session closes (compositor gone, non-exempt gone: rule of "
                  "F-021)" % (ABBANDONO_S + MARGINE_S))
        oss = ("line: %s · %.0f s after the login · gestures that reached the server %d · compositor "
               "at birth %s, at the end %s · non-exempt at the end %s · page: «%s»"
               % ((riga or "NONE")[:140], dopo, len(d["gesti"]), ", ".join(nati),
                  ", ".join(cuore_ora or []) or "gone",
                  "?" if rimasti is None else len(rimasti), (pag.get("esito") or "")[:80]))
        E.metti("F-024b", esito, ragione, atteso=atteso, osservato=oss, evidenze=ev)


def corpo(o, E):
    if not o.porta:
        o.porta = G7.PORTE_G7[o.scatola]
        o.url = "https://%s:%d/" % (o.host, o.porta)
    if o.porta != G7.PORTE_G7[o.scatola]:
        raise S.Bloccata("port %d is not our server's (%d)"
                         % (o.porta, G7.PORTE_G7[o.scatola]))
    prima_8511 = F019.sano_8511(o)
    reg = G7.Registro(o.scatola)
    try:
        if accendi(o, "--abbandono-s", str(ABBANDONO_S)) != ABBANDONO_S:
            raise S.Bloccata("the abandonment clock is not the one requested (%d s)"
                             % ABBANDONO_S)
        passata(o, E, reg, corta=True)
        if o.guasto:
            try:
                accendi(o)                            # the LONG one: the default
                passata(o, E, reg, corta=False)
            except S.Bloccata as b:
                E.bloccate(["F-024b"], str(b), passata="guasto")
    finally:
        inatt, abb, _r = G7.orologi_in_vigore(o.scatola)
        if (inatt, abb) != (1800, 3600):
            G7.server("accendi", o.scatola)           # left with the defaults
        dopo_8511 = F019.sano_8511(o)
        print("   851x server before «%s» after «%s»%s" % (
            prima_8511, dopo_8511, "" if prima_8511 == dopo_8511 else "  ⛔ CHANGED"), flush=True)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
