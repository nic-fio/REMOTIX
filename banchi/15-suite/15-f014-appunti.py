#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f014 — F-014 CLIPBOARD, BROWSER → SESSION · F-015 CLIPBOARD, SESSION → BROWSER

    python3 15-f014-appunti.py --scatola kde --browser chrome [--guasto]
    python3 15-f014-appunti.py --certifica

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
       BIRTH TO THE paste EVENT» and `appunti_su_incolla`): the `Ctrl+V` is NOT
       cancelled, it goes to the hidden field `#incolla-nascosto` ⇒ `paste` event
       (or the field's value) ⇒ APPUNTI_ANNUNCIO; on Chrome in addition the
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
         declared in `scrivi_negli_appunti`), the gesture the product asks for
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

FUNZIONI = ("F-014", "F-015")


def _parola_sudo():
    """The server's sudo password: from REMOTIX_PAROLA_SUDO, or from the «pass:» line of
    ~/SERVER.ssh (the same file as fondamenta/strumenti/sshpw.py). ⛔ Never written
    in the benches: they are in the repository."""
    p = os.environ.get("REMOTIX_PAROLA_SUDO")
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
#   the tenant alive.  ⇒ Here (and only in this process) `Scatola.dentro` does
#   a direct `sudo podman exec`, with a retry.  To be proposed for suite.py.
def _dentro_locale(self, riga, secondi=90):
    import subprocess
    for _tentativo in range(3):
        try:
            r = subprocess.run(["sudo", "-S", "-p", "", "podman", "exec", self.contenitore,
                                "sh", "-c", riga], input=_parola_sudo(), capture_output=True,
                               text=True, errors="replace", timeout=secondi)
        except subprocess.TimeoutExpired:
            return None, "(no answer in %d s)" % secondi
        if r.returncode == 125 and "Error" in (r.stderr or ""):     # podman itself
            time.sleep(1)
            continue
        testo = r.stdout or ""
        if r.returncode != 0 and r.stderr:
            testo += "\n" + r.stderr
        return r.returncode, testo.strip()
    return None, (r.stderr or "").strip()


if os.environ.get("REMOTIX_SUL_SERVER") == "1":
    S.C20V.Scatola.dentro = _dentro_locale
ATTESA_S = 12.0

# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def testo_unico(sigla):
    return "%s àèìòù €ß→ «ÀÉ» %s" % (sigla, secrets.token_hex(4))


def senza_accenti(t):
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def giudica_testo(atteso, visto):
    """(outcome, why): PASS only if IDENTICAL, byte for byte."""
    if visto is None:
        return S.FAIL, "no value read"
    if visto == atteso:
        return S.PASS, "identical (%d characters, %d bytes)" % (len(atteso),
                                                             len(atteso.encode()))
    if visto.strip() == atteso:
        return S.FAIL, "equal except for spaces/newlines at the edges: %r" % visto[:80]
    if senza_accenti(visto) == senza_accenti(atteso):
        return S.FAIL, "equal WITHOUT the accents: %r" % visto[:80]
    return S.FAIL, "different: %r instead of %r" % (visto[:80], atteso[:80])


def certifica():
    t = testo_unico("F014")
    casi = [
        ("identical ⇒ PASS", giudica_testo(t, t)[0] == S.PASS),
        ("without accents ⇒ FAIL", giudica_testo(t, senza_accenti(t))[0] == S.FAIL),
        ("the accents are really there", senza_accenti(t) != t),
        ("trailing newline ⇒ FAIL", giudica_testo(t, t + "\n")[0] == S.FAIL),
        ("empty ⇒ FAIL", giudica_testo(t, "")[0] == S.FAIL),
        ("nothing ⇒ FAIL", giudica_testo(t, None)[0] == S.FAIL),
        ("two different unique texts", testo_unico("X") != testo_unico("X")),
        ("notebook: the last value", ultimo_valore(
            [("V", ""), ("P", "x"), ("V", "ab"), ("OK", 1)]) == "ab"),
        ("Ctrl+V is recognised", tasto_visto([("K", "Control ctrl"), ("K", "v ctrl")], "v")),
        ("a v without Ctrl does not count", not tasto_visto([("K", "v")], "v")),
    ]
    ok = True
    for nome, vero in casi:
        print("%s %s" % ("⭐" if vero else "⛔", nome))
        ok = ok and vero
    return 0 if ok else 1


