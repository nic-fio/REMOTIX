#!/usr/bin/env python3
"""01-b2-sonda-trasporto.py — i parametri di trasporto, letti SUL FILO.

    python3 01-b2-sonda-trasporto.py --bersaglio innesto  --porta 7447 --idle-atteso 30000
    python3 01-b2-sonda-trasporto.py --bersaglio prodotto --porta 7448 --idle-atteso 30000
    python3 01-b2-sonda-trasporto.py --bersaglio controllo --porta 7449 \\
            --idle-atteso 60000 --credito-atteso 125 --bozze-attese 02

---------------------------------------------------------------------------
⛔ CHE COSA MISURA, E PERCHE' NON BASTAVA QUEL CHE C'ERA

Le proprieta' che `FASI.md` §01-filo-nudo assegna a B2 «perche' sono della
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
⛔⭐ IL BERSAGLIO STA DENTRO OGNI RIGA DEL REGISTRO — e questo file lo pretende

*Aggiunto l'11 agosto 2026, ed e' la ragione per cui questa sonda e' stata
riaperta.*

Le sei proprieta' sono `[M]` **sull'innesto** (`bsslserver` + gli innesti di
B2, porta 7447).  Il **prodotto** (`remotix`, porta 7448) e' un altro server, e
di cinque delle sei non si sa niente: ⛔ **sei numeri letti su due server
diversi, se il registro non dice quale, sono sei numeri che non si possono
mettere in fila.**  Da cui `--bersaglio`, che e' **obbligatorio**, e la riga
JSONL che ogni giro scrive.

⚠ E accanto al bersaglio va **l'impronta di quel che si e' misurato**
(`--impronta`): un binario ricostruito e' un altro bersaglio con lo stesso
nome.  Se il lanciatore non la passa, nel registro finisce `ignota` — che e'
un'informazione, non uno zero.

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

---------------------------------------------------------------------------
⛔ E LA PROPRIETA' CHE DAL PARI **NON SI LEGGE**, detta qui e non altrove

Le proprieta' di B2 sono sei.  Questa sonda ne legge **cinque**.

    `allowPooling: false`  —  `RCP.md` §4.1-bis

⛔ Non e' un parametro che il server manda: e' un campo dell'oggetto
`WebTransport` **che costruisce la pagina**, dentro il browser.  Sul filo non
c'e' nessun byte che lo porti, e nessuna sonda QUIC potra' mai leggerlo.  Si
legge nel sorgente della pagina (`[R]`) o nel browser che la esegue — non qui.
⚠ Dichiararlo e' informazione; dedurlo da un verde di questa sonda sarebbe
**E1**, una lettura che prova meno di quel che le si attribuisce.
"""
import argparse
import asyncio
import json
import ssl
import sys
from datetime import datetime
from pathlib import Path

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

# ⛔ Le DUE dichiarazioni di WebTransport, e sono due perche' le bozze in
#    circolazione sono due.  `src/webtransport.c` le manda tutt'e due e dice
#    perche'; qui si verifica che sul filo ci siano davvero.
#
#      0x2b603742  SETTINGS_ENABLE_WEBTRANSPORT   bozza 02  — la cerca aioquic
#      0xc671706a  SETTINGS_WT_MAX_SESSIONS       bozza 07+ — la cercano i browser
#
# ⚠ E' un rilievo GROSSO E MUTO: un server che ne mandasse una sola
#   funzionerebbe con meta' dei nostri strumenti e non con l'altra meta', e la
#   meta' che funziona sarebbe quella sbagliata da cui trarre conclusioni.  Il
#   sintomo, dal lato che sbaglia, e' «la sessione non si apre» — che e' la
#   stessa frase di altre quattro cause.
WT_BOZZA_02 = 0x2B603742
WT_BOZZA_07 = 0xC671706A
BOZZE = {"02": WT_BOZZA_02, "07": WT_BOZZA_07}

# ⚠ RFC 9220: senza questa, l'extended CONNECT non esiste e WebTransport su
#   HTTP/3 non puo' nemmeno cominciare.  `RCP.md` non la nomina — quindi qui
#   NON e' un controllo contro l'arbitro, e' una LETTURA dichiarata: la si
#   stampa perche' la sua assenza spiegherebbe da sola un «non si apre».
ENABLE_CONNECT_PROTOCOL = 0x08

