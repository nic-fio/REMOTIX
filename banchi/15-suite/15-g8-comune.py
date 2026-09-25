#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-g8-comune — gli aiuti del gruppo G8 («gli utenti, la parola, il ban»)

    python3 15-g8-comune.py accendi|spegni|sblocca|stato <desktop>   (lo chiama 15-g8-server.sh)

Che cosa c'e' qui (importato da 15-f025, 15-f026, 15-f027, 15-n027 con
`suite._carica`, non copiato):

  MioServer     ⭐ il SECONDO server del prodotto dentro una scatola: stesso
                binario /opt/remotix/remotix, unita' systemd `rete15-g8`, porta
                862x, ban-file, socket di comando, rilievo e registro SUOI in
                /var/lib/rete15-g8/.  ⛔ Serve a tutto cio' che sbaglia la
                parola: tre errori bannano 192.168.0.2 per 12 ore, e sul server
                della scatola (8511-8514) fermerebbero tutti.  Il ban e' in
                memoria del PROCESSO e nel SUO file: quello dell'85xx non lo vede.
  scena_colore  una finestra `firefox-esr --kiosk` nella sessione dell'inquilino,
                tutta di un COLORE noto, con un campo di testo a fuoco; un piccolo
                servitore annota nella casa dell'inquilino ogni tasto e ogni
                valore del campo (il «valore di un campo» della suite), e serve il
                colore da un file — cambiare quel file cambia la scena (il guasto).
  frazioni      quanta parte della fotografia e' di ciascun colore noto.
  ferma/riprendi  SIGSTOP/SIGCONT all'albero di processi di un browser: il
                client resta «attaccato» ma TACE — il fantasma di §5.1.
  leggi_pagina  esito, classe, ban, avviso della pagina, senza toccarla.
