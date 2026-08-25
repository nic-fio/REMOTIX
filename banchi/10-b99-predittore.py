#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
 10-b99 · IL PREDITTORE — *il budget si puo' calcolare PRIMA di dire di si'?*
═══════════════════════════════════════════════════════════════════════════════

⛔ **La domanda che questo banco deve chiudere** e' una sola, e non e' «quante
   sessioni ci stanno»: e'

       *«se aggiungo QUESTA sessione, la macchina regge?»*

   posta nel punto in cui il prodotto deve rispondere — `main.c:344`,
   **prima** di `figli_assicura()`, cioe' prima che il figlio nasca.

⭐ **Un budget e' esattamente questo: una funzione che risponde in anticipo.**
   Se la risposta non si puo' calcolare non c'e' nessun budget da scrivere: c'e'
   un conteggio, che e' quel che `DECISIONI.md` §4.6 ha deciso di **non** fare.

───────────────────────────────────────────────────────────────────────────────
 LA GRANDEZZA — e non e' quella che la fase cercava
───────────────────────────────────────────────────────────────────────────────

⛔⛔ Il primo giro ha smentito la premessa: **il collo non e' il codificatore.**
Col desktop vero dietro il motore video non passa il **27 %** mentre `rcs0` —
il motore di **rendering** — sta al **99,5 %** (§6.5), e la conversione di
colore gira **sulle EU** (§6.6).  ⇒ La grandezza da prevedere e' la
**composizione**, non i pixel di codifica.

⚠ **E il metro dell'occupazione non si puo' usare per un budget**:
`drm-engine-*` misura **tempo occupato, non lavoro fatto**, e il tempo dipende
dalla frequenza della GT — `[M]` fattore **3,8** fra 300 e 1550 MHz (§6.1
§CLOCK).  Un predittore tarato sull'occupazione letta a carico leggero
sbaglierebbe fino a **quattro volte**.

⭐⭐ **Da cui la scelta di questo banco: la moneta del budget e' il LAVORO
    CONSEGNATO, non il tempo occupato.**

        pixel al secondo composti-e-consegnati  =  Σ  fot/s × (larghezza × altezza)

    ⛔ E' una grandezza **indipendente dalla frequenza della GT**, percio' non
       ha il difetto del §CLOCK; ⭐ ed e' **esattamente quel che il padre ha gia'
       in mano**: ogni `MSG_FOTOGRAMMA` porta `larghezza`, `altezza` e
       `istante_us` (`figlio.c:2795`), e arriva in `deposita_fotogramma()`
       (`main.c:394`) per **ogni** fotogramma di **ogni** figlio.
       ⇒ Non serve nessun canale nuovo: serve **un accumulatore**.

    ⚠ Il prezzo, dichiarato: il lavoro consegnato **satura** quando la macchina
       e' in affanno — chi e' strozzato consegna meno di quel che chiede.  ⇒ La
       misura dice «sono pieno», **non** dice «sono pieno di quanto».  Per
       ammettere basta; per sapere quanto si sfora, no.

───────────────────────────────────────────────────────────────────────────────
 LA FUNZIONE
───────────────────────────────────────────────────────────────────────────────

    regge(dentro, nuovo)  ⟺   domanda(dentro) + domanda_peggiore(nuovo)  ≤  C

dove `C` e' la **capacita' della macchina**, misurata **a saturazione** una
volta (mai estrapolata da una retta, §6.1), e `domanda_peggiore(nuovo)` e' la
tela del nuovo per il **ritmo massimo** misurato su questo ferro.

⛔ **Due regole, non una, perche' i due errori non costano uguale**
(`LEZIONI.md` §1.33):

  «consegnato»  la domanda di chi e' dentro e' quel che **consegna adesso**.
                ⭐ E' quel che il padre misura davvero; `[M]` zero errori su
                tutt'e due i lati sui dati che ci sono.
                ⛔ **Cieca a chi e' fermo e si sveglia**: una sessione ferma
                costa GPU **zero** (§6.4-bis), entra nel conto per zero, e il
                giorno che si muove il budget e' gia' stato speso.

  «peggiore»    la domanda di chi e' dentro e' la sua **tela per il ritmo
                massimo**, come se stesse tutto il tempo a saturare.
                ⭐ Immune al risveglio; ⛔ `[M]` **un falso NO** sui dati che
                ci sono (rifiuta la sesta, che reggeva).

  «riserva F»   ⭐⭐ **la terza, ed e' quella che si propone**: la domanda di
                chi e' dentro e' il piu' grande fra quel che consegna e una
                **riserva** pari alla frazione `F` del suo caso peggiore.
                `[M]` a F = 0,5: **zero falsi NO e zero falsi SI'** sui dati
                che ci sono, tetto **sei** sature e **dieci** ferme — ⭐ che e'
                il numero promesso da `SPECIFICHE.md` §5.5 — e uno sforamento
                da risveglio limitato a **2×** invece che a 1640.
                ⚠ `F = 0` e' «consegnato», `F = 1` e' «peggiore»: e' la stessa
                regola con la manopola in mano al regista.

⛔⛔ **E prima dei pixel si guarda il RITARDO.**  Il conto sul consegnato, da
   solo, MENTE nel punto peggiore: `[M]` a otto sessioni il totale consegnato
   e' **26,6 Mpixel/s** contro i 480 di capacita' (§6.5) — direbbe *«c'e' posto
   per altre cinque»* mentre tutti stanno a 1,5 fot/s.  ⇒ Una sessione che
   consegna poco **con 600 ms di ritardo** e' strozzata, non ferma, e il
   predittore risponde **NON REGGE** senza nemmeno sommare.
   ⭐ E' `LEZIONI.md` §1.31/§1.34: il meccanismo accanto al sintomo, e qui il
   meccanismo e' il **ritardo**, non le chiavi (che restano a zero).

───────────────────────────────────────────────────────────────────────────────
 ⛔ I DUE ERRORI, E NON COSTANO UGUALE
───────────────────────────────────────────────────────────────────────────────

  **falso NO**   dice «non regge» e reggeva  ⇒ un utente rifiutato per niente.
                 Costa **un utente**.
  **falso SI'**  dice «regge» e non reggeva  ⇒ ⛔⛔ **affama tutti quelli che
                 stavano lavorando** — `[M]` la prima sessione da 39,60 a 0,96
                 fot/s (§6.5).  Viola l'invariante **I1**.  Costa **tutti**.

⇒ La soglia si mette **dal lato prudente**, e il margine si dichiara **da
  tutt'e due i lati**.

───────────────────────────────────────────────────────────────────────────────
 I PASSI
───────────────────────────────────────────────────────────────────────────────

    python3 banchi/10-b99-predittore.py --certifica        ⛔ per primo, sempre
    python3 banchi/10-b99-predittore.py taratura           il metro si tara PRIMA
    python3 banchi/10-b99-predittore.py raccogli           i dati che ci sono
    python3 banchi/10-b99-predittore.py indietro           verifica all'indietro
    python3 banchi/10-b99-predittore.py prevedi --dentro … --nuovo …
    python3 banchi/10-b99-predittore.py sigilla   --nome V1
    python3 banchi/10-b99-predittore.py avanti    --nome V1     (fa girare 10-b92)
    python3 banchi/10-b99-predittore.py confronta --nome V1

⛔ `sigilla` scrive l'**ancora** sulla macchina di prova PRIMA del giro, e
   `confronta` **si rifiuta di confrontare** se l'ancora non c'e', se l'impronta
   non torna, o se un file di misura e' **piu' vecchio** dell'ancora.
   ⇒ Una previsione scritta dopo la misura non e' difficile: e' **impossibile**.
"""

import argparse
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
import time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)

# ── L'isolamento di questo incarico (10-B10) ──────────────────────────────────
MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
PORTA = int(os.environ.get("PORTA", "8200"))
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/10b10")
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/10b10-src")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/10b10-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/10b10")
UNITA = os.environ.get("UNITA", "remotix-%d" % PORTA)
IO_SONO = os.environ.get("IO_SONO", "10-b10")
LUCCHETTO = os.environ.get("LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-gpu.d")

MISURE = os.path.join(QUI, "10-b99-misure.jsonl")
SIGILLI = os.path.join(QUI, "10-b99-sigilli.jsonl")

# ⛔ Le due etichette che rendono possibile dire «non so».  Una capacita' e' di
#    UN FERRO e di UNA CATENA: darle in pasto i numeri di un'altra scena non e'
#    un'estrapolazione ardita, e' una risposta senza senso.
FERRO = "i5-13500T · Intel UHD 730 · renderD128 (i915)"
CATENA_DESKTOP = "compositore+cattura+conversione+codificatore"
CATENA_NUDA = "codificatore-nudo"          # `10-b88`: nessun compositore dietro

# ── Colori ───────────────────────────────────────────────────────────────────
def _c(s, n):
    return "\033[%sm%s\033[0m" % (n, s) if sys.stdout.isatty() else s


def log(s):
    print("\n%s" % _c("== %s" % s, "1"))


def ok(s):
    print("    %s  %s" % (_c("OK", "1;32"), s))


def ko(s):
    print("    %s  %s" % (_c("NO", "1;31"), s))


def dub(s):
    print("    %s  %s" % (_c("??", "1;33"), s))


def inf(s):
    print("    --  %s" % s)


# ═════════════════════════════════════════════════════════════════════════════
# §1 · LE COSE — sessione, capacita', verdetto
# ═════════════════════════════════════════════════════════════════════════════

class Sessione(object):
    """Una sessione, come il server la vede.

    ⛔ `mpixel_s` e' `None` quando **non e' stata misurata**, e `None` NON e'
       zero: una sessione appena nata non ha ancora consegnato niente, e
       contarla zero e' esattamente l'errore che affama tutti.
    """

    def __init__(self, nome, tela_l=None, tela_a=None, mpixel_s=None,
                 catena=CATENA_DESKTOP, ferro=FERRO, ritardo_ms=None):
        self.nome = nome
        self.tela_l = tela_l
        self.tela_a = tela_a
        self.mpixel_s = mpixel_s          # ⛔ None = non misurato
        self.catena = catena
        self.ferro = ferro
        # ⭐⭐ IL MECCANISMO ACCANTO AL SINTOMO (`LEZIONI.md` §1.31, §1.34).
        #
        # ⛔ Il consegnato da solo MENTE quando la macchina e' gia' crollata:
        #    a otto sessioni il totale consegnato scende a 26,6 Mpixel/s
        #    (`[M]` §6.5) — cioe' il conto sui pixel direbbe *«c'e' un sacco di
        #    posto»* proprio nell'istante in cui non ce n'e' nessuno.
        # ⭐ La colonna che distingue **«ferma»** da **«strozzata»** — che
        #    consegnano tutt'e due poco — e' il RITARDO: `[M]` 10-15 ms fino a
        #    sei, 40 alla settima, 400-1200 dall'ottava (§6.5).
        # ⇒ E il padre ce l'ha gia': `istante_us` viaggia dentro ogni
        #   `MSG_FOTOGRAMMA` e lo timbra il FIGLIO all'istante della cattura
        #   (`main.c:405`), apposta perche' il ritardo non risulti piu' corto
        #   del vero.
        self.ritardo_ms = ritardo_ms

    def mpixel_tela(self):
        if self.tela_l is None or self.tela_a is None:
            return None
        return self.tela_l * self.tela_a / 1e6

    def __repr__(self):
        return "Sessione(%s %sx%s %s Mpx/s)" % (
            self.nome, self.tela_l, self.tela_a,
            "?" if self.mpixel_s is None else "%.1f" % self.mpixel_s)


class Capacita(object):
    """La capacita' della macchina, con addosso **come e' stata misurata**.

    ⛔ `scena`, `catena` e `ferro` non sono decorazioni: sono le tre cose che
       permettono al predittore di dire **«non so»** invece di dare un numero.
    """

    def __init__(self, mpixel_s, ritmo_max_fps, ferro, catena, scena,
                 misurata_da, margine_basso=None, margine_alto=None,
                 tele_provate=(), soffitto_visto=True,
                 ritardo_affanno_ms=25.0, tolleranza=0.01,
                 buffer_distinti=None, hz_compositore=60.0):
        self.mpixel_s = mpixel_s
        self.ritmo_max_fps = ritmo_max_fps
        # ⛔⛔ «LA SOLLECITAZIONE E' ARRIVATA?» (`LEZIONI.md` §1.30).
        #    Se la salita non ha mai visto la macchina CEDERE, il numero piu'
        #    alto che si e' letto non e' un soffitto: e' un **limite inferiore**,
        #    e sopra quel numero il predittore deve dire «non so», non «no».
        self.soffitto_visto = soffitto_visto
        # La soglia sopra la quale una sessione e' **strozzata** e non ferma.
        # `[M]` sano 9,7-14,8 ms fino a sei · 39-47 alla settima (§6.5)
        # ⇒ 25 ms sta a meta' strada, con 1,7× di margine sul sano.
        self.ritardo_affanno_ms = ritardo_affanno_ms
        # ⛔⭐ IL MARGINE, E DA QUALE LATO STA.
        #
        #   La capacita' e' il **culmine misurato**: lo stato che si e' visto
        #   reggere.  ⚠ Confrontarlo con `≤` nudo rifiuterebbe proprio quello
        #   stato appena l'aritmetica muove la terza cifra — un **falso NO** per
        #   arrotondamento.  ⇒ Si tollera l'1 %, che e' la ripetibilita'
        #   dichiarata del metro (`[M]` ±0,6 %, §6.1).
        #   ⛔ E l'1 % e' **diciassette volte piu' piccolo** del vuoto che c'e'
        #      fra il culmine e il primo punto che ha ceduto (+17 %): il
        #      margine sta tutto dal lato prudente.
        self.tolleranza = tolleranza
        # ⭐⭐ E LA SECONDA SOGLIA, quella che ha un'ARITMETICA invece che una
        #    misura: la pista di decollo del compositore (§1-bis).  ⛔ Si tiene
        #    accanto alla misurata e si prende la PIU' PRUDENTE delle due: una
        #    sola delle due sarebbe una fiducia mal riposta in un numero solo.
        self.buffer_distinti = buffer_distinti
        self.hz_compositore = hz_compositore
        self.ferro = ferro
        self.catena = catena
        self.scena = scena
        self.misurata_da = misurata_da
        # ⛔ I due bordi dell'intervallo in cui la capacita' vera sta di sicuro:
        #    `margine_basso` = la domanda piu' alta che si e' vista REGGERE,
        #    `margine_alto`  = la domanda piu' bassa che si e' vista CEDERE.
        self.margine_basso = margine_basso
        self.margine_alto = margine_alto
        # ⭐ Le tele su cui la capacita' e' stata **verificata**.  Fuori di
        #    queste il predittore estrapola, e lo dichiara.
        self.tele_provate = list(tele_provate)

    def pista_ms(self):
        return pista_buffer_ms(self.buffer_distinti, self.hz_compositore)

    def soglia_affanno(self):
        """⛔ La piu' PRUDENTE fra la soglia misurata e la pista aritmetica.

        Torna `(valore, chi)`; `(None, ...)` quando non ce n'e' nessuna delle
        due — e allora la porta del ritardo si spegne e si conta il caso
        peggiore, che e' il verso scomodo."""
        pista = self.pista_ms()
        m = self.ritardo_affanno_ms
        if m is None and pista is None:
            return None, "nessuna"
        if m is None:
            return pista, "pista dei buffer"
        if pista is None:
            return m, "misura"
        return (min(m, pista),
                "misura" if m <= pista else "pista dei buffer")

    def dizionario(self):
        return {"mpixel_s": self.mpixel_s, "ritmo_max_fps": self.ritmo_max_fps,
                "ferro": self.ferro, "catena": self.catena, "scena": self.scena,
                "misurata_da": self.misurata_da,
                "margine_basso": self.margine_basso,
                "margine_alto": self.margine_alto,
                "tele_provate": self.tele_provate,
                "soffitto_visto": self.soffitto_visto,
                "ritardo_affanno_ms": self.ritardo_affanno_ms,
                "buffer_distinti": self.buffer_distinti,
                "hz_compositore": self.hz_compositore,
                "pista_buffer_ms": self.pista_ms(),
                "soglia_in_vigore_ms": self.soglia_affanno()[0],
                "soglia_da": self.soglia_affanno()[1]}


# ═════════════════════════════════════════════════════════════════════════════
# §1-bis · ⭐⭐⭐ LA SOGLIA HA UN'ARITMETICA — e non e' una saturazione
# ═════════════════════════════════════════════════════════════════════════════
#
# ⛔ Il primo giro aveva chiamato il fenomeno «dirupo» e lo aveva descritto come
#    una saturazione.  ⭐ **Non lo e'**, e il meccanismo si legge nel codice:
#
#    `src/cattura.c:586` chiede al compositore **sei** buffer sulla strada della
#    scheda (`SPA_POD_CHOICE_RANGE_Int(6, 4, 8)` — un MINIMO chiesto, non un
#    ordine: quanti ne siano arrivati lo dice `buffer_distinti`, `cattura.h:198`,
#    ⭐ **che si conta, non si suppone**);
#    il prodotto ne **trattiene al massimo DUE** (`cattura.c:578` — «uno fermo
#    nel posto e uno in mano a chi legge»);
#    e a tenerli e' un'attesa **bloccante**: `vaSyncSurface`,
#    `codificatore.c:3334`, che il commento accanto chiama *«il rilascio»*.
#
# ⇒ Il compositore ha una **pista di decollo** lunga
#
#       (buffer_distinti − 2) × periodo del compositore
#
#   e finche' il nostro tempo di ritenuta ci sta dentro, non succede niente.
#   ⛔ Quando lo supera, il compositore resta senza buffer e **si ferma ad
#      aspettarci** — e non degrada in proporzione: **si pianta**.
#
# ⭐⭐⭐ E QUESTO CAMBIA LA FORMA DEL BUDGET.  Non e' *«la somma dei pixel supera
#   la capacita'»*: e' **una soglia su una grandezza per sessione**, e sono due
#   affermazioni diverse.  ⇒ Il predittore le tiene **tutt'e due**, e prende la
#   piu' prudente:
#
#     · il conto sui pixel     dice **quanta** roba ci sta;
#     · la pista dei buffer    dice **quando** il meccanismo scatta.
#
# `[M]` E i due numeri si incontrano: con 4 buffer effettivi la pista vale
#   **33,3 ms** a 60 Hz, e la soglia MISURATA sul ritardo (§5) vale **22,9 ms**
#   — cioe' la misura sta **sotto** l'aritmetica del 31 %, dal lato prudente.
#   ⚠ Con 6 buffer la pista sarebbe 66,7 ms, e allora sarebbe la MISURA a
#     mordere per prima.  ⇒ Si tengono tutt'e due e si prende il minimo.

