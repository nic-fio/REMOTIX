#!/usr/bin/env python3
"""check-prelocal - a LOCAL graphical login closes the user's remote desktop FIRST (DECISIONS-11 §11.57), with a real browser (Chrome).

    python3 check-prelocal.py [--box xfce] [--only P1,P6,P7]

Runs ON THE DEV SERVER (lib.py). Uses its own users pl1 (P1-P3, one remote desktop carried through) and pl2 (P4, P5: no desktop).
The boxes are systemd containers with no display manager, so the LOCAL login is SIMULATED: the PAM hook is run as root inside the
box, with the environment pam_exec would give it:
    env -i PAM_TYPE=open_session PAM_SERVICE=prova-dm PAM_USER=<user> XDG_SEAT=seat0 XDG_SESSION_CLASS=user XDG_SESSION_TYPE=wayland
        /usr/libexec/remotix/remotix-local-login
One line per check:  PASS|FAIL|BLOCKED name - evidence.  Exit 0 only if every selected case PASS.
  P1 hook-closes-desktop  a remote desktop of pl1 is open: the hook returns 0 within 15 s and afterwards nothing of the user is left
                          (no logind session of the service, no program, no unit of the desktop in the user manager), the page
                          was told (0x04), the journal has the request
  P2 new-desktop-after    12 s later (births are refused for 10 s after a request) a new remote login of pl1 gets a working desktop
  P3 hook-ignores         five calls that are not a local graphical login (no seat, close_session, greeter, tty, service remotix):
                          each returns 0 in under 1 s and the desktop of pl1 is still there and alive
  P4 no-desktop           pl2 has no remote desktop: the hook returns 0 in under 2 s
  P5 service-stopped      `systemctl stop remotix`: the hook returns 0 in under 2 s; the service is started again at the end
  P6 pam-line-order       /etc/pam.d/common-session has the pam_exec line of remotix-local-login AFTER the pam_systemd line
  P7 busy-terminal        (ANY of the four desktops) the remote desktop of pl3 has the desktop's terminal running `top`; the REAL local login of the same
                          user (display-manager autologin, test-bench config, DM restarted) must reach a local desktop (session with the seat, local
                          shell, local compositor) AND leave NOTHING of the remote one: no process, no desktop unit with the same invocation,
                          no `remotix` logind session, no KWin `--virtual` / REMOTIX_KDE_HOST=1 (KDE); no new core dump of the user, no new AVC of
                          remotix_t (the known `search` on sysctl_dev_t excluded). Caps: local desktop 90 s, remote gone 20 s later.
  P8 unsaved-editor       the same with an editor holding UNSAVED text (kwrite on KDE, mousepad on XFCE); GNOME and LXQt: BLOCKED (no simple, reliable
                          way to open an unsaved document without interaction)
P7/P8 make the forced-close road run (a desktop that is NOT empty): P1 closes an empty desktop only. They are slow (about 3 min each) and need the
VM's display manager: BLOCKED (never PASS) when the program cannot be started inside the remote desktop. `--only` picks cases (default: all eight).
Everything is seen from INSIDE the box. FAIL = product (also: page or login refused). BLOCKED = the tool could not look."""
import argparse
import io
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402
import deskkit as K  # noqa: E402
from lib import PASS, FAIL, BLOCKED, Fail, ToolError  # noqa: E402

PW = "pl-pass-2026"
OLD_NAMES = ("P1-hook-closes-desktop", "P2-new-desktop-after", "P3-hook-ignores", "P4-no-desktop", "P5-service-stopped", "P6-pam-line-order")
NEW_NAMES = ("P7-busy-terminal", "P8-unsaved-editor")
NAMES = OLD_NAMES + NEW_NAMES
HOOK = "/usr/libexec/remotix/remotix-local-login"
FULL = {"PAM_TYPE": "open_session", "PAM_SERVICE": "prova-dm", "XDG_SEAT": "seat0", "XDG_SESSION_CLASS": "user", "XDG_SESSION_TYPE": "wayland"}
# the sessions of a user with the service that opened them (Service=remotix is ours)
SESS = ("for i in $(loginctl list-sessions --no-legend | awk -v u=%(u)s '$3==u{print $1}'); do echo \"@@ $i $(loginctl show-session $i "
        "-p State -p Service -p Seat | tr '\\n' ' ')\"; done; true")
# what the user manager still runs of a desktop (empty when the user manager is gone)
UNITS = ("u=$(id -u %(u)s); systemctl is-active user@$u.service >/dev/null 2>&1 || exit 0; "
         "systemctl --user -M $u@ list-units --state=active --no-legend --no-pager 2>/dev/null "
         "| awk '{print $1}' | grep -E '^(graphical-session\\.target|app-|org\\.gnome\\.|plasma-|xfce|lxqt)' | head -8; "
         "ls /run/user/$u/systemd/user.control 2>/dev/null | head -5; true")
KWIN = "u=$(id -u %(u)s); systemctl --user -M $u@ is-active plasma-kwin_wayland.service 2>&1 | head -1; true"


