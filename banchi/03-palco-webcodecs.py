#!/usr/bin/env python3
# ⛔⛔ LA PROVA CHE IL PRODOTTO USA DAVVERO — non `<video>`, ma **WebCodecs
#     `VideoDecoder`**.  E non «dice di sapere», ma «HA DECODIFICATO, e i
#     `VideoFrame` che escono si CONTANO».
#
# ⚠ Il 13 agosto sera si e' misurato che Chrome DIPINGE HEVC Main10 (119
#   fotogrammi su 120, 5 giri su 5, `powerEfficient: true`) — ma per la strada
#   `<video>`.  Il prodotto decodifica con `VideoDecoder`.  Questa e' un'altra
#   strada, un altro pezzo di Chrome, e il si' dell'una NON e' il si' dell'altra.
#
# ⭐ LA DIFFICOLTA' VERA E' SPEZZARE IL FLUSSO IN `EncodedVideoChunk`, e uno
#   spezzatore sbagliato consegna ZERO fotogrammi ESATTAMENTE COME un codec non
#   supportato.  ⇒ Percio' ogni strada porta con se' il suo CONTROLLO POSITIVO,
#   su un codec che funziona di sicuro:
#
#     strada «Annex-B, description assente»   → controllo: H.264 Annex-B
#     strada «description = hvcC/avcC»        → controllo: H.264 avcC
#     harness del conteggio in se'            → controllo: VP9 in IVF
#
#   Se il controllo della STESSA strada e' rosso, il «no» su HEVC di quella
#   strada NON VALE NIENTE, e il banco lo dichiara uscendo 6 (BANCO CIECO).
#
# ⛔ CODICI D'USCITA — il rosso sta QUI, non nella prosa:
#     0  tutti i verdetti attesi
#     2  ⛔ ROSSO: un verdetto e' diverso dall'atteso (questo e' un RISULTATO)
#     3  palco non montato (Xvfb/xdpyinfo)      — «non ho potuto guardare»
#     4  la pagina non ha rimandato niente      — «non ho potuto guardare»
#     5  preparazione fallita (ffmpeg, file, disco) — «non ho potuto guardare»
#     6  ⛔ BANCO CIECO: un CONTROLLO POSITIVO e' rosso ⇒ nessun «no» vale
#     7  guasto imprevisto del banco (eccezione catturata)
#     1  ⚠ RISERVATO: Python che muore da solo.  ⛔ Non e' mai un caso rosso.
#
# uso:  python3 03-palco-webcodecs.py [con-gpu|senza-gpu] [giri] [chrome|firefox]
import http.server
import json
import os
import shutil
import socket
import socketserver
import struct
import subprocess
import sys
import threading
import time

QUI = os.path.dirname(os.path.abspath(__file__))
SORGENTI = "/tmp/sonda-vp9"          # ⚠ e' anche `~/.cache/sonda-vp9`: vedi NOTA-DISCO
ESITI = os.path.join(QUI, "03-palco-esiti.jsonl")

# ⛔ NOTA-DISCO — `~/.cache` su CHUWI e' un COLLEGAMENTO a `/tmp`, che e' una
#    tmpfs da 3,8 G al 98 %.  «Metti i profili sotto ~/.cache» NON sposta
#    niente.  I profili vanno su /dev/sda2, cioe' accanto al banco.
PROFILI = os.path.join(QUI, "03-palco-profili")

PORTA_PRIMA = 8890                   # perimetro: 8890-8899
SCHERMO_PRIMO = 95                   # perimetro: :95 in su
PORTE_PROTETTE = (7448, 7501, 7561)  # ⛔ mai toccate