# ⛔ Quanti stream unidirezionali si porta via HTTP/3 PER SE'.  Non e' una
#    costante creduta: piu' sotto si CONTANO quelli che la nostra
#    `H3Connection` ha davvero aperto, e il numero misurato e' quello che
#    entra nel conto.  Questo serve solo a dire nel registro che cosa ci si
#    aspettava di contare.
HTTP3_UNI_ATTESI = 3

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

    # ⛔ QUANTI STREAM UNIDIREZIONALI SI E' PRESO HTTP/3, CONTATI E NON CREDUTI.
    #
    #    `H3Connection` apre di suo il canale di controllo e i due di QPACK, e
    #    NON si chiudono mai per tutta la connessione.  Sono stream
    #    unidirezionali del client come tutti gli altri: mangiano lo stesso
    #    credito che `RCP.md` §2.3 riserva a RCP.
    #
    # ⚠ E' un conto fatto sul NOSTRO client, non sul browser: sta scritto
    #   accanto al numero, ed e' la ragione per cui il verdetto sul credito
    #   porta la parola «con questo client».
    def uni_di_http3(self):
        ids = [
            getattr(self._http, "_local_control_stream_id", None),
            getattr(self._http, "_local_encoder_stream_id", None),
            getattr(self._http, "_local_decoder_stream_id", None),
        ]
        return [i for i in ids if i is not None]


