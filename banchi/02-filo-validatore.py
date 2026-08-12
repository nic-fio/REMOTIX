#!/usr/bin/env python3
"""02-filo-validatore.py — ⛔ F2.4: l'arbitro meccanico impara il CANALE VIDEO.

    python3 02-filo-validatore.py registrazione.rcpreg
    python3 02-filo-validatore.py --fabbrica       costruisce le registrazioni di prova
    python3 02-filo-validatore.py --certifica      sano -> G4 -> risanato
    python3 02-filo-validatore.py --uscita 02-filo-esiti.jsonl reg.rcpreg

    uscita 0  il canale video e' conforme — e si dice SU QUANTI fotogrammi
    uscita 1  non e' conforme — e si dice QUALE byte e QUALE regola
    uscita 2  la REGISTRAZIONE e' rotta, o non si legge (non e' un giudizio sul filo)
    uscita 3  ⛔ non c'e' NIENTE DA GIUDICARE: zero blocchi sul canale video

===========================================================================
⛔ PERCHE' ESISTE, E NON E' UN DOPPIONE DI `01-b4-validatore.py`

`PIANO.md` §0.4 elenca **tre** sostituti dell'arbitro che abbiamo perso con
`mstsc`, e il validatore del filo e' quello **meccanico**: *«vede i byte non
conformi, ma solo quelli»*.

⛔ **E oggi non vede il video.**  `01-b4-validatore.py`, riga 521:

    if canale != 0x00:
        print(f"   blocco {nb}: canale {CANALI[canale]} dal {chi}, "
              f"{lung} byte — non giudicato da questo validatore")
        continue

⚠ E' una riga onesta — **dichiara** di non giudicare, che e' il contrario di
assolvere — ma la conseguenza e' che dal primo fotogramma in poi il capitolo
piu' voluminoso del filo torna a essere validato da **una sola**
implementazione, scritta dalla stessa mano che scrive il server.  ⛔ E' lo
stato che `RCP.md` §0 descrive come il difetto muto: *«se il server emette una
sciocchezza, il nostro client la accettera' volentieri»*.

⭐ **E il precedente dice che non e' teorico**: delle due contraddizioni interne
di `RCP.md` trovate nella fase 1, **una l'ha trovata questo strumento** — il
trattino basso di §4.3, alla prima esecuzione, prima che esistesse un byte di
server (`RCP.md` §4.3, riquadro del 10 agosto 2026).  ⛔ Tutt'e due sono state
trovate da programmi che leggevano **solo quel documento**, e **nessuna delle
due** da chi lo rileggeva.

===========================================================================
⛔ E QUESTO FILE NON TOCCA `01-b4-validatore.py`

Il mandato della fase 2 (§2): *«nessuno scrive fuori dai propri file»*.  B4 e'
della fase 1.  ⭐ Qui il canale video si giudica **accanto** a B4, con lo stesso
formato e gli stessi codici d'uscita, e la proposta di fonderli sta nel
rapporto `fasi/rapporti/F2-4-filo.md`: e' una decisione del coordinatore, non
di un sottoagente.

⚠ **E il giudizio non e' riscritto due volte**: importa `02-filo-fotogramma.py`,
che e' il giudice scritto leggendo `RCP.md` §6.2.  Due copie del giudizio
sarebbero due implementazioni della stessa lettura, cioe' precisamente cio' che
questo strumento esiste per impedire.

===========================================================================
⛔⭐ IL BUCO CHE QUESTO STRUMENTO HA TROVATO NEL FORMATO — P7, ED E' CHIUSO

*Trovato il 12 agosto 2026 da questo file, **provando a giudicare una
registrazione conforme** e non riuscendo a dire se il fotogramma fosse
completo.  Applicato a `RCP.md` §11.1 lo stesso giorno dal coordinatore.*

Il blocco di §11.1 **non portava nessun campo che dicesse come e' finito lo
stream**.  E per il video quella e' la distinzione piu' importante che il
documento abbia: §6.2, rilievo **R1.7** della sera del 9 agosto 2026, aggiunse
due parole — *«ma solo se lo stream e' finito con un FIN»* — perche' senza di
esse

  ⛔ *«un fotogramma abbandonato e uno completo avevano lo stesso aspetto»*,

che il documento stesso classifica come forma d'errore **E8**.  ⭐ La cura era
stata scritta **sul filo**, e la registrazione la riapriva: guardando un file
`.rcpreg`, l'arbitro non poteva distinguere un fotogramma troncato perche' il
server lo aveva **abbandonato di proposito** (§5.1, legale, e la sessione
regge) da uno troncato perche' il server **aveva sbagliato** (§3, la
connessione cade).

⛔ **Adesso il blocco porta `fine`**, subito dopo `canale`:

    0 = lo stream continua · 1 = chiuso con FIN · 2 = azzerato con RESET_STREAM

⛔⛔ **E LA MAGIA E' PASSATA A `"RCPREG" 0x00 0x02`, che e' il punto.**  §11.1:
   *«un validatore vecchio deve **rifiutare** il formato nuovo, non leggerlo di
   traverso»*.  ⚠ E la simmetria vale anche di qua: questo validatore
   **rifiuta** `0x00 0x01` con una frase che lo dice, e non prova a leggerlo.
   Il blocco vecchio era di 16 byte e il nuovo e' di 17: letto di traverso, il
   `canale` finirebbe dentro lo `stream`, e ⛔ ne uscirebbe un giudizio — cioe'
   un rosso, o peggio un verde, su byte che nessuno ha scritto.  Un formato che
   cambia misura senza cambiare versione e' la forma d'errore che §11.1 nomina
   per esteso.

⚠ Ed era lo stesso buco che B9 aveva sfiorato sul canale di controllo — la
lettura **L3**, *«il bit FIN del frame STREAM che porta il `CONGEDO`: gli
stessi byte di carico, un bit di trasporto in piu'»* — senza dire che il
formato della registrazione non sapeva scriverlo.

⛔ **E il denominatore «completezza ignota» NON e' sparito con la cura**, ed e'
importante che non sia sparito: adesso conta i flussi il cui ultimo blocco
porta `fine = 0`, cioe' gli stream che nella registrazione **non si sono mai
chiusi** — una traccia tagliata a meta', o un server ancora in mezzo al
fotogramma.  ⚠ «Non l'ho guardato» e «l'ho guardato e va bene» restano due
fatti diversi (`LEZIONI.md` §1.9); a cambiare e' **di chi e' la colpa**: prima
era del formato, adesso e' della registrazione.

===========================================================================
⛔ LE SEI RIGHE DEL 12 AGOSTO, GIUDICATE QUI SULLE REGISTRAZIONI

Quattro delle sei le applica il giudice importato (`02-filo-fotogramma.py`), e
qui arrivano gratis: P2 (`numero` parte da 1, e al giro del contatore lo `0`
si salta), P4 (FIN prima dei 28 byte), P5 (la misura e' quella della **tela in
vigore**), P6 (il primo fotogramma e' una chiave).

⛔ **Due invece questo file le deve giudicare da se', e sono le due che parlano
   di STREAM** — un giudice che vede un fotogramma per volta non le puo'
   vedere, perche' non sa **su quale stream** sia arrivato ne' **che cosa fosse
   gia' passato**:

  **P3** un `0x03` sul **canale di controllo**.  Qui si riconosce cosi': il
        canale di controllo e' lo stream su cui viaggiano i blocchi `0x00`
        (§4.2, il primo bidirezionale), e un blocco video **su quello stesso
        stream** e' `ERRORE_PROTOCOLLO`.

  **P1** nessuno stream video **prima di `SESSIONE`**.  Qui si riconosce
        leggendo il canale di controllo in ordine di file e segnando quando
        passa `SESSIONE` (`0x0007`, dal server): un flusso video il cui **primo
        blocco** compare prima di quel punto viola §2.5.
        ⚠ E se il canale di controllo non si lasciasse leggere, P1 **non si
          giudica e si dichiara**: e' `01-b4-validatore.py` l'arbitro di quel
          canale, e indovinare qui sarebbe la forma **E8**.

⭐⛔ **E P5 e' stata CORRETTA in `RCP.md` il 12 agosto 2026**, poche ore dopo
    essere entrata, perche' propagarla qui ha mostrato che uccideva una
    sessione sana: diceva *«la tela concessa in `SESSIONE`»*, e dopo un
    `TELA(ADATTATA, 1280, 720)` (§7.1) un client conforme a §6.2 chiudeva
    davanti a un server conforme a §7.1.  Adesso dice **«la tela in vigore»**,
    e questo file la segue: sfoglia il canale di controllo anche per i `TELA`,
    non solo per `SESSIONE`.  ⛔ Le due prove che la tengono onesta sono
    `p5-misura-diversa` (misura diversa **senza** un `TELA` prima: si chiude) e
    `p5-misura-dopo-adatta-tela` (**gli stessi byte**, dopo un `TELA` che l'ha
    concessa: si accetta).

===========================================================================
⛔⛔ E LA CURA DI P5 NE HA APERTA UN'ALTRA — **D14**, la sera del 12 agosto

*Adesso che la tela puo' cambiare a meta' sessione, i fotogrammi **gia' in
volo** portano **legittimamente** la misura precedente — e §6.2 alla lettera fa
chiudere chi ne riceve una diversa da quella in vigore.  ⛔ Un client conforme
uccide una sessione sana, ed e' la stessa forma di P5.*

  ⛔ **Qui si vede meglio che altrove**, ed e' la ragione per cui le due prove
     stanno anche in questo file e non solo nel giudice: in una registrazione
     l'ordine dei blocchi e' l'ordine di **arrivo**, e un flusso video il cui
     primo blocco compare **dopo** il `TELA(ADATTATA)` e' esattamente il
     fotogramma in volo.  L'arbitro non lo condanna: lo dichiara `AMBIGUO` e
     porta la proposta **P8** — la grazia di un secondo che §7.1 da' gia' alle
     coordinate di input (terza eccezione di §3).

  ⛔ **E una meta' questo arbitro NON la puo' giudicare, e la dichiara**:
     §11.1 non porta **nessun istante**, quindi da una registrazione «dentro il
     secondo di grazia» e «fuori» hanno lo stesso aspetto.  ⚠ Vale anche per la
     grazia che §7.1 ha **gia'** sulle coordinate di input: nessun arbitro
     meccanico puo' giudicarla leggendo un `.rcpreg`.  Il denominatore si
     chiama `grazia_ignota`, e c'e' perche' indovinare sarebbe la forma **E8**.

  ⛔ **Le due prove, e la seconda e' quella che conta**:
     `p8-in-volo-dopo-adatta-tela` (la sessione sana che oggi cadrebbe: esce 0
     con la dichiarazione) e `p8-misura-di-nessuna-tela` (una misura che non e'
     ne' quella in vigore ne' la precedente: esce **1**, e deve uscire 1 — una
     cura scritta troppo larga passerebbe la prima e spegnerebbe P5).
"""
import argparse
import hashlib
import importlib.util
import json
import os
import struct
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ Il giudice si IMPORTA, non si ricopia.  Vedi l'intestazione.
_spec = importlib.util.spec_from_file_location(
    "f24", os.path.join(QUI, "02-filo-fotogramma.py"))
