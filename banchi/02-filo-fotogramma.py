#!/usr/bin/env python3
"""02-filo-fotogramma.py — ⛔ F2.4: il fotogramma giudicato contro `RCP.md`, byte per byte.

    python3 02-filo-fotogramma.py --elenco              le previsioni, senza misurare
    python3 02-filo-fotogramma.py                       il giro intero
    python3 02-filo-fotogramma.py --solo numero-zero    un caso solo
    python3 02-filo-fotogramma.py --guasto G1           con un guasto innestato nel GIUDICE
    python3 02-filo-fotogramma.py --certifica           sano -> G1 -> G2 -> G3 -> risanato
    python3 02-filo-fotogramma.py --uscita 02-filo-esiti.jsonl

⚠ Gira DOVUNQUE: non tocca la rete, non vuole aioquic, non vuole un server.
  ⛔ E questo NON e' una comodita': e' la ragione per cui esiste oggi.  Il
  prodotto della fase 2 non c'e' — `grep -c '0x0301\\|0x0302' src/*` da' **0**
  su tutti e tre i file, `[M]` 12 agosto 2026 — e `PIANO.md` §0.4 momento 1
  vuole il banco **prima** del prodotto.  Un banco che per esistere pretendesse
  il prodotto sarebbe scritto dopo, cioe' sarebbe scritto **sapendo che cosa il
  prodotto fa**, che e' precisamente il difetto muto contro cui `RCP.md` §0
  esiste.

===========================================================================
⛔ PERCHE' QUESTO BANCO ESISTE, E QUALE MISURA SBAGLIATA IMPEDISCE

La fase 2 consegna **un fotogramma**.  Il modo naturale di provarlo e':
si accende il server, si apre la pagina, si guarda se compare il desktop.

  ⛔ *Quella prova e' verde anche se server e pagina hanno capito `RCP.md`
     nello stesso modo sbagliato.*

E' `PIANO.md` §0.4: in v1 l'arbitro era **mstsc**, e quando sbagliavamo a
capire la specifica un client altrui protestava gratis.  Adesso client e server
sono nostri, ⛔ **e il pixel sullo schermo non distingue un protocollo capito
da un protocollo capito uguale in due**.  Un `istante` letto little-endian da
tutt'e due i lati dipinge un desktop perfetto.

Questo programma e' il **terzo lettore** del capitolo del video: giudica
un fotogramma leggendo **soltanto** `RCP.md` §2.5, §5.1, §5.2, §6.0 e §6.2 —
⛔ e chi lo fa crescere **non guarda `src/rcp.c` ne' `src/pagina.html`**.  Chi
l'ha scritto ha contato le occorrenze di `0x0301` in `src/` per sapere che sono
zero, e non ha aperto quei file.

===========================================================================
⛔ LE QUATTRO COSE CHE OGNI CASO VERIFICA, E LA QUARTA E' NUOVA

  1. ⛔ **l'esito giusto**, e gli esiti sono **TRE**, non due.  `RCP.md` chiede
     al client tre comportamenti diversi e confonderli e' la forma **E8**:

       ACCETTATO           si consegna al decodificatore
       SCARTATO            ⛔ si BUTTA e NON si consegna — e si tratta come un
                           buco (§6.2, §5.2).  La sessione **resta viva**
       ERRORE_PROTOCOLLO   la connessione cade, col motivo (§3)

     ⚠ Un banco a due esiti fa passare `SCARTATO` per `ERRORE_PROTOCOLLO`:
     cioe' promuove a caduta della sessione un fotogramma abbandonato dal
     server **di proposito**, che e' il caso normale di §5.1;

  2. ⛔ **quale byte**, non solo che e' rosso.  `fasi/01-filo-nudo.md` B4: un
     arbitro che dice la cosa giusta accusando il byte sbagliato manda la
     diagnosi a leggere il messaggio sbagliato.  Ogni verdetto porta lo
     scostamento dentro l'intestazione e la riga di `RCP.md` che lo regge;

  3. ⛔ **la regola citata**, e si confronta.  Un rosso con la sezione
     sbagliata accanto e' verde per chi guarda il colore (rilievo R7.12 di
     `fasi/01-filo-nudo.md`);

  4. ⭐⛔ **E IL QUARTO ESITO: `AMBIGUO`.**

     `fasi/01-filo-nudo.md` §«I dodici punti in cui `RCP.md` ammette due
     letture» e' l'esito piu' prezioso di B9, e nessun banco lo produceva: li
     ha trovati un programma scritto apposta, **dopo**.  Qui il quarto esito e'
     dentro il banco che gira ogni giorno.

     ⛔ Un caso `AMBIGUO` **non e' un caso da sistemare nel prodotto**: e' un
     posto in cui `RCP.md` non decide, e due implementazioni conformi
     divergono.  ⚠ Non fa fallire il giro — nessuno ha sbagliato — ⛔ **ma si
     stampa in fondo, si conta, e finisce nel registro**, perche' un'ambiguita'
     taciuta e' indistinguibile da una regola.

===========================================================================
⭐⛔ E IL 12 AGOSTO 2026 LE QUATTRO AMBIGUITA' SONO STATE CHIUSE — questo file
    E' STATO RISCRITTO DI CONSEGUENZA

*Il 12 agosto 2026 il coordinatore ha applicato a `RCP.md` le sette righe che
questo banco proponeva (§2.5, §5.2, §6.2, §11.1).  ⛔ Da quel momento le quattro
`AMBIGUO` che questo file stampava sono **regole normative**, e un giudice che
continuasse a chiamarle ambiguita' starebbe giudicando il documento di ieri.*

  | riga entrata in `RCP.md` | dove | qui era | qui e' adesso |
  |---|---|---|---|
  | **P2** `numero` parte da 1, lo 0 e' riservato | §6.2 | `AMBIGUO` | `ERRORE_PROTOCOLLO` |
  | **P6** il primo fotogramma dopo `SESSIONE` DEVE essere chiave | §5.2 | `AMBIGUO` | `ERRORE_PROTOCOLLO` |
  | **P5** `largh.`/`altezza` DEVONO valere la tela concessa | §6.2 | `AMBIGUO` | `ERRORE_PROTOCOLLO` |
  | **P3** un `0x03` sul canale di controllo | §2.5 | `AMBIGUO` | `ERRORE_PROTOCOLLO` |
  | **P1** nessuno stream video prima di `SESSIONE` | §2.5 | derivata da §3+§1 | **citata**: §2.5 |
  | **P4** FIN prima dei 28 byte | §6.2 | derivata da §3 | **citata**: §6.2 |

⛔ **E ogni riga ha DUE casi, non uno: quello che la viola e quello che la
   rispetta.**  Un arbitro che conosce una regola e non ha l'ingresso che la fa
   scattare non la fa rispettare, e il verde che da' e' quello che da' fiducia
   (`CODER.md` §4.6).  ⚠ E il caso che la **rispetta** non e' un di piu': senza,
   una regola scritta troppo larga — «ogni misura diversa da 1920x1080 e'
   `ERRORE_PROTOCOLLO`» invece che «diversa dalla tela **concessa**» —
   resterebbe verde su tutto il banco.  La tabella `REGOLE_NUOVE` tiene i due
   nomi accanto alla sigla, e il giro **conta** quante regole hanno tutt'e due:
   un conto scritto a mano sarebbe il numero che nessuno ricalcola.

⭐ **E l'esito `AMBIGUO` resta nel codice, con zero casi che lo pretendono** —
   ⛔ e lo si **dichiara in coda a ogni giro** invece di lasciarlo scoprire:
   «nessuna ambiguita' stampata» e «il ramo che le stampa non lo esercita
   nessun caso» sono due fatti diversi, ed e' la forma **E8** rivolta contro il
   banco stesso.  Resta per due ragioni: `RCP.md` tornera' ad ammettere due
   letture — ne ha ammesse **dodici** nella sola fase 1
   (`fasi/01-filo-nudo.md` B9) — e il guasto **G5**, *«il giudice della mattina
   del 12 agosto»*, fa produrre `AMBIGUO` al giudice a ogni certificazione.
   ⚠ Quel che G5 esercita e' il ramo del **giudice**, non quello che li stampa:
   coi quattro casi che pretendono `ERRORE_PROTOCOLLO`, un `AMBIGUO` e' un
   **rosso**, ed e' esattamente quel che deve essere.

===========================================================================
⛔⛔ E LA SERA DEL 12 AGOSTO 2026 LA CURA DI P5 NE HA APERTA UN'ALTRA — **D14**

*`RCP.md` §6.2 e' stato corretto due volte lo stesso giorno.  La seconda cura —
«la misura del fotogramma deve valere la **tela in vigore**» — ha reso **legale
il cambio di tela a meta' sessione** (§7.1, `ADATTA_TELA` -> `TELA(ADATTATA)`).
⛔ E ogni volta che si rende legale una cosa nuova, si apre quel che quella cosa
nuova porta con se'.*

  ⛔ §6.2 fa chiudere con `ERRORE_PROTOCOLLO` chi riceve una misura diversa
     dalla tela in vigore, **ma §6.2 dice anche** — sette righe piu' sotto —
     che *«gli stream sono indipendenti, quindi i fotogrammi possono arrivare
     fuori ordine»*.  ⇒ Dopo un `TELA(ADATTATA)` i fotogrammi **gia' in volo**
     portano **legittimamente** la misura precedente, e un client conforme a
     §6.2 **uccide una sessione sana**.

  ⚠ E' la stessa forma di **P5**, la riga che la mattina del 12 agosto e'
    rimasta due ore dentro il documento scritta male: *un server conforme a
    §7.1 ucciso da un client conforme a §6.2*.  ⛔ Ma non e' la stessa
    famiglia: P5 era una **lettura doppia** — due implementazioni conformi
    producevano byte diversi.  Qui due implementazioni conformi e attente
    producono **lo stesso byte**, e quel byte e' la chiusura della sessione.
    ⇒ E' una **contraddizione interna**: una regola che punisce un caso che il
    documento stesso rende legale — la forma gia' nominata due volte in
    `RCP.md` (§5.5, il cursore nascosto del rilievo R11.11; §9, le sette parole
    di §2.2 trovate da B5).

  ⭐ **E la cura esiste gia' nel documento, per un altro campo**: §7.1 protegge
     la stessa identica scena per le **coordinate di input** con una **grazia
     di un secondo** — *«e' l'unico momento in cui i due lati hanno
     legittimamente due verita' diverse»*, terza eccezione dichiarata di §3.
     Per i fotogrammi quella grazia non c'e'.  La proposta **P8** e' quella
     riga, scritta per il verso in cui manca: la strada buona esisteva gia' in
     casa.

⛔ **FINCHE' IL COORDINATORE NON APPLICA P8, QUESTO GIUDICE DICE `AMBIGUO` IN
   QUELLA SCENA — E NON `ERRORE_PROTOCOLLO`.**  ⚠ Non e' indulgenza, ed e' la
   sola scelta che non avvelena il prossimo che legge questo banco: un verde su
   `ERRORE_PROTOCOLLO` in quella scena **certificherebbe che un client conforme
   deve uccidere una sessione sana**, e chi scrive il prodotto lo
   implementerebbe.  ⇒ Il caso `p8-in-volo-dopo-adatta-tela` **non fa fallire
   il giro** — nessuna delle due implementazioni ha sbagliato — ma si stampa in
   fondo con il testo pronto della cura, che e' il mestiere dell'esito
   `AMBIGUO` (punto 4 qui sopra).  ⭐ Ed e' la stessa strada da cui P2, P3, P5 e
   P6 sono passate stamattina, prima di diventare righe.

⛔ **E la scena che uccide non basta: ce ne vogliono TRE**, perche' una grazia
   scritta troppo larga e' un difetto quanto una regola scritta troppo stretta —
   ed e' esattamente cosi' che P5 e' finita sbagliata la prima volta:

     `p8-in-volo-dopo-adatta-tela`   la misura **precedente**, dentro la
                                     grazia -> `AMBIGUO` (con P8: ACCETTATO)
     `p8-in-volo-fuori-grazia`       la stessa misura, **passato il secondo**
                                     -> `ERRORE_PROTOCOLLO`.  ⛔ La grazia e'
                                     un secondo, non un permesso permanente
     `p8-misura-di-nessuna-tela`     una misura che non e' **ne'** quella in
                                     vigore **ne'** la precedente, subito dopo
                                     il `TELA` -> `ERRORE_PROTOCOLLO`.  ⛔ La
                                     grazia copre **una misura**, non «tutto
                                     per un secondo»

⚠ **E questo banco non ha un orologio**: il *secondo* di §7.1 lo dichiara il
  caso (`grazia_scaduta`), non lo misura nessuno.  ⛔ Quanto duri davvero il
  volo di un fotogramma dopo un `TELA` e' una `[?]`, e questa famiglia intera e'
  stata trovata **leggendo**, non misurando.

===========================================================================
⛔ CHE COSA QUESTO BANCO **NON** PROVA, E VA DETTO

| | perche' non e' qui |
|---|---|
| che il server **spedisca** davvero un fotogramma | il prodotto non esiste (§0 di questo file).  Lo prova `02-filo-cliente.py` sulla **7514**, quando ci sara' |
| che i **pixel** decodificati siano quelli catturati | e' la sotto-fase **F2.6**, e non e' una misura di protocollo |
| che il **decodificatore** accetti i byte | e' **F2.5**: `VideoDecoder` e la tela |
| il **credito** degli stream oltre i primi 256 fotogrammi (§2.3) | la fase 2 consegna **un** fotogramma fermo; e' la **fase 3** |
| l'**abbandono** vero con `RESET_STREAM` sul filo | qui si giudica un flusso azzerato, non se ne provoca uno.  Il banco che lo provoca e' della **fase 3** (`RCP.md` §11, «il fotogramma abbandonato») |

⚠ Scriverlo qui non e' modestia: un banco che tace su quel che non copre viene
letto come se coprisse tutto, ed e' cosi' che un verde diventa un'assoluzione.
"""
import argparse
import json
import os
import struct
import sys
import time

