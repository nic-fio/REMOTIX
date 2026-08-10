#!/usr/bin/env python3
"""01-b5-violazioni.py — ⛔ B5: il rigore verso il server, provato violandolo.

    python3 01-b5-violazioni.py --indirizzo 192.168.0.2 --porta 7447
    python3 01-b5-violazioni.py --solo tela-1921          (un caso solo)
    python3 01-b5-violazioni.py --elenco                  (le previsioni, senza misurare)

⚠ Gira DENTRO il contenitore: aioquic sta li'.

===========================================================================
⛔ PERCHE' QUESTO BANCO ESISTE

`RCP.md` §3 e' la **regola di rigore**: quel che non si capisce non si ignora,
la connessione cade, col motivo.  ⭐ Ma una regola di rigore **non si prova
facendo le cose giuste**: un server che non controlla niente passa tutti i
banchi di B3 e cade solo il giorno in cui qualcuno gli manda un byte storto —
e quel giorno non c'e' un banco a guardare.

⛔ *Un banco che non prova a violare il protocollo non prova il protocollo.*

===========================================================================
⛔ LE CINQUE COSE CHE OGNI CASO VERIFICA, E LE ULTIME DUE SI DIMENTICANO

  1. ⛔ **che la violazione sia DAVVERO partita.**  Un caso la cui
     *preparazione* fallisce — l'`ATTACCA` fisso rifiutato, l'`ECCOMI` che non
     arriva — non ha provato niente, e finche' il motivo si raschiava dal testo
     dell'eccezione diventava **verde** proprio per quello (rilievo R7.1).  Qui
     ogni caso porta `provocato`, e senza quello e' rosso;
  2. **il motivo giusto**, letto DAL LATO CHE RICEVE (§8.1) — non dal registro
     del server, che e' la stessa mano che ha scritto il codice, e ⛔ **non dal
     testo di un'eccezione**: `raccogli` lo prende da un messaggio arrivato sul
     filo, o non lo prende;
  3. ⛔ **in quale MESSAGGIO** e' arrivato.  §11 lo dice per esteso:
     `CREDENZIALI_ERRATE` e `TROPPI_TENTATIVI` viaggiano in `RESPINTO`, tutti
     gli altri in `CONGEDO`, e §4.4 vieta di mandare tutt'e due.  Sono **due
     macchine a stati diverse** — dopo `RESPINTO` il client non puo' riprovare
     — e contarle sotto la stessa etichetta e' la forma E3 (rilievo R7.9);
  4. **le due strade di §3.1**, e ⛔ **non sono facoltative allo stesso modo**:
     il **punto 2** (il `CONGEDO`) e' condizionato — *«se il canale di
     controllo e' ancora utilizzabile»* — il **punto 3** (il codice del motivo
     nella chiusura della sessione WebTransport) e' un **DEVE incondizionato**,
     ed e' quello che §3.1 chiama *«quello che salva le diagnosi»*.
     ⚠ Il rilievo R3.3 diceva che pretenderle sempre tutt'e due darebbe rosso
     sul codice giusto: vale per il punto 2, **non** per il punto 3, e averli
     scambiati aveva reso facoltativo proprio l'ultimo appiglio (rilievo R7.3).
     Qui il punto 3 si **conta**, con il suo denominatore, invece di essere
     stampato;
  5. ⛔ **e che il server sia ancora li' dopo** (B0.5).  Un server ucciso dal
     nucleo *«fa cadere la connessione»* esattamente come uno che congeda —
     e si porta via **tutte le sessioni degli altri utenti**.  Dopo ogni caso
     si apre una connessione nuova e si arriva a `ECCOMI`: e' la meta' del
     banco che nessuno scrive, ed e' quella che distingue il rigore dal
     collasso.

===========================================================================
⭐ E I CASI CHE DEVONO PASSARE

I casi con `atteso = None` sono ⭐ **verdi attesi**, e non sono riempitivo:
sono il controllo che dice *no* a «questo server chiude tutto».

  nome-con-trattino-basso    `video.misura_massima`: il `_` e' LECITO (§4.3)
  capacita-sconosciuta       un NOME che non esiste si ignora (§3, eccezione 1)
  hevc-e-vp9                 una voce sconosciuta DENTRO un elenco si SCARTA
  vista-300x801              la vista non ha i vincoli della tela (§7.1, R4.10)
  vista-1x1                  idem, al limite
  disposizione-con-variante  `de(neo)`: la variante fra parentesi e' lecita
  banco-spento               ⛔ `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)`, non
                             una chiusura e non un silenzio (§7.5 regola 2)
  banco-ritardo-20000        `RITARDO_FUORI_LIMITI`, e la sessione RESTA APERTA

⛔ **E QUANTI SONO NON STA SCRITTO QUI.**  Il numero lo conta `conta()` e lo
stampano `--elenco` e la riga finale, ciascuno con il suo denominatore.  Un
numero scritto a mano in un commento e' il numero che nessuno ricalcola: il
rilievo R7.14 ne ha trovati **tre** — «cinque casi qui dentro», «trentacinque
verdi su trentacinque», «44 violazioni su 44» — e **nessuno dei tre tornava con
il file**.  ⚠ Il terzo, per giunta, contava fra le violazioni anche i casi che
DEVONO passare, su cui «il motivo giusto ogni volta» e' falso per costruzione:
su quelli non deve arrivare nessun motivo.

===========================================================================
⛔ QUEL CHE QUESTO BANCO NON PROVA, E VA DETTO — rilievo R7.8

`RCP.md` §3 dichiara **cinque** eccezioni alla regola di rigore e dice che
«fuori da questo elenco non se ne inventano».  Qui se ne prova **una**: la
prima, con `capacita-sconosciuta` e `hevc-e-vp9`.  Le altre quattro sono
**tolleranze** — posti in cui il server DEVE *non* chiudere — e un server che
chiudesse a ogni sorpresa passerebbe questo banco al completo.

| eccezione di §3 | il caso che manca | perche' non e' qui |
|---|---|---|
| 2 (§6.3) | un datagram di 4 byte, o con `tipo` != `0x0401`, si **scarta** | l'audio non esiste prima della **fase 7** |
| 3 (§7.1) | il **secondo di grazia** sulle coordinate vecchie dopo `TELA(ADATTATA)` | `ADATTA_TELA` e l'input non esistono prima della **fase 6** |
| 4 (§7.1) | `ADATTA_TELA(1921, 1081)` → `TELA(RIFIUTATA, MISURA_FUORI_LIMITI)` **con la sessione ancora aperta** | idem — e il server della fase 1 il tipo `0x000B` non lo conosce affatto: cade nel ramo `default` di `banchi/rcp/rcp.c` come un tipo inventato |
| 5 (§5.2, §7.4) | due `RICHIEDI_CHIAVE` a meno di 200 ms: la seconda **si puo' ignorare** | `RICHIEDI_CHIAVE` non esiste prima della **fase 3** |

⚠ **Scriverli qui oggi darebbe rosso su un messaggio che nessuno ha ancora
scritto**, cioe' su una regola che il server non ha mai avuto occasione di
applicare — il difetto che `01-b5-lancia.sh` dichiara di temere per l'innesto.
Vanno nei banchi delle fasi 3, 6 e 7, e questa tabella e' il posto da cui
riprenderli.
"""
import argparse
import asyncio
import importlib.util
import os
import ssl
import struct
import sys

