#!/usr/bin/env python3
"""02-pam-fermo.py — ⛔ QUANTO STA FERMO CHI **NON** SI STA AUTENTICANDO.

    python3 02-pam-fermo.py --porta 7531 --parola-file F --giri 5

===========================================================================
⛔ PERCHE' QUESTO BANCO ESISTE, E PERCHE' NON NE BASTAVA UNO GIA' SCRITTO

`DECISIONI.md` §1.10, 11 agosto 2026, dall'utente: la verifica PAM blocca
l'unico ciclo `poll` del server, e si cura **prima della fase 2**.  ⛔ E la
riga che ordina questo file e' l'ultima di quella decisione:

    «La proprieta' da provare NON e' "PAM funziona ancora": e' "mentre uno si
     autentica, gli altri non se ne accorgono" — e oggi non esiste nessun
     banco che la guardi.  Senza quel banco la cura e' una speranza.»

⛔ **B8 non lo puo' fare, e non e' una svista sua**: B8 cronometra la risposta
   a `CREDENZIALI`, cioe' **il tempo di chi entra**.  Quel numero e' governato
   da PAM (`[M]` 11 agosto: +1034 ms oltre il secondo fisso sui respinti,
   la firma di `pam_faildelay`) e ⭐ **dopo la cura deve restare quello che
   e'**.  Chi misurasse solo quello vedrebbe una cura riuscita come un
   fallimento, o — peggio — non vedrebbe niente e chiamerebbe verde la
   speranza.

⇒ Qui si misura **l'altro numero**: quanto tempo passa fermo chi si e' gia'
  autenticato, o chi sta facendo tutt'altro, MENTRE un terzo presenta
  credenziali sbagliate (il caso lento, quello con `pam_faildelay`).

===========================================================================
⛔ LA SCENA, DICHIARATA — tre connessioni, e ciascuna ha un mestiere

    A   «gia' dentro»       stretta di mano completa fino a `SESSIONE`, utente
                            `prova`.  ⭐ **E' il righello**: da attaccata manda
                            `BANCO_MARCA` (§7.5) ogni 50 ms e cronometra il
                            `BANCO_ESITO` che torna.  E' l'unica coppia
                            domanda/risposta che RCP concede a una sessione
                            ATTIVA alla fase 1 — dalla fase 2 al suo posto ci
                            sara' un fotogramma, e il numero vorra' dire la
                            stessa cosa: **quanto sta fermo lo schermo di chi
                            sta gia' lavorando**;

    C   «il caso lento»     apre, arriva a `attesa-credenziali`, e manda
                            `CREDENZIALI` con la parola **SBAGLIATA**.  ⛔ Il
                            motivo del `RESPINTO` si legge e si pretende
                            `0x07 CREDENZIALI_ERRATE`: un `0x08
                            TROPPI_TENTATIVI` vuol dire che l'indirizzo era
                            bannato e ⛔ **PAM non e' stata nemmeno
                            interrogata** — cioe' il campione misurerebbe un
                            server che non ha fatto la cosa lenta.  Quel
                            campione si BUTTA, e si dice perche';

    B   «la seconda che fa  nasce nell'istante in cui C manda `CREDENZIALI`, e
        la stretta di mano» cronometra **da zero a `ECCOMI`**.  E' il secondo
                            righello, quello che il mandato nomina per primo:
                            un utente qualunque che apre la pagina mentre un
                            altro sbaglia la parola.

⛔ **Il denominatore che rende leggibile tutto**: prima della finestra si
   cronometrano 20 marche a ciclo tranquillo.  ⭐ Se la mediana tranquilla non
   fosse piccola, il righello sarebbe rotto e non ci sarebbe niente da
   confrontare — e il banco lo dice invece di dividere per un numero che non ha
   guardato (`LEZIONI.md` §1.9: un denominatore si legge dove la cosa succede).

===========================================================================
⭐ IL CONTROLLO POSITIVO, E QUI E' PIU' FORTE DEL SOLITO

«Lo strumento sa trovare qualcosa che c'e' di sicuro?»  ⛔ Si', ed e' **il giro
di PRIMA**: il server della fase 1 il blocco ce l'ha, misurato, e questo banco
**deve vederlo**.  Un giro «prima» che non trovasse la pausa non proverebbe
che il server e' sano: proverebbe che questo file non sa misurare — e
qualunque «dopo» verde sarebbe la peggiore delle prove (`CODER.md` §4.6).

⇒ **L'atteso, scritto prima del giro** (e ripetuto da `--previsione`):

  | | PRIMA (fase 1) | DOPO (la cura) |
  |---|---|---|
  | il picco della marca durante la finestra | ⛔ **≥ 900 ms**, e vicino al tempo che PAM si prende (1,0-2,2 s) | ⭐ **< 150 ms**, cioe' l'ordine di grandezza del ciclo tranquillo |
  | il tempo fermo di A (somma degli scarti) | ⛔ ≈ la durata di PAM | ⭐ ≈ 0 |
  | la stretta di mano di B | ⛔ **≥ 900 ms** | ⭐ **< 300 ms** |
  | ⚠ il tempo di C (chi si autentica) | 1,0-2,2 s | ⭐ **UGUALE**, e va bene cosi' |

⛔ **E il caso opposto, cioe' che aspetto avrebbe una cura che NON funziona**:
   il picco della marca resta ≥ 900 ms e la stretta di B resta ≥ 900 ms,
   **mentre il tempo di C non cambia** — cioe' esattamente la stessa
   fotografia del «prima», con il codice nuovo dentro.  ⭐ E' il caso che
   `--guasto` di `02-pam-lancia.sh` innesta apposta, e che questo banco DEVE
   colorare di rosso.

===========================================================================
⛔ CHE COSA QUESTO BANCO **NON** MISURA, perche' non se ne appropri nessuno

  · il secondo fisso di §4.4-bis e il ban dell'indirizzo: sono **di B8**, e
    questo file non li giudica.  ⚠ Li OSSERVA soltanto quel tanto che serve a
    buttare i campioni sporchi (il motivo `0x08`);
  · la correttezza di PAM: se `prova` non entra, questo banco si ferma e lo
    dice — ⛔ non prosegue misurando una scena in cui A non e' dentro, che
    darebbe un numero verde perche' non c'era niente da bloccare (E1).

===========================================================================
⛔ LO ZERO E IL FALLIMENTO SONO DUE COSE DIVERSE (`REVIEWER.md` §1 punto 4)

Ogni esito porta `valido: true//false` e, quando e' falso, **perche'**.  Un
giro che non ha potuto misurare non scrive «0 ms»: scrive che non ha misurato.
"""
import argparse
import asyncio
import json
import os
import socket
import ssl
import statistics
import struct
import sys
import time
from contextlib import AsyncExitStack

