#!/usr/bin/env python3
# T7 fase 17 — il lato DENTRO la scatola (root, podman exec).
#   t7box.py foto UTENTE   → JSON: i processi dell'utente e il capo del palco
# Il capo del palco si riconosce come lo riconosce il prodotto (src/ritrovo.h):
# pid = sid, dentro la scope di una sessione logind «remotix», padre fuori da
# quella scope.  Qui lo si guarda da fuori, per confrontarlo col registro.
import json
import os
import pwd
import subprocess
import sys


def leggi(p):
    try:
        with open(p, "rb") as f:
            return f.read().decode(errors="replace")
    except OSError:
        return ""


def cg(pid):
    for r in leggi("/proc/%s/cgroup" % pid).splitlines():
        if r.startswith("0::"):
            return r[3:]
    return ""


def foto(u):
    uid = pwd.getpwnam(u).pw_uid
    scope = {}
    for r in subprocess.run(["loginctl", "list-sessions", "--no-legend"], capture_output=True,
                            text=True).stdout.splitlines():
        c = r.split()
        if len(c) >= 3 and c[1] == str(uid):
            p = subprocess.run(["loginctl", "show-session", c[0], "-p", "Service", "-p", "Scope",
                                "-p", "State", "--value"], capture_output=True, text=True).stdout.split("\n")
            if p and p[0] == "remotix" and len(p) > 1 and p[1]:
                scope[p[1]] = {"id": c[0], "stato": p[2] if len(p) > 2 else ""}
    proc, palco = [], []
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        st = leggi("/proc/%s/stat" % d)
        if not st:
            continue
        try:
            if os.stat("/proc/" + d).st_uid != uid:
                continue
        except OSError:
            continue
        comm = st[st.index("(") + 1:st.rindex(")")]
        resto = st[st.rindex(")") + 2:].split()
        ppid, sid = int(resto[1]), int(resto[3])
        g = cg(d)
        cmd = leggi("/proc/%s/cmdline" % d).replace("\0", " ").strip()[:120]
        proc.append({"pid": int(d), "comm": comm, "cg": g, "cmd": cmd})
        if sid == int(d) and g.rsplit("/", 1)[-1] in scope and cg(ppid) != g:
            palco.append({"pid": int(d), "comm": comm, "sessione": scope[g.rsplit("/", 1)[-1]]["id"]})
    print(json.dumps({"uid": uid, "sessioni_remotix": scope, "palco": palco, "processi": proc}))


if __name__ == "__main__":
    foto(sys.argv[2])
