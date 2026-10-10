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
#   turn_on [net|senza-rete]  "client" snapshot, power on. senza-rete: the network REMOVED (restrict=on) and
#                              every packet of the interface captured in outcomes/<m>/net.pcap
#   motore                     the engine from the T9 archive (connected) or from the server (no network),
#                              and the answer files, in /root
#   cmd "<command>"            a command as root in the VM (the engine is /root/remotix-install)
#   prepare <answers>          (connected) prepare-offline; the bundle goes back to the server in
#                              outcomes/<m>/offline.tar
#   offline <answers>      (no network) the bundle inside, and install --offline --answers
#   r21 <answers>              (retired, §10.36) "client" snapshot, a NEW cloud-init seed (cloud-init-r21.yaml: user
#                              prova, answer file, curl install.sh | sh), power on; nobody touches
#                              it until cloud-init has finished; then the installation log
#   look                     a real Chrome enters and looks at the desktop (17-t1c-guarda.sh, its own labwc)
#   net                       the capture: every flow the VM sent, and whether it reached anything
#   turn_off                     powers off and goes back to "client"
#
# ⛔ At most 2 VMs of this bench and 4 in all; it does not power off a machine started by others.
# Evidence in /media/REMOTIX/vm17/t9/esiti/<machine>/.
set -uo pipefail
m=${1:?machine}; step=${2:?step}; shift 2
R=/media/REMOTIX/vm17
T9=$R/t9
E=$T9/outcomes/$m
V="bash $R/17-vm.sh"
ARCH=http://10.0.2.2:8727
PASSWORD=${REMOTIX_TEST_PASSWORD:-prova2026}
case $m in
debian13-*) n=1;; ubuntu2604-*) n=2;; fedora44-*) n=3;; arch-*) n=4;;
*) echo "unknown machine: $m"; exit 2;;
esac
k=0; case ${m#*-} in gnome) k=1;; kde) k=2;; xfce) k=3;; lxqt) k=4;; esac
PRX=$((7500 + 10 * n + k))
mkdir -p "$E"
vm() { $V ssh "$m" "$@"; }
t() { date +%H:%M:%S; }
limit() {
	if pgrep -f "qemu-system.*-name rx-$m " >/dev/null; then echo "⛔ $m is already running"; exit 2; fi
	[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { echo "⛔ 4 VMs already running"; exit 2; }
}

case $step in
turn_on)
	manner=${1:-net}
	limit
	rm -f "$E/net.pcap"
	$V returns "$m" client >/dev/null || exit 1
	if [ "$manner" = senza-rete ]; then
		RX_VM_NETWORK=,restrict=on RX_VM_CAPTURE=$E/net.pcap $V start "$m" >"$E/avvia.log" 2>&1 || { tail "$E/avvia.log"; exit 1; }
	else
		$V start "$m" >"$E/avvia.log" 2>&1 || { tail "$E/avvia.log"; exit 1; }
	fi
	vm "id -u prova >/dev/null 2>&1 || sudo useradd -m -s /bin/bash prova
echo 'prova:$PASSWORD' | sudo chpasswd
echo \"prova: \$(id prova)\"
curl -s -m 5 -o /dev/null -w 'T9 archive: HTTP %{http_code}\n' $ARCH/install.sh || echo 'T9 archive: NOT reachable'" | tee "$E/turn_on-$manner.txt"
	;;
motore)
	for f in $T9/archivio/engine/remotix-install $T9/archivio/engine/remotix-install.sha256 $T9/replies-*.conf; do
		vm "sudo tee /root/$(basename "$f") >/dev/null" <"$f"
	done
	# simplified D11 (DECISIONI §10.21): the engine is verified with the published sha256
	vm "sudo chmod 755 /root/remotix-install; cd /root && sudo sha256sum -c remotix-install.sha256; sudo /root/remotix-install version" | tee "$E/motore.txt"
	;;
cmd)
	vm "sudo sh -c '$*'" 2>&1 | tee -a "$E/comandi.txt"
	;;
prepare)
	r=${1:-risposte-debian.conf}
	T0=$(date +%s)
	vm "sudo rm -rf /root/fuori-linea; sudo /root/remotix-install prepare-offline --archive $ARCH --answers /root/$r --output /root/fuori-linea" 2>&1 | tee "$E/prepara.txt"
	echo "   prepare: $(( $(date +%s) - T0 )) s"
	vm "sudo tar -C /root -cf - offline" >"$E/offline.tar"
	echo "   bundle: $(du -h "$E/offline.tar" | cut -f1) in $E/offline.tar"
	;;
