#!/bin/bash
# ===========================================================================
# 11-two-cards.sh — a TEMPORARY box that sees BOTH graphics cards (F-SCHEDE)
#
#   bash 11-two-cards.sh build    [--ramo WT]      compiles the worktree's product (src/build-in-container.sh, as the user)
#   bash 11-two-cards.sh assemble [--ramo WT] [--stage DIR]   product + benches flat in DIR (11-assemble-product.sh)
#   bash 11-two-cards.sh start  <gnome|kde|xfce|lxqt> [--swap] [--render-node intel|amd|/dev/dri/renderDN] [--stage DIR]
#   bash 11-two-cards.sh stop   <desktop|all>
#   bash 11-two-cards.sh status [desktop|all]
#
# The box is `rete11-due-<desktop>` (ports 8531..8534), from the image `rete11/<desktop>:p0` of the four rete11-* boxes,
# which are NOT touched (and 11-start.sh is neither read at run time nor changed).  ⛔ It is the ONLY box with two cards:
# "Always ONE card" of 11-start.sh holds for the four.  ⚠ While it is up, no performance measure on either card.
#
#   --swap          the two cards exchange their NAMES inside (the Intel is renderD129/card1, the Radeon renderD128/card0 when
#                   the host has it the other way round): the simulation of «renderD128 and renderD129 swap between boots».
#                   /sys/class/drm is bind-mounted from a copy with the names exchanged too, so that what the product reads by
#                   name (driver, PCI address, boot_vga) says the truth about the node of that name.  ⚠ NOT TRIED: the minors
#                   do not follow (226:128 is called renderD129), /sys/dev/char/226:N stays the host's; `start` checks by
#                   name (driver, PCI, boot_vga) and tears down if the box is not what was asked.
#   --render-node   passed to the box's server (`--render-node /dev/dri/renderDN`, the encoder's fallback): secondary.
#                   `intel`/`amd` = the card with that driver, by the name it has INSIDE (so --swap is taken into account).
#
# The state of a box is in $ROOT/stato/<desktop>.env (KEY=VALUE, readable by all): the test F-SCHEDE reads it to know
# the port, the container and, per card, the PCI address, the names inside and boot_vga.
# ⛔ `start`, `status` and `stop` need root: they ask for it themselves (REMOTIX_SUDO_PASSWORD or ~/SERVER.ssh, via `sudo -S`).
# Clean teardown: a `start` that fails after the container exists removes it; `stop` also removes state and /sys copy.
# ===========================================================================
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../.." && pwd)
ROOT=${REMOTIX_DUE_ROOT:-/media/REMOTIX-15/lavori/due-schede}
STATE=$ROOT/stato

ok()  { printf '  \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '  \033[1;31mNO\033[0m  %s\n' "$*"; }
log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

VERB=${1:-}
[ $# -gt 0 ] && shift
DESK=""; SWAP=0; RENDER_ARG=""; RAMO=$TREE; STAGE=${REMOTIX_DUE_STAGE:-$ROOT/rete11}
case "$VERB" in start|stop|status) if [ $# -gt 0 ] && [[ $1 != --* ]]; then DESK=$1; shift; fi ;; esac
while [ $# -gt 0 ]; do
	case $1 in
	--swap) SWAP=1; shift ;;
	--render-node) [ $# -ge 2 ] || { ko "--render-node wants a value"; exit 2; }; RENDER_ARG=$2; shift 2 ;;
	--ramo) [ $# -ge 2 ] || { ko "--ramo wants a worktree"; exit 2; }; RAMO=$(cd "$2" && pwd) || exit 2; shift 2 ;;
	--stage) [ $# -ge 2 ] || { ko "--stage wants a folder"; exit 2; }; STAGE=$2; shift 2 ;;
	*) ko "unknown argument: $1"; exit 2 ;;
	esac
done
mkdir -p "$ROOT" "$STATE" || exit 1
chmod a+rx "$ROOT" "$STATE" 2>/dev/null

# ---- the verbs that run as the USER (files of the worktree must not become root's) -------------------------
case "$VERB" in
build)
	[ -f "$RAMO/src/build-in-container.sh" ] || { ko "no $RAMO/src/build-in-container.sh"; exit 2; }
	log "Compiling $RAMO"
	nice -n 19 bash "$RAMO/src/build-in-container.sh" || exit 1
	ok "built: $RAMO/src/remotix"
	exit 0 ;;
assemble)
	[ -f "$RAMO/benches/11-boxes/11-assemble-product.sh" ] || { ko "no 11-assemble-product.sh in $RAMO"; exit 2; }
	log "Assembling the product of $RAMO in $STAGE"
	# the stage is a private copy: rete11/ is not touched
	REMOTIX_RETE11=$STAGE bash "$RAMO/benches/11-boxes/11-assemble-product.sh" || exit 1
	ok "stage $STAGE: remotix $(md5sum "$STAGE/prodotto/remotix" | cut -c1-8), page $(md5sum "$STAGE/prodotto/page.html" | cut -c1-8)"
	exit 0 ;;
start|stop|status) ;;
*) sed -n '3,/^# ====/{/^# ====/d; s/^# \{0,1\}//; p;}' "$0"; exit 2 ;;
esac

