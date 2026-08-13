#!/usr/bin/env python3
"""03-b18-credito.py — il banco del CREDITO DEGLI STREAM (`RCP.md` §2.3).

  python3 03-b18-credito.py --certifica     ⭐ PRIMA di ogni misura — gira su CHUWI
  python3 03-b18-credito.py --elenco        che cosa prova, e come
  python3 03-b18-credito.py --porta 7607 --caso tutti

⛔ IL GIRO DAL VIVO gira DENTRO IL CONTENITORE (192.168.0.2): aioquic sta li'.
   ⭐ `--certifica` e `--elenco` girano anche su CHUWI, ed e' voluto: chi
   revisiona il banco prima del prodotto non ha il contenitore.
   ⚠ La porta e' la **7607**, di questo gruppo.  ⛔ 7448, 7501 e 7561 non si
   toccano; 7603 e 7605 sono di altri gruppi.

===========================================================================
⛔⭐ PERCHE' QUESTO BANCO ESISTE, E NON E' «P6 rifatto»

Il 13 agosto 2026 il caso «credito» di `03-b15-movimento.py` ha dichiarato un
rosso su §2.3: la sessione moriva con `STREAM_LIMIT_ERROR` — «Too many streams
open» — dopo che il server aveva aperto 11 stream unidirezionali.  Il banco
dichiaro' `[?]` di chi fosse il conto sbagliato, **ngtcp2 che concede troppo o
aioquic che conta male**, e fece bene a non indovinare.

⭐ **La misura del 13 agosto dice: nessuno dei due.**  Il caso «credito» di quel
   banco crede di annunciare `initial_max_streams_uni = 6` e **non lo annuncia
   mai**: scrive `_local_max_streams_uni.value` DOPO la stretta di mano, e
   aioquic quel campo lo legge **una volta sola**, quando costruisce il
   ClientHello (`quic/connection.py:2880`).  Sul filo va il predefinito **128**.
   ⇒ Il banco **rinnegava** un credito gia' concesso — che RFC 9000 §4.6 vieta —
   e poi accusava il prodotto di non reggerlo.

⛔ DA CUI LA PRIMA REGOLA DI QUESTO FILE, e vale piu' di tutti i suoi controlli:

    **la premessa del banco si MISURA, non si crede.**

   Il controllo `C1-annuncio` non guarda il prodotto: guarda **il banco**, e
   chiede al filo quanto credito e' stato annunciato davvero.  ⚠ Senza di lui
   ogni altro rosso di questo file varrebbe zero, perche' potrebbe essere il
   rosso di una scena che non e' mai esistita — che e' precisamente quel che e'
   successo il 13 agosto.

===========================================================================
⛔ CHE COSA PROVA, E IL SINTOMO CHE OGNI ROSSO NOMINA

  C1  ⭐ **la premessa**: il credito che il banco crede di annunciare e' quello
      che e' finito sul filo.  ⛔ Il rosso qui accusa IL BANCO, non il prodotto,
      ed e' l'unico controllo di questo file che lo fa.
  C2  il credito si **esaurisce davvero**: il server ha voluto piu' stream di
      quanti il pari ne concede.  ⛔ Senza, «regge il rifiuto» non e' provato —
      non si dimostra un rifiuto senza un rifiuto, e l'esito e' NON PROVATO.
  C3  il server **regge**: la sessione e' viva alla fine, non e' morta con
      `STREAM_LIMIT_ERROR`, e ⛔ **nessuna CHIAVE e' stata buttata** — §5.2 lo
      vieta con un ⛔, e §2.3 dice che la chiave si aspetta e il delta si butta.
  C4  l'abbandono per credito **finisce nel registro** e **si distingue** da
      quello per fotogramma vecchio (§5.1).  ⛔ E' la forma d'errore E8: un
      fotogramma perso in silenzio e uno abbandonato di proposito hanno lo
      stesso aspetto dal lato che riceve, e due abbandoni per due ragioni
      diverse che si scrivessero uguale sarebbero la stessa cecita' un piano
      piu' sotto.
  C5  ⭐ **il controllo negativo**: col credito ABBONDANTE non scatta niente.
      ⛔ Senza di lui, un prodotto che scrivesse la riga di §2.3 a ogni
      fotogramma passerebbe C2, C3 e C4 tutti e tre.
  C6  ⛔⭐ **la CURA**: dopo un delta saltato per posto il server prepara una
      CHIAVE (§5.2).  E' il difetto **B-18**, trovato il 13 agosto 2026, e
      **nessuno degli altri cinque lo vede**: la sessione regge, il registro
      dice tutto, nessuna chiave viene buttata — e intanto al decodificatore
      manca un delta che non tornera' mai.  ⚠ Il client non puo' nemmeno
      chiedere la cura: §6.2 vieta di consumare il `numero` per un fotogramma
      mai spedito, quindi nei numeri **non resta nessun buco**, e col GOP
      infinito del prodotto un'altra chiave non arriverebbe mai piu'.
      ⇒ Un solo delta saltato, e lo schermo resta rotto **per sempre e in
        silenzio**, con cinque controlli su sei verdi.

===========================================================================
⛔⭐ COME SI CERTIFICA — TRE GIRI E NON DUE

`LEZIONI.md` §1.2 ne chiede due: un verbale sano che deve dire VERDE, uno
guasto che deve dire ROSSO **nominando la propria regola**.  ⭐ Qui ce n'e' un
**terzo**, e non e' pignoleria:

    sano  →  guasto  →  **risanato**

Il terzo giro prende **il verbale guasto** e gli **toglie l'ago**, e il
controllo deve tornare VERDE.  ⛔ Con due soli giri, un controllo che dicesse
rosso per una ragione qualunque presente nel verbale guasto — e non per l'ago —
sembrerebbe sano: il verde del primo giro e il rosso del secondo tornerebbero
tutti e due.  Il terzo giro e' l'unico che **attribuisce** il rosso all'ago,
ed e' la stessa differenza che passa fra «so perche' succede» e «so fermarlo»
(`LEZIONI.md` §1.11).

⚠ E il risanamento si fa **sul guasto**, mai riusando il verbale sano: sarebbe
  il primo giro rifatto, e non proverebbe niente.
"""
import argparse
import copy
import importlib.util
import json
import os
import ssl
import struct
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ aioquic si importa TARDI, dentro le funzioni che lo usano: `--elenco` e
#    `--certifica` devono poter girare su CHUWI, dove aioquic non c'e'.
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


INTESTAZIONE = 28
CHIAVE, DELTA = 0x0301, 0x0302
WT_UNI = 0x54
T_RICHIEDI_CHIAVE = 0x000D

# ⛔ I TRE DI HTTP/3, e il numero e' normativo: `RCP.md` §2.3 (riquadro dei 19)
#    dice che HTTP/3 si prende lo stream di controllo e i due di QPACK appena la
#    connessione nasce, e **non li chiude mai**.  ⚠ Il riquadro dichiara anche
#    `[?]` che su un browser potrebbero essere di piu' — uno stream di *grease*
#    —, quindi questo numero e' un'ATTESA, e C1 lo confronta con quel che ha
#    contato davvero invece di darlo per buono.
UNI_DI_HTTP3 = 3

VERDE, ROSSO, NON_PROVATO = "VERDE", "ROSSO", "NON PROVATO"