"""
import base64
import copy
import io
import json
import os
import re
import signal
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import suite as S                                                     # noqa: E402

C23 = S._carica("c23_g8", os.path.join(S.BANCHI, "11-scatole",
                                       "11-c23-maiusc-e-frecce-selezionano.py"))

# ⛔ Le porte del gruppo G8 — solo queste (mandato comune).
PORTE_MIE = {"gnome": 8621, "kde": 8622, "xfce": 8623, "lxqt": 8624}
BASE_BROWSER = {"gnome": 4900, "kde": 4910, "xfce": 4920, "lxqt": 4930}
# il secondo e il terzo browser dello stesso tipo: base+50 e base+54
SPOSTA_BROWSER = (0, 50, 54)
# il servitore della scena: base+5+i (Firefox N, Chrome N+1, Android N+2 sono dei browser)
SPOSTA_SCENA = 5
UNITA = "rete15-g8"
DIR = "/var/lib/rete15-g8"
REGISTRO = DIR + "/registro.log"
BAN = DIR + "/ban"
SOCK = DIR + "/comando.sock"
BAN_85XX = "/var/lib/rete11/ban"
INDIRIZZO = "192.168.0.2"

# Le frasi della pagina (src/pagina.html, `MOTIVO`), per sottostringa.
FRASE = {
    0x07: "utente o parola d'ordine non corretti",
    0x08: "i tentativi da questo indirizzo sono esauriti",
    0x0F: "occupato da un altro client",
}
# ⚠ I rifiuti che NON sono la cosa provata: sotto carico (10 agenti, carico
#   ~50) la stretta di mano scade (0x0D) o la sonda dei codec del browser non
#   fa in tempo (0x09).  Col server della scatola si riprova; mai col server
#   G8 dopo una parola sbagliata (potrebbe contare).
AMBIENTE = ("tempo scaduto durante la stretta di mano",
            "non hanno niente in comune da parlare", "Non si collega")


def dentro(sc, riga, secondi=90):
    """`Scatola.dentro` senza la riga del «password:» di sshpw."""
    c, t = sc.dentro(riga, secondi)
    t = "\n".join(x for x in (t or "").splitlines() if "'s password:" not in x)
    return c, t


# ═══════════════════════════════════════════════════════════════════════════
#  IL SERVER MIO
# ═══════════════════════════════════════════════════════════════════════════
class MioServer:
    def __init__(self, desktop, sc=None):
        self.desktop = desktop
        self.porta = PORTE_MIE[desktop]
        self.sc = sc or S.C20V.Scatola(desktop)

    def comando_accensione(self):
        return (
            "mkdir -p %(d)s; systemctl stop %(u)s 2>/dev/null; "
            "systemctl reset-failed %(u)s 2>/dev/null; "
            "echo \"=== accensione $(date -u +%%FT%%TZ) ===\" >> %(r)s; "
            "systemd-run --unit=%(u)s --working-directory=/opt/remotix "
            "--property=StandardOutput=append:%(r)s --property=StandardError=append:%(r)s "
            "--property=KillMode=mixed /opt/remotix/remotix --indirizzo 0.0.0.0 "
            "--nome 127.0.0.1 --porta %(p)d --certificati %(d)s/certificati "
            "--pagina /opt/remotix/pagina.html --ban-file %(b)s --comando-socket %(s)s "
            "--rilievo %(d)s/rilievo --parlantina >/dev/null 2>&1; "
            % {"d": DIR, "u": UNITA, "r": REGISTRO, "p": self.porta, "b": BAN, "s": SOCK})

    def accendi(self, tetto=30):
        """(True, righe) quando il registro dice «pronto: https» DOPO l'accensione."""
        n0 = self.righe_registro() or 0
        c, t = dentro(self.sc, self.comando_accensione() + "echo acceso", 60)
        if c != 0:
            return False, "systemd-run: %s" % t[-300:]
        fine = time.time() + tetto
        while time.time() < fine:
            _c, t = dentro(self.sc, "tail -n +%d %s | grep -a -m1 'pronto: https'"
                                   % (n0 + 1, REGISTRO), 30)
            if "pronto: https" in (t or ""):
                return True, t.strip()
            time.sleep(1)
        _c, t = dentro(self.sc, "tail -8 %s" % REGISTRO, 30)
        return False, "non ha detto «pronto» in %d s: %s" % (tetto, t[-400:])

    def spegni(self):
        c, t = dentro(self.sc, "systemctl stop %s 2>&1; systemctl reset-failed %s 2>/dev/null; "
                              "systemctl is-active %s; true" % (UNITA, UNITA, UNITA), 60)
        return c == 0, t.strip()

    def acceso(self):
        c, t = dentro(self.sc, "systemctl is-active %s" % UNITA, 30)
        return (t or "").strip().endswith("active") and "inactive" not in (t or "")

    def parla(self, riga):
        """Una riga sul socket di comando (src/comando.c): PING, SBLOCCA <ind>."""
        prog = ("import socket,sys; s=socket.socket(socket.AF_UNIX); s.settimeout(5); "
                "s.connect(%r); s.sendall(%r.encode()); print(s.recv(300).decode().strip())"
                % (SOCK, riga + "\n"))
        c, t = dentro(self.sc, "python3 -c %s" % S._q(prog), 30)
        return (t or "").strip()

    def sblocca(self, indirizzo=INDIRIZZO):
        return self.parla("SBLOCCA %s" % indirizzo)

    def righe_registro(self):
        _c, t = dentro(self.sc, "wc -l < %s 2>/dev/null || echo 0" % REGISTRO, 30)
        try:
            return int(t.split()[-1])
        except (ValueError, IndexError, AttributeError):
            return None

    def registro_da(self, segno, filtro=None):
        cmd = "tail -n +%d %s" % ((segno or 0) + 1, REGISTRO)
        if filtro:
            cmd += " | grep -a -- %s" % S._q(filtro)
        _c, t = dentro(self.sc, cmd, 60)
        return (t or "").splitlines()

    def file_ban(self, quale=BAN):
        _c, t = dentro(self.sc, "cat %s 2>/dev/null; true" % quale, 30)
        return (t or "").strip()


# ═══════════════════════════════════════════════════════════════════════════
#  LA SCENA DI UN COLORE, col campo di testo e il quaderno
# ═══════════════════════════════════════════════════════════════════════════
PAGINA_SCENA = """<!doctype html><meta charset=utf-8><title>REMOTIX G8</title>
<style>
 html,body{margin:0;height:100%;overflow:hidden;background:rgb(__C__)}
 #f{position:fixed;left:15vw;top:40vh;width:70vw;height:14vh;font:10vh/1 monospace;
    border:0;padding:0 1vw;box-sizing:border-box;background:#fff;color:#000;outline:0}
</style>
<input id=f autocomplete=off spellcheck=false>
<script>
const f=document.getElementById('f');
const m=(t)=>fetch('/l',{method:'POST',body:t}).catch(()=>0);
f.focus(); m('caricata');
addEventListener('keydown',e=>m('K '+e.key));
f.addEventListener('input',()=>m('V '+JSON.stringify(f.value)));
let ult='';
setInterval(()=>{ if(document.activeElement!==f) f.focus();
  fetch('/c').then(r=>r.text()).then(c=>{c=c.trim(); if(c&&c!==ult){ult=c;
    document.body.style.background='rgb('+c+')'; m('C '+c);}}).catch(()=>0); },400);
</script>"""

