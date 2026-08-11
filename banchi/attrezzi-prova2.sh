#!/bin/bash
# ⛔ Il secondo utente si AUTENTICA davvero?  E la parola non si stampa mai.
set -uo pipefail
E=/media/REMOTIX/enter.sh; D=/srv/src
P2=$(sed -n 's/^prova2:[[:space:]]*//p' /media/REMOTIX/credenziali-banchi | head -1)
[ -n "$P2" ] || { echo "⛔ nessuna parola per prova2"; exit 2; }
bash $E --root "nohup env LD_LIBRARY_PATH=$D/b2/ngtcp2/build/lib $D/b2/ngtcp2/build/examples/bsslserver --timeout=120s 192.168.0.2 7447 /media/REMOTIX/b2-certificati/sessione.key /media/REMOTIX/b2-certificati/sessione.pem < /dev/null > $D/p2.log 2>&1 & echo \$! > $D/p2.pid"
sleep 2
PID=$(cat /media/REMOTIX/src/p2.pid)
echo "== prova2 (parola generata, non stampata)"
bash $E --root "python3 -u $D/01-b3-cliente.py --indirizzo 192.168.0.2 --porta 7447 --utente prova2 --parola '$P2' --registra $D/p2.rcpreg" 2>&1 | grep -E "AMMESSO|RESPINTO|SESSIONE|RuntimeError|ECCOMI" | sed "s/$P2/<NON SI STAMPA>/g"
echo "uscita=$?"
echo "== e il controllo che dice NO: parola sbagliata"
bash $E --root "python3 -u $D/01-b3-cliente.py --indirizzo 192.168.0.2 --porta 7447 --utente prova2 --parola questa-non-e-la-sua --registra $D/p2b.rcpreg" 2>&1 | grep -E "AMMESSO|RESPINTO|RuntimeError" | head -3
bash $E --root "kill $PID" >/dev/null 2>&1
