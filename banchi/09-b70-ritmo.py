#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b70-ritmo — IL RITMO QUANDO LA LINEA SI STRINGE, e la prima cosa che chiede
               non e' «quanto degrada bene»: e' **se degrada quando non deve**.

    porta 7809 · utente `provan9` (uid 1029) · albero `/media/REMOTIX/src/09-r-src`
    lavoro `/media/REMOTIX/tmp/09-r` · unita' `remotix-7809` · ban-file e socket suoi

═══════════════════════════════════════════════════════════════════════════════
⛔ DA DOVE NASCE — e sono tre fatti, non un'intenzione
═══════════════════════════════════════════════════════════════════════════════

 1. ⛔⛔ **In v1 la fase omologa (la 10) fu AZZERATA**, e non per un difetto
    tecnico (`v1/documenti/PIANO.md:1418`): fu validata con PSNR, SSIM e un
    fotogramma guardato a occhio dallo sviluppatore, e il giudizio dell'utente
    sul desktop vero fu *«siamo tornati indietro»*.  ⇒ **Questo banco non
    produce un verdetto sull'immagine e non ha il permesso di produrlo.**
    Produce numeri sul RITMO; l'immagine la giudica l'utente.

 2. ⛔ **Il secondo errore di v1 fu ottimizzare nella direzione sbagliata**:
    *«spendere meno banda»* fu contato come un guadagno, e per il prodotto la
    banda e' un **pavimento**, non un budget.  ⇒ ⭐ Qui **nessun predicato
    premia la banda risparmiata**.  Il verde si prende consegnando fotogrammi.

 3. ⭐⭐ **Il punto di lavoro e' cambiato il 23 agosto 2026** — `DECISIONI.md`
    §3.1-bis: *«ritengo che una connessione minima debba essere 20 mbps: al di
    sotto di questo limite l'utente nemmeno riesce a navigare»*.  ⇒ I gradini
    vecchi di `07-b65` — 3, 2, 1, 0,5 Mbit/s — **misuravano una promessa che il
    prodotto non fa piu'**, e qui non tornano come requisito.

═══════════════════════════════════════════════════════════════════════════════
⭐ CHE COSA SA VEDERE — cinque grandezze, e si scrivono TUTTE E CINQUE
═══════════════════════════════════════════════════════════════════════════════

`LEZIONI.md` §6.2: *«una tabella con una colonna sola non e' una misura corta:
e' una misura **orientata**»*.  ⇒ Ogni giro porta, sempre, anche quando non
servono alla domanda del momento:

  1. **fotogrammi consegnati al secondo** — media a regime **e** il minimo su
     finestra di un secondo.  ⛔ La media da sola e' l'inganno che il controllo
     positivo di questo file riproduce apposta (caso 2);
  2. **quante CHIAVI e quanti DELTA** — perche' §3.3 impone di degradare **nel
     tempo**, e un flusso di sole chiavi degrada nello spazio *e* nel tempo
     insieme, che e' il difetto misurato il 21 agosto (144/144, 149/149);
  3. **i byte al secondo sul filo** — letti dal contatore del `qdisc`, non
     dedotti — accanto ai byte del **carico utile**, perche' la differenza fra
     i due e' padding, ritrasmissioni, riscontri e audio;
  4. **il ritardo** — ⚠ e la sua natura esatta e' scritta piu' sotto: e' la
     **deriva**, non l'anello;
  5. **i contatori degli abbandoni del server** — video e audio — piu' ⭐ **i
     buchi nella successione dei `numero`**, che sono la *seconda gamba*: il
     conto degli abbandoni misurato dal lato che riceve, indipendente dal
     registro del server (§6.2: *«un buco nella successione e' normale e
     significa qualcosa»*).

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ I DUE PREDICATI CHE DECIDONO, E SONO SCRITTI PRIMA — non prosa
═══════════════════════════════════════════════════════════════════════════════

`07-b64-rete.py` porta il rilievo **R13**: nove «attesi» stampati, archiviati e
**mai confrontati**.  Un banco cosi' non puo' dare rosso.  ⇒ Qui ogni atteso e'
una funzione che riceve i numeri e torna `(passa, perche)`, e `passa` vale
`None` quando il banco **rifiuta di giudicare** — che e' un terzo esito, non un
verde educato (`CODER.md` §3.10).

  **I1 — il ritmo non cala perche' la scena e' ferma** (`SPECIFICHE.md` §8.2).
  ⛔ E' il primo predicato, e per questo ogni gradino si gira **in coppia**:
  scena ferma e scena mossa, stesso gradino, stessa tela, stesso tutto.

  ⭐⭐ **E «scena ferma» qui NON vuol dire «scena spenta»**, che e' quel che fa
  `07-b65 --scena no`.  A scena spenta il compositore consegna pochissimo, e i
  fotogrammi al secondo dei due giri **non sono confrontabili**: un ritmo basso
  a monte somiglia in tutto a un ritmo abbassato da noi.  ⇒ La scena ferma e'
  `04-b30-scena --movimento marca`: cambia **solo la marca**, quindi la cadenza
  di cattura resta quella del giro mosso e a cambiare c'e' il **costo**, che e'
  l'unica cosa che I1 vuole isolare.
  ⛔ E il predicato **si rifiuta di giudicare** se i `consegnati a RCP` dei due
  giri differiscono di piu' del 25 %: quella differenza e' **a monte di noi**, e
  attribuircela sarebbe la ferita di `LEZIONI.md` §1.26 (*«un candidato misurato
  non e' una licenza di attribuzione»*).

  **Il pavimento dell'immagine — 480p · 25 fps** (`DECISIONI.md` §2.1,
  riconfermata il 23 agosto).  ⛔ E la sua ragione e' cambiata: non e' piu' il
  livello a cui una linea povera costringe, e' **il fondo della scala** — il
  punto oltre il quale il regolatore non ha il permesso di scendere.
  ⇒ ⭐ **Su una linea da 20 Mbit/s un ritmo sotto i 25 al secondo e' un
  DIFETTO**, non una degradazione riuscita.  E' un predicato, non una frase.

═══════════════════════════════════════════════════════════════════════════════
⭐ I GRADINI — scelti attorno al pavimento, e due sono DIAGNOSI DICHIARATA
═══════════════════════════════════════════════════════════════════════════════

| gradino | che cos'e' | i predicati |
|---|---|---|
| `g0-largo` | nessun limite e nessun ritardo: il denominatore | requisito |
| ⭐ `g0b-ritardo` | i soli 15 ms per lato, banda libera. ⛔ **Esiste perche' fra `g0` e `g1` cambierebbero DUE cose insieme** — la banda e il giro di rete — e una differenza attribuibile a tutt'e due non e' attribuita a niente (`LEZIONI.md` §1.26) | requisito |
| `g1-40mbit` | il doppio del pavimento. ⚠ E' anche il confine del livello H.264 dichiarato: `avc1.640032` e' High **5.0**, e sopra i 40 servirebbe 5.1 (`SPECIFICHE.md` §6.4) — qui non si sale | requisito |
| `g2-30mbit` | il «fisso buono» di §3.1-bis | requisito |
| `g3-25mbit` | poco sopra il pavimento: il primo gradino in cui qualcosa puo' dover cedere | requisito |
| ⭐ `g4-20mbit` | ⛔ **IL PAVIMENTO. E' il gradino che decide la fase** | requisito |
| ⚠ `g5-15mbit` | **sotto il promesso** — diagnosi | solo «non stacca» |
| ⚠ `g6-10mbit` | meta' del pavimento — diagnosi: si guarda **come** cede | solo «non stacca» |

⛔ **Sotto il pavimento resta in vigore un solo obbligo**, e §3.1-bis lo dice
   con queste parole: *«non e' un rifiuto: il divieto di staccare resta
   intero»*.  ⇒ Ai gradini di diagnosi il banco misura tutto e **pretende una
   cosa sola: che la sessione non muoia**.  Chiamare «rosso» un ritmo basso a
   10 Mbit/s vorrebbe dire misurare una promessa che il prodotto non fa — cioe'
   ripetere l'errore 2 di v1 col segno cambiato.

