#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c2 — ⭐⭐ «UNA FINESTRA SI APRE»
===========================================================================

    python3 11-c2-una-finestra-si-apre.py --porta 8511
    python3 11-c2-una-finestra-si-apre.py --porta 8511 --applicazione-che-muore
    python3 11-c2-una-finestra-si-apre.py --porta 8511 --finestra-che-non-si-apre
    python3 11-c2-una-finestra-si-apre.py --certifica

E' la riga **C2** di `fasi/11-la-rete-di-sicurezza.md` §4.1, alla lettera:

    che cosa deve essere vero : una finestra si apre
    da dove parte             : ⛔ da zero, sessione NUOVA
    che cosa guarda           : ⛔ **IL PIXEL** — la finestra si deve VEDERE,
                                non si conta il processo
    come so che sa dare rosso : un'applicazione che muore subito ⇒ rosso.
                                ⚠ E il controllo che il conto dei processi
                                **non** basta: `[M]` diceva 1 in tutt'e due
                                i casi

---------------------------------------------------------------------------
⭐⭐ PERCHE' QUESTA MAGLIA ADESSO SI PUO' SCRIVERE — *era «bloccata» fino a ieri*
---------------------------------------------------------------------------

`fasi/11…` §4.1 la elencava fra le quattro **bloccate** dalle «sessioni che
nascono cieche»: guardano un pixel, e non c'era un pixel da guardare.