# ⛔ L'IMPORT E' DENTRO UN `try`, E NON PER INDULGENZA — `--previsione` deve
#    poter girare sulla macchina dei documenti, dove `aioquic` non c'e'.  ⚠ Ma
#    «la libreria non c'e'» NON diventa «il giro e' andato»: senza `aioquic`
#    qualunque giro vero si ferma con un messaggio che nomina la libreria,
#    invece di una traccia che nomina una riga a caso.
try:
    from aioquic.asyncio import connect
    from aioquic.asyncio.protocol import QuicConnectionProtocol
    from aioquic.h3.connection import H3_ALPN, H3Connection
    from aioquic.h3.events import HeadersReceived
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.quic.events import QuicEvent
    AIOQUIC = None
except ImportError as _e:            # noqa: N816
    AIOQUIC = str(_e)
    QuicConnectionProtocol = object
    QuicEvent = object

T = {"CIAO": 0x0001, "ECCOMI": 0x0002, "CREDENZIALI": 0x0003, "AMMESSO": 0x0004,
     "RESPINTO": 0x0005, "ATTACCA": 0x0006, "SESSIONE": 0x0007, "CONGEDO": 0x000C,
     "BANCO_MARCA": 0x000F, "BANCO_ESITO": 0x0010}
NOME = {v: k for k, v in T.items()}
MOTIVI = {0x01: "CHIUSO_DALL_UTENTE", 0x07: "CREDENZIALI_ERRATE",
          0x08: "TROPPI_TENTATIVI", 0x09: "NIENTE_IN_COMUNE",
          0x0A: "VERSIONE_INCOMPATIBILE", 0x0B: "ERRORE_PROTOCOLLO",
          0x0C: "SERVER_IN_CHIUSURA", 0x0D: "TEMPO_SCADUTO",
          0x0E: "SESSIONE_NON_SERVIBILE", 0x0F: "GIA_ATTIVA_REMOTA"}

