#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
16-salita — UNA SALITA A GRADINI DELLA FASE 16 (fasi/16-stress-e-capacita.md §6)
===========================================================================

    (sul server, come nicfio — i browser-cliente girano la', §2)
    python3 16-salita.py --scatola gnome --campagna intel-4k-gnome --misura 4k
    python3 16-salita.py --scatola lxqt --campagna taratura --misura 4k --prova
    python3 16-salita.py ... --secco              # il piano, senza fare niente

    opzioni:  --gradini 1,4,8,12,16  --minuti 10  --minuti-ultimo 30
              --controllo-min 2  --seme-base 1600  --fps-video F  --video URL
              --tetto 17  --porte-base 9900  --prova (§13.3: 1,2,4 da 3 min)

CHE COSA FA
  0. guarda che il server sia VUOTO: nessun inquilino c16*, nessun browser dei
     banchi, nessuna sessione nella scatola, nessun'altra salita — se no si
     ferma BLOCKED con la ragione (codice 3);
  1. rifa' la scatola DA ZERO (11-accendi.sh accendi · prodotto · server, come
     15-rifai-scatole.sh) col server acceso a `--tetto` sessioni
     (REMOTIX_TETTO_SESSIONI, vedi 11-accendi.sh) e GUARDA nel registro che il
     tetto sia entrato in vigore;
  2. per ogni gradino: accende i compositori che servono (16-compositori.sh),
     fa entrare gli attori mancanti (16-attore.py, un processo per utente,
     indipendente: seme = seme-base + N, porte-base + 10·N, il suo labwc) —
     uno dopo l'altro, ciascuno quando il precedente ha il primo fotogramma
     (§6: cosi' si misura la nascita sotto carico) —, 16-risorse.py per tutto
     il livello, i minuti del livello a lavoro stabile; negli ultimi
     `--controllo-min` minuti SIGUSR1 agli attori (la foto piena di ogni tela)
     e il controllo corto (16-controllo-corto.py, una sessione sua, browser
     alternato fra i livelli); poi il registro del server tagliato sul
     livello, le serie degli attori tagliate sul livello, livello.json, e
     16-classifica.py;
  3. la regola di non-prosecuzione (§6, §14): FAIL o DEGRADED significativo ⇒
     il livello si RIPETE una volta nelle stesse condizioni (scatola pulita,
     gli stessi N utenti coi loro semi); se si conferma ⇒ la RICERCA A META'
     fra l'ultimo gradino buono e quello rotto, ogni livello da scatola pulita,
     finche' si sa il confine preciso a un utente; poi si ferma;
  4. l'ultimo gradino dura `--minuti-ultimo` (le perdite di memoria, §6);
  5. alla fine: attori fermati (SIGTERM: sgomberano da se'), inquilini c16*
     sgomberati comunque, compositori spenti, il server rimesso col tetto
     predefinito (se non --lascia-tetto).

LE EVIDENZE (§10) in /media/REMOTIX/misure/fase16/<campagna>/:
    stato.json              il punto corrente, per il coordinatore
    salita.jsonl            una riga per livello (meta + classe)
    salita.log              quel che esce qui, con gli orari
    attori-<k>/utente-NN/   quel che scrivono gli attori (k: una per scatola pulita)
    livello-NN[-ripetizione]/
        livello.json        meta: campagna, livello, utenti, orari, commit,
                            binario, pagina, kernel, schede, misura, tetto…
        utente-NN/          stato.jsonl TAGLIATO sul livello, nascita.json,
                            foto e altri file dell'attore nati nel livello
        risorse.jsonl       16-risorse.py
        controllo-corto.json, controllo-corto/
        server.log (registro.log del prodotto, dal segno) · journal-err.jsonl
        (journalctl -t remotix -p err -o json) · journal-server.log
        (journalctl -u rete11-server) · journal-scatola.log (tutto il journal)
        classifica.log      l'uscita di 16-classifica.py

⛔ Le soglie sono di 16-classifica.py (§9, ferme): qui non si giudica niente,
   si legge la classe che dice lui.
"""
import argparse
import datetime
import fcntl
import glob
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time

QUI = os.path.dirname(os.path.abspath(__file__))
BANCHI = os.path.dirname(QUI)
RETE11 = os.environ.get("REMOTIX_RETE11", "/media/REMOTIX/rete11")
MISURE = os.environ.get("REMOTIX_MISURE_16", "/media/REMOTIX/misure/fase16")
PRODOTTO16 = os.environ.get("REMOTIX_PRODOTTO_16", "/media/REMOTIX/src/16-prodotto")
PORTE = {"gnome": 8511, "kde": 8512, "xfce": 8513, "lxqt": 8514}
MISURE_SCHERMO = {"4k": (3840, 2160), "3k": (3200, 1800), "2k": (2560, 1440),
                  "fhd": (1920, 1080)}
SCHEDE_NOTE = {"8086:4680": "Intel UHD 770 (i5-13500T)", "1002:73bf": "AMD Radeon RX 6800"}
CLASSI = ("GREEN", "DEGRADED", "FAIL")
UID = os.getuid()
RUN = "/run/user/%d" % UID
COMPOSITORI = os.path.join(RUN, "16-compositori")
INQUILINO_16 = re.compile(r"^c16[0-9]+u[0-9]+$")
AMBIENTE_BROWSER = {
    "XDG_RUNTIME_DIR": RUN, "REMOTIX_SCHERMO_ANNIDATO": "1", "REMOTIX_SUL_SERVER": "1",
    "MOZ_ENABLE_WAYLAND": "1",
    "REMOTIX_CHROME_OPZIONI": "--ozone-platform=wayland --disable-backgrounding-occluded-windows "
                              "--disable-renderer-backgrounding --disable-background-timer-throttling"}

_stampa = threading.Lock()
_log_file = None


def ora():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def dice(msg):
    riga = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with _stampa:
        print(riga, flush=True)
        if _log_file:
            _log_file.write(riga + "\n")
            _log_file.flush()


def _parola_sudo():
    """La parola di sudo del server: da REMOTIX_PAROLA_SUDO, o dalla riga «pass:» di
    ~/SERVER.ssh. ⛔ Mai scritta nei banchi: sono nel deposito."""
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


def sudo(comando, secondi=300):
    try:
        r = subprocess.run(["sudo", "-S", "-p", "", "sh", "-c", comando], input=_parola_sudo(),
                           capture_output=True, text=True, errors="replace", timeout=secondi)
    except subprocess.TimeoutExpired:
        return None, "(nessuna risposta in %d s)" % secondi
    return r.returncode, (r.stdout + r.stderr).strip()


def _q(s):
    return "'" + s.replace("'", "'\"'\"'") + "'"


def nella_scatola(d, comando, secondi=120):
    return sudo("podman exec rete11-%s sh -c %s" % (d, _q(comando)), secondi)


def scrivi_json(p, dati):
    with open(p + ".tmp", "w", encoding="utf-8") as f:
        json.dump(dati, f, ensure_ascii=False, indent=1)
    os.replace(p + ".tmp", p)


def md5_8(p, quanti=8):
    try:
        h = hashlib.md5()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()[:quanti]
    except OSError:
        return "?"


def comando(argv, secondi=30):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, errors="replace",
                           timeout=secondi)
        return (r.stdout + r.stderr).strip()
    except Exception as e:                       # noqa: BLE001
        return "? (%s)" % e


# ═══════════════════════════════════════════════════════════════════════════
#  LA MACCHINA: che cosa si misura (§10, in ogni riga)
# ═══════════════════════════════════════════════════════════════════════════
def schede():
    out = []
    for c in sorted(glob.glob("/sys/class/drm/card[0-9]")):
        try:
            v = open(c + "/device/vendor").read().strip().replace("0x", "")
            dv = open(c + "/device/device").read().strip().replace("0x", "")
            drv = os.path.basename(os.path.realpath(c + "/device/driver"))
        except OSError:
            continue
        pci = os.path.basename(os.path.realpath(c + "/device"))
        idn = "%s:%s" % (v, dv)
        out.append({"scheda": SCHEDE_NOTE.get(idn, idn), "id": idn, "driver": drv, "pci": pci})
    return out


def meta_macchina(o):
    m = {"kernel": os.uname().release,
         "cpu": next((r.split(":", 1)[1].strip() for r in open("/proc/cpuinfo")
                      if r.startswith("model name")), "?"),
         "schede": schede(),
         "prodotto_binario": md5_8(os.path.join(RETE11, "prodotto", "remotix")),
         "prodotto_pagina": md5_8(os.path.join(RETE11, "prodotto", "pagina.html")),
         "firefox": comando(["firefox", "--version"]),
         "chrome": comando(["google-chrome", "--version"])}
    try:
        m["commit_banchi"] = open(os.path.join(BANCHI, "..", "VERSIONE")).read().strip()
    except OSError:
        m["commit_banchi"] = "?"
    try:
        m["scheda_compositori"] = open(os.path.join(COMPOSITORI, "render")).read().strip()
    except OSError:
        m["scheda_compositori"] = "?"
    # ⭐ il commit del PRODOTTO: /media/REMOTIX/src/16-prodotto/VERSIONE, valido solo se
    #   il binario di la' e' LO STESSO di rete11/prodotto (md5 intero)
    m["commit_prodotto"] = None
    b = os.path.join(PRODOTTO16, "src", "remotix")
    if os.path.exists(b) and md5_8(b, 32) == md5_8(os.path.join(RETE11, "prodotto", "remotix"), 32):
        try:
            m["commit_prodotto"] = open(os.path.join(PRODOTTO16, "VERSIONE")).read().strip()
        except OSError:
            pass
    return m


def render_intel():
    """Il nodo di disegno della Intel integrata, per indirizzo PCI (come 11-accendi.sh)."""
    for s in schede():
        if s["driver"] in ("i915", "xe"):
            p = os.path.realpath("/dev/dri/by-path/pci-%s-render" % s["pci"])
            if os.path.exists(p):
                return p, s["pci"]
    return None, None


def ambiente_browser(s):
    """L'ambiente dei browser-cliente (attori e controllo).  ⭐ Chrome si inchioda
    alla Intel (--render-node-override): renderD128/129 si scambiano fra due avvii,
    e sul server c'e' anche la RX 6800.  Firefox segue il labwc (che e' sulla Intel)."""
    amb = dict(os.environ, WAYLAND_DISPLAY=s, **AMBIENTE_BROWSER)
    nodo, _pci = render_intel()
    if nodo:
        amb["REMOTIX_16_CHROME_IN_PIU"] = "--render-node-override=%s" % nodo
        amb["REMOTIX_CHROME_OPZIONI"] += " --render-node-override=%s" % nodo
    return amb


def browser_fuori_scheda(dirliv):
    """Dalla serie delle risorse: i processi dei browser-cliente (recinti `browser`
    e `labwc_cliente`) che disegnano su una scheda che NON e' la Intel."""
    _n, pci = render_intel()
    fuori, visti = {}, 0
    try:
        for r in open(os.path.join(dirliv, "risorse.jsonl"), encoding="utf-8", errors="replace"):
            try:
                d = json.loads(r)
            except ValueError:
                continue
            for p in d.get("processi_gpu") or []:
                if p.get("recinto") not in ("browser", "labwc_cliente"):
                    continue
                visti += 1
                if pci and p.get("pdev") and p["pdev"] != pci:
                    k = "%s@%s" % (p.get("comm"), p["pdev"])
                    fuori[k] = fuori.get(k, 0) + 1
    except OSError:
        return None
    return {"campioni_browser": visti, "fuori_intel": fuori, "intel": pci}


def meta_scatola(d):
    """Dentro la scatola: binario e pagina IN USO, la scheda che vede, i driver."""
    v = {}
    _c, t = nella_scatola(d, "md5sum /opt/remotix/remotix /opt/remotix/pagina.html; "
                             "echo @@; ls /dev/dri; echo @@; dpkg-query -W -f "
                             "'${Package}=${Version}\\n' intel-media-va-driver "
                             "intel-media-va-driver-non-free mesa-va-drivers libva2 "
                             "libgl1-mesa-dri 2>/dev/null; echo @@; "
                             "systemctl show -p ExecStart --value rete11-server 2>/dev/null "
                             "| tr ' ' '\\n' | grep -A1 -E '^--(tetto-sessioni|journal)' "
                             "| tr '\\n' ' '", 60)
    parti = (t or "").split("@@")
    while len(parti) < 4:
        parti.append("")
    for riga in parti[0].splitlines():
        p = riga.split()
        if len(p) == 2:
            v["binario" if p[1].endswith("remotix") else "pagina"] = p[0][:8]
    v["dri_nella_scatola"] = parti[1].split()
    v["driver_video"] = [x for x in parti[2].split() if "=" in x and not x.endswith("=")]
    v["opzioni_server"] = parti[3].strip()
    v["journal"] = "--journal" in parti[3]
    return v


# ═══════════════════════════════════════════════════════════════════════════
#  IL SERVER VUOTO (§6.1, §13.0)
# ═══════════════════════════════════════════════════════════════════════════
def scatole_accese():
    c, t = sudo("podman ps --format '{{.Names}}'", 60)
    return [x for x in (t or "").split() if x.startswith("rete11-")]


def perche_non_vuoto(d):
    guai = []
    for s in scatole_accese():
        _c, t = sudo("podman exec %s awk -F: '$1 ~ /^c16[0-9]+u[0-9]+$/ {print $1}' /etc/passwd"
                     % s, 60)
        if t.strip():
            guai.append("in %s ci sono inquilini della fase 16: %s" % (s, " ".join(t.split())))
    if "rete11-%s" % d in scatole_accese():
        _c, t = nella_scatola(d, "loginctl list-users --no-legend 2>/dev/null | awk '{print $2}'")
        chi = [u for u in (t or "").split() if u and u not in ("root",)]
        if chi:
            guai.append("in rete11-%s ci sono sessioni: %s" % (d, " ".join(chi)))
    me = os.getpid()
    t = comando(["pgrep", "-u", str(UID), "-af",
                 "marionette|remote-debugging-port|16-attore|16-controllo-corto"])
    browser = [r for r in t.splitlines() if r.strip() and not r.startswith("%d " % me)
               and "pgrep" not in r]
    if browser:
        guai.append("%d processi di browser/attori dei banchi vivi (es. %s)" % (
            len(browser), browser[0][:120]))
    return guai


# ═══════════════════════════════════════════════════════════════════════════
#  LA SCATOLA
# ═══════════════════════════════════════════════════════════════════════════
def rifai_scatola(o, d, tetto, dove):
    """accendi · prodotto · server, come 15-rifai-scatole.sh.  (ok, motivo)"""
    for passo in ("accendi", "prodotto", "server"):
        amb = "env REMOTIX_TETTO_SESSIONI=%d " % tetto if (passo == "server" and tetto) else ""
        t0 = time.time()
        c, t = sudo("cd %s && %sbash 11-accendi.sh %s %s" % (RETE11, amb, passo, d), 900)
        with open(os.path.join(dove, "scatola-%s.log" % passo), "a") as f:
            f.write("=== %s\n%s\n" % (ora(), t))
        ultima = [x for x in (t or "").splitlines() if x.strip()][-1:] or [""]
        dice("   scatola %s: codice %s in %.0f s · %s" % (passo, c, time.time() - t0,
                                                         re.sub(r"\x1b\[[0-9;]*m", "", ultima[0])[:120]))
        if c != 0:
            return False, "11-accendi.sh %s %s non riuscito (codice %s): %s" % (
                passo, d, c, re.sub(r"\x1b\[[0-9;]*m", "", " ".join((t or "").splitlines()[-3:]))[:300])
    if tetto:
        v = tetto_in_vigore(d)
        if v != tetto:
            return False, "il server non dice «tetto AMMINISTRATIVO delle sessioni: **%d**» " \
                          "(dice %s)" % (tetto, v)
        dice("   ⭐ tetto delle sessioni in vigore: %d" % v)
    return True, ""


def tetto_in_vigore(d):
    _c, t = nella_scatola(d, "{ cat /var/lib/rete11/registro.log 2>/dev/null; journalctl -u "
                             "rete11-server -b --no-pager -o cat 2>/dev/null; } | grep -a "
                             "'tetto AMMINISTRATIVO delle sessioni' | tail -1", 60)
    m = re.search(r"sessioni: \*\*(\d+)\*\*", t or "")
    return int(m.group(1)) if m else None


SGOMBERO_16 = r"""
for u in $(awk -F: '$1 ~ /^c16[0-9]+u[0-9]+$/ {print $1}' /etc/passwd); do
  id=$(id -u "$u" 2>/dev/null)
  m="runuser -u [$(printf %s "$u" | cut -c1)]$(printf %s "$u" | cut -c2-) "
  loginctl terminate-user "$u" >/dev/null 2>&1
  pkill -KILL -f "$m" >/dev/null 2>&1; pkill -KILL -u "$u" >/dev/null 2>&1
  sleep 0.2
  userdel -r "$u" >/dev/null 2>&1 || userdel "$u" >/dev/null 2>&1
  [ -n "$id" ] && systemctl reset-failed "user@$id.service" >/dev/null 2>&1
  [ -n "$id" ] && find /tmp -maxdepth 1 -uid "$id" -exec rm -rf {} + 2>/dev/null
  echo "sgomberato $u"
done; true
"""


def sgombera_16(d):
    """Gli inquilini c16* via dalla scatola (la riga di 15-giro.py, solo i nostri)."""
    _c, t = nella_scatola(d, SGOMBERO_16, 300)
    n = len([r for r in (t or "").splitlines() if r.startswith("sgomberato")])
    if n:
        dice("   sgomberati %d inquilini c16 rimasti" % n)


# ═══════════════════════════════════════════════════════════════════════════
#  I COMPOSITORI
# ═══════════════════════════════════════════════════════════════════════════
def compositori(azione, *arg):
    r = subprocess.run(["bash", os.path.join(QUI, "16-compositori.sh"), azione] + list(arg),
                       capture_output=True, text=True, errors="replace", timeout=300)
    return r.returncode, r.stdout + r.stderr


def socket_di(n):
    try:
        s = open(os.path.join(COMPOSITORI, "u%02d" % n)).read().strip()
    except OSError:
        return None
    return s if s and os.path.exists(os.path.join(RUN, s)) else None


# ═══════════════════════════════════════════════════════════════════════════
#  GLI ATTORI
# ═══════════════════════════════════════════════════════════════════════════
class Attore:
    def __init__(self, o, n, livello, cartella):
        self.o, self.n, self.livello, self.cartella = o, n, livello, cartella
        self.dir_utente = os.path.join(cartella, "utente-%02d" % n)
        self.proc = None
        self.partito = None
        self.nato = None
        self.morto_annotato = False

    def avvia(self):
        s = socket_di(self.n)
        if not s:
            raise RuntimeError("il compositore u%02d non c'e'" % self.n)
        largo, alto = self.o.largo, self.o.alto
        cmd = [sys.executable, self.o.prog_attore, "--scatola", self.o.scatola,
               "--utente", str(self.n), "--wayland", s, "--dir", self.cartella,
               "--seme", str(self.o.seme_base + self.n), "--largo", str(largo),
               "--alto", str(alto), "--porte-base", str(self.o.porte_base + 10 * self.n)]
        if self.o.video:
            cmd += ["--video", self.o.video]
        amb = ambiente_browser(s)
        os.makedirs(self.dir_utente, exist_ok=True)
        self.log = open(os.path.join(self.cartella, "utente-%02d.log" % self.n), "a")
        self.log.write("=== %s %s\n" % (ora(), " ".join(cmd)))
        self.log.flush()
        self.proc = subprocess.Popen(cmd, stdout=self.log, stderr=subprocess.STDOUT,
                                     env=amb, cwd=QUI, start_new_session=True)
        self.partito = time.time()
        return s

    def vivo(self):
        return self.proc is not None and self.proc.poll() is None

    def e_nato(self):
        if self.nato is None and os.path.exists(os.path.join(self.dir_utente, "nascita.json")):
            self.nato = time.time()
        return self.nato is not None

    def segnale(self, sig):
        if self.vivo():
            try:
                os.kill(self.proc.pid, sig)
            except OSError:
                pass

    def uccidi(self):
        if self.proc is not None:
            try:
                os.killpg(self.proc.pid, signal.SIGKILL)
            except OSError:
                pass


# ═══════════════════════════════════════════════════════════════════════════
#  LA SALITA
# ═══════════════════════════════════════════════════════════════════════════
class Salita:
    def __init__(self, o):
        self.o = o
        self.base = os.path.join(MISURE, o.campagna)
        self.attori = {}                 # n -> Attore
        self.giro_attori = 0             # una cartella attori-<k> per scatola pulita
        self.cartella_attori = None
        self.storia = []
        self.livelli_fatti = 0
        self.fermati = False
        self.stato = {"campagna": o.campagna, "scatola": o.scatola, "misura": o.misura,
                      "gradini": o.gradini, "pid": os.getpid(), "inizio": ora(),
                      "fase": "preparo", "gradino": None, "livello_dir": None,
                      "utenti_vivi": 0, "utenti_attesi": 0, "classe_ultimo": None,
                      "storia": self.storia, "prova": o.prova}
        self.meta = {}

    # -- lo stato per il coordinatore ----------------------------------------
    def aggiorna(self, **k):
        self.stato.update(k)
        self.stato["utenti_vivi"] = sum(1 for a in self.attori.values() if a.vivo())
        self.stato["aggiornato"] = ora()
        try:
            scrivi_json(os.path.join(self.base, "stato.json"), self.stato)
        except OSError as e:
            dice("⚠ stato.json non scritto: %s" % e)

    def nuova_cartella_attori(self):
        self.giro_attori += 1
        self.cartella_attori = os.path.join(self.base, "attori-%d" % self.giro_attori)
        os.makedirs(self.cartella_attori, exist_ok=True)

    # -- i pezzi --------------------------------------------------------------
    def ferma_attori(self):
        vivi = [a for a in self.attori.values() if a.vivo()]
        if vivi:
            dice("   fermo %d attori (SIGTERM: sgomberano da se')" % len(vivi))
        for a in vivi:
            a.segnale(signal.SIGTERM)
        fine = time.time() + self.o.attesa_uscita_s
        while time.time() < fine and any(a.vivo() for a in vivi):
            time.sleep(1)
        duri = [a for a in vivi if a.vivo()]
        if duri:
            dice("   ⚠ %d attori non sono usciti in %d s: SIGKILL al gruppo (%s)" % (
                len(duri), self.o.attesa_uscita_s, ", ".join("u%02d" % a.n for a in duri)))
        for a in self.attori.values():
            if a.vivo():
                a.uccidi()
        self.attori = {}

    def scatola_pulita(self, dove):
        """Attori via, inquilini via, scatola rifatta col tetto.  (ok, motivo)"""
        self.aggiorna(fase="rifaccio la scatola")
        self.ferma_attori()
        if self.o.non_rifare:
            dice("⚠ --non-rifare: la scatola NON si rifa' (solo prove dell'impianto)")
            sgombera_16(self.o.scatola)
            ok, perche = True, ""
        else:
            ok, perche = rifai_scatola(self.o, self.o.scatola, self.o.tetto, dove)
        if ok:
            self.meta_scatola = meta_scatola(self.o.scatola)
            dice("   scatola: binario %s · pagina %s · %s · dri %s" % (
                self.meta_scatola.get("binario"), self.meta_scatola.get("pagina"),
                self.meta_scatola.get("opzioni_server") or "(opzioni predefinite)",
                ",".join(self.meta_scatola.get("dri_nella_scatola", []))))
        self.nuova_cartella_attori()
        return ok, perche

    def entrano(self, n_fino, livello):
        """Gli attori mancanti fino a `n_fino`, uno dopo l'altro: il successivo
        quando il precedente ha il primo fotogramma (nascita.json)."""
        c, t = compositori("accendi", str(n_fino), self.o.misura)
        if c != 0:
            dice("⛔ compositori: %s" % " | ".join(t.splitlines()[-3:]))
            return False, "i compositori non si accendono: %s" % t.strip().splitlines()[-1:]
        nuovi = [n for n in range(1, n_fino + 1) if n not in self.attori]
        for n in nuovi:
            if self.fermati:
                return False, "fermata da fuori"
            a = Attore(self.o, n, livello, self.cartella_attori)
            try:
                s = a.avvia()
            except Exception as e:               # noqa: BLE001
                return False, "l'attore %d non parte: %s" % (n, e)
            self.attori[n] = a
            dice("   + utente %02d (pid %d, %s, seme %d, porte %d)" % (
                n, a.proc.pid, s, self.o.seme_base + n, self.o.porte_base + 10 * n))
            self.aggiorna(fase="entrano gli utenti", utenti_attesi=n_fino)
            fine = time.time() + self.o.attesa_nascita_s
            while time.time() < fine and a.vivo() and not a.e_nato() and not self.fermati:
                time.sleep(0.5)
            if a.e_nato():
                dice("     utente %02d nato in %.1f s" % (n, a.nato - a.partito))
            elif not a.vivo():
                dice("   ⛔ utente %02d MORTO prima di nascere (codice %s): si prosegue, "
                     "lo dira' la classifica" % (n, a.proc.returncode))
            else:
                dice("   ⚠ utente %02d non ha il primo fotogramma in %d s: entra il "
                     "prossimo lo stesso" % (n, self.o.attesa_nascita_s))
        return True, ""

    def controllo_corto(self, livello, dirliv):
        browser = ("firefox", "chrome")[self.livelli_fatti % 2]
        s = socket_di(0)
        if not s:
            dice("   ⚠ il compositore u00 del controllo non c'e'")
            return None
        cmd = [sys.executable, self.o.prog_controllo, "--scatola", self.o.scatola,
               "--livello", str(livello), "--dir", dirliv, "--browser", browser,
               "--porte-base", str(self.o.porte_base), "--largo", str(self.o.largo),
               "--alto", str(self.o.alto)]
        amb = ambiente_browser(s)
        dice("   controllo corto: %s su %s" % (browser, s))
        with open(os.path.join(dirliv, "controllo-corto.log"), "w") as log:
            try:
                p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=amb, cwd=QUI,
                                     start_new_session=True)
                try:
                    c = p.wait(timeout=self.o.tetto_controllo_s)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL)
                    p.wait()
                    c = None
                    dice("   ⛔ controllo corto oltre %d s: fermato" % self.o.tetto_controllo_s)
            except Exception as e:               # noqa: BLE001
                dice("   ⛔ controllo corto non lanciato: %s" % e)
                return None
        esito = None
        try:
            esito = json.load(open(os.path.join(dirliv, "controllo-corto.json"))).get("esito")
        except (OSError, ValueError):
            pass
        dice("   controllo corto: %s (codice %s)" % (esito, c))
        return esito

    def taglia_attori(self, dirliv, t0, t1):
        """Le serie degli attori dentro [t0, t1], nella cartella del livello."""
        for a in self.attori.values():
            src = a.dir_utente
            dst = os.path.join(dirliv, "utente-%02d" % a.n)
            os.makedirs(dst, exist_ok=True)
            if not os.path.isdir(src):
                continue
            for nome in os.listdir(src):
                p = os.path.join(src, nome)
                if not os.path.isfile(p):
                    continue
                q = os.path.join(dst, nome)
                if nome.endswith(".jsonl"):
                    taglia_jsonl(p, q, t0, t1)
                elif nome == "nascita.json" or os.path.getmtime(p) >= t0 - 1:
                    try:
                        os.link(p, q)
                    except OSError:
                        shutil.copy2(p, q)

    def registro_server(self, dirliv, segno, t0, t1):
        d = self.o.scatola
        files = []
        if segno is not None:
            # ⭐ «server.log»: il nome che legge 16-classifica.py
            _c, t = nella_scatola(d, "tail -n +%d /var/lib/rete11/registro.log" % (segno + 1), 300)
            open(os.path.join(dirliv, "server.log"), "w").write(t or "")
            files.append("server.log")
        da, a = "@%d" % int(t0), "@%d" % int(t1 + 1)
        # ⭐ gli errori del prodotto nel journal (--journal): lo schema di 16-classifica.py
        _c, t = nella_scatola(d, "journalctl -t remotix -p err -o json --since %s --until %s "
                                 "--no-pager 2>/dev/null | tail -n 200000" % (da, a), 300)
        open(os.path.join(dirliv, "journal-err.jsonl"), "w").write(
            "\n".join(r for r in (t or "").splitlines() if r.startswith("{")) + "\n")
        files.append("journal-err.jsonl")
        _c, t = nella_scatola(d, "journalctl -u rete11-server --since %s --until %s --no-pager "
                                 "-o short-iso-precise 2>&1 | tail -n 500000" % (da, a), 300)
        open(os.path.join(dirliv, "journal-server.log"), "w").write(t or "")
        files.append("journal-server.log")
        _c, t = nella_scatola(d, "journalctl --since %s --until %s --no-pager "
                                 "-o short-iso-precise 2>&1 | tail -n 500000" % (da, a), 300)
        open(os.path.join(dirliv, "journal-scatola.log"), "w").write(t or "")
        files.append("journal-scatola.log")
        return files

    def classifica(self, dirliv, livello):
        cmd = [sys.executable, self.o.prog_classifica, "--livello-dir", dirliv,
               "--campagna", self.o.campagna, "--livello", str(livello),
               "--finestra-s", str(int(self.o.controllo_min * 60)), "--json"]
        if self.o.fps_video:
            cmd += ["--fps-video", str(self.o.fps_video)]
        if self.o.prova:
            cmd.append("--secco")            # §13.3: la salita di prova non conta
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=900,
                               cwd=QUI)
            uscita, codice = r.stdout + r.stderr, r.returncode
        except Exception as e:                   # noqa: BLE001
            uscita, codice = "classifica non lanciata: %s" % e, None
        open(os.path.join(dirliv, "classifica.log"), "w").write(uscita)
        return leggi_classe(uscita, codice)

    # -- UN LIVELLO ------------------------------------------------------------
    def livello(self, n, minuti, nome, tipo):
        """Porta la salita a `n` utenti e fa il livello.  Torna (classe, signif, dirliv)."""
        o = self.o
        dirliv = os.path.join(self.base, nome)
        os.makedirs(dirliv, exist_ok=True)
        dice("══ %s: %d utenti, %s min (%s) ══" % (nome, n, minuti, tipo))
        self.aggiorna(fase="livello", gradino=n, livello_dir=dirliv, tipo_livello=tipo)
        t_inizio = time.time()
        _c, t = nella_scatola(o.scatola, "wc -l < /var/lib/rete11/registro.log 2>/dev/null", 60)
        try:
            segno = int((t or "").split()[-1])
        except (ValueError, IndexError):
            segno = None
        # ⛔ 16-risorse.py gira da ROOT (smaps_rollup e fdinfo degli inquilini):
        #   sudo -S, la parola sullo stdin; sudo passa il SIGTERM al figlio.
        cmd_r = [sys.executable, o.prog_risorse, "--scatola", o.scatola, "--dir", dirliv]
        if not o.risorse_senza_root:
            cmd_r = ["sudo", "-S", "-p", ""] + cmd_r
        risorse = subprocess.Popen(
            cmd_r, stdin=subprocess.PIPE, text=True,
            stdout=open(os.path.join(dirliv, "risorse.log"), "w"), stderr=subprocess.STDOUT,
            cwd=QUI, start_new_session=True)
        try:
            risorse.stdin.write("" if o.risorse_senza_root else _parola_sudo())
            risorse.stdin.close()
        except OSError:
            pass
        eventi = []
        ok, perche = self.entrano(n, n)
        if not ok:
            eventi.append({"t": ora(), "evento": "entrata fallita", "ragione": perche})
            dice("⛔ %s" % perche)
        t_lavoro = time.time()
        fine = t_lavoro + minuti * 60
        inizio_controllo = fine - o.controllo_min * 60
        dice("   tutti dentro (%.0f s dopo l'inizio del livello): lavoro fino alle %s" % (
            t_lavoro - t_inizio, time.strftime("%H:%M:%S", time.localtime(fine))))
        self.aggiorna(fase="lavoro", fine_prevista=datetime.datetime.fromtimestamp(
            fine).astimezone().isoformat(timespec="seconds"))
        esito_controllo = None
        fatto_controllo = False
        while not self.fermati:
            adesso = time.time()
            for a in self.attori.values():
                if not a.vivo() and not a.morto_annotato:
                    a.morto_annotato = True
                    eventi.append({"t": ora(), "evento": "attore morto", "utente": a.n,
                                   "codice": a.proc.returncode})
                    dice("   ⛔ utente %02d e' uscito (codice %s)" % (a.n, a.proc.returncode))
            if not fatto_controllo and adesso >= inizio_controllo:
                fatto_controllo = True
                self.aggiorna(fase="controllo")
                dice("   SIGUSR1 agli attori (foto piena)")
                for a in self.attori.values():
                    a.segnale(signal.SIGUSR1)
                if not o.senza_controllo:
                    esito_controllo = self.controllo_corto(n, dirliv)
                self.aggiorna(fase="lavoro")
                continue
            if adesso >= fine and fatto_controllo:
                break
            time.sleep(min(5, max(0.5, (inizio_controllo if not fatto_controllo else fine)
                                  - adesso)))
        t_fine = time.time()
        self.aggiorna(fase="registro")
        risorse.send_signal(signal.SIGTERM)
        try:
            risorse.wait(timeout=30)
        except subprocess.TimeoutExpired:
            sudo("pkill -KILL -f %s" % _q("[1]6-risorse.py --scatola %s --dir %s" % (
                o.scatola, dirliv)), 30)
        files = self.registro_server(dirliv, segno, t_inizio, t_fine)
        schede_b = browser_fuori_scheda(dirliv)
        if schede_b and schede_b["fuori_intel"]:
            dice("   ⛔ browser-cliente su una scheda che non e' la Intel: %s" % schede_b["fuori_intel"])
            eventi.append({"t": ora(), "evento": "browser fuori dalla Intel",
                           "dettaglio": schede_b["fuori_intel"]})
        self.taglia_attori(dirliv, t_inizio, t_fine)
        riga = dict(self.meta, **{
            "campagna": o.campagna, "livello": n, "nome": nome, "tipo": tipo,
            "desktop": o.scatola, "misura": o.misura, "largo": o.largo, "alto": o.alto,
            "tetto_sessioni": o.tetto, "minuti": minuti, "controllo_min": o.controllo_min,
            "inizio": iso(t_inizio), "inizio_t": round(t_inizio, 3),
            "inizio_lavoro": iso(t_lavoro), "fine": round(t_fine, 3), "fine_iso": iso(t_fine),
            "durata_s": round(t_fine - t_inizio), "durata_lavoro_s": round(t_fine - t_lavoro),
            "utenti": [{"utente": a.n, "profilo": "ABCD"[(a.n - 1) % 4],
                        "browser": "firefox" if a.n % 2 else "chrome",
                        "nuovo": bool(a.nato and a.nato >= t_inizio) or a.partito >= t_inizio}
                       for _k, a in sorted(self.attori.items())],
            "vivi_alla_fine": sorted(
                a.n for a in self.attori.values() if a.vivo()),
            "nati_nel_livello": sorted(a.n for a in self.attori.values()
                                       if a.nato and a.nato >= t_inizio),
            "nascite_s": {"%02d" % a.n: round(a.nato - a.partito, 1) for a in
                          self.attori.values() if a.nato and a.nato >= t_inizio},
            "seme_base": o.seme_base, "video": o.video, "fps_video": o.fps_video,
            "controllo_corto": esito_controllo, "registro_server": files,
            "schede_browser": schede_b,
            "eventi": eventi, "attori_da": self.cartella_attori, "prova": o.prova})
        ms = getattr(self, "meta_scatola", {})
        riga.update({"scatola_" + k: v for k, v in ms.items()})
        # ⭐ i campi di §10 coi nomi che legge 16-classifica.py (BASE)
        intel = [s for s in self.meta.get("schede", []) if s["driver"] in ("i915", "xe")]
        riga.update(scheda=(intel or [{}])[0].get("scheda", "?"),
                    driver=" ".join([(intel or [{}])[0].get("driver", "?")]
                                    + ms.get("driver_video", [])),
                    commit=self.meta.get("commit_prodotto") or
                    "banchi %s" % self.meta.get("commit_banchi"), binario=ms.get("binario"),
                    pagina=ms.get("pagina"), nucleo=self.meta.get("kernel"))
        scrivi_json(os.path.join(dirliv, "livello.json"), riga)
        if self.fermati:
            # ⛔ un livello interrotto da fuori non si classifica: non e' durato
            riga["interrotto"] = True
            scrivi_json(os.path.join(dirliv, "livello.json"), riga)
            classe, signif, perche_c = "INTERROTTO", False, "fermata da fuori (segnale)"
        else:
            self.aggiorna(fase="classifico")
            classe, signif, perche_c = self.classifica(dirliv, n)
        self.livelli_fatti += 1
        riga.update(classe=classe, significativo=signif, ragione_classe=perche_c)
        with open(os.path.join(self.base, "salita.jsonl"), "a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")
        self.storia.append({"livello": n, "nome": nome, "tipo": tipo, "classe": classe,
                            "significativo": signif, "dir": dirliv})
        self.aggiorna(classe_ultimo=classe)
        dice("   ▶ %s: %s%s — %s" % (nome, classe, " (significativo)" if signif else "",
                                     perche_c[:200]))
        return classe, signif, dirliv

    # -- LA SALITA INTERA ------------------------------------------------------
    def corri(self):
        o = self.o
        self.meta = meta_macchina(o)
        dice("⭐ SALITA %s · %s · %s (%dx%d) · gradini %s · %s min (ultimo %s) · tetto %d%s" % (
            o.campagna, o.scatola, o.misura, o.largo, o.alto, ",".join(map(str, o.gradini)),
            o.minuti, o.minuti_ultimo, o.tetto, " · PROVA (non conta)" if o.prova else ""))
        dice("   commit del prodotto: %s" % (self.meta["commit_prodotto"] or
                                            "? (16-prodotto assente o binario diverso)"))
        dice("   kernel %s · %s · binario %s · pagina %s · banchi %s" % (
            self.meta["kernel"], " + ".join("%s [%s]" % (s["scheda"], s["driver"])
                                            for s in self.meta["schede"]),
            self.meta["prodotto_binario"], self.meta["prodotto_pagina"],
            self.meta["commit_banchi"]))
        ok, perche = self.scatola_pulita(self.base)
        if not ok:
            return self.blocca(perche)
        ultimo_buono, rotto = 0, None
        for i, n in enumerate(o.gradini):
            if self.fermati:
                break
            minuti = o.minuti_ultimo if i == len(o.gradini) - 1 else o.minuti
            classe, signif, _d = self.livello(n, minuti, "livello-%02d" % n, "gradino")
            if self.fermati:
                break
            if cattivo(classe, signif):
                dice("⚠ %d utenti: %s — si RIPETE nelle stesse condizioni (§14), da scatola "
                     "pulita" % (n, classe))
                ok, perche = self.scatola_pulita(os.path.join(self.base, "livello-%02d" % n))
                if not ok:
                    return self.blocca(perche)
                classe2, signif2, _d = self.livello(n, minuti, "livello-%02d-ripetizione" % n,
                                                    "ripetizione")
                if self.fermati:
                    break
                if cattivo(classe2, signif2):
                    rotto = n
                    dice("⛔ confermato: %d utenti %s due volte" % (n, classe2))
                    break
                dice("   la ripetizione dice %s: non confermato, si sale" % classe2)
            ultimo_buono = n
        if rotto is not None and not self.fermati:
            ultimo_buono, rotto = self.ricerca(ultimo_buono, rotto)
        self.aggiorna(fase="fine", ultimo_buono=ultimo_buono, rottura=rotto)
        dice("⏹ FINE: ultimo livello buono %s · rottura %s%s" % (
            ultimo_buono, rotto, " · ⚠ FERMATA DA FUORI" if self.fermati else ""))
        if self.fermati:
            return 3
        return 0 if rotto is None else 1

    def ricerca(self, buono, rotto):
        """La ricerca a meta' (§6): ogni livello da scatola pulita coi suoi N utenti."""
        while rotto - buono > 1 and not self.fermati:
            n = (buono + rotto) // 2
            dice("🔎 ricerca a meta' fra %d (buono) e %d (rotto): %d utenti" % (buono, rotto, n))
            self.aggiorna(fase="ricerca", ricerca=[buono, rotto])
            ok, perche = self.scatola_pulita(os.path.join(self.base, "livello-%02d" % n))
            if not ok:
                self.blocca(perche)
                break
            classe, signif, _d = self.livello(n, self.o.minuti, "livello-%02d" % n, "ricerca")
            if self.fermati:
                break
            if cattivo(classe, signif):
                rotto = n
            else:
                buono = n
        return buono, rotto

    def blocca(self, perche):
        dice("⛔ BLOCKED: %s" % perche)
        self.aggiorna(fase="BLOCKED", ragione=perche)
        return 3

    def sgombera_tutto(self):
        o = self.o
        self.aggiorna(fase="sgombero")
        self.ferma_attori()
        try:
            sgombera_16(o.scatola)
        except Exception as e:                   # noqa: BLE001
            dice("⚠ sgombero: %s" % e)
        c, t = compositori("spegni")
        dice("   compositori spenti (%d)" % t.count("spento"))
        if not o.lascia_tetto and o.tetto and not o.non_rifare:
            c, t = sudo("cd %s && bash 11-accendi.sh server %s" % (RETE11, o.scatola), 300)
            dice("   server rimesso col tetto predefinito (codice %s, tetto %s)" % (
                c, tetto_in_vigore(o.scatola)))