# ---- the rest runs as root ---------------------------------------------------------------------------------
if [ "$(id -u)" != 0 ]; then
	pw=${REMOTIX_SUDO_PASSWORD:-$(sed -n 's/^pass:[[:space:]]*//p' "$HOME/SERVER.ssh" 2>/dev/null | head -1)}
	args=("$VERB")
	[ -n "$DESK" ] && args+=("$DESK")
	[ "$SWAP" = 1 ] && args+=(--swap)
	[ -n "$RENDER_ARG" ] && args+=(--render-node "$RENDER_ARG")
	args+=(--stage "$STAGE")
	printf '%s\n' "$pw" | sudo -S -p "" env REMOTIX_DUE_ROOT="$ROOT" bash "$(readlink -f "$0")" "${args[@]}"
	exit $?
fi

case "$DESK" in
gnome) PORT=8531 ;; kde) PORT=8532 ;; xfce) PORT=8533 ;; lxqt) PORT=8534 ;;
all) [ "$VERB" = start ] && { ko "start wants one desktop"; exit 2; } ;;
'') [ "$VERB" = status ] || { ko "$VERB wants a desktop: gnome|kde|xfce|lxqt"; exit 2; } ;;
*) ko "desktop «$DESK»: gnome|kde|xfce|lxqt"; exit 2 ;;
esac

teardown() {      # teardown <desktop>: container, state, /sys copy.  Always safe to repeat.
	local d=$1 n=rete11-due-$1 ov=$STATE/sysdrm-$1
	podman kill -s KILL "$n" >/dev/null 2>&1
	podman rm -f -t 0 "$n" >/dev/null 2>&1
	unlink "$STATE/$d.env" 2>/dev/null
	# the /sys copy holds only symlinks: they are unlinked one by one, never followed (and never if it is still a mount)
	if [ -d "$ov" ]; then
		if findmnt -rn "$ov" >/dev/null 2>&1; then
			ko "$ov is still a mount point: NOT touched"
		else
			find "$ov" -mindepth 1 -maxdepth 1 -type l -delete
			rmdir "$ov" 2>/dev/null
		fi
	fi
}

case "$VERB" in
stop)
	for d in $( [ "$DESK" = all ] && echo "gnome kde xfce lxqt" || echo "$DESK" ); do
		teardown "$d"; ok "rete11-due-$d off (container, state, /sys copy)"
	done
	exit 0 ;;
