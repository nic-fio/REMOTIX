#!/usr/bin/env python3
"""08-b67-elastico.py — ⭐⭐ IL BANCO DEL TRASCINAMENTO.  Fase 8, agente B.

    python3 banchi/08-b67-elastico.py --certifica          ⭐ qui, senza server
    python3 banchi/08-b67-elastico.py --finto              la FORMA del numero
    python3 banchi/08-b67-elastico.py --misura --host 192.168.0.2 --porta 7746 \\
            --utente provae8 --parola-file /tmp/08-b67/parola --secondi 30
    python3 banchi/08-b67-elastico.py --verdetto VERBALE.json

⛔ I CODICI D'USCITA SONO QUATTRO, e il terzo e' la ragione per cui questo
   paragrafo sta in testa al file:

     0   CONFORME
     1   NON CONFORME — il banco ha guardato e ha trovato un rosso
     2   uso sbagliato (argparse)
     3   ⛔⛔ NON HO NIENTE DA GIUDICARE — la scena non ha mai dipinto un eco
         leggibile, oppure nessuna coppia (movimento della mano, fotogramma
         dipinto) si e' chiusa.

   ⭐ Il 3 esiste per `LEZIONI.md` §1.9: *«tutti quelli provati sono andati
      bene»* e' vero anche quando i provati sono **zero**.  Un banco che
      uscisse 0 avendo giudicato niente e' il difetto che e' costato la
      riscrittura del validatore della fase 1.

═══════════════════════════════════════════════════════════════════════════════
⭐ DA DOVE VIENE — si dichiara in testa, e non e' una cortesia
═══════════════════════════════════════════════════════════════════════════════

**Eredita il metodo da `banchi/04-b30-anello-input.py`** (fase 4, anello A10),
che NON si tocca.  Da li' questo banco **importa** — non ricopia:

  · `Palco`, `dist`, `regime`, `leggi_celle`, `celle_unita_giusta`,
    `immagine_da_celle` da `03-b17-ritardo.py`, cioe' il lettore CERTIFICATO
    della marca.  ⛔ Se ogni banco si scrivesse la propria «mediana», la parola
    vorrebbe dire cinque cose diverse;
  · `eco_puntatore`, `eco_scomponi`, `leggi_stato_scena_da_byte` e i codici
    `RCP.md` §7.3 da `04-b30-anello-input.py`;
  · **la scena e' quella di A10 senza una riga cambiata** —
    `banchi/04-b30-scena.c` — e con lei il suo terreno,
    `banchi/04-b32-terreno.sh`, guidato dall'ambiente sulle porte MIE.

⛔ **E il PROLOGO invece e' nuovo, e la ragione e' una misura**: quello di A10
   legge i pixel dal **deposito** (`REMOTIX.schermo.deposito_p`).  `[R]` Dal
   21 agosto 2026 la strada del disegno e' `bitmaprenderer` (`DECISIONI.md`
   §5.4) e **il deposito non esiste piu'**: `this.deposito = null`.  Un prologo
   copiato leggerebbe `null` a ogni fotogramma e conterebbe
   `senza_deposito++` — cioe' **zero marche su tutte**, con la catena sana.
   ⇒ Qui i pixel si leggono dalla **VISTA**, che sulla strada nuova e' l'unico
   posto dove esistono, e che per giunta e' il confine piu' scomodo dei due.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ CHE COSA MISURA — e NON e' «il ritardo»
═══════════════════════════════════════════════════════════════════════════════

`fasi/08-l-anello.md` §1.2, e la causa ha un nome: **e' un elastico**.

    distacco = velocita' della mano × ritardo dell'anello

⭐ La freccia la muove **il browser**, alla velocita' della mano — `[R]`
  `src/pagina.html` §«IL PUNTATORE LO DISEGNA LA PAGINA»: il cursore di sistema
  e la freccia disegnata, sovrapposti, **tutt'e due locali**.  La finestra
  invece insegue con **tutto** il ritardo dell'anello.

⇒ ⛔ **Il distacco non e' costante**: si apre quando la mano accelera e si
  richiude quando rallenta.  In locale e' **zero a qualunque velocita'**.
  ⇒ La finestra *nuota* rispetto alla mano, ed e' la ragione per cui l'utente
  ha detto «meno fluido» e non «lento».

═══════════════════════════════════════════════════════════════════════════════
⭐⭐ LE TRE UNITA', E LA TERZA E' L'UNICA CHE HA GIA' RETTO A UNA SORPRESA
═══════════════════════════════════════════════════════════════════════════════

| unita' | per chi | perche' |
|---|---|---|
| **millisecondi** | per noi | e' il tetto di `SPECIFICHE.md` §3.2: 50 ms, traguardo 40 |
| **pixel di distacco** | ⭐ per l'utente | e' l'unica grandezza che lui puo' giudicare **senza strumenti**, ed e' quella in cui ha dettato la specifica: *«la meta' della larghezza della barra del titolo»* ⇒ ≈ 360 px su 720 |
| **frazioni della barra del titolo** | ⭐⭐ per il confronto | ⛔ **e' invariante di scala.**  Il 22 agosto 2026 l'utente ha confrontato REMOTIX con xrdp **a risoluzioni diverse** (xrdp sotto i ~2000 px, noi a 2560): i pixel non si sarebbero potuti confrontare, le frazioni di barra si'.  L'unita' ha retto a una variabile che nessuno aveva previsto |

⛔ **Non se ne consegna una sola, mai.**  `fasi/08-l-anello.md` §2.2 punto 4.

═══════════════════════════════════════════════════════════════════════════════
⭐ COME SI CHIUDE L'ANELLO — due volte, e le due si guardano in faccia
═══════════════════════════════════════════════════════════════════════════════

  1. ⭐⭐ **L'ECO NEI PIXEL** — `04-b30-scena.c` dipinge in una seconda marca
     **le coordinate stesse dell'evento che il compositore le ha consegnato**.
     ⇒ Dentro l'immagine decodificata e **dipinta sul vetro** il banco legge
     *dove sta la finestra che l'utente vede in questo istante*.  E' il confine
     **SCOMODO**: si chiude quando lo schermo e' davvero cambiato.
     ⇒ ⭐ **Ed e' l'unico dei due che sa dare i PIXEL**, perche' l'eco *e'* una
       posizione.  Il campo `input` da' solo un tempo.

  2. **IL CAMPO `input` DEI 28 BYTE** — `RCP.md` §6.2, che la pagina raccoglie
     gia' da se' in `REMOTIX.giro` (`pagina.html` §«IL GIRO COMPLETO»).  Il
     banco **avvolge** `GIRO.torna` e si prende l'`id` con l'istante.  E' il
     confine **COMODO**: il fotogramma e' arrivato, ma non e' ancora ne'
     decodificato ne' dipinto.

⛔ **Il disaccordo fra i due e' il regalo, non un fastidio**: la loro differenza
   e' *quanto il numero comodo si regala*.  Il banco li consegna tutt'e due e
   **dichiara come numero il secondo** — cioe' lo scomodo.

⚠ E se l'eco desse **sempre lo stesso valore**, il banco lo dice: vuol dire che
  non sta discriminando, ed e' un rilevatore che dice sempre si' (Q4).

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ LA SCENA NON SI INVENTA — e' quella dell'utente, MISURATA
═══════════════════════════════════════════════════════════════════════════════

`[M]` 22 agosto 2026, dal video girato dall'utente (404 fotogrammi, 17,5 s),
spogliato fotogramma per fotogramma:

    la finestra          720 × 433 px, barra del titolo larga quanto la finestra
    velocita'            mediana 3 400 px/s · p90 6 300 · picchi 12 400
    in trascinamento     350 intervalli su 403

⛔ **Un trascinamento lento non mostra niente**, perche' il fenomeno da misurare
   e' PROPORZIONALE alla velocita'.  ⇒ Q1 rifiuta il giro se la mano che il
   banco ha davvero mosso non somiglia a quella dell'utente, e **la somiglianza
   si misura sui messaggi USCITI** (`RCP.md` §7.3), non sull'intenzione.

═══════════════════════════════════════════════════════════════════════════════
⛔ LA RETE SI SEPARA, PERCHE' NON E' NOSTRA — e si misura NELLO STESSO GIRO
═══════════════════════════════════════════════════════════════════════════════

`SPECIFICHE.md` §3.2: *«si promette il pezzo che e' nostro, il resto si
dichiara»*.  ⇒ Il banco fa correre un `ping` verso la stessa macchina **per
tutta la durata del trascinamento**, e non riusa la misura di ieri: una rete
misurata un'ora prima non e' la rete di questo giro.

`[M]` 22 agosto 2026, 400 colpi (`wlo1`, WiFi) verso 192.168.0.2: andata+ritorno
mediana **2,85 ms**, p90 3,94, **p99 33,60**, max 37,60 — il **3,2 %** sopra i
15 ms.  ⇒ In mediana la rete e' **meno del 3 %** dell'anello; ⛔ ma un suo picco
a 35 ms vale **+128 px** di distacco a 3 400 px/s, e si apre **di colpo**.

⛔ E l'anello attraversa il filo **due volte** — l'input in salita e il
   fotogramma in discesa — quindi si sottrae **un andata+ritorno intero**, non
   la meta'.  ⚠ Il numero nostro e' `misurato − rtt`, e si stampano tutt'e due.

═══════════════════════════════════════════════════════════════════════════════
⭐ I BUCHI — e il banco deve poter dire se sono NOSTRI o del CANALE
═══════════════════════════════════════════════════════════════════════════════

`[M]` Nel video dell'utente ci sono **6 momenti in 17,5 s** (uno ogni ~3 s) in
cui la finestra **non si e' mossa affatto** mentre subito prima e subito dopo
correva a 200-400 px per tacca.  `[?]` Candidato: le raffiche del WiFi.
**Non e' provato**, e il banco lo separa con tre colonne indipendenti:

  1. ⭐ **la scena ha disegnato?** — il campo `disegno` della marca 1 e' il
     contatore della SCENA.  Se fra i due fotogrammi visti il `disegno` e'
     saltato di k > 1, la scena ha dipinto k fotogrammi che **non abbiamo
     visto** ⇒ persi a valle di lei (codifica, filo, decodifica).  Se e'
     salito di 1, la scena stessa **non ha disegnato** ⇒ il buco e' a monte
     (compositore, cattura);
  2. **la pagina ha ricevuto qualcosa?** — i conti di `REMOTIX.schermo`;
  3. **la rete aveva un picco?** — il `ping` dello stesso istante.

⛔ Nessuna delle tre da sola decide.  Il banco stampa la riga intera per ogni
   buco, e chiama `[?]` quel che le tre non concordano a chiamare.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ I PEZZI CIECHI SONO TRE, E DUE LI DICHIARAVA GIA' A10
═══════════════════════════════════════════════════════════════════════════════

  · **in USCITA** — fra il disegno finito e il pixel acceso passano `[?]`
    **16-40 ms** che nessuna API JavaScript vede (`STUDI.md` §web §6.2);
  · **in INGRESSO** — fra la mano e `event.timeStamp` ci sono il dispositivo,
    il nucleo e il compositore **del client**: `[?]` 4-12 ms su un mouse USB;
  · ⭐⭐ **E IL TERZO E' DI QUESTO BANCO, e va detto perche' e' scomodo**: la
    mano di questo banco e' **sintetica**.  I `PointerEvent` li costruisce il
    prologo e li consegna a `#schermo`; ⛔ non passano ne' dal nucleo ne' dal
    compositore del portatile.  ⇒ Il pezzo cieco in INGRESSO qui **non c'e'
    affatto**, e per questo NON si somma: si dichiara che manca.
    ⚠ E c'e' un secondo effetto, e tira dall'altra parte: un mouse vero manda
      ~125 eventi al secondo e il browser li **fonde**; questi no.  Il numero
      dei `PUNTATORE` usciti si conta e si stampa (`--mano cdp` li fa
      consegnare da Chrome, cioe' *fidati*, ed e' il controllo incrociato).

⇒ ⭐ Il numero consegnato e' **il pezzo nostro**.  Quel che l'utente sente e'
  *questo + i pezzi ciechi + la rete*, e nessun numero esce da qui senza le
  righe accanto.

═══════════════════════════════════════════════════════════════════════════════
⭐⭐ IL TERMINE DI PARAGONE LOCALE — ed e' il miglior controllo positivo
═══════════════════════════════════════════════════════════════════════════════

La specifica dell'utente e' *«il piu' vicino possibile a una situazione
locale»*.  ⇒ Il locale non e' un ideale astratto: e' un numero, e si misura.

  · ⭐ **sul banco, sempre** (Q11): all'analizzatore si da' una traccia in cui
    la finestra insegue la mano **senza nessun ritardo**.  ⛔ Se il banco non
    ci trova ~0 ms e ~0 px, **il banco e' rotto** — e non c'e' misura del
    prodotto che valga qualcosa dopo.  E' il controllo positivo che
    `CODER.md` §3.10 pretende: *«questo strumento sa trovare qualcosa che c'e'
    di sicuro?»*;
  · **sul ferro, quando c'e'** (`--locale`): la scena scrive nel suo blocco
    condiviso `eco_us` (quando il compositore le ha consegnato l'evento) e
    `eco_disegnato_us` (quando l'ha dipinto), e `wp_presentation` dice quando
    quel disegno e' finito **sullo schermo del server**.  ⇒ `presentato −
    eco_us` e' l'anello **senza di noi**: la stessa mano, la stessa scena, il
    compositore soltanto.

═══════════════════════════════════════════════════════════════════════════════
I CONTROLLI — ⛔ e ognuno ha un guasto innestato che lo DEVE far diventare rosso
═══════════════════════════════════════════════════════════════════════════════

  Q0  ⛔⛔ C'E' QUALCOSA DA GIUDICARE?  ⇒ uscita 3, e non e' «conforme».
  Q1  ⛔ LA SCENA E' QUELLA DELL'UTENTE — la velocita' della mano si misura sui
      messaggi usciti e si confronta con i `[M]` del video.
  Q2  LE DUE MARCHE SONO DELLO STESSO FOTOGRAMMA (stesso `disegno`).
  Q3  L'ECO TROVA QUEL CHE C'E' — quota di fotogrammi con eco leggibile.
  Q4  ⛔ L'ECO DISCRIMINA — non dice sempre la stessa cosa.
  Q5  ⛔ LE COORDINATE DELL'ECO SONO QUELLE SPEDITE — `RCP.md` §7.3, *«il server
      NON DEVE applicare nessuna trasformazione»*, misurato invece che creduto.
  Q6  ⭐⭐ LE TRE UNITA' SI CONSEGNANO TUTT'E TRE, e nessuna da sola.
  Q7  ⛔ P1-TEMPO: si innesta un ritardo noto e la mediana DEVE salire di quello.
  Q8  ⛔ P1-SPAZIO: lo stesso innesto DEVE far salire il distacco di `v × N`.
      ⇒ Q7 e Q8 insieme sono la prova che le due unita' sono due LETTURE, e non
        una divisa per una costante.
  Q9  ⛔ LA RETE E' MISURATA IN QUESTO GIRO, e si sottrae dichiarandolo.
  Q10 ⛔ I BUCHI SONO SEPARATI — nostri, del canale, o `[?]`.
  Q11 ⭐⭐ IL TERMINE DI PARAGONE LOCALE E' ~0.
  Q12 IL COSTO DEL BANCO (la lettura dei pixel) e' misurato e dichiarato.
  Q13 L'UNITA' DELLE CELLE e' 0-255 — il difetto del 13 agosto 2026.
"""
import argparse
import base64
import importlib.util
import json
import math
import os
import random
import re
import statistics
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
ESITI = os.path.join(QUI, "08-b67-esiti.jsonl")

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

