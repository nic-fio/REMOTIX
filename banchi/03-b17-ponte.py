#!/usr/bin/env python3
"""03-b17-ponte.py — ⭐ IL PONTE DELLO STEP 5: il ritardatore e l'ancora dell'orologio.

    python3 03-b17-ponte.py --fuori 7605 --dentro 7615 --orologio 7616 \
                            --comando /tmp/03-b17/comando --verbale /tmp/03-b17/ponte.json
    python3 03-b17-ponte.py --orologio-chiedi 192.168.0.2:7616 --campioni 200
    python3 03-b17-ponte.py --certifica          ⭐ gira da solo, su loopback

⛔ PERCHE' QUESTO FILE ESISTE, E NON E' UN ORPELLO

Il banco dell'anello del ritardo ha DUE bisogni che nessun altro pezzo copre, e
tutti e due sono controlli, non comodita'.

── 1. IL RITARDO NOTO (controllo P1) ───────────────────────────────────────────

`web.md` §6.3: «il server ritarda di N millisecondi noti, e la mediana DEVE
salire di esattamente N.  Un banco che non lo fa non sa di misurare».

⛔ E il prodotto **non sa farlo**: `RCP.md` §7.5 prevede `BANCO_MARCA` col campo
   `ritardo_ms`, ma in `src/rcp.c:53` `BANCO_ACCESO` vale **0** e il ramo
   ACCETTATA (`src/rcp.c:2498-2504`) e' uno **stub** — due assegnazioni, nessuna
   attesa, nessun disegno.  ⇒ Oggi il ritardo noto sul filo NON esiste.

⭐ La cura che NON si e' presa: ricompilare una copia del prodotto con
   l'attesa dentro `figlio.c:2248`.  Sarebbe stata onesta (li' aspettare e'
   lecito, `src/figlio.c:1470-1472`) ma avrebbe misurato **un prodotto diverso
   da quello che si consegna**, e lo step 5 ha il divieto di toccare `src/*`.

⭐ La cura presa: un **ritardatore di pacchetti**, cioe' un ponte UDP+TCP che
   sta davanti al prodotto e ritarda di N ms **la sola direzione
   server → cliente**.  Le tre proprieta' che lo rendono un P1 vero:

     a) il punto d'iniezione sta **a valle di `t0`** (il `pts` di Mutter, preso
        in `figlio.c:2248`, e ancora piu' a monte l'istante dipinto nella
        marca) e **a monte dell'arrivo** in pagina ⇒ la differenza t1−t0 DEVE
        salire di esattamente N;
     b) ⛔ **non tocca l'ancora dell'orologio**, che viaggia su una porta a
        parte (§2 qui sotto).  Se la toccasse, un ponte che ritarda tutto
        sposterebbe anche l'ancora e la mediana salirebbe di N/2 o di zero —
        cioe' P1 passerebbe **anche a banco rotto**.  E' la trappola che questo
        file esiste per non prendere;
     c) e' **fuori dal prodotto**: nessun byte di `src/` cambia, e il binario
        misurato e' quello che si consegna.

⚠ E il prezzo si dichiara: quel che si ritarda e' **il filo**, non la CPU del
  server.  Un P1 sul filo NON distinguerebbe un banco che, invece del `pts`,
  usasse come `t0` **l'istante in cui il server ha spedito** — ma distingue
  quello che usasse **l'arrivo**, che e' l'errore vero e quello che v1 ha
  pagato.  ⇒ Il controllo P1b (qui sotto, `--fuori-ordine`) copre il resto.

── 2. L'ANCORA DELL'OROLOGIO ──────────────────────────────────────────────────

⛔ Il ritardo attraversa DUE MACCHINE: `t0` e' `CLOCK_MONOTONIC` del server
   (192.168.0.2), `t1` e' `performance.now()` del browser su CHUWI.  Due
   orologi monotoni di due macchine **non hanno nessuna relazione**: sottrarli
   direttamente da' un numero che sembra un ritardo e non lo e'.  ⚠ E
   `src/pagina.html:1439-1441` lo dice gia': «`istante` e' un orologio MONOTONO
   del server: non si confronta col nostro».

⭐ L'ancora e' un'andata-e-ritorno alla NTP su una porta a parte: il cliente
   segna `a` (monotono di CHUWI), chiede, il server risponde col proprio
   monotono `s`, il cliente segna `b`.  Allora

       scarto = s − (a + b)/2        errore ≤ (b − a)/2

   e si tiene il campione col **giro piu' corto**, non la media: su LAN il giro
   minimo e' qualche decimo di millisecondo, quindi l'errore dell'ancora e'
   qualche decimo di millisecondo su un tetto di 50.  ⛔ E si dichiara: e' un
   pezzo del conto dell'errore, non una comodita'.

⛔ E la deriva NON si suppone: si misura all'inizio E alla fine, e se i due
   scarti differiscono si interpola sul tempo.  Due orologi al quarzo derivano
   di ~10-50 ppm, cioe' 0,5-2,5 ms su una misura di 50 s: sarebbe un errore
   grande quanto la meta' del traguardo.

── 3. IL FUORI ORDINE (controllo P5) ──────────────────────────────────────────

`web.md` §6.3: «i fotogrammi arrivano su stream indipendenti: un anello che non
lo regge misura la coda invece del ritardo».

⛔⭐ E LA PRIMA STESURA DI QUESTO PEZZO NON FABBRICAVA NIENTE — `[M]` 13 agosto
    2026.  Scambiava due datagram consecutivi, e sul filo vero questo **non
    produce nessun fuori ordine di fotogrammi**: QUIC riordina dentro lo
    stream, e il fotogramma esce dalla pagina quando lo stream si CHIUDE
    (`src/pagina.html:2570`).  Misurato: **0 scavalcati su 200**, cioe' un P5
    verde per costruzione — la cosa che questo banco esiste per non fare.

⭐ La forma che funziona: `fuori_ordine=N` **trattiene un pacchetto ogni N per
   `fuori_ordine_ms` (60 di riposo)**.  Lo stream a cui quel pacchetto
   appartiene chiude in ritardo, e gli stream successivi lo scavalcano davvero
   — che e' lo stesso meccanismo del fuori ordine VERO, quello che nasce dalla
   DIMENSIONE del fotogramma (`src/webtransport.c:1224-1240`: la chiave grossa
   resta in coda e i delta le passano davanti).

⚠ Resta un gemello sintetico e si dichiara: il ritardo lo mette il ponte, non
  il codificatore.  Serve a dire se l'anello REGGE, non quanto spesso accade.

── ⛔ QUEL CHE QUESTO FILE NON E' ─────────────────────────────────────────────

Non e' un pezzo del prodotto e non entra in nessun pacchetto.  ⚠ E non e'
trasparente per definizione: **quanto costa il ponte si MISURA**, girando la
stessa misura con e senza.  Un ponte creduto trasparente e' un errore
sistematico che si somma a ogni numero della fase.
"""
import argparse
import errno
import heapq
import json
import os
import socket
import struct
import sys
import threading
import time

