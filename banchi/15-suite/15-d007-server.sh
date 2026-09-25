#!/bin/bash
# ===========================================================================
# 15-d007-server.sh — un server del prodotto COL BINARIO DELLA CURA D-007 (le
#                     finestre riportate dentro al riattacco piu' piccolo),
#                     dentro una scatola, senza toccare il prodotto delle scatole
#
#   bash 15-d007-server.sh accendi <desktop> <binario|stock>
#   bash 15-d007-server.sh spegni  <desktop>
#   bash 15-d007-server.sh stato   <desktop>
#   bash 15-d007-server.sh registro <desktop> [da_riga]
#
#   <binario>  un remotix costruito sul server (es. /media/REMOTIX/src/
#              d007-dentro/src/remotix): si copia nella scatola, in
#              /var/lib/rete15-d007/remotix;
#   stock      /opt/remotix/remotix della scatola, SOLO LETTO: e' «la cura
#              spenta» — la stessa scena col prodotto di prima.
#
# ⭐ E' `15-d006-server.sh` con la pagina di serie (quella di /opt/remotix) e
#    il binario scelto.  Unita' `rete15-d007`, porte
#
#      xfce 8651 · lxqt 8654
#
# ⛔ /opt/remotix, /media/REMOTIX/rete11/prodotto e i server 851x non si
#    toccano.  ⛔ Si esegue SUL SERVER come nicfio (sudo con la parola).
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
*) echo "uso: $0 accendi|spegni|stato|registro xfce|lxqt [binario|stock]"; exit 2 ;;
esac
NOME="rete11-$DESKTOP"
UNITA=rete15-d007
DIR=/var/lib/rete15-d007
REG=$DIR/registro.log

dentro() {
	printf 'nicfio\n' | sudo -S -p '' podman exec "$NOME" sh -c "$1"
}

case "$AZIONE" in
accendi)
	BIN=${1:-}
	dentro "mkdir -p $DIR"
	if [ "$BIN" = "stock" ]; then
		ESEGUI=/opt/remotix/remotix
		echo "⭐ binario di SERIE (cura spenta): $ESEGUI $(dentro "sha256sum $ESEGUI" | cut -c1-16)"
	else
		[ -x "$BIN" ] || { echo "⛔ il binario «$BIN» non c'e'"; exit 2; }
		ESEGUI=$DIR/remotix
		dentro "systemctl stop $UNITA 2>/dev/null; true"
		printf 'nicfio\n' | sudo -S -p '' podman cp "$BIN" "$NOME:$ESEGUI" || exit 1
		echo "⭐ binario $(sha256sum "$BIN" | cut -c1-16) → $NOME:$ESEGUI"
	fi
	# ⛔ Solo la NOSTRA unita': rete11-server non si tocca.
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
		if dentro "grep -q 'pronto: https' $REG" 2>/dev/null; then
			echo "⭐ $UNITA ascolta sulla $PORTA in $NOME ($ESEGUI)"
			exit 0
		fi
		sleep 0.5
	done
	echo "⛔ $UNITA non ha detto di essere pronto in 20 s"
	dentro "tail -8 $REG" 2>/dev/null | sed 's/^/   /'
	exit 1
	;;
spegni)
	dentro "timeout 20 systemctl stop $UNITA 2>/dev/null || systemctl kill -s KILL $UNITA 2>/dev/null; systemctl reset-failed $UNITA 2>/dev/null; true"
	if dentro "systemctl is-active -q $UNITA" 2>/dev/null; then
		echo "⛔ $UNITA ancora attiva"; exit 1
	fi
	echo "⭐ $UNITA spenta in $NOME"
	;;
stato)
	dentro "systemctl is-active $UNITA; systemctl show -p MainPID --value $UNITA"
	;;
registro)
	DA=${1:-0}
	dentro "tail -n +$((DA + 1)) $REG"
	;;
*)
	echo "uso: $0 accendi|spegni|stato|registro <desktop> [binario|stock]"; exit 2 ;;
esac