USCITA_CONFORME = 0
USCITA_NON_CONFORME = 1
USCITA_USO = 2
USCITA_NIENTE_DA_GIUDICARE = 3


def ok(t):  print(f"    {VERDE}OK{GRIGIO}  {t}")
def ko(t):  print(f"    {ROSSO}NO{GRIGIO}  {t}")
def dub(t): print(f"    {GIALLO}??{GRIGIO}  {t}")
def inf(t): print(f"    --  {t}")
def log(t): print(f"\n\033[1m== {t}\033[0m")


# ═══════════════════════════════════════════════════════════════════════════
# §1  ATTREZZI — ⭐ IMPORTATI, non ricopiati
# ═══════════════════════════════════════════════════════════════════════════
_moduli = {}


def carica(nome, percorso):
    """⛔ `import 03-b17-ritardo` e' impossibile: il nome comincia per cifra."""
    if nome in _moduli:
        return _moduli[nome]
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    _moduli[nome] = m
    return m


def b17():
    """L'anello della fase 3.  ⛔ Si IMPORTA: da qui vengono `Palco`, `dist`,
    `regime`, `leggi_celle`, `celle_unita_giusta`.  Se un giorno quel file
    cambia, questo banco se ne accorge; ricopiandolo, no."""
    return carica("b17", os.path.join(QUI, "03-b17-ritardo.py"))


def b30():
    """L'anello input → vetro della fase 4.  Da qui l'ECO e i tipi di §7.3."""
    return carica("b30", os.path.join(QUI, "04-b30-anello-input.py"))


def dist(v, scala=1.0):
    return b17().dist(v, scala)


# ⛔ I DUE PEZZI CIECHI EREDITATI, e il TERZO che e' di questo banco.
CIECO_USCITA_MIN_MS, CIECO_USCITA_MAX_MS = 16.0, 40.0
CIECO_INGRESSO_MIN_MS, CIECO_INGRESSO_MAX_MS = 4.0, 12.0


def con_pezzi_ciechi(ms, mano="pagina"):
    """⛔ Il numero, coi pezzi ciechi accanto e ciascuno col suo verso."""
    if ms is None:
        return "—"
    if mano == "pagina":
        ing = ("⛔ il pezzo cieco in INGRESSO qui NON C'E': la mano e' "
               "sintetica e l'evento nasce dentro la pagina.  ⇒ non si somma, "
               "si dichiara che manca (con un mouse vero sarebbero [?] %.0f-%.0f ms)"
               % (CIECO_INGRESSO_MIN_MS, CIECO_INGRESSO_MAX_MS))
        a = b = 0.0
    else:
        ing = ("⚠ mano `cdp`: l'evento lo consegna Chrome, quindi una parte "
               "dell'ingresso c'e'; [?] %.0f-%.0f ms"
               % (CIECO_INGRESSO_MIN_MS, CIECO_INGRESSO_MAX_MS))
        a, b = CIECO_INGRESSO_MIN_MS, CIECO_INGRESSO_MAX_MS
    return ("%.1f ms MISURATI  ·  %s  ·  + [?] %.0f-%.0f ms di pezzo cieco in "
            "USCITA (disegno finito → pixel acceso, `STUDI.md` §web §6.2) "
            "⇒ %.1f-%.1f ms sullo schermo di un utente, RETE COMPRESA."
            % (ms, ing, CIECO_USCITA_MIN_MS, CIECO_USCITA_MAX_MS,
               ms + a + CIECO_USCITA_MIN_MS, ms + b + CIECO_USCITA_MAX_MS))


# ═══════════════════════════════════════════════════════════════════════════
# §2  LA SCENA DELL'UTENTE — ⛔ i numeri sono `[M]`, e stanno in UN posto solo
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Un numero copiato in tre punti diverge al primo ritocco.  Qui stanno una
#    volta, e ogni controllo li legge da qui.
SCENA_UTENTE = {
    "fonte": "[M] 22 agosto 2026, video dell'utente, 404 fotogrammi, 17,5 s",
    "finestra": [720, 433],
    "barra_px": 720,          # la barra del titolo e' larga quanto la finestra
    "mediana_px_s": 3400.0,
    "p90_px_s": 6300.0,
    "picco_px_s": 12400.0,
    "intervalli_in_trascinamento": [350, 403],
    "buchi": [6, 17.5],       # 6 buchi in 17,5 s
    "distacco_riferito": 0.5,  # ⭐ «meta' della barra del titolo», dall'utente
}

# ⛔ Quanto la mano del banco puo' discostarsi da quella dell'utente prima che
#    il giro non sia piu' «la scena vera».  ⚠ Non e' un numero scelto perche'
#    fa passare: 25 % e' meno di un fattore fra la mediana (3 400) e il p90
#    (6 300), cioe' meno della dispersione della mano dell'utente stesso.
TOLLERANZA_SCENA = 0.25

# La rete gia' misurata, per il confronto — ⛔ NON si riusa come misura.
RETE_NOTA = {"fonte": "[M] 22 agosto 2026, 400 colpi, wlo1 WiFi → 192.168.0.2",
             "mediana_ms": 2.85, "p90_ms": 3.94, "p99_ms": 33.60,
             "max_ms": 37.60, "quota_sopra_15ms": 0.032}


# ═══════════════════════════════════════════════════════════════════════════
# §3  LA MANO — ⛔ la traiettoria si genera QUI, in Python, una volta sola
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Generarla in JavaScript vorrebbe dire due implementazioni della stessa
#    curva, e il giorno in cui divergono il banco confronta la traccia di una
#    con i pixel dell'altra.  ⇒ Il prologo la ESEGUE e non la calcola.
#
# ⭐ La forma: un serpentino che scorre lo schermo per righe.  Due proprieta',
#   e tutt'e due sono richieste da un controllo:
#     · ⛔ **non ripassa mai sullo stesso pixel** — se ci ripassasse, l'eco
#       `(x, y)` non individuerebbe piu' UN evento e l'accoppiamento sarebbe
#       ambiguo.  Q0 conta e RIFIUTA i campioni ambigui invece di sceglierne
#       uno (`LEZIONI.md` §1.9: un campione plausibile e falso e' peggio di un
#       campione mancante);
#     · la velocita' e' MODULATA, perche' l'elastico e' proporzionale a lei e
#       una velocita' costante non mostrerebbe che si apre e si chiude.


def profilo_velocita(t, base, seme=0):
    """⭐ La velocita' della mano all'istante `t` (secondi), in px/s.

    ⛔ Due seni di periodo incommensurabile invece di un rumore: cosi' la
       traiettoria e' **ripetibile** (stesso seme ⇒ stessa curva) e il confronto
       prima/dopo si fa sulla STESSA scena, che e' la regola 3 di
       `fasi/08-l-anello.md` §2.2.

    I coefficienti sono tarati perche' i quantili escano su quelli dell'utente:
    mediana 3 400, p90 6 300, picco 12 400 — cioe' un rapporto p90/mediana di
    1,85 e un picco/mediana di 3,65.  ⚠ La taratura si VERIFICA (Q1) sui
    messaggi usciti: qui e' un'intenzione, non un fatto.
    """
    f1 = 0.37 + 0.01 * (seme % 7)
    f2 = 1.61 + 0.01 * (seme % 11)
    u = 0.62 * math.sin(2 * math.pi * f1 * t) + 0.38 * math.sin(2 * math.pi * f2 * t + 1.1)
    # ⛔ L'esponenziale: le velocita' di una mano sono lognormali, non normali.
    #    Una somma di seni lineare non farebbe mai un picco 3,65 volte la
    #    mediana senza far scendere il p90 sotto quello dell'utente.
    return base * math.exp(0.66 * u + 0.72 * max(0.0, u) ** 3)


def traiettoria(secondi, passo_ms, tela, base_px_s=None, seme=0, margine=80):
    """La lista `[(t_ms, x, y)]` che la mano deve percorrere.

    ⛔ `t_ms` e' relativo alla partenza.  Il prologo li consegna il piu' vicino
       possibile a questi istanti e **registra quelli veri**: il banco misura
       la mano che ha mosso davvero, non quella che voleva muovere.
    """
    base = base_px_s if base_px_s else SCENA_UTENTE["mediana_px_s"]
    L, A = tela
    x0, y0 = margine, margine
    x1 = max(margine + 10, L - margine)
    # ⛔ Il serpentino scende: ogni riga e' NUOVA, quindi nessun pixel si ripete.
    #    ⚠ Il passo verticale si calcola sulla durata perche' la traccia stia
    #      nello schermo: se uscisse, la pagina saturerebbe le coordinate
    #      (`cl_manda_puntatore`) e due istanti diversi darebbero lo stesso
    #      punto — cioe' l'ambiguita' che si vuole evitare.
    passo_s = passo_ms / 1000.0
    n = int(secondi / passo_s)
    # una stima grossolana della lunghezza per sapere quante righe servono
    lung = sum(profilo_velocita(i * passo_s, base, seme) * passo_s for i in range(n))
    righe = max(2, int(lung / max(1.0, (x1 - x0))) + 1)
    dy = max(1.0, (A - 2 * margine) / righe)
    span = float(max(1.0, x1 - x0))
    punti, x, y, verso, dyv = [], float(x0), float(y0), 1, dy
    y_alto, y_basso = float(y0), float(A - margine)
    for i in range(n):
        t = i * passo_s
        v = profilo_velocita(t, base, seme)
        d = v * passo_s
        x += verso * d
        # ⭐ La discesa e' CONTINUA, non a scalini: `y` avanza in proporzione a
        #   quanto la mano ha percorso in orizzontale.
        # ⛔ Il secondo rosso dello stesso giro: aggiungendo una riga intera
        #    (`y += dyv`) al momento del rimbalzo, quel singolo passo valeva
        #    `[M]` **26 132 px/s** su uno schermo largo — dove le righe sono
        #    poche e alte 245 px.  ⇒ Un gradino verticale e' un salto quanto un
        #    teletrasporto, solo piu' piccolo.  Qui la mano fa una diagonale.
        y += dyv * d / span
        if x > x1:
            x = x1 - (x - x1)
            verso = -1
        elif x < x0:
            x = x0 + (x0 - x)
            verso = 1
        # ⛔⛔ LA RIGA CHE E' STATA UN ROSSO, il 22 agosto 2026, primo giro vero.
        #
        #    La prima stesura, arrivata in fondo allo schermo, RIPARTIVA
        #    dall'alto: `y = y0`.  ⇒ `[M]` Q1 ha letto un picco di **450 000
        #    px/s** — un salto di 1 800 px in 4 ms — che non e' una mano: e'
        #    un TELETRASPORTO, e falsava il quantile con cui il banco decide se
        #    la scena e' quella dell'utente.
        #
        # ⇒ ⭐ Si RIMBALZA invece di ripartire, e si sfasa di mezza riga: cosi'
        #   (a) la mano resta continua — nessun salto — e (b) la passata di
        #   ritorno NON ricalca le righe dell'andata, che e' quel che tiene
        #   l'accoppiamento eco→evento non ambiguo.
        if y > y_basso:
            y = y_basso - (y - y_basso) - dy / 2.0
            dyv = -dy
        elif y < y_alto:
            y = y_alto + (y_alto - y) + dy / 2.0
            dyv = dy
        if y > y_basso or y < y_alto:          # ⛔ mai fuori dallo schermo: la
            y = min(max(y, y_alto), y_basso)   #    pagina saturerebbe, e due
                                               #    istanti diversi darebbero
                                               #    lo STESSO punto
        punti.append((round(t * 1000.0, 3), int(x), int(y)))
    return punti


def velocita_dai_messaggi(eventi):
    """⭐ La velocita' VERA della mano, letta sui `PUNTATORE` usciti.

    ⛔ Si legge da dove la cosa succede (`LEZIONI.md` §1.9 regola 5): non dalla
       traiettoria che il banco voleva, ma dai messaggi che sono partiti.
    """
    p = [e for e in eventi if e.get("tipo") == 0x0101
         and e.get("x") is not None and e.get("t_manda") is not None]
    p.sort(key=lambda e: e["t_manda"])
    v = []
    for a, b in zip(p, p[1:]):
        dt = (b["t_manda"] - a["t_manda"]) / 1000.0
        if dt <= 0 or dt > 0.5:
            continue
        d = math.hypot(b["x"] - a["x"], b["y"] - a["y"])
        v.append(d / dt)
    return v