def pista_buffer_ms(buffer_distinti, hz_compositore=60.0, trattenuti=2):
    """La pista di decollo del compositore, in millisecondi.

    ⛔ `None` se non si sa quanti buffer il produttore abbia dato davvero:
       `buffer_distinti` **si conta** (`cattura.h:198`), e supporre sei quando
       ne sono arrivati quattro raddoppierebbe la soglia — cioe' sbaglierebbe
       dal lato che affama tutti.
    """
    if buffer_distinti is None or hz_compositore in (None, 0):
        return None
    liberi = buffer_distinti - trattenuti
    if liberi <= 0:
        # ⛔ Non e' «zero millisecondi»: e' un prodotto che trattiene tutto
        #    quel che ha, e allora il compositore si ferma **sempre**.
        return 0.0
    return liberi * 1000.0 / hz_compositore


REGGE = "REGGE"
NON_REGGE = "NON REGGE"
NON_SO = "NON SO"


class Verdetto(object):
    def __init__(self, esito, perche, domanda=None, capacita=None,
                 avanzo=None, estrapola=False):
        self.esito = esito
        self.perche = perche
        self.domanda = domanda
        self.capacita = capacita
        self.avanzo = avanzo
        self.estrapola = estrapola

    def __repr__(self):
        return "%s — %s" % (self.esito, self.perche)

    def dizionario(self):
        return {"esito": self.esito, "perche": self.perche,
                "domanda_mpixel_s": self.domanda, "capacita_mpixel_s":
                self.capacita, "avanzo_mpixel_s": self.avanzo,
                "estrapola": self.estrapola}


# ═════════════════════════════════════════════════════════════════════════════
# §2 · ⭐⭐ LA FUNZIONE — la risposta in anticipo
# ═════════════════════════════════════════════════════════════════════════════

REGOLA_CONSEGNATO = "consegnato"
REGOLA_PEGGIORE = "peggiore"
# ⭐ LA TERZA, e nasce da un numero: `[M]` una sessione **ferma** consegna
#   0,05 Mpixel/s e una **satura** 82,0 — un fattore **1640**.  ⇒ Un budget
#   contato sul consegnato puo' essere sforato di 1640 volte da un risveglio, e
#   ⛔ la scala della fase 9 NON puo' rimediarlo: il regolatore vive nel padre e
#   ferma fotogrammi **gia' codificati** (§3.2).  ⇒ Si tiene una RISERVA per
#   sessione: una frazione del suo caso peggiore, che nessuno puo' spendere.
REGOLA_RISERVA = "riserva"
FRAZIONE_RISERVA = float(os.environ.get("FRAZIONE_RISERVA", "0.5"))


def domanda_peggiore(s, cap):
    """Il costo di una sessione **nel caso peggiore**: la sua tela al ritmo
    massimo che questo ferro ha mostrato di saper consegnare.

    ⛔ Torna `None` se la tela non si sa: «non ho potuto misurare» non e' zero.
    """
    mp = s.mpixel_tela()
    if mp is None:
        return None
    return mp * cap.ritmo_max_fps


def prevedi(dentro, nuovo, cap, regola=REGOLA_CONSEGNATO,
            frazione=FRAZIONE_RISERVA):
    """⭐⭐ **LA FUNZIONE**: date le sessioni gia' dentro e una che chiede di
    entrare, la macchina regge?

    `dentro`  elenco di `Sessione` — quelle che stanno gia' lavorando
    `nuovo`   la `Sessione` che chiede di entrare (⚠ il suo `mpixel_s` e'
              **sempre** ignorato: non ha ancora consegnato niente)
    `cap`     la `Capacita` misurata su questo ferro

    ⛔ Le QUATTRO porte, e tre delle quattro fanno dire «non so» invece di
       dare un numero:
       1. **ferro diverso**   — la capacita' e' di UNA macchina ⇒ non so;
       2. **catena diversa**  — i pixel del codificatore nudo (`10-b88`) non
          sono i pixel di un desktop composto: il collo e' un altro motore
          ⇒ non so;
       3. ⛔⛔ **gia' in affanno** — se qualcuno di dentro consegna con un
          ritardo sopra la soglia MISURATA, la macchina e' gia' oltre e
          ammettere viola I1 ⇒ **NON REGGE**, senza nemmeno sommare;
       4. **grandezza non misurata** — una sessione dentro senza ne' consegnato
          ne' tela e' un buco nel conto, e un buco non si riempie di zero
          ⇒ non so.

    ⚠ E una quinta, che non e' una porta ma una dichiarazione: se la taratura
      non ha mai visto la macchina **cedere**, sopra il suo numero il verdetto
      e' «non so», perche' quel numero e' un limite inferiore (§1.30).
    """
    if cap is None:
        return Verdetto(NON_SO, "⛔ non ho una capacita' misurata per questa "
                                "macchina: senza il numero del ferro non c'e' "
                                "budget, c'e' un conteggio")

    # ── porta 1 · il ferro ────────────────────────────────────────────────
    for s in list(dentro) + [nuovo]:
        if s.ferro != cap.ferro:
            return Verdetto(NON_SO,
                            "⛔ «%s» viene da un ferro diverso (%s) da quello "
                            "in cui la capacita' e' stata misurata (%s): non "
                            "so" % (s.nome, s.ferro, cap.ferro))

    # ── porta 2 · la catena, cioe' la SCENA ───────────────────────────────
    for s in list(dentro) + [nuovo]:
        if s.catena != cap.catena:
            return Verdetto(NON_SO,
                            "⛔ «%s» e' di un'altra scena: catena «%s» contro "
                            "«%s» della taratura.  ⛔ I pixel del codificatore "
                            "nudo e i pixel di un desktop composto NON sono la "
                            "stessa grandezza — a cedere e' un altro motore "
                            "(§6.5, §6.6): non so"
                            % (s.nome, s.catena, cap.catena))

    # ── porta 3 · ⛔⛔ LA MACCHINA E' GIA' IN AFFANNO? ─────────────────────
    #
    # ⛔ Il conto sui pixel consegnati, da solo, MENTE nel punto peggiore: `[M]`
    #    a otto sessioni il totale consegnato e' **26,6 Mpixel/s** contro i 480
    #    di capacita' (§6.5) — cioe' direbbe *«c'e' posto per altre cinque»*
    #    mentre tutti stanno a 1,5 fot/s.  ⇒ Prima dei pixel si guarda il
    #    RITARDO, che e' il meccanismo (§1.31, §1.34).
    soglia, da_chi = cap.soglia_affanno()
    strozzati = ([] if soglia is None else
                 [s for s in dentro
                  if s.ritardo_ms is not None and s.ritardo_ms > soglia])
    if strozzati:
        return Verdetto(NON_REGGE,
                        "⛔ la macchina e' GIA' in affanno: %d session%s "
                        "consegna%s con %.0f ms di ritardo (soglia %.1f ms, "
                        "dalla %s).  Ammettere adesso viola I1 su chi sta gia' "
                        "lavorando"
                        % (len(strozzati), "e" if len(strozzati) > 1 else "",
                           "no" if len(strozzati) > 1 else "",
                           max(s.ritardo_ms for s in strozzati), soglia,
                           da_chi))

    # ── porta 4 · le grandezze che mancano ────────────────────────────────
    domanda = 0.0
    ciechi = []
    for s in dentro:
        if regola == REGOLA_PEGGIORE:
            d = domanda_peggiore(s, cap)
            if d is None:
                return Verdetto(NON_SO,
                                "⛔ di «%s» non conosco la tela, e la regola "
                                "«peggiore» ci si regge sopra: non so" % s.nome)
        elif regola == REGOLA_RISERVA:
            # ⭐ Il piu' grande fra quel che consegna adesso e la sua riserva.
            pg = domanda_peggiore(s, cap)
            if pg is None:
                return Verdetto(NON_SO,
                                "⛔ di «%s» non conosco la tela, e la riserva "
                                "si calcola sulla tela: non so" % s.nome)
            d = s.mpixel_s
            if d is None or s.ritardo_ms is None or soglia is None:
                d = pg
            else:
                d = max(d, pg * frazione)
        else:
            d = s.mpixel_s
            if d is None or s.ritardo_ms is None or soglia is None:
                # ⚠ Ripiego dichiarato, e nel verso SCOMODO: senza il
                #   consegnato — o senza il ritardo, che e' quel che distingue
                #   «ferma» da «strozzata» — si conta il caso peggiore.
                if s.ritardo_ms is None and d is not None:
                    ciechi.append(s.nome)
                d = domanda_peggiore(s, cap)
                if d is None:
                    return Verdetto(NON_SO,
                                    "⛔ di «%s» non ho ne' il consegnato ne' la "
                                    "tela: e' un buco nel conto, e un buco NON "
                                    "si riempie di zero" % s.nome)
        domanda += d

    d_nuovo = domanda_peggiore(nuovo, cap)
    if d_nuovo is None:
        return Verdetto(NON_SO,
                        "⛔ di «%s» non conosco la tela: a `consegna_verdetto()` "
                        "la tela non e' ancora decisa (si decide a `SESSIONE`, "
                        "`rcp.c:2992`).  ⭐ Il tetto del decodificatore c'e' "
                        "gia' — `video.misura_massima`, `rcp.c:543` — ma va "
                        "portato fin qui, e se il client non l'ha dichiarata "
                        "vale 0 ⇒ non so" % nuovo.nome)
    domanda += d_nuovo

    # ── ⚠ estrapolo? ──────────────────────────────────────────────────────
    estrapola = False
    tele = set(cap.tele_provate)
    for s in list(dentro) + [nuovo]:
        if s.tela_l and s.tela_a and ("%dx%d" % (s.tela_l, s.tela_a)) not in tele:
            estrapola = True

    tetto = cap.mpixel_s * (1.0 + cap.tolleranza)
    avanzo = cap.mpixel_s - domanda
    if domanda <= tetto:
        v = Verdetto(REGGE,
                     "domanda %.1f ≤ capacita' %.1f Mpixel/s (+%.0f %% di "
                     "taratura ⇒ %.1f · avanzo %.1f)"
                     % (domanda, cap.mpixel_s, cap.tolleranza * 100, tetto,
                        avanzo),
                     domanda, cap.mpixel_s, avanzo, estrapola)
    elif not cap.soffitto_visto:
        # ⛔ §1.30: la salita di taratura non ha mai visto la macchina CEDERE
        #    ⇒ quel numero e' un limite INFERIORE, non un soffitto, e sopra di
        #    lui non si puo' dire di no piu' di quanto si possa dire di si'.
        v = Verdetto(NON_SO,
                     "⛔ domanda %.1f > %.1f Mpixel/s, ma la taratura NON ha "
                     "mai visto questa macchina cedere: quel numero e' un "
                     "limite inferiore, non un soffitto.  Non so"
                     % (domanda, cap.mpixel_s),
                     domanda, cap.mpixel_s, avanzo, estrapola)
    else:
        v = Verdetto(NON_REGGE,
                     "domanda %.1f > capacita' %.1f Mpixel/s (manca %.1f) ⇒ "
                     "BUDGET_PIENO" % (domanda, cap.mpixel_s, -avanzo),
                     domanda, cap.mpixel_s, avanzo, estrapola)
    if ciechi:
        v.perche += ("  ⚠ e di %s non ho il ritardo: contate al caso peggiore, "
                     "perche' senza ritardo «ferma» e «strozzata» sono "
                     "indistinguibili" % ", ".join(ciechi))
    if estrapola:
        v.perche += ("  ⚠ e la tela di qualcuno non e' fra quelle su cui la "
                     "capacita' e' stata VERIFICATA (%s): il numero e' "
                     "un'estrapolazione, non una misura"
                     % (", ".join(cap.tele_provate) or "nessuna"))
    return v


# ═════════════════════════════════════════════════════════════════════════════
# §3 · IL LETTORE DEI GIORNALI — e ⛔ **si tara prima**
# ═════════════════════════════════════════════════════════════════════════════
#
# I giornali di `10-b92` sono la traccia per-fotogramma di ogni sessione:
#     {"numero":…, "chiave":…, "l":1920, "a":1080, "byte":…,
#      "istante_us":…, "arrivo_ms":…}
# ⭐ E' **la stessa cosa** che il padre vede in `deposita_fotogramma()`
#   (`main.c:394`): tela, istante, byte, per fotogramma.  ⇒ Quel che questo
#   lettore ricava dai giornali, il prodotto lo puo' ricavare in corsa.


def leggi_giornale(percorso):
    """⛔ Torna `None` se non ha potuto leggere.  Una lista vuota e un file
       illeggibile sono due fatti diversi."""
    if not os.path.exists(percorso):
        return None
    v = []
    try:
        with open(percorso) as f:
            for riga in f:
                riga = riga.strip()
                if not riga:
                    continue
                try:
                    d = json.loads(riga)
                except ValueError:
                    continue
                if "arrivo_ms" not in d or "l" not in d or "a" not in d:
                    continue
                v.append(d)
    except (IOError, OSError):
        return None
    return v


def fetta(giornale, t0_ms, t1_ms):
    """Che cosa ha consegnato una sessione fra due istanti.

    ⛔ Torna `None` — non zero — se il giornale non c'e' o se la finestra e'
       vuota di tempo: «non ho misurato» ≠ «non ha consegnato niente».
    """
    if giornale is None:
        return None
    if t1_ms - t0_ms < 1000.0:
        return None
    v = [d for d in giornale if t0_ms <= d["arrivo_ms"] < t1_ms]
    dur = (t1_ms - t0_ms) / 1000.0
    if not v:
        # ⚠ Zero fotogrammi in una finestra vera E' un dato: la sessione c'e' e
        #   non consegna.  ⛔ Ma la tela non si sa, e senza tela non c'e'
        #   Mpixel/s: si dichiara.
        return {"fot_s": 0.0, "mpixel_s": 0.0, "tela": None, "quanti": 0,
                "secondi": dur, "ritardo_ms": None, "chiavi": 0,
                "mbit_s": 0.0}
    tela = "%dx%d" % (v[0]["l"], v[0]["a"])
    mp = v[0]["l"] * v[0]["a"] / 1e6
    rit = [d["arrivo_ms"] - d["istante_us"] / 1000.0
           for d in v if "istante_us" in d]
    return {"fot_s": len(v) / dur,
            "mpixel_s": len(v) / dur * mp,
            "tela": tela,
            "quanti": len(v),
            "secondi": dur,
            "ritardo_ms": statistics.median(rit) if rit else None,
            "chiavi": sum(1 for d in v if d.get("chiave")),
            "mbit_s": sum(d.get("byte", 0) for d in v) * 8.0 / 1e6 / dur}


def gradini_da_giornali(giornali, regime_s=15.0, fine_ms=None):
    """La salita, ricostruita **dai fotogrammi** e non dal riassunto di un
    altro banco.

    ⭐ Il confine di ogni gradino e' il primo fotogramma della sessione che si
      aggiunge: non serve nessun orologio esterno, e non c'e' nessun ponte fra
      due orologi da verificare.
    """
    vivi = sorted(giornali.keys())
    inizio = {}
    for i in vivi:
        g = giornali[i]
        if not g:
            return None
        inizio[i] = g[0]["arrivo_ms"]
    if fine_ms is None:
        fine_ms = max(giornali[i][-1]["arrivo_ms"] for i in vivi)
    ordine = sorted(vivi, key=lambda i: inizio[i])
    out = []
    for k, i in enumerate(ordine):
        t0 = inizio[i] + regime_s * 1000.0
        t1 = inizio[ordine[k + 1]] if k + 1 < len(ordine) else fine_ms
        if t1 - t0 < 8000.0:
            continue
        per = {}
        for j in ordine[:k + 1]:
            per[j] = fetta(giornali[j], t0, t1)
        buone = [p for p in per.values() if p]
        if len(buone) != k + 1:
            continue
        out.append({
            "gradino": k + 1,
            "finestra_s": (t1 - t0) / 1000.0,
            "per_sessione": per,
            "tot_fot_s": sum(p["fot_s"] for p in buone),
            "tot_mpixel_s": sum(p["mpixel_s"] for p in buone),
            "tot_mbit_s": sum(p["mbit_s"] for p in buone),
            "min_fot_s": min(p["fot_s"] for p in buone),
            "ritardo_ms": statistics.median(
                [p["ritardo_ms"] for p in buone if p["ritardo_ms"] is not None])
            if any(p["ritardo_ms"] is not None for p in buone) else None,
            "chiavi": sum(p["chiavi"] for p in buone),
            "tele": sorted(set(p["tela"] for p in buone if p["tela"])),
        })
    return out


def _giornale_finto(fps, secondi, l=1920, a=1080, primo_ms=0.0, ritardo_ms=10.0):
    """⛔ IL VALORE NOTO che serve a tarare il lettore (`LEZIONI.md` §1.33)."""
    v = []
    n = int(fps * secondi)
    for k in range(n):
        t = primo_ms + k * 1000.0 / fps
        v.append({"numero": k + 1, "chiave": False, "l": l, "a": a,
                  "byte": 5000, "istante_us": (t - ritardo_ms) * 1000.0,
                  "arrivo_ms": t})
    return v