def tasto_visto(quaderno, lettera):
    """Did Ctrl+<letter> arrive as keydown at the scene's application?"""
    return ("K", "%s ctrl" % lettera) in quaderno or ("K", "%s ctrl" % lettera.upper()) in quaderno


def ultimo_valore(quaderno, tag="V"):
    v = None
    for t, x in quaderno:
        if t == tag:
            v = x
    return v


# ═══════════════════════════════════════════════════════════════════════════
#  THE SCENE IN THE SESSION
# ═══════════════════════════════════════════════════════════════════════════
PAGINA = r"""<!doctype html><meta charset=utf-8><title>REMOTIX F014</title>
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

SERVITORE = r'''
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
PREFERENZE = S.C21.PREFERENZE + 'user_pref("network.proxy.type", 0);\n'


# ⛔ AND THE CACHE IN THE HOME, not in ~/.cache: `[M]` 24 Sep 2026, in the gnome
#   box `~/.cache` is a link to /tmp, and /tmp/mozilla belonged to a dead
#   uid (4016, sticky) ⇒ «Your Firefox profile cannot be loaded» and the scene
#   does not start.  The same trap as C2/C17.
class Scena:
    def __init__(self, s, porta):
        self.s, self.sc, self.chi, self.porta = s, s.sc, s.chi, porta
        self.h = "/home/%s" % self.chi
        self.n = 0

    def accendi(self):
        b = lambda x: base64.b64encode(x.encode()).decode()     # noqa: E731
        c, t = self.sc.dentro(
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
            .format(h=self.h, c=self.chi, p=self.porta, srv=b(SERVITORE), pag=b(PAGINA),
                    pref=b(PREFERENZE)), 180)
        return c == 0, t

    def spegni(self):
        """The scene's server and firefox-esr go away BEFORE the clear-out."""
        self.sc.dentro("pkill -KILL -u %s -f 'f014' 2>/dev/null; sleep 0.3; "
                       "pkill -KILL -u %s -f 'f014' 2>/dev/null; true" % (self.chi, self.chi), 30)

    def quaderno(self):
        """[(tag, value)] — the scene's notebook, whole."""
        _c, t = self.sc.dentro("base64 -w0 %s/f014.log 2>/dev/null" % self.h, 30)
        try:
            testo = base64.b64decode((t or "").strip().splitlines()[-1]).decode("utf-8")
        except Exception:                        # noqa: BLE001
            return []
        righe = []
        for r in testo.splitlines():
            tag, _, resto = r.partition(" ")
            try:
                righe.append((tag, json.loads(resto)))
            except ValueError:
                righe.append((tag, resto))
        return righe

    def comanda(self, **cmd):
        """A command to the scene; waits for its «OK».  Returns the notebook afterwards."""
        self.n += 1
        cmd["n"] = self.n
        d = base64.b64encode(json.dumps(cmd).encode()).decode()
        self.sc.dentro("echo %s | base64 -d > %s/.f014-cmd.tmp && chown %s: %s/.f014-cmd.tmp "
                       "&& mv %s/.f014-cmd.tmp %s/.f014-cmd"
                       % (d, self.h, self.chi, self.h, self.h, self.h), 30)
        fine = time.time() + 12
        while time.time() < fine:
            q = self.quaderno()
            if ("OK", self.n) in q:
                return q
            time.sleep(0.5)
        _c, coda = self.sc.dentro("tail -c 600 %s/f014.log; ls -la %s/.f014-cmd* 2>&1; "
                                  "tail -n 3 %s/.f014-servitore.log" % (self.h, self.h, self.h), 30)
        raise S.Bloccata("the scene did not execute command n=%d in 12 s (notebook: %d lines; "
                         "tail: %s)" % (self.n, len(q), (coda or "")[-500:]))

    def aspetta_valore(self, atteso, da, tetto=ATTESA_S):
        """Watches the field until it is `atteso` or the time runs out.  Returns (value, new notebook)."""
        fine = time.time() + tetto
        while True:
            q = self.quaderno()[da:]
            v = ultimo_valore(q)
            if v == atteso or time.time() >= fine:
                return v, q
            time.sleep(1.0)


