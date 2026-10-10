#!/bin/bash
#
# 17-t3-pacchetto.sh — phase 17, T3: the NATIVE PACKAGE tested in a
# "customer" VM from 17-vm.sh (for now Arch: `pacman`).  One step per call, so
# each outcome is read before going on.
#
#   (on the server, as nicfio; the VM started with 17-vm.sh avvia)
#   bash 17-t3-pacchetto.sh <machine> prepara             user `prova` (already in `video`: R33)
#   bash 17-t3-pacchetto.sh <machine> impronta <name>     $T3/<machine>/impronta-<name>.txt
#   bash 17-t3-pacchetto.sh <machine> installa <pkg>      copy and `pacman -U`, NOTHING ELSE (R4)
#   bash 17-t3-pacchetto.sh <machine> r40                 the package alone starts nothing
#   bash 17-t3-pacchetto.sh <machine> motore-monta        ENGINE STEPS by hand: groups + enable --now
#   bash 17-t3-pacchetto.sh <machine> motore-smonta       and their reverse, from the log
#   bash 17-t3-pacchetto.sh <machine> togli               `pacman -Rns remotix`
#   bash 17-t3-pacchetto.sh <machine> confronta <a> <b>   diff of the two fingerprints
#
# ⭐ "prepara" is the scene, not the installation: a person with the password
#    to enter from the browser, and already in `video` BEFORE — so the test
#    sees whether uninstalling removes a group that was there (R33, ⛔ it must not).
# ⛔ Between "fingerprint before" and "installa" nothing is touched by hand: that is R4.
set -euo pipefail
m=${1:?macchina}; passo=${2:?passo}
R=/media/REMOTIX/vm17
T3=${T3:-$R/t3}
QUI=$(cd "$(dirname "$0")" && pwd)
VM() { bash "$R/17-vm.sh" ssh "$m" "$@"; }
PAROLA=${REMOTIX_PAROLA_PROVA:-prova2026}
mkdir -p "$T3/$m"

case $m in
debian13-*) n=1;; ubuntu2604-*) n=2;; fedora44-*) n=3;; arch-*) n=4;;
tumbleweed-*) n=5;; leap16-*) n=6;; alma10-*) n=7;; *) echo "unknown machine: $m"; exit 2;;
esac
case ${m#*-} in gnome) k=1;; kde) k=2;; xfce) k=3;; lxqt) k=4;; esac
PORTA_SSH=$((2300 + 10 * n + k))
O="-i $R/ssh/id_ed25519 -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"

case $passo in
prepara)
	VM "id -u prova >/dev/null 2>&1 || sudo useradd -m -s /bin/bash prova
echo 'prova:$PAROLA' | sudo chpasswd
sudo gpasswd -a prova video >/dev/null
id prova" ;;
impronta)
	nome=${3:?nome}
	# shellcheck disable=SC2086
	scp -q $O -P "$PORTA_SSH" "$QUI/17-t3-impronta-arch.sh" nicfio@localhost:/var/tmp/
	VM 'sudo bash /var/tmp/17-t3-impronta-arch.sh' >"$T3/$m/impronta-$nome.txt"
	VM 'rm -f /var/tmp/17-t3-impronta-arch.sh'
	wc -l "$T3/$m/impronta-$nome.txt" ;;
installa)
	pkg=${3:?pacchetto}
	# shellcheck disable=SC2086
	scp -q $O -P "$PORTA_SSH" "$pkg" nicfio@localhost:/var/tmp/
	b=$(basename "$pkg")
	VM "sudo pacman -U --noconfirm /var/tmp/$b; e=\$?; rm -f /var/tmp/$b; exit \$e" 2>&1 | tee "$T3/$m/installa-$(date +%H%M%S).log" ;;
r40)
	# ⭐ R40 (DECISIONI.md §10.12): the package ON ITS OWN starts nothing.
	VM 'echo "service: $(systemctl is-enabled remotix.service 2>&1) / $(systemctl is-active remotix.service 2>&1)"
echo "listening on 7447: $(ss -Hlntu | grep -c ":7447 ")"
echo "GPU groups: $(for n in /dev/dri/card* /dev/dri/renderD*; do stat -c %G $n; done | sort -u | while read g; do printf "%s=[%s] " $g "$(getent group $g | cut -d: -f4)"; done)"
echo "active belts: $(ls /etc/polkit-1/rules.d/*remotix* /usr/share/polkit-1/rules.d/*remotix* /etc/systemd/logind.conf.d/*remotix* /usr/lib/systemd/logind.conf.d/*remotix* /etc/systemd/sleep.conf.d/*remotix* /usr/lib/systemd/sleep.conf.d/*remotix* 2>/dev/null | wc -l)"
echo "logind in force: $(systemd-analyze cat-config systemd/logind.conf | grep -c "^HandlePowerKey=ignore")  sleep in force: $(systemd-analyze cat-config systemd/sleep.conf | grep -c "^AllowSuspend=no")"
echo "firewall: $(systemctl is-active firewalld 2>&1)"
echo "== systemctl start remotix (by hand): must refuse with RX-INST-001"
sudo systemctl start remotix.service; sleep 3
echo "after start: $(systemctl is-active remotix.service)  RX-INST-001 in the log: $(sudo journalctl -u remotix.service -o cat --no-pager | grep -c RX-INST-001)"
sudo systemctl stop remotix.service' ;;
motore-monta)
	# ⚠ ENGINE STEPS done by hand (§10.12): the engine does not exist yet (T4-T5).
	#   GPU groups to the person who enters (read from the nodes, with the log
	#   of who was already there), then the start.  Not the belts: the desktop does not need them.
	VM 'for g in $(for n in /dev/dri/card* /dev/dri/renderD*; do stat -c %G $n; done | sort -u); do
  if id -nG prova | tr " " "\n" | grep -qx $g; then echo "C_ERA prova $g"; else sudo gpasswd -a prova $g >/dev/null && echo "MESSO prova $g"; fi
done' | tee "$T3/$m/motore.registro"
	VM 'sudo systemctl enable --now remotix.service && sleep 3 && systemctl is-active remotix.service
sudo journalctl -u remotix.service -o cat --no-pager | grep -E "ready:|PAM|KWin|desktop of this" | tail -5' ;;
motore-smonta)
	VM 'sudo systemctl disable --now remotix.service'
	while read -r cosa u g; do
		[ "$cosa" = MESSO ] && VM "sudo gpasswd -d $u $g"
	done <"$T3/$m/motore.registro" ;;
togli)
	VM 'sudo pacman -Rns --noconfirm remotix' 2>&1 | tee "$T3/$m/togli-$(date +%H%M%S).log" ;;
confronta)
	a=${3:?a}; b=${4:?b}
	diff "$T3/$m/impronta-$a.txt" "$T3/$m/impronta-$b.txt" >"$T3/$m/diff-$a-$b.txt" || true
	grep -c '^[<>]' "$T3/$m/diff-$a-$b.txt" || true
	echo "$T3/$m/diff-$a-$b.txt" ;;
*) echo "unknown step: $passo"; exit 2 ;;
esac