MAGIA_OROLOGIO = b"RMXT"      # 4 byte, perche' un servizio qualunque che
                              # risponde non passi per l'ancora (LEZIONI §1.9)
VERSIONE = 1


def mono_us():
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC) // 1000


def reale_us():
    return time.clock_gettime_ns(time.CLOCK_REALTIME) // 1000


# ═══════════════════════════════════════════════════════════════════════════
# L'ANCORA DELL'OROLOGIO
# ═══════════════════════════════════════════════════════════════════════════
class Orologio(threading.Thread):
    """Risponde col proprio CLOCK_MONOTONIC.  Un pacchetto, una risposta.

    ⛔ Il formato porta la magia E la versione: un servizio che rispondesse
       qualcosa d'altro darebbe uno scarto plausibile e falso, ed e' proprio la
       forma d'errore che un'ancora non puo' permettersi (e' il numero su cui
       poggia TUTTA la misura).
    """

    def __init__(self, porta, indirizzo="0.0.0.0"):
        super().__init__(daemon=True)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((indirizzo, porta))
        self.s.settimeout(0.5)
        self.vivo = True
        self.risposte = 0

    def run(self):
        while self.vivo:
            try:
                d, chi = self.s.recvfrom(64)
            except socket.timeout:
                continue
            except OSError:
                break
            if len(d) < 12 or d[:4] != MAGIA_OROLOGIO:
                continue                      # non e' per noi: si tace
            # ⛔ L'ora si prende ADESSO, non dopo aver composto la risposta.
            ora = mono_us()
            gettone = d[8:12]
            try:
                self.s.sendto(MAGIA_OROLOGIO + struct.pack("!I", VERSIONE)
                              + gettone + struct.pack("!Q", ora), chi)
                self.risposte += 1
            except OSError:
                pass

    def ferma(self):
        self.vivo = False
        try:
            self.s.close()
        except OSError:
            pass


