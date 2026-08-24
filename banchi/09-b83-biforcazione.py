#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b83-biforcazione — **PERCHE' LO STESSO INGRESSO DA' DUE USCITE.**

    porta 7971 · sonda 7979… · utente `provanr8` (uid 1071)
    albero `/media/REMOTIX/src/09nr8-src` · lavoro `/media/REMOTIX/tmp/09nr8`
    unita' `remotix-7971` · ban-file, socket e memoria condivisa suoi

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ DA DOVE NASCE — DUE USCITE PER LO STESSO INGRESSO, E NESSUNA SPIEGAZIONE
═══════════════════════════════════════════════════════════════════════════════

`[M]` 23 agosto 2026, `banchi/09-b80-dirupo.py`, **42 giri**: vicino al bordo
della perdita la spirale di chiavi e' **BISTABILE**.

  ⛔ A **0,20 %** di perdita vera, stesso binario, stesso terreno, stessa
     macchina, a venti minuti di distanza:
         `0 chiavi · 40,16 fotogrammi/s`   e   `24 chiavi · 33,84 fotogrammi/s`

E la dispersione fra giri identici **cresce con la perdita e non col carico**:
0,4 % a perdita zero → 14,8 % a 0,5 % → **46,6 %** a 0,75 %.  `[M]` La CPU e'
stata 3,7-4,7 % in *ognuno* dei 42 giri ⇒ **«macchina carica» e' gia' escluso**.

⇒ Non e' una soglia: **e' un punto di biforcazione**.  E finche' non e'
  spiegato, ogni numero preso vicino al bordo e' una moneta lanciata: il primo
  giro di `09-b76` prese il ramo fortunato e ci fu scritta sopra una forbice
  sbagliata, poi ritirata.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ LE IPOTESI — SCRITTE PRIMA DI MISURARE, E CIASCUNA CON LA SUA SMENTITA
═══════════════════════════════════════════════════════════════════════════════

⛔ Una causa **plausibile e non verificata** non e' un esito: questa fase ne ha
   gia' ritirate due.  ⇒ Ogni ipotesi qui sotto porta **il fatto che la
   ucciderebbe**, e il fatto e' scritto prima di guardare un solo numero.

⭐ IL MECCANISMO, PER INTERO, LETTO NEL CODICE (`[R]`, 24 ago 2026) — perche'
   senza di lui le ipotesi sarebbero nomi:

  1. `trasporto.c:628` chiama `ngtcp2_settings_default()` e **non tocca mai
     `cc_algo`** ⇒ si prende il predefinito di ngtcp2 1.25.0, che e'
     `NGTCP2_CC_ALGO_CUBIC` (`ngtcp2.h:7111`): **CUBIC, cioe' A PERDITA**.
     `webtransport.c:3167-3173` lo dichiara gia' `[?]` a parole.
  2. CUBIC esce dall'avvio lento **alla prima perdita dichiarata**, e ci esce
     mettendo `ssthresh = cwnd × β`.  ⛔ Da li' in poi la finestra cresce solo
     in evitamento: **`ssthresh` non risale**.
  3. Le cure sono SPENTE (I6): `--sgombra-soglia-ms` vale 0, e con la soglia
     spenta §5.1 abbandona **ogni** delta che abbia ancora byte in coda quando
     ne arriva uno piu' recente (`webtransport.c:3440-3585`, chiamata a `:4837`).
  4. Ogni abbandono accende il debito di chiave (`rcp.c:3859`:
     *«un delta e' stato abbandonato nella coda (§5.1)»*) e §5.2 gira la
     richiesta al palco (`webtransport.c:3872-3888`).
  5. E l'intervallo con cui si puo' richiedere la chiave e' stimato
     `chiave_byte × smoothed_rtt / cwnd` (`webtransport.c:3663-3757`) ⇒ **piu'
     `cwnd` e' piccola, piu' spesso si chiedono chiavi, che sono grosse.**

  ⇒ 1+2+3+4+5 fanno una spirale che si autoalimenta, e il suo interruttore e'
    **`cwnd`**: se la finestra basta a svuotare un fotogramma prima del
    successivo, non parte mai; se non basta, non si ferma piu'.

── **I0 · LA PERDITA NON ERA LA STESSA** `[?]` ────────────────────────────────
   `netem` estrae a caso.  Due giri «alla stessa perdita» possono aver visto
   perdite vere diverse, e allora la biforcazione non e' una biforcazione: e'
   la scala fine guardata da vicino.
   ⇒ **La ucciderebbe**: la perdita VERA (sonda a 20 000 pacchetti, prima di
     ogni giro) NON separa le due famiglie.
   ⛔ E' il primo controllo di tutti: se lo salto, ogni altra conclusione e'
      appesa a un'assunzione.

── **I1 · L'AVVIO LENTO DI CUBIC** `[?]` ⭐ la candidata principale ───────────
   Se la prima perdita viene dichiarata mentre `cwnd` e' ancora piccola,
   `ssthresh` scende basso e **ci resta**: la coda non si svuota, §5.1 abbandona,
   §5.2 chiede chiavi, la spirale parte.  Se la prima perdita arriva quando
   `cwnd` e' gia' grande, non parte mai.  ⇒ **La biforcazione starebbe nei primi
   secondi.**
   ⇒ **Le tre predizioni**:
       a) `ssthresh` nei primi 10 s separa le due famiglie **senza
          sovrapposizione**;
       b) l'istante in cui `ssthresh` lascia l'infinito (= l'avvio lento
          finisce) e' **prima** nella famiglia della spirale;
       c) ⭐⭐ la separazione si vede **PRIMA** dell'accensione della spirale.
   ⇒ **La ucciderebbe**: `ssthresh`/`cwnd` dei primi 10 s non separano; oppure
     separano **solo dopo** il primo abbandono §5.1 — e allora quei numeri
     registrano la spirale, non la causano.  ⛔ E' la differenza fra un
     precursore e un'eco, ed e' l'unico modo per cui I1 puo' fallire senza
     sembrare confermata.

── **I2 · LA SCENA** `[?]` ────────────────────────────────────────────────────
   Due giri «identici» non lo sono se il contenuto differisce.
   `[R]` `04-b30-scena.c:822-831`: con `--movimento barra` il disegno e'
   funzione del **solo contatore** `n`, e la scena si riaccende a ogni cella ⇒
   il CONTENUTO dovrebbe essere identico; ma la cadenza la detta il compositore,
   quindi *quali* disegni vengono catturati cambia.
   ⇒ **La ucciderebbe**: il costo in byte dei primi fotogrammi (primi 3 s, e la
     prima chiave) NON separa le due famiglie.

── **I3 · L'ALGORITMO NON E' MAI STATO SCELTO** ───────────────────────────────
   ⛔ Non e' un'ipotesi da misurare: e' un fatto da **leggere**, ed e' letto —
   punto 1 del meccanismo qui sopra.  E' la CORNICE di I1, non un'alternativa.
   ⚠ E non e' verificabile da questo banco per contrasto: `cc_algo` non e'
     esposto da nessuna opzione (`main.c:978-1140`) e `src/` non e' mio.
     ⇒ Si dichiara letto `[R]`, e la prova per contrasto resta da fare.

── **I4 · LA SOGLIA DEI TRE PACCHETTI** `[?]` ────────────────────────────────
   ngtcp2 dichiara persa una spedizione quando tre piu' recenti sono state
   riscontrate.  Al bordo, poche perdite in piu' o in meno cambiano **se** una
   perdita viene dichiarata — e una dichiarazione fa scendere `ssthresh`.
   ⇒ **La ucciderebbe**: il numero di pacchetti QUIC dichiarati persi nei primi
     10 s, e l'istante della prima dichiarazione, NON separano le famiglie.
   ⚠ E il suo limite si dichiara **prima**: con una riga di registro al secondo
     non si vede il singolo evento di dichiarazione.  ⇒ Questo banco puo' dire
     *quando* e *quante*, non *quale terzo pacchetto*.