# ⛔ Le soglie stanno QUI, in cima e con un nome, perche' l'atteso non si
#    aggiusti a giro finito.  Sono quelle scritte nel riquadro sopra.
PICCO_BLOCCATO_MS = 900.0   # sopra: il ciclo si e' fermato (il «prima»)
PICCO_LIBERO_MS = 150.0     # sotto: il ciclo non si e' fermato (il «dopo»)
STRETTA_LIBERA_MS = 300.0
BASE_MAX_MS = 60.0          # il ciclo tranquillo: sopra, il righello e' rotto


def s(t):
    b = t.encode("utf-8") if isinstance(t, str) else t
    return struct.pack("!H", len(b)) + b


def inquadra(tipo, corpo):
    return struct.pack("!HI", tipo, len(corpo)) + corpo


def corpo_ciao():
    voci = [("video.codec", "hevc,av1"), ("video.profondita", "8,10"),
            ("audio.codec", "opus,pcm"), ("video.livello", "5.1"),
            ("video.misura_massima", "3840x2160"), ("appunti.testo", "si"),
            ("input.tocco", "no"), ("client.nome", "02-pam-fermo 0.1.0")]
    out = struct.pack("!HH", 1, len(voci))
    for n, v in voci:
        out += s(n) + s(v)
    return out


class Caduta(RuntimeError):
    pass


