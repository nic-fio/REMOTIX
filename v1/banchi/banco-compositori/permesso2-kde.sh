#!/bin/bash
#
# permesso2-kde.sh — terzo giro: si CHIEDE A KWIN perche' nega, invece di dedurlo.
#
# Il secondo giro ha certificato il banco (con NO_PERMISSION_CHECKS il protocollo
# c'e') e ha stabilito che il `.desktop` in ~/.local/share NON autorizza.  Il
# codice dice che KWin, quando nega, scrive a `qCDebug` la riga
#   «Interface … not in X-KDE-Wayland-Interfaces of <percorso>»
# (`kwin/src/wayland_server.cpp:184`), e quel <percorso> e' la risposta: dice
# quale eseguibile KWin crede di avere davanti.
#
set -u
QUI=/media/REMOTIX/tmp/banco-compositori
NODO="$QUI/nodo-kwin"
EXE=$(readlink -f "$NODO")
LOG=/tmp/kde-permesso2; mkdir -p "$LOG"

export LANG=C.UTF-8 LC_ALL=C.UTF-8
[ -n "${XDG_RUNTIME_DIR:-}" ] || { export XDG_RUNTIME_DIR="/tmp/xdg-$(id -u)"; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"; }
[ -S "/run/user/$(id -u)/bus" ] && export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
unset WAYLAND_DISPLAY DISPLAY QT_QPA_PLATFORM

echo "== quel che il client E' davvero, dal punto di vista di KWin:"
echo "   argv[0] risolto : $EXE"
"$NODO" --elenca >/dev/null 2>&1 &
P=$!; sleep 0.3
echo "   /proc/pid/exe   : $(readlink -f /proc/$P/exe 2>/dev/null || echo '(gia uscito)')"
kill $P 2>/dev/null
echo "== XDG_DATA_* di questa sessione (KWin eredita questi):"
echo "   XDG_DATA_HOME=${XDG_DATA_HOME:-(non impostata → ~/.local/share)}"
echo "   XDG_DATA_DIRS=${XDG_DATA_DIRS:-(non impostata → /usr/local/share:/usr/share)}"
echo

# il file di sistema, scritto senza confondere lo stdin di sudo (l'heredoc del
# giro 2 finiva DENTRO sudo -S ed e' stato letto come password)
cat > /tmp/remotix-banco.desktop <<EOF
[Desktop Entry]
Type=Application
Name=REMOTIX banco
NoDisplay=true
Terminal=false
Exec=$EXE
X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1
EOF
sudo -S -p 'Password: ' install -m 644 /tmp/remotix-banco.desktop \
     /usr/share/applications/remotix-banco.desktop < /dev/tty 2>/dev/null \
  || sudo -S -p 'Password: ' install -m 644 /tmp/remotix-banco.desktop \
     /usr/share/applications/remotix-banco.desktop
ls -l /usr/share/applications/remotix-banco.desktop 2>&1 | tail -1
kbuildsycoca6 --noincremental >/dev/null 2>&1
echo "sycoca ricostruita"
echo

echo "== KWin con il registro dei permessi ACCESO, e il .desktop di sistema:"
rm -f "$XDG_RUNTIME_DIR/wayland-kde" "$XDG_RUNTIME_DIR/wayland-kde.lock"
QT_LOGGING_RULES='kwin_core.debug=true' \
kwin_wayland --virtual --width 1280 --height 720 --no-lockscreen \
    --socket=wayland-kde > "$LOG/kwin.log" 2>&1 &
K=$!
for _ in $(seq 40); do [ -S "$XDG_RUNTIME_DIR/wayland-kde" ] && break; sleep 0.25; done
sleep 3
if ! kill -0 $K 2>/dev/null; then echo "KWin non parte:"; tail -5 "$LOG/kwin.log"; exit 1; fi

echo -n "   verdetto: "
if WAYLAND_DISPLAY=wayland-kde "$NODO" --elenca 2>&1 | grep -qi zkde_screencast; then
    echo "✅ ANNUNCIATO con il .desktop di sistema"
else
    echo "⛔ negato — e qui sotto KWin dice perche'"
fi
echo "   righe di KWin sul permesso:"
grep -aiE 'x-kde-wayland-interfaces|not in|no desktop file|executable|denied|screencast' \
     "$LOG/kwin.log" | tail -6 | sed 's/^/      /'

echo
echo "== M3a/M3b sul pid vero ($K), output grezzo:"
ls -l "/proc/$K/fd" 2>&1 | grep -c . | sed 's/^/   descrittori totali: /'
ls -l "/proc/$K/fd" 2>&1 | grep -iE 'dri|dev' | head -6 | sed 's/^/   /'
grep -icE 'libEGL|libgbm|_dri\.so|llvmpipe' "/proc/$K/maps" 2>&1 | sed 's/^/   librerie grafiche trovate: /'
grep -oE '/usr/lib/[^ ]*(libEGL|libgbm|_dri|llvmpipe)[^ ]*' "/proc/$K/maps" 2>/dev/null | sort -u | head -5 | sed 's/^/   /'

echo
echo "== M3d: il tipo di buffer (opzioni giuste di misura-cattura):"
WAYLAND_DISPLAY=wayland-kde "$NODO" --virtuale 1280x720 > "$LOG/nodo.log" 2>&1 &
N=$!; sleep 3
NODE=$(grep -aoE '\b[0-9]{2,}\b' "$LOG/nodo.log" | head -1)
echo "   nodo: ${NODE:-nessuno}"
if [ -n "${NODE:-}" ]; then
    timeout 15 "$QUI/misura-cattura" --nodo "$NODE" --larghezza 1280 --altezza 720 --fps 60 2>&1 \
        | grep -aiE 'tipo|fotogramm|fps|danno|disegno|buffer' | head -8 | sed 's/^/   /'
fi
kill $N 2>/dev/null; kill $K 2>/dev/null; wait 2>/dev/null
echo "fine. registri in $LOG"