# ═══════════════════════════════════════════════════════════════════════════
#  THE REAL GESTURES
# ═══════════════════════════════════════════════════════════════════════════
def ctrl(g, lettera):
    """Ctrl+<letter> with REAL keys (trusted browser events)."""
    if hasattr(g, "cdp"):
        c = g.cdp
        vk = ord(lettera.upper())
        c.chiama("Input.dispatchKeyEvent", type="rawKeyDown", key="Control",
                 code="ControlLeft", windowsVirtualKeyCode=17, modifiers=2)
        time.sleep(0.06)
        c.chiama("Input.dispatchKeyEvent", type="rawKeyDown", key=lettera,
                 code="Key" + lettera.upper(), windowsVirtualKeyCode=vk, modifiers=2)
        time.sleep(0.08)
        c.chiama("Input.dispatchKeyEvent", type="keyUp", key=lettera,
                 code="Key" + lettera.upper(), windowsVirtualKeyCode=vk, modifiers=2)
        time.sleep(0.06)
        c.chiama("Input.dispatchKeyEvent", type="keyUp", key="Control",
                 code="ControlLeft", windowsVirtualKeyCode=17, modifiers=0)
        return
    g.m.chiama("WebDriver:PerformActions", {"actions": [{
        "type": "key", "id": "tastiera", "actions": [
            {"type": "keyDown", "value": ""}, {"type": "pause", "duration": 60},
            {"type": "keyDown", "value": lettera}, {"type": "pause", "duration": 80},
            {"type": "keyUp", "value": lettera}, {"type": "pause", "duration": 60},
            {"type": "keyUp", "value": ""}]}]})
    g.m.chiama("WebDriver:ReleaseActions")


def lettera(g, x):
    if hasattr(g, "cdp"):
        vk = ord(x.upper())
        g.cdp.chiama("Input.dispatchKeyEvent", type="keyDown", key=x, code="Key" + x.upper(),
                     windowsVirtualKeyCode=vk, text=x, unmodifiedText=x)
        time.sleep(0.08)
        g.cdp.chiama("Input.dispatchKeyEvent", type="keyUp", key=x, code="Key" + x.upper(),
                     windowsVirtualKeyCode=vk)
        return
    g.m.chiama("WebDriver:PerformActions", {"actions": [{
        "type": "key", "id": "tastiera", "actions": [
            {"type": "keyDown", "value": x}, {"type": "pause", "duration": 80},
            {"type": "keyUp", "value": x}]}]})
    g.m.chiama("WebDriver:ReleaseActions")


CAMPO_APRI = """
  let t = document.getElementById('__f014');
  if (!t) { t = document.createElement('textarea'); t.id = '__f014';
    t.style.cssText = 'position:fixed;left:20px;top:20px;width:600px;height:60px;z-index:99999';
    document.body.appendChild(t); }
  t.value = arguments[0]; t.focus(); t.select();
  return document.activeElement === t;
"""
CAMPO_CHIUDI = """
  const t = document.getElementById('__f014'); if (t) t.remove(); return true;
"""
STATO_APPUNTI = """
  const A = window.REMOTIX && window.REMOTIX.appunti;
  if (!A) return null;
  return {acceso: A.acceso, sorvegliata: A.sorvegliata || '', conti: A.conti,
          in_attesa: A.in_attesa_di_gesto !== null, mio_id: A.mio_id, suo_id: A.suo_id};
"""
DIARIO = """
  const r = document.getElementById('registro');
  const t = r ? r.textContent : '';
  return t.split('\\n').filter(x => /clipboard|APPUNTI|paste|Ctrl\\+V|readText|§9/.test(x)).slice(-25);
"""
LEGGI_LANCIA = """
  window.__f015 = {fatto: false};
  try {
    navigator.clipboard.readText().then(
      t => { window.__f015 = {fatto: true, testo: t}; },
      e => { window.__f015 = {fatto: true, errore: String(e)}; });
  } catch (e) { window.__f015 = {fatto: true, errore: 'exception: ' + e}; }
"""


def js_pagina(g, corpo):
    """A body executed IN the page (on Firefox with <script>, not in the sandbox)."""
    if hasattr(g, "cdp"):
        return g.js(corpo + "; return true;")
    return g.js(S.VERI._inietta(corpo))


