#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b78-apertura — QUANTO CI METTE UNA SESSIONE AD APRIRSI, QUANDO LA RETE PERDE.

⛔⭐ PERCHE' ESISTE.  `banchi/07-b64-rete.py`, profilo `7-perdita-10`, porta un
    `[M]` scritto come **esito**, non come guasto:

        «10 %: `[M]` la sessione non si apre affatto in 25 s»

    Quella riga non e' mai stata spiegata, e `DECISIONI.md` §3.1 punto 4 la
    riapre: *«una stretta di mano QUIC ha il PTO apposta per rimandare quel che
    si perde, e venticinque secondi non somigliano alla perdita, somigliano a
    qualcosa che non riprova»*.

⭐ E UN SI'/NO NON PUO' RISPONDERE.  `07-b64` a quel gradino guarda un solo
   numero — `ricevuti == 0` — e da quello non si distingue «non si e' aperta»
   da «si e' aperta e l'audio non e' arrivato» da «il cliente si e' arreso».
   ⇒ Qui si misura il **tempo di apertura**, a gradini, e diviso per **fasi**:
   una curva dice di che natura e' il fenomeno; un si'/no no.

═══════════════════════════════════════════════════════════════════════════
LE PREDIZIONI — SCRITTE PRIMA DI GIRARE (`LEZIONI.md` §1.11)
═══════════════════════════════════════════════════════════════════════════

I fatti letti nel codice, prima di qualunque misura:

  `[R]` `banchi/01-b3-cliente.py:1222`  `wait_connected()` ha **8 s**, non 25.
  `[R]` `banchi/01-b3-cliente.py:1224`  `cli.accettata` ha **8 s**.
  `[R]` `banchi/01-b3-cliente.py:1250`  `ECCOMI` ha 10 s (predefinito di
        `attendi`), `:1266` `AMMESSO` 20 s, `:1284` `SESSIONE` 10 s.
  `[R]` `banchi/07-b64-rete.py`  `--secondi` (predef. 25) e' `--resta`, cioe'
        **quanto la sessione resta aperta DOPO essersi aperta**; il tetto
        dell'ssh e' `secondi + 180`.  ⇒ ⛔ **«in 25 s» non e' mai stato il
        tempo concesso alla stretta di mano.**
  `[R]` `src/trasporto.c:544`  `ngtcp2_settings_default()` e nessuna riga
        nostra tocca `handshake_timeout` ⇒ resta `UINT64_MAX`, cioe'
        **nessun tetto alla stretta di mano dal lato server**;
        `initial_rtt` = 333 ms (`NGTCP2_DEFAULT_INITIAL_RTT`).
  `[R]` `src/trasporto.c:590`  `max_idle_timeout` = 30 000 ms.
  `[R]` `src/main.c:1379,1429`  il ciclo si riarma su `trasporto_attesa_ms()`
        (tetto 1000 ms) e chiama `trasporto_scaduti()` →
        `ngtcp2_conn_handle_expiry()`.  ⇒ il server **ha** un orologio per
        riprovare, e non e' sveglio solo quando arrivano pacchetti.
  `[R]` `src/trasporto.c:434`  **niente GSO**: un pacchetto per `sendto`.  ⇒ il
        `netem` butta pacchetti QUIC singoli, non mazzi.
  `[R]` `src/rcp.c:925-927`  `SOGLIA 3`, `FINESTRA` 5 min, `BAN_DURATA` 12 h —
        e il conto si muove **solo** su un verdetto di PAM per `CREDENZIALI`.
        Una stretta di mano che non finisce non arriva mai li'.
  `[R]` `banchi/07-b64-rete.py` `guasta()`  mette **due** filtri `u32`, `sport`
        e `dport`: su `lo` ogni pacchetto attraversa la disciplina **una volta
        sola**, ma l'andata la attraversa col `dport` e il ritorno col `sport`
        ⇒ **la perdita si paga sui due versi**: a giro `1-(1-p)²`, cioe' il
        **19 %** quando `p` = 10 %.

