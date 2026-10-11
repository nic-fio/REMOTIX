#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f014 — F-014 CLIPBOARD, BROWSER → SESSION · F-015 CLIPBOARD, SESSION → BROWSER

    python3 15-f014-appunti.py --box kde --browser chrome [--fault]
    python3 15-f014-appunti.py --certify

THE SCENE (inside the tenant's session): `firefox-esr --kiosk` on a
page with an always-focused <textarea>, served by a small server
of the tenant's.  The page WRITES DOWN in a notebook every value of the field, every
`paste` and every `copy`; and it obeys two commands of the bench (empty / put a
selected text).  ⇒ The judgment is the FIELD VALUE of a real application
of the session, not a counter of the product.

F-014  browser → session.  A unique text (accents, €, ß, →, «») is put
       into the browser's clipboard as the user does: a field, REAL `Ctrl+C`
       (Marionette / `Input.dispatchKeyEvent`).  The field is removed, a click
       on the canvas (on the remote field), REAL `Ctrl+V` on the page ⇒ the scene's
       field must be EXACTLY that text.
       How the page reads it (src/pagina.html, «THE HIDDEN FIELD THAT GIVES
       BIRTH TO THE paste EVENT» and `clipboard_on_paste`): the `Ctrl+V` is NOT
       cancelled, it goes to the hidden field `#paste-field` ⇒ `paste` event
       (or the field's value) ⇒ CLIPBOARD_ANNOUNCE; on Chrome in addition the
       `clipboardchange` watch.  The `Ctrl+V` also goes towards the
       session, and it is the one that pastes into the application.
F-015  session → browser.  The unique text is put into the scene's field,
       selected, and REAL `Ctrl+C` is typed on the page (it goes to the session)
       ⇒ the compositor changes selection, the server announces, the page requests
       and writes with `navigator.clipboard.writeText` ⇒ the browser's clipboard
       must be EXACTLY that text, read with `readText()`:
         Chrome   permission given as the user would give it (Browser.grantPermissions
                  clipboardReadWrite + clipboardSanitizedWrite on the origin);
         Firefox  a real click (activation) and `readText()`; if Firefox shows
                  the little «Paste» button (SPECIFICHE.md §9: «There every read
                  costs the Paste menu») it is clicked like the user, and counted.
       ⚠ If the page could not write at once (`in_attesa_di_gesto`,
         declared in `write_to_clipboard`), the gesture the product asks for
         is made: a click on the page.  It is reported.

FAULT (same session, after the healthy pass), in both directions:
  «copy not made» — a NEW unique text as expectation, and the copy gesture is NOT
  made (F-014: no `Ctrl+C` in the browser; F-015: no `Ctrl+C` in the
  session).  The rest identical.  ⇒ it must give RED.
  «different expectation» — the value observed in the healthy pass judged against
  the same text without accents ⇒ it must give RED (the judge sees the accents).
"""
import base64
import json
import os
import secrets
import sys
import time
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

FUNCTIONS = ("F-014", "F-015")


def _sudo_password():
    """The server's sudo password: from REMOTIX_SUDO_PASSWORD, or from the «pass:» line of
    ~/SERVER.ssh (the same file as fondamenta/strumenti/sshpw.py). ⛔ Never written
    in the benches: they are in the repository."""
    p = os.environ.get("REMOTIX_SUDO_PASSWORD")
    if p is None:
        try:
            for r in open(os.path.expanduser("~/SERVER.ssh")):
                if r.startswith("pass:"):
                    p = r.split(":", 1)[1].strip()
                    break
        except OSError:
            pass
    return (p or "") + "\n"


# ⛔ ON THE SERVER THE COMMANDS IN THE BOX DO NOT GO THROUGH ssh — `[M]` 24 Sep 2026,
#   ten agents on the same server: `ssh` to itself closes the
#   connections («Connection closed by 192.168.0.2 port 22», MaxStartups) and
#   randomly lost a command of the scene — and the CLEAR-OUT, which left
#   the tenant alive.  ⇒ Here (and only in this process) `Box.inside` does
#   a direct `sudo podman exec`, with a retry.  To be proposed for suite.py.
def _inside_local(self, line, seconds=90):
    import subprocess
    for _attempt in range(3):
        try:
            r = subprocess.run(["sudo", "-S", "-p", "", "podman", "exec", self.container,
                                "sh", "-c", line], input=_sudo_password(), capture_output=True,
                               text=True, errors="replace", timeout=seconds)
        except subprocess.TimeoutExpired:
            return None, "(no answer in %d s)" % seconds
        if r.returncode == 125 and "Error" in (r.stderr or ""):     # podman itself
            time.sleep(1)
            continue
        text = r.stdout or ""
        if r.returncode != 0 and r.stderr:
            text += "\n" + r.stderr
        return r.returncode, text.strip()
    return None, (r.stderr or "").strip()


if os.environ.get("REMOTIX_ON_SERVER") == "1":
    S.C20V.Box.inside = _inside_local
WAIT_S = 12.0

# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def unique_text(tag):
    return "%s àèìòù €ß→ «ÀÉ» %s" % (tag, secrets.token_hex(4))


def strip_accents(t):
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def judge_text(expected, seen):
    """(outcome, why): PASS only if IDENTICAL, byte for byte."""
    if seen is None:
        return S.FAIL, "no value read"
    if seen == expected:
        return S.PASS, "identical (%d characters, %d bytes)" % (len(expected),
                                                             len(expected.encode()))
    if seen.strip() == expected:
        return S.FAIL, "equal except for spaces/newlines at the edges: %r" % seen[:80]
    if strip_accents(seen) == strip_accents(expected):
        return S.FAIL, "equal WITHOUT the accents: %r" % seen[:80]
    return S.FAIL, "different: %r instead of %r" % (seen[:80], expected[:80])


def certify():
    t = unique_text("F014")
    cases = [
        ("identical ⇒ PASS", judge_text(t, t)[0] == S.PASS),
        ("without accents ⇒ FAIL", judge_text(t, strip_accents(t))[0] == S.FAIL),
        ("the accents are really there", strip_accents(t) != t),
        ("trailing newline ⇒ FAIL", judge_text(t, t + "\n")[0] == S.FAIL),
        ("empty ⇒ FAIL", judge_text(t, "")[0] == S.FAIL),
        ("nothing ⇒ FAIL", judge_text(t, None)[0] == S.FAIL),
        ("two different unique texts", unique_text("X") != unique_text("X")),
        ("notebook: the last value", last_value(
            [("V", ""), ("P", "x"), ("V", "ab"), ("OK", 1)]) == "ab"),
        ("Ctrl+V is recognised", key_seen([("K", "Control ctrl"), ("K", "v ctrl")], "v")),
        ("a v without Ctrl does not count", not key_seen([("K", "v")], "v")),
    ]
    ok = True
    for name, real in cases:
        print("%s %s" % ("⭐" if real else "⛔", name))
        ok = ok and real
    return 0 if ok else 1


def key_seen(notebook, letter):
    """Did Ctrl+<letter> arrive as keydown at the scene's application?"""
    return ("K", "%s ctrl" % letter) in notebook or ("K", "%s ctrl" % letter.upper()) in notebook


def last_value(notebook, tag="V"):
    v = None
    for t, x in notebook:
        if t == tag:
            v = x
    return v


# ═══════════════════════════════════════════════════════════════════════════
#  THE SCENE IN THE SESSION
# ═══════════════════════════════════════════════════════════════════════════
PAGE = r"""<!doctype html><meta charset=utf-8><title>REMOTIX F014</title>
<style>
 html,body{margin:0;height:100%;background:#1c2a3a;overflow:hidden}
 #f{position:fixed;left:4vw;top:8vh;width:92vw;height:50vh;font:7vh/1.2 sans-serif;
    border:0;padding:2vh 2vw;box-sizing:border-box;background:#fff;color:#000;outline:0}
</style>
<textarea id=f autocomplete=off spellcheck=false></textarea>
<script>
const f=document.getElementById('f');
const m=(tag,x)=>fetch('/l',{method:'POST',body:tag+' '+JSON.stringify(x)}).catch(()=>0);
const v=()=>m('V',f.value);
f.focus(); m('caricata',location.href);
addEventListener('keydown',e=>m('K',e.key+(e.ctrlKey?' ctrl':'')));
f.addEventListener('input',v);
f.addEventListener('paste',e=>m('P',e.clipboardData?e.clipboardData.getData('text/plain'):null));
f.addEventListener('copy',()=>m('C',f.value.substring(f.selectionStart,f.selectionEnd)));
setInterval(async()=>{
  if(document.activeElement!==f) f.focus();
  try{const r=await fetch('/c'); if(r.status===200){const c=await r.json();
    if(c.pulisci) f.value='';
    if('metti' in c){f.value=c.metti; f.focus(); f.select();}
    v(); m('OK',c.n);}}catch(e){}
},300);
</script>"""

SERVER = r'''
import http.server, os, sys
PAG = open(sys.argv[2], "rb").read()
LOG, CMD = sys.argv[3], sys.argv[4]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.startswith("/c"):
            try:
                d = open(CMD, "rb").read(); os.unlink(CMD)
            except OSError:
                self.send_response(204); self.end_headers(); return
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.end_headers(); self.wfile.write(d); return
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers(); self.wfile.write(PAG)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        t = self.rfile.read(n).decode("utf-8", "replace").replace("\n", "\\n")
        with open(LOG, "a", encoding="utf-8") as f: f.write(t + "\n")
        self.send_response(204); self.end_headers()
http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
'''


# ⚠ Not the SYSTEM proxy: on GNOME Firefox asks the portal/gsettings for it.
PREFERENCES = S.C21.PREFERENCES + 'user_pref("network.proxy.type", 0);\n'


# ⛔ AND THE CACHE IN THE HOME, not in ~/.cache: `[M]` 24 Sep 2026, in the gnome
#   box `~/.cache` is a link to /tmp, and /tmp/mozilla belonged to a dead
#   uid (4016, sticky) ⇒ «Your Firefox profile cannot be loaded» and the scene
#   does not start.  The same trap as C2/C17.
class Scene:
    def __init__(self, s, port):
        self.s, self.sc, self.chi, self.port = s, s.sc, s.chi, port
        self.h = "/home/%s" % self.chi
        self.n = 0

    def turn_on(self):
        b = lambda x: base64.b64encode(x.encode()).decode()     # noqa: E731
        c, t = self.sc.inside(
            "set -e; h={h}; mkdir -p $h/f014-profilo $h/f014-cache; "
            "echo {srv} | base64 -d > $h/f014-servitore.py; echo {pag} | base64 -d > $h/f014.html; "
            "echo {pref} | base64 -d > $h/f014-profilo/user.js; : > $h/f014.log; rm -f $h/.f014-cmd; "
            "chown -R {c}: $h/f014-profilo $h/f014-cache $h/f014-servitore.py $h/f014.html $h/f014.log; set +e; "
            "u=$(id -u {c}); "
            "setsid runuser -u {c} -- python3 $h/f014-servitore.py {p} $h/f014.html $h/f014.log "
            "$h/.f014-cmd </dev/null >$h/.f014-servitore.log 2>&1 & "
            "d=''; for i in $(seq 1 40); do d=$(ls /run/user/$u 2>/dev/null | "
            "grep -E '^wayland-[0-9]+$' | head -1); [ -n \"$d\" ] && break; sleep 0.5; done; "
            "[ -n \"$d\" ] || {{ echo 'no wayland socket'; exit 2; }}; sleep 1; "
            "setsid runuser -u {c} -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
            "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
            "XDG_SESSION_TYPE=wayland HOME=$h XDG_CACHE_HOME=$h/f014-cache "
            "firefox-esr --no-remote --new-instance "
            "--profile $h/f014-profilo --kiosk http://127.0.0.1:{p}/ "
            "</dev/null >$h/.f014-firefox.log 2>&1 & "
            "for i in $(seq 1 200); do grep -q caricata $h/f014.log && {{ echo accesa; exit 0; }}; "
            "sleep 0.5; done; echo 'the scene did not say «caricata»'; "
            "echo --ff; tail -n 8 $h/.f014-firefox.log; echo --srv; tail -n 5 $h/.f014-servitore.log; "
            "echo --ps; ps -u {c} -o pid,args | cut -c1-150 | tail -n 25; echo --run; ls /run/user/$u; "
            "echo --curl; python3 -c \"import urllib.request as u; "
            "print(len(u.urlopen('http://127.0.0.1:{p}/', timeout=3).read()))\" 2>&1 | tail -n 1; exit 1"
            .format(h=self.h, c=self.chi, p=self.port, srv=b(SERVER), page_map=b(PAGE),
                    pref=b(PREFERENCES)), 180)
        return c == 0, t

    def turn_off(self):
        """The scene's server and firefox-esr go away BEFORE the clear-out."""
        self.sc.inside("pkill -KILL -u %s -f 'f014' 2>/dev/null; sleep 0.3; "
                       "pkill -KILL -u %s -f 'f014' 2>/dev/null; true" % (self.chi, self.chi), 30)

    def notebook(self):
        """[(tag, value)] — the scene's notebook, whole."""
        _c, t = self.sc.inside("base64 -w0 %s/f014.log 2>/dev/null" % self.h, 30)
        try:
            text = base64.b64decode((t or "").strip().splitlines()[-1]).decode("utf-8")
        except Exception:                        # noqa: BLE001
            return []
        lines = []
        for r in text.splitlines():
            tag, _, rest = r.partition(" ")
            try:
                lines.append((tag, json.loads(rest)))
            except ValueError:
                lines.append((tag, rest))
        return lines

    def in_charge(self, **cmd):
        """A command to the scene; waits for its «OK».  Returns the notebook afterwards."""
        self.n += 1
        cmd["n"] = self.n
        d = base64.b64encode(json.dumps(cmd).encode()).decode()
        self.sc.inside("echo %s | base64 -d > %s/.f014-cmd.tmp && chown %s: %s/.f014-cmd.tmp "
                       "&& mv %s/.f014-cmd.tmp %s/.f014-cmd"
                       % (d, self.h, self.chi, self.h, self.h, self.h), 30)
        fine = time.time() + 12
        while time.time() < fine:
            q = self.notebook()
            if ("OK", self.n) in q:
                return q
            time.sleep(0.5)
        _c, queue = self.sc.inside("tail -c 600 %s/f014.log; ls -la %s/.f014-cmd* 2>&1; "
                                  "tail -n 3 %s/.f014-servitore.log" % (self.h, self.h, self.h), 30)
        raise S.Blocked("the scene did not execute command n=%d in 12 s (notebook: %d lines; "
                         "tail: %s)" % (self.n, len(q), (queue or "")[-500:]))

    def wait_value(self, expected, da, cap=WAIT_S):
        """Watches the field until it is `expected` or the time runs out.  Returns (value, new notebook)."""
        fine = time.time() + cap
        while True:
            q = self.notebook()[da:]
            v = last_value(q)
            if v == expected or time.time() >= fine:
                return v, q
            time.sleep(1.0)


# ═══════════════════════════════════════════════════════════════════════════
#  THE REAL GESTURES
# ═══════════════════════════════════════════════════════════════════════════
def ctrl(g, letter):
    """Ctrl+<letter> with REAL keys (trusted browser events)."""
    if hasattr(g, "cdp"):
        c = g.cdp
        vk = ord(letter.upper())
        c.call("Input.dispatchKeyEvent", type="rawKeyDown", key="Control",
                 code="ControlLeft", windowsVirtualKeyCode=17, modifiers=2)
        time.sleep(0.06)
        c.call("Input.dispatchKeyEvent", type="rawKeyDown", key=letter,
                 code="Key" + letter.upper(), windowsVirtualKeyCode=vk, modifiers=2)
        time.sleep(0.08)
        c.call("Input.dispatchKeyEvent", type="keyUp", key=letter,
                 code="Key" + letter.upper(), windowsVirtualKeyCode=vk, modifiers=2)
        time.sleep(0.06)
        c.call("Input.dispatchKeyEvent", type="keyUp", key="Control",
                 code="ControlLeft", windowsVirtualKeyCode=17, modifiers=0)
        return
    g.m.call("WebDriver:PerformActions", {"actions": [{
        "type": "key", "id": "tastiera", "actions": [
            {"type": "keyDown", "value": ""}, {"type": "pause", "duration": 60},
            {"type": "keyDown", "value": letter}, {"type": "pause", "duration": 80},
            {"type": "keyUp", "value": letter}, {"type": "pause", "duration": 60},
            {"type": "keyUp", "value": ""}]}]})
    g.m.call("WebDriver:ReleaseActions")


def letter(g, x):
    if hasattr(g, "cdp"):
        vk = ord(x.upper())
        g.cdp.call("Input.dispatchKeyEvent", type="keyDown", key=x, code="Key" + x.upper(),
                     windowsVirtualKeyCode=vk, text=x, unmodifiedText=x)
        time.sleep(0.08)
        g.cdp.call("Input.dispatchKeyEvent", type="keyUp", key=x, code="Key" + x.upper(),
                     windowsVirtualKeyCode=vk)
        return
    g.m.call("WebDriver:PerformActions", {"actions": [{
        "type": "key", "id": "tastiera", "actions": [
            {"type": "keyDown", "value": x}, {"type": "pause", "duration": 80},
            {"type": "keyUp", "value": x}]}]})
    g.m.call("WebDriver:ReleaseActions")


OPEN_FIELD = """
  let t = document.getElementById('__f014');
  if (!t) { t = document.createElement('textarea'); t.id = '__f014';
    t.style.cssText = 'position:fixed;left:20px;top:20px;width:600px;height:60px;z-index:99999';
    document.body.appendChild(t); }
  t.value = arguments[0]; t.focus(); t.select();
  return document.activeElement === t;
"""
CLOSE_FIELD = """
  const t = document.getElementById('__f014'); if (t) t.remove(); return true;
"""
CLIPBOARD_STATE = """
  const A = window.REMOTIX && window.REMOTIX.clipboard;
  if (!A) return null;
  return {on: A.on, watched: A.watched || '', counts: A.counts,
          in_attesa: A.awaiting_gesture !== null, own_id: A.own_id, peer_id: A.peer_id};
"""
DIARY = """
  const r = document.getElementById('logbook');
  const t = r ? r.textContent : '';
  return t.split('\\n').filter(x => /clipboard|CLIPBOARD|paste|Ctrl\\+V|readText|§9/.test(x)).slice(-25);
"""
READ_LAUNCH = """
  window.__f015 = {fatto: false};
  try {
    navigator.clipboard.readText().then(
      t => { window.__f015 = {fatto: true, testo: t}; },
      e => { window.__f015 = {fatto: true, errore: String(e)}; });
  } catch (e) { window.__f015 = {fatto: true, errore: 'exception: ' + e}; }
"""


def js_page(g, body):
    """A body executed IN the page (on Firefox with <script>, not in the sandbox)."""
    if hasattr(g, "cdp"):
        return g.js(body + "; return true;")
    return g.js(S.VERI._inject(body))


def read_browser_clipboard(g, s, geo):
    """(text | None, notes) — the browser's clipboard, with `readText()`."""
    note = []
    if not hasattr(g, "cdp"):
        # ⭐ the activation: a real click on the canvas (it goes to the remote field: harmless)
        x, y = S.C21.desktop_to_glass(geo, geo["tl"] * 0.5, geo["ta"] * 0.75)
        g.click(x, y)
        time.sleep(0.3)
    js_page(g, READ_LAUNCH)
    fine = time.time() + 8
    small_button = 0
    while time.time() < fine:
        r = g.js("return window.__f015 || null;") or {}
        if r.get("done"):
            if "error" in r:
                note.append("readText denied: %s" % r["error"])
                return None, note
            return r.get("text"), note
        if not hasattr(g, "cdp") and not small_button and click_paste_panel(g):
            small_button += 1
            note.append("Firefox asked for the little «Paste» button (SPECIFICHE §9): "
                        "clicked like the user")
        time.sleep(0.3)
    note.append("readText did not answer in 8 s")
    return None, note


def click_paste_panel(g):
    """Firefox's «Paste» panel (07-b56): clicks it if it is open."""
    outcome = None
    try:
        g.m.call("Marionette:SetContext", {"value": "chrome"})
        r = g.m.call("WebDriver:ExecuteScript", {"script": """
            const w = Services.wm.getMostRecentWindow('navigator:browser');
            if (!w) return 'niente-finestra';
            const p = w.document.getElementById('clipboardReadPasteMenuPopup');
            if (!p) return 'niente-pannello';
            if (p.state !== 'open' && p.state !== 'showing') return p.state;
            const v = p.querySelector('menuitem');
            if (!v) return 'aperto-senza-voce';
            v.doCommand(); p.hidePopup(); return 'cliccato';""",
            "args": [], "sandbox": "system"})
        outcome = (r or {}).get("value")
    except Exception as e:                       # noqa: BLE001
        outcome = "fault: %s" % e
    finally:
        try:
            g.m.call("Marionette:SetContext", {"value": "content"})
        except Exception:                        # noqa: BLE001
            pass
    return outcome == "cliccato"


# ═══════════════════════════════════════════════════════════════════════════
#  THE TWO DIRECTIONS
# ═══════════════════════════════════════════════════════════════════════════
def browser_to_session(s, scene, geo, text, copied=True):
    """F-014: returns (value of the remote field, details)."""
    g = s.g
    scene.in_charge(clean=True)
    da = len(scene.notebook())
    det = {"copy_done": copied}
    if copied:
        det["focused_field"] = g.js(OPEN_FIELD, text)
        time.sleep(0.3)
        ctrl(g, "c")                       # ⭐ the REAL copy in the browser
        time.sleep(0.8)
        g.js(CLOSE_FIELD)
    # the click on the remote field (focus in the session) and then the real Ctrl+V
    x, y = S.C21.desktop_to_glass(geo, geo["tl"] * 0.5, geo["ta"] * 0.3)
    g.click(x, y)
    time.sleep(1.0)
    det["state_before"] = g.js(CLIPBOARD_STATE)
    ctrl(g, "v")
    seen, q = scene.wait_value(text, da)
    if seen != text and not key_seen(q, "v"):
        # ⚠ the Ctrl+V did not REACH the application (session focus):
        #   the user types it again.  It is declared.  `[M]` gnome/chrome, one time in three.
        det["riprova_ctrl_v"] = True
        g.click(x, y)
        time.sleep(1.0)
        ctrl(g, "v")
        seen, q = scene.wait_value(text, da)
    det["gesture_arrived"] = key_seen(q, "v")
    det["notebook"] = q[-12:]
    det["state_after"] = g.js(CLIPBOARD_STATE)
    det["diary"] = g.js(DIARY)
    return seen, det


def session_to_browser(s, scene, geo, text, copied=True):
    """F-015: returns (text in the browser's clipboard, details)."""
    g = s.g
    q = scene.in_charge(put=text)
    det = {"copy_done": copied, "remote_field": last_value(q)}
    if det["remote_field"] != text:
        raise S.Blocked("the scene did not take the text to copy: %r"
                         % (det["remote_field"],))
    before = (g.js(CLIPBOARD_STATE) or {}).get("counts") or {}
    da = len(q)
    if copied:
        ctrl(g, "c")                       # ⭐ the REAL copy in the session
        fine = time.time() + 5
        while time.time() < fine and not key_seen(scene.notebook()[da:], "c"):
            time.sleep(0.7)
        if not key_seen(scene.notebook()[da:], "c"):
            det["riprova_ctrl_c"] = True     # the user types it again, and it is declared
            scene.in_charge(put=text)
            ctrl(g, "c")
            time.sleep(1.5)
        det["gesture_arrived"] = key_seen(scene.notebook()[da:], "c")
    # waits for the text to reach the page (diagnosis, not judgment)
    fine = time.time() + 8
    st = {}
    while time.time() < fine:
        st = g.js(CLIPBOARD_STATE) or {}
        c = st.get("counts") or {}
        if c.get("received", 0) > before.get("received", 0) and (
                c.get("written", 0) > before.get("written", 0) or st.get("waiting")):
            break
        time.sleep(0.4)
    det["state_after_copy"] = st
    det["copy_in_session"] = [x for t, x in scene.notebook()[da:] if t == "C"]
    if st.get("waiting"):
        # ⚠ the product declares it: «set aside, it goes there at the first click»
        det["gesto_chiesto_dal_prodotto"] = True
        x, y = S.C21.desktop_to_glass(geo, geo["tl"] * 0.5, geo["ta"] * 0.75)
        s.g.click(x, y)
        time.sleep(1.0)
        det["stato_dopo_gesto"] = g.js(CLIPBOARD_STATE)
    read, note = read_browser_clipboard(g, s, geo)
    det["reading_notes"] = note
    det["diary"] = g.js(DIARY)
    return read, det


def body(o, E):
    scene_port = o.base_port + 5
    with S.Session(o, "014", E) as s:
        g = s.g
        if o.browser in ("chrome", "phone"):
            # ⭐ the permission, as the user would give it by clicking «Allow»
            origin = o.url.rstrip("/")
            try:
                g.cdp.call("Browser.grantPermissions", origin=origin,
                             permissions=["clipboardReadWrite", "clipboardSanitizedWrite"])
                print("   clipboard permission granted to %s" % origin, flush=True)
            except Exception as e:               # noqa: BLE001
                print("   ⚠ permission NOT granted: %s" % e, flush=True)
        sign = s.log_mark()
        ok, m = s.enter()
        if not ok:
            raise S.Blocked(m)
        geo = s.geometry()
        if not geo:
            raise S.Blocked("the canvas geometry is not there")
        st = g.js(CLIPBOARD_STATE)
        print("   page clipboard: %s" % json.dumps(st, ensure_ascii=False), flush=True)
        if not st or not st.get("on"):
            E.put("F-014", S.FAIL, "the page's clipboard is not on: %s" % st)
            E.put("F-015", S.FAIL, "the page's clipboard is not on: %s" % st)
            return
        print("   wake-up: %s" % S.C21.wake(g, geo), flush=True)
        scene = Scene(s, scene_port)
        try:
            inside_scene(o, E, s, g, geo, scene, sign)
        finally:
            scene.turn_off()


def inside_scene(o, E, s, g, geo, scene, sign):
    ok, t = scene.turn_on()
    print("   scene: %s" % ((t or "?").splitlines() or ["?"])[-1], flush=True)
    if not ok:
        print(t, flush=True)
        s.photo("scena-non-accesa")
        raise S.Blocked("the scene does not start: %s" % (t or "")[-300:])
    time.sleep(3)
    # ⛔ poor man's check: does the keyboard reach the remote field?  (if not, it is not F-014)
    x, y = S.C21.desktop_to_glass(geo, geo["tl"] * 0.5, geo["ta"] * 0.3)
    g.click(x, y)
    time.sleep(1.0)
    scene.in_charge(clean=True)
    da = len(scene.notebook())
    letter(g, "q")
    v, _q = scene.wait_value("q", da, 8)
    if v != "q":
        raise S.Blocked("the keyboard does not reach the scene's field (a «q» typed ⇒ %r):"
                         " the paste cannot be looked at" % (v,))

    # ── F-014 healthy ──────────────────────────────────────────────────
    t14 = unique_text("F014")
    seen14, d14 = browser_to_session(s, scene, geo, t14)
    png, dove = s.photo("f014-sana")
    ev14 = [dove] if dove else []
    ev14.append(s.save_text("f014-sana.json", json.dumps(d14, ensure_ascii=False,
                                                           indent=1)))
    e, why = judge_text(t14, seen14)
    if e == S.FAIL and not d14.get("gesture_arrived"):
        e, why = S.BLOCKED, ("the Ctrl+V did not reach the session's application "
                                "(no keydown, even typed again): it is the keyboard, not the "
                                "clipboard — " + why)
    if d14.get("riprova_ctrl_v"):
        why += " · (Ctrl+V typed again once)"
    E.put("F-014", e, why, expected=t14, observed=seen14, evidence=ev14)

    # ── F-015 healthy ──────────────────────────────────────────────────
    t15 = unique_text("F015")
    read15, d15 = session_to_browser(s, scene, geo, t15)
    ev15 = [s.save_text("f015-sana.json", json.dumps(d15, ensure_ascii=False,
                                                       indent=1))]
    e, why = judge_text(t15, read15)
    if e == S.FAIL and not d15.get("gesture_arrived"):
        e, why = S.BLOCKED, ("the Ctrl+C did not reach the session's application "
                                "(no keydown, even typed again): it is the keyboard, not the "
                                "clipboard — " + why)
    if d15.get("riprova_ctrl_c"):
        why += " · (Ctrl+C typed again once)"
    if e == S.FAIL and read15 is None and any("button" in n or "denied" in n
                                                for n in d15.get("reading_notes", [])):
        why += " · " + "; ".join(d15["reading_notes"])
    if d15.get("gesto_chiesto_dal_prodotto"):
        why += " · (the page asked for a gesture: a click made, §9)"
    E.put("F-015", e, why, expected=t15, observed=read15, evidence=ev15)

    if o.fault:
        # different expectation: the judge on the real values, against the text without accents
        ad14 = judge_text(strip_accents(t14), seen14)[0] == S.FAIL
        ad15 = judge_text(strip_accents(t15), read15)[0] == S.FAIL
        # copy not made, F-014
        g14 = unique_text("F014G")
        vg14, dg14 = browser_to_session(s, scene, geo, g14, copied=False)
        s.save_text("f014-guasto.json", json.dumps(dg14, ensure_ascii=False, indent=1))
        r14 = judge_text(g14, vg14)[0] == S.FAIL
        seen_g14 = (r14 and ad14) if dg14.get("gesture_arrived") else None
        E.fault("F-014", seen_g14,
                 "copy not made ⇒ the remote field is %r (%s); expected without accents ⇒ %s"
                 % ((vg14 or "")[:50], "RED" if r14 else "GREEN",
                    "RED" if ad14 else "GREEN"), expected=g14, observed=vg14)
        g15 = unique_text("F015G")
        vg15, dg15 = session_to_browser(s, scene, geo, g15, copied=False)
        s.save_text("f015-guasto.json", json.dumps(dg15, ensure_ascii=False, indent=1))
        r15 = judge_text(g15, vg15)[0] == S.FAIL
        E.fault("F-015", r15 and ad15,
                 "copy not made ⇒ the browser's clipboard is %r (%s); expected without "
                 "accents ⇒ %s" % ((vg15 or "")[:50], "RED" if r15 else "GREEN",
                                   "RED" if ad15 else "GREEN"),
                 expected=g15, observed=vg15)
    s.save_text("server-f014.txt", s.log_from(sign) if sign is not None else [])
    s.save_console()


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify))
