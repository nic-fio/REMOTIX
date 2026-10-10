#!/usr/bin/env python3
# T2 phase 17 — what kills the desktops when REMOTIX stops.  Runs ON THE SERVER
# as nicfio, in the environment of 15-una.sh (real browsers in the suite's labwc).
#   python3 t2-misura.py DESKTOP EXPERIMENT [EXPERIMENT...]
#   EXPERIMENT: ferma (systemctl stop rete11-server) · uccidi-padre (kill -KILL
#   to the MainPID) · uccidi-figlio (kill -TERM to the child only, parent alive, browser closed)
import fcntl
import os
import subprocess
import sys
import time

sys.path.insert(0, "/media/REMOTIX/src/controllo/banchi/15-suite")
D = sys.argv[1]
ESP = sys.argv[2:]
sys.argv = [sys.argv[0], "--scatola", D, "--browser", "firefox"]
import suite as S                                                     # noqa: E402

SERRATURA = "/media/REMOTIX/rete11/.scatole.lock"
BASE = "/media/REMOTIX/tmp/t2"
BOX = "rete11-" + D


def log(m):
    print("%s [%s] %s" % (time.strftime("%H:%M:%S"), D, m), flush=True)


def sudo(cmd, t=300):
    r = subprocess.run(["sudo", "-S", "-p", "", "sh", "-c", cmd], input=S._parola_sudo(),
                       capture_output=True, text=True, errors="replace", timeout=t)
    return r.returncode, (r.stdout + r.stderr)


def tieni():
    fd = os.open(SERRATURA, os.O_RDWR | os.O_CREAT, 0o666)
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except OSError:
            log("lock held by: %s — waiting" % os.pread(fd, 200, 0).decode(errors="replace"))
            time.sleep(30)
    os.ftruncate(fd, 0)
    os.pwrite(fd, ("T2-misura-fase17 pid %d" % os.getpid()).encode(), 0)
    os.environ["REMOTIX_SCATOLE_TENUTE"] = "T2-misura-fase17"
    return fd


def scrivi(dir_, nome, testo):
    with open(os.path.join(dir_, nome), "w") as f:
        f.write(testo)


ORA = "#!/bin/sh\nf=$HOME/ora-$1.txt\nwhile :; do date +%H:%M:%S.%N >> $f; sleep 1; done\n"
TERMINALE = {
    "gnome": "gnome-terminal -- sh $HOME/t2-ora.sh terminale",
    "kde": "systemd-run --user --scope --unit=app-t2-konsole konsole -e sh $HOME/t2-ora.sh terminale",
    "xfce": "xfce4-terminal -x sh $HOME/t2-ora.sh terminale",
    "lxqt": "qterminal -e 'sh $HOME/t2-ora.sh terminale'",
}


