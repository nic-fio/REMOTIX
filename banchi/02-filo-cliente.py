#!/usr/bin/env python3
"""02-filo-cliente.py — ⛔ F2.4: il cliente di prova RICEVE il fotogramma, e lo giudica.

    python3 02-filo-cliente.py --porta 7514 --utente prova --parola X
    python3 02-filo-cliente.py --porta 7514 --registra t.rcpreg --attesa 20
    python3 02-filo-cliente.py --porta 7514 --violazioni      le prove verso il server
    python3 02-filo-cliente.py --elenco                       le previsioni, senza rete

⚠ Gira DENTRO il contenitore: `aioquic` sta li'.  ⛔ E la porta e' la **7514**,
  che e' quella di F2.4: la 7448 e' il prodotto di casa e la 7501 il bersaglio
  di P5, tutt'e due accese apposta (mandato §4).

⏳ **NON E' ANCORA STATO GIRATO, e va detto.**  Il prodotto della fase 2 non
   esiste — `grep -c '0x0301\\|0x0302' src/rcp.c src/webtransport.c
   src/pagina.html` da' **0 · 0 · 0**, `[M]` 12 agosto 2026 — quindi non c'e'
   nessun server che spedisca un fotogramma.  ⛔ Questo file e' il banco
   **scritto prima del prodotto** che `PIANO.md` §0.4 momento 1 pretende, e il
   suo primo giro e' la prima misura della fase 2.

===========================================================================
⛔ PERCHE' IL SECONDO LETTORE VALE IL DOPPIO QUI, E NON E' UNA RIPETIZIONE

`PIANO.md` §1.1.  Il server e' in **C**, la pagina e' in **JavaScript**, e
tutt'e due li scrive la stessa mano.  Se il server scrivesse `istante` in
little-endian e la pagina lo leggesse in little-endian, ⛔ **il desktop
comparirebbe perfetto** e nessun banco nostro se ne accorgerebbe: i due si sono
capiti su una cosa che `RCP.md` non dice.

Questo programma e' il **terzo lettore**, in un terzo linguaggio, e ⛔ chi lo
fa crescere **non guarda `src/`**.  Il suo valore non e' il verde: e' che chi
lo scrive **deve scegliere** dove `RCP.md` ammette due letture — e quelle
scelte sono l'esito piu' prezioso della fase, non un effetto collaterale.
`FASI.md` §01-filo-nudo ne ha raccolte **dodici** per la stretta di mano; il
capitolo del video ne aggiunge **sette**, ed e' onesto separarle: ⛔ **quattro
sono letture doppie vere** — due implementazioni conformi producono byte
diversi per lo stesso ingresso — e ⚠ **tre sono regole DERIVATE**, cioe' che si
ricavano da §3 e da §1 ma che nessuna riga scrive.  Le prime le tiene
`02-filo-fotogramma.py` con l'esito `AMBIGUO`; le seconde sono scelte del
banco, dichiarate accanto al caso.  ⭐ Confonderle sarebbe gonfiare il conto:
una regola derivata non fa divergere due implementazioni attente, una lettura
doppia si'.

===========================================================================
⛔ CHE COSA GUARDA, E LE PRIME DUE SI DIMENTICANO

  1. ⛔ **che il fotogramma sia ARRIVATO DAVVERO**, e con il denominatore.
     `LEZIONI.md` §1.9: un conteggio senza denominatore non e' una misura.
     ⚠ *«nessuna violazione»* e' vero anche su zero fotogrammi, ed e' il modo
     piu' facile di dichiarare verde una fase che non ha consegnato niente —
     il rilievo **R7.4** di `01-b4-validatore.py`.  ⛔ Qui zero fotogrammi ha
     un **codice d'uscita suo** (`5`), e non e' un verde;

  2. ⛔ **DAL LATO CHE RICEVE** (`CODER.md` §3.8, forma d'errore **E7**).  Il
     registro del server dice che ha chiamato una funzione, non che il byte e'
     arrivato.  In v1 il server scriveva «congedo il client» e il client, alla
     stessa ora, «errore di rete» — **per tre fasi** (`LEZIONI.md` §1.7);

  3. **su quale STREAM** e' arrivato: uno unidirezionale nuovo, aperto dal
     server, uno per fotogramma (§2.5, §5.1).  ⛔ E il canale si riconosce dal
     **byte alto di `tipo`**, mai dal numero dello stream — e' la cura del
     rilievo R11.9;

  4. ⛔ **come e' finito lo stream**: FIN o `RESET_STREAM`, e sono due cose
     diverse (§6.2, rilievo R1.7).  ⭐ **Questo lo puo' fare solo un cliente
     dal vivo**: la registrazione di §11.1 quel campo non ce l'ha, e
     `02-filo-validatore.py` lo dichiara non giudicabile.  Vedi la proposta
     **P7**;

  5. ⛔ **che cosa il client DEVE fare dopo**: su un buco o un abbandono,
     `RICHIEDI_CHIAVE` (§5.2); su una violazione, `CONGEDO` **e** il motivo nel
     codice d'errore della chiusura (§3.1 punti 2 e 3).  ⚠ Un cliente di prova
     che si limitasse a giudicare e tacere non eserciterebbe **nessuno** degli
     obblighi che §5.2 mette sul client — ed e' la meta' del protocollo che
     nessun banco del server puo' vedere.

===========================================================================
⛔ E REGISTRA, NEL FORMATO DI §11.1

Ogni byte che arriva finisce in una registrazione che `02-filo-validatore.py`
puo' giudicare.  ⭐ Cosi' il fotogramma viene letto **due volte da due
programmi**: qui dal vivo, e dopo dall'arbitro meccanico.  ⚠ E se i due
dicessero cose diverse sarebbe una misura, non un incidente.

⛔ **La parola d'ordine si oscura**, come nella fase 1: lunghezza vera, byte
sostituiti con `0x2A`, impronta di quel che c'era (§11.1).

===========================================================================
⛔ I CODICI D'USCITA, E SONO SEI PERCHE' I FATTI SONO SEI

  0  ⭐ e' arrivato almeno un fotogramma e ogni fotogramma e' conforme
  1  ⛔ un fotogramma NON e' conforme — e si dice quale byte e quale regola
  2  la stretta di mano non e' arrivata a `SESSIONE` (non si e' provato niente)
  3  ⛔ `RCP.md` ammette due letture su quel che e' arrivato: non e' un verde
     e non e' un rosso.  Vedi `02-filo-fotogramma.py --elenco`
  4  la connessione o la sessione sono cadute prima della fine dell'attesa
  5  ⛔ ZERO fotogrammi.  «Non ho niente da giudicare» non e' «va tutto bene»
"""
import argparse
import asyncio
import hashlib
import importlib.util
import json
import os
import ssl
import struct
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))


