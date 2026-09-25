// La meta' wasm della prova: decodifica `pacchetti.bin` con `opus.wasm`
// ESTRATTO DALLA PAGINA (non dal file accanto: si prova quel che si spedisce)
// e confronta campione per campione con `attesi.f32` del libopus nativo.
//
//   node confronta.mjs ../../pagina.html pacchetti.bin attesi.f32
import { readFileSync } from "node:fs";

const [pagina, fp, fa] = process.argv.slice(2);
const html = readFileSync(pagina, "utf8");
const m = /\/\*OPUS_WASM_INIZIO\*\/"([A-Za-z0-9+/=]+)"\/\*OPUS_WASM_FINE\*\//.exec(html);
if (!m) { console.log("⛔ la pagina non porta il wasm"); process.exit(1); }
const byte = Buffer.from(m[1], "base64");
const { instance } = await WebAssembly.instantiate(byte, {});
const x = instance.exports;
if (x._initialize) x._initialize();
if (x.rx_apri() !== 0) { console.log("⛔ rx_apri"); process.exit(1); }

const pk = readFileSync(fp);
const att = new Float32Array(readFileSync(fa).buffer.slice(0));
let o = 0, k = 0, pacchetti = 0, diversi = 0, maxd = 0;
const t0 = performance.now();
while (o < pk.length) {
  const n = pk[o] | (pk[o + 1] << 8); o += 2;
  new Uint8Array(x.memory.buffer, x.rx_pacchetto(), n).set(pk.subarray(o, o + n)); o += n;
  const f = x.rx_decodifica(n);
  if (f !== 960) { console.log("⛔ pacchetto " + pacchetti + ": " + f); process.exit(1); }
  const out = new Float32Array(x.memory.buffer, x.rx_uscita(), f * 2);
  for (let i = 0; i < f * 2; i++, k++) {
    const d = Math.abs(out[i] - att[k]);
    if (d !== 0) diversi++;
    if (d > maxd) maxd = d;
  }
  pacchetti++;
}
const ms = performance.now() - t0;
console.log(JSON.stringify({ pacchetti, campioni: k, attesi: att.length, diversi, max_diff: maxd,
  ms_per_pacchetto: +(ms / pacchetti).toFixed(4), wasm_byte: byte.length, base64: m[1].length }));
process.exit(k === att.length && maxd < 1e-4 ? 0 : 1);
