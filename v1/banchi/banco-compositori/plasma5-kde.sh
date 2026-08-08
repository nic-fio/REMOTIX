#!/bin/bash
#
# plasma5-kde.sh — la ricetta completa: la Intel **e** il cancello aperto.
#
# Stato: `InaccessiblePaths=` dà la Intel ma chiude il cancello; `DeviceAllow=` non
# tocca la GPU (in un'unità d'utente il controllo dei device non è delegato).
# Sospetto: il namespace di systemd porta con sé un `/proc` ridotto, e KWin ha
# bisogno di `/proc/<pid>/exe` del CLIENTE per decidere il permesso (§3.3 n.1).
#
# Tre prove, una riga di differenza per volta, e lo stderr del compositore su file
# (nel journal d'utente non arrivava).
#
set -u
QUI=/media/REMOTIX/tmp/banco-compositori
LOG=/tmp/kde-p5; rm -rf "$LOG"; mkdir -p "$LOG"; chmod 777 "$LOG"
U=$(id -u)
export XDG_RUNTIME_DIR="/run/user/$U"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
export XDG_MENU_PREFIX=plasma- LANG=C.UTF-8 LC_ALL=C.UTF-8
unset WAYLAND_DISPLAY DISPLAY QT_QPA_PLATFORM
DIR="$XDG_RUNTIME_DIR/systemd/user.control/plasma-kwin_wayland.service.d"

dropin() {   # $1 = etichetta (per il log), $2 = righe extra
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

prova() {   # $1 = etichetta
    local n
    n=$(WAYLAND_DISPLAY="$SOCKET" "$QUI/nodo-kwin" --elenca 2>&1 | grep -c zkde_screencast || true)
    printf '   ⇒ cancello: %s     ' "$([ "$n" = 0 ] && echo '⛔ CHIUSO' || echo '✅ APERTO')"
    gdbus call --session --dest org.kde.KWin --object-path /KWin \
        --method org.kde.KWin.supportInformation 2>/dev/null \
        | grep -aoE 'renderer string: [^\\]*' | head -1
    echo "   KWIN_UTILS dice:"
    grep -aE 'KWIN_UTILS|Interfaces found|Could not find the desktop' "$LOG/kwin-$1.log" 2>/dev/null \
        | sort -u | tail -3 | sed 's/^/      /'
    # la prova del /proc, fatta su un processo che NON esce subito
    if [ -n "${KPID:-}" ]; then
        sleep 60 & local vittima=$!
        echo -n "      /proc/<altro pid>/exe visibile dal namespace di KWin: "
        sudo nsenter --mount --target "$KPID" test -e "/proc/$vittima/exe" && echo "sì" || echo "NO ⛔"
        echo -n "      come è montato /proc là dentro: "
        sudo nsenter --mount --target "$KPID" grep -m1 ' /proc ' /proc/mounts | cut -c1-100; echo
        kill $vittima 2>/dev/null
    fi
}

echo "== password una volta =="; sudo -S -p 'Password: ' -v >/dev/null; echo "   ok"

echo
echo "############ A — riferimento: nessuna restrizione ############"
dropin A ""
avvia A; prova A; chiudi

echo
echo "############ B — InaccessiblePaths (Intel, cancello chiuso) ############"
dropin B "InaccessiblePaths=/dev/dri/renderD129"
avvia B; prova B; chiudi

echo
echo "############ C — InaccessiblePaths + /proc intero: la cura da verificare ############"
dropin C "InaccessiblePaths=/dev/dri/renderD129
ProcSubset=all
ProtectProc=default"
avvia C; prova C; chiudi

echo
echo "############ pulizia ############"
systemctl --user stop plasma-workspace.target 2>/dev/null
rm -rf "$DIR"; systemctl --user daemon-reload
for p in plasmashell kwin_wayland ksmserver kded6 Xwayland kglobalacceld xembedsniproxy; do pkill -x $p 2>/dev/null; done
sleep 1
echo "   residui: kwin=$(pgrep -xc kwin_wayland || true) plasmashell=$(pgrep -xc plasmashell || true)"
echo "   porte 33xx: $(ss -ltn 2>/dev/null | grep -c ':33[89][0-9]' || true)"
echo "fine. registri in $LOG"
