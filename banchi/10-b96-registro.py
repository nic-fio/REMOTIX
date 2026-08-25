#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-b96-registro — ⛔ QUANTO DEL REGISTRO SI PUO' ATTRIBUIRE quando gli inquilini
                  sono piu' di uno.  E il metro **si tara prima**.

    porta 8150 · utenti `provadec4` (1103), `provadec5` (1104), `provadec6`
    (1105) e `provamt1` (1110, ⭐ CONDIVISO — vedi `10-b96-terreno.sh`)
    albero `/media/REMOTIX/src/10b5-src` · lavoro `/media/REMOTIX/tmp/10b5`
    unita' `remotix-8150` · terreno: `banchi/10-b96-terreno.sh`

═══════════════════════════════════════════════════════════════════════════════
⭐⭐ CHE COSA MISURA, E PERCHE' NON E' IL CENSIMENTO CHE C'E' GIA'
═══════════════════════════════════════════════════════════════════════════════

Il rilievo **R10-A4** (`fasi/10-multi-tenant-e-il-budget.md` §4.2) porta gia' un
numero: **79 %** delle righe di `rcp.c`, **63 %** di `webtransport.c`, **64 %**
di `figlio.c` e ⛔ **100 %** di `codificatore.c` **senza identificatore**.  ⚠ Ma
e' un **conteggio sul sorgente**: conta le *chiamate scritte*, non le *righe
uscite*.  Le due cose non si somigliano affatto —

  · una chiamata dentro un `if` di guasto puo' non uscire mai;
  · una chiamata dentro il ciclo dei fotogrammi esce **una volta al secondo per
    ogni sessione viva**, e a quattro sessioni pesa quattro volte;
  · e ⛔ il conteggio statico non sa niente della domanda che conta davvero:
    *«con quattro inquilini insieme, di quante righe posso dire DI CHI SONO?»*

⇒ Questo banco fa girare **quattro sessioni grafiche vere di quattro utenti
  diversi**, che fanno **cose diverse**, per un tempo **dichiarato**, e misura la
  frazione **sulle righe che escono davvero**.

═══════════════════════════════════════════════════════════════════════════════
⛔ PRIMA IL METRO, E SI TARA — `LEZIONI.md` §1.33
═══════════════════════════════════════════════════════════════════════════════

Il metro, qui, e' un **classificatore**: preso il registro e una riga, dice di
quale sessione e', oppure `None`.  ⛔ Un classificatore non tarato produce una
percentuale, non una misura.  ⇒ Prima di credergli si **inietta provenienza
nota** e si guarda se la ritrova, e ⭐ **si misurano TUTT'E DUE gli errori**:

  | | |
  |---|---|
  | **sbagliate** | ha detto `provadec5` di una riga di `provadec4`.  ⛔ E' l'errore **peggiore**: manda a guardare il desktop sbagliato |
  | **astenute**  | ha detto `None`.  ⚠ E' un errore **onesto**: chi legge sa di non sapere |

⭐ **Un classificatore che indovina e' peggio di uno che si astiene**, e per
   dimostrarlo non basta dirlo: qui girano **tre** classificatori, e due sono
   fatti apposta per **indovinare**.

  1. **`prudente`** — solo identificatori **ancorati**: il nome utente come
     parola intera, la `provenienza` (`[ind]:porta`) passata per il ponte
     «posto PRESO da %s via %s» (`rcp.c`), l'`uid`, il `pid` del figlio.
     ⛔ Se i candidati sono due e discordi, dice `None`.
     ⭐ E costruisce le sue mappe **dal registro e basta**: e' la condizione di
     chi diagnostica, che il registro ce l'ha e la macchina no.
  2. **`vicinanza`** — il prudente, piu' ⛔ **l'euristica che usa un essere
     umano**: se la riga e' muta, e' di chi ha parlato **poco prima**.
  3. **`continuita`** — il prudente, piu' il fatto che le righe `ciclo:` di
     `figlio.c` portano **contatori cumulativi**: quattro figli fanno quattro
     serie crescenti, e si prova a separarle per continuita'.

⛔ La taratura viva si fa con le **finestre A UNA VOCE**, e la verita' arriva da
   **fuori dal registro**: si mette in `SIGSTOP` ogni figlio tranne uno, e per
   quei secondi ogni riga che **non** sa scrivere il padre e' di quell'uno, per
   costruzione.  ⭐ E la finestra con **tutti** i figli fermi dice, misurandolo
   invece di supporlo, **quali famiglie di righe le scrive il PADRE**.

═══════════════════════════════════════════════════════════════════════════════
⭐ LA FRAZIONE CHE CONTA DI PIU' — non tutte le righe sono uguali
═══════════════════════════════════════════════════════════════════════════════

Le righe d'avvio si attribuiscono da se': dicono «figlio generato per «X»» e il
nome ce l'hanno dentro.  ⛔ Quelle che servono a **diagnosticare** sono quelle
**di regime** — i tratti, le code, le discese del ritmo, i fotogrammi buttati —
e si misurano **a parte** (`FAMIGLIE_DIAGNOSI`).

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ E LA PROVA CHE VALE PIU' DEL CONTEGGIO: LA DIAGNOSI CIECA
═══════════════════════════════════════════════════════════════════════════════

Si spegne la scena di **una** delle quattro (a turno, tutte e quattro), e si
chiede al banco: ⭐ *«leggendo SOLO il registro, quale sessione ha smesso di
consegnare fotogrammi?»*  Il conto e' due:

  · **si vede che QUALCUNO si e' rotto?**  (⚠ e' facile: una serie di contatori
    si ferma)
  · **si sa DI CHI e'?**  ⛔ Se no, quello e' il risultato, e vale piu' di
    qualunque percentuale.

═══════════════════════════════════════════════════════════════════════════════
⚠ E L'ALTRA META' DEL DIFETTO — le righe che si INTRECCIANO
═══════════════════════════════════════════════════════════════════════════════

`registro.c:63` dichiara che l'atomicita' vale **sotto `PIPE_BUF` (4096 byte)**,
e le righe lunghe di questo prodotto ci arrivano vicino.  ⛔ Con quattro figli
che appendono allo **stesso** file, due righe lunghe possono intrecciarsi — e il
risultato e' una riga **plausibile e falsa**, che e' la cosa peggiore che possa
capitare a uno strumento di diagnosi.

⇒ Il rivelatore cerca **tre** forme, e ⛔ **si tara innestandole**:
  · **orfana** — la riga non comincia con `HH:MM:SS.mmm area`;
  · **innestata** — dentro il corpo ricompare una marca temporale;
  · **troncata** — finisce col `...` che `registro.c` mette apposta quando la
    riga supera il buffer (⭐ e' la cura dichiarata: *«una riga tagliata si
    vede, una riga intrecciata no»*).

