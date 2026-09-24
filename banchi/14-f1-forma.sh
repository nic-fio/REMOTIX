#!/bin/bash
#
# 14-f1-forma.sh — costruisce e fa girare `14-f1-forma.c`: il tema codificato
# del cursore e il dizionario (`src/forma.h`), senza desktop.
#
#   bash banchi/14-f1-forma.sh [cartella-dei-temi]      (predefinita /usr/share/icons)
#
# ⛔ I valori attesi del tema reale (misura e punto attivo di «ew-resize» alla
#    misura nominale 24) li legge QUI un parser Python indipendente da
#    `forma.c`: il banco C li confronta con quel che il modulo ha caricato.
# ⭐ E i due guasti si preparano qui: una copia di Adwaita con `index.theme`
#    corrotto, e una cartella dei temi vuota.  Un modulo che mentisse
#    (caricasse lo stesso) fa ROSSO.
#
# ⚠ Vuole gcc, pkg-config, glib e le intestazioni di PipeWire (`spa/`), e
#   Adwaita in /usr/share/icons: ci sono sul portatile e nelle quattro scatole.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
SRC=$QUI/../src
TEMI=${1:-/usr/share/icons}
LAV=$(mktemp -d "${TMPDIR:-/tmp}/14-f1.XXXXXX")

read -r L A X Y < <(python3 - "$TEMI/Adwaita/cursors/ew-resize" <<'EOF'
import struct, sys
d = open(sys.argv[1], 'rb').read()
magia, testa, _, voci = struct.unpack('<4I', d[:16])
assert magia == 0x72756358
toc = [struct.unpack('<3I', d[testa + 12 * k:testa + 12 * k + 12]) for k in range(voci)]
tipo, misura, pos = min((t for t in toc if t[0] == 0xfffd0002), key=lambda t: abs(t[1] - 24))
_, _, _, _, l, a, x, y, _ = struct.unpack('<9I', d[pos:pos + 36])
print(l, a, x, y)
EOF
) || { echo "⛔ il parser Python non legge ew-resize in $TEMI/Adwaita"; exit 2; }

# il guasto G1: Adwaita con l'indice corrotto (e breeze_cursors assente)
mkdir -p "$LAV/guasti" "$LAV/vuota" "$LAV/misti/breeze_cursors/cursors"
# T3b: Adwaita vera + un breeze_cursors FINTO che ha `size_hor` (col disegno
# della freccia, cosi' si riconosce se il modulo lo prende)
ln -s "$TEMI/Adwaita" "$LAV/misti/Adwaita"
printf '[Icon Theme]\nName=finto\n' > "$LAV/misti/breeze_cursors/index.theme"
cp -L "$TEMI/Adwaita/cursors/default" "$LAV/misti/breeze_cursors/cursors/size_hor"
cp -rL "$TEMI/Adwaita" "$LAV/guasti/Adwaita" 2>/dev/null
printf '\x00\x13spazzatura non e un indice\n' > "$LAV/guasti/Adwaita/index.theme"

gcc -O1 -g -Wall -Wextra -Wno-unused-parameter -D_GNU_SOURCE -I"$SRC" -o "$LAV/banco" \
	"$QUI/14-f1-forma.c" "$SRC/forma.c" "$SRC/cursore.c" "$SRC/registro.c" \
	$(pkg-config --cflags --libs glib-2.0 libpipewire-0.3) || exit 2

echo "attesi dal parser Python: ew-resize ${L}x${A} punto ${X},${Y}"
"$LAV/banco" "$LAV" "$TEMI" "$L" "$A" "$X" "$Y" "$LAV/guasti" "$LAV/vuota" \
	"$LAV/misti" 2> "$LAV/registro.txt"
ESITO=$?
echo "----- registro del modulo"
cat "$LAV/registro.txt"
echo "(cartella di lavoro: $LAV)"
exit $ESITO
