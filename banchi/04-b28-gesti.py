#!/usr/bin/env python3
"""04-b28-gesti.py — ⭐ IL BANCO DEL MODO A TOCCO (anello A8 della fase 4).

    python3 banchi/04-b28-gesti.py --certifica     ⭐ senza browser: il giudice
                                                      sa vedere il difetto?
    python3 banchi/04-b28-gesti.py --gira --porta 7671 --diagnosi 7672
    python3 banchi/04-b28-gesti.py --verdetto banchi/04-b28-registro.jsonl

===========================================================================
⛔ CHE COSA MISURA, E DA CHE PARTE STA

Due domande DISTINTE, e si giudicano separatamente:

  ⒜ **i sette gesti** (`SPECIFICHE.md` §7.2): una sequenza di eventi `Touch`
     sintetica per ciascuno ⇒ il messaggio di `RCP.md` §7.3 atteso;
  ⒝ **il passaggio automatico** (`DECISIONI.md` §5-bis.0-bis): si dichiara il
     contesto e si verifica **quale disposizione e' IN VIGORE** — leggendo
     `body[data-disposizione]`, che e' il prodotto a scrivere, e provando che
     l'altra meta' e' davvero SPENTA.  ⛔ Non «esiste una funzione che la
     cambia»: una funzione che non cambia niente esiste benissimo.

⛔ I byte si decodificano con un lettore scritto QUI, dalla tabella di
   `RCP.md` §7.3, senza guardare il JavaScript della pagina.  Se un giorno i
   due non andranno d'accordo, **quel disaccordo e' il regalo**.

===========================================================================
⛔⛔ IL BANCO SI CERTIFICA SULLE CONFUSIONI, NON SUI GESTI PULITI

E' la riga piu' importante di questo file.  Un banco che provi i sette gesti
puliti dice **verde** su un riconoscitore che sbaglia tutti i casi di confine:
i gesti puliti sono facili, e nessun difetto vero vive li'.

  G1..G7   i sette gesti puliti      — servono da controllo POSITIVO
  C1..C8   ⭐ le CONFUSIONI          — e' qui che si decide il verdetto
  D1..D4   il passaggio automatico
  S1       ⭐ la CUCITURA fra le due ancore, che alla fase 3 non guardava
           nessun banco (`fasi/rapporti/F5-desktop-vero.md`)

⛔ E `--certifica` inietta CINQUE guasti, uno per famiglia di confusione, e
   pretende **verde → rosso → verde** su ciascuno.  Un giudice che non sa dire
   rosso non sa dire verde (`CODER.md` §3.3, §3.10, §4.6).

===========================================================================
⚠ LA SCENA, DICHIARATA — e il palco si verifica dall'altro capo

Il browser si apre sul desktop VERO dell'utente: e' quel che il mandato
chiede, e ⛔ **non si sposta su uno schermo finto per far tornare i conti**.
Quel che la scena era davvero lo scrive il raccoglitore in ogni riga di
`04-b28-esiti.jsonl` — `XDG_SESSION_TYPE`, lo `userAgent`, e la disposizione
che il PRODOTTO ha scritto nel documento.

⛔ E il tocco lo dichiara il banco, non l'ambiente: `Emulation.setTouchEmulation
   Enabled` accende i punti di contatto, e ⚠ **quel che se ne ricava e'
   l'emulazione, non un dito** (`LEZIONI.md` §1.11).  ⇒ Da qui NON esce nessun
   numero su come si comporta una mano vera: escono i confini del
   RICONOSCITORE, che sono deterministici e si misurano bene anche cosi'.
   ⭐ Il giudizio sui gesti resta di Nic, con un dito, e sta scritto nel
   rapporto.
"""

import argparse
import http.server
import importlib.util
import json
import os
import socketserver
import struct
import sys
import threading
import time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)

# `RCP.md` §7.3 — i tipi del canale di input e i codici di evdev.
PUNTATORE, PULSANTE, ROTELLA = 0x0101, 0x0102, 0x0103
SINISTRO, DESTRO, CENTRALE = 0x110, 0x111, 0x112
NOMI = {PUNTATORE: "PUNTATORE", PULSANTE: "PULSANTE", ROTELLA: "ROTELLA"}
NOMI_BTN = {SINISTRO: "sinistro", DESTRO: "destro", CENTRALE: "centrale"}

TELA = (1920, 1080)


class Violazione(Exception):
    pass


# ---------------------------------------------------------------------------
# IL LETTORE DEI BYTE — scritto dalla tabella di `RCP.md` §7.3.
#
# ⛔ Inquadratura di §6.1: u16 tipo, u32 lunghezza, corpo.  Corpo di §7.3:
#    u32 id (crescente, mai 0) + u64 istante (microsecondi) + i campi del tipo.
# ---------------------------------------------------------------------------
def decodifica(byte):
    fuori, o = [], 0
    while o < len(byte):
        if len(byte) - o < 6:
            raise Violazione("inquadratura tronca: restano %d byte" % (len(byte) - o))
        tipo, lung = struct.unpack_from(">HI", byte, o)
        o += 6
        if len(byte) - o < lung:
            raise Violazione("corpo troncato: dichiarati %d, ce ne sono %d"
                             % (lung, len(byte) - o))
        corpo = byte[o:o + lung]
        o += lung
        if tipo >> 8 != 0x01:
            raise Violazione("tipo 0x%04X: non e' del canale di input (§2.5)" % tipo)
        if lung < 12:
            raise Violazione("corpo di %d byte: id e istante non ci stanno" % lung)
        mid, istante = struct.unpack_from(">IQ", corpo, 0)
        if mid == 0:
            raise Violazione("id 0: §7.3 lo riserva a «nessun input»")
        m = {"tipo": tipo, "nome": NOMI.get(tipo, "?"), "id": mid, "istante": istante}
        if tipo == PUNTATORE:
            if lung != 20:
                raise Violazione("PUNTATORE di %d byte, ne vuole 20" % lung)
            m["x"], m["y"] = struct.unpack_from(">II", corpo, 12)
        elif tipo == PULSANTE:
            if lung != 15:
                raise Violazione("PULSANTE di %d byte, ne vuole 15" % lung)
            m["codice"], m["premuto"] = struct.unpack_from(">HB", corpo, 12)
        elif tipo == ROTELLA:
            if lung != 20:
                raise Violazione("ROTELLA di %d byte, ne vuole 20" % lung)
            m["asse_x"], m["asse_y"] = struct.unpack_from(">ii", corpo, 12)
        else:
            raise Violazione("tipo 0x%04X sconosciuto sul canale di input" % tipo)
        fuori.append(m)
    return fuori


# ---------------------------------------------------------------------------
# IL GIUDICE.  Ogni caso e' una funzione che riceve i messaggi della sua fase e
# torna (verde: bool, perche': str).
#
# ⛔ Le attese si scrivono come PROPRIETA', non come stringhe da confrontare:
#    «nessun PULSANTE» e' una proprieta' che sopravvive a un id diverso o a un
#    PUNTATORE in piu'; «questi byte esatti» sarebbe verde solo sul giro che
#    l'ha prodotta (`LEZIONI.md` §2.3 — il banco della rotella di v1, rosso col
#    codice corretto, per una stringa cercata male).
# ---------------------------------------------------------------------------
def _pul(ms):
    return [m for m in ms if m["tipo"] == PULSANTE]


def _clic(ms, codice):
    """La coppia premuto/rilasciato di un pulsante, contata come CLIC."""
    p, n = None, 0
    for m in _pul(ms):
        if m["codice"] != codice:
            continue
        if m["premuto"] == 1:
            p = m
        elif p is not None:
            n += 1
            p = None
    return n


def _punt(ms):
    return [m for m in ms if m["tipo"] == PUNTATORE]


def _rot(ms):
    return [m for m in ms if m["tipo"] == ROTELLA]


def _solo(ms, codice):
    """Un clic solo, di quel pulsante, e nient'altro sul filo."""
    if _rot(ms):
        return False, "c'e' una ROTELLA: non era un tap"
    if _clic(ms, codice) != 1:
        return False, ("clic %s attesi 1, contati %d (pulsanti: %s)"
                       % (NOMI_BTN.get(codice, codice), _clic(ms, codice),
                          [(NOMI_BTN.get(m["codice"], m["codice"]), m["premuto"])
                           for m in _pul(ms)]))
    altri = [m for m in _pul(ms) if m["codice"] != codice]
    if altri:
        return False, ("sul filo ci sono anche altri pulsanti: %s"
                       % [(NOMI_BTN.get(m["codice"], m["codice"]), m["premuto"])
                          for m in altri])
    return True, "un clic %s e basta" % NOMI_BTN.get(codice, codice)


