#!/usr/bin/env python3
"""02-giudizio-mira.py — LA SCENA DICHIARATA del giudizio dei pixel.

    python3 02-giudizio-mira.py --giro g1 --cartella /tmp/mira
    python3 02-giudizio-mira.py --giro g2 --cartella /tmp/mira --larghezza 3840 --altezza 2160

Produce tre file:
    mira-<giro>.rgb48   i pixel, rgb48le, **valori a 10 bit portati in alto**
                        (v10 << 6): e' quel che si da' in pasto a `ffmpeg`
                        con `-pix_fmt rgb48le`.
    mira-<giro>.png     la stessa cosa a 8 bit, solo per essere guardata.
    mira-<giro>.json    ⛔ LE COORDINATE DELLE ZONE.  Senza questo file il
                        metro non sa dove guardare, e non misura niente.

===========================================================================
⛔ PERCHE' ESISTE QUESTO FILE, E NON E' UN ABBELLIMENTO

`LEZIONI.md` §1.1 e `CODER.md` §3.2: **la scena si dichiara.**  Ma qui la
ragione e' piu' stretta di «dichiarare»: **certi guasti sono invisibili su
certe scene**, e un metro puntato sulla scena sbagliata li promuove tutti.

Quattro casi concreti, e sono i quattro guasti che il mandato mi chiede di
bocciare:

  1. ⛔ **lo scorrimento di UNA RIGA e' invisibile su una scena morbida.**
     Su una sfumatura, spostare tutto di una riga cambia ogni pixel di un
     millesimo: il PSNR resta a 60 dB e il metro promuove.  ⇒ la mira porta
     due PETTINI a passo di 1 pixel — righe bianche e nere alternate —,
     dove uno scorrimento di una riga **inverte** il pettine e porta il PSNR
     a fondo scala.  E' la zona che rende sensibile M0.

  2. ⛔ **lo scambio dei piani del colore e' invisibile alla luminanza.**
     I tre riquadri saturi di questa mira hanno **la stessa luminanza**
     (BT.709: Y = 0,2126 R + 0,7152 G + 0,0722 B):
         rosso  (87,  0,  0)   Y = 18,5 / 255
         verde  ( 0, 26,  0)   Y = 18,4 / 255
         blu    ( 0,  0,255)   Y = 18,4 / 255
     ⇒ scambiare R e B **non muove Y di un LSB**, e ogni metro che guardi
     solo la luminanza promuove il guasto.  E' la zona che dimostra che M4
     (l'identita' dei canali) non e' un ornamento: senza, quel guasto passa.

  3. ⛔ **gli 8 bit al posto dei 10 non si vedono in nessun confronto di
     pixel su una tela a 8 bit** — la differenza e' al massimo un LSB e il
     PSNR resta sopra i 55 dB.  ⇒ la mira porta DUE rampe di grigio affiancate:
     `rampa10` a passo 1/1023 e `rampa8` **la stessa rampa gia' quantizzata
     a 8 bit**.  Su una catena a 10 bit la prima ha ~4 volte i livelli della
     seconda; su una catena troncata **le due diventano uguali**.  La seconda
     rampa e' il controllo interno della prova (S2 §3.7 punto 2): se il metro
     non sa distinguerle, non sta guardando i bit, sta guardando il rumore.

  4. ⛔ **«il fotogramma del giro precedente» non e' distinguibile se la scena
     non cambia.**  ⇒ il riquadro di RUMORE ha per seme il nome del giro:
     due giri diversi hanno rumore diverso, e il metro puo' chiedere «questo
     fotogramma somiglia di piu' alla cattura di ADESSO o a quella di
     PRIMA?».  Con una scena ferma quella domanda non ha risposta, ed e' la
     ragione per cui `CODER.md` §3.2 dice che **la scena si muove sempre**.

E i quattro MARCATORI d'angolo, che servono a due cose insieme:
  · dire se l'immagine e' ribaltata o ruotata (i quattro disegni sono
    diversi fra loro **e** diversi dai propri ribaltamenti);
  · ⛔ essere il **controllo positivo dello strumento sulla scena**: se il
    metro non trova i quattro marcatori nella cattura, non ha davanti la
    scena che crede, e **non da' nessun verdetto**.  E' la differenza fra
    «i pixel non coincidono» e «non ho potuto guardare».

===========================================================================
⛔ E LA TRAPPOLA PIU' CARA DI QUESTA FASE, CHE QUESTA MIRA CHIUDE

`PIANO.md` fase 2: una sessione GNOME headless senza `--virtual-monitor`
parte **viva, completa e NERA** (`STUDI.md` §gnome §13, prova M9).

⛔ Due fotogrammi neri si assomigliano **perfettamente**: PSNR infinito.  Un
metro che confronti soltanto cattura e decodifica darebbe **verde pieno** su
una sessione nera, cioe' il verde piu' vuoto che questo progetto possa
produrre — e sarebbe il gemello esatto del verde che in v1 assolveva un
difetto vivo (`README.md`, «un'accusa al prodotto che invece era del banco»).

⇒ la mira serve anche a questo: la sua varianza e i suoi marcatori sono la
prova che nella sessione **c'e' qualcosa**, e il metro la pretende PRIMA di
confrontare alcunche' (M-V).
===========================================================================
"""
import argparse
import hashlib
import json
import os
import sys

