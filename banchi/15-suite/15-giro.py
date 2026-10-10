#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
15-giro — ONE ROUND OF THE FUNCTIONAL SUITE (phase 15)
===========================================================================

    (on the server, as nicfio — the real browsers are there)
    python3 15-giro.py --giro 1
    python3 15-giro.py --giro bonifica --desktop kde --browser chrome --prove f018
    python3 15-giro.py --giro 1 --strato-tecnico          # + C7 C9 C18 C19 C14
    python3 15-giro.py --elenco                           # what it would do

    (from the tablet)  bash banchi/15-suite/15-porta.sh && \
                  ssh nicfio@192.168.0.2 'python3 /media/REMOTIX/src/controllo/banchi/15-suite/15-giro.py --giro 1'

WHAT IT DOES
  - finds the tests `15-f*.py` / `15-n*.py` of this folder and reads their
    declarations (lines of text, not imports):
        FUNZIONI = ("F-004", …)        what it looks at (mandatory)
        PER_BROWSER = False            runs only once (with Firefox)
        LUNGA = True                   runs IN PARALLEL with the others of its desktop
        SERVER = "15-g7-server.sh"     a server of its own to start/stop
  - ⭐ the FOUR desktops in parallel, one queue per desktop; in the queue the two
    browsers one after the other; different debug ports per desktop;
  - every test with `--guasto` (healthy + fault in the same session), cap
    10 minutes (beyond: BLOCKED «over 10 minutes», and the process is killed);
  - ⭐ EVERY run leaves lines in the REGISTER (append only):
        /media/REMOTIX/misure/fase15/registro.jsonl
    with giro, test, funzione, desktop, browser, versione, sistema, binario,
    pagina, commit, inizio, durata, esito, ragione, atteso, osservato,
    guasto_visto, evidenze, difetto;
  - the evidence in /media/REMOTIX/misure/fase15/giro<N>/<desktop>/<browser>/<prova>/
    (the whole output of the test in `uscita.log`, the photos and the consoles inside).

⛔ BEFORE STARTING it checks whether in the boxes there is a session of a person
   (nictest or anyone who is not a bench tenant `c<n>u<n>`): if there is, it
   stops — the user's manual test is not interrupted (24 Sep 2026).