⛔ **E i gradini di `07-b65` (3 · 2 · 1 · 0,5 Mbit/s) NON tornano**: stanno da
   sette a quaranta volte sotto il pavimento, e la domanda a cui rispondevano —
   *«chi paga quando il tubo e' stretto»* — ha gia' una risposta misurata
   (l'audio, e per la spirale di §5.2).  Rifarli qui darebbe numeri veri a una
   domanda che non si fa piu'.

⛔ **LA CODA DEL FILO SI DICHIARA, e non e' un dettaglio.**  Il predefinito di
   `netem` e' `limit 1000` pacchetti: a 20 Mbit/s con pacchetti da 1452 byte
   sono **580 ms di cuscino**, che da soli dominerebbero la misura del ritardo e
   la nasconderebbero dentro il banco.  ⇒ Ogni gradino porta il suo `limit`,
   calcolato per valere **50 ms** alla sua banda, e il numero e' stampato.
   ⚠ 50 ms e' *sufficiente, non giusto*: e' l'ordine di grandezza di una coda
   di casa, ed e' scelto da qui, non dal predefinito di un attrezzo.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔⛔ CHE COSA QUESTO BANCO **NON** SA VEDERE — e si dichiara in testa
═══════════════════════════════════════════════════════════════════════════════

 1. ⛔⛔ **L'IMMAGINE.**  Conta fotogrammi, chiavi, byte e ritardo.  Non sa dire
    *«si vede peggio»*.  ⚠ PSNR e SSIM non compaiono in questo file **per
    scelta**: in v1 sono stati il verdetto, e il verdetto e' dell'utente sul
    desktop vero.  Un verde di questo banco **non autorizza a spedire niente
    che cambi quel che si vede** (I6: interruttore spento finche' non l'ha
    guardato).

 2. ⛔ **IL RITARDO VERO.**  `RCP.md` §6.2: *«l'`istante` e' l'orologio monotono
    del server; il client NON DEVE confrontarlo con il proprio»*.  ⇒ Qui NON si
    misura il ritardo dell'anello.  Si misura la **DERIVA**:

        deriva(n) = (arrivo(n) − arrivo(0)) − (istante(n) − istante(0))

    cioe' **quanto la consegna e' rimasta indietro rispetto alla cattura da
    quando il giro e' cominciato**.  E' una differenza di differenze fra due
    orologi monotoni **dello stesso kernel** (il cliente gira in un contenitore
    sulla stessa macchina), quindi le due basi dei tempi si cancellano e le due
    velocita' sono la stessa.  ⚠ La deriva **parte da zero per costruzione**:
    dice quanto la coda e' CRESCIUTA, non quanto vale.  ⭐ Il valore assoluto lo
    misura l'anello della fase 8 — `[M]` 55,20 ms appaiato — e serve un browser.

 3. ⛔ **LA RETE VERA.**  `netem` gira su `lo`: MTU 65536, nessun WiFi, nessuna
    coda di router, nessun traffico di terzi, nessuna migrazione.  ⭐ Il
    pavimento dei 20 Mbit/s **a casa dell'utente** si strozza con
    `wondershaper` sul tablet, e **questo banco non lo fa**.  ⚠ Il banco stampa
    i **byte per pacchetto** letti dal qdisc apposta: se non valgono ~1452 la
    grana della strozzatura non e' quella di una rete e il numero va riletto.

 4. ⛔ **IL BROWSER.**  Il cliente e' `01-b3-cliente.py`: prende i byte dal filo
    e **non decodifica e non dipinge**.  «Consegnato sul filo» non e'
    «dipinto»: `[M]` fase 8, il worker dipinge di piu' sulla catena vera e il
    **73 % di meno** a saturazione.  ⇒ I fotogrammi al secondo di qui sono un
    **tetto**, non quel che l'utente vede.

 5. ⛔ **LA QUALITA' A OGNI GRADINO.**  Oggi il prodotto **non ha un controllo di
    bitrate** (`grep bit_rate|maxrate|bufsize codificatore.c` → zero) e il QP e'
    fisso a 26 (`figlio.c:4052`, `rc_mode = CQP`).  ⇒ Questo banco misura che
    cosa fa un prodotto **senza regolatore**: e' la fotografia del *prima*.

 6. ⚠ **L'AUDIO.**  Ne legge i contatori e li stampa, ma **non lo giudica**: il
    giudice del suono e' `banchi/07-b64-orecchio.py`, certificato, e non si
    riscrive qui.  ⭐ E la domanda *«chi paga fra audio e video»* e' gia' chiusa
    da `07-b65`: qui il tono e' **spento** salvo `--tono si`, cosi' il gradino
    misura il video e non una gara.

 7. ⚠ **CHI ALTRO STA SULLA MACCHINA** (`LEZIONI.md` §1.26 — *«non da' un rosso,
    da' un numero plausibile»*).  Il banco conta gli ascoltatori non suoi e il
    carico, e li stampa; garantire l'esclusiva non puo'.

 8. ⛔ **IL PROPRIO PESO.**  La traccia §11.1 la scrive il cliente in memoria: a
    20 Mbit/s per 30 s sono ~75 MB.  ⇒ Il banco confronta **sempre** i
    fotogrammi che il cliente ha preso con gli `spediti` del server: se il
    cliente ne ha meno, il collo puo' essere il testimone.  ⭐ E `--controllo-
    testimone` rigira il gradino del pavimento **senza traccia**, che e' la
    prova diretta.

═══════════════════════════════════════════════════════════════════════════════
⭐ CHE COSA NON E' RISCRITTO — si importa
═══════════════════════════════════════════════════════════════════════════════

  · la **disciplina della rete** (guardiano staccato, `prio` a quattro bande,
    due filtri `u32` sulla sola porta, `rimetti` che si verifica) e' quella di
    `banchi/07-b65-datagram.py`, **importata**, non ricopiata: l'ambiente si
    fissa PRIMA dell'import e poi si **verifica** che il modulo abbia preso la
    porta e il dispositivo giusti, o il banco non parte;
  · le **magie** del formato §11.1 si leggono da `banchi/01-b4-validatore.py`:
    due elenchi di versioni in due file sono due elenchi che divergono;
  · il **terreno** e' `banchi/07-b64-terreno.sh`, guidato dall'ambiente sulle
    porte MIE — come `08-b67` fa con `04-b32-terreno.sh`.

⛔⛔ E C'E' UN BANCO FRATELLO, `banchi/09-b68-ritmo.py`, DELLO STESSO GIORNO —
    porta **7900**, utente `prova`, di un altro agente.  Si dichiara qui perche'
    due banchi che si ignorano finiscono a rifare la stessa misura con numeri
    diversi.

    | | `09-b68` | ⭐ questo |
    |---|---|---|
    | la domanda | I1 **su linea larga**, una sola | I1 **a ogni gradino** attorno al pavimento |
    | «scena ferma» | la scena **spenta** | ⭐ `--movimento marca`: viva, cadenza uguale, costo diverso |
    | l'atteso | prosa piu' un controllo positivo (la scena `pieno`) | ⛔ **predicati scritti prima** che tornano `(passa, perche)` |
    | il ritardo | non lo misura | la **deriva**, dalla traccia §11.1 |
    | chiavi/delta | dalle righe «SPEDITO» del registro | **dal filo**, piu' i buchi nel `numero` |
    | i byte del filo | `/proc/net/dev` (⭐ `[M]` `lo` a riposo fa **0 byte in 5 s**) | il contatore del qdisc, **ristretto alla mia porta** |

    ⭐⭐ **E una cosa gliel'ho presa, ed e' la migliore delle due**: le
    **«attese a vuoto»** del figlio (`figlio.c:6842`).  La mia prima guardia di
    I1 confrontava i `consegnati a RCP`; quella dice *«abbiamo chiesto un
    fotogramma e non ce n'era»*, che e' la stessa distinzione senza deduzione.
    ⇒ Adesso la guardia e' doppia, e il controllo positivo ha un caso apposta
    (10b) in cui i `consegnati` si assomigliano e **solo** le attese a vuoto
    salvano il prodotto da un'accusa che non e' sua.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ LE QUATTRO CURE DEL 23 AGOSTO 2026 — e sono tutte della stessa forma
═══════════════════════════════════════════════════════════════════════════════

Quattro difetti, un difetto solo: **silenzio invece di rosso**, cioe' uno zero
che vuol dire *«non ho letto»* con la faccia di uno che vuol dire *«non e'
successo niente»* (`LEZIONI.md` §1.9).  Si scrivono qui perche' il progetto le
ha gia' pagate piu' volte, e la prossima volta si legga prima.

 1. ⛔ **`sudo -S` copre solo il PRIMO anello della catena** (vedi `catena_root()`
    e `root()`).  `[M]` il lettore della traccia §11.1 **non si scriveva** sulla
    macchina, e il banco non se ne accorgeva.  ⇒ Un solo `sudo`, e la catena
    intera dentro `bash -c`.
 2. ⛔⛔ **Un `< file` in coda RUBA lo stdin a `sudo -S`** (stessa sede).  `[M]`
    `righe_registro()` tornava **0** in silenzio, e allora `conti_del_server()`
    leggeva il registro **dall'accensione del server**: `[M]` 23 ago, sul giro
    a scena ferma sarebbero state **4 041** attese a vuoto invece delle **1 604**
    del giro.  ⇒ Redirezione dentro la shell di root, `righe_registro()` che
    torna `None` invece di 0, guardia in `conti_del_server()` e un predicato che
    lo dice a voce alta (`p_registro_letto`).
 3. ⛔ **La premessa implicita di I1** (vedi `p_I1` e `RESA_FERMA`).  *«A scena
    ferma non c'e' congestione che giustifichi un abbandono»* vale **solo su una
    linea senza perdita**: `[M]` su `casa-cattiva` (2 %) la gamba degli abbandoni
    ha dato un rosso che non era del prodotto.  ⇒ Gamba condizionata: si rifiuta
    di giudicare dove la premessa manca, e da' rosso dove c'e'.
 4. ⛔ **Il giornale vuoto perche' non l'ho letto** (vedi `giro()` e
    `p_niente_stacco`).  `[M]` 23 ago: il lettore §11.1 non partiva — mancava
    `01-b4-validatore.py` nell'albero — e il banco ha dato ROSSO a «non stacca»
    su una sessione viva da **797** fotogrammi.  ⇒ La traccia non letta si
    dichiara, `terreno_controlla()` verifica l'arbitro prima di misurare, e i
    predicati che vivono sul giornale si rifiutano invece di accusare.

═══════════════════════════════════════════════════════════════════════════════
I CODICI D'USCITA
═══════════════════════════════════════════════════════════════════════════════

    0   CONFORME — tutti i predicati hanno fatto quel che era scritto prima
    1   NON CONFORME — c'e' almeno un rosso
    2   uso sbagliato, terreno assente, o la rete non si e' potuta rimettere
    3   ⛔ NON HO NIENTE DA GIUDICARE — un giro non ha prodotto numeri, oppure
        un predicato si e' rifiutato di giudicare.  ⚠ Non e' un verde.

Uso (dal portatile):
    python3 banchi/09-b70-ritmo.py --certifica     ⭐ QUI, senza macchina
    python3 banchi/09-b70-ritmo.py terreno
    python3 banchi/09-b70-ritmo.py sonda [--secondi 30] [--solo g4]
    python3 banchi/09-b70-ritmo.py sonda --controllo-testimone
    python3 banchi/09-b70-ritmo.py rimetti         ⛔ e si verifica
"""
import argparse, base64, importlib.util, json, os, re, shlex, statistics, struct
import subprocess, sys, time

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ L'ISOLAMENTO, SCRITTO PRIMA DI QUALUNQUE IMPORT CHE LO LEGGA
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ La 7900 e' di un altro agente, la 7801/7802 sono della fase 7, la 7730 e'
#    dell'utente ed e' ACCESA.  La mia e' la 7809.
PORTA = int(os.environ.get("PORTA", "7809"))
UTENTE = os.environ.get("UTENTE", "provan9")
UID_B = int(os.environ.get("UID_B", "1029"))
MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
IND = os.environ.get("IND", "192.168.0.2")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/09-r")
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/09-r-src")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/09-r-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/09-r")
SCENA_BIN = os.environ.get("SCENA_BIN",
                           "/media/REMOTIX/src/04-b30-scena-lav/04-b30-scena")
QUI = os.path.dirname(os.path.abspath(__file__))
FUORI = os.environ.get("FUORI", "/tmp/09-b70")

VIETATA = "enp7s0"     # ⛔ ci passano l'ssh e la 7730 dell'utente: mai
DEV = "lo"

# ⛔ Le porte che NON sono mie: si contano prima, e non si toccano mai.
VICINE = ["7700", "7710", "7720", "7730", "7801", "7802", "7900"]

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA DISCIPLINA DELLA RETE SI IMPORTA DA 07-b65, E POI SI VERIFICA
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `07-b65-datagram.py` lega le sue costanti all'ambiente **all'import**.  ⇒
#    L'ambiente si fissa qui sopra e si passa PRIMA di importarlo, cosi' il
#    modulo nasce con la porta mia e il guardiano scrive il pid nel mio LAV.
# ⛔⛔ E poi si CONTROLLA.  Importare un modulo che si configura dall'ambiente e
#      dare per scontato che l'abbia letto e' esattamente il modo in cui si
#      finisce a strozzare la porta di qualcun altro credendo di strozzare la
#      propria — e la rete e' l'unica cosa di questo banco che, sbagliata, fa
#      male a chi non c'entra.
def _importa_rete():
    for chiave, valore in (("PORTA", str(PORTA)), ("UTENTE", UTENTE),
                           ("UID_B", str(UID_B)), ("MACCHINA", MACCHINA),
                           ("PAROLA_SUDO", PAROLA_SUDO), ("IND", IND),
                           ("LAV", LAV), ("ALBERO", ALB),
                           ("DENTRO_ALB", DENTRO_ALB), ("DENTRO_LAV", DENTRO_LAV),
                           ("FUORI", FUORI)):
        os.environ[chiave] = valore
    perc = os.path.join(QUI, "07-b65-datagram.py")
    spec = importlib.util.spec_from_file_location("b65rete", perc)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    guai = []
    if m.PORTA != PORTA:
        guai.append("la porta del modulo e' %d, la mia e' %d" % (m.PORTA, PORTA))
    if m.DEV != DEV:
        guai.append("il dispositivo del modulo e' «%s», il mio e' «%s»" % (m.DEV, DEV))
    if m.VIETATA != VIETATA:
        guai.append("l'interfaccia vietata del modulo e' «%s»" % m.VIETATA)
    if m.LAV != LAV:
        guai.append("il guardiano scriverebbe il pid in «%s», non in «%s»" % (m.LAV, LAV))
    if guai:
        raise SystemExit("⛔ NON TOCCO LA RETE: l'import di 07-b65 non ha preso "
                         "il mio ambiente — " + " · ".join(guai))
    return m


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I GRADINI — e l'atteso di ciascuno e' un PREDICATO, piu' sotto
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ C'e' sempre un ritardo: senza RTT la finestra di congestione non ha modo di
#    riempirsi e il pacer non si accorge di niente.  15 ms per lato = 30 ms di
#    giro, che e' una fibra di casa.
RITARDO_MS = int(os.environ.get("RITARDO_MS", "15"))
CUSCINO_MS = int(os.environ.get("CUSCINO_MS", "50"))   # ⛔ la coda del filo, dichiarata
PACCHETTO = 1452                                        # il pacchetto QUIC tipico


def _limite(mbit):
    """I pacchetti di coda che valgono `CUSCINO_MS` a quella banda."""
    return max(8, int(mbit * 1e6 * (CUSCINO_MS / 1000.0) / 8.0 / PACCHETTO))


def _regole(mbit, ritardo_ms):
    """⛔ ANCHE IL GRADINO LARGO PORTA UN `netem`, e la ragione e' la grandezza 3.

    I byte veri sul filo si leggono dal contatore del qdisc (`tc -s`).  Un
    gradino senza qdisc non ha quel contatore ⇒ il **denominatore** sarebbe
    l'unico giro senza i byte sul filo, cioe' l'unico giro che non si puo'
    confrontare con gli altri sulla grandezza che decide se la linea e' piena.
    ⇒ `g0` porta un `netem` **senza banda e senza ritardo**: serve solo a
    contare.  ⚠ E il suo prezzo si dichiara — un qdisc in piu' nel percorso —
    invece di lasciare il denominatore cieco.
    """
    regole = ["limit", str(_limite(mbit)) if mbit else "100000"]
    if ritardo_ms:
        regole += ["delay", "%dms" % ritardo_ms]
    if mbit:
        regole += ["rate", "%dmbit" % mbit]
    return regole


#  (nome, mbit, ritardo_ms, requisito, perche)
#
# ⭐⭐ E IL RITARDO HA UN GRADINO SUO.  Se `g0` non avesse ritardo e `g1` avesse
#     ritardo **e** banda, fra i due cambierebbero DUE cose insieme, e qualunque
#     differenza sarebbe attribuibile a tutt'e due — che e' il modo piu' educato
#     in cui una griglia di gradini puo' mentire (`LEZIONI.md` §1.26: *«ogni
#     numero va attribuito da se'»*).  ⇒ `g0b` porta i 15 ms **e basta**.
GRADINI = [
    ("g0-largo",   None, 0, True,
     "nessun limite e nessun ritardo: il denominatore. Il netem c'e' solo per "
     "contare i byte"),
    ("g0b-ritardo", None, RITARDO_MS, True,
     "⭐ i soli %d ms per lato, banda libera: isola l'effetto del GIRO DI RETE "
     "da quello della banda" % RITARDO_MS),
    ("g1-40mbit",  40, RITARDO_MS, True,
     "il doppio del pavimento — e il confine del livello H.264 dichiarato (5.0)"),
    ("g2-30mbit",  30, RITARDO_MS, True,
     "il «fisso buono» di §3.1-bis: si punta al desiderato"),
    ("g3-25mbit",  25, RITARDO_MS, True,
     "poco sopra il pavimento: il primo gradino in cui qualcosa puo' cedere"),
    ("g4-20mbit",  20, RITARDO_MS, True,
     "⭐ IL PAVIMENTO (§3.1-bis). E' il gradino che decide la fase"),
    ("g5-15mbit",  15, RITARDO_MS, False,
     "⚠ SOTTO IL PROMESSO — diagnosi dichiarata: si guarda, non si pretende"),
    ("g6-10mbit",  10, RITARDO_MS, False,
     "⚠ meta' del pavimento — diagnosi: interessa COME cede, non se cede"),
]

# ⭐ La tela.  La griglia gira a 1080p, che e' il desktop vero e quello che
#    l'utente guarda.  ⛔ Ma il pavimento di §2.1 e' scritto **a 480p**, e la
#    risoluzione adattiva e' fuori dal prodotto per decisione (§5.0-ter): il
#    prodotto serve la tela che il cliente chiede, e basta.  ⇒ Al solo gradino
#    del pavimento la coppia si rifa' anche a **768x480**, che e' il numero che
#    il progetto scrive gia' per «il minimo di §2.1» (`DECISIONI.md:1133`).
TELA_PIENA = os.environ.get("TELA", "1920x1080")
TELA_MINIMA = os.environ.get("TELA_MINIMA", "768x480")

# ⭐ Il codec si dichiara e si VERIFICA sul filo.  Il server offre «hevc,h264»
#    (`rcp.c:1674`); il predefinito del cliente e' «hevc,av1», che negozierebbe
#    **HEVC** — cioe' un punto di lavoro che non e' quello del prodotto, perche'
#    Firefox su Android non ha ne' HEVC ne' AV1.  ⇒ Si chiede h264, e il banco
#    legge dal filo quale codec e' davvero arrivato: una ricaduta silenziosa su
#    un altro codec cambierebbe ogni numero di questa pagina senza dirlo.
CODEC_CHIESTO = os.environ.get("CODEC", "h264")
CODEC_NUMERO = {1: "hevc", 2: "av1", 3: "h264"}


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LE SOGLIE, IN UN POSTO SOLO, E CIASCUNA CON LA SUA RAGIONE
# ═══════════════════════════════════════════════════════════════════════════
PAVIMENTO_FPS = 25.0        # `DECISIONI.md` §2.1: 480p · 25 fps, il fondo della scala
PAVIMENTO_FINESTRA = 20.0   # ⚠ *sufficiente, non giusto*: l'80 % del pavimento, e
                            #   serve solo a non dare rosso a una finestra che
                            #   cade a cavallo di un singolo singhiozzo.  Il primo
                            #   giro che atterra fra 20 e 25 va guardato, non
                            #   ritarato.
QUOTA_DELTA = 0.90          # §3.3: si degrada NEL TEMPO.  Un flusso che perde piu'
                            #   di un delta su dieci sta degenerando in chiavi —
                            #   `[M]` 21 ago: sui giri stretti erano 144/144.
DERIVA_FINE_MS = 250.0      # ⭐ ancorata a un numero misurato, non scelta: l'anello
                            #   intero della fase 8 vale `[M]` 55,20 ms.  Una deriva
                            #   che vale QUATTRO anelli non e' piu' un ritardo, e'
                            #   una coda.
DERIVA_MAX_MS = 400.0
I1_TOLLERANZA = 0.05        # ⚠ il rumore fra due giri della stessa macchina
I1_CONSEGNATI = 0.25        # oltre, la differenza e' A MONTE e non si giudica
RESA_FERMA = 0.98           # ⛔⛔ E LA SUA PREMESSA E' CONDIZIONATA, non generale:
                            #   «a scena ferma non c'e' congestione che
                            #   giustifichi un abbandono» vale **solo su una
                            #   linea che non perde**.  `[M]` 23 ago 2026: sul
                            #   profilo `casa-cattiva` (2 % di perdita) la
                            #   premessa e' FALSA e questa gamba ha dato un rosso
                            #   che non era un difetto del prodotto — mentre la
                            #   gamba dei fotogrammi/s passava (ferma 10,13/s
                            #   contro mossa 7,78/s: la ferma andava piu' VELOCE).
                            #   ⇒ La gamba non si toglie: si condiziona al fatto
                            #     che la giustifica (vedi `p_I1`).
SCALDATA_S = 3.0            # ⛔ i primi secondi sono apertura di sessione e prima
                            #   chiave: si dichiarano e si tolgono, e il numero
                            #   intero si stampa lo stesso accanto
MINIMO_FOTOGRAMMI = 30      # sotto, non c'e' niente da ridurre


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL LETTORE DELLA TRACCIA — gira SULLA MACCHINA, perche' la traccia pesa
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Non si inventa nessuno strumento nuovo per sapere quando un fotogramma e'
#    arrivato: `01-b3-cliente.py --registra` scrive gia' la traccia di
#    `RCP.md` §11.1, che porta per ogni blocco l'`istante_ms` dell'orologio
#    **monotono del client** e i byte, e il primo blocco di ogni stream video
#    porta i 28 byte d'intestazione di §6.2 — `numero`, `tipo` (chiave o delta),
#    `codec` e l'`istante` monotono **del server** alla cattura.
#    ⇒ Tutto quel che serve e' gia' sul disco: qui si riduce, non si misura.
#
# ⚠ La grana e' il millisecondo (§11.1 scrive `istante_ms`).  Su un intervallo
#   di 40 ms sono il 2,5 %: basta per il ritmo e per la deriva, **non** basterebbe
#   per un anello — ed e' un'altra ragione per cui l'anello non e' di qui.
#
# ⛔ E la traccia si riduce **sulla macchina**: a 20 Mbit/s per 30 s sono ~75 MB,
#    e portarli sull'ssh a ogni giro sarebbe un'ora di rete per un JSON di 80 KB.
LETTORE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09-b70-leggi — riduce una traccia RCP.md §11.1 al GIORNALE dei fotogrammi.

⛔⛔ IL FORMATO NON SI RISCRIVE QUI.  Magia, disposizione del blocco, codici di
    `fine` e verso si leggono da `01-b4-validatore.py`, che e' **l'arbitro** di
    §11.1.  Due descrizioni dello stesso formato in due file sono due
    descrizioni che divergono, ⚠ ed e' gia' costato un giro intero: il 16 agosto
    2026 il registratore scriveva ancora `0x00 0x01` mentre l'arbitro era passato
    a `0x00 0x02`, e **ogni** traccia usciva «malformata» — un difetto nato fra
    due file, dove nessuna prova unitaria guarda.
"""
import importlib.util, json, struct, sys

CANALE_VIDEO = 0x03


def arbitro(percorso):
    spec = importlib.util.spec_from_file_location("b4arbitro", percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def principale():
    traccia, validatore = sys.argv[1], sys.argv[2]
    A = arbitro(validatore)
    MAGIA, BLOCCO, BLOCCO_BYTE = A.MAGIA, A.BLOCCO, A.BLOCCO_BYTE
    SERVER, FIN, RESET = A.SERVER, A.FIN, A.RESET
    with open(traccia, "rb") as f:
        d = f.read()
    if len(d) < 16 or d[:8] != MAGIA:
        print(json.dumps({"esito": "NON HO NIENTE DA GIUDICARE — la traccia non "
                                   "porta la magia di §11.1",
                          "primi8": d[:8].hex()}))
        return 3
    quanti, orologio, r1, r2, r3 = struct.unpack("!IBBBB", d[8:16])
    if A.OROLOGIO.get(orologio) != "client":
        # ⛔ Senza sapere DI CHI sono i tempi, la deriva non e' nemmeno
        #    formulabile: non si indovina.
        print(json.dumps({"esito": "NON GIUDICO — l'orologio della traccia non "
                                   "e' quello del client", "orologio": orologio}))
        return 3
    p, letti = 16, 0
    flussi, ordine = {}, []
    for _ in range(quanti):
        if p + BLOCCO_BYTE > len(d):
            break
        verso, canale, fine, ist, stream, lung, nosc = struct.unpack(
            BLOCCO, d[p:p + BLOCCO_BYTE])
        p += BLOCCO_BYTE
        p += nosc * 40                       # (ini u32, quanti u32, impronta 32 B)
        carico = d[p:p + lung]
        p += lung
        letti += 1
        if verso != SERVER or canale != CANALE_VIDEO:
            continue
        f = flussi.get(stream)
        if f is None:
            f = flussi[stream] = {"testa": b"", "byte": 0, "fine_ms": None,
                                  "azzerato": False}
            ordine.append(stream)
        if len(f["testa"]) < 28:
            f["testa"] += carico[:28 - len(f["testa"])]
        f["byte"] += lung
        if fine == FIN:
            f["fine_ms"] = ist
        elif fine == RESET:
            # ⭐ §5.1 forma A: il server ha ABBANDONATO questo fotogramma, e si
            #    vede dal lato che riceve.  Non e' un fotogramma consegnato.
            f["azzerato"] = True
            f["fine_ms"] = ist
    giornale, azzerati, monchi = [], 0, 0
    for sid in ordine:
        f = flussi[sid]
        if f["azzerato"]:
            azzerati += 1
            continue
        if f["fine_ms"] is None or len(f["testa"]) < 28:
            # ⚠ Uno stream che la registrazione non ha visto finire: non e' un
            #   fotogramma consegnato e non e' un abbandono.  Si conta a parte,
            #   invece di sparire dentro uno dei due.
            monchi += 1
            continue
        tipo, codec, l, a, numero, istante, inp = struct.unpack("!HHIIIQI", f["testa"])
        giornale.append({"numero": numero, "chiave": tipo == 0x0301,
                         "tipo": tipo, "codec": codec, "l": l, "a": a,
                         "byte": max(0, f["byte"] - 28),
                         "istante_us": istante, "arrivo_ms": f["fine_ms"]})
    giornale.sort(key=lambda x: x["arrivo_ms"])
    print(json.dumps({"esito": "letto", "blocchi": letti, "flussi": len(ordine),
                      "azzerati": azzerati, "monchi": monchi,
                      "giornale": giornale}))
    return 0


if __name__ == "__main__":
    sys.exit(principale())
'''


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ LA RIDUZIONE — ed e' LA STESSA CODICE che `--certifica` esercita
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Il controllo positivo di questo file non prova i predicati su numeri gia'
#    pronti: fabbrica dei GIORNALI e li fa passare di qui.  ⇒ Se l'inganno vive
#    nella riduzione — ed e' il caso della media che nasconde il buco — il
#    controllo lo vede.  Un controllo che saltasse questa funzione certificherebbe
#    meta' dello strumento.
def _mediana(v):
    return statistics.median(v) if v else None


def misura(giornale, chiesto_s, server=None, filo=None, azzerati=None,
           scaldata_s=SCALDATA_S):
    """Da un giornale di fotogrammi ai numeri del giro.  Tutti e cinque."""
    n = {"chiesto_s": chiesto_s, "fotogrammi_grezzi": len(giornale),
         "scaldata_s": scaldata_s, "server": server or {},
         "azzerati_sul_filo": azzerati}
    if not giornale:
        n["esito"] = ("NON HO NIENTE DA GIUDICARE — nessun fotogramma nella "
                      "traccia")
        return n
    a0 = giornale[0]["arrivo_ms"]
    vissuto = (giornale[-1]["arrivo_ms"] - a0) / 1000.0
    n["vissuto_s"] = round(vissuto, 3)
    # ⛔ La scaldata si TOGLIE e si DICE: apertura di sessione, prima chiave e
    #    prima tela stanno li' dentro, e mescolarle col regime e' come misurare
    #    l'accelerazione di un'auto contando anche il tempo di accendere.
    #    ⚠ E il numero intero si stampa lo stesso, accanto: chi toglie dei dati
    #      deve far vedere che cosa ha tolto.
    a_regime = [f for f in giornale if (f["arrivo_ms"] - a0) / 1000.0 >= scaldata_s]
    n["fotogrammi_scaldata"] = len(giornale) - len(a_regime)
    if len(a_regime) < MINIMO_FOTOGRAMMI:
        n["esito"] = ("NON HO NIENTE DA GIUDICARE — %d fotogrammi a regime, "
                      "meno del minimo di %d" % (len(a_regime), MINIMO_FOTOGRAMMI))
        n["fotogrammi"] = len(a_regime)
        return n
    r0 = a_regime[0]["arrivo_ms"]
    durata = (a_regime[-1]["arrivo_ms"] - r0) / 1000.0
    if durata <= 0:
        n["esito"] = "NON HO NIENTE DA GIUDICARE — durata a regime nulla"
        return n
    n["fotogrammi"] = len(a_regime)
    n["durata_s"] = round(durata, 3)
    # 1 · IL RITMO, e sono DUE numeri: la media e il minimo su finestra.
    n["fps"] = round(len(a_regime) / durata, 2)
    n["fps_intero"] = round(len(giornale) / vissuto, 2) if vissuto > 0 else None
    n["fps_finestra_min"], n["finestre"] = _finestra_minima(a_regime)
    intervalli = [(a_regime[i]["arrivo_ms"] - a_regime[i - 1]["arrivo_ms"])
                  for i in range(1, len(a_regime))]
    n["intervallo_mediano_ms"] = _mediana(intervalli)
    n["intervallo_p95_ms"] = (sorted(intervalli)[int(0.95 * (len(intervalli) - 1))]
                              if intervalli else None)
    # 2 · CHIAVI E DELTA — §3.3 vive qui.
    chiavi = sum(1 for f in a_regime if f["chiave"])
    n["chiavi"] = chiavi
    n["delta"] = len(a_regime) - chiavi
    n["quota_delta"] = round(n["delta"] / len(a_regime), 4)
    # ⭐ Il codec VERO, letto dal filo: non quello chiesto.
    codici = sorted({f.get("codec") for f in a_regime})
    n["codec_sul_filo"] = [CODEC_NUMERO.get(c, "?%s" % c) for c in codici]
    misure = sorted({"%dx%d" % (f.get("l"), f.get("a")) for f in a_regime})
    n["tela_sul_filo"] = misure
    # 3 · I BYTE — carico utile qui, filo dal qdisc (piu' sotto).
    byte = sum(f["byte"] for f in a_regime)
    n["byte_carico"] = byte
    n["mbit_s_carico"] = round(byte * 8 / durata / 1e6, 3)
    n["byte_per_fotogramma"] = int(byte / len(a_regime))
    if filo and filo.get("byte") is not None and filo.get("secondi"):
        n["mbit_s_filo"] = round(filo["byte"] * 8 / filo["secondi"] / 1e6, 3)
        n["byte_per_pacchetto"] = filo.get("byte_per_pacchetto")
    else:
        # ⛔ `CODER.md` §3.10: «non ho letto» non e' «zero».  Un 0,0 Mbit/s qui
        #    direbbe «sul filo non passa niente» di una linea che porta.
        n["mbit_s_filo"] = None
        n["byte_per_pacchetto"] = None
        n["filo_non_letto"] = "il contatore del qdisc non e' stato letto"
    # 4 · LA DERIVA — e NON e' il ritardo dell'anello (vedi l'intestazione).
    s0 = a_regime[0]["istante_us"]
    d0 = 0.0
    derive = []
    for f in a_regime:
        d = ((f["arrivo_ms"] - r0) - (f["istante_us"] - s0) / 1000.0)
        derive.append(d)
    n["deriva_fine_ms"] = round(derive[-1] - d0, 1)
    n["deriva_max_ms"] = round(max(derive) - d0, 1)
    n["deriva_min_ms"] = round(min(derive) - d0, 1)
    # 5 · GLI ABBANDONI, e la SECONDA GAMBA che non passa dal registro.
    #     §6.2: il `numero` cresce di uno per ogni fotogramma che il server
    #     DECIDE di spedire, abbandonati compresi, e NON per quelli che non
    #     spedisce affatto.  ⇒ Un buco = un fotogramma partito e non arrivato.
    numeri = sorted(f["numero"] for f in a_regime)
    buchi = 0
    for i in range(1, len(numeri)):
        salto = numeri[i] - numeri[i - 1]
        if salto > 1:
            buchi += salto - 1
    n["buchi_numero"] = buchi
    n["esito"] = "misurato"
    return n


def _finestra_minima(fotogrammi, larghezza_ms=1000):
    """⛔⛔ IL NUMERO CHE LA MEDIA NASCONDE.

    Trenta secondi fatti di dieci a 45/s e venti a 17,5/s danno una media di
    **26,7/s** — sopra il pavimento — e venti secondi in cui il desktop e' a
    scatti.  ⇒ La media da sola assolve, e va accompagnata dal **peggio** che si
    e' visto in un secondo.  ⚠ La finestra e' SCORREVOLE, non a blocchi: a
    blocchi il buco puo' stare a cavallo di due finestre e sparire da tutt'e due.
    """
    if len(fotogrammi) < 2:
        return None, 0
    t = [f["arrivo_ms"] for f in fotogrammi]
    peggio, quante, i = None, 0, 0
    for j in range(len(t)):
        if t[j] - t[0] < larghezza_ms:
            continue
        while t[j] - t[i] > larghezza_ms:
            i += 1
        # fotogrammi nella finestra (t[i], t[j]]
        conto = j - i
        quante += 1
        if peggio is None or conto < peggio:
            peggio = conto
    if peggio is None:
        return None, 0
    return float(peggio), quante


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ I PREDICATI — SCRITTI PRIMA, e ne torna (passa, perche)
# ═══════════════════════════════════════════════════════════════════════════
#
#   passa = True    l'atteso ha retto
#   passa = False   ⛔ rosso
#   passa = None    ⚠ NON GIUDICO — e non e' un verde educato: e' un esito suo,
#                   e fa uscire il banco 3.
def _si(perche):    return (True, perche)
def _no(perche):    return (False, perche)
def _muto(perche):  return (None, perche)


def _ha_misurato(n):
    return n.get("esito") == "misurato"


def p_registro_letto(n):
    """⛔⛔ IL PREDICATO CHE GUARDA LO STRUMENTO, NON IL PRODOTTO — e c'e' perche'
       il difetto che copre e' MUTO.

    `LEZIONI.md` §1.9: *«uno zero che vuol dire "non ho letto" e uno zero che
    vuol dire "non e' successo niente" non devono avere la stessa faccia»*.
    `[M]` 23 agosto 2026: `righe_registro()` tornava 0 perche' un `< file` in
    coda rubava lo stdin a `sudo -S` (vedi `catena_root()`), e da li' in poi
    **ogni** numero del lato server era cumulativo dall'accensione — compreso
    `attese_a_vuoto`, che e' la colonna con cui `p_I1` decide se rifiutarsi.
    ⇒ Un banco che tira dritto con quello zero non e' un banco: da' un verde a
      una misura che non ha fatto.

    ⚠ Vale a OGNI gradino, anche a quelli di diagnosi: non e' una promessa del
      prodotto, e' la condizione perche' i numeri siano di questo giro.
    """
    s = n.get("server") or {}
    if s.get("registro_non_letto"):
        return _muto("%s ⇒ NON GIUDICO questo giro col lato server"
                     % s["registro_non_letto"])
    if not s:
        return _muto("questo giro non porta i conti del lato server")
    if "riga0" in s:
        return _si("il registro e' stato letto da riga %d in poi: i conti del "
                   "server sono DI QUESTO GIRO, non dall'accensione" % s["riga0"])
    return _si("i conti del lato server ci sono")


def p_niente_stacco(n):
    """⛔ L'UNICO obbligo che vale ANCHE sotto il pavimento — §3.1-bis:
       *«non e' un rifiuto: il divieto di staccare resta intero»*.

    ⚠ E non basta «sono arrivati dei fotogrammi»: un giro che muore a meta'
      consegna dei fotogrammi buonissimi per meta' del tempo.  ⇒ Si guarda
      quanto e' DURATO contro quanto era stato chiesto.
    """
    # ⛔⛔ PRIMA DI TUTTO: un giornale vuoto perche' NON L'HO LETTO non e' un
    #     giornale vuoto perche' non e' arrivato niente (`LEZIONI.md` §1.9).
    #     `[M]` 23 ago 2026: questo predicato ha dato rosso a una sessione viva
    #     — 797 fotogrammi spediti e presi — solo perche' il lettore di §11.1
    #     non era partito.  ⇒ Qui ci si rifiuta, e la ragione e' quella vera.
    if n.get("traccia_non_letta"):
        return _muto("%s — il giornale e' vuoto perche' NON L'HO LETTO, e non "
                     "perche' la sessione sia morta: NON GIUDICO"
                     % n["traccia_non_letta"])
    vissuto, chiesto = n.get("vissuto_s"), n.get("chiesto_s")
    if not chiesto:
        return _muto("non so quanto era stato chiesto")
    if not n.get("fotogrammi_grezzi"):
        return _no("nessun fotogramma in %.0f s: la sessione non ha consegnato "
                   "niente" % chiesto)
    if vissuto is None:
        return _muto("non so quanto e' durata la consegna")
    if vissuto < 0.90 * chiesto:
        return _no("la consegna e' durata %.1f s su %.0f chiesti: si e' staccata"
                   % (vissuto, chiesto))
    return _si("ha consegnato per %.1f s su %.0f chiesti: non si e' staccata"
               % (vissuto, chiesto))


def p_pavimento_ritmo(n):
    """⭐ `DECISIONI.md` §2.1 + §3.1-bis, e insieme: **su una linea da 20 Mbit/s
       un ritmo sotto i 25 al secondo e' un DIFETTO**, non una degradazione
       riuscita.

    ⛔ E sono DUE gambe, perche' una sola si fa ingannare:
       · la **media** a regime;
       · il **minimo su finestra di un secondo**, che e' l'unica che vede il
         buco dentro una media buona.
    """
    if not _ha_misurato(n):
        return _muto(n.get("esito", "non ho misurato"))
    fps, fin = n["fps"], n["fps_finestra_min"]
    if fin is None:
        return _muto("meno di una finestra intera: il minimo non esiste")
    if fps < PAVIMENTO_FPS:
        return _no("media %.2f/s sotto il pavimento di %.0f/s (§2.1)"
                   % (fps, PAVIMENTO_FPS))
    if fin < PAVIMENTO_FINESTRA:
        return _no("media %.2f/s va bene, ⛔ ma c'e' un secondo con %.0f "
                   "fotogrammi: la media nascondeva il buco" % (fps, fin))
    return _si("media %.2f/s e peggior secondo %.0f/s, sopra il pavimento di "
               "%.0f/s" % (fps, fin, PAVIMENTO_FPS))


def p_degrada_nel_tempo(n):
    """⛔ §3.3: *«si calano i FOTOGRAMMI. Mai sgranare, mai staccare»* — e la
       forma peggiore di degradazione non e' sgranare: e' **il flusso di sole
       chiavi**.

    `[M]` 21 agosto 2026: sui giri stretti i fotogrammi consegnati erano
    **144/144, 149/149** tutti chiavi, contro **2 su 1 019** a 15 Mbit/s.  Ogni
    abbandono di §5.1 accende il debito di §5.2, il debito fa chiedere una
    chiave, la chiave riempie la finestra, e si ricomincia.  ⇒ Il flusso degrada
    **nello spazio E nel tempo insieme**, che e' l'opposto di quel che §3.3
    chiede.
    """
    if not _ha_misurato(n):
        return _muto(n.get("esito", "non ho misurato"))
    if n["chiavi"] + n["delta"] == 0:
        return _muto("nessun fotogramma classificato")
    q = n["quota_delta"]
    if q < QUOTA_DELTA:
        return _no("delta %.1f %% (%d chiavi su %d): il flusso sta degenerando "
                   "in chiavi — e' la spirale di §5.2"
                   % (q * 100, n["chiavi"], n["chiavi"] + n["delta"]))
    return _si("delta %.1f %% (%d chiavi su %d): degrada nel tempo, non in chiavi"
               % (q * 100, n["chiavi"], n["chiavi"] + n["delta"]))


def p_ritardo_non_scappa(n):
    """⛔ `SPECIFICHE.md:128`: *«ogni memoria intermedia compra fluidita' e vende
       risposta»*, e il ritardo pesa piu' dei fotogrammi.

    ⚠ Qui si misura la **deriva** (vedi l'intestazione), non l'anello.  La
      soglia e' ancorata a una misura, non scelta: l'anello intero della fase 8
      vale `[M]` **55,20 ms**; una deriva di 250 ms vale **quattro anelli**, e a
      quel punto non e' piu' un ritardo, e' una coda.
    """
    if not _ha_misurato(n):
        return _muto(n.get("esito", "non ho misurato"))
    fine, mas = n["deriva_fine_ms"], n["deriva_max_ms"]
    if fine > DERIVA_FINE_MS:
        return _no("la consegna e' rimasta indietro di %.0f ms rispetto alla "
                   "cattura (tetto %.0f)" % (fine, DERIVA_FINE_MS))
    if mas > DERIVA_MAX_MS:
        return _no("la deriva ha toccato %.0f ms (tetto %.0f), pur rientrando a "
                   "%.0f" % (mas, DERIVA_MAX_MS, fine))
    return _si("deriva finale %.0f ms, massima %.0f: la coda non e' scappata"
               % (fine, mas))


def _perdita_dichiarata(*giri, **kw):
    """La perdita della linea sotto questi giri, in %, oppure `None` se NON LO SO.

    ⛔ Non si assume: si legge da quel che il giro porta con se' — e chi lo
       scrive e' `giro()`, che se lo fa dire dal **qdisc installato** (vedi
       `_linea_del_giro()`).  ⚠ Cosi' vale anche quando il giro l'ha girato
       qualcun altro con un `netem` suo: `09-b76-rete-cattiva.py` chiama
       `B70.giro()` con `loss` addosso, e questa funzione lo vede lo stesso.

    ⭐ E `None` NON e' zero: se non so se la linea perde, la premessa della gamba
       degli abbandoni non e' verificata, e una premessa non verificata non da'
       il diritto di dare rosso.
    """
    esplicita = kw.get("perdita_pc")
    if esplicita is not None:
        return float(esplicita), "dichiarata da chi mi ha chiamato"
    for g in giri:
        for dove, chiave in (("linea", "perdita_pc"), ("sonda", "persi_pc")):
            v = ((g or {}).get(dove) or {}).get(chiave)
            if v is not None:
                return float(v), "letta da «%s.%s» del giro" % (dove, chiave)
    return None, ("nessun giro della coppia dichiara la perdita della linea")


def p_I1(ferma, mossa, perdita_pc=None):
    """⛔⛔ L'INVARIANTE I1, ED E' IL PRIMO PREDICATO DELLA FASE.

    `SPECIFICHE.md` §8.2: *«Il ritmo non cala mai per prudenza, per risparmio o
    perche' la scena e' ferma»*.  E' la ferita da cui nasce tutta la fase: in v1
    il controllo di bitrate *«su un desktop poco mosso scendeva a 2-6 Mbit/s,
    contento di risparmiare»*.

    ⛔ **La prima cosa che fa questo predicato e' rifiutarsi di giudicare**
       quando i due giri non sono confrontabili.  Se il compositore ha
       consegnato al server molti meno fotogrammi nel giro fermo, il ritmo piu'
       basso e' **a monte di noi**: attribuirlo a I1 sarebbe esattamente
       l'errore di `LEZIONI.md` §1.26, dove un numero vero e' stato dato alla
       causa sbagliata perche' la causa era comoda.

    ⭐ E poi sono DUE gambe, perche' nessuna delle due basta:
       · **i fotogrammi al secondo** — la grandezza che l'utente sente.  ⚠ Vale
         sempre: e' un confronto fra due giri sulla **stessa** linea, quindi
         qualunque guasto della linea c'e' in tutt'e due e si cancella;
       · **la resa `spediti/consegnati` e gli abbandoni** — perche' la cadenza
         puo' essere identica mentre noi buttiamo: a scena ferma non c'e'
         nessuna congestione che giustifichi un abbandono, quindi ne bastano
         **zero**.

    ⛔⛔ E LA SECONDA GAMBA HA UNA PREMESSA, che fino al 23 agosto 2026 era
        implicita e per questo **falsa senza dirlo**: *«a scena ferma non c'e'
        congestione che giustifichi un abbandono»* vale su una linea che **non
        perde**.  Su una linea che perde il 2 % (`casa-cattiva`, `[M]` 23 ago)
        gli abbandoni li giustifica la perdita, e quella sera questa gamba ha
        dato un rosso che non era un difetto del prodotto — con la gamba dei
        fotogrammi/s che passava (ferma **10,13/s** contro mossa **7,78/s**: la
        ferma andava piu' veloce).
    ⇒ La gamba NON si toglie e non si allarga: si CONDIZIONA.  Su linea senza
      perdita da' rosso come prima; su linea che perde — o su una linea di cui
      non so se perde — **si rifiuta di giudicarla** e lo scrive.  ⚠ E se
      intanto la prima gamba e' rossa, il rosso resta: la perdita spiega gli
      abbandoni, non spiega un ritmo che cala quando la scena si ferma.
    """
    if not (_ha_misurato(ferma) and _ha_misurato(mossa)):
        return _muto("uno dei due giri della coppia non ha misurato: "
                     "ferma «%s», mossa «%s»"
                     % (ferma.get("esito"), mossa.get("esito")))
    cf = (ferma.get("server") or {}).get("consegnati")
    cm = (mossa.get("server") or {}).get("consegnati")
    if not cf or not cm:
        return _muto("il registro non ha dato i «consegnati a RCP» dei due giri: "
                     "senza denominatore la coppia non e' confrontabile")
    scarto = abs(cf - cm) / float(max(cf, cm))
    if scarto > I1_CONSEGNATI:
        return _muto("il compositore ha consegnato %d fotogrammi a scena ferma "
                     "contro %d a scena mossa (%.0f %% di scarto): la differenza "
                     "e' A MONTE di noi e NON la giudico come I1" % (cf, cm, scarto * 100))
    # ⭐⭐ LA GUARDIA MIGLIORE, e non deduce: le ATTESE A VUOTO del figlio.
    #     Se a scena ferma abbiamo chiesto un fotogramma e non ce n'era, il
    #     ritmo piu' basso e' del compositore e il prodotto non c'entra.  ⛔ E'
    #     la distinzione che `04-b32-ritmo.py` esiste per fare, e la riga
    #     `figlio.c:2669` porta la volta in cui e' stata sbagliata al contrario:
    #     *«la tesi era falsa: Mutter aveva i fotogrammi, e noi non eravamo li'
    #     a prenderli»*.
    vf = ((ferma.get("server") or {}).get("cattura") or {}).get("attese_a_vuoto")
    vm = ((mossa.get("server") or {}).get("cattura") or {}).get("attese_a_vuoto")
    if vf is not None and vm is not None and vf > max(20, 3 * (vm + 1)):
        return _muto("a scena ferma il figlio ha aspettato A VUOTO %d volte "
                     "(contro %d a scena mossa): il fotogramma non c'era, e il "
                     "ritmo piu' basso e' del COMPOSITORE — non lo giudico "
                     "come I1" % (vf, vm))
    # ── PRIMA GAMBA: il ritmo.  Vale su qualunque linea (vedi la docstring) ──
    guai = []
    if ferma["fps"] < mossa["fps"] * (1.0 - I1_TOLLERANZA):
        guai.append("il ritmo a scena FERMA e' %.2f/s contro %.2f/s a scena "
                    "mossa: cala quando non deve" % (ferma["fps"], mossa["fps"]))
    # ── SECONDA GAMBA: gli abbandoni.  ⛔ E PRIMA la sua premessa ────────────
    buttati = []
    ab = (ferma.get("server") or {}).get("abbandonati")
    if ab:
        buttati.append("a scena ferma il server ha abbandonato %d fotogrammi" % ab)
    sp = (ferma.get("server") or {}).get("spediti")
    if sp is not None and cf:
        resa = sp / float(cf)
        if resa < RESA_FERMA:
            buttati.append("a scena ferma sono usciti %d fotogrammi su %d "
                           "consegnati a RCP (resa %.3f, sotto %.2f)"
                           % (sp, cf, resa, RESA_FERMA))
    perdita, da_dove = _perdita_dichiarata(ferma, mossa, perdita_pc=perdita_pc)
    premessa = (perdita == 0.0)
    if buttati and not premessa:
        motivo = ("la premessa di questa gamba — «a scena ferma non c'e' "
                  "congestione che giustifichi un abbandono» — vale SOLO su una "
                  "linea senza perdita, e qui %s (%s)"
                  % ("la linea perde il %.2f %%" % perdita if perdita is not None
                     else "NON SO se la linea perde", da_dove))
        if guai:
            # ⚠ Il rosso del ritmo resta: la perdita spiega gli abbandoni, non
            #   spiega un ritmo che cala quando la scena si ferma.
            return _no("%s · ⚠ e gli abbandoni NON li giudico (%s): %s"
                       % (" · ".join(guai), motivo, "; ".join(buttati)))
        return _muto("%s, ma %s ⇒ NON GIUDICO gli abbandoni. ⭐ La gamba dei "
                     "fotogrammi/s ha retto: ferma %.2f/s contro mossa %.2f/s"
                     % ("; ".join(buttati), motivo, ferma["fps"], mossa["fps"]))
    guai += ["%s, e su una linea senza perdita non c'e' congestione che li "
             "giustifichi" % b for b in buttati]
    if guai:
        return _no(" · ".join(guai))
    return _si("scena ferma %.2f/s contro mossa %.2f/s, consegnati %d contro %d, "
               "zero abbandoni a scena ferma (linea %s): I1 tiene"
               % (ferma["fps"], mossa["fps"], cf, cm,
                  "senza perdita" if premessa else
                  "con perdita %s — ma non c'era niente da giustificare"
                  % ("%.2f %%" % perdita if perdita is not None else "ignota")))


# I predicati che si applicano a un giro solo, in ordine.
PREDICATI_GIRO = [
    # ⛔ Per primo, perche' se questo si rifiuta i tre numeri del lato server
    #    che seguono non sono di questo giro.  E vale ovunque (`False`).
    ("il registro e' di QUESTO giro (§1.9)", p_registro_letto, False),
    ("non stacca (§3.1-bis, vale anche sotto il pavimento)", p_niente_stacco, False),
    ("il pavimento del ritmo (§2.1: 25/s)", p_pavimento_ritmo, True),
    ("degrada nel tempo, non in chiavi (§3.3)", p_degrada_nel_tempo, True),
    ("il ritardo non scappa (la deriva)", p_ritardo_non_scappa, True),
]


def giudica_giro(n, requisito):
    """⛔ Ai gradini di diagnosi si MISURA tutto e si PRETENDE una cosa sola.

    Chiamare rosso un ritmo basso a 10 Mbit/s vorrebbe dire misurare una
    promessa che il prodotto non fa (§3.1-bis) — cioe' ripetere l'errore 2 di v1
    col segno cambiato.  ⇒ I predicati che non sono requisito a quel gradino
    girano lo stesso e il loro esito si SCRIVE, marcato «diagnosi».
    """
    fuori = []
    for nome, f, solo_se_requisito in PREDICATI_GIRO:
        passa, perche = f(n)
        conta = requisito or not solo_se_requisito
        fuori.append({"predicato": nome, "passa": passa, "perche": perche,
                      "conta": conta})
    return fuori


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL CONTROLLO POSITIVO — «come fa questo banco a sapere di saper vedere?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Sul modello di `banchi/07-b64-orecchio.py --certifica`, e per la stessa
#    ragione: *«un banco che non sa vedere il difetto che cerca non ha diritto
#    al verde»* (`PIANO.md` §0.3.4).
#
# ⭐ E i casi NON passano numeri gia' pronti ai predicati: fabbricano dei
#    GIORNALI e li fanno passare da `misura()`, che e' la stessa funzione che
#    gira sui giri veri.  ⇒ Un inganno che vive nella RIDUZIONE — ed e' il caso
#    2, la media che nasconde il buco — viene visto.  Certificare i soli
#    predicati certificherebbe meta' dello strumento.
def _fab(tratti, byte=25000, chiave_ogni=0, deriva_ms_per_fotogramma=0.0,
         numero_da=1, salta_ogni=0):
    """Fabbrica un giornale.  `tratti` = [(fps, secondi), ...].

    ⛔ `arrivo_ms` e' l'orologio del CLIENT, `istante_us` quello del SERVER: la
       deriva si costruisce allontanando il secondo dal primo, che e' quel che
       succede quando la coda cresce.
    """
    g, t_arr, t_cat, numero, i = [], 0.0, 0.0, numero_da, 0
    for fps, secondi in tratti:
        passo = 1000.0 / fps
        for _ in range(int(round(fps * secondi))):
            chiave = (chiave_ogni and i % chiave_ogni == 0) or i == 0
            salta = salta_ogni and i and i % salta_ogni == 0
            if salta:
                numero += 1          # ⭐ il buco nella successione: §6.2
            g.append({"numero": numero, "chiave": bool(chiave), "tipo":
                      0x0301 if chiave else 0x0302, "codec": 3,
                      "l": 1920, "a": 1080, "byte": byte,
                      "istante_us": int(t_cat * 1000.0),
                      "arrivo_ms": int(round(t_arr))})
            numero += 1
            i += 1
            t_arr += passo
            t_cat += passo - deriva_ms_per_fotogramma
    return g


def _con_linea(n, perdita_pc):
    """Appiccica a un giro finto la linea che `giro()` gli scriverebbe dal qdisc."""
    n["linea"] = {"perdita_pc": perdita_pc,
                  "come": "netem con «loss %s%%»" % perdita_pc if perdita_pc
                          else "netem senza `loss`"}
    return n


def certifica():
    """⛔ L'atteso e' scritto PRIMA, e i casi 2, 4, 5 e 6 sono quelli che
       rendono credibile un verde falso."""
    print("⭐ CERTIFICAZIONE DEL BANCO DEL RITMO — l'atteso e' scritto PRIMA\n")
    print("   ⛔ Nessun contatto con la macchina di prova: qui si prova lo "
          "STRUMENTO,\n      non il prodotto.\n")

    SRV = {"consegnati": 900, "non_spediti": 0, "spediti": 900,
           "abbandonati": 0, "annunci_tela": 0}
    FILO = {"byte": 90 * 1000 * 1000, "secondi": 30.0, "byte_per_pacchetto": 1452.0}

    casi = []

    # 0 · IL DENOMINATORE.  Se questo non e' verde, nessun rosso vale niente.
    g = _fab([(60, 33)], chiave_ogni=0)
    casi.append(("0-sano — 60/s per 33 s, una chiave sola",
                 misura(g, 33, SRV, FILO),
                 {"il registro": True, "non stacca": True, "il pavimento": True,
                  "degrada nel tempo": True, "il ritardo": True}))

    # 1 · IL DIFETTO NUDO: il ritmo sotto il pavimento.
    g = _fab([(18, 33)])
    casi.append(("1-⛔ ritmo 18/s uniforme: sotto il pavimento di 25",
                 misura(g, 33, SRV, FILO),
                 {"il registro": True, "non stacca": True, "il pavimento": False,
                  "degrada nel tempo": True, "il ritardo": True}))

    # 2 · ⛔⛔ LA MEDIA CHE NASCONDE IL BUCO.
    #     10 s a 45/s + 20 s a 17,5/s = 800 fotogrammi in 30 s = **26,7/s**,
    #     cioe' SOPRA il pavimento.  Un banco che guardasse la sola media
    #     scriverebbe «verde» su venti secondi di desktop a scatti.
    #     ⇒ Deve dare rosso, e per la FINESTRA.
    g = _fab([(45, 13), (17.5, 20)])
    casi.append(("2-⛔⛔ la media che nasconde il buco: 45/s poi 17,5/s "
                 "(media sopra il pavimento)",
                 misura(g, 33, SRV, FILO),
                 {"il registro": True, "non stacca": True, "il pavimento": False,
                  "degrada nel tempo": True, "il ritardo": True}))

    # 3 · ⛔ IL FLUSSO DI SOLE CHIAVI A RITMO BUONO.
    #     30/s: il pavimento e' contento.  Ma sono tutte chiavi — e' la spirale
    #     di §5.2 misurata il 21 agosto (144/144).  Solo §3.3 lo vede.
    g = _fab([(30, 33)], chiave_ogni=1)
    casi.append(("3-⛔ 30/s ma TUTTE CHIAVI: il ritmo assolve, §3.3 no",
                 misura(g, 33, SRV, FILO),
                 {"il registro": True, "non stacca": True, "il pavimento": True,
                  "degrada nel tempo": False, "il ritardo": True}))

    # 4 · ⛔⛔ IL RITMO STA IN PIEDI E IL RITARDO E' DISTRUTTO.
    #     E' `LEZIONI.md` §6.2 nella sua forma piu' cattiva: 30 fotogrammi al
    #     secondo consegnati puntuali, e ognuno e' 4 ms piu' vecchio del
    #     precedente.  Dopo 30 s la consegna e' indietro di ~3,6 s.
    #     ⇒ Un banco che contasse i soli fotogrammi darebbe verde.
    g = _fab([(30, 33)], deriva_ms_per_fotogramma=4.0)
    casi.append(("4-⛔⛔ 30/s puntuali e la deriva che scappa (+4 ms a "
                 "fotogramma): il ritmo assolve, il ritardo no",
                 misura(g, 33, SRV, FILO),
                 {"il registro": True, "non stacca": True, "il pavimento": True,
                  "degrada nel tempo": True, "il ritardo": False}))

    # 5 · ⛔ LO STACCO A META'.  Dodici secondi di fotogrammi ottimi su trenta
    #     chiesti: ogni grandezza «per secondo» e' buona, e la sessione e'
    #     morta.  ⇒ E' l'unico predicato che vale anche sotto il pavimento.
    g = _fab([(60, 12)])
    casi.append(("5-⛔ la sessione muore a 12 s su 33 chiesti: tutte le medie "
                 "sono buone",
                 misura(g, 33, SRV, FILO),
                 {"il registro": True, "non stacca": False, "il pavimento": True,
                  "degrada nel tempo": True, "il ritardo": True}))

    # 6 · ⛔⛔ IL VUOTO.  E' il caso R7a dell'orecchio, trasportato: un banco che
    #     rispondesse «zero abbandoni, zero chiavi, nessuna violazione» su un
    #     giro senza fotogrammi darebbe **il voto massimo al silenzio**.
    #     ⇒ Ogni predicato deve RIFIUTARSI, tranne «non stacca», che qui e' un
    #       rosso vero: non e' arrivato niente.
    casi.append(("6-⛔⛔ il VUOTO: zero fotogrammi (il voto massimo al silenzio)",
                 misura([], 33, SRV, FILO),
                 {"il registro": True, "non stacca": False, "il pavimento": None,
                  "degrada nel tempo": None, "il ritardo": None}))

    # 6b · ⛔⛔ LO ZERO CHE VUOL DIRE «NON HO LETTO» — `LEZIONI.md` §1.9, e la
    #      cura 2 del 23 agosto 2026.  Se `righe_registro()` torna 0 (il `< file`
    #      che rubava la parola a `sudo -S`), `conti_del_server()` leggerebbe il
    #      registro DALL'ACCENSIONE del server: `attese_a_vuoto` diventerebbe
    #      cumulativo, e con lui la colonna su cui `p_I1` decide se rifiutarsi.
    #      ⇒ Il banco deve RIFIUTARSI, non tirare dritto.  ⭐ E il rifiuto si
    #        prova sulla funzione VERA — `conti_del_server(0)` — non su un dizionario
    #        scritto a mano: e' la guardia sul percorso che il giro vero fa.
    casi.append(("6b-⛔⛔ il registro NON letto (righe_registro() → 0): i conti "
                 "del server sarebbero cumulativi dall'accensione",
                 misura(_fab([(30, 33)]), 33, conti_del_server(0), FILO),
                 {"il registro": None, "non stacca": True, "il pavimento": True,
                  "degrada nel tempo": True, "il ritardo": True}))

    # 6c · ⛔⛔ LA TERZA FACCIA DELLO ZERO, e l'ha trovata il giro VERO del
    #      23 agosto 2026: il lettore di §11.1 non parte (gli mancava
    #      `01-b4-validatore.py` nell'albero), il giornale resta vuoto, e un
    #      giornale vuoto e' identico a «la sessione non ha consegnato niente».
    #      `[M]` quella sera il banco ha dato ROSSO a «non stacca» su un giro in
    #      cui il server aveva spedito **797** fotogrammi e il cliente li aveva
    #      presi.  ⇒ «Non l'ho letto» deve rifiutarsi, non accusare il prodotto.
    #      ⚠ E il confronto con il caso 6 e' il punto: **stesso giornale vuoto**,
    #        esiti opposti, perche' la ragione del vuoto e' diversa.
    n_muta = misura([], 33, SRV, FILO)
    n_muta["traccia_non_letta"] = "⛔ LA TRACCIA §11.1 NON SI E' LETTA: prova"
    n_muta["esito"] = "NON HO NIENTE DA GIUDICARE — traccia non letta"
    casi.append(("6c-⛔⛔ il giornale vuoto perche' NON L'HO LETTO (contro il "
                 "caso 6, vuoto perche' non e' arrivato niente)",
                 n_muta,
                 {"il registro": True, "non stacca": None, "il pavimento": None,
                  "degrada nel tempo": None, "il ritardo": None}))

    verde = True
    for nome, n, atteso in casi:
        print("  %s" % nome)
        for etichetta, f, _s in PREDICATI_GIRO:
            corto = etichetta.split(" (")[0]
            chiave = ("il registro" if corto.startswith("il registro") else
                      "non stacca" if corto.startswith("non stacca") else
                      "il pavimento" if corto.startswith("il pavimento") else
                      "degrada nel tempo" if corto.startswith("degrada") else
                      "il ritardo")
            passa, perche = f(n)
            att = atteso[chiave]
            bene = (passa is att)
            verde = verde and bene
            segno = ("OK " if bene else "⛔ ")
            print("      %s%-22s atteso %-5s visto %-5s — %s"
                  % (segno, chiave, att, passa, perche[:96]))
        print()

    # ── LA COPPIA DI I1, che ha bisogno di due giri e non di uno ────────────
    print("  ── I1, e serve la COPPIA: scena ferma / scena mossa ──\n")
    srv = lambda cons, sped, abb=0: {"consegnati": cons, "spediti": sped,
                                     "abbandonati": abb, "non_spediti": cons - sped,
                                     "annunci_tela": 0}
    coppie = [
        # 7 · ⭐ I1 SANO: stessa cadenza, niente abbandoni.
        ("7-⭐ I1 sano: ferma 30/s e mossa 30/s, consegnati confrontabili",
         misura(_fab([(30, 33)]), 33, srv(1000, 1000), FILO),
         misura(_fab([(30, 33)]), 33, srv(1010, 1010), FILO),
         True),
        # 8 · ⛔ IL DIFETTO CHE LA FASE ESISTE PER TROVARE: a scena ferma il
        #     ritmo cala, e il compositore ci ha consegnato lo stesso.
        ("8-⛔⛔ I1 rotta: ferma 18/s contro mossa 30/s, consegnati uguali",
         misura(_fab([(18, 33)]), 33, srv(1000, 620, 40), FILO),
         misura(_fab([(30, 33)]), 33, srv(1010, 1010), FILO),
         False),
        # 9 · ⭐⭐ IL FALSO ROSSO, ed e' il caso senza cui questo banco
        #     accuserebbe il prodotto di un difetto del COMPOSITORE.  Stessi
        #     ritmi del caso 8 — ma a scena ferma Mutter ha consegnato 550
        #     fotogrammi contro 1 010.  ⇒ NON GIUDICO, e non «rosso».
        ("9-⭐⭐ il falso rosso: stessi ritmi, ma a scena ferma il compositore "
         "ha consegnato 550 contro 1 010",
         misura(_fab([(18, 33)]), 33, srv(550, 550), FILO),
         misura(_fab([(30, 33)]), 33, srv(1010, 1010), FILO),
         None),
        # 10 · ⛔ LA COPPIA MUTA: uno dei due giri non ha misurato.
        ("10-⛔ la coppia monca: il giro a scena ferma non ha fotogrammi",
         misura([], 33, srv(1000, 1000), FILO),
         misura(_fab([(30, 33)]), 33, srv(1010, 1010), FILO),
         None),
        # 10b · ⭐⭐ IL SECONDO FALSO ROSSO, e stavolta i «consegnati» si
        #      assomigliano — la prima guardia lascerebbe passare.  A dirlo e'
        #      la colonna che il figlio scrive da solo: **900 attese a vuoto**
        #      a scena ferma contro 3 a scena mossa.  ⇒ NON GIUDICO.
        ("10b-⭐⭐ il falso rosso che i «consegnati» non vedono: 900 attese a "
         "VUOTO a scena ferma (il fotogramma non c'era)",
         misura(_fab([(18, 33)]), 33,
                dict(srv(950, 950), cattura={"catturati": 950, "chiavi": 1,
                                             "attese_a_vuoto": 900}), FILO),
         misura(_fab([(30, 33)]), 33,
                dict(srv(1010, 1010), cattura={"catturati": 1010, "chiavi": 1,
                                               "attese_a_vuoto": 3}), FILO),
         None),
        # ══ LA CURA 3, e sono QUATTRO casi perche' una gamba condizionata si
        #    prova in tutt'e due i versi: deve tacere dove la premessa manca, e
        #    deve saper DARE ROSSO dove la premessa c'e'.
        #
        # 10c · ⛔ LA GAMBA CHE DEVE MORDERE.  Linea SENZA perdita, il ritmo a
        #      scena ferma sta in piedi (anzi corre di piu'), e il server butta
        #      lo stesso: e' I1 rotta nella forma che i fotogrammi/s non vedono.
        ("10c-⛔ linea SENZA perdita e il server butta a scena ferma: la gamba "
         "degli abbandoni deve dare ROSSO",
         _con_linea(misura(_fab([(10.13, 33)]), 33, srv(1000, 960, 40), FILO), 0.0),
         _con_linea(misura(_fab([(7.78, 33)]), 33, srv(1010, 1010), FILO), 0.0),
         False),
        # 10d · ⭐⭐ IL CASO MISURATO IL 23 AGOSTO 2026 su `casa-cattiva` (2 % di
        #      perdita): **gli stessi identici numeri** del 10c.  La premessa
        #      *«a scena ferma non c'e' congestione che li giustifichi»* qui e'
        #      FALSA — gli abbandoni li giustifica la perdita.  ⇒ NON GIUDICO.
        #      ⛔ E il rosso che questo caso toglie non e' un rosso del prodotto.
        ("10d-⭐⭐ gli STESSI numeri su una linea che perde il 2 %: la premessa "
         "e' falsa e il banco deve RIFIUTARSI, non dare rosso",
         _con_linea(misura(_fab([(10.13, 33)]), 33, srv(1000, 960, 40), FILO), 2.0),
         _con_linea(misura(_fab([(7.78, 33)]), 33, srv(1010, 1010), FILO), 2.0),
         None),
        # 10e · ⛔ E «non so se perde» NON e' «non perde»: una premessa non
        #      verificata non da' il diritto di dare rosso (§1.9, di nuovo).
        ("10e-⛔ gli stessi numeri su una linea di cui NON SO se perde: "
         "una premessa non verificata non autorizza un rosso",
         misura(_fab([(10.13, 33)]), 33, srv(1000, 960, 40), FILO),
         misura(_fab([(7.78, 33)]), 33, srv(1010, 1010), FILO),
         None),
        # 10f · ⛔⛔ E LA CURA NON DEVE DIVENTARE UN'AMNISTIA.  Linea che perde il
        #      2 %, ma stavolta il ritmo a scena ferma CALA (5,0/s contro 7,78):
        #      la perdita spiega gli abbandoni, non spiega quello.  ⇒ ROSSO.
        ("10f-⛔⛔ linea che perde il 2 % MA il ritmo a scena ferma cala "
         "(5,00/s contro 7,78/s): la perdita non lo giustifica — ROSSO",
         _con_linea(misura(_fab([(5.0, 33)]), 33, srv(1000, 960, 40), FILO), 2.0),
         _con_linea(misura(_fab([(7.78, 33)]), 33, srv(1010, 1010), FILO), 2.0),
         False),
    ]
    for nome, ferma, mossa, att in coppie:
        passa, perche = p_I1(ferma, mossa)
        bene = (passa is att)
        verde = verde and bene
        print("  %s%s\n      atteso %-5s visto %-5s — %s"
              % ("OK  " if bene else "⛔  ", nome, att, passa, perche[:150]))
    print()

    # 11 · ⛔ IL FILO NON LETTO — `CODER.md` §3.10.  Se il contatore del qdisc
    #      non si e' potuto leggere, il banco deve dire «non letto», non «0».
    n = misura(_fab([(30, 33)]), 33, SRV, None)
    bene = (n.get("mbit_s_filo") is None and "filo_non_letto" in n)
    verde = verde and bene
    print("  %s11-⛔ il contatore del filo non letto: si dice «non letto», non "
          "«0 Mbit/s» — visto mbit_s_filo=%s"
          % ("OK  " if bene else "⛔  ", n.get("mbit_s_filo")))

    # 12 · ⭐ LA SECONDA GAMBA DEGLI ABBANDONI: i buchi nel `numero`, che si
    #      leggono dal lato che RICEVE e non passano dal registro del server.
    n = misura(_fab([(30, 33)], salta_ogni=25), 33, SRV, FILO)
    atteso_buchi = (n["fotogrammi"] // 25)
    bene = n["buchi_numero"] >= atteso_buchi - 2
    verde = verde and bene
    print("  %s12-⭐ i buchi nella successione dei `numero` (§6.2): attesi ~%d, "
          "visti %d" % ("OK  " if bene else "⛔  ", atteso_buchi, n["buchi_numero"]))

    # 13 · ⭐⭐ IL GIRO INTERO DELLO STRUMENTO: dalla traccia al giornale.
    #      I casi 0-12 provano la RIDUZIONE su giornali gia' pronti; questo prova
    #      il pezzo che li fabbrica — il lettore di §11.1 — e lo prova **sul
    #      codice che verra' spedito sulla macchina**, non su una copia.
    #      ⛔ E il formato della traccia finta non lo scrivo io: lo prendo
    #        dall'ARBITRO (`01-b4-validatore.py`), che e' l'unico posto dove
    #        §11.1 e' scritta.  Una prova in cui scrivo e rileggo il MIO formato
    #        non proverebbe niente sul formato vero.
    bene, perche = _certifica_lettore()
    verde = verde and bene
    print("  %s13-⭐⭐ dalla TRACCIA §11.1 al giornale, col lettore vero: %s"
          % ("OK  " if bene else "⛔  ", perche))

    # 14-15 · ⛔⛔ LE DUE CURE DELLO STDIN DI `sudo -S`, provate DAVVERO.
    verde = _certifica_stdin_di_sudo() and verde

    print("\n== %s" % ("⭐ IL BANCO SA VEDERE I DIFETTI CHE CERCA"
                       if verde else
                       "⛔⛔ IL BANCO NON SA VEDERE QUEL CHE CERCA: non si "
                       "creda a nessun suo verde"))
    return 0 if verde else 1


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ LA PROVA DELLE CURE 1 E 2 — e NON e' un confronto di stringhe
# ═══════════════════════════════════════════════════════════════════════════
#
# Un banco che si limitasse a confrontare la riga costruita con una riga attesa
# proverebbe che la scrivo come l'ho pensata, non che FUNZIONA.  ⇒ Qui la catena
# si fa girare per davvero, in locale, con un `sudo` **finto** che si comporta
# come quello vero nell'unica cosa che conta: legge la parola dallo **stdin** e
# poi esegue quel che gli resta.  Se la parola non gli arriva, fallisce
# esattamente come sulla macchina di prova — *«3 incorrect password attempts»*.
#
# ⭐ E ogni cura si prova in DUE versi: la forma vecchia deve FALLIRE (una cura
#    che non e' mai stata vista fallire non e' provata) e la nuova deve reggere.
SUDO_FINTO = r'''#!/bin/sh
# ⛔ Il `sudo` finto: non da' privilegi, imita il solo stdin di `-S`.
while [ "$1" = "-S" ] || [ "$1" = "-p" ]; do
  if [ "$1" = "-p" ]; then shift 2; else shift; fi
done
printf '%s\n' "$*" >> "$FINTO_CHIAMATE"
IFS= read -r parola || parola=""
if [ "$parola" != "$FINTO_PAROLA" ]; then
  echo "sudo: 3 incorrect password attempts" >&2
  exit 1
fi
exec "$@"
'''


def _certifica_stdin_di_sudo():
    """I casi 14 e 15: le due forme in cui `sudo -S` perde la parola."""
    import shutil, tempfile
    d = tempfile.mkdtemp(prefix="09-b70-sudo-")
    bidone = os.path.join(d, "bidone")
    os.makedirs(bidone)
    with open(os.path.join(bidone, "sudo"), "w") as f:
        f.write(SUDO_FINTO)
    os.chmod(os.path.join(bidone, "sudo"), 0o755)
    chiamate = os.path.join(d, "chiamate")

    def gira(riga):
        open(chiamate, "w").close()
        amb = dict(os.environ, PATH=bidone + ":" + os.environ.get("PATH", ""),
                   FINTO_CHIAMATE=chiamate, FINTO_PAROLA=PAROLA_SUDO)
        p = subprocess.run(["bash", "-c", riga], capture_output=True, env=amb)
        return (p.returncode, p.stdout.decode("utf-8", "replace"),
                open(chiamate).read().strip().splitlines())

    def vecchia(comando):
        """La forma di `07-b65-datagram.py:147`: un solo `sudo`, e la catena FUORI."""
        return "printf '%%s\\n' '%s' | sudo -S -p '' %s" % (PAROLA_SUDO, comando)

    verde = True

    # ── 14 · LA CATENA — `sudo` copre solo il PRIMO anello ──────────────────
    dentro = os.path.join(d, "dentro")
    catena = ("mkdir -p %s && printf '%%s' 'CIAO' > %s/f && wc -c < %s/f"
              % (dentro, dentro, dentro))
    _rc, out_v, ch_v = gira(vecchia(catena))
    shutil.rmtree(dentro, ignore_errors=True)
    _rc, out_n, ch_n = gira(catena_root(catena))
    # ⛔ La forma vecchia: `sudo` ha ricevuto SOLO il `mkdir`; il `printf`, il
    #    `>` e il `wc` sono girati da utente normale — e sulla macchina, dove
    #    `LAV` e' di root, e' li' che il lettore §11.1 non si scriveva.
    rotta = (len(ch_v) == 1 and "mkdir" in ch_v[0] and "printf" not in ch_v[0])
    # ⭐ La forma nuova: un solo `sudo`, e la catena INTERA dentro la sua shell.
    curata = (len(ch_n) == 1 and ch_n[0].startswith("bash -c ")
              and "mkdir" in ch_n[0] and "printf" in ch_n[0] and "wc" in ch_n[0]
              and out_n.strip() == "4")
    bene = rotta and curata
    verde = verde and bene
    print("  %s14-⛔ CURA 1 · la CATENA: la forma vecchia manda a root il solo "
          "«%s…» (il resto gira da utente); la nuova ne manda uno solo, con "
          "tutta la catena dentro — e stampa «%s» (atteso «4»)"
          % ("OK  " if bene else "⛔  ",
             (ch_v[0] if ch_v else "(niente)")[:24], out_n.strip()))

    # ── 15 · IL `< file` IN CODA — ruba lo stdin a `sudo`, e TACE ───────────
    reg = os.path.join(d, "registro.log")
    with open(reg, "w") as f:
        f.write("prima riga\nseconda\nterza\nquarta\n")
    comando = "wc -l < %s 2>/dev/null || echo 0" % reg
    rc_v, out_v, _ch = gira(vecchia(comando))
    rc_n, out_n, _ch = gira(catena_root(comando))
    # ⛔⛔ La forma vecchia stampa «0» — non «errore»: e' il difetto MUTO, ed e'
    #     quello che rendeva `attese_a_vuoto` cumulativo dall'accensione.
    rotta = (out_v.strip() == "0")
    curata = (out_n.strip() == "4")
    bene = rotta and curata
    verde = verde and bene
    print("  %s15-⛔⛔ CURA 2 · il «< file» in coda su un registro da 4 righe: "
          "la forma vecchia risponde «%s» (lo stdin rubato a sudo, e TACE), la "
          "nuova «%s»"
          % ("OK  " if bene else "⛔  ", out_v.strip(), out_n.strip()))

    # ── 15b · LA GUARDIA: uno zero non deve avere la faccia di una misura ───
    vero_root = globals()["root"]
    try:
        prove = [
            ("zero righe col server acceso", (0, "0\n", ""), None),
            ("sudo che rifiuta la parola", (1, "", "sudo: 3 incorrect password "
                                                   "attempts"), None),
            ("una risposta che non e' un numero", (0, "boh\n", ""), None),
            ("un registro vero da 12 345 righe", (0, "12345\n", ""), 12345),
        ]
        esiti = []
        for etichetta, risposta, atteso in prove:
            globals()["root"] = lambda c, tetto=300, r=risposta: r
            visto = righe_registro()
            esiti.append((etichetta, atteso, visto, visto == atteso))
    finally:
        globals()["root"] = vero_root
    bene = all(e[3] for e in esiti)
    verde = verde and bene
    print("  %s15b-⭐ la guardia di `righe_registro()`: %s"
          % ("OK  " if bene else "⛔  ",
             " · ".join("%s → %s%s" % (e[0], e[2], "" if e[3] else
                                       " ⛔ ATTESO %s" % e[1]) for e in esiti)))
    shutil.rmtree(d, ignore_errors=True)
    return verde


def _certifica_lettore():
    """⛔ La traccia finta si fabbrica con le costanti DELL'ARBITRO, e porta
       dentro apposta le tre cose su cui un lettore ingenuo inciampa:

         · un fotogramma spezzato in **piu' blocchi** (e l'intestazione di 28
           byte a cavallo di due);
         · un blocco con un intervallo **oscurato** (§11.1 lo permette, e sono
           40 byte in mezzo al file che vanno saltati o tutto slitta);
         · uno stream chiuso con **RESET_STREAM**, che e' la forma A
           dell'abbandono di §5.1 e **non** e' un fotogramma consegnato.

       ⚠ E c'e' anche un blocco del canale di controllo e uno del CLIENT, che
         non devono finire nel giornale del video.
    """
    import hashlib, tempfile
    try:
        spec = importlib.util.spec_from_file_location(
            "b4cert", os.path.join(QUI, "01-b4-validatore.py"))
        A = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(A)
    except Exception as e:
        return False, "l'arbitro §11.1 non si e' potuto importare: %s" % e

    blocchi = []      # (verso, canale, fine, istante, stream, carico, oscurati)

    def testa(numero, chiave, istante_us):
        return struct.pack("!HHIIIQI", 0x0301 if chiave else 0x0302, 3,
                           1920, 1080, numero, istante_us, 0)

    # rumore che NON e' video: canale di controllo, e un blocco del client
    blocchi.append((A.CLIENT, 0x00, A.CONTINUA, 0, 0, b"\x00" * 12, []))
    blocchi.append((A.SERVER, 0x00, A.CONTINUA, 1, 0, b"\x00" * 12, []))

    atteso = []
    stream, istante_ms = 4, 10
    for k in range(6):
        chiave = (k == 0)
        cat = k * 33000                       # µs, orologio del server
        t = testa(k + 1, chiave, cat)
        if k == 3:
            # ⛔ ABBANDONATO (§5.1 forma A): non e' un fotogramma consegnato.
            blocchi.append((A.SERVER, 0x03, A.CONTINUA, istante_ms, stream,
                            t + b"\x11" * 50, []))
            blocchi.append((A.SERVER, 0x03, A.RESET, istante_ms + 1, stream,
                            b"", []))
        else:
            # ⭐ l'intestazione a cavallo di DUE blocchi
            blocchi.append((A.SERVER, 0x03, A.CONTINUA, istante_ms, stream,
                            t[:12], []))
            corpo = b"\x22" * 500
            osc = []
            if k == 2:
                # un intervallo oscurato: 40 byte in mezzo al file
                osc = [(0, 8, hashlib.sha256(b"\x22" * 8).digest())]
            blocchi.append((A.SERVER, 0x03, A.CONTINUA, istante_ms, stream,
                            t[12:] + corpo[:200], osc))
            blocchi.append((A.SERVER, 0x03, A.FIN, istante_ms + 2, stream,
                            corpo[200:], []))
            atteso.append({"numero": k + 1, "chiave": chiave,
                           "byte": 500, "arrivo_ms": istante_ms + 2,
                           "istante_us": cat})
        stream += 4
        istante_ms += 33

    out = bytearray(A.MAGIA + struct.pack("!IBBBB", len(blocchi), 1, 0, 0, 0))
    for verso, canale, fine, ist, sid, carico, osc in blocchi:
        out += struct.pack(A.BLOCCO, verso, canale, fine, ist, sid,
                           len(carico), len(osc))
        for ini, qua, imp in osc:
            out += struct.pack("!II", ini, qua) + imp
        out += carico

    d = tempfile.mkdtemp(prefix="09-b70-")
    tr, le = os.path.join(d, "t.rcpreg"), os.path.join(d, "leggi.py")
    with open(tr, "wb") as f:
        f.write(bytes(out))
    with open(le, "w") as f:
        f.write(LETTORE)
    p = subprocess.run([sys.executable, le, tr,
                        os.path.join(QUI, "01-b4-validatore.py")],
                       capture_output=True)
    import shutil
    shutil.rmtree(d, ignore_errors=True)
    try:
        letto = json.loads(p.stdout.decode())
    except Exception as e:
        return False, "il lettore non ha risposto: %s — %s" % (
            e, (p.stdout + p.stderr).decode("utf-8", "replace")[-200:])
    g = letto.get("giornale") or []
    if letto.get("azzerati") != 1:
        return False, ("l'abbandono con RESET_STREAM non e' stato contato "
                       "a parte: azzerati = %s" % letto.get("azzerati"))
    if len(g) != len(atteso):
        return False, ("%d fotogrammi nel giornale, ne attendevo %d "
                       "(il RESET non e' un fotogramma consegnato)"
                       % (len(g), len(atteso)))
    for visto, att in zip(g, atteso):
        for chiave, valore in att.items():
            if visto.get(chiave) != valore:
                return False, ("fotogramma %s: «%s» vale %s, attendevo %s"
                               % (att["numero"], chiave, visto.get(chiave), valore))
    # ⭐ E la coda del giro: cinque fotogrammi sono POCHI, e la riduzione lo
    #    deve DIRE invece di calcolare un ritmo su un pugno di campioni.
    n = misura(g, 1, None, None, scaldata_s=0.0)
    if n.get("esito") == "misurato":
        return False, ("la riduzione ha misurato un ritmo su %d fotogrammi, "
                       "sotto il minimo di %d: doveva rifiutarsi"
                       % (len(g), MINIMO_FOTOGRAMMI))
    return True, ("%d fotogrammi letti (1 chiave, %d delta), 1 abbandono con "
                  "RESET contato a parte, oscurati e blocchi non-video saltati; "
                  "e la riduzione si rifiuta di fare un ritmo con cosi' pochi"
                  % (len(g), len(atteso) - 1))


# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE PARLA CON LA MACCHINA DI PROVA
# ═══════════════════════════════════════════════════════════════════════════
RETE = None       # il modulo 07-b65, importato in `principale()`


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔⛔ LA TRAPPOLA DELLO STDIN DI `sudo -S`, E QUESTO PROGETTO L'HA GIA' PAGATA
#       TRE VOLTE — si scrive qui perche' la quarta non si paghi
# ═══════════════════════════════════════════════════════════════════════════
#
# `07-b65-datagram.py:147` costruisce, e va benissimo per UN comando solo:
#
#       printf '%s\n' 'PAROLA' | sudo -S -p '' <comando>
#
# ⛔ **PRIMA FORMA — la catena.**  Il comando che arriva li' dentro non e' un
#    comando: e' una CATENA (`a && b | c > d`).  La shell remota la spezza
#    **fuori** da `sudo`, e `sudo` copre soltanto il PRIMO anello.  Gli anelli
#    successivi girano da utente normale — e se scrivono in `LAV`, che e' di
#    root, falliscono.  ⚠ E falliscono **in silenzio**, perche' il `|| echo 0`
#    o il `; true` che li accompagna trasforma l'errore in un numero plausibile.
#    `[M]` 23 agosto 2026: `spedisci_lettore()` non scriveva `09-b70-leggi.py`
#    sulla macchina, e §11.1 restava senza lettore.
#
# ⛔⛔ **SECONDA FORMA — e la peggiore, perche' e' MUTA.**  Un `< file` in coda
#      non lo prende il comando: lo prende **`sudo`**, che e' l'ultimo comando
#      della pipeline.  ⇒ Sullo stdin di `sudo` non arriva piu' la parola, ci
#      arriva il file; `sudo` risponde *«3 incorrect password attempts»* sullo
#      stderr, esce 1, e il `|| echo 0` in coda stampa **0**.
#      ⚠ E' scritto nero su bianco in `07-b64-terreno.sh` (~riga 240) — *«niente
#        `</dev/null` in coda: quel redirect vince su `sudo -S`»* — ed e' tornato
#        qui lo stesso: `[M]` 23 agosto 2026, `righe_registro()` tornava **0** su
#        un registro da migliaia di righe, e allora `conti_del_server()` leggeva
#        **dall'accensione del server** invece che da questo giro.  I «conto
#        finale» si salvavano (c'e' un `tail -1`), le righe `ciclo:` no:
#        `catturati` e **`attese a vuoto`** diventavano CUMULATIVI — cioe' la
#        colonna su cui `p_I1` decide se rifiutarsi di giudicare.
#
# ⇒ **LA CURA, ed e' una sola per tutt'e due**: un solo `sudo`, e la catena
#   intera dentro la SUA shell.  `sudo` resta l'unico comando della pipeline del
#   `printf`, quindi la parola gli arriva; e ogni `|`, `&&`, `<` e `>` della
#   catena vive dentro `bash -c`, cioe' dentro root.
#
#       printf '%s\n' 'PAROLA' | sudo -S -p '' bash -c '<catena intera>'
#
# ⚠ E il prezzo si dichiara: dentro gli apici singoli di `shlex.quote` il `$`
#   NON viene piu' espanso dalla shell remota.  Nessun comando di questo file
#   si appoggia a quell'espansione, e chi ne aggiungesse uno deve saperlo.
def catena_root(comando):
    """La riga che parte sull'ssh: **un** `sudo`, e la catena dentro la sua shell."""
    return ("printf '%%s\\n' '%s' | sudo -S -p '' bash -c %s"
            % (PAROLA_SUDO, shlex.quote(comando)))


def root(comando, tetto=300):
    """⛔ NON e' `RETE.root`: quella copre il solo primo anello della catena.

    ⚠ E chi sostituisce questa funzione dall'esterno per trascrivere (lo fa
      `09-b79-cure.py:415`) deve avvolgere **questa**, non `RETE.root`, o si
      riporta dentro tutt'e due i difetti curati qui sopra.
    """
    return RETE.rem(catena_root(comando), tetto)


def spedisci_lettore():
    """⛔ Il lettore si spedisce in base64: le virgolette di un heredoc dentro
       un `sudo -S` dentro un `ssh` sono tre livelli di quoting, e uno sbagliato
       non da' un errore — da' un file troncato.

    ⛔⛔ E la catena e' UNA SOLA chiamata a `root()`: `mkdir`, `printf`,
        `base64 -d` e il `>` vivono tutti dentro la stessa shell di root (vedi
        la trappola scritta qui sopra).  `[M]` 23 ago 2026: nella forma vecchia
        il `>` era della shell dell'utente e il file non si scriveva mai.
    """
    b = base64.b64encode(LETTORE.encode("utf-8")).decode("ascii")
    root("mkdir -p %s && printf '%%s' '%s' | base64 -d > %s/09-b70-leggi.py"
         % (LAV, b, LAV))
    # ⛔ `wc -c < file` va bene SOLO perche' adesso il redirect e' dentro la
    #    shell di root: e' root che apre il file, e lo stdin di `sudo` resta la
    #    parola.  Nella forma vecchia questo `<` rubava la parola e il banco
    #    diceva «non si e' scritto» di un file che c'era (2 198 byte misurati).
    rc, out, _ = root("wc -c < %s/09-b70-leggi.py" % LAV)
    return out.strip().isdigit() and int(out.strip()) > 1000


def terreno_controlla():
    """⛔ Il banco si rifiuta di misurare su un terreno che non e' il suo.

    ⚠ E conta gli ascoltatori NON miei senza toccarli: `LEZIONI.md` §1.26 —
      due banchi sulla stessa macchina non danno un rosso, danno **un numero
      plausibile**.
    """
    _log("IL TERRENO — porta %d · utente %s (uid %d) · albero %s"
         % (PORTA, UTENTE, UID_B, ALB))
    guai = []
    rc, out, _ = root("id %s >/dev/null 2>&1 && echo si || echo no" % UTENTE)
    if "si" not in out:
        guai.append("l'utente «%s» non esiste: "
                    "PORTA=%d UTENTE=%s UID_B=%d ALBERO=%s LAV=%s "
                    "bash banchi/07-b64-terreno.sh utente"
                    % (UTENTE, PORTA, UTENTE, UID_B, ALB, LAV))
    rc, out, _ = root("test -s %s/parola && echo si || echo no" % LAV)
    if "si" not in out:
        guai.append("manca %s/parola (0600): D12 vieta la parola in argv" % LAV)
    rc, out, _ = root("test -d %s/banchi && echo si || echo no" % ALB)
    if "si" not in out:
        guai.append("l'albero «%s» non c'e': si allinea con "
                    "banchi/attrezzi-allinea-innesto.sh" % ALB)
    # ⛔⛔ L'ARBITRO DI §11.1, e si controlla PRIMA di misurare.  `[M]` 23 agosto
    #     2026: `07-b64-terreno.sh porta` porta solo una manciata di `banchi/`, e
    #     `01-b4-validatore.py` non era fra quelli — il lettore della traccia
    #     moriva a ogni giro, il giornale restava vuoto, e il banco dava ROSSO a
    #     «non stacca» su una sessione viva da 797 fotogrammi.  ⇒ Un file che
    #     manca si dice qui, dove costa una riga, non a giro finito.
    rc, out, _ = root("test -s %s/banchi/01-b4-validatore.py && echo si || echo no"
                      % ALB)
    if "si" not in out:
        guai.append("manca l'arbitro di §11.1 «%s/banchi/01-b4-validatore.py»: "
                    "senza, il lettore della traccia non parte e ogni giro "
                    "sembra una sessione morta — si copia con "
                    "«scp banchi/01-b4-validatore.py» nell'albero" % ALB)
    rc, out, _ = root("test -x %s && echo si || echo no" % SCENA_BIN)
    if "si" not in out:
        guai.append("la scena «%s» non e' eseguibile: serve 04-b30-scena "
                    "costruita" % SCENA_BIN)
    rc, out, _ = root("ss -tuln 2>/dev/null | grep -c ':%d ' || true" % PORTA)
    mio = out.strip()
    rc, out, _ = root("uptime")
    _inf("carico: %s" % out.strip()[-40:])
    conto = []
    for p in VICINE:
        rc, o, _ = root("ss -tuln 2>/dev/null | grep -c ':%s ' || true" % p)
        conto.append("%s:%s" % (p, o.strip()))
    _inf("ascoltatori NON miei (si contano, non si toccano): %s" % " ".join(conto))
    _inf("il mio server sulla %d: %s ascoltatore/i" % (PORTA, mio))
    if mio == "0":
        guai.append("nessuno ascolta sulla %d: "
                    "PORTA=%d UTENTE=%s UID_B=%d ALBERO=%s LAV=%s "
                    "bash banchi/07-b64-terreno.sh accendi" % (PORTA, PORTA, UTENTE,
                                                               UID_B, ALB, LAV))
    if not spedisci_lettore():
        guai.append("il lettore della traccia non si e' scritto in %s" % LAV)
    for g in guai:
        _ko(g)
    if not guai:
        _ok("il terreno c'e', ed e' mio")
    return not guai


def righe_registro():
    """Quante righe ha il registro del server ADESSO — o `None` se non l'ho letto.

    ⛔⛔ **UNO ZERO CHE VUOL DIRE «NON HO LETTO» E UNO ZERO CHE VUOL DIRE «NON E'
        SUCCESSO NIENTE» NON DEVONO AVERE LA STESSA FACCIA** (`LEZIONI.md` §1.9).
        Qui la faccia era la stessa e il prezzo e' stato quello scritto sopra
        `catena_root()`: il numero tornava 0, `conti_del_server()` leggeva il
        registro **dall'accensione del server**, e `attese_a_vuoto` — la colonna
        con cui `p_I1` decide se rifiutarsi — diventava cumulativa.

    ⇒ Tre esiti, non due:
        · un intero > 0  — l'ho letto;
        · `None`         — ⛔ NON L'HO LETTO (il comando e' fallito, o la
          risposta non e' un numero);
        · `None` anche a **zero righe**: il server e' acceso (`terreno_controlla()`
          lo verifica prima di misurare) e un server acceso ha per forza gia'
          scritto.  Uno zero, qui, e' una lettura fallita travestita da misura.

    ⚠ E niente `|| echo 0` in coda: quel ripiego e' proprio il pezzo che
      trasformava l'errore in un numero plausibile.  Se fallisce, deve vedersi.
    """
    rc, out, err = root("wc -l < %s/registro.log" % LAV)
    t = out.strip()
    if rc != 0 or not t.isdigit():
        _dub("⛔ il registro del server NON si e' letto (rc=%s): «%s»"
             % (rc, (t + " " + err.strip())[:120]))
        return None
    n = int(t)
    if n <= 0:
        _dub("⛔ il registro del server ha ZERO righe con il server acceso: e' "
             "una lettura fallita, non una misura — NON la prendo per buona")
        return None
    return n


def conti_del_server(riga0):
    """⛔ Il cliente sa dire quanti fotogrammi ha PRESO; non sa dire quanti ne
       sono partiti.  Senza questi numeri «la rete l'ha buttato» e «il server non
       l'ha mai spedito» darebbero lo stesso conto — e in un banco che strozza la
       rete apposta e' la distinzione che serve piu' di ogni altra (R13).

    ⛔⛔ E LA PRIMA COSA CHE FA E' RIFIUTARSI, se `riga0` non e' un numero buono.
        Con `riga0` mancante il `tail -n +1` leggerebbe il registro **intero**:
        i «conto finale» si salverebbero (c'e' un `tail -1`), le righe `ciclo:`
        no, e `catturati`/`attese_a_vuoto` diventerebbero cumulativi
        dall'accensione del server.  ⇒ Numeri veri dati al giro sbagliato, che
        e' la ferita di `LEZIONI.md` §1.26 nella sua forma piu' invisibile.
        ⚠ La guardia sta QUI, al punto in cui il numero si CONSUMA, e non dentro
          `righe_registro()`: cosi' vale anche quando qualcun altro sostituisce
          quella funzione con una che torna 0 invece di `None`
          (`09-b76-rete-cattiva.py:1126` lo fa).
    """
    if riga0 is None or riga0 <= 0:
        return {"registro_non_letto":
                "⛔ il registro del server non si e' letto (riga di partenza "
                "«%s»): senza la riga di partenza i conti sarebbero CUMULATIVI "
                "dall'accensione, non di questo giro" % riga0}
    # ⚠ Dal 23 agosto 2026 il server scrive anche una riga `rete-quic …
    #   giudizio=…` una volta al secondo (`src/webtransport.c:3986`).  ⭐ Non
    #   confonde nessuno dei `grep` qui sotto — non porta «conto finale», ne'
    #   «figlio  ciclo:», ne' le quattro frasi della spirale — e siccome la
    #   partenza e' un NUMERO DI RIGA, righe nuove nel registro non spostano
    #   niente.  Chi aggiunge un `grep` qui lo controlli di nuovo.
    fuori = {"riga0": riga0}
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -a 'video di .*conto "
                      "finale' | tail -1" % (riga0 + 1, LAV))
    m = re.search(r"(\d+) fotogrammi consegnati.*?(\d+) NON SPEDITI.*?"
                  r"(\d+) spediti sul filo.*?(\d+) abbandonati.*?e (\d+) ANNUNCI",
                  out.strip())
    if m:
        fuori.update({"consegnati": int(m.group(1)), "non_spediti": int(m.group(2)),
                      "spediti": int(m.group(3)), "abbandonati": int(m.group(4)),
                      "annunci_tela": int(m.group(5))})
    else:
        # ⛔ `CODER.md` §3.10: «non ho letto» non e' «zero».
        fuori["esito_video"] = "NIENTE DA LEGGERE — nessun «conto finale» del video"
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -a 'audio di .*conto "
                      "finale' | tail -1" % (riga0 + 1, LAV))
    m = re.search(r"(\d+) blocchi spediti, (\d+) buttati.*?(\d+) rifiutati.*?"
                  r"(\d+) RIMANDATI", out.strip())
    if m:
        # ⚠ Si leggono e si stampano, ma NON si giudicano: il giudice del suono
        #   e' `07-b64-orecchio.py`, e la domanda «chi paga fra audio e video»
        #   e' gia' chiusa da `07-b65`.
        fuori["audio"] = {"spediti": int(m.group(1)), "buttati": int(m.group(2)),
                          "rifiutati": int(m.group(3)), "rimandati": int(m.group(4))}
    # ⭐⭐ E IL LATO CATTURA, che e' la colonna SENZA CUI I1 NON E' GIUDICABILE.
    #
    # ⛔ La riga `ciclo:` del figlio (`figlio.c:6842`) porta, cumulativa e una
    #    volta al secondo, «N fotogrammi consegnati (K chiavi), M **attese a
    #    vuoto**» — e il prodotto stesso spiega che cosa vuol dire: *«scena
    #    ferma: Mutter consegna solo quando qualcosa cambia»*.
    #
    # ⭐ Questa colonna me l'ha insegnata `banchi/09-b68-ritmo.py`, di un altro
    #    agente, il 23 agosto: e' un discriminatore **migliore** del rapporto
    #    `spediti/consegnati` che avevo scritto per primo, perche' non deduce —
    #    dice che noi abbiamo CHIESTO un fotogramma e non ce n'era.  ⇒ «Mutter
    #    non consegna» e «noi non calavamo il ritmo» smettono di avere lo stesso
    #    aspetto, che e' esattamente la trappola di `04-b32-ritmo.py`.
    r = re.compile(r"ciclo: (\d+) fotogrammi consegnati \((\d+) chiavi\), "
                   r"(\d+) attese a vuoto")
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -a 'figlio  ciclo:'"
                      % (riga0 + 1, LAV))
    righe = r.findall(out)
    if len(righe) >= 2:
        p0, p1 = righe[0], righe[-1]
        fuori["cattura"] = {"catturati": int(p1[0]) - int(p0[0]),
                            "chiavi": int(p1[1]) - int(p0[1]),
                            "attese_a_vuoto": int(p1[2]) - int(p0[2]),
                            "righe_ciclo": len(righe)}
    else:
        fuori["cattura"] = {"esito": "NIENTE DA LEGGERE — meno di due righe "
                                     "«ciclo:» in questo giro"}
    # ⭐ E LE RIGHE DELLA SPIRALE, contate: sono il ponte fra i numeri di questa
    #    pagina e la causa nominata in `fasi/09...` §0.3.
    for etichetta, aco in (
            ("chiave_aspetta", "§5.2 vieta di abbandonarla"),
            ("delta_non_spedito", "FOTOGRAMMA NON SPEDITO"),
            ("abbandonato_in_coda", "ABBANDONATO NELLA CODA"),
            ("involo_pieno", "NON potra' essere abbandonato")):
        rc, out, _ = root("tail -n +%d %s/registro.log | grep -ac '%s' || true"
                          % (riga0 + 1, LAV, aco))
        fuori.setdefault("spirale", {})[etichetta] = (
            int(out.strip()) if out.strip().isdigit() else None)
    return fuori


