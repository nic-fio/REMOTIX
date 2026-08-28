#!/bin/bash
# ===========================================================================
# 10-f2-finestra-cieca.sh — ⭐⭐ QUANTO DURA il tratto in cui la sessione
# remota NON HA NESSUN MONITOR, e quindi nessun `wl_output`.
#
# ⛔ PERCHE' QUESTO NUMERO ESISTE, ed e' UNA SCELTA NOSTRA, non un incidente.
#
#   `src/sessione.c:744` toglie `--virtual-monitor` dalla riga della Shell —
#   apposta, e misurato il 14 agosto 2026: con un monitor suo, la cattura ne
#   monta un SECONDO e l'utente guarda uno schermo vuoto.  ⇒ ⭐ Il disegno e':
#   **la sessione non ha monitor propri, e l'unico monitor e' quello che monta
#   la nostra cattura** (`mutter.c`, `RecordVirtual`).
#
#   ⚠ Il prezzo e' scritto li' accanto: *«prima del primo client la sessione e'
#     NERA (zero monitor)»*.  ⇒ Fra l'avvio di `gnome-shell` e il montaggio del
#     palco c'e' un tratto in cui un programma GTK che parte NON TROVA NESSUN
#     MONITOR — ed e' esattamente la condizione che fa dire a GDK
#     `gdk_monitor_get_workarea: assertion 'GDK_IS_MONITOR (monitor)' failed`.
#
# ⇒ ⛔ **Quanto dura quel tratto e' un numero nostro, e questo file lo misura.**
#    Non «se c'e'»: quanto.  Un tratto di millisecondi e un tratto di secondi
#    sono due difetti diversi, e uno solo dei due morde un utente.
#
#   uso:  10-f2-finestra-cieca.sh <UTENTE> [PORTA]
#
# ⛔ L'utente NON deve avere una sessione viva: si vuole vederla NASCERE.
# ===========================================================================
set -uo pipefail

U=${1:?serve un utente}
PORTA=${2:-8420}
UID_U=$(id -u "$U") || exit 2
RUN="/run/user/$UID_U"
SOCK="$RUN/wayland-0"
LAV=/media/REMOTIX/tmp/10f2

if [ -S "$SOCK" ]; then
	echo "⛔ NON MISURO: «$U» ha gia' un socket Wayland — la sessione c'e' gia'"
	exit 2
fi

# ── il cliente fa NASCERE la sessione, e resta attaccato ────────────────────
printf '%s\n' nicfio | bash /media/REMOTIX/enter.sh \
	"cd /srv/src/10f2-src/banchi && timeout 120 python3 -u 01-b3-cliente.py \
	   --indirizzo 192.168.0.2 --porta $PORTA --utente $U \
	   --parola-file /srv/remotix/tmp/10f2/parola \
	   --larghezza 1500 --altezza 864 --resta 60" \
	>/tmp/10f2-cieca-cliente.log 2>&1 &
PID=$!

# ── si aspetta che il socket COMPAIA, e da li' si conta ─────────────────────
i=0
while [ ! -S "$SOCK" ] && [ $i -lt 600 ]; do i=$((i + 1)); sleep 0.05; done
if [ ! -S "$SOCK" ]; then
	echo "⛔ NON MISURATO: il socket Wayland non e' comparso in 30 s"
	kill $PID 2>/dev/null; exit 2
fi
T0=$(date +%s.%N)
echo "⭐ socket comparso; conto da qui"

PRIMO_OK=""
ZERI=0
LETTURE=0
i=0
while [ $i -lt 600 ]; do
	R=$(setpriv --reuid="$UID_U" --regid="$UID_U" --init-groups \
		env -i HOME="/home/$U" USER="$U" PATH=/usr/bin:/bin \
		XDG_RUNTIME_DIR="$RUN" WAYLAND_DISPLAY=wayland-0 \
		/usr/bin/python3 "$LAV/10-f2-globali.py" --json 2>/dev/null \
		| /usr/bin/python3 -c 'import sys,json
try:  print(json.load(sys.stdin)["wl_output"])
except Exception:  print("None")' 2>/dev/null)
	case "$R" in
		None|"") : ;;                       # ⛔ non ho potuto leggere: non conta
		0) ZERI=$((ZERI + 1)); LETTURE=$((LETTURE + 1)) ;;
		*) LETTURE=$((LETTURE + 1)); PRIMO_OK=$(date +%s.%N); break ;;
	esac
	i=$((i + 1)); sleep 0.05
done

if [ -z "$PRIMO_OK" ]; then
	echo "⛔ NON MISURATO: nessun wl_output in 30 s ($LETTURE letture, $ZERI a zero)"
	kill $PID 2>/dev/null; exit 1
fi
DT=$(/usr/bin/python3 -c "print(f'{($PRIMO_OK - $T0)*1000:.0f}')")
echo "⭐ il primo wl_output e comparso dopo ${DT} ms dal socket"
echo "   letture riuscite: $LETTURE, di cui a ZERO monitor: $ZERI"
echo "   ⇒ ⚠ in quel tratto un programma GTK che parte non trova nessun monitor"
kill $PID 2>/dev/null
wait $PID 2>/dev/null