f24 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(f24)

# ⛔ LA MAGIA, E QUELLA CHE NON SI LEGGE PIU' — §11.1, 12 agosto 2026.
#
#    ⛔ `MAGIA_VECCHIA` non e' un residuo: e' l'unico modo di dare al file
#       vecchio la frase che merita.  Senza, un `.rcpreg` del 10 agosto
#       cadrebbe nel ramo «non comincia con la magia», che manda a cercare un
#       file corrotto — e il file non e' corrotto, e' di **un'altra versione**.
#       Sono due cure diverse: rigenerarlo, o andare a vedere chi lo ha rotto.
MAGIA = b"RCPREG\x00\x02"
MAGIA_VECCHIA = b"RCPREG\x00\x01"
RIEMPIMENTO = 0x2A          # §11.1
CLIENT, SERVER = 1, 2
CANALI = {0x00: "controllo", 0x01: "input", 0x02: "appunti",
          0x03: "video", 0x04: "audio"}
VIDEO = 0x03
CONTROLLO = 0x00

# ⛔ `fine` — «come si e' chiuso lo stream DOPO questo blocco» (§11.1).
CONTINUA, FIN, RESET = 0, 1, 2
FINE = {CONTINUA: "continua", FIN: "FIN", RESET: "RESET_STREAM"}

# Il blocco di §11.1: verso, canale, fine, stream, lunghezza, quanti_oscurati.
# ⛔ Diciassette byte, non sedici: e' `fine` che li ha cambiati, ed e' la
#    ragione per cui la magia e' passata a `0x00 0x02`.
BLOCCO = "!BBBQIH"
BLOCCO_BYTE = struct.calcsize(BLOCCO)

SESSIONE = 0x0007           # §7.1, dal server
TELA = 0x000E               # §7.1, dal server — l'esito di `ADATTA_TELA`
ADATTATA = 1                # §7.1, `TELA.esito`

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


class NonConforme(Exception):
    def __init__(self, regola, dice, ass, rel):
        super().__init__(dice)
        self.regola, self.dice, self.ass, self.rel = regola, dice, ass, rel


class Malformata(Exception):
    """La REGISTRAZIONE e' rotta: non e' un giudizio sul filo."""


class NienteDaGiudicare(Exception):
    """⛔ Nel file non c'e' nessun blocco video.  Non e' «conforme»."""


# ---------------------------------------------------------------------------
def leggi_blocchi(d):
    """I blocchi di §11.1, con i controlli che il formato impone.

    ⛔ I controlli del FORMATO stanno qui e sollevano `Malformata`, non
       `NonConforme`: *«una registrazione malformata e un filo non conforme
       sono due cose diverse, e vanno dette con due frasi diverse»* (§11.1).
    """
    # ⛔ IL FORMATO VECCHIO SI RIFIUTA, E CON LA SUA FRASE — §11.1.
    #
    #    *«un validatore vecchio deve RIFIUTARE il formato nuovo, non leggerlo
    #    di traverso»*, e vale nei due versi.  Il blocco vecchio era di 16 byte
    #    e il nuovo e' di 17: leggendo un file `0x00 0x01` con questo lettore,
    #    il `canale` cadrebbe nel primo byte dello `stream` e ogni blocco
    #    scivolerebbe di uno.  ⛔ Ne uscirebbe un GIUDIZIO — un rosso su un byte
    #    che nessuno ha scritto, o un verde peggiore — invece di «questo file e'
    #    di un'altra versione».
    if len(d) >= 8 and d[:8] == MAGIA_VECCHIA:
        raise Malformata(
            "e' una registrazione nel formato VECCHIO, «RCPREG 0x00 0x01»: il "
            "blocco non porta il campo `fine` e misura 16 byte invece di 17.  "
            "⛔ Non si legge di traverso — §11.1, 12 agosto 2026 — e non e' un "
            "file rotto: si RIGENERA con il registratore di oggi")
    if len(d) < 16 or d[:8] != MAGIA:
        raise Malformata("non comincia con la magia di RCP.md §11.1")
    quanti, riservato = struct.unpack("!II", d[8:16])
    if riservato != 0:
        raise Malformata(f"il campo riservato vale {riservato}, DEVE essere 0")
    p, fuori = 16, []
    for nb in range(quanti):
        if p + BLOCCO_BYTE > len(d):
            raise Malformata(f"il blocco {nb} comincia oltre la fine del file")
        verso, canale, fine, stream, lung, nosc = struct.unpack(
            BLOCCO, d[p:p + BLOCCO_BYTE])
        p += BLOCCO_BYTE
        if fine not in FINE:
            raise Malformata(
                f"blocco {nb}: `fine` vale {fine}, e §11.1 ne definisce tre — "
                f"0 continua, 1 FIN, 2 RESET_STREAM")
        oscurati = []
        for _ in range(nosc):
            if p + 40 > len(d):
                raise Malformata(f"blocco {nb}: intervallo oscurato troncato")
            ini, qua = struct.unpack("!II", d[p:p + 8])
            p += 40
            if ini + qua > lung:
                raise Malformata(
                    f"blocco {nb}: intervallo oscurato [{ini},{ini + qua}) "
                    f"fuori dal carico di {lung} byte")
            for o, q in oscurati:
                if not (ini + qua <= o or ini >= o + q):
                    raise Malformata(
                        f"blocco {nb}: due intervalli oscurati si sovrappongono")
            oscurati.append((ini, qua))
        if p + lung > len(d):
            raise Malformata(f"blocco {nb}: il carico e' troncato")
        if verso not in (CLIENT, SERVER):
            raise Malformata(f"blocco {nb}: verso {verso}, previsti 1 o 2")
        for o, q in oscurati:
            if any(b != RIEMPIMENTO for b in d[p + o:p + o + q]):
                raise Malformata(
                    f"blocco {nb}: un intervallo oscurato non e' fatto di 0x2A")
        fuori.append({"n": nb, "verso": verso, "canale": canale, "fine": fine,
                      "stream": stream, "base": p, "lung": lung,
                      "carico": d[p:p + lung], "oscurati": oscurati})
        p += lung
    if p != len(d):
        raise Malformata(
            f"restano {len(d) - p} byte dopo i {quanti} blocchi dichiarati: o "
            f"`quanti_blocchi` e' sotto-dichiarato — e allora c'e' del filo che "
            f"nessuno ha giudicato — o c'e' una coda che non e' del formato")
    return fuori


