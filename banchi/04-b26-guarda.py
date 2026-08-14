#!/usr/bin/env python3
"""
04-b26-guarda.py — il GIUDIZIO del banco A6, ed e' il pezzo che decide se il
resto vale.  Non lancia niente: legge quel che `04-b26-cursore` ha depositato e
risponde alle due domande, ⛔ ciascuna con il suo controllo positivo.

    python3 04-b26-guarda.py <cartella-del-deposito>

⛔ LE DUE DOMANDE, e sono distinte:

  1. IL CURSORE NON E' NELL'IMMAGINE.
     Si guardano DUE fotogrammi presi con il puntatore in due punti noti, A e B.
     Se il puntatore finisse nei pixel, l'intorno di A sarebbe diverso fra i due
     (in B il puntatore non e' piu' li').

     ⛔ IL CONTROLLO POSITIVO, ed e' obbligatorio: lo stesso confronto si rifa'
        su un fotogramma in cui il cursore **ce l'abbiamo messo noi**, con la
        forma VERA arrivata in banda laterale.  Se il confronto non lo vede,
        lo strumento e' cieco e ⛔ il verde della domanda 1 NON VALE.
        («questo strumento sa trovare qualcosa che c'e' di sicuro?»,
        `CODER.md` §3.10.)

     ⚠ E c'e' un terzo riquadro, lontano da A e da B, che misura QUANTO SI MUOVE
       DA SOLO lo schermo fra i due scatti: se il fondo e' rumoroso, la risposta
       non e' «no», e' «non conclusiva».

  2. LA FORMA ARRIVA IN BANDA LATERALE.
     Si rileggono ⛔ **i byte** di `filo.bin` — non il registro di chi manda
     (`CODER.md` §3.8) — e su ciascun messaggio si verifica `RCP.md` §7.2:

        lunghezza == 8 + larghezza x altezza x 4      ⛔ esattamente
        larghezza <= 256 e altezza <= 256
        nascosto  ⇒ 0x0 e punto attivo 0,0            (§5.5)
        visibile  ⇒ 0 <= attivo_x < larghezza, idem y (§5.5)

     ⛔ E la terza domanda dentro la seconda: **quante** forme contro **quanti**
        buffer.  Il metadato arriva a ogni buffer: se le forme fossero tante
        quanti i buffer, si starebbe rimandando mille volte la stessa immagine.

⚠ L'inquadratura di `filo.bin` — quattro byte di lunghezza davanti a ogni
  messaggio — e' del BANCO, non di `RCP.md` §6.1: serve solo a rileggere il
  deposito.  Il messaggio che ci sta dentro e' invece esattamente quello di §7.2.
"""
import json
import os
import struct
import sys

VERDE = "\033[1;32mOK\033[0m"
ROSSO = "\033[1;31mNO\033[0m"
GRIGIO = "\033[1;33m??\033[0m"

# Quanto grande e' il riquadro guardato attorno a una posizione del puntatore.
# ⚠ Piu' grande del cursore piu' grande che Mutter possa mandare a scala 1.
RIQUADRO = 96

# Sotto questa differenza per canale due pixel si dicono uguali: la cattura e'
# BGRx senza perdita, quindi il rumore vero e' zero — la soglia c'e' solo per
# non litigare su un bit.
SOGLIA = 8


def leggi_ppm(percorso):
    """P6 binario, 8 bit per canale.  Ritorna (larghezza, altezza, bytes RGB)."""
    with open(percorso, "rb") as f:
        dati = f.read()
    campi, i = [], 0
    while len(campi) < 4:
        while i < len(dati) and dati[i : i + 1].isspace():
            i += 1
        if dati[i : i + 1] == b"#":
            while i < len(dati) and dati[i] != 0x0A:
                i += 1
            continue
        j = i
        while j < len(dati) and not dati[j : j + 1].isspace():
            j += 1
        campi.append(dati[i:j])
        i = j
    i += 1
    l, a = int(campi[1]), int(campi[2])
    return l, a, dati[i : i + l * a * 3]


