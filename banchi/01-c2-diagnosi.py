#!/usr/bin/env python3
"""01-c2-diagnosi.py — ⛔ C2: tre modi di guastare il collegamento, TRE diagnosi diverse.

    python3 01-c2-diagnosi.py --fase con-server   --esiti /srv/src/c2-esiti.json
    python3 01-c2-diagnosi.py --fase senza-server --esiti /srv/src/c2-esiti.json
    python3 01-c2-diagnosi.py --elenco            le scene e le diagnosi attese

⚠ Gira DENTRO il contenitore.  Le due fasi le orchestra `01-c2-lancia.sh`, che
  fra l'una e l'altra **spegne il server**: e' l'unica cosa che questo file non
  puo' fare da se'.

===========================================================================
⛔ CHE COSA PROVA, IN UNA RIGA D'UTENTE

*«Quando non si collega, ti dice PERCHE' non si collega.»*

`FASI.md` §01-filo-nudo B12-C2, rilievo **R3.17**: si guasta il collegamento in
**tre modi** e si pretendono **tre diagnosi diverse** — nessuno in ascolto ·
**UDP 7447 filtrato col TCP che risponde** · impronta non corrente.

  ⛔ *«Un banco che le confonde dira' «il server non risponde» il giorno in cui
     il certificato e' scaduto.»*

⭐ E la seconda scena non e' un'ipotesi di scuola: e' **il caso concreto con
   cui R2 ha dimostrato che il primo controllo positivo del progetto era
   cieco**.

===========================================================================
⛔ QUEL CHE C2 CONSEGNA NON E' UN VERDE: E' UNA TABELLA DI DECISIONE

Il pezzo che vale e' `diagnosi()`, qui sotto: **due sonde indipendenti** — TCP e
UDP — e una tabella che dice quale nome esce da quale coppia di risposte.  Ogni
banco che oggi scrive «il server non risponde» dovrebbe chiamare quella.

⛔ **E c'e' un nome per «non lo so».**  Una diagnosi che nomina sempre qualcosa
   e' una diagnosi che indovina, ed e' §3 applicata a noi: *«NON DEVE
   indovinare»*.  `NON_SO` e' un esito legittimo, e va stampato.

===========================================================================
⛔ LE QUATTRO SCENE, E LA PRIMA E' QUELLA CHE DICE **NO**

  scena 0  `sano`                 il server c'e', l'impronta e' quella giusta.
                                  ⭐ **Senza questa, «tre diagnosi diverse» e'
                                  soddisfatto anche da un diagnosta che non
                                  sa dire «va tutto bene»**, cioe' da uno che
                                  trova sempre un guasto;
  scena 1  `nessuno-in-ascolto`   il server e' spento.  TCP rifiuta (RST), UDP
                                  rifiuta (ICMP porta irraggiungibile);
  scena 2  `udp-filtrato`         ⛔ la scena di R3.17: **qualcuno risponde in
                                  TCP sulla 7447 e i pacchetti UDP spariscono
                                  nel nulla**;
  scena 3  `impronta-non-corrente` il server c'e' e risponde benissimo, ma
                                  l'impronta che abbiamo in mano e' di un altro
                                  certificato — e' la scheda lasciata aperta due
                                  settimane di §4.1-bis.

===========================================================================
⛔ COME SI COSTRUISCE LA SCENA 2, E PERCHE' NON CON UN FIREWALL

Il modo ovvio sarebbe una regola `nft`/`iptables` che scarta l'UDP 7447.  ⛔ **E
non si fa**, per una ragione di banco e non di comodita': una regola di
firewall **sopravvive allo script che l'ha messa**.  Se questo programma
morisse a meta', ogni banco di questa macchina misurerebbe un guasto che nessuno
ha piu' in mente — e la diagnosi che ne uscirebbe sarebbe *«il server non
risponde»*, cioe' precisamente l'errore che C2 esiste per impedire, provocato
da C2.

⭐ **La scena si costruisce invece con due prese**: un ascoltatore TCP che
   accetta e tace, e una presa UDP legata alla 7447 che **butta via tutto**.
   Dal lato del client i byte sono identici a quelli di un `DROP`: nessuna
   risposta e nessun ICMP.

⚠ **E quel che questa scena NON riproduce, dichiarato**: con un `DROP` vero il
  pacchetto non arriva mai allo spazio utente, qui arriva e viene buttato.  La
  differenza **non e' osservabile dal client** — e il client e' l'unico che
  diagnostica — ma esiste, e chi legge deve saperlo.

===========================================================================
⛔ LO STATO INIZIALE (B0.1) E IL CONTO DI §4.4-bis (B0.3)

  · ⭐ **C2 non manda mai `CREDENZIALI`**: si ferma alla stretta di mano del
    trasporto.  Quindi **non consuma il conto di §4.4-bis** e non lascia un ban
    addosso a nessuno.  ⚠ E non chiama il comando di sblocco — che **esiste**,
    `01-b8-sblocca.py` su `--comando-socket` — perche' non ne ha bisogno:
    dichiarato, come B0.3 pretende;
  · le prese della scena 2 si aprono **solo dopo** che il server e' stato
    spento, e la fase `senza-server` **verifica** che sia davvero spento prima
    di aprirle: due cose in ascolto sulla stessa porta darebbero una scena che
    non e' nessuna delle quattro.
"""
import argparse
import asyncio
import hashlib
import json
import os
import socket
import ssl
import sys
import threading
import time

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