def taratura(silenzioso=False):
    """⛔ **Il metro si tara PRIMA**: si inietta un ritmo NOTO e si verifica che
    il lettore lo ritrovi."""
    guai = []
    for fps, l, a in ((30.0, 1920, 1080), (12.0, 864, 480), (60.0, 3840, 2160)):
        g = _giornale_finto(fps, 40.0, l, a)
        f = fetta(g, 15000.0, 39000.0)
        if f is None:
            guai.append("il lettore non ha letto un giornale che c'e'")
            continue
        att_mp = fps * l * a / 1e6
        if abs(f["fot_s"] - fps) / fps > 0.02:
            guai.append("ritmo iniettato %.1f, letto %.2f" % (fps, f["fot_s"]))
        if abs(f["mpixel_s"] - att_mp) / att_mp > 0.02:
            guai.append("Mpixel/s attesi %.1f, letti %.2f"
                        % (att_mp, f["mpixel_s"]))
        if f["ritardo_ms"] is None or abs(f["ritardo_ms"] - 10.0) > 0.5:
            guai.append("ritardo iniettato 10 ms, letto %s" % f["ritardo_ms"])
        if not silenzioso and not guai:
            inf("%s @ %.0f fot/s → letti %.2f fot/s · %.1f Mpixel/s · "
                "ritardo %.1f ms"
                % ("%dx%d" % (l, a), fps, f["fot_s"], f["mpixel_s"],
                   f["ritardo_ms"]))
    # ⛔ E il controllo NEGATIVO: un lettore che dicesse sempre «va bene» non e'
    #    tarato.  Si inietta un ritmo sbagliato e si pretende che si veda.
    g = _giornale_finto(30.0, 40.0)
    f = fetta(g, 15000.0, 39000.0)
    if f and abs(f["fot_s"] - 20.0) / 20.0 <= 0.02:
        guai.append("⛔ il lettore accetta 30 come se fosse 20: non discrimina")
    return (not guai), guai


# ═════════════════════════════════════════════════════════════════════════════
# §4 · LA RACCOLTA — i dati che ci sono
# ═════════════════════════════════════════════════════════════════════════════

def _cita(s):
    """Una stringa dentro apici singoli, a prova di apice."""
    return "'" + s.replace("'", "'\\''") + "'"


def _ssh(cmd, secondi=120, radice=False):
    if radice:
        cmd = "printf '%%s\\n' %s | sudo -S -p '' %s" % (PAROLA_SUDO, cmd)
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, cmd],
                       capture_output=True, text=True, timeout=secondi)
    # ⚠ Nota di scena, non nostra: il profilo della macchina stampa
    #   «tput: No value for $TERM» su stderr a OGNI ssh.  Con `2>&1` finirebbe
    #   dentro i dati: qui stdout e stderr restano separati apposta.
    return p.returncode, p.stdout, p.stderr


def porta_giornali(remoto, dove):
    """Porta i giornali di un giro dalla macchina di prova a una cartella
    locale, e ⛔ **conserva le date**: il sigillo si regge su quelle."""
    os.makedirs(dove, exist_ok=True)
    rc, out, _ = _ssh("ls %s/giornale-*.jsonl 2>/dev/null | wc -l" % remoto)
    if rc != 0 or not out.strip().isdigit() or int(out.strip()) == 0:
        return None
    tar = os.path.join(dove, "giornali.tgz")
    p = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", MACCHINA,
         "printf '%s\\n' " + PAROLA_SUDO + " | sudo -S -p '' tar -C " + remoto +
         " -czf - $(cd " + remoto + " && ls giornale-*.jsonl) 2>/dev/null"],
        capture_output=True, timeout=600)
    if p.returncode != 0 or not p.stdout:
        return None
    with open(tar, "wb") as f:
        f.write(p.stdout)
    subprocess.run(["tar", "-C", dove, "-xzf", tar], check=False)
    return dove


def carica_giornali(cartella):
    g = {}
    if not os.path.isdir(cartella):
        return None
    for nome in os.listdir(cartella):
        m = re.match(r"^giornale-(\d+)\.jsonl$", nome)
        if not m:
            continue
        v = leggi_giornale(os.path.join(cartella, nome))
        if v is None or not v:
            continue
        g[int(m.group(1))] = v
    return g or None


def raccogli(cartella_b92, uscita=MISURE, etichetta="10-b92 · salita a undici",
             scena="satura", catena=CATENA_DESKTOP, aggiungi=False):
    """Costruisce il registro delle misure dai giornali di un giro.

    ⭐ Ogni punto porta addosso **la scena**: e' quel che permette al
      predittore di rifiutare i dati di un'altra scena invece di darci un
      numero sopra.
    """
    g = carica_giornali(cartella_b92)
    if g is None:
        ko("⛔ nessun giornale in %s: NON scrivo un registro vuoto"
           % cartella_b92)
        return None
    gr = gradini_da_giornali(g)
    if not gr:
        ko("⛔ i giornali ci sono ma non se ne ricava nessun gradino")
        return None
    punti = []
    # ⛔ «Ha CEDUTO?» e' un fatto della misura, non una deduzione di chi legge
    #    dopo: si scrive nel punto.  Il metro e' l'invariante **I1** — la
    #    sessione peggiore contro il ritmo pieno del primo gradino.
    ritmo_pieno = gr[0]["tot_fot_s"] / max(1, gr[0]["gradino"])
    for v in gr:
        punti.append({
            "ceduto": bool(v["min_fot_s"] < ritmo_pieno * 0.90),
            "sorgente": etichetta, "scena": scena, "catena": catena,
            "ferro": FERRO,
            "gradino": v["gradino"], "finestra_s": round(v["finestra_s"], 1),
            "tele": v["tele"],
            "tot_mpixel_s": round(v["tot_mpixel_s"], 2),
            "tot_fot_s": round(v["tot_fot_s"], 2),
            "tot_mbit_s": round(v["tot_mbit_s"], 3),
            "min_fot_s": round(v["min_fot_s"], 2),
            "ritardo_ms": None if v["ritardo_ms"] is None
            else round(v["ritardo_ms"], 1),
            "chiavi": v["chiavi"],
            "per_sessione_fot_s": {str(k): round(p["fot_s"], 2)
                                   for k, p in sorted(v["per_sessione"].items())},
            # ⭐ il MECCANISMO, per sessione: senza questo «ferma» e
            #   «strozzata» sono la stessa riga
            "per_sessione_ritardo_ms": {
                str(k): (None if p["ritardo_ms"] is None
                         else round(p["ritardo_ms"], 1))
                for k, p in sorted(v["per_sessione"].items())},
        })
    modo = "a" if aggiungi else "w"
    with open(uscita, modo) as f:
        for p in punti:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    ok("%d gradini scritti in %s" % (len(punti), uscita))
    return punti


def raccogli_b88(uscita=MISURE, esiti=None):
    """⭐ I punti del **codificatore nudo** (`10-b88`), che servono a UNA cosa
    sola: far vedere che il predittore li **rifiuta**.

    ⛔ Sono veri, sono misurati, e sono di **un'altra catena**: `testsrc2` senza
       nessun compositore dietro.  Il soffitto che descrivono e' quello dei due
       VDBOX (1,86 Gpixel/s) — quattro volte quello della macchina col desktop
       vero, perche' a cedere e' un altro motore.  ⇒ Un predittore che ci
       tarasse sopra un budget direbbe *«ne stanno ventiquattro»*.
    """
    esiti = esiti or os.path.join(QUI, "10-b88-esiti.jsonl")
    if not os.path.exists(esiti):
        return None
    punti = []
    with open(esiti) as f:
        for riga in f:
            riga = riga.strip()
            if not riga:
                continue
            d = json.loads(riga)
            s = d.get("sintomo") or {}
            if d.get("invalido") or s.get("mpixel_s_totali") is None:
                continue
            if d.get("strada") != "scheda" or d.get("codec") != "h264":
                continue
            punti.append({
                # ⛔ Qui «ceduto» lo dice il banco stesso: `verde` falso con una
                #    causa attribuita.  ⚠ Non si ri-deduce dai fot/s: 10-b88 ha
                #    gia' guardato i motori.
                "ceduto": bool(not d.get("verde") and d.get("causa")),
                "sorgente": "10-b88 · saturatore, codificatore NUDO",
                "scena": "codificatore-nudo", "catena": CATENA_NUDA,
                "ferro": FERRO,
                "gradino": d.get("n"), "finestra_s": d.get("secondi"),
                "tele": [d.get("misura")],
                "tot_mpixel_s": s.get("mpixel_s_totali"),
                "tot_fot_s": round((s.get("fps_effettivi_medio") or 0)
                                   * (d.get("n") or 0), 2),
                "tot_mbit_s": s.get("mbit_s_totali"),
                "min_fot_s": s.get("fps_effettivi_minimo"),
                "ritardo_ms": s.get("ritardo_ms_mediano"),
                "chiavi": None,
                "per_sessione_fot_s": {},
                "per_sessione_ritardo_ms": {},
            })
    with open(uscita, "a") as f:
        for p in punti:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    ok("%d punti del codificatore nudo aggiunti (scena «codificatore-nudo»)"
       % len(punti))
    return punti


def carica_misure(percorso=MISURE, scena=None):
    if not os.path.exists(percorso):
        return None
    v = []
    with open(percorso) as f:
        for riga in f:
            riga = riga.strip()
            if not riga:
                continue
            d = json.loads(riga)
            if scena is None or d.get("scena") == scena:
                v.append(d)
    return v or None


# ═════════════════════════════════════════════════════════════════════════════
# §5 · LA TARATURA DEL PREDITTORE — la capacita', misurata a SATURAZIONE
# ═════════════════════════════════════════════════════════════════════════════

def tara_capacita(punti, ritmo_max_fps=None, buffer_distinti=None,
                  hz_compositore=60.0):
    """⛔ **La capacita' si misura a saturazione, non si tira su una retta**
       (§6.1 §CLOCK).

    Il numero e' il **massimo lavoro consegnato** che la macchina ha mostrato:
    oltre quel punto il totale non sale — **scende**, ed e' il dirupo.

    ⭐ E i due bordi si portano dietro:
       `margine_basso` = la domanda piu' alta che si e' vista reggere;
       `margine_alto`  = la domanda piu' bassa che si e' vista cedere.
       ⇒ La capacita' vera sta li' in mezzo, e il predittore si mette **in
         fondo**, dal lato prudente.
    """
    if not punti:
        return None
    tot = [p["tot_mpixel_s"] for p in punti]
    culmine = max(range(len(tot)), key=lambda k: tot[k])
    cap = tot[culmine]
    # Il ritmo massimo per sessione: quel che una sessione **da sola** ha
    # consegnato.  ⛔ Se il primo gradino non c'e', non si inventa.
    if ritmo_max_fps is None:
        primo = [p for p in punti if p["gradino"] == 1]
        if not primo:
            return None
        ritmo_max_fps = primo[0]["tot_fot_s"]
    ceduti = [p for p in punti if p["gradino"] > punti[culmine]["gradino"]]
    margine_alto = None
    if ceduti:
        # La domanda del primo gradino che ha ceduto: sessioni × domanda unitaria
        d1 = punti[0]["tot_mpixel_s"] / max(1, punti[0]["gradino"])
        margine_alto = ceduti[0]["gradino"] * d1
    # ⛔⛔ «QUANTA SOLLECITAZIONE E' ARRIVATA» (`LEZIONI.md` §1.30): se il
    #    culmine e' l'ULTIMO gradino, la macchina non ha mai ceduto e il numero
    #    letto **non e' un soffitto**.  ⚠ Un banco che lo chiamasse capacita'
    #    darebbe un tetto che e' solo il punto in cui si e' smesso di provare.
    soffitto_visto = bool(ceduti) or bool(punti[culmine].get("ceduto"))
    # ⭐⭐ LA SOGLIA DEL RITARDO SI **MISURA**, non si sceglie.
    #
    # ⛔ Un numero scelto a mano sarebbe una taratura non tarata.  Qui si
    #    guarda dove stanno i due gruppi: il ritardo peggiore fra i gradini che
    #    hanno retto, e quello migliore fra quelli che hanno ceduto.  Se i due
    #    gruppi NON si toccano, la soglia e' la loro media geometrica; ⚠ se si
    #    toccano, la soglia **non esiste** e la porta del ritardo si spegne,
    #    dichiarandolo — perche' una soglia dentro la sovrapposizione
    #    sbaglierebbe da tutt'e due i lati.
    r_sani = [p["ritardo_ms"] for p in punti
              if p.get("ritardo_ms") is not None and not p.get("ceduto")]
    r_rotti = [p["ritardo_ms"] for p in punti
               if p.get("ritardo_ms") is not None and p.get("ceduto")]
    soglia = None
    if r_sani and r_rotti and max(r_sani) < min(r_rotti):
        soglia = (max(r_sani) * min(r_rotti)) ** 0.5
    tele = sorted(set(t for p in punti for t in p.get("tele", [])))
    return Capacita(
        mpixel_s=round(cap, 1), ritmo_max_fps=round(ritmo_max_fps, 2),
        ferro=FERRO, catena=punti[0].get("catena", CATENA_DESKTOP),
        scena=punti[0].get("scena", "?"),
        misurata_da="%s · culmine al gradino %d%s"
                    % (punti[0].get("sorgente", "?"), punti[culmine]["gradino"],
                       "" if soffitto_visto
                       else " ⛔ SENZA MAI CEDERE: limite inferiore"),
        margine_basso=round(cap, 1),
        margine_alto=None if margine_alto is None else round(margine_alto, 1),
        tele_provate=tele, soffitto_visto=soffitto_visto,
        ritardo_affanno_ms=soglia,
        buffer_distinti=buffer_distinti, hz_compositore=hz_compositore)


# ═════════════════════════════════════════════════════════════════════════════
# §5-bis · ⭐⭐ QUALE MONETA — il PIXEL o il FOTOGRAMMA?
# ═════════════════════════════════════════════════════════════════════════════
#
# ⛔ E' la domanda che decide se il budget si puo' scrivere in Mpixel/s.  A una
#    tela sola le due monete sono **indistinguibili**: si separano solo
#    confrontando il punto di cedimento a tele DIVERSE.
#
#      moneta = PIXEL       ⇒ al cedimento i **Mpixel/s** coincidono
#      moneta = FOTOGRAMMA  ⇒ al cedimento i **fot/s** coincidono
#
# ⭐ E la risposta si legge da sola: **quella delle due colonne che resta
#   costante al variare della tela**.

def moneta(punti, silenzioso=False):
    """Torna `("pixel"|"fotogramma"|None, dettaglio)`.

    ⛔ `None` quando le tele provate sono meno di due, o quando nessuna di esse
       ha visto la macchina cedere: senza due punti di cedimento a tele diverse
       la domanda **non ha risposta**, e inventarne una sarebbe peggio.
    """
    per = {}
    for p in punti:
        tele = p.get("tele") or []
        if len(tele) != 1:
            continue
        per.setdefault(tele[0], []).append(p)
    culmini = {}
    for tela, v in per.items():
        top = max(v, key=lambda x: x["tot_mpixel_s"])
        # ⛔ «La sollecitazione e' ARRIVATA?» (§1.30).  Una tela vale come
        #    punto di cedimento solo se **si e' visto cedere**: o il culmine
        #    stesso e' un cedimento dichiarato, o dopo il culmine c'e' un punto
        #    che consegna MENO.  ⚠ Altrimenti quel numero e' solo il punto in
        #    cui il banco ha smesso di provare.
        oltre = [x for x in v if x["gradino"] > top["gradino"]
                 and x["tot_mpixel_s"] < top["tot_mpixel_s"]]
        if not (top.get("ceduto") or oltre):
            continue
        culmini[tela] = top
    if len(culmini) < 2:
        d = ("⛔ tele con un cedimento vero: %d (%s).  Servono almeno DUE: "
             "a una tela sola le due monete danno lo stesso numero"
             % (len(culmini), ", ".join(sorted(culmini)) or "nessuna"))
        if not silenzioso:
            dub(d)
        return None, d
    mp = [c["tot_mpixel_s"] for c in culmini.values()]
    ft = [c["tot_fot_s"] for c in culmini.values()]
    sp_mp = (max(mp) - min(mp)) / max(mp)
    sp_ft = (max(ft) - min(ft)) / max(ft)
    quale = "pixel" if sp_mp < sp_ft else "fotogramma"
    d = ("Mpixel/s al cedimento: %s (scarto %.1f %%) · fot/s: %s (scarto "
         "%.1f %%) ⇒ la moneta e' il **%s**"
         % (" / ".join("%.0f" % x for x in mp), sp_mp * 100,
            " / ".join("%.0f" % x for x in ft), sp_ft * 100, quale))
    if not silenzioso:
        for tela, c in sorted(culmini.items()):
            inf("%-11s culmine a N=%d%s · %.1f Mpixel/s · %.1f fot/s"
                % (tela, c["gradino"],
                   " (e li' CEDE)" if c.get("ceduto") else " (cede al dopo)",
                   c["tot_mpixel_s"], c["tot_fot_s"]))
        ok(d)
        # ⭐⭐ E CON DUE PUNTI SI LEGGE ANCHE IL TERMINE FISSO PER FOTOGRAMMA.
        #
        #   costo = a + b · Mpixel  ⇒  f₁(a + b·px₁) = f₂(a + b·px₂)
        #   ⇒ a/b = (f₂·px₂ − f₁·px₁) / (f₁ − f₂), in **Mpixel equivalenti**.
        #
        # ⛔ Serve a smascherare una trappola: `us_codifica` per fotogramma e'
        #    un **RITARDO**, non un **COSTO**, e la sua curva ha un termine
        #    fisso molto piu' grande.  Chi ci tarasse sopra un budget
        #    sbaglierebbe le tele piccole per eccesso.
        v = sorted(culmini.values(), key=lambda c: c["tot_fot_s"])
        (f2, p2), (f1, p1) = ((v[0]["tot_fot_s"], v[0]["tot_mpixel_s"] /
                               max(v[0]["tot_fot_s"], 1e-9)),
                              (v[-1]["tot_fot_s"], v[-1]["tot_mpixel_s"] /
                               max(v[-1]["tot_fot_s"], 1e-9)))
        if abs(f1 - f2) > 1e-6:
            a_su_b = (f2 * p2 - f1 * p1) / (f1 - f2)
            if a_su_b > 0:
                lato = (a_su_b * 1e6) ** 0.5
                inf("⭐ il termine FISSO per fotogramma vale %.4f Mpixel — un "
                    "quadrato di %.0f×%.0f: trascurabile" % (a_su_b, lato, lato))
            else:
                inf("⚠ il termine fisso per fotogramma esce NEGATIVO (%.4f "
                    "Mpixel): entro il rumore, cioe' indistinguibile da zero"
                    % a_su_b)
    return quale, d


# ═════════════════════════════════════════════════════════════════════════════
# §6 · ⭐ LA VERIFICA ALL'INDIETRO — sui dati che ci sono
# ═════════════════════════════════════════════════════════════════════════════
#
# ⛔ **E questo da solo NON basta**: una funzione tarata sugli stessi dati che
#    deve prevedere e' un ricalco.  Sta qui perche' un predittore che sbaglia
#    all'indietro e' morto prima di cominciare — non perche' passarlo dimostri
#    qualcosa.