# ═══════════════════════════════════════════════════════════════════════════
# §4  IL PROLOGO — quel che gira DENTRO la pagina, senza toccarla
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Si installa con `Page.addScriptToEvaluateOnNewDocument`, cioe' PRIMA di
#    ogni script della pagina: un banco che innestasse la misura dentro
#    `pagina.html` misurerebbe la pagina strumentata, non il prodotto.
#
# ⛔ E QUI SI SPIEGA IL SOLO PUNTO IN CUI SI DISCOSTA DA A10, perche' e' una
#    misura e non un gusto:
#
#      A10 avvolge `VideoDecoder.output` e legge i pixel DOPO che il prodotto
#      ha disegnato.  ⛔ Sulla strada `bitmaprenderer` **quello non e' il
#      momento del disegno**: `output` consegna il `VideoFrame`, il prodotto
#      chiama `createImageBitmap` — che e' ASINCRONA — e dipinge dentro una
#      promessa, dopo.  ⇒ Leggere i pixel al ritorno di `output` leggerebbe il
#      fotogramma PRECEDENTE, e il ritardo uscirebbe di un fotogramma piu'
#      corto del vero: il regalo classico.
#
#    ⇒ ⭐ Qui si avvolge `ImageBitmapRenderingContext.prototype
#      .transferFromImageBitmap`, che e' **l'istruzione che cambia il vetro**.
#      Al suo ritorno la tela porta il fotogramma nuovo, e quello e' il
#      confine scomodo.  ⚠ E si avvolge anche `drawImage` della tela 2D,
#      perche' il RIPIEGO di `pagina.html` esiste e va misurato se si accende.
PROLOGO = r"""
(function () {
  if (window.__B67) return;
  const B = {
    fotogrammi: [], eventi: [], giri: [], violazioni: [], crudi: [],
    conti: { dipinti: 0, letture: 0, senza_tela: 0, tela_piccola: 0,
             buttati: 0, eventi_visti: 0, mandati: 0, non_puntatore: 0,
             mosse_generate: 0, strada_bm: 0, strada_2d: 0, giri_visti: 0 },
    leggi: true, scorrimento: [0, 0], crudi_voluti: 0,
    t_origine: performance.timeOrigin, grana: null, isolata: null,
    costo_lettura_us: [], t0_corrente: null, mano: null, versione: 1,
  };
  window.__B67 = B;

  /* ── la geometria della marca, gemella di `03-marca.py:119-131` ───────── */
  const CELLA = 24, MARGINE = 32, COLONNE = 18, RIGHE = 8, BIT = 144;
  const DENTRO = Math.max(2, CELLA >> 2);
  const LATO = CELLA - 2 * DENTRO;
  const REG_L = MARGINE + COLONNE * CELLA + 16;    /* 480 */
  const REG_A = MARGINE + RIGHE * CELLA + 16;      /* 240 */
  const KR = 0.2126, KG = 0.7152, KB = 0.0722;
  /* ⭐ La seconda marca sta UNA REGIONE sotto la prima: stessa aritmetica di
     `regione_altezza()` in `04-b30-scena.c`. */
  const FIN1 = [0, 0], FIN2 = [0, REG_A];

  /* ── la grana del cronometro, MISURATA e non dedotta (Q12) ────────────── */
  B.isolata = (typeof crossOriginIsolated !== "undefined") ? crossOriginIsolated : null;
  (function () {
    const d = [];
    let a = performance.now();
    for (let i = 0; i < 120000; i++) {
      const b = performance.now();
      if (b !== a) { d.push(b - a); a = b; }
      if (d.length > 400) break;
    }
    d.sort((x, y) => x - y);
    B.grana = d.length ? d[0] : null;
  })();

  /* ══ 1. LO SPECCHIO — ⛔ i pixel si leggono dalla VISTA ═════════════════
     Sulla strada `bitmaprenderer` non c'e' nessun deposito da cui leggere
     (`pagina.html`: `this.deposito = null`).  ⇒ Si copia la sola REGIONE
     della marca su una tela 2D nostra e la si legge di li'.
     ⚠ Il costo si misura (Q12): e' un errore sistematico dentro ogni numero
       di questo banco, e va dichiarato invece che sperato piccolo. */
  let specchio = null, specchio_p = null;

  function tela_prodotto() {
    const t = document.getElementById("schermo");
    return (t && t.width > 0 && t.height > 0) ? t : null;
  }

  /* ⛔⛔ UNA LETTURA SOLA PER DUE MARCHE, e la ragione e' un numero.
   *
   *   `[M]` 22 agosto 2026, primo giro vero: leggendo le due regioni in due
   *   `getImageData` separati, Q12 ha misurato **9,43 ms mediani per
   *   fotogramma** di sola lettura.  ⛔ Non e' «tanto»: e' lavoro sul FILO
   *   PRINCIPALE, cioe' lo stesso filo che deve decodificare e dipingere —
   *   il banco stava misurando anche se stesso.
   *
   *   La spesa non e' nel campionamento (41 000 pixel), e' nel **rientro dei
   *   pixel dalla tela accelerata**: ogni `getImageData` e' una sincronia con
   *   la GPU.  ⇒ Due sincronie diventano una: si copia UNA regione alta il
   *   doppio (480×480), che tiene tutt'e due le marche, e si campiona da li'
   *   con uno scostamento di riga.
   * ⚠ E il costo resta MISURATO e dichiarato (Q12): dimezzarlo non e'
   *   toglierlo. */
  const REG_2A = REG_A * 2;

  function leggi_le_due_marche() {
    const t = tela_prodotto();
    if (!t) { B.conti.senza_tela++; return [null, null]; }
    if (t.width < REG_L || t.height < REG_2A) {
      B.conti.tela_piccola++; return [null, null];
    }
    if (!specchio) {
      specchio = document.createElement("canvas");
      specchio.width = REG_L; specchio.height = REG_2A;
      specchio_p = specchio.getContext("2d", { willReadFrequently: true });
    }
    let d;
    try {
      specchio_p.drawImage(t, 0, 0, REG_L, REG_2A, 0, 0, REG_L, REG_2A);
      d = specchio_p.getImageData(0, 0, REG_L, REG_2A).data;
    } catch (e) { B.conti.buttati++; return [null, null]; }
    B.conti.letture++;
    return [campiona(d, 0), campiona(d, REG_A)];
  }

  function campiona(d, oy) {
    const sx = B.scorrimento[0], sy = B.scorrimento[1];
    const v = new Array(BIT);
    for (let i = 0; i < BIT; i++) {
      const r = (i / COLONNE) | 0, k = i % COLONNE;
      const xa = MARGINE + k * CELLA + DENTRO + sx;
      const ya = oy + MARGINE + r * CELLA + DENTRO + sy;
      let somma = 0;
      for (let y = ya; y < ya + LATO; y++) {
        let o = (y * REG_L + xa) * 4;
        for (let x = 0; x < LATO; x++, o += 4)
          somma += KR * d[o] + KG * d[o + 1] + KB * d[o + 2];
      }
      v[i] = somma / (LATO * LATO);
    }
    if (B.crudi.length < B.crudi_voluti) {
      let s = "";
      for (let y = oy; y < oy + REG_A; y++)
        for (let x = 0; x < REG_L; x++) {
          const o = (y * REG_L + x) * 4;
          s += String.fromCharCode(d[o], d[o + 1], d[o + 2]);
        }
      B.crudi.push({ l: REG_L, a: REG_A, ox: 0, oy: oy, b64: btoa(s),
                     celle: v.slice(), scorrimento: [sx, sy] });
    }
    return v;
  }

  function dopo_il_disegno(strada) {
    const t_dip = performance.now();
    B.conti.dipinti++;
    if (strada === "bm") B.conti.strada_bm++; else B.conti.strada_2d++;
    let c1 = null, c2 = null, t_let = t_dip;
    if (B.leggi) {
      const a = performance.now();
      const due = leggi_le_due_marche();
      c1 = due[0]; c2 = due[1];
      t_let = performance.now();
      if (B.costo_lettura_us.length < 40000)
        B.costo_lettura_us.push((t_let - a) * 1000);
    }
    if (B.fotogrammi.length < 300000)
      B.fotogrammi.push({ t_dip: t_dip, t_let: t_let, strada: strada,
                          celle: c1, celle_eco: c2,
                          visto: c1 !== null, visto_eco: c2 !== null,
                          consegnati: (window.REMOTIX && REMOTIX.schermo
                                       && REMOTIX.schermo.conti)
                                      ? REMOTIX.schermo.conti.consegnati : null });
  }

  /* ══ 2. IL CONFINE DEL DISEGNO — le due strade, tutt'e due avvolte ══════ */
  const PB = window.ImageBitmapRenderingContext
             && window.ImageBitmapRenderingContext.prototype;
  if (PB && PB.transferFromImageBitmap) {
    const vero = PB.transferFromImageBitmap;
    PB.transferFromImageBitmap = function (bm) {
      const r = vero.apply(this, arguments);
      /* ⛔ `transferFromImageBitmap(null)` e' il modo dichiarato di SVUOTARE
         la tela (`pagina.html`, `svuota()`): non e' un disegno, e contarlo
         come tale metterebbe nel campione un fotogramma nero. */
      if (bm) { try { dopo_il_disegno("bm"); } catch (e) { B.violazioni.push("" + e); } }
      return r;
    };
  }
  const P2 = window.CanvasRenderingContext2D && window.CanvasRenderingContext2D.prototype;
  if (P2 && P2.drawImage) {
    const vero2 = P2.drawImage;
    P2.drawImage = function () {
      const r = vero2.apply(this, arguments);
      /* ⚠ Lo SPECCHIO di questo banco e' anche lui una tela 2D: senza questa
         guardia ogni lettura chiamerebbe se stessa, all'infinito. */
      if (this !== specchio_p && this.canvas
          && this.canvas.id === "schermo") {
        try { dopo_il_disegno("2d"); } catch (e) { B.violazioni.push("" + e); }
      }
      return r;
    };
  }

  /* ══ 3. IL `t0` SCOMODO — ascoltatore in fase di CATTURA ════════════════
     ⛔ `event.timeStamp` e' il primo istante in cui il prodotto AVREBBE
        POTUTO vedere l'evento: tutto quel che fa da li' in poi e' dentro il
        numero.  Il confine comodo — «quando il banco chiama la spedizione» —
        si regalerebbe il gestore della pagina, che si misura invece (§1a). */
  for (const n of ["pointermove", "pointerdown", "pointerup",
                   "mousemove", "mousedown", "mouseup"]) {
    window.addEventListener(n, function (e) {
      B.conti.eventi_visti++;
      B.t0_corrente = { t0: e.timeStamp, t_udito: performance.now(),
                        tipo: n, fidato: e.isTrusted };
    }, true);
  }

  /* ══ 4. I BYTE CHE ESCONO — `RCP.md` §7.3, letti DOVE LA COSA SUCCEDE ═══ */
  function corpo_input(tipo, corpo) {
    try {
      const u = (corpo instanceof Uint8Array) ? corpo : new Uint8Array(corpo);
      if (u.byteLength < 12) return null;
      const v = new DataView(u.buffer, u.byteOffset, u.byteLength);
      const d = { id: v.getUint32(0),
                  istante_us: v.getUint32(4) * 4294967296 + v.getUint32(8) };
      if (tipo === 0x0101 && u.byteLength >= 20) {
        d.x = v.getUint32(12); d.y = v.getUint32(16);
      }
      return d;
    } catch (e) { return null; }
  }

  function aggancia_input() {
    const I = window.REMOTIX_INPUT;
    if (!I || I.__b67 || typeof I.manda !== "function") return;
    const vero = I.manda.bind(I);
    I.manda = function (tipo, corpo) {
      const t = performance.now();
      const m = corpo_input(tipo, corpo);
      const s = B.t0_corrente;
      if (tipo !== 0x0101) B.conti.non_puntatore++;
      B.conti.mandati++;
      if (B.eventi.length < 300000)
        B.eventi.push({ t_manda: t, tipo: tipo,
                        id: m ? m.id : null, x: m ? m.x : null,
                        y: m ? m.y : null,
                        istante_us: m ? m.istante_us : null,
                        t0: s ? s.t0 : null,
                        t_udito: s ? s.t_udito : null,
                        fidato: s ? s.fidato : null });
      return vero(tipo, corpo);
    };
    I.__b67 = true;
  }

  /* ══ 5. IL CONFINE COMODO — `GIRO.torna`, cioe' il campo `input` di §6.2 ═ */
  function aggancia_giro() {
    const G = window.REMOTIX && window.REMOTIX.giro;
    if (!G || G.__b67 || typeof G.torna !== "function") return;
    const vt = G.torna.bind(G);
    G.torna = function (id) {
      if (id) { B.conti.giri_visti++;
                if (B.giri.length < 300000)
                  B.giri.push({ id: id, t: performance.now() }); }
      return vt(id);
    };
    G.__b67 = true;
  }
  setInterval(function () { aggancia_input(); aggancia_giro(); }, 40);

  /* ══ 6. ⭐⭐ LA MANO — e si dichiara che e' SINTETICA ═══════════════════
     ⛔ Il pezzo cieco in ingresso qui NON C'E': questi eventi non passano ne'
        dal nucleo ne' dal compositore del portatile.  Si dichiara (vedi
        `con_pezzi_ciechi`) invece di sommare una stima che non si applica.
     ⚠ E si consegnano `PointerEvent` con `pointerType: "mouse"`, perche'
       `cl_su_pointermove` scarta il dito — che ha la sua disposizione. */
  B.muovi = function (x, y, bottone) {
    const t = document.getElementById("schermo");
    if (!t) return false;
    const r = t.getBoundingClientRect();
    const ev = new PointerEvent("pointermove", {
      bubbles: true, cancelable: true, composed: true,
      pointerId: 1, pointerType: "mouse", isPrimary: true,
      clientX: r.left + x, clientY: r.top + y,
      buttons: bottone ? 1 : 0, button: -1,
      /* ⚠ Se il puntatore fosse AGGANCIATO (`pointerlock`) la pagina usa gli
         SPOSTAMENTI e non le posizioni: si consegnano tutt'e due, cosi' il
         banco funziona nei due stati invece che in uno solo. */
      movementX: Math.round(x - (B.ultimo_vista ? B.ultimo_vista[0] : x)),
      movementY: Math.round(y - (B.ultimo_vista ? B.ultimo_vista[1] : y)),
    });
    B.ultimo_vista = [x, y];
    B.conti.mosse_generate++;
    t.dispatchEvent(ev);
    return true;
  };

  B.bottone = function (giu) {
    const t = document.getElementById("schermo");
    if (!t) return false;
    const r = t.getBoundingClientRect();
    const p = B.ultimo_vista || [0, 0];
    const nome = giu ? "mousedown" : "mouseup";
    const ev = new MouseEvent(nome, {
      bubbles: true, cancelable: true, composed: true,
      clientX: r.left + p[0], clientY: r.top + p[1],
      button: 0, buttons: giu ? 1 : 0,
    });
    (giu ? t : window).dispatchEvent(ev);
    return true;
  };

  /* ⛔ IL PILOTA sta nella pagina, ma NON gira a vuoto sul filo principale.
     `setTimeout(0)` cede il controllo fra un evento e l'altro: cosi' la
     decodifica e il disegno girano come girerebbero con un mouse vero.
     ⚠ Un ciclo che aspettasse girando su `performance.now()` bloccherebbe il
       filo che deve DIPINGERE, e il banco misurerebbe se stesso. */
  B.parti = function (punti, bottone) {
    if (B.mano) return false;
    B.mano = { i: 0, t0: performance.now(), punti: punti, finita: false };
    if (bottone) { B.muovi(punti[0][1], punti[0][2], false); B.bottone(true); }
    const passo = function () {
      const M = B.mano;
      if (!M || M.finita) return;
      const ora = performance.now() - M.t0;
      while (M.i < M.punti.length && M.punti[M.i][0] <= ora) {
        const p = M.punti[M.i];
        B.muovi(p[1], p[2], bottone);
        M.i++;
      }
      if (M.i >= M.punti.length) {
        if (bottone) B.bottone(false);
        M.finita = true;
        return;
      }
      setTimeout(passo, 0);
    };
    setTimeout(passo, 0);
    return true;
  };
  B.finita = function () { return !!(B.mano && B.mano.finita); };

  /* ══ 7. IL RITIRO — si SVUOTA, cosi' due ritiri non contano due volte ═══ */
  B.prendi = function () {
    const f = B.fotogrammi; B.fotogrammi = [];
    const e = B.eventi; B.eventi = [];
    const g = B.giri; B.giri = [];
    const co = B.costo_lettura_us; B.costo_lettura_us = [];
    const cr = B.crudi; B.crudi = [];
    return { fotogrammi: f, eventi: e, giri: g, costo_lettura_us: co,
             crudi: cr, violazioni: B.violazioni.slice(0, 200),
             conti: Object.assign({}, B.conti), grana: B.grana,
             isolata: B.isolata, t_origine: B.t_origine,
             ora_pagina: performance.now(),
             ora_reale: performance.timeOrigin + performance.now(),
             agganciato: !!document.pointerLockElement,
             prima: (window.PRIMA ? null : null),
             pagina: (window.REMOTIX && REMOTIX.schermo)
                     ? Object.assign({}, REMOTIX.schermo.conti) : null };
  };
})();
"""