def _porta(nome, file):
    s = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ⛔ SI IMPORTANO, NON SI RICOPIANO.
#
#    In `01-b3-cliente.py` c'e' la riga che impedisce di dare gli eventi del
#    canale di controllo allo strato HTTP/3 di `aioquic`: senza, la connessione
#    muore per mano del CLIENT con `0x105 — DATA frame is not allowed in this
#    state` (`[M]` 10 agosto 2026).  Una copia divergente riporterebbe quel
#    difetto qui dentro travestito da difetto del server.
#    ⚠ E il giudizio del fotogramma sta in un file solo, o due copie della
#      stessa lettura darebbero sempre ragione a se' stesse.
#
# ⛔ E `01-b3-cliente.py` SI IMPORTA TARDI, non qui in cima.
#
#    Quel file importa `aioquic`, che sta **solo dentro il contenitore**.
#    Importandolo in cima, `--elenco` — che non tocca la rete e serve a leggere
#    le previsioni **prima** del giro — moriva con `ModuleNotFoundError` su
#    CHUWI.  ⚠ E le previsioni sono precisamente la cosa che va letta da chi
#    non ha il contenitore: chi revisiona il banco prima che il prodotto esista.
#    ⭐ `02-filo-fotogramma.py` invece non ha dipendenze, ed e' voluto: il
#    giudizio del fotogramma deve poter girare dovunque.
f24 = _porta("f24", "02-filo-fotogramma.py")
b3 = None


def carica_b3():
    global b3
    if b3 is None:
        b3 = _porta("b3", "01-b3-cliente.py")
    return b3

CLIENT, SERVER = 1, 2

# ⛔ IL FORMATO DELLA REGISTRAZIONE E' `RCPREG 0x00 0x03` — §11.1.
#
#    `0x02`, 12 agosto 2026, proposta P7 (che questo banco stesso aveva
#    trovato): il blocco porta `fine`, e passa da 16 a 17 byte.
#    ⚠ Senza quel campo, quel che questo cliente registra e quel che ha visto
#      sul filo non sono la stessa cosa: **lui** sa se lo stream e' finito con
#      FIN o e' stato azzerato — glielo dice QUIC — e la registrazione non
#      sapeva scriverlo.  L'arbitro che la legge doveva indovinare.
#
# ⭐⭐ `0x03`, **21 agosto 2026**: il blocco porta `istante_ms` e passa a 21
#    byte, l'intestazione dichiara `orologio` (1 = i tempi sono del client).
#    Senza il tempo, §7.1 — il secondo di grazia — non era collaudabile da
#    nessun `.rcpreg`, e T4 («un server che dice `TELA(ADATTATA)` e non tocca
#    il palco») non era scrivibile affatto.
#
# ⛔⛔ E QUESTO FILE ERA IL SECONDO DELL'ISOLA `0x02`: `02-filo-validatore.py`
#    lo leggeva, `04-b20-desktop-vero.py` pure, e i tre andavano d'accordo fra
#    loro mentre `01-b3`/`01-b4` erano passati a `0x03`.  ⚠ Due formati vivi
#    sotto una specifica sola sono la condizione esatta del difetto del 12
#    agosto, solo piu' grande — e nessuno dei tre file era rotto da solo.
MAGIA = b"RCPREG\x00\x03"
BLOCCO = "!BBBIQIH"
CONTINUA, FIN, RESET = 0, 1, 2
OROLOGIO_CLIENT = 1        # §11.1: questo programma e' il client

# ⛔ L'istante e' MONOTONO e RELATIVO al primo blocco, mai un'ora del mondo:
#    §4.4 vieta i segreti nel file, e una data assoluta dice **quando** e —
#    con l'indirizzo che la traccia gia' porta — **da dove** un utente si e'
#    collegato.  ⚠ `time.monotonic()` e non `time.time()`: un aggiustamento di
#    NTP nel mezzo farebbe tornare indietro gli istanti, e l'arbitro
#    leggerebbe un fotogramma arrivato «prima» del `TELA` che lo precede.
_t0 = None


def istante():
    global _t0
    adesso = time.monotonic()
    if _t0 is None:
        _t0 = adesso
    return min(int((adesso - _t0) * 1000.0), 0xFFFFFFFF)

T_RICHIEDI_CHIAVE = 0x000D
T_CONGEDO = 0x000C
ERRORE_PROTOCOLLO = 0x0B      # §8.2
CHIUSO_DALL_UTENTE = 0x01

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


