#!/usr/bin/env bash
# ===========================================================================
# 10-c1-terreno — il terreno dell'incarico 10-c1 (le cure di P2/P4/P5)
#
#   porta 8210 · utenti `provaf1 … provaf7` (uid 1160-1166, CONDIVISI con 10-b6)
#   albero /media/REMOTIX/src/10c1-src · lavoro /media/REMOTIX/tmp/10c1
#   unita' remotix-8210 · lucchetto GPU `10-c1`
#
# ⛔ NON RISCRIVE `07-b64-terreno.sh`: gli passa il MIO ambiente e lo chiama,
#    come fanno `09-b86-terreno.sh`, `10-b93-terreno.sh` e `10-b97-terreno.sh`.
#    L'unico passo tutto mio e' `porta`, che deve poter costruire DUE binari.
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ I DUE BINARI, E PERCHE' IL BANCO NE VUOLE DUE
# ═══════════════════════════════════════════════════════════════════════════
#
# ⭐ «Una cura senza il rosso di prima non e' una cura: e' una speranza.»  ⇒ Il
#    banco confronta **lo stesso binario meno la cura**, e non due macchine, non
#    due giorni e non due scene.  Percio' `porta` prende da dove glielo si dice:
#
#      SORGENTE=<dir>   la cartella che contiene `src/` e `banchi/rcp/`
#                       (predefinito: questo albero di lavoro, cioe' CON le cure)
#      SENZA_INNESTO=1  non innesta il guardiano finto (prodotto nudo, per P2/P5)
#      BINARIO=<nome>   copia il binario costruito in $LAV/<nome>, cosi' i due
#                       bracci si accendono senza ricompilare
#
# ⛔ L'INNESTO DEL GUARDIANO FINTO VIVE SOLO SULLA MACCHINA DI PROVA, e lo fa
#    `banchi/10-c1-innesta.py`, che **fallisce** invece di indovinare se il testo
#    originale non combacia.  ⭐ Sa innestare tutt'e due gli adattatori e dice da
#    se' quale albero ha davanti (col ripasso = con la cura; senza = il rosso).
#
# Uso (dal portatile):
#     bash banchi/10-c1-terreno.sh utenti
#     SORGENTE=/tmp/10-c1-base BINARIO=remotix-base bash banchi/10-c1-terreno.sh porta
#     BINARIO=remotix-cura                          bash banchi/10-c1-terreno.sh porta
#     bash banchi/10-c1-terreno.sh accendi|spegni|stato
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-8210}
export UTENTE=${UTENTE:-provaf1}
export UID_B=${UID_B:-1160}
export PAROLA_UTENTE=${PAROLA_UTENTE:-f-guardiano-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10c1-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10c1}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10c1-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10c1}
export UNITA=${UNITA:-remotix-$PORTA}
QUANTI=${QUANTI:-7}
SENZA_INNESTO=${SENZA_INNESTO:-0}
BINARIO=${BINARIO:-}

QUI=$(cd "$(dirname "$0")/.." && pwd)
SORGENTE=${SORGENTE:-$QUI}
STAGING=${STAGING:-/tmp/10-c1-repo}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

nome_utente() { printf 'provaf%d' "$1"; }
uid_utente()  { printf '%d' "$((1159 + $1))"; }

PASSO=${1:-stato}
case "$PASSO" in
utenti)
	# ⛔ Sette utenti, e servono tutti: `posto_prendi()` risponde POSTO_OCCUPATO
	#    al secondo attacco dello STESSO nome (`rcp.c:947`), quindi N sessioni
	#    vogliono N nomi diversi, non N clienti.
	for i in $(seq 1 "$QUANTI"); do
		u=$(nome_utente "$i"); n=$(uid_utente "$i")
		log "utente $u (uid $n)"
		UTENTE=$u UID_B=$n bash "$QUI/banchi/07-b64-terreno.sh" utente || exit 2
	done
	exit 0 ;;

