#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
16-controllo-corto — THE SHORT FUNCTIONAL CHECK OF A LEVEL (phase 16, §7)
===========================================================================

    (on the server, as nicfio, in the environment of 15-una.sh: WAYLAND_DISPLAY of
     ITS OWN compositor — 16-compositori.sh u00 — and REMOTIX_SUL_SERVER=1)
    python3 16-controllo-corto.py --scatola lxqt --livello 4 \\
        --dir /media/REMOTIX/misure/fase16/<campagna>/livello-04 \\
        --browser chrome --porte-base 9900 [--largo 3840 --alto 2160]

WHAT IT DOES — a NEW SESSION, its own, inside the loaded level:
  tenant `c16<livello>u99` (born here, cleared out on exit), a real
  browser (the one asked for: the climb alternates them between levels), and in a row, like
  a user who arrives:
    birth    access → first frame, timed (§7 «birth of a
             new user», §9: ≤ 5 s GREEN, 5–15 DEGRADED, > 15 or refusal FAIL)
    F-004    the mouse, REDUCED: movement, left click, drag
             (the scene of 15-g2-scena.py, the judges of 15-f004)
    F-007    the special keys: the sequence of 15-f007 (Enter, Backspace,
             arrows, Tab, Esc) in the same scene
    F-003    the image, REDUCED: the test window OPENS and its
             counter CHANGES (photos no older than 1 s for 6 s) — the
             judges of 15-f003; no drag and no judged closing
    F-014    the clipboard browser → session: the scene and the judge of 15-f014
  ⇒ writes DIR/controllo-corto.json and the evidence in DIR/controllo-corto/.

  --guasto  (the test of the check, §13.2; NOT in the climb) after the healthy
            pass, in the same session, every judge receives FALSE evidence
            and must give red: F-004 gestures into nothing · F-007 the sequence without
            Esc · F-003 the photo from BEFORE (opening and counter) · F-014 copy
            not done + expected without accents.  In controllo-corto.json:
            «guasti» and «esito_guasto» (PASS = all seen); «esiti» stays the
            healthy pass only.

⭐ WHY A SESSION OF ITS OWN, and not an actor's (proposal, fasi/16 §7):
  - every actor has ITS OWN browser (Marionette/CDP on a single port): getting into it
    from outside would mean two masters on the same browser, and the gesture of one
    would spoil the work of the other — the level's measurement would get dirty;
  - the phase 15 tests are written for a `suite.Sessione`: with a
    session of its own they are REUSED as they are (scenes, judges, retries), without
    rewriting them against the work of an actor who meanwhile clicks elsewhere;
  - it is also the measurement that §7 asks for separately: the BIRTH of a new user
    with the server already loaded with N users;
  - the price: for a few minutes the level has N+1 sessions.  It is declared
    (`sessioni_durante`), and it is within the cap (16) up to step 15.
    ⚠ At step 16 the check is the 17th: the climb raises the cap to 17
    for the campaign's box (16-salita.py --tetto), and says so.