# ===========================================================================
class Flusso:
    """Uno stream unidirezionale del server: uno stream, un fotogramma (§6.2)."""

    def __init__(self, sid, ctx):
        self.sid = sid
        self.giudice = f24.Giudice(ctx, dove="uni")
        self.byte = 0
        self.aperto = time.monotonic()
        self.chiuso = None
        self.verdetto = None


def fabbrica_cliente():
    """Il cliente della fase 1, che impara a ricevere gli stream del video.

    ⛔ **Eredita, non riscrive**: la stretta di mano e' gia' il secondo lettore
       di `RCP.md`, e riscriverla qui darebbe due secondi lettori che possono
       divergere — cioe' due arbitri.

    ⚠ E' una fabbrica e non una classe al livello del file perche' la classe
      base sta dentro `01-b3-cliente.py`, che importa `aioquic`: vedi il
      riquadro in cima.
    """
    class Cliente(carica_b3().Cliente):

        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.contesto = None       # lo si pone dopo `SESSIONE`
            # ⛔ Gli stream che abbiamo riconosciuto come VIDEO: si tiene
            #    l'insieme e non si ricalcola, perche' il preambolo di
            #    WebTransport arriva una volta sola, nel primo evento.
            self.video_visti = set()
            self.flussi = {}
            self.finiti = []
            self.chiavi_chieste = 0
            # (verso, canale, stream, carico, oscurati, fine) — §11.1
            self.reg_video = []
            self.primo_byte = None     # ⛔ quando e' arrivato il PRIMO byte video
            # ⚠ Il codec negoziato in §4.3.  Lo pone il guidatore PRIMA della
            #   stretta di mano, perche' `_sfoglia` puo' averne bisogno gia'
            #   nel primo pacchetto che porta `SESSIONE`.
            self.codec_atteso = 1

        # ⛔⛔ IL CONTESTO SI PONE **QUI**, E NON NELLA COROUTINE CHE ASPETTA —
        #     difetto del banco trovato dal PRIMO giro contro un server che
        #     spedisce davvero, `[M]` 12 agosto 2026, montaggio della fase 2.
        #
        #     Il server spedisce `SESSIONE` sul canale di controllo e SUBITO
        #     DOPO apre lo stream del primo fotogramma (§5.2: «il primo dopo
        #     `SESSIONE` DEVE essere una chiave»).  Sul filo l'ordine e'
        #     giusto, e i due arrivano nello stesso volo di pacchetti.
        #
        # ⛔ Ma `cli.contesto` lo poneva il guidatore **dopo**
        #    `await attendi(cli, "SESSIONE")`, cioe' quando `asyncio` riprende
        #    la coroutine — che e' **dopo** che tutti gli eventi di quel volo
        #    sono stati smistati.  ⇒ `_arrivano()` trovava `contesto is None`,
        #    concludeva *«un fotogramma prima di SESSIONE»* e stampava
        #    `ERRORE_PROTOCOLLO` — ⛔ **un rosso puntato sul server, che aveva
        #    fatto esattamente quel che §2.5 gli impone**.
        #
        # ⭐ Chi ha detto di chi era la colpa: `02-filo-validatore.py`, il
        #    secondo lettore, sulla STESSA registrazione — *«ACCETTATO, flusso
        #    15: chiave n. 1, 1920x1080, 11923 byte, conforme»*, uscita 0.  ⚠ E
        #    che i due arbitri dello stesso banco dicessero cose opposte sugli
        #    stessi byte e' una MISURA, non un incidente (`P2-4-filo.md` §4).
        #
        # ⛔ E la cura non e' «aspettare un po'»: e' guardare il buffer del
        #    canale di controllo **prima** che `_sfoglia` lo consumi, cioe'
        #    nello stesso istante sincrono in cui i byte sono arrivati.  Cosi'
        #    «prima di `SESSIONE`» torna a essere una domanda sui BYTE, e non
        #    sull'ordine in cui `asyncio` sveglia le coroutine.
        def _sfoglia(self):
            if self.contesto is None:
                dati = bytes(self.arrivati)
                i = 0
                while len(dati) - i >= 6:
                    tipo, lung = struct.unpack("!HI", dati[i:i + 6])
                    if len(dati) - i < 6 + lung:
                        break
                    # corpo: 1 byte di stato, poi larghezza e altezza (§4.5)
                    if tipo == carica_b3().T["SESSIONE"] and lung >= 9:
                        lar, alt = struct.unpack("!II", dati[i + 7:i + 15])
                        self.contesto = f24.Contesto(
                            tela=(lar, alt),
                            codec_negoziato=self.codec_atteso,
                            sessione_aperta=True)
                        break
                    i += 6 + lung
            super()._sfoglia()

        def quic_event_received(self, event):
            nome = type(event).__name__
            # ⛔ Gli stream unidirezionali del server si intercettano PRIMA di
            #    passare l'evento alla catena della fase 1: quella non li
            #    conosce e li darebbe allo strato HTTP/3 di `aioquic`, che li
            #    leggerebbe come frame di HTTP/3 e chiuderebbe la connessione —
            #    **per mano nostra**.  ⚠ E' la stessa asimmetria pagata il 10
            #    agosto 2026 sul canale di controllo (`01-b3-cliente.py`).
            if nome == "StreamDataReceived" and self._smista(event):
                return
            if nome == "StreamReset" and event.stream_id in self.video_visti:
                # ⛔ `RESET_STREAM`: il fotogramma e' INCOMPLETO (§6.2).
                self._azzerato(event.stream_id)
                return
            super().quic_event_received(event)

        # ⛔⛔ IL PREAMBOLO DI WEBTRANSPORT, E IL PRIMO GIRO L'HA PAGATO
        #
        # ⚠ `[M]` 12 agosto 2026, PRIMO GIRO DAL VIVO di questo cliente contro
        #   la 7514.  La riga di prima diceva: *«uno stream unidirezionale
        #   aperto dal server si riconosce dai due bit bassi
        #   dell'identificatore QUIC»* — e si prendeva **anche i tre stream
        #   unidirezionali di HTTP/3** (il control stream e i due di QPACK, che
        #   `aioquic` apre da se' e che hanno gli stessi due bit).  ⇒ Lo strato
        #   HTTP/3 restava senza i suoi byte, la CONNECT estesa non arrivava
        #   mai a `:status 200`, il canale di controllo non si apriva, e il
        #   server chiudeva con `TEMPO_SCADUTO` dopo 5 s (§4.6).
        #   ⛔ Il sintomo era **un rosso puntato sul server**, che aveva fatto
        #      esattamente il suo mestiere: il controllo positivo —
        #      `01-b3-cliente.py` contro lo **stesso** server, nello stesso
        #      minuto — arrivava a `SESSIONE` in 1003 ms.
        #
        # ⭐ E la cura porta con se' una scoperta su `RCP.md`, che sta nel
        #    rapporto come **P18**: §2.5 dice *«si leggono i primi due byte
        #    dello stream, che sono in ogni caso un campo `tipo`»*, ⛔ e su
        #    WebTransport **non e' vero**: uno stream unidirezionale del server
        #    comincia con il tipo `0x54` in varint (due byte, `40 54`) e con il
        #    numero della sessione, e i 28 byte di §6.2 cominciano dopo.
        WT_UNI = 0x54  # draft-ietf-webtrans-http3: il tipo dello stream uni

        @staticmethod
        def _varint(b, i):
            """Il varint di QUIC (RFC 9000 §16).  `None` = non e' tutto qui."""
            if i >= len(b):
                return None, i
            n = 1 << (b[i] >> 6)
            if i + n > len(b):
                return None, i
            v = b[i] & 0x3F
            for k in range(1, n):
                v = (v << 8) | b[i + k]
            return v, i + n

        def _smista(self, event):
            """Questo stream e' un fotogramma?  ⛔ E se non lo e', **non se ne
            consuma un byte**: quei byte sono di HTTP/3, e prenderglieli e'
            il difetto che il primo giro ha pagato."""
            sid = event.stream_id
            if sid in self.video_visti:
                self._arrivano(sid, event.data, event.end_stream)
                return True
            # 0b11 = unidirezionale, aperto dal server
            if (sid & 0x03) != 0x03 or sid == self.sessione:
                return False
            d = event.data
            # ⛔ Si decide sul PRIMO evento e sui primi due byte, e se non
            #    bastano si lascia perdere invece di trattenerli: «non ho
            #    capito» e «e' mio» sono due cose diverse.
            if len(d) < 2 or d[0] != 0x40 or d[1] != self.WT_UNI:
                return False
            tipo, i = self._varint(d, 0)
            sessione, i = self._varint(d, i)
            if tipo != self.WT_UNI or sessione is None:
                return False
            self.video_visti.add(sid)
            self._arrivano(sid, bytes(d[i:]), event.end_stream)
            return True

        def _arrivano(self, sid, dati, fine):
            if self.contesto is None:
                # ⛔ Un fotogramma prima di `SESSIONE`: il contesto non c'e'
                #    ancora, e il giudice DEVE poterlo dire — invariante I3.
                self.contesto = f24.Contesto(sessione_aperta=False)
            f = self.flussi.get(sid)
            if f is None:
                f = self.flussi[sid] = Flusso(sid, self.contesto)
                if self.primo_byte is None:
                    self.primo_byte = time.monotonic()
            f.byte += len(dati)
            self.reg_video.append([SERVER, 0x03, sid, bytes(dati), [],
                                   FIN if fine else CONTINUA, istante()])
            f.giudice.arrivano(dati)
            if fine:
                f.chiuso = "fin"
                self._chiudi(f)

        def _azzerato(self, sid):
            # ⛔ E LO SI SCRIVE NELLA REGISTRAZIONE — §11.1, campo `fine`.
            #
            #    Il `RESET_STREAM` non porta byte, quindi non ha un blocco suo:
            #    marca l'ULTIMO blocco di quello stream.  ⚠ E se non ce n'e'
            #    nessuno — uno stream azzerato prima di aver consegnato un byte
            #    — se ne scrive uno **vuoto**: «zero byte, azzerato» e «non e'
            #    mai esistito» sono due fatti diversi, ed e' la forma E8.
            ultimo = None
            for b in self.reg_video:
                if b[2] == sid:
                    ultimo = b
            if ultimo is None:
                self.reg_video.append([SERVER, 0x03, sid, b"", [], RESET,
                                       istante()])
            else:
                ultimo[5] = RESET
            f = self.flussi.get(sid)
            if f is None:
                f = self.flussi[sid] = Flusso(
                    sid, self.contesto or f24.Contesto())
            f.chiuso = "reset"
            self._chiudi(f)

        def _chiudi(self, f):
            if f.verdetto is not None:
                return
            f.verdetto = (f.giudice.verdetto
                          if f.giudice.verdetto is not None
                          else f.giudice.finisce(f.chiuso))
            self.finiti.append(f)
            del self.flussi[f.sid]

        # -- gli obblighi che §5.2 mette sul CLIENT ----------------------
        def chiedi_chiave(self, ultimo):
            """§5.2: il client DEVE chiedere una chiave su un buco o un
            abbandono.

            ⛔ E `ultimo_numero` e' «l'ultimo fotogramma decodificato, 0 se
               nessuno» (§7.1) — che e' l'ambiguita' **A2**: se il contatore di
               §6.2 potesse partire da 0, questo campo direbbe due cose.  Qui
               si manda quel che il documento dice, e l'ambiguita' si segnala
               invece di essere risolta a mano dal banco.
            """
            self.manda(struct.pack("!HII", T_RICHIEDI_CHIAVE, 4,
                                   ultimo if ultimo is not None else 0))
            self.chiavi_chieste += 1

    return Cliente


