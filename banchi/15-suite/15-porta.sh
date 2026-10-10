#!/bin/bash
# 15-porta.sh — carries the suite benches to the server, where the real browsers run.
#
#   bash banchi/15-suite/15-porta.sh
#
# ⛔ The tests with the real browsers run ON THE SERVER as nicfio, from the tree
#    /media/REMOTIX/src/controllo (the same one 11-gancio.sh uses for C21-C23):
#    all the .py/.sh/.html of banchi/ are carried (no measurement folders),
#    banchi/11-scatole, banchi/15-suite, banchi/19-android (the phone, phase 19 §5)
#    and fondamenta/strumenti.
set -euo pipefail
RADICE=$(cd "$(dirname "$0")/../.." && pwd)
DEST=${REMOTIX_CONTROLLO:-/media/REMOTIX/src/controllo}
HOST=${REMOTIX_HOST:-nicfio@192.168.0.2}
cd "$RADICE"
elenco=$(
	ls banchi/*.py banchi/*.sh banchi/*.html banchi/*.js 2>/dev/null
	find banchi/11-scatole banchi/15-suite banchi/19-android -type f ! -name '*.pyc' ! -path '*/__pycache__/*' \
		! -name '*registro*.jsonl'
	find fondamenta/strumenti -type f ! -name '*.pyc'
)
# ⭐ the commit the benches come from (and whether the tree has uncommitted changes)
versione="$(git rev-parse --short HEAD)$(git diff --quiet HEAD -- banchi src 2>/dev/null || echo '+modifiche')"
echo "$versione" | ssh -o BatchMode=yes "$HOST" "mkdir -p $DEST && cat > $DEST/VERSIONE" 2>&1 | grep -v '^tput' || true
# shellcheck disable=SC2086
tar czf - $elenco | ssh -o BatchMode=yes "$HOST" "mkdir -p $DEST && tar xzf - -C $DEST" 2>&1 \
	| grep -v '^tput' || true
echo "carried $(echo "$elenco" | wc -l) files to $HOST:$DEST"
