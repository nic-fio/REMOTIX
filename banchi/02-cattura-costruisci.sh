#!/bin/bash
#
# 02-cattura-costruisci.sh — ⛔ GIRA SUL SERVER (NIC-OS), fuori dal contenitore.
# Costruisce il PRODOTTO della sotto-fase F2.2 (`src/cattura.c`, `src/mutter.c`)
# dentro il produttore del banco che lo mette alla prova.
#
#   bash /media/REMOTIX/src/02-cattura-costruisci.sh          costruisce
#   bash /media/REMOTIX/src/02-cattura-costruisci.sh guarda   dice e basta
#
# ===========================================================================
# ⛔ PERCHE' NON SI USA IL `Makefile` DEL PRODOTTO
#
# `src/Makefile` costruisce **un binario solo** — il server — e in fase 2 il
# server non chiama ancora la cattura: le righe che ce la metteranno stanno nel
# rapporto `P2-2-cattura.md`, e le innesta il coordinatore.  ⛔ Quattro agenti
# scrivono gli altri anelli in questo momento, e due che toccassero lo stesso
# `Makefile` si cancellerebbero a vicenda.
#
# ⇒ Questo file costruisce **gli stessi sorgenti** con **le stesse opzioni** del
#   `Makefile` (`-std=gnu11 -D_GNU_SOURCE -Wall -Wextra`), piu' le tre librerie
#   che la cattura porta con se'.  Chi innestera' le righe nel `Makefile` non
#   scoprira' che il codice non compila: qui e' gia' compilato con le sue regole.
#
# ===========================================================================
# ⛔ MAI UNA REDIREZIONE **ATTORNO** A `enter.sh`
#
# La richiesta di parola d'ordine di `sudo` va sullo stderr, e una redirezione
# la mangia: il comando resta appeso per sempre, in silenzio.  Dentro le
# virgolette si', attorno no.  `fasi/00-ambiente.md` B3.3, pagata **cinque**
# volte — e la sesta l'ho evitata scrivendola qui invece di ricordarmela.
#
# ===========================================================================
# ⛔ E SI GUARDA L'ESITO DEL COMPILATORE, NON LA PRESENZA DEL BINARIO DOPO
#
# `LEZIONI.md` §1.9: un binario di due ore prima risponde «esisto» come uno di
# adesso.  Qui si legge lo stato d'uscita di `gcc`, e in piu' si pretende che il
# binario sia PIU' NUOVO di tutti e quattro i sorgenti.
#
set -uo pipefail

QUI=${QUI:-/media/REMOTIX/tmp/02-cattura}
SRC=${SRC:-/media/REMOTIX/src}
PRODOTTO=${PRODOTTO:-$SRC/remotix}          # l'albero del prodotto, visto dall'host
DENTRO_SRC=${DENTRO_SRC:-/srv/src}          # lo stesso, visto dal contenitore
DENTRO_QUI=${DENTRO_QUI:-/srv/remotix/tmp/02-cattura}
BINARIO=$QUI/02-cattura-prodotto
REGISTRO=$QUI/costruzione-prodotto.log

# ⛔ La porta di questo agente e' la 7512, e qui non si apre nessuna porta.  La
#    riga esiste lo stesso: un banco che non nomina la propria porta e' un banco
#    che un giorno ne prende una d'altri.  Sulla 7448 e sulla 7501 girano due
#    server voluti, e restano accese.
PORTA_DI_QUESTO_BANCO=7512

SORGENTI_PRODOTTO="cattura.c mutter.c registro.c"
SORGENTE_BANCO=02-cattura-prodotto.c

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

log "0. I sorgenti, dichiarati (B0.1: si dichiara E si verifica)"
mancano=0
for f in $SORGENTI_PRODOTTO cattura.h mutter.h registro.h; do
	if [ -r "$PRODOTTO/$f" ]; then
		ok "$PRODOTTO/$f  ($(md5sum < "$PRODOTTO/$f" | cut -c1-12))"
	else
		ko "⛔ manca $PRODOTTO/$f"
		mancano=$((mancano + 1))
	fi
done
if [ -r "$SRC/$SORGENTE_BANCO" ]; then
	ok "$SRC/$SORGENTE_BANCO  ($(md5sum < "$SRC/$SORGENTE_BANCO" | cut -c1-12))"