def leggi_appunti_browser(g, s, geo):
    """(text | None, notes) — the browser's clipboard, with `readText()`."""
    note = []
    if not hasattr(g, "cdp"):
        # ⭐ the activation: a real click on the canvas (it goes to the remote field: harmless)
        x, y = S.C21.dal_desktop_al_vetro(geo, geo["tl"] * 0.5, geo["ta"] * 0.75)
        g.clic(x, y)
        time.sleep(0.3)
    js_pagina(g, LEGGI_LANCIA)
    fine = time.time() + 8
    bottoncino = 0
    while time.time() < fine:
        r = g.js("return window.__f015 || null;") or {}
        if r.get("fatto"):
            if "errore" in r:
                note.append("readText denied: %s" % r["errore"])
                return None, note
            return r.get("testo"), note
        if not hasattr(g, "cdp") and not bottoncino and paga_il_bottoncino(g):
            bottoncino += 1
            note.append("Firefox asked for the little «Paste» button (SPECIFICHE §9): "
                        "clicked like the user")
        time.sleep(0.3)
    note.append("readText did not answer in 8 s")
    return None, note


def paga_il_bottoncino(g):
    """Firefox's «Paste» panel (07-b56): clicks it if it is open."""
    esito = None
    try:
        g.m.chiama("Marionette:SetContext", {"value": "chrome"})
        r = g.m.chiama("WebDriver:ExecuteScript", {"script": """
            const w = Services.wm.getMostRecentWindow('navigator:browser');
            if (!w) return 'niente-finestra';
            const p = w.document.getElementById('clipboardReadPasteMenuPopup');
            if (!p) return 'niente-pannello';
            if (p.state !== 'open' && p.state !== 'showing') return p.state;
            const v = p.querySelector('menuitem');
            if (!v) return 'aperto-senza-voce';
            v.doCommand(); p.hidePopup(); return 'cliccato';""",
            "args": [], "sandbox": "system"})
        esito = (r or {}).get("value")
    except Exception as e:                       # noqa: BLE001
        esito = "fault: %s" % e
    finally:
        try:
            g.m.chiama("Marionette:SetContext", {"value": "content"})
        except Exception:                        # noqa: BLE001
            pass
    return esito == "cliccato"


# ═══════════════════════════════════════════════════════════════════════════
#  THE TWO DIRECTIONS
# ═══════════════════════════════════════════════════════════════════════════
def verso_browser_sessione(s, scena, geo, testo, copia=True):
    """F-014: returns (value of the remote field, details)."""
    g = s.g
    scena.comanda(pulisci=True)
    da = len(scena.quaderno())
    det = {"copia_fatta": copia}
    if copia:
        det["campo_a_fuoco"] = g.js(CAMPO_APRI, testo)
        time.sleep(0.3)
        ctrl(g, "c")                       # ⭐ the REAL copy in the browser
        time.sleep(0.8)
        g.js(CAMPO_CHIUDI)
    # the click on the remote field (focus in the session) and then the real Ctrl+V
    x, y = S.C21.dal_desktop_al_vetro(geo, geo["tl"] * 0.5, geo["ta"] * 0.3)
    g.clic(x, y)
    time.sleep(1.0)
    det["stato_prima"] = g.js(STATO_APPUNTI)
    ctrl(g, "v")
    visto, q = scena.aspetta_valore(testo, da)
    if visto != testo and not tasto_visto(q, "v"):
        # ⚠ the Ctrl+V did not REACH the application (session focus):
        #   the user types it again.  It is declared.  `[M]` gnome/chrome, one time in three.
        det["riprova_ctrl_v"] = True
        g.clic(x, y)
        time.sleep(1.0)
        ctrl(g, "v")
        visto, q = scena.aspetta_valore(testo, da)
    det["gesto_arrivato"] = tasto_visto(q, "v")
    det["quaderno"] = q[-12:]
    det["stato_dopo"] = g.js(STATO_APPUNTI)
    det["diario"] = g.js(DIARIO)
    return visto, det


