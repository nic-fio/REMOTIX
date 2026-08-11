
/* ⛔ L'impronta che il SERVER ha scritto qui dentro mentre serviva la pagina. */
const IMPRONTA_SERVITA = "__IMPRONTA__";
const AVVISO = "__AVVISO__";

const $ = (i) => document.getElementById(i);
const righe = [];
function nota(t) { righe.push(t); $("registro").textContent = righe.join("\n"); }
function esito(t, bene) { const e = $("esito"); e.textContent = t; e.className = bene ? "bene" : "male"; }

if (AVVISO.trim()) { $("avviso").hidden = false; }

/* ── I byte di RCP (RCP.md §6.0 e §6.1) ────────────────────────────────────
   ⛔ Ordine dei byte: rete (big-endian).  Nessun campo allineato, nessun
      riempimento: «un byte in piu' che fa tornare i conti in una struttura C e'
      la forma esatta del difetto corretto in §6.2».                          */

const TIPO = {
  CIAO: 0x0001, ECCOMI: 0x0002, CREDENZIALI: 0x0003, AMMESSO: 0x0004,
  RESPINTO: 0x0005, ATTACCA: 0x0006, SESSIONE: 0x0007, CONGEDO: 0x000C,
};

/* I motivi di §8.2, in parole.  ⛔ `RCP.md` §8.2 e `SPECIFICHE.md`: all'utente
   si dice PERCHE', con una frase e non con un numero. */
const MOTIVO = {
  0x01: "la sessione e' stata chiusa dall'utente",
  0x02: "silenzio troppo lungo: la sessione e' scaduta",
  0x03: "la sessione e' stata abbandonata",
  0x04: "ha prevalso la sessione locale su quella macchina",
  0x05: "quell'utente e' gia' collegato localmente",
  0x06: "il server e' pieno",
  0x07: "utente o parola d'ordine non corretti",
  0x08: "i tentativi da questo indirizzo sono esauriti: riprova fra dodici ore, o sblocca l'indirizzo dal server",
  0x09: "il server e questa pagina non hanno niente in comune da parlare",
  0x0A: "versione del protocollo incompatibile",
  0x0B: "errore di protocollo",
  0x0C: "il server si sta spegnendo",
  0x0D: "tempo scaduto durante la stretta di mano",
  0x0E: "quella sessione non si puo' servire",
  0x0F: "quell'utente e' gia' collegato da un altro dispositivo",
};

class Scrittore {
  constructor() { this.b = []; }
  u8(v)  { this.b.push(v & 0xff); return this; }
  u16(v) { this.b.push((v >> 8) & 0xff, v & 0xff); return this; }
  u32(v) { this.b.push((v >>> 24) & 0xff, (v >>> 16) & 0xff, (v >>> 8) & 0xff, v & 0xff); return this; }
  /* stringa = u16 lunghezza + i byte UTF-8, SENZA terminatore (§6.0) */
  str(t)  { const d = new TextEncoder().encode(t); this.u16(d.length); for (const x of d) this.b.push(x); return this; }
  byte()  { return new Uint8Array(this.b); }
}

/* L'inquadratura di §6.1: u16 tipo, u32 lunghezza, corpo. */
function inquadra(tipo, corpo) {
  const m = new Uint8Array(6 + corpo.length);
  const v = new DataView(m.buffer);
  v.setUint16(0, tipo);
  v.setUint32(2, corpo.length);
  m.set(corpo, 6);
  return m;
}

class Lettore {
  constructor(d) { this.v = new DataView(d.buffer, d.byteOffset, d.byteLength); this.o = 0; }
  u8()  { return this.v.getUint8(this.o++); }
  u16() { const x = this.v.getUint16(this.o); this.o += 2; return x; }
  u32() { const x = this.v.getUint32(this.o); this.o += 4; return x; }
  str() { const n = this.u16(); const d = new Uint8Array(this.v.buffer, this.v.byteOffset + this.o, n); this.o += n; return new TextDecoder().decode(d); }
  resta() { return this.v.byteLength - this.o; }
}

/* Il lettore del canale di controllo: accumula e restituisce un messaggio alla
   volta.  ⛔ La lunghezza si controlla PRIMA di allocare (§6.1). */
