#!/bin/bash
# ===========================================================================
# 15-d006-server.sh — un server del prodotto CON UNA PAGINA SUA, dentro una
#                     scatola, per provare la cura di D-006 (il decodificatore
#                     Opus in WebAssembly) senza toccare il prodotto delle scatole
#
#   bash 15-d006-server.sh accendi <desktop> <pagina.html sul server> [opzioni]
#   bash 15-d006-server.sh spegni  <desktop>
#   bash 15-d006-server.sh stato   <desktop>
#   bash 15-d006-server.sh registro <desktop> [da_riga]
#
# ⭐ E' `15-g7-server.sh` con tre differenze: la pagina e' un file NOSTRO
#    (copiato nella scatola con `podman cp` in /var/lib/rete15-d006/), l'unita'
#    e' `rete15-d006` e le porte sono
#
#      kde 8642 · lxqt 8641        (solo queste due scatole: le altre sono d'altri)
#
# ⛔ Stesso binario /opt/remotix/remotix, SOLO LETTO: /opt/remotix e il
#    prodotto delle scatole non si toccano.
# ⛔ Si esegue SUL SERVER come nicfio (sudo con la parola).
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
*) echo "uso: $0 accendi|spegni|stato|registro kde|lxqt [opzioni]"; exit 2 ;;
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
	[ -s "$PAGINA" ] || { echo "⛔ la pagina «$PAGINA» non c'e'"; exit 2; }
	dentro "mkdir -p $DIR"
	printf '%s\n' "${REMOTIX_PAROLA_SUDO:-$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh" 2>/dev/null)}" | sudo -S -p '' podman cp "$PAGINA" "$NOME:$DIR/pagina.html" || exit 1
	echo "⭐ pagina $(sha256sum "$PAGINA" | cut -c1-16) → $NOME:$DIR/pagina.html"
	# ⛔ Solo la NOSTRA unita': rete11-server non si tocca.
	dentro "
		systemctl stop $UNITA 2>/dev/null
		systemctl reset-failed $UNITA 2>/dev/null
		mkdir -p $DIR/rilievo
		[ -d $DIR/certificati ] || cp -a /var/lib/rete11/certificati $DIR/certificati
		# ⛔ Il registro NON si cancella: si mette da parte (D-011, 25 set 2026 —
		#    il riavvio fra le fasi di 15-f022 buttava via proprio le righe che
		#    spiegavano il BLOCKED).  Se ne tengono gli ultimi 30.
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
		if dentro "grep -q 'pronto: https' $REG" 2>/dev/null; then
			echo "⭐ $UNITA ascolta sulla $PORTA in $NOME ($*)"
			dentro "grep -a '§5.3, i tre orologi' $REG | tail -1" 2>/dev/null | sed 's/^/   /' | cut -c1-220
			exit 0
		fi
		sleep 0.5
	done
	echo "⛔ $UNITA non ha detto di essere pronto in 20 s"
	dentro "tail -8 $REG" 2>/dev/null | sed 's/^/   /'
	exit 1
	;;
spegni)
	# ⚠ `systemctl stop` puo' restare appeso (11-accendi.sh, riga ~450): si
	#   da' un tetto e poi si uccide l'unita' intera.
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
	echo "uso: $0 accendi|spegni|stato|registro <desktop> [opzioni]"; exit 2 ;;
esac
