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
#   bash 17-vm.sh da-iso    <macchina>-iso    lo stato ISO: dall'ISO ufficiale con l'installatore
#                                         automatico, disco nuovo, UEFI; alla fine la foto «iso»
#   bash 17-vm.sh impronta  <macchina> [foto] come e' fatta la macchina (firewall, SELinux, display
#                                         manager, rete, pacchetti); con [foto] la avvia da quella
#                                         foto in sola lettura, su porte sue (k=6)
#   bash 17-vm.sh schermo   <macchina> [file.png]  fotografia dello schermo (dal monitor di QEMU)
#
# Le macchine si chiamano <distro>-<desktop> (fedora44-kde; <distro> da sola =
# «nudo», senza desktop).  Tutto sta sotto /media/REMOTIX/vm17/<macchina>/;
# l'immagine ufficiale in /media/REMOTIX/vm17/<distro>/base.qcow2, condivisa.
# Porte sul server, per la distribuzione N e il desktop k (nudo 0, gnome 1,
# kde 2, xfce 3, lxqt 4): ssh 2300+10N+k, REMOTIX 7500+10N+k (TCP e UDP).
# Lo stato ISO (fasi/17 §7.2) e' una macchina a parte, <distro>-<desktop>-iso, con
# k=5, cartella /media/REMOTIX/vm17/<distro>-<desktop>-iso/ e firmware UEFI.
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
OVMF_CODE=/usr/share/OVMF/OVMF_CODE_4M.fd
OVMF_VARS=/usr/share/OVMF/OVMF_VARS_4M.fd
ISO_DIR="$RADICE/iso"
RISPOSTE="$(dirname "$(readlink -f "$0")")/iso-risposte"

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

riga() {  # riga <distro>[-<desktop>][-iso] -> NUM, URL, ESPR, DE, D, porte
	local nome=$1 dis de=nudo k=0 x r
	ISO=
	case "$nome" in *-iso) ISO=1; nome=${nome%-iso} ;; esac
	dis=${nome%%-*}
	DIS=$dis
	[ "$dis" != "$nome" ] && de=${nome#*-}
	for x in $DESKTOP; do [ "$x" = "$de" ] && break; k=$((k + 1)); done
	[ "$k" -lt 5 ] || die "desktop sconosciuto: $de (uno di: $DESKTOP)"
	r=$(printf '%s\n' "$DISTRO_TAB" | awk -F'|' -v OFS='|' -v d="$dis" '{gsub(/ /,"",$1)} $1==d')
	[ -n "$r" ] || die "distribuzione sconosciuta: $dis (vedi: 17-vm.sh elenco)"
	NUM=$(printf '%s' "$r" | cut -d'|' -f2 | tr -d ' ')
	URL=$(printf '%s' "$r" | cut -d'|' -f3 | tr -d ' ')
	ESPR=$(printf '%s' "$r" | cut -d'|' -f4 | tr -d ' ')
	DE=$de; D=$dis; [ "$de" = nudo ] || D="$dis-$de"
	if [ -n "$ISO" ]; then
		[ "$de" != nudo ] || die "lo stato ISO vuole un desktop: <distro>-<desktop>-iso"
		k=5; D="$D-iso"
	fi
	# l'immagine ufficiale e' UNA per distribuzione; il disco e' uno per macchina
	BASE_IMG="$RADICE/$dis/base.qcow2"
	DIR="$RADICE/$D"; DISCO="$DIR/disco.qcow2"; SEME="$DIR/seme.iso"
	PID="$DIR/qemu.pid"; MONITOR="$DIR/monitor.sock"; CONSOLE="$DIR/console.log"
	VARS="$DIR/ovmf-vars.fd"   # la NVRAM UEFI: c'e' solo per le macchine che la usano
	PORTA_SSH=$((2300 + 10 * NUM + k)); PORTA_RX=$((7500 + 10 * NUM + k))
}