class Canale {
  constructor(stream) {
    this.lettore = stream.readable.getReader();
    this.scrittore = stream.writable.getWriter();
    this.buf = new Uint8Array(0);
  }
  async manda(tipo, corpo) { await this.scrittore.write(inquadra(tipo, corpo)); }
  async ricevi() {
    for (;;) {
      if (this.buf.length >= 6) {
        const v = new DataView(this.buf.buffer, this.buf.byteOffset, this.buf.byteLength);
        const tipo = v.getUint16(0), lung = v.getUint32(2);
        if (lung > 1024 * 1024) throw new Error("messaggio oltre 1 MiB: il server viola §6.1");
        if (this.buf.length >= 6 + lung) {
          const corpo = this.buf.slice(6, 6 + lung);
          this.buf = this.buf.slice(6 + lung);
          return { tipo, corpo };
        }
      }
      const { value, done } = await this.lettore.read();
      if (done) return null;
      const n = new Uint8Array(this.buf.length + value.length);
      n.set(this.buf); n.set(value, this.buf.length);
      this.buf = n;
    }
  }
}

function base64ABytes(b64) {
  const s = atob(b64);
  const d = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) d[i] = s.charCodeAt(i);
  return d;
}

/* ⛔ L'impronta si RITIRA prima di ogni tentativo (§4.1-bis).  Se il ritiro
   fallisce si usa quella servita con la pagina, e LO SI DICE: un ripiego
   silenzioso produce due comportamenti sotto la stessa etichetta. */
async function impronta() {
  try {
    const r = await fetch("/impronta", { cache: "no-store" });
    if (!r.ok) throw new Error("stato " + r.status);
    const j = await r.json();
    if (j.impronta && j.impronta !== IMPRONTA_SERVITA) {
      nota("impronta: il certificato e' stato ruotato da quando questa pagina e' stata servita — si usa quella nuova");
    }
    return j.impronta || IMPRONTA_SERVITA;
  } catch (e) {
    nota("impronta: /impronta non risponde (" + e.message + "): si usa quella servita con la pagina");
    return IMPRONTA_SERVITA;
  }
}

