#!/bin/bash
#
# 04-b20-costruisci.sh — ⛔ GIRA DENTRO IL CONTENITORE.  Costruisce il prodotto
# dell'albero di A1 e il programma minimo che chiama `sessione_assicura()`.
#
# ⛔ Esiste per la regola di casa «un file non ha livelli di virgolette»: un
#    `$(pkg-config …)` scritto dentro `ssh → enter.sh → bash -c` lo espande la
#    shell SBAGLIATA — quella dell'host, dove `pkg-config` non c'e' — e il
#    sintomo («command not found») accusa il contenitore di una cosa che non ha
#    fatto.  `[M]` 14 agosto 2026, primo giro di questo banco.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
ALBERO=$(cd -- "$QUI/.." && pwd)
LAV=${LAV:-/srv/remotix/tmp/04-b20}

mkdir -p "$LAV"

echo "== il prodotto"
# ⛔ `costruisci.sh` butta il binario vecchio PRIMA di costruire: cosi' «c'e'»
#    significa «e' di adesso», e non «ce n'era uno di ieri» (`LEZIONI.md` §1.9).
bash "$ALBERO/src/costruisci.sh" 2>&1 | tail -20
[ -x "$ALBERO/src/remotix" ] || { echo "⛔ il prodotto NON e' stato costruito"; exit 2; }
ls -la "$ALBERO/src/remotix"

echo
echo "== il programma minimo (CODER.md §3.6): chiama sessione_assicura() e basta"
rm -f "$LAV/04-b20-nasci"
gcc -O2 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter -D_GNU_SOURCE \
    $(pkg-config --cflags gio-2.0) -I"$ALBERO/src" -o "$LAV/04-b20-nasci" \
    "$QUI/04-b20-nasci.c" "$ALBERO/src/sessione.c" "$ALBERO/src/registro.c" \
    $(pkg-config --libs gio-2.0) || { echo "⛔ il programma minimo non compila"; exit 2; }
ls -la "$LAV/04-b20-nasci"

echo
echo "== la marca: che cosa chiede il drop-in che questo binario scriverebbe"
# ⛔ Si guarda DENTRO il binario, non nel sorgente: fra i due c'e' una
#    compilazione, ed e' proprio quella che si vuole verificare.
# ⛔⛔ E NON con `| grep -q`: `set -o pipefail` piu' l'uscita anticipata di
#     `grep -q` danno **SIGPIPE a `strings`**, la pipeline esce 141, e il `if`
#     prende il ramo sbagliato.  `[M]` 14 agosto 2026, primo giro: questa riga
#     ha scritto «e' il prodotto CURATO» sopra un binario che chiedeva ancora
#     `--virtual-monitor`.  ⛔ Ha sbagliato nella direzione che NON si vede —
#     una marca che assolve — ed e' la ragione per cui adesso si conta.
QUANTE=$(strings "$LAV/04-b20-nasci" | grep -c -- '--virtual-monitor %ux%u')
if [ "$QUANTE" -gt 0 ]; then
	echo "   ⛔ il binario chiede ancora «--virtual-monitor»: e' il PRODOTTO COM'E'"
else
	echo "   ⭐ il binario NON chiede «--virtual-monitor»: e' il prodotto CURATO"
fi
strings "$LAV/04-b20-nasci" | grep -E 'ExecStart=%s|--headless' | sed 's/^/      /'
exit 0