def orologio_chiedi(host, porta, campioni=200, pausa_s=0.002, attesa_s=1.0):
    """⭐ Lo scarto fra il monotono di QUI e quello di LA', col giro piu' corto.

    Ritorna un dizionario, e ⛔ SEMPRE con `c_e`: «non ho potuto chiedere» e
    «lo scarto e' zero» non hanno lo stesso aspetto (`LEZIONI.md` §1.9).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(attesa_s)
    migliore = None
    tutti = []
    persi = 0
    for i in range(campioni):
        gettone = struct.pack("!I", i)
        a = mono_us()
        try:
            s.sendto(MAGIA_OROLOGIO + struct.pack("!I", VERSIONE) + gettone,
                     (host, porta))
            d, _ = s.recvfrom(64)
        except (socket.timeout, OSError):
            persi += 1
            continue
        b = mono_us()
        # 4 magia + 4 versione + 4 gettone + 8 ora = 20 byte
        if len(d) != 20 or d[:4] != MAGIA_OROLOGIO or d[8:12] != gettone:
            persi += 1
            continue
        (ver,) = struct.unpack("!I", d[4:8])
        if ver != VERSIONE:
            s.close()
            return {"c_e": False,
                    "perche": "⛔ l'ancora risponde versione %d, questo cliente "
                              "parla la %d: gli scarti non sarebbero "
                              "confrontabili" % (ver, VERSIONE)}
        (la,) = struct.unpack("!Q", d[12:20])
        giro = b - a
        scarto = la - (a + b) // 2
        tutti.append((giro, scarto, (a + b) // 2))
        if migliore is None or giro < migliore[0]:
            migliore = (giro, scarto, (a + b) // 2)
        if pausa_s:
            time.sleep(pausa_s)
    s.close()
    if migliore is None:
        return {"c_e": False,
                "perche": "⛔ l'ancora non ha risposto a nessuno dei %d "
                          "tentativi verso %s:%d.  ⚠ Non e' «scarto zero»: e' "
                          "«non ho potuto guardare»" % (campioni, host, porta)}
    giri = sorted(g for g, _, _ in tutti)
    return {"c_e": True,
            "scarto_us": migliore[1],
            # ⛔ L'errore dell'ancora e' META' del giro piu' corto, e si porta
            #    dietro ogni numero che ne discende.
            "errore_us": migliore[0] // 2,
            "giro_minimo_us": giri[0],
            "giro_mediano_us": giri[len(giri) // 2],
            "ancora_a_us": migliore[2],
            "campioni": len(tutti), "persi": persi}


def scarto_interpolato(a, b, quando_us):
    """Lo scarto al tempo `quando_us` (monotono di QUI), interpolando fra le
    due ancore.  ⛔ La deriva non si suppone: se le due ancore dicono numeri
    diversi, quella differenza E' la deriva, e va spalmata."""
    if not a.get("c_e"):
        return None, "l'ancora d'apertura non c'e'"
    if not b.get("c_e") or b["ancora_a_us"] == a["ancora_a_us"]:
        return a["scarto_us"], "una sola ancora: nessuna deriva corretta"
    f = (quando_us - a["ancora_a_us"]) / (b["ancora_a_us"] - a["ancora_a_us"])
    return (a["scarto_us"] + f * (b["scarto_us"] - a["scarto_us"])), None


def deriva_ppm(a, b):
    if not (a.get("c_e") and b.get("c_e")):
        return None
    dt = b["ancora_a_us"] - a["ancora_a_us"]
    if dt <= 0:
        return None
    return (b["scarto_us"] - a["scarto_us"]) * 1e6 / dt


