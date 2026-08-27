#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c6 — ⭐⭐⭐ «SI STACCA E SI RITROVA»
===========================================================================

    python3 11-c6-si-stacca-e-si-ritrova.py --porta 8511
    python3 11-c6-si-stacca-e-si-ritrova.py --porta 8511 --uccidi-la-sessione
    python3 11-c6-si-stacca-e-si-ritrova.py --certifica

La riga C6 di `fasi/11-la-rete-di-sicurezza.md` §4.1:

    che cosa deve essere vero : si stacca e si ritrova
    da dove parte             : una sessione GIA' VIVA (⚠ qui e' giusto cosi',
                                ed e' l'unica riga della lista che parte cosi')
    che cosa guarda           : dopo il riattacco — stessa sessione, stesse
                                finestre, ⭐ VISTE NELL'IMMAGINE
    come so che sa dare rosso : si uccide la sessione ⇒ rosso

---------------------------------------------------------------------------
⛔⛔⛔ PERCHE' QUESTA MAGLIA CONTA PIU' DELLE ALTRE, e va letto prima dei numeri
---------------------------------------------------------------------------

L'invariante **I4** del progetto e' una promessa dichiarata, e sta scritta nel
codice consegnato (`src/main.c:505-507`):

    *«il palco appartiene alla SESSIONE, non alla connessione, e muore solo per
      logout esplicito o per abbandono a 60 minuti senza input»*

⇒ ⭐ **C6 e' la maglia che va a vedere se quella promessa e' vera dal lato
  dell'utente** — cioe' non «il processo c'e' ancora?» ma *«mi stacco, torno, e
  ritrovo quel che avevo lasciato?»*.

⚠⚠ E OGGI C'E' UNA MISURA CHE DICE DI NO.  `[M]` 27 agosto 2026, banco isolato
   con Mutter vero (⛔ **non l'ho fatta girare io**: e' la misura di un altro
   agente di questa fase, e la riporto per intero perche' e' la ragione per cui
   C6 e' scritta cosi'):

     · il `wl_output` di una sessione headless nasce **solo quando un
       consumatore PipeWire si aggancia** al flusso — 65÷93 ms dopo, ⛔ mai
       prima;
     · il monitor **sopravvive** allo stacco del CONSUMATORE (misurato: a 15 s
       c'e' ancora), ⛔ ma **muore con la connessione D-Bus di chi ha chiamato
       `RecordVirtual`**;
     · nel prodotto quella connessione e' del **figlio** dell'inquilino.

   ⇒ ⭐⭐ Se il palco muore quando nessuno guarda, **oggi il desktop ha uno
     schermo solo mentre qualcuno lo sta guardando** — e I4, dal lato
     dell'utente, e' rotta.

⛔ E allora questa maglia deve poter dare **ROSSO** oggi.  Se dice verde, non e'
   una buona notizia: e' una maglia compiacente, e va guardata in faccia
   (`LEZIONI.md` §1.47, ultima riga).

---------------------------------------------------------------------------
⛔⛔ LE TRE DOMANDE CHE C6 NON FA — e ognuna sarebbe un verde per sempre
---------------------------------------------------------------------------

  ⛔ *«la sessione esiste ancora?»*   ⭐ ESISTE.  Il figlio sopravvive al
     distacco, e C7 l'ha gia' MISURATO (`[M]` 26 ago 2026, scatola XFCE: dopo il
     distacco l'inquilino aveva ancora 8 processi e 8 voci in
     `XDG_RUNTIME_DIR`).  ⇒ Chiedere questo vorrebbe dire un predicato che non
     puo' fallire: `LEZIONI.md` §1.44.  ⚠ **E' il PALCO a essere perso, non la
     sessione** — sono due cose, e la differenza e' tutta questa maglia.

  ⛔ *«il processo c'e'?»*            stessa cosa, un piano piu' giu'.  ⚠ Il
     conto dei processi ha gia' mentito una volta in questo progetto: `[M]`
     diceva «1» con la finestra e senza (§4.1, riga C2).

  ⛔ *«il registro dice che va bene?»*  ⚠ Il registro e' il metro di C1, e C1
     ha un difetto noto proprio li': legge come prova di cecita' una riga che
     il prodotto scrive nella nascita **riuscita** (`src/sessione.c:345-348`).
     ⇒ C6 **non apre il registro**, di proposito.  Il suo giudizio sta
     nell'immagine, e nel confronto fra due immagini.

---------------------------------------------------------------------------
⭐⭐⭐ CHE COSA VUOL DIRE «STESSE FINESTRE» — il metro, dichiarato
---------------------------------------------------------------------------

§4.3 del documento di fase: *«il confronto pixel-per-pixel con un'immagine di
riferimento marcisce in una settimana»*, e ⛔ **nessuno sa che aspetto abbia un
desktop**.  ⇒ Il metro non puo' essere «riconosco il desktop»: dev'essere povero
e non fragile.

⭐ **Allora la scena la METTIAMO NOI, e cosi' sappiamo che aspetto ha.**  Prima
  del distacco si apre, dentro la sessione, **una finestra di colore
  dichiarato**: il browser a tutto schermo sulla pagina `11-c8-pagina.html`,
  che e' `#FF00FF`.  ⇒ *«stesse finestre»* diventa una domanda a cui si puo'
  rispondere con un istogramma:

    1. ⭐ **la scena si ritrova**: dopo il riattacco almeno **la frazione minima
       di C8** (oggi il 25 % dello schermo) e' ancora del colore della scena,
       entro la tolleranza dichiarata da C8.  ⛔ Quel numero NON e' copiato qui:
       si importa, o il giorno che qualcuno tara C8 le due maglie comincerebbero
       a giudicare la stessa immagine in due modi diversi;
    2. ⭐ **ed e' la STESSA scena**: la frazione DOPO non si scosta da quella
       PRIMA piu' di **`SCARTO_MASSIMO`** in assoluto (oggi 0,25, ⚠ `[?]` non
       misurato ⇒ e' un argomento).  Non «identica»: una finestra che
       si sposta di venti pixel non e' un guasto, e pretendere l'uguaglianza
       esatta sarebbe la prova che marcisce;
    3. ⚠ **e l'immagine non e' degenere**: il giudice di `10-f1-testimone.py`
       dice «nero» / «quasi-nero» / «tinta-unita» / «disegnato», e serve a
       NOMINARE il rosso — un desktop tornato nero e un desktop tornato vuoto
       sono due guasti diversi con la stessa frazione (zero).

⛔ **E UNA FINESTRA, NON UNO SFONDO.**  La tentazione povera era tingere lo
   sfondo del desktop (`gsettings`) invece di aprire una finestra: costa meno e
   non vuole il browser.  ⚠ Ma non distinguerebbe niente: se il monitor muore e
   rinasce, lo **sfondo torna da solo** — e' del compositore.  ⭐ Quel che non
   torna, se il palco e' stato perso, sono **le finestre**.  ⇒ La scena
   dev'essere una finestra, o la maglia e' compiacente.

⛔ **E QUEL CHE NON SI GIUDICA, dichiarato**: la posizione della finestra, la
   barra di GNOME, i caratteri, la somiglianza pixel-per-pixel fra le due
   immagini.  ⇒ §4.3: sono tutte cose che cambiano senza che niente sia rotto.

---------------------------------------------------------------------------
⛔⛔⛔ LA GUARDIA CHE TIENE IN PIEDI TUTTO — «due zeri sono uguali»
---------------------------------------------------------------------------

⚠ Senza questa riga C6 sarebbe la maglia piu' compiacente della rete, e lo
  sarebbe **in silenzio**:

    la scena non si vede PRIMA (0,00)  e  non si vede DOPO (0,00)
    ⇒ «stessa frazione» ⇒ ⛔ **VERDE**

  ⭐ E' `LEZIONI.md` §1.47 alla lettera — *un confronto fra valori che nessuno
    sa dare e' verde, e non ha guardato niente* — con l'aggravante che qui i due
    valori non sono muti: sono **zero**, che ha la faccia di una misura.

⇒ ⛔ **Se la scena non si vede PRIMA del distacco, C6 esce 3: «non ho potuto
  guardare».**  Non e' un rosso e non e' un verde.  ⚠ E il motivo si porta
  accanto al sintomo — il verdetto dell'immagine dice quale difetto A MONTE ha
  fermato la prova: un desktop «nero» e' la nascita in ritardo di §7-bis.13, un
  desktop «disegnato» senza magenta e' il browser che non ha aperto la finestra.

---------------------------------------------------------------------------
⭐⭐ C6 E C7 GUARDANO LO STESSO GESTO DA DUE LATI — e ⛔ non si contraddicono
---------------------------------------------------------------------------

`11-c7-si-chiude-e-non-resta-niente.py` ha, per un caso, il gesto identico a
questo: il cliente se ne va e la sessione **non** si chiude (`--solo-distacco`).
⛔ E per C7 quel caso **dev'essere VERDE**: e' I4 che fa il suo mestiere, e un
rosso li' sarebbe il difetto §1.49 (*un rosso che non si puo' far diventare
verde*).

⇒ ⭐ **Le due maglie fanno due domande diverse sullo stesso gesto:**

    C7 · *«dopo il distacco il FIGLIO e' ancora vivo?»*      oggi: ⭐ SI'
    C6 · *«e quel che il figlio teneva in piedi si RITROVA?»*  oggi: ⛔ forse no

⚠⚠ **C7 verde e C6 rossa insieme NON e' una contraddizione**: e' la misura di
   quanto poco *«il figlio e' vivo»* garantisca all'utente.  ⛔ E se qualcuno,
   leggendo C6 rossa, andasse a rendere C7 rossa «per coerenza», romperebbe la
   maglia sana per far compagnia a quella che ha trovato qualcosa.

⛔ **E il terzo caso va distinto una volta di piu': «si stacca soltanto» non e'
   una domanda di C6.**  C6 non giudica MAI il momento del distacco: giudica
   **dopo il riattacco**.  Fra i due c'e' una pausa dichiarata, ed e' l'unico
   punto della maglia in cui il tempo e' un argomento della prova (vedi sotto).

---------------------------------------------------------------------------
⭐⭐ LA PAUSA DEV'ESSERE PIU' LUNGA DELLA SOPRAVVIVENZA MISURATA
---------------------------------------------------------------------------

`[M]` (la misura del 27 agosto riportata in testa): il monitor **sopravvive** al
distacco del consumatore, e a **15 s** c'e' ancora.

⇒ ⛔ Una pausa piu' corta di 15 s farebbe riattaccare C6 **prima che il palco
  abbia avuto modo di morire**: la maglia direbbe verde e non avrebbe provato
  niente.  ⭐ La pausa predefinita e' **il doppio della sopravvivenza misurata**,
  e si stampa in ogni giro accanto alla misura da cui viene.

