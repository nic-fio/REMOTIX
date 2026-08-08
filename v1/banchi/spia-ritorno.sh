#!/bin/bash
#
# Il ciclo che il difetto riguarda, e nient'altro:
#   accesso → logout → SECONDO accesso.
#
# Stampa il registro intero, perche' la domanda e' «cosa succede al secondo
# giro», e una coda non basta a rispondere.
set -u

BASE=/media/REMOTIX
BIN_LOCALE="$BASE/src/remotix-c/build/src/remotix"
MISURA=${MISURA:-1282x802}
PORTA=3389
DISPLAY_CLI=:109
BANCO=/srv/remotix/tmp/banco-b

vm()  { bash "$BASE/vm.sh" ssh "$@" </dev/null; }
cnt() { bash "$BASE/enter.sh" "$@"; }

cliente() {   # $1 = nome del registro, $2 = secondi di permanenza
    cnt "
        pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null; sleep 1
        Xvfb $DISPLAY_CLI -screen 0 1500x1000x24 -nolisten tcp >/dev/null 2>&1 &
        sleep 2
        cd $BANCO
        DISPLAY=$DISPLAY_CLI timeout $2 xfreerdp3 /v:127.0.0.1:$PORTA /gfx:AVC420 \
            /cert:ignore /sec:tls /u:prova /p:prova /size:$MISURA /log-level:INFO \
            >$1 2>&1 </dev/null
        pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null
        echo \"   client $1 concluso\"
    "
}

vm "sudo systemctl stop remotix.service 2>/dev/null; sleep 1" >/dev/null 2>&1
bash "$BASE/vm.sh" copia "$BIN_LOCALE" >/dev/null || exit 1
vm "rm -f ~/remotix.log; bash avvia-remotix.sh --aperto" >/dev/null || exit 1

echo '=== PRIMO ACCESSO ==='
cliente ritorno-1.log 25

echo '=== LOGOUT ==='
vm "gdbus call --session --dest org.gnome.SessionManager \
      --object-path /org/gnome/SessionManager \
      --method org.gnome.SessionManager.Logout 1" >/dev/null 2>&1 \
    && echo '   «Esci» richiesto' || echo '   Logout NON richiesto'
sleep 12

vm "pgrep -x remotix >/dev/null && echo '   il server e VIVO' || echo '   il server e MORTO'"

echo '=== SECONDO ACCESSO ==='
cliente ritorno-2.log 30

echo
echo '=== registro di REMOTIX, senza il rumore di x264 ==='
vm "grep -vE 'libx264|pila #' ~/remotix.log"
echo
echo '=== cosa ha visto il client al SECONDO accesso ==='
grep -aE 'Error|error|ERRINFO|gfx|Gfx|resolution|connected to' \
    /media/REMOTIX/tmp/banco-b/ritorno-2.log 2>/dev/null | tail -15