# ---------------------------------------------------------------------------
class ControlloIlleggibile(Exception):
    """⛔ Il canale di controllo non si sfoglia: P1 non si giudica, si DICHIARA.

    ⚠ Non e' `NonConforme`: l'arbitro di quel canale e'
       `01-b4-validatore.py`, e dare un rosso di protocollo da qui vorrebbe
       dire accusare un difetto che un altro strumento sa nominare meglio.
       ⛔ E non e' nemmeno silenzio: il flusso finisce nel denominatore
       «ordine ignoto», che si stampa.
    """


def tipi_di_controllo(carico):
    """I `tipo` dei messaggi di §6.1 dentro un blocco del canale di controllo.

    ⛔ Serve a **due cose sole**: sapere quando e' passata `SESSIONE` (meta' di
       P1, §2.5) e quando un `TELA` ha cambiato la **tela in vigore** (meta' di
       P5, §6.2 corretta il 12 agosto 2026).  Non giudica niente — il giudizio
       di quel canale e' di `01-b4-validatore.py` — e per questo si ferma alla
       prima cosa che non torna invece di sollevare un rosso.

    ⛔ Restituisce `(tipo, corpo)`, non il solo tipo: di `TELA` serve il corpo,
       e tornare a leggerlo una seconda volta vorrebbe dire sfogliare due volte
       la stessa inquadratura con due lettori diversi.
    """
    tipi, i = [], 0
    while i < len(carico):
        if i + 6 > len(carico):
            raise ControlloIlleggibile(
                f"restano {len(carico) - i} byte, e l'inquadratura di §6.1 ne "
                f"vuole 6")
        tipo, lung = struct.unpack("!HI", carico[i:i + 6])
        if i + 6 + lung > len(carico):
            raise ControlloIlleggibile(
                f"il messaggio {tipo:#06x} dichiara {lung} byte di corpo e ce "
                f"ne sono {len(carico) - i - 6}")
        tipi.append((tipo, carico[i + 6:i + 6 + lung]))
        i += 6 + lung
    return tipi


