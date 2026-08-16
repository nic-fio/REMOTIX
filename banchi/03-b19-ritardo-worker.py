#!/usr/bin/env python3
"""03-b17-ritardo.py — ⭐⭐ L'ANELLO DEL RITARDO.  Lo STEP 5 della fase 3.

    python3 banchi/03-b17-ritardo.py --certifica        ⭐ qui, senza server
    python3 banchi/03-b17-ritardo.py --misura --host 192.168.0.2 --porta 7605 \
            --utente nicfio --parola-file /tmp/03-b17/parola --secondi 30
    python3 banchi/03-b17-ritardo.py --verdetto          rilegge il verbale

═══════════════════════════════════════════════════════════════════════════════
⛔ CHE COSA MISURA — e la prima riga e' quel che NON misura
═══════════════════════════════════════════════════════════════════════════════

`SPECIFICHE.md` §3.2 chiede il ritardo **dall'input che arriva al fotogramma che
parte**.  ⛔ Alla fase 3 l'input NON ESISTE: il canale nasce alla fase 4, e il
campo `input` dei 28 byte vale **0** perche' `src/main.c:291-292` ci passa uno
zero letterale, dichiarato («*§6.2 dice «0 se nessuno», e in questa fase
l'iniezione non c'e' ancora*»).

⇒ Quel che questo banco misura e' **CATTURA → VETRO**, non input → vetro.  ⚠ E
  non e' una mezza misura per pigrizia: e' la meta' che si puo' chiudere oggi, e
  al posto dell'input c'e' il controllo **P1** (il ritardo noto), che e' quel
  che la rende una misura vera invece che un numero.

⭐ E in dote arriva un pezzo che v1 non vedeva: `t0` non e' «quando il prodotto
   se n'e' accorto» ma **l'istante vero della cattura** — il `pts` che Mutter
   attacca al fotogramma, che `src/figlio.c:1616-1653` **misura** essere lo
   stesso `CLOCK_MONOTONIC`, e che finisce nei 28 byte.  ⛔ E questo banco NON
   si fida di quella riga: la rilegge dal registro del prodotto a ogni giro
   (§ `verifica_pts`), perche' nel ramo di ripiego l'`istante` conterrebbe gia'
   l'attesa nel posto di scambio e il ritardo uscirebbe **piu' corto del vero**.

⭐⭐ E c'e' un `t0` ancora PIU' A MONTE, ed e' il regalo dello step 2: la scena
    dipinge nei pixel una **marca a 144 bit** che porta l'istante del disegno
    (`CLOCK_MONOTONIC`, 48 bit, µs).  ⇒ Il banco ha DUE `t0`:

      t0_disegno  l'istante in cui la scena ha disegnato   (dai pixel)
      t0_cattura  il `pts` di Mutter                       (dai 28 byte)

    e la loro differenza e' un pezzo della scomposizione che nessuno aveva mai
    misurato: **quanto sta fra il disegno e la cattura**.

═══════════════════════════════════════════════════════════════════════════════
⛔ LA FORMA DELL'ANELLO, E L'ORDINE E' VINCOLANTE — `STUDI.md` §web §6.3
═══════════════════════════════════════════════════════════════════════════════

      t1 = performance.now()      ⛔ PRIMA RIGA del richiamo del decodificatore
      → si DISEGNA               (il richiamo del PRODOTTO, non nostro)
      → e SOLO DOPO si legge la marca dai pixel

⛔ Leggere prima sarebbe un ritorno dalla GPU, e falserebbe la misura che sta
   prendendo.  ⭐ E l'ordine qui non e' una buona intenzione: e' garantito dalla
   struttura del `PROLOGO`, dove `t1` e' letteralmente la prima istruzione
   dell'involucro e la lettura dei pixel sta **dopo** il ritorno del richiamo
   originale.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ IL PEZZO CIECO, E SI DICHIARA ACCANTO A OGNI NUMERO
═══════════════════════════════════════════════════════════════════════════════

`STUDI.md` §web §6.2: fra il disegno e il pixel acceso passano **1,5-2,5 intervalli di
quadro, cioe' 16-40 ms a 60 Hz** — quanto tutto il nostro tetto — e **nessuna
API JavaScript li vede**.  ⇒ Ogni numero di questo banco esce con la stessa
riga accanto, e la funzione `con_pezzo_cieco()` la scrive: chi stampa un numero
senza passare di li' sta promettendo una cosa e facendone sentire un'altra.

⚠ E il banco dichiara anche il rovescio, che e' meno comodo: su **Xvfb** non
  c'e' nessun compositore, quindi in QUESTO ambiente quei 16-40 ms **non ci
  sono affatto**, e il numero misurato e' piu' vicino al vero di quanto sara'
  sullo schermo di un utente.  ⇒ Il pezzo cieco e' una stima **per lo schermo
  dell'utente**, non per il banco.

═══════════════════════════════════════════════════════════════════════════════
⛔ COME NON SI TOCCA IL PRODOTTO
═══════════════════════════════════════════════════════════════════════════════

`src/pagina.html` **non ha e non deve avere** un modo di consegnare i propri
esiti a un banco (decisione P2-6 §7 punto 1).  ⇒ Questo banco **non modifica un
byte della pagina**: entra con `Page.addScriptToEvaluateOnNewDocument`, che
mette un prologo **prima** di ogni script della pagina, e da li' **avvolge**
`VideoDecoder` e `WebTransport`.  E' la stessa tecnica di
`banchi/02-pagina-misura-cdp.py`, e la ragione e' la stessa: un banco che
avesse innestato la misura dentro `pagina.html` avrebbe misurato la pagina
strumentata, non il prodotto.

⚠ Un solo pezzo del prodotto e' toccato dall'esterno e va dichiarato: la
  **lettura dei pixel** (`getImageData`) sul deposito, dopo il disegno.  Costa,
  e il costo si MISURA (controllo P8) invece di essere creduto zero.

═══════════════════════════════════════════════════════════════════════════════
I SETTE CONTROLLI, E TRE SONO TRAPPOLE NOTE
═══════════════════════════════════════════════════════════════════════════════

  P1  ⛔ IL RITARDO NOTO.  Il ponte (`03-b17-ponte.py`) ritarda di N ms la sola
      direzione server → cliente, e la mediana DEVE salire di **esattamente N**.
      «Un banco che non lo fa non sa di misurare.»
      ⛔ E l'ancora dell'orologio NON passa dal ponte: se ci passasse, P1
      salirebbe di N/2 o di zero e passerebbe **anche a banco rotto**.

  P2  il rilevatore trova la marca CHE C'E'.  ⛔ Il rilevatore non e' nostro:
      e' `banchi/03-marca.py`, certificato esatto fino a QP 51 e con 0 falsi
      positivi su 3000 scene di rumore.  Qui si certifica il **campionamento**
      (quali pixel) contro il suo, sui pixel veri, non la decisione.

  P3  ⛔ NON trova quel che NON c'e'.  «Se dice sempre si', si sta misurando
      zero e si e' felici a torto» — e un rilevatore che dice sempre si'
      **passa anche P1**, perche' gli N ms si sommano identici.  Tre setacci:
      il rifiuto sui fotogrammi senza marca, la crescita del `disegno`, e la
      finestra di sanita' dell'istante.

  P5  ⛔ IL FUORI ORDINE.  I fotogrammi arrivano su stream indipendenti.
      ⭐ E la causa vera e' la DIMENSIONE, non la rete: `stream_video` scatta al
      **completamento** dello stream (`src/pagina.html:2570`, `:2594`), quindi
      una chiave grossa viene scavalcata dai delta che la seguono — il server
      lo sa e lo dichiara (`src/webtransport.c:1224-1240`).
      ⛔ Questo anello lo regge **per costruzione**: l'accoppiamento fra `t0` e
      `t1` non passa dall'ordine, passa dal **contenuto** (la marca dipinta nei
      pixel e il `pts` nei 28 byte).  Il controllo lo dimostra invece di
      dichiararlo.

  P6  ⛔ LA GRANA DELL'OROLOGIO.  Senza COOP+COEP i cronometri cadono su una
      griglia da 1 ms, su un tetto di 50.  ⚠ E' un **vincolo di prodotto**
      (`SPECIFICHE.md` §11.5, `STUDI.md` §web O11), non una taratura del banco: il
      prodotto le serve gia' (`src/pagina.c:32-35`).  Qui si MISURA la grana
      ottenuta, e si dichiara.

  P7  il ritmo consegnato dice se stai misurando la strada che credi.

  P8  ⛔ IL COSTO DEL BANCO.  Quel che il banco aggiunge alla pagina si misura,
      o e' un errore sistematico dentro ogni numero.

⚠ E UNA MISURA SINGOLA NON VALE NULLA: si lavora a **distribuzioni** —
  mediana, p05, p95 e code — non a campioni.  `LEZIONI.md` §1.4: e i primi
  fotogrammi sono l'avvio, non il regime, e si buttano.
"""
import argparse
import base64
import importlib.util
import json
import os
import random
import statistics
import struct
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
ESITI = os.path.join(QUI, "03-b17-esiti.jsonl")
PONTE = os.path.join(QUI, "03-b17-ponte.py")

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def ok(t):  print(f"    {VERDE}OK{GRIGIO}  {t}")
def ko(t):  print(f"    {ROSSO}NO{GRIGIO}  {t}")
def dub(t): print(f"    {GIALLO}??{GRIGIO}  {t}")
def inf(t): print(f"    --  {t}")
def log(t): print(f"\n\033[1m== {t}\033[0m")


# ═══════════════════════════════════════════════════════════════════════════
# §1  ATTREZZI
# ═══════════════════════════════════════════════════════════════════════════
_moduli = {}


def carica(nome, percorso):
    """⛔ `import 03-marca` e' impossibile (il nome comincia per cifra): si
    carica con `importlib`, come gia' fanno `03-marca-certifica.py:53` e
    `03-b14-cadenza.py:549`."""
    if nome in _moduli:
        return _moduli[nome]
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    _moduli[nome] = m
    return m


def marca_modulo():
    return carica("marca", os.path.join(QUI, "03-marca.py"))


def cdp_modulo():
    return carica("cdp", os.path.join(QUI, "02-pagina-misura-cdp.py"))


def ponte_modulo():
    return carica("ponte", PONTE)


def dist(v, scala=1.0):
    """⭐ La distribuzione, non il campione.  ⛔ Ritorna SEMPRE un dizionario:
    «zero campioni» e «non ho potuto guardare» si distinguono dal campo `n`."""
    if not v:
        return {"n": 0}
    w = sorted(x * scala for x in v)

    def q(p):
        return w[min(len(w) - 1, max(0, int(round(p * (len(w) - 1)))))]

    return {"n": len(w), "min": round(w[0], 3), "p05": round(q(0.05), 3),
            "p25": round(q(0.25), 3), "mediana": round(q(0.50), 3),
            "p75": round(q(0.75), 3), "p95": round(q(0.95), 3),
            "p99": round(q(0.99), 3), "max": round(w[-1], 3),
            "media": round(sum(w) / len(w), 3)}


# ⛔ IL PEZZO CIECO, IN UNA FUNZIONE, PERCHE' NON SI POSSA STAMPARE UN NUMERO
#    SENZA.  `STUDI.md` §web §6.2, `[?]`: nessuna API JavaScript lo vede.
CIECO_MIN_MS, CIECO_MAX_MS = 16.0, 40.0


def con_pezzo_cieco(ms):
    if ms is None:
        return "—"
    return ("%.1f ms MISURATI  +  [?] %.0f-%.0f ms di pezzo cieco "
            "(disegno → pixel acceso, `STUDI.md` §web §6.2, nessuna API lo vede)  "
            "⇒ %.1f-%.1f ms sullo schermo di un utente"
            % (ms, CIECO_MIN_MS, CIECO_MAX_MS, ms + CIECO_MIN_MS, ms + CIECO_MAX_MS))


# ── la sintesi della luminanza, per far decidere al lettore CERTIFICATO ─────
def immagine_da_celle(celle, geo=None):
    """⭐ Da 144 luminanze a un'immagine che il lettore certificato sa leggere.

    ⛔ E' il pezzo su cui questo banco poteva barare, quindi va detto per
       esteso.  Il lettore di `03-marca.py` decide da `_celle()`, che prende la
       **media del quadrato centrale al 50 %** di ogni cella.  Il prologo in
       JavaScript campiona **esattamente quel quadrato** (stessi offset, stessa
       media), perche' portare fuori dal browser 460 KB di pixel per fotogramma
       a 60 al secondo non sta in nessun canale.

       Qui si ricostruisce un'immagine in cui ogni cella e' PIENA del valore
       misurato: la media di un blocco costante e' la costante, quindi
       `_celle()` sull'immagine sintetica ritrova **gli stessi 144 numeri**, e
       da li' in poi decide il codice certificato — soglia, contrasto, sync,
       CRC, versione — riga per riga, senza una sola riga riscritta da noi.

    ⚠ E l'equivalenza NON si suppone: il controllo **P2b** la misura, dumpando
      i pixel veri di alcuni fotogrammi e confrontando i 144 numeri del
      JavaScript con quelli di numpy.
    """
    m = marca_modulo()
    # ⛔ numpy si chiede col nome del posto che lo usa: su NIC-OS non c'e', e
    #    `03-marca.py:94` vuole sapere CHI l'ha chiesto per poterlo dire.
    np = m.np_o_muori("03-b17: la sintesi dell'immagine dalle celle")
    g = geo or m.GEOMETRIA
    x0, y0, w, h = g.blocco()
    img = np.zeros((y0 + h + g.quiete, x0 + w + g.quiete), dtype=np.float64)
    for i, v in enumerate(celle):
        r, k = divmod(i, g.colonne)
        img[y0 + r * g.cella: y0 + (r + 1) * g.cella,
            x0 + k * g.cella: x0 + (k + 1) * g.cella] = v
    return np.clip(img, 0, 255).astype(np.uint8)


# ⛔⭐ L'UNITA' DELLE CELLE E' 0-255, E QUESTA RIGA E' NATA DA UN DIFETTO
#     MISURATO — `[M]` 13 agosto 2026, terzo giro dal vivo.
#
#     Il campionamento in JavaScript consegna luminanze in **0-255** (i byte di
#     `getImageData`); `_celle()` di `03-marca.py` lavora invece in **0-1**,
#     perche' `_luma()` divide per 255.  ⛔ La prima stesura moltiplicava per
#     255 quel che arrivava gia' in 0-255, e ne usciva un'immagine satura:
#     contrasto nullo, marca mai letta, **zero campioni su una catena che
#     funzionava perfettamente**.
#
#     ⚠ E la certificazione era VERDE, perche' le passava `_celle()` — cioe'
#       l'unita' SBAGLIATA, quella del lettore invece che quella
#       dell'acquisizione.  E' `LEZIONI.md` §2.2 alla lettera: una prova verde
#       per tutto il tempo in cui il difetto era vivo.  ⇒ Da qui in poi
#       l'unita' e' UNA sola, dichiarata, e c'e' un controllo che la pretende.
CELLE_MASSIMO = 255.0


def celle_unita_giusta(celle):
    """⛔ Dice se le celle sono nell'unita' dichiarata (0-255).

    Ritorna `(vero, perche)`.  ⚠ Un'immagine tutta nera sta in tutt'e due le
    unita' — ma li' la marca non c'e' comunque, e il lettore lo dira' col suo
    `perche`: non e' un caso che questo controllo debba distinguere.
    """
    if not celle:
        return False, "nessuna cella"
    alto = max(celle)
    if alto > 255.5:
        return False, ("⛔ le celle arrivano fino a %.1f: fuori da 0-255, "
                       "l'unita' non e' quella dichiarata" % alto)
    if alto <= 1.5:
        return False, ("⚠ le celle stanno tutte sotto 1,5: o l'immagine e' nera, "
                       "o sono nell'unita' 0-1 di `_celle()` invece che nella "
                       "0-255 di `getImageData` (il difetto del 13 agosto 2026)")
    return True, None


