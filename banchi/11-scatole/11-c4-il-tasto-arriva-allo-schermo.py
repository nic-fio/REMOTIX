#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c4 — ⭐⭐ «IL TASTO ARRIVA FINO ALLO SCHERMO»
===========================================================================

    python3 11-c4-il-tasto-arriva-allo-schermo.py
    python3 11-c4-il-tasto-arriva-allo-schermo.py --senza-tasto
    python3 11-c4-il-tasto-arriva-allo-schermo.py --scena-sorda
    python3 11-c4-il-tasto-arriva-allo-schermo.py --certifica

`fasi/11-la-rete-di-sicurezza.md` §4.1, riga **C4**:

  | che cosa deve essere vero | il tasto arriva **fino allo schermo**        |
  | da dove parte             | sessione nuova                               |
  | che cosa guarda           | ⛔ **il pixel, prima e dopo**: immagine ·     |
  |                           | tasto · immagine, e i pixel **della zona     |
  |                           | attesa** devono cambiare                     |
  | come so che sa dare rosso | si stacca il percorso dell'input ⇒ rosso     |

---------------------------------------------------------------------------
⭐⭐ LA PAROLA CHE CONTA E' «FINO ALLO SCHERMO»
---------------------------------------------------------------------------

⛔ Non basta che il prodotto dica di aver mandato il tasto.
⛔ Non basta che il compositore dica di averlo ricevuto.
⛔ Non basta contare gli `id` degli input, ne' leggere il campo `input` dei
   fotogrammi (§6.2): quello dice *«l'ho iniettato»*, che e' un'altra frase.

⇒ ⭐ **Deve cambiare un pixel.**  Un percorso dell'input che finisce nel nulla —
  il tasto parte, viaggia, viene iniettato, e sullo schermo non succede niente —
  e' esattamente il guasto che **nessun conteggio prende**, ed e' la stessa
  forma dei tre guasti che hanno aperto questa fase (§0.3: *«si contava il
  processo invece di guardare il pixel; il conto diceva 1 con la finestra e
  senza»*).

---------------------------------------------------------------------------
⚠⚠ E LA SECONDA PAROLA E' «DELLA ZONA ATTESA»
---------------------------------------------------------------------------

⛔ Guardare **tutta** l'immagine non serve: un orologio in un angolo che avanza
   da solo dice *«qualcosa e' cambiato»* senza che nessun tasto sia arrivato da
   nessuna parte.  ⇒ Un banco cosi' sarebbe **verde per costruzione** su GNOME,
   dove la barra in alto porta l'orologio e non si spegne mai (`[M]` 25 agosto
   2026, misurato da `10-f1-testimone.py`: un desktop nero *intero* fa lo stesso
   0,00121 di pixel accesi **solo per via della barra**).

⇒ ⭐ **Si dichiara la zona, e si guarda SOLO li' dentro.**

    LA ZONA ATTESA   : il **rettangolo centrale** dell'immagine — dal 35 % al
                       65 % della larghezza e dell'altezza, cioe' il **9 %**
                       dello schermo, esattamente in mezzo.
    LA ZONA TESTIMONE: la **cornice esterna** — tutto quel che sta **fuori** dal
                       rettangolo 12..88 %.  Li' non deve cambiare niente, ed e'
                       proprio dove vivono barre, cassetti e orologi.

    ⭐ PERCHE' PROPRIO QUELLA, e sono tre ragioni, non una:

      1. ⛔ **E' l'unica parte dello schermo che nessun desktop puo' occupare
         con la sua roba.**  Barre, cassetti, angoli attivi, decorazioni delle
         finestre e orologi stanno **ai bordi** — su tutti e quattro i desktop
         di questa fase.  ⇒ La zona e' scelta per essere **cieca al desktop**
         (§3.7), e non perche' li' «di solito non c'e' niente».
      2. ⭐ La scena che questa maglia si porta dietro dipinge un bersaglio che
         occupa il **60 %** centrale dello schermo (dal 20 % all'80 %).  ⇒ La
         zona attesa ci sta dentro con **un margine del 15 % della larghezza per
         lato**: la pagina puo' scivolare di un'intera barra di GNOME senza che
         la zona esca dal bersaglio.
      3. ⚠ Ed e' **piccola**: 9 % dello schermo.  ⇒ Un cambiamento che riempie
         la zona e lascia fermo il resto **non puo'** essere «e' cambiato tutto»,
         e la maglia lo sa distinguere (terzo controllo, qui sotto).

---------------------------------------------------------------------------
⭐ LA SCENA — scelta, dichiarata, e ⛔ DETERMINISTICA
---------------------------------------------------------------------------

Serve qualcosa che, **ricevendo un tasto**, cambi un pixel in un posto
**prevedibile**.  ⇒ La scena e' una **pagina** che la maglia scrive da se' nella
casa dell'inquilino e apre nel browser a schermo intero (`--kiosk`):

    · lo sfondo e' di un colore fisso;
    · in mezzo c'e' un **bersaglio quadrato**, dal 20 % all'80 % dello schermo,
      dipinto del COLORE DI PARTENZA;
    · al **primo tasto che arriva alla pagina** il bersaglio diventa del
      COLORE D'ARRIVO, e ci resta.

⛔ **E NON C'E' NIENT'ALTRO.**  Niente orologio, niente animazione, niente
   `setTimeout`, niente immagini che si caricano, niente carattere da scaricare.
   ⇒ Se la scena potesse cambiare da sola, la maglia non giudicherebbe piu'
   niente — direbbe «cambiato» e non saprebbe per colpa di chi.

⭐ **E LA SCENA E' STATA MISURATA, non immaginata.**  `[M]` 27 agosto 2026, **sul
  portatile**, Firefox headless a **1920x1080** che rende la pagina vera:

    la scena, prima del tasto : zona 100 % del colore di partenza, arrivo 0 %
    la scena, dopo il tasto   : zona 0 % di partenza, **100 % d'arrivo**
    la zona testimone         : **0 %** cambiata, in tutt'e due i giri
    la scena SORDA, col tasto : zona ancora 100 % di partenza ⇒ ROSSO, e
                                `guasto_visto` = **vero**
    il «prima» per `10-f1`    : **«disegnato»** — ne' nero, ne' tinta unita

  ⛔ E il limite di questa misura si dichiara: e' **il browser che rende la
     pagina**, non il tasto che attraversa il prodotto.  ⇒ Dice che la scena e la
     zona sono scelte bene; ⚠ **non** dice niente sul percorso dell'input, che
     e' quel che il giro vero deve misurare dentro la scatola.

⭐⭐ **E LA SCENA NON E' UN FILE A PARTE: LA SCRIVE QUESTO PROGRAMMA.**
   ⛔ Il colore che la pagina dipinge e il colore che il giudice cerca sono **la
   stessa costante Python**, scritta una volta sola qui sotto e infilata nel
   `<style>`.  ⇒ Non possono divergere: e' la stessa ragione per cui il giudice
   delle immagini **si importa e non si riscrive** (`10-f1-testimone.py`).
   ⚠ E cosi' la scena e' **nuova a ogni giro**, che e' la meta' di «da zero» che
     si dimentica sempre (`LEZIONI.md` §1.39, e C1 col suo `userdel` prima del
     `useradd`).

---------------------------------------------------------------------------
⭐⭐⭐ I TRE CONTROLLI POVERI — §4.3, e nessuno sa che aspetto abbia un desktop
---------------------------------------------------------------------------

  1. ⭐ **PRIMA: la scena e' in vigore.**  Nella zona attesa dev'esserci il
     COLORE DI PARTENZA, con una **tolleranza dichiarata** (§4.3, rilievo di
     Gemini accolto: i compositori applicano profili di colore, e la catena
     passa da una codifica H.264 in 4:2:0 che sottocampiona proprio il croma).
     ⛔ Se non c'e', l'esito e' **3 — non ho potuto guardare**, e ⛔ NON e' un
     rosso: un desktop su cui la scena non e' mai comparsa non testimonia sul
     tasto.  ⚠ E' la stessa regola con cui C8 rifiuta di accusare il browser di
     un desktop nero.

     ⛔⛔ E il controllo gemello, che vale ancora di piu': **la zona NON dev'essere
        gia' del colore d'arrivo**.  Se lo fosse, la maglia direbbe verde per
        sempre senza che nessun tasto arrivi mai — *un predicato che non puo'
        fallire*, `LEZIONI.md` §1.44.

  2. ⭐ **DOPO: la zona e' del COLORE D'ARRIVO.**  Non «e' cambiata»: e' di
     **quel** colore.  ⛔ Una zona diventata nera (la finestra si e' chiusa) e'
     cambiata benissimo, e non vuol dire che il tasto sia arrivato.

  3. ⭐ **IL CAMBIAMENTO E' CONCENTRATO, E FUORI E' FERMO.**  Si contano i pixel
     che si scostano fra le due immagini, **dentro** la zona attesa e nella
     **zona testimone**.  Dentro deve cambiare tanto; nel testimone quasi
     niente.  ⚠ Se il testimone si muove, la scena si sta muovendo da sola ⇒
     **3**, non verde: il cambiamento nella zona non e' piu' attribuibile al
     tasto.  ⛔ E' il controllo che l'orologio nell'angolo non passa.

     ⛔⛔ **E LA ZONA TESTIMONE NON E' «TUTTO IL RESTO DELL'IMMAGINE»** — questo
        e' costato la prima stesura, e l'ha preso `--certifica` prima di
        qualunque giro vero.  Il bersaglio della scena occupa il 20..80 % dello
        schermo, cioe' il **36 %**; la zona attesa ne guarda **9**.  ⇒ Quando il
        tasto arriva, i **27 punti percentuali** di bersaglio che stanno fuori
        dalla zona cambiano anche loro, ⛔ e un «tutto il resto» avrebbe visto
        cambiare il 30 % dello schermo **a ogni giro riuscito**: la maglia
        avrebbe detto *«non lo so»* per sempre (`LEZIONI.md` §1.49).

     ⇒ ⭐ **La zona testimone e' la CORNICE ESTERNA**: tutto quel che sta fuori
       dal rettangolo 12..88 %.  Non tocca mai il bersaglio (margine dell'8 %,
       cioe' 86 righe su 1080: due barre di GNOME), ed e' proprio dove vivono
       barre, cassetti e orologi.
     ⚠ **E la fascia in mezzo — dal 12 % al 35 % e dal 65 % all'88 % — NON si
       giudica affatto**, ed e' dichiarato: e' il margine che assorbe le barre,
       le decorazioni e lo scivolamento della pagina.  ⛔ Un banco che
       giudicasse anche quella sarebbe rosso al primo desktop con una barra piu'
       larga — cioe' alla fase 12, che e' quel che questa fase esiste per evitare.

---------------------------------------------------------------------------
⭐⭐ PERCHE' IL CLIENTE RESTA ATTACCATO PER TUTTO IL GIRO — e non e' comodita'
---------------------------------------------------------------------------

`[M]` misurato la notte del 26-27 agosto 2026: il `wl_output` di una sessione
headless **nasce soltanto quando un consumatore PipeWire si aggancia al flusso**,
e mai prima.  ⇒ ⛔ **Lo schermo esiste solo mentre il nostro cliente e'
attaccato.**

⇒ Percio' questa maglia apre **una sola connessione** e ci fa dentro tutto:
il palco, la scena, l'immagine PRIMA, il tasto, l'immagine DOPO.  ⛔ Staccarsi
in mezzo per riattaccarsi dopo vorrebbe dire far sparire lo schermo fra le due
fotografie, e confrontare due immagini di due mondi diversi.

⭐ E si attacca **PRIMA** di pretendere di vedere qualcosa, mai dopo.

---------------------------------------------------------------------------
⭐ COME SI MANDA DAVVERO UN TASTO — la parte in cui e' facile sbagliare
---------------------------------------------------------------------------

⛔ **NON** si passa da `org.gnome.Mutter.RemoteDesktop` (che e' quel che fa
   `banchi/09-b72-tasto.py`): quella e' la porta di **GNOME**, e una maglia che
   la usasse proverebbe il compositore invece del prodotto, ⛔ e tacerebbe sugli
   altri tre desktop — cioe' esattamente il difetto che questa fase esiste per
   non introdurre.

⭐ Si passa **dal prodotto**, sul canale di input di `RCP.md` §7.3:

    LETTERA          `0x0104`  + u32 carattere Unicode      (il tasto misurato)
    POSIZIONE_TASTO  `0x0105`  + u16 codice evdev · u8 premuto

  · il canale di input e' **uno solo**, unidirezionale, aperto dopo `SESSIONE` e
    **tenuto aperto** (§2.5);
  · l'`id` cresce di almeno uno **su tutto il canale**, e `0` e' riservato;
  · i codici sono quelli di **evdev**, perche' `libei` lavora in evdev.

⛔⛔ E IL CLIENTE DI PROVA NON SA MANDARE TASTI: `01-b3-cliente.py` manda
   `PUNTATORE` e basta (`manda_puntatore`, §7.3).  ⇒ Questa maglia **importa** il
   cliente e gli aggiunge i due messaggi che mancano — ⭐ **importa**, non
   ricopia: l'inquadratura, i tipi, la stretta di mano QUIC/WebTransport, la
   raccolta dei fotogrammi dal filo restano **quelle sue**, e il giorno che
   cambia il protocollo cambiano in un posto solo.
   ⚠ E il debito che resta va detto: la **sequenza** d'attacco (CIAO →
     CREDENZIALI → ATTACCA → SESSIONE) e' ricopiata, perche' `principale()` del
     cliente e' un pezzo unico governato da `argparse` e non si puo' chiamare a
     meta'.  ⛔ Se quella sequenza cambia, questa maglia va aggiornata a mano.

---------------------------------------------------------------------------
⚠ LA SVEGLIA — perche' si manda un tasto PRIMA di aprire la scena
---------------------------------------------------------------------------

`[M]` 23 agosto 2026, `banchi/09-b72-tasto.py`: **una sessione GNOME headless
resta nella vista d'insieme** (l'Overview) finche' nessuno preme un tasto
dentro, e li' le finestre non sono finestre — sono **anteprime rimpicciolite** in
mezzo allo schermo.  ⇒ Una scena aperta li' dentro non riempirebbe la zona
attesa, e la maglia direbbe **3** per sempre (`LEZIONI.md` §1.49: *un esito che
non si puo' far diventare verde e' peggio di nessuna maglia*).

⇒ ⭐ Si manda un ESC **prima di aprire il browser**, e l'ordine e' l'unica cosa
  che conta: la scena non esiste ancora, quindi la sveglia **non puo'** dipingere
  il bersaglio.  ⛔ Mandarla dopo vorrebbe dire arrivare al «prima» con la zona
  gia' del colore d'arrivo — cioe' innescare da soli il predicato che non puo'
  fallire.

⭐ E la sveglia si paga da sola: se la scena poi compare a schermo intero, quella
  e' **anche** la prova che si e' usciti dalla vista d'insieme.
⚠ `--senza-sveglia` la toglie, ed e' la strada da prendere se un giorno la
  sveglia diventasse inutile: ⛔ non si tiene un gesto perche' «male non fa».

---------------------------------------------------------------------------
⛔ COME SO CHE SA DARE ROSSO — due guasti innestati, e bracchettano il percorso
---------------------------------------------------------------------------

  `--senza-tasto`   ⛔ **si taglia il percorso dell'input alla TESTA**: si fa
                    tutto — sessione nuova, cliente attaccato, scena in vigore,
                    immagine prima, attesa, immagine dopo — **tranne mandare il
                    tasto**.  ⇒ Nel prodotto non entra niente.
                    ⭐ Che cosa prova: che il verdetto **dipende dal tasto**, e
                    che la scena **non cambia da sola**.  Se C4 dicesse verde
                    qui, starebbe guardando qualcos'altro (rumore del codificatore,
                    una finestra che si apre, un orologio) — e non ci si potrebbe
                    fidare di lei.

  `--scena-sorda`   ⛔ **si taglia il percorso alla CODA**: la scena si scrive
                    **senza il gestore di tastiera**.  ⇒ Il tasto attraversa il
                    prodotto per intero, viene iniettato nel compositore, arriva
                    al browser — ⛔ e non dipinge niente.
                    ⭐ Che cosa prova: che il rosso di C4 lo decide **il pixel**,
                    e non il fatto di aver mandato un tasto.