import numpy as np

# I quattro marcatori: ciascuno e' un quadrato diviso in 2x2, e la lista dice
# quali quadranti sono chiari.  ⛔ Scelti in modo che nessuno dei quattro,
# ribaltato in orizzontale o in verticale o ruotato di 180°, coincida con un
# altro dei quattro: e' quel che rende il controllo capace di dire
# «l'immagine e' ribaltata» invece di «i pixel non coincidono».
MARCATORI = {
    "alto-sinistra":  [1, 0, 0, 0],
    "alto-destra":    [1, 1, 0, 0],
    "basso-sinistra": [1, 1, 1, 0],
    "basso-destra":   [1, 0, 1, 1],
}

# I tre riquadri a luminanza uguale (vedi l'intestazione, punto 2).
COLORI_ISOLUMA = {
    "rosso": (87, 0, 0),
    "verde": (0, 26, 0),
    "blu":   (0, 0, 255),
}


def _v10(x8):
    """Da un valore 0..255 al corrispondente 0..1023 (replicando i bit alti)."""
    return (int(x8) << 2) | (int(x8) >> 6)


def costruisci(larghezza, altezza, giro):
    """Ritorna (immagine_10bit  uint16 [h,w,3]  valori 0..1023, zone dict)."""
    if larghezza < 640 or altezza < 480:
        raise SystemExit("⛔ la mira non si costruisce sotto i 640x480: le zone "
                         "si sovrappongono e il metro misurerebbe la zona sbagliata")
    img = np.zeros((altezza, larghezza, 3), dtype=np.uint16)
    zone = {}

    # ── il fondo: una sfumatura diagonale morbida ────────────────────────
    # ⚠ NON e' decorazione: e' la zona su cui uno scorrimento di una riga
    #   NON si vede.  Sta qui apposta, perche' il metro debba dimostrare che
    #   il suo verdetto sullo scorrimento viene dai pettini e non dal fondo.
    yy = np.linspace(0, 1, altezza, dtype=np.float64)[:, None]
    xx = np.linspace(0, 1, larghezza, dtype=np.float64)[None, :]
    fondo = np.clip((yy + xx) * 0.5, 0, 1)
    img[:, :, 0] = (fondo * 400 + 100).astype(np.uint16)
    img[:, :, 1] = (fondo * 400 + 120).astype(np.uint16)
    img[:, :, 2] = (fondo * 400 + 140).astype(np.uint16)

    lato = max(48, min(96, larghezza // 20))

    # ── i quattro marcatori d'angolo ─────────────────────────────────────
    zone["marcatori"] = {}
    posizioni = {
        "alto-sinistra":  (0, 0),
        "alto-destra":    (0, larghezza - lato),
        "basso-sinistra": (altezza - lato, 0),
        "basso-destra":   (altezza - lato, larghezza - lato),
    }
    m = lato // 2
    for nome, (y0, x0) in posizioni.items():
        quad = MARCATORI[nome]
        for i, acceso in enumerate(quad):
            dy, dx = (i // 2) * m, (i % 2) * m
            val = 1000 if acceso else 20
            img[y0 + dy:y0 + dy + m, x0 + dx:x0 + dx + m, :] = val
        zone["marcatori"][nome] = {"y": y0, "x": x0, "lato": lato,
                                   "quadranti": quad}

    # ── i due pettini a passo 1 px ───────────────────────────────────────
    ph = max(64, altezza // 10)
    pw = max(96, larghezza // 6)
    y0 = altezza // 2 - ph // 2
    x0 = lato + 8
    blocco = np.zeros((ph, pw), dtype=np.uint16)
    blocco[0::2, :] = 1000
    blocco[1::2, :] = 20
    img[y0:y0 + ph, x0:x0 + pw, :] = blocco[:, :, None]
    zone["pettine_orizzontale"] = {"y": y0, "x": x0, "h": ph, "w": pw}

    x1 = x0 + pw + 16
    blocco = np.zeros((ph, pw), dtype=np.uint16)
    blocco[:, 0::2] = 1000
    blocco[:, 1::2] = 20
    img[y0:y0 + ph, x1:x1 + pw, :] = blocco[:, :, None]
    zone["pettine_verticale"] = {"y": y0, "x": x1, "h": ph, "w": pw}

    # ── i tre riquadri a luminanza uguale ────────────────────────────────
    ch = max(48, altezza // 12)
    cw = max(48, larghezza // 14)
    y0c = y0 + ph + 16
    zone["colori"] = {}
    for k, (nome, rgb) in enumerate(COLORI_ISOLUMA.items()):
        xc = x0 + k * (cw + 12)
        img[y0c:y0c + ch, xc:xc + cw, 0] = _v10(rgb[0])
        img[y0c:y0c + ch, xc:xc + cw, 1] = _v10(rgb[1])
        img[y0c:y0c + ch, xc:xc + cw, 2] = _v10(rgb[2])
        zone["colori"][nome] = {"y": y0c, "x": xc, "h": ch, "w": cw,
                                "rgb8": list(rgb)}

    # ── le due rampe: 10 bit veri, e la stessa quantizzata a 8 ───────────
    # ⛔ La rampa copre TUTTA l'altezza utile e sale di 1/1023 per riga fin
    #    dove l'altezza lo consente.  Su 1080 righe si arriva a 1023 livelli
    #    distinti; su meno righe se ne hanno quante sono le righe, e il metro
    #    lo sa perche' il numero atteso e' scritto qui sotto.
    rw = max(32, larghezza // 24)
    ry0, ry1 = lato + 8, altezza - lato - 8
    ralt = ry1 - ry0
    rx0 = larghezza - lato - 8 - 2 * rw - 8
    livelli = np.linspace(0, 1023, ralt).astype(np.uint16)
    img[ry0:ry1, rx0:rx0 + rw, :] = livelli[:, None, None]
    # la stessa, troncata a 8 bit e riportata su 10 (cioe' 256 livelli soli)
    liv8 = ((livelli >> 2) << 2) | (livelli >> 8)
    img[ry0:ry1, rx0 + rw + 8:rx0 + 2 * rw + 8, :] = liv8[:, None, None]
    zone["rampa10"] = {"y": ry0, "x": rx0, "h": ralt, "w": rw,
                       "livelli_attesi": int(len(np.unique(livelli)))}
    zone["rampa8"] = {"y": ry0, "x": rx0 + rw + 8, "h": ralt, "w": rw,
                      "livelli_attesi": int(len(np.unique(liv8)))}

    # ── ⛔ LA SFUMATURA DICHIARATA — dove si conta la profondita' ─────────
    # Cucitura di F2.2, 12 agosto 2026, e chiude un errore di metodo che
    # questo banco stava per fare: *«il conto dei livelli va fatto sulla
    # SFUMATURA della scena, non sulle barre piatte — li' i livelli distinti
    # sono una ventina per costruzione, e il controllo direbbe 8 bit su
    # qualunque cosa»*.
    # ⛔ E non e' un'ipotesi: `[M]` 12 agosto, sorgente a 8 bit → Main10 → decodifica,
    #    i due bit bassi del piano Y misurati zona per zona:
    #        tutto il fotogramma  0,254   (regge, ma solo perche' qui la
    #                                      sfumatura e' grande)
    #        la sfumatura         0,249   ⭐ e' questo il numero buono
    #        un riquadro PIATTO   0,954   ⛔ e a gamma limitata 0,473
    #    Su una scrivania vera, dove le zone piatte sono la maggioranza, la
    #    media di tutto il fotogramma andrebbe dalla parte del riquadro
    #    piatto, e M7 direbbe «troncato» su una catena sana.
    # ⇒ un rettangolo di solo fondo sfumato, dichiarato, senza nessun blocco
    #   dentro, ed e' li' che M7 guarda.
    sx0, sy0 = int(larghezza * 0.47), int(altezza * 0.14)
    sx1, sy1 = int(larghezza * 0.83), int(altezza * 0.42)
    zone["sfumatura"] = {"y": sy0, "x": sx0, "h": sy1 - sy0, "w": sx1 - sx0}

    # ── il rumore, con per seme il nome del giro ─────────────────────────
    seme = int(hashlib.sha256(giro.encode()).hexdigest()[:8], 16)
    nh = max(64, altezza // 8)
    nw = max(64, larghezza // 8)
    ny, nx = y0c + ch + 16, x0
    if ny + nh < altezza - lato - 8:
        rng = np.random.RandomState(seme)
        img[ny:ny + nh, nx:nx + nw, :] = rng.randint(0, 1024, (nh, nw, 3),
                                                     dtype=np.int64).astype(np.uint16)
        zone["rumore"] = {"y": ny, "x": nx, "h": nh, "w": nw, "seme": seme}
    else:
        zone["rumore"] = None

    return img, zone


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--giro", required=True,
                   help="l'etichetta del giro: e' il seme del rumore, e due "
                        "giri con la stessa etichetta hanno la STESSA scena")
    p.add_argument("--cartella", required=True)
    p.add_argument("--larghezza", type=int, default=1920)
    p.add_argument("--altezza", type=int, default=1080)
    a = p.parse_args()

    os.makedirs(a.cartella, exist_ok=True)
    img, zone = costruisci(a.larghezza, a.altezza, a.giro)

    base = os.path.join(a.cartella, "mira-" + a.giro)
    # ⛔ rgb48le: i valori a 10 bit portati IN ALTO (<<6), perche' e' cosi'
    #    che `ffmpeg -pix_fmt rgb48le` li legge.  Scriverli in basso
    #    significherebbe dare in pasto al codificatore un'immagine 64 volte
    #    piu' scura e poi accusare il codificatore.
    (img.astype(np.uint16) << 6).tofile(base + ".rgb48")
    try:
        from PIL import Image
        Image.fromarray((img >> 2).astype(np.uint8)).save(base + ".png")
    except Exception as e:                       # noqa: BLE001
        print("⚠ la copia a 8 bit da guardare non e' stata scritta: %s" % e,
              file=sys.stderr)

    meta = {
        "giro": a.giro, "larghezza": a.larghezza, "altezza": a.altezza,
        "profondita": 10, "spazio": "RGB lineare sui codici, senza gamma",
        "zone": zone,
        "impronta_rgb48": hashlib.sha256(open(base + ".rgb48", "rb").read()
                                         ).hexdigest()[:16],
    }
    with open(base + ".json", "w") as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)
    print(base + ".rgb48")
    print(base + ".json")


if __name__ == "__main__":
    main()
