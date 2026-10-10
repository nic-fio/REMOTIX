#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
19-nv-suite — THE SUBSET OF THE PHASE 15 SUITE ON THE NVIDIA MACHINE

    (from `19-nv-macchina.sh suite`, as the bench user `rxbanco`)
    python3 19-nv-suite.py --registro R.jsonl --evidenze DIR --porta 7447 --modo finestra|headless

The tests are the suite's, IDENTICAL (banchi/15-suite/15-f*.py, not copied):
    F-001 F-002 (15-f001) · F-003 (15-f003) · F-011 (15-f011) · F-013 (15-f013)
    F-016 (15-f016) · F-018 (15-f018)
with the two browsers (Firefox with Marionette, Chrome with CDP), healthy + fault, cap 10 minutes
each, like `15-giro.py`.  ⭐ The only difference is where things are:

  - NO BOX: on the home server the product runs in `rete11-xfce` and the suite enters
    with `sudo podman exec`; here the product is INSTALLED on the machine (with its
    installer) and "inside the box" means `sudo -n sh -c` on the machine itself.
    ⇒ `Scatola.dentro` is replaced (the same graft that `suite.py` already does for
    REMOTIX_SUL_SERVER), and the server log is the file where the unit writes stderr;
  - one desktop only, XFCE (under labwc: the product starts it, on the card);
  - the browsers in THE BROWSERS' headless labwc (pixman, 3840x2160) like
    `15-compositori.sh`; if that one is not born, HEADLESS — and the line says so.

The log has the lines of `15-giro.py` (run "19-nvidia"): `15-rapporto.py` makes the
report as for the other runs.  Exit: 0 all PASS · 1 at least one FAIL · 3 BLOCKED.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import runpy
import subprocess
import sys
import threading
import time

QUI = os.path.dirname(os.path.abspath(__file__))
ALBERO = os.path.dirname(os.path.dirname(QUI))
SUITE = os.path.join(ALBERO, "banchi", "15-suite")
PROVE = ("15-f001-accesso-e-prima-immagine.py", "15-f003-lo-schermo-si-aggiorna.py",
         "15-f011-la-tela-all-attacco.py", "15-f013-video.py",
         "15-f016-stacco-e-riattacco.py", "15-f018-riattacco-a-misura-diversa.py")
DESKTOP = "xfce"
BROWSER = ("firefox", "chrome")
TETTO_S = 600
GIRO = "19-nvidia"
CHROME_OPZIONI = ("--ozone-platform=wayland --disable-backgrounding-occluded-windows "
                  "--disable-renderer-backgrounding --disable-background-timer-throttling")


# ═══════════════════════════════════════════════════════════════════════════
#  INSIDE A TEST (child process): the graft, then the real test
# ═══════════════════════════════════════════════════════════════════════════
def interno(file, resto):
    sys.path.insert(0, SUITE)
    import suite as S                                              # noqa: E402

    def dentro(self, riga, secondi=90):
        """(code, output) of `riga` as root ON THE MACHINE (the "box" is the machine)."""
        try:
            r = subprocess.run(["sudo", "-n", "sh", "-c", riga], capture_output=True,
                               text=True, errors="replace", timeout=secondi)
        except subprocess.TimeoutExpired:
            return None, "(no answer within %d s)" % secondi
        return r.returncode, (r.stdout + r.stderr).strip()

    S.C20V.Scatola.dentro = dentro
    S.C20V.REGISTRO = os.environ["RXNV_REGISTRO"]
    sys.argv = [file] + resto
    runpy.run_path(file, run_name="__main__")


# ═══════════════════════════════════════════════════════════════════════════
#  THE RUN
# ═══════════════════════════════════════════════════════════════════════════
def leggi(file):
    testo = open(file, encoding="utf-8").read()
    m = re.search(r"^FUNZIONI\s*=\s*\(([^)]*)\)", testo, re.M)
    funzioni = re.findall(r"[\"']([A-Z]-[0-9A-Z-]+)[\"']", m.group(1)) if m else []
    per_browser = not re.search(r"^PER_BROWSER\s*=\s*False", testo, re.M)
    return funzioni, per_browser


def md5(percorso):
    try:
        return hashlib.md5(open(percorso, "rb").read()).hexdigest()[:8]
    except OSError:
        return "?"