# ═══════════════════════════════════════════════════════════════════════════
# IL RITARDATORE
# ═══════════════════════════════════════════════════════════════════════════
class Comando:
    """⛔ Il ritardo si cambia SENZA riaccendere il ponte, perche' riaccenderlo
    riaccenderebbe la sessione QUIC — e una misura che ricomincia da capo a
    ogni valore di N confronta distribuzioni prese in condizioni diverse.

    Il canale e' un file, riletto quando cambia `mtime`.  ⚠ Un file e non un
    socket: chi lancia da `ssh` non ha un socket comodo, e un file lo scrive
    anche `printf`.
    """

    def __init__(self, percorso):
        self.percorso = percorso
        self.mtime = None
        self.valori = {"ritardo_ms": 0.0, "fuori_ordine": 0,
                       "fuori_ordine_ms": 60.0, "fuori_ordine_raffica": 4,
                       "giro": "-"}

    def aggiorna(self):
        if not self.percorso:
            return False
        try:
            m = os.stat(self.percorso).st_mtime_ns
        except OSError:
            return False
        if m == self.mtime:
            return False
        self.mtime = m
        try:
            with open(self.percorso) as f:
                testo = f.read()
        except OSError:
            return False
        for riga in testo.splitlines():
            if "=" not in riga:
                continue
            k, _, v = riga.partition("=")
            k, v = k.strip(), v.strip()
            if k == "ritardo_ms":
                try:
                    self.valori["ritardo_ms"] = float(v)
                except ValueError:
                    pass
            elif k == "fuori_ordine":
                try:
                    self.valori["fuori_ordine"] = int(v)
                except ValueError:
                    pass
            elif k == "fuori_ordine_ms":
                try:
                    self.valori["fuori_ordine_ms"] = float(v)
                except ValueError:
                    pass
            elif k == "fuori_ordine_raffica":
                try:
                    self.valori["fuori_ordine_raffica"] = int(v)
                except ValueError:
                    pass
            elif k == "giro":
                self.valori["giro"] = v
        return True