async def principale(a) -> int:
    conf = QuicConfiguration(
        is_client=True,
        alpn_protocols=H3_ALPN,
        max_datagram_frame_size=65536,
    )
    conf.verify_mode = ssl.CERT_NONE

    print(f"== i parametri di trasporto di {a.indirizzo}:{a.porta}")
    print(f"   ⛔ BERSAGLIO: {a.bersaglio}   ({a.etichetta})")
    print(f"   impronta del bersaglio: {a.impronta}")
    print()

    impostazioni = None
    perche_niente_settings = None
    uni_h3 = []
    credito_corrente = None
    try:
        # ⚠ `session_ticket_handler` sta su `connect`, non sulla
        #   configurazione: sono due posti diversi in due moduli diversi.
        async with connect(a.indirizzo, a.porta, configuration=conf,
                           create_protocol=Ascoltatore,
                           session_ticket_handler=raccogli_biglietto) as cliente:
            await asyncio.wait_for(cliente.wait_connected(), timeout=a.attesa)
            # ⛔ Il SETTINGS di HTTP/3 si aspetta e si legge: e' li' che stanno
            #    `H3_DATAGRAM` (R8.11) e le due dichiarazioni di WebTransport.
            # ⚠ E «non e' arrivato nessun SETTINGS» resta un fatto suo, diverso
            #   da «e' arrivato e non conteneva X»: si tiene il perche', e piu'
            #   sotto lo si stampa invece di un numero.
            try:
                impostazioni = await asyncio.wait_for(cliente.arrivate,
                                                      timeout=a.attesa)
            except Exception as e:  # noqa: BLE001
                perche_niente_settings = f"{type(e).__name__}: {e}"
            # ⚠ Il biglietto di sessione arriva DOPO la stretta di mano: senza
            #   questa attesa, «nessun 0-RTT» sarebbe solo «non ho aspettato».
            await asyncio.sleep(a.attesa_biglietto)
            uni_h3 = cliente.uni_di_http3()
            # ⛔ Il credito COME STA ADESSO, e viene dal pari: `aioquic` alza
            #    `_remote_max_streams_uni` a ogni `MAX_STREAMS_UNI` ricevuto.
            #    Se il server rinnova, qui si vede un numero piu' alto di
            #    quello iniziale; se non rinnova, si vede lo stesso.
            credito_corrente = getattr(cliente._quic, "_remote_max_streams_uni",
                                       None)
    except Exception as e:  # noqa: BLE001
        print(f"   ⛔ non ci si collega: {type(e).__name__}: {e}")
        print("   ⚠ verdetto sul banco, non sulla libreria.")
        scrivi_registro(a, esito="NON-COLLEGATO",
                        dettaglio=f"{type(e).__name__}: {e}", misure={},
                        controlli=[])
        return 3

    p = VISTI.get("parametri")
    if p is None:
        print("   ⛔ la spia non ha catturato niente: `aioquic` ha spostato")
        print("      `pull_quic_transport_parameters`.  Nessun numero qui sotto")
        print("      varrebbe, quindi non se ne stampa nessuno.")
        scrivi_registro(a, esito="SPIA-CIECA", dettaglio="pull_quic_transport_"
                        "parameters non e' piu' dov'era", misure={}, controlli=[])
        return 3

    idle = getattr(p, "max_idle_timeout", None)
    dgram = getattr(p, "max_datagram_frame_size", None)
    migr = getattr(p, "disable_active_migration", None)
    suni = getattr(p, "initial_max_streams_uni", None)
    sbidi = getattr(p, "initial_max_streams_bidi", None)

    # ⛔⭐ IL CONTO CHE SEPARA 19 DA 16, e sta tutto in questa riga.
    #
    #    `initial_max_streams_uni` e' un TOTALE.  HTTP/3 se ne prende tre
    #    (controllo + i due di QPACK) dal primo secondo e non li restituisce
    #    mai.  Quel che resta a RCP — lo stream di input, uno per ogni
    #    trasferimento di appunti — e' il totale MENO quelli.
    #
    #    §2.3 chiede «almeno 16 DISPONIBILI in ogni momento»: la grandezza di
    #    cui parla e' questa, non il totale.
    consumati = len(uni_h3)
    disponibili = None if suni is None else suni - consumati

    print("   quel che il server ha MANDATO:")
    print(f"      max_idle_timeout           = {idle}")
    print(f"      max_datagram_frame_size    = {dgram}")
    print(f"      disable_active_migration   = {migr}")
    print(f"      initial_max_streams_uni    = {suni}   (TOTALE)")
    print(f"      initial_max_streams_bidi   = {sbidi}")
    print(f"      credito uni ADESSO         = {credito_corrente}"
          "   (iniziale + eventuali MAX_STREAMS_UNI)")
    print()
    print("   quel che ne resta a RCP, e il conto e' scritto:")
    print(f"      stream uni presi da HTTP/3 = {consumati}   (contati: {uni_h3})")
    print(f"      disponibili a RCP          = {suni} - {consumati} = {disponibili}")
    if impostazioni is None:
        print(f"      SETTINGS di HTTP/3         = nessuno letto"
              f"  ({perche_niente_settings})")
    else:
        print(f"      SETTINGS di HTTP/3         = {len(impostazioni)} impostazioni")
        for chiave, nome in ((H3_DATAGRAM, "H3_DATAGRAM        (0x33)"),
                             (ENABLE_CONNECT_PROTOCOL,
                              "ENABLE_CONNECT_PROT (0x08)"),
                             (WT_BOZZA_02, "WT bozza 02 (0x2b603742)"),
                             (WT_BOZZA_07, "WT bozza 07 (0xc671706a)")):
            v = impostazioni.get(chiave, "assente")
            print(f"         {nome} = {v}")
    print(f"      biglietti di sessione      = {len(BIGLIETTI)}")
    for b in BIGLIETTI:
        print(f"         max_early_data_size = {getattr(b, 'max_early_data_size', None)}")
    print()

    # -----------------------------------------------------------------------
    # I controlli, ciascuno con il suo atteso e la sua riga di RCP.
    esiti = []

    def prova(nome, dove, passa, visto, atteso):
        esiti.append({"nome": nome, "dove": dove, "passa": bool(passa),
                      "visto": str(visto), "atteso": str(atteso)})
        segno = "OK " if passa else "NO "
        print(f"   {segno} {nome:38s} {dove}")
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

    # ⛔⭐ LE DUE BOZZE DI WEBTRANSPORT, E QUI SI DECIDE CHE COSA E' UN ROSSO.
    #
    #    `--bozze-attese` dice quali si pretendono da QUESTO bersaglio:
    #      · sul prodotto e sull'innesto sono DUE (02 e 07): un server che ne
    #        mandasse una sola aprirebbe la sessione con meta' degli strumenti
    #        e non con l'altra meta';
    #      · sul controllo positivo (`aioquic` che fa da server) e' UNA sola —
    #        aioquic 1.2 conosce la 02 e basta `[R]`.  ⭐ Ed e' esattamente il
    #        CONTROLLO NEGATIVO di questo controllo: se puntando la sonda
    #        contro aioquic la 07 risultasse presente, il controllo non
    #        saprebbe dire di no e i verdi sugli altri due bersagli non
    #        varrebbero niente.
    attese = [b.strip() for b in a.bozze_attese.split(",") if b.strip()]
    for nome_bozza in ("02", "07"):
        chiave = BOZZE[nome_bozza]
        presente = bool(impostazioni.get(chiave)) if impostazioni else False
        if nome_bozza in attese:
            prova(f"WebTransport dichiarato — bozza {nome_bozza}",
                  "RCP.md §2 (l'innesto ne manda due)",
                  presente,
                  impostazioni.get(chiave, "assente") if impostazioni
                  else f"nessun SETTINGS — {perche_niente_settings}",
                  "presente e non zero")
        else:
            # Non e' un controllo: e' una lettura, e si stampa senza voto.
            visto = (impostazioni.get(chiave, "assente") if impostazioni
                     else "nessun SETTINGS")
            print(f"   --  bozza {nome_bozza} non pretesa da questo bersaglio "
                  f"· letta: {visto}")

    if impostazioni is not None:
        # ⚠ Lettura, non controllo: `RCP.md` non nomina RFC 9220.  Ma la sua
        #   assenza spiegherebbe da sola un «la sessione non si apre», e
        #   cercarla dopo costa una serata.
        print(f"   --  ENABLE_CONNECT_PROTOCOL (RFC 9220, lettura non "
              f"normativa) = {impostazioni.get(ENABLE_CONNECT_PROTOCOL, 'assente')}")

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
    #
    # ⛔⭐ E IL CONTROLLO E' SUI DISPONIBILI, NON SUL TOTALE — 11 agosto 2026.
    #    Prima si controllava `suni >= 16`, e con quel controllo un server che
    #    dichiara 16 passava mentre a RCP ne restavano 13.  E' il rilievo B-12,
    #    che `src/trasporto.c` ha gia' curato dichiarando 19: quel 19 qui si
    #    LEGGE, e il verdetto si da' sul numero di cui §2.3 parla.
    if disponibili is None:
        prova("credito uni DISPONIBILE a RCP all'apertura",
              "RCP.md §2.3 (solo l'apertura)",
              False, "il pari non ha mandato initial_max_streams_uni",
              f">= {a.credito_atteso}")
    else:
        prova("credito uni DISPONIBILE a RCP all'apertura",
              "RCP.md §2.3 (solo l'apertura)",
              disponibili >= a.credito_atteso,
              f"{disponibili}  (= {suni} dichiarati - {consumati} di HTTP/3)",
              f">= {a.credito_atteso}")

    # ⚠ E un controllo sullo STRUMENTO, non sul server: se HTTP/3 non si fosse
    #   preso i tre stream che ci si aspetta, il conto qui sopra sarebbe fatto
    #   con un denominatore sbagliato — e sarebbe un numero credibile e falso.
    prova("lo strumento ha contato gli stream di HTTP/3",
          "controllo della SONDA, non del server",
          consumati == HTTP3_UNI_ATTESI, consumati, HTTP3_UNI_ATTESI)

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
    print("     (§2.3).  Sopra c'e' solo il credito all'apertura; quel che")
    print("     succede quando finisce lo vede un banco che tiene viva la")
    print("     sessione e apre stream finche' il credito non si esaurisce.")
    print("   ⚠ NON misurato qui: `allowPooling: false` (§4.1-bis) — non passa")
    print("     dal filo, sta nella pagina.  Si legge nel sorgente o nel")
    print("     browser, e questa sonda non ne sa niente.")
    print(f"   ⚠ I {consumati} stream di HTTP/3 sono contati su QUESTO client")
    print("     (aioquic).  Un browser potrebbe aprirne di piu' — per esempio")
    print("     uno stream di «grease» — e allora i disponibili sarebbero meno")
    print("     di quanti se ne leggono qui.  Nessuno l'ha misurato: `[?]`")
    if not BIGLIETTI:
        # ⛔ «Nessun biglietto» e «biglietti senza early data» sono due fatti
        #    diversi, e il verde e' lo stesso.  Chi legge deve sapere quale dei
        #    due ha avuto: nel primo caso questo giro non ha dimostrato che lo
        #    strumento sappia vedere un 0-RTT acceso, e il controllo positivo
        #    di quella riga resta quello STORICO del 10 agosto (l'innesto prima
        #    della cura, due biglietti con max_early_data_size 4294967295).
        print("   ⚠ NESSUN biglietto di sessione e' arrivato: il verde su «niente")
        print("     0-RTT» viene da un'assenza, non da un biglietto guardato.")
        print("     Il controllo positivo di quella riga resta quello del 10")
        print("     agosto sull'innesto, non questo giro.")

    falliti = [c["nome"] for c in esiti if not c["passa"]]
    misure = {
        "max_idle_timeout": idle,
        "max_datagram_frame_size": dgram,
        "disable_active_migration": migr,
        "initial_max_streams_uni": suni,
        "initial_max_streams_bidi": sbidi,
        "credito_uni_adesso": credito_corrente,
        "uni_presi_da_http3": consumati,
        "uni_disponibili_a_rcp": disponibili,
        "settings_http3": (None if impostazioni is None
                           else {hex(k): v for k, v in impostazioni.items()}),
        "perche_niente_settings": perche_niente_settings,
        "biglietti": len(BIGLIETTI),
        "biglietti_con_early_data": len(con_early),
    }
    esito = "TUTTI" if not falliti else "ROSSO"
    scrivi_registro(a, esito=esito,
                    dettaglio=("tutti i controlli passano" if not falliti
                               else "non passano: " + ", ".join(falliti)),
                    misure=misure, controlli=esiti)

    if not falliti:
        print(f"   ⭐ {len(esiti)} controlli su {len(esiti)}")
        return 0
    print(f"   ⛔ {len(falliti)} controlli su {len(esiti)} NON passano:")
    for n in falliti:
        print(f"      - {n}")
    return 1


