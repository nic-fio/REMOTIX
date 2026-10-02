#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f014c — GLI APPUNTI COME LI USA UNA PERSONA: COL COMPUTER, NON COL BANCO

    python3 15-f014c-appunti-dal-computer.py --scatola gnome --browser chrome [--guasto]
    python3 15-f014c-appunti-dal-computer.py --certifica

PERCHE' C'E' (2 ott 2026, la prova a mano dell'utente: «Ctrl+C / Ctrl+V non
funzionano, o non sempre», Firefox E Chrome, tutti i desktop).  `15-f014` e'
verde ma non vede quello che vede la persona: fa clic di cortesia, legge gli
appunti dalla pagina con `readText()`, a Chrome DA' il permesso, non riusa mai
un testo e non copia mai FUORI dal browser.  Questa prova fa come la persona:

  - gli appunti del COMPUTER (non della pagina) si scrivono e si leggono con
    `wl-copy` / `wl-paste` nella sessione Wayland del browser (il labwc senza
    schermo del desktop, quello di 15-compositori.sh: lo stesso WAYLAND_DISPLAY
    che il giro da' al browser);
  - NESSUN clic di cortesia: solo il clic che la persona fa davvero (uno sulla
    tela prima di incollare);
  - Chrome SENZA il permesso degli appunti (nessun `Browser.grantPermissions`);
  - un `Ctrl+V` alla volta, mai ribattuto: il primo e' quello che conta.

La scena e i gesti sono quelli di `15-f014` (importati, non copiati): un
`firefox-esr --kiosk` nella sessione con un <textarea> sempre a fuoco, che
annota ogni valore; il giudizio e' il VALORE DEL CAMPO dell'applicazione della
sessione, o il testo negli appunti del computer.

F-015C  (P1) sessione → computer, senza gesti recenti.  Il testo nel campo della
        scena, selezionato; 6 s fermi (nessun clic: l'attivazione del browser
        scade); `Ctrl+C` VERO sulla pagina ⇒ entro 3 s `wl-paste` deve valere
        ESATTAMENTE quel testo.
F-014C  (P2, la principale) il testo copiato FUORI dal browser.  `Ctrl+C` nella
        scena (testo Z: ora gli appunti della sessione sono di un'applicazione
        remota), poi `wl-copy X` fuori dal browser, UN clic sulla tela, UN
        `Ctrl+V` ⇒ il campo della scena deve valere X.  Cinque volte, testi
        nuovi ogni volta; verde solo se tutte e cinque.
F-014D  (P1b) lo STESSO testo copiato due volte.  `wl-copy X`, clic, `Ctrl+V` ⇒
        X; poi una copia nella sessione (testo W), poi di nuovo `wl-copy X`
        (identico), clic, `Ctrl+V` ⇒ X.

GUASTO (stessa sessione, dopo la passata sana):
  F-015C  «copia non fatta»: il testo nel campo, 6 s, NIENTE `Ctrl+C` ⇒
          `wl-paste` non lo vede ⇒ ROSSO.  E il valore sano giudicato contro
          lo stesso testo senza accenti ⇒ ROSSO.
  F-014C  «copia fuori non fatta»: `Ctrl+C` nella scena, NIENTE `wl-copy X`,
          clic, `Ctrl+V` ⇒ il campo non vale X ⇒ ROSSO.  E l'atteso senza accenti.
  F-014D  «la seconda copia e' un altro testo»: la seconda `wl-copy` mette Y,
          l'atteso resta X ⇒ ROSSO.  E l'atteso senza accenti.

⚠ Solo Firefox e Chrome sul server (il telefono non ha `wl-copy`: BLOCKED).
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

FUNZIONI = ("F-015C", "F-014C", "F-014D")

# ⭐ la scena, i gesti e il giudice di 15-f014 (anche il suo `dentro` locale)
F14 = S._carica("f014", os.path.join(S.QUI, "15-f014-appunti.py"))

GIRI_P2 = 5
FERMO_P1_S = 6.0          # niente gesti: l'attivazione transitoria (5 s) scade
TETTO_P1_S = 3.0          # entro quanto il testo deve stare negli appunti del computer
ATTESA_CAMPO_S = 12.0


# ═══════════════════════════════════════════════════════════════════════════
#  LE FUNZIONI PURE
# ═══════════════════════════════════════════════════════════════════════════
def giudica_giri(giri, quanti):
    """(esito, perche') sui giri di P2: [{"atteso", "visto", "gesto"}].
    I giri senza il keydown del Ctrl+V non contano (e' la tastiera)."""
    validi = [g for g in giri if g.get("gesto")]
    sbagliati = [g for g in validi if g.get("visto") != g.get("atteso")]
    if sbagliati:
        vecchi = sum(1 for g in sbagliati if g.get("visto") and g.get("visto") == g.get("remoto"))
        return S.FAIL, ("%d giri su %d: al primo Ctrl+V il campo NON vale il testo copiato "
                        "fuori dal browser (%d volte vale il testo VECCHIO copiato nella "
                        "sessione)" % (len(sbagliati), len(validi), vecchi))
    if len(validi) < quanti:
        return S.BLOCKED, ("solo %d giri validi su %d: il Ctrl+V non e' arrivato "
                           "all'applicazione negli altri" % (len(validi), quanti))
    return S.PASS, "%d giri su %d: il campo vale il testo copiato fuori" % (len(validi), quanti)


def certifica():
    t = F14.testo_unico("X")
    z = F14.testo_unico("Z")
    giri_ok = [{"atteso": t, "visto": t, "gesto": True}] * GIRI_P2
    casi = [
        ("il giudice di f014: identico ⇒ PASS", F14.giudica_testo(t, t)[0] == S.PASS),
        ("senza accenti ⇒ FAIL", F14.giudica_testo(t, F14.senza_accenti(t))[0] == S.FAIL),
        ("cinque giri giusti ⇒ PASS", giudica_giri(giri_ok, GIRI_P2)[0] == S.PASS),
        ("un giro col testo vecchio ⇒ FAIL", giudica_giri(
            giri_ok[:4] + [{"atteso": t, "visto": z, "remoto": z, "gesto": True}],
            GIRI_P2)[0] == S.FAIL),
        ("il testo vecchio si conta", "1 volte" in giudica_giri(
            [{"atteso": t, "visto": z, "remoto": z, "gesto": True}], 1)[1]),
        ("un giro sbagliato basta anche se pochi validi", giudica_giri(
            [{"atteso": t, "visto": None, "gesto": True},
             {"atteso": t, "visto": None, "gesto": False}], GIRI_P2)[0] == S.FAIL),
        ("giri senza gesto ⇒ BLOCKED", giudica_giri(
            [{"atteso": t, "visto": None, "gesto": False}] * GIRI_P2, GIRI_P2)[0] == S.BLOCKED),
        ("quattro validi giusti su cinque ⇒ BLOCKED", giudica_giri(
            giri_ok[:4], GIRI_P2)[0] == S.BLOCKED),
    ]
    ok = True
    for nome, vero in casi:
        print("%s %s" % ("⭐" if vero else "⛔", nome))
        ok = ok and vero
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  GLI APPUNTI DEL COMPUTER (la sessione Wayland del browser)
# ═══════════════════════════════════════════════════════════════════════════
def wl_copia(testo):
    """`wl-copy` come lo farebbe un'altra applicazione del computer.  ⚠ wl-copy
    resta vivo in fondo a servire il testo: le uscite NON vanno in un tubo."""
    r = subprocess.run(["wl-copy"], input=testo.encode("utf-8"), stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=10)
    return r.returncode == 0


def wl_leggi():
    """Il testo negli appunti del computer, o None."""
    try:
        r = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, timeout=5)
    except subprocess.TimeoutExpired:
        return None
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", "replace")