else
	ko "⛔ manca $SRC/$SORGENTE_BANCO"
	mancano=$((mancano + 1))
fi
if [ "$mancano" -ne 0 ]; then
	ko "⛔ $mancano sorgenti mancano: non costruisco, e NON dico che va bene"
	inf "si portano con: bash banchi/attrezzi-allinea-prodotto.sh allinea  (da CHUWI)"
	exit 2
fi

if [ "${1:-costruisci}" = guarda ]; then
	log "1. Il binario c'e', ed e' piu' nuovo dei sorgenti?"
	if [ ! -x "$BINARIO" ]; then
		ko "⛔ non c'e' $BINARIO"
		exit 1
	fi
	vecchio=
	for f in $SORGENTI_PRODOTTO cattura.h mutter.h registro.h; do
		[ "$PRODOTTO/$f" -nt "$BINARIO" ] && vecchio="$vecchio $f"
	done
	[ "$SRC/$SORGENTE_BANCO" -nt "$BINARIO" ] && vecchio="$vecchio $SORGENTE_BANCO"
	if [ -n "$vecchio" ]; then
		ko "⛔ il binario e' PIU' VECCHIO di:$vecchio"
		inf "misurare adesso vorrebbe dire eseguire codice diverso da quello letto"
		exit 1
	fi
	ok "il binario e' piu' nuovo di tutti i sorgenti"
	exit 0
fi

log "1. La costruzione, dentro il contenitore"
mkdir -p "$QUI" || exit 2
inf "opzioni: le stesse di src/Makefile, piu' libpipewire-0.3, gio-2.0, libdrm"
# ⛔ Nessuna redirezione attorno a enter.sh: il registro si scrive DENTRO le
#    virgolette, su un file del server, e lo si rilegge qui sotto.
bash /media/REMOTIX/enter.sh "cd $DENTRO_QUI && \
    gcc -O2 -g -std=gnu11 -D_GNU_SOURCE -Wall -Wextra -Wno-unused-parameter \
        -I$DENTRO_SRC/remotix \
        -o 02-cattura-prodotto \
        $DENTRO_SRC/$SORGENTE_BANCO \
        $DENTRO_SRC/remotix/cattura.c $DENTRO_SRC/remotix/mutter.c \
        $DENTRO_SRC/remotix/registro.c \
        \$(pkg-config --cflags --libs libpipewire-0.3 gio-2.0 libdrm) \
        > $DENTRO_QUI/costruzione-prodotto.log 2>&1; \
    echo \"uscita-gcc: \$?\" >> $DENTRO_QUI/costruzione-prodotto.log"
esito_enter=$?

log "2. L'esito del COMPILATORE, non la presenza del binario"
if [ ! -r "$REGISTRO" ]; then
	ko "⛔ non c'e' nessun registro di costruzione ($REGISTRO): enter.sh e' uscito con $esito_enter"
	inf "⚠ e questo NON e' «ha compilato»: e' «non ho potuto guardare»"
	exit 2
fi
sed 's/^/       /' "$REGISTRO"
uscita_gcc=$(sed -n 's/^uscita-gcc: //p' "$REGISTRO" | tail -1)
if [ -z "$uscita_gcc" ]; then
	ko "⛔ il registro non porta l'uscita di gcc: non so se abbia compilato"
	exit 2
fi
if [ "$uscita_gcc" != 0 ]; then
	ko "⛔ gcc e' uscito con $uscita_gcc: NON ho costruito niente"
	exit 1
fi
if [ ! -x "$BINARIO" ]; then
	ko "⛔ gcc dice 0 e il binario non c'e': $BINARIO"
	exit 2
fi
ok "gcc uscita 0, e il binario c'e'"
ls -la "$BINARIO"

log "3. Il verdetto"
ok "⭐ costruito: $BINARIO"
inf "adesso il banco si punta sul PRODOTTO cosi', e il giudice non cambia:"
inf "    PROG=$BINARIO FONTE=$SRC/$SORGENTE_BANCO \\"
inf "        bash $SRC/02-cattura-lancia.sh misura"
inf "e la certificazione intera:"
inf "    PROG=$BINARIO FONTE=$SRC/$SORGENTE_BANCO \\"
inf "        bash $SRC/02-cattura-certifica.sh"
exit 0