⚠⚠ E QUEL CHE NESSUNO DEI DUE PROVA, dichiarato invece che taciuto:
   ⛔ **non tagliano il percorso in MEZZO** — fra il prodotto e il compositore,
   cioe' il canale EIS di `src/input.c`.  `[?]` Un guasto li' oggi non si sa
   innestare senza toccare `src/` o riaccendere il server dentro la scatola, e
   riaccendere il server mentre altre maglie misurano e' vietato.  ⇒ E' scritto
   qui invece di essere spacciato per fatto, e sta nelle cose da tarare sul vero.

⭐⭐ E IL GUASTO SI LEGGE SULLA **DIFFERENZA**, NON SUL COLORE DEL VERDETTO
   — `LEZIONI.md` §1.52.  «Rosso ⇒ il guasto e' stato visto» sarebbe un predicato
   che non puo' fallire: C4 potrebbe essere rossa per conto suo (la finestra si
   e' chiusa, il browser e' morto), e la rete si certificherebbe su un guasto del
   prodotto invece che sul proprio.  ⇒ Si pretendono **tre** cose insieme:

     · il verdetto e' rosso, **e**
     · la zona e' **ancora** del colore di partenza (⛔ non nera, non sparita), **e**
     · dentro la zona non e' cambiato quasi niente (≤ 5 %), contro il ≥ 60 % che
       si pretende quando il tasto arriva.  ⭐ **Un fattore dodici**, e sta
       scritto nelle costanti qui sotto.

---------------------------------------------------------------------------
⛔ QUEL CHE C4 **NON** GUARDA — o qualcuno se ne fidera' troppo
---------------------------------------------------------------------------

  · ⛔ **non guarda QUALE tasto arriva.**  La scena si accende al **primo tasto
    qualunque**: la domanda di C4 e' *«il tasto arriva fino allo schermo»*, non
    *«arriva la lettera giusta»*.  ⚠ La disposizione della tastiera, gli accenti,
    i modificatori, `LETTERA` contro `POSIZIONE_TASTO` sono un'altra domanda, e
    una maglia che le mescolasse darebbe rosso senza dire per che cosa.
  · ⛔ **non misura il RITARDO** del tasto: dice che arriva, non quanto ci mette.
  · ⛔ **non guarda il mouse**, ne' la rotella, ne' gli appunti.  Un guasto che
    colpisse **solo** il puntatore, C4 non lo vedrebbe.
  · ⛔ **non e' una prova di intermittenza**: apre **una** sessione, non dieci.
    ⇒ Se l'input diventasse saltuario, e' un altro giro che lo prende — e C1 e'
    l'esempio di come si conta.
  · ⛔ **non prova che il desktop sia sano**: guarda 9 % di schermo, e li' sopra
    c'e' una pagina nostra.  ⇒ C4 verde non vuol dire «la sessione sta bene».
  · ⚠ **non separa il browser dal prodotto**: se il browser non parte, C4 dice
    **3**, non rosso — ed e' C8 la maglia che sul browser giudica.

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)
---------------------------------------------------------------------------

  0  ⭐ ho guardato: il tasto e' arrivato fino allo schermo
  1  ho guardato: la zona attesa NON e' cambiata           ⇒ rosso
  3  ⛔ non ho potuto guardare (nessun fotogramma, scena mai comparsa, immagini
     illeggibili, la scena si muove da sola) — ⛔ e NON e' un rosso
  2  il terreno non regge, o l'uso e' sbagliato
  4  il turno non e' mai arrivato

⛔ E col guasto innestato l'esito si legge **AL CONTRARIO**: `0` = il guasto e'
   stato **visto**.  E' la convenzione di `11-gancio.sh` (`esegui_maglia`), che
   nel registro scrive il **fatto** — `ha_visto_il_guasto` — e non l'esito
   grezzo.  ⛔ Uscire col verdetto grezzo farebbe scrivere «non visto» proprio nel
   giro in cui il guasto e' stato visto benissimo (`LEZIONI.md` §1.52).
===========================================================================
"""
import argparse
import asyncio
import importlib.util
import os
import re
import struct
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ C1 E' LA CASA DEI DUE PASSI COMUNI A TUTTE E NOVE LE MAGLIE — §1.47
#
# ⛔ Non e' comodita': una riga ripetuta in nove file e' **nove posti da cui
#    divergere**, ed erano gia' divergiti.  Da `11-c1-nasce-e-si-vede.py`:
#
#   · `e_stato_ammesso(coda)`   — «il cliente e' stato AMMESSO?», che ⛔ non e'
#        la parola dentro un testo: il cliente la stampa anche nei DUE messaggi
#        di rifiuto, e sullo stdout (`01-b3-cliente.py:1315`, `:1322`, `:2560`).
#   · `garantisci_i_gruppi(chi)` — i gruppi dei nodi `/dev/dri`, ⛔ senza i
#        quali `[M]` la sessione nasce CIECA (0 su 4, zero fotogrammi,
#        `fasi/10-…` §7.4) e questa maglia misurerebbe il buio.
#
# ⛔ Se C1 non si carica si esce **3** e lo si dice: ⛔ non si ripiega in
#    silenzio su un giudizio piu' povero.
# ═══════════════════════════════════════════════════════════════════════════
_MESTIERI_C1 = ("e_stato_ammesso", "certifica_ammissione",
                "garantisci_i_gruppi", "verdetto_gruppi", "certifica_gruppi")
_C1 = None


def _carica_c1():
    """⛔ E' un CARICATORE, non un giudice: trova il file, non decide niente.

    ⚠ Si cerca accanto a me (nella scatola tutto sta in `/opt/remotix`) e un
      piano piu' su, perche' nel deposito questa maglia sta in
      `banchi/11-scatole/`.
    """
    for base in (QUI, os.path.dirname(QUI)):
        perc = os.path.join(base, "11-c1-nasce-e-si-vede.py")
        if not os.path.exists(perc):
            continue
        spec = importlib.util.spec_from_file_location("c1_comune", perc)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None
        # ⛔ Si VERIFICA che ci sia quel che serve, non ci si fida del nome del
        #    file (`CODER.md` §3.9).
        for mestiere in _MESTIERI_C1:
            if not callable(getattr(m, mestiere, None)):
                return None
        return m
    return None


def casa_di_c1():
    global _C1
    if _C1 is None:
        _C1 = _carica_c1()
    if _C1 is None:
        print("⛔ non trovo `11-c1-nasce-e-si-vede.py` accanto a me, e da li'")
        print("   vengono il predicato dell'ammissione e la garanzia dei")
        print("   gruppi della scheda — che stanno in un posto solo (§1.47).")
        print("⇒ non ho potuto guardare — ⛔ e NON e' un rosso (§4.5).")
        sys.exit(3)
    return _C1


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ LA PROVVISTA CONDIVISA — `/tmp/mozilla`, e sta in UN POSTO SOLO
#
# `[M]` 27 agosto 2026, giro `--famiglia tutto` su tutt'e quattro le scatole,
#   binario `aa950804fed7`: C4 ⛔ **3** — «la zona e' del colore di partenza
#   solo per lo 0%».  ⚠ E l'immagine giudicata diceva tutt'altro: la sessione
#   GNOME era **viva e dipinta**, ⛔ ma Firefox stava fermo sulla **finestra di
#   scelta del profilo**, quindi la scena della tastiera non nasceva mai.
#
# ⇒ LA CAUSA: `/home/c4u1/.cache/mozilla` -> `/tmp/mozilla`, che era rimasto a
#   «c8u1» a modo 0700 — C8 e C8b, in `famiglia tutto`, girano PRIMA di me e
#   ⛔ non disfano lo scheletro che hanno messo.  ⛔ Nessuna delle due maglie
#   sbaglia da sola: e' l'ORDINE a romperle.
#
# ⛔⛔ E LA CURA NON PUO' STARE IN CHI MI ACCENDE: per un giorno e' stata in
#     `11-accendi.sh`, ⚠ ma una maglia che va «preparata da fuori» e', lanciata
#     a mano o da un altro gancio, una maglia che da' un **rosso falso**.
#
# ⭐⭐ E NON E' UNO SGOMBERO: e' la cura di `src/provisiona.sh` — una `~/.cache`
#     VERA all'inquilino che creo io.  ⛔ Cancellare il `/tmp/mozilla` di
#     un'altra maglia sarebbe un danno, e in parallelo (C14) la farebbe cadere.
#
# ⛔ Il codice sta in C2 e ⛔ non se ne fa una copia qui (§1.47).  ⚠ Sta in C2 e
#    non in C8 perche' C8 oggi non e' modificabile; ⭐ il giorno che lo sara' si
#    sposta accanto ad `applica_la_cura`.
# ═══════════════════════════════════════════════════════════════════════════
_MESTIERI_PROVVISTA = ("cura_della_provvista", "sgombra_il_mio_rimasuglio",
                       "certifica_la_provvista")
_PROVVISTA = None


def _carica_provvista():
    """⛔ E' un CARICATORE, non un giudice: trova il file, non decide niente."""
    for base in (QUI, os.path.dirname(QUI)):
        perc = os.path.join(base, "11-c2-una-finestra-si-apre.py")
        if not os.path.exists(perc):
            continue
        spec = importlib.util.spec_from_file_location("c2_provvista", perc)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None
        for mestiere in _MESTIERI_PROVVISTA:
            if not callable(getattr(m, mestiere, None)):
                return None
        return m
    return None


