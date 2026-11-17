#!/usr/bin/env python3
"""check-desktop - what must be true INSIDE a remote desktop session and about its canvas, with a real browser (SPECS 5.4, 5.5, 5.9 A-B,
6, 11.3).

    python3 check-desktop.py [--box xfce|lxqt|gnome|kde] [--only name,name] [--no-cap]

Runs ON THE DEV SERVER (see lib.py). One line per check: PASS|FAIL|BLOCKED <name> - evidence; exit 0 only if all PASS.
  FAIL = the product did not do it.  BLOCKED = the tool could not look.  Pictures go to <prove>/shots/desk-*.png.
Own users: dk1 (power, password windows, shell), dkfNN (settings: a NEW name each run, so the first start is a first start), dk5
(canvas), dk61 dk62 dk63 (session cap). Everything is looked at INSIDE the user's session: the commands run in the cgroup of the
session's logind scope and with the environment of the desktop's panel (deskkit.run_in), so logind and polkit see what the
desktop's own programs would be seen as.

  power-entries-absent         (5.9 A4, 11.3) logind CanPowerOff/CanReboot/CanHalt/CanSuspend/CanHibernate/CanHybridSleep as the user
                               say no; polkit (pkcheck) refuses the 15 login1 power actions; real `systemctl poweroff|reboot|halt|
                               suspend|hibernate|hybrid-sleep` attempts are refused and the box stays up; the desktop's own belts
                               (LXQt's lxqt-leave, XFCE's whisker buttons, GNOME's lock); a photo of the desktop's exit menu
  no-password-windows          (1.5.3) the system bus is watched for any polkit BeginAuthentication (= a password window) and the
                               user's bus for keyring/wallet prompts, from the login to 60 s after the desktop settled, with the file
                               manager and a terminal opened; pictures after each step
  users-shell-and-environment  (5.9 B) a terminal opened in the session runs the passwd shell; HOME USER LOGNAME SHELL XDG_RUNTIME_DIR
                               XDG_SESSION_TYPE=wayland, the user's bus answers, groups = a local login's, logind: an ACTIVE session of
                               class user, no seat, service remotix; sudo asks for a password; pkexec makes the agent ask (window), as
                               on a seated machine
  settings-intact              (uniform behaviour, D-017) a NEW user with settings of its own (power, lock, panel, theme), the file
                               writes of the whole home watched by fanotify (WHO wrote what), log in, use, Log Out, again: the user's
                               values are as before; a write by REMOTIX itself that stays is a FAIL, the desktop's own first-start
                               writes are listed and judged as not REMOTIX's
  canvas-limits                (6) browser views from 200x150 to 5120x2880, odd and extreme proportions, each by a reattach: the canvas is
                               what 6.1 says (multiple of 16 per side, 320x240..4096x2304), the desktop inside the box has that size, the
                               picture shows all of it (edges, quadrants), proportions kept, no band the spec does not promise
  reattach-windows-inside      (old F-018b) a 1800x1000 window born in a 3840x2160 canvas is entirely inside after a reattach at 2560x1440
                               and keeps its size
  session-cap                  (5.5) --session-cap 2 through a drop-in in the box (removed at the end, service restarted): the third
                               user is refused with the 0x0E sentence (DECISIONS-11 §11.46), the first two stay untouched. Needs a QUIET box"""
import argparse
import io
import json
import os
import re
import shlex
import sys
import time
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402
import deskkit as K  # noqa: E402
from lib import PASS, FAIL, BLOCKED, Fail, ToolError  # noqa: E402

PW = "dkpass2026"
NAMES = ("power-entries-absent", "no-password-windows", "users-shell-and-environment", "settings-intact", "canvas-limits",
         "reattach-windows-inside", "session-cap")
TERMINAL = {"xfce": "xfce4-terminal", "lxqt": "qterminal", "gnome": "gnome-terminal", "kde": "konsole"}
FILEMGR = {"xfce": "thunar", "lxqt": "pcmanfm-qt", "gnome": "nautilus", "kde": "dolphin"}
SHELLS = ("bash", "sh", "dash", "zsh", "fish")
POWER_ACTION = re.compile(r"^org\.freedesktop\.login1\.(power-off|reboot|halt|suspend|hibernate)(-multiple-sessions|-ignore-inhibit)?$")
STAMP = time.strftime("%y%m%d-%H%M%S")


def shot(name, png):
    return os.path.basename(lib.save_png("desk-%s-%s.png" % (name, STAMP), png))


def passwd_shell(box, user):
    return box.run("getent passwd %s | cut -d: -f7" % user)[1].strip()


# ----------------------------------------------------------------------------------------------------- 1. power entries
def sec_lines(text, tag):
    return [l[len(tag) + 1:] for l in text.splitlines() if l.startswith(tag + " ")]


POWER_SCRIPT = r"""
for k in CanPowerOff CanReboot CanHalt CanSuspend CanHibernate CanHybridSleep CanSuspendThenHibernate; do
  printf '@@can %s=' $k; busctl call org.freedesktop.login1 /org/freedesktop/login1 org.freedesktop.login1.Manager $k 2>&1 | tail -1; done
for a in $(pkaction | grep -E 'login1\.(power-off|reboot|halt|suspend|hibernate)'); do
  pkcheck --action-id $a --process $$ >/dev/null 2>&1; echo "@@pk $a=$?"; done
for v in poweroff reboot halt suspend hibernate hybrid-sleep; do
  out=$(timeout 25 systemctl --no-ask-password $v 2>&1); rc=$?; echo "@@try $v rc=$rc $(echo $out)"; done
"""


def judge_logind(v):
    """'ok' / 'unreadable' (container) / bad word."""
    if v in ('s "no"', 's "na"') or "Access denied" in v:
        return "ok"
    if "Read-only file system" in v or "not read" in v or v == "":
        return "unreadable"
    return v