# ⛔ I NOMI DELLE DIAGNOSI.  Sono sette e non tre, e i quattro in piu' non sono
#    zelo: sono i casi in cui una tabella a tre voci sarebbe costretta a
#    scegliere il nome sbagliato.
SANO = "SANO"
NESSUNO_IN_ASCOLTO = "NESSUNO_IN_ASCOLTO"
UDP_FILTRATO = "UDP_FILTRATO"
IMPRONTA_NON_CORRENTE = "IMPRONTA_NON_CORRENTE"
IRRAGGIUNGIBILE = "IRRAGGIUNGIBILE"
TCP_FILTRATO = "TCP_FILTRATO"
UDP_RIFIUTATO = "UDP_RIFIUTATO_TCP_RISPONDE"
NON_SO = "NON_SO"

SPIEGA = {
    SANO: "il server c'e', parla QUIC, e presenta il certificato che ci "
          "aspettavamo",
    NESSUNO_IN_ASCOLTO: "la macchina c'e' e RIFIUTA: non c'e' nessun server su "
                        "questa porta.  Cura: accenderlo",
    UDP_FILTRATO: "⛔ qualcuno risponde in TCP sulla stessa porta e i pacchetti "
                  "UDP spariscono: fra noi e il server c'e' un filtro.  Cura: "
                  "la rete, NON il server",
    IMPRONTA_NON_CORRENTE: "⛔ il server c'e' e risponde: e' l'IMPRONTA che "
                           "abbiamo in mano a non essere piu' quella.  Cura: "
                           "ritirare l'impronta corrente (§4.1-bis), non "
                           "riavviare niente",
    IRRAGGIUNGIBILE: "silenzio su tutt'e due i trasporti: la macchina non c'e', "
                     "o e' filtrata per intero.  ⚠ Non e' «il server e' rotto»",
    TCP_FILTRATO: "l'UDP rifiuta (quindi la macchina c'e') e il TCP tace: il "
                  "filtro e' sul TCP",
    UDP_RIFIUTATO: "qualcuno serve il TCP e l'UDP RIFIUTA: il server della "
                   "pagina c'e', quello di RCP no.  ⚠ Non e' un filtro: e' un "
                   "processo mancante",
    NON_SO: "⛔ le due sonde non compongono nessuno dei casi noti.  Un nome "
            "inventato qui sarebbe la diagnosi sbagliata di §3: NON DEVE "
            "indovinare",
}


