#!/bin/sh
# 09-b68-scena.sh — accende `04-b30-scena` dentro la sessione di «prova».
#
# ⛔ ESISTE PERCHE' UN FILE NON HA LIVELLI DI VIRGOLETTE.  Il primo giro
#    lanciava la scena da `ssh -> sudo -S -> setsid ... > $LAV/scena.log`, e il
#    redirect lo faceva la shell di **nicfio**, che in `/media/REMOTIX/tmp/09`
#    (di root) non puo' scrivere: il processo moriva e il registro era VUOTO —
#    cioe' il guasto peggiore, «non partita» senza dire perche'.
#    ⚠ E' la stessa trappola scritta in `07-b65-datagram.py` per il guardiano.
#
#   sh 09-b68-scena.sh <monitor> <marca|barra|pieno>     accende
#   sh 09-b68-scena.sh -- spegni                          spegne
#
# ⛔ Gira DA ROOT: `setpriv` fa scendere all'uid di «prova» (1001), che e'
#    l'unico che possa parlare col suo compositore.
set -u
UID_B=${UID_B:-1001}
UTENTE=${UTENTE:-prova}
SCENA=/media/REMOTIX/src/04-b30-scena-lav/04-b30-scena
# ⚠ La cartella di lavoro viene da fuori: il confronto appaiato ne ha DUE
#   (`tmp/09` per il prima, `tmp/09b` per il dopo), e mescolarle mescolerebbe
#   i registri senza dare nessun rosso.
LAV=${LAV:-/media/REMOTIX/tmp/09}
LOG=$LAV/b68-scena.log

if [ "${2:-}" = "spegni" ]; then
	pkill -u "$UID_B" -f 04-b30-scena
	exit 0
fi

USCITA=$1
MOVIMENTO=$2

pkill -u "$UID_B" -f 04-b30-scena 2>/dev/null
sleep 0.3
: > "$LOG"
chmod 666 "$LOG"

setsid nohup setpriv --reuid="$UID_B" --regid="$UID_B" --init-groups \
	env -i HOME="/home/$UTENTE" USER="$UTENTE" LANG=C.UTF-8 \
	PATH=/usr/local/bin:/usr/bin:/bin \
	XDG_RUNTIME_DIR="/run/user/$UID_B" WAYLAND_DISPLAY=wayland-0 \
	"$SCENA" --uscita "$USCITA" --movimento "$MOVIMENTO" \
	--shm /09-b68 --giro b68 >>"$LOG" 2>&1 &

sleep 2
if pgrep -u "$UID_B" -f '04-b30-scena --uscita' >/dev/null; then
	echo "SCENA ACCESA $MOVIMENTO su $USCITA"
	exit 0
fi
echo "SCENA NON PARTITA — il suo registro:"
cat "$LOG"
exit 1