def belts(rig, de, notes, bad):
    box, user = rig.box, rig.user
    if de == "lxqt":
        c, t = K.run_in(box, de, user, "echo PATH=$PATH; f=$(command -v lxqt-leave); echo F=$f; echo LOGOUT=$(grep -c -e '--logout' \"$f\"); "
                        "echo OTHER=$(grep -cE -e '--(lockscreen|suspend|hibernate|reboot|shutdown)' \"$f\")")
        path = (re.search(r"PATH=(\S+)", t) or [0, ""])[1]
        if "/remotix/bin-lxqt" not in path.split(":")[0]:
            bad.append("LXQt PATH does not start with the session's bin-lxqt: %s" % path[:80])
        if "LOGOUT=0" in t or "LOGOUT=" not in t:
            bad.append("the session's lxqt-leave is not a logout wrapper: %s" % t.replace("\n", " ")[-160:])
        running = box.run("ps -u %s -o comm= | grep -c '^lxqt-powermanag'; true" % user)[1].split()[0]
        notes.append("LXQt belt: PATH first folder %s, %s, lxqt-powermanagement processes: %s" % (
            path.split(":")[0], " ".join(x for x in t.split() if x.startswith(("F=", "LOGOUT=", "OTHER="))), running))
        if running != "0":
            bad.append("lxqt-powermanagement is running in the session (%s process(es))" % running)
    elif de == "xfce":
        c, t = K.run_in(box, de, user, "xfconf-query -c xfce4-panel -l -v 2>&1 | grep -iE 'whisker|actions' | head -8; "
                        "for pl in $(xfconf-query -c xfce4-panel -l -v 2>&1 | sed -n 's#^\\(/plugins/plugin-[0-9]*\\) *whiskermenu$#\\1#p'); do "
                        "for n in lockscreen switchuser suspend hibernate restart shutdown logout; do echo \"@@w $pl $n=$(xfconf-query -c xfce4-panel -p $pl/show-command-$n 2>&1)\"; done; done")
        w = [l for l in t.splitlines() if l.startswith("@@w ")]
        shown = [l[4:] for l in w if re.search(r"(lockscreen|switchuser|suspend|hibernate|restart|shutdown)=true", l)]
        notes.append("XFCE panel: %s" % (" | ".join(x.strip() for x in t.splitlines() if not x.startswith("@@w ")) or "no whisker/actions plugin line")[:160])
        if shown:
            bad.append("whisker menu shows power buttons: %s" % shown)
    elif de == "gnome":
        c, t = K.run_in(box, de, user, "gsettings get org.gnome.desktop.lockdown disable-lock-screen; gsettings get org.gnome.desktop.lockdown disable-log-out; "
                        "busctl --system list 2>/dev/null | grep -c '^org.gnome.DisplayManager '")
        notes.append("GNOME lockdown disable-lock-screen/disable-log-out/GDM on bus: %s" % " ".join(t.split()))
    else:
        notes.append("KDE: no extra belt read (the entries follow logind/polkit)")


def menu_photo(rig, de, notes):
    """A photo of the desktop's exit menu for the eyes of whoever reads the evidence; never judged by the tool."""
    g = rig.g
    L, T, W, H = rig.state()["rect"]
    try:
        if de == "xfce":
            K.run_in(rig.box, de, rig.user, "timeout 12 xfce4-session-logout", bg=True)
        elif de == "gnome":
            g.click(L + W - 30, T + 14)
        elif de == "kde":
            g.click(L + 28, T + H - 27)
        elif de == "lxqt":
            g.click(L + 14, T + H - 18)
        time.sleep(3)
        name = shot("power-menu-%s" % de, rig.canvas_png())
        notes.append("photo of the exit menu/dialog saved shots/%s (for the eyes, not judged by the tool)" % name)
        if de != "xfce":
            g.press("Escape")
        time.sleep(1)
    except Exception as e:  # noqa: BLE001
        notes.append("menu photo not taken: %s" % str(e)[:80])


def check_power(rig, de):
    box, user = rig.box, rig.user
    K.install(box)
    c, t = K.run_in(box, de, user, POWER_SCRIPT, timeout=200)
    if "NOANCHOR" in t:
        raise ToolError(t.strip())
    can = dict(x.split("=", 1) for x in sec_lines(t, "@@can") if "=" in x)
    pk = {x.split("=")[0]: int(x.split("=")[1]) for x in sec_lines(t, "@@pk") if re.match(r".*=\d+$", x)}
    tries = {}
    for x in sec_lines(t, "@@try"):
        v, _, rest = x.partition(" ")
        tries[v] = rest
    bad, notes = [], []
    for k in ("CanPowerOff", "CanReboot", "CanHalt", "CanSuspend", "CanHibernate", "CanHybridSleep", "CanSuspendThenHibernate"):
        j = judge_logind(can.get(k, "not read"))
        if j not in ("ok", "unreadable"):
            bad.append("logind %s=%s as the user (expected no)" % (k, j))
    unread = [k for k in can if judge_logind(can[k]) == "unreadable"]
    if unread:
        notes.append("logind cannot even answer %s in this container (%s): the polkit answers below are the proof for them" % (
            "/".join(k[3:] for k in unread), can[unread[0]][:40]))
    acts = {a: r for a, r in pk.items() if POWER_ACTION.match(a)}
    if len(acts) < 12:
        raise ToolError("pkcheck answered only %d power actions: %s" % (len(acts), t[-200:]))
    wrong = {a.replace("org.freedesktop.login1.", ""): r for a, r in acts.items() if r != 1}
    if wrong:
        bad.append("polkit does NOT refuse for the session user: %s (pkcheck rc 2 = asks an administrator's password = `challenge`, 0 = allowed)" %
                   ", ".join("%s rc=%d" % (a, r) for a, r in sorted(wrong.items())))
    for v in ("poweroff", "reboot", "halt", "suspend", "hibernate", "hybrid-sleep"):
        r = tries.get(v)
        if r is None:
            bad.append("systemctl %s: no result" % v)
        elif not re.search(r"rc=[1-9]", r):
            bad.append("systemctl %s by the user SUCCEEDED: %s" % (v, r[:90]))
    box_up = box.run("systemctl is-system-running; uptime -s")[1].replace("\n", " ")
    notes.append("attempts: " + " | ".join("%s: %s" % (v, tries.get(v, "?")[:70]) for v in ("poweroff", "reboot", "halt")))
    notes.append("box still up (%s)" % box_up)
    belts(rig, de, notes, bad)
    menu_photo(rig, de, notes)
    ev = "logind as the user %s; polkit refuses %d/%d power actions" % (" ".join("%s=%s" % (k[3:], can[k].replace('s "', '').replace('"', '')[:12]) for k in sorted(can)),
                                                                          sum(1 for r in acts.values() if r == 1), len(acts))
    if bad:
        return FAIL, "; ".join(bad) + " -- " + ev + "; " + "; ".join(notes)
    return PASS, ev + "; " + "; ".join(notes)


# ----------------------------------------------------------------------------------------------- 2. no password windows
def check_password_windows(rig, de, mon):
    """`mon` = the monitors started before the login (sysbus file) and after it (user bus file)."""
    box, user, g = rig.box, rig.user, rig.g
    pics = []
    t0 = time.time()
    d = rig.state()
    pics.append(("settled", shot("pw-1-settled-%s" % de, rig.canvas_png())))
    K.run_in(box, de, user, FILEMGR[de], bg=True)
    time.sleep(10)
    pics.append(("file manager", shot("pw-2-filemgr-%s" % de, rig.canvas_png())))
    K.run_in(box, de, user, TERMINAL[de], bg=True)
    time.sleep(10)
    pics.append(("terminal", shot("pw-3-terminal-%s" % de, rig.canvas_png())))
    # the unrequested windows of 1.5.3 came 20-40 s after login (DiscoverNotifier --check-delay 20, software centres): wait 60 s in all
    left = max(0, 60 - (time.time() - mon["t_settled"]))
    time.sleep(left)
    pics.append(("60 s after settling", shot("pw-4-late-%s" % de, rig.canvas_png())))
    sysb = box.run("grep -c 'BeginAuthentication' /tmp/rx-sysbus.txt; grep -B2 -A8 'BeginAuthentication' /tmp/rx-sysbus.txt | head -30; true")[1]
    nauth = int((sysb.splitlines() or ["0"])[0] or 0)
    usrb = box.run("grep -E 'member=(BeginPrompting|PerformPrompt|PromptReady|StopPrompting|CreateCollection)\\b|interface=org.freedesktop.Secret.Prompt; member=Prompt|interface=org.kde.KWallet; member=(open|openAsync|openPath|openPathAsync)\\b' /tmp/rx-userbus.txt | cut -c1-200 | head -8; wc -c < /tmp/rx-userbus.txt")[1]
    ulines = usrb.splitlines()
    size = ulines[-1].strip() if ulines else "?"
    hits = [l for l in ulines[:-1] if l.strip()]
    procs = box.run("ps -u %s -o comm= | grep -iE 'gcr-prompter|polkit.*(gnome|kde|lxqt|xfce|agent)|lxqt-policykit|kwalletd|gnome-keyring|ksecretd' | sort | uniq -c | tr '\\n' ' '; true" % user)[1]
    ev = ("polkit BeginAuthentication calls on the system bus: %d (a password window = at least one); keyring/wallet PROMPT calls (BeginPrompting/PerformPrompt/PromptReady, Secret Prompt, KWallet open) on the user's bus: %d (%s bytes watched); "
          "agents/keyring processes of the user: %s; pictures: %s" % (nauth, len(hits), size, procs.strip() or "none",
                                                                       ", ".join("%s=%s" % p for p in pics)))
    if "0" == size or size == "?":
        raise ToolError("the user's bus monitor recorded nothing (%s): the watch is blind" % size)
    if nauth or hits:
        return FAIL, ev + " | " + " ; ".join((sysb.splitlines()[1:6] + hits[:3]))[:420]
    return PASS, ev


