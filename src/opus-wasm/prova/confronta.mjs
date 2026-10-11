// The wasm half of the test: decodes `pacchetti.bin` with `opus.wasm`
// EXTRACTED FROM THE PAGE (not from the file next to it: we test what is shipped)
// and compares sample by sample with native libopus's `expected_vals.f32`.
//
//   node confronta.mjs ../../pagina.html pacchetti.bin expected_vals.f32
import { readFileSync } from "node:fs";

const [page, fp, fa] = process.argv.slice(2);
const html = readFileSync(page, "utf8");
const m = /\/\*OPUS_WASM_INIZIO\*\/"([A-Za-z0-9+/=]+)"\/\*OPUS_WASM_FINE\*\//.exec(html);
if (!m) { console.log("⛔ the page does not carry the wasm"); process.exit(1); }
const byte = Buffer.from(m[1], "base64");
const { instance } = await WebAssembly.instantiate(byte, {});
const x = instance.exports;
if (x._initialize) x._initialize();
if (x.rx_open() !== 0) { console.log("⛔ rx_open"); process.exit(1); }

const pk = readFileSync(fp);
const expect = new Float32Array(readFileSync(fa).buffer.slice(0));
let o = 0, k = 0, packets = 0, diversi = 0, maxd = 0;
const t0 = performance.now();
while (o < pk.length) {
  const n = pk[o] | (pk[o + 1] << 8); o += 2;
  new Uint8Array(x.memory.buffer, x.rx_packet(), n).set(pk.subarray(o, o + n)); o += n;
  const f = x.rx_decode(n);
  if (f !== 960) { console.log("⛔ packet " + packets + ": " + f); process.exit(1); }
  const out = new Float32Array(x.memory.buffer, x.rx_output(), f * 2);
  for (let i = 0; i < f * 2; i++, k++) {
    const d = Math.abs(out[i] - expect[k]);
    if (d !== 0) diversi++;
    if (d > maxd) maxd = d;
  }
  packets++;
}
const ms = performance.now() - t0;
console.log(JSON.stringify({ packets, campioni: k, attesi: expect.length, diversi, max_diff: maxd,
  ms_per_pacchetto: +(ms / packets).toFixed(4), wasm_byte: byte.length, base64: m[1].length }));
process.exit(k === expect.length && maxd < 1e-4 ? 0 : 1);
