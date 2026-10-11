#!/usr/bin/env python3
# T2 phase 17 — what kills the desktops when REMOTIX stops.  Runs ON THE SERVER
# as nicfio, in the environment of 15-una.sh (real browsers in the suite's labwc).
#   python3 t2-misura.py DESKTOP EXPERIMENT [EXPERIMENT...]
#   EXPERIMENT: halt (systemctl stop rete11-server) · uccidi-padre (kill -KILL
#   to the MainPID) · uccidi-figlio (kill -TERM to the child only, parent alive, browser closed)
import fcntl
import os
import subprocess
import sys
import time

sys.path.insert(0, "/media/REMOTIX/src/controllo/banchi/15-suite")
D = sys.argv[1]
ESP = sys.argv[2:]
sys.argv = [sys.argv[0], "--box", D, "--browser", "firefox"]
import suite as S                                                     # noqa: E402

LOCK_V = "/media/REMOTIX/rete11/.scatole.lock"
BASE = "/media/REMOTIX/tmp/t2"
BOX = "rete11-" + D


def log(m):
    print("%s [%s] %s" % (time.strftime("%H:%M:%S"), D, m), flush=True)


def sudo(cmd, t=300):
    r = subprocess.run(["sudo", "-S", "-p", "", "sh", "-c", cmd], input=S._sudo_password(),
                       capture_output=True, text=True, errors="replace", timeout=t)
    return r.returncode, (r.stdout + r.stderr)


def keep():
    fd = os.open(LOCK_V, os.O_RDWR | os.O_CREAT, 0o666)
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except OSError:
            log("lock held by: %s — waiting" % os.pread(fd, 200, 0).decode(errors="replace"))
            time.sleep(30)
    os.ftruncate(fd, 0)
    os.pwrite(fd, ("T2-misura-fase17 pid %d" % os.getpid()).encode(), 0)
    os.environ["REMOTIX_KEPT_BOXES"] = "T2-misura-fase17"
    return fd


def write(dir_, name, text):
    with open(os.path.join(dir_, name), "w") as f:
        f.write(text)


NOW = "#!/bin/sh\nf=$HOME/ora-$1.txt\nwhile :; do date +%H:%M:%S.%N >> $f; sleep 1; done\n"
TERMINAL = {
    "gnome": "gnome-terminal -- sh $HOME/t2-ora.sh terminale",
    "kde": "systemd-run --user --scope --unit=app-t2-konsole konsole -e sh $HOME/t2-ora.sh terminale",
    "xfce": "xfce4-terminal -x sh $HOME/t2-ora.sh terminale",
    "lxqt": "qterminal -e 'sh $HOME/t2-ora.sh terminale'",
}