def c_G1(ms):
    """1 dito trascina = muove il puntatore, e NON preme niente."""
    if _pul(ms):
        return False, "un trascinamento ha prodotto un pulsante"
    p = _punt(ms)
    if len(p) < 3:
        return False, "solo %d PUNTATORE per un trascinamento di 200 px" % len(p)
    if p[-1]["x"] <= p[0]["x"]:
        return False, ("il dito e' andato a destra e il puntatore no: da %d a %d"
                       % (p[0]["x"], p[-1]["x"]))
    return True, "%d PUNTATORE, da x=%d a x=%d, nessun pulsante" % (
        len(p), p[0]["x"], p[-1]["x"])


def c_G2(ms):
    return _solo(ms, SINISTRO)


def c_G3(ms):
    return _solo(ms, DESTRO)


def c_G4(ms):
    """2 dita trascina = rotella.  ⛔ Il SEGNO e la grana da 60 (§7.3)."""
    if _pul(ms):
        return False, "uno scorrimento a due dita ha prodotto un pulsante"
    r = _rot(ms)
    if not r:
        return False, "nessuna ROTELLA"
    for m in r:
        if m["asse_y"] % 60 or m["asse_x"] % 60:
            return False, ("ROTELLA non multipla di 60 (§7.3, il mezzo scatto): "
                           "%d, %d" % (m["asse_x"], m["asse_y"]))
    tot = sum(m["asse_y"] for m in r)
    if tot <= 0:
        return False, ("le dita sono scese e l'asse verticale non e' positivo "
                       "(%d): `RCP.md` §7.3 vuole +120 per la rotella IN SU, e "
                       "due dita che scendono spingono il foglio in giu'" % tot)
    return True, "%d ROTELLA, somma verticale +%d, tutte multiple di 60" % (len(r), tot)


def c_G5(ms):
    """⭐ TAP-E-MEZZO: tap, poi premi e trascina.  Sul filo:
       clic · premuto · PUNTATORE che si muovono · rilasciato.
       ⛔ E i PUNTATORE devono stare FRA premuto e rilasciato, o non e' un
          trascinamento: e' un doppio clic."""
    p = _pul(ms)
    sin = [m for m in p if m["codice"] == SINISTRO]
    if len(sin) != 4:
        return False, "attesi 4 eventi del sinistro (giu,su,giu,su), contati %d" % len(sin)
    if [m["premuto"] for m in sin] != [1, 0, 1, 0]:
        return False, "l'ordine non e' giu,su,giu,su: %s" % [m["premuto"] for m in sin]
    # I PUNTATORE fra il TERZO e il QUARTO evento: e' li' che vive il trascinamento.
    i3 = ms.index(sin[2])
    i4 = ms.index(sin[3])
    dentro = [m for m in ms[i3 + 1:i4] if m["tipo"] == PUNTATORE]
    if len(dentro) < 2:
        return False, ("solo %d PUNTATORE fra il premuto e il rilasciato: il "
                       "tasto e' rimasto giu' senza trascinare niente" % len(dentro))
    if dentro[-1]["y"] == dentro[0]["y"] and dentro[-1]["x"] == dentro[0]["x"]:
        return False, "il puntatore non si e' mosso mentre il tasto era giu'"
    return True, ("clic, poi premuto + %d PUNTATORE + rilasciato — "
                  "il trascinamento c'e'" % len(dentro))


def c_G6(ms):
    return _solo(ms, CENTRALE)


def c_G7(ms, zoom=None):
    """Pizzico = ingrandisce la VISTA del client.  ⛔ ZERO byte sul filo."""
    if ms:
        return False, ("il pizzico ha spedito %d messaggi: §7.2 dice che "
                       "ingrandisce la VISTA, non l'applicazione" % len(ms))
    if zoom is None:
        return True, "nessun messaggio sul filo (zoom non letto)"
    if zoom <= 1.05:
        return False, "nessun messaggio sul filo, ma la vista non si e' ingrandita (zoom %.2f)" % zoom
    return True, "zero byte sul filo, e la vista e' a %.2fx" % zoom


# ── ⭐ LE CONFUSIONI ────────────────────────────────────────────────────────
def c_C1(ms):
    """Il tap che dura un po' troppo (400 ms, fermo) ⇒ NON e' un clic.
       Soglia dichiarata: `T_TAP` = 180 ms."""
    if _pul(ms):
        return False, ("un contatto di 400 ms fermo ha prodotto un clic: la "
                       "soglia dei 180 ms non e' guardata")
    return True, "400 ms fermi, nessun clic (T_TAP = 180 ms)"


def c_C2(ms):
    """Il tap che scivola (120 ms ma 30 px) ⇒ NON e' un clic, e' un movimento.
       Soglia dichiarata: `D_TAP` = 9 px CSS."""
    if _pul(ms):
        return False, "un contatto scivolato di 30 px ha prodotto un clic (D_TAP = 9 px)"
    if not _punt(ms):
        return False, "scivolato di 30 px e il puntatore non si e' mosso affatto"
    return True, "30 px di scivolata: %d PUNTATORE, nessun clic" % len(_punt(ms))


def c_C3(ms):
    """⭐⭐ LE DUE DITA CHE SI APPOGGIANO A 30 ms DI DISTANZA.
       E' il caso che il mandato nomina.  Un riconoscitore che conta le dita
       all'inizio del gesto qui vede UN dito e manda un clic SINISTRO."""
    if _clic(ms, SINISTRO):
        return False, ("clic SINISTRO: le due dita erano scollate di 30 ms e il "
                       "conteggio non ha guardato il massimo di dita contemporanee")
    return _solo(ms, DESTRO)


def c_C4(ms):
    """⛔ IL DIFETTO DICHIARATO, e il banco lo pretende cosi' com'e'.

    Due dita che NON si sovrappongono mai (A 0→100 ms, B 130→230 ms, a 60 px
    l'una dall'altra) escono come DUE CLIC SINISTRI, non come un clic destro.
    ⛔ Non e' un difetto da correggere qui: la stessa sequenza e' anche «clicco
    qui, poi clicco subito li'», e l'unica cura sarebbe ritardare OGNI clic
    sinistro di 300 ms — il prezzo che `CODER.md` §1-bis vieta.
    ⇒ Il banco fissa il comportamento DICHIARATO: il giorno in cui cambiasse,
      questa riga diventa rossa e il rapporto si rilegge."""
    if _clic(ms, DESTRO):
        return False, ("e' uscito un clic destro da due contatti che non si "
                       "sovrappongono: il comportamento e' cambiato rispetto a "
                       "quel che il rapporto A8 dichiara — si rilegge il rapporto")
    n = _clic(ms, SINISTRO)
    if n != 2:
        return False, "attesi 2 clic sinistri (il difetto dichiarato), contati %d" % n
    return True, ("2 clic sinistri: e' il difetto DICHIARATO — sotto la "
                  "sovrapposizione di un campione un clic destro esce come "
                  "doppio clic sinistro")


def c_C5a(ms):
    """⭐ Doppio tap fermo, stesso punto ⇒ DOPPIO CLIC (4 eventi, 0 PUNTATORE)."""
    sin = [m for m in _pul(ms) if m["codice"] == SINISTRO]
    if [m["premuto"] for m in sin] != [1, 0, 1, 0]:
        return False, "non sono quattro eventi giu,su,giu,su: %s" % [
            (NOMI_BTN.get(m["codice"], m["codice"]), m["premuto"]) for m in _pul(ms)]
    if _punt(ms):
        return False, ("ci sono %d PUNTATORE dentro un doppio clic fermo: il "
                       "desktop remoto lo leggerebbe come un trascinamento"
                       % len(_punt(ms)))
    return True, "quattro eventi del sinistro, zero PUNTATORE — e' un doppio clic"


def c_C5b(ms):
    """⭐ E la STESSA apertura che poi trascina ⇒ TRASCINAMENTO.  Sono lo stesso
       gesto fino al secondo contatto: e' la refutazione, ed e' provata qui."""
    return c_G5(ms)


def c_C6(ms):
    """Il trascinamento a due dita che comincia FERMO (350 ms di attesa).
       ⛔ Un riconoscitore che decidesse «tap» al superamento di T_TAP e
          chiudesse li' non manderebbe nessuna rotella."""
    if _pul(ms):
        return False, "350 ms fermi e poi scorrimento: e' uscito un pulsante"
    if not _rot(ms):
        return False, "350 ms fermi e poi scorrimento: nessuna ROTELLA"
    return True, "%d ROTELLA dopo 350 ms di dita ferme, nessun clic" % len(_rot(ms))


def c_C7a(ms, zoom=None):
    """⭐ ROTELLA CONTRO PIZZICO — le dita si ALLONTANANO: solo zoom."""
    if _rot(ms):
        return False, ("due dita che si allontanano hanno prodotto %d ROTELLA: "
                       "pizzico e rotella si confondono" % len(_rot(ms)))
    if zoom is not None and zoom <= 1.05:
        return False, "nessuna rotella, ma nemmeno lo zoom e' cambiato (%.2f)" % zoom
    return True, "zero ROTELLA, zoom %s" % ("%.2f" % zoom if zoom else "non letto")