def leggi_celle(celle):
    """Il lettore CERTIFICATO, su un fotogramma ricostruito dalle 144 celle.

    ⛔ Le celle sono in **0-255** (vedi il riquadro qui sopra).
    """
    m = marca_modulo()
    # ⛔ `ricerca=0`: lo scorrimento e' gia' stato deciso a monte, dal
    #    campionamento in JavaScript, e ricercarlo qui sull'immagine sintetica
    #    non vorrebbe dire niente (le celle sono piene).  Lo scorrimento vero si
    #    misura sui pixel veri, in P2b.
    return m.leggi_marca(immagine_da_celle(celle), ricerca=0)


# ═══════════════════════════════════════════════════════════════════════════
# §2  IL PROLOGO — quel che gira DENTRO la pagina, senza toccarla
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Si installa con `Page.addScriptToEvaluateOnNewDocument`, cioe' PRIMA di
#    ogni script della pagina: quando `pagina.html` scrive
#    `new VideoDecoder(...)` trova gia' il nostro involucro.
#
# ⛔ E L'ORDINE DI `STUDI.md` §web §6.3 E' NELLA STRUTTURA, NON IN UN COMMENTO:
#      riga 1 dell'involucro  →  t1
#      riga 2                 →  il richiamo del PRODOTTO, che disegna
#      riga 3                 →  la lettura dei pixel
#    Non c'e' modo di eseguirle in un altro ordine senza riscrivere il file.
PROLOGO = r"""
(function () {
  if (window.__B17) return;
  const B = {
    campioni: [], intestazioni: new Map(), stream: [],
    conti: { decoder: 0, richiami: 0, letture: 0, senza_deposito: 0,
             senza_intestazione: 0, sonda: 0, buttati: 0 },
    grana: null, isolata: null, versione: 1,
    /* ⛔ I QUATTRO CAMPI CHE IL BANCO CAMBIA DA FUORI hanno un doppio fondo:
       quando la decodifica sta in un worker, il lettore dei pixel sta di la',
       e scriverli QUI e basta vorrebbe dire cambiare una copia che non legge
       nessuno — cioe' un P3 che non sposta niente e passa lo stesso. */
    _scorrimento: [0, 0], _leggi: true, crudi: [], _crudi_voluti: 0,
    /* ⛔⭐ DOVE si legge.  A riposo e' l'angolo in alto a sinistra, dove la
       scena dipinge la marca.  ⭐ Spostandola altrove si ottiene il controllo
       P3 sui PIXEL VERI: fotogrammi veri, in movimento, dello stesso desktop,
       in una regione dove la marca NON C'E'.  Se il lettore dice «si'» li',
       dice si' a qualunque cosa — ed e' esattamente il difetto che in v1 e'
       passato inosservato. */
    _finestra: [0, 0],
    t_origine: performance.timeOrigin,
    /* Lo scarto fra l'orologio del worker e quello della pagina, MISURATO. */
    scarto_worker: null, worker_visto: false, campioni_worker: 0,
    /* ⛔ Il costo della lettura dei pixel si MISURA (P8): un banco che credesse
       zero il proprio prezzo lo infilerebbe dentro il numero altrui. */
    costo_lettura_us: [],
  };
  window.__B17 = B;

  /* ══ 0-bis  IL WORKER — `STUDI.md` §web §6.1 ══════════════════════════════════
     ⛔ PERCHE' QUESTO BANCO E' CAMBIATO, e va detto accanto ai numeri.

     `src/pagina.html` sa mettere «WebTransport, decodifica e canvas» in un
     worker dedicato (interruttore `?video=worker`).  Quando lo fa, `t1`, la
     decodifica e i due `drawImage` NON sono piu' sul thread principale, e
     `Page.addScriptToEvaluateOnNewDocument` — che e' quel che avvolge
     `VideoDecoder` — **non entra nei worker**.  ⇒ Un banco non cambiato
     misurerebbe **zero richiami** e direbbe «non e' arrivato niente» di una
     catena che funziona.

     ⭐ E la cura NON e' un secondo metro: e' lo STESSO prologo, spedito anche
        dentro il worker, che rimanda di qua i suoi campioni.  L'accoppiamento
        col `pts` — cioe' con i 28 byte letti sul filo — resta dove era, perche'
        `WebTransport` resta sul thread principale anche col worker acceso.

     ⛔ E i numeri PRIMA e DOPO sono presi con QUESTO file tutti e due: un
        «dopo» misurato con lo strumento nuovo e un «prima» copiato da un
        rapporto vecchio non si sottraggono (`LEZIONI.md` §1.4). */
  function verso_worker(o) {
    if (B.w) { try { B.w.postMessage({ __b17_cmd: o }); } catch (e) { /* morto */ } }
  }
  for (const nome of ["leggi", "finestra", "scorrimento", "crudi_voluti"]) {
    Object.defineProperty(B, nome, {
      configurable: true,
      get: function () { return B["_" + nome]; },
      set: function (v) {
        B["_" + nome] = v;
        const o = {}; o[nome] = v; verso_worker(o);
      },
    });
  }

  const VeroW = window.Worker;
  if (VeroW) {
    window.Worker = function (u, o) {
      const w = new VeroW(u, o);
      B.w = w;
      /* ⚠ `addEventListener` e non `onmessage`: la pagina si mette il suo
         `onmessage` un istante dopo, e assegnarlo qui glielo cancellerebbe —
         il banco romperebbe il prodotto invece di guardarlo. */
      w.addEventListener("message", function (ev) {
        const d = ev.data;
        if (!d || !d.__b17) return;
        if (d.__b17 === "origine") {
          /* ⛔ I DUE OROLOGI.  `performance.now()` del worker parte dalla
             NASCITA DEL WORKER, non da quella del documento: sommare i due
             senza questo scarto darebbe tratti negativi o assurdi.  ⭐ E il
             controllo che lo dimostra e' il tratto 4 (`t_dec - t_ultimo`), che
             mette insieme un istante del worker e uno della pagina: se lo
             scarto fosse sbagliato, quel tratto uscirebbe assurdo. */
          B.scarto_worker = d.origine - B.t_origine;
          B.worker_visto = true;
          /* Quel che il banco ha gia' deciso PRIMA che il worker nascesse. */
          verso_worker({ leggi: B._leggi, finestra: B._finestra,
                         scorrimento: B._scorrimento,
                         crudi_voluti: B._crudi_voluti });
          return;
        }
        if (d.__b17 === "crudo") { B.crudi.push(d.crudo); return; }
        if (d.__b17 !== "c") return;
        const c = d.c, s = B.scarto_worker || 0;
        B.campioni_worker++;
        B.conti.richiami++;
        if (c.conti) for (const k in c.conti) B.conti[k] = c.conti[k];
        if (c.costo_us !== null && c.costo_us !== undefined
            && B.costo_lettura_us.length < 20000)
          B.costo_lettura_us.push(c.costo_us);
        const st = (c.pts === null || c.pts === undefined)
                   ? null : B.intestazioni.get(c.pts);
        if (!st) B.conti.senza_intestazione++;
        if (B.campioni.length < 400000) {
          B.campioni.push({
            t1: c.t1 + s, t_dip: c.t_dip + s, t_let: c.t_let + s,
            pts: c.pts, l: c.l, a: c.a, celle: c.celle, guaio: c.guaio,
            visto: c.visto, finestra: c.finestra,
            t_primo: st ? st.t_primo : null, t_ultimo: st ? st.t_ultimo : null,
            byte: st ? st.byte : null, tipo: st && st.i ? st.i.tipo : null,
            numero: st && st.i ? st.i.numero : null,
            input: st && st.i ? st.i.input : null,
            t_dec: (c.t_dec === null || c.t_dec === undefined) ? null : c.t_dec + s,
          });
        }
        if (c.pts !== null && c.pts !== undefined) B.intestazioni.delete(c.pts);
      });
      return w;
    };
    window.Worker.prototype = VeroW.prototype;
  }

  /* ── la geometria della marca, gemella di `03-marca.py:86-96` ─────────── */
  const CELLA = 24, MARGINE = 32, COLONNE = 18, RIGHE = 8, BIT = 144;
  const DENTRO = Math.max(2, CELLA >> 2);          /* = 6, come `_celle` */
  const LATO = CELLA - 2 * DENTRO;                 /* = 12 */
  const REG_L = MARGINE + COLONNE * CELLA + 16;    /* 480 */
  const REG_A = MARGINE + RIGHE * CELLA + 16;      /* 240 */
  /* BT.709, gli stessi pesi di `03-marca.py:101`. */
  const KR = 0.2126, KG = 0.7152, KB = 0.0722;

  /* ── la grana del cronometro, MISURATA e non dedotta (P6) ─────────────── */
  B.isolata = (typeof crossOriginIsolated !== "undefined") ? crossOriginIsolated : null;
  (function () {
    const d = [];
    let a = performance.now();
    for (let i = 0; i < 200000; i++) {
      const b = performance.now();
      if (b !== a) { d.push(b - a); a = b; }
      if (d.length >= 4000) break;
    }
    d.sort(function (x, y) { return x - y; });
    B.grana = { salti: d.length, minimo_ms: d.length ? d[0] : null,
                mediano_ms: d.length ? d[d.length >> 1] : null };
  })();

  /* ── §6.2: i 28 byte, riscritti QUI e non presi dalla pagina ───────────
     ⭐ E' voluto: se un giorno i due lettori divergono, quel disaccordo e' il
        regalo.  Stessi offset di `src/rcp.c:2252-2263`. */
  function intestazione(u8) {
    if (u8.length < 28) return null;
    const v = new DataView(u8.buffer, u8.byteOffset, 28);
    return { tipo: v.getUint16(0), codec: v.getUint16(2),
             larghezza: v.getUint32(4), altezza: v.getUint32(8),
             numero: v.getUint32(12),
             istante: Number(v.getBigUint64(16)),
             input: v.getUint32(24) };
  }

  /* ══ 1. WEBTRANSPORT: quando arriva il PRIMO byte e quando l'ULTIMO ═════
     Serve a due cose: la scomposizione (filo contro decodifica) e P5 (il
     fuori ordine si VEDE, invece di essere supposto). */
  const VeroWT = window.WebTransport;
  if (VeroWT) {
    window.WebTransport = function (url, opzioni) {
      const wt = new VeroWT(url, opzioni);
      const vero = Object.getOwnPropertyDescriptor(
        Object.getPrototypeOf(wt), "incomingUnidirectionalStreams");
      const originale = vero ? vero.get.call(wt) : wt.incomingUnidirectionalStreams;
      const lettore = originale.getReader();
      const avvolto = new ReadableStream({
        async pull(c) {
          const r = await lettore.read();
          if (r.done) { c.close(); return; }
          c.enqueue(spia(r.value));
        }
      });
      Object.defineProperty(wt, "incomingUnidirectionalStreams",
                            { get: function () { return avvolto; },
                              configurable: true });
      return wt;
    };
    window.WebTransport.prototype = VeroWT.prototype;
  }

  function spia(flusso) {
    /* ⛔ Non si copiano i byte: si guarda passare il primo e l'ultimo, e si
       tiene solo la testa da 28 byte.  Copiare ogni fotogramma raddoppierebbe
       il traffico di memoria dentro la misura che lo sta cronometrando. */
    const s = { t_primo: null, t_ultimo: null, byte: 0, testa: [],
                testa_byte: 0, i: null, pezzi: 0 };
    B.stream.push(s);
    const lettore = flusso.getReader();
    return new ReadableStream({
      async pull(c) {
        let r;
        try { r = await lettore.read(); }
        catch (e) { s.t_ultimo = performance.now(); s.azzerato = true; c.error(e); return; }
        if (r.done) {
          s.t_ultimo = performance.now();
          if (s.i && s.i.istante) B.intestazioni.set(s.i.istante, s);
          c.close();
          return;
        }
        const ora = performance.now();
        if (s.t_primo === null) s.t_primo = ora;
        s.pezzi++;
        s.byte += r.value.length;
        if (s.testa_byte < 28) {
          s.testa.push(r.value.subarray(0, Math.min(28 - s.testa_byte, r.value.length)));
          s.testa_byte += s.testa[s.testa.length - 1].length;
          if (s.testa_byte >= 28) {
            const t = new Uint8Array(28); let o = 0;
            for (const p of s.testa) { t.set(p, o); o += p.length; }
            s.i = intestazione(t);
            if (s.i && s.i.istante) B.intestazioni.set(s.i.istante, s);
          }
        }
        c.enqueue(r.value);
      }
    });
  }

  /* ══ 2. VIDEODECODER: t1, il disegno del prodotto, poi i pixel ══════════ */
  const VeroVD = window.VideoDecoder;
  if (VeroVD) {
    function Avvolto(init) {
      const suo = init && init.output;
      const mio = Object.assign({}, init, {
        output: function (f) {
          /* ─── RIGA 1: `t1`.  ⛔ PRIMA di tutto, `STUDI.md` §web §6.3. ─────────── */
          const t1 = performance.now();
          const pts = f.timestamp;
          const l = f.displayWidth || f.codedWidth;
          const a = f.displayHeight || f.codedHeight;
          B.conti.richiami++;
          /* ─── RIGA 2: SI DISEGNA — e a disegnare e' il PRODOTTO. ───────── */
          let guaio = null;
          try { suo(f); } catch (e) { guaio = "" + e; }
          const t_dip = performance.now();
          /* ─── RIGA 3: e SOLO ADESSO si leggono i pixel. ────────────────── */
          let celle = null, t_let = t_dip;
          if (B.leggi) {
            const c0 = performance.now();
            celle = leggi_marca_celle();
            t_let = performance.now();
            if (B.costo_lettura_us.length < 20000)
              B.costo_lettura_us.push((t_let - c0) * 1000);
          }
          const s = B.intestazioni.get(pts) || null;
          if (!s) B.conti.senza_intestazione++;
          if (B.campioni.length < 400000) {
            B.campioni.push({
              t1: t1, t_dip: t_dip, t_let: t_let, pts: pts, l: l, a: a,
              celle: celle, guaio: guaio,
              /* ⛔ «i pixel sono stati guardati» e' un FATTO del campione, non
                 una deduzione da un campo che a valle viene consumato: la
                 prima stesura lo deduceva da `celle`, che `arricchisci()`
                 toglie — e P2 diceva «non ho potuto guardare» di 482 letture
                 riuscite (`[M]` 13 agosto 2026). */
              visto: celle !== null, finestra: B.finestra.slice(),
              t_primo: s ? s.t_primo : null, t_ultimo: s ? s.t_ultimo : null,
              byte: s ? s.byte : null, tipo: s && s.i ? s.i.tipo : null,
              numero: s && s.i ? s.i.numero : null,
              input: s && s.i ? s.i.input : null,
              t_dec: B.t_dec.get(pts) || null,
            });
          }
          B.t_dec.delete(pts);
          B.intestazioni.delete(pts);
        }
      });
      const d = new VeroVD(mio);
      B.conti.decoder++;
      const suo_decode = d.decode.bind(d);
      d.decode = function (chunk) {
        B.t_dec.set(chunk.timestamp, performance.now());
        return suo_decode(chunk);
      };
      return d;
    }
    B.t_dec = new Map();
    Avvolto.isConfigSupported = VeroVD.isConfigSupported.bind(VeroVD);
    window.VideoDecoder = Avvolto;
  }

  /* ══ 3. LA LETTURA DEI PIXEL — dal DEPOSITO, non dalla vista ════════════
     ⛔ Il deposito e' alla misura NATIVA del fotogramma (`pagina.html:1778`);
        la tela visibile e' ricampionata alla vista (`:1365`).  Leggere la
        marca dalla vista vorrebbe dire leggere un ricampionamento, e la marca
        e' fatta di celle da 24 px: un fattore 0,7 le impasta.
     ⛔ E si legge DOPO il disegno, mai prima. */
  function leggi_marca_celle() {
    const S = window.REMOTIX && window.REMOTIX.schermo;
    if (!S || !S.deposito || !S.deposito_p) { B.conti.senza_deposito++; return null; }
    const ox = B.finestra[0], oy = B.finestra[1];
    if (S.deposito.width < ox + REG_L || S.deposito.height < oy + REG_A) {
      B.conti.sonda++; return null;
    }
    let d;
    try { d = S.deposito_p.getImageData(ox, oy, REG_L, REG_A).data; }
    catch (e) { B.conti.buttati++; return null; }
    B.conti.letture++;
    const sx = B.scorrimento[0], sy = B.scorrimento[1];
    const v = new Array(BIT);
    for (let i = 0; i < BIT; i++) {
      const r = (i / COLONNE) | 0, k = i % COLONNE;
      const xa = MARGINE + k * CELLA + DENTRO + sx;
      const ya = MARGINE + r * CELLA + DENTRO + sy;
      let somma = 0;
      for (let y = ya; y < ya + LATO; y++) {
        let o = (y * REG_L + xa) * 4;
        for (let x = 0; x < LATO; x++, o += 4)
          somma += KR * d[o] + KG * d[o + 1] + KB * d[o + 2];
      }
      v[i] = somma / (LATO * LATO);
    }
    if (B.crudi.length < B.crudi_voluti) {
      /* ⭐ Ogni tanto si porta fuori la REGIONE CRUDA **insieme alle celle che
         il JavaScript ne ha ricavato**: e' il controllo P2b, cioe' la prova
         che questo campionamento e' LO STESSO di `_celle()` in numpy.
         ⛔ Le due cose devono viaggiare appaiate: un crudo senza le sue celle
         non dimostrerebbe niente sul campionamento, dimostrerebbe solo che la
         marca c'era. */
      let s = "";
      for (let i = 0; i < d.length; i += 4)
        s += String.fromCharCode(d[i], d[i + 1], d[i + 2]);
      B.crudi.push({ l: REG_L, a: REG_A, b64: btoa(s), celle: v.slice(),
                     scorrimento: [sx, sy] });
    }
    return v;
  }

  /* ══ 4. IL RITIRO — si SVUOTA, cosi' due ritiri non contano due volte ═══ */
  B.prendi = function () {
    const c = B.campioni; B.campioni = [];
    const cr = B.crudi; B.crudi = [];
    const co = B.costo_lettura_us; B.costo_lettura_us = [];
    return { campioni: c, crudi: cr, costo_lettura_us: co,
             conti: Object.assign({}, B.conti), grana: B.grana,
             isolata: B.isolata, t_origine: B.t_origine,
             /* ⭐ Da qui si legge se il «dopo» e' stato misurato DAVVERO nel
                worker, invece di dedurlo dall'URL. */
             worker: { visto: B.worker_visto, scarto_ms: B.scarto_worker,
                       campioni: B.campioni_worker },
             ora_pagina: performance.now(),
             ora_reale: performance.timeOrigin + performance.now(),
             pagina: window.REMOTIX && window.REMOTIX.schermo
                     ? Object.assign({}, window.REMOTIX.schermo.conti) : null };
  };
})();
"""


