#!/usr/bin/env node
/* 07-b61 — L'ANCORA DELL'AUDIO, provata SUL CODICE VERO e non su una copia.
 *
 *     node banchi/07-b61-ancora.js
 *
 * ⛔ PERCHE' ESISTE — 21 agosto 2026.  `07-b61-conto-audio.py` ha chiuso la
 *    `[?]` di `fasi/07` §8 leggendo il registro della sessione vera: la coda
 *    dell'audio non e' un cuscino, e' un **serbatoio a senso unico** che si
 *    accorcia di 20 ms a ogni datagram perduto e non si riempie mai.  La cura
 *    e' ancorare la riproduzione all'`istante` del server (`RCP.md` §6.3).
 *
 *    ⇒ Questo banco misura se la cura fa quel che dice, **prima** che la si
 *    porti su una sessione dell'utente.
 *
 * ⛔⛔ E NON RISCRIVE `suona()`: la RITAGLIA da `src/pagina.html` e la esegue.
 *
 *      Un banco che si riscrivesse lo scheduler accanto misurerebbe la propria
 *      copia, e resterebbe verde il giorno in cui il prodotto diverge da lei.
 *      E' la forma D5 di `LEZIONI.md` — un binario stantio che resta verde —
 *      travestita da banco.  ⇒ Qui la regione audio del prodotto viene
 *      ritagliata fra due marche, eseguita dentro un `AudioContext` finto di
 *      cui questo banco governa l'orologio, e alimentata con datagram veri
 *      nell'inquadratura di §6.3.
 *
 * ⭐ IL CONTROLLO POSITIVO E' UN GUASTO INNESTATO NELLA COPIA RITAGLIATA, non
 *    nel prodotto: si rimette **lo scheduler del 17 agosto** (`a.prossimo +=
 *    n/48000`, la scaletta per successione) riscrivendo il testo prima di
 *    eseguirlo, e il banco deve vedere tornare i due difetti.  ⛔ Se non li
 *    vede, non e' un banco: e' un contatore che dice sempre di si'.
 *
 * ⚠ QUEL CHE QUESTO BANCO NON DICE: gira su un orologio finto e su un
 *   `AudioContext` finto.  Dice che l'ALGORITMO ha le proprieta' dichiarate —
 *   non che il suono esce pulito da una scheda vera.  Quello lo dice solo una
 *   sessione, e dopo di lei l'utente. */
"use strict";
const fs = require("fs");
const path = require("path");

const PAGINA = path.join(__dirname, "..", "src", "pagina.html");
const MARCA_DA = "const AUDIO_FREQUENZA = 48000";
const MARCA_A = "⭐⭐ GLI APPUNTI";

function ritaglia() {
  const t = fs.readFileSync(PAGINA, "utf8");
  const i = t.indexOf(MARCA_DA);
  const j = t.indexOf(MARCA_A);
  if (i < 0 || j < 0 || j <= i)
    throw new Error("⛔ le marche della regione audio non ci sono piu' in "
      + "src/pagina.html: questo banco non sa piu' che cosa sta provando");
  // si torna indietro fino all'inizio del commento che apre la regione appunti
  let k = t.lastIndexOf("/*", j);
  return t.slice(i, k);
}

/* ⛔ IL GUASTO INNESTATO — la scaletta per successione del 17 agosto.
 *   Si rimette esattamente quel che c'era: `quando` = `a.prossimo`, e
 *   `a.prossimo` che avanza sommando invece di essere ricalcolato. */