def scena_accendi(movimento):
    """⭐ «Scena ferma» = `--movimento marca`, NON la scena spenta.

    ⛔ A scena spenta il compositore consegna pochissimo, e i due giri della
       coppia non sono confrontabili: un ritmo basso a monte somiglia in tutto a
       un ritmo abbassato da noi.  Con `marca` cambia solo la marca — la cadenza
       di cattura resta quella del giro mosso, e a cambiare c'e' il COSTO, che e'
       l'unica cosa che I1 vuole isolare.
    """
    scena_spegni()
    rc, out, _ = root("grep -ao 'monitor «[^»]*»' %s/registro.log | tail -1" % LAV)
    m = re.findall("monitor «([^»]*)»", out)
    usc = m[-1] if m and m[-1] else None
    if not usc:
        return None
    root("setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
         "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
         "XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 "
         "%s --uscita %s --movimento %s --shm /09-b70 --giro b70 "
         ">/dev/null 2>&1 & echo acceso"
         % (UID_B, UID_B, UTENTE, UTENTE, UID_B, SCENA_BIN, usc, movimento))
    time.sleep(1.5)
    rc, out, _ = root("pgrep -u %d -f '04-b30-scena --uscita' | head -1" % UID_B)
    return usc if out.strip() else None


def scena_spegni():
    root("pkill -u %d -f 04-b30-scena; true" % UID_B)


