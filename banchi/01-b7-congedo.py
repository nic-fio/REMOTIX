#!/usr/bin/env python3
"""01-b7-congedo.py — ⛔ B7: il congedo, letto DAL LATO CHE RICEVE.

    python3 01-b7-congedo.py --indirizzo 192.168.0.2 --porta 7447 \\
                             --registro /srv/src/b7-server.log \\
                             --pagina /srv/src/01-b11-pagina.html
    python3 01-b7-congedo.py --solo tempo-scaduto      (un caso solo)
    python3 01-b7-congedo.py --elenco                  (le previsioni, senza misurare)

⚠ Gira DENTRO il contenitore: aioquic sta li', e il registro del server anche.

===========================================================================
⛔ PERCHE' QUESTO BANCO ESISTE

`RCP.md` §8.1: *«il congedo si verifica dal lato che lo riceve, mai dal
registro di chi lo manda»*.  ⚠ E il prezzo e' gia' stato pagato: in v1, per
**tre fasi**, il server scriveva compito «congedo il client» mentre il client,
alla stessa ora, scriveva «errore di rete» (`LEZIONI.md` §1.7).  Il registro di
chi manda dice che ha chiamato una funzione, non che il byte e' arrivato.

⛔ **E le strade sono DUE, non una** — `RCP.md` §3.1, che dice in byte che cosa
vuol dire «chiudere»:

    punto 1   si SCRIVE nel registro **che cosa** non si e' capito;
    punto 2   si manda `CONGEDO` col motivo **sul canale di controllo**,
              *«se il canale di controllo e' ancora utilizzabile»*;
    punto 3   si chiude la **sessione WebTransport** con il codice d'errore
              applicativo pari al **codice del motivo** di §8.2.

⭐ Il punto 3 e' quello che §3.1 chiama *«quello che salva le diagnosi»*: se il
   congedo non arriva — stream rotto, messaggio illeggibile — il motivo viaggia
   comunque dentro la chiusura della sessione.

===========================================================================
⛔ LE DUE STRADE SI CONTANO SEPARATAMENTE, E IL PERCHE' E' UNA MISURA

`[M]` **10 agosto 2026**: «§3.1 punto 3 — motivo nella chiusura WT» dava **22 su
36** in B5, e i quattordici mancanti erano tutte violazioni trovate al **primo**
messaggio: la capsula di chiusura **non partiva affatto**, perche' il lavoro
rimandato era appeso a una condizione che nessuno faceva piu' avvenire.  ⛔ E
nessun banco se n'era accorto **perche' nessuno contava quella strada
separatamente**: bastava che il `CONGEDO` arrivasse.  La cura c'e' (il
keep-alive armato in `wt_chiudi_sessione`); **il testimone permanente e' questo
file**.

⛔ Da cui la forma del verdetto, che e' la ragione per cui B7 esiste:

    per ogni caso, il motivo giusto per TUTT'E DUE le strade dichiarate —
    una `&&`, mai una `||`

`fasi/01-filo-nudo.md` §C1 costruisce il guasto apposta: *«si toglie la
spedizione del `CONGEDO` e si lascia il codice nella chiusura: se B7 resta verde
sta facendo una `||` dove serve una `&&`»*.  Con una `||` il punto 2 sparirebbe
e il banco resterebbe verde.  Qui il punto 2 e il punto 3 hanno **due
contatori, due denominatori e due righe di rosso**.

===========================================================================
⛔ E I DUE MOTORI USANO DUE STRADE DIVERSE — `[M]` 10 agosto 2026, da B11

Quando a chiudere e' **la pagina**:

    Chrome    manda il `CONGEDO` sul canale di controllo **e** chiude la
              sessione col codice: tutt'e due le strade;
    Firefox   **azzera** il canale di controllo e butta il `CONGEDO` gia' in
              coda: il motivo arriva **solo** nel codice di chiusura.

⚠ **Un banco che le confondesse direbbe «Firefox non si congeda», che e'
  falso**: e' §3.1 punto 2 che e' *condizionato* — «se il canale e' ancora
  utilizzabile» — e su Firefox non lo e' piu'.  Il punto 3, invece, e' un DEVE
  **incondizionato**, e li' Firefox c'e'.

⭐ Percio' i due comportamenti sono **due casi distinti**, ciascuno con le sue
   strade DICHIARATE PRIMA di misurare, e i denominatori non si mescolano.  Il
   caso «alla Firefox» non toglie niente al contatore del `CONGEDO`, e il caso
   «alla Chrome» non regala niente a quello della chiusura.

===========================================================================
⛔ QUALI MOTIVI SI POSSONO DAVVERO PROVOCARE, E PERCHE' IL NUMERO E' «N SU M»

§8.2 ha **quindici** motivi.  ⛔ Stampare «8 su 8» scegliendo gli otto che si
sanno provocare e' vero **per costruzione**, ed e' la forma di verde piu' vuota
che ci sia: il denominatore va **dichiarato**, con l'elenco di quel che si e'
escluso e il perche'.  Qui i provocabili sono **sette**, e gli altri otto stanno
nella tabella `ESCLUSI` con la ragione di ciascuno — ⭐ e l'esclusione di
`SERVER_IN_CHIUSURA` non e' un'opinione: si **misura**, col `grep` di §«le
esclusioni misurate», perche' un'esclusione asserita e' un buco che nessuno
ricontrolla.

⚠ Due esclusioni valgono la pena di essere ripetute qui, perche' un banco che
  le ignorasse **fallirebbe per costruzione**: `CREDENZIALI_ERRATE` e
  `TROPPI_TENTATIVI` non viaggiano in un `CONGEDO` — §4.4 li mette in
  `RESPINTO`, e §4.4 vieta di mandare tutt'e due.  Cercarli qui sarebbe cercare
  un messaggio che il protocollo vieta.

⛔ E B7 **non sbaglia mai una parola d'ordine**: non muove nessuno dei due
   contatori di §4.4-bis, quindi non blocca l'indirizzo addosso a B8 e a B10.
   E' l'isolamento che chiede **B0.3**, ottenuto togliendo il caso invece che
   azzerando un contatore.

===========================================================================
⭐ IL CONTROLLO POSITIVO, E DOV'E'

`LEZIONI.md` §1.9 seconda regola: *«questo strumento sa trovare qualcosa che c'e'
di sicuro?»*.  B7 ha **quattro** controlli positivi, e girano PRIMA di misurare:

  1. ⭐ **i due lettori delle due strade, chiamati da fuori** su byte noti
     (`CODER.md` §3.6): la capsula di chiusura ben formata deve dare `0x0b`,
     quella **nuda** deve dare `0x0b` **e dirsi nuda**, e un mucchio di byte a
     caso deve dare **niente** — ⛔ non «zero»;
  2. ⭐ **il lettore delle frasi sa dire NO**: gli si danno in pasto quattro
     tabelle guaste — la `switch` col ramo predefinito («Errore 14»), due frasi
     uguali, la frase che e' il nome del motivo, un motivo mancante — e deve
     bocciarle tutte, dopo aver promosso quella buona;
  3. ⭐ **il lettore del registro del server sa trovare una riga che c'e'** (e
     non trovarne una che non c'e'), verificato sulla stretta di mano intera;
  4. ⭐ **lo stato iniziale** (B0.1, B0.2): una stretta di mano intera fino a
     `SESSIONE`.  ⛔ Senza, il caso `GIA_ATTIVA_REMOTA` sarebbe **verde per la
     ragione sbagliata** — un posto lasciato occupato dal giro precedente fa
     rispondere `0x0F` a chiunque, e il banco lo leggerebbe come bravura.

⛔ Se uno dei quattro fallisce il banco esce **3** e non misura niente: un esito
   negativo con lo strumento non certificato e' ambiguo fra «non funziona il
   server» e «non funzionava il banco» (`CODER.md` §3.3).

===========================================================================
⛔ QUEL CHE B7 NON PROVA, E VA DETTO

  · **che la frase arrivi davvero sotto gli occhi dell'utente.**  Qui si legge
    la **tabella** del client, non lo schermo: «il banco guarda lo schermo» non
    e' eseguibile, e l'unica cosa che una prova automatica puo' fare e' leggere
    il DOM — che vuole un browser.  ⛔ Il giudizio su cio' che si VEDE resta
    dell'utente (**I8**), e va nel giudizio, non in questa tabella;
  · **il valore dei tetti di §4.6.**  Il caso `tempo-scaduto` pretende il
    *motivo* `TEMPO_SCADUTO` per tutt'e due le strade, e **stampa** quanto ha
    aspettato: i cinque secondi li misura **B6**, e duplicare qui una soglia
    darebbe due verdetti diversi sulla stessa proprieta';
  · **il verso client→server, sul filo.**  Li' chi riceve e' il server, e
    l'unico testimone e' il suo registro.  ⚠ Non e' la violazione di §8.1: §8.1
    vieta di leggere il congedo dal registro di **chi lo manda**.  Qui chi manda
    e' il banco.  ⭐ E per non poggiare su una sola gamba, quei due casi
    verificano **anche sul filo** una conseguenza osservabile: che il posto sia
    stato lasciato (§8.2 `0x0F`), con una connessione nuova che arriva a
    `SESSIONE`.
"""
import argparse
import asyncio
import contextlib
import importlib.util
import os
import re
import signal
import ssl
import struct
import sys

from aioquic.h3.connection import H3_ALPN
from aioquic.quic.configuration import QuicConfiguration
from aioquic.asyncio import connect

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ Il cliente di B3 si IMPORTA, non si ricopia.  Dentro c'e' la riga che gli
#    impedisce di dare gli eventi del canale di controllo allo strato HTTP/3 di
#    aioquic — senza la quale la connessione muore per mano del CLIENT (10
#    agosto 2026) — e c'e' `_capsula_chiusura`, cioe' il lettore della seconda
#    strada di §3.1.  Una copia divergente riporterebbe qui quei difetti
#    travestiti da difetti del server.
_spec = importlib.util.spec_from_file_location(
    "b3cliente", os.path.join(QUI, "01-b3-cliente.py"))
b3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b3)

# ⛔ E il profilo del BERSAGLIO: le differenze fra i due server stanno in un
#    file solo, e i quattro banchi le leggono invece di scoprirle da capo.
_spec_b0 = importlib.util.spec_from_file_location(
    "b0bersaglio", os.path.join(QUI, "01-b0-bersaglio.py"))
b0 = importlib.util.module_from_spec(_spec_b0)
_spec_b0.loader.exec_module(b0)

s, inquadra = b3.s, b3.inquadra

CONGEDO, RESPINTO = 0x000C, 0x0005

# ⛔ §8.2 PER INTERO, riscritto da `RCP.md` e non importato da nessuno.
#
#    `01-b3-cliente.py` ne conosce otto: gli bastano.  Qui servono tutti e
#    quindici, perche' il denominatore di B7 e' §8.2 intera — e perche' questa
#    tabella e' il **secondo lettore** con cui si giudica quella della pagina.
#    ⚠ Due tabelle scritte dalla stessa mano non confermano niente: questa
#      viene da §8.2, quella da chi ha scritto la pagina.
MOTIVI = {
    0x01: "CHIUSO_DALL_UTENTE", 0x02: "INATTIVITA",
    0x03: "SESSIONE_ABBANDONATA", 0x04: "SESSIONE_LOCALE_PREVALSA",
    0x05: "GIA_ATTIVA_LOCALE", 0x06: "BUDGET_PIENO",
    0x07: "CREDENZIALI_ERRATE", 0x08: "TROPPI_TENTATIVI",
    0x09: "NIENTE_IN_COMUNE", 0x0A: "VERSIONE_INCOMPATIBILE",
    0x0B: "ERRORE_PROTOCOLLO", 0x0C: "SERVER_IN_CHIUSURA",
    0x0D: "TEMPO_SCADUTO", 0x0E: "SESSIONE_NON_SERVIBILE",
    0x0F: "GIA_ATTIVA_REMOTA",
}

