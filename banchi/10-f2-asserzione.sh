#!/bin/bash
# ===========================================================================
# 10-f2-asserzione.sh — ⛔ DI CHI E' `gdk_monitor_get_workarea: assertion
# 'GDK_IS_MONITOR (monitor)' failed`, e quante volte esce davvero.
#
# ⛔ IL PUNTO DI PARTENZA DA VERIFICARE, non da ripetere: si diceva che Firefox
#    «sputa a valanga» quella riga, e che quindi «GTK non trova un MONITOR»
#    nella sessione headless.  ⚠ Due affermazioni, e vanno pesate a parte:
#      · **quante** righe — «a valanga» e' un numero, e si conta;
#      · **se il monitor c'e'** — e quello lo dice `10-f2-globali.py`, dal
#        posto in cui sta Firefox.
#
#   uso:  10-f2-asserzione.sh <UTENTE> <SECONDI>
#
# ⛔ Va lanciato con un CLIENTE ATTACCATO alla sessione, o Mutter non consegna
#    niente e si misura un'altra cosa.  Chi lo chiama se ne occupa
#    (`10-f2-scena.sh`).
# ===========================================================================
set -uo pipefail

U=${1:?serve un utente}
SEC=${2:-45}
UID_U=$(id -u "$U") || exit 2
LOG=/tmp/10f2-asserzione-$U.log
rm -f "$LOG"

# ⭐ Prima: che cosa vede un client Wayland qualunque, cioe' quel che vedrebbe
#    GDK.  Se qui c'e' un `wl_output`, «GTK non trova un monitor» non puo'
#    essere la spiegazione, e va cercata altrove.
echo "-- che cosa vede un client Wayland PRIMA di lanciare --"
bash /media/REMOTIX/tmp/10f2/10-f2-dentro.sh "$U" composto \
	/usr/bin/python3 /media/REMOTIX/tmp/10f2/10-f2-globali.py --taratura \
	2>&1 | tail -3 | sed 's/^/   /'

setpriv --reuid="$UID_U" --regid="$UID_U" --init-groups \
	env -i HOME="/home/$U" USER="$U" LANG=C.UTF-8 \
	PATH=/usr/local/bin:/usr/bin:/bin \
	XDG_RUNTIME_DIR="/run/user/$UID_U" WAYLAND_DISPLAY=wayland-0 \
	GDK_BACKEND=wayland \
	DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$UID_U/bus" \
	/usr/bin/firefox-esr >"$LOG" 2>&1 &
PID=$!
sleep "$SEC"
VIVO=no; kill -0 "$PID" 2>/dev/null && VIVO=si

# ⚠ `grep -c … || echo 0` scrive DUE righe quando non trova niente (lo zero di
#   grep piu' lo zero dell-`echo`), e `[ "$N" -gt 0 ]` poi si rompe.  ⇒ Il
#   conteggio si prende da `wc -l` su quel che grep ha trovato, che di righe ne
#   scrive sempre una sola.
N=$(grep -c "gdk_monitor_get_workarea" "$LOG" 2>/dev/null); N=${N:-0}
echo "-- dopo $SEC s --"
echo "   Firefox vivo: $VIVO"
echo "   righe di registro in tutto: $(wc -l <"$LOG")"
echo "   ⭐ righe «gdk_monitor_get_workarea»: $N"
if [ "$N" -gt 0 ]; then
	echo "   la prima e l'ultima, con l'ora:"
	grep "gdk_monitor_get_workarea" "$LOG" | sed -n '1p;$p' | cut -c1-140 | sed 's/^/     /'
fi
echo "   -- tutto quel che ha detto --"
cut -c1-160 "$LOG" | head -20 | sed 's/^/     /'
