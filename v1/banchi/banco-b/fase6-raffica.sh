#!/bin/bash
# La raffica vera: le misure si mandano DENTRO UNA SOLA invocazione.
#
# ⚠ Chiamare `fase6-ridimensiona.sh` una volta per misura non produce nessuna
#   raffica, e ci si casca: ogni giro costa una sessione SSH e un ingresso nel
#   contenitore, cioe' piu' di un secondo — piu' del tempo che il server impiega
#   ad applicare un ridimensionamento.  Le richieste arriverebbero in fila
#   indiana, e la prova direbbe di aver collaudato l'accorpamento senza averlo
#   mai fatto scattare.
set -u
ID=$(cat /srv/remotix/tmp/banco-b/fase6-finestra 2>/dev/null)
[ -n "$ID" ] || { echo "   nessuna finestra da ridimensionare"; exit 1; }
for m in "1500 860" "1420 820" "1340 780" "1260 740" "1180 700" "1520 880" "1360 800" "1240 720"; do
    set -- $m
    DISPLAY=:110 xdotool windowsize $ID $1 $2
    # Il client di FreeRDP non manda piu' di un layout ogni 200 ms
    # (RESIZE_MIN_DELAY): sotto quella soglia accorpa LUI, e si misurerebbe il
    # client invece del server.  Sopra di poco, e le richieste si accavallano
    # sul server, che e' esattamente il caso da provare.
    sleep 0.3
done
echo "   raffica di 8 misure mandata in 2,4 secondi"
