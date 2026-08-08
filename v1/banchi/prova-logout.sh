#!/bin/bash
set -u
BASE=/media/REMOTIX
vm() { bash "$BASE/vm.sh" ssh "$@" </dev/null; }
bash "$BASE/vm.sh" copia "$BASE/tmp/avvia-remotix.sh" >/dev/null
vm "bash avvia-remotix.sh --aperto" >/dev/null
sleep 2
vm "systemctl --user show remotix.service -p ControlGroup"
echo "== avvio la sessione grafica e poi esco"
vm "gdbus call --session --dest org.gnome.Mutter.DisplayConfig --object-path /org/gnome/Mutter/DisplayConfig --method org.freedesktop.DBus.Peer.Ping >/dev/null 2>&1 || echo 'nessuna sessione: la avvio io'"
vm "test -f /tmp/x || true"
# una connessione fa partire la sessione
bash "$BASE/enter.sh" "
    pkill -f '^Xvfb :110' 2>/dev/null; sleep 1
    Xvfb :110 -screen 0 1400x900x24 -nolisten tcp >/dev/null 2>&1 &
    sleep 2
    cd /srv/remotix/tmp/banco-b
    setsid nohup env DISPLAY=:110 xfreerdp3 /v:127.0.0.1:3389 /gfx:AVC420 /cert:ignore /sec:tls \
        /u:prova /p:prova /size:1282x802 /log-level:WARN >logout-cli.log 2>&1 </dev/null &
    sleep 1; echo '   client avviato'
"
sleep 22
vm "gdbus call --session --dest org.gnome.SessionManager --object-path /org/gnome/SessionManager --method org.gnome.SessionManager.Logout 1" >/dev/null 2>&1
echo "== «Esci» richiesto"
sleep 10
if vm "pgrep -x remotix >/dev/null"; then
    echo "   ✅ REMOTIX E' SOPRAVVISSUTO"
else
    echo "   ❌ REMOTIX E' MORTO"
fi
vm "grep -E 'arrivato SIG|sta uscendo|disiscritti' ~/remotix.log | tail -5"
bash "$BASE/enter.sh" "pkill -f '^Xvfb :110' 2>/dev/null; true"
