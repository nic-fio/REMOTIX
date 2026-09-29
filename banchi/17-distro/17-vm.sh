#!/bin/bash
#
# REMOTIX — le macchine virtuali delle distribuzioni (fase 17, l'installatore)
# ============================================================================
#
# Una macchina virtuale per distribuzione, dall'immagine «cloud» UFFICIALE di
# ognuna, per provare l'installatore dove lo troverebbe un cliente: kernel,
# SELinux, firewall e avvio veri (decisione dell'utente, 29 set 2026: «non
# misuriamo le prestazioni ma il corretto funzionamento: passiamo dai container
# alle VM»).  ⚠ Niente scheda grafica vera: la codifica e' il ripiego libx264,
# e la codifica sulla scheda per distribuzione si prova a parte in una scatola.
#
# Discende da /media/REMOTIX/vm.sh (la VM unica di v1): QEMU diretto, senza
# libvirt e senza root; rete in modalita' utente con inoltro delle porte; disco
# come sovrapposizione sull'immagine di base, che resta intatta.
#
#   bash 17-vm.sh elenco                  le distribuzioni conosciute e lo stato
#   bash 17-vm.sh crea      <distro>      scarica l'immagine, prepara disco e cloud-init
#   bash 17-vm.sh avvia     <distro>      in secondo piano; aspetta ssh e cloud-init
#   bash 17-vm.sh vesti     <macchina>    il desktop, col gruppo ufficiale (come il cliente)
#   bash 17-vm.sh ssh       <distro> [cmd]
#   bash 17-vm.sh ferma     <distro>      spegnimento ordinato (poi forzato)
#   bash 17-vm.sh riavvia   <distro>      riavvio VERO dell'ospite, e aspetta ssh
#   bash 17-vm.sh fotografa <distro> <nome>   copia del disco a macchina ferma
#   bash 17-vm.sh torna     <distro> <nome>   rimette il disco della foto
#   bash 17-vm.sh azzera    <distro>      disco nuovo dall'immagine (cloud-init rifatto)
#
# Le macchine si chiamano <distro>-<desktop> (fedora44-kde; <distro> da sola =
# «nudo», senza desktop).  Tutto sta sotto /media/REMOTIX/vm17/<macchina>/;
# l'immagine ufficiale in /media/REMOTIX/vm17/<distro>/base.qcow2, condivisa.
# Porte sul server, per la distribuzione N e il desktop k (nudo 0, gnome 1,
# kde 2, xfce 3, lxqt 4): ssh 2300+10N+k, REMOTIX 7500+10N+k (TCP e UDP).
#
set -euo pipefail
export LC_ALL=C