class Ctx:
    def __init__(self, rig):
        self.rig, self.box, self.t0 = rig, rig.box, int(time.time()) - 5

    def sessions(self, user):
        return [l[3:].strip() for l in self.box.run(SESS % {"u": user})[1].splitlines() if l.startswith("@@ ")]

    def remote_sessions(self, user):
        return [s for s in self.sessions(user) if "Service=remotix" in s]

    def procs(self, user):
        t = self.box.run("ps -u %s -o pid=,comm= | sort -n | head -40; true" % user)[1]
        return [" ".join(l.split()) for l in t.splitlines() if l.strip()]

    def journal(self, grep, n=6):
        return self.box.journal(grep, since="@%d" % self.t0, n=n)

    def hook(self, user, env=None, drop=(), timeout=60):
        """Run the hook as root with exactly that environment; returns (exit status, seconds measured inside the box)."""
        e = dict(FULL if env is None else env)
        e["PAM_USER"] = user
        for k in drop:
            e.pop(k, None)
        args = " ".join("%s=%s" % kv for kv in sorted(e.items()))
        c, t = self.box.run("s=$(date +%%s.%%N); env -i %s %s; rc=$?; e=$(date +%%s.%%N); "
                            "echo \"rc=$rc t=$(awk -v a=$s -v b=$e 'BEGIN{printf \"%%.2f\", b-a}')\"" % (args, HOOK), timeout=timeout)
        m = re.search(r"rc=(\d+) t=([\d.]+)", t)
        if not m:
            raise ToolError("the hook gave no answer line: %s" % t[-150:])
        return int(m.group(1)), float(m.group(2))


# generic helpers of the user manager that a normal Log Out also leaves for a moment (the manager then exits with the last session:
# check-lifecycle waits up to 40 s for NO process and NO logind session at all) — they get the same grace here, a desktop does not
HELPERS = ("remotix", "systemd", "(sd-pam)", "dbus-daemon", "dbus-broker", "pipewire", "wireplumber", "pipewire-pulse", "mpris-proxy", "obexd",
           "gvfsd", "gvfs", "at-spi", "dconf-service", "gpg-agent", "ssh-agent", "gcr-ssh-agent", "gnome-keyring-d", "xdg-desktop-por",
           "xdg-document-po", "xdg-permission-", "tumblerd", "xfconfd", "kded6", "kdeconnectd", "kactivitymanage", "xdg-desktop-portal",
           "plasma_waitforn", "catatonit")   # catatonit: the podman «pause» process Konsole starts (its container/Toolbx detection), a scope of the user manager and not a program of the desktop (seen 25 Nov 2026, KDE, P7); the others:
# Plasma's tiny «wait for a D-Bus name» helper: still there for a moment at the first sample, gone within the grace (measured 22 Nov 2026, KDE)


def is_helper(comm):
    return any(comm.startswith(h) for h in HELPERS)


def nothing_left_first(ctx, user, de):
    """The «nothing left» facts after a full close. The FIRST sample, taken at once, must already show no logind session of the
    service, no process of a desktop (only the helpers above), no drop-in of ours in the user manager and, on KDE, plasma-kwin_wayland
    not active. The helpers get `grace` s to go (as check-lifecycle: no process and no session of the user at all 40 s later); desktop
    units of the user manager that are still listed at the first sample are told in the evidence and must be gone within `grace` too.
    Returns (problems, facts)."""
    sess = ctx.remote_sessions(user)
    left = ctx.procs(user)
    progs = [x for x in left if not is_helper(x.split()[-1])]
    units = [x for x in ctx.box.run(UNITS % {"u": user})[1].splitlines() if x.strip()]
    dropins = [x for x in units if not re.match(r"^(graphical-session\.target|app-|org\.gnome\.|plasma-|xfce|lxqt)", x)]
    kwin = ctx.box.run(KWIN % {"u": user})[1].strip() if de == "kde" else ""
    bad = []
    if sess:
        bad.append("at the first sample the logind session(s) of the service were still there: %s" % sess)
    if progs:
        bad.append("at the first sample %d program(s) of the desktop were left: %s" % (len(progs), progs[:10]))
    if dropins:
        bad.append("at the first sample drop-ins left in the user manager: %s" % dropins)
    if kwin == "active":
        bad.append("at the first sample plasma-kwin_wayland.service was still active")
    first = "first sample: %d process(es) (%d helper(s)), %d desktop unit(s) %s" % (
        len(left), len(left) - len(progs), len(units) - len(dropins), [x for x in units if x not in dropins][:6])
    return bad, [first] + (["plasma-kwin_wayland.service \"%s\"" % (kwin or "not there")] if de == "kde" else [])


def nothing_left_wait(ctx, user, grace=40):
    """Then, as check-lifecycle: nothing of the user at all (no process, no logind session, no unit) within `grace` s."""
    bad = []
    t0, end = time.time(), time.time() + grace
    while True:  # the same end as a normal Log Out: nothing of the user at all, unit lists empty
        left, sess = ctx.procs(user), ctx.sessions(user)
        units = [x for x in ctx.box.run(UNITS % {"u": user})[1].splitlines() if x.strip()]
        if (not left and not sess) or time.time() > end:
            break
        time.sleep(2)
    if left or sess or units:
        bad.append("%d s after the hook: %d process(es) %s, logind session(s) %s, unit(s) %s still there" % (grace, len(left), left[:8], sess, units[:6]))
    return bad, ["all gone after %.0f s (no process, no session, no unit)" % (time.time() - t0)]