# ===========================================================================
# LE DUE SONDE.  ⛔ Indipendenti: e' l'intera ragione per cui C2 distingue quel
#    che un banco a una sonda sola non puo' distinguere.
# ===========================================================================
def sonda_tcp(indirizzo, porta, attesa=4.0):
    """→ «risponde» · «rifiutato» · «silenzio» · «errore: …»

    ⛔ I tre esiti sono TRE e non due: «rifiutato» dice che la macchina c'e' e
       che nessuno ascolta; «silenzio» non dice nemmeno se la macchina c'e'.
       Schiacciarli su «non risponde» e' come si perde meta' della diagnosi.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(attesa)
    try:
        s.connect((indirizzo, porta))
        return "risponde"
    except ConnectionRefusedError:
        return "rifiutato"
    except socket.timeout:
        return "silenzio"
    except OSError as e:
        # ⚠ `EHOSTUNREACH`/`ENETUNREACH` sono un rifiuto della RETE, non del
        #   pari: hanno un nome loro.
        return f"errore: {e.errno} {e.strerror}"
    finally:
        s.close()


def sonda_udp(indirizzo, porta, attesa=3.0):
    """→ «risposta» · «rifiutato» · «silenzio» · «errore: …»

    ⛔ Su una presa UDP **connessa**, un ICMP «porta irraggiungibile» torna al
       mittente come `ConnectionRefusedError`: e' l'unico modo che abbiamo di
       distinguere «nessuno ascolta» da «i pacchetti non arrivano».  Con una
       presa non connessa quell'ICMP si perde, e le due cose diventano una
       sola — ed e' esattamente la cecita' che C2 esiste per togliere.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(attesa)
    try:
        s.connect((indirizzo, porta))
        # Un pacchetto qualunque: quel che conta e' se torna un ICMP.  ⚠ Non e'
        # un `Initial` di QUIC valido, quindi un server sano lo ignorera' —
        # ed e' voluto: qui non stiamo parlando QUIC, stiamo bussando.
        for _ in range(3):
            s.send(b"\x00" * 32)
            time.sleep(0.15)
        try:
            s.recv(2048)
            return "risposta"
        except socket.timeout:
            return "silenzio"
    except ConnectionRefusedError:
        return "rifiutato"
    except OSError as e:
        return f"errore: {e.errno} {e.strerror}"
    finally:
        s.close()


async def sonda_quic(indirizzo, porta, attesa=8.0):
    """→ (completa, impronta, perche)

    `completa` dice se la stretta di mano QUIC+TLS e' arrivata in fondo;
    `impronta` e' lo SHA-256 del DER del certificato **presentato**, cioe'
    l'unico modo di rispondere alla domanda di §4.1-bis dal lato del client.
    """
    try:
        from aioquic.h3.connection import H3_ALPN
        from aioquic.quic.configuration import QuicConfiguration
        from aioquic.asyncio import connect
    except ImportError as e:
        return False, None, f"aioquic non c'e': {e}"
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             idle_timeout=15.0)
    conf.verify_mode = ssl.CERT_NONE
    try:
        # ⛔ `stream_handler` che non fa niente, e non e' pulizia estetica: il
        #    gestore predefinito di aioquic apre un `StreamWriter` per ogni
        #    stream che il PARI apre — e gli stream di controllo di HTTP/3 sono
        #    unidirezionali del server.  Alla distruzione quel writer prova a
        #    scriverci un FIN e alza `ValueError`, che Python stampa come una
        #    traccia dentro l'uscita del diagnosta.  ⚠ Una traccia in mezzo a
        #    una diagnosi non e' rumore: e' la cosa che chi legge guarda per
        #    prima, e manda a cercare nel posto sbagliato.
        gestore = connect(indirizzo, porta, configuration=conf,
                          stream_handler=lambda lettore, scrittore: None)
        cli = await gestore.__aenter__()
        try:
            await asyncio.wait_for(cli.wait_connected(), timeout=attesa)
            imp = None
            cert = getattr(getattr(cli._quic, "tls", None),
                           "_peer_certificate", None)
            if cert is not None:
                try:
                    from cryptography.hazmat.primitives.serialization import Encoding
                    imp = hashlib.sha256(
                        cert.public_bytes(Encoding.DER)).hexdigest()
                except Exception as e:  # noqa: BLE001
                    return True, None, f"certificato illeggibile: {e}"
            else:
                # ⛔ «Non ho potuto leggere l'impronta» non e' «l'impronta e'
                #    diversa»: sono due diagnosi con due cure opposte.
                return True, None, ("la stretta di mano riesce ma il "
                                    "certificato presentato non si legge da "
                                    "aioquic")
            return True, imp, ""
        finally:
            await gestore.__aexit__(None, None, None)
    except asyncio.TimeoutError:
        return False, None, "la stretta di mano QUIC non e' arrivata in fondo"
    except ConnectionRefusedError:
        return False, None, "ICMP porta irraggiungibile durante la stretta"
    except Exception as e:  # noqa: BLE001
        return False, None, f"{type(e).__name__}: {e}"