"""
import argparse
import datetime
import fcntl
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE_BANCHI = os.path.dirname(QUI)
MISURE = os.environ.get("REMOTIX_MISURE_15", "/media/REMOTIX/misure/fase15")
REGISTRO = os.path.join(MISURE, "registro.jsonl")
RETE11 = "/media/REMOTIX/rete11"
DESKTOP = ("gnome", "kde", "xfce", "lxqt")
BROWSER = ("firefox", "chrome")
TETTO_S = 600
# ⚠ the phone (phase 19 §5) declares its own: `banchi/19-android/19-android.py`
SISTEMA = os.environ.get("REMOTIX_SISTEMA_15") or \
    "Debian 13 · headless labwc 3840x2160 · i5-13500T, Intel UHD 770"
INQUILINO = re.compile(r"^c[0-9]+b?u[0-9]+$")
_serratura = threading.Lock()


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


# ═══════════════════════════════════════════════════════════════════════════
#  THE TESTS AND THEIR DECLARATIONS
# ═══════════════════════════════════════════════════════════════════════════
def leggi_prove(filtro=""):
    prove = []
    for f in sorted(glob.glob(os.path.join(QUI, "15-[fn][0-9]*.py"))):
        testo = open(f, encoding="utf-8").read()
        m = re.search(r"^FUNZIONI\s*=\s*\(([^)]*)\)", testo, re.M)
        if not m:
            continue
        funzioni = re.findall(r"[\"']([A-Z]-[0-9A-Z-]+)[\"']", m.group(1))
        nome = os.path.basename(f)[:-3]
        corto = nome.split("-")[1]                       # f004
        if filtro and not any(x.strip() and x.strip() in nome for x in filtro.split(",")):
            continue
        per_browser = not re.search(r"^PER_BROWSER\s*=\s*False", testo, re.M)
        lunga = bool(re.search(r"^LUNGA\s*=\s*True", testo, re.M))
        # ⭐ SOLO_TELEFONO = True: the test makes sense only with the real phone (F-031, touch)
        solo_tel = bool(re.search(r"^SOLO_TELEFONO\s*=\s*True", testo, re.M))
        s = re.search(r"^SERVER\s*=\s*[\"']([^\"']+)[\"']", testo, re.M)
        prove.append({"file": f, "nome": nome, "corto": corto, "funzioni": funzioni,
                      "per_browser": per_browser, "lunga": lunga, "solo_telefono": solo_tel,
                      "server": s.group(1) if s else ""})
    return prove


# ═══════════════════════════════════════════════════════════════════════════
#  THE MACHINE: boxes, binary, page, commit
# ═══════════════════════════════════════════════════════════════════════════
def sudo(comando, secondi=120):
    r = subprocess.run(["sudo", "-S", "-p", "", "sh", "-c", comando], input=_parola_sudo(),
                       capture_output=True, text=True, errors="replace", timeout=secondi)
    return r.returncode, (r.stdout + r.stderr).strip()


def nella_scatola(d, comando, secondi=60):
    return sudo("podman exec rete11-%s sh -c %s" % (d, _q(comando)), secondi)


def _q(s):
    return "'" + s.replace("'", "'\"'\"'") + "'"


def impronte(d):
    _c, t = nella_scatola(d, "md5sum /opt/remotix/remotix /opt/remotix/pagina.html")
    v = {}
    for riga in t.splitlines():
        p = riga.split()
        if len(p) == 2:
            v["binario" if p[1].endswith("remotix") else "pagina"] = p[0][:8]
    return v


def persone_dentro(d):
    """The users with a session who are NOT bench tenants."""
    _c, t = nella_scatola(d, "loginctl list-users --no-legend 2>/dev/null | awk '{print $2}'")
    return [u for u in t.split() if u and not INQUILINO.match(u) and u not in ("root", "provanic")]


def commit():
    p = os.path.join(RADICE_BANCHI, "..", "VERSIONE")
    try:
        return open(p).read().strip()
    except OSError:
        return "?"


# ⛔ THE BOXES BELONG TO ONE BENCH AT A TIME (29 Sep 2026, «user unknown» of phase 16):
#   the hook (even the pre-push one, on its own) clears out ALL the tenants
#   `c<n>u<n>` before every mesh ⇒ a push during a round deleted the tenants
#   born 7 s earlier (`[M]` 04:28, 04:40, 04:42 of 29 Sep = the 4 FAIL and 36 BLOCKED).
#   The same lock in 15-giro.py, 16-salita.py and 11-gancio.sh; whoever is launched by
#   one of them inherits REMOTIX_SCATOLE_TENUTE and does not take it again.
#   ⚠ NOT in /run/lock: the folder is «sticky» and with fs.protected_regular root does not
#   reopen the file created by nicfio (and the hook says «held» for free boxes, `[M]`).
SERRATURA_SCATOLE = "/media/REMOTIX/rete11/.scatole.lock"


def tieni_le_scatole(chi):
    """None if the boxes are ours (the lock stays taken until exit),
    otherwise the sentence saying who holds them."""
    if os.environ.get("REMOTIX_SCATOLE_TENUTE"):
        return None
    fd = os.open(SERRATURA_SCATOLE, os.O_RDWR | os.O_CREAT, 0o666)
    try:
        os.fchmod(fd, 0o666)
    except OSError:
        pass
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        try:
            tiene = os.pread(fd, 200, 0).decode(errors="replace").strip()
        except OSError:
            tiene = ""
        os.close(fd)
        return "the boxes are already held by another bench (%s)" % (tiene or "?")
    os.ftruncate(fd, 0)
    os.pwrite(fd, ("%s pid %d" % (chi, os.getpid())).encode(), 0)
    os.environ["REMOTIX_SCATOLE_TENUTE"] = chi
    globals()["_fd_scatole"] = fd
    return None


# ═══════════════════════════════════════════════════════════════════════════
#  THE REGISTER
# ═══════════════════════════════════════════════════════════════════════════
def scrivi(righe):
    os.makedirs(MISURE, exist_ok=True)
    with _serratura, open(REGISTRO, "a", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        for r in righe:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        fcntl.flock(f, fcntl.LOCK_UN)


# ═══════════════════════════════════════════════════════════════════════════
#  ONE TEST
# ═══════════════════════════════════════════════════════════════════════════
def compositore(d, u, lunga):
    """⭐ The headless labwc OF the desktop (15-compositori.sh): four desktops
    in parallel in the same compositor cover Chrome's windows, and a covered
    Chrome cannot be photographed.  The LONG tests (a browser idle for minutes)
    go into the «comune» labwc (started by 15-compositori.sh with its own name, not
    «wayland-0»: after a reboot that number may belong to a desktop)."""
    comune = os.environ.get("REMOTIX_WAYLAND_VERI", "wayland-0")
    try:
        s = open("/run/user/%d/15-compositori/%s" % (u, "comune" if lunga else d)).read().strip()
        if s and os.path.exists("/run/user/%d/%s" % (u, s)):
            return s
    except OSError:
        pass
    return comune


def una_prova(o, p, d, b, base, meta):
    ev = os.path.join(MISURE, "giro%s" % o.giro, d, b, p["corto"])
    os.makedirs(ev, exist_ok=True)
    u = os.getuid()
    amb = dict(os.environ, XDG_RUNTIME_DIR="/run/user/%d" % u,
               WAYLAND_DISPLAY=compositore(d, u, p["lunga"]),
               REMOTIX_SCHERMO_ANNIDATO="1", REMOTIX_SUL_SERVER="1",
               REMOTIX_CHROME_OPZIONI="--ozone-platform=wayland --disable-backgrounding-occluded-windows --disable-renderer-backgrounding --disable-background-timer-throttling", MOZ_ENABLE_WAYLAND="1")
    cmd = [sys.executable, p["file"], "--scatola", d, "--browser", b,
           "--porte-base", str(base), "--evidenze", ev]
    if not o.senza_guasto:
        cmd.append("--guasto")
    inizio = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    t0 = time.time()
    righe, fuori = [], ""
    with open(os.path.join(ev, "uscita.log"), "w") as log:
        try:
            pr = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, errors="replace", env=amb, cwd=QUI,
                                  start_new_session=True)
            scaduto = []

            def ferma():
                scaduto.append(1)
                try:
                    os.killpg(pr.pid, 9)
                except OSError:
                    pass
            cane = threading.Timer(TETTO_S, ferma)
            cane.start()
            try:
                for riga in pr.stdout:
                    log.write(riga)
                    log.flush()
                    if riga.startswith("SUITE "):
                        try:
                            righe.append(json.loads(riga[6:]))
                        except ValueError:
                            pass
                pr.wait()
            finally:
                cane.cancel()
            if scaduto:
                fuori = "over %d minutes: the test was stopped" % (TETTO_S // 60)
        except Exception as e:                   # noqa: BLE001
            fuori = "the round could not launch the test: %r" % e
    durata = round(time.time() - t0)
    passate = ("sana",) if o.senza_guasto else ("sana", "guasto")
    viste = {(r.get("funzione"), r.get("passata")) for r in righe}
    for f in p["funzioni"]:
        for ps in passate:
            if (f, ps) not in viste:
                righe.append({"funzione": f, "passata": ps, "esito": "BLOCKED",
                              "ragione": fuori or "the test gave no judgment for %s "
                              "(see uscita.log)" % f, "guasto_visto": None, "evidenze": []})
    uscita = []
    for r in righe:
        f = r.get("funzione", "?")
        uscita.append({
            "giro": o.giro,
            "test": "T-%s-%s-%s%s" % (f[2:] if f.startswith("F-") else f, d, b,
                                       "-guasto" if r.get("passata") == "guasto" else ""),
            "funzione": f, "passata": r.get("passata", "sana"), "prova": p["nome"],
            "desktop": d, "browser": b, "versione": r.get("versione", ""),
            "sistema": SISTEMA, "binario": meta.get(d, {}).get("binario", "?"),
            "pagina": meta.get(d, {}).get("pagina", "?"), "commit": meta.get("commit", "?"),
            "inizio": inizio, "durata_s": durata, "esito": r.get("esito"),
            "ragione": r.get("ragione", ""), "atteso": r.get("atteso", ""),
            "osservato": r.get("osservato", ""), "guasto_visto": r.get("guasto_visto"),
            "evidenze": [os.path.join(ev, "uscita.log")] + [x for x in r.get("evidenze") or [] if x],
            "difetto": None})
    scrivi(uscita)
    conto = {}
    for r in uscita:
        conto[r["esito"]] = conto.get(r["esito"], 0) + 1
    print("[%s %s] %-40s %4d s  %s" % (d, b, p["nome"], durata,
                                        " ".join("%s=%d" % kv for kv in sorted(conto.items()))),
          flush=True)
    return uscita


def fila(o, d, prove, meta, esiti):
    base = 3100 + 10 * DESKTOP.index(d)
    lunghe = [p for p in prove if p["lunga"]]
    corte = [p for p in prove if not p["lunga"]]
    fili = []
    for i, p in enumerate(lunghe):
        b = o.browser[0]
        t = threading.Thread(target=lambda p=p, b=b, i=i: esiti.extend(
            una_prova(o, p, d, b, 3500 + 10 * DESKTOP.index(d) + 2 * i, meta)))
        t.start()
        fili.append(t)
    for b in o.browser:
        for p in corte:
            if not p["per_browser"] and b != o.browser[0]:
                continue
            if p["solo_telefono"] and b != "telefono":
                continue
            esiti.extend(una_prova(o, p, d, b, base, meta))
    for t in fili:
        t.join()


def server_delle_prove(prove, desktop, azione):
    for s in sorted({p["server"] for p in prove if p["server"]}):
        for d in desktop:
            c, t = subprocess.run(["bash", os.path.join(QUI, s), azione, d],
                                  capture_output=True, text=True).returncode, ""
            print("   server %s %s %s: code %s" % (s, azione, d, c), flush=True)


# ═══════════════════════════════════════════════════════════════════════════
#  THE SHORT TECHNICAL LAYER: C7 C9 C18 C19 (per desktop) and C14 (all together)
# ═══════════════════════════════════════════════════════════════════════════
MAGLIE = [("C7", "c7", [], False), ("C7", "c7", ["--lascia-un-processo", "--attesa-chiusura", "10"], True),
          ("C9", "c9", [], False), ("C9", "c9", ["--togli-nome", "tutto"], True),
          ("C18", "c18", [], False), ("C18", "c18", ["--senza-usermod"], True),
          ("C19", "c19", [], False), ("C19", "c19", ["--lascia-un-inquilino"], True)]


SGOMBERO = r"""
for u in $(awk -F: '$1 ~ /^c[0-9]+b?u[0-9]+$/ {print $1}' /etc/passwd); do
  id=$(id -u "$u" 2>/dev/null)
  m="runuser -u [$(printf %s "$u" | cut -c1)]$(printf %s "$u" | cut -c2-) "
  loginctl terminate-user "$u" >/dev/null 2>&1
  pkill -CONT -f "$m" >/dev/null 2>&1; pkill -CONT -u "$u" >/dev/null 2>&1
  pkill -KILL -f "$m" >/dev/null 2>&1; pkill -KILL -u "$u" >/dev/null 2>&1
  sleep 0.2
  userdel -r "$u" >/dev/null 2>&1 || userdel "$u" >/dev/null 2>&1
  [ -n "$id" ] && systemctl reset-failed "user@$id.service" >/dev/null 2>&1
  [ -n "$id" ] && find /tmp -maxdepth 1 -uid "$id" -exec rm -rf {} + 2>/dev/null