# ------------------------------------------------------------------------------------------------ P7 / P8: a NOT empty remote desktop
# The desktop's terminal, as (binary, command) alternatives tried in order (the command runs INSIDE the remote desktop, deskkit.run_in).
# Fedora 45 Workstation has Ptyxis (GNOME Terminal is only a fallback); the others as check-desktop.py's TERMINAL.
TERMINALS = {"gnome": (("ptyxis", "ptyxis -s -x top"), ("ptyxis", "ptyxis -s -- top"), ("gnome-terminal", "gnome-terminal -- top")),
             "kde": (("konsole", "konsole -e top"),),
             "xfce": (("xfce4-terminal", "xfce4-terminal -x top"),),
             "lxqt": (("qterminal", "qterminal -e top"),)}
# An editor with UNSAVED text, no interaction: text on stdin (kate --stdin, mousepad -). GNOME Text Editor has no stdin and keeps drafts by itself
# (no «save?» question), FeatherPad's stdin is not known: no simple, reliable way there -> the case says BLOCKED.
EDITORS = {"kde": ("kwrite", "printf 'REMOTIX unsaved text\\n' | kwrite --stdin"),   # Fedora 45 KDE live ships KWrite, not Kate (checked 25 Nov 2026)
           "xfce": ("mousepad", "printf 'REMOTIX unsaved text\\n' | mousepad -")}
# What makes the compositor of a desktop (xfce: the local session is X11 with xfwm4, the remote one has labwc)
COMPOSITOR = {"gnome": ("gnome-shell",), "kde": ("kwin_wayland",), "xfce": ("xfwm4", "labwc"), "lxqt": ("labwc",)}
DM = {"gnome": "gdm", "kde": "plasmalogin", "xfce": "lightdm", "lxqt": "sddm"}
LOCAL_CAP, GONE_CAP = 90, 20   # s: the local desktop arrives within LOCAL_CAP of the DM restart; the remote is gone GONE_CAP after that
PROCS = ("for p in $(pgrep -u %(u)s); do [ -r /proc/$p/stat ] || continue; "
         "echo \"$p $(sed 's/.*) //' /proc/$p/stat | awk '{print $1, $20}') $(cat /proc/$p/comm 2>/dev/null)\"; done; true")   # pid state starttime comm
UNIT_IDS = ("systemctl is-active user@$(id -u %(u)s).service >/dev/null 2>&1 || exit 0; "
            "for x in $(systemctl --user -M %(u)s@ list-units --state=active --no-legend --no-pager --plain 2>/dev/null | awk '{print $1}' "
            "| grep -E '^(app-|org\\.gnome\\.|gnome-|plasma-|xfce|lxqt)'); do echo \"$x $(systemctl --user -M %(u)s@ show -p InvocationID --value $x 2>/dev/null)\"; done; true")
KDE_MARKS = ("for p in $(pgrep -u %(u)s); do tr '\\0' '\\n' < /proc/$p/environ 2>/dev/null | grep -qx REMOTIX_KDE_HOST=1 && echo \"$p $(cat /proc/$p/comm)\"; done; "
             "ps -u %(u)s -o pid=,args= | grep -E 'kwin_wayland.*--virtual' | grep -v grep | cut -c1-120; true")
# test-bench autologin (a deterministic REAL local login), written and removed here; xfce/lxqt use the scripts of banco-vm/ (as prelocal.sh)
AUTO_ON = {"gnome": "f=/etc/gdm/custom.conf; grep -q '^\\[daemon\\]' $f || exit 9; [ -f $f.rxbak ] || cp -p $f $f.rxbak; "
                    "sed -i '/^AutomaticLogin/d;/^\\[daemon\\]/a AutomaticLoginEnable=True\\nAutomaticLogin=%(u)s' $f; echo gdm custom.conf: autologin %(u)s",
           "kde": "mkdir -p /etc/plasmalogin.conf.d; printf '[Autologin]\\nUser=%(u)s\\nSession=plasma.desktop\\nRelogin=false\\n' "
                  "> /etc/plasmalogin.conf.d/99-remotix-bench.conf; echo plasmalogin autologin %(u)s"}
AUTO_OFF = {"gnome": "f=/etc/gdm/custom.conf; [ -f $f.rxbak ] && cp -p $f.rxbak $f && rm -f $f.rxbak; true",   # our own backup, taken above
            "kde": "rm -f /etc/plasmalogin.conf.d/99-remotix-bench.conf; true"}
AUTO_SCRIPT = {"xfce": "autologin-lightdm.sh", "lxqt": "autologin-sddm.sh"}


def procs_of(box, user):
    """[(pid, state, starttime, comm)] of the user's processes."""
    rows = []
    for l in box.run(PROCS % {"u": user})[1].splitlines():
        p = l.split(None, 3)
        if len(p) == 4:
            rows.append(tuple(p))
    return rows


def unit_ids_of(box, user):
    return [" ".join(l.split()) for l in box.run(UNIT_IDS % {"u": user})[1].splitlines() if l.strip()]


def pic_changed(a, b, thr=0.3):
    """True when two PNG pictures differ (mean grey difference on a 160x120 reduction above thr): a new window is on the canvas."""
    from PIL import Image, ImageChops, ImageStat
    x, y = (Image.open(io.BytesIO(p)).convert("L").resize((160, 120)) for p in (a, b))
    return ImageStat.Stat(ImageChops.difference(x, y)).mean[0] > thr