def wl_svuota():
    try:
        subprocess.run(["wl-copy", "--clear"], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=10)
    except Exception:                            # noqa: BLE001
        pass


def stato(g):
    try:
        return g.js(F14.STATO_APPUNTI) or {}
    except Exception as e:                       # noqa: BLE001
        return {"errore": str(e)[:200]}


def conti(st):
    return dict((st or {}).get("conti") or {})


# ═══════════════════════════════════════════════════════════════════════════
#  I GESTI DELLA PERSONA
# ═══════════════════════════════════════════════════════════════════════════
def punto_campo(geo):
    return S.C21.dal_desktop_al_vetro(geo, geo["tl"] * 0.5, geo["ta"] * 0.3)


def copia_nella_sessione(g, scena, testo, copia=True):
    """Il testo nel campo della scena, selezionato, e `Ctrl+C` VERO sulla pagina.
    Nessun clic.  Torna i dettagli (gesto arrivato o no)."""
    q = scena.comanda(metti=testo)
    if F14.ultimo_valore(q) != testo:
        raise S.Bloccata("la scena non ha preso il testo da copiare: %r" % (F14.ultimo_valore(q),))
    det = {"copia_fatta": copia, "stato_prima": stato(g)}
    da = len(q)
    if copia:
        F14.ctrl(g, "c")
        fine = time.time() + 5
        while time.time() < fine and not F14.tasto_visto(scena.quaderno()[da:], "c"):
            time.sleep(0.5)
        det["gesto_arrivato"] = F14.tasto_visto(scena.quaderno()[da:], "c")
    return det, da


