#!/usr/bin/env bash
# ===========================================================================
# 10-b97-terreno — il terreno del banco DELLA SOGLIA DEL GUARDIANO (agente 10-b6)
#
#   porta 8160 · utenti `provaf1 … provaf7` (uid 1160-1166)
#   albero /media/REMOTIX/src/10b6-src · lavoro /media/REMOTIX/tmp/10b6
#   unita' remotix-8160 · lucchetto GPU `10-b6`
#
# ⛔ NON RISCRIVE `07-b64-terreno.sh`: gli passa il MIO ambiente e lo chiama,
#    come fanno `09-b86-terreno.sh` e `10-b93-terreno.sh`.  Gli unici due passi
#    tutti miei sono `utenti` (sette invece di uno) e `porta` (l'innesto).
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ L'INNESTO, E VA DICHIARATO PRIMA DI QUALUNQUE NUMERO
# ═══════════════════════════════════════════════════════════════════════════
#
# Questo albero si compila con **il guardiano finto** innestato in
# `src/main.c`, e la ragione e' che R10-A3 e' un difetto **condizionato** alla
# lentezza di logind: su questa macchina logind e' sano, e senza una leva la
# condizione non si presenta mai.  ⭐ La leva la dichiara il prodotto stesso
# (`src/main.c:1028`): si sostituisce l'ADATTATORE, e il trasporto non si tocca.
#
# ⛔ LA MODIFICA VIVE SOLO QUI, SULLA MACCHINA DI PROVA: `src/main.c` del
#    repository non si tocca.  L'innesto gira DOPO lo scaricamento del tar,
#    sulla copia in `$ALBERO`, e lo fa `banchi/10-b97-innesta.py`, che
#    **fallisce** invece di indovinare se il testo originale non combacia.
#
# ⚠ `banchi/rcp/` NON e' toccato: l'innesto sta in `main.c`, che non ha gemella.
#   ⛔ Ma il `tar` deve portarlo lo stesso, o `src/costruisci.sh` si rifiuta di
#     compilare (rilievo R12.3).
#
# ⛔⛔ LE PORTE E GLI UTENTI CHE NON SONO MIEI: `provamt*` e `provadec*` sono di
#      altri incarichi, e le loro porte pure.  Qui si CONTANO, non si toccano.
#
# Uso (dal portatile):
#     bash banchi/10-b97-terreno.sh utenti      # tutti e sette
#     bash banchi/10-b97-terreno.sh porta       # tar + INNESTO + compila + md5
#     bash banchi/10-b97-terreno.sh accendi
#     bash banchi/10-b97-terreno.sh stato
#     bash banchi/10-b97-terreno.sh spegni
#
#   SENZA_INNESTO=1 bash banchi/10-b97-terreno.sh porta
#     ⭐ il braccio di controllo del `--certifica`: compila l'albero SENZA il
#       guardiano finto, cioe' il prodotto com'e'.  Il banco allora deve dire
#       «non ho misurato», non «nessuno scatto».
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-8160}
export UTENTE=${UTENTE:-provaf1}
export UID_B=${UID_B:-1160}
export PAROLA_UTENTE=${PAROLA_UTENTE:-f-guardiano-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10b6-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10b6}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10b6-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10b6}
export UNITA=${UNITA:-remotix-$PORTA}
QUANTI=${QUANTI:-7}
SENZA_INNESTO=${SENZA_INNESTO:-0}

QUI=$(cd "$(dirname "$0")/.." && pwd)
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

nome_utente() { printf 'provaf%d' "$1"; }
uid_utente()  { printf '%d' "$((1159 + $1))"; }

