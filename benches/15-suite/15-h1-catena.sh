#!/bin/bash
# 15-h1-catena.sh — la sequenza di 15-h1-run.py da usare come HOOK di suite-ramo.sh (prodotto del ramo gia' nei box).
#   bash 15-h1-catena.sh prova|completo [--out CARTELLA-BASE]
#   prova     xfce, chrome+firefox, tutti i casi con d a 3 utenti, senza guasti (~25 min)
#   completo  xfce: tutti i casi a-f (d con 8 utenti), con i guasti; poi gnome, kde, lxqt: casi a,b,c,e,f
#             (d con 8 sessioni desktop e' pesante: solo su xfce, il piu' leggero); chrome+firefox ovunque (~2 h 30)
#   -h|--help questo testo.
# Uscita: 1 se qualche corsa ha dato FAIL, altrimenti 3 se qualcuna BLOCKED, altrimenti 0 (2 = uso/preflight).
# I risultati sono in <base>/<desktop>/riepilogo.txt; la riga «RISULTATO» e' l'ultima di ognuno.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
RUN=$HERE/15-h1-run.py
MODO=${1:-}; shift || true
BASE=/media/REMOTIX-15/misure/h1-$(date +%Y%m%d-%H%M%S)
while [ $# -gt 0 ]; do
	case $1 in
	--out) BASE=${2:?--out vuole una cartella}; shift 2 ;;
	-h|--help) sed -n '2,/^set -uo/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 0 ;;
	*) echo "argomento sconosciuto: $1"; exit 2 ;;
	esac
done
case $MODO in
-h|--help) sed -n '2,/^set -uo/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 0 ;;
prova|completo) ;;
*) echo "uso: bash 15-h1-catena.sh prova|completo [--out BASE]  (vedi --help)"; exit 2 ;;
esac
mkdir -p "$BASE"
worst=0
note() { case $1 in 1) worst=1 ;; 0) ;; *) [ "$worst" = 1 ] || worst=$1 ;; esac; }
corsa() {   # corsa <desktop> [opzioni di 15-h1-run.py]
	local d=$1; shift
	echo "=== $(date -u +%T) corsa $d $*"
	python3 "$RUN" --box "$d" --browser chrome,firefox --out "$BASE/$d" "$@"
	local rc=$?
	echo "=== $(date -u +%T) corsa $d: rc=$rc ($BASE/$d/riepilogo.txt)"
	note $rc
}
if [ "$MODO" = prova ]; then
	corsa xfce --prova
else
	corsa xfce
	for d in gnome kde lxqt; do corsa "$d" --case a,b,c,e,f; done
fi
echo "=== FINE (rc=$worst)"
exit $worst
