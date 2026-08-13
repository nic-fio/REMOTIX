#!/usr/bin/env python3
# ⭐ IL PALCO DELLA CORSIA D — quel che serve a misurare un motore che NON HA CDP.
#
# ⛔ Non e' un banco: e' l'attrezzo comune di `03-ff-decodifica.py` e
#    `03-ff-disegno.py`.  Da solo non misura niente e non giudica niente.
#
# ⭐ La forma e' quella di `banchi/03-palco-codec.py` e `03-palco-dipinge.py`
#    (13 agosto sera): **la pagina rimanda gli esiti da sola** con un POST a un
#    `http.server` locale.  Cosi' lo STESSO attrezzo vale per Chrome e per
#    Firefox, e il numero di Firefox ha il suo gemello di Chrome preso con la
#    stessa mano — che e' l'unica condizione perche' i due si sottraggano.
#
# ⛔⛔ LA PRIMA COSA CHE HO SMENTITO, ED E' UNA PREMESSA DEL MIO MANDATO:
#     «metti i profili sotto ~/.cache» NON mette niente al riparo.
#     `[M]` 13 agosto, 21:10:  ~/.cache -> /tmp  (un collegamento simbolico)
#     ⇒ `~/.cache` **e' la tmpfs**, quella da 3,8 G al 98 % con 93 M liberi.
#     I profili qui vanno su `/var/tmp`, che sta su `/dev/sda2` (178 G liberi).
#     ⚠ E la stessa riga smentisce dove i flussi di prova del 13 sono stati
#     messi (`~/.cache/sonda-vp9`): erano sulla tmpfs anche loro.
#
# ⛔ LE REGOLE DEL PALCO, e sono tutte pagate da qualcun altro:
#   · `LEZIONI.md` §2.0 — un banco che dice «no» scrive CON CHE PALCO l'ha detto
#     ⇒ ogni esito porta accanto: motore, bandiere, gpu vista dalla pagina.
#   · `LEZIONI.md` §1.1 — la scena si dichiara ⇒ ogni esito porta il flusso da
#     cui viene (codificatore, preset, profondita', quanti fotogrammi).
#   · §0-bis del piano — chi misura un TEMPO controlla di essere solo e lo
#     scrive accanto al numero ⇒ `scena_macchina()`, prima e dopo ogni giro.
#   · le porte protette 7448 · 7501 · 7561 si CONTANO prima e dopo, e ⛔ vivono
#     su NIC-OS: contarle su CHUWI e' l'errore gia' fatto una volta.
import json
import os
import shutil
import socketserver
import subprocess
import sys
import threading
import time
import http.server

# ⛔ NON `~/.cache`: quello e' /tmp.  Questo sta su /dev/sda2.
BASE = "/var/tmp/corsia-d"
SERVER = "192.168.0.2"
PORTE_PROTETTE = ("7448", "7501", "7561")

# ⭐ I flussi: 1920×1080, 120 fotogrammi a 60/s, generati con le stesse
#    impostazioni del prodotto dove il prodotto ne ha (`src/codificatore.c`:
#    libsvtav1 preset 10, `pred-struct=1` bassa latenza, 4:2:0).
#    ⚠ La SCENA e' `testsrc2`, cioe' SINTETICA: non e' il desktop vero.
#    ⇒ i millisecondi qui dentro NON si sottraggono dai 74,58 della fase 3;
#      si confrontano solo fra loro, motore contro motore.
FLUSSI = [
    {"nome": "av1-10b.obu", "etichetta": "AV1 Main 10 bit — libsvtav1 preset 10, pred-struct=1",
     "ff": ["-pix_fmt", "yuv420p10le", "-c:v", "libsvtav1", "-preset", "10",
            "-svtav1-params", "pred-struct=1", "-f", "obu"],
     "codec": None},
    {"nome": "av1-8b.obu", "etichetta": "AV1 Main 8 bit — libsvtav1 preset 10, pred-struct=1",
     "ff": ["-pix_fmt", "yuv420p", "-c:v", "libsvtav1", "-preset", "10",
            "-svtav1-params", "pred-struct=1", "-f", "obu"],
     "codec": None},
    # ⛔ `-bf 0` NON e' un dettaglio, ed e' stato PAGATO: col flusso di difetto
    #    di `hevc_vaapi` il modo seriale consegnava **1 fotogramma su 30** e il
    #    modo a raffica 30 su 30.  Non era il decodificatore: erano i fotogrammi
    #    B, che impongono il riordino ⇒ il decodificatore non puo' consegnare il
    #    primo finche' non ha visto i seguenti.  ⚠ E il prodotto lavora a bassa
    #    latenza (AV1 gira con `pred-struct=1`), quindi il flusso senza B e' il
    #    flusso GIUSTO, non una comodita' del banco.
    {"nome": "hevc-10b.h265", "etichetta": "HEVC Main10 — hevc_vaapi renderD128, 20 Mbit/s, -bf 0",
     "ff": ["-vf", "format=p010,hwupload", "-vaapi_device", "/dev/dri/renderD128",
            "-c:v", "hevc_vaapi", "-b:v", "20M", "-bf", "0", "-f", "hevc"],
     "codec": None},
]


