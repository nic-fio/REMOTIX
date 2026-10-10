#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-lavori — THE ACTOR'S FOUR WORKLOADS (phase 16, fasi/16-stress-e-capacita.md §5)

Imported by `16-attore.py`; it does not run on its own.  Each workload:

    prepare()       the files in the tenant's home, BEFORE the access
    start()         the application INSIDE the session, after the first frame
    step()         one gesture (or a small series) with REAL INPUT from the browser,
                    its check (§7 «the input arrives») and the human pause
    extra()         the workload's own numbers for the status row

  A browsing       firefox-esr --kiosk on four pages of OURS served by a
                   python server in the box (no internet): text,
                   images that change at every load, a long page, a
                   table.  The pages WRITE into their notebook (load,
                   scroll, click): the check is the notebook, the latency is
                   the time of the row minus the time of the gesture.
  B file manager   the desktop's file manager on ~/prova16: creates folders
                   (Ctrl+Shift+N, name typed, Enter) in ~/prova16/nuove and
                   deletes them (Ctrl+A, Del; on LXQt Shift+Del and «y» at the
                   question: see `delete_plan`), navigates (Ctrl+L), changes view
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
   (`delete_plan`), qterminal opens dash and must be launched `-e bash` (`APP`).
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
GUEST_HANDOFF = os.environ.get("REMOTIX_HANDOFF16", "/media/REMOTIX/rete11/.c16-passaggio")
BOX_HANDOFF = "/rete11/.c16-passaggio"

PROFILES = {1: "A", 2: "B", 3: "C", 0: "D"}


def profile_of(n):
    """1,5,9,13 A · 2,6,10,14 B · 3,7,11,15 C · 4,8,12,16 D (§5)."""
    return PROFILES[n % 4]


def browser_di(n):
    """Odd Firefox, even Chrome (§4)."""
    return "firefox" if n % 2 else "chrome"


def tenant_of(n):
    """`c16%03du%d`: the clear-out recognises it (`^c[0-9]+b?u[0-9]+$`)."""
    return "c16%03du%d" % (n, n)


def internal_port(container_box, n):
    """The port of the page server IN the box (the host's network):
    one per desktop and user, outside the ports of the browsers (9700+) and of the suite."""
    return 17000 + 20 * ("gnome", "kde", "xfce", "lxqt").index(container_box) + n


# ═══════════════════════════════════════════════════════════════════════════
#  THE SERVER IN THE BOX (runs as the tenant)
# ═══════════════════════════════════════════════════════════════════════════
SERVER = r'''
import http.server, os, sys, time
PORT, ROOT, LOG, VIDEO = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".svg": "image/svg+xml",
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
        self.send_header("Content-Type", TYPES.get(os.path.splitext(VIDEO)[1], "video/mp4"))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(b - a + 1)); self.end_headers()
        with open(VIDEO, "rb") as f:
            f.seek(a); rest = b - a + 1
            try:
                while rest > 0:
                    block = f.read(min(1 << 20, rest))
                    if not block: break
                    self.wfile.write(block); rest -= len(block)
            except (BrokenPipeError, ConnectionResetError):
                pass
    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/v":
            return self._video()
        label_name = os.path.basename(p) or "testo.html"
        f = os.path.join(ROOT, label_name)
        try:
            body_el = open(f, "rb").read()
        except OSError:
            self.send_error(404); return
        self.send_response(200)
        self.send_header("Content-Type", TYPES.get(os.path.splitext(label_name)[1], "application/octet-stream"))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body_el))); self.end_headers()
        self.wfile.write(body_el)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        t = self.rfile.read(n).decode("utf-8", "replace").replace("\n", " ")[:600]
        with open(LOG, "a") as f:
            f.write("%.3f %s\n" % (time.time(), t))
        self.send_response(204); self.send_header("Content-Length", "0"); self.end_headers()
http.server.ThreadingHTTPServer.daemon_threads = True
http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
'''

# ═══════════════════════════════════════════════════════════════════════════
#  THE PAGES OF WORKLOAD A (and the video one)
# ═══════════════════════════════════════════════════════════════════════════
PAGES_A = ("testo", "images", "long", "table")
NAV_COLORS = ("#c0392b", "#2471a3", "#1e8449", "#b7950b")
NAV_Y = 0.16            # centre of the buttons, fraction of the desktop's height
NOTE_Y = 0.94           # centre of the text field at the bottom
NOTE_WORDS = ("alpha", "beta", "gamma", "delta", "session", "desktop", "keyboard", "server",
               "measure", "network", "frame", "remote")

_HEAD = r"""<!doctype html><html lang=en><meta charset=utf-8><title>c16 %(label_name)s</title>
<style>
 body{margin:0;font:28px/1.5 sans-serif;background:%(background)s;color:#222}
 nav{position:fixed;left:0;right:0;top:8vh;height:16vh;display:flex;z-index:9}
 nav a{flex:1;display:flex;align-items:center;justify-content:center;color:#fff;
       font:bold 64px sans-serif;text-decoration:none;border:6px solid #fff}
 nav a.here{outline:14px solid #000;outline-offset:-20px}
 main{padding:27vh 6vw 10vh 6vw}
 .card{display:inline-block;margin:18px;vertical-align:top}
 table{border-collapse:collapse;width:100%%} td,th{border:1px solid #888;padding:6px 14px}
 tr:nth-child(odd){background:#eef} section{padding:30px;margin:10px 0}
 #remark{position:fixed;left:6vw;width:88vw;bottom:2vh;height:8vh;z-index:9;font:44px monospace;
       background:#fffbe0;border:4px solid #555;box-sizing:border-box}
</style>
<nav>%(nav)s</nav><textarea id=remark spellcheck=false></textarea><main>
"""

