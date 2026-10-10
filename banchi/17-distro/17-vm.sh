#!/bin/bash
#
# REMOTIX — the virtual machines of the distributions (phase 17, the installer)
# =============================================================================
#
# One virtual machine per distribution, from the OFFICIAL «cloud» image of
# each, to test the installer where a customer would find it: real kernel,
# SELinux, firewall and boot (user's decision, 29 Sep 2026: «we are not
# measuring performance but correct operation: we move from containers
# to VMs»).  ⚠ No real graphics card: the encoding is the libx264 fallback,
# and the encoding on the card per distribution is tested separately in a box.
#
# Descends from /media/REMOTIX/vm.sh (the single VM of v1): QEMU directly, without
# libvirt and without root; user-mode networking with port forwarding; disk
# as an overlay on the base image, which stays untouched.
#
#   bash 17-vm.sh elenco                  the known distributions and their state
#   bash 17-vm.sh crea      <distro>      downloads the image, prepares disk and cloud-init
#   bash 17-vm.sh avvia     <distro>      in the background; waits for ssh and cloud-init
#   bash 17-vm.sh vesti     <macchina>    the desktop, with the official group (like the customer)
#   bash 17-vm.sh ssh       <distro> [cmd]
#   bash 17-vm.sh ferma     <distro>      orderly shutdown (then forced)
#   bash 17-vm.sh riavvia   <distro>      REAL reboot of the guest, and waits for ssh
#   bash 17-vm.sh fotografa <distro> <nome>   copy of the disk with the machine stopped
#   bash 17-vm.sh torna     <distro> <nome>   puts back the disk of the photo
#   bash 17-vm.sh azzera    <distro>      new disk from the image (cloud-init redone)
#   bash 17-vm.sh da-iso    <macchina>-iso    the ISO state: from the official ISO with the
#                                         automatic installer, new disk, UEFI; at the end the «iso» photo
#   bash 17-vm.sh impronta  <macchina> [foto] how the machine is made (firewall, SELinux, display
#                                         manager, network, packages); with [foto] it boots it from that
#                                         photo read-only, on its own ports (k=6)
#   bash 17-vm.sh schermo   <macchina> [file.png]  screenshot of the screen (from the QEMU monitor)
#   bash 17-vm.sh hmp       <macchina> "<comando>"  a monitor command (sendkey, mouse_move…)
#
# The machines are named <distro>-<desktop> (fedora44-kde; <distro> alone =
# «nudo», without desktop).  Everything lives under /media/REMOTIX/vm17/<macchina>/;
# the official image in /media/REMOTIX/vm17/<distro>/base.qcow2, shared.
# Ports on the server, for distribution N and desktop k (nudo 0, gnome 1,
# kde 2, xfce 3, lxqt 4): ssh 2300+10N+k, REMOTIX 7500+10N+k (TCP and UDP).
# The ISO state (fasi/17 §7.2) is a separate machine, <distro>-<desktop>-iso, with
# k=5, folder /media/REMOTIX/vm17/<distro>-<desktop>-iso/ and UEFI firmware.
#
set -euo pipefail
export LC_ALL=C