status)
	for d in $( { [ -z "$DESK" ] || [ "$DESK" = all ]; } && echo "gnome kde xfce lxqt" || echo "$DESK" ); do
		n=rete11-due-$d
		if [ "$(podman inspect --format '{{.State.Running}}' "$n" 2>/dev/null)" = true ]; then
			printf '%s: UP  ' "$n"
			if ss -ltn 2>/dev/null | grep -q ":$(sed -n 's/^PORT=//p' "$STATE/$d.env" 2>/dev/null) "; then printf 'listening  '; else printf 'NOT listening  '; fi
			grep -E '^(PORT|SWAP|RENDER_NODE|PRIMARY_PCI)=' "$STATE/$d.env" 2>/dev/null | tr '\n' ' '; echo
			grep '^CARD_' "$STATE/$d.env" 2>/dev/null | sed 's/^/      /'
		else
			echo "$n: off"
		fi
	done
	exit 0 ;;
esac

# ===========================================================================  start
NAME=rete11-due-$DESK
IMAGE=rete11/$DESK:p0
STARTED=0
cleanup() { [ "$STARTED" = 1 ] || { ko "start failed: removing $NAME (clean teardown)"; teardown "$DESK"; }; }
trap cleanup EXIT

podman image exists "$IMAGE" || { ko "the image $IMAGE is not there (build it with 11-start.sh build $DESK)"; exit 1; }
[ -x "$STAGE/prodotto/remotix" ] && [ -f "$STAGE/prodotto/page.html" ] || { ko "no product in $STAGE/prodotto: run «assemble» first"; exit 1; }
for f in remotix.pam remotix-no-poweroff.rules remotix-power-keys.conf; do
	[ -f "$STAGE/prodotto/$f" ] || { ko "$STAGE/prodotto/$f is missing: run «assemble» again"; exit 1; }
done
if podman ps --format '{{.Names}}' 2>/dev/null | grep -q '^rete11-[a-z]*$'; then
	echo "  --  note: the rete11-* boxes are up; they are not touched (they hold one card, this one holds both)"
fi
if ss -ltn 2>/dev/null | grep -q ":$PORT "; then ko "port $PORT is already in use"; exit 1; fi

log "The cards (found by driver and PCI address, as 11-start.sh does)"
CPCI=(); CDRV=(); CLAB=(); HCARD=(); HREND=(); CBOOT=()
for C in /sys/class/drm/card[0-9]*; do
	case "$C" in *-*) continue ;; esac
	[ -e "$C/device/driver" ] || continue
	pci=$(basename "$(readlink -f "$C/device")")
	drv=$(basename "$(readlink -f "$C/device/driver")")
	hc=$(readlink -f "/dev/dri/by-path/pci-$pci-card" 2>/dev/null)
	hr=$(readlink -f "/dev/dri/by-path/pci-$pci-render" 2>/dev/null)
	[ -e "$hc" ] && [ -e "$hr" ] || continue
	case "$drv" in i915|xe) lab=intel ;; amdgpu) lab=amd ;; *) lab=$drv ;; esac
	CPCI+=("$pci"); CDRV+=("$drv"); CLAB+=("$lab"); HCARD+=("$hc"); HREND+=("$hr")
	CBOOT+=("$(cat "$C/device/boot_vga" 2>/dev/null || echo 0)")
done
[ "${#CPCI[@]}" = 2 ] || { ko "I need exactly 2 cards with a render node, found ${#CPCI[@]}"; exit 1; }
# the names the cards have INSIDE: the host's own, or exchanged by --swap
INC=("${HCARD[0]}" "${HCARD[1]}"); INR=("${HREND[0]}" "${HREND[1]}")
if [ "$SWAP" = 1 ]; then INC=("${HCARD[1]}" "${HCARD[0]}"); INR=("${HREND[1]}" "${HREND[0]}"); fi
PRIMARY=""
for i in 0 1; do
	[ "${CBOOT[$i]}" = 1 ] && PRIMARY=${CPCI[$i]}
	ok "card $i: ${CLAB[$i]} (${CDRV[$i]}) PCI ${CPCI[$i]} · host ${HCARD[$i]} ${HREND[$i]} → inside ${INC[$i]} ${INR[$i]} · boot_vga=${CBOOT[$i]}"
