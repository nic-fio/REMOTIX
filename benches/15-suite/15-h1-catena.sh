#!/bin/bash
# 15-h1-catena.sh — la sequenza di 15-h1-run.py da usare come HOOK di suite-ramo.sh (prodotto del ramo gia' nei box).
#   bash 15-h1-catena.sh prova|completo [--out CARTELLA-BASE]
#   prova     xfce, chrome+firefox, tutti i casi con d a 3 utenti, senza guasti (~25 min)
#   completo  xfce: tutti i casi a-f (d con 8 utenti), con i guasti; poi gnome, kde, lxqt: casi a,b,c,e,f
#             (d con 8 sessioni desktop e' pesante: solo su xfce, il piu' leggero); chrome+firefox ovunque (~2 h 30)
#   reset     solo il caso b (H-RESET) sui 4 desktop, chrome+firefox, con il guasto (~20 min)
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
prova|completo|reset) ;;
*) echo "uso: bash 15-h1-catena.sh prova|completo|reset [--out BASE]  (vedi --help)"; exit 2 ;;
esac
mkdir -p "$BASE"
worst=0; CH=""; PARALLELE=""
# Pulizia SEMPRE (uscita, SIGTERM): toglie le tabelle nft del banco (inet remotix_g7_861x) e ferma il secondo server dei 4 box.
pulizia() {
	trap - EXIT TERM INT HUP
	if [ -n "$CH" ] && kill -0 "$CH" 2>/dev/null; then kill -TERM "$CH" 2>/dev/null; wait "$CH" 2>/dev/null; fi
	local q; for q in $PARALLELE; do kill -TERM "$q" 2>/dev/null; done; for q in $PARALLELE; do wait "$q" 2>/dev/null; done
	local pw d p
	pw=${REMOTIX_SUDO_PASSWORD:-$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh" 2>/dev/null)}
	for p in 8611 8612 8613 8614; do
		printf '%s\n' "$pw" | sudo -S -p '' /usr/sbin/nft delete table inet remotix_g7_$p >/dev/null 2>&1
	done
	for d in gnome kde xfce lxqt; do bash "$HERE/15-g7-server.sh" stop "$d" >/dev/null 2>&1; done
	# ⛔ The test users of the sessions (c<N>u<N>, c<N>bu<N>): H-RESET kills the server under a live session and
	#    its user can stay behind; 30-perf's precheck then finds the box «not empty» (25 Oct 2026, xfce c15114u620).
	for d in gnome kde xfce lxqt; do
		printf '%s\n' "$pw" | sudo -S -p '' podman exec "rete11-$d" sh -c \
			'for u in $(getent passwd | cut -d: -f1 | grep -E "^c[0-9]+b?u[0-9]+$"); do
				loginctl terminate-user "$u" 2>/dev/null; sleep 1; userdel -r "$u" 2>/dev/null; echo "   tolto $u"; done' 2>/dev/null
	done
}
trap pulizia EXIT
trap 'exit 143' TERM INT HUP
note() { case $1 in 1) worst=1 ;; 0) ;; *) [ "$worst" = 1 ] || worst=$1 ;; esac; }
corsa() {   # corsa <desktop> [opzioni di 15-h1-run.py]
	local d=$1; shift
	echo "=== $(date -u +%T) corsa $d $*"
	python3 "$RUN" --box "$d" --browser chrome,firefox --out "$BASE/$d" "$@" &
	CH=$!
	wait "$CH"
	local rc=$?
	CH=""
	echo "=== $(date -u +%T) corsa $d: rc=$rc ($BASE/$d/riepilogo.txt)"
	note $rc
	return $rc   # for the parallel runs: their note is in a subshell, the caller notes the rc again
}
if [ "$MODO" = prova ]; then
	corsa xfce --prova
elif [ "$MODO" = reset ]; then
	for d in xfce gnome kde lxqt; do corsa "$d" --case b; done
else
	corsa xfce
	# ⭐ gnome, kde, lxqt IN PARALLEL (25 Oct 2026): each desktop has its own server port (861x), its own nft table,
	#   its own labwc and its own debug ports, as in 15-round.py; xfce goes first ALONE because case d opens 8 sessions.
	#   H1_SERIE=1 runs them one after the other, as before.
	if [ "${H1_SERIE:-0}" = 1 ]; then
		for d in gnome kde lxqt; do corsa "$d" --case a,b,c,e,f; done
	else
		for d in gnome kde lxqt; do
			corsa "$d" --case a,b,c,e,f > "$BASE/corsa-$d.txt" 2>&1 &
			PARALLELE="$PARALLELE $!"
		done
		for q in $PARALLELE; do wait "$q"; note $?; done
		PARALLELE=""
		cat "$BASE"/corsa-gnome.txt "$BASE"/corsa-kde.txt "$BASE"/corsa-lxqt.txt
	fi
fi
echo "=== FINE (rc=$worst)"
exit $worst
