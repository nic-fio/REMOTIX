#!/usr/bin/env python3
"""03-b15-movimento.py — il banco dello STEP 3 della fase 3: IL MOVIMENTO.

⛔ GIRA DENTRO IL CONTENITORE della macchina di prova (192.168.0.2): aioquic
   sta li', e su CHUWI non c'e'.  Lo lancia `03-b15-lancia.sh`.

  python3 03-b15-movimento.py --certifica            ⭐ PRIMA di ogni misura
  python3 03-b15-movimento.py --elenco               che cosa prova, e come
  python3 03-b15-movimento.py --porta 7603 --caso tutti

===========================================================================
⛔ CHE COSA PROVA, E PERCHE' OGNUNA DELLE SEI

Sono le sei proprieta' che `FASI.md` §03-movimento chiede allo step 3, e
ciascuna ha accanto il sintomo che il suo rosso nomina:

  P1  i `numero` crescono di UNO per fotogramma, **compresi gli abbandonati**
      (§6.2).  ⛔ Un buco «significa qualcosa»: e' il segnale su cui §5.2 fa
      chiedere una chiave.  Se il contatore saltasse gli abbandonati, il client
      non avrebbe modo di sapere che gli manca un pezzo.
  P2  il PRIMO fotogramma dopo `SESSIONE` e' una CHIAVE `0x0301` (§5.2).
      ⛔ Senza questa riga un delta in apertura e' CONFORME e il client non ha
      modo di accorgersene — nessun buco nei numeri, nessun errore dal
      decodificatore.  Il sintomo sarebbe «il desktop compare a pezzi».
  P3  un `RICHIEDI_CHIAVE` produce DAVVERO una chiave (§5.2, §7.1).
      ⛔ Prima della fase 3 non la produceva: `codificatore_chiedi_chiave()`
      non aveva nessun chiamante nel prodotto, e con GOP infinito dopo la prima
      chiave non ne arrivava mai piu' una.
  P4  il SECONDO fotogramma esiste, e almeno uno e' un DELTA.
      ⛔ E' la trappola `EAGAIN`/`svuotato` di `codificatore.c`: un
      codificatore messo in scarico non torna indietro, e il sintomo e' «il
      video si ferma dopo il primo».  ⚠ La seconda meta' — «almeno un delta» —
      e' quella che vede il codificatore usa-e-getta: con uno nuovo a ogni
      fotogramma, TUTTI sarebbero chiavi e il primo controllo sarebbe verde.
  P5  un fotogramma abbandonato arriva come stream AZZERATO, non come stream
      finito (§5.1, §6.2).  ⛔ E' la forma d'errore E8 — «un fotogramma perso in
      silenzio e uno abbandonato di proposito hanno lo stesso aspetto dal lato
      che riceve» — e si prova SUL FILO, non nel registro.
  P6  il credito di stream esaurito NON e' un errore fatale (§2.3).
      ⛔ «Il server DEVE reggere il rifiuto di aprire uno stream invece di
      considerarlo un errore fatale.»

===========================================================================
⛔⭐ COME SI CERTIFICA — `LEZIONI.md` §1.2, E NON E' UNA FORMALITA'

«Si accerta che il banco sappia produrre il risultato atteso PRIMA di puntarlo
sull'incognita.  Altrimenti un esito negativo e' ambiguo fra "l'incognita non
funziona" e "il banco non funzionava".»

⭐ Qui ogni proprieta' e' una FUNZIONE PURA su un `Verbale` — la trascrizione di
   quel che e' arrivato sul filo — e la certificazione le esegue su DUE verbali
   fabbricati a mano:

     · il **controllo positivo**: un verbale che rispetta la proprieta'.
       Il controllo DEVE dire verde.  ⛔ Senza questo, un controllo rotto che
       dice sempre rosso sembrerebbe un banco severo;
     · il **controllo negativo**: un verbale che la viola, e la viola SOLO
       li'.  Il controllo DEVE dire rosso, ⛔ **e deve nominare la propria
       regola**: un rosso per un'altra ragione non e' un controllo negativo,
       e' un banco che e' crollato.

⚠ E i verbali fabbricati sono la stessa struttura che esce dal filo: se
  cambiasse il modo di leggere lo stream, la certificazione cambierebbe con
  lui.  Una certificazione su una struttura finta parallela sarebbe la forma
  «il banco misura il banco».

===========================================================================
⛔ LA SCENA, DICHIARATA — `LEZIONI.md` §1.1

Il desktop di `nicfio` sulla macchina di prova, con la scena dello **step 2**
se e' accesa.  ⚠ E se non lo e', **si dichiara**: un compositore Wayland
consegna un fotogramma solo quando qualcosa cambia, quindi su un desktop fermo
questo banco misura ZERO fotogrammi e **quello zero e' un risultato, non un
difetto** — ma un risultato che non dice niente sul prodotto.

⛔ Da cui la regola di questo file: se arrivano meno di `--minimo` fotogrammi,
   l'esito NON e' rosso: e' **NON PROVATO**, e sono tre esiti e non due.  Un
   rosso li' accuserebbe il prodotto di una scena ferma.
"""

import argparse
import asyncio
import importlib.util
import json
import os
import ssl
import struct
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ aioquic si importa TARDI, dentro le funzioni che lo usano: `--elenco` e
#    `--certifica` devono poter girare su CHUWI, dove aioquic non c'e', ed e'
#    precisamente li' che li legge chi revisiona il banco.  E' la stessa cura
#    gia' scritta in `02-filo-cliente.py`.
_b3 = None


def _porta(nome, file):
    s = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def carica_b3():
    global _b3
    if _b3 is None:
        _b3 = _porta("b3", "01-b3-cliente.py")
    return _b3


# --------------------------------------------------------------------------
# Le costanti del protocollo.  ⛔ Si scrivono qui e si CONFRONTANO con quelle di
# `02-filo-fotogramma.py` in `--certifica`: due tabelle che mappano le stesse
# cose divergono, ed e' la forma che `RCP.md` §0 esiste per togliere.
INTESTAZIONE = 28
CHIAVE, DELTA = 0x0301, 0x0302
WT_UNI = 0x54
T_RICHIEDI_CHIAVE = 0x000D

VERDE, ROSSO, NON_PROVATO = "VERDE", "ROSSO", "NON PROVATO"


class Esito:
    """Il verdetto di UN controllo.

    ⛔ Tre stati e non due: «non provato» non e' «passato».  `regola` e' la riga
       dell'arbitro che il controllo applica, e serve alla certificazione per
       distinguere «e' diventato rosso per la ragione giusta» da «e' crollato».
    """

    def __init__(self, esito, regola, dice, numeri=None):
        self.esito, self.regola, self.dice = esito, regola, dice
        self.numeri = numeri or {}

    @property
    def verde(self):
        return self.esito == VERDE

    def come_dizionario(self):
        return {"esito": self.esito, "regola": self.regola, "dice": self.dice,
                "numeri": self.numeri}

    def __repr__(self):
        return f"<{self.esito} {self.regola}: {self.dice}>"


class Flusso:
    """Uno stream video, come e' arrivato.

    ⛔ `fine` e' «fin» oppure «reset», e la differenza E' il messaggio (§6.2):
       FIN ⇒ fotogramma completo, `RESET_STREAM` ⇒ incompleto, si butta.
       Confonderli e' la forma d'errore E8.
    """

    def __init__(self, sid, quando):
        self.sid, self.quando = sid, quando
        self.grezzo = bytearray()
        self.letta = False
        self.tipo = self.codec = self.lar = self.alt = None
        self.numero = self.istante = self.input = None
        self.byte_dati = 0
        self.fine = None       # "fin" | "reset" | None (mai finito)
        self.finito_a = None

    def arrivano(self, d):
        if not self.letta:
            self.grezzo += d
            if len(self.grezzo) >= INTESTAZIONE:
                g = bytes(self.grezzo[:INTESTAZIONE])
                (self.tipo, self.codec, self.lar, self.alt, self.numero,
                 self.istante, self.input) = struct.unpack("!HHIIIQI", g)
                self.byte_dati = len(self.grezzo) - INTESTAZIONE
                self.letta = True
                self.grezzo = bytearray()
        else:
            self.byte_dati += len(d)

    def come_dizionario(self):
        return {"sid": self.sid, "tipo": self.tipo, "codec": self.codec,
                "lar": self.lar, "alt": self.alt, "numero": self.numero,
                "istante": self.istante, "input": self.input,
                "byte": self.byte_dati, "fine": self.fine,
                "quando": self.quando, "finito_a": self.finito_a,
                "intestazione_letta": self.letta}


class Verbale:
    """Che cosa e' successo sul filo, e nient'altro.

    ⛔ E' l'UNICO ingresso dei sei controlli: le funzioni `p1..p6` non toccano
       la rete e non leggono file.  ⇒ La certificazione le puo' eseguire su
       verbali fabbricati a mano, che e' il modo in cui questo banco si fa
       dimostrare di saper dire di no.
    """

    def __init__(self, flussi=(), chieste=(), registro="", caduta=None,
                 viva=True, tela=(1920, 1080), codec=1,
                 credito_chiesto=None, credito_annunciato=None):
        self.flussi = list(flussi)
        self.chieste = list(chieste)   # [{"quando": t, "dopo": numero}]
        self.registro = registro
        self.caduta = caduta
        self.viva = viva
        self.tela = tela
        self.codec = codec
        self.buio = None
        # ⛔⭐ LA PREMESSA DEL CASO «credito», MISURATA E NON CREDUTA — cura del
        #     13 agosto 2026 sera, e nasce da un ROSSO FALSO di questo banco.
        #
        #     `credito_chiesto`    quanto credito il banco VOLEVA annunciare;
        #     `credito_annunciato` quanto ne e' finito DAVVERO nel ClientHello,
        #                          letto nell'istante in cui aioquic serializza
        #                          i parametri di trasporto.
        #
        #     ⛔ Fino a stamattina questo banco scriveva
        #     `_local_max_streams_uni.value` **dopo** la stretta di mano: RFC
        #     9000 §4.6 vieta di rinnegare un limite gia' annunciato, aioquic
        #     quel campo lo legge **una volta sola** (in
        #     `_serialize_transport_parameters()`, mentre costruisce il
        #     ClientHello), e sul filo andava il predefinito **128** mentre il
        #     banco credeva 6.  `[M]` il registro del server lo diceva parola
        #     per parola: «stream uni 15 aperto; ngtcp2 dice che ne restano
        #     124».  ⇒ P6 accusava il prodotto di non reggere una condizione che
        #     il banco stesso aveva creato illegalmente, e che sul filo non
        #     c'era mai stata.
        #
        # ⭐ Da cui la regola: **la premessa si misura**.  Senza queste due
        #    grandezze un rosso di P6 puo' essere il rosso di una scena che non
        #    e' mai esistita — ed e' precisamente quel che e' successo.
        self.credito_chiesto = credito_chiesto
        self.credito_annunciato = credito_annunciato

    @property
    def finiti(self):
        return [f for f in self.flussi if f.letta]

    def come_dizionario(self):
        return {"flussi": [f.come_dizionario() for f in self.flussi],
                "chieste": self.chieste, "caduta": self.caduta,
                "viva": self.viva, "buio": self.buio,
                "credito_chiesto": self.credito_chiesto,
                "credito_annunciato": self.credito_annunciato,
                "righe_registro": len(self.registro.splitlines())}