# ---------------------------------------------------------------------------
# ⛔ I NUMERI DI `RCP.md`, IN UN POSTO SOLO E CON LA SEZIONE ACCANTO.
#
#    Un numero ricopiato in tre punti e' un numero che prima o poi diverge in
#    uno dei tre, e nessuno se ne accorge finche' non produce un sintomo
#    lontano.  ⚠ `INTESTAZIONE` in particolare e' il numero che `RCP.md` §6.2
#    ha gia' dovuto correggere una volta, il 9 agosto 2026: il disegno dava
#    `… 24 │ 32`, cioe' quattro byte di riempimento mai dichiarati.
INTESTAZIONE = 28                 # §6.2, «28 byte esatti, senza riempimento»
TETTO_FOTOGRAMMA = 16 * 1024 * 1024   # §6.2, «NON DEVE produrre un fotogramma
                                      # piu' lungo di 16 MiB»
CHIAVE, DELTA = 0x0301, 0x0302    # §5.2, §6.2
CODEC = {1: "hevc", 2: "av1"}     # §6.2
CANALE_VIDEO = 0x03               # §2.5
CANALI = {0x00: "controllo", 0x01: "input", 0x02: "appunti",
          0x03: "video", 0x04: "audio"}   # §2.5

# ⛔ Gli esiti, e sono QUATTRO.  Vedi il punto 1 e il punto 4 dell'intestazione.
ACCETTATO = "ACCETTATO"
SCARTATO = "SCARTATO"
ERRORE_PROTOCOLLO = "ERRORE_PROTOCOLLO"
AMBIGUO = "AMBIGUO"


class Verdetto:
    """Che cosa si e' deciso, con la riga di `RCP.md` che lo regge.

    ⛔ `scostamento` e' dentro l'intestazione del fotogramma, non dentro il
       file: qui non c'e' nessun file.  Chi legge una registrazione usa
       `02-filo-validatore.py`, che i due scostamenti di §11.1 li ha.
    """

    def __init__(self, esito, regola="", dice="", scostamento=None,
                 propone=""):
        self.esito = esito
        self.regola = regola
        self.dice = dice
        self.scostamento = scostamento
        self.propone = propone      # ⛔ solo per AMBIGUO: la cura, non il reclamo

    def __str__(self):
        p = [self.esito]
        if self.regola:
            p.append(f"[{self.regola}]")
        if self.dice:
            p.append(self.dice)
        if self.scostamento is not None:
            p.append(f"(byte {self.scostamento} dell'intestazione)")
        return " ".join(p)

    def come_dizionario(self):
        return {"esito": self.esito, "regola": self.regola, "dice": self.dice,
                "scostamento": self.scostamento}


class Contesto:
    """Quel che il client sa gia' quando arriva un fotogramma.

    ⛔ Non e' un comodo: **meta' delle regole di §6.2 si applicano solo con
       questo in mano**.  `codec` «DEVE essere quello negoziato in §4.3»;
       `largh.`/`altezza` si confrontano con la **tela concessa** di §4.5; il
       `numero` si confronta con l'ultimo consegnato.  Un giudice senza
       contesto puo' dire soltanto se i 28 byte sono ben formati, che e' il
       terzo delle regole e non e' il piu' caro.
    """

    def __init__(self, tela=(1920, 1080), codec_negoziato=1,
                 sessione_aperta=True):
        # ⛔ LA TELA E' QUELLA **IN VIGORE**, E PUO' CAMBIARE A META' SESSIONE.
        #
        #    §6.2, corretta il 12 agosto 2026: *«DEVONO valere la tela in
        #    vigore — quella concessa in `SESSIONE` (§4.5), **oppure** l'ultima
        #    concessa da `TELA` se nel frattempo e' stata adattata (§7.1)»*.
        #    ⚠ La riga precedente diceva «la tela concessa in `SESSIONE`», e
        #      **uccideva una sessione sana**: dopo un `ADATTA_TELA` il server
        #      cattura alla misura nuova, e un client che confrontasse ancora
        #      con `SESSIONE` chiuderebbe — la scena che §7.1 protegge con la
        #      sua eccezione 4.  Trovata propagando la regola a questi arbitri.
        self.tela_larghezza, self.tela_altezza = tela
        # ⛔ E si tiene DA DOVE viene, perche' e' la meta' che il verdetto deve
        #    saper dire: «diversa dalla tela di `SESSIONE`» e «diversa dalla
        #    tela in vigore» mandano a cercare in due posti diversi.
        self.tela_da = "SESSIONE (§4.5)"
        # ⛔⭐ E LE DUE VERITA' IN VOLO — difetto **D14**, proposta **P8**.
        #
        #    §7.1 lascia cambiare la tela a meta' sessione; §6.2 dice che «gli
        #    stream sono indipendenti, quindi i fotogrammi possono arrivare
        #    fuori ordine».  ⇒ Subito dopo un `TELA(ADATTATA)` il client ha in
        #    volo fotogrammi che portano **legittimamente** la misura di prima,
        #    e §6.2 alla lettera gli fa chiudere la sessione.
        #    ⚠ `tela_precedente` e' `None` finche' non e' mai cambiata niente:
        #      `None` e' «non c'e' una precedente», e NON e' una misura.
        self.tela_precedente = None
        # ⛔ La grazia di §7.1 dura **un secondo**, e questo banco non ha un
        #    orologio: lo stato lo dichiara il caso, non lo misura nessuno.
        #    ⇒ `True` vuol dire «il secondo non e' ancora passato», dichiarato.
        self.grazia_aperta = False
        self.codec_negoziato = codec_negoziato
        self.sessione_aperta = sessione_aperta
        # ⛔ `None` e' «nessuno», e NON e' zero: §6.0 vieta i valori sentinella
        #    impliciti, e zero e' un `numero` che il documento non esclude —
        #    vedi il caso `numero-zero`, che e' l'ambiguita' A1.
        self.ultimo_consegnato = None
        self.chiave_consegnata = False
        self.chiedi_chiave = False    # §5.2: il client DEVE chiederla su un buco

    def adatta_tela(self, lar, alt, precedente=None, grazia=False):
        """§7.1 — e' arrivato un `TELA(ADATTATA, lar, alt)`.

        ⛔ Da questo momento la tela **in vigore** e' un'altra, e §6.2 ci lega
           `largh.`/`altezza` di ogni fotogramma successivo.  ⚠ Chi chiama
           questo metodo lo fa perche' ha **visto** il messaggio sul filo: il
           giudice del fotogramma non lo puo' sapere da solo, e infatti la tela
           gli si dichiara sempre da fuori.

        ⛔⭐ E si tiene **la precedente**, perche' e' la meta' del difetto D14:
           i fotogrammi gia' in volo la portano **legittimamente**, e senza
           averla in mano il client non puo' distinguere «una misura vecchia
           che sta ancora arrivando» da «una misura che non e' mai stata di
           nessuna tela» — cioe' non puo' fare quel che §7.1 fa gia' per le
           coordinate di input.  ⚠ `precedente` si puo' passare da fuori: chi
           legge una **registrazione** ricostruisce le tele sfogliando il file,
           e il contesto lo riusa da un flusso all'altro.

        ⛔⛔ **E `grazia` e' SPENTA di suo, di proposito.**  La grazia di P8 non
           e' ancora una riga di `RCP.md`: e' una **proposta**.  ⇒ Chi chiama
           questo metodo senza chiederla continua a giudicare **il documento di
           oggi**, che e' quel che un arbitro deve fare — e questo giudice e'
           importato anche da `01-b4-validatore.py`, che e' della fase 1 e in
           ricertificazione.  ⚠ Accenderla di suo avrebbe cambiato in silenzio
           il verdetto di un banco che non sa niente di D14: e' l'invariante
           **I6** applicata a un banco — *cio' che cambia quel che si vede sta
           dietro un interruttore spento finche' non lo si guarda*.
        """
        self.tela_precedente = (precedente if precedente is not None
                                else (self.tela_larghezza, self.tela_altezza))
        self.grazia_aperta = bool(grazia)
        self.tela_larghezza, self.tela_altezza = lar, alt
        self.tela_da = "TELA(ADATTATA) (§7.1)"

    def scade_la_grazia(self):
        """⛔ E' passato **il secondo** di §7.1: da qui in poi la misura vecchia
           e' `ERRORE_PROTOCOLLO` come qualunque altra.

        ⚠ Non c'e' nessun messaggio che dica questo, ed e' voluto: il tempo non
          viaggia sul filo.  Lo dichiara il caso, e questo banco **non ha un
          orologio** — scriverlo qui e' meno peggio di simulare una misura che
          nessuno ha fatto (`MANDATO` §4: una cosa non misurata non si scrive
          come misurata).
        """
        self.grazia_aperta = False