# ===========================================================================
async def guarda(cli, a, ctx):
    """Resta ad ascoltare, e fa quel che §5.2 impone al client.

    ⛔ **Con gli occhi aperti, non dormendo** — rilievi R8.2/R8.4 della fase 1.
       Un `asyncio.sleep` non si accorge di niente: la connessione puo' cadere
       per il tetto d'inattivita' di QUIC, o la sessione puo' essere chiusa dal
       server, e questo programma uscirebbe 0 dicendo «ho guardato».
    """
    scadenza = asyncio.get_event_loop().time() + a.attesa
    visti = 0
    while asyncio.get_event_loop().time() < scadenza:
        if cli.caduta is not None:
            return visti, f"caduto: {cli.caduta}"
        while len(cli.finiti) > visti:
            f = cli.finiti[visti]
            visti += 1
            v = f.verdetto
            col = {f24.ACCETTATO: VERDE, f24.SCARTATO: GIALLO,
                   f24.AMBIGUO: GIALLO, f24.ERRORE_PROTOCOLLO: ROSSO}[v.esito]
            print(f"   {col}{v.esito:18s}{GRIGIO} stream {f.sid}, {f.byte} "
                  f"byte, finito con {f.chiuso}: {v.dice}")
            if v.esito == f24.ERRORE_PROTOCOLLO:
                # ⛔ §3.1, e i punti sono TRE e in quest'ordine: nel registro,
                #    il `CONGEDO` sul canale se il canale e' utilizzabile, e il
                #    motivo nel codice d'errore della chiusura della sessione.
                print(f"      ⛔ {v.regola} — byte {v.scostamento} "
                      f"dell'intestazione")
                cli.manda(struct.pack("!HIB", T_CONGEDO, 3, ERRORE_PROTOCOLLO)
                          + struct.pack("!H", 0))
                return visti, f"NON CONFORME: {v.dice}"
            # ⛔ E gli obblighi di §5.2, che sono del CLIENT e che nessun banco
            #    del server puo' esercitare al posto suo.
            if ctx.chiedi_chiave:
                cli.chiedi_chiave(ctx.ultimo_consegnato)
                print(f"      ⇒ `RICHIEDI_CHIAVE(ultimo_numero="
                      f"{ctx.ultimo_consegnato or 0})` — §5.2")
                ctx.chiedi_chiave = False
        await asyncio.sleep(0.02)
    return visti, None