Da cui le cinque predizioni, una per ipotesi, e falsificabili:

  (a) **e' il cliente che si arrende.**  ⇒ Con un tetto largo (60 s per fase)
      la sessione si apre al 10 % di perdita, e la **mediana** del tempo di
      apertura sta **sotto i 3 s**; e almeno un giro su venti supera gli 8 s
      di `01-b3-cliente.py:1222` — cioe' il tetto e' il difetto.
  (b) **e' il ban di §4.4-bis.**  ⇒ Nel registro del server compare
      «BANNATO» / `TROPPI_TENTATIVI`, e il gradino **pulito** eseguito
      SUBITO DOPO un gradino cattivo fallisce anche lui.
  (c) **e' ngtcp2 che non riprova.**  ⇒ Il tempo di apertura al 10 % e'
      **piatto e lunghissimo** (decine di secondi, tutti i giri), e la traccia
      `tcpdump` mostra il cliente che insiste mentre dal server **non esce
      piu' niente**.
  (d) **e' il `netem` che si applica due volte.**  ⇒ `tc -s qdisc` conta
      `dropped/Sent` ≈ `p` (non `2p`) sulla singola disciplina, ma i pacchetti
      **contati sono quelli dei due versi**; e togliendo il filtro `sport`
      (solo andata) il tempo di apertura cala in modo netto.
  (e) **e' davvero la perdita.**  ⇒ Il tempo di apertura cresce **liscio** coi
      gradini, e i salti stanno sulla scala del PTO: prima del primo campione
      di RTT il PTO e' `2 × 333 ms` e raddoppia (0,67 · 1,33 · 2,67 · 5,33 s);
      dopo il primo campione, su `lo`, l'RTT e' ~0,1 ms e il PTO crolla a
      qualche decina di ms.  ⇒ per arrivare a **25 s** servirebbero quattro
      flight iniziali persi di fila, che al 10 % vale `1e-4`.

⛔ E il predicato del banco e' scritto qui, PRIMA: **al 10 % di perdita, su
   dieci giri, almeno nove devono aprire la sessione, e la mediana del tempo
   di apertura deve stare sotto i 5 s.**  Se passa, il `[M]` di `07-b64` era
   un difetto del banco.  Se non passa, il `[M]` resta e la curva dira'
   perche'.

═══════════════════════════════════════════════════════════════════════════
QUEL CHE E' USCITO — `[M]` 23 agosto 2026, porta 7932, Intel UHD 730
═══════════════════════════════════════════════════════════════════════════

⭐⭐ **IL `[M]` DI `07-b64` E' FALSO COME E' SCRITTO: al 10 % di perdita la
    sessione SI APRE, e ci mette poco piu' di un secondo.**

1. Il tempo di apertura fino ad `AMMESSO` (stretta di mano QUIC + CONNECT
   estesa + `CIAO/ECCOMI` + `CREDENZIALI/AMMESSO`), 10 giri per gradino, la
   perdita **letta** da `tc -s qdisc`, non dedotta:

   | perdita chiesta | perdita vera | aperte | QUIC mediana | totale mediana | totale max |
   |---|---|---|---|---|---|
   |  0 %  |  —      | 10/10 |   7,8 ms |  1014 ms | 1116 ms |
   |  5 %  |  8,2 %  | 10/10 |   7,8 ms |  1078 ms | 1318 ms |
   | 10 %  |  9,5 %  | 10/10 |  10,9 ms |  1103 ms | 1219 ms |
   | 15 %  | 15,2 %  | 10/10 | 111,5 ms |  1281 ms | 1708 ms |
   | 25 %  | 24,3 %  | 10/10 | 211,9 ms |  1299 ms | 1738 ms |

   ⚠ Il secondo che si vede in «totale» **non e' la rete**: e' il ritardo
     fisso di §4.4-bis.  ⇒ La rete costa, dallo 0 al 25 %, **285 ms**.
   ⭐ E i massimi della stretta di mano stanno a 212 e 613 ms, cioe' **uno e
      due PTO** di aioquic (0,2 s e 0,2+0,4 s): ⇒ **si riprova, e si vede il
      passo con cui si riprova.**  L'ipotesi (c) e' smentita da questi numeri.
   ⛔ **Zero giri su settanta** hanno superato gli 8 s di
      `01-b3-cliente.py:1222`: neanche l'ipotesi (a) regge.
   ⛔ Il ban non e' mai scattato (ban-file vuoto, nessun «BANNATO» nel
      registro): l'ipotesi (b) e' smentita.
   ⛔ `tc -s qdisc` dice che la disciplina e' UNA e la attraversa **un
      pacchetto per volta**: l'ipotesi (d) («applicata due volte») e' smentita.
      ⚠ Resta vero che i due filtri prendono i due VERSI, quindi un giro di
        rete paga `1-(1-p)²`; ma un datagram, che fa un verso solo, paga `p`.

