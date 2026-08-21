#!/bin/bash
#
# 06-b40-palco-finto.sh — costruisce e lancia `06-b40-palco-finto.c`.
#
#   bash banchi/06-b40-palco-finto.sh [n]
#
#   uscita 0  i casi dichiarati sono verdi
#   uscita 1  ⛔ almeno uno no
#   uscita 2  l'ambiente non regge il banco — e si dice QUALE pezzo manca
#
# ⛔ GIRA SUL PORTATILE, e non serve la macchina di prova: il palco e' un
#    produttore PipeWire dentro il banco stesso.  ⚠ Serve pero' un **PipeWire
#    in ascolto** sulla sessione dell'utente: senza, `pw_context_connect()`
#    fallisce e il banco esce **2** invece di dire un numero falso.
set -uo pipefail

QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/.." && pwd)
LAVORO=${LAVORO:-/tmp/06-b40-palco}
CC=${CC:-gcc}

mkdir -p "$LAVORO" || exit 2

# ⛔ Le dipendenze si CHIEDONO, e la loro assenza e' una riga che dice il
#    pacchetto — non un errore di `gcc` lungo trenta righe.
for m in libpipewire-0.3 gio-2.0 libdrm; do
	pkg-config --exists "$m" || {
		printf '  ⛔ manca «%s»: il banco non si costruisce.\n' "$m"
		exit 2
	}
done
printf '  --  pipewire %s · glib %s\n' \
	"$(pkg-config --modversion libpipewire-0.3)" \
	"$(pkg-config --modversion gio-2.0)"
pgrep -x pipewire >/dev/null || {
	printf '  ⛔ nessun `pipewire` in ascolto per questo utente: il palco finto\n'
	printf '     non ha dove registrarsi, e un rosso qui non sarebbe del prodotto.\n'
	exit 2
}

$CC -O1 -g -std=gnu11 -D_GNU_SOURCE -Wall -Wextra -Wno-unused-parameter \
    -o "$LAVORO/palco-finto" \
    "$QUI/06-b40-palco-finto.c" \
    "$ALBERO/src/cattura.c" "$ALBERO/src/registro.c" "$ALBERO/src/cursore.c" \
    $(pkg-config --cflags --libs libpipewire-0.3 gio-2.0 libdrm) \
    || { printf '  ⛔ non compila\n'; exit 2; }

"$LAVORO/palco-finto" "${1:-}"
