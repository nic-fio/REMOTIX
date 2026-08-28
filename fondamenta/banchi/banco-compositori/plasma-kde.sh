#!/bin/bash
#
# plasma-kde.sh — la sessione Plasma vera, per M9 (il bus sopravvive al logout?) e
# per la prova finale del cancello: il permesso della cattura **dentro una sessione
# Plasma**, non su un KWin nudo.  È anche la prima prova della ricetta di `kde.md`
# §6.1, con due aggiunte imparate dopo:
#   · XDG_MENU_PREFIX=plasma-      (§3.3-bis: senza, il permesso non funziona)
#   · InaccessiblePaths= per la GPU (deciso dall'utente l'8 ago: si usa la Intel)
#     — ed è il modo di prodotto per fare quel che sul banco facevamo con unshare.
#
# ⚠ Non tocca porte, non tocca /etc, non installa niente. Fa pulizia alla fine e la
#   verifica; elenca i file di configurazione che Plasma crea, senza cancellarli.
#
set -u
QUI=/media/REMOTIX/tmp/banco-compositori
LOG=/tmp/kde-plasma; rm -rf "$LOG"; mkdir -p "$LOG"
U=$(id -u)
export XDG_RUNTIME_DIR="/run/user/$U"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
export XDG_MENU_PREFIX=plasma-
export LANG=C.UTF-8 LC_ALL=C.UTF-8
unset WAYLAND_DISPLAY DISPLAY QT_QPA_PLATFORM

echo "== stato di partenza =="
echo "   XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR (esiste: $([ -d "$XDG_RUNTIME_DIR" ] && echo sì || echo NO))"
echo "   systemd --user: $(systemctl --user is-system-running 2>&1)"
echo "   plasma già in piedi? $(pgrep -xc plasmashell || true) plasmashell, $(pgrep -xc kwin_wayland || true) kwin"
ls -1 ~/.config/ 2>/dev/null | sort > "$LOG/config-prima.txt"
echo "   file in ~/.config prima: $(wc -l < "$LOG/config-prima.txt")"

echo
echo "== il drop-in dell'unità del compositore (la leva di §6.1) =="
DIR="$XDG_RUNTIME_DIR/systemd/user.control/plasma-kwin_wayland.service.d"
mkdir -p "$DIR"
cat > "$DIR/remotix.conf" <<'EOF'
[Service]
ExecStart=
ExecStart=/usr/bin/kwin_wayland_wrapper --xwayland --virtual --width 1920 --height 1080 --no-lockscreen
# la Radeon resa inaccessibile al solo compositore: così findRenderDevice() prende
# la Intel integrata.  È l'equivalente di prodotto del namespace del banco.
InaccessiblePaths=/dev/dri/renderD129
EOF
cat "$DIR/remotix.conf" | sed 's/^/   /'
systemctl --user daemon-reload
echo "   daemon-reload fatto"

echo
echo "== il .desktop che ci autorizza (nella sessione vera) =="
APP="$HOME/.local/share/applications"; mkdir -p "$APP"
cat > "$APP/remotix-banco.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=REMOTIX banco
NoDisplay=true
Terminal=false
Exec=$(readlink -f "$QUI/nodo-kwin")
X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1
EOF
kbuildsycoca6 --noincremental 2>&1 | sed 's/^/   /'

echo
echo "== avvio: startplasma-wayland =="
T0=$(date +%s)
setsid nohup startplasma-wayland > "$LOG/plasma.log" 2>&1 &
SP=$!
for i in $(seq 60); do
    pgrep -x plasmashell >/dev/null && break
    sleep 1
done
T1=$(date +%s)
echo "   plasmashell comparso dopo $((T1-T0)) s (0 = mai)"
sleep 8

echo "   processi della sessione:"
for p in kwin_wayland plasmashell ksmserver kded6 Xwayland; do
    printf '      %-14s %s\n' "$p" "$(pgrep -xc "$p" 2>/dev/null || echo 0)"
done
SOCKET=$(ls -1 "$XDG_RUNTIME_DIR" | grep -E '^wayland-[0-9]+$' | head -1)
echo "   socket Wayland della sessione: ${SOCKET:-nessuno}"
echo -n "   il compositore usa: "
gdbus call --session --dest org.kde.KWin --object-path /KWin \
    --method org.kde.KWin.supportInformation 2>/dev/null \
    | grep -aoE 'OpenGL renderer string: [^\\]*' | head -1 || echo "(KWin non risponde su D-Bus)"

