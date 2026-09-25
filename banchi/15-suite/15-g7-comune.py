#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-g7-comune — gli attrezzi del gruppo G7 (la rete che cade e gli orologi).

  · il SERVER SUO (`15-g7-server.sh`): porta 8611-8614, unita' `rete15-g7`,
    registro /var/lib/rete15-g7/registro.log dentro la scatola;
  · la LINEA MORTA simulata SUL SERVER con nftables: una tabella nostra,
    `inet remotix_g7_<porta>`, che scarta i pacchetti UDP della SOLA porta del
    server nostro (⛔ gli altri agenti usano 851x) — e si toglie SEMPRE;
  · lo STATO DELLA PAGINA che conta per queste prove: che cosa dice (esito),
    se e' ancora vestita da desktop, se il modulo si vede;
  · i processi del browser, per fermarlo (SIGSTOP) e farlo ripartire;
  · i processi dell'inquilino nella scatola (la sessione c'e' ancora?).

⛔ Si importa da `15-f019-…` e `15-f022-…` (non si copia).  Gira SUL SERVER
   come nicfio: sudo con la parola, locale.
"""
import os
import re
import signal
import subprocess
import time

QUI = os.path.dirname(os.path.abspath(__file__))
SERVER_SH = os.path.join(QUI, "15-g7-server.sh")
PORTE_G7 = {"gnome": 8611, "kde": 8612, "xfce": 8613, "lxqt": 8614}
DIR_G7 = "/var/lib/rete15-g7"
REGISTRO_G7 = DIR_G7 + "/registro.log"
PAROLA_SUDO = "nicfio\n"


def sudo(argv, secondi=60, entrata=""):
    """(codice, uscita) di `argv` con sudo, sul server (locale)."""
    try:
        r = subprocess.run(["sudo", "-S", "-p", ""] + list(argv),
                           input=PAROLA_SUDO + entrata, capture_output=True,
                           text=True, errors="replace", timeout=secondi)
    except subprocess.TimeoutExpired:
        return None, "(nessuna risposta in %d s)" % secondi
    return r.returncode, (r.stdout + r.stderr).strip()


def dentro(desktop, riga, secondi=60):
    """(codice, uscita) di `riga` da root nella scatola rete11-<desktop>."""
    return sudo(["podman", "exec", "rete11-%s" % desktop, "sh", "-c", riga], secondi)


# ═══════════════════════════════════════════════════════════════════════════
#  IL SERVER NOSTRO
# ═══════════════════════════════════════════════════════════════════════════
def server(azione, desktop, *opzioni, secondi=90):
    try:
        r = subprocess.run(["bash", SERVER_SH, azione, desktop] + list(opzioni),
                           capture_output=True, text=True, errors="replace",
                           timeout=secondi)
    except subprocess.TimeoutExpired:
        return False, "(15-g7-server.sh %s: nessuna risposta in %d s)" % (azione, secondi)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def orologi_in_vigore(desktop):
    """La riga d'avvio coi tre orologi di §5.3: (inattivita_s, abbandono_s, riga)."""
    _c, t = dentro(desktop, "grep -a '§5.3, i tre orologi' %s | tail -1" % REGISTRO_G7)
    m1 = re.search(r"inattivita' dell'utente (\d+) s", t or "")
    m2 = re.search(r"abbandono della sessione (\d+) s", t or "")
    return (int(m1.group(1)) if m1 else None, int(m2.group(1)) if m2 else None,
            (t or "").strip())


class Registro:
    """Il registro del server NOSTRO, con la stessa forma di Scatola."""

    def __init__(self, desktop, percorso=REGISTRO_G7):
        self.d, self.p = desktop, percorso

    def righe(self):
        _c, t = dentro(self.d, "wc -l < %s" % self.p, 30)
        try:
            return int(t.split()[-1])
        except (ValueError, IndexError, AttributeError):
            return None

    def da(self, segno, chi=None):
        filtro = (" | grep -a -- '%s'" % chi) if chi else ""
        _c, t = dentro(self.d, "tail -n +%d %s%s" % ((segno or 0) + 1, self.p, filtro), 60)
        return (t or "").splitlines()

    def aspetta(self, segno, forme, chi=None, tetto=60, passo=1.0):
        """(forma, riga, secondi) della prima riga con una delle `forme`."""
        t0 = time.time()
        while time.time() - t0 < tetto:
            for r in self.da(segno, chi):
                for f in forme:
                    if f in r:
                        return f, r, time.time() - t0
            time.sleep(passo)
        return None, None, time.time() - t0