def c_C7b(ms, zoom=None):
    """⭐ E le dita PARALLELE: solo rotella, e la vista NON si ingrandisce."""
    if not _rot(ms):
        return False, "due dita parallele e nessuna ROTELLA"
    if zoom is not None and zoom > 1.05:
        return False, ("due dita parallele hanno ingrandito la vista a %.2fx: "
                       "e' stato letto come un pizzico" % zoom)
    return True, "%d ROTELLA, vista ferma a %s" % (
        len(_rot(ms)), "%.2f" % zoom if zoom else "?")


def c_C8(ms):
    """Il residuo: due dita scorrono, una si stacca, l'altra si muove ancora.
       ⛔ Il puntatore NON deve saltare — e' il difetto che si vede di piu',
          perche' finendo di scorrere un dito si stacca sempre un attimo prima."""
    if _punt(ms):
        return False, ("il dito rimasto dopo uno scorrimento ha mosso il "
                       "puntatore (%d PUNTATORE): a fine scorrimento il "
                       "puntatore salta" % len(_punt(ms)))
    return True, "il dito residuo non ha mosso il puntatore"


CASI = {
    "G1-un-dito-trascina": c_G1,
    "G2-un-dito-tap": c_G2,
    "G3-due-dita-tap": c_G3,
    "G4-due-dita-trascina": c_G4,
    "G5-tap-e-mezzo": c_G5,
    "G6-tre-dita-tap": c_G6,
    "G7-pizzico": c_G7,
    "C1-tap-troppo-lungo": c_C1,
    "C2-tap-che-scivola": c_C2,
    "C3-due-dita-a-30ms": c_C3,
    "C4-due-dita-senza-sovrapposizione": c_C4,
    "C5a-doppio-clic": c_C5a,
    "C5b-tap-e-mezzo-che-trascina": c_C5b,
    "C6-trascinamento-che-comincia-fermo": c_C6,
    "C7a-pizzico-non-rotella": c_C7a,
    "C7b-rotella-non-pizzico": c_C7b,
    "C8-il-dito-residuo": c_C8,
}

# Quali casi vogliono anche lo zoom letto dalla pagina.
VOGLIONO_ZOOM = {"G7-pizzico", "C7a-pizzico-non-rotella", "C7b-rotella-non-pizzico"}


def giudica(righe):
    """righe: [{"fase":…, "hex":…} | {"fase":…, "marca":True} | {"fase":…, "zoom":…}]"""
    per_fase, zoom = {}, {}
    for r in righe:
        f = r.get("fase", "?")
        if "hex" in r:
            per_fase.setdefault(f, b"")
            per_fase[f] += bytes.fromhex(r["hex"])
        elif "zoom" in r:
            zoom[f] = r["zoom"]
        else:
            per_fase.setdefault(f, b"")
    esiti = []
    for nome, fn in CASI.items():
        dati = per_fase.get(nome)
        if dati is None:
            esiti.append({"caso": nome, "verde": False,
                          "perche": "⛔ la fase non e' stata registrata affatto"})
            continue
        try:
            ms = decodifica(dati)
        except Violazione as e:
            esiti.append({"caso": nome, "verde": False,
                          "perche": "⛔ violazione di RCP.md §7.3: %s" % e})
            continue
        if nome in VOGLIONO_ZOOM:
            verde, perche = fn(ms, zoom.get(nome))
        else:
            verde, perche = fn(ms)
        esiti.append({"caso": nome, "verde": bool(verde), "perche": perche,
                      "messaggi": len(ms)})
    # ⛔ L'id cresce su TUTTO il canale, non per tipo (§7.3): si controlla una
    #    volta sola, su tutti i messaggi di tutte le fasi, in ordine di arrivo.
    # ⚠ Solo le fasi dei gesti: dopo la misura del passaggio la pagina viene
    #   RICARICATA, e su una pagina nuova il contatore riparte da 1 — che e'
    #   giusto, ed e' una sessione diversa.  Contarli insieme misurerebbe il
    #   banco, non il prodotto.
    tutti = []
    for r in righe:
        if "hex" in r and r.get("fase") in CASI:
            try:
                tutti += decodifica(bytes.fromhex(r["hex"]))
            except Violazione:
                pass
    ids = [m["id"] for m in tutti]
    cresce = all(b > a for a, b in zip(ids, ids[1:]))
    esiti.append({"caso": "R1-identificatore-crescente", "verde": bool(ids) and cresce,
                  "perche": ("%d messaggi, id da %d a %d, crescente su tutto il canale"
                             % (len(ids), ids[0], ids[-1])) if ids and cresce
                            else "gli identificatori non crescono su tutto il canale: %s"
                                 % ids[:20]})
    return esiti


# ---------------------------------------------------------------------------
# ⭐ LA CERTIFICAZIONE — verde → rosso → verde, su CINQUE guasti, uno per
#    famiglia di confusione.  ⛔ `CODER.md` §3.3: il banco si certifica prima
#    della misura, o un rosso e' ambiguo fra «non funziona» e «non funzionava
#    il banco».
# ---------------------------------------------------------------------------
def _b(tipo, mid, ist, resto):
    corpo = struct.pack(">IQ", mid, ist) + resto
    return struct.pack(">HI", tipo, len(corpo)) + corpo


class Penna:
    def __init__(self):
        self.n = 0
        self.t = 1000
        self.righe = []

    def _id(self):
        self.n += 1
        self.t += 5
        return self.n, self.t * 1000

    def punt(self, fase, x, y):
        i, t = self._id()
        self.righe.append({"fase": fase, "hex": _b(PUNTATORE, i, t,
                                                   struct.pack(">II", x, y)).hex()})

    def puls(self, fase, cod, giu):
        i, t = self._id()
        self.righe.append({"fase": fase, "hex": _b(PULSANTE, i, t,
                                                   struct.pack(">HB", cod, giu)).hex()})

    def rot(self, fase, ax, ay):
        i, t = self._id()
        self.righe.append({"fase": fase, "hex": _b(ROTELLA, i, t,
                                                   struct.pack(">ii", ax, ay)).hex()})

    def zoom(self, fase, z):
        self.righe.append({"fase": fase, "zoom": z})

    def vuota(self, fase):
        self.righe.append({"fase": fase, "marca": True})


def registrazione(guasto=None):
    """Una registrazione SANA, con un guasto opzionale iniettato."""
    p = Penna()

    def clic(fase, cod):
        p.puls(fase, cod, 1)
        p.puls(fase, cod, 0)

    f = "G1-un-dito-trascina"
    for x in range(1000, 1210, 50):
        p.punt(f, x, 540)

    clic("G2-un-dito-tap", SINISTRO)
    clic("G3-due-dita-tap", DESTRO)

    f = "G4-due-dita-trascina"
    for _ in range(3):
        p.rot(f, 0, 120 if guasto != "rotella-al-contrario" else -120)

    f = "G5-tap-e-mezzo"
    clic(f, SINISTRO)
    p.puls(f, SINISTRO, 1)
    if guasto != "tap-e-mezzo-non-trascina":
        for y in range(540, 620, 20):
            p.punt(f, 900, y)
    p.puls(f, SINISTRO, 0)

    clic("G6-tre-dita-tap", CENTRALE)

    f = "G7-pizzico"
    p.vuota(f)
    if guasto == "pizzico-manda-rotella":
        p.rot(f, 0, 120)
    p.zoom(f, 2.0)

    f = "C1-tap-troppo-lungo"
    p.vuota(f)
    if guasto == "tap-lungo-clicca":
        clic(f, SINISTRO)

    f = "C2-tap-che-scivola"
    for x in range(900, 960, 20):
        p.punt(f, x, 540)

    f = "C3-due-dita-a-30ms"
    if guasto == "trenta-ms-diventa-doppio-sinistro":
        clic(f, SINISTRO)
        clic(f, SINISTRO)
    else:
        clic(f, DESTRO)

    f = "C4-due-dita-senza-sovrapposizione"
    clic(f, SINISTRO)
    clic(f, SINISTRO)

    f = "C5a-doppio-clic"
    clic(f, SINISTRO)
    clic(f, SINISTRO)

    f = "C5b-tap-e-mezzo-che-trascina"
    clic(f, SINISTRO)
    p.puls(f, SINISTRO, 1)
    for y in range(540, 620, 20):
        p.punt(f, 900, y)
    p.puls(f, SINISTRO, 0)

    f = "C6-trascinamento-che-comincia-fermo"
    for _ in range(2):
        p.rot(f, 0, 120)

    f = "C7a-pizzico-non-rotella"
    p.vuota(f)
    p.zoom(f, 1.8)

    f = "C7b-rotella-non-pizzico"
    for _ in range(2):
        p.rot(f, 0, 120)
    p.zoom(f, 1.0)

    p.vuota("C8-il-dito-residuo")
    return p.righe


