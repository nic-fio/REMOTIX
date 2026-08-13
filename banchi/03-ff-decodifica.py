#!/usr/bin/env python3
# ⭐⭐ CORSIA D — LA DECODIFICA, MISURATA SU FIREFOX **E** SU CHROME
#     con lo stesso attrezzo, perche' un numero di Firefox senza il gemello di
#     Chrome preso con la stessa mano non si sottrae da niente.
#
# ⛔ Firefox non ha CDP e non si guida da fuori ⇒ la pagina **rimanda gli esiti
#    da sola** con un POST (la strada di `03-palco-codec.py`, 13 agosto).
#
# ⭐ CHE COSA MISURA, e sono due grandezze DIVERSE che il cronometro da solo
#    confonde (`LEZIONI.md` §6.2):
#      · **seriale** — si consegna UN pezzo, si aspetta il suo fotogramma, poi
#        il prossimo.  E' il regime del prodotto (i pezzi arrivano dal filo uno
#        alla volta) ed e' l'analogo del tratto 5 di `03-b17-ritardo.py`
#        (*«`decode()` → richiamo del decodificatore»*, 7,58 ms su Chrome).
#      · **raffica** — si consegna tutto e si aspetta `flush()`.  E' la PORTATA,
#        e sovrastima quel che il prodotto vede, perche' e' pipelined.
#
# ⛔⛔ E I FOTOGRAMMI IN USCITA SI CONTANO, sempre.  Un decodificatore che ne
#     butta la meta' e' «veloce il doppio» per il cronometro (§2.0, la sorella
#     minore del confronto che non era un confronto).
#
# ⛔ LA SCENA E' DICHIARATA ACCANTO A OGNI NUMERO (§1.1 e §2.0): motore,
#    bandiere, palco, gpu vista dalla pagina, flusso, `hardwareAcceleration`
#    chiesta.  ⚠ E la scena del FLUSSO e' **sintetica** (`testsrc2`): questi
#    millisecondi NON si sottraggono dai 74,58 della fase 3.
#
# ⛔ CODICI D'USCITA — il rosso sta qui, non nella prosa:
#      0  misurato          3  il palco non ha risposto (non e' un «no»)
#      4  la pagina non ha rimandato niente
#      5  non ero solo e mi era stato chiesto di esserlo
#      2  eccezione del banco (⛔ NON e' un caso rosso: e' il banco rotto)
#
# uso:  python3 banchi/03-ff-decodifica.py firefox|chrome [giri]
#         [--porta 8870] [--schermo :70] [--con-finestra] [--senza-gpu]
#         [--esigi-solitudine] [--pezzi 120] [--confessione]
import importlib.util
import json
import os
import sys
import time

_qui = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("palco", os.path.join(_qui, "03-ff-palco.py"))
P = importlib.util.module_from_spec(_s)
_s.loader.exec_module(P)

MODI = ["no-preference", "prefer-hardware", "prefer-software"]

