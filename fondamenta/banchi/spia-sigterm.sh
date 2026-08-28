#!/bin/bash
#
# Solo la sezione 1 di fase5.sh, ma senza cancellare il registro dopo:
# serve una cosa sola, la riga che dice CHI ha mandato il SIGTERM.
set -u

BASE=/media/REMOTIX
BIN_LOCALE="$BASE/src/remotix-c/build/src/remotix"
MISURA=${MISURA:-1282x802}
PORTA=3389
DISPLAY_CLI=:109
BANCO=/srv/remotix/tmp/banco-b

vm()  { bash "$BASE/vm.sh" ssh "$@" </dev/null; }
cnt() { bash "$BASE/enter.sh" "$@"; }

vm "sudo systemctl stop remotix.service 2>/dev/null; sleep 1" >/dev/null 2>&1
bash "$BASE/vm.sh" copia "$BIN_LOCALE" >/dev/null || exit 1
vm "rm -f ~/remotix.log; bash avvia-remotix.sh --aperto" >/dev/null || exit 1

cnt "
    pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null; sleep 1
    Xvfb $DISPLAY_CLI -screen 0 1500x1000x24 -nolisten tcp >/dev/null 2>&1 &
    sleep 2
    cd $BANCO
    setsid nohup env DISPLAY=$DISPLAY_CLI xfreerdp3 /v:127.0.0.1:$PORTA /gfx:AVC420 \
        /cert:ignore /sec:tls /u:prova /p:prova /size:$MISURA /log-level:INFO \
        >spia-sigterm.log 2>&1 </dev/null &
    sleep 1
    echo '   client avviato'
"
echo '   aspetto che il desktop sia in piedi'
sleep 20

vm "gdbus call --session --dest org.gnome.SessionManager \
      --object-path /org/gnome/SessionManager \
      --method org.gnome.SessionManager.Logout 1" >/dev/null 2>&1 \
    && echo '   «Esci» richiesto' || echo '   Logout NON richiesto'
sleep 10

echo
echo '=== coda del registro di REMOTIX ==='
vm "tail -25 ~/remotix.log"
echo
echo '=== il server e ancora vivo? ==='
vm "pgrep -x remotix >/dev/null && echo VIVO || echo MORTO"
echo
echo '=== journal, ultimi 40 ==='
vm "sudo journalctl -n 40 --no-pager"
