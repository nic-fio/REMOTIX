#!/bin/bash
#
# 06-b41-tutti-i-controlli.sh — ⭐ i controlli positivi di TUTTI gli attrezzi
# di A4, in un colpo solo e senza toccare niente di vivo.
#
#   bash banchi/06-b41-tutti-i-controlli.sh
#
# ⛔ Non accende server, non apre sessioni, non tocca la GPU: gira sul
#    portatile in due secondi.  ⇒ Si lancia PRIMA di credere a qualunque
#    numero che questi attrezzi stampino (`LEZIONI.md` §1.2).
set -uo pipefail
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
GUAI=0

controlla() {
	printf '\n\033[1m== %s\033[0m\n' "$1"
	shift
	if "$@"; then
		printf '    \033[1;32mSUPERATO\033[0m\n'
	else
		printf '    \033[1;31mFALLITO\033[0m\n'
		GUAI=$((GUAI + 1))
	fi
}

controlla "06-b35-tempi.py — le latenze dal registro" \
	python3 "$QUI/06-b35-tempi.py" --controllo
controlla "06-b35-regola.py — la regola contro il metro sano" \
	python3 "$QUI/06-b35-regola.py" --controllo
controlla "06-b41-verdetto.py — il verdetto sotto contesa" \
	python3 "$QUI/06-b41-verdetto.py" --controllo
controlla "06-b41-guasto.py — l'innesto della cura tolta" \
	python3 "$QUI/06-b41-guasto.py" --controllo

printf '\n'
if [ "$GUAI" -eq 0 ]; then
	printf '\033[1;32m⭐ tutti e quattro i controlli positivi sono superati\033[0m\n'
	exit 0
fi
printf '\033[1;31m⛔ %s controlli FALLITI: non si crede a nessun numero\033[0m\n' "$GUAI"
exit 1
