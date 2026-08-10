#!/usr/bin/env python3
"""01-b6-tetti.py — ⛔ B6: i tre tetti della stretta di mano, misurati TACENDO.

    python3 01-b6-tetti.py --fase sani --idle 120000 --tetti-codice CIAO=5000,CREDENZIALI=60000,ATTACCA=10000
    python3 01-b6-tetti.py --fase ping --idle 15000
    python3 01-b6-tetti.py --elenco            (le previsioni, senza misurare)

⚠ Gira DENTRO il contenitore: aioquic sta li'.  Lo accende e lo lancia
  `01-b6-lancia.sh`, che e' anche l'unico posto in cui si sceglie il tetto
  d'inattivita' del trasporto — e questo file non lo presume mai: se lo fa
  dire, lo stampa, e ci costruisce sopra le diagnosi.

===========================================================================
⛔ CHE COSA MISURA, IN UNA RIGA D'UTENTE

*«Quanto ci mette a dirti che non ce l'ha fatta, invece di restare li'
appeso.»*  `RCP.md` §4.6 mette tre tetti alla stretta di mano perche' *«una
connessione che si ferma a meta' stretta di mano tiene un posto e non lo
dichiara a nessuno»*.  Questo banco fa esattamente quello: si ferma a meta' e
tace, tre volte, in tre punti diversi.

| Da | A | Tetto (§4.6) |
|---|---|---|
| l'inizio (⚠ e QUALE inizio e' la domanda `[?]` R3.27, vedi sotto) | `CIAO` | **5 s** |
| `ECCOMI` spedito | `CREDENZIALI` | **60 s** |
| `AMMESSO` spedito | `ATTACCA` | **10 s** |

⛔ Scaduto un tetto il server **DEVE** congedare con `TEMPO_SCADUTO` `0x0D`
   (§8.2), per le due strade di §3.1 — il `CONGEDO` sul canale di controllo e
   il codice del motivo nella chiusura della sessione WebTransport.

===========================================================================
⛔ LA SCENA SI DICHIARA, ED E' IL SILENZIO

`LEZIONI.md` §1.1 chiede una scena dichiarata e sempre uguale.  Qui la scena
**e' il silenzio del client**: dopo il messaggio che porta la stretta di mano
allo stato da misurare, questo programma **non spedisce piu' un byte di RCP**
fino alla fine della finestra.

⚠ E quel che passa lo stesso sul filo — riscontri, PING del trasporto, il
  keep-alive che il server arma — **non e' la scena**: e' il trasporto, e
  `RCP.md` §4.6 lo nomina apposta come la cura che tiene viva la connessione
  mentre l'utente digita.  Non lo si spegne e non lo si conta.

===========================================================================
⛔ IL PRIMO IMPUTATO E' IL BANCO: LE QUATTRO CERTIFICAZIONI, PRIMA DI MISURARE

`REVIEWER.md` §1.2 e `CODER.md` §3.3.  Un tetto si misura **aspettando che non
succeda niente**, e una misura fatta di attese e' quella che si sbaglia meglio:
se lo strumento non sa leggere un `CONGEDO`, ogni tetto risulta «mai scaduto»
e il banco stampa tre rossi contro un server che fa il suo mestiere.

  cert-giro-completo   ⭐ lo strumento sa arrivare in fondo a una stretta di
                       mano che riesce.  ⛔ Ed e' anche il controllo dello
                       STATO INIZIALE (B0.1/B0.3): se qui arriva
                       `TROPPI_TENTATIVI`, l'indirizzo e' nella finestra di
                       §4.4-bis lasciata da un altro banco, e ogni rosso che
                       segue sarebbe un falso rosso.  Il banco si ferma e lo
                       dice, invece di misurare;
  cert-cronometro      ⭐ il cronometro sa misurare un'attesa NOTA sul filo: il
                       secondo fisso di §4.4-bis, che B3 ha misurato
                       1074-1085 ms `[M]`.  Chi non sa vedere un secondo che
                       c'e' di sicuro non puo' dire niente su cinque;
  cert-congedo-noto    ⛔ **la certificazione che conta**: si provoca un
                       congedo NOTO e IMMEDIATO — `CIAO(versione = 2)` su
                       `/rcp/1`, che §2.2 impone di respingere con
                       `VERSIONE_INCOMPATIBILE` `0x0A` (B5: 36 su 36) — e si
                       verifica che il lettore lo veda **per tutt'e due le
                       strade di §3.1**.  Senza, «nessun congedo e' arrivato»
                       resta ambiguo fra «il server non l'ha mandato» e «io non
                       so leggerlo»;
  cert-morte-silenziosa ⛔ solo nella fase `ping`: lo strumento sa vedere una
                       connessione che muore **senza motivo**, e sa chiamarla
                       col suo nome.  E' la diagnosi che §4.6 chiede di saper
                       produrre — *«una morte a 30 s senza motivo e' il PING
                       che manca»* — e un banco che non l'ha mai prodotta non
                       ha nessun diritto di scriverla.

⛔ Se una certificazione non passa, i tetti NON si misurano: si esce 4.  Un
   esito negativo con lo strumento non certificato non e' una misura.

===========================================================================
⛔ IL CONTROLLO CHE DICE NO: «NON PRIMA» E' META' DEL REQUISITO

Un tetto ha due meta', e la seconda non la scrive nessuno: *non dopo* — che e'
il caso che tutti provano — e ⛔ *non prima*.  Un server che congedasse
**subito** con `TEMPO_SCADUTO` darebbe `TEMPO_SCADUTO` in tutt'e tre i casi, e
un banco che guarda solo il motivo lo promuoverebbe a pieni voti.

Per ogni tetto c'e' quindi un caso `-presto`: si aspetta il **70 %** del tetto
in silenzio e **poi** si manda il messaggio atteso, che **DEVE** essere
servito.  Sono i ⭐ verdi attesi di questo banco, e sono tre.

===========================================================================
⛔ LA TRAPPOLA DI QUESTO BANCO: CHI CHIUDE, IL PROTOCOLLO O IL TRASPORTO?

`RCP.md` §4.6 lo dice per esteso: i 60 secondi della parola d'ordine erano
**irraggiungibili**, perche' al trentesimo scatta il tempo di inattivita' di
QUIC e la connessione muore **in silenzio, senza motivo**.  La cura e' del
server — i **PING del trasporto** — e senza di essa il banco misurerebbe 30
dove il documento dice 60, dando la colpa al banco.

⛔ Da cui **due fasi, e la seconda e' quella che prova qualcosa**:

  `--fase sani`  il tetto del trasporto e' alzato a **120 s**, sopra tutti e
                 tre i tetti del protocollo: qui i numeri si leggono puliti,
                 perche' a chiudere puo' essere solo RCP.
                 ⚠ Ma con 120 s **anche un server che non manda un PING**
                 darebbe 60 s: questa fase da sola benedirebbe la violazione
                 che §4.6 esiste per curare — `LEZIONI.md` §1.3.

  `--fase ping`  ⭐ il tetto del trasporto e' abbassato **SOTTO** il tetto del
                 protocollo (15 s contro 60 s).  Se il server tiene viva la
                 connessione coi PING, `TEMPO_SCADUTO` arriva **lo stesso a
                 60 s**, dopo aver attraversato quattro volte il tetto del
                 trasporto.  Se non li manda, la connessione muore a **15 s
                 senza motivo** — ed e' precisamente la firma che §4.6
                 descrive, con un numero che non si puo' confondere con
                 nessuno dei tre tetti.
                 ⛔ E nella stessa fase, sullo stesso server, `cert-morte-
                 silenziosa` **la morte a 15 s la produce apposta**: le due
                 righe insieme dicono che la sopravvivenza dell'altra non e'
                 una fortuna.

⚠ **E il tetto del trasporto non lo decide solo il server.**  RFC 9000 §10.1:
  vale il **minimo dei due valori annunciati**, e `aioquic` di suo annuncia
  60 s — cioe' esattamente il tetto che questo banco deve misurare.  Qui la
  configurazione del client lo alza a `IDLE_NOSTRO` apposta, perche' il minimo
  dei due non sia mai il nostro; e il valore che conta si **legge dal pari**
  con la sonda di B2 (lo fa `01-b6-lancia.sh`), non si presume.

===========================================================================
⛔ DOVE PARTE IL CRONOMETRO DEL PRIMO TETTO — la `[?]` R3.27, e questo banco
   e' il posto in cui si risolve

§4.6 dice *«stretta di mano TLS finita → `CIAO` ricevuto: 5 s»*.  ⛔ Ma in
WebTransport la **connessione** HTTP/3 e la **sessione** sono due cose
separate, e fra i due istanti passa almeno un giro di rete: il browser puo'
aver stabilito la connessione molto prima che la pagina chiami l'API.  Se il
server fa partire il cronometro dove dice il documento e il banco lo misura
dall'apertura della sessione, la differenza si legge come **un tetto
sbagliato**.

Tre casi lo separano, e ciascuno stampa un numero invece di un'opinione:

  ciao-tetto              il caso normale: sessione, canale di controllo,
                          silenzio.  Il numero atteso e' 5 s da qui;
  ciao-senza-controllo    ⛔ sessione aperta e **canale di controllo mai
                          aperto**.  Alla lettera di §4.6 il tetto e' gia'
                          partito (il TLS e' finito da un pezzo) e a 5 s
                          dev'essere finita.  Se non succede niente, il
                          cronometro **non parte dal TLS**;
  ciao-sessione-tardiva   ⛔ il caso peggiore di R3.27: si finisce il TLS, si
                          aspettano `RITARDO_SESSIONE` secondi **senza aprire
                          la sessione**, poi si apre e si tace.  Se il tetto
                          partisse dal TLS, il budget sarebbe **gia'
                          consumato** e il congedo arriverebbe subito; se parte
                          dalla sessione, arriva 5 s dopo l'apertura.

⛔ Il verdetto di questi tre non e' «passa/non passa» ma **una risposta**, e la
   risposta la confronta il banco (B0.4): se il cronometro parte dalla
   sessione, §4.6 riga 1 **dice una cosa che il codice non fa**, e la cura e'
   nel documento — «cambia di una parola», come lo dichiara la fase.  In quel
   caso il banco esce **3**, che non e' il rosso del server.

===========================================================================
⛔ E I TRE NUMERI CHE QUESTO BANCO CONFRONTA, CHE SONO TRE E NON DUE

  il DOCUMENTO   `RCP.md` §4.6 — scritto qui sotto in `TETTI_DOC`, a mano, ed
                 e' l'arbitro: `RCP.md` e' l'arbitro del filo;
  il CODICE      i `#define TETTO_*` di `banchi/rcp/rcp.c`, letti dal sorgente
                 e passati da `01-b6-lancia.sh` con `--tetti-codice`;
  la MISURA      quel che arriva sul filo.

⛔ **E qui c'e' un fatto datato che riguarda questo banco.**  Il 10 agosto
   2026, rilievo R9.9, `TETTO_ATTACCA` e' stato portato da **60 000 a 10 000
   ms** sulla sola lettura di §4.6, **senza che nessuno lo misurasse** — e il
   commento nel codice lo dichiara: *«nessun banco lo vedeva: B6 non e' ancora
   scritto»*.  Questo banco e' **il primo testimone di quel numero**.  Da cui
   la regola di questo file: i tre numeri si stampano **tutti e tre**, sempre,
   e se non vanno d'accordo il banco lo dice invece di adattarsi a uno dei due.

===========================================================================
⛔ CHE COSA QUESTO BANCO NON PROVA, E VA DETTO

  · il tetto **non** si prova su un client vero (browser): la pagina non ha un
    modo di «tacere a comando», e il banco misura il SERVER.  Che il browser
    veda la stessa cosa e' `[?]`, e sta a B11;
  · i tre tetti si provano **uno per connessione**: che un tetto scaduto non
    lasci strascichi su una connessione successiva lo copre B0.5, qui, ma il
    caso di due tetti nella **stessa** connessione non esiste — la macchina a
    stati di §4 non ci torna;
  · `rcp_azzera_registro_sessioni()` esiste per il banco ⛔ **ma non ha nessun
    chiamante** raggiungibile da qui: non e' innestata in nessun punto del
    server.  Lo stato fra una fase e l'altra si azzera **riaccendendo il
    server**, e lo fa `01-b6-lancia.sh`.  Dichiarato, perche' chi legge la
    riga in `rcp.h` crede che il banco la usi.
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

# ⛔ Il cliente di B3 si IMPORTA, non si ricopia — come fa B5.  Dentro c'e' la
#    riga che gli impedisce di dare gli eventi del canale di controllo allo
#    strato HTTP/3 di aioquic (senza la quale la connessione muore per mano
#    del CLIENT), il lettore della capsula di chiusura di §3.1 punto 3, e la
#    registrazione di §11.1.  Una copia divergente riporterebbe qui i difetti
#    gia' pagati la', travestiti da difetti del server.
_spec = importlib.util.spec_from_file_location(
    "b3cliente", os.path.join(QUI, "01-b3-cliente.py"))
b3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b3)

s, inquadra, MOTIVI = b3.s, b3.inquadra, b3.MOTIVI

TEMPO_SCADUTO = 0x0D
VERSIONE_INCOMPATIBILE = 0x0A
TROPPI_TENTATIVI = 0x08
CONGEDO, RESPINTO = 0x000C, 0x0005

# ⛔ I TRE TETTI COME LI SCRIVE IL DOCUMENTO — `RCP.md` §4.6, tabella.
#    Non si leggono dal codice: il codice e' l'imputato.  Il valore del codice
#    arriva a parte, con `--tetti-codice`, e i due si confrontano.
TETTI_DOC = {"CIAO": 5000, "CREDENZIALI": 60000, "ATTACCA": 10000}

# ⚠ La tolleranza, e perche' e' asimmetrica.
#
#    Il cronometro del banco parte dall'istante in cui **legge** il messaggio
#    che porta allo stato (o in cui **spedisce** l'intestazione del canale), e
#    quello del server dall'istante in cui l'ha spedito: fra i due c'e' mezzo
#    giro di rete, quindi la misura puo' risultare un filo **piu' corta** del
#    tetto.  Dall'altra parte il server valuta i tetti alla cadenza con cui
#    passa il suo percorso di scrittura, quindi puo' risultare piu' lunga.
#
# ⛔ E resta larghissima rispetto a quel che deve distinguere: 5 da 30, 10 da
#    60, 60 da 15.  Una tolleranza che non separa i numeri in gioco non e' una
#    tolleranza, e' una benedizione.
TOLL_GIU, TOLL_SU = 1000, 2500

# ⛔ IL TETTO D'INATTIVITA' CHE ANNUNCIAMO NOI, E PERCHE' NON E' SEMPRE LO
#    STESSO.  E' la meta' nostra della regola «il tetto si legge dal pari, non
#    si presume», e sono due esigenze opposte in due fasi diverse.
#
#  · fase «sani»: dev'essere **molto sopra** tutti i tetti del protocollo, o a
#    chiudere saremmo noi.  ⚠ Il predefinito di aioquic e' 60 s, cioe'
#    esattamente il tetto di §4.6 da misurare: lasciarlo sarebbe misurare il
#    nostro orologio credendo di misurare il suo;
#
#  · fase «ping»: dev'essere **poco sopra** quello del server, e la ragione e'
#    un fatto del trasporto che rende cieco chi non lo sa.  ⛔ **Una morte per
#    inattivita' NON manda un `CONNECTION_CLOSE`** (RFC 9000 §10.1: chi scade
#    per inattivita' scarta lo stato e tace).  Se il server smettesse di
#    tenere viva la connessione, dal filo non arriverebbe **niente**: l'unico
#    modo di vedere quella morte e' che scada anche il NOSTRO orologio.  Con
#    il nostro poco sopra il suo, la morte — se c'e' — si vede pochi secondi
#    dopo; e se i PING ci sono, ogni PING lo rimette a zero e i 60 s si
#    misurano lo stesso.
#    ⚠ E se `aioquic` usasse il minimo dei due invece del proprio, la si
#      vedrebbe ancora prima: in tutt'e due i casi si vede, ed e' per questo
#      che sta poco sopra e non molto sopra.
IDLE_SANI = 180.0
IDLE_PING_MARGINE = 5.0

# Quanto si aspetta prima di aprire la sessione, in `ciao-sessione-tardiva`.
# ⚠ DEVE essere piu' lungo del tetto del `CIAO`, o il caso non separa niente.
RITARDO_SESSIONE = 8.0

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def adesso():
    return asyncio.get_event_loop().time()


# ===========================================================================
class Attesa:
    """Che cosa e' successo mentre tacevamo — dal lato che riceve.

    ⛔ Gli esiti sono CINQUE e hanno cinque nomi, perche' «non e' arrivato
       niente» e «e' morto tutto» sono diagnosi opposte con lo stesso aspetto
       se si stampa un `si`/`no` (`LEZIONI.md` §1.9, forma E8).
    """

    def __init__(self, nome):
        self.nome = nome
        # ⛔ La meta' che si dimentica: il caso e' ARRIVATO allo stato che
        #    voleva misurare?  Un caso che si ferma nella preparazione — un
        #    `ECCOMI` che non arriva, le credenziali rifiutate — non ha provato
        #    niente, e senza questa marca conterebbe come rosso del server.
        #    E' il `provocato` di B5 (rilievo R7.1) applicato ai tetti.
        self.pronto = False
        self.fase = "apertura"
        self.esito = "niente"      # congedo · morte-silenziosa · sessione-chiusa
        #                            · canale-chiuso · niente · errore
        self.motivo = None         # letto da un CONGEDO/RESPINTO sul filo
        self.tipo_motivo = None
        self.dettaglio = ""
        self.codice_wt = None      # §3.1 punto 3
        self.ms = None             # quanto ci ha messo, dal riferimento
        self.riferimento = ""      # da CHE COSA si conta — si stampa sempre
        self.errore = None

    def __str__(self):
        p = [f"da «{self.riferimento}»"] if self.riferimento else []
        if not self.pronto:
            p.append(f"⛔ MAI ARRIVATO allo stato da misurare (fermo in "
                     f"«{self.fase}»)")
        p.append(f"esito={self.esito}")
        if self.ms is not None:
            p.append(f"{self.ms / 1000:.2f} s")
        if self.motivo is not None:
            p.append(f"motivo={self.motivo:#04x}="
                     f"{MOTIVI.get(self.motivo, '?')} in {self.tipo_motivo}")
        p.append("chiusura-wt=" + ("(assente)" if self.codice_wt is None
                                   else f"{self.codice_wt:#04x}"))
        if self.errore:
            p.append(f"errore={self.errore}")
        return "  ".join(p)


async def ascolta(cli, t0, riferimento, finestra, es, grazia=1.5):
    """Tace e guarda, fino al congedo o alla fine della finestra.

    ⛔ **E' l'unico posto in cui `es.motivo` e `es.ms` vengono scritti**, e li
       scrive da quel che e' arrivato sul filo: §8.1 vuole il congedo
       verificato dal lato che riceve, mai dal registro di chi lo manda.

    ⚠ Si sfoglia con un giro breve invece di aspettare un solo evento: gli
      eventi che ci interessano sono di due tipi — un messaggio sul canale di
      controllo e la **morte della connessione** — e aspettarne uno solo
      renderebbe l'altro invisibile fino allo scadere della finestra, cioe'
      trasformerebbe una morte a 15 s in un «niente per 75 s».
    """
    es.riferimento = riferimento
    scadenza = t0 + finestra
    while adesso() < scadenza:
        try:
            m = await asyncio.wait_for(cli.messaggi.get(), timeout=0.02)
        except asyncio.TimeoutError:
            # ⛔ Nessun messaggio: e' caduto qualcosa nel frattempo?
            if cli.caduta is not None and es.motivo is None:
                es.ms = (adesso() - t0) * 1000
                es.esito = _classifica(cli)
                break
            continue
        if m is None:
            # il canale di controllo o la connessione si sono chiusi
            if es.motivo is None:
                es.ms = (adesso() - t0) * 1000
                es.esito = _classifica(cli)
            break
        tipo, corpo, _ = m
        if tipo not in (CONGEDO, RESPINTO):
            # ⚠ Un messaggio che non c'entra e' un fatto, non rumore: §4.2 non
            #   prevede niente sul canale di controllo mentre il server
            #   aspetta, e chi ne manda uno sta facendo altro.
            es.errore = (f"messaggio inatteso mentre tacevamo: {tipo:#06x} "
                         f"({len(corpo)} byte)")
            continue
        es.ms = (adesso() - t0) * 1000
        es.esito = "congedo"
        es.tipo_motivo = "CONGEDO" if tipo == CONGEDO else "RESPINTO"
        # ⛔ Un corpo VUOTO non e' «nessun motivo»: §7.1 vuole `u8 motivo` e
        #    §3.1 vieta il codice 0.  Con `corpo[0] if corpo else None` un
        #    server che chiude MALE sarebbe piu' facile da far passare di uno
        #    che chiude bene (e' il rilievo R7.2 di B5).
        if not corpo:
            es.errore = (f"{es.tipo_motivo} con corpo VUOTO: §7.1 ne vuole "
                         "almeno il byte del motivo")
            break
        es.motivo = corpo[0]
        if tipo == CONGEDO and len(corpo) >= 3:
            n = struct.unpack("!H", corpo[1:3])[0]
            es.dettaglio = corpo[3:3 + n].decode("utf-8", "replace")
        break
    else:
        # ⛔ La finestra e' scaduta.  «Niente» e' un esito, e vuole il suo
        #    numero: senza, la riga «non e' successo niente» non dice per
        #    quanto tempo non e' successo — cioe' non dice il denominatore
        #    dell'attesa (`LEZIONI.md` §1.9, quarta regola).
        es.ms = (adesso() - t0) * 1000
        if cli.caduta is not None and es.motivo is None:
            es.esito = _classifica(cli)

    # ⛔ §3.1 PUNTO 3, E PERCHE' SI ASPETTA UN PO'.
    #    Il `CONGEDO` viaggia sul canale di controllo, il codice del motivo
    #    dentro la capsula che chiude la sessione: due strade diverse, due
    #    istanti diversi.  Leggere la seconda nell'istante esatto della prima
    #    misurerebbe la nostra fretta.  ⚠ La finestra e' dichiarata e limitata:
    #    se scade, il valore resta `None` e il verdetto lo conta come mancato.
    if es.motivo is not None or es.errore is not None:
        fine = adesso() + grazia
        while (cli.codice_chiusura is None and not cli.finito
               and adesso() < fine):
            await asyncio.sleep(0.02)
    es.codice_wt = cli.codice_chiusura
    return es


def _classifica(cli):
    """⛔ Come e' morta: il nome, non un `no`.

    Sono i tre imputati che §4.6 chiede di separare, e hanno tre nomi diversi
    perche' portano a tre posti diversi: il tetto del trasporto (i PING che
    mancano), la sessione chiusa senza congedo (§3.1 punto 2 non fatto), il
    canale chiuso a secco.
    """
    c = cli.caduta or ""
    if cli.codice_chiusura is not None:
        return "sessione-chiusa"
    if c.startswith("connessione TERMINATA"):
        return "morte-silenziosa"
    if "sessione" in c:
        return "sessione-chiusa"
    if "canale di controllo" in c:
        return "canale-chiuso"
    return "niente"


# ===========================================================================
async def apri(a, percorso="/rcp/1"):
    """Connessione + sessione WebTransport.  ⚠ Il canale di controllo NO."""
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536,
                             idle_timeout=a.idle_nostro)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{a.indirizzo}:{a.porta}"
    gestore = connect(a.indirizzo, a.porta, configuration=conf,
                      create_protocol=b3.Cliente)
    cli = await gestore.__aenter__()
    await asyncio.wait_for(cli.wait_connected(), timeout=8)
    cli.apri_sessione(autorita, percorso)
    stato = await asyncio.wait_for(cli.accettata, timeout=8)
    return gestore, cli, stato


async def solo_connessione(a):
    """Solo QUIC + TLS: nessuna sessione WebTransport, nessun canale.

    Serve a `cert-morte-silenziosa`: e' la connessione che **nessuno** tiene
    viva, quindi quella che il tetto del trasporto DEVE portarsi via.
    """
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536,
                             idle_timeout=a.idle_nostro)
    conf.verify_mode = ssl.CERT_NONE
    gestore = connect(a.indirizzo, a.porta, configuration=conf,
                      create_protocol=b3.Cliente)
    cli = await gestore.__aenter__()
    await asyncio.wait_for(cli.wait_connected(), timeout=8)
    return gestore, cli


def apri_controllo(cli):
    """Apre il canale di controllo E LO METTE SUL FILO, senza mandarci niente.

    ⛔ Il `transmit()` non e' una formalita': `create_webtransport_stream` si
       limita a mettere in coda l'intestazione dello stream, e senza una
       passata di scrittura quei byte **non partono**.  Il server non vedrebbe
       nessuno stream, non chiamerebbe `rcp_avvia`, e il cronometro del primo
       tetto non partirebbe affatto: il banco misurerebbe la propria coda
       d'uscita e darebbe la colpa al server.
    """
    sid = cli.apri_controllo()
    cli.transmit()
    return sid


def ciao_buono(versione=1):
    voci = [("video.codec", "hevc,av1"), ("video.profondita", "8,10"),
            ("audio.codec", "opus,pcm"), ("client.nome", "banco-b6 0.1.0")]
    corpo = struct.pack("!HH", versione, len(voci))
    for n, v in voci:
        corpo += s(n) + s(v)
    return inquadra(0x0001, corpo)


def credenziali(a):
    return inquadra(0x0003, s(a.utente) + s(a.parola))


def attacca():
    return inquadra(0x0006, struct.pack("!IIII", 1920, 1080, 1920, 1080)
                    + s("it"))


# ===========================================================================
# I CASI.  ⛔ Ciascuno dichiara la sua PREVISIONE prima di misurare: la colonna
#          «atteso» sta nel file, non nel commento sul risultato.
# ===========================================================================
CASI = []


def caso(nome, fase, tetto, atteso, spiega):
    """`tetto` = chiave di TETTI_DOC o None · `atteso` = motivo o None (⭐ deve
    passare) o "risposta" (⛔ non e' un passa/non passa: e' una domanda aperta
    a cui questo caso risponde con un numero)."""
    def dec(f):
        CASI.append({"nome": nome, "fase": fase, "tetto": tetto,
                     "atteso": atteso, "spiega": spiega, "f": f})
        return f
    return dec


# ── I tre tetti ─────────────────────────────────────────────────────────────
@caso("ciao-tetto", "sani", "CIAO", TEMPO_SCADUTO,
      "canale di controllo aperto e nessun CIAO: §4.6 riga 1, 5 s")
async def _(a, es):
    gestore, cli, stato = await apri(a)
    try:
        if stato != "200":
            es.fase = f"CONNECT estesa :status={stato}"
            return es
        apri_controllo(cli)
        t0 = adesso()
        es.pronto, es.fase = True, "canale aperto, silenzio"
        await ascolta(cli, t0, "apertura del canale di controllo",
                      TETTI_DOC["CIAO"] / 1000 + 15, es)
    finally:
        await gestore.__aexit__(None, None, None)
    return es


@caso("credenziali-tetto", "sani", "CREDENZIALI", TEMPO_SCADUTO,
      "ECCOMI ricevuto e nessuna CREDENZIALI: §4.6 riga 2, 60 s")
async def _(a, es):
    gestore, cli, stato = await apri(a)
    try:
        if stato != "200":
            es.fase = f"CONNECT estesa :status={stato}"
            return es
        apri_controllo(cli)
        cli.manda(ciao_buono())
        await b3.attendi(cli, "ECCOMI")
        t0 = adesso()
        es.pronto, es.fase = True, "ECCOMI letto, silenzio"
        await ascolta(cli, t0, "ECCOMI letto",
                      TETTI_DOC["CREDENZIALI"] / 1000 + 15, es)
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        es.errore = f"{type(e).__name__}: {e}"
    finally:
        await gestore.__aexit__(None, None, None)
    return es


@caso("attacca-tetto", "sani", "ATTACCA", TEMPO_SCADUTO,
      "⛔ AMMESSO ricevuto e nessun ATTACCA: §4.6 riga 3, 10 s — ed e' il "
      "numero cambiato il 10 agosto 2026 senza che nessuno lo misurasse")
async def _(a, es):
    gestore, cli, stato = await apri(a)
    try:
        if stato != "200":
            es.fase = f"CONNECT estesa :status={stato}"
            return es
        apri_controllo(cli)
        cli.manda(ciao_buono())
        await b3.attendi(cli, "ECCOMI")
        es.fase = "CREDENZIALI spedite"
        cli.manda(credenziali(a))
        # ⚠ `attesa=20`: c'e' di mezzo il secondo fisso di §4.4-bis, e PAM.
        await b3.attendi(cli, "AMMESSO", attesa=20)
        t0 = adesso()
        es.pronto, es.fase = True, "AMMESSO letto, silenzio"
        await ascolta(cli, t0, "AMMESSO letto",
                      TETTI_DOC["ATTACCA"] / 1000 + 15, es)
    except Exception as e:  # noqa: BLE001
        es.errore = f"{type(e).__name__}: {e}"
    finally:
        await gestore.__aexit__(None, None, None)
    return es


# ── ⭐ I tre controlli che dicono NO: il tetto non scatta PRIMA ─────────────
@caso("ciao-presto", "sani", "CIAO", None,
      "⭐ si tace il 70 % del tetto e POI si manda CIAO: DEVE arrivare ECCOMI")
async def _(a, es):
    gestore, cli, stato = await apri(a)
    try:
        if stato != "200":
            es.fase = f"CONNECT estesa :status={stato}"
            return es
        apri_controllo(cli)
        await asyncio.sleep(TETTI_DOC["CIAO"] * 0.7 / 1000)
        es.pronto, es.fase = True, "CIAO spedito in ritardo"
        cli.manda(ciao_buono())
        await b3.attendi(cli, "ECCOMI")
        es.esito = "servito"
    except Exception as e:  # noqa: BLE001
        es.errore = f"{type(e).__name__}: {e}"
        es.esito = "rifiutato"
        es.codice_wt = cli.codice_chiusura
    finally:
        await gestore.__aexit__(None, None, None)
    return es


@caso("credenziali-presto", "sani", "CREDENZIALI", None,
      "⭐ si tace il 70 % dei 60 s e POI si mandano le CREDENZIALI: DEVE "
      "arrivare AMMESSO — ed e' anche la prova che i PING reggono 42 s")
async def _(a, es):
    gestore, cli, stato = await apri(a)
    try:
        if stato != "200":
            es.fase = f"CONNECT estesa :status={stato}"
            return es
        apri_controllo(cli)
        cli.manda(ciao_buono())
        await b3.attendi(cli, "ECCOMI")
        await asyncio.sleep(TETTI_DOC["CREDENZIALI"] * 0.7 / 1000)
        es.pronto, es.fase = True, "CREDENZIALI spedite in ritardo"
        cli.manda(credenziali(a))
        await b3.attendi(cli, "AMMESSO", attesa=20)
        es.esito = "servito"
    except Exception as e:  # noqa: BLE001
        es.errore = f"{type(e).__name__}: {e}"
        es.esito = "rifiutato"
        es.codice_wt = cli.codice_chiusura
    finally:
        await gestore.__aexit__(None, None, None)
    return es


@caso("attacca-presto", "sani", "ATTACCA", None,
      "⭐ si tace il 70 % dei 10 s e POI si manda ATTACCA: DEVE arrivare "
      "SESSIONE")
async def _(a, es):
    gestore, cli, stato = await apri(a)
    try:
        if stato != "200":
            es.fase = f"CONNECT estesa :status={stato}"
            return es
        apri_controllo(cli)
        cli.manda(ciao_buono())
        await b3.attendi(cli, "ECCOMI")
        cli.manda(credenziali(a))
        await b3.attendi(cli, "AMMESSO", attesa=20)
        await asyncio.sleep(TETTI_DOC["ATTACCA"] * 0.7 / 1000)
        es.pronto, es.fase = True, "ATTACCA spedito in ritardo"
        cli.manda(attacca())
        await b3.attendi(cli, "SESSIONE")
        es.esito = "servito"
    except Exception as e:  # noqa: BLE001
        es.errore = f"{type(e).__name__}: {e}"
        es.esito = "rifiutato"
        es.codice_wt = cli.codice_chiusura
    finally:
        await gestore.__aexit__(None, None, None)
    return es


# ── ⛔ Dove parte il cronometro del primo tetto — la `[?]` R3.27 ────────────
@caso("ciao-senza-controllo", "sani", "CIAO", "risposta",
      "⛔ sessione aperta e canale di controllo MAI aperto: alla lettera di "
      "§4.6 il tetto e' gia' partito col TLS, e a 5 s dev'essere finita")
async def _(a, es):
    gestore, cli, stato = await apri(a)
    try:
        if stato != "200":
            es.fase = f"CONNECT estesa :status={stato}"
            return es
        t0 = adesso()
        es.pronto, es.fase = True, "sessione aperta, nessun canale"
        await ascolta(cli, t0, "apertura della sessione WebTransport",
                      TETTI_DOC["CIAO"] / 1000 + 15, es)
    finally:
        await gestore.__aexit__(None, None, None)
    return es


@caso("ciao-sessione-tardiva", "sani", "CIAO", "risposta",
      "⛔ il caso peggiore di R3.27: TLS finito, si aspetta, POI si apre la "
      "sessione.  Congedo subito = il budget era gia' consumato (cronometro "
      "dal TLS); congedo 5 s dopo = cronometro dalla sessione")
async def _(a, es):
    gestore, cli = await solo_connessione(a)
    try:
        # ⛔ Si aspetta CON LA CONNESSIONE APERTA e senza aprire la sessione:
        #    e' esattamente il browser che ha stabilito HTTP/3 molto prima che
        #    la pagina chiami l'API di WebTransport.
        await asyncio.sleep(RITARDO_SESSIONE)
        if cli.caduta is not None:
            es.fase = (f"la connessione e' caduta durante l'attesa: "
                       f"{cli.caduta}")
            return es
        cli.apri_sessione(f"{a.indirizzo}:{a.porta}", "/rcp/1")
        stato = await asyncio.wait_for(cli.accettata, timeout=8)
        if stato != "200":
            es.fase = f"CONNECT estesa :status={stato}"
            return es
        apri_controllo(cli)
        t0 = adesso()
        es.pronto = True
        es.fase = f"canale aperto {RITARDO_SESSIONE:.0f} s dopo il TLS"
        await ascolta(cli, t0, f"canale aperto {RITARDO_SESSIONE:.0f} s dopo "
                               f"la fine del TLS",
                      TETTI_DOC["CIAO"] / 1000 + 15, es)
    except Exception as e:  # noqa: BLE001
        es.errore = f"{type(e).__name__}: {e}"
    finally:
        await gestore.__aexit__(None, None, None)
    return es


# ── ⭐ La fase che prova i PING del trasporto (§4.6, riquadro R1.8) ─────────
@caso("credenziali-tetto-sotto-il-trasporto", "ping", "CREDENZIALI",
      TEMPO_SCADUTO,
      "⭐ lo stesso tetto dei 60 s, ma col tetto del TRASPORTO piu' CORTO: se "
      "arriva TEMPO_SCADUTO a 60 s i PING di §4.6 ci sono; se muore al tetto "
      "del trasporto SENZA motivo, mancano")
async def _(a, es):
    gestore, cli, stato = await apri(a)
    try:
        if stato != "200":
            es.fase = f"CONNECT estesa :status={stato}"
            return es
        apri_controllo(cli)
        cli.manda(ciao_buono())
        await b3.attendi(cli, "ECCOMI")
        t0 = adesso()
        es.pronto, es.fase = True, "ECCOMI letto, silenzio sotto un tetto corto"
        await ascolta(cli, t0, "ECCOMI letto",
                      TETTI_DOC["CREDENZIALI"] / 1000 + 15, es)
    except Exception as e:  # noqa: BLE001
        es.errore = f"{type(e).__name__}: {e}"
    finally:
        await gestore.__aexit__(None, None, None)
    return es


# ===========================================================================
# LE CERTIFICAZIONI.  ⛔ Girano PRIMA dei casi, e se cadono i casi non girano.
# ===========================================================================
async def cert_giro_completo(a):
    """⭐ Lo strumento sa arrivare in fondo — e lo stato iniziale e' pulito.

    ⛔ Vale anche come B0.1/B0.3: `TROPPI_TENTATIVI` qui vuol dire che
       l'indirizzo e' dentro la finestra di §4.4-bis lasciata da un altro
       banco (B5 la lascia apposta, B8 pure), e ogni rosso che segue sarebbe
       un falso rosso — proprio quello che B0.3 esiste per impedire.

    Restituisce (ok, testo, bloccato, ms_del_secondo_fisso).
    """
    # ⛔ Anche «non si apre nemmeno la connessione» e' un esito di questa
    #    certificazione, e ha una diagnosi sua: senza questo ramo il banco
    #    moriva con una traccia di Python, che e' il modo peggiore di dire «il
    #    server non c'e'» — e non stampa nessun denominatore.
    try:
        gestore, cli, stato = await apri(a)
    except Exception as e:  # noqa: BLE001
        return False, f"non si apre la sessione: {type(e).__name__}: {e}", False, None
    ms = None
    try:
        if stato != "200":
            return False, f"CONNECT estesa :status={stato}", False, None
        apri_controllo(cli)
        cli.manda(ciao_buono())
        await b3.attendi(cli, "ECCOMI")
        t0 = adesso()
        cli.manda(credenziali(a))
        try:
            await b3.attendi(cli, "AMMESSO", attesa=20)
        except RuntimeError as e:
            testo = str(e)
            # ⛔ «Non entra» ha piu' di una causa, e il banco ne deve nominare
            #    UNA sola quando sa quale: il blocco di §4.4-bis ha un nome
            #    proprio e una cura diversa (aspettare), e confonderlo con «il
            #    server e' rotto» manda a cercare nel posto sbagliato.
            return False, testo, "TROPPI_TENTATIVI" in testo, None
        ms = (adesso() - t0) * 1000
        cli.manda(attacca())
        await b3.attendi(cli, "SESSIONE")
        return True, "CIAO → ECCOMI → CREDENZIALI → AMMESSO → ATTACCA → SESSIONE", False, ms
    except Exception as e:  # noqa: BLE001
        testo = f"{type(e).__name__}: {e}"
        # ⚠ Il blocco di §4.4-bis puo' arrivare anche per strade che non sono
        #   il `RESPINTO` di sopra: si guarda comunque il nome, perche' la cura
        #   e' diversa (aspettare) e la diagnosi sbagliata manda a cercare nel
        #   posto sbagliato — `LEZIONI.md` §1.6.
        return False, testo, "TROPPI_TENTATIVI" in testo, ms
    finally:
        await gestore.__aexit__(None, None, None)


async def cert_congedo_noto(a):
    """⛔ La certificazione che conta: un congedo NOTO, immediato, letto per
    tutt'e due le strade di §3.1.

    `CIAO(versione = 2)` su `/rcp/1` → `VERSIONE_INCOMPATIBILE` `0x0A` (§2.2,
    e B5 lo misura 36 su 36).  ⭐ Se questo passa, «nessun congedo e' arrivato»
    nei casi dei tetti vuol dire **che il server non l'ha mandato**, e non che
    questo programma non sa leggerlo.

    Restituisce (ok, testo, secondi).
    """
    es = Attesa("cert-congedo-noto")
    try:
        gestore, cli, stato = await apri(a)
    except Exception as e:  # noqa: BLE001
        return False, f"non si apre la sessione: {type(e).__name__}: {e}", None
    try:
        if stato != "200":
            return False, f"CONNECT estesa :status={stato}", None
        apri_controllo(cli)
        t0 = adesso()
        cli.manda(ciao_buono(versione=2))
        await ascolta(cli, t0, "CIAO(versione = 2) spedito", 8.0, es)
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}", None
    finally:
        await gestore.__aexit__(None, None, None)
    ok = (es.motivo == VERSIONE_INCOMPATIBILE
          and es.tipo_motivo == "CONGEDO"
          and es.codice_wt == VERSIONE_INCOMPATIBILE)
    return ok, str(es), es.ms


async def cert_morte_silenziosa(a, idle_ms):
    """⛔ Lo strumento sa vedere — e NOMINARE — una morte senza motivo.

    Una connessione QUIC sola, senza sessione e senza canale: nessuno la tiene
    viva, quindi il tetto del trasporto **DEVE** portarsela via, e la riga che
    ne esce dev'essere `morte-silenziosa` — non `congedo`, non `niente`.

    ⭐ E' il gemello negativo di `credenziali-tetto-sotto-il-trasporto`: sullo
       stesso server e sotto lo stesso tetto, una connessione muore e l'altra
       no.  Senza questa riga, «e' sopravvissuta» non dimostrerebbe che
       qualcuno la teneva viva.
    """
    es = Attesa("cert-morte-silenziosa")
    try:
        gestore, cli = await solo_connessione(a)
    except Exception as e:  # noqa: BLE001
        return False, f"non si apre la connessione: {type(e).__name__}: {e}", None
    try:
        t0 = adesso()
        es.pronto = True
        await ascolta(cli, t0, "fine del TLS", idle_ms / 1000 + 15, es)
    finally:
        await gestore.__aexit__(None, None, None)
    ok = es.esito == "morte-silenziosa" and es.motivo is None
    return ok, str(es), es.ms


async def ancora_vivo(a):
    """⛔ B0.5, dopo ogni caso: il server e' ancora li'?

    «La connessione cade sempre» e' soddisfatto anche da un server ucciso dal
    nucleo, che si porterebbe via **le sessioni di tutti gli altri utenti**.
    Si arriva fino a `ECCOMI`, che e' la prima risposta che il server compone
    davvero.
    """
    try:
        gestore, cli, stato = await apri(a)
    except Exception as e:  # noqa: BLE001
        return False, f"non si apre nemmeno la connessione: {type(e).__name__}: {e}"
    try:
        if stato != "200":
            return False, f"CONNECT estesa :status={stato}"
        apri_controllo(cli)
        cli.manda(ciao_buono())
        await b3.attendi(cli, "ECCOMI", attesa=8)
        return True, "una connessione nuova arriva a ECCOMI"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"
    finally:
        await gestore.__aexit__(None, None, None)


# ===========================================================================
def riga(ok, nome, testo):
    print(f"    {VERDE if ok else ROSSO}{'OK' if ok else 'NO'}{GRIGIO}  "
          f"{nome:34s} {testo}")


def riga_gialla(nome, testo):
    """⚠ Per le RISPOSTE: non sono passa/non passa, sono numeri."""
    print(f"    {GIALLO}??{GRIGIO}  {nome:34s} {testo}")


def dentro_tolleranza(ms, tetto_ms):
    return tetto_ms - TOLL_GIU <= ms <= tetto_ms + TOLL_SU


def leggi_tetti_codice(testo):
    """`CIAO=5000,CREDENZIALI=60000,ATTACCA=10000` → dizionario.

    ⛔ E «non me l'hanno detto» non e' «combaciano»: se il parametro manca, il
       confronto documento/codice **non si fa** e si dichiara di non averlo
       fatto.  Un confronto saltato in silenzio e' peggio di un confronto
       fallito (`LEZIONI.md` §1.9: il denominatore, non solo il risultato).
    """
    fuori = {}
    for pezzo in (testo or "").split(","):
        pezzo = pezzo.strip()
        if not pezzo:
            continue
        if "=" not in pezzo:
            raise SystemExit(f"⛔ --tetti-codice: «{pezzo}» non ha la forma NOME=valore")
        n, v = pezzo.split("=", 1)
        fuori[n.strip().upper()] = int(v.strip())
    return fuori


async def principale(a):
    tetti_codice = leggi_tetti_codice(a.tetti_codice)
    # ⛔ Il nostro tetto d'inattivita' dipende dalla fase — vedi il riquadro
    #    accanto a IDLE_SANI: nella fase «ping» e' l'unico modo che abbiamo di
    #    VEDERE una morte per inattivita', che sul filo non manda niente.
    a.idle_nostro = (IDLE_SANI if a.fase == "sani"
                     else a.idle / 1000 + IDLE_PING_MARGINE)

    if a.elenco:
        print(f"== B6 — i tre tetti della stretta di mano (RCP.md §4.6)")
        print(f"   {len(CASI)} casi in due fasi.  Ogni riga e' una PREVISIONE\n")
        for c in CASI:
            if c["atteso"] is None:
                att = "⭐ DEVE PASSARE (il tetto non scatta prima)"
            elif c["atteso"] == "risposta":
                att = "⛔ RISPOSTA A UNA DOMANDA APERTA (nessun passa/non passa)"
            else:
                att = (f"{c['atteso']:#04x} {MOTIVI.get(c['atteso'], '?')} a "
                       f"{TETTI_DOC[c['tetto']] / 1000:.0f} s")
            print(f"  [{c['fase']:4s}] {c['nome']:36s} {att}")
            print(f"  {'':43s} {c['spiega']}")
        print("\n  E prima di tutto: cert-giro-completo · cert-cronometro ·")
        print("  cert-congedo-noto · cert-morte-silenziosa (solo fase «ping»)")
        return 0

    casi = [c for c in CASI if c["fase"] == a.fase
            and (not a.solo or a.solo in c["nome"])]

    # ⛔ ZERO CASI NON E' «TUTTI PASSATI» — la lezione di R7.15 su B5.  Un
    #    errore di battitura nel filtro non deve avere il colore del verde.
    if not casi:
        print(f"    {ROSSO}⛔ fase «{a.fase}» + filtro «{a.solo}»: ZERO casi "
              f"selezionati su {len(CASI)}{GRIGIO}")
        print("       Questo NON e' un verde.  I nomi si leggono con --elenco.")
        return 2

    print(f"== B6 — i tre tetti della stretta di mano · fase «{a.fase}»")
    print(f"   {len(casi)} casi su {len(CASI)} selezionati")
    print(f"   la scena: il client TACE — nessun byte di RCP dopo il messaggio "
          f"che porta allo stato.")
    print(f"   Riscontri e PING del trasporto non sono la scena, e sono "
          f"dichiarati (§4.6).")
    print(f"   tetto d'inattivita' del trasporto in vigore, LETTO DAL PARI: "
          f"{a.idle} ms")
    print(f"   tetto d'inattivita' annunciato da noi: "
          f"{a.idle_nostro * 1000:.0f} ms — ⛔ e il predefinito di aioquic "
          f"sarebbe 60 000 ms,")
    print(f"   cioe' proprio il tetto da misurare: qui e' scelto apposta "
          f"(vedi IDLE_SANI nel file)\n")

    # ── I TRE NUMERI, PRIMA DI MISURARE ────────────────────────────────────
    print("   ⛔ i tre numeri che questo banco confronta:")
    disaccordo_doc_codice = []
    for n in ("CIAO", "CREDENZIALI", "ATTACCA"):
        c = tetti_codice.get(n)
        if c is None:
            print(f"      {n:12s} documento {TETTI_DOC[n]:6d} ms · codice "
                  f"{GIALLO}non dichiarato{GRIGIO} (--tetti-codice mancante: "
                  f"il confronto NON si fa)")
        elif c != TETTI_DOC[n]:
            print(f"      {n:12s} documento {TETTI_DOC[n]:6d} ms · codice "
                  f"{ROSSO}{c} ms — ⛔ NON COMBACIANO{GRIGIO}")
            disaccordo_doc_codice.append(n)
        else:
            print(f"      {n:12s} documento {TETTI_DOC[n]:6d} ms · codice "
                  f"{c} ms · combaciano")
    if "ATTACCA" in tetti_codice:
        print(f"      ⚠ `TETTO_ATTACCA` e' stato portato da 60 000 a 10 000 ms "
              f"il 10 agosto 2026 (R9.9)")
        print(f"        sulla sola lettura di §4.6, senza misura: questo banco "
              f"e' il suo primo testimone")
    print()

    conti = {
        "certificazioni dello strumento": [0, 0],
        "tetti scaduti con TEMPO_SCADUTO": [0, 0],
        "tetti scaduti NEL TEMPO GIUSTO (§4.6)": [0, 0],
        "§3.1 punto 3 — 0x0D nella chiusura WT": [0, 0],
        "⭐ il tetto NON scatta prima": [0, 0],
        "B0.5 — il server ancora vivo dopo ogni caso": [0, 0],
        "⛔ documento e codice d'accordo": [0, 0],
    }
    for n in ("CIAO", "CREDENZIALI", "ATTACCA"):
        if n in tetti_codice:
            conti["⛔ documento e codice d'accordo"][1] += 1
            conti["⛔ documento e codice d'accordo"][0] += int(
                tetti_codice[n] == TETTI_DOC[n])

    guasti, risposte = 0, []

    # ── LE CERTIFICAZIONI ──────────────────────────────────────────────────
    print("== ⛔ Le certificazioni dello strumento, PRIMA di misurare")
    print("   (REVIEWER.md §1.2: un esito negativo con lo strumento non "
          "certificato e' ambiguo)")

    ok, testo, bloccato, ms_fisso = await cert_giro_completo(a)
    conti["certificazioni dello strumento"][1] += 1
    conti["certificazioni dello strumento"][0] += int(ok)
    riga(ok, "cert-giro-completo", testo)
    if bloccato:
        print(f"\n    {ROSSO}⛔ LO STATO INIZIALE NON E' PULITO (B0.3){GRIGIO}")
        print("       L'indirizzo e' dentro la finestra di §4.4-bis: un altro")
        print("       banco (B5, B8) ha fallito dei tentativi da qui poco fa.")
        print("       ⛔ Non e' un difetto dei tetti, ed e' precisamente il")
        print("          falso rosso che B0.3 esiste per impedire.")
        print("       Cura: aspettare (il blocco parte da 30 s e raddoppia,")
        print("       fino a 15 minuti; scade da se' dopo 30 minuti di quiete),")
        print("       oppure riaccendere il server, che azzera la tabella.")
        return 5
    if not ok:
        print(f"\n    {ROSSO}⛔ lo strumento non arriva in fondo a una stretta "
              f"di mano che riesce: i tetti non si misurano{GRIGIO}")
        return 4

    # ⭐ Il cronometro, su un'attesa NOTA: il secondo fisso di §4.4-bis.
    ok_cr = ms_fisso is not None and 1000 <= ms_fisso <= 3000
    conti["certificazioni dello strumento"][1] += 1
    conti["certificazioni dello strumento"][0] += int(ok_cr)
    riga(ok_cr, "cert-cronometro",
         (f"il secondo fisso di §4.4-bis misurato {ms_fisso:.0f} ms "
          f"(B3: 1074-1085 ms)" if ms_fisso is not None
          else "⛔ non misurato: senza un'attesa nota il cronometro non e' "
               "certificato"))
    if not ok_cr:
        guasti += 1

    ok_cn, testo_cn, ms_cn = await cert_congedo_noto(a)
    conti["certificazioni dello strumento"][1] += 1
    conti["certificazioni dello strumento"][0] += int(ok_cn)
    riga(ok_cn, "cert-congedo-noto", testo_cn)
    if not ok_cn:
        print(f"\n    {ROSSO}⛔ lo strumento non sa leggere un congedo NOTO "
              f"per le due strade di §3.1{GRIGIO}")
        print("       Ogni «nessun congedo e' arrivato» che segue sarebbe")
        print("       ambiguo fra il server e il banco: non si misura.")
        return 4

    if a.fase == "ping":
        ok_ms, testo_ms, ms_ms = await cert_morte_silenziosa(a, a.idle)
        conti["certificazioni dello strumento"][1] += 1
        conti["certificazioni dello strumento"][0] += int(ok_ms)
        riga(ok_ms, "cert-morte-silenziosa", testo_ms)
        if ms_ms is not None:
            print(f"        ⚠ morta dopo {ms_ms / 1000:.1f} s, e il tetto del "
                  f"trasporto e' {a.idle / 1000:.0f} s")
        if not ok_ms:
            print(f"\n    {ROSSO}⛔ lo strumento non sa vedere una morte senza "
                  f"motivo: la diagnosi «i PING mancano» non e' producibile"
                  f"{GRIGIO}")
            return 4

    # ── I CASI ─────────────────────────────────────────────────────────────
    print(f"\n== I casi")
    for c in casi:
        es = Attesa(c["nome"])
        try:
            await c["f"](a, es)
        except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
            es.errore = f"{type(e).__name__}: {e}"

        tetto_ms = TETTI_DOC[c["tetto"]] if c["tetto"] else None

        if c["atteso"] is None:
            # ⭐ Il controllo che dice NO: il tetto non scatta prima.
            conti["⭐ il tetto NON scatta prima"][1] += 1
            ok = es.pronto and es.esito == "servito" and es.errore is None
            conti["⭐ il tetto NON scatta prima"][0] += int(ok)
            riga(ok, c["nome"],
                 (f"servito dopo {tetto_ms * 0.7 / 1000:.1f} s di silenzio "
                  f"(tetto {tetto_ms / 1000:.0f} s)") if ok else str(es))
            if not ok:
                guasti += 1
                print(f"        atteso: ⭐ nessuna caduta — {c['spiega']}")

        elif c["atteso"] == "risposta":
            # ⛔ Non e' un passa/non passa: e' una domanda aperta, e la
            #    risposta e' un numero.  Il confronto lo fa il banco (B0.4),
            #    ma il verdetto sta in una riga sua.
            if not es.pronto:
                riga(False, c["nome"], str(es))
                guasti += 1
                print(f"        ⛔ il caso non e' mai arrivato allo stato che "
                      f"doveva misurare: non e' una prova fallita, e' una "
                      f"prova non fatta")
            else:
                # ⛔ «E' successo qualcosa» ha DUE strade, e in uno di questi
                #    casi la prima non esiste: senza canale di controllo il
                #    `CONGEDO` non ha per dove passare (§3.1 punto 2 e' proprio
                #    condizionato a quello), e resta la chiusura della sessione
                #    col codice del motivo (§3.1 punto 3).  Contare solo il
                #    `CONGEDO` darebbe «non e' successo niente» a un server che
                #    ha fatto tutto quel che poteva fare.
                per_congedo = es.esito == "congedo" and es.motivo is not None
                per_chiusura = es.codice_wt is not None
                motivo_visto = es.motivo if per_congedo else es.codice_wt
                strada = ("CONGEDO" if per_congedo else
                          "chiusura della sessione" if per_chiusura else "")
                if (per_congedo or per_chiusura) and es.ms is not None:
                    if motivo_visto != TEMPO_SCADUTO:
                        risp = (f"⛔ e' arrivato {motivo_visto:#04x}="
                                f"{MOTIVI.get(motivo_visto, '?')} invece di "
                                f"TEMPO_SCADUTO, dopo {es.ms / 1000:.2f} s: "
                                f"non e' un tetto, e' un'altra cosa")
                        verso = "?"
                        guasti += 1
                    elif es.ms < 1500:
                        risp = (f"il cronometro parte dalla FINE DEL TLS: "
                                f"TEMPO_SCADUTO per {strada} dopo "
                                f"{es.ms / 1000:.2f} s, cioe' col budget gia' "
                                f"consumato")
                        verso = "TLS"
                    else:
                        risp = (f"il cronometro parte dall'APERTURA (sessione o "
                                f"canale): TEMPO_SCADUTO per {strada} dopo "
                                f"{es.ms / 1000:.2f} s")
                        verso = "APERTURA"
                elif es.esito == "niente":
                    risp = (f"⛔ non e' successo NIENTE in "
                            f"{es.ms / 1000:.0f} s: in questo stato il "
                            f"cronometro non parte affatto, e la connessione "
                            f"resta li' appesa")
                    verso = "MAI"
                else:
                    risp = f"⛔ {es}"
                    verso = "?"
                riga_gialla(c["nome"], risp)
                risposte.append((c["nome"], verso, risp))

        else:
            # I tetti veri.
            conti["tetti scaduti con TEMPO_SCADUTO"][1] += 1
            ok_motivo = (es.motivo == c["atteso"]
                         and es.tipo_motivo == "CONGEDO")
            if not es.pronto:
                ok_motivo = False
            conti["tetti scaduti con TEMPO_SCADUTO"][0] += int(ok_motivo)

            conti["tetti scaduti NEL TEMPO GIUSTO (§4.6)"][1] += 1
            # ⛔ «Nel tempo giusto» vale solo su un CONGEDO: la finestra
            #    d'attesa dura piu' del tetto, quindi un «niente» porta con se'
            #    un numero grande che non e' un tempo di scadenza.  Senza
            #    questa condizione un caso in cui non succede niente potrebbe
            #    cadere dentro la tolleranza di un ALTRO tetto e stampare un
            #    verde — la forma E8, «niente» che prende l'aspetto di un dato.
            ok_tempo = (es.esito == "congedo" and es.ms is not None
                        and es.pronto and dentro_tolleranza(es.ms, tetto_ms))
            conti["tetti scaduti NEL TEMPO GIUSTO (§4.6)"][0] += int(ok_tempo)

            conti["§3.1 punto 3 — 0x0D nella chiusura WT"][1] += 1
            ok_wt = es.codice_wt == c["atteso"]
            conti["§3.1 punto 3 — 0x0D nella chiusura WT"][0] += int(ok_wt)

            ok = ok_motivo and ok_tempo and ok_wt
            riga(ok, c["nome"], str(es))
            if not ok:
                guasti += 1
                print(f"        atteso: {c['atteso']:#04x} "
                      f"{MOTIVI.get(c['atteso'], '?')} a "
                      f"{tetto_ms / 1000:.0f} s "
                      f"(tolleranza -{TOLL_GIU / 1000:.1f} / "
                      f"+{TOLL_SU / 1000:.1f} s)")
                print(f"        {c['spiega']}")
                if not es.pronto:
                    print(f"        ⛔ e il caso NON E' MAI ARRIVATO allo stato "
                          f"da misurare: non e' una prova fallita, e' una prova "
                          f"non fatta")
                elif es.esito == "morte-silenziosa":
                    print(f"        ⛔ MORTA SENZA MOTIVO dopo "
                          f"{es.ms / 1000:.1f} s, e il tetto del trasporto e' "
                          f"{a.idle / 1000:.0f} s:")
                    print(f"           e' la firma che §4.6 descrive — i PING "
                          f"del trasporto non ci sono, e a chiudere e' QUIC")
                elif es.esito == "niente":
                    print(f"        ⛔ NON E' SUCCESSO NIENTE per "
                          f"{es.ms / 1000 if es.ms else 0:.0f} s: il tetto non "
                          f"e' scaduto, e la connessione resta li' appesa")
                elif es.ms is not None and not ok_tempo:
                    altri = [n for n, v in TETTI_DOC.items()
                             if dentro_tolleranza(es.ms, v)]
                    if altri:
                        print(f"        ⚠ i {es.ms / 1000:.1f} s misurati "
                              f"combaciano invece col tetto di «{altri[0]}» "
                              f"({TETTI_DOC[altri[0]] / 1000:.0f} s):")
                        print(f"           e' la forma del difetto che si copia "
                              f"dalla riga precedente (R9.9)")
            if es.dettaglio:
                print(f"        dettaglio dal corpo: «{es.dettaglio}»")

        # ⛔ B0.5, dopo OGNI caso.
        conti["B0.5 — il server ancora vivo dopo ogni caso"][1] += 1
        vivo, perche = await ancora_vivo(a)
        conti["B0.5 — il server ancora vivo dopo ogni caso"][0] += int(vivo)
        if not vivo:
            riga(False, "", f"⛔ IL SERVER NON RISPONDE PIU' dopo "
                            f"«{c['nome']}»: {perche}")
            guasti += 1
            print(f"\n    {ROSSO}⛔ il banco si ferma: senza un server non "
                  f"c'e' niente da misurare{GRIGIO}")
            break

    # ── L'ESITO ────────────────────────────────────────────────────────────
    print()
    print("    == quel che questo giro ha davvero guardato")
    for che, (buoni, tot) in conti.items():
        if tot == 0:
            # ⛔ Un denominatore a zero si DICHIARA: «nessuno ha guardato» e
            #    «tutti passati» hanno lo stesso aspetto se si tace.
            print(f"    --  {che:46s} nessun caso lo ha sollecitato")
            continue
        col = VERDE if buoni == tot else ROSSO
        print(f"    {col}{buoni:3d} su {tot:3d}{GRIGIO}  {che}")

    if risposte:
        print()
        print("    == ⛔ le domande aperte a cui questo giro ha RISPOSTO")
        print("       (non sono passa/non passa: sono numeri da portare nei "
               "documenti)")
        for nome, verso, risp in risposte:
            print(f"    ??  {nome:34s} {risp}")

    # ⛔ TRE ESITI DIVERSI, PERCHE' SONO TRE COSE DIVERSE — ed e' il punto di
    #    questo banco.
    #
    #      1  il SERVER non rispetta §4.6;
    #      3  il server fa quel che il CODICE dice, ma il DOCUMENTO dice
    #         un'altra cosa: la cura sta nel documento;
    #      0  documento, codice e filo dicono la stessa cosa.
    print()
    if guasti:
        print(f"    {ROSSO}⛔ B6 «{a.fase}»: {guasti} punti non passano"
              f"{GRIGIO}")
        return 1

    fuori_dal_documento = [r for r in risposte if r[1] != "TLS"]
    if disaccordo_doc_codice:
        print(f"    {ROSSO}⛔ B6 «{a.fase}»: il filo si comporta bene, ma "
              f"DOCUMENTO e CODICE non dicono lo stesso numero{GRIGIO}")
        for n in disaccordo_doc_codice:
            print(f"       {n}: §4.6 dice {TETTI_DOC[n]} ms, "
                  f"`banchi/rcp/rcp.c` dice {tetti_codice[n]} ms")
        print("       ⛔ La cura non e' scegliere: e' che uno dei due si "
              "aggiorni, con la data e la fonte (CODER.md §5).")
        return 3
    if fuori_dal_documento:
        print(f"    {GIALLO}⛔ B6 «{a.fase}»: i tetti si comportano come il "
              f"CODICE dice, ma §4.6 riga 1 dice un'altra cosa{GRIGIO}")
        for nome, verso, risp in fuori_dal_documento:
            print(f"       {nome}: {risp}")
        print("       §4.6 dice «stretta di mano TLS finita», e il cronometro "
              "parte da un altro istante.")
        print("       ⛔ E' la `[?]` R3.27, e adesso ha una misura: «§4.6 "
              "cambia di una parola»,")
        print("          oppure il cronometro cambia istante.  Non e' il rosso "
              "del server.")
        return 3
    print(f"    {VERDE}⭐ B6 «{a.fase}» passa, e i numeri qui sopra dicono su "
          f"che cosa{GRIGIO}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="B6 — i tre tetti della stretta di mano (RCP.md §4.6)")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7447)
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola", default="parola-di-prova")
    p.add_argument("--fase", default="sani", choices=["sani", "ping"],
                   help="sani = trasporto largo · ping = trasporto piu' corto "
                        "del tetto del protocollo")
    p.add_argument("--idle", type=int, default=120000,
                   help="il tetto d'inattivita' del trasporto IN VIGORE, letto "
                        "dal pari da 01-b6-lancia.sh — serve alle diagnosi")
    p.add_argument("--tetti-codice", default="",
                   help="CIAO=5000,CREDENZIALI=60000,ATTACCA=10000 — i "
                        "#define letti da banchi/rcp/rcp.c")
    p.add_argument("--solo", default="",
                   help="gira solo i casi che contengono questo")
    p.add_argument("--elenco", action="store_true",
                   help="stampa le previsioni senza misurare")
    sys.exit(asyncio.run(principale(p.parse_args())))