def verso_sessione_browser(s, scena, geo, testo, copia=True):
    """F-015: returns (text in the browser's clipboard, details)."""
    g = s.g
    q = scena.comanda(metti=testo)
    det = {"copia_fatta": copia, "campo_remoto": ultimo_valore(q)}
    if det["campo_remoto"] != testo:
        raise S.Bloccata("the scene did not take the text to copy: %r"
                         % (det["campo_remoto"],))
    prima = (g.js(STATO_APPUNTI) or {}).get("conti") or {}
    da = len(q)
    if copia:
        ctrl(g, "c")                       # ⭐ the REAL copy in the session
        fine = time.time() + 5
        while time.time() < fine and not tasto_visto(scena.quaderno()[da:], "c"):
            time.sleep(0.7)
        if not tasto_visto(scena.quaderno()[da:], "c"):
            det["riprova_ctrl_c"] = True     # the user types it again, and it is declared
            scena.comanda(metti=testo)
            ctrl(g, "c")
            time.sleep(1.5)
        det["gesto_arrivato"] = tasto_visto(scena.quaderno()[da:], "c")
    # waits for the text to reach the page (diagnosis, not judgment)
    fine = time.time() + 8
    st = {}
    while time.time() < fine:
        st = g.js(STATO_APPUNTI) or {}
        c = st.get("conti") or {}
        if c.get("ricevuti", 0) > prima.get("ricevuti", 0) and (
                c.get("scritti", 0) > prima.get("scritti", 0) or st.get("in_attesa")):
            break
        time.sleep(0.4)
    det["stato_dopo_copia"] = st
    det["copia_nella_sessione"] = [x for t, x in scena.quaderno()[da:] if t == "C"]
    if st.get("in_attesa"):
        # ⚠ the product declares it: «set aside, it goes there at the first click»
        det["gesto_chiesto_dal_prodotto"] = True
        x, y = S.C21.dal_desktop_al_vetro(geo, geo["tl"] * 0.5, geo["ta"] * 0.75)
        s.g.clic(x, y)
        time.sleep(1.0)
        det["stato_dopo_gesto"] = g.js(STATO_APPUNTI)
    letto, note = leggi_appunti_browser(g, s, geo)
    det["note_lettura"] = note
    det["diario"] = g.js(DIARIO)
    return letto, det


def corpo(o, E):
    porta_scena = o.porte_base + 5
    with S.Sessione(o, "014", E) as s:
        g = s.g
        if o.browser in ("chrome", "telefono"):
            # ⭐ the permission, as the user would give it by clicking «Allow»
            origine = o.url.rstrip("/")
            try:
                g.cdp.chiama("Browser.grantPermissions", origin=origine,
                             permissions=["clipboardReadWrite", "clipboardSanitizedWrite"])
                print("   clipboard permission granted to %s" % origine, flush=True)
            except Exception as e:               # noqa: BLE001
                print("   ⚠ permission NOT granted: %s" % e, flush=True)
        segno = s.segno_registro()
        ok, m = s.entra()
        if not ok:
            raise S.Bloccata(m)
        geo = s.geometria()
        if not geo:
            raise S.Bloccata("the canvas geometry is not there")
        st = g.js(STATO_APPUNTI)
        print("   page clipboard: %s" % json.dumps(st, ensure_ascii=False), flush=True)
        if not st or not st.get("acceso"):
            E.metti("F-014", S.FAIL, "the page's clipboard is not on: %s" % st)
            E.metti("F-015", S.FAIL, "the page's clipboard is not on: %s" % st)
            return
        print("   wake-up: %s" % S.C21.sveglia(g, geo), flush=True)
        scena = Scena(s, porta_scena)
        try:
            dentro_la_scena(o, E, s, g, geo, scena, segno)
        finally:
            scena.spegni()