# ===========================================================================
# ⛔ LA TABELLA DI DECISIONE — il pezzo che questo banco esiste per consegnare.
# ===========================================================================
def diagnosi(tcp, udp, quic_completa, impronta, impronta_attesa):
    """(nome, perche').  ⛔ Nessun ramo predefinito che indovina."""
    if quic_completa:
        if impronta is None:
            return NON_SO, ("QUIC risponde ma il certificato presentato non si "
                            "e' potuto leggere: «impronta diversa» e «impronta "
                            "non letta» non si confondono")
        if impronta_attesa is None:
            return NON_SO, ("QUIC risponde e nessuno ci ha detto quale "
                            "impronta aspettarci: senza l'atteso non c'e' "
                            "confronto (B0.4)")
        if impronta == impronta_attesa:
            return SANO, "la stretta di mano riesce e l'impronta combacia"
        return IMPRONTA_NON_CORRENTE, (
            f"presentata {impronta[:16]}…, attesa {impronta_attesa[:16]}…")

    if tcp == "risponde" and udp == "silenzio":
        return UDP_FILTRATO, ("il TCP accetta sulla stessa porta e l'UDP non "
                              "torna indietro nemmeno con un ICMP")
    if tcp == "risponde" and udp == "rifiutato":
        return UDP_RIFIUTATO, "il TCP accetta e l'UDP risponde con un ICMP"
    if tcp == "rifiutato":
        return NESSUNO_IN_ASCOLTO, (
            f"il TCP rifiuta (quindi la macchina c'e') e l'UDP dice «{udp}»")
    if tcp == "silenzio" and udp == "rifiutato":
        return TCP_FILTRATO, "l'UDP rifiuta, quindi la macchina c'e'; il TCP tace"
    if tcp == "silenzio" and udp == "silenzio":
        return IRRAGGIUNGIBILE, "silenzio su tutt'e due i trasporti"
    return NON_SO, f"tcp={tcp} · udp={udp} · quic non completa"


# ===========================================================================
# LA SCENA 2: le due prese.  Si aprono, si usano, si chiudono.
# ===========================================================================
class ScenaUdpFiltrato:
    """Un ascoltatore TCP che accetta e tace, e una presa UDP che butta via.

    ⛔ Si chiude SEMPRE, e il `with` e' il meccanismo: una presa lasciata
       aperta sulla 7447 farebbe fallire l'accensione del prossimo server, e la
       diagnosi che ne uscirebbe sarebbe «la porta e' occupata» — cioe' un
       guasto di C2 travestito da guasto di un altro banco.
    """

    def __init__(self, indirizzo, porta):
        self.indirizzo, self.porta = indirizzo, porta
        self.tcp = self.udp = None
        self.vivo = threading.Event()
        self.buttati = 0

    def __enter__(self):
        # ⚠ SU TCP `SO_REUSEADDR` RESTA, E IL PERCHE' VA SCRITTO.  Su TCP
        #   quell'opzione permette di legarsi a una porta su cui restano
        #   connessioni in `TIME_WAIT` — e le lascia proprio questa scena, che
        #   accetta la connessione della sonda e la chiude per prima — ma
        #   **non** permette a due ascoltatori vivi di stare sulla stessa
        #   porta: il `bind` fallisce lo stesso se qualcuno ascolta davvero.
        #   Il testimone sopravvive, e senza l'opzione due giri di C2 a un
        #   minuto di distanza non partirebbero (`LEZIONI.md` §2.3-ter).
        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp.bind((self.indirizzo, self.porta))
        self.tcp.listen(8)
        # ⛔ SU UDP INVECE `SO_REUSEADDR` E' STATO TOLTO — rilievo R12-A.10.
        #
        #    Su Linux due prese UDP che dichiarano entrambe `SO_REUSEADDR`
        #    **possono legarsi allo stesso indirizzo:porta**, e i pacchetti
        #    vanno all'una o all'altra.  Cioe' l'opzione toglieva l'unico
        #    meccanismo che avrebbe fatto fallire il `bind` quando lo stato
        #    iniziale non e' quello dichiarato — e il fallimento del `bind` e'
        #    il testimone che il commento in cima a questo file chiede:
        #    *«due cose in ascolto sulla stessa porta darebbero una scena che
        #    non e' nessuna delle quattro»*.  ⚠ Su una presa che non deve
        #    essere riavviata in fretta l'opzione non serviva a niente e
        #    costava quella difesa.
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.bind((self.indirizzo, self.porta))
        self.vivo.set()
        threading.Thread(target=self._tcp, daemon=True).start()
        threading.Thread(target=self._udp, daemon=True).start()
        time.sleep(0.4)
        return self

    def _tcp(self):
        self.tcp.settimeout(0.5)
        while self.vivo.is_set():
            try:
                c, _ = self.tcp.accept()
            except (socket.timeout, OSError):
                continue
            # ⚠ Si accetta e si TACE: la scena e' «il TCP risponde», cioe' la
            #   connessione si stabilisce.  Rispondere con dell'HTTP
            #   aggiungerebbe alla scena una cosa che oggi il server non fa.
            try:
                c.close()
            except OSError:
                pass

    def _udp(self):
        self.udp.settimeout(0.5)
        while self.vivo.is_set():
            try:
                self.udp.recvfrom(65535)
                self.buttati += 1
            except (socket.timeout, OSError):
                continue

    def __exit__(self, *_):
        self.vivo.clear()
        for s in (self.tcp, self.udp):
            try:
                s.close()
            except OSError:
                pass
        time.sleep(0.3)
        return False