# ═══════════════════════════════════════════════════════════════════════════
# §1  LA SCENA DELLA MACCHINA — «ero solo?», misurato e non creduto
# ═══════════════════════════════════════════════════════════════════════════
def _out(cmd, **k):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=25, **k)
        return r.stdout
    except Exception as e:                       # noqa: BLE001
        return "⛔ non ho potuto guardare: %s" % e


def porte_protette():
    """⛔ Si contano su NIC-OS, non su CHUWI: e' li' che ascoltano."""
    s = _out(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", SERVER,
              "ss -ltn"])
    if s.startswith("⛔"):
        return {"errore": s}
    viste = [p for p in PORTE_PROTETTE if (":" + p) in s]
    return {"macchina": SERVER, "viste": viste, "quante": len(viste)}


def scena_macchina(etichetta):
    """⭐ La fotografia che va ACCANTO al numero, non al posto del numero."""
    ps = _out(["ps", "-eo", "comm,pcpu,etimes"])
    righe = ps.splitlines()[1:]

    def conta(*nomi):
        return sum(1 for r in righe if r.split() and r.split()[0] in nomi)

    try:
        carico = os.getloadavg()
    except OSError:
        carico = (-1, -1, -1)
    df = _out(["df", "-P", "/tmp", "/var/tmp"]).splitlines()[1:]
    browser = conta("chrome", "chromium", "firefox", "firefox-bin")
    xvfb = [r.split()[0] for r in righe if r.split() and r.split()[0] == "Xvfb"]
    cpu_altrui = 0.0
    for r in righe:
        c = r.split()
        if len(c) >= 2 and c[0] not in ("python3", "ps", "sh", "bash"):
            try:
                cpu_altrui = max(cpu_altrui, float(c[1]))
            except ValueError:
                pass
    s = {
        "quando": etichetta,
        "ora": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "carico_1_5_15": [round(x, 2) for x in carico],
        "nuclei": os.cpu_count(),
        "browser_vivi": browser,
        "xvfb_vivi": len(xvfb),
        "cpu_massima_di_un_altro_processo": cpu_altrui,
        "disco": [" ".join(r.split()[:6]) for r in df],
    }
    # ⛔ «solo» non e' un'opinione: e' una soglia scritta, e si scrive quale.
    s["sono_solo"] = (browser == 0 and carico[0] < 1.0
                      and cpu_altrui < 40.0)
    s["criterio_di_solitudine"] = ("nessun browser altrui vivo · carico(1m) < 1,0 "
                                   "· nessun processo altrui sopra il 40 %% di CPU "
                                   "(la macchina ha %d nuclei)" % (os.cpu_count() or 0))
    return s


# ═══════════════════════════════════════════════════════════════════════════
# §2  I FLUSSI — generati una volta, con la scena dichiarata accanto
# ═══════════════════════════════════════════════════════════════════════════
def _stringa_codec(percorso):
    """⭐ La stringa di codec si LEGGE dal flusso, non si indovina.

    ⚠ `DECISIONI.md` §1.13: in AV1 il numero nella stringa e' il
      `seq_level_idx`, non «il livello» — 4 vuol dire 3.0.  Qui si mette
      quel che `ffprobe` legge, cioe' l'indice, che e' quel che la stringa
      vuole.
    """
    d = _out(["ffprobe", "-hide_banner", "-loglevel", "error",
              "-select_streams", "v:0", "-show_entries",
              "stream=codec_name,profile,level,width,height,pix_fmt",
              "-of", "json", percorso])
    s = json.loads(d)["streams"][0]
    dieci = "10" in (s.get("pix_fmt") or "")
    if s["codec_name"] == "av1":
        return ("av01.0.%02dM.%s" % (int(s["level"]), "10" if dieci else "08"),
                s)
    if s["codec_name"] == "hevc":
        # hev1.<spazio+profilo>.<compat>.<tier><livello>.<vincoli>
        return ("hev1.%d.4.L%d.B0" % (2 if dieci else 1, int(s["level"])), s)
    raise RuntimeError("codec non previsto: %s" % s["codec_name"])


