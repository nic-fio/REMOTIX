#!/bin/bash
#
# 10-b88-costruisci.sh — costruisce `10-b88-flusso` attorno al CODIFICATORE DEL
# PRODOTTO, e a nient'altro.
#
#   bash banchi/10-b88-costruisci.sh              costruisce
#   bash banchi/10-b88-costruisci.sh dipendenze   dice che cosa manca
#
# Esce **0** se ha costruito, **1** se la compilazione e' fallita, **2** se non
# ha potuto nemmeno provare (dipendenze).  ⛔ Tre esiti, non due.
#
# ===========================================================================
# ⛔ PERCHE' NON SI USA `src/costruisci.sh`
#
# `costruisci.sh` costruisce il server intero — QUIC, WebTransport, PAM, la
# copia gemella di `rcp.c` (R12.3) — e per misurare il codificatore non serve
# niente di tutto quello.  ⚠ E ogni pezzo in piu' e' un modo in piu' di non
# compilare per una ragione che col codificatore non c'entra.
#
# ⇒ Qui si compilano **due** file del prodotto (`codificatore.c`, `registro.c`)
#   piu' il guscio del banco.  E' il modello di `02-codifica-costruisci.sh`, con
#   in piu' le librerie che l'accelerazione ha portato dentro dopo la fase 2:
#
#   libva, libva-drm   VA-API: il display, l'entrypoint, le superfici importate
#   gbm                ⭐ SOLO PER IL BANCO: i buffer che stanno gia' sulla GPU.
#                      Nel prodotto quel ruolo ce l'ha il compositore; qui non
#                      c'e' nessun compositore, e i fotogrammi sulla scheda
#                      qualcuno deve pur fabbricarli.
#   libdrm             `drm_fourcc.h`, cioe' i nomi dei formati
# ===========================================================================
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
SRC=$QUI/../src
LAV=${LAV_COSTRUZIONE:-/tmp/10-b88-costruisci}
CC=${CC:-cc}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

mkdir -p "$LAV" || { ko "non si crea $LAV"; exit 2; }

CFLAGS_AV=""
MANCA=""
for P in libavcodec libavutil libswscale libva libva-drm libdrm gbm; do
	if V=$(pkg-config --modversion "$P" 2>/dev/null); then
		ok "$P $V"
		CFLAGS_AV="$CFLAGS_AV $(pkg-config --cflags "$P")"
	else
		ko "manca $P"
		MANCA="$MANCA $P"
	fi
done

if [ -n "$MANCA" ]; then
	ko "⛔ non ho potuto nemmeno provare a compilare: manca$MANCA"
	exit 2
fi
[ "${1:-}" = dipendenze ] && { ok "ci sono tutte"; exit 0; }

AVVERTIMENTI="-Wall -Wextra -Wno-unused-parameter"
CFLAGS_TUTTI="-O2 -g -std=gnu11 -D_GNU_SOURCE $AVVERTIMENTI $CFLAGS_AV"
LIBS="-lavcodec -lavutil -lswscale -lva -lva-drm -lgbm"

printf '\n\033[1m== compilo i due file DEL PRODOTTO\033[0m\n'
for F in codificatore registro; do
	if ! $CC $CFLAGS_TUTTI -c -o "$LAV/$F.o" "$SRC/$F.c" 2> "$LAV/$F.log"; then
		ko "⛔ $F.c non compila"; cat "$LAV/$F.log"; exit 1
	fi
	# ⛔ Gli avvertimenti si stampano: uno che nessuno legge e' un difetto che aspetta.
	[ -s "$LAV/$F.log" ] && { inf "avvertimenti su $F.c:"; cat "$LAV/$F.log"; }
	ok "$F.o"
done

printf '\n\033[1m== costruisco il guscio del banco\033[0m\n'
if ! $CC $CFLAGS_TUTTI -o "$QUI/10-b88-flusso" "$QUI/10-b88-flusso.c" \
	"$LAV/codificatore.o" "$LAV/registro.o" $LIBS 2> "$LAV/flusso.log"; then
	ko "⛔ 10-b88-flusso non si e' costruito"; cat "$LAV/flusso.log"; exit 1
fi
[ -s "$LAV/flusso.log" ] && { inf "avvertimenti sul guscio:"; cat "$LAV/flusso.log"; }
ok "banchi/10-b88-flusso  (md5 $(md5sum "$QUI/10-b88-flusso" | cut -d' ' -f1))"
inf "md5 codificatore.c:   $(md5sum "$SRC/codificatore.c" | cut -d' ' -f1)"
exit 0
