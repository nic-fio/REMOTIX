#!/bin/bash
#
# 17-amministratore.sh — what the ADMINISTRATOR does before installing REMOTIX (DECISIONI §10.36:
# REMOTIX does not modify the system, `check` says what is missing and he provides it). Runs INSIDE the
# machine, as root, sent by 17-t10.sh:
#
#     ssh … 'sudo bash -s <macchina> <porta>' < 17-amministratore.sh
#        e.g. fedora44-xfce 7447
#
# What it puts in, and where the recipe comes from: these are the commands the engine ran or suggested
# up to catalogue 2026.10.10.12 (git show 890f133:installatore/catalogo/catalogo.json), moved here.
# ⛔ It is not part of the product: it is the bench playing the person.
#   - the third-party repositories and the H.264 drivers for this machine's card (Fedora: RPM Fusion,
#     Intel intel-media-driver, AMD mesa-va-drivers-freeworld; Alma: EPEL with CRB, and RPM Fusion for
#     Intel; openSUSE with AMD: the Packman Mesa);
#   - the AMD Vulkan driver where the official RADV encodes (Debian, Ubuntu, Arch);
#   (labwc, wlr-randr, breeze6-wallpapers and the scalable font are NOT put in by him: they are
#   dependencies of REMOTIX, the package manager installs them together with REMOTIX — user,
#   10 Oct 2026, DECISIONI §10.36);
#   - the REMOTIX port in the firewall, TCP and UDP (firewalld or ufw, if on).
# Every command is written before it is run: the journal is the proof of what the administrator did.
set -uo pipefail
m=${1:?machine}; porta=${2:-7447}
distro=${m%%-*}; desktop=${m#*-}; desktop=${desktop%-iso}
fai() { echo "+ $*"; "$@"; }
forn=""
for v in /sys/class/drm/renderD*/device/vendor; do
	case $(cat "$v" 2>/dev/null) in 0x8086) forn="$forn Intel" ;; 0x1002) forn="$forn AMD" ;; 0x10de) forn="$forn NVIDIA" ;; esac
done
echo "== $m · cards:${forn:- none} · port $porta"
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
*) echo "⛔ unknown machine: $m"; exit 2 ;;
esac
if systemctl is-active -q firewalld 2>/dev/null; then
	fai firewall-cmd --permanent --add-port="$porta/tcp" --add-port="$porta/udp"
	fai firewall-cmd --reload
elif command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q 'Status: active'; then
	fai ufw allow "$porta/tcp"
	fai ufw allow "$porta/udp"
fi
echo "== done"