class Cliente(QuicConnectionProtocol):
    """⚠ Scritto guardando `RCP.md`, non `src/rcp.c`: due programmi che vanno
    d'accordo perche' li ha scritti la stessa mano non confermano niente
    (`PIANO.md` §1.1).  ⛔ Quel che qui e' copiato da `01-b3-cliente.py` sono le
    DUE trappole di `aioquic` gia' pagate il 10 agosto 2026, e sono copiate
    apposta: non passare al suo strato H3 gli eventi degli stream WebTransport,
    e non leggere lo `0` come «nessuno stream»."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._http = H3Connection(self._quic, enable_webtransport=True)
        self.accettata = asyncio.get_event_loop().create_future()
        self.sessione = None
        self.controllo = None
        self.arrivati = bytearray()
        self.messaggi = asyncio.Queue()
        self.caduta = None

    def _cade(self, perche):
        if self.caduta is None:
            self.caduta = perche
            self.messaggi.put_nowait(None)

    def apri_sessione(self, autorita, percorso):
        sid = self._quic.get_next_available_stream_id(is_unidirectional=False)
        self.sessione = sid
        self._http.send_headers(sid, [
            (b":method", b"CONNECT"), (b":protocol", b"webtransport"),
            (b":scheme", b"https"), (b":authority", autorita.encode()),
            (b":path", percorso.encode()),
            (b"origin", f"https://{autorita}".encode()),
        ])
        self.transmit()

    def apri_controllo(self):
        self.controllo = self._http.create_webtransport_stream(
            self.sessione, is_unidirectional=False)
        return self.controllo

    def manda(self, dati):
        self._quic.send_stream_data(self.controllo, dati, end_stream=False)
        self.transmit()

    def quic_event_received(self, event: QuicEvent) -> None:
        nome = type(event).__name__
        if nome == "ConnectionTerminated":
            self._cade(f"connessione TERMINATA: codice "
                       f"{getattr(event, 'error_code', '?')}")
            return
        if nome == "StreamDataReceived" and event.stream_id == self.controllo:
            # ⛔ E NON si passa allo strato H3 di aioquic: lo leggerebbe come un
            #    frame DATA e ucciderebbe la connessione (`[M]` 10 agosto 2026).
            self.arrivati += event.data
            while len(self.arrivati) >= 6:
                tipo, lung = struct.unpack("!HI", self.arrivati[:6])
                if len(self.arrivati) < 6 + lung:
                    break
                corpo = bytes(self.arrivati[6:6 + lung])
                del self.arrivati[:6 + lung]
                self.messaggi.put_nowait((tipo, corpo))
            if event.end_stream:
                self._cade("il canale di controllo si e' chiuso")
            return
        if nome == "StreamDataReceived" and event.stream_id == self.sessione:
            if event.end_stream:
                self._cade("la sessione WebTransport si e' chiusa")
        for ev in self._http.handle_event(event):
            if isinstance(ev, HeadersReceived) and not self.accettata.done():
                self.accettata.set_result(
                    dict(ev.headers).get(b":status", b"?").decode())


async def attendi(cli, quale, attesa=25.0):
    """Aspetta UN messaggio e pretende che sia quello. Restituisce (nome, corpo).

    ⛔ Un `CONGEDO` o un `RESPINTO` non sono «un altro messaggio»: sono la
       misura, e vanno nominati con il loro motivo o la diagnosi punta sul
       nulla."""
    m = await asyncio.wait_for(cli.messaggi.get(), timeout=attesa)
    if m is None:
        raise Caduta(f"la sessione e' caduta: {cli.caduta}")
    tipo, corpo = m
    nome = NOME.get(tipo, f"{tipo:#06x}")
    if quale and nome != quale:
        motivo = corpo[0] if corpo else 0
        if nome in ("CONGEDO", "RESPINTO"):
            raise Caduta(f"{nome} invece di {quale}: motivo {motivo:#04x} = "
                         f"{MOTIVI.get(motivo, '?')}")
        raise Caduta(f"atteso {quale}, arrivato {nome}")
    return nome, corpo


async def apri(pila, indirizzo, porta, percorso):
    """Apre QUIC + la sessione WebTransport + il canale di controllo."""
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{indirizzo}:{porta}"
    cli = await pila.enter_async_context(
        connect(indirizzo, porta, configuration=conf, create_protocol=Cliente))
    await asyncio.wait_for(cli.wait_connected(), timeout=10)
    cli.apri_sessione(autorita, percorso)
    stato = await asyncio.wait_for(cli.accettata, timeout=10)
    if stato != "200":
        raise Caduta(f"la CONNECT estesa ha risposto {stato}, non 200")
    cli.apri_controllo()
    return cli


async def fino_a_eccomi(cli):
    cli.manda(inquadra(T["CIAO"], corpo_ciao()))
    await attendi(cli, "ECCOMI")


async def fino_a_sessione(cli, utente, parola, larghezza=1920, altezza=1080):
    await fino_a_eccomi(cli)
    cli.manda(inquadra(T["CREDENZIALI"], s(utente) + s(parola)))
    t0 = time.monotonic()
    await attendi(cli, "AMMESSO", attesa=30)
    ms_ammesso = (time.monotonic() - t0) * 1000
    cli.manda(inquadra(T["ATTACCA"],
                       struct.pack("!IIII", larghezza, altezza, larghezza,
                                   altezza) + s("it")))
    await attendi(cli, "SESSIONE")
    return ms_ammesso


# ---------------------------------------------------------------------------
# ⛔ IL RIGHELLO: `BANCO_MARCA` -> `BANCO_ESITO`, e si cronometra il ritorno.
#
# §7.5 regola 2: con la funzione di banco SPENTA il server DEVE rispondere
# `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)` — «non deve tacere e non deve
# chiudere».  ⭐ E' quel che rende questo messaggio un righello utilizzabile: la
# risposta arriva sempre, non cambia stato, e non dipinge niente sul desktop di
# nessuno (la funzione e' spenta, invariante I6).
async def sonda(cli, periodo, ferma, campioni):
    n = 0
    while not ferma.is_set():
        n += 1
        t0 = time.monotonic()
        cli.manda(inquadra(T["BANCO_MARCA"], struct.pack("!III", n, 0x00FF00FF, 0)))
        try:
            _, corpo = await attendi(cli, "BANCO_ESITO", attesa=30)
        except (Caduta, asyncio.TimeoutError) as e:
            campioni.append({"n": n, "t0": t0, "ms": None, "caduta": str(e)})
            return
        t1 = time.monotonic()
        # ⛔ Si guarda che l'esito sia DELLA MARCA MANDATA: un righello che
        #    accoppiasse una risposta col cronometro sbagliato misurerebbe
        #    numeri veri di un'altra domanda.
        eco = struct.unpack("!I", corpo[:4])[0] if len(corpo) >= 4 else 0
        campioni.append({"n": n, "t0": t0, "ms": (t1 - t0) * 1000,
                         "eco": eco, "combacia": eco == n})
        resto = periodo - (t1 - t0)
        if resto > 0:
            await asyncio.sleep(resto)


async def stretta_cronometrata(pila, indirizzo, porta, percorso, fuori):
    """La connessione B: da zero a `ECCOMI`, cronometrata."""
    t0 = time.monotonic()
    try:
        cli = await apri(pila, indirizzo, porta, percorso)
        await fino_a_eccomi(cli)
        fuori["ms"] = (time.monotonic() - t0) * 1000
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        fuori["ms"] = None
        fuori["caduta"] = f"{type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
def sblocca(percorso, indirizzo):
    """§4.4-bis, il comando di sblocco. ⛔ E si DICHIARA sempre: «il ban non e'
    scattato» e «qualcuno l'ha tolto» hanno lo stesso aspetto (regola B0.3).

    ⚠ Qui lo sblocco non e' mai un attrezzo per far passare una misura: questo
      banco NON prova il ban.  Serve a portare l'indirizzo a uno stato NOTO
      prima di cominciare, e a non lasciare il campo sporco a chi viene dopo."""
    if not percorso:
        return "nessun socket dichiarato: NON ho sbloccato, e non e' «era libero»"
    try:
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        c.settimeout(5)
        c.connect(percorso)
        c.sendall(f"SBLOCCA {indirizzo}\n".encode())
        r = c.recv(256).decode(errors="replace").strip()
        c.close()
        return r or "(risposta vuota)"
    except OSError as e:
        return f"⛔ non ho parlato con nessuno: {e}"


def ping(percorso):
    """⛔ Il denominatore dello sblocco (regola B0.3): senza, «il ban non c'era»
    e «lo sblocco non e' mai arrivato a nessuno» hanno la stessa faccia."""
    if not percorso:
        return "—"
    try:
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        c.settimeout(5)
        c.connect(percorso)
        c.sendall(b"PING\n")
        r = c.recv(64).decode(errors="replace").strip()
        c.close()
        return r or "(vuota)"
    except OSError as e:
        return f"⛔ {e}"