---------------------------------------------------------------------------
⛔ IL GUASTO INNESTATO — `--uccidi-la-sessione`, e si legge sulla DIFFERENZA
---------------------------------------------------------------------------

§4.1, colonna «come so che sa dare rosso»: *«si uccide la sessione ⇒ rosso»*.
Fra il distacco e il riattacco si fa quel che fa `logind` quando l'inquilino
esce davvero:

    loginctl terminate-user <chi>   +   pkill -KILL -u <chi>

⛔⛔ **E QUI STA LA COSA PIU' DELICATA DI TUTTA LA MAGLIA** — `LEZIONI.md`
    §1.52.  C6 porta con se' un difetto **vero e gia' noto**: se il palco muore
    col distacco, C6 e' rossa **anche senza** il guasto innestato.  ⇒ Leggere
    *«rosso ⇒ il guasto e' stato visto»* vorrebbe dire certificare tutta la rete
    su un difetto del PRODOTTO invece che sul proprio — un predicato che non
    puo' fallire, cioe' §1.44 di nuovo.

⭐ **La differenza misurabile che separa i due casi e' il PID DEL FIGLIO**, e i
  due guasti hanno firme opposte:

    il palco perso (il difetto di oggi)   il figlio e' **LO STESSO** pid, e le
                                          finestre non ci sono piu'
    la sessione uccisa (l'iniezione)      ⛔ il figlio **NON C'E' PIU'**, o e' un
                                          pid **DIVERSO**

⇒ Il guasto e' *«stato visto»* **solo se il figlio e' cambiato**.  ⛔ Se il
  verdetto e' rosso ma il figlio e' lo stesso, C6 lo dice a voce alta: *«rosso,
  ma non per colpa del guasto»*, ed esce **1**.

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)
---------------------------------------------------------------------------

  0  ⭐ ho guardato: si e' staccato, si e' riattaccato, ⭐ ha ritrovato la
     STESSA sessione e la STESSA scena
  1  ⛔ ho guardato e non regge ⇒ rosso.  Quattro specie, e si dicono per nome:
       (a) «le finestre non si ritrovano»  — la scena non c'e' piu'
       (b) «il palco non si ritrova»       — lo schermo e' tornato nero
       (c) «un'altra sessione»             — il figlio e' cambiato, o e' sparito
       (d) «non si rientra»                — il riattacco e' stato RIFIUTATO,
                                             con la stessa parola di un minuto fa
     ⚠ e una quinta, piu' mite: «la scena e' cambiata» — c'e', ma non e' quella
  3  ⛔ non ho potuto guardare: il cliente non e' stato ammesso, il figlio non
     e' nato, ⭐ **o la scena non si vedeva nemmeno PRIMA** — ⛔ e NON e' un rosso
  2  il terreno non regge, o l'uso e' sbagliato
  4  ⚠ non lo usa: C6 non prende nessun lucchetto della scheda.  E' dichiarato
     qui perche' un esito che non si usa e' meglio scriverlo che lasciarlo
     indovinare.

---------------------------------------------------------------------------
⛔ QUEL CHE C6 **NON** GUARDA — o qualcuno se ne fidera' troppo
---------------------------------------------------------------------------

  · **i residui**: che dopo la chiusura non resti niente e' C7, ed e' un altro
    mestiere.  C6 lascia la sessione viva fino allo sgombero del banco.
  · **il registro del prodotto**: non lo apre (vedi «le tre domande che non fa»).
  · **il suono, i tasti, il ritardo**: C5, C4, e la fase 12.
  · **quante volte di fila regge**: un giro solo.  ⚠ Se un giorno il difetto
    diventasse intermittente, questa riga andra' rifatta come C1 (`--giri`), e
    lo si scrive adesso invece di scoprirlo allora.
  · **il primo attacco in assoluto**: C6 parte da una sessione GIA' VIVA per
    mandato.  Che la sessione nasca e si veda e' C1 e C2.
