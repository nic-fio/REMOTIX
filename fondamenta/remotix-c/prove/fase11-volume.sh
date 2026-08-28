#!/bin/bash
#
# Il volume della sessione governa quel che il client sente?
#
#   bash prove/fase11-volume.sh [mutter|kwin]        (predefinito: kwin)
#
# Nasce come REGRESSIONE: la correzione dell'8 agosto 2026 sta nel percorso
# CONDIVISO (`suono.c` non nomina alcun compositore), quindi vale per costruzione
# su tutti i desktop — ma «per costruzione» non e' una misura (`LEZIONI.md` §1.11).
#
# Due cose, e sono diverse:
#   1. il cursore governa: il monitor consegna un segnale piu' basso, e a zero
#      tace.  ⛔ La prova va fatta sul NOSTRO sink: uno equivalente creato con
#      `pactl` assolve il codice, perche' pipewire-pulse mette da se' la
#      proprieta' che a noi mancava;
#   2. una via audio nuova parte al massimo, perche' un livello basso lasciato
#      sul server e' uno stato che il client non puo' vedere ne' spiegare.
set -u

BASE=/media/REMOTIX
BIN="$BASE/src/remotix-c/build/src/remotix"
COMP=${1:-kwin}
PORTA=3399
FUORI=/media/REMOTIX/tmp
DENTRO=/srv/remotix/tmp
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
R=$XDG_RUNTIME_DIR/remotix-volume.log

titolo() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m    %s\n' "$*"; }
#
# GUASTI VIAGGIA SU FILE, e non e' un vezzo: il lato sessione gira in un
# sottoprocesso (`lato_sessione &`), e una variabile incrementata li' dentro NON
# torna al padre.  Contando in memoria questo banco ha stampato «guasti: 0»
# sotto a un controllo rosso, e sarebbe uscito con stato ZERO: un banco che
# mente a chi lo automatizza e' peggio di un banco che manca.
CONTO=$(mktemp); echo 0 > "$CONTO"
ko()  { printf '    \033[1;31mNO\033[0m    %s\n' "$*"; echo $(( $(cat "$CONTO") + 1 )) > "$CONTO"; }
inf() { printf '    --    %s\n' "$*"; }
GUASTI=0
attendi() { for _ in $(seq 90); do [ -e "$FUORI/$1" ] && return 0; sleep 1; done; return 1; }

[ -x "$BIN" ] || { echo "manca $BIN"; exit 1; }
mkdir -p "$FUORI"; rm -f "$FUORI"/vol-*.marca

python3 - <<'PY'
import math, struct, wave
w = wave.open('/tmp/tono.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(48000)
w.writeframes(b''.join(struct.pack('<hh',*(int(12000*math.sin(2*math.pi*440*n/48000)),)*2) for n in range(48000*40)))
w.close()
PY
SORGENTE=25.9   # ampiezza del tono, in percentuale del fondo scala

# --- il client, nel contenitore --------------------------------------------
cat > "$FUORI/vol-client.sh" <<'CLIENT'
set -u
D=:78
FUORI=/srv/remotix/tmp
attendi() { for _ in $(seq 90); do [ -e "$FUORI/$1" ] && return 0; sleep 1; done; return 1; }
pkill -f "^Xvfb $D" 2>/dev/null
Xvfb $D -screen 0 1280x1024x24 >/dev/null 2>&1 &
sleep 2
giro() {
	DISPLAY=$D timeout 100 xfreerdp3 /v:127.0.0.1:PORTA_QUI /size:1024x768 /gfx:AVC420 \
		/cert:ignore /sec:tls /u:prova /p:prova /sound /log-level:WARN >$FUORI/vol-client.log 2>&1 &
	echo $!
}
RDP=$(giro); sleep 10; touch $FUORI/vol-primo.marca
attendi vol-primo-fatto.marca
kill $RDP 2>/dev/null; wait $RDP 2>/dev/null
sleep 3; touch $FUORI/vol-staccato.marca
RDP=$(giro); sleep 10; touch $FUORI/vol-secondo.marca
attendi vol-finito.marca
kill $RDP 2>/dev/null; wait $RDP 2>/dev/null
pkill -f "^Xvfb $D" 2>/dev/null
true
CLIENT
sed -i "s/PORTA_QUI/$PORTA/" "$FUORI/vol-client.sh"

# Lo stato del nostro sink, letto da PipeWire.
stato_sink() {
	pw-dump 2>/dev/null | python3 -c "
import sys, json
for o in json.load(sys.stdin):
    i = o.get('info') or {}
    p = i.get('props') or {}
    if str(p.get('node.name'))=='remotix' and 'Audio/Sink' in str(p.get('media.class')):
        pr = [x for x in ((i.get('params') or {}).get('Props') or []) if isinstance(x, dict)]
        v = [x.get('channelVolumes') for x in pr if x.get('channelVolumes')]
        m = [x.get('mute') for x in pr if 'mute' in x]
        print('%s|%s|%s' % (p.get('monitor.channel-volumes'), v[0] if v else '?', m[0] if m else '?'))
        break
else:
    print('|nessun sink|')
"
}

# L'ampiezza che il monitor consegna a un dato volume.
ampiezza() {
	pactl set-sink-volume remotix "$1" 2>/dev/null
	sleep 0.8
	timeout -s INT 3 parecord --file-format=wav -d remotix.monitor /tmp/vol.wav 2>/dev/null
	python3 -c "
import wave, array, math, os
p='/tmp/vol.wav'
if not os.path.exists(p) or os.path.getsize(p) < 4096: print('niente'); raise SystemExit
w=wave.open(p); d=array.array('h'); d.frombytes(w.readframes(w.getnframes()))
print('%.2f' % (100*math.sqrt(sum(float(x)*x for x in d)/len(d))/32768))
"
	rm -f /tmp/vol.wav
}

lato_sessione()
{
	attendi vol-primo.marca || { ko "il client non si e' collegato"; return; }

	titolo "1. il sink, com'e' nato"
	IFS='|' read -r prop vol mute <<< "$(stato_sink)"
	inf "monitor.channel-volumes = $prop   volumi $vol   mute $mute"
	[ "$prop" = "True" ] && ok "la proprieta' c'e': il volume arriva al monitor" \
		|| ko "monitor.channel-volumes = $prop: il cursore non governerebbe niente"
	case "$vol" in *1.0*) ok "nato al massimo" ;; *) ko "nato a $vol: una via nuova deve partire udibile" ;; esac
	[ "$mute" = "False" ] && ok "non zittito" || ko "nato zittito"

	titolo "2. il cursore governa quel che il client sente"
	paplay -d remotix /tmp/tono.wav 2>/dev/null & PID=$!
	sleep 1
	inf "tono in ingresso: ${SORGENTE}% del fondo scala"
	a100=$(ampiezza 100%); a25=$(ampiezza 25%); a0=$(ampiezza 0%)
	inf "100% -> ${a100}%    25% -> ${a25}%    0% -> ${a0}%"
	# ⚠ Il 25% del cursore NON e' il 25% dell'ampiezza: PulseAudio usa una curva
	#   cubica (0,25³ = 1,56%), ed e' giusto cosi' — l'orecchio e' logaritmico.
	python3 -c "
