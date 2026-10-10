#!/bin/bash
#
# ⛔ HISTORY (10 Oct 2026, DECISIONI §10.36): this bench tests an installer that no longer exists —
#   separate plan/approve/apply, signed archive and install.sh, third-party repositories, firewall and
#   belts set by the engine, answer files. Today: one .run, `install` with the [y/N] question, and
#   REMOTIX that does not modify the system. It stays as the history of the tests of 29 Sep - 1 Oct 2026; the real
#   run is banchi/17-distro/17-t10.sh. It is not launched.
#
# t9-vm.sh — phase 17, T9: WITHOUT QUESTIONS (R21, R31) and WITHOUT NETWORK (R22), on a "customer" VM, one step
# per call.
#
#   (on the server, as nicfio)   sg kvm -c 'bash t9-vm.sh <machine> <step> [arguments]'
#
#   accendi [rete|senza-rete]  "cliente" snapshot, power on. senza-rete: the network REMOVED (restrict=on) and
#                              every packet of the interface captured in esiti/<m>/rete.pcap
#   motore                     the engine from the T9 archive (connected) or from the server (no network),
#                              and the answer files, in /root
#   cmd "<command>"            a command as root in the VM (the engine is /root/remotix-install)
#   prepara <answers>          (connected) prepare-offline; the bundle goes back to the server in
#                              esiti/<m>/fuori-linea.tar
#   fuori-linea <answers>      (no network) the bundle inside, and install --offline --answers
#   r21 <answers>              "cliente" snapshot, a NEW cloud-init seed (cloud-init-r21.yaml: user
#                              prova, answer file, curl install.sh | sh), power on; nobody touches
#                              it until cloud-init has finished; then the installation log
#   guarda                     a real Chrome enters and looks at the desktop (17-t1c-guarda.sh, its own labwc)
#   rete                       the capture: every flow the VM sent, and whether it reached anything
#   spegni                     powers off and goes back to "cliente"
#
# ⛔ At most 2 VMs of this bench and 4 in all; it does not power off a machine started by others.
# Evidence in /media/REMOTIX/vm17/t9/esiti/<machine>/.
set -uo pipefail
m=${1:?macchina}; passo=${2:?passo}; shift 2
R=/media/REMOTIX/vm17
T9=$R/t9
E=$T9/esiti/$m
V="bash $R/17-vm.sh"
ARCH=http://10.0.2.2:8727
PAROLA=${REMOTIX_PAROLA_PROVA:-prova2026}
case $m in
debian13-*) n=1;; ubuntu2604-*) n=2;; fedora44-*) n=3;; arch-*) n=4;;
*) echo "unknown machine: $m"; exit 2;;
esac
k=0; case ${m#*-} in gnome) k=1;; kde) k=2;; xfce) k=3;; lxqt) k=4;; esac
PRX=$((7500 + 10 * n + k))
mkdir -p "$E"
vm() { $V ssh "$m" "$@"; }
t() { date +%H:%M:%S; }
limite() {
	if pgrep -f "qemu-system.*-name rx-$m " >/dev/null; then echo "⛔ $m is already running"; exit 2; fi
	[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { echo "⛔ 4 VMs already running"; exit 2; }
}

case $passo in
accendi)
	modo=${1:-rete}
	limite
	rm -f "$E/rete.pcap"
	$V torna "$m" cliente >/dev/null || exit 1
	if [ "$modo" = senza-rete ]; then
		RX_VM_RETE=,restrict=on RX_VM_CATTURA=$E/rete.pcap $V avvia "$m" >"$E/avvia.log" 2>&1 || { tail "$E/avvia.log"; exit 1; }
	else
		$V avvia "$m" >"$E/avvia.log" 2>&1 || { tail "$E/avvia.log"; exit 1; }
	fi
	vm "id -u prova >/dev/null 2>&1 || sudo useradd -m -s /bin/bash prova
echo 'prova:$PAROLA' | sudo chpasswd
echo \"prova: \$(id prova)\"
curl -s -m 5 -o /dev/null -w 'T9 archive: HTTP %{http_code}\n' $ARCH/install.sh || echo 'T9 archive: NOT reachable'" | tee "$E/accendi-$modo.txt"
	;;
motore)
	for f in $T9/archivio/engine/remotix-install $T9/archivio/engine/remotix-install.sha256 $T9/risposte-*.conf; do
		vm "sudo tee /root/$(basename "$f") >/dev/null" <"$f"
	done
	# simplified D11 (DECISIONI §10.21): the engine is verified with the published sha256
	vm "sudo chmod 755 /root/remotix-install; cd /root && sudo sha256sum -c remotix-install.sha256; sudo /root/remotix-install version" | tee "$E/motore.txt"
	;;
