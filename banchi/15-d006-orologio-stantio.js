#!/usr/bin/env node
/* 15-d006 — L'OROLOGIO STANTIO DI FIREFOX, provato SUL CODICE VERO di `suona()`.
 *
 *     node banchi/15-d006-orologio-stantio.js [--pagina src/pagina.html] [--vecchia <rev>]
 *
 * ⛔ PERCHE' ESISTE — D-006, 25 settembre 2026.  Su Firefox, con un video nella
 *    sessione, F-013 sente buchi di 0,1-0,4 s a grappoli; Chrome no.  `[M]` dagli
 *    orecchi del giro (f013-orecchio-sano.json, 4 desktop): ogni buco e' un
 *    RIARMO (gnome 6 buchi/6 riarmi, lxqt 16/15, xfce 3/3+1 pieno, kde 0/0), e
 *    i riarmi arrivano SENZA uno stallo del thread principale piu' lungo del
 *    cuscino (il timer del banco a 100 ms non ha mai tardato oltre 173 ms su
 *    GNOME e 142 su XFCE).  ⭐ Quel che gli stessi campioni mostrano e' un'altra
 *    cosa: su Firefox `AudioContext.currentTime` letto dal thread principale e'
 *    STANTIO — fino a 77-204 ms dietro `performance.now()` (Chrome: mai oltre
 *    rumore).  E la tirata della finestra dopo un riarmo sceglie proprio la
 *    lettura piu' stantia: ancorare con un'ora vecchia di S ms lascia un cuscino
 *    VERO di 250 − S, e il prossimo ritardo normale del thread lo buca ⇒ riarmo
 *    ⇒ nuova finestra ⇒ nuova tirata sull'ora piu' vecchia.  Un ciclo che si
 *    mantiene da solo: i buchi a grappoli.
 *
 * ⭐ LA SCENA: blocchi da 20 ms, il thread principale che si ferma ogni 0,3-0,9 s
 *    per 60-200 ms e una volta su otto per 250-330 (appena oltre il cuscino),
 *    i blocchi fermi consegnati in un mucchio alla fine dello stallo; e, per
 *    Firefox, `currentTime` che ogni tanto resta fermo per 30-200 ms.  Si
 *    misura l'UDIBILE vero: l'unione degli intervalli in cui una sorgente
 *    suonava davvero (partita, e non fermata prima della fine).
 *
 * ⭐ IL CONTROLLO: la versione di prima (`--vecchia`, d9743dc) deve fare buchi
 *    nella stessa scena — se non ne fa, la scena non riproduce D-006 e il banco
 *    e' ROSSO; la nuova non deve riarmare, ne' fare buchi oltre 100 ms.
 *
 * ⚠ QUEL CHE NON DICE: e' un modello del thread principale di Firefox, non
 *   Firefox.  Il giudizio vero e' F-013 sul giro (udibile >= 95 %, buco <= 1 s). */
"use strict";
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const arg = (n, d) => { const i = process.argv.indexOf(n); return i > 0 ? process.argv[i + 1] : d; };
const RADICE = path.join(__dirname, "..");
const PAGINA = arg("--pagina", path.join(RADICE, "src", "pagina.html"));
const VECCHIA = arg("--vecchia", "d9743dc");
const MARCA_DA = "const AUDIO_FREQUENZA = 48000";
const MARCA_A = "⭐⭐ GLI APPUNTI";

function ritaglia(t) {
  const i = t.indexOf(MARCA_DA), j = t.indexOf(MARCA_A);
  if (i < 0 || j < 0 || j <= i) throw new Error("⛔ marche della regione audio sparite");
  return t.slice(i, t.lastIndexOf("/*", j));
}

