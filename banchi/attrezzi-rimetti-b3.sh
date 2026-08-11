#!/bin/bash
set -uo pipefail
E=/media/REMOTIX/enter.sh; D=/srv/src
echo "== rimetto l'innesto RCP di B3"
bash $E --root "cd $D && python3 01-b3-rcp-innesta.py" 2>&1 | tail -4
echo "== e ricostruisco"
bash $E --root "ninja -C $D/b2/ngtcp2/build bsslserver" >/dev/null 2>&1 && echo "ricostruito" || echo "⛔ compilazione fallita"
echo "== verifica: rcp_ nel .cc"
bash $E --root "grep -c 'rcp_' $D/b2/ngtcp2/examples/http3_server_proto_codec.cc"
echo "== e i due innesti convivono? (streams_uni deve restare 19)"
bash $E --root "grep -n 'initial_max_streams_uni' $D/b2/ngtcp2/examples/server.cc | tail -3"
