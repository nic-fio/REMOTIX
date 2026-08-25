#!/usr/bin/env bash
# ===========================================================================
# 10-b89-terreno — il terreno del banco DEL COSTO DI **UNA** SESSIONE (agente A3)
#
#   porta 8010 · utente `provadec1` (uid 1100)
#   albero /media/REMOTIX/src/10a3-src · lavoro /media/REMOTIX/tmp/10a3
#   unita' remotix-8010
#
# ⛔ NON RISCRIVE `07-b64-terreno.sh`: gli passa il MIO ambiente e lo chiama.
#    E' modellato riga per riga su `09-b86-terreno.sh`.
#
# ⛔ Il tar deve portare anche `banchi/rcp`: `src/costruisci.sh` confronta
#    `rcp.c`/`rcp.h`/`autenticazione.c` con la copia gemella (rilievo R12.3), e
#    senza quella cartella la costruzione FALLISCE.
#
# ⛔ E si portano anche `01-b4-validatore.py` (l'arbitro del formato §11.1) e
#    `07-b64-terreno.sh` (che e' il copione che gira DA ROOT sulla macchina:
#    `$SUL_SERVER` lo cerca dentro l'albero).
#
# ⛔⛔ LE PORTE, GLI UTENTI E GLI ALBERI CHE NON SONO MIEI non si toccano: in
#      questa fase girano altri agenti con le loro porte 80xx.  Qui non si
#      installa nessun `netem`: si misura la linea com'e'.
#
# Uso (dal portatile):
#     bash banchi/10-b89-terreno.sh utente
#     bash banchi/10-b89-terreno.sh porta      # tar + compila dentro il contenitore
#     bash banchi/10-b89-terreno.sh accendi
#     bash banchi/10-b89-terreno.sh stato
#     bash banchi/10-b89-terreno.sh spegni
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-8010}
export UTENTE=${UTENTE:-provadec1}
export UID_B=${UID_B:-1100}
export PAROLA_UTENTE=${PAROLA_UTENTE:-dec1-costo-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10a3-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10a3}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10a3-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10a3}
export UNITA=${UNITA:-remotix-$PORTA}

QUI=$(cd "$(dirname "$0")/.." && pwd)
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

PASSO=${1:-stato}
case "$PASSO" in
porta)
	log "1 · I sorgenti in $ALBERO"
	printf '    --  HEAD = %s\n' "$(cd "$QUI" && git rev-parse --short HEAD)"
	inf "md5 locale rcp.c:    $(md5sum "$QUI/src/rcp.c" | cut -d' ' -f1)"
	inf "md5 locale figlio.c: $(md5sum "$QUI/src/figlio.c" | cut -d' ' -f1)"
	# ⛔ Le due copie di rcp.c/rcp.h/autenticazione.c si controllano QUI: un
	#    rifiuto a 200 km di distanza costa un giro di ssh per dire una cosa
	#    che si sa gia' adesso (R12.3).
	for f in rcp.c rcp.h autenticazione.c; do
		if ! cmp -s "$QUI/src/$f" "$QUI/banchi/rcp/$f"; then
			ko "⛔ src/$f e banchi/rcp/$f DIVERGONO: la costruzione fallirebbe (R12.3)"
			exit 2
		fi
	done
	ok "le due copie di rcp.c/rcp.h/autenticazione.c sono allineate"
	tar -C "$QUI" --exclude='src/remotix' --exclude='src/*.o' -cf - \
		src banchi/rcp \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/01-b4-validatore.py \
		banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py | \
		gzip | ssh -o BatchMode=yes "$MACCHINA" \
		"mkdir -p $ALBERO && tar -C $ALBERO -xzf -" || {
		ko "⛔ i sorgenti non sono arrivati"; exit 2; }
	ok "sorgenti in $ALBERO"

	log "2 · Compilo dentro il contenitore sulla macchina di prova"
	if ! ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
		  bash $DENTRO_ALB/src/costruisci.sh 2>&1 | tail -25'"; then
		ko "⛔ la compilazione e' fallita: NON accendo niente"
		exit 2
	fi
	ok "compilato"

	log "3 · ⛔ CHE COSA HO COSTRUITO — l'md5 del binario, non il nome della cartella"
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \"
		 echo md5 binario: \\\$(md5sum $ALBERO/src/remotix | cut -d' ' -f1)
		 echo md5 rcp.c:   \\\$(md5sum $ALBERO/src/rcp.c | cut -d' ' -f1)\"" \
		|| { ko "non ho potuto rileggere il binario"; exit 2; }
	exit 0 ;;
*)
	# ⛔ Tutto il resto e' `07-b64-terreno.sh`, con il MIO ambiente esportato:
	#    non se ne riscrive una riga.
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
esac