def valida(percorso, guasti=(), tela=(1920, 1080), codec=1, stampa=True):
    with open(percorso, "rb") as f:
        d = f.read()
    blocchi = leggi_blocchi(d)

    if stampa:
        print(f"== l'arbitro del canale VIDEO — {percorso}")
        print(f"   blocchi: {len(blocchi)}   byte: {len(d)}")
        print(f"   ⛔ contesto dichiarato: tela {tela[0]}x{tela[1]}, codec "
              f"negoziato {codec}")
        print(f"      ⚠ e va DICHIARATO da fuori: meta' delle regole di §6.2 "
              f"non si")
        print(f"        possono applicare senza — «DEVE essere quello "
              f"negoziato in §4.3»,")
        print(f"        «e' sempre quella della tela».  Un arbitro che li "
              f"indovinasse")
        print(f"        starebbe giudicando i propri predefiniti")

    # ⛔ I DENOMINATORI, E SONO CINQUE PERCHE' LE COSE CHE SI POSSONO NON AVER
    #    GUARDATO SONO CINQUE.  ⭐ `ordine_ignoto` e' nato col campo `fine`:
    #    e' il numero di flussi per cui **P1 non si e' potuta giudicare**.
    # ⛔⛔ `grazia_ignota` e' del 12 agosto 2026, sera — difetto **D14**: e' il
    #    numero di flussi che portano la tela **precedente** subito dopo un
    #    `TELA(ADATTATA)`.  ⚠ E si chiama «ignota» per una ragione che vale la
    #    pena avere in mano: §11.1 **non porta nessun istante**, quindi da una
    #    registrazione non si puo' sapere se il **secondo** di grazia di §7.1
    #    fosse passato o no.  ⛔ Dire «era dentro» sarebbe indovinare, e dire
    #    «era fuori» sarebbe la forma E8 al contrario: si dichiara.
    conta = {"blocchi": len(blocchi), "video": 0, "flussi": 0,
             "giudicati": 0, "completezza_ignota": 0, "ordine_ignoto": 0,
             "grazia_ignota": 0}
    ctx = f24.Contesto(tela=tela, codec_negoziato=codec, sessione_aperta=True)

    # I blocchi video si raggruppano per `stream`: uno stream, un fotogramma
    # (§6.2).  ⛔ E l'ordine dentro un flusso e' quello del file, non quello
    # dello `stream`: gli stream sono indipendenti e i blocchi si interlacciano.
    #
    # ⛔⭐ E MENTRE SI SFOGLIA SI TENGONO DUE COSE CHE UN GIUDICE DEL SINGOLO
    #     FOTOGRAMMA NON PUO' AVERE — sono le due regole del 12 agosto che
    #     parlano di **stream** invece che di byte:
    #
    #       `su_controllo`      P3 — su quali stream vive il canale di
    #                           controllo (§4.2: il primo bidirezionale).  Un
    #                           blocco video su uno di quelli e' un `0x03` sul
    #                           canale di controllo;
    #       `prima_di_sessione` P1 — quali flussi video cominciano **prima**
    #                           che `SESSIONE` sia passata.
    flussi, ordine, tele = {}, [], {}
    su_controllo, prima_di_sessione = set(), set()
    controllo_stream = {b["stream"] for b in blocchi if b["canale"] == CONTROLLO}
    sessione_vista, controllo_leggibile, perche_illeggibile = False, True, ""
    # ⛔⭐ LA TELA **IN VIGORE**, E CAMBIA A META' SESSIONE — §6.2, corretta il
    #     12 agosto 2026.  Comincia da quella dichiarata da fuori (che e' la
    #     tela di `SESSIONE`) e un `TELA(ADATTATA, …)` la sposta.
    #     ⚠ Si tiene il valore **al momento in cui ogni flusso si apre**, non
    #       quello di fine file: giudicare un fotogramma con una tela concessa
    #       dopo di lui sarebbe leggere il filo all'indietro.
    #     ⛔⛔ E SI TIENE ANCHE LA **PRECEDENTE** — difetto D14: i fotogrammi
    #        gia' in volo quando il `TELA` e' passato la portano legittimamente,
    #        e senza averla in mano l'arbitro non puo' distinguere «una misura
    #        vecchia che sta ancora arrivando» da «una misura che non e' mai
    #        stata di nessuna tela».  ⚠ `None` = non e' mai cambiata niente.
    tela_ora, tela_da_tela, tela_prec = tuple(tela), False, None
    for b in blocchi:
        if b["canale"] not in CANALI:
            raise NonConforme("RCP.md §2.5",
                              f"blocco {b['n']}: il byte alto vale "
                              f"{b['canale']:#04x}, fuori dai cinque canali",
                              b["base"], 0)
        if b["canale"] == CONTROLLO:
            # ⛔ Si legge SOLO per sapere quando passa `SESSIONE` (P1).  Un
            #    intervallo oscurato non disturba: §11.1 lo usa per la parola
            #    d'ordine (§4.4), che sta nel **corpo** di `CREDENZIALI`, e qui
            #    si guardano i sei byte dell'inquadratura.
            try:
                for tipo, corpo in tipi_di_controllo(b["carico"]):
                    if b["verso"] != SERVER:
                        continue        # §7.1: tutt'e due arrivano dal server
                    if tipo == SESSIONE:
                        sessione_vista = True
                    elif tipo == TELA and len(corpo) >= 10:
                        # ⛔ §7.1: `tela_larghezza`/`tela_altezza` sono «la tela
                        #    in vigore DOPO questo messaggio» — e lo sono anche
                        #    quando l'esito e' RIFIUTATA, dove riportano quella
                        #    di prima.  ⇒ si prende il campo, non si deduce
                        #    dall'esito: e' il campo a essere definito cosi'.
                        nuova = struct.unpack("!II", corpo[2:10])
                        # ⛔ La precedente si tiene solo se la tela **cambia**
                        #    davvero: un `TELA` che riporta la stessa misura —
                        #    ed e' quel che fa un `RIFIUTATA` — non lascia
                        #    niente in volo, e registrarlo come un cambio
                        #    aprirebbe una grazia che non serve a nessuno.
                        if nuova != tela_ora:
                            tela_prec = tela_ora
                        tela_ora = nuova
                        tela_da_tela = corpo[0] == ADATTATA
            except ControlloIlleggibile as e:
                controllo_leggibile, perche_illeggibile = False, str(e)
            continue
        if b["canale"] != VIDEO:
            continue
        conta["video"] += 1
        # ⛔ G4 — IL GUASTO CHE E' LO STATO DI OGGI DI `01-b4-validatore.py`.
        #
        #    La sua riga 521 dichiara di non giudicare i canali diversi da
        #    `0x00` e prosegue.  Innestato qui, il canale video torna a non
        #    essere guardato da nessuno, e il file esce **3** — «niente da
        #    giudicare» — che e' esattamente il verdetto onesto di uno
        #    strumento cieco.  ⭐ Se uscisse **0** questo guasto sarebbe
        #    invisibile, ed e' la ragione per cui il codice 3 esiste.
        if "G4" in guasti:
            continue
        # ⛔ IL VERSO — §2.5: «un canale usato nel verso sbagliato».  Il video
        #    va dal server al client, e basta.
        if b["verso"] != SERVER:
            raise NonConforme("RCP.md §2.5",
                              f"blocco {b['n']}: un fotogramma DAL CLIENT — il "
                              f"video va dal server al client",
                              b["base"], 0)
        if b["oscurati"]:
            # ⛔ §11.1: «il validatore NON DEVE leggere dentro un intervallo
            #    oscurato».  Su un fotogramma non ci sono segreti da nascondere
            #    — §4.4 parla della parola d'ordine — quindi un oscuramento qui
            #    e' un difetto del REGISTRATORE, e si dice come tale.
            raise Malformata(
                f"blocco {b['n']}: un intervallo oscurato su un blocco VIDEO. "
                f"§11.1 esiste per la parola d'ordine (§4.4); un fotogramma non "
                f"ha niente da oscurare, e il validatore non puo' giudicare "
                f"quel che non gli si lascia leggere")
        if b["stream"] not in flussi:
            flussi[b["stream"]] = []
            ordine.append(b["stream"])
            # ⛔ Le due regole di stream si decidono sul PRIMO blocco del
            #    flusso, non sull'ultimo: e' il momento in cui lo stream si
            #    apre, ed e' quello che §2.5 vincola.
            if b["stream"] in controllo_stream:
                su_controllo.add(b["stream"])
            if not sessione_vista:
                prima_di_sessione.add(b["stream"])
            tele[b["stream"]] = (tela_ora, tela_da_tela, tela_prec)
        flussi[b["stream"]].append(b)

    if not flussi:
        raise NienteDaGiudicare(
            f"{conta['blocchi']} blocchi, {conta['video']} sul canale video, "
            f"ZERO flussi da giudicare")

    conta["flussi"] = len(flussi)
    for sid in ordine:
        pezzi = flussi[sid]
        b0 = pezzi[0]

        # ── P3 — §2.5: «un `0x03` sul canale di controllo e' ERRORE_PROTOCOLLO»
        if sid in su_controllo:
            raise NonConforme(
                "RCP.md §2.5",
                f"flusso {sid}: un fotogramma sul CANALE DI CONTROLLO — lo "
                f"stesso stream su cui viaggiano i blocchi `0x00`.  §2.5 vuole "
                f"il video «solo su uno stream unidirezionale aperto dal "
                f"server»",
                b0["base"], 0)

        # ── P1 — §2.5: «nessuno prima di aver spedito `SESSIONE`»
        if not controllo_leggibile:
            # ⛔ E8 al contrario: non si conclude «allora era dopo».  Si conta.
            conta["ordine_ignoto"] += 1
        elif sid in prima_di_sessione:
            raise NonConforme(
                "RCP.md §2.5",
                f"flusso {sid}: uno stream video si apre PRIMA che `SESSIONE` "
                f"sia passata sul canale di controllo — il client riceve un "
                f"fotogramma di cui non conosce ne' la misura ne' il codec.  "
                f"E' l'invariante I3 sul filo",
                b0["base"], 0)

        # ── P5 — §6.2: la misura DEVE valere la **tela in vigore**, che e'
        #    quella di `SESSIONE` oppure l'ultima concessa da un `TELA` (§7.1).
        #    ⛔ Si rimette il contesto alla tela che era in vigore QUANDO
        #       questo flusso si e' aperto: e' il giudice ad applicare la
        #       regola, ma solo l'arbitro sa che cosa fosse passato prima.
        tela_fl, da_tela, prec_fl = tele.get(sid, (tuple(tela), False, None))
        if da_tela:
            # ⛔⛔ E si riapre la **grazia** di D14 con la tela precedente in
            #    mano: da una registrazione non si sa quanto tempo sia passato
            #    (§11.1 non porta istanti), quindi l'unica cosa onesta e'
            #    tenerla aperta e **dichiarare** che il secondo non si giudica.
            #    ⛔ `grazia=True` va chiesta: e' spenta di suo, perche' P8 non e'
            #       ancora una riga di `RCP.md` e chi non la chiede — B4 —
            #       continua a giudicare il documento di oggi.
            ctx.adatta_tela(*tela_fl, precedente=prec_fl, grazia=True)
        else:
            ctx.tela_larghezza, ctx.tela_altezza = tela_fl
            # ⛔ E il contesto si RIAZZERA fra un flusso e l'altro: e' lo stesso
            #    oggetto per tutta la registrazione, e una grazia lasciata
            #    aperta da un flusso di prima assolverebbe il flusso dopo.
            ctx.tela_precedente, ctx.grazia_aperta = None, False

        # ── e le altre quattro le applica il giudice, un byte per volta
        g = f24.Giudice(ctx, dove="uni", guasti=guasti)
        chiusura = pezzi[-1]["fine"]
        for b in pezzi[:-1]:
            if b["fine"] != CONTINUA:
                raise Malformata(
                    f"blocco {b['n']}: dichiara `fine = {b['fine']}` "
                    f"({FINE[b['fine']]}) ma sullo stream {sid} arrivano altri "
                    f"blocchi dopo.  ⛔ E' un difetto del REGISTRATORE: uno "
                    f"stream si chiude una volta sola")

        # ⛔⭐ E IL RESET VINCE SULL'INTESTAZIONE — §6.2, rilievo R1.7.
        #
        #    *«uno stream azzerato porta un fotogramma INCOMPLETO: il client
        #    DEVE buttare quel che ha ricevuto»*, e i byte di un'intestazione
        #    troncata **possono essere qualunque cosa**.  ⛔ Leggerla prima
        #    darebbe `ERRORE_PROTOCOLLO` — cioe' farebbe cadere la sessione —
        #    su un fotogramma che il server ha abbandonato **di proposito**,
        #    che e' il caso normale di §5.1.
        #    ⚠ Il guasto **G3** vive proprio qui, e per restare visibile deve
        #      passare da questo ramo: con `reset_come_fin` innestato lo stream
        #      azzerato si legge come uno chiuso con FIN, ed e' quel che si
        #      vuole vedere.
        if chiusura == RESET and not g.reset_come_fin:
            v = g.finisce("reset")
        else:
            for b in pezzi:
                g.arrivano(b["carico"])
                if g.verdetto is not None:
                    break
            if g.verdetto is not None:
                v = g.verdetto
            elif chiusura == CONTINUA:
                # ⛔ NON E' PIU' UN BUCO DEL FORMATO — e' un buco della
                #    REGISTRAZIONE.  Dal 12 agosto 2026 §11.1 porta `fine`, e
                #    `fine = 0` sull'ultimo blocco di un flusso vuol dire che
                #    lo stream, **in questo file**, non si e' mai chiuso: la
                #    traccia e' tagliata a meta', o il server era ancora in
                #    mezzo al fotogramma.  ⚠ Si dichiara, non si indovina: la
                #    completezza e' precisamente cio' che §6.2 lega al FIN.
                conta["completezza_ignota"] += 1
                conta["giudicati"] += 1
                if stampa:
                    print(f"   {GIALLO}?? flusso {sid}: {g.byte_dati} byte di "
                          f"dati e `fine = 0` sull'ultimo blocco — ⛔ lo stream "
                          f"non si chiude dentro questa registrazione, quindi "
                          f"la completezza NON si giudica (§6.2){GRIGIO}")
                continue
            else:
                v = g.finisce("fin" if chiusura == FIN else "reset")
        conta["giudicati"] += 1
        if v.esito in (f24.ERRORE_PROTOCOLLO,):
            b0 = pezzi[0]
            rel = v.scostamento if v.scostamento is not None else 0
            raise NonConforme(v.regola, f"flusso {sid}: {v.dice}",
                              b0["base"] + rel, rel)
        # ⛔⛔ D14 — il flusso porta la tela **precedente** subito dopo un
        #    `TELA(ADATTATA)`.  §6.2 alla lettera farebbe cadere la sessione, e
        #    cadrebbe una sessione in cui nessuno dei due lati ha sbagliato:
        #    l'arbitro NON esce 1, **dichiara** che qui il documento non decide
        #    e porta la proposta P8.  ⚠ E dichiara anche la meta' che non puo'
        #    giudicare: il **secondo** di grazia, che in un `.rcpreg` non c'e'.
        if v.esito == f24.AMBIGUO and v.propone == "P8":
            conta["grazia_ignota"] += 1
        if stampa:
            col = {f24.ACCETTATO: VERDE, f24.SCARTATO: GIALLO,
                   f24.AMBIGUO: GIALLO}[v.esito]
            extra = (f"   ⇒ proposta {v.propone}" if v.esito == f24.AMBIGUO
                     else "")
            print(f"   {col}{v.esito:18s}{GRIGIO} flusso {sid}: {v.dice}{extra}")

    if stampa:
        print(f"\n   guardati: {conta['blocchi']} blocchi, di cui "
              f"{conta['video']} sul canale video · {conta['flussi']} flussi · "
              f"{conta['giudicati']} giudicati")
        if conta["completezza_ignota"]:
            print(f"   {GIALLO}⛔ e di {conta['completezza_ignota']} su "
                  f"{conta['flussi']} NON si e' potuta giudicare la "
                  f"completezza{GRIGIO}")
            print(f"      `fine = 0` sull'ultimo blocco: lo stream non si "
                  f"chiude dentro questo")
            print(f"      file.  ⛔ NON e' un difetto del filo, ed e' un "
                  f"difetto della")
            print(f"      REGISTRAZIONE — dal 12 agosto 2026 il formato la "
                  f"domanda la sa fare")
        if conta["grazia_ignota"]:
            print(f"   {GIALLO}⛔⛔ e {conta['grazia_ignota']} flussi su "
                  f"{conta['flussi']} portano la tela **PRECEDENTE** subito "
                  f"dopo un `TELA(ADATTATA)`{GRIGIO}")
            print(f"      ⛔ §6.2 alla lettera li fa chiudere, e chiuderebbe "
                  f"una sessione in cui")
            print(f"         NESSUNO ha sbagliato: erano gia' in volo, e §6.2 "
                  f"stesso dice che i")
            print(f"         fotogrammi arrivano fuori ordine.  E' il difetto "
                  f"**D14**, e la cura")
            print(f"         e' la proposta **P8** — la grazia di un secondo "
                  f"che §7.1 da' gia'")
            print(f"         alle coordinate di input")
            print(f"      ⚠ E il **secondo** non si giudica da qui: §11.1 non "
                  f"porta istanti,")
            print(f"        quindi «dentro la grazia» e «fuori» hanno lo stesso "
                  f"aspetto in una")
            print(f"        registrazione.  Si dichiara invece di indovinare")
        if conta["ordine_ignoto"]:
            print(f"   {GIALLO}⛔ e per {conta['ordine_ignoto']} flussi su "
                  f"{conta['flussi']} NON si e' potuto giudicare se venissero "
                  f"prima di `SESSIONE`{GRIGIO}")
            print(f"      il canale di controllo non si sfoglia: "
                  f"{perche_illeggibile}")
            print(f"      ⚠ e a giudicare QUEL canale e' "
                  f"`01-b4-validatore.py`, non questo")
        print(f"   ⭐ conforme: nessuna violazione in {conta['giudicati']} "
              f"flussi")
    return 0, conta


