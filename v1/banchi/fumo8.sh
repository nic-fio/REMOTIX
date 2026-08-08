#!/bin/bash
# Prova di fumo della fase 8: il suono arriva al client?
set -u
BASE=/media/REMOTIX
BIN="$BASE/src/remotix-c/build/src/remotix"
BANCO=/srv/remotix/tmp/banco-b
BANCO_FUORI=/media/REMOTIX/tmp/banco-b
PORTA=3389
DISPLAY_CLI=:110

vm()  { bash "$BASE/vm.sh" ssh "$@" </dev/null; }
cnt() { bash "$BASE/enter.sh" "$@"; }

cat > "$BANCO_FUORI/fumo8-client.sh" <<CLIENT
#!/bin/bash
set -u
pkill -x xfreerdp3 2>/dev/null
pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null; sleep 1
Xvfb $DISPLAY_CLI -screen 0 2400x1600x24 -nolisten tcp >/dev/null 2>&1 &
sleep 2
cd $BANCO || exit 1
rm -f fumo8-client.log
setsid nohup env DISPLAY=$DISPLAY_CLI xfreerdp3 /v:127.0.0.1:$PORTA /gfx:AVC420 \\
    /cert:ignore /sec:tls /u:prova /p:prova /size:1280x800 /sound \\
    /log-level:INFO >fumo8-client.log 2>&1 </dev/null &
sleep 8
pgrep -x xfreerdp3 >/dev/null && echo "   client collegato" || echo "   client NON partito"
CLIENT

echo "== 1. binario nuovo nella VM"
vm "sudo systemctl stop remotix.service 2>/dev/null; sleep 1" >/dev/null 2>&1
bash "$BASE/vm.sh" copia "$BIN" >/dev/null || exit 1
vm "bash avvia-remotix.sh --aperto" | tail -2

echo "== 2. il client si collega con /sound"
cnt "bash $BANCO/fumo8-client.sh"

echo "== 3. dieci secondi di SILENZIO, per vedere se lo spediamo"
sleep 10
vm "grep -E 'audio:' ~/remotix.log | tail -2"

echo "== 4. adesso la sessione suona"
vm "for i in 1 2 3 4 5 6; do pw-play /tmp/tono.wav; done; echo '   tono suonato sei volte'"
sleep 3

echo "== 5. il registro del server"
vm "grep -E 'sink audio|formati audio|audio negoziato|suono collegato|blocco di suono|audio:' ~/remotix.log | tail -12"

echo "== 6. chiudo il client e leggo il conto finale"
cnt "pkill -x xfreerdp3 2>/dev/null; sleep 3; echo '   client chiuso'"
vm "grep -E 'audio:|connessione conclusa' ~/remotix.log | tail -4"
