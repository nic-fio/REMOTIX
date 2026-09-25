#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f014 — F-014 APPUNTI, BROWSER → SESSIONE · F-015 APPUNTI, SESSIONE → BROWSER

    python3 15-f014-appunti.py --scatola kde --browser chrome [--guasto]
    python3 15-f014-appunti.py --certifica

LA SCENA (dentro la sessione dell'inquilino): `firefox-esr --kiosk` su una
pagina con un <textarea> sempre a fuoco, servita da un piccolo servitore
dell'inquilino.  La pagina ANNOTA in un quaderno ogni valore del campo, ogni
`paste` e ogni `copy`; e ubbidisce a due comandi del banco (svuota / metti un
testo selezionato).  ⇒ Il giudizio e' il VALORE DEL CAMPO di un'applicazione
vera della sessione, non un contatore del prodotto.

F-014  browser → sessione.  Un testo unico (accenti, €, ß, →, «») si mette
       negli appunti del browser come fa l'utente: un campo, `Ctrl+C` VERO
       (Marionette / `Input.dispatchKeyEvent`).  Il campo si toglie, un clic
       sulla tela (sul campo remoto), `Ctrl+V` VERO sulla pagina ⇒ il campo
       della scena deve valere ESATTAMENTE quel testo.
       Come lo legge la pagina (src/pagina.html, «IL CAMPO NASCOSTO CHE FA
       NASCERE L'EVENTO paste» e `appunti_su_incolla`): il `Ctrl+V` NON e'
       annullato, va al campo nascosto `#incolla-nascosto` ⇒ evento `paste`
       (o il valore del campo) ⇒ APPUNTI_ANNUNCIO; su Chrome in piu' la
       sorveglianza `clipboardchange`.  Il `Ctrl+V` parte anche verso la
       sessione, ed e' lui che incolla nell'applicazione.
F-015  sessione → browser.  Il testo unico si mette nel campo della scena,
       selezionato, e si batte `Ctrl+C` VERO sulla pagina (va alla sessione)
       ⇒ il compositore cambia selezione, il server annuncia, la pagina chiede
       e scrive con `navigator.clipboard.writeText` ⇒ gli appunti del browser
       devono valere ESATTAMENTE quel testo, letti con `readText()`:
         Chrome   permesso dato come lo darebbe l'utente (Browser.grantPermissions
                  clipboardReadWrite + clipboardSanitizedWrite sull'origine);
         Firefox  un clic vero (attivazione) e `readText()`; se Firefox mostra
                  il bottoncino «Incolla» (SPECIFICHE.md §9: «Là ogni lettura
                  costa il menu Incolla») lo si clicca come l'utente, e si conta.
       ⚠ Se la pagina non ha potuto scrivere subito (`in_attesa_di_gesto`,
         dichiarato in `scrivi_negli_appunti`), si fa il gesto che il prodotto
         chiede: un clic sulla pagina.  Si riferisce.

GUASTO (stessa sessione, dopo la passata sana), in tutti e due i versi:
  «copia non fatta» — un testo unico NUOVO come atteso, e il gesto di copia NON
  si fa (F-014: niente `Ctrl+C` nel browser; F-015: niente `Ctrl+C` nella
  sessione).  Il resto identico.  ⇒ deve dare ROSSO.
  «atteso diverso» — il valore osservato nella passata sana giudicato contro
  lo stesso testo senza accenti ⇒ deve dare ROSSO (il giudice vede gli accenti).
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


# ⛔ SUL SERVER I COMANDI NELLA SCATOLA NON PASSANO DA ssh — `[M]` 24 set 2026,
#   dieci agenti sullo stesso server: `ssh` verso se' stesso chiude le
#   connessioni («Connection closed by 192.168.0.2 port 22», MaxStartups) e
#   perdeva a caso un comando della scena — e lo SGOMBERO, che lasciava
#   l'inquilino vivo.  ⇒ Qui (e solo in questo processo) `Scatola.dentro` fa
#   `sudo podman exec` diretto, con una riprova.  Da proporre a suite.py.
def _dentro_locale(self, riga, secondi=90):
    import subprocess
    for _tentativo in range(3):
        try:
            r = subprocess.run(["sudo", "-S", "-p", "", "podman", "exec", self.contenitore,
                                "sh", "-c", riga], input="nicfio\n", capture_output=True,
                               text=True, errors="replace", timeout=secondi)
        except subprocess.TimeoutExpired:
            return None, "(nessuna risposta in %d s)" % secondi
        if r.returncode == 125 and "Error" in (r.stderr or ""):     # podman stesso
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
#  LE FUNZIONI PURE
# ═══════════════════════════════════════════════════════════════════════════
def testo_unico(sigla):
    return "%s àèìòù €ß→ «ÀÉ» %s" % (sigla, secrets.token_hex(4))


def senza_accenti(t):
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def giudica_testo(atteso, visto):
    """(esito, perche'): PASS solo se IDENTICO, byte per byte."""
    if visto is None:
        return S.FAIL, "nessun valore letto"
    if visto == atteso:
        return S.PASS, "identico (%d caratteri, %d byte)" % (len(atteso),
                                                             len(atteso.encode()))
    if visto.strip() == atteso:
        return S.FAIL, "uguale a meno di spazi/a capo ai bordi: %r" % visto[:80]
    if senza_accenti(visto) == senza_accenti(atteso):
        return S.FAIL, "uguale SENZA gli accenti: %r" % visto[:80]
    return S.FAIL, "diverso: %r invece di %r" % (visto[:80], atteso[:80])


def certifica():
    t = testo_unico("F014")
    casi = [
        ("identico ⇒ PASS", giudica_testo(t, t)[0] == S.PASS),
        ("senza accenti ⇒ FAIL", giudica_testo(t, senza_accenti(t))[0] == S.FAIL),
        ("gli accenti ci sono davvero", senza_accenti(t) != t),
        ("a capo in coda ⇒ FAIL", giudica_testo(t, t + "\n")[0] == S.FAIL),
        ("vuoto ⇒ FAIL", giudica_testo(t, "")[0] == S.FAIL),
        ("niente ⇒ FAIL", giudica_testo(t, None)[0] == S.FAIL),
        ("due testi unici diversi", testo_unico("X") != testo_unico("X")),
        ("quaderno: l'ultimo valore", ultimo_valore(
            [("V", ""), ("P", "x"), ("V", "ab"), ("OK", 1)]) == "ab"),
        ("il Ctrl+V si riconosce", tasto_visto([("K", "Control ctrl"), ("K", "v ctrl")], "v")),
        ("un v senza Ctrl non conta", not tasto_visto([("K", "v")], "v")),
    ]
    ok = True
    for nome, vero in casi:
        print("%s %s" % ("⭐" if vero else "⛔", nome))
        ok = ok and vero
    return 0 if ok else 1


def tasto_visto(quaderno, lettera):
    """Il Ctrl+<lettera> e' arrivato come keydown all'applicazione della scena?"""
    return ("K", "%s ctrl" % lettera) in quaderno or ("K", "%s ctrl" % lettera.upper()) in quaderno


def ultimo_valore(quaderno, tag="V"):
    v = None
    for t, x in quaderno:
        if t == tag:
            v = x
    return v


# ═══════════════════════════════════════════════════════════════════════════
#  LA SCENA NELLA SESSIONE
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


# ⚠ Il proxy di SISTEMA no: su GNOME Firefox lo chiede al portale/gsettings.
PREFERENZE = S.C21.PREFERENZE + 'user_pref("network.proxy.type", 0);\n'


# ⛔ E LA CACHE NELLA CASA, non in ~/.cache: `[M]` 24 set 2026, nella scatola
#   gnome `~/.cache` e' un collegamento a /tmp, e /tmp/mozilla era di un uid
#   morto (4016, sticky) ⇒ «Your Firefox profile cannot be loaded» e la scena
#   non si accende.  La stessa trappola di C2/C17.
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
            "[ -n \"$d\" ] || {{ echo 'nessun socket wayland'; exit 2; }}; sleep 1; "
            "setsid runuser -u {c} -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
            "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
            "XDG_SESSION_TYPE=wayland HOME=$h XDG_CACHE_HOME=$h/f014-cache "
            "firefox-esr --no-remote --new-instance "
            "--profile $h/f014-profilo --kiosk http://127.0.0.1:{p}/ "
            "</dev/null >$h/.f014-firefox.log 2>&1 & "
            "for i in $(seq 1 200); do grep -q caricata $h/f014.log && {{ echo accesa; exit 0; }}; "
            "sleep 0.5; done; echo 'la scena non ha detto «caricata»'; "
            "echo --ff; tail -8 $h/.f014-firefox.log; echo --srv; tail -5 $h/.f014-servitore.log; "
            "echo --ps; ps -u {c} -o pid,args | cut -c1-150 | tail -25; echo --run; ls /run/user/$u; "
            "echo --curl; python3 -c \"import urllib.request as u; "
            "print(len(u.urlopen('http://127.0.0.1:{p}/', timeout=3).read()))\" 2>&1 | tail -1; exit 1"
            .format(h=self.h, c=self.chi, p=self.porta, srv=b(SERVITORE), pag=b(PAGINA),
                    pref=b(PREFERENZE)), 180)
        return c == 0, t

    def spegni(self):
        """Il servitore e il firefox-esr della scena se ne vanno PRIMA dello sgombero."""
        self.sc.dentro("pkill -KILL -u %s -f 'f014' 2>/dev/null; sleep 0.3; "
                       "pkill -KILL -u %s -f 'f014' 2>/dev/null; true" % (self.chi, self.chi), 30)

    def quaderno(self):
        """[(tag, valore)] — il quaderno della scena, per intero."""
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
        """Un comando alla scena; aspetta il suo «OK».  Torna il quaderno dopo."""
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
                                  "tail -3 %s/.f014-servitore.log" % (self.h, self.h, self.h), 30)
        raise S.Bloccata("la scena non ha eseguito il comando n=%d in 12 s (quaderno: %d righe; "
                         "coda: %s)" % (self.n, len(q), (coda or "")[-500:]))

    def aspetta_valore(self, atteso, da, tetto=ATTESA_S):
        """Guarda il campo finche' vale `atteso` o scade.  Torna (valore, quaderno nuovo)."""
        fine = time.time() + tetto
        while True:
            q = self.quaderno()[da:]
            v = ultimo_valore(q)
            if v == atteso or time.time() >= fine:
                return v, q
            time.sleep(1.0)