done
if [ -n "$PRIMARY" ]; then ok "BIOS primary card (boot_vga=1): $PRIMARY"; else echo "  --  no card has boot_vga=1: the product's rule falls to the lowest PCI address"; fi

# --render-node: «intel»/«amd» = the card with that driver, by its name INSIDE
REQ=""
case "$RENDER_ARG" in
'') ;;
/dev/dri/renderD[0-9]*) REQ=$RENDER_ARG ;;
*) for i in 0 1; do [ "${CLAB[$i]}" = "$RENDER_ARG" ] && REQ=${INR[$i]}; done
   [ -n "$REQ" ] || { ko "--render-node «$RENDER_ARG»: intel, amd or /dev/dri/renderDN"; exit 2; } ;;
esac

teardown "$DESK"      # the same box of an earlier run, if any (only rete11-due-<desktop>)

# --swap: /sys/class/drm with the names exchanged (symlinks to the real devices)
MOUNT_SYS=()
if [ "$SWAP" = 1 ]; then
	OV=$STATE/sysdrm-$DESK
	mkdir -p "$OV" || exit 1
	h0c=$(basename "${HCARD[0]}"); h1c=$(basename "${HCARD[1]}"); h0r=$(basename "${HREND[0]}"); h1r=$(basename "${HREND[1]}")
	for e in /sys/class/drm/*; do
		b=$(basename "$e")
		case "$b" in
		"$h0c") nb=$h1c ;; "$h1c") nb=$h0c ;;
		"$h0c"-*) nb=$h1c${b#"$h0c"} ;; "$h1c"-*) nb=$h0c${b#"$h1c"} ;;
		"$h0r") nb=$h1r ;; "$h1r") nb=$h0r ;;
		*) nb=$b ;;
		esac
		[ -d "$e" ] || continue
		ln -sfn "$(readlink -f "$e")" "$OV/$nb"
	done
	MOUNT_SYS=(-v "$OV:/sys/class/drm:ro")
	ok "/sys/class/drm copy with the names exchanged: $OV"
fi

COMMON_CAPS="--cap-add=SYS_ADMIN"
case "$DESK" in kde) CAPS="$COMMON_CAPS --cap-add=SYS_NICE --cap-add=WAKE_ALARM" ;; *) CAPS="$COMMON_CAPS" ;; esac

log "Starting $NAME (both cards)"
# shellcheck disable=SC2086
podman run -d --replace --name "$NAME" \
	--systemd=always --pids-limit 16384 --network=host \
	--device "${HCARD[0]}:${INC[0]}" --device "${HREND[0]}:${INR[0]}" \
	--device "${HCARD[1]}:${INC[1]}" --device "${HREND[1]}:${INR[1]}" \
	--cap-add=AUDIT_WRITE --cap-add=AUDIT_CONTROL $CAPS "${MOUNT_SYS[@]}" \
	--label remotix.due=1 -v "$STAGE:/rete11:ro" "$IMAGE" >/dev/null || exit 1
for _ in $(seq 1 60); do
	S=$(podman exec "$NAME" systemctl is-system-running 2>&1 | head -1)
	case "$S" in running|degraded) break ;; esac
	sleep 0.5
done
ok "$NAME started (internal state: ${S:-unknown})"
podman exec "$NAME" sh -c "mkdir -p /var/lib/rete11 && date +%s > /var/lib/rete11/nascita" >/dev/null 2>&1

# every node must have a group with a name inside (as 11-start.sh: the gid from the node, the name from the host)
for N in "${HCARD[@]}" "${HREND[@]}"; do
	G=$(stat -c %g "$N" 2>/dev/null) || continue
	podman exec "$NAME" getent group "$G" >/dev/null 2>&1 && continue
	GN=$(getent group "$G" 2>/dev/null | cut -d: -f1)
	{ [ -z "$GN" ] || [ "$GN" = remotix-nogpu ]; } && GN=scheda$G
	podman exec "$NAME" groupadd -g "$G" "$GN" >/dev/null 2>&1 || podman exec "$NAME" groupadd -g "$G" "scheda$G" >/dev/null 2>&1 \
		|| ko "gid $G of $N has NO name inside"
done

# «written is not in force»: LOOK inside at the names and at what the product will read by name
WANT=$(printf '%s\n' "$(basename "${INC[0]}")" "$(basename "${INC[1]}")" "$(basename "${INR[0]}")" "$(basename "${INR[1]}")" | sort | tr '\n' ' ')
GOT=$(podman exec "$NAME" sh -c 'ls /dev/dri | sort | tr "\n" " "' 2>/dev/null)
[ "$GOT" = "$WANT" ] || { ko "inside /dev/dri there is «$GOT», not «$WANT»"; exit 1; }
ok "inside /dev/dri: $GOT"
for i in 0 1; do
	rn=$(basename "${INR[$i]}")
	gp=$(podman exec "$NAME" sh -c "basename \$(readlink -f /sys/class/drm/$rn/device)" 2>/dev/null)
	gb=$(podman exec "$NAME" sh -c "cat /sys/class/drm/$rn/device/boot_vga 2>/dev/null || echo 0" 2>/dev/null)
	if [ "$gp" = "${CPCI[$i]}" ] && [ "$gb" = "${CBOOT[$i]}" ]; then
		ok "inside, $rn → PCI $gp, boot_vga=$gb (${CLAB[$i]}): what the product reads by name is true"
	else
		ko "inside, $rn → PCI «$gp» boot_vga «$gb», expected ${CPCI[$i]} / ${CBOOT[$i]}: the /sys view does not follow the names"
		exit 1
	fi
done

# --swap and the dev_t: code that goes through the node's major:minor (render_node.c node_of_device, wlroots.c) reads
# /sys/dev/char/226:M/device/drm, which is the HOST's; the nodes inside keep the host minors.  Is that view true by name?
SWAP_DEVT=1
for n in "${INC[@]}" "${INR[@]}"; do
	nb=$(basename "$n")
	m=$(podman exec "$NAME" stat -c %T "/dev/dri/$nb" 2>/dev/null)
	if ! podman exec "$NAME" sh -c "ls /sys/dev/char/226:\$((0x$m))/device/drm 2>/dev/null | grep -qx $nb"; then
		SWAP_DEVT=0; echo "  --  dev_t: /dev/dri/$nb has minor $((0x$m)) and /sys/dev/char/226:$((0x$m))/device/drm does not list it"
	fi
done
if [ "$SWAP_DEVT" = 1 ]; then ok "dev_t: every node's major:minor leads, through /sys/dev/char, to a device that lists that very name"
else echo "  --  SWAP_DEVT=0: the simulation is NOT faithful for code that goes through the dev_t; the test will judge only the card given to the compositor"; fi

log "Putting the product inside $NAME"
read -r -d '' INSTALL <<'XEOF'
set -e
mkdir -p /opt/remotix/lib /var/lib/rete11/certificati /var/lib/rete11/rilievo
rm -f /opt/remotix/remotix
cp /rete11/prodotto/remotix /opt/remotix/
cp /rete11/prodotto/page.html /opt/remotix/
cp /rete11/prodotto/remotix.pam /etc/pam.d/remotix
if [ ! -f /etc/remotix/denied-users ]; then
	install -D -m 644 -o root -g root /dev/null /etc/remotix/denied-users
	echo root > /etc/remotix/denied-users
fi
install -D -m 644 /rete11/prodotto/remotix-no-poweroff.rules /etc/polkit-1/rules.d/50-remotix-no-poweroff.rules
install -D -m 644 /rete11/prodotto/remotix-power-keys.conf /etc/systemd/logind.conf.d/remotix-power-keys.conf
mkdir -p /etc/systemd/sleep.conf.d
printf "[Sleep]\nAllowSuspend=no\nAllowHibernation=no\nAllowSuspendThenHibernate=no\nAllowHybridSleep=no\n" > /etc/systemd/sleep.conf.d/remotix-no-suspend.conf
systemctl restart polkit >/dev/null 2>&1 || true
systemctl reload systemd-logind >/dev/null 2>&1 || true
mkdir -p /usr/share/applications
printf "[Desktop Entry]\nType=Application\nName=REMOTIX\nComment=The desktop in the browser\nExec=/opt/remotix/remotix\nNoDisplay=true\nX-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1\n" > /usr/share/applications/org.kde.remotix.desktop
chmod 644 /usr/share/applications/org.kde.remotix.desktop
rm -f /opt/remotix/lib/*
cp -a /rete11/prodotto/lib/* /opt/remotix/lib/
echo /opt/remotix/lib > /etc/ld.so.conf.d/rete11.conf
ldconfig 2>/dev/null || true
XEOF
podman exec "$NAME" sh -c "$INSTALL" || { ko "I could not put the product inside"; exit 1; }
MISSING=$(podman exec "$NAME" sh -c 'ldd /opt/remotix/remotix | grep -c "not found"' 2>/dev/null)
[ "${MISSING:-9}" = 0 ] || { ko "$MISSING libraries do not resolve"; exit 1; }
ok "the product is inside ($(podman exec "$NAME" md5sum /opt/remotix/remotix | cut -c1-8)), libraries resolve"

log "Starting the server inside $NAME on port $PORT"
# the guard runs INSIDE the box: the 1.0 binary knows no --no-split (this box measures ONE process, like the four)
NOSPLIT='$(grep -qa -e "--no-split" /opt/remotix/remotix && echo --no-split)'
RN=""; [ -n "$REQ" ] && RN="--render-node $REQ"
podman exec "$NAME" sh -c "
	systemctl stop rete11-server 2>/dev/null
	systemctl reset-failed rete11-server 2>/dev/null
	rm -f /var/lib/rete11/registro.log
	systemd-run --unit=rete11-server \
		--working-directory=/opt/remotix \
		--property=StandardOutput=append:/var/lib/rete11/registro.log \
		--property=StandardError=append:/var/lib/rete11/registro.log \
		--property=KillMode=mixed \
		/opt/remotix/remotix --address 0.0.0.0 $NOSPLIT --name 127.0.0.1 --port $PORT $RN \
		--certificates /var/lib/rete11/certificati --page /opt/remotix/page.html \
		--ban-file /var/lib/rete11/ban --command-socket /var/lib/rete11/command.sock \
		--survey /var/lib/rete11/rilievo --verbose --journal
" >/dev/null 2>&1
READY=0
for _ in $(seq 1 40); do
	podman exec "$NAME" grep -q "ready: https" /var/lib/rete11/registro.log 2>/dev/null && { READY=1; break; }
	sleep 0.5
done
if [ "$READY" != 1 ]; then
	ko "the server did not say it was ready within 20 s"
	podman exec "$NAME" tail -8 /var/lib/rete11/registro.log 2>/dev/null | sed 's/^/      /'
	exit 1
fi
ok "the server listens on $PORT${REQ:+ (--render-node $REQ)}"

# the state, for the test
{
	echo "NAME=$NAME"; echo "DESKTOP=$DESK"; echo "PORT=$PORT"; echo "SWAP=$SWAP"; echo "RENDER_NODE=$REQ"
	echo "PRIMARY_PCI=$PRIMARY"; echo "SWAP_DEVT=$SWAP_DEVT"
	for i in 0 1; do echo "CARD_$i=${CLAB[$i]}|${CPCI[$i]}|${CDRV[$i]}|$(basename "${INR[$i]}")|$(basename "${INC[$i]}")|${CBOOT[$i]}"; done
} > "$STATE/$DESK.env"
chmod a+r "$STATE/$DESK.env"
STARTED=1
ok "state: $STATE/$DESK.env"
exit 0
