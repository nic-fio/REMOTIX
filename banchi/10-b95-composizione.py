#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-b95-composizione — ⛔⛔ IL SOFFITTO DELLA **COMPOSIZIONE**, non della codifica.

═══════════════════════════════════════════════════════════════════════════
⭐⭐⭐ LA LEGGE — quel che questo banco ha trovato, in testa perche' e' la
      risposta alla domanda da cui dipende se il budget si puo' calcolare
      in anticipo
═══════════════════════════════════════════════════════════════════════════

  ⭐ `[M]` 24 agosto 2026 · i5-13500T · **Intel UHD 730 integrata** (`renderD128`,
     `i915`; la Radeon e' chiusa da udev) · terreno `10-b0` 21/21 · lucchetto
     della GPU in mano · scena `04-b30-scena --movimento pieno` a 1920×1080,
     che danneggia **tutta** la superficie a ogni fotogramma.

  LEGGE ................ rcs0 % = 0,12068 · cambio[Mpixel/s] − 0,842
  PENDENZA ............. 0,12068 % di `rcs0` per Mpixel/s composto
  INTERCETTA ........... −0,842 % (⭐ zero entro l'errore: passa per l'origine)
  ERRORE (rms) ......... 0,304 punti su 6 gradini · R² 0,99986
  FERRO ................ Intel UHD 730 integrata (i5-13500T), GT 1267-1374 MHz

═══════════════════════════════════════════════════════════════════════════
⭐⭐⭐⭐ E IL NUMERO CHE LA FASE CERCAVA: **il soffitto della composizione**
═══════════════════════════════════════════════════════════════════════════

  `[M]` **≈ 0,97 Gpixel/s** — rampa di desktop GNOME veri, `rcs0` a saturazione:

    | N  | `rcs0` | composto Mpixel/s | GT MHz | RC6 % |
    |----|--------|-------------------|--------|-------|
    |  1 |  14,59 |  124,4            | 1267   | 66,5  |
    |  6 |  89,53 |  746,3            | 1374   |  3,1  |
    | ⚠7 |  99,21 |  870,9            | 1454   |  0,0  |
    | ⭐8 |  99,71 |  **992,1**        | 1542   |  0,0  |
    | 11 |  99,53 |  957,7            | 1542   |  0,0  |

  ⭐ A saturazione la GT si INCHIODA a 1542-1550 MHz (RP0) e RC6 va a **0,0 %**:
    ⇒ il soffitto e' letto **al massimo dell'orologio**, e li' il §CLOCK non ha
    ambiguita' da togliere.  ⛔ La PENDENZA qui sopra invece vale a ~1350 MHz e
    NON si estrapola: 100 % / 0,12068 darebbe **835,6** Mpixel/s, e il ferro ne
    fa **992** perche' a saturazione va il **14 %** piu' veloce.  ⭐⭐ 992/835,6
    = 1,187 contro 1542/1342 = 1,149: **tornano entro il 3,3 %**, ed e' la
    conferma indipendente che `drm-engine-*` misura TEMPO × frequenza.

  ⛔⛔ **E IL COLLO E' QUESTO, NON IL CODIFICATORE**: 0,97 contro i **1,86
      Gpixel/s** del codificatore nudo (§6.2 del primo giro) ⇒ la composizione
      cede per prima, con un fattore **1,9**.
  ⭐ E il conto dei posti torna con quel che l'utente ha visto: a 1920×1080 e
    60 Hz un desktop che cambia tutto vale 124,4 Mpixel/s ⇒ **7,8 desktop**
    entrano nel soffitto, e `[M]` `rcs0` passa il 99 % **al settimo**.  ⇒ Sei
    stanno comodi — la stessa risposta di §6.5, per un'altra strada.

═══════════════════════════════════════════════════════════════════════════
⭐⭐⭐ DI CHI E' `rcs0` — la scomposizione, una sessione, 124,4 Mpixel/s
═══════════════════════════════════════════════════════════════════════════

  | padrone                         | motore   | `[M]`      | contesto     |
  |---------------------------------|----------|------------|--------------|
  | compositore + cattura           | `rcs0`   | **14,54 %**| GT 1337 MHz  |
  | compositore solo (nessuno collegato) | `rcs0` | 28,37 % | ⚠ GT 612 MHz |
  | ⭐ **conversione di colore**     | `rcs0`   | **0,00 %** | —            |
  | ⭐ **conversione di colore**     | `vecs0`  | **14,53 %**| GT 1337 MHz  |
  | codifica                        | `vcs`    | 8,47 % su **200** | GT 1337 |

  ⛔⛔ **LA CONVERSIONE DI COLORE DEL PRODOTTO NON STA SULLE EU.**  Il primo
      giro (§6.6) l'aveva trovata su `rcs0` con `vecs0` a **`0,00 s` in tutta la
      campagna**, e costava **−17 % di ritmo e il doppio dei watt** — ma quello
      era `ffmpeg` con `hwupload`, 8 MB per fotogramma dalla memoria di sistema.
      ⭐ Il prodotto importa un **dmabuf a copia zero**, e `[M]` la sua
      conversione costa **ZERO sul motore di rendering** e sta tutta sul
      **VEBOX**, che nella rampa sale 14,5 → 55,9 % (N=1 → N=5) e **non e' mai
      il collo**.  ⇒ Era il `[?]` starato di §6.6, ed e' chiuso.

  ⚠ **La CATTURA non si isola** se non per differenza, e la differenza qui sopra
    **non e' confrontabile**: le due letture sono a 612 e 1337 MHz, e il banco
    si RIFIUTA di sottrarle (fattore fino a 3,8, §CLOCK).  ⭐ Normalizzando per
    la frequenza — 28,37×612,5 = 17 376 contro 14,54×1337,5 = 19 449 %·MHz — la
    cattura varrebbe **+12 %** sul lavoro del compositore, ma e' un conto sotto
    il modello del §CLOCK, `[?]` non una misura diretta.

═══════════════════════════════════════════════════════════════════════════
⭐⭐⭐ E LA DOMANDA DA CUI DIPENDE SE IL BUDGET SI CALCOLA IN ANTICIPO
═══════════════════════════════════════════════════════════════════════════

  *«Il costo di composizione dipende da che cosa fa il desktop?»*

  ⛔ **Non e' proporzionale: c'e' un GRADINO.**  `[M]` due punti alla stessa
    frequenza (~1350 MHz), un solo desktop:

      finestra  640×496 →  19,0 Mpixel/s → `rcs0`  **8,13 %**
      schermo  1920×1080 → 124,4 Mpixel/s → `rcs0` **13,69 %** (normalizzato)

    ⇒ **6,5 volte** il cambiamento costa **1,68 volte**.  Due termini:

      rcs0 % ≈ **7,1 %** (fisso, per desktop che compone) + **0,053 %** per Mpixel/s

    ⇒ ⭐ Meta' del costo di un desktop che cambia tutto e' un **pedaggio fisso**
      per il solo essere un desktop vivo a 60 Hz.
  ⚠ `[?]` **Due punti soli, e presi in due fasi diverse**: la retta a cinque
    punti la da' il modo `ritmi`, e nel primo giro la «linea morta» della fase 9
    ha chiuso la sessione a meta' (vedi sotto).  ⛔ Chi cita i due coefficienti
    citi anche questa riga.
  ⭐ E i due risultati **non si contraddicono**: la rampa passa per l'origine
    perche' aggiunge desktop INTERI (7,1 + 0,053·124,4 = 13,7 % a testa, contro
    i 15,0 % misurati per gradino), mentre il gradino si vede solo cambiando
    quanto cambia **un** desktop.  Sono due domande diverse (`LEZIONI.md` §1.28).

  ⛔⛔ **E UN DIFETTO DI PRODOTTO, VISTO UNA SECONDA VOLTA**: `[M]` bastano
      **10 s** senza che il desktop cambi perche' la «linea morta» chiuda la
      sessione — `causa=silenzio silenzio_ms=10044 persi=0`, su una sessione
      sana che consegnava 60 commit/s e 5 524 B/fotogramma un attimo prima.
      ⇒ E' §6.3 del primo giro, e non era legato al desktop fermo: basta un
      buco fra due scene.  ⭐ Il banco NON spegne la cura per passare: toglie il
      buco (la scena nuova si accende prima che la vecchia muoia).

═══════════════════════════════════════════════════════════════════════════
⛔⛔ PERCHE' ESISTE, e la ragione e' che il primo giro ha misurato la cosa
     sbagliata benissimo
═══════════════════════════════════════════════════════════════════════════

Il primo giro della fase 10 ha misurato con cura il soffitto del **codificatore**
— `[M]` **1,86 Gpixel/s** in H.264, da due banchi indipendenti (`10-b88`, `10-b94`)
— e poi ha scoperto che ⛔ **non e' quello il collo**: con dieci desktop GNOME veri
dietro (`10-b92`), la macchina si ferma a **sei** sessioni ≈ 370 Mpixel/s, il
**20 %** di quel soffitto, e il motore **video non passa mai il 27 %**.  A saturare
e' `rcs0`, il motore di **rendering** (le EU).

⇒ Il budget che la fase deve scrivere **non e' un budget di codifica**: e' un
  budget di **composizione**.  E nessuno lo aveva mai misurato.

═══════════════════════════════════════════════════════════════════════════
⭐ CHE COSA QUESTO BANCO SEPARA, E CHE COSA NON PUO' SEPARARE
═══════════════════════════════════════════════════════════════════════════

`rcs0` e' **un motore solo** e ci lavorano piu' padroni insieme.  Il metro tarato
di `banchi/10-b87-metro-gpu.py` separa **per pid e per cliente DRM** — e' per
questo che esiste — quindi i padroni si distinguono cosi':

  | padrone                | dove si legge                                       |
  |------------------------|-----------------------------------------------------|
  | il **compositore**     | `drm-engine-render` del `gnome-shell` di quell'uid   |
  | la nostra **cattura**  | ⚠ **dentro lo stesso `gnome-shell`**: e' Mutter che  |
  |                        | consegna i fotogrammi a PipeWire.  ⇒ si isola SOLO   |
  |                        | come DIFFERENZA fra «collegato» e «scollegato»       |
  | la nostra **conversione** | `drm-engine-render` del figlio `remotix` di quell'uid |
  | la **codifica**        | `drm-engine-video` dello stesso figlio (⚠ i VDBOX    |
  |                        | sono DUE: il fondo scala e' 200 %, non 100)          |

⛔⛔ E I DUE GRADINI DI MEZZO NON SI POSSONO ISOLARE, e si dichiara invece di
     stimarli.  L'incarico chiedeva una scala a quattro gradini:
       1. desktop vivo, nessuno collegato;
       2. + collegato ma **senza codifica**;
       3. + cattura e conversione, **senza** codifica;
       4. + tutto.
     `[M]` I gradini **2 e 3 non esistono in questo prodotto**: `src/main.c` non
     ha nessun interruttore che accenda la sessione senza accendere il
     codificatore (le opzioni sono state contate: nessuna la nomina), e il
     figlio costruisce cattura, conversione e codifica in un tratto solo.
     ⇒ Il banco fa **due gradini veri** (1 e 4) e ricava i quattro padroni
       dall'attribuzione **per pid e per motore**, che e' piu' fine della
       differenza fra gradini: ogni padrone ha un numero **suo**, non un resto.

═══════════════════════════════════════════════════════════════════════════
⛔ LE CINQUE REGOLE DI MISURA CHE QUESTO BANCO NON PUO' ROMPERE
═══════════════════════════════════════════════════════════════════════════

R1. ⛔⛔ **`drm-engine-*` misura TEMPO OCCUPATO, non LAVORO FATTO** (§CLOCK di
    `10-b87`): a parita' di lavoro, `[M]` 26,41 % a 300 MHz contro 7,01 % a
    1550 — un fattore **3,8**.  ⇒ Ogni riga porta accanto **frequenza GT e
    RC6**, e un soffitto si misura **a saturazione** oppure con la **GT
    bloccata** e dichiarandolo (`--gt 1550`).

R2. ⛔ **La GT che si muove fra due gradini rende il confronto nullo.**  Il
    banco campiona la GT per tutta la finestra e **si rifiuta** di confrontare
    due gradini le cui frequenze medie non combaciano (`p_gt_ferma`).

R3. ⛔ **La platea dei clienti DRM che cambia fra le due letture ⇒ `None`**,
    mai una percentuale.  ⚠ E' un difetto vero gia' pagato nel primo giro,
    dove ha prodotto un'occupazione del **−76 %**.  Il metro lo dichiara
    (`spariti`, `nuovi`); qui ci si **ferma**, non si stampa il numero.

R4. ⛔ **Un gradino non si legge dal gradino precedente.**  Ogni gradino ha una
    **marca** (`giro` della scena, che si azzera a ogni riaccensione) e una
    finestra `[t0, t1]` presa dall'orologio monotono della macchina **dopo**
    che il gradino prima e' finito.  Il banco verifica tutt'e due.

R5. ⛔ **Uno schermo fermo dichiarato come «scena che cambia» va smascherato**,
    non lasciato passare come «costo basso»: si contano i **commit** che il
    compositore ha davvero consegnato (dal blocco condiviso della scena, con il
    suo `fidato`) e i **byte per fotogramma** sul filo quando c'e' un cliente.

═══════════════════════════════════════════════════════════════════════════
⭐ COME SI MISURA «QUANTO CAMBIA» — e non e' un'opinione
═══════════════════════════════════════════════════════════════════════════

`04-b30-scena --movimento pieno` **danneggia tutta la propria superficie a ogni
disegno** (`04-b30-scena.c`, `if (S.danno == 1 || S.movimento == 2) danneggia(0,
0, W, H)`).  ⇒ Con `--finestra LxA` la superficie cambiata per commit vale
**esattamente L×A**, e allora:

    cambio [Mpixel/s]  =  commit/s (MISURATI dal blocco della scena)  ×  L·A

⭐ Due fattori, tutt'e due misurati o dichiarati per costruzione — niente
  geometria indovinata.  La scala delle finestre (480×270 … 1920×1080) da' un
  arco di **16×** in «quanto cambia» **senza toccare il ritmo**, ed e' con
  quella che si cerca la legge.
⚠ `--movimento marca` resta come estremo «quasi ferma»: li' la superficie
  cambiata e' solo il riquadro della marca, e il banco la marca `[?]` invece di
  calcolarla — non serve alla retta, serve a vedere il pavimento.

═══════════════════════════════════════════════════════════════════════════
COME SI USA
═══════════════════════════════════════════════════════════════════════════

    bash banchi/10-b91-terreno-dieci.sh porta      # con il MIO ambiente
    python3 banchi/10-b95-composizione.py porta    # i pezzi di questo banco
    python3 banchi/10-b95-composizione.py terreno
    python3 banchi/10-b95-composizione.py scomponi
    python3 banchi/10-b95-composizione.py ritmi [--scrivi-legge]
    python3 banchi/10-b95-composizione.py rampa [--fino 11] [--gt 1550]
    python3 banchi/10-b95-composizione.py sgombra
    python3 banchi/10-b95-composizione.py --certifica     # ⛔ i guasti innestati

⛔ L'isolamento di questo banco: porta **8110** · albero
   `/media/REMOTIX/src/10b1-src` · lavoro `/media/REMOTIX/tmp/10b1` · unita'
   `remotix-8110` · lucchetto GPU **`10-b1`**.  Gli utenti `provamt1…provamt11`
   sono **CONDIVISI**: lucchetto prima, palchi orfani verificati, `sgombra` alla
   fine col lucchetto ancora in mano.

⚠ E il numero del banco: c'e' **un altro `10-b95`** in questa cartella
  (`10-b95-browser.py`, di un altro agente, visto girare il 24 agosto 2026).
  I due file convivono, ma il NUMERO e' in collisione e va risolto da chi
  coordina: non l'ho risolto da solo perche' il nome me l'ha dato l'incarico.

═══════════════════════════════════════════════════════════════════════════
⛔⛔ CHE COSA QUESTO BANCO **NON** SA DIRE — detto qui, non in fondo
═══════════════════════════════════════════════════════════════════════════

Un banco che non dichiara i propri buchi e' un banco che rassicura.

 1. ⛔⛔ **Non separa il COMPOSITORE dalla CATTURA se non per differenza.**
    Mutter consegna i fotogrammi a PipeWire **dentro `gnome-shell`**: sulla GPU
    sono lo stesso cliente DRM.  ⇒ La cattura si legge solo come `G4 − G1`, e
    quella sottrazione **vale soltanto se la GT non si e' mossa** fra i due
    gradini — se si e' mossa, il banco **non la calcola** e lo dice.
 2. ⛔ **I gradini 2 e 3 dell'incarico non esistono in questo prodotto** (attacco
    senza codifica; cattura e conversione senza codifica): nessuna opzione di
    `src/main.c` li accende, e il figlio costruisce cattura, conversione e
    codifica in un tratto solo.  Dichiarato, non stimato.
 3. ⛔ **Non dice se `rcs0` e' SATURO, dice quanto e' stato OCCUPATO** — e' il
    limite del metro (`10-b87`, §NON SA DIRE punto 1).  Occupazione 99 % con la
    coda che cresce e occupazione 99 % con la coda piatta danno lo stesso numero.
 4. ⛔ **Non dice quanto LAVORO** e' stato fatto: `drm-engine-*` misura tempo, e
    il tempo dipende dalla frequenza della GT (§CLOCK, fattore 3,8).  ⇒ ogni
    riga porta GT e RC6, e c'e' `--gt 1550` per la seconda strada.
 5. ⛔ **Non sa che cosa faccia `rcs0` dentro `gnome-shell`**: comporre la scena,
    ridisegnare le decorazioni, scalare per la cattura e convertire per il
    codificatore finiscono tutti nello stesso contatore di quel processo.
 6. ⚠ **La superficie cambiata e' quella DICHIARATA dalla scena**, non quella che
    Mutter ha davvero ridipinto: se il compositore ridisegna tutto lo schermo
    anche per un danno piccolo, il costo non seguira' il «quanto cambia» — ⭐ ed
    e' **esattamente la domanda** che il modo `ritmi` esiste per rispondere.
 7. ⚠ **Il caso e' quello DURO**: `--movimento pieno` danneggia tutta la
    superficie a ogni fotogramma.  Non e' il desktop medio, e il numero che ne
    esce e' un **pavimento**, non una previsione per dieci utenti che leggono
    la posta.
 8. ⚠ **Un solo compositore**: GNOME/Mutter.  Un altro compositore avrebbe un
    altro costo, e `DECISIONI.md` non permette eccezioni per compositore.
 9. ⛔ **Non guarda la Radeon** (`renderD129`): e' chiusa apposta da udev
    (§4.6-quinquies), e il filtro e' sul `drm-pdev` della integrata.
10. ⚠ **I clienti girano sulla stessa macchina**: la rete non e' provata qui, e
    non e' quel che questo banco misura.