# ═══════════════════════════════════════════════════════════════════════════
#  I GESTI VERI
# ═══════════════════════════════════════════════════════════════════════════
def ctrl(g, lettera):
    """Ctrl+<lettera> con tasti VERI (eventi fidati del browser)."""
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
  return t.split('\\n').filter(x => /appunti|APPUNTI|paste|Ctrl\\+V|readText|§9/.test(x)).slice(-25);
"""
LEGGI_LANCIA = """
  window.__f015 = {fatto: false};
  try {
    navigator.clipboard.readText().then(
      t => { window.__f015 = {fatto: true, testo: t}; },
      e => { window.__f015 = {fatto: true, errore: String(e)}; });
  } catch (e) { window.__f015 = {fatto: true, errore: 'eccezione: ' + e}; }
"""


def js_pagina(g, corpo):
    """Un corpo eseguito NELLA pagina (su Firefox con <script>, non nella sandbox)."""
    if hasattr(g, "cdp"):
        return g.js(corpo + "; return true;")
    return g.js(S.VERI._inietta(corpo))


def leggi_appunti_browser(g, s, geo):
    """(testo | None, note) — gli appunti del browser, con `readText()`."""
    note = []
    if not hasattr(g, "cdp"):
        # ⭐ l'attivazione: un clic vero sulla tela (va al campo remoto: innocuo)
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
                note.append("readText negato: %s" % r["errore"])
                return None, note
            return r.get("testo"), note
        if not hasattr(g, "cdp") and not bottoncino and paga_il_bottoncino(g):
            bottoncino += 1
            note.append("Firefox ha chiesto il bottoncino «Incolla» (SPECIFICHE §9): "
                        "cliccato come l'utente")
        time.sleep(0.3)
    note.append("readText non ha risposto in 8 s")
    return None, note


def paga_il_bottoncino(g):
    """Il pannello «Incolla» di Firefox (07-b56): lo clicca se e' aperto."""
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
        esito = "guasto: %s" % e
    finally:
        try:
            g.m.chiama("Marionette:SetContext", {"value": "content"})
        except Exception:                        # noqa: BLE001
            pass
    return esito == "cliccato"