# ------------------------------------------------------------------------------------- 3. users shell and environment
def check_shell(rig, de):
    box, user = rig.box, rig.user
    shell = passwd_shell(box, user)
    gnome_note = ""
    K.run_in(box, de, user, TERMINAL[de], bg=True)
    pid, tty = None, ""
    for _ in range(40):
        time.sleep(1)
        c, t = box.run("ps -u %s -o pid=,ppid=,comm=,tty= | awk '$4 ~ /pts/' | head -20" % user)
        rows = [l.split() for l in t.splitlines() if len(l.split()) >= 4]
        sh = [r for r in rows if r[2] in SHELLS]
        if sh:
            pid, tty = sh[0][0], sh[0][3]
            break
    if not pid:
        c, t = box.run("ps -u %s -o pid=,ppid=,comm=,tty=,args= | grep -iE '%s' | head -6; true" % (user, TERMINAL[de]))
        raise ToolError("%s opened no shell on a pts in 40 s: its processes: %s" % (TERMINAL[de], t.replace("\n", " | ")[:300]))
    time.sleep(2)
    c, t = box.run("p=%s; echo \"exe=$(ps -o comm= -p $p)\"; echo \"argv0=$(tr '\\0' ' ' < /proc/$p/cmdline | cut -c1-60)\"; echo \"cg=$(sed 's/^0:://' /proc/$p/cgroup)\"; "
                   "echo \"groups=$(sed -n 's/^Groups:[ \\t]*//p' /proc/$p/status)\"; echo \"uid=$(sed -n 's/^Uid:[ \\t]*\\([0-9]*\\).*/\\1/p' /proc/$p/status)\"; "
                   "tr '\\0' '\\n' < /proc/$p/environ | grep -E '^(HOME|USER|LOGNAME|SHELL|XDG_RUNTIME_DIR|XDG_SESSION_TYPE|XDG_SESSION_ID|XDG_SESSION_CLASS|XDG_SEAT|DBUS_SESSION_BUS_ADDRESS|WAYLAND_DISPLAY|XDG_CURRENT_DESKTOP|LANG|PATH)='" % pid)
    f = {}
    for l in t.splitlines():
        k, _, v = l.partition("=")
        f[k] = v
    uid = box.run("id -u %s" % user)[1].strip()
    want_groups = sorted(box.run("id -G %s" % user)[1].split())
    got_groups = sorted(f.get("groups", "").split())
    bad = []
    exe = f.get("argv0", "").split()[0].lstrip("-") if f.get("argv0", "").split() else f.get("exe", "")
    if os.path.basename(exe) != os.path.basename(shell):
        bad.append("the terminal's shell is %s, passwd says %s" % (exe, shell))
    for k, want in (("HOME", "/home/%s" % user), ("USER", user), ("XDG_RUNTIME_DIR", "/run/user/%s" % uid), ("XDG_SESSION_TYPE", "wayland")):
        if f.get(k) != want:
            bad.append("%s=%s (expected %s)" % (k, f.get(k), want))
    absent = [k for k in ("LOGNAME", "XDG_SESSION_ID", "XDG_SESSION_CLASS") if k not in f]
    absent_note = (" NOTE not in the shell's environment (the spec 5.9 B does not list them; a text-console login has them): %s." % ", ".join(absent)) if absent else ""
    if de != "gnome" and f.get("SHELL") != shell:
        bad.append("SHELL=%s (expected %s)" % (f.get("SHELL"), shell))
    if de == "gnome" and f.get("SHELL") not in (shell, ""):
        bad.append("SHELL=%s" % f.get("SHELL"))
    if f.get("uid") != uid:
        bad.append("the shell runs as uid %s, not %s" % (f.get("uid"), uid))
    if got_groups != want_groups:
        bad.append("the shell's groups %s differ from a local login's `id -G` %s" % (got_groups, want_groups))
    names = box.run("for g in %s; do getent group $g | cut -d: -f1; done | tr '\\n' ' '" % " ".join(got_groups))[1].strip()
    if not all(x in names.split() for x in ("video", "render")):
        bad.append("the GPU groups (video, render) are not both in the shell's groups: %s" % names)
    if "/user.slice/user-%s.slice" % uid not in f.get("cg", ""):
        bad.append("the shell is not under the user's slice: %s" % f.get("cg"))
    # the user's session bus answers
    c, t = K.run_in(box, de, user, "busctl --user list --no-legend 2>&1 | wc -l; echo TYPE=$XDG_SESSION_TYPE", timeout=30)
    n_names = (t.split() or ["0"])[0]
    if not n_names.isdigit() or int(n_names) < 3:
        bad.append("the user's D-Bus session bus does not answer (%s)" % t.replace("\n", " ")[:80])
    # logind
    c, t = box.run("for s in $(loginctl list-sessions --no-legend | awk -v u=%s '$3==u{print $1}'); do echo \"@@ $(loginctl show-session $s -p Id -p Class -p State -p Active -p Type -p Seat -p Remote -p Service | tr '\\n' ' ')\"; done" % user)
    ses = [l[3:].strip() for l in t.splitlines() if l.startswith("@@")]
    mine = [s for s in ses if "Class=user" in s]
    if len(mine) != 1:
        bad.append("logind: %d sessions of class user for %s (%s)" % (len(mine), user, ses))
    else:
        m = mine[0]
        for need in ("State=active", "Active=yes", "Type=wayland", "Service=remotix"):
            if need not in m:
                bad.append("logind session lacks %s: %s" % (need, m))
        if re.search(r"Seat=\S", m):
            bad.append("the session has a seat: %s" % m)
    # sudo
    c, t = K.run_in(box, de, user, "sudo -n true 2>&1; echo rc=$?", timeout=30)
    sudo = t.replace("\n", " ")[:100]
    if "rc=0" in t or "password" not in t and "not in the sudoers" not in t:
        bad.append("sudo -n by the plain user: %s (expected: refused / password required)" % sudo)
    # pkexec: the agent must ask (BeginAuthentication) - never answered, killed after 8 s
    have_pkexec = box.run("command -v pkexec >/dev/null && echo yes")[1].strip() == "yes"
    if not have_pkexec:
        asked, pk, t = "-", "pkexec is not installed in this box's image (container limit, not the product)", ""
        pic = "-"
    else:
        box.run("pkill -f '[b]usctl --system monitor'; true")
        box.run("rm -f /tmp/rx-pkexec.txt; setsid nohup busctl --system monitor --match \"interface=org.freedesktop.PolicyKit1.AuthenticationAgent\" </dev/null >/tmp/rx-pkexec.txt 2>&1 & sleep 1; true")
        c, t = K.run_in(box, de, user, "timeout 8 pkexec true </dev/null 2>&1; echo rc=$?", timeout=30)
        time.sleep(1)
        asked = box.run("grep -c BeginAuthentication /tmp/rx-pkexec.txt; true")[1].split()[0]
        box.run("pkill -f '[b]usctl --system monitor'; true")
        pk = t.replace("\n", " ")[:100]
        pic = shot("shell-pkexec-%s" % de, rig.canvas_png())
        K.run_in(box, de, user, "pkill -x pkexec; true", timeout=20)
        if "rc=0" in t:
            bad.append("pkexec by the plain user SUCCEEDED")
    ev = ("terminal %s -> %s (pid %s on %s, argv %s), HOME=%s USER=%s SHELL=%s XDG_RUNTIME_DIR=%s XDG_SESSION_TYPE=%s XDG_SESSION_ID=%s, groups %s (= local `id -G`: %s), bus names %s, logind %s, "
          "sudo: %s, pkexec: agent asked %s time(s) (%s; picture %s)." % (
              TERMINAL[de], exe, pid, tty, f.get("argv0", "").strip(), f.get("HOME"), f.get("USER"), f.get("SHELL"), f.get("XDG_RUNTIME_DIR"),
              f.get("XDG_SESSION_TYPE"), f.get("XDG_SESSION_ID"), names, got_groups == want_groups, n_names, mine[0] if mine else ses, sudo, asked, pk, pic))
    if have_pkexec and asked == "0" and "rc=0" not in t:
        bad.append("pkexec by the plain user made no password window (polkit BeginAuthentication 0 times): %s" % pk)
    ev += absent_note
    return (FAIL, "; ".join(bad) + " -- " + ev) if bad else (PASS, ev)


