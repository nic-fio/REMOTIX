#!/usr/bin/env python3
# ⛔⛔ LA PROVA CHE CONTA — non «il browser dice di saper decodificare», ma
#     «il browser HA DECODIFICATO, e i fotogrammi si contano».
#
# ⚠ `isConfigSupported` e' una DICHIARAZIONE.  Qui si dipinge davvero: si
#   suona un file prodotto dal codificatore HARDWARE del server, e si legge
#   `getVideoPlaybackQuality().totalVideoFrames`.  ⛔ Un motore che dice si'
#   e poi consegna 0 fotogrammi ha lo stesso aspetto di uno che funziona,
#   finche' non si contano.
#
# ⭐ E la scena e' la stessa del banco `03-b17-ritardo.py` (Xvfb, Chrome 151),
#   con UNA differenza dichiarata: la bandiera `--disable-gpu` si mette o si
#   toglie da riga di comando, perche' e' quella la variabile sotto esame.
#
# uso:  python3 sonda-dipinge.py [con-gpu|senza-gpu] [quanti_giri]
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
FILE = [("prova-hevc.mp4",     'video/mp4; codecs="hev1.2.4.L120"',  "HEVC Main10, hevc_vaapi"),
        ("prova-vp9-10b.webm", 'video/webm; codecs="vp09.02.41.10"', "VP9 prof.2 10 bit, vp9_vaapi"),
        ("prova-h264.mp4",     'video/mp4; codecs="avc1.640028"',    "H.264 high, h264_vaapi")]

PAGINA = """<!doctype html><meta charset=utf-8><title>dipinge</title><body>
<pre id=o>in corso…</pre><script>
const FILE = %s;
const attesa = (ms) => new Promise(r => setTimeout(r, ms));
(async () => {
  const gpu = (() => { try {
      const c = document.createElement('canvas');
      const g = c.getContext('webgl2') || c.getContext('webgl');
      if (!g) return 'niente webgl';
      const d = g.getExtension('WEBGL_debug_renderer_info');
      return d ? g.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'webgl senza nome';
    } catch (e) { return 'errore: ' + e; } })();
  const esiti = [];
  for (const [nome, tipo, nota] of FILE) {
    const r = {nome, nota};
    try {
      const i = await navigator.mediaCapabilities.decodingInfo({
          type: 'file', video: {contentType: tipo, width: 1920, height: 1080,
                                bitrate: 20000000, framerate: 60}});
      r.dichiara = {supported: i.supported, smooth: i.smooth,
                    powerEfficient: i.powerEfficient};
    } catch (e) { r.dichiara = 'eccezione: ' + e.message; }

    const v = document.createElement('video');
    v.muted = true; v.playsInline = true; v.src = '/' + nome;
    document.body.appendChild(v);
    const errore = new Promise(res => { v.onerror = () => res('errore media ' +
        (v.error ? v.error.code + ' ' + v.error.message : '?')); });
    try {
      await Promise.race([v.play().then(() => 'suona'), errore, attesa(15000).then(() => 'scaduto')]);
      await attesa(4000);
      const q = v.getVideoPlaybackQuality ? v.getVideoPlaybackQuality() : {};
      r.dipinto = {larghezza: v.videoWidth, altezza: v.videoHeight,
                   secondi: Number(v.currentTime.toFixed(2)),
                   fotogrammi: q.totalVideoFrames, buttati: q.droppedVideoFrames,
                   errore: v.error ? v.error.code + ' ' + v.error.message : null};
    } catch (e) { r.dipinto = 'eccezione: ' + e.message; }
    v.pause(); v.remove();
    esiti.push(r);
  }
  const corpo = JSON.stringify({gpu, esiti});
  document.getElementById('o').textContent = corpo;
  await fetch('/esito', {method: 'POST', body: corpo});
})();
</script></body>
""" % json.dumps(FILE)

ricevuto = {}


class Servo(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=BASE, **k)

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == "/":
            b = PAGINA.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
        else:
            super().do_GET()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        ricevuto["dati"] = json.loads(self.rfile.read(n))
        self.send_response(204)
        self.end_headers()


def amb(schermo):
    e = dict(os.environ)
    e["DISPLAY"] = schermo
    e.pop("WAYLAND_DISPLAY", None)
    return e


def un_giro(con_gpu, n, porta, schermo):
    ricevuto.pop("dati", None)
    profilo = os.path.join(BASE, "prof-dip-%d" % n)
    shutil.rmtree(profilo, ignore_errors=True)
    os.makedirs(profilo)

    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", porta), Servo)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    x = subprocess.Popen(["Xvfb", schermo, "-screen", "0", "1280x1024x24"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    if subprocess.run(["xdpyinfo"], env=amb(schermo),
                      capture_output=True).returncode != 0:
        x.terminate(); srv.shutdown()
        return {"errore": "Xvfb non ha risposto a xdpyinfo"}

    flag = ["google-chrome", "--user-data-dir=" + profilo, "--no-first-run",
            "--no-default-browser-check", "--disable-sync", "--autoplay-policy=no-user-gesture-required",
            "--window-size=1280,900", "--window-position=0,0",
            "http://127.0.0.1:%d/" % porta]
    if not con_gpu:
        flag.insert(1, "--disable-gpu")
    b = subprocess.Popen(flag, env=amb(schermo),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    fine = time.time() + 120
    while time.time() < fine and "dati" not in ricevuto:
        time.sleep(0.5)
    b.terminate()
    try:
        b.wait(timeout=10)
    except subprocess.TimeoutExpired:
        b.kill()
    x.terminate()
    srv.shutdown()
    srv.server_close()
    shutil.rmtree(profilo, ignore_errors=True)
    return ricevuto.get("dati", {"errore": "la pagina non ha rimandato niente in 120 s"})


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "con-gpu"
    giri = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    con_gpu = (modo == "con-gpu")
    print("== LA SCENA ==")
    print("   Xvfb, Chrome 151, %s   ·   %d giri"
          % ("SENZA la bandiera --disable-gpu" if con_gpu
             else "CON --disable-gpu (come il banco)", giri))
    tutti = []
    for n in range(giri):
        d = un_giro(con_gpu, n, 8880 + n, ":%d" % (90 + n))
        tutti.append(d)
        if "errore" in d:
            print("   giro %d ⛔ %s" % (n + 1, d["errore"]))
            continue
        print("   giro %d — gpu: %s" % (n + 1, d["gpu"]))
        for e in d["esiti"]:
            di = e.get("dichiara", {})
            dp = e.get("dipinto", {})
            if not isinstance(dp, dict):
                print("      %-28s ⛔ %s" % (e["nota"], dp))
                continue
            fo = dp.get("fotogrammi")
            ok = isinstance(fo, int) and fo > 0
            print("      %-28s %s  dichiara(sup=%s eff=%s)  →  %sx%s  "
                  "%s fotogrammi  %s buttati  %ss  %s"
                  % (e["nota"], "⭐ DIPINGE" if ok else "⛔ ZERO   ",
                     di.get("supported"), di.get("powerEfficient"),
                     dp.get("larghezza"), dp.get("altezza"), fo,
                     dp.get("buttati"), dp.get("secondi"),
                     dp.get("errore") or ""))
    with open(os.path.join(BASE, "dipinge-%s.json" % modo), "w") as f:
        json.dump(tutti, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