def casa_della_provvista():
    global _PROVVISTA
    if _PROVVISTA is None:
        _PROVVISTA = _carica_provvista()
    return _PROVVISTA


def cura_della_provvista(chi):
    """⭐⭐ (fatto, perche') — e ⛔ se non regge NON e' un rosso."""
    casa = casa_della_provvista()
    if casa is None:
        return False, ("non trovo `11-c2-una-finestra-si-apre.py` accanto a me: "
                       "da li' viene la cura della provvista, e ⛔ non se ne fa "
                       "una copia qui (§1.47)")
    return casa.cura_della_provvista(chi)


def sgombra_il_mio_rimasuglio(mio_base):
    """Toglie `/tmp/mozilla` ⛔ soltanto se e' rimasto a un inquilino MIO."""
    casa = casa_della_provvista()
    if casa is None:
        return "⚠ non trovo C2: non ho nemmeno guardato /tmp/mozilla"
    return casa.sgombra_il_mio_rimasuglio(mio_base)


def e_stato_ammesso(coda):
    """⭐ `True` ammesso · `False` **RESPINTO** · `None` non ha detto niente.

    ⛔ `False` non e' un rosso del prodotto: un cliente respinto e' un cliente
       respinto, e chi chiama dice «non ho potuto guardare» (**3**).
    """
    return casa_di_c1().e_stato_ammesso(coda)


def garantisci_i_gruppi(chi, prefisso="   "):
    """⭐⭐ I GRUPPI DELLA SCHEDA — `(esito, perche)`; `0` = si puo' misurare.

    ⛔ Fino al 27 agosto 2026 questa maglia creava l'inquilino con
       `usermod -aG video,render` **e non rileggeva**: due nomi inchiodati (che
       sono di UNA distribuzione) e nessuna verifica — E1, «scritto non e' in
       vigore».  ⭐ Il lavoro lo fa `attrezzi-gruppi-scheda.sh`, che legge i gid
       dai NODI e rilegge confrontando i numeri.  ⛔ Non se ne fa una copia qui.
    """
    return casa_di_c1().garantisci_i_gruppi(chi, prefisso)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ IL METRO — dichiarato qui, stampato a ogni giro, e certificato da
#    `--certifica`.  Un verdetto senza il suo metro e' un'opinione (§4.2).
# ═══════════════════════════════════════════════════════════════════════════

# I due colori della scena.  ⭐ Sono **una costante sola** per la pagina e per il
# giudice: `scena_html()` li infila nel `<style>`, `misura()` li cerca nei pixel.
#
# ⚠ Perche' questi due e non due qualunque:
#   · sono **saturi e lontanissimi** — la distanza per canale, in norma del
#     massimo, e' 255 su 255: nessuna tolleranza ragionevole li confonde;
#   · ⛔ nessuno dei due somiglia a uno sfondo di desktop.  Serve al controllo
#     «la scena e' in vigore»: se il browser non c'e', la zona non sara' di
#     questo verde per il 60 % della sua area, e la maglia lo dira';
#   · il magenta e' **gia' misurato** attraverso questa catena: e' lo stesso di
#     C8, che lo ritrova dopo la codifica H.264 in 4:2:0 con ±48 (§7-bis.10).
COLORE_PARTENZA = (0x00, 0xC0, 0x60)     # verde acceso — prima del tasto
COLORE_ARRIVO = (0xFF, 0x00, 0xFF)       # magenta — dopo il tasto
COLORE_FONDO = (0x18, 0x24, 0x30)        # il resto della pagina, e non cambia mai

# ⛔ LA TOLLERANZA NON E' PRUDENZA GENERICA (§4.3, rilievo di Gemini accolto): i
#    compositori applicano profili di colore e riscalamenti, la catena passa da
#    una codifica H.264 in **4:2:0** — che sottocampiona proprio il croma, cioe'
#    il canale dove sta tutta la differenza fra magenta e non-magenta — e la
#    scala limitata (16..235) sposta ogni fondo scala di una ventina di livelli.
# ⇒ Pretendere il colore esatto vorrebbe dire una maglia gia' morta.
# ⭐ E si TARA, non si sceglie: `--certifica` contiene il caso «colore spostato
#   di quanto la tolleranza ammette ⇒ deve restare VERDE» e il suo gemello
#   «spostato troppo ⇒ ROSSO».  Senza tutt'e due, la tolleranza non separa niente.
TOLLERANZA = 48                  # per canale, norma del massimo, livelli 0..255

# ⭐ LA ZONA ATTESA, in frazioni dell'immagine.  Il perche' sta nell'intestazione.
ZONA = (0.35, 0.35, 0.65, 0.65)
# ⭐ Il bersaglio che la scena dipinge, in frazioni dello schermo: dal 20 % all'80 %.
#    ⛔ `--certifica` verifica che la ZONA sia **strettamente dentro** il
#    BERSAGLIO: due numeri scritti in due punti che si contraddicono darebbero
#    una maglia rossa per sempre senza che niente sia rotto.
BERSAGLIO = (0.20, 0.20, 0.80, 0.80)
# ⭐⭐ LA ZONA TESTIMONE: **tutto quel che sta FUORI da questo rettangolo**, cioe'
#     la cornice esterna dello schermo.  ⛔ NON e' «tutto il resto dell'immagine»:
#     il bersaglio cambia tutto insieme, e un «tutto il resto» vedrebbe cambiare
#     il 30 % dello schermo a ogni giro RIUSCITO ⇒ «non lo so» per sempre
#     (`LEZIONI.md` §1.49).  ⇒ Il margine fra il bersaglio e il testimone e'
#     l'8 % dello schermo — 86 righe su 1080, due barre di GNOME — e la fascia in
#     mezzo NON si giudica, di proposito.
TESTIMONE = (0.12, 0.12, 0.88, 0.88)

# Quanta parte della ZONA dev'essere di un colore perche' si dica «e' di quel
# colore».  ⚠ 0,60 e non 0,95: la pagina puo' essere scivolata di una barra, e la
# codifica sporca i bordi.  ⛔ E non 0,20: sotto meta' zona non e' piu' «la zona
# e' di quel colore», e' «c'e' una macchia».
FRAZIONE_COLORE = 0.60

# ⛔ Quando due pixel si considerano «cambiati»: piu' di 40 livelli su almeno un
#    canale.  ⚠ Serve a NON contare il rumore del codificatore: fra due
#    fotogrammi di una scena ferma i livelli ballano di pochi punti, e un banco
#    che li contasse direbbe «cambiato» sempre.
SOGLIA_CAMBIO = 40
CAMBIO_MINIMO_DENTRO = 0.60      # col tasto: almeno il 60 % della zona cambia
CAMBIO_MASSIMO_TESTIMONE = 0.20  # oltre, la scena si muove da sola ⇒ «non lo so»
CAMBIO_RESIDUO = 0.05            # ⭐ senza tasto: dentro non cambia piu' di questo

# ⭐ Il tasto misurato.  §7.3: `LETTERA` porta un valore scalare Unicode.
LETTERA = 0x0061                 # «a»
T_LETTERA = 0x0104
T_POSIZIONE_TASTO = 0x0105
ESC_EVDEV = 1                    # `linux/input-event-codes.h`, KEY_ESC

# ⭐⭐ IL RITARDO DEL PALCO — ⛔ e' una MISURA, non un numero tondo (§1.45).
#     `[M]` 27 agosto 2026, dentro la scatola **gnome**, tre sessioni vere
#     (C1, `RITARDO_PALCO`): gu1 98,0 s · gu2 101,0 s · gu3 95,5 s ⇒ massimo
#     **101,0 s**, e il margine dichiarato e' meta': 101,0 × 1,5 = **152 s**.
#     ⚠ Sulle altre scatole sono ~2 s: questo tetto e' largo **per GNOME**.
#
# ⛔⛔ E OGNI ATTESA HA UN NOME SUO E UN VALORE SUO — `LEZIONI.md` §1.45.  Qui ce
#     ne sono cinque, e sono cinque perche' aspettano cinque cose diverse:
#
#       ATTESA_SESSIONE    la risposta `SESSIONE`         `[?]` 30 s, prudente
#       ATTESA_PALCO       che il palco NASCA             `[M]` 152 s — C1, sopra
#       ATTESA_PRIMO_FOTO  che il codificatore consegni   `[?]` 30 s, da tarare
#       ATTESA_SCENA       che la pagina compaia          `[?]` 90 s, da tarare
#       ATTESA_TASTO       che il pixel cambi             `[?]` 8 s, da tarare
#
#     ⚠ Il primo fotogramma si aspetta **ATTESA_PALCO + ATTESA_PRIMO_FOTO**: sono
#       due fenomeni in fila (prima nasce il palco, poi il codificatore consegna),
#       e sommarli e' l'unico modo di non prestare il tetto dell'uno all'altro.
#       ⛔ Un tetto solo, corto come il secondo, guarderebbe **sempre nella
#       finestra sbagliata** su GNOME — ed e' esattamente il difetto che C1 ha
#       pagato con dieci «non lo so» su dieci.
#     ⇒ Le quattro `[?]` sono **prudenti** e vanno misurate al primo giro vero:
#       sono scritte come tali nel rapporto, e ⛔ non si spacciano per misure.
ATTESA_SESSIONE = 30.0
ATTESA_PALCO = 152.0
ATTESA_PRIMO_FOTOGRAMMA = 30.0
ATTESA_SCENA = 90.0
ATTESA_TASTO = 8.0

# ⚠ La scatola in cui questa maglia gira: **gnome**, porta 8511.  ⛔ Il prodotto
#   sa avviare solo GNOME (`src/sessione.c:778`, tutto `src/mutter.c`): sulle
#   altre scatole C4 dara' **3**, e sara' giusto — non un rosso.
PORTA_PREDEFINITA = 8511


# ═══════════════════════════════════════════════════════════════════════════
# LA SCENA — ⭐ la scrive questo programma, coi colori di qui sopra
# ═══════════════════════════════════════════════════════════════════════════
def _esa(c):
    return "#%02X%02X%02X" % c


def scena_html(sorda=False):
    """La pagina bersaglio.  ⛔ `sorda=True` e' il guasto innestato di coda.

    ⚠ Le regole che questa pagina rispetta, e che `--certifica` ricontrolla:
      · ⛔ **niente che cambi da solo**: nessun `setTimeout`, nessuna
        animazione, nessuna transizione, nessuna risorsa esterna da scaricare.
        Una scena che si muove da sola toglie alla maglia la possibilita' di
        attribuire il cambiamento al tasto.
      · il bersaglio e' dichiarato **in percentuale del riquadro**, non in pixel:
        cosi' la stessa pagina vale su qualunque misura di tela.
      · ⭐ si accende al **primo tasto qualunque**, e ci resta.  C4 non chiede
        *quale* tasto (vedi «quel che C4 non guarda»).
    """
    ascolto = "" if sorda else """
 window.addEventListener('keydown', function () {
   document.getElementById('bersaglio').style.background = '%s';
 }, true);""" % _esa(COLORE_ARRIVO)
    return """<!doctype html>
<html lang="it"><head><meta charset="utf-8">
<title>C4 — il tasto arriva allo schermo</title>
<style>
 html, body { margin:0; padding:0; width:100%%; height:100%%;
              background:%(fondo)s; overflow:hidden; }
 #bersaglio { position:absolute; left:%(bx)s%%; top:%(by)s%%;
              width:%(bw)s%%; height:%(bh)s%%; background:%(partenza)s; }
</style></head>
<body><div id="bersaglio"></div>
<script>%(ascolto)s
</script></body></html>
""" % {"fondo": _esa(COLORE_FONDO),
       "partenza": _esa(COLORE_PARTENZA),
       "bx": "%g" % round(BERSAGLIO[0] * 100, 4),
       "by": "%g" % round(BERSAGLIO[1] * 100, 4),
       "bw": "%g" % round((BERSAGLIO[2] - BERSAGLIO[0]) * 100, 4),
       "bh": "%g" % round((BERSAGLIO[3] - BERSAGLIO[1]) * 100, 4),
       "ascolto": ascolto}


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL GIUDICE DEI PIXEL — «due PNG» non e' «il tasto e' arrivato»
# ═══════════════════════════════════════════════════════════════════════════
def _numpy_o_niente():
    try:
        import numpy
        return numpy
    except ImportError:
        return None


def _carica(percorso):
    """Un PNG come array int16, oppure ⛔ `None` se non ho potuto guardare.

    ⛔ `None` non e' «nero» e non e' «zero»: file che non c'e', file vuoto, PNG
       troncato, `numpy`/`Pillow` che mancano sono tutti *«non ho guardato»*, e
       questo progetto ha gia' pagato per averli confusi con un giudizio.
    """
    if not percorso or not os.path.exists(percorso) \
            or os.path.getsize(percorso) == 0:
        return None
    np = _numpy_o_niente()
    if np is None:
        return None
    try:
        from PIL import Image
        img = np.asarray(Image.open(percorso).convert("RGB")).astype("int16")
    except Exception:
        return None
    if img.ndim != 3 or img.shape[2] != 3 or img.size == 0:
        return None
    return img