"""

import argparse
import base64
import importlib.util
import json
import math
import os
import re
import shlex
import subprocess
import sys
import time

# ═══════════════════════════════════════════════════════════════════════════
# L'AMBIENTE — tutto sovrascrivibile, niente cablato in mezzo al codice
# ═══════════════════════════════════════════════════════════════════════════
MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
IND = os.environ.get("IND", "192.168.0.2")
PORTA = int(os.environ.get("PORTA", "8110"))
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/10b1-src")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/10b1")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/10b1-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/10b1")
UNITA = os.environ.get("UNITA", "remotix-%d" % PORTA)
SCENA_BIN = os.environ.get("SCENA_BIN",
                           "/media/REMOTIX/src/04-b30-scena-lav/04-b30-scena")
LUCCHETTO = os.environ.get("LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-gpu.d")
IO_SONO = os.environ.get("IO_SONO", "10-b1")
PDEV_BUONO = os.environ.get("PDEV", "0000:00:02.0")
FUORI = os.environ.get("FUORI", "/tmp/10-b95")
QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ Gli utenti sono CONDIVISI e l'uid segue il nome per costruzione, come in
#    `10-b91-terreno-dieci.sh`: `provamtN` → uid 1109+N.  Due tabelle in due
#    file divergono, e la seconda e' sempre quella sbagliata.
UID_BASE = 1109
UTENTI_MAX = 11


def utente(i):
    return "provamt%d" % i


def uid(i):
    return UID_BASE + i


VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LE SOGLIE, IN UN POSTO SOLO, CIASCUNA CON LA SUA RAGIONE
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `LEZIONI.md` §1.33: una soglia si tara sui DUE ESTREMI NOTI prima di
#    crederci.  ⚠ Nessuna di queste stacca niente: decidono il colore di una
#    riga, e il margine si dichiara da tutt'e due i lati.

COMMIT_VIVI = 5.0        # ⛔ IL PREDICATO DELLO SCHERMO FERMO, primo pilastro.
                         #   Gli estremi noti: `[M]` una scena viva su questo
                         #   compositore consegna 55-60 commit/s (monitor
                         #   virtuale a 60 Hz); una scena spenta o un palco
                         #   senza consumatore ne consegna **0**.  La soglia sta
                         #   molto sotto il vivo e molto sopra il morto.
BYTE_VIVI = 4000         # ⛔ IL PREDICATO DELLO SCHERMO FERMO, secondo pilastro,
                         #   e vale solo quando c'e' un cliente collegato.
                         #   Gli estremi, tutti `[M]` e tutti di banchi diversi:
                         #   desktop quasi fermo **242-283 B/fotogramma** (fase
                         #   9) · scena `barra` 1080p **2 448** (10-b92, 24 ago)
                         #   · trascinamento di finestra **3 801** (fase 9) ·
                         #   scena `pieno` **5 600** e oltre.  ⇒ La soglia sta
                         #   SOPRA i tre estremi che non mordono.
GT_TOLLERANZA = 0.05     # ⛔ R2: due gradini con GT media che differisce di piu'
                         #   del 5 % non si confrontano.  ⚠ Il 5 % e' molto
                         #   sotto il fattore 3,8 del §CLOCK, cioe' sta dalla
                         #   parte prudente: rifiuta piu' di quanto servirebbe.
ASSESTAMENTO_S = 8.0     # ⛔ i primi secondi di una sessione nuova sono
                         #   apertura, prima chiave e prima tela: si tolgono e
                         #   si DICE quanto (`REVIEWER.md` E9)
FINESTRA_S = 12.0        # la finestra di misura della GPU
SATURO_RENDER = 95.0     # ⛔ oltre, `rcs0` e' pieno.  ⚠ Non e' «la macchina e'
                         #   satura»: e' «questo motore e' occupato quasi
                         #   sempre», che e' quel che il metro sa dire (§NON SA
                         #   DIRE, punto 1 di `10-b87`)

# ⭐ La scala delle finestre: e' l'arco di «quanto cambia», a ritmo invariato.
#
# ⛔ IL PAVIMENTO NON L'HO SCELTO IO, lo pone la scena — e si e' letto nel suo
#    codice invece di scoprirlo con un giro sprecato: `04-b30-scena.c` rifiuta
#    `--finestra` sotto **640×480**, e in piu' pretende che ci stiano le DUE
#    marche, cioe' `2 · (margine + 8·cella + 16) + quiete` = **492 px** di
#    altezza coi valori di riposo.  ⇒ Il punto piu' piccolo e' 640×496.
# ⚠ L'arco che ne esce e' **6,5×** (0,317 → 2,074 Mpixel per commit): non e' il
#   16× che si voleva, e si dichiara.
# ⭐ E la superficie NON si crede: si RILEGGE dal blocco condiviso della scena
#   (`larghezza`/`altezza`), che e' quel che il compositore le ha davvero dato.
SCALA_FINESTRE = [(640, 496), (960, 540), (1280, 720), (1600, 900), (1920, 1080)]
TELA = os.environ.get("TELA", "1920x1080")
CODEC_CHIESTO = os.environ.get("CODEC", "h264")


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LA RADICE — un solo `sudo`, e la catena dentro la SUA shell
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ La forma sbagliata e' MUTA (`09-b70-ritmo.py`): un `< file` o un `| grep`
#    in coda non lo prende il comando, lo prende `sudo`, che allora non riceve
#    piu' la parola sullo stdin, esce 1, e un `|| echo 0` trasforma l'errore in
#    un numero plausibile.
def catena_root(comando):
    return ("printf '%%s\\n' '%s' | sudo -S -p '' bash -c %s"
            % (PAROLA_SUDO, shlex.quote(comando)))


def rem(comando, tetto=120):
    try:
        p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, comando],
                           capture_output=True, timeout=tetto)
    except subprocess.TimeoutExpired:
        return (124, "", "⛔ scaduto dopo %d s" % tetto)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def root(comando, tetto=120):
    return rem(catena_root(comando), tetto)


def spedisci(sorgente, nome):
    """⛔ In base64: le virgolette di un heredoc dentro un `sudo -S` dentro un
       `ssh` sono tre livelli di quoting, e uno sbagliato non da' un errore —
       da' un file troncato."""
    b = base64.b64encode(sorgente.encode("utf-8")).decode("ascii")
    root("mkdir -p %s && printf '%%s' '%s' | base64 -d > %s/%s"
         % (LAV, b, LAV, nome))
    rc, out, _ = root("wc -c < %s/%s" % (LAV, nome))
    t = out.strip()
    return t.isdigit() and int(t) > 300


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE GIRA SULLA MACCHINA DI PROVA, DA ROOT
# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ PERCHE' sta qui dentro e non in cinque comandi `ssh`: il metro va letto
#    **due volte a distanza nota**, e fra le due letture ci devono stare i
#    campioni della GT e i contatori delle scene.  Cinque `ssh` sono cinque
#    istanti diversi, e cinque istanti diversi non fanno una misura — fanno un
#    collage (`10-b92`, sopra la sonda).
# ⛔ E serve ROOT: `/proc/<pid>/fdinfo` degli altri utenti non si legge, e una
#    lettura NEGATA non e' una lettura che dice zero.

SYS_GT = "/sys/class/drm/card0"


def _carica(nome, percorso):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    sys.modules[nome] = m
    spec.loader.exec_module(m)
    return m


def _uid_di(pid):
    """L'uid reale di un pid.  ⛔ `None` se non si legge — non 0, che e' root."""
    try:
        with open("/proc/%d/status" % pid) as f:
            for riga in f:
                if riga.startswith("Uid:"):
                    return int(riga.split()[1])
    except Exception:
        return None
    return None


def _sul_server(passo):
    """Il mezzo che gira da root sulla macchina di prova.  Legge la richiesta
       in JSON dallo stdin e stampa UNA riga JSON."""
    if os.geteuid() != 0:
        print(json.dumps({"esito": "⛔ «--sul-server» va eseguito DA ROOT"}))
        return 2
    try:
        richiesta = json.loads(sys.stdin.read() or "{}")
    except Exception as e:
        print(json.dumps({"esito": "⛔ richiesta illeggibile: %s" % e}))
        return 2

    qui = os.path.dirname(os.path.abspath(__file__))
    try:
        metro = _carica("metro", os.path.join(qui, "10-b87-metro-gpu.py"))
    except Exception as e:
        print(json.dumps({"esito": "⛔ il metro della GPU non si carica: %s" % e}))
        return 2

    if passo == "gt":
        return _sul_server_gt(metro, richiesta)
    if passo == "misura":
        try:
            marca = _carica("marca", os.path.join(qui, "03-marca.py"))
        except Exception as e:
            print(json.dumps({"esito": "⛔ 03-marca.py non si carica: %s" % e}))
            return 2
        return _sul_server_misura(metro, marca, richiesta)
    if passo == "scene":
        try:
            marca = _carica("marca", os.path.join(qui, "03-marca.py"))
        except Exception as e:
            print(json.dumps({"esito": "⛔ 03-marca.py non si carica: %s" % e}))
            return 2
        print(json.dumps({"esito": "letto",
                          "scene": _leggi_scene(marca, richiesta.get("scene", []))}))
        return 0
    print(json.dumps({"esito": "⛔ passo sconosciuto: %s" % passo}))
    return 2


def _leggi_scene(marca, nomi):
    """I contatori di ciascuna scena, con l'orologio monotono accanto.
       ⛔ Una scena che non si legge sta nel risultato come `c_e: False`, mai
          come zero commit."""
    fuori = {}
    for nome in nomi:
        t = time.clock_gettime(time.CLOCK_MONOTONIC)
        try:
            d = marca.leggi_conteggio(nome)
        except Exception as e:
            d = {"c_e": False, "perche": "⛔ eccezione: %s: %s"
                                         % (type(e).__name__, e)}
        d["t_mono"] = t
        fuori[nome] = d
    return fuori


def _sul_server_gt(metro, richiesta):
    """⭐ Blocca o rimette la GT.  Torna sempre il PRIMA e il DOPO letti dal
       sysfs: una frequenza «chiesta» non e' una frequenza «in vigore»."""
    prima = metro.leggi_gt()
    rpn = metro._intero(SYS_GT + "/gt_RPn_freq_mhz")
    rp0 = metro._intero(SYS_GT + "/gt_RP0_freq_mhz")
    scritture = []
    obiettivo = richiesta.get("blocca")
    if obiettivo == "rimetti":
        f_min, f_max = rpn, rp0
    elif obiettivo is not None:
        f_min = f_max = int(obiettivo)
    else:
        f_min = f_max = None
    if f_min is not None:
        # ⛔ L'ordine conta: prima si abbassa il minimo, poi si muove il massimo,
        #    poi si rialza il minimo.  Al contrario il nucleo rifiuta min > max.
        for percorso, valore in ((SYS_GT + "/gt_min_freq_mhz", rpn or f_min),
                                 (SYS_GT + "/gt_max_freq_mhz", f_max),
                                 (SYS_GT + "/gt_min_freq_mhz", f_min),
                                 (SYS_GT + "/gt_boost_freq_mhz", f_max)):
            scritture.append([percorso, valore,
                              bool(metro._scrivi_sysfs(percorso, valore))])
    dopo = metro.leggi_gt()
    print(json.dumps({"esito": "fatto", "rpn": rpn, "rp0": rp0,
                      "prima": prima, "dopo": dopo, "scritture": scritture,
                      "bloccata": (dopo.get("min_mhz") is not None
                                   and dopo["min_mhz"] == dopo["max_mhz"])}))
    return 0


def _sul_server_misura(metro, marca, r):
    """⛔⛔ LA FINESTRA DI MISURA — ed e' il cuore del banco.

    Ordine, e non e' indifferente:
        t0 → istantanea A → contatori delle scene (prima)
           → campioni di GT per tutta la durata
           → contatori delle scene (dopo) → istantanea B → t1

    ⇒ La finestra delle scene sta DENTRO quella della GPU, e le due durate si
      dichiarano tutt'e due: chi legge non deve dedurre di quanto differiscono.
    """
    secondi = float(r.get("secondi", FINESTRA_S))
    nomi_scene = r.get("scene", [])
    if secondi < 1.0:
        print(json.dumps({"esito": "⛔ finestra troppo corta: %.3f s" % secondi}))
        return 2

    t0 = time.clock_gettime(time.CLOCK_MONOTONIC)
    pdev = metro.pdev_del_nodo(metro.NODO_PREDEFINITO)
    a = metro.leggi_istantanea(pdev=pdev)
    scene_a = _leggi_scene(marca, nomi_scene)

    gt_campioni = []
    fine = time.monotonic() + secondi
    while True:
        g = metro.leggi_gt()
        g["t"] = time.monotonic()
        gt_campioni.append(g)
        resta = fine - time.monotonic()
        if resta <= 0:
            break
        time.sleep(min(0.5, resta))

    scene_b = _leggi_scene(marca, nomi_scene)
    b = metro.leggi_istantanea(pdev=pdev)
    t1 = time.clock_gettime(time.CLOCK_MONOTONIC)

    m = metro.confronta(a, b)
    # ⛔⛔ CHI e' nato e CHI e' morto, non solo QUANTI.
    #
    # ⚠ E' la correzione di un difetto che questo banco ha avuto addosso alla
    #   prima stesura, trovato misurando: `confronta` conta `spariti` e `nuovi`,
    #   e la prima versione si rifiutava di giudicare **qualunque** ricambio.
    #   `[M]` 24 agosto 2026, finestra di 3 s su questa macchina: **8 clienti
    #   spariti** senza che nessuno dei miei si muovesse — erano di un altro
    #   agente.  ⇒ Rifiutarsi li' vorrebbe dire non misurare mai niente.
    #
    # ⭐ La regola giusta: il ricambio conta se tocca **i miei** processi.  Se
    #   tocca un estraneo, i numeri PER PID dei miei restano validi (sono
    #   clienti presenti in tutt'e due le letture) e il totale DELLA MACCHINA
    #   diventa un **limite inferiore**, dichiarato.
    if m is not None:
        def _chi(clienti):
            return [{"pid": v["pid"], "comm": v.get("comm"),
                     "uid": _uid_di(v["pid"])} for v in clienti.values()]
        via = {k: v for k, v in a["clienti"].items() if k not in b["clienti"]}
        nati = {k: v for k, v in b["clienti"].items() if k not in a["clienti"]}
        m["spariti_chi"] = _chi(via)
        m["nuovi_chi"] = _chi(nati)
    # ⛔ `None` NON e' zero: se il metro non ha misurato, il banco riceve `None`
    #    e si rifiuta di giudicare.  Qui si porta anche il PERCHE'.
    fuori = {"esito": "letto", "t0_mono": t0, "t1_mono": t1,
             "scene_a": scene_a, "scene_b": scene_b,
             "gt_campioni": gt_campioni,
             "gpu": None, "gpu_perche": None}
    if m is None:
        fuori["gpu_perche"] = ("⛔ il metro non ha misurato: `confronta` ha "
                               "reso None (una delle due letture manca, o il "
                               "tempo fra le due non e' valido)")
        print(json.dumps(fuori, default=str))
        return 0

    # ⭐ L'uid di ogni pid misurato: e' quel che trasforma «un pid» in «di chi
    #    e' il lavoro».  ⛔ Letto DOPO la seconda istantanea, quando i pid
    #    esistono ancora; se non si legge resta `None`, e quel pid finisce fra
    #    i non attribuibili invece che nel mucchio di qualcun altro.
    per_pid = {}
    for pid, d in m["per_pid"].items():
        v = dict(d)
        v["pid"] = int(pid)
        v["uid"] = _uid_di(int(pid))
        per_pid[str(pid)] = v
    m["per_pid"] = per_pid
    # ⚠ `per_cliente` ha chiavi tuple: JSON non le sa scrivere.  Si conserva il
    #    conto e la lista, che e' quel che serve al predicato di attribuzione.
    clienti = []
    for chiave, v in m["per_cliente"].items():
        clienti.append({"pid": int(chiave[0]), "avvio": chiave[1],
                        "cid": chiave[2], "comm": v.get("comm"),
                        "render_pct": v.get("render_pct"),
                        "video_pct": v.get("video_pct"),
                        "video-enhance_pct": v.get("video-enhance_pct"),
                        "copy_pct": v.get("copy_pct")})
    m["per_cliente"] = clienti
    fuori["gpu"] = m
    print(json.dumps(fuori, default=str))
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE GIRA SUL PORTATILE
# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════

def misura_finestra(secondi, scene):
    """Una finestra di misura sulla macchina di prova.  ⛔ `None` se non e'
       tornata: un dizionario vuoto sarebbe «tutto zero», che e' un'altra cosa."""
    r = json.dumps({"secondi": secondi, "scene": scene})
    b = base64.b64encode(r.encode("utf-8")).decode("ascii")
    rc, out, err = root(
        "printf '%%s' '%s' | base64 -d | python3 %s/banchi/10-b95-composizione.py "
        "--sul-server misura" % (b, ALB), int(secondi) + 180)
    try:
        return json.loads(out.strip().splitlines()[-1])
    except Exception as e:
        _dub("⛔ la finestra di misura non ha risposto (rc=%s): %s — %s"
             % (rc, e, (out + err)[-300:]))
        return None


def gt_comanda(quale):
    """`quale` = un numero di MHz, oppure «rimetti».  ⛔ `None` se non si sa."""
    r = json.dumps({"blocca": quale})
    b = base64.b64encode(r.encode("utf-8")).decode("ascii")
    rc, out, err = root(
        "printf '%%s' '%s' | base64 -d | python3 %s/banchi/10-b95-composizione.py "
        "--sul-server gt" % (b, ALB), 120)
    try:
        return json.loads(out.strip().splitlines()[-1])
    except Exception as e:
        _dub("⛔ il comando alla GT non ha risposto (rc=%s): %s — %s"
             % (rc, e, (out + err)[-300:]))
        return None


def orologio():
    """L'orologio MONOTONO della macchina di prova, in ms.  ⛔ `None` se non
       l'ho letto: e' l'ancora, e un'ancora indovinata non e' un'ancora."""
    rc, out, _ = rem("python3 -c 'import time; print(\"%.3f\" % "
                     "(time.clock_gettime(time.CLOCK_MONOTONIC)*1000))'", 60)
    try:
        return float(out.strip())
    except Exception:
        return None


# ───────────────────────────────────────────────────────────────────────────
# ⭐ L'ATTRIBUZIONE — ⛔ la parte difficile e la parte che conta
# ───────────────────────────────────────────────────────────────────────────
#
# ⛔ Funzione PURA: non legge niente, quindi si puo' guastare a mano e si
#    certifica senza macchina (`10-b87`, `confronta`).

COMPOSITORI = ("gnome-shell", "gnome-shel")   # ⚠ `comm` e' troncato a 15
PRODOTTO = ("remotix",)


