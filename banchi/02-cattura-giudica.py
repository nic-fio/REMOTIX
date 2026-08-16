#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02-cattura-giudica.py — il giudice dei PIXEL della sotto-fase F2.2.

⛔ PERCHE' ESISTE — e non e' «un controllo in piu'»

Lo strumento della fase 0, `misura-cattura`, e' certificato e riproduce i 36 ± 2
fotogrammi di Mutter.  ⛔ Ma i pixel non li guarda mai: `su_processo` legge
`type`, `fd`, `chunk->stride`, il danno e la sequenza, e rimette il buffer in
coda senza toccare `piano->data`.

⇒ **Un fotogramma NERO E VALIDO passerebbe la fase 0 con il massimo dei voti.**
  36 al secondo, quattro buffer riciclati, danno parziale, zero salti: tutto
  verde, e sullo schermo il nulla.  ⛔ E il nero non e' teorico — `STUDI.md` §gnome §3.1:
  in headless `needs_outputs=false`, quindi senza `--virtual-monitor` la sessione
  parte **viva, completa e nera**; `PIANO.md`, fase 2: *«una sessione nera e
  perfettamente viva e' la cosa che si scambia per un difetto di cattura, e si
  cerca per mezza giornata dalla parte sbagliata»*.

Questo programma e' l'unica cosa del progetto che apre il fotogramma e guarda.

---------------------------------------------------------------------------
⛔ PERCHE' STA IN UN FILE SEPARATO DA CHI CATTURA

Perche' il guasto si possa innestare **nei pixel**.  Il produttore scrive un
`.raw` e un manifesto; il giudice li legge.  Fra i due si puo' infilare un
fotogramma nero della stessa identica misura, con lo stesso identico manifesto —
che e' esattamente il guasto peggiore di questa sotto-fase — senza toccare ne'
il produttore ne' il giudice.  ⭐ Un banco che non si puo' guastare non si puo'
certificare (`PIANO.md` §0.3 punto 4).

---------------------------------------------------------------------------
⛔ LA SCENA E' DICHIARATA, E LA FIRMA E' SCELTA PER SOPRAVVIVERE AL COLORE

`CODER.md` §3.2: la scena si dichiara e si muove sempre.  La fase 0 usava
`weston-simple-egl -f -o` — che si muove benissimo ma **nei pixel non e'
riconoscibile**: un triangolo che gira non ha una firma, e F2.6 (il confronto dei
pixel) non avrebbe niente da confrontare.

La scena di F2.2 e' quindi **«bandiera»**: le sette barre SMPTE a tutto schermo,
ferme, piu' un blocco bianco che scorre in basso a ogni fotogramma.

  | perche' le sette barre | una firma **ferma**, che sta nei pixel e non nel
  |                        | tempo: un'immagine ferma si giudica su di essa
  | perche' il blocco che  | Mutter consegna un fotogramma **solo se qualcosa
  | scorre                 | cambia** (`LEZIONI.md` §4 trappola 8). Senza il
  |                        | blocco, su un desktop fermo non arriverebbe nulla
  |                        | e lo zero sarebbe legittimo — ma inutile
  | perche' il blocco sta  | cosi' la firma **non dipende dall'istante** in cui
  | in un angolo           | il fotogramma e' stato preso, e due giri diversi si
  |                        | possono confrontare

⭐ E LA FIRMA NON E' UN ELENCO DI COLORI ASSOLUTI, di proposito.  Fra ffmpeg,
mpv, il 4:2:0 e la matrice colore (601 contro 709) i valori RGB assoluti si
spostano di decine di unita', e un giudice che pretendesse `(191,191,0)` sarebbe
rosso su una scena perfetta.  Si controllano invece **tre proprieta' che nessuna
matrice colore puo' invertire**:

  F1  sette bande, ciascuna **uniforme al suo interno**
  F2  la **luminanza cala** da sinistra a destra su tutte e sette — e' il disegno
      stesso delle barre SMPTE, e vale sia con i pesi 601 sia con i 709
  F3  la **firma dei canali** di ciascuna banda (quale canale domina): grigio,
      giallo, ciano, verde, magenta, rosso, blu

⛔ Un fotogramma nero fallisce tutte e tre.  Un grigio uniforme fallisce F2 e F3
   ma **passa F1**: ed e' apposta, perche' e' cosi' che si distingue «nero» da
   «non e' la scena» da «e' la scena».  Tre esiti, non due.

---------------------------------------------------------------------------
⛔ ZERO NON E' FALLIMENTO (`REVIEWER.md` §1 punto 4)

  uscita 0  verde: il fotogramma c'e', e' quello chiesto, e contiene la scena
  uscita 1  rosso: c'e' un fotogramma e qualcosa non torna. La marca dice cosa
  uscita 3  ⭐ non c'e' niente da giudicare — zero fotogrammi, dichiarato tale
            dal produttore. E' un risultato, non un guasto
  uscita 2  il GIUDICE e' fallito: file illeggibile, manifesto storto, oppure
            ⛔ **il controllo positivo in coda non e' passato** — nel qual caso
            questo programma si dichiara NON CERTIFICATO e non giudica nulla

---------------------------------------------------------------------------
⛔ IL CONTROLLO POSITIVO GIRA A OGNI ESECUZIONE, IN CODA

`LEZIONI.md` §1.9, seconda regola: *«questo strumento sa trovare qualcosa che c'e'
di sicuro?»*.  Uno strumento che non ha mai trovato niente non e' pulito: e' non
certificato.  Alla fine di ogni giro il giudice fabbrica da se' tre fotogrammi e
si guarda addosso:

  la bandiera sintetica  → deve dire VERDE
  il nero pieno          → deve dire ROSSO con la marca FOTOGRAMMA NERO
  il grigio uniforme     → deve dire ROSSO con la marca SCENA NON RICONOSCIUTA
                            (⛔ e **non** FOTOGRAMMA NERO: se un giudice chiamasse
                             nero un grigio, la sua diagnosi peggiore sarebbe
                             sbagliata proprio nel caso in cui serve)

Se anche uno solo dei tre non risponde com'e' scritto qui sopra, il verdetto sul
fotogramma vero **non viene emesso**: esce 2.

