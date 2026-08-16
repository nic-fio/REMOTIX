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


def solo_modulo():
    """⭐ L'arbitro della finestra esclusiva (`03-solo.py`, certificato).

    ⛔ Non si riscrive qui: se ogni banco si scrivesse il proprio «sono solo?»,
       la parola «solo» vorrebbe dire cinque cose diverse e nessuna sarebbe
       confrontabile con le altre.
    """
    return carica("solo", os.path.join(QUI, "03-solo.py"))


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
    scorrimento: [0, 0], leggi: true, crudi: [], crudi_voluti: 0,
    /* ⛔⭐ DOVE si legge.  A riposo e' l'angolo in alto a sinistra, dove la
       scena dipinge la marca.  ⭐ Spostandola altrove si ottiene il controllo
       P3 sui PIXEL VERI: fotogrammi veri, in movimento, dello stesso desktop,
       in una regione dove la marca NON C'E'.  Se il lettore dice «si'» li',
       dice si' a qualunque cosa — ed e' esattamente il difetto che in v1 e'
       passato inosservato. */
    finestra: [0, 0],
    t_origine: performance.timeOrigin,
    /* ⛔ Il costo della lettura dei pixel si MISURA (P8): un banco che credesse
       zero il proprio prezzo lo infilerebbe dentro il numero altrui. */
    costo_lettura_us: [],
  };
  window.__B17 = B;

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
             ora_pagina: performance.now(),
             ora_reale: performance.timeOrigin + performance.now(),
             pagina: window.REMOTIX && window.REMOTIX.schermo
                     ? Object.assign({}, window.REMOTIX.schermo.conti) : null };
  };
})();
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
        self.x = self.chrome = self.c = None
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
        # ⛔⛔ LE BANDIERE SI CONSERVANO, PERCHE' VANNO NEL VERBALE — `LEZIONI.md`
        #     §2.0.  Il 13 agosto 2026 una sonda ha risposto «no a HEVC» cinque
        #     volte su cinque **girando con `--disable-gpu` e senza dirlo**, e
        #     su quel «no» e' nata una corsia intera del piano.  ⇒ Un banco che
        #     risponde deve scrivere accanto alla risposta **con che palco** ha
        #     risposto, e un default nel sorgente non e' una dichiarazione:
        #     chiunque puo' passare `--senza-gpu` e il numero avrebbe lo stesso
        #     aspetto.
        self.bandiere = list(flag)
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
        for m in ("Page.enable", "Runtime.enable", "Network.enable"):
            self.c.chiama(m)
        self.c.chiama("Network.setCacheDisabled", cacheDisabled=True)
        self.riattacchi = getattr(self, "riattacchi", 0)
        return b

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


def delta_conto(prima, dopo, campo):
    """La DIFFERENZA di un contatore cumulativo del prodotto fra due istantanee.

    ⛔ Ritorna `None` — e non 0 — quando la differenza non si puo' fare: manca
       un'istantanea, manca il campo, o il conto e' ANDATO INDIETRO (la pagina
       si e' riaccesa e i conti sono ripartiti da zero).  «Non ho potuto
       guardare» e «zero» non sono la stessa cosa, `LEZIONI.md` §1.9.
    """
    if not isinstance(prima, dict) or not isinstance(dopo, dict):
        return None
    a, b = prima.get(campo), dopo.get(campo)
    if a is None or b is None:
        return None
    try:
        d = int(b) - int(a)
    except (TypeError, ValueError):
        return None
    return d if d >= 0 else None