def attribuisci(gpu, uid_miei):
    """Da `per_pid` ai PADRONI di `rcs0`.  ⛔ Torna `None` quando non si puo'
       attribuire, mai un numero comodo.

    Le quattro categorie, e la quinta che e' la piu' importante:
      · `compositori`  — `gnome-shell` di uno dei MIEI uid (compone + cattura)
      · `conversione`  — `render` dei figli `remotix` dei MIEI uid
      · `codifica`     — `video` degli stessi figli (⚠ fondo scala 200 %)
      · `estranei`     — tutto il resto: ⛔ si CONTA e si DICHIARA, non si butta
      · `non_attribuibili` — pid di cui non si e' letto l'uid, o motori che il
        metro ha reso `None`.  ⛔ Se ce n'e' anche uno, il totale di quella
        categoria e' `None`: «non ho misurato» non e' «non e' successo niente».
    """
    if gpu is None:
        return None
    per_pid = gpu.get("per_pid")
    if not isinstance(per_pid, dict):
        return None

    # ⛔⛔ R3 — LA PLATEA CHE CAMBIA.  Un cliente DRM nato o morto fra le due
    #    letture rende il delta di TUTTA la macchina non confrontabile: il
    #    primo giro ci ha letto un'occupazione del −76 %.
    #
    # ⭐ Ma il ricambio si guarda per NOME, non per numero: se a nascere e a
    #   morire sono processi che non sono miei, i numeri per pid dei miei sono
    #   ancora buoni (sono clienti presenti a tutt'e due le letture) e a
    #   diventare un LIMITE INFERIORE e' il totale della macchina.  ⛔ Se invece
    #   il ricambio tocca un mio uid, ci si ferma: `None`, non un numero.
    mio_ricambio = []
    for v in (gpu.get("spariti_chi") or []) + (gpu.get("nuovi_chi") or []):
        if v.get("uid") in uid_miei or v.get("uid") is None:
            mio_ricambio.append("%s (pid %s, uid %s)"
                                % (v.get("comm"), v.get("pid"), v.get("uid")))
    if mio_ricambio:
        return {"esito": None,
                "perche": ("⛔ la platea dei clienti DRM e' CAMBIATA fra le due "
                           "letture E IL RICAMBIO E' MIO (%s): il delta non e' "
                           "di una popolazione sola, e non lo giudico.  ⚠ E' il "
                           "difetto che nel primo giro ha prodotto "
                           "un'occupazione del −76 %%" % " · ".join(mio_ricambio[:4]))}
    ricambio_estraneo = (gpu.get("spariti", 0) or 0) + (gpu.get("nuovi", 0) or 0)
    if gpu.get("anomali"):
        return {"esito": None,
                "perche": ("⛔ %d contatori anomali (all'indietro o impossibili): "
                           "non giudico" % gpu["anomali"])}

    cat = {"compositori": {}, "prodotto": {}, "estranei": {}}
    buchi = []
    for spid, d in per_pid.items():
        comm = (d.get("comm") or "").strip()
        u = d.get("uid")
        rend = d.get("render_pct")
        vid = d.get("video_pct")
        veh = d.get("video-enhance_pct")
        cop = d.get("copy_pct")
        if rend is None or vid is None:
            buchi.append("pid %s (%s): il metro non ha misurato tutti i motori"
                         % (spid, comm or "?"))
        voce = {"pid": int(spid), "comm": comm, "uid": u, "render": rend,
                "video": vid, "video_enhance": veh, "copy": cop}
        if u is None:
            buchi.append("pid %s (%s): l'uid non si e' letto ⇒ non lo attribuisco "
                         "a nessuno" % (spid, comm or "?"))
            cat["estranei"][spid] = voce
            continue
        if u in uid_miei and comm in COMPOSITORI:
            cat["compositori"][spid] = voce
        elif u in uid_miei and comm in PRODOTTO:
            cat["prodotto"][spid] = voce
        else:
            cat["estranei"][spid] = voce

    def somma(voci, campo):
        # ⛔ Un solo `None` in un mucchio rende `None` tutto il mucchio.
        vals = [v[campo] for v in voci.values()]
        if any(x is None for x in vals):
            return None
        return sum(vals)

    fuori = {
        "esito": "attribuito",
        "compositore_render": somma(cat["compositori"], "render"),
        "compositore_video": somma(cat["compositori"], "video"),
        "compositore_veh": somma(cat["compositori"], "video_enhance"),
        "conversione_render": somma(cat["prodotto"], "render"),
        "codifica_video": somma(cat["prodotto"], "video"),
        "prodotto_veh": somma(cat["prodotto"], "video_enhance"),
        "estranei_render": somma(cat["estranei"], "render"),
        "estranei_video": somma(cat["estranei"], "video"),
        "n_compositori": len(cat["compositori"]),
        "n_prodotto": len(cat["prodotto"]),
        "n_estranei": len(cat["estranei"]),
        "estranei_chi": sorted(set((v["comm"], v["uid"])
                                   for v in cat["estranei"].values())),
        "buchi": buchi,
        # ⛔ Il ricambio ESTRANEO non annulla i miei numeri, ma rende il totale
        #    della macchina un limite INFERIORE, e si dichiara.
        "ricambio_estraneo": ricambio_estraneo,
        "totale_e_limite_inferiore": bool(ricambio_estraneo),
        "macchina_render": (gpu.get("macchina") or {}).get("render_pct"),
        "macchina_video": (gpu.get("macchina") or {}).get("video_pct"),
        "capacita_video": gpu.get("capacita_video"),
        "parziale": (gpu.get("macchina") or {}).get("parziale"),
        "parziale_perche": (gpu.get("macchina") or {}).get("perche"),
    }
    return fuori


def gt_riassunto(campioni):
    """Media, minimo, massimo e «bloccata» dei campioni di GT.
       ⛔ `None` se non c'e' niente da riassumere.

    ⛔⛔ E LA MEDIA E' DUE, non una — ed e' un difetto che questo banco ha avuto
        addosso e che si e' visto misurando.  `[M]` 24 agosto 2026:
        `gt_act_freq_mhz` vale **0** quando la GT e' del tutto spenta (RC6), e a
        riposo la maggioranza dei campioni e' zero.  Una media che li conta
        risponde a *«quanto e' stata sveglia»*, non a *«a che frequenza ha
        lavorato»* — e quella che governa il §CLOCK, cioe' quanto tempo un
        fotogramma tiene occupato il motore, e' **la seconda**.
      ⇒ `act_media` (tutti i campioni) e `act_media_sveglia` (solo quelli > 0),
        con accanto **quanti** erano svegli.  Il predicato usa la seconda.
    """
    if not campioni:
        return None
    att = [c["act_mhz"] for c in campioni if c.get("act_mhz") is not None]
    cur = [c["cur_mhz"] for c in campioni if c.get("cur_mhz") is not None]
    mins = set(c.get("min_mhz") for c in campioni)
    maxs = set(c.get("max_mhz") for c in campioni)
    if not att and not cur:
        return None
    serie = att or cur
    sveglia = [x for x in serie if x > 0]
    return {"campioni": len(campioni),
            "act_media": sum(serie) / len(serie),
            "act_media_sveglia": (sum(sveglia) / len(sveglia) if sveglia else None),
            "sveglia_campioni": len(sveglia),
            "frazione_sveglia": len(sveglia) / float(len(serie)),
            "act_min": min(serie), "act_max": max(serie),
            "quale": "act_mhz" if att else "cur_mhz",
            "min_mhz": (list(mins)[0] if len(mins) == 1 else sorted(
                x for x in mins if x is not None)),
            "max_mhz": (list(maxs)[0] if len(maxs) == 1 else sorted(
                x for x in maxs if x is not None)),
            "bloccata": (len(mins) == 1 and len(maxs) == 1
                         and list(mins)[0] is not None
                         and list(mins)[0] == list(maxs)[0])}


def rc6_di(gpu):
    """La residenza RC6 della finestra — ⭐ seconda misura INDIPENDENTE dai
       fdinfo.  ⛔ `None` se il metro non l'ha letta."""
    if gpu is None:
        return None
    return (gpu.get("gt") or {}).get("rc6_pct")


def cambio_delle_scene(scene_a, scene_b):
    """⭐ QUANTO E' CAMBIATO DAVVERO, in Mpixel/s, e da che cosa lo so.

    `commit` e' quel che la scena ha consegnato al compositore; `area_px` e' la
    superficie che `--movimento pieno` danneggia per ogni commit — cioe' L×A
    per costruzione, non una geometria indovinata.

    ⛔ Torna `None` per una scena che non si e' letta, o il cui blocco non e'
       `fidato` (corsa a vuoto, relitto, scrittore morto): un ritmo non fidato
       non e' un ritmo basso.
    """
    fuori = {}
    for nome, b in (scene_b or {}).items():
        a = (scene_a or {}).get(nome)
        v = {"nome": nome, "commit_s": None, "mpx_s": None, "perche": None,
             "fidato": None}
        if not a or not a.get("c_e") or not b.get("c_e"):
            v["perche"] = ("⛔ il blocco della scena non si e' letto: %s"
                           % ((b or {}).get("perche") or (a or {}).get("perche")
                              or "senza ragione dichiarata"))
            fuori[nome] = v
            continue
        v["fidato"] = bool(b.get("fidato"))
        if not b.get("fidato"):
            v["perche"] = ("⛔ il blocco c'e' ma NON e' fidato: %s"
                           % " · ".join(b.get("perche_non_fidato") or ["?"]))
            fuori[nome] = v
            continue
        dt = b["t_mono"] - a["t_mono"]
        if dt <= 0.5:
            v["perche"] = "⛔ finestra della scena troppo corta: %.3f s" % dt
            fuori[nome] = v
            continue
        dc = b["commit"] - a["commit"]
        if dc < 0:
            v["perche"] = ("⛔ i commit sono andati ALL'INDIETRO (%d → %d): la "
                           "scena e' ripartita dentro la finestra"
                           % (a["commit"], b["commit"]))
            fuori[nome] = v
            continue
        v["dt"] = dt
        v["commit"] = dc
        v["disegni"] = b["disegni"] - a["disegni"]
        v["attese"] = b["attese"] - a["attese"]
        v["commit_s"] = dc / dt
        v["larghezza"] = b.get("larghezza")
        v["altezza"] = b.get("altezza")
        v["movimento"] = b.get("movimento")
        v["danno"] = b.get("danno")
        v["giro"] = b.get("giro")
        v["refresh_hz"] = b.get("refresh_hz")
        # ⛔ Solo `pieno` danneggia tutta la superficie: per gli altri movimenti
        #    la superficie cambiata NON si dichiara, si marca `[?]`.
        if b.get("movimento") == "pieno" and b.get("larghezza") and b.get("altezza"):
            area = b["larghezza"] * b["altezza"]
            v["area_px"] = area
            v["mpx_s"] = v["commit_s"] * area / 1e6
        else:
            v["area_px"] = None
            v["perche"] = ("[?] movimento «%s»: la superficie cambiata per "
                           "commit non e' L×A e non la calcolo"
                           % b.get("movimento"))
        fuori[nome] = v
    return fuori


def cambio_totale(cambi):
    """La somma dei Mpixel/s cambiati.  ⛔ `None` se anche una sola scena non
       ha un numero: una somma con un buco dentro non e' una somma."""
    if not cambi:
        return None
    vals = [v.get("mpx_s") for v in cambi.values()]
    if any(x is None for x in vals):
        return None
    return sum(vals)


# ───────────────────────────────────────────────────────────────────────────
# ⛔ I PREDICATI — ciascuno torna (True | False | None, spiegazione)
# ───────────────────────────────────────────────────────────────────────────
#
# ⛔ `None` vuol dire «non ho potuto giudicare» e NON e' un verde: chi chiama
#    lo conta fra i muti, non fra i passati (`REVIEWER.md` §1).

def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)


def p_scena_morde(cambi, byte_per_fotogramma=None, rcs0_pct=None):
    """⛔ IL PREDICATO DELLO SCHERMO FERMO — R5.

    Un desktop che **non compone** dichiarato come «scena che cambia» dev'essere
    smascherato, non lasciato passare come «costo basso».  Tre pilastri:
      1. i **commit** consegnati al compositore (sempre disponibili);
      2. i **byte per fotogramma** sul filo (solo se c'e' un cliente collegato);
      3. ⭐ **quanto e' occupato `rcs0`** — ed e' il pilastro che distingue le
         due cose che il ritmo da solo confonde.

    ⛔⛔ E IL TERZO E' NATO DA UN DIFETTO DI QUESTO BANCO, trovato pensandoci
        prima invece che dopo.  Alla rampa, quando il compositore satura, i
        `wl_surface.frame` arrivano piano e **i commit crollano** — esattamente
        come in uno schermo fermo.  ⚠ Un predicato che guardasse il solo ritmo
        avrebbe dato «SCHERMO FERMO» proprio ai gradini che sono il RISULTATO
        della prova, cioe' un rosso al prodotto per un fenomeno che il banco
        stava cercando.
      ⇒ Il meccanismo accanto al sintomo (`LEZIONI.md` §1.31): commit bassi
        **con `rcs0` scarico** sono uno schermo fermo; commit bassi **con
        `rcs0` pieno** sono saturazione, e sono la misura, non un guasto.
      ⛔ E quando `rcs0` non si e' letto, si sta dalla parte prudente: si accusa,
        perche' «non so» non deve diventare un salvacondotto.
    """
    if not cambi:
        return _muto("⛔ nessuna scena da guardare: non giudico")
    fermi, vivi, muti = [], [], []
    for nome, v in cambi.items():
        if v.get("commit_s") is None:
            muti.append("%s: %s" % (nome, v.get("perche")))
        elif v["commit_s"] < COMMIT_VIVI:
            fermi.append("%s: %.2f commit/s (soglia %.1f)"
                         % (nome, v["commit_s"], COMMIT_VIVI))
        else:
            vivi.append("%s: %.1f commit/s" % (nome, v["commit_s"]))
    if muti:
        return _muto("⛔ %d scene non si leggono ⇒ non giudico: %s"
                     % (len(muti), " · ".join(muti[:3])))
    if fermi and rcs0_pct is not None and rcs0_pct >= SATURO_RENDER:
        return _si("⚠ il ritmo e' basso (%s) ma `rcs0` sta al %.1f %%: e' "
                   "SATURAZIONE, non uno schermo fermo — ⭐ ed e' il risultato "
                   "che la rampa cerca, non un guasto"
                   % (" · ".join(fermi[:3]), rcs0_pct))
    if fermi:
        return _no("⛔ SCHERMO FERMO dichiarato come scena che cambia — %s "
                   "(`rcs0` %s).  ⚠ Il costo basso che ne uscirebbe non e' del "
                   "prodotto: e' di un desktop che non compone"
                   % (" · ".join(fermi[:4]),
                      "non letto ⇒ accuso lo stesso" if rcs0_pct is None
                      else "al %.1f %%" % rcs0_pct))
    if byte_per_fotogramma is not None and byte_per_fotogramma < BYTE_VIVI:
        return _no("⛔ i commit ci sono, ma il filo porta %.0f byte per "
                   "fotogramma (soglia %d): quel che cambia non arriva "
                   "all'immagine" % (byte_per_fotogramma, BYTE_VIVI))
    return _si("⭐ la scena morde: %s%s" % (
        " · ".join(vivi[:4]),
        "" if byte_per_fotogramma is None
        else " · %.0f B/fotogramma" % byte_per_fotogramma))


def p_attribuzione_giusta(gpu, attr, uid_miei):
    """⛔ IL METRO NON DEVE ATTRIBUIRE A `gnome-shell` IL LAVORO DI UN ALTRO
       CLIENTE DRM.

    Il controllo e' esplicito e non si fida della categoria: ogni cliente DRM
    contato fra i compositori deve avere **il suo** pid con `comm` di
    compositore e uno dei miei uid.  Un cliente il cui pid non e' fra i
    compositori, ma il cui tempo di render e' finito nel mucchio, e' rosso.
    """
    if gpu is None or attr is None:
        return _muto("⛔ non ho niente da controllare")
    if attr.get("esito") is None:
        return _muto(attr.get("perche") or "⛔ attribuzione non fatta")
    per_pid = gpu.get("per_pid") or {}
    clienti = gpu.get("per_cliente") or []
    sbagliati = []
    pid_compositori = set()
    for spid, v in per_pid.items():
        comm = (v.get("comm") or "").strip()
        if v.get("uid") in uid_miei and comm in COMPOSITORI:
            pid_compositori.add(int(spid))
    # 2. la somma per cliente DRM di quei pid deve tornare con la somma per pid
    somma_clienti = 0.0
    visto = False
    for c in clienti:
        if c["pid"] in pid_compositori:
            if c.get("render_pct") is None:
                return _muto("⛔ un cliente DRM del compositore non e' stato "
                             "misurato: non giudico")
            somma_clienti += c["render_pct"]
            visto = True
        # ⛔⛔ QUI IL BANCO HA SBAGLIATO, e il rosso l'ho visto misurando.
        #
        # La prima stesura accusava ogni `gnome-shell` che non fosse di un mio
        # uid.  `[M]` 24 agosto 2026: sulla macchina di prova ce ne sono nove,
        # di altri agenti — e ⭐ `attribuisci` li mette GIA' fra gli estranei,
        # dove devono stare.  ⇒ Era un ROSSO SU CODICE GIUSTO (`LEZIONI.md`
        # §2.3), e per giunta su un fatto che un altro predicato — quello degli
        # estranei — misura meglio, col numero invece che col nome.
        # ⚠ Questo predicato ha UN mestiere solo: che il % attribuito ai MIEI
        #   compositori venga per intero dai clienti DRM dei MIEI pid.
    atteso = attr.get("compositore_render")
    if atteso is None:
        return _muto("⛔ il render dei compositori e' None: non giudico")
    if not visto:
        return _muto("⛔ nessun cliente DRM di compositore nella fotografia")
    if abs(somma_clienti - atteso) > 0.05:
        return _no("⛔ ATTRIBUZIONE SBAGLIATA: la somma per cliente DRM dei "
                   "compositori vale %.3f %%, quella per pid %.3f %% — c'e' "
                   "dentro il lavoro di un altro cliente" % (somma_clienti, atteso))
    if sbagliati:
        return _no("⛔ %s" % " · ".join(sbagliati[:3]))
    return _si("⭐ ogni %% attribuito ai compositori viene da un cliente DRM di "
               "un `gnome-shell` dei miei uid (%.2f %% su %d clienti)"
               % (somma_clienti, len(pid_compositori)))


def p_platea_stabile(gpu, uid_miei):
    """⛔ R3 — la platea dei clienti DRM che cambia fra le due letture.

    ⭐ E si guarda per NOME, non per numero: un ricambio fra processi che non
       sono miei non falsa i miei numeri per pid; un ricambio fra i MIEI si'.
    """
    if gpu is None:
        return _muto("⛔ nessuna fotografia")
    sp, nu = gpu.get("spariti", 0), gpu.get("nuovi", 0)
    mio = [v for v in (gpu.get("spariti_chi") or []) + (gpu.get("nuovi_chi") or [])
           if v.get("uid") in uid_miei or v.get("uid") is None]
    if mio:
        return _no("⛔ LA PLATEA E' CAMBIATA E IL RICAMBIO E' MIO: %s ⇒ il "
                   "delta non e' di una popolazione sola.  ⚠ E' il difetto che "
                   "nel primo giro ha prodotto un'occupazione del −76 %%"
                   % " · ".join("%s pid %s uid %s"
                                % (v.get("comm"), v.get("pid"), v.get("uid"))
                                for v in mio[:4]))
    if sp or nu:
        return _si("⚠ ricambio ESTRANEO (%d spariti, %d nuovi, nessuno mio): i "
                   "miei numeri per pid reggono, il totale della macchina e' un "
                   "LIMITE INFERIORE e si dichiara" % (sp, nu))
    return _si("⭐ stessa platea di clienti DRM alle due letture (%d clienti)"
               % (gpu.get("macchina") or {}).get("clienti", 0))


