#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f022 — THE THREE CLOCKS OF §5.3: F-022 silence · F-023 inactivity · F-024 abandonment

    python3 15-f022-orologi.py --scatola kde --browser chrome --guasto --porta 8612

⛔ A SERVER OF ITS OWN (`15-g7-server.sh`, ports 8611-8614): the clocks are shortened
   from the command line and the server is RESTARTED between one phase and the next — on the
   851x it cannot be done.  At the end the server stays on with the DEFAULTS.

THE REAL NAMES AND VALUES (read in the code, not in SPECIFICHE):
  · client silence: 30 s FIXED (`rcp.c` `#define SILENZIO 30000`, not
    configurable) — ⚠ but first the DEAD LINE fires at 10 s without a packet
    (`--linea-morta-silenzio-s`, default 10, `webtransport.c`): it is the one that
    detaches a mute client, and frees the slot.  ⇒ the expectation of F-022 is «detached
    WITHIN 30 s», whichever of the two does it, and the line says so;
  · user inactivity: `--inattivita-s` (default 1800), in SECONDS;
    it resets on EVERY RCP byte from the client (`rcp.c` ~7523), fires with
    `CONGEDO 0x02` and the line «§5.3 — INACTIVITY»; the graphical session STAYS;
  · session abandonment: `--abbandono-s` (default 3600); it feeds on the
    ONLY five input gestures (`main.c` `input_al_figlio` → `presenza_segna`),
    fires with the line «§5.3 — ABANDONMENT» and closes the graphical session with its
    programs (`figli_termina_sessione`).

