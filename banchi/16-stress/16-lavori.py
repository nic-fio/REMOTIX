#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-lavori — THE ACTOR'S FOUR WORKLOADS (phase 16, fasi/16-stress-e-capacita.md §5)

Imported by `16-attore.py`; it does not run on its own.  Each workload:

    prepara()       the files in the tenant's home, BEFORE the access
    avvia()         the application INSIDE the session, after the first frame
    passo()         one gesture (or a small series) with REAL INPUT from the browser,
                    its check (§7 «the input arrives») and the human pause
    extra()         the workload's own numbers for the status row

  A browsing       firefox-esr --kiosk on four pages of OURS served by a
                   python server in the box (no internet): text,
                   images that change at every load, a long page, a
                   table.  The pages WRITE into their notebook (carica,
                   scroll, clic): the check is the notebook, the latency is
                   the time of the row minus the time of the gesture.
  B file manager   the desktop's file manager on ~/prova16: creates folders
                   (Ctrl+Shift+N, name typed, Enter) in ~/prova16/nuove and
                   deletes them (Ctrl+A, Del; on LXQt Shift+Del and «y» at the
                   question: see `piano_cancella`), navigates (Ctrl+L), changes view
                   (Ctrl+1/2), opens and closes windows (Ctrl+N / Ctrl+W), wheel.
                   Check: the folder is there / is no longer there (from the disk, as
                   root); latency = ctime of the folder minus the time of the Enter.
  C terminal       the desktop's terminal: commands with output typed on the
                   keyboard (ls, find, top for a few seconds and «q», cat of a
                   long file, ps, seq…), each with a mark `#kNNN` at the end.
                   Check: the EXACT line in the bash history (PROMPT_COMMAND
                   = history -a) — a character lost or changed is KO;
                   latency = mtime of the history minus the time of the Enter.
  D 4K video       firefox-esr --kiosk on a page of ours that plays the
                   video (YouTube with the iframe API, or a local file) in a
                   full window; every 5 s the page writes time, quality,
                   state (and for the file: frames dropped by the decoder).
                   Check: the video's time ADVANCES.
                   `[M]` 25 Sep, xfce, one user: YouTube aqz-KE-bpKQ (BBB 4K
                   60 fps) reachable, hd1080 → hd2160 after ~35 s, one
                   buffering pause of ~15 s, ~25-31 painted/s; the local file
                   bbb_sunflower_2160p_30fps_normal.mp4 (H.264 High 3840x2160
                   30 fps, /media/REMOTIX/misure/fase16/video/, hooked in
                   /rete11/.c16-video/) 1 frame dropped out of 3443 in the player,
                   ~30 painted/s, audio played = received.

⛔ Names of the applications per desktop: all four present in the boxes
   (`command -v`, 25 Sep 2026); TRIED by the actor on xfce (25 Sep), and on
   lxqt on 27 Sep: pcmanfm-qt deletes only with Shift+Del and «y»
   (`piano_cancella`), qterminal opens dash and must be launched `-e bash` (`APP`).