def iso(t):
    return datetime.datetime.fromtimestamp(t).astimezone().isoformat(timespec="seconds")


def cattivo(classe, signif):
    """§6: FAIL o DEGRADED significativo fermano la salita.  Una classe che non
    si e' potuta leggere ferma anche lei: non si sale alla cieca."""
    return classe not in ("GREEN", "DEGRADED") or (classe == "DEGRADED" and signif)


def leggi_classe(uscita, codice):
    """(classe, significativo, ragione) dall'uscita di 16-classifica.py: l'ULTIMA
    riga JSON con «classe» (e «significativo»), o l'ultima parola GREEN /
    DEGRADED / FAIL; altrimenti «?» (e la salita si ferma)."""
    righe = []
    for riga in uscita.splitlines():
        riga = riga.strip()
        i = riga.find("{")
        if i < 0:
            continue
        try:
            d = json.loads(riga[i:])
        except ValueError:
            continue
        if isinstance(d, dict) and str(d.get("classe") or "").upper() in CLASSI:
            righe.append(d)
    # ⭐ la riga `"tipo": "livello"` (16-classifica.py --json), se no l'ultima
    for d in [r for r in righe if r.get("tipo") == "livello"][-1:] or righe[-1:]:
        return (str(d["classe"]).upper(), bool(d.get("significativo")),
                str(d.get("ragione") or "")[:400])
    parole = re.findall(r"\b(GREEN|DEGRADED|FAIL)\b", uscita)
    if parole:
        c = parole[-1]
        return c, bool(re.search(r"(?<!non )significativo", uscita, re.I)) and c == "DEGRADED", \
            "(letto dalla parola, codice %s)" % codice
    if codice in (0, 1, 3):                     # 16-classifica.py: GREEN 0, FAIL 1, DEGRADED 3
        return {0: "GREEN", 1: "FAIL", 3: "DEGRADED"}[codice], codice == 3, \
            "(dal codice d'uscita %s: DEGRADED contato come significativo)" % codice
    return "?", False, "16-classifica non ha detto una classe (codice %s): %s" % (
        codice, " | ".join(uscita.strip().splitlines()[-3:])[:300])


