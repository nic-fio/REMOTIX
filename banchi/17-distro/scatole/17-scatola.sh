#!/bin/bash
#
# 17-scatola.sh — phase 17: a machine of the matrix as a BOX (podman, systemd inside, the server's
# real GPU), with the verbs of 17-vm.sh that 17-t10.sh uses: so the script of §7.3 runs the same, and
# only who powers the machine on changes. Since 10 Oct 2026 it applies to the 26 combinations (fasi/17 §3): the
# VMs have no GPU, and since phase 19 the installer refuses a machine without one (§10.27).
#
#   (on the server, as nicfio, with valid sudo)   [REMOTIX_SCHEDA=intel|amd] bash 17-scatola.sh <verb> <m> …
#     costruisci <m>        the image from the distribution's recipe (Contenitore.<family>,
#                           the desktop as argument)
#     costruisci-tutte      the 26 images, one after the other (log in $T17/costruzione.log)
#     torna <m> [snapshot]  tears the box down: the next start begins again from the image
#     avvia <m>             starts (systemd, the GPU, sshd on its own port) and waits for ssh
#     ssh <m> cmd…          a command inside, as root, via ssh on 127.0.0.1:<ssh port>
#     ferma <m>             stops (the box stays, stopped)
#     riavvia <m>           the restart OF THE BOX (podman restart): the real reboot of the machine
#                           is not tested here — it is green on the 32 in VM of 1 Oct (§7.5)
#     porte <m>             prints "<ssh port> <REMOTIX port>"
#     stato <m> | elenco    one box | the 26 and the running ones
#
# <m> = <distro>-<desktop>: debian13, ubuntu2604, fedora44, arch, tumbleweed, leap16 × gnome, kde,
# xfce, lxqt; alma10 × gnome, kde.
#
# ⭐ IN PARALLEL, up to 4 (memory "benches in parallel": own port, ban-file and socket, or the ban
#   of one stops them all). Each box has:
#   · its own name, with the GPU: t17-<m>-<gpu> (the same machine can run on Intel and Radeon);
#   · its own host ports (--network=host): ssh 8600+10n+k, REMOTIX 8800+10n+k, and +100 on the
#     Radeon (n = distribution 1-7, k = desktop 1-4) ⇒ 8611…8674 / 8811…8874 (Intel),
#     8711…8774 / 8911…8974 (Radeon). ⛔ Never those of the suite (7447/7448, 8511-8514) nor of the VMs
#     (23xx/75xx);
#   · REMOTIX's ban-file, socket and /run INSIDE the box (its own filesystem): nothing shared.
#   ⛔ It does not take the lock of the rete11 boxes (/media/REMOTIX/rete11/.scatole.lock): that one
#   protects the c<n>u<n> tenants of the rete11-* boxes from the hook's cleanup, and the t17-* have
#   none. The cap of 4 is kept by `avvia` counting the running t17-*.
#
# Permissions as in banchi/11-scatole/11-accendi.sh, measured there one by one: --systemd=always,
# AUDIT_WRITE+AUDIT_CONTROL (pam_loginuid), SYS_ADMIN (polkit), SYS_NICE+WAKE_ALARM (kwin_wayland and
# powerdevil have the capability written on the file), --network=host (netavark does not apply the rules).
# The GPU: by PCI path and driver (i915 | amdgpu), with the names card0/renderD128 inside, and ALSO with the
# real name if different (libdrm rebuilds the name from the minor: 11-accendi.sh, prova-amd-1).
set -uo pipefail
QUI=$(cd "$(dirname "$0")" && pwd)
T17=${T17:-/media/REMOTIX/vm17/t17}
CHIAVE=${CHIAVE:-/media/REMOTIX/vm17/ssh/id_ed25519}
SCHEDA=${REMOTIX_SCHEDA:-intel}
TETTO=${T17_TETTO:-4}
MATRICE="debian13 ubuntu2604 fedora44 arch tumbleweed leap16 alma10"
P() { sudo -n podman "$@"; }
ok()  { printf '  OK  %s\n' "$*"; }
die() { printf '  NO  %s\n' "$*"; exit 1; }

