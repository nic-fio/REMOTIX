#!/bin/bash
#
# ⛔ STORIA: la GUI dell'installatore è stata tolta il 10 ott 2026 (DECISIONI §10.31). Questo banco ha
# provato R36/R37 il 30 set e non gira più (manca remotix-install-gui); resta come documento della prova.
#
# t9-gui.sh — fase 17, T9: la FINESTRA dell'installatore sul desktop vero di una VM «cliente»
# (lo schermo virtuale di QEMU, la schermata d'accesso della distribuzione, il desktop dell'utente,
# il dialogo di polkit), guidata dal monitor di QEMU: tavoletta assoluta per i clic, sendkey per i
# tasti, screendump per le foto. Un passo per chiamata; le foto in /media/REMOTIX/vm17/t9-gui/<m>/.
#
#   (sul server, come nicfio)   sg kvm -c 'bash t9-gui.sh <macchina> <passo> [argomenti]'
#
#   accendi               foto «cliente», accensione con la tavoletta; la password di nicfio
#                         (l'amministratore che installa) = $PAROLA
#   accedi                dalla schermata d'accesso al desktop di nicfio (tastiera)
#   password              scrive la password nel dialogo di polkit, e Invio
#   foto <nome>           lo schermo in <nome>.png
#   clic <x> <y>          un clic sinistro al pixel x,y (schermo 1280×800)
#   scrivi <testo>        il testo, tasto per tasto
#   tasto <tasto>         un tasto (ret, tab, esc, ctrl-alt-t…)
#   terminale [nome]      apre il terminale del desktop (Super, «terminal», Invio)
#   finestra [lingua]     scrive nel terminale «LANG=… sh install.sh --finestra» e Invio
#                         (LANG della lingua: it_IT.UTF-8 · en_US.UTF-8 · de_DE.UTF-8)
#   processi              chi gira: la finestra (uid) e la parte da root (R37)
#   spegni                spegne e torna a «cliente»
set -uo pipefail
m=${1:?macchina}; passo=${2:?passo}; shift 2
R=/media/REMOTIX/vm17
F=$R/t9-gui/$m
V="bash $R/17-vm.sh"
ARCH=http://10.0.2.2:8727
PAROLA=${REMOTIX_PAROLA_PROVA:-prova2026}
mkdir -p "$F"
vm() { $V ssh "$m" "$@"; }
# i comandi del monitor di QEMU, tutti in UNA connessione (uno per riga di stdin; «attendi S»
# aspetta S secondi): un tasto per chiamata di 17-vm.sh costava un secondo e mezzo a carattere
monitor() { # ⚠ i comandi arrivano da stdin: il programma va in -c, non in un heredoc (che è stdin)
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
# i caratteri in nomi di tasti (qcode; tastiera USA)
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
	[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { echo "⛔ già 4 VM accese"; exit 2; }
	$V torna "$m" cliente >/dev/null || exit 1
	RX_VM_TAVOLETTA=1 $V avvia "$m" >"$F/avvia.log" 2>&1 || { tail "$F/avvia.log"; exit 1; }
	# la password di nicfio (entra nel desktop) e quella di root: l'«amministratore» che il dialogo
	# di polkit chiede dove nicfio non è nel gruppo sudo/wheel (le immagini cloud: sudo senza gruppo)
	vm "echo 'nicfio:$PAROLA' | sudo chpasswd; echo 'root:$PAROLA' | sudo chpasswd; id nicfio; systemctl is-active display-manager"
	;;
accedi)
	# dalla schermata d'accesso, con la tastiera: Invio sul primo utente, la password, Invio; poi
	# Esc chiude il benvenuto della distribuzione
	printf 'sendkey ret\nattendi 2\n' | monitor
	tasti_di "$PAROLA" | monitor
	printf 'sendkey ret\nattendi 15\nsendkey esc\nattendi 1\nsendkey esc\n' | monitor
	;;
password)
	# il dialogo di polkit: la password, Invio
	tasti_di "$PAROLA" | monitor
	echo "sendkey ret" | monitor
	;;
foto)
	$V schermo "$m" "$F/${1:?nome}.png" >/dev/null && echo "$F/$1.png"
	;;
clic)
	# QMP: posizione assoluta (0..32767 su tutto lo schermo, 1280×800) e il tasto sinistro
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
	# come farebbe una persona: il tasto Super, «terminal», Invio (GNOME; su KDE: «konsole»)
	printf 'sendkey meta_l\nattendi 1.5\n' | monitor
	tasti_di "${1:-terminal}" | monitor
	printf 'attendi 1.5\nsendkey ret\n' | monitor
	;;
finestra)
	# la finestra lanciata DAL TERMINALE DEL DESKTOP (dev'essere in primo piano): è lì che polkit
	# trova l'agente della sessione grafica. ⚠ Da ssh no: «No authentication agent found» (`[M]`)
	case ${1:-it} in it) L=it_IT.UTF-8 ;; en) L=en_US.UTF-8 ;; de) L=de_DE.UTF-8 ;; *) L=$1 ;; esac
	vm "curl -s -o /tmp/install.sh $ARCH/install.sh && chmod 644 /tmp/install.sh" || exit 1
	tasti_di "LANG=$L LANGUAGE= sh /tmp/install.sh --archivio $ARCH --finestra" | monitor
	echo "sendkey ret" | monitor
	;;
processi)
	# R37: la finestra (uid dell'utente) e la parte da root (l'unità transitoria di systemd)
	vm "ps -eo uid,user,pid,ppid,unit,args | grep -E '[r]emotix-install|[g]ui-prova' | cut -c1-220" | tee -a "$F/processi.txt"
	;;
spegni)
	$V ferma "$m" >/dev/null 2>&1; $V torna "$m" cliente >/dev/null 2>&1; echo "   $m spenta, tornata a «cliente»"
	;;
*) sed -n 3,24p "$0"; exit 2 ;;
esac
