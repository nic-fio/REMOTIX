#!/bin/bash
# 15-porta.sh — porta i banchi della suite sul server, dove girano i browser veri.
#
#   bash banchi/15-suite/15-porta.sh
#
# ⛔ Le prove coi browser veri girano SUL SERVER come nicfio, dall'albero
#    /media/REMOTIX/src/controllo (lo stesso che usa 11-gancio.sh per C21-C23):
#    si portano tutti i .py/.sh/.html di banchi/ (niente cartelle di misure),
#    banchi/11-scatole, banchi/15-suite e fondamenta/strumenti.
set -euo pipefail
RADICE=$(cd "$(dirname "$0")/../.." && pwd)
DEST=${REMOTIX_CONTROLLO:-/media/REMOTIX/src/controllo}
HOST=${REMOTIX_HOST:-nicfio@192.168.0.2}
cd "$RADICE"
elenco=$(
	ls banchi/*.py banchi/*.sh banchi/*.html banchi/*.js 2>/dev/null
	find banchi/11-scatole banchi/15-suite -type f ! -name '*.pyc' ! -path '*/__pycache__/*' \
		! -name '*registro*.jsonl'
	find fondamenta/strumenti -type f ! -name '*.pyc'
)
# ⭐ il commit da cui vengono i banchi (e se l'albero ha modifiche non committate)
versione="$(git rev-parse --short HEAD)$(git diff --quiet HEAD -- banchi src 2>/dev/null || echo '+modifiche')"
echo "$versione" | ssh -o BatchMode=yes "$HOST" "mkdir -p $DEST && cat > $DEST/VERSIONE" 2>&1 | grep -v '^tput' || true
# shellcheck disable=SC2086
tar czf - $elenco | ssh -o BatchMode=yes "$HOST" "mkdir -p $DEST && tar xzf - -C $DEST" 2>&1 \
	| grep -v '^tput' || true
echo "portati $(echo "$elenco" | wc -l) file in $HOST:$DEST"
