#!/bin/bash
# ===========================================================================
# 15-d006-server.sh — a product server WITH A PAGE OF ITS OWN, inside a
#                     box, to try the D-006 cure (the Opus decoder
#                     in WebAssembly) without touching the boxes' product
#
#   bash 15-d006-server.sh accendi <desktop> <pagina.html sul server> [opzioni]
#   bash 15-d006-server.sh spegni  <desktop>
#   bash 15-d006-server.sh stato   <desktop>
#   bash 15-d006-server.sh registro <desktop> [da_riga]
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
if [ "${1:-}" = "--remoto" ]; then
	shift
	ssh -o BatchMode=yes nicfio@192.168.0.2 \
		"bash ${REMOTIX_CONTROLLO:-/media/REMOTIX/src/controllo}/banchi/15-suite/15-d006-server.sh $*" 2>&1 \
		| grep --line-buffered -v '^tput'
	exit "${PIPESTATUS[0]}"
fi

AZIONE=${1:-}
DESKTOP=${2:-}
shift 2 2>/dev/null || true
case "$DESKTOP" in
kde) PORTA=8642 ;;
lxqt) PORTA=8641 ;;
*) echo "usage: $0 accendi|spegni|stato|registro kde|lxqt [options]"; exit 2 ;;
esac
NOME="rete11-$DESKTOP"
UNITA=rete15-d006
DIR=/var/lib/rete15-d006
REG=$DIR/registro.log

dentro() {
	printf '%s\n' "${REMOTIX_PAROLA_SUDO:-$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh" 2>/dev/null)}" | sudo -S -p '' podman exec "$NOME" sh -c "$1"
}

case "$AZIONE" in
accendi)
	PAGINA=${1:-}
	shift 1 2>/dev/null || true
	[ -s "$PAGINA" ] || { echo "⛔ the page «$PAGINA» is not there"; exit 2; }
	dentro "mkdir -p $DIR"
	printf '%s\n' "${REMOTIX_PAROLA_SUDO:-$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh" 2>/dev/null)}" | sudo -S -p '' podman cp "$PAGINA" "$NOME:$DIR/pagina.html" || exit 1
	echo "⭐ page $(sha256sum "$PAGINA" | cut -c1-16) → $NOME:$DIR/pagina.html"
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
			--certificati $DIR/certificati --pagina $DIR/pagina.html \
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