class Esito:
    """Il verdetto di UN controllo.  Tre stati e non due."""

    def __init__(self, esito, regola, dice, numeri=None):
        self.esito, self.regola, self.dice = esito, regola, dice
        self.numeri = numeri or {}

    @property
    def verde(self):
        return self.esito == VERDE

    def come_dizionario(self):
        return {"esito": self.esito, "regola": self.regola, "dice": self.dice,
                "numeri": self.numeri}


class Verbale:
    """La trascrizione di quel che e' arrivato sul filo, piu' il registro.

    ⛔ E' la STESSA struttura che esce dal giro dal vivo e che la certificazione
       fabbrica a mano: una struttura finta parallela sarebbe «il banco misura
       il banco».
    """

    def __init__(self):
        # ⭐ La premessa, misurata: quanto credito il CLIENTE ha messo davvero
        #    nel ClientHello (letto al momento in cui aioquic serializza i
        #    parametri di trasporto), e quanto credeva di metterne.
        self.credito_chiesto = None
        self.credito_annunciato = None
        # Gli stream unidirezionali che il SERVER ha aperto, in ordine.
        self.stream_aperti = []
        # I fotogrammi arrivati interi, e quelli azzerati.
        self.finiti = []
        self.azzerati = []
        # Lo stato della sessione alla fine del giro.
        self.viva = True
        self.caduta = None
        # Il registro del server, riga per riga.
        self.registro = ""
        # ⛔ Quanti fotogrammi non sono partiti per mancanza di posto.  Si
        #    inizializza QUI e non solo nei verbali fabbricati: un attributo che
        #    esiste solo quando qualcuno si ricorda di scriverlo fa crollare il
        #    controllo con un `AttributeError`, e un banco che crolla e un banco
        #    che dice verde si assomigliano troppo.
        self.saltati_per_posto = 0
        self.minimo_raggiunto = True


# --------------------------------------------------------------------------
# ⭐ I CINQUE CONTROLLI.  Funzioni pure sul verbale, e nient'altro: e' quel che
#    permette alla certificazione di girare senza rete, senza contenitore e
#    senza prodotto.

def righe_credito(v):
    """Le righe che il prodotto scrive quando il posto manca (§2.3).

    ⛔ Il testo lo scrive `src/rcp.c` in `rcp_video_niente_credito()`, e le due
       marche insieme — «§2.3» e «stream unidirezionale» — sono quel che
       distingue questa riga da ogni altra che citi §2.3.
    """
    return [r for r in v.registro.splitlines()
            if "§2.3" in r and "stream unidirezionale" in r]


def righe_abbandono_vecchio(v):
    """Le righe dell'abbandono di §5.1 — «ne e' partito uno piu' recente».

    ⚠ Sono un'ALTRA cosa dalle righe di §2.3, e C4 esiste per non lasciarle
      confondere: li' lo stream era nato e si azzera, qui non e' mai nato.
    """
    return [r for r in v.registro.splitlines() if "ABBANDONATO (§5.1)" in r]


def c1_annuncio(v):
    """⭐ LA PREMESSA — e il rosso qui accusa IL BANCO, non il prodotto."""
    if v.credito_chiesto is None:
        return Esito(NON_PROVATO, "il banco stesso",
                     "questo giro non stringeva il credito: non c'e' nessuna "
                     "premessa da verificare")
    if v.credito_annunciato is None:
        # ⛔ «Non ho guardato» non e' «e' andato bene» (`LEZIONI.md` §1.9).
        return Esito(NON_PROVATO, "il banco stesso",
                     "non ho letto che cosa sia finito nel ClientHello: la spia "
                     "su `_serialize_transport_parameters` non ha catturato "
                     "niente, e senza di lei ogni altro rosso di questo file "
                     "non varrebbe niente")
    if v.credito_annunciato != v.credito_chiesto:
        return Esito(ROSSO, "il banco stesso",
                     f"⛔ IL BANCO MENTE: credeva di annunciare "
                     f"`initial_max_streams_uni = {v.credito_chiesto}` e sul "
                     f"filo ne ha annunciati {v.credito_annunciato}.  E' il "
                     f"difetto del 13 agosto 2026 — un credito RINNEGATO dopo "
                     f"la stretta di mano invece che annunciato prima — e "
                     f"finche' resta, ogni rosso su §2.3 accusa il prodotto di "
                     f"una scena che non e' mai esistita",
                     {"chiesto": v.credito_chiesto,
                      "annunciato": v.credito_annunciato})
    return Esito(VERDE, "il banco stesso",
                 f"il credito annunciato sul filo e' quello chiesto "
                 f"({v.credito_annunciato}): la scena di questo giro esiste "
                 f"davvero, e i rossi qui sotto valgono",
                 {"annunciato": v.credito_annunciato})


def c2_esaurito(v):
    """Il credito si e' esaurito DAVVERO — altrimenti non si e' provato niente."""
    if v.credito_annunciato is None:
        return Esito(NON_PROVATO, "RCP.md §2.3",
                     "senza sapere quanto credito e' stato annunciato non so "
                     "dire se si sia esaurito")
    # ⛔ Il conto che separa il totale da quel che resta a RCP: HTTP/3 si prende
    #    i suoi e non li restituisce (§2.3, riquadro dei 19).
    per_rcp = v.credito_annunciato - UNI_DI_HTTP3
    righe = righe_credito(v)
    if not righe:
        return Esito(NON_PROVATO, "RCP.md §2.3",
                     f"il posto non e' MAI mancato in questo giro (il pari ne "
                     f"concedeva {v.credito_annunciato}, cioe' {per_rcp} a RCP, "
                     f"e il server ha aperto {len(v.stream_aperti)} stream): la "
                     f"scena non ha provato niente.  ⛔ Non e' un verde — «regge "
                     f"il rifiuto» non si dimostra senza un rifiuto",
                     {"righe": 0, "aperti": len(v.stream_aperti),
                      "per_rcp": per_rcp})
    return Esito(VERDE, "RCP.md §2.3",
                 f"il posto e' mancato {len(righe)} volte con {per_rcp} stream "
                 f"disponibili a RCP: il rifiuto c'e' stato, e i controlli che "
                 f"seguono hanno qualcosa da giudicare",
                 {"righe": len(righe), "per_rcp": per_rcp})


def c3_regge(v):
    """⛔ §2.3 — «il server DEVE reggere il rifiuto invece di considerarlo un
       errore fatale», e §5.2 vieta di buttare una CHIAVE."""
    if not righe_credito(v):
        return Esito(NON_PROVATO, "RCP.md §2.3",
                     "il posto non e' mai mancato: non c'e' nessun rifiuto da "
                     "reggere")
    # ⛔ La sessione caduta si giudica PRIMA di tutto: e' il rosso che il 13
    #    agosto il banco non vedeva perche' guardava solo il registro.
    if v.caduta:
        return Esito(ROSSO, "RCP.md §2.3",
                     f"la sessione e' CADUTA mentre il posto mancava: "
                     f"«{v.caduta}».  ⛔ §2.3 dice che il server DEVE reggere il "
                     f"rifiuto di aprire uno stream invece di considerarlo un "
                     f"errore fatale — e qui non lo regge",
                     {"caduta": v.caduta})
    if not v.viva:
        return Esito(ROSSO, "RCP.md §2.3",
                     "il posto e' mancato e la sessione non era piu' viva alla "
                     "fine del giro: ⛔ §2.3 vuole che il rifiuto NON sia un "
                     "errore fatale",
                     {"viva": False})
    # ⛔ §5.2 con un ⛔: «il server NON DEVE abbandonare un fotogramma chiave».
    #    §2.3 lo ripete dal suo lato — la chiave si aspetta, il delta si butta —
    #    ed e' il rilievo R1.9, che nacque da due righe normative opposte.
    buttate = [r for r in righe_credito(v)
               if "CHIAVE" in r and "si BUTTA" in r]
    if buttate:
        return Esito(ROSSO, "RCP.md §5.2",
                     f"{len(buttate)} CHIAVI sono state buttate per mancanza di "
                     f"posto: ⛔ §5.2 lo vieta — «abbandonare la cura non e' una "
                     f"cura» — e §2.3 vuole che la chiave si ASPETTI mentre il "
                     f"delta si butta",
                     {"chiavi_buttate": len(buttate)})
    return Esito(VERDE, "RCP.md §2.3, §5.2",
                 f"il posto e' mancato {len(righe_credito(v))} volte, la "
                 f"sessione e' rimasta viva e nessuna chiave e' stata buttata: "
                 f"il rifiuto e' stato retto",
                 {"righe": len(righe_credito(v)), "viva": True})


