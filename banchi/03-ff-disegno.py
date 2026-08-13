#!/usr/bin/env python3
# ⭐⭐ CORSIA D — IL DISEGNO, MISURATO SU FIREFOX **E** SU CHROME
#     con lo stesso attrezzo, e col gemello di Chrome accanto a ogni numero.
#
# ⛔ TRE DOMANDE, e la prima decide se le altre due esistono:
#
#   1. ⭐ **`requestAnimationFrame` gira, su questo palco, con QUESTO motore?**
#      `banchi/03-quadri.py` (del coordinatore, 13 agosto) ha SMENTITO su Chrome
#      la riga «su Xvfb rAF non gira mai»: 153-181 quadri in 3 s in tutte e tre
#      le configurazioni.  ⛔ Ma quella misura e' di **Chrome**: su Firefox la
#      domanda e' aperta, e se li' rAF non girasse, un cammino di disegno del
#      prodotto sarebbe **codice morto** sul secondo motore.
#      ⇒ Il metodo e' copiato da `03-quadri.py` (3 secondi, rete di sicurezza a
#        6 s perche' «zero quadri» e «pagina morta» non si somiglino).
#
#   2. **Quanto costa dipingere un fotogramma decodificato**, con i DUE
#      `drawImage` del prodotto (`src/pagina.html:1863` e `:1446`): dal
#      fotogramma al deposito, e dal deposito alla tela.
#
#   3. ⛔⛔ **Quel `drawImage` ha fatto il lavoro, o l'ha rimandato?**  Il costo
#      si misura DUE VOLTE: com'e' (come fa il prodotto) e con una rilettura di
#      **un pixel solo** subito dopo, che obbliga il motore a finire.  Se i due
#      numeri divergono, il primo non e' il costo del disegno: e' il costo di
#      METTERLO IN CODA — e i due motori possono mentire in modi diversi.
#
# ⛔ E IL CONTROLLO CHE IMPEDISCE AL BANCO DI AUTOINGANNARSI: un `drawImage` che
#    non disegna niente e' velocissimo.  ⇒ alla fine si rilegge la tela e si
#    pretende che i pixel **non siano tutti uguali**.  Se lo sono, il numero e'
#    buttato e il banco lo dice.
#
# ⚠ `src/pagina.html` E' CAMBIATA DUE VOLTE la sera del 13 (le sonde HEVC).
#   ⭐ Verificato riga per riga: la FORMA che questo banco rispecchia — due
#   `drawImage` e `willReadFrequently: true` sulla tela — **non e' cambiata**;
#   sono scesi di una riga i numeri, e sono aggiornati qui sopra.
#   ⛔ E questo banco **non carica** la pagina del prodotto: serve la propria.
#
# ⚠ LA SCENA: flusso `testsrc2` 1920x1080 sintetico (non il desktop vero), AV1
#    Main 10 bit da libsvtav1 preset 10 `pred-struct=1` — le impostazioni del
#    prodotto.  ⇒ Questi millisecondi si confrontano **fra motori**, non si
#    sottraggono dai 74,58 ms della fase 3.
#
# ⛔ CODICI D'USCITA: 0 misurato · 3 palco muto · 4 la pagina non ha rimandato
#    niente · 5 non ero solo e mi era stato chiesto di esserlo · 2 eccezione del
#    banco (⛔ non e' un caso rosso) · 6 il conto delle porte protette non torna
#    · 7 la tela e' uscita UNIFORME (il disegno non ha disegnato).
#
# uso:  python3 banchi/03-ff-disegno.py firefox|chrome [giri]
#         [--porta 8875] [--schermo :75] [--con-finestra] [--senza-gpu]
#         [--esigi-solitudine] [--pezzi 120]
import importlib.util
import json
import os
import sys

_qui = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("palco", os.path.join(_qui, "03-ff-palco.py"))
P = importlib.util.module_from_spec(_s)
_s.loader.exec_module(P)

