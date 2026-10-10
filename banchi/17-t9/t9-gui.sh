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
#   accendi               "cliente" snapshot, power on with the tablet; nicfio's password
#                         (the administrator who installs) = $PAROLA
#   accedi                from the login screen to nicfio's desktop (keyboard)
#   password              types the password in the polkit dialog, and Enter
#   foto <name>           the screen into <name>.png
#   clic <x> <y>          a left click at pixel x,y (screen 1280×800)
#   scrivi <text>         the text, key by key
#   tasto <key>           one key (ret, tab, esc, ctrl-alt-t…)
#   terminale [name]      opens the desktop's terminal (Super, "terminal", Enter)
#   finestra [language]   types in the terminal "LANG=… sh install.sh --finestra" and Enter
#                         (LANG of the language: it_IT.UTF-8 · en_US.UTF-8 · de_DE.UTF-8)
#   processi              who runs: the window (uid) and the root part (R37)
#   spegni                powers off and goes back to "cliente"
set -uo pipefail
m=${1:?macchina}; passo=${2:?passo}; shift 2
R=/media/REMOTIX/vm17
F=$R/t9-gui/$m
V="bash $R/17-vm.sh"
ARCH=http://10.0.2.2:8727
PAROLA=${REMOTIX_PAROLA_PROVA:-prova2026}
mkdir -p "$F"
vm() { $V ssh "$m" "$@"; }
# the QEMU monitor commands, all in ONE connection (one per stdin line; "attendi S"
# waits S seconds): one key per 17-vm.sh call cost a second and a half per character
monitor() { # ⚠ the commands come from stdin: the program goes in -c, not in a heredoc (which is stdin)
	python3 -c '
import socket, sys, time
s = socket.socket(socket.AF_UNIX); s.settimeout(3); s.connect(sys.argv[1])
def leggi():
    time.sleep(0.05)
    try: s.recv(65536)
    except Exception: pass
leggi()
for riga in sys.stdin.read().splitlines():
    if riga.startswith("attendi "):
        time.sleep(float(riga.split()[1])); continue
    s.sendall((riga + "\n").encode()); leggi()
' "$R/$m/monitor.sock"
}
# characters into key names (qcode; US keyboard)
tasti_di() {
	python3 -c '
import sys
m = {" ": "spc", ".": "dot", "-": "minus", "/": "slash", ":": "shift-semicolon", "_": "shift-minus", "=": "equal", ",": "comma", "|": "shift-backslash"}
for c in sys.argv[1]:
    k = c if (c.islower() or c.isdigit()) else ("shift-" + c.lower() if c.isupper() else m.get(c))
    print("sendkey " + k); print("attendi 0.05")
' "$1"
}

case $passo in
accendi)
	[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { echo "⛔ 4 VMs already running"; exit 2; }
	$V torna "$m" cliente >/dev/null || exit 1
	RX_VM_TAVOLETTA=1 $V avvia "$m" >"$F/avvia.log" 2>&1 || { tail "$F/avvia.log"; exit 1; }
	# nicfio's password (logs into the desktop) and root's: the "administrator" the polkit
	# dialog asks for where nicfio is not in the sudo/wheel group (the cloud images: sudo without group)
	vm "echo 'nicfio:$PAROLA' | sudo chpasswd; echo 'root:$PAROLA' | sudo chpasswd; id nicfio; systemctl is-active display-manager"
	;;
accedi)
	# from the login screen, with the keyboard: Enter on the first user, the password, Enter; then
	# Esc closes the distribution's welcome
	printf 'sendkey ret\nattendi 2\n' | monitor
	tasti_di "$PAROLA" | monitor
	printf 'sendkey ret\nattendi 15\nsendkey esc\nattendi 1\nsendkey esc\n' | monitor
	;;
password)
	# the polkit dialog: the password, Enter
	tasti_di "$PAROLA" | monitor
	echo "sendkey ret" | monitor
	;;
foto)
	$V schermo "$m" "$F/${1:?nome}.png" >/dev/null && echo "$F/$1.png"
	;;
clic)
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
' "$R/$m/qmp.sock" "$1" "$2" "${SCHERMO_L:-1280}" "${SCHERMO_A:-800}"
	;;
scrivi)
	tasti_di "$*" | monitor
	;;
tasto)
	echo "sendkey $1" | monitor
	;;
terminale)
	# as a person would: the Super key, "terminal", Enter (GNOME; on KDE: "konsole")
	printf 'sendkey meta_l\nattendi 1.5\n' | monitor
	tasti_di "${1:-terminal}" | monitor
	printf 'attendi 1.5\nsendkey ret\n' | monitor
	;;
finestra)
	# the window launched FROM THE DESKTOP'S TERMINAL (it must be in the foreground): that is where polkit
	# finds the graphical session's agent. ⚠ Not from ssh: "No authentication agent found" (`[M]`)
	case ${1:-it} in it) L=it_IT.UTF-8 ;; en) L=en_US.UTF-8 ;; de) L=de_DE.UTF-8 ;; *) L=$1 ;; esac
	vm "curl -s -o /tmp/install.sh $ARCH/install.sh && chmod 644 /tmp/install.sh" || exit 1
	tasti_di "LANG=$L LANGUAGE= sh /tmp/install.sh --archivio $ARCH --finestra" | monitor
	echo "sendkey ret" | monitor
	;;
processi)
	# R37: the window (the user's uid) and the root part (the systemd transient unit)
	vm "ps -eo uid,user,pid,ppid,unit,args | grep -E '[r]emotix-install|[g]ui-prova' | cut -c1-220" | tee -a "$F/processi.txt"
	;;
spegni)
	$V ferma "$m" >/dev/null 2>&1; $V torna "$m" cliente >/dev/null 2>&1; echo "   $m powered off, back to \"cliente\""
	;;
*) sed -n 3,24p "$0"; exit 2 ;;
esac