── **I5 · NON STA NEI PRIMI SECONDI** `[?]` (l'ipotesi nulla) ────────────────
   Il ramo non e' deciso all'avvio: si decide piu' tardi, a un istante qualsiasi.
   ⇒ **La ucciderebbe**: qualunque grandezza dei primi 10 s che separi le
     famiglie **prima** dell'accensione della spirale.
   ⛔ Serve, e non e' cerimonia: senza di lei «ho trovato una differenza nei
      primi dieci secondi» e «la causa sta nei primi dieci secondi» hanno la
      stessa faccia — e la seconda e' proprio il genere di frase che questa fase
      ha gia' dovuto ritirare due volte.

── **I6 · NON SONO DUE RAMI** `[?]` ⭐ e nessuno l'ha ancora guardata ─────────
   La «bistabilita'» potrebbe essere una **dispersione continua**: i due giri del
   23 agosto erano le due code della stessa distribuzione larga, e con due
   osservazioni non c'e' modo di distinguere le due cose.
   ⇒ **La ucciderebbe**: venti giri che mostrano le chiavi a **zero-o-molte** e
     non una scala.
   ⛔ E se invece I6 regge, cade con lei anche il modo di parlare: non «due
      rami», ma «un profilo molto disperso» — e le ipotesi da I1 a I4, che
      cercano un interruttore, cercherebbero una cosa che non c'e'.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ QUANTI GIRI — IL CONTO SI FA PRIMA, E SI DICHIARA CHE COSA NON SI VEDRA'
═══════════════════════════════════════════════════════════════════════════════

⛔ Al bordo la dispersione e' del 46 %: **tre giri non distinguono niente**.

⭐ IL CONTO.  Il confronto fra le due famiglie e' un **test di permutazione
   esatto** sulla differenza delle mediane (nessuna assunzione di forma, e le
   famiglie sono piccole).  Con N giri e n della famiglia minore, il p **piu'
   piccolo che il test possa produrre** e' `2 / C(N, n)`:

       N=20, n=4  ⇒ 2/4845   = 0,00041     ✔ sotto la soglia
       N=20, n=3  ⇒ 2/1140   = 0,00175     ✘ SOPRA la soglia
       N=20, n=2  ⇒ 2/190    = 0,0105      ✘ molto sopra

   ⇒ **Sotto i quattro giri per famiglia, nemmeno una separazione PERFETTA
     arriverebbe alla soglia.**  Percio' il minimo e' quattro, e sotto quello il
     banco **tace** invece di concludere.

⭐ LA SOGLIA, dichiarata prima: **0,05 / 43 = 0,00116**, Bonferroni sulle **43
   prove scritte prima** (13 grandezze riassuntive + 30 prove secondo per
   secondo).  ⚠ Senza la correzione, provare 43 grandezze e tenere la piu' bella
   darebbe una «scoperta» in piu' di un giro su due per puro caso.

⭐ PERCHE' VENTI.  `[M]` 23 ago si e' visto 1 e 1: la stima migliore di p (la
   probabilita' del ramo spirale) e' 1/2.  Con N=20 e p=1/2, la probabilita' che
   una delle due famiglie resti sotto i quattro e' 2·P(X≤3) = 0,26 %.

⚠⚠ **CHE COSA NON AVREI POTUTO VEDERE CON VENTI GIRI** — e si scrive prima:

   1. **un ramo raro.**  Se p valesse 0,25, la probabilita' di restare sotto i
      quattro casi e' del **22 %**; se valesse 0,15, del **65 %**.  ⇒ Con venti
      giri un ramo raro non si giudica, e il banco lo dichiara muto.
      ⛔ **La regola d'arresto e' scritta PRIMA**: se dopo venti giri una
         famiglia ha meno di quattro casi, si aggiunge **un secondo blocco di
         venti** e lo si dichiara nel rapporto.  Non si guarda e poi si decide.
   2. **una separazione piccola.**  Venti giri, con questa soglia, vedono una
      separazione **netta** fra le famiglie, non una differenza del 10 %: una
      causa che spostasse `cwnd` del 10 % resterebbe invisibile.
   3. **una terza modalita' rara.**  Con p=0,05 venti giri hanno il **36 %** di
      probabilita' di non incontrarla nemmeno una volta.
   4. ⚠⚠ **niente di quel che accade FRA UN SECONDO E L'ALTRO.**
      `[R]` `webtransport.c:4573`: `rete_ciclo()` si frena da solo a **una riga
      al secondo** (`if (rete_detto_ms && ora_ms - rete_detto_ms < 1000) return`)
      e non esiste nessuna opzione ne' variabile d'ambiente che la cambi
      (`main.c:978-1140`: `--parlantina` accende le righe di dettaglio, non la
      cadenza).  La prima riga esce subito, poi una al secondo.
      ⇒ **Della corsa di `cwnd` nell'avvio lento vedo il punto d'arrivo, non la
        corsa**: la stretta di mano e i primi round trip durano meno di un
        secondo e stanno tutti dentro il primo campione.
      ⛔ E' un limite dello strumento, e **non lo aggiro**: dove serve la grana
        del millisecondo si usa il registro degli EVENTI (l'abbandono §5.1 e la
        chiave spedita portano l'ora al millesimo), non un'interpolazione fra
        due campioni al secondo.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ I PREDICATI — SCRITTI PRIMA, e ne torna `(passa, perche)`
═══════════════════════════════════════════════════════════════════════════════

`passa` vale `None` quando il banco **rifiuta di giudicare** (`CODER.md` §3.10).

  **B · `p_due_rami()`** — I6.  Le chiavi a regime sono **zero-o-molte** o una
  scala?  · verde = e' bistabile (≥4 giri a zero, ≥4 con ≥5 chiavi, e meno di 3
  giri nella terra di mezzo) · **rosso** = ≥3 giri con 1..4 chiavi ⇒ e' un
  CONTINUO, e la parola «bistabile» non regge · muto = una famiglia sotto i 4.

  **F · `p_famiglie_confrontabili()`** — ho quattro giri per famiglia?  · muto
  se no, e allora tutti i confronti tacciono.

  **S · `p_separa()`** — una grandezza distingue le due famiglie?  Test di
  permutazione esatto sulla differenza delle mediane, p ≤ 0,00116.
  · verde = separa · rosso = non separa · muto = famiglie troppo piccole.
  ⚠ Verde e rosso qui non sono «buono» e «cattivo»: sono «distingue» e «non
    distingue», e per I0 e I2 e' il **rosso** l'esito che assolve l'ipotesi.

  **P · `p_precede()`** — ⭐⭐ **IL PREDICATO PER CUI QUESTO BANCO ESISTE.**
  La separazione e' un **precursore** o un'**eco**?
  · verde = la prima separazione arriva **prima** dell'accensione della spirale
    (il primo abbandono §5.1) ⇒ la biforcazione sta nei primi secondi, I5 cade;
  · **rosso** = la separazione arriva **all'accensione o dopo** ⇒ quei numeri
    registrano la spirale, non la spiegano, e I1 NON e' verificata;
  · muto = nessuna grandezza separa, o l'accensione non si e' letta.
  ⛔⛔ E «l'accensione» e' il **primo abbandono §5.1 A REGIME** (oltre i 3 s di
     scaldata), non il primo in assoluto.  `[M]` 24 ago 2026, giro di prova di
     questo banco: a perdita **ZERO** il registro porta gia' un abbandono §5.1
     al secondo **1,095** — e' l'apertura di sessione, non la spirale.  ⇒ Col
     primo in assoluto l'accensione starebbe attorno al secondo 1 in TUTTI i
     giri e questo predicato sarebbe **rosso per costruzione**.  ⚠ Il taglio e'
     lo stesso che decide le famiglie (`09-b70.SCALDATA_S`): se l'etichetta
     ignora la scaldata, deve ignorarla anche l'istante.

  **D · `p_denominatore()`** — lo zero d'apertura contro lo zero di chiusura
  (`09-b80.p_due_gruppi_uguali`).  Rosso = la macchina e' derivata **durante** i
  venti giri, e allora la «biforcazione» puo' essere la deriva.
  ⛔ Senza questo, una deriva lenta si leggerebbe come due rami.

I CODICI D'USCITA
    0   CONFORME · 1 NON CONFORME (c'e' un rosso) · 2 uso/terreno/rete
    3   ⛔ NON HO NIENTE DA GIUDICARE — un giro o un predicato si e' rifiutato

Uso (dal portatile):
    python3 banchi/09-b83-biforcazione.py --certifica     ⭐ senza macchina
    python3 banchi/09-b83-biforcazione.py terreno
    python3 banchi/09-b83-biforcazione.py giri [--giri 20] [--secondi 25]
    python3 banchi/09-b83-biforcazione.py giudica          # rilegge e giudica
    python3 banchi/09-b83-biforcazione.py rimetti
"""
import argparse, importlib.util, itertools, json, math, os, random, re
import statistics, sys, time

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ L'ISOLAMENTO, SCRITTO PRIMA DELL'IMPORT CHE LO LEGGE
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `09-b80` (e dentro di lui `09-b76`, `09-b70`, `07-b65`) legano le costanti
#    all'ambiente **all'import**: un `setdefault` che arriva primo vince.  ⇒
#    L'ambiente si mette QUI.  Un import fatto e poi corretto scriverebbe nel
#    lavoro di un altro agente e guasterebbe la porta di un altro banco.
#
# ⛔ Le 7900, 7910, 7920 sono la sessione VIVA dell'utente e i termini di
#    paragone: non si toccano.  Mia e' la **7971**.
PORTA = int(os.environ.setdefault("PORTA", "7971"))
os.environ.setdefault("PORTE_SONDA", "7979,7978,7977,7976,7975")
UTENTE = os.environ.setdefault("UTENTE", "provanr8")
UID_B = int(os.environ.setdefault("UID_B", "1071"))
MACCHINA = os.environ.setdefault("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.setdefault("PAROLA_SUDO", "nicfio")
IND = os.environ.setdefault("IND", "192.168.0.2")
LAV = os.environ.setdefault("LAV", "/media/REMOTIX/tmp/09nr8")
ALB = os.environ.setdefault("ALBERO", "/media/REMOTIX/src/09nr8-src")
os.environ.setdefault("DENTRO_ALB", "/srv/src/" + os.path.basename(ALB))
os.environ.setdefault("DENTRO_LAV", "/srv/remotix/tmp/09nr8")
# ⛔ La memoria condivisa della scena e' MIA: `shm_open` di un file di un altro
#    utente da' EACCES e la scena muore all'avvio — un guasto che assomiglia in
#    tutto a «il compositore non consegna».
SHM = os.environ.setdefault("SHM", "/09nr8")
FUORI = os.environ.setdefault("FUORI", "/tmp/09-b83")
# ⭐ La sonda fitta di `09-b80`: a 0,2 % di perdita 8 000 pacchetti ne perdono
#    sedici, e sedici non misurano due decimi di punto percentuale.
os.environ.setdefault("SONDA_PACCHETTI", "20000")

QUI = os.path.dirname(os.path.abspath(__file__))
DEV = "lo"
VIETATA = "enp7s0"
CHI = "09-b83"        # ⛔ il nome col quale prendo il lucchetto del netem

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


def _carica(nome, percorso):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


B80 = None
B76 = None
B70 = None
RETE = None
LUC = None


def importa(con_macchina=True):
    """⛔⛔ E POI SI CONTROLLA CHE ABBIANO PRESO IL MIO AMBIENTE.

    ⚠ Non e' cerimonia: se per qualsiasi ragione il mio `setdefault` non fosse
      arrivato primo, girerei sulla porta **7950** — dentro il banco di un altro
      agente — e i numeri sarebbero plausibili e falsi.

    ⛔ E `09-b80.importa()` NON si puo' chiamare: quella funzione ha la memoria
       condivisa `/09nr5` **scritta a mano** nei suoi controlli
       (`09-b80-dirupo.py:265`), e con la mia `/09nr8` si rifiuterebbe.  ⇒ Si
       fanno i suoi stessi controlli qui, e gli si INIETTANO i moduli:
       `09-b80` non si tocca (ha una griglia certificata e altri la leggono).
    """
    global B80, B76, B70, RETE, LUC
    B76 = _carica("b76rete", os.path.join(QUI, "09-b76-rete-cattiva.py"))
    B80 = _carica("b80dirupo", os.path.join(QUI, "09-b80-dirupo.py"))
    guai = []
    for nome, mio, suo in (("porta", PORTA, B76.PORTA), ("utente", UTENTE, B76.UTENTE),
                           ("uid", UID_B, B76.UID_B), ("lavoro", LAV, B76.LAV),
                           ("albero", ALB, B76.ALB), ("shm", SHM, B76.SHM)):
        if mio != suo:
            guai.append("09-b76 ha «%s» per %s, il mio e' «%s»" % (suo, nome, mio))
    for nome, mio, suo in (("porta", PORTA, B80.PORTA), ("utente", UTENTE, B80.UTENTE),
                           ("uid", UID_B, B80.UID_B), ("lavoro", LAV, B80.LAV),
                           ("albero", ALB, B80.ALB)):
        if mio != suo:
            guai.append("09-b80 ha «%s» per %s, il mio e' «%s»" % (suo, nome, mio))
    if B76.PORTA in (7900, 7910, 7920, 7930, 7950) or B76.UTENTE in (
            "prova", "prova2", "provanr1", "provanr5"):
        guai.append("⛔ girerei dentro il banco (o la sessione) di un altro: NON misuro")
    if guai:
        raise SystemExit("⛔ NON MISURO: l'import non ha preso il mio ambiente — "
                         + " · ".join(guai))
    if not con_macchina:
        B76.importa_finto()
        B70 = B76.B70
    else:
        B70 = B76.importa()
        RETE = B76.RETE
        LUC = B76.LUC
        if RETE.PORTA != PORTA or RETE.DEV != DEV or RETE.VIETATA != VIETATA:
            raise SystemExit("⛔ NON TOCCO LA RETE: il modulo della rete ha porta "
                             "%d, dev «%s», vietata «%s»"
                             % (RETE.PORTA, RETE.DEV, RETE.VIETATA))
        _aggancia_giornale()
    # ⛔ L'INIEZIONE: `09-b80.cella()` vive sui suoi globali, e sono questi.
    B80.B76, B80.B70, B80.RETE, B80.LUC = B76, B70, RETE, LUC


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL GIORNALE DEI FOTOGRAMMI, CHE `misura()` BUTTA VIA
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `09-b70.misura()` riduce il giornale a cinque numeri e **non lo restituisce**
#    (`09-b70-ritmo.py:601`): dei singoli fotogrammi non resta niente.  A me
#    servono i BYTE e l'ISTANTE dei primi — cioe' il controllo di I2.
#
# ⭐ Rileggere la traccia una seconda volta costerebbe dieci secondi a giro e
#    duecento minuti di macchina in piu' su tutta la campagna.  ⇒ Si sostituisce
#    la funzione con una che tiene da parte il giornale prima di passarlo —
#    che e' la stessa disciplina con cui `09-b76` aggancia la consegna
#    (`09-b76-rete-cattiva.py:464`) **senza toccare il file di b70**.
#    ⚠ E si aggancia DOPO `B76.importa()`, cosi' la sua sostituzione resta sotto
#      la mia e continua a funzionare.
ULTIMO_GIORNALE = {"g": None}


def _aggancia_giornale():
    vecchia = B70.misura

    def nuova(giornale, *r, **k):
        ULTIMO_GIORNALE["g"] = list(giornale or [])
        return vecchia(giornale, *r, **k)
    B70.misura = nuova


# ═══════════════════════════════════════════════════════════════════════════
# LE COSTANTI DEL BANCO — in un posto solo, e ciascuna con la sua ragione
# ═══════════════════════════════════════════════════════════════════════════
PERDITA_CHIESTA = 0.2     # % — ⛔ la casella dove `[M]` 09-b80 ha visto le due
                          #     uscite.  Non si sposta: spostarla vorrebbe dire
                          #     misurare un'altra domanda.
FINESTRA_S = 10.0         # ⛔ «la storia dei primi 10 secondi», dal mandato
SCENA_PRIMI_S = 3.0       # per il costo in byte di I2 — ed e' anche la scaldata
                          # che `09-b70.misura()` toglie (`SCALDATA_S = 3.0`)
GIRI = 20                 # ⇒ §«QUANTI GIRI», e il conto e' li'
GIRI_DENOM = 2            # lo zero, in apertura e in chiusura
MINIMO_FAMIGLIA = 4       # ⛔ sotto, nemmeno una separazione perfetta arriva
                          #    alla soglia: 2/C(20,3) = 0,00175 > 0,00116
CHIAVI_MOLTE = 5          # ⚠ *sufficiente, non giusta*: `[M]` 23 ago i due rami
                          #   erano 0 e 24, e una manciata di chiavi isolate non
                          #   e' la spirale — la spirale si autoalimenta.
TERRA_DI_MEZZO_MAX = 2    # ⇒ da 3 giri in su con 1..4 chiavi e' un CONTINUO
PROVE_DICHIARATE = 43     # 13 grandezze riassuntive + 30 secondo per secondo
SOGLIA_P = 0.05 / PROVE_DICHIARATE       # = 0,001163
PERMUTAZIONI_ESATTE_MAX = 300000
PERMUTAZIONI_CAMPIONE = 50000
SSTHRESH_INF = (1 << 64) - 1
# ⭐ ngtcp2 parte con `ssthresh = UINT64_MAX`: «l'avvio lento non e' mai uscito».
#    ⇒ Un valore finito **e' l'evento**, e non serve nessuna soglia per vederlo.
SENTINELLA_S = 99.0       # ⚠ «non e' mai successo dentro la finestra».  Si usa
                          #   per poter stare in una mediana; ⛔ e si stampa
                          #   sempre quanti giri hanno la sentinella, o una
                          #   mediana di sentinelle sembrerebbe una misura.
SENTINELLA_KB = 1000000.0


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LE GRANDEZZE — l'elenco e' SCRITTO PRIMA, e il conto delle prove viene
#    da qui: se qualcuno ne aggiunge una, `PROVE_DICHIARATE` va rifatto
# ═══════════════════════════════════════════════════════════════════════════
#  (chiave, etichetta, unita', a quale ipotesi serve)
GRANDEZZE = [
    ("ssthresh_giu_s",   "quando ssthresh lascia l'infinito", "s",   "I1"),
    ("ssthresh_min_kb",  "il minimo FINITO di ssthresh",      "kB",  "I1"),
    ("cwnd_max_kb",      "il massimo di cwnd",                "kB",  "I1"),
    ("cwnd_fine_kb",     "cwnd a fine finestra",              "kB",  "I1"),
    ("cwnd_min_kb",      "il minimo di cwnd",                 "kB",  "I1"),
    ("involo_max_kb",    "il massimo di bytes_in_flight",     "kB",  "I1"),
    ("srtt_max_us",      "il massimo di srtt",                "us",  "I1"),
    ("persi_fin",        "pacchetti QUIC dichiarati persi",   "pk",  "I4"),
    ("primo_perso_s",    "quando «persi» lascia lo zero",     "s",   "I4"),
    ("vera_pc",          "⭐ la perdita VERA della sonda",     "%",   "I0"),
    ("byte_primi_kb",    "⭐ il costo dei primi %g s di scena" % SCENA_PRIMI_S,
                                                              "kB",  "I2"),
    ("byte_prima_chiave_kb", "⭐ i byte della PRIMA chiave",   "kB",  "I2"),
    ("cpu_pc",           "la CPU occupata durante il giro",   "%",   "carico"),
]
assert len(GRANDEZZE) + 30 == PROVE_DICHIARATE, \
    "⛔ le grandezze e il conto delle prove non coincidono piu'"

# ⭐ E le tre grandezze che si guardano SECONDO PER SECONDO, per rispondere alla
#    sola domanda che conta: **quando** le due famiglie cominciano a differire.
SECONDO_PER_SECONDO = [("cwnd_kb", "cwnd", "kB"),
                       ("ssthresh_finito", "ssthresh e' gia' finito (0/1)", ""),
                       ("persi", "pacchetti persi finora", "pk")]
SECONDI_GUARDATI = list(range(1, 11))     # 10 secondi × 3 grandezze = 30 prove


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA STORIA DI UN GIRO — le righe `rete-quic` e gli EVENTI, sullo stesso
#    orologio
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Il registro del server porta l'ora al millesimo in testa a ogni riga
#    (`HH:MM:SS.mmm  area  testo`).  ⇒ Le righe `rete-quic` (una al secondo) e
#    gli eventi della spirale (al millesimo) stanno **sullo stesso orologio**, e
#    si possono confrontare senza interpolare niente.
#    ⚠ Il giornale del cliente ha un orologio SUO (monotono del client): i suoi
#      numeri si usano per i BYTE, mai per gli istanti del server.
ORA = re.compile(r"^(\d\d):(\d\d):(\d\d)\.(\d\d\d)\s")


def _ora(riga):
    m = ORA.match(riga)
    if not m:
        return None
    h, mi, s, ms = (int(x) for x in m.groups())
    return h * 3600 + mi * 60 + s + ms / 1000.0


def _campi_quic(riga):
    """⛔ Il formato e' un CONTRATTO SUL TESTO (`webtransport.c:4210-4272`):
       prefisso stabile, `nome=valore` senza spazi nel valore, e `giudizio=`
       ULTIMO col valore che arriva a fine riga."""
    if "rete-quic " not in riga:
        return None
    corpo = riga.split("rete-quic ", 1)[1]
    if "giudizio=" in corpo:
        corpo = corpo.split("giudizio=", 1)[0]
    d = {}
    for p in corpo.split():
        if "=" in p:
            k, v = p.split("=", 1)
            try:
                d[k] = int(v)
            except ValueError:
                d[k] = v
    return d


def _tail_grep(riga0, espressione, extra=""):
    rc, out, _ = B76.root("bash -c \"tail -n +%d %s/registro.log | grep -a %s '%s' "
                          "|| true\"" % (riga0 + 1, LAV, extra, espressione))
    return [r for r in out.splitlines() if r.strip()]


def _conta(riga0, espressione):
    rc, out, _ = B76.root("bash -c \"tail -n +%d %s/registro.log | grep -ac '%s' "
                          "|| true\"" % (riga0 + 1, LAV, espressione))
    t = out.strip()
    return int(t) if t.isdigit() else None


def storia(riga0):
    """⭐⭐ LA STORIA DEI PRIMI SECONDI, PRESA DAL REGISTRO DEL SERVER.

    ⛔ Non giudica: legge e riduce.  ⚠ E se non c'e' nemmeno una riga
      `rete-quic`, torna «NIENTE DA LEGGERE» — che non e' «zero».
    """
    righe = _tail_grep(riga0, "rete-quic ")
    campi = [(_ora(r), _campi_quic(r)) for r in righe]
    campi = [(t, d) for t, d in campi if t is not None and d]
    st = {"righe_quic": len(campi)}
    if not campi:
        st["esito"] = ("NIENTE DA LEGGERE — nessuna riga «rete-quic» in questo "
                       "giro (⚠ il server e' quello che credo?)")
        return st
    st["esito"] = "letto"
    t0 = campi[0][0]
    st["t0"] = t0
    # ── il campionamento vero, dichiarato e non assunto ────────────────────
    passi = [round(campi[i][0] - campi[i - 1][0], 3) for i in range(1, len(campi))]
    st["passo_mediano_s"] = statistics.median(passi) if passi else None
    st["passo_max_s"] = max(passi) if passi else None
    serie = []
    for t, d in campi:
        ss = d.get("ssthresh")
        serie.append({
            "t": round(t - t0, 3),
            "cwnd_kb": (d.get("cwnd") or 0) / 1024.0,
            "ssthresh": ss,
            "ssthresh_finito": 0 if (ss is None or ss >= (1 << 62)) else 1,
            "involo_kb": (d.get("involo") or 0) / 1024.0,
            "persi": d.get("persi"),
            "spediti": d.get("spediti"),
            "srtt_us": d.get("srtt_us"),
            "rttvar_us": d.get("rttvar_us"),
            "cwnd_left_kb": (d.get("cwnd_left") or 0) / 1024.0})
    st["serie"] = serie
    dentro = [x for x in serie if x["t"] <= FINESTRA_S]
    if not dentro:
        dentro = serie[:1]
    st["campioni_in_finestra"] = len(dentro)

    # ── le grandezze riassuntive della finestra ────────────────────────────
    finiti = [x["ssthresh"] for x in dentro if x["ssthresh_finito"]]
    giu = [x["t"] for x in dentro if x["ssthresh_finito"]]
    st["ssthresh_giu_s"] = min(giu) if giu else SENTINELLA_S
    st["ssthresh_min_kb"] = (min(finiti) / 1024.0) if finiti else SENTINELLA_KB
    st["cwnd_max_kb"] = max(x["cwnd_kb"] for x in dentro)
    st["cwnd_min_kb"] = min(x["cwnd_kb"] for x in dentro)
    st["cwnd_fine_kb"] = dentro[-1]["cwnd_kb"]
    st["involo_max_kb"] = max(x["involo_kb"] for x in dentro)
    srtt = [x["srtt_us"] for x in dentro if x["srtt_us"] is not None]
    st["srtt_max_us"] = max(srtt) if srtt else None
    persi = [x["persi"] for x in dentro if x["persi"] is not None]
    st["persi_fin"] = persi[-1] if persi else None
    con_persi = [x["t"] for x in dentro
                 if x["persi"] is not None and x["persi"] > 0]
    st["primo_perso_s"] = min(con_persi) if con_persi else SENTINELLA_S
    # ── e i valori secondo per secondo: l'ultimo campione fino al secondo s ─
    #    ⚠ «fino a» e non «al»: la cadenza e' una al secondo ma non e' un
    #      metronomo (`da_ms` puo' valere 1200), e prendere «il campione con
    #      t esattamente s» darebbe buchi che sembrerebbero dati mancanti.
    st["al_secondo"] = {}
    for s in SECONDI_GUARDATI:
        fino = [x for x in serie if x["t"] <= s + 0.001]
        st["al_secondo"][str(s)] = (
            {k: fino[-1][k] for k, _, _ in SECONDO_PER_SECONDO} if fino else None)
    return st


def eventi(riga0):
    """⭐⭐ L'ACCENSIONE DELLA SPIRALE, al millesimo — e non e' la stessa cosa
       della prima chiave.

    ⛔ Le prime una o due chiavi di ogni sessione sono **strutturali**:
       `rcp.c:3003` («e' il primo dopo SESSIONE») e `rcp.c:3492` («il primo alla
       misura nuova dopo TELA»).  Prenderle per l'inizio della spirale
       metterebbe l'accensione a zero in TUTTI i giri, compresi quelli sani.
    ⇒ L'accensione e' un **abbandono §5.1** (`rcp.c:3852`): e' quello che accende
      il debito di chiave che si autoalimenta (`rcp.c:3859`).

    ⛔⛔ MA NON IL PRIMO: **il primo A REGIME.**  `[M]` 24 ago 2026, giro di
        prova di questo stesso banco: a perdita **ZERO** il registro porta gia'
        un abbandono §5.1 al secondo **1,095** — e' l'apertura di sessione, la
        prima chiave e la prima tela che si accavallano, non la spirale.
        ⇒ Prendendo il primo, l'accensione starebbe attorno al secondo 1 in
          **tutti** i giri, compresi quelli sani, e `p_precede` darebbe «eco»
          per costruzione: il banco sarebbe rosso prima di misurare.
    ⇒ Il taglio e' lo STESSO che decide le famiglie: `09-b70.misura()` toglie i
      primi **%g s** (`SCALDATA_S`) e conta le chiavi solo a regime.  Se
      l'etichetta ignora la scaldata, deve ignorarla anche l'istante.
    ⚠ E i due orologi non coincidono al millesimo: il mio zero e' la prima riga
      `rete-quic` (apertura di sessione), quello di `09-b70` e' l'arrivo del
      primo fotogramma al client, che viene **dopo**.  ⇒ Il mio taglio cade un
      filo PRIMA del suo, quindi la mia accensione e' un **estremo inferiore** —
      e sbagliare per difetto rende `p_precede` piu' difficile da far diventare
      verde, non piu' facile.
    """ % SCENA_PRIMI_S
    e = {}
    for chiave, espressione in (
            ("abbandono", "ABBANDONATO NELLA CODA"),
            ("non_spedito", "FOTOGRAMMA NON SPEDITO"),
            ("sopra_soglia", "passa SOPRA la soglia"),
            ("chiave_spedita", "SPEDITO: CHIAVE")):
        righe = _tail_grep(riga0, espressione, extra="-m 200")
        ore = [_ora(r) for r in righe]
        ore = [t for t in ore if t is not None]
        e[chiave + "_ore"] = ore[:200]
        e[chiave + "_primo"] = ore[0] if ore else None
        e[chiave + "_quanti"] = _conta(riga0, espressione)
    righe = _tail_grep(riga0, "AMMESSO", extra="-m 2")
    e["ammesso"] = ([_ora(r) for r in righe] or [None])[0]
    return e


def accensione(ore_abbandono, t0):
    """⭐⭐ L'ACCENSIONE DELLA SPIRALE — il primo abbandono §5.1 **a regime**.

    `None` = non si e' mai accesa (⛔ e non e' «zero»: e' quel che ci si aspetta
    dai giri della famiglia «liscio», che per definizione non hanno chiavi a
    regime, e un abbandono a regime ne produrrebbe una).
    """
    tardi = [round(t - t0, 3) for t in ore_abbandono
             if (t - t0) >= SCENA_PRIMI_S]
    return min(tardi) if tardi else None


def dal_giornale(giornale):
    """⭐ I BYTE dei primi fotogrammi — il controllo di I2, e viene dal CLIENTE.

    ⚠ L'orologio qui e' quello del client: si usano i byte, non gli istanti.
    """
    g = {"fotogrammi_traccia": len(giornale or [])}
    if not giornale:
        g["esito"] = "NIENTE DA LEGGERE — la traccia non ha fotogrammi"
        return g
    g["esito"] = "letto"
    a0 = giornale[0]["arrivo_ms"]
    primi = [f for f in giornale
             if (f["arrivo_ms"] - a0) / 1000.0 < SCENA_PRIMI_S]
    g["fotogrammi_primi"] = len(primi)
    g["byte_primi_kb"] = sum(f["byte"] for f in primi) / 1024.0
    chiavi = [f for f in giornale if f.get("chiave")]
    g["byte_prima_chiave_kb"] = (chiavi[0]["byte"] / 1024.0) if chiavi else None
    g["chiavi_traccia"] = len(chiavi)
    g["byte_per_fotogramma_primi"] = (
        int(sum(f["byte"] for f in primi) / len(primi)) if primi else None)
    # ⭐ E il costo MEDIO dei soli delta, che e' la grandezza che I2 vuole
    #    davvero: una scena piu' cara si vede sui delta, non sulle chiavi.
    delta = [f for f in primi if not f.get("chiave")]
    g["byte_per_delta_primi"] = (
        int(sum(f["byte"] for f in delta) / len(delta)) if delta else None)
    return g


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ IL TEST — permutazione esatta sulla SOMMA DEI RANGHI
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Non un `t` di Student e non un `U` con l'approssimazione normale: le
#    famiglie sono di quattro o cinque giri, le grandezze hanno sentinelle e
#    code lunghe, e un test che assumesse una forma darebbe un `p` che sembra
#    una probabilita' e non lo e'.
# ⭐ La permutazione non assume niente: rimescola le etichette e conta quante
#    volte il caso fa altrettanto bene.  ⚠ E si dichiara se e' stata ESATTA
#    (tutte le combinazioni) o CAMPIONATA.
#
# ⛔⛔ E LA STATISTICA E' LA SOMMA DEI RANGHI, NON LA DIFFERENZA DELLE MEDIANE —
#     e a insegnarmelo e' stato `--certifica`, prima di toccare la macchina.
#
#     `[M]` 24 ago 2026, controllo positivo: con la differenza delle MEDIANE una
#     separazione **perfetta** a 4 contro 16 da' p = **0,00165**, non 0,00041.
#     La ragione e' che la mediana e' grossolana: su 4845 combinazioni ce ne
#     sono **otto** che producono una differenza di mediane grande almeno
#     quanto quella osservata, perche' spostare il valore piu' estremo non
#     muove la mediana.  ⇒ Con la soglia dichiarata (0,00116) il test **non
#     avrebbe potuto dare verde nemmeno su una separazione perfetta**, e il
#     banco avrebbe girato un'ora per essere muto per costruzione.
#
#     ⭐ Con la somma dei ranghi (che e' l'`U` di Mann-Whitney, ma calcolato per
#       enumerazione invece che approssimato) l'assegnazione estrema e' UNA
#       sola per lato: p = 2/C(20,4) = **0,000413**, che e' il numero scritto in
#       testa al file.  ⚠ E i ranghi si fanno a **meta' strada** sui pari
#       merito: le grandezze qui hanno sentinelle, e le sentinelle sono tutte
#       uguali fra loro.
def _ranghi(v):
    """I ranghi a meta' strada sui pari merito (1-based)."""
    ordine = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(ordine):
        j = i
        while j + 1 < len(ordine) and v[ordine[j + 1]] == v[ordine[i]]:
            j += 1
        meta = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[ordine[k]] = meta
        i = j + 1
    return r


def _p_permutazione(a, b, semino=1971):
    """(p, come) — a due code sulla somma dei ranghi del primo gruppo.
       `(None, ...)` se non c'e' abbastanza da confrontare."""
    a = [x for x in a if x is not None]
    b = [x for x in b if x is not None]
    if len(a) < 1 or len(b) < 1:
        return (None, "un gruppo e' vuoto")
    tutti = list(a) + list(b)
    n, k = len(tutti), len(a)
    r = _ranghi(tutti)
    atteso = k * (n + 1) / 2.0        # la somma dei ranghi sotto il caso
    oss = abs(sum(r[:k]) - atteso)
    quante = math.comb(n, k)
    if quante <= PERMUTAZIONI_ESATTE_MAX:
        estremi = 0
        for idx in itertools.combinations(r, k):
            if abs(sum(idx) - atteso) >= oss - 1e-9:
                estremi += 1
        return (estremi / float(quante), "ranghi, esatto su %d combinazioni" % quante)
    g = random.Random(semino)
    estremi = 0
    indici = list(range(n))
    for _ in range(PERMUTAZIONI_CAMPIONE):
        g.shuffle(indici)
        if abs(sum(r[i] for i in indici[:k]) - atteso) >= oss - 1e-9:
            estremi += 1
    # ⚠ Il `+1` non e' prudenza: senza, una separazione perfetta darebbe p=0, e
    #   uno zero qui vorrebbe dire «impossibile», che nessun campionamento sa.
    return ((estremi + 1) / float(PERMUTAZIONI_CAMPIONE + 1),
            "ranghi, campionato su %d estrazioni (le combinazioni sono %d)"
            % (PERMUTAZIONI_CAMPIONE, quante))


def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)