# ---------------------------------------------------------------------------
async def un_giro(a, parola, n):
    esito = {"giro": n, "valido": False, "perche": None}
    async with AsyncExitStack() as pila:
        # ── A: gia' dentro ────────────────────────────────────────────────
        A = await apri(pila, a.indirizzo, a.porta, a.percorso)
        esito["ms_ammesso_A"] = await fino_a_sessione(A, a.utente, parola)

        campioni = []
        ferma = asyncio.Event()
        righello = asyncio.create_task(sonda(A, a.periodo, ferma, campioni))

        # ── il ciclo tranquillo: il denominatore ──────────────────────────
        await asyncio.sleep(a.tranquillo)
        base = [c["ms"] for c in campioni if c.get("ms") is not None]
        if len(base) < 5:
            ferma.set()
            await righello
            esito["perche"] = (f"solo {len(base)} marche a ciclo tranquillo: il "
                               f"righello non ha misurato niente")
            return esito
        esito["base_mediana_ms"] = statistics.median(base)
        esito["base_n"] = len(base)
        quante_prima = len(campioni)

        # ── C: le credenziali sbagliate, e B nello stesso istante ─────────
        C = await apri(pila, a.indirizzo, a.porta, a.percorso)
        await fino_a_eccomi(C)

        b_fuori = {}
        t_cred = time.monotonic()
        C.manda(inquadra(T["CREDENZIALI"], s(a.utente_cattivo) + s(a.parola_cattiva)))
        seconda = asyncio.create_task(
            stretta_cronometrata(pila, a.indirizzo, a.porta, a.percorso, b_fuori))

        try:
            nome_C, corpo = await attendi(C, None, attesa=40)
            t_resp = time.monotonic()
        except (Caduta, asyncio.TimeoutError) as e:
            ferma.set()
            await righello
            await seconda
            esito["perche"] = f"C non ha ricevuto risposta: {e}"
            return esito
        await seconda

        motivo = corpo[0] if corpo else 0
        esito["risposta_C"] = nome_C
        esito["motivo_C"] = motivo
        esito["motivo_C_nome"] = MOTIVI.get(motivo, "?")
        esito["ms_C"] = (t_resp - t_cred) * 1000

        # ── la coda: si continua a sondare dopo la finestra ───────────────
        await asyncio.sleep(a.coda)
        ferma.set()
        await righello

        # ⛔ IL CAMPIONE SPORCO SI BUTTA, E SI DICE PERCHE'.
        if nome_C != "RESPINTO":
            esito["perche"] = (
                f"a CREDENZIALI sbagliate il server ha risposto «{nome_C}», non "
                f"RESPINTO: la scena non e' quella dichiarata")
            return esito
        if motivo != 0x07:
            esito["perche"] = (
                f"il RESPINTO porta {motivo:#04x} = {MOTIVI.get(motivo, '?')}, "
                f"non 0x07 CREDENZIALI_ERRATE: ⛔ con {MOTIVI.get(motivo, '?')} "
                f"il server rifiuta SENZA interrogare PAM (§4.4-bis), cioe' la "
                f"cosa lenta non e' avvenuta e non c'era niente da bloccare")
            return esito

        # ── il conto ──────────────────────────────────────────────────────
        # La finestra: le marche PARTITE fra il `CREDENZIALI` e il `RESPINTO`.
        dentro = [c for c in campioni[quante_prima:]
                  if c.get("ms") is not None and t_cred <= c["t0"] <= t_resp]
        # ⚠ E anche la marca partita PRIMA e tornata DOPO: e' proprio quella
        #   che il blocco si mangia, ed escluderla sarebbe misurare tutto
        #   tranne il fatto (`LEZIONI.md` §1.9).
        a_cavallo = [c for c in campioni
                     if c.get("ms") is not None and c["t0"] < t_cred
                     and c["t0"] + c["ms"] / 1000 > t_cred]
        finestra = a_cavallo + dentro
        if not finestra:
            esito["perche"] = ("nessuna marca e' partita dentro la finestra: la "
                               "finestra e' durata "
                               f"{esito['ms_C']:.0f} ms e il periodo e' "
                               f"{a.periodo * 1000:.0f} ms")
            return esito

        picco = max(c["ms"] for c in finestra)
        fermo = sum(max(0.0, c["ms"] - esito["base_mediana_ms"]) for c in finestra)
        esito.update({
            "valido": True,
            "n_finestra": len(finestra),
            "picco_ms": picco,
            "fermo_ms": fermo,
            "ms_stretta_B": b_fuori.get("ms"),
            "caduta_B": b_fuori.get("caduta"),
            "marche_scombinate": sum(1 for c in campioni
                                     if c.get("combacia") is False),
        })
        return esito


