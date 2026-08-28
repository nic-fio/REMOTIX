#!/bin/bash
#
# permesso6-kde.sh — sesto giro, solo su M1.  Stato: cinque forme del `.desktop`
# negate, sempre con «Could not find the desktop file for <exe>».  Restano due
# variabili da isolare, una per prova:
#
#  (A) l'INDICE.  `kbuildsycoca6 --track <menu-id>` e' lo strumento fatto per
#      questo: dice se il file entra o dove viene scartato.  E si guarda se manca
#      /etc/xdg/menus/applications.menu (kbuildsycoca6 se ne lamenta).
#
#  (B) il PERCORSO.  Il nostro binario sta su /media/REMOTIX (un montaggio).  Se
#      un cliente in /usr/bin ottiene «Interfaces found for ... ()» invece di
#      «Could not find», la causa e' il percorso e non l'indice.  Cliente di
#      prova: /usr/bin/wayland-info, che elenca i global come nodo-kwin.
#
set -u
QUI=/media/REMOTIX/tmp/banco-compositori
NODO="$QUI/nodo-kwin"
APP="$HOME/.local/share/applications"
LOG=/tmp/kde-p6; rm -rf "$LOG"; mkdir -p "$LOG"; mkdir -p "$APP"

export LANG=C.UTF-8 LC_ALL=C.UTF-8
[ -n "${XDG_RUNTIME_DIR:-}" ] && [ -d "${XDG_RUNTIME_DIR:-}" ] || {
    export XDG_RUNTIME_DIR="/tmp/xdg-$(id -u)"; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"; }
[ -S "/run/user/$(id -u)/bus" ] && export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
unset WAYLAND_DISPLAY DISPLAY QT_QPA_PLATFORM
SOCK=wayland-kde

echo "=================== (A) l'indice ==================="
echo "-- /etc/xdg/menus:"; ls -la /etc/xdg/menus/ 2>&1 | sed 's/^/   /'
echo "-- chi fornirebbe applications.menu (se apt-file c'e'):"
command -v apt-file >/dev/null && apt-file search /etc/xdg/menus/applications.menu 2>&1 | head -3 | sed 's/^/   /' || echo "   apt-file assente"
echo "-- pacchetti KDE installati che contano:"
dpkg -l 2>/dev/null | grep -aE '^ii +(kwin-|kservice|plasma-workspace|libkf6service|desktop-file-utils)' | awk '{print "   "$2" "$3}'

cat > "$APP/remotix-banco.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=REMOTIX banco
NoDisplay=true
Terminal=false
Exec=$(readlink -f "$NODO")
X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1
EOF

echo "-- kbuildsycoca6 --track remotix-banco.desktop, output integrale:"
kbuildsycoca6 --noincremental --track remotix-banco.desktop 2>&1 | sed 's/^/   /'
echo "-- e --menutest:"
kbuildsycoca6 --menutest 2>&1 | grep -aiE 'remotix|error|not found' | head -5 | sed 's/^/   /'

echo
echo "=================== (B) il percorso ==================="
CLI=/usr/bin/wayland-info
if [ ! -x "$CLI" ]; then echo "   wayland-info assente: prova (B) saltata"; else
cat > "$APP/remotix-info.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=prova wayland-info
NoDisplay=true
Terminal=true
Exec=$CLI
X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1
EOF
kbuildsycoca6 --noincremental >/dev/null 2>&1
echo "   .desktop per $CLI installato e indice ricostruito"

rm -f "$XDG_RUNTIME_DIR/$SOCK" "$XDG_RUNTIME_DIR/$SOCK.lock"
QT_LOGGING_RULES='KWIN_UTILS.debug=true;kwin_core.debug=true' \
    /usr/bin/kwin_wayland --virtual --width 1280 --height 720 --no-lockscreen \
    --socket="$SOCK" > "$LOG/kwin.log" 2>&1 &
PID=$!
for i in $(seq 40); do [ -S "$XDG_RUNTIME_DIR/$SOCK" ] && break; sleep 0.25; done
sleep 2.5
if kill -0 "$PID" 2>/dev/null; then
    echo -n "   cliente in /usr/bin  → zkde_screencast: "
    WAYLAND_DISPLAY="$SOCK" "$CLI" > "$LOG/info.txt" 2>&1
    grep -qi zkde_screencast "$LOG/info.txt" && echo "✅ ANNUNCIATO" || echo "⛔ negato"
    echo -n "   cliente in /media    → zkde_screencast: "
    WAYLAND_DISPLAY="$SOCK" "$NODO" --elenca > "$LOG/nodo.txt" 2>&1
    grep -qi zkde_screencast "$LOG/nodo.txt" && echo "✅ ANNUNCIATO" || echo "⛔ negato"
    echo "   quel che KWin ha detto dei due (righe distinte):"
    grep -aE 'KWIN_UTILS|Interfaces found' "$LOG/kwin.log" | sort -u | sed 's/^/      /'
    echo "   e a chi ha negato zkde_screencast:"
    grep -a 'zkde_screencast_unstable_v1" not in' "$LOG/kwin.log" | sort -u | sed 's/^/      /'
    kill "$PID" 2>/dev/null; wait "$PID" 2>/dev/null
else
    echo "   ⛔ KWin non partito:"; tail -5 "$LOG/kwin.log" | sed 's/^/      /'
fi
rm -f "$APP/remotix-info.desktop"
fi

pkill -x kwin_wayland; pkill -x nodo-kwin
sleep 0.5
echo
echo "residui: kwin=$(pgrep -xc kwin_wayland || true)"
echo "fine. registri in $LOG"