# ═══════════════════════════════════════════════════════════════════════════
# §2-bis  IL PROLOGO DEL WORKER — lo stesso metro, dall'altra parte
# ═══════════════════════════════════════════════════════════════════════════
# ⛔ Si installa con `Runtime.evaluate` sul BERSAGLIO DEL WORKER, non con
#    `Page.addScriptToEvaluateOnNewDocument` — che nei worker non entra.
#
# ⚠ E percio' NON gira «prima di ogni script», ma DOPO che il worker e' nato.
#   ⇒ Il momento in cui si installa e' vincolante e il banco lo rispetta: il
#     worker di `pagina.html` a riposo non fa NIENTE (aspetta un messaggio), e
#     il suo `VideoDecoder` nasce solo alla prima chiave, cioe' DOPO che
#     l'utente e' entrato.  Il banco si aggancia PRIMA di mandare le
#     credenziali, e poi VERIFICA di aver visto dei richiami: se ne conta zero
#     lo dice, invece di stampare uno zero come se fosse una misura.
#
# ⛔ Le stesse costanti della marca e lo STESSO campionamento del prologo di
#    sopra: se qui si riscrivessero, il «dopo» sarebbe misurato con un altro
#    righello e la differenza col «prima» non vorrebbe dire niente.
PROLOGO_WORKER = r"""
(function () {
  if (self.__B17W) return "gia' dentro";
  const W = { leggi: true, finestra: [0, 0], scorrimento: [0, 0],
              crudi: 0, crudi_voluti: 0,
              conti: { letture: 0, senza_deposito: 0, sonda: 0, buttati: 0 },
              t_dec: new Map() };
  self.__B17W = W;

  /* la geometria della marca, gemella di `03-marca.py:86-96` */
  const CELLA = 24, MARGINE = 32, COLONNE = 18, RIGHE = 8, BIT = 144;
  const DENTRO = Math.max(2, CELLA >> 2);
  const LATO = CELLA - 2 * DENTRO;
  const REG_L = MARGINE + COLONNE * CELLA + 16;
  const REG_A = MARGINE + RIGHE * CELLA + 16;
  const KR = 0.2126, KG = 0.7152, KB = 0.0722;

  /* ⛔ I DUE OROLOGI: si dichiara il proprio `timeOrigin` e la pagina fa il
     conto.  Senza, i tratti che uniscono i due lati sarebbero fantasia. */
  self.postMessage({ __b17: "origine", origine: performance.timeOrigin });

  self.addEventListener("message", function (ev) {
    const d = ev.data;
    if (!d || !d.__b17_cmd) return;
    const o = d.__b17_cmd;
    for (const k of ["leggi", "finestra", "scorrimento", "crudi_voluti"])
      if (k in o) W[k] = o[k];
  });

  function leggi_marca_celle() {
    const S = self.REMOTIX && self.REMOTIX.schermo;
    if (!S || !S.deposito || !S.deposito_p) { W.conti.senza_deposito++; return null; }
    const ox = W.finestra[0], oy = W.finestra[1];
    if (S.deposito.width < ox + REG_L || S.deposito.height < oy + REG_A) {
      W.conti.sonda++; return null;
    }
    let d;
    try { d = S.deposito_p.getImageData(ox, oy, REG_L, REG_A).data; }
    catch (e) { W.conti.buttati++; return null; }
    W.conti.letture++;
    const sx = W.scorrimento[0], sy = W.scorrimento[1];
    const v = new Array(BIT);
    for (let i = 0; i < BIT; i++) {
      const r = (i / COLONNE) | 0, k = i % COLONNE;
      const xa = MARGINE + k * CELLA + DENTRO + sx;
      const ya = MARGINE + r * CELLA + DENTRO + sy;
      let somma = 0;
      for (let y = ya; y < ya + LATO; y++) {
        let o = (y * REG_L + xa) * 4;
        for (let x = 0; x < LATO; x++, o += 4)
          somma += KR * d[o] + KG * d[o + 1] + KB * d[o + 2];
      }
      v[i] = somma / (LATO * LATO);
    }
    if (W.crudi < W.crudi_voluti) {
      W.crudi++;
      let s = "";
      for (let i = 0; i < d.length; i += 4)
        s += String.fromCharCode(d[i], d[i + 1], d[i + 2]);
      self.postMessage({ __b17: "crudo",
                         crudo: { l: REG_L, a: REG_A, b64: btoa(s),
                                  celle: v.slice(), scorrimento: [sx, sy] } });
    }
    return v;
  }

  /* ══ VIDEODECODER, nel worker: t1, il disegno del PRODOTTO, poi i pixel ══ */
  const VeroVD = self.VideoDecoder;
  if (!VeroVD) return "niente VideoDecoder qui";
  function Avvolto(init) {
    const suo = init && init.output;
    const mio = Object.assign({}, init, {
      output: function (f) {
        /* ─── RIGA 1: `t1`.  ⛔ PRIMA di tutto, `STUDI.md` §web §6.3. ─────────── */
        const t1 = performance.now();
        const pts = f.timestamp;
        const l = f.displayWidth || f.codedWidth;
        const a = f.displayHeight || f.codedHeight;
        /* ─── RIGA 2: SI DISEGNA — e a disegnare e' il PRODOTTO. ───────── */
        let guaio = null;
        try { suo(f); } catch (e) { guaio = "" + e; }
        const t_dip = performance.now();
        /* ─── RIGA 3: e SOLO ADESSO si leggono i pixel. ────────────────── */
        let celle = null, t_let = t_dip, costo = null;
        if (W.leggi) {
          const c0 = performance.now();
          celle = leggi_marca_celle();
          t_let = performance.now();
          costo = (t_let - c0) * 1000;
        }
        const td = W.t_dec.get(pts);
        W.t_dec.delete(pts);
        self.postMessage({ __b17: "c", c: {
          t1: t1, t_dip: t_dip, t_let: t_let, pts: pts, l: l, a: a,
          celle: celle, guaio: guaio, visto: celle !== null,
          finestra: W.finestra.slice(), costo_us: costo,
          t_dec: (td === undefined) ? null : td,
          conti: Object.assign({}, W.conti) } });
      }
    });
    const d = new VeroVD(mio);
    const suo_decode = d.decode.bind(d);
    d.decode = function (chunk) {
      W.t_dec.set(chunk.timestamp, performance.now());
      return suo_decode(chunk);
    };
    return d;
  }
  Avvolto.isConfigSupported = VeroVD.isConfigSupported.bind(VeroVD);
  self.VideoDecoder = Avvolto;
  return "dentro";
})()
"""


