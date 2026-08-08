#!/bin/bash
#
# Banco per la misura B della fase 0: i bordi della regione AVC420 sono
# inclusivi o esclusivi?
#
# Si mette un server FreeRDP (shadow) davanti a uno schermo virtuale di misura
# NOTA, gli si fa mandare AVC420 su EGFX, e si legge che cosa scrive nei
# rettangoli della metablock.  La lettura avviene con l'innesto spia-avc420.so,
# che intercetta avc420_decompress nel client: fra quei valori e i byte del filo
# c'e' un solo passaggio, rdpgfx_read_rect16, che legge quattro UINT16 in fila
# senza aggiustamenti.
#
# Il discriminante e' netto: su uno schermo largo L, un rettangolo che parte da
# left=0 e copre tutto avra' right = L se i bordi sono esclusivi, right = L-1
# se sono inclusivi.
#
# Si usa una misura NON allineata (1282x802) apposta: se il server allineasse a
# 16/64 riducendo invece di riempire, la differenza salterebbe fuori qui.
set -u

LARG=${LARG:-1282}
ALT=${ALT:-802}
PORTA=${PORTA:-3390}
BASE=/srv/remotix/tmp/banco-b
DISPLAY_SRV=:99
DISPLAY_CLI=:100

mkdir -p "$BASE"
cd "$BASE" || exit 1

pulisci() {
    kill %1 %2 %3 2>/dev/null
    pkill -f "Xvfb $DISPLAY_SRV" 2>/dev/null
    pkill -f "Xvfb $DISPLAY_CLI" 2>/dev/null
    pkill -f "freerdp-shadow" 2>/dev/null
}
trap pulisci EXIT

echo "== 1. schermo virtuale da servire: ${LARG}x${ALT}"
Xvfb $DISPLAY_SRV -screen 0 "${LARG}x${ALT}x24" -nolisten tcp >/dev/null 2>&1 &
Xvfb $DISPLAY_CLI -screen 0 "1400x900x24" -nolisten tcp >/dev/null 2>&1 &
sleep 2
DISPLAY=$DISPLAY_SRV xsetroot -solid steelblue 2>/dev/null
DISPLAY=$DISPLAY_SRV xclock -update 1 >/dev/null 2>&1 &
sleep 1

echo "== 2. server shadow sulla porta $PORTA, con il SOLO AVC420 acceso"
# si spengono gli altri codec EGFX cosi' non resta scelta: o AVC420 o niente.
# -auth e -sec-nla tolgono l'autenticazione, che qui non c'entra e chiederebbe
# un file SAM.
DISPLAY=$DISPLAY_SRV freerdp-shadow-cli3 /port:$PORTA \
    +gfx +gfx-avc420 -gfx-avc444 -gfx-planar -gfx-progressive -gfx-rfx \
    -auth -sec-nla /log-level:INFO >shadow.log 2>&1 &
sleep 4
if ! grep -qiE "listen|Listening" shadow.log && ! ss -ltn 2>/dev/null | grep -q ":$PORTA"; then
    echo "!! il server non ascolta; registro:"; tail -20 shadow.log; exit 1
fi

echo "== 3. client con l'innesto, per 8 secondi"
rm -f rect.txt
DISPLAY=$DISPLAY_CLI LD_PRELOAD="$BASE/spia-avc420.so" SPIA_AVC420="$BASE/rect.txt" \
    timeout 12 xfreerdp3 /v:127.0.0.1:$PORTA /gfx:AVC420 /cert:ignore /sec:tls \
    /u:prova /p:prova /size:${LARG}x${ALT} /log-level:WARN \
    >client.log 2>&1

echo
echo "======== RETTANGOLI LETTI DAL FILO ========"
if [ -s rect.txt ]; then
    head -40 rect.txt
else
    echo "(nessun fotogramma AVC420 decodificato)"
    echo "--- registro server:"; tail -15 shadow.log
    echo "--- registro client:"; tail -15 client.log
fi
