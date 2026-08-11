#!/bin/bash
# Rifa' l'innesto B2 su server.cc col numero nuovo, e ricostruisce.
set -uo pipefail
E=/media/REMOTIX/enter.sh; D=/srv/src
echo "== prima:"; grep -n 'initial_max_streams_uni = ' $D/b2/ngtcp2/examples/server.cc 2>/dev/null || \
  bash $E --root "grep -n 'initial_max_streams_uni = ' $D/b2/ngtcp2/examples/server.cc"
bash $E --root "cd $D && python3 01-b2-ngtcp2-wt-innesta.py --togli" 2>&1 | tail -3
bash $E --root "cd $D && python3 01-b2-ngtcp2-wt-innesta.py" 2>&1 | tail -3
echo "== dopo:"
bash $E --root "grep -n 'initial_max_streams_uni' $D/b2/ngtcp2/examples/server.cc"
echo "== e si ricostruisce (R12-A.6)"
bash $E --root "ninja -C $D/b2/ngtcp2/build bsslserver" >/dev/null 2>&1 && echo "ricostruito" || echo "⛔ compilazione fallita"
