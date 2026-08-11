#!/bin/bash
#
# costruisci.sh — costruisce il server DENTRO il contenitore della macchina di
#                 prova.  Gira gia' dentro `enter.sh`, non lo chiama lui.
#
#   bash <dove-sta-questo-file>/costruisci.sh
#
# ⚠ Il percorso NON e' fisso, ed e' cambiato il 10 agosto 2026 notte (rilievo
#   R12.8): la riga qui sopra diceva `/srv/src/remotix/costruisci.sh`, e
#   `/srv/src` e' la cartella DEI BANCHI — nessuno script del repo copia niente
#   in `/srv/src/remotix`.  Tutto quel che serve lo ricava da `$QUI`, cioe' da
#   dove sta questo file: si mette la cartella `src/` dove si vuole e si lancia.
#
# ⛔ E LE VARIABILI D'AMBIENTE CHE ACCETTA, perche' un percorso indovinato e'
#    un percorso che un giorno cambia:
#
#      PREFISSO   dove stanno installate ngtcp2/nghttp3   (def. /srv/src/b2/prefisso)
#      NGTCP2     l'albero dei sorgenti di ngtcp2         (def. /srv/src/b2/ngtcp2)
#      NGHTTP3    l'albero dei sorgenti di nghttp3        (def. /srv/src/b2/nghttp3)
#      GEMELLO    la copia gemella di rcp.c/rcp.h/autenticazione.c da confrontare
#                 (def. <QUI>/../banchi/rcp, e `nessuno` per DICHIARARE di non
#                  confrontare — vedi il Makefile, rilievo R12.3)
#
# -----------------------------------------------------------------------------
# ⛔ DOPO AVER COSTRUITO SI GUARDA L'ESITO DEL COSTRUTTORE, NON LA PRESENZA DEL
#    FILE.
#
# `LEZIONI.md` §1.9 punto 8: «un file di ieri risponde "si'" a *esiste?*
# esattamente come uno di adesso».  Il banco di B11 ha acceso il server SANO
# dichiarando di aver acceso quello guasto, perche' controllava `test -x`.
#
# ⭐ Da cui le due cose che questo script fa e che un `make` nudo non fa:
#    1. cancella il binario PRIMA di ricostruire, cosi' «c'e'» significa «e'
#       di adesso»;
#    2. controlla la MARCA dentro il binario prodotto — che risponde alla
#       domanda giusta: *e' dentro quel che ci doveva essere?*
# -----------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
PREFISSO=${PREFISSO:-/srv/src/b2/prefisso}
NGTCP2=${NGTCP2:-/srv/src/b2/ngtcp2}
NGHTTP3=${NGHTTP3:-/srv/src/b2/nghttp3}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# -----------------------------------------------------------------------------
# 1. Dove stanno ngtcp2 e nghttp3.  ⛔ Si DICHIARA dove si e' guardato: un
#    «non trovato» senza il denominatore non e' una misura (`LEZIONI.md` §1.9).
log "Le dipendenze costruite dai sorgenti"

INC=""
LIB=""

cerca_ngtcp2()
{
	local i h
	for i in "$NGTCP2/build/lib/includes" "$NGTCP2/lib/includes" \
	         "$PREFISSO/include"; do
		[ -f "$i/ngtcp2/ngtcp2.h" ] || [ -f "$i/ngtcp2/version.h" ] && \
			INC="$INC -I$i"
	done
	# le intestazioni della crittografia stanno in un albero a parte
	h="$NGTCP2/crypto/includes"
	[ -f "$h/ngtcp2/ngtcp2_crypto_ossl.h" ] && INC="$INC -I$h"

	for i in "$NGTCP2/build/lib" "$NGTCP2/build/crypto/ossl" "$PREFISSO/lib"; do
		[ -d "$i" ] && LIB="$LIB -L$i -Wl,-rpath,$i"
	done
}

cerca_nghttp3()
{
	local i
	for i in "$NGHTTP3/lib/includes" "$NGHTTP3/build/lib/includes" \
	         "$PREFISSO/include"; do
		[ -f "$i/nghttp3/nghttp3.h" ] || [ -f "$i/nghttp3/version.h" ] && \
			INC="$INC -I$i"
	done
	for i in "$NGHTTP3/build/lib" "$PREFISSO/lib"; do
		[ -d "$i" ] && LIB="$LIB -L$i -Wl,-rpath,$i"
	done
}