Exit code: 0 all PASS · 1 at least one FAIL · 3 at least one BLOCKED and
no FAIL.  One `SUITE {...}` line per function, like the suite.
"""
import datetime
import json
import os
import re
import sys
import time
import traceback

QUI = os.path.dirname(os.path.abspath(__file__))
SUITE = os.path.join(os.path.dirname(QUI), "15-suite")
sys.path.insert(0, SUITE)
import suite as S                                                     # noqa: E402

# ⭐ the phase 15 tests, IMPORTED (not copied)
F003 = S._carica("f003", os.path.join(SUITE, "15-f003-lo-schermo-si-aggiorna.py"))
F004 = S._carica("f004", os.path.join(SUITE, "15-f004-il-mouse.py"))
F007 = S._carica("f007", os.path.join(SUITE, "15-f007-tasti-speciali.py"))
F014 = S._carica("f014", os.path.join(SUITE, "15-f014-appunti.py"))
G2 = F004.G2
C21 = S.C21

# ⛔ the phase 16 tenants are called c16<nnn>u<n>: the suite accepts only
#   its own (c15…).  The network clear-out (`^c[0-9]+b?u[0-9]+$`) recognises them.
S.MODELLO_INQUILINO = re.compile(r"^c1[56][0-9]{3}u[0-9]+$")

FUNZIONI = ("F-004", "F-007", "F-003", "F-014")
GESTI_RIDOTTI = ("movimento", "clic-sinistro", "trascinamento")
UTENTE_CONTROLLO = 99
TETTO_NASCITA_S = 90            # beyond: FAIL «no first frame» (§9: > 15 s is already FAIL)


def adesso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def extra(a):
    a.add_argument("--dir", required=True, help="the level folder (livello-NN)")
    a.add_argument("--livello", type=int, required=True)
    a.add_argument("--utente", type=int, default=UTENTE_CONTROLLO,
                   help="the number of the tenant c16<livello>u<utente> (99)")
    a.add_argument("--solo", default="", help="only these functions (F-004,F-003…): tests of the bench")


# ═══════════════════════════════════════════════════════════════════════════
#  THE BIRTH, timed
# ═══════════════════════════════════════════════════════════════════════════
def nasci(s, o):
    """Page → form → admission → first frame, with the times.
    Returns (ok, reason, times)."""
    t = {}
    t0 = time.time()
    ok, m = s.pr.apri()
    t["pagina_s"] = round(time.time() - t0, 2)
    if not ok:
        return False, "the page does not open: " + m, t
    t1 = time.time()
    e, m, _st = s.pr.entra(s.parola)
    t["ammissione_s"] = round(time.time() - t1, 2)
    if e != S.VERDE:
        t["rifiuto"] = bool(s.pr.rifiuto)
        return False, "the access: " + m, t
    # ⭐ access → first PAINTED frame: the page's counter, read
    #   closely; then the (non-degenerate) photograph is taken by `primo_fotogramma`.
    fine = t1 + TETTO_NASCITA_S
    while time.time() < fine:
        st = s.pr.stato() or {}
        if (st.get("dipinti") or 0) > 0:
            t["nascita_s"] = round(time.time() - t1, 2)
            break
        time.sleep(0.2)
    if "nascita_s" not in t:
        return False, "no painted frame %d s after the access" % TETTO_NASCITA_S, t
    e, m, st = s.pr.primo_fotogramma()
    e, m = S.C20V.desktop_scuro_ma_vivo(e, m, st)
    t["primo_non_degenere_s"] = round(time.time() - t1, 2)
    if e != S.VERDE:
        return False, "the first frame: " + m, t
    return True, m, t


def aspetta_tela(s):
    """The canvas of the wanted size (the rule of F-011), as in 15-f003."""
    cw, ch, dpr = s.g.js("const d=document.documentElement; "
                         "return [d.clientWidth, d.clientHeight, devicePixelRatio||1];")
    attesa = F003.F011.tela_attesa(cw, ch, dpr)
    fine = time.time() + 40
    geo = None
    while time.time() < fine:
        geo = s.geometria()
        if geo and [geo.get("tl"), geo.get("ta")] == attesa:
            return geo, ""
        time.sleep(1)
    if not geo:
        return None, "`REMOTIX_PUNTATORE.geometria` is not there"
    return None, "the canvas is %sx%s and not %dx%d after 40 s" % (geo.get("tl"), geo.get("ta"),
                                                           attesa[0], attesa[1])


def via_le_scene(s):
    """The session's test applications go away (the scene of G2, the
    window of F-003): the next function starts from a clean desktop."""
    s.sc.dentro("pkill -KILL -u %s -f '[f]irefox-esr' 2>/dev/null; "
                "pkill -KILL -u %s -f '[g]2-servitore' 2>/dev/null; sleep 1; true"
                % (s.chi, s.chi), 30)


# ═══════════════════════════════════════════════════════════════════════════
#  THE FOUR FUNCTIONS, reduced — the judges are those of phase 15
# ═══════════════════════════════════════════════════════════════════════════
def f004_f007(o, E, s, t_nascita):
    """The scene of G2 only once, then the reduced gestures and the keys."""
    ok_n, m_n = True, "already entered"
    vero_entra = s.entra
    s.entra = lambda *a, **k: (ok_n, m_n)          # G2.prepara does not re-enter: we are inside
    try:
        sc, mp, _geo, dove = G2.prepara(s, o.porte_base + 5)
    finally:
        s.entra = vero_entra
    ev0 = [dove] if dove else []
    if "F-004" in o.funzioni:
        F004.GESTI = GESTI_RIDOTTI
        righe = F004.passata(s, sc, mp, False)
        es = [r[1] for r in righe]
        oss = " · ".join("%s: %s %s" % (n, e, m) for n, e, m, _ in righe)
        ev = ev0 + [x for r in righe for x in r[3]]
        atteso = "movement on the BLUE block where it points, click on the GREEN counted, box moved"
        if S.FAIL in es:
            E.metti("F-004", S.FAIL, "red gestures: " + ", ".join(
                n for n, e, _m, _ in righe if e == S.FAIL), atteso=atteso, osservato=oss,
                evidenze=ev + [s.salva_console()])
        elif S.BLOCKED in es:
            E.metti("F-004", S.BLOCKED, "gestures not looked at: " + ", ".join(
                "%s (%s)" % (n, m) for n, e, m, _ in righe if e == S.BLOCKED),
                atteso=atteso, osservato=oss, evidenze=ev)
        else:
            E.metti("F-004", S.PASS, "%d gestures of %d (reduced): the effect is there "
                    "in the application" % (len(righe), len(righe)), atteso=atteso,
                    osservato=oss, evidenze=ev)
        if o.guasto:
            # ⭐ the fault of 15-f004: every gesture INTO NOTHING, same judge ⇒ all red
            righe = F004.passata(s, sc, mp, True)
            visto = F004.esito_col_guasto([r[1] for r in righe])
            E.guasto("F-004", visto, {True: "every gesture into nothing gave red",
                                      False: "gestures into nothing GREEN anyway: " + ", ".join(
                                          n for n, e, _m, _ in righe if e == S.PASS),
                                      None: "a gesture into nothing could not be looked at"}[visto],
                     osservato=" · ".join("%s: %s %s" % (n, e, m) for n, e, m, _ in righe))
    if "F-007" in o.funzioni:
        st, foto, perche = F007.batti(s, sc, mp, F007.SEQUENZA, "tasti")
        if perche:
            E.metti("F-007", S.BLOCKED, perche)
        else:
            e, m = F007.giudica(st, F007.ATTESO)
            if e == S.FAIL:
                print("   ⚠ red (%s): doing it again to confirm it" % m, flush=True)
                st2, foto2, perche2 = F007.batti(s, sc, mp, F007.SEQUENZA, "tasti-bis")
                e2, m2 = F007.giudica(st2, F007.ATTESO) if not perche2 else (S.BLOCKED, perche2)
                if e2 == S.PASS:
                    e, m = S.PASS, "⚠ RED at the first attempt (%s), green at the second" % m
                else:
                    m = "red twice: %s · %s" % (m, m2)
                foto = foto2 or foto
            E.metti("F-007", e, m, atteso="a=%r b=%r" % F007.ATTESO, osservato=m,
                    evidenze=[x for x in (foto,) if x])
        if o.guasto:
            # ⭐ the fault of 15-f007: the same sequence WITHOUT the Esc ⇒ «b» does not empty
            passi = F007.senza(F007.SEQUENZA, F007.GUASTO_TOGLIE)
            st, foto, perche = F007.batti(s, sc, mp, passi, "tasti-guasto")
            if perche:
                E.guasto("F-007", None, perche)
            else:
                eg, mg = F007.giudica(st, F007.ATTESO)
                E.guasto("F-007", None if eg == S.BLOCKED else eg == S.FAIL,
                         "without %s: %s" % (F007.GUASTO_TOGLIE, mg), osservato=mg,
                         evidenze=[foto] if foto else [])


def f003(o, E, s):
    """Opens and changes, from the PHOTOGRAPH (the judges of 15-f003)."""
    geo, perche = aspetta_tela(s)
    if not geo:
        raise S.Bloccata(perche)
    time.sleep(1.5)
    _p, im0, _a, _b = F003.foto_im(s, "f003-prima")
    if im0 is None:
        raise S.Bloccata("the canvas cannot be photographed")
    q0 = F003.frazione_ciano(im0)
    if q0 >= F003.CIANO_ASSENTE:
        raise S.Bloccata("before opening there is already some cyan (%.2f %%)" % (100 * q0))
    largo_f, alto_f = geo["tl"] * 0.45, geo["ta"] * 0.55
    c, t = F003.prepara_la_casa(s, largo_f, alto_f)
    if c != 0:
        raise S.Bloccata("the home cannot be prepared: %s" % (t or "")[-200:])
    ok, t = C21.accendi_la_finestra(s.sc, s.chi)
    if not ok:
        raise S.Bloccata("firefox-esr does not start: %s" % (t or "")[-200:])
    t_ap = time.time()
    f1, im1 = F003.aspetta_ferma(s, F003.APERTURA_S, "f003-aperta")
    parti, guasti = [], []
    if not f1:
        _p, im_x, _a, _b = F003.foto_im(s, "f003-apertura-non-vista")
        nuovo = F003.cambiato(im0, im_x) if im_x is not None else 0.0
        if not F003.processo_vivo(s):
            parti.append(("apre", S.BLOCKED, "firefox-esr did not stay alive: %s" % im1))
        elif nuovo > F003.CAMBIATO_MIN:
            parti.append(("apre", S.BLOCKED, "the photo changed (%.1f %%) but does not show the "
                          "test page" % (100 * nuovo)))
        else:
            parti.append(("apre", S.FAIL, "firefox-esr alive for %.0f s and the photo is IDENTICAL to "
                          "the one before: the screen does not update" % (time.time() - t_ap)))
    else:
        pw, _ph = f1["foto"]
        largo_foto = largo_f * geo["sx"] * pw / geo["bw"]
        e, m = F003.giudica_apertura(f1, largo_foto)
        if e == S.FAIL:
            e, m = S.BLOCKED, "the cyan is not as wide as the requested window: a preview?"
        parti.append(("apre", e, m + " (in %.1f s)" % (time.time() - t_ap)))
        # ⭐ fault «apre»: the photo from BEFORE the opening given to the judge
        f0, _ = F003.trova(im0)
        guasti.append(("apre", F003.giudica_apertura(f0, largo_foto)))
        if e == S.PASS:
            v0, mv = F003.leggi_contatore(im1, f1["rett"])
            if v0 is None:
                parti.append(("cambia", S.BLOCKED, "the counter cannot be read: %s" % mv))
            else:
                serie = []
                for giro in range(2):               # a red is confirmed, as in 15-f003
                    letture, prima_im = [], None
                    t_via = time.time()
                    while (time.time() - t_via < F003.RAPIDI_S or len(letture) < F003.FOTO_MIN) \
                            and time.time() - t_via < F003.RAPIDI_MAX_S:
                        _png, im, tp, td = F003.foto_im(s)
                        if im is None:
                            continue
                        n, mn = F003.leggi_contatore(im, f1["rett"])
                        letture.append((tp, td, n, mn))
                        prima_im = prima_im or im
                    e, m, righe = F003.giudica_rapidi(letture)
                    s.salva_testo("f003-rapide-%d.txt" % giro, righe)
                    serie.append((e, m, letture, prima_im))
                    print("   fast changes, series %d: %s %s" % (giro + 1, e, m), flush=True)
                    if e == S.PASS:
                        break
                e, m, letture, prima_im = serie[-1]
                if letture and prima_im is not None:
                    # ⭐ fault «cambia» (15-f003): the FIRST photo for all, with the real instants
                    n0, m0 = F003.leggi_contatore(prima_im, f1["rett"])
                    ge, gm, _ = F003.giudica_rapidi([(tp, td, n0, m0)
                                                     for tp, td, _n, _m in letture])
                    guasti.append(("cambia", (ge, gm)))
                if len(serie) > 1:
                    m = "series 1: %s %s · series 2: %s" % (serie[0][0], serie[0][1], m)
                parti.append(("cambia", e, m))
    via_le_scene(s)
    es = F003.complessivo(parti)
    testo = " · ".join("%s %s: %s" % p for p in parti)
    E.metti("F-003", es, testo if es != S.PASS else "opens and changes: the photos follow the "
            "screen (reduced: no drag)", atteso="the window opens in the photo; "
            "counter ≤ %.0f ms in every photo for %d s" % (F003.TETTO_MS, F003.RAPIDI_S),
            osservato=testo, evidenze=[o.evidenze], parti={p: [e, m] for p, e, m in parti})
    if o.guasto:
        if es != S.PASS:
            E.guasto("F-003", None, "the healthy pass is not green: the fault is judged only "
                     "on a healthy pass")
        else:
            visti = {p: r[0] == S.FAIL for p, r in guasti}
            E.guasto("F-003", len(visti) == 2 and all(visti.values()),
                     "photo from BEFORE ⇒ " + " · ".join("%s %s" % (p, "red" if r[0] == S.FAIL
                                                              else r[0]) for p, r in guasti),
                     osservato=" | ".join("%s: %s" % (p, r[1]) for p, r in guasti))


def f014(o, E, s):
    geo = s.geometria()
    if not geo:
        raise S.Bloccata("the canvas geometry is not there")
    g = s.g
    st = g.js(F014.STATO_APPUNTI)
    if not st or not st.get("acceso"):
        E.metti("F-014", S.FAIL, "the page's clipboard is not on: %s" % st)
        return
    scena = F014.Scena(s, o.porte_base + 5)
    try:
        ok, t = scena.accendi()
        if not ok:
            raise S.Bloccata("the clipboard scene does not start: %s" % (t or "")[-300:])
        time.sleep(3)
        x, y = C21.dal_desktop_al_vetro(geo, geo["tl"] * 0.5, geo["ta"] * 0.3)
        g.clic(x, y)
        time.sleep(1.0)
        scena.comanda(pulisci=True)
        da = len(scena.quaderno())
        F014.lettera(g, "q")
        v, _q = scena.aspetta_valore("q", da, 8)
        if v != "q":
            raise S.Bloccata("the keyboard does not reach the scene's field (a «q» ⇒ %r)" % (v,))
        testo = F014.testo_unico("F014")
        visto, det = F014.verso_browser_sessione(s, scena, geo, testo)
        _png, dove = s.foto("f014")
        ev = [x for x in (dove, s.salva_testo("f014.json", json.dumps(
            det, ensure_ascii=False, indent=1))) if x]
        e, perche = F014.giudica_testo(testo, visto)
        if e == S.FAIL and not det.get("gesto_arrivato"):
            e, perche = S.BLOCKED, ("the Ctrl+V did not reach the application: it is the "
                                    "keyboard, not the clipboard — " + perche)
        if det.get("riprova_ctrl_v"):
            perche += " · (Ctrl+V typed again once)"
        E.metti("F-014", e, perche, atteso=testo, osservato=visto, evidenze=ev)
        if o.guasto:
            # ⭐ the two faults of 15-f014: «different expected» (the true value against the text
            #   without accents) and «copy not done» (no Ctrl+C in the browser)
            ad = F014.giudica_testo(F014.senza_accenti(testo), visto)[0] == S.FAIL
            tg = F014.testo_unico("F014G")
            vg, dg = F014.verso_browser_sessione(s, scena, geo, tg, copia=False)
            s.salva_testo("f014-guasto.json", json.dumps(dg, ensure_ascii=False, indent=1))
            rg = F014.giudica_testo(tg, vg)[0] == S.FAIL
            E.guasto("F-014", (rg and ad) if dg.get("gesto_arrivato") else None,
                     "copy not done ⇒ the remote field is %r (%s); expected without accents ⇒ %s"
                     % ((vg or "")[:50], "RED" if rg else "GREEN", "RED" if ad else "GREEN"),
                     atteso=tg, osservato=vg)
    finally:
        scena.spegni()


# ═══════════════════════════════════════════════════════════════════════════
def main():
    o = S.argomenti(__doc__, extra)
    o.tetto_s = max(o.tetto_s, TETTO_NASCITA_S)
    o.funzioni = [f for f in FUNZIONI if not o.solo or f in o.solo.split(",")]
    os.makedirs(o.dir, exist_ok=True)
    o.evidenze = o.evidenze or os.path.join(o.dir, "controllo-corto")
    os.makedirs(o.evidenze, exist_ok=True)
    E = S.Esiti(o)
    nnn = "%03d" % o.livello
    chi = "c16%su%d" % (nnn, o.utente)
    inizio, t0 = adesso(), time.time()
    # ⭐ the schema that 16-classifica.py reads: «utente» is the NUMBER (99: no
    #   actor has that number ⇒ the entry goes to the level), «esiti» {F-NNN: outcome}
    rapporto = {"livello": o.livello, "utente": o.utente, "inquilino": chi, "browser": o.browser,
                "scatola": o.scatola,
                "misura": "%dx%d" % (o.largo, o.alto), "inizio": inizio,
                "wayland": os.environ.get("WAYLAND_DISPLAY", ""), "funzioni": {},
                "nascita": {}, "evidenze": o.evidenze}
    print("⭐ short check · %s · level %d · %s · %s · %s" % (
        o.scatola, o.livello, chi, o.browser, o.url), flush=True)
    segno = None
    try:
        with S.Sessione(o, nnn, E, chi=chi) as s:
            rapporto["versione"] = E.versione
            if o.browser == "chrome" and "F-014" in o.funzioni:
                # ⭐ the clipboard permission, as the user would give it (15-f014)
                try:
                    s.g.cdp.chiama("Browser.grantPermissions", origin=o.url.rstrip("/"),
                                   permissions=["clipboardReadWrite", "clipboardSanitizedWrite"])
                except Exception as e:           # noqa: BLE001
                    print("   ⚠ clipboard permission NOT granted: %s" % e, flush=True)
            segno = s.segno_registro()
            try:
                rapporto["sessioni_durante"] = sessioni_vive(s)
            except Exception:                    # noqa: BLE001
                pass
            ok, m, tempi = nasci(s, o)
            rapporto["nascita"] = dict(tempi, esito="PASS" if ok else "FAIL", ragione=m)
            print("   birth: %s · %s" % (json.dumps(tempi), m), flush=True)
            if not ok:
                raise S.Bloccata("the check's session was not born: %s" % m)
            geo = s.geometria()
            if geo:
                print("   wake-up: %s" % C21.sveglia(s.g, geo), flush=True)
            for f, passo in (("F-004", None), ("F-003", f003), ("F-014", f014)):
                if f == "F-004":
                    if "F-004" in o.funzioni or "F-007" in o.funzioni:
                        try:
                            f004_f007(o, E, s, tempi)
                        except S.Bloccata as b:
                            for ps in ("sana", "guasto") if o.guasto else ("sana",):
                                E.bloccate([x for x in ("F-004", "F-007") if x in o.funzioni],
                                           str(b), passata=ps)
                        except Exception as e:   # noqa: BLE001
                            traceback.print_exc()
                            E.bloccate([x for x in ("F-004", "F-007") if x in o.funzioni],
                                       "the bench crashed: %r" % e)
                        via_le_scene(s)
                    continue
                if f not in o.funzioni:
                    continue
                try:
                    passo(o, E, s)
                except S.Bloccata as b:
                    for ps in ("sana", "guasto") if o.guasto else ("sana",):
                        E.bloccate([f], str(b), passata=ps)
                except Exception as e:           # noqa: BLE001
                    traceback.print_exc()
                    E.bloccate([f], "the bench crashed: %r" % e)
                via_le_scene(s)
            s.salva_console()
            if segno is not None:
                s.salva_testo("server-controllo.txt", s.registro_da(segno))
    except S.Bloccata as b:
        E.bloccate(o.funzioni, str(b))
        if o.guasto:
            E.bloccate(o.funzioni, str(b), passata="guasto")
    except Exception as e:                       # noqa: BLE001
        traceback.print_exc()
        E.bloccate(o.funzioni, "the bench crashed: %r" % e)
    E.bloccate(o.funzioni, "the test gave no judgement (defect of the bench)")
    if o.guasto:
        E.bloccate(o.funzioni, "the pass with the fault gave no judgement", passata="guasto")
    rapporto["guasti"] = {}
    for r in E.righe:
        dove = rapporto["guasti"] if r["passata"] == "guasto" else rapporto["funzioni"]
        dove[r["funzione"]] = {k: r.get(k) for k in (
            "esito", "ragione", "atteso", "osservato", "evidenze", "guasto_visto")}
    # ⚠ «esiti» (read by 16-classifica.py) is ONLY the healthy pass
    rapporto["esiti"] = {f: v["esito"] for f, v in rapporto["funzioni"].items()}
    def somma(es):
        return S.FAIL if S.FAIL in es else (S.BLOCKED if S.BLOCKED in es or not es else S.PASS)
    rapporto["esito"] = somma([r["esito"] for r in E.righe if r["passata"] == "sana"])
    if o.guasto:
        # PASS = every grafted fault was SEEN (the judge gave red)
        rapporto["esito_guasto"] = somma([r["esito"] for r in E.righe if r["passata"] == "guasto"])
    if rapporto["nascita"].get("esito") == "FAIL" and rapporto["nascita"].get("rifiuto"):
        rapporto["esito"] = S.FAIL                # §9: refusal ⇒ FAIL
    rapporto["durata_s"] = round(time.time() - t0)
    rapporto["fine"] = adesso()
    p = os.path.join(o.dir, "controllo-corto.json")
    with open(p + ".tmp", "w") as f:
        json.dump(rapporto, f, ensure_ascii=False, indent=1)
    os.replace(p + ".tmp", p)
    print("⏱ %d s · %s · %s" % (rapporto["durata_s"], rapporto["esito"], p), flush=True)
    fin = [rapporto["esito"], rapporto.get("esito_guasto", S.PASS)]
    return 1 if S.FAIL in fin else (3 if S.BLOCKED in fin else 0)


def sessioni_vive(s):
    """How many graphical sessions there are in the box now (to declare N+1)."""
    _c, t = s.sc.dentro("loginctl list-sessions --no-legend 2>/dev/null | awk '{print $3}' "
                        "| grep -cE '^c[0-9]+b?u[0-9]+$'", 30)
    try:
        return int((t or "").split()[-1])
    except (ValueError, IndexError):
        return None


if __name__ == "__main__":
    sys.exit(main())
