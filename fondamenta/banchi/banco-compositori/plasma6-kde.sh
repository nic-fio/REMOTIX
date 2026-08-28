#!/bin/bash
#
# plasma6-kde.sh — la Intel SENZA namespace: si toglie il gruppo al nodo della
# Radeon, così `findRenderDevice()` non riesce ad aprirla e passa alla Intel.
# Nessun mount namespace ⇒ il permesso della cattura non viene disturbato.
# Per il prodotto l'equivalente stabile è una regola udev sul nodo per PCI id.
#
# ⚠ Modifica temporanea di /dev/dri/renderD129 (gruppo), ripristinata da una trap
#   in ogni caso: uscita normale, errore, interruzione. E /dev è ricreato al riavvio.
#
# Raccoglie anche il registro KWIN_UTILS completo, che nel giro precedente mancava.
#
set -u
QUI=/media/REMOTIX/tmp/banco-compositori
LOG="$XDG_RUNTIME_DIR/kde-p6"; rm -rf "$LOG"; mkdir -p "$LOG"
U=$(id -u)
export XDG_RUNTIME_DIR="/run/user/$U"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
export XDG_MENU_PREFIX=plasma- LANG=C.UTF-8 LC_ALL=C.UTF-8
unset WAYLAND_DISPLAY DISPLAY QT_QPA_PLATFORM
DIR="$XDG_RUNTIME_DIR/systemd/user.control/plasma-kwin_wayland.service.d"
LOG="$XDG_RUNTIME_DIR/kde-p6"; rm -rf "$LOG"; mkdir -p "$LOG"

echo "== password una volta =="; sudo -S -p 'Password: ' -v >/dev/null; echo "   ok"

GRUPPO=$(stat -c %G /dev/dri/renderD129)
echo "== gruppo originale di renderD129: $GRUPPO"
ripristina() {
    sudo chgrp "$GRUPPO" /dev/dri/renderD129 2>/dev/null
    echo "   [ripristino] renderD129 → gruppo $(stat -c %G /dev/dri/renderD129)"
    systemctl --user stop plasma-workspace.target 2>/dev/null
    rm -rf "$DIR"; systemctl --user daemon-reload 2>/dev/null
    for p in plasmashell kwin_wayland ksmserver kded6 Xwayland kglobalacceld xembedsniproxy; do pkill -x $p 2>/dev/null; done
}
trap ripristina EXIT INT TERM

dropin() {
    mkdir -p "$DIR"
    { echo "[Service]"; echo "ExecStart="
      echo "ExecStart=/bin/sh -c 'exec /usr/bin/kwin_wayland_wrapper --xwayland --virtual --width 1920 --height 1080 --no-lockscreen 2>>$LOG/kwin-$1.log'"
      echo "Environment=\"QT_LOGGING_RULES=KWIN_UTILS.debug=true\""
      [ -n "$2" ] && printf '%s\n' "$2"; } > "$DIR/remotix.conf"
    systemctl --user daemon-reload
}
avvia() { setsid nohup startplasma-wayland > "$LOG/plasma-$1.log" 2>&1 &
    local i; for i in $(seq 60); do pgrep -x plasmashell >/dev/null && break; sleep 1; done
    sleep 6
    SOCKET=$(ls -1 "$XDG_RUNTIME_DIR" | grep -E '^wayland-[0-9]+$' | head -1)
    KPID=$(pgrep -x kwin_wayland | head -1); }
chiudi() { gdbus call --session --dest org.kde.Shutdown --object-path /Shutdown \
        --method org.kde.Shutdown.logout >/dev/null 2>&1
    local i; for i in $(seq 25); do pgrep -x plasmashell >/dev/null || break; sleep 1; done
    for p in plasmashell kwin_wayland ksmserver kded6 Xwayland kglobalacceld; do pkill -x $p 2>/dev/null; done
    sleep 2; }
prova() {
    local n
    n=$(WAYLAND_DISPLAY="$SOCKET" "$QUI/nodo-kwin" --elenca 2>&1 | grep -c zkde_screencast || true)
    printf '   ⇒ cancello: %-12s  ' "$([ "$n" = 0 ] && echo '⛔ CHIUSO' || echo '✅ APERTO')"
    gdbus call --session --dest org.kde.KWin --object-path /KWin \
        --method org.kde.KWin.supportInformation 2>/dev/null \
        | grep -aoE 'renderer string: [^\\]*' | head -1
    echo "   il nostro binario, secondo KWIN_UTILS:"
    grep -aE 'KWIN_UTILS' "$LOG/kwin-$1.log" 2>/dev/null | grep -a 'banco-compositori' | sort -u | sed 's/^/      /'
    echo "   righe di KWIN_UTILS in tutto: $(grep -ac KWIN_UTILS "$LOG/kwin-$1.log" 2>/dev/null || echo 0)"
    if [ "$n" != 0 ]; then
        WAYLAND_DISPLAY="$SOCKET" "$QUI/nodo-kwin" > "$LOG/nodo-$1.log" 2>&1 &
        local np=$!; sleep 3
        echo -n "   e un flusso vero: "; grep -aoE 'nodo PipeWire [0-9]+' "$LOG/nodo-$1.log" | head -1 || echo "no"
        kill $np 2>/dev/null
    fi
}

echo
echo "############ A — Radeon negata dai PERMESSI (nessun namespace) ############"
sudo chgrp root /dev/dri/renderD129
echo "   renderD129 ora: $(stat -c '%A %U:%G' /dev/dri/renderD129)  (l'utente non è più nel gruppo)"
echo -n "   il nostro utente riesce ad aprirla? "
python3 -c "
import os
try: os.close(os.open('/dev/dri/renderD129', os.O_RDWR)); print('sì (la prova non vale)')
except OSError as e: print('no:', e.strerror, '← come deve essere')"
dropin A ""
avvia A; prova A; chiudi

echo
echo "############ B — di nuovo InaccessiblePaths, per avere il suo registro ############"
sudo chgrp "$GRUPPO" /dev/dri/renderD129
dropin B "InaccessiblePaths=/dev/dri/renderD129"
avvia B; prova B
echo "   diagnosi del caso B: dove è finito il registro?"
ls -l "$LOG"/kwin-B.log 2>&1 | sed 's/^/      /'
echo -n "      /tmp dentro il namespace di KWin è privato? "
[ -n "${KPID:-}" ] && sudo nsenter --mount --target "$KPID" grep -cE ' /tmp ' /proc/mounts || echo "?"
echo "      il .desktop, visto DA DENTRO il namespace:"
[ -n "${KPID:-}" ] && sudo nsenter --mount --target "$KPID" ls -l "$HOME/.local/share/applications/remotix-banco.desktop" 2>&1 | sed 's/^/         /'
echo "      la cache dell'indice, vista da dentro:"
[ -n "${KPID:-}" ] && sudo nsenter --mount --target "$KPID" ls -l "$HOME/.cache/" 2>&1 | grep -a ksycoca | sed 's/^/         /'
chiudi

echo
echo "############ fine ############"
echo "   porte 33xx: $(ss -ltn 2>/dev/null | grep -c ':33[89][0-9]' || true)"
echo "   registri in $LOG"