def c4_registro(v):
    """§5.1 e §2.3 — l'abbandono si SCRIVE, e i due abbandoni si DISTINGUONO."""
    per_credito = righe_credito(v)
    per_vecchio = righe_abbandono_vecchio(v)
    if not v.registro:
        return Esito(NON_PROVATO, "RCP.md §2.3",
                     "il registro del server non e' stato letto: «non ho "
                     "guardato» non e' «non e' successo»")
    # Il posto e' mancato sul filo (il server ha smesso di aprire stream) e il
    # registro non lo dice?  ⛔ E' esattamente la meta' che manca.
    if v.saltati_per_posto and not per_credito:
        return Esito(ROSSO, "RCP.md §2.3",
                     f"{v.saltati_per_posto} fotogrammi non sono partiti per "
                     f"mancanza di posto e il registro NON contiene nessuna "
                     f"riga di §2.3: ⛔ l'obbligo di registro copre anche il "
                     f"caso in cui lo stream non e' MAI nato — senza, lo schermo "
                     f"si ferma e nessuna riga dice perche' (rilievo R1.9)",
                     {"saltati": v.saltati_per_posto, "righe": 0})
    if not per_credito:
        return Esito(NON_PROVATO, "RCP.md §2.3",
                     "nessun abbandono per mancanza di posto in questo giro: non "
                     "c'e' niente da distinguere")
    # ⛔⭐ LA DISTINZIONE, che e' il mestiere vero di questo controllo.
    #     Due abbandoni per due ragioni diverse devono leggersi diversi: se le
    #     righe di §2.3 si confondessero con quelle di §5.1, chi diagnostica
    #     leggerebbe «il server abbandona» e non saprebbe se il collo di
    #     bottiglia e' il CREDITO o la CODA — due cure opposte.
    confuse = [r for r in per_credito if "ABBANDONATO (§5.1)" in r]
    if confuse:
        return Esito(ROSSO, "RCP.md §5.1",
                     f"{len(confuse)} righe portano insieme le marche di §2.3 e "
                     f"di §5.1: ⛔ l'abbandono per mancanza di posto e quello "
                     f"per fotogramma vecchio NON si distinguono piu', e sono "
                     f"due guasti con due cure opposte — il credito e la coda",
                     {"confuse": len(confuse)})
    return Esito(VERDE, "RCP.md §2.3, §5.1",
                 f"{len(per_credito)} abbandoni per mancanza di posto e "
                 f"{len(per_vecchio)} per fotogramma vecchio, e le due ragioni "
                 f"si leggono separate nel registro",
                 {"per_credito": len(per_credito),
                  "per_vecchio": len(per_vecchio)})


def c5_abbondante(v):
    """⭐ IL CONTROLLO NEGATIVO — col credito abbondante non scatta niente."""
    if v.credito_chiesto is not None:
        return Esito(NON_PROVATO, "RCP.md §2.3",
                     "questo giro stringeva il credito: il controllo negativo "
                     "vuole il giro col credito ABBONDANTE")
    righe = righe_credito(v)
    if righe:
        return Esito(ROSSO, "RCP.md §2.3",
                     f"col credito abbondante il server ha scritto lo stesso "
                     f"{len(righe)} righe di «non c'e' posto»: ⛔ o il conto del "
                     f"posto e' sbagliato, o quelle righe le scrive sempre — e "
                     f"in tutt'e due i casi i verdi di C2, C3 e C4 non "
                     f"varrebbero niente",
                     {"righe": len(righe)})
    if not v.finiti:
        return Esito(NON_PROVATO, "RCP.md §2.3",
                     "col credito abbondante non e' arrivato nessun fotogramma: "
                     "l'assenza di righe di §2.3 non prova niente, perche' non "
                     "e' partito niente")
    return Esito(VERDE, "RCP.md §2.3",
                 f"col credito abbondante sono arrivati {len(v.finiti)} "
                 f"fotogrammi e il server non ha mai detto «non c'e' posto»: le "
                 f"righe di §2.3 le scrive quando serve, non sempre",
                 {"fotogrammi": len(v.finiti), "righe": 0})


# ⛔⭐ I TRE MODI IN CUI IL PRODOTTO DICE «LA CURA E' ARMATA» — e il primo giro
#     dal vivo ha dimostrato che il marcatore scelto a tavolino era il piu' raro
#     dei tre.  `[M]` 13 agosto 2026, sera, giro «stretto» dal vivo:
#
#         «§5.2 vuole una CHIAVE — richiesta girata al palco»   155 righe
#         «⛔ FOTOGRAMMA NON SPEDITO: e' un delta e §5.2 vuole»    2 righe
#
#     ⇒ C6 guardava SOLO la seconda forma e ha dato ROSSO al prodotto dicendo
#     «non ha MAI preparato una CHIAVE», mentre il registro conteneva 155 righe
#     che dicono il contrario e 28 righe «⛔ §2.3: nessuno stream
#     unidirezionale per una CHIAVE … il debito resta acceso».
#
# ⛔ E LA RAGIONE E' STRUTTURALE, non una svista: la riga «FOTOGRAMMA NON
#    SPEDITO» la scrive `rcp_video_apri()` quando CHI CHIAMA offre un delta
#    mentre il debito e' acceso — cioe' solo quando il chiamante NON ha chiesto
#    `rcp_video_serve_chiave()` prima di codificare.  ⇒ Su un prodotto che si
#    comporta bene quella riga NON compare quasi mai, e un controllo che
#    pretende di vederla e' rosso proprio sul prodotto sano.  ⚠ E' la forma
#    peggiore: un marcatore che si accende SOLO sul comportamento sbagliato del
#    chiamante, usato come prova del comportamento giusto del server.
CURA_ARMATA = (
    # ⭐ La piu' forte: il debito e' acceso E ha raggiunto il codificatore
    #    (`src/webtransport.c:1352`, dietro `rcp_video_serve_chiave()`).
    "richiesta girata al palco",
    # Il server sta offrendo una CHIAVE e il posto manca: §2.3 dice che la
    # chiave si ASPETTA, e il debito resta acceso (`src/rcp.c`, ramo `chiave`).
    "il debito resta acceso",
    # La forma rara: un delta offerto mentre il debito era gia' acceso.
    "FOTOGRAMMA NON SPEDITO",
)


def righe_debito_chiave(v):
    """Le righe che dicono che la CURA e' stata armata (§5.2).

    ⛔ Il debito lo accende `src/rcp.c` in `rcp_video_niente_credito()`
       (`serve_chiave_perche = "un delta e' stato saltato per mancanza di posto
       (§2.3)…"`), e nel registro riesce in TRE forme diverse — vedi il riquadro
       qui sopra.  ⚠ Pretenderne una sola era un rosso falso.
    """
    return [r for r in v.registro.splitlines()
            if any(m in r for m in CURA_ARMATA)]


