#!/usr/bin/env python3
"""01-b2-sonda-trasporto.py — i parametri di trasporto, letti SUL FILO.

    python3 01-b2-sonda-trasporto.py --porta 7447 --idle-atteso 30000
    python3 01-b2-sonda-trasporto.py --porta 7447 --idle-atteso 10000 --etichetta 'tetto cambiato'

---------------------------------------------------------------------------
⛔ CHE COSA MISURA, E PERCHE' NON BASTAVA QUEL CHE C'ERA

Le proprieta' che `fasi/01-filo-nudo.md` assegna a B2 «perche' sono della
libreria e nessun altro banco le guarda»:

    max_idle_timeout = 30 s imposto dal server      RCP.md §2.2
    datagram abilitati sulla connessione HTTP/3     RCP.md §2.2
    almeno 16 stream unidirezionali di credito      RCP.md §2.3
      ⚠ qui si legge SOLO il credito iniziale — vedi il controllo
    il server NON DEVE offrire 0-RTT                RCP.md §2.3
    il server NON DEVE disabilitare la migrazione   RCP.md §2.3

⚠ **Le prime due erano gia' «misurate», e male.**  Il 10 agosto il server
  stampava da se' `max_idle_timeout=30000ms max_datagram_frame_size=65536`, e
  quella riga e' stata scritta nei documenti come una misura.  ⛔ Ma e' la sua
  CONFIGURAZIONE, non il filo: dice che cosa il server ha chiesto a ngtcp2, non
  che cosa e' arrivato al pari.  E' esattamente il corollario di `LEZIONI.md`
  §1.9 nato quella stessa mattina — *un denominatore si legge dove la cosa
  succede* — applicato contro una misura nostra invece che contro una libreria
  altrui.

⭐ Questa sonda le rilegge tutte dal **pari**, cioe' da dove si vedono davvero.

---------------------------------------------------------------------------
⛔ COME SI LEGGONO, E LO STRUMENTO E' DICHIARATO

`aioquic` conserva solo due dei parametri ricevuti (`_remote_max_idle_timeout`
e `_remote_max_datagram_frame_size`) e butta il resto dopo averlo usato.  Per
vedere anche `disable_active_migration` e il credito degli stream si mette una
**spia** sulla funzione che li analizza — `pull_quic_transport_parameters` —
e si tiene l'oggetto intero.

⚠ E' un attrezzo che entra dentro una libreria altrui, quindi e' **dichiarato
  qui** invece che nascosto: se un aggiornamento di aioquic sposta quella
  funzione, la sonda **non trova niente e lo dice**, invece di stampare zeri.

Il 0-RTT si vede da un'altra parte ancora: e' un **biglietto di sessione** con
`max_early_data_size`, e arriva dopo la stretta di mano.  Si aspetta un momento
e si guarda se ne e' arrivato uno.
"""
import argparse
import asyncio
import ssl
import sys

import aioquic.quic.connection as mod_conn
from aioquic.asyncio import connect
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent

# ⛔ H3_DATAGRAM (RFC 9297) — l'impostazione di HTTP/3, che NON e' il parametro
#    di trasporto di QUIC.  Rilievo R8.11: qui si misurava
#    `max_datagram_frame_size` (RFC 9221) e lo si chiamava «datagram sulla
#    connessione HTTP/3», che e' quel che RCP.md §2.2 pretende.  Un server che
#    alzasse il parametro di trasporto e NON annunciasse H3_DATAGRAM passava il
#    controllo, e i datagram dell'audio non partirebbero — con il sintomo
#    «sembra un difetto di rete» di LEZIONI.md §2.2.
H3_DATAGRAM = 0x33

# ---------------------------------------------------------------------------
# La spia sui parametri di trasporto.
VISTI = {}
_originale = mod_conn.pull_quic_transport_parameters


def _spia(*a, **kw):
    p = _originale(*a, **kw)
    VISTI["parametri"] = p
    return p


mod_conn.pull_quic_transport_parameters = _spia

# I biglietti di sessione, cioe' il 0-RTT.
BIGLIETTI = []


def raccogli_biglietto(b):
    BIGLIETTI.append(b)


class Ascoltatore(QuicConnectionProtocol):
    """⛔ Serve SOLO a leggere il SETTINGS di HTTP/3.

    La sonda si collegava con l'ALPN di HTTP/3 e **non costruiva nessuna
    `H3Connection`**: quindi non leggeva nessun SETTINGS, e l'impostazione che
    §2.2 pretende — `H3_DATAGRAM` — non la guardava nessuno (R8.11).  Il file
    accanto (`01-b2-sonda-impostazioni.py`) sa benissimo che e' un'altra cosa:
    la elenca per nome.
    """

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._http = H3Connection(self._quic, enable_webtransport=True)
        self.arrivate = asyncio.get_event_loop().create_future()

    def quic_event_received(self, event: QuicEvent) -> None:
        for _ in self._http.handle_event(event):
            pass
        imp = self._http.received_settings
        if imp is not None and not self.arrivate.done():
            self.arrivate.set_result(imp)


