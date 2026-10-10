#!/bin/bash
#
# ⛔ HISTORY: the installer's GUI was removed on 10 Oct 2026 (DECISIONI §10.31). This bench
# tested R36/R37 on 30 Sep and no longer runs (remotix-install-gui is missing); it stays as a record of the test.
#
# t9-gui.sh — phase 17, T9: the installer's WINDOW on the real desktop of a "customer" VM
# (QEMU's virtual screen, the distribution's login screen, the user's desktop,
# the polkit dialog), driven through the QEMU monitor: absolute tablet for clicks, sendkey for
# keys, screendump for photos. One step per call; photos in /media/REMOTIX/vm17/t9-gui/<m>/.
#
#   (on the server, as nicfio)   sg kvm -c 'bash t9-gui.sh <machine> <step> [arguments]'
#
#   turn_on               "client" snapshot, power on with the tablet; nicfio's password
#                         (the administrator who installs) = $PASSWORD
#   log_in                from the login screen to nicfio's desktop (keyboard)
#   password              types the password in the polkit dialog, and Enter
#   picture <name>           the screen into <name>.png
#   click <x> <y>          a left click at pixel x,y (screen 1280×800)
#   put_out <text>         the text, key by key
#   key <key>           one key (ret, tab, esc, ctrl-alt-t…)
#   terminal [name]      opens the desktop's terminal (Super, "terminal", Enter)
#   win [language]   types in the terminal "LANG=… sh install.sh --win" and Enter
#                         (LANG of the language: it_IT.UTF-8 · en_US.UTF-8 · de_DE.UTF-8)
#   processes              who runs: the window (uid) and the root part (R37)
#   turn_off                powers off and goes back to "client"
set -uo pipefail
m=${1:?machine}; step=${2:?step}; shift 2
R=/media/REMOTIX/vm17
F=$R/t9-gui/$m
V="bash $R/17-vm.sh"
ARCH=http://10.0.2.2:8727
PASSWORD=${REMOTIX_TEST_PASSWORD:-prova2026}
mkdir -p "$F"
vm() { $V ssh "$m" "$@"; }
# the QEMU monitor commands, all in ONE connection (one per stdin line; "should_wait S"
# waits S seconds): one key per 17-vm.sh call cost a second and a half per character
monitor() { # ⚠ the commands come from stdin: the program goes in -c, not in a heredoc (which is stdin)
	python3 -c '
import socket, sys, time
s = socket.socket(socket.AF_UNIX); s.settimeout(3); s.connect(sys.argv[1])
def read_it():
    time.sleep(0.05)
    try: s.recv(65536)
    except Exception: pass
read_it()
for row in sys.stdin.read().splitlines():
    if row.startswith("should_wait "):
        time.sleep(float(row.split()[1])); continue
    s.sendall((row + "\n").encode()); read_it()
' "$R/$m/monitor.sock"
}
# characters into key names (qcode; US keyboard)
keys_of() {
	python3 -c '
import sys
m = {" ": "spc", ".": "dot", "-": "minus", "/": "slash", ":": "shift-semicolon", "_": "shift-minus", "=": "equal", ",": "comma", "|": "shift-backslash"}
for c in sys.argv[1]:
    k = c if (c.islower() or c.isdigit()) else ("shift-" + c.lower() if c.isupper() else m.get(c))
    print("sendkey " + k); print("should_wait 0.05")
' "$1"
}

case $step in
turn_on)
	[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { echo "⛔ 4 VMs already running"; exit 2; }
	$V returns "$m" client >/dev/null || exit 1
	RX_VM_TABLET=1 $V start "$m" >"$F/avvia.log" 2>&1 || { tail "$F/avvia.log"; exit 1; }
	# nicfio's password (logs into the desktop) and root's: the "administrator" the polkit
	# dialog asks for where nicfio is not in the sudo/wheel group (the cloud images: sudo without group)
	vm "echo 'nicfio:$PASSWORD' | sudo chpasswd; echo 'root:$PASSWORD' | sudo chpasswd; id nicfio; systemctl is-active display-manager"
	;;
log_in)
	# from the login screen, with the keyboard: Enter on the first user, the password, Enter; then
	# Esc closes the distribution's welcome
	printf 'sendkey ret\nshould_wait 2\n' | monitor
	keys_of "$PASSWORD" | monitor
	printf 'sendkey ret\nshould_wait 15\nsendkey esc\nshould_wait 1\nsendkey esc\n' | monitor
	;;
password)
	# the polkit dialog: the password, Enter
	keys_of "$PASSWORD" | monitor
	echo "sendkey ret" | monitor
	;;
picture)
	$V display_screen "$m" "$F/${1:?name}.png" >/dev/null && echo "$F/$1.png"
	;;
click)
	# QMP: absolute position (0..32767 over the whole screen, 1280×800) and the left button
	python3 -c '
import json, socket, sys, time
x, y, w, h = map(int, sys.argv[2:6])
s = socket.socket(socket.AF_UNIX); s.settimeout(3); s.connect(sys.argv[1])
f = s.makefile("rw")
f.readline()
def qmp(c, a=None):
    f.write(json.dumps({"execute": c, **({"arguments": a} if a else {})}) + "\n"); f.flush()
    while True:
        r = json.loads(f.readline())
        if "return" in r or "error" in r: return r
qmp("qmp_capabilities")
ev = lambda *e: qmp("input-send-event", {"events": list(e)})
ev({"type": "abs", "data": {"axis": "x", "value": x * 32767 // (w - 1)}}, {"type": "abs", "data": {"axis": "y", "value": y * 32767 // (h - 1)}})
time.sleep(0.3)
ev({"type": "btn", "data": {"down": True, "button": "left"}}); time.sleep(0.12)
ev({"type": "btn", "data": {"down": False, "button": "left"}})
' "$R/$m/qmp.sock" "$1" "$2" "${SCREEN_W:-1280}" "${SCREEN_H:-800}"
	;;
put_out)
	keys_of "$*" | monitor
	;;
key)
	echo "sendkey $1" | monitor
	;;
terminal)
	# as a person would: the Super key, "terminal", Enter (GNOME; on KDE: "konsole")
	printf 'sendkey meta_l\nshould_wait 1.5\n' | monitor
	keys_of "${1:-terminal}" | monitor
	printf 'should_wait 1.5\nsendkey ret\n' | monitor
	;;
win)
	# the window launched FROM THE DESKTOP'S TERMINAL (it must be in the foreground): that is where polkit
	# finds the graphical session's agent. ⚠ Not from ssh: "No authentication agent found" (`[M]`)
	case ${1:-it} in it) L=it_IT.UTF-8 ;; en) L=en_US.UTF-8 ;; de) L=de_DE.UTF-8 ;; *) L=$1 ;; esac
	vm "curl -s -o /tmp/install.sh $ARCH/install.sh && chmod 644 /tmp/install.sh" || exit 1
	keys_of "LANG=$L LANGUAGE= sh /tmp/install.sh --archivio $ARCH --finestra" | monitor
	echo "sendkey ret" | monitor
	;;
processes)
	# R37: the window (the user's uid) and the root part (the systemd transient unit)
	vm "ps -eo uid,user,pid,ppid,unit,args | grep -E '[r]emotix-install|[g]ui-prova' | cut -c1-220" | tee -a "$F/processi.txt"
	;;
turn_off)
	$V halt "$m" >/dev/null 2>&1; $V returns "$m" client >/dev/null 2>&1; echo "   $m powered off, back to \"client\""
	;;
*) sed -n 3,24p "$0"; exit 2 ;;
esac