PAGINA = """<!doctype html><meta charset=utf-8><title>03-ff-decodifica</title><body>
<pre id=o>in corso…</pre><script>
const CASI = %s;
const PEZZI_MAX = %d;
const attesa = (ms) => new Promise(r => setTimeout(r, ms));
const rimanda = async (c) => {
  try { document.getElementById('o').textContent = JSON.stringify(c).slice(0, 4000); } catch (e) {}
  await fetch('/esito', {method: 'POST', body: JSON.stringify(c)});
};
window.onerror = (m, f, l) => { rimanda({errore_pagina: m + ' @' + f + ':' + l}); };

const palco = () => {
  let gpu;
  try {
    const c = document.createElement('canvas');
    const g = c.getContext('webgl2') || c.getContext('webgl');
    if (!g) gpu = 'niente webgl';
    else {
      const d = g.getExtension('WEBGL_debug_renderer_info');
      gpu = d ? g.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'webgl senza nome';
    }
  } catch (e) { gpu = 'errore: ' + e; }
  return {motore: navigator.userAgent, gpu,
          nuclei: navigator.hardwareConcurrency,
          crossOriginIsolated: self.crossOriginIsolated,
          visibilityState: document.visibilityState,
          // ⛔ IL PALCO LETTO DALLA PAGINA, e non dalle intenzioni del banco:
          //    uno `screen` di 2560x1080 vuol dire che NON siamo sull'Xvfb del
          //    banco (che e' 1920x1200) ma sul desktop vero dell'utente.
          schermo: screen.width + 'x' + screen.height,
          finestra: innerWidth + 'x' + innerHeight,
          pixelRatio: devicePixelRatio,
          VideoDecoder: ('VideoDecoder' in window)};
};

const flussi = {};
async function prendi(nome) {
  if (!flussi[nome]) flussi[nome] = await (await fetch('/' + nome)).arrayBuffer();
  return flussi[nome];
}

function chunks(buf, pezzi) {
  const out = [];
  for (let i = 0; i < pezzi.length && i < PEZZI_MAX; i++) {
    const p = pezzi[i];
    out.push(new EncodedVideoChunk({
      type: p.chiave ? 'key' : 'delta',
      timestamp: Math.round(i * 1000000 / 60),
      duration: Math.round(1000000 / 60),
      data: new Uint8Array(buf, p.pos, p.len)}));
  }
  return out;
}

// ⭐ SERIALE — un pezzo, il suo fotogramma, poi il prossimo.  Il regime del
//    prodotto.  ⛔ Il PRIMO fotogramma si tiene da parte: dentro c'e' anche
//    l'accensione del decodificatore (`LEZIONI.md` §1.4).
async function seriale(cfg, pz) {
  const lat = [];
  let uscite = 0, errore = null, risolvi = null, primo = null, forma = null;
  const dec = new VideoDecoder({
    output: (f) => {
      const t = performance.now();
      uscite++;
      if (!forma) forma = {format: f.format, w: f.codedWidth, h: f.codedHeight,
                           vw: f.visibleRect ? f.visibleRect.width : null};
      f.close();
      const r = risolvi; risolvi = null; if (r) r(t);
    },
    error: (e) => { errore = (e && e.message) || String(e);
                    const r = risolvi; risolvi = null; if (r) r(null); }});
  dec.configure(cfg);
  let scaduto = null;
  for (let i = 0; i < pz.length; i++) {
    const p = new Promise(r => { risolvi = r; });
    const t0 = performance.now();
    try { dec.decode(pz[i]); } catch (e) { errore = 'decode() ha lanciato: ' + e.message; break; }
    const t1 = await Promise.race([p, attesa(8000).then(() => 'scaduto')]);
    if (t1 === 'scaduto') { scaduto = i; break; }
    if (t1 === null) break;                       // errore del decodificatore
    if (i === 0) primo = t1 - t0; else lat.push(t1 - t0);
  }
  // ⛔ `flush()` CON UN TETTO: senza, una `Promise` che non si risolve mai fa
  //    sembrare «il motore non ce la fa» quel che e' «il banco e' appeso».
  //    `[M]` e' successo: il banco del disegno e' rimasto fermo 240 s qui.
  try { await Promise.race([dec.flush(), attesa(15000)]); } catch (e) {}
  try { dec.close(); } catch (e) {}
  return {entrate: pz.length, uscite, primo_fotogramma_ms: primo,
          latenze_ms: lat, scaduto_al_pezzo: scaduto, errore, forma};
}

// ⭐ RAFFICA — la PORTATA.  ⚠ sovrastima quel che il prodotto vede.
async function raffica(cfg, pz) {
  let uscite = 0, errore = null;
  const dec = new VideoDecoder({
    output: (f) => { uscite++; f.close(); },
    error: (e) => { errore = (e && e.message) || String(e); }});
  dec.configure(cfg);
  const t0 = performance.now();
  try { for (const c of pz) dec.decode(c); } catch (e) { errore = 'decode(): ' + e.message; }
  try { await Promise.race([dec.flush(), attesa(60000).then(() => { throw new Error('flush scaduto a 60 s'); })]); }
  catch (e) { errore = errore || e.message; }
  const t1 = performance.now();
  try { dec.close(); } catch (e) {}
  const ms = t1 - t0;
  return {entrate: pz.length, uscite, totale_ms: +ms.toFixed(2),
          ms_per_fotogramma: uscite ? +(ms / uscite).toFixed(3) : null,
          fotogrammi_al_secondo: uscite ? +(uscite * 1000 / ms).toFixed(2) : null,
          errore};
}

(async () => {
  const esiti = [];
  const p = palco();
  if (!p.VideoDecoder) { await rimanda({palco: p, esiti,
      nota: '⛔ VideoDecoder NON ESISTE in questo motore'}); return; }
  for (const caso of CASI) {
    const r = {flusso: caso.flusso, etichetta: caso.etichetta, codec: caso.codec,
               modo: caso.modo};
    const cfg = {codec: caso.codec, codedWidth: caso.larghezza,
                 codedHeight: caso.altezza, hardwareAcceleration: caso.modo,
                 optimizeForLatency: true};
    try {
      const s = await VideoDecoder.isConfigSupported(cfg);
      r.dichiara = {supported: s.supported,
                    config_tornata: s.config ? {hw: s.config.hardwareAcceleration,
                                                ofl: s.config.optimizeForLatency} : null};
    } catch (e) { r.dichiara = {eccezione: e.name + ' ' + e.message}; }
    if (!r.dichiara || r.dichiara.supported !== true) { esiti.push(r); continue; }
    try {
      const buf = await prendi(caso.flusso);
      r.seriale = await seriale(cfg, chunks(buf, caso.pezzi));
      r.raffica = await raffica(cfg, chunks(buf, caso.pezzi));
    } catch (e) { r.errore = e.name + ' ' + e.message; }
    esiti.push(r);
  }
  await rimanda({palco: p, esiti});
})();
</script></body>
"""