---------------------------------------------------------------------------
uso:
  02-cattura-giudica.py --manifesto PREFISSO.json [--quale primo|regime|tutti]
                        [--scena bandiera|ignota] [--json USCITA.json]
  02-cattura-giudica.py --solo-controllo-positivo
"""

import argparse
import json
import math
import os
import sys
import time

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

# ── Le soglie, tutte in un posto e tutte con la ragione accanto ────────────
#
# ⛔ Si scrivono qui e non sparse nel codice perche' una soglia scelta dopo aver
#    visto il numero e' un atteso allargato finche' torna — la strada disonesta
#    che `01-b12-guasti.py` ha insegnato a non prendere.
SOGLIE = {
    # Sotto questa luminanza media (0-255) il fotogramma si chiama NERO.  Il
    # nero vero e' 0; si lascia margine per un nero non perfettamente nero (una
    # sessione che disegna uno sfondo scurissimo resta un guasto da vedere).
    "nero_luma_media": 8.0,
    # …e insieme: nessun pixel campionato oltre questa soglia.  Due condizioni,
    # non una: un fotogramma nero con un solo puntatore bianco non e' «nero»,
    # ed e' un'informazione diversa.
    "nero_luma_massima": 24.0,
    # Sotto questa deviazione standard su tutto il fotogramma campionato,
    # l'immagine e' UNIFORME (una tinta piatta).  Nero e uniforme sono due
    # marche diverse.
    "uniforme_scarto": 3.0,
    # Dentro una banda: scarto massimo ammesso su ciascun canale.  Il 4:2:0 e
    # il rumore di codifica sporcano, ma dentro una banda piena restano pochi
    # livelli.
    "banda_scarto": 12.0,
    # Fra due bande adiacenti: la luminanza deve calare almeno di tanto.  Il
    # salto piu' piccolo nelle barre SMPTE e' verde→magenta, ~33 livelli con i
    # pesi 601 e ~82 con i 709; 8 e' largo e resta molto sotto.
    "salto_luma": 8.0,
    # La firma dei canali: quanto un canale «dominante» deve staccare uno
    # «spento» perche' si possa dire che domina.
    "canale_stacco": 40.0,
    # Fra `primo` e `regime`: quanti pixel campionati devono differire perche'
    # si possa dire che il buffer e' cambiato davvero.
    "cambiato_frazione": 0.02,
}

# ⛔ LA FIRMA DELLE SETTE BARRE SMPTE, scritta PRIMA di guardare il fotogramma.
#
#    Per ciascuna banda: quali canali devono essere ALTI e quali BASSI.  Sono le
#    barre a 75 %: grigio, giallo, ciano, verde, magenta, rosso, blu.
#    ⚠ Il grigio non ha ne' alti ne' bassi: e' la banda in cui i tre canali
#      devono essere VICINI FRA LORO, ed e' un vincolo, non un'assenza.
BANDE = [
    ("grigio",  [],           [],          True),
    ("giallo",  ["R", "G"],   ["B"],       False),
    ("ciano",   ["G", "B"],   ["R"],       False),
    ("verde",   ["G"],        ["R", "B"],  False),
    ("magenta", ["R", "B"],   ["G"],       False),
    ("rosso",   ["R"],        ["G", "B"],  False),
    ("blu",     ["B"],        ["R", "G"],  False),
]

# Il pixel e' BGRx/BGRA a 32 bit — l'unico formato che Mutter consegna
# (`STUDI.md` §gnome §8.3: «Solo BGRx e BGRA», R32 confermata riga per riga).
BYTE_PER_PIXEL = 4

# ===========================================================================
# ⛔ QUALI MARCHE SONO ROSSE SU QUALE FOTOGRAMMA — e non e' un'indulgenza
#
# Il fotogramma `primo` e' preso PRIMA che la scena esista: e' il desktop nudo,
# appena montato il monitor virtuale.  Pretendere li' la scena dichiarata — o
# anche solo pretendere che non sia una tinta piatta — vorrebbe dire scrivere una
# prova che da' ROSSO su un banco perfettamente sano.  E' la voce 2 di
# `FASI.md` §00-ambiente: *«la prova dell'headless cercava una frase che, se tutto
# va bene, non compare mai»* — su una sessione sana avrebbe dato rosso per
# sempre.  Uno sfondo GNOME a tinta unita e' plausibile, e non e' un difetto.
#
# ⭐ MA IL NERO SU `primo` RESTA ROSSO, ed e' il punto: un desktop nudo NERO e'
#    la firma esatta della sessione senza monitor virtuale — viva, completa e
#    nera (`STUDI.md` §gnome §3.1, prova M9 di §13).  E' il guasto che questa sotto-fase
#    esiste per vedere, e sul `primo` si vede prima che altrove.
MARCHE_ROSSE = {
    "primo":  {"FOTOGRAMMA NERO", "BYTE NON TORNANO",
               "MISURA DIVERSA DA QUELLA CHIESTA", "FILE ASSENTE"},
    # Sul `regime` la scena e' dichiarata viva: li' tutto conta.
    "regime": None,   # None = tutte
}


# ===========================================================================
#  La lettura: si legge POCO, e per righe
# ===========================================================================
def luma(r, g, b):
    """Rec.601.  ⚠ La scelta della matrice NON conta per quel che si controlla:
    l'ordine decrescente delle sette barre vale sia con i pesi 601 sia con i
    709 — e' proprio il disegno delle barre.  Si sceglie una e la si dichiara."""
    return 0.299 * r + 0.587 * g + 0.114 * b


class Fotogramma:
    """Un `.raw` come PipeWire l'ha consegnato: righe di `stride` byte, BGRx."""

    def __init__(self, percorso, larghezza, altezza, stride, colore):
        self.percorso = percorso
        self.larghezza = larghezza
        self.altezza = altezza
        self.stride = stride
        self.colore = colore
        self.byte = os.path.getsize(percorso)
        self.f = open(percorso, "rb")
        self._righe = {}

    def chiudi(self):
        self.f.close()

    def riga(self, y):
        if y not in self._righe:
            self.f.seek(y * self.stride)
            self._righe[y] = self.f.read(self.stride)
        return self._righe[y]

    def pixel(self, x, y):
        """Restituisce (R, G, B).  ⛔ L'ordine dei byte e' BGRx: B, G, R, x."""
        r = self.riga(y)
        i = x * BYTE_PER_PIXEL
        if i + 3 > len(r):
            return None
        return (r[i + 2], r[i + 1], r[i])


