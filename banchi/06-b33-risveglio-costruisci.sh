#!/bin/bash
#
# 06-b33-risveglio-costruisci.sh — ⛔ GIRA DENTRO IL CONTENITORE.  Costruisce
# l'iniettore di §7.1 (la seconda porta del clic che muore) e lo depone nella
# cartella di lavoro.
#
#   printf '<parola>\n' | bash /media/REMOTIX/enter.sh --root \
#       'bash /srv/src/06-i-src/banchi/06-b33-risveglio-costruisci.sh'
#
# ⛔ Esiste per la regola di casa «un file non ha livelli di virgolette»: un
#    `$(pkg-config …)` scritto dentro `ssh → enter.sh → bash -c` lo espande la
#    shell SBAGLIATA.
#
# ⛔⛔ E QUI IL BINARIO **E'** IL PRODOTTO, al contrario del testimone.
#      `06-b33-costruisci.sh` dice, del testimone, che *«non tocca una riga di
#      `src/`, cosi' un guasto innestato nel prodotto non lo tocca»*.  Qui e'
#      il rovescio ed e' voluto: l'imputato e' `cattura_risveglia()`, e un
#      guasto innestato in `src/cattura.c` **deve** cambiare questo binario — o
#      il controllo positivo non controllerebbe niente.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
SRC=${SRC:-$QUI/../src}
LAV=${LAV:-/srv/remotix/tmp/06-i}
USCITA=$LAV/06-b33-risveglio

mkdir -p "$LAV"
cd "$QUI" || exit 2

# ⛔ Si butta PRIMA di costruire: cosi' «c'e'» significa «e' di adesso», e non
#    «ce n'era uno di ieri» (`LEZIONI.md` §1.9 punto 8).
rm -f "$USCITA"

CFLAGS=$(pkg-config --cflags glib-2.0 gio-2.0 libpipewire-0.3 libdrm libei-1.0 xkbcommon) || exit 2
LIBS=$(pkg-config --libs glib-2.0 gio-2.0 libpipewire-0.3 libei-1.0 xkbcommon) || exit 2

echo "== l'iniettore del risveglio"
# shellcheck disable=SC2086
gcc -O1 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter -D_GNU_SOURCE \
	-I"$SRC" $CFLAGS \
	-o "$USCITA" \
	06-b33-risveglio.c \
	"$SRC/cattura.c" "$SRC/input.c" "$SRC/mutter.c" "$SRC/tastiera.c" "$SRC/registro.c" \
	"$SRC/cursore.c" \
	$LIBS -lm || exit 2

[ -x "$USCITA" ] || { echo "⛔ l'iniettore NON e' stato costruito"; exit 3; }
ls -la "$USCITA"

echo
echo "== la marca: che cosa c'e' DENTRO il binario"
# ⛔ Si guarda dentro il binario, non nel sorgente: fra i due c'e' una
#    compilazione, ed e' quella che si vuole verificare.  ⛔⛔ E NON con
#    `| grep -q`: con `pipefail` l'uscita anticipata di `grep -q` da' SIGPIPE a
#    `strings`, la pipeline esce 141 e l'`if` prende il ramo sbagliato.
R=$(strings "$USCITA" | grep -c 'flusso RIAVVIATO alla stessa misura')
echo "   la riga di «cattura_risveglia»: $R"
if [ "$R" -gt 0 ]; then
	echo "   ⭐ dentro c'e' la funzione del PRODOTTO, non una sua imitazione"
else
	echo '   ⛔ la riga di `cattura_risveglia()` non ci sta: questo binario NON'
	echo "      contiene la funzione sotto prova — ogni misura sarebbe di"
	echo "      un'altra cosa"
	exit 3
fi
O=$(strings "$USCITA" | grep -c 'erano PREMUTI sul dispositivo che il compositore ha appena tolto')
echo "   la riga degli ORFANI di src/input.c: $O"
[ "$O" -gt 0 ] || { echo "   ⛔ manca: non e' collegato l'input del prodotto"; exit 3; }
exit 0