def prepara_flussi(rifai=False):
    """⛔ Il manifesto degli AU si prende da `ffprobe`, non si parsa a mano.

    ⭐ `ffprobe -show_packets` da' posizione e lunghezza di OGNI unita' di
       accesso nel flusso grezzo ⇒ la pagina puo' tagliare i pezzi esatti
       senza demultiplatore, e ⛔ **il numero di pezzi in ingresso e' noto**:
       un decodificatore che ne consegna meno si vede, invece di sembrare
       piu' veloce (§2.0, la sorella minore del confronto che non era un
       confronto).
    """
    os.makedirs(BASE, exist_ok=True)
    fatti = []
    for f in FLUSSI:
        p = os.path.join(BASE, f["nome"])
        if rifai or not os.path.exists(p):
            cmd = (["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "testsrc2=size=1920x1080:rate=60",
                    "-frames:v", "120"] + f["ff"] + [p])
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0 or not os.path.exists(p):
                raise RuntimeError("⛔ ffmpeg non ha prodotto %s (uscita %d): %s"
                                   % (f["nome"], r.returncode, r.stderr[-400:]))
        pac = _out(["ffprobe", "-hide_banner", "-loglevel", "error",
                    "-show_packets", "-show_entries", "packet=pos,size,flags",
                    "-of", "csv=p=0", p])
        pezzi = []
        for riga in pac.strip().splitlines():
            c = riga.split(",")
            if len(c) < 3:
                continue
            pezzi.append({"pos": int(c[1]), "len": int(c[0]),
                          "chiave": c[2].startswith("K")})
        codec, info = _stringa_codec(p)
        fatti.append({"nome": f["nome"], "etichetta": f["etichetta"],
                      "codec": codec, "pezzi": pezzi,
                      "byte": os.path.getsize(p),
                      "larghezza": info["width"], "altezza": info["height"],
                      "pix_fmt": info["pix_fmt"]})
    return fatti


# ═══════════════════════════════════════════════════════════════════════════
# §3  IL SERVITORE — la pagina, i flussi, e il POST di ritorno
# ═══════════════════════════════════════════════════════════════════════════
class _Servo(http.server.SimpleHTTPRequestHandler):
    pagina = b""
    cassetta = None

    def __init__(self, *a, **k):
        super().__init__(*a, directory=BASE, **k)

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(self.pagina)))
            # ⭐ isolamento: non serve a VideoDecoder, ma non costa e rende
            #    la pagina uguale a quella del prodotto.
            self.send_header("Cross-Origin-Opener-Policy", "same-origin")
            self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
            self.end_headers()
            self.wfile.write(self.pagina)
        else:
            super().do_GET()

    def end_headers(self):
        if self.path not in ("/", "/index.html"):
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        super().end_headers()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        grezzo = self.rfile.read(n)
        self.send_response(204)
        self.end_headers()
        try:
            self.cassetta["dati"] = json.loads(grezzo)
        except json.JSONDecodeError as e:
            self.cassetta["dati"] = {"errore": "JSON rotto dalla pagina: %s" % e,
                                     "grezzo": grezzo[:400].decode("utf-8", "replace")}


def _amb(schermo, moz_log=None):
    e = dict(os.environ)
    if schermo:
        e["DISPLAY"] = schermo
    e.pop("WAYLAND_DISPLAY", None)
    if moz_log:
        e["MOZ_LOG"] = moz_log
    return e


def bandiere(motore, url, profilo, headless, con_gpu):
    """⛔ Le bandiere si RESTITUISCONO, perche' finiscono scritte accanto al
       numero: e' l'intera lezione §2.0."""
    if motore == "chrome":
        f = ["google-chrome", "--user-data-dir=" + profilo, "--no-first-run",
             "--no-default-browser-check", "--disable-sync",
             "--autoplay-policy=no-user-gesture-required",
             "--window-size=1920,1200", "--window-position=0,0"]
        if headless:
            f.append("--headless=new")
        if not con_gpu:
            f.append("--disable-gpu")     # ⛔ la bandiera che ha accecato il 13
        return f + [url]
    f = ["firefox", "--profile", profilo]
    if headless:
        f.append("--headless")
    return f + [url]


