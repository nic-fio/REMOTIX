#!/bin/bash
#
# box.sh — Ubuntu 26.04 test boxes, one systemd container per desktop (gnome=Ubuntu, kde=Kubuntu, xfce=Xubuntu, lxqt=Lubuntu).
# Run on the dev server (root podman, cgroupfs; sudo with empty password is handled).
#
#   build <de>              image rxu/<de> from Containerfile (no REMOTIX inside)
#   boot <de>               start rxu-<de> (systemd, /dev/dri, sshd), check it, wait for ssh
#   shutdown <de>           stop it (the container stays, stopped)
#   status                  the four boxes: state and ports
#   ssh <de> [cmd...]       a command (or a shell) inside, as root, via ssh on 127.0.0.1
#   install <de> <x.deb>    copy the .deb in and run `apt install -y --reinstall ./file.deb` (a same-version package replaces the files too), print apt's result
#   reset <de>              throw the container away and boot a fresh one from the image
#
# Ports (the boxes share the host network, so every box has its own):
#   ssh 2221..2224; REMOTIX 8821..8824 (gnome 1, kde 2, xfce 3, lxqt 4) (TCP page + UDP QUIC, same number). `install` writes
#   REMOTIX_PORT=<port> into /etc/remotix/remotix.conf.d/10-box-port.conf, because the default 7447
#   would clash between boxes.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
KEY=$HERE/box-key

ok()  { printf 'OK   %s\n' "$*"; }
die() { printf 'FAIL %s\n' "$*"; exit 1; }

# podman as root, cgroupfs (the server has no systemd user session)
if [ "$(id -u)" -eq 0 ]; then
	P() { podman --cgroup-manager=cgroupfs "$@"; }
else
	P() { echo | sudo -S -p "" podman --cgroup-manager=cgroupfs "$@"; }
fi

choose() {  # sets DE, NAME, IMAGE, PSSH, PRX
	DE=${1:-}
	case $DE in gnome) k=1 ;; kde) k=2 ;; xfce) k=3 ;; lxqt) k=4 ;; *) die "desktop \"$DE\": xfce|lxqt|gnome|kde" ;; esac
	NAME=rxu-$DE; IMAGE=rxu/$DE:latest
	PSSH=$((2220 + k)); PRX=$((8820 + k))
}
running() { [ "$(P inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null || true)" = true ]; }
ssh_box() {
	ssh -i "$KEY" -p "$PSSH" -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
		-o UserKnownHostsFile=/dev/null -o LogLevel=ERROR root@127.0.0.1 "$@"
}

verb=${1:-}; [ -n "$verb" ] || die "usage: box.sh build|boot|shutdown|status|ssh|install|reset ..."; shift

if [ "$verb" = status ]; then
	for d in gnome kde xfce lxqt; do
		choose "$d"
		s=$(P ps -a --filter "name=^$NAME\$" --format '{{.Status}}' 2>/dev/null || true)
		printf '%-9s %-28s ssh %s  REMOTIX %s  image %s\n' "$NAME" "${s:-no container}" "$PSSH" "$PRX" \
			"$(P image exists "$IMAGE" && echo yes || echo no)"
	done
	ok "status"; exit 0
fi

choose "${1:-}"; shift

boot() {
	P image exists "$IMAGE" || die "missing image $IMAGE: box.sh build $DE"
	running && { ok "$NAME already running"; return 0; }
	P rm -f -t 0 "$NAME" >/dev/null 2>&1 || true
	# memlock unlimited (low-memory-monitor on GNOME calls mlockall); systemd mode, caps as a real login needs them (pam_loginuid, polkit, kwin/powerdevil), host network, all GPUs
	P run -d --name "$NAME" --systemd=always --pids-limit 16384 --network=host \
		--device /dev/dri --ulimit memlock=-1:-1 \
		--cap-add=AUDIT_WRITE --cap-add=AUDIT_CONTROL --cap-add=SYS_ADMIN --cap-add=SYS_NICE --cap-add=WAKE_ALARM \
		"$IMAGE" >/dev/null || die "podman run failed for $NAME"
	local S=""
	for _ in $(seq 1 120); do
		S=$(P exec "$NAME" systemctl is-system-running 2>/dev/null | head -1 || true)
		case $S in running|degraded) break ;; esac
		sleep 1
	done
	case $S in
	running|degraded) ;;
	*) P rm -f -t 0 "$NAME" >/dev/null 2>&1 || true; die "systemd of $NAME is \"${S:-unknown}\" after 120 s (container removed)" ;;
	esac
	[ "$S" = running ] || { echo "     failed units:"; P exec "$NAME" systemctl --failed --no-legend --plain 2>&1 | sed 's/^/       /'; }
	# a tmpfs copy of /sys/power so logind answers sleep questions as on a real machine (see power.sh)
	P exec -i "$NAME" sh < "$HERE/power.sh" | sed 's/^/     /' || die "power.sh failed in $NAME"
	local t=0
	until ssh_box true 2>/dev/null; do
		running || die "$NAME stopped while waiting for ssh"
		sleep 2; t=$((t + 2)); [ "$t" -lt 90 ] || die "ssh of $NAME not answering after 90 s"
	done
	ok "$NAME up (systemd $S, ssh :$PSSH after ${t}s, REMOTIX port $PRX)"
}

case $verb in
build)
	[ -f "$KEY" ] || ssh-keygen -q -t ed25519 -N "" -C rxu-box -f "$KEY"
	cd "$HERE"
	P build --network=host --build-arg "DESKTOP=$DE" --build-arg "SSH_PORT=$PSSH" -t "$IMAGE" -f Containerfile . \
		|| die "build of $DE failed"
	ok "image $IMAGE ($(P image inspect -f '{{.Size}}' "$IMAGE") bytes)" ;;
boot) boot ;;
shutdown)
	running || { ok "$NAME already stopped"; exit 0; }
	P exec "$NAME" journalctl --sync >/dev/null 2>&1 || true
	P stop -t 15 "$NAME" >/dev/null || die "stop of $NAME failed"
	ok "$NAME stopped" ;;
ssh)
	ssh_box "$@" ;;
install)
	deb=${1:?path to .deb}; [ -f "$deb" ] || die "no such file: $deb"
	running || die "$NAME is not running: box.sh boot $DE"
	f=/root/$(basename "$deb")
	P cp "$deb" "$NAME:$f" || die "cannot copy $deb into $NAME"
	# the image carries no package lists: refresh them first, as on a real machine (else Depends/Recommends are «not installable»)
	P exec "$NAME" apt-get update -qq >/dev/null 2>&1 || die "apt-get update failed in $NAME"
	if P exec -e DEBIAN_FRONTEND=noninteractive "$NAME" apt-get install -y --reinstall "$f" 2>&1 | tail -n 25 | sed 's/^/     /' \
		&& [ "${PIPESTATUS[0]}" -eq 0 ]; then
		P exec "$NAME" sh -c "mkdir -p /etc/remotix/remotix.conf.d && echo REMOTIX_PORT=$PRX > /etc/remotix/remotix.conf.d/10-box-port.conf"
		ok "$(basename "$deb") installed in $NAME (REMOTIX_PORT=$PRX; the service is as the package leaves it)"
	else die "apt install of $(basename "$deb") failed in $NAME"; fi ;;
reset)
	running && P exec "$NAME" journalctl --sync >/dev/null 2>&1 || true
	P rm -f -t 0 "$NAME" >/dev/null 2>&1 || true
	boot
	ok "$NAME reset: fresh container from $IMAGE" ;;
*) die "unknown verb: $verb" ;;
esac