class RitardatoreUdp(threading.Thread):
    """Il ponte UDP.  Cliente ⇄ [qui] ⇄ prodotto, col ritardo su UNA direzione.

    ⛔ Il ritardo si applica **solo** a prodotto → cliente.  Ritardarle
       tutt'e due farebbe salire la mediana di N e basta lo stesso, ma
       aggiungerebbe N anche al giro d'andata del controllo, e i due effetti
       non si separerebbero piu' guardando i numeri.
    """

    def __init__(self, porta_fuori, porta_dentro, comando, indirizzo="0.0.0.0",
                 dentro_host="127.0.0.1"):
        super().__init__(daemon=True)
        self.cmd = comando
        self.dentro = (dentro_host, porta_dentro)
        self.fuori = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.fuori.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.fuori.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 << 20)
        self.fuori.bind((indirizzo, porta_fuori))
        self.fuori.setblocking(False)
        self.verso_prodotto = {}     # (ip,porta) cliente -> socket verso il prodotto
        self.di_chi = {}             # fileno del socket -> indirizzo del cliente
        self.coda = []               # heap (quando_us, seq, socket, dati, dove)
        self.seq = 0
        self.trattenuto = None
        self.trattenuto_da_us = 0
        self.contatore_fo = 0
        # ⛔ Quanto si trattiene il pacchetto scelto: deve essere PIU' LUNGO
        #    dell'intervallo fra due fotogrammi (~40 ms qui), o lo stream
        #    ritardato chiude comunque prima del successivo e non scavalca
        #    nessuno.
        self.ritardo_fo_us = 60000
        # ⛔ Quanti pacchetti CONSECUTIVI si trattengono: devono bastare a
        #    coprire un fotogramma intero (2-3 pacchetti da 1200 byte per un
        #    delta da ~2,6 KB), o si ritarda mezzo fotogramma e non scavalca
        #    nessuno.
        self.raffica_lunga = 4
        self.raffica = 0
        self.ultima_lettura_comando = 0.0
        self.vivo = True
        self.c = {"su": 0, "giu": 0, "byte_su": 0, "byte_giu": 0,
                  "ritardati": 0, "scambiati": 0, "clienti": 0}
        # ⛔ La precisione del ritardo si MISURA: «ho chiesto N» e «ho fatto N»
        #    non sono la stessa cosa, e un ponte che sbaglia di 5 ms su 30
        #    farebbe fallire P1 dando la colpa alla pagina.
        self.scarti_us = []

    def _socket_per(self, chi):
        s = self.verso_prodotto.get(chi)
        if s is None:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 << 20)
            s.setblocking(False)
            self.verso_prodotto[chi] = s
            self.di_chi[s.fileno()] = chi
            self.c["clienti"] += 1
        return s

    def _consegna(self, quando_us, dati, chi):
        self.seq += 1
        heapq.heappush(self.coda, (quando_us, self.seq, dati, chi))

    def run(self):
        import select
        while self.vivo:
            # ⛔ Il file del comando si guarda 10 volte al secondo, non a ogni
            #    giro: uno `stat()` per pacchetto e' una syscall in mezzo al
            #    percorso che si sta misurando, cioe' ritardo NOSTRO dentro il
            #    numero altrui.
            adesso = time.monotonic()
            if adesso - self.ultima_lettura_comando > 0.1:
                self.ultima_lettura_comando = adesso
                self.cmd.aggiorna()
            ritardo_us = int(self.cmd.valori["ritardo_ms"] * 1000)
            fo = self.cmd.valori["fuori_ordine"]
            self.ritardo_fo_us = int(self.cmd.valori.get("fuori_ordine_ms", 60) * 1000)
            self.raffica_lunga = int(self.cmd.valori.get("fuori_ordine_raffica", 4))

            letti = [self.fuori] + list(self.verso_prodotto.values())
            # ⛔ L'attesa si accorcia se c'e' roba in coda: dormire 5 ms con un
            #    pacchetto che scade fra 1 ms lo consegnerebbe con 4 ms di
            #    ritardo NOSTRO, dentro la misura del ritardo altrui.
            attesa = 0.002
            if self.coda:
                attesa = max(0.0, min(attesa,
                                      (self.coda[0][0] - mono_us()) / 1e6))
            try:
                pronti, _, _ = select.select(letti, [], [], attesa)
            except (OSError, ValueError):
                pronti = []

            for s in pronti:
                if s is self.fuori:
                    try:
                        d, chi = self.fuori.recvfrom(65535)
                    except OSError:
                        continue
                    # ⭐ Cliente → prodotto: NESSUN ritardo, e subito.
                    try:
                        self._socket_per(chi).sendto(d, self.dentro)
                        self.c["su"] += 1
                        self.c["byte_su"] += len(d)
                    except OSError:
                        pass
                else:
                    try:
                        d, _ = s.recvfrom(65535)
                    except OSError:
                        continue
                    chi = self.di_chi.get(s.fileno())
                    if chi is None:
                        continue
                    if fo:
                        # ⛔⭐ IL FUORI ORDINE VERO SI FA CON UN RITARDO GRANDE
                        #     SU UN PACCHETTO SOLO — e la prima stesura non lo
                        #     faceva.  `[M]` 13 agosto 2026.
                        #
                        #     Scambiare due datagram consecutivi non produce
                        #     nessun fuori ordine di FOTOGRAMMI: QUIC riordina
                        #     dentro lo stream, e il fotogramma esce dalla
                        #     pagina quando lo stream si CHIUDE
                        #     (`src/pagina.html:2570`, `:2594`).  Risultato: 0
                        #     scavalcati su 200, cioe' un P5 **verde per
                        #     costruzione** — che e' peggio di un rosso.
                        #
                        #     ⭐ Il fuori ordine vero nasce dalla DIMENSIONE:
                        #        un fotogramma grosso finisce dopo i piccoli
                        #        che lo seguono.  Lo si riproduce trattenendo
                        #        UN pacchetto ogni N per DECINE di ms: lo
                        #        stream a cui appartiene chiude in ritardo, e
                        #        gli stream successivi lo scavalcano davvero.
                        # ⛔ E NEMMENO «UN PACCHETTO OGNI N» BASTA — secondo
                        #    rosso, 13 agosto 2026.  Un fotogramma pesa 2-3
                        #    pacchetti: ritardandone uno ogni tre si ritardano
                        #    TUTTI i fotogrammi allo stesso modo, e nessuno
                        #    scavalca nessuno.  Misurato: 0 su 220.
                        #
                        # ⭐ Quel che scavalca davvero: si trattiene una RAFFICA
                        #    di pacchetti consecutivi — cioe' **un fotogramma
                        #    intero** — mentre tutti gli altri passano dritti.
                        #    Quello stream chiude in ritardo e i successivi gli
                        #    passano davanti: e' lo stesso meccanismo della
                        #    chiave grossa scavalcata dai delta.
                        self.contatore_fo += 1
                        if self.raffica > 0:
                            self.raffica -= 1
                            self._consegna(mono_us() + ritardo_us
                                           + self.ritardo_fo_us, d, chi)
                            self.c["scambiati"] += 1
                            continue
                        if self.contatore_fo % fo == 0:
                            self.raffica = self.raffica_lunga - 1
                            self._consegna(mono_us() + ritardo_us
                                           + self.ritardo_fo_us, d, chi)
                            self.c["scambiati"] += 1
                            continue
                    if ritardo_us <= 0:
                        self._spedisci_giu(d, chi, 0)
                    else:
                        self._consegna(mono_us() + ritardo_us, d, chi)
                        self.c["ritardati"] += 1

            ora = mono_us()
            # ⛔ UN PACCHETTO TRATTENUTO SI RILASCIA COMUNQUE, E QUESTA RIGA E'
            #    NATA DA UN ROSSO DELLA CERTIFICAZIONE: senza, l'ULTIMO
            #    pacchetto del flusso resta in mano al ponte per sempre —
            #    39 su 40 al giro di prova.  Su QUIC un pacchetto perso non e'
            #    un fuori ordine: e' una perdita, e falserebbe P5 con un
            #    fenomeno diverso da quello che P5 vuole provare.
            if self.trattenuto is not None and ora - self.trattenuto_da_us > 20000:
                t, tchi = self.trattenuto
                self.trattenuto = None
                self._spedisci_giu(t, tchi, 0)
            while self.coda and self.coda[0][0] <= ora:
                quando, _, d, chi = heapq.heappop(self.coda)
                self._spedisci_giu(d, chi, ora - quando)

    def _spedisci_giu(self, d, chi, scarto_us):
        try:
            self.fuori.sendto(d, chi)
            self.c["giu"] += 1
            self.c["byte_giu"] += len(d)
            if len(self.scarti_us) < 200000:
                self.scarti_us.append(scarto_us)
        except OSError as e:
            if e.errno not in (errno.ECONNREFUSED,):
                pass

    def ferma(self):
        self.vivo = False


