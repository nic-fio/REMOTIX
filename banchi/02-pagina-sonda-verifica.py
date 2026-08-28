#!/usr/bin/env python3
# ⛔ LE SONDE NUOVE DECODIFICANO DAVVERO? — e la domanda non e' retorica.
#
# Le vecchie dicevano `isConfigSupported: true` e poi cadevano con
# `EncodingError` sui byte: ⇒ **chiedere non basta, si decodifica e si contano
# i fotogrammi**. Qui si prendono le sonde ESATTAMENTE come stanno in
# `src/pagina.html` (lette dal file, non ricopiate) e si danno in pasto a
# `VideoDecoder` con la STESSA stringa di codec che la pagina dichiara.
#
# ⭐ E il controllo positivo sono le due sonde AV1, che non sono cambiate: se
#   cadessero anche quelle, il difetto sarebbe del banco.
import http.server, json, os, re, shutil, socketserver, subprocess, sys, threading, time

BASE = "/home/nicfio/K-prova-sonde"
PAGINA_HTML = "/home/nicfio/Documenti/REMOTIX/src/pagina.html"

t = open(PAGINA_HTML).read()
i = t.index("const SONDE = {")
blocco = t[i:t.index("};", i) + 2]
SONDE, MISURE = {}, {}
for nome in ("hevc-8", "hevc-10", "av1-8", "av1-10"):
    SONDE[nome] = re.search(r'"%s".*?dati: "([^"]+)"' % nome, blocco, re.S).group(1)
    MISURE[nome] = (64, 48)

# ⚠ Le stringhe sono quelle che la pagina DICHIARA: se sbagliassi qui,
#   proverei un'altra cosa.
CODEC = {"hevc-8": "hev1.1.6.L93.B0", "hevc-10": "hev1.2.4.L93.B0",
         "av1-8": "av01.0.04M.08", "av1-10": "av01.0.04M.10"}

# ⛔⛔ E LA SCALA DI MISURA ENTRA QUI PERCHE' LA PRIMA VERSIONE DI QUESTO BANCO
#     GUARDAVA SOLO META' DELLA PAGINA — la stessa meta' che era stata curata.
#
#     La pagina porta DUE gruppi di sonde e li usa per due decisioni diverse:
#       `SONDE`         64x48   → **quali codec entrano nel `CIAO`**
#       `SONDE_MISURA`  320x240…3840x2160 → **`video.misura_massima` di §4.3**
#
#     ⇒ Curato il primo gruppo e non il secondo, il prodotto e' finito in uno
#     stato PEGGIORE di prima: HEVC veniva negoziato (le sonde di presenza
#     dipingevano) e poi non dipingeva ai gradini (ancora `Rext`) ⇒
#     `misura_massima` crollava a 320x240, e il prodotto — giustamente, §6.2 —
#     si rifiutava di spedire un 1920x1080 dentro quel tetto.  ZERO fotogrammi.
#
#  ⭐ Un banco che verifica meta' di quel che la pagina dichiara **non e' meta'
#     di un controllo: e' un controllo che sa dire di si' e non di no.**
i = t.index("const SONDE_MISURA = {")
blocco_m = t[i:t.index("\n};", i) + 3]
# ⛔ E LA PRIMA STESURA DI QUESTE RIGHE HA SBAGLIATO NELLO STESSO MODO DI TUTTO
#    IL RESTO DELLA SERATA: tagliava la sezione di ogni codec al primo `]`, che
#    e' quello di `sinistra: [220, 32, 32]` ⇒ **zero gradini letti**, e il banco
#    e' uscito VERDE provandone 4 su 16.  ⚠ Un banco che prova meno di quel che
#    dice ha lo stesso aspetto di uno che passa.
#    ⇒ Adesso la sezione si trova per POSIZIONE dei due nomi, e alla fine il
#      conto dei gradini si CONTROLLA contro quel che il file dichiara.
taglio = {c: blocco_m.index("%s: [" % c) for c in ("hevc", "av1")}
ordine = sorted(taglio, key=lambda c: taglio[c])
for k, codec in enumerate(ordine):
    inizio = taglio[codec]
    fine = taglio[ordine[k + 1]] if k + 1 < len(ordine) else len(blocco_m)
    for m in re.finditer(r'\{ l: (\d+), a: (\d+).*?dati: "([^"]+)"',
                         blocco_m[inizio:fine], re.S):
        l, a, dati = m.group(1), m.group(2), m.group(3)
        nome = "%s-%sx%s" % (codec, l, a)
        SONDE[nome] = dati
        CODEC[nome] = ("hev1.1.6.L93.B0" if codec == "hevc"
                       else "av01.0.04M.08")
        MISURE[nome] = (int(l), int(a))