PAGINA = """<!doctype html><meta charset=utf-8><title>03-ff-disegno</title><body>
<canvas id=raf width=320 height=200></canvas>
<pre id=o>in corso…</pre><script>
const CASO = %s;
const PEZZI_MAX = %d;
const attesa = (ms) => new Promise(r => setTimeout(r, ms));
let rimandato = false;
const rimanda = async (c) => {
  if (rimandato) return; rimandato = true;
  try { document.getElementById('o').textContent = JSON.stringify(c).slice(0, 3000); } catch (e) {}
  await fetch('/esito', {method: 'POST', body: JSON.stringify(c)});
};
window.onerror = (m, f, l) => { rimanda({errore_pagina: m + ' @' + f + ':' + l}); };
// ⛔ La rete di sicurezza di `03-quadri.py`: senza, «non ha girato» e «la
//    pagina e' morta» avrebbero lo stesso aspetto.
setTimeout(() => rimanda({errore_pagina: 'la pagina non e\\u0027 arrivata in fondo in 240 s'}), 240000);

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
  return {motore: navigator.userAgent, gpu, nuclei: navigator.hardwareConcurrency,
          crossOriginIsolated: self.crossOriginIsolated,
          visibilita: document.visibilityState,
          // ⛔ IL PALCO LETTO DALLA PAGINA (vedi `03-ff-decodifica.py`)
          schermo: screen.width + 'x' + screen.height,
          finestra: innerWidth + 'x' + innerHeight,
          pixelRatio: devicePixelRatio,
          VideoDecoder: ('VideoDecoder' in window),
          OffscreenCanvas: (typeof OffscreenCanvas !== 'undefined')};
};

// ═══ 1. I QUADRI — il metodo di `banchi/03-quadri.py`, copiato ═══
function quadri() {
  return new Promise((res) => {
    let n = 0, primo = null, ultimo = null;
    const t0 = performance.now();
    const g = document.getElementById('raf').getContext('2d');
    let finito = false;
    const fine = () => { if (finito) return; finito = true;
      res({quadri: n, durata_ms: Math.round(performance.now() - t0),
           primo, ultimo, visibilita: document.visibilityState}); };
    function passo(t) {
      n++; if (primo === null) primo = t; ultimo = t;
      g.fillStyle = (n %% 2) ? '#000' : '#fff'; g.fillRect(0, 0, 320, 200);
      if (performance.now() - t0 < 3000) requestAnimationFrame(passo); else fine();
    }
    requestAnimationFrame(passo);
    setTimeout(() => { if (n === 0) fine(); }, 6000);   // ⛔ il controllo negativo
  });
}

// ═══ 2-3. IL DISEGNO — i due `drawImage` del prodotto, e il loro controllo ═══
async function dipingi(forzato) {
  const buf = await (await fetch('/' + CASO.flusso)).arrayBuffer();
  // Le due tele del prodotto: `deposito` (grandezza del fotogramma) e `tela`
  // (la vista).  `src/pagina.html:1861` e `:1136`.
  const deposito = document.createElement('canvas');
  deposito.width = CASO.larghezza; deposito.height = CASO.altezza;
  const dp = deposito.getContext('2d', {alpha: false});
  const tela = document.createElement('canvas');
  tela.width = 1280; tela.height = 720;
  // ⛔⛔ `willReadFrequently: true` E' QUEL CHE FA IL PRODOTTO
  //    (`src/pagina.html:1137`), e va messo in TUTT'E DUE i passaggi.
  //    ⚠ La prima stesura di questo banco lo metteva solo nel passaggio
  //    «forzato»: i due numeri differivano allora per DUE variabili (la
  //    rilettura E il tipo di tela), cioe' era lo stesso errore del confronto
  //    fra codificatori a bitrate libero.  Qui la variabile e' UNA: la
  //    rilettura di un pixel.
  const tp = tela.getContext('2d', {alpha: false, willReadFrequently: true});

  const cfg = {codec: CASO.codec, codedWidth: CASO.larghezza,
               codedHeight: CASO.altezza, hardwareAcceleration: 'no-preference',
               optimizeForLatency: true};
  const s = await VideoDecoder.isConfigSupported(cfg);
  if (s.supported !== true) return {non_dichiarato: true, dichiara: s.supported};

  const disegni = [], decodifiche = [];
  let uscite = 0, errore = null, risolvi = null, forma = null;
  const dec = new VideoDecoder({
    output: (f) => {
      const t = performance.now();
      uscite++;
      if (!forma) forma = {format: f.format, w: f.codedWidth, h: f.codedHeight};
      // ⛔ I DUE `drawImage` del prodotto, nello stesso ordine.
      const d0 = performance.now();
      try {
        dp.drawImage(f, 0, 0);
        tp.drawImage(deposito, 0, 0, tela.width, tela.height);
        if (forzato) tp.getImageData(0, 0, 1, 1);   // obbliga a finire
        disegni.push(performance.now() - d0);
      } catch (e) { errore = errore || ('drawImage ha lanciato: ' + e.message); }
      f.close();
      const r = risolvi; risolvi = null; if (r) r(t);
    },
    error: (e) => { errore = errore || ((e && e.message) || String(e));
                    const r = risolvi; risolvi = null; if (r) r(null); }});
  dec.configure(cfg);

  for (let i = 0; i < CASO.pezzi.length && i < PEZZI_MAX; i++) {
    const p = CASO.pezzi[i];
    const chunk = new EncodedVideoChunk({
      type: p.chiave ? 'key' : 'delta', timestamp: Math.round(i * 1000000 / 60),
      duration: Math.round(1000000 / 60), data: new Uint8Array(buf, p.pos, p.len)});
    const att = new Promise(r => { risolvi = r; });
    const t0 = performance.now();
    try { dec.decode(chunk); } catch (e) { errore = 'decode(): ' + e.message; break; }
    const t1 = await Promise.race([att, attesa(8000).then(() => 'scaduto')]);
    if (t1 === 'scaduto' || t1 === null) { errore = errore || ('fermo al pezzo ' + i); break; }
    decodifiche.push(t1 - t0);
  }
  // ⛔ `flush()` CON UN TETTO — vedi `03-ff-decodifica.py`: senza, il banco
  //    e' rimasto appeso 240 s e sembrava che fosse il motore a non farcela.
  try { await Promise.race([dec.flush(), attesa(15000)]); } catch (e) {}
  try { dec.close(); } catch (e) {}

  // ⛔ IL CONTROLLO CHE IMPEDISCE IL VERDE FACILE: la tela ha DAVVERO dei pixel?
  let vernice = null;
  try {
    const im = tp.getImageData(0, 0, tela.width, tela.height).data;
    let mi = 255, ma = 0, somma = 0;
    for (let i = 0; i < im.length; i += 4004) {         // un campione ogni ~1000 px
      const v = im[i]; if (v < mi) mi = v; if (v > ma) ma = v; somma += v;
    }
    vernice = {minimo: mi, massimo: ma, uniforme: (ma - mi) < 8};
  } catch (e) { vernice = {errore: e.message}; }

  return {entrate: Math.min(CASO.pezzi.length, PEZZI_MAX), uscite, forma, errore,
          disegno_ms: disegni, decodifica_ms: decodifiche, vernice};
}

(async () => {
  const p = palco();
  if (!p.VideoDecoder) { await rimanda({palco: p, nota: '⛔ VideoDecoder NON ESISTE'}); return; }
  const q = await quadri();
  const normale = await dipingi(false);
  const forzato = await dipingi(true);
  await rimanda({palco: p, quadri: q, disegno_come_il_prodotto: normale,
                 disegno_con_rilettura: forzato});
})();
</script></body>
"""