def una(o, file, browser, base):
    nome = os.path.basename(file)[:-3]
    corto = nome.split("-")[1]
    funzioni, _ = leggi(file)
    ev = os.path.join(o.evidenze, DESKTOP, browser, corto)
    os.makedirs(ev, exist_ok=True)
    amb = dict(os.environ, MOZ_ENABLE_WAYLAND="1")
    cmd = [sys.executable, os.path.abspath(__file__), "--interno", file,
           "--scatola", DESKTOP, "--browser", browser, "--host", "127.0.0.1",
           "--porta", str(o.porta), "--porte-base", str(base), "--evidenze", ev, "--guasto"]
    if o.modo == "finestra":
        amb.update(REMOTIX_SCHERMO_ANNIDATO="1", REMOTIX_CHROME_OPZIONI=CHROME_OPZIONI)
    else:
        cmd.append("--headless")
        amb.pop("WAYLAND_DISPLAY", None)
        amb.pop("REMOTIX_SCHERMO_ANNIDATO", None)
    inizio = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    t0 = time.time()
    righe, fuori = [], ""
    with open(os.path.join(ev, "uscita.log"), "w") as log:
        try:
            pr = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                  errors="replace", env=amb, cwd=SUITE, start_new_session=True)
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
        except Exception as e:                                       # noqa: BLE001
            fuori = "the bench could not launch the test: %r" % e
    durata = round(time.time() - t0)
    viste = {(r.get("funzione"), r.get("passata")) for r in righe}
    for f in funzioni:
        for ps in ("sana", "guasto"):
            if (f, ps) not in viste:
                righe.append({"funzione": f, "passata": ps, "esito": "BLOCKED",
                              "ragione": fuori or "the test gave no verdict for %s "
                              "(see uscita.log)" % f, "guasto_visto": None, "evidenze": []})
    uscita = []
    for r in righe:
        f = r.get("funzione", "?")
        uscita.append({
            "giro": GIRO,
            "test": "T-%s-%s-%s%s" % (f[2:] if f.startswith("F-") else f, DESKTOP, browser,
                                       "-guasto" if r.get("passata") == "guasto" else ""),
            "funzione": f, "passata": r.get("passata", "sana"), "prova": nome,
            "desktop": DESKTOP, "browser": browser, "versione": r.get("versione", ""),
            "sistema": os.environ.get("RXNV_SISTEMA", "?") + (" · HEADLESS" if o.modo != "finestra" else ""),
            "binario": md5("/usr/libexec/remotix/remotix"),
            "pagina": md5("/usr/share/remotix/pagina.html"),
            "commit": os.environ.get("RXNV_VERSIONE", "?"),
            "inizio": inizio, "durata_s": durata, "esito": r.get("esito"),
            "ragione": r.get("ragione", ""), "atteso": r.get("atteso", ""),
            "osservato": r.get("osservato", ""), "guasto_visto": r.get("guasto_visto"),
            "evidenze": [os.path.join(ev, "uscita.log")] + [x for x in r.get("evidenze") or [] if x],
            "difetto": None})
    with open(o.registro, "a", errors="backslashreplace") as reg:
        for r in uscita:
            reg.write(json.dumps(r, ensure_ascii=False) + "\n")
    conto = {}
    for r in uscita:
        conto[r["esito"]] = conto.get(r["esito"], 0) + 1
    print("[%s %s] %-40s %4d s  %s" % (DESKTOP, browser, nome, durata,
                                        " ".join("%s=%d" % kv for kv in sorted(conto.items()))),
          flush=True)
    return uscita


def principale():
    if len(sys.argv) > 2 and sys.argv[1] == "--interno":
        return interno(sys.argv[2], sys.argv[3:])
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--registro", required=True)
    a.add_argument("--evidenze", required=True)
    a.add_argument("--porta", type=int, default=7447)
    a.add_argument("--modo", choices=("finestra", "headless"), default="finestra")
    a.add_argument("--prove", default="", help="only these (e.g. f001,f018)")
    a.add_argument("--browser", default=",".join(BROWSER))
    a.add_argument("--desktop", default="xfce", choices=("gnome", "kde", "xfce", "lxqt"))
    o = a.parse_args()
    if "RXNV_REGISTRO" not in os.environ:
        a.error("RXNV_REGISTRO is missing (the file the server writes to)")
    os.makedirs(o.evidenze, exist_ok=True)
    tutti = []
    globals()["DESKTOP"] = o.desktop
    # the desktop's debug ports as in 15-giro.py
    base = 3100 + 10 * ("gnome", "kde", "xfce", "lxqt").index(o.desktop)
    print("⭐ 19-nv-suite · %s · %s · browser %s · port %d" % (
        o.desktop, o.modo, o.browser, o.porta), flush=True)
    # ⭐ 6 Oct 2026: with --prove one chooses among ALL the phase 15 tests (e.g. f012 for
    #    sound without video), not only among the six of the run; "-f012-" does not pick f012b
    scelte = PROVE
    if o.prove:
        voluti = ["-%s-" % x.strip() for x in o.prove.split(",") if x.strip()]
        scelte = [f for f in sorted(os.listdir(SUITE))
                  if f.startswith("15-f") and f.endswith(".py") and any(v in f for v in voluti)]
    for p in scelte:
        file = os.path.join(SUITE, p)
        _, per_browser = leggi(file)
        for b in o.browser.split(","):
            if not per_browser and b != "firefox":
                continue
            tutti += una(o, file, b, base)
    conto = {}
    for r in tutti:
        conto[r["esito"]] = conto.get(r["esito"], 0) + 1
    riassunto = " ".join("%s=%d" % kv for kv in sorted(conto.items()))
    print("END %s" % riassunto, flush=True)
    if conto.get("FAIL"):
        return 1
    return 3 if conto.get("BLOCKED") or not tutti else 0


if __name__ == "__main__":
    sys.exit(principale())