# ═══════════════════════════════════════════════════════════════════════════
#  LA LINEA MORTA — nftables sul server, SOLO la porta nostra
# ═══════════════════════════════════════════════════════════════════════════
class LineaMorta:
    """
        with LineaMorta(8611) as lm:   # da qui niente UDP da/per la 8611
            ...
        # qui la regola non c'e' piu' (anche se il corpo e' caduto)

    ⛔ Una tabella NOSTRA (`inet remotix_g7_<porta>`): si toglie con un
       `delete table` e non tocca le regole di nessun altro.  Scarta l'UDP
       (QUIC/WebTransport) in ingresso E in uscita, nei due versi della porta:
       il browser e il server stanno sulla stessa macchina (passa da `lo`), e il
       pacchetto attraversa `output` e poi `input`.
    ⚠ Il TCP (la pagina HTTPS) resta: la linea che cade e' quella della
      sessione.  Dichiarato: e' la rete del server, non il percorso vero dal
      tablet."""

    def __init__(self, porta):
        self.porta = int(porta)
        assert 8600 <= self.porta <= 8699, "solo le porte del server nostro"
        self.tabella = "remotix_g7_%d" % self.porta
        self.messa = None

    def regole(self):
        p = self.porta
        return ("table inet %(t)s {\n"
                " chain dentro { type filter hook input priority -10; policy accept;\n"
                "  udp dport %(p)d counter drop\n  udp sport %(p)d counter drop\n }\n"
                " chain fuori { type filter hook output priority -10; policy accept;\n"
                "  udp dport %(p)d counter drop\n  udp sport %(p)d counter drop\n }\n"
                "}\n" % {"t": self.tabella, "p": p})

    def togli(self):
        sudo(["/usr/sbin/nft", "delete", "table", "inet", self.tabella], 30)
        c, t = sudo(["/usr/sbin/nft", "list", "tables"], 30)
        return self.tabella not in (t or "")

    def metti(self):
        self.togli()                              # un avanzo di un giro caduto
        # ⚠ Da FILE, non da stdin: con sudo gia' autenticato la parola non si
        #   consuma e finirebbe dentro le regole (`[M]` «syntax error … nicfio»).
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".nft", delete=False) as f:
            f.write(self.regole())
        try:
            c, t = sudo(["/usr/sbin/nft", "-f", f.name], 30)
        finally:
            os.unlink(f.name)
        if c != 0:
            raise RuntimeError("nft non ha messo la regola: %s" % t[-200:])
        self.messa = time.time()
        return True

    def contati(self):
        """I pacchetti scartati (testimone che la regola MORDE)."""
        _c, t = sudo(["/usr/sbin/nft", "list", "table", "inet", self.tabella], 30)
        return sum(int(x) for x in re.findall(r"packets (\d+)", t or ""))

    def __enter__(self):
        self.metti()
        return self

    def __exit__(self, *a):
        tolta = self.togli()
        if not tolta:
            print("   ⛔ LA REGOLA nft %s NON SI TOGLIE" % self.tabella, flush=True)
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  LA PAGINA
# ═══════════════════════════════════════════════════════════════════════════
JS_PAGINA = r"""
const e = document.getElementById('esito');
const m = document.getElementById('modulo');
const reg = document.getElementById('registro');
const vis = (x) => !!x && getComputedStyle(x).display !== 'none'
                  && getComputedStyle(x).visibility !== 'hidden'
                  && x.getBoundingClientRect().width > 0;
const R = window.REMOTIX, s = R && R.schermo;
const righe = reg ? reg.textContent.split('\n') : [];
return {
  esito: e ? e.textContent : null,
  esito_classe: e ? e.className : null,
  esito_visibile: vis(e) && !!(e && e.textContent.trim()),
  modulo_visibile: vis(m),
  vestita: document.body ? (document.body.dataset.schermo || null) : null,
  sessione: !!(s && s.sessione),
  input: !!window.REMOTIX_INPUT,
  dipinti: s && s.conti ? s.conti.dipinti : null,
  coda: righe.filter(r => r.indexOf('audio:') !== 0).slice(-14),
  n_righe: righe.length,
  testo: document.body ? document.body.innerText.slice(0, 400) : ''
};
"""