===========================================================================
"""
import argparse
import importlib.util
import os
import re
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# ⭐⭐ IL NOME DEL FIGLIO — la voce su cui si regge «stessa sessione».
#
# ⛔ Il confronto e' per nome INTERO, come in C7: un `remotix-cliente` non e' il
#    figlio, e una sottostringa lo farebbe passare.
# `[M]` 26 ago 2026 (C7, scatola XFCE): `pid 12113 remotix, ppid 10575, uid c7u1`.
# ---------------------------------------------------------------------------
NOME_FIGLIO = "remotix"

# ⛔ Il valore che vuol dire «ho guardato e non c'e'».  ⚠ `None` vuol dire «non
#    ho potuto guardare», e le due cose non devono avere la stessa faccia
#    (§4.5, e la lezione §1.47).  E' la stessa convenzione di C7.
VUOTO = "(niente)"

# ---------------------------------------------------------------------------
# ⭐ QUANTO LA SCENA PUO' CAMBIARE E RESTARE «LA STESSA» — e non e' prudenza
#    generica: e' la meta' di §4.3 che si dimentica sempre.
#
# ⚠ Fra un attacco e l'altro il compositore puo' ridisegnare la barra, la
#   finestra puo' spostarsi di qualche pixel, la codifica in 4:2:0 restituisce
#   bordi leggermente diversi.  ⛔ Pretendere la stessa frazione al millesimo
#   sarebbe la prova che marcisce in una settimana.
# ⛔ E non si sceglie a occhio: `--certifica` contiene il caso «la frazione si
#   e' spostata di quanto lo scarto ammette ⇒ deve restare VERDE» **e** il caso
#   «spostata troppo ⇒ rosso», che e' la guardia che tiene onesto il numero.
# `[?]` Il valore e' PRUDENTE e non misurato sul vero: ⇒ e' un argomento
#   (`--scarto-massimo`), e si tara al primo giro verde.
# ---------------------------------------------------------------------------
SCARTO_MASSIMO = 0.25

# ---------------------------------------------------------------------------
# ⭐⭐ LA SOPRAVVIVENZA MISURATA DEL MONITOR, ed e' da qui che viene la pausa.
#
# `[M]` 27 ago 2026, banco isolato con Mutter vero (⛔ misura di un altro
# agente, non mia): staccato il consumatore PipeWire, il `wl_output` a **15 s**
# c'e' ancora.  ⇒ La pausa predefinita e' il DOPPIO: sotto quella soglia C6
# riattaccherebbe prima che il palco abbia avuto modo di morire, e direbbe verde
# senza aver provato niente.
# ---------------------------------------------------------------------------
SOPRAVVIVENZA_MISURATA_S = 15.0
PAUSA_PREDEFINITA_S = 2 * SOPRAVVIVENZA_MISURATA_S


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ I GIUDICI SI IMPORTANO, NON SI RISCRIVONO — e qui sono DUE
# ═══════════════════════════════════════════════════════════════════════════
def _carica(percorsi, nome):
    """Carica il primo modulo che esiste, o `None`.  ⛔ E' un CARICATORE, non un
       giudice: non decide niente, trova soltanto il file."""
    for p in percorsi:
        if not os.path.exists(p):
            continue
        spec = importlib.util.spec_from_file_location(nome, p)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None
        return m
    return None


_C1 = None


def casa_dell_ammissione():
    """⭐⭐ «IL CLIENTE E' STATO AMMESSO?» — ⛔ e la casa e' C1, non questo file.

    ⛔ Fino al 27 agosto 2026 qui c'era `"AMMESSO" in coda`, ⭐ e non poteva
       dire di no: `[R]` `01-b3-cliente.py` stampa quella parola anche nei
       **due messaggi di rifiuto** — «CONGEDO invece di AMMESSO: motivo …»
       (:1315) e «atteso AMMESSO, arrivato …» (:1322) — e li stampa sullo
       **stdout**, cioe' proprio dove si guardava.  ⇒ `LEZIONI.md` §1.44, un
       predicato che non puo' fallire: C6 si credeva rientrata **anche quando
       era stata respinta**, e poi dava la colpa al prodotto se la scena non
       c'era.  ⚠ E il guaio e' doppio qui, perche' `osservazione()` dichiara
       da sempre tre stati (`True`/`False`/`None`) e il preditcato vecchio
       non produceva mai il terzo.
    ⚠ Era in cinque maglie: sta in C1 sola (§1.47), e le altre la importano.
    ⛔ Se non si carica si esce **3** e lo si dice: ⛔ non si ripiega in
       silenzio sul predicato povero — che e' il difetto che si sta curando.
    """
    global _C1
    if _C1 is None:
        m = _carica([os.path.join(QUI, "11-c1-nasce-e-si-vede.py"),
                     os.path.join(os.path.dirname(QUI), "11-scatole",
                                  "11-c1-nasce-e-si-vede.py")],
                    "c1_ammissione")
        # ⛔ Si verifica che ci sia quel che serve, non ci si fida del nome
        #    del file (`CODER.md` §3.9).
        # ⭐ Da C1 vengono DUE cose: il predicato dell'ammissione e la
        #    garanzia dei gruppi della scheda.  Stessa ragione, stesso posto
        #    solo (§1.47).  ⛔ Si verifica che ci siano tutte.
        if m is not None and all(
                callable(getattr(m, x, None))
                for x in ("e_stato_ammesso", "certifica_ammissione",
                          "garantisci_i_gruppi", "verdetto_gruppi",
                          "certifica_gruppi")):
            _C1 = m
    if _C1 is None:
        print("⛔ non trovo `11-c1-nasce-e-si-vede.py` accanto a me, e da li'")
        print("   viene il predicato «il cliente e' stato AMMESSO?».")
        print("⇒ non ho potuto guardare — ⛔ e NON e' un rosso (§4.5).")
        sys.exit(3)
    return _C1


def e_stato_ammesso(coda):
    """⭐ `True` ammesso · `False` **RESPINTO** · `None` non ha detto niente.

    ⛔ `False` non e' un rosso del prodotto: `giudica()` lo porta a **3**.
    """
    return casa_dell_ammissione().e_stato_ammesso(coda)


def garantisci_i_gruppi(chi, prefisso="   "):
    """⭐⭐ I GRUPPI DELLA SCHEDA — ⛔ e anche questo sta in un posto solo (C1).

    Torna `(esito, perche)`: `0` = l'inquilino vede e si puo' misurare,
    `3` = ⛔ NON si misura.

    ⛔ Fino al 27 agosto 2026 questa maglia creava l'inquilino con
       `usermod -aG video,render` **e non rileggeva**: due nomi inchiodati (che
       sono di UNA distribuzione) e nessuna verifica.  ⭐ `[M]` senza i gruppi
       dei nodi `/dev/dri` la sessione nasce CIECA — 0 su 4, mai in 90 s, zero
       fotogrammi — e questa maglia avrebbe misurato il buio chiamandolo
       difetto del prodotto (`fasi/10-…` §7.4).
    ⭐ Il lavoro lo fa `attrezzi-gruppi-scheda.sh`, che legge i gid dai NODI e
       rilegge confrontando i numeri.  ⛔ Non se ne fa una copia qui (§1.47).
    """
    return casa_dell_ammissione().garantisci_i_gruppi(chi, prefisso)


def giudice_immagini():
    """⭐ Il giudice della DEGENERAZIONE: `10-f1-testimone.py`.

    ⛔ E' gia' tarato sul vero (25 agosto 2026: desktop nero misurato, soglia
       del «quasi-nero» messa in mezzo al vuoto fra i due mondi).  Riscriverne
       qui una copia vorrebbe dire due giudici che possono divergere in
       silenzio — e il giorno che divergono, il rosso lo darebbe quello
       sbagliato.
    ⚠ Si cerca accanto a me (dentro la scatola sta in `/opt/remotix`) e un
      piano piu' su (nel deposito sta in `banchi/`).
    """
    return _carica([os.path.join(QUI, "10-f1-testimone.py"),
                    os.path.join(os.path.dirname(QUI), "10-f1-testimone.py")],
                   "testimone10f1")


def lettore_del_colore():
    """⭐⭐ Il giudice del COLORE della scena: e' quello di **C8**, non un altro.

    ⛔ E la ragione vale piu' della comodita': C6 apre **la stessa finestra
       sulla stessa pagina** che apre C8.  ⇒ Se il colore, la tolleranza e la
       frazione minima stessero scritti in due file, il giorno che qualcuno
       tara C8 le due maglie comincerebbero a giudicare la stessa immagine in
       due modi diversi — e nessuno se ne accorgerebbe, perche' tutt'e due
       continuerebbero a girare.
    ⚠ E la taratura di quel lettore e' gia' fatta e gia' provata: la
      certificazione di C8 contiene il caso «colore spostato di quanto la
      tolleranza ammette ⇒ dev'essere VERDE».  ⛔ C6 non la rifa': la eredita'.
    """
    return _carica([os.path.join(QUI, "11-c8-il-secondo-apre-il-browser.py")],
                   "c8_browser")


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL GIUDICE — ⛔ una funzione PURA: non tocca il mondo, e percio' si
#                 certifica senza scatole, senza sessioni e senza rete.
# ═══════════════════════════════════════════════════════════════════════════
def osservazione(ammesso=None, figlio=None, frazione=None, verdetto=None,
                 fotogrammi=None):
    """Quel che si e' visto in UN attacco.

    ⛔ Ogni voce ha tre stati e non due: `None` = «non ho potuto guardare»,
       il valore = «ho guardato».  ⚠ Per il figlio c'e' anche `VUOTO` = «ho
       guardato e non c'era», che ⛔ non e' la stessa cosa di `None`.
    """
    return {"ammesso": ammesso, "figlio": figlio, "frazione": frazione,
            "verdetto": verdetto, "fotogrammi": fotogrammi}


def giudica(prima, dopo, frazione_minima, scarto_massimo=SCARTO_MASSIMO):
    """⭐ Il giudizio, tutto qui dentro.  Torna `(esito, specie, motivi)`.

    `specie` e' una parola per chi legge: «si ritrova» · «le finestre non si
    ritrovano» · «il palco non si ritrova» · «la scena e' cambiata» ·
    «un'altra sessione» · «la sessione non c'e' piu'» · «non si rientra» ·
    «non lo so».
    """
    # ═══════════════════════════════════════════════════════════════════════
    # LE GUARDIE DEL «PRIMA» — ⛔ senza queste il confronto e' fra due zeri
    # ═══════════════════════════════════════════════════════════════════════
    if prima["ammesso"] is not True:
        return 3, "non lo so", [
            "il cliente del PRIMO attacco non e' stato ammesso: non c'e'",
            "nessuna sessione viva da ritrovare, e C6 parte da una sessione",
            "gia' viva per mandato (§4.1).",
        ]
    if prima["figlio"] is None:
        return 3, "non lo so", [
            "non ho potuto leggere i processi dell'inquilino PRIMA del distacco",
            "⇒ non so quale sessione dovrei ritrovare.",
        ]
    if prima["figlio"] == VUOTO:
        return 3, "non lo so", [
            "il figlio «%s» dell'inquilino non c'era nemmeno PRIMA del distacco:"
            % NOME_FIGLIO,
            "la sessione non e' partita davvero.  ⛔ E una sessione che non e'",
            "partita non puo' ne' perdersi ne' ritrovarsi.",
        ]
    if prima["frazione"] is None:
        return 3, "non lo so", [
            "non ho potuto guardare l'immagine PRIMA del distacco (nessun",
            "fotogramma dal filo, o immagine illeggibile).",
            "⛔ E «non ho guardato» non e' «lo schermo era vuoto».",
        ]
    # ⭐⭐⭐ LA GUARDIA CHE TIENE IN PIEDI TUTTO (vedi in testa): due zeri sono
    #      uguali, e «stessa frazione» sarebbe VERDE su una prova che non ha
    #      mai visto niente.
    if prima["frazione"] < frazione_minima:
        return 3, "non lo so", [
            "⛔ LA SCENA NON SI VEDEVA NEMMENO PRIMA DEL DISTACCO: copre il",
            "   %.1f%% dello schermo e ne servirebbe almeno il %.0f%%."
            % (prima["frazione"] * 100, frazione_minima * 100),
            "   L'immagine di prima e': «%s»." % (prima["verdetto"] or "?"),
            "⇒ Non posso chiedere se una scena si RITROVA se non c'era.",
            "⛔ E questo NON e' un rosso di C6: e' un difetto A MONTE — un",
            "   desktop «nero» o «quasi-nero» e' la nascita in ritardo",
            "   (§7-bis.13), un desktop «disegnato» senza il colore della scena",
            "   e' il browser che non ha aperto la finestra.",
        ]

    # ═══════════════════════════════════════════════════════════════════════
    # IL RIATTACCO — ⭐ da qui in poi si GIUDICA
    # ═══════════════════════════════════════════════════════════════════════
    if dopo["ammesso"] is None:
        return 3, "non lo so", [
            "il cliente del RIATTACCO non e' tornato: si e' piantato lui.",
            "⛔ E' un guasto del BANCO, non del prodotto (`LEZIONI.md` §1.51).",
        ]
    if dopo["ammesso"] is False:
        return 1, "non si rientra", [
            "⛔ il RIATTACCO e' stato RIFIUTATO, e la stessa parola era buona",
            "   un minuto fa, sulla stessa porta e con lo stesso inquilino.",
            "⇒ «si stacca e si ritrova» fallisce prima ancora dei pixel: chi si",
            "  stacca non riesce piu' a rientrare.",
        ]

    # ⚠ La meta' «stessa sessione».  ⛔ `None` non e' «non c'e'»: se non ho
    #   potuto leggere i processi, quella meta' resta MUTA — e una meta' muta
    #   non puo' produrre un verde (§1.47).
    muta_sessione = False
    if dopo["figlio"] is None:
        muta_sessione = True
    elif dopo["figlio"] == VUOTO:
        return 1, "la sessione non c'e' piu'", [
            "dopo il riattacco l'inquilino non ha piu' nessun figlio «%s»."
            % NOME_FIGLIO,
            "⛔ Non ha ritrovato la sua sessione: non ce n'e' nessuna.",
        ]
    elif dopo["figlio"] != prima["figlio"]:
        return 1, "un'altra sessione", [
            "il figlio e' CAMBIATO fra i due attacchi: %s ⇒ %s"
            % (prima["figlio"], dopo["figlio"]),
            "⛔ Chi si e' riattaccato ha trovato una sessione NUOVA, non la sua:",
            "   quel che aveva aperto non c'e' in nessun posto.",
        ]

    if dopo["frazione"] is None:
        return 3, "non lo so", [
            "non ho potuto guardare l'immagine DOPO il riattacco (nessun",
            "fotogramma dal filo, o immagine illeggibile).",
            "⚠ E qui C6 e' piu' prudente di quanto potrebbe: «nessun fotogramma",
            "  dopo il riattacco» potrebbe essere il palco perso, ⛔ ma potrebbe",
            "  essere il filo — e non ho un modo di separarli.  ⇒ Dico «non lo",
            "  so» e nomino il dubbio, invece di scegliere il rosso che mi",
            "  farebbe comodo.",
        ]

    if dopo["frazione"] < frazione_minima:
        degenere = dopo["verdetto"] in ("nero", "quasi-nero")
        if degenere:
            return 1, "il palco non si ritrova", [
                "dopo il riattacco lo schermo e' «%s»: la scena copriva il"
                % dopo["verdetto"],
                "%.1f%% ⇒ %.1f%%." % (prima["frazione"] * 100,
                                      dopo["frazione"] * 100),
                "⛔ Non e' «la finestra si e' chiusa»: non c'e' piu' NIENTE da",
                "   vedere.  ⇒ E' il palco che il distacco si e' portato via —",
                "   cioe' I4 rotta dal lato dell'utente.",
            ]
        return 1, "le finestre non si ritrovano", [
            "dopo il riattacco il desktop e' «%s» — c'e' uno schermo — ⛔ ma la"
            % (dopo["verdetto"] or "?"),
            "scena non c'e' piu': copriva il %.1f%% e adesso copre il %.1f%%."
            % (prima["frazione"] * 100, dopo["frazione"] * 100),
            "⇒ La sessione si e' ritrovata, le FINESTRE no.",
        ]

    scarto = abs(dopo["frazione"] - prima["frazione"])
    if scarto > scarto_massimo:
        return 1, "la scena e' cambiata", [
            "la scena c'e' ancora, ⛔ ma non e' quella: copriva il %.1f%% e"
            % (prima["frazione"] * 100),
            "adesso copre il %.1f%% (scarto %.3f, il massimo ammesso e' %.3f)."
            % (dopo["frazione"] * 100, scarto, scarto_massimo),
            "⚠ E' il rosso piu' mite dei cinque: qualcosa si e' ritrovato, ma",
            "  non tutto.  ⇒ Se questo scattasse su un prodotto sano, il numero",
            "  da tarare e' `--scarto-massimo`, e va tarato con una misura",
            "  sotto — non allargato finche' tace.",
        ]

    if muta_sessione:
        return 3, "non lo so", [
            "⭐ l'immagine regge: la scena si e' ritrovata (%.1f%% ⇒ %.1f%%,"
            % (prima["frazione"] * 100, dopo["frazione"] * 100),
            "   scarto %.3f).  ⛔ MA non ho potuto leggere i processi dopo il" % scarto,
            "   riattacco ⇒ non so se e' la STESSA sessione o una nuova che le",
            "   somiglia.",
            "⇒ Mezzo giudizio non e' un verde (`LEZIONI.md` §1.47).",
        ]

    return 0, "si ritrova", [
        "il cliente si e' staccato, ha aspettato, si e' riattaccato,",
        "⭐ e ha ritrovato la STESSA sessione (figlio %s) e la STESSA scena"
        % prima["figlio"],
        "  (%.1f%% ⇒ %.1f%%, scarto %.3f ≤ %.3f)"
        % (prima["frazione"] * 100, dopo["frazione"] * 100, scarto,
           scarto_massimo),
    ]


def guasto_morso(prima, dopo):
    """⛔⛔ §1.52 — col guasto innestato non basta il COLORE del verdetto.

    ⭐ C6 porta con se' un difetto vero e gia' noto (il palco che muore col
      distacco), e con quello e' rossa **anche senza** iniezione.  ⇒ Un semplice
      *«rosso ⇒ visto»* direbbe «il guasto e' stato visto» anche se l'iniezione
      non avesse fatto niente: un predicato che non puo' fallire (§1.44), e
      stavolta a reggere la certificazione di tutta la rete (C13).

    ⇒ Il morso si misura sulla **DIFFERENZA** che l'iniezione ha prodotto, ed e'
      il **PID DEL FIGLIO**:

        palco perso (difetto del prodotto)  il figlio e' LO STESSO
        sessione uccisa (l'iniezione)       ⛔ il figlio non c'e' piu', o e' un
                                            pid diverso

    ⛔ E se non ho potuto leggere i processi — prima o dopo — non e' «visto»:
       «non lo so» non e' una prova che il guasto abbia morso.
    """
    p = prima.get("figlio")
    d = dopo.get("figlio")
    if p in (None, VUOTO):
        return False
    if d is None:
        return False
    return d != p


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LA CERTIFICAZIONE — casi sintetici, e ⭐ deve girare SUL PORTATILE
# ═══════════════════════════════════════════════════════════════════════════
def certifica(frazione_minima=None, scarto=SCARTO_MASSIMO):
    """⛔ Si dimostra che il giudice sa dire verde, rosso e «non lo so».

    ⚠ E si dichiara che cosa copre e che cosa no.
      COPRE: la **decisione** (le guardie e il confronto fra le due
      osservazioni), la lettura del **morso** del guasto innestato, e ⭐ che il
      lettore del colore importato da C8 sia DAVVERO vivo — un'immagine
      sintetica ci passa dentro e si guarda che numero ne esce.
      ⛔ NON COPRE: che il browser apra davvero la finestra, che il palco si
      rimonti, che i fotogrammi arrivino.  Quella meta' la dice solo il giro
      vero dentro la scatola, ed e' il collaudo `--uccidi-la-sessione`.
    ⇒ Una certificazione che si dichiara piu' larga di quel che e' vale meno di
      nessuna certificazione (la regola di C1).
    """
    c8 = lettore_del_colore()
    if c8 is None:
        print("⛔ non trovo C8 accanto a me: il lettore del colore e' SUO e non")
        print("   lo riscrivo qui.  ⇒ non ho potuto guardare")
        return 3
    if frazione_minima is None:
        frazione_minima = c8.FRAZIONE_MINIMA

    fm = frazione_minima
    print("== certificazione del giudice di C6 ==")
    print("   ⛔ copre la DECISIONE e il lettore importato, non il giro vero")
    print("   metro: colore %s ±%d per canale (da C8) · almeno il %.0f%% dello"
          % (c8.COLORE, c8.TOLLERANZA, fm * 100))
    print("          schermo · scarto massimo fra prima e dopo %.3f" % scarto)
    print("   pausa: %.0f s = 2 × la sopravvivenza misurata (%.0f s)\n"
          % (PAUSA_PREDEFINITA_S, SOPRAVVIVENZA_MISURATA_S))

    # Le due osservazioni «sane», da cui si deriva ogni caso cambiando una cosa
    # sola — ⭐ §3.3 del documento di fase: si muove una cosa per volta.
    def viva(**c):
        d = osservazione(ammesso=True, figlio="12113", frazione=0.62,
                         verdetto="disegnato", fotogrammi=180)
        d.update(c)
        return d

    casi = [
        # ── il giro sano ────────────────────────────────────────────────────
        ("⭐ si stacca e si ritrova: stessa sessione, stessa scena",
         dict(prima=viva(), dopo=viva()), (0, "si ritrova")),

        ("⭐ la scena si e' spostata di poco ⇒ dev'essere VERDE",
         dict(prima=viva(), dopo=viva(frazione=0.62 - scarto + 0.02)),
         (0, "si ritrova")),

        # ── i rossi, uno per specie ─────────────────────────────────────────
        ("⛔⛔ IL DIFETTO DI OGGI: stesso figlio, ⛔ finestre sparite",
         dict(prima=viva(), dopo=viva(frazione=0.001, verdetto="disegnato")),
         (1, "le finestre non si ritrovano")),

        ("⛔⛔ …e se lo schermo e' tornato NERO e' un'altra specie di rosso",
         dict(prima=viva(), dopo=viva(frazione=0.0, verdetto="nero")),
         (1, "il palco non si ritrova")),

        ("⛔ «quasi-nero» conta come nero: c'e' la barra e nient'altro",
         dict(prima=viva(), dopo=viva(frazione=0.0, verdetto="quasi-nero")),
         (1, "il palco non si ritrova")),

        ("⛔ IL GUASTO INNESTATO: la sessione e' stata uccisa ⇒ figlio diverso",
         dict(prima=viva(), dopo=viva(figlio="20044", frazione=0.0,
                                      verdetto="nero")),
         (1, "un'altra sessione")),

        ("⛔ …e se dopo il riattacco non c'e' proprio nessun figlio",
         dict(prima=viva(), dopo=viva(figlio=VUOTO, frazione=0.0,
                                      verdetto="nero")),
         (1, "la sessione non c'e' piu'")),

        ("⛔ il riattacco viene RIFIUTATO, con la parola di un minuto fa",
         dict(prima=viva(), dopo=viva(ammesso=False)), (1, "non si rientra")),

        ("⛔ la scena c'e' ma e' cambiata TROPPO ⇒ rosso mite",
         dict(prima=viva(), dopo=viva(frazione=0.62 - scarto - 0.05)),
         (1, "la scena e' cambiata")),

        # ═══════════════════════════════════════════════════════════════════
        # ⭐⭐⭐ I CASI PER CUI QUESTA MAGLIA ESISTE — ⛔ «due zeri sono uguali»
        #
        # ⚠ Senza la guardia del «prima», il primo di questi tre risponderebbe
        #   (0, «si ritrova»): la stessa frazione, lo stesso figlio, nessuna
        #   differenza da nessuna parte.  ⛔ E sarebbe la maglia piu'
        #   compiacente della rete, in silenzio.
        # ═══════════════════════════════════════════════════════════════════
        ("⭐⭐ la scena non c'era NEMMENO PRIMA (0 ⇒ 0) ⇒ ⛔ MAI verde",
         dict(prima=viva(frazione=0.0, verdetto="nero"),
              dopo=viva(frazione=0.0, verdetto="nero")), (3, "non lo so")),

        ("⭐⭐ …e nemmeno se DOPO la scena comparisse per caso",
         dict(prima=viva(frazione=0.0, verdetto="nero"), dopo=viva()),
         (3, "non lo so")),

        ("⭐ la scena c'era ma sotto la soglia (5%) ⇒ non ho guardato niente",
         dict(prima=viva(frazione=0.05), dopo=viva(frazione=0.05)),
         (3, "non lo so")),

        # ── i «non lo so» del banco ─────────────────────────────────────────
        ("⛔ il PRIMO attacco non e' stato ammesso ⇒ non lo so, non un rosso",
         dict(prima=viva(ammesso=False), dopo=viva()), (3, "non lo so")),

        ("⛔ il figlio non e' mai nato PRIMA ⇒ non c'e' niente da ritrovare",
         dict(prima=viva(figlio=VUOTO), dopo=viva()), (3, "non lo so")),

        ("⛔ i processi non si sono fatti leggere PRIMA ⇒ non lo so",
         dict(prima=viva(figlio=None), dopo=viva()), (3, "non lo so")),

        ("⛔ nessun fotogramma PRIMA ⇒ non lo so, ⛔ non «schermo vuoto»",
         dict(prima=viva(frazione=None, verdetto=None), dopo=viva()),
         (3, "non lo so")),

        ("⛔ nessun fotogramma DOPO ⇒ non lo so, e il dubbio si NOMINA",
         dict(prima=viva(), dopo=viva(frazione=None, verdetto=None)),
         (3, "non lo so")),

        ("⛔ il cliente del riattacco si e' piantato ⇒ guasto del BANCO",
         dict(prima=viva(), dopo=viva(ammesso=None)), (3, "non lo so")),

        # ⛔ §1.47: l'immagine regge ma la meta' «stessa sessione» e' MUTA.
        ("⛔ scena ritrovata, ⛔ ma non so se e' la stessa sessione ⇒ non lo so",
         dict(prima=viva(), dopo=viva(figlio=None)), (3, "non lo so")),
    ]

    guai = 0
    for nome, arg, atteso in casi:
        esito, specie, _m = giudica(frazione_minima=fm, scarto_massimo=scarto,
                                    **arg)
        ok = (esito, specie) == atteso
        print("  %s  %-62s  esito=%s (%s)   atteso %s (%s)"
              % ("OK " if ok else "NO ", nome, esito, specie,
                 atteso[0], atteso[1]))
        if not ok:
            guai += 1

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ LA SECONDA META' — «il guasto ha morso?» non e' «il verdetto e'
    #     rosso?» (§1.52).  ⛔ Per C6 e' la parte che vale di piu': la maglia
    #     puo' essere gia' rossa per conto suo.
    # ═══════════════════════════════════════════════════════════════════════
    casi_morso = [
        ("⭐ la sessione uccisa: il figlio e' un altro ⇒ VISTO",
         dict(prima=viva(), dopo=viva(figlio="20044")), True),

        ("⭐ la sessione uccisa e nessun figlio e' rinato ⇒ VISTO",
         dict(prima=viva(), dopo=viva(figlio=VUOTO)), True),

        ("⛔⛔ ROSSO col figlio LO STESSO: e' il difetto del PALCO, ⛔ non il",
         dict(prima=viva(), dopo=viva(frazione=0.0, verdetto="nero")), False),

        ("⛔ non ho potuto leggere i processi DOPO ⇒ NON e' «visto»",
         dict(prima=viva(), dopo=viva(figlio=None)), False),

        ("⛔ non li avevo letti nemmeno PRIMA ⇒ NON e' «visto»",
         dict(prima=viva(figlio=None), dopo=viva(figlio="20044")), False),

        ("⛔ il figlio non c'era gia' prima ⇒ NON e' «visto»",
         dict(prima=viva(figlio=VUOTO), dopo=viva(figlio=VUOTO)), False),
    ]
    print()
    print("   ⛔ e il guasto innestato si legge sulla DIFFERENZA (il PID del")
    print("      figlio), non sul colore del verdetto — `LEZIONI.md` §1.52:")
    for nome, arg, atteso in casi_morso:
        avuto = guasto_morso(**arg)
        ok = avuto is atteso
        print("  %s  %-62s  morso=%-5s  atteso %s"
              % ("OK " if ok else "NO ", nome, avuto, atteso))
        if not ok:
            guai += 1

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐ LA TERZA META' — il LETTORE importato da C8 e' davvero vivo?
    #
    # ⛔ Un giudice importato che non funziona ha esattamente l'aspetto di un
    #    giudice che non e' stato chiamato: `LEZIONI.md` §1.46.  ⇒ Gli si fa
    #    passare dentro un'immagine sintetica e si guarda che numero ne esce.
    # ⚠ La TARATURA del lettore (colore spostato, tolleranza) NON si rifa' qui:
    #   e' nella certificazione di C8, e duplicarla vorrebbe dire due tarature
    #   che possono divergere.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    print("   ⭐ e il lettore del colore e' quello di C8, importato: gli faccio")
    print("      passare dentro tre immagini per essere sicuro che sia vivo")
    try:
        import numpy as np
        from PIL import Image
        import tempfile
        lav = tempfile.mkdtemp(prefix="c6cert-")

        def dipingi(nome, riempi):
            a = np.zeros((216, 384, 3), dtype="uint8")
            a[:, :] = riempi
            p = os.path.join(lav, nome + ".png")
            Image.fromarray(a).save(p)
            return p

        prove = [
            ("la scena riempie lo schermo", dipingi("a", c8.COLORE), True),
            ("un desktop senza la scena", dipingi("b", (58, 62, 70)), False),
            ("un file che non c'e' ⇒ «non lo so», ⛔ non zero",
             os.path.join(lav, "manca.png"), None),
        ]
        for nome, png, atteso in prove:
            fr = c8.frazione_del_colore(png)
            if atteso is None:
                ok = fr is None
                detto = "non lo so" if fr is None else "%.3f" % fr
            else:
                ok = fr is not None and ((fr >= fm) == atteso)
                detto = "non lo so" if fr is None else "%.3f" % fr
            print("  %s  %-62s  frazione=%s"
                  % ("OK " if ok else "NO ", nome, detto))
            if not ok:
                guai += 1
    except ImportError:
        print("  ⛔  mancano numpy o Pillow: NON ho potuto provare il lettore")
        print("      ⇒ e questa certificazione e' incompleta, non riuscita")
        return 3

    # ⭐⭐ I CASI DELL'AMMISSIONE — ⛔ quelli che oggi non c'erano.
    #    Il predicato vive in C1 e si certifica coi casi di C1: ⛔ una copia
    #    dei casi qui sarebbe un secondo posto da cui divergere (§1.47).
    print()
    guai_amm, quanti_amm = casa_dell_ammissione().certifica_ammissione("C6")
    guai += guai_amm

    # ⭐⭐ E I CASI DEI GRUPPI DELLA SCHEDA — ⛔ l'altro caso che non c'era:
    #    un inquilino senza i gruppi dei nodi ⇒ «non ho potuto guardare», ⛔
    #    mai rosso.  Vivono in C1 col passo che certificano.
    print()
    guai_gr, quanti_gr = casa_dell_ammissione().certifica_gruppi("C6")
    guai += guai_gr

    quanti = len(casi) + len(casi_morso) + quanti_amm + quanti_gr + 3
    print()
    if guai:
        print("⛔ il giudice NON e' affidabile: %d casi su %d sbagliati"
              % (guai, quanti))
        return 1
    print("⭐ %d casi su %d: il giudice vede la scena quando si ritrova, la"
          % (quanti, quanti))
    print("   vede sparire quando sparisce, ⛔ NON dice verde quando la scena")
    print("   non c'era nemmeno prima, e ⭐ distingue «il guasto ha morso» da")
    print("   «era gia' rosso per conto suo».")
    print("⚠ e copre la DECISIONE, non il giro vero (vedi in testa)")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# IL MONDO — raccogliere i fatti.  ⛔ Da qui in giu' si TOCCA la macchina.
# ═══════════════════════════════════════════════════════════════════════════
def sh(comando, secondi=120):
    """⚠ Un guscio si usa solo dove serve davvero (`useradd`, `su`, `runuser`):
       `LEZIONI.md` §1.46 — ogni livello di virgolette e' un posto dove il
       comando puo' sparire."""
    try:
        return subprocess.run(["/bin/sh", "-c", comando],
                              capture_output=True, text=True, timeout=secondi)
    except subprocess.SubprocessError:
        return subprocess.CompletedProcess([], 127, "", "scaduto")


def corri(argv, tempo=60):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=tempo)
        return p.returncode, (p.stdout or "")
    except (OSError, subprocess.SubprocessError):
        return None, ""