# ------------------------------------------------------------------------------------------------- 4. settings intact
SEED = {
    "common": {".config/rx-dk/sentinel.conf": "[Mine]\nkeep=this\n", ".cache/sessions/rx-dk-sentinel": "sentinel\n"},
    "lxqt": {".config/lxqt/lxqt.conf": "[General]\nicon_theme=oxygen\n\n[Screensaver]\nlock_command_wayland=swaylock\n",
             ".config/lxqt/session.conf": "[General]\nlock_command_wayland=swaylock\n",
             ".config/lxqt/lxqt-powermanagement.conf": "[General]\nenableIdlenessWatcher=true\nrunCheckLevel=3\nidlenessTimeSecs=600\n"},
    "xfce": {".config/xfce4/xfconf/xfce-perchannel-xml/xfce4-session.xml":
             '<?xml version="1.0" encoding="UTF-8"?>\n<channel name="xfce4-session" version="1.0">\n  <property name="shutdown" type="empty">\n'
             '    <property name="ShowSuspend" type="bool" value="true"/>\n    <property name="ShowHibernate" type="bool" value="true"/>\n  </property>\n'
             '  <property name="general" type="empty">\n    <property name="SaveOnExit" type="bool" value="false"/>\n  </property>\n</channel>\n',
             ".config/xfce4/xfconf/xfce-perchannel-xml/xfce4-power-manager.xml":
             '<?xml version="1.0" encoding="UTF-8"?>\n<channel name="xfce4-power-manager" version="1.0">\n  <property name="xfce4-power-manager" type="empty">\n'
             '    <property name="inactivity-on-ac" type="uint" value="14"/>\n    <property name="lock-screen-suspend-hibernate" type="bool" value="true"/>\n'
             '    <property name="dpms-enabled" type="bool" value="true"/>\n  </property>\n</channel>\n'},
    "kde": {".config/kdeglobals": "[General]\nColorScheme=BreezeDark\n",
            ".config/kwinrc": "[org.kde.kdecoration2]\nBorderSize=Tiny\nBorderSizeAuto=false\n",
            ".config/kxkbrc": "[Layout]\nUse=false\n",
            ".config/ksmserverrc": "[General]\nloginMode=restorePreviousLogout\n",
            ".config/kscreenlockerrc": "[Daemon]\nAutolock=true\nTimeout=10\n",
            ".config/powerdevilrc": "[AC][SuspendAndShutdown]\nAutoSuspendAction=1\n",
            ".config/kglobalshortcutsrc": "[ksmserver]\nLock Session=Ctrl+Alt+L,none,Lock Session\n"},
    "gnome": {},
}
DCONF_SEED = [("org/gnome/desktop/interface", "gtk-theme", "'Adwaita-dark'"), ("org/gnome/desktop/session", "idle-delay", "uint32 300"),
              ("org/gnome/settings-daemon/plugins/power", "sleep-inactive-ac-type", "'suspend'"),
              ("org/gnome/desktop/screensaver", "lock-enabled", "true"), ("org/gnome/shell", "always-show-log-out", "false")]
VOLATILE = re.compile(r"^\./(\.cache/(?!sessions)|\.local/state/|\.local/share/(Trash|recently-used|gvfs-metadata|xorg|gnome-shell/session)|\.config/pulse|\.dbus|"
                      r"\.ICEauthority|\.Xauthority|\.xsession-errors|\.config/dconf/user|\.local/share/applications/mimeinfo|\.config/session/|\.config/Trolltech)")
SNAP = "cd /home/%s 2>/dev/null && find . -xdev -type f -print0 | xargs -0 -r sha256sum | sed 's/^\\([0-9a-f]*\\) *\\(.*\\)$/\\2\\t\\1/'"


def snapshot(box, user):
    t = box.run(SNAP % user, timeout=120)[1]
    d = {}
    for l in t.splitlines():
        p, _, h = l.partition("\t")
        if p and not VOLATILE.match(p):
            d[p] = h
    return d


def kv(text):
    """key-value map of an ini/QSettings or xfconf-xml text: 'section/key' -> value."""
    out = {}
    if text.lstrip().startswith("<?xml"):
        try:
            def walk(e, path):
                for c in e.findall("property"):
                    p = path + "/" + c.get("name")
                    if c.get("value") is not None:
                        out[p] = c.get("value")
                    walk(c, p)
            walk(ET.fromstring(text), "")
        except ET.ParseError:
            pass
        return out
    sec = ""
    for l in text.splitlines():
        l = l.strip()
        if l.startswith("[") and l.endswith("]"):
            sec = l[1:-1]
        elif "=" in l and not l.startswith(("#", ";")):
            k, _, v = l.partition("=")
            out["%s/%s" % (sec, k.strip())] = v.strip()
    return out


def cat(box, user, rel):
    return box.run("cat /home/%s/%s 2>/dev/null; true" % (user, rel))[1]


def dconf_dump(box, user):
    return box.run("runuser -u %s -- env HOME=/home/%s dconf dump / 2>/dev/null; true" % (user, user))[1]