def taglia(img, zona=ZONA):
    """Il rettangolo della zona attesa.  ⛔ `None` se non ci sta."""
    h, w = img.shape[0], img.shape[1]
    x0, y0 = int(round(zona[0] * w)), int(round(zona[1] * h))
    x1, y1 = int(round(zona[2] * w)), int(round(zona[3] * h))
    if x1 - x0 < 2 or y1 - y0 < 2:
        return None, None
    return img[y0:y1, x0:x1], (x0, y0, x1, y1)


def frazione_del_colore(pezzo, colore, tolleranza=TOLLERANZA):
    """Quanta parte di `pezzo` e' di quel colore, entro la tolleranza.

    ⚠ La distanza si prende **canale per canale** (norma del massimo) e non come
      somma: una somma lascerebbe passare un colore molto sbagliato su un canale
      solo, purche' azzeccato sugli altri due — e fra magenta e verde la
      differenza sta tutta in un canale per volta.
    """
    np = _numpy_o_niente()
    scarto = np.abs(pezzo - np.array(colore, dtype="int16")).max(axis=2)
    return float((scarto <= tolleranza).mean())


def frazione_cambiata(a, b, soglia=SOGLIA_CAMBIO):
    """Quanti pixel si scostano di piu' di `soglia` su almeno un canale."""
    np = _numpy_o_niente()
    return float((np.abs(a - b).max(axis=2) > soglia).mean())


def misura(png_prima, png_dopo, zona=ZONA):
    """Le sei grandezze su cui poggia tutto il giudizio.

    ⛔ Torna `None` — «non ho potuto guardare» — se una delle due immagini non
       si lascia leggere, oppure ⚠ **se le due hanno misure diverse**: due
       immagini di tela diversa non si confrontano, e fingere di farlo
       produrrebbe un numero che non vuol dire niente.
    """
    a = _carica(png_prima)
    b = _carica(png_dopo)
    if a is None or b is None:
        return None
    if a.shape != b.shape:
        return None
    za, box = taglia(a, zona)
    zb, _ = taglia(b, zona)
    if za is None or zb is None:
        return None
    _, cornice = taglia(a, TESTIMONE)
    if cornice is None:
        return None
    np = _numpy_o_niente()
    # ⭐ Le due maschere, e ⛔ **non sono l'una il complemento dell'altra**: la
    #   fascia in mezzo (dal 12 % al 35 % e dal 65 % all'88 %) non sta in
    #   nessuna delle due, e non si giudica.  E' il margine dichiarato che
    #   assorbe barre, decorazioni e scivolamenti della pagina.
    dentro = np.zeros(a.shape[:2], dtype=bool)
    dentro[box[1]:box[3], box[0]:box[2]] = True
    testimone = np.ones(a.shape[:2], dtype=bool)
    testimone[cornice[1]:cornice[3], cornice[0]:cornice[2]] = False
    diff = np.abs(a - b).max(axis=2) > SOGLIA_CAMBIO
    return {
        "larghezza": int(a.shape[1]), "altezza": int(a.shape[0]),
        "zona": box, "cornice": cornice,
        "prima_partenza": frazione_del_colore(za, COLORE_PARTENZA),
        "prima_arrivo": frazione_del_colore(za, COLORE_ARRIVO),
        "dopo_partenza": frazione_del_colore(zb, COLORE_PARTENZA),
        "dopo_arrivo": frazione_del_colore(zb, COLORE_ARRIVO),
        "dentro": float(diff[dentro].mean()),
        "testimone": (float(diff[testimone].mean())
                      if int(testimone.sum()) else 0.0),
    }


def giudica(m):
    """⭐ Il verdetto, e la sua ragione in una riga.

    Torna `(verdetto, motivo)` con `verdetto` in:
        True   il tasto e' arrivato fino allo schermo
        False  ⛔ ROSSO: la zona attesa non e' cambiata come doveva
        None   ⛔ non ho potuto guardare — e NON e' un rosso
    """
    if m is None:
        return None, "le immagini non si sono lasciate leggere (o hanno misure diverse)"

    # ── 1. PRIMA: la scena e' in vigore, e non e' gia' arrivata ────────────
    #
    # ⛔⛔ Questo caso si guarda PER PRIMO, ed e' il piu' importante di tutti:
    #    se la zona fosse gia' del colore d'arrivo, il controllo del «dopo»
    #    sarebbe verde qualunque cosa succeda — *un predicato che non puo'
    #    fallire*, `LEZIONI.md` §1.44.
    if m["prima_arrivo"] >= FRAZIONE_COLORE:
        return None, ("⛔ la zona era GIA' del colore d'arrivo PRIMA del tasto "
                      "(%.0f %%): la scena non parte dal colore di partenza, e "
                      "un «dopo» verde non proverebbe niente"
                      % (100 * m["prima_arrivo"]))
    if m["prima_partenza"] < FRAZIONE_COLORE:
        return None, ("⛔ la scena NON e' in vigore prima del tasto: nella zona "
                      "c'e' il colore di partenza solo per il %.0f %% (ne serve "
                      "il %.0f %%) — la pagina non e' comparsa, o non copre lo "
                      "schermo.  ⚠ Non e' un rosso di C4: e' un desktop che non "
                      "testimonia" % (100 * m["prima_partenza"],
                                      100 * FRAZIONE_COLORE))

    # ── 2. DOPO: la zona e' del colore d'arrivo, e 3. e' cambiata ──────────
    if m["dopo_arrivo"] < FRAZIONE_COLORE:
        return False, ("⛔ dopo il tasto la zona attesa NON e' del colore "
                       "d'arrivo: solo il %.0f %% (ne serve il %.0f %%)"
                       % (100 * m["dopo_arrivo"], 100 * FRAZIONE_COLORE))
    if m["dentro"] < CAMBIO_MINIMO_DENTRO:
        # ⚠ Il colore c'e' ma i pixel non si sono mossi: e' il caso in cui il
        #   «prima» e il «dopo» sono la stessa immagine.  ⛔ Va detto a parte,
        #   perche' e' un difetto del BANCO piu' che del prodotto.
        return False, ("⛔ la zona e' del colore d'arrivo ma solo il %.0f %% dei "
                       "suoi pixel e' cambiato (ne serve il %.0f %%): le due "
                       "immagini sono quasi identiche"
                       % (100 * m["dentro"], 100 * CAMBIO_MINIMO_DENTRO))

    # ── 3-bis. il cambiamento e' CONCENTRATO nella zona ────────────────────
    #
    # ⭐ E' il controllo che l'orologio nell'angolo non passa — al rovescio: qui
    #   la zona **e'** cambiata giusta, ma se si e' mossa anche la cornice, il
    #   merito non e' attribuibile al tasto.
    # ⚠ Ed e' un «non lo so», non un rosso: non si accusa il prodotto di una
    #   scena che si muove da sola.
    if m["testimone"] > CAMBIO_MASSIMO_TESTIMONE:
        return None, ("⚠ la zona e' cambiata giusta, ⛔ ma nella ZONA TESTIMONE "
                      "(la cornice) e' cambiato il %.0f %% (il tetto e' %.0f %%): "
                      "la scena si muove da sola e il cambiamento non e' "
                      "attribuibile al tasto"
                      % (100 * m["testimone"], 100 * CAMBIO_MASSIMO_TESTIMONE))

    return True, ("⭐ la zona attesa e' passata dal colore di partenza a quello "
                  "d'arrivo: %.0f %% dei suoi pixel cambiati, e nella cornice "
                  "solo il %.0f %%"
                  % (100 * m["dentro"], 100 * m["testimone"]))


def guasto_visto(verdetto, m):
    """⛔⛔ §1.52 — «il guasto e' stato visto» NON e' «il verdetto e' rosso».

    C4 puo' essere rossa **per conto suo**: il browser e' morto, la finestra si
    e' chiusa, la tela e' cambiata.  ⇒ Un predicato che guardasse solo il colore
    del verdetto direbbe «visto» anche se l'iniezione non avesse morso niente, e
    la certificazione della rete poggerebbe su un guasto del prodotto.

    ⭐ Si pretende una **differenza misurabile**, e sono due numeri:
      · la zona e' **ancora** del colore di partenza (⛔ non nera, non sparita);
      · dentro la zona e' cambiato al piu' `CAMBIO_RESIDUO` (5 %), contro il
        `CAMBIO_MINIMO_DENTRO` (60 %) che si pretende quando il tasto arriva
        davvero.  ⭐ **Un fattore dodici**, e sta scritto nelle costanti.
    """
    if verdetto is not False or m is None:
        return False
    return (m["dopo_partenza"] >= FRAZIONE_COLORE
            and m["dentro"] <= CAMBIO_RESIDUO)


