#!/bin/bash
# ===========================================================================
# 15-g7-server.sh — il SECONDO server del prodotto, dentro una scatola, per le
#                   prove del gruppo G7 (la rete che cade e gli orologi)
#
#   bash 15-g7-server.sh accendi <desktop> [opzioni del server...]
#   bash 15-g7-server.sh spegni  <desktop>
#   bash 15-g7-server.sh stato   <desktop>
#   bash 15-g7-server.sh registro <desktop> [da_riga]
#
#   (dal tablet: bash 15-g7-server.sh --remoto accendi gnome ...)
#
# ⭐ PERCHE' UN SERVER SUO: le prove di G7 fanno cadere la linea (nftables sulla
#    porta) e accorciano gli orologi di §5.3 (`--inattivita-s`, `--abbandono-s`).
#    Sui server 8511-8514 non si puo': li usano tutti.  ⇒ Stesso binario
#    (/opt/remotix/remotix), stessa pagina, unita' systemd SEPARATA
#    (`rete15-g7`), porta, ban-file, socket di comando, rilievo, registro e
#    certificati SUOI in /var/lib/rete15-g7/.
#
#      gnome 8611 · kde 8612 · xfce 8613 · lxqt 8614
#
# ⛔ I certificati si COPIANO da /var/lib/rete11/certificati, non si
#    condividono: il prodotto rigenera il certificato di sessione quando si
#    avvicina la scadenza, e due server che scrivono nella stessa cartella
#    potrebbero cambiarlo sotto i piedi l'uno dell'altro.
# ⛔ Il modello e' `11-accendi.sh server` (le stesse opzioni), piu' le opzioni
#    passate qui dopo il desktop (gli orologi accorciati).
# ⛔ Si esegue SUL SERVER come nicfio (sudo con la parola) — o con --remoto.
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
*) echo "uso: $0 accendi|spegni|stato|registro gnome|kde|xfce|lxqt [opzioni]"; exit 2 ;;
esac
NOME="rete11-$DESKTOP"
UNITA=rete15-g7
DIR=/var/lib/rete15-g7
REG=$DIR/registro.log

dentro() {
	printf 'nicfio\n' | sudo -S -p '' podman exec "$NOME" sh -c "$1"
}

case "$AZIONE" in
accendi)
	# ⛔ Solo la NOSTRA unita': rete11-server non si tocca.
	dentro "
		systemctl stop $UNITA 2>/dev/null
		systemctl reset-failed $UNITA 2>/dev/null
		mkdir -p $DIR/rilievo
		[ -d $DIR/certificati ] || cp -a /var/lib/rete11/certificati $DIR/certificati
		rm -f $REG $DIR/ban $DIR/comando.sock
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