def p5_fuori_ordine(campioni, conti_prima=None, conti_dopo=None):
    """⛔ I fotogrammi arrivano su stream indipendenti.  Un anello che non lo
    regge misura la coda invece del ritardo.

    ⭐ Questo anello lo regge PER COSTRUZIONE — accoppia `t0` e `t1` dal
       CONTENUTO (la marca nei pixel, il `pts` nei 28 byte), non dall'ordine —
       e il controllo lo DIMOSTRA invece di dichiararlo: si conta quanti
       fotogrammi sono arrivati fuori ordine, e si verifica che il ritardo dei
       fuori ordine e quello degli altri vengano dalla stessa distribuzione.

    ⛔⛔ E QUI STAVA LA CECITA' PIU' GRAVE DEL BANCO — trovata la sera del 13
        agosto 2026 e curata qui (corsia C, coda C3).

        Il prodotto **scarta i fotogrammi fuori ordine PRIMA del
        decodificatore**: `src/pagina.html:1578`, «un fotogramma il cui numero
        e' precedente all'ultimo gia' consegnato si scarta, e la sua misura non
        si guarda nemmeno» (§6.2, rilievo P14).  ⇒ Un fotogramma scavalcato non
        arriva **mai** al vetro, quindi non entra **mai** nel campione di questo
        banco, che guarda solo quel che e' stato dipinto.

        ⛔ Ne discendeva che «0 fotogrammi fuori ordine» era **un'identita'
        algebrica, non una misura**: su una rete che riordinasse davvero i
        fotogrammi scavalcati **sparirebbero dal campione** e questa funzione
        direbbe ancora «non eseguito».  «P5 non eseguito» e «tutto a posto»
        avevano lo stesso aspetto.

    ⭐ LA CURA: il numero c'e' gia', e ce l'ha il PRODOTTO.  `this.conti
       .scartati_ordine` (`src/pagina.html:1235`, incrementato a `:1578`) conta
       esattamente i fotogrammi buttati per ordine.  Si legge **come
       differenza** fra l'inizio e la fine del giro, e si SOMMA a quel che il
       banco vede da sé:

           fuori ordine = scavalcati VISTI (dopo il decodificatore)
                        + scartati DAL PRODOTTO (prima del decodificatore)

    ⛔ E se i conti del prodotto non ci sono, questa funzione **non dice piu'
       «non eseguito»**: dice «non ho potuto guardare», che e' un'altra cosa
       (`LEZIONI.md` §2.0).
    """
    scartati = delta_conto(conti_prima, conti_dopo, "scartati_ordine")
    consegnati = delta_conto(conti_prima, conti_dopo, "consegnati")
    ord_ = [c for c in campioni if c.get("numero") is not None]
    if len(ord_) < 20:
        return {"esito": False, "scartati_dal_prodotto": scartati,
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
    comune = {"scavalcati": scavalcati, "totali": len(ord_),
              "scavalcati_visti_dal_banco": scavalcati,
              "scartati_dal_prodotto": scartati,
              "consegnati_dal_prodotto": consegnati,
              "dove_si_e_guardato":
                  "⭐ DUE POSTI: gli scavalcati che il banco vede DOPO il "
                  "decodificatore, e gli `scartati_ordine` che il prodotto "
                  "conta PRIMA (src/pagina.html:1578).  Il banco da solo non "
                  "puo' vedere i secondi: non arrivano al vetro"}

    # ⛔⛔ IL RAMO CHE PRIMA NON C'ERA: i conti del prodotto non ci sono.
    #     ⇒ Il banco ha guardato **meta'** del fenomeno e non puo' saperlo.
    #     Un «non eseguito» qui sarebbe la cecita' travestita da misura.
    if scartati is None:
        return dict(comune, esito=False, cieco=True,
                    ritardo_in_ordine=d_b,
                    perche="⛔ NON HO POTUTO GUARDARE: mancano i conti del "
                           "prodotto (`scartati_ordine` prima e dopo il giro). "
                           "Il banco vede solo i fotogrammi DIPINTI, e un "
                           "fotogramma scavalcato il prodotto lo scarta prima "
                           "del decodificatore (src/pagina.html:1578): non "
                           "arriva mai qui.  ⚠ Con %d scavalcati visti, questo "
                           "NON e' «non eseguito» e NON e' «tutto a posto»: e' "
                           "un'assenza di informazione" % scavalcati)

    fuori_totali = scavalcati + scartati

    # ⛔⭐ «NESSUNO SCAVALCATO» NON E' «REGGE IL FUORI ORDINE»: e' «il fuori
    #     ordine non e' successo».  `LEZIONI.md` §1.9 applicata a un controllo
    #     invece che a una lettura.  ⭐ E adesso e' una MISURA e non piu'
    #     un'identita' algebrica: lo zero lo dichiara il PRODOTTO, che i fuori
    #     ordine li conta prima di buttarli.
    if fuori_totali == 0:
        return dict(comune, esito=False, quota=0.0, ritardo_in_ordine=d_b,
                    fuori_ordine_totali=0,
                    perche="⛔ NON ESEGUITO: nessuno dei %d fotogrammi e' "
                           "arrivato fuori ordine — e stavolta e' MISURATO ai "
                           "due capi: 0 scavalcati nel campione del banco E 0 "
                           "`scartati_ordine` dichiarati dal prodotto su %s "
                           "consegnati.  ⚠ Non e' «l'anello regge»: e' «il "
                           "fenomeno non si e' presentato»"
                           % (len(ord_), consegnati))

    # ⛔ IL CASO CHE PRIMA SPARIVA: il fuori ordine e' successo, e il prodotto
    #    l'ha assorbito PRIMA del decodificatore.  Il banco non ne vede
    #    nessuno — e va detto che non li vede PERCHE' NON GLI ARRIVANO, non
    #    perche' non ci sono.
    if scavalcati == 0:
        return dict(comune, esito=True, quota=0.0, ritardo_in_ordine=d_b,
                    fuori_ordine_totali=fuori_totali,
                    perche="⭐ ESEGUITO, e il fenomeno c'e' stato: il prodotto "
                           "ha scartato %d fotogrammi per ORDINE su %s "
                           "consegnati, tutti PRIMA del decodificatore "
                           "(src/pagina.html:1578).  ⇒ Nel campione del banco "
                           "non ce n'e' nessuno **per costruzione**, e i %d "
                           "che restano non possono portare dentro la coda di "
                           "quelli scavalcati.  ⚠ Quel che questo NON dice: "
                           "quanto sarebbe stato il loro ritardo — quei "
                           "fotogrammi al vetro non ci arrivano mai"
                           % (scartati, consegnati, len(ord_)))

    return dict(comune, esito=coerente, quota=round(scavalcati / len(ord_), 4),
                fuori_ordine_totali=fuori_totali,
                ritardo_scavalcati=d_a, ritardo_in_ordine=d_b,
                perche=None if coerente else
                       "⛔ i fotogrammi scavalcati hanno una mediana di %.1f ms "
                       "contro %.1f: l'anello sta misurando la coda"
                       % (d_a["mediana"], d_b["mediana"]))


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
    # ⛔ I conti del PRODOTTO, presi come differenza fra l'inizio e la fine del
    #    giro: sono la meta' del fenomeno che il banco non puo' vedere (vedi
    #    `p5_fuori_ordine`).  ⚠ Si prendono dal giro a cui appartengono, o si
    #    sommerebbe lo scarto di un giro ai fotogrammi di un altro.
    p5g = verbale.get("giro_p5") or {}
    camp5 = regime(p5g.get("campioni") or [])
    return {
        "P1": p1_ritardo_noto(g),
        "P2": p2_trova_quel_che_c_e(camp),
        "P3": p3_non_trova_quel_che_non_c_e(
            camp, verbale.get("senza_marca", [])),
        # ⛔⭐ P5 SI GIUDICA DOVE IL FENOMENO C'E', NON DOVE NON C'E'.
        #
        #     Sul giro normale, su questa LAN e con delta da ~2,6 KB, lo
        #     scavalcamento per dimensione non si presenta.  ⛔ Un P5 giudicato
        #     li' sarebbe VERDE PER COSTRUZIONE, che e' peggio di un rosso
        #     (`LEZIONI.md` §1.3, §2.2).  ⇒ Si giudica sul giro in cui il fuori
        #     ordine e' stato FABBRICATO dal ponte; il giro normale resta
        #     accanto come misura di quanto spesso accade da solo.
        #
        # ⛔⛔ QUI STAVA UN NUMERO FOSSILE, ED E' TOLTO IL 13 AGOSTO 2026 SERA
        #     (corsia C, coda C5).  Diceva «0 su **783**» con la marca `[M]`.
        #     ⚠ 783 e' il numero di campioni di UN giro (`b17-20260813-131128`,
        #     mediana 70,999): non era il denominatore dei fuori ordine del
        #     giro che ha prodotto il numero della fase, che di campioni ne ha
        #     **804**.  Un numero incollato in un commento non invecchia
        #     insieme al codice, e quello aveva gia' due giri di ritardo.
        #     ⇒ Il denominatore adesso NON si scrive qui: lo consegna
        #     `p5_fuori_ordine` a ogni giro, insieme al conto del prodotto —
        #     ed e' l'unico posto in cui puo' essere vero.
        "P5": (p5_fuori_ordine(camp5, p5g.get("conti_pagina_prima"),
                               p5g.get("conti_pagina"))
               if camp5 else
               p5_fuori_ordine(regime(camp),
                               verbale.get("conti_pagina_prima"),
                               verbale.get("conti_pagina"))),
        "P5_spontaneo": p5_fuori_ordine(regime(camp),
                                        verbale.get("conti_pagina_prima"),
                                        verbale.get("conti_pagina")),
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
    # ⛔ I CONTI DEL PRODOTTO, PRIMA E DOPO — e sono della forma vera, presi da
    #    un verbale VERO (`giro b17-20260813-193656`, /tmp/03-b17/verbale.json).
    #    Senza le DUE istantanee P5 non ha la meta' del fenomeno che gli serve
    #    e dice «non ho potuto guardare»: e' esattamente il ramo nuovo, e il
    #    verbale sintetico deve poterlo esercitare in tutt'e due i versi.
    conti_prima = {"stream": 100, "completi": 100, "consegnati": 98,
                   "dipinti": 98, "scartati_ordine": 0, "scartati_misura": 0,
                   "buchi": 0}
    conti_dopo = {"stream": 100 + quanti, "completi": 100 + quanti,
                  "consegnati": 98 + quanti, "dipinti": 98 + quanti,
                  "scartati_ordine": 0, "scartati_misura": 0, "buchi": 0}
    return {"giri": giri, "senza_marca": senza,
            "grana": {"salti": 4000, "minimo_ms": 0.005, "mediano_ms": 0.02},
            "isolata": True,
            "conti_pagina_prima": conti_prima, "conti_pagina": conti_dopo,
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


def _g_p5_conti_ciechi(v):
    """⛔⛔ IL GUASTO CHE CERTIFICA LA CURA DI C3: spariscono i conti del
    PRODOTTO, cioe' la meta' del fenomeno che il banco non puo' vedere da se'.

    ⭐ Prima della cura questo guasto non era nemmeno esprimibile: il banco non
       guardava quei conti, quindi toglierli non cambiava niente e P5 restava
       verde.  Adesso P5 deve dire «non ho potuto guardare» — e diventare
       ROSSO, perche' un anello giudicato su meta' del fenomeno non e' un
       anello giudicato.
    """
    v.pop("conti_pagina_prima", None)
    v.pop("conti_pagina", None)
    if "giro_p5" in v:
        v["giro_p5"].pop("conti_pagina_prima", None)
        v["giro_p5"].pop("conti_pagina", None)
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
    # ⛔ 13 agosto 2026 sera, corsia C: il guasto che certifica la cura di C3.
    ("P5 spariscono i conti del PRODOTTO (la cecita' per costruzione)",
     _g_p5_conti_ciechi, ["P5"]),
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
        # ...e gli altri che arrossiscono si CONTANO e si STAMPANO.
        #
        # ⛔⛔ QUI IL COMMENTO DICEVA UNA COSA CHE IL CODICE NON FA, ed e' stato
        #     riscritto il 13 agosto 2026 sera (corsia C/E) per dire il vero.
        #
        #     Diceva: «e NON deve far diventare rosso nient'altro di inatteso, o
        #     il controllo non sta distinguendo».  ⛔ Ma `preso` guarda **solo**
        #     che gli attesi siano rossi: gli `extra` finiscono in un ⚠ stampato
        #     accanto alla riga, e **non bocciano**.  ⇒ Chi leggeva il commento
        #     credeva che il banco pretendesse la separazione; il banco la
        #     stampa e basta.  E' la stessa forma della trappola n.3 — un banco
        #     che sembra piu' severo di quel che e' — dentro il commento invece
        #     che dentro il codice.
        #
        #     `[M]` il caso vivo: il guasto «P7 il ritmo e' morto» fa arrossire
        #     anche **P3 e P5**, e la riga passa lo stesso.
        #
        # ⭐ E CHE GLI `extra` NON BOCCINO E' UNA SCELTA, NON UNA DIMENTICANZA —
        #    decisa dal coordinatore il 13 agosto sera.  Stringere il controllo
        #    adesso boccerebbe il giro SANO e sposterebbe il metro **nel mezzo**
        #    della misura che si sta per fare (la corsia E deve sottrarre un
        #    «prima» e un «dopo» presi con lo stesso banco).  ⇒ Il metro non si
        #    tocca durante la misura: si tocca prima o dopo, e si dichiara.
        #    ⚠ Chi vorra' stringerlo dovra' prima spiegare perche' P7, tagliando
        #    i campioni a 15, DEBBA lasciare verdi P3 e P5 — che oggi e' una
        #    domanda aperta, non un difetto accertato.
        extra = [k for k in rossi if k not in attesi]
        dice("guasto «%s» → rossi %s (attesi %s)%s"
             % (nome, rossi or "nessuno", attesi,
                "  ⚠ e ne sporca altri: %s" % extra if extra else ""),
             preso)
        # RISANATO: si toglie il guasto e si ripretende il verde
        g2 = giudica(verbale_sintetico())
        dice("  risanato «%s»: torna tutto verde" % nome,
             all(g2[k].get("esito") for k in TUTTI))

    log("C-bis. ⛔⛔ P5 E LA CECITA' PER COSTRUZIONE — le TRE risposte devono "
        "essere TRE frasi diverse")
    # ⛔ Il difetto curato qui (corsia C, coda C3) e' che DUE stati del mondo
    #    davano la STESSA riga: «il fuori ordine non e' successo» e «il fuori
    #    ordine e' successo e il prodotto l'ha assorbito prima che io potessi
    #    vederlo».  E ce n'era un terzo, che non aveva riga affatto: «non ho i
    #    conti del prodotto».  ⇒ Si certificano tutt'e tre, sullo stesso
    #    verbale, cambiando UNA cosa per volta.
    def _senza_scavalcati(v):
        for g in v["giri"]:
            massimo = 0
            for c in g["campioni"]:
                massimo = max(massimo + 1, c.get("numero") or 0)
                c["numero"] = massimo
        return v

    base_p5 = _senza_scavalcati(copy.deepcopy(verbale_sintetico()))
    camp_p5 = regime(base_p5["giri"][0]["campioni"])

    r_zero = p5_fuori_ordine(camp_p5, base_p5["conti_pagina_prima"],
                             base_p5["conti_pagina"])
    dice("P5 (1) il fenomeno NON si e' presentato: rosso, e lo dice MISURATO "
         "ai due capi (0 visti dal banco, 0 `scartati_ordine` del prodotto)",
         (not r_zero["esito"]) and "NON ESEGUITO" in r_zero["perche"]
         and r_zero["scartati_dal_prodotto"] == 0)

    dopo_scarta = dict(base_p5["conti_pagina"])
    dopo_scarta["scartati_ordine"] = \
        base_p5["conti_pagina_prima"]["scartati_ordine"] + 30
    r_assorbito = p5_fuori_ordine(camp_p5, base_p5["conti_pagina_prima"],
                                  dopo_scarta)
    dice("P5 (2) il fenomeno C'E' STATO e il prodotto l'ha assorbito PRIMA del "
         "decodificatore: P5 diventa ESEGUITO e conta i 30 scartati che il "
         "banco non puo' vedere (scartati_dal_prodotto = %s)"
         % r_assorbito.get("scartati_dal_prodotto"),
         r_assorbito["esito"] and r_assorbito["scartati_dal_prodotto"] == 30
         and r_assorbito["fuori_ordine_totali"] == 30
         and "ESEGUITO" in r_assorbito["perche"])

    dice("P5 (1) e (2) NON dicono la stessa frase — ⛔ prima della cura la "
         "dicevano, ed e' il difetto che questo controllo esiste per non far "
         "tornare", r_zero["perche"] != r_assorbito["perche"]
         and r_zero["esito"] != r_assorbito["esito"])

    r_cieco = p5_fuori_ordine(camp_p5, None, None)
    dice("P5 (3) senza i conti del prodotto → NON passa, e dice «non ho potuto "
         "guardare» invece di «non eseguito» (`LEZIONI.md` §2.0)",
         (not r_cieco["esito"]) and r_cieco.get("cieco") is True
         and "NON HO POTUTO GUARDARE" in r_cieco["perche"]
         and "NON ESEGUITO" not in r_cieco["perche"])

    # ⛔ E il gemello negativo del conto: un contatore che va INDIETRO (la
    #    pagina si e' riaccesa a meta' giro) non e' «zero scartati».
    dice("il conto del prodotto che torna INDIETRO dice «non ho potuto», non "
         "«zero»",
         delta_conto({"scartati_ordine": 7}, {"scartati_ordine": 2},
                     "scartati_ordine") is None
         and delta_conto({"scartati_ordine": 2}, {"scartati_ordine": 7},
                         "scartati_ordine") == 5)

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

    log("E. ⛔ LA CORSIA E — il verbale, il palco, la finestra")
    # ⛔⛔ PERCHE' QUESTI CONTROLLI ESISTONO: quel che segue vive dentro
    #     `misura()`, che vuole due macchine, un server acceso e un browser ⇒
    #     **da qui non si puo' girare**.  Un pezzo di banco che non si puo'
    #     provare e' un pezzo di banco creduto.  ⇒ La logica sta in funzioni
    #     PURE, e qui si certificano una per una, col guasto dentro.

    # ── 1. IL VERBALE PER GIRO — il danno era «sovrascrivere in silenzio» ──
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        p1 = percorso_verbale(tmp, "b17-A")
        p2 = percorso_verbale(tmp, "b17-B")
        dice("verbale: due giri diversi danno due nomi diversi, e il giro sta "
             "DENTRO il nome", p1 != p2 and "b17-A" in p1 and "b17-B" in p2)
        dice("verbale: `--verbale` esplicito continua a comandare (chi ha uno "
             "script vecchio non si trova un file altrove)",
             percorso_verbale(tmp, "b17-A", "/x/y.json") == "/x/y.json")
        ult = os.path.join(tmp, "verbale-ultimo.json")
        scrivi_verbale(p1, {"giro": "b17-A"}, ult)
        dice("verbale: il primo giro si scrive (%s)" % os.path.basename(p1),
             os.path.exists(p1))
        # ⛔ IL GUASTO: si riprova a scrivere sullo STESSO nome.  Prima questa
        #    riga cancellava il verbale di prima **senza dire niente**, ed e'
        #    cosi' che il 13 agosto ne sono spariti tredici su quattordici.
        try:
            scrivi_verbale(p1, {"giro": "b17-A-bis"}, ult)
            alzato, dentro = False, None
        except RuntimeError as e:
            alzato, dentro = True, str(e)
        with open(p1) as f:
            rimasto = json.load(f)
        dice("⛔ verbale: riscrivere lo STESSO nome ALZA un errore, e il primo "
             "verbale e' ancora li' intatto",
             alzato and rimasto.get("giro") == "b17-A"
             and "C'E' GIA'" in (dentro or ""))
        # ── e il RISANATO: cambiato il giro, si scrive di nuovo ────────────
        scrivi_verbale(p2, {"giro": "b17-B"}, ult)
        dice("verbale RISANATO: cambiato il giro, il secondo si scrive e i due "
             "coesistono", os.path.exists(p1) and os.path.exists(p2))
        dice("verbale: `verbale-ultimo.json` PUNTA all'ultimo (ed e' un "
             "puntatore, non un verbale)",
             os.path.islink(ult)
             and os.path.realpath(ult) == os.path.realpath(p2))

    # ── 2. LA FINESTRA ESCLUSIVA SU DUE MACCHINE ──────────────────────────
    libera = {"solo": True, "perche": [], "carico": [0.1, 0.1, 0.1]}
    carica_ = {"solo": False, "perche": ["carico a 1 minuto 3.80 (massimo 1.00)"]}
    dice("finestra: libere tutt'e due ⇒ SOLO",
         unisci_scene(libera, dict(libera))["solo"])
    u = unisci_scene(libera, carica_)
    dice("finestra: libera di qua e CARICA di la' ⇒ NON solo, e la riga dice "
         "quale delle due (%s)" % (u["perche"][0][:40] if u["perche"] else "—"),
         (not u["solo"]) and any("NIC-OS" in g for g in u["perche"]))
    # ⛔⛔ IL GUASTO CHE CONTA, ed e' quello che un banco ingenuo sbaglia: la
    #     scena dell'altra macchina NON SI E' POTUTA LEGGERE.  Un banco che
    #     concludesse «solo» qui misurerebbe **mezzo anello** dichiarandosi
    #     pulito — `LEZIONI.md` §2.0 al punto in cui costa un numero di fase.
    m_ = unisci_scene(libera, None)
    dice("⛔⛔ finestra: la scena dell'ALTRA macchina non si legge ⇒ **NON "
         "SOLO**, e non «probabilmente sì»",
         (not m_["solo"]) and any("non ho guardato" in g or
                                  "NON si e' potuta leggere" in g
                                  for g in m_["perche"]))
    # ⭐ E l'arbitro deve saper leggere l'unione: il rifiuto esce dalla SUA
    #    bocca, o in giro ci sarebbero due idee diverse di «solo».
    _solo = solo_modulo()
    try:
        _solo.pretendi(m_)
        rifiutato = False
    except RuntimeError:
        rifiutato = True
    try:
        _solo.pretendi(unisci_scene(libera, dict(libera)))
        passato = True
    except RuntimeError:
        passato = False
    dice("finestra: `03-solo.pretendi()` legge l'unione — rifiuta quella cieca "
         "e lascia passare quella libera", rifiutato and passato)

    # ── 3. IL PALCO AI DUE ESTREMI ────────────────────────────────────────
    pal = {"chuwi": {"disable_gpu": False,
                     "pagina": {"codec_nome": "av1", "tela": [1920, 1080],
                                "webgl": {"disegnatore": "Mesa Intel(R) Graphics"}}},
           "server": {"nodi_di_rendering": []}}
    dice("palco: due letture identiche ⇒ regge",
         confronta_palco(pal, copy.deepcopy(pal))["regge"])
    # ⛔ IL GUASTO: il nodo di rendering cambia a meta' giro — cioe' esattamente
    #    quel che succederebbe se il «prima» fosse software e il «dopo»
    #    hardware **dentro lo stesso giro**.
    hw = copy.deepcopy(pal)
    hw["server"]["nodi_di_rendering"] = ["renderD128"]
    r_hw = confronta_palco(pal, hw)
    dice("⛔ palco: il NODO DI RENDERING cambia a meta' giro ⇒ NON regge, e la "
         "riga lo nomina",
         (not r_hw["regge"]) and any("nodi_di_rendering" in g
                                     for g in r_hw["perche"]))
    cod = copy.deepcopy(pal)
    cod["chuwi"]["pagina"]["codec_nome"] = "hevc"
    dice("⛔ palco: il CODEC negoziato cambia ⇒ NON regge (i due numeri non si "
         "sottrarrebbero)", not confronta_palco(pal, cod)["regge"])
    gpu = copy.deepcopy(pal)
    gpu["chuwi"]["disable_gpu"] = True
    dice("⛔ palco: `--disable-gpu` compare a meta' giro ⇒ NON regge — e' la "
         "bandiera che e' costata una corsia intera",
         not confronta_palco(pal, gpu)["regge"])
    r_meta = confronta_palco(pal, None)
    dice("palco: manca un estremo ⇒ NON regge, e dice «non ho potuto "
         "confrontare» invece di «non e' cambiato»",
         (not r_meta["regge"])
         and any("non ho potuto" in g for g in r_meta["perche"]))
    dice("palco: i campi PORTANTI sono dichiarati, non impliciti (%d)"
         % len(PALCO_PORTANTI), len(PALCO_PORTANTI) >= 5)

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


# ═══════════════════════════════════════════════════════════════════════════
# §7-quinquies  ⛔⛔ LA FINESTRA ESCLUSIVA — e QUI sono DUE macchine
# ═══════════════════════════════════════════════════════════════════════════
#
# ⭐ L'arbitro c'e' gia' ed e' certificato: `banchi/03-solo.py`.  ⛔ Ma porta
#    scritto in testa il proprio limite, e **riguarda questo banco in pieno**:
#
#      «Guarda UNA macchina sola: la sua.  L'anello del ritardo attraversa
#       NIC-OS *e* CHUWI ⇒ chi lo misura deve girarlo da tutt'e due le parti e
#       unire le due scene.  Un giro "solo" su CHUWI mentre il server e' carico
#       e' un numero contaminato che si dichiara pulito.»
#
# ⇒ Qui si fa esattamente quello, e ⛔ **la regola che tiene in piedi l'unione
#   e' una sola**: se la scena dell'altra macchina **non si e' potuta leggere**,
#   il verdetto e' **NON SOLO**.  Non «probabilmente sì», non «solo di qua»:
#   `LEZIONI.md` §2.0 — *«non c'e'» e «non ho potuto guardare» hanno lo stesso
#   aspetto*, e qui il secondo costerebbe un numero della fase.
def unisci_scene(qui, la, nome_qui="CHUWI", nome_la="NIC-OS"):
    """Le due scene in una sola.  ⛔ Funzione PURA, e si certifica.

    ⚠ Torna un dizionario della **stessa forma** che `03-solo.pretendi()` sa
      leggere (`solo` + `perche`), così l'arbitro resta uno solo e il rifiuto
      esce dalla sua bocca, non dalla nostra.
    """
    guai = []
    for nome, s in ((nome_qui, qui), (nome_la, la)):
        if s is None:
            guai.append(
                "⛔ la scena di %s NON si e' potuta leggere ⇒ conto come NON "
                "SOLO.  ⚠ Non e' «la' era libero»: e' che non l'ho guardato, e "
                "l'anello attraversa tutt'e due le macchine" % nome)
        elif not s.get("solo"):
            guai += ["%s: %s" % (nome, g) for g in (s.get("perche") or
                                                    ["ragione non registrata"])]
    return {"solo": not guai, "perche": guai,
            "scene": {nome_qui: qui, nome_la: la},
            "⛔ perche' DUE": "l'anello attraversa NIC-OS e CHUWI: una finestra "
                             "esclusiva su una macchina sola non e' una "
                             "finestra esclusiva (`03-solo.py`, limite n. 1)"}


def scena_esclusiva(a, mie_porte=(), miei_pid=(), solo_la=None,
                    pid_file_la=None):
    """La scena delle DUE macchine, adesso.

    ⚠ `solo_la` e' il percorso di `03-solo.py` **sul server** — ce lo porta
      `03-b17-lancia.sh porta`.  ⛔ Se di la' non c'e', questa funzione NON
      finge: torna una scena senza il pezzo del server, e l'unione dira' NON
      SOLO.
    """
    solo = solo_modulo()
    qui = solo.guarda(mie_porte=mie_porte, miei_pid=miei_pid)
    la = None
    percorso = solo_la or "/media/REMOTIX/src/03-solo.py"
    r = _sshpw("python3 %s --json" % percorso, silenzioso=True)
    testo = (r.stdout or "").strip().splitlines()
    for riga in reversed(testo):
        riga = riga.strip()
        if riga.startswith("{"):
            try:
                la = json.loads(riga)
            except ValueError:
                la = None
            break
    # ⛔⛔ E LE MIE PORTE VANNO TOLTE ANCHE DI LA' — trovato al primo giro vero,
    #     13 agosto 2026 sera, e senza questo la corsia E non misura MAI.
    #
    #     `03-solo.py --json` gira sul server SENZA sapere quali porte sono mie:
    #     dalla riga di comando non si possono dichiarare.  ⇒ Vedeva la 7605
    #     (il mio ponte) e la 7615 (il mio prodotto) come «porte altrui» e
    #     rispondeva NON SOLO — un rifiuto **permanente**, e per il banco stesso.
    #     ⛔ E' un falso rosso, cioe' la forma opposta di quella per cui
    #     l'arbitro esiste: costa uguale e si vede meno.
    #
    # ⭐ La correzione NON riscrive il giudizio: toglie le mie porte dall'elenco
    #    e richiama `_giudica()` **dell'arbitro**, cosi' la parola «solo»
    #    continua a voler dire una cosa sola ai due capi dell'anello.
    if isinstance(la, dict) and mie_porte:
        mie = set(int(p) for p in mie_porte)
        la["porte_mie_dichiarate_dal_banco"] = sorted(mie)
        la["porte_altrui"] = [p for p in (la.get("porte_altrui") or [])
                              if p not in mie]
        la["porte_mie"] = sorted(set(la.get("porte_mie") or []) | mie)
        la["solo"], la["perche"] = solo._giudica(la)
    # ⛔⛔ E I MIEI PROCESSI DI LA' — stessa forma delle porte, e senza questo il
    #     banco NON MISURA MAI.
    #
    #     `[M]` 14 agosto 2026: il banco si e' rifiutato per *«un vicino mangia
    #     CPU: **remotix** al 67,8 %»* — e quel `remotix` era **il figlio del
    #     prodotto che il banco stesso aveva acceso**, che bruciava CPU perche'
    #     stava codificando HEVC in software.  ⇒ Il consumo del prodotto **e'
    #     la misura**, non la contesa: un arbitro che lo conta come vicino
    #     rifiuta il banco per il fenomeno che il banco esiste per misurare.
    #
    # ⛔ E SI TOLGONO SOLO I MIEI, LETTI DAL MIO PIDFILE, non «tutti i
    #    remotix»: sulla stessa macchina girano i tre prodotti dell'utente
    #    (7448, 7501, 7561), e quelli restano vicini a tutti gli effetti.  ⚠ La
    #    differenza fra «tolgo me stesso» e «tolgo chiunque si chiami come me»
    #    e' la differenza fra una cura e un atteso allargato.
    if isinstance(la, dict) and pid_file_la:
        r2 = _sshpw("P=$(cat %s 2>/dev/null); [ -n \"$P\" ] && "
                    "{ echo $P; pgrep -P $P 2>/dev/null; "
                    "for f in $(pgrep -P $P 2>/dev/null); do "
                    "pgrep -P $f 2>/dev/null; done; }" % pid_file_la,
                    silenzioso=True)
        miei_la = set()
        for x in (r2.stdout or "").split():
            if x.isdigit():
                miei_la.add(int(x))
        la["miei_pid_dichiarati_dal_banco"] = sorted(miei_la)
        la["⛔ come li ho presi"] = (
            "dal pidfile del prodotto che HO ACCESO IO (%s) piu' i suoi figli e "
            "nipoti.  ⚠ NON «tutti i processi che si chiamano remotix»: i tre "
            "prodotti dell'utente restano vicini" % pid_file_la)
        if miei_la:
            fuori_ = [v for v in (la.get("vicini_affamati") or [])
                      if v.get("pid") not in miei_la]
            la["vicini_affamati_miei"] = [
                v for v in (la.get("vicini_affamati") or [])
                if v.get("pid") in miei_la]
            la["vicini_affamati"] = fuori_
            la["solo"], la["perche"] = solo._giudica(la)
        else:
            la["⛔ pid propri"] = (
                "non ho potuto leggere il pidfile di la': ⚠ i miei processi "
                "restano contati come vicini, e il rifiuto che ne segue va "
                "letto come «non ho potuto guardare», non come contesa")
    return unisci_scene(qui, la)


# ═══════════════════════════════════════════════════════════════════════════
# §7-quater  ⛔⛔ IL PALCO SI DICHIARA ACCANTO AL NUMERO — `LEZIONI.md` §2.0
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ *«Non c'e'» e «non ho potuto guardare» hanno lo stesso aspetto, e il secondo
#    e' piu' frequente del primo.*  Il 13 agosto 2026 e' costata **una corsia
#    intera di un piano**: una sonda chiedeva a Chrome se sapesse decodificare
#    HEVC **lanciandolo con `--disable-gpu`**, e i cinque «no» sono diventati
#    una conclusione («non e' un problema di codec, e' un problema di PALCO»)
#    su cui si e' costruito il lavoro di una sessione.
#
# ⚠ Qui il difetto NON c'era — `gpu=True` e' il predefinito e `--senza-gpu` e'
#   opt-in, quindi l'anello dei 74,58 ms non e' stato misurato al buio.  ⛔ **Ma
#   questo si sa leggendo il sorgente, non il verbale**, ed e' esattamente la
#   differenza che §2.0 vieta: un default non e' una dichiarazione.
#
# ⛔⛔ E PER LA CORSIA E LA POSTA E' PIU' ALTA CHE MAI: il «prima» e il «dopo»
#     si SOTTRAGGONO.  Se il giro nuovo girasse con un palco diverso da quello
#     vecchio — un'altra GPU, un altro codec negoziato, un altro nodo di
#     rendering — la differenza non sarebbe il codificatore, e nessuno potrebbe
#     accorgersene guardando i due numeri.  ⇒ Il palco entra nel verbale, **da
#     tutt'e due i lati dell'anello**, e ogni pezzo che manca si dichiara
#     «non ho potuto guardare» invece di sparire.
PALCO_PAGINA = """
(function () {
  const out = {};
  /* 1. LA GPU VISTA DALLA PAGINA — non il flag, quel che il motore vede. */
  try {
    const cv = document.createElement("canvas");
    const gl = cv.getContext("webgl2") || cv.getContext("webgl");
    if (!gl) out.webgl = null;
    else {
      const d = gl.getExtension("WEBGL_debug_renderer_info");
      out.webgl = { versione: gl.getParameter(gl.VERSION),
                    vendore: d ? gl.getParameter(d.UNMASKED_VENDOR_WEBGL)
                               : gl.getParameter(gl.VENDOR),
                    disegnatore: d ? gl.getParameter(d.UNMASKED_RENDERER_WEBGL)
                                   : gl.getParameter(gl.RENDERER),
                    mascherato: !d };
    }
  } catch (e) { out.webgl = "\\u26d4 " + e; }
  /* 2. IL CODEC NEGOZIATO, chiesto al prodotto e non indovinato. */
  try {
    const s = window.REMOTIX && window.REMOTIX.schermo;
    out.codec_numero = s ? s.codec : null;
    out.codec_nome = (s && typeof NOME_DEL_CODEC !== "undefined")
                     ? NOME_DEL_CODEC[s.codec] : null;
    out.stringa_codec = s ? (s.stringa_codec || s.stringa || null) : null;
    out.tela = s ? [s.tela_l, s.tela_a] : null;
    out.profondita = s ? s.profondita : null;
  } catch (e) { out.codec_numero = "\\u26d4 " + e; }
  /* 3. LA STRADA CHE IL PRODOTTO USA DAVVERO: WebCodecs, non <video>. */
  out.videodecoder = (typeof VideoDecoder !== "undefined");
  out.isolata = !!self.crossOriginIsolated;
  out.agente = navigator.userAgent;
  /* ⛔⛔ 4. SU QUALE SCHERMO STA DAVVERO QUESTO BROWSER — 13 agosto 2026 sera,
   *     rilievo della corsia D, e ribalta una conclusione della giornata.
   *
   *     Chrome IGNORA `DISPLAY` e sceglie Wayland da `XDG_SESSION_TYPE`: un
   *     banco che lancia Xvfb, gli punta `DISPLAY` addosso e crede di misurare
   *     li' puo' star misurando **sul desktop vero dell'utente**, con la GPU
   *     vera e con la contesa del desktop dentro il numero.
   *
   *     ⭐ E la misura che lo dice costa due parole: `screen`.  Su questa
   *        macchina 1280x1024 (o la misura data a Xvfb) = schermo finto;
   *        2560x1080 = il monitor dell'utente.  ⛔ Non si deduce dalle
   *        bandiere: le bandiere dicono che cosa si e' CHIESTO. */
  out.schermo_del_browser = { larghezza: screen.width, altezza: screen.height,
                              disponibile: [screen.availWidth, screen.availHeight],
                              rapporto_pixel: window.devicePixelRatio };
  return out;
})()
"""

# ⛔ E il secondo pezzo e' ASINCRONO: `isConfigSupported` torna una promessa, e
#    dice `powerEfficient` — cioe' se quella decodifica e' in HARDWARE.  ⚠ E'
#    una **dichiarazione**, non una decodifica: si scrive per quel che e'.
PALCO_DECODIFICA = """
(async function () {
  const out = {};
  if (typeof VideoDecoder === "undefined") return { errore: "niente VideoDecoder" };
  const s = window.REMOTIX && window.REMOTIX.schermo;
  const prove = [];
  const c = s && (s.stringa_codec || s.stringa);
  if (c) prove.push(c);
  prove.push("hev1.2.4.L120.B0", "av01.0.08M.10");
  for (const codec of prove) {
    try {
      const r = await VideoDecoder.isConfigSupported({ codec: codec,
                  codedWidth: 1920, codedHeight: 1080 });
      out[codec] = { supportato: !!r.supported,
                     efficiente: r.config ? !!r.config.hardwareAcceleration : null,
                     dichiarato: r.supported && r.config
                                 ? (r.config.hardwareAcceleration || null) : null };
    } catch (e) { out[codec] = { errore: String(e) }; }
  }
  return out;
})()
"""


def palco_del_server(registro_prodotto):
    """⛔ Il palco dell'ALTRO capo dell'anello, MISURATO da fuori.

    ⭐ Il nodo di rendering non si deduce e non si chiede al prodotto (che oggi
       **non lo scrive**): si guarda quali `/dev/dri/renderD*` i processi del
       prodotto hanno **aperti**.  Un descrittore aperto e' un fatto; un nome in
       un `Makefile` e' un'intenzione.

    ⛔ E il caso `nodi == []` NON e' «non lo so»: e' **la firma della codifica in
       SOFTWARE** — `libsvtav1` e `libx265` un nodo DRM non lo aprono.  ⇒ E'
       proprio il pezzo che la corsia E deve vedere cambiare fra il «prima» e il
       «dopo», e va letto insieme al codificatore, non da solo.
    """
    fuori = {}
    # ⛔⛔ SI PASSA DALL'AZIONE `palco` DI `03-b17-accendi.sh`, E GIRA DA ROOT.
    #     Il prodotto e' di root: `ls /proc/<pid>/fd` da utente normale risponde
    #     «Permission denied» e un lettore ingenuo leggerebbe **zero nodi** —
    #     cioe' «codifica in SOFTWARE» — proprio sul giro in cui la codifica e'
    #     in hardware.  ⇒ Il conto dei processi LETTI e di quelli NEGATI viaggia
    #     insieme ai nodi, o «nessun nodo» non si puo' interpretare.
    r = _sshpw("sudo -S -p 'Password sudo: ' bash "
               "/media/REMOTIX/src/03-b17-accendi.sh palco", silenzioso=True)
    d = None
    for riga in reversed((r.stdout or "").splitlines()):
        riga = riga.strip()
        if riga.startswith("{"):
            try:
                d = json.loads(riga)
            except ValueError:
                d = None
            break
    if d is None:
        fuori["nodi_di_rendering"] = None
        fuori["⛔ nodi"] = ("non ho potuto guardare: l'azione `palco` non ha "
                           "risposto JSON (ssh %d).  ⚠ NON e' «nessun nodo "
                           "aperto»" % r.returncode)
    else:
        nodi = d.get("nodi_di_rendering") or []
        fuori["nodi_di_rendering"] = nodi
        fuori["processi_del_prodotto"] = d.get("processi_remotix")
        fuori["descrittori_letti"] = d.get("letti")
        fuori["descrittori_negati"] = d.get("negati")
        fuori["utente_che_ha_guardato"] = d.get("utente")
        if not d.get("processi_remotix"):
            fuori["lettura_dei_nodi"] = (
                "⛔ NON HO POTUTO GUARDARE: nessun processo `remotix` vivo.  "
                "⚠ Zero nodi con zero processi NON e' «software»: e' «non "
                "c'era niente da guardare»")
        elif d.get("negati"):
            fuori["lettura_dei_nodi"] = (
                "⛔ NON HO POTUTO GUARDARE fino in fondo: %d processi su %d mi "
                "hanno negato i descrittori (utente «%s»).  ⚠ I nodi visti "
                "sono un MINIMO, non un conto"
                % (d["negati"], d["processi_remotix"], d.get("utente")))
        elif nodi:
            # ⛔⛔ QUESTA RIGA DICEVA «⇒ la codifica passa dall'HARDWARE», ED E'
            #     STATA SMENTITA DA UN GIRO — 13 agosto 2026 notte, corsia E,
            #     ed e' una forma d'errore che avevo appena finito di togliere
            #     ad altri e ho rimesso io.
            #
            #     `[M]` giro `E-B-hardware-stessapagina`: il binario con VA-API
            #     tiene **renderD128 aperto** e nello stesso giro codifica
            #     **`av01.0.09M.10`** — cioe' AV1, che su questa macchina in
            #     hardware **NON ESISTE** (`av1_vaapi` esce 218).  ⇒ Il nodo era
            #     aperto e i fotogrammi passavano da `libsvtav1`, in software.
            #
            # ⭐ Un descrittore aperto dice che il CONTESTO VA-API esiste, non
            #    che i fotogrammi ci passino.  ⇒ Si consegna il fatto e si
            #    dichiara che da solo non decide: chi legge deve guardarlo
            #    INSIEME al codec confessato dal prodotto.
            fuori["lettura_dei_nodi"] = (
                "⚠ %s APERTO/I dal prodotto (%d processi, %d letti, 0 negati). "
                "⛔ E NON VUOL DIRE «codifica in hardware»: un descrittore "
                "aperto dice che il contesto VA-API esiste, non che i "
                "fotogrammi ci passino.  `[M]` un giro con renderD128 aperto "
                "ha codificato `av01…`, e AV1 in hardware su questa macchina "
                "non esiste.  ⇒ Si legge INSIEME a `riga_del_codificatore`: "
                "hardware e' «nodo aperto **E** codec che l'hardware sa fare»"
                % (", ".join(nodi), d["processi_remotix"], d["letti"]))
        else:
            fuori["lettura_dei_nodi"] = (
                "⛔ NESSUN nodo DRM aperto dal prodotto (%d processi, %d "
                "letti, 0 negati) ⇒ la codifica e' in SOFTWARE.  ⭐ E' una "
                "misura: i descrittori si sono letti tutti"
                % (d["processi_remotix"], d["letti"]))
    # ⭐ E il codificatore per come lo confessa il prodotto: la riga del PRIMO
    #   fotogramma porta la stringa di codec vera, letta sui byte in uscita.
    #
    # ⛔⛔ E SI ANCORA ALL'ACCENSIONE DI ADESSO — trovato provandolo, 13 agosto
    #     2026 sera.  Il registro del prodotto e' in APPEND (`>> "$LOG"` in
    #     `03-b17-accendi.sh`): un `grep | tail -1` pesca la riga dell'ULTIMO
    #     giro che ha codificato, che puo' essere quello di un'ora fa e di un
    #     altro codec.  ⇒ E' la forma del **numero fossile**, con l'aggravante
    #     che qui il fossile finirebbe nel verbale come «il codec di questo
    #     giro».  ⭐ L'ancora e' l'ultima riga «pronto: https://», che il
    #     prodotto scrive UNA volta per accensione: si guarda solo da li' in
    #     giu'.
    # ⚠ E si fa a COSTO FISSO, non accumulando: il registro del prodotto sta a
    #   17 MB dopo mezza giornata, e un `awk` che se lo tiene in una variabile
    #   non finisce.  ⇒ si trova la RIGA dell'ultima accensione e si legge da
    #   li' in giu' con `tail -n +N`.
    rc = _sshpw("N=$(grep -an 'pronto: https:' %s 2>/dev/null | tail -1 | "
                "cut -d: -f1); [ -n \"$N\" ] && tail -n +$N %s | "
                "grep -ao 'PRIMO fotogramma codificato[^\"]*' | tail -1"
                % (registro_prodotto, registro_prodotto), silenzioso=True)
    riga = ""
    for x in (rc.stdout or "").splitlines():
        if "PRIMO fotogramma codificato" in x:
            riga = x.strip()
    fuori["riga_del_codificatore"] = riga or None
    fuori["⛔ da dove"] = ("letta SOLO dopo l'ultima riga «pronto: https://» del "
                          "registro, cioe' dentro QUESTA accensione: il "
                          "registro e' in append e un `tail` pescherebbe il "
                          "giro di prima")
    if not riga:
        fuori["⛔ codificatore"] = (
            "in questa accensione il prodotto non ha ancora scritto la riga "
            "del PRIMO fotogramma: ⛔ non e' «non ha codificato», e' «non ho "
            "potuto guardare» — e se compare a misura finita, va riletta")
    # ⚠ E QUEL CHE IL PRODOTTO NON DICE, detto qui perche' non lo si cerchi:
    #   il **nome del componente** (`libsvtav1` / `hevc_vaapi` / `libx265`) e'
    #   in `codificatore_confessione()` ma NON viene scritto in nessun
    #   registro.  ⇒ Da fuori si sa il codec e si sa il nodo, non il nome.
    fuori["⚠ quel che di la' non si puo' leggere"] = (
        "il NOME del componente di codifica: il prodotto lo tiene in "
        "`conf.componente` e non lo scrive da nessuna parte.  ⇒ software o "
        "hardware si distinguono dal NODO DRM aperto, non dal nome.  Se la "
        "corsia B facesse scrivere quel nome nel registro, questa riga "
        "diventerebbe una lettura diretta invece che un indizio")
    return fuori


def palco_dichiarato(palco, a, registro_prodotto):
    """⭐ Tutto il palco, dai due capi, in un dizionario solo.

    ⛔ Nessun campo si deduce da un default: quel che non si e' potuto leggere
       resta `None` **con accanto il motivo**.
    """
    d = {"⛔": "il palco si DICHIARA accanto al numero (`LEZIONI.md` §2.0): un "
               "numero senza il palco da cui e' uscito non e' confrontabile con "
               "un altro numero"}
    bandiere = list(getattr(palco, "bandiere", []) or [])
    d["chuwi"] = {
        "bandiere_del_browser": bandiere or None,
        # ⭐ La domanda si fa ESPLICITA, non si lascia a chi legge l'elenco:
        #   e' la bandiera che ha spento quel che la sonda stava cercando.
        "disable_gpu": ("--disable-gpu" in bandiere) if bandiere else None,
        "gpu_chiesta_al_banco": bool(getattr(palco, "gpu", None)),
        "schermo": getattr(palco, "schermo", None),
    }
    if not bandiere:
        d["chuwi"]["⛔ bandiere"] = ("il palco non ha registrato le bandiere: "
                                    "⚠ NON e' «nessuna bandiera»")
    # ⛔⛔ SU CHE PALCO GIRA DAVVERO IL BROWSER — e si misura in DUE modi che
    #     non passano l'uno per l'altro (rilievo della corsia D, 13 agosto).
    #
    #     (a) `--ozone-platform`: Chrome IGNORA `DISPLAY` e sceglie Wayland da
    #         `XDG_SESSION_TYPE`.  Senza quella bandiera il browser puo' essere
    #         **sul desktop vero dell'utente** mentre il banco crede di averlo
    #         messo su Xvfb — con la GPU vera e la contesa del desktop dentro
    #         il numero.
    #     (b) ⭐ `xlsclients`: **chi e' attaccato all'Xvfb**.  E' la controprova
    #         che non passa dal browser: zero clienti sullo schermo che il banco
    #         ha acceso vuol dire che li' non c'e' nessuno.
    ozone = [x for x in bandiere if x.startswith("--ozone-platform")]
    d["chuwi"]["ozone_platform"] = ozone[0] if ozone else None
    d["chuwi"]["⛔ ozone"] = (
        "⛔ NESSUNA `--ozone-platform` passata: Chrome sceglie da se', e da "
        "`XDG_SESSION_TYPE` sceglie Wayland ⇒ questo browser puo' NON essere "
        "sull'Xvfb che il banco ha acceso.  ⚠ Si guardi `xlsclients` e "
        "`schermo_del_browser` prima di credere alla bandiera `DISPLAY`"
        if not ozone else
        "⭐ passata: %s — il palco e' quello dichiarato" % ozone[0])
    d["chuwi"]["xdg_session_type"] = os.environ.get("XDG_SESSION_TYPE")
    d["chuwi"]["wayland_display_tolto_dal_banco"] = True
    schermo = getattr(palco, "schermo", None)
    if schermo:
        r = subprocess.run(["xlsclients", "-display", schermo],
                           capture_output=True, text=True)
        if r.returncode == 0:
            clienti = [x for x in r.stdout.splitlines() if x.strip()]
            d["chuwi"]["clienti_sull_xvfb"] = len(clienti)
            d["chuwi"]["clienti_sull_xvfb_elenco"] = clienti[:10]
            d["chuwi"]["lettura_del_palco"] = (
                "⛔⛔ ZERO clienti attaccati a %s: il browser che sto misurando "
                "NON E' sull'Xvfb del banco.  ⇒ Sta sul palco che Chrome ha "
                "scelto da se' — su questa macchina il desktop dell'utente.  "
                "⚠ Non e' un intoppo da curare adesso: e' il palco di QUESTO "
                "numero, e va scritto accanto al numero" % schermo
                if not clienti else
                "⭐ %d client(i) attaccati a %s: il browser e' sull'Xvfb del "
                "banco" % (len(clienti), schermo))
        else:
            d["chuwi"]["clienti_sull_xvfb"] = None
            d["chuwi"]["lettura_del_palco"] = (
                "⛔ `xlsclients` non ha risposto (%d): ⚠ non e' «zero clienti», "
                "e' «non ho potuto guardare»" % r.returncode)
    for nome, espressione, attendi in (
            ("pagina", PALCO_PAGINA, False),
            ("decodifica_dichiarata", PALCO_DECODIFICA, True)):
        try:
            d["chuwi"][nome] = palco.valuta(espressione, attendi=attendi)
        except Exception as e:                       # noqa: BLE001
            d["chuwi"][nome] = None
            d["chuwi"]["⛔ " + nome] = "non ho potuto guardare: %s" % str(e)[:120]
    d["server"] = palco_del_server(registro_prodotto)
    d["host_del_prodotto"] = a.host
    return d


def _pesca(d, *strada):
    for k in strada:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


# ⛔ I campi PORTANTI: quelli che, se cambiano a meta' giro, fanno sì che il
#    numero prima e il numero dopo **non si sottraggano**.  ⚠ Non e' l'elenco
#    di tutto quel che sta nel palco: e' l'elenco di quel che cambia il
#    significato del numero.
PALCO_PORTANTI = (
    ("chuwi", "disable_gpu"),
    ("chuwi", "pagina", "codec_nome"),
    ("chuwi", "pagina", "webgl", "disegnatore"),
    ("chuwi", "pagina", "tela"),
    ("server", "nodi_di_rendering"),
    # ⛔⛔ E LO SCHERMO SU CUI IL BROWSER STA DAVVERO — aggiunto il 13 agosto
    #     2026 sera, dopo che la corsia D ha misurato che Chrome ignora
    #     `DISPLAY`.  Se il «prima» finisse sull'Xvfb e il «dopo» sul desktop
    #     dell'utente, la differenza sarebbe il PALCO e la chiameremmo «la
    #     codifica in hardware».
    ("chuwi", "pagina", "schermo_del_browser", "larghezza"),
    ("chuwi", "clienti_sull_xvfb"),
)


def confronta_palco(prima, dopo):
    """⛔ Il palco si legge PRIMA e DOPO — funzione PURA.

    ⚠ Stessa forma delle porte contate ai due estremi: un palco che cambia in
      mezzo alla misura fa uscire un numero che sembra buono.  ⛔ E come per le
      porte, questa guardia **non vede** un cambio avvenuto e disfatto nel
      mezzo: lo dichiara invece di lasciarlo credere.
    """
    if not prima or not dopo:
        return {"regge": False,
                "perche": ["⛔ non ho potuto confrontare: manca il palco %s"
                           % ("d'apertura" if not prima else "di chiusura")],
                "⚠ e non e'": "«il palco non e' cambiato»"}
    guai = []
    for strada in PALCO_PORTANTI:
        a, b = _pesca(prima, *strada), _pesca(dopo, *strada)
        if a != b:
            guai.append("⛔ %s: da %r a %r" % (".".join(strada), a, b))
    return {"regge": not guai, "perche": guai,
            "campi_guardati": [".".join(s) for s in PALCO_PORTANTI],
            "⚠ quel che questa guardia NON vede":
                "un palco cambiato e rimesso a posto FRA i due estremi"}


def stampa_palco(p):
    """Il palco, a schermo, ⛔ accanto al numero e non in fondo al file."""
    if not p:
        ko("⛔ IL PALCO NON E' STATO DICHIARATO: il numero qui sopra non e' "
           "confrontabile con nessun altro numero (`LEZIONI.md` §2.0)")
        return
    c, s = p.get("chuwi") or {}, p.get("server") or {}
    pg = c.get("pagina") or {}
    w = pg.get("webgl") if isinstance(pg, dict) else None
    inf("CHUWI  · `--disable-gpu`: %s   · schermo %s"
        % ("⛔ SI" if c.get("disable_gpu") else "no", c.get("schermo")))
    inf("CHUWI  · gpu vista dalla pagina: %s"
        % (w.get("disegnatore") if isinstance(w, dict) else
           "⛔ NIENTE WEBGL — e allora ogni «no» di questo giro va letto come "
           "«non ho potuto guardare»"))
    inf("CHUWI  · codec negoziato: %s (%s)  · tela %s  · WebCodecs: %s"
        % (pg.get("codec_nome"), pg.get("codec_numero"), pg.get("tela"),
           pg.get("videodecoder")))
    inf("SERVER · nodo di rendering: %s"
        % (s.get("lettura_dei_nodi") or s.get("⛔ nodi")))
    inf("SERVER · %s" % (s.get("riga_del_codificatore")
                         or s.get("⛔ codificatore"))[:220])
    # ⛔ E IL VERDETTO SI FA SUI DUE INSIEME, mai su uno solo: il nodo dice che
    #    il contesto c'e', il codec dice che cosa e' passato di li'.
    riga = s.get("riga_del_codificatore") or ""
    nodi = s.get("nodi_di_rendering")
    if nodi is None:
        inf("SERVER · ⛔ codifica: NON HO POTUTO GUARDARE")
    elif "av01" in riga:
        inf("SERVER · ⛔ codifica: **IN SOFTWARE** — il codec e' AV1, e AV1 in "
            "hardware su questa macchina NON ESISTE (`av1_vaapi` esce 218), "
            "%s" % ("e il nodo %s e' aperto lo stesso: il contesto VA-API c'e' "
                    "ma i fotogrammi non ci passano" % ", ".join(nodi) if nodi
                    else "e infatti nessun nodo DRM e' aperto"))
    elif "hev1" in riga and nodi:
        inf("SERVER · ⭐ codifica: **IN HARDWARE** — codec HEVC E nodo %s "
            "aperto: le due cose insieme" % ", ".join(nodi))
    elif "hev1" in riga:
        # ⛔ IL RAMO CHE MANCAVA, e sul giro A ha prodotto una riga fuorviante
        #    («codec e nodo non concordano») per uno stato che invece e'
        #    perfettamente coerente: HEVC codificato in SOFTWARE non apre
        #    nessun nodo DRM, ed e' quel che ci si aspetta da x265.
        inf("SERVER · ⛔ codifica: **IN SOFTWARE** — codec HEVC ma NESSUN nodo "
            "DRM aperto: e' x265, non VA-API")
    elif riga:
        inf("SERVER · ⚠ codifica: codec e nodo non concordano — nodi %s, riga "
            "«%s»" % (nodi, riga[:90]))


# ═══════════════════════════════════════════════════════════════════════════
# §7-ter  ⛔⛔ UN VERBALE PER GIRO — e la ragione e' un danno gia' avvenuto
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `--verbale` aveva un percorso FISSO (`/tmp/03-b17/verbale.json`), scritto
#    con `open(..., "w")`: **ogni giro cancellava il precedente, in silenzio**.
#    `[M]` 13 agosto 2026: dei **quattordici** giri della giornata ne sopravvive
#    **UNO**, l'ultimo.  ⇒ Il verbale del giro da 74,576 — il numero della
#    fase — non esiste piu', e nemmeno quello del giro con P3 rosso: per questo
#    «quale parte di P3 fosse rossa» e' `[?]` **per sempre**.
#
# ⛔⛔ E PER LA CORSIA E SAREBBE PEGGIO: i due verbali che si devono SOTTRARRE
#     — il «prima» in software e il «dopo» in hardware — hanno lo stesso nome.
#     Il secondo giro cancellerebbe il primo, e la differenza non si potrebbe
#     nemmeno rifare.
#
# ⭐ La cura e' in tre pezzi, e nessuno dei tre e' «stare attenti»:
#      1. il nome porta dentro il GIRO;
#      2. ⛔ si RIFIUTA di sovrascrivere un verbale che c'e' gia' — il danno e'
#         avvenuto proprio perche' sovrascrivere era silenzioso;
#      3. ⚠ resta un `verbale-ultimo.json` che PUNTA all'ultimo, per non
#         rompere le abitudini — ma e' un puntatore, e si dice che lo e'.
def percorso_verbale(lavoro, giro, chiesto=None):
    """Dove va il verbale di QUESTO giro.  ⛔ Funzione PURA."""
    if chiesto:
        return chiesto
    return os.path.join(lavoro or ".", "verbali", "verbale-%s.json" % giro)


def scrivi_verbale(percorso, v, ultimo=None):
    """Scrive il verbale, e ⛔ **rifiuta di cancellarne uno**.

    ⚠ Torna il percorso scritto.  Alza `RuntimeError` se il file c'e' gia': non
      e' prudenza, e' che l'unico modo in cui si perdono tredici verbali e'
      sovrascriverli senza che nessuno lo veda.
    """
    if os.path.exists(percorso):
        raise RuntimeError(
            "⛔ IL VERBALE C'E' GIA': %s\n"
            "   Non lo sovrascrivo.  Due giri con lo stesso nome vogliono dire "
            "che uno dei due sta per sparire — ed e' cosi' che il 13 agosto "
            "2026 sono andati perduti TREDICI verbali su quattordici, fra cui "
            "quello del numero della fase.\n"
            "   ⇒ Cambia `--giro`, oppure sposta il file di la' se sei sicuro."
            % percorso)
    os.makedirs(os.path.dirname(percorso) or ".", exist_ok=True)
    with open(percorso, "w") as f:
        json.dump(v, f, ensure_ascii=False)
    if ultimo:
        # ⚠ Un PUNTATORE, non una copia: una copia sarebbe un secondo verbale
        #   con la stessa forma e nessun giro dentro il nome, cioe' di nuovo la
        #   cosa che si sta togliendo di mezzo.
        try:
            tmp = ultimo + ".tmp"
            if os.path.islink(tmp) or os.path.exists(tmp):
                os.unlink(tmp)
            os.symlink(os.path.abspath(percorso), tmp)
            os.replace(tmp, ultimo)
        except OSError as e:
            dub("⚠ non ho potuto rifare il puntatore %s (%s): il verbale c'e' "
                "lo stesso, e sta in %s" % (ultimo, e, percorso))
    return percorso


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

    log("0-bis. ⛔⛔ SONO SOLO? — su TUTT'E DUE le macchine, e prima di "
        "accendere il mio palco")
    # ⛔ PRIMA di accendere Xvfb e Chrome: `03-solo.py` non sa distinguere il
    #    proprio rumore da quello d'altri (limite n. 3), e un banco che si
    #    misurasse addosso si assolverebbe da solo.
    solo = solo_modulo()
    v["scena_prima"] = scena_esclusiva(
        # ⛔ LE PORTE MIE SONO TRE, non due: il ponte (`--porta`), l'ancora
        #    (`--ancora`) e ⛔ **il prodotto dietro il ponte** — che sta sul
        #    server, e' acceso da me, e senza dichiararlo l'arbitro di la' lo
        #    conta come un estraneo e rifiuta per sempre.
        a, mie_porte=(a.porta, a.ancora, a.porta_dentro),
        solo_la=getattr(a, "solo_la", None),
        pid_file_la=getattr(a, "pid_file_la", None))
    for nome, s in (v["scena_prima"].get("scene") or {}).items():
        if s is None:
            ko("%-7s ⛔ la scena non si e' potuta leggere" % nome)
        else:
            inf("%-7s carico %s · porte altrui %s · vicini %d · /tmp %s MB"
                % (nome, (s.get("carico") or ["?"])[0], s.get("porte_altrui"),
                   len(s.get("vicini_affamati") or []), s.get("tmp_liberi_mb")))
    # ⛔ E SE NON SONO SOLO, MI RIFIUTO — l'eccezione la alza l'arbitro, non io.
    #    ⚠ Non c'e' nessuna bandiera per scavalcarlo, ed e' voluto: una via
    #      d'uscita e' la stessa mossa di allargare l'atteso finche' passa.
    #      Se serve la finestra, la si chiede al coordinatore.
    try:
        solo.pretendi(v["scena_prima"])
    except RuntimeError as e:
        ko(str(e))
        ko("⛔ NON MISURO.  ⇒ Chiedi la finestra esclusiva al coordinatore: "
           "l'anello attraversa NIC-OS e CHUWI, e le vuole tutt'e due.")
        return 4
    ok("solo su tutt'e due le macchine: un tempo misurato adesso e' un tempo")

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
        url = "https://%s:%d/" % (a.host, a.porta)
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
        # ⛔⛔ L'ISTANTANEA DEI CONTI DEL PRODOTTO **PRIMA** — corsia C, coda C3.
        #     I contatori della pagina sono CUMULATIVI dall'accensione: senza
        #     il «prima» non c'e' nessuna differenza da fare, e P5 resterebbe
        #     cieco sulla meta' del fenomeno che il banco non puo' vedere (i
        #     fotogrammi scavalcati, che il prodotto scarta a
        #     `src/pagina.html:1578`, prima del decodificatore).
        # ⛔⛔ IL PALCO, DICHIARATO PRIMA DEL PRIMO NUMERO (§7-quater).
        #     Si legge QUI e non all'accensione: il codec si negozia con la
        #     sessione, e un palco letto prima direbbe «codec: null» — cioe'
        #     l'assenza di informazione travestita da informazione.
        log("5-bis. ⛔ IL PALCO, dai due capi dell'anello")
        v["palco_prima"] = palco_dichiarato(palco, a, a.registro_prodotto)
        stampa_palco(v["palco_prima"])
        _s0 = c.valuta(STATO, attendi=False)
        v["conti_pagina_prima"] = (_s0 or {}).get("conti")
        if not v["conti_pagina_prima"]:
            dub("⚠ non ho l'istantanea dei conti del prodotto PRIMA: P5 dira' "
                "«non ho potuto guardare», e sara' vero")
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
                # ⛔⛔ IL PONTE SI LEGGE **MENTRE RITARDA**, non alla fine.
                #
                #     `[M]` 14 agosto 2026: avevo scagionato il ponte da P1
                #     rosso leggendo il suo verbale **a giro finito** — cioe'
                #     con `ritardo_ms = 0`, perche' `metti_ritardo(a, 0, ...)`
                #     lo rimette a zero prima di chiudere.  ⇒ Uno scarto di
                #     consegna di 0 us misurato a ritardo ZERO **non dice
                #     niente** su come consegna quando ritarda: e' un dato
                #     preso in una condizione diversa da quella che si voleva
                #     giudicare.  ⛔ E' la stessa forma d'errore che questo
                #     banco esiste per trovare negli altri.
                #
                # ⭐ Una lettura per valore di N, all'ULTIMA mano: il ponte
                #    riscrive il verbale ogni 2 s, quindi li' dentro c'e' lo
                #    scarto misurato con QUEL ritardo attivo.
                #    ⚠ Una lettura per mano costerebbe 25 giri di `ssh`.
                if mano == mani - 1:
                    rp = _sshpw("cat %s" % a.verbale_ponte, silenzioso=True)
                    for riga in (rp.stdout or "").splitlines():
                        riga = riga.strip()
                        if riga.startswith("{"):
                            try:
                                v.setdefault("ponte_per_n", {})[str(n)] = \
                                    json.loads(riga)
                            except ValueError:
                                pass
                            break
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
            # ⛔ E l'assetto si DICHIARA insieme al suo modo di degenerazione:
            #    fo=400 con raffica=4 NON degenera (4 % 400 = 4).  Se un giorno
            #    qualcuno mettesse raffica multipla di fo, il ponte smetterebbe
            #    di riordinare e lo direbbe da se' (`03-b17-ponte.py`, conto
            #    `degenere`), invece di consegnare zero fuori ordine in
            #    silenzio — che e' quel che e' successo all'autoprova.
            metti_ritardo(a, 0, 400, a.giro + "-p5", fo_ms=45.0, raffica=4)
            time.sleep(1.0)
            # ⛔ L'istantanea dei conti del prodotto PRIMA del giro di P5, e va
            #    presa DOPO l'assestamento e PRIMA di svuotare i campioni: la
            #    differenza deve coprire la stessa finestra dei fotogrammi.
            _s5 = c.valuta(STATO, attendi=False)
            c.valuta("window.__B17.prendi(), true")
            camp5, _, _, u5 = raccogli(c, min(14.0, a.secondi))
            oro5 = Orologi(parete, anc_a, {"c_e": False},
                           v.get("origine_pagina_ms", 0))
            camp5 = arricchisci(camp5, oro5)
            v["giro_p5"] = {"campioni": camp5,
                            "distribuzione": dist([x["ritardo_ms"]
                                                   for x in regime(camp5)]),
                            "assetto_iniettore": {"fuori_ordine": 400,
                                                  "raffica": 4,
                                                  "fuori_ordine_ms": 45.0,
                                                  "degenere": (4 % 400) == 0},
                            "conti_pagina_prima": (_s5 or {}).get("conti"),
                            "conti_pagina": (u5 or {}).get("pagina")}
            metti_ritardo(a, 0, 0, a.giro)
            inf("fuori ordine fabbricato: %s campioni, mediana %s ms"
                % (v["giro_p5"]["distribuzione"].get("n"),
                   v["giro_p5"]["distribuzione"].get("mediana")))
            # ⛔ E si stampa QUEL CHE IL BANCO NON PUO' VEDERE, letto dal
            #    prodotto: i fotogrammi scavalcati non arrivano mai al vetro.
            _sc = delta_conto(v["giro_p5"].get("conti_pagina_prima"),
                              v["giro_p5"].get("conti_pagina"),
                              "scartati_ordine")
            _cg = delta_conto(v["giro_p5"].get("conti_pagina_prima"),
                              v["giro_p5"].get("conti_pagina"), "consegnati")
            inf("e quel che il banco NON vede, letto dal prodotto: "
                "`scartati_ordine` %s su %s consegnati in questa finestra  "
                "(⛔ `None` vuol dire «non ho potuto guardare», non «zero»)"
                % (_sc, _cg))
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

        log("11-bis. ⛔ IL PALCO, RILETTO — un palco che cambia a meta' giro fa "
            "uscire un numero che sembra buono")
        v["palco_dopo"] = palco_dichiarato(palco, a, a.registro_prodotto)
        v["palco_regge"] = confronta_palco(v.get("palco_prima"), v["palco_dopo"])
        (ok if v["palco_regge"]["regge"] else ko)(
            "il palco e' lo stesso ai due estremi"
            if v["palco_regge"]["regge"] else
            "⛔ IL PALCO E' CAMBIATO DURANTE LA MISURA: " +
            " · ".join(v["palco_regge"]["perche"]))

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

    # ⛔ E LA SCENA SI RILEGGE ALLA FINE: il carico e' una fotografia, non una
    #    sorveglianza (`03-solo.py`, limite n. 2).  ⚠ Qui NON si rifiuta piu' —
    #    il giro e' fatto — ma il verbale porta dentro se un vicino si e'
    #    acceso a meta', e chi legge il numero lo vede accanto al numero.
    v["scena_dopo"] = scena_esclusiva(
        # ⛔ LE PORTE MIE SONO TRE, non due: il ponte (`--porta`), l'ancora
        #    (`--ancora`) e ⛔ **il prodotto dietro il ponte** — che sta sul
        #    server, e' acceso da me, e senza dichiararlo l'arbitro di la' lo
        #    conta come un estraneo e rifiuta per sempre.
        a, mie_porte=(a.porta, a.ancora, a.porta_dentro),
        solo_la=getattr(a, "solo_la", None),
        pid_file_la=getattr(a, "pid_file_la", None))
    v["scena_regge"] = {
        n: solo_modulo().confronta(
            (v["scena_prima"].get("scene") or {}).get(n) or {},
            (v["scena_dopo"].get("scene") or {}).get(n) or {})
        for n in ("CHUWI", "NIC-OS")}
    for n, r3 in v["scena_regge"].items():
        (ok if r3["regge"] else ko)(
            "%-7s la finestra ha retto" % n if r3["regge"] else
            "⛔ %-7s la finestra NON ha retto: %s" % (n, "; ".join(r3["guai"])))

    # ⛔ UN VERBALE PER GIRO, e si RIFIUTA di cancellarne uno (§7-ter).
    dove = percorso_verbale(a.lavoro, a.giro, a.verbale)
    scrivi_verbale(dove, v, os.path.join(a.lavoro or ".", "verbale-ultimo.json"))
    a.verbale = dove
    inf("verbale: %s (%d byte)" % (dove, os.path.getsize(dove)))
    inf("⚠ `%s/verbale-ultimo.json` e' un PUNTATORE all'ultimo giro, non un "
        "verbale: il verbale di questo giro e' quello qui sopra, e porta il "
        "giro dentro il nome" % (a.lavoro or "."))

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
              # ⛔ IL PALCO E LA FINESTRA VANNO NELLA RIGA DEPOSITATA, non solo
              #    nel verbale: chi legge `03-b17-esiti.jsonl` per confrontare
              #    due giri deve vedere **da che palco** escono, o confronta
              #    due numeri che non si sottraggono.
              "palco": v.get("palco_prima"),
              # ⛔ Il ponte MENTRE ritardava: e' il testimone di P1.
              "ponte_per_n": v.get("ponte_per_n"),
              "palco_regge": v.get("palco_regge"),
              "scena_esclusiva": {
                  "prima": {"solo": (v.get("scena_prima") or {}).get("solo"),
                            "perche": (v.get("scena_prima") or {}).get("perche")},
                  "dopo": {"solo": (v.get("scena_dopo") or {}).get("solo"),
                           "perche": (v.get("scena_dopo") or {}).get("perche")},
                  "regge": v.get("scena_regge")},
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
    # ⛔ La porta del PRODOTTO dietro il ponte: il banco non ci parla mai
    #    direttamente, ⚠ ma e' SUA — l'ha accesa lui — e va dichiarata
    #    all'arbitro della finestra esclusiva, o l'arbitro la conta come un
    #    estraneo sul server e rifiuta ogni giro.
    p.add_argument("--porta-dentro", type=int, default=7615)
    p.add_argument("--comando-ponte", default="/tmp/03-b17/comando")
    p.add_argument("--utente", default="nicfio")
    p.add_argument("--parola-file")
    p.add_argument("--secondi", type=float, default=25.0)
    p.add_argument("--ritardi", default="0,25,60",
                   help="i ritardi noti di P1, in ms")
    p.add_argument("--schermo", default=":85")
    p.add_argument("--diagnosi", type=int, default=9605)
    p.add_argument("--lavoro", default="/tmp/03-b17")
    # ⛔ NIENTE PERCORSO FISSO — §7-ter.  Senza `--verbale` il nome lo fa il
    #    GIRO: `<lavoro>/verbali/verbale-<giro>.json`.  Il vecchio predefinito
    #    (`/tmp/03-b17/verbale.json`) ha cancellato tredici verbali su
    #    quattordici il 13 agosto 2026, fra cui quello del numero della fase.
    p.add_argument("--verbale", default=None,
                   help="⚠ di norma NON si passa: il nome lo fa il giro. "
                        "Passandolo si torna a un nome fisso, e due giri con "
                        "lo stesso nome adesso danno un ERRORE invece di "
                        "sovrascriversi")
    p.add_argument("--senza-gpu", action="store_true")
    p.add_argument("--gancio-scena", help="il comando che ACCENDE la scena, "
                   "eseguito DOPO il primo fotogramma dipinto (prima il monitor "
                   "virtuale non esiste)")
    p.add_argument("--gancio-scena-spegni", help="⛔ il comando che la SPEGNE: "
                   "senza, P3(a) non si puo' eseguire")
    p.add_argument("--registro-prodotto", default="/media/REMOTIX/tmp/03-b17/registro.log")
    # ⛔ L'arbitro della finestra esclusiva DALL'ALTRA PARTE: l'anello
    #    attraversa due macchine, e `03-solo.py` ne guarda una sola.
    # ⛔ Il pidfile del prodotto che il banco ha acceso SUL SERVER: serve a
    #    riconoscere i PROPRI processi.  Senza, il banco si rifiuta da se'
    #    perche' il suo prodotto sta codificando — cioe' sta misurando.
    # ⛔ Il verbale del PONTE sul server: si legge MENTRE ritarda, o non dice
    #    niente su come consegna quando ritarda (rilievo del 14 agosto).
    p.add_argument("--verbale-ponte",
                   default="/media/REMOTIX/tmp/03-b17/ponte.json",
                   help="il verbale che il ponte riscrive ogni 2 s")
    p.add_argument("--pid-file-la",
                   default="/media/REMOTIX/tmp/03-b17/pid",
                   help="il pidfile del prodotto MIO sul server")
    p.add_argument("--solo-la", default="/media/REMOTIX/src/03-solo.py",
                   help="dove sta `03-solo.py` SUL SERVER (ce lo porta "
                        "`03-b17-lancia.sh porta`)")
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
        g = stampa_verdetto(v, a)
        # ⛔⛔ IL ROSSO VA NEL CODICE D'USCITA, NON NELLA PROSA — curato il
        #     13 agosto 2026 sera (corsia C), e la cura e' MISURATA sullo
        #     stesso verbale prima e dopo.
        #
        #     Qui c'era `return 0` incondizionato: `stampa_verdetto()` stampa i
        #     rossi con `ko()` e poi il programma usciva **verde**.  ⇒ Chi
        #     rileggeva un verbale gia' salvato — che e' proprio il modo in cui
        #     si rilegge il numero della fase — vedeva sempre 0.
        #     ⚠ Il catalogo diceva «tre banchi che escono SEMPRE 0, due curati,
        #     il terzo e' ancora li' (`03-b19-ritardo-worker.py --verdetto`)».
        #     ⛔ Erano QUATTRO: il quarto e' questo, cioe' il banco che ha
        #     prodotto il numero della fase 3, e non lo aveva contato nessuno.
        #     `[M]` sullo stesso verbale `/tmp/03-b17/verbale.json` (giro
        #     `b17-20260813-193656`), P5 rosso a stampa: **prima uscita 0,
        #     dopo uscita 1**.
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
    # ⛔⛔ E IL PALCO STA QUI, ATTACCATO AL NUMERO — non in fondo al file e non
    #     in un altro documento.  Un numero senza il palco da cui e' uscito non
    #     e' confrontabile con nessun altro numero (`LEZIONI.md` §2.0), e la
    #     corsia E il suo mestiere lo fa **sottraendone due**.
    log("⛔ IL PALCO DA CUI ESCE QUESTO NUMERO")
    stampa_palco(v.get("palco_prima"))
    sc = v.get("scena_prima") or {}
    if sc:
        (inf if sc.get("solo") else ko)(
            "finestra esclusiva: %s"
            % ("⭐ ero solo su tutt'e due le macchine" if sc.get("solo")
               else "⛔ NON ero solo — " + "; ".join(sc.get("perche") or [])))
    else:
        ko("⛔ la finestra esclusiva NON e' stata verificata: questo numero "
           "puo' essere la contesa")
    # ⛔⛔ SE P1 E' ROSSO, SI DICE **DOVE** VA IL SURPLUS — 14 agosto 2026.
    #
    #     Un P1 rosso da solo dice «il metro non torna» e manda a cercare
    #     dappertutto.  ⭐ Ma il verbale ha i giri a ogni N, e la scomposizione
    #     si puo' fare su ciascuno: il surplus sta in UN tratto, e nominarlo
    #     e' la differenza fra una riserva e una diagnosi.
    #     `[M]` giro `E2-B-hardware-hevc`: tutto nel tratto 2, e il ritmo NON
    #     cala (30,18 · 30,01 · 30,33) ⇒ la saturazione e' SMENTITA.
    if not g["P1"].get("esito"):
        log("⛔ P1 E' ROSSO — dove va il surplus, tratto per tratto")
        base_n = next((x for x in v.get("giri", [])
                       if x.get("ritardo_chiesto_ms") == 0), None)
        s0 = scomponi(regime((base_n or {}).get("campioni", [])))
        for gg in v.get("giri", []):
            n_ms = gg.get("ritardo_chiesto_ms")
            if not n_ms:
                continue
            cc = regime(gg.get("campioni", []))
            sn = scomponi(cc)
            iv = sorted(b["t1"] - a2["t1"] for a2, b in zip(cc, cc[1:])
                        if 0 < b["t1"] - a2["t1"] < 500)
            fps = round(1000.0 / iv[len(iv) // 2], 2) if iv else None
            inf("N=%-4g  ritmo %s/s  (se il ritmo NON cala, non e' saturazione)"
                % (n_ms, fps))
            for k in s0:
                a3, b3 = s0.get(k, {}), sn.get(k, {})
                if not isinstance(a3, dict) or "mediana" not in a3:
                    continue
                # ⛔ IL NOME NON E' `d`: `d` in questa funzione E' LA
                #    DISTRIBUZIONE, e riusarlo la sovrascrive con un float —
                #    poi `verdetto(d, …)` esplode con AttributeError.
                #    `[M]` 14 agosto 2026: e' successo davvero, e l'eccezione
                #    e' uscita con **codice 1**, cioe' lo STESSO di un P1 rosso
                #    legittimo ⇒ si e' nascosta dietro un rosso plausibile e ha
                #    fatto saltare il deposito della riga.  E' la trappola n.4
                #    del catalogo, rifatta da chi la stava curando.
                salto = round(b3.get("mediana", 0) - a3["mediana"], 3)
                if abs(salto) >= 0.5:
                    inf("   %-56s %+8.3f  (chiesti %g)" % (k[:56], salto, n_ms))

    log("LA SCOMPOSIZIONE")
    for k, x in scomponi(camp).items():
        inf("%-58s %s" % (k, json.dumps(x, ensure_ascii=False)))
    log("IL VERDETTO")
    inf(json.dumps(verdetto(d, v.get("errore_orologio_us", 0)),
                   ensure_ascii=False, indent=1))
    return g


if __name__ == "__main__":
    sys.exit(principale())
