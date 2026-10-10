#!/bin/bash
# ===========================================================================
# 15-g7-server.sh — the SECOND product server, inside a box, for the
#                   tests of group G7 (the network dropping and the clocks)
#
#   bash 15-g7-server.sh accendi <desktop> [server options...]
#   bash 15-g7-server.sh spegni  <desktop>
#   bash 15-g7-server.sh stato   <desktop>
#   bash 15-g7-server.sh registro <desktop> [da_riga]
#
#   (from the tablet: bash 15-g7-server.sh --remoto accendi gnome ...)
#
# ⭐ WHY A SERVER OF ITS OWN: the G7 tests drop the line (nftables on the
#    port) and shorten the clocks of §5.3 (`--inattivita-s`, `--abbandono-s`).
#    On the 8511-8514 servers this cannot be done: everybody uses them.  ⇒ Same binary
#    (/opt/remotix/remotix), same page, SEPARATE systemd unit
#    (`rete15-g7`), and ITS OWN port, ban-file, command socket, survey, log and
#    certificates in /var/lib/rete15-g7/.
#
#      gnome 8611 · kde 8612 · xfce 8613 · lxqt 8614
#
# ⛔ The certificates are COPIED from /var/lib/rete11/certificati, not
#    shared: the product regenerates the session certificate when the
#    expiry approaches, and two servers writing in the same folder
#    could change it under each other's feet.
# ⛔ The model is `11-accendi.sh server` (the same options), plus the options
#    passed here after the desktop (the shortened clocks).
# ⛔ It runs ON THE SERVER as nicfio (sudo with the password) — or with --remoto.
# ===========================================================================
set -uo pipefail
if [ "${1:-}" = "--remoto" ]; then
	shift
	ssh -o BatchMode=yes nicfio@192.168.0.2 \
		"bash ${REMOTIX_CONTROLLO:-/media/REMOTIX/src/controllo}/banchi/15-suite/15-g7-server.sh $*" 2>&1 \
		| grep --line-buffered -v '^tput'
	exit "${PIPESTATUS[0]}"
fi

AZIONE=${1:-}
DESKTOP=${2:-}
shift 2 2>/dev/null || true
case "$DESKTOP" in
gnome) PORTA=8611 ;;
kde) PORTA=8612 ;;
xfce) PORTA=8613 ;;
lxqt) PORTA=8614 ;;
*) echo "usage: $0 accendi|spegni|stato|registro gnome|kde|xfce|lxqt [options]"; exit 2 ;;
esac
NOME="rete11-$DESKTOP"
UNITA=rete15-g7
DIR=/var/lib/rete15-g7
REG=$DIR/registro.log

dentro() {
	printf '%s\n' "${REMOTIX_PAROLA_SUDO:-$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh" 2>/dev/null)}" | sudo -S -p '' podman exec "$NOME" sh -c "$1"
}

case "$AZIONE" in
accendi)
	# ⛔ Only OUR unit: rete11-server is not touched.
	dentro "
		systemctl stop $UNITA 2>/dev/null
		systemctl reset-failed $UNITA 2>/dev/null
		mkdir -p $DIR/rilievo
		[ -d $DIR/certificati ] || cp -a /var/lib/rete11/certificati $DIR/certificati
		# ⛔ The log is NOT deleted: it is set aside (D-011, 25 Sep 2026 —
		#    the restart between the phases of 15-f022 threw away exactly the lines that
		#    explained the BLOCKED).  The last 30 are kept.
		[ -s $REG ] && mv $REG $DIR/registro-\$(date +%Y%m%d-%H%M%S)-\$\$.log
		ls -1t $DIR/registro-*.log 2>/dev/null | tail -n +31 | xargs -r rm -f
		rm -f $DIR/ban $DIR/comando.sock
		systemd-run --unit=$UNITA \
			--working-directory=/opt/remotix \
			--property=StandardOutput=append:$REG \
			--property=StandardError=append:$REG \
			--property=KillMode=mixed \
			/opt/remotix/remotix --indirizzo 0.0.0.0 --nome 127.0.0.1 --porta $PORTA \
			--certificati $DIR/certificati --pagina /opt/remotix/pagina.html \
			--ban-file $DIR/ban --comando-socket $DIR/comando.sock \
			--rilievo $DIR/rilievo --parlantina $*
	" >/dev/null 2>&1
	for _ in $(seq 1 40); do
		if dentro "grep -q 'ready: https' $REG" 2>/dev/null; then
			echo "⭐ $UNITA listens on $PORTA in $NOME ($*)"
			dentro "grep -a '§5.3, the three clocks' $REG | tail -1" 2>/dev/null | sed 's/^/   /' | cut -c1-220
			exit 0
		fi
		sleep 0.5
	done
	echo "⛔ $UNITA did not say it was ready in 20 s"
	dentro "tail -8 $REG" 2>/dev/null | sed 's/^/   /'
	exit 1
	;;
spegni)
	# ⚠ `systemctl stop` can stay hung (11-accendi.sh, line ~450): it is
	#   given a cap and then the whole unit is killed.
	dentro "timeout 20 systemctl stop $UNITA 2>/dev/null || systemctl kill -s KILL $UNITA 2>/dev/null; systemctl reset-failed $UNITA 2>/dev/null; true"
	if dentro "systemctl is-active -q $UNITA" 2>/dev/null; then
		echo "⛔ $UNITA still active"; exit 1
	fi
	echo "⭐ $UNITA stopped in $NOME"
	;;
stato)
	dentro "systemctl is-active $UNITA; systemctl show -p MainPID --value $UNITA"
	;;
registro)
	DA=${1:-0}
	dentro "tail -n +$((DA + 1)) $REG"
	;;
*)
	echo "usage: $0 accendi|spegni|stato|registro <desktop> [options]"; exit 2 ;;
esac