def p_gt_ferma(gradini):
    """⛔ R2 — LA GT CHE SI MUOVE FRA I DUE GRADINI RENDE IL CONFRONTO NULLO.

    `gradini` = lista di (nome, riassunto_gt).  ⛔ `None` se manca un riassunto:
    «non so a che frequenza andava» non e' «andava alla stessa».
    """
    if len(gradini) < 2:
        return _muto("⛔ meno di due gradini da confrontare")
    val = []
    for nome, g in gradini:
        # ⛔ Si usa la frequenza QUANDO LA GT ERA SVEGLIA: e' quella che governa
        #    quanto tempo un fotogramma tiene occupato il motore (§CLOCK).  Una
        #    media che conta i campioni a 0 MHz risponde a un'altra domanda.
        f = None if not g else g.get("act_media_sveglia", g.get("act_media"))
        if f is None:
            return _muto("⛔ del gradino «%s» non ho una frequenza di GT SVEGLIA "
                         "(%s campioni svegli su %s): a GT spenta non c'e' "
                         "nessun orologio da confrontare, e la differenza fra i "
                         "gradini non e' un confronto fra pari"
                         % (nome, (g or {}).get("sveglia_campioni"),
                            (g or {}).get("campioni")))
        if (g.get("sveglia_campioni") or 0) < 3:
            return _muto("⛔ del gradino «%s» ho solo %d campioni con la GT "
                         "sveglia: troppo pochi per dire a che frequenza ha "
                         "lavorato" % (nome, g.get("sveglia_campioni") or 0))
        val.append((nome, f, g.get("bloccata")))
    lo = min(v[1] for v in val)
    hi = max(v[1] for v in val)
    if lo <= 0:
        return _muto("⛔ frequenza della GT nulla o negativa: non giudico")
    scarto = (hi - lo) / lo
    dett = " · ".join("%s %.0f MHz%s" % (n, f, " ⚠BLOCCATA" if b else "")
                      for n, f, b in val)
    if scarto > GT_TOLLERANZA:
        return _no("⛔ LA GT SI E' MOSSA FRA I GRADINI (%.1f %% > %.1f %%): "
                   "%s.  ⛔ `drm-engine-*` misura TEMPO, non lavoro, e a "
                   "frequenze diverse lo stesso lavoro da' numeri diversi di "
                   "un fattore fino a 3,8 ⇒ IL CONFRONTO NON VALE"
                   % (scarto * 100, GT_TOLLERANZA * 100, dett))
    return _si("⭐ GT ferma entro il %.1f %% fra i gradini: %s"
               % (scarto * 100, dett))


def p_ancora(gradino, precedente):
    """⛔ R4 — UN GRADINO NON SI LEGGE DAL GRADINO PRECEDENTE.

    Due ancore indipendenti, e servono tutt'e due:
      · la **finestra**: `t0` di questo gradino dev'essere dopo `t1` di quello
        prima, sull'orologio monotono della macchina;
      · la **marca**: il `giro` della scena di questo gradino dev'essere il
        nonce di QUESTO gradino, non quello di prima.
    """
    if gradino is None:
        return _muto("⛔ gradino mancante")
    t0, t1 = gradino.get("t0_mono"), gradino.get("t1_mono")
    if t0 is None or t1 is None:
        return _muto("⛔ del gradino non ho la finestra: non posso ancorarlo")
    if t1 <= t0:
        return _no("⛔ finestra impossibile: t1 (%.3f) <= t0 (%.3f)" % (t1, t0))
    if precedente is not None:
        p1 = precedente.get("t1_mono")
        if p1 is None:
            return _muto("⛔ del gradino precedente non ho la fine")
        if t0 < p1:
            return _no("⛔ QUESTO GRADINO SI SOVRAPPONE AL PRECEDENTE: comincia "
                       "a %.3f mentre quello finiva a %.3f ⇒ starebbe leggendo "
                       "i suoi numeri" % (t0, p1))
    atteso = gradino.get("nonce")
    if atteso is not None:
        visti = set()
        for nome, v in (gradino.get("cambi") or {}).items():
            if v.get("giro"):
                visti.add(v["giro"])
        if visti and not all(atteso in g for g in visti):
            return _no("⛔ LA MARCA NON E' DI QUESTO GRADINO: aspettavo «%s», "
                       "le scene dicono %s ⇒ sto leggendo un altro giro"
                       % (atteso, sorted(visti)))
    return _si("⭐ finestra [%.3f, %.3f] dopo il gradino prima%s"
               % (t0, t1, "" if gradino.get("nonce") is None
                  else ", e la marca e' «%s»" % gradino["nonce"]))


def p_sollecitazione_arrivata(cambi, chiesto_mpx_s):
    """⛔ `LEZIONI.md` §1.30 — quanta sollecitazione e' ARRIVATA.
       Una prova che non morde da' un giudizio che sembra un risultato."""
    tot = cambio_totale(cambi)
    if tot is None:
        return _muto("⛔ non so quanto sia cambiato: non giudico")
    if chiesto_mpx_s is None or chiesto_mpx_s <= 0:
        return _muto("[?] non c'e' un chiesto con cui confrontare")
    q = tot / chiesto_mpx_s
    if q < 0.5:
        return _no("⛔ e' ARRIVATO solo il %.0f %% del cambiamento chiesto "
                   "(%.1f su %.1f Mpixel/s): la prova non morde"
                   % (q * 100, tot, chiesto_mpx_s))
    return _si("⭐ arrivato il %.0f %% del chiesto (%.1f su %.1f Mpixel/s)"
               % (q * 100, tot, chiesto_mpx_s))


def p_estranei_zitti(attr):
    """⭐ L'isolamento MISURATO, non supposto: se sulla GPU lavora qualcuno che
       non e' mio, il numero non e' mio."""
    if attr is None or attr.get("esito") is None:
        return _muto("⛔ nessuna attribuzione")
    e = attr.get("estranei_render")
    if e is None:
        return _muto("⛔ il render degli estranei e' None: non giudico")
    if e > 2.0:
        return _no("⛔ ESTRANEI SULLA GPU: %.2f %% di `rcs0` non e' mio (%s) ⇒ "
                   "il numero di questo gradino non e' del mio carico"
                   % (e, attr.get("estranei_chi")))
    return _si("⭐ estranei su `rcs0`: %.2f %% (%d clienti)"
               % (e, attr.get("n_estranei", 0)))


def p_conti_tornano(attr):
    """⭐ La somma dei padroni contro il totale della macchina.  ⛔ Se non
       tornano, uno dei due e' sbagliato e non si sa quale: `None`."""
    if attr is None or attr.get("esito") is None:
        return _muto("⛔ nessuna attribuzione")
    if attr.get("totale_e_limite_inferiore"):
        return _muto("⚠ %d clienti DRM estranei sono nati o morti nella "
                     "finestra ⇒ il totale della macchina e' un limite "
                     "inferiore e i conti NON devono tornare: non giudico"
                     % attr["ricambio_estraneo"])
    pezzi = [attr.get("compositore_render"), attr.get("conversione_render"),
             attr.get("estranei_render")]
    tot = attr.get("macchina_render")
    if any(x is None for x in pezzi) or tot is None:
        return _muto("⛔ un pezzo o il totale sono None: non giudico")
    somma = sum(pezzi)
    if abs(somma - tot) > 0.5:
        return _no("⛔ i conti non tornano: i padroni sommano %.2f %%, la "
                   "macchina dice %.2f %%" % (somma, tot))
    return _si("⭐ i padroni sommano %.2f %% e la macchina dice %.2f %%"
               % (somma, tot))


# ───────────────────────────────────────────────────────────────────────────
# La retta — ⭐ e il suo errore, che senza non e' una legge
# ───────────────────────────────────────────────────────────────────────────

def retta(punti):
    """Minimi quadrati su (x, y).  ⛔ `None` con meno di tre punti o con
       tutte le x uguali: due punti danno sempre una retta perfetta, e una
       retta perfetta senza errore non e' una legge."""
    punti = [(x, y) for x, y in punti if x is not None and y is not None]
    if len(punti) < 3:
        return None
    n = len(punti)
    sx = sum(p[0] for p in punti)
    sy = sum(p[1] for p in punti)
    sxx = sum(p[0] * p[0] for p in punti)
    sxy = sum(p[0] * p[1] for p in punti)
    den = n * sxx - sx * sx
    if abs(den) < 1e-12:
        return None
    a = (n * sxy - sx * sy) / den
    b = (sy - a * sx) / n
    res = [y - (a * x + b) for x, y in punti]
    rms = math.sqrt(sum(r * r for r in res) / n)
    # ⭐ R², per dire se la retta spiega davvero o se e' un caso
    my = sy / n
    sst = sum((y - my) ** 2 for _, y in punti)
    r2 = None if sst <= 0 else 1.0 - sum(r * r for r in res) / sst
    return {"pendenza": a, "intercetta": b, "rms": rms, "r2": r2, "n": n,
            "residui": res}


# ───────────────────────────────────────────────────────────────────────────
# ⭐ LE SESSIONI — si aprono una alla volta, e ciascuna porta la SUA scena
# ───────────────────────────────────────────────────────────────────────────
#
# ⛔ Non si riscrive quel che `10-b92-dieci.py` ha gia' certificato: il cliente
#    che scrive il giornale una riga per fotogramma e il ritaglio della fetta si
#    PRENDONO da li' (`CLIENTE`, `FETTA`) e si spediscono nel MIO lavoro.

def _pezzi_di_b92():
    """⭐ I due copioni gia' certificati di `10-b92`.  ⛔ Se quel file non c'e'
       o e' cambiato in modo da non portarli piu', ci si ferma: indovinarne una
       copia vorrebbe dire misurare con un cliente che nessuno ha certificato."""
    percorso = os.path.join(QUI, "10-b92-dieci.py")
    if not os.path.exists(percorso):
        return None, "⛔ manca %s: non ho il cliente certificato" % percorso
    testo = open(percorso, encoding="utf-8").read()
    fuori = {}
    for nome in ("CLIENTE", "FETTA"):
        m = re.search(r"^%s = r'''(.*?)'''" % nome, testo, re.S | re.M)
        if not m:
            return None, ("⛔ in %s non trovo il copione «%s»: non lo riscrivo"
                          % (percorso, nome))
        fuori[nome] = m.group(1)
    return fuori, None


def giornale_di(i):
    return "%s/giornale-%d.jsonl" % (LAV, i)


def registro_di(i):
    return "%s/cliente-%d.log" % (LAV, i)


def cerca_giornale(i):
    """⛔ La stringa che SOLO quel cliente porta nella riga di comando.  ⚠ La
       classe `[/]` non e' un vezzo: senza, `pgrep -f` combacia con la propria
       riga di comando."""
    return "--giornale [/]srv/remotix/tmp/%s/giornale-%d.jsonl" % (
        os.path.basename(DENTRO_LAV), i)


def vivo(i):
    rc, out, _ = root("pgrep -f -- '%s' >/dev/null 2>&1 && echo vivo || echo morto"
                      % cerca_giornale(i))
    return "vivo" in out


def apri_sessione(i, resta_s, tetto=240):
    """⛔ Torna `(True, …)` SOLO quando il registro porta la riga «SESSIONE».
       Un processo che esiste non e' una sessione aperta (`LEZIONI.md` §1.9)."""
    u, log = utente(i), registro_di(i)
    seg = "%s/segnale-%d" % (LAV, i)
    root("rm -f %s %s %s" % (log, giornale_di(i), seg))
    dentro = ("python3 -u %s/10-b92-cliente.py "
              "--cliente %s/banchi/01-b3-cliente.py --giornale %s "
              "--indirizzo %s --porta %d --utente %s --parola-file %s/parola "
              "--tela %s --video-codec %s --audio-codec pcm --resta %d "
              "--segnale %s"
              % (DENTRO_LAV, DENTRO_ALB, DENTRO_LAV + "/giornale-%d.jsonl" % i,
                 IND, PORTA, u, DENTRO_LAV, TELA, CODEC_CHIESTO, int(resta_s),
                 DENTRO_LAV + "/segnale-%d" % i))
    t_avvio = time.monotonic()
    root("setsid nohup bash /media/REMOTIX/enter.sh --root %s >> %s 2>&1 & "
         "echo avviato" % (shlex.quote(dentro), log))
    GRAZIA = 12
    for giro in range(tetto):
        time.sleep(1.0)
        rc, out, _ = root("test -f %s && echo si || echo no" % seg)
        if "si" in out:
            rc, out, _ = root("grep -am1 SESSIONE %s || true" % log)
            return True, ("aperta in %.1f s · %s"
                          % (time.monotonic() - t_avvio, out.strip()[:120]))
        if giro >= GRAZIA and not vivo(i):
            rc, out, _ = root("tail -20 %s || true" % log)
            return False, ("⛔ il cliente %d e' MORTO prima di aprire la "
                           "sessione — il suo registro:\n%s" % (i, out[-800:]))
    rc, out, _ = root("tail -20 %s || true" % log)
    return False, ("⛔ la sessione %d NON si e' aperta in %d s:\n%s"
                   % (i, tetto, out[-800:]))


def stacca(i):
    """⛔ Stacca il CLIENTE e lascia in piedi il PALCO.  ⭐ E' il gradino 1: il
       desktop e' vivo e nessuno guarda.  Torna `True` se il cliente e' sparito
       davvero — non se il comando e' stato dato."""
    root("pkill -f -- '%s'; true" % cerca_giornale(i))
    for _ in range(40):
        time.sleep(0.5)
        if not vivo(i):
            return True
    return False


def uscita_del(i):
    """Il monitor su cui la scena deve andare, CHIESTO al compositore
       (`CODER.md` §3.9: si chiede per nome, non si deduce dal registro)."""
    n = uid(i)
    rc, out, err = root(
        "setpriv --reuid=%d --regid=%d --init-groups env -i HOME=/home/%s "
        "USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
        "XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 %s --uscite"
        % (n, n, utente(i), utente(i), n, SCENA_BIN), 60)
    nomi = re.findall("«([^»]+)»", out + err)
    return nomi[0] if nomi else None


def nome_shm(i, tag=None):
    return "10b95-%d" % i if tag is None else "10b95-%d-%s" % (i, tag)


def spegni_scena(i, shm=None):
    """⛔ Se `shm` e' dato, si spegne SOLO quella scena; se no, tutte quelle
       dell'utente.  ⚠ La distinzione serve al modo `ritmi`, dove la scena
       nuova si accende PRIMA che la vecchia muoia."""
    if shm is None:
        root("pkill -u %d -f '04-b30-scena --uscita'; true" % uid(i))
        root("rm -f /dev/shm/10b95-%d /dev/shm/10b95-%d-*; true" % (uid(i) - UID_BASE,
                                                                   uid(i) - UID_BASE))
    else:
        root("pkill -u %d -f -- '--shm [/]%s '; true" % (uid(i), shm))
    # ⛔ Il blocco condiviso di una scena uccisa resta con `seq` DISPARI per
    #    sempre (`03-marca.py`): un lettore lo troverebbe «relitto» invece che
    #    «assente», e sono due diagnosi diverse.  ⇒ si toglie.
    if shm is not None:
        time.sleep(1.0)
        root("rm -f /dev/shm/%s; true" % shm)


def accendi_scena(i, movimento="pieno", finestra=None, nonce="x", shm=None):
    """⭐ La scena, col suo movimento e la sua finestra dichiarati, e la MARCA
       del gradino nel nome del giro.  ⛔ `None` se non e' partita in tre
       tentativi: una scena che non parte deve poter dire perche'."""
    n = uid(i)
    shm = shm or nome_shm(i)
    log = "%s/scena-%d.log" % (LAV, i)
    opz = "--movimento %s" % movimento
    if finestra:
        opz += " --finestra %dx%d" % finestra
    for tentativo in range(3):
        usc = uscita_del(i)
        if not usc:
            time.sleep(3.0)
            continue
        root("setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
             "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
             "XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 "
             "%s --uscita %s %s --shm /%s --giro %s "
             ">> %s 2>&1 & echo acceso"
             % (n, n, utente(i), utente(i), n, SCENA_BIN, usc, opz,
                shm, nonce, log))
        time.sleep(2.5)
        # ⛔ «C'e' un processo» non e' «questa scena e' viva»: si cerca il MIO
        #    blocco condiviso nella riga di comando, non una scena qualsiasi.
        rc, out, _ = root("pgrep -u %d -f -- '--shm [/]%s ' | head -1" % (n, shm))
        if out.strip():
            return usc
        rc, out, _ = root("tail -3 %s 2>/dev/null || true" % log)
        _dub("⚠ la scena di s%d non e' partita al tentativo %d — dice: %s"
             % (i, tentativo + 1, out.strip()[-160:]))
        time.sleep(3.0)
    return None


def byte_per_fotogramma(i, t0_ms, t1_ms):
    """⭐ Il secondo pilastro del predicato dello schermo fermo, e viene dal
       FILO, non dalla scena.  ⛔ `None` se non c'e' giornale o non ci sono
       fotogrammi nella finestra: non zero."""
    rc, out, _ = root("python3 %s/10-b92-fetta.py %s %.3f %.3f"
                      % (LAV, giornale_di(i), t0_ms, t1_ms), 180)
    try:
        d = json.loads(out.strip().splitlines()[-1])
    except Exception:
        return None, None
    if d.get("esito") != "letto":
        return None, None
    g = d.get("giornale") or []
    if not g:
        return None, 0
    byte = sum(x["byte"] for x in g)
    return byte / len(g), len(g)


# ───────────────────────────────────────────────────────────────────────────
# Il terreno, e il lucchetto
# ───────────────────────────────────────────────────────────────────────────

def _lucchetto():
    percorso = os.path.join(QUI, "09-lucchetto.py")
    os.environ["LUCCHETTO"] = LUCCHETTO
    return _carica("luc", percorso)


def porte_altrui():
    """⭐ Le porte 7xxx/8xxx di ALTRI agenti che sono in ascolto adesso.

    ⛔ Si DICHIARANO, non si nascondono, ed e' la regola scritta in testa a
       `10-b0-terreno.sh`: *«§1.26 vieta di misurare in due, non di tenere acceso
       il termine di paragone: per questo le porte tollerate si dichiarano da
       fuori e si STAMPANO»*.
    ⚠ E la protezione vera non e' questa lista: e' il **lucchetto della GPU**.
       Un server acceso e fermo non falsa niente; un server che MISURA si', e
       quello lo governa il lucchetto, non `ss`.
    ⛔ `None` se non le ho lette: allora non si dichiara niente e il terreno
       dara' rosso, che e' giusto.
    """
    rc, out, _ = rem("ss -uln 2>/dev/null | grep -oE ':(7[0-9]{3}|8[0-9]{3}) ' "
                     "| tr -d ': ' | sort -u", 60)
    if rc != 0:
        return None
    trovate = [x for x in out.split() if x.isdigit() and x != str(PORTA)]
    return trovate


def _ambiente_terreno():
    amb = dict(os.environ)
    amb.update({"PORTA": str(PORTA), "ALBERO": ALB, "LAV": LAV,
                "DENTRO_ALB": DENTRO_ALB, "DENTRO_LAV": DENTRO_LAV,
                "UNITA": UNITA, "MACCHINA": MACCHINA, "IND": IND,
                "PAROLA_SUDO": PAROLA_SUDO, "UTENTE": utente(1),
                "UID_B": str(uid(1))})
    return amb


def accendi_server():
    """⛔ Il MIO server, sulla MIA porta, con la MIA unita'.  Non se ne riscrive
       una riga: il file certificato e' `07-b64-terreno.sh`, e gli si passa il
       mio ambiente (`09-b86`).

    ⚠ `--niente-linea-morta` NON si mette: le cure della fase 9 restano ACCESE
      per predefinito (`CODER.md` §2-bis).  ⛔ Se un giro dovesse spegnerle, lo
      dichiara — e questo banco non lo fa: le scene di questo banco disegnano
      sempre, quindi la linea morta non ha ragione di scattare."""
    _log("IL MIO SERVER sulla %d — unita' %s" % (PORTA, UNITA))
    _inf("⭐ le cure della fase 9 restano ACCESE per predefinito (CODER.md §2-bis)")
    p = subprocess.run(["bash", os.path.join(QUI, "07-b64-terreno.sh"), "accendi"],
                       env=_ambiente_terreno(), capture_output=True, timeout=600)
    testo = (p.stdout + p.stderr).decode("utf-8", "replace")
    print(testo[-2500:])
    if p.returncode != 0:
        _ko("⛔ il server non si e' acceso (esce %d)" % p.returncode)
        return False
    return True


