#!/usr/bin/env python3
"""06-b40-specchio.py — ⭐ uno SPECCHIO di RCP in locale, per far girare il
                        cliente di prova SUL SERIO senza la macchina di prova.

    python3 06-b40-specchio.py --porta 7742 [--guasto NOME] [--certificati DIR]

---------------------------------------------------------------------------
⛔⛔ CHE COSA QUESTO PROGRAMMA **NON** E', E VA LETTO PRIMA DI GUARDARE UN VERDE

   ⛔ **NON e' il prodotto**, e nessun verde preso qui dice niente sul
      prodotto.  Il server e' in C (`DECISIONI.md` §6.3); questo e' Python, e
      risponde le stesse cose sempre.  Un `TELA(ADATTATA, 1264x800)` di qui
      NON tocca nessun palco: e' la trappola gia' pagata di
      `fasi/06-la-tela-e-la-vista.md` §7.2 — *«un server che rispondesse
      `TELA(ADATTATA)` senza toccare il palco passerebbe tutti e cinque i
      giri»* — ⭐ **e qui e' letteralmente vera per costruzione**;

   ⛔ **NON e' un secondo lettore di `RCP.md`**: le sue risposte sono state
      copiate dai corpi di `01-b4-registrazioni.py`, quindi non conferma
      nessuna lettura della specifica.  Il secondo lettore e' il CLIENTE
      (`01-b3-cliente.py`, `PIANO.md` §1.1), ed e' quello che qui si esercita.

⭐ **Che cosa allora prova.**  Una cosa sola, e nessun altro banco la prova:

      il cliente di prova, con `aioquic` VERO, su una connessione QUIC VERA,
      arriva in fondo alla stretta di mano e alla strada della tela, e la
      registrazione che ne esce l'arbitro la sa giudicare.

   Fino al 21 agosto 2026 quella catena si poteva esercitare **solo** sulla
   macchina di prova, e sul portatile `01-b3-cliente.py` girava soltanto con i
   surrogati di `06-b38-registratore.py` — cioe' con `aioquic` FINTO, il
   `QuicConnectionProtocol` sostituito da una classe vuota e **nessun byte che
   passa da una socket**.  ⚠ Con i surrogati il registratore si prova; il
   cliente no.

---------------------------------------------------------------------------
⛔ E IL CONTROLLO POSITIVO STA QUI DENTRO, non a fianco

Uno specchio che dice sempre la cosa giusta e' uno strumento non certificato
(`LEZIONI.md` §1.9).  ⇒ `--guasto` gli fa dire, **una cosa sbagliata per
volta**, e ogni guasto dichiara PRIMA chi lo deve vedere: il **cliente** (con
il suo codice d'uscita) o l'**arbitro** (con la regola e il byte).

  sano                  nessuno accusa niente        cliente 0 · arbitro 0
  ammesso-subito        AMMESSO senza il secondo     ⇒ lo vede il CLIENTE (1)
  tela-muta             nessun TELA all'ADATTA_TELA  ⇒ lo vede il CLIENTE (5)
  tela-non-sollecitata  un TELA che nessuno ha chiesto ⇒ l'ARBITRO, T1 §7.1
  tela-dispari          TELA(ADATTATA) con lato dispari ⇒ l'ARBITRO, T6 §4.5
  tela-oltre-massima    concede oltre `video.misura_massima` ⇒ l'ARBITRO, §4.5
  tela-dopo-vista       un TELA dopo la VISTA        ⇒ l'ARBITRO, V3 §7.1

⛔ La divisione fra i due non e' cosmetica: un guasto che nessuno dei due
   vedesse sarebbe un buco, e senza dichiarare **chi** lo deve vedere non ci
   si accorgerebbe di averlo.
"""
import argparse
import asyncio
import os
import struct
import sys
import time
from pathlib import Path

from aioquic.asyncio import QuicConnectionProtocol, serve
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import (
    DatagramReceived,
    HeadersReceived,
    WebTransportStreamDataReceived,
)
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import ProtocolNegotiated, QuicEvent

