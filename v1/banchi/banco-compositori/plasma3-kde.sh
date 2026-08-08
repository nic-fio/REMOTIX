#!/bin/bash
#
# plasma3-kde.sh — dentro la sessione Plasma il cancello resta chiuso, e l'indice è
# quello buono (KWin apre `ksycoca6_en_…` da 379 KB).  Resta un sospetto preciso:
#
#   `InaccessiblePaths=/dev/dri/renderD129` fa girare il compositore in un MOUNT
#   NAMESPACE di systemd.  KWin risolve il percorso del cliente con
#   `QFileInfo::canonicalFilePath()` (`serviceutils.h:32`) — cioè **dentro il proprio
#   namespace**.  Se `/media/REMOTIX` non è visibile lì, il percorso non si risolve e
#   il confronto con `Exec=` fallisce senza spiegazioni.
#
# Tre giri, una variabile per volta.  E questa volta si legge l'ambiente COME SI DEVE:
# `sudo cat`, non `sudo … < file` (la redirezione la fa la shell, che non è root).
#
set -u
QUI=/media/REMOTIX/tmp/banco-compositori
LOG=/tmp/kde-p3; rm -rf "$LOG"; mkdir -p "$LOG"
U=$(id -u)
export XDG_RUNTIME_DIR="/run/user/$U"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
export XDG_MENU_PREFIX=plasma- LANG=C.UTF-8 LC_ALL=C.UTF-8
unset WAYLAND_DISPLAY DISPLAY QT_QPA_PLATFORM
DIR="$XDG_RUNTIME_DIR/systemd/user.control/plasma-kwin_wayland.service.d"

echo "== una richiesta di password sola =="
sudo -S -p 'Password: ' -v; echo "   validato: $?"

dropin() {   # $1 = righe extra (può essere vuoto)
    mkdir -p "$DIR"
    { echo "[Service]"; echo "ExecStart="
      echo "ExecStart=/usr/bin/kwin_wayland_wrapper --xwayland --virtual --width 1920 --height 1080 --no-lockscreen"
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
esame() {   # $1 = etichetta
    echo "   kwin pid ${KPID:-nessuno}, socket ${SOCKET:-nessuno}"
    echo -n "   ⇒ zkde_screencast annunciato: "
    WAYLAND_DISPLAY="$SOCKET" "$QUI/nodo-kwin" --elenca 2>&1 | grep -c zkde_screencast || true
    echo -n "   renderer: "
    gdbus call --session --dest org.kde.KWin --object-path /KWin \
        --method org.kde.KWin.supportInformation 2>/dev/null \
        | grep -aoE 'OpenGL renderer string: [^\\]*' | head -1
    if [ -n "${KPID:-}" ]; then
        echo "   ambiente di KWin (sudo cat, non redirezione!):"
        sudo cat "/proc/$KPID/environ" | tr '\0' '\n' \
            | grep -aE '^(XDG_MENU_PREFIX|LANG|XDG_DATA_DIRS)=' | sed 's/^/      /'
        echo -n "   /media/REMOTIX è visibile nel namespace di KWin? "
        sudo cat "/proc/$KPID/mounts" | grep -c '/media/REMOTIX' || true
        echo -n "   il binario del cliente esiste, secondo il namespace di KWin? "
        sudo nsenter --mount --target "$KPID" test -x "$QUI/nodo-kwin" && echo "sì" || echo "NO ⛔"
        echo -n "   il .desktop è visibile nel namespace? "
        sudo nsenter --mount --target "$KPID" test -r "$HOME/.local/share/applications/remotix-banco.desktop" && echo "sì" || echo "NO ⛔"
    fi
}

echo
echo "############ A — SENZA InaccessiblePaths (userà la Radeon: è il controllo) ############"
dropin ""
avvia A
esame A
chiudi

echo
echo "############ B — CON InaccessiblePaths (la Intel, come l'ultimo giro) ############"
dropin "InaccessiblePaths=/dev/dri/renderD129"
avvia B
esame B
chiudi

echo
echo "############ C — Intel + il percorso del cliente rimontato dentro ############"
dropin "InaccessiblePaths=/dev/dri/renderD129
BindReadOnlyPaths=/media/REMOTIX"
avvia C
esame C
chiudi

echo
echo "############ e una domanda venuta dal giro precedente ############"
echo "   ksmserver e Xwayland non erano partiti. Le unità della sessione:"
systemctl --user list-units --all --no-legend 2>/dev/null | grep -aiE 'ksmserver|kwin|plasma-workspace' | awk '{print "      "$1" "$3" "$4}'

echo
echo "############ pulizia ############"
systemctl --user stop plasma-workspace.target 2>/dev/null
rm -rf "$DIR"; systemctl --user daemon-reload
for p in plasmashell kwin_wayland ksmserver kded6 Xwayland kglobalacceld xembedsniproxy; do pkill -x $p 2>/dev/null; done
sleep 1
echo "   residui: kwin=$(pgrep -xc kwin_wayland || true) plasmashell=$(pgrep -xc plasmashell || true)"
echo "   porte 33xx: $(ss -ltn 2>/dev/null | grep -c ':33[89][0-9]' || true)"
echo "fine. registri in $LOG"