from aioquic.h3.connection import H3_ALPN
from aioquic.quic.configuration import QuicConfiguration
from aioquic.asyncio import connect

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ Il cliente di B3 si IMPORTA, non si ricopia.  Dentro c'e' la riga che gli
#    impedisce di dare gli eventi del canale di controllo allo strato HTTP/3 di
#    aioquic — senza la quale la connessione muore per mano del CLIENT (10
#    agosto 2026), e una copia divergente riporterebbe quel difetto qui dentro
#    travestito da difetto del server.
_spec = importlib.util.spec_from_file_location(
    "b3cliente", os.path.join(QUI, "01-b3-cliente.py"))
b3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b3)

s, inquadra, MOTIVI = b3.s, b3.inquadra, b3.MOTIVI

ERRORE_PROTOCOLLO = 0x0B
NIENTE_IN_COMUNE = 0x09
VERSIONE_INCOMPATIBILE = 0x0A
SESSIONE_NON_SERVIBILE = 0x0E
TROPPI_TENTATIVI = 0x08
CREDENZIALI_ERRATE = 0x07
CONGEDO, RESPINTO, BANCO_ESITO = 0x000C, 0x0005, 0x0010

# ⛔ IN QUALE MESSAGGIO DEVE ARRIVARE IL MOTIVO — `RCP.md` §11, riga «il
#    congedo»: «`CREDENZIALI_ERRATE` e `TROPPI_TENTATIVI` viaggiano in
#    `RESPINTO`», tutti gli altri in `CONGEDO`, e §4.4 vieta di far seguire
#    `RESPINTO` da un `CONGEDO`.  ⚠ Non e' una formalita': dopo `RESPINTO` il
#    client NON DEVE riprovare sulla stessa connessione (§4.4), dopo un
#    `CONGEDO` la connessione e' finita e basta — due macchine a stati diverse
#    sotto lo stesso numero (rilievo R7.9).
PORTATORE = {CREDENZIALI_ERRATE: "RESPINTO", TROPPI_TENTATIVI: "RESPINTO"}


class Cliente(b3.Cliente):
    """Il cliente di B3, piu' quel che serve a violare (§2.5)."""

    def apri_uni(self):
        # aioquic scrive da se' l'intestazione dello stream unidirezionale
        # WebTransport: il tipo 0x54 e l'identificatore della sessione.
        return self._http.create_webtransport_stream(
            self.sessione, is_unidirectional=True)

    def apri_bidi(self):
        return self._http.create_webtransport_stream(
            self.sessione, is_unidirectional=False)

    def manda_su(self, stream, dati, fine=False):
        self._quic.send_stream_data(stream, dati, end_stream=fine)
        self.transmit()


# ---------------------------------------------------------------------------
# I corpi, scritti a mano perche' vanno storti apposta.
def capacita(voci, versione=1):
    out = struct.pack("!HH", versione, len(voci))
    for n, v in voci:
        out += s(n) + s(v)
    return out


BUONE = [("video.codec", "hevc,av1"), ("video.profondita", "8,10"),
         ("audio.codec", "opus,pcm"), ("client.nome", "banco-b5 0.1.0")]

# ⛔ `BUONE` senza `client.nome`, per i casi che devono violare **una regola
#    sola** su quel nome.  `BUONE + [("client.nome", ...)]` porta `client.nome`
#    DUE VOLTE, e §4.3 da' due ragioni distinte per chiudere — il duplicato e
#    il valore — quindi un server che implementasse solo la prima dava verde
#    senza aver mai guardato la lunghezza di un valore (rilievo R7.6).
SENZA_NOME = [v for v in BUONE if v[0] != "client.nome"]


def ciao(voci=None, versione=1):
    return inquadra(0x0001, capacita(BUONE if voci is None else voci, versione))


def attacca(tl=1920, ta=1080, vl=1920, va=1080, disp="it"):
    return inquadra(0x0006, struct.pack("!IIII", tl, ta, vl, va) + s(disp))


def banco_marca(id_=1, colore=0x00FF0000, ritardo=0):
    return inquadra(0x000F, struct.pack("!III", id_, colore, ritardo))


async def banco_esito(cli, es, id_, esito, motivo):
    """⛔ §7.5: `BANCO_ESITO` si verifica CAMPO PER CAMPO.

    Un server che rispondesse `BANCO_ESITO(ACCETTATA)` a funzione spenta
    passerebbe un banco che guarda solo «e' arrivata una risposta e la
    sessione regge» — e dipingerebbe quadratini sul desktop di qualcuno.
    """
    nome, corpo, _ = await b3.attendi(cli, None, attesa=6)
    if nome != "0x0010":
        raise RuntimeError(f"atteso BANCO_ESITO, arrivato {nome}")
    if len(corpo) < 14:
        raise RuntimeError(f"BANCO_ESITO di {len(corpo)} byte: §7.5 ne vuole 14")
    v_id, v_esito, v_motivo = struct.unpack("!IBB", corpo[:6])
    v_istante = struct.unpack("!Q", corpo[6:14])[0]
    es.banco = f"id={v_id} esito={v_esito} motivo={v_motivo} istante={v_istante}"
    if (v_id, v_esito, v_motivo) != (id_, esito, motivo):
        raise RuntimeError(
            f"BANCO_ESITO {es.banco}, atteso id={id_} esito={esito} "
            f"motivo={motivo}")
    # ⛔ «`istante`: 0 se rifiutata, ed e' l'unico significato di *assente*
    #    per questo campo» (§7.5, §6.0).
    if v_esito == 2 and v_istante != 0:
        raise RuntimeError(f"rifiutata, ma `istante` vale {v_istante} e non 0")