# ===========================================================================
# ⛔ LE REGISTRAZIONI DI PROVA — e servono a certificare l'arbitro, non il filo.
#
#    §11: *«prima di concludere che il validatore non trova errori, gli si da'
#    una registrazione CON UN ERRORE DENTRO e si verifica che lo veda.  Uno
#    strumento che non ha mai trovato niente non e' uno strumento pulito: e'
#    uno strumento non certificato»*.
def scrivi_reg(percorso, blocchi, magia=MAGIA):
    """⛔ `magia` e' un parametro per UNA sola ragione: la prova che deve essere
       rifiutata.  Un formato che sa scrivere solo la propria versione non puo'
       certificare di saper rifiutare le altre."""
    out = bytearray(magia + struct.pack("!II", len(blocchi), 0))
    for verso, canale, fine, stream, carico in blocchi:
        if magia == MAGIA_VECCHIA:
            # il blocco di ieri: 16 byte, senza `fine`
            out += struct.pack("!BBQIH", verso, canale, stream, len(carico), 0)
        else:
            out += struct.pack(BLOCCO, verso, canale, fine, stream,
                               len(carico), 0)
        out += carico
    with open(percorso, "wb") as f:
        f.write(bytes(out))
    return percorso


def msg(tipo, corpo=b""):
    """Un messaggio di controllo nell'inquadratura di §6.1."""
    return struct.pack("!HI", tipo, len(corpo)) + corpo


def apre_la_sessione(stream=0):
    """⛔ Il blocco che rende LEGALE tutto il video che segue — P1.

    ⚠ Il corpo di `SESSIONE` e' vuoto, e va detto: questo arbitro legge del
      canale di controllo **soltanto** l'inquadratura di §6.1, per sapere
      quando quel messaggio e' passato.  A giudicarne il corpo e'
      `01-b4-validatore.py`, e riscriverne il giudizio qui sarebbe la doppia
      lettura che `RCP.md` §0 esiste per impedire.
    """
    return (SERVER, CONTROLLO, CONTINUA, stream, msg(SESSIONE))


def adatta_la_tela(lar, alt, esito=ADATTATA, stream=0):
    """⛔ `TELA` — §7.1: *«la tela in vigore DOPO questo messaggio»*.

    E' il messaggio che ha corretto `RCP.md`: senza di lui P5 diceva «la tela
    concessa in `SESSIONE`», e un utente che trascina una finestra perdeva la
    sessione (§7.1, eccezione 4 di §3).
    """
    return (SERVER, CONTROLLO, CONTINUA, stream,
            msg(TELA, struct.pack("!BBII", esito, 0, lar, alt)))


def chiave(stream=8, coda=64, **campi):
    return [apre_la_sessione(),
            (SERVER, VIDEO, FIN, stream, f24.intestazione(**campi) + b"\x00" * coda)]