# ---------------------------------------------------------------------------
class Giudice:
    """Giudica UN fotogramma mentre arriva, non dopo che e' arrivato.

    ⛔ **E il «mentre» e' normativo, non un vezzo di ingegneria.**  §6.2:
       *«Chi ne riceve uno piu' lungo chiude con `ERRORE_PROTOCOLLO` **invece
       di continuare ad accumulare**»*.  Un giudice che prende in mano il
       fotogramma intero e poi ne misura la lunghezza ha gia' fatto la cosa che
       quella riga vieta — e su una tela 7680x4320 il fotogramma che vuole
       fermare e' precisamente quello che non entra in memoria.

    ⛔ **E non conserva i dati.**  Conta i byte e li lascia andare: un banco che
       li tenesse per «guardarli meglio» misurerebbe la propria memoria.
    """

    def __init__(self, contesto, dove="uni", guasti=()):
        self.c = contesto
        self.dove = dove              # "uni" | "controllo"
        self.guasti = set(guasti)
        self.grezzo = bytearray()     # SOLO l'intestazione, mai i dati
        self.byte_dati = 0
        self.verdetto = None          # il primo verdetto vince
        self.letta = False
        self.campi = {}

        # ── i guasti innestabili, e ciascuno rompe UNA proprieta' ────────────
        # ⛔ Stanno qui e non in una copia del file perche' cio' che va
        #    guastato e' **il giudizio**, non lo scoring: un interruttore che
        #    spegnesse un controllo farebbe diventare rosso il banco senza
        #    dimostrare che il banco sa vedere quel guasto.  Vedi `--elenco`.
        self.intestazione = 32 if "G1" in self.guasti else INTESTAZIONE
        self.tipi_leciti = ({CHIAVE, DELTA, 0x0300} if "G2" in self.guasti
                            else {CHIAVE, DELTA})
        self.reset_come_fin = "G3" in self.guasti
        # ⛔ G5 — «il giudice della mattina del 12 agosto 2026», cioe' PRIMA che
        #    le quattro righe entrassero in `RCP.md`.  Vedi l'intestazione.
        self.regole_12_agosto = "G5" not in self.guasti

    # -- l'esito si scrive una volta sola: il primo verdetto e' la causa, i
    #    successivi sono conseguenze (come `_cade` in `01-b3-cliente.py`).
    def _decidi(self, v):
        if self.verdetto is None:
            self.verdetto = v
        return self.verdetto

    def _chiuso_il_12_agosto(self, sigla, scostamento, regola, dice,
                             regola_prima, dice_prima):
        """Una delle quattro letture doppie che `RCP.md` ha chiuso il 12 agosto.

        ⛔ Le due meta' stanno **nella stessa funzione** apposta: la riga di
           oggi e quella di ieri si leggono una sotto l'altra, e chi rileggesse
           questo file fra un mese vede subito **che cosa e' cambiato e
           perche'**.  ⚠ Tenerle in due punti lontani e' il modo in cui una
           delle due invecchia da sola.

        Col guasto **G5** innestato si torna alla lettura di ieri: il verdetto
        e' `AMBIGUO` invece di `ERRORE_PROTOCOLLO`, e i quattro casi che devono
        cadere diventano rossi con la marca `nome: ERRORE_PROTOCOLLO -> AMBIGUO`.
        """
        if not self.regole_12_agosto:
            return self._decidi(Verdetto(AMBIGUO, regola_prima, dice_prima,
                                         scostamento=scostamento,
                                         propone=sigla))
        return self._decidi(Verdetto(ERRORE_PROTOCOLLO, regola, dice,
                                     scostamento=scostamento))

    def arrivano(self, pezzo):
        """Arriva un pezzo dello stream.  Puo' gia' bastare a decidere."""
        if self.verdetto is not None:
            return
        if not self.letta:
            manca = self.intestazione - len(self.grezzo)
            self.grezzo += pezzo[:manca]
            pezzo = pezzo[manca:]
            if len(self.grezzo) == self.intestazione:
                self.letta = True
                self._leggi_intestazione()
                if self.verdetto is not None:
                    return
        self.byte_dati += len(pezzo)
        # ⛔ IL TETTO SI CONTROLLA QUI, MENTRE I BYTE SCORRONO — §6.2.
        if self.intestazione + self.byte_dati > TETTO_FOTOGRAMMA:
            self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §6.2",
                f"il fotogramma ha superato i {TETTO_FOTOGRAMMA} byte "
                f"({self.intestazione + self.byte_dati} finora): si chiude "
                f"«invece di continuare ad accumulare»"))

    def finisce(self, come):
        """`come` e' «fin» o «reset».  ⛔ E la differenza e' tutto §6.2."""
        if come not in ("fin", "reset"):
            raise ValueError(f"uno stream finisce con «fin» o «reset», non {come!r}")
        # ⛔ IL RESET SI GUARDA PER PRIMO, E PRIMA ANCORA DELL'INTESTAZIONE.
        #
        #    §6.2, rilievo R1.7: *«uno stream azzerato porta un fotogramma
        #    INCOMPLETO: il client DEVE buttare quel che ha ricevuto, NON DEVE
        #    consegnarlo al decodificatore, e DEVE trattarlo come un buco»*.
        #    ⚠ Un giudice che leggesse prima l'intestazione direbbe
        #    `ERRORE_PROTOCOLLO` su un `tipo` storto dentro un fotogramma che
        #    **non esiste**: il server lo ha abbandonato a meta', e i byte di
        #    quell'intestazione possono essere qualunque cosa.  Farebbe cadere
        #    la sessione per un abbandono, che e' il caso normale di §5.1.
        if come == "reset" and not self.reset_come_fin:
            self.c.chiedi_chiave = True
            return self._decidi(Verdetto(
                SCARTATO, "RCP.md §6.2",
                "stream azzerato: fotogramma INCOMPLETO — si butta, non si "
                "consegna al decodificatore, e si tratta come un buco (§5.2)"))
        if self.verdetto is not None:
            return self.verdetto
        if not self.letta:
            # ⛔ P4 — FIN PRIMA DEI 28 BYTE, e dal 12 agosto 2026 e' **citata**.
            #
            #    §6.2, terza riga di «⛔ La regola, in due righe:»: *«uno stream
            #    chiuso con FIN prima dei 28 byte dell'intestazione e'
            #    ERRORE_PROTOCOLLO: non e' un fotogramma corto, e' una
            #    lunghezza che non torna (§3)»*.
            #    ⚠ Fino all'11 agosto la regola si **ricavava** da §3, e §6.2 —
            #      il posto in cui chi implementa la guarda — non la scriveva:
            #      letta alla lettera, *«la fine dello stream e' la fine del
            #      fotogramma»* faceva di uno stream di 12 byte un fotogramma
            #      con **meno sedici** byte di dati.
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §6.2",
                f"lo stream finisce con FIN dopo {len(self.grezzo)} byte: "
                f"l'intestazione ne vuole {self.intestazione} esatti",
                scostamento=len(self.grezzo)))
        return self._decidi(self._giudica_completo())

    # -- l'intestazione, campo per campo, nell'ordine di §6.2 ----------------
    def _leggi_intestazione(self):
        g = bytes(self.grezzo[:INTESTAZIONE])
        tipo, codec, lar, alt, num, ist, inp = struct.unpack("!HHIIIQI", g)
        self.campi = {"tipo": tipo, "codec": codec, "larghezza": lar,
                      "altezza": alt, "numero": num, "istante": ist,
                      "input": inp}

        # 1. ⛔ IL CANALE, DAL BYTE ALTO — §2.5, e MAI dal numero dello stream.
        alto = tipo >> 8
        if alto != CANALE_VIDEO:
            nome = CANALI.get(alto)
            if nome is None:
                return self._decidi(Verdetto(
                    ERRORE_PROTOCOLLO, "RCP.md §2.5",
                    f"il byte alto del tipo vale {alto:#04x}: fuori dai cinque "
                    f"canali", scostamento=0))
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §2.5",
                f"su questo stream arriva il canale «{nome}» ({alto:#04x}) "
                f"dal server: e' il canale sbagliato, o il verso sbagliato",
                scostamento=0))

        # 2. ⭐⛔ P3 — DOVE E' ARRIVATO.  Chiusa il 12 agosto 2026.
        #
        #    §2.5, riga `0x03`: *«l'intestazione di 28 byte di §6.2, senza
        #    inquadratura — ⛔ e SOLO su uno stream unidirezionale aperto dal
        #    server: un `0x03` sul canale di controllo e' ERRORE_PROTOCOLLO,
        #    come lo e' un `0x00` su uno stream unidirezionale»*.
        #    ⚠ Fino all'11 agosto la stessa tabella chiudeva il caso per due
        #      canali su cinque e **non per il video**, e il client leggeva quei
        #      28 byte con l'inquadratura di §6.1 — un messaggio inventato di
        #      64 KiB.  Il server non apre stream bidirezionali (§2.5), quindi
        #      l'unico posto in cui puo' scrivere un `0x03` fuori posto e' il
        #      canale di controllo, che il client gli ha aperto.
        if self.dove == "controllo":
            return self._chiuso_il_12_agosto(
                "P3", 0, "RCP.md §2.5",
                "un fotogramma sul canale di CONTROLLO: §2.5 vuole il video "
                "«solo su uno stream unidirezionale aperto dal server», e un "
                "`0x03` sul canale di controllo e' ERRORE_PROTOCOLLO",
                "RCP.md §2.5",
                "un fotogramma sul canale di CONTROLLO: §2.5 vieta per nome il "
                "controllo su uno stream unidirezionale e l'audio su uno "
                "stream, e per il video non dice niente")

        # 3. ⛔ P1 — LO STATO, e dal 12 agosto 2026 e' **citata**.
        #
        #    §2.5, riga «video» della tabella: *«uno per fotogramma, ⛔ e
        #    nessuno prima di aver spedito `SESSIONE`: chi ne riceve uno prima
        #    chiude con ERRORE_PROTOCOLLO»*.
        #    ⚠ Fino all'11 agosto per chi RICEVE la regola si ricavava da §1
        #      («l'ordine dei cinque passi non ammette permute») piu' §3, e per
        #      chi MANDA non si ricavava da nessuna parte: era l'invariante
        #      **I3** — *chi non passa dal validatore non riceve un pixel* —
        #      lasciata senza una riga sul filo, mentre §2.5 la scriveva per il
        #      canale di input due righe sopra.
        if not self.c.sessione_aperta:
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §2.5",
                "un fotogramma prima di `SESSIONE`: §2.5 vieta al server di "
                "aprire uno stream video prima di averla spedita — e' "
                "l'invariante I3 sul filo, chi non passa dal validatore non "
                "riceve un pixel",
                scostamento=0))

        # 4. ⛔ IL TIPO — §6.2: «Altri valori: ERRORE_PROTOCOLLO».
        if tipo not in self.tipi_leciti:
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §6.2",
                f"tipo {tipo:#06x}: RCP/1 ne definisce due, {CHIAVE:#06x} "
                f"chiave e {DELTA:#06x} delta", scostamento=0))

        # 5. ⛔ IL CODEC — §6.2: «DEVE essere quello negoziato in §4.3».
        if codec not in CODEC:
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §6.2",
                f"codec {codec}: RCP/1 ne definisce due, 1 = HEVC e 2 = AV1",
                scostamento=2))
        if codec != self.c.codec_negoziato:
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §6.2",
                f"codec {codec} = {CODEC[codec]}, ma in §4.3 si era negoziato "
                f"{self.c.codec_negoziato} = {CODEC[self.c.codec_negoziato]}",
                scostamento=2))

        # 6. ⭐⛔ IL `numero` ZERO — l'ambiguita' A2, ed e' una CONTRADDIZIONE
        #    interna, non una lacuna.
        #
        #    §6.2: `numero` e' «contatore dei fotogrammi catturati, che cresce
        #    di uno per ogni fotogramma che il server decide di spedire» — e
        #    **non dice da quanto parte**.
        #    §7.1: `RICHIEDI_CHIAVE.ultimo_numero` e' «l'ultimo fotogramma
        #    decodificato, **0 se nessuno**».
        #    §6.0: «⛔ Ogni intero ha un solo significato di *assente*, e va
        #    dichiarato dove serve: **non esistono valori sentinella
        #    impliciti**».
        #    ⇒ Se il primo fotogramma porta `numero = 0`, `RICHIEDI_CHIAVE(0)`
        #      vuol dire tutt'e due le cose, e il server non puo' sapere quale.
        #    ⭐ Chiusa il 12 agosto 2026: §6.2 porta adesso *«il primo
        #      fotogramma di una sessione porta `numero = 1`, e lo 0 e'
        #      riservato»*, che e' la stessa convenzione dell'`id` dell'input
        #      (§7.3).
        if num == 0:
            return self._chiuso_il_12_agosto(
                "P2", 12, "RCP.md §6.2",
                "`numero = 0`: §6.2 riserva lo zero — «il primo fotogramma di "
                "una sessione porta `numero = 1`», e «al giro del contatore lo "
                "0 si salta» — perche' lo 0 vuol dire «nessun fotogramma», il "
                "significato che §7.1 gli da' in `RICHIEDI_CHIAVE`",
                "RCP.md §6.2 contro §7.1, per §6.0",
                "`numero = 0`: §7.1 usa lo zero come «nessuno» in "
                "`RICHIEDI_CHIAVE`, §6.2 non dice da dove parte il contatore, "
                "e §6.0 vieta i sentinella impliciti")

        # 7. ⭐⛔ P5 — LA MISURA.  Chiusa il 12 agosto 2026, e **corretta lo
        #    stesso giorno** perche' la prima stesura uccideva una sessione sana.
        #
        #    §6.2: *«la misura di QUESTO fotogramma.  ⛔ In RCP/1 DEVONO valere
        #    la **tela in vigore** — quella concessa in `SESSIONE` (§4.5),
        #    **oppure** l'ultima concessa da `TELA` se nel frattempo e' stata
        #    adattata (§7.1) — e chi ne riceve altre chiude con
        #    ERRORE_PROTOCOLLO: il client riscala alla VISTA, non alla tela»*.
        #    ⚠ Fino all'11 agosto la riga diceva *«e' sempre quella della tela,
        #      e il client riscala»* — che **descrive** e non comanda (§0
        #      dichiara normativo solo DEVE / NON DEVE / PUO') — e nessuna riga
        #      diceva che cosa fa chi riceve una misura diversa.
        #    ⛔ E per due ore ha detto «la tela concessa in `SESSIONE`», che
        #      dopo un `ADATTA_TELA` faceva chiudere il client davanti a un
        #      server conforme: le due parole giuste sono **in vigore**.
        #    ⛔ Il confronto e' con la tela CHE SI E' DICHIARATA, mai con un
        #      numero scritto qui: lo tengono onesto i due casi
        #      `misura-uguale-a-una-tela-diversa` e `misura-dopo-adatta-tela`.
        if (lar, alt) != (self.c.tela_larghezza, self.c.tela_altezza):
            # 7-bis. ⛔⛔ **D14 — I FOTOGRAMMI IN VOLO**, e qui §6.2 ucciderebbe
            #        una sessione sana.  Proposta **P8**, non ancora nel
            #        documento: vedi l'intestazione di questo file.
            #
            #        §6.2 dice due cose che insieme non stanno in piedi:
            #        *«DEVONO valere la tela in vigore … e chi ne riceve altre
            #        chiude»* e *«gli stream sono indipendenti, quindi i
            #        fotogrammi possono arrivare fuori ordine»*.  ⇒ Il
            #        fotogramma aperto **prima** che l'`ADATTA_TELA` arrivasse
            #        al server porta la misura di prima, ed e' conforme.
            #        ⛔ E il server non puo' nemmeno sgombrare il tubo: §5.2 gli
            #        vieta di abbandonare un fotogramma **chiave**, che e' il
            #        piu' grosso e quindi il piu' probabile a essere in volo.
            #        ⭐ La cura e' la grazia di un secondo che §7.1 da' gia'
            #        alle coordinate di input (terza eccezione di §3).
            if (self.c.grazia_aperta
                    and (lar, alt) == self.c.tela_precedente):
                return self._decidi(Verdetto(
                    AMBIGUO, "RCP.md §6.2 contro §7.1",
                    f"il fotogramma e' {lar}x{alt}, cioe' la tela "
                    f"**precedente**, e la tela in vigore e' "
                    f"{self.c.tela_larghezza}x{self.c.tela_altezza} da un "
                    f"`TELA(ADATTATA)` appena passato: §6.2 alla lettera fa "
                    f"chiudere, e chiuderebbe una sessione in cui NESSUNO dei "
                    f"due ha sbagliato — il fotogramma era gia' in volo, e §6.2 "
                    f"stesso dice che i fotogrammi arrivano fuori ordine",
                    scostamento=4, propone="P8"))
            return self._chiuso_il_12_agosto(
                "P5", 4, "RCP.md §6.2",
                f"il fotogramma e' {lar}x{alt} e la tela IN VIGORE e' "
                f"{self.c.tela_larghezza}x{self.c.tela_altezza}, da "
                f"{self.c.tela_da}: §6.2 vuole che DEVANO coincidere",
                "RCP.md §6.2",
                f"il fotogramma e' {lar}x{alt} e la tela concessa e' "
                f"{self.c.tela_larghezza}x{self.c.tela_altezza}: «e' sempre "
                f"quella della tela» non dice che cosa fa chi riceve")

        # 8. ⛔ L'ORDINE — §6.2: si scarta un `numero` PRECEDENTE all'ultimo
        #    gia' consegnato, con l'aritmetica **modulo 2^32** e le differenze
        #    **con segno**.
        #    ⚠ Il modulo non e' pedanteria: a 60 fotogrammi al secondo il
        #      contatore gira dopo due anni e due mesi, e una sessione puo'
        #      durare di piu' (§6.2).  Un confronto `<` diretto farebbe
        #      scartare **ogni** fotogramma dopo il giro, per sempre.
        if self.c.ultimo_consegnato is not None:
            d = (num - self.c.ultimo_consegnato) & 0xFFFFFFFF
            if d >= 0x80000000 or d == 0:
                return self._decidi(Verdetto(
                    SCARTATO, "RCP.md §6.2",
                    f"`numero` {num} non e' successivo a "
                    f"{self.c.ultimo_consegnato} (differenza con segno "
                    f"{d - 0x100000000 if d >= 0x80000000 else d}): gli stream "
                    f"sono indipendenti e i fotogrammi arrivano fuori ordine",
                    scostamento=12))

        # 9. ⭐⛔ P6 — IL PRIMO FOTOGRAMMA E' UN DELTA.  Chiusa il 12 agosto
        #    2026, ed e' la riga che morde in QUESTA fase.
        #
        #    §5.2, primo punto delle «Le regole:»: *«⛔ il primo fotogramma che
        #    il server spedisce dopo `SESSIONE` DEVE essere una chiave
        #    (`0x0301`)»*.
        #    ⚠ Fino all'11 agosto un delta in apertura era **conforme a ogni
        #      riga del documento**, e la fase 2 — che consegna un fotogramma
        #      fermo — avrebbe mostrato spazzatura senza che nessuno avesse
        #      torto.  ⛔ E il client non aveva modo di accorgersene: §5.2 gli
        #      fa chiedere una chiave su un **buco** nei `numero`, e qui buchi
        #      non ce ne sono (e' il primo); e §5.2 stesso dichiara `[S]` che a
        #      un delta mancante il decodificatore **non solleva nessun errore**.
        if tipo == DELTA and not self.c.chiave_consegnata:
            return self._chiuso_il_12_agosto(
                "P6", 0, "RCP.md §5.2",
                "il primo fotogramma della sessione e' un DELTA: §5.2 vuole "
                "che il primo fotogramma dopo `SESSIONE` sia una chiave "
                "(0x0301)",
                "RCP.md §5.2",
                "il primo fotogramma della sessione e' un DELTA: nessuna riga "
                "obbliga il server a cominciare con una chiave, e il client "
                "non ha nessun buco da cui accorgersene")

    def _giudica_completo(self):
        """Lo stream e' finito con FIN e l'intestazione era buona."""
        num = self.campi["numero"]
        # ⛔ IL BUCO — §5.2: «il client DEVE mandare `RICHIEDI_CHIAVE` quando si
        #    accorge di un buco nella successione dei `numero`».  ⚠ E il buco
        #    e' **normale**: §6.2 dice che il contatore cresce anche per i
        #    fotogrammi che il server poi abbandona.
        if (self.c.ultimo_consegnato is not None
                and num != ((self.c.ultimo_consegnato + 1) & 0xFFFFFFFF)):
            self.c.chiedi_chiave = True
        self.c.ultimo_consegnato = num
        if self.campi["tipo"] == CHIAVE:
            self.c.chiave_consegnata = True
            self.c.chiedi_chiave = False
        return Verdetto(ACCETTATO, "RCP.md §6.2",
                        f"{'chiave' if self.campi['tipo'] == CHIAVE else 'delta'} "
                        f"n. {num}, {self.campi['larghezza']}x"
                        f"{self.campi['altezza']}, {self.byte_dati} byte di dati")