_QUEUE = r"""</main>
<script>
const LABEL_NAME = %(nome_js)s;
function send_it(t){ try { fetch('/log', {method:'POST', body:t, keepalive:true}).catch(()=>{}); } catch(e){} }
function mx(){ return Math.max(0, document.documentElement.scrollHeight - innerHeight); }
addEventListener('load', () => send_it('load ' + LABEL_NAME + ' ' + Math.round(scrollY) + ' ' + mx()));
let tS = null;
addEventListener('scroll', () => { if (tS) return; tS = setTimeout(() => { tS = null;
  send_it('scroll ' + LABEL_NAME + ' ' + Math.round(scrollY) + ' ' + mx()); }, 150); });
// ⭐ the button answers AT ONCE to the press (like every site): the image
//   changes at the click, and the load of the page after it belongs to the application
// the text field: says its value 300 ms after the last keystroke.
// ⛔ it does NOT leave the focus on its own (it used to: 1.5 s after the last key — but under
//   load Marionette/CDP can be slower than that between two keys, and the letters after
//   ended up outside the field: a false «input lost»).  It leaves it when the ACTOR
//   has finished the sentence and presses Esc (PageDown and Home must go back to the page),
//   and says so («leave»).
const remark = document.getElementById('remark');
let tN = null;
remark.addEventListener('input', () => { clearTimeout(tN);
  tN = setTimeout(() => send_it('testo ' + LABEL_NAME + ' ' + remark.value), 300); });
remark.addEventListener('keydown', (e) => { if (e.key === 'Escape') remark.blur(); });
remark.addEventListener('blur', () => send_it('leave ' + LABEL_NAME));
document.querySelectorAll('nav a').forEach((a) => a.addEventListener('mousedown',
  () => { a.style.filter = 'brightness(1.6)'; }));
addEventListener('click', (e) => { if (e.target.closest('a')) return;
  send_it('click ' + LABEL_NAME + ' ' + Math.round(e.clientX) + ' ' + Math.round(e.clientY)); });
%(extra)s
</script></html>
"""

_WORDS = ("the session", "the desktop", "a window", "the encoder", "the network",
           "the frame", "a user", "the keyboard", "the server", "the graphics card",
           "updates", "arrives", "scrolls", "stays still", "redraws", "measures",
           "without hurry", "in 4K", "on the glass", "from the browser")


def _paragraphs(n, seed):
    import random
    r = random.Random(seed)
    out = []
    for i in range(n):
        sentences = []
        for _j in range(r.randint(3, 7)):
            sentences.append(" ".join(r.choice(_WORDS) for _k in range(r.randint(6, 14))).capitalize() + ".")
        out.append("<p><b>%d.</b> %s</p>" % (i + 1, " ".join(sentences)))
    return "\n".join(out)


def pages_a():
    """{file name: html} — four pages at least three 4K screens long."""
    background = {"testo": "#fdfdf6", "images": "#20252b", "long": "#ffffff", "table": "#f6fbff"}
    out = {}
    for label_name in PAGES_A:
        nav = "".join('<a href="%s.html" style="background:%s"%s>%s</a>' % (
            p, NAV_COLORS[i], ' class=here' if p == label_name else "", p.upper())
            for i, p in enumerate(PAGES_A))
        body_el, extra = "", ""
        if label_name == "testo":
            body_el = "<h1>A text to read</h1>" + _paragraphs(60, 1)
        elif label_name == "images":
            body_el = "<h1 style=color:#eee>Images</h1><div id=g></div>"
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
        elif label_name == "long":
            sect = []
            for i in range(400):
                sect.append('<section style="background:hsl(%d,55%%,%d%%)"><h2>Section %d</h2>%s</section>'
                           % ((i * 37) % 360, 78 + (i % 3) * 6, i + 1,
                              _paragraphs(1, 100 + i)))
            body_el = "<h1>A long page</h1>" + "\n".join(sect)
        elif label_name == "table":
            line_list = ["<tr><th>#</th><th>name</th><th>value</th><th>state</th><th>note</th></tr>"]
            for i in range(600):
                line_list.append("<tr><td>%d</td><td>entry-%04d</td><td>%d.%02d</td><td>%s</td><td>%s</td></tr>"
                             % (i + 1, (i * 7919) % 10000, (i * 37) % 997, i % 100,
                                ("GREEN", "DEGRADED", "FAIL")[i % 3], _WORDS[i % len(_WORDS)]))
            body_el = "<h1>A table</h1><table>" + "".join(line_list) + "</table>"
        out[label_name + ".html"] = (_HEAD % {"label_name": label_name, "background": background[label_name], "nav": nav} + body_el
                               + _QUEUE % {"nome_js": json.dumps(label_name), "extra": extra})
    out["video.html"] = VIDEO_PAGE
    return out