# ─────────────────────────────────────────────────────────────────────────────
# GLI SPEZZATORI.  Ognuno ritorna [(inizio, fine, e_chiave)] sul blob servito.
# ─────────────────────────────────────────────────────────────────────────────
def nal_annexb(d):
    """Confini dei NAL Annex-B: [(inizio_startcode, inizio_payload, fine)]."""
    inizi = []
    i = 0
    while True:
        j = d.find(b"\x00\x00\x01", i)
        if j < 0:
            break
        inizi.append((j - 1 if j > 0 and d[j - 1] == 0 else j, j + 3))
        i = j + 3
    return [(sc, p, inizi[k + 1][0] if k + 1 < len(inizi) else len(d))
            for k, (sc, p) in enumerate(inizi)]


def spezza_annexb(d, hevc):
    """Spezza sulle UNITA' DI ACCESSO, non sui NAL.

    ⚠ Un `EncodedVideoChunk` = un FOTOGRAMMA = tutti i NAL di un'unita' di
      accesso.  Spezzare per NAL da' 4-5 volte troppi pezzi e il decodificatore
      non ne fa niente.  Il confine e' il primo NAL VCL del fotogramma:
        HEVC  first_slice_segment_in_pic_flag  = primo bit dopo i 2 di header
        H.264 first_mb_in_slice == 0           ⇔ ue(v)==0 ⇔ primo bit a 1
      I NAL non-VCL che aprono (VPS/SPS/PPS/AUD/SEI) vanno CON il fotogramma
      che segue, non con quello che li precede.
    """
    aus, ini, fine, chiave, visto_vcl = [], None, None, False, False
    for (sc, p, f) in nal_annexb(d):
        b0 = d[p]
        if hevc:
            t = (b0 >> 1) & 0x3F
            vcl, irap = t <= 31, 16 <= t <= 21
            primo = bool(d[p + 2] & 0x80) if vcl and p + 2 < len(d) else False
            apre = t in (32, 33, 34, 35, 39)      # VPS SPS PPS AUD PREFIX_SEI
        else:
            t = b0 & 0x1F
            vcl, irap = 1 <= t <= 5, t == 5
            primo = bool(d[p + 1] & 0x80) if vcl and p + 1 < len(d) else False
            apre = t in (6, 7, 8, 9)              # SEI SPS PPS AUD

        nuovo = (visto_vcl and primo) if vcl else (apre and visto_vcl)
        if nuovo or ini is None:
            if ini is not None:
                aus.append((ini, fine, chiave))
            ini, chiave, visto_vcl = sc, False, False
        fine = f
        if vcl:
            visto_vcl = True
            chiave = chiave or irap
    if ini is not None:
        aus.append((ini, fine, chiave))
    return aus


def spezza_ivf(d):
    """IVF: 32 byte d'intestazione + 12 byte per fotogramma.  Banalissimo — ed
    e' APPOSTA: e' il controllo dell'harness, non dello spezzatore."""
    if d[:4] != b"DKIF":
        raise ValueError("non e' IVF (manca DKIF)")
    i = struct.unpack_from("<H", d, 6)[0]
    aus = []
    while i + 12 <= len(d):
        n = struct.unpack_from("<I", d, i)[0]
        i += 12
        if i + n > len(d):
            break
        aus.append((i, i + n, not aus))
        i += n
    return aus


# ─────────────────────────────────────────────────────────────────────────────
# IL DEMUX MP4 MINIMO — serve `hvcC`/`avcC` e i campioni lunghezza-prefissati.
# ─────────────────────────────────────────────────────────────────────────────
def _scatole(d, ini, fine):
    i = ini
    while i + 8 <= fine:
        n = struct.unpack_from(">I", d, i)[0]
        t, c = d[i + 4:i + 8], i + 8
        if n == 1:
            n, c = struct.unpack_from(">Q", d, i + 8)[0], i + 16
        elif n == 0:
            n = fine - i
        if n < 8:
            break
        yield t, c, i + n
        i += n