def terreno(quanti, palco_ammesso=False):
    """⛔ Il controllo del terreno PRIMA di ogni giro da cui esce un numero."""
    _log("IL TERRENO — ⛔ prima di ogni giro da cui esce un numero")
    altrui = porte_altrui()
    if altrui is None:
        _ko("⛔ non ho potuto leggere le porte in ascolto: non dichiaro niente "
            "e lascio che il terreno dia rosso")
        altrui = []
    _inf("⚠ porte 7xxx/8xxx di ALTRI agenti, in ascolto adesso e TOLLERATE: %s"
         % (" ".join(altrui) or "nessuna"))
    _inf("   ⛔ tollerate perche' §1.26 vieta di MISURARE in due, non di tenere "
         "acceso un server fermo — e chi misura lo governa il LUCCHETTO, che e' "
         "mio, non questa lista")
    amb = dict(os.environ)
    amb.update({"CHI": IO_SONO, "PORTA": str(PORTA), "UTENTE": utente(1),
                "ALBERO": ALB, "LAV": LAV, "LUCCHETTO": LUCCHETTO,
                "LUCCHETTO_MIO": "1", "MACCHINA": MACCHINA,
                "PAROLA_SUDO": PAROLA_SUDO, "IND": IND,
                "PORTE_AMMESSE": " ".join(altrui),
                "PALCO_AMMESSO": "1" if palco_ammesso else "0"})
    p = subprocess.run(["bash", os.path.join(QUI, "10-b0-terreno.sh")],
                       env=amb, capture_output=True, timeout=600)
    testo = p.stdout.decode("utf-8", "replace")
    print(testo[-4000:])
    if p.returncode != 0:
        _ko("⛔ 10-b0-terreno.sh esce %d: NON misuro" % p.returncode)
        return False
    _ok("10-b0-terreno.sh: il terreno regge")

    _log("I PALCHI ORFANI — ⛔ un palco vecchio non da' rosso, da' un numero "
         "plausibile")
    amb2 = dict(os.environ)
    amb2.update({"PORTA": str(PORTA), "ALBERO": ALB, "LAV": LAV,
                 "DENTRO_ALB": DENTRO_ALB, "DENTRO_LAV": DENTRO_LAV,
                 "UNITA": UNITA, "MACCHINA": MACCHINA,
                 "PAROLA_SUDO": PAROLA_SUDO})
    p2 = subprocess.run(["bash", os.path.join(QUI, "10-b91-terreno-dieci.sh"),
                         "stato"], env=amb2, capture_output=True, timeout=600)
    t2 = p2.stdout.decode("utf-8", "replace")
    print(t2[-4000:])
    if p2.returncode != 0 and not palco_ammesso:
        _ko("⛔ il terreno dei dieci non regge (esce %d): NON misuro"
            % p2.returncode)
        return False
    return True


def pulisci_fra_fasi():
    """⭐ Fra una fase e l'altra: via i MIEI clienti, le MIE scene e i palchi
       condivisi — ⛔ ma il server resta acceso e il lucchetto resta in mano.

    ⚠ Non e' lo sgombro: e' il ritorno al punto di partenza fra due fasi dello
      STESSO giro, cosi' che la fase dopo non erediti i palchi della fase
      prima (che e' esattamente la forma del «palco orfano»)."""
    _log("PULISCO FRA LE FASI — ⛔ i palchi della fase prima non si ereditano")
    for i in range(1, UTENTI_MAX + 1):
        root("pkill -f -- '%s'; true" % cerca_giornale(i))
        spegni_scena(i)
    amb = dict(os.environ)
    amb.update({"PORTA": str(PORTA), "ALBERO": ALB, "LAV": LAV,
                "DENTRO_ALB": DENTRO_ALB, "DENTRO_LAV": DENTRO_LAV,
                "UNITA": UNITA, "MACCHINA": MACCHINA, "PAROLA_SUDO": PAROLA_SUDO})
    subprocess.run(["bash", os.path.join(QUI, "10-b91-terreno-dieci.sh"),
                    "sgombra"], env=amb, timeout=600)
    time.sleep(3.0)


def sgombra():
    """⛔ Come si lascia la macchina: i MIEI clienti, le MIE scene, i palchi
       condivisi, la MIA unita'.  E si VERIFICA, non si dichiara a memoria."""
    _log("SGOMBRO — ⛔ col lucchetto ancora in mano")
    for i in range(1, UTENTI_MAX + 1):
        root("pkill -f -- '%s'; true" % cerca_giornale(i))
        spegni_scena(i)
    amb = dict(os.environ)
    amb.update({"PORTA": str(PORTA), "ALBERO": ALB, "LAV": LAV,
                "DENTRO_ALB": DENTRO_ALB, "DENTRO_LAV": DENTRO_LAV,
                "UNITA": UNITA, "MACCHINA": MACCHINA, "PAROLA_SUDO": PAROLA_SUDO})
    subprocess.run(["bash", os.path.join(QUI, "10-b91-terreno-dieci.sh"),
                    "sgombra"], env=amb, timeout=600)
    subprocess.run(["bash", os.path.join(QUI, "07-b64-terreno.sh"), "spegni"],
                   env=amb, timeout=300)
    # ⛔ E la GT si rimette com'era SEMPRE, anche se il giro e' andato storto.
    g = gt_comanda("rimetti")
    if g:
        _inf("GT rimessa: min=%s max=%s (RPn %s, RP0 %s)"
             % (g["dopo"].get("min_mhz"), g["dopo"].get("max_mhz"),
                g.get("rpn"), g.get("rp0")))
    rc, out, _ = rem("ss -uln | grep -c ':%d ' ; pgrep -c -f 'remotix.*--porta "
                     "%d' || true" % (PORTA, PORTA))
    _inf("verifica: ascoltatori sulla %d e processi miei → %s"
         % (PORTA, out.strip().replace("\n", " / ")))
    return 0


# ───────────────────────────────────────────────────────────────────────────
# Il rapporto di un gradino
# ───────────────────────────────────────────────────────────────────────────

def riga_gradino(nome, g):
    """Una riga sola, e porta SEMPRE il contesto accanto al numero: senza
       frequenza della GT e RC6 una percentuale di occupazione e' ambigua."""
    attr = g.get("attr") or {}
    gt = g.get("gt") or {}
    # ⛔ Un «[?]» senza il perche' e' un buco che rassicura: si dice sempre
    #    perche' non c'e' il numero.
    if attr.get("esito") is None and attr.get("perche"):
        print("  %-22s ⛔ %s" % (nome, attr["perche"]), flush=True)
    if g.get("gpu_perche"):
        print("  %-22s ⛔ %s" % (nome, g["gpu_perche"]), flush=True)
    def n(v, f="%6.2f"):
        return "  [?]  " if v is None else (f % v)
    print("  %-22s rcs0 tot %s  compos %s  conver %s  vcs %s  "
          "| cambio %s Mpx/s | GT %s MHz%s  RC6 %s %%"
          % (nome,
             n(attr.get("macchina_render")),
             n(attr.get("compositore_render")),
             n(attr.get("conversione_render")),
             n(attr.get("codifica_video")),
             n(g.get("cambio_mpx_s"), "%7.2f"),
             n(gt.get("act_media_sveglia"), "%6.0f"),
             " ⚠BLOC" if gt.get("bloccata") else "      ",
             n(rc6_di(g.get("gpu")), "%5.1f")), flush=True)


def confeziona(mis, uid_miei, nonce=None, chiesto=None):
    """Dalla risposta grezza della macchina al gradino, con tutto il contesto.
       ⛔ `None` se la finestra non e' tornata."""
    if mis is None:
        return None
    g = {"t0_mono": mis.get("t0_mono"), "t1_mono": mis.get("t1_mono"),
         "nonce": nonce, "gpu": mis.get("gpu"),
         "gpu_perche": mis.get("gpu_perche")}
    g["gt"] = gt_riassunto(mis.get("gt_campioni"))
    g["cambi"] = cambio_delle_scene(mis.get("scene_a"), mis.get("scene_b"))
    g["cambio_mpx_s"] = cambio_totale(g["cambi"])
    g["attr"] = attribuisci(mis.get("gpu"), uid_miei)
    g["chiesto_mpx_s"] = chiesto
    return g


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL MODO «scomponi» — LA SCALA, e la parte difficile e' la scomposizione
# ═══════════════════════════════════════════════════════════════════════════

def scomponi(a):
    esiti = {"modo": "scomponi", "gradini": [], "predicati": []}
    rossi, muti = [], []

    def registra(nome, esito, dove=""):
        passa, perche = esito
        esiti["predicati"].append({"nome": nome + dove, "passa": passa,
                                   "perche": perche})
        if passa is True:
            _ok("%s%s — %s" % (nome, dove, perche))
        elif passa is False:
            _ko("%s%s — %s" % (nome, dove, perche))
            rossi.append(nome + dove + " · " + perche)
        else:
            _dub("%s%s — %s" % (nome, dove, perche))
            muti.append(nome + dove + " · " + perche)

    i = a.utente_i
    uid_miei = {uid(i)}
    _log("LA SCALA — un utente (%s, uid %d), scena «pieno» a schermo intero"
         % (utente(i), uid(i)))
    _inf("⛔ I GRADINI 2 E 3 DELL'INCARICO NON ESISTONO IN QUESTO PRODOTTO e si "
         "dichiara invece di stimarli: `src/main.c` non ha nessuna opzione che "
         "accenda la sessione senza il codificatore, e il figlio costruisce "
         "cattura, conversione e codifica in un tratto solo.")
    _inf("⇒ Due gradini veri (G1 «nessuno collegato» · G4 «tutto»), e i padroni "
         "ricavati dall'attribuzione PER PID e PER MOTORE, che e' piu' fine "
         "della differenza fra gradini.")

    # ── G4 per primo: la sessione va aperta comunque, e il palco nasce li' ──
    ok, dett = apri_sessione(i, resta_s=a.secondi_sessione)
    if not ok:
        _ko(dett)
        return 1, esiti
    _ok("s%d %s" % (i, dett))
    nonce4 = "b95g4-%d" % int(time.time())
    usc = accendi_scena(i, "pieno", None, nonce4)
    if not usc:
        _ko("⛔ la scena di s%d non parte: NON misuro" % i)
        return 1, esiti
    _inf("scena «pieno» a schermo intero sul monitor %s · marca «%s»" % (usc, nonce4))
    time.sleep(ASSESTAMENTO_S)
    _inf("⚠ tolti %.0f s di assestamento (apertura, prima chiave, prima tela)"
         % ASSESTAMENTO_S)

    m4 = misura_finestra(a.finestra, [nome_shm(i)])
    g4 = confeziona(m4, uid_miei, nonce4)
    if g4 is None:
        _ko("⛔ la finestra di G4 non e' tornata: NON giudico")
        return 1, esiti
    bpf, nfot = byte_per_fotogramma(i, g4["t0_mono"] * 1000.0,
                                    g4["t1_mono"] * 1000.0)
    g4["byte_per_fotogramma"] = bpf
    g4["fotogrammi"] = nfot
    g4["nome"] = "G4 · il prodotto intero"
    esiti["gradini"].append(g4)

    # ── G1: si stacca il cliente e il palco resta ──
    _log("G1 — stacco il cliente: ⭐ il desktop resta vivo e nessuno guarda")
    if not stacca(i):
        _ko("⛔ il cliente %d non e' morto: G1 non sarebbe G1" % i)
        return 1, esiti
    # ⛔⛔ «Il cliente e' morto» NON e' «nessuno e' collegato».
    #
    # Il figlio `remotix` di quell'utente puo' restare in piedi per un po' dopo
    # che il cliente se n'e' andato — e finche' c'e', puo' ancora catturare e
    # codificare dentro una connessione morta.  ⇒ G1 misurato li' non sarebbe
    # «desktop vivo e nessuno collegato»: sarebbe «desktop vivo e il prodotto
    # che lavora per nessuno», che e' un'altra scena.
    # ⭐ Quindi si ASPETTA che il figlio se ne vada, e ⛔ se non se ne va lo si
    #   DICHIARA invece di misurare lo stesso — ed e' anche un fatto sul
    #   prodotto, non solo una precauzione del banco.
    figli_via, secondi_attesi = False, 0.0
    for _giro in range(45):
        time.sleep(2.0)
        secondi_attesi += 2.0
        rc, out, _ = root("pgrep -u %d -c -f 'remotix' || true" % uid(i))
        if out.strip() in ("0", ""):
            figli_via = True
            break
    esiti["figlio_via_dopo_s"] = (secondi_attesi if figli_via else None)
    if figli_via:
        _ok("⭐ i figli `remotix` di uid %d se ne sono andati dopo %.0f s dallo "
            "stacco ⇒ G1 e' davvero «nessuno collegato»" % (uid(i), secondi_attesi))
    else:
        rc, out, _ = root("pgrep -u %d -a -f 'remotix' | head -3 || true" % uid(i))
        _dub("⚠ dopo %.0f s il figlio `remotix` di uid %d E' ANCORA VIVO: G1 NON "
             "e' «nessuno collegato», e' «il prodotto che lavora per nessuno».  "
             "⛔ Lo dichiaro e il gradino porta questa riga addosso — %s"
             % (secondi_attesi, uid(i), out.strip()[:200]))
        muti.append("G1 · il figlio `remotix` non se n'e' andato in %.0f s: il "
                    "gradino non e' «nessuno collegato»" % secondi_attesi)
    rc, out, _ = root("pgrep -u %d -c -f 'gnome-shell' || true" % uid(i))
    _inf("`gnome-shell` di uid %d: %s  ⇒ il palco %s"
         % (uid(i), out.strip(), "e' in piedi" if out.strip() not in ("0", "")
            else "⛔ NON c'e' piu': G1 non e' misurabile"))
    nonce1 = "b95g1-%d" % int(time.time())
    # ⛔ La scena si RIACCENDE con la marca di QUESTO gradino: cosi' leggere il
    #    gradino precedente non e' un errore da evitare, e' impossibile.
    spegni_scena(i)
    usc = accendi_scena(i, "pieno", None, nonce1)
    if not usc:
        _dub("⚠ la scena di s%d non riparte senza cliente collegato — ed e' un "
             "FATTO, non un guasto del banco: si dichiara" % i)
    time.sleep(3.0)
    m1 = misura_finestra(a.finestra, [nome_shm(i)])
    g1 = confeziona(m1, uid_miei, nonce1)
    if g1 is None:
        _ko("⛔ la finestra di G1 non e' tornata: NON giudico")
        return 1, esiti
    g1["nome"] = ("G1 · desktop vivo, nessuno collegato" if figli_via
                  else "G1 · ⚠ desktop vivo, FIGLIO ANCORA VIVO")
    g1["figlio_via"] = figli_via
    esiti["gradini"].insert(0, g1)

    # ── Il rapporto ──
    _log("I DUE GRADINI — ⛔ e il contesto accanto a ogni numero")
    for g in esiti["gradini"]:
        riga_gradino(g["nome"], g)

    _log("I PREDICATI")
    registra("l'ancora di G4", p_ancora(g4, None), "")
    # ⛔ G1 si misura DOPO G4 (si stacca il cliente da una sessione aperta):
    #    l'ancora di G1 si confronta con G4, che e' il gradino prima NEL TEMPO,
    #    non nell'ordine in cui si stampano.
    registra("l'ancora di G1 (misurato DOPO G4)", p_ancora(g1, g4), "")
    registra("la platea dei clienti DRM · G1", p_platea_stabile(g1["gpu"], uid_miei))
    registra("la platea dei clienti DRM · G4", p_platea_stabile(g4["gpu"], uid_miei))
    registra("la GT ferma fra i gradini",
             p_gt_ferma([("G1", g1["gt"]), ("G4", g4["gt"])]))
    registra("la scena morde · G4",
             p_scena_morde(g4["cambi"], g4.get("byte_per_fotogramma"),
                           (g4.get("attr") or {}).get("macchina_render")))
    e_g1 = p_scena_morde(g1["cambi"], None,
                         (g1.get("attr") or {}).get("macchina_render"))
    registra("la scena morde · G1", e_g1)
    if e_g1[0] is False:
        _inf("⭐⭐ E QUEL ROSSO NON E' UN GUASTO DEL BANCO: E' LA RISPOSTA.")
        _inf("    Se a G1 la scena non consegna commit e `rcs0` resta scarico, "
             "vuol dire che ⛔ **senza nessuno collegato il compositore non "
             "compone affatto** — e allora il «costo del compositore da solo» "
             "non e' basso: NON ESISTE come grandezza separabile.")
        _inf("    ⇒ La cattura non e' un padrone che si aggiunge al "
             "compositore: e' quel che lo fa lavorare.  E il budget della fase "
             "non puo' scriverli come due voci che si sommano.")
        esiti["compositore_senza_consumatore"] = "non compone"
    registra("l'attribuzione e' giusta · G4",
             p_attribuzione_giusta(g4["gpu"], g4["attr"], uid_miei))
    registra("gli estranei stanno zitti · G4", p_estranei_zitti(g4["attr"]))
    registra("i conti tornano · G4", p_conti_tornano(g4["attr"]))

    # ── LA SCOMPOSIZIONE ──
    _log("⭐⭐ LA SCOMPOSIZIONE — di chi e' `rcs0`")
    a4, a1 = g4.get("attr") or {}, g1.get("attr") or {}
    comp1 = a1.get("compositore_render")
    comp4 = a4.get("compositore_render")
    conv4 = a4.get("conversione_render")
    cod4 = a4.get("codifica_video")
    def dillo(nome, v, nota=""):
        if v is None:
            _dub("%-46s [?] non misurato %s" % (nome, nota))
        else:
            _inf("%-46s %6.2f %% %s" % (nome, v, nota))
    dillo("il COMPOSITORE, nessuno collegato (rcs0)", comp1)
    dillo("il COMPOSITORE + la CATTURA, collegato (rcs0)", comp4)
    # ⛔⛔ LA DIFFERENZA FRA DUE GRADINI VALE SOLO SE LA GT NON SI E' MOSSA.
    #     `drm-engine-*` misura TEMPO, e a frequenze diverse lo stesso lavoro
    #     da' numeri diversi fino a un fattore 3,8 (§CLOCK).  ⇒ Se il predicato
    #     della GT non e' verde, la sottrazione NON si fa: si dichiara.
    gt_ok = p_gt_ferma([("G1", g1["gt"]), ("G4", g4["gt"])])[0]
    if comp1 is None or comp4 is None:
        dillo("⇒ la CATTURA (differenza)", None,
              "un capo dei due non e' misurato")
    elif gt_ok is not True:
        _dub("%-46s [?] NON la calcolo: la GT non e' confrontabile fra i due "
             "gradini, e una differenza fra tempi presi a frequenze diverse "
             "non e' una differenza di lavoro" % "⇒ la CATTURA (differenza)")
    else:
        dillo("⇒ la CATTURA (differenza)", comp4 - comp1,
              "⚠ e' l'UNICO modo di isolarla: Mutter consegna i fotogrammi "
              "dentro lo stesso processo")
    dillo("la CONVERSIONE di colore, nel figlio (rcs0)", conv4,
          "⭐ e il prodotto importa un dmabuf a copia zero")
    dillo("la CODIFICA, nel figlio (vcs, fondo scala %s00 %%)"
          % (a4.get("capacita_video") or "?"), cod4)
    esiti["scomposizione"] = {"compositore_solo": comp1,
                              "compositore_piu_cattura": comp4,
                              "cattura": (None if (comp1 is None or comp4 is None
                                                  or gt_ok is not True)
                                          else comp4 - comp1),
                              "cattura_gt_confrontabile": gt_ok,
                              "conversione": conv4, "codifica": cod4,
                              "cambio_mpx_s_G1": g1.get("cambio_mpx_s"),
                              "cambio_mpx_s_G4": g4.get("cambio_mpx_s")}

    esiti["rossi"], esiti["muti"] = rossi, muti
    return (1 if rossi else (3 if muti else 0)), esiti


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL MODO «ritmi» — IL COSTO AL VARIARE DI QUANTO CAMBIA, e la LEGGE
# ═══════════════════════════════════════════════════════════════════════════