2. La forma esatta di `07-b64` — il cliente vero, PCM, col tono acceso,
   `--resta 20` — al **10 %**:

       SESSIONE aperta: True
       [audio] ricevuti **3235** · 3 105 600 byte · codec 2
       SERVER: spediti 3607 · buttati 0 · **rifiutati 391** · rimandati 293 718
       giudizio: resa_campioni **0,810** · purezza 0,182 · scoppiettii 19,1/s

   ⇒ 3235/3607 = **89,7 % arrivato sul filo**, che e' esattamente il 10 %
     tolto una volta.  ⚠ E la `resa_campioni` scende a 0,810 perche' ci mette
     dentro anche i **391 blocchi che il server non ha MAI spedito** (finestra
     di congestione chiusa): «perso sul filo» e «mai spedito» sono due fatti, e
     la resa li somma.

3. ⛔⛔ **PERCHE' IL BANCO DICEVA IL CONTRARIO.**  Il predicato di quel gradino
   e' `a_non_si_apre(n) = (n["ricevuti"] == 0)`, e `01-b3-cliente.py` stampa
   `[audio] ricevuti 0` **anche dal ramo `except`** (`:1286`), prima di
   rilanciare.  ⇒ **Qualunque** modo di fallire — un `CONGEDO`, un tetto
   scaduto, un `NameError` del banco — produce «ricevuti 0» e fa passare quel
   gradino di VERDE.  E' un predicato che non puo' dare rosso, cioe' la forma
   di `LEZIONI.md` §1.9: non misurava «non si apre», misurava «non ho
   ricevuto», e le due cose hanno la stessa faccia.
   `[M]` verificato girando il cliente vero **senza tono**: `SESSIONE=True` a
   ogni giro, `[audio] ricevuti 0` a ogni giro, a 1 % come a 10 %.

4. ⭐⭐ **E DIETRO C'E' UN FATTO DEL PRODOTTO, ed e' sul bersaglio della fase.**
   L'unico modo in cui, sotto perdita, un'apertura fallisce davvero e':
   `ATTACCA` → `CONGEDO(0x0F) GIA_ATTIVA_REMOTA`, cioe' **il posto della
   sessione di prima e' ancora occupato**.  `[M]` nel primo giro di scala:
   5/10 al 10 %, 0/10 al 15 %, col registro che dice
   *«posto NEGATO a provanr3 … lo occupa un altro client di questo stesso
   utente (occupati: 1)»*.

   ⛔ E il conto si chiude **senza nessun `netem`**, perche' un addio
      **perso** e un addio **mai detto** sono lo stesso fatto per il server:
      si uccide il cliente con `-9` e si misura da quando il posto torna
      libero.  `[M]` 23 agosto 2026:

          + 1,6 s  CONGEDO 0x0F      + 17,3 s  CONGEDO 0x0F
          + 4,2 s  CONGEDO 0x0F      + 19,9 s  CONGEDO 0x0F
          + 6,8 s  CONGEDO 0x0F      + 22,5 s  CONGEDO 0x0F
          + 9,5 s  CONGEDO 0x0F      + 25,2 s  CONGEDO 0x0F
          +12,1 s  CONGEDO 0x0F      + 27,9 s  CONGEDO 0x0F
          +14,7 s  CONGEDO 0x0F      **+30,5 s  APERTA**

      ⇒ **30,5 s di serratura**, cioe' `SILENZIO` (`src/rcp.c:263`, 30 000 ms)
        piu' il giro.  Undici rifiuti di fila, e la frase che il client ne
        costruisce — «hai gia' una sessione attiva altrove» — per l'utente
        **e' falsa**: quella sessione e' la sua, ed e' morta.
      ⚠ Il riquadro di `src/rcp.c:229-233` dice che l'orologio del silenzio
        *«e' la regola che fa sparire il caso "il telefono e' morto in galleria
        e ora non posso rientrare"»*.  ⛔ Non lo fa sparire: lo **dura trenta
        secondi**, e la perdita di pacchetti e' quel che lo rende normale.

═══════════════════════════════════════════════════════════════════════════
L'ISOLAMENTO — ⛔ e per un banco che tocca la rete vale doppio
═══════════════════════════════════════════════════════════════════════════

  porta **7932** · utente **provanr3** (uid 1032) ·
  albero `/media/REMOTIX/src/09nr3-src` · lavoro `/media/REMOTIX/tmp/09nr3` ·
  unita' `remotix-7932.service`, ban-file e socket propri.