def _trova(d, ini, fine, strada):
    for t, c, f in _scatole(d, ini, fine):
        if t != strada[0]:
            continue
        if len(strada) == 1:
            return c, f
        if t == b"stsd":
            c += 8
        elif t in (b"hvc1", b"hev1", b"avc1", b"avc3"):
            c += 78
        r = _trova(d, c, f, strada[1:])
        if r:
            return r
    return None


def demux_mp4(d):
    """Ritorna (description, [(inizio, fine, e_chiave)]) dal file mp4."""
    conf = None
    for nome in (b"hvcC", b"avcC"):
        for voce in (b"hvc1", b"hev1", b"avc1", b"avc3"):
            r = _trova(d, 0, len(d), [b"moov", b"trak", b"mdia", b"minf",
                                      b"stbl", b"stsd", voce, nome])
            if r:
                conf = d[r[0]:r[1]]
                break
        if conf:
            break
    if conf is None:
        raise ValueError("ne' hvcC ne' avcC nel file")

    stbl = _trova(d, 0, len(d), [b"moov", b"trak", b"mdia", b"minf", b"stbl"])
    tab = {t: (c, f) for t, c, f in _scatole(d, *stbl)}

    c = tab[b"stsz"][0]
    unif, cnt = struct.unpack_from(">II", d, c + 4)
    misure = [unif] * cnt if unif else list(
        struct.unpack_from(">%dI" % cnt, d, c + 12))

    if b"stco" in tab:
        c = tab[b"stco"][0]
        k = struct.unpack_from(">I", d, c + 4)[0]
        blocchi = struct.unpack_from(">%dI" % k, d, c + 8)
    else:
        c = tab[b"co64"][0]
        k = struct.unpack_from(">I", d, c + 4)[0]
        blocchi = struct.unpack_from(">%dQ" % k, d, c + 8)

    c = tab[b"stsc"][0]
    k = struct.unpack_from(">I", d, c + 4)[0]
    stsc = [struct.unpack_from(">III", d, c + 8 + 12 * i) for i in range(k)]

    sync = None
    if b"stss" in tab:
        c = tab[b"stss"][0]
        k = struct.unpack_from(">I", d, c + 4)[0]
        sync = set(struct.unpack_from(">%dI" % k, d, c + 8))

    camp, si = [], 0
    for gi, (primo, per_blocco, _x) in enumerate(stsc):
        ultimo = stsc[gi + 1][0] - 1 if gi + 1 < len(stsc) else len(blocchi)
        for b in range(primo, ultimo + 1):
            off = blocchi[b - 1]
            for _ in range(per_blocco):
                if si >= len(misure):
                    break
                camp.append((off, off + misure[si], sync is None or
                             (si + 1) in sync))
                off += misure[si]
                si += 1
    return conf, camp


