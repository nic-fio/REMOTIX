#!/bin/bash
#
# misure5-kde.sh — due cose in un colpo, con la stessa tecnica:
#
#  (1) LA GPU CHE VUOLE L'UTENTE.  Deciso dall'utente l'8 agosto 2026: «non usare
#      la Radeon, usa la Intel integrata».  Ma `findRenderDevice()`
#      (`virtual_backend.cpp:23-56`) prende **la prima che si apre**, senza alcuna
#      variabile: su questa macchina drmGetDevices2() dà prima la Radeon
#      (renderD129, amdgpu) e poi la Intel (renderD128, i915).
#      Quindi la Intel si ottiene in un modo solo: **rendere la Radeon
#      inaccessibile a quel processo**.  Qui con un namespace di monti privato —
#      niente cambia fuori, e finisce quando il processo esce.
#      ⚠ Per il PRODOTTO l'equivalente è `InaccessiblePaths=` nell'unità systemd
#        del compositore, che già sovrascriviamo per `--virtual` (`kde.md` §6.1).
#
#  (2) M4 — «KWIN_COMPOSE=O2 esce o parte in software?»  Con lo stesso mezzo si
#      nascondono TUTTI i render node: allora OpenGL è impossibile per davvero, che
#      è la condizione che `kde.md` §5.4 descrive e che nessun tentativo con le
#      variabili di Mesa era riuscito a produrre.
#
set -u
QUI=/media/REMOTIX/tmp/banco-compositori
LOG=/tmp/kde-m5; rm -rf "$LOG"; mkdir -p "$LOG"
export LANG=C.UTF-8 LC_ALL=C.UTF-8 XDG_MENU_PREFIX=plasma-
[ -n "${XDG_RUNTIME_DIR:-}" ] && [ -d "${XDG_RUNTIME_DIR:-}" ] || {
    export XDG_RUNTIME_DIR="/tmp/xdg-$(id -u)"; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"; }
BUS="unix:path=/run/user/$(id -u)/bus"
SOCK=wayland-kde
U=$(id -u); G=$(id -g)

: > /tmp/nodo-negato; chmod 000 /tmp/nodo-negato

echo "== una richiesta di password sola, per unshare =="
sudo -S -p 'Password: ' -v; echo "   validato: $?"
echo "== la mappa: renderD128=Intel(i915)  renderD129=Radeon(amdgpu)"

# $1 = etichetta   $2 = elenco di nodi da nascondere (spazio-separato)   $3.. = env
giro() {
    local nome="$1" nascondi="$2"; shift 2
    rm -f "$XDG_RUNTIME_DIR/$SOCK" "$XDG_RUNTIME_DIR/$SOCK.lock"
    local monta=""
    for n in $nascondi; do monta="$monta mount --bind /tmp/nodo-negato $n;"; done
    sudo unshare --mount --propagation private bash -c "
        $monta
        setpriv --reuid $U --regid $G --init-groups \
          env LANG=C.UTF-8 XDG_MENU_PREFIX=plasma- HOME=$HOME PATH=/usr/bin:/bin \
              XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS=$BUS $* \
              QT_LOGGING_RULES='kwin_core.debug=true' \
          kwin_wayland --virtual --width 1280 --height 720 --no-lockscreen --socket=$SOCK \
          > $LOG/$nome.log 2>&1 &
        K=\$!
        for i in \$(seq 40); do [ -S $XDG_RUNTIME_DIR/$SOCK ] && break; sleep 0.25; done
        sleep 3
        if kill -0 \$K 2>/dev/null; then echo VIVO > $LOG/$nome.stato; else echo MORTO > $LOG/$nome.stato; fi
        sleep 12          # tempo per le domande da fuori
        kill \$K 2>/dev/null; wait 2>/dev/null" &
    SUDOPID=$!
    sleep 6
    if [ "$(cat "$LOG/$nome.stato" 2>/dev/null)" = VIVO ]; then
        echo "   KWin: PARTITO"
        echo -n "   renderer secondo KWin : "
        gdbus call --session --dest org.kde.KWin --object-path /KWin \
            --method org.kde.KWin.supportInformation 2>/dev/null \
            | grep -aoE 'OpenGL renderer string: [^\\]*' | head -1 || echo "(nessuna: QPainter)"
        echo -n "   dmabuf annunciato     : "
        WAYLAND_DISPLAY="$SOCK" "$QUI/nodo-kwin" --elenca 2>&1 | grep -c zwp_linux_dmabuf_v1 || true
        echo -n "   cattura disponibile   : "
        WAYLAND_DISPLAY="$SOCK" "$QUI/nodo-kwin" --elenca 2>&1 | grep -c zkde_screencast || true
    else
        echo "   KWin: ⛔ USCITO"
    fi
    echo "   registro:"
    grep -aiE 'failed to open drm|render node|compositing|qpainter|opengl|not supported|falling back|enforced' \
        "$LOG/$nome.log" 2>/dev/null | head -5 | sed 's/^/      /'
    wait $SUDOPID 2>/dev/null
    sleep 1
}

echo
echo "############ (1) la Intel integrata ############"
echo "--- A: come adesso, niente nascosto (deve dire Radeon)"
giro a-cosi-com-e ""
echo
echo "--- B: Radeon nascosta → deve prendere la Intel"
giro b-solo-intel "/dev/dri/renderD129"

echo
echo "############ (2) M4 — KWIN_COMPOSE=O2 protegge? ############"
echo "--- C: TUTTI i render node nascosti, senza KWIN_COMPOSE (controllo positivo)"
giro c-niente-gpu "/dev/dri/renderD128 /dev/dri/renderD129"
echo
echo "--- D: gli stessi nodi nascosti, CON KWIN_COMPOSE=O2 → esce o ripiega?"
giro d-O2-senza-gpu "/dev/dri/renderD128 /dev/dri/renderD129" KWIN_COMPOSE=O2

rm -f /tmp/nodo-negato
sudo pkill -x kwin_wayland 2>/dev/null; pkill -x nodo-kwin 2>/dev/null
sleep 0.5
echo
echo "residui: kwin=$(pgrep -xc kwin_wayland || true)"
echo "montaggi lasciati sul sistema (deve essere vuoto):"
grep -c 'nodo-negato' /proc/mounts || true
echo "fine. registri in $LOG"