def _mediana(v):
    return P.dist(v)


def stampa(d, giro):
    p = d.get("palco", {})
    print("   giro %d — gpu vista dalla pagina: %s   ·   nuclei %s   ·   isolata %s"
          % (giro, p.get("gpu"), p.get("nuclei"), p.get("crossOriginIsolated")))
    for e in d.get("esiti", []):
        dic = e.get("dichiara") or {}
        if dic.get("supported") is not True:
            print("      %-34s %-16s ⛔ non dichiarato: %s"
                  % (e["etichetta"][:34], e["modo"], json.dumps(dic, ensure_ascii=False)))
            continue
        s, r = e.get("seriale") or {}, e.get("raffica") or {}
        ds = _mediana(s.get("latenze_ms") or [])
        buco = ""
        if s.get("uscite") != s.get("entrate"):
            buco = "  ⛔ USCITI %s SU %s" % (s.get("uscite"), s.get("entrate"))
        if s.get("errore"):
            buco += "  ⛔ %s" % s["errore"]
        print("      %-34s %-16s seriale med %s ms (n=%s, 1° %s ms) · raffica %s ms/fo "
              "= %s fo/s (%s su %s) · %s%s"
              % (e["etichetta"][:34], e["modo"], ds.get("mediana"), ds.get("n"),
                 (round(s["primo_fotogramma_ms"], 1) if s.get("primo_fotogramma_ms") else "?"),
                 r.get("ms_per_fotogramma"), r.get("fotogrammi_al_secondo"),
                 r.get("uscite"), r.get("entrate"),
                 (s.get("forma") or {}).get("format"), buco))


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("firefox", "chrome"):
        print("uso: 03-ff-decodifica.py firefox|chrome [giri] [--porta N] "
              "[--schermo :70] [--con-finestra] [--senza-gpu] "
              "[--esigi-solitudine] [--pezzi N] [--confessione]")
        return 64
    motore = a[0]
    giri = int(a[1]) if len(a) > 1 and a[1].isdigit() else 3

    def opz(nome, dif):
        return a[a.index(nome) + 1] if nome in a else dif
    porta0 = int(opz("--porta", 8870))
    schermo0 = opz("--schermo", ":70")
    pezzi = int(opz("--pezzi", 120))
    finestra = "--con-finestra" in a          # ⇒ NON headless
    con_gpu = "--senza-gpu" not in a
    confessione = "--confessione" in a
    # ⛔⛔ L'INTERRUTTORE PIU' IMPORTANTE DI QUESTO BANCO, e non c'era il 13
    #    agosto: `x11` mette Chrome sull'Xvfb del banco, `wayland` lo manda
    #    sulla SESSIONE VERA DELL'UTENTE anche se `DISPLAY` dice altro.
    #    ⇒ La differenza fra i due non e' di comodo: e' la differenza fra
    #      «misurato sul palco del banco» e «misurato sul desktop di Nic».
    ozone = opz("--ozone", "x11")

    prima = P.scena_macchina("prima del giro")
    porte_prima = P.porte_protette()
    if "--esigi-solitudine" in a and not prima["sono_solo"]:
        print("⛔ NON ERO SOLO e mi era stato chiesto di esserlo — non misuro.")
        print(json.dumps(prima, indent=1, ensure_ascii=False))
        return 5

    flussi = P.prepara_flussi()
    casi = []
    for f in flussi:
        for m in MODI:
            casi.append({"flusso": f["nome"], "etichetta": f["etichetta"],
                         "codec": f["codec"], "modo": m,
                         "larghezza": f["larghezza"], "altezza": f["altezza"],
                         "pezzi": f["pezzi"][:pezzi]})
    # ⛔⛔ L'INTERRUTTORE CHE CERCA LA VARIABILE NON DICHIARATA.  Su Firefox il
    #    PRIMO caso della lista e' uscito sistematicamente piu' lento degli
    #    altri due dello stesso flusso (11,9 contro 9,1 ms, 3 giri su 3).  Un
    #    esito che si ripete non e' rumore: o e' del caso, o e' della POSIZIONE.
    #    ⇒ Si rovescia l'ordine e si riguarda.  Se il lento resta lo stesso
    #      CASO, e' del caso; se resta la stessa POSIZIONE, e' l'accensione del
    #      motore che il banco stava attribuendo a `no-preference`.
    if "--rovescia" in a:
        casi.reverse()
    pagina = PAGINA % (json.dumps(casi), pezzi)

    print("== LA SCENA ==")
    print("   motore chiesto:  %s%s" % (motore, "" if finestra else "  (headless)"))
    print("   palco:           Xvfb %s, 1920x1200x24%s%s"
          % (schermo0, "" if con_gpu else "   ⛔ CON --disable-gpu",
             ("   ·  ozone=%s%s" % (ozone, "  ⛔⛔ NON E' L'XVFB: E' LA SESSIONE VERA"
                                    if ozone == "wayland" else ""))
             if motore == "chrome" else ""))
    print("   flusso:          testsrc2 1920x1080, 120 fotogrammi a 60/s "
          "⚠ SCENA SINTETICA, non il desktop vero")
    for f in flussi:
        print("                    %-16s %-17s %d pezzi, %d byte"
              % (f["nome"], f["codec"], len(f["pezzi"]), f["byte"]))
    print("   ero solo:        %s   (carico %s · browser altrui %d · %s)"
          % ("SI" if prima["sono_solo"] else "⛔ NO", prima["carico_1_5_15"],
             prima["browser_vivi"], prima["criterio_di_solitudine"]))
    print("   porte protette:  %s" % json.dumps(porte_prima, ensure_ascii=False))
    print("== GLI ESITI ==")

    tutti = []
    for n in range(giri):
        moz = ("PlatformDecoderModule:5,MediaFormatReader:5"
               if (confessione and motore == "firefox") else None)
        d = P.giro(pagina, motore, porta0 + n, ":%d" % (int(schermo0[1:]) + n),
                   headless=not finestra, con_gpu=con_gpu, attesa_s=420,
                   moz_log=moz, xvfb=True, ozone=ozone)
        d["_macchina"] = P.scena_macchina("dopo il giro %d" % (n + 1))
        if "errore" in d:
            print("   giro %d ⛔ %s" % (n + 1, d["errore"]))
            if d.get("coda_del_motore"):
                print("      coda del motore: %s" % d["coda_del_motore"][-300:].replace("\n", " | "))
        elif "errore_pagina" in d:
            print("   giro %d ⛔ la pagina e' morta: %s" % (n + 1, d["errore_pagina"]))
        else:
            stampa(d, n + 1)
        if moz:
            d["_confessione"] = P.leggi_registro_motore(
                d.get("_palco", {}).get("registro_motore", ""),
                ["decoder", "dav1d", "vaapi", "ffvpx", "vpx", "hardware",
                 "PDMFactory", "CreateDecoder"])[:80]
        tutti.append(d)

    dopo = P.scena_macchina("a fine banco")
    porte_dopo = P.porte_protette()
    # ⛔ Il nome porta dentro il PALCO: due giri con palchi diversi che si
    #    sovrascrivessero sarebbero la stessa trappola di `w` invece di `>>`.
    fuori = os.path.join(P.BASE, "03-ff-decodifica-%s-%s%s%s.json"
                         % (motore, "finestra" if finestra else "headless",
                            "-" + ozone if (finestra and motore == "chrome") else "",
                            "-rovesciato" if "--rovescia" in a else ""))
    with open(fuori, "w") as f:
        json.dump({"prima": prima, "dopo": dopo, "porte_prima": porte_prima,
                   "porte_dopo": porte_dopo, "giri": tutti}, f, indent=1,
                  ensure_ascii=False)
    print("== DOPO ==")
    print("   porte protette prima %s, dopo %s   ⇒ %s"
          % (porte_prima.get("quante"), porte_dopo.get("quante"),
             "⭐ non ne ho toccata nessuna"
             if porte_prima.get("quante") == porte_dopo.get("quante") == 3
             else "⛔ IL CONTO NON TORNA"))
    print("   ero solo alla fine: %s" % ("SI" if dopo["sono_solo"] else "⛔ NO"))
    print("   esiti in %s" % fuori)

    buoni = [g for g in tutti if "errore" not in g and "errore_pagina" not in g]
    if not buoni:
        print("⛔ NESSUN GIRO E' ARRIVATO — non e' «Firefox non ce la fa», e' "
              "«non ho potuto guardare».  Il palco resta [?] DICHIARATA.")
        return 4
    if porte_prima.get("quante") != porte_dopo.get("quante"):
        return 6
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:                        # noqa: BLE001
        # ⛔ `RuntimeError` esce 1 come un caso rosso: qui esce 2, e si distingue.
        import traceback
        traceback.print_exc()
        print("⛔ ECCEZIONE DEL BANCO (non e' un caso rosso): %s" % e)
        sys.exit(2)
