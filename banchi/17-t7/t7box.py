#!/usr/bin/env python3
# T7 phase 17 — the side INSIDE the box (root, podman exec).
#   t7box.py photo USER     → JSON: the user's processes and the head of the stage
# The head of the stage is recognised as the product recognises it (src/ritrovo.h):
# pid = sid, inside the scope of a "remotix" logind session, parent outside
# that scope.  Here it is looked at from outside, to compare it with the log.
import json
import os
import pwd
import subprocess
import sys


def load(p):
    try:
        with open(p, "rb") as f:
            return f.read().decode(errors="replace")
    except OSError:
        return ""


def cg(pid):
    for r in load("/proc/%s/cgroup" % pid).splitlines():
        if r.startswith("0::"):
            return r[3:]
    return ""


def photo(u):
    uid = pwd.getpwnam(u).pw_uid
    scope = {}
    for r in subprocess.run(["loginctl", "list-sessions", "--no-legend"], capture_output=True,
                            text=True).stdout.splitlines():
        c = r.split()
        if len(c) >= 3 and c[1] == str(uid):
            p = subprocess.run(["loginctl", "show-session", c[0], "-p", "Service", "-p", "Scope",
                                "-p", "State", "--value"], capture_output=True, text=True).stdout.split("\n")
            if p and p[0] == "remotix" and len(p) > 1 and p[1]:
                scope[p[1]] = {"id": c[0], "state": p[2] if len(p) > 2 else ""}
    proc, stage = [], []
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        st = load("/proc/%s/stat" % d)
        if not st:
            continue
        try:
            if os.stat("/proc/" + d).st_uid != uid:
                continue
        except OSError:
            continue
        comm = st[st.index("(") + 1:st.rindex(")")]
        rest = st[st.rindex(")") + 2:].split()
        ppid, sid = int(rest[1]), int(rest[3])
        g = cg(d)
        cmd = load("/proc/%s/cmdline" % d).replace("\0", " ").strip()[:120]
        proc.append({"pid": int(d), "comm": comm, "cg": g, "cmd": cmd})
        if sid == int(d) and g.rsplit("/", 1)[-1] in scope and cg(ppid) != g:
            stage.append({"pid": int(d), "comm": comm, "session": scope[g.rsplit("/", 1)[-1]]["id"]})
    print(json.dumps({"uid": uid, "remotix_sessions": scope, "stage": stage, "processes": proc}))


if __name__ == "__main__":
    photo(sys.argv[2])