def previsione():
    print("""
== ⛔ L'ATTESO, SCRITTO PRIMA DEL GIRO  (02-pam-fermo.py)

   La cosa misurata:  quanto sta fermo chi NON si sta autenticando, mentre
                      un terzo presenta credenziali SBAGLIATE.

   | | PRIMA (fase 1, PAM sul filo unico) | DOPO (la cura) |
   |---|---|---|
   | picco della marca in finestra | ⛔ >= %.0f ms   | ⭐ < %.0f ms |
   | tempo fermo di A (somma scarti)| ⛔ ~ la durata di PAM | ⭐ ~ 0 |
   | stretta di mano di B           | ⛔ >= %.0f ms   | ⭐ < %.0f ms |
   | ⚠ tempo di C (chi si autentica)| 1000-2200 ms | ⭐ UGUALE |

   ⛔ IL CASO OPPOSTO — che aspetto avrebbe una cura che NON funziona:
      picco e stretta restano >= %.0f ms **mentre il tempo di C non cambia**,
      cioe' la stessa fotografia del «prima» con il codice nuovo dentro.
      E' quel che `02-pam-lancia.sh --guasto` innesta apposta.

   ⛔ E se il ciclo tranquillo (la mediana di base) fosse sopra %.0f ms, il
      righello e' rotto e NON si divide per lui: il giro si dichiara non valido.
""" % (PICCO_BLOCCATO_MS, PICCO_LIBERO_MS, PICCO_BLOCCATO_MS,
       STRETTA_LIBERA_MS, PICCO_BLOCCATO_MS, BASE_MAX_MS))


