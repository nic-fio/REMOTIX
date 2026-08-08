#!/bin/bash
#
# Controprova del banco A, da eseguire nel contenitore del server.
#
# Si collega con un client FreeRDP a grd nella VM (raggiungibile su
# 127.0.0.1:3389 grazie all'inoltro di porta di QEMU) e certifica, con
# l'innesto, quale codec arriva davvero.  Serve a distinguere «il banco non
# manda RFX Progressive» da «RDM non lo rende», che e' la domanda della misura A.
set -u

BASE=/srv/remotix/tmp/banco-b
cd "$BASE" || exit 1
DISPLAY_CLI=:101

pkill -f "Xvfb $DISPLAY_CLI" 2>/dev/null
Xvfb $DISPLAY_CLI -screen 0 1400x900x24 -nolisten tcp >/dev/null 2>&1 &
sleep 2

gcc -shared -fPIC -O2 -o spia-progressive.so spia-progressive.c -ldl || exit 1
rm -f prog.txt rect-vm.txt

echo "== client verso grd nella VM (127.0.0.1:3389), 15 secondi"
DISPLAY=$DISPLAY_CLI \
LD_PRELOAD="$BASE/spia-progressive.so:$BASE/spia-avc420.so" \
SPIA_PROGRESSIVE="$BASE/prog.txt" SPIA_AVC420="$BASE/rect-vm.txt" \
    timeout 15 xfreerdp3 /v:127.0.0.1:3389 /gfx /cert:ignore \
    /u:prova /p:prova /size:1280x800 /log-level:WARN >client-vm.log 2>&1

echo
echo "======== CODEC RICEVUTI DALLA VM ========"
echo "-- RemoteFX Progressive: $(wc -l < prog.txt 2>/dev/null || echo 0) fotogrammi"
head -5 prog.txt 2>/dev/null
echo "-- AVC420: $(grep -c ^fotogramma rect-vm.txt 2>/dev/null || echo 0) fotogrammi"
head -3 rect-vm.txt 2>/dev/null
echo
echo "-- registro client (ultime righe):"
tail -12 client-vm.log
pkill -f "Xvfb $DISPLAY_CLI" 2>/dev/null