def una(esp):
    ev = os.path.join(BASE, "%s-%s" % (D, esp))
    os.makedirs(ev, exist_ok=True)
    o = S.argomenti("t2")
    o.evidenze = ev
    E = S.Esiti(o)
    rimetti = False
    with S.Sessione(o, "917", E) as s:
        u = s.chi
        log("tenant %s, entering with the browser" % u)
        ok, m = s.entra()
        log("enter: %s %s" % (ok, m[:120]))
        if not ok:
            return "enter failed: " + m
        time.sleep(10)
        s.foto("desktop-prima")
        # the three time witnesses
        import base64
        s.sc.dentro("echo %s | base64 -d > /home/%s/t2-ora.sh; chown %s /home/%s/t2-ora.sh"
                    % (base64.b64encode(ORA.encode()).decode(), u, u, u), 30)
        print(s.nella_sessione(TERMINALE[D]))
        print(s.nella_sessione("sh $HOME/t2-ora.sh sessione"))
        print(s.nella_sessione("systemd-run --user --scope --unit=t2-testimone-utente "
                               "sh $HOME/t2-ora.sh utente"))
        time.sleep(4)
        # whoever stayed in init.scope (launched by podman exec) goes into the session's
        # scope: it is where the xfce/lxqt panel would put it
        c, t = s.sc.dentro(
            "uid=$(id -u %(u)s); sc=$(loginctl show-session $(loginctl list-sessions --no-legend "
            "| awk -v uid=$uid '$2==uid && $6==\"user\"{print $1}' | head -1) -p Scope --value); "
            "cg=/sys/fs/cgroup/user.slice/user-$uid.slice/$sc; echo scope=$sc; "
            "for p in $(ps -u %(u)s -o pid=); do grep -qx 0::/init.scope /proc/$p/cgroup 2>/dev/null && "
            "{ echo $p > $cg/cgroup.procs && echo moved $p $(cat /proc/$p/comm); }; done" % {"u": u}, 30)
        log("moved into the session: %s" % t.replace("\n", " · "))
        time.sleep(3)
        s.foto("desktop-coi-testimoni")
        c, prima = s.sc.dentro("python3 /tmp/t2box.py foto %s" % u, 60)
        scrivi(ev, "prima.txt", prima)
        c, t = s.sc.dentro("tail -n1 /home/%s/ora-*.txt" % u, 20)
        log("witnesses: %s" % t.replace("\n", " "))
        c, t0 = s.sc.dentro("date +%s", 10)
        t0 = int(t0.strip()) - 2
        s.sc.dentro("rm -rf /tmp/t2run; mkdir -p /tmp/t2run; setsid python3 /tmp/t2box.py "
                    "sorveglia %s /tmp/t2run 110 > /tmp/t2run/sorv.log 2>&1 < /dev/null &" % u, 20)
        for _ in range(60):
            c, t = s.sc.dentro("test -f /tmp/t2run/pronto && echo si", 10)
            if "si" in t:
                break
            time.sleep(0.5)
        log("watch ready")
        padre = s.sc.dentro("systemctl show -p MainPID --value rete11-server", 10)[1].strip()
        figlio = s.sc.dentro("ps -eo pid=,ppid=,user:32= | awk '$2==%s && $3==\"%s\"{print $1}' | head -1" % (padre, u), 10)[1].strip()
        log("parent %s child %s" % (padre, figlio))
        if esp == "uccidi-figlio":
            s.spegni_browser()
            time.sleep(4)
        c, ta = s.sc.dentro("date +%H:%M:%S.%N", 10)
        if esp == "ferma":
            c, t = s.sc.dentro("date +%H:%M:%S.%N; systemctl stop rete11-server; date +%H:%M:%S.%N", 120)
            rimetti = True
        elif esp == "uccidi-padre":
            c, t = s.sc.dentro("kill -KILL %s; date +%%H:%%M:%%S.%%N" % padre, 30)
            rimetti = True
        elif esp == "uccidi-figlio":
            c, t = s.sc.dentro("kill -TERM %s; date +%%H:%%M:%%S.%%N" % figlio, 30)
        log("ACTION %s at %s → %s" % (esp, ta.strip(), t.strip().replace("\n", " ")))
        scrivi(ev, "azione.txt", "%s\npadre %s figlio %s\ninizio %s\n%s\n" % (esp, padre, figlio, ta, t))
        time.sleep(38)
        c, dopo = s.sc.dentro("python3 /tmp/t2box.py foto %s" % u, 60)
        scrivi(ev, "dopo.txt", dopo)
        # ⭐ THE REATTACH: the service is restarted (as the box does) and the user
        #   comes back in — we look at whether they find THEIR desktop or a new one
        if rimetti:
            c, t = sudo("bash /media/REMOTIX/rete11/11-accendi.sh server %s" % D, 120)
            log("service restarted: rc %s" % c)
            rimetti = False
        s.spegni_browser()
        s.accendi_browser()
        ok, m = s.entra()
        log("reattach: %s %s" % (ok, m[:100]))
        time.sleep(15)
        s.foto("desktop-dopo-il-riattacco")
        c, t = s.sc.dentro("python3 /tmp/t2box.py foto %s" % u, 60)
        scrivi(ev, "riattacco.txt", t)
        c, t = s.sc.dentro("for f in /home/%s/ora-*.txt; do echo \"== $f\"; tail -n3 $f; done" % u, 20)
        scrivi(ev, "ore-riattacco.txt", t)
        log("times at reattach: %s" % t.replace("\n", " "))
        for _ in range(120):
            c, t = s.sc.dentro("pgrep -f 't2box.py sorveglia' >/dev/null || echo finita", 10)
            if "finita" in t:
                break
            time.sleep(1)
        c, t = s.sc.dentro("journalctl -o short-precise --no-pager --since @%d" % t0, 60)
        scrivi(ev, "journal.txt", t)
        c, t = s.sc.dentro("tail -n 600 /var/lib/rete11/registro.log", 30)
        scrivi(ev, "registro-remotix-dopo-riattacco.txt", t)
        for f in ("vita.txt", "strace.txt", "strace.err", "bersagli.json", "sorv.log"):
            c, t = s.sc.dentro("cat /tmp/t2run/%s" % f, 30)
            scrivi(ev, f, t)
        c, t = s.sc.dentro("journalctl -o short-precise --no-pager --since @%d" % t0, 60)
        scrivi(ev, "journal.txt", t)
        c, t = s.sc.dentro("for f in /home/%s/ora-*.txt; do echo \"== $f\"; tail -n3 $f; done" % u, 20)
        scrivi(ev, "ore.txt", t)
        log("last times: %s" % t.replace("\n", " "))
        c, t = s.sc.dentro("tail -n 400 /var/lib/rete11/registro.log", 30)
        scrivi(ev, "registro-remotix.txt", t)
    log("tenant cleared")
    if rimetti:
        c, t = sudo("bash /media/REMOTIX/rete11/11-accendi.sh server %s" % D, 120)
        log("service restarted: rc %s %s" % (c, t.strip().splitlines()[-1:] if t.strip() else ""))
    return "done"


if __name__ == "__main__":
    fd = tieni()
    sudo("podman cp /media/REMOTIX/tmp/t2/t2box.py %s:/tmp/t2box.py" % BOX)
    for e in ESP:
        try:
            log("=== %s: %s" % (e, una(e)))
        except Exception as x:                  # noqa: BLE001
            import traceback
            traceback.print_exc()
            log("=== %s: CRASHED %r" % (e, x))
        c, t = sudo("podman exec %s systemctl is-active rete11-server" % BOX)
        if t.strip() != "active":
            c, t = sudo("bash /media/REMOTIX/rete11/11-accendi.sh server %s" % D, 120)
            log("service restarted after the crash: rc %s" % c)
    os.close(fd)