async def principale(a, parola):
    print(f"== 02-pam-fermo — https://{a.indirizzo}:{a.porta}{a.percorso}"
          f"  ·  {a.giri} giri  ·  attesa «{a.attesa}»")
    print(f"   PING al socket di comando: {ping(a.socket)}")
    print(f"   ⚠ sblocco DICHIARATO, prima di cominciare: "
          f"{sblocca(a.socket, a.indirizzo)}")
    print(f"   ⚠ e per l'altro indirizzo con cui questa macchina si vede: "
          f"{sblocca(a.socket, '127.0.0.1')}")

    esiti = []
    for n in range(1, a.giri + 1):
        try:
            e = await un_giro(a, parola, n)
        except Exception as ex:  # noqa: BLE001
            e = {"giro": n, "valido": False,
                 "perche": f"{type(ex).__name__}: {ex}"}
        e["quando"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        e["attesa"] = a.attesa
        e["porta"] = a.porta
        esiti.append(e)
        if e["valido"]:
            b = e["ms_stretta_B"]
            quanto_b = (f"{b:.0f} ms" if b is not None
                        else f"CADUTA ({e.get('caduta_B')})")
            print(f"   giro {n}: base {e['base_mediana_ms']:.1f} ms · "
                  f"⛔ picco {e['picco_ms']:.0f} ms · fermo {e['fermo_ms']:.0f} ms · "
                  f"stretta B {quanto_b}")
            print(f"            e chi si autenticava (C): {e['ms_C']:.0f} ms "
                  f"[{e['motivo_C_nome']}]  ·  A era entrato in "
                  f"{e['ms_ammesso_A']:.0f} ms")
        else:
            print(f"   giro {n}: ⛔ NON VALIDO — {e['perche']}")
        # ⛔ Fra un giro e l'altro si lascia respirare: A si stacca e il posto
        #    (§8.2 motivo 0x0F, invariante I2) dev'essere libero per il giro dopo.
        await asyncio.sleep(1.0)

    buoni = [e for e in esiti if e["valido"]]
    print(f"\n== il conto: {len(buoni)} giri validi su {len(esiti)}")
    if not buoni:
        print("   ⛔ NIENTE DA CONCLUDERE: nessun giro valido.  ⚠ Non e' «zero "
              "millisecondi»: e' «non ho misurato» (`LEZIONI.md` §1.9).")
        scrivi(a, esiti, None)
        return 3

    picchi = sorted(e["picco_ms"] for e in buoni)
    fermi = sorted(e["fermo_ms"] for e in buoni)
    strette = sorted(e["ms_stretta_B"] for e in buoni
                     if e["ms_stretta_B"] is not None)
    cc = sorted(e["ms_C"] for e in buoni)
    basi = sorted(e["base_mediana_ms"] for e in buoni)
    riassunto = {
        "giri_validi": len(buoni), "giri": len(esiti),
        "base_mediana_ms": statistics.median(basi),
        "picco_mediana_ms": statistics.median(picchi),
        "picco_massimo_ms": picchi[-1],
        "fermo_mediana_ms": statistics.median(fermi),
        "stretta_B_mediana_ms": statistics.median(strette) if strette else None,
        "C_mediana_ms": statistics.median(cc),
        "attesa": a.attesa,
    }
    print(f"   ciclo tranquillo (base)      mediana {riassunto['base_mediana_ms']:8.1f} ms")
    print(f"   ⛔ picco della marca         mediana {riassunto['picco_mediana_ms']:8.1f} ms"
          f"   (massimo {riassunto['picco_massimo_ms']:.0f})")
    print(f"   ⛔ tempo fermo di A          mediana {riassunto['fermo_mediana_ms']:8.1f} ms")
    if strette:
        print(f"   ⛔ stretta di mano di B      mediana {riassunto['stretta_B_mediana_ms']:8.1f} ms")
    print(f"   ⚠ chi si autenticava (C)     mediana {riassunto['C_mediana_ms']:8.1f} ms"
          f"   ← ⭐ questo NON deve cambiare")

    # ── il verdetto, contro l'atteso scritto prima ────────────────────────
    verdetto = 0
    if riassunto["base_mediana_ms"] > BASE_MAX_MS:
        print(f"\n   ⛔ IL RIGHELLO E' ROTTO: il ciclo tranquillo misura "
              f"{riassunto['base_mediana_ms']:.0f} ms, sopra i {BASE_MAX_MS:.0f} "
              f"attesi.  Nessun confronto e' leggibile.")
        verdetto = 3
    elif a.attesa == "bloccato":
        ok = (riassunto["picco_mediana_ms"] >= PICCO_BLOCCATO_MS)
        print(f"\n   {'⭐ OK' if ok else '⛔ NO'}  atteso «bloccato»: il picco "
              f"doveva essere >= {PICCO_BLOCCATO_MS:.0f} ms ed e' "
              f"{riassunto['picco_mediana_ms']:.0f}")
        if not ok:
            print("      ⛔ E NON E' UNA BUONA NOTIZIA: vuol dire che questo "
                  "banco NON SA VEDERE il blocco che il server ha davvero.\n"
                  "         Un «dopo» verde misurato con un righello cieco e' "
                  "la peggiore delle prove (`CODER.md` §4.6).")
        verdetto = 0 if ok else 1
    elif a.attesa == "libero":
        ok = (riassunto["picco_mediana_ms"] < PICCO_LIBERO_MS)
        ok_b = bool(strette) and riassunto["stretta_B_mediana_ms"] < STRETTA_LIBERA_MS
        print(f"\n   {'⭐ OK' if ok else '⛔ NO'}  atteso «libero»: il picco "
              f"doveva essere < {PICCO_LIBERO_MS:.0f} ms ed e' "
              f"{riassunto['picco_mediana_ms']:.0f}")
        if strette:
            print(f"   {'⭐ OK' if ok_b else '⛔ NO'}  e la stretta di B < "
                  f"{STRETTA_LIBERA_MS:.0f} ms: e' "
                  f"{riassunto['stretta_B_mediana_ms']:.0f}")
        else:
            print("   ⛔ NO  nessuna stretta di B misurata: non e' «e' stata "
                  "veloce», e' «non ho misurato»")
        verdetto = 0 if (ok and ok_b) else 1
    else:
        print("\n   ⚠ nessun atteso dichiarato (--attesa): il giro misura e non "
              "giudica")

    scrivi(a, esiti, riassunto)
    return verdetto


def scrivi(a, esiti, riassunto):
    if not a.esiti:
        return
    riga = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "macchina": os.uname().nodename,
            "scena": {"porta": a.porta, "indirizzo": a.indirizzo,
                      "utente": a.utente, "utente_cattivo": a.utente_cattivo,
                      "periodo_ms": a.periodo * 1000,
                      "tranquillo_s": a.tranquillo, "coda_s": a.coda},
            "attesa": a.attesa, "giri": esiti, "riassunto": riassunto,
            "nota": a.nota}
    with open(a.esiti, "a", encoding="utf-8") as f:
        f.write(json.dumps(riga, ensure_ascii=False) + "\n")
    print(f"   esiti: {a.esiti}")


