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
PAGINA_HTML = "/home/nicfio/Documenti/REMOTIX_V2/src/pagina.html"

t = open(PAGINA_HTML).read()
i = t.index("const SONDE = {")
blocco = t[i:t.index("};", i) + 2]
SONDE = {}
for nome in ("hevc-8", "hevc-10", "av1-8", "av1-10"):
    SONDE[nome] = re.search(r'"%s".*?dati: "([^"]+)"' % nome, blocco, re.S).group(1)

# ⚠ Le stringhe sono quelle che la pagina DICHIARA: se sbagliassi qui,
#   proverei un'altra cosa.
CODEC = {"hevc-8": "hev1.1.6.L93.B0", "hevc-10": "hev1.2.4.L93.B0",
         "av1-8": "av01.0.04M.08", "av1-10": "av01.0.04M.10"}

PAGINA = """<!doctype html><meta charset=utf-8><body><pre id=o>…</pre><script>
const SONDE = %s, CODEC = %s;
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
          {codec: CODEC[nome], codedWidth: 64, codedHeight: 48})).supported;
    } catch (e) { r.dichiara = 'eccezione ' + e.name; }
    try {
      await new Promise((res, rej) => {
        const d = new VideoDecoder({
          output: (f) => { r.fotogrammi++; r.formato = f.format; f.close(); },
          error: (e) => { r.errore = e.name + ': ' + e.message; rej(e); }});
        d.configure({codec: CODEC[nome], codedWidth: 64, codedHeight: 48});
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
</script></body>""" % (json.dumps(SONDE), json.dumps(CODEC))

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
            print("     %-9s %s  dichiara %-5s  fotogrammi %d  formato %s  %s"
                  % (nome, "⭐ DECODIFICA" if ok else "⛔ ZERO      ",
                     e["dichiara"], e["fotogrammi"], e["formato"],
                     e["errore"] or ""))
    sys.exit(0 if rossi == 0 else 2)