═══════════════════════════════════════════════════════════════════════════════
⛔ CHE COSA QUESTO BANCO **NON** SA DIRE — si dichiara in testa
═══════════════════════════════════════════════════════════════════════════════

 1. ⛔ **Non prova che l'intreccio sia IMPOSSIBILE.**  Il registro sta su un
    file **ext4** aperto in append: Linux serializza le `write()` sul lucchetto
    dell'inode, e con **una sola** `write` per riga (la cura del 21 agosto 2026,
    riquadro di `registro.c`) l'intreccio potrebbe non capitare mai su questa
    macchina.  ⇒ Se il conteggio esce **zero**, questo banco dice *«zero su N
    righe, su ext4, con quattro figli»* — non *«non puo' succedere»*.  ⚠ Su un
    altro filesystem (NFS, o un `tee`, o un pipe) la conclusione cadrebbe.
 2. ⛔ **Non misura il costo della cura sul prodotto**: non tocca `src/`.  Il
    costo lo **calcola** dalle righe vere (byte per riga e righe al secondo) e
    lo dichiara come **previsione**, marcata `[?]` dove e' aritmetica e `[M]`
    dove e' misura.
 3. ⚠ **Le quattro sessioni girano sulla stessa macchina del server.**  Il
    registro non ne risente (e' scrittura su file), ma il **ritmo** delle righe
    di regime si' — e il ritmo entra nel costo della cura.  ⇒ Il costo si
    riferisce **anche per sessione**, che e' la grandezza che non dipende da
    quante ne stanno insieme.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ IL MODO `--certifica`
═══════════════════════════════════════════════════════════════════════════════

Un banco non e' finito finche' non lo si e' visto dare **ROSSO**
(`LEZIONI.md` §1.29).  I guasti innestati sono i cinque dell'incarico, piu'
quelli che servono a provare il rivelatore degli intrecci — e ⛔ **girano**, non
sono immaginati.  Ogni caso e' `sano → guasto → risanato`.

Uso:
    python3 banchi/10-b96-registro.py --certifica          # ⛔ non tocca la macchina
    python3 banchi/10-b96-registro.py --durata 120         # il giro vero
    python3 banchi/10-b96-registro.py --senza-lucchetto    # ⚠ i numeri NON valgono
"""
import argparse
import base64
import gzip
import importlib.util
import io
import json
import os
import random
import re
import statistics
import sys
import time

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ L'ISOLAMENTO, SCRITTO PRIMA DI QUALUNQUE IMPORT CHE LO LEGGA
# ═══════════════════════════════════════════════════════════════════════════
QUI = os.path.dirname(os.path.abspath(__file__))
PORTA = int(os.environ.get("PORTA", "8150"))
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/10b5")
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/10b5-src")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/10b5-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/10b5")
UNITA = os.environ.get("UNITA", "remotix-%d" % PORTA)
IO_SONO = os.environ.get("IO_SONO", "10-b5")
LUCCHETTO = os.environ.get("LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-gpu.d")
FUORI = os.environ.get("FUORI", "/tmp/10-b96")
REGISTRO = LAV + "/registro.log"

# ⭐ I QUATTRO, e ciascuno fa una cosa DIVERSA: l'incarico lo chiede, e serve
#    anche al banco — quattro scene uguali darebbero quattro serie di contatori
#    che si somigliano, e il classificatore `continuita` sembrerebbe migliore di
#    quel che e' per un caso fortunato.
#    ⛔ `provamt1` e' CONDIVISO: vale il protocollo del preambolo del giro 2
#       (lucchetto prima, palchi orfani verificati, `sgombra` alla fine).
SESSIONI = [
    ("provadec4", 1103, "pieno", "pieno"),
    ("provadec5", 1104, "barra", "preciso"),
    ("provadec6", 1105, "pieno", "preciso"),
    ("provamt1", 1110, "marca", "preciso"),
]
QUANTI = len(SESSIONI)
SCENA_BIN = os.environ.get(
    "SCENA_BIN", "/media/REMOTIX/src/04-b30-scena-lav/04-b30-scena")

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LE SOGLIE, IN UN POSTO SOLO, CIASCUNA CON LA SUA RAGIONE
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `LEZIONI.md` §1.33: una soglia si tara sui DUE ESTREMI NOTI.  ⚠ Qui nessuna
#    soglia stacca nessuno: decidono il colore di una riga di rapporto.
#
# ⛔⛔ `ASSESTAMENTO_S` E' LA SOGLIA CHE FALSEREBBE TUTTO IN MEGLIO.
#     `CODER.md` §3.5: il campione si prende **a regime**.  Le righe d'avvio si
#     attribuiscono da se' — «figlio generato per «X»», «sessione aperta
#     utente=X» — e un campione preso li' direbbe una frazione buonissima di un
#     registro che, quando serve, non dice niente.  ⇒ La finestra comincia
#     `ASSESTAMENTO_S` dopo l'ultima apertura, e il banco **si rifiuta** di
#     giudicare una finestra che tocchi l'avvio (`p_a_regime`).
ASSESTAMENTO_S = 25.0
# ⛔ Sotto questo numero di righe la finestra non ha misurato niente: `None`,
#    non «0 %» (`LEZIONI.md` §1.9 · regola 5 del preambolo).  ⚠ A quattro
#    sessioni vive il registro fa `[M]` ~15-25 righe/s: 60 righe sono ~3 s.
RIGHE_MINIME = 60
# ⛔ E OGNI sessione deve aver parlato: una sessione che non ha prodotto righe
#    NON e' «tutte le sue attribuite» — e' una sessione che non c'era.
RIGHE_MINIME_PER_SESSIONE = 3
# ⚠ La finestra dell'euristica «di chi ha parlato poco prima».  Non e' una
#   scelta di comodo: `[M]` a quattro sessioni le righe di regime escono a
#   raffiche di poche decine di ms, e un secondo e' molto piu' largo del passo.
#   ⇒ Se sbaglia con UN SECONDO di finestra, sbaglierebbe anche stretta.
VICINANZA_MS = 1000
# ⛔ `PIPE_BUF`: il confine che `registro.c:63` dichiara.
PIPE_BUF = 4096
# ⚠ «vicine al confine»: sopra questa lunghezza una riga e' nella zona in cui
#   l'atomicita' non e' piu' garantita da `registro.c`.
LUNGA = 2048


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LE FAMIGLIE DI RIGHE — e la distinzione che l'incarico chiede
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Una «famiglia» e' il modello di riga, non la riga: `ciclo: 13 fotogrammi…`
#    e `ciclo: 14 fotogrammi…` sono la stessa famiglia.  Serve a due cose:
#      1. a dire QUALI famiglie le scrive il padre (finestra a tutti fermi);
#      2. a riferire la frazione per famiglia invece che in un numero solo.
#
# ⭐ E `FAMIGLIE_DIAGNOSI` e' l'insieme che conta: quel che si legge quando
#    qualcosa non va.  Ogni voce porta il file da cui esce.
# ⚠ `CAPO` tollera un identificatore in testa alla riga: oggi non c'e' (ed e'
#   il difetto), ma il registro **col rimedio** ce l'ha, e i lettori devono
#   funzionare su tutt'e due — o la prova del rimedio fallirebbe per colpa del
#   banco invece che del prodotto.
CAPO = r"^(?:\[[^\]]{1,48}\] )?"
#
# ⛔ L'ORDINE CONTA: vince la prima che combacia.  ⚠ E le famiglie si sono
#    corrette **guardando le righe vere** invece di immaginarle: `[M]` 24 agosto
#    2026, la voce piu' grossa del registro a undici sessioni non era una coda
#    che si sgombra — era `rcp fotogramma N SPEDITO: … — spediti N, abbandonati
#    0`, cioe' **una riga per fotogramma**, presa per un'altra cosa perche' la
#    parola «abbandonati» ci sta dentro.  ⇒ Una famiglia sbagliata non da'
#    rosso: da' una tabella plausibile.
FAMIGLIE_DIAGNOSI = [
    # (nome, regexp sul corpo, da dove esce)
    ("fotogramma-spedito", r"fotogramma \d+ (SPEDITO|NON SPEDITO)", "rcp.c"),
    ("ciclo-cattura", r"^ciclo: \d+ fotogrammi conse", "figlio.c"),
    ("audio-blocchi", r"^audio: \d+ blocchi spediti", "figlio.c"),
    ("ritmo", r"^ritmo di ", "rcp.c"),
    ("rete-quic", r"^rete-quic ", "webtransport.c"),
    ("cattura-danno", r"buffer distinti|danno pieno \d", "figlio.c/cattura"),
    ("banda-video", r"^banda del video", "codificatore.c"),
    ("silenzio-audio", r"^⭐ silenzio DIGITALE", "audio.c"),
    ("linea-morta", r"linea[- ]morta|la linea e' MORTA", "webtransport.c"),
    ("coda-sgombro", r"sgombr|coda video|abbandonat", "webtransport.c"),
    ("fotogrammi-persi", r"buttat|scartat|\bpersi\b|saltat|NON SPEDITI", "vari"),
    ("ritmo-sceso", r"non partit|discesa del ritmo|ritmo SCESO", "webtransport.c"),
    ("chiave", r"\bchiave\b|CHIAVE", "vari"),
    ("codifica-guasto", r"^⛔ (vaBeginPicture|vaCreateBuffer|vaRenderPicture|"
                        r"vaEndPicture|vaSyncSurface|nessuna superficie|"
                        r"il fotogramma non e' entrato|nessun pacchetto|"
                        r"nessun pixel|non ha obbedito)", "codificatore.c"),
    ("qualita", r"qualita'|\bQP\b", "vari"),
]
# ⚠ `CAPO` davanti alle ancorate: il registro **col rimedio** porta `[utente]`
#   in testa, e i lettori devono funzionare su tutt'e due.
_DIAG = [(n, re.compile((CAPO + r[1:]) if r.startswith("^") else r, re.I), d)
         for n, r, d in FAMIGLIE_DIAGNOSI]


def famiglia(corpo):
    """Il modello della riga: le cifre e i nomi propri si spengono.

    ⚠ Non e' una firma perfetta e non deve esserlo: serve a raggruppare righe
      che dicono la stessa cosa di sessioni diverse.  ⛔ Le cifre vanno via
      APPOSTA — se restassero, ogni riga di regime sarebbe una famiglia sua e il
      conto per famiglia non direbbe niente.
    """
    t = re.sub(r"\[[0-9a-fA-F:.]+\]:\d+", "«PROV»", corpo)
    t = re.sub(r"«[^»]*»", "«X»", t)
    t = re.sub(r"\d+", "#", t)
    return t[:90]


def e_di_diagnosi(corpo):
    for n, r, _d in _DIAG:
        if r.search(corpo):
            return n
    return None


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ IL LETTORE DEL REGISTRO — una riga e' una riga solo se ha la sua marca
# ═══════════════════════════════════════════════════════════════════════════
#
# Il formato lo pone `registro.c:63`:  "%s.%03ld %-7s "  ⇒
#     HH:MM:SS.mmm  +  area riempita a 7  +  uno spazio  +  il corpo
RE_RIGA = re.compile(r"^(\d{2}):(\d{2}):(\d{2})\.(\d{3}) (\S+) +(.*)$")
# ⚠ La stessa marca CERCATA DENTRO il corpo: se ricompare, due scritture si sono
#   intrecciate.  ⛔ Si ancora a un confine di parola, o «alle 12:34:56.789» in
#   un testo darebbe un falso allarme.
# ⚠ `{2,10}` e non `{3,10}`: l'area `wt` e' di DUE lettere, ed e' una delle piu'
#   frequenti (`rete-quic`).  Un rivelatore che si perdesse proprio quella
#   direbbe «nessun intreccio» su un registro che ne ha.
RE_MARCA_DENTRO = re.compile(r"(?<![\d.])\d{2}:\d{2}:\d{2}\.\d{3} [a-z]{2,10} ")
RE_PROV = re.compile(r"\[[0-9a-fA-F:.]+\]:\d+")


class Riga:
    __slots__ = ("n", "ms", "area", "corpo", "grezza", "byte")

    def __init__(self, n, ms, area, corpo, grezza):
        self.n, self.ms, self.area = n, ms, area
        self.corpo, self.grezza = corpo, grezza
        self.byte = len(grezza.encode("utf-8")) + 1   # + l'a-capo


def leggi(testo):
    """Spezza il testo in righe buone e righe **orfane**.

    ⛔ Torna `(righe, orfane, innestate, troncate)`.  Una riga orfana non e' un
       fastidio di forma: e' il sintomo che due `write()` si sono accavallate, ed
       e' il difetto piu' insidioso di R10-A4 perche' **produce testo
       plausibile**.
    """
    righe, orfane, innestate, troncate = [], [], [], []
    for n, r in enumerate(testo.split("\n")):
        if r == "":
            continue
        m = RE_RIGA.match(r)
        if not m:
            orfane.append((n, r))
            continue
        ms = (int(m.group(1)) * 3600000 + int(m.group(2)) * 60000
              + int(m.group(3)) * 1000 + int(m.group(4)))
        riga = Riga(n, ms, m.group(5), m.group(6), r)
        righe.append(riga)
        if RE_MARCA_DENTRO.search(m.group(6)):
            innestate.append((n, r))
        # ⭐ La troncatura la mette `registro.c` apposta quando la riga supera il
        #    buffer: e' la cura dichiarata, e si CONTA — una riga tagliata si
        #    vede, una intrecciata no.
        if r.endswith("...") and riga.byte > PIPE_BUF - 16:
            troncate.append((n, r))
    return righe, orfane, innestate, troncate


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL METRO — LE MAPPE, COSTRUITE **DAL REGISTRO E BASTA**
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ E' la condizione di chi diagnostica: il registro ce l'ha (glielo mandano),
#    la macchina no.  Un classificatore che chiedesse a `/proc` chi e' il pid
#    1925649 misurerebbe una cosa che nella vita vera non si puo' fare.
RE_PONTE = re.compile(r"posto PRESO da (\S+) via (\S+)")
RE_GENERATO = re.compile(r"figlio generato per «([^»]+)»: pid (\d+), uid (\d+)")
RE_PRESENTA = re.compile(r"«([^»]+)» si presenta: pid (\d+)")
RE_RICONTR = re.compile(r"«([^»]+)» ricontrollato: uid (\d+), pid (\d+)")
RE_AMMESSO = re.compile(r"ammesso utente=(\S+) da=(\S+)")
RE_APERTA = re.compile(r"sessione aperta utente=(\S+) via=(\S+)")


class Mappe:
    """utente ← provenienza · uid · pid.  ⛔ Tutte lette dal registro."""

    def __init__(self, utenti):
        self.utenti = list(utenti)
        self.prov, self.uid, self.pid = {}, {}, {}
        self.righe_ponte = 0
        self._re_nome = [(u, re.compile(r"(?<![0-9A-Za-z_])%s(?![0-9A-Za-z_])"
                                        % re.escape(u))) for u in self.utenti]

    def impara(self, righe):
        for r in righe:
            for rx, quali in ((RE_PONTE, "prov"), (RE_AMMESSO, "prov"),
                              (RE_APERTA, "prov")):
                m = rx.search(r.corpo)
                if m and m.group(1) in self.utenti:
                    self.prov[m.group(2)] = m.group(1)
                    self.righe_ponte += 1
            m = RE_GENERATO.search(r.corpo)
            if m and m.group(1) in self.utenti:
                self.pid[m.group(2)] = m.group(1)
                self.uid[m.group(3)] = m.group(1)
                self.righe_ponte += 1
            for rx, gp in ((RE_PRESENTA, (1, 2)), (RE_RICONTR, (1, 3))):
                m = rx.search(r.corpo)
                if m and m.group(gp[0]) in self.utenti:
                    self.pid[m.group(gp[1])] = m.group(gp[0])
                    self.righe_ponte += 1
        return self


def prudente(riga, m):
    """⭐ IL CLASSIFICATORE PRUDENTE — solo identificatori **ancorati**.

    Torna `(utente|None, indizio)`.  ⛔ Se i candidati sono due e discordi torna
    `None` con indizio «ambigua»: ⚠ una riga che nomina due utenti — lo sfratto
    del fantasma ne nomina due — attribuita a uno dei due sarebbe **esattamente
    l'errore peggiore**, quello che manda a guardare il desktop sbagliato.
    """
    c, indizi = set(), []
    for u, rx in m._re_nome:
        if rx.search(riga.corpo):
            c.add(u); indizi.append("nome")
    for p in RE_PROV.findall(riga.corpo):
        u = m.prov.get(p)
        if u:
            c.add(u); indizi.append("provenienza")
    for v in re.findall(r"\buid[ =]\s*(\d+)", riga.corpo):
        u = m.uid.get(v)
        if u:
            c.add(u); indizi.append("uid")
    for v in re.findall(r"\bpid[ =]\s*(\d+)", riga.corpo):
        u = m.pid.get(v)
        if u:
            c.add(u); indizi.append("pid")
    if len(c) == 1:
        return c.pop(), indizi[0]
    if len(c) > 1:
        return None, "ambigua"
    return None, "muta"


def classifica_tutte(righe, m, quale="prudente"):
    """Torna una lista `(utente|None, indizio)` lunga come `righe`.

    ⛔ I tre classificatori si chiamano da qui e non altrove: due copie
       dell'euristica in due punti divergono, e la taratura ne certificherebbe
       una sola.
    """
    base = [prudente(r, m) for r in righe]
    if quale == "prudente":
        return base
    if quale == "vicinanza":
        # ⛔ L'EURISTICA UMANA: «e' di chi ha parlato poco prima».  Si guarda
        #    indietro E avanti, perche' e' quel che fa l'occhio.
        noti = [(i, r.ms, base[i][0]) for i, r in enumerate(righe)
                if base[i][0]]
        fuori = list(base)
        for i, r in enumerate(righe):
            if base[i][0]:
                continue
            best, bestd = None, VICINANZA_MS + 1
            for j, ms, u in noti:
                d = abs(ms - r.ms)
                if d < bestd:
                    best, bestd = u, d
                elif d > bestd and j > i:
                    break
            fuori[i] = (best, "vicinanza") if best else (None, "muta")
        return fuori
    if quale == "continuita":
        return _continuita(righe, m, base)
    raise ValueError(quale)


RE_CICLO = re.compile(CAPO + r"ciclo: (\d+) fotogrammi consegnati "
                             r"\((\d+) chiavi\), (\d+) attese a vuoto")


def _continuita(righe, m, base):
    """⭐ IL CLASSIFICATORE CHE SEPARA LE SERIE — e poi **tira a indovinare** il
       nome, perche' un nome nelle righe `ciclo:` non c'e'.

    `figlio.c` scrive una volta al secondo, per ogni figlio:
        `ciclo: N fotogrammi consegnati (K chiavi), A attese a vuoto, G guasti`
    N e A sono **cumulativi e non calanti**.  ⇒ Quattro figli fanno quattro
    serie crescenti, e si prova a separarle: ogni riga va alla serie il cui
    ultimo `A` e' il **piu' vicino da sotto**.

    ⛔⛔ E POI VIENE IL PUNTO: separata la serie, **come si chiama?**  Nessuna
        delle sue righe porta un nome.  ⇒ La si battezza col nome della riga
        NOTA piu' vicina nel tempo alla sua prima riga.  ⚠ E' un'ipotesi, non
        una lettura: questo classificatore esiste per far vedere **quanto
        sbaglia**, non per essere creduto.
    """
    fuori = list(base)
    serie = []          # [{"A": ultimo, "N": ultimo, "righe": [i...]}]
    noti = [(r.ms, base[i][0]) for i, r in enumerate(righe) if base[i][0]]
    for i, r in enumerate(righe):
        if base[i][0]:
            continue
        g = RE_CICLO.match(r.corpo)
        if not g:
            continue
        N, A = int(g.group(1)), int(g.group(3))
        scelta, dist = None, None
        for s in serie:
            if A >= s["A"] and N >= s["N"]:
                d = A - s["A"]
                if dist is None or d < dist:
                    scelta, dist = s, d
        if scelta is None:
            scelta = {"A": A, "N": N, "righe": []}
            serie.append(scelta)
        scelta["A"], scelta["N"] = A, N
        scelta["righe"].append(i)
    for s in serie:
        primo = righe[s["righe"][0]]
        best, bestd = None, None
        for ms, u in noti:
            d = abs(ms - primo.ms)
            if bestd is None or d < bestd:
                best, bestd = u, d
        for i in s["righe"]:
            fuori[i] = (best, "continuita") if best else (None, "muta")
    return fuori


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ LA TARATURA — si inietta provenienza NOTA e si guarda se la ritrova
# ═══════════════════════════════════════════════════════════════════════════
def tara(righe, verita, m, quale):
    """`righe` e `verita` sono appaiate; `verita[i]` e' l'utente vero o `None`.

    ⛔ Torna `None` se il campione e' vuoto: «non ho tarato» non e' «tarato al
       100 %».  ⭐ E misura TUTT'E DUE gli errori, che e' il punto.
    """
    # ⛔⛔ SI CLASSIFICA TUTTO E SI GIUDICA SOLO DOVE SI SA LA VERITA'.
    #
    #     La prima stesura dava al classificatore le sole righe di verita' nota
    #     — cioe' quelle dei FIGLI, che sono proprio quelle mute — e cosi'
    #     l'euristica «di chi ha parlato poco prima» non aveva **nessun vicino
    #     da cui copiare**: si asteneva sempre, e sembrava prudente quanto il
    #     prudente.  ⚠ E' la forma D3 di `REVIEWER.md`: un guasto innestato in
    #     un mondo in cui non puo' mordere.  ⇒ Il classificatore vede la
    #     finestra INTERA, come chi diagnostica.
    dove = [i for i, v in enumerate(verita) if v]
    if not dove:
        return None
    det_tutte = classifica_tutte(righe, m, quale)
    coppie = [(righe[i], verita[i]) for i in dove]
    det = [det_tutte[i] for i in dove]
    giuste = sbagliate = astenute = 0
    esempi_sbagliate = []
    for (r, v), (u, ind) in zip(coppie, det):
        if u is None:
            astenute += 1
        elif u == v:
            giuste += 1
        else:
            sbagliate += 1
            if len(esempi_sbagliate) < 4:
                esempi_sbagliate.append("«%s» detta di %s, e' di %s (%s)"
                                        % (r.corpo[:70], u, v, ind))
    n = len(coppie)
    return {"campione": n, "giuste": giuste, "sbagliate": sbagliate,
            "astenute": astenute,
            "q_giuste": giuste / n, "q_sbagliate": sbagliate / n,
            "q_astenute": astenute / n, "esempi_sbagliate": esempi_sbagliate}


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA MISURA — la frazione attribuibile, e quella che conta di piu'
# ═══════════════════════════════════════════════════════════════════════════
def tara_su_regime(righe, m):
    """⛔⛔ LA TARATURA DELL'EURISTICA, e la finestra «a una voce» NON LA SA FARE.

    `[M]` 24 agosto 2026, e il banco stava per riferire il contrario: nelle
    finestre a una voce «vicinanza» ha preso **il 100 % delle righe giuste**.
    ⚠ Non perche' funzioni: perche' in una finestra a una voce **c'e' una voce
      sola da cui copiare**.  ⇒ Quel campione, per quell'euristica, e' la forma
      D3 di `REVIEWER.md`: un guasto innestato in un mondo in cui non puo'
      mordere.

    ⭐ La prova giusta si fa sulla finestra **di regime**, dove le quattro
       sessioni si intrecciano davvero, e la verita' ce la danno le righe che un
       identificatore **ce l'hanno**: si NASCONDE il loro nome all'euristica e si
       guarda se lo ritrova.  ⛔ Quelle righe sono verita' provata: il
       classificatore prudente sbaglia lo **0,0 %** sul campione a una voce.

    ⚠ E il limite si dichiara: le righe con nome non sono un campione a caso
      delle righe mute — sono `ritmo`, `rete-quic` e `fotogramma da «X»`, cioe'
      quelle che escono **una volta al secondo** o **una per fotogramma**.  ⇒ Il
      numero dice *«se QUESTA riga non avesse il nome, il vicino la
      battezzerebbe giusta?»*, che e' la domanda vera di chi diagnostica.
    """
    det = classifica_tutte(righe, m, "prudente")
    noti = [(i, righe[i].ms, det[i][0]) for i in range(len(righe))
            if det[i][0]]
    if len(noti) < 20:
        return None
    giuste = sbagliate = astenute = 0
    esempi = []
    for k, (i, ms, vero) in enumerate(noti):
        best, bestd = None, VICINANZA_MS + 1
        for j in range(max(0, k - 40), min(len(noti), k + 41)):
            if j == k:
                continue
            d = abs(noti[j][1] - ms)
            if d < bestd:
                best, bestd = noti[j][2], d
        if best is None:
            astenute += 1
        elif best == vero:
            giuste += 1
        else:
            sbagliate += 1
            if len(esempi) < 4:
                esempi.append("«%s» e' di %s, il vicino dice %s"
                              % (righe[i].corpo[:60], vero, best))
    n = len(noti)
    return {"campione": n, "giuste": giuste, "sbagliate": sbagliate,
            "astenute": astenute, "q_giuste": giuste / n,
            "q_sbagliate": sbagliate / n, "q_astenute": astenute / n,
            "esempi_sbagliate": esempi}


def misura(righe, m, quale="prudente"):
    """⛔ Torna `None` se la finestra non ha righe abbastanza: «non ho misurato»
       non e' «0 %» (regola 5 del preambolo)."""
    if len(righe) < RIGHE_MINIME:
        return None
    det = classifica_tutte(righe, m, quale)
    tot = len(righe)
    attr = sum(1 for u, _i in det if u)
    # ⛔ Le righe AMBIGUE: quelle in cui due identificatori ancorati nominano
    #    DUE utenti diversi.  ⭐ Il classificatore prudente li' si astiene, ed e'
    #    la sua garanzia interna: se questo conto e' zero, nessuna riga porta
    #    identificatori che si contraddicono, e ogni attribuzione e' l'unica
    #    lettura possibile di quella riga.  ⚠ Non e' una taratura — e' un
    #    controllo di coerenza — e si riferisce come tale.
    ambigue = sum(1 for _u, i in det if i == "ambigua")
    per_utente = {}
    per_famiglia = {}
    diag_tot = diag_attr = 0
    per_diagnosi = {}
    for r, (u, ind) in zip(righe, det):
        if u:
            per_utente[u] = per_utente.get(u, 0) + 1
        f = famiglia(r.corpo)
        d = per_famiglia.setdefault(f, {"n": 0, "attr": 0, "area": r.area})
        d["n"] += 1
        d["attr"] += 1 if u else 0
        nome = e_di_diagnosi(r.corpo)
        if nome:
            diag_tot += 1
            diag_attr += 1 if u else 0
            dd = per_diagnosi.setdefault(nome, {"n": 0, "attr": 0})
            dd["n"] += 1
            dd["attr"] += 1 if u else 0
    return {
        "righe": tot, "attribuite": attr, "quota": attr / tot,
        "ambigue": ambigue,
        "per_utente": per_utente,
        "diagnosi_righe": diag_tot, "diagnosi_attribuite": diag_attr,
        "diagnosi_quota": (diag_attr / diag_tot) if diag_tot else None,
        "per_diagnosi": per_diagnosi,
        "per_famiglia": per_famiglia,
        "byte": sum(r.byte for r in righe),
        "byte_per_riga": sum(r.byte for r in righe) / tot,
        "durata_ms": (righe[-1].ms - righe[0].ms) if tot > 1 else None,
    }


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ LA DIAGNOSI CIECA — «quale sessione ha smesso di consegnare fotogrammi?»
# ═══════════════════════════════════════════════════════════════════════════
def diagnosi_cieca(righe, m, quale="prudente"):
    """Legge SOLO il registro e prova a dire chi si e' fermato.

    Il meccanismo e' quello delle righe `ciclo:` di `figlio.c`: il contatore
    `fotogrammi consegnati` e' cumulativo, e la sessione rotta e' quella la cui
    serie **smette di crescere** mentre le altre crescono.

    ⛔ Torna `(nome|None, quante_serie, quante_ferme, perche)`.
       ⭐ E le due domande sono separate apposta:
         · `quante_ferme >= 1` ⇒ **si vede che qualcuno si e' rotto**;
         · `nome is not None` ⇒ **si sa di chi**.
       Fra le due c'e' tutto il difetto R10-A4.
    """
    det = classifica_tutte(righe, m, quale)
    serie = []
    for i, r in enumerate(righe):
        g = RE_CICLO.match(r.corpo)
        if not g:
            continue
        N, A = int(g.group(1)), int(g.group(3))
        u = det[i][0]
        scelta, dist = None, None
        for s in serie:
            # ⛔ Chi ha un nome sta con chi ha lo stesso nome; chi non ce l'ha
            #    va per continuita' del contatore.
            if u and s["nome"] and s["nome"] != u:
                continue
            if A >= s["A"] and N >= s["N"]:
                d = A - s["A"]
                if dist is None or d < dist:
                    scelta, dist = s, d
        if scelta is None:
            scelta = {"A": A, "N": N, "N0": N, "nome": u, "quante": 0}
            serie.append(scelta)
        if u and not scelta["nome"]:
            scelta["nome"] = u
        scelta["A"], scelta["N"], scelta["quante"] = A, N, scelta["quante"] + 1
    vive = [s for s in serie if s["quante"] >= 3]
    # ⛔ «FERMA» NON E' «CRESCITA ZERO», e il numero l'ha imposto il vero: un
    #    desktop GNOME senza la mia scena consegna lo stesso qualche fotogramma
    #    (il cursore che lampeggia, un orologio che cambia minuto).  ⇒ Ferma =
    #    cresce meno di un decimo della mediana delle altre.  ⚠ Sul registro
    #    fabbricato la crescita e' esattamente zero, quindi il caso della
    #    certificazione resta valido.
    cresc = [s["N"] - s["N0"] for s in vive]
    med = statistics.median(cresc) if cresc else 0
    ferme = [s for s in vive if (s["N"] - s["N0"]) <= 0.10 * med]
    if not vive:
        return None, 0, 0, "nessuna serie «ciclo:» nella finestra"
    if len(ferme) != 1:
        return (None, len(vive), len(ferme),
                "%d serie, %d ferme (crescite %s fotogrammi): non c'e' un "
                "colpevole unico" % (len(vive), len(ferme), cresc))
    nome = ferme[0]["nome"]
    if nome is None:
        return (None, len(vive), 1,
                "⛔ la serie ferma si VEDE (crescite %s fotogrammi), ma NON "
                "PORTA NESSUN NOME" % cresc)
    return nome, len(vive), 1, ("serie ferma battezzata «%s» (crescite %s)"
                                % (nome, cresc))


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ IL RIVELATORE DEGLI INTRECCI — e le sue tre forme
# ═══════════════════════════════════════════════════════════════════════════
def intrecci(testo):
    righe, orfane, innestate, troncate = leggi(testo)
    lunghe = [r for r in righe if r.byte > LUNGA]
    massima = max((r.byte for r in righe), default=None)
    return {
        "righe_buone": len(righe),
        "orfane": len(orfane), "esempi_orfane": [o[1][:110] for o in orfane[:4]],
        "innestate": len(innestate),
        "esempi_innestate": [o[1][:150] for o in innestate[:4]],
        "troncate": len(troncate),
        "lunghe_oltre_%d" % LUNGA: len(lunghe),
        "riga_piu_lunga_byte": massima,
        "byte_lunghe": sorted((r.byte for r in lunghe), reverse=True)[:5],
    }


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ I PREDICATI — SCRITTI PRIMA, e ne torna (passa, perche)
# ═══════════════════════════════════════════════════════════════════════════
#   True  — l'atteso ha retto      False — ⛔ rosso
#   None  — ⚠ NON GIUDICO, e non e' un verde educato
def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)