CHIUSO_DALL_UTENTE = 0x01
NIENTE_IN_COMUNE = 0x09
VERSIONE_INCOMPATIBILE = 0x0A
ERRORE_PROTOCOLLO = 0x0B
SERVER_IN_CHIUSURA = 0x0C
TEMPO_SCADUTO = 0x0D
SESSIONE_NON_SERVIBILE = 0x0E
GIA_ATTIVA_REMOTA = 0x0F

# ===========================================================================
# ⛔ IL DENOMINATORE, DICHIARATO — «N su M provocabili», e M sta qui.
#
#    Ogni riga di `ESCLUSI` porta il motivo per cui la fase 1 non lo sa
#    produrre.  ⚠ Chi aggiunge un motivo ai provocabili deve toglierlo di qui:
#    le due tabelle insieme devono fare quindici, e `certifica_denominatore()`
#    lo verifica invece di fidarsi.
# ===========================================================================
ESCLUSI = [
    (0x02, "30 minuti senza INPUT: il canale di input nasce alla fase 4 e "
           "l'orologio alla fase 5"),
    (0x03, "6 ore senza attacchi: e' un orologio della SESSIONE, fase 5"),
    (0x04, "vuole una sessione grafica LOCALE vera che prevalga: il palco "
           "nasce alla fase 2"),
    (0x05, "idem: per dirlo, il server deve saper guardare le sessioni "
           "locali della macchina (fase 2)"),
    (0x06, "vuole la capacita' di codifica, che nasce alla fase 3"),
    (0x07, "⛔ NON viaggia in un CONGEDO: §4.4 lo mette in RESPINTO, e vieta "
           "di mandare tutt'e due.  Cercarlo qui fallirebbe per costruzione "
           "— lo misurano B5 e B8"),
    (0x08, "idem, RESPINTO (§4.4-bis) — ⛔ e provocarlo bloccherebbe questo "
           "indirizzo per almeno 30 s, cioe' avvelenerebbe B8 e B10 (B0.3)"),
    (0x0C, "⛔ l'INNESTO non ha un percorso di spegnimento: "
           "`RCP_SERVER_IN_CHIUSURA` non compare in nessuna riga di "
           "`01-b3-rcp-innesta.py`.  ⚠ MISURATO qui sotto col grep, non "
           "supposto.  ⭐ E su `--bersaglio prodotto` questa riga SPARISCE: "
           "`src/main.c` congeda tutti con SERVER_IN_CHIUSURA prima di "
           "uscire, e i provocabili diventano OTTO"),
]


# ⛔⭐ IL DENOMINATORE DIPENDE DAL BERSAGLIO — ed e' la differenza fra i due
#     server che si vede da un NUMERO invece che da un comportamento.
#
#       innesto    SETTE provocabili + otto  esclusi = 15
#       prodotto   OTTO  provocabili + sette esclusi = 15
#
# ⛔ *«Il numero da scrivere accanto a un esito e' quello del bersaglio che si e'
#    acceso»* (`fasi/01-filo-nudo.md` B7).  ⚠ E se B7 puntato al prodotto
#    continuasse a dire «sette su sette», il denominatore sarebbe sbagliato e il
#    banco starebbe guardando dall'altra parte: sarebbe un verde per costruzione,
#    la forma piu' vuota che ci sia.
def esclusi_di(bersaglio):
    if b0.profilo(bersaglio)["spegnimento"]:
        return [(c, perche) for c, perche in ESCLUSI if c != SERVER_IN_CHIUSURA]
    return list(ESCLUSI)


def casi_di(bersaglio, tutti=None):
    """I casi che QUESTO bersaglio sa produrre.

    ⛔ `server-in-chiusura` esiste solo contro il prodotto: contro l'innesto
       resterebbe ad aspettare un congedo che nessuna riga di codice puo'
       mandare, e il suo rosso accuserebbe il server di non fare una cosa che
       nessuno gli ha mai insegnato."""
    fuori = []
    for c in (tutti if tutti is not None else CASI):
        if c[1] == SERVER_IN_CHIUSURA and not b0.profilo(bersaglio)["spegnimento"]:
            continue
        fuori.append(c)
    return fuori


# ---------------------------------------------------------------------------
# I byte, scritti a mano.
def capacita(voci, versione=1):
    out = struct.pack("!HH", versione, len(voci))
    for n, v in voci:
        out += s(n) + s(v)
    return out


BUONE = [("video.codec", "hevc,av1"), ("video.profondita", "8,10"),
         ("audio.codec", "opus,pcm"), ("client.nome", "banco-b7 0.1.0")]


def ciao(voci=None, versione=1):
    return inquadra(0x0001, capacita(BUONE if voci is None else voci, versione))


def attacca(tl=1920, ta=1080, vl=1920, va=1080, disp="it"):
    return inquadra(0x0006, struct.pack("!IIII", tl, ta, vl, va) + s(disp))


def congedo(motivo, dettaglio):
    """§7.1: `CONGEDO` = `u8 motivo` + `stringa dettaglio`."""
    return inquadra(CONGEDO, bytes([motivo]) + s(dettaglio))


def capsula_chiusura(motivo):
    """I nove byte con cui si chiude una sessione WebTransport (§3.1 punto 3).

    ⛔ La capsula `CLOSE_WEBTRANSPORT_SESSION` (tipo `0x2843`) va **dentro un
       frame `DATA`** di HTTP/3 (RFC 9297): sul filo della CONNECT estesa il
       corpo e' un flusso di capsule, e in HTTP/3 il corpo viaggia in `DATA`.
       Scritta nuda, `0x68 0x43 …` si legge come un tipo di frame HTTP/3
       sconosciuto, e RFC 9114 §9 impone di **ignorarlo**: il motivo sparisce e
       resta solo il `FIN`, che vale «chiusura senza motivo», cioe' il codice
       **0** che §3.1 vieta.  ⚠ E' il difetto che il server ha avuto fino al 10
       agosto 2026 (rilievo R10.1), qui dal lato del client.
    """
    return bytes([0x00, 7,             # frame DATA, 7 byte di capsula
                  0x68, 0x43,          # 0x2843 in intero variabile
                  4, 0, 0, 0, motivo])  # lunghezza, e il codice su 4 byte


class Cliente(b3.Cliente):
    """Il cliente di B3, piu' i due modi di CHIUDERE (§3.1, §8.1)."""

    def chiudi_sessione(self, motivo):
        """§3.1 punto 3 dal lato del client: la capsula col motivo, poi il FIN."""
        self._quic.send_stream_data(self.sessione, capsula_chiusura(motivo),
                                    end_stream=True)
        self.transmit()

    def azzera_controllo(self, codice=0):
        """⛔ Quel che fa Firefox: il canale di controllo si AZZERA.

        Da quell'istante §3.1 punto 2 non e' piu' esigibile — «se il canale di
        controllo e' ancora utilizzabile» —, e il motivo puo' viaggiare solo per
        la seconda strada.  ⚠ Se `aioquic` non sapesse azzerare uno stream il
        caso non imiterebbe niente: si DICHIARA invece di ripiegare in silenzio
        (`CODER.md` §4.2).
        """
        if not hasattr(self._quic, "reset_stream"):
            raise RuntimeError(
                "questo aioquic non ha `reset_stream`: il caso «alla Firefox» "
                "non e' imitabile, e fingere di averlo fatto sarebbe un verde "
                "senza prova")
        self._quic.reset_stream(self.controllo, codice)
        self.transmit()


# ===========================================================================
# ⛔ IL REGISTRO DEL SERVER — dove si legge, e dove NON si legge.
#
#    §8.1: *«il congedo si verifica dal lato che lo riceve, mai dal registro di
#    chi lo manda»*.  Qui il registro del server si usa per due cose sole, e
#    nessuna delle due e' il verdetto sul motivo che il server MANDA:
#
#      · **§3.1 punto 1** — la riga «che cosa non ho capito».  E' per
#        definizione una riga di chi chiude: e' il punto 1 a chiederla;
#      · **il verso client→server** — dove chi riceve E' il server, e il suo
#        registro e' il lato che riceve.
#
#    ⛔ Il motivo che il server manda lo giudicano sempre e solo le due strade,
#       lette sul filo da questo processo.
# ===========================================================================
class Registro:
    def __init__(self, percorso):
        self.percorso = percorso
        self.errore = None

    def leggibile(self):
        """⛔ «Non c'e' niente» e «non si legge» hanno lo stesso aspetto."""
        if not self.percorso:
            return False, "nessun registro dichiarato (--registro)"
        if not os.path.exists(self.percorso):
            return False, f"{self.percorso} NON ESISTE"
        try:
            with open(self.percorso, "rb") as f:
                f.read(1)
        except OSError as e:
            return False, f"{self.percorso} non si legge: {e}"
        return True, ""

    def finestra(self):
        """Il segno di spunta da cui guardare: quanto era lungo il file adesso.

        ⭐ E' un marcatore, non un `sleep` (B0.7): quel che si giudica sono i
           byte scritti DOPO questo istante, e le righe dei casi precedenti non
           possono piu' entrare in un verdetto che non e' loro.
        """
        try:
            return os.path.getsize(self.percorso)
        except OSError:
            return None

    def da(self, inizio):
        """Il testo scritto dopo il marcatore.  `None` se non si legge."""
        if inizio is None:
            return None
        try:
            with open(self.percorso, "rb") as f:
                f.seek(inizio)
                return f.read().decode("utf-8", "replace")
        except OSError as e:
            self.errore = str(e)
            return None

    async def attendi(self, inizio, frase, entro=6.0):
        """Aspetta che una riga compaia, e dice se e' comparsa.

        ⚠ Si aspetta perche' il registro e' scritto da un altro processo e i
          due non condividono un orologio: leggere nell'istante esatto in cui
          si e' spedito misurerebbe la nostra fretta.  ⛔ La finestra e'
          dichiarata e limitata: se scade, la risposta e' «non entro N s», non
          «non c'e'».
        """
        fine = asyncio.get_event_loop().time() + entro
        while True:
            testo = self.da(inizio)
            if testo is None:
                return False, "il registro non si legge"
            if frase in testo:
                return True, ""
            if asyncio.get_event_loop().time() >= fine:
                return False, f"non comparsa entro {entro:.0f} s"
            await asyncio.sleep(0.05)

    def righe_nostre(self, inizio, quante=14):
        """Le righe di RCP scritte nella finestra — per la diagnosi, non per il
        verdetto.  ⚠ Si filtra il traffico di ngtcp2, che qui e' rumore."""
        testo = self.da(inizio)
        if testo is None:
            return ["(il registro non si legge)"]
        righe = [r for r in testo.splitlines() if "REMOTIX" in r]
        return righe[-quante:] if righe else ["(nessuna riga di RCP)"]


