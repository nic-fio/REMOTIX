#!/bin/bash
#
# 17-amministratore.sh — quel che l'AMMINISTRATORE fa prima di installare REMOTIX (DECISIONI §10.36:
# REMOTIX non modifica il sistema, `check` dice cosa manca e provvede lui). Gira DENTRO la macchina,
# da root, mandato da 17-t10.sh:
#
#     ssh … 'sudo bash -s <macchina> <porta>' < 17-amministratore.sh
#        es. fedora44-xfce 7447
#
# Che cosa mette, e da dove viene la ricetta: sono i comandi che il motore eseguiva o suggeriva fino
# al catalogo 2026.10.10.12 (git show 890f133:installatore/catalogo/catalogo.json), spostati qui.
# ⛔ Non è parte del prodotto: è il banco che fa la parte della persona.
#   - gli archivi di terzi e i driver con H.264 della scheda di questa macchina (Fedora: RPM Fusion,
#     Intel intel-media-driver, AMD mesa-va-drivers-freeworld; Alma: EPEL con CRB, e RPM Fusion per
#     Intel; openSUSE con AMD: la Mesa di Packman);
#   - il driver Vulkan delle AMD dove la RADV ufficiale codifica (Debian, Ubuntu, Arch);
#   (labwc, wlr-randr, breeze6-wallpapers e il carattere scalabile NON li mette lui: sono dipendenze di
#   REMOTIX, li installa il gestore insieme a REMOTIX — utente, 10 ott 2026, DECISIONI §10.36);
#   - la porta di REMOTIX nel firewall, TCP e UDP (firewalld o ufw, se acceso).
# Ogni comando si scrive prima di farlo: il giornale è la prova di che cosa l'amministratore ha fatto.
set -uo pipefail
m=${1:?macchina}; porta=${2:-7447}
distro=${m%%-*}; desktop=${m#*-}; desktop=${desktop%-iso}
fai() { echo "+ $*"; "$@"; }
forn=""
for v in /sys/class/drm/renderD*/device/vendor; do
	case $(cat "$v" 2>/dev/null) in 0x8086) forn="$forn Intel" ;; 0x1002) forn="$forn AMD" ;; 0x10de) forn="$forn NVIDIA" ;; esac
done
echo "== $m · schede:${forn:- nessuna} · porta $porta"
ha() { case " $forn " in *" $1 "*) return 0 ;; esac; return 1; }
comp=""
case $distro in
debian13 | ubuntu2604)
	export DEBIAN_FRONTEND=noninteractive
	fai apt-get update -q
	ha AMD && comp="$comp mesa-vulkan-drivers"
	[ -n "$comp" ] && fai apt-get install -y -q $comp
	;;
fedora44)
	fai dnf install -y "https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm" \
		"https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm"
	ha Intel && fai dnf install -y intel-media-driver
	ha AMD && fai dnf swap -y mesa-va-drivers mesa-va-drivers-freeworld
	;;
alma10)
	fai dnf install -y epel-release
	fai dnf config-manager --set-enabled crb
	if ha Intel; then
		fai dnf install -y "https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-$(rpm -E %rhel).noarch.rpm" \
			"https://mirrors.rpmfusion.org/nonfree/el/rpmfusion-nonfree-release-$(rpm -E %rhel).noarch.rpm"
		fai dnf install -y intel-media-driver
	fi
	;;
tumbleweed | leap16)
	[ "$distro" = tumbleweed ] && dir=openSUSE_Tumbleweed || dir=openSUSE_Leap_16.0
	if ha AMD; then
		fai zypper --non-interactive ar -cfp 90 "https://ftp.gwdg.de/pub/linux/misc/packman/suse/$dir/" packman
		fai zypper --non-interactive --gpg-auto-import-keys refresh packman
		fai zypper --non-interactive install --from packman --allow-vendor-change Mesa-dri Mesa-libva libvulkan_radeon
	fi
	;;
arch)
	ha AMD && comp="$comp vulkan-radeon"
	[ -n "$comp" ] && fai pacman -S --needed --noconfirm $comp
	;;
*) echo "⛔ macchina sconosciuta: $m"; exit 2 ;;
esac
if systemctl is-active -q firewalld 2>/dev/null; then
	fai firewall-cmd --permanent --add-port="$porta/tcp" --add-port="$porta/udp"
	fai firewall-cmd --reload
elif command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q 'Status: active'; then
	fai ufw allow "$porta/tcp"
	fai ufw allow "$porta/udp"
fi
echo "== fatto"
