#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
15-giro — UN GIRO DELLA SUITE FUNZIONALE (fase 15)
===========================================================================

    (sul server, come nicfio — i browser veri stanno la')
    python3 15-giro.py --giro 1
    python3 15-giro.py --giro bonifica --desktop kde --browser chrome --prove f018
    python3 15-giro.py --giro 1 --strato-tecnico          # + C7 C9 C18 C19 C14
    python3 15-giro.py --elenco                           # che cosa farebbe

    (dal tablet)  bash banchi/15-suite/15-porta.sh && \
                  ssh nicfio@192.168.0.2 'python3 /media/REMOTIX/src/controllo/banchi/15-suite/15-giro.py --giro 1'

CHE COSA FA
  - trova le prove `15-f*.py` / `15-n*.py` di questa cartella e ne legge le
    dichiarazioni (righe di testo, non import):
        FUNZIONI = ("F-004", …)        che cosa guarda (obbligatoria)
        PER_BROWSER = False            gira una volta sola (con Firefox)
        LUNGA = True                   gira IN PARALLELO alle altre del suo desktop
        SERVER = "15-g7-server.sh"     un server suo da accendere/spegnere
  - ⭐ i QUATTRO desktop in parallelo, una fila per desktop; nella fila i due
    browser uno dopo l'altro; porte di debug diverse per desktop;
  - ogni prova con `--guasto` (sana + guasto nella stessa sessione), tetto
    10 minuti (oltre: BLOCKED «oltre i 10 minuti», e il processo si uccide);
  - ⭐ OGNI esecuzione lascia righe nel REGISTRO (solo aggiunte):
        /media/REMOTIX/misure/fase15/registro.jsonl
    con giro, test, funzione, desktop, browser, versione, sistema, binario,
    pagina, commit, inizio, durata, esito, ragione, atteso, osservato,
    guasto_visto, evidenze, difetto;
  - le evidenze in /media/REMOTIX/misure/fase15/giro<N>/<desktop>/<browser>/<prova>/
    (l'uscita intera della prova in `uscita.log`, le foto e le console dentro).

⛔ PRIMA DI PARTIRE guarda se nelle scatole c'e' una sessione di una persona
   (nictest o chiunque non sia un inquilino dei banchi `c<n>u<n>`): se c'e', si
   ferma — la prova a mano dell'utente non si interrompe (24 set 2026).
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
PAROLA_SUDO = "nicfio\n"
SISTEMA = "Debian 13 · labwc senza schermo 3840x2160 · i5-13500T, Intel UHD 770"
INQUILINO = re.compile(r"^c[0-9]+b?u[0-9]+$")
_serratura = threading.Lock()


# ═══════════════════════════════════════════════════════════════════════════
#  LE PROVE E LE LORO DICHIARAZIONI
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
        s = re.search(r"^SERVER\s*=\s*[\"']([^\"']+)[\"']", testo, re.M)
        prove.append({"file": f, "nome": nome, "corto": corto, "funzioni": funzioni,
                      "per_browser": per_browser, "lunga": lunga,
                      "server": s.group(1) if s else ""})
    return prove


# ═══════════════════════════════════════════════════════════════════════════
#  LA MACCHINA: scatole, binario, pagina, commit
# ═══════════════════════════════════════════════════════════════════════════
def sudo(comando, secondi=120):
    r = subprocess.run(["sudo", "-S", "-p", "", "sh", "-c", comando], input=PAROLA_SUDO,
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
    """Gli utenti con una sessione che NON sono inquilini dei banchi."""
    _c, t = nella_scatola(d, "loginctl list-users --no-legend 2>/dev/null | awk '{print $2}'")
    return [u for u in t.split() if u and not INQUILINO.match(u) and u not in ("root", "provanic")]


def commit():
    p = os.path.join(RADICE_BANCHI, "..", "VERSIONE")
    try:
        return open(p).read().strip()
    except OSError:
        return "?"


# ═══════════════════════════════════════════════════════════════════════════
#  IL REGISTRO
# ═══════════════════════════════════════════════════════════════════════════
def scrivi(righe):
    os.makedirs(MISURE, exist_ok=True)
    with _serratura, open(REGISTRO, "a", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        for r in righe:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        fcntl.flock(f, fcntl.LOCK_UN)


# ═══════════════════════════════════════════════════════════════════════════
#  UNA PROVA
# ═══════════════════════════════════════════════════════════════════════════
def compositore(d, u, lunga):
    """⭐ Il labwc senza schermo DEL desktop (15-compositori.sh): quattro desktop
    in parallelo nello stesso compositore coprono le finestre di Chrome, e Chrome
    coperto non si fotografa.  Le prove LUNGHE (un browser fermo per minuti)
    vanno nel labwc comune, per non stare sopra al browser della fila."""
    comune = os.environ.get("REMOTIX_WAYLAND_VERI", "wayland-0")
    if lunga:
        return comune
    try:
        s = open("/run/user/%d/15-compositori/%s" % (u, d)).read().strip()
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
                fuori = "oltre i %d minuti: la prova e' stata fermata" % (TETTO_S // 60)
        except Exception as e:                   # noqa: BLE001
            fuori = "il giro non ha potuto lanciare la prova: %r" % e
    durata = round(time.time() - t0)
    passate = ("sana",) if o.senza_guasto else ("sana", "guasto")
    viste = {(r.get("funzione"), r.get("passata")) for r in righe}
    for f in p["funzioni"]:
        for ps in passate:
            if (f, ps) not in viste:
                righe.append({"funzione": f, "passata": ps, "esito": "BLOCKED",
                              "ragione": fuori or "la prova non ha dato un giudizio per %s "
                              "(vedi uscita.log)" % f, "guasto_visto": None, "evidenze": []})
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
            esiti.extend(una_prova(o, p, d, b, base, meta))
    for t in fili:
        t.join()


def server_delle_prove(prove, desktop, azione):
    for s in sorted({p["server"] for p in prove if p["server"]}):
        for d in desktop:
            c, t = subprocess.run(["bash", os.path.join(QUI, s), azione, d],
                                  capture_output=True, text=True).returncode, ""
            print("   server %s %s %s: codice %s" % (s, azione, d, c), flush=True)


# ═══════════════════════════════════════════════════════════════════════════
#  LO STRATO TECNICO CORTO: C7 C9 C18 C19 (per desktop) e C14 (tutte insieme)
# ═══════════════════════════════════════════════════════════════════════════
MAGLIE = [("C7", "c7", [], False), ("C7", "c7", ["--lascia-un-processo", "--attesa-chiusura", "10"], True),
          ("C9", "c9", [], False), ("C9", "c9", ["--togli-nome", "tutto"], True),
          ("C18", "c18", [], False), ("C18", "c18", ["--senza-usermod"], True),
          ("C19", "c19", [], False), ("C19", "c19", ["--lascia-un-inquilino"], True)]


def strato_tecnico(o, desktop, meta):
    righe = []

    def una(d, nome, sotto, arg, guasto):
        t0 = time.time()
        c, t = sudo("bash %s/11-accendi.sh %s %s %s" % (RETE11, sotto, d, " ".join(arg)), 900)
        # ⛔ il guasto si legge al contrario (11-gancio.sh esegui_maglia): 0 = visto
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
                      "ragione": "codice %s · %s" % (c, coda[0][:200]),
                      "atteso": "", "osservato": "", "guasto_visto": (c == 0) if guasto else None,
                      "evidenze": [os.path.join(ev, "uscita.log")], "difetto": None})
        print("[%s tecnico] %s%s → %s" % (d, nome, " (guasto)" if guasto else "", esito), flush=True)

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
                          "ragione": "codice %s" % c, "guasto_visto": None,
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
    a.add_argument("--prove", default="", help="filtro: parti del nome, separate da virgole")
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
                                          "per browser" if p["per_browser"] else "una volta",
                                          " · LUNGA" if p["lunga"] else "",
                                          " · server " + p["server"] if p["server"] else ""))
        return 0
    meta = {"commit": commit()}
    for d in o.desktop:
        meta[d] = impronte(d)
        chi = persone_dentro(d)
        if chi and not o.anche_se_qualcuno_e_dentro:
            print("⛔ in rete11-%s c'e' una sessione di %s: la prova a mano non si interrompe. "
                  "Fermo il giro." % (d, ", ".join(chi)))
            return 3
    print("⭐ GIRO %s · %s · %s · %d prove · commit %s · %s" % (
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
    print("\n⏱ giro %s: %.0f min · %s" % (o.giro, (time.time() - t0) / 60,
                                         " ".join("%s=%d" % kv for kv in sorted(conto.items()))))
    return 1 if conto.get("FAIL") else (3 if conto.get("BLOCKED") else 0)


if __name__ == "__main__":
    sys.exit(main())