⛔ `enp7s0` (ssh e la 7730 dell'utente) **non si tocca mai**: il guasto sta su
   `lo`, con due filtri `u32` sulla **sola** porta 7932.
⛔ Le porte **7900, 7910, 7920** sono termini di paragone gia' misurati: si
   contano e non si toccano.
⛔ Il `netem` su `lo` e' **uno solo per la macchina**: si prende il lucchetto di
   `banchi/09-lucchetto.py`, si mollano affitti **corti**, e si molla in un
   `finally` — ci sono altri agenti in coda.
⛔ Il guardiano staccato toglie la disciplina anche se questo copione muore.

Uso (dal portatile):
    python3 banchi/09-b78-apertura.py scala   [--giri 10] [--fino wt]
    python3 banchi/09-b78-apertura.py un-verso              # ipotesi (d)
    python3 banchi/09-b78-apertura.py rimetti
    python3 banchi/09-b78-apertura.py stato

Uso (DENTRO il contenitore della macchina di prova — lo chiama `scala`):
    python3 banchi/09-b78-apertura.py dentro --porta 7932 --giri 10 ...
"""
import argparse, importlib.util, json, os, re, subprocess, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))

MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
IND = os.environ.get("IND", "192.168.0.2")
PORTA = int(os.environ.get("PORTA", "7932"))
UTENTE = os.environ.get("UTENTE", "provanr3")
UID_B = int(os.environ.get("UID_B", "1032"))
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/09nr3-src")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/09nr3")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/09nr3-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/09nr3")
FUORI = os.environ.get("FUORI", os.path.join(
    "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX-V2",
    "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad/09nr3"))

VIETATA = "enp7s0"        # ci passano l'ssh e la 7730 dell'utente
DEV = "lo"
VICINE = ("7700", "7730", "7900", "7910", "7920")

# I gradini.  ⭐ Non si parte dal 10 %: una scala dice di che natura e' il
#   fenomeno, un solo punto no.
GRADINI = [0, 1, 3, 5, 8, 10, 15]


# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE GIRA DENTRO IL CONTENITORE — misura UNA apertura per volta
# ═══════════════════════════════════════════════════════════════════════════

def dentro(a):
    """⛔ Le fasi si cronometrano UNA PER UNA, e con un tetto **largo**: il
       tetto stretto e' precisamente l'imputato (a), e un banco che lo ripete
       non lo puo' vedere.
       ⭐ E si registra DOVE si e' fermata, non solo che non si e' aperta:
          «QUIC non ha stretto la mano» e «il desktop non e' nato» sono due
          diagnosi opposte, e un booleano le confonde."""
    import asyncio, ssl, struct
    spec = importlib.util.spec_from_file_location(
        "b3", os.path.join(QUI, "01-b3-cliente.py"))
    b3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b3)

    from aioquic.asyncio.client import connect
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.h3.connection import H3_ALPN

    parola = open(a.parola_file).read().strip()
    autorita = "%s:%d" % (a.indirizzo, a.porta)

    async def un_giro():
        t = {}
        fermo = "prima-di-tutto"
        t0 = time.monotonic()

        def segna(nome):
            t[nome] = round((time.monotonic() - t0) * 1000, 1)

        conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                                 max_datagram_frame_size=65536)
        conf.verify_mode = ssl.CERT_NONE
        try:
            async with connect(a.indirizzo, a.porta, configuration=conf,
                               create_protocol=b3.Cliente) as cli:
                fermo = "quic"
                await asyncio.wait_for(cli.wait_connected(), timeout=a.tetto)
                segna("quic")
                if a.fino == "quic":
                    return t, "aperta", None
                fermo = "wt"
                cli.apri_sessione(autorita, a.percorso)
                stato = await asyncio.wait_for(cli.accettata, timeout=a.tetto)
                segna("wt")
                if stato != "200":
                    return t, "respinta", ":status = %s" % stato
                if a.fino == "wt":
                    return t, "aperta", None
                reg = b3.Registratore()
                reg.stream = cli.apri_controllo()
                cli.reg = reg
                fermo = "eccomi"
                cli.manda(b3.inquadra(b3.T["CIAO"], b3.corpo_ciao("pcm", "h264", "8,10")))
                await b3.attendi(cli, "ECCOMI", attesa=a.tetto)
                segna("eccomi")
                fermo = "ammesso"
                cli.manda(b3.inquadra(b3.T["CREDENZIALI"],
                                      b3.s(a.utente) + b3.s(parola)))
                await b3.attendi(cli, "AMMESSO", attesa=a.tetto)
                segna("ammesso")
                if a.fino == "ammesso":
                    return t, "aperta", None
                fermo = "sessione"
                cli.manda(b3.inquadra(
                    b3.T["ATTACCA"],
                    struct.pack("!IIII", 1920, 1080, 1920, 1080) + b3.s("it")))
                await b3.attendi(cli, "SESSIONE", attesa=a.tetto)
                segna("sessione")
                return t, "aperta", None
        except asyncio.TimeoutError:
            return t, "scaduta", "tetto di %g s scaduto in fase «%s»" % (a.tetto, fermo)
        except Exception as e:
            return t, "rotta", "%s in fase «%s»: %s" % (type(e).__name__, fermo, e)

    async def tutti():
        for i in range(a.giri):
            t, esito, perche = await un_giro()
            riga = {"giro": i, "tempi_ms": t, "esito": esito, "perche": perche}
            # ⛔⭐ IL POSTO NEGATO SI CRONOMETRA, non si conta.
            #
            #   `GIA_ATTIVA_REMOTA` vuol dire «il tuo posto e' ancora occupato
            #   dalla TUA sessione di prima»: e' uno stato che PASSA, e un
            #   si'/no lo fa sembrare un guasto permanente.  ⇒ Si riprova
            #   finche' il posto si libera, e il numero che esce e' **quanto
            #   dura la serratura** — che e' la cosa che l'utente subisce.
            if a.riprova_0f and esito == "rotta" and "0x0f" in (perche or ""):
                t_1 = time.monotonic()
                while time.monotonic() - t_1 < a.riprova_0f:
                    await asyncio.sleep(1.0)
                    t2, e2, p2 = await un_giro()
                    if e2 == "aperta":
                        riga["esito"] = "aperta-dopo-attesa"
                        riga["attesa_posto_ms"] = round(
                            (time.monotonic() - t_1) * 1000, 1)
                        riga["tempi_ms"] = t2
                        break
                    if not (e2 == "rotta" and "0x0f" in (p2 or "")):
                        riga["perche"] = p2
                        break
                else:
                    riga["attesa_posto_ms"] = -1   # ⛔ mai liberato nel tetto
            print("APERTURA " + json.dumps(riga, ensure_ascii=False), flush=True)
            if a.pausa:
                await asyncio.sleep(a.pausa)

    asyncio.get_event_loop().run_until_complete(tutti())
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE GIRA SUL PORTATILE
# ═══════════════════════════════════════════════════════════════════════════

def rem(comando, tetto=300):
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, comando],
                       capture_output=True, timeout=tetto)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def root(comando, tetto=300):
    return rem("printf '%%s\\n' '%s' | sudo -S -p '' %s" % (PAROLA_SUDO, comando),
               tetto)


def qdisc(stat=False):
    return root("/usr/sbin/tc %s qdisc show dev %s" % ("-s" if stat else "", DEV))[1]


GUARDIANO = LAV + "/.guardiano-b78.pid"


def guardiano_arma(secondi):
    guardiano_disarma()
    root('bash -c "setsid sh -c \'sleep %d; /usr/sbin/tc qdisc del dev %s root\' '
         '>/dev/null 2>&1 & echo \\$! > %s"' % (secondi, DEV, GUARDIANO))
    rc, out, _ = root("cat %s 2>/dev/null" % GUARDIANO)
    print("   OK  guardiano armato per %d s (pid %s): la rete torna com'era "
          "ANCHE se muoio" % (secondi, out.strip() or "?"))


def guardiano_disarma():
    rc, out, _ = root("cat %s 2>/dev/null || true" % GUARDIANO)
    p = out.strip()
    if p.isdigit():
        root("kill -TERM -%s 2>/dev/null; kill -TERM %s 2>/dev/null; true" % (p, p))
    root("rm -f %s; true" % GUARDIANO)


def rimetti(dillo=True, disarma=True):
    """⛔⭐ `disarma` NON e' una comodita'.  Il gradino «0 %» toglie la
       disciplina come tutti gli altri, e se togliendola disarmasse anche il
       guardiano, il giro proseguirebbe **senza rete di sicurezza**: da li' in
       poi una morte del copione lascerebbe la macchina col `netem` addosso, e
       il prossimo banco attribuirebbe al prodotto un guasto mio.
       ⚠ `banchi/07-b64-rete.py` ha questa forma: il suo profilo `0-liscio`
         chiama `rimetti(False)`, che disarma il guardiano armato due righe
         prima — e i sette profili dopo girano scoperti."""
    if disarma:
        guardiano_disarma()
    root("/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV)
    q = qdisc()
    ok = "netem" not in q
    if dillo:
        print("   %s la disciplina di «%s» adesso e': %s"
              % ("OK " if ok else "NO ", DEV, q.strip() or "(nessuna)"))
        print("   --  %s (ssh + 7730): %s"
              % (VIETATA, root("/usr/sbin/tc qdisc show dev %s"
                               % VIETATA)[1].split("\n")[0]))
    return ok


def guasta(perdita_pc, un_verso=False):
    """⛔ Il guasto, e SOLO sulla mia porta.  `un_verso` toglie il filtro
       `sport`: e' il controllo dell'ipotesi (d)."""
    if perdita_pc <= 0:
        rimetti(False, disarma=False)
        return True, "(nessun guasto)"
    passi = [
        "/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV,
        "/usr/sbin/tc qdisc add dev %s root handle 1: prio bands 4" % DEV,
        "/usr/sbin/tc qdisc add dev %s parent 1:4 handle 40: netem loss %g%%"
        % (DEV, perdita_pc),
        "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
        "match ip protocol 17 0xff match ip dport %d 0xffff flowid 1:4"
        % (DEV, PORTA),
    ]
    if not un_verso:
        passi.append(
            "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
            "match ip protocol 17 0xff match ip sport %d 0xffff flowid 1:4"
            % (DEV, PORTA))
    for c in passi:
        rc, out, err = root(c)
        if rc != 0 and "del dev" not in c:
            rimetti()
            return False, "⛔ tc ha rifiutato «%s»: %s" % (c[-60:], err[:200])
    return True, qdisc().strip()


def netem_conti():
    """⛔ La perdita che il `netem` ha DAVVERO applicato, letta — non dedotta."""
    out = qdisc(stat=True)
    dentro_netem = False
    for riga in out.split("\n"):
        if riga.startswith("qdisc netem"):
            dentro_netem = True
            continue
        if dentro_netem and "Sent" in riga:
            m = re.search(r"Sent (\d+) bytes (\d+) pkt \(dropped (\d+)", riga)
            if m:
                sped, pkt, but = int(m.group(1)), int(m.group(2)), int(m.group(3))
                tot = pkt + but
                return {"pkt_passati": pkt, "pkt_buttati": but,
                        "frazione_vera": round(but / tot, 4) if tot else None}
            break
        if dentro_netem and riga.startswith("qdisc"):
            break
    return {"pkt_passati": None, "pkt_buttati": None, "frazione_vera": None}


def ban_scattato(riga0):
    """⛔ Fra un giro e l'altro: o si attribuisce al 15 % un guasto del 10 %."""
    rc, out, _ = root("tail -n +%d %s/registro.log 2>/dev/null | "
                      "grep -ac 'BANNATO' || true" % (riga0 + 1, LAV))
    n = out.strip()
    rc2, out2, _ = root("test -s %s/ban && cat %s/ban || echo '(vuoto)'" % (LAV, LAV))
    return (n not in ("", "0")), out2.strip()[:200]


def righe_registro():
    rc, out, _ = root("wc -l < %s/registro.log 2>/dev/null || echo 0" % LAV)
    try:
        return int(out.strip())
    except Exception:
        return 0


def vicine():
    fuori = []
    for p in VICINE:
        rc, o, _ = root("ss -uln 2>/dev/null | grep -c ':%s ' || true" % p)
        fuori.append("%s:%s" % (p, o.strip()))
    return " ".join(fuori)


def spedisci():
    """⛔ Questo copione — e il cliente da cui prende la classe `Cliente` —
       devono essere DENTRO l'albero, o il contenitore non li vede.

    ⛔⭐ E `01-b3-cliente.py` SI RISPEDISCE A OGNI GIRO, e la sua impronta si
        stampa.  `[M]` 23 agosto 2026: la copia nell'albero era rimasta
        indietro di una modifica (`REGOLA_AUDIO` non esisteva ancora) e il
        primo giro e' morto con un `NameError` in fase «prima-di-tutto» —
        cioe' con la faccia di «la sessione non si apre».  ⚠ Quel file oggi lo
        modifica un altro agente: chi misura deve DICHIARARE con quale copia
        ha misurato, o il numero non e' rifacibile."""
    fuori = []
    for f in ("09-b78-apertura.py", "01-b3-cliente.py"):
        p = subprocess.run(
            "cat %s | ssh -o BatchMode=yes %s \"cat > %s/banchi/%s\""
            % (os.path.join(QUI, f), MACCHINA, ALB, f), shell=True,
            capture_output=True)
        if p.returncode != 0:
            return None
        h = subprocess.run(["md5sum", os.path.join(QUI, f)],
                           capture_output=True).stdout.decode().split()[0]
        fuori.append("%s %s" % (h[:8], f))
    return fuori


def misura(giri, fino, tetto, pausa=0.0, riprova=0.0):
    dcmd = ("python3 -u %s/banchi/09-b78-apertura.py dentro "
            "--indirizzo %s --porta %d --utente %s --parola-file %s/parola "
            "--giri %d --fino %s --tetto %g --pausa %g --riprova-0f %g"
            % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, giri, fino, tetto,
               pausa, riprova))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dcmd,
                        int(giri * (tetto + pausa + riprova) + 300))
    righe = []
    for r in (out + err).splitlines():
        if r.startswith("APERTURA "):
            try:
                righe.append(json.loads(r[9:]))
            except Exception:
                pass
    return righe, (out + err)[-800:]


