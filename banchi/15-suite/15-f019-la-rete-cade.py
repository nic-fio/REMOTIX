#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f019 — F-019 NETWORK LOSS AND RE-ENTRY · paths P-B and P-D

    python3 15-f019-la-rete-cade.py --scatola gnome --browser firefox --guasto --porta 8611

⛔ A SERVER OF ITS OWN: it runs against the box's SECOND product server
   (`15-g7-server.sh`, ports 8611-8614, DEFAULT clocks) — the line that
   drops is simulated with nftables and on the 851x everybody would see it.

⛔ THE SIMULATION, declared (decision taken for the suite): the line dies
   ON THE SERVER'S NETWORK — an nftables table of ours (`inet remotix_g7_<port>`)
   drops ALL the UDP of our server's port (QUIC/WebTransport), in both
   directions, for CADUTA_S seconds; then it is removed (always: even if the test falls over).
   ⚠ It is not the real path from the tablet (Wi-Fi, `wondershaper`): browser and
   server are on the same machine, and the HTTPS page (TCP) stays reachable.

THE REAL EXPECTATION, read in the code (not in the intentions):
  · the SERVER declares the line dead after 10 s without a packet
    (`--linea-morta-silenzio-s`, default 10: `webtransport.c`
    `linea_morta_giudica`, line `linea-morta … causa=silenzio`), closes the
    connection and FREES THE SLOT; the graphical session stays (I4);
  · re-entry is BY HAND (the user's decision of 23 Aug 2026, `main.c`
    `--niente-linea-morta`: «the wire drops and you come back in by hand»): the page does NOT
    reconnect by itself — there is no code that does it;
  · the PAGE must SAY IT (SPECIFICHE §8.2 and §3.2 of the page: «a mute wait
    is a fault»; `torna_al_modulo()` for every farewell): a visible sentence or the
    form back in view.  ⚠ In today's code the closing of the transport
    WITHOUT `CONGEDO` (that of the dead line: the `CONGEDO` cannot arrive on
    a line that does not carry) ends up in `nota()` — the hidden log — and that's all.

F-019  expected: the server writes `linea-morta` for the tenant; the page says it
       within OSSERVA_S of the line coming back (with a mouse movement, as
       whoever is in front would do); we come back in (from the form if it is there, otherwise
       by reloading: it is «by hand»); and the programs
       of the session are the SAME (pid).  ⚠ The sentence
       «resumed session» is not demanded: `rcp.c` ALWAYS sends `1 = NUOVA` in `SESSIONE`
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

_s = _iu.spec_from_file_location("g7comune", os.path.join(S.QUI, "15-g7-comune.py"))
G7 = _iu.module_from_spec(_s)
_s.loader.exec_module(G7)
G7.scatola_locale(S)

FUNZIONI = ("F-019", "P-B", "P-D")
SERVER = "15-g7-server.sh"
CADUTA_S = 20          # the dead line; the server declares it at 10 s
OSSERVA_S = 60         # after the line comes back: how long to wait for the page to say it
TETTO_RIENTRO_S = 40


def extra(a):
    a.add_argument("--caduta-s", type=int, default=CADUTA_S)
    a.add_argument("--osserva-s", type=int, default=OSSERVA_S)


def certifica():
    ok = True
    lm = G7.LineaMorta(8611)
    r = lm.regole()
    for atteso in ("table inet remotix_g7_8611", "udp dport 8611 counter drop",
                   "udp sport 8611 counter drop", "hook input", "hook output"):
        if atteso not in r:
            print("⛔ the rule does not have «%s»" % atteso)
            ok = False
    try:
        G7.LineaMorta(8511)
        print("⛔ the dead line accepts 8511 (everybody's)")
        ok = False
    except AssertionError:
        print("⭐ the dead line refuses the ports that are not ours")
    casi = [({"esito_visibile": True, "esito_classe": "male", "vestita": "acceso"}, True),
            ({"esito_visibile": False, "modulo_visibile": True, "vestita": None}, True),
            ({"esito_visibile": False, "modulo_visibile": False, "vestita": "acceso"}, False),
            ({"esito_visibile": True, "esito_classe": "bene", "vestita": "acceso"}, False),
            ({"errore": "x"}, None)]
    for st, att in casi:
        v = G7.la_pagina_lo_dice(st)
        if v is not att:
            print("⛔ la_pagina_lo_dice(%s) = %s, expected %s" % (st, v, att))
            ok = False
    print("%s nft rules and page judge" % ("⭐" if ok else "⛔"))
    return 0 if ok else 1


