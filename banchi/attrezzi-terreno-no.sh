#!/bin/bash
# ⛔ IL CONTROLLO CHE DICE NO, per 01-b0-terreno.sh: si costruiscono i due
#    difetti per cui e' nato, e il terreno DEVE diventare rosso.
set -uo pipefail
E=/media/REMOTIX/enter.sh; D=/srv/src; F=/media/REMOTIX/src
ripulisci() {
  bash $E --root "python3 $D/01-b12-guasti.py --togli B5" >/dev/null 2>&1
  bash $E --root "mv -f $D/b2/ngtcp2/examples/rcp.h.via $D/b2/ngtcp2/examples/rcp.h" 2>/dev/null
  # ⛔ E SI RICOSTRUISCE — R12-A.6, e questo script ci e' cascato dentro il
  #    giorno in cui certificava il controllo che quella trappola cerca:
  #    `--togli` rimette il sorgente e lascia il binario com'era, quindi
  #    `rcp.c` resta PIU' NUOVO del binario.  ⭐ L'ha preso 01-b0-terreno.sh.
  bash $E --root "ninja -C $D/b2/ngtcp2/build bsslserver" >/dev/null 2>&1
  echo "== rimesso a posto E ricostruito"
}
trap ripulisci EXIT

echo "=== 1. un guasto di B12 lasciato addosso ==="
bash $E --root "python3 $D/01-b12-guasti.py --applica B5" >/dev/null 2>&1
bash $F/01-b0-terreno.sh innesto 2>&1 | grep -E "guasti di B12 in rcp.c|IL TERRENO|guai" | head -4
bash $E --root "python3 $D/01-b12-guasti.py --togli B5" >/dev/null 2>&1

echo
echo "=== 2. un pezzo dell'innesto che sparisce ==="
bash $E --root "mv $D/b2/ngtcp2/examples/rcp.h $D/b2/ngtcp2/examples/rcp.h.via"
bash $F/01-b0-terreno.sh innesto 2>&1 | grep -E "rcp.h|IL TERRENO|guai" | head -4
