#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c22 — ⭐⭐ «IL BORDO SI TRASCINA»
===========================================================================

    python3 11-c22-il-bordo-si-trascina.py --scatola kde [--browser firefox,chrome]
    python3 11-c22-il-bordo-si-trascina.py --porta 8513 --host 192.168.0.2
    python3 11-c22-il-bordo-si-trascina.py --scatola kde --senza-pulsante
    python3 11-c22-il-bordo-si-trascina.py --certifica

    che cosa deve essere vero : una finestra si RIDIMENSIONA trascinandone il
                                bordo col mouse dal browser — su GNOME, KDE,
                                XFCE e LXQt (l'utente, 24 set 2026: «rimane un
                                ultimo controllo: che il ridimensionamento
                                delle finestre con il trascinamento del bordo
                                sia implementato su tutti i DE»)
    da dove parte             : ⛔ da zero, un inquilino NUOVO (`c22u<n>`)
    che cosa guarda           : ⛔ **L'IMMAGINE**: il bordo destro della finestra
                                nella fotografia della tela, prima e dopo — non
                                un contatore di clic spediti
    come so che sa dare rosso : `--senza-pulsante` (lo stesso trascinamento a
                                pulsante ALZATO) ⇒ la finestra non cambia ⇒ ROSSO

⭐ LA SORELLA DI C21.  C21 prova che sul bordo la FORMA cambia (l'utente sa di
   poter afferrare); C22 prova che afferrando la finestra CAMBIA MISURA.  La
   scena e' la stessa, e le funzioni sono quelle di C21 — ⛔ IMPORTATE, non
   copiate: la pagina nota a fondo ciano, il profilo di Firefox con la misura
   fissata (`xulstore.json`), l'ESC che su GNOME esce dalla vista d'insieme,
   la ricerca della finestra nella fotografia, le conversioni foto⇄desktop⇄
   vetro.  Se una di quelle cambia, cambia per tutt'e due le maglie.

⭐ CHE COSA FA, per ogni browser (Firefox con Marionette, Chrome con CDP):
     1  crea l'inquilino `c22u<n>`, apre REMOTIX, entra, primo fotogramma
     2  ESC vero (la sveglia di C21), poi `firefox-esr` NORMALE sulla pagina
        nota, 45 % x 55 % dello schermo
     3  trova la finestra nella fotografia: il bordo destro `x_b` e' l'ultimo
        pixel ciano, a meta' altezza
     4  per ogni punto di presa `x_b + k`, k in `PRESE` (da 2 px dentro a 6
        fuori), a meta' altezza:
          preme il pulsante sinistro (evento VERO del browser: `pointerDown`
          di Marionette, `mousePressed` di CDP), trascina a destra di `SPINTA`
          px in `PASSI` passi a pulsante premuto, rilascia
        ⇒ fotografa, e rimisura: il bordo destro, il sinistro, l'alto.
     5  VERDE al primo punto in cui il bordo destro si e' spostato di almeno
        `SOGLIA` px e la finestra e' ancora LA STESSA (bordo sinistro e alto
        fermi, e il riquadro giallo dentro): si dichiara IN QUALE punto.

⛔⭐ PERCHE' UNA SCANSIONE DI PRESE E NON UN PUNTO — la zona di presa non sta
   nello stesso posto sui quattro desktop (`[M]` da C21, 24 set 2026):
     KWin (KDE)   SUL bordo, da 1 px dentro a 1 px fuori
     GNOME        nell'ombra della finestra, da ~+1 px
     labwc        dal pixel del bordo fino a 7 px fuori
   ⇒ Un punto fisso darebbe rosso a qualcuno per una cosa che il suo desktop
     fa apposta.  ⚠ La scansione si ferma al PRIMO verde: dopo, la finestra
     e' piu' larga, e continuare vorrebbe dire rimisurare tutto per un dato
     che la domanda dell'utente non chiede.

   ⭐ `[M]` 24 set 2026, prima misura, 4K, finestre vere nel labwc annidato del
     server: VERDE su gnome, kde, xfce e lxqt, Firefox 140 e Chrome 154, +150
     px su 150 ovunque; la presa e' a +1 px dall'ultimo pixel ciano (a +0 per
     Firefox su gnome), da -2 a 0 niente.  `--senza-pulsante`: guasto VISTO
     ovunque (9 punti fermi, poi il controllo sano verde).

