#!/bin/bash
# ===========================================================================
# 15-d007-server.sh — a product server WITH THE BINARY OF THE D-007 CURE (the
#                     windows brought back inside at the smaller reattach),
#                     inside a box, without touching the boxes' product
#
#   bash 15-d007-server.sh accendi <desktop> <binario|stock>
#   bash 15-d007-server.sh spegni  <desktop>
#   bash 15-d007-server.sh stato   <desktop>
#   bash 15-d007-server.sh registro <desktop> [da_riga]
#
#   <binario>  a remotix built on the server (e.g. /media/REMOTIX/src/
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
if [ "${1:-}" = "--remoto" ]; then
	shift
	ssh -o BatchMode=yes nicfio@192.168.0.2 \
		"bash ${REMOTIX_CONTROLLO:-/media/REMOTIX/src/controllo}/banchi/15-suite/15-d007-server.sh $*" 2>&1 \
		| grep --line-buffered -v '^tput'
	exit "${PIPESTATUS[0]}"
fi

AZIONE=${1:-}
DESKTOP=${2:-}
shift 2 2>/dev/null || true
case "$DESKTOP" in
xfce) PORTA=8651 ;;
lxqt) PORTA=8654 ;;
*) echo "usage: $0 accendi|spegni|stato|registro xfce|lxqt [binario|stock]"; exit 2 ;;
esac
NOME="rete11-$DESKTOP"
UNITA=rete15-d007
DIR=/var/lib/rete15-d007
REG=$DIR/registro.log

dentro() {
	printf '%s\n' "${REMOTIX_PAROLA_SUDO:-$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh" 2>/dev/null)}" | sudo -S -p '' podman exec "$NOME" sh -c "$1"
}

case "$AZIONE" in
accendi)
	BIN=${1:-}
	dentro "mkdir -p $DIR"
	if [ "$BIN" = "stock" ]; then
		ESEGUI=/opt/remotix/remotix
		echo "⭐ STANDARD binary (cure off): $ESEGUI $(dentro "sha256sum $ESEGUI" | cut -c1-16)"
	else
		[ -x "$BIN" ] || { echo "⛔ the binary «$BIN» is not there"; exit 2; }
		ESEGUI=$DIR/remotix
		dentro "systemctl stop $UNITA 2>/dev/null; true"
		printf '%s\n' "${REMOTIX_PAROLA_SUDO:-$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh" 2>/dev/null)}" | sudo -S -p '' podman cp "$BIN" "$NOME:$ESEGUI" || exit 1
		echo "⭐ binary $(sha256sum "$BIN" | cut -c1-16) → $NOME:$ESEGUI"
	fi
	# ⛔ Only OUR unit: rete11-server is not touched.
	dentro "
		systemctl stop $UNITA 2>/dev/null
		systemctl reset-failed $UNITA 2>/dev/null
		mkdir -p $DIR/rilievo
		[ -d $DIR/certificati ] || cp -a /var/lib/rete11/certificati $DIR/certificati
		[ -s $REG ] && mv $REG $DIR/registro-\$(date +%Y%m%d-%H%M%S)-\$\$.log
		ls -1t $DIR/registro-*.log 2>/dev/null | tail -n +31 | xargs -r rm -f
		rm -f $DIR/ban $DIR/comando.sock
		systemd-run --unit=$UNITA \
			--working-directory=/opt/remotix \
			--property=StandardOutput=append:$REG \
			--property=StandardError=append:$REG \
			--property=KillMode=mixed \
			$ESEGUI --indirizzo 0.0.0.0 --nome 127.0.0.1 --porta $PORTA \
			--certificati $DIR/certificati \
			--ban-file $DIR/ban --comando-socket $DIR/comando.sock \
			--rilievo $DIR/rilievo --parlantina
	" >/dev/null 2>&1
	for _ in $(seq 1 40); do
		if dentro "grep -q 'ready: https' $REG" 2>/dev/null; then
			echo "⭐ $UNITA listens on $PORTA in $NOME ($ESEGUI)"
			exit 0
		fi
		sleep 0.5
	done
	echo "⛔ $UNITA did not say it was ready in 20 s"
	dentro "tail -8 $REG" 2>/dev/null | sed 's/^/   /'
	exit 1
	;;
spegni)
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
	echo "usage: $0 accendi|spegni|stato|registro <desktop> [binario|stock]"; exit 2 ;;
esac
