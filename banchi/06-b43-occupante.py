#!/usr/bin/env python3
"""06-b43-occupante.py — ⛔ IL CLIENT CHE **OCCUPA IL POSTO** e poi se ne va,
in uno dei quattro modi in cui un client se ne puo' andare.

    python3 06-b43-occupante.py --porta 7801 --utente provar7 \\
            --parola-file /tmp/06-b7/parola --uscita resta --tieni 240 \\
            --etichetta m1 --scena 'GNOME vero, carico 0,2'

⚠ Gira DENTRO il contenitore (`aioquic` sta li'), ma il **diario** lo scrive
  in una cartella condivisa con l'host, perche' chi misura sta fuori.

===========================================================================
⛔ CHE COSA MISURA — e perche' i modi di andarsene sono QUATTRO e non uno
===========================================================================

`SPECIFICHE.md` §5.3 dice *«il client che tace da 30 secondi e' staccato»*, e
`rcp.c:7041` conta da `ultima_vita`, cioe' **dall'ultimo pacchetto QUIC
decifrato e autenticato** — non dall'ultimo byte di RCP.  ⇒ Le due frasi
coincidono solo per un client che, tacendo, **smette anche di rispondere sul
filo**.  Un client vivo che non dice niente ⛔ **continua a rinnovare
`ultima_vita` rispondendo ai PING del server** (`webtransport.c:2027`,
`WT_TIENILA_VIVA_NS` = 10 s), e allora il tetto dei trenta secondi non scatta
mai.  Il codice lo dichiara — `rcp.c:242`: *«un client vivo sul filo ma con la
pagina morta adesso tiene il posto»* — ma nessuno l'aveva misurato.

I quattro modi, e sono quattro FATTI diversi sul filo:

  `congedo`   ⭐ il congedo pulito: `CONGEDO(0x01)` sul canale di controllo,
              poi la connessione si chiude.  E' quel che fa la pagina quando
              l'utente chiude la scheda **bene**.
  `chiusura`  la connessione QUIC si chiude **senza** `CONGEDO`: il client
              manda `CONNECTION_CLOSE` e sparisce.  ⚠ Il server LO SA.
  `resta`     ⛔ il client **non se ne va affatto**: resta appeso, non dice
              niente su RCP, ma il suo stack QUIC continua a riscontrare.
              E' la scheda congelata dal browser (§5.3 la nomina) e la pagina
              morta con il browser vivo.  ⇒ Chi lo ammazza e' il lanciatore,
              e i modi cattivi si producono da fuori:
                · `SIGKILL`  la presa si chiude ⇒ il kernel risponde con ICMP
                             «port unreachable» ai pacchetti del server;
                · `SIGSTOP`  la presa resta aperta e NESSUNO risponde piu' —
                             e' il buco nero, cioe' la rete staccata.
              ⛔ Sono due cose diverse e vanno misurate separate: se ngtcp2
                 reagisse all'ICMP, il primo sarebbe piu' rapido del secondo.

⛔ E il diario si scrive con `time.time_ns()`, l'orologio **della macchina di
   prova** — lo stesso che timbra il registro del server.  Nessun tempo
   attraversa la rete: sarebbe l'errore che rende una misura di secondi
   inservibile.

===========================================================================
⛔ I CODICI D'USCITA
===========================================================================

    0  ha occupato il posto e se n'e' andato come chiesto
    2  non e' mai arrivato a `SESSIONE` (il motivo sta nel diario e nel JSON)
    4  la connessione e' caduta prima del previsto
"""
import argparse
import asyncio
import importlib.util
import json
import os
import ssl
import struct
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _porta(nome, file):
    s = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


fc = _porta("fc", "02-filo-cliente.py")


def dimmi(*a):
    print(*a, flush=True)


class Diario:
    """⛔ Ogni evento con il suo nanosecondo, **subito su disco**.

    ⚠ Non un `print` bufferizzato e non il JSON finale: il lanciatore deve
      poter leggere «sono attaccato» MENTRE questo programma e' ancora vivo, e
      un processo ammazzato con `SIGKILL` non scrive nessun JSON.  ⇒ Quel che
      non e' su disco nell'istante in cui accade, dopo non c'e' piu'.
    """

    def __init__(self, percorso):
        self.percorso = percorso
        with open(percorso, "w", encoding="utf-8") as f:
            f.write("")

    def segna(self, evento, extra=""):
        riga = f"{time.time_ns()} {evento} {extra}".rstrip()
        # ⛔ `O_APPEND` e chiusura immediata: il buffer di Python non
        #    sopravvive a un `SIGKILL`, e questo diario esiste per quello.
        with open(self.percorso, "a", encoding="utf-8") as f:
            f.write(riga + "\n")
            f.flush()
            os.fsync(f.fileno())
        dimmi("   ·", riga)
        return riga