# ─────────────────────────────────────────────────────────────────────────────
def server_pronto(o):
    """Our server on and with the DEFAULT clocks; if not, it starts it."""
    inatt, abb, riga = G7.orologi_in_vigore(o.scatola)
    c, t = G7.dentro(o.scatola, "systemctl is-active rete15-g7", 30)
    if (t or "").strip() == "active" and inatt == 1800 and abb == 3600:
        return "our server already on, default clocks"
    ok, t = G7.server("accendi", o.scatola)
    if not ok:
        raise S.Bloccata("our server does not start: %s" % t[-300:])
    return t.splitlines()[0] if t else "on"


def sano_8511(o):
    """⛔ Everybody's server (851x) must stay the previous one: pid and active."""
    c, t = G7.dentro(o.scatola, "systemctl is-active rete11-server; "
                     "systemctl show -p MainPID --value rete11-server", 30)
    return " ".join((t or "").split())


def clic_tela(s):
    """A click at the centre of the canvas: it is the user's gesture that unblocks
    the browser's audio (autoplay) — without it, the AudioContext stays suspended."""
    st = s.stato()
    x, y = s.pr.centro(st, 0.5, 0.5)
    s.g.clic(x, y)
    time.sleep(0.5)
    return x, y


def entra_con_orecchio(s):
    ok, m = s.pr.apri()
    if not ok:
        return False, "the page does not open: " + m
    G7.orecchio(s.g)
    ok, m = s.entra(apri=False)
    return ok, m


def rientra(s, tetto):
    """The re-entry «by hand»: from the form if the page put it back in view,
    otherwise by reloading (what whoever looks at a frozen desktop would do).
    Returns (ok, how, outcome)."""
    st = G7.pagina(s.g)
    come = "from the form back in view"
    if not (st.get("modulo_visibile") and not st.get("vestita")):
        come = "by reloading the page (the form was not there)"
        ok, m = s.pr.apri()
        if not ok:
            return False, come, "the page does not reopen: " + m
    G7.orecchio(s.g)
    vecchio = s.o.tetto_s
    s.o.tetto_s = tetto
    try:
        e, m, st2 = s.pr.entra(s.parola)
        # ⚠ `[M]` 24 Sep 2026, server with load ~50: the server's loop falls
        #   behind by up to 13 s and the CIAO expires (0x0D «timed out during the
        #   handshake»).  Whoever is in front retries: we retry ONCE, and
        #   it is written.
        if e != S.VERDE and "handshake" in (m or ""):
            come += " (retried once after «%s»)" % m[:60]
            ok, m0 = s.pr.apri()
            G7.orecchio(s.g)
            e, m, st2 = s.pr.entra(s.parola)
    finally:
        s.o.tetto_s = vecchio
    if e != S.VERDE:
        return False, come, m
    e2, m2, _ = s.pr.primo_fotogramma()
    e2, m2 = S.C20V.desktop_scuro_ma_vivo(e2, m2, _)
    return e2 == S.VERDE, come, "%s · %s" % (m, m2)