function innesta_successione(src) {
  const da = "    let quando;\n    if (ist_us > 0) {";
  if (!src.includes(da)) throw new Error("⛔ non trovo dove innestare il guasto");
  const fine = "    } else {";
  const i = src.indexOf(da);
  const j = src.indexOf(fine, i);
  if (j < 0) throw new Error("⛔ non trovo la fine del ramo dell'ancora");
  const vecchio = "    let quando;\n    if (false) {\n";
  let fuori = src.slice(0, i) + vecchio + src.slice(j);
  /* ⛔⛔ E NON BASTA SPEGNERE L'ANCORA — 21 agosto 2026, secondo giro.
   *
   *     Il codice curato tiene `a.prossimo` come **massimo** dei blocchi
   *     programmati, e lo azzera quando l'ancora si sposta.  ⚠ Lasciando
   *     quelle due righe dentro la copia «guasta», la copia non era piu' il
   *     codice del 17 agosto: era un ibrido, e il banco confrontava la cura
   *     con qualcosa che non e' mai esistito.  ⇒ Il discriminante della
   *     raffica dava 270 invece di 590, cioe' **assolveva** lo scheduler
   *     vecchio.
   *
   * ⭐ Un guasto innestato vale solo se e' il guasto VERO. */
  /* ⚠ Il massimo c'e' solo se la pagina porta la finestra di riordino, che il
     22 agosto 2026 e' uscita dal mandato (e' fase 9).  ⇒ Se non c'e' non e' un
     guasto del banco: si innesta quel che c'e'.  ⛔ E si DICE, perche' un
     innesto che salta in silenzio e' un guasto non innestato. */
  const max = "    a.prossimo = Math.max(a.prossimo, quando + fotogrammi / AUDIO_FREQUENZA);";
  if (fuori.includes(max))
    fuori = fuori.replace(max, "    a.prossimo += fotogrammi / AUDIO_FREQUENZA;");
  else
    console.log("   ⚠ niente `Math.max` da togliere: la pagina non porta la "
              + "finestra di riordino (fase 9)");
  fuori = fuori.split("        a.prossimo = 0;\n").join("");
  fuori = fuori.split("        a.prossimo = 0;          /* stessa ragione: il massimo si azzera */\n").join("");
  return fuori;
}

/* ⛔⛔ IL GUASTO CHE HA FATTO TACERE UNA SESSIONE VERA, rimesso apposta.
 *
 *     Due righe: si toglie il margine dal confronto (cosi' l'uguaglianza
 *     esatta diventa «maggiore» per il rumore dell'aritmetica) e si riapre la
 *     finestra della tirata aggiornando `primo_suono` a ogni blocco.  ⇒ Ogni
 *     blocco annulla il precedente 230 ms prima del suo turno: SILENZIO, con
 *     `coda` ferma, `BUCHI 0`, `pieni 0` e `suonati == ricevuti`.
 *
 * ⭐ Se il banco non diventa rosso qui, non sa vedere il silenzio — e un banco
 *    dell'audio che non sa vedere il silenzio non serve a niente. */
/* ⛔ IL GUASTO DELLO STALLO: si richiude la finestra della tirata al riarmo,
 *    cioe' si torna al codice del 21 agosto — `primo_suono` scritto una volta
 *    sola nella vita della sessione.  ⭐ E' la differenza esatta fra «la coda
 *    torna al cuscino» e «la coda resta gonfia per il resto della sessione». */
function innesta_tirata_chiusa(src) {
  const a = "        a.primo_suono = null;\n      }";
  if (!src.includes(a)) throw new Error("⛔ non trovo la riapertura al riarmo");
  return src.replace(a, "      }");
}

function innesta_silenzio(src) {
  let s = src;
  const a = "> AUDIO_CUSCINO_MS + AUDIO_ANCORA_MARGINE_MS";
  if (!s.includes(a)) throw new Error("⛔ non trovo il margine da togliere");
  s = s.replace(a, "> AUDIO_CUSCINO_MS - 0.0000001");
  const b = "      if (a.primo_suono === null) a.primo_suono = quando;";
  if (!s.includes(b)) throw new Error("⛔ non trovo dove riaprire la finestra");
  s = s.replace(b, "      a.primo_suono = quando;");
  return s;
}

/* ── L'ambiente finto: un orologio che governo io ────────────────────────── */