# ---------------------------------------------------------------------------
class Esito:
    """Che cosa e' successo, dal lato che riceve."""

    def __init__(self):
        self.motivo = None        # dal CONGEDO / RESPINTO — MAI dedotto
        self.tipo_motivo = None   # ⛔ IN QUALE messaggio e' arrivato (§11, §4.4)
        self.dettaglio = ""
        self.codice_wt = None     # dalla chiusura della sessione (§3.1 punto 3)
        self.stato_http = None    # per il caso del percorso
        self.messaggi = []        # i tipi arrivati, in ordine
        self.viva = False         # la sessione e' ancora aperta alla fine
        # ⛔ La violazione e' partita davvero?  Vedi il punto 1 del docstring:
        #    senza questa marca un caso che cade nella PREPARAZIONE conta come
        #    verde (rilievo R7.1).
        self.provocato = False
        self.fase = "apertura"    # dove si e' fermato, se si e' fermato
        self.errore = None

    def __str__(self):
        p = []
        if self.stato_http and self.stato_http != "200":
            p.append(f":status={self.stato_http}")
        if not self.provocato:
            p.append(f"⛔ violazione MAI SPEDITA (fermo in «{self.fase}»)")
        if self.motivo is not None:
            p.append(f"motivo={self.motivo:#04x}={MOTIVI.get(self.motivo, '?')}"
                     f" in {self.tipo_motivo}")
        elif self.tipo_motivo is not None:
            p.append(f"{self.tipo_motivo} senza motivo leggibile")
        p.append("chiusura-wt=" + ("(assente)" if self.codice_wt is None
                                   else f"{self.codice_wt:#04x}"))
        if self.viva:
            p.append("sessione VIVA")
        if self.errore:
            p.append(f"errore={self.errore}")
        return "  ".join(p) if p else "niente"


async def raccogli(cli, es, attesa, grazia=1.5):
    """Aspetta il congedo, o la fine dell'attesa se la sessione regge.

    ⛔ **Questo e' l'unico posto in cui `es.motivo` viene scritto**, e lo
       scrive da un messaggio arrivato sul filo (§8.1: dal lato che riceve).
    """
    scadenza = asyncio.get_event_loop().time() + attesa
    while True:
        resta = scadenza - asyncio.get_event_loop().time()
        if resta <= 0:
            break
        try:
            m = await asyncio.wait_for(cli.messaggi.get(), timeout=resta)
        except asyncio.TimeoutError:
            break
        if m is None:
            break
        tipo, corpo, _ = m
        es.messaggi.append(tipo)
        if tipo in (CONGEDO, RESPINTO):
            # ⛔ Si ricorda QUALE dei due, perche' §4.4 e §11 li distinguono e
            #    il verdetto lo chiede (rilievo R7.9).
            es.tipo_motivo = "CONGEDO" if tipo == CONGEDO else "RESPINTO"
            # ⛔ E un corpo VUOTO non e' «nessun motivo»: §7.1 vuole `u8
            #    motivo` (piu' `stringa dettaglio` nel `CONGEDO`) e §3.1 vieta
            #    il codice 0.  Con `corpo[0] if corpo else None` un server che
            #    chiude MALE era piu' facile da far passare di uno che chiude
            #    bene, perche' lasciava `motivo = None` (rilievo R7.2).
            if not corpo:
                es.errore = (f"{es.tipo_motivo} con corpo VUOTO: §7.1 ne vuole "
                             "almeno il byte del motivo")
                break
            es.motivo = corpo[0]
            if tipo == CONGEDO and len(corpo) >= 3:
                n = struct.unpack("!H", corpo[1:3])[0]
                es.dettaglio = corpo[3:3 + n].decode("utf-8", "replace")
            break
        if tipo == BANCO_ESITO:
            break
    # ⛔ §3.1 PUNTO 3, E PERCHE' SI ASPETTA.
    #
    #    Il `CONGEDO` viaggia sul canale di controllo, la chiusura della
    #    sessione e' una capsula sullo stream della sessione: sono due strade
    #    diverse e arrivano in due momenti diversi.  Leggere `codice_chiusura`
    #    nell'istante esatto in cui il `CONGEDO` e' stato letto misurerebbe
    #    «la seconda strada non e' arrivata» ogni volta che il server la manda
    #    un millisecondo dopo — cioe' misurerebbe la nostra fretta.
    #    ⚠ La finestra e' DICHIARATA e limitata: se scade, il valore resta
    #      `None` e il verdetto lo conta come mancato, non lo nasconde.
    if es.motivo is not None or es.errore is not None:
        fine = asyncio.get_event_loop().time() + grazia
        while (cli.codice_chiusura is None and not cli.finito
               and asyncio.get_event_loop().time() < fine):
            await asyncio.sleep(0.02)
    es.codice_wt = cli.codice_chiusura
    # ⛔ «Viva» vuol dire viva.  Prima bastava che non fosse arrivato un
    #    motivo, e un server che mandava `ECCOMI` e poi CHIUDEVA la sessione
    #    senza congedo dava la riga «la sessione regge» mentre era morta
    #    (rilievo R7.2): la chiusura WebTransport e il `FIN` sul canale di
    #    controllo entrano nel giudizio, non solo nella stampa.
    es.viva = (not cli.finito and es.motivo is None
               and es.codice_wt is None and es.errore is None)


async def apri(a, percorso="/rcp/1"):
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{a.indirizzo}:{a.porta}"
    gestore = connect(a.indirizzo, a.porta, configuration=conf,
                      create_protocol=Cliente)
    cli = await gestore.__aenter__()
    await asyncio.wait_for(cli.wait_connected(), timeout=8)
    cli.apri_sessione(autorita, percorso)
    stato = await asyncio.wait_for(cli.accettata, timeout=8)
    return gestore, cli, stato


async def fino_a_eccomi(cli, corpo=None):
    cli.apri_controllo()
    cli.manda(corpo if corpo is not None else ciao())
    return await b3.attendi(cli, "ECCOMI")


async def fino_ad_ammesso(cli, a):
    await fino_a_eccomi(cli)
    cli.manda(inquadra(0x0003, s(a.utente) + s(a.parola)))
    return await b3.attendi(cli, "AMMESSO", attesa=20)


async def fino_a_sessione(cli, a):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca())
    return await b3.attendi(cli, "SESSIONE")


# ===========================================================================
# I CASI.  ⛔ Ciascuno dichiara la sua ATTESA prima di misurare (§1.11): la
#          colonna «atteso» e' una PREVISIONE scritta nel file, non un
#          commento sul risultato.
# ===========================================================================
CASI = []


def caso(nome, atteso, spiega, dove="prima"):
    def dec(f):
        CASI.append((nome, atteso, spiega, dove, f))
        return f
    return dec


# ── L'inquadratura (§6.1) ──────────────────────────────────────────────────
@caso("tipo-sconosciuto", ERRORE_PROTOCOLLO,
      "un tipo che non esiste sul canale di controllo: §3 vieta di ignorarlo")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    cli.manda(inquadra(0x00FF, b""))


@caso("tipo-del-server", ERRORE_PROTOCOLLO,
      "ECCOMI mandato DAL CLIENT: tipo conosciuto, verso sbagliato (§7.1)")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    cli.manda(inquadra(0x0002, capacita(BUONE)))


@caso("lunghezza-in-piu", ERRORE_PROTOCOLLO,
      "un CIAO buono con quattro byte di riempimento in coda (§6.0: nessun "
      "riempimento)")
async def _(cli, a, es):
    corpo = capacita(BUONE) + b"\x00\x00\x00\x00"
    cli.apri_controllo()
    cli.manda(inquadra(0x0001, corpo))