⭐ Il 27 agosto 2026 il difetto e' stato **capito**, e cambia tutto:

  1. `[R]` `src/mutter.c:697` — la sessione di cattura si avvia, ⛔ **e il
     monitor virtuale NON esiste ancora**: lo cerca `mutter_monitor_cerca()`
     *quando il flusso consegna*.  ⇒ ⭐ **il `wl_output` di una sessione
     headless nasce quando un consumatore si aggancia al flusso, mai prima.**
  2. ⇒ ⭐⭐ **Mentre un cliente e' attaccato, lo schermo c'e'.**  E' esattamente
     la condizione in cui lavora questa maglia.
  3. ⛔ Ma il monitor **muore con il figlio**, e il figlio muore col cliente ⇒
     *«il desktop ha uno schermo solo mentre qualcuno lo guarda»*.  ⚠ Non e'
     affare di C2 (e' C6), ⭐ **ma detta l'ordine delle mosse**: il cliente si
     attacca **PRIMA** di pretendere di vedere qualcosa, e resta attaccato
     fino alla fine.  ⛔ Una maglia che aprisse l'applicazione prima
     giudicherebbe un desktop che non ha ancora uno schermo, e darebbe rosso
     al prodotto per una cosa che il prodotto non ha fatto.
  4. ⚠ Dentro la scatola GNOME una sessione ha impiegato `[M]` **~97 s** a
     diventare utile, per un difetto della **scatola** (`polkit` che non
     parte, `Contenitore.gnome` §6-bis).  ⛔ Percio' **qui non ci sono tetti
     inchiodati**: sono argomenti, con un valore prudente, e ⇒ **vanno
     ritarati sul vero** (vedi «I TETTI», piu' sotto).

---------------------------------------------------------------------------
⛔⛔ IL METRO — e da dove viene, numero per numero
---------------------------------------------------------------------------

⛔ **Il conto dei processi non e' un metro**, e questa maglia lo dimostra
   invece di affermarlo.  `fasi/10…` §7.4, la riga che apre C2:

     *«E il conto dei processi diceva **1** in tutt'e due i casi — finestra o
       non finestra, lo stesso numero.»*

⇒ ⭐ Il metro e' **il pixel**: si apre un'applicazione su una pagina di un
  **colore dichiarato**, e si guarda **quanto schermo e' diventato di quel
  colore**, con una **tolleranza dichiarata** (§4.3, rilievo di Gemini
  accolto: i compositori applicano profili di colore e la catena passa per una
  codifica H.264 in 4:2:0, che sottocampiona proprio il croma).

E si guarda **PRIMA e DOPO**, non solo dopo — tre numeri, non uno:

    prima  : il **primo** fotogramma della presa — il desktop nudo.
             ⛔ Dev'essere «disegnato» per il giudice di `10-f1-testimone.py`,
             o non si giudica affatto: un desktop nero non testimonia su una
             finestra, come un desktop nero non testimonia su un browser
             (e' la stessa guardia di C8, e per la stessa ragione).
    dopo   : l'**ultimo** fotogramma della presa — il desktop con la finestra.
    margine: ⭐ `frazione_dopo - frazione_prima`.  ⛔ Senza, una finestra
             **rimasta accesa dal giro prima** darebbe verde a un'applicazione
             che non e' nemmeno partita.

⚠ **E il «prima» e' il primo fotogramma della presa, non l'istante prima di
  aprire l'applicazione** — questo va detto, perche' fra i due c'e' tutto il
  giro.  ⭐ Ed e' il motivo per cui il verdetto **non** e' *«lo schermo e'
  cambiato»* (che cambia anche per l'orologio di GNOME) ma *«il COLORE
  DICHIARATO e' comparso»*: una grandezza che non si muove da sola.

---------------------------------------------------------------------------
⛔ COME SO CHE SA DARE ROSSO — **due** guasti innestati, e sono diversi
---------------------------------------------------------------------------

  `--applicazione-che-muore`     l'applicazione parte e viene uccisa dopo
                                 `--muore-dopo` secondi.  ⇒ nessuna finestra,
                                 **e nessun processo**.
  `--finestra-che-non-si-apre`   ⭐⭐ IL CASO CHE VALE: l'applicazione parte
                                 **senza testa** (`--headless`), cioe' resta
                                 **VIVA** e non dipinge niente.  ⇒ il conto
                                 dei processi dice **≥ 1**, esattamente come
                                 nel caso sano, ⛔ **e il pixel dice NO**.
                                 ⇒ E' la dimostrazione, misurata da questa
                                 maglia e non citata da un documento, che
                                 **contare i processi non basta**.

⛔⛔ **E OGNI GUASTO INNESTATO PORTA CON SE' IL SUO CONTROLLO SANO.**
`LEZIONI.md` §1.52: *non basta il colore del verdetto — una maglia deve
distinguere «il guasto ha morso» da «era gia' rosso per conto suo»*.
⇒ Col guasto innestato questa maglia apre **DUE** inquilini:

    inquilino 1  sano      ⇒ **deve essere VERDE**
    inquilino 2  guastato  ⇒ **deve essere ROSSO**

e pretende **tutt'e tre** le cose insieme:

    · il controllo sano e' verde                         (o non si sta
      misurando il guasto, si sta misurando un rosso proprio — e' la guardia
      «ha fallito anche il PRIMO» di C8)
    · l'inquilino guastato e' rosso
    · ⭐ la frazione dell'inquilino guastato **scende sotto una QUOTA** di
      quella del sano (`QUOTA_GUASTO`, un terzo) — cioe' una differenza
      MISURABILE, non un cambio di colore del verdetto.  ⚠ Una quota e non
      una differenza in punti: §1.45, un numero assoluto e' un numero preso
      da una condizione

⚠ E ciascun guasto pretende anche **la propria firma**, o non e' quel guasto:

    `--applicazione-che-muore`    processi dopo l'uccisione = **0**
    `--finestra-che-non-si-apre`  processi = **≥ 1** (⛔ se fosse 0 staremmo
                                  provando l'altro guasto senza accorgercene)

⛔⛔ E se la firma manca, l'esito e' **3**, non un rosso: una maglia che non ha
   potuto innestare il guasto non ha ne' visto ne' mancato niente, e scrivere
   *«il guasto NON e' stato visto»* sarebbe **un'accusa a una prova che non e'
   girata**.  ⇒ E' la stessa cura che `11-gancio.sh` si e' data il 27 agosto
   2026 sul proprio `3`.

---------------------------------------------------------------------------
⛔ I TETTI — sono argomenti, e vanno RITARATI SUL VERO
---------------------------------------------------------------------------

`LEZIONI.md` §1.45: *ogni attesa ha un nome suo e un valore suo, e il valore
si giustifica con quel che si sta aspettando.*  ⛔ Qui **nessun numero e'
stato misurato da chi ha scritto questo file**: sono valori prudenti,
dichiarati, con scritto da dove vengono.

  `--attesa-palco 60`    quanto si aspetta che il compositore annunci un
                         `wl_output`.  ⇒ `[M]` (misura di C1, 27 agosto 2026,
                         **non mia**) dentro la scatola GNOME: 98,0 · 101,0 ·
                         95,5 s, massimo 101,0.  C1 ne ricava 152 s.
                         ⛔ Qui e' 200 perche' C2 deve poi ancora **aprire una
                         finestra**, e un tetto che scade in mezzo produce un
                         «non lo so» che sembra un difetto del prodotto.
                         ⭐ E QUEL RITARDO E' DELLA SCATOLA, non del prodotto:
                         quando la cura di `polkit` (`Contenitore.gnome`
                         §6-bis) e' in vigore il palco nasce in ~2 s, come
                         nelle altre tre scatole ⇒ ⛔ **allora questo tetto
                         va rimesso a ~20 s**, e il giro costa un quarto.
                         ⚠ La maglia STAMPA sempre quanto ci ha messo davvero:
                         cosi' il tetto si ritara con un numero, non con
                         un'opinione.
  `--attesa-finestra 40` quanto si da' all'applicazione per dipingere.
                         ⛔ `[?]`: il primo avvio di Firefox in una scatola
                         fredda passa i 25 s (`[M]` C8, 26 agosto 2026, dove
                         il tetto e' 120 s **per lo scatto da solo**), ⚠ ma
                         qui il profilo dell'inquilino e' gia' nato durante
                         l'attesa del palco.  ⇒ Da ritarare.
  `--muore-dopo 1.5`     quanto vive l'applicazione nel guasto «muore subito».

---------------------------------------------------------------------------
⛔ QUEL CHE QUESTA MAGLIA **NON** GUARDA — dichiarato, o qualcuno se ne fida
---------------------------------------------------------------------------

  · ⛔ **Non guarda se la finestra e' BELLA, ne' dove sta, ne' quanto e'
    grande.**  Guarda che un colore dichiarato copra una frazione dichiarata
    dello schermo.  §4.3: *nessuno sa che aspetto abbia un desktop*.
  · ⛔ **Non distingue «l'applicazione ha aperto una finestra» da «qualcosa ha
    dipinto quel colore»**.  E' il prezzo del metro povero, ed e' voluto.
  · ⚠ **Non e' cieca al programma**: oggi l'applicazione predefinita e'
    `firefox-esr`, perche' e' l'unico programma della scatola che sappia
    dipingere **un colore che decidiamo noi** (`Contenitore.gnome` §4-ter).
    ⛔ Cosi' C2 e la meta' B di C8 guardano attraverso lo **stesso programma**:
    un difetto di Firefox le farebbe rosse tutt'e due, e chi legge potrebbe
    credere a due conferme indipendenti.  ⇒ ⭐ `--applicazione` e
    `--argomenti` esistono apposta: il giorno in cui nella scatola c'e' un
    cliente Wayland minimo che dipinge un colore dichiarato (`weston-simple-shm`
    non lo fa: i suoi colori sono suoi), **C2 va spostata su quello**.
  · ⛔ **Non guarda l'input** (e' C4) ne' il riattacco (e' C6).

---------------------------------------------------------------------------
⭐ E DUE COSE CHE QUESTA MAGLIA FA APPOSTA DIVERSAMENTE DA C1
---------------------------------------------------------------------------

  1. ⛔ **Non legge il registro del PRODOTTO per sapere se lo schermo c'e'.**
     Lo chiede al **compositore**, con `wayland-info` (che sta nella ricetta
     apposta, `Contenitore.gnome` §4).  ⚠ Un banco che chiede al prodotto se
     il prodotto ha funzionato crede a quel che sta provando.
     ⭐ E c'e' una seconda ragione, piu' concreta: `[R]` la riga *«⛔ ZERO
     MONITOR»* di `src/sessione.c:345-348` **il prodotto la scrive anche
     durante una nascita che riuscira'** — perche' a quel punto il monitor non
     e' ancora comparso (`src/mutter.c:697`).  ⇒ Prenderla per una prova di
     cecita' e' un errore, e questa maglia non lo fa.
  2. ⭐ **Un giro solo, non otto.**  C1 ne fa otto perche' il guasto che
     insegue e' intermittente; C2 insegue una cosa deterministica — *si vede o
     non si vede* — e ogni giro costa una nascita di sessione.
     ⚠ `--giri` c'e' lo stesso, per chi vuole insistere.

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)
---------------------------------------------------------------------------

  0  ⭐ ho guardato: la finestra si VEDE
     (col guasto innestato: ⭐ **il guasto e' stato visto**)
  1  ho guardato: la finestra NON si vede                       ⇒ rosso
     (col guasto innestato: ⛔ il guasto NON e' stato visto, oppure il
      controllo sano era gia' rosso per conto suo)
  3  ⛔ non ho potuto guardare — il palco non e' nato, il desktop era nero
     prima ancora dell'applicazione, nessun fotogramma e' arrivato, il giudice
     non c'e'.  ⛔ E NON e' un rosso
  2  il terreno non regge, o l'uso e' sbagliato
===========================================================================
"""
import argparse
import glob
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ IL METRO, DICHIARATO QUI E STAMPATO IN OGNI ESITO — perche' «la finestra
#    si vede» e' un verdetto, e un verdetto senza il suo metro e' un'opinione.
# ═══════════════════════════════════════════════════════════════════════════

# ⭐ Il colore della pagina bersaglio.  ⛔ CIANO, e non il magenta di C8:
#    due maglie che girano nella stessa scatola devono poter distinguere la
#    PROPRIA finestra da quella rimasta accesa dall'altra.  ⚠ Non e' pignoleria:
#    C8 lascia `/tmp/mozilla` e delle finestre in giro, e un colore condiviso
#    farebbe passare per «finestra di C2» una finestra di C8.
COLORE = (0x00, 0xFF, 0xFF)

# ⛔ La tolleranza per canale.  ⚠ E' lo stesso valore di C8, e questo NON e' un
#    tetto preso in prestito (`LEZIONI.md` §1.45): governa **la stessa
#    grandezza** — lo scostamento per canale di un colore dichiarato dopo lo
#    stesso identico percorso (compositore → cattura → H.264 4:2:0 → cliente).
#    ⭐ E `--certifica` la attraversa **al bordo**, un livello sopra e uno sotto:
#      spostato di ±48 dev'essere ancora VERDE, di ±49 ROSSO.
#    ⛔⛔ MA QUESTO NON E' UNA TARATURA, e dirlo sarebbe §1.50.  Le immagini
#      della certificazione sono sintetiche e ⚠ **non hanno mai attraversato la
#      codifica in 4:2:0 ne' un profilo di colore**: si prova che il confronto
#      cade dove dice di cadere, ⛔ non che 48 basti dopo il percorso vero.
#      ⇒ Resta una `[?]`, e si tara guardando la frazione stampata dal primo
#        giro verde.
TOLLERANZA = 48

# ⛔ Quanto schermo dev'essere di quel colore perche' si dica «c'e' una finestra».
# ⚠ `[?]`, e va ritarato sul vero: 0,25 e' il valore che C8 usa per un browser a
#   schermo intero **fotografato da se'**; qui il percorso e' un altro (la stessa
#   finestra vista ATTRAVERSO il prodotto, che e' la meta' B di C8, ⛔ mai
#   misurata).  ⇒ Fra la barra di GNOME, i bordi e le decorazioni una finestra a
#   schermo intero non copre mai tutto; 0,25 e' prudente in basso apposta,
#   perche' una soglia alta si romperebbe al primo desktop con una barra piu'
#   larga — cioe' alla fase 12, che e' quel che questa fase esiste per evitare.
FRAZIONE_MINIMA = 0.25

# ⭐ Il MARGINE: quanto dev'essere cresciuta la frazione fra il primo e l'ultimo
#   fotogramma.  ⛔ Senza, una finestra **gia' aperta** (un residuo del giro
#   prima, o di un'altra maglia) darebbe verde a un'applicazione che non e'
#   nemmeno partita.  ⚠ `[?]`, prudente: 0,20 sta sotto a `FRAZIONE_MINIMA`
#   perche' un po' di quel colore potrebbe esserci gia' per caso.
MARGINE = 0.20

# ⭐ Col guasto innestato: quanto deve CROLLARE la frazione fra il controllo sano
#   e l'inquilino guastato perche' si possa dire «il guasto ha MORSO».
#   ⛔ `LEZIONI.md` §1.52: non si misura il colore del verdetto, si misura la
#      differenza.
# ⚠⚠ Ed e' una QUOTA, non una differenza in punti — e la ragione e' §1.45.
#    Una differenza assoluta (per esempio «20 punti») e' un numero preso da una
#    condizione: il giorno in cui una finestra a schermo intero coprisse il 30 %
#    invece dell'85 % (una barra piu' larga, un desktop diverso, la fase 12),
#    ⛔ il collaudo comincerebbe a dire «il guasto non ha morso» su un guasto
#    che ha morso benissimo.  ⇒ Una quota si porta dietro la sua scala.
QUOTA_GUASTO = 0.33

# ⛔ Quanti `wl_output` bastano.  Uno: la domanda e' «c'e' uno schermo?», non
#    «quanti schermi ci sono».
OUTPUT_MINIMI = 1

# `wayland-info` elenca le interfacce cosi':
#     interface: 'wl_output', version: 4, name: 42
# ⚠ Si cerca la riga intera ancorata al nome fra apici, non la parola dentro un
#   testo (`CODER.md` §3.3-bis: «wl_output» compare anche in «wl_output_manager»).
FIRMA_OUTPUT = re.compile(r"interface:\s*'wl_output'")

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ E LA FIRMA DELL'AMMISSIONE E' UNA RIGA INTERA, NON UNA PAROLA.
#
# `[R]` `01-b3-cliente.py:1615` scrive, quando va bene:  «   AMMESSO dopo 1023 ms»
#       e quando va male:  «⛔ RuntimeError: CONGEDO invece di AMMESSO: motivo …»
#                          «⛔ RuntimeError: atteso AMMESSO, arrivato …»
#       ⛔ e li stampa tutt'e tre sullo **stdout** (`01-b3-cliente.py:2560`).
#
# ⇒ ⛔ `"AMMESSO" in testo` e' **VERO IN TUTT'E TRE I CASI**: sarebbe un predicato
#   che non puo' dire «non ammesso», cioe' `LEZIONI.md` §1.44 — e proprio nel
#   caso che esiste per prendere.  ⚠ Il ramo che porta il MOTIVO accanto al
#   sintomo (§1.9) non scatterebbe mai, e un rifiuto di credenziali uscirebbe
#   come *«nessun fotogramma e' arrivato dal filo»*: un'accusa al filo.
#
# ⭐⭐ E DAL 27 AGOSTO 2026 LA REGOLA STA IN UN POSTO SOLO: `11-c1…py`, che la
#     serve a tutte e nove le maglie.  ⚠ Il difetto di famiglia (C1, C5, C6, C7,
#     C9) e' stato curato copiando **questa** riga; ⇒ tenerne qui una seconda
#     copia, ancorche' giusta, sarebbe un secondo posto da cui divergere il
#     giorno che il cliente cambia la frase (§1.47).
# ═══════════════════════════════════════════════════════════════════════════


def e_stato_ammesso(coda):
    """⭐ `True` ammesso · `False` **RESPINTO** · `None` non ha detto niente.

    ⛔⛔ E DAL 27 AGOSTO 2026 IL PREDICATO NON E' PIU' QUI: sta in C1, e ci sta
        **una volta sola** per tutte e nove le maglie (§1.47).  ⚠ Questa maglia
        e C3 ce l'avevano giusto ma in copia propria; C1, C5, C6, C7 e C9 ce
        l'avevano SBAGLIATO — cinque volte la stessa riga, cinque volte lo
        stesso difetto.  ⇒ Due copie giuste sono comunque due posti da cui
        divergere il giorno che il cliente cambia la frase.
    ⛔ `False` non e' un rosso del prodotto: un cliente respinto e' un cliente
       respinto, e chi chiama esce **3**.
    """
    return casa_di_c1().e_stato_ammesso(coda)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I GIUDICI SI IMPORTANO, NON SI RISCRIVONO — `banchi/10-f1-testimone.py`
#
# ⛔ Due giudici che possono divergere in silenzio sono peggio di uno: il giorno
#    che divergono, il rosso lo darebbe quello sbagliato.  ⇒ Qui se ne importano
#    **due**, e nessuno dei due e' scritto in questo file:
#
#      `10-f1-testimone.py`   `giudica()` — dice se un'immagine e' nera,
#                             quasi-nera, di tinta unita o disegnata.  ⭐ E'
#                             tarato sul vero (25 agosto 2026, desktop nero
#                             misurato, soglia messa in mezzo al vuoto fra i
#                             due mondi).
#      `11-c8-…py`            `frazione_del_colore()` — dice quanta parte di
#                             un'immagine e' di un colore dato, entro una
#                             tolleranza.  ⭐ E' gia' certificato (8 casi su 8,
#                             26 agosto 2026) e prende il colore e la tolleranza
#                             come ARGOMENTI: quindi si usa con i numeri di C2
#                             senza ereditare quelli di C8.
#
# ⛔ Se uno dei due manca, questa maglia esce **3**: non si ripiega su un
#    giudizio piu' povero senza dirlo.
# ═══════════════════════════════════════════════════════════════════════════
def _carica(nome_file, mestieri):
    """Carica un modulo accanto a me (o un piano sopra) e ne pretende i mestieri.

    ⚠ «un piano sopra» serve al portatile: nella scatola tutto sta in
      `/opt/remotix`, ma nel deposito `10-f1-testimone.py` sta in `banchi/` e
      questa maglia in `banchi/11-scatole/`.  ⛔ Senza, `--certifica` non
      potrebbe girare dove il documento di fase dice che deve girare.
    """
    for base in (QUI, os.path.dirname(QUI)):
        perc = os.path.join(base, nome_file)
        if not os.path.exists(perc):
            continue
        spec = importlib.util.spec_from_file_location(
            "importato_" + re.sub(r"\W", "_", nome_file), perc)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None, perc
        # ⛔ E si VERIFICA che ci sia quel che serve, invece di fidarsi del nome
        #    del file: `CODER.md` §3.9 — chiedi il pezzo per nome, e verifica
        #    che l'abbia obbedito.
        for mestiere in mestieri:
            if not callable(getattr(m, mestiere, None)):
                return None, perc
        return m, perc
    return None, ""


def giudice_del_desktop():
    return _carica("10-f1-testimone.py", ("giudica",))


def lettore_del_colore():
    return _carica("11-c8-il-secondo-apre-il-browser.py", ("frazione_del_colore",))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ C8 E' ANCHE LA CASA DELLA PROVVISTA — e da li' vengono TRE mestieri
#
# ⛔ Non se ne fa una copia qui: la regola di `/tmp/mozilla` scritta in due
#    posti e' due posti da cui divergere, ed e' precisamente l'errore che il
#    27 agosto 2026 e' costato un giro intero.  ⇒ Si importa.
#
#   · `applica_la_cura(chi)`          — le righe di `src/provisiona.sh`: una
#        `~/.cache` VERA all'inquilino che creiamo noi.  ⭐ E' questa che rende
#        la maglia immune, non uno sgombero.
#   · `sa_scrivere_nella_cache(chi)`  — E1: non si dichiara la cura, si PROVA a
#        scrivere in `~/.cache/mozilla`.
#   · `sgombra_il_posto_condiviso(b)` — toglie `/tmp/mozilla` ⛔ soltanto se e'
#        di un inquilino della base `b`, cioe' MIO.
# ═══════════════════════════════════════════════════════════════════════════
_MESTIERI_C8 = ("applica_la_cura", "sa_scrivere_nella_cache",
                "sgombra_il_posto_condiviso")
_C8 = None


def casa_di_c8():
    """⭐ Il modulo di C8, o `None`.  ⛔ Qui non si esce: chi chiama decide."""
    global _C8
    if _C8 is None:
        _C8, _ = _carica("11-c8-il-secondo-apre-il-browser.py", _MESTIERI_C8)
    return _C8


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ C1 E' LA CASA DEI DUE PASSI COMUNI A TUTTE E NOVE LE MAGLIE — §1.47
#
# ⛔ Non e' comodita': e' che una riga ripetuta in nove file e' **nove posti da
#    cui divergere**, ed erano gia' divergiti.  Da `11-c1-nasce-e-si-vede.py`
#    vengono:
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


def casa_di_c1():
    global _C1
    if _C1 is None:
        _C1, _perc = _carica("11-c1-nasce-e-si-vede.py", _MESTIERI_C1)
    if _C1 is None:
        print("⛔ non trovo `11-c1-nasce-e-si-vede.py` accanto a me, e da li'")
        print("   vengono il predicato dell'ammissione e la garanzia dei")
        print("   gruppi della scheda — che stanno in un posto solo (§1.47).")
        print("⇒ non ho potuto guardare — ⛔ e NON e' un rosso (§4.5).")
        sys.exit(3)
    return _C1


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
# ⭐⭐ IL GIUDIZIO — e sta in una funzione PURA, cosi' `--certifica` puo'
#    farlo girare su immagini finte senza accendere niente.
# ═══════════════════════════════════════════════════════════════════════════
def giudica_il_giro(primo, ultimo, giudica, frazione, processi,
                    frazione_minima=FRAZIONE_MINIMA, margine=MARGINE):
    """Dati il PRIMO e l'ULTIMO fotogramma della presa, dice se la finestra si vede.

    `giudica`  = `10-f1-testimone.py:giudica`  (nero / quasi-nero / disegnato)
    `frazione` = una funzione (percorso) -> frazione del colore, oppure `None`
    `processi` = quanti processi dell'applicazione erano vivi.  ⛔⛔ **NON entra
                 nel verdetto**: viene riportato e basta.  E' precisamente la
                 grandezza che `fasi/10…` §7.4 ha misurato uguale (1) nei due
                 casi opposti, ⇒ farla decidere qui vorrebbe dire rifare
                 l'errore che questa maglia esiste per non ripetere.

    Torna un dizionario con `stato` fra:
        "vista"     ⭐ la finestra si vede            ⇒ verde
        "non-vista"    la finestra NON si vede       ⇒ rosso
        "non-lo-so" ⛔ non ho potuto guardare         ⇒ ne' verde ne' rosso
    """
    esito = {"stato": "non-lo-so", "perche": "", "frazione_prima": None,
             "frazione_dopo": None, "desktop_prima": None, "processi": processi}

    g = giudica(primo) if primo else None
    if g is None:
        esito["perche"] = ("il PRIMO fotogramma non si e' lasciato guardare "
                           "(non c'e', e' vuoto, o non e' un'immagine)")
        return esito
    esito["desktop_prima"] = g["verdetto"]
    # ⛔ La guardia che vale piu' di tutte, ed e' la stessa di C8: **un desktop
    #    nero non testimonia su una finestra.**  Chiamare «rosso di C2» uno
    #    schermo che era nero prima ancora che l'applicazione esistesse vorrebbe
    #    dire dare la colpa all'applicazione di una cosa successa prima di lei.
    if g["verdetto"] in ("nero", "quasi-nero"):
        esito["perche"] = ("il desktop era «%s» PRIMA dell'applicazione: la "
                           "sessione non aveva niente da mostrare, e questo non "
                           "e' un giudizio su C2" % g["verdetto"])
        return esito

    fp = frazione(primo)
    fd = frazione(ultimo) if ultimo else None
    esito["frazione_prima"], esito["frazione_dopo"] = fp, fd
    if fp is None or fd is None:
        esito["perche"] = ("non ho potuto leggere %s fotogramma"
                           % ("il PRIMO" if fp is None else "l'ULTIMO"))
        return esito

    if fd < frazione_minima:
        esito["stato"] = "non-vista"
        esito["perche"] = ("il colore dichiarato copre il %.1f%% dello schermo, "
                           "sotto il %.0f%% preteso" % (fd * 100, frazione_minima * 100))
        return esito
    if fd - fp < margine:
        # ⭐ Il caso che il margine esiste per prendere: il colore c'era GIA'.
        esito["stato"] = "non-vista"
        esito["perche"] = ("il colore copre il %.1f%%, ⛔ ma ne copriva gia' il "
                           "%.1f%% PRIMA: cresciuto di %.1f punti, sotto i %.0f "
                           "pretesi ⇒ questa finestra non l'ha aperta la mia "
                           "applicazione" % (fd * 100, fp * 100, (fd - fp) * 100,
                                             margine * 100))
        return esito
    esito["stato"] = "vista"
    esito["perche"] = ("il colore dichiarato copre il %.1f%% dello schermo "
                       "(ne copriva il %.1f%% prima: +%.1f punti)"
                       % (fd * 100, fp * 100, (fd - fp) * 100))
    return esito


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LA CERTIFICAZIONE — si dimostra che il giudice sa dare VERDE, ROSSO e
#    «NON LO SO», e che le soglie sono attraversate nei DUE versi.
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⚠ E si dichiara che cosa copre e che cosa no.

    COPRE tre cose, e la terza e' quella che si dimentica:
      1. **il giudice** — il colore ritrovato quando c'e' e non quando non c'e';
         una finestra gia' aperta che non passa per una nuova; un desktop nero
         PRIMA che da' «non lo so» e non rosso; ⭐ e le tre soglie attraversate
         **al bordo**, un livello sopra e uno sotto;
      2. ⭐ che **il conto dei processi non decida niente** — nei due versi:
         conti uguali con verdetti opposti, e conti diversissimi con lo stesso
         verdetto;
      3. ⭐⭐⭐ **il GIUNTO**: il codice d'uscita col guasto innestato, che e'
         **invertito** e da cui C13 ricava se la rete sa ancora dare rosso.
         ⛔ E' il pezzo che `LEZIONI.md` §1.52 e' nata per, e che nessuna delle
         due certificazioni di allora copriva.
    ⛔ NON COPRE, e va detto perche' e' la meta' che conta:
      · che l'applicazione parta davvero dentro la sessione, ne' che il palco
        nasca — quello lo dicono i guasti innestati **sul vero**;
      · ⚠⚠ **che `TOLLERANZA = 48` sia il numero giusto DOPO IL PERCORSO VERO.**
        Qui le immagini sono sintetiche e non hanno mai attraversato ne' la
        codifica H.264 in 4:2:0 ne' un profilo di colore.  ⇒ Questa
        certificazione prova che il confronto **cade dove dice di cadere**, non
        che 48 basti.  ⛔ Quello si tara sul vero, e finche' non e' fatto la
        tolleranza resta una `[?]`.
    """
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        print("⛔ mancano numpy o Pillow: non posso nemmeno certificarmi")
        print("   ⇒ non ho potuto guardare")
        return 3
    import tempfile

    giudice, dove_g = giudice_del_desktop()
    lettore, dove_l = lettore_del_colore()
    if giudice is None:
        print("⛔ non trovo (o non regge) il giudice delle immagini "
              "10-f1-testimone.py%s" % (" in %s" % dove_g if dove_g else ""))
        print("   ⇒ non ho potuto guardare")
        return 3
    if lettore is None:
        print("⛔ non trovo (o non regge) il lettore del colore di C8%s"
              % (" in %s" % dove_l if dove_l else ""))
        print("   ⇒ non ho potuto guardare")
        return 3

    def frazione(p):
        return lettore.frazione_del_colore(p, COLORE, TOLLERANZA)

    lav = tempfile.mkdtemp(prefix="c2cert-")

    def dipingi_righe(nome, fondo, finestra, righe, disegno=True):
        """⭐ La finestra si dipinge per RIGHE ESATTE, non per quota.

        ⛔ Serve ad attraversare le soglie **al bordo**: con una quota tonda si
           prova solo il verso del confronto, non il punto in cui cade — e un
           numero che si puo' cambiare di venti punti senza che la
           certificazione se ne accorga non e' tarato, e' solo scritto
           (`LEZIONI.md` §1.50).
        """
        a = np.zeros((216, 384, 3), dtype="uint8")
        a[:, :] = fondo
        if disegno:
            a[::7, ::5] = (210, 214, 220)
            a[0:12, :] = (30, 32, 36)
        if righe > 0:
            a[216 - righe:, :] = finestra
        p = os.path.join(lav, nome + ".png")
        Image.fromarray(a).save(p)
        return p

    def dipingi(nome, fondo, finestra=None, quota=1.0, disegno=True):
        """Un desktop finto: un fondo, un po' di roba sopra, e forse una finestra.

        ⚠ `disegno=True` mette del rumore ordinato sopra il fondo — serve
          perche' il giudice di 10-f1 dichiara «tinta unita» uno schermo di un
          colore solo, e un desktop vero non lo e' mai.
        """
        a = np.zeros((216, 384, 3), dtype="uint8")
        a[:, :] = fondo
        if disegno:
            a[::7, ::5] = (210, 214, 220)
            a[0:12, :] = (30, 32, 36)          # la barra in alto
        if finestra is not None and quota > 0:
            righe = max(1, int(216 * quota))
            a[216 - righe:, :] = finestra
        p = os.path.join(lav, nome + ".png")
        Image.fromarray(a).save(p)
        return p

    FONDO = (58, 62, 70)
    nudo = dipingi("nudo", FONDO)
    nero = dipingi("nero", (0, 0, 0), disegno=False)
    # ⭐ «quasi-nero»: nero con la barra di GNOME accesa — e' il caso vero
    #   misurato da 10-f1 il 25 agosto 2026, non un'invenzione: `[M]` desktop col
    #   fondo a `#000000`, la barra in alto porta l'orologio e le icone ⇒ accesi
    #   **0,00121** (appena sopra la soglia del nero) e media **0,28** (sotto la
    #   soglia del quasi-nero).  ⛔ I pochi pixel accesi qui sotto sono tarati per
    #   riprodurre quei due numeri, non messi a occhio: con troppa roba accesa
    #   l'immagine diventa «disegnata» e il caso non proverebbe piu' niente.
    quasinero = dipingi("quasinero", (0, 0, 0), disegno=False)
    _q = np.asarray(Image.open(quasinero).convert("RGB")).copy()
    _q[0:5, ::20] = (200, 200, 200)
    Image.fromarray(_q).save(quasinero)

    spostato = tuple(min(255, max(0, c + s))
                     for c, s in zip(COLORE, (+30, -30, -30)))
    troppo = tuple(min(255, max(0, c + s))
                   for c, s in zip(COLORE, (+120, -120, -120)))

    # (nome, primo, ultimo, processi, stato atteso)
    casi = [
        ("la finestra si apre",
         nudo, dipingi("piena", FONDO, COLORE, 0.85), 1, "vista"),
        ("nessuna finestra: lo schermo e' quello di prima",
         nudo, dipingi("uguale", FONDO), 0, "non-vista"),
        # ⭐⭐ IL CASO CHE VALE PIU' DI TUTTI, ed e' la riga di §4.1:
        #    stesso conto dei processi, verdetti opposti.
        ("⭐ processo VIVO e nessuna finestra (il caso di fasi/10 §7.4)",
         nudo, dipingi("viva-cieca", FONDO), 1, "non-vista"),
        ("⭐ colore SPOSTATO di %s: dev'essere VERDE" % (spostato,),
         nudo, dipingi("spostata", FONDO, spostato, 0.85), 1, "vista"),
        ("colore spostato TROPPO %s: dev'essere ROSSO" % (troppo,),
         nudo, dipingi("troppo", FONDO, troppo, 0.85), 1, "non-vista"),
        ("una macchia piccola non e' una finestra",
         nudo, dipingi("macchia", FONDO, COLORE, 0.05), 1, "non-vista"),
        # ⛔ Il caso del MARGINE: la finestra c'era gia' prima.
        ("⛔ la finestra c'era GIA' prima (residuo di un altro giro)",
         dipingi("gia-aperta", FONDO, COLORE, 0.85),
         dipingi("ancora-aperta", FONDO, COLORE, 0.87), 1, "non-vista"),
        # ⛔ E i due «non lo so», che NON sono rossi.
        ("⛔ il desktop era NERO prima ⇒ non lo so",
         nero, dipingi("dopo-nero", FONDO, COLORE, 0.85), 1, "non-lo-so"),
        ("⛔ il desktop era QUASI-NERO prima ⇒ non lo so",
         quasinero, dipingi("dopo-qn", FONDO, COLORE, 0.85), 1, "non-lo-so"),
        ("⛔ il primo fotogramma non c'e' ⇒ non lo so",
         os.path.join(lav, "manca.png"),
         dipingi("dopo-manca", FONDO, COLORE, 0.85), 1, "non-lo-so"),
    ]
    # un file vuoto: «non ho guardato», non «era nero»
    vuoto = os.path.join(lav, "vuoto.png")
    open(vuoto, "wb").close()
    casi.append(("⛔ il primo fotogramma e' vuoto ⇒ non lo so",
                 vuoto, dipingi("dopo-vuoto", FONDO, COLORE, 0.85), 1, "non-lo-so"))
    casi.append(("⛔ l'ultimo fotogramma non c'e' ⇒ non lo so",
                 nudo, os.path.join(lav, "manca2.png"), 1, "non-lo-so"))

    print("== certificazione del giudice di C2 ==")
    print("   giudice del desktop : %s" % dove_g)
    print("   lettore del colore  : %s" % dove_l)
    print("   colore %s · tolleranza ±%d per canale · almeno il %.0f%% dello "
          "schermo · margine %.0f punti"
          % (COLORE, TOLLERANZA, FRAZIONE_MINIMA * 100, MARGINE * 100))
    print()
    guai = 0
    for nome, primo, ultimo, proc, atteso in casi:
        e = giudica_il_giro(primo, ultimo, giudice.giudica, frazione, proc)
        ok = e["stato"] == atteso
        guai += 0 if ok else 1
        print("  %s  %-56s  processi=%s  ⇒ %-10s (atteso %s)"
              % ("OK " if ok else "NO ", nome, proc, e["stato"], atteso))
        if not ok:
            print("        ⛔ ha detto: %s" % e["perche"])

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ E LA DIMOSTRAZIONE ESPLICITA, con un numero invece che con una frase:
    #    **due giri con LO STESSO conto dei processi e verdetti OPPOSTI.**
    # ⛔ Senza questo, «il conto dei processi non basta» resterebbe una citazione
    #    di un documento; con questo e' un fatto che la maglia produce da se'.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    a = giudica_il_giro(nudo, dipingi("dim-si", FONDO, COLORE, 0.85),
                        giudice.giudica, frazione, 1)
    b = giudica_il_giro(nudo, dipingi("dim-no", FONDO),
                        giudice.giudica, frazione, 1)
    dimostrato = (a["stato"] == "vista" and b["stato"] == "non-vista"
                  and a["processi"] == b["processi"] == 1)
    guai += 0 if dimostrato else 1
    print("  %s  ⭐ IL CONTO DEI PROCESSI NON BASTA: processi 1 e 1, "
          "verdetti «%s» e «%s»"
          % ("OK " if dimostrato else "NO ", a["stato"], b["stato"]))

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐ E LA LETTURA DEL COMPOSITORE: `wayland-info` dice o non dice che c'e'
    #   uno schermo.  ⛔ Un «non lo so» e uno «zero schermi» non sono la stessa
    #   cosa (`LEZIONI.md` §1.47), e qui si certifica che non si somigliano.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    letture = [
        ("due schermi annunciati",
         "interface: 'wl_compositor', version: 6, name: 1\n"
         "interface: 'wl_output', version: 4, name: 42\n"
         "interface: 'wl_output', version: 4, name: 43\n", 2),
        ("uno schermo annunciato",
         "interface: 'wl_output', version: 4, name: 42\n", 1),
        ("⛔ nessuno schermo: il compositore c'e' e non ha uscite",
         "interface: 'wl_compositor', version: 6, name: 1\n"
         "interface: 'wl_seat', version: 9, name: 5\n", 0),
        ("⚠ un nome che CONTIENE wl_output non e' wl_output",
         "interface: 'zwlr_wl_output_manager_v1', version: 1, name: 7\n", 0),
    ]
    for nome, testo, atteso in letture:
        n = quanti_schermi(testo)
        ok = n == atteso
        guai += 0 if ok else 1
        print("  %s  %-56s  schermi=%s (atteso %s)"
              % ("OK " if ok else "NO ", nome, n, atteso))
    n = quanti_schermi(None)
    ok = n is None
    guai += 0 if ok else 1
    print("  %s  %-56s  schermi=%s (atteso «non lo so»)"
          % ("OK " if ok else "NO ", "⛔ wayland-info non ha parlato ⇒ non lo so",
             "non lo so" if n is None else n))

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ «IL CLIENTE E' STATO AMMESSO?» — e la parola dentro un testo NON basta.
    #
    # ⛔ `[R]` `01-b3-cliente.py` scrive «AMMESSO» in tutt'e tre i casi: quando
    #    e' stato ammesso, quando ha ricevuto un CONGEDO al posto dell'AMMESSO,
    #    e quando ne aspettava uno e ne e' arrivato un altro.  ⇒ `"AMMESSO" in
    #    testo` sarebbe **vero anche sui due rifiuti**, cioe' un predicato che
    #    non puo' dire di no (`LEZIONI.md` §1.44) — proprio nei casi che il
    #    controllo esiste per prendere.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    ammissioni = [
        ("la riga vera del cliente ammesso",
         "   ← ECCOMI\n   AMMESSO dopo 1023 ms (ritardo fisso §4.4-bis)\n", True),
        ("⛔ CONGEDO invece di AMMESSO — la parola c'e' e il senso e' opposto",
         "   ⛔ RuntimeError: CONGEDO invece di AMMESSO: motivo 0x03\n", False),
        ("⛔ «atteso AMMESSO, arrivato …» — idem",
         "   ⛔ RuntimeError: atteso AMMESSO, arrivato CONGEDO\n", False),
        ("⚠ una riga che NOMINA l'ammissione senza esserlo",
         "   [reg] in attesa di AMMESSO\n", False),
        ("il cliente non e' partito affatto",
         "Traceback (most recent call last):\n  ImportError: aioquic\n", False),
    ]
    for nome, testo, atteso in ammissioni:
        got = e_stato_ammesso(testo)
        ok = got is atteso
        guai += 0 if ok else 1
        print("  %s  %-56s  ⇒ %s (atteso %s)"
              % ("OK " if ok else "NO ", nome, got, atteso))
    got = e_stato_ammesso("")
    ok = got is None
    guai += 0 if ok else 1
    print("  %s  %-56s  ⇒ %s (atteso «non lo so»)"
          % ("OK " if ok else "NO ", "⛔ il cliente non ha detto NIENTE",
             "non lo so" if got is None else got))

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ LE TRE SOGLIE, ATTRAVERSATE **AL BORDO** — e non da lontano.
    #
    # ⛔ Prima qui c'erano solo casi lontani: colore spostato di 30 contro 120,
    #    frazione 0,85 contro 0,05, margine 0,85 contro 0,02.  ⚠ Con quelli si
    #    poteva mettere `TOLLERANZA` a qualunque valore fra 31 e 119 e la
    #    certificazione restava verde: si attraversava **il verso** del
    #    confronto, non **la soglia**.  E siccome i tre numeri sono dichiarati
    #    `[?]` da ritarare, e' proprio il posto in cui la trappola morde.
    # ⇒ ⭐ Adesso ogni soglia e' provata a **un livello sopra e uno sotto**: se
    #   qualcuno la cambia di un solo passo, un caso diventa rosso.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    bordo = []
    al_limite = (min(255, COLORE[0] + TOLLERANZA), COLORE[1], COLORE[2])
    oltre = (min(255, COLORE[0] + TOLLERANZA + 1), COLORE[1], COLORE[2])
    bordo.append(("⭐ colore spostato di ESATTAMENTE ±%d ⇒ ancora VERDE" % TOLLERANZA,
                  nudo, dipingi("bordo-t1", FONDO, al_limite, 0.85), "vista"))
    bordo.append(("colore spostato di ±%d ⇒ ROSSO" % (TOLLERANZA + 1),
                  nudo, dipingi("bordo-t2", FONDO, oltre, 0.85), "non-vista"))
    # la frazione: 55/216 = 0,2546 (sopra 0,25) · 53/216 = 0,2454 (sotto)
    bordo.append(("⭐ la finestra copre il 25,5%% ⇒ VERDE (soglia %.0f%%)"
                  % (FRAZIONE_MINIMA * 100),
                  nudo, dipingi_righe("bordo-f1", FONDO, COLORE, 55), "vista"))
    bordo.append(("la finestra copre il 24,5% ⇒ ROSSO",
                  nudo, dipingi_righe("bordo-f2", FONDO, COLORE, 53), "non-vista"))
    # il margine: prima 65/216 = 0,3009 · dopo 111 ⇒ +0,2130 · dopo 106 ⇒ +0,1898
    gia_aperta = dipingi_righe("bordo-m0", FONDO, COLORE, 65)
    bordo.append(("⭐ il colore cresce di 21,3 punti ⇒ VERDE (margine %.0f)"
                  % (MARGINE * 100),
                  gia_aperta, dipingi_righe("bordo-m1", FONDO, COLORE, 111), "vista"))
    bordo.append(("il colore cresce di 19,0 punti ⇒ ROSSO",
                  gia_aperta, dipingi_righe("bordo-m2", FONDO, COLORE, 106),
                  "non-vista"))
    for nome, primo, ultimo, atteso in bordo:
        e = giudica_il_giro(primo, ultimo, giudice.giudica, frazione, 1)
        ok = e["stato"] == atteso
        guai += 0 if ok else 1
        print("  %s  %-56s  ⇒ %-10s (atteso %s)"
              % ("OK " if ok else "NO ", nome, e["stato"], atteso))
        if not ok:
            print("        ⛔ ha detto: %s" % e["perche"])

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐ E CHE IL CONTO DEI PROCESSI NON ENTRI NEL VERDETTO — provato, non detto.
    # ⛔ Sopra si dimostra che due conti uguali danno verdetti opposti; qui il
    #    rovescio, che e' la meta' che mancava: **conti diversissimi sulle
    #    stesse immagini danno lo stesso verdetto**.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    piena = dipingi("proc-si", FONDO, COLORE, 0.85)
    vuota = dipingi("proc-no", FONDO)
    for nome, ultimo, atteso in (("con la finestra", piena, "vista"),
                                 ("senza la finestra", vuota, "non-vista")):
        visti = set()
        for proc in (0, 1, 7, None):
            visti.add(giudica_il_giro(nudo, ultimo, giudice.giudica,
                                      frazione, proc)["stato"])
        ok = visti == {atteso}
        guai += 0 if ok else 1
        print("  %s  ⭐ processi 0/1/7/«non lo so» %-30s ⇒ sempre «%s»"
              % ("OK " if ok else "NO ", nome, ", ".join(sorted(visti))))

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐⭐ IL GIUNTO — il codice d'uscita col guasto innestato, nei due versi.
    #
    # ⛔ E' il pezzo che `LEZIONI.md` §1.52 e' nata per: la certificazione di C9
    #    provava il giudice, quella di C13 la lettura del registro, ⛔ e il
    #    difetto stava **in mezzo**, nel codice d'uscita, che non e' di nessuno
    #    dei due mestieri.  ⇒ Qui il codice d'uscita si prova.
    # ═══════════════════════════════════════════════════════════════════════
    print()

    def giro(stato, frazione_dopo, processi, ucciso=None, perche="(finto)"):
        return {"stato": stato, "frazione_dopo": frazione_dopo,
                "processi": processi, "ucciso": ucciso, "perche": perche}

    giunti = [
        ("cieca: sano verde + guasto rosso + processo vivo ⇒ 0 (visto)",
         "cieca", giro("vista", 0.85, 3), giro("non-vista", 0.00, 2), 0),
        ("muore: sano verde + guasto rosso + processi 0 ⇒ 0 (visto)",
         "muore", giro("vista", 0.85, 3), giro("non-vista", 0.00, 0, True), 0),
        ("⛔ il guasto NON morde: la finestra si vede lo stesso ⇒ 1",
         "cieca", giro("vista", 0.85, 3), giro("vista", 0.84, 2), 1),
        ("⛔ morde troppo poco: 0,85 ⇒ 0,40, sopra la quota ⇒ 1",
         "cieca", giro("vista", 0.85, 3), giro("non-vista", 0.40, 2), 1),
        # ⭐⭐ IL CASO CHE VALE PIU' DI TUTTI, ed e' una correzione:
        ("⭐ il CONTROLLO SANO e' rosso ⇒ 3, ⛔ NON 1 (non si accusa la rete)",
         "cieca", giro("non-vista", 0.01, 3), giro("non-vista", 0.00, 2), 3),
        ("il sano non ha potuto guardare ⇒ 3",
         "cieca", giro("non-lo-so", None, None), giro("non-vista", 0.0, 2), 3),
        ("il guastato non ha potuto guardare ⇒ 3",
         "cieca", giro("vista", 0.85, 3), giro("non-lo-so", None, None), 3),
        ("⚠ firma mancante: «muore» e il processo e' ancora vivo ⇒ 3",
         "muore", giro("vista", 0.85, 3), giro("non-vista", 0.0, 2), 3),
        ("⚠ firma mancante: «cieca» e non c'e' nessun processo ⇒ 3",
         "cieca", giro("vista", 0.85, 3), giro("non-vista", 0.0, 0), 3),
        ("⚠ firma mancante: `pkill` non ha trovato niente ⇒ 3",
         "muore", giro("vista", 0.85, 3), giro("non-vista", 0.0, 0, False), 3),
    ]
    for nome, quale, sano, rotto, atteso in giunti:
        e, _righe = collauda_il_guasto(quale, sano, rotto)
        ok = e == atteso
        guai += 0 if ok else 1
        print("  %s  %-62s  ⇒ esito %s (atteso %s)"
              % ("OK " if ok else "NO ", nome, e, atteso))

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
    guai_gr, _quanti_gr = casa_di_c1().certifica_gruppi("C2")
    guai += guai_gr

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐⭐ LA PROVVISTA CONDIVISA — ⛔ il caso che il 27 agosto 2026 non c'era,
    #    ed e' costato un giro intero letto al contrario.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    guai_pr, quanti_pr = certifica_la_provvista("C2", "c2u")
    guai += guai_pr

    print()
    if guai:
        print("⛔ il giudice di C2 NON e' affidabile: %d casi sbagliati" % guai)
        return 1
    print("⭐ il giudice vede la finestra quando c'e' e non quando non c'e', le "
          "tre soglie cadono dove dicono,")
    print("   ⭐ il conto dei processi non entra nel verdetto in nessuno dei due "
          "versi, «AMMESSO» e' una riga e non una parola,")
    print("   ⭐⭐ e il GIUNTO — il codice d'uscita col guasto innestato — dice 0, "
          "1 e 3 dove deve (LEZIONI.md §1.52)")
    print("   ⭐ e i GRUPPI DELLA SCHEDA: un inquilino che non vede fa dire "
          "«non ho potuto guardare», ⛔ mai rosso")
    # ⛔ E la riga della provvista si stampa SOLO se i casi veri sono girati:
    #    dire «coperta» dopo averli saltati sarebbe la §1.50 in una riga.
    if quanti_pr >= 4:
        print("   ⭐⭐ e LA PROVVISTA: un /tmp/mozilla di un'altra maglia non lo "
              "tocco, e il mio inquilino scrive lo stesso — ⛔ mai rosso")
    else:
        print("   ⚠ e LA PROVVISTA e' coperta SOLO a meta': i casi veri "
              "chiedono l'amministratore, e qui non li ho girati")
    print("⚠ e questa certificazione copre I GIUDICI E IL GIUNTO, ⛔ non "
          "l'apertura vera della finestra ne' che ±%d basti dopo la codifica "
          "(vedi in testa)" % TOLLERANZA)
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# IL TERRENO E LE MOSSE
# ═══════════════════════════════════════════════════════════════════════════
def sh(comando, secondi=120):
    try:
        return subprocess.run(["/bin/sh", "-c", comando],
                              capture_output=True, text=True, timeout=secondi)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(comando, 124, "", "scaduto")


def quanti_schermi(testo):
    """Quanti `wl_output` annuncia il compositore.  ⛔ `None` = non lo so.

    ⚠ `None` e `0` sono due cose diverse e non devono somigliarsi: *«non ho
      potuto chiedere»* e *«ho chiesto e non ce n'e' nessuno»* portano a due
      esiti opposti (3 contro un'attesa che continua).  `LEZIONI.md` §1.47.
    """
    if testo is None:
        return None
    return len(FIRMA_OUTPUT.findall(testo))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ LA PROVVISTA CONDIVISA — `/tmp/mozilla`, e perche' la cura sta QUI
#
# `[M]` 27 agosto 2026, giro `--famiglia tutto` su tutt'e quattro le scatole,
#   binario `aa950804fed7`: C2 ⛔ 1 («il colore copre lo 0,0% dello schermo»),
#   C3 ⛔ 3, C4 ⛔ 3.  ⚠ E l'immagine giudicata diceva tutt'altro: la sessione
#   GNOME era **viva e dipinta** — pannello, dock, sfondo, Firefox acceso — ⛔ ma
#   Firefox stava fermo sulla **finestra di scelta del profilo**.
#
# ⇒ LA CAUSA, letta dentro la scatola:
#     /home/c2u1/.cache/mozilla -> /tmp/mozilla   (lo scheletro della macchina
#                                                  vera, che C8 riproduce e
#                                                  ⛔ NON disfa)
#     /tmp/mozilla        di «c8u1», modo 0700
#   cioe' il posto condiviso era rimasto al PRIMO inquilino che l'aveva preso —
#   quello di C8/C8b, che in `famiglia tutto` gira PRIMA di me.  ⛔ Nessuno dei
#   due banchi sbaglia da solo: e' l'ORDINE a romperli.
#
# ⛔⛔ E LA CURA NON PUO' STARE IN CHI MI ACCENDE.  Per un giorno e' stata in
#     `11-accendi.sh`; ⚠ ma una maglia che ha bisogno di essere «preparata da
#     fuori» e', lanciata a mano o da un altro gancio, una maglia che da' un
#     **rosso falso** — ed e' il difetto che in questa rete si paga di piu'.
#
# ⭐⭐ E NON E' UNO SGOMBERO.  `src/provisiona.sh` ha gia' detto la regola —
#     *«non si tocca `/tmp/mozilla` di chi ce l'ha gia': non e' nostro e non si
#     sa chi lo usa»* — e ⛔ vale anche fra maglie: in parallelo (C14) l'altra
#     maglia ci sta DENTRO, e cancellarglielo la farebbe cadere.  ⇒ La cura e'
#     la stessa del prodotto: **una `~/.cache` vera all'inquilino che creo io**.
#     Con quella, di chi sia `/tmp/mozilla` non m'importa piu': non lo guardo.
#
# ⚠ Resta un solo sgombero legittimo, e riguarda soltanto ME: il `/tmp/mozilla`
#   che un MIO inquilino di un giro precedente ha lasciato li'.  ⛔ Quello lo
#   toglie `sgombra_il_posto_condiviso()` di C8, importata, e ⛔ non tocca
#   nient'altro.
#
# ⛔ E se la cura non regge NON si da' rosso: si esce **3** dicendo perche'
#   (`crea` torna `(False, perche)`), perche' un browser fermo sulla scelta del
#   profilo e' un difetto del BANCO e non del prodotto.
# ═══════════════════════════════════════════════════════════════════════════
IL_POSTO_CONDIVISO = "/tmp/mozilla"


def padrone_del_posto_condiviso():
    """Di chi e' `/tmp/mozilla` — `""` se non c'e'.  Serve solo a DIRLO."""
    return sh("stat -c %%U %s 2>/dev/null" % IL_POSTO_CONDIVISO).stdout.strip()


def sgombra_il_mio_rimasuglio(mio_base):
    """Toglie `/tmp/mozilla` ⛔ soltanto se e' rimasto a un inquilino MIO.

    ⛔ La regola non si riscrive: e' `sgombra_il_posto_condiviso()` di C8,
       importata — *«si toglie solo quel che e' di un inquilino di QUESTA
       prova»*.  ⇒ Se e' di un'altra maglia, o di un estraneo, quella funzione
       dice «NON lo tocco» e non tocca niente, che e' quel che voglio.
    ⚠ Torna una riga da stampare, o `None` se non c'e' niente da dire.
    """
    c8 = casa_di_c8()
    if c8 is None:
        return "⚠ non trovo C8: non ho nemmeno guardato %s" % IL_POSTO_CONDIVISO
    return c8.sgombra_il_posto_condiviso(mio_base)


def cura_della_provvista(chi):
    """⭐⭐ (fatto, perche') — la cura di `src/provisiona.sh`, e la sua PROVA.

    ⛔ E1: non basta applicarla, si prova a scrivere davvero in
       `~/.cache/mozilla` — che col collegamento a `/tmp` e' il posto che morde.
       ⚠ Scrivere in `~/.cache` non proverebbe niente: col collegamento e'
       `/tmp`, che e' scrivibile da chiunque (modo 1777).
    """
    c8 = casa_di_c8()
    if c8 is None:
        return False, ("non trovo `11-c8-il-secondo-apre-il-browser.py` accanto "
                       "a me: da li' viene la cura di `src/provisiona.sh`, e "
                       "⛔ non se ne fa una copia qui (§1.47)")
    c8.applica_la_cura(chi)
    if c8.sa_scrivere_nella_cache(chi):
        return True, ""
    padrone = padrone_del_posto_condiviso()
    return False, ("«%s» non riesce a scrivere in ~/.cache/mozilla (%s e' di "
                   "«%s»): Firefox resterebbe sulla scelta del profilo e questa "
                   "maglia misurerebbe il BANCO, non il prodotto"
                   % (chi, IL_POSTO_CONDIVISO, padrone or "nessuno"))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ LA CERTIFICAZIONE DELLA PROVVISTA — e sta in UN POSTO SOLO (§1.47)
#
# ⚠ Sta qui, in C2, e non in C8, perche' C8 non e' mia da modificare oggi.  ⭐ Il
#   giorno che lo sara', questa funzione va con `applica_la_cura`, che e' il
#   pezzo che certifica.  C3 e C4 la chiamano da qui, ⛔ non se ne fanno una
#   copia — tre copie sono tre posti da cui divergere, ed e' esattamente
#   l'errore che questa cura e' nata per riparare.
#
# ⛔⛔ E NON ISPEZIONA NIENTE (E1): fa un `/tmp/mozilla` di un altro inquilino,
#     con un inquilino vero e lo scheletro vero, e poi GUARDA che cosa succede.
# ═══════════════════════════════════════════════════════════════════════════
def certifica_la_provvista(nome_maglia, mia_base):
    """⭐ Torna `(guai, quanti_casi_provati)`.

    I casi, e sono tre:
      1. ⛔ la cura NON puo' riuscire ⇒ `(False, perche')`, cioe' la maglia si
         ferma dicendo perche' (esito **3**) — ⛔ e MAI un rosso;
      2. ⛔ `/tmp/mozilla` e' di un inquilino di UN'ALTRA maglia ⇒ non lo tocco,
         ⭐ e il mio inquilino scrive lo stesso in `~/.cache/mozilla`;
      3. ⭐ `/tmp/mozilla` e' di un inquilino MIO, rimasto dal giro prima ⇒ lo
         sgombro.
    ⚠ Il 2 e il 3 chiedono l'amministratore.  ⛔ Senza, si DICE che non sono
      stati provati: una certificazione che tace la meta' che conta e' peggio di
      una che manca.
    """
    guai = 0
    quanti = 0
    print("  ── la provvista condivisa di %s (%s) ──"
          % (nome_maglia, IL_POSTO_CONDIVISO))
    if casa_di_c8() is None:
        print("  NO   ⛔ non trovo C8: la cura di src/provisiona.sh non e' "
              "importabile, e ⛔ non se ne fa una copia")
        return 1, 1

    # ── 1 · e non serve nessun permesso ────────────────────────────────────
    quanti += 1
    fatto, perche = cura_della_provvista("non-esiste-%s-x" % mia_base)
    ok = (fatto is False) and bool(perche)
    guai += 0 if ok else 1
    print("  %s  ⛔ la cura non puo' riuscire ⇒ si ferma DICENDO PERCHE' "
          "(esito 3), ⛔ mai un rosso" % ("OK " if ok else "NO "))
    if not ok:
        print("        ⛔ ha detto: (%s, %r)" % (fatto, perche))

    # ── 2 e 3 · i casi VERI ────────────────────────────────────────────────
    if os.geteuid() != 0:
        print("  ⚠   i due casi VERI chiedono l'amministratore: ⛔ NON li ho "
              "provati, e cosi' questa certificazione non copre la cura")
        return guai, quanti
    if os.path.exists(IL_POSTO_CONDIVISO):
        print("  ⚠   %s c'e' gia' ed e' di «%s»: ⛔ non lo tocco per farci una "
              "prova — i due casi VERI NON li ho provati"
              % (IL_POSTO_CONDIVISO, padrone_del_posto_condiviso()))
        return guai, quanti

    estraneo = "c99u9"          # un inquilino della rete, ⛔ ma di un'altra maglia
    mio = "%s9" % mia_base

    def scheletro_della_macchina_vera(chi):
        """`~/.cache` come collegamento a `/tmp`, ⛔ solo su questo inquilino.

        ⚠ Non si tocca `/etc/skel`: qui il terreno si riproduce a mano, su due
          utenti che nascono e muoiono dentro questa funzione.
        """
        sh("rm -rf /home/%s/.cache && ln -s /tmp /home/%s/.cache && "
           "chown -h %s:%s /home/%s/.cache" % (chi, chi, chi, chi, chi))

    def il_posto_e_di(chi):
        sh("rm -rf %s && mkdir -p %s/firefox && chown -R %s:%s %s && "
           "chmod 700 %s"
           % (IL_POSTO_CONDIVISO, IL_POSTO_CONDIVISO, chi, chi,
              IL_POSTO_CONDIVISO, IL_POSTO_CONDIVISO))

    def via(chi):
        # ⛔ Il collegamento si toglie PRIMA di `userdel -r`: e' un puntamento a
        #    `/tmp`, e non gli si da' occasione di seguirlo.
        sh("rm -f /home/%s/.cache; userdel -r %s 2>/dev/null; rm -rf /home/%s"
           % (chi, chi, chi))

    try:
        via(estraneo)
        via(mio)
        for chi in (estraneo, mio):
            r = sh("useradd -m -s /bin/bash %s" % chi)
            if r.returncode != 0:
                print("  ⚠   non sono riuscito a creare «%s»: %s ⇒ ⛔ i due "
                      "casi VERI NON li ho provati"
                      % (chi, (r.stderr or "").strip()[:80]))
                return guai, quanti
            scheletro_della_macchina_vera(chi)

        # ── 2 · il posto e' di un'ALTRA maglia ─────────────────────────────
        il_posto_e_di(estraneo)
        detto = sgombra_il_mio_rimasuglio(mia_base)
        quanti += 1
        ok = padrone_del_posto_condiviso() == estraneo
        guai += 0 if ok else 1
        print("  %s  ⛔ %s e' di «%s» (un'altra maglia) ⇒ NON lo tocco"
              % ("OK " if ok else "NO ", IL_POSTO_CONDIVISO, estraneo))
        if detto:
            print("        dice: %s" % detto)

        # ⭐ …e la cura mi rende immune LO STESSO: e' questo il caso che
        #   dimostra che il rosso del 27 agosto non tornerebbe.
        quanti += 1
        fatto, perche = cura_della_provvista(mio)
        ancora = padrone_del_posto_condiviso() == estraneo
        ok = bool(fatto) and ancora
        guai += 0 if ok else 1
        print("  %s  ⭐ e «%s» scrive lo stesso in ~/.cache/mozilla, con %s "
              "ancora di «%s»" % ("OK " if ok else "NO ", mio,
                                  IL_POSTO_CONDIVISO, estraneo))
        if not ok:
            print("        ⛔ ha detto: (%s, %s) · adesso e' di «%s»"
                  % (fatto, perche, padrone_del_posto_condiviso()))

        # ── 3 · il posto e' MIO, rimasto dal giro prima ────────────────────
        scheletro_della_macchina_vera(mio)      # la cura gli aveva dato la sua
        il_posto_e_di(mio)
        detto = sgombra_il_mio_rimasuglio(mia_base)
        quanti += 1
        ok = not os.path.exists(IL_POSTO_CONDIVISO)
        guai += 0 if ok else 1
        print("  %s  ⭐ %s e' di «%s» (MIO, dal giro prima) ⇒ lo sgombro"
              % ("OK " if ok else "NO ", IL_POSTO_CONDIVISO, mio))
        if detto:
            print("        dice: %s" % detto)
    finally:
        # ⛔ Si toglie SOLO quel che ha fatto questa funzione.
        sh("rm -rf %s" % IL_POSTO_CONDIVISO)
        via(estraneo)
        via(mio)
    return guai, quanti


def crea(chi, parola):
    """Crea l'inquilino **da zero**, e ⛔ lo cancella PRIMA di crearlo.

    ⚠ `[M]` (C1, 26 agosto 2026): un `id -u X || useradd X` rende l'utente nuovo
      **soltanto la prima volta che il banco gira in vita sua**.  ⇒ «da zero»
      comprende anche «da zero rispetto a me stesso di ieri».
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


def sgombra(chi, attesa):
    """⛔ Si aspetta che se ne sia andato DAVVERO, non mezzo secondo a orologio.

    `[M]` (C1, 26 agosto 2026): senza questa attesa i giri si alternavano
    «non lo so» / giudizio, perche' il giro dopo partiva mentre il precedente
    stava ancora morendo.
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


def il_socket_di(chi):
    """Dove parla il compositore di questo inquilino.  ⛔ Si CERCA, non si indovina.

    ⚠ Inchiodare `wayland-0` vorrebbe dire una maglia che funziona su un desktop
      e tace sugli altri — cioe' esattamente il difetto che questa fase esiste
      per non introdurre (§3.7).
    """
    uid = sh("id -u %s" % chi).stdout.strip()
    if not uid:
        return None, None
    rtd = "/run/user/%s" % uid
    soc = sh("ls %s 2>/dev/null | grep -E '^wayland-[0-9]+$' | head -1" % rtd)
    d = soc.stdout.strip()
    return (rtd, d) if d else (rtd, None)


def chiedi_al_compositore(chi):
    """⭐ Si chiede al COMPOSITORE se c'e' uno schermo, non al prodotto.

    ⛔ Un banco che chiede al prodotto se il prodotto ha funzionato crede a quel
       che sta provando.  ⚠ E c'e' una ragione concreta in piu': `[R]` la riga
       *«⛔ ZERO MONITOR»* di `src/sessione.c:345-348` il prodotto la scrive
       **anche durante una nascita che riuscira'**, perche' a quel punto il
       monitor non e' ancora comparso (`src/mutter.c:697`).

    Torna (quanti_schermi | None, motivo).
    """
    rtd, display = il_socket_di(chi)
    if rtd is None:
        return None, ("non so l'uid di «%s»: non esiste, o `id` non ha "
                      "risposto" % chi)
    if display is None:
        return None, ("in %s non c'e' nessun socket wayland: il compositore "
                      "non e' (ancora) nato" % rtd)
    r = sh("runuser -u %s -- env XDG_RUNTIME_DIR=%s WAYLAND_DISPLAY=%s "
           "wayland-info" % (chi, rtd, display), secondi=60)
    if r.returncode != 0 and not r.stdout:
        return None, ("wayland-info non ha parlato: %s"
                      % ((r.stderr or "").strip().replace("\n", " ")[:90]))
    return quanti_schermi(r.stdout), ""


def accendi_l_applicazione(chi, applicazione, argomenti, pagina):
    """Accende l'applicazione DENTRO la sessione dell'inquilino.

    ⚠ `HOME` esplicito e non ereditato: il profilo del programma vive dentro
      `$HOME`, e una maglia che guardasse la home sbagliata direbbe una cosa
      per un'altra.
    ⛔ E il registro del programma finisce in un file SUO, non nella cartella di
       lavoro del banco: `[M]` (C8, 26 agosto 2026) la cartella del banco e' di
       `root` a modo 0755 e il programma gira da UTENTE ⇒ non poteva scriverci,
       e il banco leggeva il proprio difetto come un difetto del prodotto.
    """
    rtd, display = il_socket_di(chi)
    if display is None:
        return None, ("in %s non c'e' nessun socket wayland: non c'e' un "
                      "compositore a cui l'applicazione possa parlare"
                      % (rtd or "(uid ignoto)"))
    try:
        args = argomenti % {"pagina": pagina}
    except (ValueError, KeyError) as sbaglio:
        # ⛔ Un `%` letterale dentro `--argomenti` farebbe esplodere questa riga
        #    con una traccia di Python al posto di un messaggio.  ⇒ Uso sbagliato.
        return None, ("non riesco a costruire gli argomenti da «%s»: %s ⇒ nel "
                      "modello si scrive `%%(pagina)s`, e un `%%` letterale va "
                      "raddoppiato" % (argomenti, sbaglio))
    comando = (
        "runuser -u %s -- env XDG_RUNTIME_DIR=%s WAYLAND_DISPLAY=%s "
        "MOZ_ENABLE_WAYLAND=1 XDG_SESSION_TYPE=wayland HOME=/home/%s "
        "%s %s > %s 2>&1 &"
        % (chi, rtd, display, chi, applicazione, args, registro_applicazione(chi)))
    r = sh(comando, secondi=30)
    if r.returncode != 0:
        # ⛔ E il risultato NON si butta.  `LEZIONI.md` §1.46: un comando che
        #    puo' non essere eseguito affatto, e di cui nessuno guarda l'esito,
        #    e' un banco che accusa il prodotto di quel che non ha fatto lui.
        return None, ("il lancio non e' partito (esito %d): %s"
                      % (r.returncode,
                         ((r.stderr or "") + (r.stdout or "")).strip()[:120]))
    return display, ""


def registro_applicazione(chi):
    """⭐ Dove l'applicazione scrive quel che dice — e ⛔ **si legge**.

    `[M]` (C8, 26 agosto 2026) la cartella di lavoro del banco e' di `root` a
    modo 0755 e l'applicazione gira da UTENTE ⇒ non potrebbe scriverci.  Quindi
    scrive in casa sua.  ⚠ Ma un registro che nessuno legge e' peggio di
    nessun registro: da' l'impressione che qualcuno guardi.
    """
    return "/home/%s/.c2-applicazione.log" % chi


def ultima_riga_detta(chi):
    """L'ultima riga che l'applicazione ha detto, o «» se non ha detto niente."""
    r = sh("tail -n 5 %s 2>/dev/null" % registro_applicazione(chi))
    righe = [x.strip() for x in (r.stdout or "").splitlines() if x.strip()]
    return righe[-1][:160] if righe else ""


def aspetta_che_parta(chi, applicazione, attesa):
    """⛔ Si aspetta che l'applicazione ESISTA prima di pretendere una finestra.

    ⚠ Serve a due cose, e la seconda vale piu' della prima:
      1. se non parte affatto (PAM, gruppo, `$HOME` non scrivibile) l'esito e'
         **«non ho potuto guardare»**, non un rosso al prodotto;
      2. ⛔⛔ il guasto «muore subito» uccide **per nome e per utente**, e a 1,5
         secondi dal lancio la catena `runuser` → `env` → programma potrebbe non
         aver ancora fatto il cambio d'utente: il `pkill` non troverebbe niente,
         il programma partirebbe DOPO, dipingerebbe, e la maglia direbbe *«il
         guasto NON e' stato visto»* ⇒ ⛔ il gancio scriverebbe
         `ha_visto_il_guasto: false` e **C13 comincerebbe a dire che la rete non
         sa piu' dare rosso** mentre sta benissimo (`LEZIONI.md` §1.52).
      ⇒ Si uccide quel che si e' visto vivo, non quel che si spera esista.
    """
    scadenza = time.time() + attesa
    while time.time() < scadenza:
        n = quanti_processi(chi, applicazione)
        if n:
            return n, round(attesa - (scadenza - time.time()), 1)
        time.sleep(1.0)
    return 0, None


def quanti_processi(chi, applicazione):
    """Quanti processi dell'applicazione sono vivi.

    ⛔⛔ E QUESTO NUMERO NON DECIDE NIENTE.  E' la grandezza che `fasi/10…` §7.4
         ha misurato **uguale (1) nei due casi opposti**; sta qui perche' la
         maglia la RIFERISCA, e perche' col guasto «finestra che non si apre»
         serve a dire che il guasto e' quello giusto — non perche' giudichi.
    ⚠ `None` = non ho potuto contare.
    """
    # ⛔⛔ E NON SI CONTA CON `wc -l`, che ESCE SEMPRE 0 E STAMPA SEMPRE UN
    #     NUMERO: con quello «non ho potuto contare» e «zero processi»
    #     diventerebbero lo stesso `0` — `LEZIONI.md` §1.47 — e lo zero e'
    #     proprio la condizione con cui si riconosce il guasto «muore subito».
    # ⭐ `pgrep` invece li distingue da se': 0 = ne ho trovati, 1 = nessuno,
    #   ≥2 = non ho potuto cercare.
    r = sh("pgrep -u %s -f %s" % (chi, applicazione))
    if r.returncode == 1:
        return 0
    if r.returncode != 0:
        return None
    return len([x for x in (r.stdout or "").split() if x.strip()])


def i_fotogrammi_di_prima(flusso, dove, quanti, tetto):
    """I PRIMI `quanti` fotogrammi del flusso — ⛔ e non uno solo.

    ⚠ La prima stesura ne prendeva uno.  ⛔ Ma il primo fotogramma di una presa
      e' il candidato naturale a essere nero o mezzo disegnato: il palco e'
      appena nato e il desktop si sta ancora dipingendo.  ⇒ Se il giudice lo
      chiamasse «nero», questa maglia uscirebbe **3 per sempre** — cioe' il
      cugino del rosso perpetuo di `LEZIONI.md` §1.49, quello che non si puo'
      far diventare verde.
    ⭐ Con piu' fotogrammi si prende **il primo che il giudice chiama
      disegnato**, e se non lo e' nessuno si DICE quanti se ne sono guardati.
    """
    fuori = os.path.join(dove, "prima")
    if os.path.isdir(fuori):
        shutil.rmtree(fuori, ignore_errors=True)
    os.makedirs(fuori, exist_ok=True)
    r = sh("ffmpeg -hide_banner -loglevel error -i %s -vsync 0 -frames:v %d "
           "-y %s/p-%%03d.png" % (flusso, quanti, fuori), secondi=tetto)
    elenco = sorted(glob.glob(os.path.join(fuori, "p-*.png")))
    return elenco, (r.returncode == 124)


def l_ultimo_fotogramma(flusso, dove, tetto):
    """L'ULTIMO fotogramma del flusso — quel che il desktop mostra alla fine.

    ⛔ `-update 1` riscrive lo stesso file a ogni fotogramma decodificato: alla
       fine resta l'ultimo.  ⚠⚠ **E per questo il tetto qui MORDE in modo
       traditore**: se scade a meta', il file c'e' lo stesso ed e' un fotogramma
       **di mezzo** — che ha esattamente l'aspetto dell'ultimo.
    ⇒ ⛔ Percio' qui il codice d'uscita **si guarda**, e una scadenza diventa
      «non ho potuto guardare».  ⚠ E' il rovescio di `LEZIONI.md` §1.50: la'
      il codice d'uscita andava ignorato perche' il lavoro era **compiuto**
      (il PNG c'era ed era giusto); qui il lavoro e' stato **interrotto**, e il
      PNG c'e' ed e' un altro.
    """
    ultimo = os.path.join(dove, "ultimo.png")
    if os.path.exists(ultimo):
        os.unlink(ultimo)
    r = sh("ffmpeg -hide_banner -loglevel error -i %s -vsync 0 -update 1 -y %s"
           % (flusso, ultimo), secondi=tetto)
    if r.returncode == 124:
        return None, True
    if not os.path.exists(ultimo) or not os.path.getsize(ultimo):
        return None, False
    return ultimo, False


def scegli_il_prima(elenco, giudica):
    """⭐ Il primo fotogramma che il giudice chiama «disegnato».

    Torna (percorso|None, quanti_guardati, verdetti).
    """
    verdetti = []
    for p in elenco:
        g = giudica(p)
        verdetti.append("?" if g is None else g["verdetto"])
        if g is not None and g["verdetto"] not in ("nero", "quasi-nero"):
            return p, len(verdetti), verdetti
    return None, len(verdetti), verdetti


def quanti_fotogrammi(coda):
    """Quanti fotogrammi il cliente dice di aver preso dal filo.  `None` = non lo so."""
    quanti = None
    for riga in coda.splitlines():
        if "[vid]" in riga and "nessun fotogramma" not in riga:
            try:
                quanti = int(riga.split("[vid]", 1)[1].strip().split()[0])
            except Exception:
                pass
    return quanti


# ═══════════════════════════════════════════════════════════════════════════
# UN GIRO — un inquilino nuovo, una sessione nuova, una finestra
# ═══════════════════════════════════════════════════════════════════════════
def un_giro(chi, modo, a, giudice, lettore):
    """Torna un dizionario col verdetto di questo inquilino.

    `modo` = None | "muore" | "cieca"

    ⛔⛔ L'ORDINE DELLE MOSSE NON E' UN DETTAGLIO, ed e' la ragione per cui
         questa maglia oggi si puo' scrivere:

           1. si crea l'inquilino
           2. ⭐ **si attacca il cliente, e ci si RESTA** — il `wl_output` di
              una sessione headless nasce quando un consumatore si aggancia al
              flusso (`src/mutter.c:697` `[R]`) e muore col figlio
           3. si aspetta che il COMPOSITORE annunci uno schermo
           4. **solo allora** si apre l'applicazione
           5. il cliente finisce il suo tempo e scrive il flusso
           6. si giudicano il primo e l'ultimo fotogramma

        ⇒ Invertire 2 e 4 vorrebbe dire aprire una finestra su una sessione che
          non ha ancora uno schermo, ⛔ e dare la colpa all'applicazione.
    """
    esito = {"chi": chi, "modo": modo or "sano", "stato": "non-lo-so",
             "perche": "", "frazione_prima": None, "frazione_dopo": None,
             # ⚠ DUE conti, e non uno: quello all'apertura della finestra e
             #   quello alla fine.  ⛔ Il fotogramma che si giudica e' l'ultimo,
             #   e contare i processi due minuti prima vorrebbe dire accostare
             #   due grandezze prese in momenti diversi e chiamarle un
             #   confronto.  ⇒ La firma del guasto usa quello **finale**.
             "processi": None, "processi_apertura": None,
             "fotogrammi": None, "palco_s": None, "avvio_s": None,
             "schermi": None, "desktop_prima": None, "detto": "",
             "ucciso": None,
             "png_prima": None, "png_dopo": None, "guardati_prima": None}

    fatto, perche = crea(chi, a.parola)
    if not fatto:
        esito["perche"] = "non sono riuscito a creare «%s»: %s" % (chi, perche)
        return esito

    lavoro = os.path.join(a.lavoro, chi)
    os.makedirs(lavoro, exist_ok=True)
    flusso = os.path.join(lavoro, "presa.264")
    if os.path.exists(flusso):
        os.unlink(flusso)

    # ── 2. il cliente si attacca, e ci resta ────────────────────────────────
    # ⛔ Il tempo si calcola, non si inchioda: dev'essere abbastanza per la
    #    nascita del palco PIU' l'apertura della finestra PIU' una coda.  ⚠ Se
    #    il palco nasce presto si spreca l'avanzo: e' il prezzo del fatto che
    #    `--resta` si decide al lancio e non si puo' accorciare dopo.
    resta = a.attesa_palco + a.attesa_finestra + a.coda
    partito = time.time()
    # ⛔⛔ E L'USCITA DEL CLIENTE VA IN UN FILE, NON IN UNA PIPE — e non e' uno
    #     stile: e' un guasto evitato.  Questo cliente resta acceso per minuti
    #     **mentre il banco fa altro**, e con `-u` scrive senza risparmio.  Una
    #     pipe che nessuno svuota si riempie (64 KB su Linux) e ⛔ **blocca chi
    #     scrive**: il cliente si fermerebbe a meta' di una `print`, smetterebbe
    #     di tenere viva la sessione, e il banco leggerebbe «nessun fotogramma»
    #     dando la colpa al prodotto.
    # ⚠ Gli esemplari non hanno questo problema perche' usano `subprocess.run`,
    #   che svuota le pipe mentre aspetta.  Qui non si aspetta: si lavora.
    detto_file = os.path.join(lavoro, "cliente.log")
    detto_fd = open(detto_file, "w")
    cliente = subprocess.Popen(
        ["python3", "-u", a.cliente,
         "--indirizzo", a.indirizzo, "--porta", str(a.porta),
         "--utente", chi, "--parola", a.parola,
         "--video-scrivi", flusso, "--resta", str(resta)],
        stdout=detto_fd, stderr=subprocess.STDOUT, text=True)

    def chiudi_il_cliente(scadenza):
        """Aspetta che il cliente finisca, e torna quel che ha detto.

        ⛔ Torna sempre una stringa: se il file non si lascia leggere e' un
           «non ho potuto guardare», e chi chiama lo vede come «non AMMESSO».
        """
        try:
            cliente.wait(timeout=scadenza)
        except subprocess.TimeoutExpired:
            cliente.kill()
            cliente.wait()
        detto_fd.close()
        try:
            with open(detto_file, "r", errors="replace") as f:
                return f.read()
        except OSError:
            return ""

    # ── 3. si aspetta che il COMPOSITORE annunci uno schermo ────────────────
    schermi = None
    motivo = "non ho mai potuto chiedere"
    scadenza = time.time() + a.attesa_palco
    while time.time() < scadenza:
        if cliente.poll() is not None:
            motivo = "il cliente se n'e' andato prima che nascesse uno schermo"
            break
        schermi, motivo = chiedi_al_compositore(chi)
        if schermi is not None and schermi >= OUTPUT_MINIMI:
            esito["palco_s"] = round(time.time() - partito, 1)
            break
        schermi = None
        time.sleep(2.0)
    esito["schermi"] = schermi

    if schermi is None or schermi < OUTPUT_MINIMI:
        # ⛔ E NON e' un rosso: e' «non ho potuto guardare».  Una finestra non
        #    puo' aprirsi dove non c'e' uno schermo, e accusare l'applicazione
        #    vorrebbe dire accusarla di una cosa successa prima di lei.
        esito["perche"] = ("in %.0f s il compositore non ha annunciato nessuno "
                           "schermo (%s) ⇒ nessuna applicazione poteva aprire "
                           "una finestra" % (a.attesa_palco, motivo or "?"))
        cliente.kill()
        chiudi_il_cliente(30)
        sgombra(chi, a.attesa_sgombero)
        return esito

    # ── 4. l'applicazione ───────────────────────────────────────────────────
    argomenti = a.argomenti_ciechi if modo == "cieca" else a.argomenti
    display, err = accendi_l_applicazione(chi, a.applicazione, argomenti, a.pagina)
    if display is None:
        esito["perche"] = "non ho potuto accendere l'applicazione: %s" % err
        cliente.kill()
        chiudi_il_cliente(30)
        sgombra(chi, a.attesa_sgombero)
        return esito

    # ⛔⛔ E PRIMA DI OGNI ALTRA COSA SI ASPETTA CHE ESISTA — vedi
    #     `aspetta_che_parta`: se non parte affatto l'esito e' «non ho potuto
    #     guardare», non un rosso al prodotto; e il guasto «muore subito» deve
    #     uccidere quel che ha VISTO vivo, non quel che spera esista.
    vivi, esito["avvio_s"] = aspetta_che_parta(chi, a.applicazione, a.attesa_avvio)
    if not vivi:
        detta = ultima_riga_detta(chi)
        esito["perche"] = ("l'applicazione «%s» non e' mai partita in %.0f s%s "
                           "⇒ non e' il prodotto a non avermi mostrato una "
                           "finestra: non c'era nessuno a disegnarla"
                           % (a.applicazione, a.attesa_avvio,
                              (": dice «%s»" % detta) if detta else
                              " (e non ha detto niente)"))
        cliente.kill()
        chiudi_il_cliente(30)
        sgombra(chi, a.attesa_sgombero)
        return esito

    if modo == "muore":
        # ⛔ IL GUASTO: l'applicazione muore subito.  ⚠ E si uccide PER NOME e
        #    PER UTENTE, mai con un modello globale — fase 10 §7.3, dove un
        #    `pkill -f` globale ha rischiato di uccidere il lavoro di un'altra
        #    prova che stava misurando.
        # ⭐ E L'ESITO DEL `pkill` SI GUARDA: e' la differenza fra «ho ucciso» e
        #   «non c'era niente da uccidere», ed e' quel che distingue un guasto
        #   innestato da un'iniezione andata a vuoto (`LEZIONI.md` §1.46).
        time.sleep(a.muore_dopo)
        r = sh("pkill -KILL -u %s -f %s" % (chi, a.applicazione))
        esito["ucciso"] = (r.returncode == 0)
        if r.returncode != 0:
            esito["perche"] = ("ho chiesto di uccidere «%s» e `pkill` non ha "
                               "trovato niente da uccidere (esito %d): "
                               "l'iniezione non ha preso"
                               % (a.applicazione, r.returncode))
            cliente.kill()
            chiudi_il_cliente(30)
            sgombra(chi, a.attesa_sgombero)
            return esito

    # ── 5. si aspetta che dipinga ───────────────────────────────────────────
    time.sleep(a.attesa_finestra)
    esito["processi_apertura"] = quanti_processi(chi, a.applicazione)

    # ── 6. il cliente finisce e scrive il flusso ────────────────────────────
    # ⛔ E I PROCESSI SI RICONTANO QUI, accanto all'ultimo fotogramma: e' quello
    #    che si giudica, e un conto preso due minuti prima non gli sta accanto.
    coda = chiudi_il_cliente(int(resta) + 180)
    esito["processi"] = quanti_processi(chi, a.applicazione)
    esito["fotogrammi"] = quanti_fotogrammi(coda or "")
    esito["detto"] = ultima_riga_detta(chi)
    ammesso = e_stato_ammesso(coda)

    if ammesso is not True:
        # ⛔ «Non ammesso» da solo e' un silenzio: nasconde tre cose diverse.
        #    ⇒ Si porta il MOTIVO accanto al sintomo (`LEZIONI.md` §1.9).
        ultimo = "?"
        for riga in reversed((coda or "").strip().splitlines()):
            riga = riga.strip()
            if riga and not riga.startswith("=="):
                ultimo = riga[:90]
                break
        esito["perche"] = ("il cliente %s: %s"
                           % ("non e' stato AMMESSO" if ammesso is False
                              else "non ha detto NIENTE", ultimo))
        sgombra(chi, a.attesa_sgombero)
        return esito
    if not esito["fotogrammi"]:
        # ⚠ E si distingue «zero» da «non lo so», che qui hanno cause opposte.
        esito["perche"] = (
            "%s ⇒ non ho niente da guardare (ultima riga del cliente: «%s»)"
            % ("nessun fotogramma e' arrivato dal filo"
               if esito["fotogrammi"] == 0 else
               "il cliente non ha detto quanti fotogrammi ha preso", ultimo_detto(coda)))
        sgombra(chi, a.attesa_sgombero)
        return esito

    # ── 7. il giudizio, nel pixel ───────────────────────────────────────────
    # ⛔ I tetti di ffmpeg SEGUONO il lavoro che governano, invece di stare
    #    fermi mentre `--attesa-palco` cresce: `LEZIONI.md` §1.17 — un numero
    #    che dipende da un altro e non lo sa e' un numero che mentira'.
    tetto = max(300.0, resta * 2.0)
    prima_tutti, scaduto_p = i_fotogrammi_di_prima(
        flusso, lavoro, a.fotogrammi_prima, tetto)
    ultimo, scaduto_u = l_ultimo_fotogramma(flusso, lavoro, tetto)
    if scaduto_u:
        esito["perche"] = ("il decodificatore non ha finito in %.0f s: quel che "
                           "ha lasciato NON e' l'ultimo fotogramma ma uno di "
                           "mezzo, e non lo giudico" % tetto)
        sgombra(chi, a.attesa_sgombero)
        return esito
    if not prima_tutti:
        esito["perche"] = ("%d fotogrammi sono arrivati ma il decodificatore "
                           "non ne ha fatto nessuna immagine%s"
                           % (esito["fotogrammi"],
                              " (ed e' scaduto)" if scaduto_p else ""))
        sgombra(chi, a.attesa_sgombero)
        return esito

    primo, guardati, verdetti = scegli_il_prima(prima_tutti, giudice.giudica)
    esito["guardati_prima"] = guardati
    esito["png_prima"], esito["png_dopo"] = primo, ultimo
    if primo is None:
        esito["perche"] = ("i primi %d fotogrammi sono tutti neri o quasi (%s): "
                           "il desktop non aveva niente da mostrare PRIMA "
                           "dell'applicazione, e questo non e' un giudizio su C2"
                           % (guardati, ", ".join(verdetti[:6])))
        sgombra(chi, a.attesa_sgombero)
        return esito

    def frazione(p):
        return lettore.frazione_del_colore(p, COLORE, TOLLERANZA)

    g = giudica_il_giro(primo, ultimo, giudice.giudica, frazione,
                        esito["processi"], a.frazione_minima, a.margine)
    esito.update({k: g[k] for k in ("stato", "perche", "frazione_prima",
                                    "frazione_dopo", "desktop_prima")})
    if esito["stato"] == "non-vista" and esito["detto"]:
        # ⭐ Il motivo accanto al sintomo: «non si vede» da solo nasconde
        #   «l'applicazione si e' lamentata», e il suo registro lo dice.
        esito["perche"] += " ⚠ (l'applicazione dice: «%s»)" % esito["detto"]
    sgombra(chi, a.attesa_sgombero)
    return esito


def ultimo_detto(coda):
    for riga in reversed((coda or "").strip().splitlines()):
        riga = riga.strip()
        if riga and not riga.startswith("=="):
            return riga[:90]
    return "?"


def _n(x):
    return "non lo so" if x is None else x


def stampa(e):
    faccia = {"vista": "SI ", "non-vista": "NO ", "non-lo-so": "?  "}[e["stato"]]
    print("  %-8s %-6s %s  %s" % (e["chi"], e["modo"], faccia, e["perche"]))
    print("           schermi annunciati: %s · palco in %s s · applicazione viva "
          "dopo %s s · fotogrammi: %s"
          % (_n(e["schermi"]), _n(e["palco_s"]), _n(e["avvio_s"]),
             _n(e["fotogrammi"])))
    print("           ⚠ processi (NON decidono): %s all'apertura, %s alla fine · "
          "fotogrammi guardati per il «prima»: %s"
          % (_n(e["processi_apertura"]), _n(e["processi"]),
             _n(e["guardati_prima"])))
    # ⭐ E I DUE PNG GIUDICATI SI DICONO SEMPRE: su un rosso, senza il percorso,
    #   non c'e' niente da guardare senza sapere gia' dove cercare.
    if e["png_prima"] or e["png_dopo"]:
        print("           le due immagini giudicate: %s  ·  %s"
              % (e["png_prima"] or "—", e["png_dopo"] or "—"))


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ IL GIUNTO — e sta in una funzione PURA perche' `--certifica` lo provi.
#
# ⛔⛔ E' il pezzo che `LEZIONI.md` §1.52 e' nata per: *«la certificazione di C9
#     provava il giudice, quella di C13 provava la lettura del registro; il
#     difetto stava nel GIUNTO fra le due — nel codice d'uscita, che non e' di
#     nessuno dei due mestieri»*.  ⇒ Qui il codice d'uscita col guasto innestato
#     e' **invertito** (`0` = il guasto e' stato visto), e da lui `11-gancio.sh`
#     ricava `ha_visto_il_guasto`, da cui C13 dice se la rete sa ancora dare
#     rosso.  ⛔ Un giunto cosi' non si lascia non certificato.
# ═══════════════════════════════════════════════════════════════════════════
def collauda_il_guasto(guasto, sano, rotto, frazione_minima=FRAZIONE_MINIMA,
                       quota=QUOTA_GUASTO):
    """Torna `(esito, [righe da stampare])`.  ⛔ L'esito si legge AL CONTRARIO.

        0  ⭐ il guasto E' STATO VISTO — la maglia sa dare rosso
        1  ⛔ il guasto NON e' stato visto, o ha morso troppo poco
        3  ⚠ non ho potuto innestarlo o non ho potuto guardare
           ⇒ ne' una certificazione ne' un'accusa
    """
    r = []
    r.append("  controllo sano  : %-10s (colore %s · processi %s)"
             % (sano["stato"],
                "non lo so" if sano["frazione_dopo"] is None
                else "%.1f%%" % (sano["frazione_dopo"] * 100),
                _n(sano["processi"])))
    r.append("  con il guasto   : %-10s (colore %s · processi %s)"
             % (rotto["stato"],
                "non lo so" if rotto["frazione_dopo"] is None
                else "%.1f%%" % (rotto["frazione_dopo"] * 100),
                _n(rotto["processi"])))
    r.append("")

    if sano["stato"] == "non-lo-so" or rotto["stato"] == "non-lo-so":
        r.append("⚠ non ho potuto giudicare: non posso dire se il guasto si "
                 "sarebbe visto")
        r.append("   ⇒ e questo NON accusa la maglia (§4.5: il gancio lo scrive "
                 "come «innesto non giudicato»)")
        return 3, r

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔⛔ IL CONTROLLO SANO ROSSO ESCE **3**, E NON 1 — ed e' una correzione.
    #
    # La prima stesura usciva **1**.  ⚠ Ma `11-gancio.sh` legge un giro innestato
    # AL CONTRARIO: `1` ⇒ `ha_visto_il_guasto: false`.  ⇒ ⛔ Una regressione VERA
    # del prodotto, capitata proprio durante il giro col guasto innestato,
    # avrebbe fatto scrivere a C13 *«la rete non sa piu' dare rosso»* — che e'
    # esattamente il difetto di §1.52, prodotto dalla cura di §1.52.
    # ⭐ Il rosso vero c'e' gia' e lo da' il giro SENZA guasto, che nella
    #   famiglia gira subito prima: qui non serve ripeterlo, serve non mentire.
    # ═══════════════════════════════════════════════════════════════════════
    if sano["stato"] != "vista":
        r.append("⛔⛔ IL CONTROLLO SANO E' ROSSO: %s" % sano["perche"])
        r.append("    ⇒ questo giro NON misura il guasto — misura un rosso che")
        r.append("      c'e' gia' per conto suo (LEZIONI.md §1.45).")
        r.append("    ⚠ E l'esito e' 3 e non 1: dire «il guasto non e' stato "
                 "visto» sarebbe")
        r.append("      un'accusa alla rete per una regressione del PRODOTTO. "
                 "⇒ Il rosso vero")
        r.append("      lo da' il giro senza guasto, che gira subito prima.")
        return 3, r

    if rotto["stato"] != "non-vista":
        r.append("⛔⛔ IL GUASTO INNESTATO NON E' STATO VISTO: la finestra si "
                 "vede lo stesso.")
        r.append("    ⇒ o il guasto non morde, o questa maglia non guarda nel "
                 "posto giusto —")
        r.append("      e in tutt'e due i casi non ci si puo' fidare di lei.")
        return 1, r

    # ⚠ E OGNI GUASTO PRETENDE LA PROPRIA FIRMA, o non e' quel guasto.
    #   ⛔ E se la firma manca l'esito e' **3**: una maglia che non ha potuto
    #      innestare il guasto non ha ne' visto ne' mancato niente.
    proc = rotto["processi"]
    if guasto == "muore":
        if proc is None or proc > 0:
            r.append("⚠ il guasto chiesto era «l'applicazione muore subito», ⛔ "
                     "ma alla fine i processi sono %s: l'iniezione non ha preso."
                     % _n(proc))
            r.append("   ⇒ non ho innestato quel guasto (esito 3, non un rosso).")
            return 3, r
        if rotto.get("ucciso") is False:
            r.append("⚠ `pkill` non ha trovato niente da uccidere: l'iniezione "
                     "non ha preso (esito 3, non un rosso).")
            return 3, r
    else:
        if proc is None or proc < 1:
            r.append("⚠ il guasto chiesto era «la finestra non si apre e il "
                     "processo RESTA VIVO», ⛔ ma i processi sono %s." % _n(proc))
            r.append("   ⇒ senza un processo vivo starei provando l'altro "
                     "guasto (esito 3, non un rosso).")
            return 3, r

    # ⭐ E ADESSO LA DIFFERENZA MISURABILE, che e' quel che §1.52 pretende.
    fs = sano["frazione_dopo"] or 0.0
    fr = rotto["frazione_dopo"] or 0.0
    r.append("  ⭐ differenza misurabile: il colore passa dal %.1f%% al %.1f%% "
             "⇒ %.1f punti, cioe' il %.0f%% del sano (ne ammetto al piu' il "
             "%.0f%%)"
             % (fs * 100, fr * 100, (fs - fr) * 100,
                (fr / fs * 100) if fs else 0.0, quota * 100))
    if fs <= 0 or fr > fs * quota:
        r.append("⛔ il verdetto e' cambiato ma il NUMERO quasi no: il guasto ha "
                 "morso poco o niente,")
        r.append("   e un collaudo cosi' non certifica la rete.")
        return 1, r

    if guasto == "muore":
        r.append("  ⭐ e la firma del guasto c'e': processi = 0 alla fine "
                 "(l'applicazione e' morta davvero)")
    else:
        # ⭐⭐ LA DIMOSTRAZIONE, con due numeri invece che con una citazione.
        # ⚠ E si dice quel che dimostra DAVVERO: non che i due conti siano
        #   uguali (Firefox in kiosk fa piu' processi che senza testa), ⛔ ma
        #   che **in tutt'e due i casi c'e' almeno un processo vivo** — cioe'
        #   che il conto, qualunque sia, non separa i due mondi.  Il pixel si'.
        r.append("  ⭐⭐ E QUESTA E' LA DIMOSTRAZIONE, con due numeri invece che "
                 "con una citazione:")
        r.append("     l'applicazione e' VIVA in tutt'e due i giri — %s processi "
                 "col sano, %s col guasto —"
                 % (_n(sano["processi"]), _n(rotto["processi"])))
        r.append("     e i verdetti sono OPPOSTI.  ⇒ ⛔ il conto dei processi non "
                 "separa i due mondi; il pixel si'.")
        r.append("     E' il rilievo di `fasi/11…` §4.1 (`[M]` diceva 1 in "
                 "tutt'e due i casi), misurato qui.")

    r.append("")
    r.append("⭐ IL GUASTO INNESTATO E' STATO VISTO — questa maglia SA dare rosso.")
    return 0, r


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--utente-base", default="c2u")
    p.add_argument("--giri", type=int, default=1,
                   help="⚠ uno basta: «si vede o non si vede» e' deterministico, "
                        "e ogni giro costa una nascita di sessione")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=8511)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--pagina", default="/opt/remotix/11-c2-finestra.html")
    p.add_argument("--applicazione", default="firefox-esr",
                   help="⚠ oggi il browser, perche' e' l'unico programma della "
                        "scatola che dipinga un colore DICHIARATO. ⛔ Va "
                        "spostata su un cliente Wayland minimo appena ce n'e' "
                        "uno che sappia farlo (vedi in testa)")
    p.add_argument("--argomenti", default="--kiosk file://%(pagina)s",
                   help="come si chiede all'applicazione di aprire la pagina")
    p.add_argument("--argomenti-ciechi", default="--headless file://%(pagina)s",
                   help="⛔ IL GUASTO «finestra che non si apre»: l'applicazione "
                        "resta VIVA e non dipinge niente")
    p.add_argument("--lavoro", default="/var/lib/rete11/c2")
    # ⭐ 60 s, e il numero viene da una MISURA: `[M]` 27 agosto 2026, dentro la
    #   scatola GNOME curata il palco nasce in **2,1÷4,2 s** ⇒ 60 s sono piu'
    #   di dieci volte il peggiore misurato.  ⛔ I 200 s di prima erano un
    #   numero prudente scelto quando il fenomeno sembrava durare ~97 s — che
    #   era un guasto della scatola, poi curato (`LEZIONI.md` §1.54).
    # ⚠ E qui non e' una scadenza ma un ADDENDO di `--resta`: ogni secondo di
    #   troppo e' un secondo buttato per ogni inquilino, non un margine.
    p.add_argument("--attesa-palco", type=float, default=60.0,
                   help="⛔ TETTO DA RITARARE. [M] (C1, 27 ago 2026, non mia) il "
                        "palco nella scatola GNOME nasce in 95-101 s per un "
                        "difetto della SCATOLA (polkit); curato quello, ~2 s ⇒ "
                        "rimettere a ~20")
    p.add_argument("--attesa-avvio", type=float, default=30.0,
                   help="⛔ quanto si aspetta che l'applicazione ESISTA (un "
                        "processo suo). Scaduto: «non ho potuto guardare», mai "
                        "un rosso — e il guasto «muore subito» uccide solo quel "
                        "che ha visto vivo")
    p.add_argument("--attesa-finestra", type=float, default=120.0,
                   help="⛔ TETTO DA RITARARE: quanto si da' all'applicazione "
                        "per DIPINGERE, dopo che e' partita. ⚠ 120 come C8, e "
                        "per la stessa ragione MISURATA: [M] il primo avvio di "
                        "Firefox in una scatola fredda passa i 25 s, e qui la "
                        "scatola e' fredda davvero — `crea()` fa `userdel -r`, "
                        "quindi nessun profilo esiste")
    p.add_argument("--fotogrammi-prima", type=int, default=12,
                   help="quanti fotogrammi iniziali si guardano per trovare il "
                        "«prima» disegnato. ⛔ Uno solo darebbe «non lo so» per "
                        "sempre se il primo fosse nero (LEZIONI.md §1.49)")
    p.add_argument("--coda", type=float, default=15.0,
                   help="quanto il cliente resta attaccato DOPO che la finestra "
                        "e' stata giudicata pronta, per portarsi via i fotogrammi")
    p.add_argument("--attesa-sgombero", type=float, default=60.0)
    p.add_argument("--muore-dopo", type=float, default=1.5,
                   help="quanto vive l'applicazione nel guasto «muore subito»")
    p.add_argument("--frazione-minima", type=float, default=FRAZIONE_MINIMA)
    p.add_argument("--margine", type=float, default=MARGINE)
    p.add_argument("--applicazione-che-muore", action="store_true",
                   help="⛔ GUASTO INNESTATO: l'applicazione parte e muore subito. "
                        "L'esito si legge AL CONTRARIO (0 = il guasto e' stato visto)")
    p.add_argument("--finestra-che-non-si-apre", action="store_true",
                   help="⛔ GUASTO INNESTATO: l'applicazione resta VIVA e non "
                        "dipinge. ⭐ E' il caso che dimostra che contare i "
                        "processi non basta")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    if a.applicazione_che_muore and a.finestra_che_non_si_apre:
        print("⛔ un guasto per volta: se se ne innestano due non si sa piu' "
              "quale ha morso")
        sys.exit(2)
    # ═══════════════════════════════════════════════════════════════════════
    # ⛔⛔ LE GUARDIE SUI NUMERI, e non sono pignoleria: sono `LEZIONI.md` §1.44.
    #
    #   `--giri 0`            ⇒ nessun giro, nessun rosso, nessun «non lo so»
    #                           ⇒ ⛔ **VERDE con zero misure sotto**
    #   `--frazione-minima 0` ⇒ qualunque immagine passa ⇒ un predicato che non
    #                           puo' fallire, chiesto dalla riga di comando
    # ⚠ E `--certifica` non se ne accorgerebbe: certifica le COSTANTI, non gli
    #   argomenti.  ⇒ La guardia va qui, dove gli argomenti arrivano.
    # ═══════════════════════════════════════════════════════════════════════
    if a.giri < 1:
        print("⛔ --giri %d: un giro che non gira non e' un verde, e' un uso "
              "sbagliato" % a.giri)
        sys.exit(2)
    if a.frazione_minima <= 0 or a.frazione_minima > 1:
        print("⛔ --frazione-minima %s: con 0 (o meno) questa maglia non "
              "potrebbe piu' dare rosso, e sopra 1 non potrebbe dare verde"
              % a.frazione_minima)
        sys.exit(2)
    if a.margine < 0 or a.margine > 1:
        print("⛔ --margine %s: fuori da 0..1 non governa piu' niente"
              % a.margine)
        sys.exit(2)
    if os.geteuid() != 0:
        print("⛔ va eseguita da amministratore: deve creare inquilini nuovi")
        sys.exit(2)

    # ── il terreno: senza uno di questi non si giudica, e si dice quale ─────
    giudice, dove_g = giudice_del_desktop()
    if giudice is None:
        print("⛔ non trovo il giudice delle immagini (10-f1-testimone.py) accanto a me")
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    lettore, dove_l = lettore_del_colore()
    if lettore is None:
        print("⛔ non trovo il lettore del colore (11-c8-…py) accanto a me")
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    for che, dove in (("il cliente di prova", a.cliente),
                      ("la pagina bersaglio", a.pagina)):
        if not os.path.exists(dove):
            print("⛔ non trovo %s: %s" % (che, dove))
            print("   ⇒ non ho potuto guardare")
            sys.exit(3)
    for programma in (a.applicazione, "ffmpeg", "wayland-info", "runuser"):
        if sh("command -v %s" % programma).returncode != 0:
            print("⛔ nella scatola non c'e' %s" % programma)
            print("   ⇒ non ho potuto guardare")
            sys.exit(3)
    try:
        import numpy, PIL  # noqa: F401
    except ImportError:
        print("⛔ mancano numpy o Pillow: il giudice non puo' leggere un'immagine")
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)

    os.makedirs(a.lavoro, exist_ok=True)
    guasto = ("muore" if a.applicazione_che_muore else
              "cieca" if a.finestra_che_non_si_apre else None)

    # ⭐ PRIMA di ogni `crea`: `crea` fa `userdel -r`, e da quel momento il
    #   padrone di `/tmp/mozilla` sarebbe un NUMERO invece di un nome — cioe'
    #   non lo riconoscerei piu' come mio.
    resto = sgombra_il_mio_rimasuglio(a.utente_base)

    print("== C2 — una finestra si apre ==")
    print("   porta %d · applicazione «%s» · pagina %s"
          % (a.porta, a.applicazione, os.path.basename(a.pagina)))
    print("   metro: colore %s ±%d per canale, almeno il %.0f%% dello schermo, "
          "cresciuto di almeno %.0f punti"
          % (COLORE, TOLLERANZA, a.frazione_minima * 100, a.margine * 100))
    print("   giudici importati: %s · %s"
          % (os.path.basename(dove_g), os.path.basename(dove_l)))
    print("   provvista: la cura di src/provisiona.sh, importata da C8, a ogni "
          "inquilino che creo")
    if resto:
        print("   %s" % resto)
    print("   tetti (⛔ da ritarare sul vero): palco %.0f s · finestra %.0f s · "
          "coda %.0f s" % (a.attesa_palco, a.attesa_finestra, a.coda))
    if guasto:
        print("   ⛔ GUASTO INNESTATO: «%s» — e l'esito si legge AL CONTRARIO"
              % ("l'applicazione muore subito" if guasto == "muore"
                 else "l'applicazione resta VIVA e non dipinge"))
        print("   ⭐ e con lui gira un CONTROLLO SANO, o non si potrebbe "
              "distinguere «il guasto ha morso» da «era gia' rosso»")
    print("   ⛔ il conto dei processi viene riportato e NON decide niente: "
          "[M] fasi/10 §7.4 diceva 1 in tutt'e due i casi")
    print()

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ COL GUASTO INNESTATO SI APRONO DUE INQUILINI, e non uno.
    #    `LEZIONI.md` §1.52: il guasto non si misura sul colore del verdetto, si
    #    misura sulla DIFFERENZA rispetto al giro senza guasto.
    # ═══════════════════════════════════════════════════════════════════════
    gambe = []
    if guasto:
        gambe.append((None, "sano"))
        gambe.append((guasto, "guasto"))
    else:
        for n in range(a.giri):
            gambe.append((None, "sano"))

    esiti = []
    for n, (modo, _nome) in enumerate(gambe, 1):
        chi = "%s%d" % (a.utente_base, n)
        e = un_giro(chi, modo, a, giudice, lettore)
        esiti.append(e)
        stampa(e)

    print()
    if not guasto:
        viste = sum(1 for e in esiti if e["stato"] == "vista")
        no = sum(1 for e in esiti if e["stato"] == "non-vista")
        ignoti = sum(1 for e in esiti if e["stato"] == "non-lo-so")
        print("  finestre viste: %d   ⛔ NON viste: %d   non giudicate: %d"
              % (viste, no, ignoti))
        if no:
            print("\n  ⛔⛔ ROSSO — %d sessioni su %d non hanno mostrato nessuna "
                  "finestra." % (no, len(esiti)))
            sys.exit(1)
        if ignoti:
            print("\n  ⚠ NON GIUDICO — %d giri non hanno potuto parlare." % ignoti)
            print("     ⛔ E questo non e' un verde: e' un esito suo (§4.5).")
            sys.exit(3)
        print("\n  ⭐ VERDE — la finestra si vede in tutte e %d le sessioni."
              % len(esiti))
        sys.exit(0)

    # ── il collaudo del guasto innestato ────────────────────────────────────
    esito, righe = collauda_il_guasto(guasto, esiti[0], esiti[1],
                                      a.frazione_minima)
    for riga in righe:
        print(riga)
    sys.exit(esito)


if __name__ == "__main__":
    main()