def c6_cura(v):
    """⛔⭐ §5.2 — DOPO un delta saltato per posto, il server DEVE preparare una
       CHIAVE.  E' il difetto B-18, e nessun altro controllo lo vede.

    ⛔ PERCHE' QUESTO CONTROLLO ESISTE, e perche' C3 non basta.

       C3 chiede che la sessione REGGA, e regge: nessuno muore.  Ma il danno
       vero e' invisibile da li' — al decodificatore manca un delta e da quel
       momento produce immagini via via piu' sfasciate, **senza sollevare
       nessun errore**.  ⚠ E il client non se ne accorge nemmeno: §6.2 vieta di
       consumare il `numero` per un fotogramma mai spedito, quindi nei numeri
       non resta nessun buco — che e' l'unico segnale su cui §5.2 gli fa
       chiedere una chiave.  Col GOP infinito del prodotto un'altra chiave non
       arriverebbe mai piu'.
       ⇒ Un solo delta saltato per posto, e lo schermo resta rotto PER SEMPRE
         mentre tutti e cinque gli altri controlli dicono verde.
    """
    per_credito = [r for r in righe_credito(v) if "delta" in r]
    if not v.registro:
        return Esito(NON_PROVATO, "RCP.md §5.2",
                     "il registro del server non e' stato letto")
    if not per_credito:
        return Esito(NON_PROVATO, "RCP.md §5.2",
                     "nessun delta e' stato saltato per mancanza di posto: non "
                     "c'e' nessuna cura da armare")
    if not righe_debito_chiave(v):
        return Esito(ROSSO, "RCP.md §5.2",
                     f"{len(per_credito)} delta sono stati saltati per mancanza "
                     f"di posto e il server NON ha mai preparato una CHIAVE: ⛔ "
                     f"§5.2 gliela impone — «senza aspettare che il client lo "
                     f"chieda» — e qui il client non puo' nemmeno chiederla, "
                     f"perche' nei numeri non resta nessun buco.  ⚠ La cura non "
                     f"e' stata armata: l'immagine resta rotta per sempre e in "
                     f"silenzio",
                     {"saltati": len(per_credito), "chiavi_armate": 0,
                      "cercate": list(CURA_ARMATA)})
    armate = righe_debito_chiave(v)
    quali = sorted({m for m in CURA_ARMATA
                    if any(m in r for r in armate)})
    return Esito(VERDE, "RCP.md §5.2",
                 f"{len(per_credito)} delta saltati per mancanza di posto, e il "
                 f"server ha preparato la CHIAVE che §5.2 gli impone "
                 f"({len(armate)} righe, marcatori: {', '.join(quali)}): la "
                 f"cura e' ARMATA.  ⚠ E «armata» non e' «arrivata»: che sul filo "
                 f"il primo fotogramma dopo il ritorno del posto sia davvero "
                 f"una CHIAVE 0x0301 lo prova `03-b18b-cura.py` (V4), che il "
                 f"credito lo RILASCIA — questo banco non lo rilascia mai",
                 {"saltati": len(per_credito), "chiavi_armate": len(armate),
                  "marcatori": quali})


CONTROLLI = [
    ("C1-annuncio", c1_annuncio,
     "⭐ la premessa: il credito annunciato e' quello chiesto"),
    ("C2-esaurito", c2_esaurito, "il credito si esaurisce DAVVERO"),
    ("C3-regge", c3_regge, "il server regge il rifiuto e non butta chiavi"),
    ("C4-registro", c4_registro,
     "l'abbandono per credito e' nel registro e si distingue"),
    ("C5-abbondante", c5_abbondante,
     "⭐ il controllo negativo: col credito abbondante non scatta niente"),
    ("C6-cura", c6_cura,
     "⛔ dopo un delta saltato per posto, il server prepara una CHIAVE (§5.2)"),
]


# --------------------------------------------------------------------------
# ⛔ LA CERTIFICAZIONE — tre giri, e il terzo e' quello che attribuisce.

REG_CREDITO_DELTA = ("⚠ §2.3: nessuno stream unidirezionale per il delta che "
                     "veniva dopo il 41 (il client ne concede ancora 0): il "
                     "delta si BUTTA")
REG_CREDITO_CHIAVE = ("⛔ §2.3: nessuno stream unidirezionale per una CHIAVE "
                      "(il client ne concede ancora 0).  ⚠ La chiave NON si "
                      "butta")
REG_CURA = ("⛔ FOTOGRAMMA NON SPEDITO: e' un delta e §5.2 vuole una CHIAVE "
            "(un delta e' stato saltato per mancanza di posto (§2.3), e nei "
            "numeri non resta nessun buco)")
# ⭐ Le due forme che il prodotto scrive DAVVERO, copiate dal registro del 13
#    agosto 2026 sera.  ⛔ Stanno qui perche' la certificazione deve provare che
#    C6 le riconosce: un controllo certificato su una forma che il prodotto non
#    scrive quasi mai e' un controllo certificato su niente — ed e' l'errore che
#    ha prodotto il rosso falso di questo banco al suo primo giro dal vivo.
REG_CURA_PALCO = ("[127.0.0.1]:35522: §5.2 vuole una CHIAVE — richiesta girata "
                  "al palco di «nicfio» (codec 1)")
REG_CURA_DEBITO = ("⛔ §2.3: nessuno stream unidirezionale per una CHIAVE (il "
                   "client ne concede ancora 0).  ⚠ La chiave NON si butta: "
                   "§5.2 la vuole, il debito resta acceso e si riprova al "
                   "prossimo fotogramma")
REG_VECCHIO = ("fotogramma 37 ABBANDONATO (§5.1) dopo 210 byte su 800, stream "
               "51, perche': ne e' partito uno piu' recente (§5.1)")


def _verbale_sano():
    """Un giro col credito STRETTO e onestamente annunciato, andato bene."""
    v = Verbale()
    v.credito_chiesto = 6
    v.credito_annunciato = 6
    v.stream_aperti = [15, 19, 23]
    v.finiti = [{"numero": n} for n in range(1, 12)]
    v.azzerati = [{"numero": 37}]
    v.viva = True
    v.caduta = None
    v.saltati_per_posto = 9
    v.registro = "\n".join([REG_CREDITO_DELTA, REG_CURA, REG_VECCHIO,
                            REG_CREDITO_DELTA])
    return v


def _verbale_sano_abbondante():
    """Il gemello col credito ABBONDANTE — la scena di C5."""
    v = Verbale()
    v.credito_chiesto = None
    v.credito_annunciato = 128
    v.stream_aperti = list(range(15, 15 + 4 * 40, 4))
    v.finiti = [{"numero": n} for n in range(1, 41)]
    v.azzerati = []
    v.viva = True
    v.caduta = None
    v.saltati_per_posto = 0
    v.registro = REG_VECCHIO
    return v


