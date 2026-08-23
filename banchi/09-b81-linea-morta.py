#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b81 — LE DUE CURE CHE NON HANNO MAI GIRATO: la LINEA MORTA e lo SFRATTO DEL
         FANTASMA.

⛔⛔ PERCHE' QUESTO BANCO ESISTE, e la ragione non e' «provare che funzionano».
    Delle due cure, una BUTTA FUORI UNA SESSIONE.  ⇒ La domanda che comanda
    tutto il resto non e' *«scatta quando deve?»* ma **«scatta quando NON
    deve?»** — perche' i due errori non costano uguale, e chi ha scritto la
    cura lo dichiara nel suo stesso riquadro: sbagliare in alto vuol dire
    qualche secondo d'immagine ferma in piu', sbagliare in basso vuol dire
    **buttare fuori uno che stava lavorando**, e quello non si rimedia.

⇒ LA PROVA 1 E' QUELLA CHE PUO' FAR RITIRARE LA CURA, e le altre cinque
  esistono per contorno.  Se `casa-cattiva` — `[M]` 1,71 % di perdita, 7,8-10,2
  fotogrammi/s, sessione viva — fa scattare la linea morta anche una sola volta
  in dieci minuti, la cura non si accende e il rapporto lo dice per primo.

═══ IL FALSIFICATORE DELLA PROVA 1, DICHIARATO DA CHI HA SCRITTO LA CURA ═══

