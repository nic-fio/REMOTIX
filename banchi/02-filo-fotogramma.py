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

     ⛔ E ogni `AMBIGUO` porta **il testo che si propone a `RCP.md`**, pronto
     da incollare: un'ambiguita' segnalata senza la cura e' un reclamo.

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
        self.tela_larghezza, self.tela_altezza = tela
        self.codec_negoziato = codec_negoziato
        self.sessione_aperta = sessione_aperta
        # ⛔ `None` e' «nessuno», e NON e' zero: §6.0 vieta i valori sentinella
        #    impliciti, e zero e' un `numero` che il documento non esclude —
        #    vedi il caso `numero-zero`, che e' l'ambiguita' A1.
        self.ultimo_consegnato = None
        self.chiave_consegnata = False
        self.chiedi_chiave = False    # §5.2: il client DEVE chiederla su un buco


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

    # -- l'esito si scrive una volta sola: il primo verdetto e' la causa, i
    #    successivi sono conseguenze (come `_cade` in `01-b3-cliente.py`).
    def _decidi(self, v):
        if self.verdetto is None:
            self.verdetto = v
        return self.verdetto

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
            # ⛔ FIN prima dei 28 byte.  §6.2 dice «la fine dello stream e' la
            #    fine del fotogramma»: letta alla lettera, uno stream di 12
            #    byte e' un fotogramma con **meno sedici** byte di dati.  Il
            #    verdetto qui e' §3 — *«una lunghezza che non torna»* — e
            #    ⚠ **e' derivato, non citato**: vedi la proposta P4.
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §3 (per §6.2)",
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

        # 2. ⭐⛔ DOVE E' ARRIVATO — l'ambiguita' A3, e non e' teorica.
        #
        #    §2.5 dice, per il canale di controllo, «su uno stream
        #    unidirezionale e' ERRORE_PROTOCOLLO», e per l'audio «su uno stream
        #    e' ERRORE_PROTOCOLLO».  ⛔ Per il **video** la stessa tabella dice
        #    soltanto che cosa segue il tipo, e **non dice su che stream vive**.
        #    Il server non apre stream bidirezionali (§2.5), quindi l'unico
        #    posto in cui puo' scrivere un `0x03` fuori posto e' il canale di
        #    controllo, che il client gli ha aperto.
        if self.dove == "controllo":
            return self._decidi(Verdetto(
                AMBIGUO, "RCP.md §2.5",
                "un fotogramma sul canale di CONTROLLO: §2.5 vieta per nome il "
                "controllo su uno stream unidirezionale e l'audio su uno "
                "stream, e per il video non dice niente",
                scostamento=0, propone="P3"))

        # 3. ⛔ LO STATO — §1 «l'ordine dei cinque passi non ammette permute»,
        #    §3 «un messaggio arrivato nello stato sbagliato», e l'invariante
        #    **I3**: *chi non passa dal validatore non riceve un pixel*.
        #    ⚠ Derivato: §2.5 lo scrive per il canale di **input** («aperto
        #      dopo aver ricevuto `SESSIONE`») e per il video no.  Proposta P1.
        if not self.c.sessione_aperta:
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §3 (per §1, I3)",
                "un fotogramma prima di `SESSIONE`: la guardia parte da negato "
                "— chi non passa dal validatore non riceve un pixel",
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
        if num == 0:
            return self._decidi(Verdetto(
                AMBIGUO, "RCP.md §6.2 contro §7.1, per §6.0",
                "`numero = 0`: §7.1 usa lo zero come «nessuno» in "
                "`RICHIEDI_CHIAVE`, §6.2 non dice da dove parte il contatore, "
                "e §6.0 vieta i sentinella impliciti",
                scostamento=12, propone="P2"))

        # 7. ⭐⛔ LA MISURA — l'ambiguita' A4.
        #
        #    §6.2: «⛔ In RCP/1 e' **sempre** quella della tela, e il client
        #    riscala».  ⚠ «e' sempre» descrive, non comanda: §0 dichiara
        #    normativo solo cio' che porta DEVE / NON DEVE / PUO'.  E non c'e'
        #    nessuna riga che dica **che cosa fa chi riceve** una misura
        #    diversa: chiudere, o riscalare come fa gia' per la vista?
        if (lar, alt) != (self.c.tela_larghezza, self.c.tela_altezza):
            return self._decidi(Verdetto(
                AMBIGUO, "RCP.md §6.2",
                f"il fotogramma e' {lar}x{alt} e la tela concessa e' "
                f"{self.c.tela_larghezza}x{self.c.tela_altezza}: «e' sempre "
                f"quella della tela» non dice che cosa fa chi riceve",
                scostamento=4, propone="P5"))

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

        # 9. ⭐⛔ IL PRIMO FOTOGRAMMA E' UN DELTA — l'ambiguita' A1, ed e'
        #    quella che morde in QUESTA fase.
        #
        #    §5.2: un delta e' la differenza da quelli precedenti, e «a un
        #    delta mancante il decodificatore **non solleva nessun errore**, si
        #    limita a produrre immagini via via piu' sfasciate».  ⛔ Nessuna
        #    riga di `RCP.md` dice che il primo fotogramma di una sessione
        #    DEVE essere una chiave.
        #    ⇒ Un server che apre la sessione con un delta e' **conforme a ogni
        #      riga del documento**, e la fase 2 — che consegna un fotogramma
        #      fermo — mostrerebbe spazzatura senza che nessuno abbia torto.
        #    ⚠ E il client non se ne accorgerebbe da §5.2: non c'e' nessun buco
        #      nella successione dei `numero` (e' il primo), e il decodificatore
        #      non rifiuta niente.
        if tipo == DELTA and not self.c.chiave_consegnata:
            return self._decidi(Verdetto(
                AMBIGUO, "RCP.md §5.2",
                "il primo fotogramma della sessione e' un DELTA: nessuna riga "
                "obbliga il server a cominciare con una chiave, e il client "
                "non ha nessun buco da cui accorgersene",
                scostamento=0, propone="P6"))

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
# ⛔ LE PROPOSTE A `RCP.md`, CON IL TESTO PRONTO.
#
#    Stanno **qui** e non nel rapporto soltanto perche' il banco le stampa: la
#    copia normativa e' `fasi/rapporti/F2-4-filo.md`.  ⛔ E `RCP.md` non si
#    tocca da qui: lo tocca il coordinatore, o sei agenti si sovrascrivono
#    l'arbitro.
PROPOSTE = {
    "P1": ("§2.5, riga «video» della tabella — quando il video PUO' cominciare",
           "Il server NON DEVE aprire uno stream video prima di aver spedito "
           "`SESSIONE`; chi ne riceve uno prima chiude con `ERRORE_PROTOCOLLO`."),
    "P2": ("§6.2, campo `numero` — da dove parte il contatore",
           "Il primo fotogramma di una sessione porta `numero = 1`; **0 e' "
           "riservato** e vuol dire «nessun fotogramma», che e' il significato "
           "che §7.1 gli da' in `RICHIEDI_CHIAVE`."),
    "P3": ("§2.5, riga «video» — su che stream vive",
           "Il video vive **solo** su uno stream unidirezionale aperto dal "
           "server: un `0x03` sul canale di controllo e' `ERRORE_PROTOCOLLO`."),
    "P4": ("§6.2 — lo stream che finisce prima dell'intestazione",
           "Uno stream video chiuso con FIN prima dei 28 byte "
           "dell'intestazione e' `ERRORE_PROTOCOLLO`."),
    "P5": ("§6.2, campi `largh.` e `altezza` — che cosa fa chi riceve",
           "In RCP/1 `largh.` e `altezza` **DEVONO** valere la tela concessa "
           "in `SESSIONE`; chi riceve una misura diversa chiude con "
           "`ERRORE_PROTOCOLLO`."),
    "P6": ("§5.2 — il primo fotogramma",
           "Il primo fotogramma che il server spedisce dopo `SESSIONE` **DEVE** "
           "essere una chiave (`0x0301`)."),
}


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