def _riass(v):
    v = [x for x in v if x is not None]
    if not v:
        return "—"
    return ("mediana %.4g · %.4g…%.4g" % (statistics.median(v), min(v), max(v)))


def p_separa(nome, unita, va, vb, nome_a="spirale", nome_b="liscio"):
    """**S · UNA GRANDEZZA DISTINGUE LE DUE FAMIGLIE?**

    · verde = separa (p ≤ soglia) · rosso = non separa · muto = famiglie piccole.
    ⚠ Verde e rosso non sono «buono» e «cattivo»: per I0 e I2 e' il **rosso**
      l'esito che assolve l'ipotesi.
    """
    a = [x for x in va if x is not None]
    b = [x for x in vb if x is not None]
    if len(a) < MINIMO_FAMIGLIA or len(b) < MINIMO_FAMIGLIA:
        return _muto("«%s»: ho %d «%s» e %d «%s» validi, e sotto i %d nemmeno "
                     "una separazione perfetta arriverebbe alla soglia"
                     % (nome, len(a), nome_a, len(b), nome_b, MINIMO_FAMIGLIA))
    p, come = _p_permutazione(a, b)
    sovr = (min(a) <= max(b) and min(b) <= max(a))
    coda = ("%s %s: %s  |  %s %s: %s  |  p = %.5f (%s) · %s"
            % (nome_a, unita, _riass(a), nome_b, unita, _riass(b), p, come,
               "le escursioni si SOVRAPPONGONO" if sovr
               else "⭐ le escursioni NON si sovrappongono"))
    if p <= SOGLIA_P:
        return _si("⭐ «%s» SEPARA le due famiglie — %s (soglia %.5f)"
                   % (nome, coda, SOGLIA_P))
    return _no("«%s» non separa le due famiglie — %s (soglia %.5f)"
               % (nome, coda, SOGLIA_P))