BASE=/media/REMOTIX
RADICE="$BASE/vm17"
CHIAVE="$RADICE/ssh/id_ed25519"
UTENTE=nicfio
CPU=${RX_VM_CPU:-4}
RAM=${RX_VM_RAM:-6144}   # MB; the load test with 8 decides whether to go down to 4096
DISCO_GRANDE=40G
OVMF_CODE=/usr/share/OVMF/OVMF_CODE_4M.fd
OVMF_VARS=/usr/share/OVMF/OVMF_VARS_4M.fd
ISO_DIR="$RADICE/iso"
RISPOSTE="$(dirname "$(readlink -f "$0")")/iso-risposte"

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
die() { printf '\n\033[1;31mERROR\033[0m %s\n' "$*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# The distributions: name | number | folder (or direct url) | file expression
#   ⚠ the order is NOT changed: the number decides the ports.
# ---------------------------------------------------------------------------
DISTRO_TAB='
debian13   | 1 | https://cloud.debian.org/images/cloud/trixie/latest/debian-13-generic-amd64.qcow2 |
ubuntu2604 | 2 | https://cloud-images.ubuntu.com/releases/26.04/release/ | ubuntu-26\.04-server-cloudimg-amd64\.img
fedora44   | 3 | https://download.fedoraproject.org/pub/fedora/linux/releases/44/Cloud/x86_64/images/ | Fedora-Cloud-Base-Generic-44-[0-9.]*\.x86_64\.qcow2
arch       | 4 | https://geo.mirror.pkgbuild.com/images/latest/Arch-Linux-x86_64-cloudimg.qcow2 |
tumbleweed | 5 | https://download.opensuse.org/tumbleweed/appliances/openSUSE-Tumbleweed-Minimal-VM.x86_64-Cloud.qcow2 |
leap16     | 6 | https://download.opensuse.org/distribution/leap/16.0/appliances/ | Leap-16\.0-Minimal-VM\.x86_64-Cloud\.qcow2
alma10     | 7 | https://repo.almalinux.org/almalinux/10/cloud/x86_64/images/AlmaLinux-10-GenericCloud-latest.x86_64.qcow2 |
ubuntu2404 | 8 | https://cloud-images.ubuntu.com/releases/24.04/release/ | ubuntu-24\.04-server-cloudimg-amd64\.img
fedora43   | 9 | https://download.fedoraproject.org/pub/fedora/linux/releases/43/Cloud/x86_64/images/ | Fedora-Cloud-Base-Generic-43-[0-9.]*\.x86_64\.qcow2
'

# The desktops: one machine per desktop (user's decision, 29 Sep: a customer usually has
#   ONE, and four together would hide the package forgotten for one of them).
#   `nudo` = the distribution as downloaded, without desktop.
#   ⚠ the order is NOT changed: it decides the ports.
DESKTOP="nudo gnome kde xfce lxqt"

riga() {  # riga <distro>[-<desktop>][-iso] -> NUM, URL, ESPR, DE, D, porte
	local nome=$1 dis de=nudo k=0 x r
	ISO=
	case "$nome" in *-iso) ISO=1; nome=${nome%-iso} ;; esac
	dis=${nome%%-*}
	DIS=$dis
	[ "$dis" != "$nome" ] && de=${nome#*-}
	for x in $DESKTOP; do [ "$x" = "$de" ] && break; k=$((k + 1)); done
	[ "$k" -lt 5 ] || die "unknown desktop: $de (one of: $DESKTOP)"
	r=$(printf '%s\n' "$DISTRO_TAB" | awk -F'|' -v OFS='|' -v d="$dis" '{gsub(/ /,"",$1)} $1==d')
	[ -n "$r" ] || die "unknown distribution: $dis (see: 17-vm.sh elenco)"
	NUM=$(printf '%s' "$r" | cut -d'|' -f2 | tr -d ' ')
	URL=$(printf '%s' "$r" | cut -d'|' -f3 | tr -d ' ')
	ESPR=$(printf '%s' "$r" | cut -d'|' -f4 | tr -d ' ')
	DE=$de; D=$dis; [ "$de" = nudo ] || D="$dis-$de"
	if [ -n "$ISO" ]; then
		[ "$de" != nudo ] || die "the ISO state wants a desktop: <distro>-<desktop>-iso"
		k=5; D="$D-iso"
	fi
	# the official image is ONE per distribution; the disk is one per machine
	BASE_IMG="$RADICE/$dis/base.qcow2"
	DIR="$RADICE/$D"; DISCO="$DIR/disco.qcow2"; SEME="${RX_VM_SEME:-$DIR/seme.iso}"
	PID="$DIR/qemu.pid"; MONITOR="$DIR/monitor.sock"; CONSOLE="$DIR/console.log"
	VARS="$DIR/ovmf-vars.fd"   # the UEFI NVRAM: it exists only for the machines that use it
	PORTA_SSH=$((2300 + 10 * NUM + k)); PORTA_RX=$((7500 + 10 * NUM + k))
}

AVVIA_EXTRA=()   # extra arguments for QEMU in cmd_avvia (impronta: -snapshot)
# For the tests of installation without questions and without network (phase 17, T9), at boot only:
#   RX_VM_SEME=file.iso     a different cloud-init seed (the test's user-data, new instance-id)
#   RX_VM_RETE=,restrict=on the network REMOVED: the VM reaches nothing outside (the forwards towards it
#                           stay: ssh and the REMOTIX port)
#   RX_VM_CATTURA=file.pcap every packet of the VM's network card, in both directions (filter-dump)
RETE_EXTRA=${RX_VM_RETE:-}
[ -n "${RX_VM_CATTURA:-}" ] && AVVIA_EXTRA+=(-object "filter-dump,id=cattura0,netdev=n0,file=$RX_VM_CATTURA")
#   RX_VM_CHI=nome          who turns it on (written in <dir>/chi; by default «pid <n>»): «avvia» on a VM
#                           turned on by SOMEONE ELSE stops with an error; RX_VM_CONDIVIDI=1 to do it on purpose
#   RX_VM_TAVOLETTA=1       a USB tablet (ABSOLUTE pointer) and a QMP monitor in <dir>/qmp.sock:
#                           «input-send-event» brings the pointer to the wanted pixel (T9, the installer
#                           window). ⚠ «mouse_move» of the HMP monitor sends only RELATIVE
#                           movements, which the tablet discards (`[M]` 30 Sep: no ABS event in the guest)
[ -n "${RX_VM_TAVOLETTA:-}" ] && AVVIA_EXTRA+=(-device qemu-xhci -device usb-tablet)

accesa() { [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; }

ssh_vm() {
	ssh -i "$CHIAVE" -p "$PORTA_SSH" -o BatchMode=yes -o ConnectTimeout=5 \
		-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR \
		"$UTENTE@localhost" "$@"
}

aspetta_ssh() {  # aspetta_ssh <secondi>
	local t=0
	until ssh_vm true 2>/dev/null; do
		accesa || die "the VM has stopped (console: $CONSOLE)"
		sleep 3; t=$((t + 3))
		[ "$t" -lt "$1" ] || die "ssh does not answer after $1 s (console: $CONSOLE)"
	done
	ok "ssh answers after ${t} s"
}

# ---------------------------------------------------------------------------
cmd_elenco() {
	printf '%-11s %-3s %-6s %-6s %s\n' distro num ssh remotix state
	printf '%s\n' "$DISTRO_TAB" | awk -F'|' 'NF>2{gsub(/ /,"",$1); print $1}' | while read -r d; do
		riga "$d"
		local s="-"
		[ -f "$DISCO" ] && s="created"
		accesa && s="ON (pid $(cat "$PID"))"
		printf '%-11s %-3s %-6s %-6s %s\n' "$d" "$NUM" "$PORTA_SSH" "$PORTA_RX" "$s"
	done
}

cmd_crea() {
	mkdir -p "$DIR" "$RADICE/ssh" "$(dirname "$BASE_IMG")"
	[ -f "$CHIAVE" ] || ssh-keygen -q -t ed25519 -N '' -C remotix-vm17 -f "$CHIAVE"

	log "$D: official image"
	if [ -f "$BASE_IMG" ]; then
		ok "already downloaded ($(du -h "$BASE_IMG" | cut -f1))"
	else
		local u="$URL"
		if [ -n "$ESPR" ]; then
			local f
			f=$(curl -fsSL "$URL" | grep -o "$ESPR" | sort -V | tail -1)
			[ -n "$f" ] || die "no file «$ESPR» in $URL"
			u="${URL%/}/$f"
		fi
		inf "downloading $u"
		curl -fL -sS -o "$BASE_IMG.parte" "$u" || die "download failed"
		mv "$BASE_IMG.parte" "$BASE_IMG"
		printf '%s\n' "$u" > "$(dirname "$BASE_IMG")/origine.txt"
		ok "downloaded ($(du -h "$BASE_IMG" | cut -f1)), sha256 $(sha256sum "$BASE_IMG" | cut -c1-16)…"
	fi

	log "$D: cloud-init"
	mkdir -p "$DIR/seme"
	printf 'instance-id: remotix-%s-%s\nlocal-hostname: rx-%s\n' "$D" "$(date +%s)" "$D" \
		> "$DIR/seme/meta-data"
	# ⚠ No group with a distribution name (sudo/wheel): sudo goes through a
	#   rule of its own. video and render must be given by the INSTALLER, not by us:
	#   the machine's service user is born without them, as at a customer's.
	cat > "$DIR/seme/user-data" <<UD
#cloud-config
hostname: rx-$D
users:
  - name: $UTENTE
    shell: /bin/bash
    sudo: ["ALL=(ALL) NOPASSWD:ALL"]
    lock_passwd: false
    ssh_authorized_keys:
      - $(cat "$CHIAVE.pub")
chpasswd:
  expire: false
  users:
    - {name: $UTENTE, password: $UTENTE, type: text}
ssh_pwauth: false
growpart: {mode: auto, devices: ['/']}
final_message: "rx-$D ready after \$UPTIME s"
UD
	genisoimage -quiet -output "$SEME" -volid cidata -joliet -rock \
		"$DIR/seme/user-data" "$DIR/seme/meta-data" || die "seme.iso not built"
	ok "seme.iso"

	log "$D: disk"
	if [ -f "$DISCO" ]; then
		ok "already present ($(du -h "$DISCO" | cut -f1) used)"
	else
		qemu-img create -q -f qcow2 -F qcow2 -b "$BASE_IMG" "$DISCO" "$DISCO_GRANDE"
		ok "overlay on the base image ($DISCO_GRANDE)"
	fi
}

# who turned the machine on: RX_VM_CHI, otherwise «pid <whoever launched this script>». ⛔ A VM
# turned on by SOMEONE ELSE is not used by two: `[M]` 30 Sep, an agent found another's VM on and
# installed on it for a few moments (before, «avvia» said «already on» and went ahead)
CHI_IO=${RX_VM_CHI:-pid $PPID}

cmd_avvia() {
	if accesa; then
		local tiene
		tiene=$(cat "$DIR/chi" 2>/dev/null || echo "unknown (turned on before the guard)")
		if [ "$tiene" = "$CHI_IO" ] || [ -n "${RX_VM_CONDIVIDI:-}" ]; then
			ok "$D already on (pid $(cat "$PID"), by «$tiene»)"
			return
		fi
		die "$D is already on and «$tiene» holds it: it is not used by two (RX_VM_CONDIVIDI=1 only if wanted)"
	fi
	[ -f "$DISCO" ] || die "disk missing: 17-vm.sh crea $D"
	[ -w /dev/kvm ] || die "/dev/kvm not writable: usermod -aG kvm $USER and log in again"
	log "$D: boot (ssh :$PORTA_SSH, REMOTIX :$PORTA_RX)"
	rm -f "$MONITOR"
	: > "$CONSOLE"
	local extra=()
	[ -f "$VARS" ] && extra+=(-drive "if=pflash,format=raw,readonly=on,file=$OVMF_CODE" \
		-drive "if=pflash,format=raw,file=$VARS")
	[ -f "$SEME" ] && extra+=(-drive "file=$SEME,if=virtio,format=raw,readonly=on")
	[ -n "${RX_VM_TAVOLETTA:-}" ] && extra+=(-qmp "unix:$DIR/qmp.sock,server=on,wait=off")
	qemu-system-x86_64 \
		-name "rx-$D" -machine q35,accel=kvm -cpu host -smp "$CPU" -m "$RAM" \
		-device virtio-vga -display none \
		-drive "file=$DISCO,if=virtio,format=qcow2,discard=unmap" \
		"${extra[@]}" "${AVVIA_EXTRA[@]}" \
		-netdev "user,id=n0,hostfwd=tcp::$PORTA_SSH-:22,hostfwd=tcp::$PORTA_RX-:7447,hostfwd=udp::$PORTA_RX-:7447$RETE_EXTRA" \
		-device virtio-net-pci,netdev=n0 \
		-device virtio-rng-pci \
		-serial "file:$CONSOLE" \
		-monitor "unix:$MONITOR,server,nowait" \
		-pidfile "$PID" -daemonize
	printf '%s\n' "$CHI_IO" >"$DIR/chi"
	ok "qemu pid $(cat "$PID"), of «$CHI_IO»"
	aspetta_ssh 600
	# cloud-init all the way through, or the tests start on a half-made machine
	ssh_vm 'command -v cloud-init >/dev/null && sudo cloud-init status --wait >/dev/null 2>&1; true'
	ok "$(ssh_vm '. /etc/os-release; printf "%s · kernel %s" "$PRETTY_NAME" "$(uname -r)"')"
}

cmd_ferma() {
	accesa || { ok "$D already off"; return; }
	log "$D: shutdown"
	printf 'system_powerdown\n' | socat - "UNIX-CONNECT:$MONITOR" >/dev/null 2>&1 \
		|| ssh_vm 'sudo systemctl poweroff' 2>/dev/null || true
	local t=0
	while accesa && [ "$t" -lt 90 ]; do sleep 2; t=$((t + 2)); done
	if accesa; then kill "$(cat "$PID")"; sleep 2; inf "forced after 90 s"; fi
	rm -f "$PID" "$DIR/chi"
	ok "off"
}

cmd_riavvia() {
	accesa || die "$D is off"
	log "$D: real reboot of the guest"
	local b0; b0=$(ssh_vm 'cat /proc/sys/kernel/random/boot_id')
	ssh_vm 'sudo systemctl reboot' 2>/dev/null || true
	sleep 5
	# RX_VM_RIAVVIA_S: the reboot patience (default 300 s); with several VMs together the
	# shutdown+reboot gets longer from contention (T10, 30 Sep: Fedora under load > 300 s)
	aspetta_ssh "${RX_VM_RIAVVIA_S:-300}"
	local b1; b1=$(ssh_vm 'cat /proc/sys/kernel/random/boot_id')
	[ "$b0" != "$b1" ] || die "boot_id unchanged: the machine did not reboot"
	ok "rebooted (boot_id changed)"
}

cmd_fotografa() {
	[ -n "${1:-}" ] || die "the photo name is missing"
	accesa && die "first: 17-vm.sh ferma $D (the photo is taken with the machine stopped)"
	cp --sparse=always "$DISCO" "$DIR/foto-$1.qcow2"
	[ -f "$VARS" ] && cp "$VARS" "$DIR/foto-$1.vars.fd"
	ok "photo «$1» ($(du -h "$DIR/foto-$1.qcow2" | cut -f1))"
}

cmd_torna() {
	[ -f "$DIR/foto-${1:-}.qcow2" ] || die "no photo «${1:-}» for $D"
	accesa && die "first: 17-vm.sh ferma $D"
	cp --sparse=always "$DIR/foto-$1.qcow2" "$DISCO"
	[ -f "$DIR/foto-$1.vars.fd" ] && cp "$DIR/foto-$1.vars.fd" "$VARS"
	ok "$D is back to the photo «$1»"
}

cmd_azzera() {
	accesa && die "first: 17-vm.sh ferma $D"
	rm -f "$DISCO"
	cmd_crea
}

# ---------------------------------------------------------------------------
# vesti: the desktop as the CUSTOMER would install it, with the distribution's
#   official package group.  ⛔ Nothing of REMOTIX in here (labwc for
#   XFCE and LXQt under Wayland, video/render groups, codecs): that is the
#   installer's job, and the test must see it missing if it forgets it.
# ---------------------------------------------------------------------------
comando_desktop() {  # prints the command for $D0 (distro) and $DE
	local fam=$1
	case "$fam:$DE" in
	debian13:*)       echo "sudo DEBIAN_FRONTEND=noninteractive apt-get update -q && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q task-$DE-desktop" ;;
	ubuntu*:gnome)    echo "sudo DEBIAN_FRONTEND=noninteractive apt-get update -q && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q ubuntu-desktop" ;;
	ubuntu*:kde)      echo "sudo DEBIAN_FRONTEND=noninteractive apt-get update -q && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q kubuntu-desktop" ;;
	ubuntu*:xfce)     echo "sudo DEBIAN_FRONTEND=noninteractive apt-get update -q && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q xubuntu-desktop" ;;
	ubuntu*:lxqt)     echo "sudo DEBIAN_FRONTEND=noninteractive apt-get update -q && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q lubuntu-desktop" ;;
	fedora*:gnome)    echo "sudo dnf -y -q group install workstation-product-environment" ;;
	fedora*:kde)      echo "sudo dnf -y -q group install kde-desktop-environment" ;;
	fedora*:xfce)     echo "sudo dnf -y -q group install xfce-desktop-environment" ;;
	fedora*:lxqt)     echo "sudo dnf -y -q group install lxqt-desktop-environment" ;;
	arch:gnome)       echo "sudo pacman -Syu --noconfirm gnome && sudo systemctl enable gdm" ;;
	arch:kde)         echo "sudo pacman -Syu --noconfirm plasma && sudo systemctl enable sddm" ;;
	arch:xfce)        echo "sudo pacman -Syu --noconfirm xfce4 xfce4-goodies lightdm lightdm-gtk-greeter && sudo systemctl enable lightdm" ;;
	arch:lxqt)        echo "sudo pacman -Syu --noconfirm lxqt breeze-icons sddm && sudo systemctl enable sddm" ;;
	tumbleweed:*|leap16:*)
		local pat=$DE; [ "$DE" = kde ] && pat=kde
		echo "sudo zypper -n --gpg-auto-import-keys install -t pattern $pat" ;;
	alma10:gnome)     echo "sudo dnf -y -q group install 'Server with GUI'" ;;
	alma10:kde)       echo "sudo dnf -y -q install epel-release && sudo dnf config-manager --set-enabled crb && sudo dnf -y -q group install 'KDE Plasma Workspaces'" ;;
	*) return 1 ;;
	esac
}