def dconf_kv(text):
    out, sec = {}, ""
    for l in text.splitlines():
        if l.startswith("["):
            sec = l.strip("[]")
        elif "=" in l:
            k, _, v = l.partition("=")
            out["%s/%s" % (sec, k)] = v
    return out


def seed_user(box, user, de):
    files = dict(SEED["common"])
    files.update(SEED[de])
    script = ["set -e", "cd /home/%s" % user]
    for rel, content in files.items():
        script.append("mkdir -p %s; cat > %s <<'EOF_RX'\n%sEOF_RX" % (shlex.quote(os.path.dirname(rel)), shlex.quote(rel), content))
    if de == "lxqt":
        script.append("mkdir -p .config/lxqt; cp /usr/share/lxqt/panel.conf .config/lxqt/panel.conf")
    if de == "gnome":
        f = "/tmp/rx-dconf-seed-%s.sh" % user
        script.append("cat > %s <<'EOF_RX'\n%s\nsleep 1\nEOF_RX\ndbus-run-session -- bash %s; rm -f %s" % (
            f, "\n".join("dconf write /%s/%s %s" % (p, k, shlex.quote(v)) for p, k, v in DCONF_SEED), f, f))
    c, t = box.run("runuser -u %s -- bash -c %s" % (user, shlex.quote("\n".join(script))), timeout=60)
    if c:
        raise ToolError("cannot seed the settings of %s: %s" % (user, t[-150:]))
    return files


def new_user(box):
    for n in range(10, 60):
        u = "dkf%d" % n
        if box.run("id -u %s >/dev/null 2>&1 && echo yes; true" % u)[1].strip() != "yes":
            return u
    raise ToolError("no free dkfNN name in the box")


def logout_and_wait(rig, de, user, cap=70):
    """The desktop's own Log Out in the session, then wait until nothing of the user is left. Returns seconds."""
    box = rig.box
    t0 = time.time()
    K.run_in(box, de, user, "timeout 60 %s; echo rc=$?" % K.LOGOUT[de], bg=True)
    end = time.time() + cap
    while time.time() < end:
        c, t = box.run("echo \"$(pgrep -u %s | grep -vc '^$')\"; loginctl list-sessions --no-legend | awk -v u=%s '$3==u' | wc -l" % (user, user))
        a = t.split()
        if len(a) >= 2 and a[0] == "0" and a[1] == "0":
            return time.time() - t0, True
        time.sleep(2)
    return time.time() - t0, False


def one_session(rig, de, use=True):
    rig.open_page()
    ok, s = rig.try_login(real=True, retry=40)
    if not ok:
        raise Fail("login of %s not admitted: %s" % (rig.user, (s.get("outcome") or "").strip()))
    d = rig.settle(rig.cap)
    if use:
        K.run_in(rig.box, de, rig.user, FILEMGR[de], bg=True)
        time.sleep(6)
        K.run_in(rig.box, de, rig.user, TERMINAL[de], bg=True)
        time.sleep(8)
    time.sleep(12)
    return d


def check_settings(rig, de, a):
    box = rig.box
    user = new_user(box)
    rig.user = user
    box.ensure_user(user, PW)
    seeded = seed_user(box, user, de)
    sys_panel = box.run("cat /usr/share/lxqt/panel.conf 2>/dev/null")[1] if de == "lxqt" else ""
    if de == "lxqt":
        seeded[".config/lxqt/panel.conf"] = sys_panel
    before = snapshot(box, user)
    dconf0 = dconf_kv(dconf_dump(box, user)) if de == "gnome" else {}
    K.fan_start(box, "/home/%s" % user)
    notes, bad = [], []
    try:
        ensure_browser(rig)
        one_session(rig, de)
        shot("settings-1-%s" % de, rig.canvas_png())
        secs, gone = logout_and_wait(rig, de, user)
        if not gone:
            raise Fail("Log Out did not end the session of %s in %.0f s (processes or logind session left)" % (user, secs))
        notes.append("session 1 ended %.0f s after Log Out" % secs)
        mid = snapshot(box, user)
        one_session(rig, de, use=False)
        secs2, gone2 = logout_and_wait(rig, de, user)
        if not gone2:
            raise Fail("Log Out of the second session did not end it in %.0f s" % secs2)
        after = snapshot(box, user)
        rows = K.fan_stop(box)
    except BaseException:
        K.fan_stop(box)
        raise

    def writers(rel):
        d = "/home/%s/%s" % (user, os.path.dirname(rel) if os.path.dirname(rel) else "")
        return sorted({r[2] for r in rows if r[3] == "W" and (r[4].startswith(d + "/") or r[4] == d)} - {"gone"})
    rx = lambda comms: [c for c in comms if c.startswith("remotix")]  # noqa: E731
    # 1. sentinels and every seeded file still there
    for rel in seeded:
        if ("./" + rel) not in after:
            bad.append("the user's file %s is GONE after the sessions" % rel)
    # 2. seeded keys keep their values
    changed, same = [], 0
    for rel, want in seeded.items():
        got = cat(box, user, rel)
        if want is None:
            continue
        w, g_ = kv(want), kv(got)
        for k, v in w.items():
            if g_.get(k) != v:
                changed.append((rel, k, v, g_.get(k)))
            else:
                same += 1
    if de == "gnome":
        d1 = dconf_kv(dconf_dump(box, user))
        for p, k, v in DCONF_SEED:
            key = "%s/%s" % (p, k)
            want = v
            got = d1.get(key)
            if got is None:
                changed.append(("dconf", key, v, None))
            elif got != want:
                changed.append(("dconf", key, v, got))
            else:
                same += 1
        newkeys = sorted(set(d1) - set(dconf0))
        notes.append("dconf: %d new key(s) by the desktop/session: %s" % (len(newkeys), ", ".join(newkeys)[:200] or "none"))
    for rel, k, v, g_ in changed:
        w = writers(rel)
        if rx(w):
            bad.append("%s [%s] was %s now %s, and REMOTIX itself wrote in that folder (%s)" % (rel, k, v, g_, ",".join(w)))
        else:
            notes.append("%s [%s] %s -> %s: written by the desktop's own %s, not by REMOTIX" % (rel, k, v, g_, ",".join(w) or "(writer not seen)"))
    # 3. what REMOTIX itself wrote in the user's home outside its own state folder
    own = sorted({r[4].replace("/home/%s/" % user, "") for r in rows if r[2].startswith("remotix") and r[3] == "W"})
    own = [p for p in own if not p.startswith(".local/state/remotix") and "(deleted)" not in p]
    left = [p for p in own if ("./" + p) in after and ("./" + p) not in before or (("./" + p) in after and ("./" + p) in before and before[("./" + p)] != after[("./" + p)])]
    if left:
        bad.append("REMOTIX wrote and LEFT in the user's home: %s" % left[:6])
    cache = [p for p in own if p.startswith((".cache/", ".local/state/"))]
    other = [p for p in own if p not in cache and p not in left]
    if cache:
        notes.append("REMOTIX's own process wrote caches (not settings): %s" % ", ".join(cache[:4]))
    if other:
        notes.append("REMOTIX wrote and the file is back to the original: %s" % other[:6])
    # 4. the second session changes nothing the first had settled
    diff2 = sorted(p for p in set(mid) | set(after) if mid.get(p) != after.get(p))
    d2rx = [p for p in diff2 if rx(writers(p[2:]))]
    if d2rx:
        bad.append("the second session changed files after the first had settled, and REMOTIX wrote there: %s" % d2rx[:5])
    new_files = sorted(p for p in after if p not in before)
    chg_files = sorted(p for p in after if p in before and before[p] != after[p])
    who = {}
    for p in new_files + chg_files:
        for c in writers(p[2:]):
            who[c] = who.get(c, 0) + 1
    notes.append("%d new files and %d changed files in the home after two sessions (writers by name: %s); second session changed %d file(s)" % (
        len(new_files), len(chg_files), ", ".join("%s %d" % kvp for kvp in sorted(who.items(), key=lambda x: -x[1])[:6]) or "none", len(diff2)))
    if chg_files:
        notes.append("files of the seed the desktop rewrote: %s" % ", ".join(p[2:] for p in chg_files if p[2:] in seeded)[:260])
    # 5. nothing of REMOTIX left in the user manager
    um = box.run("id=$(id -u %s); systemctl is-active user@$id.service 2>&1; ls /run/user/$id/systemd/user.control ~%s/.config/systemd/user 2>&1 | head -5; "
                 "systemctl --user -M $id@ show-environment 2>&1 | grep -iE 'remotix|DCONF_PROFILE' | head -3; true" % (user, user))[1]
    if re.search(r"remotix|DCONF_PROFILE", um.split("\n", 1)[-1], re.I):
        bad.append("REMOTIX marks left in the user manager after Log Out: %s" % um.replace("\n", " ")[:160])
    notes.append("user manager after Log Out: %s" % um.replace("\n", " ")[:80])
    ev = "user %s, %d seeded value(s) intact, %d changed by the desktop; %s" % (user, same, len(changed), "; ".join(notes))
    return (FAIL, "; ".join(bad) + " -- " + ev) if bad else (PASS, ev)