BASE=/media/REMOTIX
RADICE="$BASE/vm17"
CHIAVE="$RADICE/ssh/id_ed25519"
UTENTE=nicfio
CPU=${RX_VM_CPU:-4}
RAM=${RX_VM_RAM:-6144}   # MB; la prova di carico da 8 decide se scendere a 4096
DISCO_GRANDE=40G

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
die() { printf '\n\033[1;31mERRORE\033[0m %s\n' "$*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Le distribuzioni: nome | numero | cartella (o url diretto) | espressione del file
#   ⚠ l'ordine NON si cambia: il numero decide le porte.
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

# I desktop: una macchina per desktop (decisione dell'utente, 29 set: un cliente ne ha
#   di solito UNO, e quattro insieme nasconderebbero il pacchetto dimenticato per uno).
#   `nudo` = la distribuzione com'e' scaricata, senza desktop.
#   ⚠ l'ordine NON si cambia: decide le porte.
DESKTOP="nudo gnome kde xfce lxqt"

riga() {  # riga <distro>[-<desktop>] -> NUM, URL, ESPR, DE, D, porte
	local nome=$1 dis de=nudo k=0 x r
	dis=${nome%%-*}
	[ "$dis" != "$nome" ] && de=${nome#*-}
	for x in $DESKTOP; do [ "$x" = "$de" ] && break; k=$((k + 1)); done
	[ "$k" -lt 5 ] || die "desktop sconosciuto: $de (uno di: $DESKTOP)"
	r=$(printf '%s\n' "$DISTRO_TAB" | awk -F'|' -v OFS='|' -v d="$dis" '{gsub(/ /,"",$1)} $1==d')
	[ -n "$r" ] || die "distribuzione sconosciuta: $dis (vedi: 17-vm.sh elenco)"
	NUM=$(printf '%s' "$r" | cut -d'|' -f2 | tr -d ' ')
	URL=$(printf '%s' "$r" | cut -d'|' -f3 | tr -d ' ')
	ESPR=$(printf '%s' "$r" | cut -d'|' -f4 | tr -d ' ')
	DE=$de; D=$dis; [ "$de" = nudo ] || D="$dis-$de"
	# l'immagine ufficiale e' UNA per distribuzione; il disco e' uno per macchina
	BASE_IMG="$RADICE/$dis/base.qcow2"
	DIR="$RADICE/$D"; DISCO="$DIR/disco.qcow2"; SEME="$DIR/seme.iso"
	PID="$DIR/qemu.pid"; MONITOR="$DIR/monitor.sock"; CONSOLE="$DIR/console.log"
	PORTA_SSH=$((2300 + 10 * NUM + k)); PORTA_RX=$((7500 + 10 * NUM + k))
}

accesa() { [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; }

ssh_vm() {
	ssh -i "$CHIAVE" -p "$PORTA_SSH" -o BatchMode=yes -o ConnectTimeout=5 \
		-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR \
		"$UTENTE@localhost" "$@"
}

aspetta_ssh() {  # aspetta_ssh <secondi>
	local t=0
	until ssh_vm true 2>/dev/null; do
		accesa || die "la VM si e' fermata (console: $CONSOLE)"
		sleep 3; t=$((t + 3))
		[ "$t" -lt "$1" ] || die "ssh non risponde dopo $1 s (console: $CONSOLE)"
	done
	ok "ssh risponde dopo ${t} s"
}

# ---------------------------------------------------------------------------
cmd_elenco() {
	printf '%-11s %-3s %-6s %-6s %s\n' distro num ssh remotix stato
	printf '%s\n' "$DISTRO_TAB" | awk -F'|' 'NF>2{gsub(/ /,"",$1); print $1}' | while read -r d; do
		riga "$d"
		local s="-"
		[ -f "$DISCO" ] && s="creata"
		accesa && s="ACCESA (pid $(cat "$PID"))"
		printf '%-11s %-3s %-6s %-6s %s\n' "$d" "$NUM" "$PORTA_SSH" "$PORTA_RX" "$s"
	done
}

cmd_crea() {
	mkdir -p "$DIR" "$RADICE/ssh" "$(dirname "$BASE_IMG")"
	[ -f "$CHIAVE" ] || ssh-keygen -q -t ed25519 -N '' -C remotix-vm17 -f "$CHIAVE"

	log "$D: immagine ufficiale"
	if [ -f "$BASE_IMG" ]; then
		ok "gia' scaricata ($(du -h "$BASE_IMG" | cut -f1))"
	else
		local u="$URL"
		if [ -n "$ESPR" ]; then
			local f
			f=$(curl -fsSL "$URL" | grep -o "$ESPR" | sort -V | tail -1)
			[ -n "$f" ] || die "nessun file «$ESPR» in $URL"
			u="${URL%/}/$f"
		fi
		inf "scarico $u"
		curl -fL -sS -o "$BASE_IMG.parte" "$u" || die "scaricamento fallito"
		mv "$BASE_IMG.parte" "$BASE_IMG"
		printf '%s\n' "$u" > "$(dirname "$BASE_IMG")/origine.txt"
		ok "scaricata ($(du -h "$BASE_IMG" | cut -f1)), sha256 $(sha256sum "$BASE_IMG" | cut -c1-16)…"
	fi

	log "$D: cloud-init"
	mkdir -p "$DIR/seme"
	printf 'instance-id: remotix-%s-%s\nlocal-hostname: rx-%s\n' "$D" "$(date +%s)" "$D" \
		> "$DIR/seme/meta-data"
	# ⚠ Nessun gruppo con nome di distribuzione (sudo/wheel): sudo passa da una
	#   regola propria. video e render li deve dare l'INSTALLATORE, non noi:
	#   l'utente di servizio della macchina nasce senza, come da un cliente.
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
final_message: "rx-$D pronta dopo \$UPTIME s"
UD
	genisoimage -quiet -output "$SEME" -volid cidata -joliet -rock \
		"$DIR/seme/user-data" "$DIR/seme/meta-data" || die "seme.iso non costruito"
	ok "seme.iso"

	log "$D: disco"
	if [ -f "$DISCO" ]; then
		ok "gia' presente ($(du -h "$DISCO" | cut -f1) usati)"
	else
		qemu-img create -q -f qcow2 -F qcow2 -b "$BASE_IMG" "$DISCO" "$DISCO_GRANDE"
		ok "sovrapposizione sull'immagine di base ($DISCO_GRANDE)"
	fi
}

cmd_avvia() {
	accesa && { ok "$D gia' accesa (pid $(cat "$PID"))"; return; }
	[ -f "$DISCO" ] || die "disco assente: 17-vm.sh crea $D"
	[ -w /dev/kvm ] || die "/dev/kvm non scrivibile: usermod -aG kvm $USER e rientra"
	log "$D: avvio (ssh :$PORTA_SSH, REMOTIX :$PORTA_RX)"
	rm -f "$MONITOR"
	: > "$CONSOLE"
	qemu-system-x86_64 \
		-name "rx-$D" -machine q35,accel=kvm -cpu host -smp "$CPU" -m "$RAM" \
		-device virtio-vga -display none \
		-drive "file=$DISCO,if=virtio,format=qcow2,discard=unmap" \
		-drive "file=$SEME,if=virtio,format=raw,readonly=on" \
		-netdev "user,id=n0,hostfwd=tcp::$PORTA_SSH-:22,hostfwd=tcp::$PORTA_RX-:7447,hostfwd=udp::$PORTA_RX-:7447" \
		-device virtio-net-pci,netdev=n0 \
		-device virtio-rng-pci \
		-serial "file:$CONSOLE" \
		-monitor "unix:$MONITOR,server,nowait" \
		-pidfile "$PID" -daemonize
	ok "qemu pid $(cat "$PID")"
	aspetta_ssh 600
	# cloud-init fino in fondo, o le prove partono su una macchina a meta'
	ssh_vm 'command -v cloud-init >/dev/null && sudo cloud-init status --wait >/dev/null 2>&1; true'
	ok "$(ssh_vm '. /etc/os-release; printf "%s · kernel %s" "$PRETTY_NAME" "$(uname -r)"')"
}

cmd_ferma() {
	accesa || { ok "$D gia' spenta"; return; }
	log "$D: spegnimento"
	printf 'system_powerdown\n' | socat - "UNIX-CONNECT:$MONITOR" >/dev/null 2>&1 \
		|| ssh_vm 'sudo systemctl poweroff' 2>/dev/null || true
	local t=0
	while accesa && [ "$t" -lt 90 ]; do sleep 2; t=$((t + 2)); done
	if accesa; then kill "$(cat "$PID")"; sleep 2; inf "forzata dopo 90 s"; fi
	rm -f "$PID"
	ok "spenta"
}

cmd_riavvia() {
	accesa || die "$D e' spenta"
	log "$D: riavvio vero dell'ospite"
	local b0; b0=$(ssh_vm 'cat /proc/sys/kernel/random/boot_id')
	ssh_vm 'sudo systemctl reboot' 2>/dev/null || true
	sleep 5
	aspetta_ssh 300
	local b1; b1=$(ssh_vm 'cat /proc/sys/kernel/random/boot_id')
	[ "$b0" != "$b1" ] || die "boot_id invariato: la macchina non si e' riavviata"
	ok "riavviata (boot_id cambiato)"
}

cmd_fotografa() {
	[ -n "${1:-}" ] || die "manca il nome della foto"
	accesa && die "prima: 17-vm.sh ferma $D (la foto si fa a macchina ferma)"
	cp --sparse=always "$DISCO" "$DIR/foto-$1.qcow2"
	ok "foto «$1» ($(du -h "$DIR/foto-$1.qcow2" | cut -f1))"
}

cmd_torna() {
	[ -f "$DIR/foto-${1:-}.qcow2" ] || die "nessuna foto «${1:-}» per $D"
	accesa && die "prima: 17-vm.sh ferma $D"
	cp --sparse=always "$DIR/foto-$1.qcow2" "$DISCO"
	ok "$D e' tornata alla foto «$1»"
}

cmd_azzera() {
	accesa && die "prima: 17-vm.sh ferma $D"
	rm -f "$DISCO"
	cmd_crea
}

# ---------------------------------------------------------------------------
# vesti: il desktop come lo installerebbe il CLIENTE, col gruppo di pacchetti
#   ufficiale della distribuzione.  ⛔ Niente di REMOTIX qui dentro (labwc per
#   XFCE e LXQt sotto Wayland, gruppi video/render, codec): quello e' mestiere
#   dell'installatore, e la prova deve vederlo mancare se lui lo dimentica.
# ---------------------------------------------------------------------------
comando_desktop() {  # stampa il comando per $D0 (distro) e $DE
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
	[ "$DE" != nudo ] || die "$D non ha desktop da vestire (usa <distro>-<desktop>)"
	local c
	c=$(comando_desktop "${D%%-*}") || die "$D: questa distribuzione non offre $DE (fuori dalla matrice)"
	accesa || die "$D e' spenta"
	log "$D: installo il desktop come il cliente"
	inf "$c"
	local t0=$SECONDS
	ssh_vm "$c" > "$DIR/vesti.log" 2>&1 || { tail -20 "$DIR/vesti.log"; die "installazione del desktop fallita"; }
	ssh_vm 'sudo systemctl set-default graphical.target >/dev/null 2>&1; true'
	ok "$DE installato in $((SECONDS - t0)) s ($(ssh_vm 'df -h / | tail -1' | awk '{print $3}') usati)"
	ok "sessioni Wayland: $(ssh_vm 'ls /usr/share/wayland-sessions 2>/dev/null | tr "
" " "')"
}

# ---------------------------------------------------------------------------
c=${1:-}; shift || true
case "$c" in
elenco) cmd_elenco ;;
crea|avvia|ferma|riavvia|azzera|vesti)
	riga "${1:?manca la distribuzione}"; shift; "cmd_$c" "$@" ;;
fotografa|torna)
	riga "${1:?manca la distribuzione}"; shift; "cmd_$c" "$@" ;;
ssh)
	riga "${1:?manca la distribuzione}"; shift; ssh_vm "$@" ;;
*) sed -n '2,30p' "$0"; exit 2 ;;
esac