cmd_vesti() {
	[ "$DE" != nudo ] || die "$D has no desktop to dress (use <distro>-<desktop>)"
	local c
	c=$(comando_desktop "${D%%-*}") || die "$D: this distribution does not offer $DE (outside the matrix)"
	accesa || die "$D is off"
	log "$D: installing the desktop like the customer"
	inf "$c"
	local t0=$SECONDS
	ssh_vm "$c" > "$DIR/vesti.log" 2>&1 || { tail -20 "$DIR/vesti.log"; die "desktop installation failed"; }
	ssh_vm 'sudo systemctl set-default graphical.target >/dev/null 2>&1; true'
	ok "$DE installed in $((SECONDS - t0)) s ($(ssh_vm 'df -h / | tail -1' | awk '{print $3}') used)"
	ok "Wayland sessions: $(ssh_vm 'ls /usr/share/wayland-sessions 2>/dev/null | tr "
" " "')"
}

# ---------------------------------------------------------------------------
# The ISO state (fasi/17 §7.2): the machine installed from the OFFICIAL ISO with
#   the distribution's automatic installer, and its default desktop.
#   A cloud image with a desktop on top is NOT a customer's machine:
#   firewall, display manager, SELinux, network and packages are decided by the installer.
#   The answers live in iso-risposte/ next to this script; compared with the
#   default choices they only add ssh with the bench key and sudo without
#   password, and they do it INSIDE the installation.  ⛔ Nothing of REMOTIX.
#   NEW disk (not an overlay on the cloud image), UEFI firmware
#   (OVMF, own NVRAM in ovmf-vars.fd), no serial in the installed system.
# ---------------------------------------------------------------------------
# distro | official folder | checksum file (expr.) | ISO (expr.) | kernel | initrd
ISO_TAB='
debian13   | https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/ | SHA256SUMS | debian-13\.[0-9.]*-amd64-netinst\.iso | /install.amd/vmlinuz | /install.amd/initrd.gz
ubuntu2604 | https://releases.ubuntu.com/26.04/ | SHA256SUMS | ubuntu-26\.04[0-9.]*-desktop-amd64\.iso | /casper/vmlinuz | /casper/initrd
fedora44   | https://download.fedoraproject.org/pub/fedora/linux/releases/44/Everything/x86_64/iso/ | Fedora-Everything-44-[0-9.]*-x86_64-CHECKSUM | Fedora-Everything-netinst-x86_64-44-[0-9.]*\.iso | /images/pxeboot/vmlinuz | /images/pxeboot/initrd.img
arch       | https://geo.mirror.pkgbuild.com/iso/latest/ | sha256sums\.txt | archlinux-20[0-9.]*-x86_64\.iso | /arch/boot/x86_64/vmlinuz-linux | /arch/boot/x86_64/initramfs-linux.img
tumbleweed | https://download.opensuse.org/tumbleweed/iso/ | openSUSE-Tumbleweed-NET-x86_64-Current\.iso\.sha256 | openSUSE-Tumbleweed-NET-x86_64-Snapshot[0-9]*-Media\.iso | /boot/x86_64/loader/linux | /boot/x86_64/loader/initrd
alma10     | https://repo.almalinux.org/almalinux/10/isos/x86_64/ | CHECKSUM | AlmaLinux-10\.[0-9]*-x86_64-boot\.iso | /images/pxeboot/vmlinuz | /images/pxeboot/initrd.img
'
# The combinations that have written answers: one per family (§7.2)
ISO_MACCHINE="debian13-gnome ubuntu2604-gnome fedora44-gnome arch-kde tumbleweed-kde alma10-gnome"

