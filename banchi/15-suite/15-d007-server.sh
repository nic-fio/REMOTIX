#!/bin/bash
# ===========================================================================
# 15-d007-server.sh — a product server WITH THE BINARY OF THE D-007 CURE (the
#                     windows brought back inside at the smaller reattach),
#                     inside a box, without touching the boxes' product
#
#   bash 15-d007-server.sh turn_on <desktop> <binary|stock>
#   bash 15-d007-server.sh turn_off  <desktop>
#   bash 15-d007-server.sh state   <desktop>
#   bash 15-d007-server.sh logbook <desktop> [da_riga]
#
#   <binary>  a remotix built on the server (e.g. /media/REMOTIX/src/
#              d007-dentro/src/remotix): it is copied into the box, into
#              /var/lib/rete15-d007/remotix;
#   stock      the box's /opt/remotix/remotix, READ ONLY: it is «the cure
#              off» — the same scene with the previous product.
#
# ⭐ It is `15-d006-server.sh` with the standard page (the one in /opt/remotix) and
#    the chosen binary.  Unit `rete15-d007`, ports
#
#      xfce 8651 · lxqt 8654
#
# ⛔ /opt/remotix, /media/REMOTIX/rete11/prodotto and the 851x servers are not
#    touched.  ⛔ It runs ON THE SERVER as nicfio (sudo with the password).
# ===========================================================================
set -uo pipefail
if [ "${1:-}" = "--remote" ]; then
	shift
	ssh -o BatchMode=yes nicfio@192.168.0.2 \
		"bash ${REMOTIX_CHECK:-/media/REMOTIX/src/controllo}/banchi/15-suite/15-d007-server.sh $*" 2>&1 \
		| grep --line-buffered -v '^tput'
	exit "${PIPESTATUS[0]}"
fi

ACTION=${1:-}
DESKTOP=${2:-}
shift 2 2>/dev/null || true
case "$DESKTOP" in
xfce) PORT=8651 ;;
lxqt) PORT=8654 ;;
*) echo "usage: $0 turn_on|turn_off|state|logbook xfce|lxqt [binary|stock]"; exit 2 ;;
esac
LABEL_NAME="rete11-$DESKTOP"
UNIT=rete15-d007
DIR=/var/lib/rete15-d007
REG=$DIR/registro.log

inside() {
	printf '%s\n' "${REMOTIX_SUDO_PASSWORD:-$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh" 2>/dev/null)}" | sudo -S -p '' podman exec "$LABEL_NAME" sh -c "$1"
}

case "$ACTION" in
turn_on)
	BIN=${1:-}
	inside "mkdir -p $DIR"
	if [ "$BIN" = "stock" ]; then
		RUN=/opt/remotix/remotix
		echo "⭐ STANDARD binary (cure off): $RUN $(inside "sha256sum $RUN" | cut -c1-16)"
	else
		[ -x "$BIN" ] || { echo "⛔ the binary «$BIN» is not there"; exit 2; }
		RUN=$DIR/remotix
		inside "systemctl stop $UNIT 2>/dev/null; true"
		printf '%s\n' "${REMOTIX_SUDO_PASSWORD:-$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh" 2>/dev/null)}" | sudo -S -p '' podman cp "$BIN" "$LABEL_NAME:$RUN" || exit 1
		echo "⭐ binary $(sha256sum "$BIN" | cut -c1-16) → $LABEL_NAME:$RUN"
	fi
	# ⛔ Only OUR unit: rete11-server is not touched.
	inside "
		systemctl stop $UNIT 2>/dev/null
		systemctl reset-failed $UNIT 2>/dev/null
		mkdir -p $DIR/survey
		[ -d $DIR/certificates ] || cp -a /var/lib/rete11/certificates $DIR/certificates
		[ -s $REG ] && mv $REG $DIR/logbook-\$(date +%Y%m%d-%H%M%S)-\$\$.log
		ls -1t $DIR/logbook-*.log 2>/dev/null | tail -n +31 | xargs -r rm -f
		rm -f $DIR/ban $DIR/command.sock
		systemd-run --unit=$UNIT \
			--working-directory=/opt/remotix \
			--property=StandardOutput=append:$REG \
			--property=StandardError=append:$REG \
			--property=KillMode=mixed \
			$RUN --address 0.0.0.0 --label_name 127.0.0.1 --port $PORT \
			--certificates $DIR/certificates \
			--ban-file $DIR/ban --command-socket $DIR/command.sock \
			--survey $DIR/survey --chatter
	" >/dev/null 2>&1
	for _ in $(seq 1 40); do
		if inside "grep -q 'ready: https' $REG" 2>/dev/null; then
			echo "⭐ $UNIT listens on $PORT in $LABEL_NAME ($RUN)"
			exit 0
		fi
		sleep 0.5
	done
	echo "⛔ $UNIT did not say it was ready in 20 s"
	inside "tail -8 $REG" 2>/dev/null | sed 's/^/   /'
	exit 1
	;;
turn_off)
	inside "timeout 20 systemctl stop $UNIT 2>/dev/null || systemctl kill -s KILL $UNIT 2>/dev/null; systemctl reset-failed $UNIT 2>/dev/null; true"
	if inside "systemctl is-active -q $UNIT" 2>/dev/null; then
		echo "⛔ $UNIT still active"; exit 1
	fi
	echo "⭐ $UNIT stopped in $LABEL_NAME"
	;;
state)
	inside "systemctl is-active $UNIT; systemctl show -p MainPID --value $UNIT"
	;;
logbook)
	DA=${1:-0}
	inside "tail -n +$((DA + 1)) $REG"
	;;
*)
	echo "usage: $0 turn_on|turn_off|state|logbook <desktop> [binary|stock]"; exit 2 ;;
esac
