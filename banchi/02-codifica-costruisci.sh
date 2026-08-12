#!/bin/bash
#
# 02-codifica-costruisci.sh — costruisce il codificatore DA SOLO, e l'attrezzo
# con cui il banco lo punta.
#
#   bash banchi/02-codifica-costruisci.sh              costruisce
#   bash banchi/02-codifica-costruisci.sh dipendenze   dice che cosa manca
#
# Esce **0** se ha costruito, **1** se la compilazione e' fallita, **2** se non
# ha potuto nemmeno provare (dipendenze).  ⛔ Tre esiti, non due.
#
# ===========================================================================
# ⛔ PERCHE' NON SI USA `src/Makefile`
#
# Il 12 agosto 2026 quattro agenti scrivono quattro anelli della fase 2 in
# parallelo.  `src/Makefile` e `src/main.c` sono di tutti e di nessuno: chi ci
# scrive dentro sovrascrive il lavoro degli altri, e il sintomo arriverebbe a
# qualcun altro.  ⇒ Questo script compila **solo** `codificatore.c`, e le righe
# esatte per il Makefile e per `main.c` stanno nel rapporto
# `fasi/rapporti/P2-3-codifica.md`, da applicare quando i quattro anelli si
# ricuciono.
#
# ===========================================================================
# ⛔ LE DIPENDENZE, DICHIARATE
#
#   libavcodec-dev   >= 61   il codificatore, chiesto PER NOME (libx265/libsvtav1)
#   libavutil-dev    >= 59   i fotogrammi e i formati di pixel
#   libswscale-dev   >= 8    ⭐ NUOVA in questa sotto-fase: BGRx (quel che
#                            consegna la cattura di GNOME, `[M]` F2.2) →
#                            yuv420p10le.  `CODER.md` §4.1: di RGB→YUV esiste
#                            UNA implementazione standard, e scriverne una
#                            nostra sarebbe un componente da mantenere per
#                            sempre — per giunta piu' lenta di quella con le
#                            istruzioni vettoriali, su un cammino dove v1 aveva
#                            gia' misurato il collo di bottiglia (12,5 ms).
#
# Su Debian Trixie: `apt install libavcodec-dev libavutil-dev libswscale-dev`.
# ⚠ Tutti e tre dal pacchetto sorgente `ffmpeg` 7:7.1.5-0+deb13u1, cioe' la
#   STESSA versione dell'`ffmpeg` che il banco usa come lettore indipendente.
#
# ⛔ E NIENTE dal di fuori dei pacchetti: e' la lezione di `quiche`, scartata
#    anche perche' pretendeva una catena Rust fuori dai pacchetti
#    (`DECISIONI.md` §6.4).
#
# ⚠ Se `libswscale-dev` non e' installato e non si ha `root`, questo script sa
#   scaricarne l'archivio ufficiale di Trixie e scompattarlo in una cartella di
#   lavoro: `PRESTITO=1 bash banchi/02-codifica-costruisci.sh`.  ⛔ E' un
#   PRESTITO dichiarato, non una dipendenza nascosta — la libreria che si collega
#   resta quella di sistema (`libswscale.so.8`), si prendono solo le
#   intestazioni.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
SRC=$QUI/../src
LAV=${LAV_COSTRUZIONE:-/tmp/02-codifica-costruisci}
CC=${CC:-cc}
PRESTITO=${PRESTITO:-0}
LDFLAGS_PRESTITO=""

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

mkdir -p "$LAV" || { ko "non si crea $LAV"; exit 2; }

# ───────────────────────────────────────────────────────────────────────────
# Le tre dipendenze, chieste a `pkg-config` e non indovinate.
CFLAGS_AV=""
MANCA=""
for P in libavcodec libavutil libswscale; do
	if V=$(pkg-config --modversion "$P" 2>/dev/null); then
		ok "$P $V"
		CFLAGS_AV="$CFLAGS_AV $(pkg-config --cflags "$P")"
	else
		ko "manca $P (pacchetto ${P}-dev)"
		MANCA="$MANCA $P"
	fi
done

