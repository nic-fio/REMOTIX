#!/bin/bash
#
# Prova visibile della fase 1, da eseguire DENTRO la VM di runtime.
#
# PIANO.md la definisce cosi': «remotix --version gira dentro la VM; Ctrl-C lo
# ferma senza lasciare processi».  Qui si verifica esattamente quello, piu' il
# fratello SIGTERM, che e' il segnale con cui systemd fermera' il servizio
# nella fase 11.
set -u

BIN=${1:-$HOME/remotix}
esito=0

riga() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
buono() { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
cattivo() { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; esito=1; }

riga "1. versione"
if "$BIN" --version; then buono "--version risponde"; else cattivo "--version fallisce"; fi

riga "2. aiuto"
"$BIN" --help >/dev/null 2>&1 && buono "--help risponde" || cattivo "--help fallisce"

riga "3. opzione sbagliata: deve rifiutare, non ignorare"
if "$BIN" --registro inesistente >/dev/null 2>&1; then
    cattivo "ha accettato un livello di registro inventato"
else
    buono "livello di registro sconosciuto: rifiutato"
fi
if "$BIN" --porta 70000 >/dev/null 2>&1; then
    cattivo "ha accettato la porta 70000"
else
    buono "porta fuori intervallo: rifiutata"
fi

for segnale in INT TERM; do
    riga "4. arresto con SIG$segnale"
    "$BIN" --registro diagnostica >/tmp/remotix-$segnale.log 2>&1 &
    pid=$!
    sleep 1
    if ! kill -0 "$pid" 2>/dev/null; then
        cattivo "non e' rimasto in esecuzione"
        continue
    fi
    inizio=$(date +%s%N)
    kill -"$segnale" "$pid"
    wait "$pid"
    uscita=$?
    durata=$(( ($(date +%s%N) - inizio) / 1000000 ))

    [ "$uscita" -eq 0 ] && buono "uscito con codice 0 in ${durata} ms" \
        || cattivo "uscito con codice $uscita"
    grep -q "arresto richiesto" /tmp/remotix-$segnale.log \
        && buono "ha dichiarato l'arresto nel registro" \
        || cattivo "non ha annotato l'arresto"
    grep -q "chiuso" /tmp/remotix-$segnale.log \
        && buono "ha annotato la chiusura" || cattivo "non ha annotato la chiusura"
done

riga "5. nessun processo residuo"
sleep 1
if pgrep -x remotix >/dev/null; then
    cattivo "sono rimasti processi: $(pgrep -x remotix | tr '\n' ' ')"
else
    buono "nessun processo remotix in esecuzione"
fi

riga "Esito"
[ $esito -eq 0 ] && printf '    \033[1;32mFASE 1 VERDE\033[0m\n' \
                 || printf '    \033[1;31mQUALCOSA NON VA\033[0m\n'
exit $esito