def p_due_rami(chiavi):
    """**B · I6 — LE CHIAVI SONO ZERO-O-MOLTE, O UNA SCALA?**

    ⛔ E' il primo predicato di tutti, perche' se le chiavi fossero una scala
       continua le ipotesi da I1 a I4 cercherebbero un interruttore che non c'e'.
    """
    v = [c for c in chiavi if c is not None]
    if len(v) < 2 * MINIMO_FAMIGLIA:
        return _muto("ho %d giri validi su %d: sotto i %d non posso dire se sia "
                     "bistabile" % (len(v), len(chiavi), 2 * MINIMO_FAMIGLIA))
    zero = [c for c in v if c == 0]
    molte = [c for c in v if c >= CHIAVI_MOLTE]
    mezzo = [c for c in v if 1 <= c < CHIAVI_MOLTE]
    coda = ("%d giri a ZERO chiavi · %d con almeno %d · %d nella terra di mezzo "
            "(1..%d) — chiavi per giro: %s"
            % (len(zero), len(molte), CHIAVI_MOLTE, len(mezzo), CHIAVI_MOLTE - 1,
               sorted(v)))
    if len(mezzo) > TERRA_DI_MEZZO_MAX:
        return _no("⛔⛔ NON E' UNA BIFORCAZIONE, E' UN CONTINUO: %s ⇒ la parola "
                   "«bistabile» del 23 agosto non regge, e i due giri di allora "
                   "erano le due code della stessa distribuzione larga" % coda)
    if len(zero) < MINIMO_FAMIGLIA or len(molte) < MINIMO_FAMIGLIA:
        return _muto("⚠ la bistabilita' NON si e' ripresentata su questa "
                     "casella: %s ⇒ con meno di %d giri per famiglia non ho due "
                     "famiglie da confrontare" % (coda, MINIMO_FAMIGLIA))
    return _si("⭐ E' BISTABILE, e non e' un continuo: %s" % coda)


def p_famiglie_confrontabili(n_spirale, n_liscio):
    """**F · HO QUATTRO GIRI PER FAMIGLIA?**  ⛔ E se no, tutto il resto tace."""
    if n_spirale < MINIMO_FAMIGLIA or n_liscio < MINIMO_FAMIGLIA:
        return _muto("ho %d giri «spirale» e %d «liscio»: sotto i %d per "
                     "famiglia il test di permutazione non puo' produrre un p "
                     "sotto la soglia nemmeno con una separazione perfetta "
                     "(2/C(20,3) = 0,00175 > %.5f) ⇒ i confronti TACCIONO, e la "
                     "regola d'arresto scritta prima dice di aggiungere un "
                     "secondo blocco di %d giri"
                     % (n_spirale, n_liscio, MINIMO_FAMIGLIA, SOGLIA_P, GIRI))
    return _si("%d giri «spirale» e %d «liscio»: sopra il minimo di %d, i "
               "confronti si possono fare" % (n_spirale, n_liscio,
                                              MINIMO_FAMIGLIA))


def p_precede(secondo_separazione, quale, accensione_s):
    """**P · ⭐⭐ IL PREDICATO PER CUI QUESTO BANCO ESISTE.**

    La separazione fra le due famiglie e' un **precursore** o un'**eco**?

      · verde = la prima separazione arriva **prima** dell'accensione della
        spirale ⇒ la biforcazione sta nei primi secondi: I5 cade e I1 regge;
      · **rosso** = arriva all'accensione o **dopo** ⇒ quei numeri registrano la
        spirale invece di spiegarla, e I1 NON e' verificata.  ⛔ E' l'unico modo
        per cui I1 puo' fallire senza sembrare confermata;
      · muto = nessuna grandezza separa, oppure l'accensione non si e' letta.
    """
    if secondo_separazione is None:
        return _muto("nessuna delle %d prove secondo-per-secondo separa le due "
                     "famiglie dentro i primi %g s: non ho un istante di "
                     "separazione da confrontare con l'accensione"
                     % (len(SECONDI_GUARDATI) * len(SECONDO_PER_SECONDO),
                        FINESTRA_S))
    if accensione_s is None:
        return _muto("la separazione compare al secondo %g su «%s», ma nella "
                     "famiglia «spirale» non ho letto nessun abbandono §5.1: "
                     "senza l'istante d'accensione non so dire se preceda"
                     % (secondo_separazione, quale))
    coda = ("la prima separazione compare al secondo **%g** su «%s»; la spirale "
            "si accende (primo abbandono §5.1) al secondo **%.3f** (mediana "
            "della famiglia «spirale»)" % (secondo_separazione, quale,
                                           accensione_s))
    if secondo_separazione < accensione_s:
        return _si("⭐⭐ LA SEPARAZIONE E' UN PRECURSORE: %s ⇒ il ramo e' gia' "
                   "deciso %.3f s PRIMA che la spirale si accenda: la "
                   "biforcazione sta nei primi secondi" % (coda,
                                                           accensione_s - secondo_separazione))
    return _no("⛔⛔ LA SEPARAZIONE E' UN'ECO, NON UN PRECURSORE: %s ⇒ i numeri "
               "dei primi secondi REGISTRANO la spirale, non la spiegano, e "
               "l'ipotesi dell'avvio lento NON e' verificata da questa misura"
               % coda)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ UN GIRO — e' la `cella()` di `09-b80`, piu' la storia dei primi secondi
# ═══════════════════════════════════════════════════════════════════════════
def giro(nome, regole, verifica, secondi, etichetta=""):
    """⛔ Non riscrive nessuna riga di `09-b80.cella()`: la CHIAMA, e ci mette
       attorno la sola cosa che li' non c'era — la storia dei primi secondi.

    ⛔ `riga0` si prende PRIMA della cella, non dopo: fra qui e il giro ci sono
       la sonda e l'accensione della scena, che non aprono nessuna sessione e
       quindi non scrivono nessuna riga `rete-quic`.  ⚠ E si verifica: se le
       righe lette fossero piu' del doppio dei secondi chiesti, avrei preso
       dentro anche il giro precedente, e il banco lo dice.
    """
    riga0 = B76.righe_registro()
    ULTIMO_GIORNALE["g"] = None
    c = B80.cella(nome, regole, verifica, secondi, etichetta=etichetta)
    c["riga0"] = riga0
    if riga0 is None or riga0 <= 0:
        c["storia"] = {"esito": "NIENTE DA LEGGERE — il registro non si e' "
                                "letto prima del giro"}
        c["eventi"] = {}
        c["traccia"] = {"esito": "non guardata"}
        return c
    c["storia"] = storia(riga0)
    c["eventi"] = eventi(riga0)
    c["traccia"] = dal_giornale(ULTIMO_GIORNALE["g"])
    st, ev = c["storia"], c["eventi"]
    if st.get("esito") == "letto":
        if st["righe_quic"] > 2 * secondi:
            st["sospetto"] = ("⚠ %d righe «rete-quic» per %d secondi chiesti: "
                              "potrei aver preso dentro anche il giro precedente"
                              % (st["righe_quic"], secondi))
            _dub(st["sospetto"])
        for k, _, _, _ in GRANDEZZE:
            if k in st:
                c[k] = st[k]
        # ⭐ L'accensione, in secondi dal primo campione: e' l'istante che
        #    `p_precede` confronta con la separazione.  ⇒ `accensione()` spiega
        #    perche' e' il primo A REGIME e non il primo in assoluto.
        c["primo_abbandono_s"] = (round(ev["abbandono_primo"] - st["t0"], 3)
                                  if ev.get("abbandono_primo") is not None else None)
        c["accensione_s"] = accensione(ev.get("abbandono_ore") or [], st["t0"])
    else:
        c["accensione_s"] = None
        c["primo_abbandono_s"] = None
    for k in ("byte_primi_kb", "byte_prima_chiave_kb"):
        c[k] = c["traccia"].get(k)
    stampa_storia(c)
    return c