def _finto(numero, tipo=DELTA, fine="fin", byte=5000, quando=0.0, sid=None,
           lar=1920, alt=1080, codec=1, istante=None, letta=True):
    """Un flusso fabbricato, per la certificazione.

    ⛔ Passa dallo stesso `Flusso` che usa il filo: un finto costruito con una
       struttura parallela farebbe certificare il banco su una cosa che non e'
       quella che misura.
    """
    f = Flusso(sid if sid is not None else 3 + 4 * numero, quando)
    if letta:
        f.arrivano(struct.pack("!HHIIIQI", tipo, codec, lar, alt, numero,
                               istante if istante is not None else numero * 16000,
                               0))
        f.arrivano(b"\0" * byte)
    f.fine = fine
    f.finito_a = quando
    return f


# ==========================================================================
# ⭐ I SEI CONTROLLI.  Funzioni pure sul verbale, e nient'altro.
# ==========================================================================

def p1_numeri(v, minimo=8):
    """§6.2 — i `numero` crescono di UNO per fotogramma, ABBANDONATI COMPRESI.

    ⛔⭐ E UN BUCO NON E' UN ROSSO — cura del 13 agosto 2026, trovata dal primo
        giro con la linea cattiva.

        La prima stesura pretendeva una successione **senza buchi**, e §6.2 dice
        il contrario con le sue stesse parole: *«un buco nella successione e'
        quindi normale e SIGNIFICA QUALCOSA: e' il segnale su cui §5.2 fa
        chiedere una chiave»*.  ⚠ Il controllo sbagliato ha puntato un rosso su
        un prodotto che stava facendo **esattamente quel che l'arbitro
        prescrive**: aveva abbandonato due fotogrammi prima che ne uscisse un
        byte, e i loro numeri erano stati consumati come §6.2 impone.

    ⇒ La proprieta' vera e' piu' stretta, non piu' larga: **ogni buco dev'essere
      SPIEGATO**.  Le due sole spiegazioni che §6.2 ammette sono
        · un fotogramma ABBANDONATO (il numero e' stato consumato, §5.1), e
          allora il registro del server lo dichiara;
        · niente altro — «quelli che non spedisce affatto» NON consumano il
          numero, quindi non aprono nessun buco.
      ⛔ Un buco senza una riga di registro che lo spieghi e' un fotogramma
      **perso in silenzio**, ed e' la cosa che §5.1 esiste per rendere
      impossibile.
    """
    f = sorted(v.finiti, key=lambda x: x.numero)
    if len(f) < minimo:
        return Esito(NON_PROVATO, "RCP.md §6.2",
                     f"sono arrivati {len(f)} fotogrammi e ne servono almeno "
                     f"{minimo}: NON e' un rosso del prodotto — su una scena "
                     f"ferma Mutter non consegna niente (LEZIONI.md §1.1)",
                     {"flussi": len(f), "minimo": minimo})
    numeri = [x.numero for x in f]
    if len(set(numeri)) != len(numeri):
        doppi = sorted({n for n in numeri if numeri.count(n) > 1})
        return Esito(ROSSO, "RCP.md §6.2",
                     f"il `numero` si RIPETE: {doppi} — «cresce di uno per "
                     f"ciascuno» non ammette due fotogrammi con lo stesso",
                     {"doppi": doppi})
    mancanti = numeri[-1] - numeri[0] + 1 - len(numeri)
    azzerati = [x.numero for x in f if x.fine == "reset"]
    # ⛔ Quanti il SERVER dichiara di aver abbandonato: §5.1 lo obbliga a
    #    scriverlo, e questa e' la riga che rende il buco leggibile.
    detti = len([r for r in v.registro.splitlines() if "ABBANDONATO" in r])
    if mancanti and not v.registro:
        return Esito(NON_PROVATO, "RCP.md §6.2",
                     f"mancano {mancanti} numeri fra {numeri[0]} e {numeri[-1]} e "
                     f"il registro del server non e' stato letto: non so dire se "
                     f"siano abbandoni dichiarati o fotogrammi persi in silenzio",
                     {"mancanti": mancanti})
    if mancanti > detti:
        return Esito(ROSSO, "RCP.md §6.2, §5.1",
                     f"mancano {mancanti} numeri fra {numeri[0]} e {numeri[-1]} e "
                     f"il registro del server ne dichiara abbandonati solo "
                     f"{detti}: {mancanti - detti} fotogrammi sono spariti IN "
                     f"SILENZIO.  ⛔ §6.2 dice che il contatore NON cresce per "
                     f"quelli che non spedisce affatto, quindi ogni buco e' un "
                     f"numero consumato — e §5.1 impone di scriverlo",
                     {"mancanti": mancanti, "detti": detti})
    return Esito(VERDE, "RCP.md §6.2",
                 f"{len(numeri)} fotogrammi, `numero` da {numeri[0]} a "
                 f"{numeri[-1]}; {len(azzerati)} arrivati AZZERATI e {mancanti} "
                 f"numeri mancanti, tutti spiegati dai {detti} abbandoni che il "
                 f"registro dichiara — il contatore ha contato anche quelli che "
                 f"ha buttato",
                 {"flussi": len(numeri), "primo": numeri[0], "ultimo": numeri[-1],
                  "azzerati": len(azzerati), "mancanti": mancanti, "detti": detti})


def p2_prima_chiave(v):
    """§5.2 — il primo fotogramma dopo `SESSIONE` DEVE essere una CHIAVE."""
    f = sorted(v.finiti, key=lambda x: x.numero)
    if not f:
        return Esito(NON_PROVATO, "RCP.md §5.2",
                     "non e' arrivato nessun fotogramma: non c'e' un primo da "
                     "giudicare")
    primo = f[0]
    if primo.numero != 1:
        return Esito(NON_PROVATO, "RCP.md §5.2",
                     f"il primo fotogramma visto porta `numero` {primo.numero} e "
                     f"non 1: questa sessione era gia' cominciata quando il "
                     f"banco si e' messo ad ascoltare, e «il primo dopo "
                     f"SESSIONE» non e' quello che ho in mano",
                     {"numero": primo.numero})
    if primo.tipo != CHIAVE:
        return Esito(ROSSO, "RCP.md §5.2",
                     f"il primo fotogramma della sessione (`numero` 1) porta "
                     f"tipo 0x{primo.tipo:04X} e §5.2 vuole 0x0301 (CHIAVE).  "
                     f"⛔ Un delta in apertura e' CONFORME a ogni altra riga e "
                     f"il client non ha modo di accorgersene",
                     {"tipo": primo.tipo})
    if primo.fine != "fin":
        return Esito(ROSSO, "RCP.md §5.2",
                     f"il primo fotogramma e' una CHIAVE ma e' finito con "
                     f"«{primo.fine}»: §5.2 vieta di abbandonare una chiave, e "
                     f"una chiave azzerata non rimette in piedi niente",
                     {"fine": primo.fine})
    return Esito(VERDE, "RCP.md §5.2",
                 f"il primo fotogramma (`numero` 1) e' una CHIAVE 0x0301 di "
                 f"{primo.byte_dati} byte, chiusa con FIN",
                 {"byte": primo.byte_dati})


def p3_richiedi_chiave(v, entro=3.0):
    """§5.2 / §7.1 — un `RICHIEDI_CHIAVE` produce DAVVERO una chiave."""
    if not v.chieste:
        return Esito(NON_PROVATO, "RCP.md §5.2",
                     "nessun RICHIEDI_CHIAVE e' stato spedito: non c'e' niente "
                     "da giudicare")
    for c in v.chieste:
        dopo = [x for x in v.finiti
                if x.numero > c["dopo"] and x.quando >= c["quando"]]
        chiavi = [x for x in dopo if x.tipo == CHIAVE and x.quando - c["quando"] <= entro]
        if not chiavi:
            return Esito(ROSSO, "RCP.md §5.2",
                         f"RICHIEDI_CHIAVE(ultimo_numero={c['dopo']}) spedita, e "
                         f"nei {entro} s dopo sono arrivati {len(dopo)} "
                         f"fotogrammi e NESSUNO era una chiave.  ⛔ E' il debito "
                         f"che resta acceso e non paga: con GOP infinito lo "
                         f"schermo del client non riparte piu'",
                         {"dopo": len(dopo), "chiavi": 0})
        prima = min(chiavi, key=lambda x: x.quando)
        c["risposta_ms"] = round((prima.quando - c["quando"]) * 1000)
        c["risposta_numero"] = prima.numero
    ms = [c["risposta_ms"] for c in v.chieste]
    return Esito(VERDE, "RCP.md §5.2",
                 f"{len(v.chieste)} RICHIEDI_CHIAVE, {len(v.chieste)} chiavi "
                 f"arrivate — la piu' lenta in {max(ms)} ms",
                 {"richieste": len(v.chieste), "ms": ms})