@caso("video-sul-controllo", AMBIGUO,
      "⭐ un fotogramma BEN FORMATO scritto sul canale di controllo.  §2.5 "
      "vieta per nome il controllo su uno stream unidirezionale e l'audio su "
      "uno stream, e per il video **non dice niente**",
      "RCP.md §2.5", dove="controllo")
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
      "FIN dopo 27 byte: uno in meno dei 28.  ⛔ Letta alla lettera, «la fine "
      "dello stream e' la fine del fotogramma» fa di questo un fotogramma con "
      "**meno un** byte di dati",
      "RCP.md §3 (per §6.2)")
def _():
    return [intestazione()[:27]], "fin"


@caso("stream-vuoto", ERRORE_PROTOCOLLO,
      "FIN a zero byte.  ⚠ E' il caso in cui «zero» e «fallimento» si "
      "somigliano di piu': uno stream aperto e chiuso subito",
      "RCP.md §3 (per §6.2)")
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
      "⭐ un fotogramma ben formato **prima di `SESSIONE`**.  E' l'invariante "
      "**I3** sul filo: *chi non passa dal validatore non riceve un pixel*.  "
      "⚠ Il verdetto e' DERIVATO da §3 + §1: §2.5 lo scrive per il canale di "
      "input («aperto dopo aver ricevuto `SESSIONE`») e per il video no — "
      "proposta P1",
      "RCP.md §3 (per §1, I3)",
      contesto={"sessione_aperta": False})
