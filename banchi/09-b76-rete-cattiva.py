#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b76-rete-cattiva — IL PRODOTTO SU UNA LINEA CHE **PERDE, RIORDINA E
                      SFARFALLA**, che non e' una linea STRETTA.

    porta 7930 · sonda 7931 · utente `provanr1` (uid 1030)
    albero `/media/REMOTIX/src/09nr1-src` · lavoro `/media/REMOTIX/tmp/09nr1`
    unita' `remotix-7930` · ban-file e socket suoi

═══════════════════════════════════════════════════════════════════════════════
⛔ DA DOVE NASCE — il bersaglio della fase e' cambiato il 23 agosto 2026
═══════════════════════════════════════════════════════════════════════════════

Il regista: *«30 Mbit/s e' una connessione da meta' anni 90»*.  ⇒ La banda ha
smesso di essere la domanda.  ⭐ La domanda e' **la rete che perde pacchetti, li
consegna fuori sequenza o fa jitter**, che e' quel che fa un WiFi lontano, una
radio mobile o un router di casa sotto carico — e che una linea *stretta* non
riproduce affatto.

⛔ E le due cose non si somigliano.  Una linea stretta mette in coda; una linea
   cattiva mette in coda **e mente al mittente**: QUIC vede un buco nella
   successione dei pacchetti e non sa se e' una perdita o un sorpasso.  Se lo
   scambia per perdita, stringe la finestra di congestione **senza motivo** — e
   il prodotto rallenta per un guasto che non c'e' stato.
   ⚠ E oggi il prodotto **non ha mai scelto** un algoritmo di congestione
     (`src/webtransport.c` riga ~2730): prende quello che ngtcp2 gli da'.  ⇒ Un
     calo che si vedesse solo sui profili di disordine sarebbe **nostro**, non
     della rete.

═══════════════════════════════════════════════════════════════════════════════
⭐ CHE COSA SA VEDERE — le cinque grandezze di `09-b70-ritmo.py`, PIU' UNA
═══════════════════════════════════════════════════════════════════════════════