offline)
	r=${1:-risposte-debian.conf}
	pkt=${PACKAGE:-$E/offline.tar}
	vm "sudo rm -rf /root/fuori-linea && sudo tar -C /root -xf -" <"$pkt"
	T0=$(date +%s); date -u +%T >"$E/finestra.txt"
	vm "sudo /root/remotix-install install --offline /root/fuori-linea --answers /root/$r" >"$E/installa.txt" 2>&1
	u=$?; date -u +%T >>"$E/finestra.txt"
	echo "   install: exit $u in $(( $(date +%s) - T0 )) s — $(grep -E '^operation ' "$E/installa.txt")"
	grep -E 'BLOCKED|FAILED|RX-(OUT|REPLIES|PIANO)' "$E/installa.txt" | head -6 | sed 's/^/   /'
	;;
r21)
	# ⛔ RETIRED (10 Oct 2026, §10.36): the .run prints no «install.sh: uscita» line (nor any
	#   equivalent: there is no script that downloads and checks the engine). The body stays as history.
	echo "⛔ step «r21» retired (DECISIONI §10.36): the seed ran «curl install.sh | sh», and install.sh no longer exists — REMOTIX comes as one .run; the real run is banchi/17-distro/17-t10.sh"; exit 2
	r=${1:-risposte-debian.conf}
	limit
	S=$E/seed; rm -rf "$S"; mkdir -p "$S"
	printf 'instance-id: remotix-t9-%s-%s\nlocal-hostname: rx-%s\n' "$m" "$(date +%s)" "$m" >"$S/meta-data"
	replies=$(sed 's/^/      /' "$T9/$r")
	python3 - "$T9/cloud-init-r21.yaml" "$S/user-data" "$m" "$(cat $R/ssh/id_ed25519.pub)" "$PASSWORD" "$ARCH" "$replies" <<'PY'
import sys
t = open(sys.argv[1]).read()
for k, v in zip(["@MACHINE@", "@KEY@", "@PASSWORD@", "@ARCHIVIO@", "@REPLIES@"], sys.argv[3:]):
    t = t.replace(k, v)
open(sys.argv[2], "w").write(t)
PY
	genisoimage -quiet -output "$S/seed.iso" -volid cidata -joliet -rock "$S/user-data" "$S/meta-data" || exit 1
	$V returns "$m" client >/dev/null || exit 1
	T0=$(date +%s)
	# 17-vm.sh start waits for ssh AND the end of cloud-init (cloud-init status --wait): nobody touches
	# the machine before
	RX_VM_SEED=$S/seed.iso $V start "$m" >"$E/avvia-r21.log" 2>&1 || { tail "$E/avvia-r21.log"; exit 1; }
	echo "   cloud-init finished in $(( $(date +%s) - T0 )) s (from power-on)"
	vm "sudo cloud-init status --long | head -8; echo ---; sudo cat /var/log/remotix-installa.log; echo ---; sudo grep -E 'remotix|runcmd' /var/log/cloud-init-output.log | tail -5" >"$E/r21.txt" 2>&1
	grep -E 'status:|install.sh: out_dir|^operation |VERIFIED|RX-RISPOSTE|BLOCKED' "$E/r21.txt" | sed 's/^/   /'
	;;
look)
	mkdir -p "$T9/t1c"
	T1C=$T9/t1c T1C_EVIDENCE=$E/browser bash "$R/t1c/17-t1c-guarda.sh" "$m" "$PRX" chrome >"$E/guarda.txt" 2>&1
	echo "   look: exit $?"; tail -4 "$E/guarda.txt" | cut -c1-300 | sed 's/^/   /'
	;;
net)
	# the installation window (UTC, the server's clock: the same as the capture's), written
	# by the offline step
	[ -f "$E/net.pcap" ] || { echo "no capture"; exit 2; }
	set -- $(cat "$E/finestra.txt" 2>/dev/null)
	python3 "$T9/t9-rete.py" "$E/net.pcap" ${1:+DAL $1 AL ${2:-$1}} | tee "$E/rete.txt"
	;;
turn_off)
	$V halt "$m" >/dev/null 2>&1; $V returns "$m" client >/dev/null 2>&1; echo "   $m powered off, back to \"client\""
	;;
*) sed -n 3,24p "$0"; exit 2 ;;
esac
