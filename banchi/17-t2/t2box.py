#!/usr/bin/env python3
# T2 phase 17 — the side INSIDE the box (runs as root with podman exec).
#   t2box.py foto USER                → the BEFORE/AFTER snapshots, text
#   t2box.py sorveglia USER DIR SEC   → records births/deaths every 50 ms and
#                                       attaches strace to the user's processes
import json
import os
import subprocess
import sys
import time

STRACE = "/tmp/t2s/usr/bin/strace"
LIBS = "/tmp/t2s/usr/lib/x86_64-linux-gnu"


def leggi(p):
    try:
        with open(p, "rb") as f:
            return f.read()
    except OSError:
        return b""


def processi():
    v = {}
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        st = leggi("/proc/%s/stat" % d).decode(errors="replace")
        if not st:
            continue
        try:
            comm = st[st.index("(") + 1:st.rindex(")")]
            resto = st[st.rindex(")") + 2:].split()
        except ValueError:
            continue
        uid = None
        for r in leggi("/proc/%s/status" % d).decode(errors="replace").splitlines():
            if r.startswith("Uid:"):
                uid = int(r.split()[1])
        cg = leggi("/proc/%s/cgroup" % d).decode(errors="replace").strip()
        cmd = leggi("/proc/%s/cmdline" % d).replace(b"\0", b" ").decode(errors="replace").strip()
        v[int(d)] = {"pid": int(d), "ppid": int(resto[1]), "sid": int(resto[3]), "uid": uid,
                     "comm": comm, "cg": cg.replace("0::", ""), "cmd": cmd[:160]}
    return v


def sh(c):
    r = subprocess.run(c, shell=True, capture_output=True, text=True, errors="replace")
    return (r.stdout + r.stderr).rstrip()


def foto(u):
    uid = sh("id -u %s" % u)
    print("### ora %s" % time.strftime("%H:%M:%S"))
    print("### loginctl list-sessions\n" + sh("loginctl list-sessions --no-legend"))
    for s in sh("loginctl list-sessions --no-legend").splitlines():
        c = s.split()
        if len(c) >= 3 and c[2] == u:
            print("### loginctl show-session %s\n" % c[0] + sh(
                "loginctl show-session %s -p Id -p Leader -p Scope -p Class -p Type -p Remote "
                "-p RemoteHost -p Service -p State -p Active -p Seat -p TTY" % c[0]))
    print("### loginctl show-user\n" + sh("loginctl show-user %s -p State -p Linger -p Sessions "
                                         "-p Display -p Service -p Slice" % u))
    print("### systemctl --user list-units (%s@)\n" % u + sh(
        "systemctl --user -M %s@ list-units --no-pager --plain --no-legend 2>&1 | grep -v '\\.device\\|\\.mount\\|\\.path\\|\\.target ' " % u))
    print("### systemd-cgls\n" + sh("systemd-cgls --no-pager -l 2>&1 | cut -c1-220"))
    print("### rete11-server\n" + sh("systemctl show rete11-server -p MainPID -p KillMode -p ActiveState -p ControlGroup"))
    pr = processi()
    padre = sh("systemctl show -p MainPID --value rete11-server")
    print("### processes of the user (uid %s) and of the parent %s" % (uid, padre))
    for p in sorted(pr.values(), key=lambda x: x["pid"]):
        if str(p["uid"]) == uid or str(p["pid"]) == padre or str(p["ppid"]) == padre:
            print("%6d %6d sid=%-6d uid=%-5s %-16s %-70s %s" % (
                p["pid"], p["ppid"], p["sid"], p["uid"], p["comm"], p["cg"], p["cmd"][:90]))


def sorveglia(u, dir_, sec):
    uid = int(sh("id -u %s" % u))
    padre = sh("systemctl show -p MainPID --value rete11-server")
    pr = processi()
    bersagli = [p for p in pr.values() if p["uid"] == uid or str(p["pid"]) == padre]
    # strace: one file per process (-ff not needed: -o with several -p writes [pid N])
    args = [STRACE, "-tt", "-e", "trace=none", "-e", "signal=all", "-o", dir_ + "/strace.txt"]
    for p in bersagli:
        args += ["-p", str(p["pid"])]
    st = subprocess.Popen(args, env=dict(os.environ, LD_LIBRARY_PATH=LIBS),
                          stdout=open(dir_ + "/strace.err", "w"), stderr=subprocess.STDOUT)
    with open(dir_ + "/bersagli.json", "w") as f:
        json.dump(bersagli, f)
    time.sleep(1.5)
    with open(dir_ + "/pronto", "w") as f:
        f.write("%d\n" % st.pid)
    fine = time.time() + sec
    prima = pr
    with open(dir_ + "/vita.txt", "w") as f:
        f.write("%s INIZIO %d processi\n" % (time.strftime("%H:%M:%S"), len(pr)))
        while time.time() < fine:
            time.sleep(0.05)
            ora = processi()
            t = time.time()
            ts = time.strftime("%H:%M:%S", time.localtime(t)) + ".%03d" % int((t % 1) * 1000)
            for pid in sorted(set(prima) - set(ora)):
                p = prima[pid]
                f.write("%s MORTO %6d ppid=%-6d uid=%-5s %-16s %s | %s\n" % (
                    ts, pid, p["ppid"], p["uid"], p["comm"], p["cg"], p["cmd"][:80]))
            for pid in sorted(set(ora) - set(prima)):
                p = ora[pid]
                f.write("%s NATO  %6d ppid=%-6d uid=%-5s %-16s %s | %s\n" % (
                    ts, pid, p["ppid"], p["uid"], p["comm"], p["cg"], p["cmd"][:80]))
            f.flush()
            prima = ora
    st.terminate()
    try:
        st.wait(5)
    except subprocess.TimeoutExpired:
        st.kill()


if __name__ == "__main__":
    if sys.argv[1] == "foto":
        foto(sys.argv[2])
    else:
        sorveglia(sys.argv[2], sys.argv[3], float(sys.argv[4]))