def p4_secondo(v):
    """La trappola `EAGAIN`/`svuotato`, e il codificatore usa-e-getta."""
    f = sorted(v.finiti, key=lambda x: x.numero)
    if len(f) < 2:
        return Esito(ROSSO, "codificatore.c:1253 · RCP.md §5.2",
                     f"sono arrivati {len(f)} fotogrammi: il SECONDO non esiste. "
                     f"⛔ E' il sintomo che il commento della trappola nomina "
                     f"parola per parola — «il video si ferma dopo il primo»",
                     {"flussi": len(f)})
    delta = [x for x in f if x.tipo == DELTA]
    # ⛔⭐ E PRIMA DI ACCUSARE IL CODIFICATORE SI GUARDA LA SCENA — cura del 13
    #     agosto 2026 sera, e nasce da un ROSSO FALSO che questo banco ha
    #     prodotto **appena** il caso «credito» ha cominciato a funzionare.
    #
    #     `[M]` Col credito onestamente stretto a 6 (3 stream a RCP) sono
    #     arrivati 3 fotogrammi e **tutti e tre erano chiavi**, e non perche' il
    #     codificatore sia usa-e-getta: il primo e' la chiave che §5.2 impone,
    #     poi il posto e' finito, i delta sono stati saltati e §5.2 ha armato la
    #     CURA — cioe' ha chiesto una CHIAVE.  ⇒ In quella scena il prodotto
    #     stava facendo **esattamente quel che l'arbitro prescrive**, e questo
    #     controllo lo accusava del difetto opposto.
    #
    # ⚠ E' la stessa forma che P1 ha gia' pagato: «un buco non e' un rosso, un
    #   buco NON SPIEGATO lo e'».  Qui: «nessun delta non e' un rosso se il
    #   registro dice che i delta sono stati saltati per mancanza di posto».
    saltati = [r for r in v.registro.splitlines()
               if "§2.3" in r and "delta" in r]
    if not delta and saltati:
        return Esito(NON_PROVATO, "figlio.c · RCP.md §5.2, §2.3",
                     f"{len(f)} fotogrammi e nessun delta, ma il registro del "
                     f"server dichiara {len(saltati)} delta SALTATI per "
                     f"mancanza di posto (§2.3): i delta non sono mancati "
                     f"perche' il codificatore non li sa fare, ma perche' la "
                     f"scena non ha lasciato loro uno stream.  ⛔ Un rosso qui "
                     f"accuserebbe il codificatore di una condizione che il "
                     f"banco ha creato apposta",
                     {"flussi": len(f), "delta": 0, "saltati": len(saltati)})
    if not delta:
        return Esito(ROSSO, "figlio.c · RCP.md §5.2",
                     f"{len(f)} fotogrammi e NESSUN delta: sono tutti chiavi.  "
                     f"⛔ E' il codificatore usa-e-getta — uno nuovo per "
                     f"fotogramma non ha nessun passato da cui predire, quindi "
                     f"ogni fotogramma e' una chiave e costa dieci volte tanto. "
                     f"⚠ Il primo controllo qui sopra sarebbe VERDE lo stesso",
                     {"flussi": len(f), "delta": 0})
    return Esito(VERDE, "codificatore.c:1253 · RCP.md §5.2",
                 f"{len(f)} fotogrammi consegnati, di cui {len(delta)} delta e "
                 f"{len(f) - len(delta)} chiavi: il codificatore ha uno stato e "
                 f"non si e' chiuso al secondo",
                 {"flussi": len(f), "delta": len(delta),
                  "chiavi": len(f) - len(delta)})


def p5_abbandono(v):
    """§5.1 / §6.2 — l'abbandono si vede SUL FILO, ed e' la forma E8.

    ⛔⭐ E IL REGISTRO SI GUARDA PER PRIMO, non per ultimo — cura trovata dalla
        CERTIFICAZIONE di questo stesso file, il 13 agosto 2026.

        La prima stesura diceva: nessuno stream azzerato ⇒ NON PROVATO, e basta.
        ⛔ Con quella riga il controllo negativo non poteva esistere: la scena
        di **E8** — il server abbandona e il fotogramma arriva lo stesso come
        stream FINITO — usciva «non provato» invece che rossa.  ⚠ Cioe' il
        banco non sapeva vedere il difetto che esiste per vedere: «un
        fotogramma abbandonato e uno completo avevano lo stesso aspetto»
        (rilievo R1.7), e il banco li avrebbe fatti sembrare uguali una seconda
        volta.

        ⇒ Le due meta' si confrontano: quel che il SERVER dice di aver
        abbandonato (§5.1 obbliga a scriverlo) e quel che e' arrivato azzerato
        SUL FILO.  Se la prima c'e' e la seconda no, e' E8, ed e' rosso.
    """
    azzerati = [x for x in v.flussi if x.fine == "reset"]
    finiti = [x for x in v.flussi if x.fine == "fin"]
    detti = [r for r in v.registro.splitlines() if "ABBANDONATO" in r]
    if not azzerati:
        if detti:
            # ⛔⭐ E QUI CI SONO DUE SCENE, NON UNA — cura del 13 agosto 2026.
            #
            #     Un fotogramma abbandonato **prima che ne esca un byte** non
            #     puo' arrivare come stream azzerato: il client non ha mai visto
            #     nemmeno il preambolo, quindi per lui quello stream non e' mai
            #     esistito.  ⛔ Ma NON e' invisibile: §6.2 gli lascia un **buco
            #     nella successione dei `numero`**, ed e' proprio il segnale su
            #     cui §5.2 gli fa chiedere una chiave.  ⇒ Quella scena e'
            #     CONFORME, e chiamarla E8 sarebbe un rosso all'imputato
            #     sbagliato — ci e' cascata la prima stesura di questo controllo.
            #
            #     ⛔ E8 e' l'altra: il fotogramma abbandonato che arriva
            #     **completo**, cioe' con dei numeri tutti attaccati e nessuno
            #     stream azzerato.  Li' i due sono davvero indistinguibili.
            letti = sorted(x.numero for x in v.finiti)
            mancanti = (letti[-1] - letti[0] + 1 - len(letti)) if letti else 0
            if mancanti >= len(detti):
                return Esito(NON_PROVATO, "RCP.md §5.1, §6.2",
                             f"il server dichiara {len(detti)} abbandoni e sul "
                             f"filo si vedono {mancanti} numeri mancanti: gli "
                             f"abbandoni sono avvenuti PRIMA che uscisse un "
                             f"byte, quindi il client li vede come un buco (§6.2) "
                             f"e non come uno stream azzerato.  ⛔ E' conforme, "
                             f"ma NON prova il `RESET_STREAM` sul filo: serve un "
                             f"abbandono su un fotogramma gia' COMINCIATO",
                             {"detti": len(detti), "mancanti": mancanti, "reset": 0})
            return Esito(ROSSO, "RCP.md §6.2 (forma E8)",
                         f"il registro del server dichiara {len(detti)} "
                         f"fotogrammi ABBANDONATI, sul filo NON e' arrivato "
                         f"nessuno stream azzerato e i numeri non hanno buchi "
                         f"({mancanti}): {len(finiti)} sono arrivati tutti con "
                         f"FIN.  ⛔ E' la forma d'errore E8, rilievo R1.7 — «un "
                         f"fotogramma abbandonato e uno completo hanno lo stesso "
                         f"aspetto dal lato che riceve», e il client "
                         f"consegnerebbe mezza immagine al decodificatore",
                         {"detti": len(detti), "reset": 0, "fin": len(finiti),
                          "mancanti": mancanti})
        return Esito(NON_PROVATO, "RCP.md §5.1, §6.2",
                     f"nessuno stream azzerato in {len(finiti)} fotogrammi, e il "
                     f"registro del server non ne dichiara nessuno: la coda non "
                     f"si e' mai riempita abbastanza da far abbandonare niente.  "
                     f"⛔ NON e' un verde — «l'abbandono funziona» non si "
                     f"dimostra non abbandonando mai",
                     {"fin": len(finiti), "reset": 0, "detti": 0})
    chiavi_azzerate = [x for x in azzerati if x.letta and x.tipo == CHIAVE]
    if chiavi_azzerate:
        return Esito(ROSSO, "RCP.md §5.2",
                     f"{len(chiavi_azzerate)} CHIAVI sono state azzerate "
                     f"(numeri {[x.numero for x in chiavi_azzerate][:5]}): §5.2 "
                     f"lo vieta con un ⛔ — «abbandonare la cura non e' una "
                     f"cura»",
                     {"chiavi_azzerate": len(chiavi_azzerate)})
    # ⛔ §5.1: «ogni abbandono DEVE essere scritto nel registro».  Si guarda, e
    #    l'assenza NON e' un dettaglio: e' precisamente la meta' che rende un
    #    fotogramma perso indistinguibile da uno abbandonato di proposito.
    if v.registro and not detti:
        return Esito(ROSSO, "RCP.md §5.1",
                     f"{len(azzerati)} stream sono stati azzerati sul filo e il "
                     f"registro del server NON contiene nessuna riga "
                     f"«ABBANDONATO»: §5.1 lo impone — «un fotogramma perso in "
                     f"silenzio e uno abbandonato di proposito hanno lo stesso "
                     f"aspetto dal lato che riceve»",
                     {"reset": len(azzerati), "righe": 0})
    return Esito(VERDE, "RCP.md §5.1, §6.2",
                 f"{len(azzerati)} fotogrammi sono arrivati come stream AZZERATO "
                 f"e {len(finiti)} come stream chiuso con FIN: i due si "
                 f"distinguono sul filo, nessuna chiave e' stata abbandonata, e "
                 f"il registro ne dichiara {len(detti)}",
                 {"reset": len(azzerati), "fin": len(finiti), "detti": len(detti)})