def campiona_griglia(fg, passo_x=24, passo_y=24):
    """Un reticolo su tutto il fotogramma: serve al nero e all'uniforme.

    ⚠ Si campiona invece di leggere tutto: a 1920×1080 il file e' 8 MB, e
      leggerlo intero in Python a ogni giro renderebbe il banco lento senza
      rispondere a una domanda in piu'.  Il reticolo di ~3600 punti copre ogni
      riquadro di 24×24 px: un fotogramma nero non ha nessun posto in cui
      nascondersi."""
    punti = []
    y = 0
    while y < fg.altezza:
        x = 0
        riga = fg.riga(y)
        while x < fg.larghezza:
            i = x * BYTE_PER_PIXEL
            if i + 3 <= len(riga):
                punti.append((riga[i + 2], riga[i + 1], riga[i]))
            x += passo_x
        y += passo_y
    return punti


def media_e_scarto(valori):
    if not valori:
        return 0.0, 0.0
    m = sum(valori) / len(valori)
    v = sum((x - m) ** 2 for x in valori) / len(valori)
    return m, math.sqrt(v)


# ===========================================================================
#  I controlli
# ===========================================================================
def controlla_nero(fg, rilievi, misure):
    punti = campiona_griglia(fg)
    if not punti:
        rilievi.append(("BYTE NON TORNANO",
                        "il reticolo non ha trovato nemmeno un pixel leggibile: "
                        "stride o altezza non combaciano con i byte del file"))
        return
    lume = [luma(*p) for p in punti]
    media, scarto = media_e_scarto(lume)
    massima = max(lume)
    misure["luma_media"] = round(media, 2)
    misure["luma_massima"] = round(massima, 2)
    misure["luma_scarto"] = round(scarto, 2)
    misure["punti_campionati"] = len(punti)

    if media <= SOGLIE["nero_luma_media"] and massima <= SOGLIE["nero_luma_massima"]:
        rilievi.append(("FOTOGRAMMA NERO",
                        "luminanza media %.2f (soglia %.1f) e massima %.2f (soglia %.1f) "
                        "su %d punti: il fotogramma e' valido e non contiene nulla. "
                        "E' il guasto peggiore di F2.2 — STUDI.md §gnome §3.1, sessione viva, "
                        "completa e nera"
                        % (media, SOGLIE["nero_luma_media"], massima,
                           SOGLIE["nero_luma_massima"], len(punti))))
        return
    if scarto <= SOGLIE["uniforme_scarto"]:
        rilievi.append(("FOTOGRAMMA UNIFORME",
                        "scarto della luminanza %.2f (soglia %.1f) su %d punti: una tinta "
                        "piatta, non nera. ⚠ Non e' «nero», ed e' una diagnosi diversa: "
                        "un buffer mai dipinto, o riempito di grigio"
                        % (scarto, SOGLIE["uniforme_scarto"], len(punti))))


def misura_profondita(fg, misure):
    """⛔ I BIT VERI SI CONTANO, non si leggono sull'etichetta.

    Chiesto da F2.3 (la codifica) come **cucitura**, e il guasto che ci sta
    dietro e' quello che F2.3 chiama **F2.3-A**:

      *se la cattura consegna 8 bit, tutta la catena resta verde e l'etichetta
      continua a dire Main10.*  ⛔ Nessuno se ne accorge guardando l'immagine,
      perche' viene bene lo stesso.

    Il numero che lo smaschera, `[M]` da F2.3: **877 livelli distinti e 0,25 di
    multipli di 4** su un fotogramma a 10 bit veri, contro **220 livelli e
    1,000** su uno passato per 8 bit.

    ⭐ Qui il conto si fa **gia' alla cattura**, cosi' il difetto ha un imputato
       PRIMA di entrare nel codificatore.  ⚠ E con una differenza che va detta:
       il buffer di Mutter e' BGRx a **8 bit per canale** (`STUDI.md` §gnome §8.3 `[R]`),
       quindi i livelli qui si contano su 256 e non su 1024.  La domanda che
       questo conto risponde non e' «sono dieci bit?» — la risposta e' no per
       costruzione — ma **«sono almeno otto bit veri, o e' un percorso piu'
       povero promosso?»**.  Un canale che prendesse solo 64 valori distinti,
       tutti multipli di 4, sarebbe un percorso a 6 bit sotto un'etichetta a 8.
    """
    punti = campiona_griglia(fg, 8, 8)
    if not punti:
        return
    for i, canale in enumerate(("R", "G", "B")):
        v = [p[i] for p in punti]
        distinti = sorted(set(v))
        misure.setdefault("profondita", {})[canale] = {
            "minimo": min(v),
            "massimo": max(v),
            "livelli_distinti": len(distinti),
            "livelli_possibili": 256,
            "frazione_multipli_di_2": round(sum(1 for x in v if x % 2 == 0) / len(v), 3),
            "frazione_multipli_di_4": round(sum(1 for x in v if x % 4 == 0) / len(v), 3),
            "frazione_multipli_di_8": round(sum(1 for x in v if x % 8 == 0) / len(v), 3),
        }
    misure["profondita"]["campioni"] = len(punti)
    misure["profondita"]["⚠ come si legge"] = (
        "il conto dei livelli distinti su TUTTO il fotogramma dipende dalla scena: "
        "sette barre piatte ne hanno una ventina per costruzione, e li' un numero "
        "basso non dice niente sui bit. Il conto che vuol dire qualcosa e' quello "
        "sulla SFUMATURA (profondita_sfumatura), che attraversa tutti i 256 livelli.")
    # ⛔ E IL RANGE SI MISURA, non si assume — anche quando il produttore lo
    #    dichiara.  Se tutti e tre i canali stessero dentro 16-235 su una scena
    #    che arriva a 0 e a 255, qualcuno lungo la strada avrebbe applicato un
    #    range limitato senza dirlo.  ⚠ Non e' un rosso: e' una misura, e
    #    dipende dalla scena.  Si scrive, e chi la legge sa cosa guarda.
    mn = min(misure["profondita"][c]["minimo"] for c in "RGB")
    mx = max(misure["profondita"][c]["massimo"] for c in "RGB")
    misure["profondita"]["range_misurato"] = (
        "sospetto LIMITATO (nessun canale sotto 16 ne' sopra 235)"
        if mn >= 16 and mx <= 235 else "compatibile con PIENO (min %d, max %d)" % (mn, mx))


