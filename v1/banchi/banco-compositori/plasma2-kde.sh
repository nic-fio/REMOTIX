#!/bin/bash
#
# plasma2-kde.sh — perché dentro la sessione Plasma il cancello resta chiuso, con lo
# stesso `.desktop` che su KWin nudo funziona.  Non si indovina: si legge l'ambiente
# VERO del compositore e si guarda quale cache di indice usa.
#
# Sospetto principale: la cache sycoca si chiama `ksycoca6_<locale>_<hash>` e
# **l'hash non dipende da XDG_MENU_PREFIX** (misurato il 7 ago).  Dentro Plasma la
# locale può essere un'altra, e la cache di quella locale è quella vecchia,
# costruita senza prefisso e quindi VUOTA.
#
set -u
QUI=/media/REMOTIX/tmp/banco-compositori
LOG=/tmp/kde-p2; rm -rf "$LOG"; mkdir -p "$LOG"
U=$(id -u)
export XDG_RUNTIME_DIR="/run/user/$U"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
export XDG_MENU_PREFIX=plasma- LANG=C.UTF-8 LC_ALL=C.UTF-8
unset WAYLAND_DISPLAY DISPLAY QT_QPA_PLATFORM

echo "== una richiesta di password sola (kwin_wayland è non dumpable) =="
sudo -S -p 'Password: ' -v; echo "   validato: $?"

echo "== le cache di indice presenti adesso =="
ls -la ~/.cache/ksycoca6* 2>&1 | sed 's/^/   /'
echo "== la locale che Plasma si è scritto:"; cat ~/.config/plasma-localerc 2>&1 | sed 's/^/   /'

DIR="$XDG_RUNTIME_DIR/systemd/user.control/plasma-kwin_wayland.service.d"
mkdir -p "$DIR"
cat > "$DIR/remotix.conf" <<'EOF'
[Service]
ExecStart=
ExecStart=/usr/bin/kwin_wayland_wrapper --xwayland --virtual --width 1920 --height 1080 --no-lockscreen
InaccessiblePaths=/dev/dri/renderD129
EOF
systemctl --user daemon-reload

avvia_plasma() {
    setsid nohup startplasma-wayland > "$LOG/plasma-$1.log" 2>&1 &
    local i; for i in $(seq 60); do pgrep -x plasmashell >/dev/null && break; sleep 1; done
    sleep 6
    SOCKET=$(ls -1 "$XDG_RUNTIME_DIR" | grep -E '^wayland-[0-9]+$' | head -1)
    KPID=$(pgrep -x kwin_wayland | head -1)
}
chiudi_plasma() {
    gdbus call --session --dest org.kde.Shutdown --object-path /Shutdown \
        --method org.kde.Shutdown.logout >/dev/null 2>&1
    local i; for i in $(seq 25); do pgrep -x plasmashell >/dev/null || break; sleep 1; done
    for p in plasmashell kwin_wayland ksmserver kded6 Xwayland kglobalacceld; do pkill -x $p 2>/dev/null; done
    sleep 2
}
verdetto() {
    echo -n "   zkde_screencast annunciato: "
    WAYLAND_DISPLAY="$SOCKET" "$QUI/nodo-kwin" --elenca 2>&1 | grep -c zkde_screencast || true
}

echo
echo "############ giro 1 — così com'è, e si CHIEDE a KWin perché ############"
avvia_plasma 1
echo "   kwin pid: ${KPID:-nessuno}   socket: ${SOCKET:-nessuno}"
verdetto
echo "   l'ambiente VERO del compositore (le tre variabili che contano):"
sudo tr '\0' '\n' < "/proc/$KPID/environ" | grep -aE '^(XDG_MENU_PREFIX|LANG|LC_ALL|XDG_DATA_DIRS|XDG_CURRENT_DESKTOP)=' | sed 's/^/      /'
echo "   e quale cache di indice ha aperto:"
sudo ls -l "/proc/$KPID/fd" 2>/dev/null | grep -oE 'ksycoca6[^ ]*' | sort -u | sed 's/^/      /'
sudo ls -l "/proc/$KPID/map_files" 2>/dev/null | grep -oE 'ksycoca6[^ ]*' | sort -u | sed 's/^/      /'
echo "   ksmserver è partito? $(pgrep -xc ksmserver || echo 0)   Xwayland? $(pgrep -xc Xwayland || echo 0)"
echo "   righe di ksmserver nel registro della sessione:"
grep -aiE 'ksmserver|xwayland|x11' "$LOG/plasma-1.log" | head -4 | sed 's/^/      /'
chiudi_plasma

echo
echo "############ giro 2 — cache RICOSTRUITA con la locale e il prefisso di KWin ############"
# si tolgono tutte le cache: al primo processo KDE che serve, si ricostruiscono
# nell'ambiente giusto (quello della sessione), che è la cura se l'ipotesi è giusta.
rm -f ~/.cache/ksycoca6*
echo "   cache cancellate: $(ls ~/.cache/ksycoca6* 2>&1 | head -1)"
avvia_plasma 2
echo "   kwin pid: ${KPID:-nessuno}   socket: ${SOCKET:-nessuno}"
verdetto
echo "   cache presenti ora:"; ls -la ~/.cache/ksycoca6* 2>&1 | sed 's/^/      /'
echo "   e KWin dice:"
sudo tr '\0' '\n' < "/proc/$KPID/environ" 2>/dev/null | grep -aE '^(XDG_MENU_PREFIX|LANG)=' | sed 's/^/      /'
if [ "$(WAYLAND_DISPLAY="$SOCKET" "$QUI/nodo-kwin" --elenca 2>&1 | grep -c zkde_screencast || true)" != "0" ]; then
    echo "   ✅ il cancello si è aperto: un flusso vero, per prova:"
    WAYLAND_DISPLAY="$SOCKET" "$QUI/nodo-kwin" > "$LOG/nodo.log" 2>&1 &
    NP=$!; sleep 3
    grep -aoE 'nodo PipeWire [0-9]+' "$LOG/nodo.log" | head -1 | sed 's/^/      /'
    kill $NP 2>/dev/null
fi
chiudi_plasma

echo
echo "############ pulizia ############"
systemctl --user stop plasma-workspace.target 2>/dev/null
rm -rf "$XDG_RUNTIME_DIR/systemd/user.control/plasma-kwin_wayland.service.d"
systemctl --user daemon-reload
for p in plasmashell kwin_wayland ksmserver kded6 Xwayland kglobalacceld xembedsniproxy; do pkill -x $p 2>/dev/null; done
sleep 1
echo "   residui: kwin=$(pgrep -xc kwin_wayland || true) plasmashell=$(pgrep -xc plasmashell || true)"
echo "   porte 33xx: $(ss -ltn 2>/dev/null | grep -c ':33[89][0-9]' || true)"
echo "fine. registri in $LOG"