PERCORSO = "/rcp/1"

T_CIAO, T_ECCOMI = 0x0001, 0x0002
T_CREDENZIALI, T_AMMESSO, T_RESPINTO = 0x0003, 0x0004, 0x0005
T_ATTACCA, T_SESSIONE = 0x0006, 0x0007
T_VISTA, T_DISPOSIZIONE = 0x0008, 0x0009
T_ADATTA_TELA, T_CONGEDO, T_TELA = 0x000B, 0x000C, 0x000E
T_TERMINA = 0x0011
NOME = {T_CIAO: "CIAO", T_CREDENZIALI: "CREDENZIALI", T_ATTACCA: "ATTACCA",
        T_VISTA: "VISTA", T_DISPOSIZIONE: "DISPOSIZIONE",
        T_ADATTA_TELA: "ADATTA_TELA", T_TERMINA: "TERMINA_SESSIONE"}

GUASTI = ("sano", "ammesso-subito", "tela-muta", "tela-non-sollecitata",
          "tela-dispari", "tela-oltre-massima", "tela-dopo-vista",
          "tela-in-piu")

# §4.5: i limiti sono normativi, e i lati sono pari.
MIN_L, MAX_L, MIN_A, MAX_A = 320, 7680, 240, 4320


def registra(*cose):
    print(*cose, flush=True)


def s(t):
    b = t.encode("utf-8") if isinstance(t, str) else t
    return struct.pack("!H", len(b)) + b


def cap(voci):
    out = struct.pack("!H", len(voci))
    for n, v in voci:
        out += s(n) + s(v)
    return out


def msg(tipo, corpo):
    return struct.pack("!HI", tipo, len(corpo)) + corpo


def tela_msg(esito, motivo, lar, alt):
    return msg(T_TELA, struct.pack("!BBII", esito, motivo, lar, alt))


