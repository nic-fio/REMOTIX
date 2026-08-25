#!/bin/bash
#
# 06-b33-costruisci.sh — ⛔ GIRA DENTRO IL CONTENITORE.  Costruisce il testimone
# della sottofase 6.1 e lo depone nella cartella di lavoro.
#
#   printf '<parola>\n' | bash /media/REMOTIX/enter.sh --root \
#       'bash /srv/src/06-i-src/banchi/06-b33-costruisci.sh'
#
# ⛔ Esiste per la regola di casa «un file non ha livelli di virgolette»: un
#    `$(pkg-config …)` scritto dentro `ssh → enter.sh → bash -c` lo espande la
#    shell SBAGLIATA — quella dell'host, dove `pkg-config` non c'e'.
#
# ⛔ E il binario del testimone NON e' il prodotto: e' un cliente Wayland che
#    non tocca una riga di `src/`.  Si costruisce a parte apposta — cosi' un
#    guasto innestato nel prodotto non lo tocca, e lo strumento resta lo stesso
#    fra il giro sano e il giro guasto (`CODER.md` §3.3).
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
LAV=${LAV:-/srv/remotix/tmp/06-i}
XDG=${XDG:-/usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml}

mkdir -p "$LAV"
cd "$QUI" || exit 2

echo "== il protocollo xdg-shell"
[ -f "$XDG" ] || { echo "⛔ $XDG non c'e'"; exit 2; }
wayland-scanner client-header "$XDG" xdg-shell-client-protocol.h || exit 2
wayland-scanner private-code  "$XDG" xdg-shell-protocol.c || exit 2
echo "   fatti xdg-shell-client-protocol.h e xdg-shell-protocol.c"

echo
echo "== il testimone"
# ⛔ Si butta PRIMA di costruire: cosi' «c'e'» significa «e' di adesso», e non
#    «ce n'era uno di ieri» (`LEZIONI.md` §1.9 punto 8).
rm -f "$LAV/06-b33-testimone"
gcc -O1 -g -Wall -o "$LAV/06-b33-testimone" 06-b33-testimone.c xdg-shell-protocol.c \
	$(pkg-config --cflags --libs wayland-client) || exit 2
[ -x "$LAV/06-b33-testimone" ] || { echo "⛔ il testimone NON e' stato costruito"; exit 2; }
ls -la "$LAV/06-b33-testimone"

echo
echo "== la marca: che cosa c'e' DENTRO il binario"
# ⛔ Si guarda dentro il binario, non nel sorgente: fra i due c'e' una
#    compilazione, ed e' quella che si vuole verificare.  ⛔⛔ E NON con
#    `| grep -q`: con `pipefail` l'uscita anticipata di `grep -q` da' SIGPIPE a
#    `strings`, la pipeline esce 141 e l'`if` prende il ramo sbagliato.
R=$(strings "$LAV/06-b33-testimone" | grep -c 'RITELA')
echo "   «RITELA»: $R"
if [ "$R" -gt 0 ]; then
	echo "   ⭐ c'e' la riga che dice, DAL LATO CHE RICEVE, che la tela e' cambiata"
else
	echo "   ⛔ la riga RITELA non c'e': il testimone non saprebbe dire di essere"
	echo "      stato ridimensionato, e «non e' successo niente» e «non l'ho"
	echo "      visto» avrebbero lo stesso aspetto"
	exit 3
fi
exit 0