def stampa_storia(c):
    st, ev, tr = c.get("storia") or {}, c.get("eventi") or {}, c.get("traccia") or {}
    if st.get("esito") != "letto":
        _dub("STORIA  %s" % st.get("esito"))
    else:
        _inf("STORIA  %d righe «rete-quic» · passo mediano %s s (max %s) · %d "
             "campioni nei primi %g s"
             % (st["righe_quic"], st.get("passo_mediano_s"), st.get("passo_max_s"),
                st.get("campioni_in_finestra"), FINESTRA_S))
        _inf("        ssthresh giu' al secondo %s · minimo finito %s kB · cwnd "
             "%s…%s kB (fine %s) · involo max %s kB"
             % (st.get("ssthresh_giu_s"),
                _n(st.get("ssthresh_min_kb")), _n(st.get("cwnd_min_kb")),
                _n(st.get("cwnd_max_kb")), _n(st.get("cwnd_fine_kb")),
                _n(st.get("involo_max_kb"))))
        _inf("        persi %s pacchetti · primo perso al secondo %s · srtt max "
             "%s us" % (st.get("persi_fin"), st.get("primo_perso_s"),
                        st.get("srtt_max_us")))
        _inf("        i primi %g s, secondo per secondo: %s" % (
            FINESTRA_S,
            " | ".join("%d: cwnd %s kB ss%s persi %s"
                       % (s, _n((st["al_secondo"].get(str(s)) or {}).get("cwnd_kb")),
                          (st["al_secondo"].get(str(s)) or {}).get("ssthresh_finito"),
                          (st["al_secondo"].get(str(s)) or {}).get("persi"))
                       for s in SECONDI_GUARDATI
                       if st["al_secondo"].get(str(s)))))
    _inf("SPIRALE ⭐ accensione (primo abbandono §5.1 A REGIME, oltre %g s) al "
         "secondo %s · il primo in assoluto al %s (⚠ scaldata) · abbandoni %s · "
         "«non spediti» %s · chiavi spedite %s · sopra soglia %s"
         % (SCENA_PRIMI_S, c.get("accensione_s"), c.get("primo_abbandono_s"),
            ev.get("abbandono_quanti"), ev.get("non_spedito_quanti"),
            ev.get("chiave_spedita_quanti"), ev.get("sopra_soglia_quanti")))
    _inf("SCENA   %s fotogrammi nei primi %g s · %s kB · %s byte/delta · prima "
         "chiave %s kB"
         % (tr.get("fotogrammi_primi"), SCENA_PRIMI_S, _n(tr.get("byte_primi_kb")),
            tr.get("byte_per_delta_primi"), _n(tr.get("byte_prima_chiave_kb"))))


def _n(x):
    return ("%.1f" % x) if isinstance(x, (int, float)) else "?"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL GIUDIZIO — e le famiglie si tagliano col criterio gia' scritto
# ═══════════════════════════════════════════════════════════════════════════
def famiglie(celle):
    """⛔ Il taglio e' quello di `09-b80.rotto_chiavi()`: «la quota di chiavi
       lascia lo zero» (§3.3), che e' il MECCANISMO e non il sintomo.
       ⚠ Non si taglia sui fotogrammi/s: una soglia sul ritmo sarebbe un numero
         scelto da me, e questa e' esattamente la mossa che la fase ha gia'
         dovuto ritirare."""
    buone = [c for c in celle if c.get("esito") == "misurato"]
    sp = [c for c in buone if B80.rotto_chiavi(c)]
    li = [c for c in buone if not B80.rotto_chiavi(c)]
    return sp, li


def val(celle, chiave):
    return [c.get(chiave) for c in celle]


def giudica(d):
    rossi, muti, verdi = [], [], []
    celle = d["celle"]
    buone = [c for c in celle if c.get("esito") == "misurato"]

    _log("⭐ I VENTI GIRI, uno per riga — e le sentinelle si vedono")
    print("   %-4s %6s %7s %6s %8s %9s %8s %8s %7s %6s"
          % ("giro", "fps", "chiavi", "vera%", "ssgiu_s", "ssmin_kB",
             "cwndmax", "persi", "acces.", "cpu%"))
    for i, c in enumerate(celle, 1):
        if c.get("esito") != "misurato":
            _dub("%-4d %s" % (i, c.get("esito")))
            continue
        print("   %-4d %6s %7s %6s %8s %9s %8s %8s %7s %6s"
              % (i, c.get("fps"), c.get("chiavi"), c.get("vera_pc"),
                 c.get("ssthresh_giu_s"), _n(c.get("ssthresh_min_kb")),
                 _n(c.get("cwnd_max_kb")), c.get("persi_fin"),
                 c.get("accensione_s"), c.get("cpu_pc")))

    # ── B · I6: e' una biforcazione, o un continuo? ────────────────────────
    _log("B · ⭐ I6 — E' UNA BIFORCAZIONE, O UN CONTINUO?")
    passa, perche = p_due_rami(val(buone, "chiavi"))
    (_ok if passa else (_dub if passa is None else _ko))("B · %s" % perche)
    if passa is False:
        rossi.append("B · I6 REGGE: non e' una biforcazione, e' un continuo")
    elif passa is None:
        muti.append("B · I6 — %s" % perche[:120])
    else:
        verdi.append("B · I6 ESCLUSA: le chiavi sono zero-o-molte")

    sp, li = famiglie(celle)
    _log("F · LE DUE FAMIGLIE")
    _inf("«spirale» (chiavi ≥ 1 a regime): %d giri · fps %s · chiavi %s"
         % (len(sp), _riass(val(sp, "fps")), sorted(x for x in val(sp, "chiavi")
                                                    if x is not None)))
    _inf("«liscio»  (zero chiavi)        : %d giri · fps %s"
         % (len(li), _riass(val(li, "fps"))))
    passa, perche = p_famiglie_confrontabili(len(sp), len(li))
    (_ok if passa else (_dub if passa is None else _ko))("F · %s" % perche)
    d["n_spirale"], d["n_liscio"] = len(sp), len(li)
    if passa is None:
        muti.append("F · %s" % perche[:140])

    # ── S · le tredici grandezze riassuntive ───────────────────────────────
    _log("S · ⭐⭐ QUALE GRANDEZZA DISTINGUE I DUE RAMI? — %d prove, soglia "
         "%.5f (0,05 / %d, Bonferroni)"
         % (PROVE_DICHIARATE, SOGLIA_P, PROVE_DICHIARATE))
    esiti = {}
    for k, etichetta, unita, ipotesi in GRANDEZZE:
        pa, pe = p_separa("%s [%s]" % (etichetta, ipotesi), unita,
                          val(sp, k), val(li, k))
        (_ok if pa else (_dub if pa is None else _ko))("S · %s" % pe)
        esiti[k] = {"passa": pa, "perche": pe, "ipotesi": ipotesi}
        if pa is None:
            muti.append("S · %s" % etichetta)
    d["separazioni"] = esiti

    # ── S2 · secondo per secondo: QUANDO cominciano a differire ────────────
    _log("S · ⭐⭐ E QUANDO COMINCIANO A DIFFERIRE? — secondo per secondo")
    primo_s, primo_quale = None, None
    per_secondo = {}
    for s in SECONDI_GUARDATI:
        for k, etichetta, unita in SECONDO_PER_SECONDO:
            va = [(c.get("storia", {}).get("al_secondo", {}).get(str(s)) or {}).get(k)
                  for c in sp]
            vb = [(c.get("storia", {}).get("al_secondo", {}).get(str(s)) or {}).get(k)
                  for c in li]
            pa, pe = p_separa("%s al secondo %d" % (etichetta, s), unita, va, vb)
            per_secondo["%s@%d" % (k, s)] = {"passa": pa, "perche": pe}
            if pa:
                _ok("S · %s" % pe)
                if primo_s is None:
                    primo_s, primo_quale = float(s), etichetta
            elif pa is None:
                pass          # gia' detto da F: non si ripete trenta volte
            else:
                _inf("s=%2d %-32s p oltre la soglia" % (s, etichetta))
    d["per_secondo"] = per_secondo
    d["prima_separazione_s"], d["prima_separazione_quale"] = primo_s, primo_quale
    if primo_s is None:
        _dub("⚠ nessuna delle %d prove secondo-per-secondo separa le due "
             "famiglie" % (len(SECONDI_GUARDATI) * len(SECONDO_PER_SECONDO)))

    # ── P · precursore o eco? ──────────────────────────────────────────────
    _log("P · ⭐⭐ LA SEPARAZIONE E' UN PRECURSORE O UN'ECO?")
    acc = [c.get("accensione_s") for c in sp if c.get("accensione_s") is not None]
    acc_med = statistics.median(acc) if acc else None
    _inf("accensione della spirale nei %d giri «spirale»: %s"
         % (len(sp), sorted(acc) if acc else "MAI LETTA"))
    passa, perche = p_precede(primo_s, primo_quale, acc_med)
    (_ok if passa else (_dub if passa is None else _ko))("P · %s" % perche)
    d["accensione_mediana_s"] = acc_med
    if passa is False:
        rossi.append("P · la separazione e' un'eco: I1 NON e' verificata")
    elif passa is None:
        muti.append("P · %s" % perche[:140])
    else:
        verdi.append("P · la separazione PRECEDE l'accensione")

    # ── ⭐⭐ il ritratto dei due rami (DESCRITTIVO, non una prova) ──
    stampa_confronto(d, sp, li, primo_s, acc_med)

    # ── D · il denominatore ha retto? ──────────────────────────────────────
    _log("D · IL DENOMINATORE HA RETTO PER TUTTI I VENTI GIRI?")
    va = [c.get("fps") for c in d.get("apertura", []) if c.get("esito") == "misurato"]
    vb = [c.get("fps") for c in d.get("chiusura", []) if c.get("esito") == "misurato"]
    passa, perche = B80.p_due_gruppi_uguali("zero d'apertura", va,
                                            "zero di chiusura", vb,
                                            B80.METRO_MINIMO, "IL DENOMINATORE")
    (_ok if passa else (_dub if passa is None else _ko))("D · %s" % perche)
    if passa is False:
        rossi.append("D · la macchina e' derivata durante i venti giri: la "
                     "«biforcazione» puo' essere la deriva")
    elif passa is None:
        muti.append("D · il denominatore — %s" % perche[:120])

    # ── L'ESITO DI OGNI IPOTESI, scritto accanto a quel che l'ha deciso ────
    _log("⭐⭐ L'ESITO DI OGNI IPOTESI — e ciascuna col fatto che l'ha decisa")
    d["ipotesi"] = tira_le_somme(d, esiti, primo_s, passa)
    for riga in d["ipotesi"]:
        print("   %s" % riga)
    return rossi, muti, verdi