# ─────────────────────────────────────────────────────────────────────────────
# LE SCENE.  Ognuna dichiara che cosa e' ATTESA di fare, con e senza GPU.
#   atteso: (con_gpu, senza_gpu)   ·   controllo: che strada certifica
# ─────────────────────────────────────────────────────────────────────────────
SCENE = [
    dict(chiave="vp9-ivf", codec="vp09.02.41.10", strada="IVF (nessuna description)",
         fonte="prova-vp9-10b.webm", forma="ivf",
         nota="⭐ CONTROLLO POSITIVO dell'HARNESS — se qui non si contano "
              "fotogrammi, nessun «no» di questo banco vale niente",
         controllo=True, atteso=("si", "si")),
    dict(chiave="av1-ivf", codec="av01.0.08M.08", strada="IVF (nessuna description)",
         fonte="prova-h264.mp4", forma="av1-ivf",
         nota="⭐ CONTROLLO POSITIVO chiesto dal mandato.  ⚠ SCENA DIVERSA "
              "DALLE ALTRE: NON esce dal codificatore hardware del server "
              "(av1_vaapi su questa macchina da' «No usable encoding profile "
              "found», vedi 03-palco-codificatori) — e' un TRANSCODE software "
              "libsvtav1 preset 10 crf 40 dal file h264",
         controllo=True, atteso=("si", "si")),
    dict(chiave="h264-annexb", codec="avc1.640028", strada="Annex-B (description assente)",
         fonte="prova-h264.mp4", forma="annexb-h264",
         nota="⭐ CONTROLLO POSITIVO dello SPEZZATORE ANNEX-B — stesso codice "
              "che spezza HEVC",
         controllo=True, atteso=("si", "si")),
    dict(chiave="h264-avcc", codec="avc1.640028", strada="description = avcC",
         fonte="prova-h264.mp4", forma="mp4",
         nota="⭐ CONTROLLO POSITIVO della strada DESCRIPTION — stesso demux "
              "mp4 che tira fuori hvcC",
         controllo=True, atteso=("si", "si")),
    dict(chiave="hevc-annexb", codec="hev1.2.4.L120", strada="Annex-B (description assente)",
         fonte="prova-hevc.mp4", forma="annexb-hevc",
         nota="⛔ LA DOMANDA — HEVC Main10 da hevc_vaapi, unita' d'accesso",
         controllo=False, atteso=("si", "no")),
    dict(chiave="hevc-hvcc", codec="hvc1.2.4.L120", strada="description = hvcC",
         fonte="prova-hevc.mp4", forma="mp4",
         nota="⛔ LA DOMANDA, seconda strada — campioni lunghezza-prefissati",
         controllo=False, atteso=("si", "no")),
]


def prepara():
    """Deriva i flussi IN MEMORIA.  ⛔ Niente file nuovi: /tmp e' al 98 %."""
    grezzi, blob, indice = {}, {}, {}
    for s in SCENE:
        p = os.path.join(SORGENTI, s["fonte"])
        if not os.path.exists(p):
            raise FileNotFoundError(p)
        if s["fonte"] not in grezzi:
            grezzi[s["fonte"]] = open(p, "rb").read()

        if s["forma"] == "mp4":
            desc, aus = demux_mp4(grezzi[s["fonte"]])
            d = grezzi[s["fonte"]]
        else:
            if s["forma"] == "av1-ivf":
                # ⚠ l'unico flusso RICODIFICATO, e in software: qui non c'e'
                #   av1_vaapi.  La scena lo dichiara, il verdetto no.
                cmd = ["ffmpeg", "-v", "error", "-i", p, "-c:v", "libsvtav1",
                       "-preset", "10", "-crf", "40", "-g", "120",
                       "-f", "ivf", "pipe:1"]
            else:
                fmt = {"ivf": "ivf", "annexb-h264": "h264",
                       "annexb-hevc": "hevc"}[s["forma"]]
                cmd = ["ffmpeg", "-v", "error", "-i", p, "-c", "copy",
                       "-f", fmt, "pipe:1"]
            r = subprocess.run(cmd, capture_output=True)
            if r.returncode != 0 or not r.stdout:
                raise RuntimeError("ffmpeg %s: uscita %d %s"
                                   % (s["forma"], r.returncode, r.stderr[:200]))
            d = r.stdout
            desc = None
            aus = (spezza_annexb(d, s["forma"] == "annexb-hevc")
                   if s["forma"].startswith("annexb") else spezza_ivf(d))

        if not aus:
            raise RuntimeError("%s: zero unita' — spezzatore rotto" % s["chiave"])
        blob[s["chiave"]] = d
        indice[s["chiave"]] = dict(
            codec=s["codec"], strada=s["strada"], nota=s["nota"],
            controllo=s["controllo"], fonte=s["fonte"],
            description=desc.hex() if desc else None,
            byte=len(d),
            pezzi=[[a, b - a, 1 if k else 0] for a, b, k in aus])
    return blob, indice