# ===========================================================================
# ⭐ LE FRASI DI §8.2 — «BUDGET_PIENO non e' "errore 6"»
#
# §8.2: *«ogni motivo DEVE essere mostrabile all'utente in una frase
# comprensibile … e la frase la costruisce il client, dal codice»*.  ⛔ E il
# `dettaglio` NON si mostra: e' per il registro.
#
# ⛔ «Quindici su quindici» non basta, ed e' il rilievo R3.20: una `switch` col
#    ramo predefinito — `mostra("Errore " + codice)` — produce quindici stringhe
#    non vuote **e tutte distinte fra loro**.  L'utente legge «Errore 14» per
#    `SESSIONE_NON_SERVIBILE`, che §8.2 vieta con un ⛔ e un esempio quasi
#    identico.  Percio' i criteri sono quattro, e il secondo e' quello che
#    smaschera la `switch`.
# ===========================================================================
ANCORA_TABELLA = "const MOTIVO = new Map(["
VOCE = re.compile(r'\[\s*0x([0-9A-Fa-f]{1,2})\s*,\s*\[\s*"([^"]*)"\s*,\s*"([^"]*)"\s*\]')


def leggi_tabella(testo):
    """Estrae {codice: (nome, frase)} dalla tabella del client.

    ⛔ Torna `(None, perche')` quando la tabella non si e' letta: «zero frasi» e
       «non ho trovato la tabella» sono due fatti diversi, e confonderli
       darebbe un rosso al client per un difetto del banco.
    """
    i = testo.find(ANCORA_TABELLA)
    if i < 0:
        return None, f"l'appiglio «{ANCORA_TABELLA}» non c'e' in questo file"
    j = testo.find("]);", i)
    if j < 0:
        return None, "la tabella comincia e non finisce: manca «]);»"
    voci = {}
    for m in VOCE.finditer(testo[i:j]):
        voci[int(m.group(1), 16)] = (m.group(2), m.group(3))
    if not voci:
        return None, "l'appiglio c'e' ma nessuna voce combacia con la forma attesa"
    return voci, ""


def giudica_frasi(voci):
    """I quattro criteri, uno per volta, con il perche' del no.

    Torna [(codice, ok, perche')] per tutti e quindici i motivi di §8.2.
    """
    fuori = []
    viste = {}
    for c in sorted(MOTIVI):
        nome_atteso = MOTIVI[c]
        if c not in voci:
            fuori.append((c, False, "⛔ il motivo non e' nella tabella del "
                                    "client: non c'e' nessuna frase da mostrare"))
            continue
        nome, frase = voci[c]
        f = frase.strip()
        chiave = " ".join(f.lower().split())
        if nome != nome_atteso:
            fuori.append((c, False, f"il nome dice «{nome}», §8.2 dice "
                                    f"«{nome_atteso}»"))
            continue
        # 1. una frase, non un'etichetta
        if len(f.split()) < 3:
            fuori.append((c, False, f"«{f}» non e' una frase ({len(f.split())} "
                                    f"parole): §8.2 vuole qualcosa di "
                                    f"mostrabile all'utente"))
            continue
        # 2. ⛔ nessun numero del motivo, e nessun «errore N» — la switch
        #    col ramo predefinito muore qui.
        if re.search(r"(?<![0-9])%d(?![0-9])" % c, f) or \
           re.search(r"0x0?%x" % c, f, re.I) or \
           re.search(r"errore\s*[:\-]?\s*[0-9]", f, re.I):
            fuori.append((c, False, f"⛔ «{f}» contiene il NUMERO del motivo: "
                                    f"§8.2 vieta «errore {c}»"))
            continue
        # 3. il nome del motivo non e' una frase per l'utente
        if nome.lower() in f.lower() or nome in f:
            fuori.append((c, False, f"⛔ «{f}» e' il NOME del motivo, non una "
                                    f"frase: e' un numero scritto in lettere"))
            continue
        # 4. distinte fra loro
        if chiave in viste:
            fuori.append((c, False, f"⛔ la stessa frase di "
                                    f"{MOTIVI[viste[chiave]]}: due motivi "
                                    f"diversi che dicono la stessa cosa"))
            continue
        viste[chiave] = c
        fuori.append((c, True, f))
    return fuori


# ---------------------------------------------------------------------------
# ⭐ LE TABELLE FINTE — il controllo positivo E quello che dice NO.
#
# ⚠ Le frasi buone non contengono NESSUNA cifra, di proposito: il criterio 2
#   cerca il numero del motivo, e una frase di prova che ne portasse uno per
#   caso farebbe fallire il controllo positivo dando la colpa al lettore.
def _tabella_finta(frase_di):
    return {c: (MOTIVI[c], frase_di(c)) for c in MOTIVI}


def _buone():
    return _tabella_finta(
        lambda c: f"questa e' la frase {chr(96 + c)} da mostrare all'utente")


def certifica_frasi():
    """⭐ Lo strumento che giudica le frasi sa dire di si', e sa dire di no.

    ⛔ Senza questo, «quindici su quindici» e' compatibile con un lettore che
       approva qualunque cosa — ed e' il difetto che B11 ha dovuto curare sulla
       pagina, qui applicato a chi legge.

    ⚠ La tabella guasta piu' importante e' la seconda: la `switch` col ramo
      predefinito produce quindici stringhe non vuote **e tutte distinte**, cioe'
      passa ogni criterio tranne quello che R3.20 ha dovuto scrivere apposta.
    """
    doppia = _buone()
    doppia[0x03] = (MOTIVI[0x03], doppia[0x04][1])
    mancante = _buone()
    del mancante[0x0E]
    # ⚠ Le guaste sono scritte come le scriverebbe qualcuno in buona fede —
    #   frasi intere, lunghe, distinte — perche' una guasta troppo goffa
    #   verrebbe bocciata dal criterio SBAGLIATO, e il controllo non
    #   dimostrerebbe niente sul criterio che serve.
    prove = [
        ("una tabella buona", _buone(), True),
        ("⛔ la switch col ramo predefinito",
         _tabella_finta(lambda c: f"Errore {c} durante la connessione al "
                                  f"server"), False),
        ("⛔ e la stessa cosa scritta in esadecimale",
         _tabella_finta(lambda c: f"la sessione si e' chiusa col codice "
                                  f"0x{c:02x}, riprovare"), False),
        ("⛔ due motivi con la stessa frase", doppia, False),
        ("⛔ la frase che porta il NOME del motivo",
         _tabella_finta(lambda c: f"il server ha risposto {MOTIVI[c]} a "
                                  f"questa richiesta"), False),
        ("⛔ un motivo che manca del tutto", mancante, False),
        ("⛔ un'etichetta invece di una frase",
         _tabella_finta(lambda c: "non servibile"), False),
    ]
    fuori = []
    for nome, voci, atteso in prove:
        esiti = giudica_frasi(voci)
        passa = all(ok for _, ok, _ in esiti)
        fuori.append((nome, passa == atteso,
                      "promossa" if passa else
                      "bocciata: " + next(p for _, ok, p in esiti
                                          if not ok)[:78]))
    return fuori


def certifica_lettori():
    """⭐ I DUE LETTORI DELLE DUE STRADE, chiamati da fuori su byte noti.

    `CODER.md` §3.6: quando la catena e' gia' ristretta, non si fa un altro giro
    di banco — si chiama la sola funzione sospetta su un ingresso noto.  ⛔ E
    senza questo, un «il motivo non e' arrivato» resta ambiguo fra «il server
    non l'ha mandato» e «il banco non lo sa leggere» — cioe' esattamente il
    difetto che B7 esiste per non fare.
    """
    prove = []

    # ── strada 2: la capsula di chiusura ────────────────────────────────────
    c, nuda = b3._capsula_chiusura(capsula_chiusura(0x0B))
    prove.append(("la capsula dentro il frame DATA", (c, nuda) == (0x0B, False),
                  f"letto {c!r}, nuda={nuda}  (atteso 11, False)"))
    c, nuda = b3._capsula_chiusura(capsula_chiusura(0x0B)[2:])
    prove.append(("⛔ la capsula NUDA si legge E si dichiara",
                  (c, nuda) == (0x0B, True),
                  f"letto {c!r}, nuda={nuda}  (atteso 11, True)"))
    c, nuda = b3._capsula_chiusura(b"\x99\x99\x99\x99")
    prove.append(("⛔ e su byte a caso dice NIENTE, non zero", c is None,
                  f"letto {c!r}  (atteso None — «0» sarebbe il codice che "
                  f"§3.1 vieta)"))

    # ── strada 1: l'inquadratura del CONGEDO ────────────────────────────────
    #    Si chiama il `_sfoglia` VERO, quello che gira sul filo, da fuori.
    class Finto:
        def __init__(self):
            self.arrivati = bytearray()
            self.messaggi = asyncio.Queue()

    f = Finto()
    f.arrivati += congedo(0x0E, "disposizione sconosciuta: zz")
    b3.Cliente._sfoglia(f)
    try:
        tipo, corpo, _ = f.messaggi.get_nowait()
        ok = (tipo == CONGEDO and corpo[0] == 0x0E)
        det = struct.unpack("!H", corpo[1:3])[0]
        ok = ok and corpo[3:3 + det].decode() == "disposizione sconosciuta: zz"
        prove.append(("il CONGEDO si sfoglia, motivo e dettaglio", ok,
                      f"tipo={tipo:#06x} motivo={corpo[0]:#04x}"))
    except asyncio.QueueEmpty:
        prove.append(("il CONGEDO si sfoglia, motivo e dettaglio", False,
                      "nessun messaggio dal lettore"))

    f = Finto()
    f.arrivati += congedo(0x0E, "tronco")[:-3]
    b3.Cliente._sfoglia(f)
    prove.append(("⛔ e un CONGEDO troncato NON diventa un motivo",
                  f.messaggi.empty(),
                  "il lettore ha prodotto un messaggio da byte incompleti"
                  if not f.messaggi.empty() else "niente, come deve"))
    return prove


def certifica_denominatore(casi, esclusi_lista=None):
    """⛔ M + gli esclusi devono fare quindici, e il conto lo fa il programma.

    Un numero scritto a mano in un commento e' il numero che nessuno
    ricalcola: il rilievo R7.14 ne ha trovati tre in B5, e nessuno dei tre
    tornava col file.
    """
    provocabili = {c[1] for c in casi}
    esclusi = {c for c, _ in (esclusi_lista if esclusi_lista is not None
                              else ESCLUSI)}
    doppi = provocabili & esclusi
    tutti = provocabili | esclusi
    if doppi:
        return False, ("questi motivi sono provocabili E esclusi: "
                       + " ".join(MOTIVI[c] for c in sorted(doppi)))
    if tutti != set(MOTIVI):
        manca = set(MOTIVI) - tutti
        return False, ("§8.2 ha 15 motivi e questo banco ne nomina "
                       f"{len(tutti)}: mancano "
                       + " ".join(MOTIVI[c] for c in sorted(manca)))
    return True, (f"{len(provocabili)} provocabili + {len(esclusi)} esclusi "
                  f"= {len(MOTIVI)} motivi di §8.2")