SERVITORE = r'''
import http.server, sys
PAG = open(sys.argv[2], "rb").read()
LOG, COL = sys.argv[3], sys.argv[4]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        corpo = PAG
        if self.path.startswith("/c"):
            try: corpo = open(COL, "rb").read()
            except Exception: corpo = b""
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(corpo)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        t = self.rfile.read(n).decode("utf-8", "replace")
        with open(LOG, "a") as f: f.write(t + "\n")
        self.send_response(204); self.end_headers()
http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
'''


def rgb(c):
    return "%d,%d,%d" % tuple(c)


def accendi_scena(sc, chi, porta, colore, attesa=45):
    """Servitore + `firefox-esr --kiosk` nella sessione di `chi`; aspetta «caricata»."""
    b = lambda s: base64.b64encode(s.encode()).decode()     # noqa: E731
    pag = PAGINA_SCENA.replace("__C__", rgb(colore))
    c, t = dentro(sc, 
        "set -e; h=/home/{c}; mkdir -p $h/.g8-profilo; "
        "echo {srv} | base64 -d > $h/g8-servitore.py; echo {pag} | base64 -d > $h/g8.html; "
        "echo {pref} | base64 -d > $h/.g8-profilo/user.js; : > $h/g8.log; "
        "echo {col} > $h/g8-colore; "
        "chown -R {c}: $h/.g8-profilo $h/g8-servitore.py $h/g8.html $h/g8.log $h/g8-colore; "
        "set +e; u=$(id -u {c}); "
        "pkill -f 'python3 /home/[^ ]*/g8-servitore[.]py {p} ' 2>/dev/null; sleep 0.3; "
        "setsid runuser -u {c} -- python3 $h/g8-servitore.py {p} $h/g8.html $h/g8.log "
        "$h/g8-colore </dev/null >$h/.g8-servitore.log 2>&1 & "
        "for i in $(seq 1 20); do grep -q {c} /proc/$(ss -ltnpH 'sport = :{p}' | "
        "sed -n 's/.*pid=\\([0-9]*\\).*/\\1/p' | head -1)/cmdline 2>/dev/null && break; sleep 0.3; done; "
        "d=''; for i in $(seq 1 40); do d=$(ls /run/user/$u 2>/dev/null | "
        "grep -E '^wayland-[0-9]+$' | head -1); [ -n \"$d\" ] && break; sleep 0.5; done; "
        "[ -n \"$d\" ] || {{ echo 'nessun socket wayland'; exit 2; }}; sleep 1; "
        "setsid runuser -u {c} -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
        "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
        "XDG_SESSION_TYPE=wayland HOME=$h firefox-esr --no-remote --new-instance "
        "--profile $h/.g8-profilo --kiosk http://127.0.0.1:{p}/ "
        "</dev/null >$h/.g8-firefox.log 2>&1 & "
        "for i in $(seq 1 {n}); do grep -q caricata $h/g8.log && {{ echo accesa; exit 0; }}; "
        "sleep 0.5; done; echo 'la scena non ha detto «caricata»'; tail -5 $h/.g8-firefox.log; "
        "echo '-- servitore:'; ss -ltn | grep ':{p} ' ; pgrep -a -u {c} | cut -c1-150 | tail -8; "
        "exit 1".format(c=chi, p=porta, srv=b(SERVITORE), pag=b(pag),
                        pref=b(S.C21.PREFERENZE), col=rgb(colore), n=attesa * 2), attesa + 60)
    return c == 0, t


def cambia_colore(sc, chi, colore):
    c, t = dentro(sc, "echo %s > /home/%s/g8-colore" % (rgb(colore), chi), 30)
    return c == 0


def quaderno(sc, chi):
    _c, t = dentro(sc, "cat /home/%s/g8.log 2>/dev/null" % chi, 30)
    return [r for r in (t or "").splitlines() if r.strip()]


def valore(righe):
    """L'ultimo valore del campo annotato (o "" se mai scritto)."""
    v = ""
    for r in righe:
        if r.startswith("V "):
            try:
                v = json.loads(r[2:])
            except ValueError:
                pass
    return v


def tasti(righe):
    return [r[2:] for r in righe if r.startswith("K ")]