# ─────────────────────────────────────────────────────────────────────────────
# LA PAGINA.  ⛔ Rimanda gli esiti da sola (POST), niente CDP: cosi' vale
#    uguale per Chrome e per Firefox.  ⛔ Nessun alert/confirm: bloccherebbero.
# ─────────────────────────────────────────────────────────────────────────────
PAGINA = r"""<!doctype html><meta charset=utf-8><title>webcodecs</title><body>
<pre id=o>in corso...</pre><script>
const attesa = ms => new Promise(r => setTimeout(r, ms));
const gpu = (() => { try {
    const c = document.createElement('canvas');
    const g = c.getContext('webgl2') || c.getContext('webgl');
    if (!g) return 'niente webgl';
    const d = g.getExtension('WEBGL_debug_renderer_info');
    return d ? g.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'webgl senza nome';
  } catch (e) { return 'errore: ' + e; } })();

function daEsa(h) {
  const a = new Uint8Array(h.length / 2);
  for (let i = 0; i < a.length; i++) a[i] = parseInt(h.substr(i * 2, 2), 16);
  return a;
}

async function unaScena(chiave, s) {
  const r = {chiave, codec: s.codec, strada: s.strada, controllo: s.controllo,
             pezzi_dati: s.pezzi.length, chiavi: s.pezzi.filter(p => p[2]).length};
  const cfg = {codec: s.codec, codedWidth: 1920, codedHeight: 1080};
  if (s.description) cfg.description = daEsa(s.description);

  try {
    const q = await VideoDecoder.isConfigSupported(cfg);
    r.dichiara = q.supported === true;
  } catch (e) { r.dichiara = 'eccezione: ' + e.name + ' ' + e.message; }

  const buf = await (await fetch('/flusso/' + chiave)).arrayBuffer();
  if (buf.byteLength !== s.byte) { r.errore = 'blob troncato'; return r; }

  let usciti = 0, primo = null, guasto = null;
  const dec = new VideoDecoder({
    output: f => { usciti++;
                   if (!primo) primo = {w: f.codedWidth, h: f.codedHeight,
                                        formato: f.format, ts: f.timestamp};
                   f.close(); },
    error: e => { guasto = guasto || (e.name + ': ' + e.message); }
  });

  const t0 = performance.now();
  try {
    dec.configure(cfg);
    for (let i = 0; i < s.pezzi.length; i++) {
      if (guasto) break;
      const [off, n, k] = s.pezzi[i];
      dec.decode(new EncodedVideoChunk({
          type: k ? 'key' : 'delta', timestamp: Math.round(i * 1e6 / 60),
          duration: Math.round(1e6 / 60), data: new Uint8Array(buf, off, n)}));
      if (i % 24 === 23) await attesa(0);
    }
    if (!guasto) await Promise.race([dec.flush(), attesa(20000)]);
  } catch (e) { guasto = guasto || (e.name + ': ' + e.message); }
  r.ms = Math.round(performance.now() - t0);
  try { if (dec.state !== 'closed') dec.close(); } catch (e) {}

  r.fotogrammi = usciti;
  r.primo = primo;
  r.guasto = guasto;
  r.verdetto = usciti > 0 ? 'si' : 'no';
  return r;
}

(async () => {
  const esiti = [];
  let indice = null;
  try { indice = await (await fetch('/indice.json')).json(); } catch (e) {}
  if (!('VideoDecoder' in window)) {
    esiti.push({chiave: '—', errore: 'VideoDecoder NON ESISTE in questo motore'});
  } else if (indice) {
    for (const chiave of Object.keys(indice)) {
      try { esiti.push(await unaScena(chiave, indice[chiave])); }
      catch (e) { esiti.push({chiave, errore: e.name + ': ' + e.message}); }
    }
  }
  const corpo = JSON.stringify({motore: navigator.userAgent, gpu,
      videodecoder: 'VideoDecoder' in window, esiti});
  document.getElementById('o').textContent = corpo;
  await fetch('/esito', {method: 'POST', body: corpo});
})();
</script></body>
"""