def scrivi_registrazione(percorso, blocchi):
    """Il formato di §11.1, con i blocchi del video accanto a quelli di controllo.

    ⛔ `fine` predefinito a CONTINUA: il canale di controllo vive su **un solo
       stream per tutta la sessione** (§2.5), e dentro la registrazione quello
       stream non si chiude.  ⚠ Scrivere `FIN` a ogni messaggio direbbe che la
       sessione si chiude e riapre a ogni riga.
    """
    # ⛔⛔ E I BLOCCHI SI RIMETTONO IN ORDINE DI TEMPO, e non e' cosmetica.
    #
    #    Chi chiama passa `blocchi + cli.reg_video`: i blocchi di CONTROLLO
    #    tutti prima, quelli VIDEO tutti dopo.  ⚠ Ma un `RICHIEDI_CHIAVE`
    #    spedito a meta' sessione finiva **davanti** al primo fotogramma, che
    #    sul filo era passato molto prima.  ⛔ Con `0x02` non si vedeva: senza
    #    il tempo, un ordine sbagliato e uno giusto hanno la stessa faccia.
    #    Con `0x03` l'arbitro pretende un orologio monotono e lo direbbe —
    #    «registrazione rotta» — su una traccia di un filo sanissimo.
    #
    # ⭐ `sorted` e' STABILE: due blocchi con lo stesso millisecondo restano
    #    nell'ordine in cui sono stati registrati, che e' quel che si sa di
    #    loro.  Inventare un ordine fra pari sarebbe peggio di non averlo.
    def _quando(b):
        return b[6] if len(b) > 6 else 0

    blocchi = sorted(blocchi, key=_quando)
    out = bytearray(MAGIA + struct.pack("!IBBBB", len(blocchi),
                                        OROLOGIO_CLIENT, 0, 0, 0))
    for verso, canale, stream, carico, *resto in blocchi:
        oscurati = resto[0] if resto else []
        fine = resto[1] if len(resto) > 1 else CONTINUA
        ist = resto[2] if len(resto) > 2 else 0
        out += struct.pack(BLOCCO, verso, canale, fine, ist, stream,
                           len(carico), len(oscurati))
        for ini, qua, imp in oscurati:
            out += struct.pack("!II", ini, qua) + imp
        out += carico
    with open(percorso, "wb") as f:
        f.write(bytes(out))
    return len(blocchi)