async def principale(a):
    from aioquic.h3.connection import H3_ALPN
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.asyncio import connect
    b3 = fc.carica_b3()
    Cliente = fc.fabbrica_cliente()

    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{a.indirizzo}:{a.porta}"
    os.makedirs(a.lavoro, exist_ok=True)

    d = Diario(os.path.join(a.lavoro, f"{a.etichetta}-diario.txt"))
    d.segna("AVVIO", f"pid={os.getpid()} uscita={a.uscita} tieni={a.tieni}")

    esito = {"banco": "06-b43", "etichetta": a.etichetta,
             "quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "porta": a.porta, "utente": a.utente, "scena": a.scena,
             "uscita": a.uscita, "tieni": a.tieni, "pid": os.getpid(),
             "sessione": None, "congedo": None, "errore": None,
             "attaccato_ns": None, "partito_ns": None, "sockname": None}

    dimmi(f"== 06-b43 occupante «{a.etichetta}» — pid {os.getpid()}")
    dimmi(f"   bersaglio: https://{autorita}{a.percorso}")
    dimmi(f"   scena: {a.scena}")

    codice = 0
    try:
        async with connect(a.indirizzo, a.porta, configuration=conf,
                           create_protocol=Cliente) as cli:
            await asyncio.wait_for(cli.wait_connected(), timeout=8)
            # ⭐ La porta locale UDP: serve a chi vuole staccare la rete con una
            #    regola stretta invece che con l'accetta.
            try:
                esito["sockname"] = list(
                    cli._transport.get_extra_info("sockname"))
            except Exception:      # noqa: BLE001
                esito["sockname"] = None
            d.segna("QUIC_APERTO", f"sockname={esito['sockname']}")

            cli.apri_sessione(autorita, a.percorso)
            stato = await asyncio.wait_for(cli.accettata, timeout=8)
            if stato != "200":
                esito["errore"] = f"CONNECT estesa: :status = {stato}"
                d.segna("ROSSO", esito["errore"])
                return 2
            cli.apri_controllo()
            cli.codec_atteso = a.codec

            try:
                cli.manda(b3.inquadra(b3.T["CIAO"], b3.corpo_ciao()))
                await b3.attendi(cli, "ECCOMI")
                cli.manda(b3.inquadra(b3.T["CREDENZIALI"],
                                      b3.s(a.utente) + b3.s(a.parola)))
                await b3.attendi(cli, "AMMESSO", attesa=25)
                d.segna("AMMESSO")
                cli.manda(b3.inquadra(b3.T["ATTACCA"],
                                      struct.pack("!IIII", a.larghezza,
                                                  a.altezza, a.larghezza,
                                                  a.altezza)
                                      + b3.s(a.disposizione)))
                _, corpo, _ = await b3.attendi(cli, "SESSIONE",
                                               attesa=a.attesa_sessione)
            except Exception as e:   # noqa: BLE001 — il tipo dell'errore E' la misura
                esito["errore"] = f"{type(e).__name__}: {e}"
                esito["congedo"] = str(e)
                d.segna("NON_ATTACCATO", esito["errore"])
                return 2

            lar, alt = struct.unpack("!II", corpo[1:9])
            esito["sessione"] = {"stato": corpo[0], "tela": [lar, alt]}
            esito["attaccato_ns"] = time.time_ns()
            # ⛔ `stato` DOVREBBE essere 1 = NUOVA / 2 = RIPRESA, ⛔ ma
            #    `rcp.c:2589` scrive la costante `1` e il `2` non esce mai:
            #    `[M]` 22 agosto 2026, dodici riattacchi su uno stesso figlio,
            #    stato = 1 dodici volte.  ⇒ Si registra, ma la domanda «il
            #    figlio e' quello di prima?» la risponde `ps`.
            d.segna("ATTACCATO", f"stato={corpo[0]} tela={lar}x{alt}")

            # ⚠ Il canale di input si apre come lo aprirebbe la pagina, e poi
            #   NON ci passa piu' niente: da qui in avanti questo client tace su
            #   RCP.  E' la scena che il tetto dei trenta secondi deve vedere.
            stream = cli._http.create_webtransport_stream(
                cli.sessione, is_unidirectional=True)
            d.segna("CANALE_INPUT", f"stream={stream}")

            # ⛔⭐ UN SOLO TASTO, E NON E' UN ORNAMENTO — `[M]` 22 agosto 2026.
            #
            # Il TERZO orologio di §5.3 — l'abbandono della sessione, 60 minuti
            # — si nutre di `presenza_segna()` (`main.c:508`), e quella
            # funzione ⛔ **e' chiamata da un posto solo**: `input_al_figlio()`,
            # `main.c:552`.  ⇒ Un utente che si attacca e **non tocca mai
            # niente** non entra mai nella tabella `presenti[]`, e l'orologio
            # dell'abbandono **non parte affatto**: la sua sessione grafica non
            # scade mai.
            #
            # ⚠ E' il caso normale di un banco — ci si attacca, si guarda, ci si
            #   stacca — quindi e' anche il modo in cui una macchina di prova si
            #   riempie di desktop immortali da 477 MB l'uno (§5.3 li ha
            #   misurati).
            #
            # ⇒ Questa opzione esiste per **misurare la differenza**: lo stesso
            #   giro con e senza un tasto, e il figlio che muore in un caso e
            #   nell'altro no.  Un caso solo non distinguerebbe «l'orologio non
            #   parte» da «l'orologio non l'ho aspettato abbastanza».
            if a.un_tasto:
                # ⛔ §7.3: l'`id` cresce su TUTTO il canale e comincia da 1 (lo
                #    0 e' riservato), e l'`istante` e' in microsecondi VERI.
                us = int(time.monotonic() * 1_000_000) % (1 << 63)
                idn = 0
                for premuto in (1, 0):
                    idn += 1
                    corpo = (struct.pack("!IQ", idn, us)
                             + struct.pack("!HB", a.un_tasto, premuto))
                    cli._quic.send_stream_data(
                        stream, struct.pack("!HI", 0x0105, len(corpo)) + corpo,
                        end_stream=False)
                    cli.transmit()
                    us += 1000
                    await asyncio.sleep(0.15)
                d.segna("UN_TASTO", f"POSIZIONE_TASTO {a.un_tasto} giu' e su")

            # ---- si tiene il posto -----------------------------------------
            fine = time.monotonic() + a.tieni
            while time.monotonic() < fine:
                if cli.caduta is not None:
                    d.segna("CADUTO", str(cli.caduta))
                    esito["congedo"] = f"caduto: {cli.caduta}"
                    codice = 4
                    break
                await asyncio.sleep(0.25)

            if codice == 0:
                if a.uscita == "congedo":
                    # ⛔ L'istante si segna PRIMA di mandare: quel che si misura
                    #    e' «da quando il client se n'e' andato», e il byte
                    #    parte dopo.
                    esito["partito_ns"] = time.time_ns()
                    d.segna("PARTO_CONGEDO", "0x01 CHIUSO_DALL_UTENTE")
                    cli.manda(b3.inquadra(b3.T["CONGEDO"],
                                          struct.pack("!B", 0x01)
                                          + b3.s("banco 06-b43")))
                    await asyncio.sleep(0.5)
                elif a.uscita == "chiusura":
                    esito["partito_ns"] = time.time_ns()
                    d.segna("PARTO_CHIUSURA", "CONNECTION_CLOSE, senza CONGEDO")
                else:
                    # `resta`: la finestra e' finita e nessuno mi ha ammazzato.
                    d.segna("TIENI_SCADUTO",
                            "⚠ nessuno mi ha ammazzato: il lanciatore e' in "
                            "ritardo, o la misura e' piu' lunga di --tieni")
    except Exception as e:   # noqa: BLE001 — il tipo dell'errore E' la misura
        esito["errore"] = f"{type(e).__name__}: {e}"
        d.segna("ECCEZIONE", esito["errore"])
        codice = codice or 2

    esito["finito_ns"] = time.time_ns()
    percorso = os.path.join(a.lavoro, f"{a.etichetta}-occupante.json")
    with open(percorso, "w", encoding="utf-8") as f:
        json.dump(esito, f, ensure_ascii=False, indent=1)
    dimmi(f"   esito: {percorso}")
    return codice


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="06-b43 — il client che occupa il posto e se ne va")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7801)
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default="provar7")
    p.add_argument("--parola", default="")
    p.add_argument("--parola-file", default="")
    p.add_argument("--larghezza", type=int, default=1280)
    p.add_argument("--altezza", type=int, default=800)
    p.add_argument("--disposizione", default="it")
    p.add_argument("--codec", type=int, default=1)
    p.add_argument("--uscita", choices=["resta", "congedo", "chiusura"],
                   default="resta")
    p.add_argument("--tieni", type=float, default=240.0,
                   help="quanto si tiene il posto prima di uscire (s)")
    p.add_argument("--un-tasto", type=int, default=0,
                   help="⛔ manda UN tasto (codice evdev, 30 = «a») subito dopo "
                        "SESSIONE, e poi tace: e' l'unico modo di far partire "
                        "l'orologio dell'abbandono (main.c:552)")
    p.add_argument("--attesa-sessione", type=float, default=90.0,
                   help="⚠ largo: il figlio deve nascere e agganciare il palco")
    p.add_argument("--lavoro", default="/tmp/06-b7")
    p.add_argument("--etichetta", default="occupante")
    p.add_argument("--scena", default="(non dichiarata)")
    a = p.parse_args()
    a.parola = fc.parola_dagli_argomenti(a)
    if a.scena == "(non dichiarata)":
        dimmi("⛔ serve --scena (CODER.md §3.2)")
        sys.exit(2)
    try:
        sys.exit(asyncio.run(principale(a)))
    except Exception as e:  # noqa: BLE001
        dimmi(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