def fai_servo(blob, indice, ricevuto):
    class Servo(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def _manda(self, b, tipo):
            self.send_response(200)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            if self.path == "/":
                self._manda(PAGINA.encode(), "text/html; charset=utf-8")
            elif self.path == "/indice.json":
                self._manda(json.dumps(indice).encode(), "application/json")
            elif self.path.startswith("/flusso/"):
                k = self.path[len("/flusso/"):]
                if k in blob:
                    self._manda(blob[k], "application/octet-stream")
                else:
                    self.send_error(404)
            else:
                self.send_error(404)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            ricevuto["dati"] = json.loads(self.rfile.read(n))
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()

    return Servo


class Multi(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def amb(schermo):
    e = dict(os.environ)
    e["DISPLAY"] = schermo
    e.pop("WAYLAND_DISPLAY", None)
    return e


def porte_protette_vive():
    vive = []
    for p in PORTE_PROTETTE:
        s = socket.socket()
        s.settimeout(0.3)
        if s.connect_ex(("127.0.0.1", p)) == 0:
            vive.append(p)
        s.close()
    return vive


def liberi(percorso):
    st = os.statvfs(percorso)
    return st.f_bavail * st.f_frsize // (1024 * 1024)


def un_giro(blob, indice, con_gpu, n, motore):
    """⛔ Ritorna SEMPRE un dizionario.  Un giro che non ha potuto guardare si
    riconosce dalla chiave `errore`, non da un'eccezione che sale."""
    ricevuto = {}
    porta = PORTA_PRIMA + (n % 10)
    schermo = ":%d" % (SCHERMO_PRIMO + n)
    profilo = os.path.join(PROFILI, "%s-%d" % (motore, n))
    shutil.rmtree(profilo, ignore_errors=True)
    os.makedirs(profilo, exist_ok=True)

    srv = x = b = None
    try:
        srv = Multi(("127.0.0.1", porta), fai_servo(blob, indice, ricevuto))
        threading.Thread(target=srv.serve_forever, daemon=True).start()

        x = subprocess.Popen(["Xvfb", schermo, "-screen", "0", "1280x1024x24"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        if subprocess.run(["xdpyinfo"], env=amb(schermo),
                          capture_output=True).returncode != 0:
            return {"errore": "Xvfb %s non ha risposto a xdpyinfo — non e' "
                              "«tutti no», e' «non ho potuto guardare»" % schermo}

        url = "http://127.0.0.1:%d/" % porta
        if motore == "chrome":
            flag = ["google-chrome", "--user-data-dir=" + profilo,
                    "--no-first-run", "--no-default-browser-check",
                    "--disable-sync", "--window-size=1280,900",
                    "--window-position=0,0", url]
            if not con_gpu:
                flag.insert(1, "--disable-gpu")
        else:
            flag = ["firefox", "--headless", "--profile", profilo, url]
        b = subprocess.Popen(flag, env=amb(schermo),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        fine = time.time() + 180
        while time.time() < fine and "dati" not in ricevuto:
            if b.poll() is not None and "dati" not in ricevuto:
                time.sleep(3)
                break
            time.sleep(0.5)

        if "dati" not in ricevuto:
            # ⚠ GUARDA IL DISCO PRIMA DI CREDERE A UN ERRORE: quando la tmpfs si
            #   riempie, il browser non apre il profilo e accusa la pagina.
            return {"errore": "la pagina non ha rimandato niente in 180 s "
                              "(browser vivo: %s · liberi: /tmp %d M, profili "
                              "%d M)" % (b.poll() is None, liberi("/tmp"),
                                         liberi(PROFILI))}
        d = ricevuto["dati"]
        d["porta"], d["schermo"] = porta, schermo
        return d
    except Exception as e:                                   # noqa: BLE001
        return {"errore": "guasto del banco: %s: %s" % (type(e).__name__, e)}
    finally:
        for p in (b, x):
            if p is None:
                continue
            p.terminate()
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
        if srv is not None:
            srv.shutdown()
            srv.server_close()
        shutil.rmtree(profilo, ignore_errors=True)           # ⚠ libera a fine giro


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "con-gpu"
    giri = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    motore = sys.argv[3] if len(sys.argv) > 3 else "chrome"
    if modo not in ("con-gpu", "senza-gpu"):
        print("⛔ modo: con-gpu | senza-gpu")
        return 5
    con_gpu = (modo == "con-gpu")
    idx = 0 if con_gpu else 1

    prima = porte_protette_vive()
    os.makedirs(PROFILI, exist_ok=True)

    try:
        blob, indice = prepara()
    except Exception as e:                                   # noqa: BLE001
        print("⛔ preparazione fallita — «non ho potuto guardare», non «no»: "
              "%s: %s" % (type(e).__name__, e))
        return 5

    print("== LA SCENA ==")
    print("   macchina: CHUWI   ·   motore: %s   ·   %d giri" % (motore, giri))
    print("   palco:    Xvfb :%d..:%d 1280x1024x24, %s"
          % (SCHERMO_PRIMO, SCHERMO_PRIMO + giri - 1,
             "SENZA la bandiera --disable-gpu" if con_gpu
             else "CON --disable-gpu (⭐ CONTROLLO NEGATIVO)"))
    print("   strada:   WebCodecs VideoDecoder — ⛔ NON `<video>`")
    print("   porte:    %d..%d   ·   protette vive prima: %s"
          % (PORTA_PRIMA, PORTA_PRIMA + giri - 1, prima or "nessuna"))
    print("   disco:    /tmp %d M liberi   ·   profili in %s (%d M liberi)"
          % (liberi("/tmp"), PROFILI, liberi(PROFILI)))
    print("== I FLUSSI, COME SONO STATI SPEZZATI ==")
    for k, v in indice.items():
        print("   %-13s %-15s %-30s %4d pezzi (%d chiave)  %d byte%s"
              % (k, v["codec"], v["strada"], len(v["pezzi"]),
                 sum(p[2] for p in v["pezzi"]), v["byte"],
                 "  description %d B" % (len(v["description"]) // 2)
                 if v["description"] else ""))

    tutti, verdetti = [], {}
    for n in range(giri):
        d = un_giro(blob, indice, con_gpu, n, motore)
        tutti.append(d)
        if "errore" in d:
            print("   giro %d ⛔ %s" % (n + 1, d["errore"]))
            continue
        print("   giro %d — gpu: %s   ·   VideoDecoder: %s"
              % (n + 1, d["gpu"], d.get("videodecoder")))
        for e in d["esiti"]:
            if "errore" in e:
                print("      ⛔ %-13s %s" % (e.get("chiave"), e["errore"]))
                continue
            v = e["verdetto"]
            verdetti.setdefault(e["chiave"], []).append(v)
            p = e.get("primo") or {}
            print("      %s %-13s dichiara=%-5s  %3d/%d fotogrammi  %s  %s ms  %s"
                  % ("⭐ SI" if v == "si" else "   no", e["chiave"],
                     e["dichiara"], e["fotogrammi"], e["pezzi_dati"],
                     "%sx%s %s" % (p.get("w"), p.get("h"), p.get("formato"))
                     if p else "—", e["ms"], e.get("guasto") or ""))

    # ── IL VERDETTO, e il rosso va nel codice d'uscita ────────────────────────
    print("== IL VERDETTO ==")
    buoni = [d for d in tutti if "errore" not in d]
    if not buoni:
        print("   ⛔ nessun giro ha guardato: non e' un «no»")
        return 4

    ciechi, rossi = [], []
    for s in SCENE:
        v = verdetti.get(s["chiave"], [])
        att = s["atteso"][idx]
        stabile = len(set(v)) == 1 and len(v) == len(buoni)
        ottenuto = v[0] if stabile and v else "instabile %s" % v
        ok = (ottenuto == att)
        print("   %-13s atteso=%-3s ottenuto=%-12s  %s%s"
              % (s["chiave"], att, ottenuto,
                 "ok" if ok else "⛔ ROSSO",
                 "   [CONTROLLO POSITIVO]" if s["controllo"] else ""))
        if not ok:
            (ciechi if s["controllo"] else rossi).append(s["chiave"])

    riga = {"banco": "03-palco-webcodecs", "giro": modo, "motore": motore,
            "ora": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "macchina": "CHUWI",
            "giri": giri, "giri_buoni": len(buoni),
            "scena": "Xvfb :%d..:%d 1280x1024x24, %s, %s; strada WebCodecs "
                     "VideoDecoder (NON <video>); flussi da %s derivati IN "
                     "MEMORIA e serviti da 127.0.0.1:%d..%d; esiti rimandati "
                     "dalla pagina, niente CDP"
                     % (SCHERMO_PRIMO, SCHERMO_PRIMO + giri - 1, motore,
                        "senza --disable-gpu" if con_gpu else "CON --disable-gpu",
                        SORGENTI, PORTA_PRIMA, PORTA_PRIMA + giri - 1),
            "gpu_vista_dalla_pagina": buoni[0].get("gpu"),
            "spezzatura": {k: {"pezzi": len(v["pezzi"]),
                               "chiave": sum(p[2] for p in v["pezzi"]),
                               "description": bool(v["description"])}
                           for k, v in indice.items()},
            "verdetti": verdetti,
            # ⚠ per giro, non solo il primo: un numero che non si ripete e' una
            #   variabile non dichiarata, e si vede solo se si scrivono tutti.
            "fotogrammi": {s["chiave"]: [e.get("fotogrammi", e.get("errore"))
                                         for d in buoni for e in d["esiti"]
                                         if e.get("chiave") == s["chiave"]]
                           for s in SCENE},
            "ms": {s["chiave"]: [e.get("ms") for d in buoni for e in d["esiti"]
                                 if e.get("chiave") == s["chiave"]]
                   for s in SCENE},
            "formato_fotogramma": {s["chiave"]: sorted(
                {str((e.get("primo") or {}).get("formato")) + " " +
                 str((e.get("primo") or {}).get("w")) + "x" +
                 str((e.get("primo") or {}).get("h"))
                 for d in buoni for e in d["esiti"]
                 if e.get("chiave") == s["chiave"] and e.get("primo")})
                for s in SCENE},
            "porte_protette_prima": prima, "porte_protette_dopo": porte_protette_vive(),
            "giri_falliti": [d["errore"] for d in tutti if "errore" in d]}

    if ciechi:
        riga["nota"] = ("⛔ BANCO CIECO: il controllo positivo %s e' rosso ⇒ "
                        "nessun «no» di questo giro vale niente" % ciechi)
        uscita = 6
    elif rossi:
        riga["nota"] = "⛔ ROSSO: %s non ha fatto quel che era atteso" % rossi
        uscita = 2
    else:
        riga["nota"] = "⭐ tutti i verdetti attesi, controlli positivi verdi"
        uscita = 0

    with open(ESITI, "a") as f:                              # ⛔ 'a', mai 'w'
        f.write(json.dumps(riga, ensure_ascii=False) + "\n")

    dopo = porte_protette_vive()
    print("   porte protette: prima %s  dopo %s%s"
          % (prima or "nessuna", dopo or "nessuna",
             "   ⛔ CAMBIATE" if prima != dopo else ""))
    print("   %s" % riga["nota"])
    return uscita


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:                                   # noqa: BLE001
        # ⛔ Un'eccezione NON deve uscire 1: 1 e' «Python e' morto da solo» e si
        #   confonde con un caso rosso.  Il guasto del banco esce 7.
        print("⛔ guasto imprevisto del banco: %s: %s" % (type(e).__name__, e))
        sys.exit(7)