VIDEO_PAGE = r"""<!doctype html><html><meta charset=utf-8><title>c16 video</title>
<style>html,body{margin:0;height:100%;background:#000;overflow:hidden}
#p,video{position:fixed;left:0;top:0;width:100vw;height:100vh;border:0}</style>
<div id=p></div>
<script>
const q = new URLSearchParams(location.search);
const yt = q.get('yt'), fl = q.get('file');
function send_it(t){ try { fetch('/log', {method:'POST', body:t, keepalive:true}).catch(()=>{}); } catch(e){} }
send_it('load video ' + (yt ? 'yt ' + yt : 'file'));
if (yt) {
  const tag = document.createElement('script');
  tag.src = 'https://www.youtube.com/iframe_api';
  tag.onerror = () => send_it('video failure api-non-caricata');
  document.head.appendChild(tag);
  window.onYouTubeIframeAPIReady = function () {
    window.P = new YT.Player('p', { width: innerWidth, height: innerHeight, videoId: yt,
      host: 'https://www.youtube-nocookie.com',
      playerVars: { autoplay: 1, controls: 0, loop: 1, playlist: yt, rel: 0, iv_load_policy: 3,
                    playsinline: 1, disablekb: 1, fs: 0, vq: 'hd2160', origin: location.origin },
      events: {
        onReady: (e) => { try { e.target.unMute(); e.target.setVolume(70);
                   e.target.setPlaybackQuality('hd2160'); } catch (x) {}
                   e.target.playVideo(); send_it('video ready'); },
        onStateChange: (e) => send_it('video state ' + e.data),
        onPlaybackQualityChange: (e) => send_it('video quality ' + e.data),
        onError: (e) => send_it('video failure ' + e.data) } });
  };
  setInterval(() => {
    if (!window.P || !P.getCurrentTime) return;
    let lv = []; try { lv = P.getAvailableQualityLevels() || []; } catch (x) {}
    send_it('video yt t=' + P.getCurrentTime().toFixed(2) + ' state=' + P.getPlayerState()
      + ' q=' + P.getPlaybackQuality() + ' levels=' + lv.join(',')
      + ' loaded=' + (P.getVideoLoadedFraction() || 0).toFixed(3)
      + ' mute=' + (P.isMuted() ? 1 : 0) + ' vol=' + P.getVolume());
  }, 5000);
} else {
  const v = document.createElement('video');
  v.src = '/v'; v.autoplay = true; v.loop = true; v.controls = false;
  document.body.appendChild(v);
  v.addEventListener('error', () => send_it('video failure ' + (v.error ? v.error.code + ' ' + v.error.message : '?')));
  v.addEventListener('playing', () => send_it('video state 1'));
  v.play().catch((e) => send_it('video failure play ' + e));
  setInterval(() => {
    const qq = v.getVideoPlaybackQuality ? v.getVideoPlaybackQuality() : {};
    send_it('video file t=' + v.currentTime.toFixed(2) + ' state=' + (v.paused ? 2 : 1)
      + ' q=' + v.videoWidth + 'x' + v.videoHeight + ' lost=' + (qq.droppedVideoFrames || 0)
      + ' totals=' + (qq.totalVideoFrames || 0) + ' mute=' + (v.muted ? 1 : 0));
  }, 5000);
}
</script></html>
"""

INTERNAL_PREFS = """user_pref("media.autoplay.default", 0);
user_pref("media.autoplay.blocking_policy", 0);
user_pref("app.update.enabled", false);
user_pref("browser.tabs.warnOnClose", false);
user_pref("toolkit.startup.max_resumed_crashes", -1);
user_pref("browser.startup.page", 0);
user_pref("privacy.webrtc.legacyGlobalIndicator", false);
"""

# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE READINGS (certified by 16-attore.py --certify)
# ═══════════════════════════════════════════════════════════════════════════
_LOG_LINE = re.compile(r"^(\d+\.\d+) (\S+)(?: (.*))?$")


def read_notebook(body_text):
    """The rows of the pages' notebook ⇒ [(time, type, [words])]."""
    out = []
    for r in (body_text or "").splitlines():
        m = _LOG_LINE.match(r.strip())
        if m:
            out.append((float(m.group(1)), m.group(2), (m.group(3) or "").split()))
    return out


def read_video(words):
    """`video yt t=12.3 state=1 q=hd2160 …` (words after «video») ⇒ dict."""
    d = {"source": words[0] if words else None}
    for p in words[1:]:
        k, s, v = p.partition("=")
        if not s:
            continue
        try:
            d[k] = float(v) if k in ("t", "loaded") else (int(v) if v.lstrip("-").isdigit() else v)
        except ValueError:
            d[k] = v
    return d


def sentence_in_field(e, sentence):
    """⭐ A notebook row «testo <page> <value>» with the value EQUAL
    to the typed sentence (a character lost or outside the field ⇒ no)."""
    return e[1] == "testo" and " ".join(e[2][1:]) == sentence


def field_left_alone(html):
    """⛔ Does the page's field drop the focus ON ITS OWN on a timer (a setTimeout that
    calls blur)?  It must be no: under load the letters after it would be lost."""
    return bool(re.search(r"setTimeout\([^;]*\.blur\(\)", html or ""))


def history_contains(body_text, row):
    """⭐ The typed line is in the bash history EXACTLY (a whole line)."""
    return any(r == row for r in (body_text or "").splitlines())


def shell_below(ps_text, proc):
    """⭐ The processes running UNDER the terminal (the direct children of every
    process whose name matches `proc`), from `ps -o pid=,ppid=,comm=`:
    ['bash'], ['dash'], [] if the terminal is not there or has no children yet.
    ⚠ `comm` is cut at 15 characters («gnome-terminal-server» ⇒
    «gnome-terminal-»): `proc` is searched inside, not compared whole."""
    line_list = []
    for r in (ps_text or "").splitlines():
        p = r.split(None, 2)
        if len(p) == 3 and p[0].isdigit() and p[1].isdigit():
            line_list.append((p[0], p[1], p[2].strip()))
    parents = {pid for pid, _pp, comm in line_list if re.search(proc, comm)}
    return sorted({comm for _pid, pp, comm in line_list if pp in parents})