class PonteTcp(threading.Thread):
    """Il ponte TCP, SENZA ritardo: serve solo a far arrivare la pagina e
    `/impronta` dalla stessa `location.host` da cui la pagina aprira'
    WebTransport (`src/pagina.html:2015`).

    ⛔ Senza questo, la pagina caricata da :7615 aprirebbe WebTransport verso
       :7615 e il ritardatore non vedrebbe un byte del video: il banco sarebbe
       verde e non misurerebbe niente.
    """

    def __init__(self, porta_fuori, porta_dentro, indirizzo="0.0.0.0",
                 dentro_host="127.0.0.1"):
        super().__init__(daemon=True)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((indirizzo, porta_fuori))
        self.s.listen(16)
        self.s.settimeout(0.5)
        self.dentro = (dentro_host, porta_dentro)
        self.vivo = True
        self.connessioni = 0

    def run(self):
        while self.vivo:
            try:
                c, _ = self.s.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self.connessioni += 1
            threading.Thread(target=self._serve, args=(c,), daemon=True).start()

    def _serve(self, c):
        try:
            d = socket.create_connection(self.dentro, timeout=10)
        except OSError:
            c.close()
            return
        for a, b in ((c, d), (d, c)):
            threading.Thread(target=self._travasa, args=(a, b), daemon=True).start()

    @staticmethod
    def _travasa(a, b):
        try:
            while True:
                p = a.recv(65536)
                if not p:
                    break
                b.sendall(p)
        except OSError:
            pass
        finally:
            for s in (a, b):
                try:
                    s.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    s.close()
                except OSError:
                    pass

    def ferma(self):
        self.vivo = False
        try:
            self.s.close()
        except OSError:
            pass


# ═══════════════════════════════════════════════════════════════════════════
# LA CERTIFICAZIONE DEL PONTE — ⭐ gira da sola, su loopback, senza server
# ═══════════════════════════════════════════════════════════════════════════
def _stat(v):
    if not v:
        return None
    v = sorted(v)
    def q(p):
        return v[min(len(v) - 1, max(0, int(round(p * (len(v) - 1)))))]
    return {"n": len(v), "min": v[0], "p05": q(0.05), "mediana": q(0.5),
            "p95": q(0.95), "max": v[-1]}