def parola_dal_file(percorso):
    """⛔ D12: la parola d'ordine non passa dalla riga di comando —
    `/proc/<pid>/cmdline` la legge chiunque."""
    try:
        modo = os.stat(percorso).st_mode & 0o077
    except OSError as e:
        print(f"   ⛔ il file della parola «{percorso}» non si legge: {e}")
        sys.exit(2)
    if modo:
        print(f"   ⚠ «{percorso}» e' leggibile da altri (bit {modo:o})")
    with open(percorso, encoding="utf-8") as f:
        parola = f.read().strip("\n")
    if not parola:
        print(f"   ⛔ «{percorso}» e' VUOTO: non e' «la parola e' vuota», e' "
              f"«il lanciatore non l'ha scritta»")
        sys.exit(2)
    return parola


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="quanto sta fermo chi NON si sta autenticando")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7531)
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola-file", default="")
    p.add_argument("--utente-cattivo", default="prova2")
    p.add_argument("--parola-cattiva", default="questa-non-e-la-parola-giusta")
    p.add_argument("--socket", default="")
    p.add_argument("--giri", type=int, default=5)
    p.add_argument("--periodo", type=float, default=0.05,
                   help="ogni quanto parte una marca, in secondi")
    p.add_argument("--tranquillo", type=float, default=1.2,
                   help="quanto si sonda a ciclo fermo, per il denominatore")
    p.add_argument("--coda", type=float, default=0.7)
    p.add_argument("--attesa", choices=["bloccato", "libero", "nessuna"],
                   default="nessuna",
                   help="l'atteso, DICHIARATO PRIMA del giro")
    p.add_argument("--esiti", default="")
    p.add_argument("--nota", default="")
    p.add_argument("--previsione", action="store_true")
    a = p.parse_args()
    if a.previsione:
        previsione()
        sys.exit(0)
    if AIOQUIC:
        print(f"   ⛔ «aioquic» non c'e' su questa macchina ({AIOQUIC}): questo "
              f"banco gira DENTRO il contenitore di NIC-OS.\n"
              f"      ⚠ Non e' «il giro e' andato»: e' «non ho misurato».")
        sys.exit(2)
    if not a.parola_file:
        print("   ⛔ serve --parola-file (D12: la parola non passa da argv)")
        sys.exit(2)
    parola = parola_dal_file(a.parola_file)
    try:
        sys.exit(asyncio.run(principale(a, parola)))
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        print(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
