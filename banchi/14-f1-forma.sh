#!/bin/bash
#
# 14-f1-forma.sh — builds and runs `14-f1-forma.c`: the encoded cursor theme
# and the dictionary (`src/forma.h`), without a desktop.
#
#   bash banchi/14-f1-forma.sh [themes-folder]      (default /usr/share/icons)
#
# ⛔ The expected values of the real theme (size and hotspot of "ew-resize" at
#    nominal size 24) are read HERE by a Python parser independent of
#    `forma.c`: the C bench compares them with what the module loaded.
# ⭐ And the two faults are prepared here: a copy of Adwaita with a corrupted
#    `index.theme`, and an empty themes folder.  A module that lied
#    (loaded all the same) gives RED.
#
# ⚠ It needs gcc, pkg-config, glib and the PipeWire headers (`spa/`), and
#   Adwaita in /usr/share/icons: they are on the laptop and in the four boxes.
set -uo pipefail

HERE=$(cd -- "$(dirname -- "$0")" && pwd)
SRC=$HERE/../src
THEMES=${1:-/usr/share/icons}
LAV=$(mktemp -d "${TMPDIR:-/tmp}/14-f1.XXXXXX")

read -r L A X Y < <(python3 - "$THEMES/Adwaita/cursors/ew-resize" <<'EOF'
import struct, sys
d = open(sys.argv[1], 'rb').read()
magic, head, _, entries = struct.unpack('<4I', d[:16])
assert magic == 0x72756358
toc = [struct.unpack('<3I', d[head + 12 * k:head + 12 * k + 12]) for k in range(entries)]
kind, gauge, pos = min((t for t in toc if t[0] == 0xfffd0002), key=lambda t: abs(t[1] - 24))
_, _, _, _, l, a, x, y, _ = struct.unpack('<9I', d[pos:pos + 36])
print(l, a, x, y)
EOF
) || { echo "⛔ the Python parser cannot read ew-resize in $THEMES/Adwaita"; exit 2; }

# fault G1: Adwaita with the corrupted index (and breeze_cursors absent)
mkdir -p "$LAV/faults" "$LAV/empty" "$LAV/mixed/breeze_cursors/cursors"
# T3b: real Adwaita + a FAKE breeze_cursors that has `size_hor` (with the arrow
# drawing, so one can tell if the module takes it)
ln -s "$THEMES/Adwaita" "$LAV/mixed/Adwaita"
printf '[Icon Theme]\nName=fake\n' > "$LAV/mixed/breeze_cursors/index.theme"
cp -L "$THEMES/Adwaita/cursors/default" "$LAV/mixed/breeze_cursors/cursors/size_hor"
cp -rL "$THEMES/Adwaita" "$LAV/faults/Adwaita" 2>/dev/null
printf '\x00\x13garbage that is not an index\n' > "$LAV/faults/Adwaita/index.theme"

gcc -O1 -g -Wall -Wextra -Wno-unused-parameter -D_GNU_SOURCE -I"$SRC" -o "$LAV/banco" \
	"$HERE/14-f1-forma.c" "$SRC/forma.c" "$SRC/cursore.c" "$SRC/registro.c" \
	$(pkg-config --cflags --libs glib-2.0 libpipewire-0.3) || exit 2

echo "expected by the Python parser: ew-resize ${L}x${A} hotspot ${X},${Y}"
"$LAV/banco" "$LAV" "$THEMES" "$L" "$A" "$X" "$Y" "$LAV/faults" "$LAV/empty" \
	"$LAV/mixed" 2> "$LAV/registro.txt"
OUTCOME=$?
echo "----- module log"
cat "$LAV/registro.txt"
echo "(working folder: $LAV)"
exit $OUTCOME
