#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
16-controllo-corto — IL CONTROLLO FUNZIONALE CORTO DI UN LIVELLO (fase 16, §7)
===========================================================================

    (sul server, come nicfio, nell'ambiente di 15-una.sh: WAYLAND_DISPLAY del
     SUO compositore — 16-compositori.sh u00 — e REMOTIX_SUL_SERVER=1)
    python3 16-controllo-corto.py --scatola lxqt --livello 4 \\
        --dir /media/REMOTIX/misure/fase16/<campagna>/livello-04 \\
        --browser chrome --porte-base 9900 [--largo 3840 --alto 2160]

CHE COSA FA — una SESSIONE NUOVA, sua, dentro il livello carico:
  inquilino `c16<livello>u99` (nato qui, sgomberato all'uscita), un browser
  vero (quello chiesto: la salita li alterna fra i livelli), e in fila, come
  un utente che arriva:
    nascita  accesso → primo fotogramma, cronometrato (§7 «nascita di un
             utente nuovo», §9: ≤ 5 s GREEN, 5–15 DEGRADED, > 15 o rifiuto FAIL)
    F-004    il mouse, RIDOTTO: movimento, clic sinistro, trascinamento
             (la scena di 15-g2-scena.py, i giudici di 15-f004)
    F-007    i tasti speciali: la sequenza di 15-f007 (Invio, Canc indietro,
             frecce, Tab, Esc) nella stessa scena
    F-003    l'immagine, RIDOTTA: la finestra di prova si APRE e il suo
             contatore CAMBIA (foto non piu' vecchie di 1 s per 6 s) — i
             giudici di 15-f003; niente trascinamento ne' chiusura giudicata
    F-014    gli appunti browser → sessione: la scena e il giudice di 15-f014
  ⇒ scrive DIR/controllo-corto.json e le evidenze in DIR/controllo-corto/.

  --guasto  (la prova del controllo, §13.2; NON nella salita) dopo la passata
            sana, nella stessa sessione, ogni giudice riceve un'evidenza FALSA
            e deve dare rosso: F-004 gesti a vuoto · F-007 la sequenza senza
            Esc · F-003 la foto di PRIMA (apertura e contatore) · F-014 copia
            non fatta + atteso senza accenti.  In controllo-corto.json:
            «guasti» e «esito_guasto» (PASS = tutti visti); «esiti» resta la
            sola passata sana.

⭐ PERCHE' UNA SESSIONE SUA, e non quella di un attore (proposta, fasi/16 §7):
  - ogni attore ha il SUO browser (Marionette/CDP a una porta sola): entrarci
    da fuori vorrebbe dire due padroni sullo stesso browser, e il gesto di uno
    rovinerebbe il lavoro dell'altro — la misura del livello si sporcherebbe;
  - le prove della fase 15 sono scritte per una `suite.Sessione`: con una
    sessione sua si RIUSANO come sono (scene, giudici, riprove), senza
    riscriverle contro il lavoro di un attore che intanto clicca altrove;
  - e' anche la misura che §7 chiede a parte: la NASCITA di un utente nuovo
    col server gia' carico di N utenti;
  - il prezzo: per qualche minuto il livello ha N+1 sessioni.  Si dichiara
    (`sessioni_durante`), ed e' dentro il tetto (16) fino al gradino 15.
    ⚠ Al gradino 16 il controllo e' la 17-esima: la salita alza il tetto a 17
    per la scatola della campagna (16-salita.py --tetto), e lo dice.

Codice d'uscita: 0 tutto PASS · 1 almeno un FAIL · 3 almeno un BLOCKED e
nessun FAIL.  Una riga `SUITE {...}` per funzione, come la suite.
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

# ⭐ le prove della fase 15, IMPORTATE (non copiate)
F003 = S._carica("f003", os.path.join(SUITE, "15-f003-lo-schermo-si-aggiorna.py"))
F004 = S._carica("f004", os.path.join(SUITE, "15-f004-il-mouse.py"))
F007 = S._carica("f007", os.path.join(SUITE, "15-f007-tasti-speciali.py"))
F014 = S._carica("f014", os.path.join(SUITE, "15-f014-appunti.py"))
G2 = F004.G2
C21 = S.C21

# ⛔ gli inquilini della fase 16 si chiamano c16<nnn>u<n>: la suite accetta solo
#   i suoi (c15…).  Lo sgombero della rete (`^c[0-9]+b?u[0-9]+$`) li riconosce.
S.MODELLO_INQUILINO = re.compile(r"^c1[56][0-9]{3}u[0-9]+$")

FUNZIONI = ("F-004", "F-007", "F-003", "F-014")
GESTI_RIDOTTI = ("movimento", "clic-sinistro", "trascinamento")
UTENTE_CONTROLLO = 99
TETTO_NASCITA_S = 90            # oltre: FAIL «nessun primo fotogramma» (§9: > 15 s e' gia' FAIL)


def adesso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def extra(a):
    a.add_argument("--dir", required=True, help="la cartella del livello (livello-NN)")
    a.add_argument("--livello", type=int, required=True)
    a.add_argument("--utente", type=int, default=UTENTE_CONTROLLO,
                   help="il numero dell'inquilino c16<livello>u<utente> (99)")
    a.add_argument("--solo", default="", help="solo queste funzioni (F-004,F-003…): prove del banco")


# ═══════════════════════════════════════════════════════════════════════════
#  LA NASCITA, cronometrata
# ═══════════════════════════════════════════════════════════════════════════
def nasci(s, o):
    """Pagina → modulo → ammissione → primo fotogramma, coi tempi.
    Torna (ok, motivo, tempi)."""
    t = {}
    t0 = time.time()
    ok, m = s.pr.apri()
    t["pagina_s"] = round(time.time() - t0, 2)
    if not ok:
        return False, "la pagina non si apre: " + m, t
    t1 = time.time()
    e, m, _st = s.pr.entra(s.parola)
    t["ammissione_s"] = round(time.time() - t1, 2)
    if e != S.VERDE:
        t["rifiuto"] = bool(s.pr.rifiuto)
        return False, "l'accesso: " + m, t
    # ⭐ accesso → primo fotogramma DIPINTO: il contatore della pagina, letto
    #   fitto; poi la fotografia (non degenere) la fa `primo_fotogramma`.
    fine = t1 + TETTO_NASCITA_S
    while time.time() < fine:
        st = s.pr.stato() or {}
        if (st.get("dipinti") or 0) > 0:
            t["nascita_s"] = round(time.time() - t1, 2)
            break
        time.sleep(0.2)
    if "nascita_s" not in t:
        return False, "nessun fotogramma dipinto %d s dopo l'accesso" % TETTO_NASCITA_S, t
    e, m, st = s.pr.primo_fotogramma()
    e, m = S.C20V.desktop_scuro_ma_vivo(e, m, st)
    t["primo_non_degenere_s"] = round(time.time() - t1, 2)
    if e != S.VERDE:
        return False, "il primo fotogramma: " + m, t
    return True, m, t


def aspetta_tela(s):
    """La tela della misura voluta (la regola di F-011), come in 15-f003."""
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
        return None, "`REMOTIX_PUNTATORE.geometria` non c'e'"
    return None, "la tela e' %sx%s e non %dx%d dopo 40 s" % (geo.get("tl"), geo.get("ta"),
                                                           attesa[0], attesa[1])


def via_le_scene(s):
    """Le applicazioni di prova della sessione se ne vanno (la scena di G2, la
    finestra di F-003): la funzione dopo parte da un desktop pulito."""
    s.sc.dentro("pkill -KILL -u %s -f '[f]irefox-esr' 2>/dev/null; "
                "pkill -KILL -u %s -f '[g]2-servitore' 2>/dev/null; sleep 1; true"
                % (s.chi, s.chi), 30)


# ═══════════════════════════════════════════════════════════════════════════
#  LE QUATTRO FUNZIONI, ridotte — i giudici sono quelli della fase 15
# ═══════════════════════════════════════════════════════════════════════════
def f004_f007(o, E, s, t_nascita):
    """La scena di G2 una volta sola, poi i gesti ridotti e i tasti."""
    ok_n, m_n = True, "gia' entrato"
    vero_entra = s.entra
    s.entra = lambda *a, **k: (ok_n, m_n)          # G2.prepara non rientra: siamo dentro
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
        atteso = "movimento sul blocco BLU dove punta, clic sul VERDE contato, box spostato"
        if S.FAIL in es:
            E.metti("F-004", S.FAIL, "gesti rossi: " + ", ".join(
                n for n, e, _m, _ in righe if e == S.FAIL), atteso=atteso, osservato=oss,
                evidenze=ev + [s.salva_console()])
        elif S.BLOCKED in es:
            E.metti("F-004", S.BLOCKED, "gesti non guardati: " + ", ".join(
                "%s (%s)" % (n, m) for n, e, m, _ in righe if e == S.BLOCKED),
                atteso=atteso, osservato=oss, evidenze=ev)
        else:
            E.metti("F-004", S.PASS, "%d gesti su %d (ridotto): l'effetto c'e' "
                    "nell'applicazione" % (len(righe), len(righe)), atteso=atteso,
                    osservato=oss, evidenze=ev)
        if o.guasto:
            # ⭐ il guasto di 15-f004: ogni gesto A VUOTO, stesso giudice ⇒ tutti rossi
            righe = F004.passata(s, sc, mp, True)
            visto = F004.esito_col_guasto([r[1] for r in righe])
            E.guasto("F-004", visto, {True: "ogni gesto a vuoto ha dato rosso",
                                      False: "gesti a vuoto VERDI lo stesso: " + ", ".join(
                                          n for n, e, _m, _ in righe if e == S.PASS),
                                      None: "un gesto a vuoto non si e' potuto guardare"}[visto],
                     osservato=" · ".join("%s: %s %s" % (n, e, m) for n, e, m, _ in righe))
    if "F-007" in o.funzioni:
        st, foto, perche = F007.batti(s, sc, mp, F007.SEQUENZA, "tasti")
        if perche:
            E.metti("F-007", S.BLOCKED, perche)
        else:
            e, m = F007.giudica(st, F007.ATTESO)
            if e == S.FAIL:
                print("   ⚠ rosso (%s): lo rifaccio per confermarlo" % m, flush=True)
                st2, foto2, perche2 = F007.batti(s, sc, mp, F007.SEQUENZA, "tasti-bis")
                e2, m2 = F007.giudica(st2, F007.ATTESO) if not perche2 else (S.BLOCKED, perche2)
                if e2 == S.PASS:
                    e, m = S.PASS, "⚠ ROSSO al primo tentativo (%s), verde al secondo" % m
                else:
                    m = "rosso due volte: %s · %s" % (m, m2)
                foto = foto2 or foto
            E.metti("F-007", e, m, atteso="a=%r b=%r" % F007.ATTESO, osservato=m,
                    evidenze=[x for x in (foto,) if x])
        if o.guasto:
            # ⭐ il guasto di 15-f007: la stessa sequenza SENZA l'Esc ⇒ «b» non si svuota
            passi = F007.senza(F007.SEQUENZA, F007.GUASTO_TOGLIE)
            st, foto, perche = F007.batti(s, sc, mp, passi, "tasti-guasto")
            if perche:
                E.guasto("F-007", None, perche)
            else:
                eg, mg = F007.giudica(st, F007.ATTESO)
                E.guasto("F-007", None if eg == S.BLOCKED else eg == S.FAIL,
                         "senza %s: %s" % (F007.GUASTO_TOGLIE, mg), osservato=mg,
                         evidenze=[foto] if foto else [])


def f003(o, E, s):
    """Apre e cambia, dalla FOTOGRAFIA (i giudici di 15-f003)."""
    geo, perche = aspetta_tela(s)
    if not geo:
        raise S.Bloccata(perche)
    time.sleep(1.5)
    _p, im0, _a, _b = F003.foto_im(s, "f003-prima")
    if im0 is None:
        raise S.Bloccata("la tela non si fotografa")
    q0 = F003.frazione_ciano(im0)
    if q0 >= F003.CIANO_ASSENTE:
        raise S.Bloccata("prima di aprire c'e' gia' del ciano (%.2f %%)" % (100 * q0))
    largo_f, alto_f = geo["tl"] * 0.45, geo["ta"] * 0.55
    c, t = F003.prepara_la_casa(s, largo_f, alto_f)
    if c != 0:
        raise S.Bloccata("la casa non si prepara: %s" % (t or "")[-200:])
    ok, t = C21.accendi_la_finestra(s.sc, s.chi)
    if not ok:
        raise S.Bloccata("firefox-esr non parte: %s" % (t or "")[-200:])
    t_ap = time.time()
    f1, im1 = F003.aspetta_ferma(s, F003.APERTURA_S, "f003-aperta")
    parti, guasti = [], []
    if not f1:
        _p, im_x, _a, _b = F003.foto_im(s, "f003-apertura-non-vista")
        nuovo = F003.cambiato(im0, im_x) if im_x is not None else 0.0
        if not F003.processo_vivo(s):
            parti.append(("apre", S.BLOCKED, "firefox-esr non e' rimasto vivo: %s" % im1))
        elif nuovo > F003.CAMBIATO_MIN:
            parti.append(("apre", S.BLOCKED, "la foto e' cambiata (%.1f %%) ma non mostra la "
                          "pagina di prova" % (100 * nuovo)))
        else:
            parti.append(("apre", S.FAIL, "firefox-esr vivo da %.0f s e la foto e' IDENTICA a "
                          "quella di prima: lo schermo non si aggiorna" % (time.time() - t_ap)))
    else:
        pw, _ph = f1["foto"]
        largo_foto = largo_f * geo["sx"] * pw / geo["bw"]
        e, m = F003.giudica_apertura(f1, largo_foto)
        if e == S.FAIL:
            e, m = S.BLOCKED, "il ciano non e' largo quanto la finestra chiesta: un'anteprima?"
        parti.append(("apre", e, m + " (in %.1f s)" % (time.time() - t_ap)))
        # ⭐ guasto «apre»: la foto di PRIMA dell'apertura data al giudice
        f0, _ = F003.trova(im0)
        guasti.append(("apre", F003.giudica_apertura(f0, largo_foto)))
        if e == S.PASS:
            v0, mv = F003.leggi_contatore(im1, f1["rett"])
            if v0 is None:
                parti.append(("cambia", S.BLOCKED, "il contatore non si legge: %s" % mv))
            else:
                serie = []
                for giro in range(2):               # un rosso si conferma, come in 15-f003
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
                    print("   cambi rapidi, serie %d: %s %s" % (giro + 1, e, m), flush=True)
                    if e == S.PASS:
                        break
                e, m, letture, prima_im = serie[-1]
                if letture and prima_im is not None:
                    # ⭐ guasto «cambia» (15-f003): la PRIMA foto per tutte, cogli istanti veri
                    n0, m0 = F003.leggi_contatore(prima_im, f1["rett"])
                    ge, gm, _ = F003.giudica_rapidi([(tp, td, n0, m0)
                                                     for tp, td, _n, _m in letture])
                    guasti.append(("cambia", (ge, gm)))
                if len(serie) > 1:
                    m = "serie 1: %s %s · serie 2: %s" % (serie[0][0], serie[0][1], m)
                parti.append(("cambia", e, m))
    via_le_scene(s)
    es = F003.complessivo(parti)
    testo = " · ".join("%s %s: %s" % p for p in parti)
    E.metti("F-003", es, testo if es != S.PASS else "apre e cambia: le foto seguono lo "
            "schermo (ridotto: niente trascinamento)", atteso="la finestra si apre nella foto; "
            "contatore ≤ %.0f ms in ogni foto per %d s" % (F003.TETTO_MS, F003.RAPIDI_S),
            osservato=testo, evidenze=[o.evidenze], parti={p: [e, m] for p, e, m in parti})
    if o.guasto:
        if es != S.PASS:
            E.guasto("F-003", None, "la passata sana non e' verde: il guasto si giudica solo "
                     "su una passata sana")
        else:
            visti = {p: r[0] == S.FAIL for p, r in guasti}
            E.guasto("F-003", len(visti) == 2 and all(visti.values()),
                     "foto di PRIMA ⇒ " + " · ".join("%s %s" % (p, "rosso" if r[0] == S.FAIL
                                                              else r[0]) for p, r in guasti),
                     osservato=" | ".join("%s: %s" % (p, r[1]) for p, r in guasti))


def f014(o, E, s):
    geo = s.geometria()
    if not geo:
        raise S.Bloccata("la geometria della tela non c'e'")
    g = s.g
    st = g.js(F014.STATO_APPUNTI)
    if not st or not st.get("acceso"):
        E.metti("F-014", S.FAIL, "gli appunti della pagina non sono accesi: %s" % st)
        return
    scena = F014.Scena(s, o.porte_base + 5)
    try:
        ok, t = scena.accendi()
        if not ok:
            raise S.Bloccata("la scena degli appunti non si accende: %s" % (t or "")[-300:])
        time.sleep(3)
        x, y = C21.dal_desktop_al_vetro(geo, geo["tl"] * 0.5, geo["ta"] * 0.3)
        g.clic(x, y)
        time.sleep(1.0)
        scena.comanda(pulisci=True)
        da = len(scena.quaderno())
        F014.lettera(g, "q")
        v, _q = scena.aspetta_valore("q", da, 8)
        if v != "q":
            raise S.Bloccata("la tastiera non arriva al campo della scena (una «q» ⇒ %r)" % (v,))
        testo = F014.testo_unico("F014")
        visto, det = F014.verso_browser_sessione(s, scena, geo, testo)
        _png, dove = s.foto("f014")
        ev = [x for x in (dove, s.salva_testo("f014.json", json.dumps(
            det, ensure_ascii=False, indent=1))) if x]
        e, perche = F014.giudica_testo(testo, visto)
        if e == S.FAIL and not det.get("gesto_arrivato"):
            e, perche = S.BLOCKED, ("il Ctrl+V non e' arrivato all'applicazione: e' la "
                                    "tastiera, non gli appunti — " + perche)
        if det.get("riprova_ctrl_v"):
            perche += " · (Ctrl+V ribattuto una volta)"
        E.metti("F-014", e, perche, atteso=testo, osservato=visto, evidenze=ev)
        if o.guasto:
            # ⭐ i due guasti di 15-f014: «atteso diverso» (il valore vero contro il testo
            #   senza accenti) e «copia non fatta» (niente Ctrl+C nel browser)
            ad = F014.giudica_testo(F014.senza_accenti(testo), visto)[0] == S.FAIL
            tg = F014.testo_unico("F014G")
            vg, dg = F014.verso_browser_sessione(s, scena, geo, tg, copia=False)
            s.salva_testo("f014-guasto.json", json.dumps(dg, ensure_ascii=False, indent=1))
            rg = F014.giudica_testo(tg, vg)[0] == S.FAIL
            E.guasto("F-014", (rg and ad) if dg.get("gesto_arrivato") else None,
                     "copia non fatta ⇒ il campo remoto vale %r (%s); atteso senza accenti ⇒ %s"
                     % ((vg or "")[:50], "ROSSO" if rg else "VERDE", "ROSSO" if ad else "VERDE"),
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
    # ⭐ lo schema che legge 16-classifica.py: «utente» e' il NUMERO (99: nessun
    #   attore ha quel numero ⇒ la voce va al livello), «esiti» {F-NNN: esito}
    rapporto = {"livello": o.livello, "utente": o.utente, "inquilino": chi, "browser": o.browser,
                "scatola": o.scatola,
                "misura": "%dx%d" % (o.largo, o.alto), "inizio": inizio,
                "wayland": os.environ.get("WAYLAND_DISPLAY", ""), "funzioni": {},
                "nascita": {}, "evidenze": o.evidenze}
    print("⭐ controllo corto · %s · livello %d · %s · %s · %s" % (
        o.scatola, o.livello, chi, o.browser, o.url), flush=True)
    segno = None
    try:
        with S.Sessione(o, nnn, E, chi=chi) as s:
            rapporto["versione"] = E.versione
            if o.browser == "chrome" and "F-014" in o.funzioni:
                # ⭐ il permesso degli appunti, come lo darebbe l'utente (15-f014)
                try:
                    s.g.cdp.chiama("Browser.grantPermissions", origin=o.url.rstrip("/"),
                                   permissions=["clipboardReadWrite", "clipboardSanitizedWrite"])
                except Exception as e:           # noqa: BLE001
                    print("   ⚠ permesso appunti NON concesso: %s" % e, flush=True)
            segno = s.segno_registro()
            try:
                rapporto["sessioni_durante"] = sessioni_vive(s)
            except Exception:                    # noqa: BLE001
                pass
            ok, m, tempi = nasci(s, o)
            rapporto["nascita"] = dict(tempi, esito="PASS" if ok else "FAIL", ragione=m)
            print("   nascita: %s · %s" % (json.dumps(tempi), m), flush=True)
            if not ok:
                raise S.Bloccata("la sessione del controllo non e' nata: %s" % m)
            geo = s.geometria()
            if geo:
                print("   sveglia: %s" % C21.sveglia(s.g, geo), flush=True)
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
                                       "il banco e' caduto: %r" % e)
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
                    E.bloccate([f], "il banco e' caduto: %r" % e)
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
        E.bloccate(o.funzioni, "il banco e' caduto: %r" % e)
    E.bloccate(o.funzioni, "la prova non ha dato un giudizio (difetto del banco)")
    if o.guasto:
        E.bloccate(o.funzioni, "la passata col guasto non ha dato un giudizio", passata="guasto")
    rapporto["guasti"] = {}
    for r in E.righe:
        dove = rapporto["guasti"] if r["passata"] == "guasto" else rapporto["funzioni"]
        dove[r["funzione"]] = {k: r.get(k) for k in (
            "esito", "ragione", "atteso", "osservato", "evidenze", "guasto_visto")}
    # ⚠ «esiti» (lo legge 16-classifica.py) e' SOLO la passata sana
    rapporto["esiti"] = {f: v["esito"] for f, v in rapporto["funzioni"].items()}
    def somma(es):
        return S.FAIL if S.FAIL in es else (S.BLOCKED if S.BLOCKED in es or not es else S.PASS)
    rapporto["esito"] = somma([r["esito"] for r in E.righe if r["passata"] == "sana"])
    if o.guasto:
        # PASS = ogni guasto innestato e' stato VISTO (il giudice ha dato rosso)
        rapporto["esito_guasto"] = somma([r["esito"] for r in E.righe if r["passata"] == "guasto"])
    if rapporto["nascita"].get("esito") == "FAIL" and rapporto["nascita"].get("rifiuto"):
        rapporto["esito"] = S.FAIL                # §9: rifiuto ⇒ FAIL
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
    """Quante sessioni grafiche ci sono nella scatola adesso (per dichiarare N+1)."""
    _c, t = s.sc.dentro("loginctl list-sessions --no-legend 2>/dev/null | awk '{print $3}' "
                        "| grep -cE '^c[0-9]+b?u[0-9]+$'", 30)
    try:
        return int((t or "").split()[-1])
    except (ValueError, IndexError):
        return None


if __name__ == "__main__":
    sys.exit(main())