cmd)
	vm "sudo sh -c '$*'" 2>&1 | tee -a "$E/comandi.txt"
	;;
prepara)
	r=${1:-risposte-debian.conf}
	T0=$(date +%s)
	vm "sudo rm -rf /root/fuori-linea; sudo /root/remotix-install prepare-offline --archive $ARCH --answers /root/$r --output /root/fuori-linea" 2>&1 | tee "$E/prepara.txt"
	echo "   prepare: $(( $(date +%s) - T0 )) s"
	vm "sudo tar -C /root -cf - fuori-linea" >"$E/fuori-linea.tar"
	echo "   bundle: $(du -h "$E/fuori-linea.tar" | cut -f1) in $E/fuori-linea.tar"
	;;
fuori-linea)
	r=${1:-risposte-debian.conf}
	pac=${PACCHETTO:-$E/fuori-linea.tar}
	vm "sudo rm -rf /root/fuori-linea && sudo tar -C /root -xf -" <"$pac"
	T0=$(date +%s); date -u +%T >"$E/finestra.txt"
	vm "sudo /root/remotix-install install --offline /root/fuori-linea --answers /root/$r" >"$E/installa.txt" 2>&1
	u=$?; date -u +%T >>"$E/finestra.txt"
	echo "   install: exit $u in $(( $(date +%s) - T0 )) s — $(grep -E '^operation ' "$E/installa.txt")"
	grep -E 'BLOCKED|FAILED|RX-(FUORI|RISPOSTE|PIANO)' "$E/installa.txt" | head -6 | sed 's/^/   /'
	;;
r21)
	r=${1:-risposte-debian.conf}
	limite
	S=$E/seme; rm -rf "$S"; mkdir -p "$S"
	printf 'instance-id: remotix-t9-%s-%s\nlocal-hostname: rx-%s\n' "$m" "$(date +%s)" "$m" >"$S/meta-data"
	risposte=$(sed 's/^/      /' "$T9/$r")
	python3 - "$T9/cloud-init-r21.yaml" "$S/user-data" "$m" "$(cat $R/ssh/id_ed25519.pub)" "$PAROLA" "$ARCH" "$risposte" <<'PY'
import sys
t = open(sys.argv[1]).read()
for k, v in zip(["@MACCHINA@", "@CHIAVE@", "@PAROLA@", "@ARCHIVIO@", "@RISPOSTE@"], sys.argv[3:]):
    t = t.replace(k, v)
open(sys.argv[2], "w").write(t)
PY
	genisoimage -quiet -output "$S/seme.iso" -volid cidata -joliet -rock "$S/user-data" "$S/meta-data" || exit 1
	$V torna "$m" cliente >/dev/null || exit 1
	T0=$(date +%s)
	# 17-vm.sh avvia waits for ssh AND the end of cloud-init (cloud-init status --wait): nobody touches
	# the machine before
	RX_VM_SEME=$S/seme.iso $V avvia "$m" >"$E/avvia-r21.log" 2>&1 || { tail "$E/avvia-r21.log"; exit 1; }
	echo "   cloud-init finished in $(( $(date +%s) - T0 )) s (from power-on)"
	vm "sudo cloud-init status --long | head -8; echo ---; sudo cat /var/log/remotix-installa.log; echo ---; sudo grep -E 'remotix|runcmd' /var/log/cloud-init-output.log | tail -5" >"$E/r21.txt" 2>&1
	grep -E 'status:|install.sh: uscita|^operation |VERIFIED|RX-RISPOSTE|BLOCKED' "$E/r21.txt" | sed 's/^/   /'
	;;
guarda)
	mkdir -p "$T9/t1c"
	T1C=$T9/t1c T1C_EVIDENZE=$E/browser bash "$R/t1c/17-t1c-guarda.sh" "$m" "$PRX" chrome >"$E/guarda.txt" 2>&1
	echo "   guarda: exit $?"; tail -4 "$E/guarda.txt" | cut -c1-300 | sed 's/^/   /'
	;;
rete)
	# the installation window (UTC, the server's clock: the same as the capture's), written
	# by the fuori-linea step
	[ -f "$E/rete.pcap" ] || { echo "no capture"; exit 2; }
	set -- $(cat "$E/finestra.txt" 2>/dev/null)
	python3 "$T9/t9-rete.py" "$E/rete.pcap" ${1:+DAL $1 AL ${2:-$1}} | tee "$E/rete.txt"
	;;
spegni)
	$V ferma "$m" >/dev/null 2>&1; $V torna "$m" cliente >/dev/null 2>&1; echo "   $m powered off, back to \"cliente\""
	;;
*) sed -n 3,24p "$0"; exit 2 ;;
esac
