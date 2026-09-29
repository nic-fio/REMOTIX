#!/bin/bash
#
# 17-t3-rpm.sh — fase 17, T3, linea C: il PACCHETTO .rpm provato in una VM
# «cliente» di 17-vm.sh (Fedora, Alma, Tumbleweed, Leap).  Un passo per
# chiamata, cosi' ogni esito si legge prima di andare avanti.  Gemello di
# `17-t3-pacchetto.sh` (linea Arch), con dnf/zypper.
#
#   (sul server, come nicfio; la VM accesa con 17-vm.sh avvia)
#   bash 17-t3-rpm.sh <macchina> prepara            utente `prova` (gia' in `video`: R33)
#   bash 17-t3-rpm.sh <macchina> impronta <nome>    $T3/<macchina>/impronta-<nome>.txt
#   bash 17-t3-rpm.sh <macchina> installa <rpm>     copia e `dnf install` / `zypper install`, NIENT'ALTRO (R4)
#   bash 17-t3-rpm.sh <macchina> reinstalla <rpm>   `dnf reinstall` / `zypper install -f` (R5)
#   bash 17-t3-rpm.sh <macchina> r40                il pacchetto da solo non ha acceso niente (R40)
#   bash 17-t3-rpm.sh <macchina> motore             ⚠ i PASSI DEL MOTORE fatti a mano (§10.12): i gruppi
#                                                   della scheda (`17-t3-gruppi.sh iscrivi`), il servizio
#                                                   firewalld aperto se firewalld e' acceso (D6), e
#                                                   `systemctl enable --now` — niente cinture
#   bash 17-t3-rpm.sh <macchina> motore-annulla     il ritorno indietro del motore: `disable --now`, gruppi annullati
#   bash 17-t3-rpm.sh <macchina> terzi              RPM Fusion / Packman e i codec — ⚠ passo SEPARATO:
#                                                   e' la condizione di §11.1, la chiedera' il motore (D5)
#   bash 17-t3-rpm.sh <macchina> selinux [da]       stato e `ausearch -m avc` (da: «recent», «today», un'ora)
#   bash 17-t3-rpm.sh <macchina> togli              `dnf remove` / `zypper remove --clean-deps`
#   bash 17-t3-rpm.sh <macchina> confronta <a> <b>  diff delle due impronte
#
# ⛔ Fra «impronta prima» e «installa» non si tocca niente a mano: e' R4.
set -euo pipefail
m=${1:?macchina}; passo=${2:?passo}
R=/media/REMOTIX/vm17
T3=${T3:-$R/t3-rpm}
QUI=$(cd "$(dirname "$0")" && pwd)
VM() { bash "$R/17-vm.sh" ssh "$m" "$@"; }
PAROLA=${REMOTIX_PAROLA_PROVA:-prova2026}
mkdir -p "$T3/$m"

case $m in
fedora44-*) n=3;; tumbleweed-*) n=5;; leap16-*) n=6;; alma10-*) n=7;;
*) echo "macchina non della famiglia .rpm: $m"; exit 2;;
esac
case ${m#*-} in gnome) k=1;; kde) k=2;; xfce) k=3;; lxqt) k=4;; esac
PORTA_SSH=$((2300 + 10 * n + k))
O="-i $R/ssh/id_ed25519 -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
case $m in fedora44-*|alma10-*) G=dnf;; *) G=zypper;; esac
ora() { date +%H%M%S; }

copia() { # shellcheck disable=SC2086
	scp -q $O -P "$PORTA_SSH" "$1" nicfio@localhost:/var/tmp/; }

case $passo in
prepara)
	VM "id -u prova >/dev/null 2>&1 || sudo useradd -m -s /bin/bash prova
echo 'prova:$PAROLA' | sudo chpasswd
sudo gpasswd -a prova video >/dev/null
id prova" ;;
impronta)
	nome=${3:?nome}
	copia "$QUI/17-t3-impronta-rpm.sh"
	VM 'sudo bash /var/tmp/17-t3-impronta-rpm.sh' >"$T3/$m/impronta-$nome.txt"
	VM 'rm -f /var/tmp/17-t3-impronta-rpm.sh'
	wc -l "$T3/$m/impronta-$nome.txt" ;;
installa|reinstalla)
	pkg=${3:?rpm}; b=$(basename "$pkg"); copia "$pkg"
	if [ $G = dnf ]; then
		[ $passo = installa ] && c="dnf -y install" || c="dnf -y reinstall"
	else
		[ $passo = installa ] && c="zypper -n install --allow-unsigned-rpm" || c="zypper -n install -f --allow-unsigned-rpm"
	fi
	VM "sudo $c /var/tmp/$b; e=\$?; rm -f /var/tmp/$b; exit \$e" 2>&1 | tee "$T3/$m/$passo-$(ora).log" ;;