echo
echo "############ il cancello, dentro la sessione vera ############"
if [ -n "${SOCKET:-}" ]; then
    echo -n "   zkde_screencast annunciato al nostro binario: "
    WAYLAND_DISPLAY="$SOCKET" "$QUI/nodo-kwin" --elenca 2>&1 | grep -c zkde_screencast || true
    echo "   e i global che ci servono:"
    WAYLAND_DISPLAY="$SOCKET" "$QUI/nodo-kwin" --elenca 2>&1 \
        | grep -iE 'zkde_screencast|fake_input|keystate|data_control|dmabuf' | sed 's/^/      /'
    echo -n "   un flusso si monta? "
    WAYLAND_DISPLAY="$SOCKET" "$QUI/nodo-kwin" > "$LOG/nodo.log" 2>&1 &
    NP=$!; sleep 3
    grep -aoE 'nodo PipeWire [0-9]+' "$LOG/nodo.log" | head -1 || echo "no"
    kill $NP 2>/dev/null
fi

echo
echo "############ M12 — la configurazione che plasmashell può lasciare ############"
echo -n "   'Open GL context could not be created' nel registro: "
grep -ac 'Open GL context could not be created' "$LOG/plasma.log" || true
echo -n "   SceneGraphBackend scritto in kdeglobals: "
grep -a 'SceneGraphBackend' ~/.config/kdeglobals 2>/dev/null || echo "(no, come deve essere con la GPU)"

echo
echo "############ M9 — il logout, e cosa sopravvive ############"
echo "   nomi sul bus prima del logout: $(gdbus call --session --dest org.freedesktop.DBus --object-path /org/freedesktop/DBus --method org.freedesktop.DBus.ListNames 2>/dev/null | tr ',' '\n' | grep -c org.kde || true) nomi org.kde"
echo "   chiamo org.kde.Shutdown.logout()"
gdbus call --session --dest org.kde.Shutdown --object-path /Shutdown \
    --method org.kde.Shutdown.logout 2>&1 | head -2 | sed 's/^/      /'
for i in $(seq 30); do pgrep -x plasmashell >/dev/null || break; sleep 1; done
sleep 3
echo "   dopo il logout:"
for p in kwin_wayland plasmashell ksmserver kded6 Xwayland; do
    printf '      %-14s %s\n' "$p" "$(pgrep -xc "$p" 2>/dev/null || echo 0)"
done
echo -n "   il bus d'utente risponde ancora? "
gdbus call --session --dest org.freedesktop.DBus --object-path /org/freedesktop/DBus \
    --method org.freedesktop.DBus.GetId 2>&1 | head -1 | sed 's/^/ /'
echo -n "   systemd --user è ancora vivo? "; systemctl --user is-system-running 2>&1
echo -n "   il socket Wayland è sparito? "; [ -S "$XDG_RUNTIME_DIR/${SOCKET:-nessuno}" ] && echo "NO, c'è ancora" || echo "sì"

echo
echo "############ pulizia ############"
systemctl --user stop plasma-workspace.target 2>&1 | head -2 | sed 's/^/   /'
for p in plasmashell kwin_wayland ksmserver kded6 Xwayland kglobalacceld xembedsniproxy; do pkill -x $p 2>/dev/null; done
sleep 2
rm -rf "$XDG_RUNTIME_DIR/systemd/user.control/plasma-kwin_wayland.service.d"
systemctl --user daemon-reload
echo "   drop-in rimosso, daemon-reload fatto"
echo "   residui:"
for p in kwin_wayland plasmashell ksmserver kded6 Xwayland; do
    printf '      %-14s %s\n' "$p" "$(pgrep -xc "$p" 2>/dev/null || echo 0)"
done
ls -1 ~/.config/ 2>/dev/null | sort > "$LOG/config-dopo.txt"
echo "   file di configurazione che Plasma ha creato (lasciati, non cancellati):"
comm -13 "$LOG/config-prima.txt" "$LOG/config-dopo.txt" | tr '\n' ' ' | sed 's/^/      /'; echo
echo "   porte 33xx: $(ss -ltn 2>/dev/null | grep -c ':33[89][0-9]' || true)"
echo "fine. registri in $LOG"