def giro(pagina, motore, porta, schermo, headless=True, con_gpu=True,
         attesa_s=300, moz_log=None, xvfb=True):
    """⭐ Un giro solo: accende il palco, serve la pagina, aspetta il POST.

    ⛔ Torna sempre un dizionario: se la pagina non rimanda niente **non e'
       «tutti no», e' «non ho potuto guardare»**, e lo dice con quelle parole.
    """
    cassetta = {}
    profilo = os.path.join(BASE, "prof-%s-%d" % (motore, porta))
    shutil.rmtree(profilo, ignore_errors=True)
    os.makedirs(profilo)
    reg = os.path.join(BASE, "motore-%s-%d.log" % (motore, porta))

    servo = type("Servo", (_Servo,), {"pagina": pagina.encode(),
                                      "cassetta": cassetta})
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", porta), servo)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    x = None
    if xvfb and schermo:
        x = subprocess.Popen(["Xvfb", schermo, "-screen", "0", "1920x1200x24"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        if subprocess.run(["xdpyinfo"], env=_amb(schermo),
                          capture_output=True).returncode != 0:
            x.terminate(); srv.shutdown(); srv.server_close()
            return {"errore": "⛔ Xvfb %s non ha risposto a xdpyinfo: non e' "
                              "«schermo vuoto», e' «non ho potuto guardare»" % schermo}

    url = "http://127.0.0.1:%d/" % porta
    f = bandiere(motore, url, profilo, headless, con_gpu)
    t0 = time.time()
    with open(reg, "wb") as log:
        b = subprocess.Popen(f, env=_amb(schermo if xvfb else None, moz_log),
                             stdout=log, stderr=subprocess.STDOUT)
        fine = time.time() + attesa_s
        while time.time() < fine and "dati" not in cassetta:
            if b.poll() is not None and "dati" not in cassetta:
                time.sleep(1.5)          # ⚠ l'ultimo POST puo' essere in volo
                break
            time.sleep(0.25)
        b.terminate()
        try:
            b.wait(timeout=10)
        except subprocess.TimeoutExpired:
            b.kill()
    if x:
        x.terminate()
    srv.shutdown()
    srv.server_close()
    shutil.rmtree(profilo, ignore_errors=True)   # ⭐ si libera a fine giro

    d = cassetta.get("dati")
    if d is None:
        coda = ""
        try:
            with open(reg, "r", errors="replace") as fh:
                coda = fh.read()[-600:]
        except OSError:
            pass
        return {"errore": "⛔ la pagina non ha rimandato niente in %d s — NON e' "
                          "«tutti no», e' «non ho potuto guardare»" % attesa_s,
                "coda_del_motore": coda}
    d["_palco"] = {"motore": motore, "bandiere": f[:-1], "schermo": schermo,
                   "headless": headless, "con_gpu_chiesta": con_gpu,
                   "xvfb": bool(x), "secondi": round(time.time() - t0, 1),
                   "registro_motore": reg}
    return d


def leggi_registro_motore(percorso, chiavi):
    """⭐ «Non si deduce: si chiede» (§1.6) — qui si chiede a Firefox QUALE
       modulo di decodifica ha scelto, invece di dedurlo dai millisecondi."""
    try:
        with open(percorso, "r", errors="replace") as f:
            t = f.read()
    except OSError:
        return []
    return [r.strip() for r in t.splitlines()
            if any(k.lower() in r.lower() for k in chiavi)]


def dist(v):
    """mediana, p95, minimo, massimo — e ⛔ SEMPRE quanti campioni."""
    v = sorted(x for x in v if isinstance(x, (int, float)))
    if not v:
        return {"n": 0, "nota": "⛔ nessun campione: non e' «zero», e' «non so»"}

    def q(p):
        i = min(len(v) - 1, max(0, int(round(p * (len(v) - 1)))))
        return round(v[i], 3)
    return {"n": len(v), "mediana": q(0.5), "p95": q(0.95),
            "min": round(v[0], 3), "max": round(v[-1], 3),
            "media": round(sum(v) / len(v), 3)}


if __name__ == "__main__":
    print("⛔ Questo non e' un banco: e' il palco comune di `03-ff-decodifica.py`")
    print("   e `03-ff-disegno.py`.  Da solo non misura e non giudica niente.")
    print()
    print("== LA MACCHINA ==")
    print(json.dumps(scena_macchina("controllo a mano"), indent=1, ensure_ascii=False))
    print("== LE PORTE PROTETTE (su %s) ==" % SERVER)
    print(json.dumps(porte_protette(), indent=1, ensure_ascii=False))
    if len(sys.argv) > 1 and sys.argv[1] == "flussi":
        for f in prepara_flussi():
            print("   %-16s %-9s %d pezzi  %d byte  %s"
                  % (f["nome"], f["codec"], len(f["pezzi"]), f["byte"], f["pix_fmt"]))
    sys.exit(0)