def innesca_sessione(secondi=8):
    """⛔ Il palco e il monitor nascono col PRIMO cliente: su un server appena
       acceso il registro non porta ancora il nome del monitor, e la scena non
       saprebbe dove disegnare.  ⇒ Si apre una sessione corta apposta; il palco
       le sopravvive (I4)."""
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s/parola --audio-codec pcm "
              "--video-codec %s --adatta %s --resta %d"
              % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, CODEC_CHIESTO,
                 TELA_PIENA, secondi))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro,
                        secondi + 180)
    return "SESSIONE" in (out + err)


def _linea_del_giro():
    """⭐ La perdita della linea si LEGGE dal qdisc installato, non si assume.

    ⛔ Assumerla sarebbe peggio del difetto che cura: `09-b76-rete-cattiva.py`
       chiama questa stessa `giro()` con un `netem` che **perde**, e un
       «perdita 0» scritto a mano qui rimetterebbe in piedi esattamente il falso
       rosso di `p_I1` che si sta togliendo.  ⇒ Si guarda quel che c'e' davvero.

    ⚠ E se il qdisc non si legge, si scrive `None` — che vuol dire «non lo so»,
      e `p_I1` allora si rifiuta invece di dare rosso.
    """
    try:
        testo = RETE.qdisc() or ""
    except Exception as e:
        return {"perdita_pc": None, "come": "il qdisc non si e' letto: %s" % e}
    if "netem" not in testo:
        return {"perdita_pc": None, "come": "nessun netem sul dispositivo: la "
                                            "linea non e' quella che credo",
                "qdisc": testo[:200]}
    # `loss 1%` (indipendente) oppure `loss gemodel p 0.2% r 20% …` (a raffica)
    m = re.search(r"loss\s+(?:gemodel\s+p\s+)?([\d.]+)%", testo)
    return {"perdita_pc": float(m.group(1)) if m else 0.0,
            "come": ("netem con «%s»" % m.group(0)) if m else
                    "netem senza `loss`: la sola perdita possibile e' la coda "
                    "che trabocca",
            "qdisc": testo[:200]}