riga_iso() {  # -> ISO_URL ISO_SOMME ISO_ESPR ISO_KERNEL ISO_INITRD
	local r
	r=$(printf '%s\n' "$ISO_TAB" | awk -F'|' -v OFS='|' -v d="$DIS" '{gsub(/ /,"",$1)} $1==d')
	[ -n "$r" ] || die "$DIS: no ISO in the table"
	ISO_URL=$(printf '%s' "$r" | cut -d'|' -f2 | tr -d ' ')
	ISO_SOMME=$(printf '%s' "$r" | cut -d'|' -f3 | tr -d ' ')
	ISO_ESPR=$(printf '%s' "$r" | cut -d'|' -f4 | tr -d ' ')
	ISO_KERNEL=$(printf '%s' "$r" | cut -d'|' -f5 | tr -d ' ')
	ISO_INITRD=$(printf '%s' "$r" | cut -d'|' -f6 | tr -d ' ')
}

scarica_iso() {  # -> ISO_FILE, downloaded and VERIFIED with the sha256 of the official site
	local somme nome atteso
	mkdir -p "$ISO_DIR"
	log "$D: the official ISO"
	somme=$(curl -fsSL "$ISO_URL" | grep -oE "$ISO_SOMME" | sort -V | tail -1)
	[ -n "$somme" ] || die "no checksum file «$ISO_SOMME» in $ISO_URL"
	# two forms: «HASH  file» (or «HASH *file») and «SHA256 (file) = HASH»
	read -r atteso nome < <(curl -fsSL "${ISO_URL%/}/$somme" | awk '
		/^SHA256 \(/ { f=$2; gsub(/[()]/, "", f); print $4, f; next }
		length($1) == 64 && NF == 2 { f=$2; sub(/^\*/, "", f); print $1, f }' |
		grep -E " $ISO_ESPR\$" | sort -k2 -V | tail -1) || true
	[ -n "${nome:-}" ] || die "no ISO «$ISO_ESPR» in $somme"
	ISO_FILE="$ISO_DIR/$nome"
	if [ -f "$ISO_FILE" ] && [ "$(cat "$ISO_FILE.sha256-ok" 2>/dev/null)" = "$atteso" ]; then
		ok "$nome (already verified)"; return
	fi
	if [ ! -f "$ISO_FILE" ]; then
		inf "downloading ${ISO_URL%/}/$nome"
		curl -fL -sS -o "$ISO_FILE.parte" "${ISO_URL%/}/$nome" || die "download failed"
		mv "$ISO_FILE.parte" "$ISO_FILE"
	fi
	inf "verifying the sha256 ($somme)"
	[ "$(sha256sum "$ISO_FILE" | cut -d' ' -f1)" = "$atteso" ] || {
		mv "$ISO_FILE" "$ISO_FILE.sbagliata"; die "$nome: sha256 different from the official one"; }
	printf '%s\n' "$atteso" > "$ISO_FILE.sha256-ok"
	printf '%s\n' "${ISO_URL%/}/$nome" > "$ISO_FILE.origine"
	ok "$nome, sha256 ${atteso:0:16}… as per $somme"
}

prepara_risposte() {  # the installer's answers in $DIR/risposte, served over HTTP
	local r="$DIR/risposte" hash chiave
	rm -rf "$r"; mkdir -p "$r"
	hash=$(openssl passwd -6 "$UTENTE")
	chiave=$(cat "$CHIAVE.pub")
	riempi() {
		[ -f "$RISPOSTE/$1" ] || die "$RISPOSTE/$1 is missing"
		sed -e "s|@UTENTE@|$UTENTE|g" -e "s|@HASH@|$hash|g" -e "s|@CHIAVE@|$chiave|g" \
			-e "s|@NOME@|rx-$D|g" -e "s|@WEB@|$WEB|g" "$RISPOSTE/$1" > "$r/$2"
	}
	case "$DIS" in
	debian13)   riempi debian13.preseed preseed.cfg ;;
	ubuntu2604) riempi ubuntu2604.user-data user-data; : > "$r/meta-data"; : > "$r/vendor-data" ;;
	fedora44)   riempi fedora44.ks ks.cfg ;;
	alma10)     riempi alma10.ks ks.cfg ;;
	arch)       riempi arch.sh installa.sh; riempi arch.config.json config.json
	            riempi arch.creds.json creds.json ;;
	tumbleweed) riempi tumbleweed.xml autoinst.xml ;;
	*) die "$DIS: no written answers" ;;
	esac
	ok "answers: $(ls "$r" | tr '\n' ' ')"
}