def tira_le_somme(d, esiti, primo_s, denom_ok):
    """⛔ Nessuna causa **plausibile e non verificata**: ogni riga qui sotto dice
       che cosa l'ha decisa, o dichiara che resta aperta."""
    def stato(chiavi):
        v = [esiti.get(k, {}).get("passa") for k in chiavi]
        if any(x is None for x in v):
            return None
        return any(v)
    fuori = []

    s0 = stato(["vera_pc"])
    if s0 is None:
        fuori.append("I0 la perdita non era la stessa  ⇒ ⚠ NON GIUDICATA "
                     "(famiglie troppo piccole)")
    elif s0:
        fuori.append("I0 la perdita non era la stessa  ⇒ ⛔ REGGE: la perdita "
                     "VERA separa le famiglie — non e' una biforcazione, e' la "
                     "scala fine vista da vicino")
    else:
        fuori.append("I0 la perdita non era la stessa  ⇒ ⭐ ESCLUSA: la perdita "
                     "vera (sonda a 20 000 pacchetti) NON separa le famiglie")

    s1 = stato(["ssthresh_giu_s", "ssthresh_min_kb", "cwnd_max_kb",
                "cwnd_fine_kb", "cwnd_min_kb", "involo_max_kb"])
    if s1 is None:
        fuori.append("I1 l'avvio lento di CUBIC     ⇒ ⚠ NON GIUDICATA")
    elif not s1:
        fuori.append("I1 l'avvio lento di CUBIC     ⇒ ⛔ NON VERIFICATA: "
                     "ssthresh e cwnd dei primi %g s NON separano le famiglie"
                     % FINESTRA_S)
    elif denom_ok is False:
        fuori.append("I1 l'avvio lento di CUBIC     ⇒ ⚠ SOSPESA: separa, ma il "
                     "denominatore e' derivato e non posso attribuire")
    elif primo_s is None:
        fuori.append("I1 l'avvio lento di CUBIC     ⇒ ⚠ PARZIALE: le grandezze "
                     "riassuntive separano, ma nessun singolo secondo lo fa ⇒ "
                     "non so dire se preceda l'accensione")
    elif d.get("accensione_mediana_s") is None:
        fuori.append("I1 l'avvio lento di CUBIC     ⇒ ⚠ PARZIALE: separa al "
                     "secondo %g, ma l'accensione non si e' letta" % primo_s)
    elif primo_s < d["accensione_mediana_s"]:
        fuori.append("I1 l'avvio lento di CUBIC     ⇒ ⭐⭐ REGGE: separa al "
                     "secondo %g, cioe' %.3f s PRIMA dell'accensione della "
                     "spirale (%.3f s)"
                     % (primo_s, d["accensione_mediana_s"] - primo_s,
                        d["accensione_mediana_s"]))
    else:
        fuori.append("I1 l'avvio lento di CUBIC     ⇒ ⛔ NON VERIFICATA: la "
                     "separazione (secondo %g) NON precede l'accensione "
                     "(%.3f s) — e' un'eco"
                     % (primo_s, d["accensione_mediana_s"]))

    s2 = stato(["byte_primi_kb", "byte_prima_chiave_kb"])
    if s2 is None:
        fuori.append("I2 la scena                   ⇒ ⚠ NON GIUDICATA")
    elif s2:
        fuori.append("I2 la scena                   ⇒ ⛔ REGGE: il costo in "
                     "byte dei primi fotogrammi separa le famiglie — i giri NON "
                     "erano identici nel contenuto")
    else:
        fuori.append("I2 la scena                   ⇒ ⭐ ESCLUSA: il costo in "
                     "byte dei primi %g s non separa le famiglie" % SCENA_PRIMI_S)

    fuori.append("I3 l'algoritmo non scelto     ⇒ `[R]` LETTO, non misurato: "
                 "CUBIC (ngtcp2 1.25.0, `trasporto.c:628` non tocca `cc_algo`). "
                 "⚠ La prova per contrasto NON e' fatta: `cc_algo` non e' "
                 "esposto da nessuna opzione e `src/` non e' mio")

    s4 = stato(["persi_fin", "primo_perso_s"])
    if s4 is None:
        fuori.append("I4 la soglia dei tre pacchetti⇒ ⚠ NON GIUDICATA")
    elif s4:
        fuori.append("I4 la soglia dei tre pacchetti⇒ ⭐ REGGE (in parte): le "
                     "perdite DICHIARATE nei primi %g s separano le famiglie. "
                     "⚠ Con una riga al secondo non vedo il singolo evento di "
                     "dichiarazione: dico quando e quante, non quale terzo "
                     "pacchetto" % FINESTRA_S)
    else:
        fuori.append("I4 la soglia dei tre pacchetti⇒ ⛔ NON VERIFICATA: ne' il "
                     "numero di perdite dichiarate ne' l'istante della prima "
                     "separano le famiglie")

    if primo_s is None:
        fuori.append("I5 non sta nei primi secondi  ⇒ ⭐ REGGE: NESSUNA delle "
                     "%d prove sui primi %g s separa le famiglie ⇒ il ramo non "
                     "e' deciso all'avvio, o non e' deciso da quel che so "
                     "guardare" % (len(SECONDI_GUARDATI) * len(SECONDO_PER_SECONDO),
                                   FINESTRA_S))
    else:
        fuori.append("I5 non sta nei primi secondi  ⇒ ⛔ SMENTITA: le famiglie "
                     "differiscono gia' al secondo %g" % primo_s)
    return fuori


# ════════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL RITRATTO DEI DUE RAMI — «che cosa distingue uno 0 chiavi da un 28»
# ════════════════════════════════════════════════════════════════════════════
#
# ⛔⛔ QUESTA PARTE E' **DESCRITTIVA**, e la riga che segue non e' modestia:
#     **le prove sono le 43 dichiarate in testa, e non queste.**  Un numero
#     guardato dopo aver visto i dati e poi promosso a prova e' esattamente la
#     mossa che questa fase ha gia' dovuto ritirare due volte.  ⇒ Qui si
#     DISEGNA il meccanismo; a giudicare ci pensano `p_separa` e `p_precede`.
#
# ⛔ E c'e' un'asimmetria che va detta prima di leggere qualunque tabella: la
#    famiglia «liscio» **non ha** una prima chiave a regime ne' un'accensione —
#    e' la sua definizione.  ⇒ Le grandezze «all'accensione» si possono
#    guardare **solo** nella famiglia «spirale», e non sono un confronto: sono
#    un ritratto.  Il confronto fra le due famiglie si fa **a istanti fissi**
#    (secondo per secondo), che e' l'unico modo di chiedere la stessa cosa a
#    tutt'e due.
def stato_a(serie, t):
    """Lo stato della rete all'istante `t`: l'ULTIMO campione al piu' tardi a `t`.

    ⚠ E **non si interpola**: fra due campioni c'e' un secondo intero
      (`webtransport.c:4573` si frena da solo), e un valore interpolato sarebbe
      un numero inventato con la faccia di una misura.
    """
    if not serie or t is None:
        return None
    fino = [x for x in serie if x["t"] <= t + 1e-9]
    return fino[-1] if fino else None


def prima_chiave_regime(c):
    """L'istante della prima chiave spedita **a regime** — lo stesso taglio
       dell'accensione.  `None` nella famiglia «liscio», dove per definizione
       non ce n'e' nessuna (⛔ e `None` qui vuol dire «non ce n'e'», non «zero»)."""
    ev, st = c.get("eventi") or {}, c.get("storia") or {}
    t0 = st.get("t0")
    if st.get("esito") != "letto" or t0 is None:
        return None
    tardi = [round(t - t0, 3) for t in (ev.get("chiave_spedita_ore") or [])
             if (t - t0) >= SCENA_PRIMI_S]
    return min(tardi) if tardi else None


def ritratto(c):
    """Come stava la rete quando la spirale si e' accesa, e quando ha spedito la
       sua prima chiave a regime."""
    st = c.get("storia") or {}
    serie, ev = st.get("serie") or [], c.get("eventi") or {}
    r = {"accensione_s": c.get("accensione_s"),
         "chiave_s": prima_chiave_regime(c)}
    for come, t in (("all_accensione", r["accensione_s"]),
                    ("alla_chiave", r["chiave_s"])):
        x = stato_a(serie, t)
        r[come] = ({"cwnd_kb": round(x["cwnd_kb"], 1),
                    "ssthresh_finito": x["ssthresh_finito"],
                    "ssthresh_kb": (round(x["ssthresh"] / 1024.0, 1)
                                    if x["ssthresh_finito"] else None),
                    "involo_kb": round(x["involo_kb"], 1),
                    "persi": x["persi"], "srtt_us": x["srtt_us"]} if x else None)
    t0 = st.get("t0")
    if st.get("esito") == "letto" and t0 is not None:
        r["abbandoni_10s"] = sum(1 for t in (ev.get("abbandono_ore") or [])
                                 if (t - t0) <= FINESTRA_S)
        r["chiavi_10s"] = sum(1 for t in (ev.get("chiave_spedita_ore") or [])
                              if (t - t0) <= FINESTRA_S)
    return r


def _med(v):
    v = [x for x in v if x is not None]
    return statistics.median(v) if v else None


def stampa_confronto(d, sp, li, primo_s, acc_med):
    """⭐⭐ LA DOMANDA VERA, DISEGNATA: che cosa distingue un giro «0 chiavi»
       da un giro «28 chiavi» nei primi dieci secondi?

    ⛔ E sa dire di NO: se le due famiglie non differiscono in nessuna delle
       grandezze dei primi secondi, la risposta e' *«non e' nei primi dieci
       secondi»* — che e' un risultato valido, e molto migliore di una causa
       plausibile e non verificata.
    """
    _log("⭐⭐ IL RITRATTO DEI DUE RAMI — ⚠ DESCRITTIVO: le prove sono le %d "
         "dichiarate in testa, non queste" % PROVE_DICHIARATE)
    if not sp or not li:
        _dub("⚠ una delle due famiglie e' vuota: non c'e' nessun ritratto da "
             "disegnare (spirale %d · liscio %d)" % (len(sp), len(li)))
        return
    for c in d["celle"]:
        if c.get("esito") == "misurato":
            c["ritratto"] = ritratto(c)

    _inf("—— A ISTANTI FISSI, la stessa domanda a tutt'e due (mediana ed "
         "escursione) ——")
    print("   %-32s %21s %21s" % ("", "spirale (n=%d)" % len(sp),
                                  "liscio (n=%d)" % len(li)))

    def riga(etichetta, va, vb, fmt="%.1f"):
        def q(v):
            v = [x for x in v if x is not None]
            if not v:
                return "—"
            return ((fmt + " (" + fmt + "…" + fmt + ")")
                    % (statistics.median(v), min(v), max(v)))
        print("   %-32s %21s %21s" % (etichetta, q(va), q(vb)))

    for s in (1, 2, 3, 5, 10):
        for k, et, un in SECONDO_PER_SECONDO:
            va = [(c.get("storia", {}).get("al_secondo", {}).get(str(s)) or {}).get(k)
                  for c in sp]
            vb = [(c.get("storia", {}).get("al_secondo", {}).get(str(s)) or {}).get(k)
                  for c in li]
            riga("%s @ %2d s" % (et.split(" (")[0][:22], s), va, vb,
                 "%.1f" if k == "cwnd_kb" else "%.0f")
    for k, et in (("ssthresh_giu_s", "ssthresh lascia l'infinito [s]"),
                  ("ssthresh_min_kb", "ssthresh minimo finito [kB]"),
                  ("cwnd_max_kb", "cwnd massima [kB]"),
                  ("primo_perso_s", "⭐ «persi» si muove [s]"),
                  ("persi_fin", "persi nei primi 10 s [pk]"),
                  ("vera_pc", "⛔ perdita VERA, sonda [%]"),
                  ("byte_primi_kb", "⛔ costo dei primi 3 s [kB]"),
                  ("cpu_pc", "⛔ cpu del giro [%]")):
        riga(et, val(sp, k), val(li, k), "%.3f" if k == "vera_pc" else "%.1f")

    _inf("—— ⭐ SOLO «spirale»: com'era la rete quando si e' accesa ——")
    _inf("⛔ Qui NON c'e' confronto: la famiglia «liscio» non ha ne' "
         "accensione ne' chiave a regime, ed e' la sua definizione.")
    rit = [c["ritratto"] for c in sp if c.get("ritratto")]
    acc = [r["all_accensione"] for r in rit if r.get("all_accensione")]
    chi = [r["alla_chiave"] for r in rit if r.get("alla_chiave")]
    _inf("accensione (primo abbandono §5.1 a regime) al secondo: mediana %s · %s"
         % (_n(_med([r["accensione_s"] for r in rit])),
            sorted(x for x in (r["accensione_s"] for r in rit) if x is not None)))
    _inf("prima chiave A REGIME al secondo: mediana %s"
         % _n(_med([r["chiave_s"] for r in rit])))
    for come, gruppo in (("ALL'ACCENSIONE", acc), ("ALLA PRIMA CHIAVE", chi)):
        if not gruppo:
            _dub("%s: nessun campione" % come)
            continue
        _inf("%-18s cwnd %s kB · ssthresh gia' finito in %d/%d giri (mediana %s "
             "kB) · involo %s kB · persi %s · srtt %s us"
             % (come, _n(_med([x["cwnd_kb"] for x in gruppo])),
                sum(1 for x in gruppo if x["ssthresh_finito"]), len(gruppo),
                _n(_med([x["ssthresh_kb"] for x in gruppo])),
                _n(_med([x["involo_kb"] for x in gruppo])),
                _n(_med([x["persi"] for x in gruppo])),
                _n(_med([x["srtt_us"] for x in gruppo]))))
    for c in li:
        c["ritratto"] = c.get("ritratto") or ritratto(c)
    _inf("abbandoni §5.1 nei primi %g s — spirale: %s · liscio: %s"
         % (FINESTRA_S,
            sorted(r.get("abbandoni_10s") for r in rit
                   if r.get("abbandoni_10s") is not None),
            sorted((c.get("ritratto") or {}).get("abbandoni_10s") for c in li
                   if (c.get("ritratto") or {}).get("abbandoni_10s") is not None)))

    # ── ⭐⭐ LA RISPOSTA, E SA DIRE DI NO ──────────────────────────────────
    _log("⭐⭐ LA RISPOSTA ALLA DOMANDA VERA")
    if primo_s is None:
        _dub("⛔ **NON E' NEI PRIMI %g SECONDI** — nessuna delle %d prove "
             "secondo-per-secondo distingue un giro «0 chiavi» da un giro con "
             "la spirale. ⭐ E' un risultato valido: il ramo non e' deciso "
             "dall'avvio, oppure non e' deciso da quel che questo strumento sa "
             "guardare (una riga al secondo)."
             % (FINESTRA_S, len(SECONDI_GUARDATI) * len(SECONDO_PER_SECONDO)))
    elif acc_med is None:
        _dub("⚠ le famiglie differiscono gia' al secondo %g, ma senza "
             "l'istante d'accensione non posso dire se sia una causa o un'eco"
             % primo_s)
    elif primo_s < acc_med:
        _ok("⭐⭐ **SI', ED E' NEI PRIMI %g SECONDI**: le due famiglie "
            "differiscono gia' al secondo %g, cioe' %.1f s PRIMA che la spirale "
            "si accenda (secondo %.1f). ⇒ Il ramo e' deciso all'avvio."
            % (FINESTRA_S, primo_s, acc_med - primo_s, acc_med))
    else:
        _ko("⛔ **NO**: la prima differenza (secondo %g) NON precede "
            "l'accensione (secondo %.1f) ⇒ quel che si vede nei primi secondi "
            "e' la spirale che gia' gira, non la sua causa."
            % (primo_s, acc_med))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL CONTROLLO POSITIVO — «come fa questo banco a sapere di saper vedere?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `PIANO.md` §0.3.4: *«un banco che non sa vedere il difetto che cerca non ha