# ---------------------------------------------------------------------------
def intestazione(tipo=CHIAVE, codec=1, lar=1920, alt=1080, num=1, ist=0, inp=0):
    """I 28 byte di §6.2, in ordine di rete e senza un byte di riempimento."""
    return struct.pack("!HHIIIQI", tipo, codec, lar, alt, num, ist, inp)


# ===========================================================================
# ⛔ LE SEI RIGHE ENTRATE IN `RCP.md` IL 12 AGOSTO 2026, E I DUE CASI DI OGNUNA.
#
#    ⚠ Fino all'11 agosto questa tabella si chiamava `PROPOSTE` ed era un
#      elenco di cose **da chiedere** al coordinatore.  Adesso le righe sono
#      **normative** — stanno in `RCP.md` §2.5, §5.2, §6.2 — e questa tabella
#      dice due cose che un elenco di proposte non diceva:
#
#      ⛔ **dove sta la riga**, per andarla a rileggere invece di fidarsi;
#      ⛔ **quale caso la viola e quale la rispetta**, per nome.
#
#    ⭐ E i due nomi non sono documentazione: `regole_coperte()` li **cerca**
#       fra i casi e il giro stampa il conto.  Una regola che perdesse uno dei
#       due casi — o che ne citasse uno rinominato — diventa rossa qui, e non
#       fra sei mesi quando qualcuno se ne accorge.
REGOLE_NUOVE = {
    "P1": {
        "dove": "RCP.md §2.5, riga «video» della tabella",
        "dice": "Il server NON DEVE aprire uno stream video prima di aver "
                "spedito `SESSIONE`; chi ne riceve uno prima chiude con "
                "`ERRORE_PROTOCOLLO`.",
        "era": "derivata da §1 + §3 per chi riceve, e da NIENTE per chi manda",
        "viola": "prima-di-sessione",
        "rispetta": "dopo-sessione",
    },
    "P2": {
        "dove": "RCP.md §6.2, campo `numero`",
        "dice": "Il primo fotogramma di una sessione porta `numero = 1`; ⛔ **0 "
                "e' riservato** e vuol dire «nessun fotogramma», che e' il "
                "significato che §7.1 gli da' in `RICHIEDI_CHIAVE`.  ⛔ E al "
                "giro del contatore lo 0 **si salta**: da `0xFFFFFFFF` si "
                "passa a `1`.",
        "era": "lettura doppia — §6.2 non diceva da dove parte il contatore; e "
               "la cura stessa e' durata due ore prima che si vedesse che al "
               "giro del contatore lo `0` riservato tornava in circolo da solo",
        "viola": "numero-zero",
        "rispetta": "numero-uno",
    },
    "P3": {
        "dove": "RCP.md §2.5, riga `0x03` della tabella dei canali",
        "dice": "Il video vive **solo** su uno stream unidirezionale aperto dal "
                "server: un `0x03` sul canale di controllo e' "
                "`ERRORE_PROTOCOLLO`.",
        "era": "lettura doppia — §2.5 chiudeva il caso per 0x00 e 0x04 e non "
               "per il video",
        "viola": "video-sul-controllo",
        "rispetta": "video-su-unidirezionale",
    },
    "P4": {
        "dove": "RCP.md §6.2, terza riga di «La regola, in due righe»",
        "dice": "Uno stream video chiuso con **FIN prima dei 28 byte** "
                "dell'intestazione e' `ERRORE_PROTOCOLLO`: non e' un "
                "fotogramma corto, e' una lunghezza che non torna (§3).",
        "era": "derivata da §3, e §6.2 — dove chi implementa la guarda — taceva",
        "viola": "intestazione-27-byte",
        "rispetta": "chiave-senza-dati",
    },
    "P5": {
        "dove": "RCP.md §6.2, campi `largh.` e `altezza`",
        "dice": "In RCP/1 `largh.` e `altezza` **DEVONO** valere la **tela in "
                "vigore** — quella di `SESSIONE` (§4.5), oppure l'ultima "
                "concessa da `TELA` se e' stata adattata (§7.1); chi riceve "
                "una misura diversa chiude con `ERRORE_PROTOCOLLO`.",
        "era": "lettura doppia — «e' sempre quella della tela» descrive e non "
               "comanda, e nessuna riga diceva che cosa fa chi riceve.  ⛔ E "
               "per due ore la cura stessa e' stata sbagliata: diceva «la tela "
               "concessa in `SESSIONE`», che dopo un `ADATTA_TELA` uccide una "
               "sessione sana.  Corretta il 12 agosto 2026: «la tela IN VIGORE»",
        "viola": "misura-diversa-dalla-tela",
        "rispetta": "misura-dopo-adatta-tela",
    },
    "P6": {
        "dove": "RCP.md §5.2, primo punto delle «Le regole:»",
        "dice": "Il primo fotogramma che il server spedisce dopo `SESSIONE` "
                "**DEVE** essere una chiave (`0x0301`).",
        "era": "lettura doppia — un delta in apertura era conforme a ogni riga, "
               "e il client non aveva modo di accorgersene",
        "viola": "primo-fotogramma-delta",
        "rispetta": "primo-fotogramma-chiave",
    },
}


# ===========================================================================
# ⛔⛔ E LE PROPOSTE ANCORA **APERTE** — quel che `RCP.md` NON dice ancora.
#
#    ⚠ Stanno in una tabella **separata** da `REGOLE_NUOVE`, e la separazione e'
#      la cosa piu' importante di questo blocco: la' ci sono righe **normative**
#      che si vanno a rileggere nel documento, qui c'e' una cura che il
#      coordinatore non ha ancora applicato.  ⛔ Mescolarle vorrebbe dire che
#      fra un mese nessuno sa piu' quale delle due un banco sta facendo
#      rispettare — ed e' la forma **E5** («un "fatto" che era una deduzione
#      mai misurata») applicata al documento invece che al codice.
#
#    ⛔ E ogni proposta porta i **suoi** casi con l'atteso di OGGI: quello che
#       la fa vedere, e quelli che impediscono di scriverla troppo larga.
PROPOSTE_APERTE = {
    "P8": {
        "dove": "RCP.md §6.2 (i campi `largh.`/`altezza`) e §3 (l'elenco delle "
                "eccezioni, che diventerebbero sei)",
        "dice": "Dopo aver ricevuto un `TELA(ADATTATA)` il client **DEVE** "
                "accettare per **un secondo** i fotogrammi la cui misura vale "
                "la tela **precedente**, dipingendoli riscalati alla vista e "
                "scrivendolo nel registro; passato quel secondo sono "
                "`ERRORE_PROTOCOLLO`.  ⛔ E' la grazia che §7.1 da' gia' alle "
                "coordinate di input, scritta per il verso in cui manca.",
        "era": "⛔ **contraddizione interna, non lettura doppia**: §6.2 fa "
               "chiudere chi riceve una misura diversa dalla tela in vigore, e "
               "§6.2 stesso dice che i fotogrammi arrivano **fuori ordine**.  "
               "Due implementazioni conformi e attente producono lo **stesso** "
               "byte — la chiusura — e uccidono una sessione sana.  ⚠ Trovata "
               "**leggendo** la sera del 12 agosto 2026, `[?]` non misurata.",
        # ⛔ tre casi, e i due che pretendono ERRORE_PROTOCOLLO valgono quanto
        #    il primo: senza, la grazia diventa «per un secondo passa tutto».
        "casi": {"p8-in-volo-dopo-adatta-tela": AMBIGUO,
                 "p8-in-volo-fuori-grazia": ERRORE_PROTOCOLLO,
                 "p8-misura-di-nessuna-tela": ERRORE_PROTOCOLLO},
    },
}


def proposte_coperte(casi):
    """⛔ Come `regole_coperte`, per le proposte che il documento non ha ancora.

    ⚠ La differenza sta nella **forma della coppia**: una regola gia' entrata
      ha un caso che la viola (`ERRORE_PROTOCOLLO`) e uno che la rispetta
      (`ACCETTATO`); una proposta aperta ha il caso che la **fa vedere** —
      oggi `AMBIGUO`, perche' il documento non ha ancora deciso — e quelli che
      impediscono di scriverla **troppo larga**.  ⛔ Pretendere qui la stessa
      forma di la' vorrebbe dire far finta che la cura sia gia' applicata.
    """
    per_nome = {c["nome"]: c for c in casi}
    coperte, mancanti = [], []
    for sigla, p in PROPOSTE_APERTE.items():
        buchi = []
        for nome, atteso in p["casi"].items():
            c = per_nome.get(nome)
            if c is None:
                buchi.append(f"manca il caso «{nome}»")
            elif c["atteso"] != atteso:
                buchi.append(f"«{nome}» non pretende {atteso} ma {c['atteso']}")
        if buchi:
            mancanti.append((sigla, "; ".join(buchi)))
        else:
            coperte.append(sigla)
    return coperte, mancanti


def regole_coperte(casi):
    """⛔ Quante delle sei righe hanno DAVVERO un caso che le fa scattare.

    ⛔ Il conto lo **calcola** questa funzione cercando i nomi fra i casi: un
       numero scritto a mano in un commento e' il numero che nessuno ricalcola
       (`01-b5-violazioni.py`, rilievo R7.14 — tre numeri nei commenti e
       nessuno dei tre tornava con il file).

    Restituisce (coperte, mancanti), dove `mancanti` porta la sigla e **quale
    delle due meta'** manca: ⚠ «la regola c'e' ma il caso che la rispetta no»
    e «la regola non e' provata affatto» sono due difetti diversi, e il primo
    e' quello che lascia passare una regola scritta troppo larga.
    """
    per_nome = {c["nome"]: c for c in casi}
    coperte, mancanti = [], []
    for sigla, r in REGOLE_NUOVE.items():
        v, s = per_nome.get(r["viola"]), per_nome.get(r["rispetta"])
        buchi = []
        if v is None:
            buchi.append(f"manca il caso che la VIOLA («{r['viola']}»)")
        elif v["atteso"] != ERRORE_PROTOCOLLO:
            buchi.append(f"«{r['viola']}» non pretende ERRORE_PROTOCOLLO ma "
                         f"{v['atteso']}")
        if s is None:
            buchi.append(f"manca il caso che la RISPETTA («{r['rispetta']}»)")
        elif s["atteso"] != ACCETTATO:
            buchi.append(f"«{r['rispetta']}» non pretende ACCETTATO ma "
                         f"{s['atteso']}")
        if buchi:
            mancanti.append((sigla, "; ".join(buchi)))
        else:
            coperte.append(sigla)
    return coperte, mancanti


# ===========================================================================
# I CASI.  ⛔ Ciascuno dichiara la sua ATTESA **prima** di misurare: la colonna
#          «atteso» e' una PREVISIONE scritta nel file, non un commento sul
#          risultato (`LEZIONI.md` §1.11, `PIANO.md` §0.3 regola 4).
# ===========================================================================
CASI = []


