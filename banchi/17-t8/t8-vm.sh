#!/bin/bash
#
# ⛔ HISTORY (10 Oct 2026, DECISIONI §10.36): this bench tests an installer that no longer exists —
#   separate plan/approve/apply, signed archive and install.sh, third-party repositories, firewall and
#   belts set by the engine, answer files. Today: one .run, `install` with the [y/N] question, and
#   REMOTIX that does not modify the system. It stays as the history of the tests of 29 Sep - 1 Oct 2026; the real
#   run is banchi/17-distro/17-t10.sh. It is not launched.
#
# t8-vm.sh — phase 17, T8: REMOTIX from the signed ARCHIVE, on a "customer" VM, one step per call.
#
#   (on the server, as nicfio)   sg kvm -c 'bash t8-vm.sh <machine> <step> [arguments]'
#
#   accendi                 "cliente" snapshot, power on; the person "prova" already in the node's group
#   terzi                   R18: a THIRD-PARTY archive already configured (its own key, its own package)
#   impronta <name>         the fingerprint of the machine (17-t3-impronta*.sh) and of the repositories (R18)
#   motore                  the engine downloaded FROM THE ARCHIVE (as install.sh does) and its sha256
#   installa [channel]      check → plan --install --archive → approve → apply
#   script                  like the administrator: install.sh and its sha256 from the archive, the
#                           check (sha256sum -c), then `sh install.sh --archive … --answers …`
#   aggiorna                the SYSTEM upgrade (apt-get upgrade · dnf upgrade): REMOTIX
#                           comes with it (DECISIONI §10.23); the journal of remotix.service
#   disinstalla             uninstall --purge → apply, and what is left of REMOTIX
#   stato                   versions, service, operations, certificate, catalogue
#   collega                 a real Chrome enters and STAYS connected (t8-browser.py) — in the background
#   via                     the connected browser reloads and re-enters: it must see the desktop again
#   palco                   the processes of "prova"'s desktop (pid): before and after must match
#   motore-cmd "<arg>"      remotix-install <arg> in the VM (as root)
#   spegni                  powers off and goes back to "cliente"
#
# The archive is in /media/REMOTIX/vm17/archivio/, served on 127.0.0.1:8717 (from the VM: 10.0.2.2);
# another one with ARCH=http://10.0.2.2:<port> (t8-porta.sh with DOVE and PORTA).
# ⛔ At most 2 VMs of this bench and 4 in all; it does not power off a machine already started by others.
# Evidence in /media/REMOTIX/vm17/t8/esiti/<machine>/.
set -uo pipefail
m=${1:?macchina}; passo=${2:?passo}; shift 2
R=/media/REMOTIX/vm17
T8=${T8:-$R/t8}
QUI=$(cd "$(dirname "$0")" && pwd)
E=$T8/esiti/$m
V="bash $R/17-vm.sh"
ARCH=${ARCH:-http://10.0.2.2:8717}
PAROLA=${REMOTIX_PAROLA_PROVA:-prova2026}
IMPRONTA=17-t3-impronta.sh
case $m in
debian13-*) n=1;; ubuntu2604-*) n=2;;
fedora44-*) n=3; IMPRONTA=17-t3-impronta-rpm.sh;;
arch-*) n=4; IMPRONTA=17-t3-impronta-arch.sh;;
*) echo "unknown machine: $m"; exit 2;;
esac
k=0; case ${m#*-} in gnome) k=1;; kde) k=2;; xfce) k=3;; lxqt) k=4;; esac
PSSH=$((2300 + 10 * n + k)); PRX=$((7500 + 10 * n + k))
mkdir -p "$E"
vm() { $V ssh "$m" "$@"; }
t() { date +%H:%M:%S; }

case $passo in
accendi)
	if pgrep -f "qemu-system.*-name rx-$m " >/dev/null; then echo "⛔ $m is already running"; exit 2; fi
	[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { echo "⛔ 4 VMs already running"; exit 2; }
	rm -rf "$E"; mkdir -p "$E"
	$V torna "$m" cliente >/dev/null || exit 1
	$V avvia "$m" >"$E/avvia.log" 2>&1 || { tail "$E/avvia.log"; exit 1; }
	vm "id -u prova >/dev/null 2>&1 || sudo useradd -m -s /bin/bash prova
echo 'prova:$PAROLA' | sudo chpasswd
G=\$(for x in /dev/dri/card[0-9]*; do [ -e \$x ] && getent group \$(stat -c %g \$x) | cut -d: -f1; done | sort -u | head -1)
[ -n \"\$G\" ] && sudo gpasswd -a prova \"\$G\" >/dev/null
id prova; curl -s -o /dev/null -w 'archive: HTTP %{http_code}\n' $ARCH/chiavi/LEGGIMI" | tee "$E/accendi.txt"
	;;
terzi)
	# R18: a third-party archive configured BEFORE REMOTIX (served by the same server, with its
	# own key); after the installation its files and its key must be identical
	case $n in
	1) vm "sudo install -d -m 755 /etc/apt/keyrings