macchine() {  # the 26, one per line
	local d e
	for d in $MATRICE; do
		for e in gnome kde xfce lxqt; do
			[ "$d" = alma10 ] && case $e in xfce|lxqt) continue ;; esac
			echo "$d-$e"
		done
	done
}

scegli() {  # scegli <m>: sets D, DE, n, k, FAM, ARGS, PSSH, PRX, NOME, IMMAGINE
	m=$1; D=${m%%-*}; DE=${m#*-}
	macchine | grep -qx "$m" || die "$m: not in the matrix (bash 17-scatola.sh elenco)"
	local y; n=0; for y in $MATRICE; do n=$((n + 1)); [ "$y" = "$D" ] && break; done
	case $DE in gnome) k=1 ;; kde) k=2 ;; xfce) k=3 ;; lxqt) k=4 ;; esac
	ARGS=(--build-arg "DESKTOP=$DE")
	case $D in
	tumbleweed) FAM=suse; ARGS+=(--build-arg BASE=tumbleweed) ;;
	leap16)     FAM=suse; ARGS+=(--build-arg BASE=leap:16.0) ;;
	*)          FAM=$D ;;
	esac
	case $SCHEDA in
	intel) DRV=i915; s=0 ;;
	amd)   DRV=amdgpu; s=100 ;;
	*) die "REMOTIX_SCHEDA=\"$SCHEDA\": must be intel or amd" ;;
	esac
	PSSH=$((8600 + s + 10 * n + k)); PRX=$((8800 + s + 10 * n + k))
	NOME="t17-$m-$SCHEDA"
	IMMAGINE="t17/$m:cliente"
}

ssh_s() {
	ssh -i "$CHIAVE" -p "$PSSH" -o BatchMode=yes -o ConnectTimeout=5 \
		-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR \
		root@127.0.0.1 "$@"
}
accesa() { [ "$(P inspect -f '{{.State.Running}}' "$NOME" 2>/dev/null)" = true ]; }
aspetta_systemd() {
	local S=""
	for _ in $(seq 1 120); do
		S=$(P exec "$NOME" systemctl is-system-running 2>&1 | head -1)
		case $S in running|degraded) break ;; esac
		sleep 1
	done
	echo "${S:-unknown}"
}
aspetta_ssh() {  # aspetta_ssh <secondi>
	local t=0
	until ssh_s true 2>/dev/null; do
		accesa || die "the box $NOME has stopped"
		sleep 2; t=$((t + 2))
		[ "$t" -lt "$1" ] || die "ssh not answering after $1 s"
	done
	ok "ssh answers after ${t} s"
}

costruisci() {  # costruisci <m>
	scegli "$1"
	[ -f "$QUI/Contenitore.$FAM" ] || die "missing $QUI/Contenitore.$FAM"
	[ -f "$QUI/chiave-banco.pub" ] || cp "$CHIAVE.pub" "$QUI/chiave-banco.pub" || die "missing $CHIAVE.pub"
	# the image depends neither on the GPU nor on the port: the build ssh port is the Intel one,
	# and `avvia` rewrites it for the Radeon (below)
	P build --network=host "${ARGS[@]}" --build-arg "PORTA_SSH=$PSSH" \
		-f "$QUI/Contenitore.$FAM" -t "$IMMAGINE" "$QUI" || die "build of $m failed"
	ok "image $IMMAGINE"
}

verbo=${1:?verb}; shift
case $verbo in
elenco)
	for x in $(macchine); do
		scegli "$x"
		printf '%-18s ssh %s REMOTIX %s  %s\n' "$x" "$PSSH" "$PRX" \
			"$(P image exists "$IMMAGINE" && echo image || echo '—')$(accesa && echo ' · RUNNING')"
	done
	exit 0 ;;
costruisci-tutte)
	mkdir -p "$T17"
	for x in $(macchine); do
		t0=$(date +%s)
		if ( costruisci "$x" ) >>"$T17/costruzione.log" 2>&1; then e=OK; else e=FALLITA; fi
		printf '%s %-18s %s in %s s\n' "$(date -u +%H:%M:%S)" "$x" "$e" "$(( $(date +%s) - t0 ))" | tee -a "$T17/costruzione.log"
	done
	exit 0 ;;