def certifica(verboso=True):
    """⛔ Il ponte si certifica PRIMA di essere creduto (`LEZIONI.md` §1.2), e a
    TRE giri: sano → guasto → risanato.

    Il «guasto» qui e' il ritardo chiesto: un ponte che non ritarda e' un ponte
    che dice sempre la stessa cosa, e un P1 fatto con lui sarebbe verde per
    costruzione.
    """
    esiti = []

    def dice(t, buono):
        esiti.append({"controllo": t, "esito": bool(buono)})
        if verboso:
            print(("    \033[1;32mOK\033[0m  " if buono
                   else "    \033[1;31mNO\033[0m  ") + t)

    # ── un eco UDP che fa da «prodotto» ────────────────────────────────────
    eco = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    eco.bind(("127.0.0.1", 0))
    porta_eco = eco.getsockname()[1]
    eco.settimeout(0.3)
    fermo = threading.Event()

    def gira_eco():
        while not fermo.is_set():
            try:
                d, chi = eco.recvfrom(65535)
            except (socket.timeout, OSError):
                continue
            try:
                eco.sendto(d, chi)
            except OSError:
                pass

    threading.Thread(target=gira_eco, daemon=True).start()

    cmdf = os.path.join(os.environ.get("TMPDIR", "/tmp"),
                        "03-b17-certifica-comando-%d" % os.getpid())
    with open(cmdf, "w") as f:
        f.write("ritardo_ms=0\n")
    cmd = Comando(cmdf)
    cmd.aggiorna()
    ponte = RitardatoreUdp(0, porta_eco, cmd, indirizzo="127.0.0.1")
    porta_ponte = ponte.fuori.getsockname()[1]
    ponte.start()

    def misura_giro(quanti=120):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2.0)
        v = []
        for i in range(quanti):
            a = mono_us()
            try:
                s.sendto(b"x" * 200 + struct.pack("!I", i),
                         ("127.0.0.1", porta_ponte))
                s.recvfrom(65535)
            except (socket.timeout, OSError):
                continue
            v.append(mono_us() - a)
            time.sleep(0.004)
        s.close()
        return v

    def metti(ritardo_ms):
        with open(cmdf, "w") as f:
            f.write("ritardo_ms=%s\n" % ritardo_ms)
        # il ponte rilegge sul cambio di mtime: gli si da' un giro di ciclo
        time.sleep(0.15)

    # ── GIRO 1, SANO: il ponte passa i pacchetti, e costa poco ─────────────
    sano = _stat(misura_giro())
    dice("giro SANO: il ponte inoltra (%d giri, mediana %s us)"
         % ((sano or {}).get("n", 0), (sano or {}).get("mediana")),
         sano is not None and sano["n"] >= 100)
    # ⛔ La tolleranza si scrive sulla grandezza vera (`LEZIONI.md` §1.13): il
    #    ponte deve costare MOLTO meno del millisecondo su un tetto di 50, o
    #    entra nel numero come errore sistematico.
    dice("giro SANO: il ponte costa meno di 2 ms al p95 (p95 = %s us)"
         % (sano or {}).get("p95"),
         sano is not None and sano["p95"] < 2000)

    # ── GIRO 2, GUASTO: si chiede N e si pretende esattamente N ────────────
    guasti = []
    for n in (10, 30, 75):
        metti(n)
        g = _stat(misura_giro())
        salita = (g["mediana"] - sano["mediana"]) / 1000.0 if (g and sano) else None
        guasti.append({"chiesto_ms": n, "salita_ms": salita, "stat_us": g})
        dice("giro GUASTO %d ms: la mediana sale di %.2f ms (atteso %d ± 2)"
             % (n, salita if salita is not None else -1, n),
             salita is not None and abs(salita - n) <= 2.0)

    # ── GIRO 3, RISANATO: si toglie il ritardo e si torna al sano ──────────
    metti(0)
    risanato = _stat(misura_giro())
    torna = (risanato and sano
             and abs(risanato["mediana"] - sano["mediana"]) < 2000)
    dice("giro RISANATO: tolto il ritardo si torna al sano (%s us contro %s us)"
         % ((risanato or {}).get("mediana"), (sano or {}).get("mediana")), torna)

    # ── il fuori ordine ────────────────────────────────────────────────────
    with open(cmdf, "w") as f:
        f.write("ritardo_ms=0\nfuori_ordine=2\n")
    time.sleep(0.15)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1.0)
    ordine = []
    for i in range(40):
        s.sendto(struct.pack("!I", i) + b"y" * 100, ("127.0.0.1", porta_ponte))
        time.sleep(0.004)
    fine = time.time() + 1.5
    while time.time() < fine:
        try:
            d, _ = s.recvfrom(65535)
        except socket.timeout:
            break
        ordine.append(struct.unpack("!I", d[:4])[0])
    s.close()
    inversioni = sum(1 for a, b in zip(ordine, ordine[1:]) if b < a)
    dice("fuori ordine: %d inversioni su %d pacchetti tornati (attese > 0)"
         % (inversioni, len(ordine)), inversioni > 0)
    dice("fuori ordine: nessun pacchetto perso (%d su 40)" % len(ordine),
         len(ordine) == 40)

    # ── l'ancora dell'orologio, contro se stessa ───────────────────────────
    o = Orologio(0, indirizzo="127.0.0.1")
    porta_o = o.s.getsockname()[1]
    o.start()
    a = orologio_chiedi("127.0.0.1", porta_o, campioni=300, pausa_s=0.0)
    dice("ancora: risponde (%d campioni, giro minimo %s us)"
         % (a.get("campioni", 0), a.get("giro_minimo_us")), a.get("c_e"))
    # ⛔ Su loopback lo scarto VERO e' zero: e' il controllo positivo
    #    dell'ancora.  Se qui non desse ~0, ogni numero della fase sarebbe
    #    spostato di quell'errore senza che nessuno lo vedesse.
    dice("ancora: su loopback lo scarto e' ~0 (%s us, errore dichiarato %s us)"
         % (a.get("scarto_us"), a.get("errore_us")),
         a.get("c_e") and abs(a["scarto_us"]) <= max(200, a["errore_us"] * 3))
    # ⛔ E il gemello negativo: un'ancora che non c'e' deve dire «non ho potuto
    #    guardare», non «scarto zero» (`LEZIONI.md` §1.9).
    b = orologio_chiedi("127.0.0.1", 1, campioni=3, pausa_s=0, attesa_s=0.1)
    dice("ancora: un'ancora assente dice «non ho potuto», non «zero»",
         (not b.get("c_e")) and "non ho potuto" in b.get("perche", ""))
    o.ferma()

    ponte.ferma()
    fermo.set()
    time.sleep(0.1)
    eco.close()
    try:
        os.unlink(cmdf)
    except OSError:
        pass

    passati = sum(1 for e in esiti if e["esito"])
    return {"controlli": len(esiti), "passati": passati,
            "esiti": esiti, "sano_us": sano, "risanato_us": risanato,
            "guasti": guasti,
            "esito": "PROMOSSO" if passati == len(esiti) else "BOCCIATO"}