curl -s http://10.0.2.2:8719/terzi.asc -o /tmp/terzi.asc
sudo install -m 644 /tmp/terzi.asc /etc/apt/keyrings/terzi.asc
printf 'Types: deb\nURIs: http://10.0.2.2:8719/deb\nSuites: terzi\nComponents: main\nSigned-By: /etc/apt/keyrings/terzi.asc\n' | sudo tee /etc/apt/sources.list.d/terzi.sources >/dev/null
sudo apt-get update 2>&1 | tail -2; sudo apt-get install -y terzi-prova 2>&1 | tail -1; dpkg -l terzi-prova | tail -1" ;;
	3) vm "curl -s http://10.0.2.2:8719/terzi.asc | sudo tee /etc/pki/rpm-gpg/RPM-GPG-KEY-terzi >/dev/null
printf '[terzi]\nname=terzi\nbaseurl=http://10.0.2.2:8719/rpm/\nenabled=1\ngpgcheck=1\nrepo_gpgcheck=1\ngpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-terzi\n' | sudo tee /etc/yum.repos.d/terzi.repo >/dev/null
sudo dnf install -y terzi-prova 2>&1 | tail -2; rpm -q terzi-prova" ;;
	*) echo "terzi: only debian13 and fedora44"; exit 2 ;;
	esac 2>&1 | tee "$E/terzi.txt"
	;;
impronta)
	nome=${1:?nome}
	vm 'sudo bash -s' <"$R/t4/$IMPRONTA" >"$E/impronta-$nome.txt" 2>"$E/impronta-$nome.err"
	vm "sudo sh -c 'for f in /etc/apt/sources.list.d/* /etc/apt/keyrings/* /etc/apt/trusted.gpg.d/* /etc/apt/preferences.d/* /usr/share/keyrings/* /etc/yum.repos.d/* /etc/pki/rpm-gpg/* /etc/pacman.conf; do [ -f \$f ] && sha256sum \$f; done 2>/dev/null; ls -la /etc/apt/trusted.gpg.d 2>/dev/null; rpm -q gpg-pubkey 2>/dev/null; pacman-key --list-keys 2>/dev/null | grep -c ^pub'" >"$E/depositi-$nome.txt" 2>&1
	echo "   fingerprint \"$nome\": $(wc -l <"$E/impronta-$nome.txt") lines; repositories: $(wc -l <"$E/depositi-$nome.txt") lines"
	;;
motore)
	vm "cd /tmp && curl -sf $ARCH/engine/remotix-install -o remotix-install && curl -sf $ARCH/engine/remotix-install.sha256 -o remotix-install.sha256
sha256sum -c remotix-install.sha256; echo \"sha256: exit \$?\"
sudo install -m 755 /tmp/remotix-install /root/remotix-install
sudo /root/remotix-install version" | tee "$E/motore.txt"
	;;
script)
	# the answers: the person "prova" in the GPU groups; firewall and RPM Fusion with consent (D5,
	# D6: the engine notes those not needed on this machine)
	vm "printf 'format = remotix-answers/2\nusers = prova\nconsent.firewall = yes\n' | sudo tee /root/risposte.conf >/dev/null
[ -e /etc/fedora-release ] && echo 'consent.repo.rpmfusion = yes' | sudo tee -a /root/risposte.conf >/dev/null
cd /tmp && curl -sf $ARCH/install.sh -o install.sh && curl -sf $ARCH/install.sh.sha256 -o install.sh.sha256
sha256sum -c install.sh.sha256 && grep -E '^SHA256_MOTORE=' install.sh" >"$E/script.txt" 2>&1
	echo "   install.sh: $(grep -E 'install.sh: ' "$E/script.txt")"
	T0=$(date +%s)
	vm "cd /tmp && sudo sh install.sh --archive $ARCH --answers /root/risposte.conf" >>"$E/script.txt" 2>&1
	echo "   install.sh --answers: exit $? in $(( $(date +%s) - T0 )) s — $(grep -E '^operation |Engine VERIFIED' "$E/script.txt" | tr '\n' ' ')"
	grep -E 'FAILED|BLOCKED|RX-' "$E/script.txt" | head -8 | sed 's/^/   /'
	;;
aggiorna)
	T0=$(date +%s)
	vm "if command -v apt-get >/dev/null; then sudo apt-get update -q && sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -q; else sudo dnf upgrade -y --refresh; fi
echo \"exit: \$?\"
echo --- remotix.service:
sudo journalctl -u remotix.service --since @$T0 --no-pager -o short-unix | grep -aE 'FOUND AGAIN|ready|avvio|Stopp|Start' | tail -12" >"$E/aggiorna-$(t).txt" 2>&1
	echo "   system upgrade in $(( $(date +%s) - T0 )) s: $(grep -cE '^(Setting up|Configurazione di|  Upgrading|  Aggiornamento|  Upgraded)' "$E"/aggiorna-*.txt | tail -1) package lines"
	grep -aE 'remotix|installation certified|REMOTIX versions|RX-|exit:|FOUND AGAIN' "$E"/aggiorna-*.txt | tail -16 | cut -c1-220 | sed 's/^/   /'
	;;