def dentro_la_scena(o, E, s, g, geo, scena, segno):
    ok, t = scena.accendi()
    print("   scene: %s" % ((t or "?").splitlines() or ["?"])[-1], flush=True)
    if not ok:
        print(t, flush=True)
        s.foto("scena-non-accesa")
        raise S.Bloccata("the scene does not start: %s" % (t or "")[-300:])
    time.sleep(3)
    # ⛔ poor man's check: does the keyboard reach the remote field?  (if not, it is not F-014)
    x, y = S.C21.dal_desktop_al_vetro(geo, geo["tl"] * 0.5, geo["ta"] * 0.3)
    g.clic(x, y)
    time.sleep(1.0)
    scena.comanda(pulisci=True)
    da = len(scena.quaderno())
    lettera(g, "q")
    v, _q = scena.aspetta_valore("q", da, 8)
    if v != "q":
        raise S.Bloccata("the keyboard does not reach the scene's field (a «q» typed ⇒ %r):"
                         " the paste cannot be looked at" % (v,))

    # ── F-014 healthy ──────────────────────────────────────────────────
    t14 = testo_unico("F014")
    visto14, d14 = verso_browser_sessione(s, scena, geo, t14)
    png, dove = s.foto("f014-sana")
    ev14 = [dove] if dove else []
    ev14.append(s.salva_testo("f014-sana.json", json.dumps(d14, ensure_ascii=False,
                                                           indent=1)))
    e, perche = giudica_testo(t14, visto14)
    if e == S.FAIL and not d14.get("gesto_arrivato"):
        e, perche = S.BLOCKED, ("the Ctrl+V did not reach the session's application "
                                "(no keydown, even typed again): it is the keyboard, not the "
                                "clipboard — " + perche)
    if d14.get("riprova_ctrl_v"):
        perche += " · (Ctrl+V typed again once)"
    E.metti("F-014", e, perche, atteso=t14, osservato=visto14, evidenze=ev14)

    # ── F-015 healthy ──────────────────────────────────────────────────
    t15 = testo_unico("F015")
    letto15, d15 = verso_sessione_browser(s, scena, geo, t15)
    ev15 = [s.salva_testo("f015-sana.json", json.dumps(d15, ensure_ascii=False,
                                                       indent=1))]
    e, perche = giudica_testo(t15, letto15)
    if e == S.FAIL and not d15.get("gesto_arrivato"):
        e, perche = S.BLOCKED, ("the Ctrl+C did not reach the session's application "
                                "(no keydown, even typed again): it is the keyboard, not the "
                                "clipboard — " + perche)
    if d15.get("riprova_ctrl_c"):
        perche += " · (Ctrl+C typed again once)"
    if e == S.FAIL and letto15 is None and any("button" in n or "denied" in n
                                                for n in d15.get("note_lettura", [])):
        perche += " · " + "; ".join(d15["note_lettura"])
    if d15.get("gesto_chiesto_dal_prodotto"):
        perche += " · (the page asked for a gesture: a click made, §9)"
    E.metti("F-015", e, perche, atteso=t15, osservato=letto15, evidenze=ev15)

    if o.guasto:
        # different expectation: the judge on the real values, against the text without accents
        ad14 = giudica_testo(senza_accenti(t14), visto14)[0] == S.FAIL
        ad15 = giudica_testo(senza_accenti(t15), letto15)[0] == S.FAIL
        # copy not made, F-014
        g14 = testo_unico("F014G")
        vg14, dg14 = verso_browser_sessione(s, scena, geo, g14, copia=False)
        s.salva_testo("f014-guasto.json", json.dumps(dg14, ensure_ascii=False, indent=1))
        r14 = giudica_testo(g14, vg14)[0] == S.FAIL
        visto_g14 = (r14 and ad14) if dg14.get("gesto_arrivato") else None
        E.guasto("F-014", visto_g14,
                 "copy not made ⇒ the remote field is %r (%s); expected without accents ⇒ %s"
                 % ((vg14 or "")[:50], "ROSSO" if r14 else "VERDE",
                    "ROSSO" if ad14 else "VERDE"), atteso=g14, osservato=vg14)
        g15 = testo_unico("F015G")
        vg15, dg15 = verso_sessione_browser(s, scena, geo, g15, copia=False)
        s.salva_testo("f015-guasto.json", json.dumps(dg15, ensure_ascii=False, indent=1))
        r15 = giudica_testo(g15, vg15)[0] == S.FAIL
        E.guasto("F-015", r15 and ad15,
                 "copy not made ⇒ the browser's clipboard is %r (%s); expected without "
                 "accents ⇒ %s" % ((vg15 or "")[:50], "ROSSO" if r15 else "VERDE",
                                   "ROSSO" if ad15 else "VERDE"),
                 atteso=g15, osservato=vg15)
    s.salva_testo("server-f014.txt", s.registro_da(segno) if segno is not None else [])
    s.salva_console()


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
