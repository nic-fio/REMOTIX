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
  return src.slice(0, i) + vecchio + src.slice(j);
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
  class Contesto {
    constructor(o) {
      this.sampleRate = o.sampleRate; this.state = "running";
      this.destination = {}; this._chiuso = false;
    }
    get currentTime() { return ora; }
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
    resume() { return Promise.resolve(); }
    close() { this._chiuso = true; }
  }
  const g = {
    AudioContext: Contesto, webkitAudioContext: Contesto,
    performance: { now: () => ora * 1000 },
    setInterval: () => 0, clearInterval: () => {},
    document: { body: { dataset: {} }, hasFocus: () => true },
    fetch: () => Promise.resolve(),
    nota: (r) => registro.push(String(r)),
    TASTI_VISTI: 0, TASTI_ULTIMO: "", schermo: null,
    AudioDecoder: undefined, EncodedAudioChunk: undefined
  };
  return { g, partite, ora: () => ora,
           avanza: (s) => { ora += s; scadono(); } };
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
  let ist = scena.ist0 || 1000000;            // µs
  for (let i = 0; i < N; i++) {
    const perso = scena.perde(i);
    if (!perso) {
      f.spingi(datagram(ist, 960));
      await new Promise((r) => setImmediate(r));   // lascia girare il lettore
    }
    ist += 20000;
    // ⭐ IL TEMPO PASSA: e' la cosa che il codice vecchio non guardava.  ⛔ In
    //    una raffica NON passa — i blocchi arrivano tutti insieme.
    amb.avanza(scena.raffica && i < scena.raffica ? 0 : PASSO);
    if (i % 5 === 4) code.push(Math.round(A.coda_ms()));
  }
  const c = M.audio_conti();
  const esito = {
    coda: code, coda_fine: c.in_coda_ms,
    coda_min: Math.min(...code), coda_max: Math.max(...code),
    buchi: A.riarmi || 0, mancati: c.mancati, ricevuti: c.ricevuti,
    suonati: c.suonati, pieni: c.scartati_pieno, aoff: c.aoff_ms,
    usciti: c.usciti, tagliati: c.tagliati, tirate: c.tirate,
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
    discrimina: { campo: "coda_fine", ancora: [245, 275], vecchio: [500, null] } }
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
              + "tagliati %d · tirate %d",
      a.coda_min, a.coda_max, a.coda_fine, a.buchi, a.mancati, a.ricevuti,
      a.suonati, a.usciti, a.tagliati, a.tirate);
    console.log("   ⛔ guasto innestato coda %d→%d ms (fine %d) · BUCHI %d · "
              + "mancati %d",
      v.coda_min, v.coda_max, v.coda_fine, v.buchi, v.mancati);

    // ⛔⭐ IL CONTROLLO CHE MANCAVA: non «quanti blocchi sono passati per
    //     `start()`», ma quanti hanno SUONATO fino in fondo.  ⚠ Senza di lui
    //     questo banco ha dato 13 su 13 a un codice che faceva silenzio.
    tot += 2;
    const suona_davvero = a.usciti >= 0.9 * a.suonati - 5;
    /* ⛔ E QUESTO ATTESO ERA SCRITTO SBAGLIATO — terzo di giornata, 21 agosto.
     *    Diceva «tagliati <= 2 sempre».  ⚠ Sulla scena della raffica ne taglia
     *    **20**, ed e' GIUSTO: sono i blocchi dell'anello del figlio, cioe'
     *    l'audio che il desktop ha prodotto PRIMA che ci collegassimo.
     *    Buttarli e' la cura; suonarli vorrebbe dire partire 400 ms indietro e
     *    restarci per tutta la sessione.  ⇒ L'atteso e' «quanti ne ha buttati
     *    la raffica, e non uno di piu'». */
    const tagliati_max = (s.scena.raffica || 0) + 2;
    const non_taglia = a.tagliati <= tagliati_max;
    ok += suona_davvero + non_taglia;
    console.log("      %s HA SUONATO: usciti %d su %d messi in scaletta",
      suona_davvero ? "⭐" : "⛔", a.usciti, a.suonati);
    console.log("      %s tagliati %d (atteso al piu' %d: la raffica "
              + "dell'attacco, buttata apposta)", non_taglia ? "⭐" : "⛔",
      a.tagliati, tagliati_max);

    tot += 3;
    const c1 = dentro(a.coda_fine, s.ancora.coda);
    const c2 = a.buchi === s.ancora.buchi;
    const c3 = a.mancati === s.ancora.mancati;
    ok += c1 + c2 + c3;
    console.log("      %s la coda finisce in [%s, %s]", c1 ? "⭐" : "⛔",
      s.ancora.coda[0], s.ancora.coda[1]);
    console.log("      %s BUCHI attesi %d", c2 ? "⭐" : "⛔", s.ancora.buchi);
    console.log("      %s mancati attesi %d", c3 ? "⭐" : "⛔", s.ancora.mancati);

    // ⛔ E IL CONTROLLO POSITIVO: la copia guasta DEVE comportarsi diversamente
    //    dove la cura promette una differenza.  Se le due colonne coincidono,
    //    il banco non sta provando niente.
    if (s.discrimina) {
      const d = s.discrimina;
      tot += 2;
      const sana = dentro(a[d.campo], d.ancora);
      const rotta = dentro(v[d.campo], d.vecchio);
      ok += sana + rotta;
      console.log("      %s discriminante «%s»: con l'ancora %s, atteso in "
                + "[%s, %s]", sana ? "⭐" : "⛔", d.campo, a[d.campo],
        d.ancora[0], d.ancora[1]);
      console.log("      %s discriminante «%s»: col guasto %s, atteso in "
                + "[%s, %s] ⇒ il banco VEDE il guasto", rotta ? "⭐" : "⛔",
        d.campo, v[d.campo], d.vecchio[0], d.vecchio[1]);
    } else {
      console.log("      ⚠ nessun discriminante: qui le due strade devono "
                + "coincidere, e coincidono");
    }
    // ⛔ E il guasto del SILENZIO: il banco deve vederlo su questa scena.
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
