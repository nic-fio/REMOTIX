#!/bin/bash
# 15-ship.sh — carries the suite benches to the server, where the real browsers run.
#
#   bash benches/15-suite/15-ship.sh
#
# ⛔ The tests with the real browsers run ON THE SERVER as nicfio, from the tree
#    /media/REMOTIX/src/check (the same one 11-hook.sh uses for C21-C23):
#    all the .py/.sh/.html of benches/ are carried (no measurement folders),
#    benches/11-boxes, benches/15-suite, benches/19-android (the phone, phase 19 §5)
#    and fondamenta/strumenti.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
DEST=${REMOTIX_CHECK_DIR:-/media/REMOTIX/src/controllo}
HOST=${REMOTIX_HOST:-nicfio@192.168.0.2}
cd "$ROOT"
listing=$(
	ls benches/*.py benches/*.sh benches/*.html benches/*.js 2>/dev/null
	find benches/11-boxes benches/15-suite benches/19-android -type f ! -name '*.pyc' ! -path '*/__pycache__/*' \
		! -name '*registro*.jsonl'
	find fondamenta/strumenti -type f ! -name '*.pyc'
)
# ⭐ the commit the benches come from (and whether the tree has uncommitted changes)
version="$(git rev-parse --short HEAD)$(git diff --quiet HEAD -- benches src 2>/dev/null || echo '+modifiche')"
echo "$version" | ssh -o BatchMode=yes "$HOST" "mkdir -p $DEST && cat > $DEST/VERSIONE" 2>&1 | grep -v '^tput' || true
# shellcheck disable=SC2086
tar czf - $listing | ssh -o BatchMode=yes "$HOST" "mkdir -p $DEST && tar xzf - -C $DEST" 2>&1 \
	| grep -v '^tput' || true
echo "carried $(echo "$listing" | wc -l) files to $HOST:$DEST"