def caduta(s, o, reg, lm, osserva_s, togli=True, durante=None):
    """The line dies for `o.caduta_s`; `durante()` is called halfway.
    Returns a dictionary with the facts seen."""
    f = {"linea_morta": None, "detto": None, "detto_dopo_s": None, "scartati": 0}
    segno = reg.righe()
    lm.metti()
    t0 = time.time()
    try:
        chiamato = False
        while time.time() - t0 < o.caduta_s:
            if durante and not chiamato and time.time() - t0 > o.caduta_s / 3:
                durante()
                chiamato = True
            st = G7.pagina(s.g)
            if f["detto"] is None and G7.la_pagina_lo_dice(st):
                f["detto"], f["detto_dopo_s"] = st, time.time() - t0
            time.sleep(2)
        f["scartati"] = lm.contati()
        forma, riga, _ = reg.aspetta(segno, ["linea-morta"], s.chi, tetto=2)
        f["linea_morta"] = riga
    finally:
        if togli:
            f["tolta"] = lm.togli()
    if not togli:
        return f
    # the line came back: whoever is in front moves the mouse and looks
    t1 = time.time()
    mosso = 0
    while time.time() - t1 < osserva_s and f["detto"] is None:
        try:
            st0 = s.stato()
            x, y = s.pr.centro(st0, 0.3 + 0.1 * (mosso % 4), 0.5)
            s.g.muovi(x, y)
            mosso += 1
        except Exception:                        # noqa: BLE001
            pass
        st = G7.pagina(s.g)
        if G7.la_pagina_lo_dice(st):
            f["detto"], f["detto_dopo_s"] = st, time.time() - t0
            break
        time.sleep(3)
    f["ultima_pagina"] = G7.pagina(s.g)
    f["mossi"] = mosso
    if f["linea_morta"] is None:
        _f, riga, _ = reg.aspetta(segno, ["linea-morta"], s.chi, tetto=2)
        f["linea_morta"] = riga
    f["segno"] = segno
    return f