def caso(nome, atteso, spiega, regola="", contesto=None, dove="uni"):
    def dec(f):
        CASI.append({"nome": nome, "atteso": atteso, "spiega": spiega,
                     "regola": regola, "contesto": contesto, "dove": dove,
                     "fabbrica": f})
        return f
    return dec


# ── L'inquadratura del canale (§2.5) ───────────────────────────────────────
@caso("canale-controllo-su-uni", ERRORE_PROTOCOLLO,
      "il canale di CONTROLLO (0x00) su uno stream unidirezionale del server: "
      "«il controllo vive solo sul primo stream bidirezionale»",
      "RCP.md §2.5")
def _():
    return [struct.pack("!HI", 0x0001, 0) + b"\x00" * 22], "fin"


@caso("canale-audio-su-stream", ERRORE_PROTOCOLLO,
      "il canale AUDIO (0x04) su uno stream: l'audio vive solo sui datagram.  "
      "⚠ Il carico e' l'intestazione di §6.3 ben formata — l'unica cosa storta "
      "e' lo stream",
      "RCP.md §2.5, §6.3")
def _():
    return [struct.pack("!HHQ", 0x0401, 2, 0) + b"\x00" * 16], "fin"


@caso("canale-ignoto", ERRORE_PROTOCOLLO,
      "un byte alto che non e' nessuno dei cinque di §2.5",
      "RCP.md §2.5")
def _():
    return [intestazione(tipo=0x0901)], "fin"


@caso("video-sul-controllo", ERRORE_PROTOCOLLO,
      "⭐⛔ **P3, il caso che la VIOLA** — un fotogramma BEN FORMATO scritto sul "
      "canale di controllo.  ⛔ E' l'unico posto in cui il server puo' "
      "sbagliare stream: §2.5 gli vieta di aprire stream bidirezionali, e il "
      "canale di controllo glielo ha aperto il client.  ⚠ Senza la riga del 12 "
      "agosto il client leggeva quei 28 byte con l'inquadratura di §6.1 e ne "
      "ricavava un messaggio inventato di 64 KiB",
      "RCP.md §2.5", dove="controllo")
def _():
    return [intestazione() + b"\x00" * 64], "fin"


@caso("video-su-unidirezionale", ACCETTATO,
      "⭐ **P3, il caso che la RISPETTA** — gli **stessi identici byte** del "
      "caso qui sopra, su uno stream unidirezionale del server.  ⛔ Senza "
      "questo caso, un giudice che rifiutasse il video **dovunque** — cioe' "
      "che avesse capito P3 come «il video non si accetta» invece che «il "
      "video solo di la'» — resterebbe verde sul caso che la viola",
      "RCP.md §6.2", dove="uni")
def _():
    return [intestazione() + b"\x00" * 64], "fin"


# ── Il tipo e il codec (§6.2) ──────────────────────────────────────────────
@caso("tipo-0x0300", ERRORE_PROTOCOLLO,
      "`tipo = 0x0300`: canale giusto, valore non definito — §6.2 dice «Altri "
      "valori: ERRORE_PROTOCOLLO»",
      "RCP.md §6.2")
def _():
    return [intestazione(tipo=0x0300) + b"\x00" * 64], "fin"


@caso("tipo-0x0303", ERRORE_PROTOCOLLO,
      "`tipo = 0x0303`: il valore subito dopo i due definiti.  ⚠ E' il caso "
      "che un `if (tipo >= 0x0301)` scritto in fretta lascia passare",
      "RCP.md §6.2")
def _():
    return [intestazione(tipo=0x0303) + b"\x00" * 64], "fin"


@caso("codec-3", ERRORE_PROTOCOLLO,
      "`codec = 3`: RCP/1 ne definisce due, 1 = HEVC e 2 = AV1",
      "RCP.md §6.2")
def _():
    return [intestazione(codec=3) + b"\x00" * 64], "fin"


@caso("codec-non-negoziato", ERRORE_PROTOCOLLO,
      "`codec = 2` (AV1) su una sessione in cui §4.3 aveva negoziato HEVC.  "
      "⛔ Il campo e' ben formato: l'unica violazione e' che contraddice la "
      "negoziazione, ed e' la sola regola che un giudice senza contesto non "
      "puo' applicare",
      "RCP.md §6.2, §4.3")
def _():
    return [intestazione(codec=2) + b"\x00" * 64], "fin"


# ── La lunghezza, e il FIN contro il RESET (§6.2) ──────────────────────────
@caso("intestazione-27-byte", ERRORE_PROTOCOLLO,
      "⛔ **P4, il caso che la VIOLA** — FIN dopo 27 byte: uno in meno dei 28.  "
      "Letta alla lettera, «la fine dello stream e' la fine del fotogramma» fa "
      "di questo un fotogramma con **meno un** byte di dati.  ⭐ Dal 12 agosto "
      "2026 la regola non si ricava piu' da §3: §6.2 la scrive",
      "RCP.md §6.2")
def _():
    return [intestazione()[:27]], "fin"


@caso("stream-vuoto", ERRORE_PROTOCOLLO,
      "FIN a zero byte.  ⚠ E' il caso in cui «zero» e «fallimento» si "
      "somigliano di piu': uno stream aperto e chiuso subito",
      "RCP.md §6.2")
def _():
    return [], "fin"


@caso("reset-a-meta", SCARTATO,
      "⭐ stream AZZERATO dopo 10 KB: si butta, ⛔ **non** si consegna al "
      "decodificatore, e si tratta come un buco.  ⛔ E la sessione RESTA VIVA: "
      "l'abbandono e' il caso normale di §5.1, non una violazione",
      "RCP.md §6.2, §5.1, §5.2")
def _():
    return [intestazione(), b"\x00" * 10240], "reset"


@caso("reset-prima-dell-intestazione", SCARTATO,
      "stream azzerato dopo 4 byte soli.  ⛔ Il giudizio DEVE guardare il "
      "reset **prima** dell'intestazione: quei quattro byte possono essere "
      "qualunque cosa, e leggerli darebbe `ERRORE_PROTOCOLLO` su un fotogramma "
      "che il server ha abbandonato di proposito",
      "RCP.md §6.2")
def _():
    return [b"\xff\xff\xff\xff"], "reset"


@caso("oltre-16-mib", ERRORE_PROTOCOLLO,
      "un fotogramma di 16 MiB + 1 byte.  ⛔ E il giudizio deve arrivare "
      "**mentre** i byte scorrono, «invece di continuare ad accumulare»",
      "RCP.md §6.2")
def _():
    def pezzi():
        yield intestazione()
        rimane = TETTO_FOTOGRAMMA - INTESTAZIONE + 1
        blocco = b"\x00" * (1 << 20)
        while rimane > 0:
            n = min(rimane, len(blocco))
            yield blocco[:n]
            rimane -= n
    return pezzi(), "fin"


@caso("16-mib-esatti", ACCETTATO,
      "⭐ un fotogramma lungo **esattamente** 16 MiB: il tetto e' un massimo, "
      "non un limite superiore stretto.  ⚠ Senza questo caso «> 16 MiB» e "
      "«>= 16 MiB» danno lo stesso verde su tutto il resto del banco",
      "RCP.md §6.2")
def _():
    def pezzi():
        yield intestazione()
        rimane = TETTO_FOTOGRAMMA - INTESTAZIONE
        blocco = b"\x00" * (1 << 20)
        while rimane > 0:
            n = min(rimane, len(blocco))
            yield blocco[:n]
            rimane -= n
    return pezzi(), "fin"


# ── Lo stato (§1, §3, I3) ──────────────────────────────────────────────────
@caso("prima-di-sessione", ERRORE_PROTOCOLLO,
      "⭐⛔ **P1, il caso che la VIOLA** — un fotogramma ben formato **prima di "
      "`SESSIONE`**, cioe' prima che la tela sia concordata: il client "
      "riceverebbe un fotogramma di cui non conosce ne' la misura ne' il "
      "codec.  E' l'invariante **I3** sul filo — *chi non passa dal validatore "
      "non riceve un pixel* — e dal 12 agosto 2026 §2.5 la scrive anche per "
      "chi **manda**",
      "RCP.md §2.5",
      contesto={"sessione_aperta": False})
def _():
    return [intestazione() + b"\x00" * 64], "fin"


@caso("dopo-sessione", ACCETTATO,
      "⭐ **P1, il caso che la RISPETTA** — gli **stessi identici byte**, con "
      "`SESSIONE` gia' spedita.  ⛔ Senza questo caso il banco non "
      "distinguerebbe «il video prima di `SESSIONE` cade» da «il video cade», "
      "e la seconda lettura fa fallire la fase 2 per intero",
      "RCP.md §6.2",
      contesto={"sessione_aperta": True})
def _():
    return [intestazione() + b"\x00" * 64], "fin"


# ── I numeri (§6.2, §6.0, §7.1) ────────────────────────────────────────────
@caso("numero-zero", ERRORE_PROTOCOLLO,
      "⭐⛔ **P2, il caso che la VIOLA** — `numero = 0` sul primo fotogramma.  "
      "Dal 12 agosto 2026 §6.2 riserva lo zero: **il primo porta 1**.  ⚠ Il "
      "caso concreto che la riga chiude: il client decodifica il fotogramma 0, "
      "poi manda `RICHIEDI_CHIAVE(ultimo_numero = 0)` — e il server non puo' "
      "sapere se voglia dire «ho decodificato il fotogramma 0» o «non ne ho "
      "decodificato nessuno» (§7.1), cioe' il sentinella implicito che §6.0 "
      "vieta",
      "RCP.md §6.2")
def _():
    return [intestazione(num=0) + b"\x00" * 64], "fin"


@caso("numero-zero-al-giro", ERRORE_PROTOCOLLO,
      "⭐⛔ **P2 dall'altra parte: lo `0` che RITORNA** — il fotogramma dopo il "
      "4294967295 porta `numero = 0`.  ⛔ E' la falla che P2 aveva lasciata "
      "aperta per due ore: riservava lo `0` e non diceva che al giro del "
      "contatore va **saltato**, cosi' il valore riservato tornava in circolo "
      "da solo dopo due anni e due mesi di sessione.  ⚠ Il sintomo sarebbe "
      "arrivato **una volta sola nella vita di una sessione**, e nessuno "
      "l'avrebbe collegato a `RICHIEDI_CHIAVE`.  Chiusa da §6.2 il 12 agosto "
      "2026: da `0xFFFFFFFF` si passa a `1`",
      "RCP.md §6.2",
      contesto={"ultimo_consegnato": 0xFFFFFFFF, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=0) + b"\x00" * 64], "fin"


@caso("numero-uno", ACCETTATO,
      "⭐ **P2, il caso che la RISPETTA** — `numero = 1` sul primo fotogramma, "
      "che e' il valore che §6.2 impone.  ⛔ E' anche il caso che tiene onesto "
      "il confronto: un giudice che rifiutasse **ogni** `numero` basso "
      "sembrerebbe severissimo e sarebbe rotto",
      "RCP.md §6.2")
def _():
    return [intestazione(num=1) + b"\x00" * 64], "fin"


@caso("misura-diversa-dalla-tela", ERRORE_PROTOCOLLO,
      "⭐⛔ **P5, il caso che la VIOLA** — un fotogramma 1280x720 su una tela in "
      "vigore 1920x1080, e ⛔ **nessun `ADATTA_TELA` prima**.  Dal 12 agosto "
      "2026 §6.2 dice che `largh.` e `altezza` **DEVONO** valere la tela in "
      "vigore, e che chi ne riceve altre chiude.  ⚠ Prima le due letture erano "
      "tutt'e due difendibili — chiudere per §3, o riscalare come il client fa "
      "gia' per la **vista**",
      "RCP.md §6.2")
def _():
    return [intestazione(lar=1280, alt=720) + b"\x00" * 64], "fin"


@caso("misura-dopo-adatta-tela", ACCETTATO,
      "⭐⛔ **P5, il caso che la RISPETTA, e ha corretto `RCP.md`** — gli "
      "**stessi identici byte** del caso qui sopra, ma prima e' passato un "
      "`TELA(ADATTATA, 1280, 720)` sul canale di controllo (§7.1).  ⛔ Per due "
      "ore §6.2 ha detto «la tela concessa in `SESSIONE`», e con quella riga "
      "questo caso sarebbe `ERRORE_PROTOCOLLO`: il client avrebbe ucciso la "
      "sessione perche' l'utente ha trascinato una finestra — che e' "
      "**esattamente** la scena che §7.1 protegge con la sua eccezione 4.  "
      "⚠ Senza questo caso la regola nuova sarebbe severa quanto quella "
      "sbagliata di prima, e nessun banco lo direbbe",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720)})
def _():
    return [intestazione(lar=1280, alt=720) + b"\x00" * 64], "fin"


@caso("misura-uguale-a-una-tela-diversa", ACCETTATO,
      "⭐⛔ **P5, il caso che la RISPETTA, e non e' il fotogramma predefinito** "
      "— 1280x720 su una tela **concessa** 1280x720.  ⛔ Sono gli **stessi "
      "byte** del caso che la viola: cambia solo la tela concordata in "
      "`SESSIONE`.  ⚠ Senza questo caso, un giudice che avesse scritto "
      "`if (lar, alt) != (1920, 1080)` — cioe' la misura predefinita al posto "
      "della tela concessa — sarebbe verde su tutti e ventisette gli altri "
      "casi, e rosso sulla prima sessione a 720p",
      "RCP.md §6.2",
      contesto={"tela": (1280, 720)})
def _():
    return [intestazione(lar=1280, alt=720) + b"\x00" * 64], "fin"


