#!/usr/bin/env bash
# ===========================================================================
# 09-b79-terreno — the ground of the bench OF THE TWO PAIRED CURES (agent NR4)
#
#   port 7940 · user `provanr4` (uid 1040) · tree /media/REMOTIX/src/09nr4-src
#   work /media/REMOTIX/tmp/09nr4 · unit remotix-7940
#
# ⛔ IT DOES NOT REWRITE `07-b64-terreno.sh`: it passes it MY environment and calls it.
#    It is modelled line by line on `09-b76-terreno.sh`, with **one** difference,
#    and the difference is the reason this file exists:
#
# ⛔⭐ THE SOURCES ARE TAKEN FROM THE WORKING TREE, NOT FROM `git archive HEAD`.
#     `09-b76-terreno.sh` takes HEAD on purpose, because on 23 August two other
#     agents were working on `src/` and sending their folder in the middle of a
#     change would have meant measuring on a binary that nobody had
#     decided to send.
#     ⭐ Now those agents have finished, and HEAD is **old**: it carries neither
#       `--sgombra-soglia-ms` nor `--niente-ritmo-adattivo` — that is, the two things
#       this bench exists to measure — nor the counters `dgram_persi` /
#       `dgram_falsi` and the `rete-quic` lines with `cwnd`, `srtt_us` and `giudizio=`.
#     ⇒ Here the working tree is sent, and its identity is DECLARED with
#       the md5 of the sources and of the binary produced: a folder name is
#       an intention, the md5 is a fact.
#
# ⛔ And the tar must also carry `banchi/rcp`: `src/costruisci.sh` compares
#    `rcp.c`/`rcp.h`/`autenticazione.c` with the twin copy (finding R12.3), and
#    without that folder the build FAILS.
#
# ⛔ `banchi/01-b4-validatore.py` is carried too: it is the REFEREE of the
#    §11.1 format, and the trace reader of `09-b70-ritmo.py` looks for it inside
#    the tree.  `07-b64-terreno.sh porta` does not send it.
#
# ⛔ `enp7s0` is not touched: no network is touched here, but the server is born
#    on 7940 and 7900/7910/7920/7930/7931/7932 are not mine.
#
# Usage (from the laptop):
#     bash banchi/09-b79-terreno.sh porta      # tar of the working tree + build
#     bash banchi/09-b79-terreno.sh utente
#     bash banchi/09-b79-terreno.sh accendi    # OPZIONI_SERVER='...' for the cures
#     bash banchi/09-b79-terreno.sh stato
#     bash banchi/09-b79-terreno.sh spegni
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-7940}
export UTENTE=${UTENTE:-provanr4}
export UID_B=${UID_B:-1040}
export PAROLA_UTENTE=${PAROLA_UTENTE:-nr4-due-cure-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/09nr4-src}
export LAV=${LAV:-/media/REMOTIX/tmp/09nr4}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/09nr4-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/09nr4}
export UNITA=${UNITA:-remotix-$PORTA}

QUI=$(cd "$(dirname "$0")/.." && pwd)
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

PASSO=${1:-stato}
case "$PASSO" in
porta)
	log "1 · The sources OF THE WORKING TREE in $ALBERO"
	printf '    --  HEAD = %s (⚠ and it is NOT what I send)\n' \
		"$(cd "$QUI" && git rev-parse --short HEAD)"
	inf "local md5 webtransport.c: $(md5sum "$QUI/src/webtransport.c" | cut -d' ' -f1)"
	inf "local md5 rcp.c:          $(md5sum "$QUI/src/rcp.c" | cut -d' ' -f1)"
	# ⛔ `banchi/rcp` is there or `costruisci.sh` fails on the twin comparison.
	tar -C "$QUI" --exclude='src/remotix' --exclude='src/*.o' -cf - \
		src banchi/rcp \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/01-b4-validatore.py \
		banchi/attrezzi-gruppi-scheda.sh banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py | \
		gzip | ssh -o BatchMode=yes "$MACCHINA" \
		"mkdir -p $ALBERO && tar -C $ALBERO -xzf -" || {
		ko "⛔ the sources did not arrive"; exit 2; }
	ok "sources in $ALBERO"

	log "2 · Building inside the container on the test machine"
	if ! ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
		  bash $DENTRO_ALB/src/costruisci.sh 2>&1 | tail -20'"; then
		ko "⛔ the build failed: I do NOT start anything"
		exit 2
	fi
	ok "built"

	# ⛔⭐ AND THE BINARY I MEASURE IS THE ONE I THINK — the md5 is declared, and we
	#     check that it REALLY carries the two options of the phase.  An old
	#     binary would greet `--sgombra-soglia-ms` with an error, and an error
	#     at startup looks the same as a server that does not start.
	log "3 · ⛔ WHAT I BUILT — md5 and the two options, read from the binary"
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \"
		 echo md5 binary:       \\\$(md5sum $ALBERO/src/remotix | cut -d' ' -f1)
		 echo md5 webtransport: \\\$(md5sum $ALBERO/src/webtransport.c | cut -d' ' -f1)
		 for o in sgombra-soglia-ms niente-ritmo-adattivo; do
		   if grep -qa -- --\\\$o $ALBERO/src/remotix; then
		     echo \\\"option --\\\$o: ⭐ PRESENT in the binary\\\"
		   else
		     echo \\\"option --\\\$o: ⛔ ABSENT\\\"; fi
		 done\"" || { ko "I could not read the binary back"; exit 2; }
	exit 0 ;;
*)
	# ⛔ Everything else is `07-b64-terreno.sh`, with MY environment exported:
	#    not one line of it is rewritten.  ⭐ And `OPZIONI_SERVER` passes through there up to
	#    the server's command line: it is the only place where the two cures
	#    are turned on.
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
esac