AVVIA_EXTRA=()   # argomenti in piu' per QEMU in cmd_avvia (impronta: -snapshot)

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
	local extra=()
	[ -f "$VARS" ] && extra+=(-drive "if=pflash,format=raw,readonly=on,file=$OVMF_CODE" \
		-drive "if=pflash,format=raw,file=$VARS")
	[ -f "$SEME" ] && extra+=(-drive "file=$SEME,if=virtio,format=raw,readonly=on")
	qemu-system-x86_64 \
		-name "rx-$D" -machine q35,accel=kvm -cpu host -smp "$CPU" -m "$RAM" \
		-device virtio-vga -display none \
		-drive "file=$DISCO,if=virtio,format=qcow2,discard=unmap" \
		"${extra[@]}" "${AVVIA_EXTRA[@]}" \
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
	[ -f "$VARS" ] && cp "$VARS" "$DIR/foto-$1.vars.fd"
	ok "foto «$1» ($(du -h "$DIR/foto-$1.qcow2" | cut -f1))"
}

cmd_torna() {
	[ -f "$DIR/foto-${1:-}.qcow2" ] || die "nessuna foto «${1:-}» per $D"
	accesa && die "prima: 17-vm.sh ferma $D"
	cp --sparse=always "$DIR/foto-$1.qcow2" "$DISCO"
	[ -f "$DIR/foto-$1.vars.fd" ] && cp "$DIR/foto-$1.vars.fd" "$VARS"
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
# Lo stato ISO (fasi/17 §7.2): la macchina installata dall'ISO UFFICIALE con
#   l'installatore automatico della distribuzione, e il suo desktop di serie.
#   Una immagine cloud con un desktop sopra NON e' la macchina di un cliente:
#   firewall, display manager, SELinux, rete e pacchetti li decide l'installatore.
#   Le risposte stanno in iso-risposte/ accanto a questo copione; rispetto alle
#   scelte di serie aggiungono solo ssh con la chiave del banco e sudo senza
#   parola, e lo fanno DENTRO l'installazione.  ⛔ Niente di REMOTIX.
#   Disco NUOVO (non una sovrapposizione sull'immagine cloud), firmware UEFI
#   (OVMF, NVRAM propria in ovmf-vars.fd), niente seriale nel sistema installato.
# ---------------------------------------------------------------------------
# distro | cartella ufficiale | file delle somme (espr.) | ISO (espr.) | kernel | initrd
ISO_TAB='
debian13   | https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/ | SHA256SUMS | debian-13\.[0-9.]*-amd64-netinst\.iso | /install.amd/vmlinuz | /install.amd/initrd.gz
ubuntu2604 | https://releases.ubuntu.com/26.04/ | SHA256SUMS | ubuntu-26\.04[0-9.]*-desktop-amd64\.iso | /casper/vmlinuz | /casper/initrd
fedora44   | https://download.fedoraproject.org/pub/fedora/linux/releases/44/Everything/x86_64/iso/ | Fedora-Everything-44-[0-9.]*-x86_64-CHECKSUM | Fedora-Everything-netinst-x86_64-44-[0-9.]*\.iso | /images/pxeboot/vmlinuz | /images/pxeboot/initrd.img
arch       | https://geo.mirror.pkgbuild.com/iso/latest/ | sha256sums\.txt | archlinux-20[0-9.]*-x86_64\.iso | /arch/boot/x86_64/vmlinuz-linux | /arch/boot/x86_64/initramfs-linux.img
tumbleweed | https://download.opensuse.org/tumbleweed/iso/ | openSUSE-Tumbleweed-NET-x86_64-Current\.iso\.sha256 | openSUSE-Tumbleweed-NET-x86_64-Snapshot[0-9]*-Media\.iso | /boot/x86_64/loader/linux | /boot/x86_64/loader/initrd
alma10     | https://repo.almalinux.org/almalinux/10/isos/x86_64/ | CHECKSUM | AlmaLinux-10\.[0-9]*-x86_64-boot\.iso | /images/pxeboot/vmlinuz | /images/pxeboot/initrd.img
'
# Le combinazioni che hanno le risposte scritte: una per famiglia (§7.2)
ISO_MACCHINE="debian13-gnome ubuntu2604-gnome fedora44-gnome arch-kde tumbleweed-kde alma10-gnome"

riga_iso() {  # -> ISO_URL ISO_SOMME ISO_ESPR ISO_KERNEL ISO_INITRD
	local r
	r=$(printf '%s\n' "$ISO_TAB" | awk -F'|' -v OFS='|' -v d="$DIS" '{gsub(/ /,"",$1)} $1==d')
	[ -n "$r" ] || die "$DIS: nessuna ISO nella tabella"
	ISO_URL=$(printf '%s' "$r" | cut -d'|' -f2 | tr -d ' ')
	ISO_SOMME=$(printf '%s' "$r" | cut -d'|' -f3 | tr -d ' ')
	ISO_ESPR=$(printf '%s' "$r" | cut -d'|' -f4 | tr -d ' ')
	ISO_KERNEL=$(printf '%s' "$r" | cut -d'|' -f5 | tr -d ' ')
	ISO_INITRD=$(printf '%s' "$r" | cut -d'|' -f6 | tr -d ' ')
}

scarica_iso() {  # -> ISO_FILE, scaricata e VERIFICATA con la sha256 del sito ufficiale
	local somme nome atteso
	mkdir -p "$ISO_DIR"
	log "$D: l'ISO ufficiale"
	somme=$(curl -fsSL "$ISO_URL" | grep -oE "$ISO_SOMME" | sort -V | tail -1)
	[ -n "$somme" ] || die "nessun file delle somme «$ISO_SOMME» in $ISO_URL"
	# due forme: «HASH  file» (o «HASH *file») e «SHA256 (file) = HASH»
	read -r atteso nome < <(curl -fsSL "${ISO_URL%/}/$somme" | awk '
		/^SHA256 \(/ { f=$2; gsub(/[()]/, "", f); print $4, f; next }
		length($1) == 64 && NF == 2 { f=$2; sub(/^\*/, "", f); print $1, f }' |
		grep -E " $ISO_ESPR\$" | sort -k2 -V | tail -1) || true
	[ -n "${nome:-}" ] || die "nessuna ISO «$ISO_ESPR» in $somme"
	ISO_FILE="$ISO_DIR/$nome"
	if [ -f "$ISO_FILE" ] && [ "$(cat "$ISO_FILE.sha256-ok" 2>/dev/null)" = "$atteso" ]; then
		ok "$nome (gia' verificata)"; return
	fi
	if [ ! -f "$ISO_FILE" ]; then
		inf "scarico ${ISO_URL%/}/$nome"
		curl -fL -sS -o "$ISO_FILE.parte" "${ISO_URL%/}/$nome" || die "scaricamento fallito"
		mv "$ISO_FILE.parte" "$ISO_FILE"
	fi
	inf "verifico la sha256 ($somme)"
	[ "$(sha256sum "$ISO_FILE" | cut -d' ' -f1)" = "$atteso" ] || {
		mv "$ISO_FILE" "$ISO_FILE.sbagliata"; die "$nome: sha256 diversa da quella ufficiale"; }
	printf '%s\n' "$atteso" > "$ISO_FILE.sha256-ok"
	printf '%s\n' "${ISO_URL%/}/$nome" > "$ISO_FILE.origine"
	ok "$nome, sha256 ${atteso:0:16}… come da $somme"
}

prepara_risposte() {  # le risposte dell'installatore in $DIR/risposte, servite in HTTP
	local r="$DIR/risposte" hash chiave
	rm -rf "$r"; mkdir -p "$r"
	hash=$(openssl passwd -6 "$UTENTE")
	chiave=$(cat "$CHIAVE.pub")
	riempi() {
		[ -f "$RISPOSTE/$1" ] || die "manca $RISPOSTE/$1"
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
	*) die "$DIS: nessuna risposta scritta" ;;
	esac
	ok "risposte: $(ls "$r" | tr '\n' ' ')"
}

comando_iso() {  # la riga del kernel dell'installatore (nessuna seriale: resterebbe nel sistema)
	case "$DIS" in
	debian13)   echo "auto=true priority=critical url=$WEB/preseed.cfg locale=it_IT.UTF-8 keymap=it hostname=rx-$D domain= ---" ;;
	ubuntu2604) echo "autoinstall ds=nocloud;s=$WEB/ noprompt --- quiet splash" ;;
	fedora44|alma10) echo "inst.stage2=hd:LABEL=$ETICHETTA inst.ks=$WEB/ks.cfg" ;;
	arch)       echo "archisobasedir=arch archisosearchuuid=$ARCH_UUID script=$WEB/installa.sh" ;;
	tumbleweed) echo "autoyast=$WEB/autoinst.xml splash=silent" ;;
	esac
}