import sys
a100,a25,a0 = float('$a100' or 0), float('$a25' or 0), float('$a0' or 0)
sys.exit(0 if (a100 > $SORGENTE*0.9 and a25 < a100*0.1 and a0 < 0.05) else 1)
" && ok "il volume passa, e lo zero e' zero" \
  || ko "il monitor non segue il cursore (100%=$a100 25%=$a25 0%=$a0)"

	kill $PID 2>/dev/null; wait $PID 2>/dev/null
	touch "$FUORI/vol-primo-fatto.marca"

	titolo "3. la via nuova parte udibile, anche se l'utente aveva zittito"
	attendi vol-staccato.marca
	# ⛔ SI ZITTISCE ADESSO, A CLIENT STACCATO, e non prima: al primo giro il
	#    banco zittiva durante la connessione e alla lettura trovava gia' il
	#    massimo — cioe' dichiarava verde un controllo che non aveva mai visto lo
	#    stato che doveva provare.  E' la §1.3: un banco che non riproduce non e'
	#    una prova di correttezza.
	pactl set-sink-volume remotix 0% 2>/dev/null
	pactl set-sink-mute remotix 1 2>/dev/null
	sleep 1
	IFS='|' read -r _ vol mute <<< "$(stato_sink)"
	inf "staccato e zittito a mano: volumi $vol   mute $mute"
	case "$vol:$mute" in *1.0*:False) ko "non sono riuscito a zittirlo: il controllo che segue non prova niente" ;;
		*) ok "lo stato da recuperare c'e' davvero" ;; esac
	attendi vol-secondo.marca || ko "il client non si e' ricollegato"
	sleep 2
	IFS='|' read -r _ vol mute <<< "$(stato_sink)"
	inf "ricollegato:       volumi $vol   mute $mute"
	case "$vol:$mute" in *1.0*:False) ok "il collegamento nuovo trova il volume al massimo" ;;
		*) ko "il collegamento nuovo trova volumi $vol mute $mute" ;; esac

	touch "$FUORI/vol-finito.marca"
}

titolo "REMOTIX su «$COMP», porta $PORTA"
pkill -x remotix 2>/dev/null; sleep 1
setsid nohup "$BIN" --compositore "$COMP" --senza-autenticazione --porta "$PORTA" \
	--registro diagnostica > "$R" 2>&1 &
sleep 2
[ "$(ss -ltn | grep -c ":$PORTA")" = 1 ] && ok "porta aperta" || ko "porta chiusa"

lato_sessione &
LATO=$!
bash "$BASE/enter.sh" "bash $DENTRO/vol-client.sh"
wait $LATO

titolo "dal registro"
grep -aE 'compositore:|volume del sink|sink audio' "$R" | tail -6 | sed 's/^/    /'
pkill -x remotix 2>/dev/null
rm -f /tmp/tono.wav
GUASTI=$(cat "$CONTO"); rm -f "$CONTO"
titolo "guasti: $GUASTI"
exit $((GUASTI > 0))