def una(esp):
    ev = os.path.join(BASE, "%s-%s" % (D, esp))
    os.makedirs(ev, exist_ok=True)
    o = S.call_args("t2")
    o.evidence = ev
    E = S.Outcomes(o)
    restore = False
    with S.Session(o, "917", E) as s:
        u = s.chi
        log("tenant %s, entering with the browser" % u)
        ok, m = s.enter()
        log("enter: %s %s" % (ok, m[:120]))
        if not ok:
            return "enter failed: " + m
        time.sleep(10)
        s.photo("desktop-prima")
        # the three time witnesses
        import base64
        s.sc.inside("echo %s | base64 -d > /home/%s/t2-ora.sh; chown %s /home/%s/t2-ora.sh"
                    % (base64.b64encode(NOW.encode()).decode(), u, u, u), 30)
        print(s.in_session(TERMINAL[D]))
        print(s.in_session("sh $HOME/t2-ora.sh sessione"))
        print(s.in_session("systemd-run --user --scope --unit=t2-testimone-utente "
                               "sh $HOME/t2-ora.sh utente"))
        time.sleep(4)
        # whoever stayed in init.scope (launched by podman exec) goes into the session's
        # scope: it is where the xfce/lxqt panel would put it
        c, t = s.sc.inside(
            "uid=$(id -u %(u)s); sc=$(loginctl show-session $(loginctl list-sessions --no-legend "
            "| awk -v uid=$uid '$2==uid && $6==\"user\"{print $1}' | head -1) -p Scope --value); "
            "cg=/sys/fs/cgroup/user.slice/user-$uid.slice/$sc; echo scope=$sc; "
            "for p in $(ps -u %(u)s -o pid=); do grep -qx 0::/init.scope /proc/$p/cgroup 2>/dev/null && "
            "{ echo $p > $cg/cgroup.procs && echo moved $p $(cat /proc/$p/comm); }; done" % {"u": u}, 30)
        log("moved into the session: %s" % t.replace("\n", " · "))
        time.sleep(3)
        s.photo("desktop-coi-testimoni")
        c, prima = s.sc.inside("python3 /tmp/t2box.py photo %s" % u, 60)
        write(ev, "prima.txt", prima)
        c, t = s.sc.inside("tail -n1 /home/%s/ora-*.txt" % u, 20)
        log("witnesses: %s" % t.replace("\n", " "))
        c, t0 = s.sc.inside("date +%s", 10)
        t0 = int(t0.strip()) - 2
        s.sc.inside("rm -rf /tmp/t2run; mkdir -p /tmp/t2run; setsid python3 /tmp/t2box.py "
                    "sorveglia %s /tmp/t2run 110 > /tmp/t2run/sorv.log 2>&1 < /dev/null &" % u, 20)
        for _ in range(60):
            c, t = s.sc.inside("test -f /tmp/t2run/pronto && echo si", 10)
            if "yes" in t:
                break
            time.sleep(0.5)
        log("watch ready")
        padre = s.sc.inside("systemctl show -p MainPID --value rete11-server", 10)[1].strip()
        child = s.sc.inside("ps -eo pid=,ppid=,user:32= | awk '$2==%s && $3==\"%s\"{print $1}' | head -1" % (padre, u), 10)[1].strip()
        log("parent %s child %s" % (padre, child))
        if esp == "uccidi-figlio":
            s.turn_off_browser()
            time.sleep(4)
        c, ta = s.sc.inside("date +%H:%M:%S.%N", 10)
        if esp == "ferma":
            c, t = s.sc.inside("date +%H:%M:%S.%N; systemctl stop rete11-server; date +%H:%M:%S.%N", 120)
            restore = True
        elif esp == "uccidi-padre":
            c, t = s.sc.inside("kill -KILL %s; date +%%H:%%M:%%S.%%N" % padre, 30)
            restore = True
        elif esp == "uccidi-figlio":
            c, t = s.sc.inside("kill -TERM %s; date +%%H:%%M:%%S.%%N" % child, 30)
        log("ACTION %s at %s → %s" % (esp, ta.strip(), t.strip().replace("\n", " ")))
        write(ev, "azione.txt", "%s\nparent %s child %s\nstart: %s\n%s\n" % (esp, padre, child, ta, t))
        time.sleep(38)
        c, dopo = s.sc.inside("python3 /tmp/t2box.py photo %s" % u, 60)
        write(ev, "dopo.txt", dopo)
        # ⭐ THE REATTACH: the service is restarted (as the box does) and the user
        #   comes back in — we look at whether they find THEIR desktop or a new one
        if restore:
            c, t = sudo("bash /media/REMOTIX/rete11/11-accendi.sh server %s" % D, 120)
            log("service restarted: rc %s" % c)
            restore = False
        s.turn_off_browser()
        s.turn_on_browser()
        ok, m = s.enter()
        log("reattach: %s %s" % (ok, m[:100]))
        time.sleep(15)
        s.photo("desktop-dopo-il-riattacco")
        c, t = s.sc.inside("python3 /tmp/t2box.py photo %s" % u, 60)
        write(ev, "riattacco.txt", t)
        c, t = s.sc.inside("for f in /home/%s/ora-*.txt; do echo \"== $f\"; tail -n3 $f; done" % u, 20)
        write(ev, "ore-riattacco.txt", t)
        log("times at reattach: %s" % t.replace("\n", " "))
        for _ in range(120):
            c, t = s.sc.inside("pgrep -f 't2box.py sorveglia' >/dev/null || echo finita", 10)
            if "finished" in t:
                break
            time.sleep(1)
        c, t = s.sc.inside("journalctl -o short-precise --no-pager --since @%d" % t0, 60)
        write(ev, "journal.txt", t)
        c, t = s.sc.inside("tail -n 600 /var/lib/rete11/registro.log", 30)
        write(ev, "registro-remotix-dopo-riattacco.txt", t)
        for f in ("vita.txt", "strace.txt", "strace.err", "bersagli.json", "sorv.log"):
            c, t = s.sc.inside("cat /tmp/t2run/%s" % f, 30)
            write(ev, f, t)
        c, t = s.sc.inside("journalctl -o short-precise --no-pager --since @%d" % t0, 60)
        write(ev, "journal.txt", t)
        c, t = s.sc.inside("for f in /home/%s/ora-*.txt; do echo \"== $f\"; tail -n3 $f; done" % u, 20)
        write(ev, "ore.txt", t)
        log("last times: %s" % t.replace("\n", " "))
        c, t = s.sc.inside("tail -n 400 /var/lib/rete11/registro.log", 30)
        write(ev, "registro-remotix.txt", t)
    log("tenant cleared")
    if restore:
        c, t = sudo("bash /media/REMOTIX/rete11/11-accendi.sh server %s" % D, 120)
        log("service restarted: rc %s %s" % (c, t.strip().splitlines()[-1:] if t.strip() else ""))
    return "done"


if __name__ == "__main__":
    fd = keep()
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