# ===========================================================================
# ⛔ LE ESCLUSIONI SI MISURANO — quella di `SERVER_IN_CHIUSURA` soprattutto.
# ===========================================================================
def esclusione_misurata(sorgenti):
    """Quante volte `RCP_SERVER_IN_CHIUSURA` compare nei sorgenti DEL BERSAGLIO.

    ⛔⭐ E I SORGENTI NON SONO `rcp.c`, o non solo.  Fino all'11 agosto 2026
        questa funzione guardava `rcp.c` e basta — e `rcp.c` e' **identico byte
        per byte nei due server** (md5 `cb7af778…`).  Puntata al prodotto
        avrebbe detto «zero occorrenze», cioe' avrebbe dichiarato NON
        producibile un motivo che il prodotto produce, e B7 avrebbe stampato
        «7 su 7» su un server che ne fa otto.
        ⚠ E' `LEZIONI.md` §1.9 corollario 5 in casa nostra: *un denominatore si
        legge dove la cosa succede*.  Un percorso di spegnimento non puo' vivere
        in `rcp.c`, che non sa nemmeno che esista un processo: sul prodotto vive
        in `main.c`, `trasporto.c` e `webtransport.c`.

    ⭐ Il controllo positivo resta nella stessa riga: `RCP_TEMPO_SCADUTO` c'e'
       di sicuro, e se il lettore non trovasse nemmeno quello il suo «zero» non
       varrebbe niente.

    Torna `(quanti, testo)`, con `quanti = None` se non si e' potuto guardare.
    """
    quanti, controllo, letti, mancati = 0, 0, [], []
    for sorgente in sorgenti:
        try:
            with open(sorgente, encoding="utf-8", errors="replace") as f:
                testo = f.read()
        except OSError as e:
            mancati.append(f"{os.path.basename(sorgente)} ({e.strerror})")
            continue
        quanti += testo.count("RCP_SERVER_IN_CHIUSURA")
        controllo += testo.count("RCP_TEMPO_SCADUTO")
        letti.append(os.path.basename(sorgente))
    if mancati:
        return None, (f"⛔ {len(mancati)} sorgenti su {len(sorgenti)} non si "
                      f"leggono ({', '.join(mancati)}): l'esclusione resterebbe "
                      f"ASSERITA invece che misurata")
    if controllo == 0:
        return None, ("⛔ il lettore non trova nemmeno `RCP_TEMPO_SCADUTO`, "
                      "che c'e' di sicuro: il suo «zero» non vale niente")
    return quanti, (f"`RCP_SERVER_IN_CHIUSURA`: {quanti} occorrenze in "
                    f"{len(letti)} file ({', '.join(letti)})  ·  controllo "
                    f"positivo `RCP_TEMPO_SCADUTO`: {controllo}")


# ===========================================================================
# Che cosa e' successo, dal lato che riceve.
# ===========================================================================
class Esito:
    def __init__(self, verso=None):
        self.verso = verso
        self.motivo = None        # dal CONGEDO — MAI dedotto, MAI dal registro
        self.tipo_motivo = None   # ⛔ in QUALE messaggio (§11, §4.4)
        self.dettaglio = ""
        self.codice_wt = None     # §3.1 punto 3, letto sul filo
        self.riga_registro = None # §3.1 punto 1
        self.al_server = {}       # il verso client→server, dal registro
        self.posto_libero = None  # la conseguenza osservabile sul filo
        self.messaggi = []
        self.provocato = False    # ⛔ la provocazione e' partita davvero?
        self.fase = "apertura"
        self.attesa_ms = None
        self.errore = None

    def __str__(self):
        p = []
        if not self.provocato:
            p.append(f"⛔ provocazione MAI PARTITA (fermo in «{self.fase}»)")
        # ⚠ Le due prime voci dicono che cosa ha ricevuto QUESTO processo:
        #   hanno senso solo quando a chiudere e' il server.  Nell'altro verso
        #   chi riceve e' lui, e stamparle «assenti» inviterebbe a leggere un
        #   silenzio come un guasto.
        if self.verso != VERSO_CS:
            if self.motivo is not None:
                p.append(f"CONGEDO={self.motivo:#04x}="
                         f"{MOTIVI.get(self.motivo, '?')} in {self.tipo_motivo}")
            elif self.tipo_motivo is not None:
                p.append(f"{self.tipo_motivo} senza motivo leggibile")
            else:
                p.append("CONGEDO=(assente)")
            p.append("chiusura-WT=" + ("(assente)" if self.codice_wt is None
                                       else f"{self.codice_wt:#04x}"))
        for k, v in self.al_server.items():
            p.append(f"{k}={'si' if v else 'NO'}")
        if self.posto_libero is not None:
            p.append("posto=" + ("libero" if self.posto_libero else "OCCUPATO"))
        if self.attesa_ms is not None:
            p.append(f"dopo {self.attesa_ms:.0f} ms")
        if self.errore:
            p.append(f"errore={self.errore}")
        return "  ".join(p)


async def osserva(cli, es, attesa, grazia=3.0):
    """⛔ Le due strade, e si aspettano TUTT'E DUE — anche quando la prima manca.

    Il `CONGEDO` viaggia sul canale di controllo, la chiusura della sessione e'
    una capsula sullo stream della CONNECT: sono due strade e arrivano in due
    momenti diversi.  ⭐ Il server le distanzia apposta di cinque passate di
    scrittura (mezzo secondo), perche' altrimenti il browser processa la capsula
    prima dei byte dello stream e **il `CONGEDO` non lo vede nessuno**.

    ⛔ E la grazia si aspetta ANCHE se il `CONGEDO` non e' arrivato: e' il caso
       del guasto di §C1 — congedo tolto, codice lasciato — e un banco che
       smettesse di guardare la seconda strada quando manca la prima non
       saprebbe dire QUALE delle due manca.
    """
    orologio = asyncio.get_event_loop().time
    t0 = orologio()
    scadenza = t0 + attesa
    while True:
        resta = scadenza - orologio()
        if resta <= 0:
            break
        try:
            m = await asyncio.wait_for(cli.messaggi.get(), timeout=resta)
        except asyncio.TimeoutError:
            break
        if m is None:            # connessione terminata, o FIN sul controllo
            break
        tipo, corpo, _ = m
        es.messaggi.append(tipo)
        if tipo in (CONGEDO, RESPINTO):
            es.tipo_motivo = "CONGEDO" if tipo == CONGEDO else "RESPINTO"
            es.attesa_ms = (orologio() - t0) * 1000
            # ⛔ Un corpo VUOTO non e' «nessun motivo»: §7.1 vuole il byte del
            #    motivo, e §3.1 vieta il codice 0.  Con `corpo[0] if corpo`
            #    un server che chiude MALE sarebbe piu' facile da far passare
            #    di uno che chiude bene (rilievo R7.2).
            if not corpo:
                es.errore = (f"{es.tipo_motivo} con corpo VUOTO: §7.1 ne vuole "
                             "almeno il byte del motivo")
                break
            es.motivo = corpo[0]
            if tipo == CONGEDO and len(corpo) >= 3:
                n = struct.unpack("!H", corpo[1:3])[0]
                es.dettaglio = corpo[3:3 + n].decode("utf-8", "replace")
            break
    fine = orologio() + grazia
    while cli.codice_chiusura is None and orologio() < fine:
        await asyncio.sleep(0.02)
    es.codice_wt = cli.codice_chiusura


# ===========================================================================
# Il campo: le connessioni di un caso, e la loro chiusura.
# ===========================================================================
class Campo:
    def __init__(self, a, pila, registro, inizio):
        self.a = a
        self.pila = pila
        self.registro = registro
        self.inizio = inizio      # il marcatore nel registro del server

    async def apri(self, percorso="/rcp/1"):
        conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                                 max_datagram_frame_size=65536)
        conf.verify_mode = ssl.CERT_NONE
        autorita = f"{self.a.indirizzo}:{self.a.porta}"
        gestore = connect(self.a.indirizzo, self.a.porta, configuration=conf,
                          create_protocol=Cliente)
        cli = await gestore.__aenter__()
        self.pila.push_async_callback(chiudi_piano, gestore)
        await asyncio.wait_for(cli.wait_connected(), timeout=8)
        cli.apri_sessione(autorita, percorso)
        stato = await asyncio.wait_for(cli.accettata, timeout=8)
        if stato != "200":
            raise RuntimeError(f"la CONNECT estesa ha risposto {stato}")
        return cli

    async def eccomi(self, cli, corpo=None):
        cli.apri_controllo()
        cli.manda(corpo if corpo is not None else ciao())
        return await b3.attendi(cli, "ECCOMI")

    async def ammesso(self, cli):
        await self.eccomi(cli)
        cli.manda(inquadra(0x0003, s(self.a.utente) + s(self.a.parola)))
        return await b3.attendi(cli, "AMMESSO", attesa=20)

    async def sessione(self, cli, disp="it"):
        await self.ammesso(cli)
        cli.manda(attacca(disp=disp))
        return await b3.attendi(cli, "SESSIONE")


async def chiudi_piano(gestore):
    try:
        await gestore.__aexit__(None, None, None)
    except Exception:  # noqa: BLE001
        pass


# ===========================================================================
# ⛔ I CASI.  Ciascuno dichiara PRIMA di misurare: il motivo atteso, il verso, e
#    **quali strade di §3.1 sono esigibili** — che e' la dichiarazione che
#    impedisce di dire «Firefox non si congeda».
# ===========================================================================
CASI = []
VERSO_SC, VERSO_CS = "server→client", "client→server"


def caso(nome, motivo, verso, strade, spiega):
    def dec(f):
        CASI.append((nome, motivo, verso, strade, spiega, f))
        return f
    return dec


# ── il verso server→client: le due strade si pretendono tutt'e due ─────────
#
# ⛔ In TUTTI questi casi il canale di controllo e' aperto e utilizzabile
#    nell'istante in cui il server congeda — lo apre il banco, e il server non
#    congeda prima che esista.  Quindi qui il condizionale di §3.1 punto 2
#    **non morde**, e pretendere il `CONGEDO` non e' dare rosso a codice giusto
#    (che era il timore del rilievo R3.3).  Il caso in cui il condizionale morde
#    e' nell'altro verso, ed e' `chiuso-dall-utente-alla-firefox`.
@caso("errore-protocollo", ERRORE_PROTOCOLLO, VERSO_SC, ("congedo", "chiusura"),
      "un tipo che non esiste sul canale di controllo: §3 vieta di ignorarlo")
async def _(campo, es):
    cli = await campo.apri()
    await campo.eccomi(cli)
    es.fase = "provocazione"
    cli.manda(inquadra(0x00FF, b""))
    es.provocato = True
    await osserva(cli, es, attesa=12)


@caso("versione-incompatibile", VERSIONE_INCOMPATIBILE, VERSO_SC,
      ("congedo", "chiusura"),
      "CIAO(versione=2) su /rcp/1: §2.2 vuole che le due coincidano")
async def _(campo, es):
    cli = await campo.apri()
    cli.apri_controllo()
    es.fase = "provocazione"
    cli.manda(ciao(versione=2))
    es.provocato = True
    await osserva(cli, es, attesa=12)


@caso("niente-in-comune", NIENTE_IN_COMUNE, VERSO_SC, ("congedo", "chiusura"),
      "`audio.codec = opus` senza `pcm`: §4.3 lo impone a entrambi i lati, e "
      "chi non lo dichiara si congeda con NIENTE_IN_COMUNE — non con "
      "ERRORE_PROTOCOLLO: non ha sbagliato a scrivere, non ha di che parlare")
