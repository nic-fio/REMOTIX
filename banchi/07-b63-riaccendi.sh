#!/usr/bin/env bash
#
# 07-b63-riaccendi.sh — riaccende IL MIO server (7771) con UNA PAGINA A SCELTA,
# senza ricompilare niente.
#
#   bash banchi/07-b63-riaccendi.sh                      la pagina del prodotto
#   bash banchi/07-b63-riaccendi.sh /tmp/pagina-diag.html   una copia strumentata
#
# ⛔ PERCHE' ESISTE, invece di rigirare `07-b41-accendi.sh`: la diagnosi del
#    percorso worker vuole una pagina STRUMENTATA, e strumentare il prodotto per
#    guardarci dentro e' esattamente il modo di misurare una cosa e chiamarne
#    un'altra.  ⇒ La copia diagnostica sta FUORI dall'albero del prodotto, e il
#    server la serve con `--pagina`: nessun byte del prodotto cambia, e il
#    binario e' lo stesso identico di prima (nessun `make`).
#
# ⛔ E LA PAGINA IN VIGORE SI RILEGGE, non si spera: il server la stampa nel suo
#    registro all'avvio, e questo copione la ristampa.  «L'ho passata» non e'
#    «la sta servendo» (forma E1).
#
# ⛔ 7700, 7730 e l'utente `prova` NON SI TOCCANO.
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
PORTA=${PORTA:-7771}
ALBERO=${ALBERO:-/media/REMOTIX/src/07-v-src}
LAV=${LAV:-/media/REMOTIX/tmp/07-v}
PAGINA=${1:-$ALBERO/src/pagina.html}
UNITA=remotix-$PORTA

COPIONE=$(mktemp)
trap 'rm -f "$COPIONE"' EXIT
cat > "$COPIONE" <<FINE
set -e
B2=/media/REMOTIX/src/b2
SRC=$ALBERO/src
export LD_LIBRARY_PATH="\$B2/ngtcp2/build/lib:\$B2/prefisso/lib\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}"

[ -s "$PAGINA" ] || { echo "⛔ la pagina «$PAGINA» non c'e' o e' vuota"; exit 2; }

systemctl stop $UNITA.service 2>/dev/null || true
systemctl reset-failed $UNITA.service 2>/dev/null || true
i=0
while ss -uln 2>/dev/null | grep -q ':$PORTA ' && [ \$i -lt 50 ]; do i=\$((i+1)); sleep 0.2; done

mkdir -p $LAV
: > $LAV/registro.log

systemd-run \
	--unit=$UNITA --collect --description="REMOTIX_V2, banco 07-b63 (video)" \
	--working-directory="\$SRC" \
	--setenv=LD_LIBRARY_PATH="\$LD_LIBRARY_PATH" \
	--property=StandardOutput=append:$LAV/registro.log \
	--property=StandardError=append:$LAV/registro.log \
	--property=KillMode=mixed \
	--property=LimitRTPRIO=20 \
	--property=LimitNICE=-11 \
	"\$SRC/remotix" \
	--indirizzo 0.0.0.0 --nome 192.168.0.2 --porta $PORTA \
	--certificati $LAV/certificati \
	--pagina "$PAGINA" \
	--ban-file $LAV/ban \
	--comando-socket $LAV/comando.sock \
	--rilievo $LAV/rilievo \
	--audio-prova 0 \
	--parlantina >/dev/null

i=0; PID=0
while [ \$i -lt 50 ]; do
	PID=\$(systemctl show -p MainPID --value $UNITA.service 2>/dev/null || echo 0)
	[ "\$PID" != "0" ] && [ -n "\$PID" ] && break
	i=\$((i+1)); sleep 0.1
done
[ "\$PID" != "0" ] || { echo "⛔ non e' partito:"; tail -20 $LAV/registro.log; exit 1; }
echo "⭐ server \$PID sulla 7771 — pagina $PAGINA (\$(stat -c %s "$PAGINA") byte, \$(date -r "$PAGINA" +%H:%M:%S))"
sleep 1
grep -E "in ascolto|pronto|pagina" $LAV/registro.log | head -4 || true
FINE

scp -q -o BatchMode=yes "$COPIONE" "$MACCHINA:/tmp/07-b63-riaccendi-remoto.sh"
ssh -o BatchMode=yes "$MACCHINA" \
	"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /tmp/07-b63-riaccendi-remoto.sh; rc=\$?; rm -f /tmp/07-b63-riaccendi-remoto.sh; exit \$rc"