# ------------------------------------------------------------------------------------------------------ 5. canvas limits
def expect_canvas(w, h):
    p = lambda n, lo, hi: max(lo, min(hi, int(round(n)))) // 16 * 16  # noqa: E731
    return p(w, 320, 4096), p(h, 240, 2304)


def px(png, x, y):
    from PIL import Image
    return Image.open(io.BytesIO(png)).convert("RGB").getpixel((int(x), int(y)))


def near(c, ref, tol=70):
    return sum(abs(c[i] - ref[i]) for i in range(3)) < tol


FRAME_REFS = {"red": (209, 31, 31), "green": (31, 179, 31), "blue": (31, 31, 209), "yellow": (230, 217, 26), "white": (255, 255, 255)}


def look_frame(png):
    """What the picture of the frame window shows: the four quadrant centres and the four edge middles."""
    from PIL import Image
    im = Image.open(io.BytesIO(png))
    w, h = im.size
    q = [px(png, w * .25, h * .25), px(png, w * .75, h * .25), px(png, w * .25, h * .75), px(png, w * .75, h * .75)]
    e = [px(png, w * .5, 1.5), px(png, w * .5, h - 2.5), px(png, 1.5, h * .25), px(png, w - 2.5, h * .25)]
    ok_q = all(near(c, FRAME_REFS[n]) for c, n in zip(q, ("red", "green", "blue", "yellow")))
    # an edge can be softened by a rescale: the white frame must at least be much lighter than the quadrant next to it
    ok_e = all(sum(c) > 560 for c in e)
    return ok_q, ok_e, (w, h)


def ensure_browser(rig):
    if rig.g:
        rig.g.close()
        rig.g = None
    if rig.env is None:
        rig.start(make_user=False)
    else:
        rig.new_browser()


def reattach_at(rig, size, tag):
    """Close the browser (detach) and come back with a view of `size`; returns the settled facts."""
    if rig.g:
        rig.g.close()
        rig.g = None
    time.sleep(3)
    ensure_browser(rig)
    rig.g.call("Emulation.setDeviceMetricsOverride", width=size[0], height=size[1], deviceScaleFactor=1, mobile=False)
    rig.open_page()
    ok, s = rig.try_login(retry=60)
    if not ok:
        raise Fail("reattach with a view of %dx%d: user not admitted: \"%s\"" % (size[0], size[1], (s.get("outcome") or "").strip()))
    return s


def settle_view(rig, cap=40):
    end, s = time.time() + cap, {}
    while time.time() < end:
        s = rig.state()
        if s.get("painted", 0) >= 1 and s.get("rect") and s["rect"][2] > 2:  # a still desktop sends one keyframe at the attach and nothing after
            time.sleep(3)
            return rig.state()
        time.sleep(0.5)
    raise Fail("no decoded frame / no canvas rectangle in %d s (painted=%s)" % (cap, s.get("painted")))