def giro(nome, movimento, tela, secondi, con_traccia=True):
    """Un giro: il cliente dentro il contenitore, la traccia ridotta sul posto."""
    root("rm -f %s/%s.rcpreg %s/%s.json; true" % (LAV, nome, LAV, nome))
    # ⛔ `None` (o 0) qui vuol dire «il registro non l'ho letto», e da li' in poi
    #    i conti del server sarebbero cumulativi dall'accensione: la guardia sta
    #    dentro `conti_del_server()`, che si rifiuta invece di leggere tutto.
    riga0 = righe_registro()
    linea = _linea_del_giro()
    prima = RETE.byte_sul_filo()
    t0 = time.time()
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s/parola --audio-codec pcm "
              "--video-codec %s --adatta %s %s--resta %d"
              % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, CODEC_CHIESTO, tela,
                 ("--registra %s/%s.rcpreg " % (DENTRO_LAV, nome)) if con_traccia else "",
                 secondi))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro,
                        secondi + 300)
    dopo = RETE.byte_sul_filo()
    vero = time.time() - t0
    testo = out + err
    # ⭐ Il conto che il CLIENTE stampa da solo, che e' indipendente dalla
    #    traccia: e' con questo che si smaschera il peso del testimone.
    dal_cliente = None
    for x in testo.splitlines():
        m = re.search(r"\[vid\]\s+(\d+) fotogrammi \((\d+) chiavi\)", x)
        if m:
            dal_cliente = {"fotogrammi": int(m.group(1)), "chiavi": int(m.group(2))}
    filo = None
    if prima and dopo:
        b, pk = dopo[0] - prima[0], dopo[1] - prima[1]
        filo = {"byte": b, "pacchetti": pk, "secondi": vero,
                "byte_per_pacchetto": round(b / pk, 1) if pk else None}
    server = conti_del_server(riga0)
    giornale, letto, muta = [], {"esito": "senza traccia"}, None
    if con_traccia:
        rc, out2, err2 = root("python3 %s/09-b70-leggi.py %s/%s.rcpreg "
                              "%s/banchi/01-b4-validatore.py"
                              % (LAV, LAV, nome, ALB), 600)
        try:
            letto = json.loads(out2)
            giornale = letto.pop("giornale", [])
        except Exception as e:
            letto = {"esito": "il lettore non ha risposto: %s — %s"
                             % (e, (out2 + err2)[-200:])}
            # ⛔⛔ E QUESTA E' LA TERZA FACCIA DELLO STESSO DIFETTO (§1.9), e
            #     l'ha trovata il giro vero del 23 agosto 2026: se il lettore
            #     non risponde, il giornale e' VUOTO — e un giornale vuoto ha la
            #     faccia identica a *«la sessione non ha consegnato niente»*.
            #     ⇒ `[M]` quella sera il banco ha dato ROSSO a «non stacca» su
            #       un giro in cui il server aveva spedito **797** fotogrammi e
            #       il cliente li aveva presi: un rosso sul prodotto per un file
            #       che mancava nel MIO albero (`01-b4-validatore.py`).
            #     ⇒ La traccia non letta si DICHIARA, e i predicati che vivono
            #       sul giornale si rifiutano invece di accusare.
            muta = ("⛔ LA TRACCIA §11.1 NON SI E' LETTA: %s" % letto["esito"])
    n = misura(giornale, secondi, server, filo,
               azzerati=letto.get("azzerati"))
    if muta:
        n["traccia_non_letta"] = muta
        n["esito"] = "NON HO NIENTE DA GIUDICARE — " + muta
    n["nome"] = nome
    n["movimento"] = movimento
    n["linea"] = linea          # ⭐ la premessa della seconda gamba di I1
    n["tela_chiesta"] = tela
    n["dal_cliente"] = dal_cliente
    n["lettore"] = letto
    n["secondi_veri"] = round(vero, 1)
    n["coda_cliente"] = testo[-400:]
    return n