def corpo(o, E):
    if not o.porta:
        o.porta = G7.PORTE_G7[o.scatola]
        o.url = "https://%s:%d/" % (o.host, o.porta)
    if o.porta != G7.PORTE_G7[o.scatola]:
            raise S.Bloccata("port %d is not our server's (%d)"
                         % (o.porta, G7.PORTE_G7[o.scatola]))
    print("   %s" % server_pronto(o), flush=True)
    prima_8511 = sano_8511(o)
    reg = G7.Registro(o.scatola)
    lm = G7.LineaMorta(o.porta)
    lm.togli()
    ev_srv = []
    try:
        with S.Sessione(o, "019", E) as s:
            segno0 = reg.righe()
            ok, m = entra_con_orecchio(s)
            if not ok:
                raise S.Bloccata("you cannot get in even with a healthy line: " + m)
            print("   in: %s" % m, flush=True)
            clic_tela(s)
            pid_scena, t = G7.lancia_scena(s)
            print("   %s" % t, flush=True)
            if not pid_scena:
                raise S.Bloccata("the scene does not start: " + t)
            c, t = G7.lancia_tono(s)
            vista, t = G7.aspetta_scena(s, S)
            if not vista:
                raise S.Bloccata("before the drop: " + t)
            time.sleep(3)
            ps0 = G7.processi_inquilino(o.scatola, s.chi)
            pid_tono = [p for p, n in ps0.items() if n.startswith("pw-play")]
            rms0, d0 = G7.ascolta(s.g, 3)
            mossa0, dm0, ev0 = G7.la_scena_si_muove(s, "prima")
            print("   before: scene %s (%s) · sound RMS %s %s · %d processes"
                  % (mossa0, dm0, rms0, d0, len(ps0)), flush=True)

            # ═══ THE HEALTHY DROP ═════════════════════════════════════════
            f = caduta(s, o, reg, lm, o.osserva_s)
            print("   drop: %d packets dropped · linea-morta: %s · said: %s"
                  % (f["scartati"], bool(f["linea_morta"]),
                     ("after %.0f s" % f["detto_dopo_s"]) if f["detto"] else "NO"), flush=True)
            if f["scartati"] == 0:
                raise S.Bloccata("the nft rule dropped nothing: the line did not die")
            ok_r, come, mr = rientra(s, TETTO_RIENTRO_S)
            print("   re-entry %s: %s — %s" % (come, ok_r, mr[:200]), flush=True)
            if ok_r:
                clic_tela(s)
            time.sleep(4)
            ps1 = G7.processi_inquilino(o.scatola, s.chi)
            mossa1, dm1, ev1 = G7.la_scena_si_muove(s, "dopo")
            rms1, d1 = G7.ascolta(s.g, 3)
            ev_srv.append(s.salva_testo("server-f019-sana.txt", reg.da(segno0, s.chi)))
            ev_pag = s.salva_testo("pagina-dopo-caduta.txt", "\n".join(
                "%s: %s" % (k, v) for k, v in (f.get("ultima_pagina") or {}).items()))
            # ⚠ pw-play's pid changes at every turn of the loop (a 5 s file):
            #   the session's state is judged on the scene's pid.
            stessi = pid_scena in ps1
            ripresa = "resumed" in mr
            ev = ev0 + ev1 + ev_srv + [ev_pag, s.salva_console()]

            # F-019
            osservato = ("linea-morta from the server: %s · the page: %s · re-entry %s: %s · "
                         "the page writes «resumed session»: %s (⚠ rcp.c always sends "
                         "1=NUOVA) · previous programs alive: %s"
                         % ("yes" if f["linea_morta"] else "NO",
                            ("it says so after %.0f s: «%s»" % (f["detto_dopo_s"],
                                                           (f["detto"].get("esito") or "")[:100]))
                            if f["detto"] else
                            ("it does NOT say so: %d s after the line came back (and %d mouse "
                             "movements) the page is still dressed as a desktop, frozen, outcome "
                             "«%s»" % (o.osserva_s, f.get("mossi", 0),
                                      (f["ultima_pagina"].get("esito") or "")[:80])),
                            come, "succeeded" if ok_r else "FAILED", ripresa, stessi))
            atteso = ("linea-morta in the log; the page says it (sentence or form) within "
                      "%d s of the return; you come back in by hand; «resumed session» with the "
                      "previous programs" % o.osserva_s)
            if not f["linea_morta"]:
                E.metti("F-019", S.FAIL, "the server did not declare the line dead in %d s"
                        % o.caduta_s, atteso=atteso, osservato=osservato, evidenze=ev)
            elif not ok_r or not stessi:
                E.metti("F-019", S.FAIL, "after the drop the session is not found again: " + osservato,
                        atteso=atteso, osservato=osservato, evidenze=ev)
            elif not f["detto"]:
                E.metti("F-019", S.FAIL, "the wire drops and the page does NOT say it: frozen desktop "
                        "without a word (you come back in only by reloading on your own initiative)",
                        atteso=atteso, osservato=osservato, evidenze=ev)
            else:
                E.metti("F-019", S.PASS, osservato, atteso=atteso, osservato=osservato,
                        evidenze=ev)

            # P-B
            atteso_b = "after the re-entry the scene moves in the photos, same process as before"
            if not ok_r:
                E.metti("P-B", S.FAIL, "no getting back in: " + mr[:200], atteso=atteso_b,
                        osservato=mr[:200], evidenze=ev)
            elif mossa1 is None:
                E.metti("P-B", S.BLOCKED, "photos not judgeable: " + dm1, evidenze=ev)
            elif mossa1 and pid_scena in ps1:
                E.metti("P-B", S.PASS, "scene alive after the re-entry (%s), pid %d" % (dm1, pid_scena),
                        atteso=atteso_b, osservato=dm1, evidenze=ev)
            else:
                E.metti("P-B", S.FAIL, "after the re-entry the scene is still or gone (%s, pid alive %s)"
                        % (dm1, pid_scena in ps1), atteso=atteso_b, osservato=dm1, evidenze=ev)

            # P-D
            atteso_d = "after the re-entry moving photos AND sound played not silence (RMS > %.2f)" \
                % G7.SOGLIA_RMS
            if rms0 is None or rms0 < G7.SOGLIA_RMS:
                E.metti("P-D", S.BLOCKED, "the sound was not arriving even BEFORE the drop "
                        "(RMS %s, %s): I have no «before» to find again" % (rms0, d0), evidenze=ev)
            elif not ok_r:
                E.metti("P-D", S.FAIL, "no getting back in: " + mr[:200], atteso=atteso_d, evidenze=ev)
            elif mossa1 and rms1 is not None and rms1 >= G7.SOGLIA_RMS:
                E.metti("P-D", S.PASS, "after the re-entry video alive (%s) and sound RMS %.3f (before %.3f)"
                        % (dm1, rms1, rms0), atteso=atteso_d,
                        osservato="RMS %.3f · %s" % (rms1, d1), evidenze=ev)
            else:
                E.metti("P-D", S.FAIL, "after the re-entry: video %s (%s), sound RMS %s (%s)"
                        % (mossa1, dm1, rms1, d1), atteso=atteso_d, evidenze=ev)

            if not o.guasto:
                return
            # ═══ THE FAULT: the state is lost AND the line stays dead ═════
            if not ok_r:
                E.guasto("F-019", None, "the healthy pass did not come back in: nothing to break")
                E.guasto("P-B", None, "same")
                E.guasto("P-D", None, "same")
                return
            vittime = [pid_scena] + pid_tono

            def uccidi():
                G7.dentro(o.scatola, "pkill -KILL -u %s -f 'pw-play|weston-simple-egl'; "
                          "kill -KILL %s 2>/dev/null; true"
                          % (s.chi, " ".join(str(p) for p in vittime)), 30)
            f2 = caduta(s, o, reg, lm, 0, togli=False, durante=uccidi)
            try:
                ok_g, come_g, mg = rientra(s, 30)          # line STILL dead
            finally:
                lm.togli()
            E.guasto("F-019", not ok_g, "re-entry with the line still dead ⇒ %s (%s)"
                     % ("NO getting back in: " + mg[:120] if not ok_g else "BACK IN?!", come_g))
            ok_r2, come2, mr2 = rientra(s, TETTO_RIENTRO_S)
            if not ok_r2:
                E.guasto("P-B", None, "after the fault you can no longer get back in: " + mr2[:150])
                E.guasto("P-D", None, "same")
                return
            clic_tela(s)
            time.sleep(4)
            ps2 = G7.processi_inquilino(o.scatola, s.chi)
            mossa2, dm2, _e = G7.la_scena_si_muove(s, "guasto")
            rms2, d2 = G7.ascolta(s.g, 3)
            s.salva_testo("server-f019-guasto.txt", reg.da(f2.get("segno") or segno0, s.chi))
            vivo = pid_scena in ps2
            pb_rosso = not (mossa2 and vivo)
            E.guasto("P-B", pb_rosso if mossa2 is not None else None,
                     "scene killed during the drop ⇒ P-B's judge says %s (%s, pid alive %s)"
                     % ("red" if pb_rosso else "VERDE", dm2, vivo))
            pd_rosso = not (mossa2 and rms2 is not None and rms2 >= G7.SOGLIA_RMS)
            E.guasto("P-D", pd_rosso, "scene and tone killed ⇒ P-D's judge says %s "
                     "(video %s, RMS %s)" % ("red" if pd_rosso else "VERDE", mossa2, rms2))
    finally:
        tolta = lm.togli()
        dopo_8511 = sano_8511(o)
        print("   nft rule removed: %s · 851x server before «%s» after «%s»%s"
              % (tolta, prima_8511, dopo_8511,
                 "" if prima_8511 == dopo_8511 else "  ⛔ CHANGED"), flush=True)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica, extra=extra))