Le cinque si leggono con la **stessa** macchineria di `09-b70-ritmo.py`, che si
IMPORTA e non si ricopia (§«CHE COSA NON E' RISCRITTO» di quel file):

  1. fotogrammi consegnati/s **medi** e **minimo su finestra di un secondo**;
  2. chiavi contro delta (§3.3: si degrada **nel tempo**, non in chiavi);
  3. byte sul filo (dal contatore del `qdisc`) accanto ai byte del carico utile;
  4. la **deriva** del ritardo — ⚠ non l'anello: `RCP.md` §6.2 vieta di
     confrontare l'orologio del server con quello del client;
  5. abbandoni del server (video e audio) **e** buchi nella successione dei
     `numero` — la seconda gamba, che non passa dal registro del server.

⭐⭐ E LA SESTA, CHE E' DI QUESTO BANCO: **QUANTO HA DAVVERO PERSO, RIORDINATO
    E DUPLICATO IL `netem`**, misurato e non sperato.

    ⛔ Senza questo numero non si sa se il guasto che si credeva di mettere e'
       stato messo, ed e' la differenza fra una misura e una speranza.  Si legge
       da DUE gambe indipendenti:

      a) **il contatore del `qdisc`** — `tc -s qdisc show dev lo`.
         `[M]` 23 ago 2026: il campo `dropped` del blocco `netem 40:` conta
         **esattamente** i pacchetti che il `netem` ha buttato — 2 000 spediti
         con `loss 5%`, `dropped 101`, e la sonda ne ha visti mancare 101.
         Due strumenti, lo stesso numero.
         ⛔⛔ MA `tc` **NON HA NESSUN CONTATORE `reordered`**: `[M]` il blocco
             `netem` stampa solo `Sent / dropped / overlimits / requeues /
             backlog`, e con `reorder 25% 50%` acceso il solo campo che si e'
             mosso e' `requeues` (127), che **non e' il riordino**.  ⇒ Il
             riordino, il jitter e la duplicazione NON sono leggibili dal
             `qdisc`, e chiederlo a `tc` darebbe zero su un guasto che c'e'.

      b) ⭐ **LA SONDA** (piu' sotto): 8 000 pacchetti UDP numerati da 1 452
         byte spediti **attraverso lo stesso `netem`**, sulla mia porta 7931,
         subito prima del giro.  Dice, misurandoli: quanti persi, in quante
         **raffiche** e lunghe quanto, quanti duplicati, quanti **fuori
         ordine**, e il ritardo mediano e la sua dispersione.

    ⛔ E c'e' una TERZA verifica, che e' la piu' scema e ha gia' preso una
       trappola vera: **si rilegge la regola installata** e si controlla che non
       porti verbi che non ho chiesto.  `[M]` 23 ago: `tc qdisc change` e'
       APPICCICOSO — un `reorder 25% 50%` messo per un profilo e' rimasto acceso
       nei **quattro profili successivi**, che avrebbero misurato una rete che
       nessuno aveva chiesto.  ⇒ Ogni profilo si installa con `qdisc del root` +
       `add` (che e' quel che fa `stringi()` di `07-b65`), e poi si **rilegge**.

═══════════════════════════════════════════════════════════════════════════════
⭐ I PROFILI — e non c'e' nessuna banda, per scelta
═══════════════════════════════════════════════════════════════════════════════

⛔ **Nessun profilo porta `rate`.**  La banda e' la domanda di `09-b70-ritmo.py`
   ed e' gia' misurata li'.  Qui il tubo e' largo e il guasto e' un altro: se ci
   fosse anche una strozzatura, ogni numero sarebbe attribuibile a due cause
   insieme, che e' il modo piu' educato in cui una griglia mente
   (`LEZIONI.md` §1.26).

⛔ **E per la stessa ragione la coda si dichiara al contrario di b70.**  Li' il
   `limit` valeva 50 ms *alla banda del gradino*, perche' c'era una banda.  Qui
   non c'e': il `limit` dev'essere abbastanza GRANDE da non buttare mai niente
   di suo, o aggiungerebbe una perdita non dichiarata sopra quella dichiarata.
   ⇒ `limit 20000` pacchetti, e il profilo `liscio` **lo verifica**: se il
   `dropped` non e' zero a perdita zero, e' la mia coda che perde e **ogni altro
   numero di questa pagina e' contaminato**.

| profilo | `netem` | perche' | requisito |
|---|---|---|---|
| `liscio` | (solo `limit`) | ⛔ il denominatore. Il `netem` c'e' lo stesso perche' e' lui che porta il contatore dei byte: un denominatore cieco non si confronta con niente (e' la scelta di b70, e si tiene) | pieno |
| ⭐ `ritardo-30` | `delay 30ms` | ⭐⭐ **IL CONTROLLO CHE SEPARA IL RITARDO DAL DISORDINE**: arriva tardi ma **in ordine** (`[M]` 0 fuori-ordine su 2 000). Se qualcosa peggiora gia' qui, non e' il riordino — ed e' il termine di paragone di tutti i confronti | pieno |
| `perdita-0,5` … `perdita-3` | `delay 15ms loss X%` | ⛔ il ritardo c'e' sempre: senza un giro di rete la finestra di congestione non si riempie e il pacer non si accorge di niente (b70 riga ~322) | non stacca · niente spirale di chiavi · la resa |
| ⚠ `perdita-5` | `delay 15ms loss 5%` | oltre il 3 %: **diagnosi**, si guarda COME cede | solo «non stacca» |
| ⭐ `raffica-1` | `delay 15ms loss gemodel 0.2% 20% 100% 0%` | ⭐⭐ **LA GEMELLA ESATTA DI `perdita-1`**: la stessa perdita media, ma a **grappoli**. `[M]` 23 ago: 0,60 % in raffiche di **4,4 pacchetti** (max 13), contro raffiche di 1,00 della perdita indipendente. La perdita di una radio non e' indipendente, e questa e' l'unica coppia che lo isola | come `perdita-1` |
| ⚠ `raffica-forte` | `delay 15ms loss gemodel 3% 20% 100% 0%` | `[M]` **14,35 %** in raffiche di 5,5: il WiFi lontano davvero — **diagnosi** | solo «non stacca» |
| ⭐ `riordino-25` | `delay 10ms reorder 25% 50%` | il **riordino esplicito**, che non e' il jitter: un pacchetto su quattro salta la coda. `[M]` 33,5 % fuori ordine, e **perdita zero**. ⛔ `reorder` senza `delay` non fa niente | non stacca · spirale · ⭐ **non e' perdita** |
| `jitter-5/15/30` | `delay 20ms Xms distribution normal` | ⚠ `[M]` e qui c'e' un fatto da dichiarare: a 15 e 30 ms di sfarfallio la normale va **sotto zero**, `netem` taglia a 0, e il profilo diventa jitter **piu' riordino massiccio** (`[M]` `delay 20ms 15ms`: minimo 0,02 ms, p95 45 ms, **81 % fuori ordine**). Non e' un difetto del banco: e' quel che il jitter E' quando supera la distanza fra due pacchetti | come `riordino-25` |
| `duplicazione-1` | `delay 15ms duplicate 1%` | il caso che nessuno prova mai. QUIC deve ignorarli; se il nostro codice contasse un pacchetto due volte si vedrebbe qui | non stacca · spirale · non e' perdita |
| ⭐ `casa-cattiva` | `delay 40ms 20ms distribution normal loss 2%` | il misto: una casa col WiFi lontano. ⭐ E' l'unico profilo che si gira **in COPPIA** (scena mossa e scena ferma) per l'invariante I1 | tutto, piu' I1 |

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ I PREDICATI — SCRITTI PRIMA, e ne torna `(passa, perche)`
═══════════════════════════════════════════════════════════════════════════════

`07-b64-rete.py` porta il rilievo **R13**: nove «attesi» stampati e mai
confrontati.  Un banco cosi' non puo' dare rosso.  ⇒ Qui ogni atteso e' una
funzione, e `passa` vale `None` quando il banco **rifiuta di giudicare** — che
e' un terzo esito, non un verde educato (`CODER.md` §3.10).

  **G · IL GUASTO E' STATO MESSO** (⭐ e viene PRIMA di tutti).  Ogni profilo
  porta la sua verifica sui numeri della sonda, scritta accanto al profilo.  Se
  il guasto non si vede, il profilo **non si giudica**: misurare un profilo che
  non esiste e' peggio che non misurarlo.

  **S · NON STACCA** (§3.1-bis: *«non e' un rifiuto: il divieto di staccare
  resta intero»*).  ⛔ E' l'unico obbligo che vale su TUTTI i profili, anche
  quelli di diagnosi.  Si importa da b70 (`p_niente_stacco`).

  **K · NIENTE SPIRALE DI CHIAVI** — §3.3, importato da b70
  (`p_degrada_nel_tempo`): la quota di delta resta ≥ 0,90 su tutti i profili con
  perdita ≤ 3 %.  `[M]` 21 ago 2026, ed e' la faccia del difetto: sui giri
  stretti erano **144 chiavi su 144 fotogrammi**.  Ogni abbandono di §5.1 accende
  il debito di §5.2, il debito chiede una chiave, la chiave riempie la finestra,
  e si ricomincia.

  ⭐⭐ **R · IL JITTER E IL RIORDINO NON SONO PERDITA.**  E' la domanda per cui
  questo banco esiste.  Ai profili `riordino-25`, `jitter-*` e `duplicazione-1`
  la sonda misura **perdita zero**: ogni pacchetto arriva.  ⇒ I fotogrammi
  consegnati/s non devono calare in modo apprezzabile rispetto a `ritardo-30`,
  che ha lo stesso ordine di ritardo e nessun disordine.
  ⛔ Se calano, **non e' della rete**: e' nostro, o dell'algoritmo di congestione
     che non abbiamo mai scelto.
  ⚠ La soglia e' 0,90 — il 10 % e' *sufficiente, non giusto*: e' piu' del rumore
    fra due giri della stessa macchina (b70 lo stima al 5 %) e meno di qualunque
    calo che l'utente noterebbe.
  ⛔ E si rifiuta di giudicare se la sonda ha visto perdita sopra lo 0,2 % sul
     profilo, perche' allora il confronto non isolerebbe piu' il disordine.

  **P · LA PERDITA SI PAGA IN RITARDO, NON IN FOTOGRAMMI BUTTATI.**  Il video va
  su **stream** QUIC (`RCP.md` §6.2), e uno stream ritrasmette: un pacchetto
  perso non e' un fotogramma perso, e' un fotogramma **in ritardo**.
  ⇒ A `perdita-1` la resa in fotogrammi/s dev'essere ≥ 0,90 di `ritardo-30`, e a
    pagare dev'essere la **deriva**.
  ⚠ ⛔ E per questo il predicato della deriva di b70 (250 ms) qui **NON e' un
    requisito** sui profili con perdita: pretendere insieme «i fotogrammi non
    calano» e «il ritardo non cresce» vorrebbe dire vietare al prodotto l'unico
    modo che ha di pagare una perdita.  Gira lo stesso e si SCRIVE, marcato
    «diagnosi».

  **I1 · IL RITMO NON CALA PERCHE' LA SCENA E' FERMA** (`SPECIFICHE.md` §8.2) —
  importato da b70 (`p_I1`), con le sue due guardie che si rifiutano di
  giudicare quando la differenza e' a monte di noi.  ⭐ Si gira sulla
  `casa-cattiva`, che e' il profilo piu' vicino a una casa vera.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔⛔ CHE COSA QUESTO BANCO **NON** SA VEDERE
═══════════════════════════════════════════════════════════════════════════════

 1. ⛔ **L'IMMAGINE.**  Conta fotogrammi, chiavi, byte e ritardo.  Non sa dire
    «si vede peggio»: quel verdetto e' dell'utente sul desktop vero, e in v1 la
    fase omologa fu azzerata proprio perche' era stata validata con PSNR e SSIM.
 2. ⛔ **LA RETE VERA.**  `netem` gira su `lo`: nessuna radio, nessuna coda di
    router, nessun traffico di terzi, nessuna migrazione di percorso.  ⭐ Il
    guasto e' *un modello* della rete cattiva, e il modello e' scritto qui sopra
    riga per riga apposta: chi non e' d'accordo puo' discutere il modello invece
    di indovinare che cosa e' stato misurato.
 3. ⛔ **IL BROWSER.**  Il cliente e' `01-b3-cliente.py`: prende i byte dal filo
    e **non decodifica e non dipinge**.  I fotogrammi/s di qui sono un **tetto**.
 4. ⚠ **IL `distribution normal` NON SI PUO' RILEGGERE.**  `[M]` `tc qdisc show`
    non lo stampa: la regola riletta dice `delay 20ms 15ms` e basta.  ⇒ La forma
    della distribuzione e' l'unica cosa del guasto che questo banco dichiara e
    non verifica; quel che verifica e' la **dispersione misurata** dalla sonda.
 5. ⚠ **CHI ALTRO STA SULLA MACCHINA.**  Il lucchetto del `netem` garantisce che
    nessun altro banco stia guastando la rete; non garantisce che nessuno stia
    usando la CPU.  Il carico si stampa.

I CODICI D'USCITA
    0   CONFORME · 1 NON CONFORME (c'e' un rosso) · 2 uso/terreno/rete
    3   ⛔ NON HO NIENTE DA GIUDICARE — un giro o un predicato si e' rifiutato

Uso (dal portatile):
    python3 banchi/09-b76-rete-cattiva.py --certifica    ⭐ senza macchina
    python3 banchi/09-b76-rete-cattiva.py terreno
    python3 banchi/09-b76-rete-cattiva.py sonda [--secondi 25] [--solo riordino]
    python3 banchi/09-b76-rete-cattiva.py rimetti        ⛔ e si verifica
"""
import argparse, base64, importlib.util, json, os, re, statistics
import subprocess, sys, time

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ L'ISOLAMENTO, SCRITTO PRIMA DI QUALUNQUE IMPORT CHE LO LEGGA
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Le 7900, 7910, 7920 sono termini di paragone gia' misurati e NON si
#    toccano; la 7809 e' del banco del ritmo, la 7730 e' dell'utente.  Mie sono
#    la **7930** (il server) e la **7931** (la sonda, che non ascolta nessuno).
PORTA = os.environ.setdefault("PORTA", "7930")
PORTA = int(PORTA)
# ⛔⭐ LA PORTA DELLA SONDA NON PUO' ESSERE FISSA, e l'ho imparato perdendo un
#     giro: avevo scelto la 7931 dopo averla vista libera, e **mentre giravo**
#     un altro agente ci ha acceso il suo server (`09nr2`).  La sonda ha detto
#     «Address already in use» a ogni profilo, e il banco — giustamente — si e'
#     rifiutato di giudicare tutta la griglia.
#     ⇒ Si sceglie fra le mie candidate quella che in QUEL momento non ascolta
#       nessuno, e se non ce n'e' nessuna il banco si ferma invece di misurare
#       una rete che non ha verificato.
PORTE_SONDA = [int(x) for x in
               os.environ.get("PORTE_SONDA", "7939,7938,7937,7936,7935").split(",")]
PORTA_SONDA = PORTE_SONDA[0]
UTENTE = os.environ.setdefault("UTENTE", "provanr1")
UID_B = int(os.environ.setdefault("UID_B", "1030"))
MACCHINA = os.environ.setdefault("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.setdefault("PAROLA_SUDO", "nicfio")
IND = os.environ.setdefault("IND", "192.168.0.2")
LAV = os.environ.setdefault("LAV", "/media/REMOTIX/tmp/09nr1")
ALB = os.environ.setdefault("ALBERO", "/media/REMOTIX/src/09nr1-src")
DENTRO_ALB = os.environ.setdefault("DENTRO_ALB", "/srv/src/09nr1-src")
DENTRO_LAV = os.environ.setdefault("DENTRO_LAV", "/srv/remotix/tmp/09nr1")
QUI = os.path.dirname(os.path.abspath(__file__))
FUORI = os.environ.setdefault("FUORI", "/tmp/09-b76")
SHM = os.environ.get("SHM", "/09nr1")     # ⛔ non «/09-b70»: vedi scena_accendi()

VIETATA = "enp7s0"     # ⛔ ci passano l'ssh e la sessione dell'utente: MAI
DEV = "lo"

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


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA MACCHINERIA DEL RITMO SI IMPORTA DA `09-b70-ritmo.py`, E POI SI CONTROLLA
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Non si ricopia una riga: il lettore della traccia §11.1, la riduzione ai
#    cinque numeri, la finestra minima, i conti del server e i quattro predicati
#    del singolo giro sono **suoi**, sono certificati **li'**, e due copie della
#    stessa riduzione in due file sono due riduzioni che divergono (e' la ferita
#    del 16 agosto, `09-b70` riga ~430).
#
# ⛔⛔ E POI SI CONTROLLA CHE ABBIA PRESO IL MIO AMBIENTE.  `09-b70` lega le sue
#      costanti all'ambiente **all'import**: importarlo e dare per scontato che
#      abbia letto il mio vorrebbe dire scrivere la traccia nel lavoro di un
#      altro agente e guastare la porta di un altro banco — e la rete e' l'unica
#      cosa che, sbagliata, fa male a chi non c'entra.
B70 = None
RETE = None
LUC = None


def importa():
    global B70, RETE, LUC
    B70 = _carica("b70ritmo", os.path.join(QUI, "09-b70-ritmo.py"))
    guai = []
    for nome, mio, suo in (("porta", PORTA, B70.PORTA), ("utente", UTENTE, B70.UTENTE),
                           ("uid", UID_B, B70.UID_B), ("lavoro", LAV, B70.LAV),
                           ("albero", ALB, B70.ALB), ("dev", DEV, B70.DEV),
                           ("dentro_lav", DENTRO_LAV, B70.DENTRO_LAV)):
        if mio != suo:
            guai.append("%s: il modulo ha «%s», il mio e' «%s»" % (nome, suo, mio))
    if guai:
        raise SystemExit("⛔ NON MISURO: l'import di 09-b70 non ha preso il mio "
                         "ambiente — " + " · ".join(guai))
    # ⛔ E la disciplina della rete la prende b70 stesso, con la sua verifica
    #    (guardiano staccato, `prio` a quattro bande, due filtri `u32` sulla
    #    sola porta, `rimetti` che si controlla).  Qui si aggancia al modulo.
    RETE = B70._importa_rete()
    B70.RETE = RETE
    if RETE.PORTA != PORTA or RETE.DEV != DEV or RETE.VIETATA != VIETATA:
        raise SystemExit("⛔ NON TOCCO LA RETE: il modulo della rete ha porta %d, "
                         "dev «%s», vietata «%s»"
                         % (RETE.PORTA, RETE.DEV, RETE.VIETATA))
    LUC = _carica("lucchetto", os.path.join(QUI, "09-lucchetto.py"))
    # ⛔ Le due funzioni di b70 che il redirect ha reso mute si sostituiscono
    #    QUI, senza toccare il suo file (ci sta lavorando un altro agente).
    B70.righe_registro = righe_registro
    B70.spedisci_lettore = (lambda:
                            scrivi_sulla_macchina("09-b70-leggi.py", B70.LETTORE))
    return B70


def root(comando, tetto=300):
    return RETE.root(comando, tetto)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ LA SONDA — «il guasto che credevo di mettere e' stato messo?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Gira SULLA MACCHINA DI PROVA e attraversa **lo stesso `netem`** del giro:
#    e' la sola cosa che la rende una verifica e non un'altra misura.
#    ⇒ Due filtri `u32` in piu' sulla mia porta 7931, dentro la stessa banda
#      1:4, e via.
#
# ⛔ Spedisce e riceve su `127.0.0.1`, che su questa macchina passa da `lo`
#    esattamente come il traffico verso 192.168.0.2 (il cliente gira in un
#    contenitore sulla stessa macchina: e' il motivo per cui tutto il banco
#    funziona su `lo`).
#
# ⚠ Il pacchetto e' da **1 452 byte**, la misura del pacchetto QUIC: un guasto
#   che dipendesse dalla lunghezza si vedrebbe alla stessa grana del prodotto.
#
# ⭐ E la sonda **non giudica**: stampa gli arrivi grezzi, e a ridurli e' la
#    funzione `riduci_sonda()` sul portatile — che e' la STESSA che
#    `--certifica` esercita su arrivi fabbricati.  Una sonda che riducesse per
#    conto suo certificherebbe meta' dello strumento.
SONDA = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09-b76-sonda — pacchetti numerati attraverso il netem, e stampa gli ARRIVI.

⛔ Non riduce e non giudica: la riduzione sta nel banco, ed e' quella che il
   controllo positivo esercita.  Qui si spedisce, si riceve e si scrive.
"""
import json, socket, struct, sys, threading, time


def principale():
    porta = int(sys.argv[1])
    quanti = int(sys.argv[2])
    passo_ms = float(sys.argv[3])
    misura = int(sys.argv[4]) if len(sys.argv) > 4 else 1452
    ric = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ric.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16 * 1024 * 1024)
    ric.bind(("127.0.0.1", porta))
    ric.settimeout(0.3)
    arrivi = []
    fine = threading.Event()

    def ricevi():
        # ⛔ Il ricevente sta in un filo suo: spedire tutto e POI ricevere
        #    farebbe traboccare la coda del socket e chiamerei «persa» roba
        #    che la rete aveva consegnato.
        while True:
            try:
                d, _ = ric.recvfrom(4096)
            except socket.timeout:
                if fine.is_set():
                    return
                continue
            t = time.monotonic_ns()
            if len(d) >= 16:
                seq, part = struct.unpack("!Qq", d[:16])
                arrivi.append([seq, round((t - part) / 1e6, 3)])

    th = threading.Thread(target=ricevi, daemon=True)
    th.start()
    sp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    riempi = b"\x5a" * (misura - 16)
    t0 = time.monotonic()
    for i in range(quanti):
        sp.sendto(struct.pack("!Qq", i, time.monotonic_ns()) + riempi,
                  ("127.0.0.1", porta))
        d = t0 + (i + 1) * passo_ms / 1000.0 - time.monotonic()
        if d > 0:
            time.sleep(d)
    # ⚠ Si aspetta che la coda del netem si svuoti: con `delay 40ms 20ms` gli
    #   ultimi pacchetti arrivano dopo la fine della spedizione, e chiuderei
    #   dichiarandoli persi.
    time.sleep(2.0)
    fine.set()
    th.join(timeout=3)
    print(json.dumps({"quanti": quanti, "passo_ms": passo_ms,
                      "misura": misura, "arrivi": arrivi}))


if __name__ == "__main__":
    principale()
'''


def riduci_sonda(arrivi, quanti):
    """⭐ Dagli arrivi grezzi ai numeri del GUASTO.  ⛔ Ed e' la stessa funzione
       che `--certifica` esercita su arrivi fabbricati.

    · **persi**    = i numeri che non sono mai arrivati;
    · **raffiche** = quanti sono lunghe in media, ⭐ che e' l'unica cosa che
      distingue una perdita indipendente da quella di una radio.  `[M]` 23 ago:
      `loss 1%` da' raffiche di **1,00**; `loss gemodel` di **4,4**;
    · **duplicati** = arrivati piu' di una volta;
    · **fuori ordine** = arrivati DOPO uno con numero piu' alto.  ⛔ E' la sola
      misura del riordino che esista: `tc` non ha un contatore `reordered`;
    · **il ritardo** e la sua **dispersione** (p95 − minimo), che e' lo
      sfarfallio misurato invece che dichiarato.
    """
    n = {"quanti": quanti, "ricevuti": len(arrivi)}
    if not quanti:
        n["esito"] = "NON GIUDICO — la sonda non ha spedito niente"
        return n
    numeri = [a[0] for a in arrivi]
    unici = set(numeri)
    mancanti = [i for i in range(quanti) if i not in unici]
    raffiche = []
    for i in mancanti:
        if raffiche and i == raffiche[-1][-1] + 1:
            raffiche[-1].append(i)
        else:
            raffiche.append([i])
    massimo, fuori = -1, 0
    for q in numeri:
        if q < massimo:
            fuori += 1
        else:
            massimo = q
    n["persi"] = len(mancanti)
    n["persi_pc"] = round(100.0 * len(mancanti) / quanti, 3)
    n["raffiche"] = len(raffiche)
    n["raffica_media"] = (round(len(mancanti) / float(len(raffiche)), 2)
                          if raffiche else 0.0)
    n["raffica_max"] = max((len(x) for x in raffiche), default=0)
    n["duplicati"] = len(arrivi) - len(unici)
    n["duplicati_pc"] = round(100.0 * (len(arrivi) - len(unici)) / quanti, 3)
    n["fuori_ordine"] = fuori
    n["fuori_ordine_pc"] = round(100.0 * fuori / max(1, len(arrivi)), 2)
    if arrivi:
        r = sorted(a[1] for a in arrivi)
        n["ritardo_min_ms"] = r[0]
        n["ritardo_mediano_ms"] = round(statistics.median(r), 3)
        n["ritardo_p95_ms"] = r[int(0.95 * (len(r) - 1))]
        n["ritardo_max_ms"] = r[-1]
        n["dispersione_ms"] = round(n["ritardo_p95_ms"] - r[0], 3)
    n["esito"] = "misurato"
    return n


def _ha_sondato(s):
    return bool(s) and s.get("esito") == "misurato"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I PROFILI — e l'atteso di CIASCUNO e' una funzione, non una frase
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `limit 20000`: qui non c'e' banda, quindi la coda non deve MAI essere lei a
#    buttare.  Il profilo `liscio` lo verifica, e se non regge tutto il resto e'
#    contaminato.
CODA = int(os.environ.get("CODA", "20000"))
SONDA_PACCHETTI = int(os.environ.get("SONDA_PACCHETTI", "8000"))
SONDA_PASSO_MS = float(os.environ.get("SONDA_PASSO_MS", "0.4"))

# ── le soglie, in un posto solo, e ciascuna con la sua ragione ─────────────
RESA_MINIMA = 0.90      # ⚠ *sufficiente, non giusta*: piu' del rumore fra due
                        #   giri (b70 lo stima al 5 %), meno di qualunque calo
                        #   che l'utente noterebbe.
PERDITA_TRASCURABILE = 0.2   # % — sopra, un profilo «senza perdita» non isola
                             #     piu' il disordine e il confronto tace
CODA_MIA_MAX_PC = 0.10       # % — `dropped` a perdita nominale zero: sopra,
                             #     e' il mio `limit` che butta
GUASTO_MINIMO = 0.30    # il guasto misurato dev'essere almeno il 30 % del
                        # nominale, o non e' stato messo
GUASTO_MASSIMO = 3.0    # ⚠ e non piu' del triplo: un `loss 1%` che ne perde il
                        # 6 % non e' il profilo che ho dichiarato


def _v_liscio(s):
    """⛔⛔ IL PROFILO CHE VERIFICA IL BANCO, NON IL PRODOTTO.

    A perdita nominale zero la sonda deve vedere zero: se vede qualcosa, e' la
    **mia** coda (`limit %d`) che butta, e ogni numero di ogni altro profilo
    porta dentro una perdita che non ho dichiarato.
    """ % CODA
    if s["persi_pc"] > CODA_MIA_MAX_PC:
        return (False, "a perdita nominale ZERO la sonda ne ha persi %d su %d "
                       "(%.2f %%): e' la MIA coda che butta, e ogni altro "
                       "profilo e' contaminato"
                % (s["persi"], s["quanti"], s["persi_pc"]))
    if s["fuori_ordine_pc"] > 0.5:
        return (False, "a rete liscia il %.1f %% dei pacchetti e' arrivato "
                       "fuori ordine: il denominatore non e' liscio"
                % s["fuori_ordine_pc"])
    return (True, "zero perdita (%d su %d), zero disordine, ritardo mediano "
                  "%.2f ms: il denominatore e' pulito"
            % (s["persi"], s["quanti"], s.get("ritardo_mediano_ms", -1)))


def _v_ritardo(s):
    """⭐⭐ IL RIFERIMENTO: tardi ma IN ORDINE.  Se non fosse in ordine, tutti i
       confronti di questo banco non separerebbero piu' niente."""
    med = s.get("ritardo_mediano_ms", 0)
    if not (25.0 <= med <= 40.0):
        return (None, "il ritardo mediano misurato e' %.2f ms, e avevo chiesto "
                      "30: NON uso come riferimento un profilo che non e' "
                      "quello che credo" % med)
    if s["fuori_ordine_pc"] > 0.5:
        return (False, "il profilo del solo ritardo ha il %.1f %% di pacchetti "
                       "fuori ordine: non separa piu' il ritardo dal disordine"
                % s["fuori_ordine_pc"])
    if s["persi_pc"] > CODA_MIA_MAX_PC:
        return (False, "il riferimento ha perso il %.2f %%: non e' un "
                       "riferimento senza perdita" % s["persi_pc"])
    return (True, "ritardo mediano %.2f ms, ZERO fuori ordine, ZERO persi: "
                  "tardi ma in ordine, ed e' il riferimento" % med)


def _v_perdita(nominale, indipendente=True):
    def verifica(s):
        if s["persi_pc"] < GUASTO_MINIMO * nominale:
            return (None, "avevo chiesto il %.2f %% di perdita e la sonda ne ha "
                          "vista lo %.2f %%: il guasto NON e' stato messo, e non "
                          "giudico un profilo che non esiste"
                    % (nominale, s["persi_pc"]))
        if s["persi_pc"] > GUASTO_MASSIMO * nominale:
            return (None, "avevo chiesto il %.2f %% e la sonda ne ha visto lo "
                          "%.2f %%: non e' il profilo che ho dichiarato"
                    % (nominale, s["persi_pc"]))
        if indipendente and s["raffica_media"] > 1.6:
            return (None, "la perdita indipendente e' arrivata in raffiche di "
                          "%.2f pacchetti: non e' indipendente"
                    % s["raffica_media"])
        if not indipendente and s["raffica_media"] < 2.0:
            return (None, "⛔ la perdita a RAFFICA e' arrivata in raffiche di "
                          "%.2f pacchetti, cioe' come quella indipendente: il "
                          "profilo che rende questo giro diverso da «perdita-1» "
                          "NON e' stato messo" % s["raffica_media"])
        return (True, "persi %d su %d = %.2f %% (chiesto %.2f) in %d raffiche "
                      "lunghe in media %.2f (max %d)"
                % (s["persi"], s["quanti"], s["persi_pc"], nominale,
                   s["raffiche"], s["raffica_media"], s["raffica_max"]))
    return verifica


def _v_riordino(s):
    """⛔ `netem reorder` senza `delay` non fa NIENTE, e non lo dice.  ⇒ Il
       riordino si misura, o si e' misurato un profilo che non esiste."""
    if s["fuori_ordine_pc"] < 5.0:
        return (None, "il %.1f %% di pacchetti fuori ordine: il riordino NON e' "
                      "stato messo (⛔ `reorder` senza `delay` non fa niente), e "
                      "non giudico un profilo che non esiste"
                % s["fuori_ordine_pc"])
    if s["persi_pc"] > PERDITA_TRASCURABILE:
        return (None, "il profilo del riordino ha perso il %.2f %%: non isola "
                      "piu' il disordine dalla perdita" % s["persi_pc"])
    return (True, "%d pacchetti su %d fuori ordine (%.1f %%) e ZERO persi: e' "
                  "disordine puro" % (s["fuori_ordine"], s["ricevuti"],
                                      s["fuori_ordine_pc"]))


def _v_jitter(nominale_ms):
    def verifica(s):
        disp = s.get("dispersione_ms", 0)
        if disp < 0.5 * nominale_ms:
            return (None, "lo sfarfallio misurato (p95 − minimo) e' %.1f ms e "
                          "ne avevo chiesti %d: il guasto non e' stato messo"
                    % (disp, nominale_ms))
        if s["persi_pc"] > PERDITA_TRASCURABILE:
            return (None, "il profilo dello sfarfallio ha perso il %.2f %%: non "
                          "isola piu' il disordine" % s["persi_pc"])
        return (True, "ritardo mediano %.1f ms, dispersione p95−min %.1f ms "
                      "(chiesti %d), %.1f %% fuori ordine, ZERO persi"
                % (s.get("ritardo_mediano_ms", -1), disp, nominale_ms,
                   s["fuori_ordine_pc"]))
    return verifica


def _v_duplicazione(s):
    if s["duplicati_pc"] < GUASTO_MINIMO * 1.0:
        return (None, "duplicati %.2f %% su 1 %% chiesto: il guasto non e' "
                      "stato messo" % s["duplicati_pc"])
    if s["persi_pc"] > PERDITA_TRASCURABILE:
        return (None, "il profilo della duplicazione ha perso il %.2f %%"
                % s["persi_pc"])
    return (True, "%d pacchetti duplicati su %d (%.2f %%) e ZERO persi: QUIC li "
                  "deve ignorare" % (s["duplicati"], s["quanti"],
                                     s["duplicati_pc"]))


def _v_casa(s):
    if s["persi_pc"] < GUASTO_MINIMO * 2.0:
        return (None, "avevo chiesto il 2 %% di perdita e la sonda ne ha vista "
                      "lo %.2f %%: il guasto non e' stato messo" % s["persi_pc"])
    if s.get("dispersione_ms", 0) < 10.0:
        return (None, "lo sfarfallio misurato e' %.1f ms su 20 chiesti: il "
                      "guasto non e' stato messo" % s.get("dispersione_ms", 0))
    return (True, "persi %.2f %%, ritardo mediano %.1f ms, dispersione %.1f ms, "
                  "%.1f %% fuori ordine: e' una casa col WiFi lontano"
            % (s["persi_pc"], s.get("ritardo_mediano_ms", -1),
               s.get("dispersione_ms", -1), s["fuori_ordine_pc"]))


#  (nome, regole netem, requisito_pieno, spirale_e_resa, senza_perdita, perche, verifica)
#
#   requisito_pieno   il pavimento del ritmo e la deriva sono REQUISITO
#                     (solo il denominatore e il riferimento: sono le due linee
#                      che non hanno nessun guasto da pagare)
#   spirale_e_resa    §3.3 (quota delta) e la resa in fotogrammi sono REQUISITO
#                     ⛔ vale sui profili con perdita ≤ 3 %, come chiesto
#   senza_perdita     ⭐ il profilo NON perde: la resa si confronta con
#                     `ritardo-30` e un calo e' NOSTRO, non della rete
PROFILI = [
    ("liscio", [], True, True, True,
     "⛔ il denominatore. Il netem c'e' lo stesso perche' e' lui che porta il "
     "contatore dei byte, e verifica che la MIA coda non butti niente di suo",
     _v_liscio),
    ("ritardo-30", ["delay", "30ms"], True, True, True,
     "⭐⭐ IL CONTROLLO CHE SEPARA IL RITARDO DAL DISORDINE: tardi ma IN ORDINE. "
     "E' il riferimento di tutti i confronti",
     _v_ritardo),
    ("perdita-0,5", ["delay", "15ms", "loss", "0.5%"], False, True, False,
     "la prima perdita: mezzo pacchetto su cento", _v_perdita(0.5)),
    ("perdita-1", ["delay", "15ms", "loss", "1%"], False, True, False,
     "⭐ IL PROFILO SU CUI E' SCRITTO IL PREDICATO «la perdita si paga in "
     "ritardo, non in fotogrammi buttati»", _v_perdita(1.0)),
    ("perdita-3", ["delay", "15ms", "loss", "3%"], False, True, False,
     "il confine dichiarato: fin qui la spirale di chiavi e' un REQUISITO",
     _v_perdita(3.0)),
    ("perdita-5", ["delay", "15ms", "loss", "5%"], False, False, False,
     "⚠ oltre il confine — DIAGNOSI: si guarda COME cede, non se cede",
     _v_perdita(5.0)),
    ("raffica-1", ["delay", "15ms", "loss", "gemodel", "0.2%", "20%", "100%", "0%"],
     False, True, False,
     "⭐⭐ LA GEMELLA ESATTA DI «perdita-1»: stessa perdita media, ma a "
     "GRAPPOLI (`[M]` raffiche di 4,4 contro 1,0). E' l'unica coppia che isola "
     "la STRUTTURA della perdita dalla sua quantita'",
     _v_perdita(1.0, indipendente=False)),
    ("raffica-forte", ["delay", "15ms", "loss", "gemodel", "3%", "20%", "100%", "0%"],
     False, False, False,
     "⚠ `[M]` 14,35 % a raffiche di 5,5: il WiFi lontano davvero — DIAGNOSI",
     _v_perdita(14.0, indipendente=False)),
    ("riordino-25", ["delay", "10ms", "reorder", "25%", "50%"], False, True, True,
     "⭐⭐ IL RIORDINO ESPLICITO, che non e' il jitter: un pacchetto su quattro "
     "salta la coda, e NESSUNO si perde",
     _v_riordino),
    ("jitter-5", ["delay", "20ms", "5ms", "distribution", "normal"], False, True, True,
     "lo sfarfallio piccolo: 20 ± 5 ms", _v_jitter(5)),
    ("jitter-15", ["delay", "20ms", "15ms", "distribution", "normal"], False, True, True,
     "⚠ `[M]` a 15 ms la normale va sotto zero e netem taglia: diventa "
     "sfarfallio PIU' riordino massiccio (81 % fuori ordine). Non e' un difetto "
     "del banco: e' quel che il jitter E'", _v_jitter(15)),
    ("jitter-30", ["delay", "20ms", "30ms", "distribution", "normal"], False, True, True,
     "lo sfarfallio piu' largo del ritardo medio: il caso peggiore del disordine",
     _v_jitter(30)),
    ("duplicazione-1", ["delay", "15ms", "duplicate", "1%"], False, True, True,
     "⭐ il caso che nessuno prova mai. QUIC deve ignorarli; se il nostro codice "
     "contasse un pacchetto due volte si vedrebbe qui", _v_duplicazione),
    ("casa-cattiva", ["delay", "40ms", "20ms", "distribution", "normal",
                      "loss", "2%"], False, True, False,
     "⭐ IL MISTO: una casa col WiFi lontano. E' l'unico profilo che si gira in "
     "COPPIA (scena mossa e scena ferma) per l'invariante I1", _v_casa),
]

RIFERIMENTO = "ritardo-30"

# ⛔ I verbi del `netem` che cambiano la rete.  Se ne compare uno che NON ho
#    chiesto, la regola non e' mia: `[M]` 23 ago 2026, `tc qdisc change` e'
#    appiccicoso e si e' portato dietro un `reorder 25% 50%` per quattro
#    profili.
VERBI = ["loss", "reorder", "duplicate", "corrupt", "rate", "slot", "ecn"]


def _regole(profilo):
    return ["limit", str(CODA)] + list(profilo)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I CONTATORI DEL `qdisc` — la prima gamba, e si legge, non si deduce
# ═══════════════════════════════════════════════════════════════════════════
def conti_qdisc():
    """`[M]` 23 ago 2026: il `dropped` del blocco `netem 40:` conta ESATTAMENTE
       i pacchetti buttati dal netem (2 000 spediti con `loss 5%` → `dropped
       101`, e la sonda ne ha visti mancare 101).

    ⛔⛔ E non c'e' nessun `reordered`: il blocco stampa solo
        `Sent / dropped / overlimits / requeues / backlog`.  Chi cercasse li' il
        riordino leggerebbe zero su un guasto che c'e'.
    """
    rc, out, _ = root("/usr/sbin/tc -s qdisc show dev %s" % DEV)
    pezzi = out.split("qdisc netem 40:")
    if len(pezzi) < 2:
        return None
    m = re.search(r"Sent (\d+) bytes (\d+) pkt \(dropped (\d+), "
                  r"overlimits (\d+) requeues (\d+)\)", pezzi[1])
    if not m:
        return None
    return {"byte": int(m.group(1)), "pacchetti": int(m.group(2)),
            "buttati": int(m.group(3)), "oltre": int(m.group(4)),
            "rimessi": int(m.group(5))}


def regola_riletta():
    """⛔ La terza verifica, ed e' la piu' scema delle tre: si RILEGGE la regola.

    ⚠ `distribution normal` NON viene ristampato da `tc`: e' l'unica parte del
      guasto che si dichiara e non si rilegge (la sua prova e' la dispersione
      misurata dalla sonda).
    """
    rc, out, _ = root("/usr/sbin/tc qdisc show dev %s" % DEV)
    for riga in out.splitlines():
        if "netem 40:" in riga:
            return re.sub(r"\s*seed \d+", "", riga).strip()
    return ""


def controlla_regola(chieste, riletta):
    """(passa, perche) — il guasto installato e' quello e SOLO quello."""
    if not riletta:
        return _no("non ho riletto nessun `netem 40:` su «%s»: la regola non "
                   "c'e'" % DEV)
    guai = []
    for verbo in VERBI:
        chiesto = verbo in chieste
        c_e = re.search(r"\b%s\b" % verbo, riletta) is not None
        if c_e and not chiesto:
            guai.append("c'e' «%s» e NON l'ho chiesto" % verbo)
        if chiesto and not c_e:
            guai.append("ho chiesto «%s» e non c'e'" % verbo)
    if "delay" in chieste and "delay" not in riletta:
        guai.append("ho chiesto un ritardo e non c'e'")
    if guai:
        return _no("⛔ LA REGOLA INSTALLATA NON E' LA MIA — %s · riletta: «%s»"
                   % (" · ".join(guai), riletta))
    return _si("regola riletta: «%s»" % riletta)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ I PREDICATI CHE SONO DI QUESTO BANCO — scritti PRIMA
# ═══════════════════════════════════════════════════════════════════════════
def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)


def p_guasto_messo(profilo_nome, verifica, sonda):
    """⭐ VIENE PRIMA DI TUTTI: misurare un profilo che non esiste e' peggio che
       non misurarlo, perche' il numero e' vero e la causa e' inventata."""
    if not _ha_sondato(sonda):
        return _muto("la sonda non ha misurato: senza, non so se il guasto di "
                     "«%s» sia stato messo" % profilo_nome)
    return verifica(sonda)


def p_non_e_perdita(n, n_rif, sonda, nome):
    """⭐⭐ IL PREDICATO PER CUI QUESTO BANCO ESISTE.

    `SPECIFICHE.md` non lo scrive perche' nessuno ci aveva pensato: **il
    riordino e il jitter NON sono perdita**.  Su questi profili la sonda misura
    perdita ZERO — ogni pacchetto arriva, solo in un ordine diverso o a un'ora
    diversa.  ⇒ Il ritmo consegnato non deve calare rispetto a `ritardo-30`,
    che ha lo stesso ordine di ritardo e nessun disordine.

    ⛔ Se cala, la rete non ha perso niente e il calo e' **nostro**: o del
       rilevamento di perdita di QUIC che scambia un sorpasso per un buco, o
       dell'algoritmo di congestione che non abbiamo mai scelto
       (`src/webtransport.c` ~2730).
    """
    if not B70._ha_misurato(n):
        return _muto(n.get("esito", "non ho misurato questo profilo"))
    if not B70._ha_misurato(n_rif or {}):
        return _muto("il riferimento «%s» non ha misurato: senza di lui non c'e' "
                     "confronto, e un numero senza denominatore non giudica"
                     % RIFERIMENTO)
    if _ha_sondato(sonda) and sonda["persi_pc"] > PERDITA_TRASCURABILE:
        return _muto("su «%s» la sonda ha visto il %.2f %% di perdita vera: il "
                     "confronto non isolerebbe piu' il disordine"
                     % (nome, sonda["persi_pc"]))
    rapporto = n["fps"] / n_rif["fps"] if n_rif["fps"] else 0.0
    coda = ("%.2f/s contro %.2f/s del riferimento «%s» (%.0f %%), peggior "
            "secondo %s contro %s"
            % (n["fps"], n_rif["fps"], RIFERIMENTO, rapporto * 100,
               n["fps_finestra_min"], n_rif["fps_finestra_min"]))
    if rapporto < RESA_MINIMA:
        return _no("⛔ il ritmo cala su una rete che NON PERDE NIENTE: %s — il "
                   "disordine e' stato scambiato per perdita, e non e' della "
                   "rete" % coda)
    return _si("il disordine non e' stato scambiato per perdita: %s" % coda)


def p_perdita_in_ritardo(n, n_rif, sonda, nome):
    """**La perdita si paga in RITARDO, non in fotogrammi buttati.**

    Il video va su **stream** QUIC (`RCP.md` §6.2), e uno stream ritrasmette: un
    pacchetto perso non e' un fotogramma perso, e' un fotogramma **in ritardo**.
    ⇒ La resa in fotogrammi/s resta ≥ %.2f del riferimento, e a pagare e' la
      deriva — che qui si STAMPA e non si giudica, perche' pretendere insieme
      «i fotogrammi non calano» e «il ritardo non cresce» vorrebbe dire vietare
      al prodotto l'unico modo che ha di pagare una perdita.
    """ % RESA_MINIMA
    if not B70._ha_misurato(n):
        return _muto(n.get("esito", "non ho misurato questo profilo"))
    if not B70._ha_misurato(n_rif or {}):
        return _muto("il riferimento «%s» non ha misurato" % RIFERIMENTO)
    rapporto = n["fps"] / n_rif["fps"] if n_rif["fps"] else 0.0
    perso = ("%.2f %%" % sonda["persi_pc"]) if _ha_sondato(sonda) else "?"
    coda = ("%.2f/s contro %.2f/s (%.0f %%) con %s di perdita vera · la deriva "
            "e' finita a %s ms (massima %s)"
            % (n["fps"], n_rif["fps"], rapporto * 100, perso,
               n["deriva_fine_ms"], n["deriva_max_ms"]))
    if rapporto < RESA_MINIMA:
        return _no("⛔ la perdita si e' pagata in FOTOGRAMMI e non in ritardo: "
                   "%s — su stream QUIC che ritrasmettono non dovrebbe" % coda)
    return _si("la perdita si e' pagata in ritardo, non in fotogrammi: %s" % coda)


def p_coda_mia(profilo_nome, senza_perdita, delta):
    """⛔ Il `limit` di questo banco non deve MAI buttare niente di suo: qui non
       c'e' banda, quindi ogni pacchetto buttato a perdita nominale zero e' un
       guasto che ho aggiunto senza dichiararlo."""
    if not delta:
        return _muto("non ho letto i contatori del qdisc attorno al giro")
    if not delta["pacchetti"]:
        return _muto("zero pacchetti nel qdisc attorno al giro")
    pc = 100.0 * delta["buttati"] / float(delta["pacchetti"] + delta["buttati"])
    if senza_perdita and pc > CODA_MIA_MAX_PC:
        return _no("⛔ il qdisc ha buttato %d pacchetti su %d (%.2f %%) su un "
                   "profilo SENZA perdita: e' il mio `limit %d` che butta, e il "
                   "numero di questo giro e' contaminato"
                   % (delta["buttati"], delta["pacchetti"], pc, CODA))
    return _si("il qdisc ha spedito %d pacchetti (%.1f MB) e ne ha buttati %d "
               "(%.2f %%)" % (delta["pacchetti"], delta["byte"] / 1e6,
                              delta["buttati"], pc))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL CONTROLLO POSITIVO — «come fa questo banco a sapere di saper vedere?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `PIANO.md` §0.3.4: *«un banco che non sa vedere il difetto che cerca non ha
#    diritto al verde»*.  ⇒ Qui si fabbricano numeri e si controlla che i
#    predicati diano quel che e' scritto PRIMA — verde, rosso **e muto**.
#
# ⭐ E i casi non passano numeri gia' pronti: fabbricano ARRIVI e li fanno
#    passare da `riduci_sonda()`, che e' la stessa funzione che gira sui giri
#    veri.  Un inganno che vivesse nella riduzione verrebbe visto.
def _fab_arrivi(quanti, persi=(), duplicati=(), scambi=(), ritardo=15.0,
                sfarfallio=0.0):
    """Fabbrica gli arrivi della sonda.  `scambi` = coppie (i, j) da scambiare
       nell'ORDINE DI ARRIVO, che e' quel che fa un pacchetto che sorpassa."""
    persi = set(persi)
    ordine = [i for i in range(quanti) if i not in persi]
    for i, j in scambi:
        if i < len(ordine) and j < len(ordine):
            ordine[i], ordine[j] = ordine[j], ordine[i]
    arrivi = []
    for k, numero in enumerate(ordine):
        r = ritardo + (sfarfallio if k % 2 else -sfarfallio)
        arrivi.append([numero, round(r, 3)])
        if numero in duplicati:
            arrivi.append([numero, round(r + 0.05, 3)])
    return arrivi


def _fab_giro(fps, secondi=25, chiave_ogni=0, deriva=0.0, cons=1000, sped=1000,
              abb=0, vuote=3):
    """Un giro finto, ridotto dalla STESSA `misura()` che gira sui giri veri."""
    g = B70._fab([(fps, secondi + 3)], chiave_ogni=chiave_ogni,
                 deriva_ms_per_fotogramma=deriva)
    srv = {"consegnati": cons, "spediti": sped, "abbandonati": abb,
           "non_spediti": cons - sped, "annunci_tela": 0,
           "cattura": {"catturati": cons, "chiavi": 1, "attese_a_vuoto": vuote}}
    filo = {"byte": 90 * 1000 * 1000, "secondi": float(secondi),
            "byte_per_pacchetto": 1452.0}
    return B70.misura(g, secondi, srv, filo)


def certifica():
    print("⭐ CERTIFICAZIONE DEL BANCO DELLA RETE CATTIVA — l'atteso e' scritto "
          "PRIMA\n")
    print("   ⛔ Nessun contatto con la macchina di prova: qui si prova lo "
          "STRUMENTO,\n      non il prodotto.\n")
    importa_finto()
    verde = True

    def esito(nome, visto, atteso, perche):
        nonlocal verde
        bene = (visto is atteso)
        verde = verde and bene
        print("  %s%-62s atteso %-5s visto %-5s\n        %s"
              % ("OK  " if bene else "⛔  ", nome, atteso, visto, perche[:150]))

    # ── 1 · LA RIDUZIONE DELLA SONDA, che e' meta' dello strumento ─────────
    print("  ── la riduzione della sonda: dagli arrivi ai numeri del guasto ──\n")
    s = riduci_sonda(_fab_arrivi(1000), 1000)
    esito("1-⭐ sonda liscia: 1 000 su 1 000, in ordine",
          (s["persi"] == 0 and s["duplicati"] == 0 and s["fuori_ordine"] == 0),
          True, "persi %d · dup %d · fuori ordine %d" % (s["persi"],
                s["duplicati"], s["fuori_ordine"]))

    s = riduci_sonda(_fab_arrivi(1000, persi=[10, 11, 12, 500]), 1000)
    esito("2-⭐ perdita a RAFFICA: 3 di fila piu' 1 sola → raffiche 2, media 2,0",
          (s["persi"] == 4 and s["raffiche"] == 2 and s["raffica_media"] == 2.0
           and s["raffica_max"] == 3),
          True, "persi %d in %d raffiche, media %.2f, max %d"
          % (s["persi"], s["raffiche"], s["raffica_media"], s["raffica_max"]))

    s = riduci_sonda(_fab_arrivi(1000, duplicati=[3, 7, 9]), 1000)
    esito("3-⭐ duplicati: 3 pacchetti arrivati due volte, e ZERO persi",
          (s["duplicati"] == 3 and s["persi"] == 0), True,
          "duplicati %d · persi %d · ricevuti %d"
          % (s["duplicati"], s["persi"], s["ricevuti"]))

    # ⭐⭐ E QUI C'E' UNA COSA CHE NON E' OVVIA, e il primo atteso che avevo
    #    scritto era SBAGLIATO: **un solo sorpasso lungo fa arrivare tardi
    #    molti pacchetti**.  Lo scambio (10,11) ne fa arrivare tardi 1; lo
    #    scambio (20,25) ne fa arrivare tardi 5 — il numero 25 passa avanti e i
    #    quattro in mezzo piu' il 20 restano tutti dietro a un numero piu' alto.
    #    ⇒ 6, non 2.  ⚠ E' anche il motivo per cui `[M]` `delay 20ms 15ms` da'
    #      l'81 % di «fuori ordine» con un guasto che sposta pochi pacchetti: la
    #      grandezza conta gli SPOSTATI DA, non gli spostati.
    s = riduci_sonda(_fab_arrivi(1000, scambi=[(10, 11), (20, 25)]), 1000)
    esito("4-⭐ riordino: un sorpasso corto (1 tardivo) piu' uno lungo (5) = 6",
          (s["fuori_ordine"] == 6 and s["persi"] == 0), True,
          "fuori ordine %d (%.2f %%) · persi %d"
          % (s["fuori_ordine"], s["fuori_ordine_pc"], s["persi"]))

    # ── 2 · «IL GUASTO E' STATO MESSO?», e la risposta giusta e' spesso MUTO ─
    print("\n  ── il guasto e' stato messo? (⭐ e «non lo so» e' un esito) ──\n")
    p, q = p_guasto_messo("liscio", _v_liscio, riduci_sonda(_fab_arrivi(8000), 8000))
    esito("5-⭐ liscio pulito", p, True, q)

    p, q = p_guasto_messo("liscio", _v_liscio,
                          riduci_sonda(_fab_arrivi(8000, persi=range(0, 8000, 50)), 8000))
    esito("6-⛔⛔ liscio che perde il 2 %: e' la MIA coda, e contamina tutto",
          p, False, q)

    p, q = p_guasto_messo("perdita-1", _v_perdita(1.0),
                          riduci_sonda(_fab_arrivi(8000, persi=range(0, 8000, 100)), 8000))
    esito("7-⭐ perdita-1: la sonda ne vede l'1 %", p, True, q)

    p, q = p_guasto_messo("perdita-3", _v_perdita(3.0),
                          riduci_sonda(_fab_arrivi(8000), 8000))
    esito("8-⛔⛔ perdita-3 CHIESTA e MAI MESSA: il banco deve TACERE, non dare "
          "verde", p, None, q)

    # ⛔ Il caso che il 23 agosto e' successo davvero: `tc qdisc change` si e'
    #    portato dietro il `reorder` del profilo prima.
    p, q = p_guasto_messo("riordino-25", _v_riordino, riduci_sonda(_fab_arrivi(8000), 8000))
    esito("9-⛔⛔ riordino chiesto e non messo (⚠ `reorder` senza `delay` non fa "
          "niente): TACE", p, None, q)

    scambi = [(i, i + 1) for i in range(0, 6000, 4)]
    p, q = p_guasto_messo("riordino-25", _v_riordino,
                          riduci_sonda(_fab_arrivi(8000, scambi=scambi), 8000))
    esito("10-⭐ riordino messo davvero: un pacchetto su quattro sorpassa",
          p, True, q)

    p, q = p_guasto_messo("raffica-1", _v_perdita(1.0, indipendente=False),
                          riduci_sonda(_fab_arrivi(8000, persi=range(0, 8000, 100)), 8000))
    esito("11-⛔⛔ «raffica» che perde l'1 % ma UNO ALLA VOLTA: e' «perdita-1» "
          "travestita, e il banco TACE", p, None, q)

    a_raffica = [i for base in range(0, 8000, 500) for i in range(base, base + 5)]
    p, q = p_guasto_messo("raffica-1", _v_perdita(1.0, indipendente=False),
                          riduci_sonda(_fab_arrivi(8000, persi=a_raffica), 8000))
    esito("12-⭐ raffica vera: 1 % in grappoli da 5", p, True, q)

    p, q = p_guasto_messo("jitter-15", _v_jitter(15),
                          riduci_sonda(_fab_arrivi(8000, ritardo=20.0,
                                                   sfarfallio=0.2), 8000))
    esito("13-⛔ jitter chiesto 15 ms, misurati 0,4: TACE", p, None, q)

    p, q = p_guasto_messo("duplicazione-1", _v_duplicazione,
                          riduci_sonda(_fab_arrivi(8000), 8000))
    esito("14-⛔ duplicazione chiesta e nessun duplicato: TACE", p, None, q)

    # ── 3 · ⭐⭐ IL PREDICATO PER CUI IL BANCO ESISTE ──────────────────────
    print("\n  ── ⭐⭐ «il disordine non e' perdita»: il ritmo cala dove non "
          "si perde niente? ──\n")
    rif = _fab_giro(60)
    pulita = riduci_sonda(_fab_arrivi(8000, scambi=scambi), 8000)
    p, q = p_non_e_perdita(_fab_giro(59), rif, pulita, "riordino-25")
    esito("15-⭐ riordino, ritmo intatto (59 contro 60)", p, True, q)

    p, q = p_non_e_perdita(_fab_giro(40), rif, pulita, "riordino-25")
    esito("16-⛔⛔ IL DIFETTO CHE IL BANCO ESISTE PER TROVARE: 40/s contro 60/s "
          "su una rete che NON PERDE NIENTE", p, False, q)

    p, q = p_non_e_perdita(_fab_giro(40), rif,
                           riduci_sonda(_fab_arrivi(8000, persi=range(0, 8000, 100),
                                                    scambi=scambi), 8000),
                           "riordino-25")
    esito("17-⭐⭐ IL FALSO ROSSO: stesso calo, ma la sonda ha visto l'1 % di "
          "perdita vera — allora il confronto non isola niente e il banco TACE",
          p, None, q)

    p, q = p_non_e_perdita(_fab_giro(40), {"esito": "niente"}, pulita, "riordino-25")
    esito("18-⛔ senza riferimento non c'e' confronto: TACE", p, None, q)

    p, q = p_non_e_perdita(B70.misura([], 25, None, None), rif, pulita, "jitter-30")
    esito("19-⛔ il profilo non ha consegnato niente: TACE", p, None, q)

    # ── 4 · «la perdita si paga in ritardo» ────────────────────────────────
    print("\n  ── «la perdita si paga in ritardo, non in fotogrammi» ──\n")
    persa = riduci_sonda(_fab_arrivi(8000, persi=range(0, 8000, 100)), 8000)
    p, q = p_perdita_in_ritardo(_fab_giro(58, deriva=1.5), rif, persa, "perdita-1")
    esito("20-⭐ a perdita-1 il ritmo tiene e a pagare e' la deriva", p, True, q)

    p, q = p_perdita_in_ritardo(_fab_giro(30), rif, persa, "perdita-1")
    esito("21-⛔⛔ a perdita-1 il ritmo si dimezza: la perdita si e' pagata in "
          "FOTOGRAMMI, e su stream che ritrasmettono non dovrebbe", p, False, q)

    # ── 5 · la coda MIA, e i predicati importati da b70 ────────────────────
    print("\n  ── la mia coda, e i predicati importati da 09-b70 ──\n")
    p, q = p_coda_mia("liscio", True, {"pacchetti": 500000, "buttati": 0, "byte": 700e6})
    esito("22-⭐ la mia coda non butta niente", p, True, q)

    p, q = p_coda_mia("riordino-25", True,
                      {"pacchetti": 500000, "buttati": 5000, "byte": 700e6})
    esito("23-⛔⛔ la mia coda butta l'1 % su un profilo senza perdita: ogni "
          "numero e' contaminato", p, False, q)

    p, q = B70.p_degrada_nel_tempo(_fab_giro(30, chiave_ogni=1))
    esito("24-⛔ la SPIRALE DI CHIAVI (§3.3): 30/s ma tutte chiavi", p, False, q)

    # ⛔ «Muore a meta'» = ha consegnato 10 s dei 25 chiesti.  ⚠ E il giro si
    #    fabbrica a mano, non con `_fab_giro`, perche' quello consegna SEMPRE
    #    tutto il tempo chiesto: un aiuto che non sa fabbricare il difetto non
    #    puo' certificare il predicato che lo cerca.
    morto = B70.misura(B70._fab([(60, 10)]), 25,
                       {"consegnati": 600, "spediti": 600, "abbandonati": 0,
                        "non_spediti": 0, "annunci_tela": 0}, None)
    p, q = B70.p_niente_stacco(morto)
    esito("25-⛔ la sessione muore a 10 s sui 25 chiesti: ogni media e' buona",
          p, False, q)

    p, q = B70.p_I1(_fab_giro(18, cons=1000, sped=620, abb=40), _fab_giro(30))
    esito("26-⛔⛔ I1 rotta: a scena FERMA il ritmo cala e i consegnati sono "
          "uguali", p, False, q)

    p, q = B70.p_I1(_fab_giro(18, cons=550, sped=550), _fab_giro(30))
    esito("27-⭐⭐ il falso rosso di I1: a scena ferma il compositore ha "
          "consegnato la meta' — e' A MONTE di noi, e il banco TACE", p, None, q)

    # ── 6 · la rilettura della regola: la trappola vera del 23 agosto ──────
    print("\n  ── ⛔ la regola riletta: `tc qdisc change` e' APPICCICOSO ──\n")
    p, q = controlla_regola(["delay", "15ms", "loss", "1%"],
                            "qdisc netem 40: parent 1:4 limit 20000 delay 15ms loss 1%")
    esito("28-⭐ la regola riletta e' quella chiesta", p, True, q)

    p, q = controlla_regola(["delay", "15ms", "loss", "1%"],
                            "qdisc netem 40: parent 1:4 limit 20000 delay 15ms "
                            "loss 1% reorder 25% 50% gap 1")
    esito("29-⛔⛔ IL CASO VERO: un `reorder` avanzato dal profilo prima — e "
          "avrei misurato una rete che nessuno ha chiesto", p, False, q)

    p, q = controlla_regola(["delay", "10ms", "reorder", "25%", "50%"],
                            "qdisc netem 40: parent 1:4 limit 20000 delay 10ms")
    esito("30-⛔ ho chiesto il riordino e la regola non ce l'ha", p, False, q)

    p, q = controlla_regola(["delay", "30ms"], "")
    esito("31-⛔ nessun netem riletto: la regola non c'e'", p, False, q)

    print("\n== %s" % ("⭐ IL BANCO SA VEDERE I DIFETTI CHE CERCA — e sa TACERE "
                       "dove non puo' giudicare"
                       if verde else
                       "⛔⛔ IL BANCO NON SA VEDERE QUEL CHE CERCA: non si creda "
                       "a nessun suo verde"))
    return 0 if verde else 1


def importa_finto():
    """⛔ Il controllo positivo non tocca la macchina, ma ha bisogno della
       RIDUZIONE di b70 (`misura`, `_fab`, i quattro predicati).  ⇒ Si importa
       il modulo e basta, **senza** agganciargli la rete: `RETE` resta `None` e
       nessuna funzione che parli con la macchina e' raggiungibile da qui."""
    global B70
    if B70 is None:
        B70 = _carica("b70ritmo", os.path.join(QUI, "09-b70-ritmo.py"))


# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE PARLA CON LA MACCHINA DI PROVA
# ═══════════════════════════════════════════════════════════════════════════
def scrivi_sulla_macchina(nome, testo):
    """⛔ In base64: le virgolette di un heredoc dentro un `sudo -S` dentro un
       `ssh` sono tre livelli di quoting, e uno sbagliato non da' un errore —
       da' un file troncato.

    ⛔⛔ E TUTTA LA CATENA VA DENTRO UN `bash -c`, ed e' un RILIEVO trovato qui
        il 23 agosto 2026 — vale anche per `09-b70-ritmo.py`
        (`spedisci_lettore()`, riga ~1300), che ne soffre:

          printf … | sudo -S -p '' mkdir -p LAV && printf '…' | base64 -d > LAV/x

        `sudo` copre **il solo `mkdir`**.  La seconda meta' della catena gira
        come `nicfio`, e `LAV` appartiene a `root` con permessi 755 ⇒
        *«Permission denied»*, il file non si scrive, e il banco dice «il
        lettore non si e' scritto» senza sapere perche'.
        ⚠ E sull'albero di chi ha gia' quel file da un giro precedente il
          difetto e' **invisibile**: `wc -c` trova il file vecchio e da' verde.
        ⇒ Qui la catena intera sta dentro un `bash -c "…"`, cosi' `sudo` copre
          tutto.  ⭐ E si scrive **anche il lettore di b70**, con lo stesso
          rimedio, perche' senza quello la traccia §11.1 non si riduce.
    """
    b = base64.b64encode(testo.encode("utf-8")).decode("ascii")
    root("bash -c \"mkdir -p %s && printf '%%s' '%s' | base64 -d > %s/%s\""
         % (LAV, b, LAV, nome))
    rc, out, _ = root("bash -c \"wc -c < %s/%s\"" % (LAV, nome))
    return out.strip().isdigit() and int(out.strip()) > 800


# ⛔⛔ E IL SECONDO RILIEVO DELLO STESSO GIORNO, PEGGIORE DEL PRIMO PERCHE' E'
#     MUTO: **un `< file` in coda ruba lo stdin a `sudo -S`**, che allora non
#     riceve la parola e risponde *«3 incorrect password attempts»*.
#     ⚠ E' scritto nero su bianco in `07-b64-terreno.sh` riga ~240 — *«niente
#       `</dev/null` in coda: quel redirect vince su `sudo -S`»* — ed e' tornato
#       lo stesso in `09-b70-ritmo.py`, due volte:
#         · `spedisci_lettore()`  → `wc -c < …` : il file **c'era** (2 198 byte
#           misurati) e il banco diceva «non si e' scritto»;
#         · `righe_registro()`    → `wc -l < …` : torna **0** in silenzio, e
#           allora `conti_del_server()` legge il registro **dall'inizio** invece
#           che da questo giro.  ⛔ I «conto finale» si salvano (c'e' un
#           `tail -1`), ma le righe `ciclo:` no: `catturati` e **`attese a
#           vuoto`** diventano cumulativi da quando il server e' acceso — cioe'
#           la colonna su cui I1 decide se rifiutarsi di giudicare.
#     ⇒ Qui si rimette a posto **senza toccare il file di b70**: si sostituisce
#       la sua funzione con una che mette il redirect dentro un `bash -c`.
def righe_registro():
    rc, out, _ = root("bash -c \"wc -l < %s/registro.log 2>/dev/null || echo 0\""
                      % LAV)
    try:
        return int(out.strip())
    except Exception:
        return 0


def scegli_porta_sonda():
    """⛔ La porta si sceglie ADESSO, non ieri: su questa macchina ci sono altri
       agenti che accendono server mentre io giro."""
    global PORTA_SONDA
    for porta in PORTE_SONDA:
        rc, out, _ = root("bash -c \"ss -uln | grep -c ':%d ' || true\"" % porta)
        if out.strip() == "0":
            PORTA_SONDA = porta
            return porta
    return None


def spedisci_sonda():
    ok_s = scrivi_sulla_macchina("09-b76-sonda.py", SONDA)
    ok_l = scrivi_sulla_macchina("09-b70-leggi.py", B70.LETTORE)
    if not ok_l:
        _ko("il lettore della traccia §11.1 non si e' scritto in %s" % LAV)
    return ok_s and ok_l


def filtri_sonda():
    """⛔ Due filtri `u32` in piu', sulla **mia** porta 7931 e nella stessa banda
       1:4: e' l'unico modo perche' la sonda attraversi lo STESSO `netem` del
       giro.  ⚠ Se ne andasse per la banda predefinita misurerebbe una rete
       liscia e direbbe «il guasto non c'e'» su ogni profilo."""
    for verso in ("sport", "dport"):
        root("/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
             "match ip protocol 17 0xff match ip %s %d 0xffff flowid 1:4"
             % (DEV, verso, PORTA_SONDA))


def sonda_gira():
    rc, out, err = root("python3 %s/09-b76-sonda.py %d %d %s 1452"
                        % (LAV, PORTA_SONDA, SONDA_PACCHETTI, SONDA_PASSO_MS),
                        180)
    try:
        d = json.loads(out)
    except Exception as e:
        _dub("la sonda non ha risposto: %s — %s" % (e, (out + err)[-200:]))
        return None
    return riduci_sonda(d.get("arrivi") or [], d.get("quanti") or 0)


def scena_accendi(movimento):
    """⛔⛔ E' l'UNICA cosa di `09-b70` che non si puo' importare, e la ragione e'
       l'isolamento: `09-b70.scena_accendi()` scrive la memoria condivisa in
       `/09-b70`, e oggi sulla stessa macchina c'e' l'agente di b70 con
       l'utente `provan9`.  `shm_open(..., 0644)` di un file che appartiene a un
       altro utente da' EACCES e la scena **muore all'avvio** — un guasto che
       assomiglia in tutto a «il compositore non consegna».
       ⇒ Stessa riga, mia memoria condivisa: `%s`.

    ⭐ E «scena ferma» resta `--movimento marca`, non la scena spenta: cambia
       solo la marca, quindi la cadenza di cattura e' quella del giro mosso e a
       cambiare c'e' il COSTO, che e' l'unica cosa che I1 vuole isolare.
    """ % SHM
    scena_spegni()
    rc, out, _ = root("grep -ao 'monitor «[^»]*»' %s/registro.log | tail -1" % LAV)
    m = re.findall("monitor «([^»]*)»", out)
    usc = m[-1] if m and m[-1] else None
    if not usc:
        return None
    root("setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
         "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
         "XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 "
         "%s --uscita %s --movimento %s --shm %s --giro b76 "
         ">/dev/null 2>&1 & echo acceso"
         % (UID_B, UID_B, UTENTE, UTENTE, UID_B, B70.SCENA_BIN, usc, movimento, SHM))
    time.sleep(1.5)
    rc, out, _ = root("pgrep -u %d -f '04-b30-scena --uscita' | head -1" % UID_B)
    return usc if out.strip() else None


def scena_spegni():
    root("pkill -u %d -f 04-b30-scena; true" % UID_B)


def rinnova(chi, secondi):
    """⛔ Gli affitti si prendono CORTI e si rinnovano: ci sono altri agenti in
       coda, e un affitto lungo li ferma anche quando ho finito.
       ⚠ E si rinnova solo se il lucchetto e' ancora MIO: se mi hanno
         scassinato, rinnovare vorrebbe dire rubarlo a chi e' subentrato."""
    altro, _ = LUC.stato()
    if altro != chi:
        return False
    LUC._root("bash -c \"printf '%%s %%s\\n' %d '%s' > %s/chi\""
              % (int(time.time() + secondi), chi, LUC.POSTO))
    return True


def stampa_sonda(s):
    if not _ha_sondato(s):
        _dub("SONDA  %s" % (s or {}).get("esito", "non ha misurato"))
        return
    _inf("SONDA   persi %d/%d = %.2f %% in %d raffiche (media %.2f, max %d) · "
         "duplicati %d (%.2f %%) · fuori ordine %d (%.1f %%)"
         % (s["persi"], s["quanti"], s["persi_pc"], s["raffiche"],
            s["raffica_media"], s["raffica_max"], s["duplicati"],
            s["duplicati_pc"], s["fuori_ordine"], s["fuori_ordine_pc"]))
    _inf("        ritardo min %.2f · mediano %.2f · p95 %.2f · max %.2f ms "
         "(dispersione p95−min %.2f)"
         % (s["ritardo_min_ms"], s["ritardo_mediano_ms"], s["ritardo_p95_ms"],
            s["ritardo_max_ms"], s["dispersione_ms"]))


# ═══════════════════════════════════════════════════════════════════════════
def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", nargs="?", choices=["terreno", "sonda", "rimetti", "stato"])
    p.add_argument("--certifica", action="store_true",
                   help="⭐ il controllo positivo: prova che il banco sa vedere "
                        "i difetti che cerca. Non tocca la macchina di prova")
    p.add_argument("--secondi", type=int, default=25)
    p.add_argument("--solo", default="", help="un profilo solo, per nome")
    p.add_argument("--attesa", type=int, default=2400,
                   help="quanti secondi aspetto il lucchetto del netem")
    p.add_argument("--senza-coppia", action="store_true",
                   help="salta la coppia I1 su «casa-cattiva»")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if not a.passo:
        p.error("serve un passo, oppure --certifica")

    os.makedirs(FUORI, exist_ok=True)
    importa()

    if a.passo in ("rimetti", "stato"):
        _log("la rete della macchina di prova — dev «%s», porta %d" % (DEV, PORTA))
        return 0 if RETE.rimetti() else 2

    if a.passo == "terreno":
        # ⛔ PRIMA i due copioni, POI il controllo: `terreno_controlla()` di b70
        #    cerca il lettore e non sa scriverlo (vedi `scrivi_sulla_macchina`).
        ok = spedisci_sonda()
        return 0 if (B70.terreno_controlla() and ok) else 2

    _log("09-b76 · LA RETE CATTIVA — porta %d · dev «%s»" % (PORTA, DEV))
    print("   ⛔ «%s» (ssh + la sessione dell'utente) NON si tocca" % VIETATA)
    print("   ⛔ nessun profilo porta `rate`: qui il tubo e' largo e il guasto e'")
    print("      la PERDITA, il RIORDINO e lo SFARFALLIO — la banda e' di 09-b70")
    print("   --  «%s» prima: %s" % (DEV, RETE.qdisc() or "(nessuna)"))
    if not spedisci_sonda():
        _ko("i copioni non si sono scritti in %s" % LAV)
        return 2
    if scegli_porta_sonda() is None:
        _ko("⛔ nessuna delle mie porte per la sonda (%s) e' libera: NON misuro, "
            "perche' senza sonda non so se il guasto sia stato messo"
            % ",".join(str(x) for x in PORTE_SONDA))
        return 2
    _ok("la sonda e il lettore della traccia sono in %s · la sonda usera' la "
        "porta %d" % (LAV, PORTA_SONDA))
    if not B70.terreno_controlla():
        return 2

    scelti = [p for p in PROFILI if not a.solo or a.solo in p[0]]
    if not scelti:
        _ko("nessun profilo corrisponde a «%s»" % a.solo)
        return 2
    quanti = len(scelti) + (1 if (not a.senza_coppia and
                                  any(x[0] == "casa-cattiva" for x in scelti)) else 0)

    # ═══ ⛔ IL LUCCHETTO — il netem su `lo` e' UNO SOLO per tutta la macchina ═
    #
    # ⛔ Chi non ce la fa si FERMA, non misura lo stesso: un altro banco che
    #    guasta la stessa `lo` non da' un rosso, da' un numero plausibile e
    #    falso (`LEZIONI.md` §1.26).
    CHI = "09-b76-rete-cattiva"
    AFFITTO = 900
    try:
        LUC.prendi(CHI, secondi=AFFITTO, attesa=a.attesa)
    except Exception as e:
        _ko("⛔ NON MISURO: %s" % e)
        return 2
    scadenza = time.time() + AFFITTO

    esiti, rossi, muti = [], [], []
    riferimento = None
    RETE.guardiano_arma(min(3600, quanti * (a.secondi + 130) + 600))
    try:
        _inf("apro una sessione corta per far nascere il palco e il monitor")
        if not B70.innesca_sessione():
            _ko("la sessione non si apre: non misuro")
            return 2

        for nome, regole, pieno, spirale, senza_perdita, perche, verifica in scelti:
            if time.time() > scadenza - 400:
                if rinnova(CHI, AFFITTO):
                    scadenza = time.time() + AFFITTO
                    _inf("⛔ affitto del lucchetto rinnovato per %d s (la coda "
                         "deve scorrere: altri agenti aspettano)" % AFFITTO)
                else:
                    _ko("⛔ il lucchetto non e' piu' mio: MI FERMO")
                    break

            _log("%s · %s" % (nome, perche))
            ok, q = RETE.stringi(_regole(regole))
            if not ok:
                _ko(q)
                rossi.append("%s · tc ha rifiutato la regola" % nome)
                break
            filtri_sonda()
            riletta = regola_riletta()
            passa_r, perche_r = controlla_regola(regole, riletta)
            (_ok if passa_r else _ko)("la regola: %s" % perche_r)
            if not passa_r:
                rossi.append("%s · la regola installata non e' quella chiesta" % nome)
                continue

            # ⭐ PRIMA la sonda, POI il giro: cosi' i contatori del qdisc che
            #   leggo attorno al giro non portano dentro i pacchetti della sonda.
            s = sonda_gira()
            stampa_sonda(s)
            passa_g, perche_g = p_guasto_messo(nome, verifica, s)
            (_ok if passa_g else (_dub if passa_g is None else _ko))(
                "IL GUASTO E' STATO MESSO: %s" % perche_g)

            voci = {"profilo": nome, "regole": " ".join(_regole(regole)),
                    "regola_riletta": riletta, "requisito_pieno": pieno,
                    "spirale_e_resa": spirale, "senza_perdita": senza_perdita,
                    "perche": perche, "sonda": s,
                    "guasto": {"passa": passa_g, "perche": perche_g},
                    "predicati": []}
            if passa_g is False:
                rossi.append("%s · il guasto: %s" % (nome, perche_g[:90]))
            elif passa_g is None:
                muti.append("%s · il guasto non e' stato messo — %s"
                            % (nome, perche_g[:90]))

            coppia = {}
            versi = [("mossa", "barra")]
            if nome == "casa-cattiva" and not a.senza_coppia:
                versi.append(("ferma", "marca"))
            prima = conti_qdisc()
            for etichetta, movimento in versi:
                usc = scena_accendi(movimento)
                if not usc:
                    _ko("la scena «%s» non parte: NON giudico questo giro" % movimento)
                    coppia[etichetta] = {"esito": "NON HO NIENTE DA GIUDICARE — "
                                                  "la scena non e' partita"}
                    continue
                _inf("scena «%s» sul monitor %s" % (movimento, usc))
                n = B70.giro("%s-%s" % (nome, etichetta), movimento,
                             B70.TELA_PIENA, a.secondi)
                print("   [%s]" % etichetta)
                B70.stampa_giro(n)
                coppia[etichetta] = n
                scena_spegni()
            dopo = conti_qdisc()
            delta = None
            if prima and dopo:
                delta = {k: dopo[k] - prima[k] for k in prima}
            voci["qdisc"] = delta
            _inf("QDISC   attorno al giro: %s" % json.dumps(delta))

            n = coppia.get("mossa") or {}
            if nome == RIFERIMENTO and B70._ha_misurato(n) and passa_g:
                riferimento = n
                _ok("⭐ «%s» diventa il RIFERIMENTO di tutti i confronti "
                    "(%.2f fotogrammi/s)" % (nome, n["fps"]))

            # ── i predicati, e ciascuno dice se CONTA a questo profilo ──────
            elenco = []
            passa, perche2 = B70.p_niente_stacco(n)
            elenco.append(("non stacca (§3.1-bis: vale ovunque)", passa, perche2, True))
            passa, perche2 = B70.p_degrada_nel_tempo(n)
            elenco.append(("niente spirale di chiavi (§3.3)", passa, perche2, spirale))
            passa, perche2 = B70.p_pavimento_ritmo(n)
            elenco.append(("il pavimento del ritmo (§2.1: 25/s)", passa, perche2, pieno))
            passa, perche2 = B70.p_ritardo_non_scappa(n)
            elenco.append(("la deriva non scappa", passa, perche2, pieno))
            passa, perche2 = p_coda_mia(nome, senza_perdita, delta)
            elenco.append(("⛔ la MIA coda non butta niente di suo", passa,
                           perche2, senza_perdita))
            if senza_perdita and nome not in ("liscio", RIFERIMENTO):
                passa, perche2 = p_non_e_perdita(n, riferimento, s, nome)
                elenco.append(("⭐⭐ il disordine NON e' perdita", passa, perche2, True))
            if not senza_perdita:
                passa, perche2 = p_perdita_in_ritardo(n, riferimento, s, nome)
                elenco.append(("la perdita si paga in RITARDO, non in fotogrammi",
                               passa, perche2, spirale))

            for etichetta, passa, perche2, conta in elenco:
                voci["predicati"].append({"predicato": etichetta, "passa": passa,
                                          "perche": perche2, "conta": conta})
                if not conta:
                    _inf("⚠ diagnosi · %s → %s (%s)"
                         % (etichetta, passa, perche2[:90]))
                    continue
                (_ok if passa else (_dub if passa is None else _ko))(
                    "%s: %s" % (etichetta, perche2))
                if passa is False:
                    rossi.append("%s · %s" % (nome, etichetta))
                elif passa is None:
                    muti.append("%s · %s — %s" % (nome, etichetta, perche2[:90]))

            if "ferma" in coppia:
                passa_i1, perche_i1 = B70.p_I1(coppia.get("ferma", {}),
                                               coppia.get("mossa", {}))
                (_ok if passa_i1 else (_dub if passa_i1 is None else _ko))(
                    "I1 — il ritmo non cala a scena ferma: %s" % perche_i1)
                voci["I1"] = {"passa": passa_i1, "perche": perche_i1}
                if passa_i1 is False:
                    rossi.append("%s · I1" % nome)
                elif passa_i1 is None:
                    muti.append("%s · I1 — %s" % (nome, perche_i1[:90]))
            voci["giri"] = coppia
            esiti.append(voci)
    finally:
        scena_spegni()
        _log("⛔ LA RETE SI RIMETTE COM'ERA")
        rimessa = RETE.rimetti()
        LUC.molla(CHI)

    with open(os.path.join(FUORI, "09-b76-esiti.json"), "w") as f:
        json.dump(esiti, f, ensure_ascii=False, indent=1)
    _inf("esiti in %s/09-b76-esiti.json" % FUORI)

    _log("IL VERDETTO — %d profili girati · %d rossi · %d non giudicati"
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
        return 3
    _ok("⭐ tutti i predicati hanno fatto quel che era scritto prima")
    return 0


if __name__ == "__main__":
    sys.exit(principale())