monitor() {  # monitor <comando HMP>: senza socat, che sul server non c'e'
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

cmd_schermo() {
	accesa || die "$D e' spenta"
	local f=${1:-$DIR/schermo.png}
	rm -f "$f"
	monitor "screendump $f -f png" >/dev/null
	[ -s "$f" ] || die "schermata non fatta"
	ok "schermata: $f"
}

cmd_da_iso() {
	[ -n "$ISO" ] || die "uso: 17-vm.sh da-iso <distro>-<desktop>-iso (una di: $ISO_MACCHINE)"
	case " $ISO_MACCHINE " in *" ${D%-iso} "*) ;; *) die "${D%-iso}: nessuna risposta scritta (una di: $ISO_MACCHINE)" ;; esac
	accesa && die "$D e' accesa: prima 17-vm.sh ferma $D"
	[ -w /dev/kvm ] || die "/dev/kvm non scrivibile: usermod -aG kvm $USER e rientra"
	local t0=$SECONDS
	mkdir -p "$DIR" "$RADICE/ssh"
	[ -f "$CHIAVE" ] || ssh-keygen -q -t ed25519 -N '' -C remotix-vm17 -f "$CHIAVE"
	riga_iso
	scarica_iso

	log "$D: kernel e initrd dell'installatore, dall'ISO"
	isoinfo -R -i "$ISO_FILE" -x "$ISO_KERNEL" > "$DIR/iso-kernel"
	isoinfo -R -i "$ISO_FILE" -x "$ISO_INITRD" > "$DIR/iso-initrd"
	[ -s "$DIR/iso-kernel" ] && [ -s "$DIR/iso-initrd" ] || die "kernel o initrd non trovati nell'ISO"
	ETICHETTA=$(isoinfo -d -i "$ISO_FILE" | sed -n 's/^Volume id: //p')
	ARCH_UUID=$(isoinfo -R -f -i "$ISO_FILE" | sed -n 's|^/boot/\(.*\)\.uuid$|\1|p' | head -1)
	ok "etichetta «$ETICHETTA»"
	PORTA_WEB=$((18300 + 10 * NUM + 5))
	WEB="http://10.0.2.2:$PORTA_WEB"     # 10.0.2.2 e' il server visto dalla rete utente di QEMU
	prepara_risposte
	local riga_k; riga_k=$(comando_iso)
	inf "kernel: $riga_k"
	if [ -n "${RX_ISO_SOLO_PREPARA:-}" ]; then
		ok "preparata senza accendere niente (RX_ISO_SOLO_PREPARA)"; return
	fi

	log "$D: disco NUOVO ($DISCO_GRANDE) e NVRAM UEFI nuova"
	rm -f "$DISCO" "$VARS" "$PID"
	qemu-img create -q -f qcow2 "$DISCO" "$DISCO_GRANDE"
	cp "$OVMF_VARS" "$VARS"
	ok "fatto"

	python3 -m http.server "$PORTA_WEB" --bind 127.0.0.1 --directory "$DIR/risposte" \
		> "$DIR/web.log" 2>&1 &
	local web=$!
	# shellcheck disable=SC2064
	trap "kill $web 2>/dev/null" EXIT
	sleep 1
	kill -0 "$web" 2>/dev/null || die "il servitore delle risposte non parte (porta $PORTA_WEB occupata? un altro da-iso?): $DIR/web.log"

	log "$D: installazione automatica dall'ISO (senza schermo; per guardare: 17-vm.sh schermo $D)"
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
	ok "qemu pid $(cat "$PID"); a fine installazione l'installatore riavvia e QEMU esce (-no-reboot)"
	local limite=${RX_ISO_ATTESA:-10800} t=0
	while accesa; do
		sleep 30; t=$((t + 30))
		[ $((t % 600)) -ne 0 ] || inf "$((t / 60)) min: disco $(du -h "$DISCO" | cut -f1)"
		if [ "$t" -ge "$limite" ]; then
			cmd_schermo "$DIR/schermo-scaduto.png" || true
			kill "$(cat "$PID")"; die "installazione non finita in $limite s (schermata: $DIR/schermo-scaduto.png)"
		fi
	done
	rm -f "$PID"
	kill "$web" 2>/dev/null; trap - EXIT
	local t_inst=$((SECONDS - t0))
	grep -q '" 200 ' "$DIR/web.log" || die "l'installatore non ha mai chiesto le risposte (web.log)"
	! grep -q 'RX-ESITO: FALLITA' "$CONSOLE" || die "l'installatore dice FALLITA (console: $CONSOLE)"
	[ "$(du -k "$DISCO" | cut -f1)" -gt 1500000 ] || die "disco quasi vuoto ($(du -h "$DISCO" | cut -f1)): installazione non fatta"
	ok "installazione finita in $((t_inst / 60)) min ($(du -h "$DISCO" | cut -f1) sul disco)"

	log "$D: primo avvio dal disco installato"
	cmd_avvia
	ssh_vm 'sudo -n true' || die "sudo senza parola non va"
	ok "sudo senza parola"
	# che la macchina sia arrivata in fondo all'avvio, desktop compreso
	if ssh_vm 'timeout 300 systemctl is-system-running --wait >/dev/null 2>&1; systemctl is-active graphical.target' | grep -qx active; then
		ok "graphical.target raggiunto"
	else
		inf "⚠ graphical.target NON attivo"
	fi
	cmd_impronta
	cmd_ferma
	cmd_fotografa iso
	printf 'data %s\nISO %s\ninstallazione %s s\nin tutto %s s\n' "$(date -Is)" \
		"$(basename "$ISO_FILE")" "$t_inst" "$((SECONDS - t0))" > "$DIR/da-iso.txt"
	ok "$D pronta, foto «iso», in tutto $(((SECONDS - t0) / 60)) min"
}