async function collega(utente, parola) {
  if (!("WebTransport" in window)) {
    esito("Questo browser non ha WebTransport: serve Chrome/Edge, Firefox o Safari 26+.", false);
    return;
  }

  const b64 = await impronta();
  const url = "https://" + location.host + "/rcp/1";
  nota("apro " + url);

  /* ⛔ `allowPooling: false` e l'impronta: `RCP.md` §4.1-bis.  Con
     `serverCertificateHashes` il browser NON guarda l'eccezione — guarda
     l'impronta — ed e' l'unico meccanismo che i browser espongono per un
     server senza dominio. */
  const wt = new WebTransport(url, {
    allowPooling: false,
    serverCertificateHashes: [{ algorithm: "sha-256", value: base64ABytes(b64) }],
  });

  wt.closed.then((info) => {
    const c = info && info.closeCode;
    if (c && MOTIVO[c]) esito(MOTIVO[c], false);
    nota("sessione chiusa dal server: codice " + (c === undefined ? "?" : c));
  }).catch((e) => nota("sessione chiusa con errore: " + e));

  await wt.ready;
  nota("sessione WebTransport aperta");

  /* ⛔ §4.2: il client apre il PRIMO stream bidirezionale della sessione.
     Quello e' il canale di controllo, e il suo chiudersi E' la fine della
     sessione. */
  const canale = new Canale(await wt.createBidirectionalStream());

  /* ── CIAO (§4.3) ────────────────────────────────────────────────────── */
  const cap = [
    ["video.codec", "hevc,av1"],
    ["video.profondita", "8,10"],
    ["video.livello", "5.1"],
    ["video.misura_massima", screen.width * devicePixelRatio + "x" + screen.height * devicePixelRatio],
    ["audio.codec", "opus,pcm"],
    ["input.tocco", "no"],
    ["appunti.testo", "si"],
    ["client.nome", "remotix-pagina 0.1.0"],
  ];
  const s = new Scrittore();
  s.u16(1);              /* la versione maggiore che questa pagina sa parlare */
  s.u16(cap.length);
  for (const [n, v] of cap) s.str(n).str(v);
  await canale.manda(TIPO.CIAO, s.byte());
  nota("CIAO mandato (" + cap.length + " capacita')");

  let m = await canale.ricevi();
  if (!m) { esito("Il server ha chiuso il canale senza rispondere.", false); return; }
  if (m.tipo === TIPO.CONGEDO) { const l = new Lettore(m.corpo); esito(MOTIVO[l.u8()] || "congedato", false); return; }
  if (m.tipo !== TIPO.ECCOMI) { esito("Il server ha risposto 0x" + m.tipo.toString(16) + " invece di ECCOMI.", false); return; }
  {
    const l = new Lettore(m.corpo);
    const ver = l.u16(), quante = l.u16();
    const scelte = [];
    for (let i = 0; i < quante; i++) scelte.push(l.str() + "=" + l.str());
    nota("ECCOMI: versione " + ver + " — " + scelte.join(" · "));
  }

  /* ── CREDENZIALI (§4.4) ─────────────────────────────────────────────── */
  await canale.manda(TIPO.CREDENZIALI, new Scrittore().str(utente).str(parola).byte());
  nota("CREDENZIALI mandate (la parola non compare in nessun registro)");

  m = await canale.ricevi();
  if (!m) { esito("Il server ha chiuso il canale senza rispondere alle credenziali.", false); return; }
  if (m.tipo === TIPO.RESPINTO) {
    const l = new Lettore(m.corpo);
    const mot = l.u8();
    esito(MOTIVO[mot] || ("respinto, motivo 0x" + mot.toString(16)), false);
    /* ⛔ §4.4: «il client NON DEVE riprovare sulla stessa connessione: per un
       secondo tentativo se ne apre una nuova».  E l'unica cosa che gli resta
       da dire e' CONGEDO — che §8.1 gli IMPONE quando e' lui a chiudere; qui
       chiude il server, quindi si tace. */
    return;
  }
  if (m.tipo === TIPO.CONGEDO) { const l = new Lettore(m.corpo); esito(MOTIVO[l.u8()] || "congedato", false); return; }
  if (m.tipo !== TIPO.AMMESSO) { esito("Il server ha risposto 0x" + m.tipo.toString(16) + " invece di AMMESSO.", false); return; }
  nota("AMMESSO");

  /* ── ATTACCA (§4.5) ─────────────────────────────────────────────────── */
  /* ⛔ I limiti sono normativi: fra 320×240 e 7680×4320, ed entrambe PARI. */
  const pari = (n, min, max) => Math.max(min, Math.min(max, n - (n % 2)));
  const tela_l = pari(1920, 320, 7680), tela_a = pari(1080, 240, 4320);
  const vista_l = Math.max(1, Math.round(innerWidth * devicePixelRatio));
  const vista_a = Math.max(1, Math.round(innerHeight * devicePixelRatio));
  const disp = (navigator.language || "it").slice(0, 2).toLowerCase();
  await canale.manda(TIPO.ATTACCA,
    new Scrittore().u32(tela_l).u32(tela_a).u32(vista_l).u32(vista_a).str(disp).byte());
  nota("ATTACCA: tela " + tela_l + "×" + tela_a + ", vista " + vista_l + "×" + vista_a + ", disposizione «" + disp + "»");

  m = await canale.ricevi();
  if (!m) { esito("Il server ha chiuso il canale senza rispondere ad ATTACCA.", false); return; }
  if (m.tipo === TIPO.CONGEDO) { const l = new Lettore(m.corpo); esito(MOTIVO[l.u8()] || "congedato", false); return; }
  if (m.tipo !== TIPO.SESSIONE) { esito("Il server ha risposto 0x" + m.tipo.toString(16) + " invece di SESSIONE.", false); return; }
  {
    const l = new Lettore(m.corpo);
    const stato = l.u8(), tl = l.u32(), ta = l.u32(), desktop = l.str();
    esito("Ammesso, sessione " + (stato === 1 ? "nuova" : "ripresa") +
          ", tela " + tl + "×" + ta + ", desktop " + desktop, true);
  }
}