esac

scegli "${1:?machine}"; shift
case $verbo in
porte) echo "$PSSH $PRX" ;;
stato) P ps -a --filter "name=^$NOME\$" --format '{{.Names}} {{.Status}} {{.Image}}' ;;
costruisci) costruisci "$m" ;;
torna)
	P rm -f -t 0 "$NOME" >/dev/null 2>&1
	ok "$NOME torn down: it will start again from the image $IMMAGINE (the \"snapshot\" ${1:-cliente})"
	;;
avvia)
	accesa && { ok "$NOME is already running"; exit 0; }
	P image exists "$IMMAGINE" || die "missing image $IMMAGINE: bash 17-scatola.sh costruisci $m"
	accese=$(P ps --filter 'name=^t17-' --format '{{.Names}}' | grep -c . || true)
	[ "$accese" -lt "$TETTO" ] || die "already $accese t17 boxes running (cap $TETTO)"
	CARD=""; RENDER=""
	for C in /sys/class/drm/card[0-9]*; do
		case "$C" in *-*) continue ;; esac
		[ -e "$C/device/driver" ] || continue
		[ "$(basename "$(readlink -f "$C/device/driver")")" = "$DRV" ] || continue
		PCI=$(basename "$(readlink -f "$C/device")")
		CARD=$(readlink -f "/dev/dri/by-path/pci-$PCI-card" 2>/dev/null)
		RENDER=$(readlink -f "/dev/dri/by-path/pci-$PCI-render" 2>/dev/null)
		break
	done
	[ -e "$CARD" ] && [ -e "$RENDER" ] || die "cannot find the $SCHEDA GPU (driver $DRV): not starting on another one"
	VERI=()
	for N in "$CARD" "$RENDER"; do
		case "$N" in /dev/dri/card0|/dev/dri/renderD128) ;; *) VERI+=(--device "$N:$N") ;; esac
	done
	P rm -f -t 0 "$NOME" >/dev/null 2>&1
	P run -d --name "$NOME" \
		--systemd=always --pids-limit 16384 --network=host \
		--device "$CARD:/dev/dri/card0" --device "$RENDER:/dev/dri/renderD128" "${VERI[@]}" \
		--cap-add=AUDIT_WRITE --cap-add=AUDIT_CONTROL --cap-add=SYS_ADMIN --cap-add=SYS_NICE --cap-add=WAKE_ALARM \
		"$IMMAGINE" >/dev/null || die "podman run failed"
	S=$(aspetta_systemd)
	# the ssh port: the image is born with the Intel one; on the Radeon (or if the scheme changes) it is
	# rewritten before the bench enters
	P exec "$NOME" sh -c "grep -q '^Port $PSSH\$' /etc/ssh/sshd_config.d/t17.conf || { sed -i 's/^Port .*/Port $PSSH/' /etc/ssh/sshd_config.d/t17.conf; systemctl restart sshd.service 2>/dev/null || systemctl restart ssh.service; }"
	ok "$NOME running (systemd: $S; GPU $CARD→card0, $RENDER→renderD128${VERI:+ and with the real name}; ssh :$PSSH, REMOTIX :$PRX)"
	aspetta_ssh 90
	;;
ssh) ssh_s "$@" ;;
ferma)
	accesa || { ok "$NOME is already stopped"; exit 0; }
	P stop -t 15 "$NOME" >/dev/null && ok "$NOME stopped (it stays, stopped)"
	;;
riavvia)
	accesa || die "$NOME is stopped"
	a0=$(P inspect -f '{{.State.StartedAt}}' "$NOME")
	P restart -t 15 "$NOME" >/dev/null || die "podman restart failed"
	a1=$(P inspect -f '{{.State.StartedAt}}' "$NOME")
	[ "$a0" != "$a1" ] || die "the box did not restart (StartedAt unchanged)"
	S=$(aspetta_systemd)
	ok "rebooted: the container restarted ($a0 → $a1; systemd $S)"
	aspetta_ssh 90
	;;
*) echo "unknown verb: $verbo"; exit 2 ;;
esac