def misura_profondita_sfumatura(fg, misure):
    """⭐ IL CONTO DEI BIT SI FA DOVE I BIT SI VEDONO: sulla sfumatura.

    La scena «bandiera» porta, sotto le barre, una **rampa da nero a bianco larga
    tutto lo schermo**: 1920 px per 256 livelli, cioe' ogni livello ripetuto ~7,5
    volte.  ⛔ E' l'unica parte dell'immagine su cui «quanti livelli distinti» sia
    una domanda sui BIT e non sulla scena.

    Il guasto che questo numero smaschera e' **F2.3-A**: se la catena passa da 8
    bit e l'etichetta dice Main10, l'immagine viene bene lo stesso e tutto resta
    verde.  Il numero di F2.3, `[M]`: **877 livelli distinti e 0,25 di multipli di
    4** a 10 bit veri, contro **220 e 1,000** dopo un passaggio a 8 bit.

    ⚠ Qui il fondo scala e' 256 e non 1024, perche' il buffer di Mutter e' BGRx
      (`STUDI.md` §gnome §8.3 `[R]`).  Quindi la domanda a cui questo conto risponde e'
      **«sono almeno otto bit veri?»** — l'atteso e' ~256 livelli distinti e una
      frazione di multipli di 4 vicina a 0,25.  ⛔ Una frazione di multipli di 4
      pari a 1,000 direbbe che qualcuno lungo la strada e' passato per 6 bit.
    """
    y0 = int(fg.altezza) - 240
    y1 = int(fg.altezza) - 150
    if y0 < 0:
        return
    v = {"R": [], "G": [], "B": []}
    y = y0
    while y < y1 and y < fg.altezza:
        riga = fg.riga(y)
        x = 0
        while x < fg.larghezza:
            i = x * BYTE_PER_PIXEL
            if i + 3 <= len(riga):
                v["R"].append(riga[i + 2])
                v["G"].append(riga[i + 1])
                v["B"].append(riga[i])
            x += 2
        y += 10
    if not v["R"]:
        return
    d = {"riga_da": y0, "riga_a": y1, "campioni": len(v["R"])}
    for c in "RGB":
        d[c] = {
            "minimo": min(v[c]), "massimo": max(v[c]),
            "livelli_distinti": len(set(v[c])),
            "livelli_possibili": 256,
            "frazione_multipli_di_4": round(
                sum(1 for x in v[c] if x % 4 == 0) / len(v[c]), 3),
        }
    d["⚠ per F2.3"] = (
        "atteso su 8 bit veri: livelli distinti vicini a 256 e multipli di 4 "
        "vicini a 0,25. Una frazione di 1,000 direbbe che la strada e' passata "
        "per meno bit di quelli che l'etichetta dichiara — e' F2.3-A visto "
        "gia' alla cattura.")
    misure["profondita_sfumatura"] = d


def controlla_byte(fg, atteso_larghezza, atteso_altezza, rilievi, misure):
    """⛔ I byte devono tornare con lo stride DICHIARATO, non con larghezza*4.

    `cattura.h` di v1, prima riga: *«lo stride si legge dal chunk del buffer, mai
    calcolato come larghezza*4. Il produttore allinea le righe come gli conviene,
    e dedurlo produce immagini oblique»*.  Qui non si deduce: si confronta quel
    che il produttore ha dichiarato con i byte che ci sono."""
    minimo = fg.larghezza * BYTE_PER_PIXEL
    atteso = fg.stride * fg.altezza
    misure["byte_nel_file"] = fg.byte
    misure["byte_attesi_stride_per_altezza"] = atteso
    misure["stride_dichiarato"] = fg.stride
    misure["stride_minimo_larghezza_per_4"] = minimo

    if fg.stride < minimo:
        rilievi.append(("BYTE NON TORNANO",
                        "stride dichiarato %d, ma servono almeno %d byte per una riga di "
                        "%d pixel a 32 bit" % (fg.stride, minimo, fg.larghezza)))
    if fg.byte < atteso:
        rilievi.append(("BYTE NON TORNANO",
                        "il file ha %d byte, ne servono %d (stride %d × altezza %d): "
                        "il fotogramma e' TRONCATO" % (fg.byte, atteso, fg.stride, fg.altezza)))
    elif fg.byte > atteso:
        misure["byte_in_piu"] = fg.byte - atteso

    if atteso_larghezza and (fg.larghezza != atteso_larghezza or fg.altezza != atteso_altezza):
        rilievi.append(("MISURA DIVERSA DA QUELLA CHIESTA",
                        "chiesti %d×%d, negoziati %d×%d. ⛔ Su Mutter e' un guasto: il "
                        "monitor virtuale si chiede e lui lo fa della misura chiesta "
                        "(cattura.h, `misura_negoziabile` FALSO). Su KWin sarebbe la "
                        "risposta normale — ed e' per questo che le due colonne stanno "
                        "separate invece di essere confrontate a mente"
                        % (atteso_larghezza, atteso_altezza, fg.larghezza, fg.altezza)))


def leggi_bande(fg):
    """Legge le sette bande sulla riga di firma e restituisce le loro misure."""
    y = int(fg.altezza * 0.25)          # dentro la zona delle sette barre
    larghezza_banda = fg.larghezza / 7.0
    bande = []
    for i in range(7):
        # ⛔ Si campiona il CUORE della banda, non il bordo: il 4:2:0 sfuma i
        #    passaggi su due pixel per lato, e un campione sul bordo misurerebbe
        #    la sfumatura invece della banda.
        x0 = int(i * larghezza_banda + larghezza_banda * 0.25)
        x1 = int(i * larghezza_banda + larghezza_banda * 0.75)
        erre, gi, bi = [], [], []
        for x in range(x0, x1, 3):
            p = fg.pixel(x, y)
            if p:
                erre.append(p[0])
                gi.append(p[1])
                bi.append(p[2])
        mr, sr = media_e_scarto(erre)
        mg, sg = media_e_scarto(gi)
        mb, sb = media_e_scarto(bi)
        bande.append({
            "riga": y, "da_x": x0, "a_x": x1, "campioni": len(erre),
            "R": round(mr, 1), "G": round(mg, 1), "B": round(mb, 1),
            "scarto_max": round(max(sr, sg, sb), 2),
            "luma": round(luma(mr, mg, mb), 1),
        })
    return bande


