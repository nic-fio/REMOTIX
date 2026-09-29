#!/bin/bash
# ripresa del 28 set dopo il blocco (fasi/16 §17.3): la Radeon da XFCE 3K, poi LXQt; poi LXQt Intel.
set -u
B=/media/REMOTIX/src/controllo/banchi/16-stress
M=/media/REMOTIX/misure/fase16
figlio=""; trap "[ -n \"\$figlio\" ] && kill -TERM \$figlio; exit 0" TERM INT
passo() { echo "$(date "+%F %T") ▶ ripresa: $*" >> $M/campagna.log; "$@" & figlio=$!; wait $figlio; while kill -0 $figlio 2>/dev/null; do wait $figlio; done; figlio=""; [ -e $M/FERMA ] && exit 0; }
passo env REMOTIX_16_IN_PIU="--scheda amd" REMOTIX_16_MISURE="3k 2k fhd" bash $B/16-coda.sh amd-b xfce
passo env REMOTIX_16_IN_PIU="--scheda amd" bash $B/16-coda.sh amd-b lxqt
echo "$(date "+%F %T") ⏹ campagna amd-b finita" >> $M/campagna.log
passo env REMOTIX_16_MISURE="4k 3k 2k" bash $B/16-coda.sh intel-c lxqt
echo "$(date "+%F %T") ⏹ campagna intel-c finita" >> $M/campagna.log