"""
import json
import os
import re
import time

# ═══════════════════════════════════════════════════════════════════════════
#  THE APPLICATIONS OF EACH DESKTOP
# ═══════════════════════════════════════════════════════════════════════════
#  fm:   file manager command (with {dir}), process name
#  term: terminal command, process name
APP = {
    "gnome": {"fm": ("nautilus --new-window {dir}", "nautilus"),
              "term": ("gnome-terminal --maximize", "gnome-terminal")},
    "kde":   {"fm": ("dolphin --new-window {dir}", "dolphin"),
              "term": ("konsole", "konsole")},
    # ⚠ xfce: `thunar DIR` hands the window to the session's «Thunar --daemon»
    #   and exits at once ⇒ the process to watch is «Thunar» (`[M]` 25 Sep)
    "xfce":  {"fm": ("thunar {dir}", "[Tt]hunar"),
              "term": ("xfce4-terminal --maximize", "xfce4-terminal")},
    # ⛔ lxqt: `qterminal` on its own opens DASH, not bash (`[M]` 27 Sep 2026, intel-b
    #   2K level 4, user 3, twice out of two): in the sessions SHELL is absent
    #   by choice (02-sessione-stato), and qtermwidget 2.1 without SHELL falls back to
    #   /bin/sh (in the binary there are only «SHELL» and «/bin/sh», never «/bin/bash»);
    #   /bin/sh → dash.  The other three terminals take the shell from passwd
    #   (bash).  With dash the .bashrc is not read, the history is never written,
    #   every command comes out KO and the first line «does not arrive» ⇒ three attempts,
    #   three windows with the bare «$ » prompt in the photo, then «in_attesa» for the whole
    #   level: 6 status rows out of 122 with the block, and the classifier
    #   says NOT MEASURED.  ⇒ `-e bash`: «Execute command instead of shell».
    "lxqt":  {"fm": ("pcmanfm-qt {dir}", "pcmanfm-qt"),
              "term": ("qterminal -e bash", "qterminal")},
}

# the passage of files into the box: the host's folder mounted inside
PASSAGGIO_OSPITE = os.environ.get("REMOTIX_PASSAGGIO16", "/media/REMOTIX/rete11/.c16-passaggio")
PASSAGGIO_SCATOLA = "/rete11/.c16-passaggio"

PROFILI = {1: "A", 2: "B", 3: "C", 0: "D"}


def profilo_di(n):
    """1,5,9,13 A · 2,6,10,14 B · 3,7,11,15 C · 4,8,12,16 D (§5)."""
    return PROFILI[n % 4]


def browser_di(n):
    """Odd Firefox, even Chrome (§4)."""
    return "firefox" if n % 2 else "chrome"


def inquilino_di(n):
    """`c16%03du%d`: the clear-out recognises it (`^c[0-9]+b?u[0-9]+$`)."""
    return "c16%03du%d" % (n, n)


def porta_interna(scatola, n):
    """The port of the page server IN the box (the host's network):
    one per desktop and user, outside the ports of the browsers (9700+) and of the suite."""
    return 17000 + 20 * ("gnome", "kde", "xfce", "lxqt").index(scatola) + n


# ═══════════════════════════════════════════════════════════════════════════
#  THE SERVER IN THE BOX (runs as the tenant)
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
#  THE PAGES OF WORKLOAD A (and the video one)
# ═══════════════════════════════════════════════════════════════════════════
PAGINE_A = ("testo", "immagini", "lunga", "tabella")
COLORI_NAV = ("#c0392b", "#2471a3", "#1e8449", "#b7950b")
NAV_Y = 0.16            # centre of the buttons, fraction of the desktop's height
NOTA_Y = 0.94           # centre of the text field at the bottom
PAROLE_NOTA = ("alpha", "beta", "gamma", "delta", "session", "desktop", "keyboard", "server",
               "measure", "network", "frame", "remote")

_TESTA = r"""<!doctype html><html lang=en><meta charset=utf-8><title>c16 %(nome)s</title>
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
// ⭐ the button answers AT ONCE to the press (like every site): the image
//   changes at the click, and the load of the page after it belongs to the application
// the text field: says its value 300 ms after the last keystroke.
// ⛔ it does NOT leave the focus on its own (it used to: 1.5 s after the last key — but under
//   load Marionette/CDP can be slower than that between two keys, and the letters after
//   ended up outside the field: a false «input lost»).  It leaves it when the ACTOR
//   has finished the sentence and presses Esc (PageDown and Home must go back to the page),
//   and says so («lascia»).
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

_PAROLE = ("the session", "the desktop", "a window", "the encoder", "the network",
           "the frame", "a user", "the keyboard", "the server", "the graphics card",
           "updates", "arrives", "scrolls", "stays still", "redraws", "measures",
           "without hurry", "in 4K", "on the glass", "from the browser")


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
    """{file name: html} — four pages at least three 4K screens long."""
    fondo = {"testo": "#fdfdf6", "immagini": "#20252b", "lunga": "#ffffff", "tabella": "#f6fbff"}
    out = {}
    for nome in PAGINE_A:
        nav = "".join('<a href="%s.html" style="background:%s"%s>%s</a>' % (
            p, COLORI_NAV[i], ' class=qui' if p == nome else "", p.upper())
            for i, p in enumerate(PAGINE_A))
        corpo, extra = "", ""
        if nome == "testo":
            corpo = "<h1>A text to read</h1>" + _paragrafi(60, 1)
        elif nome == "immagini":
            corpo = "<h1 style=color:#eee>Images</h1><div id=g></div>"
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
                sez.append('<section style="background:hsl(%d,55%%,%d%%)"><h2>Section %d</h2>%s</section>'
                           % ((i * 37) % 360, 78 + (i % 3) * 6, i + 1,
                              _paragrafi(1, 100 + i)))
            corpo = "<h1>A long page</h1>" + "\n".join(sez)
        elif nome == "tabella":
            righe = ["<tr><th>#</th><th>name</th><th>value</th><th>state</th><th>note</th></tr>"]
            for i in range(600):
                righe.append("<tr><td>%d</td><td>entry-%04d</td><td>%d.%02d</td><td>%s</td><td>%s</td></tr>"
                             % (i + 1, (i * 7919) % 10000, (i * 37) % 997, i % 100,
                                ("GREEN", "DEGRADED", "FAIL")[i % 3], _PAROLE[i % len(_PAROLE)]))
            corpo = "<h1>A table</h1><table>" + "".join(righe) + "</table>"
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
#  THE PURE READINGS (certified by 16-attore.py --certifica)
# ═══════════════════════════════════════════════════════════════════════════
_RIGA_LOG = re.compile(r"^(\d+\.\d+) (\S+)(?: (.*))?$")


def leggi_quaderno(testo):
    """The rows of the pages' notebook ⇒ [(time, type, [words])]."""
    out = []
    for r in (testo or "").splitlines():
        m = _RIGA_LOG.match(r.strip())
        if m:
            out.append((float(m.group(1)), m.group(2), (m.group(3) or "").split()))
    return out


def leggi_video(parole):
    """`video yt t=12.3 stato=1 q=hd2160 …` (words after «video») ⇒ dict."""
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
    """⭐ A notebook row «testo <page> <value>» with the value EQUAL
    to the typed sentence (a character lost or outside the field ⇒ no)."""
    return e[1] == "testo" and " ".join(e[2][1:]) == frase


def campo_lascia_da_solo(html):
    """⛔ Does the page's field drop the focus ON ITS OWN on a timer (a setTimeout that
    calls blur)?  It must be no: under load the letters after it would be lost."""
    return bool(re.search(r"setTimeout\([^;]*\.blur\(\)", html or ""))


def storia_contiene(testo, riga):
    """⭐ The typed line is in the bash history EXACTLY (a whole line)."""
    return any(r == riga for r in (testo or "").splitlines())


def shell_sotto(ps_testo, proc):
    """⭐ The processes running UNDER the terminal (the direct children of every
    process whose name matches `proc`), from `ps -o pid=,ppid=,comm=`:
    ['bash'], ['dash'], [] if the terminal is not there or has no children yet.
    ⚠ `comm` is cut at 15 characters («gnome-terminal-server» ⇒
    «gnome-terminal-»): `proc` is searched inside, not compared whole."""
    righe = []
    for r in (ps_testo or "").splitlines():
        p = r.split(None, 2)
        if len(p) == 3 and p[0].isdigit() and p[1].isdigit():
            righe.append((p[0], p[1], p[2].strip()))
    padri = {pid for pid, _pp, comm in righe if re.search(proc, comm)}
    return sorted({comm for _pid, pp, comm in righe if pp in padri})


def piano_cancella(scatola):
    """⭐ The gesture that deletes the selection in the file manager, per desktop:
    (modifiers, key, answer to the dialog, seconds before the answer,
    answer ALWAYS or only if the folders are still there).

    ⛔ `[M]` 27 Sep 2026, intel-b 4K and 3K campaigns on LXQt: Del + Enter after
       2.5 s NEVER had any effect (0 out of 30 and more attempts, already at 2
       users).  The photos (livello-02/utente-02 4K, livello-04/utente-02 3K)
       show the pcmanfm-qt window on «nuove» with «8 item(s) selected»
       (the Ctrl+A arrived), NO dialog, all the folders in their
       place, and in the tenant's home `~/.local/share/Trash` does not exist
       ⇒ the Del's «Move to Trash» never started (GLib creates the trash
       BEFORE moving).  On thunar (xfce) the same Del goes through «with
       confirmation», on nautilus and dolphin in ~350 ms without.
       In pcmanfm-qt 2.1.0 Del is the shortcut of the menu's QAction «Move to
       Trash»; Shift+Del is a window QShortcut («Delete»,
       really deletes) like the Ctrl+L that works, and it opens the dialog «Do you
       want to delete the selected file(s)?» Yes/No with default **No**:
       Enter would say no.  ⇒ On LXQt we do as a user who wants to
       delete: Shift+Del, and the question is answered with the letter «y»
       (QMessageBox accepts the button's letter even without Alt).
    On the other desktops it stays Del, and Enter at 2.5 s only if needed (thunar)."""
    if scatola == "lxqt":
        return (["Shift"], "Delete", "y", 1.2, True)
    return ([], "Delete", "Enter", 2.5, False)


def rett_finestra(prima, dopo, soglia=40, fattore=8):
    """⭐ The rect (x0,y0,x1,y1) — photo pixels — of the window that APPEARED
    between two PIL photos of the same size, or None.  «Changed» columns and rows
    (at least 2 points above `soglia` at scale 1/`fattore`), and the LONGEST
    contiguous run per axis: the panel clock changes too, but
    it is a short run."""
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
#  THE WORKLOAD, THE BASE
# ═══════════════════════════════════════════════════════════════════════════
class Lavoro:
    nome = "?"

    def __init__(self, att):
        self.a = att                      # the actor: s, sc, chi, ritmo, mani, dorme, verifica
        self.h = "/home/%s" % att.chi
        self.rett = None                  # the application's window (desktop)
        self.log_da = 0                   # bytes of the notebook already read
        self.ultimo_video = {}

    # -- commands in the box ---------------------------------------------------
    def dentro(self, riga, secondi=60):
        t0 = time.time()
        r = self.a.sc.dentro(riga, secondi)
        if time.time() - t0 > 3:
            print("   [%02d] ⚠ a command in the box took %.1f s: %s"
                  % (self.a.n, time.time() - t0, riga[:80]), flush=True)
        return r

    def scrivi_file(self, percorso, testo, modo="644"):
        """⚠ Not in base64 on the command line: a long page exceeds the
        argument limit («Argument list too long»).  ⇒ The file goes through the
        host's folder mounted in the box (/media/REMOTIX/rete11 ⇒
        /rete11) and is installed from there."""
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
        """The new rows of the pages' notebook (from the byte already read)."""
        # ⚠ `dentro` strips the trailing whitespace (the last newline too): the
        #   sentinel says where the file ends, and we advance only over whole
        #   rows (`[M]` 25 Sep: without it, no row was ever read)
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
        # an earlier attempt would leave «Firefox is already running»
        self.dentro("pkill -u %s -f firefox-esr 2>/dev/null; sleep 1" % self.a.chi, 30)
        return self.a.s.nella_sessione(
            "firefox-esr --no-remote --new-instance --profile %s/.c16/profilo --kiosk '%s'"
            % (self.h, url), 60)

    def vivo(self, processo):
        c, _t = self.dentro("pgrep -u %s -f %s >/dev/null" % (self.a.chi, processo), 30)
        return c == 0

    def trova_finestra(self, prima, attesa=25):
        """Waits for the window to appear STILL (two photos with the same rect)
        and returns the rect in the desktop, or None."""
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
        """A point of the application's window (or of the desktop), fractions."""
        tl, ta = self.a.desktop
        r = self.rett or (0, 0, tl, ta)
        return r[0] + fx * (r[2] - r[0]), r[1] + fy * (r[3] - r[1])

    def extra(self):
        return {}


# ═══════════════════════════════════════════════════════════════════════════
#  A — BROWSING
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
            return False, "the page server does not start: %s" % t[-200:]
        c, t = self.firefox_interno("http://127.0.0.1:%d/testo.html" % self.a.porta_interna)
        if c != 0:
            return False, "firefox-esr does not launch: %s" % t[-200:]
        r = self.aspetta(lambda e: e[1] == "carica" and e[2][:1] == ["testo"], 60)
        if not r:
            return False, "the first page did not say «carica» in 60 s"
        self.leggi_pos(r)
        return True, "firefox-esr --kiosk on the «testo» page (max scroll %d)" % self.max

    def leggi_pos(self, e):
        try:
            self.pagina, self.y, self.max = e[2][0], int(e[2][1]), int(e[2][2])
        except (IndexError, ValueError):
            pass

    def aspetta(self, cerca, attesa, dopo=0.0):
        """The first notebook row (after the time `dopo`) for which `cerca` is true.

        ⛔ The batch read is read WHOLE before returning (anomaly A4, 27 Sep):
           returning at the first good row, the positions after it were lost, and after
           a wheel the actor believed the page halfway while it was at the bottom —
           the next PageDown could not move it, and it counted as LOST input.
           `[M]` at 1 user: KDE 14 PageDown «lost» out of 49, all after a
           wheel or another PageDown; the other desktops 0 out of 172."""
        fine = time.time() + attesa
        while True:
            trovata = None
            for e in self.quaderno_nuovo():
                if e[1] in ("carica", "scroll"):
                    self.leggi_pos(e)
                if trovata is None and e[0] >= dopo and cerca(e):
                    trovata = e
            if trovata is not None:
                return trovata
            if time.time() >= fine:
                return None
            self.a.dorme(0.4)

    def lascia_il_campo(self):
        """⭐ Once the sentence is finished, the actor takes the focus off the field: Esc (the page
        says «lascia»); if it does not say it, a click on an empty point of the page."""
        t = self.a.mani.premi("Escape")
        if self.aspetta(lambda e: e[1] == "lascia", 5, t - 1):
            return True
        tl, ta = self.a.desktop
        t = self.a.mani.clic(tl * 0.5, ta * 0.6)
        ok = self.aspetta(lambda e: e[1] == "lascia", 5, t - 1) is not None
        if not ok:
            self.a.evento("errore", testo="the text field does not leave the focus (Esc and click)")
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
            self.aspetta(lambda e: False, 0)   # ⭐ A4: the REAL position before choosing
            giu = self.y < self.max * 0.6
            tacche = R.intero(3, 12)
            y0 = self.y
            t0 = M.rotella(tl * R.uniforme(0.3, 0.7), ta * R.uniforme(0.4, 0.85),
                           tacche * (1 if giu else -1), atteso=True)
            e = self.aspetta(lambda e: e[1] == "scroll" and len(e[2]) > 1
                             and e[2][1].isdigit() and int(e[2][1]) != y0, 8, t0)
            self.a.verifica("rotella", e is not None, (e[0] - t0) * 1000 if e else None,
                            "%s %d notches" % ("down" if giu else "up", tacche))
            self.a.dorme(R.pausa_s("breve"))
        elif az == "scrivi":
            # ⭐ typing with immediate echo in a field of the page: the click
            #   sets the focus, Ctrl+A makes the earlier text get replaced
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
            self.aspetta(lambda e: False, 0)   # ⭐ A4: the REAL position before choosing
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
        self.foto_ko = 0                  # the photos taken at a failed «cancella»

    def prepara(self):
        p = self.h + "/prova16"
        self.dentro("mkdir -p %(p)s/nuove %(p)s/alfa %(p)s/beta/dentro %(p)s/gamma && "
                    "for i in $(seq 1 30); do echo line $i > %(p)s/alfa/nota-$i.txt; done && "
                    "for i in $(seq 1 12); do mkdir -p %(p)s/beta/cartella-$i; done && "
                    "seq 1 5000 > %(p)s/gamma/numeri.txt && chown -R %(c)s: %(p)s"
                    % {"p": p, "c": self.a.chi}, 60)

    def avvia(self):
        prima = self.a.foto_pil()
        c, t = self.a.s.nella_sessione(self.fm.format(dir=self.h + "/prova16"), 60)
        if c != 0:
            return False, "%s does not launch: %s" % (self.proc, t[-200:])
        fine = time.time() + 30
        while time.time() < fine and not self.vivo(self.proc):
            self.a.dorme(0.5)
        if not self.vivo(self.proc):
            return False, "%s is not alive after 30 s" % self.proc
        self.rett = self.trova_finestra(prima)
        return True, "%s on ~/prova16, window %s" % (
            self.proc, [int(x) for x in self.rett] if self.rett else "NOT found (using the centre)")

    def vai(self, percorso):
        M, R = self.a.mani, self.a.ritmo
        M.combo(["Control"], "l")
        self.a.dorme(R.pausa_s("gesto"))
        M.combo(["Control"], "a")
        M.batti(percorso, eco=True)
        M.premi("Enter")
        self.a.dorme(0.8 + R.pausa_s("gesto"))

    def fuoco_vista(self):
        """A click on an EMPTY point of the view (bottom right)."""
        x, y = self.punto(0.85, 0.88)
        self.a.mani.clic(x, y)
        self.a.dorme(0.3)

    def esiste(self, nome):
        """(is there, ctime) of ~/prova16/nuove/<nome>."""
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
            self.a.evento("applicazione", testo="%s is no longer there: relaunching it" % self.proc)
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
                M.premi("Escape")           # a dialog left open
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
                    # ⭐ LXQt: the «delete?» question is always there, and the answer is «y»
                    M.batti(risposta, atteso=False)
                    conferma = True
                _c, t = self.dentro("ls -A %s/prova16/nuove | wc -l" % self.h, 30)
                n = int(t.split()[-1]) if t and t.split()[-1].isdigit() else -1
                if n == 0:
                    break
                if not sempre and not conferma and time.time() > t0 + dopo_s:
                    M.premi(risposta)        # the confirmation dialog (thunar)
                    conferma = True
                self.a.dorme(0.4)
            gesto = "+".join(mod + [tasto]) + (", " + risposta if conferma else "")
            self.a.verifica("cancella", n == 0, (time.time() - t0) * 1000 if n == 0 else None,
                            "%d folders (%s)" % (len(self.nuove), gesto))
            if n == 0:
                self.nuove = []
            else:
                # ⛔ The screen is LOOKED AT: the photo says what was there (dialog? filter?
                #   selection?) — at most three per actor, then Esc to close
                #   whatever was left open (dialog, filter bar)
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
#  C — TERMINAL
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
        testo = "\n".join("line %05d · %s" % (i, " ".join(_PAROLE[(i * 7 + j) % len(_PAROLE)]
                                                            for j in range(8)))
                          for i in range(1, 2001))
        self.scrivi_file(h + "/prova16/lungo.txt", testo + "\n")
        self.dentro("printf '\\n# c16: the history is written at every command (the actor checks it)\\n"
                    "export HISTFILE=~/.c16-storia HISTCONTROL= HISTSIZE=100000 HISTFILESIZE=100000\\n"
                    "PROMPT_COMMAND=\"history -a\"\\n' >> %(h)s/.bashrc; touch %(h)s/.c16-storia; "
                    "chown %(c)s: %(h)s/.bashrc %(h)s/.c16-storia" % {"h": h, "c": self.a.chi}, 30)

    def avvia(self):
        prima = self.a.foto_pil()
        c, t = self.a.s.nella_sessione(self.term, 60)
        if c != 0:
            return False, "%s does not launch: %s" % (self.proc, t[-200:])
        fine = time.time() + 30
        while time.time() < fine and not self.vivo(self.proc):
            self.a.dorme(0.5)
        if not self.vivo(self.proc):
            return False, "%s is not alive after 30 s" % self.proc
        self.rett = self.trova_finestra(prima)
        self.a.dorme(2)
        # ⛔ the shell under the terminal MUST be bash: the check is the bash
        #   history (`[M]` 27 Sep: qterminal opened dash, see APP["lxqt"])
        shell = self.shell()
        if shell and "bash" not in shell:
            return False, "%s with %s under it and not bash: the history (~/.c16-storia) would never be written" % (
                self.proc, "/".join(shell))
        # the focus in the window, and a first line that says the history is written
        x, y = self.punto(0.5, 0.5)
        self.a.mani.clic(x, y)
        ok = self.comando("echo ready")
        return ok, "%s, window %s, under it %s, first line %s" % (
            self.proc, [int(v) for v in self.rett] if self.rett else "NOT found (using the centre)",
            "/".join(shell) if shell else "(no child)", "arrived" if ok else "NOT arrived")

    def shell(self):
        """The terminal's direct children (the shell), from the box's `ps`."""
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
            M.combo(["Control"], "c")       # a wrong line does not stay on the prompt
        return ok

    def passo(self):
        R, M = self.a.ritmo, self.a.mani
        if not self.vivo(self.proc):
            self.a.evento("applicazione", testo="%s is no longer there: relaunching it" % self.proc)
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
#  D — 4K VIDEO
# ═══════════════════════════════════════════════════════════════════════════
def fonte_video(url):
    """--video ⇒ ('yt', ID) | ('file', path) | (None, reason)."""
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
    return None, "video source not recognised: %r" % url


RETE11_OSPITE, RETE11_SCATOLA = "/media/REMOTIX/rete11", "/rete11"


def video_nella_scatola(percorso):
    """The video file as seen FROM the box.  /rete11/… is already inside; a file
    of the host under /media/REMOTIX (e.g. misure/fase16/video/) is hooked in
    with a hard link in /media/REMOTIX/rete11/.c16-video/ (same
    disk: no copy) ⇒ /rete11/.c16-video/<nome>."""
    if percorso.startswith(RETE11_SCATOLA + "/"):
        return percorso, ""
    if percorso.startswith(RETE11_OSPITE + "/"):
        return RETE11_SCATOLA + percorso[len(RETE11_OSPITE):], ""
    if not os.path.isfile(percorso):
        return None, "the video file %s is not on the host" % percorso
    cartella = os.path.join(RETE11_OSPITE, ".c16-video")
    os.makedirs(cartella, exist_ok=True)
    dest = os.path.join(cartella, os.path.basename(percorso))
    try:
        if not (os.path.exists(dest) and os.path.samefile(dest, percorso)):
            tmp = dest + ".%d" % os.getpid()
            os.link(percorso, tmp)
            os.replace(tmp, dest)
    except OSError as e:
        return None, "the video file cannot be hooked in %s: %s" % (cartella, e)
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
                return False, "the video file %s cannot be read INSIDE the box" % video
        ok, t = self.servitore(video)
        if not ok:
            return False, "the server does not start: %s" % t[-200:]
        q = "yt=%s" % self.fonte if self.tipo == "yt" else "file=1"
        c, t = self.firefox_interno("http://127.0.0.1:%d/video.html?%s" % (self.a.porta_interna, q))
        if c != 0:
            return False, "firefox-esr does not launch: %s" % t[-200:]
        fine = time.time() + 90
        while time.time() < fine:
            self.leggi_video()
            if self.ultimo_video.get("stato") == 1 and (self.ultimo_video.get("t") or 0) > 0:
                return True, "video %s %s playing: %s" % (self.tipo, self.fonte,
                                                                 self.ultimo_video)
            self.a.dorme(2)
        return False, "the video did not start in 90 s: %s" % (self.ultimo_video or "no row")

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
            # ⚠ only a movement, never a click: the click would stop the video
            M.muovi(tl * R.uniforme(0.3, 0.7), ta * R.uniforme(0.3, 0.7))
            self.a.conta("muovi")

    def extra(self):
        self.leggi_video()
        return {"video": dict(self.ultimo_video)}


LAVORI = {"A": LavoroA, "B": LavoroB, "C": LavoroC, "D": LavoroD}