# ---------------------------------------------------------------------------
# impronta: come e' fatta la macchina, per confrontare ISO e DESKTOP (§7.2).
#   Con una foto la macchina parte DA QUELLA FOTO con -snapshot (il disco non si
#   tocca, e nemmeno la macchina di chi la sta usando) e su porte sue (k=6).
# ---------------------------------------------------------------------------
IMPRONTA='
set +e
. /etc/os-release
v() { printf "%-18s %s\n" "$1:" "$2"; }
v sistema "$PRETTY_NAME, kernel $(uname -r)"
v firmware "$([ -d /sys/firmware/efi ] && echo UEFI || echo BIOS)"
v lsm "$(cat /sys/kernel/security/lsm 2>/dev/null)"
v selinux "$(if [ -r /sys/fs/selinux/enforce ]; then [ "$(cat /sys/fs/selinux/enforce)" = 1 ] && echo Enforcing || echo Permissive; else echo assente; fi)"
v apparmor "$(sudo aa-status --enabled 2>/dev/null && echo attivo || echo spento/assente)"
v firewalld "$(systemctl is-enabled firewalld 2>/dev/null | head -1) / $(systemctl is-active firewalld 2>/dev/null)"
v "altri firewall" "$(for u in ufw nftables iptables; do systemctl is-enabled $u >/dev/null 2>&1 && printf "%s " $u; done)"
[ "$(systemctl is-active firewalld 2>/dev/null)" = active ] && v "  zona" "$(sudo firewall-cmd --get-default-zone): servizi [$(sudo firewall-cmd --list-services)] porte [$(sudo firewall-cmd --list-ports)]"
v ufw "$(command -v ufw >/dev/null && sudo ufw status | head -1 || echo assente)"
v nft "$(sudo nft list ruleset 2>/dev/null | grep -c . ) righe di regole"
dm=$(readlink -f /etc/systemd/system/display-manager.service 2>/dev/null)
v "display manager" "${dm##*/}"
v "accesso autom." "$(grep -hsiE "^[[:space:]]*(AutomaticLoginEnable|AutomaticLogin|User|Session)[[:space:]]*=|^DISPLAYMANAGER(_AUTOLOGIN)?=" /etc/gdm/custom.conf /etc/gdm3/custom.conf /etc/gdm3/daemon.conf /etc/sddm.conf /etc/sddm.conf.d/* /etc/sysconfig/displaymanager 2>/dev/null | tr "\n" " ")"
v "sessioni wayland" "$(ls /usr/share/wayland-sessions 2>/dev/null | tr "\n" " ")"
v "sessioni x11" "$(ls /usr/share/xsessions 2>/dev/null | tr "\n" " ")"
v "obiettivo" "$(systemctl get-default)"
v rete "NetworkManager=$(systemctl is-active NetworkManager) networkd=$(systemctl is-active systemd-networkd) wicked=$(systemctl is-active wicked 2>/dev/null) netplan=[$(ls /etc/netplan 2>/dev/null | tr "\n" " ")]"
v resolved "$(systemctl is-active systemd-resolved)"
v sshd "$(for u in ssh sshd; do x=$(systemctl is-enabled $u 2>/dev/null) && { echo "$u $x"; break; }; done)"
v cloud-init "$(command -v cloud-init >/dev/null && echo presente || echo assente)"
v pacchetti "$( (dpkg-query -W 2>/dev/null || rpm -qa 2>/dev/null || pacman -Q 2>/dev/null) | wc -l)"
v flatpak "$(command -v flatpak >/dev/null && flatpak remotes --columns=name 2>/dev/null | tr "\n" " " || echo assente)"
v snap "$(command -v snap >/dev/null && snap list 2>/dev/null | awk "NR>1{print \$1}" | tr "\n" " " || echo assente)"
v radice "$(findmnt -no FSTYPE /) su $(findmnt -no SOURCE /)"
v swap "$(sudo swapon --show=NAME,TYPE --noheadings | tr -s " " | tr "\n" " ")"
v lingua "$(localectl status | sed -n "s/.*LANG=//p") / tastiera $(localectl status | sed -n "s/.*X11 Layout: //p")"
v fuso "$(timedatectl show -p Timezone --value)"
v "gruppi utente" "$(id -nG)"
v "utenti umani" "$(awk -F: "\$3>=1000 && \$3<60000 {print \$1}" /etc/passwd | tr "\n" " ")"
v "root" "$(sudo passwd -S root 2>/dev/null | cut -d" " -f2)"
v faillock "$(grep -lsr pam_faillock /etc/pam.d /usr/lib/pam.d 2>/dev/null | wc -l) file PAM"
v pipewire "$(systemctl --global is-enabled pipewire.socket 2>/dev/null)"
v "unita abilitate" "$(systemctl list-unit-files --state=enabled --no-legend | wc -l)"
v snapper "$(command -v snapper >/dev/null && sudo snapper list-configs 2>/dev/null | awk "NR>2{print \$1}" | tr "\n" " " || echo assente) $(command -v snapper >/dev/null && echo "($(sudo snapper list 2>/dev/null | grep -c "^ *[0-9]") foto)")"
v raccomandati "apt=$(apt-config dump APT::Install-Recommends 2>/dev/null | sed -n "s/.*\"\(.*\)\";/\1/p") zypp.onlyRequires=$(grep -hsE "^[[:space:]]*solver.onlyRequires" /etc/zypp/zypp.conf /etc/zypp/zypp.conf.d/* /usr/etc/zypp/zypp.conf /usr/etc/zypp/zypp.conf.d/* 2>/dev/null | tr -d " " | tr "\n" " ") dnf=$(grep -hs install_weak_deps /etc/dnf/dnf.conf /etc/dnf/libdnf5.conf.d/* 2>/dev/null | tr -d " " | tr "\n" " ")"
v "gruppi video/render" "$(getent group video render | cut -d: -f1,4 | tr "\n" " ")"
v "in ascolto" "$(sudo ss -Hltnu 2>/dev/null | awk "{print \$1\"/\"\$5}" | sort -u | tr "\n" " ")"
'

cmd_impronta() {
	local foto=${1:-} nome=attuale
	if [ -n "$foto" ]; then
		[ -f "$DIR/foto-$foto.qcow2" ] || die "nessuna foto «$foto» per $D"
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
	accesa || die "$D e' spenta"
	log "$D: impronta ($nome)"
	ssh_vm "$IMPRONTA" | tee "$DIR/impronta-$nome.txt"
	ssh_vm '(dpkg-query -W -f="\${Package}\n" 2>/dev/null || rpm -qa --qf "%{NAME}\n" 2>/dev/null || pacman -Qq) | sort -u' \
		> "$DIR/pacchetti-$nome.txt"
	ssh_vm 'systemctl list-unit-files --state=enabled --no-legend | cut -d" " -f1 | sort' > "$DIR/unita-$nome.txt"
	ok "in $DIR/{impronta,pacchetti,unita}-$nome.txt"
	if [ -n "$foto" ]; then
		kill "$(cat "$PID")" 2>/dev/null; rm -f "$PID"; trap - EXIT
		ok "spenta (le modifiche di -snapshot se ne vanno con lei)"
	fi
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
da-iso)
	riga "${1:?manca la macchina (<distro>-<desktop>-iso)}"; shift; cmd_da_iso "$@" ;;
impronta|schermo)
	riga "${1:?manca la macchina}"; shift; "cmd_$c" "$@" ;;
*) sed -n '2,42p' "$0"; exit 2 ;;
esac