async def principale(a):
    from aioquic.h3.connection import H3_ALPN
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.asyncio import connect
    b3 = carica_b3()
    Cliente = fabbrica_cliente()

    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{a.indirizzo}:{a.porta}"
    blocchi = []

    print(f"== F2.4 — il cliente di prova RICEVE il fotogramma")
    print(f"   ⛔ BERSAGLIO: https://{autorita}{a.percorso}")
    print(f"   ⛔ SCENA: sessione appena aperta, nessun input, nessun "
          f"movimento —")
    print(f"      la fase 2 consegna **un'immagine ferma** (`PIANO.md` "
          f"«Fase 2»).")
    print(f"      ⚠ E va dichiarato: `CODER.md` §3.2 vuole una scena sempre in")
    print(f"        movimento, e qui la scena ferma **e' il soggetto**, non "
          f"una")
    print(f"        distrazione.  Dalla fase 3 in poi quella regola torna a "
          f"valere.")
    print(f"   attesa: {a.attesa} s\n")

    async with connect(a.indirizzo, a.porta, configuration=conf,
                       create_protocol=Cliente) as cli:
        await asyncio.wait_for(cli.wait_connected(), timeout=8)
        cli.apri_sessione(autorita, a.percorso)
        stato = await asyncio.wait_for(cli.accettata, timeout=8)
        print(f"   CONNECT estesa: :status = {stato}")
        if stato != "200":
            return 2
        cli.apri_controllo()
        # ⛔ PRIMA della stretta di mano: `_sfoglia` puo' aver bisogno del
        #    codec gia' nel pacchetto che porta `SESSIONE`, e un valore posto
        #    dopo sarebbe posto troppo tardi — e' lo stesso difetto di ordine
        #    che il riquadro di `_sfoglia` descrive.
        cli.codec_atteso = a.codec
        try:
            b = b3.inquadra(b3.T["CIAO"], b3.corpo_ciao())
            cli.manda(b)
            blocchi.append((CLIENT, 0x00, 0, b, [], CONTINUA, istante()))
            _, corpo, grezzo = await b3.attendi(cli, "ECCOMI")
            blocchi.append((SERVER, 0x00, 0, grezzo, [], CONTINUA, istante()))

            corpo_c = b3.s(a.utente) + b3.s(a.parola)
            b = b3.inquadra(b3.T["CREDENZIALI"], corpo_c)
            ini = 6 + 2 + len(a.utente.encode()) + 2
            qua = len(a.parola.encode())
            cli.manda(b)
            blocchi.append((CLIENT, 0x00, 0,
                            b[:ini] + bytes([0x2A]) * qua + b[ini + qua:],
                            [(ini, qua, hashlib.sha256(a.parola.encode()).digest())],
                            CONTINUA, istante()))
            _, corpo, grezzo = await b3.attendi(cli, "AMMESSO", attesa=20)
            blocchi.append((SERVER, 0x00, 0, grezzo, [], CONTINUA, istante()))

            b = b3.inquadra(b3.T["ATTACCA"],
                            struct.pack("!IIII", a.larghezza, a.altezza,
                                        a.larghezza, a.altezza)
                            + b3.s(a.disposizione))
            cli.manda(b)
            blocchi.append((CLIENT, 0x00, 0, b, [], CONTINUA, istante()))
            _, corpo, grezzo = await b3.attendi(cli, "SESSIONE")
            blocchi.append((SERVER, 0x00, 0, grezzo, [], CONTINUA, istante()))
        except Exception as e:      # noqa: BLE001 — il tipo dell'errore E' la misura
            print(f"   ⛔ la stretta di mano non e' arrivata a SESSIONE: "
                  f"{type(e).__name__}: {e}")
            print(f"      ⚠ Questo NON e' un rosso del video: non si e' provato "
                  f"niente")
            return 2

        lar, alt = struct.unpack("!II", corpo[1:9])
        print(f"   ⭐ SESSIONE: tela concessa {lar}x{alt}")
        # ⛔ IL CONTESTO SI PRENDE DA `SESSIONE`, NON DAI PREDEFINITI.
        #
        #    §6.2 lega `largh.`/`altezza` alla **tela concessa** — che puo'
        #    essere diversa da quella chiesta (§4.5, il ripiego su KDE) — e
        #    `codec` a quel che §4.3 ha negoziato.  Un giudice che usasse i
        #    propri predefiniti giudicherebbe se stesso.
        # ⚠ `_sfoglia` puo' averlo gia' posto, sugli stessi byte e con gli
        #   stessi valori: allora non si rifa'.  ⛔ Rifarlo qui cancellerebbe
        #   un contesto gia' usato dai flussi arrivati nello stesso volo — e i
        #   loro `Flusso` terrebbero il vecchio oggetto, cioe' due verita'
        #   sulla stessa sessione.
        if cli.contesto is None:
            cli.contesto = f24.Contesto(tela=(lar, alt),
                                        codec_negoziato=a.codec,
                                        sessione_aperta=True)
        ctx = cli.contesto

        visti, perche = await guarda(cli, a, ctx)

    if a.registra:
        n = scrivi_registrazione(a.registra, blocchi + cli.reg_video)
        print(f"\n   registrazione: {a.registra} ({n} blocchi) — "
              f"⛔ e va data a `02-filo-validatore.py`, che e' l'altro lettore")

    esiti = [f.verdetto.esito for f in cli.finiti]
    conformi = sum(1 for e in esiti if e == f24.ACCETTATO)
    ambigui = sum(1 for e in esiti if e == f24.AMBIGUO)
    print(f"\n   guardati: {len(cli.finiti)} flussi video · {conformi} "
          f"conformi · {ambigui} ambigui · {cli.chiavi_chieste} "
          f"`RICHIEDI_CHIAVE` spedite")

    if a.uscita:
        with open(a.uscita, "a") as f:
            f.write(json.dumps({
                "quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "banco": "F2.4-cliente", "porta": a.porta,
                "scena": "sessione appena aperta, nessun input, immagine ferma",
                "flussi": len(cli.finiti), "conformi": conformi,
                "ambigui": ambigui, "chiavi_chieste": cli.chiavi_chieste,
                "esiti": esiti, "caduta": cli.caduta}, ensure_ascii=False) + "\n")

    # ⛔ E LO ZERO HA UN CODICE SUO — vedi il punto 1 dell'intestazione.
    if not cli.finiti:
        print(f"\n   {ROSSO}⛔ ZERO fotogrammi in {a.attesa} s.{GRIGIO}")
        print(f"      Questo NON e' «conforme»: e' l'assenza dell'oggetto del "
              f"giudizio.")
        print(f"      Si guarda chi doveva spedirli — non `RCP.md`.")
        return 5
    if f24.ERRORE_PROTOCOLLO in esiti:
        print(f"\n   {ROSSO}⛔ un fotogramma NON e' conforme{GRIGIO}")
        return 1
    if perche:
        print(f"\n   {ROSSO}⛔ {perche}{GRIGIO}")
        return 4
    if ambigui:
        print(f"\n   {GIALLO}⭐⛔ `RCP.md` ammette due letture su quel che e' "
              f"arrivato{GRIGIO}")
        print(f"      Non e' un verde e non e' un rosso: e' un difetto del "
              f"DOCUMENTO.")
        print(f"      Le proposte: `python3 02-filo-fotogramma.py --elenco`")
        return 3
    print(f"\n   {VERDE}⭐ {conformi} fotogrammi, tutti conformi a `RCP.md`"
          f"{GRIGIO}")
    print(f"   ⚠ e NON e' «l'utente vede il suo desktop»: qui si giudicano i "
          f"BYTE.")
    print(f"     I pixel li confronta F2.6, e il metro e' l'utente (I8).")
    return 0