# ── ⛔⛔ D14 — I FOTOGRAMMI IN VOLO, e la proposta **P8** ───────────────────
#    I tre casi vanno letti insieme: il primo mostra la sessione sana uccisa,
#    il secondo e il terzo impediscono di curarla con una regola troppo larga.
@caso("p8-in-volo-dopo-adatta-tela", AMBIGUO,
      "⛔⛔ **D14, LA SCENA CHE UCCIDE UNA SESSIONE SANA** — la tela era "
      "1920x1080, e' passato un `TELA(ADATTATA, 1280, 720)` (§7.1), e adesso "
      "arriva il fotogramma **aperto prima**, che porta 1920x1080.  ⛔ §6.2 "
      "alla lettera dice `ERRORE_PROTOCOLLO` — e §6.2 **stesso** dice che «gli "
      "stream sono indipendenti, quindi i fotogrammi possono arrivare fuori "
      "ordine».  ⇒ Nessuno dei due lati ha sbagliato, e la sessione cade.  "
      "⭐ La cura e' **P8**, che e' la grazia di un secondo gia' scritta in "
      "§7.1 per le coordinate di input.  ⚠ Finche' il coordinatore non "
      "l'applica, l'esito onesto e' `AMBIGUO`: un verde su `ERRORE_PROTOCOLLO` "
      "qui certificherebbe che un client conforme deve uccidere una sessione "
      "sana, e chi scrive il prodotto lo implementerebbe",
      "RCP.md §6.2 contro §7.1",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720)})
def _():
    return [intestazione(lar=1920, alt=1080, num=41) + b"\x00" * 64], "fin"


@caso("p8-in-volo-fuori-grazia", ERRORE_PROTOCOLLO,
      "⭐⛔ **P8 non e' un permesso permanente** — gli **stessi identici byte** "
      "del caso qui sopra, ma il **secondo** di grazia e' passato "
      "(`grazia_scaduta`).  ⛔ Da li' in poi un fotogramma alla misura vecchia "
      "non e' piu' uno in volo: e' un server che continua a catturare a una "
      "tela che non e' piu' in vigore, ed e' §6.2 senza sconti.  ⚠ Senza "
      "questo caso, P8 scritta come «dopo un `TELA` la misura vecchia si "
      "accetta» spegnerebbe la regola per sempre, e nessun banco lo direbbe.  "
      "⛔ Il secondo lo **dichiara** questo caso: qui non c'e' nessun orologio",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720),
                "grazia_scaduta": True})
def _():
    return [intestazione(lar=1920, alt=1080, num=41) + b"\x00" * 64], "fin"


@caso("p8-misura-di-nessuna-tela", ERRORE_PROTOCOLLO,
      "⭐⛔ **P8 copre UNA misura, non «tutto per un secondo»** — stessa scena "
      "e stessa grazia aperta, ma il fotogramma porta 800x600: ⛔ ne' la tela "
      "in vigore (1280x720) ne' la precedente (1920x1080).  Non e' un "
      "fotogramma in volo, e' un campo sbagliato — §6.2 chiude, e deve "
      "chiudere.  ⚠ Senza questo caso una grazia scritta «durante il cambio di "
      "tela la misura non si controlla» passerebbe il caso che uccide e "
      "spegnerebbe P5 nella finestra in cui il server e' piu' probabile che "
      "sbagli.  ⭐ E' la seconda meta' che alla prima stesura di P5 mancava",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720)})
def _():
    return [intestazione(lar=800, alt=600, num=41) + b"\x00" * 64], "fin"


@caso("primo-fotogramma-delta", ERRORE_PROTOCOLLO,
      "⭐⛔ **P6, il caso che la VIOLA, e morde proprio in questa fase** — il "
      "PRIMO fotogramma della sessione e' un delta.  Dal 12 agosto 2026 §5.2 "
      "vuole una chiave.  ⚠ Prima era conforme a **ogni riga** del documento, "
      "e il client non aveva modo di accorgersene: nessun buco nei `numero` "
      "(e' il primo) e il decodificatore non solleva errori su un delta orfano "
      "— il sintomo sarebbe stato *«il desktop compare a pezzi»*, che non "
      "nomina ne' il protocollo ne' la chiave",
      "RCP.md §5.2")
def _():
    return [intestazione(tipo=DELTA) + b"\x00" * 64], "fin"


@caso("primo-fotogramma-chiave", ACCETTATO,
      "⭐ **P6, il caso che la RISPETTA** — il primo fotogramma della sessione "
      "e' una chiave (`0x0301`).  ⛔ E' il fotogramma che la fase 2 esiste per "
      "consegnare, ed e' qui col suo nome perche' la riga di §5.2 abbia le due "
      "facce e non una",
      "RCP.md §6.2")
def _():
    return [intestazione(tipo=CHIAVE) + b"\x00" * 64], "fin"


@caso("delta-dopo-la-chiave", ACCETTATO,
      "⭐⛔ **P6, la seconda faccia: un delta che NON e' il primo** — chiave 4 "
      "gia' consegnata, arriva il delta 5.  ⚠ Senza questo caso, un giudice "
      "che avesse capito §5.2 come «i delta non si accettano» invece che «il "
      "PRIMO dev'essere una chiave» resterebbe verde su tutto il banco — e "
      "fermerebbe il video dalla fase 3 in poi, dove i delta sono il 99 % dei "
      "fotogrammi",
      "RCP.md §6.2",
      contesto={"ultimo_consegnato": 4, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=5) + b"\x00" * 64], "fin"


@caso("fuori-ordine", SCARTATO,
      "il fotogramma 7 arriva dopo che il 9 e' stato consegnato: si scarta.  "
      "⛔ E si SCARTA, non si chiude: gli stream sono indipendenti e i "
      "fotogrammi fuori ordine sono il caso normale di §5.1",
      "RCP.md §6.2",
      contesto={"ultimo_consegnato": 9, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=7) + b"\x00" * 64], "fin"


@caso("ripetuto", SCARTATO,
      "lo stesso `numero` due volte: la differenza con segno vale zero, che "
      "non e' «successivo».  ⚠ Senza questo caso un `d < 0x80000000` lascia "
      "passare il duplicato e il decodificatore riceve due volte lo stesso "
      "fotogramma",
      "RCP.md §6.2",
      contesto={"ultimo_consegnato": 9, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=9) + b"\x00" * 64], "fin"


@caso("modulo-2-32", ACCETTATO,
      "⭐ il fotogramma **1** dopo il 4294967295: e' **successivo**, non "
      "precedente.  §6.2 vuole l'aritmetica modulo 2^32 con le differenze con "
      "segno, ⛔ e un confronto `<` diretto farebbe scartare **ogni** "
      "fotogramma dopo il giro, per sempre — a 60 al secondo il contatore gira "
      "dopo due anni e due mesi, e una sessione puo' durare di piu'.  ⭐⛔ E "
      "che dopo `0xFFFFFFFF` venga **1 e non 0** adesso e' una RIGA di §6.2 — "
      "*«al giro del contatore lo 0 si salta»*, aggiunta il 12 agosto 2026 — "
      "mentre fino a quel giorno era una scelta di questo banco: P2 riservava "
      "lo `0` e nessuna riga impediva al contatore di ripassarci sopra da solo",
      "RCP.md §6.2",
      contesto={"ultimo_consegnato": 0xFFFFFFFF, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=1) + b"\x00" * 64], "fin"


@caso("buco-nella-successione", ACCETTATO,
      "⭐ il fotogramma 12 dopo il 9: si ACCETTA — un buco e' normale, §6.2 "
      "dice che il contatore cresce anche per i fotogrammi abbandonati — ⛔ e "
      "il client DEVE chiedere una chiave.  ⚠ E' il caso in cui «accettato» da "
      "solo non basta: si guarda anche `chiedi_chiave`",
      "RCP.md §6.2, §5.2",
      contesto={"ultimo_consegnato": 9, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=12) + b"\x00" * 64], "fin"


# ── I verdi attesi: quel che DEVE passare ──────────────────────────────────
@caso("chiave-buona", ACCETTATO,
      "⭐ il fotogramma che la fase 2 esiste per consegnare: chiave, HEVC, "
      "1920x1080, numero 1.  ⛔ Senza questo caso il banco potrebbe rifiutare "
      "tutto e sembrare severissimo",
      "RCP.md §6.2")
def _():
    return [intestazione() + b"\x00" * 4096], "fin"


@caso("chiave-senza-dati", ACCETTATO,
      "⭐ 28 byte esatti e FIN: un fotogramma con **zero** byte di dati.  "
      "⚠ Nessuna riga di `RCP.md` lo vieta, e questo caso e' qui per "
      "dichiararlo invece di scoprirlo: e' legale, e passera' al "
      "decodificatore che lo rifiutera' lui.  ⛔ Se un giorno si decidesse che "
      "e' un errore, la riga va in `RCP.md`, non in un `if` del client",
      "RCP.md §6.2")
def _():
    return [intestazione()], "fin"


@caso("istante-zero", ACCETTATO,
      "⭐ `istante = 0`.  §6.2: «non e' un'ora, e' un orologio monotono che "
      "parte da un punto qualunque» — e zero e' un punto qualunque.  ⚠ Un "
      "giudice che lo rifiutasse starebbe inventando un sentinella che §6.0 "
      "vieta",
      "RCP.md §6.2")
def _():
    return [intestazione(ist=0) + b"\x00" * 64], "fin"


@caso("input-zero", ACCETTATO,
      "⭐ `input = 0`, che §6.2 dichiara essere «nessuno».  E' il valore che "
      "porta **ogni** fotogramma della fase 2, dove non esiste input",
      "RCP.md §6.2")
def _():
    return [intestazione(inp=0) + b"\x00" * 64], "fin"


@caso("dati-a-pezzetti", ACCETTATO,
      "⭐ l'intestazione spezzata in sette pezzi da quattro byte.  ⛔ Uno "
      "stream QUIC arriva a pezzi di misura qualunque, e un giudice che "
      "leggesse i 28 byte da un solo `recv` sarebbe verde su ogni banco e "
      "rosso sulla prima rete vera",
      "RCP.md §6.2")
def _():
    g = intestazione()
    return [g[i:i + 4] for i in range(0, 28, 4)] + [b"\x00" * 64], "fin"


# ===========================================================================
# ⛔ I GUASTI, E OGNUNO ROMPE UNA PROPRIETA' SOLA — `PIANO.md` §0.3 regola 4.
#
#    «Un banco che non e' mai diventato rosso non e' pulito: e' NON
#    CERTIFICATO» (`01-b12-guasti.py`).  ⛔ E la marca ha DUE meta': il giro
#    guasto la deve dire **e il giro sano NON la deve gia' dire** — il criterio
#    che l'11 agosto 2026 mancava proprio al banco che certifica gli altri
#    undici (rilievo R12-A.3).
GUASTI = {
    "G1": {
        "titolo": "l'intestazione letta di 32 byte invece che di 28",
        "rompe": "la misura dell'intestazione (§6.2)",
        "dimostra":
            "⛔ E' il difetto **storico** di questo campo: `RCP.md` §6.2 e' "
            "stato corretto il 9 agosto 2026 perche' il disegno dava «… 24 │ "
            "32», cioe' quattro byte di riempimento mai dichiarati.  Con 32, "
            "il giudice mangia quattro byte di dati dentro l'intestazione: "
            "ogni fotogramma corto diventa «intestazione corta» e ogni "
            "fotogramma lungo si sposta di quattro byte.  ⭐ Un banco che non "
            "avesse un caso da 28 byte esatti (`chiave-senza-dati`) NON "
            "vedrebbe questo guasto.",
        # ⭐ Questa marca e' piu' forte delle altre due, e va detto: non dice
        #    «un caso e' rosso», dice **il numero sbagliato**.  Distingue il
        #    rosso del guasto dal rosso di un banco che crolla.
        "marca": "l'intestazione ne vuole 32",
    },
    "G2": {
        "titolo": "il giudice accetta anche `tipo = 0x0300`",
        "rompe": "la regola di rigore sul tipo (§3, §6.2)",
        "dimostra":
            "⛔ E' l'indulgenza che `RCP.md` §3 esiste per togliere, nella sua "
            "forma piu' innocua: un valore in piu' in un `set`.  ⭐ Il guasto "
            "**non rompe niente di visibile** — tutti i fotogrammi buoni "
            "continuano a passare — e si vede solo dal caso che deve fallire.  "
            "Un banco fatto di soli verdi attesi resterebbe verde.",
        "marca": "tipo-0x0300: ERRORE_PROTOCOLLO -> ACCETTATO",
    },
    "G3": {
        "titolo": "uno stream AZZERATO trattato come uno chiuso con FIN",
        "rompe": "la distinzione fra abbandono e fotogramma completo (§6.2)",
        "dimostra":
            "⛔ E' **esattamente** il difetto che il rilievo R1.7 ha trovato in "
            "`RCP.md` la sera del 9 agosto 2026: senza le due parole «ma solo "
            "se lo stream e' finito con un FIN», *«un fotogramma abbandonato e "
            "uno completo avevano lo stesso aspetto»* — forma d'errore **E8**. "
            "⭐ Col guasto, i 10 KB di un fotogramma abbandonato finiscono al "
            "decodificatore: mezza immagine, o un rifiuto che nessuno collega "
            "all'abbandono.",
        "marca": "reset-a-meta: SCARTATO -> ACCETTATO",
    },
    # ⭐⛔ G5 — E QUESTO GUASTO NON E' INVENTATO: E' IL GIUDICE DI IERI MATTINA.
    "G5": {
        "titolo": "le quattro righe del 12 agosto tornano a essere ambiguita'",
        "rompe": "le quattro letture doppie chiuse da `RCP.md` il 12 agosto "
                 "2026 (P2 §6.2, P3 §2.5, P5 §6.2, P6 §5.2)",
        "dimostra":
            "⛔ E' **lo stato di questo stesso file la mattina del 12 agosto "
            "2026**, prima che il coordinatore applicasse le sette righe — "
            "come **G4** e' lo stato di oggi di `01-b4-validatore.py`.  ⭐ Un "
            "guasto preso dalla storia vera vale piu' di uno inventato: "
            "dimostra che il banco sa distinguere il documento di oggi da "
            "quello di ieri, che e' precisamente il modo in cui una "
            "certificazione scade senza che nessuno se ne accorga.  ⚠ E il "
            "guasto **non fa cadere niente**: i quattro casi diventano "
            "`AMBIGUO`, cioe' *«nessuno ha sbagliato»* — l'esito piu' "
            "indulgente che questo banco abbia.  Un banco che contasse solo i "
            "rossi lo lascerebbe passare.",
        # ⛔ Quattro casi cambiano, e la marca ne cita **uno**: basta e avanza,
        #    perche' la seconda meta' del criterio (R12-A.3) chiede che il giro
        #    sano NON la dica — e da sano `numero-zero` esce ERRORE_PROTOCOLLO
        #    atteso ed ERRORE_PROTOCOLLO visto.
        "marca": "numero-zero: ERRORE_PROTOCOLLO -> AMBIGUO",
    },
}