comando_iso() {  # the installer's kernel line (no serial: it would stay in the system)
	case "$DIS" in
	debian13)   echo "auto=true priority=critical url=$WEB/preseed.cfg locale=it_IT.UTF-8 keymap=it hostname=rx-$D domain= ---" ;;
	ubuntu2604) echo "autoinstall ds=nocloud;s=$WEB/ noprompt --- quiet splash" ;;
	fedora44|alma10) echo "inst.stage2=hd:LABEL=$ETICHETTA inst.ks=$WEB/ks.cfg" ;;
	arch)       echo "archisobasedir=arch archisosearchuuid=$ARCH_UUID script=$WEB/installa.sh" ;;
	tumbleweed) echo "autoyast=$WEB/autoinst.xml splash=silent" ;;
	esac
}

monitor() {  # monitor <HMP command>: without socat, which is not on the server
	python3 - "$MONITOR" "$1" <<'PY'
import socket, sys, time
s = socket.socket(socket.AF_UNIX); s.settimeout(3); s.connect(sys.argv[1])
time.sleep(0.3)
try: s.recv(65536)
except Exception: pass
s.sendall((sys.argv[2] + "\n").encode()); time.sleep(1.5)
try: sys.stdout.write(s.recv(65536).decode(errors="replace"))
except Exception: pass
PY
}