# ═══════════════════════════════════════════════════════════════════════════
#  I DUE VERSI
# ═══════════════════════════════════════════════════════════════════════════
def verso_browser_sessione(s, scena, geo, testo, copia=True):
    """F-014: torna (valore del campo remoto, dettagli)."""
    g = s.g
    scena.comanda(pulisci=True)
    da = len(scena.quaderno())
    det = {"copia_fatta": copia}
    if copia:
        det["campo_a_fuoco"] = g.js(CAMPO_APRI, testo)
        time.sleep(0.3)
        ctrl(g, "c")                       # ⭐ la copia VERA nel browser
        time.sleep(0.8)
        g.js(CAMPO_CHIUDI)
    # il clic sul campo remoto (fuoco nella sessione) e poi il Ctrl+V vero
    x, y = S.C21.dal_desktop_al_vetro(geo, geo["tl"] * 0.5, geo["ta"] * 0.3)
    g.clic(x, y)
    time.sleep(1.0)
    det["stato_prima"] = g.js(STATO_APPUNTI)
    ctrl(g, "v")
    visto, q = scena.aspetta_valore(testo, da)
    if visto != testo and not tasto_visto(q, "v"):
        # ⚠ il Ctrl+V non e' ARRIVATO all'applicazione (fuoco della sessione):
        #   l'utente lo ribatte.  Si dichiara.  `[M]` gnome/chrome, una volta su tre.
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
    """F-015: torna (testo negli appunti del browser, dettagli)."""
    g = s.g
    q = scena.comanda(metti=testo)
    det = {"copia_fatta": copia, "campo_remoto": ultimo_valore(q)}
    if det["campo_remoto"] != testo:
        raise S.Bloccata("la scena non ha preso il testo da copiare: %r"
                         % (det["campo_remoto"],))
    prima = (g.js(STATO_APPUNTI) or {}).get("conti") or {}
    da = len(q)
    if copia:
        ctrl(g, "c")                       # ⭐ la copia VERA nella sessione
        fine = time.time() + 5
        while time.time() < fine and not tasto_visto(scena.quaderno()[da:], "c"):
            time.sleep(0.7)
        if not tasto_visto(scena.quaderno()[da:], "c"):
            det["riprova_ctrl_c"] = True     # l'utente lo ribatte, e si dichiara
            scena.comanda(metti=testo)
            ctrl(g, "c")
            time.sleep(1.5)
        det["gesto_arrivato"] = tasto_visto(scena.quaderno()[da:], "c")
    # aspetta che il testo arrivi alla pagina (diagnosi, non giudizio)
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
        # ⚠ il prodotto lo dichiara: «messo da parte, ci va al primo clic»
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
        if o.browser == "chrome":
            # ⭐ il permesso, come lo darebbe l'utente cliccando «Consenti»
            origine = o.url.rstrip("/")
            try:
                g.cdp.chiama("Browser.grantPermissions", origin=origine,
                             permissions=["clipboardReadWrite", "clipboardSanitizedWrite"])
                print("   permesso appunti concesso a %s" % origine, flush=True)
            except Exception as e:               # noqa: BLE001
                print("   ⚠ permesso NON concesso: %s" % e, flush=True)
        segno = s.segno_registro()
        ok, m = s.entra()
        if not ok:
            raise S.Bloccata(m)
        geo = s.geometria()
        if not geo:
            raise S.Bloccata("la geometria della tela non c'e'")
        st = g.js(STATO_APPUNTI)
        print("   appunti della pagina: %s" % json.dumps(st, ensure_ascii=False), flush=True)
        if not st or not st.get("acceso"):
            E.metti("F-014", S.FAIL, "gli appunti della pagina non sono accesi: %s" % st)
            E.metti("F-015", S.FAIL, "gli appunti della pagina non sono accesi: %s" % st)
            return
        print("   sveglia: %s" % S.C21.sveglia(g, geo), flush=True)
        scena = Scena(s, porta_scena)
        try:
            dentro_la_scena(o, E, s, g, geo, scena, segno)
        finally:
            scena.spegni()