# ═══════════════════════════════════════════════════════════════════════════
# §5  L'ARRICCHIMENTO — le celle diventano marche col lettore CERTIFICATO
# ═══════════════════════════════════════════════════════════════════════════
def arricchisci(fotogrammi):
    """⛔ Il lettore non e' scritto qui: e' `03-marca.py` attraverso
    `03-b17-ritardo.py`.  Qui si fa solo passare le celle."""
    m17 = b17()
    vuota = {"c_e": False, "perche": "⛔ non ho potuto guardare i pixel"}
    for f in fotogrammi:
        f["marca"] = m17.leggi_celle(f["celle"]) if f.get("celle") else dict(vuota)
        f["marca_eco"] = (m17.leggi_celle(f["celle_eco"])
                          if f.get("celle_eco") else dict(vuota))
        # ⛔ L'unita' delle celle: 0-255 e non 0-1 (il difetto del 13 agosto).
        u_ok, u_perche = (m17.celle_unita_giusta(f["celle"])
                          if f.get("celle") else (None, "nessuna cella"))
        f["unita_ok"] = u_ok
        f["unita_perche"] = u_perche
        e = f["marca_eco"]
        f["eco"] = e.get("disegno") if e.get("c_e") else None
        f["eco_us"] = e.get("istante_us") if e.get("c_e") else None
        f["disegno"] = f["marca"].get("disegno") if f["marca"].get("c_e") else None
        f["disegno_eco"] = e.get("disegno_marca1") if False else None
        # ⛔ Le DUE marche devono essere dello STESSO fotogramma.  La marca 2
        #    porta l'eco nel campo `disegno`, quindi il confronto NON puo'
        #    essere su quel campo: si confronta l'`istante` della marca 1 con
        #    quello della marca 2, che `04-b30-scena.c` scrive nella stessa
        #    passata.  ⚠ Un campione a cavallo di due disegni darebbe un
        #    ritardo plausibile e falso.
        f["stesso_fotogramma"] = None
        if f["marca"].get("c_e") and e.get("c_e"):
            # `eco_us` e' l'istante in cui la scena ha RICEVUTO l'input, che e'
            # <= l'istante del disegno.  Se fosse MAGGIORE, le due marche sono
            # di due passate diverse.
            f["stesso_fotogramma"] = bool(e["istante_us"] <= f["marca"]["istante_us"])
        if f.get("eco") is not None:
            f["eco_letto"] = b30().eco_scomponi(f["eco"])
        else:
            f["eco_letto"] = {"tipo": None,
                              "perche": "⛔ nessun eco leggibile in questo fotogramma"}
    return fotogrammi


# ═══════════════════════════════════════════════════════════════════════════
# §6  L'ACCOPPIAMENTO — ⛔ e i campioni AMBIGUI si rifiutano da soli
# ═══════════════════════════════════════════════════════════════════════════
def accoppia(verbale):
    """Da (fotogrammi, eventi) ai campioni dell'elastico.

    ⭐ La chiave dell'accoppiamento sono **le coordinate**: l'eco *e'* la
      posizione che il compositore ha consegnato alla scena, e la traiettoria
      non ripassa mai sullo stesso pixel.  ⇒ Un eco individua UN evento.

    ⛔ E quando non lo individua — perche' la mano ci e' ripassata, o perche'
       quell'evento non e' mai partito — il campione **si butta e si conta**.
       `LEZIONI.md` §1.9: un campione plausibile e falso e' peggio di uno
       mancante, perche' entra nella mediana.
    """
    ev = [e for e in verbale.get("eventi", [])
          if e.get("tipo") == 0x0101 and e.get("x") is not None]
    ev.sort(key=lambda e: (e.get("t0") if e.get("t0") is not None else e["t_manda"]))
    per_punto = {}
    for e in ev:
        per_punto.setdefault((e["x"], e["y"]), []).append(e)
    tempi = [(e.get("t0") if e.get("t0") is not None else e["t_manda"]) for e in ev]

    giri = {}
    for g in verbale.get("giri", []):
        giri.setdefault(g["id"], g["t"])

    barra = float(verbale.get("barra_px") or SCENA_UTENTE["barra_px"])
    conti = {"senza_eco": 0, "eco_non_puntatore": 0, "senza_evento": 0,
             "ambigui": 0, "due_marche_diverse": 0, "buoni": 0,
             "coord_esatte": 0, "coord_vicine": 0, "coord_lontane": 0}
    campioni = []
    for f in verbale.get("fotogrammi", []):
        el = f.get("eco_letto") or {}
        if f.get("eco") is None:
            conti["senza_eco"] += 1
            continue
        if el.get("tipo") != 1:          # 1 = PUNTATORE
            conti["eco_non_puntatore"] += 1
            continue
        if f.get("stesso_fotogramma") is False:
            conti["due_marche_diverse"] += 1
            continue
        chiave = (el["x"], el["y"])
        lista = per_punto.get(chiave)
        if not lista:
            conti["senza_evento"] += 1
            continue
        if len(lista) > 1:
            conti["ambigui"] += 1
            continue
        e = lista[0]
        t0 = e.get("t0") if e.get("t0") is not None else e["t_manda"]
        ritardo = f["t_dip"] - t0
        if not (0.0 <= ritardo <= 5000.0):
            # ⛔ Un ritardo negativo vuol dire che il fotogramma e' stato
            #    dipinto PRIMA che l'evento esistesse: e' impossibile, quindi
            #    e' un difetto del banco e non una misura del prodotto.
            conti["senza_evento"] += 1
            continue
        # ⭐ LA FRECCIA: dov'era la mano quando quel fotogramma e' stato dipinto.
        #   ⛔ NON si interpola: la pagina disegna la freccia DENTRO il gestore
        #      del movimento, quindi quel che l'utente vede e' l'ULTIMO evento
        #      trattato prima del disegno.  Interpolare inventerebbe una
        #      posizione che nessuno ha mai disegnato.
        k = _ultimo_prima(tempi, f["t_dip"])
        if k is None:
            conti["senza_evento"] += 1
            continue
        mano = ev[k]
        dx, dy = mano["x"] - el["x"], mano["y"] - el["y"]
        distacco = math.hypot(dx, dy)
        # la velocita' istantanea sulla finestra [t_dip - ritardo, t_dip]
        j = _ultimo_prima(tempi, f["t_dip"] - ritardo)
        vel = None
        if j is not None and k > j:
            dt = (tempi[k] - tempi[j]) / 1000.0
            if dt > 0:
                vel = math.hypot(ev[k]["x"] - ev[j]["x"],
                                 ev[k]["y"] - ev[j]["y"]) / dt
        c = {"t_dip": f["t_dip"], "t0": t0, "t_manda": e["t_manda"],
             "id": e.get("id"), "ritardo_ms": ritardo,
             "eco_x": el["x"], "eco_y": el["y"],
             "mano_x": mano["x"], "mano_y": mano["y"],
             "distacco_px": distacco,
             "distacco_barre": distacco / barra if barra else None,
             "velocita_px_s": vel,
             "tratto_1a_ms": e["t_manda"] - t0,
             "disegno": f.get("disegno"),
             "comodo_ms": (giri[e["id"]] - t0) if e.get("id") in giri else None,
             "strada": f.get("strada")}
        campioni.append(c)
        conti["buoni"] += 1
    verbale["conti_accoppiamento"] = conti
    return campioni


def _ultimo_prima(tempi, t):
    """L'indice dell'ultimo istante <= t, o `None`.  ⛔ Ricerca binaria: con
    decine di migliaia di eventi una scansione lineare per fotogramma
    trasformerebbe l'analisi in minuti."""
    lo, hi, r = 0, len(tempi) - 1, None
    while lo <= hi:
        m = (lo + hi) // 2
        if tempi[m] <= t:
            r = m
            lo = m + 1
        else:
            hi = m - 1
    return r