⛔ PERCHE' «LA STESSA FINESTRA» — un trascinamento che SPOSTA la finestra
   (preso per la barra, o col gesto «Alt+trascina») porta a destra anche il
   bordo destro: di 150 px, piu' della soglia.  ⇒ Il verde vuole il bordo
   SINISTRO fermo (±`FERMO` px): se si sono mossi tutt'e due, e' uno
   spostamento, e lo si dice.

⛔ COME SO CHE SA DARE ROSSO — `--senza-pulsante`.
   Lo stesso gesto, gli stessi punti, gli stessi passi, ma il pulsante NON si
   preme: nessun desktop ridimensiona una finestra al solo passaggio.  ⇒ Su
   tutti i punti la finestra deve restare com'era, e la maglia deve dare ROSSO.
   ⭐ E poi il CONTROLLO SANO, nella stessa sessione: la scansione col
   pulsante deve dare verde.  Senza il controllo, un «rosso» a pulsante alzato
   potrebbe venire da un prodotto rotto e non dal guasto.
   ⛔ Si legge AL CONTRARIO, come ogni guasto della rete (`11-gancio.sh`,
     `esegui_maglia`): 0 = il guasto e' stato VISTO, 1 = NON visto, 3 = il
     controllo sano non era verde ⇒ non si e' potuto innestare niente.

⚠ ESITI: 0 verde · 1 rosso · 3 «non ho potuto guardare», col motivo.
   Il 3 e' del BANCO (la finestra non si vede, la pressione non e' arrivata
   alla PAGINA, il puntatore non e' dove dico); il rosso e' del PRODOTTO (la
   pagina ha spedito pressione e movimento, e la finestra non ha cambiato
   misura).

⚠ DOVE GIRA: sulla macchina che ha i browser (il server, `REMOTIX_SUL_SERVER=1`
  col `labwc` annidato), come C21; l'inquilino `c22u<n>` segue il modello di
  C19 (`^c[0-9]+b?u[0-9]+$`): se il banco morisse a meta', il gancio lo sgombera.
