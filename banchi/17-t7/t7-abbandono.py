#!/usr/bin/env python3
# T7 phase 17 — the abandonment clock on a desktop FOUND AGAIN (no child).
# On the server as nicfio, lock already taken, new binary already in the box.
#   python3 t7-abbandono.py DESKTOP [SECONDS]
# A user enters with the real browser and leaves (browser closed: the desktop stays);
# the service restarts with --abandon-s SECONDS; the new parent finds it again, and
# when time is up it must spawn a child that CLOSES the desktop.
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, "/media/REMOTIX/src/controllo/banchi/15-suite")
D = sys.argv[1]
SEC = int(sys.argv[2]) if len(sys.argv) > 2 else 60
sys.argv = [sys.argv[0], "--container_box", D, "--browser", "firefox"]
import suite as S                                                     # noqa: E402

BASE = "/media/REMOTIX/tmp/t7"
BOX = "rete11-" + D
PORT = {"gnome": 8511, "kde": 8512, "xfce": 8513, "lxqt": 8514}[D]
EV = os.path.join(BASE, "%s-abbandono" % D)
os.makedirs(EV, exist_ok=True)


def log(m):
    print("%s [%s abandonment] %s" % (time.strftime("%H:%M:%S"), D, m), flush=True)


def inside(cmd, t=60):
    r = subprocess.run(["sudo", "-S", "-p", "", "podman", "exec", BOX, "sh", "-c", cmd],
                       input=S._sudo_password(), capture_output=True, text=True, errors="replace",
                       timeout=t)
    return r.returncode, (r.stdout + r.stderr)


def stage(u):
    c, t = inside("python3 /tmp/t7box.py picture %s" % u)
    try:
        return json.loads(t.strip().splitlines()[-1])
    except Exception:                            # noqa: BLE001
        return {"failure": t[-200:]}


o = S.call_args("t7-abbandono")
o.evidence = EV
E = S.Outcomes(o)
outcome = {"desktop": D, "abbandono_s": SEC}
with S.Session(o, "974", E) as s:
    ok, m = s.enter()
    log("enter: %s %s" % (ok, m[:80]))
    time.sleep(5)
    s.turn_off_browser()
    p0 = stage(s.chi)
    outcome["palco_prima"] = p0.get("stage")
    t0 = float(inside("date +%s.%N")[1].strip())
    row = ("systemctl stop rete11-server; systemctl reset-failed rete11-server; "
            "systemd-run --unit=rete11-server --working-directory=/opt/remotix "
            "--property=StandardError=append:/var/lib/rete11/registro.log --property=KillMode=mixed "
            "/opt/remotix/remotix --address 0.0.0.0 --label_name 127.0.0.1 --port %d --abandon-s %d "
            "--certificates /var/lib/rete11/certificates --page_v /opt/remotix/pagina.html "
            "--ban-file /var/lib/rete11/ban --command-socket /var/lib/rete11/command.sock "
            "--survey /var/lib/rete11/survey --chatter --journal" % (PORT, SEC))
    log("restart with --abandon-s %d: %s" % (SEC, inside(row)[1].strip()[:120]))
    time.sleep(SEC + 25)
    c, t = inside("journalctl -o short-unix --no-pager --since @%d | grep -a 'FOUND AGAIN\\|found again "
                  "at\\|ABANDONMENT\\|I spawn one\\|ABANDONED\\|graphical session\\|no longer' "
                  "| cut -c1-330" % int(t0))
    with open(os.path.join(EV, "righe.txt"), "w") as f:
        f.write(t)
    outcome["line_list"] = [r[:260] for r in t.splitlines()][:14]
    p1 = stage(s.chi)
    outcome["palco_dopo"] = p1.get("stage")
    outcome["sessioni_remotix_dopo"] = p1.get("sessioni_remotix")
    outcome["processes_after"] = [(x["pid"], x["comm"]) for x in p1.get("processes", [])][:20]
print("T7ABB " + json.dumps(outcome, ensure_ascii=False), flush=True)
