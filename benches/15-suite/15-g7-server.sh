#!/bin/bash
# ===========================================================================
# 15-g7-server.sh — the SECOND product server, inside a box, for the
#                   tests of group G7 (the network dropping and the clocks)
#
#   bash 15-g7-server.sh start <desktop> [server options...]
#   bash 15-g7-server.sh stop  <desktop>
#   bash 15-g7-server.sh status   <desktop>
#   bash 15-g7-server.sh log <desktop> [da_riga]
#
#   (from the tablet: bash 15-g7-server.sh --remote start gnome ...)
#
# ⭐ WHY A SERVER OF ITS OWN: the G7 tests drop the line (nftables on the
#    port) and shorten the clocks of §5.3 (`--inactivity-s`, `--abandon-s`).
#    On the 8511-8514 servers this cannot be done: everybody uses them.  ⇒ Same binary
#    (/opt/remotix/remotix), same page, SEPARATE systemd unit
#    (`rete15-g7`), and ITS OWN port, ban-file, command socket, survey, log and
#    certificates in /var/lib/rete15-g7/.
#
#      gnome 8611 · kde 8612 · xfce 8613 · lxqt 8614
#
# ⛔ The certificates are COPIED from /var/lib/rete11/certificates, not
#    shared: the product regenerates the session certificate when the
#    expiry approaches, and two servers writing in the same folder
#    could change it under each other's feet.
# ⛔ The model is `11-start.sh server` (the same options), plus the options
#    passed here after the desktop (the shortened clocks).
# ⛔ It runs ON THE SERVER as nicfio (sudo with the password) — or with --remote.
# ===========================================================================
set -uo pipefail
if [ "${1:-}" = "--remote" ]; then
	shift
	ssh -o BatchMode=yes nicfio@192.168.0.2 \
		"bash ${REMOTIX_CHECK_DIR:-/media/REMOTIX/src/controllo}/benches/15-suite/15-g7-server.sh $*" 2>&1 \
		| grep --line-buffered -v '^tput'
	exit "${PIPESTATUS[0]}"
fi

ACTION=${1:-}
DESKTOP=${2:-}
shift 2 2>/dev/null || true
case "$DESKTOP" in
gnome) PORT=8611 ;;
kde) PORT=8612 ;;
xfce) PORT=8613 ;;
lxqt) PORT=8614 ;;
*) echo "usage: $0 start|stop|status|log gnome|kde|xfce|lxqt [options]"; exit 2 ;;
esac
NAME="rete11-$DESKTOP"
UNIT=rete15-g7
DIR=/var/lib/rete15-g7
REG=$DIR/registro.log

inside() {
	printf '%s\n' "${REMOTIX_SUDO_PASSWORD:-$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh" 2>/dev/null)}" | sudo -S -p '' podman exec "$NAME" sh -c "$1"
}

case "$ACTION" in
start)
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
			--certificates $DIR/certificati --page /opt/remotix/page.html \
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