# ===========================================================================
def impronta_di(pem):
    import subprocess
    try:
        p = subprocess.run(["openssl", "x509", "-in", pem, "-outform", "der"],
                           capture_output=True, timeout=15)
        if p.returncode != 0:
            return None
        return hashlib.sha256(p.stdout).hexdigest()
    except (OSError, subprocess.TimeoutExpired):
        return None


def misura_scena(nome, a, indirizzo, porta, impronta_attesa, attesa_diagnosi):
    """Le tre sonde, la diagnosi, e il confronto con l'atteso — B0.4."""
    t0 = time.monotonic()
    tcp = sonda_tcp(indirizzo, porta)
    udp = sonda_udp(indirizzo, porta)
    completa, imp, perche_quic = asyncio.run(sonda_quic(indirizzo, porta))
    d, perche = diagnosi(tcp, udp, completa, imp, impronta_attesa)
    ms = (time.monotonic() - t0) * 1000
    return {"scena": nome, "tcp": tcp, "udp": udp, "quic": completa,
            "impronta": imp, "impronta_attesa": impronta_attesa,
            "perche_quic": perche_quic, "diagnosi": d, "perche": perche,
            "attesa": attesa_diagnosi, "ms": ms}


def stampa(r):
    ok = r["diagnosi"] == r["attesa"]
    c = VERDE if ok else ROSSO
    print(f"  {c}{'OK' if ok else 'NO'}{GRIGIO}  scena «{r['scena']}»  "
          f"({r['ms'] / 1000:.1f} s)")
    print(f"        sonde: TCP «{r['tcp']}» · UDP «{r['udp']}» · "
          f"QUIC {'completa' if r['quic'] else 'NON completa'}"
          + (f" ({r['perche_quic']})" if r["perche_quic"] else ""))
    print(f"        DIAGNOSI: {r['diagnosi']}   (attesa: {r['attesa']})")
    print(f"        perche':  {r['perche']}")
    print(f"        cura:     {SPIEGA[r['diagnosi']]}")