@caso("lunghezza-in-meno", ERRORE_PROTOCOLLO,
      "una lunghezza piu' corta dei campi che il tipo prevede")
async def _(cli, a, es):
    corpo = capacita(BUONE)
    cli.apri_controllo()
    # si dichiara meta' corpo, e si mandano solo quei byte: l'elenco delle
    # capacita' si tronca a meta' di una stringa
    cli.manda(struct.pack("!HI", 0x0001, len(corpo) // 2) + corpo[:len(corpo) // 2])


@caso("lunghezza-4gib", ERRORE_PROTOCOLLO,
      "⛔ una lunghezza annunciata di 4 GiB: §6.1 vieta di allocare prima di "
      "controllare, e un server ucciso dal nucleo «fa cadere la connessione» "
      "lo stesso — portandosi via le sessioni di tutti gli altri (R3.3)")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(struct.pack("!HI", 0x0001, 0xFFFFFFFF))


@caso("lunghezza-oltre-1mib", ERRORE_PROTOCOLLO,
      "un messaggio che annuncia piu' di 1 MiB (§6.1)")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(struct.pack("!HI", 0x0001, 2 * 1024 * 1024))


@caso("stato-sbagliato", ERRORE_PROTOCOLLO,
      "CREDENZIALI come primo messaggio, prima di CIAO")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(inquadra(0x0003, s(a.utente) + s(a.parola)))


@caso("ciao-due-volte", ERRORE_PROTOCOLLO,
      "un secondo CIAO dopo ECCOMI: lo stesso messaggio, lo stato sbagliato")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    cli.manda(ciao())


# ── La versione (§2.4, §9) ─────────────────────────────────────────────────
@caso("versione-2", VERSIONE_INCOMPATIBILE,
      "⛔ CIAO(versione=2) su /rcp/1: §2.4 dice che le due DEVONO coincidere. "
      "⚠ §9 da sola direbbe ECCOMI(1) — e' una contraddizione di RCP.md")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(versione=2))


@caso("versione-0", VERSIONE_INCOMPATIBILE,
      "CIAO(versione=0) su /rcp/1: dall'altra parte dello stesso confine")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(versione=0))


# ── Le capacita' (§4.3) ────────────────────────────────────────────────────
@caso("nome-maiuscolo", ERRORE_PROTOCOLLO,
      "un nome di capacita' con le maiuscole: §4.3 ammette a-z 0-9 . _")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(BUONE + [("Video.Codec", "hevc")]))


@caso("nome-65-byte", ERRORE_PROTOCOLLO,
      "un nome da 65 byte: il limite di §4.3 e' 64")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(BUONE + [("x" * 65, "si")]))


@caso("nome-con-trattino-basso", None,
      "⭐ `video.misura_massima`: il trattino basso e' LECITO, ed e' la "
      "contraddizione che il validatore di B4 ha trovato in §4.3 il 10 agosto")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(BUONE + [("video.misura_massima", "3840x2160")]))
    await b3.attendi(cli, "ECCOMI")


@caso("valore-vuoto", ERRORE_PROTOCOLLO,
      "un valore vuoto: «chi non ha niente da dire non manda la capacita'».  "
      "⛔ UNA violazione sola: `client.nome` compare una volta e basta")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(SENZA_NOME + [("client.nome", "")]))


@caso("valore-257-byte", ERRORE_PROTOCOLLO,
      "un valore da 257 byte: il limite di §4.3 e' 256.  ⛔ UNA violazione "
      "sola, per la stessa ragione del caso di sopra")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(SENZA_NOME + [("client.nome", "x" * 257)]))


@caso("capacita-ripetuta", ERRORE_PROTOCOLLO,
      "`video.codec` due volte: «vince l'ultimo» e «vince il primo» sono due "
      "implementazioni dello stesso documento")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(BUONE + [("video.codec", "av1")]))


@caso("capacita-del-lato-sbagliato", ERRORE_PROTOCOLLO,
      "`banco.marca` mandata DAL CLIENT: §4.3 la dichiara del server, e il "
      "nome e' conosciuto — l'eccezione dei nomi sconosciuti non la copre")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(BUONE + [("banco.marca", "si")]))


@caso("capacita-sconosciuta", None,
      "⭐ un NOME che non esiste: si ignora e si prosegue — eccezione 1 di §3")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(BUONE + [("questa.non.esiste", "boh")]))
    await b3.attendi(cli, "ECCOMI")


@caso("solo-vp9", NIENTE_IN_COMUNE,
      "`video.codec = vp9` e basta: non ha sbagliato a scrivere, non ha di "
      "che parlare — e il motivo NON e' ERRORE_PROTOCOLLO")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao([("video.codec", "vp9"), ("video.profondita", "8"),
                    ("audio.codec", "pcm")]))


@caso("hevc-e-vp9", None,
      "⭐ `video.codec = hevc,vp9`: si legge `hevc` e si prosegue, e lo "
      "SCARTO si scrive nel registro del server (§4.3)")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao([("video.codec", "hevc,vp9"), ("video.profondita", "8"),
                    ("audio.codec", "pcm")]))
    await b3.attendi(cli, "ECCOMI")


@caso("senza-pcm", NIENTE_IN_COMUNE,
      "`audio.codec = opus` senza `pcm`: §4.3 lo impone a entrambi, e chi non "
      "lo dichiara si congeda con NIENTE_IN_COMUNE — non con ERRORE_PROTOCOLLO")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao([("video.codec", "hevc"), ("video.profondita", "8"),
                    ("audio.codec", "opus")]))


@caso("senza-8", NIENTE_IN_COMUNE,
      "`video.profondita = 10` senza `8`: idem")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao([("video.codec", "hevc"), ("video.profondita", "10"),
                    ("audio.codec", "pcm")]))


# ── Le credenziali (§4.4) ──────────────────────────────────────────────────
@caso("utente-vuoto", ERRORE_PROTOCOLLO,
      "⛔ utente di zero byte: legale per §6.0, fuori intervallo per §4.4 — e "
      "senza questo controllo un attaccante non muove nessun contatore")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    cli.manda(inquadra(0x0003, s("") + s(a.parola)))


@caso("parola-vuota", ERRORE_PROTOCOLLO,
      "parola di zero byte: idem")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    cli.manda(inquadra(0x0003, s(a.utente) + s("")))


@caso("utente-257-byte", ERRORE_PROTOCOLLO,
      "utente da 257 byte: il limite di §4.4 e' 256")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    cli.manda(inquadra(0x0003, s("u" * 257) + s(a.parola)))


@caso("parola-1025-byte", ERRORE_PROTOCOLLO,
      "parola da 1025 byte: il limite di §4.4 e' 1024")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    cli.manda(inquadra(0x0003, s(a.utente) + s("p" * 1025)))


@caso("credenziali-due-volte", ERRORE_PROTOCOLLO,
      "§4.4: un solo tentativo per connessione")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(inquadra(0x0003, s(a.utente) + s(a.parola)))