def pagina(g):
    try:
        return g.js(JS_PAGINA) or {}
    except Exception as e:                       # noqa: BLE001
        return {"errore": str(e)[:200]}


def la_pagina_lo_dice(st):
    """⭐ La pagina DICE all'utente che il filo e' caduto: una frase visibile
    nella riga dell'esito, o il modulo di accesso tornato in vista (e il
    vestito da desktop tolto).  ⛔ Il registro nascosto (`#registro`, spento
    di serie) non e' «dirlo»: l'utente non lo vede."""
    if not isinstance(st, dict) or st.get("errore"):
        return None
    if st.get("esito_visibile") and st.get("esito_classe") == "male":
        return True
    if st.get("modulo_visibile") and not st.get("vestita"):
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════
#  IL BROWSER: fermarlo e farlo ripartire (tutto l'albero dei processi)
# ═══════════════════════════════════════════════════════════════════════════
def discendenti(pid):
    figli = {}
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            with open("/proc/%s/stat" % d) as f:
                st = f.read()
            pp = int(st.rsplit(")", 1)[1].split()[1])
        except Exception:                        # noqa: BLE001
            continue
        figli.setdefault(pp, []).append(int(d))
    tutti, coda = [], [pid]
    while coda:
        p = coda.pop()
        tutti.append(p)
        coda.extend(figli.get(p, []))
    return tutti


def pid_browser(g):
    p = getattr(g, "p", None)
    return getattr(p, "pid", None)


def segnale_albero(g, sig):
    pid = pid_browser(g)
    if not pid:
        return []
    fatti = []
    for p in discendenti(pid):
        try:
            os.kill(p, sig)
            fatti.append(p)
        except ProcessLookupError:
            pass
    return fatti


def ferma_browser(g):
    return segnale_albero(g, signal.SIGSTOP)


def riprendi_browser(g):
    return segnale_albero(g, signal.SIGCONT)


# ═══════════════════════════════════════════════════════════════════════════
#  L'INQUILINO NELLA SCATOLA
# ═══════════════════════════════════════════════════════════════════════════
def processi_inquilino(desktop, chi):
    """{pid: comando} dei processi dell'inquilino (vuoto = la sessione non c'e')."""
    _c, t = dentro(desktop, "ps -u %s -o pid=,comm= 2>/dev/null" % chi, 30)
    ps = {}
    for r in (t or "").splitlines():
        a = r.split(None, 1)
        if len(a) == 2 and a[0].isdigit():
            ps[int(a[0])] = a[1].strip()
    return ps


def nella_sessione(s, comando, secondi=60):
    """Come `Sessione.nella_sessione(fondo=True)`, ma da qui (sudo locale sul
    server) invece che per ssh: `[M]` 24 set, con dieci agenti insieme l'ssh
    del banco verso il server stesso cade («Connection closed … port 22»)."""
    chi = s.chi
    amb = ("u=$(id -u %(c)s); d=$(ls /run/user/$u 2>/dev/null | grep -E '^wayland-[0-9]+$' "
           "| head -1); [ -n \"$d\" ] || { echo 'nessun socket wayland'; exit 2; }; "
           % {"c": chi})
    corpo = ("runuser -u %(c)s -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
             "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
             "XDG_SESSION_TYPE=wayland HOME=/home/%(c)s sh -c %(q)s"
             % {"c": chi, "q": S_q(comando)})
    corpo = "setsid %s < /dev/null > /home/%s/.g7-%s.log 2>&1 & echo lanciato" % (
        corpo, chi, re.sub(r"\W", "", comando.split()[0])[:20])
    return dentro(s.o.scatola, amb + corpo, secondi)


def S_q(x):
    return "'" + x.replace("'", "'\"'\"'") + "'"