cmd_hmp() {  # a QEMU monitor command (sendkey, mouse_move, mouse_button…)
	accesa || die "$D is off"
	monitor "$*"
}

cmd_schermo() {
	accesa || die "$D is off"
	local f=${1:-$DIR/schermo.png}
	rm -f "$f"
	monitor "screendump $f -f png" >/dev/null
	[ -s "$f" ] || die "screenshot not taken"
	ok "screenshot: $f"
}

cmd_da_iso() {
	[ -n "$ISO" ] || die "usage: 17-vm.sh da-iso <distro>-<desktop>-iso (one of: $ISO_MACCHINE)"
	case " $ISO_MACCHINE " in *" ${D%-iso} "*) ;; *) die "${D%-iso}: no written answers (one of: $ISO_MACCHINE)" ;; esac
	accesa && die "$D is on: first 17-vm.sh ferma $D"
	[ -w /dev/kvm ] || die "/dev/kvm not writable: usermod -aG kvm $USER and log in again"
	local t0=$SECONDS
	mkdir -p "$DIR" "$RADICE/ssh"
	[ -f "$CHIAVE" ] || ssh-keygen -q -t ed25519 -N '' -C remotix-vm17 -f "$CHIAVE"
	riga_iso
	scarica_iso

	log "$D: kernel and initrd of the installer, from the ISO"
	isoinfo -R -i "$ISO_FILE" -x "$ISO_KERNEL" > "$DIR/iso-kernel"
	isoinfo -R -i "$ISO_FILE" -x "$ISO_INITRD" > "$DIR/iso-initrd"
	[ -s "$DIR/iso-kernel" ] && [ -s "$DIR/iso-initrd" ] || die "kernel or initrd not found in the ISO"
	ETICHETTA=$(isoinfo -d -i "$ISO_FILE" | sed -n 's/^Volume id: //p')
	ARCH_UUID=$(isoinfo -R -f -i "$ISO_FILE" | sed -n 's|^/boot/\(.*\)\.uuid$|\1|p' | head -1)
	ok "label «$ETICHETTA»"
	PORTA_WEB=$((18300 + 10 * NUM + 5))
	WEB="http://10.0.2.2:$PORTA_WEB"     # 10.0.2.2 is the server as seen from QEMU's user network
	prepara_risposte
	local riga_k; riga_k=$(comando_iso)
	inf "kernel: $riga_k"
	if [ -n "${RX_ISO_SOLO_PREPARA:-}" ]; then
		ok "prepared without turning anything on (RX_ISO_SOLO_PREPARA)"; return
	fi

	log "$D: NEW disk ($DISCO_GRANDE) and new UEFI NVRAM"
	rm -f "$DISCO" "$VARS" "$PID"
	qemu-img create -q -f qcow2 "$DISCO" "$DISCO_GRANDE"
	cp "$OVMF_VARS" "$VARS"
	ok "done"

	python3 -m http.server "$PORTA_WEB" --bind 127.0.0.1 --directory "$DIR/risposte" \
		> "$DIR/web.log" 2>&1 &
	local web=$!
	# shellcheck disable=SC2064
	trap "kill $web 2>/dev/null" EXIT
	sleep 1
	kill -0 "$web" 2>/dev/null || die "the answer server does not start (port $PORTA_WEB busy? another da-iso?): $DIR/web.log"

	log "$D: automatic installation from the ISO (without screen; to watch: 17-vm.sh schermo $D)"
	: > "$CONSOLE"; rm -f "$MONITOR"
	qemu-system-x86_64 \
		-name "rx-$D" -machine q35,accel=kvm -cpu host -smp "$CPU" -m "$RAM" \
		-device virtio-vga -display none \
		-drive "if=pflash,format=raw,readonly=on,file=$OVMF_CODE" \
		-drive "if=pflash,format=raw,file=$VARS" \
		-drive "file=$DISCO,if=virtio,format=qcow2,discard=unmap" \
		-drive "file=$ISO_FILE,media=cdrom,readonly=on" \
		-kernel "$DIR/iso-kernel" -initrd "$DIR/iso-initrd" -append "$riga_k" \
		-netdev "user,id=n0,hostfwd=tcp::$PORTA_SSH-:22" \
		-device virtio-net-pci,netdev=n0 \
		-device virtio-rng-pci \
		-serial "file:$CONSOLE" \
		-monitor "unix:$MONITOR,server,nowait" \
		-no-reboot -pidfile "$PID" -daemonize
	ok "qemu pid $(cat "$PID"); at the end of installation the installer reboots and QEMU exits (-no-reboot)"
	local limite=${RX_ISO_ATTESA:-10800} t=0
	while accesa; do
		sleep 30; t=$((t + 30))
		[ $((t % 600)) -ne 0 ] || inf "$((t / 60)) min: disk $(du -h "$DISCO" | cut -f1)"
		if [ "$t" -ge "$limite" ]; then
			cmd_schermo "$DIR/schermo-scaduto.png" || true
			kill "$(cat "$PID")"; die "installation not finished in $limite s (screenshot: $DIR/schermo-scaduto.png)"
		fi
	done
	rm -f "$PID"
	kill "$web" 2>/dev/null; trap - EXIT
	local t_inst=$((SECONDS - t0))
	grep -q '" 200 ' "$DIR/web.log" || die "the installer never asked for the answers (web.log)"
	! grep -q 'RX-ESITO: FALLITA' "$CONSOLE" || die "the installer says FALLITA (console: $CONSOLE)"
	[ "$(du -k "$DISCO" | cut -f1)" -gt 1500000 ] || die "disk almost empty ($(du -h "$DISCO" | cut -f1)): installation not done"
	ok "installation finished in $((t_inst / 60)) min ($(du -h "$DISCO" | cut -f1) on the disk)"

	log "$D: first boot from the installed disk"
	cmd_avvia
	ssh_vm 'sudo -n true' || die "passwordless sudo does not work"
	ok "passwordless sudo"
	# that the machine got to the end of boot, desktop included
	if ssh_vm 'timeout 300 systemctl is-system-running --wait >/dev/null 2>&1; systemctl is-active graphical.target' | grep -qx active; then
		ok "graphical.target reached"
	else
		inf "⚠ graphical.target NOT active"
	fi
	cmd_impronta
	cmd_ferma
	cmd_fotografa iso
	printf 'date %s\nISO %s\ninstallation %s s\nin all %s s\n' "$(date -Is)" \
		"$(basename "$ISO_FILE")" "$t_inst" "$((SECONDS - t0))" > "$DIR/da-iso.txt"
	ok "$D ready, photo «iso», in all $(((SECONDS - t0) / 60)) min"
}