def scrivi_registro(a, esito, dettaglio, misure, controlli):
    """⛔ Una riga per giro, e il BERSAGLIO ci sta dentro.

    Senza, sei numeri letti su due server diversi non si possono mettere in
    fila — ed e' precisamente il lavoro per cui questa sonda e' stata riaperta
    l'11 agosto 2026.
    """
    riga = {
        "banco": "B2-trasporto",
        "bersaglio": a.bersaglio,
        "impronta_bersaglio": a.impronta,
        "indirizzo": f"{a.indirizzo}:{a.porta}",
        "etichetta": a.etichetta,
        "attesi": {
            "max_idle_timeout": a.idle_atteso,
            "uni_disponibili_a_rcp": a.credito_atteso,
            "bozze_webtransport": a.bozze_attese,
        },
        "esito": esito,
        "dettaglio": dettaglio,
        "misure": misure,
        "controlli": controlli,
        "ora": datetime.now().isoformat(timespec="seconds"),
    }
    try:
        with Path(a.registro).open("a") as f:
            f.write(json.dumps(riga, ensure_ascii=False, default=str) + "\n")
        print(f"   ·· registrato in {a.registro}")
    except Exception as e:  # noqa: BLE001
        # ⛔ Un registro che non si scrive si DICE.  Un giro senza riga e' un
        #    giro che fra sei mesi non e' mai avvenuto.
        print(f"   ⛔ il registro NON e' stato scritto: {type(e).__name__}: {e}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="i parametri di trasporto, sul filo")
    # ⛔ Obbligatorio, e non ha un valore predefinito apposta: un giro senza
    #    bersaglio produce un numero che non si puo' mettere in fila con gli
    #    altri, ed e' peggio di nessun giro.
    p.add_argument("--bersaglio", required=True,
                   choices=("innesto", "prodotto", "controllo"),
                   help="innesto = bsslserver+B2 (7447) · prodotto = remotix "
                        "(7448) · controllo = aioquic che fa da server")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7447)
    p.add_argument("--etichetta", default="senza-etichetta")
    p.add_argument("--impronta", default="ignota",
                   help="l'impronta di CIO' CHE SI MISURA (md5 del binario): "
                        "un binario ricostruito e' un altro bersaglio con lo "
                        "stesso nome")
    p.add_argument("--idle-atteso", type=int, default=30000)
    p.add_argument("--credito-atteso", type=int, default=16,
                   help="stream uni DISPONIBILI a RCP dopo i 3 di HTTP/3 "
                        "(RCP.md §2.3)")
    p.add_argument("--bozze-attese", default="02,07",
                   help="quali dichiarazioni di WebTransport si pretendono da "
                        "questo bersaglio")
    p.add_argument("--registro",
                   default=str(Path(__file__).resolve().parent
                               / "b2-trasporto-esiti.jsonl"))
    p.add_argument("--attesa", type=float, default=8.0)
    p.add_argument("--attesa-biglietto", type=float, default=1.5)
    a = p.parse_args()
    try:
        sys.exit(asyncio.run(principale(a)))
    except KeyboardInterrupt:
        sys.exit(130)
