#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-lavori — I QUATTRO LAVORI DELL'ATTORE (fase 16, fasi/16-stress-e-capacita.md §5)

Importato da `16-attore.py`; da solo non gira.  Ogni lavoro:

    prepara()       i file nella casa dell'inquilino, PRIMA dell'accesso
    avvia()         l'applicazione DENTRO la sessione, dopo il primo fotogramma
    passo()         un gesto (o una piccola serie) con INPUT VERO dal browser,
                    la sua verifica (§7 «l'input arriva») e la pausa umana
    extra()         i numeri propri del lavoro per la riga di stato

  A navigazione    firefox-esr --kiosk su quattro pagine NOSTRE servite da un
                   servitore python nella scatola (niente internet): testo,
                   immagini che cambiano a ogni carico, una pagina lunga, una
                   tabella.  Le pagine SCRIVONO nel loro quaderno (carica,
                   scroll, clic): la verifica e' il quaderno, la latenza e'
                   l'ora della riga meno l'ora del gesto.
  B file manager   il file manager del desktop su ~/prova16: crea cartelle
                   (Ctrl+Maiusc+N, nome battuto, Invio) in ~/prova16/nuove e le
                   cancella (Ctrl+A, Canc; su LXQt Maiusc+Canc e «y» alla
                   domanda: vedi `piano_cancella`), naviga (Ctrl+L), cambia vista
                   (Ctrl+1/2), apre e chiude finestre (Ctrl+N / Ctrl+W), rotella.
                   Verifica: la cartella c'e' / non c'e' piu' (dal disco, come
                   root); latenza = ctime della cartella meno l'ora dell'Invio.
  C terminale      il terminale del desktop: comandi con uscita battuti dalla
                   tastiera (ls, find, top per qualche secondo e «q», cat di un
                   file lungo, ps, seq…), ognuno con un segno `#kNNN` in coda.
                   Verifica: la riga ESATTA nella storia di bash (PROMPT_COMMAND
                   = history -a) — un carattere perso o cambiato e' KO;
                   latenza = mtime della storia meno l'ora dell'Invio.
  D video 4K       firefox-esr --kiosk su una pagina nostra che fa suonare il
                   video (YouTube con l'API dell'iframe, o un file locale) a
                   tutta finestra; la pagina scrive ogni 5 s tempo, qualita',
                   stato (e per il file: fotogrammi persi dal decodificatore).
                   Verifica: il tempo del video AVANZA.
                   `[M]` 25 set, xfce, un utente: YouTube aqz-KE-bpKQ (BBB 4K
                   60 fps) raggiungibile, hd1080 → hd2160 dopo ~35 s, una
                   pausa di buffer di ~15 s, ~25-31 dipinti/s; il file locale
                   bbb_sunflower_2160p_30fps_normal.mp4 (H.264 High 3840x2160
                   30 fps, /media/REMOTIX/misure/fase16/video/, agganciato in
                   /rete11/.c16-video/) 1 fotogramma perso su 3443 nel player,
                   ~30 dipinti/s, audio suonati = ricevuti.

⛔ Nomi delle applicazioni per desktop: presenti tutti e quattro nelle scatole
   (`command -v`, 25 set 2026); PROVATE dall'attore su xfce (25 set), e su
   lxqt il 27 set: pcmanfm-qt cancella solo con Maiusc+Canc e «y»
   (`piano_cancella`), qterminal apre dash e va lanciato `-e bash` (`APP`).