def _():
    return [intestazione() + b"\x00" * 64], "fin"


# ── I numeri (§6.2, §6.0, §7.1) ────────────────────────────────────────────
@caso("numero-zero", AMBIGUO,
      "⭐ `numero = 0` sul primo fotogramma.  §7.1 usa lo zero come «nessuno» "
      "in `RICHIEDI_CHIAVE`, §6.2 non dice da dove parte il contatore, e §6.0 "
      "vieta i sentinella impliciti: `RICHIEDI_CHIAVE(0)` vorrebbe dire due "
      "cose — proposta P2",
      "RCP.md §6.2 contro §7.1, per §6.0")
def _():
    return [intestazione(num=0) + b"\x00" * 64], "fin"


@caso("misura-diversa-dalla-tela", AMBIGUO,
      "⭐ un fotogramma 1280x720 su una tela 1920x1080.  §6.2 dice «e' sempre "
      "quella della tela» — che descrive e non comanda — e non dice che cosa "
      "fa chi riceve: chiudere, o riscalare come gia' fa per la vista? — "
      "proposta P5",
      "RCP.md §6.2")
def _():
    return [intestazione(lar=1280, alt=720) + b"\x00" * 64], "fin"


@caso("primo-fotogramma-delta", AMBIGUO,
      "⭐⛔ il PRIMO fotogramma della sessione e' un delta.  Nessuna riga "
      "obbliga il server a cominciare con una chiave, il decodificatore non "
      "solleva errori su un delta orfano (§5.2), e non c'e' nessun buco nei "
      "`numero` da cui accorgersene: **la fase 2 mostrerebbe spazzatura e "
      "nessuno avrebbe torto** — proposta P6",
      "RCP.md §5.2")
def _():
    return [intestazione(tipo=DELTA) + b"\x00" * 64], "fin"


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
      "⭐ il fotogramma 1 dopo il 4294967295: e' **successivo**, non "
      "precedente.  §6.2 vuole l'aritmetica modulo 2^32 con le differenze con "
      "segno, ⛔ e un confronto `<` diretto farebbe scartare **ogni** "
      "fotogramma dopo il giro, per sempre — a 60 al secondo il contatore gira "
      "dopo due anni e due mesi, e una sessione puo' durare di piu'",
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
    for k, v in campi.items():
        setattr(ctx, k, v)
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
        print(f"\n== ⛔ LE PROPOSTE A `RCP.md`, se le ambiguita' si confermano")
        for sigla, (dove, testo) in PROPOSTE.items():
            print(f"  {sigla}  {dove}")
            print(f"      «{testo}»")
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

    # ⭐⛔ LE AMBIGUITA' DI `RCP.md`, IN FONDO E CON LA CURA ACCANTO.
    if ambigui:
        print(f"\n    {GIALLO}⭐⛔ `RCP.md` AMMETTE DUE LETTURE IN "
              f"{len(ambigui)} PUNTI{GRIGIO}")
        print(f"       ⚠ Non e' un guasto del prodotto e non fa fallire questo")
        print(f"         giro: e' un difetto del DOCUMENTO, e §0 dice che i")
        print(f"         difetti di quel file sono di quel file.")
        for nome, prop, dice in ambigui:
            dove, testo = PROPOSTE.get(prop, ("?", "?"))
            print(f"\n       {nome}")
            print(f"         {dice}")
            print(f"         ⇒ {prop} — {dove}")
            print(f"           «{testo}»")

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