def ritmi(a):
    esiti = {"modo": "ritmi", "punti": [], "predicati": []}
    rossi, muti = [], []
    i = a.utente_i
    uid_miei = {uid(i)}

    _log("I RITMI — ⭐ il costo di composizione al variare di QUANTO CAMBIA")
    _inf("⛔ Il ritmo NON si tocca: a cambiare e' la SUPERFICIE danneggiata per "
         "commit, che con `--movimento pieno --finestra LxA` vale L×A per "
         "costruzione (`04-b30-scena.c`).  ⇒ cambio [Mpx/s] = commit/s × L·A")

    ok, dett = apri_sessione(i, resta_s=a.secondi_sessione)
    if not ok:
        _ko(dett)
        return 1, esiti
    _ok("s%d %s" % (i, dett))

    # ⛔⛔ LA SCENA SI CAMBIA SENZA LASCIARE UN BUCO, e la ragione e' MISURATA.
    #
    # `[M]` 24 agosto 2026, primo giro di questo banco: fra un punto e l'altro
    # la scena veniva spenta e riaccesa, e in quel buco il desktop non cambiava
    # piu' niente ⇒ ⛔ **la «linea morta» della fase 9 ha chiuso la sessione**
    # (`causa=silenzio silenzio_ms=10044 persi=0`), e da li' in poi il palco non
    # c'era piu': tre punti su cinque persi con `wl_display_connect: Connection
    # refused`.  ⚠ Non era un guasto del banco soltanto: e' la stessa cura che
    # §6.3 del primo giro aveva gia' colto, vista una seconda volta.
    # ⇒ La scena NUOVA si accende PRIMA che la vecchia muoia, ciascuna col
    #   PROPRIO blocco condiviso (due scrittori su un blocco solo lo
    #   corromperebbero), e la vecchia si spegne per nome subito dopo.
    # ⭐ E le cure restano ACCESE: non si spegne la linea morta per far passare
    #   il banco — si toglie il buco che la faceva scattare.
    scala = list(SCALA_FINESTRE)
    precedente = None
    scena_prima = None
    for k, (L, A) in enumerate(scala):
        nonce = "b95r%dx%d-%d" % (L, A, int(time.time()))
        # ⛔ Se il cliente non c'e' piu', la sessione si RIAPRE e si dichiara:
        #    misurare il compositore di un palco senza sessione sarebbe un'altra
        #    scena con lo stesso nome.
        if not vivo(i):
            _dub("⚠ il cliente di s%d non e' vivo prima del punto %dx%d: "
                 "RIAPRO la sessione e lo dichiaro" % (i, L, A))
            muti.append("il cliente e' morto prima del punto %dx%d" % (L, A))
            ok2, dett2 = apri_sessione(i, resta_s=a.secondi_sessione)
            if not ok2:
                _ko(dett2)
                rossi.append("la sessione non si riapre al punto %dx%d" % (L, A))
                break
            scena_prima = None
        shm = nome_shm(i, "%d" % k)
        usc = accendi_scena(i, "pieno", (L, A), nonce, shm)
        if not usc:
            _dub("⚠ la scena %dx%d non parte: salto il punto" % (L, A))
            muti.append("finestra %dx%d · la scena non parte" % (L, A))
            continue
        if scena_prima:
            spegni_scena(i, scena_prima)
        scena_prima = shm
        time.sleep(a.assestamento)
        mis = misura_finestra(a.finestra, [shm])
        g = confeziona(mis, uid_miei, nonce)
        if g is None:
            _dub("⚠ la finestra %dx%d non e' tornata: salto il punto" % (L, A))
            muti.append("finestra %dx%d · la finestra di misura non torna" % (L, A))
            continue
        bpf, nfot = byte_per_fotogramma(i, g["t0_mono"] * 1000.0,
                                        g["t1_mono"] * 1000.0)
        g["byte_per_fotogramma"] = bpf
        g["fotogrammi"] = nfot
        g["nome"] = "pieno %dx%d" % (L, A)
        g["finestra_px"] = L * A
        # ⛔ IL CLIENTE DEV'ESSERE ANCORA LI'.  ⚠ Con una scena che cambia poco,
        #    la «linea morta» della fase 9 sfratta chi tace — `[M]` §6.3 del
        #    primo giro: desktop fermo, perdita ZERO, sessione chiusa a 10 s.
        #    Un punto misurato su una sessione sfrattata a meta' non e' un punto.
        g["cliente_vivo"] = vivo(i)
        if not g["cliente_vivo"]:
            _ko("⛔ il cliente di s%d NON e' piu' vivo dopo il punto %dx%d: "
                "questo punto non vale, e ⚠ e' la forma della «linea morta» "
                "che sfratta chi tace (§6.3 del primo giro)" % (i, L, A))
            rossi.append("il cliente e' morto durante il punto %dx%d" % (L, A))
        riga_gradino(g["nome"], g)
        e = p_ancora(g, precedente)
        if e[0] is False:
            _ko("l'ancora · %s — %s" % (g["nome"], e[1]))
            rossi.append("ancora " + g["nome"])
        elif e[0] is None:
            _dub("l'ancora · %s — %s" % (g["nome"], e[1]))
            muti.append("ancora " + g["nome"])
        e = p_platea_stabile(g["gpu"], uid_miei)
        if e[0] is False:
            _ko("la platea · %s — %s" % (g["nome"], e[1]))
            rossi.append("platea " + g["nome"])
        e = p_scena_morde(g["cambi"], None,
                          (g.get("attr") or {}).get("macchina_render"))
        if e[0] is False:
            _ko("la scena morde · %s — %s" % (g["nome"], e[1]))
            rossi.append("scena ferma " + g["nome"])
        e = p_estranei_zitti(g["attr"])
        if e[0] is False:
            _ko("gli estranei · %s — %s" % (g["nome"], e[1]))
            rossi.append("estranei sulla GPU " + g["nome"])
        # ⛔ `LEZIONI.md` §1.30 — quanta sollecitazione e' ARRIVATA.  Il chiesto
        #    e' 60 commit/s (il monitor virtuale) per la superficie della
        #    finestra: se ne arriva meno della meta', il punto non morde e la
        #    retta ci passerebbe sopra un numero che non e' quello che credo.
        g["chiesto_mpx_s"] = 60.0 * L * A / 1e6
        e = p_sollecitazione_arrivata(g["cambi"], g["chiesto_mpx_s"])
        if e[0] is False:
            _dub("la sollecitazione arrivata · %s — %s" % (g["nome"], e[1]))
            muti.append("sollecitazione %s · %s" % (g["nome"], e[1]))
        elif e[0] is True:
            _inf("sollecitazione: %s" % e[1])
        esiti["punti"].append(g)
        precedente = g

    # ── L'estremo «quasi ferma»: la marca sola, a schermo intero ──
    nonce = "b95rmarca-%d" % int(time.time())
    shm_m = nome_shm(i, "marca")
    usc = accendi_scena(i, "marca", None, nonce, shm_m) if vivo(i) else None
    if usc:
        if scena_prima:
            spegni_scena(i, scena_prima)
        time.sleep(a.assestamento)
        mis = misura_finestra(a.finestra, [shm_m])
        gm = confeziona(mis, uid_miei, nonce)
        if gm is not None:
            gm["nome"] = "marca (quasi ferma)"
            bpf, nfot = byte_per_fotogramma(i, gm["t0_mono"] * 1000.0,
                                            gm["t1_mono"] * 1000.0)
            gm["byte_per_fotogramma"] = bpf
            gm["fotogrammi"] = nfot
            riga_gradino(gm["nome"], gm)
            _inf("[?] la superficie cambiata di «marca» non e' L×A: non la "
                 "calcolo, e questo punto NON entra nella retta")
            esiti["estremo_marca"] = gm

    # ── LA GT: se si e' mossa fra i punti, la retta non e' fra numeri
    #    confrontabili, e si dichiara invece di tirarla lo stesso ──
    e = p_gt_ferma([(g["nome"], g["gt"]) for g in esiti["punti"]])
    if e[0] is True:
        _ok("la GT ferma fra i punti — %s" % e[1])
    elif e[0] is False:
        _ko("la GT ferma fra i punti — %s" % e[1])
        rossi.append("la GT si e' mossa fra i punti della retta")
    else:
        _dub("la GT ferma fra i punti — %s" % e[1])
        muti.append("la GT fra i punti")
    esiti["gt_confrontabile"] = e[0]

    # ── LA LEGGE ──
    _log("⭐⭐ LA LEGGE — il costo di composizione dipende da quanto cambia?")
    punti_c = [(g.get("cambio_mpx_s"),
                (g.get("attr") or {}).get("compositore_render"))
               for g in esiti["punti"]]
    r_comp = retta(punti_c)
    punti_t = [(g.get("cambio_mpx_s"),
                (g.get("attr") or {}).get("macchina_render"))
               for g in esiti["punti"]]
    r_tot = retta(punti_t)
    for nome, r in (("il COMPOSITORE (rcs0 di gnome-shell)", r_comp),
                    ("TUTTO `rcs0` della macchina", r_tot)):
        if r is None:
            _dub("%s: ⛔ meno di tre punti buoni ⇒ nessuna legge" % nome)
            muti.append("la legge di " + nome)
            continue
        _inf("%s:" % nome)
        _inf("    rcs0 %% = %.4f · cambio[Mpx/s] + %.3f   "
             "(rms %.3f punti · R² %s · n=%d)"
             % (r["pendenza"], r["intercetta"], r["rms"],
                "[?]" if r["r2"] is None else "%.4f" % r["r2"], r["n"]))
        if r["r2"] is not None and r["r2"] > 0.97 and abs(r["intercetta"]) < 5.0:
            _inf("    ⇒ ⭐ PROPORZIONALE: il costo segue quanto cambia, e il "
                 "budget si puo' calcolare in anticipo")
        elif r["r2"] is not None and r["r2"] > 0.97:
            _inf("    ⇒ ⚠ retta buona ma con un GRADINO di %.2f punti a "
                 "cambio zero: c'e' un costo fisso che non dipende da quanto "
                 "cambia" % r["intercetta"])
        else:
            _inf("    ⇒ ⛔ NON e' una retta (R² %s): il costo NON e' "
                 "proporzionale a quanto cambia"
                 % ("[?]" if r["r2"] is None else "%.3f" % r["r2"]))
    esiti["legge_compositore"] = r_comp
    esiti["legge_totale"] = r_tot

    if a.scrivi_legge and r_comp is not None:
        scrivi_legge(r_comp, esiti)

    esiti["rossi"], esiti["muti"] = rossi, muti
    return (1 if rossi else (3 if muti else 0)), esiti


def scrivi_legge(r, esiti):
    """⭐ `LEZIONI.md` §1.35: quel che si tara si lascia dove gli altri lo
       trovino.  ⇒ la legge va IN TESTA A QUESTO FILE, con la sua pendenza e
       il suo errore."""
    percorso = os.path.abspath(__file__)
    testo = open(percorso, encoding="utf-8").read()
    gt = None
    for g in esiti.get("punti", []):
        if g.get("gt") and g["gt"].get("act_media_sveglia"):
            gt = g["gt"]["act_media_sveglia"]
            break
    nuovo = (
        "  LEGGE ................ rcs0 %% = %.4f · cambio[Mpixel/s] + %.3f\n"
        "  PENDENZA ............. %.4f %% di `rcs0` per Mpixel/s cambiato\n"
        "  INTERCETTA ........... %.3f %% (il costo che resta a cambio zero)\n"
        "  ERRORE (rms) ......... %.3f punti su %d punti · R² %s\n"
        "  FERRO ................ Intel UHD 730 integrata (i5-13500T), "
        "GT ~%s MHz, `renderD128`\n"
        % (r["pendenza"], r["intercetta"], r["pendenza"], r["intercetta"],
           r["rms"], r["n"],
           "[?]" if r["r2"] is None else "%.4f" % r["r2"],
           "[?]" if gt is None else "%.0f" % gt))
    m = re.search(r"^  LEGGE \.+ .*?\n  PENDENZA .*?\n  INTERCETTA .*?\n"
                  r"  ERRORE .*?\n  FERRO .*?\n", testo, re.S | re.M)
    if not m:
        _dub("⚠ non trovo il riquadro della legge in testa al file: non lo "
             "riscrivo a caso")
        return
    open(percorso, "w", encoding="utf-8").write(
        testo[:m.start()] + nuovo + testo[m.end():])
    _ok("⭐ la legge e' scritta in testa a %s" % os.path.basename(percorso))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL MODO «rampa» — IL SOFFITTO: N desktop che compongono, fino a saturare
# ═══════════════════════════════════════════════════════════════════════════

def rampa(a):
    esiti = {"modo": "rampa", "gradini": [], "predicati": [],
             "gt_bloccata": a.gt}
    rossi, muti = [], []
    _log("LA RAMPA — N desktop veri che compongono, fino a saturare `rcs0`")
    _inf("⛔ A SATURAZIONE, non su una retta: `drm-engine-*` misura tempo "
         "occupato, e a carico leggero la GT sta bassa e ogni fotogramma occupa "
         "piu' tempo (fattore 3,8 fra 300 e 1550 MHz).")
    if a.gt:
        # ⛔ Si VERIFICA che sia bloccata, non si crede al comando dato: il
        #    blocco lo mette `principale` una volta per tutto il giro, e qui si
        #    rilegge dal sysfs.  «Chiesto» non e' «in vigore».
        g = gt_comanda(None)
        if g is None or not g.get("bloccata"):
            _ko("⛔ la GT NON risulta bloccata: NON dichiaro un giro «a GT "
                "bloccata» che non lo e'")
            return 1, esiti
        _ok("⚠ GT BLOCCATA a min=%s max=%s MHz — ⭐ dichiarato: e' la seconda "
            "strada per avere un numero confrontabile quando non si satura"
            % (g["dopo"].get("min_mhz"), g["dopo"].get("max_mhz")))

    uid_miei = set()
    scene = []
    precedente = None
    ferma = None
    for n in range(1, a.fino + 1):
        ok, dett = apri_sessione(n, resta_s=a.secondi_sessione)
        if not ok:
            _ko(dett)
            _ko("⛔ LA RAMPA SI FERMA a N=%d: una sessione che non si apre non "
                "e' un gradino con una sessione in meno" % n)
            rossi.append("la sessione %d non si apre" % n)
            break
        _ok("s%d %s" % (n, dett))
        uid_miei.add(uid(n))
        nonce = "b95n%d-%d" % (n, int(time.time()))
        # ⛔ TUTTE le scene si riaccendono a ogni gradino con la marca del
        #    gradino: cosi' nessun contatore viene dal gradino prima.
        for i in range(1, n + 1):
            spegni_scena(i)
        scene = []
        for i in range(1, n + 1):
            usc = accendi_scena(i, "pieno", None, nonce)
            if not usc:
                _dub("⚠ la scena di s%d non riparte al gradino %d" % (i, n))
                muti.append("gradino %d · la scena di s%d non riparte" % (n, i))
            scene.append(nome_shm(i))
        time.sleep(a.assestamento)
        mis = misura_finestra(a.finestra, scene)
        g = confeziona(mis, uid_miei, nonce)
        if g is None:
            _dub("⚠ la finestra del gradino %d non e' tornata" % n)
            muti.append("gradino %d · la finestra non torna" % n)
            continue
        g["nome"] = "N=%d" % n
        g["n"] = n
        bpf, nfot = byte_per_fotogramma(n, g["t0_mono"] * 1000.0,
                                        g["t1_mono"] * 1000.0)
        g["byte_per_fotogramma"] = bpf
        g["fotogrammi"] = nfot
        riga_gradino(g["nome"], g)
        e = p_ancora(g, precedente)
        if e[0] is False:
            _ko("l'ancora · N=%d — %s" % (n, e[1]))
            rossi.append("ancora N=%d" % n)
        e = p_platea_stabile(g["gpu"], uid_miei)
        if e[0] is False:
            _ko("la platea · N=%d — %s" % (n, e[1]))
            rossi.append("platea N=%d" % n)
        e = p_scena_morde(g["cambi"], g.get("byte_per_fotogramma"),
                          (g.get("attr") or {}).get("macchina_render"))
        if e[0] is False:
            _ko("la scena morde · N=%d — %s" % (n, e[1]))
            rossi.append("scena ferma N=%d" % n)
        elif e[0] is True and "SATURAZIONE" in (e[1] or ""):
            _inf("N=%d · %s" % (n, e[1]))
        # ⭐ L'isolamento MISURATO: se su `rcs0` lavora qualcuno che non e' mio,
        #    il soffitto che ne esce non e' della mia composizione.
        e = p_estranei_zitti(g["attr"])
        if e[0] is False:
            _ko("gli estranei · N=%d — %s" % (n, e[1]))
            rossi.append("estranei sulla GPU N=%d" % n)
        esiti["gradini"].append(g)
        precedente = g
        tot = (g.get("attr") or {}).get("macchina_render")
        if tot is not None and tot >= SATURO_RENDER and ferma is None:
            ferma = n
            _inf("⭐ `rcs0` ha passato il %.0f %% al gradino N=%d" % (SATURO_RENDER, n))
            if a.fermati_a_saturazione:
                _inf("mi fermo qui: il soffitto e' raggiunto")
                break

    # ── ⭐⭐ LA LEGGE, PRESA DALLA RAMPA PRIMA DELLA SATURAZIONE ──
    #
    # ⛔ Solo i gradini PRIMA che `rcs0` si riempia: oltre, il costo non puo'
    #    piu' crescere perche' il motore e' finito, e una retta tirata dentro la
    #    saturazione misurerebbe il tetto, non la pendenza.
    # ⚠ E questa retta risponde a una domanda DIVERSA da quella del modo
    #   `ritmi`: qui a crescere e' il NUMERO di desktop, li' e' quanto cambia
    #   UN desktop.  Non si mescolano.
    _log("⭐⭐ LA LEGGE DELLA RAMPA — il costo cresce col totale composto?")
    prima = [g for g in esiti["gradini"]
             if (g.get("attr") or {}).get("macchina_render") is not None
             and g["attr"]["macchina_render"] < SATURO_RENDER
             and g.get("cambio_mpx_s") is not None]
    r = retta([(g["cambio_mpx_s"], g["attr"]["macchina_render"]) for g in prima])
    esiti["legge_rampa"] = r
    if r is None:
        _dub("⛔ meno di tre gradini prima della saturazione ⇒ nessuna legge")
        muti.append("la legge della rampa")
    else:
        gtm = [g["gt"]["act_media_sveglia"] for g in prima
               if (g.get("gt") or {}).get("act_media_sveglia")]
        _inf("rcs0 %% = %.5f · cambio[Mpx/s] + %.3f   (rms %.3f · R² %s · n=%d)"
             % (r["pendenza"], r["intercetta"], r["rms"],
                "[?]" if r["r2"] is None else "%.5f" % r["r2"], r["n"]))
        _inf("    ⚠ e la GT su questi gradini stava fra %s e %s MHz: la "
             "pendenza vale A QUELLA frequenza, non in assoluto (§CLOCK)"
             % ("[?]" if not gtm else "%.0f" % min(gtm),
                "[?]" if not gtm else "%.0f" % max(gtm)))
        if r["pendenza"] > 0:
            _inf("    ⇒ ⭐ estrapolata a `rcs0` = 100 %%, la capacita' sarebbe "
                 "**%.0f Mpixel/s** a ~%s MHz"
                 % ((100.0 - r["intercetta"]) / r["pendenza"],
                    "[?]" if not gtm else "%.0f" % (sum(gtm) / len(gtm))))
            _inf("    ⛔ ma e' un'ESTRAPOLAZIONE: il numero che vale e' quello "
                 "misurato a saturazione, qui sotto")

    # ── IL SOFFITTO ──
    _log("⭐⭐ IL SOFFITTO DELLA COMPOSIZIONE")
    buoni = [g for g in esiti["gradini"] if g.get("cambio_mpx_s") is not None]
    if not buoni:
        _dub("⛔ nessun gradino con un cambiamento misurato: nessun soffitto")
        muti.append("nessun gradino misurato")
    else:
        migliore = max(buoni, key=lambda g: g["cambio_mpx_s"])
        _inf("il massimo di composizione passata: %.1f Mpixel/s al gradino %s"
             % (migliore["cambio_mpx_s"], migliore["nome"]))
        attr = migliore.get("attr") or {}
        _inf("    a quel gradino `rcs0` stava al %s %% e la GT a %s MHz%s"
             % ("[?]" if attr.get("macchina_render") is None
                else "%.2f" % attr["macchina_render"],
                "[?]" if not (migliore.get("gt") or {}).get("act_media_sveglia")
                else "%.0f" % migliore["gt"]["act_media_sveglia"],
                " ⚠BLOCCATA" if (migliore.get("gt") or {}).get("bloccata") else ""))
        esiti["soffitto"] = {"mpx_s": migliore["cambio_mpx_s"],
                             "gradino": migliore["nome"],
                             "rcs0": attr.get("macchina_render"),
                             "gt": (migliore.get("gt") or {}).get("act_media_sveglia"),
                             "gt_bloccata": (migliore.get("gt") or {}).get("bloccata")}
        if ferma is None:
            _dub("⚠ `rcs0` non ha mai passato il %.0f %%: quel che ho e' un "
                 "LIMITE INFERIORE del soffitto, non il soffitto"
                 % SATURO_RENDER)
            muti.append("`rcs0` non e' mai arrivato a saturazione")
    esiti["saturo_a"] = ferma
    esiti["rossi"], esiti["muti"] = rossi, muti
    return (1 if rossi else (3 if muti else 0)), esiti


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ LA CERTIFICAZIONE — un banco non e' finito finche' non lo si e' visto
#     dare ROSSO (`LEZIONI.md` §1.29)
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Ogni predicato ha il suo guasto innestato, e il guasto va FATTO GIRARE.
#    ⭐ Tutti i predicati di questo banco sono funzioni PURE su dizionari: si
#    guastano a mano, senza macchina, e il conto e' sano → guasto → risanato.