class Specchio(QuicConnectionProtocol):
    """Un solo client per volta, un solo canale di controllo.  E' quanto basta."""

    guasto = "sano"
    secondo_fisso = 1.05

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._http = None
        self.sessione = None
        self.controllo = None
        self.coda = b""
        self.attaccato = False
        # ⛔ `video.misura_massima` si LEGGE dal CIAO, non si suppone: e' il
        #    numero contro cui §4.5 misura la tela concessa, e supporlo
        #    vorrebbe dire che il guasto `tela-oltre-massima` non e' un guasto
        #    ma un caso qualunque.
        self.max_l, self.max_a = 0, 0
        self.tela = (0, 0)
        self.vista_vista = False

    # ── il giro di HTTP/3 ────────────────────────────────────────────────
    def quic_event_received(self, event: QuicEvent) -> None:
        if isinstance(event, ProtocolNegotiated):
            self._http = H3Connection(self._quic, enable_webtransport=True)
        if self._http is None:
            return
        for ev in self._http.handle_event(event):
            self._gestisci(ev)

    def _gestisci(self, ev) -> None:
        if isinstance(ev, HeadersReceived):
            i = dict(ev.headers)
            metodo = i.get(b":method", b"").decode()
            proto = i.get(b":protocol", b"").decode()
            perc = i.get(b":path", b"").decode()
            if metodo == "CONNECT" and proto == "webtransport" and perc == PERCORSO:
                registra(f"  ⭐ sessione WebTransport accettata su {perc}")
                self._http.send_headers(ev.stream_id, [(b":status", b"200")])
                self.sessione = ev.stream_id
            else:
                registra(f"  ⛔ {metodo} {perc} (:protocol={proto or '-'}) -> 404")
                self._http.send_headers(ev.stream_id, [(b":status", b"404")],
                                        end_stream=True)
            self.transmit()
        elif isinstance(ev, WebTransportStreamDataReceived):
            if self.controllo is None:
                # §4.2: il canale di controllo e' il PRIMO bidirezionale.
                self.controllo = ev.stream_id
                registra(f"  canale di controllo: stream {ev.stream_id}")
            if ev.stream_id != self.controllo:
                return
            self.coda += ev.data
            self._sfoglia()
        elif isinstance(ev, DatagramReceived):
            pass

    def manda(self, dati):
        self._http._quic.send_stream_data(self.controllo, dati, end_stream=False)
        self.transmit()

    def _sfoglia(self):
        while len(self.coda) >= 6:
            tipo, lung = struct.unpack("!HI", self.coda[:6])
            if len(self.coda) < 6 + lung:
                return
            corpo = self.coda[6:6 + lung]
            self.coda = self.coda[6 + lung:]
            registra(f"  ← {NOME.get(tipo, hex(tipo))} ({lung} byte)")
            asyncio.ensure_future(self._risposta(tipo, corpo))

    # ── le risposte ──────────────────────────────────────────────────────
    async def _risposta(self, tipo, corpo):
        if tipo == T_CIAO:
            self._leggi_ciao(corpo)
            self.manda(msg(T_ECCOMI, struct.pack("!H", 1) + cap([
                ("video.codec", "hevc"),
                ("video.profondita", "8,10"),
                ("audio.codec", "opus,pcm"),
                ("appunti.testo", "si"),
                ("banco.marca", "no"),
            ])))
            registra("  → ECCOMI")

        elif tipo == T_CREDENZIALI:
            # ⛔ §4.4-bis: il ritardo fisso vale ANCHE per la risposta
            #    RIUSCITA.  ⚠ Qui e' un `sleep`, non una difesa: lo specchio
            #    non autentica nessuno.  Serve a far esercitare al cliente il
            #    cronometro che nessun altro banco guarda.
            if self.guasto == "ammesso-subito":
                registra("  ⛔ GUASTO «ammesso-subito»: nessuna attesa")
            else:
                await asyncio.sleep(self.secondo_fisso)
            self.manda(msg(T_AMMESSO, b""))
            registra("  → AMMESSO")

        elif tipo == T_ATTACCA:
            lar, alt = struct.unpack("!II", corpo[:8])
            self.tela = self._concedibile(lar, alt)
            self.attaccato = True
            self.manda(msg(T_SESSIONE, struct.pack("!B", 1)
                           + struct.pack("!II", *self.tela) + s("specchio")))
            registra(f"  → SESSIONE tela={self.tela[0]}x{self.tela[1]}")
            if self.guasto == "tela-non-sollecitata":
                # ⛔ E si aspetta un momento, invece di spedirlo subito: mandato
                #    nello stesso istante del SESSIONE, il TELA correrebbe
                #    contro l'`ADATTA_TELA` che il client spedisce all'attacco
                #    (`DECISIONI.md` §5.0-sexies) e finirebbe per fargli da
                #    risposta — cioe' l'arbitro accuserebbe **T2** (§6.2, «un
                #    TELA di troppo») invece di **T1** (§7.1, «spontaneo»), e
                #    il caso proverebbe una regola diversa da quella scritta.
                await asyncio.sleep(0.4)
                registra("  ⛔ GUASTO «tela-non-sollecitata»: un TELA che nessuno "
                         "ha chiesto")
                self.manda(tela_msg(1, 0, 1280, 720))

        elif tipo == T_ADATTA_TELA:
            lar, alt = struct.unpack("!II", corpo[:8])
            if self.guasto == "tela-muta":
                registra("  ⛔ GUASTO «tela-muta»: non rispondo")
                return
            if self.guasto == "tela-dispari":
                registra("  ⛔ GUASTO «tela-dispari»: concedo 1281x800")
                self.manda(tela_msg(1, 0, 1281, 800))
                return
            if self.guasto == "tela-oltre-massima":
                registra("  ⛔ GUASTO «tela-oltre-massima»: concedo 7680x4320")
                self.manda(tela_msg(1, 0, 7680, 4320))
                return
            if not (MIN_L <= lar <= MAX_L and MIN_A <= alt <= MAX_A):
                # §7.1: una richiesta fuori dai limiti e' LECITA, e la risposta
                # e' un rifiuto con il motivo — non una caduta.
                registra(f"  → TELA(RIFIUTATA, MISURA_FUORI_LIMITI) "
                         f"[{lar}x{alt}]")
                self.manda(tela_msg(2, 2, *self.tela))
                return
            self.tela = self._concedibile(lar, alt)
            registra(f"  → TELA(ADATTATA, {self.tela[0]}x{self.tela[1]})")
            self.manda(tela_msg(1, 0, *self.tela))
            if self.guasto == "tela-in-piu":
                registra("  ⛔ GUASTO «tela-in-piu»: un secondo TELA per la "
                         "stessa ADATTA_TELA")
                self.manda(tela_msg(1, 0, 1280, 720))

        elif tipo == T_VISTA:
            # §7.1: la VISTA non deve far cambiare la tela.  Si tace.
            self.vista_vista = True
            registra("  ·  VISTA presa in nota (nessun TELA: §7.1)")
            if self.guasto == "tela-dopo-vista":
                registra("  ⛔ GUASTO «tela-dopo-vista»: rispondo con un TELA")
                self.manda(tela_msg(1, 0, 1280, 720))

        elif tipo == T_TERMINA:
            registra("  → CONGEDO(0x10 SESSIONE_TERMINATA)")
            self.manda(msg(T_CONGEDO, struct.pack("!B", 0x10) + s("")))

        elif tipo == T_DISPOSIZIONE:
            registra("  ·  DISPOSIZIONE presa in nota")

    def _leggi_ciao(self, corpo):
        try:
            quante = struct.unpack("!H", corpo[2:4])[0]
            i = 4
            for _ in range(quante):
                n = struct.unpack("!H", corpo[i:i + 2])[0]
                nome = corpo[i + 2:i + 2 + n].decode()
                i += 2 + n
                n = struct.unpack("!H", corpo[i:i + 2])[0]
                val = corpo[i + 2:i + 2 + n].decode()
                i += 2 + n
                if nome == "video.misura_massima" and "x" in val:
                    self.max_l, self.max_a = (int(x) for x in val.split("x", 1))
        except Exception as e:                                    # noqa: BLE001
            registra(f"  ⚠ CIAO non interpretabile ({e}): niente misura massima")
        registra(f"  ·  video.misura_massima dichiarata: "
                 f"{self.max_l}x{self.max_a or '?'}")

    def _concedibile(self, lar, alt):
        """§4.5: dentro i limiti, pari, e non oltre quel che il client regge."""
        lar = max(MIN_L, min(lar, MAX_L, self.max_l or MAX_L))
        alt = max(MIN_A, min(alt, MAX_A, self.max_a or MAX_A))
        return (lar - (lar & 1), alt - (alt & 1))


async def principale(a) -> None:
    conf = QuicConfiguration(is_client=False, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    dire = Path(a.certificati)
    conf.load_cert_chain(dire / "sessione.pem", dire / "sessione.key")
    Specchio.guasto = a.guasto
    Specchio.secondo_fisso = a.secondo_fisso
    registra(f"== 06-b40 specchio RCP — UDP {a.porta}{PERCORSO}")
    registra(f"   guasto: {a.guasto}"
             + ("" if a.guasto == "sano" else "   ⛔ NON e' sano, ed e' apposta"))
    registra("   ⛔ NON e' il prodotto: leggi l'intestazione del file.\n")
    await serve("127.0.0.1", a.porta, configuration=conf,
                create_protocol=Specchio)
    await asyncio.Future()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--porta", type=int, default=7742)
    p.add_argument("--guasto", choices=GUASTI, default="sano")
    p.add_argument("--secondo-fisso", type=float, default=1.05)
    p.add_argument("--certificati",
                   default=os.environ.get("CERTIFICATI",
                                          "/media/REMOTIX/b2-certificati"))
    try:
        asyncio.run(principale(p.parse_args()))
    except KeyboardInterrupt:
        registra("\nfermato")
        sys.exit(0)