def check_canvas(rig, de):
    box = rig.box
    sizes = [(1280, 720), (200, 150), (320, 240), (1001, 701), (3000, 300), (400, 2000), (3840, 2160), (4096, 2304), (5120, 2880), (5120, 1440)]
    rig.user = "dk5"
    box.ensure_user("dk5", PW)
    ensure_browser(rig)
    rig.g.call("Emulation.setDeviceMetricsOverride", width=sizes[0][0], height=sizes[0][1], deviceScaleFactor=1, mobile=False)
    rig.open_page()
    rig.login(real=False)
    rig.settle(rig.cap, still=2)
    box.run("rm -f /tmp/rx-geom.log; true")
    box.run("pkill -u dk5 -f geom-window; true")
    K.put(box, "geom-window.py", "/tmp/rx-geom-window.py")
    box.in_session("dk5", "python3 /tmp/rx-geom-window.py frame /tmp/rx-geom.log 2>/tmp/rx-geom.err")
    time.sleep(6)
    rows, bad = [], []
    for i, (vw, vh) in enumerate(sizes):
        try:
            if i:
                reattach_at(rig, (vw, vh), "c%d" % i)
            s = settle_view(rig)
        except Fail as e:
            msg = "view %dx%d: %s [remotix journal: %s]" % (vw, vh, e, box.journal("dk5|canvas|FIT_CANVAS|REFUSED|beyond", since="-2min", n=4))
            print("NOTE canvas-limits " + msg[:400], flush=True)
            rows.append(msg)
            bad.append("%dx%d: %s" % (vw, vh, e))
            continue
        time.sleep(4)
        s = rig.state()
        vcw, vch = rig.g.js("const d=document.documentElement; return [d.clientWidth, d.clientHeight, innerWidth, innerHeight];")[:2]
        ex = expect_canvas(vcw, vch)
        page_c = tuple(rig.g.js("const v=document.getElementById('viewer'); return [v.width, v.height];"))  # the canvas buffer the page decodes into
        sz = [json.loads(l) for l in box.run("grep '\"size\"' /tmp/rx-geom.log | tail -3")[1].splitlines() if l.startswith("{")]
        inbox = (sz[-1]["w"], sz[-1]["h"]) if sz else None
        rect = s["rect"]
        scale = min(1.0, vcw / ex[0], vch / ex[1])
        png = rig.canvas_png()
        ok_q, ok_e, pic = look_frame(png)
        line = "view %dx%d (page client area %dx%d) -> canvas expected %dx%d, page says %s, desktop inside the box %s, viewer %.0fx%.0f (expected %.0fx%.0f at scale %.2f), picture %dx%d quadrants %s edges %s" % (
            vw, vh, vcw, vch, ex[0], ex[1], page_c, inbox, rect[2], rect[3], ex[0] * scale, ex[1] * scale, scale, pic[0], pic[1], "ok" if ok_q else "WRONG", "ok" if ok_e else "WRONG")
        pn = shot("canvas-%dx%d-%s" % (vw, vh, de), png) if (not ok_q or not ok_e or i in (0, 1, 7, 8)) else ""
        problems = []
        if page_c != ex:
            problems.append("page canvas %s != %s" % (page_c, ex))
        if inbox != ex:
            problems.append("desktop size inside the box %s != %s" % (inbox, ex))
        if abs(rect[2] - ex[0] * scale) > max(3, ex[0] * scale * 0.02) or abs(rect[3] - ex[1] * scale) > max(3, ex[1] * scale * 0.02):
            problems.append("viewer rectangle %.0fx%.0f is not the canvas at scale %.2f (%.0fx%.0f): bands or stretch the spec does not promise" % (
                rect[2], rect[3], scale, ex[0] * scale, ex[1] * scale))
        if not ok_q:
            problems.append("the four quadrant colours are not where they must be (half picture / shifted)")
        if not ok_e:
            problems.append("the white frame is not on all four edges (a cut picture)")
        print("NOTE canvas-limits " + line[:300], flush=True)
        rows.append(line + (" -- " + "; ".join(problems) + (" [shots/%s]" % pn if pn else "") if problems else ""))
        if problems:
            bad.append("%dx%d: %s" % (vw, vh, "; ".join(problems)))
    jr = box.run("journalctl -u remotix --no-pager -o cat --since '-15min' | grep -iE 'DECLARED FALLBACK|beyond the maximum' | tail -3 | cut -c1-200")[1].replace("\n", " | ")
    ms = (rig.g.js("return ((document.getElementById('logbook')||{}).textContent||'').split('\\n').filter(l=>/max_size|video probe · size/.test(l)).slice(-2).join(' | ')") or "")[:260]
    ev = " || ".join(rows) + (" || journal: " + jr if jr else "") + (" || page log: " + ms if ms else "") + (" || LADDER NOTE: the ceiling is not the browser's decoder: the page's own size ladder (src/page.html:1503-1507, MEASURE_PROBES, last rung l:3840 a:2160) never probes anything above 3840x2160, so 4096x2304 is unreachable with ANY client" if any(r.startswith("view 4096x2304") and "3840, 2160" in r for r in rows) else "")
    return (FAIL, "; ".join(bad) + " -- " + ev) if bad else (PASS, ev)