⚠ `[?]` La soglia e' sulla frazione **DICHIARATA DA NGTCP2** (`pkt_lost /
  pkt_sent`), mentre l'1,71 % che regge e' la perdita **INIETTATA** dal
  `netem`.  E le due possono non coincidere: con jitter e riordino la
  dichiarata puo' essere PIU' ALTA, perche' un pacchetto che sorpassa viene
  scambiato per un pacchetto perso — ed e' il fatto centrale di questa fase
  (`09-b76`, «il disordine NON e' perdita»).

⇒ QUI SI MISURANO TUTT'E DUE, e si riportano accanto:
    · l'INIETTATA — la sonda di `09-b76`, che attraversa lo stesso `netem`;
    · la DICHIARATA — ricostruita dalle righe `rete-quic`, che portano
      `persi_d`, `spediti_d` e `da_ms`, cioe' esattamente i tre numeri con cui
      `linea_morta_giudica()` decide.  ⇒ Si applicano le SUE guardie
      (`spediti_d >= 200`, `da_ms >= 1000`) e si conta se due finestre di fila
      avrebbero mai sfondato i 50‰.
  ⛔ Se la DICHIARATA sfonda la soglia su una linea che REGGE, la soglia e'
     sbagliata **e va detto**, non aggirato: e' il predicato `p1b`.
  ⚠ `[?]` La ricostruzione e' un'APPROSSIMAZIONE dichiarata, e nel verso
    prudente sbagliato: le righe `rete-quic` tacciono quando non cambia niente,
    quindi una loro finestra puo' essere piu' LUNGA di un secondo — e una
    finestra piu' lunga media di piu', cioe' **abbassa** il picco.  ⇒ Da sola
    non basta, e accanto ci va la taratura (piu' sotto).

⭐ LA TARATURA, che chiude il buco della ricostruzione: un giro corto sullo
   STESSO `casa-cattiva` con `--linea-morta-permille 1`.  A quella soglia la
   cura scatta di sicuro, e scattando **stampa il `permille=` che ha calcolato
   lei**, sulla sua finestra, con la sua aritmetica.  ⇒ E' l'unico modo di
   leggere la frazione dichiarata senza rifarla a mano, e serve a controllare
   la ricostruzione contro il numero vero del prodotto.

═══ `[M]` 23 AGOSTO 2026 — QUEL CHE E' USCITO, E IL FATTO CHE CHIUDE LA 1 ═══

⛔⛔⛔ **LA FRAZIONE DICHIARATA ORDINA I DUE CASI AL CONTRARIO**, e questo non e'
      una taratura da rifare: e' la grandezza che non separa quel che deve
      separare.  `[M]` stessa macchina, stesso binario
      (`md5 d8c2c4461df7319fb40f33d1f96df4de`, albero di lavoro = HEAD 2de961d):

        profilo         INIETTATA (sonda)   DICHIARATA (ngtcp2)   la linea…
        casa-cattiva      1,86 - 2,15 %       **512‰** (51,2 %)   REGGE: 9,60
                                                                  fotogrammi/s,
                                                                  copertura 1,00,
                                                                  buco max 0,50 s,
                                                                  DIECI MINUTI interi
        raffica-forte    12,28 - 14,00 %      **123‰** (12,3 %)   NON regge:
                                                                  copertura 0,20,
                                                                  buco 30,06 s

      ⇒ La linea che FUNZIONA dichiara **quattro volte piu' perdita** di quella
        che non funziona.  ⛔ Nessun valore di `--linea-morta-permille` puo'
        separarle: qualunque soglia che lasci passare `casa-cattiva` (≥ 512‰)
        lascia passare anche `raffica-forte`, e qualunque soglia che fermi
        `raffica-forte` (≤ 123‰) ferma prima `casa-cattiva`.

⭐ LA CAUSA, misurata e non ipotizzata: `casa-cattiva` porta `delay 40ms 20ms
   distribution normal`, e la sonda ci misura il **93,5 %** di pacchetti fuori
   ordine (dispersione p95−min 73 ms) con l'1,9 % di perdita vera.  Il
   rilevamento di perdita di ngtcp2 conta un pacchetto SORPASSATO come perso.
   ⇒ `pkt_lost/pkt_sent` su una linea che riordina non misura la perdita:
     misura il RIORDINO — che e' il fatto centrale di questa fase
     (`09-b76`, «il disordine NON e' perdita»).

⚠ E NON E' LA PARTENZA DELLA CONNESSIONE, che era l'altra spiegazione possibile:
  tolte le prime dieci finestre, **399 finestre su 399** restano sopra la soglia,
  con **398 coppie di fila** — cioe' la condizione di scatto, ininterrotta per
  dieci minuti.  Mediana dopo la partenza **524‰**.

⛔ IL GIRO ACCESO: la cura ha chiuso la sessione dopo **~4 s** (`persi=217
   spediti=428 permille=507 finestre=2/2`), e il giro di CONTROLLO — stessa
   linea, stessi dieci minuti, cure spente — ha retto tutto: fra i due cambia
   **un interruttore**.

⭐ E LE ALTRE CINQUE SONO VERDI, la cura del fantasma compresa:
    2 · `raffica-forte`: scatta a **5,05 s**, `causa=perdita`, 137‰ contro 50‰,
        e il filo cade (riga di `trasporto.c`).
    3 · silenzio: scatta a **`silenzio_ms=10002`** (soglia 10 000), `prove=10`,
        10,36 s dopo il `kill -9`; e dopo lo scatto il posto e' libero **al
        primo tentativo**.  ⚠ Il prezzo dei PING NON si e' potuto isolare: una
        sessione «ferma» costa **2 463 kbit/s** di audio PCM (§4.3, che non si
        spegne: `[M]` un CIAO senza codec audio comune si becca `0x09`), cioe'
        **11 727 volte** il costo dichiarato — e il contatore non si ferma mai
        per 0,6 s, cioe' il keep-alive non ha MAI occasione di scattare su una
        sessione viva.
    4 · sfratto: **16,83 s e 7 rifiuti** contro **32,13 s e 14 rifiuti** senza —
        il fantasma scende del **48 %**.
    5 · due utenti: zero sfratti, `provanr6b` entra sul proprio posto con zero
        rifiuti, e la riga `SFRATTO NEGATO` non esce (previsto `[R]`).
    6 · I6: coi predefiniti zero scatti, zero sfratti, e i due profili stanno
        nella griglia di `09-b76`.

═══ CHE COSA SI MISURA, E CON CHE COSA ═══

⛔ Non si riscrive una riga di quel che c'e' gia'.  Questo banco e' quasi tutto
   fatto di pezzi altrui, e li DICHIARA:

     `09-b76-rete-cattiva.py`  i profili (`casa-cattiva`, `raffica-forte`), la
                               SONDA della perdita iniettata, la disciplina del
                               `netem`, i contatori del qdisc, i testimoni
                               della connessione, la riduzione della consegna,
                               e per suo tramite tutto `09-b70-ritmo.py`
                               (`giro()`, la traccia §11.1, i cinque numeri).
     `09-b78-apertura.py`      l'apertura di sessione cronometrata fase per
                               fase, e ⭐ `--riprova-0f`, che **cronometra il
                               posto negato invece di contarlo** — cioe' e' gia'
                               lo strumento della prova 4.
     `07-b64-rete.py`          ⛔ `registro_posato()`, portato qui dentro: vedi
                               il riquadro sopra la funzione.
     `09-lucchetto.py`         il `netem` su `lo` e' uno solo per tutta la
                               macchina.

⛔ L'ISOLAMENTO: porta **7960**, utente **`provanr6`** (uid 1060) e — solo per
   la prova 5 — **`provanr6b`** (uid 1061), albero
   `/media/REMOTIX/src/09nr6-src`, lavoro `/media/REMOTIX/tmp/09nr6`, unita'
   `remotix-7960`.  ⛔ Le porte 7900, 7910 e 7920 non si toccano; `enp7s0` non
   si tocca MAI; il `netem` sta su `lo` e i filtri `u32` sulla sola 7960.

⛔⛔ E IL BINARIO E' COSTRUITO DALL'ALBERO DI LAVORO, non da `git archive`: le
    due cure non stanno in nessun binario esistente, e un binario che non le ha
    farebbe passare per MISURATA una cura mai girata.  L'impronta si dichiara
    (`09-b81-terreno.sh porta`, passo 3).

I CODICI D'USCITA
    0   CONFORME · 1 NON CONFORME (c'e' un rosso) · 2 uso/terreno/rete
    3   ⛔ NON HO NIENTE DA GIUDICARE — un giro o un predicato si e' rifiutato

Uso (dal portatile):
    python3 banchi/09-b81-linea-morta.py --certifica     ⭐ senza macchina
    python3 banchi/09-b81-linea-morta.py terreno
    python3 banchi/09-b81-linea-morta.py p1     # ⛔⛔ il falso positivo
    python3 banchi/09-b81-linea-morta.py p2     # lo scatto vero
    python3 banchi/09-b81-linea-morta.py p3     # il silenzio, e i PING
    python3 banchi/09-b81-linea-morta.py p4     # lo sfratto
    python3 banchi/09-b81-linea-morta.py p5     # ⛔ due utenti diversi
    python3 banchi/09-b81-linea-morta.py p6     # ⛔ i predefiniti non cambiano
    python3 banchi/09-b81-linea-morta.py tutte
    python3 banchi/09-b81-linea-morta.py rimetti          ⛔ e si verifica
"""
import argparse, importlib.util, json, os, re, subprocess, sys, time

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ L'ISOLAMENTO, SCRITTO PRIMA DI QUALUNQUE IMPORT CHE LO LEGGA
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `setdefault` e non `=`: i moduli che importo leggono l'ambiente all'import,
#    e devono leggere IL MIO.  ⚠ E dopo l'import si CONTROLLA che l'abbiano
#    letto (`importa()`), perche' un modulo che ha preso l'ambiente di un altro
#    agente guasterebbe la porta di un altro banco — e la rete e' l'unica cosa
#    che, sbagliata, fa male a chi non c'entra.
PORTA = int(os.environ.setdefault("PORTA", "7960"))
UTENTE = os.environ.setdefault("UTENTE", "provanr6")
UID_B = int(os.environ.setdefault("UID_B", "1060"))
UTENTE2 = os.environ.setdefault("UTENTE2", "provanr6b")
UID_B2 = int(os.environ.setdefault("UID_B2", "1061"))
MACCHINA = os.environ.setdefault("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.setdefault("PAROLA_SUDO", "nicfio")
IND = os.environ.setdefault("IND", "192.168.0.2")
LAV = os.environ.setdefault("LAV", "/media/REMOTIX/tmp/09nr6")
ALB = os.environ.setdefault("ALBERO", "/media/REMOTIX/src/09nr6-src")
DENTRO_ALB = os.environ.setdefault("DENTRO_ALB", "/srv/src/09nr6-src")
DENTRO_LAV = os.environ.setdefault("DENTRO_LAV", "/srv/remotix/tmp/09nr6")
# ⛔ Le porte della sonda sono MIE e si scelgono al volo (vedi `09-b76`): un
#    altro agente puo' accendere un server mentre giro.
os.environ.setdefault("PORTE_SONDA", "7969,7968,7967,7966,7965")
os.environ.setdefault("SHM", "/09nr6")
QUI = os.path.dirname(os.path.abspath(__file__))
FUORI = os.environ.setdefault(
    "FUORI", "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX-V2/"
             "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad/09-b81")
UNITA = os.environ.get("UNITA", "remotix-%d" % PORTA)

VIETATA = "enp7s0"     # ⛔ ci passano l'ssh e la sessione dell'utente: MAI
DEV = "lo"
# ⛔ Le porte che NON sono mie: si CONTANO e non si toccano.
VICINE = ("7900", "7910", "7920", "7700", "7730")

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)


def _carica(nome, percorso):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LE COSTANTI DELLE DUE CURE — LETTE NEL CODICE, non indovinate
# ═══════════════════════════════════════════════════════════════════════════
#
# `[R]` `src/webtransport.h` e `src/webtransport.c`, 23 agosto 2026.  ⚠ Stanno
# qui perche' i predicati ci si appoggiano; se il prodotto le cambia, il banco
# deve dare rosso — e per questo il valore IN VIGORE si rilegge dalla riga
# d'avvio (`stato_delle_cure()`) e si confronta con questi.
LM_PERMILLE = 50            # `WT_LM_PERMILLE`   — 5,0 %
LM_SILENZIO_S = 10          # `WT_LM_SILENZIO_S`
LM_MIN_PACCHETTI = 200      # `WT_LM_MIN_PACCHETTI`
LM_FINESTRE = 2             # `WT_LM_FINESTRE`
LM_FINESTRA_MS = 1000       # `WT_LM_FINESTRA_MS`
LM_MIN_PROVE = 2            # `WT_LM_MIN_PROVE`
SFRATTO_CONSIGLIATO_MS = 15000   # `SFRATTO_PREDEFINITO` = `SILENZIO / 2`
SILENZIO_MS = 30000              # `SILENZIO` di `rcp.c` — l'orologio di §5.3

# ── le soglie DEL BANCO, in un posto solo e ciascuna con la sua ragione ────
#
# ⛔ «La linea REGGE» non e' un'opinione: e' il numero sotto il quale la prova 1
#    non ha provato niente, perche' non avrei piu' un utente che stava
#    lavorando da NON buttare fuori.  ⚠ *Sufficiente, non giusto*: `[M]` 23 ago
#    `casa-cattiva` da' 7,8-10,2 fotogrammi/s e 1,48 % ne da' 5,5 con copertura
#    1,00 — 5,0 sta sotto tutt'e due, e sotto di li' la linea non porta piu'.
FPS_LINEA_CHE_REGGE = 5.0
# ⛔ Sotto queste finestre valide la ricostruzione della frazione dichiarata non
#    e' una misura: dieci minuti a una finestra al secondo ne danno ~600.
MIN_FINESTRE_VALIDE = 60
# ⭐ Quante finestre contano come «la PARTENZA della connessione»: dieci, cioe'
#   i primi ~10 s, che e' il tratto in cui `cwnd` si apre e ngtcp2 fa il grosso
#   del suo rilevamento di perdita a finestra piccola.  ⚠ Il numero e' scelto,
#   non misurato: serve a SEPARARE due tratti, non a giudicarne uno.
PRIME_FINESTRE = 10
# ⚠ Il giudizio della linea morta si prende UNA VOLTA AL SECONDO (`rete_ciclo`),
#   quindi uno scatto non puo' arrivare PRIMA della soglia e non deve arrivare
#   molto dopo.  Tre secondi coprono il ciclo, la coda del pacer e lo `ssh`.
TOLLERANZA_SILENZIO_MS = 3000
# ⭐ Il costo dichiarato dei PING: ~130 B a giro ogni soglia/2 secondi.
COSTO_PING_DICHIARATO_KBIT_S = 0.21
# ⚠ Lo sfratto e' un numero grosso: si accetta il ritardo di un giro di riprova
#   del cliente (1 s) piu' il ciclo del server.
TOLLERANZA_SFRATTO_MS = 4000

# ⭐ La griglia di `09-b76`, `[M]` 23 agosto 2026 — e' il denominatore della
#    prova 6: «i predefiniti non cambiano niente» vuol dire *identico a questo*.
GRIGLIA_B76 = {
    "casa-cattiva": {"fps_min": 7.0, "fps_max": 11.0, "copertura_min": 0.90,
                     "perche": "`[M]` 7,8-10,2 fotogrammi/s, sessione viva, "
                               "consegna che non si ferma"},
    "raffica-forte": {"consegna_si_ferma": True,
                      "perche": "`[M]` la consegna SI FERMA — 7 secondi su 25 "
                                "hanno visto un fotogramma, buco 14,26 s"},
}


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I MODULI ALTRUI — si importano, e POI si controlla che abbiano preso il MIO
#   ambiente
# ═══════════════════════════════════════════════════════════════════════════
B76 = None
B70 = None
B78 = None
RETE = None
LUC = None


def importa():
    global B76, B70, B78, RETE, LUC
    if B76 is not None:
        return B76
    B76 = _carica("b76rete", os.path.join(QUI, "09-b76-rete-cattiva.py"))
    guai = []
    for nome, mio, suo in (("porta", PORTA, B76.PORTA), ("utente", UTENTE, B76.UTENTE),
                           ("uid", UID_B, B76.UID_B), ("lavoro", LAV, B76.LAV),
                           ("albero", ALB, B76.ALB), ("dev", DEV, B76.DEV),
                           ("vietata", VIETATA, B76.VIETATA),
                           ("dentro_lav", DENTRO_LAV, B76.DENTRO_LAV)):
        if mio != suo:
            guai.append("09-b76 %s: ha «%s», il mio e' «%s»" % (nome, suo, mio))
    if guai:
        raise SystemExit("⛔ NON MISURO: l'import di 09-b76 non ha preso il mio "
                         "ambiente — " + " · ".join(guai))
    # ⛔ E il suo `importa()` fa il resto: carica b70, gli aggancia la rete con
    #    le SUE verifiche (guardiano, `prio` a quattro bande, due filtri `u32`
    #    sulla sola porta, `rimetti` che si controlla) e il lucchetto.
    B70 = B76.importa()
    RETE, LUC = B76.RETE, B76.LUC
    if RETE.PORTA != PORTA or RETE.DEV != DEV or RETE.VIETATA != VIETATA:
        raise SystemExit("⛔ NON TOCCO LA RETE: il modulo della rete ha porta %d, "
                         "dev «%s», vietata «%s»"
                         % (RETE.PORTA, RETE.DEV, RETE.VIETATA))
    B78 = _carica("b78apertura", os.path.join(QUI, "09-b78-apertura.py"))
    guai = []
    for nome, mio, suo in (("porta", PORTA, B78.PORTA), ("utente", UTENTE, B78.UTENTE),
                           ("lavoro", LAV, B78.LAV), ("albero", ALB, B78.ALB),
                           ("dentro_lav", DENTRO_LAV, B78.DENTRO_LAV)):
        if mio != suo:
            guai.append("09-b78 %s: ha «%s», il mio e' «%s»" % (nome, suo, mio))
    if guai:
        raise SystemExit("⛔ NON MISURO: l'import di 09-b78 non ha preso il mio "
                         "ambiente — " + " · ".join(guai))
    return B76


def root(comando, tetto=300):
    return RETE.root(comando, tetto)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ `registro_posato()` — PORTATO DA `07-b64-rete.py`, e non si tocca quel
#     file
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ IL DIFETTO CHE EVITA, `[M]` 23 agosto 2026 (`07-b64-rete.py:497`): la
#    chiusura di una sessione e' LENTA quando il pacer ha una coda — quel banco
#    ha misurato **29 s** di ritardo sul «conto finale» del profilo che perdeva
#    di piu'.  ⇒ Chi prende `riga0` subito dopo un giro prende una riga PRIMA
#    che il giro precedente abbia finito di scriversi, e legge il registro del
#    giro prima credendolo suo.
#
# ⛔⛔ E QUI FA MALE IL DOPPIO, perche' quel che leggo io non e' un conto: e' se
#     la cura sia SCATTATA.  Una riga `linea-morta` del giro prima letta dentro
#     la finestra di questo giro darebbe *«e' scattata»* a un giro in cui non e'
#     scattato niente — cioe' il falso positivo della prova 1 verrebbe
#     FABBRICATO DAL BANCO.  ⚠ E il verso opposto e' altrettanto brutto: la
#     prova 6 (i predefiniti) darebbe rosso su un prodotto che si comporta bene.
#
# ⚠ E il secondo guasto che quel riquadro racconta vale identico qui: finche' la
#   sessione di prima non si e' chiusa, §4.4-bis rifiuta la nuova con
#   `0x0F GIA_ATTIVA_REMOTA` — che nella prova 4 e' PROPRIO IL FENOMENO CHE
#   MISURO.  Misurare la serratura del giro prima al posto della mia darebbe un
#   numero vero e una causa inventata.
def conta_conti_finali():
    """Quante righe «audio di …, conto finale» ci sono ADESSO nel registro."""
    rc, out, _ = root("bash -c \"grep -ac 'audio di .*conto finale' "
                      "%s/registro.log || true\"" % LAV)
    try:
        return int(out.strip())
    except Exception:
        return -1


def registro_posato(tetto=90.0, quiete=3.0):
    """Si aspetta che il conto delle righe «conto finale» stia FERMO per
       `quiete` secondi, e si torna quel conto — vedi il riquadro qui sopra."""
    n = conta_conti_finali()
    fermo, scade = 0.0, time.time() + tetto
    while time.time() < scade and fermo < quiete:
        time.sleep(1.0)
        m = conta_conti_finali()
        fermo = (fermo + 1.0) if m == n else 0.0
        n = m
    return n


def righe_registro():
    """⛔ Niente `< file` in coda a un `sudo -S`: quel redirect gli RUBA lo
       stdin e la parola non arriva — e il conto torna 0 in silenzio, cioe' il
       banco legge il registro dall'accensione del server credendo di leggere
       il proprio giro (`09-b76`, il riquadro sopra `righe_registro`)."""
    return B76.righe_registro()


def riga0_pulita(tetto=90.0):
    """⭐ La riga da cui leggere QUESTO giro, presa quando il giro di prima ha
       finito di scriversi."""
    registro_posato(tetto=tetto)
    return righe_registro()


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL REGISTRO — l'orologio, e le tre righe che questo banco legge
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Le righe del registro cominciano con `HH:MM:SS.mmm ` (`src/registro.c`), ed
#    e' l'unico orologio che va bene per questi numeri: e' quello del SERVER.
#    ⚠ Un cronometro sul portatile misurerebbe anche l'`ssh`, il contenitore e
#      la differenza fra due orologi — su una soglia da 10 s quella e' la meta'
#      dell'errore che sto cercando.
_OROLOGIO = re.compile(r"^(\d\d):(\d\d):(\d\d)\.(\d\d\d)\s")


def t_registro(riga):
    """I secondi dalla mezzanotte di una riga di registro, o `None`.

    ⚠ Torna `None` e non `0` quando non c'e' l'ora: uno zero qui vorrebbe dire
      «mezzanotte» e sarebbe un numero plausibile e falso (`LEZIONI.md` §1.9).
    """
    m = _OROLOGIO.match(riga or "")
    if not m:
        return None
    return (int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
            + int(m.group(4)) / 1000.0)


def dt_registro(dopo, prima):
    """`dopo - prima` in secondi, con la mezzanotte scavalcata.

    ⚠ Torna `None` se manca uno dei due: «non lo so» non deve avere la stessa
      faccia di «zero secondi», che qui vorrebbe dire «e' scattata subito».
    """
    a, b = t_registro(dopo), t_registro(prima)
    if a is None or b is None:
        return None
    d = a - b
    return d + 86400.0 if d < -43200.0 else d


def leggi_registro(riga0, filtro, quante=400):
    """Le righe di QUESTO giro che contengono `filtro` (un `grep -e … -e …`).

    ⛔ `tail -n +riga0+1` e non l'intero registro: i congedi, gli scatti e i
       posti negati di chi ha girato prima non sono miei.
    """
    pezzi = " ".join("-e '%s'" % f for f in filtro)
    rc, out, _ = root("bash -c \"tail -n +%d %s/registro.log | grep -a %s | "
                      "tail -%d\"" % (riga0 + 1, LAV, pezzi, quante))
    return [r for r in out.splitlines() if r.strip()]


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ LA RIGA `linea-morta` — un contratto sul TESTO, e si legge come tale
# ═══════════════════════════════════════════════════════════════════════════
#
# `src/webtransport.c`, `linea_morta_scatta()`, fissa il formato come contratto:
#   1. il prefisso `linea-morta` e' STABILE ed e' la prima parola del corpo;
#   2. il secondo campo e' la provenienza (IND:PORTA), senza `=`;
#   3. ogni campo e' `nome=valore` senza spazi nel valore;
#   4. ⛔ `giudizio=` E' L'ULTIMO e arriva a fine riga, spazi compresi;
#   5. ⛔ i campi ci sono SEMPRE TUTTI, anche quelli che la causa non usa: a
#      dire quale ha deciso e' `causa=`, che e' il primo.
#
# ⛔ La riduzione sta a parte perche' e' quella che `--certifica` esercita su
#    righe FABBRICATE: un contratto sul testo si prova sul testo.
def riduci_linea_morta(righe, letto=True):
    """Dalle righe grezze ai numeri degli SCATTI.  ⛔ Non giudica: riduce.

    ⛔⛔ E «zero scatti» NON e' «non ho letto», ed e' la distinzione da cui
        dipende tutta la prova 1: zero righe `linea-morta` e' **il risultato che
        la prova 1 si aspetta**, mentre un registro non letto e' un banco cieco.
        ⇒ `letto` lo dice il chiamante, che sa se il `grep` e' andato a buon
          fine, e senza di lui questa funzione si rifiuta.
    """
    if not letto:
        return {"esito": "⛔ NON HO LETTO IL REGISTRO — «zero scatti» e «non ho "
                         "guardato» non devono avere la stessa faccia"}
    righe = [r for r in righe if "linea-morta " in r]
    n = {"esito": "letto", "scatti": len(righe), "righe": []}
    for r in righe:
        corpo = r.split("linea-morta ", 1)[1]
        giud = ""
        if "giudizio=" in corpo:
            corpo, giud = corpo.split("giudizio=", 1)
        pezzi = corpo.split()
        d = {"provenienza": pezzi[0] if pezzi and "=" not in pezzi[0] else None}
        for p in pezzi:
            if "=" in p:
                k, v = p.split("=", 1)
                d[k] = v
        d["giudizio"] = giud.strip()
        d["ora"] = t_registro(r)
        d["riga"] = r
        n["righe"].append(d)
    if righe:
        p = n["righe"][0]

        def num(k):
            try:
                return int(p.get(k))
            except (TypeError, ValueError):
                return None

        n["causa"] = p.get("causa")
        n["persi"] = num("persi")
        n["spediti"] = num("spediti")
        n["permille"] = num("permille")
        n["soglia_permille"] = num("soglia_permille")
        n["finestra_ms"] = num("finestra_ms")
        n["silenzio_ms"] = num("silenzio_ms")
        n["soglia_silenzio_ms"] = num("soglia_silenzio_ms")
        n["prove"] = num("prove")
        n["cwnd"] = num("cwnd")
        n["srtt_us"] = num("srtt_us")
        n["giudizio"] = p.get("giudizio", "")
        n["ora_primo"] = p.get("ora")
        n["cause"] = [x.get("causa") for x in n["righe"]]
    return n


def leggi_linea_morta(riga0):
    """Gli scatti di QUESTO giro, e la riga del trasporto che li esegue.

    ⚠ Si legge anche `LINEA MORTA — la connessione QUIC si chiude`: e' la meta'
      di `trasporto.c`, e una decisione presa senza che il filo cada sarebbe
      un'altra cosa da quel che l'utente ha scelto.
    """
    righe = leggi_registro(riga0, ["linea-morta ", "LINEA MORTA"])
    n = riduci_linea_morta([r for r in righe if "linea-morta " in r], letto=True)
    n["chiuse_dal_trasporto"] = len([r for r in righe if "LINEA MORTA" in r])
    return n


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ LO SFRATTO — le tre marche greppabili, come le dichiara `src/rcp.c`
# ═══════════════════════════════════════════════════════════════════════════
def riduci_sfratto(righe, letto=True):
    """`SFRATTO per silenzio:` · `⛔ SFRATTO NEGATO:` · `posto NEGATO`.

    ⛔ Anche qui «zero» non e' «non ho letto» — vedi `riduci_linea_morta`.
    """
    if not letto:
        return {"esito": "⛔ NON HO LETTO IL REGISTRO"}
    sfratti = [r for r in righe if "SFRATTO per silenzio:" in r]
    negati = [r for r in righe if "SFRATTO NEGATO:" in r]
    rifiuti = [r for r in righe if "posto NEGATO" in r]
    presi = [r for r in righe if "posto PRESO" in r]
    n = {"esito": "letto", "sfratti": len(sfratti), "negati": len(negati),
         "rifiuti": len(rifiuti), "presi": len(presi),
         "righe_sfratto": sfratti[:4], "righe_negato": negati[:4],
         "righe_rifiuto": rifiuti[:4], "righe_preso": presi[:4]}
    if sfratti:
        m = re.search(r"SFRATTO per silenzio: (\d+) ms", sfratti[0])
        n["muto_ms"] = int(m.group(1)) if m else None
        n["ora_sfratto"] = t_registro(sfratti[0])
        # ⭐ Chi e' stato sfrattato: serve alla prova 5, dove sfrattare l'utente
        #    sbagliato non sarebbe una comodita' ma un buco di sicurezza.
        m = re.search(r"il posto di (\S+) va al client", sfratti[0])
        n["sfrattato"] = m.group(1) if m else None
    # ⭐ Il silenzio dichiarato dentro la riga del RIFIUTO: e' il numero che
    #    mancava a chi legge il registro per sapere se il posto era di un client
    #    vivo o di un cadavere, ed esce anche a sfratto SPENTO.
    if rifiuti:
        m = re.search(r"segno di vita (\d+) ms fa", rifiuti[-1])
        n["ultimo_rifiuto_muto_ms"] = int(m.group(1)) if m else None
        n["sfratto_dice"] = ("SPENTO" if "e' SPENTO" in rifiuti[-1]
                             else "NON e' scattato" if "NON e' scattato" in rifiuti[-1]
                             else None)
    # ⛔ Chi ha preso il posto per ULTIMO, e a che ora: e' il numero della
    #    prova 4 — «a che secondo entra», e sull'orologio del server.
    if presi:
        m = re.search(r"posto PRESO da (\S+)", presi[-1])
        n["ultimo_preso_da"] = m.group(1) if m else None
        n["ora_ultimo_preso"] = t_registro(presi[-1])
    return n


def leggi_sfratto(riga0):
    righe = leggi_registro(riga0, ["SFRATTO", "posto NEGATO", "posto PRESO"])
    return riduci_sfratto(righe, letto=True)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ LA FRAZIONE **DICHIARATA**, ricostruita dalle righe `rete-quic`
# ═══════════════════════════════════════════════════════════════════════════
#
# ⇒ E' il falsificatore della prova 1 (⇒ il riquadro in testa).  Le righe
#   `rete-quic` portano `da_ms`, `persi_d` e `spediti_d`, che sono esattamente i
#   tre numeri con cui `linea_morta_giudica()` decide.  ⇒ Si applicano le SUE
#   guardie e si conta se due finestre di fila avrebbero mai sfondato la soglia.
#
# ⚠ `[?]` L'approssimazione e' dichiarata e sta nel verso prudente sbagliato: le
#   righe `rete-quic` tacciono quando non e' cambiato niente, quindi una loro
#   finestra puo' essere piu' lunga di un secondo — e mediando su piu' tempo
#   ABBASSA il picco.  ⇒ Da sola non chiude la domanda: accanto ci va la
#   taratura a `--linea-morta-permille 1`, che fa stampare al prodotto il
#   `permille=` calcolato da lui.
def finestre_dichiarate(righe, soglia_permille=LM_PERMILLE):
    """Dalle righe `rete-quic` alle finestre di giudizio della linea morta."""
    righe = [r for r in righe if "rete-quic " in r]
    if not righe:
        return {"esito": "NIENTE DA LEGGERE — nessuna riga «rete-quic» in questo "
                         "giro (⚠ binario piu' vecchio del 23 ago 2026?)"}
    valide, tutte = [], []
    for r in righe:
        corpo = r.split("rete-quic ", 1)[1].split("giudizio=", 1)[0]
        d = dict(p.split("=", 1) for p in corpo.split() if "=" in p)
        try:
            da, persi, sped = (int(d["da_ms"]), int(d["persi_d"]),
                               int(d["spediti_d"]))
        except (KeyError, ValueError):
            continue
        pm = (persi * 1000 // sped) if sped else None
        tutte.append({"da_ms": da, "persi_d": persi, "spediti_d": sped,
                      "permille": pm})
        # ⛔ Le due guardie della cura, alla lettera: sotto il minimo dei
        #    pacchetti non si decide niente, e la finestra dev'essere almeno
        #    quella minima.
        if sped >= LM_MIN_PACCHETTI and da >= LM_FINESTRA_MS:
            valide.append(pm)
    n = {"esito": "letto", "righe": len(tutte), "finestre_valide": len(valide)}
    if not valide:
        n["esito"] = ("NON GIUDICO — nessuna finestra ha superato le guardie "
                      "della cura (%d pacchetti spediti, %d ms): su %d righe "
                      "`rete-quic` la cura non avrebbe MAI deciso niente"
                      % (LM_MIN_PACCHETTI, LM_FINESTRA_MS, len(tutte)))
        return n
    ordinate = sorted(valide)
    n["permille_max"] = ordinate[-1]
    n["permille_p95"] = ordinate[int(0.95 * (len(ordinate) - 1))]
    n["permille_mediano"] = ordinate[len(ordinate) // 2]
    n["permille_medio"] = round(sum(valide) / float(len(valide)), 2)
    n["sopra_soglia"] = len([x for x in valide if x >= soglia_permille])
    # ⛔ `WT_LM_FINESTRE` = due DI FILA: e' quel che la cura pretende, e una
    #    finestra sola sopra soglia non chiude niente.
    fila, massima, coppie = 0, 0, 0
    for x in valide:
        if x >= soglia_permille:
            fila += 1
            massima = max(massima, fila)
            if fila >= LM_FINESTRE:
                coppie += 1
        else:
            fila = 0
    n["fila_massima_sopra_soglia"] = massima
    n["coppie_sopra_soglia"] = coppie
    n["soglia_permille"] = soglia_permille
    # ⭐⭐ E LA DOMANDA CHE IL PRIMO GIRO HA FATTO NASCERE: la frazione alta e'
    #    solo la PARTENZA della connessione, o dura tutta la sessione?
    #    `[M]` 23 ago 2026: la cura e' scattata al quarto secondo, dentro le
    #    prime finestre — quando `cwnd` si sta ancora aprendo e ogni pacchetto
    #    che sorpassa vale, in proporzione, molto di piu'.
    # ⇒ Le due meta' si contano a parte: se la coda e' bassa e solo l'inizio e'
    #   alto, il difetto non e' la SOGLIA, e' il MOMENTO in cui si giudica.
    primi = valide[:PRIME_FINESTRE]
    dopo = valide[PRIME_FINESTRE:]
    n["prime_finestre"] = len(primi)
    n["permille_max_prime"] = max(primi) if primi else None
    n["permille_max_dopo"] = max(dopo) if dopo else None
    n["permille_mediano_dopo"] = (sorted(dopo)[len(dopo) // 2] if dopo else None)
    n["sopra_soglia_dopo"] = len([x for x in dopo if x >= soglia_permille])
    fila, massima_d, coppie_d = 0, 0, 0
    for x in dopo:
        if x >= soglia_permille:
            fila += 1
            massima_d = max(massima_d, fila)
            if fila >= LM_FINESTRE:
                coppie_d += 1
        else:
            fila = 0
    n["fila_massima_dopo"] = massima_d
    n["coppie_sopra_soglia_dopo"] = coppie_d
    # ⭐ E la CUMULATIVA, che e' un'altra grandezza e va detta accanto: e' la
    #    frazione su tutta la sessione, non su una finestra.
    tot_p = sum(x["persi_d"] for x in tutte)
    tot_s = sum(x["spediti_d"] for x in tutte)
    n["cumulativa_permille"] = round(1000.0 * tot_p / tot_s, 2) if tot_s else None
    n["persi_totali"] = tot_p
    n["spediti_totali"] = tot_s
    return n


def leggi_finestre(riga0, soglia_permille=LM_PERMILLE):
    righe = leggi_registro(riga0, ["rete-quic "], quante=2000)
    return finestre_dichiarate(righe, soglia_permille)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ L'OROLOGIO DEL FILO — «quanto costa davvero una sessione ferma?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Gira SULLA MACCHINA e legge i contatori del `netem`, non un `tcpdump`: e'
#    lo stesso contatore che `09-b76` usa per il qdisc, e leggerlo da qui
#    costerebbe un giro di `ssh` per campione — cioe' 200 ms di errore su una
#    misura che deve distinguere 5 s da 10 s.
OROLOGIO = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09-b81-orologio — i contatori del netem campionati SUL POSTO.

⛔ Non riduce e non giudica: stampa i campioni.  La riduzione sta nel banco, ed
   e' quella che il controllo positivo esercita su campioni fabbricati.
"""
import json, re, subprocess, sys, time

def principale():
    dev, secondi, passo = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    campioni = []
    t0 = time.monotonic()
    while time.monotonic() - t0 < secondi:
        out = subprocess.run(["/usr/sbin/tc", "-s", "qdisc", "show", "dev", dev],
                             capture_output=True).stdout.decode("utf-8", "replace")
        pezzi = out.split("qdisc netem 40:")
        if len(pezzi) > 1:
            m = re.search(r"Sent (\d+) bytes (\d+) pkt", pezzi[1])
            if m:
                campioni.append([round(time.monotonic() - t0, 3),
                                 int(m.group(1)), int(m.group(2))])
        time.sleep(passo)
    print(json.dumps({"campioni": campioni}))

if __name__ == "__main__":
    principale()
'''


def riduci_orologio(campioni, quiete_s=0.6):
    """Dai campioni del contatore ai numeri del TRAFFICO A RIPOSO.

    · **kbit_s** e **pacchetti_s** — quel che una sessione ferma costa DAVVERO;
    · **eventi** — i gruppi di campioni in cui il contatore e' salito, separati
      da almeno `quiete_s` di silenzio: ⭐ e' il modo di vedere i PING senza un
      `tcpdump`, perche' su una linea ferma un PING e il suo riscontro sono
      l'unica cosa che muove il contatore;
    · **intervallo_mediano_s** — il periodo fra due eventi, ed e' il numero che
      dice se i PING sono passati da 10 s a 5.

    ⛔ Non giudica: riduce.  ⚠ E se il contatore non si ferma MAI, gli eventi
      sono uno solo e l'intervallo e' `None` — che vuol dire «questa sessione
      non e' ferma», non «zero secondi».
    """
    n = {"campioni": len(campioni or [])}
    if not campioni or len(campioni) < 3:
        n["esito"] = ("NON GIUDICO — %d campioni: senza almeno tre non c'e' un "
                      "intervallo da misurare" % len(campioni or []))
        return n
    t0, b0, p0 = campioni[0]
    t1, b1, p1 = campioni[-1]
    durata = t1 - t0
    if durata <= 0:
        n["esito"] = "NON GIUDICO — la finestra dei campioni e' lunga zero"
        return n
    n["esito"] = "misurato"
    n["secondi"] = round(durata, 2)
    n["byte"] = b1 - b0
    n["pacchetti"] = p1 - p0
    n["kbit_s"] = round(8.0 * (b1 - b0) / durata / 1000.0, 4)
    n["pacchetti_s"] = round((p1 - p0) / durata, 3)
    eventi, prec_t, prec_p, aperto = [], t0, p0, None
    for t, b, p in campioni[1:]:
        if p > prec_p:
            if aperto is None:
                aperto = t
            prec_t = t
        elif aperto is not None and t - prec_t >= quiete_s:
            eventi.append([round(aperto, 3), round(prec_t, 3),
                           p - _pkt_a(campioni, aperto)])
            aperto = None
        prec_p = p
    if aperto is not None:
        eventi.append([round(aperto, 3), round(prec_t, 3), None])
    n["eventi"] = len(eventi)
    n["eventi_primi"] = eventi[:6]
    if len(eventi) >= 2:
        inter = [round(eventi[i][0] - eventi[i - 1][0], 3)
                 for i in range(1, len(eventi))]
        inter_ord = sorted(inter)
        n["intervalli_s"] = inter[:12]
        n["intervallo_mediano_s"] = inter_ord[len(inter_ord) // 2]
        n["intervallo_min_s"] = inter_ord[0]
        n["intervallo_max_s"] = inter_ord[-1]
        # ⭐ I byte per giro: il conto che il riquadro dei PING dichiara ~130 B.
        n["byte_per_evento"] = round((b1 - b0) / float(len(eventi)), 1)
    else:
        n["intervallo_mediano_s"] = None
        n["perche_niente_intervallo"] = (
            "il contatore non si e' mai fermato per %.1f s di fila: questa "
            "sessione NON e' ferma, e un intervallo fra due eventi non esiste"
            % quiete_s)
    return n


def _pkt_a(campioni, t):
    for x in campioni:
        if x[0] >= t:
            return x[2]
    return campioni[-1][2]


def orologio_gira(secondi=60.0, passo=0.1):
    rc, out, err = root("python3 %s/09-b81-orologio.py %s %g %g"
                        % (LAV, DEV, secondi, passo), int(secondi) + 120)
    try:
        d = json.loads(out)
    except Exception as e:
        _dub("l'orologio non ha risposto: %s — %s" % (e, (out + err)[-200:]))
        return {"esito": "NON GIUDICO — l'orologio del filo non ha risposto"}
    return riduci_orologio(d.get("campioni") or [])


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ LO STATO DELLE DUE CURE — si RILEGGE dalla riga d'avvio, non si assume
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔⛔ E' LA GUARDIA DA CUI DIPENDE TUTTA LA PROVA 1.  «Zero scatti» vale solo se
#     la cura era ACCESA: con la cura spenta zero scatti e' il comportamento di
#     ieri, e chiamarlo «nessun falso positivo» vorrebbe dire dichiarare
#     provata una cura che non ha nemmeno girato — ⚠ e con un'opzione battuta a
#     mano dentro tre livelli di `ssh` e `systemd-run` non e' un'ipotesi
#     teorica.
#
# ⭐ E si puo' fare solo perche' `main.c` chiama `wt_linea_morta()` SEMPRE, e
#    `rcp_sfratto()` si stampa acceso E spento: la riga d'avvio esce nei due
#    casi per costruzione, ed e' meta' del valore delle due cure.
def stato_delle_cure():
    """Che cosa dice il server di se stesso, all'ULTIMO avvio."""
    rc, out, _ = root("bash -c \"grep -a -n -e 'LINEA MORTA e' -e 'sfratto del "
                      "fantasma: soglia' %s/registro.log | tail -6\"" % LAV)
    righe = [r for r in out.splitlines() if r.strip()]
    n = {"esito": "letto" if righe else "⛔ NON HO LETTO nessuna riga d'avvio "
                                        "delle due cure",
         "linea_morta": None, "permille": None, "silenzio_s": None,
         "sfratto_ms": None, "righe": righe[-2:]}
    for r in righe:
        if "LINEA MORTA e' ACCESA" in r:
            n["linea_morta"] = "accesa"
            m = re.search(r"persi/spediti ≥ (\d+)‰", r)
            n["permille"] = int(m.group(1)) if m else None
            m = re.search(r"\(2\) SILENZIO: (\d+) s", r)
            n["silenzio_s"] = int(m.group(1)) if m else None
        elif "LINEA MORTA e' SPENTA" in r:
            n["linea_morta"] = "spenta"
            n["permille"], n["silenzio_s"] = None, None
        if "sfratto del fantasma: soglia" in r:
            m = re.search(r"soglia (\d+) ms", r)
            n["sfratto_ms"] = int(m.group(1)) if m else None
    return n


def cure_come_voglio(stato, linea_morta=None, permille=None, silenzio_s=None,
                     sfratto_ms=None):
    """(va_bene, perche') — il server e' configurato come questa prova pretende?

    ⛔ Chiamata PRIMA di ogni prova: un predicato che gira su una configurazione
       diversa da quella che crede non da' rosso, da' un numero plausibile.
    """
    if stato.get("esito") != "letto":
        return _muto(stato.get("esito"))
    guai = []
    if linea_morta is not None and stato["linea_morta"] != linea_morta:
        guai.append("la linea morta risulta «%s» e la volevo «%s»"
                    % (stato["linea_morta"], linea_morta))
    if permille is not None and stato["permille"] != permille:
        guai.append("la soglia della perdita e' %s‰ e la volevo %d‰"
                    % (stato["permille"], permille))
    if silenzio_s is not None and stato["silenzio_s"] != silenzio_s:
        guai.append("la soglia del silenzio e' %s s e la volevo %d"
                    % (stato["silenzio_s"], silenzio_s))
    if sfratto_ms is not None and stato["sfratto_ms"] != sfratto_ms:
        guai.append("lo sfratto e' a %s ms e lo volevo a %d"
                    % (stato["sfratto_ms"], sfratto_ms))
    if guai:
        return _muto("⛔ NON MISURO: il server non e' configurato come questa "
                     "prova pretende — " + " · ".join(guai))
    return _si("il server dice di se': linea morta %s (%s‰, %s s) · sfratto %s ms"
               % (stato["linea_morta"], stato["permille"], stato["silenzio_s"],
                  stato["sfratto_ms"]))


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ I SEI PREDICATI, SCRITTI PRIMA — «(numeri) -> (passa, perche')»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `PIANO.md` §0.3.4: un banco che non sa vedere il difetto che cerca non ha
#    diritto al verde.  ⇒ Ognuno di questi sa dare VERDE, ROSSO e MUTO, e
#    `--certifica` lo prova su numeri fabbricati.  Un predicato mai visto
#    fallire non e' un predicato.

def p1_niente_falso_positivo(lm, testimoni, n, minuti):
    """⛔⛔ **LA PROVA CHE PUO' FAR RITIRARE LA CURA.**

    Su `casa-cattiva` — la linea che REGGE — la linea morta accesa non deve
    scattare NEMMENO UNA VOLTA in dieci minuti.  Uno scatto qui vuol dire
    buttare fuori uno che stava lavorando, ed e' l'errore che non si rimedia.

    ⚠ E il verde vale solo se la linea ha davvero retto: se la sessione non si
      e' aperta, o e' caduta per altro, o il ritmo e' sotto `FPS_LINEA_CHE_REGGE`
      (5,0 fotogrammi/s), qui non c'era nessun utente al lavoro da NON buttare
      fuori — e allora questo predicato TACE invece di dare un verde che non ha
      guadagnato.
    """
    if not lm or lm.get("esito") != "letto":
        return _muto((lm or {}).get("esito", "non ho letto gli scatti"))
    if lm["scatti"] > 0:
        p = lm["righe"][0]
        return _no("⛔⛔ FALSO POSITIVO: la linea morta e' scattata %d volta/e "
                   "in %g minuti su una linea che il prodotto stava servendo — "
                   "causa=%s persi=%s spediti=%s permille=%s (soglia %s‰) "
                   "finestra_ms=%s.  ⇒ Accenderla vorrebbe dire buttare fuori "
                   "un utente al lavoro: LA CURA NON SI ACCENDE"
                   % (lm["scatti"], minuti, p.get("causa"), p.get("persi"),
                      p.get("spediti"), p.get("permille"),
                      p.get("soglia_permille"), p.get("finestra_ms")))
    if not testimoni:
        return _muto("nessuno scatto, ma non ho interrogato i testimoni della "
                     "connessione: senza, non so se ci fosse un utente al "
                     "lavoro da non buttare fuori")
    if testimoni.get("aperta") is False:
        return _muto("⚠ nessuno scatto, ma la sessione non risulta essersi "
                     "APERTA: «non si e' mai aperta» ha la stessa faccia di «non "
                     "e' scattato niente», e non e' la stessa cosa")
    if testimoni.get("cliente_staccato"):
        return _muto("⚠ nessuno scatto della linea morta, ma il cliente e' "
                     "caduto lo stesso: «%s» — la linea non ha retto, e questa "
                     "prova non ha provato niente"
                     % (testimoni.get("caduta") or "")[:140])
    fps = (n or {}).get("fps")
    if fps is None:
        return _muto("nessuno scatto, ma non ho il ritmo consegnato: senza, "
                     "non so se la linea reggesse")
    if fps < FPS_LINEA_CHE_REGGE:
        return _muto("⚠ ZERO scatti, ma il ritmo e' %.2f fotogrammi/s (sotto "
                     "%.1f): questa linea non stava servendo nessuno, e non "
                     "avere buttato fuori nessuno non e' un merito"
                     % (fps, FPS_LINEA_CHE_REGGE))
    c = (n or {}).get("consegna") or {}
    return _si("⭐ ZERO scatti in %g minuti su una linea che REGGE: %.2f "
               "fotogrammi/s, copertura %s, buco piu' lungo %s s, cliente "
               "ancora attaccato e nessun congedo nel registro"
               % (minuti, fps, c.get("copertura"), c.get("buco_max_s")))


def p1c_la_linea_regge_a_cura_spenta(testimoni, n, minuti, scatti_accesa):
    """⛔⛔ **IL CONTROLLO DELLA PROVA 1, E SENZA DI LUI IL SUO ROSSO NON VALE.**

    Quando la cura scatta, la sessione MUORE — e da un giro in cui la sessione e'
    morta a 4 s non si puo' dire se la linea reggesse: «la cura ha buttato fuori
    uno che lavorava» e «la linea era finita comunque» hanno la stessa faccia.
    ⚠ E' la forma di `LEZIONI.md` §1.9 applicata a un giudizio invece che a un
      numero.

    ⇒ Stessa linea, stessa durata, **cure SPENTE**: se la sessione regge tutti i
      minuti a piu' di `FPS_LINEA_CHE_REGGE` fotogrammi al secondo, allora la
      differenza fra i due giri e' **un interruttore**, e quel che la cura ha
      buttato fuori era un utente al lavoro.  Se invece non regge nemmeno a cura
      spenta, questo predicato da' ROSSO — perche' allora il rosso della prova 1
      non e' un falso positivo, e il banco lo deve dire.
    """
    if not testimoni:
        return _muto("non ho interrogato i testimoni della connessione")
    if testimoni.get("aperta") is False:
        return _muto("la sessione non risulta essersi aperta: la domanda e' di "
                     "`09-b78-apertura.py`, e io non giudico")
    if testimoni.get("cliente_staccato"):
        return _no("⛔ A CURA SPENTA LA SESSIONE E' CADUTA LO STESSO: «%s» — "
                   "allora lo scatto della prova 1 non e' un falso positivo, e "
                   "questa linea non e' quella che REGGE"
                   % (testimoni.get("caduta") or "")[:160])
    fps = (n or {}).get("fps")
    c = (n or {}).get("consegna") or {}
    if fps is None or c.get("esito") != "misurato":
        return _muto("non ho il ritmo o la consegna di questo giro: senza, non "
                     "posso dire che la linea reggesse")
    coda = ("%.2f fotogrammi/s · copertura %.2f · buco piu' lungo %.2f s · "
            "ultimo fotogramma a %.2f s su %g minuti"
            % (fps, c["copertura"], c["buco_max_s"], c["consegna_fino_a_s"],
               minuti))
    if fps < FPS_LINEA_CHE_REGGE:
        return _no("⛔ a cura spenta la linea da' %.2f fotogrammi/s (sotto %.1f): "
                   "non stava servendo nessuno nemmeno cosi', e lo scatto della "
                   "prova 1 non si puo' chiamare falso positivo.  %s"
                   % (fps, FPS_LINEA_CHE_REGGE, coda))
    if c["copertura"] < B76.COPERTURA_MINIMA:
        return _no("⛔ a cura spenta la consegna si e' fermata lo stesso "
                   "(copertura %.2f < %.2f): %s"
                   % (c["copertura"], B76.COPERTURA_MINIMA, coda))
    return _si("⭐ A CURA SPENTA LA STESSA LINEA REGGE %g minuti interi: %s — "
               "⇒ fra i due giri cambia UN INTERRUTTORE, e con quello acceso la "
               "sessione e' stata chiusa %d volta/e.  Quel che la cura butta "
               "fuori e' un utente al lavoro" % (minuti, coda, scatti_accesa))


def p1b_soglia_sopra_la_dichiarata(fin, sonda):
    """⛔⭐ IL FALSIFICATORE DICHIARATO — ⇒ il riquadro in testa al file.

    La soglia e' sulla frazione DICHIARATA da ngtcp2; l'1,71 %% che regge e' la
    perdita INIETTATA.  Con jitter e riordino la dichiarata puo' essere piu'
    alta, perche' un sorpasso viene scambiato per una perdita.  ⇒ Se sulla
    linea che REGGE la dichiarata ha sfondato i %d‰ — e peggio, per due finestre
    di fila — la soglia e' sbagliata, e va detto invece che aggirato.
    """ % LM_PERMILLE
    if not fin or fin.get("esito") != "letto":
        return _muto((fin or {}).get("esito", "non ho ricostruito le finestre"))
    if fin["finestre_valide"] < MIN_FINESTRE_VALIDE:
        return _muto("solo %d finestre hanno superato le guardie della cura "
                     "(ne volevo almeno %d): su cosi' poche, «non ha mai "
                     "sfondato» non e' una misura"
                     % (fin["finestre_valide"], MIN_FINESTRE_VALIDE))
    coda = ("%d finestre valide · DICHIARATA max %d‰ · p95 %d‰ · mediana %d‰ · "
            "media %.2f‰ · cumulativa %.2f‰ (%d persi su %d spediti)"
            % (fin["finestre_valide"], fin["permille_max"], fin["permille_p95"],
               fin["permille_mediano"], fin["permille_medio"],
               fin["cumulativa_permille"], fin["persi_totali"],
               fin["spediti_totali"]))
    iniettata = ("INIETTATA %.2f %% (sonda)" % sonda["persi_pc"]) if (
        sonda and sonda.get("esito") == "misurato") else "INIETTATA: non sondata"
    if fin["coppie_sopra_soglia"] > 0:
        return _no("⛔⛔ LA SOGLIA E' SBAGLIATA: su una linea che REGGE la "
                   "frazione DICHIARATA ha sfondato i %d‰ per %d finestre di "
                   "fila (fila massima %d) — cioe' la condizione esatta con cui "
                   "la cura chiude la sessione.  %s · %s"
                   % (fin["soglia_permille"], LM_FINESTRE,
                      fin["fila_massima_sopra_soglia"], coda, iniettata))
    if fin["permille_max"] >= fin["soglia_permille"]:
        return _no("⛔ la frazione DICHIARATA ha toccato la soglia (%d‰ ≥ %d‰) "
                   "in %d finestre su una linea che REGGE: non ha fatto due di "
                   "fila e per questo la cura non e' scattata, ma il margine "
                   "dichiarato (2,9× sopra l'1,71 %%) qui non c'e'.  %s · %s"
                   % (fin["permille_max"], fin["soglia_permille"],
                      fin["sopra_soglia"], coda, iniettata))
    return _si("⭐ la DICHIARATA non ha mai toccato la soglia: %s ≤ %d‰ · %s · %s"
               % (fin["permille_max"], fin["soglia_permille"], coda, iniettata))


def p2_scatta_sulla_raffica(lm, sonda, secondi_a_scatto):
    """**Lo scatto vero.**  Su `raffica-forte` — `[M]` 11,10 % di perdita a
    raffiche, `cwnd` mediana 8 948 B contro 105 616 del riferimento, la consegna
    che si ferma — la cura DEVE scattare, e con `causa=perdita`.

    ⚠ Se la sonda dice che il guasto non e' stato messo, qui si TACE: misurare
      un profilo che non esiste e' peggio che non misurarlo, perche' il numero e'
      vero e la causa e' inventata.
    """
    if not sonda or sonda.get("esito") != "misurato":
        return _muto("la sonda non ha misurato: senza, non so se la raffica sia "
                     "stata messa, e uno scatto senza guasto non e' uno scatto")
    if sonda["persi_pc"] < 5.0:
        return _muto("⚠ la sonda ha visto il %.2f %% di perdita: non e' "
                     "`raffica-forte` (`[M]` 11,10 %%), e non giudico un "
                     "profilo che non esiste" % sonda["persi_pc"])
    if not lm or lm.get("esito") != "letto":
        return _muto((lm or {}).get("esito", "non ho letto gli scatti"))
    if lm["scatti"] == 0:
        return _no("⛔ la cura NON e' scattata su una linea che il prodotto non "
                   "sa servire: la sonda ha visto il %.2f %% in raffiche di "
                   "%.2f, e `[M]` a questa perdita l'immagine o si congela "
                   "(14,26 s su 25) o arriva con 4,5 s di ritardo"
                   % (sonda["persi_pc"], sonda["raffica_media"]))
    if lm.get("causa") != "perdita":
        return _no("⛔ e' scattata, ma per il motivo SBAGLIATO: causa=%s su una "
                   "linea che perde il %.2f %% — un silenzio non e' una "
                   "raffica, e le due cause mandano a cercare la causa in due "
                   "posti diversi" % (lm.get("causa"), sonda["persi_pc"]))
    if lm.get("chiuse_dal_trasporto", 0) < 1:
        return _no("⛔ la decisione e' stata presa (riga `linea-morta`) ma il "
                   "filo NON e' caduto: manca la riga di `trasporto.c` «LINEA "
                   "MORTA — la connessione QUIC si chiude».  ⚠ L'utente ha "
                   "scelto che il filo cada, non che il server lo scriva")
    return _si("⭐ scattata dopo %s s dall'aggancio del posto: causa=perdita "
               "persi=%s spediti=%s permille=%s‰ (soglia %s‰) finestra_ms=%s "
               "finestre=%s cwnd=%s srtt_us=%s · il filo e' caduto (%d riga/e "
               "di `trasporto.c`) · la sonda: %.2f %% in raffiche di %.2f"
               % (("%.2f" % secondi_a_scatto) if secondi_a_scatto is not None
                  else "?", lm.get("persi"), lm.get("spediti"),
                  lm.get("permille"), lm.get("soglia_permille"),
                  lm.get("finestra_ms"),
                  (lm["righe"][0].get("finestre") if lm.get("righe") else "?"),
                  lm.get("cwnd"), lm.get("srtt_us"),
                  lm.get("chiuse_dal_trasporto", 0), sonda["persi_pc"],
                  sonda["raffica_media"]))


def p3_scatta_sul_silenzio(lm, soglia_ms):
    """**Il silenzio.**  Cliente ucciso con `kill -9` — cioe' un addio MAI
    DETTO, che per il server e' identico a un addio perso — e la cura deve
    scattare con `causa=silenzio` alla sua soglia.

    ⛔ E LE DUE DIREZIONI NON COSTANO UGUALE, come per la prova 1: scattare
       TARDI vuol dire qualche secondo in piu' di fantasma; scattare PRIMA della
       soglia vuol dire buttare fuori un client vivo che stava zitto — ⇒ sotto
       la soglia e' rosso senza sconti, sopra si concede %.1f s (il giudizio si
       prende una volta al secondo, e c'e' la coda del pacer).
    """ % (TOLLERANZA_SILENZIO_MS / 1000.0)
    if not lm or lm.get("esito") != "letto":
        return _muto((lm or {}).get("esito", "non ho letto gli scatti"))
    if lm["scatti"] == 0:
        return _no("⛔ il cliente e' morto senza dire addio e la cura NON e' "
                   "scattata: il posto resta a un fantasma fino ai 30 s di "
                   "§5.3, che e' precisamente quel che questa cura doveva "
                   "togliere")
    if lm.get("causa") != "silenzio":
        return _no("⛔ e' scattata con causa=%s e non «silenzio»: il cliente e' "
                   "stato ucciso, non c'era nessuna raffica da vedere"
                   % lm.get("causa"))
    s = lm.get("silenzio_ms")
    if s is None:
        return _muto("la riga non porta `silenzio_ms`: il contratto sul testo "
                     "non regge, e non ho il numero su cui giudicare")
    if s < soglia_ms:
        return _no("⛔⛔ SCATTATA PRIMA DELLA SUA SOGLIA: %d ms di silenzio "
                   "contro %d dichiarati — un client vivo e fermo verrebbe "
                   "buttato fuori, ed e' la regressione gia' pagata il 16 "
                   "agosto 2026" % (s, soglia_ms))
    if s > soglia_ms + TOLLERANZA_SILENZIO_MS:
        return _no("⛔ scattata a %d ms contro %d dichiarati (+%d di "
                   "tolleranza): il numero scritto e quello in vigore "
                   "divergono, ed e' la forma E1"
                   % (s, soglia_ms, TOLLERANZA_SILENZIO_MS))
    if lm.get("chiuse_dal_trasporto", 0) < 1:
        return _no("⛔ la decisione e' stata presa ma il filo NON e' caduto: "
                   "manca la riga di `trasporto.c`")
    return _si("⭐ scattata a %d ms di silenzio (soglia %d) con causa=silenzio, "
               "prove=%s (minimo %s) — e il filo e' caduto"
               % (s, soglia_ms, lm.get("prove"), lm.get("minimo_prove")
                  or LM_MIN_PROVE))


def p3b_costo_dei_ping(acceso, spento, dichiarato=COSTO_PING_DICHIARATO_KBIT_S):
    """⚠ **IL PREZZO DICHIARATO DEI PING.**  Il riquadro di `webtransport.c`
    dichiara ~130 B a giro ogni META' della soglia, cioe' **%.2f kbit/s** per
    sessione.  ⇒ Si misura il traffico VERO di una sessione ferma, acceso e
    spento, e la differenza non puo' superare il costo dichiarato — se lo
    supera, e' un numero da correggere.

    ⛔ E QUESTO PREDICATO SI RIFIUTA QUANDO IL RUMORE E' PIU' GROSSO DEL
       BERSAGLIO, che e' l'unica cosa onesta da fare: un «verde» ottenuto
       misurando %.2f kbit/s dentro un fondo mille volte piu' alto non
       prova niente, e sarebbe la forma E1 al contrario.
    """ % (COSTO_PING_DICHIARATO_KBIT_S, COSTO_PING_DICHIARATO_KBIT_S)
    if not acceso or acceso.get("esito") != "misurato":
        return _muto("il traffico a cura ACCESA non l'ho misurato")
    if not spento or spento.get("esito") != "misurato":
        return _muto("il traffico a cura SPENTA non l'ho misurato")
    delta = acceso["kbit_s"] - spento["kbit_s"]
    fondo = min(acceso["kbit_s"], spento["kbit_s"])
    coda = ("acceso %.3f kbit/s (%d pacchetti in %.1f s) · spento %.3f kbit/s "
            "(%d in %.1f s) · differenza %+.3f kbit/s · dichiarato %.2f"
            % (acceso["kbit_s"], acceso["pacchetti"], acceso["secondi"],
               spento["kbit_s"], spento["pacchetti"], spento["secondi"],
               delta, dichiarato))
    # ⛔ Il fondo dev'essere piccolo davanti al bersaglio, o non si sta
    #    misurando il bersaglio.  Dieci volte e' generoso e si dichiara.
    if fondo > 10.0 * dichiarato:
        return _muto("⛔ NON GIUDICO — una sessione «ferma» di questo prodotto "
                     "non e' ferma: costa %.1f kbit/s, cioe' %d volte il costo "
                     "dichiarato dei PING (%.2f).  ⭐ E' l'audio PCM di §4.3, "
                     "che NON si puo' spegnere (`[M]` un CIAO senza codec audio "
                     "in comune si becca `0x09 NIENTE_IN_COMUNE`).  ⇒ Dentro "
                     "questo fondo il costo dei PING non si isola, e un verde "
                     "qui non proverebbe niente.  %s"
                     % (fondo, int(fondo / dichiarato), dichiarato, coda))
    if delta > 2.0 * dichiarato:
        return _no("⛔ i PING costano piu' del dichiarato: %s" % coda)
    return _si("il costo dei PING sta nel dichiarato: %s" % coda)


def p4_lo_sfratto_libera_il_posto(sf, soglia_ms, secondi_a_entrare, riferimento_s):
    """**Lo sfratto.**  Stesso utente, cliente ucciso con `-9`, un secondo
    client che chiede il posto.  `[M]` oggi servono **30,5 s** e **11 rifiuti**;
    con `--sfratto-ms %d` il posto deve tornare libero a **~%.0f s**.

    ⚠ E anche qui il verso conta: sfrattare TROPPO PRESTO vuol dire togliere il
      posto a un client vivo e fermo, cioe' spegnere I2 — quindi sotto la
      soglia e' rosso.
    """ % (SFRATTO_CONSIGLIATO_MS, SFRATTO_CONSIGLIATO_MS / 1000.0)
    if not sf or sf.get("esito") != "letto":
        return _muto((sf or {}).get("esito", "non ho letto il registro"))
    if secondi_a_entrare is None:
        return _muto("non ho l'ora in cui il posto e' stato ripreso: senza, "
                     "«e' entrato» e «non e' entrato» hanno la stessa faccia")
    if sf["sfratti"] == 0:
        return _no("⛔ nessuno SFRATTO: il posto e' tornato libero dopo %.2f s "
                   "con %d rifiuti, cioe' all'orologio del silenzio di §5.3 — "
                   "la cura non ha fatto niente"
                   % (secondi_a_entrare, sf["rifiuti"]))
    muto = sf.get("muto_ms")
    if muto is None:
        return _muto("la riga dello sfratto non porta i millisecondi di "
                     "silenzio: il contratto sul testo non regge")
    if muto < soglia_ms:
        return _no("⛔⛔ SFRATTATO PRIMA DELLA SOGLIA: l'occupante taceva da %d "
                   "ms e la soglia e' %d — un client vivo e fermo (`[M]` il "
                   "keep-alive di un browser tace 15 s) verrebbe buttato fuori, "
                   "e quello spegne l'invariante I2" % (muto, soglia_ms))
    if secondi_a_entrare > (soglia_ms + TOLLERANZA_SFRATTO_MS) / 1000.0:
        return _no("⛔ il posto e' tornato libero dopo %.2f s con la soglia a "
                   "%.1f s (+%.1f di tolleranza): la cura e' scattata ma non ha "
                   "accorciato quel che doveva"
                   % (secondi_a_entrare, soglia_ms / 1000.0,
                      TOLLERANZA_SFRATTO_MS / 1000.0))
    guadagno = ("da %.1f s a %.2f s (%.0f %% in meno)"
                % (riferimento_s, secondi_a_entrare,
                   100.0 * (1.0 - secondi_a_entrare / riferimento_s))
                if riferimento_s else "senza riferimento misurato in questo giro")
    return _si("⭐ il posto e' tornato libero dopo %.2f s con %d rifiuti — "
               "l'occupante taceva da %d ms (soglia %d), sfrattato «%s» · %s"
               % (secondi_a_entrare, sf["rifiuti"], muto, soglia_ms,
                  sf.get("sfrattato"), guadagno))


def p5_fra_utenti_diversi_non_si_sfratta(sf, entrato, utente_a, utente_b):
    """⛔ **IL CASO CHE NON DEVE ROMPERSI.**  Uno sfratto fra utenti diversi non
    sarebbe una comodita': sarebbe un buco di sicurezza — chiunque potrebbe far
    cadere il desktop di un altro semplicemente bussando.

    ⇒ Due cose insieme, e la prima e' quella che conta:
      a) NESSUNO sfratto che tolga il posto al primo utente mentre a chiedere
         e' un utente DIVERSO;
      b) il secondo utente entra lo stesso, sul PROPRIO posto (`MAX_ATTACCATE`
         = 16): negargli l'ingresso sarebbe un difetto diverso e altrettanto
         vero.
    """
    if not sf or sf.get("esito") != "letto":
        return _muto((sf or {}).get("esito", "non ho letto il registro"))
    if sf["sfratti"] > 0:
        return _no("⛔⛔ BUCO DI SICUREZZA: c'e' stato uno SFRATTO mentre a "
                   "chiedere il posto era un utente DIVERSO — sfrattato «%s», "
                   "riga: «%s»"
                   % (sf.get("sfrattato"), (sf.get("righe_sfratto") or [""])[0][:200]))
    if entrato is not True:
        return _muto("nessuno sfratto (ed e' quel che volevo), ma «%s» non "
                     "risulta essere entrato: senza il suo ingresso non ho "
                     "provato che il posto del primo sia rimasto suo — ho solo "
                     "provato che non e' successo niente" % utente_b)
    return _si("⭐ nessuno sfratto fra «%s» e «%s», e il secondo utente e' "
               "entrato lo stesso sul proprio posto: %d posti presi, %d rifiuti"
               % (utente_a, utente_b, sf["presi"], sf["rifiuti"]))


def p5b_la_riga_del_negato(sf):
    """⚠ **E LA RIGA `⛔ SFRATTO NEGATO` ESCE?**  La previsione e' scritta PRIMA
    e va nel verso scomodo: `[R]` 23 agosto 2026, leggendo `src/rcp.c`, **NO**.

    Il registro dei posti e' indicizzato PER NOME (`posto_occupato(utente)`),
    quindi `POSTO_OCCUPATO` implica gia' «stesso utente» e due utenti diversi
    prendono due posti diversi: il ramo con quella riga non viene MAI percorso.
    ⇒ Chi l'ha scritto lo dichiara nel suo stesso commento — *«ridondante per
    costruzione, non per progetto»*, e serve il giorno in cui il registro
    diventasse la tabella delle sessioni di un server vero.

    ⛔ Questo predicato quindi NON da' rosso se la riga manca: darebbe rosso a
       un codice giusto.  Da' rosso se la riga ESCE, perche' allora la mia
       lettura era sbagliata e il ramo e' raggiungibile — cioe' c'e' un modo di
       arrivare a `POSTO_OCCUPATO` con due nomi diversi, e QUELLO va guardato.
    """
    if not sf or sf.get("esito") != "letto":
        return _muto((sf or {}).get("esito", "non ho letto il registro"))
    if sf["negati"] > 0:
        return _no("⛔ la riga «SFRATTO NEGATO» E' USCITA, e `[R]` avevo letto "
                   "che non poteva: vuol dire che si arriva a POSTO_OCCUPATO "
                   "con due nomi diversi — «%s»"
                   % (sf.get("righe_negato") or [""])[0][:200])
    return _si("nessuna riga «SFRATTO NEGATO», come previsto `[R]`: il registro "
               "dei posti e' per NOME, quindi il ramo non e' raggiungibile — la "
               "protezione la fa la struttura, e il controllo esplicito resta "
               "come rete per il giorno in cui la struttura cambiera'")


def p6_i_predefiniti_non_cambiano_niente(lm, sf, stato, n, nome_profilo):
    """⛔ **L'INVARIANTE I6.**  Senza `--linea-morta` e con `--sfratto-ms 0` —
    cioe' **cosi' come il prodotto esce oggi** — tutto dev'essere identico a
    ieri: nessuno scatto, nessuno sfratto, e il profilo si comporta come nella
    griglia di `09-b76`.

    ⭐ Ed e' anche la prova che le due cure sono davvero SPENTE, non solo
       scritte: due righe d'avvio che lo dicono, e zero righe di scatto.
    """
    va, perche = cure_come_voglio(stato, linea_morta="spenta", sfratto_ms=0)
    if va is not True:
        return _muto("⚠ non giudico I6 su una configurazione che non e' quella "
                     "predefinita — %s" % perche)
    if not lm or lm.get("esito") != "letto":
        return _muto((lm or {}).get("esito", "non ho letto gli scatti"))
    if lm["scatti"] > 0 or lm.get("chiuse_dal_trasporto", 0) > 0:
        return _no("⛔ I6 VIOLATA: con la cura SPENTA sono uscite %d righe "
                   "`linea-morta` e %d chiusure dal trasporto"
                   % (lm["scatti"], lm.get("chiuse_dal_trasporto", 0)))
    if not sf or sf.get("esito") != "letto":
        return _muto((sf or {}).get("esito", "non ho letto lo sfratto"))
    if sf["sfratti"] > 0:
        return _no("⛔ I6 VIOLATA: con lo sfratto SPENTO c'e' stato uno "
                   "sfratto — «%s»" % (sf.get("righe_sfratto") or [""])[0][:180])
    atteso = GRIGLIA_B76.get(nome_profilo)
    if not atteso:
        return _si("nessuno scatto e nessuno sfratto con le cure spente "
                   "(⚠ «%s» non e' nella griglia di 09-b76: niente da "
                   "confrontare)" % nome_profilo)
    c = (n or {}).get("consegna") or {}
    fps = (n or {}).get("fps")
    if c.get("esito") != "misurato" or fps is None:
        return _muto("nessuno scatto e nessuno sfratto, ma non ho i numeri del "
                     "giro: senza, non posso dire che si comporti come nella "
                     "griglia di 09-b76")
    coda = ("%.2f fotogrammi/s · copertura %.2f · buco piu' lungo %.2f s "
            "(griglia 09-b76: %s)"
            % (fps, c["copertura"], c["buco_max_s"], atteso["perche"]))
    if atteso.get("consegna_si_ferma"):
        # ⛔ Su `raffica-forte` la griglia dice che la consegna SI FERMA: se qui
        #    non si fermasse, il prodotto sarebbe cambiato — e' un rosso a I6
        #    tanto quanto uno scatto.
        ferma = (c["copertura"] < B76.COPERTURA_MINIMA
                 or c["buco_max_s"] >= B76.BUCO_SCHERMO_FERMO_S)
        if not ferma:
            return _no("⛔ I6: con le cure spente «%s» NON si comporta come "
                       "nella griglia di 09-b76 — li' la consegna si ferma, qui "
                       "no.  %s" % (nome_profilo, coda))
        return _si("⭐ cure spente: zero scatti, zero sfratti, e «%s» si "
                   "comporta come nella griglia — %s" % (nome_profilo, coda))
    if not (atteso["fps_min"] <= fps <= atteso["fps_max"]):
        return _no("⛔ I6: con le cure spente «%s» da' %.2f fotogrammi/s, fuori "
                   "dalla griglia di 09-b76 (%.1f-%.1f).  %s"
                   % (nome_profilo, fps, atteso["fps_min"], atteso["fps_max"],
                      coda))
    if c["copertura"] < atteso["copertura_min"]:
        return _no("⛔ I6: con le cure spente «%s» ha copertura %.2f contro %.2f "
                   "della griglia.  %s"
                   % (nome_profilo, c["copertura"], atteso["copertura_min"], coda))
    return _si("⭐ cure spente: zero scatti, zero sfratti, e «%s» sta nella "
               "griglia di 09-b76 — %s" % (nome_profilo, coda))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL CONTROLLO POSITIVO — «come fa questo banco a sapere di saper vedere?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `PIANO.md` §0.3.4: *«un banco che non sa vedere il difetto che cerca non ha
#    diritto al verde»*.  ⇒ Qui si fabbricano righe e numeri e si controlla che
#    i sei predicati diano quel che e' scritto PRIMA — verde, rosso **e muto**.
#
# ⭐ E i casi non passano numeri gia' pronti: fabbricano il TESTO DEL REGISTRO e
#    lo fanno passare dalle STESSE riduzioni che girano sui giri veri.  Un
#    inganno che vivesse nella riduzione verrebbe visto.

# ⛔ Il formato e' quello di `src/webtransport.c`, `linea_morta_scatta()`, campo
#    per campo e NELL'ORDINE: `_certifica_contratto()` lo rilegge dal sorgente e
#    confronta, cosi' il giorno che il prodotto cambia la riga il banco lo dice
#    invece di leggere il campo sbagliato in silenzio.
CAMPI_LM = ["causa", "persi", "spediti", "permille", "soglia_permille",
            "finestra_ms", "finestre", "minimo_pacchetti", "silenzio_ms",
            "soglia_silenzio_ms", "prove", "minimo_prove", "cwnd", "srtt_us",
            "giudizio"]


def _fab_lm(ora="21:14:02.123", causa="perdita", persi=31, spediti=412,
            permille=75, soglia=LM_PERMILLE, finestra_ms=1004, finestre=2,
            silenzio_ms=1300, prove=9, cwnd=8948, srtt_us=61230,
            giudizio="⛔ la linea e' MORTA: la perdita ha superato la soglia"):
    """Una riga `linea-morta` come la scrive il prodotto, campo per campo."""
    return ("%s wt      linea-morta [192.168.0.2]:50875 causa=%s persi=%d "
            "spediti=%d permille=%d soglia_permille=%d finestra_ms=%d "
            "finestre=%d/%d minimo_pacchetti=%d silenzio_ms=%d "
            "soglia_silenzio_ms=%d prove=%d minimo_prove=%d cwnd=%d srtt_us=%d "
            "giudizio=%s"
            % (ora, causa, persi, spediti, permille, soglia, finestra_ms,
               finestre, LM_FINESTRE, LM_MIN_PACCHETTI, silenzio_ms,
               LM_SILENZIO_S * 1000, prove, LM_MIN_PROVE, cwnd, srtt_us,
               giudizio))


def _fab_chiusa(ora="21:14:02.124"):
    return ("%s quic    ⛔ [192.168.0.2]:50875: LINEA MORTA — la connessione "
            "QUIC si chiude (un solo CONNECTION_CLOSE, spedito)." % ora)


def _fab_rq(da_ms=1002, persi_d=3, spediti_d=410):
    return ("21:14:00.000 wt      rete-quic [192.168.0.2]:50875 da_ms=%d "
            "persi=7 persi_d=%d byte_persi=9856 byte_persi_d=4224 spediti=48210 "
            "spediti_d=%d byte_spediti=59284410 ricevuti=3011 ricevuti_d=61 "
            "scartati=0 scartati_d=0 cwnd=48000 cwnd_left=0 ssthresh=32000 "
            "involo=47180 srtt_us=41230 latest_us=52980 rttvar_us=11400 "
            "min_rtt_us=22100 coda_rete_us=19130 pto_us=132000 dgram_persi=0 "
            "dgram_persi_d=0 dgram_ok=99 dgram_falsi=1 dgram_falsi_d=0 "
            "giudizio=-- niente da segnalare" % (da_ms, persi_d, spediti_d))


def _fab_sfratto(ora="21:14:31.500", muto=15412, chi=UTENTE):
    return ("%s rcp     ⭐ SFRATTO per silenzio: %d ms senza un PACCHETTO da "
            "[192.168.0.2]:50875 (soglia 15000 ms) — il posto di %s va al "
            "client che sta arrivando da [192.168.0.2]:50999 (§4.4: chi tace e' "
            "staccato; §8.2 NON e' violata) (posti occupati adesso: 0)"
            % (ora, muto, chi))


def _fab_rifiuto(ora="21:14:20.100", muto=4020, acceso=True):
    return ("%s rcp     posto NEGATO a %s da [192.168.0.2]:50999: lo occupa un "
            "altro client di questo stesso utente (occupati: 1) — quell'occupante "
            "ha dato un segno di vita %d ms fa, e lo sfratto %s"
            % (ora, UTENTE, muto,
               "NON e' scattato" if acceso else "e' SPENTO (--sfratto-ms)"))


def _fab_preso(ora="21:14:31.510", chi=UTENTE):
    return ("%s rcp     posto PRESO da %s via [192.168.0.2]:50999 "
            "(occupati adesso: 1)" % (ora, chi))


def _fab_negato(ora="21:14:20.100"):
    return ("%s rcp     ⛔ SFRATTO NEGATO: il posto risulta di «%s» e a chiedere "
            "e' «%s» — fra utenti diversi non si sfratta MAI, e questo registro "
            "non dovrebbe nemmeno poterlo proporre" % (ora, UTENTE, UTENTE2))


def _fab_campioni(secondi=60.0, passo=0.1, periodo=5.0, byte_giro=130,
                  pacchetti_giro=2, fondo_byte_s=0.0, fondo_pkt_s=0.0):
    """Campioni del contatore: un «giro» di PING ogni `periodo` secondi.

    ⭐ Fabbricare i campioni e non i numeri e' quel che rende vero il controllo:
       la riduzione deve saper trovare gli EVENTI dentro un contatore che sale a
       scatti, ed e' l'unica cosa che sa dire se i PING sono passati a 5 s.
    """
    campioni, b, p, t, resto = [], 1000, 10, 0.0, 0.0
    prossimo = periodo
    while t < secondi:
        if t >= prossimo:
            b += byte_giro
            p += pacchetti_giro
            prossimo += periodo
        # ⛔ Il fondo muove ANCHE i pacchetti, o non e' un fondo: e' proprio
        #    quello che rende invisibili gli eventi, ed e' il caso da provare.
        b += int(fondo_byte_s * passo)
        resto += fondo_pkt_s * passo
        p += int(resto)
        resto -= int(resto)
        campioni.append([round(t, 3), b, p])
        t += passo
    return campioni


def _certifica_contratto():
    """⛔⛔ IL CONTRATTO SUL TESTO SI PROVA SUL TESTO — e contro il SORGENTE.

    La riga `linea-morta` e' un contratto: se il prodotto le cambia l'ordine dei
    campi, un banco che facesse `split('=')` leggerebbe il campo sbagliato
    **senza accorgersene**.  ⇒ Qui l'ordine dei campi si rilegge da
    `src/webtransport.c` e si confronta con quello che questo banco si aspetta.

    ⚠ Se il sorgente non c'e' (il banco gira altrove), questo controllo TACE:
      «non ho guardato» non e' «va bene».
    """
    perc = os.path.join(os.path.dirname(QUI), "src", "webtransport.c")
    if not os.path.exists(perc):
        return None, "⚠ «%s» non c'e': non ho riletto il contratto dal sorgente" % perc
    testo = open(perc, encoding="utf-8", errors="replace").read()
    i = testo.find('"linea-morta %s causa=')
    if i < 0:
        return (False, "⛔ in `webtransport.c` non trovo piu' la riga di formato "
                       "che comincia con «linea-morta %s causa=»: il contratto "
                       "e' cambiato, e questo banco leggerebbe campi che non ci "
                       "sono piu'")
    # ⛔ Il formato e' spezzato su piu' letterali C attaccati: si ricuciono.
    pezzi, j = [], i
    while True:
        a = testo.find('"', j)
        if a < 0:
            break
        b = testo.find('"', a + 1)
        if b < 0:
            break
        pezzo = testo[a + 1:b]
        pezzi.append(pezzo)
        j = b + 1
        # la fine del formato: il letterale che contiene `giudizio=`
        if "giudizio=" in pezzo:
            break
        # e se fra un letterale e l'altro c'e' altro che spazi, e' finita
        if testo[b + 1:testo.find('"', b + 1) if testo.find('"', b + 1) > 0
                 else b + 1].strip() not in ("",):
            break
    fmt = "".join(pezzi)
    nomi = [x.split("=")[0] for x in fmt.split() if "=" in x]
    if nomi != CAMPI_LM:
        return (False, "⛔ IL CONTRATTO E' CAMBIATO: il sorgente scrive i campi "
                       "%s, questo banco si aspetta %s" % (nomi, CAMPI_LM))
    if not fmt.rstrip().endswith("giudizio=%s"):
        return (False, "⛔ `giudizio=` non e' piu' l'ULTIMO campo: il valore "
                       "contiene spazi, e un campo dopo di lui verrebbe letto "
                       "dentro il giudizio")
    return (True, "⭐ il contratto e' quello: %d campi nell'ordine, e `giudizio=` "
                  "ultimo — riletto da `src/webtransport.c`" % len(nomi))


def importa_finto():
    """⛔ Il controllo positivo non tocca la macchina, ma ha bisogno delle
       SOGLIE di `09-b76` (`COPERTURA_MINIMA`, `BUCO_SCHERMO_FERMO_S`): quelle
       sono il metro con cui la prova 6 dice «si comporta come nella griglia».

    ⚠ Si importa il modulo e basta, **senza** agganciargli la rete: `RETE` resta
      `None` e nessuna funzione che parli con la macchina e' raggiungibile da
      qui — e' la stessa forma di `09-b76.importa_finto()`.
    ⛔ E le due soglie si RILEGGONO da li' invece di ricopiarle: due copie della
       stessa soglia in due file sono due soglie che divergono.
    """
    global B76
    if B76 is None:
        B76 = _carica("b76rete", os.path.join(QUI, "09-b76-rete-cattiva.py"))


def certifica():
    print("⭐ CERTIFICAZIONE DEL BANCO DELLE DUE CURE — l'atteso e' scritto PRIMA\n")
    print("   ⛔ Nessun contatto con la macchina di prova: qui si prova lo "
          "STRUMENTO,\n      non il prodotto.\n")
    importa_finto()
    verde = True
    casi = []

    def caso(nome, atteso, avuto):
        """`atteso` e' `True`/`False`/`None` — verde, rosso, muto."""
        passa, perche = avuto
        ok = (passa is atteso)
        casi.append({"caso": nome, "atteso": atteso, "avuto": passa,
                     "perche": perche})
        (_ok if ok else _ko)("%s → atteso %s, avuto %s%s"
                             % (nome, atteso, passa,
                                "" if ok else "  ⛔ «%s»" % perche[:150]))
        return ok

    # ── 0 · il contratto sul testo, riletto dal sorgente ───────────────────
    _log("0 · IL CONTRATTO DELLA RIGA `linea-morta`, riletto da `src/`")
    passa, perche = _certifica_contratto()
    (_ok if passa else (_dub if passa is None else _ko))(perche)
    if passa is False:
        verde = False

    # ── 1 · le riduzioni, su TESTO fabbricato ─────────────────────────────
    _log("1 · LE RIDUZIONI — testo fabbricato dentro le stesse funzioni dei "
         "giri veri")
    lm = riduci_linea_morta([_fab_lm()])
    ok = (lm["esito"] == "letto" and lm["scatti"] == 1
          and lm["causa"] == "perdita" and lm["permille"] == 75
          and lm["spediti"] == 412 and lm["persi"] == 31
          and lm["soglia_permille"] == LM_PERMILLE
          and lm["righe"][0]["finestre"] == "2/2"
          and lm["giudizio"].startswith("⛔ la linea e' MORTA")
          and abs(lm["ora_primo"] - (21 * 3600 + 14 * 60 + 2.123)) < 1e-6)
    (_ok if ok else _ko)("la riga `linea-morta` si legge campo per campo, "
                         "`giudizio=` compreso (con gli spazi): %s"
                         % json.dumps({k: lm.get(k) for k in
                                       ("causa", "persi", "spediti", "permille",
                                        "silenzio_ms", "prove")},
                                      ensure_ascii=False))
    verde = verde and ok

    lm0 = riduci_linea_morta([])
    lmx = riduci_linea_morta([], letto=False)
    ok = (lm0["esito"] == "letto" and lm0["scatti"] == 0
          and lmx["esito"] != "letto")
    (_ok if ok else _ko)("⛔⛔ «zero scatti» e «non ho letto» NON hanno la stessa "
                         "faccia: «%s» contro «%s»"
                         % (lm0["esito"], lmx["esito"][:60]))
    verde = verde and ok

    sf = riduci_sfratto([_fab_rifiuto(), _fab_rifiuto(), _fab_sfratto(),
                         _fab_preso()])
    ok = (sf["sfratti"] == 1 and sf["rifiuti"] == 2 and sf["presi"] == 1
          and sf["muto_ms"] == 15412 and sf["sfrattato"] == UTENTE
          and sf["negati"] == 0 and sf["ultimo_rifiuto_muto_ms"] == 4020
          and sf["sfratto_dice"] == "NON e' scattato")
    (_ok if ok else _ko)("le tre marche dello sfratto si leggono: %d sfratti, "
                         "%d rifiuti, muto %s ms, sfrattato «%s», la riga del "
                         "rifiuto dice «%s»"
                         % (sf["sfratti"], sf["rifiuti"], sf.get("muto_ms"),
                            sf.get("sfrattato"), sf.get("sfratto_dice")))
    verde = verde and ok

    sf2 = riduci_sfratto([_fab_rifiuto(acceso=False), _fab_negato()])
    ok = (sf2["negati"] == 1 and sf2["sfratti"] == 0
          and sf2["sfratto_dice"] == "SPENTO")
    (_ok if ok else _ko)("la riga «SFRATTO NEGATO» e il rifiuto a sfratto SPENTO "
                         "si distinguono: negati %d, dice «%s»"
                         % (sf2["negati"], sf2.get("sfratto_dice")))
    verde = verde and ok

    # ⭐ Le finestre dichiarate: due finestre di fila sopra soglia dentro un
    #    mucchio di finestre buone, e le guardie della cura che scartano quelle
    #    troppo corte o troppo vuote.
    righe = ([_fab_rq(persi_d=2, spediti_d=400)] * 20
             + [_fab_rq(persi_d=30, spediti_d=400)] * 2
             + [_fab_rq(persi_d=2, spediti_d=400)] * 20
             + [_fab_rq(persi_d=90, spediti_d=100)]      # ⛔ pochi pacchetti
             + [_fab_rq(persi_d=90, spediti_d=400, da_ms=400)])  # ⛔ finestra corta
    fin = finestre_dichiarate(righe)
    ok = (fin["esito"] == "letto" and fin["finestre_valide"] == 42
          and fin["permille_max"] == 75 and fin["sopra_soglia"] == 2
          and fin["coppie_sopra_soglia"] == 1
          and fin["fila_massima_sopra_soglia"] == 2)
    (_ok if ok else _ko)("⛔ le GUARDIE della cura si applicano: 44 righe, %d "
                         "finestre valide (le due sotto %d pacchetti / sotto %d "
                         "ms sono scartate), max %d‰, %d coppie di fila sopra "
                         "soglia" % (fin["finestre_valide"], LM_MIN_PACCHETTI,
                                     LM_FINESTRA_MS, fin["permille_max"],
                                     fin["coppie_sopra_soglia"]))
    verde = verde and ok

    fin0 = finestre_dichiarate([_fab_rq(persi_d=1, spediti_d=10)] * 30)
    ok = fin0["esito"].startswith("NON GIUDICO")
    (_ok if ok else _ko)("⭐ e se NESSUNA finestra supera le guardie, la "
                         "ricostruzione si RIFIUTA invece di dire «zero»: «%s»"
                         % fin0["esito"][:110])
    verde = verde and ok

    oro = riduci_orologio(_fab_campioni(periodo=5.0))
    ok = (oro["esito"] == "misurato" and abs(oro["intervallo_mediano_s"] - 5.0) < 0.3
          and oro["eventi"] >= 10)
    (_ok if ok else _ko)("l'orologio del filo trova i giri di PING dentro il "
                         "contatore: %d eventi, intervallo mediano %s s, %.4f "
                         "kbit/s, %s byte a giro"
                         % (oro["eventi"], oro.get("intervallo_mediano_s"),
                            oro["kbit_s"], oro.get("byte_per_evento")))
    verde = verde and ok

    oro10 = riduci_orologio(_fab_campioni(periodo=10.0))
    ok = (oro10["esito"] == "misurato"
          and abs(oro10["intervallo_mediano_s"] - 10.0) < 0.3)
    (_ok if ok else _ko)("⭐ e sa distinguere 10 s da 5: intervallo mediano %s s"
                         % oro10.get("intervallo_mediano_s"))
    verde = verde and ok

    oroF = riduci_orologio(_fab_campioni(periodo=5.0, fondo_byte_s=180000,
                                         fondo_pkt_s=190.0))
    ok = (oroF["esito"] == "misurato" and oroF["intervallo_mediano_s"] is None
          and "NON e' ferma" in oroF.get("perche_niente_intervallo", ""))
    (_ok if ok else _ko)("⛔ e su una sessione che NON e' ferma (fondo audio) si "
                         "rifiuta di dare un intervallo invece di inventarne "
                         "uno: «%s»" % oroF.get("perche_niente_intervallo", "")[:90])
    verde = verde and ok

    ok = (abs(dt_registro("00:00:01.500 x", "23:59:59.500 x") - 2.0) < 1e-6
          and dt_registro("nessuna ora", "23:59:59.500 x") is None)
    (_ok if ok else _ko)("l'orologio del registro scavalca la mezzanotte, e "
                         "«non lo so» non e' «zero secondi»")
    verde = verde and ok

    # ── 2 · i sei predicati: VERDE, ROSSO e MUTO ──────────────────────────
    _log("2 · I SEI PREDICATI — e ognuno deve saper dare rosso, non solo verde")

    testimone_vivo = {"aperta": True, "cliente_attaccato": True,
                      "cliente_staccato": False, "congedi": []}
    testimone_caduto = {"aperta": True, "cliente_attaccato": False,
                        "cliente_staccato": True, "caduta": "la sessione e' caduta",
                        "congedi": []}
    giro_buono = {"fps": 9.1, "consegna": {"esito": "misurato", "copertura": 1.0,
                                           "buco_max_s": 0.37}}
    giro_fiacco = {"fps": 1.2, "consegna": {"esito": "misurato", "copertura": 0.4,
                                            "buco_max_s": 6.0}}

    _inf("P1 · ⛔⛔ il falso positivo")
    verde &= caso("P1 verde · zero scatti su una linea che regge", True,
                  p1_niente_falso_positivo(lm0, testimone_vivo, giro_buono, 10))
    verde &= caso("P1 ROSSO · uno scatto su una linea che regge", False,
                  p1_niente_falso_positivo(lm, testimone_vivo, giro_buono, 10))
    verde &= caso("P1 muto · zero scatti ma la linea non reggeva", None,
                  p1_niente_falso_positivo(lm0, testimone_vivo, giro_fiacco, 10))
    verde &= caso("P1 muto · zero scatti ma il cliente e' caduto per altro", None,
                  p1_niente_falso_positivo(lm0, testimone_caduto, giro_buono, 10))
    verde &= caso("P1 muto · il registro non l'ho letto", None,
                  p1_niente_falso_positivo(lmx, testimone_vivo, giro_buono, 10))

    _inf("P1c · ⛔⛔ il CONTROLLO: la stessa linea a cure spente")
    giro_regge = {"fps": 9.1, "consegna": {"esito": "misurato", "copertura": 0.99,
                                           "buco_max_s": 0.42,
                                           "consegna_fino_a_s": 599.8}}
    giro_non_regge = {"fps": 1.1, "consegna": {"esito": "misurato",
                                               "copertura": 0.30,
                                               "buco_max_s": 40.0,
                                               "consegna_fino_a_s": 22.0}}
    giro_si_ferma = {"fps": 8.0, "consegna": {"esito": "misurato",
                                              "copertura": 0.40,
                                              "buco_max_s": 30.0,
                                              "consegna_fino_a_s": 240.0}}
    verde &= caso("P1c verde · a cure spente la stessa linea regge 10 minuti",
                  True, p1c_la_linea_regge_a_cura_spenta(testimone_vivo,
                                                         giro_regge, 10, 1))
    verde &= caso("P1c ROSSO · ⛔ cade anche a cure spente: il rosso della 1 non "
                  "e' un falso positivo", False,
                  p1c_la_linea_regge_a_cura_spenta(testimone_caduto,
                                                   giro_regge, 10, 1))
    verde &= caso("P1c ROSSO · a cure spente il ritmo e' sotto il pavimento del "
                  "banco", False,
                  p1c_la_linea_regge_a_cura_spenta(testimone_vivo,
                                                   giro_non_regge, 10, 1))
    verde &= caso("P1c ROSSO · a cure spente la consegna si ferma lo stesso",
                  False, p1c_la_linea_regge_a_cura_spenta(testimone_vivo,
                                                          giro_si_ferma, 10, 1))
    verde &= caso("P1c muto · non ho i numeri del giro di controllo", None,
                  p1c_la_linea_regge_a_cura_spenta(testimone_vivo,
                                                   {"fps": None}, 10, 1))

    _inf("P1b · ⛔ il falsificatore: la soglia contro la frazione DICHIARATA")
    sonda_casa = {"esito": "misurato", "persi_pc": 1.71, "raffica_media": 1.02}
    fin_buone = finestre_dichiarate([_fab_rq(persi_d=7, spediti_d=400)] * 200)
    fin_toccata = finestre_dichiarate([_fab_rq(persi_d=7, spediti_d=400)] * 199
                                      + [_fab_rq(persi_d=25, spediti_d=400)])
    fin_sfondata = finestre_dichiarate([_fab_rq(persi_d=7, spediti_d=400)] * 198
                                       + [_fab_rq(persi_d=25, spediti_d=400)] * 2)
    verde &= caso("P1b verde · la dichiarata resta sotto soglia", True,
                  p1b_soglia_sopra_la_dichiarata(fin_buone, sonda_casa))
    verde &= caso("P1b ROSSO · due finestre di fila sopra soglia", False,
                  p1b_soglia_sopra_la_dichiarata(fin_sfondata, sonda_casa))
    verde &= caso("P1b ROSSO · una finestra sola tocca la soglia (il margine "
                  "dichiarato non c'e')", False,
                  p1b_soglia_sopra_la_dichiarata(fin_toccata, sonda_casa))
    verde &= caso("P1b muto · troppe poche finestre valide", None,
                  p1b_soglia_sopra_la_dichiarata(
                      finestre_dichiarate([_fab_rq(persi_d=7, spediti_d=400)] * 5),
                      sonda_casa))

    _inf("P2 · lo scatto vero")
    sonda_raffica = {"esito": "misurato", "persi_pc": 11.10, "raffica_media": 5.5}
    lm_p = riduci_linea_morta([_fab_lm(causa="perdita")])
    lm_p["chiuse_dal_trasporto"] = 1
    lm_p_senza_filo = riduci_linea_morta([_fab_lm(causa="perdita")])
    lm_p_senza_filo["chiuse_dal_trasporto"] = 0
    lm_s = riduci_linea_morta([_fab_lm(causa="silenzio", permille=0,
                                       silenzio_ms=10004, prove=3)])
    lm_s["chiuse_dal_trasporto"] = 1
    lm0["chiuse_dal_trasporto"] = 0
    verde &= caso("P2 verde · scattata con causa=perdita e il filo e' caduto", True,
                  p2_scatta_sulla_raffica(lm_p, sonda_raffica, 18.4))
    verde &= caso("P2 ROSSO · non e' scattata su una linea che non si sa servire",
                  False, p2_scatta_sulla_raffica(lm0, sonda_raffica, None))
    verde &= caso("P2 ROSSO · scattata per il motivo sbagliato", False,
                  p2_scatta_sulla_raffica(lm_s, sonda_raffica, 12.0))
    verde &= caso("P2 ROSSO · decisa ma il filo NON e' caduto", False,
                  p2_scatta_sulla_raffica(lm_p_senza_filo, sonda_raffica, 18.4))
    verde &= caso("P2 muto · il guasto non e' stato messo", None,
                  p2_scatta_sulla_raffica(lm_p, sonda_casa, 18.4))
    verde &= caso("P2 muto · la sonda non ha misurato", None,
                  p2_scatta_sulla_raffica(lm_p, None, 18.4))

    _inf("P3 · il silenzio")
    lm_presto = riduci_linea_morta([_fab_lm(causa="silenzio", silenzio_ms=6100)])
    lm_presto["chiuse_dal_trasporto"] = 1
    lm_tardi = riduci_linea_morta([_fab_lm(causa="silenzio", silenzio_ms=21000)])
    lm_tardi["chiuse_dal_trasporto"] = 1
    verde &= caso("P3 verde · scattata a 10,0 s con causa=silenzio", True,
                  p3_scatta_sul_silenzio(lm_s, LM_SILENZIO_S * 1000))
    verde &= caso("P3 ROSSO · non e' scattata: il fantasma resta ai 30 s", False,
                  p3_scatta_sul_silenzio(lm0, LM_SILENZIO_S * 1000))
    verde &= caso("P3 ROSSO · ⛔ scattata PRIMA della soglia (un client vivo e "
                  "fermo verrebbe buttato fuori)", False,
                  p3_scatta_sul_silenzio(lm_presto, LM_SILENZIO_S * 1000))
    verde &= caso("P3 ROSSO · scattata molto dopo la soglia (forma E1)", False,
                  p3_scatta_sul_silenzio(lm_tardi, LM_SILENZIO_S * 1000))
    verde &= caso("P3 ROSSO · scattata per perdita e non per silenzio", False,
                  p3_scatta_sul_silenzio(lm_p, LM_SILENZIO_S * 1000))
    verde &= caso("P3 muto · il registro non l'ho letto", None,
                  p3_scatta_sul_silenzio(lmx, LM_SILENZIO_S * 1000))

    _inf("P3b · il prezzo dichiarato dei PING")
    fermo_acceso = {"esito": "misurato", "kbit_s": 0.21, "pacchetti": 24,
                    "secondi": 60.0}
    fermo_spento = {"esito": "misurato", "kbit_s": 0.10, "pacchetti": 12,
                    "secondi": 60.0}
    fermo_caro = {"esito": "misurato", "kbit_s": 1.30, "pacchetti": 160,
                  "secondi": 60.0}
    audio_acceso = {"esito": "misurato", "kbit_s": 1412.0, "pacchetti": 11800,
                    "secondi": 60.0}
    audio_spento = {"esito": "misurato", "kbit_s": 1409.0, "pacchetti": 11790,
                    "secondi": 60.0}
    verde &= caso("P3b verde · la differenza sta nel dichiarato", True,
                  p3b_costo_dei_ping(fermo_acceso, fermo_spento))
    verde &= caso("P3b ROSSO · i PING costano piu' del dichiarato", False,
                  p3b_costo_dei_ping(fermo_caro, fermo_spento))
    verde &= caso("P3b muto · ⛔ il fondo e' piu' grosso del bersaglio", None,
                  p3b_costo_dei_ping(audio_acceso, audio_spento))
    verde &= caso("P3b muto · una delle due misure non c'e'", None,
                  p3b_costo_dei_ping(fermo_acceso, {"esito": "NON GIUDICO"}))

    _inf("P4 · lo sfratto")
    sf_ok = riduci_sfratto([_fab_rifiuto(), _fab_sfratto(), _fab_preso()])
    sf_presto = riduci_sfratto([_fab_sfratto(muto=9000), _fab_preso()])
    sf_niente = riduci_sfratto([_fab_rifiuto()] * 11 + [_fab_preso()])
    verde &= caso("P4 verde · il posto torna libero a ~15 s", True,
                  p4_lo_sfratto_libera_il_posto(sf_ok, SFRATTO_CONSIGLIATO_MS,
                                                15.6, 30.5))
    verde &= caso("P4 ROSSO · nessuno sfratto, si aspetta il silenzio di §5.3",
                  False,
                  p4_lo_sfratto_libera_il_posto(sf_niente, SFRATTO_CONSIGLIATO_MS,
                                                30.5, 30.5))
    verde &= caso("P4 ROSSO · ⛔ sfrattato PRIMA della soglia (I2 spenta)", False,
                  p4_lo_sfratto_libera_il_posto(sf_presto, SFRATTO_CONSIGLIATO_MS,
                                                9.2, 30.5))
    verde &= caso("P4 ROSSO · sfrattato, ma il posto ci mette lo stesso 28 s",
                  False,
                  p4_lo_sfratto_libera_il_posto(sf_ok, SFRATTO_CONSIGLIATO_MS,
                                                28.0, 30.5))
    verde &= caso("P4 muto · non so quando il posto sia stato ripreso", None,
                  p4_lo_sfratto_libera_il_posto(sf_ok, SFRATTO_CONSIGLIATO_MS,
                                                None, 30.5))

    _inf("P5 · ⛔ due utenti diversi")
    sf_due_ok = riduci_sfratto([_fab_preso(chi=UTENTE), _fab_preso(chi=UTENTE2)])
    sf_buco = riduci_sfratto([_fab_sfratto(chi=UTENTE), _fab_preso(chi=UTENTE2)])
    verde &= caso("P5 verde · nessuno sfratto e il secondo utente entra", True,
                  p5_fra_utenti_diversi_non_si_sfratta(sf_due_ok, True,
                                                       UTENTE, UTENTE2))
    verde &= caso("P5 ROSSO · ⛔⛔ sfratto fra utenti diversi = buco di sicurezza",
                  False,
                  p5_fra_utenti_diversi_non_si_sfratta(sf_buco, True,
                                                       UTENTE, UTENTE2))
    verde &= caso("P5 muto · nessuno sfratto, ma il secondo non e' entrato", None,
                  p5_fra_utenti_diversi_non_si_sfratta(sf_due_ok, False,
                                                       UTENTE, UTENTE2))
    verde &= caso("P5b verde · la riga «SFRATTO NEGATO» NON esce (previsto `[R]`)",
                  True, p5b_la_riga_del_negato(sf_due_ok))
    verde &= caso("P5b ROSSO · la riga ESCE, cioe' la mia lettura era sbagliata",
                  False, p5b_la_riga_del_negato(riduci_sfratto([_fab_negato()])))

    _inf("P6 · ⛔ i predefiniti non cambiano niente (I6)")
    spento = {"esito": "letto", "linea_morta": "spenta", "permille": None,
              "silenzio_s": None, "sfratto_ms": 0, "righe": []}
    acceso = {"esito": "letto", "linea_morta": "accesa", "permille": LM_PERMILLE,
              "silenzio_s": LM_SILENZIO_S, "sfratto_ms": SFRATTO_CONSIGLIATO_MS,
              "righe": []}
    sf_vuoto = riduci_sfratto([_fab_preso()])
    giro_casa = {"fps": 9.1, "consegna": {"esito": "misurato", "copertura": 0.96,
                                          "buco_max_s": 0.42}}
    giro_casa_fuori = {"fps": 22.0, "consegna": {"esito": "misurato",
                                                 "copertura": 1.0,
                                                 "buco_max_s": 0.1}}
    giro_raffica = {"fps": 2.1, "consegna": {"esito": "misurato", "copertura": 0.28,
                                             "buco_max_s": 14.26}}
    giro_raffica_sana = {"fps": 30.0, "consegna": {"esito": "misurato",
                                                   "copertura": 1.0,
                                                   "buco_max_s": 0.2}}
    verde &= caso("P6 verde · cure spente, «casa-cattiva» come nella griglia b76",
                  True, p6_i_predefiniti_non_cambiano_niente(
                      lm0, sf_vuoto, spento, giro_casa, "casa-cattiva"))
    verde &= caso("P6 verde · cure spente, «raffica-forte» si ferma come li'",
                  True, p6_i_predefiniti_non_cambiano_niente(
                      lm0, sf_vuoto, spento, giro_raffica, "raffica-forte"))
    verde &= caso("P6 ROSSO · ⛔ I6: la cura e' spenta e ha scattato lo stesso",
                  False, p6_i_predefiniti_non_cambiano_niente(
                      lm_p, sf_vuoto, spento, giro_casa, "casa-cattiva"))
    verde &= caso("P6 ROSSO · ⛔ I6: lo sfratto e' spento e c'e' stato uno sfratto",
                  False, p6_i_predefiniti_non_cambiano_niente(
                      lm0, sf_ok, spento, giro_casa, "casa-cattiva"))
    verde &= caso("P6 ROSSO · il profilo esce dalla griglia di 09-b76", False,
                  p6_i_predefiniti_non_cambiano_niente(
                      lm0, sf_vuoto, spento, giro_casa_fuori, "casa-cattiva"))
    verde &= caso("P6 ROSSO · «raffica-forte» NON si ferma piu': il prodotto e' "
                  "cambiato", False, p6_i_predefiniti_non_cambiano_niente(
                      lm0, sf_vuoto, spento, giro_raffica_sana, "raffica-forte"))
    verde &= caso("P6 muto · il server NON era coi predefiniti", None,
                  p6_i_predefiniti_non_cambiano_niente(
                      lm0, sf_vuoto, acceso, giro_casa, "casa-cattiva"))

    # ── 3 · la guardia della configurazione ───────────────────────────────
    _log("3 · LA GUARDIA — «il server e' configurato come questa prova crede?»")
    verde &= caso("cure ACCESE come le voglio", True,
                  cure_come_voglio(acceso, linea_morta="accesa",
                                   permille=LM_PERMILLE,
                                   sfratto_ms=SFRATTO_CONSIGLIATO_MS))
    verde &= caso("⛔ muto se la linea morta risulta SPENTA quando la volevo "
                  "accesa", None,
                  cure_come_voglio(spento, linea_morta="accesa"))
    verde &= caso("⛔ muto se la soglia in vigore non e' quella che credo", None,
                  cure_come_voglio(acceso, linea_morta="accesa", permille=1))
    verde &= caso("⛔ muto se la riga d'avvio non l'ho letta", None,
                  cure_come_voglio({"esito": "⛔ NON HO LETTO nessuna riga"},
                                   linea_morta="accesa"))

    os.makedirs(FUORI, exist_ok=True)
    with open(os.path.join(FUORI, "09-b81-certifica.json"), "w") as f:
        json.dump(casi, f, ensure_ascii=False, indent=1)
    _log("ESITO DELLA CERTIFICAZIONE")
    _inf("%d casi, %d sbagliati · dettaglio in %s/09-b81-certifica.json"
         % (len(casi), len([c for c in casi if c["avuto"] is not c["atteso"]]),
            FUORI))
    if verde:
        _ok("⭐ tutti i predicati hanno fatto quel che era scritto prima — e "
            "ognuno ha dato rosso almeno una volta")
        return 0
    _ko("⛔ il banco NON sa vedere quel che cerca: non ha diritto al verde")
    return 1


# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE PARLA CON LA MACCHINA DI PROVA
# ═══════════════════════════════════════════════════════════════════════════
import contextlib   # noqa: E402  (sta qui perche' serve solo a questa meta')

CHI = "09-b81-linea-morta"
AFFITTO = 900        # ⛔ affitti CORTI e rinnovati: altri agenti sono in coda


def vicine():
    """⛔ Le porte che NON sono mie: si CONTANO prima e dopo, non si toccano."""
    fuori = []
    for p in VICINE:
        rc, o, _ = root("bash -c \"ss -uln 2>/dev/null | grep -c ':%s ' || true\"" % p)
        fuori.append("%s:%s" % (p, o.strip()))
    return " ".join(fuori)


def preparati():
    """I copioni sulla macchina, e la porta della sonda scelta ADESSO.

    ⛔ La porta della sonda non puo' essere fissa: mentre giro, un altro agente
       puo' accendere un server su quella che avevo visto libera (`09-b76`).
    """
    if not B76.spedisci_sonda():
        _ko("i copioni della sonda / del lettore non si sono scritti in %s" % LAV)
        return False
    if not B76.scrivi_sulla_macchina("09-b81-orologio.py", OROLOGIO):
        _ko("l'orologio del filo non si e' scritto in %s" % LAV)
        return False
    if B76.scegli_porta_sonda() is None:
        _ko("⛔ nessuna delle mie porte per la sonda e' libera: NON misuro, "
            "perche' senza sonda non so se il guasto sia stato messo")
        return False
    impronte = B78.spedisci()
    if impronte is None:
        _ko("`09-b78-apertura.py` / `01-b3-cliente.py` non sono arrivati nell'albero")
        return False
    _ok("copioni pronti · sonda sulla porta %d · %s"
        % (B76.PORTA_SONDA, " · ".join(impronte)))
    _inf("porte NON mie (si contano, non si toccano): %s" % vicine())
    return True


def accendi_server(opzioni, perche):
    """⛔ Riaccende il MIO server (unita' `%s`) con quelle opzioni, e POI
       rilegge dalla riga d'avvio che le abbia davvero prese.

    ⚠ Un'opzione battuta attraverso `ssh` → `sudo` → `systemd-run` → `bash -lc`
      ha quattro modi di perdersi per strada, e nessuno dei quattro da' errore:
      da' un server che gira coi predefiniti mentre il banco crede di misurare
      una cura accesa.
    """ % UNITA
    _log("IL SERVER SI RIACCENDE — %s" % perche)
    _inf("opzioni: %s" % (opzioni or "(nessuna: i predefiniti, cioe' I6)"))
    amb = dict(os.environ)
    amb["OPZIONI_SERVER"] = opzioni
    amb["UNITA"] = UNITA
    p = subprocess.run(["bash", os.path.join(QUI, "09-b81-terreno.sh"), "accendi"],
                       env=amb, capture_output=True, timeout=420)
    testo = (p.stdout + p.stderr).decode("utf-8", "replace")
    for r in testo.splitlines():
        if re.search(r"server \d+ sulla porta|NO |non e' partito", r):
            _inf(r.strip()[:180])
    if p.returncode != 0:
        _ko("⛔ il server non e' ripartito: %s" % testo[-400:])
        return False
    stato = stato_delle_cure()
    _inf("il server dice di se': linea morta %s (%s‰, %s s) · sfratto %s ms"
         % (stato["linea_morta"], stato["permille"], stato["silenzio_s"],
            stato["sfratto_ms"]))
    # ⛔ Il palco e il monitor nascono col PRIMO cliente: senza, la scena non
    #    saprebbe dove disegnare (`09-b70.innesca_sessione`).
    if not B70.innesca_sessione():
        _ko("la sessione d'innesco non si apre: il palco non c'e'")
        return False
    _ok("server riacceso e palco innescato")
    return True


@contextlib.contextmanager
def rete_guasta(regole, previsti_s, attesa=1800):
    """⛔ Il lucchetto, il guardiano e il `netem`, presi e resi INSIEME.

    · il lucchetto perche' il `netem` su `lo` e' uno solo per tutta la macchina,
      e due banchi che la guastano insieme non danno un rosso: danno un numero
      plausibile (`LEZIONI.md` §1.26);
    · il guardiano perche' la rete deve tornare com'era **anche se muoio**;
    · i filtri `u32` sulla sola %d, e `enp7s0` non si tocca MAI.
    """ % PORTA
    LUC.prendi(CHI, secondi=AFFITTO, attesa=attesa)
    RETE.guardiano_arma(min(3600, previsti_s + 600))
    messa = False
    try:
        ok, q = RETE.stringi(regole)
        if not ok:
            raise SystemExit("⛔ tc ha rifiutato la regola: %s" % q)
        messa = True
        B76.filtri_sonda()
        riletta = B76.regola_riletta()
        # ⛔ La regola si RILEGGE: `tc qdisc change` e' appiccicoso, e `[M]` 23
        #    ago 2026 si e' portato dietro un `reorder` per quattro profili.
        passa, perche = B76.controlla_regola([x for x in regole if x != "limit"
                                              and not x.isdigit()], riletta)
        (_ok if passa else _ko)("la regola: %s" % perche)
        if not passa:
            raise SystemExit("⛔ la regola installata non e' quella chiesta")
        yield riletta
    finally:
        _log("⛔ LA RETE SI RIMETTE COM'ERA")
        if not RETE.rimetti():
            _ko("⛔ la rete NON e' tornata com'era: si rimette a mano con «rimetti»")
        LUC.molla(CHI)
        if messa:
            _inf("porte NON mie dopo il giro: %s" % vicine())


def profilo(nome):
    """Le regole `netem` di un profilo di `09-b76`, prese da li' e non ricopiate."""
    for p in B76.PROFILI:
        if p[0] == nome:
            return p
    raise SystemExit("⛔ il profilo «%s» non e' in 09-b76" % nome)


def sonda(nome):
    """La sonda di `09-b76`, e il suo verdetto «il guasto e' stato messo?»."""
    s = B76.sonda_gira()
    B76.stampa_sonda(s)
    p = profilo(nome)
    passa, perche = B76.p_guasto_messo(nome, p[6], s)
    (_ok if passa else (_dub if passa is None else _ko))(
        "IL GUASTO E' STATO MESSO: %s" % perche)
    return s, (passa, perche)


def cliente_in_sottofondo(utente, parola_dentro, secondi, marca):
    """⛔ Il cliente DENTRO il chroot, staccato dalla mia `ssh`: dev'essere
       ancora vivo quando lo uccido, e `enter.sh` e' un `chroot` — quindi il
       processo si vede e si uccide dall'HOST col suo pid vero."""
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s --audio-codec pcm --video-codec h264 "
              "--adatta 1920x1080 --resta %d"
              % (DENTRO_ALB, IND, PORTA, utente, parola_dentro, secondi))
    root("bash /media/REMOTIX/enter.sh --root 'setsid nohup %s > %s/%s.log 2>&1 & "
         "sleep 0.5; echo lanciato'" % (dentro, DENTRO_LAV, marca), 180)


def cliente_pid(utente):
    """⛔ DUE guardie nel pattern, e sono tutt'e due contro lo stesso errore —
       uccidere il processo sbagliato:

       1. il `[.]` spezza il letterale, cosi' `pgrep` non trova SE STESSO (il
          suo pattern e' dentro la sua riga di comando);
       2. l'ancora `^python3` esclude il `bash -lc` che ha LANCIATO il cliente e
          che porta la stessa riga dentro la propria: ⚠ quello dura mezzo
          secondo, e se lo prendessi ucciderei un guscio gia' morto e
          crederei di aver ucciso il cliente — che invece resterebbe vivo, e
          la prova del silenzio misurerebbe un silenzio che non c'e'.
    """
    rc, out, _ = root("bash -c \"pgrep -f '^python3 .*b3-cliente[.]py .*--utente "
                      "%s ' | head -1\"" % utente)
    t = out.strip().splitlines()
    return int(t[0]) if t and t[0].isdigit() else None


def uccidi(pid):
    """⛔ `kill -9`, cosi' l'addio NON parte: per il server e' identico a un
       addio PERSO, ed e' il caso vero — l'utente a cui cade il filo.

    ⭐ E torna l'ora SUL SERVER, non sul portatile: e' l'unico orologio che si
       possa sottrarre a quello del registro senza portarci dentro l'`ssh`, il
       contenitore e la differenza fra due macchine.
    """
    if pid is None:
        return None
    rc, out, _ = root("bash -c \"kill -9 %d; date +'%%H:%%M:%%S.%%3N'\"" % pid)
    t = out.strip().splitlines()
    return (t[-1] + " x") if t else None


def ripulisci_clienti():
    """⚠ Fra una prova e l'altra: un cliente rimasto vivo terrebbe il posto, e
       la prova dopo misurerebbe la serratura del giro prima."""
    root("bash -c \"pkill -9 -f '^python3 .*b3-cliente[.]py .*--porta %d ' ; "
         "true\"" % PORTA)


def aspetta_riga(riga0, filtro, tetto=45.0, passo=1.0):
    scade = time.time() + tetto
    while True:
        r = leggi_registro(riga0, filtro)
        if r or time.time() >= scade:
            return r
        time.sleep(passo)


def stampa_finestre(fin):
    if fin.get("esito") != "letto":
        _dub("DICHIARATA  %s" % fin.get("esito"))
        return
    _inf("DICHIARATA  %d finestre valide su %d righe `rete-quic` · max %d‰ · "
         "p95 %d‰ · mediana %d‰ · media %.2f‰"
         % (fin["finestre_valide"], fin["righe"], fin["permille_max"],
            fin["permille_p95"], fin["permille_mediano"], fin["permille_medio"]))
    _inf("            sopra la soglia di %d‰: %d finestre · fila massima %d · "
         "coppie (= la condizione di scatto) %d · cumulativa %.2f‰ (%d persi su "
         "%d spediti)"
         % (fin["soglia_permille"], fin["sopra_soglia"],
            fin["fila_massima_sopra_soglia"], fin["coppie_sopra_soglia"],
            fin["cumulativa_permille"], fin["persi_totali"],
            fin["spediti_totali"]))
    _inf("            ⭐ la PARTENZA a parte: prime %d finestre max %s‰ · dopo: "
         "max %s‰, mediana %s‰, %s sopra soglia, fila massima %s, coppie %s"
         % (fin["prime_finestre"], fin["permille_max_prime"],
            fin["permille_max_dopo"], fin["permille_mediano_dopo"],
            fin["sopra_soglia_dopo"], fin["fila_massima_dopo"],
            fin["coppie_sopra_soglia_dopo"]))


def stampa_scatti(lm):
    if lm.get("esito") != "letto":
        _dub("SCATTI  %s" % lm.get("esito"))
        return
    _inf("SCATTI  %d riga/e `linea-morta` · %d chiusure dal trasporto"
         % (lm["scatti"], lm.get("chiuse_dal_trasporto", 0)))
    for r in lm.get("righe", [])[:3]:
        _inf("        %s" % r["riga"][:240])


def stampa_sfratto(sf):
    if sf.get("esito") != "letto":
        _dub("SFRATTO %s" % sf.get("esito"))
        return
    _inf("SFRATTO %d sfratti · %d NEGATI · %d rifiuti («posto NEGATO») · %d "
         "posti presi · l'ultimo rifiuto diceva «segno di vita %s ms fa» e lo "
         "sfratto «%s»"
         % (sf["sfratti"], sf["negati"], sf["rifiuti"], sf["presi"],
            sf.get("ultimo_rifiuto_muto_ms"), sf.get("sfratto_dice")))
    for r in (sf.get("righe_sfratto") or [])[:2]:
        _inf("        %s" % r[:240])
    for r in (sf.get("righe_negato") or [])[:2]:
        _inf("        %s" % r[:240])


def stampa_orologio(o, come):
    if o.get("esito") != "misurato":
        _dub("FILO %s  %s" % (come, o.get("esito")))
        return
    _inf("FILO %s  %.3f kbit/s (%d byte, %d pacchetti in %.1f s) · %d eventi · "
         "intervallo mediano %s s (min %s, max %s) · %s byte a giro"
         % (come, o["kbit_s"], o["byte"], o["pacchetti"], o["secondi"],
            o["eventi"], o.get("intervallo_mediano_s"),
            o.get("intervallo_min_s"), o.get("intervallo_max_s"),
            o.get("byte_per_evento")))
    if o.get("perche_niente_intervallo"):
        _inf("        ⚠ %s" % o["perche_niente_intervallo"])


def fps_del_giro(n):
    """⭐ Il ritmo, e da DUE testimoni: la traccia §11.1 se si e' letta, e il
       conto che il CLIENTE stampa da solo se no.

    ⛔ Il secondo non e' un ripiego di comodo: su una finestra da dieci minuti la
       traccia e' grossa, e *«il lettore non ha risposto»* ha la faccia identica
       a *«la sessione non ha consegnato niente»* (`09-b70`, la terza faccia di
       §1.9).  ⇒ Con due testimoni, quel guasto non puo' travestirsi da misura.
    """
    if B70._ha_misurato(n) and n.get("fps"):
        return n["fps"], "traccia §11.1"
    d, sec = n.get("dal_cliente"), n.get("secondi_veri")
    if d and sec:
        return round(d["fotogrammi"] / float(sec), 2), "il conto del CLIENTE"
    return None, "nessun testimone del ritmo"


def _fuori(nome):
    return os.path.join(FUORI, "09-b81-%s.json" % nome)


def salva(nome, roba):
    os.makedirs(FUORI, exist_ok=True)
    with open(_fuori(nome), "w") as f:
        json.dump(roba, f, ensure_ascii=False, indent=1)


def carica(nome):
    try:
        with open(_fuori(nome)) as f:
            return json.load(f)
    except Exception:
        return None


def _voci(titolo, **k):
    v = {"prova": titolo, "predicati": []}
    v.update(k)
    return v


def _predica(voci, etichetta, esito):
    passa, perche = esito
    voci["predicati"].append({"predicato": etichetta, "passa": passa,
                              "perche": perche})
    (_ok if passa else (_dub if passa is None else _ko))("%s: %s"
                                                         % (etichetta, perche))
    return voci


# ═══════════════════════════════════════════════════════════════════════════
# PROVA 1 · ⛔⛔ IL FALSO POSITIVO
# ═══════════════════════════════════════════════════════════════════════════
def prova1(a):
    _log("PROVA 1 · ⛔⛔ IL FALSO POSITIVO — la prova che puo' far RITIRARE la cura")
    print("   `casa-cattiva` (delay 40ms 20ms distribution normal loss 2%), linea")
    print("   morta ACCESA, per %g minuti: l'atteso e' ZERO scatti." % (a.secondi / 60.0))
    print("   ⛔ Quella linea REGGE (`[M]` 7,8-10,2 fotogrammi/s): dichiararla")
    print("      morta vorrebbe dire buttare fuori uno che stava lavorando.")
    v = _voci("1 · il falso positivo", profilo="casa-cattiva", secondi=a.secondi)
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    va, perche = cure_come_voglio(stato, linea_morta="accesa",
                                  permille=LM_PERMILLE, silenzio_s=LM_SILENZIO_S)
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "P1 · ⛔⛔ nessun falso positivo", _muto(perche))
    p = profilo("casa-cattiva")
    with rete_guasta(B76._regole(p[1]), a.secondi + 400) as riletta:
        v["regola"] = riletta
        s, (pg, perche_g) = sonda("casa-cattiva")
        v["sonda"], v["guasto"] = s, {"passa": pg, "perche": perche_g}
        usc = B76.scena_accendi("barra")
        if not usc:
            _ko("la scena non parte: NON giudico questo giro")
            return _predica(v, "P1 · ⛔⛔ nessun falso positivo",
                            _muto("la scena non e' partita: senza una scena che "
                                  "si muove non c'e' nessun utente al lavoro da "
                                  "non buttare fuori"))
        _inf("scena «barra» sul monitor %s" % usc)
        riga0 = riga0_pulita()
        B76.rinnova(CHI, AFFITTO)
        _inf("⏳ %g minuti di sessione — comincio adesso" % (a.secondi / 60.0))
        n = B70.giro("p1-casa-cattiva", "barra", B70.TELA_PIENA, a.secondi)
        n["testimoni"] = B76.testimoni_connessione(riga0, n)
        lm = leggi_linea_morta(riga0)
        fin = leggi_finestre(riga0)
        B76.scena_spegni()
    B70.stampa_giro(n)
    B76.stampa_consegna(n)
    B76.stampa_testimoni(n["testimoni"])
    stampa_scatti(lm)
    stampa_finestre(fin)
    fps, da_dove = fps_del_giro(n)
    _inf("RITMO   %s fotogrammi/s (%s)" % (fps, da_dove))
    n2 = dict(n)
    n2["fps"] = fps
    v["giro"] = {k: n.get(k) for k in ("fps", "esito", "dal_cliente",
                                       "secondi_veri", "consegna", "server",
                                       "testimoni")}
    v["fps"], v["fps_da"] = fps, da_dove
    v["scatti"], v["dichiarata"] = lm, fin
    salva("p1", v)
    _predica(v, "P1 · ⛔⛔ NESSUN FALSO POSITIVO in %g minuti" % (a.secondi / 60.0),
             p1_niente_falso_positivo(lm, n["testimoni"], n2, a.secondi / 60.0))
    _predica(v, "P1b · ⛔ la soglia sta sopra la frazione DICHIARATA",
             p1b_soglia_sopra_la_dichiarata(fin, s))
    return v


def prova1_controllo(a):
    """⛔⛔ IL CONTROLLO DELLA PROVA 1 — stessa linea, stessa durata, cure SPENTE.

    ⇒ Serve a due cose, e nessuna delle due e' un di piu':
      1. **rendere valido il rosso della prova 1**: quando la cura scatta la
         sessione muore, e da un giro morto a 4 s non si legge se la linea
         reggesse (⇒ `p1c`);
      2. **dare a `P1b` le sue finestre**: la ricostruzione della frazione
         DICHIARATA ha bisogno di centinaia di finestre, e con la cura accesa
         ce ne sono cinque perche' la sessione e' durata quattro secondi.
    """
    _log("PROVA 1 · IL CONTROLLO — stessa linea, stessa durata, cure SPENTE")
    print("   ⛔ Senza questo giro il rosso della prova 1 non vale: quando la cura")
    print("      scatta la sessione muore, e «ha buttato fuori uno che lavorava»")
    print("      avrebbe la stessa faccia di «la linea era finita comunque».")
    v = _voci("1-controllo · la stessa linea a cure SPENTE",
              profilo="casa-cattiva", secondi=a.secondi)
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    va, perche = cure_come_voglio(stato, linea_morta="spenta", sfratto_ms=0)
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "P1c · il controllo", _muto(perche))
    accesa = carica("p1") or {}
    scatti_accesa = ((accesa.get("scatti") or {}).get("scatti"))
    p = profilo("casa-cattiva")
    with rete_guasta(B76._regole(p[1]), a.secondi + 400) as riletta:
        v["regola"] = riletta
        s, (pg, perche_g) = sonda("casa-cattiva")
        v["sonda"], v["guasto"] = s, {"passa": pg, "perche": perche_g}
        usc = B76.scena_accendi("barra")
        if not usc:
            return _predica(v, "P1c · il controllo",
                            _muto("la scena non e' partita"))
        _inf("scena «barra» sul monitor %s" % usc)
        riga0 = riga0_pulita()
        B76.rinnova(CHI, AFFITTO)
        _inf("⏳ %g minuti di sessione a cure SPENTE — comincio adesso"
             % (a.secondi / 60.0))
        n = B70.giro("p1c-casa-cattiva", "barra", B70.TELA_PIENA, a.secondi)
        n["testimoni"] = B76.testimoni_connessione(riga0, n)
        lm = leggi_linea_morta(riga0)
        fin = leggi_finestre(riga0)
        B76.scena_spegni()
    B70.stampa_giro(n)
    B76.stampa_consegna(n)
    B76.stampa_testimoni(n["testimoni"])
    stampa_scatti(lm)
    stampa_finestre(fin)
    fps, da_dove = fps_del_giro(n)
    _inf("RITMO   %s fotogrammi/s (%s)" % (fps, da_dove))
    n2 = dict(n)
    n2["fps"] = fps
    v["giro"] = {k: n.get(k) for k in ("fps", "esito", "dal_cliente",
                                       "secondi_veri", "consegna")}
    v["fps"], v["scatti"], v["dichiarata"] = fps, lm, fin
    salva("p1-controllo", v)
    _predica(v, "P1c · ⛔⛔ a cure SPENTE la stessa linea REGGE %g minuti"
             % (a.secondi / 60.0),
             p1c_la_linea_regge_a_cura_spenta(n["testimoni"], n2,
                                              a.secondi / 60.0, scatti_accesa))
    # ⛔ E QUI si giudica la soglia, non nel giro acceso: e' l'unico giro che
    #    abbia abbastanza finestre perche' «non ha mai sfondato» sia una misura.
    _predica(v, "P1b · ⛔ la soglia sta sopra la frazione DICHIARATA "
             "(su %g minuti di linea che regge)" % (a.secondi / 60.0),
             p1b_soglia_sopra_la_dichiarata(fin, s))
    return v


def prova1_taratura(a):
    """⭐ LA TARATURA — e chiude il buco della ricostruzione (⇒ il riquadro in
       testa).  Stesso `casa-cattiva`, ma con `--linea-morta-permille 1`: a
       quella soglia la cura scatta di sicuro, e scattando **stampa il
       `permille=` che ha calcolato lei**, sulla sua finestra, con la sua
       aritmetica.  ⇒ E' l'unico modo di leggere la frazione DICHIARATA senza
       rifarla a mano.

    ⛔ Non giudica: MISURA e riporta.  Il giudizio sulla soglia e' di `P1b`.
    """
    _log("PROVA 1 · LA TARATURA — quanto vale la frazione DICHIARATA, detta dal "
         "PRODOTTO")
    v = _voci("1-taratura · la frazione dichiarata, letta dal prodotto",
              profilo="casa-cattiva")
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    va, perche = cure_come_voglio(stato, linea_morta="accesa", permille=1)
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "taratura", _muto(perche))
    p = profilo("casa-cattiva")
    with rete_guasta(B76._regole(p[1]), 240) as riletta:
        v["regola"] = riletta
        s, _g = sonda("casa-cattiva")
        v["sonda"] = s
        usc = B76.scena_accendi("barra")
        _inf("scena «barra» sul monitor %s" % usc)
        riga0 = riga0_pulita()
        n = B70.giro("p1-taratura", "barra", B70.TELA_PIENA, a.taratura_s)
        lm = leggi_linea_morta(riga0)
        fin = leggi_finestre(riga0, soglia_permille=1)
        B76.scena_spegni()
    stampa_scatti(lm)
    stampa_finestre(fin)
    v["scatti"], v["dichiarata"] = lm, fin
    if lm.get("esito") == "letto" and lm["scatti"]:
        _ok("⭐ IL PRODOTTO DICE LA SUA: sulla finestra in cui ha deciso, la "
            "frazione DICHIARATA valeva **%s‰** (%s persi su %s spediti in %s "
            "ms) — e la mia ricostruzione dalle righe `rete-quic` dava max %s‰, "
            "mediana %s‰"
            % (lm.get("permille"), lm.get("persi"), lm.get("spediti"),
               lm.get("finestra_ms"), fin.get("permille_max"),
               fin.get("permille_mediano")))
        v["permille_dal_prodotto"] = lm.get("permille")
    else:
        _dub("⚠ a 1‰ la cura non e' scattata: la taratura non ha prodotto il "
             "numero del prodotto, e resta la sola ricostruzione")
    salva("p1-taratura", v)
    return v


# ═══════════════════════════════════════════════════════════════════════════
# PROVA 2 · LO SCATTO VERO
# ═══════════════════════════════════════════════════════════════════════════
def prova2(a):
    _log("PROVA 2 · LO SCATTO VERO — `raffica-forte`, e DEVE scattare")
    print("   `[M]` 11,10 % di perdita a raffiche: a cura spenta lo schermo resta")
    print("   fermo 14,26 s su 25 (griglia di 09-b76).  ⇒ La cura deve scattare,")
    print("   con causa=perdita, e il filo deve cadere.")
    v = _voci("2 · lo scatto vero", profilo="raffica-forte", secondi=a.corti)
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    va, perche = cure_come_voglio(stato, linea_morta="accesa", permille=LM_PERMILLE)
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "P2 · lo scatto vero", _muto(perche))
    p = profilo("raffica-forte")
    with rete_guasta(B76._regole(p[1]), a.corti + 400) as riletta:
        v["regola"] = riletta
        s, (pg, perche_g) = sonda("raffica-forte")
        v["sonda"], v["guasto"] = s, {"passa": pg, "perche": perche_g}
        usc = B76.scena_accendi("barra")
        _inf("scena «barra» sul monitor %s" % usc)
        riga0 = riga0_pulita()
        n = B70.giro("p2-raffica-forte", "barra", B70.TELA_PIENA, a.corti)
        n["testimoni"] = B76.testimoni_connessione(riga0, n)
        lm = leggi_linea_morta(riga0)
        fin = leggi_finestre(riga0)
        sf = leggi_sfratto(riga0)
        B76.scena_spegni()
    B70.stampa_giro(n)
    B76.stampa_consegna(n)
    stampa_scatti(lm)
    stampa_finestre(fin)
    # ⭐ Da quando il posto e' stato preso a quando la cura ha deciso: e'
    #   l'orologio del SERVER, e i due istanti stanno nello stesso registro.
    secondi = None
    if lm.get("esito") == "letto" and lm["scatti"] and sf.get("righe_preso"):
        secondi = dt_registro(lm["righe"][0]["riga"], sf["righe_preso"][0])
    v["secondi_a_scatto"] = secondi
    _inf("QUANDO  scattata %s s dopo che il posto era stato preso"
         % (("%.2f" % secondi) if secondi is not None else "?"))
    v["scatti"], v["dichiarata"] = lm, fin
    v["giro"] = {k: n.get(k) for k in ("fps", "esito", "dal_cliente",
                                       "secondi_veri", "consegna")}
    salva("p2", v)
    _predica(v, "P2 · la cura SCATTA sulla raffica, con causa=perdita",
             p2_scatta_sulla_raffica(lm, s, secondi))
    return v


# ═══════════════════════════════════════════════════════════════════════════
# PROVA 3 · IL SILENZIO, E IL PREZZO DEI PING
# ═══════════════════════════════════════════════════════════════════════════
def prova3(a, acceso):
    come = "ACCESA" if acceso else "SPENTA"
    _log("PROVA 3 · IL SILENZIO — cliente ucciso con `kill -9`, cura %s" % come)
    print("   ⛔ `-9` e non un congedo: l'addio NON parte, e per il server e'")
    print("      identico a un addio PERSO — cioe' e' il caso vero.")
    v = _voci("3 · il silenzio (cura %s)" % come, acceso=acceso)
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    va, perche = cure_come_voglio(
        stato, linea_morta=("accesa" if acceso else "spenta"),
        silenzio_s=(LM_SILENZIO_S if acceso else None))
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "P3 · il silenzio", _muto(perche))
    ripulisci_clienti()
    # ⛔ Il `netem` c'e' anche senza guasto: e' lui che porta il CONTATORE dei
    #    byte, e senza contatore «il traffico vero a sessione ferma» non si
    #    misura.  ⚠ `limit 20000` e basta — e il profilo `liscio` di 09-b76
    #    verifica che quella coda non butti niente di suo.
    with rete_guasta(B76._regole([]), 400) as riletta:
        v["regola"] = riletta
        # ⭐ Scena SPENTA: «a sessione ferma» vuol dire che il desktop non si
        #   muove, o quel che misuro e' il video.
        B76.scena_spegni()
        riga0 = riga0_pulita()
        cliente_in_sottofondo(UTENTE, DENTRO_LAV + "/parola", 400,
                              "p3-%s" % ("acceso" if acceso else "spento"))
        preso = aspetta_riga(riga0, ["posto PRESO da %s " % UTENTE], 120)
        if not preso:
            ripulisci_clienti()
            return _predica(v, "P3 · il silenzio",
                            _muto("la sessione non si e' aperta in 120 s: non ho "
                                  "niente da uccidere"))
        _ok("sessione aperta: %s" % preso[-1][:120])
        _inf("⏳ %g s di orologio del filo a sessione FERMA" % a.orologio_s)
        oro = orologio_gira(a.orologio_s)
        stampa_orologio(oro, come)
        v["orologio"] = oro
        salva("p3-orologio-%s" % ("acceso" if acceso else "spento"), oro)
        pid = cliente_pid(UTENTE)
        _inf("il cliente e' il pid %s sull'host (⛔ `enter.sh` e' un chroot)" % pid)
        t_kill = uccidi(pid)
        _inf("UCCISO  con -9 alle %s (orologio del SERVER)" % (t_kill or "?"))
        v["t_kill"] = t_kill
        righe = aspetta_riga(riga0, ["linea-morta "],
                             tetto=(a.attesa_scatto if acceso else 25.0))
        lm = leggi_linea_morta(riga0)
        # ⭐ E SUBITO DOPO: il posto e' tornato libero?  E' l'altra meta' del
        #   fantasma, e la risposta della LINEA MORTA (non dello sfratto).
        posto = None
        if acceso:
            righe_p, coda = B78.misura(giri=1, fino="sessione", tetto=20,
                                       riprova=a.riprova_s)
            v["apertura_dopo_scatto"] = righe_p
            if righe_p:
                r = righe_p[0]
                posto = (r.get("attesa_posto_ms") if r.get("attesa_posto_ms")
                         is not None else 0)
                _inf("POSTO   dopo lo scatto: esito «%s», attesa del posto %s ms"
                     % (r.get("esito"), r.get("attesa_posto_ms")))
        sf = leggi_sfratto(riga0)
        ripulisci_clienti()
    stampa_scatti(lm)
    stampa_sfratto(sf)
    if lm.get("esito") == "letto" and lm["scatti"] and t_kill:
        v["secondi_dal_kill"] = dt_registro(lm["righe"][0]["riga"], t_kill)
        _inf("QUANDO  scattata %.2f s dopo il `kill -9` (orologio del server) · "
             "la riga dice silenzio_ms=%s"
             % (v["secondi_dal_kill"] or -1, lm.get("silenzio_ms")))
    v["scatti"], v["sfratto"] = lm, sf
    salva("p3-%s" % ("acceso" if acceso else "spento"), v)
    if acceso:
        _predica(v, "P3 · la cura scatta sul SILENZIO alla sua soglia",
                 p3_scatta_sul_silenzio(lm, LM_SILENZIO_S * 1000))
    else:
        # ⛔ A cura spenta lo scatto NON deve esserci: e' meta' di I6, e si
        #    giudica col predicato di I6, non con questo.
        _predica(v, "P3/I6 · a cura SPENTA il silenzio non chiude niente",
                 p6_i_predefiniti_non_cambiano_niente(lm, sf, stato, None,
                                                      "(nessun profilo)"))
    acc = carica("p3-orologio-acceso")
    spe = carica("p3-orologio-spento")
    if acc and spe:
        _predica(v, "P3b · ⚠ il prezzo DICHIARATO dei PING (%.2f kbit/s)"
                 % COSTO_PING_DICHIARATO_KBIT_S, p3b_costo_dei_ping(acc, spe))
    else:
        _dub("P3b · il prezzo dei PING: ho una sola delle due misure "
             "(acceso=%s, spento=%s) — si giudica quando ci sono tutt'e due"
             % (bool(acc), bool(spe)))
    return v


# ═══════════════════════════════════════════════════════════════════════════
# PROVA 4 · LO SFRATTO   ·   PROVA 5 · DUE UTENTI DIVERSI
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔⛔ E QUI C'E' UNA COSA DA DIRE PRIMA DI MISURARE, o le due prove misurerebbero
#     la cura sbagliata: **le due cure si accavallano**.  Con la linea morta
#     accesa il fantasma sparisce a 10 s (la connessione si chiude, e chiudendosi
#     lascia il posto); lo sfratto e' consigliato a 15 s.  ⇒ Con tutt'e due
#     accese lo sfratto NON scatterebbe MAI in questo scenario, e un banco che le
#     accendesse insieme misurerebbe la linea morta chiamandola sfratto.
#     ⇒ Le prove 4 e 5 girano con `--sfratto-ms 15000` e la LINEA MORTA SPENTA.
def _fantasma(a, chi_chiede, parola_dentro_dir, attesa_prima=0.0):
    """Il pezzo comune: un cliente di `%s` prende il posto, muore di `-9`, e poi
       qualcuno chiede quel posto.  Torna i numeri, non i giudizi.""" % UTENTE
    ripulisci_clienti()
    riga0 = riga0_pulita()
    cliente_in_sottofondo(UTENTE, DENTRO_LAV + "/parola", 400, "p4-vittima")
    preso = aspetta_riga(riga0, ["posto PRESO da %s " % UTENTE], 120)
    if not preso:
        ripulisci_clienti()
        return {"esito": "⛔ la sessione della vittima non si e' aperta in 120 s"}
    _ok("il posto e' di %s: %s" % (UTENTE, preso[-1][:120]))
    pid = cliente_pid(UTENTE)
    t_kill = uccidi(pid)
    _inf("UCCISO  il pid %s con -9 alle %s (orologio del SERVER)" % (pid, t_kill))
    if attesa_prima:
        _inf("⏳ aspetto %g s prima di bussare: cosi' l'occupante e' gia' oltre "
             "la soglia dello sfratto, e se lo sfratto potesse scattare "
             "scatterebbe" % attesa_prima)
        time.sleep(attesa_prima)
    # ⛔ `09-b78-apertura.py --riprova-0f`: CRONOMETRA il posto negato invece di
    #    contarlo — `GIA_ATTIVA_REMOTA` e' uno stato che PASSA, e un si'/no lo
    #    farebbe sembrare un guasto permanente.
    ute, dl = B78.UTENTE, B78.DENTRO_LAV
    try:
        B78.UTENTE, B78.DENTRO_LAV = chi_chiede, parola_dentro_dir
        righe, coda = B78.misura(giri=1, fino="sessione", tetto=20,
                                 riprova=a.riprova_s)
    finally:
        B78.UTENTE, B78.DENTRO_LAV = ute, dl
    sf = leggi_sfratto(riga0)
    n = {"esito": "misurato", "t_kill": t_kill, "aperture": righe,
         "coda": coda[-400:], "sfratto": sf, "chi_chiede": chi_chiede}
    r = righe[0] if righe else {}
    n["esito_apertura"] = r.get("esito")
    n["attesa_posto_ms"] = r.get("attesa_posto_ms")
    n["entrato"] = bool(r.get("esito", "").startswith("aperta"))
    # ⭐ «A che secondo entra», sull'orologio del SERVER: l'ultimo `posto PRESO`
    #   dopo `riga0` e' quello di chi ha bussato.
    if sf.get("presi", 0) >= 2 and t_kill:
        n["secondi_a_entrare"] = dt_registro(sf["righe_preso"][-1], t_kill)
    ripulisci_clienti()
    return n


def prova4(a, sfratto_ms):
    come = ("--sfratto-ms %d" % sfratto_ms) if sfratto_ms else "sfratto SPENTO"
    _log("PROVA 4 · LO SFRATTO DEL FANTASMA — %s" % come)
    print("   `[M]` oggi servono 30,5 s e 11 rifiuti: il filo cade, l'utente")
    print("   riprova, e per mezzo minuto gli si dice «hai gia' una sessione")
    print("   attiva altrove» — che per lui e' FALSO: quella sessione e' la sua.")
    v = _voci("4 · lo sfratto (%s)" % come, sfratto_ms=sfratto_ms)
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    # ⛔ La linea morta dev'essere SPENTA: vedi il riquadro sopra `_fantasma`.
    va, perche = cure_come_voglio(stato, linea_morta="spenta",
                                  sfratto_ms=sfratto_ms)
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "P4 · lo sfratto", _muto(perche))
    n = _fantasma(a, UTENTE, DENTRO_LAV)
    v["fantasma"] = n
    if n.get("esito") != "misurato":
        return _predica(v, "P4 · lo sfratto", _muto(n.get("esito")))
    stampa_sfratto(n["sfratto"])
    _inf("SCALA   %d rifiuti («posto NEGATO») · esito «%s» · il posto e' tornato "
         "libero dopo %s s (orologio del server) · il cliente ha aspettato %s ms"
         % (n["sfratto"]["rifiuti"], n.get("esito_apertura"),
            ("%.2f" % n["secondi_a_entrare"]) if n.get("secondi_a_entrare")
            is not None else "?", n.get("attesa_posto_ms")))
    salva("p4-%d" % sfratto_ms, v)
    if not sfratto_ms:
        # ⛔ E' il RIFERIMENTO, non una prova: qui non c'e' nessuna cura da
        #    giudicare, c'e' il numero contro cui si misura il guadagno.
        _inf("⭐ questo e' il RIFERIMENTO (cura spenta): %s s e %d rifiuti"
             % (("%.2f" % n["secondi_a_entrare"]) if n.get("secondi_a_entrare")
                is not None else "?", n["sfratto"]["rifiuti"]))
        # ⚠ Qui la linea morta e' spenta per costruzione (`cure_come_voglio`
        #   l'ha gia' preteso), e in questo giro non c'e' nessun `netem`: non
        #   c'e' niente che possa averla fatta scattare.  ⇒ Si passa una
        #   riduzione VUOTA e LETTA, e a giudicare resta il solo sfratto.
        _predica(v, "P4/I6 · a sfratto SPENTO non c'e' nessuno sfratto",
                 p6_i_predefiniti_non_cambiano_niente(
                     {"esito": "letto", "scatti": 0, "righe": [],
                      "chiuse_dal_trasporto": 0},
                     n["sfratto"], stato, None, "(nessun profilo)"))
        return v
    rif = carica("p4-0")
    rif_s = ((rif or {}).get("fantasma") or {}).get("secondi_a_entrare")
    _predica(v, "P4 · lo SFRATTO libera il posto alla soglia",
             p4_lo_sfratto_libera_il_posto(n["sfratto"], sfratto_ms,
                                           n.get("secondi_a_entrare"), rif_s))
    return v


def prova5(a):
    _log("PROVA 5 · ⛔ IL CASO CHE NON DEVE ROMPERSI — due utenti diversi")
    print("   Uno sfratto fra utenti diversi non sarebbe una comodita': sarebbe")
    print("   un buco di sicurezza — chiunque potrebbe far cadere il desktop di")
    print("   un altro semplicemente bussando.")
    v = _voci("5 · due utenti diversi", utente_a=UTENTE, utente_b=UTENTE2)
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    va, perche = cure_come_voglio(stato, linea_morta="spenta",
                                  sfratto_ms=SFRATTO_CONSIGLIATO_MS)
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "P5 · due utenti diversi", _muto(perche))
    # ⛔ La parola del SECONDO utente sta in un file a parte, e la si mette dove
    #    `09-b78` la cerca (`<DENTRO_LAV>/parola`) senza toccarne una riga: cosi'
    #    l'apertura del secondo utente passa dallo STESSO strumento della 4.
    root("bash -c \"mkdir -p %s/u2 && cp %s/parola2 %s/u2/parola && "
         "chmod 600 %s/u2/parola\"" % (LAV, LAV, LAV, LAV))
    rc, out, _ = root("bash -c \"test -s %s/u2/parola && echo si || echo no\"" % LAV)
    if "si" not in out:
        return _predica(v, "P5 · due utenti diversi",
                        _muto("la parola del secondo utente non e' in %s/u2/parola: "
                              "senza, aprirei due sessioni dello STESSO utente "
                              "credendo di averne aperte due di utenti diversi" % LAV))
    # ⭐ Si aspetta OLTRE la soglia dello sfratto prima di bussare: se lo sfratto
    #   potesse scattare fra utenti diversi, a quel punto scatterebbe.
    n = _fantasma(a, UTENTE2, DENTRO_LAV + "/u2",
                  attesa_prima=SFRATTO_CONSIGLIATO_MS / 1000.0 + 3.0)
    v["fantasma"] = n
    if n.get("esito") != "misurato":
        return _predica(v, "P5 · due utenti diversi", _muto(n.get("esito")))
    stampa_sfratto(n["sfratto"])
    _inf("ESITO   «%s» per «%s» · %d rifiuti · %d posti presi"
         % (n.get("esito_apertura"), UTENTE2, n["sfratto"]["rifiuti"],
            n["sfratto"]["presi"]))
    salva("p5", v)
    _predica(v, "P5 · ⛔ fra utenti diversi NON si sfratta",
             p5_fra_utenti_diversi_non_si_sfratta(n["sfratto"], n.get("entrato"),
                                                  UTENTE, UTENTE2))
    _predica(v, "P5b · ⚠ e la riga «SFRATTO NEGATO»? (previsione `[R]`: non esce)",
             p5b_la_riga_del_negato(n["sfratto"]))
    return v


# ═══════════════════════════════════════════════════════════════════════════
# PROVA 6 · ⛔ I PREDEFINITI NON CAMBIANO NIENTE (I6)
# ═══════════════════════════════════════════════════════════════════════════
def prova6(a, nome):
    _log("PROVA 6 · ⛔ I PREDEFINITI — «%s» col prodotto COSI' COME ESCE OGGI" % nome)
    print("   Senza `--linea-morta` e con `--sfratto-ms 0`: nessuno scatto,")
    print("   nessuno sfratto, e il profilo si comporta come nella griglia di")
    print("   09-b76.  ⛔ E' l'invariante I6, ed e' anche la prova che le due")
    print("   cure sono davvero SPENTE, non solo scritte.")
    v = _voci("6 · i predefiniti (%s)" % nome, profilo=nome, secondi=a.corti)
    stato = stato_delle_cure()
    v["stato_cure"] = stato
    va, perche = cure_come_voglio(stato, linea_morta="spenta", sfratto_ms=0)
    (_ok if va else _dub)(perche)
    if va is not True:
        return _predica(v, "P6 · I6 su «%s»" % nome, _muto(perche))
    p = profilo(nome)
    with rete_guasta(B76._regole(p[1]), a.corti + 400) as riletta:
        v["regola"] = riletta
        s, (pg, perche_g) = sonda(nome)
        v["sonda"], v["guasto"] = s, {"passa": pg, "perche": perche_g}
        usc = B76.scena_accendi("barra")
        _inf("scena «barra» sul monitor %s" % usc)
        riga0 = riga0_pulita()
        n = B70.giro("p6-%s" % nome, "barra", B70.TELA_PIENA, a.corti)
        n["testimoni"] = B76.testimoni_connessione(riga0, n)
        lm = leggi_linea_morta(riga0)
        sf = leggi_sfratto(riga0)
        fin = leggi_finestre(riga0)
        B76.scena_spegni()
    B70.stampa_giro(n)
    B76.stampa_consegna(n)
    B76.stampa_testimoni(n["testimoni"])
    stampa_scatti(lm)
    stampa_sfratto(sf)
    stampa_finestre(fin)
    fps, da_dove = fps_del_giro(n)
    _inf("RITMO   %s fotogrammi/s (%s)" % (fps, da_dove))
    n2 = dict(n)
    n2["fps"] = fps
    v["giro"] = {k: n.get(k) for k in ("fps", "esito", "dal_cliente",
                                       "secondi_veri", "consegna")}
    v["fps"], v["scatti"], v["sfratto"], v["dichiarata"] = fps, lm, sf, fin
    salva("p6-%s" % nome, v)
    _predica(v, "P6 · ⛔ I6: coi predefiniti «%s» e' identico a prima" % nome,
             p6_i_predefiniti_non_cambiano_niente(lm, sf, stato, n2, nome))
    return v


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LE QUATTRO CONFIGURAZIONI DEL SERVER — e perche' sono quattro
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Non e' una comodita': **le due cure si accavallano**, e accenderle insieme
#    farebbe misurare la prima chiamandola seconda (⇒ il riquadro sopra
#    `_fantasma`).  ⇒ Ogni prova gira sulla configurazione che ISOLA la cura che
#    misura, e `cure_come_voglio()` si rifiuta se il server non e' quella.
CONFIGURAZIONI = {
    "A": ("--linea-morta",
          "la LINEA MORTA accesa coi predefiniti (50‰, 10 s) e lo sfratto SPENTO "
          "— prove 1, 2 e 3"),
    "B": ("--linea-morta --linea-morta-permille 1",
          "la linea morta con la soglia a 1‰ — la TARATURA della prova 1: a "
          "quella soglia la cura scatta e STAMPA la frazione che ha calcolato lei"),
    "C": ("--sfratto-ms %d" % SFRATTO_CONSIGLIATO_MS,
          "lo SFRATTO acceso e la linea morta SPENTA — prove 4 e 5, e la linea "
          "morta dev'essere spenta o il fantasma sparirebbe a 10 s per l'altra "
          "cura e lo sfratto non scatterebbe mai"),
    "D": ("--sfratto-ms 0",
          "⛔ I PREDEFINITI, cioe' il prodotto cosi' come esce oggi — prova 6, "
          "il riferimento della 4 e la meta' spenta della 3"),
}


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", nargs="?",
                   choices=["terreno", "p1", "p1c", "p1t", "p2", "p3", "p4", "p5", "p6",
                            "tutte", "rimetti", "stato"])
    p.add_argument("--certifica", action="store_true",
                   help="⭐ il controllo positivo: prova che il banco sa vedere "
                        "i difetti che cerca. Non tocca la macchina di prova")
    p.add_argument("--secondi", type=int, default=600,
                   help="la finestra della prova 1 — ⛔ dieci minuti, ed e' il "
                        "numero che l'utente ha chiesto")
    p.add_argument("--corti", type=int, default=60,
                   help="la finestra dei giri corti (prove 2 e 6)")
    p.add_argument("--taratura-s", type=int, default=40)
    p.add_argument("--orologio-s", type=float, default=60.0,
                   help="quanto dura la misura del traffico a sessione ferma")
    p.add_argument("--attesa-scatto", type=float, default=45.0,
                   help="quanti secondi aspetto la riga `linea-morta` dopo il -9")
    p.add_argument("--riprova-s", type=float, default=75.0,
                   help="quanto a lungo il secondo client ribussa al posto "
                        "(09-b78 `--riprova-0f`)")
    p.add_argument("--attesa", type=int, default=1800,
                   help="quanti secondi aspetto il lucchetto del netem")
    p.add_argument("--salta-riaccensione", action="store_true",
                   help="⚠ non riaccende il server: si usa SOLO quando e' gia' "
                        "nella configurazione giusta, e `cure_come_voglio()` lo "
                        "verifica lo stesso")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if not a.passo:
        p.error("serve un passo, oppure --certifica")

    os.makedirs(FUORI, exist_ok=True)
    importa()

    if a.passo in ("rimetti", "stato"):
        _log("la rete della macchina di prova — dev «%s», porta %d" % (DEV, PORTA))
        ok = RETE.rimetti()
        _inf("porte NON mie: %s" % vicine())
        _inf("le cure, come il server le dichiara: %s"
             % json.dumps(stato_delle_cure(), ensure_ascii=False)[:400])
        return 0 if ok else 2

    _log("09-b81 · LE DUE CURE — porta %d · utente %s (uid %d) · dev «%s»"
         % (PORTA, UTENTE, UID_B, DEV))
    print("   ⛔ «%s» (ssh + la sessione dell'utente) NON si tocca" % VIETATA)
    print("   ⛔ le porte 7900, 7910 e 7920 si contano e non si toccano")
    print("   --  «%s» prima: %s" % (DEV, RETE.qdisc() or "(nessuna)"))
    if not preparati():
        return 2
    if not B70.terreno_controlla():
        return 2
    if a.passo == "terreno":
        _ok("il terreno c'e', ed e' mio")
        return 0

    def configura(chiave):
        if a.salta_riaccensione:
            _dub("⚠ NON riaccendo il server (--salta-riaccensione): mi fido di "
                 "`cure_come_voglio()`, che si rifiutera' se non e' la %s" % chiave)
            return True
        opz, perche = CONFIGURAZIONI[chiave]
        return accendi_server(opz, "configurazione %s — %s" % (chiave, perche))

    esiti = []
    try:
        # ⛔⛔ L'ORDINE NON E' UNA COMODITA': ogni prova gira sulla
        #     configurazione che ISOLA la cura che misura, e le prove che
        #     condividono la stessa configurazione stanno attaccate, o si
        #     pagherebbe una riaccensione (e una sessione d'innesco) per niente.
        #     ⚠ E `cure_come_voglio()` ricontrolla lo stesso, dentro ogni prova:
        #       l'ordine e' un risparmio, non una garanzia.
        tutte = (a.passo == "tutte")
        # ── configurazione A: la linea morta accesa coi predefiniti ────────
        if a.passo in ("p1", "p2", "p3", "tutte"):
            if configura("A"):
                if a.passo in ("p1", "tutte"):
                    esiti.append(prova1(a))
                if a.passo in ("p2", "tutte"):
                    esiti.append(prova2(a))
                if a.passo in ("p3", "tutte"):
                    esiti.append(prova3(a, acceso=True))
        # ── configurazione B: la taratura della frazione dichiarata ────────
        if a.passo in ("p1t", "tutte"):
            if configura("B"):
                esiti.append(prova1_taratura(a))
        # ── configurazione C: lo sfratto acceso, la linea morta SPENTA ─────
        if a.passo in ("p4", "p5", "tutte"):
            if configura("C"):
                if a.passo in ("p4", "tutte"):
                    esiti.append(prova4(a, SFRATTO_CONSIGLIATO_MS))
                if a.passo in ("p5", "tutte"):
                    esiti.append(prova5(a))
        # ── configurazione D: ⛔ i predefiniti, il prodotto come esce oggi ──
        if a.passo in ("p6", "p3", "p4", "p1c", "tutte"):
            if configura("D"):
                # ⛔ PRIMA il controllo della 1: e' quello che rende valido (o
                #    ritira) il rosso della prova 1, e va letto insieme a lei.
                if a.passo in ("p1c", "tutte"):
                    esiti.append(prova1_controllo(a))
                if a.passo in ("p6", "tutte"):
                    for nome in ("casa-cattiva", "raffica-forte"):
                        esiti.append(prova6(a, nome))
                if a.passo in ("p3", "tutte"):
                    esiti.append(prova3(a, acceso=False))
                if a.passo in ("p4", "tutte"):
                    esiti.append(prova4(a, 0))
        # ⛔ E il guadagno si conta alla fine: («di quanto e' sceso il
        #    fantasma») ha bisogno di tutt'e due i numeri, e quando la 4 con la
        #    cura e' girata il riferimento non c'era ancora.
        if tutte:
            rif, cur = carica("p4-0"), carica("p4-%d" % SFRATTO_CONSIGLIATO_MS)
            if rif and cur:
                _log("IL GUADAGNO — «di quanto e' sceso il fantasma»")
                rs = (rif.get("fantasma") or {}).get("secondi_a_entrare")
                cs = (cur.get("fantasma") or {}).get("secondi_a_entrare")
                rr = ((rif.get("fantasma") or {}).get("sfratto") or {}).get("rifiuti")
                cr = ((cur.get("fantasma") or {}).get("sfratto") or {}).get("rifiuti")
                _inf("sfratto SPENTO: %s s e %s rifiuti · sfratto a %d ms: %s s "
                     "e %s rifiuti" % (rs, rr, SFRATTO_CONSIGLIATO_MS, cs, cr))
                esiti.append({"prova": "il guadagno", "predicati": [],
                              "riferimento_s": rs, "con_cura_s": cs,
                              "rifiuti_riferimento": rr, "rifiuti_con_cura": cr})
    finally:
        ripulisci_clienti()
        B76.scena_spegni()
        rimessa = RETE.rimetti()
        try:
            LUC.molla(CHI, dillo=False)
        except Exception:
            pass

    salva("esiti", esiti)
    _log("IL VERDETTO")
    rossi, muti = [], []
    for v in esiti:
        for d in v["predicati"]:
            if d["passa"] is False:
                rossi.append("%s · %s — %s" % (v["prova"], d["predicato"],
                                               d["perche"][:120]))
            elif d["passa"] is None:
                muti.append("%s · %s — %s" % (v["prova"], d["predicato"],
                                              d["perche"][:120]))
    _inf("%d prove girate · %d rossi · %d non giudicati · esiti in %s"
         % (len(esiti), len(rossi), len(muti), _fuori("esiti")))
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