#    diritto al verde»*.  ⇒ Qui si fabbricano numeri e si controlla che i
#    predicati diano quel che e' scritto PRIMA — verde, rosso **e muto**.
def _c(chiavi, fps=35.0, **extra):
    c = {"esito": "misurato", "chiavi": chiavi, "fps": fps}
    c.update(extra)
    return c


def certifica():
    print("⭐ CERTIFICAZIONE DEL BANCO DELLA BIFORCAZIONE — l'atteso e' scritto "
          "PRIMA\n")
    print("   ⛔ Nessun contatto con la macchina di prova: qui si prova lo "
          "STRUMENTO,\n      non il prodotto.\n")
    importa(con_macchina=False)
    verde = True
    n = [0]

    def caso(titolo, atteso, avuto):
        n[0] += 1
        passa, perche = avuto
        ok = (passa is atteso) if atteso is None else (passa == atteso)
        print("  %2d · %s" % (n[0], titolo))
        print("       atteso %-5s   avuto %-5s   %s" % (atteso, passa, perche[:170]))
        if ok:
            _ok("come scritto")
        else:
            _ko("⛔ IL BANCO NON SA VEDERE QUEL CHE DICE DI CERCARE")
        return ok

    # ── il conto dei giri, che e' l'argomento e non un commento ────────────
    _log("⛔ IL CONTO DEI GIRI — la soglia e il minimo per famiglia sono "
         "COERENTI?")
    n[0] += 1
    p4 = 2.0 / math.comb(20, 4)
    p3 = 2.0 / math.comb(20, 3)
    print("  %2d · il p piu' piccolo possibile: 4 su 20 ⇒ %.5f · 3 su 20 ⇒ "
          "%.5f · soglia %.5f" % (n[0], p4, p3, SOGLIA_P))
    if p4 <= SOGLIA_P < p3 and MINIMO_FAMIGLIA == 4:
        _ok("⭐ il minimo di 4 per famiglia e' esattamente il piu' piccolo che "
            "possa arrivare alla soglia — e a 3 non ci arriverebbe")
    else:
        _ko("⛔ il minimo per famiglia e la soglia non si giustificano a "
            "vicenda"); verde = False

    # ── B · p_due_rami ─────────────────────────────────────────────────────
    _log("B · ⭐ «le chiavi sono zero-o-molte, o una scala?»")
    verde &= caso("dieci a zero e dieci a molte ⇒ VERDE (e' bistabile)", True,
                  p_due_rami([0] * 10 + [24, 30, 18, 40, 22, 27, 19, 33, 25, 21]))
    verde &= caso("⛔ una scala continua (0,1,2,3,4,…) ⇒ ROSSO (non e' una "
                  "biforcazione)", False,
                  p_due_rami([0, 0, 0, 0, 1, 2, 3, 4, 2, 3, 6, 8, 9, 12, 14,
                              16, 18, 20, 22, 24]))
    verde &= caso("⛔ tutti a zero (la bistabilita' non si e' ripresentata) ⇒ "
                  "MUTO", None, p_due_rami([0] * 20))
    verde &= caso("⛔ tre soli giri validi ⇒ MUTO", None, p_due_rami([0, 0, 30]))
    verde &= caso("⚠ due soli giri nella terra di mezzo NON bastano per il "
                  "rosso ⇒ VERDE", True,
                  p_due_rami([0] * 9 + [2, 3] + [20, 25, 30, 22, 28, 26, 31,
                                                 19, 24]))

    # ── F · p_famiglie_confrontabili ───────────────────────────────────────
    _log("F · «ho quattro giri per famiglia?»")
    verde &= caso("4 e 16 ⇒ VERDE", True, p_famiglie_confrontabili(4, 16))
    verde &= caso("⛔ 3 e 17 ⇒ MUTO (nemmeno una separazione perfetta ci "
                  "arriverebbe)", None, p_famiglie_confrontabili(3, 17))
    verde &= caso("⛔ 20 e 0 ⇒ MUTO", None, p_famiglie_confrontabili(20, 0))

    # ── S · p_separa ───────────────────────────────────────────────────────
    _log("S · ⭐⭐ «una grandezza distingue le due famiglie?»")
    verde &= caso("⭐ separazione PERFETTA a 4 contro 16 ⇒ VERDE", True,
                  p_separa("finta", "kB", [10, 11, 12, 13],
                           [90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101,
                            102, 103, 104, 105]))
    verde &= caso("⛔ due nuvole sovrapposte ⇒ ROSSO (non separa)", False,
                  p_separa("finta", "kB", [50, 60, 40, 55],
                           [52, 58, 44, 61, 49, 57, 43, 62, 51, 59, 45, 60,
                            48, 56, 42, 63]))
    verde &= caso("⛔ una famiglia a 3 ⇒ MUTO", None,
                  p_separa("finta", "kB", [10, 11, 12],
                           [90, 91, 92, 93, 94, 95, 96]))
    verde &= caso("⚠ una separazione MEDIA (il 20 %) a 4 contro 16 NON arriva "
                  "alla soglia ⇒ ROSSO: e' il limite dichiarato al punto 2",
                  False,
                  p_separa("finta", "kB", [80, 84, 88, 92],
                           [96, 100, 104, 108, 112, 92, 88, 116, 120, 84, 124,
                            80, 128, 76, 132, 72]))
    n[0] += 1
    p, come = _p_permutazione([1, 2, 3, 4], list(range(10, 26)))
    print("  %2d · il p esatto di una separazione perfetta 4-16 vale %.6f "
          "(%s)" % (n[0], p, come))
    if abs(p - 2.0 / math.comb(20, 4)) < 1e-9:
        _ok("⭐ e' esattamente 2/C(20,4): il test e' esatto, non approssimato")
    else:
        _ko("⛔ il test non produce il p esatto"); verde = False

    # ── P · p_precede ──────────────────────────────────────────────────────
    _log("P · ⭐⭐ «precursore o eco?»")
    verde &= caso("⭐ separa al secondo 2, la spirale si accende al 6,5 ⇒ VERDE "
                  "(precursore)", True, p_precede(2.0, "cwnd", 6.5))
    verde &= caso("⛔ separa al secondo 7, la spirale si accende al 6,5 ⇒ ROSSO "
                  "(eco)", False, p_precede(7.0, "cwnd", 6.5))
    verde &= caso("⛔ separa esattamente all'accensione ⇒ ROSSO (non precede)",
                  False, p_precede(6.5, "cwnd", 6.5))
    verde &= caso("⛔ nessuna separazione ⇒ MUTO", None,
                  p_precede(None, None, 6.5))
    verde &= caso("⛔ accensione mai letta ⇒ MUTO", None,
                  p_precede(2.0, "cwnd", None))

    # ── la lettura del testo: il contratto di `rete-quic` ──────────────────
    _log("⛔ IL CONTRATTO SUL TESTO — la riga `rete-quic` si legge sul TESTO")
    riga = ("19:00:31.658 wt      rete-quic 127.0.0.1:41234 da_ms=1001 persi=7 "
            "persi_d=3 byte_persi=9100 byte_persi_d=4300 spediti=2210 "
            "spediti_d=810 byte_spediti=3100000 ricevuti=402 ricevuti_d=140 "
            "scartati=0 scartati_d=0 cwnd=28900 cwnd_left=4100 ssthresh=26000 "
            "involo=24800 srtt_us=31200 latest_us=30800 rttvar_us=2100 "
            "min_rtt_us=30100 coda_rete_us=1100 pto_us=98000 dgram_persi=0 "
            "dgram_persi_d=0 dgram_ok=0 dgram_falsi=0 dgram_falsi_d=0 "
            "giudizio=⛔ la linea perde")
    n[0] += 1
    d = _campi_quic(riga)
    t = _ora(riga)
    print("  %2d · ora %s · cwnd %s · ssthresh %s · persi %s · involo %s"
          % (n[0], t, d.get("cwnd"), d.get("ssthresh"), d.get("persi"),
             d.get("involo")))
    if (abs(t - (19 * 3600 + 31.658)) < 1e-6 and d["cwnd"] == 28900
            and d["ssthresh"] == 26000 and d["persi"] == 7 and d["involo"] == 24800
            and "giudizio" not in d):
        _ok("⭐ il contratto si legge, e il `giudizio=` con gli spazi non entra "
            "fra i campi")
    else:
        _ko("⛔ la riga non si legge come il contratto dice"); verde = False
    n[0] += 1
    print("  %2d · una riga che NON e' `rete-quic` ⇒ None" % n[0])
    if _campi_quic("19:00:31.658 rcp     fotogramma 12 SPEDITO") is None:
        _ok("come scritto")
    else:
        _ko("⛔ ha letto campi da una riga che non e' la sua"); verde = False

    # ── la riduzione della storia, su righe FABBRICATE ─────────────────────
    _log("⭐⭐ LA STORIA SI RIDUCE — e si prova su righe fabbricate, come il "
         "contratto")
    n[0] += 1
    inf = SSTHRESH_INF
    finte = []
    for i, (cw, ss, pe) in enumerate([(12000, inf, 0), (48000, inf, 0),
                                      (96000, inf, 0), (70000, 68000, 4),
                                      (72000, 68000, 4), (74000, 68000, 6)]):
        finte.append("19:00:%02d.100 wt      rete-quic 127.0.0.1:1 da_ms=1000 "
                     "persi=%d spediti=100 cwnd=%d cwnd_left=10 ssthresh=%d "
                     "involo=%d srtt_us=%d rttvar_us=100 giudizio=--"
                     % (30 + i, pe, cw, ss, cw // 2, 30000 + 100 * i))
    vecchia = globals()["_tail_grep"]
    globals()["_tail_grep"] = lambda r, e, extra="": (
        finte if "rete-quic" in e else [])
    try:
        st = storia(1)
    finally:
        globals()["_tail_grep"] = vecchia
    print("  %2d · %d righe · ssthresh giu' al secondo %s · minimo finito %s kB "
          "· cwnd max %s kB · primo perso al secondo %s · persi finali %s"
          % (n[0], st["righe_quic"], st["ssthresh_giu_s"],
             _n(st["ssthresh_min_kb"]), _n(st["cwnd_max_kb"]),
             st["primo_perso_s"], st["persi_fin"]))
    if (st["righe_quic"] == 6 and abs(st["ssthresh_giu_s"] - 3.0) < 1e-6
            and abs(st["ssthresh_min_kb"] - 68000 / 1024.0) < 1e-6
            and abs(st["cwnd_max_kb"] - 96000 / 1024.0) < 1e-6
            and abs(st["primo_perso_s"] - 3.0) < 1e-6 and st["persi_fin"] == 6
            and st["al_secondo"]["2"]["ssthresh_finito"] == 0
            and st["al_secondo"]["4"]["ssthresh_finito"] == 1
            and st["al_secondo"]["9"] is not None):
        _ok("⭐ la storia si riduce come scritto, e «l'ultimo campione FINO al "
            "secondo s» tiene anche dove non c'e' un campione")
    else:
        _ko("⛔ la riduzione della storia non fa quel che dice"); verde = False
    n[0] += 1
    print("  %2d · ssthresh che non scende MAI ⇒ la sentinella, non uno zero"
          % n[0])
    globals()["_tail_grep"] = lambda r, e, extra="": (
        [x.replace("ssthresh=68000", "ssthresh=%d" % inf) for x in finte]
        if "rete-quic" in e else [])
    try:
        st2 = storia(1)
    finally:
        globals()["_tail_grep"] = vecchia
    if (st2["ssthresh_giu_s"] == SENTINELLA_S
            and st2["ssthresh_min_kb"] == SENTINELLA_KB):
        _ok("come scritto: «non e' mai successo» ha una faccia sua e non e' "
            "zero (`CODER.md` §3.10)")
    else:
        _ko("⛔ «mai sceso» e «sceso a zero» hanno la stessa faccia"); verde = False
    n[0] += 1
    print("  %2d · nessuna riga `rete-quic` ⇒ NIENTE DA LEGGERE, non zero" % n[0])
    globals()["_tail_grep"] = lambda r, e, extra="": []
    try:
        st3 = storia(1)
    finally:
        globals()["_tail_grep"] = vecchia
    if st3.get("esito", "").startswith("NIENTE DA LEGGERE"):
        _ok("come scritto")
    else:
        _ko("⛔ una storia vuota ha prodotto dei numeri"); verde = False

    # ── il giornale ────────────────────────────────────────────────────────
    _log("⭐ IL COSTO DELLA SCENA, dal giornale del cliente")
    n[0] += 1
    gio = ([{"arrivo_ms": 1000 + 25 * i, "byte": 8000, "chiave": (i == 0)}
            for i in range(200)])
    g = dal_giornale(gio)
    print("  %2d · %d fotogrammi nei primi %g s · %.1f kB · prima chiave %.1f kB"
          % (n[0], g["fotogrammi_primi"], SCENA_PRIMI_S, g["byte_primi_kb"],
             g["byte_prima_chiave_kb"]))
    if g["fotogrammi_primi"] == 120 and abs(g["byte_primi_kb"] - 120 * 8000 / 1024.0) < 1e-6:
        _ok("come scritto")
    else:
        _ko("⛔ il costo dei primi fotogrammi non e' quello"); verde = False
    n[0] += 1
    print("  %2d · giornale vuoto ⇒ NIENTE DA LEGGERE, non zero byte" % n[0])
    if dal_giornale([]).get("esito", "").startswith("NIENTE DA LEGGERE"):
        _ok("come scritto")
    else:
        _ko("⛔ un giornale vuoto ha prodotto un costo"); verde = False

    # ── l'accensione: il primo A REGIME, non il primo ──────────────────────
    _log("⭐⭐ L'ACCENSIONE — «il primo abbandono §5.1 A REGIME», e il perche' "
         "l'ha insegnato il giro di prova")
    n[0] += 1
    # `[M]` 24 ago 2026, giro di prova a perdita ZERO: un abbandono al secondo
    #   1,095 e nessun altro.  ⇒ Col «primo in assoluto» l'accensione sarebbe a
    #   1,095 anche li', e `p_precede` non potrebbe mai dare verde.
    solo_scaldata = accensione([100.0 + 1.095], 100.0)
    vera = accensione([100.0 + 1.095, 100.0 + 6.4, 100.0 + 6.5], 100.0)
    print("  %2d · solo scaldata (1,095 s) ⇒ %s · scaldata + regime (6,4 s) ⇒ %s"
          % (n[0], solo_scaldata, vera))
    if solo_scaldata is None and abs(vera - 6.4) < 1e-9:
        _ok("⭐ l'abbandono della scaldata NON accende niente, e a regime vince "
            "il PRIMO — come il taglio che decide le famiglie")
    else:
        _ko("⛔ l'accensione conta anche la scaldata: p_precede sarebbe rosso "
            "per costruzione"); verde = False
    n[0] += 1
    print("  %2d · nessun abbandono ⇒ None (non si e' mai accesa), non zero" % n[0])
    if accensione([], 100.0) is None:
        _ok("come scritto")
    else:
        _ko("⛔ «mai accesa» e «accesa a zero» hanno la stessa faccia"); verde = False

    # ── il taglio delle famiglie ───────────────────────────────────────────
    _log("⛔ IL TAGLIO DELLE FAMIGLIE — e' quello di `09-b80.rotto_chiavi()`")
    n[0] += 1
    sp, li = famiglie([_c(0), _c(24), _c(1), _c(0),
                       {"esito": "NON HO NIENTE", "chiavi": None}])
    print("  %2d · 4 celle buone + 1 muta ⇒ spirale %d, liscio %d"
          % (n[0], len(sp), len(li)))
    if len(sp) == 2 and len(li) == 2:
        _ok("⭐ una chiave sola basta per la spirale, e la cella muta non entra "
            "in nessuna delle due famiglie")
    else:
        _ko("⛔ il taglio non e' quello di 09-b80"); verde = False

    print()
    if verde:
        _ok("⭐ %d casi: il banco sa dare VERDE, ROSSO e MUTO dove e' scritto"
            % n[0])
    else:
        _ko("⛔ IL BANCO NON HA DIRITTO AL VERDE: c'e' un caso che non fa quel "
            "che dice")
    return 0 if verde else 1


# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE PARLA CON LA MACCHINA DI PROVA
# ═══════════════════════════════════════════════════════════════════════════
def salva(nome, roba):
    os.makedirs(FUORI, exist_ok=True)
    p = os.path.join(FUORI, nome)
    with open(p, "w") as f:
        json.dump(roba, f, ensure_ascii=False, indent=1)
    return p


def leggi(nome):
    p = os.path.join(FUORI, nome)
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


def impronta_binario():
    try:
        rc, out, _ = RETE.rem("md5sum %s/src/remotix" % ALB, 60)
        return out.strip().split()[0] if out.strip() else None
    except Exception:
        return None


def stato_macchina():
    _log("COM'E' LA MACCHINA ADESSO — si dichiara, e non si ricorda")
    rc, out, _ = RETE.rem("cat /proc/loadavg; nproc; "
                          "systemctl list-units --no-legend 'remotix-*' "
                          "| awk '{print $1, $4}'; echo ---; "
                          "ss -lnu 2>/dev/null | grep -oE ':(7[89][0-9][0-9])' "
                          "| sort -u | tr '\\n' ' '", 60)
    for riga in out.splitlines():
        _inf(riga.strip())
    return out


def apparecchia():
    if not B76.spedisci_sonda():
        _ko("i copioni non si sono scritti in %s" % LAV)
        return False
    if B76.scegli_porta_sonda() is None:
        _ko("⛔ nessuna delle mie porte per la sonda e' libera: NON misuro, "
            "perche' senza sonda non so se il guasto sia stato messo")
        return False
    _ok("la sonda e il lettore sono in %s · la sonda usera' la porta %d"
        % (LAV, B76.PORTA_SONDA))
    return B70.terreno_controlla()


SCADENZA = [0.0]
AFFITTO = 900


def rinnova_se_serve():
    """⛔ Gli affitti si prendono CORTI e si rinnovano: ci sono altri agenti in
       coda, e un affitto lungo li ferma anche quando ho finito."""
    if time.time() > SCADENZA[0] - 400:
        if B76.rinnova(CHI, AFFITTO):
            SCADENZA[0] = time.time() + AFFITTO
            _inf("⛔ affitto del lucchetto rinnovato per %d s" % AFFITTO)
        else:
            raise SystemExit("⛔ il lucchetto non e' piu' mio: MI FERMO")


def passo_giri(a):
    """⛔ Venti giri IDENTICI sulla stessa casella, piu' il denominatore in
       apertura e in chiusura.  La regola si rimette a ogni giro
       (`RETE.stringi` fa `del root` + `add`): `[M]` 23 ago `tc qdisc change` e'
       APPICCICOSO, e un giro che ereditasse la regola del precedente
       misurerebbe una rete che nessuno ha chiesto."""
    nome0, reg0, ver0 = B80.casella(0.0)
    nome, reg, ver = B80.casella(PERDITA_CHIESTA)
    d = {"banco": CHI, "quando": time.strftime("%F %T"), "casella": nome,
         "secondi": a.secondi, "giri_chiesti": a.giri, "albero": ALB,
         "md5": impronta_binario(), "finestra_s": FINESTRA_S,
         "soglia_p": SOGLIA_P, "prove_dichiarate": PROVE_DICHIARATE,
         "minimo_famiglia": MINIMO_FAMIGLIA,
         "apertura": [], "celle": [], "chiusura": []}
    nomefile = "09-b83-biforcazione.json"

    for i in range(GIRI_DENOM):
        d["apertura"].append(giro(nome0, reg0, ver0, a.secondi,
                                  etichetta="%s · APERTURA %d/%d"
                                            % (nome0, i + 1, GIRI_DENOM)))
        salva(nomefile, d)
        rinnova_se_serve()
    for i in range(a.giri):
        d["celle"].append(giro(nome, reg, ver, a.secondi,
                               etichetta="%s · giro %d/%d" % (nome, i + 1, a.giri)))
        salva(nomefile, d)
        rinnova_se_serve()
        c = d["celle"][-1]
        _inf("⭐ FINORA: %s"
             % " ".join("%s/%s" % (x.get("chiavi"), x.get("fps"))
                        for x in d["celle"]))
    for i in range(GIRI_DENOM):
        d["chiusura"].append(giro(nome0, reg0, ver0, a.secondi,
                                  etichetta="%s · CHIUSURA %d/%d"
                                            % (nome0, i + 1, GIRI_DENOM)))
        salva(nomefile, d)
        rinnova_se_serve()
    _inf("scritto in %s" % salva(nomefile, d))
    return d


def con_lucchetto(quanti_giri, secondi, attesa, lavoro):
    """⛔⛔ IL LUCCHETTO — il `netem` su `lo` e' UNO SOLO per tutta la macchina.

    Chi non ce la fa si FERMA, non misura lo stesso: un altro banco che guasta
    la stessa `lo` non da' un rosso, da' **un numero plausibile e falso**
    (`LEZIONI.md` §1.26).
    """
    try:
        LUC.prendi(CHI, secondi=AFFITTO, attesa=attesa)
    except Exception as e:
        _ko("⛔ NON MISURO: %s" % e)
        return None
    SCADENZA[0] = time.time() + AFFITTO
    RETE.guardiano_arma(min(14400, quanti_giri * (secondi + 140) + 900))
    try:
        _inf("apro una sessione corta per far nascere il palco e il monitor")
        if not B70.innesca_sessione():
            _ko("la sessione non si apre: non misuro")
            return None
        return lavoro()
    finally:
        # ⛔ Il `finally`, e non e' una precauzione: se salto di qui con una
        #    `netem` addosso, la macchina resta guasta per tutti gli altri.
        B76.scena_spegni()
        _log("⛔ LA RETE SI RIMETTE COM'ERA")
        if not RETE.rimetti():
            _ko("⛔ la rete NON e' tornata com'era: si rimette a mano con "
                "«rimetti»")
        LUC.molla(CHI)


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", nargs="?",
                   choices=["terreno", "giri", "giudica", "rimetti", "stato"])
    p.add_argument("--certifica", action="store_true",
                   help="⭐ il controllo positivo: prova che il banco sa vedere "
                        "i difetti che cerca. Non tocca la macchina di prova")
    p.add_argument("--secondi", type=int, default=25)
    p.add_argument("--giri", type=int, default=GIRI,
                   help="quanti giri identici sulla casella (⛔ il conto sta in "
                        "testa al file: sotto i venti un ramo raro non si vede)")
    p.add_argument("--attesa", type=int, default=3600,
                   help="quanti secondi aspetto il lucchetto del netem")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if not a.passo:
        p.error("serve un passo, oppure --certifica")

    os.makedirs(FUORI, exist_ok=True)

    if a.passo == "giudica":
        importa(con_macchina=False)
        d = leggi("09-b83-biforcazione.json")
        if not d:
            _ko("⛔ non trovo %s/09-b83-biforcazione.json: prima si gira «giri»"
                % FUORI)
            return 2
        _log("09-b83 · LA BIFORCAZIONE — rileggo i giri del %s · md5 %s"
             % (d.get("quando"), d.get("md5")))
        rossi, muti, verdi = giudica(d)
        salva("09-b83-biforcazione.json", d)
        return verdetto(rossi, muti, verdi)

    importa()

    if a.passo in ("rimetti", "stato"):
        stato_macchina()
        _log("la rete della macchina di prova — dev «%s», porta %d" % (DEV, PORTA))
        return 0 if RETE.rimetti() else 2
    if a.passo == "terreno":
        ok = B76.spedisci_sonda()
        return 0 if (B70.terreno_controlla() and ok) else 2

    _log("09-b83 · LA BIFORCAZIONE — porta %d · dev «%s» · albero %s"
         % (PORTA, DEV, ALB))
    print("   ⛔ «%s» (ssh + la sessione dell'utente) NON si tocca" % VIETATA)
    print("   ⛔ le 7900, 7910, 7920 e l'utente «prova2» NON si toccano")
    print("   ⛔ le cure del prodotto restano SPENTE (I6): la bistabilita' va "
          "capita sul prodotto COM'E'")
    stato_macchina()
    _inf("impronta del binario: %s" % impronta_binario())
    if not apparecchia():
        return 2

    d = con_lucchetto(a.giri + 2 * GIRI_DENOM, a.secondi, a.attesa,
                      lambda: passo_giri(a))
    if d is None:
        return 2
    rossi, muti, verdi = giudica(d)
    salva("09-b83-biforcazione.json", d)
    return verdetto(rossi, muti, verdi)


def verdetto(rossi, muti, verdi):
    _log("IL VERDETTO — %d rossi · %d non giudicati" % (len(rossi), len(muti)))
    for r in rossi:
        _ko(r)
    for m in muti:
        _dub(m)
    for v in verdi:
        _ok(v)
    if rossi:
        return 1
    if muti:
        return 3
    _ok("⭐ tutti i predicati hanno fatto quel che era scritto prima")
    return 0


if __name__ == "__main__":
    sys.exit(principale())