def controlla_firma(fg, rilievi, misure):
    bande = leggi_bande(fg)
    misure["bande"] = bande
    if any(b["campioni"] == 0 for b in bande):
        rilievi.append(("SCENA NON RICONOSCIUTA",
                        "una banda non ha nemmeno un campione: la riga di firma non si legge"))
        return

    # F1 — ciascuna banda uniforme al suo interno
    sporche = [(i, b["scarto_max"]) for i, b in enumerate(bande)
               if b["scarto_max"] > SOGLIE["banda_scarto"]]
    # F2 — la luminanza cala da sinistra a destra
    salti = [round(bande[i]["luma"] - bande[i + 1]["luma"], 1) for i in range(6)]
    misure["salti_luma"] = salti
    non_cala = [i for i, s in enumerate(salti) if s < SOGLIE["salto_luma"]]
    # F3 — la firma dei canali
    sbagliate = []
    for i, (nome, alti, bassi, vicini) in enumerate(BANDE):
        b = bande[i]
        val = {"R": b["R"], "G": b["G"], "B": b["B"]}
        if vicini:
            if max(val.values()) - min(val.values()) > SOGLIE["canale_stacco"]:
                sbagliate.append((nome, "i tre canali dovrebbero essere vicini: %s" % val))
            continue
        piu_basso_alto = min(val[c] for c in alti)
        piu_alto_basso = max(val[c] for c in bassi)
        if piu_basso_alto - piu_alto_basso < SOGLIE["canale_stacco"]:
            sbagliate.append((nome, "%s dovrebbero dominare su %s, e invece %s"
                              % ("+".join(alti), "+".join(bassi), val)))

    if sporche or non_cala or sbagliate:
        motivi = []
        if sporche:
            motivi.append("F1 — bande non uniformi: %s" % sporche)
        if non_cala:
            motivi.append("F2 — la luminanza non cala fra le bande %s (salti %s, soglia %.1f)"
                          % ([(i, i + 1) for i in non_cala], salti, SOGLIE["salto_luma"]))
        if sbagliate:
            motivi.append("F3 — firma dei canali: %s" % sbagliate)
        rilievi.append(("SCENA NON RICONOSCIUTA",
                        "il fotogramma non e' nero ma non e' la scena dichiarata «bandiera». "
                        + " · ".join(motivi)))


def controlla_cambiato(a, b, rilievi, misure):
    """⛔ `primo` e `regime` devono essere DIVERSI.

    Se fossero identici, il produttore ci starebbe restituendo lo stesso buffer
    due volte — ed e' la forma esatta della trappola 8 di `LEZIONI.md` §4: chi si
    collega a un desktop fermo resta al nero finche' non si muove qualcosa, e la
    schermata vecchia ha lo stesso aspetto di una nuova."""
    pa = campiona_griglia(a)
    pb = campiona_griglia(b)
    n = min(len(pa), len(pb))
    if n == 0:
        return
    diversi = sum(1 for i in range(n) if pa[i] != pb[i])
    frazione = diversi / n
    misure["punti_campionati"] = n
    misure["punti_diversi_fra_primo_e_regime"] = diversi
    misure["frazione_diversa"] = round(frazione, 4)
    if frazione < SOGLIE["cambiato_frazione"]:
        rilievi.append(("IL BUFFER NON E' CAMBIATO",
                        "fra `primo` e `regime` solo %d punti su %d differiscono (%.2f %%, "
                        "soglia %.2f %%): il produttore potrebbe averci restituito lo stesso "
                        "buffer, e una schermata vecchia ha lo stesso aspetto di una nuova"
                        % (diversi, n, frazione * 100, SOGLIE["cambiato_frazione"] * 100)))


# ===========================================================================
#  Il giudizio di un fotogramma
# ===========================================================================
def giudica_uno(percorso, larghezza, altezza, stride, colore, scena,
                chiesto_larghezza, chiesto_altezza):
    rilievi, misure = [], {}
    if not os.path.exists(percorso):
        return [("FILE ASSENTE", "non c'e' nessun file da giudicare: %s" % percorso)], misure, None
    fg = Fotogramma(percorso, larghezza, altezza, stride, colore)
    controlla_byte(fg, chiesto_larghezza, chiesto_altezza, rilievi, misure)
    misura_profondita(fg, misure)
    if scena == "bandiera":
        misura_profondita_sfumatura(fg, misure)
    controlla_nero(fg, rilievi, misure)
    # ⛔ La firma si controlla SOLO se il fotogramma non e' gia' nero o uniforme:
    #    su un nero fallirebbe anche lei, e tre marche per una causa sola fanno
    #    sembrare tre difetti quel che ne e' uno.
    marche = [m for m, _ in rilievi]
    if scena == "bandiera" and "FOTOGRAMMA NERO" not in marche:
        controlla_firma(fg, rilievi, misure)
    elif scena != "bandiera":
        misure["firma"] = "non controllata: scena «%s», nessuna firma dichiarata" % scena
    return rilievi, misure, fg