def p_ha_misurato(d):
    """⛔ «Non ho misurato» ≠ «0 %» — regola 5 del preambolo."""
    if d is None:
        return _muto("⛔ NON HO MISURATO: la finestra non arriva a %d righe "
                     "buone.  ⚠ Non e' «lo 0 %% e' attribuibile»: e' che il "
                     "campione non c'e'" % RIGHE_MINIME)
    return _si("la finestra porta %d righe buone" % d["righe"])


def p_tutte_hanno_parlato(d, utenti):
    """⛔ Una sessione che non ha prodotto righe NON e' «tutte attribuite».

    ⚠ E' la forma peggiore: la frazione salirebbe proprio perche' una sessione
      manca, e il numero sembrerebbe **migliore**.  ⇒ ROSSO.
    """
    if d is None:
        return _muto("non c'e' niente da guardare")
    mute = [u for u in utenti
            if d["per_utente"].get(u, 0) < RIGHE_MINIME_PER_SESSIONE]
    if mute:
        return _no("⛔ %d sessioni su %d non hanno prodotto nemmeno %d righe "
                   "attribuibili (%s): la frazione di questa finestra e' alta "
                   "PERCHE' MANCANO, non perche' il registro parli chiaro"
                   % (len(mute), len(utenti), RIGHE_MINIME_PER_SESSIONE,
                      ", ".join(mute)))
    return _si("tutte e %d le sessioni hanno lasciato righe attribuibili (%s)"
               % (len(utenti),
                  " ".join("%s:%d" % (u, d["per_utente"].get(u, 0))
                           for u in utenti)))


def p_a_regime(righe, avvio_ms):
    """⛔ `CODER.md` §3.5: il campione si prende A REGIME.

    Un campione preso all'avvio falserebbe tutto **in meglio**: le righe
    d'apertura portano il nome dentro per costruzione.
    """
    if not righe:
        return _muto("nessuna riga")
    if avvio_ms is None:
        return _muto("⛔ non so quando le sessioni si sono aperte: non posso "
                     "dire se questa finestra e' a regime")
    da = righe[0].ms - avvio_ms
    if da < ASSESTAMENTO_S * 1000:
        return _no("⛔ LA FINESTRA TOCCA L'AVVIO: comincia %0.1f s dopo "
                   "l'ultima apertura, e il minimo dichiarato e' %0.0f s.  "
                   "Le righe d'avvio si attribuiscono da se' e la frazione "
                   "uscirebbe FALSA IN MEGLIO (`CODER.md` §3.5)"
                   % (da / 1000.0, ASSESTAMENTO_S))
    return _si("la finestra comincia %0.1f s dopo l'ultima apertura: e' a "
               "regime" % (da / 1000.0))


def p_taratura(t, quale, tetto_sbagliate):
    """⛔ Il metro si tara PRIMA (`LEZIONI.md` §1.33), e i due errori si
       misurano SEPARATI: astenersi e' onesto, indovinare no."""
    if t is None:
        return _muto("⛔ NON HO TARATO «%s»: non e' arrivata nessuna riga di "
                     "provenienza nota.  ⚠ Un metro non tarato produce numeri, "
                     "non misure" % quale)
    if t["q_sbagliate"] > tetto_sbagliate:
        return _no("⛔ «%s» SBAGLIA il %0.1f %% delle righe di provenienza nota "
                   "(%d su %d), e il tetto dichiarato e' %0.1f %%.  ⚠ Una riga "
                   "attribuita male manda a guardare il desktop di un altro: e' "
                   "peggio di una riga muta.  Esempi: %s"
                   % (quale, 100 * t["q_sbagliate"], t["sbagliate"],
                      t["campione"], 100 * tetto_sbagliate,
                      " | ".join(t["esempi_sbagliate"][:2])))
    return _si("«%s» tarato su %d righe di provenienza nota: %0.1f %% giuste, "
               "%0.1f %% SBAGLIATE, %0.1f %% astenute"
               % (quale, t["campione"], 100 * t["q_giuste"],
                  100 * t["q_sbagliate"], 100 * t["q_astenute"]))


def p_rivelatore_intrecci(sano, guasto):
    """⛔ Un rivelatore che non trova gli intrecci QUANDO CI SONO non vale
       niente quando dice che non ce ne sono."""
    if guasto is None:
        return _muto("non ho innestato niente: non so se il rivelatore vede")
    trovati = guasto["orfane"] + guasto["innestate"]
    if trovati == 0:
        return _no("⛔ IL RIVELATORE E' CIECO: ho innestato righe intrecciate e "
                   "non ne ha trovata nessuna.  ⇒ Il suo «zero» sul registro "
                   "vero non vale niente")
    return _si("il rivelatore trova %d righe intrecciate su quelle innestate "
               "(sul sano ne trovava %d)"
               % (trovati, sano["orfane"] + sano["innestate"]))


def p_diagnosi_cieca(esiti):
    """⭐ Il predicato che NON e' un si'/no sul prodotto: e' la misura del
       difetto.  ⛔ Rosso se il banco pretendesse di aver diagnosticato senza
       averne il diritto."""
    if not esiti:
        return _muto("nessuna prova cieca eseguita")
    visti = sum(1 for e in esiti if e["ferme"] == 1)
    nomi = sum(1 for e in esiti if e["nome"])
    giusti = sum(1 for e in esiti if e["nome"] and e["nome"] == e["vero"])
    if visti == 0:
        return _muto("⛔ NON HO POTUTO PROVARE: in nessuna delle %d prove si "
                     "vede una serie ferma — il guasto non ha morso"
                     % len(esiti))
    return _si("su %d prove: %d volte si VEDE che una sessione si e' fermata, "
               "%d volte il registro dice UN NOME, e di quelle %d e' il nome "
               "giusto" % (len(esiti), visti, nomi, giusti))


# ⚠ La soglia della frazione di diagnosi, e i due estremi sono MISURATI, non
#   scelti: `[M]` §6.7 — **4,2 %** sul binario col difetto (quattro sessioni
#   vere), e ⭐ il rimedio, provato sulle stesse righe, riporta il nome giusto.
#   ⇒ A meta' strada fra i due estremi non c'e' niente: o le famiglie grosse
#   (`fotogramma-spedito`, `ciclo-cattura`, `audio-blocchi`) portano l'identita'
#   e la frazione salta oltre la meta', o non la portano e resta sotto il 10 %.
DIAGNOSI_CURATA = 0.50


def p_la_cura_regge(esiti, mis):
    """⛔⛔ IL PREDICATO DELLA CURA DI R10-A4 — 25 agosto 2026.

    `p_diagnosi_cieca` qui sopra **misura** il difetto e non lo giudica: e' nato
    quando il difetto c'era, e un banco che dicesse ROSSO su un prodotto che si
    sa essere rotto non aggiungerebbe niente.  ⛔ Ma dal 25 agosto il prodotto e'
    stato CURATO, e da quel momento serve l'opposto: un predicato che torni
    **rosso il giorno in cui la cura si perde** — un `(void)ctx` rimesso, una
    `registro_identita()` cancellata da un montaggio, un'area rinominata.

    ⇒ Torna ROSSO se, quando **si vede** una serie ferma, il registro **non dice
      il nome** o ne dice **uno sbagliato**; e ROSSO anche se la frazione di
      righe di diagnosi attribuibili e' rimasta sotto `DIAGNOSI_CURATA`.
    ⚠ E MUTO (non verde) se il guasto non ha morso: «non ho potuto provare» non
      e' «la cura regge».
    """
    if not esiti:
        return _muto("nessuna prova cieca eseguita: NON giudico la cura")
    visti = [e for e in esiti if e["ferme"] == 1]
    if not visti:
        return _muto("⛔ NON HO POTUTO PROVARE la cura: in nessuna delle %d "
                     "prove si vede una serie ferma — il guasto non ha morso"
                     % len(esiti))
    muti = [e for e in visti if not e["nome"]]
    sbagliati = [e for e in visti if e["nome"] and e["nome"] != e["vero"]]
    if muti:
        return _no("⛔ LA CURA NON C'E': in %d prove su %d la serie ferma si "
                   "VEDE ma il registro non dice nessun nome (%s)"
                   % (len(muti), len(visti),
                      ", ".join(e["vero"] for e in muti)))
    if sbagliati:
        return _no("⛔⛔ PEGGIO DEL MUTO: %d prove su %d danno il nome "
                   "SBAGLIATO — manda a guardare il desktop di un altro (%s)"
                   % (len(sbagliati), len(visti),
                      ", ".join("%s→%s" % (e["vero"], e["nome"])
                                for e in sbagliati)))
    if mis is None or mis.get("diagnosi_quota") is None:
        return _muto("⭐ la prova cieca torna il nome giusto %d volte su %d, "
                     "⚠ ma la frazione di diagnosi non e' stata misurata: "
                     "NON giudico" % (len(visti), len(visti)))
    if mis["diagnosi_quota"] < DIAGNOSI_CURATA:
        return _no("⛔ la prova cieca torna il nome giusto, ⚠ ma solo il %0.1f "
                   "%% delle righe di DIAGNOSI e' attribuibile (sotto il %0.0f "
                   "%%): la cura non e' arrivata alle famiglie grosse"
                   % (100 * mis["diagnosi_quota"], 100 * DIAGNOSI_CURATA))
    return _si("⭐⭐ LA CURA REGGE: la prova cieca torna il NOME GIUSTO %d volte "
               "su %d, e il %0.1f %% delle righe di diagnosi e' attribuibile"
               % (len(visti), len(visti), 100 * mis["diagnosi_quota"]))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA FABBRICA — registri finti di verita' NOTA, per la taratura e i guasti