# ── ATTACCA (§4.5, §7.1) ───────────────────────────────────────────────────
@caso("tela-1921x1080", ERRORE_PROTOCOLLO,
      "tela dispari: il codificatore l'arrotonderebbe in silenzio — due misure "
      "diverse sotto la stessa etichetta, la forma d'errore E2")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca(tl=1921))


@caso("tela-319x240", ERRORE_PROTOCOLLO, "tela sotto il minimo di §4.5")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca(tl=319, ta=240))


@caso("tela-7682x4320", ERRORE_PROTOCOLLO, "tela sopra il massimo di §4.5")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca(tl=7682, ta=4320))


@caso("vista-300x801", None,
      "⭐ DEVE PASSARE: §7.1 dice che la vista non ha i vincoli della tela — "
      "«qualunque misura da 1x1 in su e' legale, dispari compresa» (R1.17)")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca(vl=300, va=801))
    await b3.attendi(cli, "SESSIONE")


@caso("vista-1x1", None,
      "⭐ DEVE PASSARE: il limite inferiore dichiarato da §7.1, alla lettera")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca(vl=1, va=1))
    await b3.attendi(cli, "SESSIONE")


@caso("disposizione-malformata", ERRORE_PROTOCOLLO,
      "`it!!` non e' un nome XKB: ha sbagliato a scrivere")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca(disp="it!!"))


@caso("disposizione-sconosciuta", SESSIONE_NON_SERVIBILE,
      "⛔ `zz` e' BEN FORMATA e la macchina non ce l'ha: §4.5 vuole DUE guasti "
      "diversi, e il dettaglio DEVE stare nel corpo (§8.2)")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca(disp="zz"))


@caso("disposizione-con-variante", None,
      "⭐ `de(neo)`: la forma con la variante fra parentesi e' lecita (§4.5)")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca(disp="de(neo)"))
    await b3.attendi(cli, "SESSIONE")


# ── La funzione di banco (§7.5) ────────────────────────────────────────────
@caso("banco-spento", None,
      "⛔ `BANCO_MARCA` a funzione spenta: DEVE arrivare "
      "`BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)` — non un silenzio e non una "
      "chiusura.  E' lo stato PREDEFINITO di ogni server")
async def _(cli, a, es):
    await fino_a_sessione(cli, a)
    cli.manda(banco_marca(id_=1, ritardo=0))
    await banco_esito(cli, es, id_=1, esito=2, motivo=1)  # RIFIUTATA, SPENTA


@caso("banco-ritardo-20000", None,
      "`ritardo_ms = 20000`: `RITARDO_FUORI_LIMITI`, e ⛔ **non** "
      "ERRORE_PROTOCOLLO — far cadere la sessione al banco che si sta tarando "
      "e' la cattiva idea che §7.1 evita per le misure fuori limite")
async def _(cli, a, es):
    await fino_a_sessione(cli, a)
    cli.manda(banco_marca(id_=7, ritardo=20000))
    await banco_esito(cli, es, id_=7, esito=2, motivo=2)  # RIFIUTATA, RITARDO


@caso("banco-id-zero", ERRORE_PROTOCOLLO,
      "`id = 0`, che §7.5 dichiara riservato.  ⚠ Il documento non dice l'esito: "
      "qui si sceglie la caduta, perche' e' un messaggio malformato e non un "
      "parametro di banco sbagliato")
async def _(cli, a, es):
    await fino_a_sessione(cli, a)
    cli.manda(banco_marca(id_=0))


@caso("banco-prima-di-sessione", ERRORE_PROTOCOLLO,
      "`BANCO_MARCA` prima di `SESSIONE`: non c'e' nessun fotogramma su cui "
      "dipingere")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(banco_marca())


# ── Gli stream (§2.5) ──────────────────────────────────────────────────────
#
# ⛔ QUI DENTRO IL CARICO E' BEN FORMATO APPOSTA, e non e' un dettaglio.
#
#    La violazione che questi quattro casi provano e' **lo stream**: quanti ce
#    ne sono, in che verso va il canale, su che tipo di stream vive.  Se dentro
#    ci si mette anche un messaggio storto — un `CIAO` con corpo di zero byte,
#    un `tipo` che non esiste — un server che non conta gli stream congeda
#    ugualmente, per l'altra ragione, e il caso e' **verde senza aver provato
#    niente** (rilievo R7.7).  Ogni carico qui sotto e' legale *in se'* e nello
#    stato in cui viene mandato: l'unica cosa storta e' lo stream.
@caso("secondo-bidirezionale", ERRORE_PROTOCOLLO,
      "⛔ «il client NON DEVE aprire stream bidirezionali oltre lo 0»: il "
      "canale di controllo e' UNO SOLO per tutta la sessione.  Il carico e' "
      "un CREDENZIALI ben formato, che dopo ECCOMI e' il messaggio giusto: "
      "l'unica violazione e' lo stream in piu'")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    altro = cli.apri_bidi()
    cli.manda_su(altro, inquadra(0x0003, s(a.utente) + s(a.parola)))


@caso("uni-controllo", ERRORE_PROTOCOLLO,
      "il canale di CONTROLLO (byte alto 0x00) su uno stream unidirezionale: "
      "«il controllo vive solo sullo stream 0» (§2.5).  ⚠ CREDENZIALI e non "
      "CIAO: un secondo CIAO sarebbe anche uno stato sbagliato, cioe' una "
      "seconda ragione per congedare")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    u = cli.apri_uni()
    cli.manda_su(u, inquadra(0x0003, s(a.utente) + s(a.parola)))


@caso("uni-video", ERRORE_PROTOCOLLO,
      "il canale VIDEO (0x03) DAL CLIENT: verso sbagliato — il video va dal "
      "server al client (§2.5).  ⛔ `0x0301` = fotogramma chiave, che §6.2 "
      "dichiara LEGALE: con `0x0300` l'unica regola applicabile era «altri "
      "valori: ERRORE_PROTOCOLLO», e il verso non veniva mai messo alla prova")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    u = cli.apri_uni()
    # l'intestazione di 28 byte esatti di §6.2: tipo, codec, largh., altezza,
    # numero, istante, input — tutti valori dentro i limiti
    cli.manda_su(u, struct.pack("!HHIIIQI", 0x0301, 1, 1920, 1080, 1, 0, 0))


@caso("uni-audio", ERRORE_PROTOCOLLO,
      "il canale AUDIO (0x04) su uno STREAM: l'audio vive solo sui datagram "
      "(§2.5, §6.3).  Il carico e' l'intestazione di §6.3 ben formata — "
      "`tipo = 0x0401`, `codec = 2` (PCM): l'unica violazione e' lo stream")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    u = cli.apri_uni()
    cli.manda_su(u, struct.pack("!HHQ", 0x0401, 2, 0))


