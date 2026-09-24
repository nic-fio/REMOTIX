#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c23 — ⭐⭐ «MAIUSC E FRECCE SELEZIONANO»
===========================================================================

    python3 11-c23-maiusc-e-frecce-selezionano.py --scatola gnome [--browser firefox,chrome]
    python3 11-c23-maiusc-e-frecce-selezionano.py --scatola lxqt --porta 8524 \\
            --contenitore rete14-lxqt            # una scatola di sviluppo
    python3 11-c23-maiusc-e-frecce-selezionano.py --scatola gnome --senza-maiusc
    python3 11-c23-maiusc-e-frecce-selezionano.py --certifica

    che cosa deve essere vero : Maiusc+frecce SELEZIONANO nel desktop remoto,
                                e il Maiusc non resta incastrato — su GNOME,
                                KDE, XFCE e LXQt (l'utente, 24 set 2026:
                                «rimane un ultimo controllo: che la selezione
                                con Maiusc+frecce sia implementata su tutti i
                                DE»)
    da dove parte             : ⛔ da zero, un inquilino NUOVO (`c23u<n>`)
    che cosa guarda           : ⛔ **LA FOTOGRAFIA** del campo remoto: il valore
                                si legge dai pixel della tela, non da un
                                contatore degli eventi
    come so che sa dare rosso : `--senza-maiusc` (le stesse sequenze senza mai
                                premere Maiusc: niente selezione) ⇒ ROSSO

⛔⛔ PERCHE' ESISTE.
   `[M]` 24 set 2026, su tutti e quattro i desktop: Maiusc+Sinistra partiva
   dalla pagina come `105↓ 105↑` — il Maiusc gia' giu' si recuperava solo se
   c'era anche Ctrl/Alt/Super ⇒ la freccia muoveva il cursore e NON
   selezionava.  E dopo una lettera battuta col Maiusc giu' la pagina credeva
   il Maiusc ancora premuto mentre il server lo aveva gia' rilasciato.  La cura
   e' in `src/pagina.html` (`cl_su_keydown`, commit 694f77f, due meta'); questa
   maglia e' la prova che resta, sui quattro desktop.
   ⚠ Coi BROWSER VERI (l'utente, 23 set 2026: *«i test vanno fatti con i
     browser veri, non con emulatori»*): il difetto era proprio nel modo in cui
     la pagina legge gli eventi DEL BROWSER (`getModifierState`, `ev.code`), e
     il cliente Python quegli eventi non li ha.