def macchia(pixel, l, a, cx, cy, colore, lato=RIQUADRO):
    """
    ⛔ LA DOMANDA 1, NELLA SUA FORMA PIU' DIRETTA: quanti pixel del riquadro NON
       sono del colore noto?  Un cursore dipinto dentro l'immagine e' una macchia;
       uno sfondo a tinta piatta non lo e'.  ⚠ Non ha bisogno di due scatti, e
       quindi non ha bisogno che i due scatti siano freschi.
    """
    r, g, b = colore
    x0, y0 = max(0, cx - lato // 2), max(0, cy - lato // 2)
    x1, y1 = min(l, x0 + lato), min(a, y0 + lato)
    n = 0
    for y in range(y0, y1):
        base = (y * l + x0) * 3
        riga = pixel[base : base + (x1 - x0) * 3]
        for i in range(0, len(riga), 3):
            if (
                abs(riga[i] - r) > SOGLIA
                or abs(riga[i + 1] - g) > SOGLIA
                or abs(riga[i + 2] - b) > SOGLIA
            ):
                n += 1
    return n, (x1 - x0) * (y1 - y0)


def colore_da_esadecimale(testo):
    testo = testo.lstrip("#")
    return int(testo[0:2], 16), int(testo[2:4], 16), int(testo[4:6], 16)


def riquadro(pixel, l, a, cx, cy, lato=RIQUADRO):
    x0, y0 = max(0, cx - lato // 2), max(0, cy - lato // 2)
    x1, y1 = min(l, x0 + lato), min(a, y0 + lato)
    fuori = []
    for y in range(y0, y1):
        base = (y * l + x0) * 3
        fuori.append(pixel[base : base + (x1 - x0) * 3])
    return b"".join(fuori), (x1 - x0), (y1 - y0)


def diversi(uno, due):
    """Quanti pixel differiscono di piu' di SOGLIA su almeno un canale."""
    if len(uno) != len(due):
        return -1
    n = 0
    for i in range(0, len(uno), 3):
        if (
            abs(uno[i] - due[i]) > SOGLIA
            or abs(uno[i + 1] - due[i + 1]) > SOGLIA
            or abs(uno[i + 2] - due[i + 2]) > SOGLIA
        ):
            n += 1
    return n


def componi(pixel, l, a, forma_bgra, fl, fa, px, py, hx, hy):
    """
    ⛔ IL CONTROLLO POSITIVO: mette il cursore VERO dentro il fotogramma, con
       l'alfa premoltiplicata come dice `RCP.md` §5.5 — cioe'
       `fuori = sopra + sotto x (1 - alfa)`.
    """
    fuori = bytearray(pixel)
    x0, y0 = px - hx, py - hy
    for y in range(fa):
        yy = y0 + y
        if not (0 <= yy < a):
            continue
        for x in range(fl):
            xx = x0 + x
            if not (0 <= xx < l):
                continue
            i = (y * fl + x) * 4
            b, g, r, al = forma_bgra[i], forma_bgra[i + 1], forma_bgra[i + 2], forma_bgra[i + 3]
            j = (yy * l + xx) * 3
            fuori[j + 0] = min(255, r + (fuori[j + 0] * (255 - al)) // 255)
            fuori[j + 1] = min(255, g + (fuori[j + 1] * (255 - al)) // 255)
            fuori[j + 2] = min(255, b + (fuori[j + 2] * (255 - al)) // 255)
    return bytes(fuori)


def rileggi_il_filo(percorso):
    """⛔ I BYTE, dal lato che riceve.  Ritorna (messaggi, rilievi)."""
    messaggi, rilievi = [], []
    with open(percorso, "rb") as f:
        dati = f.read()
    i = 0
    while i + 4 <= len(dati):
        (lunghezza,) = struct.unpack(">I", dati[i : i + 4])
        i += 4
        corpo = dati[i : i + lunghezza]
        i += lunghezza
        if len(corpo) < 8:
            rilievi.append("un messaggio tronco: %d byte invece di %d" % (len(corpo), lunghezza))
            break
        larghezza, altezza, ax, ay = struct.unpack(">HHhh", corpo[:8])
        atteso = 8 + larghezza * altezza * 4
        m = {
            "larghezza": larghezza,
            "altezza": altezza,
            "attivo_x": ax,
            "attivo_y": ay,
            "lunghezza": lunghezza,
            "lunghezza_attesa": atteso,
            "immagine": corpo[8:],
        }
        # ⛔ RCP §7.2 e §5.5, applicati ai byte e non alle intenzioni.
        if lunghezza != atteso:
            rilievi.append(
                "⛔ ERRORE_PROTOCOLLO: lunghezza %d, ne servivano %d (%dx%d)"
                % (lunghezza, atteso, larghezza, altezza)
            )
        if larghezza > 256 or altezza > 256:
            rilievi.append("⛔ ERRORE_PROTOCOLLO: %dx%d supera 256" % (larghezza, altezza))
        if (larghezza == 0) != (altezza == 0):
            rilievi.append("⛔ §5.5: una sola misura a zero (%dx%d)" % (larghezza, altezza))
        if larghezza == 0 and altezza == 0:
            if ax or ay:
                rilievi.append("⛔ §5.5: nascosto con punto attivo %d,%d" % (ax, ay))
        else:
            if not (0 <= ax < larghezza) or not (0 <= ay < altezza):
                rilievi.append(
                    "⛔ §5.5: punto attivo %d,%d fuori da %dx%d" % (ax, ay, larghezza, altezza)
                )
        messaggi.append(m)
    return messaggi, rilievi


def principale(cartella, incorporato=None):
    esiti = []
    percorso = os.path.join(cartella, "esiti.jsonl")
    if os.path.exists(percorso):
        with open(percorso) as f:
            for riga in f:
                riga = riga.strip()
                if riga:
                    esiti.append(json.loads(riga))

    conteggi = [e for e in esiti if e.get("cosa") == "conteggi"]
    forme = [e for e in esiti if e.get("cosa") == "CURSORE_FORMA"]
    modo = conteggi[0]["modo"] if conteggi else "?"
    stato = 0

    print("\n\033[1m== 04-b26 — il giudizio, modo %s ==\033[0m" % modo)

    # ------------------------------------------------------------------
    # DOMANDA 2 — la forma arriva in banda laterale, letta DAI BYTE
    # ------------------------------------------------------------------
    print("\n\033[1m-- domanda 2: la forma arriva in banda laterale?\033[0m")
    filo = os.path.join(cartella, "filo.bin")
    if not os.path.exists(filo):
        print("  %s  nessun `filo.bin`: non ho guardato — ⛔ NON e «non arriva»" % GRIGIO)
        stato = max(stato, 3)
        messaggi, rilievi = [], []
    else:
        messaggi, rilievi = rileggi_il_filo(filo)
        nascosti = [m for m in messaggi if m["larghezza"] == 0 and m["altezza"] == 0]
        visibili = [m for m in messaggi if m["larghezza"] or m["altezza"]]
        print(
            "  --  %d messaggi sul filo: %d nascosti (0x0), %d con una forma"
            % (len(messaggi), len(nascosti), len(visibili))
        )
        for m in visibili:
            print(
                "  --  forma %dx%d, punto attivo %d,%d, lunghezza %d (attesa %d)"
                % (
                    m["larghezza"],
                    m["altezza"],
                    m["attivo_x"],
                    m["attivo_y"],
                    m["lunghezza"],
                    m["lunghezza_attesa"],
                )
            )
        if rilievi:
            for r in rilievi:
                print("  %s  %s" % (ROSSO, r))
            stato = max(stato, 5)
        elif messaggi:
            print("  %s  ogni messaggio rispetta RCP §7.2 e §5.5, ai byte" % VERDE)

        # ⛔ nascosto e non pervenuto sono due cose diverse
        if conteggi:
            c = conteggi[0]
            assenti = c.get("cursore_assente", 0)
            presenti = c.get("cursore_metadati", 0)
            buffer = c.get("fotogrammi", c.get("buffer", 0))
            print(
                "  --  metadati: presenti %d, assenti %d, su %d buffer"
                % (presenti, assenti, buffer)
            )
            if presenti == 0 and buffer > 0:
                print(
                    "  %s  ⛔ IL DIFETTO: %d buffer e ZERO metadati ⇒ `CURSORE_FORMA` e un "
                    "canale senza sorgente" % (ROSSO, buffer)
                )
                stato = max(stato, 6)
            elif buffer == 0:
                print("  %s  zero buffer: non ho misurato niente" % GRIGIO)
                stato = max(stato, 3)
            else:
                print("  %s  il metadato ARRIVA (%d buffer su %d)" % (VERDE, presenti, buffer))

    # ------------------------------------------------------------------
    # DOMANDA 2-bis — non si rimanda mille volte la stessa immagine
    # ------------------------------------------------------------------
    print("\n\033[1m-- domanda 2-bis: si rimanda la stessa immagine?\033[0m")
    movimento = [e for e in esiti if e.get("cosa") == "solo-movimento"]
    if conteggi:
        c = conteggi[0]
        buffer = c.get("fotogrammi", c.get("buffer", 0))
        presenti = c.get("cursore_metadati", 0)
        if presenti and len(messaggi):
            print(
                "  --  %d metadati letti ⇒ %d `CURSORE_FORMA` (%.2f%%)"
                % (presenti, len(messaggi), 100.0 * len(messaggi) / presenti)
            )
            if len(messaggi) >= presenti:
                print("  %s  ⛔ una forma per metadato: NON si sta deduplicando" % ROSSO)
                stato = max(stato, 7)
            else:
                print("  %s  la stessa forma non riparte a ogni buffer" % VERDE)
        elif buffer:
            print("  %s  nessun metadato da deduplicare" % GRIGIO)
    if movimento:
        m = movimento[0]
        print(
            "  --  %d movimenti del puntatore senza cambiargli forma ⇒ %d forme nuove"
            % (m["movimenti"], m["forme_nuove"])
        )
        if m["forme_nuove"] > 1:
            print("  %s  ⛔ la forma riparte muovendo il puntatore" % ROSSO)
            stato = max(stato, 7)
        else:
            print("  %s  muovere il puntatore NON rimanda la forma" % VERDE)

    # ------------------------------------------------------------------
    # DOMANDA 2-ter — nascosto, ritorno, forma diversa
    # ⛔ «Non rimanda sempre» non deve essere diventato «non manda mai».
    # ------------------------------------------------------------------
    print("\n\033[1m-- domanda 2-ter: nascosto, ritorno, forma diversa\033[0m")
    for cosa, atteso, spiega in (
        ("tocco", "nascosti_nuovi", "un tocco deve NASCONDERE il puntatore (0x0)"),
        ("ritorno", "forme_nuove", "tornando, la forma deve RIPARTIRE"),
        ("forma-diversa", "forme_nuove", "una forma diversa deve PARTIRE"),
    ):
        righe = [e for e in esiti if e.get("cosa") == cosa]
        if not righe:
            print("  %s  «%s» non misurato" % (GRIGIO, cosa))
            continue
        n = righe[0][atteso]
        if n >= 1:
            print("  %s  %s — %d" % (VERDE, spiega, n))
        else:
            print("  %s  ⛔ %s — %d" % (ROSSO, spiega, n))
            stato = max(stato, 7)

    # ------------------------------------------------------------------
    # DOMANDA 1 — il cursore non e' dentro l'immagine
    # ------------------------------------------------------------------
    print("\n\033[1m-- domanda 1: il cursore e dentro l'immagine?\033[0m")
    fa_p = os.path.join(cartella, "fotogramma-A.ppm")
    fb_p = os.path.join(cartella, "fotogramma-B.ppm")
    if not os.path.exists(fa_p):
        print("  %s  manca il fotogramma: non ho guardato — ⛔ NON e «non c'e»" % GRIGIO)
        return max(stato, 3)

    punti = {e["punto"]: e for e in esiti if e.get("cosa") == "fotogramma" and "x" in e}
    if "A" not in punti:
        print("  %s  non so dove fosse il puntatore: non giudico" % GRIGIO)
        return max(stato, 3)
    ax, ay = punti["A"]["x"], punti["A"]["y"]

    l, a, pa = leggi_ppm(fa_p)
    ra_in_a, _, _ = riquadro(pa, l, a, ax, ay)
    fondo_a, _, _ = riquadro(pa, l, a, l // 2, a // 2)
    totale = RIQUADRO * RIQUADRO

    # ------------------------------------------------------------------
    # ⭐⭐ LA PROVA DIRETTA: il riquadro attorno al puntatore e ancora tutto
    #     del colore noto?  ⛔ Non serve un secondo scatto, e non serve che lo
    #     scatto sia fresco: un cursore dipinto dentro sarebbe una MACCHIA.
    # ------------------------------------------------------------------
    tinte = {e["punto"]: e["colore"] for e in esiti if e.get("cosa") == "tinta"}
    macchia_meta = None
    if "A" in tinte:
        colore = colore_da_esadecimale(tinte["A"])
        macchia_meta, quanti = macchia(pa, l, a, ax, ay, colore)
        print(
            "  --  il riquadro attorno ad A doveva essere tutto %s: %d pixel su %d\n"
            "      non lo sono" % (tinte["A"], macchia_meta, quanti)
        )
        if macchia_meta > quanti // 2:
            print(
                "  %s  il fondo NON e della tinta chiesta: la prova diretta non vale\n"
                "      (lo sfondo non e stato ridipinto?)" % GRIGIO
            )
            macchia_meta = None

    # ------------------------------------------------------------------
    # ⛔⛔ IL CONTROLLO POSITIVO SUI PIXEL VERI, e viene PRIMA del verdetto.
    #
    # Il giro `--incorporato` chiede a Mutter `cursor-mode = 1`: il puntatore
    # lo dipinge LUI, dentro l'immagine.  ⇒ Se il confronto non lo vede nemmeno
    # li', lo strumento e cieco e il «non c'e» dell'altro giro non vale niente.
    # ------------------------------------------------------------------
    d_controllo_pixel = None
    if incorporato:
        inc_p = os.path.join(incorporato, "fotogramma-A.ppm")
        if os.path.exists(inc_p):
            li, ai, pi = leggi_ppm(inc_p)
            if (li, ai) == (l, a):
                ra_in_inc, _, _ = riquadro(pi, l, a, ax, ay)
                fondo_inc, _, _ = riquadro(pi, l, a, l // 2, a // 2)
                d_controllo_pixel = diversi(ra_in_a, ra_in_inc)
                d_fondo_inc = diversi(fondo_a, fondo_inc)
                print(
                    "  --  CONTROLLO POSITIVO sui PIXEL (cursor-mode = 1, il puntatore lo\n"
                    "      dipinge Mutter): attorno ad A cambiano %d pixel su %d; nel riquadro\n"
                    "      di fondo, dove il puntatore non c'e mai stato, %d"
                    % (d_controllo_pixel, totale, d_fondo_inc)
                )
                if d_controllo_pixel <= max(4 * d_fondo_inc, 20):
                    print(
                        "  %s  ⛔ LO STRUMENTO E CIECO: non vede il cursore nemmeno quando\n"
                        "      Mutter lo dipinge dentro.  La domanda 1 NON HA RISPOSTA." % ROSSO
                    )
                    return max(stato, 8)
                print("  %s  lo strumento sa vedere un cursore DIPINTO NEI PIXEL" % VERDE)
                if macchia_meta is not None and "A" in tinte:
                    colore = colore_da_esadecimale(tinte["A"])
                    macchia_inc, quanti = macchia(pi, l, a, ax, ay, colore)
                    print(
                        "  --  ⭐ LA PROVA DIRETTA, i due giri a confronto: pixel NON del\n"
                        "      colore noto attorno ad A — a metadato %d, incorporato %d"
                        % (macchia_meta, macchia_inc)
                    )
                    if macchia_inc <= macchia_meta:
                        print(
                            "  %s  ⛔ nemmeno con `cursor-mode = 1` compare una macchia: la\n"
                            "      prova diretta NON distingue niente" % ROSSO
                        )
                        stato = max(stato, 8)
                    elif macchia_meta == 0:
                        print(
                            "  %s  ⭐⭐ IL CURSORE NON E NELL'IMMAGINE: attorno al puntatore\n"
                            "      NON c'e un solo pixel fuori dalla tinta, e con `cursor-mode = 1`\n"
                            "      ce ne sono %d — cioe la macchia si vedrebbe eccome"
                            % (VERDE, macchia_inc)
                        )
                    else:
                        print(
                            "  %s  ⛔ IL CURSORE E NELL'IMMAGINE: %d pixel fuori dalla tinta\n"
                            "      attorno al puntatore (`SPECIFICHE.md` §7.1)"
                            % (ROSSO, macchia_meta)
                        )
                        stato = max(stato, 9)
            else:
                print("  %s  il giro incorporato ha misure diverse: non confrontabile" % GRIGIO)
        else:
            print("  %s  nessun fotogramma dal giro `--incorporato`" % GRIGIO)

    # --- il secondo controllo positivo, indipendente: la forma VERA composta ---
    forma_file, forma_meta = None, None
    for e in sorted(forme, key=lambda e: e.get("serie", 0), reverse=True):
        if e.get("larghezza"):
            q = os.path.join(cartella, "forma-%03d.bgra" % e["serie"])
            if os.path.exists(q):
                forma_file, forma_meta = q, e
                break
    d_controllo_finto = None
    if forma_file:
        with open(forma_file, "rb") as f:
            bgra = f.read()
        finto = componi(
            pa, l, a, bgra,
            forma_meta["larghezza"], forma_meta["altezza"],
            ax, ay, forma_meta["attivo_x"], forma_meta["attivo_y"],
        )
        rc, _, _ = riquadro(finto, l, a, ax, ay)
        d_controllo_finto = diversi(ra_in_a, rc)
        print(
            "  --  secondo controllo: la forma VERA (%dx%d, serie %d) composta a mano\n"
            "      dentro il fotogramma cambia %d pixel su %d"
            % (
                forma_meta["larghezza"], forma_meta["altezza"], forma_meta["serie"],
                d_controllo_finto, totale,
            )
        )

    if d_controllo_pixel is None and d_controllo_finto is None:
        print(
            "  %s  ⛔ NESSUN CONTROLLO POSITIVO: «non l'ho visto» e «non so guardare»\n"
            "      hanno lo stesso aspetto (`CODER.md` §3.10).  Non giudico." % ROSSO
        )
        return max(stato, 8)

    # --- il verdetto: spostando il puntatore, i pixel dove stava non cambiano ---
    if os.path.exists(fb_p) and "B" in punti:
        bx, by = punti["B"]["x"], punti["B"]["y"]
        l2, a2, pb = leggi_ppm(fb_p)
        if (l2, a2) == (l, a):
            d_a = diversi(ra_in_a, riquadro(pb, l, a, ax, ay)[0])
            d_b = diversi(riquadro(pa, l, a, bx, by)[0], riquadro(pb, l, a, bx, by)[0])
            d_fondo = diversi(fondo_a, riquadro(pb, l, a, l // 2, a // 2)[0])
            print(
                "  --  fra i due fotogrammi (puntatore in A e poi in B): attorno ad A\n"
                "      cambiano %d pixel, attorno a B %d, nel fondo fermo %d"
                % (d_a, d_b, d_fondo)
            )
            rumore = max(d_fondo * 2, 20)
            if d_a <= rumore and d_b <= rumore:
                print(
                    "  %s  ⭐ IL CURSORE NON E NELL'IMMAGINE: spostandolo, i pixel dove stava\n"
                    "      non cambiano — e lo strumento un cursore lo vedrebbe (%s)"
                    % (
                        VERDE,
                        "controllo sui pixel: %d" % d_controllo_pixel
                        if d_controllo_pixel is not None
                        else "controllo composto: %d" % d_controllo_finto,
                    )
                )
            else:
                print(
                    "  %s  ⛔ IL CURSORE E DENTRO L'IMMAGINE: %d/%d pixel cambiano dove stava\n"
                    "      il puntatore — l'utente ne vedrebbe DUE (`SPECIFICHE.md` §7.1)"
                    % (ROSSO, d_a, d_b)
                )
                stato = max(stato, 9)
        else:
            print("  %s  i due fotogrammi hanno misure diverse" % GRIGIO)
    elif d_controllo_pixel is not None:
        # ⚠ Un fotogramma solo basta se il controllo positivo e sui PIXEL VERI:
        #   il giro incorporato dice quanti pixel varrebbe un cursore li dentro.
        print(
            "  %s  ⭐ IL CURSORE NON E NELL'IMMAGINE: nel giro a metadato il riquadro\n"
            "      attorno ad A e diverso da quello incorporato per %d pixel, cioe' quel\n"
            "      cursore li dentro NON c'e" % (VERDE, d_controllo_pixel)
        )
    else:
        print("  %s  un fotogramma solo e nessun controllo sui pixel: non concludo" % GRIGIO)
        stato = max(stato, 3)
    return stato


if __name__ == "__main__":
    sys.exit(
        principale(
            sys.argv[1] if len(sys.argv) > 1 else ".",
            sys.argv[2] if len(sys.argv) > 2 else None,
        )
    )