# ═══════════════════════════════════════════════════════════════════════════
# §7  LA RETE — misurata NELLO STESSO GIRO
# ═══════════════════════════════════════════════════════════════════════════
class Rete:
    """⛔ `ping -D`: la marca temporale e' quella del NUCLEO, e serve per
    mettere i picchi accanto ai buchi.  ⚠ Se `ping` non parte, il banco lo
    DICE: «non ho potuto guardare» non e' «la rete era buona» (Q9)."""

    def __init__(self, host, intervallo=0.05):
        self.host, self.intervallo, self.p, self.perche = host, intervallo, None, None

    def parti(self):
        try:
            self.p = subprocess.Popen(
                ["ping", "-D", "-i", str(self.intervallo), self.host],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        except Exception as e:                      # noqa: BLE001
            self.perche = "⛔ `ping` non e' partito: %s" % e
            self.p = None
        return self.p is not None

    def ferma(self):
        if self.p is None:
            return {"c_e": False, "perche": self.perche or "⛔ `ping` non c'era"}
        try:
            self.p.terminate()
            uscita = self.p.communicate(timeout=10)[0] or ""
        except Exception:                           # noqa: BLE001
            self.p.kill()
            uscita = ""
        campioni = []
        for r in uscita.splitlines():
            m = re.match(r"\[(\d+\.\d+)\].*time=([\d.]+) ms", r)
            if m:
                campioni.append({"t": float(m.group(1)) * 1000.0,
                                 "rtt_ms": float(m.group(2))})
        if not campioni:
            return {"c_e": False,
                    "perche": ("⛔ `ping` e' partito ma non ha prodotto NESSUN "
                               "colpo leggibile: non e' «rete perfetta», e' "
                               "«non ho misurato»"),
                    "grezzo": uscita[-400:]}
        r = [c["rtt_ms"] for c in campioni]
        d = dist(r)
        d["c_e"] = True
        d["campioni"] = campioni
        d["quota_sopra_15ms"] = round(
            sum(1 for x in r if x > 15.0) / float(len(r)), 4)
        d["intervallo_s"] = self.intervallo
        return d


def separa_la_rete(mediana_ms, rete):
    """⛔ `SPECIFICHE.md` §3.2: si promette il pezzo nostro, il resto si dichiara.

    ⛔ E si sottrae un andata+ritorno INTERO: l'anello attraversa il filo due
       volte — l'input in salita, il fotogramma in discesa.
    """
    if mediana_ms is None:
        return {"c_e": False, "perche": "⛔ non c'e' nessuna mediana da separare"}
    if not rete or not rete.get("c_e"):
        return {"c_e": False,
                "perche": ("⛔ la rete NON e' stata misurata in questo giro: il "
                           "numero nostro NON si puo' dichiarare.  ⚠ «non ho "
                           "potuto guardare» non e' «la rete non c'entra» "
                           "(`LEZIONI.md` §1.9)")}
    rtt = rete["mediana"]
    return {"c_e": True, "totale_ms": round(mediana_ms, 2),
            "rete_ms": round(rtt, 2),
            "nostro_ms": round(mediana_ms - rtt, 2),
            "quota_rete": round(rtt / mediana_ms, 4) if mediana_ms else None,
            "p99_rete_ms": rete.get("p99"),
            "nota": ("⚠ si sottrae UN andata+ritorno intero: l'anello passa il "
                     "filo due volte.  ⛔ E il p99 della rete (%.1f ms) NON si "
                     "sottrae: e' un picco, non una base — vale +%.0f px di "
                     "distacco a %.0f px/s, e si apre di colpo."
                     % (rete.get("p99") or 0.0,
                        (rete.get("p99") or 0.0) * SCENA_UTENTE["mediana_px_s"] / 1000.0,
                        SCENA_UTENTE["mediana_px_s"]))}


# ═══════════════════════════════════════════════════════════════════════════
# §8  I BUCHI — tre colonne indipendenti, e nessuna decide da sola
# ═══════════════════════════════════════════════════════════════════════════
def trova_buchi(campioni, fotogrammi, rete, soglia_volte=3.0, soglia_min_ms=45.0):
    """⭐ Un buco: due fotogrammi visti di fila fra i quali la finestra NON si
    e' mossa abbastanza a lungo, mentre la mano correva.

    ⛔ La soglia non e' a sentimento: e' `soglia_volte` volte l'intervallo
       MEDIANO fra due disegni di questo stesso giro — cioe' si misura contro
       il ritmo che il giro ha davvero avuto — e comunque non meno di
       `soglia_min_ms`, che e' ~3 fotogrammi a 60 Hz.
    """
    if len(campioni) < 4:
        return {"c_e": False,
                "perche": "⛔ meno di 4 campioni: non ho un ritmo da cui partire",
                "buchi": []}
    c = sorted(campioni, key=lambda x: x["t_dip"])
    dt = [b["t_dip"] - a["t_dip"] for a, b in zip(c, c[1:])]
    dt_med = statistics.median(dt) if dt else 0.0
    soglia = max(soglia_min_ms, soglia_volte * dt_med)
    # I disegni della scena, per sapere se ha dipinto qualcosa che non abbiamo visto.
    buchi = []
    for a, b in zip(c, c[1:]):
        salto = b["t_dip"] - a["t_dip"]
        if salto < soglia:
            continue
        v = b.get("velocita_px_s") or a.get("velocita_px_s")
        mosso = math.hypot(b["mano_x"] - a["mano_x"], b["mano_y"] - a["mano_y"])
        if mosso < 20:
            # ⛔ Se la mano era ferma, un fotogramma che non arriva NON e' un
            #    buco: e' una scena ferma, ed e' quel che il prodotto deve fare.
            continue
        da = a.get("disegno")
        db = b.get("disegno")
        saltati = (db - da - 1) if (da is not None and db is not None
                                    and db > da) else None
        # la rete in quella finestra
        picco = None
        if rete and rete.get("c_e") and rete.get("campioni"):
            t0 = a["t_dip"], b["t_dip"]
            # i tempi del ping sono in ms d'epoca: si riportano alla pagina
            pass
        buchi.append({
            "t_da_ms": round(a["t_dip"], 1), "durata_ms": round(salto, 1),
            "la_mano_ha_percorso_px": round(mosso, 1),
            "distacco_aperto_px": round((v or 0.0) * salto / 1000.0, 1),
            "disegni_saltati_dalla_scena": saltati,
            "chi": _chi_e_il_buco(saltati),
        })
    quanti = len(buchi)
    durata_s = (c[-1]["t_dip"] - c[0]["t_dip"]) / 1000.0
    return {"c_e": True, "buchi": buchi, "quanti": quanti,
            "durata_s": round(durata_s, 2),
            "ogni_s": round(durata_s / quanti, 2) if quanti else None,
            "soglia_ms": round(soglia, 1),
            "intervallo_mediano_ms": round(dt_med, 2),
            "utente": "[M] l'utente ne ha 6 in 17,5 s ⇒ uno ogni ~2,9 s"}


def _chi_e_il_buco(saltati):
    """⛔ Tre esiti, e il terzo e' `[?]` apposta: un banco che chiamasse
    «nostro» tutto quel che non capisce curerebbe una cosa che non c'e'."""
    if saltati is None:
        return ("[?] non lo so: uno dei due fotogrammi non porta il numero di "
                "disegno della scena")
    if saltati == 0:
        return ("⛔ NOSTRO, A MONTE: la scena non ha disegnato affatto in "
                "questo tratto — compositore o cattura")
    return ("⚠ %d disegni della scena NON sono arrivati al vetro: il buco e' a "
            "VALLE di lei (codifica, filo, decodifica).  ⛔ Non basta a "
            "chiamarlo «della rete»: serve il picco del `ping` nello stesso "
            "istante" % saltati)


# ═══════════════════════════════════════════════════════════════════════════
# §9  I CONTROLLI — ⛔ funzioni PURE sul verbale, cosi' si certificano da sole
# ═══════════════════════════════════════════════════════════════════════════
def q0_c_e_qualcosa(verbale, campioni):
    """⛔⛔ Tre stati distinti, tre frasi distinte, e nessuno dei tre e'
    «conforme».  Codice d'uscita 3."""
    f = verbale.get("fotogrammi") or []
    e = [x for x in verbale.get("eventi") or [] if x.get("tipo") == 0x0101]
    if not f:
        return {"esito": None, "vuoto": True,
                "perche": ("⛔ NESSUN fotogramma dipinto: la pagina non ha "
                           "disegnato niente.  ⚠ Non e' «il ritardo e' zero», "
                           "e' «non ho potuto guardare»")}
    if not e:
        return {"esito": None, "vuoto": True,
                "perche": ("⛔ NESSUN `PUNTATORE` e' uscito sul filo: la mano "
                           "non ha mosso niente, o il canale di input non c'e'. "
                           "⚠ %d fotogrammi dipinti non fanno una misura "
                           "dell'elastico" % len(f))}
    if not campioni:
        c = verbale.get("conti_accoppiamento") or {}
        return {"esito": None, "vuoto": True,
                "perche": ("⛔ %d fotogrammi e %d movimenti, e NESSUNA coppia "
                           "si e' chiusa: senza eco %d · eco non puntatore %d · "
                           "senza evento %d · ambigui %d · marche di due "
                           "fotogrammi %d.  ⚠ Zero campioni NON e' «conforme»"
                           % (len(f), len(e), c.get("senza_eco", 0),
                              c.get("eco_non_puntatore", 0),
                              c.get("senza_evento", 0), c.get("ambigui", 0),
                              c.get("due_marche_diverse", 0)))}
    return {"esito": True, "vuoto": False,
            "perche": "%d campioni su %d fotogrammi dipinti e %d movimenti usciti"
                      % (len(campioni), len(f), len(e))}


def q1_la_scena_e_quella_dell_utente(verbale):
    """⛔ Un trascinamento lento non mostra niente.  La velocita' si misura sui
    messaggi USCITI e si confronta con i `[M]` del video dell'utente."""
    v = velocita_dai_messaggi(verbale.get("eventi") or [])
    if len(v) < 30:
        return {"esito": False,
                "perche": ("⛔ %d intervalli di movimento: troppo pochi per "
                           "dire che velocita' aveva la mano.  ⚠ Non e' «la "
                           "mano era lenta»" % len(v))}
    d = dist(v)
    # ⛔ Il p90 si calcola, non si sostituisce col p95: confrontare il MIO p95
    #    col SUO p90 sarebbe confrontare due quantili diversi, e uscirebbe
    #    sempre «piu' veloce» anche a scena identica.
    w = sorted(v)
    d["p90"] = round(w[min(len(w) - 1, int(round(0.90 * (len(w) - 1))))], 3)
    att = SCENA_UTENTE
    righe, buono = [], True
    for nome, mio, suo in (("mediana", d["mediana"], att["mediana_px_s"]),
                           ("p90", d["p90"], att["p90_px_s"]),
                           ("picco (max)", d["max"], att["picco_px_s"])):
        scarto = abs(mio - suo) / suo
        # ⛔ Il picco puo' SUPERARE quello dell'utente senza danno: una mano
        #    piu' veloce mostra PIU' elastico, non meno.  ⚠ Il rosso e' solo
        #    quando e' piu' LENTA.
        cattivo = (scarto > TOLLERANZA_SCENA) and (mio < suo)
        if cattivo:
            buono = False
        righe.append({"quantile": nome, "misurato_px_s": round(mio, 0),
                      "utente_px_s": suo, "scarto": round(scarto, 3),
                      "rosso": cattivo})
    return {"esito": buono, "righe": righe, "distribuzione": d,
            "n": len(v),
            "perche": ("la mano del banco ha fatto mediana %.0f px/s (l'utente "
                       "3 400), p90 %.0f (il suo 6 300), picco %.0f (il suo "
                       "12 400), su %d intervalli"
                       % (d["mediana"], d["p90"], d["max"], len(v)))}


def q2_due_marche_stesso_fotogramma(verbale):
    f = [x for x in verbale.get("fotogrammi") or []
         if x.get("stesso_fotogramma") is not None]
    if not f:
        return {"esito": False,
                "perche": ("⛔ nessun fotogramma porta TUTT'E DUE le marche "
                           "leggibili: il controllo non ha girato.  ⚠ Non e' "
                           "«sono sempre dello stesso fotogramma»")}
    buoni = sum(1 for x in f if x["stesso_fotogramma"])
    quota = buoni / float(len(f))
    return {"esito": quota >= 0.98, "quota": round(quota, 4),
            "n": len(f), "buoni": buoni,
            "perche": ("%d marche appaiate su %d sono dello stesso fotogramma "
                       "(%.1f %%).  ⛔ Un campione a cavallo di due disegni "
                       "darebbe un ritardo plausibile e falso"
                       % (buoni, len(f), 100 * quota))}


def q3_eco_trova_quel_che_c_e(verbale):
    f = verbale.get("fotogrammi") or []
    if not f:
        return {"esito": False, "perche": "⛔ zero fotogrammi: 0 su 0"}
    letti = sum(1 for x in f if x.get("eco") is not None)
    quota = letti / float(len(f))
    return {"esito": quota >= 0.60, "quota": round(quota, 4),
            "n": len(f), "letti": letti,
            "perche": ("%d eco letti su %d fotogrammi dipinti (%.1f %%)"
                       % (letti, len(f), 100 * quota))}


# ⛔ IL CONTROLLO NEGATIVO SI CALCOLA UNA VOLTA SOLA, e la ragione e' di
#    misura e non di velocita': il rumore non dipende dal giro, e ricalcolarlo
#    a ogni giudizio darebbe **numeri diversi sotto la stessa etichetta**
#    (`CODER.md` §3.9).  ⇒ Si calcola qui, si conserva col suo denominatore, e
#    ogni Q4 legge lo stesso.
_RUMORE = {"falsi": None, "quante": 0}


def rumore_certificato(quante=3000, seme=11):
    """⭐ «Questo rilevatore sa dire di NO?» — `CODER.md` §3.10.

    ⛔ Il calcolo del falso positivo (≈ 1 / 670 000 per posizione provata) sta
       scritto in `03-marca.py`; qui NON ci si fida, si prova.
    """
    if _RUMORE["falsi"] is not None and _RUMORE["quante"] >= quante:
        return _RUMORE
    m17 = b17()
    r = random.Random(seme)
    sonde = [[r.random() * 255.0 for _ in range(144)] for _ in range(quante)]
    _RUMORE["falsi"] = sum(1 for s in sonde if m17.leggi_celle(s).get("c_e"))
    _RUMORE["quante"] = quante
    return _RUMORE


def q4_eco_discrimina(verbale, rumore=None):
    """⛔ Il controllo caduto in v1: un rilevatore che dice sempre si' misura
    zero ed e' felice a torto.  ⇒ TRE setacci."""
    f = verbale.get("fotogrammi") or []
    valori = [x["eco"] for x in f if x.get("eco") is not None]
    if len(valori) < 10:
        return {"esito": False,
                "perche": "⛔ %d eco letti: troppo pochi per dire se discrimina"
                          % len(valori)}
    distinti = len(set(valori))
    # 1. l'eco CAMBIA
    cambia = distinti >= max(5, 0.2 * len(valori))
    # 2. sul rumore NON trova niente
    falsi = rumore["falsi"] if rumore else None
    # 3. i valori sono PUNTATORI, non un tipo a caso
    tipi = {}
    for x in f:
        el = x.get("eco_letto") or {}
        if el.get("tipo") is not None:
            tipi[el["tipo"]] = tipi.get(el["tipo"], 0) + 1
    esito = bool(cambia) and (falsi in (None, 0))
    return {"esito": esito, "distinti": distinti, "n": len(valori),
            "falsi_sul_rumore": falsi, "tipi": tipi,
            "perche": ("%d valori distinti su %d eco letti%s.  ⛔ Se l'eco "
                       "dicesse sempre la stessa cosa, non starebbe "
                       "discriminando: sarebbe un rilevatore che dice sempre si'"
                       % (distinti, len(valori),
                          "" if falsi is None
                          else "; %d falsi su %d sonde di rumore"
                               % (falsi, rumore["quante"])))}


def q5_coordinate_non_trasformate(campioni, verbale):
    """⭐ `RCP.md` §7.3 — *«il server NON DEVE applicare nessuna trasformazione
    alle coordinate ricevute»* — smette di essere una riga da credere."""
    if not campioni:
        return {"esito": False, "perche": "⛔ zero campioni: 0 su 0"}
    # L'accoppiamento e' PER COORDINATE, quindi l'esattezza e' garantita per
    # costruzione sui campioni buoni.  ⛔ Il numero che conta e' quanti eco NON
    # hanno trovato il loro evento: se il server trasformasse, sarebbero quasi
    # tutti.
    c = verbale.get("conti_accoppiamento") or {}
    senza = c.get("senza_evento", 0)
    tot = senza + c.get("buoni", 0)
    quota = (c.get("buoni", 0) / float(tot)) if tot else 0.0
    return {"esito": quota >= 0.80, "quota": round(quota, 4),
            "buoni": c.get("buoni", 0), "senza_evento": senza,
            "perche": ("%d eco su %d hanno ritrovato ESATTAMENTE le coordinate "
                       "spedite (%.1f %%).  ⛔ Se il server le trasformasse, "
                       "quasi nessuno le ritroverebbe: e' §7.3 misurata invece "
                       "che creduta" % (c.get("buoni", 0), tot, 100 * quota))}


def q6_tre_unita(riassunto):
    """⭐⭐ Le tre unita' si consegnano TUTT'E TRE, e nessuna da sola."""
    manca = [k for k in ("ritardo_ms", "distacco_px", "distacco_barre")
             if riassunto.get(k) is None]
    return {"esito": not manca, "manca": manca,
            "perche": ("tutte e tre le unita' ci sono: %.1f ms · %.0f px · "
                       "%.2f barre del titolo"
                       % (riassunto.get("ritardo_ms") or 0,
                          riassunto.get("distacco_px") or 0,
                          riassunto.get("distacco_barre") or 0)
                       if not manca else
                       "⛔ mancano: %s.  `fasi/08-l-anello.md` §2.2 punto 4 "
                       "pretende tutt'e tre: i pixel si confrontano solo a "
                       "schermo uguale, le frazioni di barra no" % ", ".join(manca))}


def q7_q8_p1(giri, tolleranza_ms=6.0, tolleranza_px=0.30):
    """⛔ IL CONTROLLO DECISIVO, e sono DUE in uno.

    Si innesta un ritardo noto di N ms.  ⇒
      Q7  la mediana del RITARDO deve salire di N;
      Q8  la mediana del DISTACCO deve salire di `v × N` pixel.

    ⭐ E il perche' i due vadano insieme: se il banco calcolasse il distacco
      dividendo il ritardo per una costante, Q8 passerebbe **per costruzione**.
      Qui il distacco viene dai PIXEL (l'eco) e il ritardo dai TEMPI: sono due
      letture, e l'innesto le muove tutt'e due nel rapporto giusto solo se
      tutt'e due sono vere.
    """
    base = [g for g in giri if g.get("ritardo_innestato_ms") == 0]
    if not base:
        return {"esito": False,
                "perche": "⛔ manca il giro a innesto 0: senza base non si puo' "
                          "dire «e' salita»"}
    b = base[0]
    if not (b.get("ritardo") or {}).get("n"):
        return {"esito": False,
                "perche": "⛔ il giro a innesto 0 non ha NESSUN campione: non e' "
                          "«non e' salita», e' «non ho misurato»"}
    m0 = b["ritardo"]["mediana"]
    d0 = b["distacco"]["mediana"]
    v0 = b.get("velocita_mediana_px_s") or SCENA_UTENTE["mediana_px_s"]
    righe, buono = [], True
    for g in giri:
        n = g.get("ritardo_innestato_ms")
        if not n:
            continue
        r = g.get("ritardo") or {}
        d = g.get("distacco") or {}
        if not r.get("n"):
            righe.append({"innesto_ms": n, "rosso": True,
                          "perche": "⛔ zero campioni"})
            buono = False
            continue
        salita_t = r["mediana"] - m0
        salita_x = d["mediana"] - d0
        atteso_x = v0 * n / 1000.0
        ok_t = abs(salita_t - n) <= tolleranza_ms
        ok_x = (abs(salita_x - atteso_x) <= max(20.0, tolleranza_px * atteso_x))
        if not (ok_t and ok_x):
            buono = False
        righe.append({"innesto_ms": n,
                      "salita_tempo_ms": round(salita_t, 2), "atteso_ms": n,
                      "salita_distacco_px": round(salita_x, 1),
                      "atteso_px": round(atteso_x, 1),
                      "q7": ok_t, "q8": ok_x,
                      "rosso": not (ok_t and ok_x)})
    if not righe:
        return {"esito": False,
                "perche": ("⛔ nessun giro con un ritardo innestato: il banco "
                           "non e' TARATO.  ⚠ Un metro non tarato da' numeri, "
                           "non misure (`LEZIONI.md` §1.14)")}
    return {"esito": buono, "righe": righe, "base_ms": round(m0, 2),
            "base_px": round(d0, 1),
            "perche": ("innesto ritrovato in %d giri su %d, nel tempo E nei "
                       "pixel" % (sum(1 for r in righe if not r["rosso"]),
                                  len(righe)))}


def q9_rete(sep):
    return {"esito": bool(sep.get("c_e")),
            "perche": (sep.get("nota") if sep.get("c_e") else sep.get("perche"))}


def q10_buchi(b):
    if not b.get("c_e"):
        return {"esito": False, "perche": b.get("perche")}
    sconosciuti = sum(1 for x in b["buchi"] if x["chi"].startswith("[?]"))
    return {"esito": True, "quanti": b["quanti"], "sconosciuti": sconosciuti,
            "perche": ("%d buchi in %.1f s (uno ogni %s s) — l'utente ne ha 6 "
                       "in 17,5 s.  ⛔ %d restano `[?]`, e restano `[?]`: "
                       "chiamarli «nostri» curerebbe una cosa che non c'e'"
                       % (b["quanti"], b["durata_s"],
                          b["ogni_s"] if b["ogni_s"] else "—", sconosciuti))}


def q11_locale(controllo, passo_ms=8.0):
    """⭐⭐ Il termine di paragone locale.  ⛔ Se il banco non trova ~0 su una
    traccia a ritardo zero, IL BANCO E' ROTTO.

    ⛔⛔ E QUI VA DETTO CHE COSA «~0» VUOL DIRE, perche' la prima stesura di
       questo controllo pretendeva **0,0 ms** e si accusava da sola.

       `[M]` Su una traccia a ritardo zero il banco trova **4,0 ms** e **0 px**,
       e i due numeri non dicono la stessa cosa:

       · **0 px e' esatto, e non e' un'approssimazione**: la finestra mostra
         *proprio* l'ultima posizione che la mano ha toccato.  ⇒ La grandezza
         che l'utente giudica e' zero, ed e' quel che «locale» significa;
       · **i 4 ms sono la GRANA DELLA MANO, non un ritardo**: la mano manda un
         evento ogni `passo_ms` (8 ms = 125 Hz, il ritmo di un mouse USB vero)
         e i fotogrammi cadono dove capita in mezzo.  ⇒ In media mezzo passo.
         ⛔ **Nemmeno un anello perfetto potrebbe scendere sotto**, e pretendere
         zero vorrebbe dire chiedere allo strumento di mentire.

    ⇒ La soglia e' **un passo della mano** sul tempo e **pochi pixel** sullo
      spazio, e sta scritto qui invece che in un numero nudo.
    """
    if not controllo.get("c_e"):
        return {"esito": False, "perche": controllo.get("perche")}
    ms = controllo["ritardo_ms"]
    px = controllo["distacco_px"]
    buono = (0.0 <= ms <= passo_ms + 0.5) and px <= 5.0
    return {"esito": buono, "ritardo_ms": ms, "distacco_px": px,
            "soglia_ms": passo_ms, "soglia_px": 5.0,
            "perche": ("su una traccia in cui la finestra insegue la mano SENZA "
                       "ritardo il banco trova %.2f ms e %.0f px (soglie: ≤ %.0f "
                       "ms — un passo della mano — e ≤ 5 px).  %s"
                       % (ms, px, passo_ms,
                          "⭐ E' il controllo positivo: lo strumento sa "
                          "riconoscere il locale, e i %.1f ms residui sono la "
                          "grana della mano, non un ritardo." % ms
                          if buono else
                          "⛔ Dovrebbe trovare ~0: il banco e' ROTTO, e nessun "
                          "numero che produce vale niente."))}


def q12_costo_del_banco(verbale):
    c = verbale.get("costo_lettura_us") or []
    if not c:
        return {"esito": False,
                "perche": ("⛔ il costo della lettura dei pixel NON e' stato "
                           "misurato: e' un errore sistematico dentro OGNI "
                           "numero di questo banco, e non dichiararlo e' un "
                           "difetto del banco")}
    d = dist(c, 0.001)
    return {"esito": True, "distribuzione": d,
            "perche": ("la lettura delle due marche costa %.2f ms mediani "
                       "(p95 %.2f) e sta DENTRO il tratto disegno→lettura: si "
                       "dichiara, non si nasconde" % (d["mediana"], d["p95"]))}


def q13_unita_celle(verbale):
    """⛔ Il difetto del 13 agosto 2026: `_celle()` da' 0-1, `getImageData` da'
    0-255, e la certificazione era VERDE perche' le passava `_celle()`."""
    f = [x for x in verbale.get("fotogrammi") or [] if x.get("unita_ok") is not None]
    if not f:
        return {"esito": False,
                "perche": "⛔ nessuna cella da controllare: 0 su 0"}
    cattivi = [x for x in f if x["unita_ok"] is False]
    return {"esito": not cattivi, "n": len(f), "cattivi": len(cattivi),
            "perche": ("%d letture su %d nell'unita' dichiarata (0-255)%s"
                       % (len(f) - len(cattivi), len(f),
                          "" if not cattivi
                          else " — ⛔ %s" % cattivi[0]["unita_perche"]))}


# ═══════════════════════════════════════════════════════════════════════════
# §10  IL RIASSUNTO — ⛔ le tre unita' escono INSIEME o non escono
# ═══════════════════════════════════════════════════════════════════════════
def riassumi(campioni, verbale):
    if not campioni:
        return {"n": 0}
    r = [c["ritardo_ms"] for c in campioni]
    p = [c["distacco_px"] for c in campioni]
    ba = [c["distacco_barre"] for c in campioni if c["distacco_barre"] is not None]
    v = [c["velocita_px_s"] for c in campioni if c["velocita_px_s"] is not None]
    com = [c["comodo_ms"] for c in campioni if c["comodo_ms"] is not None]
    t1a = [c["tratto_1a_ms"] for c in campioni if c["tratto_1a_ms"] is not None]
    d = {"n": len(campioni),
         "ritardo_ms": statistics.median(r),
         "ritardo": dist(r),
         "distacco_px": statistics.median(p),
         "distacco": dist(p),
         "distacco_barre": statistics.median(ba) if ba else None,
         "barre": dist(ba) if ba else {"n": 0},
         "velocita_mediana_px_s": statistics.median(v) if v else None,
         "comodo_ms": statistics.median(com) if com else None,
         "comodo": dist(com) if com else {"n": 0},
         "tratto_1a_ms": statistics.median(t1a) if t1a else None}
    # ⭐ Il disaccordo fra i due confini E' IL REGALO: e' quanto il numero
    #   comodo si regala.
    if d["comodo_ms"] is not None:
        d["regalo_del_comodo_ms"] = round(d["ritardo_ms"] - d["comodo_ms"], 2)
    return d


def stampa_riassunto(d, verbale, sep, mano="pagina"):
    if not d.get("n"):
        return
    barra = verbale.get("barra_px") or SCENA_UTENTE["barra_px"]
    log("⭐⭐ IL NUMERO, NELLE TRE UNITA' — e nessuna esce da sola")
    inf("n = %d campioni" % d["n"])
    inf("  ⏱  RITARDO (confine SCOMODO, il disegno finito)  %s"
        % con_pezzi_ciechi(d["ritardo_ms"], mano))
    if d.get("comodo_ms") is not None:
        inf("  ⏱  ritardo al confine COMODO (il fotogramma ARRIVATO, `RCP.md` "
            "§6.2)  %.1f ms  ⇒ ⭐ il comodo si regala %.1f ms"
            % (d["comodo_ms"], d.get("regalo_del_comodo_ms") or 0.0))
    inf("  📏  DISTACCO  %.0f px mediani (p95 %.0f, max %.0f)"
        % (d["distacco_px"], d["distacco"]["p95"], d["distacco"]["max"]))
    inf("  ⭐  DISTACCO IN BARRE DEL TITOLO  %.2f barre (barra = %d px) — "
        "l'utente riferisce **mezza barra**"
        % (d["distacco_barre"] or 0.0, barra))
    if d.get("velocita_mediana_px_s"):
        inf("  🖐  la mano correva a %.0f px/s (l'utente: mediana 3 400)"
            % d["velocita_mediana_px_s"])
    if sep.get("c_e"):
        inf("  🌐  di cui RETE %.1f ms (%.1f %%) ⇒ ⭐ IL PEZZO NOSTRO e' "
            "%.1f ms" % (sep["rete_ms"], 100 * (sep["quota_rete"] or 0),
                         sep["nostro_ms"]))
    else:
        ko("  🌐  la rete NON e' separata: %s" % sep.get("perche"))


# ═══════════════════════════════════════════════════════════════════════════
# §11  LA CERTIFICAZIONE — ⛔ ogni verde ha un guasto che lo DEVE far rosso
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `CODER.md` §3.3 e `LEZIONI.md` §1.20: la misura e' buona e il giudizio e'
#    staccato da lei.  ⇒ Qui si costruisce un verbale SANO, si controlla che il
#    banco lo chiami verde, e poi si innesta un guasto per volta pretendendo il
#    rosso.  Un banco che non sa come fallire non vale.


# ⛔ Le durate dei giri sintetici: si dichiarano, perche' un giro piu' corto e'
#    meno campioni, e «pochi campioni» e' una proprieta' della prova che chi la
#    legge deve poter vedere senza cercarla nel codice.
SEC_CERT = 10.0        # il sano e la taratura: ~600 fotogrammi a 60/s
SEC_GUASTO = 6.0       # i guasti: basta che il controllo scatti
SEC_LOCALE = 5.0       # il controllo positivo del locale


def _finta_marca(disegno, istante_us, giro):
    """Una marca sintetica, DIPINTA col pittore vero e riletta col lettore vero.

    ⛔ Non si fabbricano celle a mano: si passa dal pittore di `03-marca.py`,
       cosi' la certificazione mette alla prova il lettore CERTIFICATO e non una
       finzione che gli somiglia.
    """
    m = carica("marca", os.path.join(QUI, "03-marca.py"))
    np = m.np_o_muori("08-b67: la sintesi della marca")
    geo = m.GEOMETRIA
    l = geo.margine + geo.colonne * geo.cella + 16
    a = geo.margine + geo.righe * geo.cella + 16
    img = np.zeros((a, l, 3), dtype=np.uint8)
    m.dipingi_marca(img, disegno, istante_us, giro, geo)
    y = (0.2126 * img[:, :, 0] + 0.7152 * img[:, :, 1]
         + 0.0722 * img[:, :, 2]) / 255.0
    return [float(x) * 255.0 for x in m._celle(y, geo, 0, 0)]


def verbale_sintetico(ritardo_ms=140.0, secondi=12.0, passo_ms=8.0,
                      distacco_extra_px=0.0, seme=1, tela=(2560, 1440),
                      quanti_fotogrammi=None, base_px_s=None):
    """⭐ Un verbale FINTO ma costruito con i pezzi veri: la traiettoria e' quella
    che il banco userebbe, le marche le dipinge il pittore vero.

    ⛔ Il ritardo si innesta **nella scena**: la finestra mostra la posizione
       che la mano aveva `ritardo_ms` fa.  ⇒ E' il fenomeno, non il numero.
    """
    punti = traiettoria(secondi, passo_ms, tela, base_px_s=base_px_s, seme=seme)
    eventi = []
    for i, (t, x, y) in enumerate(punti):
        eventi.append({"t_manda": t + 0.4, "tipo": 0x0101, "id": i + 1,
                       "x": x, "y": y, "istante_us": int(t * 1000),
                       "t0": t, "t_udito": t + 0.2, "fidato": False})
    # I fotogrammi: uno ogni ~16,7 ms (60 al secondo), ciascuno mostra la
    # posizione che la mano aveva `ritardo_ms` prima.
    tempi = [e["t0"] for e in eventi]
    fotogrammi, giri = [], []
    passo_f = 1000.0 / 60.0
    t = ritardo_ms + 5.0
    n = 0
    while t < secondi * 1000.0:
        k = _ultimo_prima(tempi, t - ritardo_ms)
        if k is not None:
            e = eventi[k]
            x, y = e["x"], e["y"]
            if distacco_extra_px:
                # ⛔ Lo spostamento si fa LUNGO LA TRAIETTORIA, indietro: uno
                #    spostamento fuori dal cammino non corrisponderebbe a
                #    nessun evento e il banco lo butterebbe — cioe' il guasto
                #    non metterebbe alla prova quel che deve.
                j = k
                perc = 0.0
                while j > 0 and perc < distacco_extra_px:
                    perc += math.hypot(eventi[j]["x"] - eventi[j - 1]["x"],
                                       eventi[j]["y"] - eventi[j - 1]["y"])
                    j -= 1
                x, y = eventi[j]["x"], eventi[j]["y"]
                e = eventi[j]
            n += 1
            eco = b30().eco_puntatore(x, y)
            fotogrammi.append({
                "t_dip": t, "t_let": t + 1.2, "strada": "bm",
                "celle": _finta_marca(n, int(t * 1000), 0x11111111),
                "celle_eco": _finta_marca(eco, int((t - ritardo_ms) * 1000),
                                          0x22222222),
                "visto": True, "visto_eco": True, "consegnati": n})
            giri.append({"id": e["id"], "t": t - 25.0})
        t += passo_f
        if quanti_fotogrammi and n >= quanti_fotogrammi:
            break
    return {"giro": "sintetico", "barra_px": SCENA_UTENTE["barra_px"],
            "tela": list(tela), "mano": "pagina",
            "fotogrammi": fotogrammi, "eventi": eventi, "giri": giri,
            "costo_lettura_us": [1400.0 + (i % 300) for i in range(600)],
            "conti": {"dipinti": len(fotogrammi), "mandati": len(eventi)},
            "sintetico": True}


def _analizza(verbale, rete=None, controllo_locale=None, sonde=None):
    """⛔ UNA sola strada dall'analisi al verdetto: la certificazione e la misura
    vera passano di qui tutt'e due, o si certificherebbe un codice diverso da
    quello che misura."""
    arricchisci(verbale["fotogrammi"])
    campioni = accoppia(verbale)
    d = riassumi(campioni, verbale)
    sep = separa_la_rete(d.get("ritardo_ms"), rete)
    buchi = trova_buchi(campioni, verbale["fotogrammi"], rete)
    return {"campioni": campioni, "riassunto": d, "rete": sep, "buchi": buchi,
            "verbale": verbale}


def _controllo_locale_sintetico():
    """⭐⭐ Il termine di paragone locale, e gira SEMPRE."""
    v = verbale_sintetico(ritardo_ms=0.0, secondi=SEC_LOCALE)
    a = _analizza(v)
    d = a["riassunto"]
    if not d.get("n"):
        return {"c_e": False,
                "perche": ("⛔ il controllo locale non ha prodotto NESSUN "
                           "campione: il banco non sa nemmeno leggere una "
                           "traccia che si e' costruito da se'")}
    return {"c_e": True, "ritardo_ms": round(d["ritardo_ms"], 3),
            "distacco_px": round(d["distacco_px"], 1), "n": d["n"]}


# ── I GUASTI INNESTATI ─────────────────────────────────────────────────────
#
# ⛔ Ogni guasto e' una funzione che PRENDE un verbale sano e lo guasta, piu'
#    l'elenco dei controlli che DEVONO diventare rossi.  ⚠ Se un guasto non fa
#    diventare rosso nessuno, il controllo che avrebbe dovuto prenderlo NON
#    ESISTE, e il banco lo dice invece di tacere.

def _g_eco_fermo(v):
    """La scena riceve gli input ma non aggiorna l'eco: la finestra e' ferma."""
    e = b30().eco_puntatore(400, 400)
    for f in v["fotogrammi"]:
        f["celle_eco"] = _finta_marca(e, 1000, 0x22222222)
    return v


def _g_eco_illeggibile(v):
    """I pixel della seconda marca sono rumore: nessun eco si legge."""
    r = random.Random(7)
    for f in v["fotogrammi"]:
        f["celle_eco"] = [r.random() * 255.0 for _ in range(144)]
    return v


def _g_niente_da_giudicare(v):
    """⛔ Zero fotogrammi con eco E zero coppie ⇒ uscita 3, non 0."""
    for f in v["fotogrammi"]:
        f["celle_eco"] = None
        f["celle"] = None
    return v


def _g_mano_lenta(v):
    """⛔ Un trascinamento lento non mostra niente: Q1 deve rifiutarlo."""
    return verbale_sintetico(ritardo_ms=140.0, secondi=SEC_GUASTO, base_px_s=300.0)


def _g_marche_di_due_fotogrammi(v):
    """La marca 2 porta un istante POSTERIORE a quello della marca 1: le due
    letture sono di due passate diverse."""
    for f in v["fotogrammi"]:
        f["celle"] = _finta_marca(1, 1000, 0x11111111)
    return v


def _g_unita_zero_uno(v):
    """⛔ Il difetto del 13 agosto 2026: le celle in 0-1 invece che in 0-255."""
    for f in v["fotogrammi"]:
        if f.get("celle"):
            f["celle"] = [c / 255.0 for c in f["celle"]]
    return v


def _g_rete_non_misurata(v):
    """⛔ La rete non e' stata misurata: il pezzo nostro NON si dichiara."""
    return v          # il guasto sta nel non passare `rete` a `_analizza`


def _g_ritardo_negativo(v):
    """I fotogrammi sono dipinti PRIMA degli eventi che mostrano: impossibile."""
    for f in v["fotogrammi"]:
        f["t_dip"] -= 500.0
    return v


def _g_coordinate_trasformate(v):
    """⛔ Il server applica una trasformazione alle coordinate (§7.3 violata):
    nessun eco ritrova il suo evento."""
    b = b30()
    for f in v["fotogrammi"]:
        # si rilegge l'eco dal pittore: si sposta di 7 px, che non e' un punto
        # della traiettoria
        f["celle_eco"] = _finta_marca(b.eco_puntatore(9000, 9000), 1000,
                                      0x22222222)
    return v


def _g_traiettoria_ambigua(v):
    """La mano ripassa sugli stessi pixel: l'eco non individua piu' UN evento.
    ⛔ Il banco deve RIFIUTARE i campioni ambigui, non sceglierne uno."""
    for e in v["eventi"]:
        e["x"], e["y"] = 500, 500
    return v


def _g_buco_innestato(v):
    """⭐ Si toglie mezzo secondo di fotogrammi nel mezzo: il rilevatore dei
    buchi DEVE trovarne almeno uno."""
    f = v["fotogrammi"]
    if len(f) < 40:
        return v
    k = len(f) // 2
    quanti = max(6, int(0.30 * 60))     # ~300 ms a 60/s
    v["fotogrammi"] = f[:k] + f[k + quanti:]
    return v


def _g_costo_non_misurato(v):
    """⛔ Il costo del banco non e' misurato: e' un errore sistematico dentro
    ogni numero, e tacerlo e' un difetto del banco."""
    v["costo_lettura_us"] = []
    return v


def _g_confine_comodo_solo(v):
    """⛔ Il banco consegna solo i millisecondi e non i pixel: Q6 lo prende."""
    return v          # il guasto si innesta nel riassunto, vedi `certifica`


GUASTI = [
    ("G1  l'eco e' FERMO (la finestra non insegue)", _g_eco_fermo, ["Q4"]),
    ("G2  l'eco e' ILLEGGIBILE (rumore nei pixel)", _g_eco_illeggibile,
     ["Q0", "Q3"]),
    ("G3  ⛔ NIENTE da giudicare (zero marche)", _g_niente_da_giudicare,
     ["Q0", "Q3"]),
    ("G4  la mano e' LENTA (300 px/s invece di 3 400)", _g_mano_lenta, ["Q1"]),
    ("G5  le due marche sono di DUE fotogrammi", _g_marche_di_due_fotogrammi,
     ["Q2"]),
    ("G6  le celle sono in 0-1 invece che in 0-255", _g_unita_zero_uno,
     ["Q0", "Q3", "Q13"]),
    ("G7  ⛔ la RETE non e' misurata in questo giro", _g_rete_non_misurata,
     ["Q9"]),
    ("G8  il ritardo e' NEGATIVO (fotogramma prima dell'evento)",
     _g_ritardo_negativo, ["Q0"]),
    ("G9  ⛔ il server TRASFORMA le coordinate (§7.3 violata)",
     _g_coordinate_trasformate, ["Q0", "Q5"]),
    ("G10 la traiettoria RIPASSA sugli stessi pixel (accoppiamento ambiguo)",
     _g_traiettoria_ambigua, ["Q0", "Q5"]),
    ("G11 ⭐ un BUCO di 300 ms innestato nel mezzo", _g_buco_innestato,
     ["Q10+"]),
    ("G12 il costo del banco NON e' misurato", _g_costo_non_misurato, ["Q12"]),
]


def _giudica(a, rete_passata, controllo_locale, rumore, giri_p1=None,
             solo_ms=False):
    """⛔ I controlli, in un posto solo.  Ritorna `{nome: {esito, perche}}`."""
    v = a["verbale"]
    c = a["campioni"]
    d = dict(a["riassunto"])
    if solo_ms:
        d["distacco_px"] = None
        d["distacco_barre"] = None
    q = {}
    q["Q0"] = q0_c_e_qualcosa(v, c)
    q["Q1"] = q1_la_scena_e_quella_dell_utente(v)
    q["Q2"] = q2_due_marche_stesso_fotogramma(v)
    q["Q3"] = q3_eco_trova_quel_che_c_e(v)
    q["Q4"] = q4_eco_discrimina(v, rumore)
    q["Q5"] = q5_coordinate_non_trasformate(c, v)
    q["Q6"] = q6_tre_unita(d)
    if giri_p1 is not None:
        q["Q7/Q8"] = q7_q8_p1(giri_p1)
    q["Q9"] = q9_rete(a["rete"])
    q["Q10"] = q10_buchi(a["buchi"])
    q["Q11"] = q11_locale(controllo_locale)
    q["Q12"] = q12_costo_del_banco(v)
    q["Q13"] = q13_unita_celle(v)
    return q


def certifica():
    """⛔ Tre giri: il sano, i guasti, e il conto onesto di quanti ne accusa."""
    log("⭐ LA CERTIFICAZIONE — gira QUI, senza rete e senza server")
    inf("⛔ `CODER.md` §3.3: il banco si certifica PRIMA di essere puntato")
    inf("   sull'incognita, o un rosso e' ambiguo fra il prodotto e lo strumento.")
    rossi = 0

    # ── 0. il lettore certificato, sui suoi tre setacci ────────────────────
    log("0 · IL LETTORE DELLA MARCA — ⛔ il controllo NEGATIVO prima di tutto")
    m17 = b17()
    rumore = rumore_certificato(3000)
    falsi = rumore["falsi"]
    if falsi == 0:
        ok("3 000 sonde di rumore attraverso il lettore certificato → 0 falsi "
           "su 3 000")
    else:
        ko("⛔ %d falsi positivi su 3 000: il lettore dice si' a caso" % falsi)
        rossi += 1
    # e il positivo: una marca dipinta e riletta
    prova = m17.leggi_celle(_finta_marca(41, 987654321, 0xABCDEF01))
    if prova.get("c_e") and prova["disegno"] == 41 and prova["istante_us"] == 987654321:
        ok("una marca DIPINTA dal pittore vero e riletta dal lettore vero torna "
           "identica (disegno 41, istante 987 654 321)")
    else:
        ko("⛔ il giro pittore→lettore NON torna: %s" % prova)
        rossi += 1

    # ── 1. il termine di paragone LOCALE ──────────────────────────────────
    log("1 · ⭐⭐ IL TERMINE DI PARAGONE LOCALE — il controllo positivo")
    loc = _controllo_locale_sintetico()
    j = q11_locale(loc)
    (ok if j["esito"] else ko)(j["perche"])
    if not j["esito"]:
        rossi += 1

    # ── 2. il giro SANO ───────────────────────────────────────────────────
    log("2 · IL GIRO SANO — il banco lo deve chiamare verde")
    v = verbale_sintetico(ritardo_ms=140.0, secondi=SEC_CERT)
    rete_finta = {"c_e": True, "n": 400, "mediana": 2.85, "p90": 3.94,
                  "p95": 5.2, "p99": 33.60, "max": 37.60, "min": 1.49,
                  "campioni": [], "quota_sopra_15ms": 0.032}
    a = _analizza(v, rete=rete_finta)
    q = _giudica(a, rete_finta, loc, rumore)
    stampa_riassunto(a["riassunto"], v, a["rete"])
    inf("")
    sani_rossi = []
    for nome in sorted(q, key=_ordine_q):
        e = q[nome]["esito"]
        if e is True:
            ok("%-6s %s" % (nome, q[nome]["perche"]))
        elif e is None:
            dub("%-6s %s" % (nome, q[nome]["perche"]))
            sani_rossi.append(nome)
        else:
            ko("%-6s %s" % (nome, q[nome]["perche"]))
            sani_rossi.append(nome)
    if sani_rossi:
        ko("⛔ sul giro SANO sono rossi: %s — il banco accusa se stesso"
           % ", ".join(sani_rossi))
        rossi += 1
    else:
        ok("⭐ sul giro sano tutti i controlli sono verdi")

    # ── 3. LA TARATURA — Q7 e Q8 insieme ──────────────────────────────────
    log("3 · ⛔ LA TARATURA (Q7/Q8): si innesta un ritardo NOTO e devono salire")
    inf("    tutt'e due le unita', ciascuna della sua quantita'.")
    giri_p1 = []
    for n in (0, 30, 60):
        vv = verbale_sintetico(ritardo_ms=140.0 + n, secondi=SEC_CERT)
        aa = _analizza(vv, rete=rete_finta)
        dd = aa["riassunto"]
        giri_p1.append({"ritardo_innestato_ms": n,
                        "ritardo": dd.get("ritardo", {"n": 0}),
                        "distacco": dd.get("distacco", {"n": 0}),
                        "velocita_mediana_px_s": dd.get("velocita_mediana_px_s")})
    p1 = q7_q8_p1(giri_p1)
    for riga in p1.get("righe", []):
        (ok if not riga["rosso"] else ko)(
            "innesto %+d ms → il TEMPO sale di %s ms (atteso %d) e il DISTACCO "
            "di %s px (atteso %s)"
            % (riga["innesto_ms"], riga.get("salita_tempo_ms"),
               riga["innesto_ms"], riga.get("salita_distacco_px"),
               riga.get("atteso_px")))
    if p1["esito"]:
        ok("⭐⭐ le DUE unita' si muovono insieme, nel rapporto della velocita': "
           "sono due LETTURE, non una divisa per una costante")
    else:
        ko("⛔ la taratura NON torna: %s" % p1["perche"])
        rossi += 1

    # ── 4. I GUASTI INNESTATI ─────────────────────────────────────────────
    log("4 · ⭐⭐ I GUASTI INNESTATI — ognuno DEVE far diventare rosso il banco")
    inf("⛔ `LEZIONI.md` §1.20: la misura e' buona e il giudizio e' staccato da")
    inf("   lei.  Un banco che non sa come fallire non vale.")
    accusati, totale = 0, 0
    for nome, guasto, attesi in GUASTI:
        totale += 1
        vv = guasto(verbale_sintetico(ritardo_ms=140.0, secondi=SEC_GUASTO))
        rete_qui = None if guasto is _g_rete_non_misurata else rete_finta
        solo_ms = guasto is _g_confine_comodo_solo
        aa = _analizza(vv, rete=rete_qui)
        # Q10+ e' il caso speciale: il guasto non deve far rosso un controllo,
        # deve farsi TROVARE dal rilevatore dei buchi.
        if "Q10+" in attesi:
            b = aa["buchi"]
            trovato = bool(b.get("c_e") and b.get("quanti", 0) >= 1)
            if trovato:
                ok("%-62s ⇒ ⭐ il rilevatore ha trovato %d buchi (chi: %s)"
                   % (nome, b["quanti"], b["buchi"][0]["chi"][:48]))
                accusati += 1
            else:
                ko("%-62s ⇒ ⛔ NON trovato: il rilevatore dei buchi non serve"
                   % nome)
            continue
        qq = _giudica(aa, rete_qui, loc, rumore, solo_ms=solo_ms)
        rossi_qui = [k for k in qq if qq[k]["esito"] is not True]
        preso = [k for k in attesi if k in rossi_qui]
        if preso:
            ok("%-62s ⇒ rosso su %s" % (nome, ", ".join(sorted(preso, key=_ordine_q))))
            accusati += 1
        else:
            ko("%-62s ⇒ ⛔ NESSUN controllo l'ha preso (attesi: %s; rossi: %s)"
               % (nome, ", ".join(attesi), ", ".join(sorted(rossi_qui, key=_ordine_q)) or "nessuno"))
    # G13: il verbale senza i pixel — Q6 deve prenderlo
    totale += 1
    aa = _analizza(verbale_sintetico(ritardo_ms=140.0, secondi=SEC_GUASTO),
                   rete=rete_finta)
    qq = _giudica(aa, rete_finta, loc, rumore, solo_ms=True)
    if qq["Q6"]["esito"] is not True:
        ok("%-62s ⇒ rosso su Q6" % "G13 si consegnano SOLO i millisecondi")
        accusati += 1
    else:
        ko("%-62s ⇒ ⛔ NON preso: si potrebbe consegnare una sola unita'"
           % "G13 si consegnano SOLO i millisecondi")

    log("IL CONTO — ⛔ col denominatore accanto, sempre")
    if accusati == totale:
        ok("⭐⭐ %d guasti innestati su %d accusati: %d su %d"
           % (accusati, totale, accusati, totale))
    else:
        ko("⛔ %d guasti su %d accusati: %d NON hanno fatto diventare rosso "
           "niente" % (accusati, totale, totale - accusati))
        rossi += 1

    if rossi:
        ko("⛔ LA CERTIFICAZIONE NON PASSA: %d capitoli rossi" % rossi)
        return USCITA_NON_CONFORME
    ok("⭐ LA CERTIFICAZIONE PASSA — il banco sa misurare E sa fallire")
    return USCITA_CONFORME


def _ordine_q(nome):
    m = re.match(r"Q(\d+)", nome)
    return (int(m.group(1)) if m else 99, nome)


# ═══════════════════════════════════════════════════════════════════════════
# §12  IL FINTO — che cosa il banco DIRA' quando il prodotto arriva
# ═══════════════════════════════════════════════════════════════════════════
def finto():
    log("⭐ IL FINTO — la FORMA della misura, non la misura")
    inf("⛔ Nessuno di questi numeri e' `[M]`: sono costruiti su una traccia")
    inf("   sintetica col ritardo che la fase 4 aveva misurato (139,4 ms).")
    v = verbale_sintetico(ritardo_ms=139.4, secondi=14.0)
    rete = {"c_e": True, "n": 400, "mediana": 2.85, "p90": 3.94, "p95": 5.2,
            "p99": 33.60, "max": 37.60, "min": 1.49, "campioni": [],
            "quota_sopra_15ms": 0.032}
    a = _analizza(v, rete=rete)
    stampa_riassunto(a["riassunto"], v, a["rete"])
    d = a["riassunto"]
    log("⭐ E LA LETTURA CHE L'UTENTE PUO' FARE SENZA STRUMENTI")
    inf("l'utente riferisce **mezza barra del titolo** ⇒ 0,50 barre.")
    inf("questo finto darebbe %.2f barre." % (d["distacco_barre"] or 0))
    inf("⛔ Se il numero vero uscisse molto diverso dalla meta', la causa "
        "e' UNA delle due: o l'anello non e' quello che l'utente ha visto, o "
        "la velocita' a cui lui guarda non e' la mediana.")
    return USCITA_CONFORME


# ═══════════════════════════════════════════════════════════════════════════
# §13  LA MISURA VERA
# ═══════════════════════════════════════════════════════════════════════════
def batti(palco, testo):
    """⛔ «thisisunsafe» SI BATTE, non si aggira con un flag.

    ⭐ E' la scelta gia' presa da `02-pagina-misura-prova.py` e da
      `01-p5-lancia.sh`, con la ragione scritta li': `--ignore-certificate-errors`
      *«sarebbe il modo piu' rapido di far aprire la pagina e il modo piu'
      sicuro di non misurare piu' niente»* — toglierebbe dalla misura proprio
      la cosa che l'utente fa la prima volta.

    ⚠ E' l'unico pezzo che questo banco RICOPIA invece di importare, e si
      dichiara perche': il modulo che lo contiene (`02-pagina-misura-prova.py`)
      fa `argparse` a livello di modulo e importarlo lancerebbe un banco.
    """
    for ch in testo:
        for tipo in ("keyDown", "char", "keyUp"):
            p = {"type": tipo, "text": ch} if tipo == "char" else {"type": tipo}
            if tipo != "char":
                p["key"] = ch
            palco.chiama("Input.dispatchKeyEvent", **p)
        time.sleep(0.03)


def supera_l_avviso(palco, url):
    """⛔ Il certificato e' nostro e non e' firmato da nessuno: l'avviso c'e', ed
    e' ATTESO (`RCP.md` §4.1-bis).  ⇒ Si supera dalla stessa porta dell'utente e
    si VERIFICA che si sia superato, invece di presumerlo."""
    for _ in range(3):
        r = palco.valuta(
            "(function(){return document.title + '|' + "
            "(document.getElementById('modulo') ? 'modulo' : 'niente');})()",
            attendi=False) or ""
        if "modulo" in str(r):
            return True
        dub("⚠ c'e' l'interstiziale del certificato (titolo «%s»): batto "
            "«thisisunsafe», come farebbe l'utente" % str(r).split("|")[0][:40])
        batti(palco, "thisisunsafe")
        time.sleep(4.0)
        palco.chiama("Page.navigate", url=url)
        time.sleep(3.0)
    return False


def _ritira(palco):
    r = palco.valuta("window.__B67 ? JSON.stringify(window.__B67.prendi()) : null",
                     attendi=False)
    if not r:
        return None
    try:
        return json.loads(r)
    except Exception:                               # noqa: BLE001
        return None


def misura(a):
    m17 = b17()
    log("IL PALCO — Xvfb + Chrome sul PORTATILE, cioe' il client vero")
    inf("⛔ Il browser sta QUI e il server e' la' (%s:%d): la rete IN MEZZO e'"
        % (a.host, a.porta))
    inf("   quella vera, ed e' la ragione per cui `ping` corre nello stesso giro.")
    palco = m17.Palco(schermo=a.schermo, diagnosi=a.diagnosi,
                      finestra=(a.larghezza, a.altezza), lavoro=a.lavoro,
                      gpu=not a.senza_gpu)
    rete = Rete(a.host, a.intervallo_ping)
    verbale = {"giro": a.giro, "quando": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "host": a.host, "porta": a.porta, "utente": a.utente,
               "barra_px": a.barra, "mano": a.mano,
               "scena_utente": SCENA_UTENTE, "rete_nota": RETE_NOTA,
               "fotogrammi": [], "eventi": [], "giri": [],
               "costo_lettura_us": [], "sintetico": False}
    try:
        misurato = palco.accendi()
        verbale["palco"] = {"xvfb": misurato, "bandiere": palco.bandiere,
                            "schermo": a.schermo}
        ok("Xvfb %s e Chrome accesi" % misurato)
        c = palco.c
        # ⛔ Il prologo si mette PRIMA di navigare: e' l'unico momento in cui
        #    si puo' entrare davanti a ogni script della pagina.
        palco.chiama("Page.addScriptToEvaluateOnNewDocument", source=PROLOGO)
        url = "https://%s:%d/" % (a.host, a.porta)
        palco.chiama("Page.navigate", url=url)
        time.sleep(3.0)
        if not palco.valuta("!!window.__B67", attendi=False):
            ko("⛔ il PROLOGO non e' entrato: senza, non c'e' nessun `t0`")
            return USCITA_NON_CONFORME
        if not supera_l_avviso(palco, url):
            ko("⛔ l'avviso del certificato NON si e' superato: la pagina non "
               "e' mai stata caricata.  ⚠ Non e' «il prodotto non disegna»")
            return USCITA_NIENTE_DA_GIUDICARE
        if not palco.valuta("!!window.__B67", attendi=False):
            ko("⛔ il PROLOGO non e' entrato dopo il superamento dell'avviso")
            return USCITA_NON_CONFORME
        ok("pagina aperta e prologo dentro")

        # ── l'ingresso ────────────────────────────────────────────────────
        parola = ""
        if a.parola_file and os.path.exists(a.parola_file):
            with open(a.parola_file) as f:
                parola = f.read().strip()
        if not parola:
            ko("⛔ nessuna parola d'ordine (--parola-file): non entro")
            return USCITA_NON_CONFORME
        palco.valuta(
            "(function(){var u=document.getElementById('utente');"
            "var p=document.getElementById('parola');"
            "if(!u||!p) return 'no-modulo';"
            "u.value=%s; p.value=%s;"
            "var f=document.getElementById('modulo');"
            "if(f) f.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));"
            "return 'inviato';})()" % (json.dumps(a.utente), json.dumps(parola)),
            attendi=False)
        fine = time.time() + 60
        pronto = False
        while time.time() < fine:
            r = palco.valuta(
                "(window.REMOTIX && REMOTIX.schermo && "
                " REMOTIX.schermo.conti.dipinti) || 0", attendi=False)
            try:
                if int(r or 0) > 0:
                    pronto = True
                    break
            except Exception:                       # noqa: BLE001
                pass
            time.sleep(1.0)
        if not pronto:
            ko("⛔ la pagina non ha dipinto NESSUN fotogramma in 60 s: non e' "
               "«il ritardo e' grande», e' «non ho potuto guardare»")
            return USCITA_NIENTE_DA_GIUDICARE
        ok("la sessione e' aperta e la pagina dipinge")

        # ── la geometria della tela, letta e non dedotta ──────────────────
        g = palco.valuta(
            "(function(){var t=document.getElementById('schermo');"
            "var s=window.REMOTIX&&REMOTIX.schermo;if(!t||!s)return null;"
            "var r=t.getBoundingClientRect();"
            "return JSON.stringify({tela:[s.tela_l,s.tela_a],"
            "buffer:[t.width,t.height],"
            "vetro:[Math.round(r.left),Math.round(r.top),"
            "Math.round(r.width),Math.round(r.height)]});})()", attendi=False)
        geo = json.loads(g) if g else None
        if not geo or not geo["tela"][0]:
            ko("⛔ non so quanto e' grande la tela: senza, la mano non si puo' "
               "muovere alla velocita' dell'utente")
            return USCITA_NIENTE_DA_GIUDICARE
        verbale["geometria"] = geo
        tela = (geo["tela"][0], geo["tela"][1])
        vw, vh = geo["vetro"][2], geo["vetro"][3]
        ok("tela %dx%d · vetro %dx%d" % (tela[0], tela[1], vw, vh))
        # ⛔ La mano si muove in coordinate del VETRO, ma la velocita' che
        #    conta e' quella sulla TELA: e' li' che vive il distacco che
        #    l'utente vede.  ⇒ si genera in tela e si converte, e il FATTORE
        #    si dichiara.
        kx = vw / float(tela[0]) if tela[0] else 1.0
        ky = vh / float(tela[1]) if tela[1] else 1.0
        verbale["fattore_vetro"] = [round(kx, 4), round(ky, 4)]
        inf("il vetro e' %.3f× la tela: la mano si genera in TELA e si "
            "converte, o si misurerebbe la velocita' sbagliata" % kx)

        punti = traiettoria(a.secondi, a.passo_ms, tela, seme=a.seme)
        verbale["punti_previsti"] = len(punti)
        punti_vetro = [[t, round(x * kx, 2), round(y * ky, 2)]
                       for (t, x, y) in punti]

        # ── il `ping` parte PRIMA della mano e si ferma DOPO ──────────────
        if not rete.parti():
            dub("⚠ `ping` non e' partito: il pezzo nostro non si potra' "
                "dichiarare (Q9 sara' rosso, ed e' giusto cosi')")

        palco.valuta("window.__B67.prendi(), true", attendi=False)   # si svuota
        log("LA MANO — %d movimenti in %g s, alla velocita' dell'utente"
            % (len(punti), a.secondi))
        palco.valuta("window.__B67.parti(%s, %s)"
                     % (json.dumps(punti_vetro),
                        "true" if not a.senza_bottone else "false"),
                     attendi=False)
        t_fine = time.time() + a.secondi + 15
        while time.time() < t_fine:
            time.sleep(1.0)
            if palco.valuta("window.__B67.finita()", attendi=False):
                break
        time.sleep(1.0)
        r = _ritira(palco)
        verbale["rete"] = rete.ferma()
        if not r:
            ko("⛔ il ritiro non ha prodotto niente")
            return USCITA_NIENTE_DA_GIUDICARE
        verbale["fotogrammi"] = r.get("fotogrammi") or []
        verbale["eventi"] = r.get("eventi") or []
        verbale["giri"] = r.get("giri") or []
        verbale["costo_lettura_us"] = r.get("costo_lettura_us") or []
        verbale["conti"] = r.get("conti")
        verbale["grana_orologio_ms"] = r.get("grana")
        verbale["isolata"] = r.get("isolata")
        verbale["t_origine"] = r.get("t_origine")
        verbale["pagina"] = r.get("pagina")
        verbale["violazioni"] = r.get("violazioni")
    finally:
        try:
            palco.spegni()
        except Exception:                           # noqa: BLE001
            pass

    return verdetto(verbale)


def verdetto(verbale):
    rete = verbale.get("rete")
    a = _analizza(verbale, rete=rete)
    loc = _controllo_locale_sintetico()
    rumore = rumore_certificato(2000)
    q = _giudica(a, rete, loc, rumore)
    stampa_riassunto(a["riassunto"], verbale, a["rete"], verbale.get("mano", "pagina"))

    log("I BUCHI — ⛔ nostri o del canale?")
    b = a["buchi"]
    if b.get("c_e"):
        inf("%d buchi in %.1f s (soglia %.0f ms = 3× l'intervallo mediano di "
            "%.1f ms).  L'utente: 6 in 17,5 s"
            % (b["quanti"], b["durata_s"], b["soglia_ms"],
               b["intervallo_mediano_ms"]))
        for x in b["buchi"][:10]:
            inf("  · a %.0f ms · %.0f ms di buco · la mano ha percorso %.0f px "
                "⇒ %.0f px di distacco aperti · %s"
                % (x["t_da_ms"], x["durata_ms"], x["la_mano_ha_percorso_px"],
                   x["distacco_aperto_px"], x["chi"]))
    else:
        dub(b.get("perche"))

    log("I CONTROLLI")
    vuoto = q["Q0"].get("vuoto")
    rossi = 0
    for nome in sorted(q, key=_ordine_q):
        e = q[nome]["esito"]
        if e is True:
            ok("%-6s %s" % (nome, q[nome]["perche"]))
        elif e is None:
            dub("%-6s %s" % (nome, q[nome]["perche"]))
        else:
            ko("%-6s %s" % (nome, q[nome]["perche"]))
            rossi += 1

    verbale["verdetto"] = {k: {"esito": v.get("esito"), "perche": v.get("perche")}
                           for k, v in q.items()}
    verbale["riassunto"] = a["riassunto"]
    verbale["separazione_rete"] = a["rete"]
    verbale["analisi_buchi"] = {k: v for k, v in a["buchi"].items()
                                if k != "campioni"}
    with open(ESITI, "a") as f:
        leggero = dict(verbale)
        for k in ("fotogrammi", "eventi", "giri", "costo_lettura_us",
                  "punti_previsti"):
            leggero.pop(k, None)
        if leggero.get("rete"):
            leggero["rete"] = {k: v for k, v in leggero["rete"].items()
                               if k != "campioni"}
        f.write(json.dumps(leggero, ensure_ascii=False) + "\n")
    inf("verbale in %s" % ESITI)

    if vuoto:
        ko("⛔⛔ NON HO NIENTE DA GIUDICARE — e NON e' «conforme»")
        return USCITA_NIENTE_DA_GIUDICARE
    if rossi:
        ko("⛔ NON CONFORME: %d controlli rossi" % rossi)
        return USCITA_NON_CONFORME
    ok("⭐ CONFORME")
    return USCITA_CONFORME


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--finto", action="store_true")
    p.add_argument("--misura", action="store_true")
    p.add_argument("--verdetto", metavar="VERBALE.json")
    p.add_argument("--host", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7746)
    p.add_argument("--utente", default="provab8")
    p.add_argument("--parola-file", default="/tmp/08-b67/parola")
    p.add_argument("--secondi", type=float, default=25.0)
    p.add_argument("--passo-ms", type=float, default=8.0,
                   help="⛔ 8 ms = 125 Hz, il ritmo di un mouse USB vero")
    p.add_argument("--barra", type=int, default=SCENA_UTENTE["barra_px"],
                   help="la larghezza della barra del titolo, in px (720)")
    p.add_argument("--seme", type=int, default=1)
    p.add_argument("--mano", default="pagina", choices=["pagina", "cdp"])
    p.add_argument("--senza-bottone", action="store_true",
                   help="⚠ senza il pulsante premuto NON e' un trascinamento")
    p.add_argument("--schermo", default=":88")
    p.add_argument("--diagnosi", type=int, default=9641)
    p.add_argument("--larghezza", type=int, default=1600)
    p.add_argument("--altezza", type=int, default=1000)
    p.add_argument("--lavoro", default="/tmp/08-b67")
    p.add_argument("--senza-gpu", action="store_true")
    p.add_argument("--intervallo-ping", type=float, default=0.05)
    p.add_argument("--giro", default="b67-%s" % time.strftime("%Y%m%d-%H%M%S"))
    a = p.parse_args()
    if a.certifica:
        return certifica()
    if a.finto:
        return finto()
    if a.verdetto:
        with open(a.verdetto) as f:
            return verdetto(json.load(f))
    if a.misura:
        return misura(a)
    p.print_help()
    return USCITA_USO


if __name__ == "__main__":
    sys.exit(main())
