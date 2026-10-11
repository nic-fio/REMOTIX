#!/bin/bash
#
# 17-box.sh — phase 17: a machine of the matrix as a BOX (podman, systemd inside, the server's
# real GPU), with the verbs of 17-vm.sh that 17-t10.sh uses: so the script of §7.3 runs the same, and
# only who powers the machine on changes. Since 10 Oct 2026 it applies to the 26 combinations (phases/17 §3): the
# VMs have no GPU, and since phase 19 the installer refuses a machine without one (§10.27).
#
#   (on the server, as nicfio, with valid sudo)   [REMOTIX_CARD=intel|amd] bash 17-box.sh <verb> <m> …
#     build <m>        the image from the distribution's recipe (Containerfile.<family>,
#                           the desktop as argument)
#     build-all      the 26 images, one after the other (log in $T17/costruzione.log)
#     revert <m> [snapshot]  tears the box down: the next start begins again from the image
#     boot <m>             starts (systemd, the GPU, sshd on its own port) and waits for ssh
#     ssh <m> cmd…          a command inside, as root, via ssh on 127.0.0.1:<ssh port>
#     shutdown <m>             stops (the box stays, stopped)
#     reboot <m>           the restart OF THE BOX (podman restart): the real reboot of the machine
#                           is not tested here — it is green on the 32 in VM of 1 Oct (§7.5)
#     ports <m>             prints "<ssh port> <REMOTIX port>"
#     status <m> | list    one box | the 26 and the running ones
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
#   none. The cap of 4 is kept by `boot` counting the running t17-*.
#
# Permissions as in benches/11-boxes/11-start.sh, measured there one by one: --systemd=always,
# AUDIT_WRITE+AUDIT_CONTROL (pam_loginuid), SYS_ADMIN (polkit), SYS_NICE+WAKE_ALARM (kwin_wayland and
# powerdevil have the capability written on the file), --network=host (netavark does not apply the rules).
# The GPU: by PCI path and driver (i915 | amdgpu), with the names card0/renderD128 inside, and ALSO with the
# real name if different (libdrm rebuilds the name from the minor: 11-start.sh, prova-amd-1).
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
T17=${T17:-/media/REMOTIX/vm17/t17}
SSH_KEY=${SSH_KEY:-/media/REMOTIX/vm17/ssh/id_ed25519}
GPU=${REMOTIX_CARD:-intel}
CAP=${T17_CAP:-4}
MATRIX="debian13 ubuntu2604 fedora44 arch tumbleweed leap16 alma10"
P() { sudo -n podman "$@"; }
ok()  { printf '  OK  %s\n' "$*"; }
die() { printf '  NO  %s\n' "$*"; exit 1; }

machines() {  # the 26, one per line
	local d e
	for d in $MATRIX; do
		for e in gnome kde xfce lxqt; do
			[ "$d" = alma10 ] && case $e in xfce|lxqt) continue ;; esac
			echo "$d-$e"
		done
	done
}

choose() {  # choose <m>: sets D, DE, n, k, FAM, ARGS, PSSH, PRX, NAME, IMAGE
	m=$1; D=${m%%-*}; DE=${m#*-}
	machines | grep -qx "$m" || die "$m: not in the matrix (bash 17-box.sh list)"
	local y; n=0; for y in $MATRIX; do n=$((n + 1)); [ "$y" = "$D" ] && break; done
	case $DE in gnome) k=1 ;; kde) k=2 ;; xfce) k=3 ;; lxqt) k=4 ;; esac
	ARGS=(--build-arg "DESKTOP=$DE")
	case $D in
	tumbleweed) FAM=suse; ARGS+=(--build-arg BASE=tumbleweed) ;;
	leap16)     FAM=suse; ARGS+=(--build-arg BASE=leap:16.0) ;;
	*)          FAM=$D ;;
	esac
	case $GPU in
	intel) DRV=i915; s=0 ;;
	amd)   DRV=amdgpu; s=100 ;;
	*) die "REMOTIX_CARD=\"$GPU\": must be intel or amd" ;;
	esac
	PSSH=$((8600 + s + 10 * n + k)); PRX=$((8800 + s + 10 * n + k))
	NAME="t17-$m-$GPU"
	IMAGE="t17/$m:cliente"
}

ssh_s() {
	ssh -i "$SSH_KEY" -p "$PSSH" -o BatchMode=yes -o ConnectTimeout=5 \
		-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR \
		root@127.0.0.1 "$@"
}
enabled() { [ "$(P inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null)" = true ]; }
wait_systemd() {
	local S=""
	for _ in $(seq 1 120); do
		S=$(P exec "$NAME" systemctl is-system-running 2>&1 | head -1)
		case $S in running|degraded) break ;; esac
		sleep 1
	done
	echo "${S:-unknown}"
}
wait_ssh() {  # wait_ssh <seconds>
	local t=0
	until ssh_s true 2>/dev/null; do
		enabled || die "the box $NAME has stopped"
		sleep 2; t=$((t + 2))
		[ "$t" -lt "$1" ] || die "ssh not answering after $1 s"
	done
	ok "ssh answers after ${t} s"
}