function ambiente(registro) {
  registro.sospeso = registro.sospeso || false;
  registro.svegliabile = false;
  let ora = 0;                       // secondi, l'orologio dell'AudioContext
  const partite = [];                // (quando, fotogrammi) di ogni sorgente
  const vive = [];                   // le sorgenti in scaletta non ancora finite
  /* ⛔⛔ E LE SORGENTI FINTE DEVONO FINIRE DAVVERO — 21 agosto 2026.
   *
   *     La prima scrittura di questo ambiente non chiamava MAI `onended`: le
   *     sorgenti partivano e sparivano.  ⇒ Il banco non poteva distinguere
   *     «ha suonato» da «e' stata fermata prima del suo turno», ⛔ ed e'
   *     esattamente il difetto che poi ha fatto tacere una sessione vera con
   *     tutti i contatori verdi.  ⚠ Il banco era passato al 13 su 13 sopra
   *     quel difetto.
   *
   * ⇒ Qui `onended` scatta in tutt'e due i modi, come nei browser: quando
   *   l'orologio supera la fine naturale, e subito quando qualcuno chiama
   *   `stop()`.  E' quel che rende leggibili `usciti` e `tagliati`. */
  function scadono() {
    for (let i = vive.length - 1; i >= 0; i--) {
      const s = vive[i];
      if (ora + 1e-9 >= s._fine) {
        vive.splice(i, 1);
        if (s.onended) s.onended();
      }
    }
  }
  /* ⛔⛔ E IL CONTESTO FINTO DEVE SAPER NASCERE SOSPESO — 22 agosto 2026.
   *
   *     Nasceva sempre `running`, cioe' nello stato in cui un browser vero non
   *     nasce **mai** prima di un gesto.  ⇒ Il banco non poteva vedere ne' che
   *     `suona()` butta i blocchi a orologio fermo, ne' — peggio — che la
   *     frase «il suono parte al primo clic» non aveva codice sotto.
   *     ⚠ `[M]` A7: in headless il contesto e' rimasto sospeso 90 s **dopo un
   *     clic vero**.
   *
   * ⭐ Qui `sospeso: true` lo fa nascere fermo, e `amb.gesto()` fa quel che fa
   *    un dito sullo schermo: nient'altro.  Se il prodotto non ha un
   *    ascoltatore, non succede niente — ed e' esattamente quel che il banco
   *    deve poter vedere. */
  const ascoltatori = [];
  class Contesto {
    constructor(o) {
      this.sampleRate = o.sampleRate;
      this.state = registro.sospeso ? "suspended" : "running";
      this.destination = {}; this._chiuso = false;
    }
    /* ⛔ Fermo vuol dire FERMO: e' il difetto che l'orologio finto nascondeva
       quando avanzava comunque. */
    get currentTime() { return this.state === "running" ? ora : 0; }
    createBuffer(ch, n) {
      const dati = [];
      for (let c = 0; c < ch; c++) dati.push(new Float32Array(n));
      return { length: n, getChannelData: (c) => dati[c] };
    }
    createBufferSource() {
      const s = {
        buffer: null, onended: null, _fermata: false, _fine: 0,
        connect() {},
        stop() {
          if (s._fermata) return;
          s._fermata = true;
          const i = vive.indexOf(s); if (i >= 0) vive.splice(i, 1);
          if (s.onended) s.onended();
        },
        start(t) {
          partite.push({ quando: t, n: s.buffer.length });
          s._fine = t + s.buffer.length / 48000;
          vive.push(s);
        }
      };
      return s;
    }
    /* ⚠ `resume()` NON sveglia da solo: come nei motori veri, senza un gesto
       la promessa puo' restare li'.  Si sveglia solo `amb.gesto()`. */
    resume() {
      if (registro.svegliabile) this.state = "running";
      return Promise.resolve();
    }
    close() { this._chiuso = true; }
  }
  const g = {
    AudioContext: Contesto, webkitAudioContext: Contesto,
    /* Il `window` che il prodotto usa per l'ascoltatore del risveglio. */
    addEventListener: (nome, f) => ascoltatori.push({ nome: nome, f: f }),
    removeEventListener: (nome, f) => {
      const i = ascoltatori.findIndex((x) => x.nome === nome && x.f === f);
      if (i >= 0) ascoltatori.splice(i, 1);
    },
    performance: { now: () => ora * 1000 },
    setInterval: () => 0, clearInterval: () => {},
    document: { body: { dataset: {} }, hasFocus: () => true },
    fetch: () => Promise.resolve(),
    nota: (r) => registro.push(String(r)),
    TASTI_VISTI: 0, TASTI_ULTIMO: "", schermo: null,
    AudioDecoder: undefined, EncodedAudioChunk: undefined
  };
  return { g, partite, ora: () => ora, ascoltatori: ascoltatori,
           avanza: (s) => { ora += s; scadono(); },
           /* ⭐ Un dito sullo schermo, e nient'altro. */
           gesto: () => {
             registro.svegliabile = true;
             for (const x of ascoltatori.slice()) x.f();
           } };
}