# ═══════════════════════════════════════════════════════════════════════════
#  LE FOTOGRAFIE
# ═══════════════════════════════════════════════════════════════════════════
def frazioni(png, colori, toll=60, riduci=8):
    """{nome: frazione dei pixel vicini a quel colore} — o None."""
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(png)).convert("RGB")
    except Exception:                            # noqa: BLE001
        return None
    w, h = im.size
    im = im.resize((max(1, w // riduci), max(1, h // riduci)), Image.NEAREST)
    px = list(im.getdata())
    n = float(len(px)) or 1.0
    fuori = {}
    for nome, c in colori.items():
        k = 0
        for p in px:
            if abs(p[0] - c[0]) <= toll and abs(p[1] - c[1]) <= toll and abs(p[2] - c[2]) <= toll:
                k += 1
        fuori[nome] = k / n
    return fuori


def aspetta_colore(s, nome_foto, colori, voluto, soglia=0.5, tetto=40):
    """Fotografa finche' il colore `voluto` copre `soglia` o scade il tetto; la
    fotografia che decide si SALVA nelle evidenze.
    Torna (frazioni o None, percorso della foto, motivo)."""
    fine = time.time() + tetto
    fr, perche = None, "nessuna fotografia"
    while True:
        png, perche = _foto_muta(s)
        if png:
            fr = frazioni(png, colori)
            if fr and fr.get(voluto, 0) >= soglia:
                break
        if time.time() >= fine:
            break
        time.sleep(1.5)
    png, dove = s.foto(nome_foto)
    if png:
        fr = frazioni(png, colori)
        return fr, dove, ""
    return fr, "", dove


def _foto_muta(s):
    """Una fotografia che NON si salva (i tentativi dell'attesa)."""
    try:
        png = S.C21.foto_piena(s.g)
    except Exception as e:                       # noqa: BLE001
        return None, "fotografia fallita: %s" % str(e)[:200]
    return (png, "") if png else (None, "la tela non si fotografa")


def fr_testo(fr):
    if not fr:
        return "(nessuna misura)"
    return ", ".join("%s %.1f%%" % (k, 100 * v) for k, v in fr.items())


# ═══════════════════════════════════════════════════════════════════════════
#  I BROWSER: un secondo e un terzo dello stesso tipo, il fantasma
# ═══════════════════════════════════════════════════════════════════════════
def o_per(o, i):
    """Una copia delle opzioni per il browser numero `i` (0, 1, 2)."""
    o2 = copy.copy(o)
    o2.porte_base = o.porte_base + SPOSTA_BROWSER[i]
    if o.evidenze:
        o2.evidenze = os.path.join(o.evidenze, "browser%d" % i) if i else o.evidenze
        os.makedirs(o2.evidenze, exist_ok=True)
    return o2


def _figli():
    fig = {}
    for v in os.listdir("/proc"):
        if not v.isdigit():
            continue
        try:
            with open("/proc/%s/stat" % v) as f:
                st = f.read()
            ppid = int(st[st.rindex(")") + 2:].split()[1])
        except (OSError, ValueError, IndexError):
            continue
        fig.setdefault(ppid, []).append(int(v))
    return fig


def albero(pid):
    fig = _figli()
    tutti, coda = [], [pid]
    while coda:
        p = coda.pop()
        tutti.append(p)
        coda.extend(fig.get(p, []))
    return tutti


def _cmdline(pid):
    try:
        with open("/proc/%d/cmdline" % pid, "rb") as f:
            return f.read().replace(b"\0", b" ").decode("utf-8", "replace")
    except OSError:
        return ""


def ferma(g, stop=True):
    """⛔ Il FANTASMA: il client resta attaccato per il server ma non manda piu'
    un pacchetto.  SIGSTOP (o SIGCONT) —
      Chrome   al solo servizio di rete (`network.mojom.NetworkService`, dove
               vive QUIC): il browser e CDP restano vivi, la pagina anche;
      Firefox  a TUTTO l'albero (la rete sta nel processo padre o in quello
               «socket»); Marionette riprende dopo il SIGCONT.
    Torna quanti processi."""
    p = getattr(g, "p", None)
    if p is None:
        return 0
    pids = albero(p.pid)
    if hasattr(g, "cdp"):
        rete = [q for q in pids if "NetworkService" in _cmdline(q)]
        if rete:
            pids = rete
    for q in pids:
        try:
            os.kill(q, signal.SIGSTOP if stop else signal.SIGCONT)
        except OSError:
            pass
    return len(pids)


def riprendi(g):
    return ferma(g, False)


def muovi_un_po(s, volte=3):
    """Il segno di vita di un utente vero: il puntatore si muove sulla tela."""
    try:
        geo = s.geometria()
        for k in range(volte):
            x, y = S.C21.dal_desktop_al_vetro(geo, geo["tl"] * (0.3 + 0.1 * k),
                                              geo["ta"] * 0.2)
            s.g.muovi(x, y)
            time.sleep(0.2)
        return True
    except Exception:                            # noqa: BLE001
        return False


def clic_centro(s, fy=0.47):
    geo = s.geometria()
    x, y = S.C21.dal_desktop_al_vetro(geo, geo["tl"] * 0.5, geo["ta"] * fy)
    s.g.clic(x, y)


JS_PAGINA = r"""
const e = document.getElementById('esito'), m = document.getElementById('modulo');
const a = document.getElementById('avviso');
const vis = (x) => !!x && getComputedStyle(x).display !== 'none' && x.getBoundingClientRect().width > 0;
const R = window.REMOTIX, s = R && R.schermo;
return { url: location.href, esito: e ? e.textContent : null, classe: e ? e.className : null,
         modulo: vis(m), sessione: !!(s && s.sessione),
         bannato: document.body ? (document.body.dataset.bannato || null) : null,
         avviso: a ? a.textContent : '',
         ore: (document.getElementById('ore') || {}).textContent || null,
         minuti: (document.getElementById('minuti') || {}).textContent || null,
         testo: document.body ? document.body.innerText.slice(0, 400) : '' };
"""


def leggi_pagina(g):
    try:
        return g.js(JS_PAGINA) or {}
    except Exception as e:                       # noqa: BLE001
        return {"errore": str(e)[:200]}


def carica(g, url, attesa=20):
    """Apre `url` e aspetta il documento completo; torna leggi_pagina()."""
    ok, perche = g.vai(url)
    fine = time.time() + attesa
    p = {}
    while time.time() < fine:
        try:
            if g.js("return document.readyState") == "complete":
                break
        except Exception:                        # noqa: BLE001
            pass
        time.sleep(0.4)
    p = leggi_pagina(g)
    if not ok:
        p["non_aperta"] = perche
    return p


def tenta_tenace(s, utente, parola, tetto=30, volte=3):
    """`tenta`, riprovando quando il rifiuto e' dell'AMBIENTE (vedi `AMBIENTE`).
    Torna (ammesso, stato, [rifiuti d'ambiente visti])."""
    visti = []
    for _ in range(volte):
        amm, st = tenta(s, utente, parola, tetto)
        e = (st or {}).get("esito") or ""
        if amm is False and any(a in e for a in AMBIENTE):
            visti.append(e[:80])
            time.sleep(2)
            continue
        return amm, st, visti
    return None, st, visti


def tenta_senza_ricarica(s, utente, parola, tetto=30):
    return tenta(s, utente, parola, tetto, ricarica=False)


def tenta(s, utente, parola, tetto=30, ricarica=True):
    """Ricarica la pagina, manda utente e parola, e aspetta un verdetto.
    Torna (ammesso: True/False/None, stato della pagina)."""
    if ricarica:
        s.pr.apri()
    vecchio = s.o.utente
    s.o.utente = utente
    try:
        r = s.g.js(S.VERI.JS_ENTRA, utente, parola)
    finally:
        s.o.utente = vecchio
    if r != "mandato":
        return None, {"esito": "non ho potuto compilare il modulo: %s" % r}
    fine = time.time() + tetto
    st = {}
    while time.time() < fine:
        st = s.stato()
        if st.get("sessione") and st.get("esito_classe") == "bene" \
                and (st.get("esito") or "").startswith("Ammesso"):
            return True, st
        if st.get("esito_classe") == "male" and st.get("esito") \
                and "Collego" not in (st.get("esito") or ""):
            return False, st
        time.sleep(0.4)
    return None, st


# ═══════════════════════════════════════════════════════════════════════════
#  LA RIGA DI COMANDO (per 15-g8-server.sh)
# ═══════════════════════════════════════════════════════════════════════════
def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("accendi", "spegni", "sblocca", "stato") \
            or sys.argv[2] not in PORTE_MIE:
        print(__doc__)
        return 2
    cosa, d = sys.argv[1], sys.argv[2]
    m = MioServer(d)
    if cosa == "accendi":
        ok, t = m.accendi()
        print(("⭐ acceso %s sulla %d: %s" if ok else "⛔ %s %d NON acceso: %s")
              % (d, m.porta, t))
        return 0 if ok else 1
    if cosa == "spegni":
        ok, t = m.spegni()
        print("spento %s (%s)" % (d, t.splitlines()[-1] if t else "?"))
        return 0
    if cosa == "sblocca":
        print(m.sblocca(sys.argv[3] if len(sys.argv) > 3 else INDIRIZZO))
        return 0
    print("unita': %s · PING: %s · ban: «%s» · ban dell'85xx: «%s»"
          % ("attiva" if m.acceso() else "NON attiva", m.parla("PING"), m.file_ban(),
             m.file_ban(BAN_85XX)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