"""
import argparse
import importlib.util as _iu
import json
import os
import random
import re
import secrets
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))


def _carica(nome, file):
    s = _iu.spec_from_file_location(nome, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ⛔ Importata, non copiata: C21 porta con se' `12-c20-veri` e `12-client-veri`
#   — un solo VERI in memoria, e l'ESC gia' aggiunto alla tabella dei tasti.
C21 = _carica("c21", os.path.join(QUI, "11-c21-sul-bordo-la-forma-cambia.py"))
C20V, VERI = C21.C20V, C21.VERI
VERDE, ROSSO, CIECO = C21.VERDE, C21.ROSSO, C21.CIECO
PORTE = C21.PORTE
NOME_ESITO = C21.NOME_ESITO

MODELLO_INQUILINO = re.compile(r"^c22u[0-9]+$")

# ---------------------------------------------------------------------------
# ⛔ I NUMERI — ciascuno col suo perche'.
# ---------------------------------------------------------------------------
# ⭐ I punti di presa, in pixel del DESKTOP rispetto all'ultimo pixel ciano:
#   da 2 dentro a 6 fuori (le tre zone misurate stanno fra -1 e +7).
PRESE = tuple(range(-2, 7))
# Quanto si trascina, e in quanti passi: un gesto di mano, non un salto.
SPINTA = 150
PASSI = 15
PAUSA_PASSO_MS = 30
# ⭐ Il verde vuole almeno 100 px dei 150: il desktop puo' arrotondare la misura
#   (la griglia dei caratteri, un minimo, un'animazione non finita) ma un
#   ridimensionamento vero ne porta quasi tutti.
SOGLIA = 100
# Il bordo sinistro e l'alto devono restare fermi entro questi pixel: se no la
# finestra si e' SPOSTATA, non ridimensionata.
FERMO = 4
# Fra un punto e l'altro: piu' del doppio clic di ogni desktop (400-500 ms),
# cosi' due pressioni vicine non diventano un «doppio clic sul bordo».
FRA_I_PUNTI_S = 1.0


# ═══════════════════════════════════════════════════════════════════════════
#  LE FUNZIONI PURE — e sono quelle che `--certifica` prova
# ═══════════════════════════════════════════════════════════════════════════
def finestra_nel_desktop(geo, f):
    """La finestra trovata nella foto (`C21.trova_finestra`) in pixel del desktop:
    {sinistro, destro, alto} — il destro e' l'ULTIMO pixel ciano."""
    pw, ph = f["foto"]
    x0, y0 = C21.dalla_foto_al_desktop(geo, pw, ph, f["ciano"][0] + 0.5, f["ciano"][1] + 0.5)
    xd, _ = C21.dalla_foto_al_desktop(geo, pw, ph, f["destro"] + 0.5, f["centro"][1] + 0.5)
    return {"sinistro": int(x0), "destro": int(xd), "alto": int(y0)}


def giudica_presa(k, prima, dopo):
    """⭐ Il giudizio di UN punto di presa.

    `prima`, `dopo`  {sinistro, destro, alto} in pixel del desktop, o None
    Torna (esito, motivo, spostamento del bordo destro | None)."""
    if not dopo:
        return CIECO, "%+d px: dopo il trascinamento la finestra non si vede piu'" % k, None
    sp = dopo["destro"] - prima["destro"]
    ds = dopo["sinistro"] - prima["sinistro"]
    da = dopo["alto"] - prima["alto"]
    fermi = abs(ds) <= FERMO and abs(da) <= FERMO
    if sp >= SOGLIA and fermi:
        return VERDE, ("%+d px: il bordo destro e' andato da x=%d a x=%d (%+d px), il "
                       "sinistro e l'alto fermi — RIDIMENSIONATA"
                       % (k, prima["destro"], dopo["destro"], sp)), sp
    if sp >= SOGLIA:
        return ROSSO, ("%+d px: il bordo destro %+d px ma anche il sinistro %+d e l'alto "
                       "%+d — la finestra si e' SPOSTATA, non ridimensionata" % (k, sp, ds, da)), sp
    return ROSSO, ("%+d px: il bordo destro %+d px (serve %d), il sinistro %+d — la misura "
                   "non e' cambiata" % (k, sp, SOGLIA, ds)), sp


def giudica_scansione(risultati):
    """[(k, esito, motivo, sp)] ⇒ (esito, motivo, (k, sp) | None).

    VERDE al primo punto verde; ROSSO se tutti i punti sono stati guardati e
    nessuno e' verde; CIECO se un punto non si e' potuto guardare prima di un
    verde (la finestra sparita non e' un «non ridimensiona»)."""
    if not risultati:
        return CIECO, "nessun punto di presa provato", None
    for k, e, m, sp in risultati:
        if e == VERDE:
            return VERDE, m, (k, sp)
        if e == CIECO:
            return CIECO, m, None
    return ROSSO, ("in NESSUNO dei %d punti di presa (da %+d a %+d px dal bordo) la finestra "
                   "ha cambiato misura: %s" % (len(risultati), risultati[0][0], risultati[-1][0],
                                              "; ".join(r[2] for r in risultati[-2:]))), None


def verdetto_col_guasto(senza, sano):
    """⭐ Il guasto innestato, letto al contrario.

    `senza`  (esito, motivo, x) della scansione a pulsante ALZATO
    `sano`   (esito, motivo, x) del controllo col pulsante, o None
    Torna (esito della maglia col guasto, motivo)."""
    if senza[0] == VERDE:
        return ROSSO, ("⛔ GUASTO NON VISTO: a pulsante alzato la finestra ha cambiato misura "
                       "lo stesso (%s)" % senza[1])
    if senza[0] == CIECO:
        return CIECO, "a pulsante alzato non ho potuto guardare: %s" % senza[1]
    if not sano or sano[0] != VERDE:
        return CIECO, ("il controllo sano non e' verde (%s): il guasto non si puo' innestare"
                       % (sano[1] if sano else "non fatto"))
    return VERDE, ("⭐ GUASTO VISTO: a pulsante alzato nessun punto ridimensiona, col pulsante "
                   "si' (%s)" % sano[1])


def gesto(x0, y0, dx, passi):
    """I punti del trascinamento, in pixel del desktop: la partenza esclusa."""
    return [(x0 + dx * (i + 1) / float(passi), y0) for i in range(passi)]


# ═══════════════════════════════════════════════════════════════════════════
#  LA CERTIFICAZIONE DELLE FUNZIONI PURE
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    print("⭐ 11-c22 · CERTIFICAZIONE DELLE FUNZIONI PURE")
    guai, fatte = [], []

    def prova(cosa, vero, dettaglio=""):
        fatte.append(cosa)
        print("   %s %s%s" % ("⭐ ok  " if vero else "⛔ NO  ", cosa,
                              (" — " + dettaglio) if dettaglio else ""))
        if not vero:
            guai.append(cosa)

    P = {"sinistro": 80, "destro": 1807, "alto": 80}
    casi = [
        ("allargata di 150, sinistro fermo ⇒ VERDE",
         {"sinistro": 80, "destro": 1957, "alto": 80}, VERDE),
        ("allargata di 120 (arrotondata) ⇒ VERDE",
         {"sinistro": 81, "destro": 1927, "alto": 80}, VERDE),
        ("allargata di 60 ⇒ ROSSO", {"sinistro": 80, "destro": 1867, "alto": 80}, ROSSO),
        ("ferma ⇒ ROSSO", dict(P), ROSSO),
        ("SPOSTATA di 150 (tutti e due i bordi) ⇒ ROSSO",
         {"sinistro": 230, "destro": 1957, "alto": 80}, ROSSO),
        ("allargata ma l'alto si e' mosso ⇒ ROSSO",
         {"sinistro": 80, "destro": 1957, "alto": 140}, ROSSO),
        ("sparita ⇒ 3", None, CIECO),
    ]
    for nome, dopo, atteso in casi:
        e, m, _sp = giudica_presa(3, P, dopo)
        prova("giudica_presa: %s" % nome, e == atteso, m)
    r = [(-2, ROSSO, "a", 0), (-1, ROSSO, "b", 1), (0, VERDE, "c", 148)]
    e, m, x = giudica_scansione(r)
    prova("giudica_scansione: verde a 0 px ⇒ VERDE, e dice dove", e == VERDE and x == (0, 148), m)
    e, m, x = giudica_scansione([(k, ROSSO, "fermo", 0) for k in PRESE])
    prova("giudica_scansione: nessun punto ⇒ ROSSO", e == ROSSO, m)
    e, m, x = giudica_scansione([(-2, ROSSO, "a", 0), (-1, CIECO, "sparita", None)])
    prova("giudica_scansione: sparita prima di un verde ⇒ 3", e == CIECO, m)
    prova("giudica_scansione: vuota ⇒ 3", giudica_scansione([])[0] == CIECO)
    # il guasto, letto al contrario
    R, V, Cc = (ROSSO, "fermo", None), (VERDE, "+1 px", (1, 150)), (CIECO, "sparita", None)
    for nome, senza, sano, atteso in [
            ("alzato fermo, sano verde ⇒ 0 (visto)", R, V, VERDE),
            ("alzato RIDIMENSIONA ⇒ 1 (non visto)", V, V, ROSSO),
            ("alzato fermo, sano ROSSO ⇒ 3", R, (ROSSO, "fermo", None), CIECO),
            ("alzato fermo, sano non fatto ⇒ 3", R, None, CIECO),
            ("alzato cieco ⇒ 3", Cc, V, CIECO)]:
        e, m = verdetto_col_guasto(senza, sano)
        prova("verdetto_col_guasto: %s" % nome, e == atteso, m)
    g = gesto(100, 50, SPINTA, PASSI)
    prova("gesto: %d passi, l'ultimo a +%d" % (PASSI, SPINTA),
          len(g) == PASSI and g[-1] == (100 + SPINTA, 50) and g[0][0] > 100)
    # la finestra nella foto ⇒ nel desktop (geometria 1:1 e 2:1)
    f = {"foto": [400, 250], "ciano": [50, 40, 299, 199], "destro": 299, "centro": [174, 118]}
    geo = {"bw": 400, "bh": 250, "bx0": 0, "by0": 0, "sx": 1.0, "sy": 1.0}
    d = finestra_nel_desktop(geo, f)
    prova("finestra_nel_desktop 1:1", d == {"sinistro": 50, "destro": 299, "alto": 40}, str(d))
    geo2 = dict(geo, bw=800, bh=500)
    d2 = finestra_nel_desktop(geo2, f)
    prova("finestra_nel_desktop con la foto a meta'", d2["destro"] == 599, str(d2))
    print()
    if guai:
        print("⛔ CERTIFICAZIONE FALLITA: %d prove su %d" % (len(guai), len(fatte)))
        return 1
    print("⭐ CERTIFICATO: il giudice distingue ridimensionata, ferma e SPOSTATA, e il\n"
          "   guasto si legge al contrario solo col controllo sano verde.")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
#  DENTRO LA PAGINA — che cosa ha visto, per separare il banco dal prodotto
# ═══════════════════════════════════════════════════════════════════════════
JS_OSSERVA = r"""
(function () {
  if (window.__C22__) return;
  const C = window.__C22__ = { giu: 0, su: 0, premuti: 0, alzati: 0 };
  addEventListener('mousedown', function () { C.giu++; }, true);
  addEventListener('mouseup', function () { C.su++; }, true);
  addEventListener('pointermove', function (e) {
    if (e.pointerType === 'touch') return;
    if (e.buttons & 1) C.premuti++; else C.alzati++;
  }, true);
})();
"""
JS_AZZERA = ("const C=window.__C22__; if(!C) return false; "
             "C.giu=0; C.su=0; C.premuti=0; C.alzati=0; return true;")
JS_CONTA = r"""
const C = window.__C22__;
const st = window.REMOTIX && REMOTIX.input_classico ? REMOTIX.input_classico.stato() : null;
return C ? { giu: C.giu, su: C.su, premuti: C.premuti, alzati: C.alzati,
             spedito: st ? st.ultimo_spedito : null } : null;
"""


def trascina(g, geo, X, Y, premi):
    """⭐ Il gesto, con EVENTI VERI del browser: si porta il puntatore su (X,Y),
    si preme (se `premi`), si trascina a destra di `SPINTA` px in `PASSI`
    passi, si rilascia.  (X,Y) e i punti sono pixel del DESKTOP."""
    punti = [C21.dal_desktop_al_vetro(geo, X, Y)] + \
        [C21.dal_desktop_al_vetro(geo, x, y) for x, y in gesto(X, Y, SPINTA, PASSI)]
    if hasattr(g, "cdp"):
        c = g.cdp.chiama
        x0, y0 = punti[0]
        c("Input.dispatchMouseEvent", type="mouseMoved", x=x0, y=y0)
        time.sleep(0.15)
        if premi:
            c("Input.dispatchMouseEvent", type="mousePressed", x=x0, y=y0, button="left",
              buttons=1, clickCount=1)
        time.sleep(0.2)
        for x, y in punti[1:]:
            if premi:
                c("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y, button="left",
                  buttons=1)
            else:
                c("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
            time.sleep(PAUSA_PASSO_MS / 1000.0)
        time.sleep(0.2)
        if premi:
            x, y = punti[-1]
            c("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button="left",
              buttons=0, clickCount=1)
        return
    # Marionette: UNA catena di azioni, cosi' il pulsante resta giu' fra i passi
    az = [{"type": "pointerMove", "x": int(round(punti[0][0])), "y": int(round(punti[0][1])),
           "origin": "viewport", "duration": 0},
          {"type": "pause", "duration": 150}]
    if premi:
        az.append({"type": "pointerDown", "button": 0})
    az.append({"type": "pause", "duration": 200})
    for x, y in punti[1:]:
        az.append({"type": "pointerMove", "x": int(round(x)), "y": int(round(y)),
                   "origin": "viewport", "duration": 0})
        az.append({"type": "pause", "duration": PAUSA_PASSO_MS})
    az.append({"type": "pause", "duration": 200})
    if premi:
        az.append({"type": "pointerUp", "button": 0})
    g._azioni([{"type": "pointer", "id": "topo", "parameters": {"pointerType": "mouse"},
                "actions": az}])


def misura(g, geo, o, nome, etichetta):
    """La finestra nel desktop, dalla fotografia (ferma), o (None, motivo)."""
    f, perche = C21.cerca_la_finestra(g, o.attesa_finestra, "", nome)
    if not f:
        return None, perche
    if o.salva:
        try:
            with open(os.path.join(o.salva, "%s-%s.png" % (nome, etichetta)), "wb") as fh:
                fh.write(C21.foto_piena(g))
        except Exception:                        # noqa: BLE001
            pass
    return dict(finestra_nel_desktop(geo, f), cy=f["centro"][1], f=f), ""


def scansiona(g, geo, o, nome, premi):
    """⭐ La scansione dei punti di presa.  Torna (esito, motivo, x, righe)."""
    righe = []
    for k in PRESE:
        prima, perche = misura(g, geo, o, nome, "prima%+d" % k)
        if not prima:
            righe.append((k, CIECO, "%+d px: prima del gesto la finestra non si vede: %s"
                          % (k, perche), None))
            break
        pw, ph = prima["f"]["foto"]
        _x, Yc = C21.dalla_foto_al_desktop(geo, pw, ph, 0, prima["cy"] + 0.5)
        X = prima["destro"] + k + 0.5
        if X + SPINTA + 2 >= geo["tl"]:
            righe.append((k, CIECO, "%+d px: a destra non c'e' posto per trascinare (bordo "
                          "x=%d, schermo %d)" % (k, prima["destro"], geo["tl"]), None))
            break
        g.js(JS_AZZERA)
        trascina(g, geo, X, Yc, premi)
        time.sleep(0.3)
        n = g.js(JS_CONTA) or {}
        # ⛔ Il banco prima del prodotto: se la pagina non ha visto il gesto,
        #   non c'e' niente da giudicare.
        if premi and (n.get("giu", 0) < 1 or n.get("su", 0) < 1
                      or n.get("premuti", 0) < PASSI // 2):
            righe.append((k, CIECO, "%+d px: il browser non ha consegnato il gesto alla pagina "
                          "(%s)" % (k, n), None))
            break
        if not premi and (n.get("giu", 0) or n.get("alzati", 0) < PASSI // 2):
            righe.append((k, CIECO, "%+d px: il gesto a pulsante alzato non e' arrivato come "
                          "doveva (%s)" % (k, n), None))
            break
        sp_ = n.get("spedito") or [-1, -1]
        atteso_x = int(X + SPINTA)
        if abs(sp_[0] - atteso_x) > 2 or abs(sp_[1] - int(Yc)) > 2:
            righe.append((k, CIECO, "%+d px: la pagina ha spedito per ultimo (%s,%s) invece di "
                          "(%d,%d): il puntatore non e' dove dico"
                          % (k, sp_[0], sp_[1], atteso_x, int(Yc)), None))
            break
        dopo, perche = misura(g, geo, o, nome, "dopo%+d" % k)
        e, m, sp = giudica_presa(k, prima, dopo)
        if not dopo:
            m += " (%s)" % perche
        print("   %s presa %+d px (x=%d, y=%d)%s → %s" % (
            {VERDE: "⭐", ROSSO: "·", CIECO: "⚠"}[e], k, int(X), int(Yc),
            "" if premi else " a pulsante ALZATO", m), flush=True)
        righe.append((k, e, m, sp))
        if e != ROSSO:
            break
        time.sleep(FRA_I_PUNTI_S)
    es, ms, x = giudica_scansione(righe)
    return es, ms, x, righe


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA DI UN BROWSER
# ═══════════════════════════════════════════════════════════════════════════
def prova_browser(nome, o, sc, chi):
    print("\n══ %s ══════════════════════════════" % nome.upper(), flush=True)
    riga = {"browser": nome}
    g = VERI.accendi_guida(nome, o)
    try:
        print("   palco: %s" % g.palco(), flush=True)
        if o.largo:
            print("   %s" % C20V.dimensiona(g, nome, o.largo, o.alto), flush=True)
        pr = VERI.Prova(g, o, o.url, o.parola)
        ok, m = pr.apri()
        if not ok:
            return dict(riga, esito=CIECO, perche="la pagina non si apre: " + m)
        e, m, s = pr.entra(o.parola)
        if e != VERDE:
            return dict(riga, esito=CIECO, perche="l'accesso: " + m)
        e, m, s = pr.primo_fotogramma()
        e, m = C20V.desktop_scuro_ma_vivo(e, m, s)
        print("   ⭐ primo fotogramma: %s" % m, flush=True)
        if e != VERDE:
            return dict(riga, esito=CIECO, perche="senza immagine non si guarda: " + m)
        geo = g.js(C21.JS_GEOMETRIA)
        if not geo:
            return dict(riga, esito=CIECO, perche="`REMOTIX_PUNTATORE.geometria` non c'e'")
        print("   tela %sx%s · buffer %sx%s · disposizione «%s»"
              % (geo["tl"], geo["ta"], geo["bw"], geo["bh"], geo["disposizione"]), flush=True)
        if geo["disposizione"] != "classico":
            # ⛔ Il mouse con pulsanti e' della disposizione classica; col dito
            #   il trascinamento e' un altro gesto, e non e' questa domanda.
            return dict(riga, esito=CIECO, perche="la pagina non e' nella disposizione "
                        "classica (%s)" % geo["disposizione"])
        # ⚠ La sveglia di C21 (GNOME nasce nella vista d'insieme), PRIMA della finestra
        print("   sveglia: %s" % C21.sveglia(g, geo), flush=True)
        largo_f, alto_f = geo["tl"] * 0.45, geo["ta"] * 0.55
        ok, t = C21.prepara_la_casa(sc, chi, largo_f, alto_f)
        if not ok:
            return dict(riga, esito=CIECO, perche="la casa non si prepara: %s" % t[-200:])
        ok, t = C21.accendi_la_finestra(sc, chi)
        if not ok:
            return dict(riga, esito=CIECO, perche="firefox-esr non parte: %s" % t[-200:])
        w0, perche = misura(g, geo, o, nome, "finestra")
        if not w0:
            return dict(riga, esito=CIECO, perche="la finestra di prova non si vede in %d s: %s"
                        % (o.attesa_finestra, perche))
        if w0["destro"] - w0["sinistro"] < 0.7 * largo_f:
            return dict(riga, esito=CIECO, perche="la finestra e' larga %d px e ne ho chiesti "
                        "%d: e' un'anteprima (la vista d'insieme?), non la finestra"
                        % (w0["destro"] - w0["sinistro"], largo_f))
        riga["finestra"] = {k: w0[k] for k in ("sinistro", "destro", "alto")}
        print("   ⭐ finestra: x=%d..%d, alto y=%d nel desktop · prese da %+d a %+d px"
              % (w0["sinistro"], w0["destro"], w0["alto"], PRESE[0], PRESE[-1]), flush=True)
        g.js(VERI._inietta(JS_OSSERVA))
        if not g.js("return !!window.__C22__;"):
            return dict(riga, esito=CIECO, perche="l'osservatore non si e' installato")

        if not o.senza_pulsante:
            es, ms, x, righe = scansiona(g, geo, o, nome, True)
            riga["prese"] = [[k, e, m] for k, e, m, _ in righe]
            if x:
                riga["presa_px"], riga["spostamento_px"] = x
            return dict(riga, esito=es, perche=ms)
        # ── il guasto innestato: prima a pulsante alzato, poi il controllo ──
        print("   ── --senza-pulsante: lo stesso gesto, pulsante ALZATO ──", flush=True)
        senza = scansiona(g, geo, o, nome, False)
        riga["senza_pulsante"] = [[k, e, m] for k, e, m, _ in senza[3]]
        sano = None
        if senza[0] == ROSSO:
            print("   ── il controllo sano: col pulsante ──", flush=True)
            sano = scansiona(g, geo, o, nome, True)
            riga["sano"] = [[k, e, m] for k, e, m, _ in sano[3]]
            if sano[2]:
                riga["presa_px"], riga["spostamento_px"] = sano[2]
        eg, mg = verdetto_col_guasto(senza[:3], sano[:3] if sano else None)
        return dict(riga, esito=eg, perche=mg)
    finally:
        try:
            g.chiudi()
        except Exception as ex:                  # noqa: BLE001
            print("   ⚠ chiusura del browser: %s" % ex)


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--scatola", choices=sorted(PORTE))
    a.add_argument("--porta", type=int)
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--browser", default="firefox,chrome")
    a.add_argument("--visibile", action="store_true",
                   help="finestre vere (nel compositore annidato) invece di headless")
    a.add_argument("--salva", default="", help="cartella per le fotografie")
    a.add_argument("--senza-pulsante", action="store_true",
                   help="GUASTO INNESTATO: lo stesso trascinamento a pulsante alzato")
    a.add_argument("--certifica", action="store_true")
    a.add_argument("--attesa-finestra", type=int, default=60)
    a.add_argument("--tetto-s", type=int, default=45)
    a.add_argument("--porte-base", type=int, default=2961)
    a.add_argument("--largo", type=int, default=3840)
    a.add_argument("--alto", type=int, default=2160)
    o = a.parse_args()
    if o.certifica:
        return certifica()
    if not o.scatola and o.porta:
        o.scatola = {p: s for s, p in PORTE.items()}.get(o.porta)
    if not o.scatola:
        print("⛔ serve --scatola, o una --porta della rete (%s)" % PORTE)
        return 3
    porta = o.porta or PORTE[o.scatola]
    # ⚠ i campi che le guide e `Prova` di 12-client-veri si aspettano
    o.url = "https://%s:%d/" % (o.host, porta)
    o.parola = "c22-" + secrets.token_hex(6)
    o.scena, o.continuita_s, o.registro_cmd = "viva", 8, ""
    o.lascia_acceso = False
    if o.salva:
        os.makedirs(o.salva, exist_ok=True)
    sc = C20V.Scatola(o.scatola)
    chi = "c22u%03d" % random.randint(0, 999)
    assert MODELLO_INQUILINO.match(chi)
    o.utente = chi
    print("⭐ 11-c22 · %s · %s · inquilino %s · browser %s · %s%s"
          % (sc.contenitore, o.url, chi, o.browser,
             "finestre vere" if o.visibile else "HEADLESS",
             " · ⛔ GUASTO INNESTATO --senza-pulsante" if o.senza_pulsante else ""))
    righe = []
    for b in [x.strip() for x in o.browser.split(",") if x.strip()]:
        sc.sgombera(chi)
        c, t = sc.crea(chi, o.parola)
        if c != 0:
            print("⛔ non ho potuto creare %s: %s" % (chi, t[-200:]))
            return 3
        try:
            r = prova_browser(b, o, sc, chi)
        except Exception as e:                   # noqa: BLE001
            r = {"browser": b, "esito": CIECO, "perche": "il banco e' caduto: %r" % e}
        finally:
            sc.sgombera(chi)
        print("   ▶ %s: %s — %s" % (b, NOME_ESITO.get(r["esito"], r["esito"]),
                                   r.get("perche")))
        print("RIGA " + json.dumps(r, ensure_ascii=False), flush=True)
        righe.append(r)
    v = [r["esito"] for r in righe]
    esito = ROSSO if ROSSO in v else (CIECO if CIECO in v else VERDE)
    print()
    if o.senza_pulsante:
        print({VERDE: "⭐ IL GUASTO INNESTATO E' STATO VISTO (esito 0: al contrario, "
                      "come ogni guasto della rete)",
               ROSSO: "⛔⛔ IL GUASTO INNESTATO NON E' STATO VISTO",
               CIECO: "⚠ col guasto innestato NON ho potuto guardare ⇒ 3"}[esito])
    else:
        print("%s C22(%s): %s" % ({VERDE: "⭐", ROSSO: "⛔⛔", CIECO: "⚠"}[esito],
                                  o.scatola, NOME_ESITO[esito]))
    return esito


if __name__ == "__main__":
    sys.exit(main())