# ⛔ IL DENOMINATORE PRIMA DEL RISULTATO: quante sonde il file DICHIARA, contate
#    sul file, contro quante ne ho lette.  Senza, «le ho provate tutte» e «ne ho
#    lette quattro» si leggono uguali.
_dichiarate = len(re.findall(r'dati: "', blocco)) + \
    len(re.findall(r'dati: "', blocco_m))
if len(SONDE) != _dichiarate:
    raise SystemExit("⛔ la pagina dichiara %d sonde e ne ho lette %d: NON "
                     "provo un sottoinsieme e lo chiamo verde"
                     % (_dichiarate, len(SONDE)))

PAGINA = """<!doctype html><meta charset=utf-8><body><pre id=o>…</pre><script>
const SONDE = %s, CODEC = %s, MISURE = %s;
const b64 = (s) => Uint8Array.from(atob(s), c => c.charCodeAt(0));
(async () => {
  const gpu = (() => { try { const c = document.createElement('canvas');
      const g = c.getContext('webgl'); if (!g) return 'niente webgl';
      const d = g.getExtension('WEBGL_debug_renderer_info');
      return d ? g.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'webgl'; }
      catch (e) { return 'errore'; } })();
  const esiti = {};
  for (const nome of Object.keys(SONDE)) {
    const r = {codec: CODEC[nome], fotogrammi: 0, formato: null, errore: null};
    try {
      r.dichiara = (await VideoDecoder.isConfigSupported(
          {codec: CODEC[nome], codedWidth: MISURE[nome][0],
           codedHeight: MISURE[nome][1]})).supported;
    } catch (e) { r.dichiara = 'eccezione ' + e.name; }
    try {
      await new Promise((res, rej) => {
        const d = new VideoDecoder({
          output: (f) => { r.fotogrammi++; r.formato = f.format; f.close(); },
          error: (e) => { r.errore = e.name + ': ' + e.message; rej(e); }});
        d.configure({codec: CODEC[nome], codedWidth: MISURE[nome][0],
                     codedHeight: MISURE[nome][1]});
        d.decode(new EncodedVideoChunk(
            {type: 'key', timestamp: 0, data: b64(SONDE[nome])}));
        d.flush().then(res, rej);
        setTimeout(() => rej(new Error('scaduto')), 8000);
      });
    } catch (e) { if (!r.errore) r.errore = String(e && e.message || e); }
    esiti[nome] = r;
  }
  const corpo = JSON.stringify({gpu, esiti});
  document.getElementById('o').textContent = corpo;
  await fetch('/esito', {method: 'POST', body: corpo});
})();
</script></body>""" % (json.dumps(SONDE), json.dumps(CODEC), json.dumps(MISURE))

ric = {}


class S(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        b = PAGINA.encode(); self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers()
        self.wfile.write(b)
    def do_POST(self):
        ric["d"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.send_response(204); self.end_headers()


def giro(n):
    ric.pop("d", None)
    prof = os.path.join(BASE, "p%d" % n)
    shutil.rmtree(prof, ignore_errors=True); os.makedirs(prof)
    porta, schermo = 8850 + n, ":%d" % (50 + n)
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", porta), S)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    x = subprocess.Popen(["Xvfb", schermo, "-screen", "0", "1280x1024x24"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    amb = dict(os.environ); amb["DISPLAY"] = schermo
    amb.pop("WAYLAND_DISPLAY", None)
    b = subprocess.Popen(["google-chrome", "--user-data-dir=" + prof,
                          "--no-first-run", "--no-default-browser-check",
                          "--disable-sync", "http://127.0.0.1:%d/" % porta],
                         env=amb, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    fine = time.time() + 90
    while time.time() < fine and "d" not in ric:
        time.sleep(0.3)
    b.terminate()
    try: b.wait(timeout=10)
    except subprocess.TimeoutExpired: b.kill()
    x.terminate(); srv.shutdown(); srv.server_close()
    shutil.rmtree(prof, ignore_errors=True)
    return ric.get("d", {"errore": "niente in 90 s"})


if __name__ == "__main__":
    os.makedirs(BASE, exist_ok=True)
    d = subprocess.run(["df", "-h", BASE], capture_output=True, text=True).stdout
    print("== La scena: %s" % d.strip().splitlines()[-1])
    rossi = 0
    for n in range(3):
        r = giro(n)
        if "errore" in r and "esiti" not in r:
            print("  giro %d ⛔ %s" % (n + 1, r["errore"])); rossi += 1; continue
        print("  giro %d — gpu: %s" % (n + 1, r["gpu"]))
        for nome, e in r["esiti"].items():
            ok = e["fotogrammi"] > 0
            if not ok:
                rossi += 1
            print("     %-16s %s  dichiara %-5s  fotogrammi %d  formato %s  %s"
                  % (nome, "⭐ DECODIFICA" if ok else "⛔ ZERO      ",
                     e["dichiara"], e["fotogrammi"], e["formato"],
                     e["errore"] or ""))
    sys.exit(0 if rossi == 0 else 2)