def _aghi():
    """Per ogni controllo: come si GUASTA il verbale, e come si RISANA.

    ⛔ `risana` lavora sul verbale GUASTO, non sul sano: e' il terzo giro, ed e'
       l'unico che attribuisce il rosso all'ago invece che al verbale.
    """
    def g_c1(v):
        # Il gesto del 13 agosto: si crede di annunciare 6, sul filo va 128.
        v.credito_annunciato = 128
    def r_c1(v):
        v.credito_annunciato = v.credito_chiesto

    def g_c2(v):
        # Il posto non e' mai mancato: niente righe di §2.3.
        v.registro = REG_VECCHIO
        v.saltati_per_posto = 0
    def r_c2(v):
        v.registro = "\n".join([REG_CREDITO_DELTA, REG_CURA, REG_VECCHIO,
                                REG_CREDITO_DELTA])
        v.saltati_per_posto = 9

    def g_c3(v):
        # La sessione muore sul credito, che e' il difetto del 13 agosto.
        v.caduta = "STREAM_LIMIT_ERROR — «Too many streams open»"
        v.viva = False
    def r_c3(v):
        v.caduta = None
        v.viva = True

    def g_c4(v):
        # Le due ragioni si confondono in una riga sola.
        v.registro = ("⚠ §2.3: nessuno stream unidirezionale per il delta — "
                      "fotogramma 41 ABBANDONATO (§5.1)")
    def r_c4(v):
        v.registro = "\n".join([REG_CREDITO_DELTA, REG_CURA, REG_VECCHIO,
                                REG_CREDITO_DELTA])

    def g_c5(v):
        # Col credito abbondante il server dice lo stesso «non c'e' posto».
        v.registro = REG_VECCHIO + "\n" + REG_CREDITO_DELTA
    def r_c5(v):
        v.registro = REG_VECCHIO

    # ⛔⭐ L'ESITO ATTESO DAL GIRO GUASTO SI DICHIARA, e non e' sempre ROSSO.
    #
    #     La prima stesura di questa tabella pretendeva ROSSO da tutti e cinque,
    #     e la certificazione bocciava `C2-esaurito`.  ⚠ Ma il torto era della
    #     certificazione: C2 **non ha un ramo rosso**, e non deve averlo.  «Il
    #     credito non e' mai mancato» non e' un difetto del prodotto — e' una
    #     scena che non ha provato niente, e §2.3 vuole che si dica NON PROVATO
    #     invece di verde («regge il rifiuto» non si dimostra senza un rifiuto).
    #     Un rosso li' accuserebbe il prodotto di una scena ferma, che e'
    #     esattamente l'errore di attribuzione che questo banco esiste per non
    #     ripetere.
    #
    # ⇒ Quel che il giro guasto deve provare non e' «diventa rosso», ma:
    #      **non dice VERDE**, e **nomina la propria regola**.
    def g_c6(v):
        # ⛔ Il difetto B-18: il delta e' saltato e la CHIAVE non e' stata
        #    preparata.  E' lo stato del prodotto PRIMA della cura del 13
        #    agosto 2026.
        # ⚠ Si tolgono TUTTE le forme, non quella che si ha in mente: lasciarne
        #   una dentro farebbe passare il giro guasto per verde.
        v.registro = "\n".join([r for r in v.registro.splitlines()
                                if not any(m in r for m in CURA_ARMATA)])

    def r_c6(v):
        v.registro = "\n".join([REG_CREDITO_DELTA, REG_CURA, REG_VECCHIO,
                                REG_CREDITO_DELTA])

    def r_c6_palco(v):
        v.registro = "\n".join([REG_CREDITO_DELTA, REG_CURA_PALCO, REG_VECCHIO,
                                REG_CREDITO_DELTA])

    def r_c6_debito(v):
        v.registro = "\n".join([REG_CREDITO_DELTA, REG_CURA_DEBITO,
                                REG_VECCHIO, REG_CREDITO_DELTA])

    def _sano_palco():
        v = _verbale_sano()
        v.registro = "\n".join([REG_CREDITO_DELTA, REG_CURA_PALCO, REG_VECCHIO,
                                REG_CREDITO_DELTA])
        return v

    def _sano_debito():
        v = _verbale_sano()
        v.registro = "\n".join([REG_CREDITO_DELTA, REG_CURA_DEBITO,
                                REG_VECCHIO, REG_CREDITO_DELTA])
        return v

    # ⚠ Ogni controllo ha una LISTA di aghi, non uno solo: C6 ne ha tre perche'
    #   il prodotto dice «la cura e' armata» in tre forme diverse, e un
    #   controllo certificato su una forma sola e' certificato su niente.
    return {
        "C1-annuncio": [
            ("il gesto del 13 agosto", _verbale_sano, g_c1, r_c1,
             "il banco mente", ROSSO)],
        "C2-esaurito": [
            ("il posto non manca mai", _verbale_sano, g_c2, r_c2,
             "non ha provato niente", NON_PROVATO)],
        "C3-regge": [
            ("la sessione muore", _verbale_sano, g_c3, r_c3, "caduta", ROSSO)],
        "C4-registro": [
            ("le due ragioni si confondono", _verbale_sano, g_c4, r_c4,
             "non si distinguono", ROSSO)],
        "C5-abbondante": [
            ("le righe di §2.3 le scrive sempre", _verbale_sano_abbondante,
             g_c5, r_c5, "non varrebbero niente", ROSSO)],
        "C6-cura": [
            ("B-18 in piedi (forma «FOTOGRAMMA NON SPEDITO»)", _verbale_sano,
             g_c6, r_c6, "la cura non e' stata armata", ROSSO),
            ("⭐ B-18 in piedi (forma «girata al palco»)", _sano_palco,
             g_c6, r_c6_palco, "la cura non e' stata armata", ROSSO),
            ("⭐ B-18 in piedi (forma «il debito resta acceso»)", _sano_debito,
             g_c6, r_c6_debito, "la cura non e' stata armata", ROSSO),
        ],
    }