def p6_credito(v):
    """§2.3 — il credito esaurito NON e' un errore fatale.

    ⛔⭐ E LA PRIMA COSA CHE GUARDA E' LA PROPRIA PREMESSA, NON IL PRODOTTO.

        `[M]` 13 agosto 2026: questo controllo ha dato ROSSO al prodotto per una
        stretta di credito che **sul filo non c'e' mai stata** — il banco
        scriveva `_local_max_streams_uni.value = 6` DOPO la stretta di mano,
        aioquic aveva gia' annunciato **128**, e la sessione moriva con
        `STREAM_LIMIT_ERROR` perche' il banco stesso contava 6 su un limite che
        il pari credeva 128.  ⛔ RFC 9000 §4.6: un limite annunciato non si
        ritira.  ⇒ Il rosso era del BANCO, e accusava il prodotto.

    ⭐ Adesso il credito si annuncia PRIMA della stretta di mano e quel che e'
       finito nel ClientHello si LEGGE.  I due rami nuovi qui sotto sono la
       differenza fra un banco che sa di aver costruito la scena e uno che ci
       crede: e il rosso della premessa dice `il banco stesso`, non `RCP.md`.
    """
    # ⛔ «Non ho guardato» non e' «e' andato bene» (`LEZIONI.md` §1.9): se la
    #    spia sul ClientHello non ha catturato niente, non c'e' nessuna scena
    #    dichiarabile e ogni verdetto qui sotto sarebbe su una premessa creduta.
    if v.credito_chiesto is not None and v.credito_annunciato is None:
        return Esito(NON_PROVATO, "il banco stesso",
                     "non ho letto quanto credito sia finito nel ClientHello: "
                     "la spia su `_serialize_transport_parameters` non ha "
                     "catturato niente, e senza la premessa misurata un rosso "
                     "su §2.3 potrebbe essere il rosso di una scena mai "
                     "esistita",
                     {"chiesto": v.credito_chiesto, "annunciato": None})
    if (v.credito_chiesto is not None
            and v.credito_annunciato != v.credito_chiesto):
        return Esito(ROSSO, "il banco stesso",
                     f"⛔ IL BANCO MENTE: credeva di annunciare "
                     f"`initial_max_streams_uni = {v.credito_chiesto}` e sul "
                     f"filo ne sono andati {v.credito_annunciato}.  E' il "
                     f"difetto del 13 agosto 2026 — un credito RINNEGATO dopo "
                     f"la stretta di mano invece che annunciato prima, che RFC "
                     f"9000 §4.6 vieta — e finche' resta, ogni rosso di questo "
                     f"controllo accusa il prodotto di una scena che non e' "
                     f"mai esistita",
                     {"chiesto": v.credito_chiesto,
                      "annunciato": v.credito_annunciato})
    # ⛔⭐ LA SESSIONE CADUTA SI GIUDICA PRIMA DI TUTTO — cura del 13 agosto
    #     2026, e viene da un rosso che il banco NON aveva visto.
    #
    #     `[M]` con `initial_max_streams_uni = 6` il cliente ha chiuso la
    #     connessione con **«Too many streams open»** (STREAM_LIMIT_ERROR): il
    #     server aveva aperto **11** stream unidirezionali.  ⛔ La prima stesura
    #     di questo controllo guardava solo il registro, non ci trovava la riga
    #     di §2.3, e usciva **NON PROVATO** — cioe' dichiarava «la scena non ha
    #     provato niente» proprio nel giro in cui la sessione era MORTA sul
    #     credito.  ⚠ E' la forma peggiore: un banco che tace davanti al difetto
    #     che esiste per trovare.
    #
    # ⛔ E il verdetto e' rosso QUALUNQUE SIA L'ARITMETICA SBAGLIATA: §2.3 dice
    #    «il server DEVE reggere il rifiuto di aprire uno stream invece di
    #    considerarlo un errore fatale», e dal lato che riceve la sessione e'
    #    caduta.  ⚠ Di CHI sia il conto sbagliato — ngtcp2 che concede troppo o
    #    il cliente che conta stretto — questo banco NON lo sa dire, e non lo
    #    indovina: lo dichiara `[?]`.
    if v.caduta:
        return Esito(ROSSO, "RCP.md §2.3",
                     f"la sessione e' CADUTA mentre si stringeva il credito: "
                     f"«{v.caduta}».  ⛔ §2.3 dice che il server DEVE reggere il "
                     f"rifiuto di aprire uno stream invece di considerarlo un "
                     f"errore fatale — e qui non lo regge.  ⚠ `[?]` di chi sia "
                     f"il conto sbagliato (ngtcp2 che concede o il cliente che "
                     f"conta) questo banco non lo sa dire",
                     {"caduta": v.caduta, "flussi": len(v.finiti)})
    if not v.registro:
        return Esito(NON_PROVATO, "RCP.md §2.3",
                     "il registro del server non e' stato letto: non so dire se "
                     "il credito sia mai mancato, e «non ho guardato» non e' "
                     "«non e' successo»")
    righe = [r for r in v.registro.splitlines()
             if "§2.3" in r and "unidirezionale" in r]
    if not righe:
        return Esito(NON_PROVATO, "RCP.md §2.3",
                     "il credito di stream non e' MAI mancato in questo giro: la "
                     "scena non ha provato niente.  ⛔ Non e' un verde — «regge "
                     "il rifiuto» non si dimostra senza un rifiuto",
                     {"righe": 0})
    if not v.viva:
        return Esito(ROSSO, "RCP.md §2.3",
                     f"il credito e' mancato ({len(righe)} volte) e la sessione "
                     f"non era piu' viva alla fine del giro",
                     {"righe": len(righe)})
    # ⛔ E non basta «non e' morta»: dopo il rifiuto devono essere arrivati altri
    #    fotogrammi.  Una sessione viva e muta ha lo stesso aspetto di una che
    #    regge, dal lato che riceve — ed e' la forma E8.
    dopo = len([x for x in v.finiti])
    if dopo < 2:
        return Esito(ROSSO, "RCP.md §2.3",
                     f"il credito e' mancato e sono arrivati in tutto {dopo} "
                     f"fotogrammi: la sessione e' viva e MUTA, che dal lato che "
                     f"riceve ha lo stesso aspetto di una caduta",
                     {"righe": len(righe), "flussi": dopo})
    chiavi_buttate = [r for r in righe if "CHIAVE" in r and "si BUTTA" in r]
    if chiavi_buttate:
        return Esito(ROSSO, "RCP.md §2.3, §5.2",
                     f"una CHIAVE e' stata buttata per mancanza di credito: §2.3 "
                     f"dice che si butta il delta e si ASPETTA per la chiave",
                     {"chiavi_buttate": len(chiavi_buttate)})
    return Esito(VERDE, "RCP.md §2.3",
                 f"col credito onestamente annunciato sul filo "
                 f"({v.credito_annunciato}, di cui 3 se li prende HTTP/3) il "
                 f"posto e' mancato {len(righe)} volte, la sessione e' viva e "
                 f"ha consegnato {dopo} fotogrammi: il rifiuto e' stato retto, "
                 f"non e' stato un errore fatale",
                 {"righe": len(righe), "flussi": dopo,
                  "annunciato": v.credito_annunciato})


CONTROLLI = [
    ("P1-numeri", p1_numeri, "i `numero` crescono di uno, abbandonati compresi"),
    ("P2-prima-chiave", p2_prima_chiave, "il primo dopo SESSIONE e' una CHIAVE"),
    ("P3-richiedi-chiave", p3_richiedi_chiave, "un RICHIEDI_CHIAVE produce una chiave"),
    ("P4-secondo", p4_secondo, "il secondo fotogramma esiste, e c'e' almeno un delta"),
    ("P5-abbandono", p5_abbandono, "l'abbandono arriva come stream AZZERATO (E8)"),
    ("P6-credito", p6_credito, "il credito esaurito non e' un errore fatale"),
]


# ==========================================================================
# ⭐⭐ LA CERTIFICAZIONE — un controllo POSITIVO e uno NEGATIVO per ciascuna
# ==========================================================================

def _verbale_sano(n=12, con_reset=True, con_richiesta=True, registro=None):
    """Il verbale di una sessione che fa tutto giusto.

    ⛔ Serve al controllo POSITIVO: se un controllo dicesse rosso anche qui, i
       suoi rossi sul filo non varrebbero niente.
    """
    flussi = []
    for i in range(1, n + 1):
        tipo = CHIAVE if i in (1, 7) else DELTA
        # il 4 e il 9 sono abbandonati: §6.2 li conta lo stesso
        azzerato = con_reset and i in (4, 9)
        flussi.append(_finto(i, tipo=tipo,
                             fine="reset" if azzerato else "fin",
                             byte=200000 if tipo == CHIAVE else 6000,
                             quando=i * 0.016))
    if registro is None:
        registro = ("10:00:00.000 rcp fotogramma 4 ABBANDONATO NELLA CODA (§5.1, "
                    "RESET_STREAM): 5000 byte non sono usciti\n"
                    "10:00:00.100 rcp fotogramma 9 ABBANDONATO NELLA CODA (§5.1, "
                    "RESET_STREAM): 4000 byte non sono usciti\n"
                    "10:00:00.200 rcp ⚠ §2.3: nessuno stream unidirezionale per "
                    "il delta che veniva dopo il 9 (il client ne concede ancora 0)\n")
    chieste = [{"quando": 6 * 0.016, "dopo": 6}] if con_richiesta else []
    return Verbale(flussi, chieste, registro=registro, viva=True)


def _verbale_sano_credito(n=12):
    """Il gemello del sano per il caso «credito»: la premessa e' DICHIARATA.

    ⛔ Il credito che il banco voleva annunciare e quello che e' finito sul filo
       combaciano — cioe' la scena esiste.  E' il verbale su cui si certificano
       i due rami nuovi di P6, quelli che il 13 agosto non c'erano.
    """
    v = _verbale_sano(n=n)
    v.credito_chiesto = 6
    v.credito_annunciato = 6
    return v