# ⛔ Ogni prova dichiara il proprio codice d'uscita PRIMA di essere girata, e
#    `tela` sta qui e non nei predefiniti perche' P5 si prova **cambiandola**.
PROVE = {
    "buona": {
        "spiega": "⭐ un fotogramma chiave conforme in tre blocchi sullo stesso "
                  "stream, dopo `SESSIONE`: e' il caso che la fase 2 esiste "
                  "per produrre, ⛔ ed e' il caso che RISPETTA tutte e sei le "
                  "righe del 12 agosto in un colpo",
        "uscita": 0,
        "blocchi": lambda: [
            apre_la_sessione(),
            (SERVER, VIDEO, CONTINUA, 8, f24.intestazione()),
            (SERVER, VIDEO, CONTINUA, 8, b"\x00" * 2048),
            (SERVER, VIDEO, FIN, 8, b"\x00" * 2048)],
    },
    "abbandonato": {
        "spiega": "⭐⛔ uno stream AZZERATO a meta' — §5.1, il server abbandona "
                  "un fotogramma **di proposito**.  ⛔ Esce **0**: il "
                  "fotogramma si butta e **la sessione regge**.  ⚠ Senza il "
                  "campo `fine` questa registrazione era indistinguibile da "
                  "una troncata per errore, ed e' la forma E8 per cui P7 e' "
                  "stata scritta",
        "uscita": 0,
        "blocchi": lambda: [
            apre_la_sessione(),
            (SERVER, VIDEO, CONTINUA, 8, f24.intestazione()),
            (SERVER, VIDEO, RESET, 8, b"\x00" * 10240)],
    },
    "stream-non-chiuso": {
        "spiega": "⛔ l'ultimo blocco del flusso porta `fine = 0`: lo stream "
                  "non si chiude dentro il file.  Esce **0** — non c'e' "
                  "nessuna violazione — ⛔ ma la completezza si dichiara NON "
                  "giudicata, che e' un fatto diverso da «giudicata e va bene»",
        "uscita": 0,
        "blocchi": lambda: [
            apre_la_sessione(),
            (SERVER, VIDEO, CONTINUA, 8, f24.intestazione() + b"\x00" * 64)],
    },
    "formato-vecchio": {
        "spiega": "⛔⛔ una registrazione «RCPREG 0x00 0x01», il formato di "
                  "ieri.  §11.1: *«un validatore vecchio deve RIFIUTARE il "
                  "formato nuovo, non leggerlo di traverso»* — e vale nei due "
                  "versi.  ⛔ Esce **2**: e' un difetto del FILE, non del filo, "
                  "e la cura e' rigenerarlo",
        "uscita": 2,
        "magia": MAGIA_VECCHIA,
        "blocchi": lambda: chiave(),
    },
    "tipo-storto": {
        "spiega": "`tipo = 0x0300` nell'intestazione: §6.2 «Altri valori: "
                  "ERRORE_PROTOCOLLO»",
        "uscita": 1,
        "blocchi": lambda: chiave(tipo=0x0300),
    },
    "verso-sbagliato": {
        "spiega": "un fotogramma DAL CLIENT: §2.5, il canale nel verso "
                  "sbagliato",
        "uscita": 1,
        "blocchi": lambda: [apre_la_sessione(),
                            (CLIENT, VIDEO, FIN, 9,
                             f24.intestazione() + b"\x00" * 64)],
    },
    # ── ⭐⛔ LE SEI RIGHE DEL 12 AGOSTO, UNA PROVA PER CIASCUNA ──────────────
    "p1-prima-di-sessione": {
        "spiega": "⭐⛔ **P1 violata** — uno stream video si apre e nel file "
                  "`SESSIONE` non e' ancora passata.  ⛔ E la prova che la "
                  "RISPETTA e' `buona`: gli stessi byte, con il blocco di "
                  "`SESSIONE` davanti",
        "uscita": 1,
        "blocchi": lambda: [(SERVER, VIDEO, FIN, 8,
                             f24.intestazione() + b"\x00" * 64)],
    },
    "p2-numero-zero": {
        "spiega": "⭐⛔ **P2 violata** — `numero = 0`, che §6.2 riserva a "
                  "«nessun fotogramma» dal 12 agosto 2026",
        "uscita": 1,
        "blocchi": lambda: chiave(num=0),
    },
    "p3-video-sul-controllo": {
        "spiega": "⭐⛔ **P3 violata** — l'intestazione di 28 byte scritta "
                  "sullo **stesso stream** su cui viaggia il canale di "
                  "controllo.  ⛔ E' l'unico posto in cui il server puo' "
                  "sbagliare stream: §2.5 gli vieta di aprire bidirezionali",
        "uscita": 1,
        "blocchi": lambda: [apre_la_sessione(),
                            (SERVER, VIDEO, FIN, 0,
                             f24.intestazione() + b"\x00" * 64)],
    },
    "p4-fin-prima-dei-28": {
        "spiega": "⭐⛔ **P4 violata** — lo stream si chiude con **FIN** dopo "
                  "12 byte: non e' un fotogramma corto, e' una lunghezza che "
                  "non torna (§6.2, terza riga)",
        "uscita": 1,
        "blocchi": lambda: [apre_la_sessione(),
                            (SERVER, VIDEO, FIN, 8,
                             f24.intestazione()[:12])],
    },
    "p5-misura-diversa": {
        "spiega": "⭐⛔ **P5 violata** — un fotogramma 1280x720 su una tela "
                  "concessa 1920x1080",
        "uscita": 1,
        "blocchi": lambda: chiave(lar=1280, alt=720),
    },
    "p5-misura-dopo-adatta-tela": {
        "spiega": "⭐⛔ **P5 rispettata, ed e' la prova che ha corretto "
                  "`RCP.md`** — gli **stessi identici byte** di "
                  "`p5-misura-diversa`, ma fra `SESSIONE` e il fotogramma "
                  "passa un `TELA(ADATTATA, 1280, 720)` (§7.1).  ⛔ Con la "
                  "prima stesura di P5 — «la tela concessa in `SESSIONE`» — "
                  "questa registrazione usciva **1**: il client uccideva la "
                  "sessione perche' l'utente aveva trascinato una finestra.  "
                  "⚠ Senza questa prova la regola nuova sarebbe severa quanto "
                  "quella sbagliata di prima, e nessun banco lo direbbe",
        "uscita": 0,
        "blocchi": lambda: [
            apre_la_sessione(),
            adatta_la_tela(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.intestazione(lar=1280, alt=720) + b"\x00" * 64)],
    },
    "p5-misura-uguale-a-una-tela-diversa": {
        "spiega": "⭐ **P5 rispettata, e NON con la tela predefinita** — gli "
                  "**stessi byte** della prova qui sopra, con la tela concessa "
                  "a 1280x720.  ⛔ Senza questa prova, un arbitro che "
                  "confrontasse con un 1920x1080 scritto a mano sarebbe verde "
                  "su tutte le altre",
        "uscita": 0,
        "tela": (1280, 720),
        "blocchi": lambda: chiave(lar=1280, alt=720),
    },
    # ── ⛔⛔ D14 — I FOTOGRAMMI IN VOLO, e la proposta **P8** ────────────────
    "p8-in-volo-dopo-adatta-tela": {
        "spiega": "⛔⛔ **D14, LA REGISTRAZIONE DI UNA SESSIONE SANA UCCISA** — "
                  "`SESSIONE` a 1920x1080, poi un `TELA(ADATTATA, 1280, 720)` "
                  "(§7.1), e **poi** arriva il flusso video che porta ancora "
                  "1920x1080: e' il fotogramma aperto **prima** che "
                  "l'`ADATTA_TELA` arrivasse al server.  ⛔ §6.2 alla lettera "
                  "farebbe uscire **1** — la sessione cade — e §6.2 **stesso** "
                  "dice che «gli stream sono indipendenti, quindi i fotogrammi "
                  "possono arrivare fuori ordine».  ⇒ Esce **0**, con il flusso "
                  "dichiarato `AMBIGUO` e la proposta **P8** accanto: un "
                  "arbitro che uscisse 1 certificherebbe che un client "
                  "conforme deve uccidere una sessione sana.  ⚠ E il "
                  "**secondo** di grazia da qui non si giudica: §11.1 non porta "
                  "istanti, e l'arbitro lo dichiara invece di indovinarlo",
        "uscita": 0,
        "blocchi": lambda: [
            apre_la_sessione(),
            adatta_la_tela(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.intestazione(lar=1920, alt=1080, num=41) + b"\x00" * 64)],
    },
    "p8-misura-di-nessuna-tela": {
        "spiega": "⭐⛔ **P8 copre UNA misura, non «tutto dopo un `TELA`»** — "
                  "stessa registrazione, ma il fotogramma porta 800x600: ⛔ ne' "
                  "la tela in vigore (1280x720) ne' la precedente (1920x1080). "
                  "Non era in volo, e' un campo sbagliato — esce **1**, e deve "
                  "uscire 1.  ⚠ **E' la prova che conta**: senza, una cura "
                  "scritta «dopo un `TELA` la misura non si controlla» "
                  "passerebbe la prova qui sopra e spegnerebbe P5 proprio nella "
                  "finestra in cui il server e' piu' probabile che sbagli — ed "
                  "e' esattamente cosi' che P5 e' finita sbagliata la prima "
                  "volta",
        "uscita": 1,
        "blocchi": lambda: [
            apre_la_sessione(),
            adatta_la_tela(1280, 720),
            (SERVER, VIDEO, FIN, 8,
             f24.intestazione(lar=800, alt=600, num=41) + b"\x00" * 64)],
    },
    "p6-primo-delta": {
        "spiega": "⭐⛔ **P6 violata** — il primo fotogramma dopo `SESSIONE` e' "
                  "un delta (`0x0302`).  ⚠ Fino all'11 agosto era conforme a "
                  "ogni riga, e il sintomo sarebbe stato «il desktop compare a "
                  "pezzi»",
        "uscita": 1,
        "blocchi": lambda: chiave(tipo=0x0302),
    },
    "p6-delta-dopo-la-chiave": {
        "spiega": "⭐ **P6 rispettata dalla parte difficile** — chiave sullo "
                  "stream 8, **poi** un delta sullo stream 9.  ⛔ Senza questa "
                  "prova, un arbitro che avesse capito «i delta non si "
                  "accettano» resterebbe verde su tutto e fermerebbe il video "
                  "dalla fase 3 in poi",
        "uscita": 0,
        "blocchi": lambda: [
            apre_la_sessione(),
            (SERVER, VIDEO, FIN, 8, f24.intestazione(num=1) + b"\x00" * 64),
            (SERVER, VIDEO, FIN, 9,
             f24.intestazione(tipo=0x0302, num=2) + b"\x00" * 64)],
    },
    # ── i tre esiti che non sono un giudizio sul filo ───────────────────────
    "solo-controllo": {
        "spiega": "⛔ una registrazione di sola stretta di mano: ZERO blocchi "
                  "video.  «Non ho niente da giudicare» e «ho giudicato tutto "
                  "e va bene» sono due fatti diversi",
        "uscita": 3,
        "blocchi": lambda: [(CLIENT, CONTROLLO, CONTINUA, 0, msg(0x0001))],
    },
    "coda-di-troppo": {
        "spiega": "⛔ `quanti_blocchi` sotto-dichiarato: del filo che nessuno "
                  "giudica.  E' un difetto del FILE, non del filo",
        "uscita": 2,
        "blocchi": None,
    },
    "canale-ignoto": {
        "spiega": "un byte alto che non e' nessuno dei cinque di §2.5",
        "uscita": 1,
        "blocchi": lambda: [apre_la_sessione(),
                            (SERVER, 0x09, FIN, 8, b"\x00" * 28)],
    },
    "controllo-illeggibile": {
        "spiega": "⛔ il canale di controllo non si sfoglia — un messaggio che "
                  "dichiara piu' corpo di quanto ce ne sia — e c'e' un flusso "
                  "video conforme.  ⭐ Esce **0**, ⛔ ma P1 si dichiara NON "
                  "giudicata: «allora era dopo `SESSIONE`» sarebbe la forma "
                  "**E8**.  ⚠ E a giudicare quel canale e' "
                  "`01-b4-validatore.py`, non questo",
        "uscita": 0,
        "blocchi": lambda: [
            (SERVER, CONTROLLO, CONTINUA, 0, struct.pack("!HI", SESSIONE, 99)),
            (SERVER, VIDEO, FIN, 8, f24.intestazione() + b"\x00" * 64)],
    },
    "fine-fuori-intervallo": {
        "spiega": "⛔ `fine = 7`, e §11.1 ne definisce **tre**.  ⚠ Prova che il "
                  "campo nuovo e' letto e non solo saltato: senza, un "
                  "registratore che scrivesse spazzatura in quel byte "
                  "passerebbe, e con lui ogni giudizio di completezza",
        "uscita": 2,
        "blocchi": lambda: [(SERVER, VIDEO, 7, 8, f24.intestazione())],
    },
}