def _fab_pid(pid, comm, u, render, video, veh=0.0, cop=0.0):
    return {"pid": pid, "comm": comm, "uid": u, "render_pct": render,
            "video_pct": video, "video-enhance_pct": veh, "copy_pct": cop,
            "clienti": 1, "mem_kib": 1000}


def _fab_gpu(pids, clienti=None, spariti=0, nuovi=0, anomali=0,
             macchina_render=None, rc6=1.0, act=1350,
             spariti_chi=None, nuovi_chi=None):
    per_pid = {str(p["pid"]): p for p in pids}
    if clienti is None:
        clienti = [{"pid": p["pid"], "avvio": 7, "cid": str(p["pid"] * 10),
                    "comm": p["comm"], "render_pct": p["render_pct"],
                    "video_pct": p["video_pct"],
                    "video-enhance_pct": p["video-enhance_pct"],
                    "copy_pct": p["copy_pct"]} for p in pids]
    if macchina_render is None:
        vals = [p["render_pct"] for p in pids]
        macchina_render = None if any(v is None for v in vals) else sum(vals)
    return {"dt": 12.0, "capacita_video": 2, "radice": True,
            "macchina": {"parziale": False, "perche": [], "clienti": len(clienti),
                         "render_pct": macchina_render,
                         "video_pct": sum((p["video_pct"] or 0) for p in pids),
                         "video_uso_pct": 0.0, "mancanti": {}},
            "per_pid": per_pid, "per_cliente": clienti,
            "spariti": spariti, "nuovi": nuovi, "anomali": anomali,
            "spariti_chi": (spariti_chi if spariti_chi is not None
                            else [{"pid": 900 + k, "comm": "ffmpeg", "uid": 1999}
                                  for k in range(spariti)]),
            "nuovi_chi": (nuovi_chi if nuovi_chi is not None
                          else [{"pid": 950 + k, "comm": "ffmpeg", "uid": 1999}
                                for k in range(nuovi)]),
            "gt": {"rc6_pct": rc6, "sveglia_pct": 100 - rc6, "cur_mhz": act,
                   "act_mhz": act, "min_mhz": 300, "max_mhz": 1550,
                   "bloccata": False},
            "pdev": PDEV_BUONO, "nodo": "/dev/dri/renderD128"}


def _fab_scena(nome, commit0, commit1, dt=12.0, L=1920, A=1080,
               movimento="pieno", fidato=True, c_e=True, giro="b95x"):
    a = {"c_e": c_e, "fidato": fidato, "commit": commit0, "disegni": commit0,
         "attese": 0, "t_mono": 100.0, "larghezza": L, "altezza": A,
         "movimento": movimento, "danno": "pieno", "giro": giro,
         "refresh_hz": 60.0, "perche_non_fidato": [],
         "perche": None if c_e else "⛔ il blocco non esiste"}
    b = dict(a)
    b["commit"] = commit1
    b["disegni"] = commit1
    b["t_mono"] = 100.0 + dt
    return a, b


def certifica():
    print("═" * 78)
    print("⛔⛔ 10-b95 — I GUASTI INNESTATI.  Un banco non e' finito finche' non")
    print("     lo si e' visto dare ROSSO (`LEZIONI.md` §1.29)")
    print("═" * 78)
    esiti = []

    def caso(nome, atteso, ottenuto, passa):
        esiti.append((nome, bool(passa)))
        seg = ("%sOK%s" % (VERDE, GRIGIO)) if passa else ("%sNO%s" % (ROSSO, GRIGIO))
        print("  %s  %s" % (seg, nome))
        print("        atteso:  %s" % atteso)
        # ⚠ Un predicato torna `(esito, perche)`; una misura torna un numero o
        #   una tupla di numeri.  Si stampano tutt'e due senza indovinare.
        if (isinstance(ottenuto, tuple) and len(ottenuto) == 2
                and (ottenuto[0] is None or isinstance(ottenuto[0], bool))
                and (ottenuto[1] is None or isinstance(ottenuto[1], str))):
            testo = "%s — %s" % (ottenuto[0], (ottenuto[1] or "")[:150])
        else:
            testo = repr(ottenuto)
        print("        avuto:   %s" % testo)

    MIEI = {1110}
    GS = _fab_pid(101, "gnome-shell", 1110, 42.0, 0.0)
    FIG = _fab_pid(202, "remotix", 1110, 9.0, 13.0)

    # ═══════════════════════════════════════════════════════════════════════
    print("\n── 1 · ⛔ UN DESKTOP CHE NON COMPONE, dichiarato come scena che "
          "cambia ──")
    a, b = _fab_scena("s1", 1000, 1720)              # 60 commit/s
    vivo = cambio_delle_scene({"s1": a}, {"s1": b})
    caso("1a · sano: 60,0 commit/s ⇒ la scena morde",
         "True, e nomina i commit", p_scena_morde(vivo),
         p_scena_morde(vivo)[0] is True)
    caso("1a-bis · e il cambiamento vale 60 × 1920×1080 = 124,4 Mpixel/s",
         "124,4 ± 0,1", "%.1f" % vivo["s1"]["mpx_s"],
         abs(vivo["s1"]["mpx_s"] - 124.4) < 0.2)
    a, b = _fab_scena("s1", 1000, 1002)              # 0,17 commit/s
    fermo = cambio_delle_scene({"s1": a}, {"s1": b})
    e = p_scena_morde(fermo)
    caso("1b · GUASTO: schermo fermo (0,17 commit/s) dichiarato come scena "
         "che cambia",
         "False, e nomina «SCHERMO FERMO», NON «costo basso»", e,
         e[0] is False and "SCHERMO FERMO" in (e[1] or ""))
    e = p_scena_morde(vivo, byte_per_fotogramma=280.0)
    caso("1c · GUASTO: i commit ci sono ma il filo porta 280 B/fotogramma",
         "False, smascherato dai BYTE per fotogramma", e,
         e[0] is False and "byte per fotogramma" in (e[1] or ""))
    caso("1d · risanato: la stessa funzione su una scena che morde e con "
         "5 600 B/fotogramma", "True",
         p_scena_morde(vivo, 5600.0), p_scena_morde(vivo, 5600.0)[0] is True)
    # ⭐ IL TERZO PILASTRO — commit bassi con `rcs0` PIENO non sono uno schermo
    #   fermo: sono saturazione, ed e' il risultato che la rampa cerca
    e = p_scena_morde(fermo, None, 99.4)
    caso("1b-bis · ⭐ gli stessi 0,17 commit/s ma con `rcs0` al 99,4 %: NON e' "
         "uno schermo fermo, e' SATURAZIONE",
         "True, e lo dice col numero di rcs0", e,
         e[0] is True and "SATURAZIONE" in (e[1] or ""))
    e = p_scena_morde(fermo, None, 12.0)
    caso("1b-ter · e con `rcs0` al 12 % gli stessi commit tornano ROSSI",
         "False, «SCHERMO FERMO»", e,
         e[0] is False and "SCHERMO FERMO" in (e[1] or ""))
    e = p_scena_morde(fermo, None, None)
    caso("1b-quater · ⛔ e con `rcs0` NON LETTO si accusa lo stesso: «non so» "
         "non e' un salvacondotto",
         "False, e dice «non letto ⇒ accuso lo stesso»", e,
         e[0] is False and "accuso lo stesso" in (e[1] or ""))
    a, b = _fab_scena("s1", 1000, 1720, fidato=False)
    b["perche_non_fidato"] = ["⛔ 9 wl_surface.frame in volo"]
    nf = cambio_delle_scene({"s1": a}, {"s1": b})
    caso("1e · GUASTO: blocco NON fidato (corsa a vuoto) ⇒ None, non «ritmo alto»",
         "mpx_s = None e il predicato NON giudica",
         (nf["s1"]["mpx_s"], p_scena_morde(nf)[0]),
         nf["s1"]["mpx_s"] is None and p_scena_morde(nf)[0] is None)
    a, b = _fab_scena("s1", 5000, 12)     # ripartita a meta'
    ind = cambio_delle_scene({"s1": a}, {"s1": b})
    caso("1f · GUASTO: i commit vanno ALL'INDIETRO (la scena e' ripartita)",
         "mpx_s = None, mai un numero negativo",
         ind["s1"]["mpx_s"], ind["s1"]["mpx_s"] is None)

    # ═══════════════════════════════════════════════════════════════════════
    print("\n── 2 · ⛔ IL METRO CHE ATTRIBUISCE A `gnome-shell` IL LAVORO DI UN "
          "ALTRO CLIENTE DRM ──")
    sano = _fab_gpu([GS, FIG])
    at = attribuisci(sano, MIEI)
    caso("2a · sano: 42 % al compositore, 9 % alla conversione, 13 % alla codifica",
         "42,0 / 9,0 / 13,0",
         (at["compositore_render"], at["conversione_render"], at["codifica_video"]),
         (at["compositore_render"], at["conversione_render"],
          at["codifica_video"]) == (42.0, 9.0, 13.0))
    e = p_attribuzione_giusta(sano, at, MIEI)
    caso("2a-bis · e il predicato di attribuzione e' verde",
         "True", e, e[0] is True)
    # GUASTO: un cliente DRM in piu' sul pid del compositore, che non e' suo
    guasto = _fab_gpu([GS, FIG])
    guasto["per_cliente"].append({"pid": 101, "avvio": 7, "cid": "999",
                                  "comm": "gnome-shell", "render_pct": 30.0,
                                  "video_pct": 0.0, "video-enhance_pct": 0.0,
                                  "copy_pct": 0.0})
    e = p_attribuzione_giusta(guasto, attribuisci(guasto, MIEI), MIEI)
    caso("2b · GUASTO: un secondo cliente DRM (30 %) messo sul pid del "
         "compositore, che il conto per pid non ha",
         "False, e dice «ATTRIBUZIONE SBAGLIATA» col numero", e,
         e[0] is False and "ATTRIBUZIONE SBAGLIATA" in (e[1] or ""))
    # GUASTO: un gnome-shell di un ALTRO uid finisce fra i miei
    altro = _fab_pid(303, "gnome-shell", 1999, 55.0, 0.0)
    g2 = _fab_gpu([GS, FIG, altro])
    a2 = attribuisci(g2, MIEI)
    caso("2c · GUASTO: un `gnome-shell` di uid 1999 (non mio) sulla stessa GPU",
         "sta negli ESTRANEI (55 %), non fra i miei compositori (42 %)",
         (a2["compositore_render"], a2["estranei_render"]),
         a2["compositore_render"] == 42.0 and a2["estranei_render"] == 55.0)
    e = p_estranei_zitti(a2)
    caso("2c-bis · e il predicato degli estranei da' ROSSO",
         "False, e nomina chi", e, e[0] is False)
    caso("2d · risanato: senza l'estraneo il predicato torna verde",
         "True", p_estranei_zitti(attribuisci(sano, MIEI)),
         p_estranei_zitti(attribuisci(sano, MIEI))[0] is True)

    # ═══════════════════════════════════════════════════════════════════════
    print("\n── 3 · ⛔ LA PLATEA DEI CLIENTI DRM CHE CAMBIA ⇒ `None`, MAI una "
          "percentuale inventata ──")
    print("       ⚠ e' un difetto vero gia' pagato nel primo giro, dove ha "
          "prodotto un'occupazione del −76 %")
    caso("3a · sano: nessuno nasce, nessuno muore",
         "True", p_platea_stabile(sano, MIEI),
         p_platea_stabile(sano, MIEI)[0] is True)
    # ⛔ IL RICAMBIO **MIO** — quello che falsa i numeri
    morto = _fab_gpu([GS, FIG], spariti=1,
                     spariti_chi=[{"pid": 707, "comm": "gnome-shell", "uid": 1110}])
    e = p_platea_stabile(morto, MIEI)
    caso("3b · GUASTO: un cliente DRM MIO SPARITO fra le due letture",
         "False, e nomina il −76 % del primo giro", e,
         e[0] is False and "76" in (e[1] or ""))
    caso("3b-bis · e l'attribuzione si RIFIUTA: esito None, non un numero",
         "esito = None",
         attribuisci(morto, MIEI)["esito"],
         attribuisci(morto, MIEI)["esito"] is None)
    nato = _fab_gpu([GS, FIG], nuovi=2,
                    nuovi_chi=[{"pid": 708, "comm": "remotix", "uid": 1110},
                               {"pid": 709, "comm": "remotix", "uid": 1110}])
    caso("3c · GUASTO: due clienti DRM MIEI NUOVI fra le due letture",
         "esito = None", attribuisci(nato, MIEI)["esito"],
         attribuisci(nato, MIEI)["esito"] is None)
    # ⭐ IL RICAMBIO **ESTRANEO** — `[M]` 8 clienti spariti in 3 s su questa
    #    macchina, nessuno mio.  Rifiutarsi li' vorrebbe dire non misurare mai.
    estr = _fab_gpu([GS, FIG], spariti=8)
    ae = attribuisci(estr, MIEI)
    caso("3c-bis · ⭐ ricambio di 8 clienti ESTRANEI: i miei numeri per pid "
         "REGGONO e il totale della macchina si dichiara limite inferiore",
         "compositore = 42,0 e totale_e_limite_inferiore = True",
         (ae["esito"], ae["compositore_render"], ae["totale_e_limite_inferiore"]),
         ae["esito"] == "attribuito" and ae["compositore_render"] == 42.0
         and ae["totale_e_limite_inferiore"] is True)
    caso("3c-ter · e i conti NON si giudicano quando il totale e' un limite "
         "inferiore: None, non un rosso a un totale che non puo' tornare",
         "None", p_conti_tornano(ae), p_conti_tornano(ae)[0] is None)
    ce = _fab_gpu([GS, FIG], spariti=1,
                  spariti_chi=[{"pid": 777, "comm": "Xwayland", "uid": None}])
    caso("3c-quater · GUASTO: un cliente sparito di cui NON so l'uid ⇒ si tratta "
         "come MIO (prudente), non come estraneo",
         "esito = None", attribuisci(ce, MIEI)["esito"],
         attribuisci(ce, MIEI)["esito"] is None)
    anom = _fab_gpu([GS, FIG], anomali=1)
    caso("3d · GUASTO: un contatore anomalo (all'indietro o impossibile)",
         "esito = None", attribuisci(anom, MIEI)["esito"],
         attribuisci(anom, MIEI)["esito"] is None)
    caso("3e · risanato: la stessa funzione sulla fotografia sana",
         "esito = «attribuito»", attribuisci(sano, MIEI)["esito"],
         attribuisci(sano, MIEI)["esito"] == "attribuito")
    # ⛔ «non ho letto» ≠ zero
    cieco = _fab_pid(101, "gnome-shell", 1110, None, 0.0)
    gc = _fab_gpu([cieco, FIG])
    ac = attribuisci(gc, MIEI)
    caso("3f · GUASTO: il metro non ha letto il render del compositore",
         "compositore_render = None, MAI 0, e un buco dichiarato",
         (ac["compositore_render"], len(ac["buchi"])),
         ac["compositore_render"] is None and len(ac["buchi"]) >= 1)
    senza_uid = _fab_pid(404, "gnome-shell", None, 12.0, 0.0)
    gu = _fab_gpu([GS, FIG, senza_uid])
    au = attribuisci(gu, MIEI)
    caso("3g · GUASTO: un pid di cui NON si e' letto l'uid",
         "non entra fra i miei compositori (42, non 54) e si dichiara",
         (au["compositore_render"], len(au["buchi"])),
         au["compositore_render"] == 42.0 and len(au["buchi"]) >= 1)

    # ═══════════════════════════════════════════════════════════════════════
    print("\n── 4 · ⛔ LA GT CHE SI MUOVE FRA I DUE GRADINI ⇒ il confronto non "
          "vale, e il banco lo DICE ──")
    def _g(f, bloccata=False, svegli=24, campioni=24):
        return {"act_media": f, "act_media_sveglia": f, "bloccata": bloccata,
                "sveglia_campioni": svegli, "campioni": campioni}
    g_fermo = [("G1", _g(1350.0)), ("G4", _g(1352.0))]
    caso("4a · sano: 1350 e 1352 MHz (0,15 %)",
         "True", p_gt_ferma(g_fermo), p_gt_ferma(g_fermo)[0] is True)
    g_mosso = [("G1", _g(350.0)), ("G4", _g(1350.0))]
    e = p_gt_ferma(g_mosso)
    caso("4b · GUASTO: 350 MHz a G1 e 1350 a G4 (il caso del §CLOCK)",
         "False, e dice che il confronto NON VALE", e,
         e[0] is False and "NON VALE" in (e[1] or ""))
    e = p_gt_ferma([("G1", _g(None, svegli=0)), ("G4", _g(1350.0))])
    caso("4c · GUASTO: di un gradino non ho la frequenza",
         "None — «non so» non e' «uguale»", e, e[0] is None)
    caso("4d · risanato: due gradini a 1550 bloccati",
         "True", p_gt_ferma([("G1", _g(1550.0, True)), ("G4", _g(1549.0, True))]),
         p_gt_ferma([("G1", _g(1550.0, True)),
                     ("G4", _g(1549.0, True))])[0] is True)
    # ⛔⛔ LA GT SPENTA — `[M]` `gt_act_freq_mhz` vale 0 in RC6, e una media che
    #     conta gli zeri risponde a un'altra domanda
    e = p_gt_ferma([("G1", _g(1350.0, svegli=2, campioni=24)), ("G4", _g(1350.0))])
    caso("4e · GUASTO: un gradino ha solo 2 campioni con la GT sveglia su 24",
         "None, e dice che sono troppo pochi", e,
         e[0] is None and "troppo pochi" in (e[1] or ""))
    r0 = gt_riassunto([{"act_mhz": 0, "cur_mhz": 300, "min_mhz": 300,
                        "max_mhz": 1550}] * 20 +
                      [{"act_mhz": 1350, "cur_mhz": 1350, "min_mhz": 300,
                        "max_mhz": 1550}] * 4)
    caso("4f · ⭐ 20 campioni a GT SPENTA e 4 a 1350: la media di tutti dice "
         "225 MHz, quella dei SVEGLI dice 1350 — e il §CLOCK vuole la seconda",
         "act_media 225,0 · act_media_sveglia 1350,0 · frazione_sveglia 0,167",
         (round(r0["act_media"], 1), r0["act_media_sveglia"],
          round(r0["frazione_sveglia"], 3)),
         (round(r0["act_media"], 1), r0["act_media_sveglia"],
          round(r0["frazione_sveglia"], 3)) == (225.0, 1350.0, 0.167))

    # ═══════════════════════════════════════════════════════════════════════
    print("\n── 5 · ⛔ UN GRADINO LETTO DAL GRADINO PRECEDENTE — l'ancora che "
          "lo rende impossibile ──")
    a_, b_ = _fab_scena("s1", 1000, 1720, giro="b95n2-777")
    g_prec = {"t0_mono": 100.0, "t1_mono": 112.0, "nonce": "b95n1-777",
              "cambi": {}}
    g_ora = {"t0_mono": 120.0, "t1_mono": 132.0, "nonce": "b95n2-777",
             "cambi": cambio_delle_scene({"s1": a_}, {"s1": b_})}
    caso("5a · sano: il gradino comincia dopo che il precedente e' finito, e la "
         "marca e' la sua",
         "True", p_ancora(g_ora, g_prec), p_ancora(g_ora, g_prec)[0] is True)
    g_sovr = dict(g_ora); g_sovr["t0_mono"] = 105.0
    e = p_ancora(g_sovr, g_prec)
    caso("5b · GUASTO: la finestra si SOVRAPPONE a quella del gradino prima",
         "False, e dice che starebbe leggendo i suoi numeri", e,
         e[0] is False and "SOVRAPPONE" in (e[1] or ""))
    a2_, b2_ = _fab_scena("s1", 1000, 1720, giro="b95n1-777")   # la marca VECCHIA
    g_vecchio = {"t0_mono": 120.0, "t1_mono": 132.0, "nonce": "b95n2-777",
                 "cambi": cambio_delle_scene({"s1": a2_}, {"s1": b2_})}
    e = p_ancora(g_vecchio, g_prec)
    caso("5c · GUASTO: la finestra e' giusta ma la MARCA e' quella del gradino "
         "prima (una scena non riaccesa)",
         "False, e dice «sto leggendo un altro giro»", e,
         e[0] is False and "altro giro" in (e[1] or ""))
    caso("5d · risanato: marca giusta e finestra giusta",
         "True", p_ancora(g_ora, g_prec), p_ancora(g_ora, g_prec)[0] is True)
    e = p_ancora({"t0_mono": None, "t1_mono": 132.0}, g_prec)
    caso("5e · GUASTO: della finestra manca t0 ⇒ None, non un verde",
         "None", e, e[0] is None)

    # ═══════════════════════════════════════════════════════════════════════
    print("\n── 6 · ⭐ LA SOLLECITAZIONE ARRIVATA, e i conti che devono tornare ──")
    e = p_sollecitazione_arrivata(vivo, 124.4)
    caso("6a · sano: e' arrivato quel che si e' chiesto",
         "True", e, e[0] is True)
    a3, b3 = _fab_scena("s1", 1000, 1120)   # 10 commit/s invece di 60
    poco = cambio_delle_scene({"s1": a3}, {"s1": b3})
    e = p_sollecitazione_arrivata(poco, 124.4)
    caso("6b · GUASTO: e' arrivato un sesto del cambiamento chiesto",
         "False, e dice «la prova non morde»", e,
         e[0] is False and "non morde" in (e[1] or ""))
    caso("6c · sano: i padroni sommano quanto la macchina",
         "True", p_conti_tornano(at), p_conti_tornano(at)[0] is True)
    sballato = dict(at); sballato["macchina_render"] = 99.0
    e = p_conti_tornano(sballato)
    caso("6d · GUASTO: la macchina dice 99 % ma i padroni sommano 51 %",
         "False, coi due numeri", e, e[0] is False)
    caso("6e · GUASTO: un padrone e' None ⇒ non giudico, non sommo zero",
         "None", p_conti_tornano(ac), p_conti_tornano(ac)[0] is None)

    # ═══════════════════════════════════════════════════════════════════════
    print("\n── 7 · ⭐ LA RETTA — e un'ipotesi che non regge deve restare senza "
          "legge ──")
    r = retta([(10.0, 5.0), (20.0, 10.0), (40.0, 20.0), (80.0, 40.0)])
    caso("7a · sano: y = 0,5·x ⇒ pendenza 0,5, errore ~0",
         "0,5000 e rms < 1e-9", (round(r["pendenza"], 6), r["rms"] < 1e-9),
         abs(r["pendenza"] - 0.5) < 1e-9 and r["rms"] < 1e-9)
    caso("7b · GUASTO: due punti soli ⇒ None, perche' due punti danno sempre "
         "una retta perfetta",
         "None", retta([(1.0, 2.0), (2.0, 4.0)]),
         retta([(1.0, 2.0), (2.0, 4.0)]) is None)
    caso("7c · GUASTO: un punto con y = None non entra e ne restano due ⇒ None",
         "None", retta([(1.0, 2.0), (2.0, 4.0), (3.0, None)]),
         retta([(1.0, 2.0), (2.0, 4.0), (3.0, None)]) is None)
    r2 = retta([(10.0, 40.0), (20.0, 40.0), (40.0, 40.0), (80.0, 40.0)])
    caso("7d · un GRADINO invece di una retta (costo piatto): pendenza 0 e "
         "R² non definito ⇒ il banco NON dira' «proporzionale»",
         "pendenza ~0 e r2 None", (round(r2["pendenza"], 6), r2["r2"]),
         abs(r2["pendenza"]) < 1e-9 and r2["r2"] is None)

    # ═══════════════════════════════════════════════════════════════════════
    print("\n── 8 · ⭐ IL RIASSUNTO DELLA GT, e «non ho letto» ≠ «zero» ──")
    caso("8a · sano: tre campioni a 1350",
         "media 1350, non bloccata",
         gt_riassunto([{"act_mhz": 1350, "cur_mhz": 1350, "min_mhz": 300,
                        "max_mhz": 1550}] * 3)["act_media"],
         gt_riassunto([{"act_mhz": 1350, "cur_mhz": 1350, "min_mhz": 300,
                        "max_mhz": 1550}] * 3)["act_media"] == 1350)
    caso("8b · GUASTO: nessun campione ⇒ None, non 0 MHz",
         "None", gt_riassunto([]), gt_riassunto([]) is None)
    caso("8c · GUASTO: campioni senza frequenza ⇒ None",
         "None", gt_riassunto([{"act_mhz": None, "cur_mhz": None}]),
         gt_riassunto([{"act_mhz": None, "cur_mhz": None}]) is None)
    rr = gt_riassunto([{"act_mhz": 1550, "cur_mhz": 1550, "min_mhz": 1550,
                        "max_mhz": 1550}] * 4)
    caso("8d · la GT BLOCCATA si riconosce (min == max) e si dichiara",
         "bloccata = True", rr["bloccata"], rr["bloccata"] is True)
    caso("8e · GUASTO: una somma con un buco dentro non e' una somma",
         "cambio_totale = None",
         cambio_totale({"a": {"mpx_s": 10.0}, "b": {"mpx_s": None}}),
         cambio_totale({"a": {"mpx_s": 10.0}, "b": {"mpx_s": None}}) is None)

    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 78)
    verdi = sum(1 for _, p in esiti if p)
    print("   %d su %d" % (verdi, len(esiti)))
    if verdi != len(esiti):
        for nome, p in esiti:
            if not p:
                print("   %sNO%s  %s" % (ROSSO, GRIGIO, nome))
        print("═" * 78)
        return 1
    print("   ⭐ ogni predicato ha fatto quel che era scritto prima, e ogni "
          "guasto e' stato VISTO dare rosso")
    print("═" * 78)
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# La riga di comando
# ═══════════════════════════════════════════════════════════════════════════

