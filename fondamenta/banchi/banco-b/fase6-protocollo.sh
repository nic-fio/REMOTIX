#!/bin/bash
# REMOTIX con la SCENA SINTETICA, dentro il contenitore: nessuna sessione
# grafica, nessun palco, nessun PipeWire.  Se il ridimensionamento non si vede
# qui, il sospetto cade su una cosa sola — il protocollo — ed e' la lezione di
# §5.4 di SPECIFICA.md applicata alla fase 6.
set -u
pkill -f "remotix --porta 3390" 2>/dev/null; sleep 1
cd /srv/remotix/tmp/banco-b || exit 1
rm -f fase6-protocollo.log
setsid nohup /srv/src/remotix-c/build/src/remotix --porta 3390 --registro diagnostica \
    --senza-autenticazione --immagine-di-prova >fase6-protocollo.log 2>&1 </dev/null &
sleep 2
pgrep -f "remotix --porta 3390" >/dev/null \
    && echo "   REMOTIX (scena sintetica) avviato sulla 3390" \
    || { echo "   NON avviato"; exit 1; }