def _regge_davvero(punto, ritmo_pieno, tolleranza=0.10):
    """⭐ Che cosa vuol dire «ha retto», **misurato e non deciso a occhio**.

    ⛔ Non e' «il totale e' alto»: e' **l'invariante I1** — nessuno di quelli
       che stavano lavorando ha perso piu' della tolleranza.
    """
    if punto.get("min_fot_s") is None:
        return None
    return punto["min_fot_s"] >= ritmo_pieno * (1.0 - tolleranza)


def indietro(punti, regola=REGOLA_CONSEGNATO, cap=None, silenzioso=False,
             tolleranza=0.10, frazione=FRAZIONE_RISERVA):
    """Rigioca la salita gradino per gradino: **prima** si prevede, **poi** si
    guarda il gradino dopo."""
    if not punti:
        return None
    if cap is None:
        cap = tara_capacita(punti)
    if cap is None:
        return None
    ritmo_pieno = punti[0]["tot_fot_s"] / max(1, punti[0]["gradino"])
    esiti = []
    for k in range(len(punti) - 1):
        qui, dopo = punti[k], punti[k + 1]
        tele = qui.get("tele") or []
        l, a = (int(x) for x in tele[0].split("x")) if tele else (None, None)
        dentro = []
        per = qui.get("per_sessione_fot_s", {})
        rit = qui.get("per_sessione_ritardo_ms", {})
        mp_tela = (l * a / 1e6) if l else None
        for nome, fps in sorted(per.items()):
            dentro.append(Sessione("s%s" % nome, l, a,
                                   None if mp_tela is None else fps * mp_tela,
                                   catena=qui.get("catena", CATENA_DESKTOP),
                                   ritardo_ms=rit.get(nome)))
        tele_d = dopo.get("tele") or tele
        ln, an = (int(x) for x in tele_d[0].split("x")) if tele_d else (None, None)
        nuovo = Sessione("s%d" % dopo["gradino"], ln, an,
                         catena=dopo.get("catena", CATENA_DESKTOP))
        v = prevedi(dentro, nuovo, cap, regola, frazione)
        vero = _regge_davvero(dopo, ritmo_pieno, tolleranza)
        esiti.append({"da": qui["gradino"], "a": dopo["gradino"],
                      "previsto": v.esito, "vero": vero,
                      "domanda": v.domanda, "min_fot_s": dopo.get("min_fot_s"),
                      "perche": v.perche})
    falsi_no = [e for e in esiti if e["previsto"] == NON_REGGE and e["vero"] is True]
    falsi_si = [e for e in esiti if e["previsto"] == REGGE and e["vero"] is False]
    non_so = [e for e in esiti if e["previsto"] == NON_SO]
    if not silenzioso:
        inf("capacita' tarata: %.1f Mpixel/s · ritmo pieno %.2f fot/s · "
            "tele provate %s" % (cap.mpixel_s, ritmo_pieno,
                                 ", ".join(cap.tele_provate)))
        print("      gradino   previsto      vero      min fot/s   domanda")
        for e in esiti:
            v = {True: "regge", False: "NON regge", None: "?"}[e["vero"]]
            segno = "  "
            if e in falsi_no:
                segno = _c("⛔", "1;31")
            elif e in falsi_si:
                segno = _c("⛔⛔", "1;31")
            print("      %2d → %-2d  %-11s %-11s %8s   %s"
                  % (e["da"], e["a"], e["previsto"], v,
                     "?" if e["min_fot_s"] is None else "%.2f" % e["min_fot_s"],
                     ("%.1f" % e["domanda"]) if e["domanda"] else "-") + " " + segno)
    return {"esiti": esiti, "falsi_no": len(falsi_no), "falsi_si": len(falsi_si),
            "non_so": len(non_so), "capacita": cap}


def ritmo_pieno_di(punti):
    """Il ritmo di UNA sessione quando e' sola: il metro di tutto il resto."""
    if not punti:
        return None
    return punti[0]["tot_fot_s"] / max(1, punti[0]["gradino"])


def convalida(punti, silenzioso=False):
    """⛔⛔ **LA PROVA CHE LA VERIFICA ALL'INDIETRO NON E' UN RICALCO.**

    Si tara la capacita' sui **primi k gradini soltanto** e si predicono gli
    altri, per ogni k.  ⭐ E il risultato e' un fatto di prodotto, non una
    curiosita': dice **da quale gradino in poi** la taratura sa gia' dove sta
    il tetto — cioe' **quanta saturazione serve** perche' il numero del budget
    esista.
    """
    fuori = []
    if not punti:
        return None
    ritmo_pieno = punti[0]["tot_fot_s"] / max(1, punti[0]["gradino"])
    for k in range(2, len(punti)):
        cap = tara_capacita(punti[:k])
        if cap is None:
            continue
        r = indietro(punti, REGOLA_CONSEGNATO, cap, silenzioso=True)
        # ⛔ Gli errori si contano SOLO sui gradini che NON hanno tarato.
        vis = [e for e in r["esiti"] if e["a"] > k]
        fno = sum(1 for e in vis if e["previsto"] == NON_REGGE
                  and e["vero"] is True)
        fsi = sum(1 for e in vis if e["previsto"] == REGGE
                  and e["vero"] is False)
        nso = sum(1 for e in vis if e["previsto"] == NON_SO)
        fuori.append({"tarato_su": k, "capacita": cap.mpixel_s,
                      "soffitto_visto": cap.soffitto_visto,
                      "giudicati": len(vis), "falsi_no": fno, "falsi_si": fsi,
                      "non_so": nso})
        if not silenzioso:
            riga = ("      tarato sui primi %2d gradini → capacita' %6.1f %s "
                    "· giudicati %2d · falsi NO %d · falsi SI' %d · non so %d"
                    % (k, cap.mpixel_s,
                       "  " if cap.soffitto_visto else "⛔",
                       len(vis), fno, fsi, nso))
            print(riga + ("   %s" % _c("⛔", "1;31") if fsi else ""))
    return fuori


# ═════════════════════════════════════════════════════════════════════════════
# §7 · ⛔⛔ IL SIGILLO — perche' una previsione scritta dopo sia IMPOSSIBILE
# ═════════════════════════════════════════════════════════════════════════════
#
# ⭐ Il meccanismo ha tre gambe, e servono tutte e tre:
#    a. l'**impronta** (sha256) delle previsioni, calcolata quando si sigilla;
#    b. l'**ancora**: un file scritto **sulla macchina di prova** PRIMA del
#       giro, che porta l'impronta e la data;
#    c. il **confronto delle date**: ogni file di misura dev'essere **piu'
#       giovane** dell'ancora.
#
# ⛔ `confronta` si rifiuta di giudicare se manca una qualunque delle tre.
#
# ⚠ E QUEL CHE IL SIGILLO **NON** GARANTISCE, dichiarato invece che sottinteso:
#   chi ha `root` sulla macchina di prova puo' `touch -d` l'ancora e mettersi
#   una data di comodo.  ⇒ Il sigillo non e' una difesa contro un avversario:
#   e' una difesa contro **se stessi**, cioe' contro la tentazione di
#   aggiustare una previsione dopo aver visto il numero.  Per quello basta e
#   avanza, ed e' il rischio vero (`LEZIONI.md` §1.33 e' nata cosi').