# ===========================================================================
#  ⛔ IL CONTROLLO POSITIVO — gira in coda a OGNI esecuzione
# ===========================================================================
def fabbrica(percorso, larghezza, altezza, stride, che):
    """Fabbrica un `.raw` BGRx: «bandiera», «nero» o «grigio»."""
    colori = [(191, 191, 191), (191, 191, 0), (0, 191, 191), (0, 191, 0),
              (191, 0, 191), (191, 0, 0), (0, 0, 191)]
    with open(percorso, "wb") as f:
        for y in range(altezza):
            riga = bytearray(stride)
            for x in range(larghezza):
                if che == "nero":
                    r = g = b = 0
                elif che == "grigio":
                    r = g = b = 128
                else:
                    r, g, b = colori[min(6, x * 7 // larghezza)]
                i = x * BYTE_PER_PIXEL
                riga[i] = b
                riga[i + 1] = g
                riga[i + 2] = r
                riga[i + 3] = 255
            f.write(riga)


def controllo_positivo(cartella, righe):
    """⛔ Lo strumento sa trovare qualcosa che c'e' di sicuro, e sa NON trovarlo?

    Tre prove, e l'atteso di ciascuna e' scritto qui sopra, non dopo il giro.
    ⚠ Si usa un fotogramma piccolo (280×140): la fabbrica e' in Python puro e a
      1920×1080 costerebbe secondi a ogni esecuzione, senza rispondere a una
      domanda in piu' — la firma sta nelle proporzioni, non nella misura."""
    L, A = 280, 140
    S = L * BYTE_PER_PIXEL
    #  nome                che        marche PRETESE          marche VIETATE
    prove = [
        ("bandiera sintetica", "bandiera", [],                        ["FOTOGRAMMA NERO",
                                                                       "SCENA NON RICONOSCIUTA",
                                                                       "FOTOGRAMMA UNIFORME",
                                                                       "BYTE NON TORNANO"]),
        ("nero pieno",         "nero",     ["FOTOGRAMMA NERO"],       []),
        # ⛔ LA PROVA CHE VALE DOPPIO, e la colonna «vietate» e' la meta' che
        #    conta: un giudice che chiamasse NERO un grigio sbaglierebbe la sua
        #    diagnosi peggiore proprio nel caso in cui serve.  Pretendere solo
        #    «dice qualcosa di rosso» non lo distinguerebbe.
        ("grigio uniforme",    "grigio",   ["SCENA NON RICONOSCIUTA",
                                            "FOTOGRAMMA UNIFORME"],   ["FOTOGRAMMA NERO"]),
    ]
    tutto_bene = True
    for nome, che, pretese, vietate in prove:
        p = os.path.join(cartella, "controllo-positivo-%s.raw" % che)
        fabbrica(p, L, A, S, che)
        rilievi, misure, fg = giudica_uno(p, L, A, S, "BGRx", "bandiera", L, A)
        if fg:
            fg.chiudi()
        os.unlink(p)
        marche = [m for m, _ in rilievi]
        mancano = [m for m in pretese if m not in marche]
        di_troppo = [m for m in vietate if m in marche]
        ok = not mancano and not di_troppo
        detto = "detto %s" % (marche or "verde")
        if mancano:
            detto += " ⛔ mancano %s" % mancano
        if di_troppo:
            detto += " ⛔ di troppo %s" % di_troppo
        righe.append(("  controllo positivo — %s" % nome,
                      "atteso %s / vietate %s, %s"
                      % (pretese or "verde", vietate or "—", detto), ok))
        tutto_bene = tutto_bene and ok
    return tutto_bene


# ===========================================================================
def main():
    a = argparse.ArgumentParser(add_help=True)
    a.add_argument("--manifesto")
    a.add_argument("--quale", default="tutti", choices=["primo", "regime", "tutti"])
    a.add_argument("--scena", default="bandiera")
    a.add_argument("--json")
    a.add_argument("--solo-controllo-positivo", action="store_true")
    o = a.parse_args()

    cartella = os.path.dirname(os.path.abspath(o.manifesto)) if o.manifesto else "."
    righe_cp = []

    if o.solo_controllo_positivo:
        ok = controllo_positivo(cartella, righe_cp)
        for t, d, buono in righe_cp:
            print("%s%s%s  %s — %s" % (VERDE if buono else ROSSO, "OK" if buono else "NO",
                                       GRIGIO, t.strip(), d))
        return 0 if ok else 2

    if not o.manifesto:
        print("⛔ serve --manifesto PREFISSO.json", file=sys.stderr)
        return 2

    try:
        with open(o.manifesto) as f:
            man = json.load(f)
    except Exception as e:
        print("⛔ il manifesto non si legge: %s" % e, file=sys.stderr)
        return 2

    verdetto = {
        "giudice": "02-cattura-giudica.py",
        "quando_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "manifesto": o.manifesto,
        "etichetta": man.get("etichetta"),
        "scena": o.scena,
        "esito_del_produttore": man.get("esito"),
        "fotogrammi": {},
    }

    print("\n\033[1m== il giudizio dei pixel — %s ==\033[0m" % man.get("etichetta"))
    print("   produttore: %s (uscita %s)" % (man.get("esito"), man.get("uscita")))

    # ⛔ ZERO NON E' FALLIMENTO, e qui e' il punto in cui si separano.
    if man.get("uscita") == 3 or man.get("esito") == "ZERO FOTOGRAMMI":
        print("%s--%s  ZERO FOTOGRAMMI: non c'e' niente da giudicare, e non e' un rosso.\n"
              "      Il flusso e' stato attivo per tutta la presa e il desktop non e'\n"
              "      cambiato: su Mutter e' il comportamento dichiarato (LEZIONI.md §4\n"
              "      trappola 8), non un guasto. ⚠ Ma con una scena dichiarata VIVA e'\n"
              "      un'informazione pesante: vuol dire che la scena non dipingeva."
              % (GIALLO, GRIGIO))
        verdetto["verdetto"] = "ZERO FOTOGRAMMI"
        codice = 3
        rilievi_tutti = []
    elif str(man.get("esito", "")).startswith("TIPO DICHIARATO"):
        print("%s--%s  strada DMA-BUF: il tipo di buffer e' dichiarato, i pixel NON si\n"
              "      leggono da qui (il descrittore vive sulla scheda). Questo giro\n"
              "      risponde a «di che tipo e' il buffer», non a «cosa c'e' dentro»."
              % (GIALLO, GRIGIO))
        verdetto["verdetto"] = "SOLO IL TIPO"
        codice = 3
        rilievi_tutti = []
    else:
        neg = man.get("negoziato", {})
        chi = man.get("chiesto", {})
        larghezza = neg.get("larghezza") or chi.get("larghezza")
        altezza = neg.get("altezza") or chi.get("altezza")
        colore = neg.get("colore", "?")

        # ⛔ IL TIPO DI BUFFER SI RIPORTA CON CHI LO DICE, mai dedotto.
        buf = man.get("buffer", {})
        print("   buffer:     tipi visti %s · distinti riciclati %s"
              % (buf.get("tipi_visti"), buf.get("distinti_riciclati")))
        print("               chi lo dice: %s" % buf.get("chi_lo_dice"))
        print("   negoziato:  %s×%s %s, modificatore %s"
              % (larghezza, altezza, colore, neg.get("modificatore")))
        print("   chiesto:    %s×%s %s, strada %s"
              % (chi.get("larghezza"), chi.get("altezza"), chi.get("colore"), chi.get("strada")))
        # ⛔ LE TRE COSE CHE F2.3 CHIEDE DICHIARATE si stampano PRIMA dei
        #    pixel: chi legge questo giro deve vederle senza cercarle.
        cons = man.get("consegna_a_F2_3", {})
        if cons:
            print("\n   \033[1m── quel che si consegna a F2.3, dichiarato ──\033[0m")
            print("      bit per canale: %s   (%s)"
                  % (cons.get("bit_per_canale"), cons.get("bit_per_canale_chi_lo_dice")))
            print("      range:          %s" % cons.get("range"))
            print("      matrice:        %s" % cons.get("matrice"))
            print("      trasferimento:  %s" % cons.get("trasferimento"))
            print("      primari:        %s" % cons.get("primari"))
            print("      %s" % cons.get("⛔ F2.3-A"))
            print("      %s" % cons.get("⚠ sulla matrice"))
        for av in man.get("avvertenze", []):
            print("   %s" % av)

        rilievi_tutti = []
        quali = ["primo", "regime"] if o.quale == "tutti" else [o.quale]
        letti = {}
        for q in quali:
            f = man.get(q)
            if not f and q == "regime" and o.scena == "fermo":
                # ⭐ SULLA SCENA «fermo» L'ATTESO E' ROVESCIATO, e va detto qui.
                #
                # `fermo` e' il CASO OPPOSTO dichiarato: nessuno dipinge, e su
                # Mutter un fotogramma arriva **solo se qualcosa cambia**
                # (`LEZIONI.md` §4 trappola 8).  ⇒ Qui l'assenza del `regime` e'
                # la risposta giusta, non un rilievo: chiamarla rossa vorrebbe
                # dire scrivere una prova che da' rosso su un banco sano — la
                # voce 2 di `FASI.md` §00-ambiente.
                #
                # ⛔ E il rovescio e' un rilievo vero: se sulla scena `fermo`
                #    ARRIVASSE un fotogramma di regime, vorrebbe dire che sullo
                #    schermo si muove qualcosa che non abbiamo dichiarato — e
                #    ogni misura fatta su quello schermo misurerebbe anche
                #    quello.
                print("%s--%s  ⭐ scena «fermo»: il «regime» NON c'e', ed e' l'ATTESO.\n"
                      "      Nessuno dipingeva, e Mutter consegna solo quando qualcosa\n"
                      "      cambia. E' lo zero legittimo della trappola 8, non un rosso."
                      % (GIALLO, GRIGIO))
                verdetto["zero_legittimo_confermato"] = True
                continue
            if f and q == "regime" and o.scena == "fermo":
                rilievi_tutti.append((q, "QUALCOSA SI MUOVEVA E NON L'ABBIAMO DICHIARATO",
                                      "sulla scena «fermo» non doveva arrivare nessun "
                                      "fotogramma di regime, e ne e' arrivato uno: sullo "
                                      "schermo si muove qualcosa che il banco non conosce, "
                                      "e ogni misura su quello schermo misura anche quello"))
                print("%sNO%s  ⛔ sulla scena «fermo» e' arrivato un fotogramma di regime"
                      % (ROSSO, GRIGIO))
            if not f:
                # ⛔ «NON C'E'» NON E' «VA BENE» — e questo giudice ci e' cascato.
                #
                # Il 12 agosto 2026, al primo giro vero, il produttore ha preso
                # solo il fotogramma `primo` (la scena dipingeva su un altro
                # schermo) e questo giudice ha stampato una riga gialla e ha
                # concluso **VERDE**.  Un banco verde col difetto vivo e' la
                # peggiore delle prove, perche' da' fiducia (`CODER.md` §4.6).
                #
                # E' la forma E8: il silenzio scambiato per zero.  Il fotogramma
                # che manca e' quello che RISPONDE alla domanda di F2.2 — e
                # senza di lui non c'e' nessun verde da dare.
                rilievi_tutti.append((q, "IL FOTOGRAMMA MANCA",
                                      "il produttore non ha preso «%s». Se manca il "
                                      "«regime», non c'e' nessun fotogramma con la scena "
                                      "dentro: il verde non si da'" % q))
                print("%sNO%s  ⛔ «%s» NON C'E' nel manifesto, e non e' un'assenza innocua: "
                      "e' la domanda di F2.2 rimasta senza risposta" % (ROSSO, GRIGIO, q))
                continue
            percorso = f["file"]
            if not os.path.isabs(percorso):
                percorso = os.path.join(cartella, percorso)
            rilievi, misure, fg = giudica_uno(percorso, larghezza, altezza, f["stride"], colore,
                                              o.scena if q == "regime" else "ignota",
                                              chi.get("larghezza"), chi.get("altezza"))
            # ⚠ La firma si pretende solo sul fotogramma di REGIME.  Il `primo`
            #   e' preso PRIMA che la scena esista — pretendere la bandiera li'
            #   sarebbe rosso su un banco che funziona, che e' la voce 2 di
            #   `FASI.md` §00-ambiente (una prova che cerca una frase che, se
            #   tutto va bene, non compare mai).
            misure["danno"] = f.get("danno")
            misure["seq"] = f.get("seq")
            misure["indice_fra_gli_arrivati"] = f.get("indice_fra_gli_arrivati")
            rosse_q = MARCHE_ROSSE.get(q)
            verdetto["fotogrammi"][q] = {
                "rilievi": [{"marca": m, "perche": d,
                             "rosso": rosse_q is None or m in rosse_q}
                            for m, d in rilievi],
                "misure": misure}
            letti[q] = fg
            print("\n   ── %s ── (danno %s, seq %s, fotogramma n° %s fra gli arrivati)"
                  % (q, f.get("danno"), f.get("seq"), f.get("indice_fra_gli_arrivati")))
            print("      luminanza media %s · massima %s · scarto %s su %s punti"
                  % (misure.get("luma_media"), misure.get("luma_massima"),
                     misure.get("luma_scarto"), misure.get("punti_campionati")))
            print("      byte %s (attesi %s = stride %s × altezza %s)"
                  % (misure.get("byte_nel_file"), misure.get("byte_attesi_stride_per_altezza"),
                     misure.get("stride_dichiarato"), altezza))
            pr = misure.get("profondita")
            if pr:
                print("      profondita' misurata su %d campioni — %s"
                      % (pr["campioni"], pr["range_misurato"]))
                for c in "RGB":
                    d = pr[c]
                    print("        %s  min %-4d max %-4d livelli distinti %-4d/256"
                          "  multipli di 2 %.3f · di 4 %.3f · di 8 %.3f"
                          % (c, d["minimo"], d["massimo"], d["livelli_distinti"],
                             d["frazione_multipli_di_2"], d["frazione_multipli_di_4"],
                             d["frazione_multipli_di_8"]))
            sf = misure.get("profondita_sfumatura")
            if sf:
                print("      ⭐ sulla SFUMATURA (righe %d-%d, %d campioni) — il conto che"
                      " vuol dire qualcosa sui bit:" % (sf["riga_da"], sf["riga_a"],
                                                        sf["campioni"]))
                for c in "RGB":
                    print("        %s  livelli distinti %-4d/256   multipli di 4 %.3f"
                          "   (atteso su 8 bit veri: ~256 e ~0,250)"
                          % (c, sf[c]["livelli_distinti"], sf[c]["frazione_multipli_di_4"]))
            if "bande" in misure:
                for nome, b in zip([n for n, _, _, _ in BANDE], misure["bande"]):
                    print("      %-8s R%-6.1f G%-6.1f B%-6.1f  luma %-6.1f  scarto %.2f"
                          % (nome, b["R"], b["G"], b["B"], b["luma"], b["scarto_max"]))
            rosse = MARCHE_ROSSE.get(q)
            for m, d in rilievi:
                # ⛔ Un avviso NON e' un rosso, e la differenza si stampa: due
                #    esiti sotto lo stesso colore sarebbero due misure sotto la
                #    stessa etichetta (forma E2).
                if rosse is None or m in rosse:
                    print("      %sNO%s  %s — %s" % (ROSSO, GRIGIO, m, d))
                    rilievi_tutti.append((q, m, d))
                else:
                    print("      %s⚠%s   %s — %s" % (GIALLO, GRIGIO, m, d))
                    print("            (avviso, non rosso: sul «%s» la scena non c'e'"
                          " ancora — vedi MARCHE_ROSSE)" % q)
            if not rilievi:
                print("      %sOK%s  nessun rilievo" % (VERDE, GRIGIO))

        # ⛔ E il confronto fra i due, che nessuno dei due da solo puo' dare.
        if letti.get("primo") and letti.get("regime"):
            rc, mc = [], {}
            controlla_cambiato(letti["primo"], letti["regime"], rc, mc)
            verdetto["confronto_primo_regime"] = {
                "rilievi": [{"marca": m, "perche": d} for m, d in rc], "misure": mc}
            print("\n   ── primo contro regime ──")
            print("      punti diversi %s su %s (%s %%)"
                  % (mc.get("punti_diversi_fra_primo_e_regime"),
                     mc.get("punti_campionati", "—"),
                     round((mc.get("frazione_diversa") or 0) * 100, 2)))
            for m, d in rc:
                print("      %sNO%s  %s — %s" % (ROSSO, GRIGIO, m, d))
                rilievi_tutti.append(("confronto", m, d))
            if not rc:
                print("      %sOK%s  il buffer e' cambiato: non e' una schermata vecchia"
                      % (VERDE, GRIGIO))

        # ⭐ E la risposta alla domanda che i documenti si contraddicono su:
        #    un fotogramma con danno PARZIALE e' comunque INTERO?
        reg = man.get("regime") or {}
        if reg.get("danno") == "parziale":
            firma_ok = not any(q == "regime" and m == "SCENA NON RICONOSCIUTA"
                               for q, m, _ in rilievi_tutti)
            nero = any(q == "regime" and m == "FOTOGRAMMA NERO" for q, m, _ in rilievi_tutti)
            verdetto["danno_parziale_ma_intero"] = bool(firma_ok and not nero)
            print("\n   ⭐ il fotogramma di regime porta danno PARZIALE e la scena %s"
                  % ("SI VEDE INTERA ⇒ il buffer e' intero (STUDI.md §gnome §8.1: blit dell'intero "
                     "framebuffer), non un diff (cattura.h di v1)"
                     if firma_ok and not nero else
                     "NON si vede intera ⇒ il sospetto va sul diff di cattura.h"))

        for fg in letti.values():
            if fg:
                fg.chiudi()
        codice = 1 if rilievi_tutti else 0
        verdetto["verdetto"] = "ROSSO" if rilievi_tutti else "VERDE"

    # ── ⛔ IL CONTROLLO POSITIVO, IN CODA A OGNI ESECUZIONE ────────────────
    print("\n\033[1m== il controllo positivo dello strumento ==\033[0m")
    ok_cp = controllo_positivo(cartella, righe_cp)
    for t, d, buono in righe_cp:
        print("%s%s%s%s — %s" % (VERDE if buono else ROSSO, t, GRIGIO, " OK" if buono else " NO", d))
    verdetto["controllo_positivo"] = {"passato": ok_cp,
                                      "prove": [{"prova": t.strip(), "esito": d, "ok": b}
                                                for t, d, b in righe_cp]}
    if not ok_cp:
        print("\n%s⛔ IL GIUDICE NON E' CERTIFICATO%s: il controllo positivo non e' passato.\n"
              "   Il verdetto sul fotogramma vero NON viene emesso — uno strumento che non\n"
              "   sa trovare quel che c'e' di sicuro non e' pulito, e' non certificato\n"
              "   (LEZIONI.md §1.9, seconda regola)." % (ROSSO, GRIGIO))
        verdetto["verdetto"] = "GIUDICE NON CERTIFICATO"
        codice = 2

    if o.json:
        with open(o.json, "w") as f:
            json.dump(verdetto, f, ensure_ascii=False, indent=1)

    print("\n\033[1mVERDETTO: %s\033[0m (uscita %d)" % (verdetto["verdetto"], codice))
    return codice


if __name__ == "__main__":
    sys.exit(main())