/* Un datagram audio di §6.3: tipo 0x0401, codec 2 (PCM), istante, campioni.
 * ⛔ PCM e non Opus apposta: il percorso PCM e' sincrono e non chiede
 *    `AudioDecoder`, ⚠ ma passa per LA STESSA `suona()` — cioe' per l'unica
 *    cosa che questo banco sta provando. */
function datagram(ist_us, fotogrammi) {
  const b = new ArrayBuffer(12 + fotogrammi * 4);
  const v = new DataView(b);
  v.setUint16(0, 0x0401); v.setUint16(2, 2); v.setBigUint64(4, BigInt(ist_us));
  for (let i = 0; i < fotogrammi * 2; i++) v.setInt16(12 + i * 2, 3000, true);
  return new Uint8Array(b);
}

/* Il lettore finto dei datagram: gli si spinge dentro un blocco per volta. */
function filo() {
  const coda = [], attesa = [];
  return {
    wt: { datagrams: { readable: { getReader: () => ({
      read() {
        if (coda.length) return Promise.resolve({ value: coda.shift(), done: false });
        return new Promise((ris) => attesa.push(ris));
      }
    }) } } },
    spingi(b) {
      if (attesa.length) attesa.shift()({ value: b, done: false });
      else coda.push(b);
    }
  };
}

/* ── La scena: un flusso di blocchi da 20 ms con un profilo di perdita ───── */