def incolla_una_volta(g, scena, geo, atteso):
    """UN clic sulla tela (sul campo remoto), UN Ctrl+V.  Mai ribattuto.
    Torna (valore del campo, dettagli)."""
    da = len(scena.quaderno())
    x, y = punto_campo(geo)
    det = {}
    g.clic(x, y)
    time.sleep(1.0)
    det["computer_al_ctrl_v"] = wl_leggi()
    det["stato_prima"] = stato(g)
    F14.ctrl(g, "v")
    visto, q = scena.aspetta_valore(atteso, da, ATTESA_CAMPO_S)
    det["gesto_arrivato"] = F14.tasto_visto(q, "v")
    det["incollato_dalla_scena"] = [v for t, v in q if t == "P"]
    det["quaderno"] = q[-10:]
    det["stato_dopo"] = stato(g)
    det["annunci"] = conti(det["stato_dopo"]).get("annunciati", 0) - \
        conti(det["stato_prima"]).get("annunciati", 0)
    det["computer_dopo"] = wl_leggi()
    return visto, det


# ═══════════════════════════════════════════════════════════════════════════
#  LE TRE PROVE
# ═══════════════════════════════════════════════════════════════════════════
def p1(g, scena, testo, copia=True):
    """F-015C: torna (testo negli appunti del computer entro 3 s, dettagli)."""
    wl_copia("prima-di-P1 " + F14.testo_unico("S"))
    q = scena.comanda(metti=testo)
    if F14.ultimo_valore(q) != testo:
        raise S.Bloccata("la scena non ha preso il testo: %r" % (F14.ultimo_valore(q),))
    time.sleep(FERMO_P1_S)                       # ⭐ fermi: nessun gesto recente
    det = {"copia_fatta": copia, "stato_prima": stato(g)}
    da = len(scena.quaderno())
    if copia:
        F14.ctrl(g, "c")
    t0 = time.time()
    letto, letture = None, []
    while time.time() - t0 < TETTO_P1_S:
        letto = wl_leggi()
        letture.append((round(time.time() - t0, 2), (letto or "")[:60]))
        if letto == testo:
            break
        time.sleep(0.2)
    det["entro_s"] = round(time.time() - t0, 2) if letto == testo else None
    det["letture"] = letture[-6:]
    det["gesto_arrivato"] = F14.tasto_visto(scena.quaderno()[da:], "c") if copia else None
    det["stato_dopo"] = stato(g)
    det["computer_dopo_5s"] = None
    if letto != testo:
        time.sleep(2.0)
        det["computer_dopo_5s"] = wl_leggi()      # diagnosi: e' solo in ritardo?
        det["stato_dopo_5s"] = stato(g)
    det["diario"] = g.js(F14.DIARIO)
    return letto, det