# ===========================================================================
VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def riga(colore, segno, nome, testo):
    print(f"    {colore}{segno}{GRIGIO}  {nome:30s} {testo}")


def gira_caso(c, guasti):
    """⛔ Restituisce (esito_visto, verdetto, contesto), e non giudica: giudicare
       e' di chi chiama, che ha in mano l'atteso.  Tenere le due cose insieme
       fa scrivere `if visto != atteso: atteso = visto` senza accorgersene."""
    campi = dict(c["contesto"] or {})
    ctx = Contesto(tela=campi.pop("tela", (1920, 1080)),
                   codec_negoziato=campi.pop("codec_negoziato", 1),
                   sessione_aperta=campi.pop("sessione_aperta", True))
    # ⛔ `adatta_tela` NON e' un campo: e' un messaggio arrivato sul filo
    #    (§7.1), e va fatto passare per il metodo — cosi' il contesto si porta
    #    dietro anche DA DOVE viene la tela in vigore, che e' meta' del
    #    verdetto di P5.  ⚠ Un `setattr` diretto avrebbe cambiato i numeri
    #    lasciando `tela_da` a dire «SESSIONE», cioe' un verdetto che nomina
    #    la sezione sbagliata.
    adatta = campi.pop("adatta_tela", None)
    # ⛔ E nemmeno il **secondo** di grazia di §7.1 e' un campo: e' tempo che
    #    passa, e non viaggia sul filo.  Il caso lo dichiara, questo banco non
    #    lo misura, e la differenza sta scritta in `scade_la_grazia()`.
    grazia_scaduta = campi.pop("grazia_scaduta", False)
    for k, v in campi.items():
        setattr(ctx, k, v)
    if adatta is not None:
        # ⛔ `grazia=True`: questo banco porta i casi di D14, quindi la chiede.
        #    ⚠ Chi non la chiede — `01-b4-validatore.py`, per esempio — giudica
        #    il documento di oggi, ed e' quel che deve fare.
        ctx.adatta_tela(*adatta, grazia=True)
    if grazia_scaduta:
        ctx.scade_la_grazia()
    g = Giudice(ctx, dove=c["dove"], guasti=guasti)
    pezzi, come = c["fabbrica"]()
    for p in pezzi:
        g.arrivano(p)
        if g.verdetto is not None:
            break          # ⛔ chi ha gia' deciso smette di leggere: e' §6.2
    v = g.finisce(come) if g.verdetto is None else g.verdetto
    return v.esito, v, ctx


def sezione_principale(r):
    """La PRIMA sezione citata, che e' quella che regge il verdetto.

    ⛔ Questa funzione e' nata da un rosso su giudizio giusto, al primo giro
       del banco — 12 agosto 2026.  Il confronto era
       `v.regola.split(" (")[0] == c["regola"].split(" (")[0]`, cioe'
       pretendeva che il verdetto citasse **tutte** le sezioni che la
       previsione elenca: `«RCP.md §6.2»` contro `«RCP.md §6.2, §5.1, §5.2»`
       dava **rosso**, e l'esito era ACCETTATO contro ACCETTATO.

    ⚠ Quattro casi su ventisette, tutti con il giudizio esatto: e' la forma
      che questo progetto paga piu' spesso — **il banco che accusa il
      prodotto** — e stavolta e' costata dieci minuti perche' il banco
      stampava «esito giusto, REGOLA sbagliata» invece di «rosso».  ⛔ Un
      controllo che non dice PERCHE' e' rosso manda a cercare dalla parte
      sbagliata: quella riga e' rimasta, e ha fatto il suo mestiere.

    ⭐ La regola giusta: il verdetto DEVE citare la sezione **portante**; le
       altre che la previsione elenca sono il contorno, e pretenderle sarebbe
       pretendere una formulazione, non un giudizio.
    """
    return r.split(",")[0].split(" (")[0].strip()


def conta(casi):
    """⛔ I numeri li CALCOLA questa funzione — mai un commento.

    `01-b5-violazioni.py` rilievo R7.14: tre numeri scritti a mano nei
    commenti, e **nessuno dei tre tornava con il file**.
    """
    return {
        "violazioni": sum(1 for c in casi if c["atteso"] == ERRORE_PROTOCOLLO),
        "scarti": sum(1 for c in casi if c["atteso"] == SCARTATO),
        "verdi": sum(1 for c in casi if c["atteso"] == ACCETTATO),
        "ambigui": sum(1 for c in casi if c["atteso"] == AMBIGUO),
    }


def giro(a, guasti=(), silenzioso=False):
    """Un giro intero.  Restituisce (guastati, ambigui, marche, righe)."""
    casi = [c for c in CASI if not a.solo or a.solo in c["nome"]]
    if not casi:
        # ⛔ ZERO CASI NON E' «TUTTI PASSATI» — rilievo R7.15.
        print(f"    {ROSSO}⛔ «--solo {a.solo}» ha selezionato ZERO casi su "
              f"{len(CASI)}: non c'e' niente da misurare{GRIGIO}")
        print("       Questo NON e' un verde.  I nomi si leggono con --elenco.")
        return None
    guastati, ambigui, righe = 0, [], []
    testo_intero = []
    for c in casi:
        try:
            visto, v, ctx = gira_caso(c, guasti)
            errore = None
        except Exception as e:   # noqa: BLE001 — il tipo dell'errore E' la misura
            visto, v, ctx, errore = None, None, None, f"{type(e).__name__}: {e}"
        atteso = c["atteso"]
        ok = (errore is None and visto == atteso)
        # ⛔ E LA REGOLA CITATA SI CONFRONTA, non si stampa soltanto: un rosso
        #    con la sezione sbagliata accanto passa per un rosso giusto.
        regola_ok = (errore is None and c["regola"]
                     and sezione_principale(v.regola)
                     == sezione_principale(c["regola"]))
        if ok and c["regola"] and not regola_ok:
            ok = False
            errore = (f"esito giusto, ma la SEZIONE PORTANTE non torna: il "
                      f"verdetto cita «{sezione_principale(v.regola)}», la "
                      f"previsione «{sezione_principale(c['regola'])}»")
        # ⛔ e i casi che chiedono qualcosa in piu' del solo esito
        if ok and c["nome"] == "buco-nella-successione" and not ctx.chiedi_chiave:
            ok, errore = False, ("accettato, ma il client non si e' segnato di "
                                 "dover chiedere una chiave (§5.2)")
        if ok and c["nome"] == "reset-a-meta" and not ctx.chiedi_chiave:
            ok, errore = False, ("scartato, ma non trattato come un buco: "
                                 "§6.2 lo impone (§5.2)")
        testo = (errore if errore else str(v))
        righe.append({"nome": c["nome"], "atteso": atteso, "visto": visto,
                      "esito": bool(ok), "regola_vista": v.regola if v else None,
                      "dice": v.dice if v else None, "errore": errore})
        # ⛔ L'USCITA SU CUI SI CERCA LA MARCA PORTA `nome: atteso -> visto`.
        #
        #    Alla prima certificazione le marche di G2 e G3 erano i NOMI dei
        #    casi (`tipo-0x0300`, `reset-a-meta`), e non comparivano: il nome
        #    del caso sta nella riga stampata, non nel testo del verdetto, e
        #    `--certifica` gira in silenzio.  ⛔ Ma la cura non e' «cerchiamo
        #    anche nella riga stampata»: una marca che e' il nome del caso
        #    compare **anche nel giro sano**, dove quel caso passa — cioe'
        #    fallirebbe la seconda meta' del criterio (R12-A.3).
        # ⭐ `nome: atteso -> visto` e' una marca vera: nel giro sano atteso e
        #    visto coincidono sempre, quindi `X: A -> B` con A != B esiste
        #    **soltanto** quando qualcosa e' rotto.
        testo_intero.append(f"{c['nome']}: {atteso} -> {visto}    {testo}")
        if atteso == AMBIGUO:
            # ⛔ UN AMBIGUO NON E' UN GUASTO, E NON E' UN VERDE.
            #    Il caso e' verde se il giudice **riconosce** l'ambiguita';
            #    quel che resta rosso e' `RCP.md`, e si conta a parte.
            if ok:
                ambigui.append((c["nome"], v.propone, v.dice))
                if not silenzioso:
                    riga(GIALLO, "??", c["nome"],
                         f"⭐ RCP.md ammette due letture — proposta "
                         f"{v.propone or '?'}")
                continue
        if not silenzioso:
            riga(VERDE if ok else ROSSO, "OK" if ok else "NO", c["nome"], testo)
        if not ok:
            guastati += 1
            if not silenzioso:
                print(f"        atteso {atteso}, visto {visto}")
                print(f"        {c['spiega']}")
    return guastati, ambigui, righe, "\n".join(testo_intero)