r40)
	VM 'echo "abilitato: $(systemctl is-enabled remotix.service 2>&1)  acceso: $(systemctl is-active remotix.service 2>&1)"
echo "in ascolto sulla 7447: $(sudo ss -Hlntup 2>/dev/null | grep -c ":7447 ")"
echo "cinture attive: $(ls /usr/share/polkit-1/rules.d/*remotix* /etc/polkit-1/rules.d/*remotix* /usr/lib/systemd/logind.conf.d/*remotix* /etc/systemd/logind.conf.d/*remotix* /usr/lib/systemd/sleep.conf.d/*remotix* /etc/systemd/sleep.conf.d/*remotix* 2>/dev/null | wc -l)"
echo "gruppi: $(id -nG prova)"
if systemctl -q is-active firewalld; then echo "firewalld remotix aperto: $(sudo firewall-cmd --permanent --list-services | grep -cw remotix)"; else echo "firewalld: spento"; fi' \
		| tee "$T3/$m/r40-$(ora).log" ;;
motore)
	copia "$QUI/17-t3-gruppi.sh"
	VM 'sudo sh /var/tmp/17-t3-gruppi.sh iscrivi; sudo cat /var/tmp/remotix-t3-gruppi.registro
if systemctl -q is-active firewalld; then
	echo "firewalld acceso: il servizio remotix si apre (D6, col consenso: qui a mano)"
	sudo firewall-cmd -q --reload && sudo firewall-cmd -q --permanent --add-service=remotix && sudo firewall-cmd -q --reload
	sudo firewall-cmd --list-services
fi
sudo systemctl enable --now remotix.service && sleep 3 && systemctl is-active remotix.service
sudo journalctl -u remotix.service -o cat --no-pager | grep -E "pronto:|PAM|KWin|RIPIEGO|⛔" | tail -8' \
		| tee "$T3/$m/motore-$(ora).log" ;;
motore-annulla)
	VM 'sudo systemctl disable --now remotix.service; sudo sh /var/tmp/17-t3-gruppi.sh annulla; sudo rm -f /var/tmp/17-t3-gruppi.sh
if systemctl -q is-active firewalld && sudo firewall-cmd --permanent --query-service=remotix >/dev/null 2>&1; then
	sudo firewall-cmd -q --permanent --remove-service=remotix && sudo firewall-cmd -q --reload && echo "firewalld: remotix richiuso"
fi' \
		| tee "$T3/$m/motore-annulla-$(ora).log" ;;
terzi)
	case $m in
	fedora44-*)
		VM 'sudo dnf -y -q install https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-44.noarch.rpm 2>&1 | tail -2
sudo dnf -y install libavcodec-freeworld 2>&1 | tail -3
rpm -q libavcodec-freeworld' ;;
	alma10-*)
		VM 'sudo dnf -y -q install https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-10.noarch.rpm 2>&1 | tail -2
sudo dnf -y install libavcodec-freeworld 2>&1 | tail -3; rpm -q libavcodec-freeworld' ;;
	tumbleweed-*|leap16-*)
		case $m in tumbleweed-*) u=openSUSE_Tumbleweed; l=libavcodec63;; *) u=openSUSE_Leap_16.0; l=libavcodec61;; esac
		VM "sudo zypper -n --gpg-auto-import-keys ar -cfp 90 https://ftp.gwdg.de/pub/linux/misc/packman/suse/$u/ packman 2>&1 | tail -1
sudo zypper -n --gpg-auto-import-keys refresh packman 2>&1 | tail -1
sudo zypper -n install --from packman --allow-vendor-change $l 2>&1 | tail -3
rpm -q --qf '%{NAME} %{VERSION} %{VENDOR}\n' $l" ;;
	esac 2>&1 | tee "$T3/$m/terzi-$(ora).log" ;;
selinux)
	da=${3:-today}
	VM "getenforce 2>/dev/null || cat /sys/fs/selinux/enforce; sudo ausearch -m avc,user_avc,selinux_err -ts $da 2>&1 | tail -40" \
		| tee "$T3/$m/selinux-$(ora).log" ;;
togli)
	if [ $G = dnf ]; then c="dnf -y remove remotix"; else c="zypper -n remove --clean-deps remotix"; fi
	VM "sudo $c" 2>&1 | tee "$T3/$m/togli-$(ora).log" ;;
confronta)
	a=${3:?a}; b=${4:?b}
	diff "$T3/$m/impronta-$a.txt" "$T3/$m/impronta-$b.txt" >"$T3/$m/diff-$a-$b.txt" || true
	grep -c '^[<>]' "$T3/$m/diff-$a-$b.txt" || true
	echo "$T3/$m/diff-$a-$b.txt" ;;
*) echo "passo sconosciuto: $passo"; exit 2 ;;
esac