def porta():
    """I pezzi di QUESTO banco sulla macchina di prova.  ⛔ Il metro della GPU e
       il lettore del blocco della scena vanno accanto a me, o la meta' che gira
       da root non li trova."""
    _log("I PEZZI DI 10-b95 SULLA MACCHINA DI PROVA")
    p = subprocess.run(
        ["tar", "-C", os.path.dirname(QUI), "-cf", "-",
         "banchi/10-b95-composizione.py", "banchi/10-b87-metro-gpu.py",
         "banchi/03-marca.py", "banchi/09-lucchetto.py",
         "banchi/10-b0-terreno.sh", "banchi/10-b91-terreno-dieci.sh"],
        capture_output=True, timeout=300)
    if p.returncode != 0:
        _ko("⛔ il tar non e' riuscito: %s" % p.stderr.decode()[-300:])
        return 2
    q = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA,
                        "mkdir -p %s/banchi && tar -C %s -xf -" % (ALB, ALB)],
                       input=p.stdout, capture_output=True, timeout=300)
    if q.returncode != 0:
        _ko("⛔ i pezzi non sono arrivati: %s" % q.stderr.decode()[-300:])
        return 2
    _ok("i pezzi sono in %s/banchi" % ALB)

    pezzi, perche = _pezzi_di_b92()
    if pezzi is None:
        _ko(perche)
        return 2
    for nome, sorg in (("10-b92-cliente.py", pezzi["CLIENTE"]),
                       ("10-b92-fetta.py", pezzi["FETTA"])):
        if not spedisci(sorg, nome):
            _ko("⛔ «%s» non si e' scritto in %s" % (nome, LAV))
            return 2
        _ok("⭐ «%s» preso da 10-b92 (gia' certificato) e scritto in %s"
            % (nome, LAV))
    rc, out, _ = root("md5sum %s/banchi/10-b87-metro-gpu.py %s/banchi/03-marca.py"
                      % (ALB, ALB))
    _inf("md5 dei pezzi che leggeranno la macchina:\n        %s"
         % out.strip().replace("\n", "\n        "))
    return 0


def principale():
    p = argparse.ArgumentParser(
        description="10-b95 — il soffitto della COMPOSIZIONE")
    p.add_argument("modo", nargs="?", default="stato",
                   choices=["stato", "porta", "terreno", "scomponi", "ritmi",
                            "rampa", "tutto", "giro2", "sgombra"])
    p.add_argument("--sul-server", metavar="PASSO", default=None,
                   help="⛔ la meta' che gira DA ROOT sulla macchina di prova")
    p.add_argument("--certifica", action="store_true",
                   help="⛔ innesta i guasti e conta sano→guasto→risanato")
    p.add_argument("--finestra", type=float, default=FINESTRA_S,
                   help="la durata della finestra di misura, in secondi")
    p.add_argument("--assestamento", type=float, default=ASSESTAMENTO_S)
    p.add_argument("--secondi-sessione", type=float, default=3600.0)
    p.add_argument("--utente-i", type=int, default=1,
                   help="quale provamtN usare per «scomponi» e «ritmi»")
    p.add_argument("--fino", type=int, default=11)
    p.add_argument("--gt", type=int, default=None,
                   help="⭐ blocca la GT a questi MHz e lo DICHIARA")
    p.add_argument("--fermati-a-saturazione", action="store_true")
    p.add_argument("--scrivi-legge", action="store_true",
                   help="⭐ scrive la legge trovata IN TESTA a questo file")
    p.add_argument("--senza-lucchetto", action="store_true",
                   help="⛔ SOLO per la messa a punto: i numeri non valgono e "
                        "non si riferiscono")
    a = p.parse_args()

    if a.sul_server:
        return _sul_server(a.sul_server)
    if a.certifica:
        return certifica()
    if a.modo == "porta":
        return porta()
    if a.modo == "stato":
        rc, out, _ = rem("ss -uln | grep -c ':%d ' || true" % PORTA)
        _inf("ascoltatori sulla mia porta %d: %s" % (PORTA, out.strip()))
        luc = _lucchetto()
        chi, quando = luc.stato()
        _inf("lucchetto GPU: %s" % ("libero" if chi is None else
                                    "di «%s» fino a %s"
                                    % (chi, time.strftime("%H:%M:%S",
                                                          time.localtime(quando)))))
        return 0
    if a.modo == "sgombra":
        return sgombra()

    os.makedirs(FUORI, exist_ok=True)
    # ⛔⛔ IL LUCCHETTO PRIMA, POI GLI UTENTI.  Chi non ha il lucchetto non tocca
    #     un `provamt*`.
    luc = None
    if not a.senza_lucchetto:
        luc = _lucchetto()
        _log("IL LUCCHETTO DELLA GPU — ⛔ la GPU e' UNA")
        # ⛔ Il possesso si dichiara per quanto DURA il giro, non per quanto fa
        #    comodo: «tutto» sono tre fasi di fila (~35 min misurati a tavolino),
        #    e un possesso troppo corto scadrebbe a meta' — allora il prossimo
        #    che arriva SCASSINA, e lo fa mentre io sto ancora misurando.
        durata = 3600 if a.modo in ("tutto", "giro2") else 2400
        # ⛔⛔ L'ATTESA E' LUNGA, E LA RAGIONE E' MISURATA, non prudenziale.
        #
        # `prendi()` NON e' una coda: e' una CORSA.  Il `mkdir` si ritenta ogni
        # 5 s e vince chi arriva per primo dopo un `molla` — ⛔ **nessuna
        # prenotazione, nessuna anzianita'**.  `[M]` 24 agosto 2026: siamo in
        # cinque sulla stessa scheda, ogni giro dura ~90 minuti, e un incarico
        # che aspettava dalle 19:53 ha perso **due passaggi di mano
        # consecutivi** senza mai toccare la GPU.
        # ⛔ Un'attesa corta scade DENTRO il turno di un altro, e allora il giro
        #   esce con un codice che somiglia a un problema di terreno mentre ⛔ la
        #   domanda non e' mai stata posta: e' «silenzio invece di rosso» nello
        #   strato che ci coordina, che e' la forma peggiore (`LEZIONI.md` §1.29).
        # ⇒ Sei ore: e' cinque giri pieni degli altri quattro, cioe' il tempo
        #   oltre il quale «non ho vinto la corsa» diventa un fatto da riferire
        #   invece di un caso.
        luc.prendi(IO_SONO, secondi=durata, attesa=21600)
        _inf("⚠ possesso dichiarato per %d s (modo «%s»)" % (durata, a.modo))
    else:
        _dub("⛔ SENZA LUCCHETTO: i numeri di questo giro NON valgono e NON si "
             "riferiscono")

    codice, esiti = 2, {}
    try:
        # ⛔⛔ LA GT BLOCCATA — la seconda strada del §CLOCK, e si dichiara.
        #     Si mette UNA volta per tutto il giro: bloccarla dentro una fase
        #     sola vorrebbe dire confrontare fasi prese a orologi diversi.
        if a.gt:
            g = gt_comanda(a.gt)
            if g is None or not g.get("bloccata"):
                _ko("⛔ non ho potuto bloccare la GT a %s MHz (RPn %s, RP0 %s): "
                    "mi fermo invece di dichiarare un blocco che non c'e'"
                    % (a.gt, (g or {}).get("rpn"), (g or {}).get("rp0")))
                return 1
            _ok("⚠ GT BLOCCATA a %s MHz per TUTTO il giro (min=%s max=%s) — "
                "⭐ e' dichiarato, ed e' la seconda strada per un numero "
                "confrontabile fuori dalla saturazione"
                % (a.gt, g["dopo"].get("min_mhz"), g["dopo"].get("max_mhz")))
        if not accendi_server():
            return 1
        if a.modo == "terreno":
            return 0 if terreno(a.fino) else 1
        if not terreno(a.fino, palco_ammesso=False):
            return 1
        # ⭐ «tutto» = le tre fasi sotto UN SOLO possesso del lucchetto.
        #
        # ⛔ E si dichiara perche': tre prese separate vorrebbero dire tre code
        #   da un'ora e mezza l'una dietro gli altri agenti, e le tre fasi sono
        #   UN giro solo — misurano la stessa grandezza sullo stesso ferro nella
        #   stessa ora.  ⚠ Il prezzo e' che gli altri aspettano piu' a lungo, ed
        #   e' per questo che il possesso dichiara 2 400 s e non di piu'.
        fasi = {"tutto": ["scomponi", "ritmi", "rampa"],
                "giro2": ["ritmi", "rampa"]}.get(a.modo, [a.modo])
        tutti = {}
        codice = 0
        for k, fase in enumerate(fasi):
            if k:
                pulisci_fra_fasi()
            _log("═══ FASE «%s» (%d di %d) ═══" % (fase, k + 1, len(fasi)))
            c, e = {"scomponi": scomponi, "ritmi": ritmi,
                    "rampa": rampa}[fase](a)
            tutti[fase] = e
            codice = max(codice, c)
            dove = os.path.join(FUORI, "10-b95-%s.json" % fase)
            with open(dove, "w", encoding="utf-8") as f:
                json.dump(e, f, ensure_ascii=False, indent=1, default=str)
            _inf("esiti di «%s» in %s" % (fase, dove))
        esiti = (tutti if a.modo in ("tutto", "giro2") else tutti[a.modo])
        if a.modo in ("tutto", "giro2"):
            esiti = {"modo": a.modo, "fasi": tutti,
                     "rossi": [r for e in tutti.values()
                               for r in e.get("rossi", [])],
                     "muti": [m for e in tutti.values()
                              for m in e.get("muti", [])]}
    finally:
        try:
            if a.gt:
                gt_comanda("rimetti")
            sgombra()
        finally:
            if luc is not None:
                luc.molla(IO_SONO)

    dove = os.path.join(FUORI, "10-b95-%s.json" % a.modo)
    with open(dove, "w", encoding="utf-8") as f:
        json.dump(esiti, f, ensure_ascii=False, indent=1, default=str)
    _inf("esiti in %s" % dove)
    rossi, muti = esiti.get("rossi", []), esiti.get("muti", [])
    _log("IL VERDETTO — %d rossi · %d non giudicati" % (len(rossi), len(muti)))
    for r in rossi[:40]:
        _ko(r)
    for m in muti[:40]:
        _dub(m)
    if not rossi and not muti:
        _ok("⭐ tutti i predicati hanno fatto quel che era scritto prima")
    return codice


if __name__ == "__main__":
    sys.exit(principale())
