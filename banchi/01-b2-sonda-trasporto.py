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
from aioquic.h3.connection import H3_ALPN
from aioquic.quic.configuration import QuicConfiguration

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


async def principale(a) -> int:
    conf = QuicConfiguration(
        is_client=True,
        alpn_protocols=H3_ALPN,
        max_datagram_frame_size=65536,
    )
    conf.verify_mode = ssl.CERT_NONE

    print(f"== i parametri di trasporto di {a.indirizzo}:{a.porta}  ({a.etichetta})")
    print()

    try:
        # ⚠ `session_ticket_handler` sta su `connect`, non sulla
        #   configurazione: sono due posti diversi in due moduli diversi.
        async with connect(a.indirizzo, a.porta, configuration=conf,
                           session_ticket_handler=raccogli_biglietto) as cliente:
            await asyncio.wait_for(cliente.wait_connected(), timeout=a.attesa)
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

    prova("datagram abilitati", "RCP.md §2.2",
          bool(dgram), dgram, "> 0")

    # ⛔ Il credito degli stream unidirezionali: §2.3 ne impone almeno 16 «in
    #    ogni momento», perche' il client apre uno stream di input e uno per
    #    ogni trasferimento di appunti.  Se finisse, l'input non partirebbe
    #    affatto e il sintomo sarebbe «il desktop non risponde».
    prova("credito stream unidirezionali", "RCP.md §2.3",
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