async function gira(src, scena) {
  const registro = [];
  registro.sospeso = !!scena.sospeso;
  const amb = ambiente(registro);
  const f = filo();
  // ⛔ Si esegue la regione RITAGLIATA dal prodotto, con l'ambiente finto
  //    passato per argomento invece che per variabile globale: cosi' due giri
  //    dello stesso processo non si sporcano a vicenda.
  const fabbrica = new Function(
    "window", "performance", "setInterval", "clearInterval", "document",
    "fetch", "nota", "TASTI_VISTI", "TASTI_ULTIMO", "schermo", "AudioDecoder",
    "EncodedAudioChunk",
    src + "\n;return { avvia_audio, audio_conti, audio_ferma, "
        + "AUDIO_CUSCINO_MS, dammi: () => AUDIO };");
  const M = fabbrica(amb.g, amb.g.performance, amb.g.setInterval,
    amb.g.clearInterval, amb.g.document, amb.g.fetch, amb.g.nota, 0, "", null,
    undefined, undefined);

  M.avvia_audio(f.wt);
  const A = M.dammi();

  const PASSO = 0.020;                        // 20 ms per blocco
  const N = scena.blocchi;
  const code = [];
  const IST0 = scena.ist0 || 1000000;         // µs
  const ist_di = (k) => IST0 + k * 20000;

  /* ⭐ L'ORDINE DI CONSEGNA, che non e' per forza quello di produzione.
   *    `scena.scambia(i)` vera vuol dire «il blocco i arriva DOPO l'i+1»:
   *    e' quel che fa un jitter piu' corto del passo, ed e' la scena che il
   *    banco non aveva.  ⚠ `scena.tardivo(i)` sposta il blocco molto piu' in
   *    la', oltre il cuscino: quello si DEVE buttare. */
  const ordine = [];
  for (let i = 0; i < N; i++) ordine.push(i);
  if (scena.scambia)
    for (let i = 0; i + 1 < N; i++)
      if (scena.scambia(i)) { const t = ordine[i]; ordine[i] = ordine[i + 1];
                              ordine[i + 1] = t; i++; }
  if (scena.tardivo)
    for (let i = 0; i < N; i++)
      if (scena.tardivo(i)) {
        const j = ordine.indexOf(i);
        if (j >= 0 && j + 40 < N) { ordine.splice(j, 1); ordine.splice(j + 40, 0, i); }
      }

  /* ⭐⭐ LO STALLO DEL THREAD PRINCIPALE, ed e' la scena che mancava.
   *
   *     Per `stallo_n` passi non si legge niente — il tempo pero' passa, come
   *     quando il thread principale e' occupato — e poi il mucchio arriva
   *     TUTTO INSIEME.  ⛔ E' quel che `[M]` e' successo sul ferro il 22
   *     agosto: la coda e' saltata da 266 a 519 ms e non e' piu' scesa. */
  let trattenuti = [];
  for (let k = 0; k < ordine.length; k++) {
    const i = ordine[k];
    const in_stallo = scena.stallo_a !== undefined
      && k >= scena.stallo_a && k < scena.stallo_a + (scena.stallo_n || 0);
    if (in_stallo) {
      if (!scena.perde(i)) trattenuti.push(ist_di(i));
      amb.avanza(PASSO);
      if (k % 5 === 4) code.push(Math.round(A.coda_ms()));
      continue;
    }
    if (trattenuti.length) {
      /* il mucchio, tutto in un colpo e senza far passare il tempo */
      for (const ist of trattenuti) {
        f.spingi(datagram(ist, 960));
        await new Promise((r) => setImmediate(r));
      }
      trattenuti = [];
    }
    if (!scena.perde(i)) {
      f.spingi(datagram(ist_di(i), 960));
      await new Promise((r) => setImmediate(r));   // lascia girare il lettore
      // ⛔ E il doppione: la rete a volte consegna due volte, e la regola
      //    vecchia lo scartava per un motivo sbagliato ma lo scartava.
      if (scena.doppia && scena.doppia(i)) {
        f.spingi(datagram(ist_di(i), 960));
        await new Promise((r) => setImmediate(r));
      }
    }
    // ⭐ IL GESTO DELL'UTENTE, se la scena ne prevede uno.
    if (scena.gesto_a === k) amb.gesto();
    // ⭐ IL TEMPO PASSA: e' la cosa che il codice vecchio non guardava.  ⛔ In
    //    una raffica NON passa — i blocchi arrivano tutti insieme.
    amb.avanza(scena.raffica && k < scena.raffica ? 0 : PASSO);
    if (k % 5 === 4) code.push(Math.round(A.coda_ms()));
  }
  const c = M.audio_conti();
  const esito = {
    coda: code, coda_fine: c.in_coda_ms,
    coda_min: Math.min(...code), coda_max: Math.max(...code),
    buchi: A.riarmi || 0, mancati: c.mancati, ricevuti: c.ricevuti,
    suonati: c.suonati, pieni: c.scartati_pieno, aoff: c.aoff_ms,
    usciti: c.usciti, tagliati: c.tagliati, tirate: c.tirate,
    sospesi: c.sospesi, risvegli: c.risvegli,
    ascoltatori: amb.ascoltatori.length,
    vecchi: c.scartati_vecchi,
    registro
  };
  M.audio_ferma();
  return esito;
}

/* ── Le scene, e per ognuna l'atteso scritto PRIMA ───────────────────────── */

/* ⛔ Ogni scena porta il suo DISCRIMINANTE: il campo su cui la cura promette
 *    una differenza, con l'intervallo atteso di qua e di la'.  ⚠ Senza, una
 *    scena in cui le due colonne coincidono per costruzione — il flusso pulito
 *    — passerebbe il controllo positivo senza provare niente.
 *
 * ⛔⛔ E DUE DI QUESTI ATTESI ERANO SCRITTI SBAGLIATI AL PRIMO GIRO, il 21
 *     agosto 2026.  Si riscrivono con accanto l'errore, che e' `LEZIONI.md`
 *     §1.11: la predizione stava scritta prima, e per questo l'errore si vede.
 *
 *     · «con la scaletta vecchia e le perdite la coda finisce sotto i 200 ms»
 *       — ⛔ FALSO: finisce a **250**, perche' l'ultima perdita l'ha svuotata e
 *       il riarmo la rimette al cuscino.  Il danno non e' nella coda finale:
 *       e' nei **BUCHI**, che sono 3 contro 0.  ⇒ Guardare la coda alla fine
 *       avrebbe assolto lo scheduler vecchio;
 *     · «con la sola ancora la raffica dell'attacco finisce a 250» — ⛔ FALSO:
 *       `[M]` **290**, con un blocco buttato per traboccamento.  L'ancora si
 *       aggancia al primo blocco della raffica e i venti dietro hanno gia' il
 *       loro posto piu' in la'.  ⇒ E' il difetto che ha prodotto la seconda
 *       meta' della cura (`a.primo_suono`), e senza questo banco sarebbe
 *       arrivato su una sessione dell'utente. */