async def _(campo, es):
    cli = await campo.apri()
    cli.apri_controllo()
    es.fase = "provocazione"
    cli.manda(ciao([("video.codec", "hevc"), ("video.profondita", "8"),
                    ("audio.codec", "opus")]))
    es.provocato = True
    await osserva(cli, es, attesa=12)


@caso("tempo-scaduto", TEMPO_SCADUTO, VERSO_SC, ("congedo", "chiusura"),
      "si apre il canale di controllo e SI TACE: §4.6, il tetto per il CIAO. "
      "⚠ B7 pretende il MOTIVO, non il valore del tetto: i secondi li misura B6")
async def _(campo, es):
    cli = await campo.apri()
    cli.apri_controllo()
    # ⛔⭐ E QUI SI SPINGE, PERCHE' IL SILENZIO NON SI SPEDISCE DA SE'.
    #
    #    `create_webtransport_stream` scrive l'intestazione dello stream —
    #    `0x41` piu' l'identificatore della sessione — ma `aioquic` non manda
    #    niente finche' non gli si dice `transmit()`.  ⚠ Senza questa riga il
    #    server non vedrebbe **nessuno** stream, non aprirebbe nessuna sessione
    #    RCP, e l'orologio del tetto di §4.6 non partirebbe mai: il banco
    #    aspetterebbe venti secondi e scriverebbe «TEMPO_SCADUTO non arriva»
    #    su un server che non ha mai saputo di dover contare.
    #
    # ⭐ Da qui in poi la provocazione E' il silenzio, ed e' partita: il canale
    #    esiste dal lato del server, e il banco non manda piu' niente.
    cli.transmit()
    es.fase = "provocazione"
    es.provocato = True
    await osserva(cli, es, attesa=20)


@caso("sessione-non-servibile", SESSIONE_NON_SERVIBILE, VERSO_SC,
      ("congedo", "chiusura", "dettaglio"),
      "ATTACCA con disposizione `zz`: BEN FORMATA e sconosciuta alla macchina "
      "(§4.5 vuole due guasti diversi).  ⛔ E §8.2 impone il `dettaglio` nel "
      "corpo — che si scrive nel registro e NON si mostra all'utente")
async def _(campo, es):
    cli = await campo.apri()
    await campo.ammesso(cli)
    es.fase = "provocazione"
    cli.manda(attacca(disp="zz"))
    es.provocato = True
    await osserva(cli, es, attesa=12)


@caso("gia-attiva-remota", GIA_ATTIVA_REMOTA, VERSO_SC, ("congedo", "chiusura"),
      "due client dello stesso utente: al SECONDO tocca 0x0F (I2, §8.2). "
      "⛔ E il primo dev'essere arrivato a SESSIONE, o il rosso e il verde "
      "vorrebbero dire la stessa cosa")
async def _(campo, es):
    primo = await campo.apri()
    await campo.sessione(primo)          # ⛔ se questo fallisce, `provocato`
    es.fase = "provocazione"             #    resta falso: non e' una prova
    secondo = await campo.apri()         #    fallita, e' una prova non fatta
    await campo.ammesso(secondo)
    secondo.manda(attacca())
    es.provocato = True
    await osserva(secondo, es, attesa=12)


# ── il verso client→server: chi riceve e' il server, e le strade sono due ───
async def guarda_il_posto(campo, es):
    """⛔ IL POSTO SI GUARDA MENTRE LA CONNESSIONE E' ANCORA VIVA.

    §4.2 e §8.2 `0x0F`: chi si congeda lascia il posto **subito**, perche' la
    sessione e' finita — non «quando il trasporto avra' finito di smontarsi».

    ⚠ E questa e' la differenza che fa la misura.  Se il posto lo si guardasse
      dopo aver chiuso la connessione, lo libererebbe il distruttore della
      connessione e la riga sarebbe verde **anche col congedo ignorato**: e'
      esattamente il difetto che B11 ha trovato il 10 agosto 2026 con Chrome —
      *«un BROWSER chiude la sessione e tiene viva la connessione, e da quel
      momento il posto resta occupato da una sessione che non esiste piu'»*,
      sette `posto NEGATO` su nove.  ⭐ Qui la connessione del caso e' ancora
      aperta, quindi a liberare il posto puo' essere stato solo il congedo.
    """
    libero, perche = await stretta_intera(campo.a)
    es.posto_libero = libero
    if not libero:
        es.errore = (es.errore or "") + f" · il posto NON e' libero: {perche}"



@caso("chiuso-dall-utente-alla-chrome", CHIUSO_DALL_UTENTE, VERSO_CS,
      ("congedo", "chiusura", "posto"),
      "quel che fa Chrome: `CONGEDO(0x01)` sul canale **e** la sessione chiusa "
      "col codice 0x01.  §8.1 impone tutt'e due a chi chiude")
async def _(campo, es):
    cli = await campo.apri()
    await campo.sessione(cli)
    es.fase = "provocazione"
    cli.manda(congedo(CHIUSO_DALL_UTENTE, "il banco B7 chiude, come farebbe "
                                          "l'utente"))
    await asyncio.sleep(0.3)   # ⚠ i due byte non devono partire nello stesso
    cli.chiudi_sessione(CHIUSO_DALL_UTENTE)   # volo: e' la corsa che B11 ha
    es.provocato = True                       # trovato, qui dal lato del client
    await asyncio.sleep(0.5)
    await guarda_il_posto(campo, es)


@caso("chiuso-dall-utente-alla-firefox", CHIUSO_DALL_UTENTE, VERSO_CS,
      ("chiusura", "posto"),
      "⛔ quel che fa Firefox: la sessione si chiude col codice 0x01 e il canale "
      "di controllo viene AZZERATO, senza nessun CONGEDO. §3.1 punto 2 e' "
      "condizionato — «se il canale e' ancora utilizzabile» — e qui non lo e': "
      "⚠ chiamarlo «non si congeda» sarebbe falso, il motivo arriva di la'")
async def _(campo, es):
    cli = await campo.apri()
    await campo.sessione(cli)
    es.fase = "provocazione"
    cli.chiudi_sessione(CHIUSO_DALL_UTENTE)
    # ⚠ E QUI C'E' UN'ATTESA DICHIARATA, con quel che costa.
    #
    #    Firefox spedisce le due cose nello stesso volo, e in quel volo
    #    l'ordine con cui il server le processa decide se il motivo arriva:
    #    l'azzeramento del canale fa liberare la sessione, e una capsula
    #    processata dopo non troverebbe piu' nessuno a cui dirlo.  ⛔ Quella
    #    corsa qui NON si prova — la prova con i motori veri e' di B11 — e
    #    provarla per caso, senza dichiararla, darebbe un rosso che cambia
    #    colore a ogni giro.  ⚠ Resta una `[?]` aperta, ed e' scritta qui
    #    perche' qualcuno la raccolga invece di riscoprirla.
    await asyncio.sleep(0.2)
    cli.azzera_controllo()
    es.provocato = True
    await asyncio.sleep(0.5)
    await guarda_il_posto(campo, es)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⛔ IL CASO CHE ESISTE SOLO CONTRO IL PRODOTTO — `SERVER_IN_CHIUSURA` 0x0C.
#
# *«E `0x0C` e' cambiato di soggetto la notte del 10 agosto, ed e' il primo
# posto in cui i due server divergono in modo visibile: il prodotto un percorso
# di spegnimento adesso ce l'ha — `src/main.c` congeda tutti con
# `SERVER_IN_CHIUSURA` prima di uscire — mentre l'innesto no.»*
# (`fasi/01-filo-nudo.md` B7.)
#
# ⛔ E' l'ottavo motivo provocabile, e senza di lui B7 puntato al prodotto
#    direbbe «sette su sette» **guardando dall'altra parte**.
#
# ---------------------------------------------------------------------------
# ⛔ COME SI PROVOCA, E PERCHE' IL BANCO UCCIDE IL PROPRIO SERVER
#
# `SERVER_IN_CHIUSURA` non si provoca con un byte storto: lo provoca un
# `SIGTERM` al processo.  ⚠ Quindi questo caso **spegne il server**, e da lui in
# poi non c'e' piu' niente da misurare: gira per ultimo, in un'invocazione sua,
# e lo script di lancio riaccende il server apposta prima di chiamarlo.
#
# ⛔ E B0.5 — «dopo ogni prova il server dev'essere ancora li'» — qui NON si
#    applica, e non e' una deroga comoda: e' l'unico caso in cui la morte del
#    server E' la cosa provata.  Lo si dichiara, invece di lasciare che il
#    controllo di B0.5 dia un rosso su un server che ha fatto quel che doveva.
#
# ---------------------------------------------------------------------------
# ⛔ E IL SEGNALE SI MANDA A UN PID VERIFICATO, non a un numero
#
# `/proc/<pid>/comm` dice il nome del programma.  ⚠ Il file del PID puo' essere
# di un'esecuzione precedente, i PID si riusano, e il rootfs di questo server
# vive in RAM: al riavvio i numeri ripartono dal basso e quel numero indica **un
# processo di sistema** (rilievo R8.13, gia' pagato su `01-b2-lancia-wt.sh`).
# ⛔ Se il nome non e' quello atteso, il caso NON manda niente e si dichiara
#    «prova non fatta» — che non e' «prova fallita».
@caso("server-in-chiusura", SERVER_IN_CHIUSURA, VERSO_SC,
      ("congedo", "chiusura"),
      "⭐ SOLO CONTRO IL PRODOTTO: sessione aperta, poi SIGTERM al server. "
      "§8.1 vieta di chiudere con un silenzio, e src/main.c congeda tutti con "
      "0x0C e ASPETTA che i byte escano prima di uscire.  ⛔ Contro l'innesto "
      "questo caso non esiste: aspetterebbe un congedo che nessuna riga puo' "
      "mandare")
async def _(campo, es):
    a = campo.a
    pid = getattr(a, "pid_server", 0)
    if not pid:
        es.fase = ("⛔ nessun --pid-server: non ho nessuno a cui mandare il "
                   "segnale.  Prova NON FATTA, non prova fallita")
        return
    # ⛔ Chi e' quel PID?  Si chiede al nucleo, non si deduce (CODER.md §3.7).
    try:
        with open(f"/proc/{pid}/comm", encoding="utf-8") as fp:
            comm = fp.read().strip()
    except OSError as e:
        es.fase = (f"⛔ /proc/{pid}/comm non si legge ({e.strerror}): il "
                   f"processo non c'e' piu', oppure non e' mio.  Prova NON "
                   f"FATTA — e non mando nessun segnale al buio")
        return
    if comm != "remotix":
        es.fase = (f"⛔ il PID {pid} adesso e' «{comm}», non «remotix»: NON gli "
                   f"mando niente.  I PID si riusano (R8.13), e un SIGTERM a un "
                   f"processo di sistema non e' una misura")
        return

    cli = await campo.apri()
    # ⛔ Si arriva a SESSIONE e non ad AMMESSO: il congedo di §8.1 deve
    #    raggiungere una sessione VIVA, e una stretta di mano a meta' potrebbe
    #    cadere per un tetto di §4.6 mentre aspettiamo.
    await campo.sessione(cli)
    es.fase = "provocazione: SIGTERM al server"
    os.kill(pid, signal.SIGTERM)
    es.provocato = True
    # ⚠ L'attesa e' 12 s e non 3: `main.c` aspetta fino a **due secondi** che i
    #   byte del congedo escano davvero, e `wt_batti` fa maturare la capsula di
    #   §3.1 punto 3 mezzo secondo dopo che la coda si e' svuotata.  Un banco
    #   che smettesse di guardare subito leggerebbe «nessuna chiusura» su un
    #   server che sta ancora parlando.
    await osserva(cli, es, attesa=12)