def _impronta(previsioni):
    s = json.dumps(previsioni, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class Ancore(object):
    """Dove vive l'ancora.  ⭐ Sulla macchina di prova nel giro vero; in una
    cartella locale sotto `--certifica`, che non deve toccare la macchina."""

    def __init__(self, locale=None):
        self.locale = locale

    def scrivi(self, nome, impronta):
        corpo = "%s\n%s\n%d\n" % (nome, impronta, int(time.time()))
        if self.locale:
            os.makedirs(self.locale, exist_ok=True)
            p = os.path.join(self.locale, "sigillo-%s.txt" % nome)
            with open(p, "w") as f:
                f.write(corpo)
            return p
        p = "%s/sigillo-%s.txt" % (LAV, nome)
        # ⛔ Un solo `sudo`, e la catena DENTRO la sua shell: una ridirezione in
        #    coda girerebbe come `nicfio` su una cartella di root — e il
        #    messaggio sarebbe «Permission denied» su un `mkdir` riuscito.
        dentro = "mkdir -p %s && printf '%%s\\n' '%s' '%s' '%d' > %s" % (
            LAV, nome, impronta, int(time.time()), p)
        rc, _, err = _ssh("bash -c %s" % _cita(dentro), radice=True)
        if rc != 0:
            inf(err.strip()[-200:])
            return None
        return p

    def leggi(self, nome):
        """Torna `(impronta, quando_epoch)` oppure `None`.  ⛔ `None` vuol dire
        «l'ancora non c'e'», e allora non si confronta."""
        if self.locale:
            p = os.path.join(self.locale, "sigillo-%s.txt" % nome)
            if not os.path.exists(p):
                return None
            righe = open(p).read().split("\n")
            return righe[1].strip(), os.path.getmtime(p)
        p = "%s/sigillo-%s.txt" % (LAV, nome)
        rc, out, _ = _ssh("bash -c %s" % _cita(
            "cat %s 2>/dev/null; echo ---; stat -c %%Y %s 2>/dev/null"
            % (p, p)), radice=True)
        if rc != 0 or "---" not in out:
            return None
        testa, coda = out.split("---", 1)
        righe = [r for r in testa.split("\n") if r.strip()]
        if len(righe) < 2 or not coda.strip().isdigit():
            return None
        return righe[1].strip(), float(coda.strip())


def sigilla(nome, previsioni, ancore=None, file_sigilli=SIGILLI):
    """Scrive le previsioni e le ancora.  ⛔ **Prima del giro, sempre.**"""
    ancore = ancore or Ancore()
    imp = _impronta(previsioni)
    dove = ancore.scrivi(nome, imp)
    if dove is None:
        ko("⛔ l'ancora NON e' stata scritta: senza ancora non sigillo, e senza "
           "sigillo il giro non vale")
        return None
    voce = {"nome": nome, "impronta": imp, "previsioni": previsioni,
            "quando_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "ancora": dove}
    with open(file_sigilli, "a") as f:
        f.write(json.dumps(voce, ensure_ascii=False) + "\n")
    ok("sigillo «%s» · impronta %s… · ancora in %s" % (nome, imp[:16], dove))
    return voce


def leggi_sigillo(nome, file_sigilli=SIGILLI):
    if not os.path.exists(file_sigilli):
        return None
    voce = None
    with open(file_sigilli) as f:
        for riga in f:
            riga = riga.strip()
            if not riga:
                continue
            d = json.loads(riga)
            if d.get("nome") == nome:
                voce = d
    return voce


def confronta(nome, file_misura, ancore=None, file_sigilli=SIGILLI,
              silenzioso=False):
    """⛔ **Le tre porte**, e se una sola e' chiusa non si confronta.

    Torna `None` quando **non ha potuto giudicare** — che non e' «le previsioni
    erano sbagliate».
    """
    ancore = ancore or Ancore()
    voce = leggi_sigillo(nome, file_sigilli)
    if voce is None:
        ko("⛔ NON CONFRONTO: non c'e' nessun sigillo «%s»" % nome)
        return None
    a = ancore.leggi(nome)
    if a is None:
        ko("⛔ NON CONFRONTO: l'ancora di «%s» non c'e'.  Una previsione senza "
           "ancora e' una previsione scritta dopo, finche' non si dimostra il "
           "contrario" % nome)
        return None
    imp_ancora, quando = a
    imp_ora = _impronta(voce["previsioni"])
    if imp_ora != voce["impronta"]:
        ko("⛔ NON CONFRONTO: le previsioni sono state CAMBIATE dopo il "
           "sigillo (impronta %s… contro %s…)" % (imp_ora[:16],
                                                  voce["impronta"][:16]))
        return None
    if imp_ancora != voce["impronta"]:
        ko("⛔ NON CONFRONTO: l'ancora porta un'altra impronta (%s… contro "
           "%s…)" % (imp_ancora[:16], voce["impronta"][:16]))
        return None
    for f in file_misura:
        if not os.path.exists(f):
            ko("⛔ NON CONFRONTO: la misura «%s» non c'e'" % f)
            return None
        if os.path.getmtime(f) <= quando:
            ko("⛔ NON CONFRONTO: «%s» e' PIU' VECCHIO dell'ancora (%s contro "
               "%s): quella misura c'era gia' quando ho scritto la previsione"
               % (os.path.basename(f),
                  time.strftime("%H:%M:%S", time.gmtime(os.path.getmtime(f))),
                  time.strftime("%H:%M:%S", time.gmtime(quando))))
            return None
    if not silenzioso:
        ok("il sigillo regge: impronta %s…, ancora del %s, %d file di misura "
           "tutti piu' giovani" % (voce["impronta"][:16],
                                   time.strftime("%H:%M:%SZ", time.gmtime(quando)),
                                   len(file_misura)))
    return voce


# ═════════════════════════════════════════════════════════════════════════════
# §8 · LA VERIFICA IN AVANTI — si fa girare `10-b92`, non lo si riscrive
# ═════════════════════════════════════════════════════════════════════════════

def gira_b92(tela, quanti, durata, scena="satura", giornali_in=None):
    """⭐ `10-b92` fa gia' la salita con **ogni** sessione misurata a **ogni**
    gradino: qui si chiama, non si riscrive.  ⛔ E prende il lucchetto da se'.
    """
    amb = dict(os.environ)
    amb.update({"PORTA": str(PORTA), "LAV": LAV, "ALBERO": ALB,
                "DENTRO_ALB": DENTRO_ALB, "DENTRO_LAV": DENTRO_LAV,
                "UNITA": UNITA, "IO_SONO": IO_SONO, "LUCCHETTO": LUCCHETTO,
                "TELA": tela, "SCENA": scena, "QUANTI": str(quanti),
                "SHM_BASE": "10b99", "FUORI": giornali_in or "/tmp/10-b99"})
    cmd = [sys.executable, "-u", os.path.join(QUI, "10-b92-dieci.py"), "salita",
           "--quanti", str(quanti), "--durata", str(durata)]
    inf("faccio girare: TELA=%s SCENA=%s QUANTI=%d --durata %d"
        % (tela, scena, quanti, durata))
    p = subprocess.run(cmd, env=amb)
    return p.returncode


# ═════════════════════════════════════════════════════════════════════════════
# §9 · LE PREVISIONI DA SIGILLARE
# ═════════════════════════════════════════════════════════════════════════════
#
# ⛔ Stanno qui, nel codice, **prima** del giro, e vengono sigillate con
#    l'impronta.  ⚠ Cambiarle dopo rompe l'impronta e `confronta` si ferma.

def previsioni_V1(cap):
    """**V1 · la tela** — undici sessioni a **864×480**, scena satura.

    ⛔⛔ E' l'esperimento che DECIDE fra i due modelli possibili, perche' a
       1080p soltanto sono indistinguibili:

       modello **P** «la moneta e' il PIXEL»
           capacita' %(cap).0f Mpixel/s; una sessione 480p satura chiede
           0,4147 Mpixel × ritmo ⇒ undici stanno larghe.
           ⇒ **NESSUN dirupo fino a undici.**

       modello **F** «la moneta e' il FOTOGRAMMA»
           capacita' ≈ %(fot).0f fot/s in tutto, qualunque sia la tela.
           ⇒ **il dirupo arriva allo stesso gradino di 1080p**, cioe' fra il
             sesto e l'ottavo, anche a 480p.

    ⭐ I due modelli danno risposte opposte sullo stesso giro: uno dei due
      **muore**.
    """
    fot = cap.mpixel_s / 2.0736
    return {
        "nome": "V1",
        "scena": "10-b92 · TELA=864x480 · SCENA=satura · QUANTI=11 · h264",
        "capacita_usata_mpixel_s": cap.mpixel_s,
        "ritmo_max_1080p_fot_s": cap.ritmo_max_fps,
        "modello_P_pixel": {
            "dirupo_atteso_al_gradino": None,
            "tot_mpixel_s_all_undicesimo_fra": [120.0, 330.0],
            "min_fot_s_all_undicesimo_almeno": 30.0,
            "ritardo_ms_all_undicesimo_al_massimo": 30.0,
        },
        "modello_F_fotogrammi": {
            "dirupo_atteso_al_gradino": 8,
            "tot_fot_s_al_soffitto": round(fot, 1),
            "min_fot_s_all_undicesimo_al_massimo": 5.0,
        },
        "io_prevedo": "P",
        "come_si_smentisce":
            "⛔ se all'undicesimo gradino la sessione peggiore sta sotto 30 "
            "fot/s, il modello del PIXEL e' morto e il budget non si misura in "
            "pixel al secondo: si misura in fotogrammi al secondo, e la tela "
            "non conta.",
    }


def previsioni_V2(cap):
    """**V2 · il contenuto** — undici sessioni a 1920×1080 con la scena
    **«desktop vero»** invece di quella satura.

    ⚠ Qui la previsione e' **parametrica**, e sta sigillata cosi' apposta: il
      predittore del prodotto non sapra' mai «che scena» sta girando — sapra'
      solo **quanto consegna** chi e' dentro.  ⇒ Si sigilla la FUNZIONE, e la
      si istanzia sul primo gradino del giro stesso.
    """
    return {
        "nome": "V2",
        "scena": "10-b92 · TELA=1920x1080 · SCENA=vero · QUANTI=11 · h264",
        "capacita_usata_mpixel_s": cap.mpixel_s,
        "parametrica": (
            "detta d1 = Mpixel/s consegnati al PRIMO gradino (una sessione "
            "sola), prevedo: tetto N* = floor(%.1f / d1); regge fino a N*; "
            "degrada a N*+1; dirupo (min fot/s < 5) da N*+2 in poi"
            % cap.mpixel_s),
        "assoluta": {
            "d1_atteso_mpixel_s_fra": [60.0, 90.0],
            "tetto_atteso": 6,
            "perche": "⚠ §6.5 dice che il caso leggero di 10-b92 vale [M] "
                      "2 448 B/fotogramma e 0,77 Mbit/s ⇒ ~39 fot/s, cioe' "
                      "quasi come la scena satura: prevedo che «vero» costi "
                      "alla GPU quanto «satura» entro il 25 %, e che il tetto "
                      "resti SEI",
        },
        "come_si_smentisce":
            "⛔ se d1 esce sotto 60 Mpixel/s il «desktop vero» costa meno della "
            "scena satura e il tetto sale: allora il tetto NON e' una proprieta' "
            "della macchina, e un `--tetto-sessioni` fisso e' sbagliato per "
            "costruzione.",
    }


def previsioni_V4(cap):
    """**V4 · quanti buffer il compositore ha dato DAVVERO.**

    ⭐⭐ E' una previsione su una grandezza che **nessuno ha ancora guardato**,
    dedotta dai tempi gia' misurati e sigillata prima che qualcuno la legga.

    L'aritmetica di §1-bis dice che la pista vale `(N − 2) × 1000/60` ms.
    `[M]` L'ultimo gradino che ha retto ha **13,1 ms** di ritardo mediano, il
    primo che ha rotto I1 ne ha **39,9**.  ⇒ Perche' la pista cada fra i due:

        13,1 < (N − 2) × 16,67 < 39,9   ⇒   2,8 < N < 4,4   ⇒   **N = 3 o 4**

    ⛔ E `cattura.c:586` ne chiede **sei**, con minimo quattro.  ⇒ Prevedo che
       **il produttore abbia dato il MINIMO**, non quel che si chiedeva — e se
       e' cosi', il commento di `cattura.c:575` («con quattro il produttore ne
       avrebbe due, e su una raffica si fermerebbe ad aspettarci») descrive
       esattamente quel che succede, **e succede sempre**, non su una raffica.
    """
    return {
        "nome": "V4",
        "scena": "lettura di `buffer_distinti` (cattura.h:198) in un giro "
                 "qualunque sulla strada della scheda",
        "prevedo": "buffer_distinti ∈ {3, 4} — il MINIMO, non i 6 chiesti",
        "da_dove": "13,1 < (N−2)×16,67 < 39,9 sui ritardi di 10-b92 (§6.5)",
        "come_si_smentisce":
            "⛔ se `buffer_distinti` esce **6**, la pista vale 66,7 ms e il "
            "peggioramento del settimo gradino (39,9 ms) NON e' spiegato dai "
            "buffer: allora il meccanismo del dirupo e' un altro, e questa "
            "aritmetica va buttata invece che aggiustata.",
        "cosa_cambia_se_e_vero":
            "⭐ alzare la domanda di `cattura.c:586` da 6 a 8 allungherebbe la "
            "pista da 33 a 100 ms — cioe' `[M]` sposterebbe il dirupo di due "
            "gradini pieni, e non costa che memoria.",
    }


def previsioni_V3(cap):
    """**V3 · le miscele** — i casi che il primo giro NON ha misurato, e che
    l'agente **B8** sta misurando.  ⛔ Qui non si misura: si **prevede**, e si
    confronta col suo risultato quando arriva."""
    d1080 = 2.0736 * cap.ritmo_max_fps
    d480 = 0.41472 * cap.ritmo_max_fps
    d4k = 8.2944 * cap.ritmo_max_fps
    casi = []

    def caso(nome, dentro, nuovo):
        v = prevedi(dentro, nuovo, cap, REGOLA_PEGGIORE)
        casi.append({"caso": nome, "verdetto": v.esito,
                     "domanda_mpixel_s": None if v.domanda is None
                     else round(v.domanda, 1), "perche": v.perche})

    def s1080(n):
        return [Sessione("a%d" % k, 1920, 1080, d1080) for k in range(n)]

    def s480(n):
        return [Sessione("b%d" % k, 864, 480, d480) for k in range(n)]

    caso("una 4K accanto a cinque 1080p",
         s1080(5), Sessione("4k", 3840, 2160))
    caso("cinque 1080p accanto a una 4K gia' dentro",
         [Sessione("4k", 3840, 2160, d4k)] + s1080(4),
         Sessione("sesta", 1920, 1080))
    caso("due 4K", [Sessione("4k1", 3840, 2160, d4k)],
         Sessione("4k2", 3840, 2160))
    caso("una 4K da sola", [], Sessione("4k1", 3840, 2160))
    caso("dieci 480p", s480(9), Sessione("b10", 864, 480))
    caso("venti 480p", s480(19), Sessione("b20", 864, 480))
    caso("trenta 480p", s480(29), Sessione("b30", 864, 480))
    caso("sei 1080p FERME + una satura",
         [Sessione("f%d" % k, 1920, 1080, 0.0) for k in range(6)],
         Sessione("viva", 1920, 1080))
    casi.append({
        "caso": "sei 1080p FERME + una satura — con la regola «consegnato»",
        "verdetto": prevedi(
            [Sessione("f%d" % k, 1920, 1080, 0.0) for k in range(6)],
            Sessione("viva", 1920, 1080), cap, REGOLA_CONSEGNATO).esito,
        "perche": "⚠ le due regole danno risposte DIVERSE su questo caso, ed e' "
                  "esattamente il caso in cui il contenuto conta piu' della tela",
    })
    return {"nome": "V3", "scena": "previsione pura — nessuna misura mia",
            "capacita_usata_mpixel_s": cap.mpixel_s,
            "regola": REGOLA_PEGGIORE, "casi": casi,
            "come_si_smentisce":
                "⛔ B8 misura le miscele: ogni riga qui sopra e' un verdetto "
                "falsificabile.  Un solo «REGGE» che nella misura non regge e' "
                "un falso SI', e vale piu' di dieci verdetti azzeccati."}


# ═════════════════════════════════════════════════════════════════════════════
# §9-bis · ⭐ IL PEZZO PRATICO — che numeri il server ha GIA' in mano
# ═════════════════════════════════════════════════════════════════════════════
#
# ⛔ §3.2 del documento di fase dice che il costo vero (`us_codifica`,
#    `figlio.c:4718`) vive **nel figlio** e non esce mai da quel processo, e che
#    i pixel consegnati si possono derivare dai `MSG_FOTOGRAMMA` che il padre
#    gia' riceve.  ⛔ **Qui lo si VERIFICA sul codice, invece di ripeterlo** —
#    e ogni predicato si legge dai sorgenti, non da un numero di riga scritto
#    a mano, perche' un numero di riga invecchia in silenzio.

def _sorgente(nome, radice=None):
    p = os.path.join(radice or os.path.join(RADICE, "src"), nome)
    if not os.path.exists(p):
        return None
    return open(p, encoding="utf-8", errors="replace").read().split("\n")


def _trova(righe, modello):
    """Torna (numero_di_riga, riga) della prima che combacia, oppure `None`."""
    if righe is None:
        return None
    r = re.compile(modello)
    for k, riga in enumerate(righe, 1):
        if r.search(riga):
            return k, riga.strip()
    return None


def pratico(radice=None, silenzioso=False):
    """I sei predicati che dicono **se serve un canale nuovo oppure no**."""
    src = radice or os.path.join(RADICE, "src")
    main = _sorgente("main.c", src)
    figlio_c = _sorgente("figlio.c", src)
    rcp_c = _sorgente("rcp.c", src)
    rcp_h = _sorgente("rcp.h", src)
    tras = _sorgente("trasporto.c", src)
    esiti = []

    def p(nome, valore, atteso=True, dettaglio=""):
        esiti.append({"predicato": nome, "vero": valore, "atteso": atteso,
                      "dettaglio": dettaglio})
        if silenzioso:
            return
        if valore is None:
            dub("%-56s %s" % (nome, "⛔ NON HO POTUTO LEGGERE"))
        else:
            (ok if valore == atteso else ko)("%-56s %s" % (nome, dettaglio))

    # 1 · il fotogramma arriva al padre con TELA e ISTANTE
    t = _trova(main, r"static void deposita_fotogramma")
    firma = " ".join(main[t[0] - 1:t[0] + 5]) if t else ""
    p("il padre riceve ogni fotogramma con tela e istante",
      None if not t else all(x in firma for x in
                             ("larghezza", "altezza", "istante_us", "byte")),
      True, "" if not t else "main.c:%d deposita_fotogramma()" % t[0])

    # 2 · e li riceve SENZA guardie: anche dai figli che nessuno guarda
    t = _trova(figlio_c, r"f->deposita\(f->ctx")
    guardia = None
    if t and figlio_c:
        prima = "\n".join(figlio_c[max(0, t[0] - 4):t[0] - 1])
        guardia = ("if (f->deposita)" in prima.replace("\t", "")
                   .replace("  ", " ").replace("\n", " ")
                   or "if (f->deposita)" in prima)
    p("e li riceve senza guardie su «qualcuno guarda»",
      None if not t else guardia is True, True,
      "" if not t else "figlio.c:%d — l'unica guardia e' che il gancio "
                       "esista ⇒ il padre vede anche i FANTASMI di §3.2" % t[0])

    # 3 · `us_codifica` non esce dal figlio
    fuori = []
    for nome in ("main.c", "webtransport.c", "rcp.c", "trasporto.c"):
        righe = _sorgente(nome, src)
        if righe and _trova(righe, r"us_codifica"):
            fuori.append(nome)
    dentro = _trova(figlio_c, r"us_codifica")
    p("`us_codifica` vive SOLO nel figlio",
      None if dentro is None else (len(fuori) == 0), True,
      "figlio.c:%d · fuori dal figlio: %s"
      % (dentro[0] if dentro else -1, ", ".join(fuori) or "nessuno"))

    # 4 · non esiste nessun contatore aggregato dei pixel consegnati
    trovati = []
    for nome in ("main.c", "webtransport.c", "rcp.c", "figlio.c"):
        righe = _sorgente(nome, src)
        if righe and _trova(righe, r"(mpixel|pixel_s|pixel_al_secondo|"
                                   r"pixel_consegnati|budget_pixel)"):
            trovati.append(nome)
    p("⛔ NON esiste nessun contatore di pixel/s nel prodotto",
      None if main is None else (len(trovati) == 0), True,
      "trovati in: %s" % (", ".join(trovati) or "nessun file"))

    # 5 · la tela del NUOVO: c'e' al CIAO, ma non esce da rcp.c
    dentro = _trova(rcp_c, r"uint32_t max_l, max_a;")
    esposto = _trova(rcp_h, r"max_l|misura_massima")
    p("il tetto del decodificatore c'e' al CIAO (`video.misura_massima`)",
      None if dentro is None else True, True,
      "rcp.c:%d — `s->max_l/max_a`" % (dentro[0] if dentro else -1))
    p("⛔ ma NON e' esposto da rcp.h: non arriva al verdetto",
      None if rcp_h is None else (esposto is None), True,
      "nessun accessore in rcp.h" if esposto is None
      else "rcp.h:%d" % esposto[0])

    # 6 · che cosa ha in mano `consegna_verdetto`
    t = _trova(main, r"static void consegna_verdetto")
    ponte = _trova(main, r"^struct ponte \{")
    campi = []
    if ponte and main:
        for riga in main[ponte[0]:ponte[0] + 6]:
            if "};" in riga:
                break
            campi.append(riga.strip().rstrip(";"))
    p("il verdetto ha in mano il trasporto e la tabella dei figli",
      None if not (t and ponte) else (len(campi) == 2), True,
      "main.c:%d · ponte = {%s}" % (t[0] if t else -1, ", ".join(campi)))
    t2 = _trova(tras, r"if \(wt_verdetto\(c->w, pratica, ammesso\)\)")
    p("e dalla pratica si risale alla sessione RCP del nuovo",
      None if t2 is None else True, True,
      "trasporto.c:%d — `wt_verdetto()` trova la connessione della pratica ⇒ "
      "`w->rcp` e' li'" % (t2[0] if t2 else -1))

    # 7 · ⭐⭐ LA PISTA DEI BUFFER — i tre numeri dell'aritmetica del dirupo,
    #        letti dal codice invece che ripetuti (§1-bis)
    catt = _sorgente("cattura.c", src)
    catt_h = _sorgente("cattura.h", src)
    cod = _sorgente("codificatore.c", src)
    t = _trova(catt, r"SPA_POD_CHOICE_RANGE_Int\(quanti, minimo, 8\)")
    q = _trova(catt, r"int quanti = .*SCHEDA \? 6 : 4;")
    m = _trova(catt, r"int minimo = .*SCHEDA \? 4 : 2;")
    p("il compositore riceve la domanda di 6 buffer (min 4, max 8)",
      None if not (t and q and m) else True, True,
      "" if not q else "cattura.c:%d — chiesti 6, minimo 4" % q[0])
    t = _trova(catt, r"al massimo DUE\s*$")
    p("e il prodotto ne trattiene al massimo DUE",
      None if t is None else True, True,
      "" if not t else "cattura.c:%d — «uno fermo nel posto e uno in mano»"
                       % t[0])
    t = _trova(catt_h, r"buffer_distinti")
    p("⭐ e quanti ne siano ARRIVATI si conta, non si suppone",
      None if t is None else True, True,
      "" if not t else "cattura.h:%d — `buffer_distinti`" % t[0])
    t = _trova(cod, r"vaSyncSurface\(dpy, destinazione\)")
    p("⛔ e a tenerli e' un'attesa BLOCCANTE (`vaSyncSurface`)",
      None if t is None else True, True,
      "" if not t else "codificatore.c:%d — il commento accanto lo chiama "
                       "«il rilascio»" % t[0])
    # ⛔ E il numero che ne esce, con la sua aritmetica.
    if not silenzioso:
        for n_buf in (4, 6):
            inf("   pista con %d buffer effettivi a 60 Hz: **%.1f ms**"
                % (n_buf, pista_buffer_ms(n_buf, 60.0)))

    if not silenzioso:
        print()
        inf("⇒ ⭐ IL MINIMO CHE SERVE: **un accumulatore** in "
            "`deposita_fotogramma()` (pixel e istanti, per utente) e **un "
            "accessore** in `rcp.h` per `video.misura_massima`.")
        inf("⛔ NON serve nessun canale nuovo fra padre e figlio: "
            "`MSG_FOTOGRAMMA` porta gia' tela e istante, e li porta anche dai "
            "figli che nessuno guarda.")
        inf("⛔⛔ E `buffer_distinti` INVECE SI': vive in `cattura.c`, cioe' "
            "nel FIGLIO, e la pista di decollo non si calcola senza.  ⇒ E' "
            "l'unico numero nuovo che il padre non ha.")
        inf("⚠ E `us_codifica` NON serve: e' il costo del CODIFICATORE, che "
            "`[M]` non e' il collo (27 % contro il 99,5 % del rendering).")
    rossi = [e for e in esiti if e["vero"] != e["atteso"]]
    return esiti, rossi


# ═════════════════════════════════════════════════════════════════════════════
# §9-ter · IL GIUDIZIO — la previsione sigillata contro la misura
# ═════════════════════════════════════════════════════════════════════════════

def giudica(prev, gradini, silenzioso=False):
    """⛔ Confronta ciascuna clausola sigillata con quel che si e' misurato.
    Torna l'elenco delle clausole **smentite** — ⭐ che sono la parte che
    insegna."""
    smentite = []

    def dillo(quale, atteso, visto, tenuta):
        if not silenzioso:
            (ok if tenuta else ko)("%-46s atteso %-22s visto %s"
                                   % (quale, atteso, visto))
        if not tenuta:
            smentite.append(quale)

    ultimo = gradini[-1] if gradini else None
    if ultimo is None:
        dub("⛔ nessun gradino misurato: NON giudico")
        return None
    ritmo1 = gradini[0]["tot_fot_s"] if gradini else None
    # il primo gradino in cui la peggiore scende sotto il 90 % del ritmo pieno
    dirupo = None
    for v in gradini:
        if ritmo1 and v["min_fot_s"] < ritmo1 * 0.90:
            dirupo = v["gradino"]
            break

    if prev.get("nome") == "V1":
        p = prev["modello_P_pixel"]
        f = prev["modello_F_fotogrammi"]
        dillo("P · nessun dirupo fino all'undicesimo", "nessuno",
              "gradino %s" % dirupo, dirupo is None)
        lo, hi = p["tot_mpixel_s_all_undicesimo_fra"]
        dillo("P · totale all'ultimo gradino", "%.0f-%.0f Mpixel/s" % (lo, hi),
              "%.1f" % ultimo["tot_mpixel_s"],
              lo <= ultimo["tot_mpixel_s"] <= hi)
        dillo("P · la peggiore all'ultimo gradino",
              "≥ %.0f fot/s" % p["min_fot_s_all_undicesimo_almeno"],
              "%.2f" % ultimo["min_fot_s"],
              ultimo["min_fot_s"] >= p["min_fot_s_all_undicesimo_almeno"])
        dillo("P · ritardo all'ultimo gradino",
              "≤ %.0f ms" % p["ritardo_ms_all_undicesimo_al_massimo"],
              "?" if ultimo["ritardo_ms"] is None
              else "%.1f" % ultimo["ritardo_ms"],
              ultimo["ritardo_ms"] is not None
              and ultimo["ritardo_ms"] <= p["ritardo_ms_all_undicesimo_al_massimo"])
        # ⭐ E il modello concorrente, giudicato ANCHE LUI: uno dei due muore.
        vinto_F = dirupo is not None and abs(dirupo - f["dirupo_atteso_al_gradino"]) <= 1
        if not silenzioso:
            (ko if vinto_F else ok)(
                "%-46s atteso %-22s visto %s"
                % ("F · il dirupo al gradino %d" % f["dirupo_atteso_al_gradino"],
                   "gradino %d" % f["dirupo_atteso_al_gradino"],
                   "gradino %s ⇒ %s" % (dirupo,
                                        "⛔ VINCE F" if vinto_F else "⭐ F E' MORTO")))
    elif prev.get("nome") == "V2":
        d1 = gradini[0]["tot_mpixel_s"]
        cap = prev["capacita_usata_mpixel_s"]
        tetto = int(cap // d1) if d1 > 0 else None
        lo, hi = prev["assoluta"]["d1_atteso_mpixel_s_fra"]
        dillo("assoluta · d1 (una sessione sola)",
              "%.0f-%.0f Mpixel/s" % (lo, hi), "%.1f" % d1, lo <= d1 <= hi)
        dillo("assoluta · il tetto",
              "%d" % prev["assoluta"]["tetto_atteso"],
              "%s" % ((dirupo - 1) if dirupo else "mai ceduta"),
              dirupo is not None
              and dirupo - 1 == prev["assoluta"]["tetto_atteso"])
        dillo("parametrica · N* = floor(C / d1)", "%s" % tetto,
              "%s" % ((dirupo - 1) if dirupo else "mai ceduta"),
              dirupo is not None and abs((dirupo - 1) - (tetto or -9)) <= 1)
    else:
        dub("⚠ «%s» non ha clausole giudicabili da qui" % prev.get("nome"))
    return smentite


# ═════════════════════════════════════════════════════════════════════════════
# §10 · ⛔⛔ LA CERTIFICAZIONE — i guasti innestati, e FATTI GIRARE
# ═════════════════════════════════════════════════════════════════════════════

def certifica():
    log("10-b99 · ⛔ LA CERTIFICAZIONE — sano → guasto → risanato")
    esiti = []

    def prova(nome, atteso, visto, nota=""):
        buono = (atteso == visto)
        esiti.append({"caso": nome, "atteso": atteso, "visto": visto,
                      "ok": buono})
        (ok if buono else ko)("%-58s atteso %-11s visto %-11s %s"
                              % (nome, atteso, visto, nota))
        return buono

    # ── 0 · il metro si tara PRIMA ────────────────────────────────────────
    log("0 · ⛔ IL METRO SI TARA PRIMA (`LEZIONI.md` §1.33)")
    sano, guai = taratura()
    prova("il lettore ritrova i ritmi iniettati", True, sano,
          "" if sano else str(guai))

    # ⛔ E il controllo NEGATIVO del metro: un lettore guasto deve fallire la
    #    taratura.  Se passa lo stesso, la taratura non serviva a niente.
    orig_fetta = globals()["fetta"]

    def fetta_guasta(g, t0, t1):
        f = orig_fetta(g, t0, t1)
        if f:
            f["fot_s"] *= 0.5           # ⛔ il metro dimezza in silenzio
            f["mpixel_s"] *= 0.5
        return f

    globals()["fetta"] = fetta_guasta
    guasto, _ = taratura(silenzioso=True)
    globals()["fetta"] = orig_fetta
    prova("G0 · metro dimezzato ⇒ la taratura NON passa", False, guasto)
    risanato, _ = taratura(silenzioso=True)
    prova("G0 · risanato ⇒ la taratura ripassa", True, risanato)

    # ── 1 · la scena sbagliata ⇒ «non so», non un numero ──────────────────
    log("1 · ⛔ ALIMENTATO CON I DATI DI UN'ALTRA SCENA ⇒ deve dire «non so»")
    cap = Capacita(480.0, 39.54, FERRO, CATENA_DESKTOP, "satura-1080p",
                   "finta, per la certificazione", 480.0, 559.0, ["1920x1080"])
    dentro_ok = [Sessione("a", 1920, 1080, 80.0, ritardo_ms=10.0)
                 for _ in range(3)]
    prova("sano · tre 1080p dentro, una chiede ⇒ REGGE", REGGE,
          prevedi(dentro_ok, Sessione("n", 1920, 1080), cap).esito)
    nudo = [Sessione("x", 1920, 1080, 80.0, catena=CATENA_NUDA,
                     ritardo_ms=10.0)]
    prova("G1 · una sessione del CODIFICATORE NUDO fra quelle dentro",
          NON_SO, prevedi(nudo, Sessione("n", 1920, 1080), cap).esito,
          "(10-b88: nessun compositore dietro)")
    prova("G1b · il NUOVO viene da un'altra catena", NON_SO,
          prevedi(dentro_ok, Sessione("n", 1920, 1080, catena=CATENA_NUDA),
                  cap).esito)
    prova("G1c · un altro FERRO", NON_SO,
          prevedi(dentro_ok, Sessione("n", 1920, 1080, ferro="AMD RX 6800"),
                  cap).esito)
    prova("risanato · tutti della stessa scena ⇒ REGGE di nuovo", REGGE,
          prevedi(dentro_ok, Sessione("n", 1920, 1080), cap).esito)

    # ── 2 · `None` non e' zero ────────────────────────────────────────────
    log("2 · ⛔ UNA GRANDEZZA NON MISURATA ⇒ `None`, non uno zero")
    cieco = [Sessione("a", None, None, None)] + dentro_ok
    prova("G2 · dentro c'e' uno senza tela E senza consegnato", NON_SO,
          prevedi(cieco, Sessione("n", 1920, 1080), cap).esito)
    prova("G2b · il NUOVO senza tela (`video.misura_massima` assente)",
          NON_SO, prevedi(dentro_ok, Sessione("n", None, None), cap).esito)
    # ⭐ E il ripiego dichiarato: senza consegnato ma CON la tela si usa il
    #   caso peggiore — il verso scomodo — e si risponde lo stesso.
    mezzo = [Sessione("a", 1920, 1080, None, ritardo_ms=10.0)
             for _ in range(3)]
    v = prevedi(mezzo, Sessione("n", 1920, 1080), cap)
    prova("G2c · senza consegnato ma con la tela ⇒ ripiego sul PEGGIORE",
          True, v.esito != NON_SO and v.domanda > 4 * 79.0,
          "domanda %.1f (4 × 82 = 328)" % (v.domanda or 0))
    prova("G2d · e con `None` NON si conta zero: cinque «vuote» + una",
          NON_REGGE,
          prevedi([Sessione("a%d" % k, 1920, 1080, None, ritardo_ms=10.0)
                   for k in range(5)],
                  Sessione("n", 1920, 1080), cap).esito)
    prova("G2e · cinque FERME (0,0) ma SENZA il ritardo ⇒ caso peggiore",
          NON_REGGE,
          prevedi([Sessione("a%d" % k, 1920, 1080, 0.0) for k in range(5)],
                  Sessione("n", 1920, 1080), cap).esito,
          "⚠ senza ritardo «ferma» e «strozzata» sono la stessa riga")
    prova("risanato · le stesse cinque FERME e con 10 ms di ritardo ⇒ REGGE",
          REGGE,
          prevedi([Sessione("a%d" % k, 1920, 1080, 0.0, ritardo_ms=10.0)
                   for k in range(5)],
                  Sessione("n", 1920, 1080), cap).esito)

    # ── 2-bis · ⛔⛔ IL RISVEGLIO — la falla che il consegnato NON copre ────
    log("2-bis · ⛔⛔ IL RISVEGLIO: una sessione ferma costa GPU ZERO, e il "
        "giorno che si muove il budget e' gia' stato speso")
    ferme = lambda n: [Sessione("f%d" % k, 1920, 1080, 0.05, ritardo_ms=10.0)
                       for k in range(n)]
    prova("G2f · quaranta FERME + una ⇒ «consegnato» dice REGGE", REGGE,
          prevedi(ferme(40), Sessione("n", 1920, 1080), cap).esito,
          "⛔ e se si svegliano tutte, la domanda e' 7× la capacita'")
    prova("cura A · «peggiore» le conta al massimo ⇒ NON REGGE", NON_REGGE,
          prevedi(ferme(40), Sessione("n", 1920, 1080), cap,
                  REGOLA_PEGGIORE).esito)
    prova("cura B · «riserva» 50 % ⇒ NON REGGE a quaranta", NON_REGGE,
          prevedi(ferme(40), Sessione("n", 1920, 1080), cap,
                  REGOLA_RISERVA, 0.5).esito)
    prova("cura B · «riserva» 50 % ⇒ REGGE a nove ferme + una", REGGE,
          prevedi(ferme(9), Sessione("n", 1920, 1080), cap,
                  REGOLA_RISERVA, 0.5).esito,
          "⭐ tetto dieci ferme: il numero di SPECIFICHE §5.5")
    prova("⚠ e la riserva a ZERO torna «consegnato» — il controllo negativo",
          REGGE, prevedi(ferme(40), Sessione("n", 1920, 1080), cap,
                         REGOLA_RISERVA, 0.0).esito)
    prova("⚠ e la riserva a UNO torna «peggiore»", NON_REGGE,
          prevedi(ferme(5), Sessione("n", 1920, 1080), cap,
                  REGOLA_RISERVA, 1.0).esito)

    # ── 2-ter · ⭐⭐⭐ LA PISTA DEI BUFFER — la soglia che ha un'ARITMETICA ──
    log("2-ter · ⭐⭐⭐ LA PISTA DEI BUFFER (§1-bis): il dirupo non e' una "
        "saturazione, e' una SOGLIA — e la soglia si calcola")
    prova("pista con 6 buffer effettivi a 60 Hz", 66.7,
          round(pista_buffer_ms(6, 60.0), 1))
    prova("pista con 4 buffer effettivi a 60 Hz", 33.3,
          round(pista_buffer_ms(4, 60.0), 1))
    prova("⭐ e un compositore a 30 Hz ha la pista DOPPIA", 66.7,
          round(pista_buffer_ms(4, 30.0), 1),
          "⇒ un desktop che ridisegna piano tollera piu' contesa")
    prova("G2g · buffer_distinti non letto ⇒ `None`, non «sei»", None,
          pista_buffer_ms(None, 60.0))
    prova("G2h · un prodotto che trattenesse TUTTI i buffer ⇒ pista ZERO",
          0.0, pista_buffer_ms(2, 60.0),
          "⛔ e zero non e' «non lo so»: e' «il compositore si ferma sempre»")
    # ⭐ E le due soglie si incontrano sui numeri VERI.
    c4 = Capacita(479.8, 39.54, FERRO, CATENA_DESKTOP, "satura", "prova",
                  tele_provate=["1920x1080"], ritardo_affanno_ms=22.9,
                  buffer_distinti=4)
    c6 = Capacita(479.8, 39.54, FERRO, CATENA_DESKTOP, "satura", "prova",
                  tele_provate=["1920x1080"], ritardo_affanno_ms=22.9,
                  buffer_distinti=6)
    prova("⭐ con 4 buffer vince la MISURA (22,9 < 33,3)", "misura",
          c4.soglia_affanno()[1],
          "⚠ e le due stanno al 31 %% l'una dall'altra: si incontrano")
    prova("⭐ con 6 buffer vince ancora la misura (22,9 < 66,7)", "misura",
          c6.soglia_affanno()[1])
    c_no = Capacita(479.8, 39.54, FERRO, CATENA_DESKTOP, "satura", "prova",
                    tele_provate=["1920x1080"], ritardo_affanno_ms=None,
                    buffer_distinti=4)
    prova("⭐ senza misura resta l'ARITMETICA — e basta a decidere",
          "pista dei buffer", c_no.soglia_affanno()[1],
          "%.1f ms" % c_no.soglia_affanno()[0])
    c_niente = Capacita(479.8, 39.54, FERRO, CATENA_DESKTOP, "satura", "prova",
                        tele_provate=["1920x1080"], ritardo_affanno_ms=None,
                        buffer_distinti=None)
    prova("G2i · senza NESSUNA delle due ⇒ nessuna soglia", None,
          c_niente.soglia_affanno()[0])
    prova("G2j · e allora si conta il caso PEGGIORE, non zero", NON_REGGE,
          prevedi([Sessione("a%d" % k, 1920, 1080, 0.05, ritardo_ms=10.0)
                   for k in range(6)],
                  Sessione("n", 1920, 1080), c_niente).esito)
    # ⛔ E il controllo che smaschera un'aritmetica cablata invece che letta:
    #    con una pista corta, otto sessioni a 40 ms sono GIA' in affanno.
    c_corta = Capacita(479.8, 39.54, FERRO, CATENA_DESKTOP, "satura", "prova",
                       tele_provate=["1920x1080"], ritardo_affanno_ms=None,
                       buffer_distinti=3)
    prova("G2k · pista corta (3 buffer ⇒ 16,7 ms) ⇒ 40 ms e' affanno",
          NON_REGGE,
          prevedi([Sessione("a", 1920, 1080, 60.0, ritardo_ms=40.0)],
                  Sessione("n", 1920, 1080), c_corta).esito)
    prova("risanato · con la pista lunga (8 buffer ⇒ 100 ms) 40 ms passa",
          REGGE,
          prevedi([Sessione("a", 1920, 1080, 60.0, ritardo_ms=40.0)],
                  Sessione("n", 1920, 1080),
                  Capacita(479.8, 39.54, FERRO, CATENA_DESKTOP, "satura",
                           "prova", tele_provate=["1920x1080"],
                           ritardo_affanno_ms=None,
                           buffer_distinti=8)).esito)

    # ── 3 · il sigillo ────────────────────────────────────────────────────
    log("3 · ⛔⛔ UNA PREVISIONE SCRITTA DOPO LA MISURA ⇒ IMPOSSIBILE")
    tmp = tempfile.mkdtemp(prefix="10b99-cert-")
    anc = Ancore(locale=os.path.join(tmp, "ancore"))
    fs = os.path.join(tmp, "sigilli.jsonl")
    prev = {"nome": "T", "dico": "regge fino a sei"}

    misura = os.path.join(tmp, "misura.jsonl")
    with open(misura, "w") as f:
        f.write("{}\n")
    time.sleep(1.1)
    voce = sigilla("T", prev, anc, fs)
    prova("il sigillo si scrive", True, voce is not None)
    prova("G3 · la misura e' PIU' VECCHIA dell'ancora ⇒ non confronto",
          None, confronta("T", [misura], anc, fs, True),
          "(e' la previsione scritta dopo)")
    time.sleep(1.1)
    with open(misura, "w") as f:                    # misura rifatta ADESSO
        f.write("{}\n")
    prova("risanato · misura piu' giovane dell'ancora ⇒ confronto", True,
          confronta("T", [misura], anc, fs, True) is not None)

    os.remove(os.path.join(anc.locale, "sigillo-T.txt"))
    prova("G3b · l'ancora TOLTA ⇒ non confronto", None,
          confronta("T", [misura], anc, fs, True))
    anc.scrivi("T", voce["impronta"])
    time.sleep(1.1)
    with open(misura, "w") as f:      # ⚠ l'ancora rimessa e' NUOVA: si rimisura
        f.write("{}\n")
    prova("risanato · ancora rimessa ⇒ confronto", True,
          confronta("T", [misura], anc, fs, True) is not None)

    # ⛔ le previsioni cambiate DOPO il sigillo
    righe = [json.loads(r) for r in open(fs) if r.strip()]
    righe[-1]["previsioni"]["dico"] = "regge fino a undici"
    with open(fs, "w") as f:
        for r in righe:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    prova("G3c · previsioni RITOCCATE dopo il sigillo ⇒ non confronto", None,
          confronta("T", [misura], anc, fs, True))
    righe[-1]["previsioni"]["dico"] = "regge fino a sei"
    with open(fs, "w") as f:
        for r in righe:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    prova("risanato · previsioni rimesse ⇒ confronto", True,
          confronta("T", [misura], anc, fs, True) is not None)
    prova("G3d · un sigillo che non esiste ⇒ non confronto", None,
          confronta("MAI-SCRITTO", [misura], anc, fs, True))
    prova("G3e · un file di misura che non c'e' ⇒ non confronto", None,
          confronta("T", [os.path.join(tmp, "fantasma.jsonl")], anc, fs, True))

    # ── 4 · ⛔ ha imparato dal BANCO o dal FERRO? ──────────────────────────
    log("4 · ⛔⛔ UNA MACCHINA FINTA COL SOFFITTO DIVERSO — se indovina lo "
        "stesso, sta RICALCANDO")
    # Una macchina finta che regge il DOPPIO: undici sessioni a pieno ritmo.
    def salita_finta(tetto, quanti=11, fps_pieno=39.54, l=1920, a=1080,
                     dirupo_fps=1.5):
        """Genera una salita come la produrrebbe una macchina con quel tetto:
        fino a `tetto` tutti pieni, oltre il tetto il dirupo — ⭐ **col ritardo
        che sale**, che e' il meccanismo (§6.5)."""
        mp = l * a / 1e6
        punti = []
        for n in range(1, quanti + 1):
            if n <= tetto:
                fps, rit = fps_pieno, 10.0
            elif n == tetto + 1:
                fps, rit = fps_pieno * 0.72, 42.0
            else:
                fps, rit = dirupo_fps, 200.0 + 100.0 * (n - tetto)
            punti.append({
                "sorgente": "macchina finta (tetto %d)" % tetto,
                "scena": "satura", "catena": CATENA_DESKTOP, "ferro": FERRO,
                "gradino": n, "finestra_s": 45.0, "tele": ["%dx%d" % (l, a)],
                "ceduto": n > tetto,
                "tot_mpixel_s": round(n * fps * mp, 2),
                "tot_fot_s": round(n * fps, 2),
                "tot_mbit_s": 1.0, "min_fot_s": round(fps, 2),
                "ritardo_ms": rit, "chiavi": 0,
                "per_sessione_fot_s": {str(k): round(fps, 2)
                                       for k in range(1, n + 1)},
                "per_sessione_ritardo_ms": {str(k): rit
                                            for k in range(1, n + 1)}})
        return punti

    vera = salita_finta(6)
    cap_vera = tara_capacita(vera)
    r = indietro(vera, REGOLA_CONSEGNATO, cap_vera, silenzioso=True)
    prova("sano · tarato sulla macchina VERA, la prevede", True,
          r["falsi_no"] == 0 and r["falsi_si"] == 0,
          "falsi NO %d · falsi SI' %d" % (r["falsi_no"], r["falsi_si"]))

    finta = salita_finta(11)                     # ⛔ soffitto quasi doppio
    r2 = indietro(finta, REGOLA_CONSEGNATO, cap_vera, silenzioso=True)
    prova("G4 · macchina FINTA (tetto 11) col metro della VERA ⇒ deve SBAGLIARE",
          True, r2["falsi_no"] > 0,
          "falsi NO %d (rifiuta chi sarebbe entrato)" % r2["falsi_no"])
    cap_finta = tara_capacita(finta)
    r3 = indietro(finta, REGOLA_CONSEGNATO, cap_finta, silenzioso=True)
    prova("risanato · ritarato SULLA finta, la prevede", True,
          r3["falsi_no"] == 0 and r3["falsi_si"] == 0,
          "capacita' %.0f contro %.0f della vera"
          % (cap_finta.mpixel_s, cap_vera.mpixel_s))
    finta2 = salita_finta(3)                     # ⛔ soffitto dimezzato
    r4 = indietro(finta2, REGOLA_CONSEGNATO, cap_vera, silenzioso=True)
    prova("G4b · macchina finta col tetto a TRE ⇒ deve sbagliare col FALSO SI'",
          True, r4["falsi_si"] > 0,
          "falsi SI' %d (ammette e affama tutti)" % r4["falsi_si"])

    # ── 5 · i due errori si contano SEPARATI ──────────────────────────────
    log("5 · ⛔ I DUE ERRORI NON COSTANO UGUALE, e si contano separati")
    prova("un falso NO e un falso SI' non finiscono nella stessa colonna",
          True, ("falsi_no" in r4 and "falsi_si" in r4 and
                 r4["falsi_si"] != r2["falsi_no"]),
          "finta-3: NO %d SI' %d · finta-11: NO %d SI' %d"
          % (r4["falsi_no"], r4["falsi_si"], r2["falsi_no"], r2["falsi_si"]))

    # ── 6 · la sollecitazione e' ARRIVATA? ────────────────────────────────
    log("6 · ⛔ SI CONTA QUANTA SOLLECITAZIONE E' ARRIVATA (§1.30)")
    # ⛔ Una salita che non arriva mai a far cedere la macchina: il numero piu'
    #    alto letto NON e' un soffitto, e chiamarlo capacita' darebbe un tetto
    #    che e' solo il punto in cui si e' smesso di provare.
    mai = salita_finta(99, quanti=11)
    cm = tara_capacita(mai)
    prova("G6 · una salita che non fa MAI cedere ⇒ soffitto NON visto", False,
          cm.soffitto_visto,
          "capacita' letta %.0f Mpixel/s = limite inferiore" % cm.mpixel_s)
    prova("G6b · e sopra quel limite inferiore il verdetto e' «non so»",
          NON_SO,
          prevedi([Sessione("a%d" % k, 1920, 1080, 82.0, ritardo_ms=10.0)
                   for k in range(11)],
                  Sessione("n", 1920, 1080), cm).esito)
    prova("risanato · la salita che CEDE ⇒ soffitto visto, e si puo' dire no",
          True, cap_vera.soffitto_visto,
          "%.0f Mpixel/s, ceduta al gradino 7" % cap_vera.mpixel_s)
    # ⛔ E una salita in cui la scena NON MORDE: 0,4 fot/s a sessione.
    fermo = salita_finta(99, quanti=11, fps_pieno=0.4)
    cf = tara_capacita(fermo)
    prova("G6c · una scena che non morde ⇒ nessun soffitto e un numero minuscolo",
          True, (not cf.soffitto_visto) and cf.mpixel_s < 20.0,
          "capacita' letta %.2f Mpixel/s" % cf.mpixel_s)

    # ── 6-bis · ⛔⛔ IL CONSEGNATO DA SOLO MENTE DOPO IL DIRUPO ────────────
    log("6-bis · ⛔⛔ DOPO IL DIRUPO IL CONSEGNATO CROLLA — e un budget che "
        "guarda solo i pixel direbbe «c'e' posto»")
    crollo = [Sessione("a%d" % k, 1920, 1080, 1.5 * 2.0736, ritardo_ms=None)
              for k in range(8)]
    v_cieco = prevedi(crollo, Sessione("n", 1920, 1080), cap_vera)
    prova("G6d · otto strozzate SENZA il ritardo ⇒ ripiego sul peggiore",
          NON_REGGE, v_cieco.esito,
          "domanda %.0f Mpixel/s" % (v_cieco.domanda or 0))
    crollo2 = [Sessione("a%d" % k, 1920, 1080, 1.5 * 2.0736, ritardo_ms=636.0)
               for k in range(8)]
    v_rit = prevedi(crollo2, Sessione("n", 1920, 1080), cap_vera)
    prova("G6e · le stesse otto CON il ritardo ⇒ «gia' in affanno»",
          NON_REGGE, v_rit.esito, v_rit.perche[:70])
    # ⛔ E il controllo negativo: senza la porta del ritardo il predittore
    #    direbbe REGGE, che e' il falso SI' che affama tutti.
    cap_senza = Capacita(cap_vera.mpixel_s, cap_vera.ritmo_max_fps, FERRO,
                         CATENA_DESKTOP, "satura", "senza la porta del ritardo",
                         tele_provate=["1920x1080"],
                         ritardo_affanno_ms=1e9)
    prova("G6f · TOLTA la porta del ritardo ⇒ ⛔ FALSO SI' su otto strozzate",
          REGGE, prevedi(crollo2, Sessione("n", 1920, 1080), cap_senza).esito,
          "e' il difetto che la porta cura")
    # ⭐ E LA SOGLIA SI MISURA: dai dati veri, e dai dati che si sovrappongono
    #   non si misura affatto.
    prova("G6g · la soglia del ritardo esce dai DATI, non da una scelta", True,
          cap_vera.ritardo_affanno_ms is not None,
          "" if cap_vera.ritardo_affanno_ms is None
          else "%.1f ms — media geometrica fra sano e rotto"
               % cap_vera.ritardo_affanno_ms)
    confuso = salita_finta(6)
    for p_ in confuso:                     # ⛔ ritardo identico sano e rotto
        p_["ritardo_ms"] = 10.0
    prova("G6h · sano e rotto con lo STESSO ritardo ⇒ nessuna soglia", None,
          tara_capacita(confuso).ritardo_affanno_ms,
          "⚠ e allora la porta si spegne e si conta il caso peggiore")
    prova("G6i · e con la porta spenta NON nasce un falso SI'", NON_REGGE,
          prevedi(crollo2, Sessione("n", 1920, 1080),
                  tara_capacita(confuso)).esito)

    # ── 7 · giornali rotti ────────────────────────────────────────────────
    log("7 · ⛔ IL LETTORE DAVANTI AI GIORNALI ROTTI")
    prova("G7 · giornale che non c'e' ⇒ None", None,
          leggi_giornale(os.path.join(tmp, "mai-esistito.jsonl")))
    p = os.path.join(tmp, "storto.jsonl")
    with open(p, "w") as f:
        f.write("non e' json\n{\"arrivo_ms\": 1}\n")   # riga senza tela
    prova("G7b · righe storte e senza tela ⇒ scartate, lista vuota", 0,
          len(leggi_giornale(p)))
    prova("G7c · finestra piu' corta di un secondo ⇒ None", None,
          fetta(_giornale_finto(30.0, 40.0), 0.0, 500.0))
    prova("G7d · giornale None ⇒ fetta None", None, fetta(None, 0.0, 40000.0))

    # ── 8 · nessuna capacita' ─────────────────────────────────────────────
    log("8 · ⛔ SENZA UNA CAPACITA' MISURATA NON C'E' BUDGET")
    prova("G8 · capacita' None ⇒ «non so», non un tetto a caso", NON_SO,
          prevedi(dentro_ok, Sessione("n", 1920, 1080), None).esito)
    prova("G8b · nessun punto ⇒ nessuna capacita'", None, tara_capacita([]))

    # ── 9 · l'estrapolazione si DICHIARA ──────────────────────────────────
    log("9 · ⚠ UNA TELA MAI PROVATA SI DICHIARA, non si nasconde")
    v = prevedi([], Sessione("4k", 3840, 2160), cap)
    prova("una 4K con la capacita' tarata solo a 1080p ⇒ lo dichiara", True,
          v.estrapola, v.esito)
    v = prevedi([], Sessione("n", 1920, 1080), cap)
    prova("risanato · una 1080p, che e' fra le tele provate ⇒ non estrapola",
          False, v.estrapola)

    # ── 10 · ⛔⛔ E ADESSO COI DATI VERI: la scena sbagliata, non finta ────
    #
    # ⭐ I casi 1 e 4 usano macchine costruite a tavolino.  Qui invece si
    #   prende la capacita' vera di **un'altra scena vera** — il codificatore
    #   nudo di `10-b88`, 1,87 Gpixel/s — e le si fa prevedere la salita coi
    #   desktop veri.  ⛔ Se il predittore indovinasse lo stesso vorrebbe dire
    #   che non e' il numero del ferro a decidere, ed e' un ricalco.
    reali = carica_misure(MISURE, "satura")
    nudi = carica_misure(MISURE, "codificatore-nudo")
    if reali and nudi:
        log("10 · ⛔⛔ COI DATI VERI — la capacita' di UN'ALTRA SCENA VERA")
        c_vera = tara_capacita(reali)
        c_nuda = tara_capacita(nudi)
        inf("desktop veri: %.1f Mpixel/s · codificatore nudo: %.1f Mpixel/s "
            "⇒ fattore %.1f"
            % (c_vera.mpixel_s, c_nuda.mpixel_s,
               c_nuda.mpixel_s / c_vera.mpixel_s))
        r = indietro(reali, REGOLA_CONSEGNATO, c_vera, silenzioso=True)
        prova("sano · capacita' della SUA scena ⇒ zero errori", True,
              r["falsi_no"] == 0 and r["falsi_si"] == 0,
              "NO %d · SI' %d" % (r["falsi_no"], r["falsi_si"]))
        # ⛔ Il travaso: la stessa capacita', ma con l'etichetta della scena
        #    giusta, cosi' la porta della catena non scatta e si vede il DANNO
        #    del numero sbagliato invece del rifiuto.
        c_travasata = Capacita(c_nuda.mpixel_s, c_vera.ritmo_max_fps, FERRO,
                               CATENA_DESKTOP, "⛔ presa da un'altra scena",
                               "10-b88 travasata", tele_provate=["1920x1080"],
                               ritardo_affanno_ms=1e9)
        r2 = indietro(reali, REGOLA_CONSEGNATO, c_travasata, silenzioso=True)
        prova("G10 · capacita' del CODIFICATORE NUDO ⇒ ⛔ falsi SI'", True,
              r2["falsi_si"] > 0,
              "%d falsi SI': ammetterebbe fino a ~%d sessioni dove ne stanno 6"
              % (r2["falsi_si"],
                 int(c_nuda.mpixel_s / (2.0736 * c_vera.ritmo_max_fps))))
        # ⭐ E con l'etichetta VERA la porta scatta prima, e dice «non so».
        prova("risanato · con l'etichetta vera la porta della catena scatta",
              NON_SO,
              prevedi([Sessione("a", 1920, 1080, 80.0, catena=CATENA_NUDA,
                                ritardo_ms=10.0)],
                      Sessione("n", 1920, 1080), c_vera).esito)

    # ── 10-bis · LA MONETA, e il suo controllo NEGATIVO ───────────────────
    log("10-bis · ⭐⭐ LA MONETA — e la prova sa dare TUTT'E DUE le risposte")

    def salita_tela(tetto_mpixel, l, a, fps=39.54, quanti=12,
                    per_fotogramma=False, tetto_fot=None):
        """Una macchina finta in cui la moneta e' nota per costruzione."""
        mp = l * a / 1e6
        punti = []
        for n in range(1, quanti + 1):
            if per_fotogramma:
                ceduto = n * fps > tetto_fot
            else:
                ceduto = n * fps * mp > tetto_mpixel
            f = fps if not ceduto else 1.5
            punti.append({
                "sorgente": "finta", "scena": "s", "catena": CATENA_DESKTOP,
                "ferro": FERRO, "gradino": n, "finestra_s": 45.0,
                "ceduto": ceduto, "tele": ["%dx%d" % (l, a)],
                "tot_mpixel_s": round(n * f * mp, 2),
                "tot_fot_s": round(n * f, 2), "tot_mbit_s": 1.0,
                "min_fot_s": f, "ritardo_ms": 10.0 if not ceduto else 600.0,
                "chiavi": 0, "per_sessione_fot_s": {},
                "per_sessione_ritardo_ms": {}})
        return punti

    a_pixel = (salita_tela(480.0, 1920, 1080) + salita_tela(480.0, 3840, 2160)
               + salita_tela(480.0, 864, 480, quanti=40))
    q, d = moneta(a_pixel, silenzioso=True)
    prova("una macchina che spende PIXEL ⇒ «pixel»", "pixel", q, d[:60])
    a_fot = (salita_tela(0, 1920, 1080, per_fotogramma=True, tetto_fot=237.0)
             + salita_tela(0, 3840, 2160, per_fotogramma=True, tetto_fot=237.0)
             + salita_tela(0, 864, 480, per_fotogramma=True, tetto_fot=237.0,
                           quanti=40))
    q2, d2 = moneta(a_fot, silenzioso=True)
    prova("⭐ una macchina che spende FOTOGRAMMI ⇒ «fotogramma»", "fotogramma",
          q2, "il controllo negativo: la prova non risponde sempre «pixel»")
    prova("G10b · una tela sola ⇒ «non so», mai una moneta", None,
          moneta(salita_tela(480.0, 1920, 1080), silenzioso=True)[0])
    mai = salita_tela(1e9, 1920, 1080) + salita_tela(1e9, 3840, 2160)
    prova("G10c · due tele che non cedono MAI ⇒ «non so»", None,
          moneta(mai, silenzioso=True)[0])
    q3, _ = moneta(carica_misure(MISURE, "codificatore-nudo") or [],
                   silenzioso=True)
    prova("⭐ e sui DATI VERI del codificatore nudo (tre tele)", "pixel", q3)

    # ── 10-ter · LA CONVALIDA: tarare su meno dati non deve produrre falsi SI'
    log("10-ter · ⛔⛔ LA CONVALIDA — tarare su meno gradini puo' far dire "
        "«non so», MAI un falso SI'")
    cv = convalida(vera, silenzioso=True)
    prova("sulla macchina vera: zero falsi SI' a ogni taratura parziale", 0,
          sum(x["falsi_si"] for x in cv))
    prova("e prima di aver visto cedere la macchina dice «non so»", True,
          any(x["non_so"] > 0 and not x["soffitto_visto"] for x in cv),
          "%d tarature su %d non avevano ancora visto il soffitto"
          % (sum(1 for x in cv if not x["soffitto_visto"]), len(cv)))
    reali2 = carica_misure(MISURE, "satura")
    if reali2:
        cv2 = convalida(reali2, silenzioso=True)
        prova("⭐ e sui DATI VERI: zero falsi SI' a ogni k", 0,
              sum(x["falsi_si"] for x in cv2))
        prova("⭐ e zero falsi NO a ogni k", 0,
              sum(x["falsi_no"] for x in cv2))

    # ── 10-quater · IL GIUDIZIO sa dire ANCHE «smentita» ──────────────────
    log("10-quater · ⛔ IL GIUDIZIO — e deve saper smentire, non solo "
        "confermare")
    prev_V1 = leggi_sigillo("V1") or {"previsioni": None}
    if prev_V1["previsioni"]:
        pv = prev_V1["previsioni"]
        # una salita 480p che REGGE fino a 11: P vince, F muore
        buona = [{"gradino": n, "min_fot_s": 40.0, "tot_fot_s": 40.0 * n,
                  "tot_mpixel_s": 40.0 * n * 0.41472, "ritardo_ms": 11.0}
                 for n in range(1, 12)]
        prova("una misura che CONFERMA P ⇒ zero clausole smentite", 0,
              len(giudica(pv, buona, silenzioso=True)))
        # una salita 480p che cede all'ottavo come a 1080p: P muore
        cattiva = []
        for n in range(1, 12):
            f = 40.0 if n <= 6 else (28.0 if n == 7 else 1.5)
            cattiva.append({"gradino": n, "min_fot_s": f, "tot_fot_s": f * n,
                            "tot_mpixel_s": f * n * 0.41472,
                            "ritardo_ms": 11.0 if n <= 6 else 600.0})
        smentite = giudica(pv, cattiva, silenzioso=True)
        prova("G10d · una misura che SMENTISCE P ⇒ clausole smentite", True,
              len(smentite) >= 3, "%d clausole: %s"
              % (len(smentite), "; ".join(smentite)[:70]))
        prova("G10e · nessun gradino misurato ⇒ `None`, non «confermata»",
              None, giudica(pv, [], silenzioso=True))

    # ── 11 · il pezzo pratico, e i guasti innestati SUI SORGENTI ──────────
    log("11 · ⭐ IL PEZZO PRATICO — e i guasti si innestano su una COPIA di "
        "`src/`, mai sull'originale")
    veri, rossi_v = pratico(silenzioso=True)
    prova("sano · gli otto predicati sul `src/` vero", 0, len(rossi_v),
          "; ".join(e["predicato"] for e in rossi_v))
    copia = os.path.join(tmp, "src")
    os.makedirs(copia, exist_ok=True)
    for n in ("main.c", "figlio.c", "rcp.c", "rcp.h", "webtransport.c",
              "trasporto.c", "cattura.c", "cattura.h", "codificatore.c"):
        o = os.path.join(RADICE, "src", n)
        if os.path.exists(o):
            with open(copia + "/" + n, "w") as f:
                f.write(open(o, encoding="utf-8", errors="replace").read())

    def guasta(nome, vecchio, nuovo):
        p = os.path.join(copia, nome)
        t = open(p, encoding="utf-8", errors="replace").read()
        assert vecchio in t, nome
        open(p, "w").write(t.replace(vecchio, nuovo, 1))

    def rimetti(nome):
        o = os.path.join(RADICE, "src", nome)
        with open(os.path.join(copia, nome), "w") as f:
            f.write(open(o, encoding="utf-8", errors="replace").read())

    def quanti_rossi():
        return len(pratico(copia, silenzioso=True)[1])

    prova("la copia sana da' gli stessi otto verdi", 0, quanti_rossi())
    # ⛔ G11a — un contatore di pixel che esiste gia': il predicato «non c'e'»
    #    deve diventare ROSSO, o il banco direbbe «serve un canale nuovo»
    #    quando invece c'e' gia' tutto.
    guasta("main.c", "static void deposita_fotogramma",
           "static uint64_t mpixel_totali;\nstatic void deposita_fotogramma")
    prova("G11a · un contatore di pixel gia' nel prodotto ⇒ rosso", 1,
          quanti_rossi())
    rimetti("main.c")
    prova("risanato", 0, quanti_rossi())
    # ⛔ G11b — `us_codifica` che esce dal figlio
    guasta("webtransport.c", "static void rcp_avvia",
           "/* us_codifica */\nstatic void rcp_avvia")
    prova("G11b · `us_codifica` nominato fuori dal figlio ⇒ rosso", 1,
          quanti_rossi())
    rimetti("webtransport.c")
    # ⛔ G11c — un file che non c'e': «non ho potuto leggere», non un verde
    os.remove(os.path.join(copia, "rcp.h"))
    e_c, r_c = pratico(copia, silenzioso=True)
    prova("G11c · un sorgente mancante ⇒ `None`, mai un verde", True,
          any(e["vero"] is None for e in e_c),
          "%d predicati non letti" % sum(1 for e in e_c if e["vero"] is None))
    rimetti("rcp.h")
    prova("risanato · gli otto tornano verdi", 0, quanti_rossi())

    rossi = [e for e in esiti if not e["ok"]]
    print("\n%s" % _c("== %d casi · %d rossi" % (len(esiti), len(rossi)),
                      "1;31" if rossi else "1;32"))
    for e in rossi:
        ko("%s: atteso %s, visto %s" % (e["caso"], e["atteso"], e["visto"]))
    return 1 if rossi else 0


# ═════════════════════════════════════════════════════════════════════════════
# §11 · IL PROGRAMMA
# ═════════════════════════════════════════════════════════════════════════════

def _sessioni_da_riga(spec):
    """«1920x1080@80/10,1920x1080@0/9,864x480» → tre sessioni.

       forma:  <larghezza>x<altezza>[@<Mpixel/s consegnati>[/<ritardo ms>]]
       ⛔ Senza `@` il consegnato e' `None`, che NON e' zero; senza `/` il
          ritardo e' `None`, e allora «ferma» e «strozzata» non si distinguono
          ⇒ si conta il caso peggiore."""
    v = []
    if not spec:
        return v
    for k, pezzo in enumerate(spec.split(",")):
        pezzo = pezzo.strip()
        if not pezzo:
            continue
        mp = rit = None
        if "@" in pezzo:
            pezzo, m = pezzo.split("@", 1)
            if "/" in m:
                m, r = m.split("/", 1)
                rit = float(r)
            mp = float(m)
        if "x" in pezzo:
            l, a = (int(x) for x in pezzo.split("x", 1))
        else:
            l = a = None
        v.append(Sessione("s%d" % (k + 1), l, a, mp, ritardo_ms=rit))
    return v


def principale():
    p = argparse.ArgumentParser(
        description="10-b99 · il predittore del budget")
    p.add_argument("passo", nargs="?",
                   choices=["taratura", "raccogli", "indietro", "prevedi",
                            "sigilla", "avanti", "confronta", "capacita",
                            "pratico", "moneta", "convalida"])
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--misure", default=MISURE)
    p.add_argument("--giornali", default=None,
                   help="cartella con i giornale-N.jsonl")
    p.add_argument("--remoto", default=None,
                   help="cartella sulla macchina di prova da cui portarli")
    p.add_argument("--scena", default="satura")
    p.add_argument("--etichetta", default="10-b92 · salita")
    p.add_argument("--aggiungi", action="store_true")
    p.add_argument("--b88", action="store_true",
                   help="⭐ aggiunge i punti del CODIFICATORE NUDO di 10-b88 — "
                        "servono a far vedere che il predittore li rifiuta")
    p.add_argument("--dentro", default="")
    p.add_argument("--nuovo", default="")
    p.add_argument("--regola", default=REGOLA_CONSEGNATO,
                   choices=[REGOLA_CONSEGNATO, REGOLA_PEGGIORE,
                            REGOLA_RISERVA])
    p.add_argument("--frazione", type=float, default=FRAZIONE_RISERVA,
                   help="la riserva per sessione, in frazione del suo caso "
                        "peggiore (solo per la regola «riserva»)")
    p.add_argument("--nome", default=None)
    p.add_argument("--tela", default="864x480")
    p.add_argument("--quanti", type=int, default=11)
    p.add_argument("--durata", type=int, default=30)
    p.add_argument("--scena-b92", default="satura")
    p.add_argument("--buffer", type=int, default=6,
                   help="⭐ quanti buffer il compositore ha dato DAVVERO "
                        "(`buffer_distinti`, cattura.h:198).  ⭐ Il "
                        "predefinito e' **6**, e non e' una supposizione: `[M]` "
                        "letto nel registro della salita a undici — 524 righe "
                        "dicono 6 e 65 dicono 8.  ⛔ Non e' lo stesso numero "
                        "per tutte le sessioni, e chi ne ha 6 arriva al muro "
                        "prima di chi ne ha 8")
    p.add_argument("--hz", type=float, default=60.0,
                   help="il ritmo del compositore, per la pista dei buffer")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if not a.passo:
        p.error("serve un passo, oppure --certifica")

    if a.passo == "pratico":
        log("⭐ IL PEZZO PRATICO — che numeri il server ha GIA' in mano nel "
            "punto in cui deve decidere (`main.c` consegna_verdetto)")
        esiti, rossi = pratico()
        return 1 if rossi else 0

    if a.passo == "taratura":
        log("⛔ IL METRO SI TARA PRIMA — `LEZIONI.md` §1.33")
        sano, guai = taratura()
        if sano:
            ok("il lettore dei giornali ritrova i valori iniettati")
            return 0
        for g in guai:
            ko(g)
        return 1

    if a.passo == "raccogli":
        if a.b88:
            return 0 if raccogli_b88(a.misure) else 2
        cart = a.giornali
        if a.remoto:
            cart = cart or os.path.join(tempfile.gettempdir(), "10b99-giornali")
            if porta_giornali(a.remoto, cart) is None:
                ko("⛔ non ho potuto portare i giornali da %s" % a.remoto)
                return 2
        if not cart:
            ko("⛔ serve --giornali o --remoto")
            return 2
        return 0 if raccogli(cart, a.misure, a.etichetta, a.scena,
                             aggiungi=a.aggiungi) else 2

    punti = carica_misure(a.misure, a.scena if a.passo != "capacita" else None)

    if a.passo == "capacita":
        if not punti:
            ko("⛔ nessuna misura in %s" % a.misure)
            return 2
        vv = [q for q in punti if q.get("scena") == a.scena]
        cap = tara_capacita(vv, buffer_distinti=a.buffer, hz_compositore=a.hz)
        if cap is None:
            ko("⛔ non ho potuto tarare la capacita'")
            return 2
        print(json.dumps(cap.dizionario(), ensure_ascii=False, indent=1))
        # ⛔ E IL MARGINE SI SCRIVE DA TUTT'E DUE I LATI (`LEZIONI.md` §1.33):
        #    quanto sta la soglia sopra la domanda piu' alta che ha RETTO (il
        #    lato del falso NO, che costa un utente) e quanto sotto la piu'
        #    bassa che ha CEDUTO (il lato del falso SI', che affama tutti).
        r = indietro(vv, REGOLA_CONSEGNATO, cap, silenzioso=True)
        if r:
            retta = [e["domanda"] for e in r["esiti"]
                     if e["vero"] is True and e["domanda"]]
            ceduta = [e["domanda"] for e in r["esiti"]
                      if e["vero"] is False and e["domanda"]]
            tetto = cap.mpixel_s * (1.0 + cap.tolleranza)
            log("il margine, dai due lati")
            inf("soglia in vigore: %.1f Mpixel/s (capacita' %.1f + %.0f %% di "
                "taratura)" % (tetto, cap.mpixel_s, cap.tolleranza * 100))
            if retta:
                inf("⚠ lato FALSO NO — la domanda piu' alta che ha retto vale "
                    "%.1f ⇒ la soglia le sta sopra del **%.2f %%**"
                    % (max(retta), (tetto - max(retta)) / max(retta) * 100))
            if ceduta:
                inf("⛔ lato FALSO SI' — la domanda piu' bassa che ha ceduto "
                    "vale %.1f ⇒ la soglia le sta sotto del **%.1f %%**"
                    % (min(ceduta), (min(ceduta) - tetto) / min(ceduta) * 100))
            if retta and ceduta:
                m1 = (tetto - max(retta)) / max(retta)
                m2 = (min(ceduta) - tetto) / min(ceduta)
                (ok if m2 > m1 else ko)(
                    "il margine dal lato pericoloso e' **%.0f volte** quello "
                    "dal lato che costa un utente" % (m2 / m1 if m1 else 0))
        # ⭐⭐ E DOVE LA PISTA DEI BUFFER VIENE ATTRAVERSATA — la prova che il
        #    meccanismo di §1-bis regge sui numeri gia' raccolti.
        pista = cap.pista_ms()
        if pista is not None:
            log("la pista dei buffer, contro il ritardo misurato")
            inf("pista = (%d − 2) buffer × 1000/%.0f Hz = **%.1f ms**"
                % (cap.buffer_distinti, cap.hz_compositore, pista))
            prima = ultima = None
            for q in vv:
                if q.get("ritardo_ms") is None:
                    continue
                if q["ritardo_ms"] <= pista:
                    ultima = q
                elif prima is None:
                    prima = q
            if ultima:
                inf("⭐ l'ultimo gradino SOTTO la pista e' il **%d** "
                    "(ritardo %.1f ms) — `[M]` peggior sessione %.2f fot/s"
                    % (ultima["gradino"], ultima["ritardo_ms"],
                       ultima["min_fot_s"]))
            if prima:
                inf("⛔ il primo gradino SOPRA la pista e' il **%d** "
                    "(ritardo %.1f ms) — e li' `[M]` la peggiore sta a "
                    "%.2f fot/s" % (prima["gradino"], prima["ritardo_ms"],
                                    prima["min_fot_s"]))
            # ⛔ E QUI IL PREDICATO DEVE POTER DIRE DI NO.
            #    Il primo giro di questo controllo confrontava il gradino che
            #    attraversa la pista con «l'ultimo sotto piu' uno» — che e' lo
            #    stesso numero per costruzione: un predicato che non sa dare
            #    rosso (`REVIEWER.md` E14).  ⭐ Il confronto vero e' con il
            #    primo gradino in cui **I1 si rompe**, che e' un fatto
            #    indipendente dalla pista.
            # ⛔⛔ E I DUE GRADINI NON SONO LO STESSO FATTO, ed e' il punto:
            #    · **il primo peggioramento** — I1 si rompe, tutti perdono un
            #      pezzo di ritmo ma la sessione vive: e' CONTESA, e la spiega
            #      il conto sui pixel;
            #    · **il dirupo** — il ritmo crolla sotto un quinto: e' la
            #      SOGLIA, e la spiega la pista dei buffer.
            #    ⇒ Confonderli farebbe accusare un meccanismo del danno
            #      dell'altro.
            rotti = [q for q in vv if q.get("ceduto")]
            primo_rotto = rotti[0]["gradino"] if rotti else None
            crollati = [q for q in vv
                        if q.get("min_fot_s") is not None
                        and q["min_fot_s"] < 0.20 * ritmo_pieno_di(vv)]
            dirupo = crollati[0]["gradino"] if crollati else None
            attraversa = prima["gradino"] if prima else None
            if attraversa is None:
                dub("⛔ la pista non viene mai attraversata: non posso "
                    "confrontare")
            elif dirupo is not None and attraversa == dirupo:
                ok("⭐⭐ la pista si attraversa al gradino **%d**, ed e' lo "
                   "STESSO del DIRUPO: l'aritmetica di §1-bis regge sui "
                   "numeri gia' raccolti" % attraversa)
                if primo_rotto is not None and primo_rotto != dirupo:
                    inf("⚠ e NON spiega il primo peggioramento, che e' al "
                        "gradino %d (ritardo %.1f ms, sotto la pista): quello "
                        "e' contesa, e lo spiega il conto sui pixel"
                        % (primo_rotto,
                           rotti[0].get("ritardo_ms") or float("nan")))
            elif dirupo is not None:
                ko("⚠ la pista si attraversa al %d ma il dirupo e' al %d: con "
                   "%d buffer il conto NON torna"
                   % (attraversa, dirupo, cap.buffer_distinti))
            else:
                dub("⛔ nessun dirupo in questi dati: non posso confrontare")
            # ⭐ E DA QUI ESCE UN NUMERO CHE NESSUNO AVEVA: quanti buffer il
            #   compositore abbia dato DAVVERO, dedotto dai tempi.
            # ⛔ E si deduce dai due gradini che il DIRUPO separa, non da
            #    quelli che la pista separa: quelli dipendono dal numero che si
            #    sta cercando, e il conto girerebbe a vuoto su se stesso.
            if dirupo is not None:
                sotto = [q for q in vv if q["gradino"] < dirupo
                         and q.get("ritardo_ms") is not None]
                sopra = [q for q in vv if q["gradino"] == dirupo
                         and q.get("ritardo_ms") is not None]
                if sotto and sopra:
                    lo = sotto[-1]["ritardo_ms"] * cap.hz_compositore / 1000 + 2
                    hi = sopra[0]["ritardo_ms"] * cap.hz_compositore / 1000 + 2
                    dentro = lo < cap.buffer_distinti < hi
                    (ok if dentro else ko)(
                        "⇒ perche' la pista cada nel dirupo, i buffer devono "
                        "stare fra **%.1f e %.1f**: il valore misurato (%d) ci "
                        "sta %s" % (lo, hi, cap.buffer_distinti,
                                    "DENTRO" if dentro else "⛔ FUORI"))
                    inf("⚠ ma il vincolo e' LARGO — un fattore %.0f fra i due "
                        "bordi: la misura e' **compatibile** con l'aritmetica, "
                        "non la conferma" % (hi / lo))
        return 0

    if a.passo == "indietro":
        if not punti:
            ko("⛔ nessuna misura per la scena «%s» in %s" % (a.scena, a.misure))
            return 2
        log("⭐ LA VERIFICA ALL'INDIETRO — e ⛔ da sola NON basta: una funzione "
            "tarata sugli stessi dati che deve prevedere e' un ricalco")
        fuori = 0
        for regola in (REGOLA_CONSEGNATO, REGOLA_RISERVA, REGOLA_PEGGIORE):
            log("regola «%s»%s" % (regola, " (riserva %.0f %%)"
                                   % (a.frazione * 100)
                                   if regola == REGOLA_RISERVA else ""))
            r = indietro(punti, regola,
                         tara_capacita(punti, buffer_distinti=a.buffer,
                                       hz_compositore=a.hz),
                         frazione=a.frazione)
            if r is None:
                ko("⛔ non ho potuto giudicare")
                return 2
            m = ("falsi NO %d (un utente rifiutato per niente) · "
                 "falsi SI' %d (⛔ affama tutti, viola I1) · non so %d"
                 % (r["falsi_no"], r["falsi_si"], r["non_so"]))
            (ok if r["falsi_si"] == 0 else ko)(m)
            if r["falsi_si"]:
                fuori = 1
        return fuori

    if a.passo == "moneta":
        if not punti:
            ko("⛔ nessuna misura per la scena «%s»" % a.scena)
            return 2
        log("⭐⭐ QUALE MONETA — il PIXEL o il FOTOGRAMMA?  (scena «%s»)"
            % a.scena)
        q, _ = moneta(punti)
        return 0 if q else 3

    if a.passo == "convalida":
        if not punti:
            ko("⛔ nessuna misura per la scena «%s»" % a.scena)
            return 2
        log("⛔⛔ LA CONVALIDA — si tara sui primi k gradini e si predicono "
            "gli altri: se sbaglia poco solo quando li ha visti TUTTI, la "
            "verifica all'indietro era un ricalco")
        v = convalida(punti)
        return 0 if v else 2

    if a.passo == "prevedi":
        if not punti:
            ko("⛔ nessuna misura: senza capacita' non c'e' budget")
            return 2
        cap = tara_capacita([q for q in punti if q.get("scena") == a.scena], buffer_distinti=a.buffer, hz_compositore=a.hz)
        dentro = _sessioni_da_riga(a.dentro)
        nuovi = _sessioni_da_riga(a.nuovo)
        if not nuovi:
            ko("⛔ serve --nuovo (per esempio 1920x1080)")
            return 2
        v = prevedi(dentro, nuovi[0], cap, a.regola, a.frazione)
        print(json.dumps(v.dizionario(), ensure_ascii=False, indent=1))
        return 0 if v.esito != NON_SO else 3

    if a.passo == "sigilla":
        if not punti:
            ko("⛔ nessuna misura: non sigillo una previsione senza capacita'")
            return 2
        cap = tara_capacita([q for q in punti if q.get("scena") == "satura"], buffer_distinti=a.buffer, hz_compositore=a.hz)
        quali = {"V1": previsioni_V1, "V2": previsioni_V2,
                 "V3": previsioni_V3, "V4": previsioni_V4}
        nomi = [a.nome] if a.nome else sorted(quali)
        for n in nomi:
            if n not in quali:
                ko("⛔ non so che previsioni siano «%s»" % n)
                return 2
            if leggi_sigillo(n):
                dub("«%s» e' gia' sigillato: NON lo risigillo" % n)
                continue
            sigilla(n, quali[n](cap))
        return 0

    if a.passo == "avanti":
        if not a.nome:
            ko("⛔ serve --nome: si gira contro un sigillo, mai a mano libera")
            return 2
        if leggi_sigillo(a.nome) is None:
            ko("⛔ «%s» non e' sigillato: NON misuro.  Prima si sigilla, poi si "
               "misura — l'ordine e' il metodo" % a.nome)
            return 2
        return gira_b92(a.tela, a.quanti, a.durata, a.scena_b92)

    if a.passo == "confronta":
        if not a.nome or not a.giornali:
            ko("⛔ servono --nome e --giornali")
            return 2
        file_misura = [os.path.join(a.giornali, n)
                       for n in sorted(os.listdir(a.giornali))
                       if re.match(r"^giornale-\d+\.jsonl$", n)]
        if not file_misura:
            ko("⛔ nessun giornale in %s" % a.giornali)
            return 2
        voce = confronta(a.nome, file_misura)
        if voce is None:
            return 2
        g = carica_giornali(a.giornali)
        gr = gradini_da_giornali(g)
        if not gr:
            ko("⛔ i giornali non danno gradini")
            return 2
        print()
        print("      gradino  min fot/s   tot fot/s   tot Mpixel/s   ritardo")
        for v in gr:
            print("      %2d       %8.2f   %9.2f   %12.1f   %s"
                  % (v["gradino"], v["min_fot_s"], v["tot_fot_s"],
                     v["tot_mpixel_s"],
                     "?" if v["ritardo_ms"] is None
                     else "%.1f ms" % v["ritardo_ms"]))
        print()
        rossi = giudica(voce["previsioni"], gr)
        print()
        print(json.dumps(voce["previsioni"], ensure_ascii=False, indent=1))
        return 1 if rossi else 0

    return 0


if __name__ == "__main__":
    sys.exit(principale())