def p2_giro(g, scena, geo, sigla, copia_fuori=True):
    """F-014C, un giro.  Torna {"atteso", "visto", "remoto", "gesto", ...}."""
    z = F14.testo_unico(sigla + "Z")
    x = F14.testo_unico(sigla + "X")
    dc, _da = copia_nella_sessione(g, scena, z)
    time.sleep(2.0)                              # la persona passa a un'altra finestra
    st_copia = stato(g)
    scena.comanda(pulisci=True)
    if copia_fuori:
        wl_copia(x)
    fuori = wl_leggi()
    time.sleep(1.0)                              # e torna al browser
    visto, di = incolla_una_volta(g, scena, geo, x)
    r = {"atteso": x, "visto": visto, "remoto": z, "copia_fuori": copia_fuori,
         "gesto": di["gesto_arrivato"], "ctrl_c_arrivato": dc.get("gesto_arrivato"),
         "computer_dopo_wl_copy": fuori, "stato_dopo_copia": st_copia}
    r.update(di)
    return r


def p1b(g, scena, geo, x, seconda):
    """F-014D: (primo valore, secondo valore, dettagli)."""
    det = {}
    scena.comanda(pulisci=True)
    wl_copia(x)
    time.sleep(1.0)
    v1, det["primo"] = incolla_una_volta(g, scena, geo, x)
    w = F14.testo_unico("P1bW")
    det["copia_remota"], _ = copia_nella_sessione(g, scena, w)
    time.sleep(2.0)
    det["stato_dopo_copia_remota"] = stato(g)
    scena.comanda(pulisci=True)
    wl_copia(seconda)
    det["computer_seconda"] = wl_leggi()
    time.sleep(1.0)
    v2, det["secondo"] = incolla_una_volta(g, scena, geo, x)
    det["remoto"] = w
    det["diario"] = g.js(F14.DIARIO)
    return v1, v2, det


def giudica_p1b(x, v1, v2, det):
    e1, p1_ = F14.giudica_testo(x, v1)
    e2, p2_ = F14.giudica_testo(x, v2)
    if e1 == S.PASS and e2 == S.PASS:
        return S.PASS, "le due volte il campo vale il testo copiato (anche la seconda, identica)"
    parti = []
    if e1 != S.PASS:
        parti.append("prima volta: " + p1_)
    if e2 != S.PASS:
        quale = "il testo della copia REMOTA" if v2 == det.get("remoto") else p2_
        parti.append("seconda volta (stesso testo ricopiato): %s · annunci partiti al "
                     "Ctrl+V: %s" % (quale, det.get("secondo", {}).get("annunci")))
    gesti = [det.get(k, {}).get("gesto_arrivato") for k in ("primo", "secondo")]
    if not all(gesti):
        return S.BLOCKED, ("il Ctrl+V non e' arrivato all'applicazione (%s): e' la tastiera "
                           "— " % gesti) + " · ".join(parti)
    return S.FAIL, " · ".join(parti)


# ═══════════════════════════════════════════════════════════════════════════
def corpo(o, E):
    if o.browser == "telefono":
        raise S.Bloccata("il telefono non ha `wl-copy`: gli appunti del computer si guardano "
                         "solo sul server")
    wd = os.environ.get("WAYLAND_DISPLAY", "")
    rd = os.environ.get("XDG_RUNTIME_DIR", "")
    if not wd or not os.path.exists(os.path.join(rd, wd)):
        raise S.Bloccata("nessuna sessione Wayland del browser (WAYLAND_DISPLAY=%r, "
                         "XDG_RUNTIME_DIR=%r): si lancia dal giro o da 15-una.sh" % (wd, rd))
    prova = F14.testo_unico("WL")
    if not wl_copia(prova) or wl_leggi() != prova:
        raise S.Bloccata("gli appunti del computer non si scrivono/leggono con wl-copy/"
                         "wl-paste su %s" % wd)
    print("   appunti del computer: %s (wl-copy/wl-paste)" % wd, flush=True)
    porta_scena = o.porte_base + 6
    try:
        with S.Sessione(o, "914", E) as s:
            # ⛔ a Chrome NESSUN permesso degli appunti: come l'utente che non ha
            #   mai cliccato «Consenti»
            dentro(o, E, s, porta_scena)
    finally:
        wl_svuota()