# ⚠ Il prestito delle sole intestazioni di libswscale, quando non si ha root.
if [ -n "$MANCA" ] && [ "$PRESTITO" = 1 ]; then
	inf "PRESTITO=1: scarico le intestazioni dai pacchetti ufficiali di Trixie"
	for P in $MANCA; do
		( cd "$LAV" && apt-get download "${P}-dev" ) > "$LAV/scarica.log" 2>&1 || {
			ko "non ho potuto scaricare ${P}-dev — vedi $LAV/scarica.log"; exit 2; }
		DEB=$(ls "$LAV"/${P}-dev_*.deb 2>/dev/null | head -1)
		[ -n "$DEB" ] || { ko "nessun archivio ${P}-dev"; exit 2; }
		dpkg -x "$DEB" "$LAV/prestito" || { ko "non si scompatta $DEB"; exit 2; }
		# ⛔ La libreria che si COLLEGA resta quella di sistema: si fabbrica solo
		#    il nome senza versione che il linker cerca (`-lswscale`).  ⚠ Se si
		#    collegasse quella dell'archivio, si costruirebbe contro una libreria
		#    che sulla macchina non gira — due versioni sotto la stessa etichetta.
		VERA=$(ls /usr/lib/"$(uname -m)"-linux-gnu/${P}.so.* 2>/dev/null | head -1)
		if [ -z "$VERA" ]; then
			ko "⛔ $P non e' installata nemmeno come libreria a runtime"; exit 2
		fi
		mkdir -p "$LAV/prestito/collega"
		ln -sf "$VERA" "$LAV/prestito/collega/${P}.so"
		ok "intestazioni di $P in prestito da $(basename "$DEB"); si collega $VERA"
	done
	CFLAGS_AV="$CFLAGS_AV -I$LAV/prestito/usr/include/$(uname -m)-linux-gnu -I$LAV/prestito/usr/include"
	LDFLAGS_PRESTITO="-L$LAV/prestito/collega"
	MANCA=""
fi

if [ -n "$MANCA" ]; then
	ko "⛔ non ho potuto nemmeno provare a compilare: manca$MANCA"
	inf "cura:  sudo apt install libavcodec-dev libavutil-dev libswscale-dev"
	inf "oppure senza root:  PRESTITO=1 bash banchi/02-codifica-costruisci.sh"
	exit 2
fi

if [ "${1:-}" = dipendenze ]; then
	ok "tutte e tre le dipendenze ci sono"
	exit 0
fi

# ───────────────────────────────────────────────────────────────────────────
# ⚠ `registro.c` entra perche' `codificatore.c` scrive nel registro invece che
#   in `stderr`: ogni ripiego e ogni degradazione **si dichiarano li'**
#   (`CODER.md` §6), e un registro sparso in venti `fprintf` non ha ne' istante
#   ne' area.
AVVERTIMENTI="-Wall -Wextra -Wno-unused-parameter"
CFLAGS_TUTTI="-O2 -g -std=gnu11 -D_GNU_SOURCE $AVVERTIMENTI $CFLAGS_AV"
LIBS="-lavcodec -lavutil -lswscale"

printf '\n\033[1m== compilo il codificatore\033[0m\n'
if ! $CC $CFLAGS_TUTTI -c -o "$LAV/codificatore.o" "$SRC/codificatore.c" 2> "$LAV/cc.log"; then
	ko "⛔ codificatore.c non compila"
	cat "$LAV/cc.log"
	exit 1
fi
if [ -s "$LAV/cc.log" ]; then
	# ⛔ Gli avvertimenti si stampano.  Un avvertimento che nessuno legge e' un
	#    difetto che aspetta.
	inf "avvertimenti del compilatore:"
	cat "$LAV/cc.log"
fi
ok "codificatore.o"

if ! $CC $CFLAGS_TUTTI -c -o "$LAV/registro.o" "$SRC/registro.c" 2>> "$LAV/cc.log"; then
	ko "⛔ registro.c non compila"; cat "$LAV/cc.log"; exit 1
fi
ok "registro.o"

printf '\n\033[1m== costruisco l'"'"'attrezzo con cui il banco punta sul prodotto\033[0m\n'
if ! $CC $CFLAGS_TUTTI -o "$QUI/02-codifica-prova" "$QUI/02-codifica-prova.c" \
	"$LAV/codificatore.o" "$LAV/registro.o" $LDFLAGS_PRESTITO $LIBS 2>> "$LAV/cc.log"; then
	ko "⛔ 02-codifica-prova non si e' costruito"
	cat "$LAV/cc.log"
	exit 1
fi
ok "banchi/02-codifica-prova"
inf "adesso:  CODIFICATORE=prodotto bash banchi/02-codifica-lancia.sh"
exit 0