build() {  # build <m>
	choose "$1"
	[ -f "$HERE/Containerfile.$FAM" ] || die "missing $HERE/Containerfile.$FAM"
	[ -f "$HERE/chiave-banco.pub" ] || cp "$SSH_KEY.pub" "$HERE/chiave-banco.pub" || die "missing $SSH_KEY.pub"
	# the image depends neither on the GPU nor on the port: the build ssh port is the Intel one,
	# and `boot` rewrites it for the Radeon (below)
	P build --network=host "${ARGS[@]}" --build-arg "SSH_PORT=$PSSH" \
		-f "$HERE/Containerfile.$FAM" -t "$IMAGE" "$HERE" || die "build of $m failed"
	ok "image $IMAGE"
}

verb=${1:?verb}; shift
case $verb in
list)
	for x in $(machines); do
		choose "$x"
		printf '%-18s ssh %s REMOTIX %s  %s\n' "$x" "$PSSH" "$PRX" \
			"$(P image exists "$IMAGE" && echo image || echo '—')$(enabled && echo ' · RUNNING')"
	done
	exit 0 ;;
build-all)
	mkdir -p "$T17"
	for x in $(machines); do
		t0=$(date +%s)
		if ( build "$x" ) >>"$T17/costruzione.log" 2>&1; then e=OK; else e=FALLITA; fi
		printf '%s %-18s %s in %s s\n' "$(date -u +%H:%M:%S)" "$x" "$e" "$(( $(date +%s) - t0 ))" | tee -a "$T17/costruzione.log"
	done
	exit 0 ;;
esac

choose "${1:?machine}"; shift
case $verb in
ports) echo "$PSSH $PRX" ;;
status) P ps -a --filter "name=^$NAME\$" --format '{{.Names}} {{.Status}} {{.Image}}' ;;
build) build "$m" ;;
revert)
	P rm -f -t 0 "$NAME" >/dev/null 2>&1
	ok "$NAME torn down: it will start again from the image $IMAGE (the \"snapshot\" ${1:-cliente})"
	;;
boot)
	enabled && { ok "$NAME is already running"; exit 0; }
	P image exists "$IMAGE" || die "missing image $IMAGE: bash 17-box.sh build $m"
	ongoing=$(P ps --filter 'name=^t17-' --format '{{.Names}}' | grep -c . || true)
	[ "$ongoing" -lt "$CAP" ] || die "already $ongoing t17 boxes running (cap $CAP)"
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
	[ -e "$CARD" ] && [ -e "$RENDER" ] || die "cannot find the $GPU GPU (driver $DRV): not starting on another one"
	REAL=()
	for N in "$CARD" "$RENDER"; do
		case "$N" in /dev/dri/card0|/dev/dri/renderD128) ;; *) REAL+=(--device "$N:$N") ;; esac
	done
	P rm -f -t 0 "$NAME" >/dev/null 2>&1
	P run -d --name "$NAME" \
		--systemd=always --pids-limit 16384 --network=host \
		--device "$CARD:/dev/dri/card0" --device "$RENDER:/dev/dri/renderD128" "${REAL[@]}" \
		--cap-add=AUDIT_WRITE --cap-add=AUDIT_CONTROL --cap-add=SYS_ADMIN --cap-add=SYS_NICE --cap-add=WAKE_ALARM \
		"$IMAGE" >/dev/null || die "podman run failed"
	S=$(wait_systemd)
	# the ssh port: the image is born with the Intel one; on the Radeon (or if the scheme changes) it is
	# rewritten before the bench enters
	P exec "$NAME" sh -c "grep -q '^Port $PSSH\$' /etc/ssh/sshd_config.d/t17.conf || { sed -i 's/^Port .*/Port $PSSH/' /etc/ssh/sshd_config.d/t17.conf; systemctl restart sshd.service 2>/dev/null || systemctl restart ssh.service; }"
	ok "$NAME running (systemd: $S; GPU $CARD→card0, $RENDER→renderD128${REAL:+ and with the real name}; ssh :$PSSH, REMOTIX :$PRX)"
	wait_ssh 90
	;;
ssh) ssh_s "$@" ;;
shutdown)
	enabled || { ok "$NAME is already stopped"; exit 0; }
	P stop -t 15 "$NAME" >/dev/null && ok "$NAME stopped (it stays, stopped)"
	;;
reboot)
	enabled || die "$NAME is stopped"
	a0=$(P inspect -f '{{.State.StartedAt}}' "$NAME")
	P restart -t 15 "$NAME" >/dev/null || die "podman restart failed"
	a1=$(P inspect -f '{{.State.StartedAt}}' "$NAME")
	[ "$a0" != "$a1" ] || die "the box did not restart (StartedAt unchanged)"
	S=$(wait_systemd)
	ok "rebooted: the container restarted ($a0 → $a1; systemd $S)"
	wait_ssh 90
	;;
*) echo "unknown verb: $verb"; exit 2 ;;
esac