def lancia_scena(s, S=None, cosa="scena"):
    """La SCENA IN MOVIMENTO dentro la sessione: `weston-simple-egl -f` — il
    triangolo che gira, a tutto schermo, disegnato dalla scheda (EGL) e nativo
    Wayland: c'e' in tutt'e quattro le scatole.
    ⛔ Non la scena di C3 in firefox-esr: `[M]` 24 set 2026 su GNOME, firefox-esr
       lanciato cosi' non scrive un byte nel profilo e apre «Your Firefox profile
       cannot be loaded» (anche col profilo preparato come C21, anche headless
       con un utente di prova) ⇒ la scena non compariva mai.
    Torna (pid | None, testo)."""
    c, t = nella_sessione(s, "weston-simple-egl -f", 60)
    for _ in range(40):
        ps = processi_inquilino(s.o.scatola, s.chi)
        f = [p for p, n in ps.items() if n.startswith("weston-simple")]
        if f:
            return min(f), "weston-simple-egl della %s: pid %d" % (cosa, min(f))
        time.sleep(0.5)
    return None, "weston-simple-egl non si e' visto partire: %s" % (t or "")[-200:]


def lancia_tono(s, secondi=600):
    """pw-play di un'onda a 440 Hz sul sink «remotix» del prodotto, in ciclo."""
    corpo = ("python3 -c \"import math,struct,wave;w=wave.open('/tmp/g7-onda-%(c)s.wav','wb');"
             "w.setnchannels(2);w.setsampwidth(2);w.setframerate(48000);"
             "w.writeframes(b''.join(struct.pack('<hh',int(16000*math.sin(2*math.pi*440*i/48000)),"
             "int(16000*math.sin(2*math.pi*440*i/48000))) for i in range(48000*5)));w.close()\" "
             "&& end=$(( $(date +%%s) + %(s)d )); while [ $(date +%%s) -lt $end ]; do "
             "pw-play --target=remotix /tmp/g7-onda-%(c)s.wav; done"
             % {"c": s.chi, "s": secondi})
    return nella_sessione(s, corpo, 60)


# ⭐ L'ORECCHIO: si avvolge `AudioBufferSourceNode.start` della pagina, e per
#   ogni buffer che la pagina manda davvero all'uscita si misura l'RMS dei
#   CAMPIONI (non si contano blocchi: un flusso di zeri sono blocchi che
#   arrivano ed e' silenzio).  Si mette dopo il carico, prima dell'accesso:
#   la pagina crea le sorgenti solo a sessione aperta.
JS_ORECCHIO = r"""
if (window.__G7_ORECCHIO__) return 'gia';
const O = window.__G7_ORECCHIO__ = { finestre: [] };
const vero = AudioBufferSourceNode.prototype.start;
AudioBufferSourceNode.prototype.start = function () {
  try {
    const b = this.buffer;
    if (b && b.numberOfChannels > 0) {
      const d = b.getChannelData(0);
      let q = 0;
      for (let i = 0; i < d.length; i++) q += d[i] * d[i];
      const t = Math.floor(performance.now() / 1000);
      let f = O.finestre[O.finestre.length - 1];
      if (!f || f.t !== t) { f = { t: t, n: 0, q: 0, c: 0 }; O.finestre.push(f);
                             if (O.finestre.length > 900) O.finestre.shift(); }
      f.q += q; f.c += d.length; f.n += 1;
    }
  } catch (e) {}
  return vero.apply(this, arguments);
};
return 'messo';
"""

JS_ASCOLTA = r"""
const O = window.__G7_ORECCHIO__;
if (!O) return null;
const da = arguments[0], a = arguments[1];
let q = 0, c = 0, n = 0;
for (const f of O.finestre) if (f.t >= da && f.t < a) { q += f.q; c += f.c; n += f.n; }
return { rms: c ? Math.sqrt(q / c) : null, campioni: c, buffer: n,
         adesso: Math.floor(performance.now() / 1000) };
"""

SOGLIA_RMS = 0.01      # l'onda e' 16000/32767 ≈ 0,49 di picco ⇒ RMS ≈ 0,35


def orecchio(g):
    try:
        return g.js(JS_ORECCHIO)
    except Exception as e:                       # noqa: BLE001
        return "non messo: %s" % str(e)[:120]


def ascolta(g, secondi):
    """(rms | None, dettagli) sugli ultimi `secondi` di suono SUONATO dalla pagina."""
    try:
        ora = g.js("return Math.floor(performance.now() / 1000);")
        r = g.js(JS_ASCOLTA, ora - secondi, ora + 1)
    except Exception as e:                       # noqa: BLE001
        return None, "orecchio illeggibile: %s" % str(e)[:120]
    if not r:
        return None, "l'orecchio non c'e' sulla pagina"
    return r.get("rms"), r