F-022  (default server) the browser STOPS (SIGSTOP to the whole tree of
       processes: the client goes silent, like a laptop switching off) ⇒ expected: within
       30 s the server detaches it (line `linea-morta`/`DETACHED`/`slot LEFT`),
       the session stays (the tenant's programs alive), and with the browser resumed
       you come back in with user and password finding the same programs.
       FAULT: the browser does NOT stop ⇒ no detach in 35 s ⇒ the judge must
       say «not detached» (red).
F-023  (server with `--inattivita-s 12 --abbandono-s 45`) one click and then nothing ⇒
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

_s = _iu.spec_from_file_location("g7comune", os.path.join(S.QUI, "15-g7-comune.py"))
G7 = _iu.module_from_spec(_s)
_s.loader.exec_module(G7)
G7.scatola_locale(S)
_f = _iu.spec_from_file_location("f019", os.path.join(S.QUI, "15-f019-la-rete-cade.py"))
F019 = _iu.module_from_spec(_f)
_f.loader.exec_module(F019)

FUNZIONI = ("F-022", "F-023", "F-024")
SERVER = "15-g7-server.sh"
SILENZIO_S = 30
MARGINE_S = 15
# ⚠ 25 and not 12: `[M]` 25 Sep 2026 (D-011) the inactivity clock counts from the last
#   byte of the client, that is from the ATTACCA, even while the session IS BEING BORN; on XFCE
#   in 4K the birth exceeds 12 s ⇒ CONGEDO 0x02 one second after the first
#   frame.  With the real values (1800 s) it does not bite; here the clock must be kept
#   longer than the slowest birth.
INATTIVITA_S = 25
ABBANDONO_S = 60
FORME_STACCO = ("linea-morta", "DETACHED for silence", "slot LEFT")


def certifica():
    ok = True
    # the detach judge: a line of ANOTHER tenant does not count
    righe = ["21:00 rcp [c15022u111] slot LEFT by c15022u111 via x (taken now: 0)"]
    if giudica_stacco(righe, "c15022u222")[0]:
        print("⛔ the detach of another tenant counts as mine")
        ok = False
    if not giudica_stacco(righe, "c15022u111")[0]:
        print("⛔ the tenant's detach is not seen")
        ok = False
    for inatt, abb in ((12, 45), (1800, 3600)):
        if not (inatt + MARGINE_S < abb):
            print("⛔ the clocks tread on each other: inactivity %d, abandonment %d" % (inatt, abb))
            ok = False
    print("%s clock judges" % ("⭐" if ok else "⛔"))
    return 0 if ok else 1


def giudica_stacco(righe, chi):
    for r in righe:
        if chi not in r:
            continue
        for f in FORME_STACCO:
            if f in r:
                return True, r
    return False, None


def accendi(o, *opz):
    ok, t = G7.server("accendi", o.scatola, *opz)
    if not ok:
        raise S.Bloccata("our server does not start (%s): %s" % (" ".join(opz), t[-300:]))
    inatt, abb, riga = G7.orologi_in_vigore(o.scatola)
    print("   our server: inactivity %s s · abandonment %s s" % (inatt, abb), flush=True)
    return inatt, abb


JS_GEO = r"""
const t = document.getElementById('schermo');
const r = t ? t.getBoundingClientRect() : null;
const cs = t ? getComputedStyle(t) : null;
const reg = document.getElementById('registro');
return { rect: r ? [r.left, r.top, r.width, r.height] : null,
         display: cs ? cs.display : null, visibility: cs ? cs.visibility : null,
         buffer: t ? [t.width, t.height] : null,
         schermo: document.body.dataset.schermo || null,
         visibilita: document.visibilityState, fuoco: document.hasFocus(),
         finestra: [innerWidth, innerHeight, outerWidth, outerHeight, screenX, screenY],
         registro: reg ? reg.textContent.split('\n').filter(x => x.indexOf('audio:') !== 0).slice(-40) : [] };
"""


def _traccia(s):
    """G7_TRACCIA=1: every call to the browser with its time (diagnosis D-011)."""
    if os.environ.get("G7_TRACCIA") != "1" or getattr(s.g, "_tracciata", False):
        return
    s.g._tracciata = True
    for nome in ("js", "fotografa_tela"):
        vera = getattr(s.g, nome)

        def avvolta(*a, _v=vera, _n=nome):
            t0 = time.time()
            try:
                r = _v(*a)
                esito = "ok"
                return r
            except Exception as e:               # noqa: BLE001
                esito = "EXCEPTION %s" % str(e)[:80]
                raise
            finally:
                print("   ⏱ %s %s %.2f s %s · %s" % (time.strftime("%H:%M:%S"), _n,
                      time.time() - t0, esito, (str(a[0])[:50] if a else "")), flush=True)
        setattr(s.g, nome, avvolta)


def sessione_con_scena(s, reg=None, tetto_foto=None):
    segno = reg.righe() if reg else None
    _traccia(s)
    # ⛔⭐ D-011, the cause (25 Sep 2026, measured with G7_TRACCIA=1): on XFCE the
    #    background is BLACK and in 4K the pixel judge calls it «degenerate» ⇒
    #    `Prova.primo_fotogramma()` photographs for the WHOLE cap (45 s) and only
    #    at the end `desktop_scuro_ma_vivo` saves it.  With the inactivity
    #    clock shortened to 25 s, during those 45 s without a gesture the
    #    server says farewell (0x02, rightly), the page goes back to the form (canvas 16x16,
    #    display:none) and the next photo fails: the BLOCKED was the BENCH's.
    #    ⇒ In the short-clock phases the first frame is looked at with a
    #    cap shorter than the clock (`tetto_foto`), and the click arrives at once.
    vecchio = s.o.tetto_s
    if tetto_foto:
        s.o.tetto_s = min(vecchio, tetto_foto)
    try:
        ok, m = F019.entra_con_orecchio(s)
    finally:
        s.o.tetto_s = vecchio
    # ⚠ D-011, second reading (25 Sep 2026): on XFCE the photo of the first
    #   frame ~1 s after entering fails (Firefox: TakeScreenshot
    #   «Failure»; Chrome: canvas of area 0) — labwc's output is born 1280x720 and
    #   resizes AFTER the birth.  The CONGEDO 0x02 seen in the page was
    #   a CONSEQUENCE (the bench, having given up, touched nothing more for 25 s).
    #   ⇒ The canvas is looked at again for 15 s before giving up.
    riprove = 0
    if not ok:
        try:
            g0 = s.g.js(JS_GEO)
            g0.pop("registro", None)
        except Exception as e:                   # noqa: BLE001
            g0 = str(e)[:150]
        print("   ⚠ first frame not observable, the page AT ONCE: %s · %s"
              % (g0, str(G7.pagina(s.g).get("esito"))[:100]), flush=True)
    while not ok and "could not look at the" in m and riprove < 5:
        riprove += 1
        time.sleep(3)
        e, m2, st = s.pr.primo_fotogramma()
        e, m2 = S.C20V.desktop_scuro_ma_vivo(e, m2, st)
        ok, m = (e == S.VERDE), "the first frame (retry %d): %s" % (riprove, m2)
    if not ok:
        # ⛔ D-011 (25 Sep 2026): here the round said only «the canvas has no visible
        #    area» and the evidence of why vanished with the server restart.
        #    ⇒ Before giving up we photograph the STATE OF THE PAGE (what it
        #    says, whether it is still dressed as a desktop, its log) and the lines
        #    of the server for this tenant, and the page's sentence enters the
        #    reason of the BLOCKED.
        time.sleep(1)
        pag = G7.pagina(s.g)
        try:
            geo = s.g.js(JS_GEO)
        except Exception as e:                   # noqa: BLE001
            geo = {"errore": str(e)[:200]}
        pag["geometria"] = geo
        s.salva_testo("pagina-ingresso-fallito.txt",
                      "\n".join("%s: %s" % kv for kv in pag.items()))
        print("   ⚠ login failed, the page: %s" % geo, flush=True)
        if reg is not None and segno is not None:
            s.salva_testo("server-ingresso-fallito.txt", reg.da(segno, s.chi))
        s.salva_console()
        raise S.Bloccata("you cannot get in: %s · the page: outcome «%s», dressed=%s, form=%s"
                         % (m, (pag.get("esito") or "")[:120], pag.get("vestita"),
                            pag.get("modulo_visibile")))
    F019.clic_tela(s)                 # ⭐ the FIRST gesture: the abandonment clock starts
    t_gesto = time.time()
    pid, t = G7.lancia_scena(s)
    if not pid:
        raise S.Bloccata("the scene does not start: " + t)
    vista, t = G7.aspetta_scena(s, S)
    if not vista:
        raise S.Bloccata(t)
    return pid, t_gesto


# ─────────────────────────────────────────────────────────────────────────────
def fase_silenzio(o, E, reg):
    with S.Sessione(o, "022", E) as s:
        pid, _t = sessione_con_scena(s, reg)
        segno = reg.righe()
        fermati = G7.ferma_browser(s.g)
        t0 = time.time()
        try:
            forma, riga, dopo = reg.aspetta(segno, FORME_STACCO, s.chi,
                                            tetto=SILENZIO_S + 5, passo=1.0)
            vivi = G7.processi_inquilino(o.scatola, s.chi)
        finally:
            G7.riprendi_browser(s.g)
        print("   F-022: %d browser processes stopped · detach: %s after %.0f s"
              % (len(fermati), forma, dopo), flush=True)
        time.sleep(2)
        ok_r, come, mr = F019.rientra(s, 40)
        ps1 = G7.processi_inquilino(o.scatola, s.chi)
        ev = [s.salva_testo("server-f022.txt", reg.da(segno, s.chi)), s.salva_console()]
        atteso = ("browser stopped ⇒ detached within %d s (line linea-morta/DETACHED/slot "
                  "LEFT), session alive, you come back in with the previous programs" % SILENZIO_S)
        oss = ("detach: %s · programs alive during: %s · re-entry %s: %s (%s) · previous scene "
               "alive after: %s" % ((riga or "NONE")[:180], pid in vivi, come,
                                   "succeeded" if ok_r else "FAILED", mr[:100], pid in ps1))
        if not fermati:
            E.metti("F-022", S.BLOCKED, "I could not stop the browser (no pid)",
                    evidenze=ev)
        elif not forma:
            E.metti("F-022", S.FAIL, "the client has been silent for %d s and the server does NOT detach it"
                    % (SILENZIO_S + 5), atteso=atteso, osservato=oss, evidenze=ev)
        elif pid not in vivi or not ok_r or pid not in ps1:
            E.metti("F-022", S.FAIL, "detached, but the session is not found again: " + oss,
                    atteso=atteso, osservato=oss, evidenze=ev)
        else:
            E.metti("F-022", S.PASS, "detached after %.0f s by «%s», session found again"
                    % (dopo, forma), atteso=atteso, osservato=oss, evidenze=ev)
        if o.guasto:
            # FAULT: the browser does NOT stop — the judge must say «not detached»
            segno2 = reg.righe()
            forma2, riga2, dopo2 = reg.aspetta(segno2, FORME_STACCO, s.chi,
                                               tetto=SILENZIO_S + 5, passo=2.0)
            E.guasto("F-022", forma2 is None,
                     "browser alive ⇒ the judge %s" % ("sees no detach in %d s (red)"
                                                      % (SILENZIO_S + 5) if forma2 is None
                                                      else "sees a DETACH: " + riga2[:150]))


def fase_orologi(o, E, reg, corti):
    """corti=True: the healthy pass (F-023, F-024); False: the FAULT (long clocks)."""
    passata = "sana" if corti else "guasto"
    with S.Sessione(o, "022", E) as s:
        segno = reg.righe()
        # the first frame is looked at for less than the inactivity clock
        pid, t_gesto = sessione_con_scena(s, reg, tetto_foto=max(8, INATTIVITA_S - 10))
        # — F-023 —
        forma, riga, _d = reg.aspetta(segno, ["INACTIVITY"], s.chi,
                                      tetto=max(1, INATTIVITA_S + MARGINE_S - (time.time() - t_gesto)),
                                      passo=1.0)
        dopo = time.time() - t_gesto
        # the page has up to 10 s to say it (the CONGEDO arrives, then the form)
        pag = G7.pagina(s.g)
        for _ in range(10):
            if not forma or G7.la_pagina_lo_dice(pag):
                break
            time.sleep(1)
            pag = G7.pagina(s.g)
        vivi = G7.processi_inquilino(o.scatola, s.chi)
        detto = G7.la_pagina_lo_dice(pag)
        if not corti:
            E.guasto("F-023", forma is None,
                     "LONG clock ⇒ the judge %s" % (
                         "sees no INACTIVITY in %d s (red)" % (INATTIVITA_S + MARGINE_S)
                         if forma is None else "sees INACTIVITY: " + riga[:150]))
        else:
            ok_r, come, mr = (False, "", "not attempted")
            if forma:
                # you come back in ONLY with user and password: the page must not have
                # reconnected by itself
                da_se = bool(pag.get("sessione")) and pag.get("vestita") == "acceso" \
                    and not pag.get("modulo_visibile")
                ok_r, come, mr = F019.rientra(s, 40)
            ps1 = G7.processi_inquilino(o.scatola, s.chi)
            ev = [s.salva_testo("server-f023.txt", reg.da(segno, s.chi)),
                  s.salva_testo("pagina-f023.txt", "\n".join("%s: %s" % kv for kv in pag.items()))]
            atteso = ("one click, then nothing ⇒ between %d and %d s CONGEDO 0x02 (INACTIVITY line), the "
                      "page says it and goes back to the form, the programs stay, you come back in with "
                      "user and password" % (INATTIVITA_S, INATTIVITA_S + MARGINE_S))
            oss = ("line: %s · %.0f s after the click · page: outcome «%s» form %s dressed %s · "
                   "scene alive %s · re-entry %s: %s · scene alive after %s"
                   % ((riga or "NONE")[:120], dopo, (pag.get("esito") or "")[:90],
                      pag.get("modulo_visibile"), pag.get("vestita"), pid in vivi, come,
                      "succeeded" if ok_r else mr[:80], pid in ps1))
            if not forma:
                E.metti("F-023", S.FAIL, "no INACTIVITY within %d s of the last gesture"
                        % (INATTIVITA_S + MARGINE_S), atteso=atteso, osservato=oss, evidenze=ev)
            elif not detto:
                E.metti("F-023", S.FAIL, "detached for inactivity, but the page does not say it: "
                        + oss, atteso=atteso, osservato=oss, evidenze=ev)
            elif pid not in vivi or not ok_r or pid not in ps1:
                E.metti("F-023", S.FAIL, "after the inactivity the session is not found again: " + oss,
                        atteso=atteso, osservato=oss, evidenze=ev)
            elif da_se:
                E.metti("F-023", S.FAIL, "the page reconnected by itself (it should not have)",
                        atteso=atteso, osservato=oss, evidenze=ev)
            else:
                E.metti("F-023", S.PASS, "detached at %.0f s, page at the form with «%s», back in "
                        "with the password, scene found again" % (dopo, (pag.get("esito") or "")[:60]),
                        atteso=atteso, osservato=oss, evidenze=ev)
        # — F-024 — no gesture since the click: the abandonment
        resta = ABBANDONO_S + MARGINE_S - (time.time() - t_gesto)
        forma4, riga4, _d = reg.aspetta(segno, ["ABANDONMENT"], s.chi,
                                        tetto=max(1, resta), passo=2.0)
        dopo4 = time.time() - t_gesto
        time.sleep(4)
        ps4 = {}
        for _ in range(8):                        # the closing is not instantaneous
            ps4 = G7.processi_inquilino(o.scatola, s.chi)
            if pid not in ps4 and not (forma4 and ps4):
                break
            time.sleep(2)
        if not corti:
            rosso = forma4 is None and pid in ps4
            E.guasto("F-024", rosso,
                     "LONG clock ⇒ the judge %s" % (
                         "sees no ABANDONMENT in %d s and the scene is alive (red)"
                         % (ABBANDONO_S + MARGINE_S) if rosso
                         else "sees an ABANDONMENT (%s) or the scene gone (%s)"
                         % ((riga4 or "")[:100], pid not in ps4)))
            return
        ev = [s.salva_testo("server-f024.txt", reg.da(segno, s.chi)),
              s.salva_testo("processi-f024.txt", "\n".join("%d %s" % kv for kv in sorted(ps4.items())))]
        atteso = ("no gesture since the click ⇒ within %d s ABANDONMENT line and the session closes "
                  "with its programs (the tenant's processes gone)" % (ABBANDONO_S + MARGINE_S))
        oss = ("line: %s · %.0f s after the click · scene alive %s · tenant's processes left "
               "%d: %s" % ((riga4 or "NONE")[:120], dopo4, pid in ps4, len(ps4),
                           ", ".join(sorted(set(ps4.values())))[:200]))
        if not forma4:
            E.metti("F-024", S.FAIL, "no ABANDONMENT within %d s of the last gesture"
                    % (ABBANDONO_S + MARGINE_S), atteso=atteso, osservato=oss, evidenze=ev)
        elif pid in ps4 or _residui(s):
            oss += " · non-exempt (F-021's rule): %s" % ", ".join(_residui(s) or [])[:200]
            E.metti("F-024", S.FAIL, "ABANDONMENT written, but processes of the session remain: "
                    + oss, atteso=atteso, osservato=oss, evidenze=ev)
        else:
            E.metti("F-024", S.PASS, "abandonment at %.0f s after the click, no tenant process "
                    "left" % dopo4, atteso=atteso, osservato=oss, evidenze=ev)


def _residui(s):
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
    return m.residui(m.processi(s))


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
        print("   %s" % F019.server_pronto(o), flush=True)
        try:
            fase_silenzio(o, E, reg)
        except S.Bloccata as b:
            E.bloccate(["F-022"], str(b))
            if o.guasto:
                E.bloccate(["F-022"], str(b), passata="guasto")
        accendi(o, "--inattivita-s", str(INATTIVITA_S), "--abbandono-s", str(ABBANDONO_S))
        fase_orologi(o, E, reg, corti=True)
        if o.guasto:
            accendi(o)                                # the LONG ones: the defaults
            try:
                fase_orologi(o, E, reg, corti=False)
            except S.Bloccata as b:
                E.bloccate(["F-023", "F-024"], str(b), passata="guasto")
    finally:
        inatt, abb, _r = G7.orologi_in_vigore(o.scatola)
        if (inatt, abb) != (1800, 3600):
            G7.server("accendi", o.scatola)           # left with the defaults
        dopo_8511 = F019.sano_8511(o)
        print("   851x server before «%s» after «%s»%s" % (
            prima_8511, dopo_8511, "" if prima_8511 == dopo_8511 else "  ⛔ CHANGED"), flush=True)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