@caso("uni-byte-alto-ignoto", ERRORE_PROTOCOLLO,
      "un byte alto che non e' nessuno dei cinque di §2.5")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    u = cli.apri_uni()
    cli.manda_su(u, struct.pack("!HI", 0x0900, 0))


# ===========================================================================
async def gira_caso(a, nome, atteso, spiega, f):
    es = Esito()
    gestore = None
    try:
        gestore, cli, stato = await apri(a)
        es.stato_http = stato
        if stato != "200":
            es.errore = f"la CONNECT estesa ha risposto {stato}"
            return es
        es.fase = "preparazione+violazione"
        await f(cli, a, es)
        # ⛔ QUI, E NON PRIMA.  Tutti i casi con un `atteso` finiscono con
        #    l'invio del byte storto e non aspettano niente dopo: se `f` torna,
        #    la violazione e' partita davvero.  Se invece si e' fermata prima —
        #    l'`ATTACCA` fisso rifiutato, l'`ECCOMI` che non arriva, PAM che
        #    dice di no — il caso non ha provato niente e `provocato` resta
        #    falso, che e' quel che il verdetto guarda (rilievo R7.1).
        es.provocato = True
        es.fase = "raccolta"
        # ⚠ Sui casi che DEVONO passare si aspetta lo stesso: «non e' caduta
        #   subito» non e' «non e' caduta».
        await raccogli(cli, es, attesa=3.0 if atteso is None else 12.0)
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        es.errore = f"{type(e).__name__}: {e}"
        # ⛔ E IL MOTIVO NON SI RASCHIA DAL TESTO DELL'ECCEZIONE.
        #
        #    Qui c'era un giro su `MOTIVI` che cercava il nome di un motivo di
        #    §8.2 dentro `str(e)` e lo prendeva per «motivo arrivato».  Il
        #    difetto: `b3.attendi` solleva `RuntimeError("CONGEDO invece di
        #    SESSIONE: motivo 0x0b = ERRORE_PROTOCOLLO")` anche quando a
        #    cadere e' la PREPARAZIONE — e quella stringa contiene esattamente
        #    il nome del motivo atteso.  R7.1 ne ha contati **dodici** che
        #    potevano essere verdi col byte storto mai spedito, e ⚠ **si
        #    richiudeva su se' stesso**: piu' il server era rotto a monte, piu'
        #    quei casi diventavano verdi (rilievo R7.1, forme E6 ed E7).
        #
        # ⭐ Il motivo lo legge `raccogli`, da un messaggio arrivato sul filo.
        #    Il testo dell'eccezione resta quel che e': una diagnosi da
        #    stampare, non un verdetto.
    finally:
        if gestore is not None:
            try:
                await gestore.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass
    return es


async def il_percorso(a):
    """⛔ §2.2: una sessione WebTransport su un percorso diverso e' un 404.

    Sta a parte perche' non e' una violazione di RCP: e' §3 applicata **al
    primo byte**, prima che RCP cominci — e infatti non c'e' nessun CONGEDO da
    aspettare, perche' non c'e' nessun canale di controllo.
    """
    fuori = []
    for percorso, atteso in (("/rcp/2", "404"), ("/", "404"),
                             ("/rcp/1", "200")):
        gestore = None
        try:
            gestore, cli, stato = await apri(a, percorso)
        except Exception as e:  # noqa: BLE001
            stato = f"errore {type(e).__name__}"
        finally:
            if gestore is not None:
                try:
                    await gestore.__aexit__(None, None, None)
                except Exception:  # noqa: BLE001
                    pass
        fuori.append((percorso, atteso, stato, stato == atteso))
    return fuori


async def ancora_vivo(a):
    """⛔ B0.5 — la meta' che nessuno scrive.

    Non basta che la connessione sia caduta: **deve essere caduta la
    connessione, non il server**.  Qui si apre una connessione nuova e si
    arriva fino a `ECCOMI`.
    ⚠ Non fino a `SESSIONE`: costerebbe il secondo fisso di §4.4-bis a ogni
      caso, cioe' quaranta secondi di banco per una proprieta' che il giro
      completo in coda verifica una volta e bene.
    """
    gestore = None
    try:
        gestore, cli, stato = await apri(a)
        if stato != "200":
            return False, f":status {stato}"
        await fino_a_eccomi(cli)
        return True, ""
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"
    finally:
        if gestore is not None:
            try:
                await gestore.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass


async def giro_completo(a):
    """La stretta di mano buona, intera: il controllo che dice che il server
    non e' rimasto in piedi ma inutile."""
    gestore = None
    try:
        gestore, cli, stato = await apri(a)
        if stato != "200":
            return False, f":status {stato}"
        await fino_a_sessione(cli, a)
        return True, ""
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"
    finally:
        if gestore is not None:
            try:
                await gestore.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass


async def limitatore(a):
    """⛔ §4.4-bis, e le due meta' che si dimenticano.

    a) i messaggi MALFORMATI non muovono nessun contatore: sei `CREDENZIALI`
       fuori intervallo, e poi una buona che DEVE passare;
    b) il contatore **per indirizzo** esiste davvero: sei tentativi falliti con
       SEI NOMI DIVERSI dallo stesso indirizzo, e il settimo — ancora un nome
       nuovo — deve ricevere `TROPPI_TENTATIVI`.

    ⚠ **Previsione scritta prima di misurare**: (b) sara' ROSSO.  La chiave del
      contatore per indirizzo e' la `provenienza`, che contiene **la porta** —
      e con un solo tentativo per connessione (§4.4) la porta cambia ogni
      volta, quindi quel contatore vale sempre 1 e non blocca mai nessuno.  E'
      la forma peggiore: codice presente, che sembra giusto, e che non fa
      niente.
    """
    fuori = {}
    # (a) sei malformati, poi una buona
    for i in range(6):
        gestore, cli, _ = await apri(a)
        try:
            await fino_a_eccomi(cli)
            cli.manda(inquadra(0x0003, s("") + s("x")))
            await asyncio.sleep(0.2)
        except Exception:  # noqa: BLE001
            pass
        finally:
            await gestore.__aexit__(None, None, None)
    ok, perche = await giro_completo(a)
    fuori["malformati-non-contano"] = (ok, perche)

    # (b) sette falliti con SETTE NOMI DIVERSI, dallo stesso indirizzo
    motivi = []
    for i in range(7):
        gestore, cli, _ = await apri(a)
        es = Esito()
        try:
            await fino_a_eccomi(cli)
            cli.manda(inquadra(0x0003, s(f"nessuno{i}") + s("sbagliata")))
            # ⚠ Si ASPETTA la risposta invece di dormire un tempo scelto a
            #   occhio: PAM ha un suo ritardo sui fallimenti, e un `sleep`
            #   troppo corto misurerebbe un contatore che non e' ancora stato
            #   incrementato.
            await raccogli(cli, es, attesa=15)
        except Exception:  # noqa: BLE001
            pass
        finally:
            await gestore.__aexit__(None, None, None)
        motivi.append(es.motivo)
    # I primi cinque sono CREDENZIALI_ERRATE; dal sesto in poi la soglia di
    # §4.4-bis e' passata, e il contatore PER INDIRIZZO deve parlare.
    fuori["contatore-per-indirizzo"] = (
        motivi[-1] == TROPPI_TENTATIVI,
        "motivi: " + " ".join(
            MOTIVI.get(m, str(m)) if m is not None else "-" for m in motivi))

    # ⛔ E IL CONTROLLO CHE DISTINGUE UN CONTATORE DA UN BLOCCO: adesso la
    #    parola d'ordine GIUSTA, dallo stesso indirizzo, DEVE ricevere
    #    TROPPI_TENTATIVI lo stesso.  Un server che contasse senza bloccare
    #    darebbe la stessa riga di sopra e lascerebbe entrare chiunque
    #    indovinasse al sesto colpo.
    gestore, cli, _ = await apri(a)
    es = Esito()
    try:
        await fino_a_eccomi(cli)
        cli.manda(inquadra(0x0003, s(a.utente) + s(a.parola)))
        await raccogli(cli, es, attesa=15)
    except Exception:  # noqa: BLE001
        pass
    finally:
        await gestore.__aexit__(None, None, None)
    fuori["blocca-anche-la-parola-giusta"] = (
        es.motivo == TROPPI_TENTATIVI,
        f"con le credenziali BUONE: {MOTIVI.get(es.motivo, es.motivo)}")
    return fuori