def certifica(a):
    """⛔ Si esegue PRIMA di ogni misura, e il suo rosso ferma il giro."""
    aghi = _aghi()
    righe, falle = [], 0
    print("\n\033[1m== ⭐ LA CERTIFICAZIONE — TRE GIRI: sano → guasto → "
          "risanato\033[0m")
    print("   sano     : il verbale rispetta la proprieta'  ⇒ deve dire VERDE")
    print("   guasto   : la viola SOLO li'                  ⇒ deve dire ROSSO,")
    print("              e deve NOMINARE la propria regola")
    print("   risanato : ⭐ al verbale GUASTO si toglie l'ago ⇒ deve tornare "
          "VERDE")
    print("   ⛔ Il terzo giro e' l'unico che attribuisce il rosso all'ago.\n")

    for nome, fn, che_cosa in CONTROLLI:
        print(f"  \033[1m{nome:<16}\033[0m {che_cosa}")
        for etichetta, fabbrica, guasta, risana, ago, atteso in aghi[nome]:
            v_sano = fabbrica()
            e_sano = fn(v_sano)

            v_guasto = fabbrica()
            guasta(v_guasto)
            e_guasto = fn(v_guasto)

            # ⛔ Il risanamento parte dal GUASTO, non dal sano.
            v_risanato = copy.deepcopy(v_guasto)
            risana(v_risanato)
            e_risanato = fn(v_risanato)

            pos = e_sano.esito == VERDE
            # ⛔ «non dice VERDE», non «dice ROSSO»: vedi il riquadro su `_aghi()`.
            neg = e_guasto.esito == atteso and atteso != VERDE
            nomina = ago.lower() in e_guasto.dice.lower() if neg else False
            ris = e_risanato.esito == VERDE
            buono = pos and neg and nomina and ris
            if not buono:
                falle += 1
            segno = "\033[1;32mOK\033[0m" if buono else "\033[1;31mNO\033[0m"
            print(f"    {segno}  ago: {etichetta}")
            print(f"        sano     : {e_sano.esito:<11} {e_sano.dice[:88]}")
            print(f"        guasto   : {e_guasto.esito:<11} "
                  f"(atteso {atteso}) {e_guasto.dice[:74]}")
            print(f"        risanato : {e_risanato.esito:<11} "
                  f"{e_risanato.dice[:88]}")
            if not pos:
                print("        \033[1;31m⛔ rosso anche sul verbale SANO: i suoi "
                      "rossi sul filo non varrebbero niente\033[0m")
            if not neg:
                print(f"        \033[1;31m⛔ sul verbale guasto dice "
                      f"{e_guasto.esito} invece di {atteso}: non sa vedere quel "
                      f"che cerca\033[0m")
            if neg and not nomina:
                print(f"        \033[1;31m⛔ e' {e_guasto.esito} ma NON nomina "
                      f"«{ago}»: e' cosi' per un'altra ragione, cioe' e' "
                      f"crollato\033[0m")
            if not ris:
                print("        \033[1;31m⛔ TOLTO L'AGO non torna verde: il "
                      "verdetto del secondo giro NON era dell'ago — il")
                print("           controllo sta giudicando qualcos'altro del "
                      "verbale guasto\033[0m")
            righe.append({"controllo": nome, "ago": etichetta,
                          "sano": e_sano.esito, "guasto": e_guasto.esito,
                          "atteso": atteso, "nomina": nomina,
                          "risanato": e_risanato.esito, "esito": buono})

    # ⛔ Le costanti di §6.2 si confrontano con l'altro banco: due tabelle che
    #    mappano le stesse cose divergono in silenzio.
    uguali = None
    try:
        f24 = _porta("f24", "02-filo-fotogramma.py")
        uguali = (f24.INTESTAZIONE == INTESTAZIONE and f24.CHIAVE == CHIAVE
                  and f24.DELTA == DELTA)
        segno = "\033[1;32mOK\033[0m" if uguali else "\033[1;31mNO\033[0m"
        print(f"\n  {segno}  le costanti di §6.2 combaciano con quelle di "
              f"02-filo-fotogramma.py")
        if not uguali:
            falle += 1
    except Exception as e:                              # noqa: BLE001
        print(f"\n  --  le costanti non si sono potute confrontare: "
              f"{type(e).__name__}: {e}")

    print(f"\n  {len(righe) - falle} aghi su {len(righe)}, per "
          f"{len(CONTROLLI)} controlli, certificati su TRE giri.")
    if falle:
        print("  \033[1;31m⛔ La certificazione ha falle: le misure di questo "
              "banco NON valgono finche' restano.\033[0m")
    # ⛔⭐ IN CODA, E IL PRIMO `w` E' COSTATO I TRE GIRI — difetto trovato il 13
    #     agosto 2026 sera, guardando il file invece di fidarsi del codice.
    #
    #     La prima stesura di questa cura apriva qui con `w` («le righe della
    #     certificazione sono uguali a ogni giro, accumularle non dice niente di
    #     piu'») e in coda nel giro dal vivo.  ⚠ Ma da quando la certificazione
    #     gira PRIMA DI OGNI MISURA, quel `w` tronca il file a ogni giro: il
    #     file conteneva solo l'ULTIMO, e i tre giri del metodo di casa — sano,
    #     guasto, risanato — sparivano uno dopo l'altro.  ⇒ Un file di esiti che
    #     dice sempre «tutto verde» perche' ha buttato le altre due misure.
    #
    # ⭐ E' la stessa scelta che `03-b15-movimento.py` fa gia' in
    #    `scrivi_esito()`: un registro di esiti si SCRIVE IN CODA.
    if a.uscita:
        with open(a.uscita, "a") as f:
            for r in righe:
                f.write(json.dumps({"quando": time.strftime("%FT%T"),
                                    "banco": "03-b18", "tipo": "certificazione",
                                    **r}, ensure_ascii=False) + "\n")
    return falle


# --------------------------------------------------------------------------
# ⛔ IL GIRO DAL VIVO — richiede aioquic e il prodotto sulla 7607.