def stampa_giro(n):
    """⛔ §6.2: si stampano TUTTE le grandezze, anche quelle che non servono
       alla domanda del momento.  Una tabella con una colonna sola non e' una
       misura corta: e' una misura ORIENTATA."""
    if not _ha_misurato(n):
        _dub("%s · %s" % (n.get("nome"), n.get("esito")))
        return
    _inf("RITMO   media %6.2f/s   peggior secondo %s/s   intero %s/s   "
         "mediana %s ms   p95 %s ms"
         % (n["fps"], n["fps_finestra_min"], n["fps_intero"],
            n["intervallo_mediano_ms"], n["intervallo_p95_ms"]))
    _inf("FORMA   %d fotogrammi (%d chiavi · %d delta = %.1f %% delta)   "
         "codec sul filo %s   tela %s"
         % (n["fotogrammi"], n["chiavi"], n["delta"], n["quota_delta"] * 100,
            ",".join(n["codec_sul_filo"]), ",".join(n["tela_sul_filo"])))
    _inf("BYTE    carico %s Mbit/s (%d B/fotogramma)   filo %s Mbit/s   "
         "%s B/pacchetto"
         % (n["mbit_s_carico"], n["byte_per_fotogramma"],
            n["mbit_s_filo"] if n["mbit_s_filo"] is not None else "NON LETTO",
            n["byte_per_pacchetto"]))
    _inf("RITARDO deriva finale %s ms   massima %s ms   minima %s ms   "
         "⚠ e' la DERIVA, non l'anello"
         % (n["deriva_fine_ms"], n["deriva_max_ms"], n["deriva_min_ms"]))
    if n.get("linea"):
        _inf("LINEA   perdita dichiarata dal qdisc: %s   (%s)"
             % ("%.2f %%" % n["linea"]["perdita_pc"]
                if n["linea"].get("perdita_pc") is not None else "⛔ NON LO SO",
                n["linea"].get("come")))
    s = n.get("server") or {}
    if s.get("registro_non_letto"):
        _dub("SERVER  %s" % s["registro_non_letto"])
        return
    _inf("SERVER  consegnati %s · non spediti %s · spediti %s · ABBANDONATI %s "
         "· annunci tela %s   (registro da riga %s)"
         % (s.get("consegnati"), s.get("non_spediti"), s.get("spediti"),
            s.get("abbandonati"), s.get("annunci_tela"), s.get("riga0")))
    _inf("CATTURA %s   ⭐ «attese a vuoto» = abbiamo chiesto e non c'era: e' la "
         "colonna che separa Mutter da noi"
         % json.dumps(s.get("cattura"), ensure_ascii=False))
    _inf("        seconda gamba: buchi nel `numero` %s · stream azzerati nella "
         "traccia %s · audio %s"
         % (n["buchi_numero"], n.get("azzerati_sul_filo"), s.get("audio")))
    _inf("        spirale (§5.2/§5.1): %s" % json.dumps(s.get("spirale"),
                                                        ensure_ascii=False))
    # ⛔ IL PESO DEL TESTIMONE, e si guarda a OGNI giro.
    dc, sp = n.get("dal_cliente"), s.get("spediti")
    if dc and sp:
        manca = sp - dc["fotogrammi"]
        if manca > max(5, 0.05 * sp):
            _dub("⚠ il server ne ha spediti %d e il cliente ne ha presi %d "
                 "(%d in meno): il collo puo' essere il TESTIMONE, non la linea"
                 % (sp, dc["fotogrammi"], manca))


