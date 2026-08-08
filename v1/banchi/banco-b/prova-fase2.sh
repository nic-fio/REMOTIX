#!/bin/bash
#
# Prova della fase 2 nel contenitore: REMOTIX disegna?
#
# Si collega un client FreeRDP strumentato con gli stessi innesti usati per la
# misura B, cosi' si vede QUALE codec arriva e con quali rettangoli — non solo
# «si connette».  Un client che si collega e non riceve fotogrammi e' lo
# schermo nero di §8.1, ed e' il difetto che questa prova deve saper vedere.
set -u

BANCO=/srv/remotix/tmp/banco-b
BIN=${BIN:-/srv/src/remotix-c/build/src/remotix}
PORTA=${PORTA:-3391}
MISURA=${MISURA:-1282x802}
DISPLAY_CLI=:102

cd "$BANCO" || exit 1
pkill -f "remotix --porta $PORTA" 2>/dev/null
pkill -f "Xvfb $DISPLAY_CLI" 2>/dev/null
rm -f fase2-rect.txt fase2-prog.txt fase2-server.log fase2-client.log

Xvfb $DISPLAY_CLI -screen 0 1400x900x24 -nolisten tcp >/dev/null 2>&1 &
sleep 2

echo "== avvio REMOTIX sulla porta $PORTA"
XDG_DATA_HOME="$BANCO/dati" "$BIN" --porta "$PORTA" --senza-autenticazione \
    --registro diagnostica >fase2-server.log 2>&1 &
SERVER=$!
sleep 3
if ! kill -0 $SERVER 2>/dev/null; then
    echo "!! il server non e' partito:"; cat fase2-server.log; exit 1
fi

echo "== client per 10 secondi, misura $MISURA, codec richiesto: ${GFX:-AVC420}"
DISPLAY=$DISPLAY_CLI \
LD_PRELOAD="$BANCO/spia-progressive.so:$BANCO/spia-avc420.so" \
SPIA_PROGRESSIVE="$BANCO/fase2-prog.txt" SPIA_AVC420="$BANCO/fase2-rect.txt" \
    timeout 10 xfreerdp3 /v:127.0.0.1:$PORTA "/gfx:${GFX:-AVC420}" /cert:ignore /sec:tls \
    /u:prova /p:prova "/size:$MISURA" /log-level:WARN >fase2-client.log 2>&1

kill -INT $SERVER 2>/dev/null; wait $SERVER 2>/dev/null
pkill -f "Xvfb $DISPLAY_CLI" 2>/dev/null

echo
echo "======== COSA E' ARRIVATO AL CLIENT ========"
echo "-- AVC420:               $(grep -c '^fotogramma' fase2-rect.txt 2>/dev/null || echo 0) fotogrammi"
head -4 fase2-rect.txt 2>/dev/null
echo "-- RemoteFX Progressive: $(wc -l < fase2-prog.txt 2>/dev/null || echo 0) fotogrammi"
head -2 fase2-prog.txt 2>/dev/null
echo
echo "======== REGISTRO DEL SERVER ========"
grep -vE "TRACC" fase2-server.log | tail -20
echo
echo "======== REGISTRO DEL CLIENT (errori) ========"
grep -iE "error|fail" fase2-client.log | head -8 || echo "(nessun errore)"
