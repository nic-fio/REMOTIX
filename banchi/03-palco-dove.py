# ⛔ SU CHE PALCO GIRA DAVVERO QUEL CHROME? — la pagina lo dice da se'.
import http.server, json, os, shutil, socketserver, subprocess, sys, threading, time
BASE = "/var/tmp/dove-gira"
PAGINA = """<!doctype html><meta charset=utf-8><body><pre id=o>…</pre><script>
(async () => {
  const gpu = (() => { try { const c=document.createElement('canvas');
    const g=c.getContext('webgl'); if(!g) return 'niente webgl';
    const d=g.getExtension('WEBGL_debug_renderer_info');
    return d? g.getParameter(d.UNMASKED_RENDERER_WEBGL):'webgl'; }
    catch(e){ return 'errore'; } })();
  let hevc=false; try { hevc=(await VideoDecoder.isConfigSupported(
      {codec:'hev1.2.4.L120',codedWidth:1920,codedHeight:1080})).supported; } catch(e){}
  const corpo = JSON.stringify({gpu, hevc,
      schermo: screen.width+'x'+screen.height, finestra: innerWidth+'x'+innerHeight});
  document.getElementById('o').textContent = corpo;
  await fetch('/esito',{method:'POST',body:corpo});
})();
</script></body>"""
ric={}
class S(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        b=PAGINA.encode(); self.send_response(200)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        ric["d"]=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.send_response(204); self.end_headers()
def giro(extra, n, schermo):
    ric.pop("d",None)
    prof=os.path.join(BASE,"p%d"%n); shutil.rmtree(prof,ignore_errors=True); os.makedirs(prof)
    porta=8840+n
    socketserver.TCPServer.allow_reuse_address=True
    srv=socketserver.TCPServer(("127.0.0.1",porta),S)
    threading.Thread(target=srv.serve_forever,daemon=True).start()
    x=subprocess.Popen(["Xvfb",schermo,"-screen","0","1280x1024x24"],
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(2)
    amb=dict(os.environ); amb["DISPLAY"]=schermo; amb.pop("WAYLAND_DISPLAY",None)
    b=subprocess.Popen(["google-chrome","--user-data-dir="+prof,"--no-first-run",
        "--no-default-browser-check","--disable-sync","--window-size=900,700"]+extra+
        ["http://127.0.0.1:%d/"%porta], env=amb,
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    fine=time.time()+45
    while time.time()<fine and "d" not in ric: time.sleep(0.3)
    # ⭐ E la controprova che NON passa dalla pagina: chi e' attaccato all'Xvfb?
    cl=subprocess.run(["xlsclients","-display",schermo],capture_output=True,text=True)
    clienti=len([r for r in cl.stdout.splitlines() if r.strip()])
    b.terminate()
    try: b.wait(timeout=8)
    except subprocess.TimeoutExpired: b.kill()
    x.terminate(); srv.shutdown(); srv.server_close(); shutil.rmtree(prof,ignore_errors=True)
    d=ric.get("d",{"errore":"niente"}); d["clienti_sull_xvfb"]=clienti
    return d
os.makedirs(BASE,exist_ok=True)
for nome,extra,n in (("come l'ho lanciato io (nessuna ozone)",[],0),
                     ("--ozone-platform=x11",["--ozone-platform=x11"],1),
                     ("--ozone-platform=wayland",["--ozone-platform=wayland"],2)):
    d=giro(extra,n,":%d"%(40+n))
    print("  %-38s clienti sull'Xvfb: %s · schermo %s · gpu: %s · HEVC: %s"
          % (nome, d.get("clienti_sull_xvfb"), d.get("schermo"), d.get("gpu"), d.get("hevc")))