# ═══════════════════════════════════════════════════════════════════════════
#  LE FOTOGRAFIE: la scena si muove?
# ═══════════════════════════════════════════════════════════════════════════
def diversita(png_a, png_b):
    """Frazione di pixel che cambiano (|Δ| > 40 su un canale) fra due foto,
    a scala ridotta.  None se non si possono confrontare."""
    try:
        import io
        from PIL import Image, ImageChops
        a = Image.open(io.BytesIO(png_a)).convert("RGB").resize((320, 180))
        b = Image.open(io.BytesIO(png_b)).convert("RGB").resize((320, 180))
        d = ImageChops.difference(a, b).getdata()
        cambiati = sum(1 for p in d if max(p) > 40)
        return cambiati / float(len(d))
    except Exception:                            # noqa: BLE001
        return None


def colori_scena(png):
    """Quota di pixel blu (#0000FF) e gialli (#FFFF00) della scena di C3."""
    try:
        import io
        from PIL import Image
        im = Image.open(io.BytesIO(png)).convert("RGB").resize((320, 180))
        px = list(im.getdata())
        blu = sum(1 for r, g_, b in px if b > 180 and r < 80 and g_ < 80)
        gia = sum(1 for r, g_, b in px if r > 180 and g_ > 180 and b < 80)
        return blu / float(len(px)), gia / float(len(px))
    except Exception:                            # noqa: BLE001
        return None, None


def aspetta_scena(s, S, tetto=40):
    """(True | None, descrizione): la scena in movimento in vista entro
    `tetto` — due fotografie a 0,7 s che differiscono per > 2 % dei pixel."""
    t0 = time.time()
    desc = ""
    prima = None
    while time.time() - t0 < tetto:
        try:
            png = S.C21.foto_piena(s.g)
        except Exception as e:                   # noqa: BLE001
            png, desc = None, str(e)[:120]
        if png and prima:
            d = diversita(prima, png)
            desc = "cambio %.1f%%" % (100 * (d or 0))
            if d and d > 0.02:
                return True, "scena in movimento dopo %.0f s (%s)" % (time.time() - t0, desc)
        prima = png
        time.sleep(0.7)
    return None, "la scena in movimento non e' comparsa in %d s (%s)" % (tetto, desc)


def la_scena_si_muove(s, nome, coppie=3, pausa=0.7):
    """(True/False/None, descrizione, [percorsi]) — foto a distanza di
    `pausa`: almeno una coppia diversa per > 2 % dei pixel."""
    foto, ev = [], []
    for i in range(coppie + 1):
        png, dove = s.foto("%s-%d" % (nome, i))
        if not png:
            return None, "fotografia fallita: %s" % dove, ev
        foto.append(png)
        if dove:
            ev.append(dove)
        time.sleep(pausa)
    diffs = [diversita(foto[i], foto[i + 1]) for i in range(coppie)]
    if any(d is None for d in diffs):
        return None, "foto non confrontabili", ev
    desc = "cambi fra foto %s" % ["%.1f%%" % (100 * d) for d in diffs]
    return max(diffs) > 0.02, desc, ev


# ═══════════════════════════════════════════════════════════════════════════
#  ⛔ LA SCATOLA SENZA SSH, quando si gira SUL SERVER
# ═══════════════════════════════════════════════════════════════════════════
def scatola_locale(S):
    """`[M]` 24 set 2026, dieci agenti insieme: `Scatola.dentro()` passa per
    `sshpw.py` → ssh verso il server STESSO, e sshd ne tronca una parte
    («Connection closed by 192.168.0.2 port 22») ⇒ inquilini non creati,
    BLOCKED che non sono del prodotto.  Sul server (REMOTIX_SUL_SERVER=1) si
    esegue la stessa riga con `sudo podman exec` locale.  ⚠ Si cambia la
    classe caricata da suite.py in QUESTO processo, non suite.py."""
    if os.environ.get("REMOTIX_SUL_SERVER") != "1":
        return False

    def _dentro(self, riga, secondi=90):
        c, t = sudo(["podman", "exec", self.contenitore, "sh", "-c", riga], secondi)
        return c, (t or "").strip()
    S.C20V.Scatola.dentro = _dentro
    return True