def dentro(o, E, s, porta_scena):
    g = s.g
    segno = s.segno_registro()
    ok, m = s.entra()
    if not ok:
        raise S.Bloccata(m)
    geo = s.geometria()
    if not geo:
        raise S.Bloccata("la geometria della tela non c'e'")
    st = stato(g)
    print("   appunti della pagina: %s" % json.dumps(st, ensure_ascii=False), flush=True)
    if not st or not st.get("acceso"):
        for f in FUNZIONI:
            E.metti(f, S.FAIL, "gli appunti della pagina non sono accesi: %s" % st)
        return
    print("   sveglia: %s" % S.C21.sveglia(g, geo), flush=True)
    scena = F14.Scena(s, porta_scena)
    try:
        la_scena(o, E, s, g, geo, scena)
    finally:
        try:
            s.salva_testo("server-f014c.txt", s.registro_da(segno) if segno is not None else [])
            s.salva_console()
        finally:
            scena.spegni()


def la_scena(o, E, s, g, geo, scena):
    ok, t = scena.accendi()
    print("   scena: %s" % ((t or "?").splitlines() or ["?"])[-1], flush=True)
    if not ok:
        print(t, flush=True)
        s.foto("scena-non-accesa")
        raise S.Bloccata("la scena non si accende: %s" % (t or "")[-300:])
    time.sleep(3)
    # ⛔ controllo povero: la tastiera arriva al campo remoto?
    x, y = punto_campo(geo)
    g.clic(x, y)
    time.sleep(1.0)
    scena.comanda(pulisci=True)
    da = len(scena.quaderno())
    F14.lettera(g, "q")
    v, _q = scena.aspetta_valore("q", da, 8)
    if v != "q":
        raise S.Bloccata("la tastiera non arriva al campo della scena (una «q» battuta ⇒ %r)"
                         % (v,))
    scena.comanda(pulisci=True)
    salva = lambda nome, d: s.salva_testo(nome, json.dumps(d, ensure_ascii=False, indent=1))  # noqa: E731

    # ── P1 · F-015C ────────────────────────────────────────────────────────
    t1 = F14.testo_unico("P1")
    letto1, d1 = p1(g, scena, t1)
    ev1 = [salva("p1-sana.json", d1)]
    e, perche = F14.giudica_testo(t1, letto1)
    if e == S.PASS:
        perche += " · negli appunti del computer dopo %.2f s" % d1["entro_s"]
    else:
        perche = "entro %.0f s dal Ctrl+C (fermi da %.0f s, nessun clic) gli appunti del " \
                 "computer non hanno il testo: %s" % (TETTO_P1_S, FERMO_P1_S, perche)
        if d1.get("computer_dopo_5s") == t1:
            perche += " · ci arriva DOPO i 3 s"
        if (d1.get("stato_dopo") or {}).get("in_attesa"):
            perche += " · la pagina lo tiene «in attesa di un gesto»"
        if not d1.get("gesto_arrivato"):
            e, perche = S.BLOCKED, ("il Ctrl+C non e' arrivato all'applicazione della "
                                    "sessione: e' la tastiera — " + perche)
    E.metti("F-015C", e, perche, atteso=t1, osservato=letto1, evidenze=ev1)

    # ── P2 · F-014C ────────────────────────────────────────────────────────
    giri = []
    for i in range(GIRI_P2 + 3):
        if sum(1 for r in giri if r["gesto"]) >= GIRI_P2:
            break
        r = p2_giro(g, scena, geo, "P2%d" % i)
        giri.append(r)
        print("   P2 giro %d: %s (Ctrl+V %s, annunci %s)" % (
            i + 1, "giusto" if r["visto"] == r["atteso"] else
            ("TESTO VECCHIO della sessione" if r["visto"] == r["remoto"] else
             "sbagliato: %r" % (r["visto"] or "")[:40]),
            "arrivato" if r["gesto"] else "NON arrivato", r.get("annunci")), flush=True)
        if r["visto"] != r["atteso"] and not any(x.get("foto") for x in giri):
            r["foto"] = s.foto("p2-giro%d-sbagliato" % (i + 1))[1]
    _png, foto2 = s.foto("p2-fine")
    ev2 = [salva("p2-sana.json", {"giri": giri, "diario": g.js(F14.DIARIO)})]
    ev2 += [x for x in [foto2] + [r.get("foto") for r in giri] if x]
    e, perche = giudica_giri(giri, GIRI_P2)
    E.metti("F-014C", e, perche, atteso=" | ".join(r["atteso"] for r in giri),
            osservato=" | ".join(repr(r["visto"]) for r in giri), evidenze=ev2)

    # ── P1b · F-014D ───────────────────────────────────────────────────────
    xb = F14.testo_unico("P1b")
    v1, v2, db = p1b(g, scena, geo, xb, xb)
    evb = [salva("p1b-sana.json", db)]
    e, perche = giudica_p1b(xb, v1, v2, db)
    E.metti("F-014D", e, perche, atteso=xb, osservato="%r | %r" % (v1, v2), evidenze=evb)

    if not o.guasto:
        return
    # ── I GUASTI ───────────────────────────────────────────────────────────
    ad1 = F14.giudica_testo(F14.senza_accenti(t1), letto1)[0] == S.FAIL
    g1 = F14.testo_unico("P1G")
    lg1, dg1 = p1(g, scena, g1, copia=False)
    salva("p1-guasto.json", dg1)
    r1 = F14.giudica_testo(g1, lg1)[0] == S.FAIL
    E.guasto("F-015C", r1 and ad1,
             "Ctrl+C non fatto ⇒ gli appunti del computer valgono %r (%s); atteso senza "
             "accenti ⇒ %s" % ((lg1 or "")[:50], "ROSSO" if r1 else "VERDE",
                               "ROSSO" if ad1 else "VERDE"), atteso=g1, osservato=lg1)

    ad2 = all(F14.giudica_testo(F14.senza_accenti(r["atteso"]), r["visto"])[0] == S.FAIL
              for r in giri)
    rg = p2_giro(g, scena, geo, "P2G", copia_fuori=False)
    salva("p2-guasto.json", rg)
    r2 = rg["visto"] != rg["atteso"]
    E.guasto("F-014C", (r2 and ad2) if rg["gesto"] else None,
             "wl-copy non fatto ⇒ il campo vale %r (%s); atteso senza accenti ⇒ %s"
             % ((rg["visto"] or "")[:50], "ROSSO" if r2 else "VERDE",
                "ROSSO" if ad2 else "VERDE"), atteso=rg["atteso"], osservato=rg["visto"])

    adb = F14.giudica_testo(F14.senza_accenti(xb), v2)[0] == S.FAIL
    xg = F14.testo_unico("P1bG")
    yg = F14.testo_unico("P1bY")
    gv1, gv2, dgb = p1b(g, scena, geo, xg, yg)
    salva("p1b-guasto.json", dgb)
    rb = giudica_p1b(xg, gv1, gv2, dgb)[0] != S.PASS
    gesti = dgb["primo"]["gesto_arrivato"] and dgb["secondo"]["gesto_arrivato"]
    E.guasto("F-014D", (rb and adb) if gesti else None,
             "la seconda copia e' un altro testo ⇒ il campo vale %r (%s); atteso senza "
             "accenti ⇒ %s" % ((gv2 or "")[:50], "ROSSO" if rb else "VERDE",
                               "ROSSO" if adb else "VERDE"), atteso=xg, osservato=gv2)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