def scrivi_esito(a, rec):
    """⛔ Una riga per giro, con l'ora e la scena, e si sincronizza subito.

    ⚠ Un registro assente e un registro vuoto non devono avere lo stesso
      aspetto: senza `--uscita` si dice, non si tace.
    """
    if not a.uscita:
        print(f"    ⚠ nessun --uscita: questo giro NON lascia registro")
        return False
    fuori = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "banco": "F2.4",
             "scena": "nessuna rete e nessun server: i fotogrammi li fabbrica "
                      "il banco, e il giudice li legge come li leggerebbe da "
                      "uno stream QUIC (a pezzi, senza tenere i dati)",
             "macchina": os.uname().nodename, "python": sys.version.split()[0]}
    fuori.update(rec)
    try:
        with open(a.uscita, "a") as f:
            f.write(json.dumps(fuori, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except OSError as e:
        print(f"    {ROSSO}⛔ il registro «{a.uscita}» non si scrive: {e}{GRIGIO}")
        return False
    return True


def controllo_positivo():
    """⛔ IN CODA A OGNI ESECUZIONE: lo strumento sa trovare qualcosa che c'e'?

    `LEZIONI.md` §1.9, seconda regola.  Qui la domanda ha una risposta
    esatta e a costo zero: si innesta **G2** — un guasto che non rompe niente
    di visibile — e si verifica che il caso `tipo-0x0300` diventi rosso.

    ⚠ Se questo controllo passasse **anche a giudice sano**, vorrebbe dire che
      quel caso e' rosso sempre, cioe' che il verde di poco fa non era un
      verde.  Si guardano tutt'e due i giri, non uno.
    """
    class Finto:
        solo, uscita = "tipo-0x0300", ""
    sano = giro(Finto(), guasti=(), silenzioso=True)
    guasto = giro(Finto(), guasti=("G2",), silenzioso=True)
    if sano is None or guasto is None:
        return False, "il caso del controllo positivo non esiste piu'"
    if sano[0] != 0:
        return False, (f"⛔ `tipo-0x0300` e' rosso anche a giudice SANO: il "
                       f"verde di questo giro non vale niente")
    if guasto[0] != 1:
        return False, (f"⛔ col guasto G2 innestato `tipo-0x0300` resta VERDE: "
                       f"questo banco non sa vedere il guasto che cerca")
    return True, ("G2 innestato -> `tipo-0x0300` rosso; G2 tolto -> verde.  "
                  "Lo strumento sa trovare quel che c'e'")


def certifica(a):
    """⛔ sano N -> guasto M -> risanato N, e sono TRE esecuzioni per guasto.

    `01-b12-guasti.py`: *«"e' diventato rosso" non vuol dire niente se non era
    verde prima»*, e il terzo passo e' il piu' insidioso da perdere — senza,
    «il banco vede il guasto» e «il banco e' rimasto rotto» hanno lo stesso
    aspetto.
    """
    print(f"\n== ⛔ LA CERTIFICAZIONE — sano -> guasto -> risanato, "
          f"{len(GUASTI)} guasti")
    print(f"   ⛔ Gli attesi sono scritti in `--elenco`, PRIMA di questo giro\n")
    tutto_bene, righe = True, []
    sano = giro(a, guasti=(), silenzioso=True)
    if sano is None:
        return 2
    n_sano, _, _, testo_sano = sano
    print(f"    sano: {n_sano} guasti")
    for sigla, g in GUASTI.items():
        rotto = giro(a, guasti=(sigla,), silenzioso=True)
        n_rotto, _, _, testo_rotto = rotto
        marca = g["marca"]
        # ⛔ LA MARCA HA DUE META', e la seconda si dimentica — R12-A.3.
        vista = marca in testo_rotto
        gia = marca in testo_sano
        risanato = giro(a, guasti=(), silenzioso=True)[0]
        ok = (n_sano == 0 and n_rotto > n_sano and vista and not gia
              and risanato == n_sano)
        tutto_bene &= ok
        riga(VERDE if ok else ROSSO, "OK" if ok else "NO", sigla,
             f"sano {n_sano} -> guasto {n_rotto} -> risanato {risanato}   "
             f"marca «{marca}»: {'vista' if vista else '⛔ NON vista'}"
             + ("  ⛔ ma gia' presente nel giro sano" if gia else ""))
        if not ok:
            print(f"        {g['titolo']}")
        righe.append({"guasto": sigla, "titolo": g["titolo"], "sano": n_sano,
                      "guasto_conta": n_rotto, "risanato": risanato,
                      "marca": marca, "marca_vista": vista,
                      "marca_gia_nel_sano": gia, "esito": bool(ok)})
    scrivi_esito(a, {"tipo": "certificazione", "guasti": righe,
                     "esito": bool(tutto_bene)})
    print()
    if tutto_bene:
        print(f"    {VERDE}⭐ 02-filo-fotogramma.py e' CERTIFICATO: "
              f"{len(GUASTI)} guasti su {len(GUASTI)}{GRIGIO}")
        return 0
    print(f"    {ROSSO}⛔ NON certificato{GRIGIO}")
    return 1


def principale(a):
    n = conta(CASI)
    if a.elenco:
        print(f"== F2.4 — il fotogramma contro `RCP.md`: {len(CASI)} casi")
        print(f"   {n['violazioni']} violazioni · {n['scarti']} scarti · "
              f"{n['verdi']} ⭐ verdi attesi · {n['ambigui']} ⭐ ambiguita' "
              f"di `RCP.md`")
        print(f"   ⛔ Ogni riga e' una PREVISIONE, scritta prima del giro\n")
        for c in CASI:
            print(f"  {c['nome']:30s} {c['atteso']}")
            print(f"  {'':30s}   {c['spiega']}")
            if c["regola"]:
                print(f"  {'':30s}   regola attesa: {c['regola']}")
        print(f"\n== ⛔ I GUASTI, e l'atteso di ciascuno — scritto PRIMA")
        for sigla, g in GUASTI.items():
            print(f"  {sigla}  {g['titolo']}")
            print(f"      rompe:    {g['rompe']}")
            print(f"      atteso sano:   0 guasti su {len(CASI)} casi")
            print(f"      atteso guasto: > 0 guasti, e nell'uscita la marca "
                  f"«{g['marca']}»")
            print(f"      ⛔ e la marca NON deve comparire nel giro sano")
        print(f"\n== ⭐⛔ LE SEI RIGHE ENTRATE IN `RCP.md` IL 12 AGOSTO 2026,")
        print(f"      e i DUE casi di ciascuna")
        coperte, mancanti = regole_coperte(CASI)
        for sigla, r in REGOLE_NUOVE.items():
            print(f"  {sigla}  {r['dove']}")
            print(f"      «{r['dice']}»")
            print(f"      era:      {r['era']}")
            print(f"      la VIOLA:    {r['viola']}")
            print(f"      la RISPETTA: {r['rispetta']}")
        print(f"\n  ⛔ regole con TUTT'E DUE i casi: {len(coperte)} su "
              f"{len(REGOLE_NUOVE)} — {', '.join(coperte) or '—'}")
        for sigla, perche in mancanti:
            print(f"     {ROSSO}⛔ {sigla}: {perche}{GRIGIO}")
        # ⛔⛔ E LE PROPOSTE APERTE, SEPARATE: quel che il documento NON dice.
        print(f"\n== ⛔⛔ LE PROPOSTE ANCORA APERTE — `RCP.md` non le porta")
        print(f"      ⚠ Non sono regole: sono cure con il testo pronto, e il "
              f"documento")
        print(f"        lo tocca il coordinatore.  Qui c'e' l'atteso di OGGI, "
              f"non di domani")
        ap_coperte, ap_mancanti = proposte_coperte(CASI)
        for sigla, p in PROPOSTE_APERTE.items():
            print(f"  {sigla}  {p['dove']}")
            print(f"      «{p['dice']}»")
            print(f"      e':       {p['era']}")
            for nome, atteso in p["casi"].items():
                # ⛔ «(oggi)» in coda non e' decorazione: senza, questa riga
                #    finirebbe con `AMBIGUO` e `02-filo-lancia.sh` — che le
                #    ambiguita' le cerca con `grep 'AMBIGUO$'` — stamperebbe
                #    due volte lo stesso caso, una dalla tabella e una
                #    dall'elenco.  ⚠ Un banco che si duplica addosso le proprie
                #    righe fa contare male chi legge l'uscita.
                print(f"      {nome:32s} atteso {atteso} (oggi)")
        print(f"\n  ⛔ proposte con TUTTI i loro casi: {len(ap_coperte)} su "
              f"{len(PROPOSTE_APERTE)} — {', '.join(ap_coperte) or '—'}")
        for sigla, perche in ap_mancanti:
            print(f"     {ROSSO}⛔ {sigla}: {perche}{GRIGIO}")
        return 0

    if a.certifica:
        return certifica(a)

    print(f"== F2.4 — il fotogramma giudicato contro `RCP.md`")
    print(f"   ⛔ SCENA: nessuna rete, nessun server.  I fotogrammi li fabbrica")
    print(f"      questo banco e il giudice li legge **a pezzi**, come "
          f"arriverebbero")
    print(f"      da uno stream QUIC.  Il prodotto della fase 2 non esiste: "
          f"`grep -c`")
    print(f"      di `0x0301` in `src/` da' 0 su tutti e tre i file `[M]`")
    if a.guasto:
        print(f"   {GIALLO}⚠ GUASTO INNESTATO: {a.guasto} — "
              f"{GUASTI[a.guasto]['titolo']}{GRIGIO}")
    print(f"   {len(CASI)} casi: {n['violazioni']} violazioni · {n['scarti']} "
          f"scarti · {n['verdi']} verdi · {n['ambigui']} ambiguita'")
    print(f"   registro: {a.uscita or '⛔ NESSUNO'}\n")

    r = giro(a, guasti=(a.guasto,) if a.guasto else ())
    if r is None:
        return 2
    guastati, ambigui, righe, _ = r

    print(f"\n    == quel che questo giro ha davvero guardato")
    sel = conta([c for c in CASI if not a.solo or a.solo in c["nome"]])
    for che, tot in sel.items():
        if tot == 0:
            print(f"    --  {che:36s} nessun caso lo ha sollecitato")
        else:
            print(f"    {tot:3d}      {che}")

    # ⭐⛔ LE SEI RIGHE NUOVE: QUANTE HANNO DAVVERO I DUE CASI.
    #
    #    ⛔ Questo conto sta **dentro il giro**, non in un commento e non nel
    #       rapporto: una regola che perdesse il caso che la fa scattare
    #       tornerebbe a essere una regola che nessuno fa rispettare, e il
    #       banco resterebbe verde — che e' la forma peggiore di verde.
    coperte, mancanti = regole_coperte(CASI)
    print(f"\n    == ⭐⛔ le sei righe entrate in `RCP.md` il 12 agosto 2026")
    riga(VERDE if not mancanti else ROSSO, "OK" if not mancanti else "NO",
         "regole-con-i-due-casi",
         f"{len(coperte)} su {len(REGOLE_NUOVE)} hanno il caso che le VIOLA e "
         f"quello che le RISPETTA: {', '.join(coperte) or '—'}")
    for sigla, perche in mancanti:
        print(f"        ⛔ {sigla}: {perche}")

    # ⛔⛔ E LE PROPOSTE ANCORA APERTE, CONTATE ALLO STESSO MODO.
    #
    #    ⚠ Il conto sta accanto a quello delle regole entrate e **non insieme**:
    #      «sei righe che il documento porta» e «una cura che il documento non
    #      ha ancora» sono due fatti diversi, e sommarli darebbe un numero che
    #      non vuol dire niente.
    ap_coperte, ap_mancanti = proposte_coperte(CASI)
    print(f"\n    == ⛔⛔ le proposte APERTE — `RCP.md` non le porta ancora")
    riga(VERDE if not ap_mancanti else ROSSO, "OK" if not ap_mancanti else "NO",
         "proposte-con-i-loro-casi",
         f"{len(ap_coperte)} su {len(PROPOSTE_APERTE)} hanno tutti i loro "
         f"casi: {', '.join(ap_coperte) or '—'}")
    for sigla, perche in ap_mancanti:
        print(f"        ⛔ {sigla}: {perche}")

    # ⭐⛔ LE AMBIGUITA' DI `RCP.md`, IN FONDO E CON LA CURA ACCANTO.
    if ambigui:
        print(f"\n    {GIALLO}⭐⛔ `RCP.md` NON DECIDE BENE IN "
              f"{len(ambigui)} PUNT{'O' if len(ambigui) == 1 else 'I'}"
              f"{GRIGIO}")
        print(f"       ⚠ Non e' un guasto del prodotto e non fa fallire questo")
        print(f"         giro: e' un difetto del DOCUMENTO, e §0 dice che i")
        print(f"         difetti di quel file sono di quel file.")
        # ⛔ E le due famiglie si nominano, perche' non sono la stessa cosa e
        #    confonderle gonfia il conto (`F2-4-filo.md`, «Che cosa propongo»):
        #      lettura doppia  -> due implementazioni conformi producono byte
        #                         DIVERSI per lo stesso ingresso;
        #      contraddizione  -> due implementazioni conformi producono lo
        #                         STESSO byte, e quel byte e' sbagliato.
        print(f"       ⚠ E sono due famiglie: una **lettura doppia** fa "
              f"divergere due")
        print(f"         implementazioni attente; una **contraddizione "
              f"interna** le fa")
        print(f"         convergere sullo stesso byte sbagliato — e la seconda "
              f"e' peggio,")
        print(f"         perche' nessun confronto fra due implementazioni la "
              f"trova.")
        for nome, prop, dice in ambigui:
            # ⛔ La cura si cerca in tutt'e due le tabelle: una proposta ancora
            #    aperta non sta fra le regole entrate, e stamparla come «?»
            #    farebbe di un rilievo con la cura pronta un reclamo.
            r = REGOLE_NUOVE.get(prop) or PROPOSTE_APERTE.get(prop, {})
            print(f"\n       {nome}")
            print(f"         {dice}")
            print(f"         ⇒ {prop} — {r.get('dove', '?')}")
            print(f"           «{r.get('dice', '?')}»")
    elif not a.solo:
        # ⛔ E LO ZERO SI DICHIARA, non si tace: «nessuna ambiguita' stampata»
        #    e «il ramo che le stampa non e' esercitato da nessun caso» sono
        #    due fatti diversi, ed e' la forma E8 applicata al banco stesso.
        print(f"\n    --  ⭐ `RCP.md` non ammette piu' due letture in nessuno "
              f"dei {len(CASI)} casi:")
        print(f"        le quattro che questo banco aveva trovato sono entrate "
              f"nel documento")
        print(f"        il 12 agosto 2026 (P2 §6.2 · P3 §2.5 · P5 §6.2 · P6 "
              f"§5.2).")
        print(f"        ⚠ Da cui: **nessun caso** pretende oggi `AMBIGUO`, e il "
              f"ramo che li")
        print(f"        stampa non e' esercitato da questo giro.  Il ramo del "
              f"GIUDICE che")
        print(f"        produce `AMBIGUO` lo esercita il guasto **G5**, a ogni "
              f"certificazione.")

    # ⛔ IL CONTROLLO POSITIVO, IN CODA A OGNI ESECUZIONE.
    print(f"\n    == ⛔ il controllo positivo")
    ok_cp, perche = controllo_positivo()
    riga(VERDE if ok_cp else ROSSO, "OK" if ok_cp else "NO",
         "controllo-positivo", perche)

    scritto = scrivi_esito(a, {
        "tipo": "giro", "guasto_innestato": a.guasto or None,
        "filtro": a.solo or None, "casi": len(righe), "guastati": guastati,
        "ambigui": [x[0] for x in ambigui], "proposte": [x[1] for x in ambigui],
        "controllo_positivo": bool(ok_cp), "righe": righe})
    print(f"    --  registro: {'una riga scritta in ' + a.uscita if scritto else 'NESSUNO'}")

    print()
    if guastati or not ok_cp:
        print(f"    {ROSSO}⛔ F2.4-fotogramma: {guastati} casi non passano"
              f"{'' if ok_cp else ', e il controllo positivo non regge'}{GRIGIO}")
        return 1
    if a.solo:
        print(f"    {VERDE}⭐ i casi selezionati passano{GRIGIO} — ⚠ e questo "
              f"NON e' «il banco passa»: il giro era parziale")
        return 0
    print(f"    {VERDE}⭐ il giudice del fotogramma e' d'accordo con `RCP.md` "
          f"su {len(righe)} casi{GRIGIO}")
    print(f"    ⚠ e NON e' «il fotogramma arriva»: qui non e' passato un byte "
          f"sulla rete.")
    print(f"      Quello lo misura `02-filo-cliente.py`, contro un server che "
          f"non esiste ancora.")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="F2.4 — il fotogramma giudicato contro RCP.md")
    p.add_argument("--solo", default="",
                   help="gira solo i casi che contengono questo")
    p.add_argument("--elenco", action="store_true",
                   help="stampa le previsioni e i guasti, senza misurare")
    p.add_argument("--guasto", choices=sorted(GUASTI),
                   help="innesta un guasto NEL GIUDICE")
    p.add_argument("--certifica", action="store_true",
                   help="sano -> guasto -> risanato, per ogni guasto")
    p.add_argument("--uscita", default="",
                   help="il registro del giro, in JSONL")
    sys.exit(principale(p.parse_args()))