# ⛔ QUALE PROVA FA SCATTARE QUALE RIGA, E QUALE LA RISPETTA — e il conto lo
#    calcola `regole_coperte()`, che le **cerca** in `PROVE`.
REGOLE_NUOVE = {
    "P1": ("RCP.md §2.5", "p1-prima-di-sessione", "buona"),
    "P2": ("RCP.md §6.2", "p2-numero-zero", "buona"),
    "P3": ("RCP.md §2.5", "p3-video-sul-controllo", "buona"),
    "P4": ("RCP.md §6.2", "p4-fin-prima-dei-28", "buona"),
    "P5": ("RCP.md §6.2", "p5-misura-diversa", "p5-misura-dopo-adatta-tela"),
    "P6": ("RCP.md §5.2", "p6-primo-delta", "p6-delta-dopo-la-chiave"),
    "P7": ("RCP.md §11.1", "formato-vecchio", "abbandonato"),
}


# ⛔⛔ E LE PROPOSTE ANCORA APERTE, IN UNA TABELLA A PARTE — quel che `RCP.md`
#    NON dice ancora.  ⚠ La separazione e' la cosa importante: sopra ci sono
#    righe normative da rileggere nel documento, qui una cura che il
#    coordinatore non ha applicato.  ⛔ E la coppia ha una forma diversa: la
#    prova che la fa VEDERE esce **0** (l'arbitro dichiara, non condanna) e
#    quella che tiene la cura stretta esce **1**.
PROPOSTE_APERTE = {
    "P8": ("RCP.md §6.2 contro §7.1 — difetto D14",
           "p8-misura-di-nessuna-tela", "p8-in-volo-dopo-adatta-tela"),
}


def proposte_coperte():
    """⛔ Come `regole_coperte()`, per le cure che il documento non ha ancora."""
    coperte, mancanti = [], []
    for sigla, (_, stretta, vede) in PROPOSTE_APERTE.items():
        buchi = []
        if stretta not in PROVE:
            buchi.append(f"manca la prova che la tiene STRETTA («{stretta}»)")
        elif PROVE[stretta]["uscita"] != 1:
            buchi.append(f"«{stretta}» non pretende uscita 1: una cura senza "
                         f"questa prova si scrive troppo larga")
        if vede not in PROVE:
            buchi.append(f"manca la prova che la fa VEDERE («{vede}»)")
        elif PROVE[vede]["uscita"] != 0:
            buchi.append(f"«{vede}» non pretende uscita 0")
        (mancanti if buchi else coperte).append(
            (sigla, "; ".join(buchi)) if buchi else sigla)
    return coperte, mancanti


def regole_coperte():
    """⛔ Quante righe hanno DAVVERO la prova che le viola e quella che le
       rispetta, **cercate in `PROVE`** — mai un numero scritto a mano."""
    coperte, mancanti = [], []
    for sigla, (_, viola, rispetta) in REGOLE_NUOVE.items():
        buchi = []
        if viola not in PROVE:
            buchi.append(f"manca la prova che la VIOLA («{viola}»)")
        elif PROVE[viola]["uscita"] not in (1, 2):
            buchi.append(f"«{viola}» non pretende un rifiuto")
        if rispetta not in PROVE:
            buchi.append(f"manca la prova che la RISPETTA («{rispetta}»)")
        elif PROVE[rispetta]["uscita"] != 0:
            buchi.append(f"«{rispetta}» non pretende uscita 0")
        (mancanti if buchi else coperte).append(
            (sigla, "; ".join(buchi)) if buchi else sigla)
    return coperte, mancanti


def fabbrica(cartella):
    fatti = []
    for nome, v in PROVE.items():
        p = os.path.join(cartella, f"02-filo-prova-{nome}.rcpreg")
        magia = v.get("magia", MAGIA)
        if v["blocchi"] is None:
            # la coda di spazzatura si costruisce a mano
            scrivi_reg(p, chiave())
            with open(p, "ab") as fh:
                fh.write(b"spazzatura")
        else:
            scrivi_reg(p, v["blocchi"](), magia=magia)
        fatti.append((nome, p, v["uscita"], v["spiega"],
                      v.get("tela", (1920, 1080))))
        print(f"   {os.path.basename(p):50s} atteso uscita {v['uscita']}")
        print(f"   {'':50s} {v['spiega']}")
    return fatti


def gira_prove(cartella, guasti=(), stampa=True):
    """⛔ Ogni prova dichiara il proprio codice d'uscita PRIMA di essere girata."""
    fatti = fabbrica(cartella) if stampa else _fabbrica_muta(cartella)
    guastati, righe = 0, []
    if stampa:
        print()
    for nome, p, atteso, spiega, tela in fatti:
        try:
            visto, _ = valida(p, guasti=guasti, tela=tela, stampa=False)
        except NonConforme:
            visto = 1
        except Malformata:
            visto = 2
        except NienteDaGiudicare:
            visto = 3
        except OSError:
            visto = 2
        ok = visto == atteso
        guastati += int(not ok)
        righe.append({"prova": nome, "atteso": atteso, "visto": visto,
                      "esito": bool(ok)})
        if stampa:
            print(f"    {VERDE if ok else ROSSO}{'OK' if ok else 'NO'}{GRIGIO}  "
                  f"{nome:36s} uscita {visto} (atteso {atteso})")
            if not ok:
                print(f"        {spiega}")
    return guastati, righe


def _fabbrica_muta(cartella):
    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        return fabbrica(cartella)


P7 = (
    "§11.1, il blocco della registrazione — come e' finito lo stream",
    "⭐ APPLICATA A `RCP.md` IL 12 AGOSTO 2026.  Il blocco porta, dopo "
    "`canale`, un `u8 fine`: `0` = lo stream continua, `1` = chiuso con "
    "**FIN**, `2` = azzerato con **RESET_STREAM**; e la magia e' passata a "
    "`\"RCPREG\" 0x00 0x02` perche' il blocco cambia misura — 17 byte invece "
    "di 16 — e un validatore vecchio DEVE rifiutare il formato nuovo invece di "
    "leggerlo di traverso.  Senza quel campo un fotogramma abbandonato (§5.1, "
    "legale) e uno troncato per errore (§3, la connessione cade) avevano lo "
    "stesso aspetto nella registrazione, cioe' l'arbitro non poteva applicare "
    "la riga che §6.2 ha aggiunto apposta il 9 agosto 2026.")