def _aghi():
    """Per ogni controllo: come si GUASTA il verbale, e come si RISANA.

    ⛔ «Solo quella» e' la meta' che si dimentica: un verbale rotto dappertutto
       farebbe diventare rossi tutti i controlli, e non proverebbe che ciascuno
       sa vedere il PROPRIO guasto.

    ⛔⭐ E `risana` lavora sul verbale GUASTO, mai riusando il sano: e' il TERZO
        giro, ed e' l'unico che ATTRIBUISCE il rosso all'ago.  Con due soli
        giri, un controllo che diventasse rosso per una ragione qualunque
        presente nel verbale guasto — e non per l'ago — sembrerebbe sano.

    ⚠ E l'esito atteso dal giro guasto si DICHIARA, e non e' sempre ROSSO: certi
      rami sono NON PROVATO per costruzione («la scena non ha dato niente da
      giudicare» non e' un difetto del prodotto), e pretendere rosso da loro
      sarebbe l'errore di attribuzione che questo banco esiste per non fare.
    """
    def g_p1(v):
        # ⛔ Un buco che NESSUNO SPIEGA.  E' la meta' che conta: un buco
        #    dichiarato e' conforme (§6.2, «significa qualcosa»), un buco muto
        #    e' un fotogramma perso in silenzio.  ⚠ La prima stesura toglieva
        #    solo il fotogramma e lasciava il registro pieno di abbandoni: il
        #    controllo diceva verde, e aveva ragione lui.
        v.registro = ("10:00:00.200 rcp ⚠ §2.3: nessuno stream unidirezionale "
                      "per il delta (ne concede 0)\n")
        v.flussi = [f for f in v.flussi if f.numero != 5]

    def r_p1(v):
        # ⭐ Si rimette il fotogramma, NON il registro: cosi' il buco si chiude
        #    e il verde del terzo giro e' dell'ago, non della riga di registro.
        v.flussi = sorted(v.flussi + [_finto(5, tipo=DELTA, byte=6000,
                                             quando=5 * 0.016)],
                          key=lambda f: f.numero)

    def g_p2(v):
        # Il primo e' un delta: il caso che §5.2 chiama «conforme a ogni altra
        # riga» — nessun buco, nessun errore del decodificatore.
        v.flussi[0] = _finto(1, tipo=DELTA, fine="fin", byte=200000,
                             quando=0.016)

    def r_p2(v):
        v.flussi[0] = _finto(1, tipo=CHIAVE, fine="fin", byte=200000,
                             quando=0.016)

    def g_p3(v):
        # La chiave chiesta non arriva: dopo la richiesta solo delta.
        v.flussi = [f if f.numero != 7
                    else _finto(7, tipo=DELTA, quando=7 * 0.016)
                    for f in v.flussi]

    def r_p3(v):
        v.flussi = [f if f.numero != 7
                    else _finto(7, tipo=CHIAVE, byte=200000, quando=7 * 0.016)
                    for f in v.flussi]

    def g_p4(v):
        # Tutti chiavi: il codificatore usa-e-getta.
        # ⛔ E il registro NON deve dichiarare delta saltati per mancanza di
        #    posto, o la scena non e' piu' quella: sarebbe «nessun delta perche'
        #    non c'era posto», che e' l'ago qui sotto e ha un altro verdetto.
        v.registro = "\n".join(r for r in v.registro.splitlines()
                               if "§2.3" not in r)
        v.flussi = [_finto(f.numero, tipo=CHIAVE, fine=f.fine, byte=200000,
                           quando=f.quando) for f in v.flussi]

    def r_p4(v):
        v.flussi = [f if f.numero in (1, 7)
                    else _finto(f.numero, tipo=DELTA, fine=f.fine, byte=6000,
                                quando=f.quando)
                    for f in v.flussi]

    def g_p4_posto(v):
        # ⭐ Tutti chiavi MA il registro spiega perche': i delta sono stati
        #    saltati per mancanza di posto.  ⛔ L'atteso NON e' rosso — e' la
        #    scena che il caso «credito» costruisce apposta, e accusare li' il
        #    codificatore e' il rosso falso del 13 agosto sera.
        v.flussi = [_finto(f.numero, tipo=CHIAVE, fine=f.fine, byte=200000,
                           quando=f.quando) for f in v.flussi]

    def r_p4_posto(v):
        v.flussi = [f if f.numero in (1, 7)
                    else _finto(f.numero, tipo=DELTA, fine=f.fine, byte=6000,
                                quando=f.quando)
                    for f in v.flussi]

    def g_p5(v):
        # ⛔ E8: l'abbandonato arriva come stream FINITO.  Il registro dice che
        #    e' stato abbandonato, il filo dice che e' completo — la scena del
        #    rilievo R1.7, «avevano lo stesso aspetto dal lato che riceve».
        for f in v.flussi:
            f.fine = "fin"

    def r_p5(v):
        for f in v.flussi:
            if f.numero in (4, 9):
                f.fine = "reset"

    def g_p6_caduta(v):
        v.caduta = "ERRORE_PROTOCOLLO dal server dopo il rifiuto dello stream"
        v.viva = False

    def r_p6_caduta(v):
        v.caduta = None
        v.viva = True

    def g_p6_mente(v):
        # ⛔⭐ IL GESTO DEL 13 AGOSTO: il banco crede di annunciare 6 e sul filo
        #     ne vanno 128, perche' scriveva il limite DOPO la stretta di mano.
        #     ⚠ Questo ago non guasta il prodotto: guasta IL BANCO — ed e'
        #       l'unico di questa tabella che lo fa.
        v.credito_annunciato = 128

    def r_p6_mente(v):
        v.credito_annunciato = v.credito_chiesto

    def g_p6_cieca(v):
        # La spia sul ClientHello non ha catturato niente: «non ho guardato» non
        # e' «e' andato bene» (LEZIONI.md §1.9).
        v.credito_annunciato = None

    def r_p6_cieca(v):
        v.credito_annunciato = v.credito_chiesto

    def g_p6_niente(v):
        # ⛔ Il posto non e' mai mancato: e' il male di 03-b18 — un caso che non
        #    arriva mai alla propria condizione.  L'esito atteso NON e' rosso:
        #    «regge il rifiuto» non si dimostra senza un rifiuto.
        v.registro = "\n".join(r for r in v.registro.splitlines()
                               if "§2.3" not in r)

    def r_p6_niente(v):
        v.registro += ("\n10:00:00.200 rcp ⚠ §2.3: nessuno stream "
                       "unidirezionale per il delta che veniva dopo il 9 (il "
                       "client ne concede ancora 0)\n")

    return {
        "P1-numeri": [
            ("buco muto", _verbale_sano, g_p1, r_p1, "in silenzio", ROSSO)],
        "P2-prima-chiave": [
            ("delta in apertura", _verbale_sano, g_p2, r_p2,
             "il primo fotogramma della sessione", ROSSO)],
        "P3-richiedi-chiave": [
            ("il debito non paga", _verbale_sano, g_p3, r_p3,
             "RICHIEDI_CHIAVE", ROSSO)],
        "P4-secondo": [
            ("usa-e-getta", _verbale_sano, g_p4, r_p4, "NESSUN delta", ROSSO),
            ("⭐ nessun delta, ma il posto mancava", _verbale_sano,
             g_p4_posto, r_p4_posto, "mancanza di posto", NON_PROVATO)],
        "P5-abbandono": [
            ("E8", _verbale_sano, g_p5, r_p5, "forma d'errore E8", ROSSO)],
        "P6-credito": [
            ("la sessione cade", _verbale_sano_credito, g_p6_caduta,
             r_p6_caduta, "e' CADUTA", ROSSO),
            ("⭐ il banco mente (13 ago)", _verbale_sano_credito, g_p6_mente,
             r_p6_mente, "il banco mente", ROSSO),
            ("la spia e' cieca", _verbale_sano_credito, g_p6_cieca,
             r_p6_cieca, "non ho letto", NON_PROVATO),
            ("il posto non manca mai", _verbale_sano_credito, g_p6_niente,
             r_p6_niente, "non ha provato niente", NON_PROVATO),
        ],
    }


def certifica(a):
    """⛔ Si esegue PRIMA di ogni misura, e il suo rosso ferma il giro."""
    import copy as _copy
    aghi = _aghi()
    righe, falle = [], 0
    print("\n\033[1m== ⭐ LA CERTIFICAZIONE — TRE GIRI: sano → guasto → "
          "risanato\033[0m")
    print("   sano     : il verbale rispetta la proprieta'   ⇒ deve dire VERDE")
    print("   guasto   : la viola SOLO li'                   ⇒ deve dire quel")
    print("              che si e' dichiarato, e NOMINARE la propria regola")
    print("   risanato : ⭐ al verbale GUASTO si toglie l'ago ⇒ deve tornare VERDE")
    print("   ⛔ Il terzo giro e' l'unico che attribuisce il rosso all'ago.\n")

    for nome, fn, che_cosa in CONTROLLI:
        print(f"  \033[1m{nome:<20}\033[0m {che_cosa}")
        for etichetta, fabbrica, guasta, risana, ago, atteso in aghi[nome]:
            v_sano = fabbrica()
            e_sano = fn(v_sano)

            v_guasto = fabbrica()
            guasta(v_guasto)
            e_guasto = fn(v_guasto)

            # ⛔ Il risanamento parte dal GUASTO, non dal sano: rifare il sano
            #    sarebbe il primo giro rifatto, e non proverebbe niente.
            v_risanato = _copy.deepcopy(v_guasto)
            risana(v_risanato)
            e_risanato = fn(v_risanato)

            pos = e_sano.esito == VERDE
            # ⛔ «dice quel che si e' dichiarato», non «dice ROSSO»: certi rami
            #    sono NON PROVATO per costruzione.  ⚠ E VERDE non e' mai un
            #    esito atteso da un giro guasto.
            neg = e_guasto.esito == atteso and atteso != VERDE
            nomina = ago.lower() in e_guasto.dice.lower() if neg else False
            ris = e_risanato.esito == VERDE
            buono = pos and neg and nomina and ris
            if not buono:
                falle += 1
            segno = "\033[1;32mOK\033[0m" if buono else "\033[1;31mNO\033[0m"
            print(f"    {segno}  ago: {etichetta}")
            print(f"        sano     : {e_sano.esito:<11} {e_sano.dice[:88]}")
            print(f"        guasto   : {e_guasto.esito:<11} (atteso {atteso}) "
                  f"{e_guasto.dice[:70]}")
            print(f"        risanato : {e_risanato.esito:<11} "
                  f"{e_risanato.dice[:88]}")
            if not pos:
                print("        \033[1;31m⛔ rosso anche sul verbale SANO: i suoi")
                print("           rossi sul filo non varrebbero niente\033[0m")
            if not neg:
                print(f"        \033[1;31m⛔ sul verbale guasto dice "
                      f"{e_guasto.esito} invece di {atteso}: non sa vedere")
                print("           quel che cerca\033[0m")
            if neg and not nomina:
                print(f"        \033[1;31m⛔ e' {e_guasto.esito} ma NON nomina "
                      f"«{ago}»: e' cosi' per un'altra")
                print("           ragione, cioe' e' crollato\033[0m")
            if not ris:
                print("        \033[1;31m⛔ TOLTO L'AGO non torna verde: il "
                      "verdetto del secondo giro NON era")
                print("           dell'ago — il controllo sta giudicando "
                      "qualcos'altro\033[0m")
            righe.append({"controllo": nome, "ago": etichetta,
                          "sano": e_sano.esito, "guasto": e_guasto.esito,
                          "atteso": atteso, "nomina": nomina,
                          "risanato": e_risanato.esito, "esito": buono})

    # ⛔ E le costanti del protocollo si confrontano con l'altro banco: due
    #    tabelle che mappano le stesse cose divergono in silenzio.
    try:
        f24 = _porta("f24", "02-filo-fotogramma.py")
        uguali = (f24.INTESTAZIONE == INTESTAZIONE and f24.CHIAVE == CHIAVE
                  and f24.DELTA == DELTA)
        print(f"\n  {'\033[1;32mOK\033[0m' if uguali else '\033[1;31mNO\033[0m'}  "
              f"le costanti di §6.2 combaciano con quelle di 02-filo-fotogramma.py "
              f"({f24.INTESTAZIONE}/{f24.CHIAVE:#06x}/{f24.DELTA:#06x})")
        if not uguali:
            falle += 1
        righe.append({"controllo": "costanti-gemelle", "esito": uguali})
    except Exception as e:  # noqa: BLE001
        print(f"\n  \033[1;33m??\033[0m  non ho potuto confrontare le costanti con "
              f"02-filo-fotogramma.py: {e}")
        print("       ⚠ «non ho guardato» non e' «combaciano»")
        righe.append({"controllo": "costanti-gemelle", "esito": None})
        falle += 1

    if falle == 0:
        print("\n    \033[1;32m⭐ LA CERTIFICAZIONE PASSA: ogni controllo tace sul sano,\033[0m")
        print("    \033[1;32m   dice di no sul guasto, e dice PERCHE'.\033[0m")
    else:
        print(f"\n    \033[1;31m⛔ LA CERTIFICAZIONE NON PASSA: {falle} cose non tornano.\033[0m")
        print("    \033[1;31m   ⇒ I verdetti di questo banco non valgono finche' non torna.\033[0m")
    return falle, righe