VERDE, ROSSO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[0m"


def riga(ok, nome, testo):
    print(f"    {VERDE if ok else ROSSO}{'OK' if ok else 'NO'}{GRIGIO}  "
          f"{nome:26s} {testo}")


def esito_finale(conti, guasti, parziale):
    """⛔ Ogni conteggio con il suo denominatore, e il denominatore CALCOLATO.

    La riga vecchia stampava `N su N` — la stessa espressione due volte — e
    solo quando `guasti == 0`, cioe' non portava nessuna informazione che il
    colore non portasse gia' (rilievo R7.14).  ⚠ E un denominatore a **zero**
    si dice, non si nasconde: «0 su 0» non e' un verde.
    """
    print()
    print("    == quel che questo giro ha davvero guardato")
    for che, (buoni, tot) in conti.items():
        if tot == 0:
            # ⛔ Un denominatore zero si DICHIARA: «nessuno ha guardato» e
            #    «tutti passati» hanno lo stesso aspetto se si tace.
            print(f"    --  {che:44s} nessun caso lo ha sollecitato")
            continue
        col = VERDE if buoni == tot else ROSSO
        print(f"    {col}{buoni:3d} su {tot:3d}{GRIGIO}  {che}")
    print()
    if guasti:
        print(f"    {ROSSO}⛔ B5: {guasti} punti non passano{GRIGIO}")
        return 1
    if parziale:
        print(f"    {VERDE}⭐ i casi selezionati passano{GRIGIO} — ⚠ e questo "
              f"NON e' «B5 passa»: il giro era parziale")
        return 0
    print(f"    {VERDE}⭐ B5 passa, e i numeri qui sopra dicono su che cosa"
          f"{GRIGIO}")
    return 0


def conta(casi):
    """⛔ I due numeri, CALCOLATI — e sono due, non uno.

    «44 violazioni su 44» stampava la stessa espressione come numeratore e
    come denominatore, e ci contava dentro anche gli otto casi che DEVONO
    passare, su cui «il motivo giusto ogni volta» e' falso per costruzione
    (rilievo R7.14).  Da qui in poi il numero lo produce questa funzione, e
    nessun commento lo riscrive a mano.
    """
    violazioni = sum(1 for c in casi if c[1] is not None)
    return violazioni, len(casi) - violazioni


async def principale(a):
    casi = [c for c in CASI if not a.solo or a.solo in c[0]]
    tot_v, tot_verdi = conta(CASI)
    if a.elenco:
        print(f"== B5: {len(CASI)} casi — {tot_v} violazioni e {tot_verdi} "
              f"⭐ verdi attesi.  Ogni riga e' una PREVISIONE\n")
        for nome, atteso, spiega, dove, _ in CASI:
            att = (f"{atteso:#04x} {MOTIVI.get(atteso, '?')}" if atteso
                   else "⭐ DEVE PASSARE")
            print(f"  {nome:26s} {att}")
            print(f"  {'':26s}   {spiega}")
        return 0

    # ⛔ ZERO CASI NON E' «TUTTI PASSATI».
    #
    #    `--solo pippo` non combaciava con nessun nome, il ciclo non girava, e
    #    il banco stampava «0 violazioni su 0» e usciva 0: un errore di
    #    battitura nel filtro era indistinguibile da un banco verde (rilievo
    #    R7.15).  ⭐ Sono TRE esiti — non ho niente da misurare, non passa,
    #    passa — e vogliono tre codici d'uscita diversi.
    if not casi:
        print(f"    {ROSSO}⛔ «--solo {a.solo}» ha selezionato ZERO casi su "
              f"{len(CASI)}: non c'e' niente da misurare{GRIGIO}")
        print("       Questo NON e' un verde.  I nomi si leggono con --elenco.")
        return 2

    sel_v, sel_verdi = conta(casi)
    print(f"== B5 — le prove di violazione verso il server")
    print(f"   {len(casi)} casi su {len(CASI)} selezionati: {sel_v} violazioni "
          f"e {sel_verdi} ⭐ verdi attesi")
    print("   ⛔ ogni caso: la violazione spedita davvero, il motivo giusto nel "
          "messaggio giusto,")
    print("      le due strade di §3.1, e il server ancora vivo dopo\n")
    if a.solo:
        print(f"    ⚠ GIRO PARZIALE.  Il percorso (§2.2), il giro completo e il")
        print(f"      limitatore (§4.4-bis) NON si eseguono: non dipendono dai")
        print(f"      casi selezionati, e girarli qui direbbe «passa» su una")
        print(f"      parte del banco che nessuno ha chiesto di misurare.\n")

    # ⛔ OGNI CONTEGGIO CON IL SUO DENOMINATORE, e i denominatori sono diversi
    #    perche' le proprieta' misurate sono diverse.
    conti = {
        "violazioni col motivo atteso": [0, 0],
        "⭐ verdi attesi, sessione viva": [0, 0],
        "§3.1 punto 3 — motivo nella chiusura WT": [0, 0],
        "§11 — motivo nel messaggio giusto": [0, 0],
    }
    guasti, morto = 0, False
    for nome, atteso, spiega, dove, f in casi:
        es = await gira_caso(a, nome, atteso, spiega, f)
        if atteso is None:
            conti["⭐ verdi attesi, sessione viva"][1] += 1
            # ⛔ `viva` si CALCOLAVA e non si guardava: bastava che non fosse
            #    arrivato un motivo, quindi un server che manda ECCOMI e poi
            #    chiude la sessione WebTransport dava la riga «la sessione
            #    regge» mentre la sessione era morta (rilievo R7.2).
            ok = es.viva and es.errore is None
            testo = ("la sessione regge" if ok else str(es))
            conti["⭐ verdi attesi, sessione viva"][0] += int(ok)
        else:
            conti["violazioni col motivo atteso"][1] += 1
            atteso_in = PORTATORE.get(atteso, "CONGEDO")
            # §11: «almeno una delle due strade» deve aver portato il motivo.
            strade = []
            if es.motivo == atteso and es.tipo_motivo == atteso_in:
                strade.append(atteso_in)
            if es.codice_wt == atteso:
                strade.append("chiusura-WT")
            ok = es.provocato and bool(strade)
            conti["violazioni col motivo atteso"][0] += int(ok)
            testo = str(es)
        riga(ok, nome, testo)
        if not ok:
            guasti += 1
            print(f"        atteso: "
                  + (f"{atteso:#04x} {MOTIVI.get(atteso, '?')}" if atteso
                     else "⭐ nessuna caduta"))
            print(f"        {spiega}")
            if atteso is not None and not es.provocato:
                print(f"        ⛔ e la violazione NON E' MAI PARTITA: il caso "
                      f"si e' fermato in «{es.fase}».  Non e' una prova "
                      f"fallita, e' una prova non fatta")
        if es.dettaglio:
            print(f"        dettaglio dal corpo: «{es.dettaglio}»")
        if getattr(es, "banco", None):
            print(f"        BANCO_ESITO: {es.banco}")
        if atteso is not None and es.provocato:
            # ⛔ §3.1 PUNTO 3 SI CONTA, NON SI STAMPA.
            #
            #    Qui c'era una riga che diceva «il motivo e' arrivato per
            #    CONGEDO» anche quando la seconda strada non era arrivata
            #    affatto — vera, e capace di far credere il contrario — e
            #    `guasti` non veniva toccato in nessuno dei tre rami: R7.3 ha
            #    mostrato che TUTTE le violazioni restavano verdi con il punto
            #    3 mai implementato.
            #    Il punto 3 e' un DEVE **incondizionato**: la condizione di
            #    §3.1 sta sul punto 2, ed e' il punto 3 che il documento chiama
            #    «quello che salva le diagnosi».
            conti["§3.1 punto 3 — motivo nella chiusura WT"][1] += 1
            if es.codice_wt == atteso:
                conti["§3.1 punto 3 — motivo nella chiusura WT"][0] += 1
            else:
                guasti += 1
                visto = ("assente" if es.codice_wt is None
                         else f"{es.codice_wt:#04x}")
                riga(False, "", f"   §3.1 punto 3 su «{nome}»: la chiusura "
                                f"della sessione porta {visto}, atteso "
                                f"{atteso:#04x}")
            # ⛔ E IN QUALE MESSAGGIO (§11, §4.4).
            if es.motivo is not None:
                conti["§11 — motivo nel messaggio giusto"][1] += 1
                if es.tipo_motivo == PORTATORE.get(atteso, "CONGEDO"):
                    conti["§11 — motivo nel messaggio giusto"][0] += 1
                else:
                    guasti += 1
                    riga(False, "", f"   §11 su «{nome}»: il motivo e' arrivato "
                                    f"in {es.tipo_motivo}, e §11 lo vuole in "
                                    f"{PORTATORE.get(atteso, 'CONGEDO')} — sono "
                                    f"due macchine a stati diverse")
        # ⛔ e il server dopo?
        vivo, perche = await ancora_vivo(a)
        if not vivo:
            riga(False, "", f"⛔ IL SERVER NON RISPONDE PIU' dopo «{nome}»: {perche}")
            guasti += 1
            morto = True
            break

    if morto:
        print(f"\n    {ROSSO}⛔ il banco si ferma: senza un server non c'e' "
              f"niente da misurare{GRIGIO}")
        # ⚠ E si stampa lo stesso quel che si era guardato FIN LI': un banco
        #   che si ferma senza dire quanto aveva coperto lascia credere che
        #   avesse coperto tutto.
        return esito_finale(conti, guasti, parziale=True)

    # ⛔ SOTTO UN FILTRO QUESTE TRE SEZIONI NON SI ESEGUONO, ed e' dichiarato.
    #
    #    Non dipendono dai casi selezionati: girarle su una selezione parziale
    #    fa passare per «B5 passa» una misura che nessuno ha chiesto — e nel
    #    caso del limitatore blocca l'indirizzo per trenta secondi a chi stava
    #    solo riprovando un caso.  E' il gemello di R7.15(b), che nello script
    #    di lancio dava rosso su una regola mai sollecitata.
    if a.solo:
        print(f"\n    ⚠ giro parziale: percorso, giro completo e limitatore "
              f"saltati (vedi sopra)")
        return esito_finale(conti, guasti, parziale=True)

    print("\n== ⛔ Il percorso della sessione (§2.2), che viene prima di RCP")
    for percorso, atteso, stato, ok in await il_percorso(a):
        riga(ok, percorso, f":status = {stato}   (atteso {atteso})")
        if not ok:
            guasti += 1

    # ⛔ IL GIRO COMPLETO VIENE PRIMA DEL LIMITATORE, e l'ordine e' una misura.
    #
    #    Il limitatore di §4.4-bis, quando funziona, **blocca l'indirizzo** — e
    #    da quel momento anche la parola d'ordine giusta riceve
    #    TROPPI_TENTATIVI, per una finestra che parte da trenta secondi.  ⚠ Un
    #    banco che mettesse la stretta di mano buona DOPO leggerebbe quel
    #    rifiuto come «il server e' rotto», cioe' darebbe rosso proprio quando
    #    la regola funziona.
    print("\n== ⭐ La stretta di mano buona, intera")
    ok, perche = await giro_completo(a)
    riga(ok, "giro-completo", perche or "CIAO → CREDENZIALI → ATTACCA → SESSIONE")
    if not ok:
        guasti += 1

    print("\n== ⛔ Il limitatore dei tentativi (§4.4-bis) — per ultimo, e si dice perche'")
    print("   ⚠ da qui in poi questo indirizzo resta BLOCCATO per almeno trenta")
    print("     secondi: e' la regola che funziona, non un guasto del banco")
    for nome, (ok, perche) in (await limitatore(a)).items():
        riga(ok, nome, perche)
        if not ok:
            guasti += 1

    return esito_finale(conti, guasti, parziale=False)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="B5 — le violazioni verso il server")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7447)
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola", default="parola-di-prova")
    p.add_argument("--solo", default="", help="gira solo i casi che contengono questo")
    p.add_argument("--elenco", action="store_true",
                   help="stampa le previsioni senza misurare")
    sys.exit(asyncio.run(principale(p.parse_args())))