/* Un generatore deterministico: la stessa scena per tutte e due le versioni. */
function lcg(seme) { let s = seme >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

async function gira(src, stantio, seme) {
  let vero = 0;            // l'ora VERA dell'orologio audio (s)
  let foto = 0;            // quel che `currentTime` restituisce al thread principale
  const sorgenti = [];
  const registro = [];
  class Contesto {
    constructor() { this.state = "running"; this.destination = {}; this.sampleRate = 48000; }
    get currentTime() { return foto; }
    createBuffer(ch, n) { const d = []; for (let c = 0; c < ch; c++) d.push(new Float32Array(n)); return { length: n, getChannelData: (c) => d[c] }; }
    createBufferSource() {
      const s = { buffer: null, onended: null, _da: null, _a: null, _stop: null, connect() {},
        start(t) { s._da = Math.max(t, vero); s._a = s._da + s.buffer.length / 48000; sorgenti.push(s); },
        stop() { if (s._stop !== null || s._finita) return; s._stop = vero; s._finita = true; if (s.onended) s.onended(); } };
      return s;
    }
    resume() { return Promise.resolve(); }
    close() {}
  }
  const g = { AudioContext: Contesto, webkitAudioContext: Contesto,
    addEventListener() {}, removeEventListener() {},
    performance: { now: () => vero * 1000 }, setInterval: () => 0, clearInterval() {},
    document: { body: { dataset: {} }, hasFocus: () => true }, fetch: () => Promise.resolve(),
    nota: (r) => registro.push(String(r)) };
  const M = new Function("window", "performance", "setInterval", "clearInterval", "document",
    "fetch", "nota", "TASTI_VISTI", "TASTI_ULTIMO", "schermo", "AudioDecoder", "EncodedAudioChunk",
    src + "\n;return { avvia_audio, audio_conti, audio_ferma, dammi: () => AUDIO };")(
    g, g.performance, g.setInterval, g.clearInterval, g.document, g.fetch, g.nota, 0, "", null,
    undefined, undefined);
  const coda = [], attesa = [];
  const wt = { datagrams: { readable: { getReader: () => ({ read() {
    if (coda.length) return Promise.resolve({ value: coda.shift(), done: false });
    return new Promise((r) => attesa.push(r)); } }) } } };
  const spingi = (b) => { if (attesa.length) attesa.shift()({ value: b, done: false }); else coda.push(b); };
  function datagram(ist_us) {
    const b = new ArrayBuffer(12 + 960 * 4), v = new DataView(b);
    v.setUint16(0, 0x0401); v.setUint16(2, 2); v.setBigUint64(4, BigInt(ist_us));
    return new Uint8Array(b);
  }
  M.avvia_audio(wt);
  const scadono = () => {
    for (const s of sorgenti) if (!s._finita && s._stop === null && vero >= s._a) { s._finita = true; if (s.onended) s.onended(); }
  };

  const caso = lcg(seme);
  const DURATA = 60, PASSO = 0.001, RETE = 0.005;
  // gli stalli: [inizio, fine) in secondi
  const stalli = [];
  /* 60-200 ms di solito; uno su otto 250-330 ms, appena oltre il cuscino
     (`[M]` F-013 lxqt/Firefox: il timer a 100 ms ha tardato fino a 257 ms). */
  for (let t = 0.5; t < DURATA;) {
    const n = caso() < 0.125 ? 0.25 + 0.08 * caso() : 0.06 + 0.14 * caso();
    stalli.push([t, t + n]); t += n + 0.3 + 0.6 * caso();
  }
  /* ⛔ i geli dell'orologio: per 30-200 ms `currentTime` non si aggiorna (`[M]`
     F-013 su Firefox: 30-204 ms dietro `performance.now()`, a timer puntuali).
     Con l'orologio fresco (Chrome) non ce ne sono. */
  const geli = [];
  if (stantio)
    for (let t = 0.05; t < DURATA;) { const n = 0.03 + 0.17 * caso(); geli.push([t, t + n]); t += n + 0.2 + 1.3 * caso(); }
  let si = 0, gi = 0, prossimo_blocco = 0, trattenuti = [];
  for (let passo = 0; passo * PASSO < DURATA; passo++) {
    vero = passo * PASSO;
    while (si < stalli.length && stalli[si][1] <= vero) si++;
    while (gi < geli.length && geli[gi][1] <= vero) gi++;
    const fermo = si < stalli.length && stalli[si][0] <= vero && vero < stalli[si][1];
    const gelato = gi < geli.length && geli[gi][0] <= vero && vero < geli[gi][1];
    // i blocchi prodotti dal server arrivano dopo la rete
    while (prossimo_blocco * 0.020 + RETE <= vero) { trattenuti.push(1000000 + prossimo_blocco * 20000); prossimo_blocco++; }
    if (fermo) continue;                       // il thread principale non gira
    if (!gelato) foto = vero;
    if (trattenuti.length) {
      for (const ist of trattenuti) { spingi(datagram(ist)); await new Promise((r) => setImmediate(r)); }
      trattenuti = [];
    }
    scadono();
  }
  const c = M.audio_conti();
  // l'udibile: unione degli intervalli suonati davvero, fra 1 s e la fine
  const iv = sorgenti.map((s) => [s._da, s._stop !== null ? Math.min(s._a, s._stop) : Math.min(s._a, DURATA)])
    .filter(([a, b]) => b > a).sort((x, y) => x[0] - y[0]);
  const T0 = 1, T1 = DURATA - 0.5;
  let coperto = 0, fin = T0; const buchi = [];
  for (const [a, b] of iv) {
    const aa = Math.max(a, T0), bb = Math.min(b, T1);
    if (bb <= aa) { continue; }
    if (aa > fin + 0.002) buchi.push(Math.round((aa - fin) * 1000));
    coperto += Math.max(0, bb - Math.max(aa, fin)); fin = Math.max(fin, bb);
  }
  if (T1 > fin + 0.002) buchi.push(Math.round((T1 - fin) * 1000));
  M.audio_ferma();
  return { udibile: 100 * coperto / (T1 - T0), buchi, riarmi: c.riarmi, tirate: c.tirate,
           tagliati: c.tagliati, usciti: c.usciti, stalli: stalli.length };
}

(async () => {
  const nuova = ritaglia(fs.readFileSync(PAGINA, "utf8"));
  let vecchia;
  try { vecchia = ritaglia(execFileSync("git", ["-C", RADICE, "show", VECCHIA + ":src/pagina.html"], { encoding: "utf8" })); }
  catch (e) { console.log("⛔ non trovo la versione vecchia " + VECCHIA); process.exit(2); }
  let ok = true;
  const riga = (nome, r) => console.log("   " + nome.padEnd(28) + " udibile " + r.udibile.toFixed(1)
    + " % · buchi " + r.buchi.length + (r.buchi.length ? " (ms: " + r.buchi.slice(0, 12).join(" ") + ")" : "")
    + " · riarmi " + r.riarmi + " · tirate " + r.tirate + " · tagliati " + r.tagliati);
  for (const seme of [1, 2, 3]) {
    console.log("── seme " + seme + ": stalli 60-200 ms (1 su 8: 250-330) ogni 0,3-0,9 s, 60 s");
    for (const stantio of [false, true]) {
      const qui = stantio ? "orologio stantio (Firefox)" : "orologio fresco (Chrome)";
      const v = await gira(vecchia, stantio, seme); riga("vecchia, " + qui, v);
      const n = await gira(nuova, stantio, seme); riga("nuova,   " + qui, n);
      const bmax = n.buchi.length ? Math.max(...n.buchi) : 0;
      // il controllo: la scena deve far fare buchi alla vecchia, o non prova niente
      if (v.riarmi === 0 || v.udibile >= 99.5) { ok = false; console.log("   ⛔ la vecchia non fa buchi: la scena non riproduce D-006"); }
      if (n.riarmi > 0 || n.udibile < 99 || bmax > 100 || n.udibile < v.udibile) {
        ok = false; console.log("   ⛔ la nuova: riarmi " + n.riarmi + ", buco piu' lungo " + bmax + " ms");
      } else console.log("   ⭐ la nuova: nessun riarmo, buco piu' lungo " + bmax + " ms");
    }
  }
  console.log(ok ? "⭐ VERDE" : "⛔ ROSSO");
  process.exit(ok ? 0 : 1);
})();