# ===========================================================================
async def ancora_vivo(a):
    """⛔ B0.5 — dopo ogni caso, il server dev'essere ancora li'.

    Un server ucciso dal nucleo «fa cadere la connessione» esattamente come uno
    che congeda, e si porta via le sessioni di tutti gli altri.  ⚠ Si arriva a
    `ECCOMI` e non a `SESSIONE`: la seconda costerebbe il secondo fisso di
    §4.4-bis a ogni caso, e il posto lo verifica chi ne ha bisogno.
    """
    async with contextlib.AsyncExitStack() as pila:
        campo = Campo(a, pila, None, None)
        try:
            cli = await campo.apri()
            await campo.eccomi(cli)
            return True, ""
        except Exception as e:  # noqa: BLE001
            return False, f"{type(e).__name__}: {e}"


async def stretta_intera(a, disp="it"):
    """La stretta di mano buona, intera, fino a `SESSIONE` — e poi si congeda.

    ⭐ E' tre cose in una: lo **stato iniziale** dichiarato e verificato (B0.1),
       il **controllo che dice si'** (un server che congedasse tutto darebbe
       sette motivi su sette e nessuna sessione), e la prova che **il posto e'
       libero** — senza la quale `gia-attiva-remota` sarebbe verde per la
       ragione sbagliata (B0.2).
    """
    async with contextlib.AsyncExitStack() as pila:
        campo = Campo(a, pila, None, None)
        try:
            cli = await campo.apri()
            _, corpo, _ = await campo.sessione(cli, disp)
            stato = corpo[0]
            lar, alt = struct.unpack("!II", corpo[1:9])
            # ⛔ Ci si congeda come si deve, invece di lasciar cadere la
            #    connessione: cosi' il posto e' libero **subito** per il caso
            #    dopo, e non «quando il trasporto avra' finito di smontarsi».
            cli.manda(congedo(CHIUSO_DALL_UTENTE, "controllo dello stato "
                                                  "iniziale di B7"))
            await asyncio.sleep(0.3)
            cli.chiudi_sessione(CHIUSO_DALL_UTENTE)
            await asyncio.sleep(0.4)
            return True, f"SESSIONE stato={stato} tela={lar}x{alt}"
        except Exception as e:  # noqa: BLE001
            return False, f"{type(e).__name__}: {e}"


async def gira_caso(a, registro, inizio, motivo, verso, f):
    es = Esito(verso)
    async with contextlib.AsyncExitStack() as pila:
        campo = Campo(a, pila, registro, inizio)
        try:
            await f(campo, es)
        except Exception as e:  # noqa: BLE001
            es.errore = f"{type(e).__name__}: {e}"
            # ⛔ E IL MOTIVO NON SI RASCHIA DAL TESTO DELL'ECCEZIONE.
            #    `b3.attendi` solleva `RuntimeError("CONGEDO invece di …:
            #    motivo 0x0b = ERRORE_PROTOCOLLO")` anche quando a cadere e' la
            #    PREPARAZIONE, e quella stringa contiene il nome del motivo
            #    atteso: piu' il server e' rotto a monte, piu' il caso
            #    diventerebbe verde (rilievo R7.1).  Il motivo lo scrive solo
            #    `osserva`, da un messaggio arrivato sul filo.
    # ── §3.1 punto 1, e il verso client→server: dal registro del server ─────
    if inizio is not None:
        if verso == VERSO_SC:
            # ⛔ SENZA IL PREFISSO, e non e' pigrizia — 11 agosto 2026.
            #
            #    Qui c'era `f"REMOTIX B3: congedo motivo=…"`, cioe' il prefisso
            #    dell'INNESTO.  Il prodotto scrive la stessa riga preceduta da
            #    `HH:MM:SS.mmm rcp `, quindi contro di lui questa attesa non
            #    trovava MAI niente: ⛔ §3.1 punto 1 dichiarato assente su OGNI
            #    caso, cioe' un rosso pieno su un server che quella riga la
            #    scrive — misurato oggi, 8 casi su 8.
            #
            # ⚠ E il rilievo era gia' stato scritto (R-A2) e dichiarato curato:
            #   la cura era arrivata al lanciatore e non a questa riga.  E' la
            #   forma «una cura applicata in un posto solo», che questo
            #   progetto paga piu' spesso di ogni altra.
            #
            # ⭐ La cura giusta non e' un secondo prefisso: e' NESSUN prefisso.
            #    `congedo motivo=0xNN` e' quel che i due server hanno in comune,
            #    ed e' esattamente la parte che §3.1 punto 1 pretende — il resto
            #    e' l'intestazione di chi scrive il registro, che non e' del
            #    protocollo.
            trovata, perche = await registro.attendi(
                inizio, f"congedo motivo={motivo:#04x}", entro=6)
            es.riga_registro = (trovata, perche)
        else:
            for chiave, frase in (
                    ("congedo-al-server",
                     f"il client si congeda, motivo={motivo:#04x}"),
                    ("chiusura-al-server",
                     f"la pagina ha chiuso la sessione, motivo {motivo:#04x}")):
                trovata, _ = await registro.attendi(inizio, frase, entro=6)
                es.al_server[chiave] = trovata
    return es


def esigenze(strade, es, motivo, verso):
    """⛔ Il verdetto per strada, e ciascuna con la sua riga.

    Torna [(etichetta, esigibile, arrivata, testo)].  ⚠ `esigibile = False` non
    vuol dire «non si guarda»: si guarda e si stampa, ma non entra nel
    denominatore di quella strada.  E' la differenza fra «Firefox non si
    congeda» e «su Firefox il punto 2 non e' esigibile».
    """
    fuori = []
    if verso == VERSO_SC:
        fuori.append((
            "§3.1 punto 1 — la riga «che cosa» nel registro di chi chiude",
            es.riga_registro is not None,
            bool(es.riga_registro and es.riga_registro[0]),
            "" if not es.riga_registro else (es.riga_registro[1] or "c'e'")))
        fuori.append((
            "§3.1 punto 2 — il motivo nel CONGEDO sul canale",
            "congedo" in strade,
            es.motivo == motivo and es.tipo_motivo == "CONGEDO",
            "assente" if es.motivo is None
            else f"{es.motivo:#04x} in {es.tipo_motivo}"))
        fuori.append((
            "§3.1 punto 3 — il motivo nella chiusura della sessione",
            "chiusura" in strade,
            es.codice_wt == motivo,
            "assente" if es.codice_wt is None else f"{es.codice_wt:#04x}"))
        # ⛔ §11 si conta solo se un motivo E' arrivato: «in quale messaggio»
        #    non e' una domanda che si possa fare a un silenzio, e contarlo
        #    fallito due volte gonfierebbe il rosso della strada 2.
        fuori.append((
            "§11 — il motivo nel messaggio giusto (CONGEDO, non RESPINTO)",
            es.motivo is not None,
            es.tipo_motivo == "CONGEDO",
            f"arrivato in {es.tipo_motivo}" if es.motivo is not None
            else "nessun motivo e' arrivato: la domanda «in quale messaggio» "
                 "non ha oggetto"))
        if "dettaglio" in strade:
            fuori.append((
                "§8.2 — il `dettaglio` nel corpo (per il registro, non per "
                "l'utente)", True, bool(es.dettaglio),
                es.dettaglio or "assente"))
    else:
        fuori.append((
            "§3.1 punto 2 — il motivo nel CONGEDO sul canale",
            "congedo" in strade,
            bool(es.al_server.get("congedo-al-server")),
            "il server l'ha scritto"
            if es.al_server.get("congedo-al-server")
            else ("assente — ed e' atteso: il canale e' azzerato"
                  if "congedo" not in strade else "assente")))
        fuori.append((
            "§3.1 punto 3 — il motivo nella chiusura della sessione",
            "chiusura" in strade,
            bool(es.al_server.get("chiusura-al-server")),
            "il server l'ha scritto"
            if es.al_server.get("chiusura-al-server") else "assente"))
        if "posto" in strade:
            fuori.append((
                "e il posto si libera, osservato SUL FILO", True,
                bool(es.posto_libero), "libero" if es.posto_libero
                else "OCCUPATO: §8.2 0x0F a chi non ha nessuna sessione"))
    return fuori


VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def riga(ok, nome, testo):
    print(f"    {VERDE if ok else ROSSO}{'OK' if ok else 'NO'}{GRIGIO}  "
          f"{nome:34s} {testo}")


def inf(testo):
    print(f"    --  {testo}")


