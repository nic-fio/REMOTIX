#!/usr/bin/env python3
# ⛔ «Su Xvfb `requestAnimationFrame` non gira mai — 0 quadri in 3 s, CON E
#    SENZA GPU» e' una riga in attesa di entrare in LEZIONI.md.
#
# ⚠ La meta' «senza GPU» e' presa sullo stesso palco che il 13 agosto sera si e'
#   scoperto essere accecato da `--disable-gpu`. ⇒ Prima di scriverla in un
#   documento che poi decide dei banchi, si rimisura CON la GPU accesa.
#
# ⭐ E la domanda e' di CORRETTEZZA, non di tempo: 0 quadri contro ~180 non
#   cambia se la macchina e' carica. Il carico si dichiara lo stesso.
import http.server, json, os, shutil, socketserver, subprocess, sys, threading, time

BASE = os.path.expanduser("~/.cache/sonda-raf")
PAGINA = """<!doctype html><meta charset=utf-8><title>raf</title><body>
<canvas id=c width=320 height=200></canvas><pre id=o>…</pre><script>
let quadri = 0, t0 = performance.now(), primo = null, ultimo = null;
const g = document.getElementById('c').getContext('2d');
function passo(t) {
  quadri++; if (primo === null) primo = t; ultimo = t;
  g.fillStyle = (quadri % 2) ? '#000' : '#fff'; g.fillRect(0, 0, 320, 200);
  if (performance.now() - t0 < 3000) requestAnimationFrame(passo);
  else fine();
}
function gpu() { try {
    const c = document.createElement('canvas');
    const x = c.getContext('webgl2') || c.getContext('webgl');
    if (!x) return 'niente webgl';
    const d = x.getExtension('WEBGL_debug_renderer_info');
    return d ? x.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'webgl senza nome';
  } catch (e) { return 'errore ' + e; } }
async function fine() {
  const corpo = JSON.stringify({quadri, durata_ms: Math.round(performance.now() - t0),
      primo, ultimo, visibilita: document.visibilityState, gpu: gpu()});
  document.getElementById('o').textContent = corpo;
  await fetch('/esito', {method: 'POST', body: corpo});
}
requestAnimationFrame(passo);
// ⛔ Il controllo NEGATIVO del banco stesso: se rAF non parte affatto, senza
//    questa rete la pagina tacerebbe e «zero quadri» e «pagina morta»
//    avrebbero lo stesso aspetto.
setTimeout(() => { if (quadri === 0) fine(); }, 6000);
</script></body>"""

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


def giro(con_gpu, n):
    ric.pop("d", None)
    prof = os.path.join(BASE, "p%d" % n)
    shutil.rmtree(prof, ignore_errors=True); os.makedirs(prof)
    porta, schermo = 8860 + n, ":%d" % (60 + n)
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", porta), S)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    x = subprocess.Popen(["Xvfb", schermo, "-screen", "0", "1280x1024x24"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    amb = dict(os.environ); amb["DISPLAY"] = schermo; amb.pop("WAYLAND_DISPLAY", None)
    f = ["google-chrome", "--user-data-dir=" + prof, "--no-first-run",
         "--no-default-browser-check", "--disable-sync",
         "--window-size=800,600", "http://127.0.0.1:%d/" % porta]
    if con_gpu == "headless":
        f.insert(1, "--headless=new")
    elif not con_gpu:
        f.insert(1, "--disable-gpu")
    b = subprocess.Popen(f, env=amb, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    fine = time.time() + 60
    while time.time() < fine and "d" not in ric:
        time.sleep(0.3)
    b.terminate()
    try: b.wait(timeout=10)
    except subprocess.TimeoutExpired: b.kill()
    x.terminate(); srv.shutdown(); srv.server_close()
    shutil.rmtree(prof, ignore_errors=True)
    return ric.get("d", {"errore": "la pagina non ha rimandato niente in 60 s"})


if __name__ == "__main__":
    os.makedirs(BASE, exist_ok=True)
    with open("/proc/loadavg") as fh:
        carico = fh.read().split()[:3]
    print("== LA SCENA: CHUWI, Xvfb, Chrome 151, carico %s" % " ".join(carico))
    tutti = []
    for modo, con in (("CON la GPU", True), ("con --disable-gpu", False),
                      ("--headless=new", "headless")):
        print("\n== %s" % modo)
        for n in range(3):
            d = giro(con, n + {True: 0, False: 3, "headless": 6}[con])
            tutti.append({"modo": modo, **d})
            if "errore" in d:
                print("   giro %d ⛔ %s" % (n + 1, d["errore"])); continue
            print("   giro %d — %4d quadri in %d ms · visibilita' %s · gpu: %s"
                  % (n + 1, d["quadri"], d["durata_ms"], d["visibilita"], d["gpu"]))
    with open(os.path.join(BASE, "esiti.json"), "w") as fh:
        json.dump({"carico": carico, "giri": tutti}, fh, indent=1)