def mediana(v):
    v = sorted(v)
    if not v:
        return None
    n = len(v)
    return v[n // 2] if n % 2 else round((v[n // 2 - 1] + v[n // 2]) / 2, 1)


def riassumi(righe, fino):
    aperte = [r for r in righe if r["esito"].startswith("aperta")]
    subito = [r for r in righe if r["esito"] == "aperta"]
    serrate = [r.get("attesa_posto_ms") for r in righe
               if r.get("attesa_posto_ms") is not None]
    fase = {"quic": "quic", "wt": "wt", "ammesso": "ammesso",
            "sessione": "sessione"}[fino]
    tot = [r["tempi_ms"].get(fase) for r in aperte if r["tempi_ms"].get(fase)]
    quic = [r["tempi_ms"].get("quic") for r in aperte if r["tempi_ms"].get("quic")]
    # ⭐ E il numero che accusa o assolve `01-b3-cliente.py`: quanti giri
    #    avrebbero sfondato il suo tetto di 8 s sulla stretta di mano QUIC.
    oltre8 = len([x for x in quic if x > 8000])
    return {"giri": len(righe), "aperte": len(aperte), "aperte_subito": len(subito),
            "quic_mediana_ms": mediana(quic), "quic_max_ms": max(quic) if quic else None,
            "tot_mediana_ms": mediana(tot), "tot_max_ms": max(tot) if tot else None,
            "quic_oltre_8s": oltre8,
            "posto_serrato_ms": serrate,
            "guai": [r["perche"] for r in righe
                     if not r["esito"].startswith("aperta")][:3]}


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", choices=["scala", "un-verso", "dentro", "rimetti", "stato"])
    p.add_argument("--giri", type=int, default=10)
    p.add_argument("--fino", default="wt", choices=["quic", "wt", "ammesso", "sessione"])
    p.add_argument("--tetto", type=float, default=60.0)
    p.add_argument("--pausa", type=float, default=0.0)
    p.add_argument("--gradini", default="")
    # gli argomenti della meta' «dentro»
    p.add_argument("--indirizzo", default=IND)
    p.add_argument("--porta", type=int, default=PORTA)
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default=UTENTE)
    p.add_argument("--parola-file", default="")
    p.add_argument("--riprova-0f", type=float, default=0, metavar="SECONDI",
                   help="⭐ dopo un CONGEDO(0x0F) riprova fino a N s e "
                        "cronometra QUANTO DURA la serratura del posto")
    a = p.parse_args()

    if a.passo == "dentro":
        return dentro(a)

    os.makedirs(FUORI, exist_ok=True)

    if a.passo in ("rimetti", "stato"):
        print("== la rete della macchina di prova")
        print("   --  ascoltatori NON miei (si contano, non si toccano): %s" % vicine())
        return 0 if rimetti() else 2

    gradini = ([float(x) for x in a.gradini.split(",")] if a.gradini
               else ([0, 10] if a.passo == "un-verso" else GRADINI))
    un_verso = (a.passo == "un-verso")

    print("== 09-b78 · IL TEMPO DI APERTURA CONTRO LA PERDITA — porta %d" % PORTA)
    print("   ⛔ «%s» (ssh + 7730) NON si tocca; il guasto sta su «%s», "
          "filtri sulla sola %d" % (VIETATA, DEV, PORTA))
    print("   --  ascoltatori NON miei: %s" % vicine())
    if un_verso:
        print("   ⭐ UN VERSO SOLO (solo `dport`): e' il controllo dell'ipotesi (d)")
    print("   --  gradini: %s %%   giri: %d   fino a: «%s»   tetto: %g s"
          % (gradini, a.giri, a.fino, a.tetto))

    impronte = spedisci()
    if not impronte:
        print("   NO  i copioni non sono arrivati nell'albero: non misuro")
        return 2
    print("   --  misurato con: %s" % " · ".join(impronte))

    luc = importlib.util.spec_from_file_location(
        "luc", os.path.join(QUI, "09-lucchetto.py"))
    lucchetto = importlib.util.module_from_spec(luc)
    luc.loader.exec_module(lucchetto)

    # ⛔ Affitto CORTO: ci sono altri agenti in coda.
    per_gradino = a.giri * ((a.tetto if a.fino != "wt" else 12)
                            + a.pausa + a.riprova_0f) + 60
    affitto = int(min(900, len(gradini) * per_gradino + 120))
    lucchetto.prendi("09-b78", secondi=affitto, attesa=2400)
    esiti = []
    try:
        guardiano_arma(affitto)
        for g in gradini:
            print("\n-- perdita %g %%" % g)
            riga0 = righe_registro()
            ok, q = guasta(g, un_verso)
            if not ok:
                print("   ", q)
                break
            print("   tc:", " ".join(q.split("\n")[:3])[:150])
            righe, coda = misura(a.giri, a.fino, a.tetto, a.pausa, a.riprova_0f)
            vero = netem_conti()
            bannato, banfile = ban_scattato(riga0)
            r = riassumi(righe, a.fino)
            r.update({"perdita_chiesta_pc": g, "netem": vero,
                      "ban_scattato": bannato, "ban_file": banfile,
                      "un_verso": un_verso})
            if not righe:
                r["coda"] = coda
            esiti.append(r)
            print("   ", json.dumps(r, ensure_ascii=False))
            if bannato:
                print("   ⛔ IL BAN E' SCATTATO: mi fermo, o attribuirei al "
                      "gradino dopo un guasto di questo")
                break
    finally:
        print("\n== ⛔ LA RETE SI RIMETTE COM'ERA")
        rimetti()
        lucchetto.molla("09-b78")

    nome = "apertura-un-verso.json" if un_verso else "apertura-scala.json"
    json.dump(esiti, open(os.path.join(FUORI, nome), "w"),
              ensure_ascii=False, indent=1)

    print("\n== LA TABELLA — tempo di apertura (fino a «%s») contro perdita" % a.fino)
    print("   %-8s %-9s %-8s %-11s %-11s %-9s %s"
          % ("perdita", "netem_vero", "subito+dopo/n", "quic_med", "tot_med",
             "tot_max", "oltre 8 s"))
    for e in esiti:
        print("   %-8s %-9s %-8s %-11s %-11s %-9s %s"
              % ("%g %%" % e["perdita_chiesta_pc"],
                 ("%.1f %%" % (100 * e["netem"]["frazione_vera"]))
                 if e["netem"]["frazione_vera"] is not None else "—",
                 "%d+%d/%d" % (e["aperte_subito"],
                               e["aperte"] - e["aperte_subito"], e["giri"]),
                 e["quic_mediana_ms"], e["tot_mediana_ms"], e["tot_max_ms"],
                 e["quic_oltre_8s"]))

    # ⛔ IL PREDICATO, scritto nel riquadro in testa PRIMA di girare.
    dieci = [e for e in esiti if e["perdita_chiesta_pc"] == 10]
    if not dieci:
        print("\n   ⚠  il gradino del 10 % non e' stato misurato: nessun verdetto")
        return 2
    e = dieci[0]
    passa = (e["aperte"] >= 0.9 * e["giri"]
             and e["tot_mediana_ms"] is not None and e["tot_mediana_ms"] < 5000)
    print("\n== IL VERDETTO SUL `[M]` DI 07-b64 (`7-perdita-10`)")
    if passa:
        print("   ⭐ al 10 %% la sessione SI APRE: %d/%d, mediana %.0f ms.  "
              "⇒ Il «non si apre affatto in 25 s» era un difetto del banco."
              % (e["aperte"], e["giri"], e["tot_mediana_ms"]))
        return 0
    print("   ⛔ al 10 %% la sessione NON si apre come previsto: %d/%d, "
          "mediana %s ms ⇒ il `[M]` regge, e la curva dice perche'"
          % (e["aperte"], e["giri"], e["tot_mediana_ms"]))
    return 1


if __name__ == "__main__":
    sys.exit(principale())