# ---------------------------------------------------------------------------
# impronta: how the machine is made, to compare ISO and DESKTOP (§7.2).
#   With a photo the machine boots FROM THAT PHOTO with -snapshot (the disk is not
#   touched, nor is the machine of whoever is using it) and on its own ports (k=6).
# ---------------------------------------------------------------------------
IMPRONTA='
set +e
. /etc/os-release
v() { printf "%-18s %s\n" "$1:" "$2"; }
v system "$PRETTY_NAME, kernel $(uname -r)"
v firmware "$([ -d /sys/firmware/efi ] && echo UEFI || echo BIOS)"
v lsm "$(cat /sys/kernel/security/lsm 2>/dev/null)"
v selinux "$(if [ -r /sys/fs/selinux/enforce ]; then [ "$(cat /sys/fs/selinux/enforce)" = 1 ] && echo Enforcing || echo Permissive; else echo absent; fi)"
v apparmor "$(sudo aa-status --enabled 2>/dev/null && echo active || echo off/absent)"
v firewalld "$(systemctl is-enabled firewalld 2>/dev/null | head -1) / $(systemctl is-active firewalld 2>/dev/null)"
v "other firewalls" "$(for u in ufw nftables iptables; do systemctl is-enabled $u >/dev/null 2>&1 && printf "%s " $u; done)"
[ "$(systemctl is-active firewalld 2>/dev/null)" = active ] && v "  zone" "$(sudo firewall-cmd --get-default-zone): services [$(sudo firewall-cmd --list-services)] ports [$(sudo firewall-cmd --list-ports)]"
v ufw "$(command -v ufw >/dev/null && sudo ufw status | head -1 || echo absent)"
v nft "$(sudo nft list ruleset 2>/dev/null | grep -c . ) rule lines"
dm=$(readlink -f /etc/systemd/system/display-manager.service 2>/dev/null)
v "display manager" "${dm##*/}"
v "autologin" "$(grep -hsiE "^[[:space:]]*(AutomaticLoginEnable|AutomaticLogin|User|Session)[[:space:]]*=|^DISPLAYMANAGER(_AUTOLOGIN)?=" /etc/gdm/custom.conf /etc/gdm3/custom.conf /etc/gdm3/daemon.conf /etc/sddm.conf /etc/sddm.conf.d/* /etc/sysconfig/displaymanager 2>/dev/null | tr "\n" " ")"
v "wayland sessions" "$(ls /usr/share/wayland-sessions 2>/dev/null | tr "\n" " ")"
v "x11 sessions" "$(ls /usr/share/xsessions 2>/dev/null | tr "\n" " ")"
v "target" "$(systemctl get-default)"
v network "NetworkManager=$(systemctl is-active NetworkManager) networkd=$(systemctl is-active systemd-networkd) wicked=$(systemctl is-active wicked 2>/dev/null) netplan=[$(ls /etc/netplan 2>/dev/null | tr "\n" " ")]"
v resolved "$(systemctl is-active systemd-resolved)"
v sshd "$(for u in ssh sshd; do x=$(systemctl is-enabled $u 2>/dev/null) && { echo "$u $x"; break; }; done)"
v cloud-init "$(command -v cloud-init >/dev/null && echo present || echo absent)"
v packages "$( (dpkg-query -W 2>/dev/null || rpm -qa 2>/dev/null || pacman -Q 2>/dev/null) | wc -l)"
v flatpak "$(command -v flatpak >/dev/null && flatpak remotes --columns=name 2>/dev/null | tr "\n" " " || echo absent)"
v snap "$(command -v snap >/dev/null && snap list 2>/dev/null | awk "NR>1{print \$1}" | tr "\n" " " || echo absent)"
v root-fs "$(findmnt -no FSTYPE /) on $(findmnt -no SOURCE /)"
v swap "$(sudo swapon --show=NAME,TYPE --noheadings | tr -s " " | tr "\n" " ")"
v language "$(localectl status | sed -n "s/.*LANG=//p") / keyboard $(localectl status | sed -n "s/.*X11 Layout: //p")"
v timezone "$(timedatectl show -p Timezone --value)"
v "user groups" "$(id -nG)"
v "human users" "$(awk -F: "\$3>=1000 && \$3<60000 {print \$1}" /etc/passwd | tr "\n" " ")"
v "root" "$(sudo passwd -S root 2>/dev/null | cut -d" " -f2)"
v faillock "$(grep -lsr pam_faillock /etc/pam.d /usr/lib/pam.d 2>/dev/null | wc -l) PAM files"
v pipewire "$(systemctl --global is-enabled pipewire.socket 2>/dev/null)"
v "enabled units" "$(systemctl list-unit-files --state=enabled --no-legend | wc -l)"
v snapper "$(command -v snapper >/dev/null && sudo snapper list-configs 2>/dev/null | awk "NR>2{print \$1}" | tr "\n" " " || echo absent) $(command -v snapper >/dev/null && echo "($(sudo snapper list 2>/dev/null | grep -c "^ *[0-9]") snapshots)")"
v recommends "apt=$(apt-config dump APT::Install-Recommends 2>/dev/null | sed -n "s/.*\"\(.*\)\";/\1/p") zypp.onlyRequires=$(grep -hsE "^[[:space:]]*solver.onlyRequires" /etc/zypp/zypp.conf /etc/zypp/zypp.conf.d/* /usr/etc/zypp/zypp.conf /usr/etc/zypp/zypp.conf.d/* 2>/dev/null | tr -d " " | tr "\n" " ") dnf=$(grep -hs install_weak_deps /etc/dnf/dnf.conf /etc/dnf/libdnf5.conf.d/* 2>/dev/null | tr -d " " | tr "\n" " ")"
v "video/render groups" "$(getent group video render | cut -d: -f1,4 | tr "\n" " ")"
v "listening" "$(sudo ss -Hltnu 2>/dev/null | awk "{print \$1\"/\"\$5}" | sort -u | tr "\n" " ")"
'

cmd_impronta() {
	local foto=${1:-} nome=attuale
	if [ -n "$foto" ]; then
		[ -f "$DIR/foto-$foto.qcow2" ] || die "no photo «$foto» for $D"
		nome=$foto
		DISCO="$DIR/foto-$foto.qcow2"; PID="$DIR/impronta.pid"; MONITOR="$DIR/impronta.sock"
		CONSOLE="$DIR/impronta-console.log"
		if [ -f "$DIR/foto-$foto.vars.fd" ]; then
			cp "$DIR/foto-$foto.vars.fd" "$DIR/impronta-vars.fd"; VARS="$DIR/impronta-vars.fd"
		fi
		PORTA_SSH=$((2300 + 10 * NUM + 6)); PORTA_RX=$((7500 + 10 * NUM + 6))
		D="$D-impronta"
		AVVIA_EXTRA=(-snapshot)
		cmd_avvia
		# shellcheck disable=SC2064
		trap "kill \$(cat '$PID') 2>/dev/null; rm -f '$PID'" EXIT
	fi
	accesa || die "$D is off"
	log "$D: fingerprint ($nome)"
	ssh_vm "$IMPRONTA" | tee "$DIR/impronta-$nome.txt"
	ssh_vm '(dpkg-query -W -f="\${Package}\n" 2>/dev/null || rpm -qa --qf "%{NAME}\n" 2>/dev/null || pacman -Qq) | sort -u' \
		> "$DIR/pacchetti-$nome.txt"
	ssh_vm 'systemctl list-unit-files --state=enabled --no-legend | cut -d" " -f1 | sort' > "$DIR/unita-$nome.txt"
	ok "in $DIR/{impronta,pacchetti,unita}-$nome.txt"
	if [ -n "$foto" ]; then
		kill "$(cat "$PID")" 2>/dev/null; rm -f "$PID"; trap - EXIT
		ok "off (the -snapshot changes go away with it)"
	fi
}

# ---------------------------------------------------------------------------
c=${1:-}; shift || true
case "$c" in
elenco) cmd_elenco ;;
crea|avvia|ferma|riavvia|azzera|vesti)
	riga "${1:?the distribution is missing}"; shift; "cmd_$c" "$@" ;;
fotografa|torna)
	riga "${1:?the distribution is missing}"; shift; "cmd_$c" "$@" ;;
ssh)
	riga "${1:?the distribution is missing}"; shift; ssh_vm "$@" ;;
da-iso)
	riga "${1:?the machine is missing (<distro>-<desktop>-iso)}"; shift; cmd_da_iso "$@" ;;
impronta|schermo|hmp)
	riga "${1:?the machine is missing}"; shift; "cmd_$c" "$@" ;;
*) sed -n '2,42p' "$0"; exit 2 ;;
esac
