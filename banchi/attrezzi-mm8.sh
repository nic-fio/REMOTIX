#!/bin/bash
# ⛔ La parola d'ordine NON passa dalla riga di comando — difetto **D12**,
#    curato il 12 agosto 2026.  Stava dentro `$C`, cioe' nella stringa che
#    `bash $E --root "…"` riceve come argomento: nell'`argv` di `bash`, in
#    quello di `sudo` e in quello di `python3`.  ⭐ La strada e' quella di
#    `01-b10-lancia.sh`: file `0600` scritto con `printf` (builtin), passato
#    come `--parola-file`, cancellato con una `trap`.
set -uo pipefail
E=/media/REMOTIX/enter.sh; D=/srv/src
FUORI=/media/REMOTIX/src
PAROLA=${PAROLA:-parola-di-prova}
PAROLA_FUORI=$FUORI/tmp/attrezzi-mm8-parola
PAROLA_DENTRO=$D/tmp/attrezzi-mm8-parola
# ⛔ `umask` in una SOTTOSHELL: nudo resterebbe addosso a tutto quel che segue,
#    compresi i comandi mandati dentro il contenitore (la riga che B10 ha
#    pagato con un giro intero).
mkdir -p "$FUORI/tmp" \
  && ( umask 077; : > "$PAROLA_FUORI" ) \
  && chmod 600 "$PAROLA_FUORI" \
  || { printf '⛔ non si scrive %s\n' "$PAROLA_FUORI"; exit 2; }
printf '%s\n' "$PAROLA" > "$PAROLA_FUORI"
C="python3 -u $D/01-b8-cronometro.py --bersaglio innesto --porta 7447 --indirizzi 127.0.0.1,192.168.0.2 --utente prova --parola-file $PAROLA_DENTRO"
ripulisci() {
  rm -f "$PAROLA_FUORI"
  bash $E --root "python3 $D/01-b12-guasti.py --togli B8" >/dev/null 2>&1
  bash $E --root "ninja -C $D/b2/ngtcp2/build bsslserver" >/dev/null 2>&1
  echo "== ripulito e ricostruito"
}
trap ripulisci EXIT
bash $E --root "python3 $D/01-b12-guasti.py --applica B8" 2>&1 | tail -1
bash $E --root "ninja -C $D/b2/ngtcp2/build bsslserver" >/dev/null 2>&1 || { echo "compilazione fallita"; exit 3; }
bash $E --root "nohup env LD_LIBRARY_PATH=$D/b2/ngtcp2/build/lib $D/b2/ngtcp2/build/examples/bsslserver --timeout=120s 0.0.0.0 7447 /media/REMOTIX/b2-certificati/sessione.key /media/REMOTIX/b2-certificati/sessione.pem < /dev/null > $D/mm.log 2>&1 & echo \$! > $D/mm.pid"
sleep 2
PID=$(cat /media/REMOTIX/src/mm.pid)
bash $E --root "rm -f $D/mm8.jsonl; $C --campioni --blocco 1 --giro mm8 --uscita $D/mm8.jsonl > $D/mm-uscita.txt 2>&1"
echo "CAMPIONI=$?"
bash $E --root "$C --verdetto --giro mm8 --uscita $D/mm8.jsonl >> $D/mm-uscita.txt 2>&1"
echo "VERDETTO=$?"
bash $E --root "kill $PID" >/dev/null 2>&1