def delete_plan(container_box):
    """⭐ The gesture that deletes the selection in the file manager, per desktop:
    (modifiers, key, answer to the dialog, seconds before the answer,
    answer ALWAYS or only if the folders are still there).

    ⛔ `[M]` 27 Sep 2026, intel-b 4K and 3K campaigns on LXQt: Del + Enter after
       2.5 s NEVER had any effect (0 out of 30 and more attempts, already at 2
       users).  The photos (livello-02/utente-02 4K, livello-04/utente-02 3K)
       show the pcmanfm-qt window on «new_ones» with «8 item(s) selected»
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
    if container_box == "lxqt":
        return (["Shift"], "Delete", "y", 1.2, True)
    return ([], "Delete", "Enter", 2.5, False)


def window_rect(before, after, threshold=40, factor=8):
    """⭐ The rect (x0,y0,x1,y1) — photo pixels — of the window that APPEARED
    between two PIL photos of the same size, or None.  «Changed» columns and rows
    (at least 2 points above `threshold` at scale 1/`factor`), and the LONGEST
    contiguous run per axis: the panel clock changes too, but
    it is a short run."""
    from PIL import ImageChops
    w, h = after.size
    a = before.resize((max(1, w // factor), max(1, h // factor))).convert("L")
    b = after.resize((max(1, w // factor), max(1, h // factor))).convert("L")
    d = ImageChops.difference(a, b).point(lambda v: 255 if v > threshold else 0)
    pw, ph = d.size
    px = list(d.getdata())
    clr = [0] * pw
    rig = [0] * ph
    for i, v in enumerate(px):
        if v:
            clr[i % pw] += 1
            rig[i // pw] += 1

    def run(v):
        better, i0 = (0, 0, -1), None
        for i, x in enumerate(v + [0]):
            if x >= 2 and i0 is None:
                i0 = i
            elif x < 2 and i0 is not None:
                if i - i0 > better[0]:
                    better = (i - i0, i0, i)
                i0 = None
        return better
    cx, cy = run(clr), run(rig)
    if cx[0] < pw * 0.08 or cy[0] < ph * 0.08:
        return None
    return (cx[1] * w / float(pw), cy[1] * h / float(ph), cx[2] * w / float(pw), cy[2] * h / float(ph))


# ═══════════════════════════════════════════════════════════════════════════
#  THE WORKLOAD, THE BASE
# ═══════════════════════════════════════════════════════════════════════════
class Work:
    label_name = "?"

    def __init__(self, expect):
        self.a = expect                      # the actor: s, sc, chi, rate, hands, sleeps, verify
        self.h = "/home/%s" % expect.chi
        self.rect = None                  # the application's window (desktop)
        self.log_da = 0                   # bytes of the notebook already read
        self.last_video = {}

    # -- commands in the box ---------------------------------------------------
    def inside(self, row, seconds=60):
        t0 = time.time()
        r = self.a.sc.inside(row, seconds)
        if time.time() - t0 > 3:
            print("   [%02d] ⚠ a command in the box took %.1f s: %s"
                  % (self.a.n, time.time() - t0, row[:80]), flush=True)
        return r

    def write_file(self, fpath, body_text, manner="644"):
        """⚠ Not in base64 on the command line: a long page exceeds the
        argument limit («Argument list too long»).  ⇒ The file goes through the
        host's folder mounted in the box (/media/REMOTIX/rete11 ⇒
        /rete11) and is installed from there."""
        label_name = "%s-%s" % (self.a.chi, os.path.basename(fpath))
        os.makedirs(GUEST_HANDOFF, exist_ok=True)
        with open(os.path.join(GUEST_HANDOFF, label_name), "w") as f:
            f.write(body_text)
        try:
            return self.inside("install -D -o %s -g %s -m %s %s/%s %s"
                               % (self.a.chi, self.a.chi, manner, BOX_HANDOFF, label_name,
                                  fpath), 60)
        finally:
            try:
                os.unlink(os.path.join(GUEST_HANDOFF, label_name))
            except OSError:
                pass

    def new_notebook(self):
        """The new rows of the pages' notebook (from the byte already read)."""
        # ⚠ `inside` strips the trailing whitespace (the last newline too): the
        #   sentinel says where the file ends, and we advance only over whole
        #   rows (`[M]` 25 Sep: without it, no row was ever read)
        c, t = self.inside("tail -c +%d %s/.c16/quaderno.log 2>/dev/null; echo @@FINE"
                           % (self.log_da + 1, self.h), 30)
        if c is None or not t or "@@FINE" not in t:
            return []
        t = t[:t.rfind("@@FINE")]
        body_text = t[:t.rfind("\n") + 1] if "\n" in t else ""
        self.log_da += len(body_text.encode())
        return read_notebook(body_text)

    def server(self, video=""):
        port = self.a.internal_port
        c, t = self.inside(
            "h=%(h)s; pkill -u %(c)s -f c16-servitore.py 2>/dev/null; : > $h/.c16/quaderno.log; "
            "chown %(c)s: $h/.c16/quaderno.log; "
            "setsid runuser -u %(c)s -- python3 $h/.c16/c16-servitore.py %(p)d $h/.c16/pages "
            "$h/.c16/quaderno.log '%(v)s' </dev/null >$h/.c16/servitore.log 2>&1 & "
            "for i in $(seq 1 40); do python3 -c \"import socket; socket.create_connection(('127.0.0.1', %(p)d), 1)\" "
            "2>/dev/null && { echo lit; exit 0; }; sleep 0.25; done; cat $h/.c16/servitore.log; exit 1"
            % {"h": self.h, "c": self.a.chi, "p": port, "v": video}, 40)
        self.log_da = 0
        return c == 0, t

    def prepare_pages(self):
        for label_name, html in pages_a().items():
            self.write_file("%s/.c16/pages/%s" % (self.h, label_name), html)
        self.write_file("%s/.c16/c16-servitore.py" % self.h, SERVER)
        self.write_file("%s/.c16/profile_v/user.js" % self.h,
                         self.a.internal_preferences() + INTERNAL_PREFS, "600")
        self.inside("chown -R %s: %s/.c16" % (self.a.chi, self.h), 30)

    def internal_firefox(self, url):
        # an earlier attempt would leave «Firefox is already running»
        self.inside("pkill -u %s -f firefox-esr 2>/dev/null; sleep 1" % self.a.chi, 30)
        return self.a.s.in_session(
            "firefox-esr --no-remote --new-instance --profile %s/.c16/profile_v --kiosk '%s'"
            % (self.h, url), 60)

    def alive(self, process):
        c, _t = self.inside("pgrep -u %s -f %s >/dev/null" % (self.a.chi, process), 30)
        return c == 0

    def find_window(self, before, wait=25):
        """Waits for the window to appear STILL (two photos with the same rect)
        and returns the rect in the desktop, or None."""
        fine = time.time() + wait
        last = None
        while time.time() < fine:
            self.a.sleeps(1.5)
            after = self.a.photo_pil()
            if after is None or before is None or after.size != before.size:
                continue
            r = window_rect(before, after)
            if r and last and all(abs(x - y) < 20 for x, y in zip(r, last)):
                return self.a.photo_to_desktop(r)
            last = r
        return self.a.photo_to_desktop(last) if last else None

    def spot(self, fx, fy):
        """A point of the application's window (or of the desktop), fractions."""
        tl, ta = self.a.desktop
        r = self.rect or (0, 0, tl, ta)
        return r[0] + fx * (r[2] - r[0]), r[1] + fy * (r[3] - r[1])

    def extra(self):
        return {}