# ===========================================================================
# ⛔ LE VIOLAZIONI VERSO IL SERVER, e sono quelle che la fase 2 aggiunge.
#
#    `01-b5-violazioni.py` ne prova quarantaquattro sulla stretta di mano, e
#    dichiara in testa quali NON prova perche' il messaggio non esiste ancora:
#    fra queste, *«due `RICHIEDI_CHIAVE` a meno di 200 ms»*, rinviata alla
#    fase 3.  ⭐ Qui si aggiungono quelle che nascono col primo fotogramma.
#
# ⚠ E una che c'e' gia' in B5 si RIFA', e non e' un doppione: `uni-video`
#   spediva `0x0301` a un server che il canale video **non lo conosceva
#   affatto** — cadeva nel ramo `default`.  Contro un server che lo conosce,
#   lo stesso ingresso esercita un percorso di codice **diverso**, e un caso
#   che passa contro il primo non dice niente del secondo.
VIOLAZIONI = [
    ("video-dal-client", ERRORE_PROTOCOLLO,
     "un fotogramma chiave BEN FORMATO su uno stream unidirezionale del "
     "client: §2.5, «un `0x03` che arriva dal client».  ⛔ Il carico e' legale "
     "in se': l'unica cosa storta e' il verso"),
    ("richiedi-chiave-prima-di-sessione", ERRORE_PROTOCOLLO,
     "`RICHIEDI_CHIAVE` fra `AMMESSO` e `SESSIONE`: non esiste nessun "
     "fotogramma di cui chiedere la chiave (§1, §3)"),
    ("richiedi-chiave-corta", ERRORE_PROTOCOLLO,
     "`RICHIEDI_CHIAVE` con tre byte di corpo invece di quattro: §6.1, «una "
     "lunghezza incoerente con quel che il tipo prevede»"),
    ("richiedi-chiave-zero", None,
     "⭐ `RICHIEDI_CHIAVE(ultimo_numero = 0)`: §7.1 lo dichiara legale — «0 se "
     "nessuno» — ed e' quel che manda un client appena attaccato.  ⛔ La "
     "sessione DEVE restare viva"),
    ("richiedi-chiave-due-volte", None,
     "⏳ due `RICHIEDI_CHIAVE` a meno di 200 ms: il server **PUO'** ignorare la "
     "seconda (§3 eccezione 5, §5.2) — e in tutt'e due i casi la sessione "
     "DEVE restare viva.  ⚠ La misura vera e' della **fase 3**, dove le "
     "chiavi si contano: qui si prova solo che la sessione regge"),
]


def elenco():
    print("== F2.4 — il cliente di prova: che cosa prova, e contro che cosa")
    print("   ⏳ NON ANCORA GIRATO: il prodotto della fase 2 non esiste\n")
    print("== ⛔ dal lato che RICEVE — i casi stanno in 02-filo-fotogramma.py")
    print("   `python3 02-filo-fotogramma.py --elenco`\n")
    print("== ⛔ verso il SERVER — le violazioni che la fase 2 aggiunge")
    print("   ⛔ Ogni riga e' una PREVISIONE, scritta prima del giro\n")
    for nome, atteso, spiega in VIOLAZIONI:
        att = (f"{atteso:#04x} ERRORE_PROTOCOLLO" if atteso
               else "⭐ DEVE PASSARE, e la sessione DEVE restare viva")
        print(f"  {nome:36s} {att}")
        print(f"  {'':36s}   {spiega}")
    print(f"\n  {len(VIOLAZIONI)} casi: "
          f"{sum(1 for v in VIOLAZIONI if v[1])} violazioni e "
          f"{sum(1 for v in VIOLAZIONI if not v[1])} ⭐ verdi attesi")
    return 0