const SCENE = [
  { nome: "flusso pulito, 500 blocchi (10 s)",
    scena: { blocchi: 500, perde: () => false },
    ancora: { coda: [245, 255], buchi: 0, mancati: 0 },
    // ⚠ Nessun discriminante: senza perdite e senza raffica le due strade
    //   coincidono, ed e' giusto che coincidano.  Si dichiara.
    discrimina: null },

  { nome: "perdita 0,6 % a strappi (la sessione vera del 21 agosto)",
    scena: { blocchi: 3000,
             perde: (i) => (i > 500 && i < 520) || (i > 1500 && i < 1512)
                        || (i > 2400 && i < 2410) },
    ancora: { coda: [245, 255], buchi: 0, mancati: 39 },
    discrimina: { campo: "buchi", ancora: [0, 0], vecchio: [1, null] } },

  { nome: "raffica all'attacco: 20 blocchi insieme (l'anello del figlio)",
    scena: { blocchi: 500, raffica: 20, perde: () => false },
    ancora: { coda: [245, 275], buchi: 0, mancati: 0 },
    discrimina: { campo: "coda_fine", ancora: [245, 275], vecchio: [500, null] } },

  /* ⭐⭐ LO STALLO DI META' SESSIONE — `[M]` sul ferro, 22 agosto 2026.
   *
   *     ⛔ Senza la cura la coda si gonfia del mucchio e **non scende piu'**:
   *     e' il ritardo che l'utente aveva confermato, che torna da solo.
   *     ⭐ Con la cura la finestra della tirata si riapre al riarmo, il mucchio
   *     vecchio si butta, e la coda torna al cuscino.
   * ⚠ E l'atteso della coda ha una tolleranza larga in basso: dopo un riarmo
   *   il primo campione puo' cadere prima che la scaletta si sia riempita. */
  /* ⛔ TREDICI blocchi e non venti, e la differenza e' tutta la lezione: con
   *    venti il mucchio porta la coda a 250+400 = 650, cioe' OLTRE il tetto dei
   *    600, e il traboccamento la rimette a posto da se'.  ⚠ Con tredici sta a
   *    510 — **sotto il tetto** — e li' non la salva nessuno.  ⇒ E' esattamente
   *    la misura vista sul ferro (519), ed e' il motivo per cui il difetto era
   *    invisibile: la rete di sicurezza esisteva e passava sopra. */
  { nome: "stallo di 260 ms a meta' sessione, poi il mucchio tutto insieme",
    scena: { blocchi: 900, perde: () => false, stallo_a: 400, stallo_n: 13 },
    ancora: { coda: [245, 290], buchi: [1, null], mancati: 0 },
    discrimina: { campo: "coda_fine", ancora: [245, 290], vecchio: [400, null] } },

  /* ⭐⭐ IL CONTESTO CHE NASCE SOSPESO E SI SVEGLIA AL GESTO — la scena che
   *     il banco non aveva, ed e' quella in cui il prodotto prometteva senza
   *     mantenere.  ⛔ Prima del gesto: tutto buttato, zero usciti (ed e'
   *     giusto).  ⭐ Dopo il gesto: si sente, e la coda si arma dal presente.
   *     ⚠ E `ascoltatori 0` alla fine dice che il gestore si e' tolto da se'. */
  { nome: "contesto sospeso, gesto dell'utente a 5 s: si sveglia",
    scena: { blocchi: 800, perde: () => false, sospeso: true, gesto_a: 250 },
    ancora: { coda: [245, 275], buchi: 0, mancati: 0 },
    riordino: { sospesi: [240, 260], risvegli: [1, 3], ascoltatori: [0, 0] },
    discrimina: null },

  /* ⛔ E il rovescio, che e' il difetto vero: nessun gesto MAI.  ⚠ Qui non si
   *    sente niente, ed e' inevitabile — ma deve essere DETTO dai contatori,
   *    non scoperto dall'utente.  `sospesi` sale, `usciti` resta a zero. */
  { nome: "contesto sospeso e nessun gesto: muto, e i conti lo dicono",
    scena: { blocchi: 400, perde: () => false, sospeso: true },
    ancora: { coda: [0, 0], buchi: 0, mancati: 0 },
    riordino: { sospesi: [395, 400], risvegli: [0, 0] },
    muto_atteso: true, discrimina: null }
];