def _riassunto(r):
    if not r or r.get("non_dichiarato"):
        return "⛔ il motore non dichiara il codec"
    d = P.dist(r.get("disegno_ms") or [])
    c = P.dist(r.get("decodifica_ms") or [])
    v = r.get("vernice") or {}
    stato = "⭐" if not v.get("uniforme") else "⛔ TELA UNIFORME"
    coda = ""
    if r.get("uscite") != r.get("entrate"):
        coda += "  ⛔ USCITI %s SU %s" % (r.get("uscite"), r.get("entrate"))
    if r.get("errore"):
        coda += "  ⛔ %s" % r["errore"]
    return ("%s disegno med %s ms (p95 %s, n=%s) · decodifica med %s ms · "
            "pixel %s-%s%s" % (stato, d.get("mediana"), d.get("p95"), d.get("n"),
                               c.get("mediana"), v.get("minimo"), v.get("massimo"), coda))


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("firefox", "chrome"):
        print("uso: 03-ff-disegno.py firefox|chrome [giri] [--porta N] [--schermo :75] "
              "[--con-finestra] [--senza-gpu] [--esigi-solitudine] [--pezzi N]")
        return 64
    motore = a[0]
    giri = int(a[1]) if len(a) > 1 and a[1].isdigit() else 3

    def opz(nome, dif):
        return a[a.index(nome) + 1] if nome in a else dif
    porta0 = int(opz("--porta", 8875))
    schermo0 = opz("--schermo", ":75")
    pezzi = int(opz("--pezzi", 120))
    finestra = "--con-finestra" in a
    con_gpu = "--senza-gpu" not in a

    mie = tuple(range(porta0, porta0 + giri))
    prima = P.scena_macchina("prima del banco", mie_porte=mie)
    porte_prima = P.porte_protette()
    if "--esigi-solitudine" in a and not prima["sono_solo"]:
        print("⛔ NON ERO SOLO e mi era stato chiesto di esserlo — non misuro.")
        print("   ragioni: %s" % "; ".join(prima.get("perche") or []))
        print("   browser altrui vivi: %d" % prima["browser_vivi"])
        return 5

    f = [x for x in P.prepara_flussi() if x["nome"] == "av1-10b.obu"][0]
    caso = {"flusso": f["nome"], "codec": f["codec"], "larghezza": f["larghezza"],
            "altezza": f["altezza"], "pezzi": f["pezzi"][:pezzi]}
    pagina = PAGINA % (json.dumps(caso), pezzi)

    print("== LA SCENA ==")
    print("   motore:    %s%s" % (motore, "  (con finestra)" if finestra else "  (headless)"))
    print("   palco:     Xvfb %s, 1920x1200x24%s"
          % (schermo0, "" if con_gpu else "   ⛔ CON --disable-gpu"))
    print("   flusso:    %s  %s  %d pezzi  ⚠ scena SINTETICA (testsrc2), non il desktop vero"
          % (f["nome"], f["codec"], len(caso["pezzi"])))
    print("   disegno:   i due `drawImage` del prodotto (pagina.html:1863 e :1446),"
          " deposito 1920x1080 → tela 1280x720")
    print("   ero solo:  %s   %s" % ("SI" if prima["sono_solo"] else "⛔ NO",
                                     "; ".join(prima.get("perche") or [])))
    print("   porte protette: %s" % json.dumps(porte_prima, ensure_ascii=False))
    print("== GLI ESITI ==")

    tutti, uniforme = [], False
    for n in range(giri):
        d = P.giro(pagina, motore, porta0 + n, ":%d" % (int(schermo0[1:]) + n),
                   headless=not finestra, con_gpu=con_gpu, attesa_s=360)
        d["_macchina_dopo"] = P.scena_macchina("dopo il giro %d" % (n + 1), mie_porte=mie)
        tutti.append(d)
        if "errore" in d:
            print("   giro %d ⛔ %s" % (n + 1, d["errore"]))
            if d.get("coda_del_motore"):
                print("      coda del motore: %s"
                      % d["coda_del_motore"][-250:].replace("\n", " | "))
            continue
        if "errore_pagina" in d:
            print("   giro %d ⛔ la pagina e' morta: %s" % (n + 1, d["errore_pagina"]))
            continue
        q = d.get("quadri") or {}
        print("   giro %d — gpu: %s" % (n + 1, (d.get("palco") or {}).get("gpu")))
        print("      QUADRI (rAF)          %s %d quadri in %s ms · visibilita' %s"
              % ("⭐" if q.get("quadri") else "⛔ ZERO —", q.get("quadri", 0),
                 q.get("durata_ms"), q.get("visibilita")))
        print("      disegno come il prodotto   %s" % _riassunto(d.get("disegno_come_il_prodotto")))
        print("      disegno + rilettura 1 px   %s" % _riassunto(d.get("disegno_con_rilettura")))
        for k in ("disegno_come_il_prodotto", "disegno_con_rilettura"):
            v = ((d.get(k) or {}).get("vernice") or {})
            if v.get("uniforme"):
                uniforme = True

    dopo = P.scena_macchina("a fine banco", mie_porte=mie)
    porte_dopo = P.porte_protette()
    guardia = P.solo.confronta(prima, dopo)
    fuori = os.path.join(P.BASE, "03-ff-disegno-%s%s.json"
                         % (motore, "-finestra" if finestra else "-headless"))
    with open(fuori, "w") as fh:
        json.dump({"prima": prima, "dopo": dopo, "guardia": guardia,
                   "porte_prima": porte_prima, "porte_dopo": porte_dopo,
                   "giri": tutti}, fh, indent=1, ensure_ascii=False)
    print("== DOPO ==")
    print("   la finestra ha retto: %s   %s"
          % (guardia["regge"], "; ".join(guardia["guai"])))
    print("   porte protette prima %s, dopo %s ⇒ %s"
          % (porte_prima.get("quante"), porte_dopo.get("quante"),
             "⭐ non ne ho toccata nessuna"
             if porte_prima.get("quante") == porte_dopo.get("quante") == 3
             else "⛔ IL CONTO NON TORNA"))
    print("   esiti in %s" % fuori)

    buoni = [g for g in tutti if "errore" not in g and "errore_pagina" not in g]
    if not buoni:
        print("⛔ NESSUN GIRO E' ARRIVATO — non e' «Firefox non ce la fa», e' «non "
              "ho potuto guardare».  Resta [?] DICHIARATA.")
        return 4
    if porte_prima.get("quante") != porte_dopo.get("quante"):
        return 6
    if uniforme:
        print("⛔ LA TELA E' USCITA UNIFORME in almeno un giro: il disegno non ha "
              "disegnato, e il numero non vale.")
        return 7
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:                        # noqa: BLE001
        import traceback
        traceback.print_exc()
        print("⛔ ECCEZIONE DEL BANCO (non e' un caso rosso): %s" % e)
        sys.exit(2)