def dentro_la_scena(o, E, s, g, geo, scena, segno):
    ok, t = scena.accendi()
    print("   scena: %s" % ((t or "?").splitlines() or ["?"])[-1], flush=True)
    if not ok:
        print(t, flush=True)
        s.foto("scena-non-accesa")
        raise S.Bloccata("la scena non si accende: %s" % (t or "")[-300:])
    time.sleep(3)
    # ⛔ controllo povero: la tastiera arriva al campo remoto?  (se no, non e' F-014)
    x, y = S.C21.dal_desktop_al_vetro(geo, geo["tl"] * 0.5, geo["ta"] * 0.3)
    g.clic(x, y)
    time.sleep(1.0)
    scena.comanda(pulisci=True)
    da = len(scena.quaderno())
    lettera(g, "q")
    v, _q = scena.aspetta_valore("q", da, 8)
    if v != "q":
        raise S.Bloccata("la tastiera non arriva al campo della scena (una «q» battuta ⇒ %r):"
                         " non si puo' guardare l'incolla" % (v,))

    # ── F-014 sana ─────────────────────────────────────────────────────
    t14 = testo_unico("F014")
    visto14, d14 = verso_browser_sessione(s, scena, geo, t14)
    png, dove = s.foto("f014-sana")
    ev14 = [dove] if dove else []
    ev14.append(s.salva_testo("f014-sana.json", json.dumps(d14, ensure_ascii=False,
                                                           indent=1)))
    e, perche = giudica_testo(t14, visto14)
    if e == S.FAIL and not d14.get("gesto_arrivato"):
        e, perche = S.BLOCKED, ("il Ctrl+V non e' arrivato all'applicazione della sessione "
                                "(nessun keydown, anche ribattuto): e' la tastiera, non gli "
                                "appunti — " + perche)
    if d14.get("riprova_ctrl_v"):
        perche += " · (Ctrl+V ribattuto una volta)"
    E.metti("F-014", e, perche, atteso=t14, osservato=visto14, evidenze=ev14)

    # ── F-015 sana ─────────────────────────────────────────────────────
    t15 = testo_unico("F015")
    letto15, d15 = verso_sessione_browser(s, scena, geo, t15)
    ev15 = [s.salva_testo("f015-sana.json", json.dumps(d15, ensure_ascii=False,
                                                       indent=1))]
    e, perche = giudica_testo(t15, letto15)
    if e == S.FAIL and not d15.get("gesto_arrivato"):
        e, perche = S.BLOCKED, ("il Ctrl+C non e' arrivato all'applicazione della sessione "
                                "(nessun keydown, anche ribattuto): e' la tastiera, non gli "
                                "appunti — " + perche)
    if d15.get("riprova_ctrl_c"):
        perche += " · (Ctrl+C ribattuto una volta)"
    if e == S.FAIL and letto15 is None and any("bottoncino" in n or "negato" in n
                                                for n in d15.get("note_lettura", [])):
        perche += " · " + "; ".join(d15["note_lettura"])
    if d15.get("gesto_chiesto_dal_prodotto"):
        perche += " · (la pagina ha chiesto un gesto: fatto un clic, §9)"
    E.metti("F-015", e, perche, atteso=t15, osservato=letto15, evidenze=ev15)

    if o.guasto:
        # atteso diverso: il giudice sui valori veri, contro il testo senza accenti
        ad14 = giudica_testo(senza_accenti(t14), visto14)[0] == S.FAIL
        ad15 = giudica_testo(senza_accenti(t15), letto15)[0] == S.FAIL
        # copia non fatta, F-014
        g14 = testo_unico("F014G")
        vg14, dg14 = verso_browser_sessione(s, scena, geo, g14, copia=False)
        s.salva_testo("f014-guasto.json", json.dumps(dg14, ensure_ascii=False, indent=1))
        r14 = giudica_testo(g14, vg14)[0] == S.FAIL
        visto_g14 = (r14 and ad14) if dg14.get("gesto_arrivato") else None
        E.guasto("F-014", visto_g14,
                 "copia non fatta ⇒ il campo remoto vale %r (%s); atteso senza accenti ⇒ %s"
                 % ((vg14 or "")[:50], "ROSSO" if r14 else "VERDE",
                    "ROSSO" if ad14 else "VERDE"), atteso=g14, osservato=vg14)
        g15 = testo_unico("F015G")
        vg15, dg15 = verso_sessione_browser(s, scena, geo, g15, copia=False)
        s.salva_testo("f015-guasto.json", json.dumps(dg15, ensure_ascii=False, indent=1))
        r15 = giudica_testo(g15, vg15)[0] == S.FAIL
        E.guasto("F-015", r15 and ad15,
                 "copia non fatta ⇒ gli appunti del browser valgono %r (%s); atteso senza "
                 "accenti ⇒ %s" % ((vg15 or "")[:50], "ROSSO" if r15 else "VERDE",
                                   "ROSSO" if ad15 else "VERDE"),
                 atteso=g15, osservato=vg15)
    s.salva_testo("server-f014.txt", s.registro_da(segno) if segno is not None else [])
    s.salva_console()


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