disinstalla)
	vm "sudo /usr/bin/remotix-install uninstall --purge --output /root/d.json >/dev/null && sudo /usr/bin/remotix-install apply /root/d.json --approve" >"$E/disinstalla.txt" 2>&1
	echo "   uninstall: exit $? — $(grep -E '^operation ' "$E/disinstalla.txt")"
	grep -E 'FAILED|BLOCKED|RX-' "$E/disinstalla.txt" | head -6 | sed 's/^/   /'
	vm "echo \"packages left: \$( (dpkg-query -W -f='\${Package} ' 'remotix*' 2>/dev/null; rpm -qa 'remotix*' 2>/dev/null) | tr '\n' ' ')\"
echo \"archives: \$(ls /etc/apt/sources.list.d /etc/yum.repos.d 2>/dev/null | grep -ci remotix) · service: \$(systemctl is-active remotix 2>&1) · /var/lib/remotix: \$(sudo ls /var/lib/remotix 2>&1 | tr '\n' ' ')\"" | tee -a "$E/disinstalla.txt"
	;;
installa)
	canale=${1:-stabile}
	vm "sudo /root/remotix-install check --archive $ARCH --channel $canale" >"$E/verifica.txt" 2>&1; echo "   check: exit $?"
	grep -E '^Trust|^catalogue' "$E/verifica.txt" | sed 's/^/   /'
	vm "cd /tmp && sudo /root/remotix-install plan --install --archive $ARCH --channel $canale --users prova ${PIANO_OPZ:-} --output /root/piano.json" >"$E/piano.txt" 2>&1
	echo "   plan: exit $? — $(grep -c '^[0-9]*\. ' "$E/piano.txt") steps"
	vm "sudo /root/remotix-install approve /root/piano.json" >>"$E/piano.txt" 2>&1
	T0=$(date +%s)
	vm "sudo /root/remotix-install apply /root/piano.json" >"$E/applica.txt" 2>&1
	echo "   apply: exit $? in $(( $(date +%s) - T0 )) s — $(grep -E '^operation ' "$E/applica.txt")"
	grep -E 'FAILED|BLOCKED|RX-' "$E/applica.txt" | head -8 | sed 's/^/   /'
	;;
stato)
	vm "echo \"packages: \$( (dpkg-query -W -f='\${Package}=\${Version} ' remotix remotix-install remotix-archive-keyring 2>/dev/null; rpm -q remotix remotix-install remotix-selinux 2>/dev/null; pacman -Q remotix remotix-install 2>/dev/null) | tr '\n' ' ')\"
echo \"service: \$(systemctl is-enabled remotix) \$(systemctl is-active remotix) · pid \$(systemctl show -p MainPID --value remotix)\"
sudo /usr/bin/remotix-install status
sudo /usr/bin/remotix-install catalog 2>&1 | head -1
sudo /usr/bin/remotix-install certify 2>&1 | head -1
sudo sh -c 'cat /var/lib/remotix/recorded-versions.json 2>/dev/null'; echo" 2>&1 | tee "$E/stato-$(t).txt"
	;;
collega)
	rm -rf "$E/browser"; mkdir -p "$E/browser"
	T1C=$R/t1c T1C_PROGRAMMA=$QUI/t8-browser.py T1C_EVIDENZE=$E/browser \
		setsid nohup bash "$R/t1c/17-t1c-guarda.sh" "$m" "$PRX" chrome >"$E/browser.log" 2>&1 </dev/null &
	for _ in $(seq 1 120); do [ -f "$E/browser/pronto" ] && break; grep -q '^T8 ' "$E/browser.log" && break; sleep 1; done
	if [ -f "$E/browser/pronto" ]; then echo "   connected: the desktop is visible ($(t))"; else echo "   ⛔ not connected:"; tail -3 "$E/browser.log"; fi
	;;
via)
	touch "$E/browser/via"
	for _ in $(seq 1 240); do grep -q '^T8 ' "$E/browser.log" && break; sleep 1; done
	grep '^T8 ' "$E/browser.log" | cut -c1-700
	;;
palco)
	vm "for p in gnome-shell kwin_wayland plasmashell labwc; do for x in \$(pgrep -u prova -x \$p); do echo \"\$p \$x \$(ps -o lstart= -p \$x)\"; done; done
echo processes of prova: \$(pgrep -u prova | wc -l)
loginctl list-sessions --no-legend | grep prova" | tee "$E/palco-$(t).txt"
	;;
motore-cmd)
	vm "sudo /usr/bin/remotix-install $*" 2>&1 | tee -a "$E/comandi.txt"
	;;
spegni)
	$V ferma "$m" >/dev/null 2>&1; $V torna "$m" cliente >/dev/null 2>&1; echo "   $m powered off, back to \"cliente\""
	;;
*) sed -n 3,27p "$0"; exit 2 ;;
esac