# ═══════════════════════════════════════════════════════════════════════════
# §3  IL PALCO — Xvfb, Chrome, CDP
# ═══════════════════════════════════════════════════════════════════════════
class Palco:
    """⛔ Copiato nella forma da `03-b16-dipinti.py:427-496`, che a sua volta
    verifica `Xvfb` con `xdpyinfo` invece che con uno `sleep`."""

    def __init__(self, schermo=":85", diagnosi=9605, finestra=(1500, 1000),
                 lavoro=None, gpu=True):
        self.schermo, self.diagnosi = schermo, diagnosi
        self.finestra, self.gpu = finestra, gpu
        self.t = lavoro or "/tmp/03-b17-palco-%d" % os.getpid()
        self.x = self.chrome = self.c = self.cw = None
        os.makedirs(self.t, exist_ok=True)

    def _amb(self):
        e = dict(os.environ)
        e.pop("WAYLAND_DISPLAY", None)
        e["DISPLAY"] = self.schermo
        return e

    def accendi(self):
        sock = "/tmp/.X11-unix/X" + self.schermo.lstrip(":")
        if os.path.exists(sock):
            raise RuntimeError("⛔ %s esiste gia': un altro banco sta usando lo "
                               "schermo %s.  Due banchi sullo stesso schermo si "
                               "guastano a vicenda." % (sock, self.schermo))
        l, a = self.finestra
        self.x = subprocess.Popen(["Xvfb", self.schermo, "-screen", "0",
                                   "%dx%dx24" % (l + 100, a + 200)],
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
        fine = time.time() + 15
        misurato = None
        while time.time() < fine:
            r = subprocess.run(["xdpyinfo"], env=self._amb(),
                               capture_output=True, text=True)
            if r.returncode == 0:
                for riga in r.stdout.splitlines():
                    if "dimensions:" in riga:
                        misurato = riga.split()[1]
                break
            time.sleep(0.3)
        if misurato is None:
            raise RuntimeError("⛔ Xvfb non ha risposto a `xdpyinfo`: non e' "
                               "«schermo vuoto», e' «non ho potuto guardare»")
        flag = ["google-chrome", "--user-data-dir=%s/profilo" % self.t,
                "--no-first-run", "--no-default-browser-check", "--disable-sync",
                "--remote-debugging-port=%d" % self.diagnosi,
                "--remote-allow-origins=*",
                "--window-size=%d,%d" % (l, a), "--window-position=0,0",
                "about:blank"]
        if not self.gpu:
            flag.insert(1, "--disable-gpu")
        self.chrome = subprocess.Popen(flag, env=self._amb(),
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
        self.riattacca()
        return misurato

    def riattacca(self):
        """⛔ IL CANALE CDP SI PUO' CHIUDERE, E NON E' UN DIFETTO DEL PRODOTTO.

        Una navigazione fra due processi di rendering puo' far cadere il
        WebSocket di diagnosi.  ⚠ Un banco che morisse li' perderebbe il giro e
        darebbe la colpa alla misura: si riattacca, e **si dice** che l'ha
        fatto — un riattacco silenzioso nasconderebbe una pagina ricaricata,
        cioe' una scena diversa sotto la stessa etichetta.
        """
        cdp = cdp_modulo()
        b = cdp.pagina(self.diagnosi, attesa=40)
        self.c = cdp.Cdp(b["webSocketDebuggerUrl"], timeout=180)
        # ⛔⭐ GLI EVENTI SI TENGONO.  `Cdp.chiama` di `02-pagina-misura-cdp.py`
        #    SCARTA tutto quel che non e' la risposta attesa («e' un evento: non
        #    serve»), e per i worker serve eccome: l'unico modo di sapere che un
        #    worker e' nato — e con quale `sessionId` gli si parla — e'
        #    l'evento `Target.attachedToTarget`.  ⚠ Il modulo condiviso NON si
        #    tocca (ci si appoggiano altri banchi): si avvolge qui.
        self.eventi = []
        self._bufferizza()
        for m in ("Page.enable", "Runtime.enable", "Network.enable"):
            self.c.chiama(m)
        # ⛔ PRIMA di navigare: cosi' il worker che nascera' col caricamento
        #    viene annunciato invece di essere scoperto quando e' gia' partito.
        try:
            self.c.chiama("Target.setAutoAttach", autoAttach=True,
                          waitForDebuggerOnStart=False, flatten=True)
        except Exception as e:                          # noqa: BLE001
            dub("⚠ Target.setAutoAttach non e' passato (%s): senza, un worker "
                "non si puo' guardare" % str(e)[:90])
        self.c.chiama("Network.setCacheDisabled", cacheDisabled=True)
        self.riattacchi = getattr(self, "riattacchi", 0)
        return b

    def _bufferizza(self):
        """Rimpiazza `chiama` con una che mette gli EVENTI da parte."""
        c = self.c
        eventi = self.eventi

        def chiama(metodo, **par):
            return self._dialogo(metodo, par, None)

        c.chiama = chiama
        self._eventi = eventi

    def _dialogo(self, metodo, par=None, sid=None, scadenza=60.0):
        """Manda un comando e aspetta LA SUA risposta, tenendo gli eventi.

        ⛔ `sessionId` e' un campo di PRIMO LIVELLO del messaggio, non un
           parametro: infilarlo in `params` lo manderebbe al bersaglio
           sbagliato — cioe' alla pagina invece che al worker."""
        c = self.c
        c.n += 1
        mio = c.n
        m = {"id": mio, "method": metodo, "params": par or {}}
        if sid:
            m["sessionId"] = sid
        c.ws.manda(json.dumps(m))
        fine = time.time() + scadenza
        while time.time() < fine:
            r = json.loads(c.ws.ricevi())
            if "method" in r:
                self.eventi.append(r)
                continue
            if r.get("id") != mio:
                continue
            if "error" in r:
                raise RuntimeError(metodo + ": " + json.dumps(r["error"]))
            return r.get("result", {})
        raise RuntimeError("%s: nessuna risposta in %.0f s" % (metodo, scadenza))

    def _sessione_worker(self):
        """Il `sessionId` del worker, dagli eventi gia' arrivati."""
        for e in self.eventi:
            if e.get("method") != "Target.attachedToTarget":
                continue
            ti = e.get("params", {}).get("targetInfo", {})
            if "worker" in (ti.get("type") or ""):
                return e["params"]["sessionId"]
        return None

    def aggancia_worker(self, attesa=20):
        """⛔⭐ IL BERSAGLIO DEL WORKER — e perche' serve una SECONDA presa.

        `Page.addScriptToEvaluateOnNewDocument` e `Runtime.evaluate` parlano al
        frame principale.  Un worker dedicato e' un BERSAGLIO A PARTE, con un
        suo WebSocket: senza attaccarcisi, `VideoDecoder` non si avvolge e il
        banco conterebbe zero richiami su una catena che funziona.

        ⚠ Torna `None` quando un worker non c'e' — che NON e' un guasto: e' il
          caso PRIMA, cioe' la pagina che decodifica sul thread principale.
        """
        # ⛔⭐ E NON SI APRE UNA PRESA SUA.  `[M]` 13 agosto 2026: il bersaglio
        #    del worker compare in `/json/list` con un `webSocketDebuggerUrl`
        #    che ACCETTA la connessione e poi **non risponde a un comando** —
        #    `Runtime.enable` scade.  ⇒ A un worker dedicato si parla dalla
        #    sessione del suo GENITORE, con `Target.setAutoAttach(flatten)` e
        #    il `sessionId` che l'evento `Target.attachedToTarget` porta.
        #    ⚠ Una presa che si apre e non risponde e' peggio di una che
        #      rifiuta: sembra agganciata.
        fine = time.time() + attesa
        sid = self._sessione_worker()
        while sid is None and time.time() < fine:
            # si pompa il canale con un comando innocuo: gli eventi arretrati
            # entrano nel buffer mentre si aspetta la sua risposta
            try:
                self._dialogo("Runtime.evaluate",
                              {"expression": "1", "returnByValue": True},
                              None, scadenza=5.0)
            except Exception:                          # noqa: BLE001
                pass
            sid = self._sessione_worker()
            if sid is None:
                time.sleep(0.4)
        if sid is None:
            return None
        self.cw = sid
        try:
            r = self._dialogo("Runtime.evaluate",
                              {"expression": PROLOGO_WORKER,
                               "returnByValue": True, "awaitPromise": False},
                              sid, scadenza=30.0)
        except Exception as e:                         # noqa: BLE001
            dub("⚠ il prologo non e' entrato nel worker: %s" % str(e)[:140])
            return None
        if "exceptionDetails" in r:
            dub("⚠ il prologo del worker ha lanciato: %s"
                % json.dumps(r["exceptionDetails"])[:200])
            return None
        return r.get("result", {}).get("value")

    def valuta(self, espressione, attendi=False):
        try:
            return self.c.valuta(espressione, attendi=attendi)
        except Exception as e:                       # noqa: BLE001
            dub("⚠ il canale CDP e' caduto (%s): mi riattacco" % str(e)[:80])
            self.riattacca()
            self.riattacchi = getattr(self, "riattacchi", 0) + 1
            try:
                return self.c.valuta(espressione, attendi=attendi)
            except Exception as e2:                  # noqa: BLE001
                ko("⛔ il canale CDP non torna: %s" % str(e2)[:120])
                return None

    def chiama(self, metodo, **par):
        try:
            return self.c.chiama(metodo, **par)
        except Exception as e:                       # noqa: BLE001
            dub("⚠ il canale CDP e' caduto su %s (%s): mi riattacco"
                % (metodo, str(e)[:60]))
            self.riattacca()
            self.riattacchi = getattr(self, "riattacchi", 0) + 1
            return self.c.chiama(metodo, **par)

    def spegni(self):
        for p in (self.chrome, self.x):
            if p:
                try:
                    p.terminate()
                    p.wait(timeout=8)
                except Exception:      # noqa: BLE001
                    try:
                        p.kill()
                    except Exception:  # noqa: BLE001
                        pass


def batti(c, testo):
    """⛔ «thisisunsafe» si BATTE, non si aggira con un flag: il certificato del
    prodotto e' il suo (`02-giudizio-catena.py:323`)."""
    for ch in testo:
        for tipo in ("keyDown", "char", "keyUp"):
            p = {"type": tipo, "text": ch} if tipo == "char" else {"type": tipo, "key": ch}
            c.chiama("Input.dispatchKeyEvent", **p)
        time.sleep(0.03)


ENTRA = """
(function () {
  const u = document.getElementById("utente"), p = document.getElementById("parola");
  if (!u || !p) return "⛔ il modulo non c'e'";
  u.value = %s; p.value = %s;
  document.getElementById("modulo").requestSubmit();
  return "inviato";
})()
"""


def aspetta(c, espressione, quanto, pronto, passo=0.4):
    fine = time.time() + quanto
    ultimo = None
    while time.time() < fine:
        ultimo = c.valuta(espressione, attendi=False)
        if ultimo and pronto(ultimo):
            return ultimo
        time.sleep(passo)
    return ultimo


# ═══════════════════════════════════════════════════════════════════════════
# §4  L'OROLOGIO — dalla pagina al server, in due tratti misurati
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Sono DUE macchine.  `t1` sta nell'orologio della pagina, `t0` in quello del
#    server: senza un ponte fra i due, sottrarli da' un numero che sembra un
#    ritardo e non lo e'.
#
#      pagina  --(A)-->  CLOCK_MONOTONIC di CHUWI  --(B)-->  del server
#
#    (A) `performance.timeOrigin + performance.now()` e' l'ora di parete di
#        CHUWI, e l'ora di parete e il monotono si leggono insieme, qui, con una
#        syscall.  ⚠ E si CONTROLLA: la stessa relazione si rimisura da fuori
#        con un giro CDP, e le due devono coincidere.  Se non coincidono,
#        `timeOrigin` non e' quel che credevamo e il numero non si scrive.
#    (B) l'ancora del ponte (`03-b17-ponte.py`), su una porta CHE NON PASSA DAL
#        RITARDATORE — altrimenti P1 salirebbe di N/2 invece che di N.
def scarto_parete_monotono_us():
    """Quanto vale `reale − monotono` QUI, adesso.  ⛔ Le due letture si
    prendono a cavallo l'una dell'altra e si tiene il giro piu' corto: fra le
    due passa una syscall, e su un tetto di 50 ms conta."""
    migliore = None
    for _ in range(60):
        a = time.clock_gettime_ns(time.CLOCK_MONOTONIC) // 1000
        r = time.clock_gettime_ns(time.CLOCK_REALTIME) // 1000
        b = time.clock_gettime_ns(time.CLOCK_MONOTONIC) // 1000
        if migliore is None or (b - a) < migliore[1]:
            migliore = (r - (a + b) // 2, b - a)
    return {"scarto_us": migliore[0], "errore_us": migliore[1] // 2}


def ancora_pagina_cdp(c, campioni=40):
    """⭐ Il CONTROLLO di (A): si chiede `performance.now()` da fuori, si
    cronometra il giro CDP, e si tiene il piu' corto.  ⛔ Non e' la strada
    principale — il giro CDP e' millisecondi — ma dice se `timeOrigin` mente."""
    migliore = None
    for _ in range(campioni):
        a = time.clock_gettime_ns(time.CLOCK_MONOTONIC) // 1000
        v = c.valuta("[performance.timeOrigin, performance.now()]", attendi=False)
        b = time.clock_gettime_ns(time.CLOCK_MONOTONIC) // 1000
        if not isinstance(v, list) or len(v) != 2:
            continue
        pagina_us = int((v[0] + v[1]) * 1000)
        if migliore is None or (b - a) < migliore[1]:
            migliore = (pagina_us - (a + b) // 2, b - a)
    if migliore is None:
        return {"c_e": False, "perche": "⛔ nessuna risposta dal canale CDP"}
    return {"c_e": True, "scarto_us": migliore[0], "errore_us": migliore[1] // 2}


class Orologi:
    """Il convertitore: da `performance.now()` a `CLOCK_MONOTONIC` del server."""

    def __init__(self, parete, ancora_a, ancora_b, origine_pagina_ms):
        self.parete = parete
        self.a, self.b = ancora_a, ancora_b
        self.origine_us = int(origine_pagina_ms * 1000)

    def utilizzabile(self):
        return self.a.get("c_e")

    def a_server_us(self, t_pagina_ms):
        """t (ms, orologio della pagina) → µs, CLOCK_MONOTONIC del server."""
        reale_us = self.origine_us + int(t_pagina_ms * 1000)
        chuwi_mono_us = reale_us - self.parete["scarto_us"]
        p = ponte_modulo()
        s, _ = p.scarto_interpolato(self.a, self.b, chuwi_mono_us)
        if s is None:
            return None
        return chuwi_mono_us + s

    def errore_us(self):
        """⛔ L'errore si SOMMA e si dichiara: e' il margine dentro cui ogni
        numero di questo banco e' vero."""
        e = self.parete["errore_us"] + self.a.get("errore_us", 0)
        if self.b.get("c_e"):
            e = max(e, self.parete["errore_us"] + self.b.get("errore_us", 0))
        return e


# ═══════════════════════════════════════════════════════════════════════════
# §5  I SETTE CONTROLLI — funzioni PURE sul verbale
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Pure apposta: cosi' `--certifica` gira su CHUWI senza rete e senza server,
#    e chi revisiona il banco puo' rileggerlo e riprovarlo senza toccare la
#    macchina.  ⚠ E cosi' si puo' innestare il guasto NEL VERBALE e pretendere
#    che il controllo diventi rosso: e' la certificazione a tre giri di
#    `LEZIONI.md` §1.2.
AVVIO_MS = 3000.0        # ⛔ `LEZIONI.md` §1.4: l'avvio non e' il regime
CODA_MS = 500.0


def regime(campioni, avvio_ms=AVVIO_MS, coda_ms=CODA_MS):
    """I campioni del REGIME.  ⛔ I primi si buttano: sono l'avvio, quando la
    pagina si riconfigura, il decodificatore si sveglia e la prima chiave e'
    grossa dieci volte."""
    buoni = [c for c in campioni if c.get("ritardo_ms") is not None]
    if not buoni:
        return []
    t0 = min(c["t1"] for c in buoni)
    t9 = max(c["t1"] for c in buoni)
    return [c for c in buoni if t0 + avvio_ms <= c["t1"] <= t9 - coda_ms]


def p1_ritardo_noto(giri, tolleranza_ms=3.0):
    """⛔ IL CONTROLLO DECISIVO.  Il ponte ritarda di N, la mediana DEVE salire
    di esattamente N.

    ⚠ La tolleranza sta sulla GRANDEZZA VERA del fenomeno (`LEZIONI.md` §1.13):
      3 ms e' la somma di (a) l'errore dell'ancora dell'orologio, (b) lo scarto
      di consegna del ponte misurato dalla sua certificazione (~0,3 ms), e
      (c) mezzo intervallo di quadro di rumore sulla mediana.  Non e' un numero
      scelto perche' fa passare.
    """
    base = [g for g in giri if g.get("ritardo_chiesto_ms") == 0]
    if not base:
        return {"esito": False, "perche": "⛔ manca il giro a ritardo 0: senza "
                                          "base non si puo' dire «e' salita»"}
    # ⛔ «zero campioni» non e' un numero: si dice, non si esplode.
    if not (base[0].get("distribuzione") or {}).get("n"):
        return {"esito": False,
                "perche": "⛔ il giro a ritardo 0 non ha NESSUN campione: non e' "
                          "«la mediana non e' salita», e' «non ho misurato»"}
    m0 = base[0]["distribuzione"]["mediana"]
    righe, buono = [], True
    for g in giri:
        n = g.get("ritardo_chiesto_ms")
        if not n:
            continue
        d = g.get("distribuzione") or {}
        if not d.get("n"):
            righe.append({"n_ms": n, "salita_ms": None,
                          "perche": "nessun campione"})
            buono = False
            continue
        salita = d["mediana"] - m0
        va = abs(salita - n) <= tolleranza_ms
        righe.append({"n_ms": n, "salita_ms": round(salita, 2),
                      "scarto_ms": round(salita - n, 2), "esito": va,
                      "campioni": d["n"]})
        buono = buono and va
    if not righe:
        return {"esito": False,
                "perche": "⛔ nessun giro con ritardo iniettato: P1 NON e' stato "
                          "eseguito.  ⚠ Non e' «passato»: e' «non fatto», ed e' "
                          "il caso in cui il banco non sa di misurare"}
    return {"esito": buono, "mediana_base_ms": m0, "righe": righe,
            "tolleranza_ms": tolleranza_ms}


def p2_trova_quel_che_c_e(campioni):
    """Il rilevatore trova la marca CHE C'E'."""
    con = [c for c in campioni if c.get("visto")]
    letti = [c for c in con if c.get("marca", {}).get("c_e")]
    if not con:
        return {"esito": False,
                "perche": "⛔ nessun fotogramma con i pixel letti: non e' «la "
                          "marca non c'era», e' «non ho potuto guardare»"}
    q = len(letti) / len(con)
    # ⛔⭐ E LA QUOTA DA SOLA NON BASTA: CONTA IL MOTIVO DEL RIFIUTO.
    #
    #     `[M]` 13 agosto 2026, sulla catena vera: il 9,5 % dei fotogrammi
    #     guardati viene RIFIUTATO dal lettore certificato con «il sync c'e' ma
    #     il CRC non torna — letto 0x1271, calcolato 0x1273».  ⭐ Non e' un
    #     difetto: il codificatore aggiorna il blocco della marca **a pezzi**,
    #     quindi in quei fotogrammi meta' delle celle sono del disegno prima e
    #     meta' di quello dopo.  Il CRC lo vede e la respinge — che e'
    #     esattamente il comportamento per cui esiste.
    #
    #     ⛔ Senza quel CRC, il banco avrebbe letto un carico mescolato e ne
    #        avrebbe ricavato un istante di disegno **plausibile e falso**: e'
    #        la stessa forma d'errore di P3, un fotogramma alla volta.
    #
    #     ⇒ Qui si pretendono due cose diverse: che la maggioranza si legga
    #       (la soglia sta sulla grandezza vera, `LEZIONI.md` §1.13), e che
    #       **nessun rifiuto sia della specie «non ho potuto guardare»** —
    #       quello vorrebbe dire che il banco non sta guardando i pixel.
    motivi = {}
    ciechi = 0
    for c in con:
        if c["marca"].get("c_e"):
            continue
        p = c["marca"].get("perche") or "(senza motivo)"
        if "CRC" in p:
            k = "il CRC non torna (marca a meta' fra due disegni)"
        elif "contrasto" in p:
            k = "contrasto sotto il minimo"
        elif "sync" in p:
            k = "il sync non c'e'"
        elif "non ho potuto GUARDARE" in p or "nessun pixel" in p:
            k = "⛔ NON HO POTUTO GUARDARE"
            ciechi += 1
        else:
            k = p[:60]
        motivi[k] = motivi.get(k, 0) + 1
    buono = q >= 0.80 and ciechi == 0
    return {"esito": buono, "letti": len(letti), "guardati": len(con),
            "quota": round(q, 4), "motivi_del_rifiuto": motivi,
            "ciechi": ciechi,
            "contrasto": dist([c["marca"]["contrasto"] for c in letti]),
            "perche": None if buono else
                      ("⛔ %d fotogrammi guardati senza poter guardare" % ciechi
                       if ciechi else
                       "solo il %.1f%% dei fotogrammi guardati porta una marca "
                       "leggibile, e la soglia e' 80 %%" % (q * 100))}


def p3_non_trova_quel_che_non_c_e(campioni, senza_marca, disegni_attesi=True):
    """⛔ IL CONTROLLO CADUTO IN v1, E IL PIU' IMPORTANTE DI TUTTI.

    «Se dice sempre si', si sta misurando zero e si e' felici a torto» — ⛔ e un
    rilevatore che dice sempre si' **passa anche P1**, perche' gli N ms si
    sommano identici a qualunque numero inventato.  ⇒ P1 da solo non basta, e
    questo e' il motivo.

    Tre setacci, e servono tutti e tre:
      a) sui fotogrammi SENZA marca il lettore deve dire NO, e con un `perche`;
      b) il `disegno` letto deve CRESCERE: un rilevatore che inventa un numero
         costante o casuale non produce una successione crescente;
      c) l'istante letto deve stare in una finestra sensata rispetto al `pts`
         dei 28 byte — due orologi dello STESSO server.
    """
    fuori = {}
    # (a)
    falsi = [c for c in senza_marca if c.get("marca", {}).get("c_e")]
    fuori["a_falsi_positivi"] = len(falsi)
    fuori["a_guardati"] = len(senza_marca)
    fuori["a_esito"] = (len(senza_marca) > 0 and not falsi)
    if not senza_marca:
        fuori["a_perche"] = ("⛔ nessun fotogramma senza marca da mostrargli: "
                             "P3(a) NON e' stato eseguito, e un P3 non eseguito "
                             "e' esattamente il caso di v1")
    # (b)
    letti = [c for c in campioni if c.get("marca", {}).get("c_e")]
    dis = [c["marca"]["disegno"] for c in letti]
    cresce = sum(1 for x, y in zip(dis, dis[1:]) if y > x)
    indietro = sum(1 for x, y in zip(dis, dis[1:]) if y < x)
    fuori["b_cresciuti"] = cresce
    fuori["b_indietro"] = indietro
    fuori["b_distinti"] = len(set(dis))
    fuori["b_esito"] = (len(dis) > 20 and len(set(dis)) > 0.5 * len(dis)
                        and cresce > 5 * max(1, indietro)) if disegni_attesi else True
    # (c)
    scarti = [c["marca"]["istante_us"] - c["pts"] for c in letti if c.get("pts")]
    fuori["c_scarto_disegno_cattura_us"] = dist(scarti)
    # ⛔ Il disegno viene PRIMA della cattura: lo scarto deve essere negativo o
    #    quasi nullo, e mai piu' vecchio di un secondo.  Un rilevatore che
    #    inventasse l'istante non starebbe in questa finestra per costruzione.
    dentro = [s for s in scarti if -1000000 <= s <= 5000]
    fuori["c_dentro"] = len(dentro)
    fuori["c_guardati"] = len(scarti)
    fuori["c_esito"] = bool(scarti) and len(dentro) >= 0.95 * len(scarti)
    fuori["esito"] = bool(fuori["a_esito"] and fuori["b_esito"] and fuori["c_esito"])
    return fuori


def p5_fuori_ordine(campioni):
    """⛔ I fotogrammi arrivano su stream indipendenti.  Un anello che non lo
    regge misura la coda invece del ritardo.

    ⭐ Questo anello lo regge PER COSTRUZIONE — accoppia `t0` e `t1` dal
       CONTENUTO (la marca nei pixel, il `pts` nei 28 byte), non dall'ordine —
       e il controllo lo DIMOSTRA invece di dichiararlo: si conta quanti
       fotogrammi sono arrivati fuori ordine, e si verifica che il ritardo dei
       fuori ordine e quello degli altri vengano dalla stessa distribuzione.
    """
    ord_ = [c for c in campioni if c.get("numero") is not None]
    if len(ord_) < 20:
        return {"esito": False,
                "perche": "⛔ meno di 20 fotogrammi con un `numero`: non ho "
                          "potuto guardare l'ordine"}
    scavalcati = 0
    massimo = None
    for c in ord_:
        if massimo is not None and c["numero"] < massimo:
            scavalcati += 1
            c["scavalcato"] = True
        else:
            massimo = c["numero"]
    a = [c["ritardo_ms"] for c in ord_ if c.get("scavalcato")]
    b = [c["ritardo_ms"] for c in ord_ if not c.get("scavalcato")]
    d_a, d_b = dist(a), dist(b)
    # ⛔ Il controllo non e' «non ce ne sono»: e' «anche quando ce ne sono, il
    #    numero non cambia».  Un anello che misurasse la CODA vedrebbe i
    #    fuori ordine con un ritardo sistematicamente diverso.
    coerente = True
    if d_a["n"] >= 5 and d_b["n"] >= 5:
        coerente = abs(d_a["mediana"] - d_b["mediana"]) <= max(
            8.0, 0.4 * d_b["mediana"])
    # ⛔⭐ «NESSUNO SCAVALCATO» NON E' «REGGE IL FUORI ORDINE»: e' «il fuori
    #     ordine non e' successo».  `LEZIONI.md` §1.9 applicata a un controllo
    #     invece che a una lettura.  `[M]` 13 agosto 2026: sul giro normale gli
    #     scavalcati sono 0 su 783, e un P5 dichiarato verde li' sarebbe verde
    #     PER COSTRUZIONE — il caso che questo banco esiste per non fare.
    if scavalcati == 0:
        return {"esito": False, "scavalcati": 0, "totali": len(ord_),
                "quota": 0.0, "ritardo_in_ordine": dist(b),
                "perche": "⛔ NON ESEGUITO: nessuno dei %d fotogrammi e' arrivato "
                          "fuori ordine, quindi non c'e' niente da reggere.  "
                          "⚠ Non e' «l'anello regge»: e' «il fenomeno non si e' "
                          "presentato»" % len(ord_)}
    return {"esito": coerente, "scavalcati": scavalcati, "totali": len(ord_),
            "quota": round(scavalcati / len(ord_), 4),
            "ritardo_scavalcati": d_a, "ritardo_in_ordine": d_b,
            "perche": None if coerente else
                      "⛔ i fotogrammi scavalcati hanno una mediana di %.1f ms "
                      "contro %.1f: l'anello sta misurando la coda"
                      % (d_a["mediana"], d_b["mediana"])}


def p6_grana(grana, isolata):
    """⛔ Vincolo di PRODOTTO, non taratura del banco (`SPECIFICHE.md` §11.5)."""
    if not grana:
        return {"esito": False, "perche": "⛔ la grana non e' stata misurata"}
    m = grana.get("minimo_ms")
    return {"esito": bool(isolata) and m is not None and m < 0.5,
            "isolata": isolata, "grana_minima_ms": m,
            "grana_mediana_ms": grana.get("mediano_ms"),
            "salti": grana.get("salti"),
            "perche": None if isolata else
                      "⛔ `crossOriginIsolated` e' %s: senza COOP+COEP i "
                      "cronometri cadono su una griglia da 1 ms, su un tetto "
                      "di 50" % isolata}


def p7_ritmo(campioni, conti_pagina):
    """Il ritmo consegnato dice se stai misurando la strada che credi."""
    r = regime(campioni)
    if len(r) < 20:
        return {"esito": False,
                "perche": "⛔ meno di 20 fotogrammi a regime: il ritmo non si "
                          "misura su un campione"}
    durata = (max(c["t1"] for c in r) - min(c["t1"] for c in r)) / 1000.0
    # ⛔ IL RITMO SI FA SUGLI INTERVALLI, NON SU «QUANTI DIVISO QUANTO».
    #    I campioni di un giro sono raccolti a FETTE ALTERNATE (§6): fra una
    #    fetta e l'altra passano i secondi degli altri valori di N, e
    #    dividere il totale per la durata li conta come fotogrammi mancanti.
    #    `[M]` 13 agosto 2026: il conto ingenuo diceva 6,53 al secondo di una
    #    catena che ne consegnava 23.
    inter = sorted(b["t1"] - a["t1"] for a, b in zip(r, r[1:])
                   if 0 < b["t1"] - a["t1"] < 500)
    fps = round(1000.0 / inter[len(inter) // 2], 2) if inter else 0
    return {"esito": fps > 5, "fotogrammi_al_secondo": fps,
            "durata_s": round(durata, 2), "fette": "⚠ raccolte a fette alternate", "dipinti_dalla_pagina": (conti_pagina or {}).get("dipinti"),
            "intervallo_ms": dist(inter),
            "perche": None if fps > 5 else
                      "⛔ %0.1f fotogrammi al secondo: non si sta misurando un "
                      "desktop che si muove" % fps}


def p8_costo_del_banco(costo_us, senza_lettura, con_lettura):
    """⛔ Quel che il banco AGGIUNGE si misura, o e' un errore sistematico."""
    d = dist(costo_us, 0.001)
    fuori = {"lettura_pixel_ms": d}
    if senza_lettura and con_lettura:
        fuori["fps_senza_lettura"] = senza_lettura
        fuori["fps_con_lettura"] = con_lettura
        cala = (senza_lettura - con_lettura) / senza_lettura if senza_lettura else 1
        fuori["calo_di_ritmo"] = round(cala, 4)
        fuori["esito"] = cala < 0.10
        if not fuori["esito"]:
            fuori["perche"] = ("⛔ la lettura dei pixel toglie il %.1f%% del "
                               "ritmo: il banco si sta misurando addosso"
                               % (cala * 100))
    else:
        fuori["esito"] = d.get("n", 0) > 0 and d.get("p95", 99) < 3.0
        fuori["perche"] = ("⚠ il confronto con/senza lettura non e' stato fatto: "
                           "si dichiara il solo costo della lettura")
    return fuori


TUTTI = ["P1", "P2", "P3", "P5", "P6", "P7", "P8"]


def giudica(verbale):
    """Tutti i controlli, su un verbale.  ⛔ Funzione PURA."""
    g = verbale.get("giri", [])
    base = next((x for x in g if x.get("ritardo_chiesto_ms") == 0), None)
    camp = (base or {}).get("campioni", [])
    return {
        "P1": p1_ritardo_noto(g),
        "P2": p2_trova_quel_che_c_e(camp),
        "P3": p3_non_trova_quel_che_non_c_e(
            camp, verbale.get("senza_marca", [])),
        # ⛔⭐ P5 SI GIUDICA DOVE IL FENOMENO C'E', NON DOVE NON C'E'.
        #
        #     `[M]` 13 agosto 2026: sul giro normale i fotogrammi fuori ordine
        #     sono **0 su 783** — su questa LAN, con delta da 2,6 KB, lo
        #     scavalcamento per dimensione non si presenta.  ⛔ Un P5 giudicato
        #     li' sarebbe VERDE PER COSTRUZIONE, che e' peggio di un rosso
        #     (`LEZIONI.md` §1.3, §2.2).  ⇒ Si giudica sul giro in cui il fuori
        #     ordine e' stato FABBRICATO dal ponte; il giro normale resta
        #     accanto come misura di quanto spesso accade da solo.
        "P5": p5_fuori_ordine(
            regime((verbale.get("giro_p5") or {}).get("campioni") or [])
            or regime(camp)),
        "P5_spontaneo": p5_fuori_ordine(regime(camp)),
        "P6": p6_grana(verbale.get("grana"), verbale.get("isolata")),
        "P7": p7_ritmo(camp, verbale.get("conti_pagina")),
        "P8": p8_costo_del_banco(verbale.get("costo_lettura_us", []),
                                 verbale.get("fps_senza_lettura"),
                                 verbale.get("fps_con_lettura")),
    }


# ═══════════════════════════════════════════════════════════════════════════
# §6  LA CERTIFICAZIONE — sano → guasto → RISANATO, e a tre giri
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `LEZIONI.md` §1.2: il banco si certifica PRIMA della misura.  E a TRE giri,
#    non a due: un controllo che diventa rosso col guasto ma non torna verde
#    quando lo si toglie sta bocciando qualcos'altro.
def verbale_sintetico(seme=7, quanti=900, ritardi=(0, 25, 60), ritardo_vero_ms=22.0):
    """Un verbale finto ma della forma vera: serve a certificare i GIUDICI."""
    m = marca_modulo()
    rnd = random.Random(seme)
    giri = []
    t_base = 1000.0
    disegno = 1000
    for n in ritardi:
        campioni = []
        t = t_base
        for i in range(quanti):
            t += rnd.gauss(16.7, 2.0)
            disegno += 1
            ritardo = ritardo_vero_ms + n + rnd.gauss(0, 3.0)
            istante_disegno_us = int((t - ritardo) * 1000) + 500000000
            campioni.append({
                "t1": t, "t_dip": t + 0.4, "t_let": t + 0.9,
                "pts": istante_disegno_us + rnd.randint(2000, 9000),
                "numero": i + 1, "tipo": 0x0301 if i == 0 else 0x0302,
                "byte": 4000 + rnd.randint(0, 2000), "input": 0,
                "t_primo": t - 3.0, "t_ultimo": t - 1.2, "t_dec": t - 1.0,
                "ritardo_ms": ritardo,
                "ritardo_al_richiamo_ms": ritardo - 9.0,
                "ritardo_cattura_disegno_ms": ritardo - 12.0,
                "marca": {"c_e": True, "disegno": disegno,
                          "istante_us": istante_disegno_us,
                          "giro": m.fnv1a32("b17-finto"), "contrasto": 0.9},
                "celle": [0.0, 255.0] * 72, "visto": True,
            })
        giri.append({"ritardo_chiesto_ms": n, "campioni": campioni,
                     "distribuzione": dist([c["ritardo_ms"] for c in regime(campioni)])})
    # ⛔ Il giro «sano» deve contenere dei fuori ordine, o P5 direbbe «non
    #    eseguito» e la certificazione non proverebbe niente su di lui.
    for k, c in enumerate(giri[0]["campioni"]):
        if k % 23 == 11 and k > 0:
            c["numero"] = max(1, c["numero"] - 2)
    senza = [{"celle": [rnd.random() * 255.0 for _ in range(144)], "visto": True,
              "marca": {"c_e": False, "perche": "rumore"}} for _ in range(120)]
    return {"giri": giri, "senza_marca": senza,
            "grana": {"salti": 4000, "minimo_ms": 0.005, "mediano_ms": 0.02},
            "isolata": True, "conti_pagina": {"dipinti": quanti},
            "costo_lettura_us": [rnd.gauss(600, 120) for _ in range(500)],
            "fps_senza_lettura": 59.8, "fps_con_lettura": 58.9}


# I guasti: ciascuno rompe UNA cosa, e si dichiara QUALE controllo deve
# accorgersene e quali devono restare verdi.
def _g_p1_non_ritarda(v):
    """Il ponte non ritarda: tutte le distribuzioni identiche.  ⛔ E' il caso in
    cui il banco «non sa di misurare»."""
    base = v["giri"][0]
    for g in v["giri"][1:]:
        g["distribuzione"] = dict(base["distribuzione"])
    return v


def _g_p1_meta(v):
    """⛔ IL GUASTO CHE UN BANCO INGENUO NON VEDE: l'ancora dell'orologio passa
    dal ritardatore, quindi la mediana sale di N/2 invece che di N."""
    base = v["giri"][0]["distribuzione"]["mediana"]
    for g in v["giri"][1:]:
        n = g["ritardo_chiesto_ms"]
        g["distribuzione"]["mediana"] = base + n / 2.0
    return v


def _g_p2_marca_illeggibile(v):
    for g in v["giri"]:
        for c in g["campioni"]:
            c["marca"] = {"c_e": False, "perche": "contrasto sotto il minimo"}
    return v


def _g_p3_dice_sempre_si(v):
    """⛔⛔ IL GUASTO DI v1: il rilevatore dice sempre «ho visto la marca».
    ⚠ E si noti che P1 resta VERDE: gli N ms si sommano identici."""
    for c in v["senza_marca"]:
        c["marca"] = {"c_e": True, "disegno": 1, "istante_us": 0,
                      "giro": 0, "contrasto": 0.9}
    return v


def _g_p3_disegno_fermo(v):
    for g in v["giri"]:
        for c in g["campioni"]:
            if c["marca"].get("c_e"):
                c["marca"]["disegno"] = 4242
    return v


def _g_p3_istante_inventato(v):
    for g in v["giri"]:
        for c in g["campioni"]:
            if c["marca"].get("c_e"):
                c["marca"]["istante_us"] = c["pts"] + 900000
    return v


def _g_p5_coda(v):
    """L'anello misura la coda: i fotogrammi scavalcati hanno un ritardo
    sistematicamente diverso."""
    g = v["giri"][0]
    for i, c in enumerate(g["campioni"]):
        if i % 7 == 3 and i > 0:
            c["numero"] = max(1, c["numero"] - 3)
            c["ritardo_ms"] += 45.0
    return v


def _g_p6_non_isolata(v):
    v["isolata"] = False
    v["grana"] = {"salti": 4000, "minimo_ms": 1.0, "mediano_ms": 1.0}
    return v


def _g_p7_ritmo_morto(v):
    for g in v["giri"]:
        g["campioni"] = g["campioni"][:15]
    return v


def _g_p8_banco_caro(v):
    v["fps_con_lettura"] = 31.0
    v["costo_lettura_us"] = [9000.0] * 500
    return v


GUASTI = [
    ("P1 il ponte non ritarda", _g_p1_non_ritarda, ["P1"]),
    ("P1 la mediana sale di META' di N", _g_p1_meta, ["P1"]),
    ("P2 la marca non si legge piu'", _g_p2_marca_illeggibile, ["P2", "P3"]),
    ("P3 il rilevatore dice SEMPRE si'", _g_p3_dice_sempre_si, ["P3"]),
    ("P3 il `disegno` non cresce", _g_p3_disegno_fermo, ["P3"]),
    ("P3 l'istante e' inventato", _g_p3_istante_inventato, ["P3"]),
    ("P5 l'anello misura la coda", _g_p5_coda, ["P5"]),
    ("P6 la pagina non e' isolata", _g_p6_non_isolata, ["P6"]),
    ("P7 il ritmo e' morto", _g_p7_ritmo_morto, ["P7"]),
    ("P8 il banco costa mezzo ritmo", _g_p8_banco_caro, ["P8"]),
]


def certifica(verboso=True):
    import copy
    esiti = []

    def dice(t, buono):
        esiti.append({"controllo": t, "esito": bool(buono)})
        (ok if buono else ko)(t)

    log("A. Il PONTE — il ritardo noto e l'ancora dell'orologio")
    p = ponte_modulo()
    rp = p.certifica(verboso=verboso)
    dice("il ponte e' %s (%d controlli su %d)"
         % (rp["esito"], rp["passati"], rp["controlli"]),
         rp["esito"] == "PROMOSSO")

    log("B. Il LETTORE della marca, sul percorso di QUESTO banco")
    m = marca_modulo()
    np = m.np_o_muori("03-b17: la certificazione del lettore")
    # ⭐ P2 sintetico: si dipinge una marca nota, si campiona come fa il
    #    JavaScript, e la si rilegge col lettore certificato.
    giusti = 0
    for i in range(60):
        disegno, istante = 1000 + i, 123456789000 + i * 16667
        img = np.zeros((300, 520, 3), dtype=np.uint8)
        m.dipingi_marca(img, disegno, istante, m.fnv1a32("b17"))
        y = (img[:, :, :3].astype(np.float64) @ m.PESI_LUMA) / 255.0
        # ⛔ `_celle()` da' 0-1; l'acquisizione da' 0-255.  Si certifica
        #    nell'unita' DELL'ACQUISIZIONE, o si certifica un percorso che non
        #    esiste — ed e' esattamente quel che era successo.
        celle = [float(x) * 255.0 for x in m._celle(y, m.GEOMETRIA, 0, 0)]
        r = leggi_celle(celle)
        if (r.get("c_e") and r["disegno"] == disegno
                and r["istante_us"] == istante):
            giusti += 1
    dice("P2 sintetico: 60 marche dipinte e rilette dal campionamento a celle "
         "(%d giuste su 60)" % giusti, giusti == 60)

    # ⛔ P3 sintetico, sullo STESSO percorso: rumore che passa dalla sintesi.
    rnd = random.Random(11)
    falsi = 0
    for _ in range(3000):
        celle = [rnd.random() * 255.0 for _ in range(144)]
        if leggi_celle(celle).get("c_e"):
            falsi += 1
    dice("P3 sintetico: 3000 rumori attraverso la sintesi a celle → %d falsi "
         "positivi (attesi 0)" % falsi, falsi == 0)
    # e il rumore BINARIO, che ha la stessa statistica della marca
    falsi_b = 0
    for _ in range(3000):
        celle = [rnd.choice((5.0, 250.0)) for _ in range(144)]
        if leggi_celle(celle).get("c_e"):
            falsi_b += 1
    buona, perche = celle_unita_giusta([0.0] * 143 + [254.0])
    cattiva, _ = celle_unita_giusta([0.0] * 143 + [0.99])
    dice("l'unita' delle celle e' controllata: 0-255 passa, 0-1 NON passa",
         buona and not cattiva)
    dice("P3 sintetico: 3000 rumori BINARI (stessa statistica della marca) → "
         "%d falsi positivi (attesi 0)" % falsi_b, falsi_b == 0)

    log("C. I GIUDICI — tre giri: sano → guasto → RISANATO")
    sano = verbale_sintetico()
    g_sano = giudica(sano)
    verdi = [k for k in TUTTI if g_sano[k].get("esito")]
    dice("giro SANO: tutti e sette i controlli sono verdi (%s)"
         % ", ".join(verdi), len(verdi) == len(TUTTI))
    if len(verdi) != len(TUTTI):
        for k in TUTTI:
            if not g_sano[k].get("esito"):
                inf("  ⛔ %s: %s" % (k, json.dumps(g_sano[k], ensure_ascii=False)[:300]))

    for nome, rompi, attesi in GUASTI:
        v = rompi(copy.deepcopy(verbale_sintetico()))
        gg = giudica(v)
        rossi = [k for k in TUTTI if not gg[k].get("esito")]
        # il guasto DEVE far diventare rossi quelli attesi...
        preso = all(k in rossi for k in attesi)
        # ...e ⛔ NON deve far diventare rosso nient'altro di inatteso, o il
        #    controllo non sta distinguendo: e' `LEZIONI.md` §2.3, una prova che
        #    boccia il codice giusto costa quanto una che promuove lo sbagliato.
        extra = [k for k in rossi if k not in attesi]
        dice("guasto «%s» → rossi %s (attesi %s)%s"
             % (nome, rossi or "nessuno", attesi,
                "  ⚠ e ne sporca altri: %s" % extra if extra else ""),
             preso)
        # RISANATO: si toglie il guasto e si ripretende il verde
        g2 = giudica(verbale_sintetico())
        dice("  risanato «%s»: torna tutto verde" % nome,
             all(g2[k].get("esito") for k in TUTTI))

    log("D. Gli attrezzi che dicono «non ho potuto guardare»")
    dice("P1 senza il giro a ritardo 0 → NON passa",
         not p1_ritardo_noto([{"ritardo_chiesto_ms": 30,
                               "distribuzione": dist([1, 2, 3])}])["esito"])
    dice("P1 senza NESSUN giro iniettato → NON passa, e dice «non fatto»",
         (lambda r: (not r["esito"]) and "non fatto" in (r.get("perche") or ""))(
             p1_ritardo_noto([{"ritardo_chiesto_ms": 0,
                               "distribuzione": dist([10, 11, 12])}])))
    dice("P2 senza un pixel guardato → NON passa, e dice «non ho potuto»",
         (lambda r: (not r["esito"]) and "non ho potuto" in (r.get("perche") or ""))(
             p2_trova_quel_che_c_e([])))
    dice("P3 senza fotogrammi senza marca → NON passa (P3 non eseguito)",
         not p3_non_trova_quel_che_non_c_e(
             sano["giri"][0]["campioni"], [])["esito"])
    dice("il pezzo cieco compare in ogni numero stampato",
         "pezzo cieco" in con_pezzo_cieco(30.0))

    passati = sum(1 for e in esiti if e["esito"])
    print()
    esito = "PROMOSSO" if passati == len(esiti) else "BOCCIATO"
    (ok if esito == "PROMOSSO" else ko)(
        "%s — %d controlli su %d" % (esito, passati, len(esiti)))
    return {"esito": esito, "controlli": len(esiti), "passati": passati,
            "esiti": esiti, "ponte": rp}


# ═══════════════════════════════════════════════════════════════════════════
# §7  LA SCOMPOSIZIONE E IL VERDETTO
# ═══════════════════════════════════════════════════════════════════════════
def scomponi(campioni):
    """⭐ Quel che rende il numero UTILE invece che solo vero.

    ⛔ Tutti i tratti si misurano SUL FOTOGRAMMA, non su medie di grandezze
       diverse: ogni riga qui sotto e' una differenza fra due istanti dello
       STESSO fotogramma.
    """
    def d(f):
        return dist([f(c) for c in campioni if f(c) is not None])

    return {
        "1 disegno → cattura (scena → `pts` di Mutter)":
            d(lambda c: (c["pts"] - c["marca"]["istante_us"]) / 1000.0
              if c.get("marca", {}).get("c_e") and c.get("pts") else None),
        "2 cattura → PRIMO byte in pagina (codifica + filo)":
            d(lambda c: c.get("t_primo_server_ms") - c["pts"] / 1000.0
              if c.get("t_primo_server_ms") and c.get("pts") else None),
        "3 primo byte → ULTIMO byte (lo stream sul filo)":
            d(lambda c: c["t_ultimo"] - c["t_primo"]
              if c.get("t_ultimo") and c.get("t_primo") else None),
        "4 stream completo → richiamo di `decode()`":
            d(lambda c: c["t_dec"] - c["t_ultimo"]
              if c.get("t_dec") and c.get("t_ultimo") else None),
        "5 `decode()` → richiamo del decodificatore (la decodifica)":
            d(lambda c: c["t1"] - c["t_dec"] if c.get("t_dec") else None),
        "6 richiamo → disegno finito (`drawImage` ×2)":
            d(lambda c: c["t_dip"] - c["t1"]),
        "7 ⭐ TOTALE disegno → DISEGNO FINITO (il numero del banco)":
            d(lambda c: c.get("ritardo_ms")),
        "7a  di cui fino al RICHIAMO del decodificatore (prima di dipingere)":
            d(lambda c: c.get("ritardo_al_richiamo_ms")),
        "7b TOTALE cattura → disegno finito (senza il pezzo della scena)":
            d(lambda c: c.get("ritardo_cattura_disegno_ms")),
        "8 ⛔ [?] disegno → PIXEL ACCESO (pezzo cieco, nessuna API lo vede)":
            {"stima_ms": [CIECO_MIN_MS, CIECO_MAX_MS], "marca": "[?]",
             "fonte": "STUDI.md §web §6.2",
             "nota": "⚠ su Xvfb non c'e' compositore: in QUESTO ambiente non "
                     "esiste affatto.  La stima e' per lo schermo di un utente"},
    }


def verdetto(d, errore_orologio_us=0):
    """⛔ Il verdetto contro 50 e contro 40, col pezzo cieco accanto."""
    if not d or not d.get("n"):
        return {"esito": "NON MISURATO",
                "perche": "⛔ nessun campione: non e' «passa», e' «non so»"}
    med, p95 = d["mediana"], d["p95"]
    e = errore_orologio_us / 1000.0
    return {
        "mediana_ms": med, "p95_ms": p95, "p99_ms": d["p99"], "max_ms": d["max"],
        "errore_orologio_ms": round(e, 3),
        "contro_50": "PASSA" if med + e <= 50 else "SFORA",
        "contro_50_al_p95": "PASSA" if p95 + e <= 50 else "SFORA",
        "contro_40": "PASSA" if med + e <= 40 else "SFORA",
        "contro_40_al_p95": "PASSA" if p95 + e <= 40 else "SFORA",
        "letto_con_il_pezzo_cieco": con_pezzo_cieco(med),
        "⛔": "il pezzo cieco NON e' compreso nei numeri qui sopra: `SPECIFICHE.md` "
              "§3.2 misura «solo il pezzo che e' nostro», e i 16-40 ms del "
              "compositore non lo sono.  Si DICHIARA, non si promette",
    }


# ═══════════════════════════════════════════════════════════════════════════
# §7-bis  LA MISURA — sulla catena vera
# ═══════════════════════════════════════════════════════════════════════════
STATO = """
(function () {
  const R = window.REMOTIX, s = R && R.schermo, B = window.__B17;
  return { pronto: !!(R && s), banco: !!B,
           conti: s ? Object.assign({}, s.conti) : null,
           dichiarazione: (document.getElementById("dichiarazione") || {}).textContent,
           registro: ((document.getElementById("registro") || {}).textContent || "").slice(-900),
           schermo: document.body.dataset.schermo || null,
           deposito: s && s.deposito ? [s.deposito.width, s.deposito.height] : null };
})()
"""


def _sshpw(comando, silenzioso=False):
    """⛔ MAI una redirezione ATTORNO a `ssh`: la richiesta della parola di
    `sudo` va sullo stderr, e una redirezione la mangia — il comando resta
    appeso per sempre, in silenzio.  Pagata sei volte (`03-b15-lancia.sh:18`)."""
    r = subprocess.run(["python3", os.path.join(RADICE, "v1/strumenti/sshpw.py"),
                        comando], capture_output=True, text=True, timeout=300)
    if not silenzioso and r.returncode != 0:
        dub("ssh ha risposto %d: %s" % (r.returncode, (r.stderr or "")[-200:]))
    return r


def metti_ritardo(a, ritardo_ms, fuori_ordine=0, giro="-", fo_ms=45.0,
                  raffica=4):
    """Cambia il ritardo del ponte SENZA riaccenderlo.  ⛔ Riaccenderlo
    riaccenderebbe la sessione QUIC, e si confronterebbero distribuzioni prese
    in condizioni diverse."""
    testo = ("ritardo_ms=%s\\nfuori_ordine=%d\\nfuori_ordine_ms=%s\\n"
             "fuori_ordine_raffica=%d\\ngiro=%s\\n"
             % (ritardo_ms, fuori_ordine, fo_ms, raffica, giro))
    if a.host in ("127.0.0.1", "localhost"):
        with open(a.comando_ponte, "w") as f:
            f.write(testo.replace("\\n", "\n"))
        return True
    r = _sshpw("printf '%s' > %s" % (testo, a.comando_ponte))
    return r.returncode == 0


def raccogli(c, quanto_s, passo_s=1.5):
    """Ritira i campioni dalla pagina, a fette.  ⛔ Si ritira ANCHE durante,
    non solo alla fine: 25 s di campioni a 60/s sono 1500 fotogrammi × 144
    celle, e tenerli tutti nella pagina prima di portarli fuori vorrebbe dire
    misurare anche la pressione sul mucchio del browser."""
    fine = time.time() + quanto_s
    campioni, crudi, costo = [], [], []
    ultimo = None
    while time.time() < fine:
        time.sleep(min(passo_s, max(0.05, fine - time.time())))
        r = c.valuta("window.__B17 ? window.__B17.prendi() : null", attendi=False)
        if not isinstance(r, dict):
            continue
        campioni += r.get("campioni") or []
        crudi += r.get("crudi") or []
        costo += r.get("costo_lettura_us") or []
        ultimo = r
    return campioni, crudi, costo, ultimo


def arricchisci(campioni, orologi):
    """Da campioni grezzi a campioni con il RITARDO dentro.

    ⛔ Il lettore della marca e' quello CERTIFICATO: qui non si decide niente
       sui pixel, si chiama `03-marca.py`.
    """
    fuori = []
    for c in campioni:
        # ⛔⭐ SI RILEGGE LA MARCA UNA VOLTA SOLA, E QUESTA RIGA E' NATA DA UN
        #     DIFETTO MISURATO — `[M]` 13 agosto 2026, primo giro dal vivo.
        #
        #     Questa funzione viene chiamata DUE volte sugli stessi campioni:
        #     una col solo scarto d'apertura, e una col conto rifatto sulle due
        #     ancore (la deriva si spalma).  ⛔ La prima passata consumava
        #     `celle`; la seconda non le trovava piu' e riscriveva la marca a
        #     «nessun pixel letto», **cancellando 264 letture buone**.  Il
        #     sintomo era «zero campioni» con la catena, la scena e il lettore
        #     tutti perfettamente funzionanti — cioe' un rosso puntato
        #     sull'imputato sbagliato, dentro il banco stesso.
        if "marca" not in c:
            celle = c.get("celle")
            if celle:
                va, perche = celle_unita_giusta(celle)
                c["marca"] = (leggi_celle(celle) if va
                              else {"c_e": False, "perche": perche})
            else:
                c["marca"] = {"c_e": False,
                              "perche": "⛔ nessun pixel letto per questo "
                                        "fotogramma (deposito assente o troppo "
                                        "piccolo): non e' «la marca non c'era»"}
            c.pop("celle", None)
        t1s = orologi.a_server_us(c["t1"]) if orologi.utilizzabile() else None
        c["t1_server_us"] = t1s
        if c.get("t_primo") is not None and t1s is not None:
            c["t_primo_server_ms"] = orologi.a_server_us(c["t_primo"]) / 1000.0
        # ⛔⭐ DOVE FINISCE IL NUMERO, E LA PRIMA STESURA LO CHIUDEVA TROPPO
        #     PRESTO — corretto il 13 agosto 2026, a numeri gia' in mano.
        #
        #     `STUDI.md` §web §6.3 costruisce l'anello con `t1` come prima riga del
        #     richiamo; ma §6.2 dice che il pezzo cieco sta «fra **il disegno**
        #     e il pixel acceso».  ⇒ Il confine fra quel che si misura e quel
        #     che si stima non e' `t1`: e' la fine del DISEGNO.  Chiudere a
        #     `t1` regalava al numero gli 11,6 ms dei due `drawImage`, che sono
        #     NOSTRI, misurabili, e dentro il tetto dei 50.
        #
        #     ⚠ E la correzione va nella direzione scomoda: alza il numero.
        #       Si fa lo stesso — `LEZIONI.md` §0: non si tira per il verde.
        t_dip = orologi.a_server_us(c["t_dip"]) if orologi.utilizzabile() else None
        c["t_dip_server_us"] = t_dip
        if t1s is not None and c.get("pts"):
            c["ritardo_cattura_ms"] = (t1s - c["pts"]) / 1000.0
        if t_dip is not None and c.get("pts"):
            c["ritardo_cattura_disegno_ms"] = (t_dip - c["pts"]) / 1000.0
        if c["marca"].get("c_e"):
            if t1s is not None:
                c["ritardo_al_richiamo_ms"] = (t1s - c["marca"]["istante_us"]) / 1000.0
            if t_dip is not None:
                c["ritardo_ms"] = (t_dip - c["marca"]["istante_us"]) / 1000.0
        fuori.append(c)
    return fuori


def misura(a):
    os.makedirs(a.lavoro, exist_ok=True)
    p = ponte_modulo()
    m = marca_modulo()
    v = {"banco": "B17", "giro": a.giro, "host": a.host, "porta": a.porta,
         "giri": [], "senza_marca": [], "note": []}

    log("0. Le porte, CONTATE — 7448 · 7501 · 7561 non si toccano")
    r = _sshpw("ss -tuln | grep -E ':(7448|7501|7561|760[0-9]|761[0-9])\\b' | sort")
    prima_porte = r.stdout
    for riga in prima_porte.strip().splitlines():
        inf(riga.strip())
    v["porte_prima"] = prima_porte

    log("1. L'ANCORA DELL'OROLOGIO — ⛔ e NON passa dal ritardatore")
    parete = scarto_parete_monotono_us()
    inf("CHUWI: parete − monotono = %d us (errore %d us)"
        % (parete["scarto_us"], parete["errore_us"]))
    anc_a = p.orologio_chiedi(a.host, a.ancora, campioni=1200, pausa_s=0.0005)
    if not anc_a.get("c_e"):
        ko(anc_a["perche"])
        ko("⛔ senza ancora non si scrive nessun numero: due orologi monotoni di "
           "due macchine non hanno nessuna relazione")
        return 3
    ok("ancora: scarto %d us, errore %d us (giro minimo %d us su %d campioni)"
       % (anc_a["scarto_us"], anc_a["errore_us"], anc_a["giro_minimo_us"],
          anc_a["campioni"]))

    log("2. Il PALCO — Xvfb e Chrome")
    palco = Palco(a.schermo, a.diagnosi, (1500, 1000),
                  os.path.join(a.lavoro, "palco"), gpu=not a.senza_gpu)
    try:
        inf("Xvfb: " + palco.accendi())
        c = palco
        # ⛔ Il prologo si mette PRIMA di navigare: `addScriptToEvaluateOnNewDocument`
        #    gira prima di ogni script della pagina, che e' l'unico momento in cui
        #    si puo' avvolgere `VideoDecoder` senza toccare `pagina.html`.
        c.chiama("Page.addScriptToEvaluateOnNewDocument", source=PROLOGO)
        # ⛔ IL FRAMMENTO, non la stringa di ricerca: `src/pagina.c:243`
        #    confronta il bersaglio col `?` dentro e risponde 404 a
        #    `GET /?video=worker` (MISURATO il 13 agosto 2026).  Il frammento
        #    non viaggia sul filo, quindi arriva anche con quel difetto vivo.
        url = "https://%s:%d/%s" % (a.host, a.porta,
                                    "#video=worker" if a.video_worker else "")
        inf("apro " + url)
        c.chiama("Page.navigate", url=url)
        time.sleep(2.5)
        s = c.valuta(STATO, attendi=False)
        if not (isinstance(s, dict) and s.get("pronto")):
            # ⛔ L'interstiziale si BATTE, non si aggira con un flag.
            inf("interstiziale del certificato: batto «thisisunsafe»")
            batti(c, "thisisunsafe")
            time.sleep(2.5)
        s = aspetta(c, STATO, 30, lambda x: x.get("pronto"))
        if not (isinstance(s, dict) and s.get("pronto")):
            ko("⛔ la pagina non e' arrivata a `window.REMOTIX`: %s" % str(s)[:300])
            return 4
        if not s.get("banco"):
            ko("⛔ il PROLOGO non e' entrato: senza, non c'e' nessun `t1` e "
               "nessuna lettura di pixel")
            return 4
        ok("pagina pronta, e il prologo del banco e' dentro")

        # ⛔⭐ IL WORKER — si aggancia ADESSO, cioe' PRIMA delle credenziali.
        #    Il worker di `pagina.html` a riposo non fa niente e il suo
        #    `VideoDecoder` nasce alla prima chiave: questo e' l'unico momento
        #    in cui ci si puo' mettere in mezzo senza perdere un fotogramma.
        rw = palco.aggancia_worker(attesa=15)
        v["worker"] = {"chiesto": bool(a.video_worker), "aggancio": rw}
        if rw:
            ok("⭐ worker agganciato, e il prologo e' dentro anche li': «%s»" % rw)
        elif a.video_worker:
            ko("⛔ e' stato chiesto «?video=worker» ma nessun bersaglio "
               "«worker» si e' fatto agganciare: NON misuro.  ⚠ Un numero "
               "preso cosi' sarebbe il thread principale con l'etichetta del "
               "worker")
            return 4
        else:
            inf("nessun worker (ed e' il caso atteso senza «?video=worker»): "
                "la pagina decodifica sul thread principale")

        log("3. Dentro come utente")
        if not a.parola_file:
            ko("⛔ serve --parola-file (0600).  La parola NON passa da argv (D12)")
            return 2
        with open(a.parola_file) as f:
            parola = f.read().strip()
        c.valuta(ENTRA % (json.dumps(a.utente), json.dumps(parola)), attendi=False)
        del parola
        inf("credenziali inviate per «%s» (mai da argv)" % a.utente)
        # ⛔⭐ QUI NON SI ASPETTA IL PRIMO FOTOGRAMMA, E IL PRIMO GIRO DI QUESTO
        #     BANCO L'AVEVA SBAGLIATO — `[M]` 13 agosto 2026.
        #
        #     Aspettare `dipinti > 0` prima di accendere la scena e' un'attesa
        #     che non finisce MAI: senza scena Mutter non consegna niente
        #     («0 fotogrammi consegnati, 216 attese a vuoto — scena ferma»), e
        #     il banco moriva dicendo «nessun fotogramma dipinto» con la catena
        #     perfettamente funzionante.  ⚠ E' `LEZIONI.md` §1.1 travestita da
        #     ordine delle operazioni: la scena non e' un contorno della misura,
        #     e' una sua precondizione.
        #
        #     ⇒ L'ordine giusto e': sessione → SCENA → primo fotogramma.
        s = aspetta(c, STATO, 40,
                    lambda x: "sessione" in (x.get("registro") or "").lower()
                    or (x.get("conti") or {}).get("stream", 0) > 0)
        ok("sessione stabilita (registro: …%s)"
           % (s.get("registro") or "")[-140:].replace("\n", " · "))

        log("4. LA SCENA — ⛔ e va sul monitor CHE SI STA CATTURANDO")
        if a.gancio_scena:
            # ⛔ Si RIPROVA: il monitor virtuale del palco lo monta il FIGLIO,
            #    non il server, e il suo nome compare nel registro qualche
            #    istante dopo la sessione.  `scena-avvia` si rifiuta di
            #    accendere «da qualche parte» finche' non lo legge — e ha
            #    ragione: una scena sul monitor sbagliato da' zero fotogrammi
            #    con la catena perfetta.
            acceso = False
            for tentativo in range(6):
                rs = subprocess.run(a.gancio_scena, shell=True,
                                    capture_output=True, text=True, timeout=240)
                if rs.returncode == 0:
                    acceso = True
                    inf((rs.stdout or "")[-500:])
                    break
                inf("tentativo %d: la scena non si accende ancora (%s)"
                    % (tentativo + 1,
                       (rs.stdout or "").strip().splitlines()[-1:] or ""))
                time.sleep(3.0)
            if not acceso:
                ko("⛔ la scena non si e' accesa in 6 tentativi: NON misuro.  "
                   "⚠ Un numero preso senza scena e' uno zero che accusa il "
                   "prodotto invece della scena")
                v["guaio"] = "scena non accesa"
                return 6
            time.sleep(2.0)
        else:
            dub("⚠ nessun --gancio-scena: si presume che la scena sia gia' accesa "
                "sul monitor giusto.  ⛔ Se non lo e', P2 sara' rosso e dira' "
                "perche' — non uscira' un numero sbagliato")

        s = aspetta(c, STATO, 40,
                    lambda x: (x.get("conti") or {}).get("dipinti", 0) > 0)
        if not (s and (s.get("conti") or {}).get("dipinti", 0) > 0):
            ko("⛔ nessun fotogramma dipinto CON LA SCENA ACCESA: %s"
               % str((s or {}).get("registro"))[-400:])
            v["guaio"] = "niente dipinto"
            return 5
        ok("dipinti: %s · deposito: %s" % (s["conti"]["dipinti"], s.get("deposito")))

        log("5. LO SCORRIMENTO della marca — MISURATO sui pixel veri (P2b)")
        c.valuta("window.__B17.crudi_voluti = 3, window.__B17.crudi = [], true",
                 attendi=False)
        time.sleep(2.0)
        rr = c.valuta("window.__B17.prendi()", attendi=False)
        crudi = (rr or {}).get("crudi") or []
        v["P2b"] = {"crudi": len(crudi), "confronti": []}
        scorrimento = [0, 0]
        for cr in crudi:
            grezzo = base64.b64decode(cr["b64"])
            np = m.np_o_muori("03-b17: il confronto del campionamento")
            img = np.frombuffer(grezzo, dtype=np.uint8).reshape(cr["a"], cr["l"], 3)
            vero = m.leggi_marca(img, ricerca=2)
            # ⛔ E il confronto che conta: le 144 celle di numpy contro quelle
            #    del JavaScript.  Se differiscono, il campionamento del banco
            #    NON e' quello del lettore certificato, e ogni P2 e' un caso.
            y = (img[:, :, :3].astype(np.float64) @ m.PESI_LUMA) / 255.0
            celle_np = m._celle(y, m.GEOMETRIA, 0, 0) * 255.0
            scarto = max(abs(float(x) - float(z))
                         for x, z in zip(celle_np, cr["celle"]))
            v["P2b"]["confronti"].append(
                {"marca_sui_pixel_veri": {k: vero.get(k) for k in
                                          ("c_e", "disegno", "istante_us",
                                           "contrasto", "scorrimento_provato",
                                           "perche")},
                 "scarto_massimo_celle_su_255": round(scarto, 4)})
            if vero.get("c_e"):
                scorrimento = vero["scorrimento_provato"]
        if v["P2b"]["confronti"]:
            peggio = max(x["scarto_massimo_celle_su_255"]
                         for x in v["P2b"]["confronti"])
            letti = sum(1 for x in v["P2b"]["confronti"]
                        if x["marca_sui_pixel_veri"]["c_e"])
            (ok if peggio < 1.0 else ko)(
                "P2b: il campionamento in JavaScript e quello di numpy "
                "differiscono al massimo di %.3f su 255 (marche lette sui pixel "
                "veri: %d su %d)" % (peggio, letti, len(v["P2b"]["confronti"])))
            v["P2b"]["scarto_peggiore"] = peggio
            v["P2b"]["lette"] = letti
        else:
            dub("⚠ nessuna regione cruda portata fuori: P2b non eseguito")
        inf("scorrimento della marca: %s" % scorrimento)
        c.valuta("window.__B17.scorrimento = %s, true" % json.dumps(scorrimento),
                 attendi=False)

        log("6. ⛔ P1 — I GIRI COL RITARDO NOTO, **INTRECCIATI**")
        # ⛔⭐ I GIRI SI INTRECCIANO, E QUESTA E' UNA CORREZIONE DI METODO NATA
        #     DA UN ROSSO — `[M]` 13 agosto 2026.
        #
        #     A blocchi (25 s di N=0, poi 25 s di N=25, poi 25 s di N=60) il
        #     ritardo iniettato e' confuso con **il tempo**: la macchina, il
        #     codificatore e la cadenza consegnata non stanno fermi per un
        #     minuto e mezzo, e la salita misurata ne porta dentro la deriva.
        #     Il sintomo: N=25 dava +22,8 ms in un giro e +28,3 nel giro dopo,
        #     con lo stesso ponte che sul suo banco inietta 25,00 ± 0,3.
        #
        #     ⛔ E la cura NON e' allargare la tolleranza finche' passa: quella
        #        e' la mossa che `LEZIONI.md` §1.13 vieta.  La cura e' togliere
        #        la confusione: fette corte, alternate, tante volte.  Cosi' la
        #        deriva colpisce **tutti** i valori di N allo stesso modo e la
        #        differenza fra le mediane resta il solo ritardo iniettato.
        ritardi = [float(x) for x in a.ritardi.split(",")]
        mani = max(2, a.mani)
        fetta = max(3.0, a.secondi / mani)
        inf("%d mani da %.1f s per ciascuno di %s" % (mani, fetta, ritardi))
        raccolto = {n: [] for n in ritardi}
        ultimi = {}
        for mano in range(mani):
            for n in ritardi:
                if not metti_ritardo(a, n, 0, "%s-m%d-n%g" % (a.giro, mano, n)):
                    dub("⚠ non ho potuto scrivere il comando del ponte per N=%g" % n)
                # ⛔ Si BUTTA la fetta di assestamento: i primi fotogrammi dopo
                #    un cambio di N sono ancora quelli in volo col N di prima.
                time.sleep(1.0)
                c.valuta("window.__B17.prendi(), true")
                camp, _, costo, ultimo = raccogli(c, fetta)
                raccolto[n] += camp
                ultimi[n] = ultimo
                if n == 0:
                    v.setdefault("costo_lettura_us", []).extend(costo)
        metti_ritardo(a, 0, 0, a.giro)
        oro0 = Orologi(parete, anc_a, {"c_e": False},
                       (ultimi.get(0.0) or ultimi.get(ritardi[0]) or {}).get("t_origine", 0))
        for n in ritardi:
            camp = arricchisci(raccolto[n], oro0)
            d = dist([x["ritardo_ms"] for x in regime(camp)])
            v["giri"].append({"ritardo_chiesto_ms": n, "campioni": camp,
                              "distribuzione": d, "mani": mani,
                              "conti_banco": (ultimi.get(n) or {}).get("conti"),
                              "conti_pagina": (ultimi.get(n) or {}).get("pagina")})
            if n == 0:
                u = ultimi[n] or {}
                v["grana"] = u.get("grana")
                v["isolata"] = u.get("isolata")
                v["conti_pagina"] = u.get("pagina")
                v["origine_pagina_ms"] = u.get("t_origine")
            inf("N=%-4g  campioni %-5s  mediana %s ms  p95 %s ms"
                % (n, d.get("n"), d.get("mediana"), d.get("p95")))

        log("7. P8 — quanto costa il banco, ⛔ anche qui A FETTE ALTERNATE")
        senza, con = [], []
        for mano in range(3):
            for leggi, dove in ((False, senza), (True, con)):
                c.valuta("window.__B17.leggi = %s, window.__B17.prendi(), true"
                         % ("true" if leggi else "false"))
                cc, _, _, _ = raccogli(c, 5.0)
                dove += cc
        c.valuta("window.__B17.leggi = true, true")
        def ritmo(cc):
            if len(cc) < 5:
                return None
            d = (max(x["t1"] for x in cc) - min(x["t1"] for x in cc)) / 1000.0
            # ⚠ Le fette sono staccate nel tempo: il ritmo si fa sugli
            #   INTERVALLI, non su «quanti diviso quanto», o si conterebbero
            #   dentro anche i buchi fra una fetta e l'altra.
            iv = sorted(b["t1"] - x["t1"] for x, b in zip(cc, cc[1:])
                        if 0 < b["t1"] - x["t1"] < 500)
            if not iv:
                return None
            return round(1000.0 / iv[len(iv) // 2], 2)
        v["fps_senza_lettura"] = ritmo(senza)
        v["fps_con_lettura"] = ritmo(con)
        inf("ritmo senza la lettura: %s · con la lettura: %s  (%d e %d fotogrammi)"
            % (v["fps_senza_lettura"], v["fps_con_lettura"], len(senza), len(con)))

        log("8. ⛔⛔ P3 — IL RILEVATORE DAVANTI A QUEL CHE NON C'E'")
        # ⛔⭐ E LA PRIMA STESURA DI QUESTO CONTROLLO ERA INESEGUIBILE.
        #
        #     Spegnere la scena sembrava il modo ovvio di mostrare al lettore
        #     un fotogramma senza marca.  ⛔ Non lo e': senza scena **Mutter
        #     non consegna nessun fotogramma** («0 consegnati, 216 attese a
        #     vuoto»), quindi il richiamo del decodificatore non scatta e al
        #     lettore non si mostra proprio niente.  `[M]` 13 agosto 2026: 0
        #     fotogrammi guardati, e P3 rosso per «non eseguito» — che era
        #     l'esito ONESTO, ma non il controllo.
        #
        # ⭐ La strada che funziona: si sposta la FINESTRA DI LETTURA su
        #    un'altra parte dello stesso fotogramma.  Sono pixel VERI, dello
        #    stesso desktop, in movimento, decodificati dalla stessa catena —
        #    e li' la marca NON C'E'.  Se il lettore dicesse «si'» anche li',
        #    direbbe si' a qualunque cosa, e ogni ritardo di questo banco
        #    sarebbe un numero inventato.
        #
        # ⚠ E si tiene ANCHE la prova a scena spenta, dichiarata per quel che
        #   e': non «zero falsi positivi», ma «non c'e' niente da guardare».
        fuori_marca = json.dumps([a.finestra_p3_x, a.finestra_p3_y])
        c.valuta("window.__B17.finestra = %s, window.__B17.prendi(), true"
                 % fuori_marca)
        camp_n, _, _, _ = raccogli(c, 10.0)
        oro3 = Orologi(parete, anc_a, {"c_e": False},
                       v.get("origine_pagina_ms", 0))
        camp_n = arricchisci(camp_n, oro3)
        v["senza_marca"] = [x for x in camp_n if x.get("visto")]
        v["senza_marca_finestra"] = [a.finestra_p3_x, a.finestra_p3_y]
        falsi = [x for x in v["senza_marca"] if x["marca"].get("c_e")]
        (ok if (v["senza_marca"] and not falsi) else ko)(
            "P3: %d fotogrammi VERI guardati in (%d,%d), dove la marca non c'e' "
            "→ %d falsi positivi"
            % (len(v["senza_marca"]), a.finestra_p3_x, a.finestra_p3_y,
               len(falsi)))
        c.valuta("window.__B17.finestra = [0,0], true")

        log("9. P5 — il fuori ordine, fabbricato (⛔ a scena ANCORA ACCESA)")
        # ⛔ L'ORDINE DI QUESTI DUE PASSI E' STATO CORRETTO — `[M]` 13 agosto
        #    2026.  La prima stesura spegneva la scena per P3 e POI faceva P5:
        #    senza scena non arriva un fotogramma, e P5 raccoglieva ZERO
        #    campioni senza che niente fosse rotto.  ⇒ Prima quel che ha
        #    bisogno della scena, e per ultimo quel che ha bisogno che non ci
        #    sia.
        if a.p5:
            # ⛔⭐ UNA RAFFICA OGNI 400 PACCHETTI, E IL NUMERO E' STATO
            #     ABBASSATO DUE VOLTE SU MISURA.
            #
            #     A 40 e a 60 la pagina SMETTEVA di consegnare: trattenere il
            #     10 % dei pacchetti per 45 ms assomiglia a una perdita, il
            #     controllo di congestione di QUIC ci crede e chiude il
            #     rubinetto.  ⇒ P5 e P3 restavano senza dati — cioe' un rosso
            #     del BANCO travestito da rosso del prodotto, che e' la cosa
            #     peggiore che un banco possa produrre.
            #
            # ⚠ E si dichiara il prezzo: con una raffica ogni 400 pacchetti il
            #   fuori ordine si fabbrica RARAMENTE.  Se non ne esce nessuno
            #   scavalcato, P5 dira' «NON ESEGUITO» — e sara' vero.
            metti_ritardo(a, 0, 400, a.giro + "-p5", fo_ms=45.0, raffica=4)
            time.sleep(1.0)
            c.valuta("window.__B17.prendi(), true")
            camp5, _, _, u5 = raccogli(c, min(14.0, a.secondi))
            oro5 = Orologi(parete, anc_a, {"c_e": False},
                           v.get("origine_pagina_ms", 0))
            camp5 = arricchisci(camp5, oro5)
            v["giro_p5"] = {"campioni": camp5,
                            "distribuzione": dist([x["ritardo_ms"]
                                                   for x in regime(camp5)]),
                            "conti_pagina": (u5 or {}).get("pagina")}
            metti_ritardo(a, 0, 0, a.giro)
            inf("fuori ordine fabbricato: %s campioni, mediana %s ms"
                % (v["giro_p5"]["distribuzione"].get("n"),
                   v["giro_p5"]["distribuzione"].get("mediana")))
            time.sleep(1.0)

        log("9-bis. ⛔ E la scena SI SPEGNE — quel che succede va detto")
        if a.gancio_scena_spegni:
            rs = subprocess.run(a.gancio_scena_spegni, shell=True,
                                capture_output=True, text=True, timeout=120)
            time.sleep(2.0)
            c.valuta("window.__B17.prendi(), true")
            camp_z, _, _, _ = raccogli(c, 8.0)
            v["a_scena_spenta"] = {
                "fotogrammi_arrivati": len(camp_z),
                "nota": "⛔ Se e' 0, NON e' «zero falsi positivi»: e' «non c'e' "
                        "niente da guardare».  Senza scena Mutter non consegna "
                        "un fotogramma, ed e' `LEZIONI.md` §1.1 vista dal lato "
                        "del lettore.  Il P3 vero e' quello del passo 9."}
            inf("fotogrammi arrivati a scena spenta: %d  (⛔ e uno zero qui e' "
                "la conferma di §1.1, non un controllo superato)" % len(camp_z))
        else:
            dub("⚠ nessun --gancio-scena-spegni: la conferma di §1.1 non si fa")

        log("10. L'ancora, RILETTA — la deriva non si suppone")
        anc_b = p.orologio_chiedi(a.host, a.ancora, campioni=1200, pausa_s=0.0005)
        if anc_b.get("c_e"):
            dpm = p.deriva_ppm(anc_a, anc_b)
            inf("scarto d'apertura %d us · di chiusura %d us · deriva %s ppm"
                % (anc_a["scarto_us"], anc_b["scarto_us"],
                   round(dpm, 2) if dpm is not None else "?"))
            v["deriva_ppm"] = dpm
            # ⛔ E si RIFA' il conto con le due ancore: la deriva si spalma.
            oro = Orologi(parete, anc_a, anc_b, v.get("origine_pagina_ms", 0))
            for g in v["giri"]:
                g["campioni"] = arricchisci(g["campioni"], oro)
                g["distribuzione"] = dist([x["ritardo_ms"]
                                           for x in regime(g["campioni"])])
            v["senza_marca"] = arricchisci(v.get("senza_marca", []), oro)
            v["errore_orologio_us"] = oro.errore_us()
        else:
            dub("⚠ l'ancora di chiusura non ha risposto: la deriva resta `[?]`")
            v["errore_orologio_us"] = parete["errore_us"] + anc_a["errore_us"]
        v["ancora_apertura"], v["ancora_chiusura"] = anc_a, anc_b
        v["parete"] = parete

        log("11. IL CONTROLLO DELL'OROLOGIO DELLA PAGINA (la strada A)")
        cdp_anc = ancora_pagina_cdp(c)
        if cdp_anc.get("c_e"):
            # ⛔ Le due grandezze sono OMOGENEE e vanno SOTTRATTE:
            #    `parete` e' (reale − monotono) letto qui con una syscall;
            #    `cdp_anc` e' (orologio della pagina − monotono di qui) letto
            #    con un giro CDP.  Se `timeOrigin` dice il vero, la differenza
            #    e' zero.  ⚠ La prima stesura stampava il secondo numero da
            #    solo — 1,7·10¹⁵ µs — e lo confrontava con una soglia di 3 ms:
            #    un rosso garantito che non diceva niente.
            differenza = cdp_anc["scarto_us"] - parete["scarto_us"]
            inf("`timeOrigin` contro il giro CDP: scarto %d us, errore del giro "
                "%d us" % (differenza, cdp_anc["errore_us"]))
            v["controllo_orologio_pagina"] = cdp_anc
            (ok if abs(differenza) <= max(3000, cdp_anc["errore_us"] * 3) else ko)(
                "l'orologio della pagina e quello di CHUWI concordano entro "
                "%.2f ms" % (abs(differenza) / 1000.0))
        else:
            dub("⚠ " + cdp_anc.get("perche", ""))

        log("12. ⛔ Quale dei due orologi ha letto il prodotto (il `pts`)")
        v["riattacchi_cdp"] = getattr(palco, "riattacchi", 0)
        rl = _sshpw("grep -aoh 'MISURATO: il .pts. di Mutter[^\"]*' "
                    "%s 2>/dev/null | tail -2" % a.registro_prodotto)
        v["riga_del_pts"] = (rl.stdout or "").strip()
        if v["riga_del_pts"]:
            (ok if "e' lo stesso" in v["riga_del_pts"] else ko)(v["riga_del_pts"][:300])
        else:
            dub("⚠ non ho trovato la riga del `pts` nel registro del prodotto: "
                "⛔ non e' «il pts va bene», e' «non ho potuto guardare».  "
                "Il numero della scomposizione 1 va letto con questa riserva")

    finally:
        palco.spegni()

    r2 = _sshpw("ss -tuln | grep -E ':(7448|7501|7561|760[0-9]|761[0-9])\\b' | sort")
    v["porte_dopo"] = r2.stdout
    if v["porte_dopo"] != v["porte_prima"]:
        dub("⚠ le porte sono cambiate durante la misura:\n%s" % v["porte_dopo"])

    os.makedirs(os.path.dirname(a.verbale) or ".", exist_ok=True)
    with open(a.verbale, "w") as f:
        json.dump(v, f, ensure_ascii=False)
    inf("verbale: %s (%d byte)" % (a.verbale, os.path.getsize(a.verbale)))

    g = stampa_verdetto(v, a)
    base = next((x for x in v["giri"] if x.get("ritardo_chiesto_ms") == 0), None)
    d = (base or {}).get("distribuzione") or {}
    deposita({"banco": "B17", "tipo": "MISURA", "giro": a.giro,
              "host": a.host, "porta": a.porta,
              "controlli": {k: bool(g[k].get("esito")) for k in TUTTI},
              "P1": g["P1"], "distribuzione_ms": d,
              "verdetto": verdetto(d, v.get("errore_orologio_us", 0)),
              "scomposizione": scomponi(regime((base or {}).get("campioni", []))),
              "pezzo_cieco": con_pezzo_cieco(d.get("mediana")),
              "errore_orologio_us": v.get("errore_orologio_us"),
              "deriva_ppm": v.get("deriva_ppm"),
              "riga_del_pts": v.get("riga_del_pts"),
              "P2b": v.get("P2b"), "verbale": a.verbale})
    return 0 if all(g[k].get("esito") for k in TUTTI) else 1


# ═══════════════════════════════════════════════════════════════════════════
def deposita(riga):
    riga["quando"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(ESITI, "a") as f:
        f.write(json.dumps(riga, ensure_ascii=False) + "\n")


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--misura", action="store_true")
    p.add_argument("--verdetto", help="rilegge un verbale su disco")
    p.add_argument("--host", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7605)
    p.add_argument("--ancora", type=int, default=7616)
    p.add_argument("--comando-ponte", default="/tmp/03-b17/comando")
    p.add_argument("--utente", default="nicfio")
    p.add_argument("--parola-file")
    p.add_argument("--secondi", type=float, default=25.0)
    p.add_argument("--ritardi", default="0,25,60",
                   help="i ritardi noti di P1, in ms")
    p.add_argument("--schermo", default=":85")
    p.add_argument("--diagnosi", type=int, default=9605)
    p.add_argument("--lavoro", default="/tmp/03-b17")
    p.add_argument("--verbale", default="/tmp/03-b17/verbale.json")
    p.add_argument("--senza-gpu", action="store_true")
    # ⭐ L'interruttore di `STUDI.md` §web §6.1, misurato invece che creduto.
    p.add_argument("--video-worker", action="store_true",
                   help="apre la pagina con «?video=worker»")
    p.add_argument("--gancio-scena", help="il comando che ACCENDE la scena, "
                   "eseguito DOPO il primo fotogramma dipinto (prima il monitor "
                   "virtuale non esiste)")
    p.add_argument("--gancio-scena-spegni", help="⛔ il comando che la SPEGNE: "
                   "senza, P3(a) non si puo' eseguire")
    p.add_argument("--registro-prodotto", default="/media/REMOTIX/tmp/03-b17/registro.log")
    p.add_argument("--mani", type=int, default=5,
                   help="⛔ in quante fette ALTERNATE si divide ogni giro di P1: "
                        "a blocchi il ritardo iniettato si confonde con la "
                        "deriva della macchina")
    p.add_argument("--p5", action="store_true", help="fabbrica il fuori ordine")
    p.add_argument("--finestra-p3-x", type=int, default=900,
                   help="⛔ dove leggere per P3: una regione dello STESSO "
                        "fotogramma in cui la marca NON c'e'")
    p.add_argument("--finestra-p3-y", type=int, default=600)
    p.add_argument("--giro", default=time.strftime("b17-%Y%m%d-%H%M%S"))
    a = p.parse_args()

    if a.certifica:
        r = certifica()
        deposita({"banco": "B17", "tipo": "CERTIFICAZIONE", "giro": a.giro,
                  "esito": r["esito"], "controlli": r["controlli"],
                  "passati": r["passati"],
                  "dettaglio": [e for e in r["esiti"] if not e["esito"]][:20]})
        return 0 if r["esito"] == "PROMOSSO" else 1

    if a.verdetto:
        with open(a.verdetto) as f:
            v = json.load(f)
        # ⛔⭐ LA CURA DEL 13 AGOSTO 2026 SERA — il terzo `return 0`
        #     incondizionato, quello che il catalogo (`01-b12-guasti.py`, voce
        #     03-b19) dichiarava «ancora li'».  `stampa_verdetto()` stampa i
        #     rossi con `ko()`, e `ko()` STAMPA E BASTA: col guasto dentro, il
        #     rosso restava nella prosa e chi legge a macchina vedeva verde.
        #
        # ⛔ E la riga non e' inventata: e' la STESSA di `misura()` (la riga
        #    che chiude quella strada), presa tale e quale.  Le due strade
        #    leggono lo stesso `g` dallo stesso `giudica()`, quindi rileggere
        #    un verbale salvato e misurarlo dal vivo adesso danno lo stesso
        #    codice d'uscita — che era il punto.
        g = stampa_verdetto(v, a)
        return 0 if all(g[k].get("esito") for k in TUTTI) else 1

    if a.misura:
        from importlib import import_module  # noqa: F401
        return misura(a)

    p.print_help()
    return 2


def stampa_verdetto(v, a=None):
    g = giudica(v)
    log("I SETTE CONTROLLI")
    for k in TUTTI:
        r = g[k]
        (ok if r.get("esito") else ko)(
            "%s  %s" % (k, r.get("perche") or json.dumps(
                {x: y for x, y in r.items() if x != "perche"},
                ensure_ascii=False)[:220]))
    base = next((x for x in v.get("giri", []) if x.get("ritardo_chiesto_ms") == 0), None)
    camp = regime((base or {}).get("campioni", []))
    d = dist([c["ritardo_ms"] for c in camp])
    log("IL NUMERO — ⛔ col pezzo cieco accanto")
    inf(json.dumps(d, ensure_ascii=False))
    inf(con_pezzo_cieco(d.get("mediana")))
    log("LA SCOMPOSIZIONE")
    for k, x in scomponi(camp).items():
        inf("%-58s %s" % (k, json.dumps(x, ensure_ascii=False)))
    log("IL VERDETTO")
    inf(json.dumps(verdetto(d, v.get("errore_orologio_us", 0)),
                   ensure_ascii=False, indent=1))
    return g


if __name__ == "__main__":
    sys.exit(principale())