done; true
"""


def sgombera(d):
    """The net's tenants (`c<n>[b]u<n>`) out of the box: the same line
    as 11-gancio.sh, in the same namespace (nictest and provanic stay)."""
    nella_scatola(d, SGOMBERO, 120)


def strato_tecnico(o, desktop, meta):
    righe = []

    def una(d, nome, sotto, arg, guasto):
        # ⛔ the net's CLEAR-OUT (11-gancio.sh sgombera_inquilini), before
        #   every mesh: the meshes delete their tenant BEFORE creating it,
        #   not after ⇒ without it, C19 sees C9's tenants and says red.
        #   `[M]` round 1, 25 Sep 2026 (D-013, class C).
        sgombera(d)
        t0 = time.time()
        c, t = sudo("bash %s/11-accendi.sh %s %s %s" % (RETE11, sotto, d, " ".join(arg)), 900)
        # ⛔ the fault reads the other way round (11-gancio.sh esegui_maglia): 0 = seen
        if guasto:
            esito = {0: "PASS", 1: "FAIL"}.get(c, "BLOCKED")
        else:
            esito = {0: "PASS", 1: "FAIL"}.get(c, "BLOCKED")
        ev = os.path.join(MISURE, "giro%s" % o.giro, d, "tecnico", nome + ("-guasto" if guasto else ""))
        os.makedirs(ev, exist_ok=True)
        with open(os.path.join(ev, "uscita.log"), "w") as f:
            f.write(t)
        coda = [x for x in t.splitlines() if x.strip()][-1:] or [""]
        righe.append({"giro": o.giro, "test": "T-%s-%s%s" % (nome, d, "-guasto" if guasto else ""),
                      "funzione": nome, "passata": "guasto" if guasto else "sana",
                      "prova": "11-accendi.sh %s" % sotto, "desktop": d, "browser": "-",
                      "versione": "", "sistema": SISTEMA,
                      "binario": meta.get(d, {}).get("binario", "?"),
                      "pagina": meta.get(d, {}).get("pagina", "?"), "commit": meta.get("commit"),
                      "inizio": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                      "durata_s": round(time.time() - t0), "esito": esito,
                      "ragione": "code %s · %s" % (c, coda[0][:200]),
                      "atteso": "", "osservato": "", "guasto_visto": (c == 0) if guasto else None,
                      "evidenze": [os.path.join(ev, "uscita.log")], "difetto": None})
        print("[%s technical] %s%s → %s" % (d, nome, " (fault)" if guasto else "", esito), flush=True)

    fili = []
    for d in desktop:
        def fila_t(d=d):
            for nome, sotto, arg, guasto in MAGLIE:
                una(d, nome, sotto, arg, guasto)
        t = threading.Thread(target=fila_t)
        t.start()
        fili.append(t)
    for t in fili:
        t.join()
    if set(desktop) == set(DESKTOP):
        c14 = glob.glob(os.path.join(RETE11, "11-c14-*.py"))
        if c14:
            t0 = time.time()
            c, t = sudo("cd %s && python3 %s" % (RETE11, c14[0]), 1800)
            righe.append({"giro": o.giro, "test": "T-C14-tutte", "funzione": "C14",
                          "passata": "sana", "prova": os.path.basename(c14[0]),
                          "desktop": "tutte", "browser": "-", "sistema": SISTEMA,
                          "commit": meta.get("commit"), "durata_s": round(time.time() - t0),
                          "inizio": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                          "esito": {0: "PASS", 1: "FAIL"}.get(c, "BLOCKED"),
                          "ragione": "code %s" % c, "guasto_visto": None,
                          "evidenze": [], "difetto": None})
    scrivi(righe)
    return righe


# ═══════════════════════════════════════════════════════════════════════════
def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--giro", default="prova")
    a.add_argument("--desktop", default=",".join(DESKTOP))
    a.add_argument("--browser", default=",".join(BROWSER))
    a.add_argument("--prove", default="", help="filter: parts of the name, separated by commas")
    a.add_argument("--senza-guasto", action="store_true")
    a.add_argument("--strato-tecnico", action="store_true")
    a.add_argument("--solo-strato-tecnico", action="store_true")
    a.add_argument("--elenco", action="store_true")
    a.add_argument("--anche-se-qualcuno-e-dentro", action="store_true")
    o = a.parse_args()
    o.desktop = [x for x in o.desktop.split(",") if x]
    o.browser = [x for x in o.browser.split(",") if x]
    prove = leggi_prove(o.prove)
    if o.elenco:
        for p in prove:
            print("%-44s %-28s %s%s%s" % (p["nome"], ",".join(p["funzioni"]),
                                          "per browser" if p["per_browser"] else "once",
                                          " · LONG" if p["lunga"] else "",
                                          " · server " + p["server"] if p["server"] else ""))
        return 0
    guaio = tieni_le_scatole("15-giro %s" % o.giro)
    if guaio:
        print("⛔ %s: the round does not start (a hook or a climb would clear out its "
              "tenants, or it theirs)" % guaio)
        return 3
    meta = {"commit": commit()}
    for d in o.desktop:
        meta[d] = impronte(d)
        chi = persone_dentro(d)
        if chi and not o.anche_se_qualcuno_e_dentro:
            print("⛔ in rete11-%s there is a session of %s: the manual test is not interrupted. "
                  "I stop the round." % (d, ", ".join(chi)))
            return 3
    print("⭐ ROUND %s · %s · %s · %d tests · commit %s · %s" % (
        o.giro, ",".join(o.desktop), ",".join(o.browser), len(prove), meta["commit"],
        " ".join("%s=%s/%s" % (d, meta[d].get("binario"), meta[d].get("pagina"))
                 for d in o.desktop)), flush=True)
    t0 = time.time()
    esiti = []
    if not o.solo_strato_tecnico:
        server_delle_prove(prove, o.desktop, "accendi")
        try:
            fili = [threading.Thread(target=fila, args=(o, d, prove, meta, esiti))
                    for d in o.desktop]
            for t in fili:
                t.start()
            for t in fili:
                t.join()
        finally:
            server_delle_prove(prove, o.desktop, "spegni")
    if o.strato_tecnico or o.solo_strato_tecnico:
        esiti.extend(strato_tecnico(o, o.desktop, meta))
    conto = {}
    for r in esiti:
        conto[r["esito"]] = conto.get(r["esito"], 0) + 1
    print("\n⏱ round %s: %.0f min · %s" % (o.giro, (time.time() - t0) / 60,
                                         " ".join("%s=%d" % kv for kv in sorted(conto.items()))))
    return 1 if conto.get("FAIL") else (3 if conto.get("BLOCKED") else 0)


if __name__ == "__main__":
    sys.exit(main())
