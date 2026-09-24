#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c21 — ⭐⭐ «SUL BORDO LA FORMA CAMBIA»
===========================================================================

    python3 11-c21-sul-bordo-la-forma-cambia.py --scatola gnome [--browser firefox,chrome]
    python3 11-c21-sul-bordo-la-forma-cambia.py --porta 8513 --host 192.168.0.2
    python3 11-c21-sul-bordo-la-forma-cambia.py --scatola gnome --forma-sbagliata
    python3 11-c21-sul-bordo-la-forma-cambia.py --certifica

    che cosa deve essere vero : la FORMA VERA del puntatore arriva al browser —
                                su GNOME, KDE, XFCE e LXQt (decisione
                                dell'utente, 24 set 2026)
    da dove parte             : ⛔ da zero, un inquilino NUOVO (`c21u<n>`)
    che cosa guarda           : ⛔ **L'IMMAGINE** del cursore che la pagina fa
                                indossare al browser — non un contatore
    come so che sa dare rosso : `--forma-sbagliata` (la tabella delle attese
                                spostata di uno) ⇒ ROSSO, sulle stesse immagini

⛔⛔ PERCHE' ESISTE, E PERCHE' COI BROWSER VERI.
   Oggi (24 set 2026) la forma del cursore arriva solo da GNOME: sugli altri
   tre desktop la pagina mostra sempre la freccia, e sul bordo di una finestra
   l'utente non sa di poterla ridimensionare.  ⇒ La prova si scrive PRIMA del
   prodotto, e sui desktop dove la forma non arriva deve dare rosso.
   ⚠ Coi browser veri e non col cliente Python: l'utente, 23 set 2026, *«i test
     vanno fatti con i browser veri, non con emulatori»*.  E qui c'e' una
     ragione in piu': la forma la INDOSSA IL BROWSER (`cursor: url(...) hx hy`),
     e il cliente Python non ha un cursore da vestire.

⭐ CHE COSA FA, per ogni browser (Firefox con Marionette, Chrome con CDP: i
   guidatori sono quelli di `banchi/12-client-veri.py`, e l'ingresso nella
   scatola e' quello di `banchi/12-c20-veri.py` — ⛔ importati, non copiati):
     1  crea l'inquilino `c21u<n>` e gli mette in casa una PAGINA NOTA
        (`PAGINA`: fondo ciano, un riquadro giallo di testo) e un profilo di
        Firefox con la finestra di misura dichiarata (`xulstore.json`)
     2  apre REMOTIX, entra, aspetta il primo fotogramma non degenere
     3  dentro la sessione accende `firefox-esr` NORMALE — ⛔ non `--kiosk`,
        che non ha bordi — sulla pagina nota
     4  trova la finestra NELLA FOTOGRAFIA della tela: il ciano e' la pagina, e
        il suo ultimo pixel a destra e' il bordo destro della finestra.  ⚠ Si
        cerca nei pixel perche' non c'e' uno strumento comune ai quattro
        desktop per chiedere il rettangolo di una finestra (GNOME non espone
        `wlr-foreign-toplevel`, e dentro la scatola non c'e' `lswt`).
     5  muove il puntatore con EVENTI VERI del browser (`pointerMove` di
        Marionette, `Input.dispatchMouseEvent` di CDP), in quattro passi:
          partenza  sul testo            (prepara: la forma di prima e' nota)
          centro    al centro della finestra     ⇒ attesa «freccia»
          bordo     una SCANSIONE sul bordo destro, da 4 px dentro a 8 px
                    fuori, un pixel per passo  ⇒ attesa «orizzontale»
                    in almeno un punto della scansione
          testo     sul riquadro giallo          ⇒ attesa «testo»
        ⭐ La partenza sul testo c'e' perche' ogni passo giudicato sia un
          CAMBIO: sul desktop nudo il cursore e' gia' una freccia, e un
          «centro» che non cambia non proverebbe niente.
     6  per ogni passo legge nella pagina la regola `cursor` che la pagina da'
        alla tela (`#schermo`, `cl_applica_modo()` in `src/pagina.html`
        ~9212-9222, che la prende da `REMOTIX_PUNTATORE.forma()` ~9145-9186):
        un'immagine PNG e il suo punto attivo.  Un osservatore
        (`MutationObserver`) scrive l'ISTANTE di ogni cambio, e un ascoltatore
        l'istante del movimento: la latenza e' misurata DENTRO la pagina.

⛔⛔ IL METRO — L'IMMAGINE, NON UN CONTATORE.
   `LEZIONI` del progetto: *«i contatori non vedono l'immagine»* — un
   `CURSORE_FORMA` ricevuto conta come uno giusto anche se porta la freccia.
   ⇒ Ogni immagine si CLASSIFICA dai suoi pixel (`classifica()`): si prende la
   sagoma (alfa >= 128), il suo rettangolo, e dove cade il punto attivo:
     freccia      punto attivo nell'angolo in alto a sinistra della sagoma
     orizzontale  la freccia di ridimensionamento orizzontale: punto attivo a
                  meta' altezza, sagoma simmetrica sopra/sotto, sottile, con
                  l'asta ORIZZONTALE che passa per il punto attivo
     testo        punto attivo al centro, sagoma piu' alta che larga
   ⛔⭐ `[M]` 24 set 2026, gnome: l'«e-resize» di Adwaita NON e' la freccia
       doppia col punto attivo al centro che ci si aspettava — e' UNA freccia
       che punta a destra contro una barra, 18x17, col punto attivo sulla
       barra (0,92 della larghezza, 0,56 dell'altezza).  ⇒ La classe non
       pretende il centro orizzontale: pretende la meta' ALTEZZA e l'asta
       orizzontale.  La doppia di Breeze (`size_hor`) ci sta dentro lo stesso.
     nascosta  `cursor: none` (§5.5, larghezza e altezza zero)
     altra     tutto il resto (una mano, una clessidra, ...)
   E un passo e' VERDE solo se la forma IN VIGORE `TETTO_MS` (300 ms) dopo il
   movimento e' della classe attesa, ed e' ARRIVATA dopo il movimento.

⛔⭐ PERCHE' IL BORDO E' UNA SCANSIONE E NON UN PUNTO — la zona di
   ridimensionamento NON sta nello stesso posto sui quattro desktop:
     `[M]` KWin (KDE)  `size_hor` solo SUL bordo (da 1 px dentro a 1 px
                       fuori); a 3 px fuori c'e' gia' la freccia normale
     `[M]` labwc       dal pixel del bordo fino a 7 px fuori
     `[M]` GNOME       nell'ombra della finestra (Firefox disegna i suoi
                       bordi): `[M]` da questa maglia: da +1 px
   ⇒ Un «3 px fuori» fisso darebbe rosso a KWin per una cosa che KWin fa
     apposta.  Si cammina da `SCANSIONE[0]` a `SCANSIONE[-1]` px dal bordo
     (l'ultimo pixel della pagina), un pixel per passo, `PASSO_SCANSIONE_S`
     per passo: VERDE se in un punto la forma diventa «orizzontale» entro
     300 ms dal movimento che l'ha portata, e il rapporto dice DOVE.

⛔ COME SO CHE SA DARE ROSSO — `--forma-sbagliata`.
   La tabella delle attese si sposta di uno (centro⇒orizzontale, bordo⇒testo,
   testo⇒freccia) e si giudicano LE STESSE IMMAGINI due volte:
     · con la tabella giusta      ⇒ deve essere VERDE (il controllo sano)
     · con la tabella spostata    ⇒ deve essere ROSSO
   ⭐ Il rosso puo' venire solo dalle classi, cioe' dai PIXEL: il numero dei
     cambi e i tempi sono gli stessi nei due giudizi.
   ⛔ Si legge AL CONTRARIO, come ogni guasto della rete (`11-gancio.sh`,
     `esegui_maglia`): 0 = il guasto e' stato VISTO, 1 = NON visto, 3 = il
     controllo sano non era verde ⇒ non si e' potuto innestare niente.

⚠ ESITI: 0 verde · 1 rosso · 3 «non ho potuto guardare», col motivo.
   Il 3 e' del BANCO (la finestra non si vede, il movimento non e' partito,
   la pagina non e' nel modo `sistema`); il rosso e' del PRODOTTO (la forma
   non arriva, arriva tardi, o e' sbagliata).

⚠ DOVE GIRA: sulla macchina che ha i browser (il server, `REMOTIX_SUL_SERVER=1`
  con `labwc` annidato — `[M]` 24 set 2026, il tablet e' il collo), e si entra
  nella scatola con `fondamenta/strumenti/sshpw.py` + `podman exec`, come
  `12-c20-veri.py`.  ⚠ L'inquilino e' `c21u<n>` (modello di C19
  `^c[0-9]+b?u[0-9]+$`): se il banco morisse a meta', il gancio lo sgombera.
"""
import argparse
import base64
import importlib.util as _iu
import io
import json
import os
import random
import re
import secrets
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
BANCHI = os.path.dirname(QUI)


def _carica(nome, file):
    s = _iu.spec_from_file_location(nome, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ⛔ Importati, non copiati: i guidatori dei browser e la strada nella scatola.
#   `12-c20-veri` porta con se' `12-client-veri` (VERI) — uno solo in memoria.
C20V = _carica("c20_veri", os.path.join(BANCHI, "12-c20-veri.py"))
VERI = C20V.VERI
VERDE, ROSSO, CIECO = VERI.VERDE, VERI.ROSSO, VERI.CIECO
PORTE = C20V.PORTE
NOME_ESITO = {VERDE: "VERDE", ROSSO: "ROSSO", CIECO: "NON HO POTUTO GUARDARE"}

# ⭐ L'inquilino: un nome della rete, che C19 riconosce e il gancio sgombera.
MODELLO_INQUILINO = re.compile(r"^c21u[0-9]+$")

# ---------------------------------------------------------------------------
# ⛔ I NUMERI — ciascuno col suo perche'.
# ---------------------------------------------------------------------------
# La richiesta dell'utente: la forma cambia entro 300 ms dal movimento.
TETTO_MS = 300.0
# Quanto si guarda DOPO il tetto: non per dare verde, ma per dire QUANDO e'
# arrivata una forma tardiva (un rosso «a 450 ms» si cura, «mai» e' un altro
# difetto).
GUARDA_S = 2.0
# ⭐ La scansione del bordo destro, in pixel del DESKTOP rispetto all'ultimo
#   pixel della pagina: da 4 dentro a 8 fuori (le tre zone misurate stanno fra
#   -1 e +7).  ⚠ Il passo dura piu' del tetto, cosi' ogni cambio si attribuisce
#   a UN movimento solo: quello subito prima.
SCANSIONE = tuple(range(-4, 9))
PASSO_SCANSIONE_S = 0.4
# I colori della pagina, e la tolleranza: la catena passa per H.264 4:2:0, che
# sottocampiona il croma (§4.3 di fase 11, la stessa ragione di C2).
CIANO = (0x00, 0xFF, 0xFF)
GIALLO = (0xFF, 0xFF, 0x00)
TOLLERANZA = 60
# La finestra dev'essere almeno questa quota della tela, o e' un rimasuglio.
AREA_MINIMA = 0.02
# La soglia di alfa della sagoma: i bordi morbidi del tema non sono sagoma.
ALFA = 128

# ⭐ LA TABELLA DELLE ATTESE, e la stessa spostata di uno (il guasto).
PASSI = ("centro", "bordo", "testo")
ATTESO = {"centro": "freccia", "bordo": "orizzontale", "testo": "testo"}
ATTESO_SBAGLIATO = {"centro": "orizzontale", "bordo": "testo", "testo": "freccia"}

# ⭐ LA PAGINA NOTA.  Fondo ciano con `cursor: default`, e un riquadro giallo
#   con `cursor: text` in alto a sinistra — lontano dal centro, cosi' il centro
#   della finestra e' ciano puro.  ⚠ Le regole `cursor` sono dichiarate e non
#   lasciate al motore: senza, la freccia di testo comparirebbe solo sopra i
#   glifi e fra una lettera e l'altra si tornerebbe alla freccia.
#   ⛔ Nessuna risorsa esterna: la scatola non ha rete verso fuori.
PAGINA = """<!doctype html>
<meta charset="utf-8"><title>REMOTIX C21</title>
<style>
 html,body{margin:0;padding:0;width:100%;height:100%;background:#00FFFF;cursor:default;overflow:hidden}
 #t{position:absolute;left:6%;top:8%;width:34%;height:30%;background:#FFFF00;color:#000;
    cursor:text;font:28px/1.25 sans-serif;overflow:hidden}
</style>
<div id="t">REMOTIX C21 &mdash; il puntatore sopra questo testo deve diventare
la barra del testo. REMOTIX C21 &mdash; testo testo testo testo testo testo
testo testo testo testo testo testo testo testo testo testo testo testo</div>
"""
PROFILO = ".c21-profilo"
FILE_PAGINA = "c21-finestra.html"
PREFERENZE = """user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("startup.homepage_welcome_url", "");
user_pref("startup.homepage_welcome_url.additional", "");
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.reportingpolicy.firstRun", false);
user_pref("browser.sessionstore.resume_from_crash", false);
user_pref("browser.tabs.warnOnClose", false);
"""


def xulstore(largo, alto):
    """⭐ La misura della finestra di Firefox, dichiarata nel profilo.

    ⛔ Una finestra massimizzata non ha bordo destro dentro lo schermo: senza
       questa riga la prova dipenderebbe da che cosa decide il desktop."""
    return json.dumps({"chrome://browser/content/browser.xhtml": {"main-window": {
        "width": str(int(largo)), "height": str(int(alto)),
        "screenX": "80", "screenY": "80", "sizemode": "normal"}}})


# ═══════════════════════════════════════════════════════════════════════════
#  LE FUNZIONI PURE — e sono quelle che `--certifica` prova
# ═══════════════════════════════════════════════════════════════════════════
_VESTE = re.compile(r'url\(\s*["\']?(data:image/png;base64,[^"\')]+)["\']?\s*\)'
                    r'\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)')


def leggi_veste(stile):
    """Dalla regola `cursor` di `#schermo` a (png, hx, hy) — o una parola.

    Torna ("png", bytes, hx, hy) · ("nascosta",) · ("sistema",) se non c'e'
    nessuna veste (il cursore del browser e' quello suo) · ("illeggibile", s)."""
    s = (stile or "").strip()
    if not s or s in ("auto", "default"):
        return ("sistema",)
    if s == "none":
        return ("nascosta",)
    m = _VESTE.search(s)
    if not m:
        return ("illeggibile", s[:80])
    try:
        png = base64.b64decode(m.group(1).split(",", 1)[1])
    except Exception:                            # noqa: BLE001
        return ("illeggibile", s[:80])
    return ("png", png, float(m.group(2)), float(m.group(3)))


def classifica_sagoma(larghezza, altezza, alfa, hx, hy):
    """⭐ La classe di un cursore dai suoi PIXEL: `alfa` e' la lista riga per
    riga dei valori di alfa.  Torna (classe, descrizione)."""
    xs = [i % larghezza for i, a in enumerate(alfa) if a >= ALFA]
    ys = [i // larghezza for i, a in enumerate(alfa) if a >= ALFA]
    if not xs:
        return "nascosta", "%dx%d senza pixel opachi" % (larghezza, altezza)
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    rx, ry = (hx - x0 + 0.5) / w, (hy - y0 + 0.5) / h
    pieni = set(zip(xs, ys))
    # la simmetria sopra-sotto della sagoma dentro il suo rettangolo
    simm = sum(1 for (x, y) in pieni if (x, y0 + y1 - y) in pieni) / len(pieni)
    # quanto del rettangolo e' pieno: una freccia e' sottile, una clessidra no
    pieno = len(pieni) / float(w * h)
    # l'asta: la corsa opaca piu' lunga sulla riga del punto attivo (± 1)
    asta = 0
    for y in (int(hy) - 1, int(hy), int(hy) + 1):
        corsa = 0
        for x in range(x0, x1 + 1):
            corsa = corsa + 1 if (x, y) in pieni else 0
            asta = max(asta, corsa)
    desc = ("%dx%d, sagoma %dx%d a (%d,%d), punto attivo (%g,%g) = %.2f,%.2f della "
            "sagoma, simmetria sopra/sotto %.2f, pieno %.2f, asta %d/%d"
            % (larghezza, altezza, w, h, x0, y0, hx, hy, rx, ry, simm, pieno, asta, w))
    if rx <= 0.2 and ry <= 0.2:
        return "freccia", desc
    if 0.25 <= rx <= 0.75 and 0.25 <= ry <= 0.75 and h >= 1.5 * w:
        return "testo", desc
    if 0.3 <= ry <= 0.7 and w >= 0.8 * h and simm >= 0.8 and pieno <= 0.68 \
            and asta >= 0.6 * w:
        return "orizzontale", desc
    return "altra", desc


def classifica(veste):
    """(classe, descrizione) di una veste letta da `leggi_veste`."""
    if veste[0] == "nascosta":
        return "nascosta", "cursor: none"
    if veste[0] == "sistema":
        return "sistema", "nessuna forma remota indossata (il cursore del browser)"
    if veste[0] != "png":
        return "illeggibile", veste[1]
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(veste[1])).convert("RGBA")
    except Exception as e:                       # noqa: BLE001
        return "illeggibile", "PNG illeggibile: %s" % e
    l, a = im.size
    alfa = [p[3] for p in im.getdata()]
    return classifica_sagoma(l, a, alfa, veste[2], veste[3])


def giudica_passo(nome, atteso, prima, cambi, t_mossa):
    """⭐ Il giudizio di un passo.

    `prima`  la classe in vigore all'istante del movimento
    `cambi`  [(t_ms, classe, descrizione)] i cambi dopo il movimento
    Torna (esito, motivo, ms del cambio giusto | None)."""
    dopo = [c for c in cambi if c[0] >= t_mossa]
    if not dopo:
        if prima == atteso:
            # ⛔ Non e' un verde: la forma era gia' quella, il passo non prova
            #   niente — e la partenza sul testo esiste per non finire qui.
            return CIECO, ("%s: la forma era gia' «%s» prima del movimento e non e' "
                           "cambiata: il passo non prova niente" % (nome, atteso)), None
        return ROSSO, ("%s: in %.0f ms la forma NON E' CAMBIATA (resta «%s», attesa «%s»)"
                       % (nome, GUARDA_S * 1000, prima, atteso)), None
    entro = [c for c in dopo if c[0] - t_mossa <= TETTO_MS]
    if not entro:
        c = dopo[0]
        return ROSSO, ("%s: la forma e' cambiata a %.0f ms, OLTRE i %.0f (arrivata «%s», "
                       "attesa «%s»)" % (nome, c[0] - t_mossa, TETTO_MS, c[1], atteso)), None
    vigore = entro[-1]
    if vigore[1] != atteso:
        return ROSSO, ("%s: a %.0f ms la forma e' «%s», attesa «%s» (%s)"
                       % (nome, TETTO_MS, vigore[1], atteso, vigore[2])), None
    giusto = next(c for c in entro if c[1] == atteso)
    ms = giusto[0] - t_mossa
    return VERDE, ("%s: «%s» a %.0f ms (%s)" % (nome, atteso, ms, giusto[2])), ms


def giudica_scansione(nome, atteso, prima, cambi, mosse):
    """⭐ Il giudizio del BORDO: una scansione, non un punto.

    `mosse`  [(scarto_px, t_ms)] l'istante di ogni movimento della scansione
    Torna (esito, motivo, (scarto, ms) | None)."""
    if not mosse:
        return CIECO, "%s: la scansione non ha movimenti" % nome, None
    mosse = sorted(mosse, key=lambda m: m[1])
    dopo = [c for c in cambi if c[0] >= mosse[0][1]]
    tardi = None
    for c in dopo:
        if c[1] != atteso:
            continue
        # ⭐ il movimento che l'ha portata: l'ultimo prima del cambio
        chi = [m for m in mosse if m[1] <= c[0]][-1]
        ms = c[0] - chi[1]
        if ms <= TETTO_MS:
            return VERDE, ("%s: «%s» a %+d px dal bordo, %.0f ms dopo il movimento (%s)"
                           % (nome, atteso, chi[0], ms, c[2])), (chi[0], ms)
        tardi = tardi or (chi[0], ms)
    if tardi:
        return ROSSO, ("%s: «%s» e' arrivata a %+d px ma %.0f ms dopo il movimento, OLTRE "
                       "i %.0f" % (nome, atteso, tardi[0], tardi[1], TETTO_MS)), None
    if not dopo and prima == atteso:
        return CIECO, ("%s: la forma era gia' «%s» prima della scansione e non e' "
                       "cambiata: il passo non prova niente" % (nome, atteso)), None
    viste = []
    for c in dopo:
        if c[1] not in viste:
            viste.append(c[1])
    return ROSSO, ("%s: da %+d a %+d px dal bordo la forma non e' MAI «%s» (%s)"
                   % (nome, mosse[0][0], mosse[-1][0], atteso,
                      ("viste: " + ", ".join(viste)) if viste
                      else "resta «%s», nessun cambio" % prima)), None


def giudica_tutto(osservati, tabella):
    """[(passo, esito, motivo, ms)] e l'esito complessivo, per una tabella."""
    righe = []
    for p in PASSI:
        o = osservati.get(p)
        if o is None:
            righe.append((p, CIECO, "%s: non osservato" % p, None))
            continue
        if o.get("scansione"):
            e, m, ms = giudica_scansione(p, tabella[p], o["prima"], o["cambi"],
                                         o["scansione"])
        else:
            e, m, ms = giudica_passo(p, tabella[p], o["prima"], o["cambi"], o["t_mossa"])
        righe.append((p, e, m, ms))
    v = [r[1] for r in righe]
    return (ROSSO if ROSSO in v else (CIECO if CIECO in v else VERDE)), righe


def _vicino(p, c, toll=TOLLERANZA):
    return abs(p[0] - c[0]) <= toll and abs(p[1] - c[1]) <= toll and abs(p[2] - c[2]) <= toll


def trova_finestra(larghezza, altezza, pixel, passo=1):
    """⭐ La finestra di prova nella fotografia: dict o (None, motivo).

    `pixel` e' la lista RGB riga per riga.  Si cerca il CIANO della pagina:
      · il suo rettangolo, dalle colonne e righe dove il ciano e' tanto (il
        30 % del massimo: una scritta nera o un'icona non lo spostano)
      · ⭐ il bordo destro FINE: su cinque righe attorno al centro si cammina
        dal centro verso destra finche' il pixel e' ciano, e si prende la
        mediana — l'ultimo pixel ciano, in pixel della fotografia
      · il riquadro GIALLO del testo, dentro.
    ⚠ `passo`: i conti del rettangolo si fanno su un pixel ogni `passo` (in 4K
      sono 8 milioni di pixel, e senza numpy il giro intero costa ~10 s per
      fotografia); il bordo fine si cerca comunque pixel per pixel."""
    col = [0] * larghezza
    rig = [0] * altezza
    gcol, grig = [0] * larghezza, [0] * altezza
    for y in range(0, altezza, passo):
        base = y * larghezza
        for x in range(0, larghezza, passo):
            p = pixel[base + x]
            if _vicino(p, CIANO):
                col[x] += 1
                rig[y] += 1
            elif _vicino(p, GIALLO):
                gcol[x] += 1
                grig[y] += 1
    if max(col) == 0:
        return None, "nessun pixel ciano: la finestra di prova non si vede"
    xs = [x for x, n in enumerate(col) if n >= 0.3 * max(col)]
    ys = [y for y, n in enumerate(rig) if n >= 0.3 * max(rig)]
    x0, x1, y0, y1 = min(xs), max(xs) + passo - 1, min(ys), max(ys) + passo - 1
    if (x1 - x0 + 1) * (y1 - y0 + 1) < AREA_MINIMA * larghezza * altezza:
        return None, ("il ciano c'e' ma e' piccolo (%dx%d): non e' la finestra"
                      % (x1 - x0 + 1, y1 - y0 + 1))
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    # ⚠ con `passo` il centro va rimesso su una riga campionata del ciano
    cx, cy = cx - cx % passo, cy - cy % passo
    if not _vicino(pixel[cy * larghezza + cx], CIANO):
        return None, "il centro del ciano (%d,%d) non e' ciano: la finestra e' coperta" % (cx, cy)
    bordi = []
    for dy in (-20, -10, 0, 10, 20):
        y = min(max(cy + dy, 0), altezza - 1)
        x = cx
        while x + 1 < larghezza and _vicino(pixel[y * larghezza + x + 1], CIANO):
            x += 1
        bordi.append(x)
    bordi.sort()
    destro = bordi[2]
    if max(gcol) == 0:
        return None, "nessun pixel giallo: il riquadro del testo non si vede"
    gx = [x for x, n in enumerate(gcol) if n >= 0.3 * max(gcol)]
    gy = [y for y, n in enumerate(grig) if n >= 0.3 * max(grig)]
    return {"ciano": [x0, y0, x1, y1], "centro": [cx, cy], "destro": destro,
            "bordi": bordi,
            "testo": [(min(gx) + max(gx)) // 2, (min(gy) + max(gy)) // 2],
            "giallo": [min(gx), min(gy), max(gx), max(gy)]}, ""


# ═══════════════════════════════════════════════════════════════════════════
#  LA CERTIFICAZIONE DELLE FUNZIONI PURE
# ═══════════════════════════════════════════════════════════════════════════
def _png(im):
    b = io.BytesIO()
    im.save(b, "PNG")
    return b.getvalue()


def cursori_finti():
    """I cursori disegnati qui, con la forma di quelli veri."""
    from PIL import Image, ImageDraw
    fr = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(fr)
    d.polygon([(3, 3), (3, 20), (7, 16), (10, 22), (12, 21), (9, 15), (15, 15)],
              fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
    # la doppia di Breeze: asta e due punte, punto attivo al centro
    dp = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(dp)
    d.rectangle([9, 14, 22, 17], fill=(0, 0, 0, 255))
    d.polygon([(3, 15), (10, 8), (10, 23)], fill=(0, 0, 0, 255))
    d.polygon([(28, 15), (21, 8), (21, 23)], fill=(0, 0, 0, 255))
    # ⭐ l'e-resize di Adwaita, `[M]` 24 set 2026: freccia verso destra contro
    #   una barra, punto attivo sulla barra
    ae = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(ae)
    d.rectangle([17, 4, 20, 20], fill=(0, 0, 0, 255))
    d.rectangle([3, 11, 16, 13], fill=(0, 0, 0, 255))
    d.polygon([(11, 5), (16, 12), (11, 19)], fill=(0, 0, 0, 255))
    te = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(te)
    d.rectangle([15, 5, 16, 26], fill=(0, 0, 0, 255))
    d.rectangle([11, 5, 20, 6], fill=(0, 0, 0, 255))
    d.rectangle([11, 25, 20, 26], fill=(0, 0, 0, 255))
    # una clessidra piena col punto attivo al centro: NON e' un ridimensionamento
    cl = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    ImageDraw.Draw(cl).ellipse([2, 2, 21, 21], fill=(0, 0, 0, 255))
    # una mano: punto attivo in alto, al dito
    ma = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(ma)
    d.rectangle([8, 2, 11, 12], fill=(0, 0, 0, 255))
    d.rectangle([5, 10, 19, 21], fill=(0, 0, 0, 255))
    return {"freccia": (("png", _png(fr), 3, 3), "freccia"),
            "doppia di Breeze": (("png", _png(dp), 15, 15), "orizzontale"),
            "e-resize di Adwaita": (("png", _png(ae), 19, 12), "orizzontale"),
            "barra del testo": (("png", _png(te), 15, 15), "testo"),
            "clessidra piena": (("png", _png(cl), 11, 11), "altra"),
            "mano": (("png", _png(ma), 9, 2), "altra")}


def certifica():
    print("⭐ 11-c21 · CERTIFICAZIONE DELLE FUNZIONI PURE")
    guai, fatte = [], []

    def prova(cosa, vero, dettaglio=""):
        fatte.append(cosa)
        print("   %s %s%s" % ("⭐ ok  " if vero else "⛔ NO  ", cosa,
                              (" — " + dettaglio) if dettaglio else ""))
        if not vero:
            guai.append(cosa)

    try:
        c = cursori_finti()
    except ImportError:
        print("⛔ PIL non c'e': non posso certificare ⇒ 3")
        return 3
    # 1. la regola CSS si legge, nelle due grafie dei browser
    dv = c["doppia di Breeze"][0]
    b64 = base64.b64encode(dv[1]).decode()
    for s in ('url("data:image/png;base64,%s") 15 15, default' % b64,
              "url(data:image/png;base64,%s) 15 15, default" % b64):
        v = leggi_veste(s)
        prova("leggi_veste: %s…" % s[:14], v[0] == "png" and v[2:] == (15.0, 15.0))
    prova("leggi_veste: «none» ⇒ nascosta", leggi_veste("none") == ("nascosta",))
    prova("leggi_veste: vuota ⇒ sistema", leggi_veste("") == ("sistema",))
    # 2. il classificatore dai PIXEL
    for nome, (veste, attesa) in c.items():
        k, d = classifica(veste)
        prova("classifica %s ⇒ %s" % (nome, k), k == attesa, d)
    # ⛔ e la stessa immagine della doppia col punto attivo in alto a sinistra
    #   NON e' un ridimensionamento: il punto attivo fa parte della forma
    k, d = classifica(dv[:2] + (3, 8))
    prova("doppia col punto attivo in alto a sinistra ⇒ non orizzontale (%s)" % k,
          k != "orizzontale", d)
    # 3. il giudizio del passo
    fr, dp = classifica(c["freccia"][0]), classifica(dv)
    te = classifica(c["barra del testo"][0])
    casi = [
        ("giusta a 120 ms ⇒ VERDE", ("freccia", [(1120, dp[0], dp[1])], 1000), VERDE),
        ("giusta a 350 ms ⇒ ROSSO", ("freccia", [(1350, dp[0], dp[1])], 1000), ROSSO),
        ("nessun cambio ⇒ ROSSO", ("freccia", [], 1000), ROSSO),
        ("sbagliata a 100 ms ⇒ ROSSO", ("freccia", [(1100, fr[0], fr[1])], 1000), ROSSO),
        ("gia' giusta e ferma ⇒ 3", ("orizzontale", [], 1000), CIECO),
        ("cambio di PRIMA del movimento ⇒ ROSSO", ("freccia", [(900, dp[0], dp[1])], 1000),
         ROSSO),
        ("giusta a 100 poi sbagliata a 250 ⇒ ROSSO",
         ("freccia", [(1100, dp[0], dp[1]), (1250, fr[0], fr[1])], 1000), ROSSO),
    ]
    for nome, (prima, cambi, t), atteso in casi:
        e, m, _ms = giudica_passo("bordo", "orizzontale", prima, cambi, t)
        prova("giudica_passo: %s" % nome, e == atteso, m)
    # 3-bis. la scansione del bordo (tre desktop, tre posti)
    mosse = [(k, 10000 + 400 * i) for i, k in enumerate(SCANSIONE)]
    t_di = dict(mosse)
    scasi = [
        ("KWin: sul bordo (-1 px) ⇒ VERDE a -1",
         ("freccia", [(t_di[-1] + 40, dp[0], dp[1]), (t_di[2] + 40, fr[0], fr[1])]),
         VERDE, -1),
        ("GNOME: nell'ombra (+4 px) ⇒ VERDE a +4",
         ("freccia", [(t_di[4] + 30, dp[0], dp[1])]), VERDE, 4),
        ("mai orizzontale ⇒ ROSSO", ("freccia", [(t_di[3] + 30, te[0], te[1])]), ROSSO, None),
        ("nessun cambio ⇒ ROSSO", ("freccia", []), ROSSO, None),
        ("orizzontale a 350 ms dal suo movimento ⇒ ROSSO",
         ("freccia", [(t_di[5] + 350, dp[0], dp[1])]), ROSSO, None),
    ]
    for nome, (prima, cambi), atteso, dove in scasi:
        e, m, x = giudica_scansione("bordo", "orizzontale", prima, cambi, mosse)
        prova("giudica_scansione: %s" % nome,
              e == atteso and (dove is None or (x and x[0] == dove)), m)
    e, m, _x = giudica_scansione("bordo", "testo", "freccia",
                                 [(t_di[4] + 30, dp[0], dp[1])], mosse)
    prova("giudica_scansione con la tabella spostata ⇒ ROSSO", e == ROSSO, m)

    # 4. ⭐ il guasto innestato: le STESSE osservazioni, due tabelle
    oss = {"centro": {"prima": "testo", "cambi": [(1080, fr[0], fr[1])], "t_mossa": 1000},
           "bordo": {"prima": "freccia", "cambi": [(2090, dp[0], dp[1])], "t_mossa": 2000,
                     "scansione": [(-1, 2000), (0, 2400)]},
           "testo": {"prima": "orizzontale", "cambi": [(3070, te[0], te[1])],
                     "t_mossa": 3000}}
    es, _ = giudica_tutto(oss, ATTESO)
    eg, righe = giudica_tutto(oss, ATTESO_SBAGLIATO)
    prova("tabella giusta ⇒ VERDE, tabella spostata ⇒ ROSSO", es == VERDE and eg == ROSSO,
          "sano %s · guasto %s (%s)" % (es, eg, righe[0][2]))
    # 5. la finestra nella fotografia
    L, A = 400, 250
    px = [((x * 7 + y * 3) % 90 + 60,) * 3 for y in range(A) for x in range(L)]
    for y in range(40, 200):
        for x in range(50, 300):
            px[y * L + x] = (8, 250, 244)        # ciano «dopo la codifica»
    for y in range(52, 100):
        for x in range(62, 150):
            px[y * L + x] = (250, 248, 10)
    for x in range(70, 140, 6):                  # scritte nere nel giallo
        px[70 * L + x] = (0, 0, 0)
    f, perche = trova_finestra(L, A, px)
    prova("trova_finestra: bordo destro = 299", bool(f) and f["destro"] == 299,
          perche or json.dumps(f))
    f3, perche3 = trova_finestra(L, A, px, passo=3)
    prova("trova_finestra col passo 3: bordo destro = 299 lo stesso",
          bool(f3) and f3["destro"] == 299, perche3 or json.dumps(f3))
    prova("trova_finestra: il testo cade nel giallo",
          bool(f) and 62 <= f["testo"][0] < 150 and 52 <= f["testo"][1] < 100)
    f2, perche2 = trova_finestra(L, A, [(90, 90, 90)] * (L * A))
    prova("trova_finestra: senza ciano ⇒ nessuna finestra", f2 is None, perche2)
    print()
    if guai:
        print("⛔ CERTIFICAZIONE FALLITA: %d prove su %d" % (len(guai), len(fatte)))
        return 1
    print("⭐ CERTIFICATO: il classificatore distingue le tre forme dai pixel, il "
          "giudice\n   da' rosso al tardi, al fermo e allo sbagliato, e la tabella "
          "spostata e' ROSSO.")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
#  DENTRO LA PAGINA
# ═══════════════════════════════════════════════════════════════════════════
# ⭐ L'osservatore: l'istante di ogni movimento e di ogni cambio della veste,
#   col `performance.now()` della pagina — cioe' la latenza misurata dove la
#   vede l'utente, non dal banco che aspetta le risposte di Marionette.
JS_OSSERVA = r"""
(function () {
  if (window.__C21__) return;
  const s = document.getElementById('schermo');
  if (!s) return;
  const C = window.__C21__ = { mosse: [], vesti: [] };
  addEventListener('pointermove', function (e) {
    C.mosse.push([performance.now(), e.clientX, e.clientY]);
    if (C.mosse.length > 200) C.mosse.shift();
  }, true);
  const leggi = function () {
    const v = s.style.cursor || '';
    const u = C.vesti.length ? C.vesti[C.vesti.length - 1][1] : null;
    if (v === u) return;
    C.vesti.push([performance.now(), v]);
    if (C.vesti.length > 60) C.vesti.shift();
  };
  leggi();
  new MutationObserver(leggi).observe(s, { attributes: true, attributeFilter: ['style'] });
})();
"""

JS_ORA = "return performance.now();"

JS_DOPO = r"""
const C = window.__C21__;
if (!C) return null;
const t = arguments[0];
let prima = '';
for (const v of C.vesti) if (v[0] <= t) prima = v[1];
const st = window.REMOTIX && REMOTIX.input_classico ? REMOTIX.input_classico.stato() : null;
return { mosse: C.mosse.filter(m => m[0] > t),
         vesti: C.vesti.filter(v => v[0] > t),
         prima: prima,
         spedito: st ? st.ultimo_spedito : null,
         utilizzabile: st ? st.utilizzabile : null };
"""

JS_GEOMETRIA = r"""
const P = window.REMOTIX_PUNTATORE, t = document.getElementById('schermo');
if (!P || !P.geometria || !t) return null;
const g = P.geometria();
return { left: g.r.left, top: g.r.top, width: g.r.width, height: g.r.height,
         bx0: g.bx0, by0: g.by0, sx: g.sx, sy: g.sy, vx: g.vx, vy: g.vy,
         tl: g.tl, ta: g.ta, bw: t.width, bh: t.height,
         modo: document.body.dataset.puntatore || null,
         disposizione: document.body.dataset.disposizione || null };
"""


def foto_piena(g):
    """La fotografia della tela a PIENA risoluzione.  ⚠ La guida di Chrome di
    `12-client-veri` la riduce a 640 px di larghezza (per il giudice degenere):
    qui servono i singoli pixel del bordo, e si chiede la scala 1."""
    if hasattr(g, "cdp"):
        r = g.js("const t=document.getElementById('schermo');"
                 "if(!t) return null; const b=t.getBoundingClientRect();"
                 "return [b.left, b.top, b.width, b.height];")
        if not r:
            return None
        s = g.cdp.chiama("Page.captureScreenshot", format="png",
                         clip={"x": r[0], "y": r[1], "width": r[2], "height": r[3],
                               "scale": 1})
        return base64.b64decode(s["data"])
    png, _p = g.fotografa_tela()
    return png


def dalla_foto_al_desktop(geo, pw, ph, px, py):
    """Pixel della fotografia ⇒ pixel del desktop (virgola mobile)."""
    return ((px * geo["bw"] / pw - geo["bx0"]) / geo["sx"],
            (py * geo["bh"] / ph - geo["by0"]) / geo["sy"])


def dal_desktop_al_vetro(geo, X, Y):
    """Pixel del desktop ⇒ coordinate del browser (le stesse di `cl_disegna`)."""
    return (geo["left"] + (geo["bx0"] + X * geo["sx"]) * geo["vx"],
            geo["top"] + (geo["by0"] + Y * geo["sy"]) * geo["vy"])


def cerca_la_finestra(g, attesa, salva, nome):
    """Aspetta che la finestra di prova compaia FERMA (due fotografie uguali)."""
    from PIL import Image
    fine = time.time() + attesa
    ultima, perche, png = None, "nessuna fotografia", None
    while time.time() < fine:
        time.sleep(1.5)
        try:
            png = foto_piena(g)
        except Exception as e:                   # noqa: BLE001
            perche = "fotografia fallita: %s" % str(e)[:120]
            continue
        if not png:
            perche = "la tela non si fotografa"
            continue
        im = Image.open(io.BytesIO(png)).convert("RGB")
        f, perche = trova_finestra(im.size[0], im.size[1], list(im.getdata()),
                                   passo=max(1, im.size[0] // 960))
        if not f:
            ultima = None
            continue
        f["foto"] = list(im.size)
        if ultima and all(abs(a - b) <= 2 for a, b in zip(ultima["ciano"], f["ciano"])) \
                and abs(ultima["destro"] - f["destro"]) <= 1:
            if salva:
                with open(os.path.join(salva, "%s-finestra.png" % nome), "wb") as fh:
                    fh.write(png)
            return f, ""
        ultima = f
    if salva and png:
        with open(os.path.join(salva, "%s-finestra-NON-trovata.png" % nome), "wb") as fh:
            fh.write(png)
    return None, perche


# ⭐ L'ESC nella tabella dei tasti di `12-client-veri` (che ha solo Control e
#   la freccia): si AGGIUNGE una voce, non si copia la guida.
VERI.TASTI.setdefault("Escape", {"key": "Escape", "code": "Escape", "vk": 27,
                                 "wd": "\ue00c"})


def sveglia(g, geo):
    """Un ESC vero, col puntatore sulla tela e il fuoco fuori dal modulo."""
    try:
        g.js("if (document.activeElement && document.activeElement.blur) "
             "document.activeElement.blur(); return 1;")
        x, y = dal_desktop_al_vetro(geo, geo["tl"] * 0.5, geo["ta"] * 0.5)
        g.muovi(x, y)
        time.sleep(0.3)
        g.tasto("Escape")
        time.sleep(1.5)
        return "ESC mandato"
    except Exception as e:                       # noqa: BLE001
        return "⚠ ESC non mandato: %s" % str(e)[:120]


def scansiona(g, geo, Xbordo, Y):
    """⭐ Il bordo, un pixel per passo.  Torna (X finale, [(scarto, t0)], t0, dati)."""
    t_inizio = g.js(JS_ORA)
    passi = []
    for k in SCANSIONE:
        vx, vy = dal_desktop_al_vetro(geo, Xbordo + k, Y)
        passi.append((k, g.js(JS_ORA)))
        g.muovi(vx, vy)
        time.sleep(PASSO_SCANSIONE_S)
    time.sleep(max(0.0, GUARDA_S - PASSO_SCANSIONE_S))
    return Xbordo + SCANSIONE[-1], passi, t_inizio, g.js(JS_DOPO, t_inizio)


def un_passo(g, x, y):
    """Muove il puntatore e raccoglie quel che la pagina ha visto."""
    t0 = g.js(JS_ORA)
    g.muovi(x, y)
    time.sleep(GUARDA_S)
    return t0, g.js(JS_DOPO, t0)


# ═══════════════════════════════════════════════════════════════════════════
#  DENTRO LA SCATOLA
# ═══════════════════════════════════════════════════════════════════════════
def prepara_la_casa(sc, chi, largo, alto):
    """La pagina nota e il profilo di Firefox, nella casa dell'inquilino."""
    b = lambda s: base64.b64encode(s.encode()).decode()     # noqa: E731
    c, t = sc.dentro(
        "set -e; h=/home/%s; mkdir -p $h/%s; "
        "echo %s | base64 -d > $h/%s; echo %s | base64 -d > $h/%s/user.js; "
        "echo %s | base64 -d > $h/%s/xulstore.json; chown -R %s: $h/%s $h/%s; echo pronta"
        % (chi, PROFILO, b(PAGINA), FILE_PAGINA, b(PREFERENZE), PROFILO,
           b(xulstore(largo, alto)), PROFILO, chi, PROFILO, FILE_PAGINA), 60)
    return c == 0, t


def accendi_la_finestra(sc, chi):
    """⭐ `firefox-esr` NORMALE nella sessione dell'inquilino: ha i bordi."""
    c, t = sc.dentro(
        "u=$(id -u %(c)s); d=$(ls /run/user/$u 2>/dev/null | grep -E '^wayland-[0-9]+$' "
        "| head -1); [ -n \"$d\" ] || { echo 'nessun socket wayland'; exit 2; }; "
        "setsid runuser -u %(c)s -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
        "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
        "XDG_SESSION_TYPE=wayland HOME=/home/%(c)s firefox-esr --no-remote --new-instance "
        "--profile /home/%(c)s/%(p)s file:///home/%(c)s/%(f)s "
        "< /dev/null > /home/%(c)s/.c21-firefox.log 2>&1 & "
        "for i in $(seq 1 40); do pgrep -u %(c)s -f firefox-esr >/dev/null && "
        "{ echo accesa; exit 0; }; sleep 0.25; done; echo 'non si e vista'; exit 1"
        % {"c": chi, "p": PROFILO, "f": FILE_PAGINA}, 60)
    return c == 0, t


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA DI UN BROWSER
# ═══════════════════════════════════════════════════════════════════════════
def osserva(nome, o, sc, chi):
    """Torna (riga, osservati) — `osservati` e' None se non si e' guardato."""
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
            return dict(riga, esito=CIECO, perche="la pagina non si apre: " + m), None
        e, m, s = pr.entra(o.parola)
        if e != VERDE:
            return dict(riga, esito=CIECO, perche="l'accesso: " + m), None
        e, m, s = pr.primo_fotogramma()
        e, m = C20V.desktop_scuro_ma_vivo(e, m, s)
        print("   ⭐ primo fotogramma: %s" % m, flush=True)
        if e != VERDE:
            return dict(riga, esito=CIECO, perche="senza immagine non si guarda: " + m), None
        geo = g.js(JS_GEOMETRIA)
        if not geo:
            return dict(riga, esito=CIECO, perche="`REMOTIX_PUNTATORE.geometria` non c'e'"), None
        riga["geometria"] = {k: geo[k] for k in ("tl", "ta", "bw", "bh", "sx", "vx",
                                                 "modo", "disposizione")}
        print("   tela %sx%s · buffer %sx%s · modo «%s» · disposizione «%s»"
              % (geo["tl"], geo["ta"], geo["bw"], geo["bh"], geo["modo"],
                 geo["disposizione"]), flush=True)
        if geo["modo"] != "sistema" or geo["disposizione"] != "classico":
            # ⛔ Fuori dal modo `sistema` la veste non va sulla tela: guardare
            #   la regola `cursor` direbbe «non cambia» a un prodotto sano.
            return dict(riga, esito=CIECO, perche="la pagina non e' nel modo «sistema» "
                        "classico (modo %s, disposizione %s): la veste non si legge"
                        % (geo["modo"], geo["disposizione"])), None

        # ── la sveglia: un ESC PRIMA di aprire la finestra ─────────────────
        # ⚠ `[M]` 24 set 2026, gnome: la sessione nasce nella VISTA D'INSIEME,
        #   e li' la finestra e' un'anteprima rimpicciolita su cui il desktop
        #   non cambia forma (il primo giro di questa maglia: ROSSO falso, tre
        #   passi senza un cambio).  ⭐ E' la sveglia di C4 (`11-c4…`, «LA
        #   SVEGLIA»), mandata come la manda l'utente: un tasto VERO del
        #   browser, col fuoco fuori dai campi del modulo (`cl_nel_modulo`).
        #   ⛔ Niente clic per dare il fuoco: il primo clic sulla tela chiede il
        #     `Pointer Lock`, e da li' i movimenti sarebbero relativi.
        e_sv = sveglia(g, geo)
        print("   sveglia: %s" % e_sv, flush=True)

        # ── la finestra di prova ───────────────────────────────────────────
        largo_f, alto_f = geo["tl"] * 0.45, geo["ta"] * 0.55
        ok, t = prepara_la_casa(sc, chi, largo_f, alto_f)
        if not ok:
            return dict(riga, esito=CIECO, perche="la casa non si prepara: %s" % t[-200:]), None
        ok, t = accendi_la_finestra(sc, chi)
        if not ok:
            return dict(riga, esito=CIECO, perche="firefox-esr non parte: %s" % t[-200:]), None
        f, perche = cerca_la_finestra(g, o.attesa_finestra, o.salva, nome)
        if not f:
            return dict(riga, esito=CIECO, perche="la finestra di prova non si vede in "
                        "%d s: %s" % (o.attesa_finestra, perche)), None
        pw, ph = f["foto"]
        # ⛔ Un'anteprima non e' una finestra: se il ciano e' molto piu' stretto
        #   della misura chiesta nel profilo, la vista d'insieme e' ancora li'.
        lx0, _ = dalla_foto_al_desktop(geo, pw, ph, f["ciano"][0], 0)
        lx1, _ = dalla_foto_al_desktop(geo, pw, ph, f["destro"] + 1, 0)
        if lx1 - lx0 < 0.7 * largo_f:
            return dict(riga, esito=CIECO, perche="la finestra e' larga %d px e ne ho chiesti "
                        "%d: e' un'anteprima (la vista d'insieme?), non la finestra"
                        % (lx1 - lx0, largo_f)), None
        Xd, Yc = dalla_foto_al_desktop(geo, pw, ph, f["destro"] + 0.5, f["centro"][1] + 0.5)
        Xd = int(Xd)                               # l'ultimo pixel ciano, nel desktop
        Xc, Yc = dalla_foto_al_desktop(geo, pw, ph, f["centro"][0] + 0.5, f["centro"][1] + 0.5)
        Xt, Yt = dalla_foto_al_desktop(geo, pw, ph, f["testo"][0] + 0.5, f["testo"][1] + 0.5)
        if Xd + SCANSIONE[-1] + 2 >= geo["tl"]:
            return dict(riga, esito=CIECO, perche="il bordo destro della finestra (x=%d) e' "
                        "sul bordo dello schermo: fuori non c'e' posto" % Xd), None
        mira = {"partenza": (Xt, Yt), "centro": (Xc, Yc),
                "bordo": (Xd + 0.5, Yc), "testo": (Xt, Yt)}
        riga["finestra"] = {"ciano_foto": f["ciano"], "bordo_destro_desktop": Xd,
                            "bordi_foto": f["bordi"], "foto": f["foto"],
                            "mira_desktop": {k: [round(a, 1), round(b, 1)]
                                             for k, (a, b) in mira.items()}}
        print("   ⭐ finestra: ciano %s nella foto %dx%d · bordo destro x=%d nel desktop · "
              "scansione da x=%d a x=%d" % (f["ciano"], pw, ph, Xd, Xd + SCANSIONE[0],
                                            Xd + SCANSIONE[-1]), flush=True)

        # ── i passi ────────────────────────────────────────────────────────
        g.js(VERI._inietta(JS_OSSERVA))
        if not g.js("return !!window.__C21__;"):
            return dict(riga, esito=CIECO, perche="l'osservatore non si e' installato"), None
        osservati = {}
        for passo in ("partenza",) + PASSI:
            X, Y = mira[passo]
            scansione = None
            if passo == "bordo":
                X, scansione, t0, d = scansiona(g, geo, X, Y)
            else:
                vx, vy = dal_desktop_al_vetro(geo, X, Y)
                t0, d = un_passo(g, vx, vy)
            if not d:
                return dict(riga, esito=CIECO, perche="%s: l'osservatore non risponde" % passo), \
                    None
            if not d["mosse"]:
                # ⛔ Il movimento non e' arrivato alla PAGINA: e' il banco.
                return dict(riga, esito=CIECO, perche="%s: il browser non ha consegnato il "
                            "movimento alla pagina (nessun pointermove)" % passo), None
            sp = d.get("spedito") or [-1, -1]
            if abs(sp[0] - int(X)) > 2 or abs(sp[1] - int(Y)) > 2:
                return dict(riga, esito=CIECO, perche="%s: la pagina ha spedito (%s,%s) "
                            "invece di (%d,%d): il puntatore non e' dove dico"
                            % (passo, sp[0], sp[1], X, Y)), None
            t_mossa = d["mosse"][0][0]
            pk, pd = classifica(leggi_veste(d["prima"]))
            cambi = []
            for tv, stile in d["vesti"]:
                k, kd = classifica(leggi_veste(stile))
                cambi.append((tv, k, kd))
            osservati[passo] = {"prima": pk, "cambi": cambi, "t_mossa": t_mossa}
            if scansione is not None:
                # ⭐ ogni movimento della scansione col SUO istante nella pagina
                mm = [m[0] for m in d["mosse"]]
                sc_t = []
                for k, tk in scansione:
                    dopo_k = [t for t in mm if t >= tk]
                    if dopo_k:
                        sc_t.append((k, dopo_k[0]))
                if len(sc_t) < len(scansione):
                    return dict(riga, esito=CIECO, perche="bordo: %d movimenti della "
                                "scansione su %d arrivati alla pagina"
                                % (len(sc_t), len(scansione))), None
                osservati[passo]["scansione"] = sc_t
                t_mossa = sc_t[0][1]
                osservati[passo]["t_mossa"] = t_mossa

                def dove(tc):
                    ks = [k for k, tk in sc_t if tk <= tc]
                    return ("%+dpx" % ks[-1]) if ks else "?"
                print("   %-8s → scansione x=%+d..%+d px dal bordo, y=%.1f: prima «%s» · "
                      "cambi %s" % (passo, SCANSIONE[0], SCANSIONE[-1], Y, pk,
                                    " ".join("%s «%s»" % (dove(c[0]), c[1]) for c in cambi)
                                    or "nessuno"), flush=True)
            else:
                print("   %-8s → (%.1f,%.1f): prima «%s» · cambi %s" % (
                    passo, X, Y, pk,
                    " ".join("+%.0fms «%s»" % (c[0] - t_mossa, c[1]) for c in cambi)
                    or "nessuno"), flush=True)
            for c in cambi:
                print("            %s: %s" % (c[1], c[2]), flush=True)
            if o.salva:
                for i, (tv, stile) in enumerate(d["vesti"]):
                    v = leggi_veste(stile)
                    if v[0] == "png":
                        with open(os.path.join(o.salva, "%s-%s-%d.png" % (nome, passo, i)),
                                  "wb") as fh:
                            fh.write(v[1])
        riga["osservati"] = {p: {"prima": v["prima"],
                                 "cambi": [[round(c[0] - v["t_mossa"]), c[1], c[2]]
                                           for c in v["cambi"]]}
                             for p, v in osservati.items()}
        return riga, osservati
    finally:
        try:
            g.chiudi()
        except Exception as ex:                  # noqa: BLE001
            print("   ⚠ chiusura del browser: %s" % ex)


def giudica_browser(riga, osservati, guasto):
    """Il verdetto di un browser.  ⛔ Col guasto si legge al contrario."""
    if osservati is None:
        return riga
    es, rs = giudica_tutto(osservati, ATTESO)
    for p, e, m, _ms in rs:
        print("   %s %s" % ({VERDE: "⭐ 0", ROSSO: "⛔ 1", CIECO: "⚠ 3"}[e], m))
    riga["sano"] = {"esito": es, "passi": [[p, e, m] for p, e, m, _ in rs]}
    if not guasto:
        perche = "; ".join(m for _p, e, m, _ in rs if e == es) if es != VERDE else \
            "la forma cambia su tutti e tre i passi entro %.0f ms" % TETTO_MS
        return dict(riga, esito=es, perche=perche)
    eg, rg = giudica_tutto(osservati, ATTESO_SBAGLIATO)
    riga["guasto"] = {"esito": eg, "passi": [[p, e, m] for p, e, m, _ in rg]}
    print("   ── la tabella spostata di uno (--forma-sbagliata) ──")
    for p, e, m, _ms in rg:
        print("   %s %s" % ({VERDE: "⭐ 0", ROSSO: "⛔ 1", CIECO: "⚠ 3"}[e], m))
    if es != VERDE:
        return dict(riga, esito=CIECO, perche="il controllo sano non e' verde (%s): il "
                    "guasto non si puo' innestare" % NOME_ESITO[es])
    if eg == ROSSO:
        return dict(riga, esito=VERDE, perche="⭐ GUASTO VISTO: con la tabella spostata le "
                    "stesse immagini danno ROSSO (%s)"
                    % "; ".join(m for _p, e, m, _ in rg if e == ROSSO))
    return dict(riga, esito=ROSSO, perche="⛔ GUASTO NON VISTO: la tabella spostata da' %s"
                % NOME_ESITO[eg])


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--scatola", choices=sorted(PORTE))
    a.add_argument("--porta", type=int)
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--browser", default="firefox,chrome")
    a.add_argument("--visibile", action="store_true",
                   help="finestre vere (nel compositore annidato) invece di headless")
    a.add_argument("--salva", default="", help="cartella per le fotografie e i cursori")
    a.add_argument("--forma-sbagliata", action="store_true",
                   help="GUASTO INNESTATO: la tabella delle attese spostata di uno")
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
    o.parola = "c21-" + secrets.token_hex(6)
    o.scena, o.continuita_s, o.registro_cmd = "viva", 8, ""
    o.lascia_acceso = False
    if o.salva:
        os.makedirs(o.salva, exist_ok=True)
    sc = C20V.Scatola(o.scatola)
    chi = "c21u%03d" % random.randint(0, 999)
    assert MODELLO_INQUILINO.match(chi)
    o.utente = chi
    print("⭐ 11-c21 · %s · %s · inquilino %s · browser %s · %s%s"
          % (sc.contenitore, o.url, chi, o.browser,
             "finestre vere" if o.visibile else "HEADLESS",
             " · ⛔ GUASTO INNESTATO --forma-sbagliata" if o.forma_sbagliata else ""))
    righe = []
    for b in [x.strip() for x in o.browser.split(",") if x.strip()]:
        sc.sgombera(chi)
        c, t = sc.crea(chi, o.parola)
        if c != 0:
            print("⛔ non ho potuto creare %s: %s" % (chi, t[-200:]))
            return 3
        try:
            r, oss = osserva(b, o, sc, chi)
            r = giudica_browser(r, oss, o.forma_sbagliata)
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
    if o.forma_sbagliata:
        print({VERDE: "⭐ IL GUASTO INNESTATO E' STATO VISTO (esito 0: al contrario, "
                      "come ogni guasto della rete)",
               ROSSO: "⛔⛔ IL GUASTO INNESTATO NON E' STATO VISTO",
               CIECO: "⚠ col guasto innestato NON ho potuto guardare ⇒ 3"}[esito])
    else:
        print("%s C21(%s): %s" % ({VERDE: "⭐", ROSSO: "⛔⛔", CIECO: "⚠"}[esito],
                                  o.scatola, NOME_ESITO[esito]))
    return esito


if __name__ == "__main__":
    sys.exit(main())