GUASTI = [
    ("tap-lungo-clicca", "C1-tap-troppo-lungo",
     "un contatto di 400 ms fermo che manda un clic (la soglia T_TAP non guardata)"),
    ("trenta-ms-diventa-doppio-sinistro", "C3-due-dita-a-30ms",
     "due dita a 30 ms che escono come due clic sinistri invece di un destro"),
    ("rotella-al-contrario", "G4-due-dita-trascina",
     "il segno della rotella invertito (`RCP.md` §7.3, forma E11)"),
    ("tap-e-mezzo-non-trascina", "G5-tap-e-mezzo",
     "il tap-e-mezzo che preme e rilascia senza trascinare — cioe' un doppio clic"),
    ("pizzico-manda-rotella", "G7-pizzico",
     "il pizzico che spedisce una rotella invece di ingrandire la vista"),
]


def certifica():
    print("⭐ CERTIFICAZIONE DEL GIUDICE — verde → rosso → verde, su cinque")
    print("   guasti, uno per famiglia di confusione.\n")
    sano = giudica(registrazione())
    rossi = [e for e in sano if not e["verde"]]
    if rossi:
        print("⛔ la registrazione SANA non e' verde: il giudice e' rotto.")
        for e in rossi:
            print("     %-40s %s" % (e["caso"], e["perche"]))
        return 1
    print("  ✅ registrazione SANA: %d casi, tutti verdi" % len(sano))

    ok = True
    for guasto, caso, testo in GUASTI:
        esiti = giudica(registrazione(guasto))
        mio = [e for e in esiti if e["caso"] == caso][0]
        altri = [e["caso"] for e in esiti if not e["verde"] and e["caso"] != caso]
        if mio["verde"]:
            print("  ⛔ guasto «%s»: il giudice NON lo vede." % guasto)
            print("       %s" % testo)
            ok = False
        elif altri:
            print("  ⚠ guasto «%s»: visto, ma ha tinto di rosso anche %s"
                  % (guasto, altri))
            print("       (un giudice che sanguina non sa dire DOVE sta il difetto)")
            ok = False
        else:
            print("  ✅ %-36s rosso solo su %s" % (guasto, caso))
            print("       ↳ %s" % testo)

    risanato = giudica(registrazione())
    if [e for e in risanato if not e["verde"]]:
        print("⛔ la registrazione RISANATA non torna verde.")
        return 1
    print("  ✅ registrazione RISANATA: torna verde")
    print("\n%s" % ("⭐ il giudice e' certificato." if ok
                    else "⛔ il giudice NON e' certificato: non si misura niente."))
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# IL SERVITORE E LA CUCITURA — la stessa forma di `04-b27-classico.py`.
# ---------------------------------------------------------------------------
class Raccolta:
    def __init__(self):
        self.righe = []
        self.fase = "F-nessuna"
        self.blocco = threading.Lock()
        self.byte = 0

    def marca(self, fase):
        with self.blocco:
            self.fase = fase
            self.righe.append({"t": time.time(), "fase": fase, "marca": True})

    def aggiungi(self, dati):
        with self.blocco:
            self.byte += len(dati)
            self.righe.append({"t": time.time(), "fase": self.fase, "hex": dati.hex()})

    def zoom(self, fase, z):
        with self.blocco:
            self.righe.append({"t": time.time(), "fase": fase, "zoom": z})


