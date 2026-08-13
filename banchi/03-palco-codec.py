#!/usr/bin/env python3
# ⭐ SONDA DEL PALCO — quali codec il browser del banco dice di saper DECODIFICARE.
#
# ⛔ E' una misura di CORRETTEZZA (un si'/no), non di tempo: non serve la
#    finestra esclusiva.  ⚠ Ma la scena si dichiara lo stesso: e' Xvfb, cioe'
#    SENZA GPU — lo stesso palco di `03-b17-ritardo.py`, dove il 13 agosto
#    HEVC ha detto no 5 volte su 5 e AV1 ha detto si'.
#
# ⭐ La forma e' quella gia' usata il 13 per Firefox: **la pagina rimanda gli
#    esiti da sola**, niente CDP.  Cosi' la stessa sonda vale per tutt'e due i
#    motori, e la corsia D non ha bisogno di un attrezzo diverso.
#
# ⛔ HEV1 e AV1 sono dentro APPOSTA: sono i due CONTROLLI.  Se HEVC non torna
#    `false` e AV1 non torna `true`, la sonda non e' confrontabile col 13
#    agosto e nessuna delle altre righe si legge.
import http.server
import json
import os
import shutil
import socketserver
import subprocess
import sys
import threading
import time

BASE = os.path.expanduser("~/.cache/sonda-vp9")
PORTA = 8899
SCHERMO = ":85"

CODEC = [
    ("hev1.1.6.L93",   "HEVC Main    — CONTROLLO, atteso false"),
    ("hev1.2.4.L120",  "HEVC Main10  — CONTROLLO, atteso false"),
    ("av01.0.08M.10",  "AV1 Main 10b — CONTROLLO, atteso true"),
    ("av01.0.08M.08",  "AV1 Main  8b"),
    ("vp09.00.41.08",  "⭐ VP9 profilo 0, 8 bit"),
    ("vp09.02.41.10",  "⭐ VP9 profilo 2, 10 bit"),
    ("vp8",            "VP8"),
    ("avc1.42E01E",    "H.264 baseline"),
    ("avc1.640028",    "H.264 high"),
]

PAGINA = """<!doctype html><meta charset=utf-8><title>sonda</title><body>
<pre id=o>in corso…</pre><script>
const CODEC = %s;
(async () => {
  const esiti = [];
  const gpu = (() => { try {
      const c = document.createElement('canvas');
      const g = c.getContext('webgl2') || c.getContext('webgl');
      if (!g) return 'niente webgl';
      const d = g.getExtension('WEBGL_debug_renderer_info');
      return d ? g.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'webgl senza nome';
    } catch (e) { return 'errore: ' + e; } })();
  if (!('VideoDecoder' in window)) {
    esiti.push({codec: '—', nota: 'VideoDecoder NON ESISTE in questo motore'});
  } else {
    for (const [codec, nota] of CODEC) {
      let r;
      try {
        const s = await VideoDecoder.isConfigSupported(
            {codec, codedWidth: 1920, codedHeight: 1080});
        r = s.supported === true;
      } catch (e) { r = 'eccezione: ' + e.name + ' ' + e.message; }
      esiti.push({codec, nota, supported: r});
    }
  }
  const corpo = JSON.stringify({
      motore: navigator.userAgent, gpu,
      hardwareConcurrency: navigator.hardwareConcurrency,
      crossOriginIsolated: self.crossOriginIsolated, esiti});
  document.getElementById('o').textContent = corpo;
  await fetch('/esito', {method: 'POST', body: corpo});
})();
</script></body>
""" % json.dumps(CODEC)

ricevuto = {}


class Servo(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        b = PAGINA.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        ricevuto["dati"] = json.loads(self.rfile.read(n))
        self.send_response(204)
        self.end_headers()


def amb():
    e = dict(os.environ)
    e["DISPLAY"] = SCHERMO
    e.pop("WAYLAND_DISPLAY", None)
    return e


def main():
    motore = sys.argv[1] if len(sys.argv) > 1 else "chrome"
    os.makedirs(BASE, exist_ok=True)
    profilo = os.path.join(BASE, "profilo-" + motore)
    shutil.rmtree(profilo, ignore_errors=True)
    os.makedirs(profilo)

    srv = socketserver.TCPServer(("127.0.0.1", PORTA), Servo)
    srv.allow_reuse_address = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    x = subprocess.Popen(["Xvfb", SCHERMO, "-screen", "0", "1280x1024x24"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    r = subprocess.run(["xdpyinfo"], env=amb(), capture_output=True, text=True)
    if r.returncode != 0:
        print("⛔ Xvfb non ha risposto a xdpyinfo: non e' «schermo vuoto», "
              "e' «non ho potuto guardare»")
        x.terminate()
        return 3

    if motore == "chrome":
        flag = ["google-chrome", "--user-data-dir=" + profilo,
                "--no-first-run", "--no-default-browser-check", "--disable-sync",
                "--window-size=1280,900", "--window-position=0,0",
                "http://127.0.0.1:%d/" % PORTA]
    else:
        flag = ["firefox", "--headless", "--profile", profilo,
                "http://127.0.0.1:%d/" % PORTA]
    b = subprocess.Popen(flag, env=amb(),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    fine = time.time() + 60
    while time.time() < fine and "dati" not in ricevuto:
        time.sleep(0.5)

    b.terminate()
    try:
        b.wait(timeout=10)
    except subprocess.TimeoutExpired:
        b.kill()
    x.terminate()
    srv.shutdown()

    if "dati" not in ricevuto:
        print("⛔ la pagina non ha rimandato niente in 60 s — NON e' «tutti no»,"
              " e' «non ho potuto guardare»")
        return 4

    d = ricevuto["dati"]
    print("== LA SCENA ==")
    print("   motore:   %s" % d["motore"])
    print("   palco:    Xvfb %s (SENZA GPU)   ·   gpu vista dalla pagina: %s"
          % (SCHERMO, d["gpu"]))
    print("   nuclei:   %s   ·   crossOriginIsolated: %s"
          % (d["hardwareConcurrency"], d["crossOriginIsolated"]))
    print("== GLI ESITI ==")
    for e in d["esiti"]:
        s = e.get("supported")
        segno = "⭐ SI " if s is True else ("   no " if s is False else "⛔ ??? ")
        print("   %s %-16s  %s%s" % (segno, e["codec"], e.get("nota", ""),
                                     "" if isinstance(s, bool) else "  → %s" % s))
    with open(os.path.join(BASE, "esiti-%s.json" % motore), "w") as f:
        json.dump(d, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