# ==========================================================================
# ⭐ IL GIRO DAL VIVO
# ==========================================================================

def costruisci_cliente(a, caso):
    """⛔ Il cliente, con le tre leve che i tre casi hanno bisogno di muovere."""
    b3 = carica_b3()

    class Movimento(b3.Cliente):
        def __init__(self, *args, **kw):
            super().__init__(*args, **kw)
            self.video = {}        # sid -> Flusso
            self.visti = set()
            self.finiti = []
            self.t0 = time.monotonic()
            self.chieste = []
            self.ultimo_numero = 0
            # ⛔⭐ IL BUIO — la condizione di rete che P5 e P6 hanno bisogno di
            #     provocare, e senza la quale restano NON PROVATE per sempre.
            #
            #     `[M]` 13 agosto 2026: con la finestra di flusso stretta e il
            #     credito stretto, su loopback **non succede niente** — aioquic
            #     rinnova credito e finestra a ogni pacchetto, e il giro di rete
            #     e' di un decimo di millisecondo.  ⇒ La coda del server non si
            #     riempie mai, quindi §5.1 non abbandona mai, e gli stream si
            #     chiudono cosi' in fretta che il credito non finisce mai.
            #
            # ⭐ Allora si spegne la luce: per `--buio` secondi il cliente BUTTA
            #    i datagram che arrivano.  ⚠ E non e' un guasto innestato nel
            #    prodotto — e' una condizione di rete che il modello DICHIARA:
            #    `SPECIFICHE.md` §8.1, «mobile critico, sotto i 2 Mbps,
            #    variabile, alti con perdita».  Il client ha il diritto di
            #    stare su una linea cattiva, e il server ha il dovere di
            #    reggerla senza staccare (invariante I1).
            #
            # ⛔ E il buio si SCRIVE nel verbale: un fotogramma che non arriva
            #    perche' l'abbiamo buttato noi e uno che il server non ha
            #    spedito hanno lo stesso aspetto, se nessuno dichiara quale.
            self.buio_fino = 0.0
            self.buio_da = None
            self.buio_buttati = 0
            self.buio_fatto = False
            self.ritardo_s = 0.0
            self.ritardati = 0
            # ⛔⭐ IL CREDITO SI ANNUNCIA **QUI**, E NON DOPO LA STRETTA DI MANO.
            #
            #     `aioquic.asyncio.client.connect()` costruisce il protocollo —
            #     cioe' esegue questo `__init__` — e SOLO DOPO chiama
            #     `connect()`, che spedisce il ClientHello.  ⇒ Quel che si
            #     scrive qui finisce sul filo; quel che si scrive dopo non ci
            #     finisce **mai**, perche' `_serialize_transport_parameters()`
            #     legge `_local_max_streams_uni.value` una volta sola.
            #
            # ⛔ E scriverlo dopo non e' solo inutile: e' VIETATO.  RFC 9000
            #    §4.6 — un limite annunciato non si ritira.  Il banco che lo
            #    faceva contava 6 su un pari che ne credeva 128, chiudeva con
            #    `STREAM_LIMIT_ERROR` e dava la colpa al prodotto.
            #
            # ⚠ `_local_max_streams_uni` e' un campo PRIVATO di aioquic e si
            #   dichiara: `QuicConfiguration` non espone
            #   `initial_max_streams_uni`, e il predefinito della libreria e'
            #   128.  ⛔ Il numero non e' quel che resta a RCP: HTTP/3 si prende
            #   TRE stream unidirezionali appena la connessione nasce (§2.3,
            #   riquadro dei 19) e non li chiude mai.
            self.annunciato = None
            self.pinza_chiusa = False
            if caso == "credito":
                try:
                    q = self._quic
                    q._local_max_streams_uni.value = a.credito
                    q._local_max_streams_uni.sent = a.credito
                except Exception as e:  # noqa: BLE001
                    print(f"⛔ non ho potuto stringere il credito: {e}")
                    print("   ⚠ il caso «credito» NON provera' niente, e lo dice")
                else:
                    self._spia_il_clienthello()
                    if a.pinza:
                        self._chiudi_la_pinza()

        # ⭐⭐ LA SPIA — «la premessa si misura, non si crede».
        #     Non si CREDE che il credito sia finito nel ClientHello: si guarda
        #     il valore nell'istante in cui aioquic serializza i parametri di
        #     trasporto, che e' l'unico momento in cui quel campo tocca il filo.
        #     ⛔ Se aioquic cambiasse il nome di quella funzione la spia resta
        #        cieca e `annunciato` resta `None`: P6 dice NON PROVATO invece
        #        di dire verde a vuoto.
        def _spia_il_clienthello(self):
            q = self._quic
            vero = getattr(q, "_serialize_transport_parameters", None)
            if vero is None:
                return

            def spia():
                self.annunciato = q._local_max_streams_uni.value
                return vero()

            q._serialize_transport_parameters = spia

        # ⛔⭐ LA PINZA SUL RADDOPPIO, e senza di lei il credito NON si esaurisce
        #     mai — `[M]` 13 agosto 2026 dal banco 03-b18: `--credito 6` ⇒ 333
        #     stream video in 30 s, credito mai finito.
        #
        #     `aioquic/quic/connection.py:_write_connection_limits` fa:
        #         if limit.used * 2 > limit.value: limit.value *= 2
        #     cioe' RADDOPPIA il limite appena se ne consuma meta', e su
        #     loopback il rinnovo torna sempre prima che serva.  ⇒ Il caso di
        #     §2.3 non si presenta MAI e P6 resterebbe NON PROVATO per sempre.
        #
        # ⭐ E la pinza NON e' un rinnegamento: il valore annunciato non si
        #    tocca e non SCENDE mai.  Si impedisce soltanto che CRESCA — cioe'
        #    non si manda nessun `MAX_STREAMS`, che RFC 9000 permette a
        #    chiunque: aumentare un limite e' una facolta', non un obbligo.
        #    ⛔ La differenza fra le due mosse e' tutta qui, ed e' la differenza
        #       fra un banco che costruisce la scena e uno che bara.
        #
        # ⚠ Si lavora su una COPIA del limite: si passa a `_write_connection_
        #   limits` un gemello con `used = 0` (niente raddoppio) e
        #   `sent = value` (niente frame da mandare), e si rimette l'originale
        #   subito dopo.  Cosi' il contatore vero di aioquic resta intatto e la
        #   pinza si puo' aprire senza aver perso il conto.
        def _chiudi_la_pinza(self):
            from aioquic.quic.connection import Limit
            q = self._quic
            self.pinza_chiusa = True
            vero = q._write_connection_limits

            def con_la_pinza(builder, space):
                if not self.pinza_chiusa:
                    return vero(builder, space)
                salvo = q._local_max_streams_uni
                finto = Limit(frame_type=salvo.frame_type, name=salvo.name,
                              value=salvo.value)
                finto.sent = salvo.value
                finto.used = 0
                q._local_max_streams_uni = finto
                try:
                    return vero(builder, space)
                finally:
                    q._local_max_streams_uni = salvo

            q._write_connection_limits = con_la_pinza

        def datagram_received(self, data, addr):
            if time.monotonic() < self.buio_fino:
                self.buio_buttati += 1
                return
            # ⛔⭐ E IL RITARDO E' LO STRUMENTO GIUSTO PER §5.1, IL BUIO NO —
            #     cura del 13 agosto 2026, e la ragione e' che il buio ACCECA
            #     ANCHE IL BANCO.
            #
            #     Buttando i datagram, la coda del server si riempie e §5.1
            #     abbandona: ⛔ ma i byte di quel fotogramma li avevamo buttati
            #     noi, quindi il suo preambolo non e' mai arrivato e per il
            #     cliente **quello stream non e' mai esistito** — il
            #     `RESET_STREAM` gli piove addosso su uno stream che non
            #     conosce, e non lo sa attribuire.  `[M]` primo giro: due
            #     abbandoni dichiarati dal server, zero stream azzerati visti.
            #
            #     ⭐ Col RITARDO invece arriva tutto, solo piu' tardi: il
            #     cliente vede il preambolo e i 28 byte, il server intanto ha la
            #     coda piena perche' gli ACK tornano dopo, e quando ne parte uno
            #     piu' recente il vecchio viene azzerato **su uno stream che il
            #     cliente ha gia' visto**.  ⇒ E8 si prova sul filo.
            #
            # ⚠ E anche questa e' una condizione dichiarata dal modello:
            #   `SPECIFICHE.md` §8.1, «ritardo e perdita alti».
            if self.ritardo_s > 0:
                self.ritardati += 1
                asyncio.get_event_loop().call_later(
                    self.ritardo_s, self._consegna_dopo, data, addr)
                return
            super().datagram_received(data, addr)

        def _consegna_dopo(self, data, addr):
            try:
                super().datagram_received(data, addr)
            except Exception:  # noqa: BLE001
                pass

        def spegni_la_luce(self, secondi):
            self.buio_da = time.monotonic() - self.t0
            self.buio_fino = time.monotonic() + secondi
            self.buio_fatto = True

        def allunga_il_filo(self, ms):
            """La linea cattiva di `SPECIFICHE.md` §8.1, accesa a sessione
               aperta.

            ⛔ DOPO la stretta di mano, mai prima: un ritardo sul `CIAO`
               misurerebbe la pazienza di §4.6 invece del canale video.

            ⛔⭐ E QUI NON SI TOCCA PIU' IL CREDITO — cura del 13 agosto 2026.
                Fino a stamattina queste righe scrivevano
                `_local_max_streams_uni.value = a.credito` **dopo** la stretta
                di mano: un limite gia' annunciato che si ritira, che RFC 9000
                §4.6 vieta e che aioquic non rilegge nemmeno.  Adesso il credito
                si annuncia in `__init__`, cioe' prima che parta un byte, e qui
                resta soltanto quel che questo metodo ha sempre fatto davvero:
                allungare il filo.
            """
            self.buio_da = time.monotonic() - self.t0
            self.ritardo_s = ms / 1000.0
            self.buio_fatto = True

        WT_UNI = WT_UNI

        @staticmethod
        def _vint(b, i):
            if i >= len(b):
                return None, i
            n = 1 << (b[i] >> 6)
            if i + n > len(b):
                return None, i
            v = b[i] & 0x3F
            for k in range(1, n):
                v = (v << 8) | b[i + k]
            return v, i + n

        def _arrivano(self, sid, dati, fine):
            f = self.video.get(sid)
            if f is None:
                return
            f.arrivano(dati)
            if f.numero and f.numero > self.ultimo_numero:
                self.ultimo_numero = f.numero
            if fine:
                # ⛔ FIN: il fotogramma e' COMPLETO (§6.2).
                f.fine = "fin"
                f.finito_a = time.monotonic() - self.t0
                self.finiti.append(f)
                del self.video[sid]

        def _azzerato(self, sid):
            f = self.video.get(sid)
            if f is None:
                return
            # ⛔ RESET_STREAM: il fotogramma e' INCOMPLETO — si butta, non si
            #    consegna al decodificatore, e si tratta come un buco (§6.2).
            f.fine = "reset"
            f.finito_a = time.monotonic() - self.t0
            self.finiti.append(f)
            del self.video[sid]

        def _smista(self, event):
            sid = event.stream_id
            if sid in self.visti:
                self._arrivano(sid, event.data, event.end_stream)
                return True
            # 0b11 = unidirezionale, aperto dal server
            if (sid & 0x03) != 0x03 or sid == self.sessione:
                return False
            d = event.data
            if len(d) < 2 or d[0] != 0x40 or d[1] != self.WT_UNI:
                return False
            tipo, i = self._vint(d, 0)
            sessione, i = self._vint(d, i)
            if tipo != self.WT_UNI or sessione is None:
                return False
            self.visti.add(sid)
            self.video[sid] = Flusso(sid, time.monotonic() - self.t0)
            self._arrivano(sid, bytes(d[i:]), event.end_stream)
            return True

        def quic_event_received(self, event):
            nome = type(event).__name__
            if nome == "StreamDataReceived" and self._smista(event):
                return
            if nome == "StreamReset" and event.stream_id in self.visti:
                self._azzerato(event.stream_id)
                return
            super().quic_event_received(event)

        def chiedi_chiave(self):
            """⛔ §7.1: `RICHIEDI_CHIAVE(ultimo_numero)` sul canale di controllo."""
            self.chieste.append({"quando": time.monotonic() - self.t0,
                                 "dopo": self.ultimo_numero})
            self.manda(struct.pack("!HII", T_RICHIEDI_CHIAVE, 4,
                                   self.ultimo_numero))

    return Movimento