# ═══════════════════════════════════════════════════════════════════════════
def principale():
    global RETE
    p = argparse.ArgumentParser()
    p.add_argument("passo", nargs="?",
                   choices=["terreno", "sonda", "rimetti", "stato"])
    p.add_argument("--certifica", action="store_true",
                   help="⭐ il controllo positivo: prova che il banco sa vedere "
                        "i difetti che cerca.  Non tocca la macchina di prova")
    p.add_argument("--secondi", type=int, default=30)
    p.add_argument("--solo", default="", help="un gradino solo, per nome")
    p.add_argument("--tono", default="no", choices=["si", "no"],
                   help="⚠ accende 1,56 Mbit/s di PCM: la domanda «chi paga fra "
                        "audio e video» e' gia' chiusa da 07-b65, qui il "
                        "predefinito e' SPENTO cosi' il gradino misura il video")
    p.add_argument("--controllo-testimone", action="store_true",
                   help="⭐ rigira il gradino del pavimento SENZA traccia: e' la "
                        "prova diretta che il testimone non pesa sul numero")
    p.add_argument("--senza-tela-minima", action="store_true",
                   help="salta la coppia a 768x480 del gradino del pavimento")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if not a.passo:
        p.error("serve un passo, oppure --certifica")

    os.makedirs(FUORI, exist_ok=True)
    RETE = _importa_rete()

    if a.passo in ("rimetti", "stato"):
        _log("la rete della macchina di prova — dev «%s», porta %d" % (DEV, PORTA))
        return 0 if RETE.rimetti() else 2

    if a.passo == "terreno":
        return 0 if terreno_controlla() else 2

    _log("09-b70 · IL RITMO — porta %d · dev «%s» · codec chiesto «%s»"
         % (PORTA, DEV, CODEC_CHIESTO))
    print("   ⛔ «%s» (ssh + la 7730 dell'utente) NON si tocca" % VIETATA)
    print("   ⛔ il pavimento e' 20 Mbit/s (§3.1-bis) e 25 fotogrammi/s (§2.1):")
    print("      sotto i 20 si GUARDA, non si pretende")
    print("   --  «%s» prima: %s" % (DEV, RETE.qdisc() or "(nessuna)"))
    if not terreno_controlla():
        return 2

    scelti = [g for g in GRADINI if not a.solo or a.solo in g[0]]
    if not scelti:
        _ko("nessun gradino corrisponde a «%s»" % a.solo)
        return 2
    # scena ferma + scena mossa per ogni gradino, piu' la coppia a tela minima
    quanti = 2 * len(scelti) + (2 if (not a.senza_tela_minima and
                                      any(g[0].startswith("g4") for g in scelti)) else 0)
    totale = (a.secondi + 170) * quanti + 400
    RETE.guardiano_arma(totale)

    esiti, rossi, muti = [], [], []
    try:
        _inf("apro una sessione corta per far nascere il palco e il monitor")
        if not innesca_sessione():
            _ko("la sessione non si apre: non misuro")
            return 2
        if a.tono == "si":
            RETE.tono_accendi()
            _inf("⚠ il tono e' ACCESO: il gradino non misura il solo video")

        lavoro = []
        for nome, mbit, rit, requisito, perche in scelti:
            lavoro.append((nome, mbit, rit, requisito, perche, TELA_PIENA, ""))
            if nome.startswith("g4") and not a.senza_tela_minima:
                lavoro.append((nome, mbit, rit, requisito,
                               "⭐ lo stesso gradino alla TELA DEL PAVIMENTO: "
                               "§2.1 e' scritta a 480p, e la risoluzione "
                               "adattiva e' fuori dal prodotto (§5.0-ter)",
                               TELA_MINIMA, "-480"))

        for nome, mbit, rit, requisito, perche, tela, suff in lavoro:
            _log("%s%s · %s" % (nome, suff, perche))
            reg = _regole(mbit, rit)
            ok, q = RETE.stringi(reg)
            if not ok:
                _ko(q)
                esiti.append({"gradino": nome + suff, "passa": False,
                              "perche": "tc ha rifiutato la regola"})
                rossi.append(nome + suff)
                break
            if mbit:
                _inf("tc: %s  (coda %d pacchetti = %d ms a %d Mbit/s — il "
                     "predefinito di netem sarebbe 1000, cioe' %d ms)"
                     % (" ".join(reg), _limite(mbit), CUSCINO_MS, mbit,
                        int(1000 * PACCHETTO * 8 * 1000 / (mbit * 1e6))))
            else:
                _inf("tc: %s  (nessun limite di banda: il netem conta e basta)"
                     % " ".join(reg))
            _inf("tela %s" % tela)

            coppia = {}
            for etichetta, movimento in (("mossa", "barra"), ("ferma", "marca")):
                usc = scena_accendi(movimento)
                if not usc:
                    _ko("la scena «%s» non parte: NON giudico questo gradino"
                        % movimento)
                    coppia[etichetta] = {"esito": "NON HO NIENTE DA GIUDICARE — "
                                                 "la scena non e' partita"}
                    continue
                _inf("scena «%s» sul monitor %s" % (movimento, usc))
                n = giro("%s%s-%s" % (nome, suff, etichetta), movimento, tela,
                         a.secondi)
                print("   [%s]" % etichetta)
                stampa_giro(n)
                coppia[etichetta] = n
                scena_spegni()

            # ⛔ I1 PER PRIMA, ed e' la ragione per cui il gradino si gira in due.
            passa_i1, perche_i1 = p_I1(coppia.get("ferma", {}),
                                       coppia.get("mossa", {}))
            (_ok if passa_i1 else (_dub if passa_i1 is None else _ko))(
                "I1 — il ritmo non cala a scena ferma: %s" % perche_i1)

            voci = {"gradino": nome + suff, "mbit": mbit, "ritardo_ms": rit,
                    "coda_pacchetti": _limite(mbit) if mbit else None,
                    "tela": tela, "requisito": requisito, "perche": perche,
                    "I1": {"passa": passa_i1, "perche": perche_i1},
                    "ferma": coppia.get("ferma"), "mossa": coppia.get("mossa"),
                    "predicati": {}}
            if passa_i1 is False:
                rossi.append("%s%s · I1" % (nome, suff))
            elif passa_i1 is None:
                muti.append("%s%s · I1 — %s" % (nome, suff, perche_i1))

            # Poi i predicati del singolo giro, sul giro MOSSO (che e' il caso
            # su cui il pavimento e' scritto) e su quello FERMO.
            for etichetta in ("mossa", "ferma"):
                n = coppia.get(etichetta) or {}
                voci["predicati"][etichetta] = giudica_giro(n, requisito)
                for voce in voci["predicati"][etichetta]:
                    marca = "%s%s · %s · %s" % (nome, suff, etichetta,
                                                voce["predicato"])
                    if not voce["conta"]:
                        _inf("⚠ diagnosi · %s · %s → %s (%s)"
                             % (etichetta, voce["predicato"].split(" (")[0],
                                voce["passa"], voce["perche"][:80]))
                        continue
                    (_ok if voce["passa"] else
                     (_dub if voce["passa"] is None else _ko))(
                        "%s · %s: %s" % (etichetta,
                                         voce["predicato"].split(" (")[0],
                                         voce["perche"]))
                    if voce["passa"] is False:
                        rossi.append(marca)
                    elif voce["passa"] is None:
                        muti.append("%s — %s" % (marca, voce["perche"]))
            esiti.append(voci)

        # ⭐ IL CONTROLLO DEL TESTIMONE — la prova diretta che la traccia non
        #    e' il collo.  Stesso gradino, stessa scena, senza `--registra`.
        if a.controllo_testimone:
            _log("⭐ CONTROLLO DEL TESTIMONE — lo stesso gradino SENZA traccia")
            RETE.stringi(_regole(20, RITARDO_MS))
            usc = scena_accendi("barra")
            if usc:
                senza = giro("controllo-senza-traccia", "barra", TELA_PIENA,
                             a.secondi, con_traccia=False)
                scena_spegni()
                _inf("senza traccia — il cliente dice: %s · il server: %s"
                     % (senza.get("dal_cliente"),
                        (senza.get("server") or {}).get("spediti")))
                esiti.append({"gradino": "controllo-testimone", "senza": senza})
                _inf("⛔ si confronta con il giro «g4-20mbit-mossa» qui sopra: "
                     "se il cliente ne prende sensibilmente di piu' SENZA "
                     "traccia, il numero della griglia e' del testimone")
    finally:
        scena_spegni()
        if a.tono == "si":
            RETE.tono_spegni()
        _log("⛔ LA RETE SI RIMETTE COM'ERA")
        rimessa = RETE.rimetti()

    with open(os.path.join(FUORI, "09-b70-esiti.json"), "w") as f:
        json.dump(esiti, f, ensure_ascii=False, indent=1)
    _inf("esiti in %s/09-b70-esiti.json" % FUORI)

    _log("IL VERDETTO — %d gradini girati · %d rossi · %d non giudicati"
         % (len(esiti), len(rossi), len(muti)))
    for r in rossi:
        _ko(r)
    for m in muti:
        _dub(m)
    if not rimessa:
        _ko("⛔ la rete NON e' tornata com'era: si rimette a mano con «rimetti»")
        return 2
    if rossi:
        return 1
    if muti:
        # ⚠ «non ho misurato» e' un esito SUO, non un verde.
        return 3
    _ok("⭐ tutti i predicati hanno fatto quel che era scritto prima")
    return 0


if __name__ == "__main__":
    sys.exit(principale())
