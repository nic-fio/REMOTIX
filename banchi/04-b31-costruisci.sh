#!/bin/bash
#
# 04-b31-costruisci.sh — ⛔ GIRA DENTRO IL CONTENITORE.  Costruisce il prodotto
# dell'albero di O1.
#
# ⛔ Esiste per la regola di casa «un file non ha livelli di virgolette»: un
#    `$(pkg-config …)` scritto dentro `ssh → enter.sh → bash -c` lo espande la
#    shell SBAGLIATA — quella dell'host, dove `pkg-config` non c'e'.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
ALBERO=$(cd -- "$QUI/.." && pwd)
LAV=${LAV:-/srv/remotix/tmp/04-b31}

mkdir -p "$LAV" "$LAV/cert"

echo "== il prodotto"
# ⛔ `costruisci.sh` butta il binario vecchio PRIMA di costruire: cosi' «c'e'»
#    significa «e' di adesso», e non «ce n'era uno di ieri» (`LEZIONI.md` §1.9).
bash "$ALBERO/src/costruisci.sh" 2>&1 | tail -25
[ -x "$ALBERO/src/remotix" ] || { echo "⛔ il prodotto NON e' stato costruito"; exit 2; }
ls -la "$ALBERO/src/remotix"

echo
echo "== la marca: che cosa c'e' DENTRO il binario"
# ⛔ Si guarda dentro il binario, non nel sorgente: fra i due c'e' una
#    compilazione, ed e' proprio quella che si vuole verificare.
# ⛔⛔ E NON con `| grep -q`: `set -o pipefail` piu' l'uscita anticipata di
#     `grep -q` danno SIGPIPE a `strings`, la pipeline esce 141, e il `if`
#     prende il ramo sbagliato (difetto pagato da A1 il 14 agosto 2026).
RIAVVIA=$(strings "$ALBERO/src/remotix" | grep -c 'RIAVVIO LA CATTURA')
SENZA=$(strings "$ALBERO/src/remotix" | grep -c 'SENZA PALCO')
echo "   «RIAVVIO LA CATTURA»: $RIAVVIA   «SENZA PALCO»: $SENZA"
if [ "$RIAVVIA" -gt 0 ] || [ "$SENZA" -gt 0 ]; then
	echo "   ⭐ e' il prodotto CURATO da O1"
else
	echo "   ⛔ e' il PRODOTTO COM'E' (senza la cura di O1) — e va bene, se e' il giro rosso"
fi
exit 0