# ═══════════════════════════════════════════════════════════════════════════
#  A — BROWSING
# ═══════════════════════════════════════════════════════════════════════════
class WorkA(Work):
    label_name = "A"

    def __init__(self, expect):
        super().__init__(expect)
        self.page_v, self.y, self.max = "testo", 0, 0

    def prepare(self):
        self.prepare_pages()

    def start(self):
        ok, t = self.server()
        if not ok:
            return False, "the page server does not start: %s" % t[-200:]
        c, t = self.internal_firefox("http://127.0.0.1:%d/testo.html" % self.a.internal_port)
        if c != 0:
            return False, "firefox-esr does not launch: %s" % t[-200:]
        r = self.wait_for(lambda e: e[1] == "load" and e[2][:1] == ["testo"], 60)
        if not r:
            return False, "the first page did not say «load» in 60 s"
        self.read_pos(r)
        return True, "firefox-esr --kiosk on the «testo» page (max scroll %d)" % self.max

    def read_pos(self, e):
        try:
            self.page_v, self.y, self.max = e[2][0], int(e[2][1]), int(e[2][2])
        except (IndexError, ValueError):
            pass

    def wait_for(self, search, wait, after=0.0):
        """The first notebook row (after the time `after`) for which `search` is true.

        ⛔ The batch read is read WHOLE before returning (anomaly A4, 27 Sep):
           returning at the first good row, the positions after it were lost, and after
           a wheel the actor believed the page halfway while it was at the bottom —
           the next PageDown could not move it, and it counted as LOST input.
           `[M]` at 1 user: KDE 14 PageDown «lost» out of 49, all after a
           wheel or another PageDown; the other desktops 0 out of 172."""
        fine = time.time() + wait
        while True:
            found_at = None
            for e in self.new_notebook():
                if e[1] in ("load", "scroll"):
                    self.read_pos(e)
                if found_at is None and e[0] >= after and search(e):
                    found_at = e
            if found_at is not None:
                return found_at
            if time.time() >= fine:
                return None
            self.a.sleeps(0.4)

    def leave_field(self):
        """⭐ Once the sentence is finished, the actor takes the focus off the field: Esc (the page
        says «leave»); if it does not say it, a click on an empty point of the page."""
        t = self.a.hands.press("Escape")
        if self.wait_for(lambda e: e[1] == "leave", 5, t - 1):
            return True
        tl, ta = self.a.desktop
        t = self.a.hands.click(tl * 0.5, ta * 0.6)
        ok = self.wait_for(lambda e: e[1] == "leave", 5, t - 1) is not None
        if not ok:
            self.a.event("failure", body_text="the text field does not leave the focus (Esc and click)")
        return ok

    def step(self):
        R, M = self.a.rate, self.a.hands
        tl, ta = self.a.desktop
        az = R.choose(("naviga", "scroll_wheel", "click", "key", "put_out"), (30, 30, 12, 12, 16))
        if az == "naviga":
            other_ones = [p for p in PAGES_A if p != self.page_v]
            dove = R.choose(other_ones)
            i = PAGES_A.index(dove)
            t0 = M.click((i + 0.5) * tl / 4.0, NAV_Y * ta, expected_val=True)
            e = self.wait_for(lambda e: e[1] == "load" and e[2][:1] == [dove], 10, t0)
            self.a.verify("naviga", e is not None, (e[0] - t0) * 1000 if e else None,
                            dove)
            self.a.sleeps(R.pause_s("leggere"))
        elif az == "scroll_wheel":
            self.wait_for(lambda e: False, 0)   # ⭐ A4: the REAL position before choosing
            down = self.y < self.max * 0.6
            ticks = R.whole(3, 12)
            y0 = self.y
            t0 = M.scroll_wheel(tl * R.uniform(0.3, 0.7), ta * R.uniform(0.4, 0.85),
                           ticks * (1 if down else -1), expected_val=True)
            e = self.wait_for(lambda e: e[1] == "scroll" and len(e[2]) > 1
                             and e[2][1].isdigit() and int(e[2][1]) != y0, 8, t0)
            self.a.verify("scroll_wheel", e is not None, (e[0] - t0) * 1000 if e else None,
                            "%s %d notches" % ("down" if down else "up", ticks))
            self.a.sleeps(R.pause_s("brief"))
        elif az == "put_out":
            # ⭐ typing with immediate echo in a field of the page: the click
            #   sets the focus, Ctrl+A makes the earlier text get replaced
            M.click(tl * R.uniform(0.3, 0.7), NOTE_Y * ta)
            self.a.sleeps(R.pause_s("gesture"))
            M.combo(["Control"], "a")
            sentence = " ".join(R.choose(NOTE_WORDS) for _ in range(R.whole(2, 5)))
            t0 = M.beat(sentence, echo=True)
            e = self.wait_for(lambda e: sentence_in_field(e, sentence), 8, t0 - 30)
            self.a.verify("put_out", e is not None, (e[0] - t0) * 1000 if e else None, sentence)
            self.leave_field()
            self.a.sleeps(R.pause_s("brief"))
        elif az == "click":
            t0 = M.click(tl * R.uniform(0.2, 0.8), ta * R.uniform(0.45, 0.85))
            e = self.wait_for(lambda e: e[1] == "click", 8, t0)
            self.a.verify("click", e is not None, (e[0] - t0) * 1000 if e else None, self.page_v)
            self.a.sleeps(R.pause_s("brief"))
        else:
            self.wait_for(lambda e: False, 0)   # ⭐ A4: the REAL position before choosing
            key = "PageDown" if self.y < self.max * 0.7 else "Home"
            y0 = self.y
            M.move_to(tl * 0.5, ta * 0.6)
            t0 = M.press(key, expected_val=True)
            e = self.wait_for(lambda e: e[1] == "scroll" and len(e[2]) > 1
                             and e[2][1].isdigit() and int(e[2][1]) != y0, 8, t0)
            self.a.verify("key", e is not None, (e[0] - t0) * 1000 if e else None, key)
            self.a.sleeps(R.pause_s("brief"))