def costruisci_cliente(a, caso):
    """Il cliente, e ⭐ la sola leva che questo banco muove: il CREDITO.

    ⛔⭐ E LA MUOVE PRIMA DELLA STRETTA DI MANO, che e' tutta la differenza fra
        questo banco e il caso «credito» del 13 agosto.

        `aioquic.asyncio.client.connect()` costruisce il protocollo a `:86` e
        chiama `connect()` — cioe' spedisce il ClientHello — solo a `:91`.  ⇒
        Quel che si scrive in `__init__` FINISCE sul filo; quel che si scrive
        dopo la stretta di mano non ci finisce **mai**, e RFC 9000 §4.6 vieta di
        rinnegare un limite gia' concesso.

    ⚠ `_local_max_streams_uni` e' un campo PRIVATO di aioquic e va dichiarato:
      `QuicConfiguration` **non espone** `initial_max_streams_uni`, e il
      predefinito scritto a mano nella libreria e' 128.

    ⛔⭐ E LA LEVA NON BASTAVA: SERVE ANCHE LA PINZA — cura del 13 agosto 2026,
        sera, e viene dal PRIMO giro dal vivo di questo banco.

        `[M]` `--credito 6` ⇒ **333** stream video aperti in 30 s, credito mai
        esaurito.  `--credito 4` ⇒ **264** in 25 s, credito mai esaurito.  ⇒ C2,
        C3, C4 e C6 tutti NON PROVATO: il banco non arrivava **mai** al proprio
        caso, e un `NON PROVATO` che nessuno guarda si legge come un verde.

        La ragione sta in `aioquic/quic/connection.py:_write_connection_limits`:

            if limit.used * 2 > limit.value:
                limit.value *= 2

        cioe' il pari **raddoppia** il limite appena se ne consuma meta', e su
        loopback il rinnovo torna sempre prima che serva.  ⚠ Non e' un difetto
        del prodotto: e' una scena che il banco non riusciva a costruire.
    """
    b3 = carica_b3()

    class Credito(b3.Cliente):
        def __init__(self, *args, **kw):
            super().__init__(*args, **kw)
            self.video = {}
            self.finiti = []
            self.azzerati = []
            # ⛔ Gli id degli stream video VISTI sul filo, che restano anche
            #    dopo che lo stream si e' chiuso: e' la grandezza che C2 usa.
            self.visti_uni = []
            self.ultimo_numero = 0
            self.t0 = time.monotonic()
            self.caduta = None
            self.annunciato = None
            self.pinza_chiusa = False
            q = self._quic
            if caso == "stretto":
                q._local_max_streams_uni.value = a.credito
                q._local_max_streams_uni.sent = a.credito

            # ⭐⭐ LA SPIA CHE RENDE VERO C1, ed e' il pezzo che il 13 agosto
            #     mancava.  Non si CREDE che il credito sia finito nel
            #     ClientHello: si guarda il valore **nel momento in cui aioquic
            #     serializza i parametri di trasporto**, che e' l'unico istante
            #     in cui quel campo tocca il filo.
            #     ⛔ Se aioquic spostasse `_serialize_transport_parameters`, la
            #        spia resta cieca e `credito_annunciato` resta `None` — e C1
            #        dice NON PROVATO invece di dire verde a vuoto.
            # ⚠ E si mette in TUTT'E DUE i casi, non solo nello stretto: nel
            #   giro abbondante serve a dichiarare **quanto** era abbondante
            #   (128, il predefinito di aioquic) invece di lasciarlo supporre.
            vero = getattr(q, "_serialize_transport_parameters", None)
            if vero is not None:
                def spia():
                    self.annunciato = q._local_max_streams_uni.value
                    return vero()
                q._serialize_transport_parameters = spia

            # ⛔⭐ LA PINZA SUL RADDOPPIO — e senza di lei questo banco non
            #     arriva MAI al proprio caso (il riquadro qui sopra).
            #
            # ⭐ E NON E' UN RINNEGAMENTO, che e' precisamente la differenza fra
            #    questa mossa e il difetto che C1 esiste per non far ripetere:
            #    il valore annunciato non si tocca e non SCENDE mai.  Si
            #    impedisce soltanto che CRESCA, cioe' non si manda nessun
            #    `MAX_STREAMS` — e RFC 9000 lo permette a chiunque, perche'
            #    alzare un limite e' una facolta' e non un obbligo.  ⛔ Ritirare
            #    un limite gia' annunciato lo vieta §4.6; non alzarlo non lo
            #    vieta niente.
            #
            # ⚠ Si lavora su una COPIA del limite: a `_write_connection_limits`
            #   si passa un gemello con `used = 0` (⇒ niente raddoppio) e
            #   `sent = value` (⇒ nessun frame da mandare), e l'originale torna
            #   al suo posto subito dopo.  Cosi' il contatore vero di aioquic
            #   resta intatto: la pinza si potrebbe riaprire senza aver perso il
            #   conto, ed e' quel che fa `03-b18b-cura.py` per provare la cura.
            if caso == "stretto" and a.pinza:
                from aioquic.quic.connection import Limit
                self.pinza_chiusa = True
                vero_wcl = q._write_connection_limits

                def con_la_pinza(builder, space):
                    if not self.pinza_chiusa:
                        return vero_wcl(builder, space)
                    salvo = q._local_max_streams_uni
                    finto = Limit(frame_type=salvo.frame_type, name=salvo.name,
                                  value=salvo.value)
                    finto.sent = salvo.value
                    finto.used = 0
                    q._local_max_streams_uni = finto
                    try:
                        return vero_wcl(builder, space)
                    finally:
                        q._local_max_streams_uni = salvo

                q._write_connection_limits = con_la_pinza

        # ⛔ Uno stream unidirezionale APERTO DAL SERVER ha `id % 4 == 3`
        #    (RFC 9000 §2.1).  ⚠ E non tutti sono video: i primi tre se li
        #    prende HTTP/3 (§2.3).  Il modo di distinguerli NON e' il numero —
        #    che sarebbe indovinare — ma il **preambolo di WebTransport**:
        #    `0x54` seguito dal numero di sessione, cioe' i byte `40 54` sul
        #    filo (proposta P18, e lo stesso riquadro di `src/webtransport.c`).
        @staticmethod
        def _e_del_server_uni(sid):
            return sid % 4 == 3

        def quic_event_received(self, event):
            from aioquic.quic.events import (ConnectionTerminated,
                                             StreamDataReceived, StreamReset)
            if isinstance(event, ConnectionTerminated):
                # ⛔ Il motivo si tiene PER INTERO: «Too many streams open» e
                #    «idle timeout» sono due diagnosi diverse, e un booleano le
                #    appiattirebbe.
                self.caduta = (f"codice 0x{event.error_code:02x} — "
                               f"{event.reason_phrase!r}")
            elif (isinstance(event, StreamDataReceived)
                    and self._e_del_server_uni(event.stream_id)
                    and event.stream_id not in (self.controllo, self.sessione)):
                f = self.video.get(event.stream_id)
                if f is None and event.data[:2] == b"\x40\x54":
                    f = self.video[event.stream_id] = {"byte": 0}
                    self.visti_uni.append(event.stream_id)
                if f is not None:
                    f["byte"] += len(event.data)
                    if event.end_stream:
                        # ⛔ §6.2: come lo stream finisce E' parte del
                        #    messaggio.  FIN ⇒ fotogramma completo.
                        self.finiti.append(self.video.pop(event.stream_id))
                    return
            elif (isinstance(event, StreamReset)
                    and event.stream_id in self.video):
                # ⛔ `RESET_STREAM` ⇒ fotogramma INCOMPLETO, abbandonato di
                #    proposito (§5.1).  Tenerlo insieme ai finiti cancellerebbe
                #    esattamente la distinzione che §6.2 esiste per dare.
                self.azzerati.append(self.video.pop(event.stream_id))
                return
            super().quic_event_received(event)

    return Credito


def righe_registro(percorso):
    """Quante righe ha il registro ADESSO — la riga di partenza del giro.

    ⛔⭐ E SENZA DI LEI IL CONTROLLO NEGATIVO E' UNA TRAPPOLA — difetto trovato
        il 13 agosto 2026 leggendo il banco, non girandolo.

        `--caso tutti` fa prima il giro «stretto» e poi quello «abbondante», e
        il registro del server e' lo STESSO file, in coda.  ⇒ Leggendolo
        INTERO, il giro abbondante ritrova le righe di §2.3 che ha scritto il
        giro stretto, e **C5 — il controllo negativo — direbbe ROSSO su un
        prodotto sano**, accusandolo di «scrivere quelle righe sempre».
        ⚠ E' la forma peggiore: il controllo che esiste per rendere validi gli
        altri cinque sarebbe l'unico a mentire.  `03-b15-movimento.py` la riga
        di partenza la segna gia'; qui mancava.
    """
    if not percorso:
        return 0
    try:
        with open(percorso, errors="replace") as f:
            return len(f.read().splitlines())
    except OSError:
        return 0


def leggi_registro(a, da_riga=0):
    """Il registro del server, che e' il lato che DEVE ricevere.

    ⛔ `CODER.md` §3.8: «il registro di chi manda dice che ha chiamato una
       funzione, non che il byte e' arrivato».  Qui a dover reggere il rifiuto e'
       il server, quindi il verdetto di §2.3 viene dal SUO registro.

    ⛔ E si leggono solo le righe NUOVE, da `da_riga` in giu': vedi il riquadro
       di `righe_registro()`.
    """
    if not a.registro:
        return ""
    try:
        with open(a.registro, errors="replace") as f:
            return "\n".join(f.read().splitlines()[da_riga:])
    except OSError as e:
        print(f"   ⛔ il registro non si legge: {e}")
        return ""