"""
import json
import os
import re
import time

# ═══════════════════════════════════════════════════════════════════════════
#  LE APPLICAZIONI DI OGNI DESKTOP
# ═══════════════════════════════════════════════════════════════════════════
#  fm:   comando del file manager (con {dir}), nome del processo
#  term: comando del terminale, nome del processo
APP = {
    "gnome": {"fm": ("nautilus --new-window {dir}", "nautilus"),
              "term": ("gnome-terminal --maximize", "gnome-terminal")},
    "kde":   {"fm": ("dolphin --new-window {dir}", "dolphin"),
              "term": ("konsole", "konsole")},
    # ⚠ xfce: `thunar DIR` consegna la finestra al demone «Thunar --daemon» della
    #   sessione ed esce subito ⇒ il processo da guardare e' «Thunar» (`[M]` 25 set)
    "xfce":  {"fm": ("thunar {dir}", "[Tt]hunar"),
              "term": ("xfce4-terminal --maximize", "xfce4-terminal")},
    # ⛔ lxqt: `qterminal` da solo apre DASH, non bash (`[M]` 27 set 2026, intel-b
    #   2K livello 4, utente 3, due volte su due): nelle sessioni SHELL e' assente
    #   per scelta (02-sessione-stato), e qtermwidget 2.1 senza SHELL ripiega su
    #   /bin/sh (nel binario ci sono solo «SHELL» e «/bin/sh», mai «/bin/bash»);
    #   /bin/sh → dash.  Gli altri tre terminali prendono la shell da passwd
    #   (bash).  Con dash il .bashrc non si legge, la storia non si scrive mai,
    #   ogni comando risulta KO e la prima riga «non arriva» ⇒ tre tentativi,
    #   tre finestre col prompt «$ » nudo nella foto, poi «in_attesa» per tutto
    #   il livello: 6 righe di stato su 122 col blocco, e il classificatore
    #   dice NON MISURATO.  ⇒ `-e bash`: «Execute command instead of shell».
    "lxqt":  {"fm": ("pcmanfm-qt {dir}", "pcmanfm-qt"),
              "term": ("qterminal -e bash", "qterminal")},
}

# il passaggio dei file verso la scatola: la cartella dell'ospite montata dentro
PASSAGGIO_OSPITE = os.environ.get("REMOTIX_PASSAGGIO16", "/media/REMOTIX/rete11/.c16-passaggio")
PASSAGGIO_SCATOLA = "/rete11/.c16-passaggio"

PROFILI = {1: "A", 2: "B", 3: "C", 0: "D"}


def profilo_di(n):
    """1,5,9,13 A · 2,6,10,14 B · 3,7,11,15 C · 4,8,12,16 D (§5)."""
    return PROFILI[n % 4]


def browser_di(n):
    """Dispari Firefox, pari Chrome (§4)."""
    return "firefox" if n % 2 else "chrome"


def inquilino_di(n):
    """`c16%03du%d`: lo riconosce lo sgombero (`^c[0-9]+b?u[0-9]+$`)."""
    return "c16%03du%d" % (n, n)


def porta_interna(scatola, n):
    """La porta del servitore delle pagine NELLA scatola (rete dell'ospite):
    una per desktop e utente, fuori dalle porte dei browser (9700+) e della suite."""
    return 17000 + 20 * ("gnome", "kde", "xfce", "lxqt").index(scatola) + n


# ═══════════════════════════════════════════════════════════════════════════
#  IL SERVITORE NELLA SCATOLA (gira come l'inquilino)
# ═══════════════════════════════════════════════════════════════════════════
SERVITORE = r'''
import http.server, os, sys, time
PORTA, RADICE, LOG, VIDEO = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
TIPI = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".svg": "image/svg+xml",
        ".png": "image/png", ".mp4": "video/mp4", ".webm": "video/webm", ".txt": "text/plain"}
class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def _video(self):
        try:
            n = os.path.getsize(VIDEO)
        except OSError:
            self.send_error(404); return
        a, b = 0, n - 1
        rng = self.headers.get("Range", "")
        if rng.startswith("bytes="):
            x, _, y = rng[6:].split(",")[0].partition("-")
            if x: a = int(x)
            if y: b = min(int(y), n - 1)
            if not x and y: a, b = max(0, n - int(y)), n - 1
            self.send_response(206)
            self.send_header("Content-Range", "bytes %d-%d/%d" % (a, b, n))
        else:
            self.send_response(200)
        self.send_header("Content-Type", TIPI.get(os.path.splitext(VIDEO)[1], "video/mp4"))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(b - a + 1)); self.end_headers()
        with open(VIDEO, "rb") as f:
            f.seek(a); resto = b - a + 1
            try:
                while resto > 0:
                    blocco = f.read(min(1 << 20, resto))
                    if not blocco: break
                    self.wfile.write(blocco); resto -= len(blocco)
            except (BrokenPipeError, ConnectionResetError):
                pass
    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/v":
            return self._video()
        nome = os.path.basename(p) or "testo.html"
        f = os.path.join(RADICE, nome)
        try:
            corpo = open(f, "rb").read()
        except OSError:
            self.send_error(404); return
        self.send_response(200)
        self.send_header("Content-Type", TIPI.get(os.path.splitext(nome)[1], "application/octet-stream"))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(corpo))); self.end_headers()
        self.wfile.write(corpo)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        t = self.rfile.read(n).decode("utf-8", "replace").replace("\n", " ")[:600]
        with open(LOG, "a") as f:
            f.write("%.3f %s\n" % (time.time(), t))
        self.send_response(204); self.send_header("Content-Length", "0"); self.end_headers()
http.server.ThreadingHTTPServer.daemon_threads = True
http.server.ThreadingHTTPServer(("127.0.0.1", PORTA), H).serve_forever()
'''

# ═══════════════════════════════════════════════════════════════════════════
#  LE PAGINE DEL LAVORO A (e quella del video)
# ═══════════════════════════════════════════════════════════════════════════
PAGINE_A = ("testo", "immagini", "lunga", "tabella")
COLORI_NAV = ("#c0392b", "#2471a3", "#1e8449", "#b7950b")
NAV_Y = 0.16            # centro dei bottoni, frazione dell'altezza del desktop
NOTA_Y = 0.94           # centro del campo di testo in fondo
PAROLE_NOTA = ("alfa", "beta", "gamma", "delta", "sessione", "desktop", "tastiera", "server",
               "misura", "rete", "fotogramma", "remoto")

_TESTA = r"""<!doctype html><html lang=it><meta charset=utf-8><title>c16 %(nome)s</title>
<style>
 body{margin:0;font:28px/1.5 sans-serif;background:%(fondo)s;color:#222}
 nav{position:fixed;left:0;right:0;top:8vh;height:16vh;display:flex;z-index:9}
 nav a{flex:1;display:flex;align-items:center;justify-content:center;color:#fff;
       font:bold 64px sans-serif;text-decoration:none;border:6px solid #fff}
 nav a.qui{outline:14px solid #000;outline-offset:-20px}
 main{padding:27vh 6vw 10vh 6vw}
 .card{display:inline-block;margin:18px;vertical-align:top}
 table{border-collapse:collapse;width:100%%} td,th{border:1px solid #888;padding:6px 14px}
 tr:nth-child(odd){background:#eef} section{padding:30px;margin:10px 0}
 #nota{position:fixed;left:6vw;width:88vw;bottom:2vh;height:8vh;z-index:9;font:44px monospace;
       background:#fffbe0;border:4px solid #555;box-sizing:border-box}
</style>
<nav>%(nav)s</nav><textarea id=nota spellcheck=false></textarea><main>
"""

_CODA = r"""</main>
<script>
const NOME = %(nome_js)s;
function manda(t){ try { fetch('/log', {method:'POST', body:t, keepalive:true}).catch(()=>{}); } catch(e){} }
function mx(){ return Math.max(0, document.documentElement.scrollHeight - innerHeight); }
addEventListener('load', () => manda('carica ' + NOME + ' ' + Math.round(scrollY) + ' ' + mx()));
let tS = null;
addEventListener('scroll', () => { if (tS) return; tS = setTimeout(() => { tS = null;
  manda('scroll ' + NOME + ' ' + Math.round(scrollY) + ' ' + mx()); }, 150); });
// ⭐ il bottone risponde SUBITO alla pressione (come ogni sito): l'immagine
//   cambia al clic, e il carico della pagina dopo e' dell'applicazione
// il campo di testo: dice il suo valore 300 ms dopo l'ultima battitura.
// ⛔ NON lascia il fuoco da solo (un tempo: 1,5 s dopo l'ultimo tasto — ma sotto
//   carico Marionette/CDP puo' tardare di piu' fra due tasti, e le lettere dopo
//   finivano fuori dal campo: «input perso» falso).  Lo lascia quando l'ATTORE
//   ha finito la frase e preme Esc (PagGiu' e Home devono tornare alla pagina),
//   e lo dice («lascia»).
const nota = document.getElementById('nota');
let tN = null;
nota.addEventListener('input', () => { clearTimeout(tN);
  tN = setTimeout(() => manda('testo ' + NOME + ' ' + nota.value), 300); });
nota.addEventListener('keydown', (e) => { if (e.key === 'Escape') nota.blur(); });
nota.addEventListener('blur', () => manda('lascia ' + NOME));
document.querySelectorAll('nav a').forEach((a) => a.addEventListener('mousedown',
  () => { a.style.filter = 'brightness(1.6)'; }));
addEventListener('click', (e) => { if (e.target.closest('a')) return;
  manda('clic ' + NOME + ' ' + Math.round(e.clientX) + ' ' + Math.round(e.clientY)); });
%(extra)s
</script></html>
"""

_PAROLE = ("la sessione", "il desktop", "una finestra", "il codificatore", "la rete",
           "il fotogramma", "un utente", "la tastiera", "il server", "la scheda grafica",
           "si aggiorna", "arriva", "scorre", "resta ferma", "si ridisegna", "misura",
           "senza fretta", "in 4K", "sul vetro", "dal browser")


def _paragrafi(n, seme):
    import random
    r = random.Random(seme)
    out = []
    for i in range(n):
        frasi = []
        for _j in range(r.randint(3, 7)):
            frasi.append(" ".join(r.choice(_PAROLE) for _k in range(r.randint(6, 14))).capitalize() + ".")
        out.append("<p><b>%d.</b> %s</p>" % (i + 1, " ".join(frasi)))
    return "\n".join(out)


def pagine_a():
    """{nome file: html} — quattro pagine lunghe almeno tre schermi 4K."""
    fondo = {"testo": "#fdfdf6", "immagini": "#20252b", "lunga": "#ffffff", "tabella": "#f6fbff"}
    out = {}
    for nome in PAGINE_A:
        nav = "".join('<a href="%s.html" style="background:%s"%s>%s</a>' % (
            p, COLORI_NAV[i], ' class=qui' if p == nome else "", p.upper())
            for i, p in enumerate(PAGINE_A))
        corpo, extra = "", ""
        if nome == "testo":
            corpo = "<h1>Un testo da leggere</h1>" + _paragrafi(60, 1)
        elif nome == "immagini":
            corpo = "<h1 style=color:#eee>Immagini</h1><div id=g></div>"
            extra = r"""
const g = document.getElementById('g');
for (let i = 0; i < 36; i++) {
  const w = 560, h = 380; let s = '<svg class=card width=' + w + ' height=' + h + '>';
  s += '<rect width=100% height=100% fill="hsl(' + Math.floor(Math.random()*360) + ',60%,35%)"/>';
  for (let k = 0; k < 14; k++) {
    const c = 'hsl(' + Math.floor(Math.random()*360) + ',80%,' + (40+Math.floor(Math.random()*40)) + '%)';
    if (k % 2) s += '<circle cx=' + Math.random()*w + ' cy=' + Math.random()*h + ' r=' + (20+Math.random()*90) + ' fill="' + c + '" opacity=.8 />';
    else s += '<rect x=' + Math.random()*w + ' y=' + Math.random()*h + ' width=' + (30+Math.random()*200) + ' height=' + (20+Math.random()*120) + ' fill="' + c + '" />';
  }
  g.insertAdjacentHTML('beforeend', s + '</svg>');
}"""
        elif nome == "lunga":
            sez = []
            for i in range(400):
                sez.append('<section style="background:hsl(%d,55%%,%d%%)"><h2>Sezione %d</h2>%s</section>'
                           % ((i * 37) % 360, 78 + (i % 3) * 6, i + 1,
                              _paragrafi(1, 100 + i)))
            corpo = "<h1>Una pagina lunga</h1>" + "\n".join(sez)
        elif nome == "tabella":
            righe = ["<tr><th>#</th><th>nome</th><th>valore</th><th>stato</th><th>nota</th></tr>"]
            for i in range(600):
                righe.append("<tr><td>%d</td><td>voce-%04d</td><td>%d,%02d</td><td>%s</td><td>%s</td></tr>"
                             % (i + 1, (i * 7919) % 10000, (i * 37) % 997, i % 100,
                                ("GREEN", "DEGRADED", "FAIL")[i % 3], _PAROLE[i % len(_PAROLE)]))
            corpo = "<h1>Una tabella</h1><table>" + "".join(righe) + "</table>"
        out[nome + ".html"] = (_TESTA % {"nome": nome, "fondo": fondo[nome], "nav": nav} + corpo
                               + _CODA % {"nome_js": json.dumps(nome), "extra": extra})
    out["video.html"] = PAGINA_VIDEO
    return out


PAGINA_VIDEO = r"""<!doctype html><html><meta charset=utf-8><title>c16 video</title>
<style>html,body{margin:0;height:100%;background:#000;overflow:hidden}
#p,video{position:fixed;left:0;top:0;width:100vw;height:100vh;border:0}</style>
<div id=p></div>
<script>
const q = new URLSearchParams(location.search);
const yt = q.get('yt'), fl = q.get('file');
function manda(t){ try { fetch('/log', {method:'POST', body:t, keepalive:true}).catch(()=>{}); } catch(e){} }
manda('carica video ' + (yt ? 'yt ' + yt : 'file'));
if (yt) {
  const tag = document.createElement('script');
  tag.src = 'https://www.youtube.com/iframe_api';
  tag.onerror = () => manda('video errore api-non-caricata');
  document.head.appendChild(tag);
  window.onYouTubeIframeAPIReady = function () {
    window.P = new YT.Player('p', { width: innerWidth, height: innerHeight, videoId: yt,
      host: 'https://www.youtube-nocookie.com',
      playerVars: { autoplay: 1, controls: 0, loop: 1, playlist: yt, rel: 0, iv_load_policy: 3,
                    playsinline: 1, disablekb: 1, fs: 0, vq: 'hd2160', origin: location.origin },
      events: {
        onReady: (e) => { try { e.target.unMute(); e.target.setVolume(70);
                   e.target.setPlaybackQuality('hd2160'); } catch (x) {}
                   e.target.playVideo(); manda('video pronto'); },
        onStateChange: (e) => manda('video stato ' + e.data),
        onPlaybackQualityChange: (e) => manda('video qualita ' + e.data),
        onError: (e) => manda('video errore ' + e.data) } });
  };
  setInterval(() => {
    if (!window.P || !P.getCurrentTime) return;
    let lv = []; try { lv = P.getAvailableQualityLevels() || []; } catch (x) {}
    manda('video yt t=' + P.getCurrentTime().toFixed(2) + ' stato=' + P.getPlayerState()
      + ' q=' + P.getPlaybackQuality() + ' livelli=' + lv.join(',')
      + ' caricato=' + (P.getVideoLoadedFraction() || 0).toFixed(3)
      + ' muto=' + (P.isMuted() ? 1 : 0) + ' vol=' + P.getVolume());
  }, 5000);
} else {
  const v = document.createElement('video');
  v.src = '/v'; v.autoplay = true; v.loop = true; v.controls = false;
  document.body.appendChild(v);
  v.addEventListener('error', () => manda('video errore ' + (v.error ? v.error.code + ' ' + v.error.message : '?')));
  v.addEventListener('playing', () => manda('video stato 1'));
  v.play().catch((e) => manda('video errore play ' + e));
  setInterval(() => {
    const qq = v.getVideoPlaybackQuality ? v.getVideoPlaybackQuality() : {};
    manda('video file t=' + v.currentTime.toFixed(2) + ' stato=' + (v.paused ? 2 : 1)
      + ' q=' + v.videoWidth + 'x' + v.videoHeight + ' persi=' + (qq.droppedVideoFrames || 0)
      + ' totali=' + (qq.totalVideoFrames || 0) + ' muto=' + (v.muted ? 1 : 0));
  }, 5000);
}
</script></html>
"""

PREF_INTERNE = """user_pref("media.autoplay.default", 0);
user_pref("media.autoplay.blocking_policy", 0);
user_pref("app.update.enabled", false);
user_pref("browser.tabs.warnOnClose", false);
user_pref("toolkit.startup.max_resumed_crashes", -1);
user_pref("browser.startup.page", 0);
user_pref("privacy.webrtc.legacyGlobalIndicator", false);
"""

# ═══════════════════════════════════════════════════════════════════════════
#  LE LETTURE PURE (certificate da 16-attore.py --certifica)
# ═══════════════════════════════════════════════════════════════════════════
_RIGA_LOG = re.compile(r"^(\d+\.\d+) (\S+)(?: (.*))?$")


def leggi_quaderno(testo):
    """Le righe del quaderno delle pagine ⇒ [(ora, tipo, [parole])]."""
    out = []
    for r in (testo or "").splitlines():
        m = _RIGA_LOG.match(r.strip())
        if m:
            out.append((float(m.group(1)), m.group(2), (m.group(3) or "").split()))
    return out


def leggi_video(parole):
    """`video yt t=12.3 stato=1 q=hd2160 …` (parole dopo «video») ⇒ dict."""
    d = {"fonte": parole[0] if parole else None}
    for p in parole[1:]:
        k, s, v = p.partition("=")
        if not s:
            continue
        try:
            d[k] = float(v) if k in ("t", "caricato") else (int(v) if v.lstrip("-").isdigit() else v)
        except ValueError:
            d[k] = v
    return d


def frase_nel_campo(e, frase):
    """⭐ Una riga del quaderno «testo <pagina> <valore>» con il valore UGUALE
    alla frase battuta (un carattere perso o fuori dal campo ⇒ no)."""
    return e[1] == "testo" and " ".join(e[2][1:]) == frase


def campo_lascia_da_solo(html):
    """⛔ Il campo della pagina toglie il fuoco da SOLO a tempo (un setTimeout che
    chiama blur)?  Deve essere no: sotto carico le lettere dopo andrebbero perse."""
    return bool(re.search(r"setTimeout\([^;]*\.blur\(\)", html or ""))


def storia_contiene(testo, riga):
    """⭐ La riga battuta c'e' ESATTA nella storia di bash (una riga intera)."""
    return any(r == riga for r in (testo or "").splitlines())


def shell_sotto(ps_testo, proc):
    """⭐ I processi che girano SOTTO il terminale (i figli diretti di ogni
    processo il cui nome combacia con `proc`), da `ps -o pid=,ppid=,comm=`:
    ['bash'], ['dash'], [] se il terminale non c'e' o non ha ancora figli.
    ⚠ `comm` e' tagliato a 15 caratteri («gnome-terminal-server» ⇒
    «gnome-terminal-»): `proc` si cerca dentro, non si confronta intero."""
    righe = []
    for r in (ps_testo or "").splitlines():
        p = r.split(None, 2)
        if len(p) == 3 and p[0].isdigit() and p[1].isdigit():
            righe.append((p[0], p[1], p[2].strip()))
    padri = {pid for pid, _pp, comm in righe if re.search(proc, comm)}
    return sorted({comm for _pid, pp, comm in righe if pp in padri})


def piano_cancella(scatola):
    """⭐ Il gesto con cui si cancella la selezione nel file manager, per desktop:
    (modificatori, tasto, risposta al dialogo, secondi prima della risposta,
    risposta SEMPRE o solo se le cartelle ci sono ancora).

    ⛔ `[M]` 27 set 2026, campagne intel-b 4K e 3K su LXQt: Canc + Invio dopo
       2,5 s NON ha mai avuto effetto (0 su 30 e piu' tentativi, gia' a 2
       utenti).  Le foto (livello-02/utente-02 4K, livello-04/utente-02 3K)
       mostrano la finestra di pcmanfm-qt su «nuove» con «8 item(s) selected»
       (il Ctrl+A e' arrivato), NESSUN dialogo, tutte le cartelle al loro
       posto, e nella casa dell'inquilino non esiste `~/.local/share/Trash`
       ⇒ il «Move to Trash» del Canc non e' mai partito (GLib crea il cestino
       PRIMA di spostare).  Su thunar (xfce) lo stesso Canc passa «con
       conferma», su nautilus e dolphin in ~350 ms senza.
       In pcmanfm-qt 2.1.0 il Canc e' la scorciatoia della QAction «Move to
       Trash» del menu; Maiusc+Canc e' un QShortcut della finestra («Delete»,
       elimina davvero) come il Ctrl+L che funziona, e apre il dialogo «Do you
       want to delete the selected file(s)?» Yes/No con predefinito **No**:
       l'Invio direbbe di no.  ⇒ Su LXQt si fa come un utente che vuole
       eliminare: Maiusc+Canc, e alla domanda si risponde con la lettera «y»
       (QMessageBox accetta la lettera del bottone anche senza Alt).
    Sugli altri desktop resta Canc, e l'Invio a 2,5 s solo se serve (thunar)."""
    if scatola == "lxqt":
        return (["Shift"], "Delete", "y", 1.2, True)
    return ([], "Delete", "Enter", 2.5, False)


def rett_finestra(prima, dopo, soglia=40, fattore=8):
    """⭐ Il riquadro (x0,y0,x1,y1) — pixel della foto — della finestra COMPARSA
    fra due foto PIL della stessa misura, o None.  Colonne e righe «cambiate»
    (almeno 2 punti sopra `soglia` alla scala 1/`fattore`), e la corsa
    contigua PIU' LUNGA per asse: l'orologio del pannello cambia anche lui, ma
    e' una corsa corta."""
    from PIL import ImageChops
    w, h = dopo.size
    a = prima.resize((max(1, w // fattore), max(1, h // fattore))).convert("L")
    b = dopo.resize((max(1, w // fattore), max(1, h // fattore))).convert("L")
    d = ImageChops.difference(a, b).point(lambda v: 255 if v > soglia else 0)
    pw, ph = d.size
    px = list(d.getdata())
    col = [0] * pw
    rig = [0] * ph
    for i, v in enumerate(px):
        if v:
            col[i % pw] += 1
            rig[i // pw] += 1

    def corsa(v):
        meglio, i0 = (0, 0, -1), None
        for i, x in enumerate(v + [0]):
            if x >= 2 and i0 is None:
                i0 = i
            elif x < 2 and i0 is not None:
                if i - i0 > meglio[0]:
                    meglio = (i - i0, i0, i)
                i0 = None
        return meglio
    cx, cy = corsa(col), corsa(rig)
    if cx[0] < pw * 0.08 or cy[0] < ph * 0.08:
        return None
    return (cx[1] * w / float(pw), cy[1] * h / float(ph), cx[2] * w / float(pw), cy[2] * h / float(ph))


# ═══════════════════════════════════════════════════════════════════════════
#  IL LAVORO, LA BASE
# ═══════════════════════════════════════════════════════════════════════════
class Lavoro:
    nome = "?"

    def __init__(self, att):
        self.a = att                      # l'attore: s, sc, chi, ritmo, mani, dorme, verifica
        self.h = "/home/%s" % att.chi
        self.rett = None                  # la finestra dell'applicazione (desktop)
        self.log_da = 0                   # byte gia' letti del quaderno
        self.ultimo_video = {}

    # -- comandi nella scatola ------------------------------------------------
    def dentro(self, riga, secondi=60):
        t0 = time.time()
        r = self.a.sc.dentro(riga, secondi)
        if time.time() - t0 > 3:
            print("   [%02d] ⚠ un comando nella scatola ha preso %.1f s: %s"
                  % (self.a.n, time.time() - t0, riga[:80]), flush=True)
        return r

    def scrivi_file(self, percorso, testo, modo="644"):
        """⚠ Non in base64 sulla riga di comando: una pagina lunga supera il
        limite degli argomenti («Argument list too long»).  ⇒ Il file passa dalla
        cartella dell'ospite montata nella scatola (/media/REMOTIX/rete11 ⇒
        /rete11) e si installa da li'."""
        nome = "%s-%s" % (self.a.chi, os.path.basename(percorso))
        os.makedirs(PASSAGGIO_OSPITE, exist_ok=True)
        with open(os.path.join(PASSAGGIO_OSPITE, nome), "w") as f:
            f.write(testo)
        try:
            return self.dentro("install -D -o %s -g %s -m %s %s/%s %s"
                               % (self.a.chi, self.a.chi, modo, PASSAGGIO_SCATOLA, nome,
                                  percorso), 60)
        finally:
            try:
                os.unlink(os.path.join(PASSAGGIO_OSPITE, nome))
            except OSError:
                pass

    def quaderno_nuovo(self):
        """Le righe nuove del quaderno delle pagine (dal byte gia' letto)."""
        # ⚠ `dentro` toglie gli spazi in fondo (anche l'ultimo a capo): la
        #   sentinella dice dove finisce il file, e si avanza solo sulle righe
        #   intere (`[M]` 25 set: senza, nessuna riga veniva mai letta)
        c, t = self.dentro("tail -c +%d %s/.c16/quaderno.log 2>/dev/null; echo @@FINE"
                           % (self.log_da + 1, self.h), 30)
        if c is None or not t or "@@FINE" not in t:
            return []
        t = t[:t.rfind("@@FINE")]
        testo = t[:t.rfind("\n") + 1] if "\n" in t else ""
        self.log_da += len(testo.encode())
        return leggi_quaderno(testo)

    def servitore(self, video=""):
        porta = self.a.porta_interna
        c, t = self.dentro(
            "h=%(h)s; pkill -u %(c)s -f c16-servitore.py 2>/dev/null; : > $h/.c16/quaderno.log; "
            "chown %(c)s: $h/.c16/quaderno.log; "
            "setsid runuser -u %(c)s -- python3 $h/.c16/c16-servitore.py %(p)d $h/.c16/pagine "
            "$h/.c16/quaderno.log '%(v)s' </dev/null >$h/.c16/servitore.log 2>&1 & "
            "for i in $(seq 1 40); do python3 -c \"import socket; socket.create_connection(('127.0.0.1', %(p)d), 1)\" "
            "2>/dev/null && { echo acceso; exit 0; }; sleep 0.25; done; cat $h/.c16/servitore.log; exit 1"
            % {"h": self.h, "c": self.a.chi, "p": porta, "v": video}, 40)
        self.log_da = 0
        return c == 0, t

    def prepara_pagine(self):
        for nome, html in pagine_a().items():
            self.scrivi_file("%s/.c16/pagine/%s" % (self.h, nome), html)
        self.scrivi_file("%s/.c16/c16-servitore.py" % self.h, SERVITORE)
        self.scrivi_file("%s/.c16/profilo/user.js" % self.h,
                         self.a.preferenze_interne() + PREF_INTERNE, "600")
        self.dentro("chown -R %s: %s/.c16" % (self.a.chi, self.h), 30)

    def firefox_interno(self, url):
        # un tentativo precedente lascerebbe «Firefox is already running»
        self.dentro("pkill -u %s -f firefox-esr 2>/dev/null; sleep 1" % self.a.chi, 30)
        return self.a.s.nella_sessione(
            "firefox-esr --no-remote --new-instance --profile %s/.c16/profilo --kiosk '%s'"
            % (self.h, url), 60)

    def vivo(self, processo):
        c, _t = self.dentro("pgrep -u %s -f %s >/dev/null" % (self.a.chi, processo), 30)
        return c == 0

    def trova_finestra(self, prima, attesa=25):
        """Aspetta che la finestra compaia FERMA (due foto con lo stesso riquadro)
        e torna il riquadro nel desktop, o None."""
        fine = time.time() + attesa
        ultimo = None
        while time.time() < fine:
            self.a.dorme(1.5)
            dopo = self.a.foto_pil()
            if dopo is None or prima is None or dopo.size != prima.size:
                continue
            r = rett_finestra(prima, dopo)
            if r and ultimo and all(abs(x - y) < 20 for x, y in zip(r, ultimo)):
                return self.a.foto_al_desktop(r)
            ultimo = r
        return self.a.foto_al_desktop(ultimo) if ultimo else None

    def punto(self, fx, fy):
        """Un punto della finestra dell'applicazione (o del desktop), frazioni."""
        tl, ta = self.a.desktop
        r = self.rett or (0, 0, tl, ta)
        return r[0] + fx * (r[2] - r[0]), r[1] + fy * (r[3] - r[1])

    def extra(self):
        return {}


# ═══════════════════════════════════════════════════════════════════════════
#  A — NAVIGAZIONE
# ═══════════════════════════════════════════════════════════════════════════
class LavoroA(Lavoro):
    nome = "A"

    def __init__(self, att):
        super().__init__(att)
        self.pagina, self.y, self.max = "testo", 0, 0

    def prepara(self):
        self.prepara_pagine()

    def avvia(self):
        ok, t = self.servitore()
        if not ok:
            return False, "il servitore delle pagine non parte: %s" % t[-200:]
        c, t = self.firefox_interno("http://127.0.0.1:%d/testo.html" % self.a.porta_interna)
        if c != 0:
            return False, "firefox-esr non si lancia: %s" % t[-200:]
        r = self.aspetta(lambda e: e[1] == "carica" and e[2][:1] == ["testo"], 60)
        if not r:
            return False, "la prima pagina non ha detto «carica» in 60 s"
        self.leggi_pos(r)
        return True, "firefox-esr --kiosk sulla pagina «testo» (max scroll %d)" % self.max

    def leggi_pos(self, e):
        try:
            self.pagina, self.y, self.max = e[2][0], int(e[2][1]), int(e[2][2])
        except (IndexError, ValueError):
            pass

    def aspetta(self, cerca, attesa, dopo=0.0):
        """La prima riga del quaderno (dopo l'ora `dopo`) per cui `cerca` e' vero."""
        fine = time.time() + attesa
        while True:
            for e in self.quaderno_nuovo():
                if e[1] in ("carica", "scroll"):
                    self.leggi_pos(e)
                if e[0] >= dopo and cerca(e):
                    return e
            if time.time() >= fine:
                return None
            self.a.dorme(0.4)

    def lascia_il_campo(self):
        """⭐ Finita la frase, l'attore toglie il fuoco al campo: Esc (la pagina
        dice «lascia»); se non lo dice, un clic su un punto vuoto della pagina."""
        t = self.a.mani.premi("Escape")
        if self.aspetta(lambda e: e[1] == "lascia", 5, t - 1):
            return True
        tl, ta = self.a.desktop
        t = self.a.mani.clic(tl * 0.5, ta * 0.6)
        ok = self.aspetta(lambda e: e[1] == "lascia", 5, t - 1) is not None
        if not ok:
            self.a.evento("errore", testo="il campo di testo non lascia il fuoco (Esc e clic)")
        return ok

    def passo(self):
        R, M = self.a.ritmo, self.a.mani
        tl, ta = self.a.desktop
        az = R.scegli(("naviga", "rotella", "clic", "tasto", "scrivi"), (30, 30, 12, 12, 16))
        if az == "naviga":
            altre = [p for p in PAGINE_A if p != self.pagina]
            dove = R.scegli(altre)
            i = PAGINE_A.index(dove)
            t0 = M.clic((i + 0.5) * tl / 4.0, NAV_Y * ta, atteso=True)
            e = self.aspetta(lambda e: e[1] == "carica" and e[2][:1] == [dove], 10, t0)
            self.a.verifica("naviga", e is not None, (e[0] - t0) * 1000 if e else None,
                            dove)
            self.a.dorme(R.pausa_s("leggere"))
        elif az == "rotella":
            giu = self.y < self.max * 0.6
            tacche = R.intero(3, 12)
            y0 = self.y
            t0 = M.rotella(tl * R.uniforme(0.3, 0.7), ta * R.uniforme(0.4, 0.85),
                           tacche * (1 if giu else -1), atteso=True)
            e = self.aspetta(lambda e: e[1] == "scroll" and len(e[2]) > 1
                             and e[2][1].isdigit() and int(e[2][1]) != y0, 8, t0)
            self.a.verifica("rotella", e is not None, (e[0] - t0) * 1000 if e else None,
                            "%s %d tacche" % ("giu" if giu else "su", tacche))
            self.a.dorme(R.pausa_s("breve"))
        elif az == "scrivi":
            # ⭐ battitura a eco immediato in un campo della pagina: il clic
            #   mette il fuoco, Ctrl+A fa sostituire il testo di prima
            M.clic(tl * R.uniforme(0.3, 0.7), NOTA_Y * ta)
            self.a.dorme(R.pausa_s("gesto"))
            M.combo(["Control"], "a")
            frase = " ".join(R.scegli(PAROLE_NOTA) for _ in range(R.intero(2, 5)))
            t0 = M.batti(frase, eco=True)
            e = self.aspetta(lambda e: frase_nel_campo(e, frase), 8, t0 - 30)
            self.a.verifica("scrivi", e is not None, (e[0] - t0) * 1000 if e else None, frase)
            self.lascia_il_campo()
            self.a.dorme(R.pausa_s("breve"))
        elif az == "clic":
            t0 = M.clic(tl * R.uniforme(0.2, 0.8), ta * R.uniforme(0.45, 0.85))
            e = self.aspetta(lambda e: e[1] == "clic", 8, t0)
            self.a.verifica("clic", e is not None, (e[0] - t0) * 1000 if e else None, self.pagina)
            self.a.dorme(R.pausa_s("breve"))
        else:
            tasto = "PageDown" if self.y < self.max * 0.7 else "Home"
            y0 = self.y
            M.muovi(tl * 0.5, ta * 0.6)
            t0 = M.premi(tasto, atteso=True)
            e = self.aspetta(lambda e: e[1] == "scroll" and len(e[2]) > 1
                             and e[2][1].isdigit() and int(e[2][1]) != y0, 8, t0)
            self.a.verifica("tasto", e is not None, (e[0] - t0) * 1000 if e else None, tasto)
            self.a.dorme(R.pausa_s("breve"))


# ═══════════════════════════════════════════════════════════════════════════
#  B — FILE MANAGER
# ═══════════════════════════════════════════════════════════════════════════
class LavoroB(Lavoro):
    nome = "B"

    def __init__(self, att):
        super().__init__(att)
        self.fm, self.proc = APP[att.o.scatola]["fm"]
        self.k = 0
        self.nuove = []
        self.foto_ko = 0                  # le foto scattate a un «cancella» fallito

    def prepara(self):
        p = self.h + "/prova16"
        self.dentro("mkdir -p %(p)s/nuove %(p)s/alfa %(p)s/beta/dentro %(p)s/gamma && "
                    "for i in $(seq 1 30); do echo riga $i > %(p)s/alfa/nota-$i.txt; done && "
                    "for i in $(seq 1 12); do mkdir -p %(p)s/beta/cartella-$i; done && "
                    "seq 1 5000 > %(p)s/gamma/numeri.txt && chown -R %(c)s: %(p)s"
                    % {"p": p, "c": self.a.chi}, 60)

    def avvia(self):
        prima = self.a.foto_pil()
        c, t = self.a.s.nella_sessione(self.fm.format(dir=self.h + "/prova16"), 60)
        if c != 0:
            return False, "%s non si lancia: %s" % (self.proc, t[-200:])
        fine = time.time() + 30
        while time.time() < fine and not self.vivo(self.proc):
            self.a.dorme(0.5)
        if not self.vivo(self.proc):
            return False, "%s non e' vivo dopo 30 s" % self.proc
        self.rett = self.trova_finestra(prima)
        return True, "%s su ~/prova16, finestra %s" % (
            self.proc, [int(x) for x in self.rett] if self.rett else "NON trovata (uso il centro)")

    def vai(self, percorso):
        M, R = self.a.mani, self.a.ritmo
        M.combo(["Control"], "l")
        self.a.dorme(R.pausa_s("gesto"))
        M.combo(["Control"], "a")
        M.batti(percorso, eco=True)
        M.premi("Enter")
        self.a.dorme(0.8 + R.pausa_s("gesto"))

    def fuoco_vista(self):
        """Un clic su un punto VUOTO della vista (in basso a destra)."""
        x, y = self.punto(0.85, 0.88)
        self.a.mani.clic(x, y)
        self.a.dorme(0.3)

    def esiste(self, nome):
        """(c'e', ctime) di ~/prova16/nuove/<nome>."""
        c, t = self.dentro("stat -c %%.3Z %s/prova16/nuove/%s 2>/dev/null" % (self.h, nome), 30)
        if c == 0 and t.strip():
            try:
                return True, float(t.split()[-1])
            except ValueError:
                return True, None
        return False, None

    def passo(self):
        R, M = self.a.ritmo, self.a.mani
        if not self.vivo(self.proc):
            self.a.evento("applicazione", testo="%s non c'e' piu': la rilancio" % self.proc)
            ok, m = self.avvia()
            self.a.evento("applicazione", testo=m, ok=ok)
            self.a.dorme(3)
            return
        az = R.scegli(("crea", "cancella", "naviga", "vista", "finestra", "rotella"),
                      (30, 12 if len(self.nuove) < 3 else 35, 15, 12, 8, 12))
        if az == "crea":
            self.vai(self.h + "/prova16/nuove")
            self.fuoco_vista()
            self.k += 1
            nome = "c16n%d%s" % (self.k, R.cifre(3))
            M.combo(["Control", "Shift"], "N")
            self.a.dorme(1.2 + R.pausa_s("gesto"))
            M.combo(["Control"], "a")
            M.batti(nome, eco=True)
            t0 = M.premi("Enter")
            fine, c, ct = time.time() + 10, False, None
            while time.time() < fine:
                c, ct = self.esiste(nome)
                if c:
                    break
                self.a.dorme(0.4)
            self.a.verifica("crea", c, (ct - t0) * 1000 if (c and ct) else None, nome)
            if c:
                self.nuove.append(nome)
            else:
                M.premi("Escape")           # un dialogo rimasto aperto
        elif az == "cancella":
            self.vai(self.h + "/prova16/nuove")
            self.fuoco_vista()
            M.combo(["Control"], "a")
            self.a.dorme(R.pausa_s("gesto"))
            mod, tasto, risposta, dopo_s, sempre = piano_cancella(self.a.o.scatola)
            t0 = M.combo(mod, tasto) if mod else M.premi(tasto)
            fine = time.time() + 10
            conferma = False
            n = -1
            while time.time() < fine:
                if sempre and not conferma and time.time() > t0 + dopo_s:
                    # ⭐ LXQt: la domanda «delete?» c'e' sempre, e si risponde «y»
                    M.batti(risposta, atteso=False)
                    conferma = True
                _c, t = self.dentro("ls -A %s/prova16/nuove | wc -l" % self.h, 30)
                n = int(t.split()[-1]) if t and t.split()[-1].isdigit() else -1
                if n == 0:
                    break
                if not sempre and not conferma and time.time() > t0 + dopo_s:
                    M.premi(risposta)        # il dialogo di conferma (thunar)
                    conferma = True
                self.a.dorme(0.4)
            gesto = "+".join(mod + [tasto]) + (", " + risposta if conferma else "")
            self.a.verifica("cancella", n == 0, (time.time() - t0) * 1000 if n == 0 else None,
                            "%d cartelle (%s)" % (len(self.nuove), gesto))
            if n == 0:
                self.nuove = []
            else:
                # ⛔ Si GUARDA lo schermo: la foto dice che c'era (dialogo? filtro?
                #   selezione?) — al massimo tre per attore, poi Esc per chiudere
                #   quel che fosse rimasto aperto (dialogo, barra del filtro)
                if self.foto_ko < 3:
                    self.foto_ko += 1
                    self.a.scatta()
                M.premi("Escape")
        elif az == "naviga":
            dove = R.scegli(("alfa", "beta", "beta/dentro", "gamma", ""))
            self.vai(self.h + "/prova16/" + dove)
            self.a.conta("naviga")
        elif az == "vista":
            M.combo(["Control"], R.scegli(("1", "2")))
            self.a.conta("vista")
        elif az == "finestra":
            M.combo(["Control"], "n")
            self.a.dorme(1.5 + R.pausa_s("breve"))
            M.combo(["Control"], "w")
            self.a.conta("finestra")
        else:
            x, y = self.punto(R.uniforme(0.4, 0.7), R.uniforme(0.4, 0.7))
            M.rotella(x, y, R.intero(2, 8) * R.scegli((1, -1)))
            self.a.conta("rotella")
        self.a.dorme(R.pausa_s("breve"))


# ═══════════════════════════════════════════════════════════════════════════
#  C — TERMINALE
# ═══════════════════════════════════════════════════════════════════════════
COMANDI_C = (
    ("ls -la ~/prova16", 20),
    ("ls -R /usr/share/doc | head -n 200", 10),
    ("find /usr/share -name '*.png' | head -n 60", 12),
    ("find ~ -maxdepth 3 -type f | wc -l", 6),
    ("top", 12),
    ("cat ~/prova16/lungo.txt", 12),
    ("ps aux | head -n 40", 8),
    ("seq 1 800", 6),
    ("df -h", 6),
    ("uname -a", 4),
    ("clear", 4),
)


class LavoroC(Lavoro):
    nome = "C"

    def __init__(self, att):
        super().__init__(att)
        self.term, self.proc = APP[att.o.scatola]["term"]
        self.k = 0

    def prepara(self):
        h = self.h
        testo = "\n".join("riga %05d · %s" % (i, " ".join(_PAROLE[(i * 7 + j) % len(_PAROLE)]
                                                            for j in range(8)))
                          for i in range(1, 2001))
        self.scrivi_file(h + "/prova16/lungo.txt", testo + "\n")
        self.dentro("printf '\\n# c16: la storia si scrive a ogni comando (verifica dell attore)\\n"
                    "export HISTFILE=~/.c16-storia HISTCONTROL= HISTSIZE=100000 HISTFILESIZE=100000\\n"
                    "PROMPT_COMMAND=\"history -a\"\\n' >> %(h)s/.bashrc; touch %(h)s/.c16-storia; "
                    "chown %(c)s: %(h)s/.bashrc %(h)s/.c16-storia" % {"h": h, "c": self.a.chi}, 30)

    def avvia(self):
        prima = self.a.foto_pil()
        c, t = self.a.s.nella_sessione(self.term, 60)
        if c != 0:
            return False, "%s non si lancia: %s" % (self.proc, t[-200:])
        fine = time.time() + 30
        while time.time() < fine and not self.vivo(self.proc):
            self.a.dorme(0.5)
        if not self.vivo(self.proc):
            return False, "%s non e' vivo dopo 30 s" % self.proc
        self.rett = self.trova_finestra(prima)
        self.a.dorme(2)
        # ⛔ la shell sotto il terminale DEVE essere bash: la verifica e' la storia
        #   di bash (`[M]` 27 set: qterminal apriva dash, vedi APP["lxqt"])
        shell = self.shell()
        if shell and "bash" not in shell:
            return False, "%s con sotto %s e non bash: la storia (~/.c16-storia) non si scriverebbe mai" % (
                self.proc, "/".join(shell))
        # il fuoco nella finestra, e una prima riga che dice che la storia si scrive
        x, y = self.punto(0.5, 0.5)
        self.a.mani.clic(x, y)
        ok = self.comando("echo pronto")
        return ok, "%s, finestra %s, sotto %s, prima riga %s" % (
            self.proc, [int(v) for v in self.rett] if self.rett else "NON trovata (uso il centro)",
            "/".join(shell) if shell else "(nessun figlio)", "arrivata" if ok else "NON arrivata")

    def shell(self):
        """I figli diretti del terminale (la shell), dal `ps` della scatola."""
        c, t = self.dentro("ps -u %s -o pid=,ppid=,comm=" % self.a.chi, 30)
        return shell_sotto(t, self.proc) if c == 0 else []

    def storia(self):
        c, t = self.dentro("stat -c %%.3Y %s/.c16-storia; tail -n 30 %s/.c16-storia"
                           % (self.h, self.h), 30)
        if c != 0 or not t:
            return None, ""
        prima, _, resto = t.partition("\n")
        try:
            return float(prima.strip()), resto
        except ValueError:
            return None, resto

    def comando(self, cmd, durata_top=0.0):
        R, M = self.a.ritmo, self.a.mani
        self.k += 1
        riga = "%s #k%d" % (cmd, self.k)
        M.batti(riga, eco=True)
        self.a.dorme(R.pausa_s("gesto"))
        t0 = M.premi("Enter", atteso=True)
        if durata_top:
            self.a.dorme(durata_top)
            t0 = M.premi("q", atteso=True)
        fine = time.time() + 20
        ok, mt = False, None
        while time.time() < fine:
            mt, st = self.storia()
            if storia_contiene(st, riga):
                ok = True
                break
            self.a.dorme(0.4)
        self.a.verifica("comando", ok, (mt - t0) * 1000 if (ok and mt) else None,
                        cmd.split()[0])
        if not ok:
            M.combo(["Control"], "c")       # una riga sbagliata non resta sul prompt
        return ok

    def passo(self):
        R, M = self.a.ritmo, self.a.mani
        if not self.vivo(self.proc):
            self.a.evento("applicazione", testo="%s non c'e' piu': lo rilancio" % self.proc)
            ok, m = self.avvia()
            self.a.evento("applicazione", testo=m, ok=ok)
            self.a.dorme(3)
            return
        if R.probabile(0.15):
            x, y = self.punto(0.5, R.uniforme(0.3, 0.7))
            M.rotella(x, y, R.intero(3, 10) * R.scegli((1, -1)))
            self.a.conta("rotella")
        else:
            cmd = R.scegli([c for c, _p in COMANDI_C], [p for _c, p in COMANDI_C])
            self.comando(cmd, R.uniforme(3, 8) if cmd == "top" else 0.0)
        self.a.dorme(R.pausa_s("leggere" if R.probabile(0.3) else "breve"))


# ═══════════════════════════════════════════════════════════════════════════
#  D — VIDEO 4K
# ═══════════════════════════════════════════════════════════════════════════
def fonte_video(url):
    """--video ⇒ ('yt', ID) | ('file', percorso) | (None, perche')."""
    u = (url or "").strip()
    m = re.search(r"(?:youtube(?:-nocookie)?\.com/(?:watch\?v=|embed/)|youtu\.be/)([\w-]{11})", u)
    if m:
        return "yt", m.group(1)
    if re.fullmatch(r"[\w-]{11}", u):
        return "yt", u
    if u.startswith("file://"):
        u = u[7:]
    if u.startswith("/"):
        return "file", u
    return None, "fonte video non riconosciuta: %r" % url


RETE11_OSPITE, RETE11_SCATOLA = "/media/REMOTIX/rete11", "/rete11"


def video_nella_scatola(percorso):
    """Il file video visto DALLA scatola.  /rete11/… e' gia' dentro; un file
    dell'ospite sotto /media/REMOTIX (es. misure/fase16/video/) si aggancia
    con un collegamento fisso in /media/REMOTIX/rete11/.c16-video/ (stesso
    disco: niente copia) ⇒ /rete11/.c16-video/<nome>."""
    if percorso.startswith(RETE11_SCATOLA + "/"):
        return percorso, ""
    if percorso.startswith(RETE11_OSPITE + "/"):
        return RETE11_SCATOLA + percorso[len(RETE11_OSPITE):], ""
    if not os.path.isfile(percorso):
        return None, "il file video %s non c'e' sull'ospite" % percorso
    cartella = os.path.join(RETE11_OSPITE, ".c16-video")
    os.makedirs(cartella, exist_ok=True)
    dest = os.path.join(cartella, os.path.basename(percorso))
    try:
        if not (os.path.exists(dest) and os.path.samefile(dest, percorso)):
            tmp = dest + ".%d" % os.getpid()
            os.link(percorso, tmp)
            os.replace(tmp, dest)
    except OSError as e:
        return None, "il file video non si aggancia in %s: %s" % (cartella, e)
    return RETE11_SCATOLA + "/.c16-video/" + os.path.basename(percorso), ""


class LavoroD(Lavoro):
    nome = "D"

    def __init__(self, att):
        super().__init__(att)
        self.tipo, self.fonte = fonte_video(att.o.video)
        self.t_video, self.fermo_da = None, None

    def prepara(self):
        self.prepara_pagine()

    def avvia(self):
        if not self.tipo:
            return False, self.fonte
        video = self.fonte if self.tipo == "file" else ""
        if video:
            video, perche = video_nella_scatola(video)
            if not video:
                return False, perche
            c, _t = self.dentro("test -r %s" % video, 30)
            if c != 0:
                return False, "il file video %s non si legge DENTRO la scatola" % video
        ok, t = self.servitore(video)
        if not ok:
            return False, "il servitore non parte: %s" % t[-200:]
        q = "yt=%s" % self.fonte if self.tipo == "yt" else "file=1"
        c, t = self.firefox_interno("http://127.0.0.1:%d/video.html?%s" % (self.a.porta_interna, q))
        if c != 0:
            return False, "firefox-esr non si lancia: %s" % t[-200:]
        fine = time.time() + 90
        while time.time() < fine:
            self.leggi_video()
            if self.ultimo_video.get("stato") == 1 and (self.ultimo_video.get("t") or 0) > 0:
                return True, "video %s %s in riproduzione: %s" % (self.tipo, self.fonte,
                                                                 self.ultimo_video)
            self.a.dorme(2)
        return False, "il video non e' partito in 90 s: %s" % (self.ultimo_video or "nessuna riga")

    def leggi_video(self):
        for ora, tipo, parole in self.quaderno_nuovo():
            if tipo != "video" or not parole:
                continue
            if parole[0] in ("yt", "file"):
                d = leggi_video(parole)
                d["ora"] = ora
                self.ultimo_video = d
            elif parole[0] in ("errore", "qualita"):
                self.a.evento("video", testo=" ".join(parole))
        return self.ultimo_video

    def passo(self):
        R, M = self.a.ritmo, self.a.mani
        tl, ta = self.a.desktop
        prima = self.ultimo_video.get("t")
        self.a.dorme(R.uniforme(15, 40))
        v = self.leggi_video()
        dopo = v.get("t")
        avanza = prima is not None and dopo is not None and dopo != prima
        self.a.verifica("video_avanza", avanza, None,
                        "t %s→%s q=%s stato=%s" % (prima, dopo, v.get("q"), v.get("stato")))
        if R.probabile(0.3):
            # ⚠ solo un movimento, mai un clic: il clic fermerebbe il video
            M.muovi(tl * R.uniforme(0.3, 0.7), ta * R.uniforme(0.3, 0.7))
            self.a.conta("muovi")

    def extra(self):
        self.leggi_video()
        return {"video": dict(self.ultimo_video)}


LAVORI = {"A": LavoroA, "B": LavoroB, "C": LavoroC, "D": LavoroD}