# ═══════════════════════════════════════════════════════════════════════════
#  B — FILE MANAGER
# ═══════════════════════════════════════════════════════════════════════════
class WorkB(Work):
    label_name = "B"

    def __init__(self, expect):
        super().__init__(expect)
        self.fm, self.proc = APP[expect.o.container_box]["fm"]
        self.k = 0
        self.new_ones = []
        self.photo_ko = 0                  # the photos taken at a failed «cancella»

    def prepare(self):
        p = self.h + "/prova16"
        self.inside("mkdir -p %(p)s/new_ones %(p)s/alpha_ch %(p)s/beta/inside %(p)s/gamma && "
                    "for i in $(seq 1 30); do echo line $i > %(p)s/alpha_ch/remark-$i.txt; done && "
                    "for i in $(seq 1 12); do mkdir -p %(p)s/beta/folder-$i; done && "
                    "seq 1 5000 > %(p)s/gamma/numeri.txt && chown -R %(c)s: %(p)s"
                    % {"p": p, "c": self.a.chi}, 60)

    def start(self):
        before = self.a.photo_pil()
        c, t = self.a.s.in_session(self.fm.format(dir=self.h + "/prova16"), 60)
        if c != 0:
            return False, "%s does not launch: %s" % (self.proc, t[-200:])
        fine = time.time() + 30
        while time.time() < fine and not self.alive(self.proc):
            self.a.sleeps(0.5)
        if not self.alive(self.proc):
            return False, "%s is not alive after 30 s" % self.proc
        self.rect = self.find_window(before)
        return True, "%s on ~/prova16, window %s" % (
            self.proc, [int(x) for x in self.rect] if self.rect else "NOT found (using the centre)")

    def go_to(self, fpath):
        M, R = self.a.hands, self.a.rate
        M.combo(["Control"], "l")
        self.a.sleeps(R.pause_s("gesture"))
        M.combo(["Control"], "a")
        M.beat(fpath, echo=True)
        M.press("Enter")
        self.a.sleeps(0.8 + R.pause_s("gesture"))

    def focus_view(self):
        """A click on an EMPTY point of the view (bottom right)."""
        x, y = self.spot(0.85, 0.88)
        self.a.hands.click(x, y)
        self.a.sleeps(0.3)

    def path_exists(self, label_name):
        """(is there, ctime) of ~/prova16/nuove/<label_name>."""
        c, t = self.inside("stat -c %%.3Z %s/prova16/new_ones/%s 2>/dev/null" % (self.h, label_name), 30)
        if c == 0 and t.strip():
            try:
                return True, float(t.split()[-1])
            except ValueError:
                return True, None
        return False, None

    def step(self):
        R, M = self.a.rate, self.a.hands
        if not self.alive(self.proc):
            self.a.event("application", body_text="%s is no longer there: relaunching it" % self.proc)
            ok, m = self.start()
            self.a.event("application", body_text=m, ok=ok)
            self.a.sleeps(3)
            return
        az = R.choose(("create", "delete", "naviga", "vista", "win", "scroll_wheel"),
                      (30, 12 if len(self.new_ones) < 3 else 35, 15, 12, 8, 12))
        if az == "create":
            self.go_to(self.h + "/prova16/new_ones")
            self.focus_view()
            self.k += 1
            label_name = "c16n%d%s" % (self.k, R.digits(3))
            M.combo(["Control", "Shift"], "N")
            self.a.sleeps(1.2 + R.pause_s("gesture"))
            M.combo(["Control"], "a")
            M.beat(label_name, echo=True)
            t0 = M.press("Enter")
            fine, c, ct = time.time() + 10, False, None
            while time.time() < fine:
                c, ct = self.path_exists(label_name)
                if c:
                    break
                self.a.sleeps(0.4)
            self.a.verify("create", c, (ct - t0) * 1000 if (c and ct) else None, label_name)
            if c:
                self.new_ones.append(label_name)
            else:
                M.press("Escape")           # a dialog left open
        elif az == "delete":
            self.go_to(self.h + "/prova16/new_ones")
            self.focus_view()
            M.combo(["Control"], "a")
            self.a.sleeps(R.pause_s("gesture"))
            mod, key, response, after_s, always = delete_plan(self.a.o.container_box)
            t0 = M.combo(mod, key) if mod else M.press(key)
            fine = time.time() + 10
            confirm = False
            n = -1
            while time.time() < fine:
                if always and not confirm and time.time() > t0 + after_s:
                    # ⭐ LXQt: the «delete?» question is always there, and the answer is «y»
                    M.beat(response, expected_val=False)
                    confirm = True
                _c, t = self.inside("ls -A %s/prova16/new_ones | wc -l" % self.h, 30)
                n = int(t.split()[-1]) if t and t.split()[-1].isdigit() else -1
                if n == 0:
                    break
                if not always and not confirm and time.time() > t0 + after_s:
                    M.press(response)        # the confirmation dialog (thunar)
                    confirm = True
                self.a.sleeps(0.4)
            gesture = "+".join(mod + [key]) + (", " + response if confirm else "")
            self.a.verify("delete", n == 0, (time.time() - t0) * 1000 if n == 0 else None,
                            "%d folders (%s)" % (len(self.new_ones), gesture))
            if n == 0:
                self.new_ones = []
            else:
                # ⛔ The screen is LOOKED AT: the photo says what was there (dialog? filter?
                #   selection?) — at most three per actor, then Esc to close
                #   whatever was left open (dialog, filter bar)
                if self.photo_ko < 3:
                    self.photo_ko += 1
                    self.a.fires()
                M.press("Escape")
        elif az == "naviga":
            dove = R.choose(("alpha_ch", "beta", "beta/inside", "gamma", ""))
            self.go_to(self.h + "/prova16/" + dove)
            self.a.tally("naviga")
        elif az == "vista":
            M.combo(["Control"], R.choose(("1", "2")))
            self.a.tally("vista")
        elif az == "win":
            M.combo(["Control"], "n")
            self.a.sleeps(1.5 + R.pause_s("brief"))
            M.combo(["Control"], "w")
            self.a.tally("win")
        else:
            x, y = self.spot(R.uniform(0.4, 0.7), R.uniform(0.4, 0.7))
            M.scroll_wheel(x, y, R.whole(2, 8) * R.choose((1, -1)))
            self.a.tally("scroll_wheel")
        self.a.sleeps(R.pause_s("brief"))