def uid_di(chi):
    import pwd
    try:
        return pwd.getpwnam(chi).pw_uid
    except KeyError:
        return None


def figlio_di(uid):
    """Il pid del figlio «remotix» dell'inquilino.

    ⛔ Tre esiti e non due: `None` = «/proc non si e' fatto leggere», `VUOTO` =
       «ho guardato e non c'e'», altrimenti il pid (o i pid, separati).
    ⚠ Si legge `/proc` invece di chiamare `ps`: un guscio in meno, e la stessa
      scelta di C7.
    """
    try:
        elenco = os.listdir("/proc")
    except OSError:
        return None
    pid = []
    for voce in elenco:
        if not voce.isdigit():
            continue
        try:
            if os.stat("/proc/%s" % voce).st_uid != uid:
                continue
            with open("/proc/%s/comm" % voce) as f:
                nome = f.read().strip()
        except OSError:
            continue
        if nome == NOME_FIGLIO:
            pid.append(voce)
    if not pid:
        return VUOTO
    return " · ".join(sorted(pid, key=int))


def socket_wayland(uid):
    """Il socket del compositore dell'inquilino, o `None`.

    ⛔ Il nome si CERCA, non si indovina: inchiodare `wayland-0` vorrebbe dire
       una prova che funziona su un desktop e tace sugli altri — il difetto che
       questa fase esiste per non introdurre (la stessa scelta di C8).
    """
    try:
        voci = sorted(os.listdir("/run/user/%d" % uid))
    except OSError:
        return None
    for v in voci:
        if re.match(r"^wayland-[0-9]+$", v):
            return v
    return None


