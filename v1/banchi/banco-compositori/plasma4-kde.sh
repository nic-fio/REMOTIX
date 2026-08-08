#!/bin/bash
#
# plasma4-kde.sh — `InaccessiblePaths=` (il modo di scegliere la GPU) chiude il
# cancello della cattura.  Il perché non si indovina: si accende KWIN_UTILS dentro
# l'unità e si legge il journal del compositore.
#
#   «Could not find the desktop file for ""»        → /proc/<pid>/exe non si risolve
#   «Could not find the desktop file for "<path>"»  → l'indice non associa
#   «Interfaces found … : ()»                        → associa, campo vuoto
#
set -u
QUI=/media/REMOTIX/tmp/banco-compositori
LOG=/tmp/kde-p4; rm -rf "$LOG"; mkdir -p "$LOG"
U=$(id -u)
export XDG_RUNTIME_DIR="/run/user/$U"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
export XDG_MENU_PREFIX=plasma- LANG=C.UTF-8 LC_ALL=C.UTF-8
unset WAYLAND_DISPLAY DISPLAY QT_QPA_PLATFORM
DIR="$XDG_RUNTIME_DIR/systemd/user.control/plasma-kwin_wayland.service.d"

dropin() {
    mkdir -p "$DIR"
    { echo "[Service]"; echo "ExecStart="
      echo "ExecStart=/usr/bin/kwin_wayland_wrapper --xwayland --virtual --width 1920 --height 1080 --no-lockscreen"
      echo "Environment=QT_LOGGING_RULES=KWIN_UTILS.debug=true;kwin_core.debug=true"
      [ -n "$1" ] && printf '%s\n' "$1"; } > "$DIR/remotix.conf"
    systemctl --user daemon-reload
}
avvia() {
    setsid nohup startplasma-wayland > "$LOG/plasma-$1.log" 2>&1 &
    local i; for i in $(seq 60); do pgrep -x plasmashell >/dev/null && break; sleep 1; done
    sleep 6
    SOCKET=$(ls -1 "$XDG_RUNTIME_DIR" | grep -E '^wayland-[0-9]+$' | head -1)
    KPID=$(pgrep -x kwin_wayland | head -1)
}
chiudi() {
    gdbus call --session --dest org.kde.Shutdown --object-path /Shutdown \
        --method org.kde.Shutdown.logout >/dev/null 2>&1
    local i; for i in $(seq 25); do pgrep -x plasmashell >/dev/null || break; sleep 1; done
    for p in plasmashell kwin_wayland ksmserver kded6 Xwayland kglobalacceld; do pkill -x $p 2>/dev/null; done
    sleep 2
}
prova() {   # $1 = etichetta
    echo "   kwin pid ${KPID:-nessuno}"
    echo -n "   ⇒ zkde_screencast: "
    WAYLAND_DISPLAY="$SOCKET" "$QUI/nodo-kwin" --elenca 2>&1 | grep -c zkde_screencast || true
    sleep 1
    echo "   ---- quel che KWin ha scritto sul permesso (journal dell'unità):"
    journalctl --user -u plasma-kwin_wayland.service --since "-3min" --no-pager 2>/dev/null \
        | grep -aE 'KWIN_UTILS|Interfaces found|not in X-KDE|Could not find the desktop' \
        | tail -5 | sed 's/^/      /'
    echo "   ---- e nel registro della sessione:"
    grep -aE 'KWIN_UTILS|Interfaces found|Could not find the desktop' "$LOG/plasma-$1.log" \
        | tail -4 | sed 's/^/      /'
}

echo "== password una volta =="; sudo -S -p 'Password: ' -v >/dev/null; echo "   ok"

echo
echo "############ A — senza InaccessiblePaths (il caso che FUNZIONA) ############"
dropin ""
avvia A
prova A
chiudi

echo
echo "############ B — con InaccessiblePaths (il caso che NON funziona) ############"
dropin "InaccessiblePaths=/dev/dri/renderD129"
avvia B
prova B
echo "   ---- e per confronto, che cosa vede KWin del cliente:"
if [ -n "${KPID:-}" ]; then
    WAYLAND_DISPLAY="$SOCKET" "$QUI/nodo-kwin" --elenca >/dev/null 2>&1 &
    CP=$!; sleep 0.5
    echo -n "      il pid del cliente ($CP) è visibile in /proc dal namespace di KWin? "
    sudo nsenter --mount --target "$KPID" test -e "/proc/$CP/exe" && echo "sì" || echo "NO ⛔"
    echo -n "      e /proc dentro il namespace è lo stesso? mount di /proc: "
    sudo cat "/proc/$KPID/mounts" | grep -cE '^proc /proc ' || true
    kill $CP 2>/dev/null
fi
chiudi

echo
echo "############ C — la cura da provare: DeviceAllow invece di InaccessiblePaths ############"
echo "   (DeviceAllow usa il cgroup dei device, NON un mount namespace: se il"
echo "    sospetto è il namespace, questa via deve funzionare)"
dropin "DeviceAllow=/dev/dri/renderD128 rw
DeviceAllow=/dev/dri/card0 rw
DevicePolicy=closed"
avvia C
prova C
echo -n "   renderer: "
gdbus call --session --dest org.kde.KWin --object-path /KWin \
    --method org.kde.KWin.supportInformation 2>/dev/null \
    | grep -aoE 'OpenGL renderer string: [^\\]*' | head -1
chiudi

echo
echo "############ pulizia ############"
systemctl --user stop plasma-workspace.target 2>/dev/null
rm -rf "$DIR"; systemctl --user daemon-reload
for p in plasmashell kwin_wayland ksmserver kded6 Xwayland kglobalacceld xembedsniproxy; do pkill -x $p 2>/dev/null; done
sleep 1
echo "   residui: kwin=$(pgrep -xc kwin_wayland || true) plasmashell=$(pgrep -xc plasmashell || true)"
echo "   porte 33xx: $(ss -ltn 2>/dev/null | grep -c ':33[89][0-9]' || true)"
echo "fine. registri in $LOG"