# ═══════════════════════════════════════════════════════════════════════════
def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--fuori", type=int, help="la porta che il browser apre")
    p.add_argument("--dentro", type=int, help="la porta su cui gira il prodotto")
    p.add_argument("--dentro-host", default="127.0.0.1")
    p.add_argument("--indirizzo", default="0.0.0.0")
    p.add_argument("--orologio", type=int, help="la porta dell'ancora")
    p.add_argument("--comando", help="il file da cui si rilegge il ritardo")
    p.add_argument("--verbale", help="dove scrivere i conti, ogni 2 s")
    p.add_argument("--orologio-chiedi", help="HOST:PORTA — chiede e stampa lo scarto")
    p.add_argument("--campioni", type=int, default=200)
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        r = certifica()
        print("\n  %s — %d controlli su %d"
              % (r["esito"], r["passati"], r["controlli"]))
        print(json.dumps(r, ensure_ascii=False))
        return 0 if r["esito"] == "PROMOSSO" else 1

    if a.orologio_chiedi:
        host, _, porta = a.orologio_chiedi.partition(":")
        print(json.dumps(orologio_chiedi(host, int(porta), a.campioni),
                         ensure_ascii=False))
        return 0

    if not (a.fuori and a.dentro):
        p.error("servono --fuori e --dentro (oppure --certifica)")

    cmd = Comando(a.comando)
    cmd.aggiorna()
    udp = RitardatoreUdp(a.fuori, a.dentro, cmd, a.indirizzo, a.dentro_host)
    tcp = PonteTcp(a.fuori, a.dentro, a.indirizzo, a.dentro_host)
    udp.start()
    tcp.start()
    oro = None
    if a.orologio:
        oro = Orologio(a.orologio, a.indirizzo)
        oro.start()
    print("ponte acceso: %s:%d -> %s:%d (udp+tcp)%s"
          % (a.indirizzo, a.fuori, a.dentro_host, a.dentro,
             ", ancora su %d" % a.orologio if a.orologio else ""),
          flush=True)
    try:
        while True:
            time.sleep(2)
            if a.verbale:
                d = dict(udp.c)
                d.update({"quando": time.strftime("%FT%T"),
                          "ritardo_ms": cmd.valori["ritardo_ms"],
                          "fuori_ordine": cmd.valori["fuori_ordine"],
                          "giro": cmd.valori["giro"],
                          "connessioni_tcp": tcp.connessioni,
                          "risposte_ancora": oro.risposte if oro else None,
                          # ⛔ «ho chiesto N» e «ho fatto N» sono due numeri.
                          "scarto_consegna_us": _stat(udp.scarti_us[-20000:])})
                tmp = a.verbale + ".tmp"
                with open(tmp, "w") as f:
                    json.dump(d, f, ensure_ascii=False)
                os.replace(tmp, a.verbale)
    except KeyboardInterrupt:
        pass
    finally:
        udp.ferma()
        tcp.ferma()
        if oro:
            oro.ferma()
    return 0


if __name__ == "__main__":
    sys.exit(principale())