def servitore(porta, raccolta, pagina_html):
    class H(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def _corpo(self, tipo, dati, stato=200):
            self.send_response(stato)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(dati)))
            self.end_headers()
            self.wfile.write(dati)

        def do_GET(self):
            p = self.path.split("?")[0].split("#")[0]
            if p == "/":
                self._corpo("text/html; charset=utf-8", pagina_html)
            else:
                self._corpo("text/plain", b"non c'e'", 404)

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            dati = self.rfile.read(n)
            p = self.path.split("?")[0]
            if p == "/byte":
                raccolta.aggiungi(dati)
            elif p == "/fase":
                raccolta.marca(dati.decode("utf-8", "replace"))
            self._corpo("text/plain", b"ok")

    # ⛔ `allow_reuse_address` va messo sulla CLASSE: `TCPServer.__init__` lega
    #    la porta subito, e `server_bind()` legge l'attributo PRIMA che si possa
    #    scriverlo sull'istanza.  ⚠ Scritto dopo, non ha nessun effetto — e il
    #    sintomo e' «Address already in use» al giro dopo, con la porta che
    #    `ss` dichiara libera perche' e' solo in TIME_WAIT.
    class _Servitore(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    s = _Servitore(("127.0.0.1", porta), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


# ---------------------------------------------------------------------------
# ⛔⭐ LA GUIDA AL BROWSER, CON IL RIAGGANCIO.
#
# `[M]` 14 agosto 2026, Chrome 151.0.7922.137: `Input.dispatchTouchEvent`
# **non torna** in alcune condizioni (dopo un evento di mouse, e dopo un
# identificatore di contatto riciclato).  ⇒ Il primo giro di questo banco moriva
# a meta' e buttava via sedici misure buone per un difetto della guida.
#
# ⛔ E non si finge che non sia successo: ogni riaggancio finisce in `guasti`,
#    che va nel registro degli esiti — cosi' un rosso si puo' attribuire allo
#    strumento invece che al prodotto (`CODER.md` §3.10, §3.11).
# ---------------------------------------------------------------------------
class Guida:
    def __init__(self, modulo, url, timeout=20):
        self._m = modulo
        self._url = url
        self._t = timeout
        self.c = modulo.Cdp(url, timeout)
        self.guasti = []

    def riaggancia(self, perche):
        self.guasti.append(perche)
        try:
            self.c.chiudi()
        except Exception:                      # noqa: BLE001
            pass
        time.sleep(0.6)
        self.c = self._m.Cdp(self._url, self._t)
        self.c.chiama("Runtime.enable")
        try:
            self.c.chiama("Emulation.setTouchEmulationEnabled",
                          enabled=True, maxTouchPoints=5)
        except Exception:                      # noqa: BLE001
            pass

    def chiama(self, metodo, **p):
        return self.c.chiama(metodo, **p)

    def valuta(self, e, attendi=True):
        return self.c.valuta(e, attendi)


def _cdp():
    p = os.path.join(QUI, "02-pagina-misura-cdp.py")
    spec = importlib.util.spec_from_file_location("cdpmod", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ⛔ La cucitura che l'ancora `F4-TOCCO` chiede, messa dal banco.  E' la stessa
#    di `04-b27-classico.py`: il coordinatore la scrivera' in `collega()` sullo
#    stream unidirezionale di §2.5, qui spedisce a questo processo.
#    ⚠ E' l'unica differenza fra banco e prodotto, ed e' dichiarata: il
#      TRASPORTO non e' misurato qui.
PROLOGO = r"""
(function () {
  var n = 0, coda = Promise.resolve();
  window.__b28 = { spediti: 0, errori: [] };
  window.REMOTIX_INPUT = {
    prossimo_id: function () { n = (n >= 4294967295) ? 1 : n + 1; return n; },
    manda: function (tipo, corpo) {
      var m = new Uint8Array(6 + corpo.length);
      var v = new DataView(m.buffer);
      v.setUint16(0, tipo); v.setUint32(2, corpo.length); m.set(corpo, 6);
      window.__b28.spediti++;
      coda = coda.then(function () { return fetch("/byte", { method: "POST", body: m }); })
                 .catch(function (e) { window.__b28.errori.push(String(e)); });
    },
  };
  window.__b28.fase = function (nome) {
    coda = coda.then(function () { return fetch("/fase", { method: "POST", body: nome }); })
               .catch(function (e) { window.__b28.errori.push(String(e)); });
    return coda;
  };
  window.__b28.attendi = function () { return coda.then(function () { return true; }); };
  /* ⛔⭐ LA SPIA — `CODER.md` §3.7: «non si deduce il mittente: lo si chiede».
     Registra che cosa il BROWSER ha davvero consegnato alla pagina, cosi' un
     rosso del passaggio automatico si puo' attribuire — al prodotto, o al banco
     che non ha consegnato l'evento che credeva di aver mandato.
     ⚠ Sono osservazioni del banco su Chrome: nessun verdetto si costruisce su
       questi campi, servono a dire DOVE guardare. */
})()
"""

# ⛔⭐ LA SPIA DELLA SCHEDA DEL PASSAGGIO — `CODER.md` §3.7: «non si deduce il
#     mittente: lo si chiede al nucleo».  Registra che cosa il BROWSER ha
#     davvero consegnato alla pagina, cosi' un rosso del passaggio si puo'
#     attribuire: al prodotto, o al banco che non ha consegnato l'evento.
# ⚠ E' PASSIVA: un ascoltatore non passivo su `touchstart` blocca
#   `Input.dispatchTouchEvent` — misurato il 14 agosto 2026.
SPIA = r"""
(function () {
  window.__spia = [];
  var p = { capture: true, passive: true };
  addEventListener("pointerdown", function (e) {
    window.__spia.push(["pointerdown", e.pointerType]); }, p);
  addEventListener("touchstart", function (e) {
    window.__spia.push(["touchstart", e.touches.length]); }, p);
  addEventListener("mousedown", function () {
    window.__spia.push(["mousedown", 0]); }, p);
})()
"""

# ⛔ La scena della pagina: si accende la tela e le si da' una cornice NOTA, o
#    non si saprebbe dove toccare.  ⚠ E' quel che `04-b27` fa per il classico.
SCENA = r"""
(function () {
  document.body.dataset.schermo = "acceso";
  const t = document.getElementById("schermo");
  t.width = %d; t.height = %d;
  t.style.width = "960px"; t.style.height = "540px";
  const s = window.REMOTIX && window.REMOTIX.tocco;
  if (!s) return JSON.stringify({errore: "⛔ REMOTIX.tocco non esiste"});
  const r = t.getBoundingClientRect();
  return JSON.stringify({ disposizione: document.body.dataset.disposizione,
                          perche: s.perche(), contesto: s.contesto(),
                          soglie: s.soglie, stato: s.stato(),
                          cornice: [r.left, r.top, r.width, r.height] });
})()
"""


def gira(porta, diagnosi, esiti_f, registro_f, attesa=30):
    cdp = _cdp()
    with open(os.path.join(RADICE, "src", "pagina.html"), "rb") as f:
        html = f.read()
    for chiave, valore in ((b"__IMPRONTA__", b""), (b"__AVVISO__", b""),
                           (b"__BANNATO__", b"no"), (b"__RESTANO_MS__", b"0")):
        html = html.replace(chiave, valore)
    raccolta = Raccolta()
    s = servitore(porta, raccolta, html)
    print("  servitore su http://127.0.0.1:%d — pagina del PRODOTTO, %d byte"
          % (porta, len(html)))

    b = cdp.pagina(diagnosi, attesa)
    c = Guida(cdp, b["webSocketDebuggerUrl"], timeout=20)
    c.chiama("Page.enable")
    c.chiama("Runtime.enable")
    c.chiama("Page.addScriptToEvaluateOnNewDocument", source=PROLOGO)
    # ⛔ Il tocco si DICHIARA: senza, un Chrome da scrivania non consegna
    #    nessun evento `Touch` e il banco misurerebbe il proprio silenzio.
    c.chiama("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=5)
    # ⛔⭐ LA FINESTRA DEVE ESSERE DAVANTI E ATTIVA, E NON E' UN VEZZO.
    #  `[M]` 14 agosto 2026: `Input.dispatchTouchEvent` **non torna** in modo
    #  intermittente, in fasi diverse a ogni giro.  Il banco gira sul desktop
    #  VERO dell'utente (e' quel che il mandato chiede): quando la finestra
    #  finisce dietro un'altra, il renderer smette di produrre quadri — e' lo
    #  stesso fatto che `STUDI.md` §web §6.2 misura su Xvfb, «senza schermo non c'e'
    #  scanout» — e l'assenso all'evento di input non arriva mai.
    #  ⇒ Si dichiara alla pagina che il fuoco ce l'ha, e si porta la finestra
    #    davanti.  ⚠ E' una dichiarazione sulla SCENA, non una cura del
    #    prodotto: il palco si dichiara, non si sposta.
    try:
        c.chiama("Emulation.setFocusEmulationEnabled", enabled=True)
    except Exception:                          # noqa: BLE001
        print("  ⚠ questo Chrome non ha `setFocusEmulationEnabled`")
    try:
        c.chiama("Page.bringToFront")
    except Exception:                          # noqa: BLE001
        pass
    c.chiama("Page.navigate",
             url="http://127.0.0.1:%d/?disposizione=tocco" % porta)
    time.sleep(2.0)

    scena = {
        "macchina": os.uname().nodename,
        "sessione": os.environ.get("XDG_SESSION_TYPE"),
        "wayland": os.environ.get("WAYLAND_DISPLAY"),
        "display": os.environ.get("DISPLAY"),
        "browser": c.valuta("navigator.userAgent"),
        "tela": list(TELA),
        "quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    acceso = c.valuta(SCENA % TELA)
    if not acceso:
        print("  ⛔ la pagina non ha risposto alla scena")
        s.shutdown()
        return 3, scena, []
    pag = json.loads(acceso)
    scena["pagina"] = pag
    print("  scena:", json.dumps(scena, ensure_ascii=False)[:600])
    if pag.get("errore"):
        print("  " + pag["errore"])
        s.shutdown()
        return 3, scena, []
    if pag.get("disposizione") != "tocco":
        print("  ⛔ la disposizione in vigore e' «%s», non «tocco»: il banco "
              "misurerebbe l'altra meta' della pagina" % pag.get("disposizione"))
        s.shutdown()
        return 3, scena, []

    cx, cy, cw, ch = pag["cornice"]
    ox, oy = cx + cw / 2, cy + ch / 2      # il centro della tela, in px CSS

    # ── LA MANO SINTETICA ──────────────────────────────────────────────────
    # ⛔ CDP vuole i punti ATTIVI a ogni evento: al `touchEnd` si mandano quelli
    #    che RESTANO, e il rilasciato si omette.  Sbagliarlo vuol dire misurare
    #    una mano che nessuno ha mai fatto.
    #
    # ⛔⭐ E OGNI CONTATTO NUOVO PRENDE UN IDENTIFICATORE NUOVO — `[M]` 14 agosto
    #     2026, e la riga e' nata da un BLOCCO del banco, non da un ragionamento.
    #
    #  Riusando l'identificatore `1` per il secondo contatto del tap-e-mezzo,
    #  `Input.dispatchTouchEvent` **non tornava piu'**: la chiamata CDP scadeva
    #  al primo `touchMove` dopo il riappoggio, in modo riproducibile (caso C5b,
    #  due giri su due).  ⛔ E' un difetto dello STRUMENTO, non del prodotto.
    #
    # ⭐ E l'identificatore nuovo e' anche piu' fedele al vero: un pannello
    #    tattile assegna un `tracking id` NUOVO a ogni contatto nuovo, e non
    #    ricicla quello appena rilasciato.  ⇒ Il banco ora prova il tap-e-mezzo
    #    con due identificatori DIVERSI, che e' quel che succede con un dito
    #    vero — e prova per forza che il riconoscitore lo aggancia sullo SPAZIO
    #    (40 px) e sul TEMPO (300 ms), mai sull'identita' del contatto.
    attivi = {}
    posti = {}
    prossimo = [100]

    def _manda(tipo):
        c.chiama("Input.dispatchTouchEvent", type=tipo,
                 touchPoints=[{"x": float(v[0]), "y": float(v[1]), "id": k}
                              for k, v in attivi.items()])

    def giu(i, x, y):
        prossimo[0] += 1
        posti[i] = prossimo[0]
        attivi[posti[i]] = (ox + x, oy + y)
        _manda("touchStart")

    def muovi(punti):
        for i, x, y in punti:
            if i in posti:
                attivi[posti[i]] = (ox + x, oy + y)
        _manda("touchMove")

    def su(i):
        attivi.pop(posti.pop(i, None), None)
        _manda("touchEnd")

    def dorme(ms):
        time.sleep(ms / 1000.0)

    def fase(nome):
        c.valuta("window.__b28.attendi()")
        c.valuta("window.__b28.fase(%s)" % json.dumps(nome))
        c.valuta("window.__b28.attendi()")

    def zoom_azzera():
        # ⚠ Non e' un interruttore del prodotto: e' un PIZZICO al contrario,
        #   fatto con le stesse dita sintetiche, per riportare la vista a 1x.
        giu(80, -150, 0)
        giu(81, 150, 0)
        for k in range(1, 7):
            muovi([(80, -150 + 24 * k, 0), (81, 150 - 24 * k, 0)])
            dorme(16)
        su(80)
        su(81)
        dorme(60)

    def leggi_zoom(nome):
        z = c.valuta("window.REMOTIX.tocco.stato().zoom")
        raccolta.zoom(nome, z if isinstance(z, (int, float)) else 0)

    def riposa():
        # ⛔ Oltre `T_SEQUENZA` (300 ms), o il gesto dopo si aggancerebbe come
        #    tap-e-mezzo a quello prima: e' proprio la trappola che il banco
        #    deve evitare di infilarsi da solo.
        dorme(450)

    # ══════════════════════════════════════════════════════════════════════
    # LE SCENE, UNA FUNZIONE PER GESTO.
    #
    # ⛔ E OGNI SCENA E' PROTETTA: un guasto dello STRUMENTO (la chiamata CDP
    #    che non torna) non deve buttare via le altre sedici misure, e ⛔ non
    #    deve nemmeno passare per un esito.  ⇒ Si riaggancia, si annulla il
    #    tocco in corso, la fase resta SENZA byte — e il giudice la dichiara
    #    rossa con «la fase non e' stata registrata affatto», che e' la verita'.
    #    ⚠ `CODER.md` §3.10: «una lettura negata non e' una lettura che dice
    #      zero».  I guasti finiscono in `04-b28-esiti.jsonl` sotto `guasti`,
    #      cosi' un rosso si puo' attribuire al banco invece che al prodotto.
    # ══════════════════════════════════════════════════════════════════════

    def f_G1():
        giu(1, -200, 0)
        for k in range(1, 11):
            muovi([(1, -200 + 20 * k, 0)])
            dorme(16)
        su(1)

    def f_G2():
        giu(1, 0, 0)
        dorme(80)
        su(1)

    def f_G3():
        giu(1, -30, 0)
        giu(2, 30, 0)
        dorme(80)
        su(1)
        su(2)

    def _due_dita_scendono():
        giu(1, -30, -100)
        giu(2, 30, -100)
        for k in range(1, 9):
            muovi([(1, -30, -100 + 25 * k), (2, 30, -100 + 25 * k)])
            dorme(16)
        su(1)
        su(2)

    def f_G4():
        # Le dita SCENDONO ⇒ `RCP.md` §7.3 vuole l'asse verticale POSITIVO.
        _due_dita_scendono()

    def f_G5():
        giu(1, 0, 0)
        dorme(80)
        su(1)
        dorme(90)            # dentro i 300 ms di T_SEQUENZA
        giu(1, 3, 3)         # e dentro i 40 px di D_STESSO_DITO
        dorme(30)
        for k in range(1, 9):
            muovi([(1, 3, 3 + 20 * k)])
            dorme(16)
        su(1)

    def f_G6():
        # ⛔⭐ QUI SI TIENE PREMUTO 20 ms E NON 80, E IL MOTIVO E' MISURATO.
        #
        # `[M]` 14 agosto 2026: con 80 ms di attesa il tap a tre dita usciva
        # **senza clic centrale**, e il riconoscitore era corretto.  Sonda
        # diretta: `durata_max` = **147 ms** su una soglia di 180 — cioe' la
        # MANO SINTETICA da sola costa ~120 ms, perche' tre dita giu' e tre su
        # sono SEI andate-e-ritorni CDP a ~20 ms l'uno.
        #
        # ⇒ Il banco stava misurando la latenza del proprio strumento, non il
        #   gesto (`LEZIONI.md` §1.11).  Si toglie l'attesa, e il tempo che
        #   resta e' quello vero dei sei viaggi.
        # ⭐ E resta una domanda per Nic, che nessun banco chiude: **180 ms per
        #    contatto bastano a un tap a tre dita fatto con una mano vera?**
        #    Tre dita non si staccano insieme, e questo e' proprio il caso in
        #    cui la soglia si giudica usandola.
        giu(1, -40, 0)
        giu(2, 0, 0)
        giu(3, 40, 0)
        dorme(20)
        su(1)
        su(2)
        su(3)

    def _allontana():
        giu(1, -60, 0)
        giu(2, 60, 0)
        for k in range(1, 9):
            muovi([(1, -60 - 15 * k, 0), (2, 60 + 15 * k, 0)])
            dorme(16)
        su(1)
        su(2)
        dorme(60)

    def f_G7():
        _allontana()
        leggi_zoom("G7-pizzico")
        zoom_azzera()

    def f_C1():
        # Il tap che dura un po' troppo: 400 ms, e FERMO.  T_TAP = 180 ms.
        giu(1, 0, 0)
        dorme(400)
        su(1)

    def f_C2():
        # Il tap che scivola: 120 ms, ma 30 px.  D_TAP = 9 px CSS.
        giu(1, 0, 0)
        for k in range(1, 4):
            muovi([(1, 10 * k, 0)])
            dorme(30)
        su(1)

    def f_C3():
        # ⭐ Le due dita che si appoggiano a 30 ms di distanza — MA si
        #    sovrappongono: e' la soglia dichiarata.
        giu(1, -30, 0)
        dorme(30)
        giu(2, 30, 0)
        dorme(70)
        su(1)
        dorme(20)
        su(2)

    def f_C4():
        # ⛔ E le due dita che NON si sovrappongono MAI: il difetto dichiarato.
        giu(1, -30, 0)
        dorme(90)
        su(1)
        dorme(40)
        giu(2, 30, 0)
        dorme(90)
        su(2)

    def f_C5a():
        # Doppio tap fermo, stesso punto ⇒ DOPPIO CLIC.
        giu(1, 0, 0)
        dorme(70)
        su(1)
        dorme(90)
        giu(1, 2, 2)
        dorme(70)
        su(1)

    def f_C5b():
        # ⭐ La STESSA apertura, e poi trascina ⇒ TRASCINAMENTO.
        giu(1, 0, 0)
        dorme(70)
        su(1)
        dorme(90)
        giu(1, 2, 2)
        dorme(40)
        for k in range(1, 9):
            muovi([(1, 2 + 18 * k, 2)])
            dorme(16)
        su(1)

    def f_C6():
        # Il trascinamento a due dita che comincia FERMO.
        giu(1, -30, -100)
        giu(2, 30, -100)
        dorme(350)
        for k in range(1, 9):
            muovi([(1, -30, -100 + 25 * k), (2, 30, -100 + 25 * k)])
            dorme(16)
        su(1)
        su(2)

    def f_C7a():
        _allontana()
        leggi_zoom("C7a-pizzico-non-rotella")
        zoom_azzera()

    def f_C7b():
        _due_dita_scendono()
        dorme(60)
        leggi_zoom("C7b-rotella-non-pizzico")

    def f_C8():
        # Il dito residuo: due scorrono, una si stacca, l'altra continua.
        giu(1, -30, -100)
        giu(2, 30, -100)
        for k in range(1, 5):
            muovi([(1, -30, -100 + 25 * k), (2, 30, -100 + 25 * k)])
            dorme(16)
        su(1)
        for k in range(1, 5):
            muovi([(2, 30 + 20 * k, 0)])
            dorme(16)
        su(2)

    SCENE = [
        ("G1-un-dito-trascina", f_G1),
        ("G2-un-dito-tap", f_G2),
        ("G3-due-dita-tap", f_G3),
        ("G4-due-dita-trascina", f_G4),
        ("G5-tap-e-mezzo", f_G5),
        ("G6-tre-dita-tap", f_G6),
        ("G7-pizzico", f_G7),
        ("C1-tap-troppo-lungo", f_C1),
        ("C2-tap-che-scivola", f_C2),
        ("C3-due-dita-a-30ms", f_C3),
        ("C4-due-dita-senza-sovrapposizione", f_C4),
        ("C5a-doppio-clic", f_C5a),
        ("C5b-tap-e-mezzo-che-trascina", f_C5b),
        ("C6-trascinamento-che-comincia-fermo", f_C6),
        ("C7a-pizzico-non-rotella", f_C7a),
        ("C7b-rotella-non-pizzico", f_C7b),
        ("C8-il-dito-residuo", f_C8),
    ]
    assert sorted(n for n, _ in SCENE) == sorted(CASI), \
        "le scene e i casi del giudice non combaciano"

    verdetti = {}
    guasti_di_fase = []
    for nome, fn in SCENE:
        # ⛔ UN TENTATIVO SOLO, e il secondo NON si fa.  Riprovando, i byte del
        #    tentativo mezzo riuscito restano nella fase e si sommano a quelli
        #    del secondo: il giudice leggeva «tre eventi del sinistro su
        #    quattro» su un gesto che il prodotto aveva fatto due volte bene.
        #    ⇒ Un guasto dello strumento si DICHIARA, non si nasconde con una
        #      ripetizione (`CODER.md` §3.10: «una lettura negata non e' una
        #      lettura che dice zero»).
        for tentativo in (1,):
            try:
                fase(nome)
                fn()                # ⛔ Il verdetto che la PAGINA ha dato al gesto, coi suoi numeri:
                #    quando un caso e' rosso, dice quale condizione ha ceduto —
                #    durata, sbavatura o decisione — invece di lasciarlo dedurre.
                try:
                    verdetti[nome] = json.loads(c.valuta(
                        "JSON.stringify(window.REMOTIX.tocco.stato().ultimo_gesto)")
                        or "null")
                except Exception:              # noqa: BLE001
                    pass
                break
            except (TimeoutError, OSError, RuntimeError) as e:
                print("  ⚠ GUASTO DELLO STRUMENTO nella fase %s (%s)"
                      % (nome, type(e).__name__))
                guasti_di_fase.append(nome)
                c.riaggancia("fase %s: %s" % (nome, type(e).__name__))
                attivi.clear()
                posti.clear()
                try:
                    c.chiama("Input.dispatchTouchEvent", type="touchCancel",
                             touchPoints=[])
                except Exception:              # noqa: BLE001
                    pass
                dorme(400)
        riposa()

    fase("F-fine")

    c.valuta("window.__b28.attendi()")
    time.sleep(0.5)

    # ── ⒝ IL PASSAGGIO AUTOMATICO, e S1 la cucitura ───────────────────────
    passaggio = misura_passaggio(c, cdp, porta, ox, oy, diagnosi)
    scena["passaggio"] = passaggio
    scena["verdetti_della_pagina"] = verdetti
    scena["guasti_dello_strumento"] = list(c.guasti)
    if c.guasti:
        print("  ⚠ %d guasti dello strumento, riagganciati: %s"
              % (len(c.guasti), c.guasti))

    with raccolta.blocco:
        righe = list(raccolta.righe)
    s.shutdown()

    with open(registro_f, "w", encoding="utf-8") as f:
        for r in righe:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    esiti = giudica(righe)
    esiti += passaggio["esiti"]
    # ⛔ Le fasi in cui lo STRUMENTO si e' guastato non si contano fra i rossi
    #    del prodotto — e non si contano nemmeno fra i verdi.  Restano NON
    #    MISURATE, con un segno tutto loro, e il banco esce con un codice
    #    diverso: «da rifare», non «il prodotto e' rotto».
    for e in esiti:
        if e["caso"] in guasti_di_fase:
            e["strumento"] = True
    return 0, scena, esiti


# ⛔ Il passaggio si misura su QUALE DISPOSIZIONE E' IN VIGORE, letta dal
#    documento — non «esiste una funzione che la cambia».
def misura_passaggio(c_vecchia, cdp, porta, ox, oy, diagnosi):
    """⛔⭐ IL PASSAGGIO SI MISURA IN UNA SCHEDA NUOVA, E NON E' UNA COMODITA'.

    `[M]` 14 agosto 2026, Chrome 151.0.7922.137.  Misurando il passaggio nella
    **stessa** scheda dei gesti — cioe' dopo una seconda `Page.navigate` e dopo
    un evento di mouse — ⛔ `Input.dispatchTouchEvent` **non consegna piu'
    niente alla pagina**: la spia del prologo non registra ne' un `touchstart`
    ne' un `pointerdown` di tipo `touch`, e la chiamata CDP torna senza errore.
    ⇒ Il banco leggeva «dopo un DITO: classico» e accusava il PRODOTTO.

    ⭐ In una scheda appena aperta la stessa sequenza funziona, e il passaggio
       si misura per intero: avvio → **tocco**, mouse → **classico**, dito →
       **tocco**.  ⚠ `CODER.md` §3.11: il sospetto va prima sulla misura.
    """
    import urllib.request
    esiti, note = [], {}

    # Una scheda nuova, sua, chiusa alla fine.
    with urllib.request.urlopen(urllib.request.Request(
            "http://127.0.0.1:%d/json/new?about:blank" % diagnosi,
            method="PUT"), timeout=10) as r:
        scheda = json.loads(r.read().decode())
    c = Guida(cdp, scheda["webSocketDebuggerUrl"], timeout=20)
    c.chiama("Page.enable")
    c.chiama("Runtime.enable")
    c.chiama("Page.addScriptToEvaluateOnNewDocument", source=SPIA)
    c.chiama("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=5)

    # ⛔⭐ UN DIFETTO DELLO STRUMENTO, MISURATO E AGGIRATO — `[M]` 14 agosto 2026,
    #     Chrome 151.0.7922.137 su CHUWI.
    #
    # Dopo un `Input.dispatchMouseEvent`, il successivo `Input.dispatchTouchEvent`
    # **non torna mai**: la chiamata CDP scade in attesa di una risposta che non
    # arriva.  ⇒ Il primo giro di questo banco leggeva «dopo un TOCCO: classico»
    # e accusava il PRODOTTO di non tornare al tocco.
    #
    # ⚠ `CODER.md` §3.11 — «quando codice letto e misura si contraddicono, il
    #   sospetto va PRIMA sulla misura».  Qui il codice diceva che il passaggio
    #   c'era e la misura diceva di no: aveva ragione il codice.
    #
    # ⭐ La cura: si riaccende l'emulazione del tocco dopo ogni evento di mouse.
    #    Misurato: avvio «tocco» → dito «tocco» → mouse «classico» → dito
    #    «tocco».  ⛔ E si dichiara qui invece di nasconderla in una riga.
    def mouse():
        c.chiama("Input.dispatchMouseEvent", type="mousePressed", x=ox, y=oy,
                 button="left", clickCount=1, buttons=1)
        c.chiama("Input.dispatchMouseEvent", type="mouseReleased", x=ox, y=oy,
                 button="left", clickCount=1, buttons=0)
        time.sleep(0.3)
        c.chiama("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=5)

    # ⚠ Identificatore NUOVO a ogni contatto, come nella mano sintetica: un id
    #   riciclato blocca `Input.dispatchTouchEvent` (misurato, vedi sopra).
    dito_id = [200]

    def dito(pt=None):
        dito_id[0] += 1
        # ⛔ L'emulazione del tocco si RIACCENDE prima di ogni contatto — `[M]`
        #    14 agosto 2026, e la spia della pagina e' quella che l'ha detto:
        #    dopo la seconda navigazione e dopo un evento di mouse i
        #    `touchStart` NON arrivavano piu' alla pagina (nessun `touchstart`
        #    e nessun `pointerdown` di tipo touch nella spia), e il banco
        #    accusava il PRODOTTO di non tornare al tocco.  ⚠ `CODER.md` §3.7:
        #    non si deduce il mittente, lo si chiede.
        c.chiama("Emulation.setTouchEmulationEnabled", enabled=True,
                 maxTouchPoints=5)
        c.chiama("Input.dispatchTouchEvent", type="touchStart",
                 touchPoints=[{"x": pt[0] if pt else ox, "y": pt[1] if pt else oy,
                               "id": dito_id[0]}])
        c.chiama("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])
        time.sleep(0.3)

    def disposizione():
        return c.valuta("document.body.dataset.disposizione")

    def stato():
        v = c.valuta("JSON.stringify(window.REMOTIX.tocco.stato())")
        return json.loads(v) if v else {}

    def spediti():
        return c.valuta("window.__b28.spediti") or 0

    # ── D1 · la disposizione forzata e' davvero in vigore, e il tocco parla ─
    #    ⚠ Si legge sulla scheda dei GESTI, non su quella nuova.
    d = c_vecchia.valuta("document.body.dataset.disposizione")
    esiti.append({"caso": "D1-disposizione-in-vigore", "verde": d == "tocco",
                  "perche": "`body[data-disposizione]` = «%s» (il PRODOTTO l'ha "
                            "scritto, non il banco)" % d})

    # ── D2 · ⭐ IL PASSAGGIO VERO, su eventi VERI ──────────────────────────
    # Si toglie la forzatura ricaricando senza `?disposizione`, poi si usa il
    # mouse (⇒ classico) e poi il dito (⇒ tocco).  ⛔ Non si emula nessun
    # hardware: si mandano eventi che il browser consegna come qualunque altro.
    c.chiama("Page.navigate", url="http://127.0.0.1:%d/" % porta)
    time.sleep(2.0)
    c.valuta(SCENA % TELA)
    d0 = disposizione()
    note["allavvio"] = {"disposizione": d0,
                        "perche": c.valuta("window.REMOTIX.tocco.perche()"),
                        "contesto": json.loads(
                            c.valuta("JSON.stringify(window.REMOTIX.tocco.contesto())"))}

    dito()
    d_dito0 = disposizione()
    mouse()
    d_mouse = disposizione()
    dito()
    d_dito = disposizione()

    note["spia"] = json.loads(c.valuta("JSON.stringify(window.__spia)") or "[]")
    verde = (d_dito0 == "tocco" and d_mouse == "classico" and d_dito == "tocco")
    esiti.append({"caso": "D2-passaggio-automatico", "verde": verde,
                  "perche": ("all'avvio «%s»; dopo un DITO «%s»; dopo un CLIC di "
                             "mouse «%s»; dopo un altro DITO «%s»"
                             % (d0, d_dito0, d_mouse, d_dito))
                            + ("" if verde else
                               "  ⛔ atteso tocco → classico → tocco; la spia dice: %s"
                               % note["spia"][-8:])})

    # ── D3 · ⭐ «in vigore» vuol dire che l'ALTRA E' SPENTA ────────────────
    # In classico, un tocco completo NON deve produrre nessun messaggio del
    # tocco: i gestori sono staccati davvero, non solo dichiarati staccati.
    mouse()
    if disposizione() != "classico":
        esiti.append({"caso": "D3-l-altra-e-spenta", "verde": False,
                      "perche": "non si e' riusciti a rientrare nel classico"})
    else:
        # ⛔ Prima: in CLASSICO il tocco dev'essere spento e il classico acceso.
        t_prima = json.loads(c.valuta("JSON.stringify(window.REMOTIX.tocco.stato())"))
        cl_prima = json.loads(c.valuta(
            "JSON.stringify(window.REMOTIX.input_classico.stato())"))
        prima = c.valuta("window.REMOTIX.tocco.spediti.length")
        c.chiama("Input.dispatchTouchEvent", type="touchStart",
                 touchPoints=[{"x": ox - 100, "y": oy, "id": 7}])
        for k in range(1, 6):
            c.chiama("Input.dispatchTouchEvent", type="touchMove",
                     touchPoints=[{"x": ox - 100 + 30 * k, "y": oy, "id": 7}])
            time.sleep(0.02)
        c.chiama("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])
        time.sleep(0.3)
        dopo = c.valuta("window.REMOTIX.tocco.spediti.length")
        cl = json.loads(c.valuta(
            "JSON.stringify(window.REMOTIX.input_classico.stato())"))
        nuovi = json.loads(c.valuta(
            "JSON.stringify(window.REMOTIX.tocco.spediti.slice(%d))" % prima) or "[]")
        d_fin = disposizione()
        # ⛔⭐ «IN VIGORE» VUOL DIRE CHE L'ALTRA E' SPENTA, e si prova su tre
        #    fatti osservabili, non su una variabile che dice cosi':
        #
        #   1. prima del gesto, in CLASSICO: il tocco e' spento e il classico
        #      acceso — le due meta' non sono mai accese insieme;
        #   2. dopo il gesto, in TOCCO: il classico e' spento;
        #   3. ⛔ e il trascinamento cominciato NELL'ALTRA disposizione non
        #      produce **nessun clic fantasma**: puo' muovere il puntatore (il
        #      contatto e' quello che fa passare al tocco, ed e' giusto che il
        #      gesto non vada perso), ma un PULSANTE li' dentro vorrebbe dire
        #      che un mezzo gesto e' stato preso per un gesto intero.
        clic = [m for m in nuovi if m.get("nome") == "PULSANTE"]
        verde = (t_prima.get("in_vigore") is False
                 and cl_prima.get("in_vigore") is True
                 and d_fin == "tocco" and not cl.get("in_vigore")
                 and not clic)
        esiti.append({"caso": "D3-l-altra-e-spenta", "verde": verde,
                      "perche": ("in classico: tocco in vigore %s, classico in "
                                 "vigore %s; dopo il gesto: disposizione «%s», "
                                 "classico in vigore %s; il gesto ha prodotto %d "
                                 "messaggi, di cui %d PULSANTE (clic fantasma)"
                                 % (t_prima.get("in_vigore"),
                                    cl_prima.get("in_vigore"), d_fin,
                                    cl.get("in_vigore"), dopo - prima, len(clic)))})

    # ── S1 · ⭐ LA CUCITURA fra le due ancore ──────────────────────────────
    c.chiama("Input.dispatchTouchEvent", type="touchStart",
             touchPoints=[{"x": ox, "y": oy, "id": 5}])
    for k in range(1, 6):
        c.chiama("Input.dispatchTouchEvent", type="touchMove",
                 touchPoints=[{"x": ox + 25 * k, "y": oy, "id": 5}])
        time.sleep(0.02)
    c.chiama("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])
    time.sleep(0.3)
    st = stato()
    visibile = c.valuta(r"""
      (function () {
        const nomi = ["puntatore", "puntatore-di-ripiego"];
        for (const n of nomi) {
          const e = document.getElementById(n);
          if (e && getComputedStyle(e).display !== "none"
                && e.getBoundingClientRect().width > 0) return n;
        }
        return null;
      })()""")
    # ⛔ DUE COSE DISTINTE, e confonderle nasconderebbe la piu' importante:
    #   S1a  l'utente VEDE un puntatore mentre trascina        (invariante I8)
    #   S1b  e lo vede senza RIPIEGO, cioe' la cucitura regge  (la lezione F5)
    esiti.append({"caso": "S1a-il-puntatore-si-vede", "verde": bool(visibile),
                  "perche": "in disposizione a tocco il puntatore visibile e' «%s»"
                            % visibile})
    esiti.append({"caso": "S1b-cucitura-senza-ripiego",
                  "verde": bool(st.get("puntatore_cucito"))
                           and not st.get("puntatore_cucitura_rotta"),
                  "perche": ("`REMOTIX_PUNTATORE` c'e': %s; cucitura rotta: %s"
                             % (st.get("puntatore_cucito"),
                                st.get("puntatore_cucitura_rotta")))
                            + ("" if not st.get("puntatore_cucitura_rotta") else
                               "  ⛔ `muovi()` non accende `cl_noto`: in tocco il "
                               "puntatore condiviso resta invisibile — cura di UNA "
                               "riga nell'ancora F4-INPUT-CLASSICO (anello A7)")})
    esiti.append({"caso": "S2-cucitura-classico",
                  "verde": bool(st.get("classico_cucito")),
                  "perche": "`REMOTIX_CLASSICO` (ancora F4-INPUT-CLASSICO, anello A7): %s"
                            % st.get("classico_cucito")})

    # ── D4 · il contesto NON e' il sistema operativo ───────────────────────
    with open(os.path.join(RADICE, "src", "pagina.html"), encoding="utf-8") as f:
        testo = f.read()
    a = testo.split("ANCORA F4-TOCCO — INIZIO")[-1].split("ANCORA F4-TOCCO — FINE")[0]
    # ⛔ I commenti si tolgono PRIMA di cercare, e non e' una finezza: il primo
    #    giro di questo controllo era rosso su una riga di commento che diceva
    #    «qui non compare `navigator.userAgent`».  Un controllo che legge le
    #    proprie spiegazioni misura la prosa, non il codice.
    import re as _re
    codice = _re.sub(r"/\*.*?\*/", "", a, flags=_re.S)
    codice = _re.sub(r"^\s*//.*$", "", codice, flags=_re.M)
    colpevoli = [s for s in ("userAgent", "navigator.platform", "userAgentData")
                 if s in codice]
    esiti.append({"caso": "D4-il-contesto-non-e-il-sistema", "verde": not colpevoli,
                  "perche": ("nell'ancora F4-TOCCO non compare niente che venga dal "
                             "sistema operativo" if not colpevoli
                             else "⛔ compaiono: %s" % colpevoli)})

    try:
        urllib.request.urlopen(
            "http://127.0.0.1:%d/json/close/%s" % (diagnosi, scheda["id"]),
            timeout=5).read()
    except Exception:                          # noqa: BLE001
        pass
    note["guasti_della_scheda"] = list(c.guasti)
    return {"esiti": esiti, "note": note}


# ---------------------------------------------------------------------------
def stampa(esiti):
    guasti = [e for e in esiti if e.get("strumento")]
    misurati = [e for e in esiti if not e.get("strumento")]
    verdi = sum(1 for e in misurati if e["verde"])
    rossi = [e for e in misurati if not e["verde"]]
    for e in esiti:
        segno = "⚠ " if e.get("strumento") else ("✅" if e["verde"] else "⛔")
        print("  %s %-38s %s" % (segno, e["caso"], e["perche"]))
    print("\n  %d verdi su %d misurati" % (verdi, len(misurati)))
    if guasti:
        print("  ⚠ %d NON MISURATI per un guasto dello strumento: %s"
              % (len(guasti), [e["caso"] for e in guasti]))
        print("    (⛔ non sono verdi e non sono rossi: si rifa' il giro)")
    if rossi:
        return 1
    return 2 if guasti else 0


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--certifica", action="store_true")
    a.add_argument("--gira", action="store_true")
    a.add_argument("--verdetto")
    a.add_argument("--porta", type=int, default=7671)
    a.add_argument("--diagnosi", type=int, default=7672)
    a.add_argument("--esiti", default=os.path.join(QUI, "04-b28-esiti.jsonl"))
    a.add_argument("--registro", default=os.path.join(QUI, "04-b28-registro.jsonl"))
    o = a.parse_args()

    if o.certifica:
        return certifica()
    if o.verdetto:
        righe = [json.loads(r) for r in open(o.verdetto, encoding="utf-8") if r.strip()]
        return stampa(giudica(righe))
    if o.gira:
        codice, scena, esiti = gira(o.porta, o.diagnosi, o.esiti, o.registro)
        if codice:
            return codice
        with open(o.esiti, "a", encoding="utf-8") as f:
            f.write(json.dumps({"scena": scena, "esiti": esiti},
                               ensure_ascii=False) + "\n")
        return stampa(esiti)
    a.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