function dentro(v, [lo, hi]) {
  return (lo === null || v >= lo) && (hi === null || v <= hi);
}

(async function () {
  const src = ritaglia();
  const rotto = innesta_successione(src);
  const silenzioso = innesta_silenzio(src);
  console.log("⛔ 07-b61 — L'ANCORA, sul codice ritagliato da src/pagina.html");
  console.log("   regione audio: %d byte  ·  guasto innestato nella COPIA: "
            + "%d byte\n", src.length, rotto.length);
  let ok = 0, tot = 0;
  for (const s of SCENE) {
    const a = await gira(src, s.scena);
    const v = await gira(rotto, s.scena);
    console.log("── %s", s.nome);
    console.log("   ⭐ con l'ancora     coda %d→%d ms (fine %d) · BUCHI %d · "
              + "mancati %d · ricevuti %d · suonati %d · USCITI %d · "
              + "tagliati %d · tirate %d · vecchi %d",
      a.coda_min, a.coda_max, a.coda_fine, a.buchi, a.mancati, a.ricevuti,
      a.suonati, a.usciti, a.tagliati, a.tirate, a.vecchi);
    console.log("   ⛔ guasto innestato coda %d→%d ms (fine %d) · BUCHI %d · "
              + "mancati %d",
      v.coda_min, v.coda_max, v.coda_fine, v.buchi, v.mancati);

    // ⛔⭐ IL CONTROLLO CHE MANCAVA: non «quanti blocchi sono passati per
    //     `start()`», ma quanti hanno SUONATO fino in fondo.  ⚠ Senza di lui
    //     questo banco ha dato 13 su 13 a un codice che faceva silenzio.
    tot += 2;
    /* ⚠ Una scena che DEVE essere muta si giudica al contrario: qui «zero
       usciti» e' l'atteso, e trovarne sarebbe il difetto. */
    const suona_davvero = s.muto_atteso
      ? (a.usciti === 0 && a.suonati === 0)
      : a.usciti >= 0.9 * a.suonati - 5;
    /* ⛔ E QUESTO ATTESO ERA SCRITTO SBAGLIATO — terzo di giornata, 21 agosto.
     *    Diceva «tagliati <= 2 sempre».  ⚠ Sulla scena della raffica ne taglia
     *    **20**, ed e' GIUSTO: sono i blocchi dell'anello del figlio, cioe'
     *    l'audio che il desktop ha prodotto PRIMA che ci collegassimo.
     *    Buttarli e' la cura; suonarli vorrebbe dire partire 400 ms indietro e
     *    restarci per tutta la sessione.  ⇒ L'atteso e' «quanti ne ha buttati
     *    la raffica, e non uno di piu'». */
    /* ⚠ E il mucchio di uno stallo si butta come quello dell'attacco: sono la
       stessa cosa, e buttarli e' la cura, non il difetto. */
    const tagliati_max = (s.scena.raffica || 0) + (s.scena.stallo_n || 0) + 2;
    const non_taglia = a.tagliati <= tagliati_max;
    ok += suona_davvero + non_taglia;
    console.log("      %s HA SUONATO: usciti %d su %d messi in scaletta",
      suona_davvero ? "⭐" : "⛔", a.usciti, a.suonati);
    console.log("      %s tagliati %d (atteso al piu' %d: la raffica "
              + "dell'attacco, buttata apposta)", non_taglia ? "⭐" : "⛔",
      a.tagliati, tagliati_max);

    if (s.riordino) {
      for (const campo of Object.keys(s.riordino)) {
        tot += 1;
        const bene = dentro(a[campo], s.riordino[campo]);
        ok += bene;
        console.log("      %s riordino «%s»: %s, atteso in [%s, %s]",
          bene ? "⭐" : "⛔", campo, a[campo], s.riordino[campo][0],
          s.riordino[campo][1]);
      }
    }

    tot += 3;
    const c1 = dentro(a.coda_fine, s.ancora.coda);
    const c2 = Array.isArray(s.ancora.buchi)
      ? dentro(a.buchi, s.ancora.buchi) : a.buchi === s.ancora.buchi;
    const c3 = a.mancati === s.ancora.mancati;
    ok += c1 + c2 + c3;
    console.log("      %s la coda finisce in [%s, %s]", c1 ? "⭐" : "⛔",
      s.ancora.coda[0], s.ancora.coda[1]);
    console.log("      %s BUCHI %d, attesi %s", c2 ? "⭐" : "⛔", a.buchi,
      Array.isArray(s.ancora.buchi)
        ? "in [" + s.ancora.buchi[0] + ", " + s.ancora.buchi[1] + "]"
        : s.ancora.buchi);
    console.log("      %s mancati attesi %d", c3 ? "⭐" : "⛔", s.ancora.mancati);

    // ⛔ E IL CONTROLLO POSITIVO: la copia guasta DEVE comportarsi diversamente
    //    dove la cura promette una differenza.  Se le due colonne coincidono,
    //    il banco non sta provando niente.
    if (s.discrimina) {
      const d = s.discrimina;
      /* ⛔ Il guasto giusto per la scena giusta: lo stallo si prova contro la
         CURA TOLTA, non contro la scaletta per successione — provarlo con
         quella direbbe di si' per la ragione sbagliata. */
      const rotto_giusto = (s.scena.stallo_a !== undefined)
        ? await gira(innesta_tirata_chiusa(src), s.scena) : v;
      tot += 2;
      const sana = dentro(a[d.campo], d.ancora);
      const rotta = dentro(rotto_giusto[d.campo], d.vecchio);
      ok += sana + rotta;
      console.log("      %s discriminante «%s»: con l'ancora %s, atteso in "
                + "[%s, %s]", sana ? "⭐" : "⛔", d.campo, a[d.campo],
        d.ancora[0], d.ancora[1]);
      console.log("      %s discriminante «%s»: col guasto %s, atteso in "
                + "[%s, %s] ⇒ il banco VEDE il guasto", rotta ? "⭐" : "⛔",
        d.campo, rotto_giusto[d.campo], d.vecchio[0], d.vecchio[1]);
    } else {
      console.log("      ⚠ nessun discriminante: qui le due strade devono "
                + "coincidere, e coincidono");
    }
    // ⛔ E il guasto del SILENZIO: il banco deve vederlo su questa scena.
    // ⚠ Tranne dove la scena e' gia' muta per costruzione — li' non c'e'
    //   niente da far tacere, e pretenderlo sarebbe un controllo che non puo'
    //   passare: un rosso del banco travestito da rosso del prodotto.
    if (s.muto_atteso) {
      console.log("      ⚠ guasto «silenzio»: non si prova qui, la scena e' "
                + "gia' muta apposta");
      console.log("");
      continue;
    }
    const muto = await gira(silenzioso, s.scena);
    tot += 1;
    const visto = muto.usciti < 0.5 * muto.suonati;
    ok += visto;
    console.log("      %s guasto «silenzio» innestato: usciti %d su %d "
              + "suonati, tagliati %d ⇒ il banco %s", visto ? "⭐" : "⛔",
      muto.usciti, muto.suonati, muto.tagliati,
      visto ? "LO VEDE" : "NON LO VEDE");
    console.log("");
  }
  console.log("%s %d controlli su %d", ok === tot ? "⭐" : "⛔", ok, tot);
  process.exit(ok === tot ? 0 : 1);
})().catch((e) => { console.error("⛔ " + (e && e.stack || e)); process.exit(2); });
