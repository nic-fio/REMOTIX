"""deskkit - what check-desktop.py and check-media.py share, on top of lib.py (which it does not modify): running things INSIDE the
user's session (its cgroup = logind's session scope, its environment = the desktop panel's), the file-write watcher (fanwatch.py:
WHO wrote which file), the counter reader of media-window.py, a quiet-box test."""
import io
import os
import re
import shlex
import subprocess
import time

import lib

HERE = os.path.dirname(os.path.abspath(__file__))
PANEL = {"xfce": "xfce4-panel", "lxqt": "lxqt-panel", "gnome": "gnome-shell", "kde": "plasmashell"}
# the desktop's own Log Out, as check-lifecycle.py
LOGOUT = {"xfce": "xfce4-session-logout --logout",
          "lxqt": "busctl --user --expect-reply=no call org.lxqt.session /LXQtSession org.lxqt.session logout",
          "gnome": "busctl --user call org.gnome.SessionManager /org/gnome/SessionManager org.gnome.SessionManager Logout u 1",
          "kde": "busctl --user call org.kde.Shutdown /Shutdown org.kde.Shutdown logout"}
IN_SH = r'''#!/bin/bash
# rx-in.sh USER CGPID ENVPID CMD...: CMD as USER, inside the cgroup of process CGPID (the logind session scope of the remote session,
# so logind and polkit see the caller as the session's own program) and with the environment of process ENVPID (the desktop's panel)
U=$1; C=$2; P=$3; shift 3
echo $$ > /sys/fs/cgroup$(sed 's/^0:://' /proc/$C/cgroup)/cgroup.procs 2>/dev/null
mapfile -d '' E < /proc/$P/environ
cd "$(getent passwd $U | cut -d: -f6)"   # the user's home, as a program started from the desktop has it (root's /root is unreadable: qterminal then fails to start its shell)
exec setpriv --reuid=$U --regid=$(id -g $U) --init-groups env -i "${E[@]}" "$@"
'''
ANCHOR = ("L=; for s in $(loginctl list-sessions --no-legend | awk -v u=%(u)s '$3==u{print $1}'); do "
          "[ \"$(loginctl show-session $s -p Class --value)\" = user ] && L=$(loginctl show-session $s -p Leader --value); done; "
          "P=$(pgrep -u %(u)s -x %(p)s | head -1); [ -n \"$L\" ] && [ -n \"$P\" ] || { echo 'NOANCHOR: no session leader or no %(p)s'; exit 9; }; ")


def put(box, local, remote, mode="755"):
    """Copy a file of prove/ (or text given as bytes/str) into the box."""
    data = open(os.path.join(HERE, local), "rb").read() if not local.startswith("\n") else local.encode()
    r = subprocess.run([box.sh, "ssh", box.name, "cat > %s && chmod %s %s" % (remote, mode, remote)], input=data, capture_output=True, timeout=60)
    if r.returncode:
        raise lib.ToolError("cannot write %s in the box: %s" % (remote, r.stderr[-150:]))


def install(box):
    r = subprocess.run([box.sh, "ssh", box.name, "cat > /tmp/rx-in.sh && chmod 755 /tmp/rx-in.sh"], input=IN_SH.encode(), capture_output=True, timeout=60)
    if r.returncode:
        raise lib.ToolError("cannot write rx-in.sh in the box: %s" % r.stderr[-150:])


def run_in(box, de, user, cmd, timeout=60, bg=False):
    """(rc, output) of `bash -c cmd` run as `user` INSIDE the session (see IN_SH). bg: detached, returns at once."""
    inner = "/tmp/rx-in.sh %s $L $P bash -c %s" % (user, shlex.quote(cmd))
    if bg:
        inner = "setsid %s </dev/null >/dev/null 2>&1 & sleep 0.5; echo started" % inner
    return box.run(ANCHOR % {"u": user, "p": PANEL[de]} + inner, timeout=timeout)


def fan_start(box, prefix, out="/tmp/rx-fan.out"):
    put(box, "fanwatch.py", "/tmp/fanwatch.py")
    box.run("pkill -f '[f]anwatch.py'; true")
    box.run("rm -f %s /tmp/rx-fan.err; setsid nohup /tmp/fanwatch.py %s %s </dev/null >/tmp/rx-fan.err 2>&1 & sleep 1; cat /tmp/rx-fan.err" % (out, prefix, out))
    for _ in range(10):
        if "ready" in box.run("cat /tmp/rx-fan.err")[1]:
            return
        time.sleep(1)
    raise lib.ToolError("the file-write watcher did not start in the box: %s" % box.run("cat /tmp/rx-fan.err")[1][-150:])


def fan_stop(box, out="/tmp/rx-fan.out"):
    """Stop the watcher; returns [(time, pid, comm, kind, path)]."""
    box.run("pkill -f [f]anwatch.py; true")
    rows = []
    for l in box.run("cat %s 2>/dev/null; true" % out, timeout=120)[1].splitlines():
        p = l.split(" ", 4)
        if len(p) == 5:
            rows.append((float(p[0]), int(p[1]), p[2], p[3], p[4]))
    return rows


def read_counter(png, cell=20, bits=20, x0=8, y0=8):
    """The number drawn by media-window.py in the top left cells of a picture whose (0,0) is the canvas' (0,0)."""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("L")
    n = 0
    for i in range(bits):
        cx, cy = x0 + i * cell + cell // 2, y0 + cell // 2
        v = sum(im.getpixel((cx + dx, cy + dy)) for dx in (-3, 0, 3) for dy in (-3, 0, 3)) / 9.0
        if v > 127:
            n |= 1 << i
    return n


def other_checks(de):
    """Other check-*.py runs (not me, not one of my ancestors, wrappers like `timeout` and `sh -c` excluded) aimed at the same box."""
    mine, p = set(), os.getpid()
    while p > 1:
        mine.add(p)
        try:
            p = int(open("/proc/%d/stat" % p).read().rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            break
    out = subprocess.run(["pgrep", "-af", r"check-[a-z-]+\.py"], capture_output=True, text=True).stdout.splitlines()
    res = []
    for l in out:
        pid, _, cmd = l.partition(" ")
        words = cmd.split()
        if int(pid) in mine or not words or not os.path.basename(words[0]).startswith("python") or "--box %s" % de not in cmd:
            continue
        res.append(l.strip()[:90])
    return res


def load():
    return open("/proc/loadavg").read().split()[0]
