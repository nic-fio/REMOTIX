#!/bin/bash
# ===========================================================================
# 15-d006-server.sh — a product server WITH A PAGE OF ITS OWN, inside a
#                     box, to try the D-006 cure (the Opus decoder
#                     in WebAssembly) without touching the boxes' product
#
#   bash 15-d006-server.sh start <desktop> <page.html sul server> [options]
#   bash 15-d006-server.sh stop  <desktop>
#   bash 15-d006-server.sh status   <desktop>
#   bash 15-d006-server.sh log <desktop> [da_riga]
#
# ⭐ It is `15-g7-server.sh` with three differences: the page is OUR file
#    (copied into the box with `podman cp` into /var/lib/rete15-d006/), the unit
#    is `rete15-d006` and the ports are
#
#      kde 8642 · lxqt 8641        (only these two boxes: the others belong to others)
#
# ⛔ Same binary /opt/remotix/remotix, READ ONLY: /opt/remotix and the
#    boxes' product are not touched.
# ⛔ It runs ON THE SERVER as nicfio (sudo with the password).
# ===========================================================================
set -uo pipefail
if [ "${1:-}" = "--remote" ]; then
	shift
	ssh -o BatchMode=yes nicfio@192.168.0.2 \
		"bash ${REMOTIX_CHECK_DIR:-/media/REMOTIX/src/controllo}/benches/15-suite/15-d006-server.sh $*" 2>&1 \
		| grep --line-buffered -v '^tput'
	exit "${PIPESTATUS[0]}"
fi

ACTION=${1:-}
DESKTOP=${2:-}
shift 2 2>/dev/null || true
case "$DESKTOP" in
kde) PORT=8642 ;;
lxqt) PORT=8641 ;;
*) echo "usage: $0 start|stop|status|log kde|lxqt [options]"; exit 2 ;;
esac
NAME="rete11-$DESKTOP"
UNIT=rete15-d006
DIR=/var/lib/rete15-d006
REG=$DIR/registro.log

inside() {
	printf '%s\n' "${REMOTIX_SUDO_PASSWORD:-$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh" 2>/dev/null)}" | sudo -S -p '' podman exec "$NAME" sh -c "$1"
}

case "$ACTION" in
start)
	PAGE=${1:-}
	shift 1 2>/dev/null || true
	[ -s "$PAGE" ] || { echo "⛔ the page «$PAGE» is not there"; exit 2; }
	inside "mkdir -p $DIR"
	printf '%s\n' "${REMOTIX_SUDO_PASSWORD:-$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh" 2>/dev/null)}" | sudo -S -p '' podman cp "$PAGE" "$NAME:$DIR/page.html" || exit 1
	echo "⭐ page $(sha256sum "$PAGE" | cut -c1-16) → $NAME:$DIR/page.html"
	# ⛔ Only OUR unit: rete11-server is not touched.
	inside "
		systemctl stop $UNIT 2>/dev/null
		systemctl reset-failed $UNIT 2>/dev/null
		mkdir -p $DIR/rilievo
		[ -d $DIR/certificati ] || cp -a /var/lib/rete11/certificati $DIR/certificati
		# ⛔ The log is NOT deleted: it is set aside (D-011, 25 Sep 2026 —
		#    the restart between the phases of 15-f022 threw away exactly the lines that
		#    explained the BLOCKED).  The last 30 are kept.
		[ -s $REG ] && mv $REG $DIR/registro-\$(date +%Y%m%d-%H%M%S)-\$\$.log
		ls -1t $DIR/registro-*.log 2>/dev/null | tail -n +31 | xargs -r rm -f
		rm -f $DIR/ban $DIR/command.sock
		systemd-run --unit=$UNIT \
			--working-directory=/opt/remotix \
			--property=StandardOutput=append:$REG \
			--property=StandardError=append:$REG \
			--property=KillMode=mixed \
			/opt/remotix/remotix --address 0.0.0.0 --name 127.0.0.1 --port $PORT \
			--certificates $DIR/certificati --page $DIR/page.html \
			--ban-file $DIR/ban --command-socket $DIR/command.sock \
			--survey $DIR/rilievo --verbose $*
	" >/dev/null 2>&1
	for _ in $(seq 1 40); do
		if inside "grep -q 'ready: https' $REG" 2>/dev/null; then
			echo "⭐ $UNIT listens on $PORT in $NAME ($*)"
			inside "grep -a '§5.3, the three clocks' $REG | tail -1" 2>/dev/null | sed 's/^/   /' | cut -c1-220
			exit 0
		fi
		sleep 0.5
	done
	echo "⛔ $UNIT did not say it was ready in 20 s"
	inside "tail -8 $REG" 2>/dev/null | sed 's/^/   /'
	exit 1
	;;
stop)
	# ⚠ `systemctl stop` can stay hung (11-start.sh, line ~450): it is
	#   given a cap and then the whole unit is killed.
	inside "timeout 20 systemctl stop $UNIT 2>/dev/null || systemctl kill -s KILL $UNIT 2>/dev/null; systemctl reset-failed $UNIT 2>/dev/null; true"
	if inside "systemctl is-active -q $UNIT" 2>/dev/null; then
		echo "⛔ $UNIT still active"; exit 1
	fi
	echo "⭐ $UNIT stopped in $NAME"
	;;
status)
	inside "systemctl is-active $UNIT; systemctl show -p MainPID --value $UNIT"
	;;
log)
	DA=${1:-0}
	inside "tail -n +$((DA + 1)) $REG"
	;;
*)
	echo "usage: $0 start|stop|status|log <desktop> [options]"; exit 2 ;;
esac