async def principale(a):
    registro = Registro(a.registro)
    # ⛔ I casi e gli esclusi sono quelli DEL BERSAGLIO: contro il prodotto
    #    `server-in-chiusura` c'e' e 0x0C esce dagli esclusi; contro l'innesto
    #    e' l'opposto.  ⭐ Il numero che B7 stampa accanto a un esito e' quello
    #    del bersaglio che si e' acceso, non quello del documento.
    TUTTI = casi_di(a.bersaglio)
    ESCL = esclusi_di(a.bersaglio)
    casi = [c for c in TUTTI if not a.solo or a.solo in c[0]]
    if a.escludi:
        prima = len(casi)
        casi = [c for c in casi if a.escludi not in c[0]]
        a.esclusi_a_mano = prima - len(casi)
    else:
        a.esclusi_a_mano = 0

    # ── --elenco: le previsioni, e il denominatore, senza misurare ──────────
    if a.elenco:
        print(f"== B7 — il congedo dal lato che riceve\n")
        print(f"   ⛔ {len({c[1] for c in TUTTI})} motivi PROVOCABILI su "
              f"{len(MOTIVI)} di §8.2, in {len(TUTTI)} casi.  Ogni riga e' una "
              f"PREVISIONE scritta prima di misurare\n")
        for nome, motivo, verso, strade, spiega, _ in TUTTI:
            print(f"  {nome:34s} {motivo:#04x} {MOTIVI[motivo]}  [{verso}]")
            print(f"  {'':34s}   strade esigibili: {', '.join(strade)}")
            print(f"  {'':34s}   {spiega}")
        print(f"\n   ⛔ E GLI {len(ESCL)} ESCLUSI, col perche' — senza "
              f"questo elenco «7 su 7» sarebbe vero per costruzione:\n")
        for c, perche in ESCL:
            print(f"  {MOTIVI[c]:26s} {c:#04x}  {perche}")
        ok, testo = certifica_denominatore(TUTTI, ESCL)
        print(f"\n   {'⭐' if ok else '⛔'} {testo}")
        return 0 if ok else 3

    # ⛔ IL REGISTRO DEL GIRO — e la prima riga dice contro che cosa si misura.
    #    Fino all'11 agosto 2026 B7 non ne aveva nessuno.
    a.reg = b0.Registro(a.uscita, a.bersaglio, a.porta, a.giro or None,
                        a.md5 or None)
    a.reg.apri_giro(
        "B7", "un caso per motivo, ciascuno su una connessione nuova; il "
              "congedo si legge SUL FILO dal lato che riceve, mai dal registro "
              "di chi lo manda",
        extra={"casi": len(casi), "casi_del_bersaglio": len(TUTTI),
               "provocabili": len({c[1] for c in TUTTI}),
               "esclusi": len(ESCL), "filtro": a.solo,
               # ⛔ IL NUMERO CHE CAMBIA COL BERSAGLIO, scritto PRIMA di
               #    misurare: sette contro l'innesto, otto contro il prodotto.
               "attesi_provocabili": b0.profilo(a.bersaglio)["motivi_provocabili"],
               "pid_server": getattr(a, "pid_server", 0)})
    print("== B7 — il congedo, verificato DAL LATO CHE RICEVE (§8.1)")
    print(f"   ⛔ BERSAGLIO: {a.bersaglio} · porta {a.porta} · binario md5 "
          f"{(a.md5 or 'ignota')[:12]}…")
    atteso_prov = b0.profilo(a.bersaglio)["motivi_provocabili"]
    visti_prov = len({c[1] for c in TUTTI})
    if visti_prov != atteso_prov:
        print(f"   {ROSSO}⛔ i provocabili di questo bersaglio dovrebbero essere "
              f"{atteso_prov} e i casi ne coprono {visti_prov}{GRIGIO}")
        print(f"      ⛔ Non e' un rosso del server: e' il banco che non sa "
              f"contare quel che sta per misurare.")
        return 3
    print(f"   ⛔ {visti_prov} motivi provocabili su {len(MOTIVI)} di §8.2 — e "
          f"il numero e' del BERSAGLIO, non del documento")
    print("   ⛔ per ogni motivo: il CONGEDO sul canale **e** il codice nella "
          "chiusura")
    print("      della sessione — due strade, due contatori, una `&&`\n")

    # ═══ LA CERTIFICAZIONE, PRIMA DI MISURARE ═══════════════════════════════
    print("== ⭐ Il banco si certifica prima di puntarsi sull'incognita "
          "(CODER.md §3.3)")
    guasti_cert = 0
    ok, testo = certifica_denominatore(TUTTI, ESCL)
    riga(ok, "il denominatore torna", testo)
    guasti_cert += 0 if ok else 1
    for nome, ok, testo in certifica_lettori():
        riga(ok, nome, testo)
        guasti_cert += 0 if ok else 1
    for nome, ok, testo in certifica_frasi():
        riga(ok, nome, testo)
        guasti_cert += 0 if ok else 1
    if a.registro:
        ok, perche = registro.leggibile()
        riga(ok, "il registro del server si legge", perche or a.registro)
        guasti_cert += 0 if ok else 1
    else:
        inf("⚠ nessun --registro: §3.1 punto 1 e il verso client→server NON si")
        inf("  misurano, e il giro sara' dichiarato PARZIALE")

    print("\n== ⭐ Lo stato iniziale, dichiarato e verificato (B0.1, B0.2)")
    inf("una stretta di mano intera: se il posto fosse gia' occupato dal giro")
    inf("prima, `gia-attiva-remota` sarebbe verde per la ragione sbagliata")
    marca = registro.finestra() if a.registro else None
    ok, testo = await stretta_intera(a)
    riga(ok, "stretta-di-mano-intera", testo)
    guasti_cert += 0 if ok else 1
    if a.registro and ok:
        # ⭐ Il controllo positivo del LETTORE del registro, sulla riga che
        #    dev'esserci di sicuro — e quello negativo su una che non c'e'.
        trovata, perche = await registro.attendi(
            marca, f"ammesso utente={a.utente}", entro=6)
        riga(trovata, "⭐ il lettore del registro trova",
             f"«ammesso utente={a.utente}»" if trovata else perche)
        guasti_cert += 0 if trovata else 1
        testo_finestra = registro.da(marca) or ""
        finta = "congedo motivo=0xff" not in testo_finestra
        riga(finta, "⛔ e non trova quel che non c'e'",
             "«congedo motivo=0xff» non c'e', come deve")
        guasti_cert += 0 if finta else 1

    if guasti_cert:
        print(f"\n    {ROSSO}⛔ B7 NON MISURA: lo strumento non e' certificato "
              f"({guasti_cert} controlli falliti){GRIGIO}")
        print("       Un esito negativo con lo strumento non certificato e'")
        print("       ambiguo fra «non funziona il server» e «non funzionava")
        print("       il banco» — e questo NON e' un rosso del server.")
        return 3

    # ⛔ SENZA IL REGISTRO, I CASI client→server NON SI GIRANO.
    #
    #    Li' chi riceve e' il server, e il suo registro e' l'unico testimone:
    #    girarli senza saper leggere quel file darebbe due rossi per una
    #    mancanza del BANCO, e sarebbero rossi indistinguibili da un server che
    #    ignora i congedi.  ⚠ Meglio una misura in meno, dichiarata, che una
    #    misura che accusa l'imputato sbagliato.
    if not a.registro:
        prima = len(casi)
        casi = [c for c in casi if c[2] != VERSO_CS]
        if prima != len(casi):
            print(f"    {GIALLO}⚠{GRIGIO} senza --registro i {prima - len(casi)}"
                  f" casi client→server NON si girano: manca il testimone")

    # ═══ I CASI  ════════════════════════════════════════════════════════════
    if not casi:
        print(f"\n    {ROSSO}⛔ «--solo {a.solo}» ha selezionato ZERO casi su "
              f"{len(TUTTI)}: non c'e' niente da misurare{GRIGIO}")
        print("       Questo NON e' un verde.  I nomi si leggono con --elenco.")
        return 2

    print(f"\n== I casi: {len(casi)} su {len(TUTTI)}, "
          f"{len({c[1] for c in casi})} motivi su "
          f"{len({c[1] for c in TUTTI})} provocabili")
    if a.solo:
        print(f"    {GIALLO}⚠ GIRO PARZIALE{GRIGIO}: l'esito verde si legge «i "
              f"casi selezionati passano», mai «B7 passa»")
    if a.esclusi_a_mano:
        print(f"    {GIALLO}⚠{GRIGIO} {a.esclusi_a_mano} casi tolti da "
              f"«--escludi {a.escludi}»: il giro e' PARZIALE, e l'esito verde "
              f"non li copre")

    conti = {
        "§3.1 punto 1 — la riga «che cosa» nel registro di chi chiude": [0, 0],
        "§3.1 punto 2 — il motivo nel CONGEDO sul canale": [0, 0],
        "§3.1 punto 3 — il motivo nella chiusura della sessione": [0, 0],
        "§11 — il motivo nel messaggio giusto (CONGEDO, non RESPINTO)": [0, 0],
        "§8.2 — il `dettaglio` nel corpo (per il registro, non per l'utente)": [0, 0],
        "e il posto si libera, osservato SUL FILO": [0, 0],
        "⛔ il server e' ancora li' dopo il caso (B0.5)": [0, 0],
        "§8.2 — una frase distinta e mostrabile, mai un numero": [0, 0],
    }
    guasti, morto = 0, False
    # ⛔ Un motivo vale «provato» solo se TUTTI i suoi casi passano.
    #    `CHIUSO_DALL_UTENTE` ne ha due — alla Chrome e alla Firefox — e
    #    contarlo pieno perche' uno dei due e' andato bene sarebbe scambiare
    #    «un motore su due» per «il motivo e' coperto».
    motivi_visti, motivi_rotti = set(), set()

    for nome, motivo, verso, strade, spiega, f in casi:
        inizio = registro.finestra() if a.registro else None
        es = await gira_caso(a, registro, inizio, motivo, verso, f)
        motivi_visti.add(motivo)
        # ⚠ Il posto lo guarda il CASO, con la sua connessione ancora aperta
        #   (vedi `guarda_il_posto`): guardarlo di qui, a connessione chiusa,
        #   lo troverebbe libero anche col congedo ignorato.
        prove = esigenze(strade, es, motivo, verso)
        buono = es.provocato and es.errore is None
        for etichetta, esigibile, arrivata, testo in prove:
            if not esigibile:
                continue
            # ⚠ `setdefault`: un'etichetta nuova si aggiunge al riepilogo col
            #   suo denominatore invece di far cadere il banco — e cosi' chi
            #   aggiunge una strada non deve ricordarsi di due posti.
            conto = conti.setdefault(etichetta, [0, 0])
            conto[1] += 1
            conto[0] += int(arrivata)
            buono = buono and arrivata
        riga(buono, nome, str(es))
        if not buono:
            motivi_rotti.add(motivo)
            guasti += 1
            print(f"        atteso: {motivo:#04x} {MOTIVI[motivo]}  "
                  f"[{verso}]  strade esigibili: {', '.join(strade)}")
            print(f"        {spiega}")
            if not es.provocato:
                print(f"        ⛔ e la provocazione NON E' MAI PARTITA (fermo "
                      f"in «{es.fase}»): non e' una prova fallita, e' una "
                      f"prova non fatta")
            for etichetta, esigibile, arrivata, testo in prove:
                if esigibile and not arrivata:
                    print(f"        {ROSSO}⛔{GRIGIO} {etichetta}: {testo}")
            if a.registro and inizio is not None:
                print("        il registro del server, in quella finestra:")
                for r in registro.righe_nostre(inizio):
                    print(f"          {r[:150]}")
        # ⚠ Le strade non esigibili si STAMPANO lo stesso: e' la riga che
        #   impedisce di leggere «assente» come «rotto».
        for etichetta, esigibile, arrivata, testo in prove:
            if not esigibile:
                print(f"        {GIALLO}~{GRIGIO} {etichetta}: {testo} "
                      f"(non esigibile in questo caso, e non entra nel conto)")
        if es.dettaglio:
            print(f"        dettaglio dal corpo: «{es.dettaglio}»  "
                  f"⚠ va nel registro, NON all'utente (§8.2)")

        # ⛔ E il fatto va nel registro PRIMA di ogni conclusione: un caso che
        #    fa cadere il banco deve aver lasciato la propria riga, o il
        #    registro racconterebbe solo i giri andati bene.
        a.reg.scrivi({"tipo": "caso", "nome": nome, "esito": bool(buono),
                      "motivo_atteso": motivo, "verso": verso,
                      "strade_esigibili": list(strade),
                      "motivo_visto": es.motivo, "tipo_motivo": es.tipo_motivo,
                      "codice_wt": es.codice_wt, "provocato": es.provocato,
                      "fase": es.fase, "errore": es.errore,
                      "dettaglio": es.dettaglio,
                      "prove": [[e_, bool(x_), bool(y_)]
                                for e_, x_, y_, _ in prove]})

        # ⛔ B0.5 — «dopo ogni prova il server dev'essere ancora li'» — E IL
        #    CASO CHE FA ECCEZIONE, dichiarato invece che dimenticato.
        #
        #    `server-in-chiusura` **spegne il server apposta**: e' l'unico caso
        #    in cui la morte del server E' la cosa provata.  ⚠ Girare B0.5 qui
        #    darebbe un rosso su un server che ha fatto esattamente quel che
        #    §8.1 gli chiede, e sarebbe il rosso sull'imputato sbagliato dentro
        #    il banco che quella lezione cita.
        if motivo == SERVER_IN_CHIUSURA:
            inf("⚠ B0.5 NON si applica a questo caso: il server l'ho spento io,")
            inf("  ed e' la cosa provata.  Il conto non lo tocca, e questa riga")
            inf("  esiste perche' «saltato» e «passato» non abbiano la stessa")
            inf("  faccia")
            a.reg.scrivi({"tipo": "b0.5-saltato", "nome": nome,
                          "perche": "il caso spegne il server apposta"})
            morto = True
            break
        conto = conti["⛔ il server e' ancora li' dopo il caso (B0.5)"]
        conto[1] += 1
        vivo, perche = await ancora_vivo(a)
        conto[0] += int(vivo)
        if not vivo:
            riga(False, "", f"⛔ IL SERVER NON RISPONDE PIU' dopo «{nome}»: "
                            f"{perche}")
            guasti += 1
            morto = True
            break

    # ═══ LE FRASI (§8.2) ═══════════════════════════════════════════════════
    #
    # ⚠ Questa sezione e la prossima NON dipendono dai casi selezionati e non
    #   toccano il server: girano anche sotto filtro, e si dice.  (In B5 le
    #   sezioni indipendenti si saltano perche' li' dipendevano davvero dai
    #   casi — qui non e' cosi', e saltarle nasconderebbe una misura gratis.)
    if not morto:
        print(f"\n== ⭐ Le frasi di §8.2 — «BUDGET_PIENO non e' \"errore 6\"»")
        inf(f"si legge la TABELLA del client, non lo schermo: che la frase")
        inf(f"arrivi sotto gli occhi dell'utente e' giudizio suo (I8)")
        try:
            with open(a.pagina, encoding="utf-8", errors="replace") as fp:
                testo = fp.read()
            voci, perche = leggi_tabella(testo)
        except OSError as e:
            voci, perche = None, f"{a.pagina} non si legge: {e}"
        if voci is None:
            riga(False, "la tabella si legge", f"⛔ {perche}")
            inf("⛔ e questo NON e' «zero frasi»: e' «la tabella non si e'")
            inf("   letta».  Il conto qui sotto resta senza denominatore")
            guasti += 1
        else:
            esiti = giudica_frasi(voci)
            conti["§8.2 — una frase distinta e mostrabile, mai un numero"][1] = \
                len(esiti)
            for c, ok, testo in esiti:
                conti["§8.2 — una frase distinta e mostrabile, mai un "
                      "numero"][0] += int(ok)
                if not ok:
                    riga(False, MOTIVI[c], testo)
                    guasti += 1
                elif a.frasi:
                    riga(True, MOTIVI[c], f"«{testo}»")
            if all(ok for _, ok, _ in esiti):
                riga(True, "le 15 frasi", f"distinte, senza numeri, dal file "
                                          f"{os.path.basename(a.pagina)}")
                inf("(--frasi le stampa tutte)")

        # ═══ L'ESCLUSIONE MISURATA — E IL SEGNO SI INVERTE COL BERSAGLIO ═══
        #
        # ⛔ Contro l'INNESTO il grep deve dire **zero**: il motivo e' escluso, e
        #    l'esclusione e' misurata invece che asserita.
        # ⭐ Contro il PRODOTTO deve dire **piu' di zero**: il percorso esiste,
        #    ed e' l'ottavo motivo provocabile.  ⚠ Uno zero qui vorrebbe dire
        #    che sto misurando un binario **di prima** di quella notte, e il
        #    caso `server-in-chiusura` sarebbe rosso per la ragione sbagliata.
        atteso_positivo = b0.profilo(a.bersaglio)["spegnimento"]
        sorgenti = b0.sorgenti_spegnimento(a.bersaglio, a.dentro)
        print(f"\n== ⛔ L'esclusione che si MISURA: SERVER_IN_CHIUSURA (0x0C)")
        inf(f"si guarda DOVE LA COSA SUCCEDE, e su «{a.bersaglio}» sono "
            f"{len(sorgenti)} file — ⛔ non `rcp.c` da solo, che e' identico "
            f"nei due server e non sa che esista un processo")
        quanti, testo = esclusione_misurata(sorgenti)
        if quanti is None:
            riga(False, "i sorgenti si leggono", testo)
            guasti += 1
        elif atteso_positivo:
            riga(quanti > 0, "⭐ SERVER_IN_CHIUSURA E' producibile", testo)
            if quanti > 0:
                inf("⭐ e infatti i provocabili qui sono OTTO, non sette: e' la "
                    "prima")
                inf("  differenza visibile fra i due server (fasi/01-filo-nudo.md B7)")
            else:
                inf("⛔ ZERO occorrenze su un bersaglio che dovrebbe averle: o")
                inf("  sto misurando un binario di PRIMA della notte del 10")
                inf("  agosto, o i sorgenti non sono quelli da cui e' stato")
                inf("  costruito.  ⚠ Non e' «il prodotto non congeda»: e' che")
                inf("  non sto guardando il prodotto che credo")
                guasti += 1
        else:
            riga(quanti == 0, "SERVER_IN_CHIUSURA non e' producibile", testo)
            if quanti == 0:
                inf("⚠ e `fasi/01-filo-nudo.md` B7 lo elencava fra «gli otto")
                inf("  motivi che questa fase sa produrre»: contro l'innesto")
                inf("  sono sette")
            else:
                inf("⭐ il percorso adesso esiste anche nell'innesto: va tolto")
                inf("  dagli esclusi e gli si scrive un caso, o B7 conta un")
                inf("  motivo in meno del vero")
                guasti += 1

    # ═══ IL RIEPILOGO ══════════════════════════════════════════════════════
    print("\n    == quel che questo giro ha davvero guardato")
    for che, (buoni, tot) in conti.items():
        if tot == 0:
            # ⛔ Un denominatore a zero si DICHIARA: «nessuno ha guardato» e
            #    «tutti passati» hanno lo stesso aspetto se si tace.
            print(f"    --  {che:62s} nessun caso lo ha sollecitato")
            continue
        col = VERDE if buoni == tot else ROSSO
        print(f"    {col}{buoni:3d} su {tot:3d}{GRIGIO}  {che}")

    motivi_pieni = motivi_visti - motivi_rotti
    print()
    print(f"    ⛔ i motivi: {len(motivi_pieni)} su {len(motivi_visti)} "
          f"provati in questo giro, e i PROVOCABILI dalla fase 1 sono "
          f"{len({c[1] for c in TUTTI})} su {len(MOTIVI)} di §8.2")
    print(f"       gli altri {len(ESCL)} sono esclusi, ciascuno col suo "
          f"perche' (--elenco), e l'esclusione di")
    print(f"       SERVER_IN_CHIUSURA e' misurata, non asserita")

    if morto and any(c[1] == SERVER_IN_CHIUSURA for c in casi):
        # ⭐ Il server e' morto perche' gliel'ho chiesto io: e' il caso
        #    `server-in-chiusura`, e le sezioni che seguono (le frasi,
        #    l'esclusione misurata) non toccano il server — girano lo stesso.
        print(f"\n    ⚠ il server e' spento perche' questo giro lo ha spento "
              f"apposta: il giro e' PARZIALE per costruzione")
        a.reg.scrivi({"tipo": "verdetto", "guasti": guasti, "parziale": True,
                      "perche": "giro dello spegnimento"})
        print(f"    --  {a.reg.riassunto()}")
        return 1 if guasti else 0
    if morto:
        print(f"\n    {ROSSO}⛔ il banco si e' fermato: senza un server non "
              f"c'e' niente da misurare{GRIGIO}")
        a.reg.scrivi({"tipo": "verdetto", "guasti": guasti, "parziale": True,
                      "perche": "il server e' morto senza che glielo chiedessi"})
        return 1
    a.reg.scrivi({"tipo": "verdetto", "guasti": guasti,
                  "parziale": bool(a.solo or not a.registro
                                   or a.esclusi_a_mano),
                  "motivi_pieni": sorted(motivi_pieni),
                  "provocabili": len({c[1] for c in TUTTI}),
                  "conti": {k: v for k, v in conti.items()}})
    print(f"\n    --  {a.reg.riassunto()}")
    if guasti:
        print(f"\n    {ROSSO}⛔ B7: {guasti} punti non passano contro "
              f"«{a.bersaglio}»{GRIGIO}")
        return 1
    if a.solo or not a.registro or a.esclusi_a_mano:
        print(f"\n    {VERDE}⭐ i punti misurati passano contro "
              f"«{a.bersaglio}»{GRIGIO} — ⚠ e questo NON e' «B7 passa»: il giro "
              f"era parziale")
        return 0
    print(f"\n    {VERDE}⭐ B7 passa: {len(motivi_pieni)} su "
          f"{len({c[1] for c in TUTTI})} motivi provocabili, per TUTT'E DUE le "
          f"strade di §3.1,{GRIGIO}")
    print(f"    {VERDE}      e 15 frasi distinte su 15 — e i numeri qui sopra "
          f"dicono su che cosa{GRIGIO}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="B7 — il congedo, verificato dal lato che riceve")
    p.add_argument("--indirizzo", default="192.168.0.2")
    # ⛔ Nessun predefinito che nomini un bersaglio: 7447 e' l'innesto e 7448 il
    #    prodotto, e un predefinito qui vorrebbe dire che «--bersaglio prodotto»
    #    senza «--porta» misura l'innesto dichiarando il prodotto.
    p.add_argument("--porta", type=int, required=True)
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola", default="parola-di-prova")
    p.add_argument("--dentro", default=QUI,
                   help="la radice dei sorgenti da cui si misura l'esclusione "
                        "di SERVER_IN_CHIUSURA (dipende dal bersaglio)")
    # ⛔ Il PID del server, per il solo caso `server-in-chiusura`.  Zero vuol
    #    dire «non me l'hanno detto», e quel caso si dichiara NON FATTO invece
    #    di mandare un segnale al buio.
    p.add_argument("--pid-server", type=int, default=0,
                   help="il PID del server, per provocare SERVER_IN_CHIUSURA")
    p.add_argument("--registro", default="",
                   help="il registro del server: serve a §3.1 punto 1 e al "
                        "verso client→server")
    p.add_argument("--pagina", default=os.path.join(QUI, "01-b11-pagina.html"),
                   help="il file dove vive la tabella delle frasi di §8.2")
    p.add_argument("--solo", default="",
                   help="gira solo i casi che contengono questo")
    # ⛔ `--escludi` e non «--solo tutto tranne»: `server-in-chiusura` SPEGNE il
    #    server, quindi il giro normale lo lascia fuori e lo script di lancio lo
    #    chiama dopo, con il server riacceso apposta.  ⚠ Un filtro che togliesse
    #    un caso in silenzio renderebbe «N su N» vero per costruzione: qui il
    #    caso tolto si stampa, e il denominatore resta quello del bersaglio.
    p.add_argument("--escludi", default="",
                   help="NON gira i casi che contengono questo, e lo dichiara")
    p.add_argument("--frasi", action="store_true",
                   help="stampa tutte e quindici le frasi di §8.2")
    p.add_argument("--elenco", action="store_true",
                   help="stampa le previsioni e il denominatore, senza misurare")
    b0.aggiungi_argomenti(p)
    # ⚠ `--elenco` non misura e non ha bisogno di una porta.
    if "--elenco" in sys.argv:
        for _az in p._actions:
            if _az.dest == "porta":
                _az.required = False
    sys.exit(asyncio.run(principale(p.parse_args())))
