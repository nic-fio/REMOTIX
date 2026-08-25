#!/bin/bash
# ===========================================================================
# 10-f2-dove-si-ferma.sh — ⛔ DOVE si ferma Firefox, e se si ferma anche
# FUORI da REMOTIX.
#
# ⛔ PERCHE'.  La fase 9 aveva dichiarato «Firefox non parte sulla macchina di
#    prova — anche fuori da REMOTIX», ⚠ ma quella misura era su una macchina
#    SENZA sessione grafica, dove nessun browser potrebbe partire: quella
#    conclusione non copre il caso di adesso.  ⇒ Qui si rifa', e si rifa' in
#    modo che il verdetto valga: **headless, senza compositore, senza REMOTIX,
#    con un profilo tutto suo in una cartella vuota**.  Se si ferma anche li',
#    il difetto non e' del desktop remoto.
#
#   uso:  10-f2-dove-si-ferma.sh <UTENTE> <SECONDI>
#
# ⭐ E non si guarda solo «e' morto o no»: si guarda **dove** e' fermo — i
#    thread, il loro `wchan`, e i descrittori aperti.  ⛔ «Non parte» e «e'
#    appeso su qualcosa» hanno la stessa faccia e sono due difetti diversi.
# ===========================================================================
set -uo pipefail

U=${1:?serve un utente}
SEC=${2:-40}
UID_U=$(id -u "$U") || exit 2
PROF=$(mktemp -d /tmp/10f2-prof-XXXXXX)
chown "$UID_U:$UID_U" "$PROF"
rmdir "$PROF"                     # ⚠ Firefox la vuole creare lui
USCITA=/tmp/10f2-fuori.log

setpriv --reuid="$UID_U" --regid="$UID_U" --init-groups \
	env -i HOME="/home/$U" USER="$U" LANG=C.UTF-8 PATH=/usr/bin:/bin \
	TMPDIR=/tmp MOZ_HEADLESS=1 \
	/usr/bin/firefox-esr --headless --profile "$PROF" \
	--screenshot /tmp/10f2-fuori.png about:blank \
	>"$USCITA" 2>&1 &
PID=$!

sleep "$SEC"

if kill -0 "$PID" 2>/dev/null; then
	echo "⛔ DOPO $SEC s E' ANCORA VIVO (pid $PID) — non e' «non parte», e' APPESO"
	echo "   albero dei processi:"
	ps --forest -o pid,stat,wchan:24,etime,cmd -g "$(ps -o sid= -p $PID | tr -d ' ')" \
		2>/dev/null | sed 's/^/     /' | head -20
	echo "   i thread del processo principale, e dove stanno:"
	for t in /proc/$PID/task/*; do
		n=$(cat "$t/comm" 2>/dev/null)
		w=$(cat "$t/wchan" 2>/dev/null)
		s=$(awk '{print $3}' "$t/stat" 2>/dev/null)
		printf '     %-20s %s  %s\n' "$n" "$s" "$w"
	done | head -40
	echo "   la cartella del profilo esiste? $( [ -d "$PROF" ] && echo si || echo NO )"
	kill -9 "$PID" 2>/dev/null
	wait "$PID" 2>/dev/null
	ESITO=appeso
else
	wait "$PID"; C=$?
	echo "⭐ e' uscito da solo, codice $C"
	echo "   scatto prodotto? $( [ -s /tmp/10f2-fuori.png ] && echo si || echo NO )"
	echo "   cartella profilo? $( [ -d "$PROF" ] && echo si || echo NO )"
	ESITO=uscito
fi
echo "   --- quel che ha detto ---"
sed 's/^/     /' "$USCITA" | head -30
echo "   esito=$ESITO"