async def principale(a) -> int:
    conf = QuicConfiguration(
        is_client=True,
        alpn_protocols=H3_ALPN,
        max_datagram_frame_size=65536,
    )
    conf.verify_mode = ssl.CERT_NONE

    print(f"== i parametri di trasporto di {a.indirizzo}:{a.porta}  ({a.etichetta})")
    print()

    impostazioni = None
    perche_niente_settings = None
    try:
        # ⚠ `session_ticket_handler` sta su `connect`, non sulla
        #   configurazione: sono due posti diversi in due moduli diversi.
        async with connect(a.indirizzo, a.porta, configuration=conf,
                           create_protocol=Ascoltatore,
                           session_ticket_handler=raccogli_biglietto) as cliente:
            await asyncio.wait_for(cliente.wait_connected(), timeout=a.attesa)
            # ⛔ Il SETTINGS di HTTP/3 si aspetta e si legge: e' li' che sta
            #    `H3_DATAGRAM`, l'impostazione che §2.2 chiede (R8.11).
            # ⚠ E «non e' arrivato nessun SETTINGS» resta un fatto suo, diverso
            #   da «e' arrivato e non conteneva H3_DATAGRAM»: si tiene il
            #   perche', e piu' sotto lo si stampa invece di un numero.
            try:
                impostazioni = await asyncio.wait_for(cliente.arrivate,
                                                      timeout=a.attesa)
            except Exception as e:  # noqa: BLE001
                perche_niente_settings = f"{type(e).__name__}: {e}"
            # ⚠ Il biglietto di sessione arriva DOPO la stretta di mano: senza
            #   questa attesa, «nessun 0-RTT» sarebbe solo «non ho aspettato».
            await asyncio.sleep(a.attesa_biglietto)
    except Exception as e:  # noqa: BLE001
        print(f"   ⛔ non ci si collega: {type(e).__name__}: {e}")
        print("   ⚠ verdetto sul banco, non sulla libreria.")
        return 3

    p = VISTI.get("parametri")
    if p is None:
        print("   ⛔ la spia non ha catturato niente: `aioquic` ha spostato")
        print("      `pull_quic_transport_parameters`.  Nessun numero qui sotto")
        print("      varrebbe, quindi non se ne stampa nessuno.")
        return 3

    idle = getattr(p, "max_idle_timeout", None)
    dgram = getattr(p, "max_datagram_frame_size", None)
    migr = getattr(p, "disable_active_migration", None)
    suni = getattr(p, "initial_max_streams_uni", None)
    sbidi = getattr(p, "initial_max_streams_bidi", None)

    print("   quel che il server ha MANDATO:")
    print(f"      max_idle_timeout           = {idle}")
    print(f"      max_datagram_frame_size    = {dgram}")
    print(f"      disable_active_migration   = {migr}")
    print(f"      initial_max_streams_uni    = {suni}")
    print(f"      initial_max_streams_bidi   = {sbidi}")
    if impostazioni is None:
        print(f"      SETTINGS di HTTP/3         = nessuno letto"
              f"  ({perche_niente_settings})")
    else:
        print(f"      SETTINGS di HTTP/3         = {len(impostazioni)}"
              f"  ·  H3_DATAGRAM (0x33) = {impostazioni.get(H3_DATAGRAM)}")
    print(f"      biglietti di sessione      = {len(BIGLIETTI)}")
    for b in BIGLIETTI:
        print(f"         max_early_data_size = {getattr(b, 'max_early_data_size', None)}")
    print()

    # -----------------------------------------------------------------------
    # I controlli, ciascuno con il suo atteso e la sua riga di RCP.
    esiti = []

    def prova(nome, dove, passa, visto, atteso):
        esiti.append((nome, passa))
        segno = "OK " if passa else "NO "
        print(f"   {segno} {nome:34s} {dove}")
        print(f"       atteso {atteso} · misurato {visto}")

    prova("max_idle_timeout", "RCP.md §2.2",
          idle == a.idle_atteso, idle, a.idle_atteso)

    # ⛔ DUE COSE DIVERSE, DUE CONTROLLI DIVERSI — rilievo R8.11.
    #
    #    `max_datagram_frame_size` e' il parametro di TRASPORTO (RFC 9221):
    #    dice che la connessione QUIC sa portare datagram.  `H3_DATAGRAM`
    #    (0x33, RFC 9297) e' l'impostazione di HTTP/3, ed e' quella che
    #    `RCP.md` §2.2 pretende — «datagram DEVONO essere abilitati sulla
    #    connessione HTTP/3».  Il primo era misurato col nome del secondo.
    prova("datagram sul trasporto QUIC", "RFC 9221 (la fondamenta)",
          bool(dgram), dgram, "> 0")

    if impostazioni is None:
        prova("datagram su HTTP/3 (H3_DATAGRAM)", "RCP.md §2.2",
              False, f"nessun SETTINGS letto — {perche_niente_settings}",
              "0x33 presente e non zero")
    else:
        prova("datagram su HTTP/3 (H3_DATAGRAM)", "RCP.md §2.2",
              bool(impostazioni.get(H3_DATAGRAM)),
              impostazioni.get(H3_DATAGRAM, "assente"),
              "0x33 presente e non zero")

    # ⛔ Il credito degli stream unidirezionali: §2.3 ne impone almeno 16 «in
    #    ogni momento», perche' il client apre uno stream di input e uno per
    #    ogni trasferimento di appunti.  Se finisse, l'input non partirebbe
    #    affatto e il sintomo sarebbe «il desktop non risponde».
    #
    # ⚠ E IL NOME DEL CONTROLLO DICE QUEL CHE MISURA — rilievo R8.12.
    #   `initial_max_streams_uni` e' il credito che il server concede
    #   ALL'APERTURA, e non dice niente su quel che succede dopo: §2.3 e'
    #   scritta esattamente per il dopo, ed e' la forma di difetto che un banco
    #   corto non vede — funziona per i primi secondi e si ferma (LEZIONI.md
    #   §1.4).  Questa sonda apre, legge un numero e chiude: e' il banco corto
    #   contro cui quella riga e' stata scritta.  ⛔ Il credito «in ogni
    #   momento» qui NON e' misurato, e lo si dice invece di lasciarlo credere.
    prova("credito INIZIALE stream unidirezionali", "RCP.md §2.3 (solo l'apertura)",
          suni is not None and suni >= 16, suni, ">= 16")

    # ⛔ La migrazione: e' la ragione per cui QUIC e' stato scelto — il
    #    telefono che passa da WiFi a rete mobile.  Il parametro e' un
    #    interruttore che DEVE restare spento.
    prova("migrazione NON disabilitata", "RCP.md §2.3",
          not migr, migr, "falso o assente")

    # ⛔ Il 0-RTT: i dati si possono ripetere, e il secondo messaggio di RCP e'
    #    `CREDENZIALI`.
    #
    # ⭐ E questo controllo il suo controllo POSITIVO ce l'ha avuto subito, dal
    #    bersaglio stesso: al primo giro il server d'esempio di ngtcp2 ha
    #    mandato **due biglietti con max_early_data_size = 4294967295** `[M]`
    #    10 agosto 2026.  Cioe' la sonda sa vedere un 0-RTT acceso, perche'
    #    l'ha visto.  Il verde che segue e' un verde dopo una cura, non un
    #    verde da uno strumento cieco — che e' la differenza che conta.
    con_early = [b for b in BIGLIETTI
                 if getattr(b, "max_early_data_size", None)]
    prova("niente 0-RTT", "RCP.md §2.3",
          not con_early, f"{len(con_early)} biglietti con early data",
          "nessuno")

    print()
    print("== Verdetto")
    # ⛔ Quel che questi controlli NON dicono, detto qui e non altrove: un
    #    verdetto «tutti su tutti» che copre una proprieta' diversa da quella
    #    nominata e' peggio di un rosso (rilievo R8.12).
    print("   ⚠ NON misurato qui: il credito degli stream «in ogni momento»")
    print("     (§2.3).  Sopra c'e' solo il credito iniziale; quel che succede")
    print("     quando finisce lo vede un banco che tiene la sessione viva.")
    falliti = [n for n, ok in esiti if not ok]
    if not falliti:
        print(f"   ⭐ {len(esiti)} controlli su {len(esiti)}")
        return 0
    print(f"   ⛔ {len(falliti)} controlli su {len(esiti)} NON passano:")
    for n in falliti:
        print(f"      - {n}")
    return 1


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="i parametri di trasporto, sul filo")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7447)
    p.add_argument("--etichetta", default="ngtcp2")
    p.add_argument("--idle-atteso", type=int, default=30000)
    p.add_argument("--attesa", type=float, default=8.0)
    p.add_argument("--attesa-biglietto", type=float, default=1.5)
    a = p.parse_args()
    try:
        sys.exit(asyncio.run(principale(a)))
    except KeyboardInterrupt:
        sys.exit(130)