⭐ CHE COSA FA, per ogni browser (Firefox con Marionette, Chrome con CDP: i
   guidatori sono quelli di `banchi/12-client-veri.py`, la scatola quella di
   `banchi/12-c20-veri.py`, la sveglia e la geometria quelle di
   `11-c21-sul-bordo-la-forma-cambia.py` — ⛔ importati, non copiati):
     1  crea l'inquilino `c23u<n>`, entra, aspetta il primo fotogramma
     2  la SVEGLIA di C21 (un ESC vero: su GNOME la sessione nasce nella vista
        d'insieme)
     3  nella sessione accende un piccolo servitore (`python3`) e
        `firefox-esr --kiosk` sulla SCENA: un <input> sempre a fuoco
     4  per ogni caso (`CASI`): pulisce il campo (Ctrl+A, Canc indietro),
        batte la BASE, e poi la sequenza da provare — con TASTI VERI dati al
        browser (`WebDriver:PerformActions`, `Input.dispatchKeyEvent`)
     5  fotografa la tela e LEGGE il valore del campo dai pixel

⭐⭐ LA SCENA — il valore si vede, due volte.
   · IN GRANDE, nel campo stesso: e' per chi guarda le fotografie salvate
     (`--salva`), cioe' per l'utente.
   · E COME STRISCIA DI COLORI sotto il campo: una casella per carattere, del
     colore che `ALFABETO` da' a quel carattere (e grigio `VUOTO` dove il
     valore e' finito), fra due caselle bianche di MARCA.  ⇒ La maglia legge
     il valore dalla fotografia senza riconoscere le lettere: prende il colore
     al centro di ogni casella e cerca il piu' vicino nella tavolozza.
     ⛔ La tavolozza e' scritta UNA volta, qui, e infilata nella pagina: il
       colore che la pagina dipinge e quello che il giudice cerca non possono
       divergere (la stessa ragione della scena di C4).
     ⚠ I colori sono i 27 vertici e punti medi del cubo RGB (0, 128, 255 per
       canale): due colori distano almeno 127, e la tolleranza e' 60 — la
       catena passa per H.264 4:2:0, che sottocampiona il croma (§4.3 di fase
       11), ma su caselle di ~270 px il croma al centro arriva intero.
   · Il servitore scrive anche, in un file dell'inquilino, ogni keydown della
     pagina remota e ogni valore del campo: ⛔ NON giudica — e' la diagnosi
     del rosso (quale tasto e' arrivato, con quale Maiusc).

⭐ I CASI — quelli della cura, misurati il 24 set 2026 su rete14-lxqt:
     1  «abcdef», Maiusc+Sinistra×3, Y                ⇒ «abcY»
     2  «uno due», Ctrl+Maiusc+Sinistra, z             ⇒ «uno z»
     3  «abcdef», Maiusc giu', Sinistra, A, Maiusc su, b
                                                      ⇒ «abcdeAb»
        (il caso a rischio: dopo la lettera il Maiusc NON resta incastrato,
         e la «b» esce minuscola)
     4  «abcdef», Maiusc giu', Sinistra, A, Sinistra×2, X, Maiusc su, q
                                                      ⇒ «abcdXq»
        (la seconda meta' della cura: DOPO la lettera, col Maiusc ancora giu',
         le frecce selezionano ancora.  `[M]` senza quella meta' ⇒ «abcdXqeA»)
   ⭐ L'atteso non e' solo scritto a mano: `simula()` applica la sequenza a un
     campo di testo finto, e `--certifica` controlla che dia l'atteso — e che
     la stessa sequenza SENZA Maiusc dia un'altra cosa (il guasto si vede).

⛔ I TRE CONTROLLI POVERI, per ogni caso:
     1  dopo la pulizia la striscia c'e' ed e' VUOTA  — se no, 3: la scena non
        e' in vigore (o il campo non si pulisce) e non testimonia
     2  dopo la base la striscia dice LA BASE          — se no, 3: se la
        scrittura semplice non arriva e' di C4, non di C23; e cosi' un rosso
        qui viene SOLO dalla selezione
     3  dopo la sequenza la striscia dice L'ATTESO     — se no, ROSSO, col
        valore visto e la coda dei keydown remoti
   ⚠ Si fotografa piu' volte fino a `ATTESA_S`: qui non si misura la latenza,
     e un fotogramma in ritardo non e' un difetto di selezione.

⛔ COME SO CHE SA DARE ROSSO — `--senza-maiusc`.
   Le stesse sequenze, tolti il «Maiusc giu'» e il «Maiusc su»: le lettere
   restano della loro forma (la «Y» e' ancora «Y»), ⇒ l'unica differenza e'
   che le frecce muovono invece di selezionare, e ogni caso deve dare ROSSO.
   ⛔ Si legge AL CONTRARIO, come ogni guasto della rete (`11-gancio.sh`,
     `esegui_maglia`): 0 = il guasto e' stato VISTO (tutti i casi rossi),
     1 = NON visto (un caso e' tornato lo stesso), 3 = non ho potuto guardare.

⚠ ESITI: 0 verde · 1 rosso · 3 «non ho potuto guardare», col motivo.

⚠ DOVE GIRA: come C21, sull'ospite coi browser veri (`REMOTIX_SUL_SERVER=1`,
  `labwc` senza schermo), e nella scatola con `podman exec`.  L'inquilino e'
  `c23u<n>` (modello di C19 `^c[0-9]+b?u[0-9]+$`): se il banco morisse a
  meta', il gancio lo sgombera.
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


# ⛔ Importati, non copiati: C21 porta con se' `12-c20-veri` (la scatola) e
#   `12-client-veri` (i browser) — uno solo in memoria, e l'ESC gia' in tabella.
C21 = _carica("c21", os.path.join(QUI, "11-c21-sul-bordo-la-forma-cambia.py"))
C20V = C21.C20V
VERI = C21.VERI
VERDE, ROSSO, CIECO = VERI.VERDE, VERI.ROSSO, VERI.CIECO
PORTE = C20V.PORTE
NOME_ESITO = C21.NOME_ESITO

MODELLO_INQUILINO = re.compile(r"^c23u[0-9]+$")

# ---------------------------------------------------------------------------
# ⛔ I NUMERI — ciascuno col suo perche'.
# ---------------------------------------------------------------------------
# Fra un evento e l'altro: piu' della ripetizione piu' corta di un umano, e
# abbastanza perche' ogni tasto viaggi da solo (`[M]` c95: 90 ms bastano).
PAUSA_MS = 90
# Quanto si aspetta che la fotografia dica il valore: non e' una latenza, e'
# un tetto oltre il quale il valore non arriva piu'.
ATTESA_S = 6.0
FOTO_OGNI_S = 0.7
# La tolleranza sul colore di una casella: meta' della distanza minima fra due
# colori della tavolozza (127) meno un margine.
TOLLERANZA = 60
# ⭐ La striscia, in frazioni della finestra del kiosk (= il desktop): larga e
#   in mezzo, lontana da barre e cassetti anche se il kiosk non li coprisse.
CASELLE = 14
STRISCIA_X0, STRISCIA_X1 = 0.04, 0.96      # dalla marca sinistra alla destra
STRISCIA_Y0, STRISCIA_Y1 = 0.55, 0.75
# Il campione al centro di ogni casella: +/- questa frazione della casella.
CAMPIONE = 0.2

# ⭐ LA TAVOLOZZA.  Riservati: VUOTO (casella senza carattere), ALTRO (un
#   carattere fuori dall'alfabeto, o il valore troppo lungo), MARCA (i due
#   estremi della striscia).  Le lettere prendono gli altri colori in ordine.
VUOTO = (128, 128, 128)
ALTRO = (0, 0, 0)
MARCA = (255, 255, 255)
ALFABETO = "abcdefnoquxyzAXY "


def _cubo():
    livelli = (0, 128, 255)
    return [(r, g, b) for r in livelli for g in livelli for b in livelli]


COLORI = {}
for _c in [c for c in _cubo() if c not in (VUOTO, ALTRO, MARCA)][:len(ALFABETO)]:
    COLORI[ALFABETO[len(COLORI)]] = _c
assert len(COLORI) == len(ALFABETO)

# ---------------------------------------------------------------------------
# ⭐ I TASTI.  Un passo e' («giu»|«su», nome).  Le lettere si scrivono GIA'
#   nella forma che il browser riporta (`ev.key`): «Y», non «y» + Maiusc.
#   ⇒ Il guasto puo' togliere il Maiusc senza cambiare le lettere.
# ---------------------------------------------------------------------------
SPECIALI = {
    #  nome        key          code          vk  WebDriver   bit CDP
    "Shift":     ("Shift",     "ShiftLeft",   16, "", 8),
    "Control":   ("Control",   "ControlLeft", 17, "", 2),
    "ArrowLeft": ("ArrowLeft", "ArrowLeft",   37, "", 0),
    "Backspace": ("Backspace", "Backspace",    8, "", 0),
}


def premi(nome):
    return [("giu", nome), ("su", nome)]


def scrivi(testo):
    p = []
    for c in testo:
        p += premi(c)
    return p


def col(mod, passi):
    """`passi` col modificatore `mod` tenuto giu'."""
    return [("giu", mod)] + passi + [("su", mod)]


PULISCI = col("Control", premi("a")) + premi("Backspace")

# (titolo, base, sequenza, atteso)
CASI = [
    ("1 Maiusc+Sinistra×3, Y", "abcdef",
     col("Shift", premi("ArrowLeft") * 3 + premi("Y")), "abcY"),
    ("2 Ctrl+Maiusc+Sinistra, z", "uno due",
     col("Control", col("Shift", premi("ArrowLeft"))) + premi("z"), "uno z"),
    ("3 RISCHIO Maiusc giu', Sinistra, A, Maiusc su, b", "abcdef",
     col("Shift", premi("ArrowLeft") + premi("A")) + premi("b"), "abcdeAb"),
    ("4 RISCHIO+ Maiusc giu', Sinistra, A, Sinistra×2, X, Maiusc su, q", "abcdef",
     col("Shift", premi("ArrowLeft") + premi("A") + premi("ArrowLeft") * 2 + premi("X"))
     + premi("q"), "abcdXq"),
]


def senza_maiusc(passi):
    """⛔ IL GUASTO: le stesse sequenze senza mai premere Maiusc."""
    return [p for p in passi if p[1] != "Shift"]


# ═══════════════════════════════════════════════════════════════════════════
#  LE FUNZIONI PURE
# ═══════════════════════════════════════════════════════════════════════════
def simula(passi, valore=""):
    """⭐ Un campo di testo finto: applica i passi e torna il valore.

    La semantica e' quella di un <input> di Firefox/GTK: la lettera sostituisce
    la selezione; Sinistra senza Maiusc con una selezione la chiude al suo
    inizio; Ctrl+Sinistra salta all'inizio della parola; Ctrl+A seleziona
    tutto; Canc indietro cancella la selezione o il carattere prima."""
    ancora = fuoco = len(valore)
    giu = set()
    for tipo, nome in passi:
        if tipo == "su":
            giu.discard(nome)
            continue
        if nome in ("Shift", "Control"):
            giu.add(nome)
            continue
        a, b = min(ancora, fuoco), max(ancora, fuoco)
        if nome == "ArrowLeft":
            if "Control" in giu:
                i = fuoco
                while i > 0 and valore[i - 1] == " ":
                    i -= 1
                while i > 0 and valore[i - 1] != " ":
                    i -= 1
                nuovo = i
            elif "Shift" not in giu and a != b:
                nuovo = a
            else:
                nuovo = max(0, fuoco - 1)
            fuoco = nuovo
            if "Shift" not in giu:
                ancora = fuoco
        elif nome == "Backspace":
            if a != b:
                valore = valore[:a] + valore[b:]
                ancora = fuoco = a
            elif a > 0:
                valore = valore[:a - 1] + valore[a:]
                ancora = fuoco = a - 1
        elif "Control" in giu:
            if nome.lower() == "a":
                ancora, fuoco = 0, len(valore)
        else:
            valore = valore[:a] + nome + valore[b:]
            ancora = fuoco = a + len(nome)
    return valore


def centri_caselle():
    """[(fx, fy)] dei centri: marca, CASELLE caselle, marca — in frazioni."""
    passo = (STRISCIA_X1 - STRISCIA_X0) / (CASELLE + 2)
    fy = (STRISCIA_Y0 + STRISCIA_Y1) / 2
    return [(STRISCIA_X0 + (i + 0.5) * passo, fy) for i in range(CASELLE + 2)]


def _dist(a, b):
    return max(abs(x - y) for x, y in zip(a, b))


def nome_colore(c):
    """(nome, distanza) del colore della tavolozza piu' vicino."""
    tutti = [("MARCA", MARCA), ("VUOTO", VUOTO), ("ALTRO", ALTRO)] + \
        [(k, v) for k, v in COLORI.items()]
    k, v = min(tutti, key=lambda kv: _dist(kv[1], c))
    return k, _dist(v, c)


def leggi_striscia(campiona):
    """⭐ Il valore del campo dalla fotografia.

    `campiona(fx, fy, rx, ry)` torna il colore (mediano) del rettangolo
    centrato in (fx, fy) di semiampiezza (rx, ry), in frazioni del desktop.
    Torna (valore o None, perche')."""
    cc = centri_caselle()
    passo = (STRISCIA_X1 - STRISCIA_X0) / (CASELLE + 2)
    rx, ry = passo * CAMPIONE, (STRISCIA_Y1 - STRISCIA_Y0) * CAMPIONE
    nomi = []
    for i, (fx, fy) in enumerate(cc):
        c = campiona(fx, fy, rx, ry)
        k, d = nome_colore(c)
        if d > TOLLERANZA:
            return None, "casella %d illeggibile: %s dista %d dal piu' vicino (%s)" % (
                i, c, d, k)
        nomi.append(k)
    if nomi[0] != "MARCA" or nomi[-1] != "MARCA":
        return None, "la striscia non si vede: agli estremi %s e %s invece delle marche" % (
            nomi[0], nomi[-1])
    corpo = nomi[1:-1]
    if "MARCA" in corpo:
        return None, "una marca in mezzo alla striscia: %s" % corpo
    v = ""
    fine = False
    for k in corpo:
        if k == "VUOTO":
            fine = True
            continue
        if fine:
            return None, "un carattere dopo una casella vuota: %s" % corpo
        v += "�" if k == "ALTRO" else k
    return v, ""


def campionatore(im, geo):
    """`campiona()` su un'immagine PIL della tela, con la geometria di C21:
    frazione del desktop ⇒ pixel del desktop ⇒ pixel della fotografia."""
    pw, ph = im.size

    def al_pixel(fx, fy):
        X, Y = fx * geo["tl"], fy * geo["ta"]
        return ((geo["bx0"] + X * geo["sx"]) * pw / geo["bw"],
                (geo["by0"] + Y * geo["sy"]) * ph / geo["bh"])

    def campiona(fx, fy, rx, ry):
        vals = []
        for i in range(5):
            for j in range(5):
                x, y = al_pixel(fx + rx * (i - 2) / 2, fy + ry * (j - 2) / 2)
                x = min(pw - 1, max(0, int(x)))
                y = min(ph - 1, max(0, int(y)))
                vals.append(im.getpixel((x, y))[:3])
        return tuple(sorted(v[k] for v in vals)[len(vals) // 2] for k in range(3))
    return campiona


def giudica_caso(titolo, base, atteso, vuoto, visto_base, visto):
    """(esito, motivo) di un caso, dai tre valori letti nelle fotografie."""
    if vuoto != "":
        return CIECO, "%s: dopo la pulizia la striscia non e' vuota (%r): la scena non " \
            "testimonia" % (titolo, vuoto)
    if visto_base != base:
        return CIECO, "%s: la base %r non e' arrivata (visto %r): la scrittura semplice " \
            "e' di C4, non si giudica la selezione" % (titolo, base, visto_base)
    if visto == atteso:
        return VERDE, "%s: %r ⇒ %r" % (titolo, base, visto)
    return ROSSO, "%s: %r ⇒ %r invece di %r" % (titolo, base, visto, atteso)


def esito_complessivo(esiti):
    return ROSSO if ROSSO in esiti else (CIECO if CIECO in esiti else VERDE)


def esito_col_guasto(esiti):
    """⛔ Al contrario: 0 se OGNI caso e' rosso (il guasto si vede ovunque)."""
    if CIECO in esiti:
        return CIECO
    return VERDE if all(e == ROSSO for e in esiti) else ROSSO


# ═══════════════════════════════════════════════════════════════════════════
#  LA CERTIFICAZIONE DELLE FUNZIONI PURE
# ═══════════════════════════════════════════════════════════════════════════
def _foto_finta(valore, geo, spost=(0, 0), rumore=25, seme=7):
    """Una tela dipinta come la scena, con uno spostamento (una barra che il
    kiosk non copre) e del rumore (la codifica)."""
    from PIL import Image, ImageDraw
    rnd = random.Random(seme)
    im = Image.new("RGB", (geo["bw"], geo["bh"]), (32, 32, 32))
    d = ImageDraw.Draw(im)
    passo = (STRISCIA_X1 - STRISCIA_X0) / (CASELLE + 2)
    colori = [MARCA] + [COLORI.get(c, ALTRO) for c in valore[:CASELLE]] + \
        [VUOTO] * (CASELLE - len(valore[:CASELLE])) + [MARCA]
    for i, c in enumerate(colori):
        x0 = (STRISCIA_X0 + i * passo) * geo["bw"] + spost[0]
        x1 = (STRISCIA_X0 + (i + 1) * passo) * geo["bw"] + spost[0] - 3
        c = tuple(min(255, max(0, v + rnd.randint(-rumore, rumore))) for v in c)
        d.rectangle([x0, STRISCIA_Y0 * geo["bh"] + spost[1], x1,
                     STRISCIA_Y1 * geo["bh"] + spost[1]], fill=c)
    return im


def certifica():
    print("⭐ 11-c23 · CERTIFICAZIONE DELLE FUNZIONI PURE")
    guai, fatte = [], []

    def prova(cosa, vero, dettaglio=""):
        fatte.append(cosa)
        print("   %s %s%s" % ("⭐ ok  " if vero else "⛔ NO  ", cosa,
                              (" — " + dettaglio) if dettaglio else ""))
        if not vero:
            guai.append(cosa)

    # 1. la tavolozza: colori distinti ben oltre il doppio della tolleranza
    tutti = [MARCA, VUOTO, ALTRO] + list(COLORI.values())
    dmin = min(_dist(a, b) for i, a in enumerate(tutti) for b in tutti[i + 1:])
    prova("tavolozza: %d colori, distanza minima %d > 2×%d" % (len(tutti), dmin, TOLLERANZA),
          dmin > 2 * TOLLERANZA)
    prova("ogni carattere dei casi e' nell'alfabeto",
          all(c in ALFABETO for _t, b, s, a in CASI for c in b + a
              + "".join(n for _x, n in s if len(n) == 1)))
    # 2. il campo finto: l'atteso scritto a mano e' quello che la sequenza da'
    for t, base, seq, atteso in CASI:
        v = simula(scrivi(base) + seq)
        prova("simula %s ⇒ %r" % (t.split()[0], atteso), v == atteso, "da' %r" % v)
        vg = simula(scrivi(base) + senza_maiusc(seq))
        prova("simula %s SENZA Maiusc ⇒ un'altra cosa" % t.split()[0], vg != atteso,
              "da' %r" % vg)
    prova("simula: la pulizia svuota il campo", simula(PULISCI, "abc") == "")
    # ⭐ il caso 4 con la sola prima meta' della cura: dopo la lettera il Maiusc
    #   e' SU per il server ⇒ le due Sinistra muovono.  `[M]` c95: «abcdXqeA».
    vecchia = scrivi("abcdef") + col("Shift", premi("ArrowLeft") + premi("A")) \
        + premi("ArrowLeft") * 2 + premi("X") + premi("q")
    prova("simula il caso 4 com'era prima della meta' 2 ⇒ «abcdXqeA» (il [M] di c95)",
          simula(vecchia) == "abcdXqeA", "da' %r" % simula(vecchia))
    # 3. la striscia si legge dai pixel
    try:
        from PIL import Image                     # noqa: F401
    except ImportError:
        print("⛔ PIL non c'e': non posso certificare la lettura ⇒ 3")
        return 3
    geo = {"tl": 1920, "ta": 1080, "bw": 1920, "bh": 1080, "bx0": 0, "by0": 0,
           "sx": 1.0, "sy": 1.0}
    for v in ("", "abcY", "uno z", "abcdeAb", "abcdXqeA", "abcdefabcdefab"):
        for sp in ((0, 0), (0, 40), (-30, 25)):
            letto, perche = leggi_striscia(campionatore(_foto_finta(v, geo, sp), geo))
            prova("striscia %r spostata %s ⇒ si rilegge" % (v, sp), letto == v,
                  "letto %r %s" % (letto, perche))
    letto, perche = leggi_striscia(campionatore(_foto_finta("abc@", geo), geo))
    prova("un carattere fuori alfabeto ⇒ il segno di sostituzione", letto == "abc�",
          "letto %r %s" % (letto, perche))
    # la tela piu' grande della foto (Chrome la riduce) e con i margini neri
    geo2 = {"tl": 3840, "ta": 2160, "bw": 1920, "bh": 1200, "bx0": 0, "by0": 60,
            "sx": 0.5, "sy": 0.5}
    from PIL import Image
    tela = Image.new("RGB", (1920, 1200), (0, 0, 0))
    tela.paste(_foto_finta("abcY", {"bw": 1920, "bh": 1080}), (0, 60))
    letto, perche = leggi_striscia(campionatore(tela, geo2))
    prova("tela 4K in un buffer con margini ⇒ si rilegge", letto == "abcY",
          "letto %r %s" % (letto, perche))
    letto, perche = leggi_striscia(campionatore(Image.new("RGB", (1920, 1080), (90, 60, 30)),
                                                geo))
    prova("senza striscia ⇒ None (non si giudica)", letto is None, perche)
    # 4. i giudici
    prova("giudica: atteso ⇒ VERDE",
          giudica_caso("t", "abcdef", "abcY", "", "abcdef", "abcY")[0] == VERDE)
    prova("giudica: il Maiusc non seleziona ⇒ ROSSO",
          giudica_caso("t", "abcdef", "abcY", "", "abcdef", "abcYdef")[0] == ROSSO)
    prova("giudica: la base non arriva ⇒ 3",
          giudica_caso("t", "abcdef", "abcY", "", "abc", "abcY")[0] == CIECO)
    prova("giudica: la pulizia non svuota ⇒ 3",
          giudica_caso("t", "abcdef", "abcY", "xx", "abcdef", "abcY")[0] == CIECO)
    prova("col guasto: tutti rossi ⇒ 0 (visto)", esito_col_guasto([ROSSO] * 4) == VERDE)
    prova("col guasto: uno verde ⇒ 1 (non visto)",
          esito_col_guasto([ROSSO, VERDE, ROSSO, ROSSO]) == ROSSO)
    prova("col guasto: un cieco ⇒ 3", esito_col_guasto([ROSSO, CIECO]) == CIECO)
    print()
    if guai:
        print("⛔ CERTIFICAZIONE FALLITA: %d prove su %d" % (len(guai), len(fatte)))
        return 1
    print("⭐ CERTIFICATO (%d prove): l'atteso e' quel che un campo fa con quei tasti, "
          "senza Maiusc\n   viene un'altra cosa, e il valore si rilegge dai pixel anche "
          "spostato e sporcato." % len(fatte))
    return 0


# ═══════════════════════════════════════════════════════════════════════════
#  DENTRO LA SCATOLA — la scena
# ═══════════════════════════════════════════════════════════════════════════
def pagina_scena():
    """⭐ La pagina, con la tavolozza di QUESTO programma infilata dentro."""
    tav = {k: "rgb(%d,%d,%d)" % v for k, v in COLORI.items()}
    passo = (STRISCIA_X1 - STRISCIA_X0) / (CASELLE + 2) * 100
    return """<!doctype html><meta charset=utf-8><title>REMOTIX C23</title>
<style>
 html,body{margin:0;height:100%%;background:#202020;overflow:hidden}
 #f{position:fixed;left:4vw;top:8vh;width:92vw;height:36vh;font:18vh/1 monospace;
    border:0;padding:0 2vw;box-sizing:border-box;background:#fff;color:#000;outline:0}
 .k{position:fixed;top:%(y0)fvh;height:%(h)fvh;width:calc(%(w)fvw - 6px)}
</style>
<input id=f autocomplete=off spellcheck=false>
<div id=s></div>
<script>
const TAV=%(tav)s, VUOTO='rgb(%(vu)s)', ALTRO='rgb(%(al)s)', MARCA='rgb(%(ma)s)', N=%(n)d;
const f=document.getElementById('f'), s=document.getElementById('s'), k=[];
for (let i=0;i<N+2;i++){const d=document.createElement('div');d.className='k';
  d.style.left=(%(x0)f+i*%(w)f)+'vw';s.appendChild(d);k.push(d);}
const m=(t)=>fetch('/l',{method:'POST',body:t}).catch(()=>0);
function dipingi(){const v=f.value;k[0].style.background=MARCA;k[N+1].style.background=MARCA;
  for(let i=0;i<N;i++){k[i+1].style.background = i<v.length ? (TAV[v[i]]||ALTRO) : VUOTO;}
  if(v.length>N) k[N].style.background=ALTRO;}
dipingi(); f.focus(); m('caricata');
addEventListener('keydown',e=>m('K '+e.key+' shift='+e.shiftKey+' ctrl='+e.ctrlKey));
f.addEventListener('input',()=>{dipingi();m('V '+JSON.stringify(f.value));});
setInterval(()=>{ if(document.activeElement!==f) f.focus(); dipingi(); },300);
</script>""" % {"tav": json.dumps(tav), "vu": "%d,%d,%d" % VUOTO, "al": "%d,%d,%d" % ALTRO,
                "ma": "%d,%d,%d" % MARCA, "n": CASELLE, "x0": STRISCIA_X0 * 100,
                "w": passo, "y0": STRISCIA_Y0 * 100, "h": (STRISCIA_Y1 - STRISCIA_Y0) * 100}


# Il servitore della scena: serve la pagina e annota quel che la pagina dice.
SERVITORE = r'''
import http.server, sys
PAG = open(sys.argv[2], "rb").read()
LOG = sys.argv[3]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers(); self.wfile.write(PAG)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        t = self.rfile.read(n).decode("utf-8", "replace")
        with open(LOG, "a") as f: f.write(t + "\n")
        self.send_response(204); self.end_headers()
http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
'''


def accendi_la_scena(sc, chi, porta):
    """Servitore + `firefox-esr --kiosk` nella sessione; aspetta «caricata»."""
    b = lambda s: base64.b64encode(s.encode()).decode()     # noqa: E731
    c, t = sc.dentro(
        "set -e; h=/home/{c}; mkdir -p $h/.c23-profilo; "
        "echo {srv} | base64 -d > $h/c23-servitore.py; echo {pag} | base64 -d > $h/c23.html; "
        "echo {pref} | base64 -d > $h/.c23-profilo/user.js; : > $h/c23.log; "
        "chown -R {c}: $h/.c23-profilo $h/c23-servitore.py $h/c23.html $h/c23.log; set +e; "
        "u=$(id -u {c}); "
        "setsid runuser -u {c} -- python3 $h/c23-servitore.py {p} $h/c23.html $h/c23.log "
        "</dev/null >/dev/null 2>&1 & "
        "d=''; for i in $(seq 1 40); do d=$(ls /run/user/$u 2>/dev/null | "
        "grep -E '^wayland-[0-9]+$' | head -1); [ -n \"$d\" ] && break; sleep 0.5; done; "
        "[ -n \"$d\" ] || {{ echo 'nessun socket wayland'; exit 2; }}; sleep 1; "
        "setsid runuser -u {c} -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
        "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
        "XDG_SESSION_TYPE=wayland HOME=$h firefox-esr --no-remote --new-instance "
        "--profile $h/.c23-profilo --kiosk http://127.0.0.1:{p}/ "
        "</dev/null >$h/.c23-firefox.log 2>&1 & "
        "for i in $(seq 1 80); do grep -q caricata $h/c23.log && {{ echo accesa; exit 0; }}; "
        "sleep 0.5; done; echo 'la scena non ha detto «caricata»'; tail -5 $h/.c23-firefox.log; "
        "exit 1".format(c=chi, p=porta, srv=b(SERVITORE), pag=b(pagina_scena()),
                        pref=b(C21.PREFERENZE)), 90)
    return c == 0, t


def leggi_il_quaderno(sc, chi):
    _c, t = sc.dentro("cat /home/%s/c23.log 2>/dev/null" % chi, 30)
    return [r for r in t.splitlines() if r.strip()]


# ═══════════════════════════════════════════════════════════════════════════
#  I TASTI VERI
# ═══════════════════════════════════════════════════════════════════════════
def manda(g, passi):
    """⭐ Tasti VERI dati al browser: `Input.dispatchKeyEvent` o le azioni W3C."""
    if hasattr(g, "cdp"):
        mod = 0
        for tipo, nome in passi:
            if nome in SPECIALI:
                key, code, vk, _w, bit = SPECIALI[nome]
                if tipo == "giu":
                    mod |= bit
                g.cdp.chiama("Input.dispatchKeyEvent",
                             type="rawKeyDown" if tipo == "giu" else "keyUp",
                             key=key, code=code, windowsVirtualKeyCode=vk, modifiers=mod)
                if tipo == "su":
                    mod &= ~bit
            else:
                code = "Space" if nome == " " else "Key" + nome.upper()
                vk = 32 if nome == " " else ord(nome.upper())
                p = dict(type="keyDown" if tipo == "giu" else "keyUp", key=nome, code=code,
                         windowsVirtualKeyCode=vk, modifiers=mod)
                if tipo == "giu" and not (mod & 2):
                    p["text"] = p["unmodifiedText"] = nome
                g.cdp.chiama("Input.dispatchKeyEvent", **p)
            time.sleep(PAUSA_MS / 1000.0)
        return
    az = []
    for tipo, nome in passi:
        v = SPECIALI[nome][3] if nome in SPECIALI else nome
        az.append({"type": "keyDown" if tipo == "giu" else "keyUp", "value": v})
        az.append({"type": "pause", "duration": PAUSA_MS})
    g.m.chiama("WebDriver:PerformActions",
               {"actions": [{"type": "key", "id": "tastiera", "actions": az}]})
    g.m.chiama("WebDriver:ReleaseActions")


def fotografa_e_leggi(g, geo, voluto, salva, nome):
    """Fotografa finche' la striscia dice `voluto` o finisce `ATTESA_S`.
    Torna (valore letto o None, perche')."""
    from PIL import Image
    fine = time.time() + ATTESA_S
    letto, perche, png = None, "nessuna fotografia", None
    while True:
        try:
            png = C21.foto_piena(g)
        except Exception as e:                   # noqa: BLE001
            png, perche = None, "fotografia fallita: %s" % str(e)[:120]
        if png:
            im = Image.open(io.BytesIO(png)).convert("RGB")
            letto, perche = leggi_striscia(campionatore(im, geo))
            if letto == voluto:
                break
        if time.time() >= fine:
            break
        time.sleep(FOTO_OGNI_S)
    if salva and png:
        with open(os.path.join(salva, "%s.png" % nome), "wb") as fh:
            fh.write(png)
    return letto, perche


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA DI UN BROWSER
# ═══════════════════════════════════════════════════════════════════════════
def osserva(nome, o, sc, chi):
    """Torna la riga del browser, con `esiti` dei casi (o `esito` CIECO)."""
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
        print("   tela %sx%s · buffer %sx%s" % (geo["tl"], geo["ta"], geo["bw"], geo["bh"]),
              flush=True)
        # ⭐ la sveglia di C21: su GNOME la sessione nasce nella vista d'insieme
        print("   sveglia: %s" % C21.sveglia(g, geo), flush=True)
        ok, t = accendi_la_scena(sc, chi, o.porta_scena)
        print("   scena: %s" % ((t or "?").splitlines() or ["?"])[-1], flush=True)
        if not ok:
            return dict(riga, esito=CIECO, perche="la scena non si accende: %s" % t[-300:])
        time.sleep(3)
        # ⚠ Un clic nel campo remoto: la finestra nuova prende il fuoco della
        #   tastiera anche dove il desktop non glielo da' da se'.
        x, y = C21.dal_desktop_al_vetro(geo, geo["tl"] * 0.5, geo["ta"] * 0.26)
        g.clic(x, y)
        time.sleep(1.0)
        esiti, casi = [], []
        for titolo, base, seq, atteso in CASI:
            if o.senza_maiusc:
                seq = senza_maiusc(seq)
            corto = titolo.split()[0]
            manda(g, PULISCI)
            vuoto, pv = fotografa_e_leggi(g, geo, "", o.salva, "%s-c%s-0vuoto" % (nome, corto))
            manda(g, scrivi(base))
            vb, pb = fotografa_e_leggi(g, geo, base, o.salva, "%s-c%s-1base" % (nome, corto))
            n0 = len(leggi_il_quaderno(sc, chi))
            manda(g, seq)
            visto, pvi = fotografa_e_leggi(g, geo, atteso, o.salva,
                                           "%s-c%s-2dopo" % (nome, corto))
            es, msg = giudica_caso(titolo, base, atteso, vuoto, vb, visto)
            if es == CIECO and (vuoto is None or vb is None):
                msg += " — %s" % (pv or pb)
            elif visto is None:
                es, msg = CIECO, "%s: la striscia non si legge dopo la sequenza: %s" % (
                    titolo, pvi)
            quad = leggi_il_quaderno(sc, chi)[n0:]
            tasti = [r[2:] for r in quad if r.startswith("K ")]
            print("   %s %s" % ({VERDE: "⭐ 0", ROSSO: "⛔ 1", CIECO: "⚠ 3"}[es], msg),
                  flush=True)
            if es != VERDE:
                print("        keydown remoti: %s" % " | ".join(tasti)[:400], flush=True)
            esiti.append(es)
            casi.append({"caso": corto, "esito": es, "visto": visto, "atteso": atteso,
                         "keydown_remoti": tasti})
            if es == CIECO:
                break
        try:
            st = g.js("return REMOTIX.input_classico.stato().tasti_premuti")
        except Exception as ex:                  # noqa: BLE001
            st = "? (%s)" % str(ex)[:80]
        print("   tasti premuti per la pagina, alla fine: %s" % (st,), flush=True)
        return dict(riga, esiti=esiti, casi=casi, tasti_premuti_alla_fine=st)
    finally:
        try:
            g.chiudi()
        except Exception as ex:                  # noqa: BLE001
            print("   ⚠ chiusura del browser: %s" % ex)


def giudica_browser(riga, guasto):
    if "esiti" not in riga:
        return riga
    es = riga["esiti"]
    if not guasto:
        e = esito_complessivo(es)
        perche = {VERDE: "tutti e %d i casi tornano" % len(es),
                  ROSSO: "%d casi su %d non tornano" % (es.count(ROSSO), len(es)),
                  CIECO: "un caso non si e' potuto guardare"}[e]
        return dict(riga, esito=e, perche=perche)
    e = esito_col_guasto(es)
    perche = {VERDE: "⭐ GUASTO VISTO: senza Maiusc tutti e %d i casi sono rossi" % len(es),
              ROSSO: "⛔ GUASTO NON VISTO: senza Maiusc %d casi tornano lo stesso"
                     % es.count(VERDE),
              CIECO: "col guasto un caso non si e' potuto guardare"}[e]
    return dict(riga, esito=e, perche=perche)


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--scatola", choices=sorted(PORTE))
    a.add_argument("--porta", type=int, help="la porta del prodotto (di norma quella "
                   "della scatola della rete)")
    a.add_argument("--contenitore", default="", help="il contenitore podman, se non e' "
                   "rete11-<scatola> (le scatole di sviluppo rete14-*)")
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--browser", default="firefox,chrome")
    a.add_argument("--visibile", action="store_true",
                   help="finestre vere (nel compositore annidato) invece di headless")
    a.add_argument("--salva", default="", help="cartella per le fotografie")
    a.add_argument("--senza-maiusc", action="store_true",
                   help="GUASTO INNESTATO: le stesse sequenze senza mai premere Maiusc")
    a.add_argument("--certifica", action="store_true")
    a.add_argument("--tetto-s", type=int, default=45)
    a.add_argument("--porte-base", type=int, default=3231)
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
    o.url = "https://%s:%d/" % (o.host, porta)
    o.parola = "c23-" + secrets.token_hex(6)
    o.scena, o.continuita_s, o.registro_cmd = "viva", 8, ""
    o.lascia_acceso = False
    o.porta_scena = random.randint(39000, 39899)
    if o.salva:
        os.makedirs(o.salva, exist_ok=True)
    sc = C20V.Scatola(o.scatola)
    if o.contenitore:
        sc.contenitore = o.contenitore
    chi = "c23u%03d" % random.randint(0, 999)
    assert MODELLO_INQUILINO.match(chi)
    o.utente = chi
    print("⭐ 11-c23 · %s · %s · inquilino %s · browser %s · %s%s"
          % (sc.contenitore, o.url, chi, o.browser,
             "finestre vere" if o.visibile else "HEADLESS",
             " · ⛔ GUASTO INNESTATO --senza-maiusc" if o.senza_maiusc else ""))
    righe = []
    for b in [x.strip() for x in o.browser.split(",") if x.strip()]:
        sc.sgombera(chi)
        c, t = sc.crea(chi, o.parola)
        if c != 0:
            print("⛔ non ho potuto creare %s: %s" % (chi, t[-200:]))
            return 3
        try:
            r = giudica_browser(osserva(b, o, sc, chi), o.senza_maiusc)
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
    if o.senza_maiusc:
        print({VERDE: "⭐ IL GUASTO INNESTATO E' STATO VISTO (esito 0: al contrario, "
                      "come ogni guasto della rete)",
               ROSSO: "⛔⛔ IL GUASTO INNESTATO NON E' STATO VISTO",
               CIECO: "⚠ col guasto innestato NON ho potuto guardare ⇒ 3"}[esito])
    else:
        print("%s C23(%s): %s" % ({VERDE: "⭐", ROSSO: "⛔⛔", CIECO: "⚠"}[esito],
                                  o.scatola, NOME_ESITO[esito]))
    return esito


if __name__ == "__main__":
    sys.exit(main())