def bbox(png, rgb=(0, 255, 255), tol=90):
    """Bounding box (x0,y0,x1,y1) of the pixels near rgb in a picture, found on a 1/2 reduction (None if absent)."""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    w, h = im.size
    small = im.resize((w // 2, h // 2))
    xs, ys = [], []
    data = small.load()
    for y in range(small.height):
        for x in range(small.width):
            p = data[x, y]
            if sum(abs(p[i] - rgb[i]) for i in range(3)) < tol:
                xs.append(x)
                ys.append(y)
    if len(xs) < 50:
        return None
    return (min(xs) * 2, min(ys) * 2, max(xs) * 2 + 1, max(ys) * 2 + 1)


def check_reattach_inside(rig, de):
    box = rig.box
    rig.user = "dk5"
    # a fresh scene: the frame window of the canvas check is closed, the 1800x1000 window opened at 3840x2160
    box.run("pkill -u dk5 -f geom-window; rm -f /tmp/rx-geom2.log; true")
    reattach_at(rig, (3840, 2160), "r1")
    settle_view(rig)
    K.put(box, "geom-window.py", "/tmp/rx-geom-window.py")
    box.in_session("dk5", "python3 /tmp/rx-geom-window.py scene /tmp/rx-geom2.log 2>/tmp/rx-geom2.err")
    for _ in range(30):
        time.sleep(1)
        if '"ready"' in box.run("cat /tmp/rx-geom2.log 2>/dev/null; true")[1]:
            break
    time.sleep(4)
    s = rig.state()
    png1 = rig.canvas_png()
    b1 = bbox(png1)
    if not b1:
        raise Fail("at 3840x2160 the 1800x1000 window is not seen in the picture (cyan not found)")
    w1, h1 = b1[2] - b1[0], b1[3] - b1[1]
    c1 = tuple(rig.g.js("const v=document.getElementById('viewer'); return [v.width, v.height];"))
    shot("reattach-1-3840-%s" % de, png1)
    if not (b1[2] > 2559 or b1[3] > 1439):
        raise ToolError("the scene is not discriminating: at 3840x2160 the window sits at %s, so it would fit in 2560x1440 without any move" % (b1,))
    reattach_at(rig, (2560, 1440), "r2")
    settle_view(rig)
    end, b2, png2 = time.time() + 20, None, None
    while time.time() < end:  # the desktop may need a moment to bring the window back
        png2 = rig.canvas_png()
        b2 = bbox(png2)
        if b2 and b2[0] >= 0 and b2[1] >= 0:
            time.sleep(2)
            png2 = rig.canvas_png()
            b2 = bbox(png2)
            break
        time.sleep(1.5)
    c2 = tuple(rig.g.js("const v=document.getElementById('viewer'); return [v.width, v.height];"))
    pn = shot("reattach-2-2560-%s" % de, png2)
    if not b2:
        return FAIL, "after the reattach at 2560x1440 (canvas %s) the 1800x1000 window is not seen at all (was %dx%d in canvas %s): shots/%s" % (c2, w1, h1, c1, pn)
    w2, h2 = b2[2] - b2[0], b2[3] - b2[1]
    W2, H2 = rig.state()["rect"][2:]
    cut_r = png2_size(png2)[0] - 1 - b2[2]
    cut_b = png2_size(png2)[1] - 1 - b2[3]
    same = abs(w2 - w1) <= 0.03 * w1 and abs(h2 - h1) <= 0.03 * h1
    ev = ("canvas %s -> %s; the window was %dx%d at %s, after the smaller reattach it is %dx%d at %s in a picture of %dx%d (distance to right/bottom edge %d/%d px); shots/%s"
          % (c1, c2, w1, h1, b1[:2], w2, h2, b2[:2], png2_size(png2)[0], png2_size(png2)[1], cut_r, cut_b, pn))
    if not same:
        return FAIL, "the window is cut by the edge or shrunk (a moved window keeps its size): " + ev
    return PASS, ev + " (entirely inside, same size +-3%)"


def png2_size(png):
    from PIL import Image
    return Image.open(io.BytesIO(png)).size


# ------------------------------------------------------------------------------------------------------ 6. session cap
CAP_FILE = "/etc/remotix/remotix.conf.d/99-dk-cap.conf"


def wait_port(box, de, cap=60):
    import socket
    end = time.time() + cap
    while time.time() < end:
        try:
            socket.create_connection(("127.0.0.1", lib.PORTS[de]), timeout=3).close()
            return True
        except OSError:
            time.sleep(2)
    return False


def check_cap(rig, de, a):
    box = rig.box
    others = K.other_checks(de)
    if others:
        raise ToolError("the box is not quiet: another check runs on %s (%s); the service is not restarted" % (de, others[0]))
    if rig.g:
        rig.g.close()
        rig.g = None
    box.run("pkill -u dk5 -f geom-window; true")
    rig.box.end_users(["dk1", "dk5"])
    opts = box.run("cat /etc/remotix/remotix.conf.d/*.conf /usr/share/remotix/remotix.conf 2>/dev/null | grep '^REMOTIX_OPTIONS=' | tail -1 | cut -d= -f2-")[1].strip()
    users = ["dk61", "dk62", "dk63"]
    for u in users:
        box.ensure_user(u, PW)
    clients, bad, notes = [], [], []
    try:
        box.run("printf 'REMOTIX_OPTIONS=%s --session-cap 2\\n' > %s; systemctl restart remotix; true" % (opts, CAP_FILE))
        if not wait_port(box, de):
            raise Fail("the service does not answer 60 s after the restart with --session-cap 2")
        time.sleep(3)
        for i, u in enumerate(users):
            r = lib.Rig(de, "chrome", u, PW, "cap%d" % i, cap=a.cap)
            clients.append(r)
            r.start(make_user=False)
            r.open_page()
            ok, s = r.try_login(retry=0)
            if i < 2:
                if not ok:
                    raise Fail("user %s (number %d of 2) refused with cap 2: \"%s\"" % (u, i + 1, (s.get("outcome") or "").strip()))
                r.settle(a.cap)
            else:
                out = (s.get("outcome") or "").strip()
                if ok:
                    bad.append("the third user %s was ADMITTED with --session-cap 2" % u)
                # the cap answers 0x0E with its generic sentence ON PURPOSE (DECISIONS-11 §11.46, RCP §8.2: the detail
                # «all the stages … in use» is for the log, never for the page); 0x06 is the BUDGET, a different limit
                elif not re.search(r"could not open your session", out):
                    bad.append("the third user was refused, but not with the 0x0E sentence: \"%s\"" % out[:160])
                notes.append("third user: \"%s\"" % out[:200])
        # the first two are untouched: still attached, desktop still alive and painting
        for r in clients[:2]:
            s0 = r.state()
            time.sleep(4)
            s1 = r.state()
            alive = box.run("pgrep -u %s -c . ; loginctl list-sessions --no-legend | awk -v u=%s '$3==u' | wc -l" % (r.user, r.user))[1].split()
            if not (s1["session"] and s1["painted"] >= s0["painted"]) or alive[0] == "0":
                bad.append("%s was touched by the refusal: session=%s painted %s->%s, processes %s" % (r.user, s1["session"], s0["painted"], s1["painted"], alive[0]))
            notes.append("%s still attached, painted %s->%s, %s processes" % (r.user, s0["painted"], s1["painted"], alive[0]))
        jr = box.journal("farewell reason=0x0e|DENIED", since="-3min", n=2)
        notes.append("journal: %s" % jr[:300])
    finally:
        for r in clients:
            r.stop()
        box.run("rm -f %s; systemctl restart remotix; true" % CAP_FILE)
        back = wait_port(box, de)
        notes.append("drop-in removed, service restarted, answers again: %s" % back)
    ev = "; ".join(notes)
    return (FAIL, "; ".join(bad) + " -- " + ev) if bad else (PASS, ev)


# ------------------------------------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--box", default="xfce", choices=sorted(lib.PORTS))
    ap.add_argument("--only", default="", help="comma-separated check names")
    ap.add_argument("--no-cap", action="store_true", help="skip session-cap (it restarts the service of the box)")
    ap.add_argument("--cap", type=int, default=75, help="seconds allowed for login and desktop")
    a = ap.parse_args()
    de = a.box
    want = [n for n in NAMES if (not a.only or n in a.only.split(",")) and not (a.no_cap and n == "session-cap")]
    res = lib.Results(want)
    rig = lib.Rig(de, "chrome", "dk1", PW, "desk", cap=a.cap)
    mon = {}

    def session_checks():
        # one session of dk1 for the first three checks
        needs = [n for n in want if n in NAMES[:3]]
        if not needs:
            return
        box = rig.box
        box.ensure_user("dk1", PW)
        K.install(box)
        if "no-password-windows" in needs:
            box.run("pkill -f '[b]usctl --system monitor'; true")
            box.run("rm -f /tmp/rx-sysbus.txt /tmp/rx-userbus.txt; setsid nohup busctl --system monitor --match \"interface=org.freedesktop.PolicyKit1.AuthenticationAgent\" </dev/null >/tmp/rx-sysbus.txt 2>&1 & sleep 1; true")
        rig.start(make_user=False)
        rig.open_page()
        rig.login(real=True)
        if "no-password-windows" in needs:
            uid = box.run("id -u dk1")[1].strip()
            box.run("for i in $(seq 40); do [ -S /run/user/%s/bus ] && break; sleep 0.5; done; "
                    "setsid nohup runuser -u dk1 -- env DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%s/bus timeout 150 dbus-monitor --session </dev/null >/tmp/rx-userbus.txt 2>&1 & sleep 1; true" % (uid, uid))
        d = rig.settle(a.cap)
        mon["t_settled"] = time.time()
        lib.save_png("desk-session-%s-%s.png" % (de, STAMP), d["png"])
        print("session of dk1 up: %s, shell %.0f s" % (d["desc"], d["shell_s"]), flush=True)
        if "power-entries-absent" in needs:
            res.attempt("power-entries-absent", lambda: check_power(rig, de))
        if "no-password-windows" in needs:
            res.attempt("no-password-windows", lambda: check_password_windows(rig, de, mon))
        box.run("pkill -f '[b]usctl --system monitor'; true")
        box.run("pkill -u dk1 -x dbus-monitor; true")
        if "users-shell-and-environment" in needs:
            res.attempt("users-shell-and-environment", lambda: check_shell(rig, de))

    def flow():
        try:
            session_checks()
        except (Fail, ToolError) as e:
            for n in [n for n in NAMES[:3] if n in res.pending()]:
                res.say(FAIL if isinstance(e, Fail) else BLOCKED, n, "session of dk1: " + str(e))
        except Exception as e:  # noqa: BLE001
            for n in [n for n in NAMES[:3] if n in res.pending()]:
                res.say(BLOCKED, n, lib.tool_error(e))
        finally:
            rig.box.end_users(["dk1"])
            if rig.g:
                rig.g.close()
                rig.g = None
        rig.user = "dkf"
        if "settings-intact" in want:
            res.attempt("settings-intact", lambda: check_settings(rig, de, a))
            if rig.g:
                rig.g.close()
                rig.g = None
        if "canvas-limits" in want or "reattach-windows-inside" in want:
            if "canvas-limits" in want:
                res.attempt("canvas-limits", lambda: check_canvas(rig, de))
            if "reattach-windows-inside" in want:
                res.attempt("reattach-windows-inside", lambda: check_reattach_inside(rig, de))
            rig.box.end_users(["dk5"])
            if rig.g:
                rig.g.close()
                rig.g = None
        if "session-cap" in want:
            res.attempt("session-cap", lambda: check_cap(rig, de, a))

    try:
        return res.sequence(flow, 2400)
    finally:
        rig.stop()


if __name__ == "__main__":
    sys.exit(main())