porta)
	log "1 · I sorgenti da «$SORGENTE» verso $ALBERO"
	[ -d "$SORGENTE/src" ] || { ko "⛔ «$SORGENTE/src» non c'e'"; exit 2; }
	inf "md5 main.c:         $(md5sum "$SORGENTE/src/main.c" | cut -d' ' -f1)"
	inf "md5 webtransport.c: $(md5sum "$SORGENTE/src/webtransport.c" | cut -d' ' -f1)"
	inf "md5 sentinella.c:   $(md5sum "$SORGENTE/src/sentinella.c" | cut -d' ' -f1)"
	# ⛔ R12.3: le tre copie gemelle devono combaciare, o il Makefile si rifiuta.
	for f in rcp.c rcp.h autenticazione.c; do
		if ! cmp -s "$SORGENTE/src/$f" "$SORGENTE/banchi/rcp/$f"; then
			ko "⛔ src/$f e banchi/rcp/$f DIVERGONO (R12.3)"; exit 2
		fi
	done
	ok "le tre copie gemelle sono allineate"
	# ⛔ `--exclude` di oggetti e binario: spedendoli `make` troverebbe tutto
	#    aggiornato e resterebbe il binario del portatile (forma D5).
	tar -C "$SORGENTE" --exclude='src/remotix' --exclude='src/*.o' -cf - \
		src banchi/rcp | gzip | \
		ssh -o BatchMode=yes "$MACCHINA" "mkdir -p $ALBERO && tar -C $ALBERO -xzf -" || {
		ko "⛔ i sorgenti non sono arrivati"; exit 2; }
	# ⛔ Gli attrezzi vengono SEMPRE da questo albero di lavoro, anche quando i
	#    sorgenti vengono da un'altra parte: il braccio del rosso deve usare gli
	#    STESSI attrezzi del verde, o si confronterebbero due banchi.
	tar -C "$QUI" -cf - \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py \
		banchi/10-c1-innesta.py | gzip | \
		ssh -o BatchMode=yes "$MACCHINA" "tar -C $ALBERO -xzf -" || {
		ko "⛔ gli attrezzi non sono arrivati"; exit 2; }
	ok "sorgenti e attrezzi in $ALBERO"

	# ⛔⭐ LA COPIA DI RAFFRONTO, e serve a un controllo che altrimenti sarebbe
	#     COSTRETTO A DARE ROSSO.  `10-b0-terreno.sh` T5.2 confronta byte per
	#     byte i sorgenti sulla macchina con quelli del repository; con un
	#     innesto quel confronto DEVE fallire.  ⇒ Non si spegne il controllo: gli
	#     si da' il termine di paragone giusto, una copia su cui gira lo STESSO
	#     innesto.
	rm -rf "$STAGING"
	mkdir -p "$STAGING/src" "$STAGING/banchi"
	cp -a "$SORGENTE/src/." "$STAGING/src/"
	rm -f "$STAGING/src/remotix" "$STAGING"/src/*.o
	cp -a "$SORGENTE/banchi/rcp" "$STAGING/banchi/rcp"

	if [ "$SENZA_INNESTO" = 1 ]; then
		log "2 · ⚠ SENZA_INNESTO=1 — NON innesto il guardiano finto"
		inf "e' il binario del PRODOTTO NUDO (P2/P5); per P4 serve la leva"
	else
		log "2 · ⛔ L'INNESTO DEL GUARDIANO FINTO — solo qui, mai nel repository"
		python3 "$QUI/banchi/10-c1-innesta.py" --file="$LAV/c1-ritardo" \
			"$STAGING/src/main.c" | sed 's/^/        /' || {
			ko "⛔ l'innesto sulla copia di raffronto non e' riuscito"; exit 2; }
		ssh -o BatchMode=yes "$MACCHINA" \
			"python3 $ALBERO/banchi/10-c1-innesta.py --file=$LAV/c1-ritardo $ALBERO/src/main.c" \
			|| { ko "⛔ l'innesto NON e' riuscito"; exit 2; }
		ssh -o BatchMode=yes "$MACCHINA" \
			"python3 $ALBERO/banchi/10-c1-innesta.py --verifica $ALBERO/src/main.c" \
			|| { ko "⛔ l'innesto non si rilegge"; exit 2; }
		ok "innestato"
	fi
	inf "copia di raffronto in $STAGING (⛔ FUORI dal repository)"

	log "3 · Compilo dentro il contenitore"
	if ! ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
		  bash $DENTRO_ALB/src/costruisci.sh 2>&1 | tail -25'"; then
		ko "⛔ la compilazione e' fallita: NON accendo niente"
		exit 2
	fi
	ok "compilato"

	# ⛔⭐ E IL BINARIO CHE MISURO E' QUELLO CHE CREDO — tre gambe: l'md5, l'eta'
	#     rispetto al sorgente (forma D5), e la marca letta DAL BINARIO.
	log "4 · ⛔ CHE COSA HO COSTRUITO"
	ssh -o BatchMode=yes "$MACCHINA" "
		echo \"md5 main.c remoto:  \$(md5sum $ALBERO/src/main.c | cut -d' ' -f1)\"
		echo \"md5 binario:        \$(md5sum $ALBERO/src/remotix | cut -d' ' -f1)\"
		if [ \$(stat -c %Y $ALBERO/src/remotix) -ge \$(stat -c %Y $ALBERO/src/main.c) ]; then
			echo '⭐ il binario e\" piu\" giovane del sorgente'
		else
			echo '⛔ IL BINARIO E\" PIU\" VECCHIO DEL SORGENTE: forma D5'
		fi
		if grep -qa 'b97-guardiano INNESTATO' $ALBERO/src/remotix; then
			echo '⭐ la marca del guardiano finto C\"E\" nel binario'
		else
			echo '⚠ la marca del guardiano finto NON c\"e\" (albero senza innesto)'
		fi
		if grep -qa 'una chiamata per RIPASSO' $ALBERO/src/remotix; then
			echo '⭐ la CURA di P4 c\"e\" nel binario (una domanda per ripasso)'
		else
			echo '⚠ la cura di P4 NON c\"e\" nel binario: e\" il braccio del ROSSO'
		fi
		if grep -qa 'il ciclo del padre e. rimasto indietro' $ALBERO/src/remotix; then
			echo '⭐ la CURA del buco del ciclo c\"e\" nel binario'
		else
			echo '⚠ la cura del buco del ciclo NON c\"e\": e\" il braccio del ROSSO'
		fi
	" || { ko "non ho potuto rileggere il binario"; exit 2; }

	if [ -n "$BINARIO" ]; then
		ssh -o BatchMode=yes "$MACCHINA" \
			"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' cp -a $ALBERO/src/remotix $LAV/$BINARIO" \
			|| { ko "⛔ non ho potuto mettere da parte il binario"; exit 2; }
		ok "binario messo da parte in $LAV/$BINARIO"
	fi
	exit 0 ;;

metti)
	# ⭐ Rimette in $ALBERO/src/remotix uno dei binari messi da parte, senza
	#    ricompilare: e' quel che permette al controllo negativo di costare
	#    trenta secondi invece di dieci minuti.
	[ -n "$BINARIO" ] || { ko "⛔ manca BINARIO=<nome>"; exit 2; }
	# ⛔⛔ PRIMA SI SPEGNE L'UNITA', E NON E' PULIZIA: `cp` **sopra un eseguibile
	#     in esecuzione** fallisce con `ETXTBSY` («Text file busy»).  `[M]` 25
	#     agosto 2026, primo giro vero: il braccio del verde non e' partito
	#     affatto, e il banco ha detto «non ho potuto rimettere il binario» —
	#     giusto, ⚠ ma la ragione non si capiva dalla riga.  ⇒ Si spegne, si
	#     copia, e chi accende dopo trova il binario che ha chiesto.
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c 'systemctl stop $UNITA.service 2>/dev/null; systemctl reset-failed $UNITA.service 2>/dev/null; i=0; while ss -uln | grep -q \":$PORTA \" && [ \$i -lt 50 ]; do i=\$((i+1)); sleep 0.2; done; cp -a $LAV/$BINARIO $ALBERO/src/remotix && md5sum $ALBERO/src/remotix'" \
		|| { ko "⛔ non ho potuto rimettere «$BINARIO»"; exit 2; }
	ok "in $ALBERO/src/remotix adesso c'e' «$BINARIO»"
	exit 0 ;;

*)
	# ⛔ Tutto il resto e' `07-b64-terreno.sh`, con il MIO ambiente esportato.
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
esac