async def giro(a, caso):
    b3 = carica_b3()
    from aioquic.asyncio import connect
    from aioquic.h3.connection import H3_ALPN
    from aioquic.quic.configuration import QuicConfiguration

    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    if caso == "abbandono":
        # ⛔⭐ LA FINESTRA STRETTA, ED E' L'UNICO MODO DI PROVARE §5.1 SUL FILO.
        #
        #     L'abbandono avviene quando «ne e' gia' partito uno piu' recente» e
        #     il vecchio e' ancora fermo nella coda: su un loopback con la
        #     finestra predefinita la coda non si riempie mai, e il controllo
        #     direbbe NON PROVATO per sempre.
        #     ⚠ E non e' un guasto innestato nel prodotto: e' una CONDIZIONE DI
        #       RETE che il modello dichiara — `SPECIFICHE.md` §8.1, «mobile
        #       critico, sotto i 2 Mbps».  Il client ha diritto di annunciare
        #       questi numeri, e il server ha il dovere di reggerli.
        conf.max_data = a.finestra * 4
        conf.max_stream_data = a.finestra
    autorita = f"{a.indirizzo}:{a.porta}"
    Cliente = costruisci_cliente(a, caso)

    v = Verbale()
    # ⛔ Che cosa il banco VOLEVA annunciare: si dichiara prima di connettersi,
    #    cosi' se il giro muore nella stretta di mano la premessa e' comunque
    #    scritta nel verbale e P6 sa dire «non ho potuto guardare».
    v.credito_chiesto = a.credito if caso == "credito" else None
    async with connect(a.indirizzo, a.porta, configuration=conf,
                       create_protocol=Cliente) as cli:
        try:
            await asyncio.wait_for(cli.wait_connected(), timeout=10)
            # ⭐ E che cosa e' finito DAVVERO nel ClientHello, letto dalla spia.
            v.credito_annunciato = cli.annunciato
            cli.apri_sessione(autorita, a.percorso)
            stato = await asyncio.wait_for(cli.accettata, timeout=10)
            if stato != "200":
                v.caduta = f"la CONNECT estesa ha risposto {stato}"
                return v
            cli.apri_controllo()
            cli.codec_atteso = a.codec

            cli.manda(b3.inquadra(b3.T["CIAO"], b3.corpo_ciao()))
            await b3.attendi(cli, "ECCOMI")
            cli.manda(b3.inquadra(b3.T["CREDENZIALI"],
                                  b3.s(a.utente) + b3.s(a.parola)))
            # ⚠ 20 s e non 10: PAM ci mette il suo, e §4.4-bis aggiunge un
            #   secondo fisso.
            await b3.attendi(cli, "AMMESSO", attesa=25)
            cli.manda(b3.inquadra(b3.T["ATTACCA"],
                                  struct.pack("!IIII", a.larghezza, a.altezza,
                                              a.larghezza, a.altezza)
                                  + b3.s(a.disposizione)))
            _, corpo, _ = await b3.attendi(cli, "SESSIONE", attesa=15)
            v.tela = struct.unpack("!II", corpo[1:9])

            # ── si sta ad ascoltare, e si conta ────────────────────────────
            fine = time.monotonic() + a.attesa
            chiesto = 0
            while time.monotonic() < fine:
                await asyncio.sleep(0.05)
                if cli.caduta:
                    break
                # ⛔ `giro()` riceve sempre un caso CONCRETO, mai «tutti»: la
                #    prima stesura confrontava con «tutti» e la richiesta non
                #    partiva MAI, cosi' P3 usciva NON PROVATO su un prodotto che
                #    la serviva.  ⚠ Un controllo che non prova mai niente e uno
                #    rotto hanno la stessa faccia.
                if (caso in ("abbandono", "credito") and not cli.buio_fatto
                        and cli.ultimo_numero >= a.prima_di_chiedere):
                    if a.ritardo > 0:
                        cli.allunga_il_filo(a.ritardo)
                    else:
                        cli.spegni_la_luce(a.buio)
                if caso == "movimento" and chiesto < a.chiavi:
                    # ⛔ Si chiede DOPO che sono arrivati dei fotogrammi, e non
                    #    prima: §5.2 concede al server di ignorare una richiesta
                    #    che arrivi entro 200 ms dall'ultima chiave SPEDITA, e
                    #    chiedendo subito si misurerebbe la tolleranza invece
                    #    della cucitura.
                    if (cli.ultimo_numero >= a.prima_di_chiedere
                            and (chiesto == 0
                                 or time.monotonic() - ultima_chiesta > 1.5)):
                        cli.chiedi_chiave()
                        ultima_chiesta = time.monotonic()
                        chiesto += 1
            v.viva = cli.caduta is None
            v.caduta = cli.caduta
            v.buio = {"da": cli.buio_da,
                      "secondi": a.buio if (cli.buio_fatto and not a.ritardo) else 0,
                      "ritardo_ms": a.ritardo if cli.buio_fatto else 0,
                      "datagram_buttati": cli.buio_buttati,
                      "datagram_ritardati": cli.ritardati}
            v.flussi = list(cli.finiti)
            # ⛔ Gli stream ancora APERTI si dichiarano: uno stream che non e'
            #    ne' finito ne' azzerato quando il giro si chiude non e' un
            #    fotogramma perso — e' un fotogramma che stava arrivando.
            v.flussi += list(cli.video.values())
            v.chieste = list(cli.chieste)
        finally:
            cli.chiusa_da_noi = True
    return v


def leggi_registro(percorso, da_riga=0):
    """⛔ Tre esiti e non due: letto · non c'e' · non ho potuto leggerlo."""
    if not percorso:
        return "", "nessun registro dichiarato"
    try:
        with open(percorso, "r", errors="replace") as f:
            righe = f.read().splitlines()
    except OSError as e:
        return "", f"⛔ non ho potuto leggere {percorso}: {e}"
    return "\n".join(righe[da_riga:]), f"{len(righe) - da_riga} righe nuove"


def righe_registro(percorso):
    try:
        with open(percorso, "r", errors="replace") as f:
            return len(f.read().splitlines())
    except OSError:
        return 0