def scrivi_esito(percorso, rec):
    if not percorso:
        print("    ⚠ nessun --uscita: questo giro NON lascia registro")
        return False
    fuori = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "banco": "F2.4-validatore",
             "scena": "registrazioni fabbricate da questo stesso file, nel "
                      "formato di RCP.md §11.1: nessuna rete e nessun server",
             "macchina": os.uname().nodename}
    fuori.update(rec)
    try:
        with open(percorso, "a") as f:
            f.write(json.dumps(fuori, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except OSError as e:
        print(f"    {ROSSO}⛔ il registro «{percorso}» non si scrive: {e}{GRIGIO}")
        return False
    return True


def certifica(a):
    """⛔ sano -> G4 -> risanato.  E G4 e' LO STATO DI OGGI DI `01-b4`.

    Il guasto da innestare non e' inventato: e' *«il validatore salta il canale
    video»*, cioe' la riga 521 di `01-b4-validatore.py`.  ⭐ Certificare contro
    quel guasto e' l'unico modo di dimostrare che questo file **aggiunge**
    qualcosa invece di ripetere B4 con altre parole.
    """
    print("\n== ⛔ LA CERTIFICAZIONE — sano -> G4 -> risanato")
    print("   G4: «l'arbitro salta il canale video», che e' quel che")
    print("       `01-b4-validatore.py` fa oggi (la sua riga 521).")
    print("   atteso sano:   0 prove sbagliate")
    print("   atteso guasto: le prove che devono uscire 1 escono 3 —")
    print("                  «niente da giudicare» — perche' il canale video")
    print("                  non viene guardato.  ⛔ E NON escono 0: un")
    print("                  arbitro che salta tutto non assolve, dichiara")
    print("                  di non aver guardato.  Se uscisse 0 il guasto")
    print("                  sarebbe passato per un verde\n")
    sano, righe_sane = gira_prove(a.cartella, guasti=())
    print()
    rotto, righe_rotte = gira_prove(a.cartella, guasti=("G4",))
    print()
    # ⛔ LA MARCA, CON LE SUE DUE META' (R12-A.3): il giro guasto la deve dire
    #    e il giro sano NON la deve gia' dire.
    marca_rotto = sum(1 for r in righe_rotte
                      if r["atteso"] == 1 and r["visto"] == 3)
    marca_sano = sum(1 for r in righe_sane
                     if r["atteso"] == 1 and r["visto"] == 3)
    risanato, _ = gira_prove(a.cartella, guasti=(), stampa=False)
    ok = (sano == 0 and rotto > 0 and marca_rotto > 0 and marca_sano == 0
          and risanato == 0)
    print(f"    {VERDE if ok else ROSSO}{'OK' if ok else 'NO'}{GRIGIO}  G4  "
          f"sano {sano} -> guasto {rotto} -> risanato {risanato}   "
          f"marca «uscita 3 dove ne serviva 1»: {marca_rotto} volte col "
          f"guasto, {marca_sano} volte da sano")
    scrivi_esito(a.uscita, {"tipo": "certificazione", "guasto": "G4",
                            "sano": sano, "guasto_conta": rotto,
                            "risanato": risanato, "marca_col_guasto": marca_rotto,
                            "marca_da_sano": marca_sano, "esito": bool(ok),
                            "prove_sane": righe_sane, "prove_rotte": righe_rotte})
    print()
    if ok:
        print(f"    {VERDE}⭐ 02-filo-validatore.py e' CERTIFICATO{GRIGIO}")
        return 0
    print(f"    {ROSSO}⛔ NON certificato{GRIGIO}")
    return 1


def principale(a):
    if a.elenco:
        print("== le registrazioni di prova, e il codice d'uscita atteso di "
              "ciascuna")
        print("   ⛔ Ogni riga e' una PREVISIONE, scritta prima del giro\n")
        for nome, v in PROVE.items():
            print(f"  {nome:36s} uscita {v['uscita']}"
                  + (f"   tela {v['tela'][0]}x{v['tela'][1]}"
                     if "tela" in v else ""))
            print(f"  {'':36s}   {v['spiega']}")
        print(f"\n== ⭐⛔ LE RIGHE DEL 12 AGOSTO, E LE DUE PROVE DI CIASCUNA")
        coperte, mancanti = regole_coperte()
        for sigla, (dove, viola, rispetta) in REGOLE_NUOVE.items():
            print(f"  {sigla}  {dove}")
            print(f"      la VIOLA:    {viola}")
            print(f"      la RISPETTA: {rispetta}")
        print(f"\n  ⛔ righe con TUTT'E DUE le prove: {len(coperte)} su "
              f"{len(REGOLE_NUOVE)} — {', '.join(coperte) or '—'}")
        for sigla, perche in mancanti:
            print(f"     {ROSSO}⛔ {sigla}: {perche}{GRIGIO}")
        print(f"\n== ⛔⛔ LE PROPOSTE ANCORA APERTE — `RCP.md` non le porta")
        print(f"      ⚠ La coppia ha una forma diversa: la prova che la fa "
              f"VEDERE esce 0")
        print(f"        (l'arbitro dichiara, non condanna) e quella che tiene "
              f"la cura")
        print(f"        STRETTA esce 1 — ed e' la seconda quella che conta")
        ap_coperte, ap_mancanti = proposte_coperte()
        for sigla, (dove, stretta, vede) in PROPOSTE_APERTE.items():
            print(f"  {sigla}  {dove}")
            print(f"      la fa VEDERE:   {vede}")
            print(f"      la tiene STRETTA: {stretta}")
        print(f"\n  ⛔ proposte con TUTT'E DUE le prove: {len(ap_coperte)} su "
              f"{len(PROPOSTE_APERTE)} — {', '.join(ap_coperte) or '—'}")
        for sigla, perche in ap_mancanti:
            print(f"     {ROSSO}⛔ {sigla}: {perche}{GRIGIO}")
        print(f"\n== ⭐ P7 — {P7[0]}")
        print(f"      «{P7[1]}»")
        return 0
    if a.fabbrica:
        print("== le registrazioni di prova, nel formato di RCP.md §11.1\n")
        fabbrica(a.cartella)
        return 0
    if a.certifica:
        return certifica(a)
    if not a.registrazione:
        # ⛔ Senza un file non si gira in silenzio: si dice che non c'e' niente
        #    da giudicare, con il codice che quel fatto ha.
        print("== ⛔ nessuna registrazione da giudicare.")
        print("   Le prove si fabbricano con --fabbrica, il giro con "
              "--certifica.")
        return 3

    # ⛔ IL CONTROLLO POSITIVO, PRIMA del verdetto e non dopo: si verifica che
    #    questo strumento sappia trovare un errore che c'e' di sicuro, e solo
    #    dopo lo si punta sull'incognita (`LEZIONI.md` §1.2).
    print("== ⛔ il controllo positivo, PRIMA di puntare l'arbitro "
          "sull'incognita")
    guastati, _ = gira_prove(a.cartella)
    if guastati:
        print(f"\n    {ROSSO}⛔ l'arbitro sbaglia su {guastati} registrazioni "
              f"note: non e' il caso di credergli su una nuova{GRIGIO}")
        return 2
    print(f"\n    {VERDE}⭐ l'arbitro e' d'accordo su tutte le prove note"
          f"{GRIGIO}\n")

    try:
        codice, conta = valida(a.registrazione, tela=(a.tela_larghezza,
                                                      a.tela_altezza),
                               codec=a.codec)
    except NonConforme as e:
        print(f"\n   {ROSSO}⛔ NON CONFORME — {e.regola}{GRIGIO}")
        print(f"      {e.dice}")
        print(f"      byte {e.ass} nel file · scostamento {e.rel} nel carico "
              f"del blocco")
        scrivi_esito(a.uscita, {"tipo": "giudizio", "file": a.registrazione,
                                "uscita": 1, "regola": e.regola, "dice": e.dice,
                                "byte": e.ass})
        return 1
    except Malformata as e:
        print(f"\n   ⚠ REGISTRAZIONE MALFORMATA: {e}")
        print("      ⛔ Non e' un giudizio sul filo: e' un difetto del file.")
        scrivi_esito(a.uscita, {"tipo": "giudizio", "file": a.registrazione,
                                "uscita": 2, "dice": str(e)})
        return 2
    except NienteDaGiudicare as e:
        print(f"\n   ⛔ NIENTE DA GIUDICARE: {e}")
        print("      Non e' «conforme»: e' l'assenza dell'oggetto del "
              "giudizio.")
        print("      Si guarda il registratore — chi doveva scrivere quei "
              "byte.")
        scrivi_esito(a.uscita, {"tipo": "giudizio", "file": a.registrazione,
                                "uscita": 3, "dice": str(e)})
        return 3
    except OSError as e:
        # ⛔ E8: «vuoto» e «proibito» hanno lo stesso aspetto.
        print(f"\n   ⚠ LA REGISTRAZIONE NON SI LEGGE: {e}")
        print("      ⛔ Non e' un giudizio sul filo, e non e' «il file e' "
              "rotto»:")
        print("         e' che non si e' potuto aprire.  Si guardano permessi,")
        print("         percorso e volume — non RCP.md.")
        return 2
    scrivi_esito(a.uscita, {"tipo": "giudizio", "file": a.registrazione,
                            "uscita": 0, **conta})
    return codice


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="F2.4 — l'arbitro meccanico del canale video")
    p.add_argument("registrazione", nargs="?")
    p.add_argument("--fabbrica", action="store_true",
                   help="costruisce le registrazioni di prova")
    p.add_argument("--certifica", action="store_true",
                   help="sano -> G4 -> risanato")
    p.add_argument("--elenco", action="store_true",
                   help="le previsioni e la proposta P7, senza misurare")
    p.add_argument("--cartella", default=os.path.join(QUI, "02-filo-prove"),
                   help="dove stanno le registrazioni di prova")
    p.add_argument("--tela-larghezza", type=int, default=1920)
    p.add_argument("--tela-altezza", type=int, default=1080)
    p.add_argument("--codec", type=int, default=1, help="1 = HEVC, 2 = AV1")
    p.add_argument("--uscita", default="", help="il registro del giro, in JSONL")
    a = p.parse_args()
    os.makedirs(a.cartella, exist_ok=True)
    sys.exit(principale(a))