cerca_ngtcp2
cerca_nghttp3

printf '    --  ho guardato in:\n'
printf '        %s\n' "$NGTCP2" "$NGHTTP3" "$PREFISSO"
printf '    --  intestazioni: %s\n' "${INC:-(nessuna)}"
printf '    --  librerie:     %s\n' "${LIB:-(nessuna)}"

[ -n "$INC" ] || { ko "nessuna intestazione trovata"; exit 2; }
[ -n "$LIB" ] || { ko "nessuna libreria trovata"; exit 2; }
ok "percorsi composti"

# -----------------------------------------------------------------------------
log "OpenSSL"
V=$(openssl version 2>&1)
printf '    --  %s\n' "$V"
case "$V" in
	OpenSSL\ 3.[5-9]*|OpenSSL\ [4-9]*) ok "3.5 o piu': c'e' l'API QUIC nativa" ;;
	*) ko "serve OpenSSL >= 3.5 per ngtcp2_crypto_ossl"; exit 2 ;;
esac

# -----------------------------------------------------------------------------
log "Si butta il binario vecchio PRIMA di costruire"
rm -f "$QUI/remotix" "$QUI"/*.o
if [ -e "$QUI/remotix" ]; then
	ko "il binario vecchio non si cancella: non si distinguerebbe dal nuovo"
	exit 2
fi
ok "via il vecchio"

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# ⛔⭐ LE DUE COPIE DELLO STESSO MODULO — rilievo R12.3.
#
# `rcp.c`, `rcp.h` e `autenticazione.c` stanno in due cartelle di questo repo,
# perche' sono lo stesso modulo montato su due ospiti.  Il confronto lo fa il
# bersaglio `impronte` del Makefile, e il Makefile FERMA la costruzione se
# divergono.  ⚠ Qui si sceglie soltanto DOVE guardare, e si DICHIARA se non si
# e' potuto guardare: «non ho trovato differenze» e «non ho guardato» sono due
# fatti diversi.
log "La copia gemella di rcp.c"
if [ -z "${GEMELLO:-}" ]; then
	for c in "$QUI/../banchi/rcp" "$QUI/rcp-gemello" /srv/src/rcp; do
		if [ -f "$c/rcp.c" ]; then GEMELLO=$c; break; fi
	done
fi
if [ -z "${GEMELLO:-}" ]; then
	ko "⛔ nessuna copia gemella trovata: ho guardato in"
	printf '        %s\n' "$QUI/../banchi/rcp" "$QUI/rcp-gemello" /srv/src/rcp
	ko "   NON e' «le copie combaciano»: e' «non ho potuto guardare».  Si"
	ko "   costruisce lo stesso, e questa riga e' la dichiarazione (R12.3)."
	GEMELLO=nessuno
else
	ok "confronto contro «$GEMELLO»"
fi

# -----------------------------------------------------------------------------
log "make"
# ⚠ L'uscita di make va a terminale come esce: niente tubi, o lo stato che si
#   legge sarebbe quello dell'ultimo comando del tubo (`LEZIONI.md` §1.9).
make -C "$QUI" \
	GEMELLO="$GEMELLO" \
	CFLAGS="-O2 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter $INC" \
	LDFLAGS="$LIB" \
	tutto
ESITO=$?

if [ "$ESITO" -ne 0 ]; then
	ko "⛔ la compilazione e' FALLITA (uscita $ESITO).  Il binario NON e' stato"
	ko "   costruito, e quel che eventualmente c'e' sul disco non e' di adesso."
	exit "$ESITO"
fi
ok "make e' uscito 0"

# -----------------------------------------------------------------------------
# ⛔ E adesso la domanda giusta: e' dentro quel che ci doveva essere?
log "La marca dentro il binario"
if [ ! -x "$QUI/remotix" ]; then
	ko "make e' uscito 0 e il binario non c'e': qualcosa non torna"
	exit 3
fi

# ⚠ `grep -a` sul binario, e NON `strings`: `binutils` puo' non esserci — e la
#   prima stesura di questo script ci e' inciampata, dichiarando assenti tutte e
#   cinque le marche perche' lo STRUMENTO non c'era.  E' `LEZIONI.md` §1.9
#   seconda regola: e' stato il controllo positivo a dirlo, non le cinque righe
#   rosse.
cerca() # $1 = file, $2 = testo
{
	grep -a -F -q -e "$2" -- "$1"
}

MANCA=0
# ⚠ Le ultime tre marche sono del 10 agosto 2026 notte, e ciascuna risponde a
#   una domanda che un `make` riuscito NON risponde:
#     NON-BANNATO         il comando di sblocco su socket c'e' davvero (R12.1)
#     PING del trasporto  la cura di §4.6 e' dentro questo binario (B-2)
#     pam.d/remotix       il servizio PAM e' quello di SPECIFICHE.md §4.2 (B-11)
for marca in "REMOTIX_V2 — fase 1" "Cross-Origin-Embedder-Policy" \
             "Cross-Origin-Opener-Policy" "/rcp/1" "/impronta" \
             "NON-BANNATO" "PING del trasporto" "/etc/pam.d/remotix"; do
	if cerca "$QUI/remotix" "$marca"; then
		ok "«$marca» c'e' nel binario"
	else
		ko "«$marca» NON c'e' nel binario"
		MANCA=1
	fi
done

# ⛔ E i segni che il server sostituisce nella pagina stanno nella PAGINA, non
#    nel binario: e' il controllo che `pagina_apri()` rifa' all'avvio, e senza
#    il quale il server servirebbe per sempre una pagina senza impronta — o una
#    pagina che non dice se l'indirizzo e' bannato (R12.2).
for segno in "__IMPRONTA__" "__AVVISO__" "__BANNATO__" "__RESTANO_MS__"; do
	if cerca "$QUI/pagina.html" "$segno"; then
		ok "«$segno» c'e' in pagina.html"
	else
		ko "«$segno» NON c'e' in pagina.html: il server rifiutera' di partire"
		MANCA=1
	fi
done

# Il controllo positivo dello strumento: sa trovare qualcosa che c'e' di sicuro?
# Senza, «non l'ho trovato» e «non so cercare» hanno la stessa faccia.
if cerca "$QUI/remotix" "GCC:" || cerca "$QUI/remotix" "main.c"; then
	ok "controllo positivo: lo strumento sa trovare quel che c'e' di sicuro"
else
	ko "⛔ lo strumento NON trova nemmeno la marca del compilatore: i NO qui"
	ko "   sopra non valgono niente"
	exit 3
fi

[ "$MANCA" -eq 0 ] || exit 3

# -----------------------------------------------------------------------------
# ⛔⭐ IL SERVIZIO PAM — `SPECIFICHE.md` §4.2, rilievo B-11.
#
# Senza `/etc/pam.d/remotix`, Linux-PAM ripiega sul servizio `other`, che su
# Debian e' `pam_deny`: OGNI parola d'ordine giusta viene rifiutata, e quel che
# si legge e' «utente o parola d'ordine non corretti».  ⛔ Il difetto e' un file
# mancante e la diagnosi punta sulla parola d'ordine — la forma esatta che
# `LEZIONI.md` §1.9 chiama la piu' cara.
#
# ⚠ Non si sovrascrive un file gia' presente: chi amministra la macchina puo'
#   averlo modificato, e riscriverglielo a ogni costruzione sarebbe una
#   configurazione che si perde da sola.
log "Il servizio PAM"
if [ -f /etc/pam.d/remotix ]; then
	ok "/etc/pam.d/remotix c'e' gia' (non lo tocco)"
elif cp "$QUI/remotix.pam" /etc/pam.d/remotix 2>/dev/null; then
	ok "installato /etc/pam.d/remotix da $QUI/remotix.pam"
else
	ko "⛔ /etc/pam.d/remotix NON c'e' e non l'ho potuto installare (serve root)."
	ko "   Il server partira' e RIFIUTERA' ogni parola d'ordine, dicendo che e'"
	ko "   sbagliata.  Si copia a mano:  cp $QUI/remotix.pam /etc/pam.d/remotix"
fi

log "Le librerie da cui dipende davvero"
ldd "$QUI/remotix" | grep -E 'ngtcp2|nghttp3|ssl|crypto|pam' || true

printf '\n'
ok "⭐ costruito: $QUI/remotix"