# ---------------------------------------------------------------------------
# ⛔ LA PAROLA D'ORDINE NON DEVE PASSARE DALLA RIGA DI COMANDO — difetto **D12**,
#    curato il 12 agosto 2026.
#
# ⛔ `--parola` finisce nell'`argv` del processo, cioe' in `/proc/<pid>/cmdline`,
#    che su Linux e' **leggibile da chiunque**: un `ps` lanciato da un altro
#    utente durante il giro la stampa per intero.
#
# ⭐ La strada buona esisteva gia' in casa e questa e' la sua estensione, non un
#    secondo modo: `01-b10-secondo-utente.py` prende `--parola-file`, un file
#    `0600` che il lanciatore scrive con `printf` — un **builtin** della shell,
#    quindi nemmeno la scrittura passa per un processo con la parola in `argv` —
#    e cancella con una `trap`.
#
# ⚠ E `--parola` NON e' stata tolta, e non per pigrizia: dei chiamanti non
#   ancora curati la passano ancora, e romperli **in silenzio** sarebbe peggio
#   del difetto.  ⛔ Ma il ripiego si DICHIARA (`CODER.md` §4.2): un ripiego
#   silenzioso produce due comportamenti sotto la stessa etichetta, che e' la
#   forma **E2** — e qui i due comportamenti sono «il segreto e' protetto» e
#   «il segreto e' pubblico».  ⇒ chi passa `--parola` se lo sente dire.
#
# ⚠ E l'avviso guarda `sys.argv`, non il valore: il predefinito scritto nel
#   codice non sta in nessuna riga di comando, e dirgli il contrario sarebbe un
#   allarme che si impara a ignorare.
def parola_dagli_argomenti(a):
    """La parola d'ordine: da `--parola-file` se c'e', da `--parola` altrimenti.

    ⛔ E i tre modi di fallire si distinguono: «non si legge», «e' leggibile da
    altri» e «e' vuoto» hanno tre cure diverse, e un file vuoto NON e' una
    parola vuota — e' «il lanciatore non l'ha scritta» (`LEZIONI.md` §1.9).
    """
    percorso = getattr(a, "parola_file", "") or ""
    if percorso:
        try:
            modo = os.stat(percorso).st_mode & 0o077
        except OSError as e:
            print(f"   ⛔ il file della parola «{percorso}» non si legge: {e}")
            sys.exit(2)
        if modo:
            print(f"   ⚠ «{percorso}» e' leggibile da altri (bit {modo:o}): il "
                  f"segreto non e' protetto")
        try:
            with open(percorso, encoding="utf-8") as f:
                parola = f.read().strip("\n")
        except OSError as e:
            print(f"   ⛔ la parola non si legge da «{percorso}»: {e}")
            sys.exit(2)
        if not parola:
            print(f"   ⛔ il file della parola «{percorso}» e' VUOTO.  Non e'")
            print("      «la parola e' vuota»: e' «il lanciatore non l'ha scritta».")
            sys.exit(2)
        return parola
    if any(x == "--parola" or x.startswith("--parola=") for x in sys.argv[1:]):
        print("   ⚠ D12: la parola d'ordine e' arrivata da `--parola`, cioe' dalla")
        print("     RIGA DI COMANDO: sta in `/proc/<pid>/cmdline` e la vede chiunque")
        print("     faccia `ps` su questa macchina.  Il giro prosegue — il chiamante")
        print("     non e' stato curato — ma non e' un giro riservato.")
        print("     ⭐ La cura: `--parola-file <file 0600>`, come in B10.")
    return a.parola


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="F2.4 — il cliente di prova che riceve il fotogramma")
    p.add_argument("--indirizzo", default="192.168.0.2")
    # ⛔ La porta NON ha un predefinito che nomini un bersaglio: 7448 e' il
    #    prodotto di casa e 7501 il bersaglio di P5, tutt'e due accese apposta.
    #    La porta di F2.4 e' la **7514**, e si passa a mano.
    p.add_argument("--porta", type=int, help="⛔ la 7514, per F2.4")
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola", default="parola-di-prova")
    # ⛔ D12: la strada che NON passa da `ps`.  Vince su `--parola` se ci sono
    #    tutt'e due — un file scritto apposta e' sempre piu' recente di un
    #    predefinito.
    p.add_argument("--parola-file", default="",
                   help="file 0600 con la sola parola d'ordine (⭐ D12: cosi' "
                        "non finisce in `ps`)")
    p.add_argument("--larghezza", type=int, default=1920)
    p.add_argument("--altezza", type=int, default=1080)
    p.add_argument("--disposizione", default="it")
    p.add_argument("--codec", type=int, default=1, help="1 = HEVC, 2 = AV1")
    p.add_argument("--attesa", type=float, default=15.0,
                   help="quanti secondi si resta ad ascoltare")
    p.add_argument("--registra", help="la traccia, nel formato di §11.1")
    p.add_argument("--uscita", default="", help="il registro del giro, in JSONL")
    p.add_argument("--elenco", action="store_true",
                   help="le previsioni, senza rete")
    p.add_argument("--violazioni", action="store_true",
                   help="⏳ le prove verso il server (vuole un server)")
    a = p.parse_args()
    a.parola = parola_dagli_argomenti(a)
    if a.elenco:
        sys.exit(elenco())
    if not a.porta:
        print("⛔ serve --porta.  Per F2.4 e' la 7514: la 7448 e la 7501 sono")
        print("   accese apposta e non si toccano (mandato §4).")
        sys.exit(2)
    try:
        sys.exit(asyncio.run(principale(a)))
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        print(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
