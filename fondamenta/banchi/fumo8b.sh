#!/bin/bash
# Fase 8, prova completa: il tono suonato nella sessione esce dagli altoparlanti
# del CLIENT.  Il client suona su un impianto PipeWire finto dentro il
# contenitore, e si registra il monitor del suo sink.
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
export XDG_RUNTIME_DIR=/tmp/rt
pkill -x xfreerdp3 2>/dev/null
pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null; sleep 1
Xvfb $DISPLAY_CLI -screen 0 2400x1600x24 -nolisten tcp >/dev/null 2>&1 &
sleep 2
cd $BANCO || exit 1
rm -f fumo8-client.log
setsid nohup env DISPLAY=$DISPLAY_CLI XDG_RUNTIME_DIR=/tmp/rt xfreerdp3 \\
    /v:127.0.0.1:$PORTA /gfx:AVC420 /cert:ignore /sec:tls /u:prova /p:prova \\
    /size:1280x800 /sound /log-level:INFO >fumo8-client.log 2>&1 </dev/null &
sleep 8
pgrep -x xfreerdp3 >/dev/null && echo "   client collegato" || echo "   client NON partito"
CLIENT

cat > "$BANCO_FUORI/fumo8-registra.sh" <<REG
#!/bin/bash
set -u
export XDG_RUNTIME_DIR=/tmp/rt
rm -f /tmp/uscita.wav
setsid nohup pw-record --target uscita --rate 44100 --channels 2 --format s16 \\
    /tmp/uscita.wav >/dev/null 2>&1 </dev/null &
echo \$! > /tmp/rec.pid
echo "   registrazione avviata"
REG

cat > "$BANCO_FUORI/fumo8-esamina.sh" <<ESA
#!/bin/bash
set -u
kill \$(cat /tmp/rec.pid) 2>/dev/null; sleep 1
python3 - <<'PY'
import wave, struct
w = wave.open('/tmp/uscita.wav'); n = w.getnframes(); d = w.readframes(n)
v = struct.unpack('<%dh' % (len(d)//2), d) if d else ()
picco = max(abs(x) for x in v) if v else 0
sopra = sum(1 for x in v if abs(x) > 1000)
print("   il client ha suonato %d fotogrammi, picco %d, campioni non silenziosi %d"
      % (n, picco, sopra))
PY
ESA

echo "== 1. binario nuovo nella VM"
vm "sudo systemctl stop remotix.service 2>/dev/null; sleep 1" >/dev/null 2>&1
bash "$BASE/vm.sh" copia "$BIN" >/dev/null || exit 1
vm "bash avvia-remotix.sh --aperto" | tail -1

echo "== 2. il client si collega con /sound, e registro la sua uscita"
cnt "bash $BANCO/fumo8-client.sh"
cnt "bash $BANCO/fumo8-registra.sh"

echo "== 3. la sessione suona"
vm "for i in 1 2 3; do pw-play /tmp/tono.wav; done; echo '   tono suonato tre volte'"
sleep 3

echo "== 4. che cosa e' uscito dal client"
cnt "bash $BANCO/fumo8-esamina.sh"

echo "== 5. il registro del server"
vm "grep -E 'audio negoziato|audio:' ~/remotix.log | tail -3"

echo "== 6. il registro audio del client"
cnt "grep -iE 'rdpsnd' $BANCO/fumo8-client.log | tail -4"
cnt "pkill -x xfreerdp3 2>/dev/null; sleep 2; echo '   client chiuso'"