# ═══════════════════════════════════════════════════════════════════════════
def _marca(ms):
    return "%02d:%02d:%02d.%03d" % (ms // 3600000, (ms // 60000) % 60,
                                    (ms // 1000) % 60, ms % 1000)


def fabbrica(utenti, secondi=40, t0=12 * 3600000, avvio=True, muta=None,
             frizzo=None, con_cura=False):
    """Un registro finto **di verita' nota**, modellato riga per riga su quello
       vero (le famiglie sono quelle misurate il 24 agosto 2026 sulla 8150).

    Torna `(testo, verita)`: `verita[i]` e' l'utente della riga i-esima, o
    `None` per le righe che non sono di nessuna sessione (il padre).

    ⛔⛔ E LE FASI SONO INDIPENDENTI PER FAMIGLIA E PER SESSIONE, che e' la cosa
        che conta.  `[M]` sul registro vero: `rcp ritmo` esce a `.028`, `figlio
        ciclo:` a `.486`, `figlio audio:` a `.598` — cioe' **mezzo secondo**
        dopo la riga che porta il nome.  ⚠ Una fabbrica che mettesse le righe di
        una sessione tutte vicine renderebbe l'euristica «di chi ha parlato
        poco prima» **giusta per costruzione**, e la certificazione direbbe che
        indovinare funziona.  ⇒ Le fasi si scelgono a caso (seme FISSO: un
        banco che cambia numeri a ogni giro non e' un banco).

    · `muta`     — un utente che non produce NESSUNA riga
    · `frizzo`   — un utente il cui contatore dei fotogrammi **e' fermo** (la
                   scena spenta: il difetto vero della prova cieca)
    · `con_cura` — ⭐ il registro **come sarebbe con il rimedio**: ogni riga di
                   sessione portata in testa dal suo `[utente]`.  Serve a
                   mostrare che il rimedio chiude la diagnosi, e a pesarlo.
    """
    rng = random.Random(96)
    prov = {u: "[192.168.0.2]:%d" % (35000 + 7 * i)
            for i, u in enumerate(utenti)}
    pid = {u: 1925000 + 13 * i for i, u in enumerate(utenti)}
    uid = {u: 1103 + i for i, u in enumerate(utenti)}
    vivi = [u for u in utenti if u != muta]
    ev = []                                  # (ms, area, corpo, chi)

    def agg(ms, area, corpo, chi):
        if con_cura and chi:
            corpo = "[%s] %s" % (chi, corpo)
        ev.append((ms, area, corpo, chi))

    ms = t0
    if avvio:
        agg(ms, "avvio", "REMOTIX_V2 — fase 1, il filo nudo", None)
        for u in vivi:
            ms += 120
            agg(ms, "figlio", "⭐ figlio generato per «%s»: pid %d, uid %d, "
                              "gid %d, matricola 1"
                % (u, pid[u], uid[u], uid[u]), u)
            agg(ms + 1, "rcp", "ammesso utente=%s da=%s" % (u, prov[u]), u)
            agg(ms + 2, "rcp", "posto PRESO da %s via %s (occupati adesso: 1)"
                % (u, prov[u]), u)
        ms += 800
    # ⭐ IL REGIME — le famiglie vere, coi loro contatori cumulativi.
    cont = {u: {"N": 40 + 3 * i, "A": 6000 + 700 * i, "B": 0}
            for i, u in enumerate(vivi)}
    passo = {u: 24 + 5 * i for i, u in enumerate(vivi)}
    fase = {u: {k: rng.randrange(0, 1000) for k in
                ("ritmo", "rete", "ciclo", "audio", "video")} for u in vivi}
    for s in range(secondi):
        for u in vivi:
            f, b = fase[u], ms + s * 1000
            agg(b + f["ritmo"], "rcp",
                "ritmo di %s: arretrato LETTO %d volte in quest'ultimo "
                "secondo, massimo 1, ultimo 0, posti 2 — 0 fotogrammi non "
                "partiti in questo secondo, 0 in tutto" % (prov[u], 20), u)
            agg(b + f["rete"], "wt",
                "rete-quic %s da_ms=1000 persi=0 spediti=%d byte_spediti=%d "
                "cwnd=13200 srtt_us=1900" % (prov[u], 70 + s, 90000 + 1400 * s),
                u)
            if frizzo != u:
                cont[u]["N"] += passo[u]
            cont[u]["A"] += 120 + 7 * (u != vivi[0])
            agg(b + f["ciclo"], "figlio",
                "ciclo: %d fotogrammi consegnati (2 chiavi), %d attese a vuoto "
                "(scena ferma: Mutter consegna solo quando qualcosa cambia), 0 "
                "guasti — codec 3, 60/s chiesti, attesa 0.01 s"
                % (cont[u]["N"], cont[u]["A"]), u)
            agg(b + f["audio"], "figlio",
                "audio: %d blocchi spediti, 0 persi, %d fotogrammi in attesa "
                "nell'anello — codec 2" % (cont[u]["B"], 16 * (s % 12)), u)
            if s % 5 == 0:
                agg(b + f["video"], "video",
                    "⛔ nessuna superficie libera nel magazzino (3 pronte): "
                    "riprovo", u)
        if s % 10 == 3:
            agg(ms + s * 1000 + 500, "quic",
                "connessione nuova da [192.168.0.9]:%d (in tutto %d)"
                % (40000 + s, 4 + s), None)
    ev.sort(key=lambda e: e[0])
    R = ["%s %-7s %s" % (_marca(e[0]), e[1], e[2]) for e in ev]
    V = [e[3] for e in ev]
    return "\n".join(R) + "\n", V


def _intreccia(righe, quale, dove):
    """⛔ L'INTRECCIO VERO, non una riga sporcata a caso.

    Quando la `write()` di B cade dentro quella di A, sul file restano **due**
    righe fisiche: `A[:k] + B` (che porta una marca temporale **dentro il
    corpo**) e `A[k:]` (che non ne ha nessuna, ed e' **orfana**).  ⇒ Si innesta
    esattamente quello, o il rivelatore si taribbe su un guasto che non e' il
    suo.  ⚠ Il taglio si mette **su uno spazio**: tagliando dentro un numero, la
    marca di B verrebbe preceduta da una cifra e la ricerca la scarterebbe.
    """
    a = righe[quale]
    k = a.find(" ", dove)
    if k < 0:
        k = max(0, len(a) // 2)
    fuori = list(righe)
    fuori[quale] = a[:k + 1] + righe[quale + 1]
    fuori.insert(quale + 1, a[k + 1:])
    return fuori


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ LA RADICE — un solo `sudo`, e la catena dentro la SUA shell
# ═══════════════════════════════════════════════════════════════════════════
def _b92():
    """⭐ Il macchinario delle sessioni sta gia' scritto e gia' certificato in
       `10-b92-dieci.py`: non se ne riscrive una riga, si importa e gli si
       cambiano SOLO gli utenti (che li' sono `provamt*` e qui no).

    ⚠ E le variabili d'ambiente vanno poste PRIMA dell'import: quel modulo le
      legge al caricamento.
    """
    os.environ.update({
        "PORTA": str(PORTA), "LAV": LAV, "ALBERO": ALB,
        "DENTRO_ALB": DENTRO_ALB, "DENTRO_LAV": DENTRO_LAV, "UNITA": UNITA,
        "IO_SONO": IO_SONO, "FUORI": FUORI, "LUCCHETTO": LUCCHETTO,
        "QUANTI": str(QUANTI)})
    spec = importlib.util.spec_from_file_location(
        "b92", os.path.join(QUI, "10-b92-dieci.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.utente = lambda i: SESSIONI[i - 1][0]
    m.uid = lambda i: SESSIONI[i - 1][1]
    return m


B = None    # il modulo `10-b92-dieci.py`, importato in `principale()`


def root(cmd, tetto=180):
    return B.root(cmd, tetto)


def punto(percorso=None):
    """A che byte e' il registro **adesso**.  ⛔ `None` se non l'ho letto."""
    REGISTRO = percorso or globals()["REGISTRO"]
    rc, out, err = root("stat -c %%s %s" % REGISTRO)
    t = out.strip()
    if rc != 0 or not t.isdigit():
        _dub("⛔ il registro NON si e' letto (rc=%s): «%s»"
             % (rc, (t + " " + err.strip())[:120]))
        return None
    n = int(t)
    if n <= 0:
        _dub("⛔ il registro e' a ZERO byte col server acceso: e' una lettura "
             "fallita, non una misura")
        return None
    return n


def fetta(a, b, percorso=None):
    """I byte del registro fra `a` e `b`.  ⛔ `None` se non li ho presi.

    ⭐ I confini sono **byte**, non orologi: due finestre non possono
       sovrapporsi per costruzione, e non serve nessun ponte fra orologi.
    """
    REGISTRO = percorso or globals()["REGISTRO"]
    if a is None or b is None or b <= a:
        return None
    rc, out, err = root("tail -c +%d %s | head -c %d | gzip -9 | base64 -w0"
                        % (a + 1, REGISTRO, b - a), 600)
    t = out.strip()
    if rc != 0 or not t:
        _dub("⛔ la fetta [%s,%s) non si e' presa: %s" % (a, b, err[-120:]))
        return None
    try:
        crudo = gzip.decompress(base64.b64decode(t))
    except Exception as e:
        _dub("⛔ la fetta [%s,%s) non si e' decompressa: %s" % (a, b, e))
        return None
    testo = crudo.decode("utf-8", "replace")
    # ⛔⛔ LA PRIMA RIGA DI UNA FETTA CHE NON COMINCIA A ZERO E' MOZZA, E IL
    #     RIVELATORE DEGLI INTRECCI LA CONTAVA COME UN INTRECCIO — `[M]` 24
    #     agosto 2026, sul registro a undici sessioni: **1 riga orfana** su
    #     49 389, e sembrava il difetto che questo banco cerca.  ⚠ Non lo era:
    #     era il taglio della fetta.  ⇒ La riga mozza si butta, e il fatto si
    #     dichiara qui invece di finire in un numero.
    # ⭐ E il controllo che l'ha smascherata e' la scansione dell'INTERO file
    #    (`scansione_intera`), che non ha nessun taglio: diceva **zero**.
    #    Due metri sulla stessa grandezza, e il disaccordo era del banco.
    if a > 0:
        k = testo.find("\n")
        testo = testo[k + 1:] if k >= 0 else ""
    return testo


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LE SESSIONI, E LE FINESTRE «A UNA VOCE»
# ═══════════════════════════════════════════════════════════════════════════
def figli_pid():
    """pid del figlio di ciascuna sessione, CHIESTO AL NUCLEO.

    ⛔ E' la verita' esterna: il registro non lo dice (e' il difetto).  ⚠ Serve
       solo al BANCO, per fermare i figli e sapere di chi sono le righe: il
       classificatore non la usa mai, e se la usasse misurerebbe una cosa che
       chi diagnostica non puo' fare.
    """
    fuori = {}
    for u, n, _mv, _dn in SESSIONI:
        rc, out, _ = root("pgrep -u %d -f -- '--figlio-interno' | head -2" % n)
        p = [x for x in out.split() if x.isdigit()]
        fuori[u] = p[0] if len(p) == 1 else None
        if len(p) > 1:
            _dub("⚠ «%s» ha %d processi «--figlio-interno»: NON so quale sia "
                 "il suo figlio, e non lo indovino" % (u, len(p)))
    return fuori


def accendi_scena_mia(i):
    """⛔ Come `10-b92-dieci.accendi_scena`, con DUE cambi che sono isolamento:
       il blocco in `/dev/shm` porta il MIO nome e non `10b92-*`.

    `[M]` 24 agosto 2026: col nome di b92 la scena non parte affatto —
    `shm_open(//10b92-1): Permission denied`, perche' quel blocco esiste gia' ed
    e' di `provamt1` dal giro dell'altro agente.  ⚠ E il sintomo sarebbe stato
    «quattro desktop fermi contati come quattro desktop al lavoro».
    """
    u, n, mv, dn = SESSIONI[i - 1]
    reg = "%s/scena-%d.log" % (LAV, i)
    for tentativo in range(3):
        usc = B.uscita_del(i)
        if not usc:
            time.sleep(3.0)
            continue
        root("setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
             "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
             "XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 "
             "%s --uscita %s --movimento %s --danno %s --shm /10b96-%d "
             "--giro b96-%d >> %s 2>&1 & echo acceso"
             % (n, n, u, u, n, SCENA_BIN, usc, mv, dn, i, i, reg))
        time.sleep(2.5)
        rc, out, _ = root("pgrep -u %d -f '04-b30-scena --uscita' | head -1" % n)
        if out.strip():
            return usc
        rc, out, _ = root("tail -3 %s 2>/dev/null || true" % reg)
        _dub("⚠ la scena di s%d non e' partita al tentativo %d — dice: %s"
             % (i, tentativo + 1, out.strip()[-160:]))
        time.sleep(3.0)
    return None


# ⛔⛔ NESSUNA CONTROBARRA IN QUESTE DUE, E NON E' UN VEZZO — `[M]` 24 ago 2026.
#
#     La prima stesura scriveva `\.`, e fra il `ssh`, il `sudo -S` e il
#     `bash -c` la controbarra si perdeva: `grep -acvE` rispondeva che **tutte
#     le 354 178 righe erano orfane**.  ⚠ E il banco l'avrebbe riferito: «il
#     100 % delle righe e' rotto» e' un numero, e sembrava una misura.
#   ⇒ Il punto letterale si scrive `[.]`, che attraversa tre livelli di
#     virgolette senza cambiare — la stessa cura che il progetto usa gia' per
#     `pgrep -f '[/]srv/...'`.
# ⭐ E il controllo che l'ha smascherata sta nel banco: `p_scansione_sana`.
MARCA_RX = "^[0-9][0-9]:[0-9][0-9]:[0-9][0-9][.][0-9][0-9][0-9] "
DENTRO_RX = ("^[0-9][0-9]:[0-9][0-9]:[0-9][0-9][.][0-9][0-9][0-9] .*"
             "[^0-9.][0-9][0-9]:[0-9][0-9]:[0-9][0-9][.][0-9][0-9][0-9] "
             "[a-z][a-z]* ")


def scansione_intera(percorso):
    """⭐ LE RIGHE ROTTE SU **TUTTO** IL FILE, non sulla fetta.

    ⛔ Gli intrecci sono rari: cercarli in 8 MB di coda vorrebbe dire misurare
       una frequenza su un campione venti volte piu' piccolo del disponibile, e
       poi dire «zero».  ⚠ E lo `zero` di un campione piccolo somiglia in tutto
       allo zero di un fatto.  ⇒ Le passate sono quattro `grep`/`awk` sulla
       macchina, che costano niente e leggono i 42 MB per intero.
    ⛔ E ogni conto che non si legge torna `None`, non zero.
    """
    def numero(comando):
        rc, out, _ = root(comando, 900)
        t = out.strip().split()
        return int(t[0]) if t and t[0].isdigit() else None

    tot = numero("wc -l < %s" % percorso)
    orfane = numero("grep -acvE '%s' %s || true" % (MARCA_RX, percorso))
    # ⛔⛔ E NON TUTTE LE RIGHE SENZA MARCA SONO UN INTRECCIO — `[M]` 24 ago 2026.
    #
    #     Sul registro `08-f` le sette righe «orfane» erano tutte
    #     `[libopus @ 0x…] 1 frames left in the queue on closing`, e su `09`
    #     l'unica era il caricatore dinamico: *«error while loading shared
    #     libraries»*.  ⇒ Sono **terzi che scrivono sul nostro stesso stderr**,
    #     non nostre righe spezzate.
    # ⭐ Ed e' un fatto che riguarda R10-A4 lo stesso, e va detto: il registro
    #    di questo prodotto **non e' solo suo**.  Le righe di `libopus`, di
    #    SVT-AV1 e del caricatore non portano ne' ora, ne' area, ne' identita' —
    #    e a dieci inquilini nemmeno si sa di quale sessione parlino.
    estranee = numero(
        "grep -acE '^[[][A-Za-z0-9_]+ @ 0x|^Svt[[]|error while loading "
        "shared|[|] *(INFO|WARN|DEBUG) *[|]' %s || true" % percorso)
    dentro = numero("grep -acE '%s' %s || true" % (DENTRO_RX, percorso))
    massima = numero("awk '{ if (length($0)>m) m=length($0) } END {print m+0}' "
                     "%s" % percorso)
    lunghe = numero("awk 'length($0)>%d' %s | wc -l" % (LUNGA, percorso))
    troncate = numero("grep -acE '[.][.][.]$' %s || true" % percorso)
    # ⛔⛔ IL CONTROLLO POSITIVO DELLA SCANSIONE, e nasce da un errore vero:
    #     se il modello non arriva intero fino a `grep`, «nessuna riga combacia»
    #     e «tutte le righe sono rotte» hanno la stessa faccia.  ⇒ Si contano
    #     anche le righe **buone**, e se non fanno quasi il totale la scansione
    #     si dichiara NON FATTA invece di riferire il 100 %.
    buone = numero("grep -acE '%s' %s || true" % (MARCA_RX, percorso))
    sana = (tot and buone is not None and buone > 0.5 * tot)
    rotte = (None if not sana or orfane is None or estranee is None
             else max(0, orfane - estranee))
    return {"righe_in_tutto": tot, "righe_buone": buone,
            "senza_marca": orfane if sana else None,
            "estranee": estranee if sana else None,
            "orfane": rotte,
            "innestate": dentro if sana else None,
            "riga_piu_lunga": massima, "lunghe_oltre_%d" % LUNGA: lunghe,
            "finiscono_in_puntini": troncate,
            "scansione_credibile": bool(sana),
            "quota_rotte": (None if rotte is None or dentro is None
                            else (rotte + dentro) / tot)}


def analizza_file(percorso, mega=8.0):
    """⭐ LA SECONDA PROVA, su un registro **gia' scritto**: si legge una fetta
       di CODA (cioe' a regime, non all'avvio), si scoprono gli utenti dalle
       righe di ponte, e si misura.

    ⛔⛔ E PERCHE' ESISTE: il mio giro ha **quattro** sessioni, e la fase punta a
        dieci.  Sulla macchina di prova ci sono i registri veri dei giri a
        **undici** sessioni.  ⚠ Non sono miei, e questo si DICHIARA: da quel
        registro si prende quel che non dipende da chi l'ha prodotto — la
        frazione attribuibile e le righe intrecciate — e **non** si prende
        niente che riguardi le prestazioni.
    ⛔ E il classificatore e' lo stesso, tarato sul mio giro: un metro tarato e'
       un prodotto, non un attrezzo privato (`LEZIONI.md` §1.35).
    """
    n = punto(percorso)
    if n is None:
        return None
    da = max(0, int(n - mega * 1024 * 1024))
    # ⛔ Gli utenti si scoprono DAL REGISTRO, su tutto il file: e' quel che ha in
    #    mano chi diagnostica.  ⚠ E si prende anche il primo pezzo del file,
    #    dove sta il ponte: le mappe le si impara di li', la misura no.
    rc, out, _ = root("grep -ao 'posto PRESO da [A-Za-z0-9_]*' %s | "
                      "sed 's/.* //' | sort -u | head -20" % percorso)
    utenti = [u for u in out.split() if u]
    if not utenti:
        _dub("⛔ nessuna riga di ponte «posto PRESO da» in «%s»: NON misuro"
             % percorso)
        return None
    testo = fetta(da, n, percorso)
    if testo is None:
        return None
    righe, orfane, innestate, troncate = leggi(testo)
    # ⛔⛔ LE MAPPE SI PRENDONO DA TUTTO IL FILE, NON DALL'INIZIO.
    #
    #     La prima stesura leggeva i primi 4 MB e cercava li' il ponte: `[M]` le
    #     righe `ritmo di [prov]` risultavano attribuibili solo al **28,6 %**,
    #     perche' chi si riattacca cambia porta e il suo ponte sta **in mezzo**
    #     al file.  ⇒ Il ponte si cerca con un `grep` su tutti i 42 MB.
    # ⭐ Ed e' gia' un risultato: per attribuire UNA riga di regime bisogna
    #    setacciare **l'intero registro** in cerca della riga di ponte.  Se il
    #    registro e' stato ruotato, quella riga non c'e' piu' e la riga di
    #    regime torna muta per sempre.
    rc, out, _ = root("grep -aE 'posto PRESO da |figlio generato per |"
                      "ammesso utente=|sessione aperta utente=|si presenta: "
                      "pid |ricontrollato: uid ' %s | head -20000" % percorso,
                      600)
    r_ponte, _o, _i, _t = leggi(out)
    m = Mappe(utenti).impara(r_ponte + righe)
    d = misura(righe, m, "prudente")
    inv = intrecci(testo)
    aperture = sum(1 for r in righe if "posto PRESO da" in r.corpo)
    return {"percorso": percorso, "byte_file": n, "byte_letti": n - da,
            "utenti": utenti, "misura": d, "intrecci": inv,
            "scansione_intera": scansione_intera(percorso),
            "righe_di_ponte_in_tutto": len(r_ponte),
            "aperture_dentro_la_fetta": aperture,
            "mappe": {"prov": len(m.prov), "uid": len(m.uid),
                      "pid": len(m.pid), "righe_ponte": m.righe_ponte}}


def ultima_marca():
    """La marca temporale dell'ULTIMA riga del registro, in ms dalla mezzanotte.

    ⛔ Serve a `p_a_regime`, e dev'essere letta **dallo stesso orologio delle
       righe**: un `time.time()` del portatile e le marche del server sono due
       orologi diversi, e il ponte fra i due sarebbe una cosa da tarare a sua
       volta.  ⭐ Cosi' non c'e' nessun ponte: e' la stessa scala.
    ⚠ E la mezzanotte: un giro a cavallo delle 00:00 darebbe una differenza
      negativa.  ⇒ `p_a_regime` la rifiuta invece di crederci.
    """
    rc, out, _ = root("tail -c 4000 %s | tail -1" % REGISTRO)
    m = RE_RIGA.match(out.strip())
    if not m:
        return None
    return (int(m.group(1)) * 3600000 + int(m.group(2)) * 60000
            + int(m.group(3)) * 1000 + int(m.group(4)))


def scene_vive():
    """Chi disegna e chi no.  ⛔ Una scena morta a meta' non fa cadere niente:
       fa **calare il carico**, ed e' la forma che non da' rosso."""
    fuori = {}
    for i, (_u, n, _m, _d) in enumerate(SESSIONI, 1):
        rc, out, _ = root("pgrep -u %d -f '04-b30-scena --uscita' | head -1" % n)
        fuori[i] = bool(out.strip())
    return fuori


def assicura_scene():
    riaccese = []
    for i, viva in scene_vive().items():
        if not viva and accendi_scena_mia(i):
            riaccese.append(i)
    if riaccese:
        _dub("⚠ RIACCESE le scene di %s: erano morte, e senza di loro quelle "
             "sessioni sarebbero desktop fermi contati come sessioni al lavoro"
             % ", ".join("s%d" % i for i in riaccese))
    return riaccese


def finestra(secondi, prima=None, dopo=None):
    """Una finestra di registro, in byte.  ⭐ `prima`/`dopo` girano DENTRO i
       confini, cosi' quel che fanno finisce nella fetta."""
    if prima:
        prima()
    a = punto()
    time.sleep(secondi)
    b = punto()
    if dopo:
        dopo()
    return fetta(a, b)


def a_una_voce(pid_di, secondi, chi=None, riposo=4.0):
    """⛔⛔ LA TARATURA VIVA — la verita' viene da FUORI dal registro.

    Si mette in `SIGSTOP` ogni figlio **tranne** `chi` (o tutti, se `chi` e'
    `None`), si prende una finestra, e si riparte.  ⇒ In quella finestra le
    righe che un figlio puo' aver scritto sono di **uno solo**, per costruzione.

    ═══════════════════════════════════════════════════════════════════════
    ⛔⛔ E LA FINESTRA DURA UN SECONDO E MEZZO, NON CINQUE — `[M]` 24 ago 2026
    ═══════════════════════════════════════════════════════════════════════

    La prima stesura fermava i figli per **5 s**.  ⚠ Il banco l'ha provato, e
    **tutte e quattro le sessioni sono morte**:

        `20:04:17  rcp  ⛔ [192.168.0.2]:59521: il ritmo SCENDE — arretrato 2
                        delta contro 2 posti, 7403 byte fermi nella coda`
        `20:04:26  wt   linea-morta … causa=stallo stallo_ms=5000
                        soglia_stallo_ms=5000 usciti_byte=0 coda_video=8862
                        persi=0`

    ⇒ Un figlio fermo lascia byte fermi nella coda del video del padre, e
      **quello** e' lo stallo che la linea morta conta: soglia 5 000 ms.  Con 5 s
      di fermo piu' la ripresa si arriva a nove secondi, e la cura chiude.
    ⭐ Con **1,5 s** si sta 3,3 volte sotto la soglia, e il campione basta lo
      stesso: `[M]` il registro fa ~650 righe/s con quattro sessioni sature, cioe'
      ~160 per sessione al secondo — un secondo e mezzo sono centinaia di righe.
    ⛔ E il riposo dopo il `SIGCONT` e' LUNGO (4 s) apposta: alla ripresa il
      figlio scarica in un colpo quel che aveva, la coda si gonfia di nuovo, e il
      conto dello stallo **non riparte da zero subito**.
    ⚠ E dopo ogni finestra si guarda se le sessioni sono vive: se una e' caduta,
      la taratura si ferma li' invece di raccogliere un campione di una
      popolazione diversa da quella che dichiara.
    """
    altri = [p for u, p in pid_di.items() if p and u != chi]
    if not altri:
        return None
    root("kill -STOP %s; true" % " ".join(altri))
    time.sleep(0.4)                       # ⚠ che l'ultimo fiato sia uscito
    testo = finestra(secondi)
    root("kill -CONT %s; true" % " ".join(altri))
    time.sleep(riposo)                    # ⚠ che il fiato trattenuto esca
    return testo


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL DISEGNO DELLA CURA, E QUANTO COSTEREBBE
# ═══════════════════════════════════════════════════════════════════════════
def disegno_cura(d, secondi, quante_sessioni):
    """⛔ Si VERIFICA sul sorgente invece di ripeterlo, e si dice **quanto
       costa**: un registro che raddoppia di volume e' un altro problema."""
    fuori = {"verifiche": [], "costo": {}}

    def guarda(nome, comando, atteso):
        rc, out, _ = root(comando)
        t = out.strip()
        fuori["verifiche"].append(
            {"che": nome, "visto": t[:200], "regge": bool(t)})
        return t

    # 1. `gancio_registra` ha DAVVERO il contesto in mano, e lo butta.
    guarda("webtransport.c — gancio_registra butta il contesto",
           "grep -n -A3 'static void gancio_registra' %s/src/webtransport.c"
           % ALB, None)
    # 2. …e da quel contesto si arriva DAVVERO al nome dell'utente.
    guarda("rcp.h — c'e' `rcp_utente()`, e il `wt` porta `rcp` e `provenienza`",
           "grep -n 'rcp_utente' %s/src/rcp.h; grep -n 'char provenienza\\|"
           "struct rcp_sessione \\*rcp;' %s/src/webtransport.c" % (ALB, ALB),
           None)
    # 3. Tutte le righe di `rcp.c` passano da UN SOLO punto.
    guarda("rcp.c — tutte le righe passano da `reg(s, …)`, che HA la sessione",
           "grep -c 'reg(s,' %s/src/rcp.c; grep -n 'static void reg(rcp_sessione'"
           " %s/src/rcp.c" % (ALB, ALB), None)
    # 4. Il formato di `registro.c` non porta il pid.
    guarda("registro.c — il formato e' ora + area, e basta",
           "grep -n 'snprintf(buf, sizeof buf' %s/src/registro.c" % ALB, None)
    # 5. I figli hanno il pid (e il nome) nella loro riga di comando.
    guarda("figlio.c — il figlio conosce il proprio utente fin dall'exec",
           "grep -n 'figlio-interno' %s/src/figlio.c | head -4" % ALB, None)

    # ⭐⭐ E IL CONTO CHE DICE **DOVE** VA MESSO IL RIMEDIO: quante righe di
    #     registro nascono in ciascun file, e — soprattutto — **quali le scrive
    #     il PADRE** (che e' UN processo per tutte le sessioni) e quali il
    #     FIGLIO (che e' un processo per sessione).
    # ⛔ La distinzione e' tutta qui: il pid nel formato di `registro.c` separa
    #    per PROCESSO, quindi cura i figli **tutti in una riga di codice** e non
    #    cura il padre **per niente**.
    rc, out, _ = root(
        "cd %s/src && for f in rcp.c webtransport.c figlio.c codificatore.c "
        "audio.c sessione.c main.c; do printf '%%s=%%s ' \"$f\" "
        "\"$(grep -cE 'registro_dice[(]|registro_dettaglio[(]|reg[(]s,' $f)\"; "
        "done" % ALB)
    fuori["chiamate_per_file"] = out.strip()

    if d:
        righe_s = d["righe"] / max(1.0, (d["durata_ms"] or 1) / 1000.0)
        bpr = d["byte_per_riga"]
        # ⭐ I due prefissi, misurati sul vero:
        #    · il pid nel formato di `registro.c`: «%6d » = 7 byte per OGNI riga
        #    · «[utente] » in `gancio_registra`: solo sulle righe che passano
        #      di li', ma per il conto peggiore lo si mette su tutte
        nome_medio = statistics.mean([len(u) for u, _n, _m, _dn in SESSIONI])
        fuori["costo"] = {
            "righe_al_secondo": round(righe_s, 2),
            "righe_al_secondo_per_sessione": round(righe_s / quante_sessioni, 2),
            "byte_per_riga": round(bpr, 1),
            "byte_al_secondo": round(righe_s * bpr, 0),
            "pid_byte_per_riga": 7,
            "pid_crescita_pct": round(100 * 7 / bpr, 2),
            "utente_byte_per_riga": round(nome_medio + 3, 1),
            "utente_crescita_pct": round(100 * (nome_medio + 3) / bpr, 2),
            "tutt_e_due_crescita_pct": round(100 * (7 + nome_medio + 3) / bpr, 2),
            "byte_in_piu_al_secondo": round(righe_s * (7 + nome_medio + 3), 0),
            "previsione_a_10_sessioni_byte_s":
                round(righe_s / quante_sessioni * 10 * (bpr + 7 + nome_medio + 3), 0),
        }
    return fuori


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ IL MODO `--certifica` — i guasti si INNESTANO e si FANNO GIRARE
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    _log("⛔⛔ CERTIFICAZIONE — ogni predicato col suo guasto, e il guasto GIRA")
    _inf("⚠ non tocca la macchina di prova: i registri sono FABBRICATI, e la "
         "loro verita' e' nota riga per riga")
    esiti = []

    def caso(nome, atteso, visto, ok):
        esiti.append({"caso": nome, "atteso": atteso, "visto": visto, "ok": ok})
        (_ok if ok else _ko)("%-46s atteso %-9s visto %-9s" % (nome, atteso, visto))
        return ok

    U = [u for u, _n, _m, _d in SESSIONI]

    # ── 1 · SANO: il classificatore prudente si tara e non sbaglia ──────────
    testo, ver = fabbrica(U, secondi=40)
    righe, _o, _i, _t = leggi(testo)
    m = Mappe(U).impara(righe)
    t = tara(righe, ver, m, "prudente")
    caso("1 sano · prudente tarato, zero sbagliate",
         "0 sbagliate", "%d sbagliate su %d" % (t["sbagliate"], t["campione"]),
         p_taratura(t, "prudente", 0.0)[0] is True and t["sbagliate"] == 0)

    # ── 2 · ⛔ IL CLASSIFICATORE CHE INDOVINA — misurato, non nascosto ──────
    tv = tara(righe, ver, m, "vicinanza")
    tc = tara(righe, ver, m, "continuita")
    caso("2 guasto · «vicinanza» indovina ⇒ SBAGLIA e si vede",
         "sbagliate>0", "%0.1f %% sbagliate" % (100 * tv["q_sbagliate"]),
         tv["q_sbagliate"] > 0 and p_taratura(tv, "vicinanza", 0.0)[0] is False)
    caso("2-bis guasto · «continuita» indovina ⇒ SBAGLIA e si vede",
         "sbagliate>0", "%0.1f %% sbagliate" % (100 * tc["q_sbagliate"]),
         tc["q_sbagliate"] > 0)
    caso("2-ter risanato · il prudente sulle STESSE righe si astiene",
         "astenute>0, sbagliate=0",
         "%0.1f %% astenute, %d sbagliate"
         % (100 * t["q_astenute"], t["sbagliate"]),
         t["q_astenute"] > 0 and t["sbagliate"] == 0)

    # ── 3 · ⛔ UNA SESSIONE CHE NON HA PRODOTTO RIGHE ⇒ ROSSO ───────────────
    d_sano = misura(righe, m)
    caso("3 sano · tutte e quattro hanno parlato", "vero",
         str(p_tutte_hanno_parlato(d_sano, U)[0]),
         p_tutte_hanno_parlato(d_sano, U)[0] is True)
    testo_m, ver_m = fabbrica(U, secondi=40, muta=U[2])
    righe_m, _o, _i, _t2 = leggi(testo_m)
    m_m = Mappe(U).impara(righe_m)
    d_muta = misura(righe_m, m_m)
    p = p_tutte_hanno_parlato(d_muta, U)
    caso("3 guasto · «%s» non parla ⇒ ROSSO" % U[2],
         "False", str(p[0]), p[0] is False)
    #    ⛔⛔ E LA TRAPPOLA SI FA VEDERE: il conto INGENUO — «delle sessioni che
    #        compaiono nel registro, quante so attribuire?» — darebbe **100 %**
    #        proprio perche' una sessione **manca**.  E' la forma peggiore: non
    #        un rosso, un numero migliore del vero.
    ingenuo = len(d_muta["per_utente"]) / max(1, len(d_muta["per_utente"]))
    onesto = len(d_muta["per_utente"]) / len(U)
    caso("3-bis · il conto INGENUO direbbe 100 % perche' una manca",
         "ingenuo>onesto", "%0.0f %% contro %0.0f %%"
         % (100 * ingenuo, 100 * onesto), ingenuo > onesto)
    caso("3 risanato · rimessa la sessione, torna vero", "True",
         str(p_tutte_hanno_parlato(d_sano, U)[0]),
         p_tutte_hanno_parlato(d_sano, U)[0] is True)

    # ── 4 · ⛔ IL REGISTRO LETTO PRIMA CHE LE SESSIONI SCRIVESSERO ──────────
    testo_v, _vv = fabbrica(U, secondi=1, avvio=False)
    righe_v, _o, _i, _t3 = leggi(testo_v)
    d_v = misura(righe_v, Mappe(U).impara(righe_v))
    p = p_ha_misurato(d_v)
    caso("4 guasto · finestra quasi vuota ⇒ «non ho misurato», non «0 %»",
         "None", str(p[0]), p[0] is None and d_v is None)
    caso("4 risanato · finestra piena ⇒ misura", "True",
         str(p_ha_misurato(d_sano)[0]), p_ha_misurato(d_sano)[0] is True)

    # ── 5 · ⛔ IL CAMPIONE PRESO ALL'AVVIO INVECE CHE A REGIME ──────────────
    #    ⚠ E la trappola si VEDE: la quota all'avvio e' molto migliore.
    testo_a, _va = fabbrica(U, secondi=6)
    righe_a, _o, _i, _t4 = leggi(testo_a)
    m_a = Mappe(U).impara(righe_a)
    avvio_ms = righe_a[0].ms
    p = p_a_regime(righe_a, avvio_ms)
    caso("5 guasto · finestra sull'avvio ⇒ ROSSO", "False", str(p[0]),
         p[0] is False)
    p2 = p_a_regime(righe, righe[0].ms - int(ASSESTAMENTO_S * 1000) - 1000)
    caso("5 risanato · finestra a regime ⇒ vero", "True", str(p2[0]),
         p2[0] is True)
    d_a = misura(righe_a, m_a)
    caso("5-bis · e all'avvio la quota e' FALSA IN MEGLIO",
         "avvio>regime",
         "%0.1f %% > %0.1f %%" % (100 * (d_a["quota"] if d_a else 0),
                                  100 * d_sano["quota"]),
         bool(d_a) and d_a["quota"] > d_sano["quota"])

    # ── 6 · ⛔ RIGHE INTRECCIATE INNESTATE APPOSTA ⇒ IL RIVELATORE LE TROVA ─
    sano_i = intrecci(testo)
    rr = testo.rstrip("\n").split("\n")
    #    (a) l'intreccio vero: due righe fisiche, una innestata e una orfana
    rr = _intreccia(rr, 10, 60)
    rr = _intreccia(rr, 40, 30)
    #    (b) una riga che supera il buffer e viene troncata da `registro.c`
    rr[60] = rr[60][:24] + ("x" * (PIPE_BUF - 30)) + "..."
    guasto_i = intrecci("\n".join(rr))
    p = p_rivelatore_intrecci(sano_i, guasto_i)
    caso("6 guasto · intrecci innestati ⇒ il rivelatore li TROVA",
         "trovati>0", "%d orfane + %d innestate + %d troncate"
         % (guasto_i["orfane"], guasto_i["innestate"], guasto_i["troncate"]),
         p[0] is True and guasto_i["orfane"] >= 1 and guasto_i["innestate"] >= 1
         and guasto_i["troncate"] >= 1)
    caso("6 risanato · sul registro sano non ne inventa",
         "0", "%d orfane + %d innestate"
         % (sano_i["orfane"], sano_i["innestate"]),
         sano_i["orfane"] == 0 and sano_i["innestate"] == 0)
    #    ⛔ E il controllo che vale piu' di tutti: un rivelatore CIECO
    #       dev'essere smascherato dal predicato, non passare per buono.
    p_cieco = p_rivelatore_intrecci(sano_i, {"orfane": 0, "innestate": 0})
    caso("6-bis guasto · rivelatore CIECO ⇒ il predicato lo dice",
         "False", str(p_cieco[0]), p_cieco[0] is False)

    # ── 7 · ⭐ LA DIAGNOSI CIECA — il difetto vero, su verita' nota ─────────
    vittima = U[1]
    #    ⚠ La fetta e' TUTTA dopo il guasto — come nel giro vero, dove la
    #      finestra si apre due secondi dopo che la scena e' stata spenta.
    testo_f, ver_f = fabbrica(U, secondi=40, frizzo=vittima, avvio=False)
    righe_f, _o, _i, _t5 = leggi(testo_f)
    #    ⛔ E le mappe le impara dal registro INTERO (l'avvio compreso): e' quel
    #       che ha in mano chi diagnostica.  Il ponte c'e'; ⭐ e non basta lo
    #       stesso, ed e' il punto.
    testo_tutto, _vt = fabbrica(U, secondi=40, frizzo=vittima)
    r_tutto, _o, _i, _t6 = leggi(testo_tutto)
    m_f = Mappe(U).impara(r_tutto)
    nome_p, vive_p, ferme_p, perche_p = diagnosi_cieca(righe_f, m_f, "prudente")
    caso("7 · nella fetta si VEDE che una serie si e' fermata",
         "1 ferma su 4", "%d ferme su %d" % (ferme_p, vive_p),
         ferme_p == 1 and vive_p == len(U))
    caso("7-bis ⛔ ma NON si sa di chi: il prudente non da' nessun nome",
         "None", str(nome_p), nome_p is None)
    nome_v, _v2, _f2, _p2 = diagnosi_cieca(righe_f, m_f, "vicinanza")
    caso("7-ter · e chi indovina da' un nome (giusto o sbagliato che sia)",
         "un nome", str(nome_v), nome_v is not None)
    #    ⭐⭐ RISANATO — e il risanamento e' **il rimedio proposto**, provato su
    #        un registro finto: la stessa scena, con `[utente]` in testa a ogni
    #        riga di sessione (cioe' quel che farebbero `gancio_registra` e il
    #        formato di `registro.c`).  ⇒ La diagnosi si chiude.
    testo_c, _vc = fabbrica(U, secondi=40, frizzo=vittima, avvio=False,
                            con_cura=True)
    righe_c, _o, _i, _t7 = leggi(testo_c)
    nome_c, _v3, _f3, _p3 = diagnosi_cieca(righe_c, Mappe(U).impara(righe_c),
                                           "prudente")
    caso("7-quater risanato · col rimedio «[utente]» in testa, il nome ESCE",
         vittima, str(nome_c), nome_c == vittima)
    #    ⭐ E quanto costa il rimedio, misurato sulle stesse righe.
    b_senza = len(testo_f.encode("utf-8")) / max(1, len(righe_f))
    b_con = len(testo_c.encode("utf-8")) / max(1, len(righe_c))
    caso("7-quinquies · e il rimedio costa poco (byte per riga)",
         "<+15 %", "%0.1f → %0.1f byte (+%0.1f %%)"
         % (b_senza, b_con, 100 * (b_con - b_senza) / b_senza),
         (b_con - b_senza) / b_senza < 0.15)
    #    ⛔⛔ E IL PREDICATO DELLA CURA, CERTIFICATO SUI DUE ESTREMI NOTI — 25
    #        agosto 2026.  ⭐ Il registro **senza** rimedio e' il guasto, quello
    #        **col** rimedio e' il sano, e sono gli stessi due testi di 7-bis e
    #        7-quater: cosi' il predicato nuovo non porta con se' una fabbrica
    #        sua da tarare a parte.
    def _prova(righe_x, mm):
        n, _v, f, _p = diagnosi_cieca(righe_x, mm, "prudente")
        return [{"vero": vittima, "nome": n, "ferme": f}]
    mis_finta = misura(righe_c, Mappe(U).impara(righe_c))
    p_g = p_la_cura_regge(_prova(righe_f, m_f), mis_finta)
    caso("7-sexies guasto · senza rimedio il predicato della cura da' ROSSO",
         "False", str(p_g[0]), p_g[0] is False)
    p_s = p_la_cura_regge(_prova(righe_c, Mappe(U).impara(righe_c)), mis_finta)
    caso("7-sexies risanato · col rimedio lo stesso predicato da' VERDE",
         "True", str(p_s[0]), p_s[0] is True)
    #    ⛔ E il terzo esito, che non e' un verde educato: se il guasto non ha
    #       morso (nessuna serie ferma), il predicato NON GIUDICA.
    p_m = p_la_cura_regge([{"vero": vittima, "nome": None, "ferme": 0}],
                          mis_finta)
    caso("7-septies · guasto che non ha morso ⇒ NON GIUDICO, non verde",
         "None", str(p_m[0]), p_m[0] is None)
    #    ⛔ E il nome SBAGLIATO e' rosso quanto il muto — anzi, si dichiara
    #       peggio: manda a guardare il desktop di un altro.
    p_x = p_la_cura_regge([{"vero": vittima, "nome": U[0], "ferme": 1}],
                          mis_finta)
    caso("7-octies guasto · nome SBAGLIATO ⇒ ROSSO (non «ha detto un nome»)",
         "False", str(p_x[0]), p_x[0] is False)
    #    ⛔ E la frazione: nome giusto ma famiglie grosse ancora mute ⇒ ROSSO.
    mis_bassa = dict(mis_finta or {})
    mis_bassa["diagnosi_quota"] = 0.042        # `[M]` §6.7, il 4,2 % vero
    p_q = p_la_cura_regge([{"vero": vittima, "nome": vittima, "ferme": 1}],
                          mis_bassa)
    caso("7-nonies guasto · nome giusto ma diagnosi al 4,2 % ⇒ ROSSO lo stesso",
         "False", str(p_q[0]), p_q[0] is False)

    # ── 8 · ⛔ LA TARATURA CHE NON HA TARATO ⇒ None, non 100 % ──────────────
    t_vuota = tara(righe, [None] * len(righe), m, "prudente")
    p = p_taratura(t_vuota, "prudente", 0.0)
    caso("8 guasto · nessuna riga di provenienza nota ⇒ «non ho tarato»",
         "None", str(p[0]), t_vuota is None and p[0] is None)

    # ── 9 · ⛔ E IL METRO SI TARA ANCHE SUL NEGATIVO: righe che NON sono di
    #          nessuno non devono ricevere un nome dal prudente.
    #    ⛔ Si classifica TUTTO il registro e poi si guardano quelle righe: se
    #       si desse al classificatore la sola lista delle righe del padre, non
    #       avrebbe nessun vicino da cui copiare e «vicinanza» sembrerebbe
    #       prudente quanto il prudente.  ⚠ E' la forma D3 di `REVIEWER.md`: il
    #       guasto innestato in un mondo in cui non puo' mordere.
    dove = [i for i, v in enumerate(ver) if v is None]
    det = classifica_tutte(righe, m, "prudente")
    dati = sum(1 for i in dove if det[i][0])
    caso("9 · righe che non sono di nessuno: il prudente non le battezza",
         "0", "%d su %d" % (dati, len(dove)), dati == 0)
    det_v = classifica_tutte(righe, m, "vicinanza")
    dati_v = sum(1 for i in dove if det_v[i][0])
    caso("9-bis guasto · «vicinanza» invece le battezza",
         ">0", "%d su %d" % (dati_v, len(dove)), dati_v > 0)

    # ── 10 · ⛔⛔ IL CAMPIONE SPORCO — il rosso vero del 24 agosto 2026 ──────
    #
    #   Nella finestra «a una voce» di `chi` capitano anche righe che il PADRE
    #   ha scritto **su un'altra sessione** (`rete-quic [prov di un altro]`).
    #   ⚠ La finestra a tutti fermi e' corta e il padre e' quasi muto: quella
    #     famiglia puo' non comparirci, e allora la regola «tutto quel che il
    #     padre non sa scrivere e' di `chi`» **battezza col nome sbagliato**.
    #   ⛔ E il danno non e' un rosso qualunque: e' un rosso **sul
    #     classificatore giusto**, cioe' un metro che accusa il metro.
    # ⭐ La cura: entrano nel campione solo le righe **MUTE**.  Una riga che si
    #    nomina da se' non e' di provenienza ignota — non fa parte della domanda.
    U2 = U
    finta_padre = Riga(0, 12 * 3600000, "wt",
                       "rete-quic [192.168.0.2]:35007 da_ms=1000 persi=0 "
                       "spediti=70 cwnd=13200", "")
    finta_muta = Riga(1, 12 * 3600000 + 5, "figlio",
                      "ciclo: 40 fotogrammi consegnati (2 chiavi), 6000 attese "
                      "a vuoto, 0 guasti", "")
    m10 = Mappe(U2).impara(righe)     # il ponte c'e': 35007 e' di U2[1]
    fam_padre_corta = set()           # ⛔ la finestra corta non ha visto nulla
    chi = U2[0]
    guasta = [chi if famiglia(r.corpo) not in fam_padre_corta else None
              for r in (finta_padre, finta_muta)]
    sana = [chi if (famiglia(r.corpo) not in fam_padre_corta
                    and prudente(r, m10)[0] is None) else None
            for r in (finta_padre, finta_muta)]
    t_g = tara([finta_padre, finta_muta], guasta, m10, "prudente")
    t_s = tara([finta_padre, finta_muta], sana, m10, "prudente")
    caso("10 guasto · campione sporco ⇒ il prudente sembra SBAGLIARE",
         "sbagliate>0", "%d sbagliate su %d" % (t_g["sbagliate"],
                                                t_g["campione"]),
         t_g["sbagliate"] > 0)
    caso("10 risanato · solo le righe MUTE nel campione ⇒ zero sbagliate",
         "0 sbagliate su 1", "%d sbagliate su %d" % (t_s["sbagliate"],
                                                     t_s["campione"]),
         t_s is not None and t_s["sbagliate"] == 0 and t_s["campione"] == 1)

    ko = [e for e in esiti if not e["ok"]]
    _log("CERTIFICAZIONE: %d casi, %d falliti" % (len(esiti), len(ko)))
    for e in ko:
        _ko("%s — atteso %s, visto %s" % (e["caso"], e["atteso"], e["visto"]))
    if not ko:
        _ok("⭐ %d casi su %d: ogni predicato ha il suo guasto, e il guasto ha "
            "morso" % (len(esiti), len(esiti)))
    return 0 if not ko else 1


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL GIRO VERO
# ═══════════════════════════════════════════════════════════════════════════
def terreno(con_lucchetto):
    """⛔ `banchi/10-b0-terreno.sh` PRIMA di misurare, e poi quel che e' mio.

    ⚠ Non se ne riscrive una riga: 21 predicati, `[M]` 30 guasti su 30 lo fanno
      mordere.  ⭐ E i tre esiti sono tre: `0` regge · `1` non regge · **`2` non
      ho potuto verificare** — e il 2 non e' un verde.
    """
    _log("IL TERRENO — porta %d · %d sessioni · albero %s"
         % (PORTA, QUANTI, ALB))
    # ⚠ GLI ALTRI AGENTI DEL GIRO 2 HANNO I LORO SERVER ACCESI, e il controllo
    #   del terreno pretende che si DICHIARINO invece di tacerli.  ⇒ Si leggono
    #   dalla macchina e si stampano, uno per uno: ⛔ dichiararli non vuol dire
    #   che non contino — vuol dire che li ho visti.
    #   ⭐ Il carico di GPU degli altri, quello si', e' escluso dal lucchetto:
    #     e' per quello che il lucchetto esiste.
    rc, out, _ = root("ss -uln | grep -oE ':8[0-9]{3} ' | tr -d ': ' | sort -u")
    altre = [p for p in out.split() if p.isdigit() and int(p) != PORTA]
    if altre:
        _dub("⚠ ALTRI SERVER ACCESI sulla macchina, e li DICHIARO: %s.  Il "
             "registro che misuro e' il MIO (%s), e la GPU la protegge il "
             "lucchetto" % (" ".join(altre), REGISTRO))
    amb = dict(os.environ)
    amb.update({"CHI": IO_SONO, "PORTA": str(PORTA), "UTENTE": SESSIONI[0][0],
                "ALBERO": ALB, "LAV": LAV, "LUCCHETTO": LUCCHETTO,
                "PORTE_AMMESSE": " ".join(altre),
                "LUCCHETTO_MIO": "1" if con_lucchetto else "0"})
    import subprocess
    p = subprocess.run(["bash", os.path.join(QUI, "10-b0-terreno.sh")],
                       env=amb, capture_output=True)
    coda = p.stdout.decode("utf-8", "replace").splitlines()
    # ⛔⛔ SI STAMPA QUAL E' IL PREDICATO CADUTO, NON SOLO IL CONTO — 25 ago 2026.
    #     Qui c'erano le ultime 14 righe e basta: `10-b0-terreno.sh` mette il
    #     conto in coda e i NO in mezzo, ⇒ chi leggeva vedeva «1 guai» senza
    #     sapere QUALE, e per scoprirlo bisognava rigirare il terreno a mano —
    #     cioe' in un altro istante, quando magari il guaio non c'era piu'.
    #     ⚠ E' la forma «silenzio invece di rosso» un piano piu' su (§7.3): il
    #     banco sapeva e non l'ha detto.  ⭐ Adesso i NO si stampano TUTTI.
    for r in coda:
        if "NO\033[0m" in r or "IL TERRENO NON REGGE" in r:
            print("    |⛔" + r)
    for r in coda[-14:]:
        print("    | " + r)
    if p.returncode == 2:
        _dub("⛔ 10-b0-terreno esce 2: NON HO POTUTO VERIFICARE il terreno")
        return False
    if p.returncode != 0:
        _ko("⛔ 10-b0-terreno esce %d: il terreno non regge" % p.returncode)
        return False
    _ok("10-b0-terreno: il terreno della fase regge")
    guai = []
    rc, out, _ = root("ss -uln | grep -c ':%d ' || true" % PORTA)
    if out.strip() == "0":
        guai.append("nessuno ascolta sulla %d: «bash banchi/10-b96-terreno.sh "
                    "accendi»" % PORTA)
    rc, out, _ = root("test -s %s/parola && echo si || echo no" % LAV)
    if "si" not in out:
        guai.append("manca %s/parola (0600): D12 vieta la parola in argv" % LAV)
    rc, out, _ = root("test -x %s && echo si || echo no" % SCENA_BIN)
    if "si" not in out:
        guai.append("la scena «%s» non e' eseguibile" % SCENA_BIN)
    if not B.spedisci(B.CLIENTE, "10-b92-cliente.py"):
        guai.append("«10-b92-cliente.py» non si e' scritto in %s" % LAV)
    # ⛔⛔ IL PALCO ORFANO — in fase 9 non dava rosso: dava UN NUMERO PLAUSIBILE.
    PALCO = "gnome-shell|gnome-session|mutter|Xwayland|04-b30-scena|remotix"
    orfani = []
    for i, (u, n, _m, _d) in enumerate(SESSIONI, 1):
        rc, out, _ = root("pgrep -u %d -a 2>/dev/null | grep -E '%s' || true"
                          % (n, PALCO))
        righe = [x.strip() for x in out.splitlines() if x.strip()]
        if righe:
            orfani.append("%s (uid %d): %d processi del PALCO — %s"
                          % (u, n, len(righe),
                             " / ".join(x[:60] for x in righe[:3])))
    if orfani:
        guai.append("⛔⛔ PALCO ORFANO del giro precedente:\n        "
                    + "\n        ".join(orfani)
                    + "\n        ⇒ «bash banchi/10-b96-terreno.sh sgombra»")
    for g in guai:
        _ko(g)
    if not guai:
        _ok("il terreno c'e', ed e' mio: nessun palco orfano, il cliente e' "
            "sulla macchina")
    return not guai


def apri_tutte(resta_s):
    _log("LE %d SESSIONI — utenti diversi, scene DIVERSE" % QUANTI)
    _inf("⚠ quattro scene uguali darebbero quattro serie di contatori che si "
         "somigliano, e «continuita» sembrerebbe migliore per un caso fortunato")
    aperte, avvio_ms = [], None
    for i, (u, n, mv, dn) in enumerate(SESSIONI, 1):
        t0 = time.time()
        ok, detto = B.apri_sessione(i, resta_s)
        if not ok:
            _ko("s%d (%s): %s" % (i, u, detto))
            return aperte, None
        usc = accendi_scena_mia(i)
        _ok("s%d (%s) aperta in %d ms · scena «%s» movimento=%s danno=%s"
            % (i, u, int(1000 * (time.time() - t0)), usc, mv, dn))
        if not usc:
            _dub("⚠ s%d NON disegna: e' un desktop fermo contato come una "
                 "sessione al lavoro (`LEZIONI.md` §1.30).  Lo dichiaro" % i)
        aperte.append(i)
    return aperte, time.time()


def giro(a):
    esiti = {"quanti": QUANTI, "durata_s": a.durata,
             "sessioni": [{"utente": u, "uid": n, "movimento": mv, "danno": dn}
                          for u, n, mv, dn in SESSIONI]}
    rossi, muti = [], []
    U = [u for u, _n, _m, _d in SESSIONI]

    aperte, t_aperte = apri_tutte(a.durata * 6 + 900)
    if len(aperte) < QUANTI:
        _ko("⛔ non tutte le sessioni si sono aperte: NON misuro")
        return esiti, ["le sessioni non si sono aperte"], muti
    # ⭐ La marca dell'ultima apertura, letta DAL REGISTRO e non dal portatile:
    #    e' l'orologio con cui `p_a_regime` giudica, e dev'essere lo stesso
    #    delle righe.
    avvio_ms = ultima_marca()
    esiti["avvio_ms"] = avvio_ms
    _inf("⚠ assestamento dichiarato: %0.0f s (`CODER.md` §3.5 — il campione si "
         "prende a REGIME)" % ASSESTAMENTO_S)
    time.sleep(ASSESTAMENTO_S)
    pid_di = figli_pid()
    _inf("i figli, CHIESTI AL NUCLEO (⚠ verita' del banco, non del "
         "classificatore): %s" % " ".join("%s=%s" % (u, p)
                                          for u, p in pid_di.items()))
    esiti["figli_pid"] = pid_di
    pid_completi = all(p for p in pid_di.values())
    if not pid_completi:
        muti.append("⛔ non conosco il figlio di TUTTE le sessioni: la taratura "
                    "viva NON si fa.  ⚠ Fermarne tre su quattro darebbe una "
                    "finestra «a una voce» con due voci, e la verita' del "
                    "campione sarebbe falsa — un campione sporco taratura non e'")

    # ═══════════════════════════════════════════════════════════════════════
    _log("1 · ⛔ LA TARATURA — provenienza NOTA iniettata, e DUE errori misurati")
    _inf("⛔ la verita' viene da FUORI dal registro: si ferma ogni figlio "
         "tranne uno, e per quei secondi le righe dei figli sono di quell'uno")
    testo0 = a_una_voce(pid_di, a.taratura, chi=None) if pid_completi else None
    if testo0 is None:
        muti.append("⛔ NON HO TARATO: la finestra a tutti fermi non si e' letta")
        fam_padre = None
    else:
        r0, _o, _i, _t = leggi(testo0)
        fam_padre = set(famiglia(r.corpo) for r in r0)
        _ok("finestra a TUTTI I FIGLI FERMI: %d righe · ⭐ %d famiglie che "
            "sa scrivere il PADRE (misurate, non supposte)"
            % (len(r0), len(fam_padre)))
        aree_padre = sorted(set(r.area for r in r0))
        _inf("aree del padre: %s" % " ".join(aree_padre))
        esiti["famiglie_del_padre"] = len(fam_padre)
        esiti["aree_del_padre"] = aree_padre

    # ⛔⛔ LE MAPPE PRIMA DELLA TARATURA, e lette da TUTTO il registro: sono
    #     quel che ha in mano chi diagnostica (il registro intero), e servono
    #     gia' dentro la taratura per riconoscere le righe che si nominano da
    #     se' — quelle NON entrano nel campione (vedi il riquadro qui sotto).
    tutto0 = fetta(0, punto())
    m_ponte = Mappe(U)
    if tutto0:
        r_tutto, _o, _i, _t = leggi(tutto0)
        m_ponte = Mappe(U).impara(r_tutto)
        _inf("le mappe del classificatore, LETTE DAL REGISTRO: %d provenienze, "
             "%d uid, %d pid (da %d righe di ponte)"
             % (len(m_ponte.prov), len(m_ponte.uid), len(m_ponte.pid),
                m_ponte.righe_ponte))
        esiti["mappe"] = {"prov": len(m_ponte.prov), "uid": len(m_ponte.uid),
                          "pid": len(m_ponte.pid),
                          "righe_ponte": m_ponte.righe_ponte}
    else:
        muti.append("⛔ NON HO LETTO il registro intero: le mappe del "
                    "classificatore sono vuote")

    righe_tara, verita = [], []
    caduta = None
    if fam_padre is not None:
        for i, (u, _n, _m, _d) in enumerate(SESSIONI, 1):
            # ⛔ SI GUARDA PRIMA, NON SOLO DOPO: se una sessione e' gia' caduta
            #    nella finestra precedente, questa finestra non ha «una voce» —
            #    ne ha zero per quella, e il campione sarebbe di una
            #    popolazione diversa da quella dichiarata.
            morte = [j for j in range(1, QUANTI + 1) if not B.vivo(j)]
            if morte:
                caduta = ("⛔ prima della finestra di s%d erano gia' cadute %d "
                          "sessioni (%s): FERMO la taratura invece di "
                          "raccogliere un campione sporco"
                          % (i, len(morte),
                             " ".join(SESSIONI[j - 1][0] for j in morte)))
                _ko(caduta)
                break
            testo_k = a_una_voce(pid_di, a.taratura, chi=u)
            if testo_k is None:
                continue
            rk, _o, _i2, _t2 = leggi(testo_k)
            # ⛔ Verita' per COSTRUZIONE: in questa finestra un figlio solo era
            #    vivo ⇒ le righe di famiglie che il padre NON sa scrivere sono
            #    sue.  ⚠ Le altre restano fuori dal campione: un campione
            #    sporco taratura non e'.
            # ⛔ Le righe entrano TUTTE (il classificatore dev'essere nella
            #    condizione di chi legge il registro), ma la verita' e' `None`
            #    dove non la so: un campione sporco taratura non e'.
            #
            # ⛔⛔ E LA SECONDA CONDIZIONE E' COSTATA UN ROSSO VERO — `[M]` 24
            #     agosto 2026, giro delle 20:19.  La prima stesura diceva «tutto
            #     quel che il padre non sa scrivere e' di `chi`», e prendeva la
            #     lista delle famiglie del padre dalla finestra a tutti fermi.
            #     ⚠ Quella finestra pero' e' CORTA (1,5 s) e col padre quasi
            #       muto: `[M]` **6 righe, UNA famiglia**.  ⇒ `rete-quic`, che e'
            #       del padre, non ci compariva, e tre righe `rete-quic` di ALTRE
            #       sessioni sono finite nel campione col nome di `chi`.
            #     ⛔ Il banco ha dato ROSSO — «il prudente sbaglia lo 0,3 %» — e
            #       il rosso era **del campione, non del classificatore**: quelle
            #       righe portano scritta dentro la provenienza di un'altra
            #       sessione, e il classificatore le leggeva giuste.
            # ⭐ La cura non e' allungare la finestra (allungarla uccide le
            #    sessioni: vedi `a_una_voce`).  E' restringere la DOMANDA: la
            #    finestra a una voce dice di chi sono le righe **MUTE**, non
            #    quelle che portano gia' un identificatore dentro.  Una riga che
            #    si nomina da se' non e' «di provenienza ignota» — non fa parte
            #    della domanda.
            # ⇒ Verita' = famiglia che il padre non sa scrivere **E** riga che
            #   nessun identificatore ancorato nomina.
            sue = [u if (famiglia(r.corpo) not in fam_padre
                         and prudente(r, m_ponte)[0] is None) else None
                   for r in rk]
            righe_tara += rk
            verita += sue
            _inf("s%d «%s» a una voce: %d righe, di cui %d SUE per costruzione "
                 "(⚠ le altre le sa scrivere anche il padre: fuori dal campione)"
                 % (i, u, len(rk), sum(1 for x in sue if x)))

    # ⛔⛔ E SUBITO DOPO SI GUARDA SE LE SESSIONI SONO ANCORA VIVE.
    #
    #     Fermare un figlio e' un gesto che il prodotto puo' prendere per un
    #     silenzio, e la linea morta chiude una sessione a 10 s.  ⚠ Se il banco
    #     ne avesse persa una e non guardasse, misurerebbe **tre** sessioni
    #     chiamandole quattro — e non darebbe rosso: darebbe un numero
    #     plausibile e piu' bello del vero.
    morte = [i for i in range(1, QUANTI + 1) if not B.vivo(i)]
    if caduta:
        rossi.append(caduta)
    if morte:
        r = ("⛔ la taratura ha lasciato per strada %d sessioni su %d (%s): la "
             "finestra di regime NON avrebbe quattro voci"
             % (len(morte), QUANTI,
                " ".join(SESSIONI[i - 1][0] for i in morte)))
        _ko(r); rossi.append(r)
    else:
        _ok("dopo la taratura tutte e %d le sessioni sono ancora vive "
            "(⚠ il fermo dura %0.1f s: 3,3 volte sotto i 5 000 ms dello stallo "
            "della linea morta, che con 5 s le aveva uccise tutte)"
            % (QUANTI, a.taratura))

    m_tara = m_ponte
    esiti["taratura"] = {}
    for quale, tetto in (("prudente", 0.0), ("vicinanza", 0.0),
                         ("continuita", 0.0)):
        t = tara(righe_tara, verita, m_tara, quale)
        esiti["taratura"][quale] = t
        passa, perche = p_taratura(t, quale, tetto)
        if quale == "prudente":
            (_ok if passa else _ko if passa is False else _dub)(perche)
            if passa is False:
                rossi.append(perche)
            if passa is None:
                muti.append(perche)
        else:
            # ⭐ Per i due che INDOVINANO il rosso e' l'ATTESO: si misura e si
            #    dichiara, non si nasconde.  Il rosso di questi due non e' un
            #    rosso del banco: e' il numero che l'incarico chiede.
            if t:
                _dub("⭐ «%s» (quello che INDOVINA): %0.1f %% giuste, ⛔ %0.1f "
                     "%% SBAGLIATE, %0.1f %% astenute su %d righe"
                     % (quale, 100 * t["q_giuste"], 100 * t["q_sbagliate"],
                        100 * t["q_astenute"], t["campione"]))
                for e in t["esempi_sbagliate"][:2]:
                    _inf("    e sbaglia cosi': %s" % e)
            else:
                _dub("⛔ «%s» NON tarato" % quale)
    _dub("⚠ E QUEI DUE NUMERI VANNO LETTI CON LA FINESTRA IN MANO: in una "
         "finestra «a una voce» c'e' UNA VOCE SOLA da cui copiare, quindi "
         "l'euristica del vicino ci prende per costruzione.  ⇒ La sua prova "
         "vera e' sulla finestra di REGIME, qui sotto")

    # ═══════════════════════════════════════════════════════════════════════
    _log("2 · LA MISURA — %0.0f s con %d sessioni vive, a regime"
         % (a.durata, QUANTI))
    assicura_scene()
    aa = punto()
    time.sleep(a.durata)
    bb = punto()
    testo = fetta(aa, bb)
    if testo is None:
        muti.append("⛔ NON HO MISURATO: la fetta di regime non si e' letta")
        return esiti, rossi, muti
    righe, orfane, innestate, troncate = leggi(testo)
    passa, perche = p_a_regime(righe, avvio_ms)
    (_ok if passa else _ko if passa is False else _dub)(perche)
    if passa is False:
        rossi.append(perche)
    d = misura(righe, m_tara, "prudente")
    passa, perche = p_ha_misurato(d)
    if passa is None:
        _dub(perche); muti.append(perche)
        return esiti, rossi, muti
    _ok(perche)
    passa, perche = p_tutte_hanno_parlato(d, U)
    (_ok if passa else _ko if passa is False else _dub)(perche)
    if passa is False:
        rossi.append(perche)
    esiti["misura"] = d
    _inf("⭐⭐ LA FRAZIONE: %d righe in %0.1f s · attribuite %d ⇒ **%0.1f %%** "
         "· ⭐ righe AMBIGUE (due identificatori discordi): %d"
         % (d["righe"], (d["durata_ms"] or 0) / 1000.0, d["attribuite"],
            100 * d["quota"], d["ambigue"]))
    if d["diagnosi_quota"] is None:
        _dub("⛔ nessuna riga DI DIAGNOSI nella finestra: non giudico quella "
             "frazione")
        muti.append("frazione di diagnosi non misurata")
    else:
        _inf("⭐⭐ E QUELLA CHE CONTA — righe DI DIAGNOSI: %d, attribuite %d ⇒ "
             "**%0.1f %%**" % (d["diagnosi_righe"], d["diagnosi_attribuite"],
                               100 * d["diagnosi_quota"]))
    for nome in sorted(d["per_diagnosi"], key=lambda x: -d["per_diagnosi"][x]["n"]):
        v = d["per_diagnosi"][nome]
        _inf("    %-18s %5d righe · attribuite %5d (%5.1f %%)"
             % (nome, v["n"], v["attr"], 100 * v["attr"] / v["n"]))
    # ⭐⭐ LA PROVA VERA DELL'EURISTICA — sulle righe intrecciate, col nome
    #     nascosto.  ⛔ E' il numero che l'incarico chiede: quante ne
    #     attribuisce MALE chi indovina invece di astenersi.
    tv = tara_su_regime(righe, m_tara)
    esiti["vicinanza_a_regime"] = tv
    if tv is None:
        _dub("⛔ NON HO TARATO «vicinanza» sul regime: meno di 20 righe con un "
             "identificatore in questa finestra")
        muti.append("«vicinanza» non tarata sul regime")
    else:
        _dub("⭐⭐ «vicinanza» SULLE RIGHE INTRECCIATE (nome nascosto, %d righe "
             "di verita' provata): %0.1f %% giuste, ⛔ **%0.1f %% SBAGLIATE**, "
             "%0.1f %% astenute" % (tv["campione"], 100 * tv["q_giuste"],
                                    100 * tv["q_sbagliate"],
                                    100 * tv["q_astenute"]))
        for e in tv["esempi_sbagliate"][:2]:
            _inf("    e sbaglia cosi': %s" % e)
        _inf("⇒ ⭐ il prudente su quelle stesse righe si sarebbe astenuto: "
             "0,0 % sbagliate.  ⛔ Un classificatore che indovina e' PEGGIO "
             "di uno che si astiene, e questo e' di quanto")

    peggiori = sorted(d["per_famiglia"].items(),
                      key=lambda kv: (kv[1]["attr"] / kv[1]["n"], -kv[1]["n"]))
    _inf("le famiglie piu' MUTE (area · quante · quota):")
    for f, v in peggiori[:10]:
        if v["n"] >= 3:
            _inf("    %-7s %5d  %5.1f %%  %s"
                 % (v["area"], v["n"], 100 * v["attr"] / v["n"], f[:74]))

    # ═══════════════════════════════════════════════════════════════════════
    _log("3 · ⚠ L'ALTRA META' — le righe SPEZZATE o MESCOLATE")
    inv = intrecci(testo)
    esiti["intrecci"] = inv
    _inf("righe buone %d · orfane %d · innestate %d · troncate %d"
         % (inv["righe_buone"], inv["orfane"], inv["innestate"],
            inv["troncate"]))
    _inf("riga piu' lunga %s byte · sopra %d byte: %d righe (`PIPE_BUF` e' %d)"
         % (inv["riga_piu_lunga_byte"], LUNGA,
            inv["lunghe_oltre_%d" % LUNGA], PIPE_BUF))
    for e in inv["esempi_orfane"][:2]:
        _dub("orfana: %s" % e)
    for e in inv["esempi_innestate"][:2]:
        _dub("innestata: %s" % e)
    # ⭐ E la stessa caccia su TUTTO il registro, non sulla sola finestra: gli
    #    intrecci sono rari, e uno «zero» su un campione piccolo somiglia in
    #    tutto allo zero di un fatto.
    sc = scansione_intera(REGISTRO)
    esiti["scansione_intera"] = sc
    if not sc["scansione_credibile"]:
        r = ("⛔ la scansione dell'intero registro NON e' credibile (%s righe "
             "buone su %s): NON riferisco il suo conto"
             % (sc["righe_buone"], sc["righe_in_tutto"]))
        _dub(r); muti.append(r)
    _inf("⭐ su TUTTO il mio registro (%s righe): %s ORFANE + %s INNESTATE "
         "(%s senza marca, di cui %s di TERZI) · %s in «...» · piu' lunga %s "
         "byte · sopra %d byte: %s"
         % (sc["righe_in_tutto"], sc["orfane"], sc["innestate"],
            sc["senza_marca"], sc["estranee"], sc["finiscono_in_puntini"],
            sc["riga_piu_lunga"], LUNGA, sc["lunghe_oltre_%d" % LUNGA]))
    # ⛔ E il rivelatore si TARA QUI, sul registro vero: si innestano intrecci
    #    dentro questa stessa fetta e si guarda se li trova.  Senza, il suo
    #    «zero» non varrebbe niente.
    rr = testo.rstrip("\n").split("\n")
    if len(rr) > 80:
        # ⛔ LO STESSO INNESTO DELLA CERTIFICAZIONE, e sul registro VERO: due
        #    righe fisiche per ogni intreccio (una innestata, una orfana), piu'
        #    una riga oltre il buffer.  ⚠ Se qui non li trovasse, il suo «zero»
        #    di poche righe sopra non varrebbe niente.
        rr = _intreccia(rr, 10, 60)
        rr = _intreccia(rr, 40, 30)
        rr[70] = rr[70][:24] + ("x" * (PIPE_BUF - 30)) + "..."
        inv_g = intrecci("\n".join(rr))
        passa, perche = p_rivelatore_intrecci(inv, inv_g)
        (_ok if passa else _ko if passa is False else _dub)(perche)
        if passa is False:
            rossi.append(perche)
        esiti["intrecci_tarato_su"] = {"orfane": inv_g["orfane"],
                                       "innestate": inv_g["innestate"],
                                       "troncate": inv_g["troncate"]}

    # ═══════════════════════════════════════════════════════════════════════
    _log("4 · ⭐⭐ LA PROVA CIECA — «quale sessione ha smesso di consegnare?»")
    prove = []
    for i, (u, n, mv, dn) in enumerate(SESSIONI, 1):
        if i > a.prove:
            break
        _inf("prova %d/%d · spengo la scena di s%d («%s») — il registro NON lo "
             "sa" % (i, min(a.prove, QUANTI), i, u))
        root("pkill -u %d -f 04-b30-scena; true" % n)
        # ⛔ DIECI SECONDI PRIMA DI GUARDARE, e non e' prudenza — `[M]` 24 ago
        #    2026: con **due** secondi la serie del colpevole cresceva ancora e
        #    il banco diceva «0 serie ferme», cioe' **il guasto non aveva
        #    morso** (`LEZIONI.md` §1.30).  Spenta la scena, il compositore
        #    consegna ancora per qualche secondo quel che aveva in canna: prima
        #    di misurare bisogna che si sia fermato davvero.
        time.sleep(10)
        aa = punto(); time.sleep(a.cieca); bb = punto()
        tc = fetta(aa, bb)
        riacceso = accendi_scena_mia(i)
        if tc is None:
            _dub("⛔ la fetta della prova %d non si e' letta: NON giudico" % i)
            continue
        rc_, _o, _i2, _t2 = leggi(tc)
        riga = {"vero": u, "righe": len(rc_)}
        for quale in ("prudente", "vicinanza", "continuita"):
            nome, vive, ferme, perche = diagnosi_cieca(rc_, m_tara, quale)
            riga[quale] = {"nome": nome, "vive": vive, "ferme": ferme,
                           "perche": perche}
        riga["ferme"] = riga["prudente"]["ferme"]
        riga["nome"] = riga["prudente"]["nome"]
        prove.append(riga)
        _inf("    prudente: %s (%s) · vicinanza: %s · continuita: %s"
             % (riga["prudente"]["nome"], riga["prudente"]["perche"],
                riga["vicinanza"]["nome"], riga["continuita"]["nome"]))
        if not riacceso:
            _dub("⚠ la scena di s%d non si e' riaccesa: le prove dopo hanno un "
                 "carico diverso, e lo dichiaro" % i)
        time.sleep(4)
    esiti["prova_cieca"] = prove
    passa, perche = p_diagnosi_cieca(prove)
    (_ok if passa else _ko if passa is False else _dub)(perche)
    if passa is None:
        muti.append(perche)
    # ⭐⭐ E IL PREDICATO DELLA CURA — quello che sa dare ROSSO, dal 25 ago 2026.
    #    ⚠ Sul binario col difetto questo predicato DEVE essere rosso: e' il
    #      «rosso prima» che il terzo giro della fase 10 pretende.
    passa2, perche2 = p_la_cura_regge(prove, esiti.get("misura"))
    (_ok if passa2 else _ko if passa2 is False else _dub)(perche2)
    if passa2 is False:
        rossi.append(perche2)
    elif passa2 is None:
        muti.append(perche2)
    for quale in ("prudente", "vicinanza", "continuita"):
        dati = [p for p in prove if p[quale]["nome"]]
        giusti = [p for p in dati if p[quale]["nome"] == p["vero"]]
        _inf("    «%-11s» ha dato un nome %d volte su %d, giusto %d volte"
             % (quale, len(dati), len(prove), len(giusti)))

    # ═══════════════════════════════════════════════════════════════════════
    _log("5 · ⭐ CHE COSA BASTEREBBE — verificato sul sorgente, e quanto costa")
    cura = disegno_cura(d, a.durata, QUANTI)
    esiti["cura"] = cura
    for v in cura["verifiche"]:
        (_ok if v["regge"] else _ko)("%s → %s" % (v["che"], v["visto"][:120]))
    _inf("⭐ chiamate al registro per file (dai sorgenti SPEDITI): %s"
         % cura.get("chiamate_per_file", "?"))
    _inf("⇒ ⭐ le scrive il PADRE: rcp.c + webtransport.c (un processo per "
         "TUTTE le sessioni) · le scrivono i FIGLI: figlio.c (meta') + "
         "codificatore.c + audio.c + sessione.c (un processo A TESTA)")
    c = cura["costo"]
    if c:
        _inf("`[M]` il registro fa %s righe/s con %d sessioni (%s righe/s per "
             "sessione), %s byte per riga, %s byte/s"
             % (c["righe_al_secondo"], QUANTI,
                c["righe_al_secondo_per_sessione"], c["byte_per_riga"],
                c["byte_al_secondo"]))
        _inf("`[?]` il pid nel formato costerebbe +%d byte/riga = +%s %% · il "
             "nome utente +%s byte/riga = +%s %% · tutt'e due +%s %%"
             % (c["pid_byte_per_riga"], c["pid_crescita_pct"],
                c["utente_byte_per_riga"], c["utente_crescita_pct"],
                c["tutt_e_due_crescita_pct"]))
        _inf("`[?]` a 10 sessioni: %s byte/s col rimedio addosso (oggi sarebbe "
             "%s)" % (c["previsione_a_10_sessioni_byte_s"],
                      round(c["righe_al_secondo"] / QUANTI * 10
                            * c["byte_per_riga"])))
    return esiti, rossi, muti


def principale():
    global B
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--durata", type=float, default=120.0,
                   help="la finestra di regime, in secondi")
    # ⛔⛔ CINQUE SECONDI, E IL NUMERO E' UNA CURA, NON UNA COMODITA'.
    #
    #     La finestra «a una voce» tiene i figli in `SIGSTOP`, e per quei secondi
    #     dalle sessioni fermate **non esce niente**.  ⚠ E' esattamente la scena
    #     del difetto trovato dal primo giro (`fasi/10-…md` §S.4).  ⛔ E NON E'
    #     UN TIMORE: `[M]` 24 agosto 2026, con **5 s** di fermo tutte e quattro
    #     le sessioni sono morte di `linea-morta causa=stallo stallo_ms=5000
    #     usciti_byte=0 coda_video=8862 persi=0`.  ⇒ 1,5 s sta 3,3 volte sotto
    #     la soglia dello stallo, ed e' il numero che regge.
    # ⚠ Il prezzo si dichiara: il campione della taratura e' piccolo, e si
    #   STAMPA quanto e' (`LEZIONI.md` §1.30 — quanta sollecitazione e'
    #   ARRIVATA).  ⛔ E allungarlo non e' gratis: e' rompere le sessioni.
    p.add_argument("--taratura", type=float, default=1.5,
                   help="ogni finestra «a una voce», in secondi")
    p.add_argument("--cieca", type=float, default=30.0,
                   help="ogni prova cieca, in secondi")
    p.add_argument("--prove", type=int, default=4,
                   help="quante prove cieche (una per sessione)")
    p.add_argument("--senza-lucchetto", action="store_true")
    # ⭐ IL LUCCHETTO PRESO DA FUORI, e non e' una comodita': `prendi()` non e'
    #    rientrante (e' un `mkdir`), quindi un banco che gira DUE volte dentro
    #    lo stesso turno — la messa a punto e poi la misura — non puo'
    #    riprenderlo.  ⛔ E qui non si finge: si VERIFICA che sia mio, e se non
    #    lo e' ci si ferma.  ⚠ E non lo si molla: e' di chi l'ha preso.
    p.add_argument("--lucchetto-esterno", action="store_true")
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--analizza", default=None,
                   help="⭐ misura un registro GIA' SCRITTO (percorso sulla "
                        "macchina di prova) invece di farne uno")
    p.add_argument("--mega", type=float, default=8.0,
                   help="quanti MB di CODA leggere con --analizza")
    # ⭐⭐ IL CONTROLLO POSITIVO DEL RIVELATORE DEGLI INTRECCI, e non e' un
    #     extra: sulla macchina di prova ci sono registri **di prima** della
    #     cura del 21 agosto 2026 (quando `registro.c` faceva TRE `write()` per
    #     riga) e registri **di dopo**.  ⛔ Un rivelatore che dicesse «zero» su
    #     tutt'e due sarebbe cieco; uno che trova le righe rotte solo nei
    #     vecchi ha dimostrato due cose in un colpo: che vede, e che la cura
    #     regge.  ⚠ Quei registri non sono miei, e di li' si prende SOLO la
    #     forma delle righe.
    p.add_argument("--scansiona", default=None,
                   help="registri (separati da virgola) da setacciare per "
                        "righe rotte, senza leggerli qui")
    a = p.parse_args()

    if a.certifica:
        return certifica()

    os.makedirs(FUORI, exist_ok=True)
    B = _b92()

    if a.scansiona:
        _log("⭐⭐ LE RIGHE ROTTE, su registri gia' scritti — il CONTROLLO "
             "POSITIVO del rivelatore")
        _inf("⛔ i registri di PRIMA del 21 agosto 2026 furono scritti con TRE "
             "«write()» per riga (riquadro di `registro.c`): li' le righe "
             "orfane devono ESSERCI.  ⚠ Se il rivelatore non le trovasse "
             "nemmeno li', il suo «zero» sui registri nuovi non varrebbe niente")
        fuori = []
        for perc in a.scansiona.split(","):
            perc = perc.strip()
            if not perc:
                continue
            rc, out, _ = root("stat -c '%%y %%s' %s 2>/dev/null || echo NO"
                              % perc)
            quando = out.strip()
            s = scansione_intera(perc)
            fuori.append({"percorso": perc, "quando": quando, **s})
            if not s["scansione_credibile"]:
                _dub("%s — ⛔ scansione NON credibile (%s buone su %s)"
                     % (perc, s["righe_buone"], s["righe_in_tutto"]))
                continue
            _inf("%-42s %s" % (perc, quando[:19]))
            _inf("    %8s righe · %4s ORFANE + %3s INNESTATE · (%s senza marca, "
                 "di cui %s di TERZI) · %s in «...» · piu' lunga %s byte · "
                 "sopra %d: %s"
                 % (s["righe_in_tutto"], s["orfane"], s["innestate"],
                    s["senza_marca"], s["estranee"],
                    s["finiscono_in_puntini"], s["riga_piu_lunga"], LUNGA,
                    s["lunghe_oltre_%d" % LUNGA]))
        vecchi = [f for f in fuori if f.get("orfane")]
        if vecchi:
            _ok("⭐ il rivelatore TROVA righe rotte in %d registri su %d: non "
                "e' cieco, e il suo «zero» altrove e' un fatto"
                % (len(vecchi), len(fuori)))
        else:
            _dub("⛔ NESSUNA riga rotta in nessuno dei %d registri: ⚠ o la cura "
                 "regge ovunque, o il rivelatore non vede.  Senza un registro "
                 "di PRIMA della cura non lo posso distinguere" % len(fuori))
        with open(os.path.join(FUORI, "10-b96-scansione.json"), "w") as f:
            json.dump(fuori, f, ensure_ascii=False, indent=1, default=str)
        return 0

    if a.analizza:
        _log("⭐ UN REGISTRO GIA' SCRITTO — «%s»" % a.analizza)
        _inf("⚠ se non e' il mio, lo DICHIARO: di qui si prende solo quel che "
             "non dipende da chi l'ha prodotto (la frazione attribuibile e le "
             "righe intrecciate), mai una prestazione")
        r = analizza_file(a.analizza, a.mega)
        if r is None:
            _dub("⛔ NON HO MISURATO")
            return 3
        d = r["misura"]
        _inf("file %s byte · letti gli ultimi %s · utenti trovati nel registro: "
             "%d (%s)" % (r["byte_file"], r["byte_letti"], len(r["utenti"]),
                          " ".join(r["utenti"])))
        _inf("mappe dal registro: %d provenienze, %d uid, %d pid (%d righe di "
             "ponte)" % (r["mappe"]["prov"], r["mappe"]["uid"],
                         r["mappe"]["pid"], r["mappe"]["righe_ponte"]))
        _inf("⚠ aperture DENTRO la fetta: %d (se sono zero, la fetta e' tutta "
             "a regime)" % r["aperture_dentro_la_fetta"])
        if d is None:
            _dub("⛔ NON HO MISURATO: troppo poche righe")
            return 3
        _inf("⭐⭐ %d righe · attribuite %d ⇒ **%0.1f %%** · ⭐ righe AMBIGUE "
             "(due identificatori discordi): %d"
             % (d["righe"], d["attribuite"], 100 * d["quota"], d["ambigue"]))
        if d["diagnosi_quota"] is not None:
            _inf("⭐⭐ righe DI DIAGNOSI: %d · attribuite %d ⇒ **%0.1f %%**"
                 % (d["diagnosi_righe"], d["diagnosi_attribuite"],
                    100 * d["diagnosi_quota"]))
        for nome in sorted(d["per_diagnosi"],
                           key=lambda x: -d["per_diagnosi"][x]["n"]):
            v = d["per_diagnosi"][nome]
            _inf("    %-18s %6d righe · attribuite %6d (%5.1f %%)"
                 % (nome, v["n"], v["attr"], 100 * v["attr"] / v["n"]))
        i = r["intrecci"]
        _inf("intrecci: %d righe buone · %d orfane · %d innestate · %d troncate "
             "· piu' lunga %s byte · sopra %d byte: %d"
             % (i["righe_buone"], i["orfane"], i["innestate"], i["troncate"],
                i["riga_piu_lunga_byte"], LUNGA,
                i["lunghe_oltre_%d" % LUNGA]))
        for e in i["esempi_orfane"][:3]:
            _dub("orfana: %s" % e)
        for e in i["esempi_innestate"][:3]:
            _dub("innestata: %s" % e)
        s = r["scansione_intera"]
        if not s["scansione_credibile"]:
            _dub("⛔ LA SCANSIONE INTERA NON E' CREDIBILE (%s righe buone su "
                 "%s): NON riferisco il suo conto"
                 % (s["righe_buone"], s["righe_in_tutto"]))
        _inf("⭐ e su TUTTO il file (%s righe): %s ORFANE + %s INNESTATE "
             "(%s senza marca, di cui %s di TERZI: libopus, SVT, ld.so) · %s "
             "in «...» · piu' lunga %s byte · sopra %d byte: %s"
             % (s["righe_in_tutto"], s["orfane"], s["innestate"],
                s["senza_marca"], s["estranee"], s["finiscono_in_puntini"],
                s["riga_piu_lunga"], LUNGA, s["lunghe_oltre_%d" % LUNGA]))
        if s["quota_rotte"] is not None:
            _inf("⇒ righe rotte: %0.5f %% (%s su %s)"
                 % (100 * s["quota_rotte"],
                    (s["orfane"] or 0) + (s["innestate"] or 0),
                    s["righe_in_tutto"]))
        _inf("righe di PONTE in tutto il file: %d ⇒ ⭐ per attribuire UNA riga "
             "di regime bisogna setacciare l'intero registro"
             % r["righe_di_ponte_in_tutto"])
        # ⛔ E IL RIVELATORE SI TARA QUI DENTRO, su queste stesse righe: un
        #    «zero intrecci» che non fosse stato messo alla prova sul MEDESIMO
        #    testo non varrebbe niente (`LEZIONI.md` §1.33).
        crudo = fetta(max(0, r["byte_file"] - 200000), r["byte_file"],
                      a.analizza)
        if crudo:
            lst = crudo.rstrip("\n").split("\n")
            if len(lst) > 80:
                lst = _intreccia(lst, 10, 60)
                lst = _intreccia(lst, 40, 30)
                g = intrecci("\n".join(lst))
                passa, perche = p_rivelatore_intrecci(
                    intrecci(crudo), g)
                (_ok if passa else _ko if passa is False else _dub)(perche)
        with open(os.path.join(FUORI, "10-b96-analisi.json"), "w") as f:
            json.dump(r, f, ensure_ascii=False, indent=1, default=str)
        _inf("esiti in %s/10-b96-analisi.json" % FUORI)
        return 0

    _log("10-b96 — IL REGISTRO A PIU' SESSIONI · porta %d · %d utenti"
         % (PORTA, QUANTI))

    # ⛔⛔ IL LUCCHETTO PRIMA DEL TERRENO, e non e' un dettaglio d'ordine: il
    #     controllo del terreno con `LUCCHETTO_MIO=1` pretende che il lucchetto
    #     sia GIA' mio, e «libero» non basta.  ⭐ Ed e' anche il protocollo del
    #     preambolo del giro 2: `provamt1` e' condiviso, e chi non ha il
    #     lucchetto non lo tocca.
    luc = None
    mio_il_lucchetto = False
    if a.lucchetto_esterno:
        L = B._lucchetto()
        chi, scad = L.stato()
        if chi != IO_SONO:
            _ko("⛔ NON MISURO: il lucchetto dovrebbe essere gia' mio «%s», e "
                "invece e' di «%s»" % (IO_SONO, chi))
            return 2
        _ok("il lucchetto della GPU e' gia' mio «%s», ancora per %d s — NON lo "
            "prendo e NON lo mollo: e' di chi mi ha lanciato"
            % (IO_SONO, int((scad or 0) - time.time())))
        mio_il_lucchetto = True
    elif not a.senza_lucchetto:
        luc = B._lucchetto()
        quanto = int(a.durata + a.taratura * (QUANTI + 1) * 2
                     + a.cieca * a.prove + 900)
        _inf("prendo il lucchetto della GPU «%s» per %d s (aspetto davvero)"
             % (IO_SONO, quanto))
        try:
            luc.prendi(IO_SONO, secondi=quanto, attesa=7200)
        except Exception as e:
            _ko("⛔ NON MISURO: %s" % e)
            return 2
        mio_il_lucchetto = True
    else:
        _dub("⛔ SENZA LUCCHETTO: i numeri di questo giro NON valgono e non si "
             "riferiscono")

    esiti, rossi, muti = {}, [], []
    try:
        if not terreno(mio_il_lucchetto):
            _ko("⛔ il terreno non regge: NON misuro")
            return 2   # ⚠ il `finally` qui sotto molla il lucchetto lo stesso
        esiti, rossi, muti = giro(a)
    finally:
        _log("⛔ LA MACCHINA SI RIMETTE COM'ERA")
        for _u, n, _m, _d in SESSIONI:
            root("pkill -u %d -f 04-b30-scena; true" % n)
        # ⛔⛔ LA PULIZIA SI CHIUDE DENTRO IL PROPRIO RECINTO — 25 ago 2026.
        #
        #     Qui c'erano due modelli **globali**: `[/]srv/remotix/tmp/10b5/`
        #     (la cartella di lavoro scritta a mano, che smette di essere la
        #     mia appena `DENTRO_LAV` cambia) e `10-b92-cliente[.]py --cliente`
        #     **senza nessun recinto**, che ammazza i clienti di CHIUNQUE altro
        #     stia girando.  ⛔ E' la quinta trappola di `fasi/10-…md` §7.3,
        #     «una pulizia con modello globale che ammazza i clienti di un
        #     altro» — passata a un pelo una volta, e qui era scritta.
        # ⭐ Adesso il recinto e' la MIA cartella di lavoro, e viene da
        #    `DENTRO_LAV`: chi non scrive li' dentro non e' mio e non si tocca.
        root("pkill -f -- '--giornale %s/'; true"
             % DENTRO_LAV.replace("/", "[/]", 1))
        root("pkill -f '10-b92-cliente[.]py --cliente .*%s'; true"
             % DENTRO_LAV.replace("/", "[/]", 1))
        time.sleep(3)
        for i in range(1, QUANTI + 1):
            B.chiudi_palco(i)
        if luc:
            luc.molla(IO_SONO)

    with open(os.path.join(FUORI, "10-b96-esiti.json"), "w") as f:
        json.dump(esiti, f, ensure_ascii=False, indent=1, default=str)
    _inf("esiti in %s/10-b96-esiti.json" % FUORI)

    _log("IL VERDETTO — %d rossi · %d non giudicati" % (len(rossi), len(muti)))
    for r in rossi[:30]:
        _ko(r)
    for m in muti[:30]:
        _dub(m)
    if rossi:
        return 1
    if muti:
        return 3
    _ok("⭐ tutti i predicati hanno fatto quel che era scritto prima")
    return 0


if __name__ == "__main__":
    sys.exit(principale())