def taglia_jsonl(src, dst, t0, t1):
    """Le righe di `src` con l'istante dentro [t0, t1]; le righe senza istante
    leggibile passano tutte."""
    chiavi = ("t", "ts", "tempo", "epoch", "quando", "ora", "istante", "orario")
    with open(src, encoding="utf-8", errors="replace") as f, \
            open(dst, "w", encoding="utf-8") as g:
        for riga in f:
            try:
                d = json.loads(riga)
            except ValueError:
                continue
            t = None
            for k in chiavi:
                v = d.get(k) if isinstance(d, dict) else None
                if isinstance(v, (int, float)) and v > 1e9:
                    t = v / 1000.0 if v > 1e12 else float(v)
                    break
                if isinstance(v, str) and len(v) >= 19:
                    try:
                        t = datetime.datetime.fromisoformat(v).timestamp()
                        break
                    except ValueError:
                        pass
            if t is None or t0 - 1 <= t <= t1 + 1:
                g.write(riga)


# ═══════════════════════════════════════════════════════════════════════════
def main():
    global _log_file
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--scatola", required=True, choices=sorted(PORTE))
    a.add_argument("--campagna", required=True)
    a.add_argument("--misura", default="4k", choices=sorted(MISURE_SCHERMO))
    a.add_argument("--gradini", default="1,4,8,12,16")
    a.add_argument("--minuti", type=float, default=10)
    a.add_argument("--minuti-ultimo", type=float, default=30)
    a.add_argument("--controllo-min", type=float, default=2)
    a.add_argument("--seme-base", type=int, default=1600)
    a.add_argument("--fps-video", type=float, default=0)
    a.add_argument("--video", default="")
    a.add_argument("--tetto", type=int, default=0,
                   help="il tetto delle sessioni del server (predefinito: gradino piu' alto + 1, "
                        "per il controllo corto)")
    a.add_argument("--porte-base", type=int, default=9900)
    a.add_argument("--prova", action="store_true",
                   help="salita di prova §13.3: gradini 1,2,4 da 3 minuti; non conta")
    a.add_argument("--secco", action="store_true", help="stampa il piano e basta")
    a.add_argument("--attesa-nascita-s", type=int, default=180)
    a.add_argument("--attesa-uscita-s", type=int, default=120)
    a.add_argument("--tetto-controllo-s", type=int, default=600)
    a.add_argument("--lascia-tetto", action="store_true")
    # ⚠ solo per provare l'impianto, mai in una campagna:
    a.add_argument("--anche-se-non-vuoto", action="store_true")
    a.add_argument("--non-rifare", action="store_true")
    a.add_argument("--senza-controllo", action="store_true")
    a.add_argument("--risorse-senza-root", action="store_true",
                   help="16-risorse.py come nicfio (i finti): senza, PSS e fdinfo non si leggono")
    a.add_argument("--programmi", default=QUI,
                   help="la cartella di 16-attore/16-risorse/16-classifica (i finti: finti/)")
    o = a.parse_args()
    if o.prova:
        if "--gradini" not in sys.argv:
            o.gradini = "1,2,4"
        if "--minuti" not in sys.argv:
            o.minuti = 3
        if "--minuti-ultimo" not in sys.argv:
            o.minuti_ultimo = 3
        if not o.campagna.startswith("prova-"):
            o.campagna = "prova-" + o.campagna
    o.gradini = [int(x) for x in str(o.gradini).split(",") if x.strip()]
    if o.gradini != sorted(set(o.gradini)) or not o.gradini or o.gradini[0] < 1:
        a.error("--gradini: numeri crescenti da 1 in su")
    if o.controllo_min > min(o.minuti, o.minuti_ultimo):
        a.error("--controllo-min piu' lungo del livello")
    o.tetto = o.tetto or (max(o.gradini) + 1)
    o.largo, o.alto = MISURE_SCHERMO[o.misura]
    prog = os.path.abspath(o.programmi)
    o.prog_attore = os.path.join(prog, "16-attore.py")
    o.prog_risorse = os.path.join(prog, "16-risorse.py")
    o.prog_classifica = os.path.join(prog, "16-classifica.py")
    o.prog_controllo = os.path.join(QUI, "16-controllo-corto.py")
    if o.secco:
        tot = sum(o.minuti for _ in o.gradini[:-1]) + o.minuti_ultimo
        print("piano: %s · %s · gradini %s · %s min + ultimo %s ≈ %.0f min di lavoro (+ nascite, "
              "controlli, registro) · tetto %d · porte %d-%d · programmi %s" % (
                  o.campagna, o.scatola, o.gradini, o.minuti, o.minuti_ultimo, tot, o.tetto,
                  o.porte_base, o.porte_base + 10 * max(o.gradini) + 9, prog))
        for p in (o.prog_attore, o.prog_risorse, o.prog_classifica, o.prog_controllo):
            print("  %s %s" % ("✓" if os.path.exists(p) else "✗ MANCA", p))
        return 0
    for p in (o.prog_attore, o.prog_risorse, o.prog_classifica, o.prog_controllo):
        if not os.path.exists(p):
            print("⛔ manca %s" % p)
            return 3
    base = os.path.join(MISURE, o.campagna)
    if glob.glob(os.path.join(base, "livello-*")):
        print("⛔ la campagna %s ha gia' dei livelli in %s: le evidenze non si toccano (§14). "
              "Un altro nome." % (o.campagna, base))
        return 3
    os.makedirs(base, exist_ok=True)
    _log_file = open(os.path.join(base, "salita.log"), "a", encoding="utf-8")
    # ⛔ UNA salita alla volta sul server
    serratura = open(os.path.join(RUN, "16-salita.lock"), "w")
    try:
        fcntl.flock(serratura, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        dice("⛔ BLOCKED: c'e' gia' un'altra salita in corso su questo server")
        return 3
    sal = Salita(o)
    guai = perche_non_vuoto(o.scatola)
    if guai:
        sal.stato["server_non_vuoto"] = guai
        if not o.anche_se_non_vuoto:
            return sal.blocca("il server non e' vuoto: " + " · ".join(guai))
        dice("⚠ il server NON e' vuoto (--anche-se-non-vuoto, prova dell'impianto): " +
             " · ".join(guai))

    def fermati(sig, _f):
        dice("⚠ segnale %d: mi fermo e sgombero" % sig)
        sal.fermati = True
    signal.signal(signal.SIGTERM, fermati)
    signal.signal(signal.SIGINT, fermati)
    codice = 3
    try:
        codice = sal.corri()
    except Exception as e:                       # noqa: BLE001
        import traceback
        dice("⛔ la salita e' caduta: %r\n%s" % (e, traceback.format_exc()))
        sal.aggiorna(fase="caduta", ragione=repr(e))
    finally:
        sal.sgombera_tutto()
        if sal.stato.get("fase") not in ("BLOCKED", "caduta"):
            sal.aggiorna(fase="finita" if not sal.fermati else "fermata")
        dice("fine · %s" % json.dumps(sal.storia, ensure_ascii=False))
    return codice


if __name__ == "__main__":
    sys.exit(main())