def scrivi_esito(a, rec):
    if not a.uscita:
        return True
    fuori = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "banco": "03-b15", "porta": a.porta,
             "scena": ("il desktop di «%s» sulla macchina di prova; se la scena "
                       "dello step 2 non e' accesa il conto e' quello di un "
                       "desktop fermo, e lo dice" % a.utente),
             # ⛔⭐ CHE COS'ERA IL PRODOTTO IN QUESTO GIRO.  Un file di esiti che
             #     mescola i giri sul prodotto SANO e quelli sul prodotto
             #     GUASTO senza dire quale e' quale mette due cose diverse sotto
             #     la stessa etichetta (forma E2), e i tre giri del metodo di
             #     casa diventano illeggibili il giorno dopo.
             "prodotto": a.nota or "⚠ NON DICHIARATO",
             "macchina": os.uname().nodename, "python": sys.version.split()[0]}
    fuori.update(rec)
    try:
        with open(a.uscita, "a") as f:
            f.write(json.dumps(fuori, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return True
    except OSError as e:
        print(f"⛔ l'esito NON si e' scritto in {a.uscita}: {e}")
        return False


CASI = {
    "movimento": ("la scena normale: si guarda per --attesa secondi e si conta. "
                  "Prova P1, P2, P3, P4"),
    "abbandono": ("finestra di flusso STRETTA, cosi' la coda del server si "
                  "riempie e §5.1 fa abbandonare i delta vecchi.  Prova P5"),
    "credito":   ("`initial_max_streams_uni` STRETTO, cosi' il server resta "
                  "senza stream da aprire.  Prova P6"),
}


def stampa_esiti(nome_caso, v, esiti):
    print(f"\n\033[1m== Il caso «{nome_caso}» — che cosa e' arrivato\033[0m")
    letti = v.finiti
    print(f"    --  {len(v.flussi)} stream video, {len(letti)} con "
          f"l'intestazione letta")
    if letti:
        n = sorted(x.numero for x in letti)
        chiavi = [x for x in letti if x.tipo == CHIAVE]
        reset = [x for x in v.flussi if x.fine == "reset"]
        durata = max(x.quando for x in letti) - min(x.quando for x in letti)
        print(f"    --  `numero` da {n[0]} a {n[-1]}, {len(chiavi)} chiavi, "
              f"{len(reset)} azzerati, {sum(x.byte_dati for x in letti)} byte")
        if durata > 0:
            print(f"    --  {len(letti) / durata:.1f} fotogrammi al secondo su "
                  f"{durata:.1f} s ⚠ e questo numero e' della SCENA quanto del "
                  f"prodotto (LEZIONI.md §1.1)")
    # ⭐ La premessa del caso «credito», MISURATA: e' la riga che il 13 agosto
    #    mancava, e senza la quale un rosso di P6 poteva essere il rosso di una
    #    scena mai esistita.
    if v.credito_chiesto is not None:
        print(f"    --  credito: chiesto {v.credito_chiesto}, annunciato sul "
              f"filo {v.credito_annunciato} (⛔ HTTP/3 se ne prende 3: a RCP ne "
              f"restano {(v.credito_annunciato or 0) - 3})")
    if v.buio and v.buio.get("ritardo_ms"):
        print(f"    --  ⚠ LINEA CATTIVA DICHIARATA: +{v.buio['ritardo_ms']} ms di "
              f"ritardo dal secondo {v.buio['da']:.1f}, "
              f"{v.buio['datagram_ritardati']} datagram ritardati dal CLIENTE "
              f"(SPECIFICHE.md §8.1)")
    elif v.buio and v.buio["secondi"]:
        print(f"    --  ⚠ BUIO DICHIARATO: {v.buio['secondi']} s a partire da "
              f"{v.buio['da']:.1f} s, {v.buio['datagram_buttati']} datagram "
              f"buttati dal CLIENTE (SPECIFICHE.md §8.1, linea cattiva)")
    if v.caduta:
        print(f"    \033[1;31mNO\033[0m  la sessione e' CADUTA: {v.caduta}")
    for nome, e in esiti:
        colore = {"VERDE": "\033[1;32mOK\033[0m", "ROSSO": "\033[1;31mNO\033[0m",
                  "NON PROVATO": "\033[1;33m??\033[0m"}[e.esito]
        print(f"    {colore}  {nome:<20} [{e.regola}]")
        print(f"          {e.dice}")


def principale():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--porta", type=int, default=7603,
                   help="⛔ la 7603, dello STEP 3.  7448/7501/7561 non si toccano")
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default="nicfio")
    p.add_argument("--parola", default="")
    p.add_argument("--parola-file", default="",
                   help="⛔ difetto D12: la parola non passa mai da argv")
    p.add_argument("--larghezza", type=int, default=1920)
    p.add_argument("--altezza", type=int, default=1080)
    p.add_argument("--disposizione", default="it")
    p.add_argument("--codec", type=int, default=1, help="1 = HEVC, 2 = AV1")
    p.add_argument("--attesa", type=float, default=10.0)
    p.add_argument("--minimo", type=int, default=8,
                   help="sotto questo numero di fotogrammi l'esito e' NON PROVATO")
    p.add_argument("--chiavi", type=int, default=2,
                   help="quante RICHIEDI_CHIAVE spedire nel giro")
    p.add_argument("--prima-di-chiedere", type=int, default=4,
                   help="quanti fotogrammi aspettare prima della prima richiesta")
    p.add_argument("--finestra", type=int, default=600,
                   help="il caso «abbandono»: max_stream_data annunciato.  ⛔ Il "
                        "predefinito e' MISURATO, non scelto: sotto la misura di "
                        "un fotogramma (i delta di questa scena stanno in ~800 "
                        "byte), cosi' l'intestazione esce e i dati no — che e' "
                        "l'unica scena in cui il RESET_STREAM si VEDE.  Con "
                        "24576 non succedeva niente e P5 restava NON PROVATA")
    p.add_argument("--ritardo", type=float, default=400.0,
                   help="i casi «abbandono» e «credito»: quanti ms di ritardo il "
                        "cliente aggiunge alla linea DOPO la stretta di mano.  "
                        "⛔ 0 = si usa il buio invece, che pero' acceca il banco")
    p.add_argument("--buio", type=float, default=2.0,
                   help="i casi «abbandono» e «credito»: per quanti secondi il "
                        "cliente BUTTA i datagram che arrivano — la linea "
                        "cattiva di SPECIFICHE.md §8.1")
    p.add_argument("--credito", type=int, default=6,
                   help="il caso «credito»: initial_max_streams_uni annunciato "
                        "⭐ PRIMA della stretta di mano (⛔ HTTP/3 se ne prende "
                        "TRE, §2.3, quindi con 6 ne restano 3 a RCP)")
    p.add_argument("--niente-pinza", dest="pinza", action="store_false",
                   help="⛔ il caso «credito»: NON impedire ad aioquic di "
                        "raddoppiare il limite appena se ne consuma meta' "
                        "(`_write_connection_limits`).  ⚠ Senza la pinza il "
                        "credito su loopback non si esaurisce quasi mai e P6 "
                        "esce NON PROVATO: si lascia per poterlo MISURARE, non "
                        "perche' sia un'alternativa")
    p.set_defaults(pinza=True)
    p.add_argument("--registro", default="",
                   help="il registro del server, per le righe che §5.1 e §2.3 "
                        "impongono")
    p.add_argument("--caso", default="tutti",
                   choices=["tutti", "movimento", "abbandono", "credito"])
    p.add_argument("--uscita", default="")
    p.add_argument("--nota", default="",
                   help="⛔ che cos'era il PRODOTTO in questo giro (sano, o con "
                        "quale ago innestato): finisce in ogni riga di "
                        "`--uscita`.  ⚠ Senza, i tre giri del metodo di casa — "
                        "sano, guasto, risanato — sono indistinguibili nel file")
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--elenco", action="store_true")
    a = p.parse_args()

    if a.elenco:
        print(__doc__)
        print("I sei controlli:")
        for nome, _, che_cosa in CONTROLLI:
            print(f"  {nome:<20} {che_cosa}")
        print("\nI tre casi dal vivo:")
        for nome, che_cosa in CASI.items():
            print(f"  {nome:<20} {che_cosa}")
        return 0

    falle, righe_cert = certifica(a)
    scrivi_esito(a, {"tipo": "certificazione", "falle": falle,
                     "righe": righe_cert, "esito": falle == 0})
    if falle:
        print("\n⛔ Non punto un banco non certificato sull'incognita: un rosso "
              "sarebbe ambiguo\n   fra «il prodotto non funziona» e «il banco "
              "non funzionava» (LEZIONI.md §1.2).")
        return 2
    if a.certifica:
        return 0

    # ⛔ La parola: preferita da file, e un file vuoto NON e' una parola vuota.
    parola = a.parola
    if a.parola_file:
        try:
            with open(a.parola_file) as f:
                parola = f.read().strip("\n")
        except OSError as e:
            print(f"⛔ non ho letto la parola da {a.parola_file}: {e}")
            return 2
        if not parola:
            print(f"⛔ {a.parola_file} e' VUOTO: non e' «la parola e' vuota»")
            return 2
    elif parola:
        print("⚠ la parola e' arrivata da argv (difetto D12): il giro prosegue, "
              "e lo dichiara")
    a.parola = parola

    casi = ["movimento", "abbandono", "credito"] if a.caso == "tutti" else [a.caso]
    conto = {"verde": 0, "rosso": 0, "non_provato": 0}
    tutti_esiti = []

    for caso in casi:
        da = righe_registro(a.registro) if a.registro else 0
        try:
            v = asyncio.run(giro(a, caso))
        except Exception as e:  # noqa: BLE001
            print(f"\n\033[1;31mNO\033[0m  il caso «{caso}» non e' arrivato in "
                  f"fondo: {type(e).__name__}: {e}")
            conto["rosso"] += 1
            tutti_esiti.append({"caso": caso, "guasto": f"{type(e).__name__}: {e}"})
            continue
        v.registro, quante = leggi_registro(a.registro, da)
        print(f"\n    --  registro del server: {quante}")

        esiti = []
        for nome, fn, _ in CONTROLLI:
            # ⛔ Ogni caso e' costruito per provare certe proprieta': le altre
            #    restano NON PROVATE, e non si spacciano per verdi.
            if caso == "abbandono" and nome not in ("P1-numeri", "P5-abbandono",
                                                    "P4-secondo"):
                continue
            if caso == "credito" and nome not in ("P6-credito", "P4-secondo"):
                continue
            if caso == "movimento" and nome in ("P5-abbandono", "P6-credito"):
                continue
            e = fn(v, a.minimo) if fn is p1_numeri else fn(v)
            esiti.append((nome, e))
        stampa_esiti(caso, v, esiti)
        for nome, e in esiti:
            conto["verde" if e.esito == VERDE
                  else "rosso" if e.esito == ROSSO else "non_provato"] += 1
        tutti_esiti.append({"caso": caso, "verbale": v.come_dizionario(),
                            "controlli": {n: e.come_dizionario() for n, e in esiti}})

    print(f"\n\033[1m== Il conto\033[0m")
    print(f"    {conto['verde']} verdi · {conto['rosso']} rossi · "
          f"{conto['non_provato']} NON PROVATI")
    print("    ⚠ «non provato» non e' «passato»: e' un controllo a cui la scena "
          "non ha dato\n      niente da giudicare, e va letto come un buco nella "
          "misura.")
    scrivi_esito(a, {"tipo": "giro", "casi": casi, "conto": conto,
                     "esiti": tutti_esiti,
                     "esito": conto["rosso"] == 0})
    return 1 if conto["rosso"] else 0


if __name__ == "__main__":
    sys.exit(principale())