PASSO=${1:-stato}
case "$PASSO" in
utenti)
	# ⛔ Sette utenti, e servono tutti: `posto_prendi()` risponde
	#    POSTO_OCCUPATO al secondo attacco dello STESSO nome (`rcp.c:947`), e il
	#    guardiano costa **una chiamata per SESSIONE ATTACCATA** — quindi N
	#    sessioni vogliono N nomi diversi, non N clienti.
	for i in $(seq 1 "$QUANTI"); do
		u=$(nome_utente "$i"); n=$(uid_utente "$i")
		log "utente $u (uid $n)"
		UTENTE=$u UID_B=$n bash "$QUI/banchi/07-b64-terreno.sh" utente || exit 2
	done
	exit 0 ;;

porta)
	log "1 · I sorgenti in $ALBERO"
	printf '    --  HEAD = %s\n' "$(cd "$QUI" && git rev-parse --short HEAD)"
	inf "md5 locale main.c:        $(md5sum "$QUI/src/main.c" | cut -d' ' -f1)"
	inf "md5 locale webtransport.c:$(md5sum "$QUI/src/webtransport.c" | cut -d' ' -f1)"
	inf "md5 locale sentinella.c:  $(md5sum "$QUI/src/sentinella.c" | cut -d' ' -f1)"
	for f in rcp.c rcp.h autenticazione.c; do
		if ! cmp -s "$QUI/src/$f" "$QUI/banchi/rcp/$f"; then
			ko "⛔ src/$f e banchi/rcp/$f DIVERGONO gia' nel repo (R12.3)"
			exit 2
		fi
	done
	ok "le due copie gemelle sono allineate nel repository"
	# ⛔ `--exclude` di oggetti e binario: spedendoli `make` troverebbe tutto
	#    aggiornato e resterebbe il binario del portatile (forma D5).
	tar -C "$QUI" --exclude='src/remotix' --exclude='src/*.o' -cf - \
		src banchi/rcp \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/01-b4-validatore.py \
		banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py \
		banchi/10-b97-innesta.py | \
		gzip | ssh -o BatchMode=yes "$MACCHINA" \
		"mkdir -p $ALBERO && tar -C $ALBERO -xzf -" || {
		ko "⛔ i sorgenti non sono arrivati"; exit 2; }
	ok "sorgenti in $ALBERO"

	# ⛔⭐ LA COPIA DI RAFFRONTO, e serve a un controllo che altrimenti sarebbe
	#     COSTRETTO A DARE ROSSO.  `10-b0-terreno.sh` T5.2 confronta byte per
	#     byte i sorgenti sulla macchina con quelli del repository, ed e' la riga
	#     che in fase 1 disse «il server misura una versione che nessuno sta
	#     leggendo».  Con un innesto, quel confronto DEVE fallire.
	#
	# ⇒ Non si spegne il controllo: gli si da' il termine di paragone GIUSTO —
	#   una copia locale, fuori dal repository, su cui gira lo STESSO innesto.
	#   ⭐ Se i due md5 combaciano, l'innesto e' esattamente quello dichiarato e
	#     niente altro e' cambiato; e la differenza col repository resta scritta
	#     qui sotto, in chiaro.
	STAGING=${STAGING:-/tmp/10-b97-repo}
	rm -rf "$STAGING"
	mkdir -p "$STAGING/src" "$STAGING/banchi"
	cp -a "$QUI/src/." "$STAGING/src/"
	rm -f "$STAGING/src/remotix" "$STAGING"/src/*.o
	cp -a "$QUI/banchi/rcp" "$STAGING/banchi/rcp"
	if [ "$SENZA_INNESTO" != 1 ]; then
		python3 "$QUI/banchi/10-b97-innesta.py" --file="$LAV/b97-ritardo" \
			"$STAGING/src/main.c" | sed 's/^/        /' || {
			ko "⛔ l'innesto sulla copia di raffronto non e' riuscito"; exit 2; }
	fi
	inf "copia di raffronto in $STAGING (⛔ FUORI dal repository)"

	if [ "$SENZA_INNESTO" = 1 ]; then
		log "2 · ⚠ SENZA_INNESTO=1 — NON innesto il guardiano finto"
		inf "e' il braccio di controllo: il banco dovra' dire «non ho misurato»"
	else
		log "2 · ⛔ L'INNESTO DEL GUARDIANO FINTO — solo qui, mai nel repository"
		ssh -o BatchMode=yes "$MACCHINA" \
			"python3 $ALBERO/banchi/10-b97-innesta.py --file=$LAV/b97-ritardo $ALBERO/src/main.c" \
			|| { ko "⛔ l'innesto NON e' riuscito"; exit 2; }
		ssh -o BatchMode=yes "$MACCHINA" \
			"python3 $ALBERO/banchi/10-b97-innesta.py --verifica $ALBERO/src/main.c" \
			|| { ko "⛔ l'innesto non si rilegge"; exit 2; }
		ok "innestato"
	fi

	log "3 · Compilo dentro il contenitore"
	if ! ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
		  bash $DENTRO_ALB/src/costruisci.sh 2>&1 | tail -25'"; then
		ko "⛔ la compilazione e' fallita: NON accendo niente"
		exit 2
	fi
	ok "compilato"

	# ⛔⭐ E IL BINARIO CHE MISURO E' QUELLO CHE CREDO — tre gambe:
	#     a. l'md5 del sorgente innestato, che si confronta con quello LOCALE:
	#        devono essere DIVERSI, o l'innesto non e' entrato;
	#     b. l'md5 del binario e la sua eta' rispetto a `main.c` (forma D5);
	#     c. ⭐ la marca letta DAL BINARIO: `b97-guardiano` dev'esserci, ed e'
	#        l'unica gamba che parli del binario e non dei sorgenti.
	log "4 · ⛔ CHE COSA HO COSTRUITO"
	ssh -o BatchMode=yes "$MACCHINA" "
		echo \"md5 main.c remoto:  \$(md5sum $ALBERO/src/main.c | cut -d' ' -f1)\"
		echo \"md5 binario:        \$(md5sum $ALBERO/src/remotix | cut -d' ' -f1)\"
		echo \"eta' binario:       \$(stat -c %Y $ALBERO/src/remotix) · main.c: \$(stat -c %Y $ALBERO/src/main.c)\"
		if [ \$(stat -c %Y $ALBERO/src/remotix) -ge \$(stat -c %Y $ALBERO/src/main.c) ]; then
			echo '⭐ il binario e\" piu\" giovane del sorgente'
		else
			echo '⛔ IL BINARIO E\" PIU\" VECCHIO DEL SORGENTE: forma D5'
		fi
		if grep -qa 'b97-guardiano INNESTATO' $ALBERO/src/remotix; then
			echo '⭐ la marca «b97-guardiano» C\"E\" nel binario: la leva puo\" prendere'
		else
			echo '⚠ la marca «b97-guardiano» NON c\"e\" nel binario (albero SENZA innesto)'
		fi
	" || { ko "non ho potuto rileggere il binario"; exit 2; }
	log "5 · ⛔ LA DIFFERENZA COL REPOSITORY, DICHIARATA"
	inf "md5 main.c nel REPOSITORY (che NON e' cambiato): $(md5sum "$QUI/src/main.c" | cut -d' ' -f1)"
	inf "md5 main.c nella copia di raffronto:             $(md5sum "$STAGING/src/main.c" | cut -d' ' -f1)"
	inf "righe cambiate rispetto al repository:           $(diff -u "$QUI/src/main.c" "$STAGING/src/main.c" | grep -c '^[+-][^+-]' || true)"
	D=0; for f in "$QUI"/src/*.c "$QUI"/src/*.h; do
		b=$(basename "$f")
		cmp -s "$f" "$STAGING/src/$b" || { D=$((D+1)); inf "  ⛔ diverge: src/$b"; }
	done
	inf "sorgenti .c/.h cambiati rispetto al repository:  $D (atteso: 1, cioe' main.c)"
	exit 0 ;;

*)
	# ⛔ Tutto il resto e' `07-b64-terreno.sh`, con il MIO ambiente esportato.
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
esac