# ═══════════════════════════════════════════════════════════════════════════
#  C — TERMINAL
# ═══════════════════════════════════════════════════════════════════════════
COMMANDS_C = (
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


class WorkC(Work):
    label_name = "C"

    def __init__(self, expect):
        super().__init__(expect)
        self.term, self.proc = APP[expect.o.container_box]["term"]
        self.k = 0

    def prepare(self):
        h = self.h
        body_text = "\n".join("line %05d · %s" % (i, " ".join(_WORDS[(i * 7 + j) % len(_WORDS)]
                                                            for j in range(8)))
                          for i in range(1, 2001))
        self.write_file(h + "/prova16/lungo.txt", body_text + "\n")
        self.inside("printf '\\n# c16: the history is written at every command (the actor checks it)\\n"
                    "export HISTFILE=~/.c16-storia HISTCONTROL= HISTSIZE=100000 HISTFILESIZE=100000\\n"
                    "PROMPT_COMMAND=\"history -a\"\\n' >> %(h)s/.bashrc; touch %(h)s/.c16-storia; "
                    "chown %(c)s: %(h)s/.bashrc %(h)s/.c16-storia" % {"h": h, "c": self.a.chi}, 30)

    def start(self):
        before = self.a.photo_pil()
        c, t = self.a.s.in_session(self.term, 60)
        if c != 0:
            return False, "%s does not launch: %s" % (self.proc, t[-200:])
        fine = time.time() + 30
        while time.time() < fine and not self.alive(self.proc):
            self.a.sleeps(0.5)
        if not self.alive(self.proc):
            return False, "%s is not alive after 30 s" % self.proc
        self.rect = self.find_window(before)
        self.a.sleeps(2)
        # ⛔ the shell under the terminal MUST be bash: the check is the bash
        #   history (`[M]` 27 Sep: qterminal opened dash, see APP["lxqt"])
        shell = self.shell()
        if shell and "bash" not in shell:
            return False, "%s with %s under it and not bash: the history (~/.c16-storia) would never be written" % (
                self.proc, "/".join(shell))
        # the focus in the window, and a first line that says the history is written
        x, y = self.spot(0.5, 0.5)
        self.a.hands.click(x, y)
        ok = self.command("echo ready")
        return ok, "%s, window %s, under it %s, first line %s" % (
            self.proc, [int(v) for v in self.rect] if self.rect else "NOT found (using the centre)",
            "/".join(shell) if shell else "(no child)", "arrived" if ok else "NOT arrived")

    def shell(self):
        """The terminal's direct children (the shell), from the box's `ps`."""
        c, t = self.inside("ps -u %s -o pid=,ppid=,comm=" % self.a.chi, 30)
        return shell_below(t, self.proc) if c == 0 else []

    def history(self):
        c, t = self.inside("stat -c %%.3Y %s/.c16-storia; tail -n 30 %s/.c16-storia"
                           % (self.h, self.h), 30)
        if c != 0 or not t:
            return None, ""
        before, _, rest = t.partition("\n")
        try:
            return float(before.strip()), rest
        except ValueError:
            return None, rest

    def command(self, cmd, duration_top=0.0):
        R, M = self.a.rate, self.a.hands
        self.k += 1
        row = "%s #k%d" % (cmd, self.k)
        M.beat(row, echo=True)
        self.a.sleeps(R.pause_s("gesture"))
        t0 = M.press("Enter", expected_val=True)
        if duration_top:
            self.a.sleeps(duration_top)
            t0 = M.press("q", expected_val=True)
        fine = time.time() + 20
        ok, mt = False, None
        while time.time() < fine:
            mt, st = self.history()
            if history_contains(st, row):
                ok = True
                break
            self.a.sleeps(0.4)
        self.a.verify("command", ok, (mt - t0) * 1000 if (ok and mt) else None,
                        cmd.split()[0])
        if not ok:
            M.combo(["Control"], "c")       # a wrong line does not stay on the prompt
        return ok

    def step(self):
        R, M = self.a.rate, self.a.hands
        if not self.alive(self.proc):
            self.a.event("application", body_text="%s is no longer there: relaunching it" % self.proc)
            ok, m = self.start()
            self.a.event("application", body_text=m, ok=ok)
            self.a.sleeps(3)
            return
        if R.probable(0.15):
            x, y = self.spot(0.5, R.uniform(0.3, 0.7))
            M.scroll_wheel(x, y, R.whole(3, 10) * R.choose((1, -1)))
            self.a.tally("scroll_wheel")
        else:
            cmd = R.choose([c for c, _p in COMMANDS_C], [p for _c, p in COMMANDS_C])
            self.command(cmd, R.uniform(3, 8) if cmd == "top" else 0.0)
        self.a.sleeps(R.pause_s("leggere" if R.probable(0.3) else "brief"))


# ═══════════════════════════════════════════════════════════════════════════
#  D — 4K VIDEO
# ═══════════════════════════════════════════════════════════════════════════
def video_source(url):
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


NETWORK11_GUEST, NETWORK11_BOX = "/media/REMOTIX/rete11", "/rete11"


def video_in_box(fpath):
    """The video file as seen FROM the box.  /rete11/… is already inside; a file
    of the host under /media/REMOTIX (e.g. misure/fase16/video/) is hooked in
    with a hard link in /media/REMOTIX/rete11/.c16-video/ (same
    disk: no copy) ⇒ /rete11/.c16-video/<label_name>."""
    if fpath.startswith(NETWORK11_BOX + "/"):
        return fpath, ""
    if fpath.startswith(NETWORK11_GUEST + "/"):
        return NETWORK11_BOX + fpath[len(NETWORK11_GUEST):], ""
    if not os.path.isfile(fpath):
        return None, "the video file %s is not on the host" % fpath
    folder = os.path.join(NETWORK11_GUEST, ".c16-video")
    os.makedirs(folder, exist_ok=True)
    dest = os.path.join(folder, os.path.basename(fpath))
    try:
        if not (os.path.exists(dest) and os.path.samefile(dest, fpath)):
            tmp = dest + ".%d" % os.getpid()
            os.link(fpath, tmp)
            os.replace(tmp, dest)
    except OSError as e:
        return None, "the video file cannot be hooked in %s: %s" % (folder, e)
    return NETWORK11_BOX + "/.c16-video/" + os.path.basename(fpath), ""


class WorkD(Work):
    label_name = "D"

    def __init__(self, expect):
        super().__init__(expect)
        self.kind, self.source = video_source(expect.o.video)
        self.t_video, self.stalled_for = None, None

    def prepare(self):
        self.prepare_pages()

    def start(self):
        if not self.kind:
            return False, self.source
        video = self.source if self.kind == "file" else ""
        if video:
            video, reason_text = video_in_box(video)
            if not video:
                return False, reason_text
            c, _t = self.inside("test -r %s" % video, 30)
            if c != 0:
                return False, "the video file %s cannot be read INSIDE the box" % video
        ok, t = self.server(video)
        if not ok:
            return False, "the server does not start: %s" % t[-200:]
        q = "yt=%s" % self.source if self.kind == "yt" else "file=1"
        c, t = self.internal_firefox("http://127.0.0.1:%d/video.html?%s" % (self.a.internal_port, q))
        if c != 0:
            return False, "firefox-esr does not launch: %s" % t[-200:]
        fine = time.time() + 90
        while time.time() < fine:
            self.read_video()
            if self.last_video.get("state") == 1 and (self.last_video.get("t") or 0) > 0:
                return True, "video %s %s playing: %s" % (self.kind, self.source,
                                                                 self.last_video)
            self.a.sleeps(2)
        return False, "the video did not start in 90 s: %s" % (self.last_video or "no row")

    def read_video(self):
        for now, kind, words in self.new_notebook():
            if kind != "video" or not words:
                continue
            if words[0] in ("yt", "file"):
                d = read_video(words)
                d["now"] = now
                self.last_video = d
            elif words[0] in ("failure", "quality"):
                self.a.event("video", body_text=" ".join(words))
        return self.last_video

    def step(self):
        R, M = self.a.rate, self.a.hands
        tl, ta = self.a.desktop
        before = self.last_video.get("t")
        self.a.sleeps(R.uniform(15, 40))
        v = self.read_video()
        after = v.get("t")
        advances = before is not None and after is not None and after != before
        self.a.verify("video_advances", advances, None,
                        "t %s→%s q=%s state=%s" % (before, after, v.get("q"), v.get("state")))
        if R.probable(0.3):
            # ⚠ only a movement, never a click: the click would stop the video
            M.move_to(tl * R.uniform(0.3, 0.7), ta * R.uniform(0.3, 0.7))
            self.a.tally("move_to")

    def extra(self):
        self.read_video()
        return {"video": dict(self.last_video)}


JOBS = {"A": WorkA, "B": WorkB, "C": WorkC, "D": WorkD}
