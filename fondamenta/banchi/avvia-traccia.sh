#!/bin/bash
cd "$HOME" || exit 1
pkill -x remotix 2>/dev/null
sleep 1
rm -f "$HOME/remotix.log"
setsid nohup ./remotix --porta 3389 --registro traccia --senza-autenticazione \
    >"$HOME/remotix.log" 2>&1 </dev/null &
sleep 3
pgrep -x remotix >/dev/null && echo "   REMOTIX avviato" || { echo "   NON avviato"; exit 1; }