# ===========================================================================
def principale(a):
    if a.elenco:
        print("== ⛔ C2 — tre modi di guastare il collegamento, TRE diagnosi")
        for n, d, q in (
            ("0 sano", SANO, "il controllo che dice NO: il diagnosta sa anche "
                             "dire «va tutto bene»"),
            ("1 nessuno-in-ascolto", NESSUNO_IN_ASCOLTO, "server spento"),
            ("2 udp-filtrato", UDP_FILTRATO, "⛔ la scena di R3.17: TCP che "
                                             "risponde, UDP nel nulla"),
            ("3 impronta-non-corrente", IMPRONTA_NON_CORRENTE,
             "server sanissimo, impronta di un altro certificato"),
        ):
            print(f"  {n:26s} → {d}")
            print(f"  {'':26s}   {q}")
        print("\n  ⛔ E un ottavo nome, NON_SO: un diagnosta che nomina sempre "
              "qualcosa indovina.")
        return 0

    impronta_sessione = impronta_di(os.path.join(a.certificati, "sessione.pem"))
    impronta_pagina = impronta_di(os.path.join(a.certificati, "pagina.pem"))

    print(f"== ⛔ C2 — fase «{a.fase}»")
    print(f"   bersaglio {a.indirizzo}:{a.porta}")
    print(f"   impronta del certificato di SESSIONE (quella giusta): "
          f"{(impronta_sessione or '⛔ non letta')[:32]}…")
    print(f"   impronta del certificato della PAGINA (la «vecchia» della "
          f"scena 3): {(impronta_pagina or '⛔ non letta')[:32]}…\n")

    if impronta_sessione is None or impronta_pagina is None:
        print(f"    {ROSSO}⛔ senza le due impronte la scena 3 non esiste: non "
              f"si misura{GRIGIO}")
        print("       (non e' «le impronte combaciano»: e' che non si e' "
              "potuto guardare)")
        return 4
    if impronta_sessione == impronta_pagina:
        print(f"    {ROSSO}⛔ le due impronte COMBACIANO: la scena 3 non "
              f"separerebbe niente{GRIGIO}")
        print("       ⚠ Ed e' anche un rosso di B13.1 — i due certificati "
              "devono essere DUE.")
        return 4

    risultati = []

    if a.fase == "con-server":
        # ── scena 0: il controllo che dice NO ──────────────────────────────
        print("== scena 0 — `sano`  ⭐ il controllo che dice NO")
        r = misura_scena("sano", a, a.indirizzo, a.porta, impronta_sessione,
                         SANO)
        stampa(r)
        risultati.append(r)
        print()
        # ── scena 3: l'impronta non corrente ───────────────────────────────
        print("== scena 3 — `impronta-non-corrente`")
        print("   ⚠ la scena e' la stessa di prima: cambia SOLO l'impronta che")
        print("     teniamo in mano, che e' quella dell'ALTRO certificato —")
        print("     cioe' la scheda lasciata aperta due settimane di §4.1-bis")
        r = misura_scena("impronta-non-corrente", a, a.indirizzo, a.porta,
                         impronta_pagina, IMPRONTA_NON_CORRENTE)
        stampa(r)
        risultati.append(r)
        with open(a.esiti, "w", encoding="utf-8") as f:
            json.dump(risultati, f, ensure_ascii=False, indent=1)
        print(f"\n    --  i due esiti restano in {a.esiti}: il verdetto lo da'")
        print("        la fase «senza-server», che le ha tutte e quattro")
        return 0

    # ── fase «senza-server» ────────────────────────────────────────────────
    # ⛔ E PRIMA DI TUTTO: il server e' DAVVERO spento?  Le scene 1 e 2 non
    #    vogliono dire niente se qualcuno risponde ancora.
    #
    # ⛔ E QUI SI CONFRONTANO TUTT'E TRE I DATI, NON UNO — rilievo R12-A.9.
    #
    #    Fino all'11 agosto 2026 questa fase misurava `tcp0`, `udp0` e
    #    `completa0`, li **stampava tutti e tre** e ne confrontava **uno solo**
    #    (`if completa0: return 5`).  Ma il dato che dice «c'e' ancora qualcuno
    #    legato alla porta UDP» e' `udp0`: a server spento la sonda UDP deve
    #    ricevere l'ICMP «porta irraggiungibile», cioe' `"rifiutato"`; se torna
    #    `"silenzio"` **qualcuno tiene ancora quella presa**.
    #
    #    ⛔ Caso concreto, ed e' come B12 usa questo file: il server e' stato
    #       ucciso ma non e' ancora uscito.  La stretta QUIC non si completa →
    #       `completa0` falso → «OK nessuno parla QUIC» → si aprono le prese
    #       della scena 2 **su una porta gia' tenuta**, e le scene 1 e 2
    #       ricevono due nomi giusti per la ragione sbagliata.  La riga che
    #       l'avrebbe detto era stampata sullo schermo (B0.4: l'atteso lo
    #       confronta il banco, non chi legge).
    print("== ⛔ Lo stato iniziale della fase: il server dev'essere SPENTO")
    tcp0, udp0 = sonda_tcp(a.indirizzo, a.porta), sonda_udp(a.indirizzo, a.porta)
    completa0, _, _ = asyncio.run(sonda_quic(a.indirizzo, a.porta, attesa=5))
    print(f"    --  misurato: TCP «{tcp0}» · UDP «{udp0}» · QUIC "
          f"{'completa' if completa0 else 'NON completa'}")
    print("    --  atteso:   TCP «rifiutato» · UDP «rifiutato» · QUIC NON "
          "completa")
    # ⛔ E IL CONFRONTO GUARDA SOLO QUEL CHE FAREBBE MENTIRE LE SCENE, E NON
    #    TUTTO QUEL CHE E' DIVERSO DALL'ATTESO.  ⚠ La prima stesura di questa
    #    cura fermava il giro anche quando la sonda TCP diceva «silenzio», e il
    #    guasto di B12 su questo file — la sonda TCP accecata, che dice
    #    «silenzio» per costruzione — cadeva qui e usciva 5 invece di produrre
    #    `IRRAGGIUNGIBILE`: cioe' **il controllo dello stato iniziale toglieva
    #    al banco la capacita' di vedere il proprio guasto**, e C2 diventava
    #    non certificabile.  Misurato l'11 agosto 2026 sul giro vero.
    #
    #    ⭐ Da cui la regola: fermano il giro solo i fatti che rendono le scene
    #    **impossibili da costruire** — qualcuno tiene la porta, o qualcuno
    #    risponde.  Tutto il resto e' una misura, e la misura la fa il
    #    diagnosta: e' il suo mestiere, non un motivo per non lasciarlo
    #    lavorare.
    guai, note = [], []
    if completa0:
        guai.append("⛔ QUALCUNO PARLA ANCORA QUIC: le scene 1 e 2 "
                    "misurerebbero un server vivo credendolo spento")
    if udp0 == "silenzio":
        guai.append("⛔ la sonda UDP non riceve nemmeno l'ICMP «porta "
                    "irraggiungibile»: QUALCUNO TIENE ANCORA LA PRESA UDP "
                    "— e la scena 2 aprirebbe le proprie prese sopra la sua")
    elif udp0 != "rifiutato":
        note.append(f"⚠ la sonda UDP dice «{udp0}» e non «rifiutato»")
    if tcp0 == "risponde":
        guai.append("⛔ qualcuno ASCOLTA IN TCP sulla porta: la scena 1 "
                    "riceverebbe la diagnosi della scena 2")
    elif tcp0 != "rifiutato":
        note.append(f"⚠ la sonda TCP dice «{tcp0}» e non «rifiutato»: la "
                    f"scena 1 non potra' uscire NESSUNO_IN_ASCOLTO.  ⛔ E le "
                    f"cause sono DUE e vanno tenute distinte — o fra noi e la "
                    f"macchina c'e' un filtro, o la sonda TCP di questo "
                    f"diagnosta e' cieca.  Se la scena 1 diventa rossa, e' "
                    f"qui che si guarda per primo")
    for n in note:
        print(f"    {GIALLO}{n}{GRIGIO}")
    if guai:
        print(f"    {ROSSO}⛔ LO STATO INIZIALE NON E' QUELLO DICHIARATO "
              f"(B0.1){GRIGIO}")
        for g in guai:
            print(f"       {g}")
        print("       ⛔ Non si misura: due scene che si contaminano danno due")
        print("          nomi giusti per la ragione sbagliata, e questo NON e'")
        print("          un rosso del diagnosta.")
        return 5
    print(f"    {VERDE}OK{GRIGIO}  nessuno tiene la porta e nessuno risponde: "
          f"le scene 1 e 2 si possono costruire"
          + ("  ⚠ (con le note qui sopra)" if note else "") + "\n")

    try:
        with open(a.esiti, encoding="utf-8") as f:
            risultati = json.load(f)
        print(f"    --  {len(risultati)} scene ereditate da «con-server»\n")
    except (OSError, ValueError) as e:
        print(f"    {GIALLO}[?]{GRIGIO} le scene con il server non si leggono "
              f"({e}): il giro sara' PARZIALE, e lo dice\n")
        risultati = []

    print("== scena 1 — `nessuno-in-ascolto`")
    r = misura_scena("nessuno-in-ascolto", a, a.indirizzo, a.porta,
                     impronta_sessione, NESSUNO_IN_ASCOLTO)
    stampa(r)
    risultati.append(r)
    print()

    print("== scena 2 — `udp-filtrato`  ⛔ la scena di R3.17")
    print("   due prese: un ascoltatore TCP che accetta e tace, e una presa UDP")
    print("   che butta via tutto.  ⚠ Non e' una regola di firewall, e il")
    print("   perche' sta in cima a questo file — dal lato del client i byte")
    print("   sono gli stessi.")
    with ScenaUdpFiltrato(a.indirizzo, a.porta) as scena:
        r = misura_scena("udp-filtrato", a, a.indirizzo, a.porta,
                         impronta_sessione, UDP_FILTRATO)
        r["pacchetti_buttati"] = scena.buttati
    stampa(r)
    print(f"        ⭐ e la presa UDP ha buttato {r['pacchetti_buttati']} "
          f"pacchetti: la scena c'era davvero")
    # ⛔ Zero pacchetti buttati vorrebbe dire che i nostri UDP non sono nemmeno
    #    arrivati alla presa, cioe' che la scena non e' quella che crediamo.
    if r["pacchetti_buttati"] == 0:
        print(f"        {ROSSO}⛔ ZERO pacchetti buttati: la presa non ha visto "
              f"niente, quindi il silenzio misurato non e' il suo{GRIGIO}")
        r["diagnosi"] = NON_SO
    risultati.append(r)
    print()

    # ⛔ Gli esiti si riscrivono TUTTI E QUATTRO, non solo i due nuovi: il file
    #    e' quel che un altro banco leggera' per sapere com'e' andato questo
    #    giro, e un file che ne contiene due su quattro racconta mezza prova.
    try:
        with open(a.esiti, "w", encoding="utf-8") as f:
            json.dump(risultati, f, ensure_ascii=False, indent=1)
    except OSError as e:
        print(f"    {GIALLO}[?] gli esiti non si sono riscritti: {e}{GRIGIO}")

    # ── IL VERDETTO ────────────────────────────────────────────────────────
    print("    == quel che questo giro ha davvero guardato")
    print(f"    --  scene misurate: {len(risultati)} su 4")
    giuste = [r for r in risultati if r["diagnosi"] == r["attesa"]]
    print(f"    --  diagnosi che combaciano con l'attesa: {len(giuste)} su "
          f"{len(risultati)}")
    nomi = {r["diagnosi"] for r in risultati}
    print(f"    --  nomi diversi prodotti: {len(nomi)} su {len(risultati)} "
          f"scene  ({', '.join(sorted(nomi))})")

    # ⛔ UN VERDETTO SU ZERO SCENE NON SI DA'.
    if not risultati:
        print(f"\n    {ROSSO}⛔ ZERO scene: non e' un verde{GRIGIO}")
        return 2

    print()
    if len(risultati) < 4:
        print(f"    {GIALLO}[?] C2: giro PARZIALE — {len(risultati)} scene su "
              f"4{GRIGIO}")
        print("       «Tre diagnosi diverse» non si puo' dire con meno di tre "
              "guasti.")
        return 3
    sbagliate = [r for r in risultati if r["diagnosi"] != r["attesa"]]
    if sbagliate:
        print(f"    {ROSSO}⛔ C2: {len(sbagliate)} scene su {len(risultati)} "
              f"ricevono la diagnosi sbagliata{GRIGIO}")
        for r in sbagliate:
            print(f"       «{r['scena']}»: detto {r['diagnosi']}, atteso "
                  f"{r['attesa']}")
        return 1
    # ⛔ E il controllo che nessuno scrive: le diagnosi devono essere DIVERSE
    #    FRA LORO.  Quattro scene che ricevono lo stesso nome giusto per caso
    #    non sarebbero quattro diagnosi.
    if len(nomi) != len(risultati):
        print(f"    {ROSSO}⛔ C2: {len(risultati)} scene ma solo {len(nomi)} "
              f"nomi diversi{GRIGIO}")
        return 1
    print(f"    {VERDE}⭐ C2: quattro guasti, quattro diagnosi diverse, e "
          f"ciascuna nomina la cura giusta{GRIGIO}")
    print("       ⛔ Compresa quella che il giorno del certificato scaduto non")
    print("          dira' «il server non risponde».")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="C2 — tre modi di guastare il collegamento, tre diagnosi")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7447)
    p.add_argument("--certificati", default="/media/REMOTIX/b2-certificati")
    p.add_argument("--fase", default="con-server",
                   choices=["con-server", "senza-server"])
    p.add_argument("--esiti", default="/srv/src/c2-esiti.json")
    p.add_argument("--elenco", action="store_true")
    sys.exit(principale(p.parse_args()))