def aspetta(predicato, tetto, passo=1.0):
    """⭐ Si aspetta l'EVENTO, non l'orologio (`LEZIONI.md` §1.49).

    Torna `(valore, secondi)`; `valore` e' `None` se il tetto e' scaduto — e
    allora ⛔ chi chiama deve dire «non lo so», non tirare avanti fingendo.
    """
    partenza = time.time()
    scadenza = partenza + tetto
    while time.time() < scadenza:
        v = predicato()
        if v:
            return v, time.time() - partenza
        time.sleep(passo)
    return None, time.time() - partenza


# ---------------------------------------------------------------------------
# L'ATTACCO — il cliente di prova, e l'immagine che ne esce
# ---------------------------------------------------------------------------
def leggi(percorso):
    try:
        with open(percorso, "r", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def attacca(chi, a, resta, diario, video=None):
    """Lancia il cliente IN SOTTOFONDO e torna `(processo, presa_del_diario)`.

    ⛔ In sottofondo e non bloccante, e la ragione e' tutta la maglia: la scena
       va aperta **mentre un cliente e' attaccato**.  `[M]` (la misura del 27
       agosto in testa) il `wl_output` nasce solo quando un consumatore si
       aggancia ⇒ aprire una finestra a filo staccato vorrebbe dire aprirla su
       un desktop che non ha nessuno schermo, e poi accusare il prodotto di non
       avercela ritrovata.

    ⛔⛔ E QUEL CHE DICE FINISCE IN UN FILE, non in una `PIPE` — ⚠ e questa riga
        vale piu' di quel che sembra.  Con `stdout=PIPE` nessuno legge il tubo
        finche' il banco dorme (e qui dorme quasi un minuto, aspettando la
        scena): il tubo si riempie, ⛔ **il cliente si blocca sulla scrittura**,
        e il banco lo vedrebbe come «il prodotto non manda piu' niente».
        ⇒ Un guasto del BANCO con la faccia di un guasto del prodotto, che e'
          la famiglia §1.51.
    ⭐ E in piu' il diario resta sul disco per chi diagnostica, invece di
      sparire dentro una variabile.
    """
    argv = ["python3", "-u", a.cliente,
            "--indirizzo", a.indirizzo, "--porta", str(a.porta),
            "--utente", chi, "--parola", a.parola,
            "--resta", str(resta)]
    if video:
        if os.path.exists(video):
            os.unlink(video)
        argv += ["--video-scrivi", video]
    presa = open(diario, "w")
    return subprocess.Popen(argv, stdout=presa, stderr=subprocess.STDOUT,
                            text=True), presa


def raccogli_il_cliente(proc, presa, diario, tetto):
    """Aspetta che il cliente finisca.  Torna `(ammesso, fotogrammi, coda)`.

    ⛔ `ammesso` ha TRE stati: `True`, `False`, e `None` = «il cliente non e'
       tornato», che e' un guasto del BANCO e non del prodotto (§1.51).
    """
    scaduto = False
    try:
        proc.wait(timeout=tetto)
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            proc.wait(timeout=30)
        except subprocess.SubprocessError:
            pass
        scaduto = True
    try:
        presa.close()
    except OSError:
        pass
    coda = leggi(diario)
    if scaduto:
        return None, None, ("il cliente di prova non e' tornato entro il "
                            "tetto\n" + coda)
    # ⛔ NON `"AMMESSO" in coda`: la parola c'e' anche nei due rifiuti, e ci
    #    arriva sullo stdout — vedi `e_stato_ammesso()` in testa.  ⭐ E cosi'
    #    il terzo stato promesso dal docstring qui sopra esiste davvero.
    ammesso = e_stato_ammesso(coda)
    # ⚠ Il conto dei fotogrammi si legge dalla riga `[vid]` del cliente, come
    #   fa C8: e' un'informazione, ⛔ non un verdetto.
    quanti = None
    for riga in coda.splitlines():
        if "[vid]" in riga and "nessun fotogramma" not in riga:
            try:
                quanti = int(riga.split("[vid]", 1)[1].strip().split()[0])
            except (ValueError, IndexError):
                pass
    return ammesso, quanti, coda


def immagine_dal_flusso(flusso, fuori):
    """L'ULTIMO fotogramma del flusso, in PNG.  `None` se non se n'e' fatto uno.

    ⛔ `-update 1` tiene l'ULTIMO: e' quel che il desktop mostra adesso.  Il
       primo sarebbe la chiave d'apertura, cioe' un minuto fa — e per una maglia
       che chiede *«che cosa vedo QUANDO torno»* sarebbe la domanda sbagliata.
    """
    if os.path.exists(fuori):
        os.unlink(fuori)
    if not os.path.exists(flusso) or os.path.getsize(flusso) == 0:
        return None
    sh("ffmpeg -hide_banner -loglevel error -i %s -vsync 0 -update 1 -y %s"
       % (flusso, fuori), secondi=240)
    if os.path.exists(fuori) and os.path.getsize(fuori):
        return fuori
    return None


# ---------------------------------------------------------------------------
# LA SCENA — ⭐ la finestra che dev'essere ritrovata
# ---------------------------------------------------------------------------
def apri_la_scena(chi, a):
    """Accende il browser a tutto schermo sulla pagina del colore dichiarato.

    ⛔ Il socket di Wayland si CERCA (vedi `socket_wayland`).
    ⚠ Il registro del browser finisce in casa SUA: `[M]` C8, 26 ago 2026 — la
      cartella di lavoro del banco e' di `root` a modo 0755 e il browser gira
      da utente, e un file che non si puo' scrivere diventava «il browser non
      ha disegnato», cioe' ⛔ il banco che dava rosso a se stesso.
    """
    uid = uid_di(chi)
    if uid is None:
        return None, "non so l'uid di «%s»" % chi
    display = socket_wayland(uid)
    if not display:
        return None, ("in /run/user/%d non c'e' nessun socket wayland: la "
                      "sessione non ha un compositore a cui il browser possa "
                      "parlare" % uid)
    sh("runuser -u %s -- env XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=%s "
       "MOZ_ENABLE_WAYLAND=1 XDG_SESSION_TYPE=wayland HOME=/home/%s "
       "%s --kiosk file://%s > /home/%s/.c6-scena.log 2>&1 &"
       % (chi, uid, display, chi, a.browser, a.pagina, chi), secondi=30)
    return display, None


def profilo_del_browser(chi):
    """⭐ L'EVENTO «il browser e' partito»: il suo profilo esiste.

    ⛔ Non e' «la finestra si vede» — quello lo dice solo il pixel, ed e' il
       giudizio.  ⚠ Ma e' meglio di un'attesa cieca: separa «il browser non e'
       partito affatto» da «e' partito e ci mette».
    """
    r = sh("ls -d /home/%s/.cache/mozilla/firefox/*/ 2>/dev/null | head -1" % chi)
    return r.stdout.strip() or None


def scalda_il_browser(chi, a, fuori):
    """⭐⭐ IL PRIMO AVVIO SI FA FUORI DALLA SESSIONE, e serve a DUE cose.

    1. ⛔ **Scalda il profilo.**  `LEZIONI.md` §1.45: il primo avvio di Firefox
       in una scatola fredda passa abbondantemente i 25 s, perche' deve crearsi
       il profilo.  ⇒ Se quel primo avvio capitasse DENTRO la sessione, l'attesa
       della scena dovrebbe essere lunghissima, e ogni rosso di C6 sarebbe
       indistinguibile dal proprio tetto — che e' esattamente il difetto per cui
       C8 dava rosso a tutt'e due gli inquilini.

    2. ⭐ **E' una GUARDIA.**  Se in questa scatola il browser non riesce a
       disegnare la pagina nemmeno da solo, la domanda di C6 non e' ponibile:
       ⛔ non e' un rosso del prodotto, e' una scatola senza scena.  `[M]` C8,
       26 ago 2026: senza `libpci3` Firefox non produceva nessuna immagine, e il
       banco lo leggeva come un guasto del prodotto.

    ⚠ E il tetto e' SUO (`--attesa-scena`), non prestato da un'altra attesa
      (§1.45).  ⛔ E si giudica il FILE, non il codice d'uscita: `[M]` §1.50 —
      con un tetto stretto Firefox esce 124 e **il PNG c'e' lo stesso**.
    """
    if os.path.exists(fuori):
        os.unlink(fuori)
    suo = "/home/%s/.c6-scaldata.png" % chi
    sh("rm -f %s" % suo)
    r = sh("runuser -u %s -- env HOME=/home/%s MOZ_HEADLESS=1 "
           "timeout %d %s --headless --screenshot %s file://%s"
           % (chi, chi, int(a.attesa_scena), a.browser, suo, a.pagina),
           secondi=int(a.attesa_scena) + 60)
    if os.path.exists(suo) and os.path.getsize(suo):
        sh("cp -f %s %s" % (suo, fuori))
    detto = ((r.stdout or "") + (r.stderr or "")).strip()
    if os.path.exists(fuori) and os.path.getsize(fuori):
        return fuori, detto[-160:]
    return None, detto[-160:]


# ---------------------------------------------------------------------------
# L'INQUILINO — si crea nuovo, e ⛔ si cancella PRIMA di crearlo
# ---------------------------------------------------------------------------
def sgombera(chi, cancella=True):
    """⭐ Lo sgombero del BANCO, che ⛔ non e' la prova.

    Si chiude l'inquilino di QUESTO giro **per nome**, mai un modello globale
    (fase 10 §7.3, dove un `pkill -f` globale ha rischiato di uccidere il lavoro
    di un'altra prova in corso).  ⚠ E si fa in un `finally`: un banco che lascia
    i suoi avanzi rende rosso il banco dopo, e quel rosso non e' del prodotto.
    """
    corri(["loginctl", "terminate-user", chi], tempo=60)
    time.sleep(1.0)
    corri(["pkill", "-KILL", "-u", chi], tempo=60)
    time.sleep(0.5)
    if cancella:
        corri(["userdel", "-r", chi], tempo=120)
        corri(["rm", "-rf", "/home/%s" % chi], tempo=60)


def crea(chi, parola):
    """Crea l'inquilino **come lo crea il prodotto**: `useradd -m`, la parola,
       ⭐ e i gruppi della scheda LETTI DAI NODI e riletti.

    ⛔ Fino al 27 agosto 2026 qui c'era `usermod -aG video,render`: due nomi
       inchiodati (che sono di UNA distribuzione) e nessuna verifica.  ⭐ `[M]`
       senza i gruppi dei nodi `/dev/dri` la sessione nasce CIECA — 0 su 4,
       zero fotogrammi — e C6 avrebbe detto «la scena non si ritrova»
       accusando il prodotto di un guasto del banco (§1.51).
    """
    r = sh("useradd -m -s /bin/bash %s && "
           "printf '%s:%s\n' | chpasswd" % (chi, chi, parola))
    if r.returncode != 0:
        return False, ((r.stderr or "") + (r.stdout or "")).strip()[:140]
    e_gr, perche_gr = garantisci_i_gruppi(chi, prefisso="      ")
    if e_gr != 0:
        return False, perche_gr
    return True, ""


def togli_di_mezzo_il_difetto_di_c8(chi, c8):
    """⚠ C6 NON prova il difetto della provvista: lo TOGLIE DI MEZZO.

    ⛔ E la ragione e' un pericolo vero fra banchi: `11-c8` prepara il terreno
       facendo di `/etc/skel/.cache` un collegamento a `/tmp`, e **non lo
       disfa**.  ⇒ Se C8 ha girato prima di C6 in questa scatola, l'inquilino di
       C6 nascerebbe con `~/.cache` condivisa, e se `/tmp/mozilla` fosse di un
       inquilino di C8 il browser di C6 non farebbe il profilo.
    ⚠ Allora C6 direbbe *«la scena non si vedeva nemmeno prima»* — un «non lo
      so» perfettamente onesto, ⛔ ma per un difetto che non e' suo e che un
      giorno di taratura non troverebbe.
    ⇒ Si applica la cura di `src/provisiona.sh` all'inquilino di C6, ed e' la
      STESSA riga di C8, importata invece che riscritta.
    """
    c8.applica_la_cura(chi)


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--utente", default="c6u1",
                   help="l'inquilino di prova: si crea NUOVO e si cancella")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=8511)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--pagina", default=os.path.join(QUI, "11-c8-pagina.html"),
                   help="la pagina della scena: e' quella di C8, e il colore "
                        "lo dichiara C8")
    p.add_argument("--browser", default="firefox-esr")
    p.add_argument("--lavoro", default="/var/lib/rete11/c6")

    # ── LE ATTESE.  ⛔ Ognuna ha un NOME suo e un VALORE suo (`LEZIONI.md`
    #    §1.45): riusare un tetto perche' «e' li' e piu' o meno va bene» e' il
    #    modo esatto in cui un rosso smette di distinguere il guasto dal banco.
    p.add_argument("--resta-nascita", type=float, default=30.0,
                   help="quanto sta attaccato il cliente che fa NASCERE la "
                        "sessione. ⚠ Non gli si chiede nessun fotogramma")
    p.add_argument("--attesa-ammissione", type=float, default=60.0,
                   help="quanto si aspetta che il diario del cliente dica "
                        "AMMESSO. ⭐ E' un EVENTO, non un'attesa cieca")
    p.add_argument("--aggancio", type=float, default=5.0,
                   help="quanto si da' al consumatore per agganciarsi al flusso "
                        "DOPO l'ammissione. `[M]` il wl_output nasce 65÷93 ms "
                        "dopo l'aggancio: 5 s e' larghissimo apposta, ed e' "
                        "l'unico punto in cui questo tempo si spende")
    p.add_argument("--coda-scatto", type=float, default=10.0,
                   help="quanto il cliente resta attaccato DOPO la posa della "
                        "scena. ⛔ Serve perche' la foto e' l'ULTIMO fotogramma: "
                        "senza coda l'ultimo sarebbe quello di mezzo secondo "
                        "prima che la finestra fosse a posto")
    p.add_argument("--attesa-compositore", type=float, default=240.0,
                   help="quanto si aspetta che compaia il socket wayland "
                        "dell'inquilino. ⛔ Su GNOME `[M]` 101,0 s (C1, 27 ago "
                        "2026, massimo su tre sessioni), e c'e' un difetto "
                        "della SCATOLA (polkit, ~97 s) in cura proprio adesso: "
                        "⇒ il valore e' largo APPOSTA e va ritarato quando la "
                        "cura e' misurata")
    p.add_argument("--attesa-figlio", type=float, default=90.0,
                   help="quanto si aspetta che il figlio «%s» compaia fra i "
                        "processi dell'inquilino. Scaduto: «non lo so»"
                        % NOME_FIGLIO)
    p.add_argument("--attesa-scena", type=float, default=180.0,
                   help="quanto si da' al browser per crearsi il profilo e "
                        "disegnare la pagina FUORI dalla sessione (la "
                        "scaldata). ⛔ Largo: `LEZIONI.md` §1.45, il primo "
                        "avvio in una scatola fredda passa i 25 s")
    p.add_argument("--posa-scena", type=float, default=40.0,
                   help="quanto si da' alla finestra per comparire nell'immagine "
                        "DENTRO la sessione, dopo che il profilo c'e' gia'. "
                        "`[?]` non misurato: valore prudente, da tarare")
    p.add_argument("--resta-prima", type=float, default=75.0,
                   help="quanto sta attaccato il cliente che scatta la foto "
                        "PRIMA. ⚠ Dev'essere piu' lungo di --posa-scena, o la "
                        "foto arriva prima della finestra")
    p.add_argument("--pausa-staccato", type=float, default=PAUSA_PREDEFINITA_S,
                   help="⭐⭐ quanto si resta STACCATI. Il predefinito e' il "
                        "DOPPIO della sopravvivenza misurata del monitor "
                        "(`[M]` 15 s): sotto quella soglia si riattaccherebbe "
                        "prima che il palco abbia modo di morire, ⛔ e la "
                        "maglia direbbe verde senza aver provato niente")
    p.add_argument("--resta-dopo", type=float, default=60.0,
                   help="quanto sta attaccato il cliente del RIATTACCO. ⚠ Piu' "
                        "lungo del primo apposta: al riattacco il palco puo' "
                        "doversi rimontare, e una foto troppo presa presto "
                        "direbbe «nero» su un desktop che sta tornando")

    p.add_argument("--scarto-massimo", type=float, default=SCARTO_MASSIMO,
                   help="di quanto la frazione della scena puo' cambiare fra "
                        "prima e dopo e restare «la stessa»")
    p.add_argument("--uccidi-la-sessione", action="store_true",
                   help="⛔ IL GUASTO INNESTATO: fra il distacco e il riattacco "
                        "si chiude la sessione dell'inquilino. Deve dare ROSSO, "
                        "⭐ e il morso si legge sul PID del figlio")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica(scarto=a.scarto_massimo))

    if os.geteuid() != 0:
        print("⛔ va eseguita da amministratore: crea e cancella un inquilino")
        sys.exit(2)
    # ⛔⛔ IL BILANCIO DEL PRIMO ATTACCO SI VERIFICA PRIMA DI COMINCIARE.
    #
    # ⚠ Il cliente «prima» deve stare attaccato per TUTTO: l'ammissione,
    #   l'aggancio del consumatore, la posa della scena, e una coda perche' la
    #   foto e' l'ULTIMO fotogramma.  Se il conto non torna, il cliente finisce
    #   di scrivere il flusso **mentre la finestra sta ancora comparendo** ⇒ la
    #   foto e' di prima della scena, ⛔ C6 dice «la scena non si vedeva nemmeno
    #   PRIMA» e chi legge da' la colpa al prodotto.
    # ⭐ E' §1.45 applicato alla somma invece che al singolo tetto: un tetto
    #   giusto e una somma sbagliata danno lo stesso rosso falso.
    minimo = a.aggancio + a.posa_scena + a.coda_scatto
    if a.resta_prima < minimo:
        print("⛔ --resta-prima e' %.0f s e ne servono almeno %.0f:"
              % (a.resta_prima, minimo))
        print("   aggancio %.0f + posa della scena %.0f + coda %.0f"
              % (a.aggancio, a.posa_scena, a.coda_scatto))
        print("   ⇒ cosi' la foto arriverebbe prima della finestra, e il rosso")
        print("     sarebbe del BANCO, non del prodotto")
        sys.exit(2)

    # ── le cose senza le quali non si giudica ─────────────────────────────
    c8 = lettore_del_colore()
    if c8 is None:
        print("⛔ non trovo C8 accanto a me: il lettore del colore e' SUO e non")
        print("   lo riscrivo qui.  ⇒ non ho potuto guardare")
        sys.exit(3)
    giudice = giudice_immagini()
    if giudice is None:
        print("⛔ non trovo il giudice delle immagini (10-f1-testimone.py)")
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    for che, dove in (("il cliente di prova", a.cliente),
                      ("la pagina della scena", a.pagina)):
        if not os.path.exists(dove):
            print("⛔ non trovo %s: %s" % (che, dove))
            print("   ⇒ non ho potuto guardare")
            sys.exit(3)
    for attrezzo, perche in ((a.browser, "non posso aprire nessuna finestra"),
                             ("ffmpeg", "i fotogrammi non diventano un'immagine")):
        if sh("command -v %s" % attrezzo).returncode != 0:
            print("⛔ nella scatola non c'e' %s: %s" % (attrezzo, perche))
            print("   ⇒ non ho potuto guardare")
            sys.exit(3)

    fm = c8.FRAZIONE_MINIMA
    os.makedirs(a.lavoro, exist_ok=True)
    chi = a.utente

    print("== C6 — si stacca e si ritrova ==")
    print("   inquilino «%s» · porta %d · scena %s"
          % (chi, a.porta, os.path.basename(a.pagina)))
    print("   metro: colore %s ±%d per canale (di C8) · almeno il %.0f%% dello"
          % (c8.COLORE, c8.TOLLERANZA, fm * 100))
    print("          schermo · scarto massimo prima/dopo %.3f" % a.scarto_massimo)
    print("   pausa staccato: %.0f s  (⭐ = 2 × i %.0f s di sopravvivenza "
          "misurata del monitor)" % (a.pausa_staccato, SOPRAVVIVENZA_MISURATA_S))
    print("   modo: %s" % (
        "⛔ GUASTO INNESTATO — fra il distacco e il riattacco si UCCIDE la "
        "sessione: deve dare ROSSO, e il morso e' il PID del figlio che cambia"
        if a.uccidi_la_sessione else
        "giro normale: si apre, si vede la scena, ci si stacca, si torna"))
    print()

    # ⛔ SI CANCELLA PRIMA DI CREARLO: «da zero» comprende anche «da zero
    #    rispetto a me stesso di ieri» (`LEZIONI.md` §1.39).
    sgombera(chi)
    fatto, perche = crea(chi, a.parola)
    if not fatto:
        print("⛔ non sono riuscito a creare «%s»: %s" % (chi, perche))
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    togli_di_mezzo_il_difetto_di_c8(chi, c8)
    uid = uid_di(chi)

    esito = 3
    prima = osservazione()
    dopo = osservazione()
    try:
        # ═══════════════════════════════════════════════════════════════════
        # 1 · LA SESSIONE DIVENTA VIVA — ⭐ C6 parte da qui, per mandato
        # ═══════════════════════════════════════════════════════════════════
        print("  1 · faccio nascere la sessione (cliente attaccato %.0f s)…"
              % a.resta_nascita)
        dn = os.path.join(a.lavoro, "nascita.log")
        pn, sn = attacca(chi, a, a.resta_nascita, dn)
        amm_n, _f, coda_n = raccogli_il_cliente(
            pn, sn, dn, max(120.0, a.resta_nascita * 4))
        if amm_n is None:
            print("      ⛔ il cliente di prova non e' tornato: e' un guasto del "
                  "BANCO (§1.51)")
            print("   ⇒ non ho potuto guardare")
            sys.exit(3)
        if not amm_n:
            # ⛔ «Non ammesso» da solo e' un silenzio: si porta il MOTIVO
            #    accanto al sintomo (la lezione di C1, 26 ago 2026).
            motivo = "?"
            for riga in reversed((coda_n or "").strip().splitlines()):
                riga = riga.strip()
                if riga and not riga.startswith("=="):
                    motivo = riga[:100]
                    break
            print("      ⛔ NON ammesso: %s" % motivo)
            print("   ⇒ non ho potuto guardare")
            sys.exit(3)

        figlio, quanto = aspetta(lambda: (lambda v: v if v != VUOTO else None)(
            figlio_di(uid)), a.attesa_figlio)
        print("      il figlio «%s»: %s"
              % (NOME_FIGLIO,
                 ("⭐ pid %s, dopo %.1f s" % (figlio, quanto)) if figlio
                 else "⛔ mai comparso in %.0f s" % a.attesa_figlio))
        display, quanto = aspetta(lambda: socket_wayland(uid),
                                  a.attesa_compositore)
        print("      il compositore: %s"
              % (("⭐ %s, dopo %.1f s" % (display, quanto)) if display
                 else "⛔ nessun socket wayland in %.0f s"
                      % a.attesa_compositore))
        if not display:
            print()
            print("⚠ NON GIUDICO (esito 3) — senza compositore non posso aprire")
            print("  nessuna finestra, ⇒ non c'e' nessuna scena da ritrovare.")
            print("  ⛔ E non e' un rosso di C6: e' la nascita della sessione,")
            print("     che e' la domanda di C1 e C2.")
            sys.exit(3)

        # ═══════════════════════════════════════════════════════════════════
        # 2 · LA SCENA — ⭐ prima la si scalda FUORI, poi la si apre DENTRO
        # ═══════════════════════════════════════════════════════════════════
        print("  2 · scaldo il browser fuori dalla sessione (tetto %.0f s)…"
              % a.attesa_scena)
        png_s, detto = scalda_il_browser(chi, a, os.path.join(a.lavoro, "scaldata.png"))
        fr_s = c8.frazione_del_colore(png_s) if png_s else None
        if fr_s is None or fr_s < fm:
            print("      ⛔ il browser non disegna la pagina nemmeno da solo "
                  "(frazione: %s)" % ("non lo so" if fr_s is None
                                      else "%.3f" % fr_s))
            if detto:
                print("      ⛔ dice: %s" % detto.replace("\n", " ")[:150])
            print()
            print("⚠ NON GIUDICO (esito 3) — in questa scatola non c'e' nessuna")
            print("  scena da mettere in sessione.  ⛔ Non e' un rosso del")
            print("  prodotto: e' la scatola (`[M]` C8, 26 ago 2026: senza")
            print("  `libpci3` Firefox non produce nessuna immagine).")
            sys.exit(3)
        print("      ⭐ il browser disegna: la pagina copre il %.1f%% "
              "(profilo scaldato)" % (fr_s * 100))

        print("  3 · attacco «PRIMA» (%.0fs) e apro la scena DENTRO la sessione…"
              % a.resta_prima)
        flusso1 = os.path.join(a.lavoro, "prima.264")
        dp = os.path.join(a.lavoro, "prima.log")
        pp, sp = attacca(chi, a, a.resta_prima, dp, video=flusso1)
        # ⭐ SI ASPETTA L'EVENTO, NON L'OROLOGIO (§1.49): il diario del cliente
        #    dice quando e' stato AMMESSO.  ⛔ Aprire la finestra prima di
        #    quell'istante vorrebbe dire aprirla su un desktop che, `[M]`, non
        #    ha ancora nessuno schermo — e poi accusare il prodotto di non
        #    avercela ritrovata.
        # ⛔ E si aspetta la RIGA, non la parola: col predicato vecchio questo
        #    ciclo usciva **subito e contento** su un cliente RESPINTO, e la
        #    scena si apriva su una sessione che non esisteva.
        visto, quanto = aspetta(lambda: e_stato_ammesso(leggi(dp)) is True,
                                a.attesa_ammissione, passo=0.5)
        print("      il cliente «prima» e' stato ammesso: %s"
              % (("⭐ dopo %.1f s" % quanto) if visto
                 else "⛔ non l'ha detto in %.0f s" % a.attesa_ammissione))
        # ⚠ E poi l'aggancio del consumatore, che `[M]` costa 65÷93 ms: il
        #   valore predefinito e' larghissimo, ed e' l'unico tempo cieco che
        #   questa maglia spende.
        time.sleep(a.aggancio)
        partita = time.time()
        display, err = apri_la_scena(chi, a)
        if display is None:
            print("      ⛔ non ho potuto accendere la scena: %s" % err)
        else:
            # ⛔⛔ L'ATTESA DEL PROFILO STA DENTRO LA POSA, non in piu'.
            #     ⚠ Sommarle sfonderebbe `--resta-prima` e la foto arriverebbe
            #       DOPO che il cliente se n'e' gia' andato — cioe' il difetto
            #       che il controllo del bilancio, qui sopra, esiste per
            #       impedire.
            prof, q2 = aspetta(lambda: profilo_del_browser(chi),
                               max(1.0, a.posa_scena / 2.0))
            print("      il browser e' partito: %s"
                  % (("⭐ profilo suo dopo %.1f s" % q2) if prof
                     else "⚠ nessun profilo suo (era gia' scaldato)"))
            resto = a.posa_scena - (time.time() - partita)
            print("      la posa della scena: %.0f s in tutto (ne restano %.0f)"
                  % (a.posa_scena, max(0.0, resto)))
            if resto > 0:
                time.sleep(resto)

        amm_p, fot_p, coda_p = raccogli_il_cliente(
            pp, sp, dp, max(180.0, a.resta_prima * 3))
        if amm_p is False:
            # ⛔ «Non ammesso» da solo e' un silenzio: il motivo si porta
            #    accanto al sintomo, come fa C1 dal 26 ago 2026.
            motivo = "?"
            for riga in reversed((coda_p or "").strip().splitlines()):
                riga = riga.strip()
                if riga and not riga.startswith("=="):
                    motivo = riga[:100]
                    break
            print("      ⛔ il cliente «prima» NON e' stato ammesso: %s" % motivo)
        figlio_p = figlio_di(uid)
        png1 = immagine_dal_flusso(flusso1, os.path.join(a.lavoro, "prima.png"))
        fr_p = c8.frazione_del_colore(png1) if png1 else None
        g1 = giudice.giudica(png1) if png1 else None
        prima = osservazione(ammesso=amm_p, figlio=figlio_p, frazione=fr_p,
                             verdetto=(g1 or {}).get("verdetto"),
                             fotogrammi=fot_p)
        print("      PRIMA: ammesso=%s · figlio=%s · fotogrammi=%s · "
              "immagine=«%s» · scena=%s"
              % (amm_p, figlio_p, fot_p, (g1 or {}).get("verdetto", "?"),
                 "non lo so" if fr_p is None else "%.1f%%" % (fr_p * 100)))

        # ═══════════════════════════════════════════════════════════════════
        # 4 · IL DISTACCO — ⛔ il cliente e' gia' finito: E' il gesto.
        #     ⚠ E qui NON si giudica niente: «si stacca soltanto» e' la
        #       domanda di C7, e per lei dev'essere VERDE (I4).
        # ═══════════════════════════════════════════════════════════════════
        print("  4 · il cliente se n'e' andato.  ⛔ La sessione NON si chiude: "
              "resto staccato %.0f s" % a.pausa_staccato)
        if a.uccidi_la_sessione:
            # ⛔ IL GUASTO INNESTATO, ed e' il gesto vero: quel che succede
            #    quando l'inquilino ESCE (la stessa riga che C7 chiama
            #    «chiudere la sessione»).  ⚠ Il prodotto non ha un comando
            #    «chiudi la sessione»: la fine di una sessione, oggi, e' la
            #    fine della sessione di `logind`.
            print("      ⛔ GUASTO INNESTATO: uccido la sessione di «%s»" % chi)
            corri(["loginctl", "terminate-user", chi], tempo=60)
            time.sleep(1.0)
            corri(["pkill", "-KILL", "-u", chi], tempo=60)
        time.sleep(a.pausa_staccato)

        # ═══════════════════════════════════════════════════════════════════
        # 5 · IL RIATTACCO — ⭐ e qui si guarda
        # ═══════════════════════════════════════════════════════════════════
        print("  5 · riattacco (%.0f s)…" % a.resta_dopo)
        flusso2 = os.path.join(a.lavoro, "dopo.264")
        dd = os.path.join(a.lavoro, "dopo.log")
        pd, sd = attacca(chi, a, a.resta_dopo, dd, video=flusso2)
        amm_d, fot_d, coda_d = raccogli_il_cliente(
            pd, sd, dd, max(180.0, a.resta_dopo * 3))
        if amm_d is False:
            motivo = "?"
            for riga in reversed((coda_d or "").strip().splitlines()):
                riga = riga.strip()
                if riga and not riga.startswith("=="):
                    motivo = riga[:100]
                    break
            print("      ⛔ il riattacco NON e' stato ammesso: %s" % motivo)
        figlio_d = figlio_di(uid)
        png2 = immagine_dal_flusso(flusso2, os.path.join(a.lavoro, "dopo.png"))
        fr_d = c8.frazione_del_colore(png2) if png2 else None
        g2 = giudice.giudica(png2) if png2 else None
        dopo = osservazione(ammesso=amm_d, figlio=figlio_d, frazione=fr_d,
                            verdetto=(g2 or {}).get("verdetto"),
                            fotogrammi=fot_d)
        print("      DOPO : ammesso=%s · figlio=%s · fotogrammi=%s · "
              "immagine=«%s» · scena=%s"
              % (amm_d, figlio_d, fot_d, (g2 or {}).get("verdetto", "?"),
                 "non lo so" if fr_d is None else "%.1f%%" % (fr_d * 100)))
        print()

        # ═══════════════════════════════════════════════════════════════════
        esito, specie, motivi = giudica(prima, dopo, fm, a.scarto_massimo)
        if esito == 0:
            print("⭐ VERDE (%s)" % specie)
        elif esito == 1:
            print("⛔⛔ ROSSO — specie: %s" % specie)
        elif esito == 2:
            print("⛔ TERRENO CATTIVO (esito 2)")
        else:
            print("⚠ NON GIUDICO (esito 3) — specie: %s" % specie)
        for riga in motivi:
            print("   %s" % riga)
        if esito == 3:
            print("   ⛔ E questo non e' un verde: e' un esito suo (§4.5).")

        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ COL GUASTO INNESTATO L'ESITO SI LEGGE AL CONTRARIO — e' la
        #     convenzione del gancio (`11-gancio.sh`, `esegui_maglia`): una
        #     maglia col guasto innestato esce 0 quando il guasto E' STATO
        #     VISTO.  ⇒ Da li' il gancio ricava `ha_visto_il_guasto`, ed e'
        #     quella chiave che tiene in vita C13.
        # ⛔ E si invertono SOLO 0 e 1: il 2 e il 3 non sono giudizi, e un «non
        #    ho guardato» rovesciato diventerebbe un verde inventato.
        # ═══════════════════════════════════════════════════════════════════
        if a.uccidi_la_sessione and esito in (0, 1):
            print()
            morso = guasto_morso(prima, dopo)
            if esito == 1 and morso:
                print("⭐ IL GUASTO INNESTATO E' STATO VISTO ⇒ questa maglia SA "
                      "dare rosso")
                print("   ⭐ e il morso e' misurabile: il figlio e' passato da "
                      "%s a %s" % (prima["figlio"], dopo["figlio"]))
                print("   ⚠ e percio' esce **0**: col guasto innestato l'esito "
                      "si legge al contrario")
                esito = 0
            elif esito == 1:
                print("⛔⛔ ROSSO, ma NON per colpa del guasto: il figlio e' "
                      "rimasto LO STESSO (%s)." % prima["figlio"])
                print("    ⇒ E' il difetto del PALCO, quello che C6 esiste per")
                print("      trovare — non l'iniezione.  ⛔ Certificare la rete")
                print("      su un difetto del prodotto e' `LEZIONI.md` §1.52.")
                print("    ⚠ Il rosso resta vero e resta importante: ⛔ ma non")
                print("      dimostra che questa maglia sappia dare rosso, e i")
                print("      due fatti non vanno confusi.")
                esito = 1
            else:
                print("⛔⛔ IL GUASTO INNESTATO NON E' STATO VISTO: si e' uccisa "
                      "la sessione e la maglia dice VERDE.")
                print("    ⇒ o l'inquilino ha ritrovato una sessione nuova senza")
                print("      accorgersene, o questa maglia non guarda nel posto")
                print("      giusto — ⛔ e in tutt'e due i casi non ci si puo'")
                print("      fidare di lei (`LEZIONI.md` §1.44).")
                esito = 1
    finally:
        # ⛔ Chi apre, chiude (`LEZIONI.md` §9-ter): anche col guasto innestato,
        #    e anche se il giudizio e' andato male.
        for f in ("prima.264", "dopo.264"):
            try:
                os.unlink(os.path.join(a.lavoro, f))
            except OSError:
                pass
        sgombera(chi)
    sys.exit(esito)


if __name__ == "__main__":
    main()