def riga_misure(m):
    if m is None:
        return "non lo so"
    return ("zona %d,%d..%d,%d su %dx%d · PRIMA partenza %.0f %% arrivo %.0f %% · "
            "DOPO partenza %.0f %% arrivo %.0f %% · cambiati: dentro %.0f %%, "
            "testimone %.0f %%"
            % (m["zona"][0], m["zona"][1], m["zona"][2], m["zona"][3],
               m["larghezza"], m["altezza"],
               100 * m["prima_partenza"], 100 * m["prima_arrivo"],
               100 * m["dopo_partenza"], 100 * m["dopo_arrivo"],
               100 * m["dentro"], 100 * m["testimone"]))


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ LA CERTIFICAZIONE — si dimostra che il giudice sa dire verde, rosso e
#     «non lo so», e ⭐ che sa distinguere il guasto che ha morso da uno che no
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⚠ E si dichiara che cosa copre e che cosa no.

    COPRE: il **giudice** — la zona, i due colori, la tolleranza, i tre
    controlli poveri, la lettura del guasto innestato, e la coerenza fra la
    scena che si scrive e il colore che si cerca.
    ⛔ NON COPRE: che il tasto attraversi davvero il prodotto.  Quello lo dicono
    il giro vero e i suoi due guasti innestati, sulla scatola — ed e' l'altra
    meta' del collaudo.  ⇒ Una certificazione che si dichiara piu' larga di
    quel che e' vale meno di nessuna certificazione.
    """
    np = _numpy_o_niente()
    if np is None:
        print("⛔ manca numpy: non posso nemmeno certificarmi")
        print("   ⇒ non ho potuto guardare")
        return 3
    try:
        from PIL import Image
    except ImportError:
        print("⛔ manca Pillow: non posso nemmeno certificarmi")
        print("   ⇒ non ho potuto guardare")
        return 3
    import tempfile

    lav = tempfile.mkdtemp(prefix="c4cert-")
    L, A = 384, 216       # la stessa forma di uno schermo 16:9, in piccolo

    def dipingi(nome, bersaglio, fondo=COLORE_FONDO, macchia=None):
        """Uno schermo finto: fondo + bersaglio al 20..80 % + una macchia.

        ⚠ `macchia = (x0, y0, x1, y1, colore)` in frazioni: serve a mettere
          roba **fuori** dalla zona attesa — cioe' l'orologio nell'angolo.
        """
        img = np.zeros((A, L, 3), dtype="uint8")
        img[:, :] = fondo
        bx0, by0 = int(BERSAGLIO[0] * L), int(BERSAGLIO[1] * A)
        bx1, by1 = int(BERSAGLIO[2] * L), int(BERSAGLIO[3] * A)
        img[by0:by1, bx0:bx1] = bersaglio
        if macchia is not None:
            x0, y0, x1, y1, c = macchia
            img[int(y0 * A):int(y1 * A), int(x0 * L):int(x1 * L)] = c
        p = os.path.join(lav, nome + ".png")
        Image.fromarray(img).save(p)
        return p

    guai = 0
    print("== certificazione del giudice di C4 ==")
    print("   zona attesa %s (il %.0f %% dello schermo, in mezzo)"
          % (ZONA, 100 * (ZONA[2] - ZONA[0]) * (ZONA[3] - ZONA[1])))
    print("   zona testimone: tutto FUORI da %s (la cornice)" % (TESTIMONE,))
    print("   partenza %s · arrivo %s · tolleranza ±%d per canale"
          % (_esa(COLORE_PARTENZA), _esa(COLORE_ARRIVO), TOLLERANZA))
    print("   serve il %.0f %% della zona del colore · cambiati: dentro ≥ %.0f %%, "
          "testimone ≤ %.0f %%"
          % (100 * FRAZIONE_COLORE, 100 * CAMBIO_MINIMO_DENTRO,
             100 * CAMBIO_MASSIMO_TESTIMONE))
    print()

    # ── PARTE 1 · IL VERDETTO ──────────────────────────────────────────────
    verde = dipingi("v-prima", COLORE_PARTENZA)
    arrivato = dipingi("v-dopo", COLORE_ARRIVO)

    # ⭐ Il colore spostato di **quanto la tolleranza ammette**: profili di
    #    colore, 4:2:0, scala limitata.  Deve restare VERDE, o la soglia e'
    #    troppo stretta e la maglia si butta fra due settimane.
    spostato = tuple(min(255, max(0, c + s))
                     for c, s in zip(COLORE_ARRIVO, (-TOLLERANZA, +TOLLERANZA,
                                                     -TOLLERANZA)))
    # ⛔ E uno spostato TROPPO non deve passare, o la tolleranza non separa piu'
    #    niente: un colore ammesso comunque e' una tolleranza infinita.
    troppo = tuple(min(255, max(0, c + s))
                   for c, s in zip(COLORE_ARRIVO, (0, +3 * TOLLERANZA, 0)))

    casi = [
        # nome, png prima, png dopo, verdetto atteso
        ("⭐ il tasto arriva: la zona passa da partenza ad arrivo",
         verde, arrivato, True),

        ("⛔ nessun tasto: le due immagini sono identiche",
         verde, dipingi("r-dopo", COLORE_PARTENZA), False),

        # ⭐⭐⭐ IL CASO CHE CONTA DI PIU' (mandato di C4, e §4.3):
        #    cambia qualcosa FUORI dalla zona attesa — un orologio in un angolo
        #    che avanza — e dentro non cambia niente.  ⛔ DEVE essere ROSSO.
        ("⭐⭐ cambia SOLO fuori dalla zona (l'orologio nell'angolo) ⇒ ROSSO",
         dipingi("o-prima", COLORE_PARTENZA,
                 macchia=(0.02, 0.02, 0.20, 0.09, (0, 0, 0))),
         dipingi("o-dopo", COLORE_PARTENZA,
                 macchia=(0.02, 0.02, 0.20, 0.09, (255, 255, 255))),
         False),

        ("⛔ la zona cambia ma nel colore SBAGLIATO (la finestra si e' chiusa)",
         verde, dipingi("n-dopo", (0, 0, 0)), False),

        ("⭐ colore d'arrivo spostato di ±%d ⇒ dev'essere VERDE" % TOLLERANZA,
         verde, dipingi("t-dopo", spostato), True),

        ("⛔ colore d'arrivo spostato di ±%d ⇒ dev'essere ROSSO" % (3 * TOLLERANZA),
         verde, dipingi("tt-dopo", troppo), False),

        # ⚠ La scena non e' in vigore: un desktop qualunque, senza la pagina.
        #   ⛔ E' un «non lo so», non un rosso: un desktop che non testimonia non
        #   e' un prodotto che sbaglia.
        ("⚠ la scena non e' in vigore prima del tasto ⇒ «non lo so»",
         dipingi("s-prima", (58, 62, 70), fondo=(58, 62, 70)),
         dipingi("s-dopo", COLORE_ARRIVO), None),

        # ⛔⛔ Il predicato che non puo' fallire (§1.44): la zona e' GIA' del
        #    colore d'arrivo prima che il tasto parta.
        ("⛔⛔ la zona era GIA' arrivata PRIMA del tasto ⇒ «non lo so»",
         dipingi("g-prima", COLORE_ARRIVO), arrivato, None),

        # ⭐ La scena si muove da sola: la zona cambia giusta, ma anche mezzo
        #   schermo intorno.  ⇒ «non lo so», non verde.
        ("⭐ la zona e' giusta ma si muove anche la cornice ⇒ «non lo so»",
         dipingi("m-prima", COLORE_PARTENZA),
         dipingi("m-dopo", COLORE_ARRIVO, fondo=(240, 240, 240)), None),

        # ⭐⭐ IL CASO CHE LA PRIMA STESURA NON PASSAVA, e che ha corretto il
        #    disegno prima di qualunque giro vero: il bersaglio cambia **tutto
        #    intero** — che e' quel che succede sul vero — e la zona testimone
        #    resta ferma.  ⛔ Con un «fuori» fatto di tutto-il-resto, questo
        #    caso dava «non lo so», cioe' la maglia non sarebbe MAI diventata
        #    verde (`LEZIONI.md` §1.49).
        ("⭐⭐ il bersaglio cambia TUTTO INTERO (il caso vero) ⇒ VERDE",
         dipingi("b-prima", COLORE_PARTENZA), dipingi("b-dopo", COLORE_ARRIVO),
         True),

        # ⚠ E una barra in alto che si accende: sta NEL TESTIMONE, ma e' piccola.
        #   ⛔ Non deve rovinare un verde, o la maglia si romperebbe al primo
        #   desktop con una barra piu' larga — cioe' alla fase 12.
        ("⚠ una barra in alto si accende, e il tasto arriva ⇒ VERDE lo stesso",
         dipingi("br-prima", COLORE_PARTENZA,
                 macchia=(0.0, 0.0, 1.0, 0.04, (30, 30, 30))),
         dipingi("br-dopo", COLORE_ARRIVO,
                 macchia=(0.0, 0.0, 1.0, 0.04, (200, 200, 200))), True),
    ]

    for nome, pa, pb, atteso in casi:
        m = misura(pa, pb)
        v, perche = giudica(m)
        ok = (v is atteso)
        print("  %s  %-58s ⇒ %-11s (atteso %s)"
              % ("OK " if ok else "NO ", nome,
                 {True: "VERDE", False: "ROSSO", None: "non lo so"}[v],
                 {True: "VERDE", False: "ROSSO", None: "non lo so"}[atteso]))
        if not ok:
            guai += 1
            print("        ⛔ %s" % perche)
            print("        %s" % riga_misure(m))

    # ── PARTE 2 · «NON HO POTUTO GUARDARE» dev'essere `None`, non zero ────
    print()
    print("  ⛔ e «non ho potuto guardare» dev'essere «non lo so», mai un numero:")
    vuoto = os.path.join(lav, "vuoto.png")
    open(vuoto, "wb").close()
    # ⚠ Due immagini di misura diversa: non si confrontano, e fingere di farlo
    #   produrrebbe un numero senza senso.
    piccola = np.zeros((100, 100, 3), dtype="uint8")
    piccola[:, :] = COLORE_PARTENZA
    pic = os.path.join(lav, "piccola.png")
    Image.fromarray(piccola).save(pic)
    for nome, pa, pb in (("il file «prima» non c'e'",
                          os.path.join(lav, "manca.png"), arrivato),
                         ("il file «dopo» e' vuoto", verde, vuoto),
                         ("le due immagini hanno misure diverse", pic, arrivato)):
        m = misura(pa, pb)
        v, _ = giudica(m)
        ok = (m is None and v is None)
        print("  %s  %-58s ⇒ %s"
              % ("OK " if ok else "NO ", nome,
                 "non lo so" if ok else "⛔ ha giudicato lo stesso"))
        if not ok:
            guai += 1

    # ── PARTE 3 · IL GUASTO INNESTATO SI LEGGE SULLA DIFFERENZA (§1.52) ───
    print()
    print("  ⭐⭐ e «il guasto e' stato visto» non e' «il verdetto e' rosso»:")
    casi_guasto = [
        ("⭐ senza tasto: la zona e' ANCORA di partenza e non cambia ⇒ VISTO",
         verde, dipingi("gv-dopo", COLORE_PARTENZA), True),
        # ⛔ Rosso, ma per un'altra ragione: la finestra e' sparita.  L'iniezione
        #    non ha morso niente, e dire «visto» sarebbe certificare la rete su
        #    un guasto del prodotto.
        ("⛔ rosso perche' la finestra e' sparita ⇒ NON e' il guasto",
         verde, dipingi("gn-dopo", (0, 0, 0)), False),
        # ⛔ E il verde non e' mai «il guasto e' stato visto».
        ("⛔ verde ⇒ il guasto NON e' stato visto", verde, arrivato, False),
        # ⛔ E nemmeno «non ho potuto guardare» (§4.5, e il difetto del gancio
        #    del 27 agosto: un `3` scritto come «non l'ha visto» e' un'accusa a
        #    una prova che non ha guardato).
        ("⛔ «non lo so» ⇒ il guasto NON e' stato visto",
         dipingi("gi-prima", (58, 62, 70), fondo=(58, 62, 70)), arrivato, False),
    ]
    for nome, pa, pb, atteso in casi_guasto:
        m = misura(pa, pb)
        v, _ = giudica(m)
        avuto = guasto_visto(v, m)
        ok = (avuto == atteso)
        print("  %s  %-58s ⇒ %-9s (atteso %s)"
              % ("OK " if ok else "NO ", nome,
                 "VISTO" if avuto else "non visto",
                 "VISTO" if atteso else "non visto"))
        if not ok:
            guai += 1

    # ── PARTE 4 · LE COSTANTI SI CERTIFICANO COME UNA SOGLIA ──────────────
    #
    # ⭐ `LEZIONI.md` §1.45 e la lezione del tetto di C1: un numero che nessuno
    #   ricontrolla piu' e' un numero che un giorno guardera' nella finestra
    #   sbagliata.  Qui i numeri sono **geometrici**, e si ricontrollano da soli.
    print()
    print("  ⭐⭐ e le costanti si controllano fra loro, o si contraddicono in silenzio:")
    controlli = [
        ("la ZONA sta STRETTAMENTE dentro il BERSAGLIO della scena",
         ZONA[0] > BERSAGLIO[0] and ZONA[1] > BERSAGLIO[1]
         and ZONA[2] < BERSAGLIO[2] and ZONA[3] < BERSAGLIO[3],
         "zona %s · bersaglio %s · margine %.0f %% per lato"
         % (ZONA, BERSAGLIO, 100 * (ZONA[0] - BERSAGLIO[0]))),
        ("i due colori sono piu' lontani della tolleranza, e di molto",
         max(abs(a - b) for a, b in zip(COLORE_PARTENZA, COLORE_ARRIVO))
         > 3 * TOLLERANZA,
         "distanza per canale %d, tolleranza %d"
         % (max(abs(a - b) for a, b in zip(COLORE_PARTENZA, COLORE_ARRIVO)),
            TOLLERANZA)),
        ("il «cambia» col tasto e il «non cambia» senza sono separati da un fattore ≥ 10",
         CAMBIO_MINIMO_DENTRO >= 10 * CAMBIO_RESIDUO,
         "dentro ≥ %.2f col tasto · ≤ %.2f senza ⇒ fattore %.0f"
         % (CAMBIO_MINIMO_DENTRO, CAMBIO_RESIDUO,
            CAMBIO_MINIMO_DENTRO / CAMBIO_RESIDUO)),
        ("il tetto del testimone e' piu' basso del minimo «dentro»",
         CAMBIO_MASSIMO_TESTIMONE < CAMBIO_MINIMO_DENTRO,
         "testimone ≤ %.2f · dentro ≥ %.2f"
         % (CAMBIO_MASSIMO_TESTIMONE, CAMBIO_MINIMO_DENTRO)),
        # ⭐⭐ Il controllo che ha corretto il disegno: il TESTIMONE non deve
        #    toccare il BERSAGLIO, o vedrebbe cambiare la scena a ogni giro
        #    riuscito e la maglia non diventerebbe mai verde (§1.49).
        ("la ZONA TESTIMONE non tocca MAI il bersaglio della scena",
         TESTIMONE[0] < BERSAGLIO[0] and TESTIMONE[1] < BERSAGLIO[1]
         and TESTIMONE[2] > BERSAGLIO[2] and TESTIMONE[3] > BERSAGLIO[3],
         "testimone fuori da %s · bersaglio %s · margine %.0f %% (%.0f righe su "
         "1080)" % (TESTIMONE, BERSAGLIO, 100 * (BERSAGLIO[0] - TESTIMONE[0]),
                    1080 * (BERSAGLIO[0] - TESTIMONE[0]))),
        ("e il margine regge due barre di GNOME (40 righe l'una)",
         1080 * (BERSAGLIO[0] - TESTIMONE[0]) >= 80,
         "%.0f righe di margine" % (1080 * (BERSAGLIO[0] - TESTIMONE[0]))),
        # ⭐ La scena e il giudice condividono la costante: si verifica sul testo
        #   che il programma scrive davvero, non su una promessa.
        ("la scena dipinge ESATTAMENTE i colori che il giudice cerca",
         _esa(COLORE_PARTENZA) in scena_html()
         and _esa(COLORE_ARRIVO) in scena_html()
         and _esa(COLORE_FONDO) in scena_html(),
         "%s · %s · %s" % (_esa(COLORE_PARTENZA), _esa(COLORE_ARRIVO),
                           _esa(COLORE_FONDO))),
        ("la scena NON ha niente che cambi da solo",
         not any(x in scena_html() for x in
                 ("setTimeout", "setInterval", "requestAnimationFrame",
                  "animation", "transition", "http://", "https://")),
         "nessun timer, nessuna animazione, nessuna risorsa esterna"),
        ("la scena SORDA non ascolta la tastiera (guasto innestato di coda)",
         "keydown" in scena_html() and "keydown" not in scena_html(sorda=True),
         "sana: ascolta · sorda: non ascolta"),
        ("e la scena sorda dipinge lo stesso il colore di partenza",
         _esa(COLORE_PARTENZA) in scena_html(sorda=True)
         and _esa(COLORE_ARRIVO) not in scena_html(sorda=True),
         "⇒ il «prima» resta giudicabile, e il «dopo» non puo' arrivare"),
    ]
    for nome, ok, detto in controlli:
        print("  %s  %-58s  %s" % ("OK " if ok else "NO ", nome, detto))
        if not ok:
            guai += 1

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ I GRUPPI DELLA SCHEDA — ⛔ il caso che oggi non c'era.
    #
    # ⛔ Un inquilino fuori dai gruppi dei nodi `/dev/dri` fa nascere una
    #    sessione CIECA (`[M]` 0 su 4, zero fotogrammi, `fasi/10-…` §7.4) ⇒
    #    questa maglia misurerebbe il buio.  ⭐ Si pretende che dica «non ho
    #    potuto guardare», ⛔ e MAI rosso: e' un guasto del BANCO (§1.51).
    # ⚠ I casi vivono in C1, col passo che certificano: ⛔ una copia qui
    #   sarebbe un secondo posto da cui divergere (§1.47).
    # ═══════════════════════════════════════════════════════════════════════
    print()
    guai_gr, quanti_gr = casa_di_c1().certifica_gruppi("C4")
    guai += guai_gr

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐⭐ LA PROVVISTA CONDIVISA — ⛔ il caso che il 27 agosto 2026 non c'era,
    #    e per cui questa maglia ha detto «non ho potuto guardare» mentre la
    #    sessione era viva e dipinta.
    # ⚠ I casi vivono in C2, col codice che certificano: ⛔ una copia qui sarebbe
    #   un secondo posto da cui divergere (§1.47).
    # ═══════════════════════════════════════════════════════════════════════
    print()
    casa_pr = casa_della_provvista()
    if casa_pr is None:
        print("  NO   ⛔ non trovo `11-c2-…py`: la provvista non e' certificabile")
        guai += 1
        guai_pr, quanti_pr = 0, 0
    else:
        guai_pr, quanti_pr = casa_pr.certifica_la_provvista("C4", "c4u")
        guai += guai_pr

    quanti = (len(casi) + 3 + len(casi_guasto) + len(controlli)
              + quanti_gr + quanti_pr)
    print()
    if guai:
        print("⛔ il giudice NON e' affidabile: %d casi su %d sbagliati"
              % (guai, quanti))
        return 1
    print("⭐ %d casi su %d: il giudice sa dire VERDE, ROSSO e «non lo so»," % (quanti, quanti))
    print("   ⭐⭐ da' ROSSO quando cambia SOLO fuori dalla zona attesa,")
    print("   ⭐ regge uno spostamento di colore di ±%d, e ⛔ legge il guasto" % TOLLERANZA)
    print("   innestato sulla DIFFERENZA e non sul colore del verdetto.")
    # ⛔ La riga della provvista si stampa SOLO se i casi veri sono girati.
    if quanti_pr >= 4:
        print("   ⭐⭐ e LA PROVVISTA: un /tmp/mozilla di un'altra maglia non lo "
              "tocco, e il mio inquilino scrive lo stesso — ⛔ mai rosso")
    else:
        print("   ⚠ e LA PROVVISTA e' coperta SOLO a meta': i casi veri "
              "chiedono l'amministratore, e qui non li ho girati")
    print("⚠ e questa certificazione copre IL GIUDICE, non il percorso dell'input")
    print("  (vedi in testa): quello lo dicono il giro vero e i suoi due guasti.")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# IL TERRENO — ⛔ si prepara, e si VERIFICA che sia in vigore
# ═══════════════════════════════════════════════════════════════════════════
def sh(comando, secondi=180):
    return subprocess.run(["/bin/sh", "-c", comando],
                          capture_output=True, text=True, timeout=secondi)


def cliente_di_prova(percorso):
    """⭐ Il cliente RCP si IMPORTA, non si riscrive.

    ⛔ Tutta la stretta di mano QUIC/WebTransport, l'inquadratura di §6.1, i
       tipi di §7.3 e la raccolta dei fotogrammi dal filo stanno li' dentro e
       sono gia' passati per l'arbitro di B4.  Riscriverne qui una copia
       vorrebbe dire due clienti che possono divergere in silenzio.
    ⇒ Se non c'e', o se non si lascia importare, questa maglia esce **3**.
    """
    if not percorso or not os.path.exists(percorso):
        return None
    spec = importlib.util.spec_from_file_location("b3cliente", percorso)
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except Exception:
        return None
    return m


def giudice_immagini():
    """⭐ Il giudice «nero / tinta unita / disegnato» si IMPORTA anche lui.

    ⚠ Qui non decide il verdetto — quello lo decide la zona attesa — ma dice
      **perche'** un «prima» non e' in vigore: *«lo schermo era nero»* e *«la
      pagina non e' comparsa»* sono due diagnosi diverse, e portarle tutt'e due
      costa una riga.  ⛔ Se manca, si tira avanti senza: e si dice.
    """
    for base in (QUI, os.path.dirname(QUI)):
        perc = os.path.join(base, "10-f1-testimone.py")
        if os.path.exists(perc):
            spec = importlib.util.spec_from_file_location("testimone10f1", perc)
            m = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(m)
                return m
            except Exception:
                return None
    return None


def crea(chi, parola):
    """L'inquilino, ⛔ **da zero**, e creato **come lo crea il prodotto**.

    ⛔⛔ E SI CANCELLA PRIMA DI CREARLO.  `LEZIONI.md` §1.39, e la riga che C1 ha
       pagato: `id -u X || useradd X` fa un utente nuovo **soltanto la prima
       volta che il banco gira in vita sua**.  ⇒ «Da zero» comprende anche «da
       zero rispetto a me stesso di ieri».
    """
    sh("loginctl terminate-user %s 2>/dev/null; pkill -KILL -u %s 2>/dev/null; "
       "userdel -r %s 2>/dev/null; rm -rf /home/%s" % (chi, chi, chi, chi))
    # ⛔⛔ I GRUPPI DELLA SCHEDA NON STANNO PIU' DENTRO IL `useradd`.
    #     `usermod -aG video,render` inchiodava due nomi — che sono di UNA
    #     distribuzione — e ⛔ **non rileggeva**: `usermod` riuscito non vuol
    #     dire «ci sta dentro» (E1, «scritto non e' in vigore»).
    # ⭐ Li da' `attrezzi-gruppi-scheda.sh`, che li LEGGE dai nodi `/dev/dri` e
    #   poi VERIFICA confrontando i numeri.  ⇒ Qui non c'e' piu' nessun nome di
    #   gruppo e nessun numero.
    # ⛔ E senza, `[M]` la sessione nasce CIECA (0 su 4, zero fotogrammi,
    #   `fasi/10-…` §7.4): questa maglia misurerebbe il buio e lo chiamerebbe
    #   difetto del prodotto.  ⇒ Non si misura: chi chiama esce **3**.
    r = sh("useradd -m -s /bin/bash %s && "
           "printf '%s:%s\n' | chpasswd" % (chi, chi, parola))
    if r.returncode != 0:
        return False, (r.stderr or "").strip()[:120]
    e_gr, perche_gr = garantisci_i_gruppi(chi, prefisso="      ")
    if e_gr != 0:
        return False, perche_gr
    # ⭐⭐ E LA PROVVISTA, subito dopo il `useradd -m` che copia lo scheletro:
    #    e' li' che l'inquilino nasce con `~/.cache` puntata a `/tmp`, ⇒ e' li'
    #    che gli si da' la sua.  ⛔ Prima di accendere qualunque cosa.
    fatto_cura, perche_cura = cura_della_provvista(chi)
    if not fatto_cura:
        return False, perche_cura
    return True, ""


def sgombra(chi, attesa=45.0):
    """⛔ Si aspetta che se ne sia andato DAVVERO, non mezzo secondo a orologio.

    ⚠ E' la cura di C1: `[M]` 26 agosto 2026, dieci giri, un'alternanza perfetta
      fra «non lo so» e «cieca» — uno stato che sopravviveva al giro.
    """
    sh("loginctl terminate-user %s 2>/dev/null" % chi)
    time.sleep(1.0)
    sh("pkill -KILL -u %s 2>/dev/null" % chi)
    scadenza = time.time() + attesa
    while time.time() < scadenza:
        viva = sh("loginctl show-user %s >/dev/null 2>&1" % chi).returncode == 0
        proc = sh("pgrep -u %s >/dev/null 2>&1" % chi).returncode == 0
        if not viva and not proc:
            return True
        time.sleep(0.5)
    return False


def scrivi_la_scena(chi, sorda):
    """⭐ La scena si scrive **in casa dell'inquilino**, e nuova a ogni giro.

    ⛔ E non nella cartella di lavoro del banco: `[M]` 26 agosto 2026, C8 —
       quella e' di `root`, e il browser gira **da utente**.  Il difetto la'
       usciva come «il browser non ha disegnato», cioe' ⛔ il banco dava rosso a
       se stesso e lo attribuiva al prodotto (`LEZIONI.md`, §7-bis.10).
    """
    perc = "/home/%s/.c4-scena.html" % chi
    try:
        with open(perc, "w") as f:
            f.write(scena_html(sorda=sorda))
    except OSError as e:
        return None, str(e)[:120]
    sh("chown %s:%s %s; chmod 644 %s" % (chi, chi, perc, perc))
    return perc, None


def apri_la_scena(chi, browser, pagina, registro):
    """Accende il browser DENTRO la sessione dell'inquilino, a schermo intero.

    ⛔ Il socket di Wayland si CERCA, non si indovina: il nome dipende da come
       il compositore e' nato, e inchiodare `wayland-0` qui vorrebbe dire una
       maglia che funziona su un desktop e tace sugli altri — cioe' il difetto
       che questa fase esiste per non introdurre.
    """
    uid = sh("id -u %s" % chi).stdout.strip()
    if not uid:
        return None, "non so l'uid di %s" % chi
    rtd = "/run/user/%s" % uid
    soc = sh("ls %s 2>/dev/null | grep -E '^wayland-[0-9]+$' | head -1" % rtd)
    display = soc.stdout.strip()
    if not display:
        return None, ("in %s non c'e' nessun socket wayland: la sessione non ha "
                      "un compositore a cui il browser possa parlare" % rtd)
    sh("runuser -u %s -- env XDG_RUNTIME_DIR=%s WAYLAND_DISPLAY=%s "
       "MOZ_ENABLE_WAYLAND=1 XDG_SESSION_TYPE=wayland HOME=/home/%s "
       "%s --kiosk file://%s > %s 2>&1 &"
       % (chi, rtd, display, chi, browser, pagina, registro), secondi=30)
    return display, None


# ═══════════════════════════════════════════════════════════════════════════
# IL FILO — ⭐ una connessione sola, e ci sta dentro tutto il giro
# ═══════════════════════════════════════════════════════════════════════════
def fabbrica_cliente(B3):
    """⭐ Il cliente di prova, **piu' i due messaggi che non sapeva mandare**.

    ⛔ §7.3: `LETTERA` e `POSIZIONE_TASTO` viaggiano sul **canale di input** —
       uno stream unidirezionale solo, aperto dopo `SESSIONE` e tenuto aperto —
       e portano `u32 id` (crescente su tutto il canale, `0` riservato) e
       `u64 istante` in microsecondi dell'orologio monotono del client.
    ⚠ L'`id` e' quello di `apri_input()`/`inp_id` del cliente importato: si
      **continua la sua numerazione**, non se ne apre una seconda.  Due contatori
      sullo stesso canale sarebbero due verita' sullo stesso fatto.
    """

    class ClienteCoiTasti(B3.Cliente):
        def _manda_input(self, tipo, resto):
            sid = self.apri_input()
            self.inp_id += 1
            # ⛔ §7.3, rilievo R1.27: microsecondi VERI.  Non si moltiplicano i
            #    millisecondi per mille per far credere a una precisione che non
            #    si ha — e su Linux `time.monotonic()` ha grana di nanosecondi.
            ist = int(time.monotonic() * 1_000_000)
            b = B3.inquadra(tipo, struct.pack("!IQ", self.inp_id, ist) + resto)
            self._quic.send_stream_data(sid, b, end_stream=False)
            self.transmit()
            return self.inp_id

        def manda_lettera(self, carattere):
            """§7.3 `LETTERA` — un valore scalare Unicode."""
            return self._manda_input(T_LETTERA, struct.pack("!I", carattere))

        def manda_posizione_tasto(self, codice, premuto):
            """§7.3 `POSIZIONE_TASTO` — codice **evdev**, premuto/rilasciato."""
            return self._manda_input(
                T_POSIZIONE_TASTO, struct.pack("!HB", codice, 1 if premuto else 0))

    return ClienteCoiTasti


def fetta_di_flusso(fotogrammi, percorso):
    """I fotogrammi di una finestra di tempo, messi in un file `.264`.

    ⛔ Si parte dalla prima **chiave**: un flusso che comincia con un fotogramma
       differenziale non si decodifica, e ffmpeg produrrebbe o niente o
       un'immagine sporca — cioe' artefatti **nostri del banco**, la risposta
       sbagliata alla domanda che questa maglia esiste per fare.
    ⛔ E si ordina per NUMERO (§6.2): gli stream sono indipendenti e possono
       arrivare fuori ordine.
    ⇒ Torna `None` se in quella finestra non e' arrivata nessuna chiave.
    """
    ordinati = sorted(fotogrammi, key=lambda f: f[0])
    inizio = None
    for i, f in enumerate(ordinati):
        if f[1]:
            inizio = i
            break
    if inizio is None:
        return None
    with open(percorso, "wb") as f:
        for x in ordinati[inizio:]:
            f.write(x[4])
    return len(ordinati) - inizio


def _decodifica(flusso, fuori):
    """⛔ `-update 1` tiene l'ULTIMO fotogramma: e' quel che il desktop mostra
       ADESSO.  Il primo sarebbe la chiave d'apertura, cioe' un secondo fa."""
    d = sh("ffmpeg -hide_banner -loglevel error -i %s -vsync 0 -update 1 -y %s"
           % (flusso, fuori), secondi=180)
    if d.returncode != 0 or not os.path.exists(fuori) \
            or os.path.getsize(fuori) == 0:
        return None
    return fuori


async def scatta(B3, cli, lavoro, nome, secondi):
    """Una fotografia della sessione, **senza staccarsi**.

    ⇒ Torna `(png|None, quanti_fotogrammi, perche'|None)`.
    ⛔ Tre esiti e non due: «il PNG c'e'», «non e' arrivato nessun fotogramma»,
       «sono arrivati ma non se n'e' fatta un'immagine» — e i due ultimi sono
       *«non ho guardato»*, non «lo schermo era vuoto».
    """
    n0 = len(cli.v_fotogrammi)
    # ⛔ UN DESKTOP FERMO NON MANDA FOTOGRAMMI: il server spedisce solo quel che
    #    cambia.  ⇒ Si CHIEDE una chiave, o il «prima» di una scena immobile
    #    sarebbe sempre vuoto e la maglia direbbe «non lo so» per sempre.
    #    ⚠ E' lo stesso motivo per cui il cliente ha `--chiave-dopo` (§6.2).
    ultimo = max((f[0] for f in cli.v_fotogrammi), default=0)
    try:
        cli.manda(B3.inquadra(B3.T["RICHIEDI_CHIAVE"], struct.pack("!I", ultimo)))
    except Exception as e:
        return None, 0, "non ho potuto chiedere una chiave: %s" % str(e)[:80]
    # ⛔ Si aspetta con gli occhi aperti: un `sleep` non si accorgerebbe che la
    #    sessione e' caduta, e il banco misurerebbe se stesso (R8.2/R8.4).
    try:
        await asyncio.wait_for(cli.caduto.wait(), timeout=secondi)
        return None, 0, "la sessione e' caduta mentre guardavo: %s" % cli.caduta
    except asyncio.TimeoutError:
        pass
    fetta = cli.v_fotogrammi[n0:]
    if not fetta:
        return None, 0, ("nessun fotogramma e' arrivato dal filo in %.0f s "
                         "(palco che non consegna, o sessione senza monitor)"
                         % secondi)
    flusso = os.path.join(lavoro, "%s.264" % nome)
    quanti = fetta_di_flusso(fetta, flusso)
    if quanti is None:
        return None, len(fetta), ("%d fotogrammi arrivati ma nessuna chiave: non "
                                  "so da dove cominciare a decodificare"
                                  % len(fetta))
    fuori = os.path.join(lavoro, "%s.png" % nome)
    # ⚠ ffmpeg puo' metterci parecchio: gira in un filo suo, o il cliente
    #   smetterebbe di leggere dal socket e la connessione cadrebbe da sola.
    png = await asyncio.to_thread(_decodifica, flusso, fuori)
    if png is None:
        return None, quanti, ("%d fotogrammi sono arrivati ma ffmpeg non ne ha "
                              "fatto un'immagine" % quanti)
    return png, quanti, None


async def aspetta_la_scena(B3, cli, a, lavoro):
    """⛔ SI ASPETTA L'EVENTO, NON L'OROLOGIO.

    `[M]` 26 agosto 2026, C1: con un'attesa fissa **sei giri su sei** hanno detto
    «non lo so» — non perche' qualcosa fosse rotto, ma perche' il banco guardava
    troppo presto.  ⇒ Qui si guarda **finche' la scena compare**, e se non compare
    entro il tempo dichiarato l'esito e' «non lo so», ⛔ mai un verde.

    Torna `(png|None, perche')` — l'immagine e' gia' il «prima».
    """
    scadenza = time.time() + a.attesa_scena
    ultimo_perche = "la scena non e' comparsa in %.0f s" % a.attesa_scena
    giro = 0
    while time.time() < scadenza:
        giro += 1
        png, quanti, perche = await scatta(
            B3, cli, lavoro, "prima-%02d" % giro, a.passo_scena)
        if png is None:
            ultimo_perche = perche
            continue
        img = _carica(png)
        if img is None:
            ultimo_perche = "l'immagine non si e' lasciata leggere"
            continue
        pezzo, _ = taglia(img)
        fr = frazione_del_colore(pezzo, COLORE_PARTENZA)
        if fr >= FRAZIONE_COLORE:
            return png, ("la scena e' in vigore: la zona e' del colore di "
                         "partenza per il %.0f %% (dopo %d tentativi)"
                         % (100 * fr, giro))
        ultimo_perche = ("la zona e' del colore di partenza solo per il %.0f %% "
                         "(ne serve il %.0f %%)"
                         % (100 * fr, 100 * FRAZIONE_COLORE))
    return None, ultimo_perche


async def il_giro(B3, a, chi, lavoro):
    """Il giro vero: una connessione sola, e dentro tutto.

    ⇒ Torna `(png_prima, png_dopo, note)`; i due `None` vogliono dire «non ho
      potuto guardare», e la nota dice **perche'**.
    """
    note = []
    Cl = fabbrica_cliente(B3)
    conf = B3.QuicConfiguration(is_client=True, alpn_protocols=B3.H3_ALPN,
                                max_datagram_frame_size=65536)
    conf.verify_mode = B3.ssl.CERT_NONE
    autorita = "%s:%d" % (a.indirizzo, a.porta)

    async with B3.connect(a.indirizzo, a.porta, configuration=conf,
                          create_protocol=Cl) as cli:
        await asyncio.wait_for(cli.wait_connected(), timeout=8)
        cli.apri_sessione(autorita, a.percorso)
        stato = await asyncio.wait_for(cli.accettata, timeout=8)
        if stato != "200":
            return None, None, ["la CONNECT estesa ha risposto %s" % stato]
        cli.apri_controllo()

        # ⚠ LA SEQUENZA D'ATTACCO E' RICOPIATA DA `principale()` del cliente:
        #   quel programma e' un pezzo unico governato da `argparse` e non si
        #   puo' chiamare a meta'.  ⛔ Se la stretta di mano cambia, questa
        #   maglia va aggiornata a mano — ed e' il debito dichiarato in testa.
        # ⚠ Si dichiara **H.264**, e va detto: il PNG lo fa `ffmpeg` dai byte del
        #   filo, e restringere l'intersezione e' un uso del protocollo, non un
        #   aggiramento (§4.3).  ⛔ E i numeri presi con codec diversi non si
        #   confrontano — qui non se ne prendono, ma la regola vale lo stesso.
        cli.manda(B3.inquadra(
            B3.T["CIAO"], B3.corpo_ciao(audio="pcm", video="h264", prof="8,10")))
        await B3.attendi(cli, "ECCOMI")
        cli.manda(B3.inquadra(B3.T["CREDENZIALI"], B3.s(chi) + B3.s(a.parola)))
        # ⚠ §4.4-bis: l'AMMESSO ha un ritardo fisso di un secondo.  ⛔ Qui non si
        #   giudica (quella e' un'altra maglia): si aspetta abbastanza.
        await B3.attendi(cli, "AMMESSO", attesa=30)
        cli.manda(B3.inquadra(
            B3.T["ATTACCA"],
            struct.pack("!IIII", a.larghezza, a.altezza, a.larghezza, a.altezza)
            + B3.s(a.disposizione)))
        nome, corpo, _ = await B3.attendi(cli, "SESSIONE",
                                          attesa=a.attesa_sessione)
        lar, alt = struct.unpack("!II", corpo[1:9])
        note.append("SESSIONE: tela %dx%d" % (lar, alt))

        # ── il palco: si aspetta il PRIMO FOTOGRAMMA ───────────────────────
        #
        # ⭐ E non «il registro dice monitor»: quello lo guarda C1.  Qui serve
        #   che il filo consegni pixel, che e' lo strato di sopra.
        # ⛔ E si aspetta l'EVENTO: la scadenza produce «non lo so», mai un verde.
        # ⚠ Il tetto e' la SOMMA di due attese distinte (vedi in testa): il palco
        #   che nasce `[M]` (fino a 152 s su GNOME) e il codificatore che
        #   consegna `[?]`.
        tetto = a.attesa_palco + a.attesa_primo_fotogramma
        t0 = time.monotonic()
        scadenza = time.time() + tetto
        while time.time() < scadenza and not cli.v_fotogrammi:
            try:
                await asyncio.wait_for(cli.caduto.wait(), timeout=1.0)
                return None, None, note + ["la sessione e' caduta aspettando il "
                                           "primo fotogramma: %s" % cli.caduta]
            except asyncio.TimeoutError:
                pass
        if not cli.v_fotogrammi:
            return None, None, note + [
                "nessun fotogramma in %.0f s (palco %.0f + codificatore %.0f): "
                "il palco non consegna"
                % (tetto, a.attesa_palco, a.attesa_primo_fotogramma)]
        # ⭐ E il tempo si STAMPA: e' il numero da cui si tarano le `[?]`, e senza
        #   scriverlo la prossima taratura sarebbe di nuovo un'indovinata.
        note.append("il palco consegna: primo fotogramma dopo %.1f s dal SESSIONE"
                    % (time.monotonic() - t0))

        # ── la sveglia — ⛔ PRIMA di aprire la scena, e il perche' e' in testa ─
        if a.sveglia > 0:
            for _ in range(a.sveglia):
                cli.manda_posizione_tasto(ESC_EVDEV, True)
                await asyncio.sleep(0.06)
                cli.manda_posizione_tasto(ESC_EVDEV, False)
                await asyncio.sleep(0.12)
            note.append("sveglia: %d ESC mandati PRIMA che la scena esista "
                        "(⇒ non possono dipingerla)" % a.sveglia)
            await asyncio.sleep(a.attesa_sveglia)

        # ── la scena ───────────────────────────────────────────────────────
        pagina, err = scrivi_la_scena(chi, a.scena_sorda)
        if pagina is None:
            return None, None, note + ["non ho potuto scrivere la scena: %s" % err]
        note.append("scena scritta in %s%s"
                    % (pagina, "  ⛔ SORDA (guasto innestato)"
                       if a.scena_sorda else ""))
        display, err = apri_la_scena(chi, a.browser, pagina,
                                     "/tmp/c4-%s.log" % chi)
        if display is None:
            return None, None, note + ["non ho potuto aprire la scena: %s" % err]
        note.append("browser acceso su %s" % display)

        png_prima, perche = await aspetta_la_scena(B3, cli, a, lavoro)
        note.append(perche)
        if png_prima is None:
            return None, None, note

        # ── ⭐ IL TASTO ─────────────────────────────────────────────────────
        if a.senza_tasto:
            note.append("⛔ GUASTO INNESTATO: il tasto NON e' stato mandato")
        else:
            for i in range(a.ripetizioni):
                if a.tasto == "posizione":
                    cli.manda_posizione_tasto(a.codice_evdev, True)
                    await asyncio.sleep(0.06)
                    cli.manda_posizione_tasto(a.codice_evdev, False)
                else:
                    cli.manda_lettera(a.lettera)
                if i + 1 < a.ripetizioni:
                    await asyncio.sleep(a.pausa_tasto)
            note.append("mandati %d tasti (%s, id fino a %d)"
                        % (a.ripetizioni,
                           "POSIZIONE_TASTO evdev %d" % a.codice_evdev
                           if a.tasto == "posizione"
                           else "LETTERA U+%04X" % a.lettera,
                           cli.inp_id))

        # ── e l'immagine DOPO ──────────────────────────────────────────────
        png_dopo, quanti, perche = await scatta(
            B3, cli, lavoro, "dopo", a.attesa_tasto)
        if png_dopo is None:
            return png_prima, None, note + ["il «dopo» non si e' fatto "
                                            "guardare: %s" % perche]
        note.append("«dopo» preso da %d fotogrammi" % quanti)
        return png_prima, png_dopo, note


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--utente", default="c4u1",
                   help="⛔ si cancella e si ricrea a ogni giro: «da zero» "
                        "comprende «da zero rispetto a me stesso di ieri»")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=PORTA_PREDEFINITA)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--browser", default="firefox-esr")
    p.add_argument("--lavoro", default="/var/lib/rete11/c4")
    p.add_argument("--larghezza", type=int, default=1920)
    p.add_argument("--altezza", type=int, default=1080)
    p.add_argument("--disposizione", default="it")

    p.add_argument("--tasto", choices=("lettera", "posizione"), default="lettera",
                   help="⭐ quale messaggio di §7.3 si usa. «lettera» attraversa "
                        "anche la mappa di src/tastiera.c, ed e' il percorso "
                        "piu' lungo: e' il predefinito apposta")
    p.add_argument("--lettera", type=lambda x: int(x, 0), default=LETTERA,
                   help="il valore scalare Unicode della LETTERA (predefinito «a»)")
    p.add_argument("--codice-evdev", type=int, default=ESC_EVDEV,
                   help="il codice evdev di POSIZIONE_TASTO (1 = ESC)")
    p.add_argument("--ripetizioni", type=int, default=3,
                   help="⚠ non e' «sperare»: [M] 23 ago 2026 (09-b72) una "
                        "sessione GNOME appena nata puo' consumare il primo "
                        "tasto per uscire dalla vista d'insieme. ⛔ E se NESSUNO "
                        "dei tasti fa cambiare un pixel, il percorso e' rotto")
    p.add_argument("--pausa-tasto", type=float, default=0.15)

    p.add_argument("--sveglia", type=int, default=1,
                   help="quanti ESC mandare PRIMA di aprire la scena, per uscire "
                        "dalla vista d'insieme di GNOME. ⛔ Prima, non dopo: "
                        "dopo dipingerebbero il bersaglio da soli")
    p.add_argument("--senza-sveglia", action="store_true",
                   help="⭐ toglie la sveglia: da usare per misurare se serve "
                        "ancora. ⛔ Un gesto non si tiene perche' «male non fa»")
    p.add_argument("--attesa-sveglia", type=float, default=3.0)

    p.add_argument("--attesa-sessione", type=float, default=ATTESA_SESSIONE,
                   help="quanto si aspetta la risposta SESSIONE. ⚠ [?] prudente")
    p.add_argument("--attesa-palco", type=float, default=ATTESA_PALCO,
                   help="quanto si da' al PALCO per nascere. ⭐ 152 s = il "
                        "massimo misurato su GNOME (101,0 s) piu' meta' — [M] "
                        "27 ago 2026, C1")
    p.add_argument("--attesa-primo-fotogramma", type=float,
                   default=ATTESA_PRIMO_FOTOGRAMMA,
                   help="quanto si da' al CODIFICATORE dopo che il palco c'e'. "
                        "⚠ [?] non misurato: si SOMMA all'attesa del palco, "
                        "perche' sono due fenomeni in fila (§1.45)")
    p.add_argument("--attesa-scena", type=float, default=ATTESA_SCENA,
                   help="quanto si aspetta che la pagina compaia nella zona. "
                        "⚠ [?] non misurato: comprende il PRIMO avvio di Firefox "
                        "in una scatola fredda, che [M] passa i 25 s (C8, §1.45)")
    p.add_argument("--passo-scena", type=float, default=5.0,
                   help="ogni quanto si riguarda, aspettando la scena")
    p.add_argument("--attesa-tasto", type=float, default=ATTESA_TASTO,
                   help="quanto si aspetta che il pixel cambi. ⚠ [?] da tarare")
    p.add_argument("--attesa-sgombero", type=float, default=45.0)

    p.add_argument("--senza-tasto", action="store_true",
                   help="⛔ GUASTO INNESTATO (testa): si fa tutto tranne mandare "
                        "il tasto. La maglia DEVE dare rosso")
    p.add_argument("--scena-sorda", action="store_true",
                   help="⛔ GUASTO INNESTATO (coda): la scena si scrive senza il "
                        "gestore di tastiera. La maglia DEVE dare rosso")
    p.add_argument("--tieni-inquilino", action="store_true",
                   help="⚠ solo per diagnosi: non sgombra alla fine")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    if a.senza_sveglia:
        a.sveglia = 0
    innestato = a.senza_tasto or a.scena_sorda

    if os.geteuid() != 0:
        print("⛔ va eseguita da amministratore: deve creare un inquilino")
        sys.exit(2)

    # ── il terreno, e le cose senza le quali non si giudica ────────────────
    if _numpy_o_niente() is None:
        print("⛔ nella scatola non c'e' numpy: non so guardare un pixel")
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    B3 = cliente_di_prova(a.cliente)
    if B3 is None:
        print("⛔ non trovo (o non riesco a importare) il cliente di prova: %s"
              % a.cliente)
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    if getattr(B3, "AIOQUIC", None) is not None:
        print("⛔ nella scatola manca `aioquic`: il cliente non puo' nemmeno "
              "provarci (%s)" % B3.AIOQUIC)
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    if sh("command -v %s" % a.browser).returncode != 0:
        print("⛔ nella scatola non c'e' %s: non ho una scena da mettere sullo "
              "schermo" % a.browser)
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    if sh("command -v ffmpeg").returncode != 0:
        print("⛔ nella scatola non c'e' ffmpeg: i fotogrammi non diventano "
              "un'immagine")
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)

    os.makedirs(a.lavoro, exist_ok=True)
    giudice = giudice_immagini()

    print("== C4 — il tasto arriva fino allo schermo ==")
    print("   inquilino «%s» (NUOVO) · porta %d · tela %dx%d"
          % (a.utente, a.porta, a.larghezza, a.altezza))
    print("   la scena: bersaglio dal %.0f %% all'%.0f %% dello schermo, "
          "%s → %s al primo tasto"
          % (100 * BERSAGLIO[0], 100 * BERSAGLIO[2],
             _esa(COLORE_PARTENZA), _esa(COLORE_ARRIVO)))
    print("   la ZONA ATTESA: dal %.0f %% al %.0f %% in tutt'e due i versi "
          "(il %.0f %% dello schermo, in mezzo)"
          % (100 * ZONA[0], 100 * ZONA[2],
             100 * (ZONA[2] - ZONA[0]) * (ZONA[3] - ZONA[1])))
    print("   la ZONA TESTIMONE: la cornice, tutto fuori dal %.0f..%.0f %% — "
          "li' non deve cambiare niente"
          % (100 * TESTIMONE[0], 100 * TESTIMONE[2]))
    print("   il metro: %.0f %% della zona del colore ±%d · cambiati dentro "
          "≥ %.0f %% · testimone ≤ %.0f %%"
          % (100 * FRAZIONE_COLORE, TOLLERANZA, 100 * CAMBIO_MINIMO_DENTRO,
             100 * CAMBIO_MASSIMO_TESTIMONE))
    print("   il tasto: %s × %d"
          % ("POSIZIONE_TASTO evdev %d" % a.codice_evdev
             if a.tasto == "posizione" else "LETTERA U+%04X" % a.lettera,
             a.ripetizioni))
    if a.senza_tasto:
        print("   ⛔ GUASTO INNESTATO (testa): il tasto NON verra' mandato")
    if a.scena_sorda:
        print("   ⛔ GUASTO INNESTATO (coda): la scena non ascolta la tastiera")
    if giudice is None:
        print("   ⚠ non trovo 10-f1-testimone.py: il «prima» sara' diagnosticato "
              "senza la sua parola («nero» / «disegnato»)")
    print()

    # ⭐ PRIMA di `crea`: `crea` fa `userdel -r`, e da quel momento il padrone di
    #   `/tmp/mozilla` sarebbe un NUMERO invece di un nome — cioe' non lo
    #   riconoscerei piu' come mio.  ⛔ La mia base e' il nome senza le cifre in
    #   coda: «c4u1» ⇒ «c4u».
    resto = sgombra_il_mio_rimasuglio(re.sub(r"\d+$", "", a.utente))
    print("   provvista: la cura di src/provisiona.sh, importata da C2, "
          "all'inquilino che creo")
    if resto:
        print("   %s" % resto)

    fatto, perche = crea(a.utente, a.parola)
    if not fatto:
        print("⛔ non sono riuscito a creare «%s»: %s" % (a.utente, perche))
        print("   ⇒ il terreno non regge")
        sys.exit(2)

    png_prima = png_dopo = None
    note = []
    try:
        png_prima, png_dopo, note = asyncio.run(il_giro(B3, a, a.utente, a.lavoro))
    except Exception as e:
        note = ["il giro si e' interrotto: %s: %s" % (type(e).__name__, str(e)[:160])]
    finally:
        if not a.tieni_inquilino:
            if not sgombra(a.utente, a.attesa_sgombero):
                note.append("⚠ «%s» non se n'e' andato in %.0f s"
                            % (a.utente, a.attesa_sgombero))

    for n in note:
        print("   ·  %s" % n)

    # ── e la diagnosi del «prima», quando c'e' il testimone ────────────────
    if giudice is not None and png_prima:
        g = giudice.giudica(png_prima)
        if g is not None:
            print("   ·  il «prima», visto dal testimone di 10-f1: %s "
                  "(media %.1f, accesi %.5f)"
                  % (g["verdetto"], g["media"], g["accesi"]))

    m = misura(png_prima, png_dopo)
    verdetto, motivo = giudica(m)
    print()
    print("   %s" % riga_misure(m))
    print("   %s" % motivo)
    print()

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔ COL GUASTO INNESTATO L'ESITO SI LEGGE AL CONTRARIO: `0` = visto.
    #    E «visto» si legge sulla DIFFERENZA, non sul colore del verdetto
    #    (`LEZIONI.md` §1.52).
    # ═══════════════════════════════════════════════════════════════════════
    if innestato:
        quale = "senza tasto" if a.senza_tasto else "scena sorda"
        if guasto_visto(verdetto, m):
            print("⭐ IL GUASTO INNESTATO (%s) E' STATO VISTO: la maglia e' rossa,"
                  % quale)
            print("   ⛔ la zona e' ANCORA del colore di partenza (%.0f %%) e "
                  "dentro e' cambiato solo il %.0f %% (il tetto e' %.0f %%)."
                  % (100 * m["dopo_partenza"], 100 * m["dentro"],
                     100 * CAMBIO_RESIDUO))
            print("   ⇒ questa maglia SA dare rosso, e lo da' per la ragione giusta")
            return 0
        if verdetto is None:
            print("⛔ non ho potuto giudicare: non posso dire se il guasto si "
                  "sarebbe visto.")
            print("   ⚠ E questo NON e' «il guasto non e' stato visto»: e' una "
                  "prova che non ha guardato (§4.5).")
            return 3
        if verdetto is False:
            print("⛔⛔ ROSSO, ma NON per colpa del guasto: la zona non e' rimasta "
                  "al colore di partenza,")
            print("    o dentro e' cambiato piu' del %.0f %%.  ⇒ Dire «il guasto "
                  "e' stato visto» qui" % (100 * CAMBIO_RESIDUO))
            print("    vorrebbe dire certificare la rete su un guasto del "
                  "prodotto (§1.52).")
            return 1
        print("⛔⛔ IL GUASTO INNESTATO (%s) NON E' STATO VISTO: la maglia dice "
              "VERDE." % quale)
        print("    ⇒ o il tasto non c'entra niente col pixel che cambia, o questa "
              "maglia non guarda")
        print("    nel posto giusto — e in tutt'e due i casi non ci si puo' "
              "fidare di lei.")
        return 1

    # ── il giro normale ────────────────────────────────────────────────────
    if verdetto is True:
        print("⭐ VERDE — il tasto e' arrivato FINO ALLO SCHERMO.")
        return 0
    if verdetto is False:
        print("⛔⛔ ROSSO — il tasto NON arriva allo schermo.")
        print("    La sessione c'era, la scena c'era, il tasto e' partito, ⛔ e la "
              "zona attesa non e' cambiata.")
        return 1
    print("⚠ NON GIUDICO — ⛔ e questo non e' un verde: e' un esito suo (§4.5).")
    return 3


if __name__ == "__main__":
    sys.exit(main())
