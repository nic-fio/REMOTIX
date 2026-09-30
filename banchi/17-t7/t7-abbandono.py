#!/usr/bin/env python3
# T7 fase 17 — l'orologio dell'abbandono su un desktop RITROVATO (nessun figlio).
# Sul server come nicfio, serratura gia' presa, binario nuovo gia' nella scatola.
#   python3 t7-abbandono.py DESKTOP [SECONDI]
# Un utente entra col browser vero ed esce (browser chiuso: il desktop resta);
# il servizio riparte con --abbandono-s SECONDI; il padre nuovo lo ritrova, e
# allo scadere deve far nascere un figlio che CHIUDA il desktop.
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, "/media/REMOTIX/src/controllo/banchi/15-suite")
D = sys.argv[1]
SEC = int(sys.argv[2]) if len(sys.argv) > 2 else 60
sys.argv = [sys.argv[0], "--scatola", D, "--browser", "firefox"]
import suite as S                                                     # noqa: E402

BASE = "/media/REMOTIX/tmp/t7"
BOX = "rete11-" + D
PORTA = {"gnome": 8511, "kde": 8512, "xfce": 8513, "lxqt": 8514}[D]
EV = os.path.join(BASE, "%s-abbandono" % D)
os.makedirs(EV, exist_ok=True)


def log(m):
    print("%s [%s abbandono] %s" % (time.strftime("%H:%M:%S"), D, m), flush=True)


def dentro(cmd, t=60):
    r = subprocess.run(["sudo", "-S", "-p", "", "podman", "exec", BOX, "sh", "-c", cmd],
                       input=S._parola_sudo(), capture_output=True, text=True, errors="replace",
                       timeout=t)
    return r.returncode, (r.stdout + r.stderr)


def palco(u):
    c, t = dentro("python3 /tmp/t7box.py foto %s" % u)
    try:
        return json.loads(t.strip().splitlines()[-1])
    except Exception:                            # noqa: BLE001
        return {"errore": t[-200:]}


o = S.argomenti("t7-abbandono")
o.evidenze = EV
E = S.Esiti(o)
esito = {"desktop": D, "abbandono_s": SEC}
with S.Sessione(o, "974", E) as s:
    ok, m = s.entra()
    log("entra: %s %s" % (ok, m[:80]))
    time.sleep(5)
    s.spegni_browser()
    p0 = palco(s.chi)
    esito["palco_prima"] = p0.get("palco")
    t0 = float(dentro("date +%s.%N")[1].strip())
    riga = ("systemctl stop rete11-server; systemctl reset-failed rete11-server; "
            "systemd-run --unit=rete11-server --working-directory=/opt/remotix "
            "--property=StandardError=append:/var/lib/rete11/registro.log --property=KillMode=mixed "
            "/opt/remotix/remotix --indirizzo 0.0.0.0 --nome 127.0.0.1 --porta %d --abbandono-s %d "
            "--certificati /var/lib/rete11/certificati --pagina /opt/remotix/pagina.html "
            "--ban-file /var/lib/rete11/ban --comando-socket /var/lib/rete11/comando.sock "
            "--rilievo /var/lib/rete11/rilievo --parlantina --journal" % (PORTA, SEC))
    log("riavvio con --abbandono-s %d: %s" % (SEC, dentro(riga)[1].strip()[:120]))
    time.sleep(SEC + 25)
    c, t = dentro("journalctl -o short-unix --no-pager --since @%d | grep -a 'RITROVATO\\|ritrovati "
                  "all\\|ABBANDONO\\|ne faccio nascere\\|ABBANDONATA\\|sessione grafica\\|non c.e. piu' "
                  "| cut -c1-330" % int(t0))
    with open(os.path.join(EV, "righe.txt"), "w") as f:
        f.write(t)
    esito["righe"] = [r[:260] for r in t.splitlines()][:14]
    p1 = palco(s.chi)
    esito["palco_dopo"] = p1.get("palco")
    esito["sessioni_remotix_dopo"] = p1.get("sessioni_remotix")
    esito["processi_dopo"] = [(x["pid"], x["comm"]) for x in p1.get("processi", [])][:20]
print("T7ABB " + json.dumps(esito, ensure_ascii=False), flush=True)