async def giro(a, caso, da_riga=0):
    """Un giro contro il prodotto.  `caso` = «stretto» oppure «abbondante»."""
    import asyncio
    b3 = carica_b3()
    from aioquic.asyncio import connect
    from aioquic.h3.connection import H3_ALPN
    from aioquic.quic.configuration import QuicConfiguration

    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{a.indirizzo}:{a.porta}"
    Cliente = costruisci_cliente(a, caso)

    v = Verbale()
    v.credito_chiesto = a.credito if caso == "stretto" else None
    v.saltati_per_posto = 0

    async with connect(a.indirizzo, a.porta, configuration=conf,
                       create_protocol=Cliente) as cli:
        try:
            await asyncio.wait_for(cli.wait_connected(), timeout=10)
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
            await b3.attendi(cli, "AMMESSO", attesa=25)
            cli.manda(b3.inquadra(b3.T["ATTACCA"],
                                  struct.pack("!IIII", a.larghezza, a.altezza,
                                              a.larghezza, a.altezza)
                                  + b3.s(a.disposizione)))
            await b3.attendi(cli, "SESSIONE", attesa=15)

            fine = time.monotonic() + a.attesa
            while time.monotonic() < fine:
                await asyncio.sleep(0.05)
                if cli.caduta:
                    break
        except Exception as e:                          # noqa: BLE001
            if v.caduta is None:
                v.caduta = f"{type(e).__name__}: {e}"

        # ⛔ La premessa si scrive ANCHE se il giro e' finito male: un giro
        #    morto nella stretta di mano ha comunque annunciato qualcosa, e C1
        #    deve poterlo dire invece di uscire NON PROVATO per un'altra ragione.
        if cli.annunciato is not None:
            v.credito_annunciato = cli.annunciato
        v.viva = cli.caduta is None and v.caduta is None
        if cli.caduta:
            v.caduta = cli.caduta
        v.finiti = list(cli.finiti)
        v.azzerati = list(cli.azzerati)
        # ⛔ Gli stream VISTI, non quelli ancora aperti: a fine giro
        #    `cli.video` tiene solo gli incompiuti, e contare quelli direbbe
        #    «il server non ha aperto niente» proprio nel giro in cui ha
        #    aperto tutto e chiuso bene.
        v.stream_aperti = sorted(cli.visti_uni)

    v.registro = leggi_registro(a, da_riga)
    # ⛔ Quanti fotogrammi non sono partiti per mancanza di posto lo dice il
    #    SERVER: dal lato del client un fotogramma mai spedito e uno perso hanno
    #    lo stesso aspetto — che e' la forma d'errore E8.
    v.saltati_per_posto = len(righe_credito(v))
    return v


def principale():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--porta", type=int, default=7607,
                   help="⛔ la 7607, di questo gruppo.  7448/7501/7561 non si "
                        "toccano; 7603 e 7605 sono di altri gruppi")
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
    p.add_argument("--credito", type=int, default=8,
                   help="⭐ `initial_max_streams_uni` annunciato DAVVERO, cioe' "
                        "scritto PRIMA della stretta di mano.  ⛔ HTTP/3 se ne "
                        "prende TRE (§2.3), quindi con 8 ne restano 5 a RCP.  "
                        "⚠ E il credito degli stream NON torna indietro quando "
                        "uno stream si chiude (RFC 9000 §4.6: `max_streams` e' "
                        "cumulativo): con la pinza chiusa questi sono i "
                        "fotogrammi che passano, poi il posto e' finito")
    p.add_argument("--niente-pinza", dest="pinza", action="store_false",
                   help="⛔ NON impedire ad aioquic di raddoppiare il limite "
                        "appena se ne consuma meta' (`_write_connection_"
                        "limits`).  ⚠ Senza la pinza il credito su loopback "
                        "non si esaurisce mai e C2-C6 escono NON PROVATO: "
                        "l'interruttore c'e' per poterlo MISURARE, non perche' "
                        "sia un'alternativa")
    p.set_defaults(pinza=True)
    p.add_argument("--registro", default="",
                   help="il registro del server, per le righe di §2.3 e §5.1")
    p.add_argument("--caso", default="tutti",
                   choices=["tutti", "stretto", "abbondante"])
    p.add_argument("--uscita", default="")
    p.add_argument("--nota", default="",
                   help="⛔⭐ CHE COS'ERA IL PRODOTTO IN QUESTO GIRO, e finisce "
                        "in ogni riga di `--uscita`.  ⚠ Un file di esiti che "
                        "mescola i giri sul prodotto SANO e quelli sul "
                        "prodotto GUASTO senza dire quale e' quale mette due "
                        "cose diverse sotto la stessa etichetta — la forma "
                        "d'errore E2 — e chi legge non ha modo di separarle")
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--elenco", action="store_true")
    a = p.parse_args()

    if a.parola_file:
        with open(a.parola_file) as f:
            a.parola = f.read().strip()

    if a.elenco:
        print(__doc__)
        print("I cinque controlli:")
        for nome, _, che_cosa in CONTROLLI:
            print(f"  {nome:<16} {che_cosa}")
        return 0

    # ⛔⭐ LA CERTIFICAZIONE GIRA SEMPRE, ANCHE PRIMA DI UNA MISURA — `LEZIONI.md`
    #     §1.2, ed e' quel che `03-b15-movimento.py` fa gia'.  «Si accerta che il
    #     banco sappia produrre il risultato atteso PRIMA di puntarlo
    #     sull'incognita: altrimenti un esito negativo e' ambiguo fra "l'incognita
    #     non funziona" e "il banco non funzionava".»  ⚠ Fino a stasera qui la
    #     certificazione girava SOLO con `--certifica`, cioe' mai nel giro che
    #     conta.
    falle = certifica(a)
    if falle:
        print("\n⛔ Non punto un banco non certificato sull'incognita: un rosso "
              "sarebbe ambiguo\n   fra «il prodotto non funziona» e «il banco "
              "non funzionava» (LEZIONI.md §1.2).")
        return 2
    if a.certifica:
        return 0

    import asyncio
    casi = ["stretto", "abbondante"] if a.caso == "tutti" else [a.caso]
    fuori, rossi = {}, 0
    for caso in casi:
        print(f"\n\033[1m== il giro «{caso}»\033[0m")
        # ⛔ La riga di partenza si segna PRIMA del giro: vedi il riquadro di
        #    `righe_registro()`.  Senza, il giro «abbondante» leggerebbe le
        #    righe di §2.3 dello «stretto» e C5 direbbe rosso su un prodotto
        #    sano.
        da_riga = righe_registro(a.registro)
        v = asyncio.run(giro(a, caso, da_riga))
        print(f"  --  credito annunciato sul filo: {v.credito_annunciato} "
              f"(chiesto: {v.credito_chiesto}) · pinza sul raddoppio: "
              f"{'CHIUSA' if (caso == 'stretto' and a.pinza) else 'aperta'}")
        print(f"  --  stream video visti: {len(v.stream_aperti)} · fotogrammi "
              f"interi: {len(v.finiti)} · azzerati: {len(v.azzerati)} · righe "
              f"nuove nel registro: {len(v.registro.splitlines())}")
        for nome, fn, _ in CONTROLLI:
            # ⛔ Ogni controllo gira sul caso che lo riguarda, e sugli altri
            #    dice NON PROVATO da se': un verde raccolto dal caso sbagliato
            #    sarebbe un verde su niente.
            e = fn(v)
            fuori[f"{caso}/{nome}"] = e.come_dizionario()
            colore = {"VERDE": "\033[1;32m", "ROSSO": "\033[1;31m"}.get(
                e.esito, "\033[1;33m")
            print(f"  {colore}{e.esito:<11}\033[0m {nome:<16} {e.dice[:110]}")
            if e.esito == ROSSO:
                rossi += 1
    # ⛔ IN CODA, non troncando: la certificazione ha appena scritto le proprie
    #    righe in questo stesso file, e un `w` qui le cancellerebbe — cioe' il
    #    giro dal vivo butterebbe via la prova che il banco sa dire di no.
    #    ⚠ E' il modo in cui `03-b18-esiti.jsonl` e' rimasto per un giorno con
    #      sole righe di certificazione senza che si vedesse.
    if a.uscita:
        with open(a.uscita, "a") as f:
            for k, r in fuori.items():
                f.write(json.dumps({"quando": time.strftime("%FT%T"),
                                    "banco": "03-b18", "tipo": "giro",
                                    "porta": a.porta, "credito": a.credito,
                                    "pinza": a.pinza,
                                    "prodotto": a.nota or "⚠ NON DICHIARATO",
                                    "controllo": k, **r},
                                   ensure_ascii=False) + "\n")
    print(f"\n  {rossi} rossi.")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(principale())