def autologin(box, de, user, on):
    if de in AUTO_SCRIPT:
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "banco-vm", AUTO_SCRIPT[de])).read()
        c, t = box.run("bash -s %s %s norestart" % ("on" if on else "off", user if on else "x"), stdin=src)
    else:
        c, t = box.run((AUTO_ON if on else AUTO_OFF)[de] % {"u": user})
    if c and on:
        raise lib.ToolError("cannot %s the bench autologin of %s in the box (rc %d): %s" % ("write", DM[de], c, t[-150:]))
    return t


def dm_restart(box, de):
    box.run("systemctl reset-failed %s 2>/dev/null; systemctl restart %s; true" % (DM[de], DM[de]), timeout=120)


def busy_case(box_name, user, kind):
    """P7 (kind "terminal") / P8 (kind "editor"): see the module docstring. Returns (status, evidence)."""
    de = box_name
    rig = lib.Rig(box_name, "chrome", user, PW, "prelocal-" + kind)
    box = rig.box
    ctx = Ctx(rig)
    t_case = ctx.t0 = int(time.time()) - 5      # core dumps, AVCs and journal lines are looked at from here
    bench_on = False
    try:
        # -- what the bench can do on this desktop (BLOCKED, never PASS, when it cannot)
        if kind == "terminal":
            alts = TERMINALS[de]
        elif de in EDITORS:
            alts = ((EDITORS[de][0], EDITORS[de][1]),)
        else:
            raise lib.ToolError("no simple, reliable way to open an editor with UNSAVED text without interaction on %s (GNOME Text Editor: no stdin, "
                                "keeps drafts by itself; FeatherPad: stdin not known): only the terminal case (P7) exists there" % de)
        if not any(box.run("command -v %s >/dev/null && echo yes" % b)[1].strip() == "yes" for b, _ in alts):
            raise lib.ToolError("none of %s is installed in the box (dnf install it): the program cannot be started inside the remote desktop" % [b for b, _ in alts])
        if kind == "terminal" and box.run("command -v top >/dev/null && echo yes")[1].strip() != "yes":
            raise lib.ToolError("`top` is not installed in the box (procps-ng)")
        box.ensure_user(user, PW)
        left = box.end_users([user])
        if left:
            raise lib.ToolError("an earlier session of %s could not be ended: %s" % (user, left))
        if box.run("systemctl is-active %s" % DM[de])[1].strip() != "active":
            raise lib.ToolError("the display manager %s is not active in the box: the real local login cannot be done" % DM[de])
        # -- the remote desktop of the user, with the program running INSIDE it
        rig.start(make_user=False)
        rig.open_page()
        ok, s = rig.try_login(retry=20)
        if not (ok and s["session"] and s["cls"] == "good"):
            raise Fail("%s not admitted: \"%s\" (%s); journal: %s" % (user, (s.get("outcome") or "").strip(), s.get("cls"), ctx.journal(user)))
        rig.settle(still=1)
        remote_sess = ctx.remote_sessions(user)
        if not remote_sess:
            raise Fail("frames shown but no logind session of the service for %s" % user)
        K.install(box)
        before_png = rig.canvas_png()
        prog, what = None, ""
        for binary, cmd in alts:
            if box.run("command -v %s >/dev/null && echo yes" % binary)[1].strip() != "yes":
                continue
            c, t = K.run_in(box, de, user, cmd, bg=True)
            if c == 9 or "NOANCHOR" in t:
                raise lib.ToolError("the bench cannot start a program inside the remote desktop of %s: %s" % (de, t[-150:]))
            end = time.time() + 25
            while time.time() < end:
                time.sleep(1)
                if kind == "terminal":
                    rows = [l.split() for l in box.run("ps -u %s -o pid=,comm=,tty= | awk '$3 ~ /pts/'" % user)[1].splitlines()]
                    hit = [r for r in rows if len(r) >= 3 and r[1] == "top"]
                else:
                    hit = [l for l in box.run("pgrep -u %s -x %s" % (user, binary))[1].split() if l.strip().isdigit()]
                if hit:
                    prog = binary
                    what = "top on %s" % hit[0][2] if kind == "terminal" else "%s pid %s" % (binary, hit[0])
                    break
            if prog:
                break
        if not prog:
            raise lib.ToolError("the program did not start inside the remote desktop in 25 s per command (%s); processes: %s" % (
                " | ".join(c for _, c in alts), ctx.procs(user)[:8]))
        time.sleep(4)   # the window gets painted and shown to the client
        if not pic_changed(before_png, rig.canvas_png()):
            raise lib.ToolError("%s is running (%s) but the picture of the remote desktop did not change: no window seen on the canvas" % (prog, what))
        # -- everything the remote desktop has now, to see afterwards that none of it is still there
        pr_before = procs_of(box, user)
        proc_set = {(p, st, c) for p, s_, st, c in pr_before}       # (pid, starttime, comm)
        remote_procs = [(p, st, c) for p, s_, st, c in pr_before if not is_helper(c)]
        units_before = unit_ids_of(box, user)
        print("%s: remote desktop of %s up, %s running (%s); %d process(es) (%d not helpers), %d desktop unit(s)" % (
            kind, user, prog, what, len(pr_before), len(remote_procs), len(units_before)), flush=True)
        # -- the REAL local login of the same user
        autologin(box, de, user, True)
        bench_on = True
        t_dm = time.time()
        dm_restart(box, de)
        loc, arrived = {}, None
        while time.time() < t_dm + LOCAL_CAP:
            time.sleep(3)
            sess = [x for x in ctx.sessions(user) if "Seat=seat0" in x and "Service=remotix" not in x]
            procs_now = procs_of(box, user)
            new = [(p, st, c) for p, s_, st, c in procs_now if (p, st, c) not in proc_set and s_ != "Z"]
            shell_new = [x for x in new if x[2] == K.PANEL[de]]
            comp_new = [x for x in new if x[2] in COMPOSITOR[de]]
            if de == "kde" and comp_new:   # a KWin of the local session is not REMOTIX's virtual one
                virt = box.run("ps -u %s -o pid=,args= | grep -E 'kwin_wayland.*--virtual' | grep -v grep | awk '{print $1}'" % user)[1].split()
                comp_new = [x for x in comp_new if x[0] not in virt]
            loc = dict(sess=sess, shell=shell_new, comp=comp_new)
            if sess and shell_new and comp_new:
                arrived = time.time() - t_dm
                break
        bad, ok_ = [], ["real local login (DM %s restarted, bench autologin)" % DM[de]]
        if arrived is None:
            hook = ctx.journal("prelocal|local login|by force|HELD", n=6)
            note = "no local desktop in %d s: local sessions %s, new local shell %s, new compositor %s" % (
                LOCAL_CAP, loc.get("sess"), loc.get("shell"), loc.get("comp"))
            if not loc.get("sess") and hook.startswith("(no remotix journal line"):
                raise lib.ToolError(note + "; REMOTIX saw no local login at all: the bench autologin did not engage, nothing to judge")
            bad.append(note)
        else:
            ok_.append("local desktop after %.0f s (session %s, shell %s, compositor %s)" % (
                arrived, loc["sess"][0].split()[0], loc["shell"][0][2], loc["comp"][0][2]))
        # -- the remote desktop is gone (GONE_CAP s after the local desktop; from the cap when the local one never came)
        end = time.time() + GONE_CAP
        while True:
            now = {(p, st, c) for p, s_, st, c in procs_of(box, user) if s_ != "Z"}
            procs_left = [x for x in remote_procs if x in now]
            units_left = [u for u in unit_ids_of(box, user) if u in units_before]
            rsess = ctx.remote_sessions(user)
            marks = box.run(KDE_MARKS % {"u": user})[1].strip()
            if not (procs_left or units_left or rsess or marks) or time.time() > end:
                break
            time.sleep(2)
        if procs_left:
            bad.append("%d process(es) of the remote desktop still alive %d s after the local desktop: %s" % (len(procs_left), GONE_CAP, [x[2] + ":" + x[0] for x in procs_left][:12]))
        if units_left:
            bad.append("desktop unit(s) of the remote desktop still active (same invocation): %s" % units_left[:10])
        if rsess:
            bad.append("logind session(s) of the service still there: %s" % rsess)
        if marks:
            bad.append("KWin --virtual / REMOTIX_KDE_HOST=1 still there: %s" % marks.replace("\n", " | ")[:300])
        if not (procs_left or units_left or rsess or marks):
            ok_.append("remote desktop gone (no process, no desktop unit of it, no remotix session, no KWin --virtual / REMOTIX_KDE_HOST=1)")
        # -- no core dump and no AVC of remotix_t since the start of the case
        cores = box.run("coredumpctl list --no-legend --no-pager -q --since @%d COREDUMP_UID=$(id -u %s) 2>&1 | grep -vi 'no coredumps'; true" % (t_case, user))[1].strip()
        if cores:
            bad.append("core dump(s) of %s since the start of the case: %s" % (user, cores.replace("\n", " | ")[:300]))
        else:
            ok_.append("no core dump of %s" % user)
        # the known AVC `search` on sysctl_dev_t (remotix_t reading /proc/sys) is EXCLUDED here: it is a recorded, accepted denial, not this rule's concern
        avc = box.run("LC_ALL=C ausearch -m avc,user_avc -ts $(LC_ALL=C date -d @%d +%%m/%%d/%%Y) $(LC_ALL=C date -d @%d +%%T) </dev/null 2>&1 "
                      "| grep -E 'type=(USER_)?AVC' | grep remotix_t | grep -vE '\\{ search \\}.*sysctl_dev_t' | cut -c1-260 | tail -5; true" % (t_case, t_case))[1].strip()
        if avc:
            bad.append("new AVC(s) of remotix_t: %s" % avc.replace("\n", " | "))
        else:
            ok_.append("no new AVC of remotix_t (sysctl_dev_t search excluded)")
        if bad:
            c, st = box.run("systemctl --user -M %s@ list-units --state=active --no-legend --no-pager --plain 2>&1 | awk '{print $1}' | head -25 | tr '\\n' ' '; true" % user)
            jl = box.run("journalctl -u remotix --no-pager -o cat --since @%d | grep -E 'by force|HELD|local excludes remote|FAILED|stop ' | tail -12 | cut -c1-220; true" % t_case)[1]
            return FAIL, "; ".join(bad) + " | ok: " + "; ".join(ok_) + " | active user units: " + st.strip() + " | processes: " + \
                str([c + ":" + p for p, s_, st_, c in procs_of(box, user)][:25]) + " | remotix journal: " + jl.replace("\n", " | ")
        return PASS, "; ".join(ok_) + " (program: %s)" % what
    finally:
        try:
            if bench_on:
                autologin(box, de, user, False)
            box.run("loginctl terminate-user %s; true" % user, timeout=60)
            if bench_on:
                dm_restart(box, de)    # back to the greeter, no autologin left
        except Exception as e:  # noqa: BLE001 - cleanup must not hide the verdict
            print("cleanup of %s: %s" % (user, lib.tool_error(e)), flush=True)
        rig.stop()
        box.end_users([user])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--box", default="xfce", choices=sorted(lib.PORTS))
    ap.add_argument("--only", default="", help="comma list of cases, by number or name (P1,P7 ...): default all eight")
    a = ap.parse_args()
    want = [x.strip().upper() for x in a.only.split(",") if x.strip()]
    sel = [n for n in NAMES if not want or n.split("-")[0] in want]
    if want and not sel:
        ap.error("--only: no such case in %s" % ", ".join(n.split("-")[0] for n in NAMES))
    old_sel = [n for n in sel if n in OLD_NAMES]
    res = lib.Results(sel)
    rig = lib.Rig(a.box, "chrome", "pl1", PW, "prelocal") if old_sel else None
    ctx = Ctx(rig) if rig else None
    st = {}

    def login_new(retry=20):
        """Open the page, sign in as pl1, wait for a desktop that shows frames. Returns the page state."""
        rig.open_page()
        ok, s = rig.try_login(retry=retry)
        if not (ok and s["session"] and s["cls"] == "good"):
            raise Fail("pl1 not admitted: \"%s\" (%s); journal: %s" % ((s.get("outcome") or "").strip(), s.get("cls"), ctx.journal("pl1")))
        d = rig.settle(still=1)
        s = rig.state()
        return s, d

    def setup():
        for u in ("pl1", "pl2"):
            ctx.box.ensure_user(u, PW)
        for u in ("pl1", "pl2"):  # an earlier run's session is ended, so that the first login is a NEW one
            ctx.box.run("loginctl terminate-user %s; for i in $(seq 25); do pgrep -u %s >/dev/null || break; sleep 1; done; true" % (u, u), timeout=60)
        if ctx.box.run("test -x %s" % HOOK)[0] != 0:
            raise Fail("%s is not installed in the box" % HOOK)
        rig.start(make_user=False)
        s, d = login_new()
        if "new" not in s["outcome"]:
            raise Fail("base failed: first login of pl1 is not \"new\": \"%s\"" % s["outcome"].strip())
        st["up_t"] = time.time()
        print("setup %s: pl1 desktop up (\"%s\"), logind sessions: %s" % (a.box, s["outcome"].strip(), ctx.sessions("pl1")), flush=True)

    def p1():
        sess0 = ctx.remote_sessions("pl1")
        if not sess0:
            raise Fail("no logind session of the service for pl1 before the hook: %s" % ctx.sessions("pl1"))
        # boxes only: RealtimeKit cannot start in a container and holds a young child's exit for 25 s
        age = time.time() - st["up_t"]
        waited = max(0.0, 31 - age)
        time.sleep(waited)
        t_start = int(time.time()) - 1
        rc, secs = ctx.hook("pl1")
        t_end = st["hook_end"] = time.time()
        bad, ok = [], ["waited %.0f s before the hook (boxes only: RealtimeKit cannot start in a container and holds a young child's exit for 25 s; "
                       "the desktop was %.0f s old)" % (waited, age + waited), "hook exit %d in %.1f s" % (rc, secs)]
        if rc != 0:
            bad.append("the hook exited %d (it must ALWAYS exit 0)" % rc)
        if secs > 15:
            bad.append("the hook took %.1f s (ceiling 15 s)" % secs)
        left_bad, left_ok = nothing_left_first(ctx, "pl1", a.box)
        bad += left_bad
        ok += left_ok
        g, end, f, s = rig.g, time.time() + 20, {}, {}
        while time.time() < end:
            s, f = rig.state(), g.js(lib.JS_FORM)
            if f.get("form") and (s["outcome"] or "").strip():
                break
            time.sleep(1)
        out = (s.get("outcome") or "").strip()
        if not f.get("form"):
            bad.append("the page was NOT told: the sign-in form did not come back in 20 s (outcome \"%s\")" % out)
        elif "precedence" not in out:
            bad.append("the page was told, but not with 0x04 (\"the local session ... took precedence\"): \"%s\"" % out)
        else:
            ok.append("page told with 0x04: \"%s\"" % out)
        # no early login here: a login inside the root side's 10 s refusal gets the page's generic «try again» and a page that
        # retries by itself would get in late (review note 2) — the refusal is in the root side's journal, not judged here
        st["early"] = (None, "not tried")
        # ⚠ evidence only: after a local login's hold the user manager is EXPECTED to stay (the local session is about to use it);
        #    «no process and no session at all» is the criterion of a Log Out with nobody coming, not of this case
        wb, wo = nothing_left_wait(ctx, "pl1", grace=15)
        ok += ["(evidence, not judged) 15 s later: " + "; ".join(wb or wo)]
        # the root side's answer lines for this request
        c, jl = ctx.box.run("journalctl -u remotix --no-pager -o cat --since @%d | grep -E 'scope ended by the root side|nothing of its REMOTIX desktop is left' | tail -4 | cut -c1-260; true" % t_start)
        jl = jl.strip()
        if not jl:
            bad.append("the journal of remotix has no root-side answer line (\"nothing of its REMOTIX desktop is left (N ms\") for the request")
        else:
            if "scope ended by the root side" in jl:
                bad.append("the root side had to end the scope itself (the close was not the child's own full close): %s" % jl.replace("\n", " | "))
            m = re.findall(r"is left \((\d+) ms", jl)
            if m:
                ms = int(m[-1])
                ok.append("root side measured %d ms" % ms)
                if ms > 10000:
                    bad.append("the root side measured %d ms (fail above 10 s; expected under 5 s)" % ms)
                elif ms > 5000:
                    ok.append("(above the 5 s expected)")
            else:
                bad.append("the root side's line has no measured time: %s" % jl.replace("\n", " | "))
            ok.append("journal: " + jl.replace("\n", " | ")[:300])
        jr = ctx.journal("prelocal|local login")
        if jr.startswith("(no remotix journal line"):
            bad.append("the journal of remotix has no line for the request")
        st["p1_ok"] = not bad
        if bad:
            return FAIL, "; ".join(bad) + " | " + "; ".join(ok) + " | sessions of pl1: %s" % ctx.sessions("pl1")
        return PASS, "; ".join(ok)

    def p2():
        if not st.get("p1_ok"):
            raise ToolError("P1 did not close the desktop: nothing to start again from")
        ok_early, early = st.get("early", (None, "not tried"))
        if ok_early:
            raise Fail("a login of pl1 %s: it GOT IN although the root side refuses births of that user for 10 s after the request" % early)
        time.sleep(max(0.0, 12 - (time.time() - st["hook_end"])))  # the root side refuses births for that user for 10 s after a request
        s, d = login_new(retry=30)
        if "new" not in s["outcome"]:
            raise Fail("the desktop after the hook is not a NEW one: \"%s\"" % s["outcome"].strip())
        sess = ctx.remote_sessions("pl1")
        if not sess:
            raise Fail("frames shown but no logind session of the service for pl1")
        return PASS, "early login: " + early + "; 12 s after the hook a new login of pl1 got \"%s\"; shell up %.0f s, picture settled (%s), logind: %s" % (
            s["outcome"].strip(), d["shell_s"], d["desc"], sess)

    def alive(s_before):
        """pl1's desktop is still there: the session of the service, the shell, the page attached."""
        s = rig.state()
        bad = []
        if not ctx.remote_sessions("pl1"):
            bad.append("no logind session of the service for pl1")
        if ctx.box.run(lib.SHELL_UP[a.box] % {"u": "pl1"})[0] != 0:
            bad.append("the desktop shell is gone")
        if not s["session"] or "precedence" in (s["outcome"] or "") or "ended" in (s["outcome"] or ""):
            bad.append("the page lost its session (\"%s\")" % (s["outcome"] or "").strip())
        return bad

    def p3():
        cases = (("no XDG_SEAT", None, ("XDG_SEAT",)),
                 ("PAM_TYPE=close_session", dict(FULL, PAM_TYPE="close_session"), ()),
                 ("XDG_SESSION_CLASS=greeter", dict(FULL, XDG_SESSION_CLASS="greeter"), ()),
                 ("XDG_SESSION_TYPE=tty", dict(FULL, XDG_SESSION_TYPE="tty"), ()),
                 ("PAM_SERVICE=remotix", dict(FULL, PAM_SERVICE="remotix"), ()))
        if not ctx.remote_sessions("pl1"):
            raise ToolError("no desktop of pl1 to leave alone (P2 did not bring one)")
        bad, ok = [], []
        for label, env, drop in cases:
            rc, secs = ctx.hook("pl1", env=env, drop=drop)
            b = []
            if rc != 0:
                b.append("exit %d" % rc)
            if secs >= 1:
                b.append("%.1f s (must be under 1 s)" % secs)
            b += alive(None)
            (bad if b else ok).append("%s: %s" % (label, "; ".join(b) if b else "0 in %.2f s, desktop alive" % secs))
        return (FAIL, "; ".join(bad) + " | ok: " + "; ".join(ok)) if bad else (PASS, "; ".join(ok))

    def p4():
        rc, secs = ctx.hook("pl2")
        if ctx.remote_sessions("pl2"):
            raise ToolError("pl2 has a REMOTIX session: the case is not «no desktop»")
        if rc != 0 or secs >= 2:
            return FAIL, "pl2 has no desktop: the hook exited %d in %.1f s (expected 0 in under 2 s)" % (rc, secs)
        gone = alive(None)
        if gone:
            return FAIL, "pl2's hook touched pl1's desktop: " + "; ".join(gone)
        return PASS, "pl2 without a desktop: hook exit 0 in %.2f s; pl1's desktop still alive" % secs

    def p5():
        try:
            c, t = ctx.box.run("systemctl stop remotix; systemctl is-active remotix", timeout=90)
            if "active" in t.splitlines()[-1:] and "inactive" not in t.splitlines()[-1:]:
                raise ToolError("the service did not stop: %s" % t[-80:])
            rc, secs = ctx.hook("pl2")
        finally:
            ctx.box.run("systemctl start remotix; for i in $(seq 40); do systemctl is-active --quiet remotix && break; sleep 1; done; systemctl is-active remotix", timeout=90)
        c, t = ctx.box.run("systemctl is-active remotix")
        if t.strip() != "active":
            raise ToolError("the service is not active again: \"%s\"" % t.strip())
        if rc != 0 or secs >= 2:
            return FAIL, "service stopped: the hook exited %d in %.1f s (expected 0 in under 2 s)" % (rc, secs)
        return PASS, "service stopped: hook exit 0 in %.2f s; service started again and active" % secs

    def p6_fedora():
        # Fedora has no common-session: the hook line is put by remotix-pam-hook in the PAM files of each login screen, BEFORE `pam_selinux open`
        # (that module sets the exec context of the NEXT exec: a pam_exec line after it would spend it on the hook, AVC `entrypoint`)
        c, t = ctx.box.run("for f in /etc/pam.d/gdm-* /etc/pam.d/plasmalogin* /etc/pam.d/lightdm* /etc/pam.d/sddm*; do [ -f \"$f\" ] || continue; "
                           "case $f in *.rpm*|*greeter*|*launch-environment*) continue;; esac; "
                           "h=$(grep -nE '^[[:space:]]*session[[:space:]]+[^#]*pam_exec\\.so.*remotix-local-login' \"$f\" | head -1 | cut -d: -f1); "
                           "s=$(grep -nE '^[[:space:]]*session[[:space:]]+[^#]*pam_selinux\\.so[[:space:]]+open' \"$f\" | head -1 | cut -d: -f1); "
                           "echo \"$f hook=${h:-none} selinux_open=${s:-none}\"; done")
        rows = [l.split() for l in t.strip().splitlines() if l.strip()]
        if not rows:
            raise ToolError("no PAM file of a login screen found to look at")
        bad = [r[0] for r in rows if r[1] == "hook=none" or (r[2] != "selinux_open=none" and int(r[1][5:]) >= int(r[2][13:]))]
        if bad:
            return FAIL, "hook line missing or NOT before pam_selinux open in: %s (%s)" % (" ".join(bad), "; ".join(" ".join(r) for r in rows))
        return PASS, "the hook line is before pam_selinux open in every login-screen file: " + "; ".join(" ".join(r) for r in rows)

    def p6():
        if ctx.box.run("[ -f /etc/pam.d/common-session ] && echo yes")[1].strip() != "yes":
            return p6_fedora()
        c, t = ctx.box.run("grep -nE '^[[:space:]]*session[[:space:]]+[^#]*pam_systemd\\.so' /etc/pam.d/common-session | head -3; echo ---; "
                           "grep -nE '^[[:space:]]*session[[:space:]]+[^#]*pam_exec\\.so.*remotix-local-login' /etc/pam.d/common-session | head -3")
        sd, ex = t.split("---", 1)
        n_sd = [int(l.split(":")[0]) for l in sd.strip().splitlines() if l.strip()]
        n_ex = [int(l.split(":")[0]) for l in ex.strip().splitlines() if l.strip()]
        if not n_ex:
            return FAIL, "common-session has no pam_exec line of remotix-local-login (pam_systemd at line %s)" % (n_sd or "none")
        if not n_sd:
            raise ToolError("common-session has no pam_systemd line to compare with (pam_exec at line %d)" % n_ex[0])
        if n_ex[0] <= n_sd[0]:
            return FAIL, "pam_exec of remotix-local-login (line %d) is NOT after pam_systemd (line %d)" % (n_ex[0], n_sd[0])
        return PASS, "pam_systemd line %d, pam_exec remotix-local-login line %d (after it)" % (n_sd[0], n_ex[0])

    lib.guard((900 if old_sel else 0) + 700 * (len(sel) - len(old_sel)))
    try:
        if old_sel:
            try:
                try:
                    setup()
                except Exception as e:  # noqa: BLE001
                    why = str(e) if isinstance(e, Fail) else lib.tool_error(e)
                    for i, n in enumerate(old_sel):   # only the old cases: P7/P8 do not depend on this setup
                        res.say((FAIL if isinstance(e, Fail) else BLOCKED) if i == 0 else BLOCKED, n, why if i == 0 else "an earlier check stopped the run")
                else:
                    for name, fn in zip(OLD_NAMES, (p1, p2, p3, p4, p5, p6)):
                        if name in sel:
                            res.attempt(name, fn)
            finally:
                rig.stop()
                ctx.box.run("systemctl is-active --quiet remotix || systemctl start remotix; true", timeout=60)
        for name, user, kind in (("P7-busy-terminal", "pl3", "terminal"), ("P8-unsaved-editor", "pl4", "editor")):
            if name in sel:
                res.attempt(name, lambda u=user, k=kind: busy_case(a.box, u, k))
        return res.code()
    finally:
        lib.Box(a.box).run("systemctl is-active --quiet remotix || systemctl start remotix; true", timeout=60)


if __name__ == "__main__":
    sys.exit(main())
