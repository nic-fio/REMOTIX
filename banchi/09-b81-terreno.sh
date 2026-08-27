#!/usr/bin/env bash
# ===========================================================================
# 09-b81-terreno — il terreno del banco delle DUE CURE NUOVE (agente NR6)
#
#   porta 7960 · utente `provanr6` (uid 1060) · albero /media/REMOTIX/src/09nr6-src
#   lavoro /media/REMOTIX/tmp/09nr6 · unita' remotix-7960
#   ⭐ e un SECONDO utente, `provanr6b` (uid 1061): serve alla prova 5, «due
#      utenti diversi non si sfrattano», che senza di lui non e' formulabile.
#
# ⛔ NON RISCRIVE `07-b64-terreno.sh`: gli passa il MIO ambiente e lo chiama.
#    Fanno da se' due passi soli, e ognuno ha la sua ragione:
#
# ⛔⛔⭐ 1. I SORGENTI SI PRENDONO DALL'ALBERO DI LAVORO, **NON** da `git
#          archive HEAD` — ed e' l'esatto contrario di `09-b76-terreno.sh`.
#
#          La ragione e' il bersaglio: le due cure di stanotte — la LINEA MORTA
#          (`webtransport.c`, `trasporto.c`) e lo SFRATTO DEL FANTASMA
#          (`rcp.c`) — **non sono committate**.  `git archive HEAD` spedirebbe
#          il prodotto di ieri, il banco girerebbe benissimo, e ogni predicato
#          direbbe «la cura non e' scattata» su un binario che la cura non ce
#          l'ha.  ⚠ E' la forma D5 nella sua versione peggiore: non un binario
#          stantio che resta verde, ma un binario stantio che fa passare per
#          MISURATA una cura mai girata.
#
#          ⇒ Si spedisce l'albero di lavoro, e si DICHIARA l'`md5` di quel che
#            si e' spedito e di quel che ne e' uscito: senza le due impronte
#            questo numero non e' rifacibile da nessuno.
#          ⚠ E si escludono `*.o` e `src/remotix`: spedendoli, `make` troverebbe
#            tutto aggiornato e resterebbe il binario del portatile.
#
# ⛔ 2. IL SECONDO UTENTE.  `07-b64-terreno.sh utente` ne sa fare uno solo e
#      scrive la sua parola in `$LAV/parola`; il secondo finisce in
#      `$LAV/parola2`, cosi' le due non possono scambiarsi di posto.
#
# ⛔ E si porta anche `banchi/01-b4-validatore.py`: e' l'ARBITRO del formato
#    §11.1 e il lettore della traccia lo cerca dentro l'albero.
#
# Uso (dal portatile):
#     bash banchi/09-b81-terreno.sh porta      # albero di lavoro + compila + md5
#     bash banchi/09-b81-terreno.sh utente     # provanr6 e provanr6b
#     bash banchi/09-b81-terreno.sh accendi    # OPZIONI_SERVER='...' per le cure
#     bash banchi/09-b81-terreno.sh stato
#     bash banchi/09-b81-terreno.sh spegni
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-7960}
export UTENTE=${UTENTE:-provanr6}
export UID_B=${UID_B:-1060}
export PAROLA_UTENTE=${PAROLA_UTENTE:-nr6-cure-nuove-2026}
export UTENTE2=${UTENTE2:-provanr6b}
export UID_B2=${UID_B2:-1061}
export PAROLA_UTENTE2=${PAROLA_UTENTE2:-nr6b-secondo-utente-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/09nr6-src}
export LAV=${LAV:-/media/REMOTIX/tmp/09nr6}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/09nr6-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/09nr6}
export UNITA=${UNITA:-remotix-$PORTA}

QUI=$(cd "$(dirname "$0")/.." && pwd)
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I GRUPPI DELLA SCHEDA SI DANNO IN UN POSTO SOLO — `attrezzi-gruppi-scheda.sh`
#
# ⛔ Qui c'era `usermod -aG render,video` (o niente affatto), coi NOMI
#    INCHIODATI e senza rileggere: due difetti in una riga sola.  La ragione
#    per cui la cura sta in un file a parte, e i numeri che la giustificano,
#    stanno nel riquadro in testa a quel file — ⛔ non si ricopiano qui, o
#    diventano dieci posti da cui divergere (`LEZIONI.md` §1.47).
# ═══════════════════════════════════════════════════════════════════════════
GRUPPI_SCHEDA_SH=${GRUPPI_SCHEDA_SH:-$(cd "$(dirname "$0")" && pwd)/attrezzi-gruppi-scheda.sh}
[ -f "$GRUPPI_SCHEDA_SH" ] || { ko "⛔ manca $GRUPPI_SCHEDA_SH: senza, l'inquilino nascerebbe CIECO"; exit 2; }
. "$GRUPPI_SCHEDA_SH"


# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE GIRA SULLA MACCHINA DI PROVA, DA ROOT — e fa un passo solo
# ═══════════════════════════════════════════════════════════════════════════
if [ "${1:-}" = "--sul-server" ]; then
	[ "$(id -u)" -eq 0 ] || { ko "⛔ «--sul-server» va eseguito DA ROOT"; exit 2; }
	case "${2:-}" in
	utente2)
		log "Il SECONDO utente del banco: $UTENTE2 (uid $UID_B2)"
		mkdir -p "$LAV" 2>/dev/null
		if id "$UTENTE2" >/dev/null 2>&1; then
			ok "c'e' gia' — non lo rifaccio"
		else
			useradd -m -u "$UID_B2" -s /bin/bash "$UTENTE2" || {
				ko "⛔ useradd non e' riuscito"; exit 2; }
			ok "creato"
		fi
		# ⛔ D12: la parola in un file 0600, mai in argv.
		( umask 077; printf '%s:%s\n' "$UTENTE2" "$PAROLA_UTENTE2" > "$LAV/.chp2" )
		chmod 600 "$LAV/.chp2"
		chpasswd < "$LAV/.chp2" || { ko "⛔ chpasswd fallito"; rm -f "$LAV/.chp2"; exit 2; }
		rm -f "$LAV/.chp2"
		ok "parola d'ordine posta (dallo stdin, mai in argv — D12)"
		# ⛔ Qui c'erano i due nomi INCHIODATI e nessuna rilettura.
		gruppi_scheda_dai_a "$UTENTE2" || exit 3
		ok "gruppi: $(id -nG "$UTENTE2")"
		loginctl enable-linger "$UTENTE2" || { ko "⛔ enable-linger fallito"; exit 2; }
		ok "linger acceso: /run/user/$UID_B2 vivra' anche senza nessuno collegato"
		# ⛔ In un file A PARTE: se andasse in `$LAV/parola` la prova 5 aprirebbe
		#    due sessioni dello STESSO utente credendo di averne aperte due di
		#    utenti diversi — cioe' misurerebbe la prova 4 e la chiamerebbe 5.
		( umask 077; printf '%s\n' "$PAROLA_UTENTE2" > "$LAV/parola2" )
		chmod 600 "$LAV/parola2"
		ok "la parola del secondo utente sta in $LAV/parola2, 0600"
		exit 0 ;;
	*)
		ko "⛔ «--sul-server» qui sa fare solo «utente2»"; exit 2 ;;
	esac
fi

# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE GIRA SUL PORTATILE
# ═══════════════════════════════════════════════════════════════════════════
PASSO=${1:-stato}
case "$PASSO" in
porta)
	log "1 · I sorgenti DELL'ALBERO DI LAVORO in $ALBERO (⛔ non git archive)"
	printf '    --  HEAD = %s · stato dell albero:\n' "$(cd "$QUI" && git rev-parse --short HEAD)"
	(cd "$QUI" && git status --short -- src banchi/rcp) | sed 's/^/        /'
	log "   le impronte di quel che SPEDISCO (⛔ le cure vivono qui)"
	(cd "$QUI" && md5sum src/webtransport.c src/webtransport.h src/trasporto.c \
		src/rcp.c src/rcp.h src/main.c banchi/rcp/rcp.c banchi/rcp/rcp.h) | \
		sed 's/^/        /'
	# ⛔ SENZA `sudo`: `printf … | sudo -S` mangerebbe lo stdin, che qui E' lo
	#    stream del `tar`.  E non serve: /media/REMOTIX/src e' di `nicfio`.
	(cd "$QUI" && tar --exclude='*.o' --exclude='src/remotix' -czf - \
		src banchi/rcp \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/01-b4-validatore.py \
		banchi/09-b78-apertura.py banchi/09-b81-terreno.sh \
		banchi/attrezzi-gruppi-scheda.sh banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py) | \
		ssh -o BatchMode=yes "$MACCHINA" \
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

	# ⛔⛔ E ADESSO SI DICHIARA CHE COSA E' USCITO, e non basta l'`md5` del
	#     binario: la domanda vera e' *«le due cure ci sono dentro?»*.  Un
	#     binario che compila e non le ha e' esattamente il caso che questo
	#     terreno esiste per escludere (⇒ il riquadro in testa).  Si cercano le
	#     stringhe che SOLO le cure nuove mettono nell'eseguibile.
	log "3 · L'impronta del binario, e la MARCA delle due cure dentro"
	ssh -o BatchMode=yes "$MACCHINA" "md5sum $ALBERO/src/remotix" | sed 's/^/        /'
	for m in "linea-morta %s causa=" "LINEA MORTA — la connessione QUIC si chiude" \
	         "causa=%s stallo_ms=" "soglia_stallo_ms=" "usciti_byte=" \
	         "SFRATTO per silenzio:" "SFRATTO NEGATO:" "--linea-morta-stallo-ms" \
	         "--sfratto-ms"; do
		N=$(ssh -o BatchMode=yes "$MACCHINA" \
			"grep -ac -- '$m' $ALBERO/src/remotix 2>/dev/null || echo 0")
		if [ "${N:-0}" = "0" ]; then
			ko "⛔ la marca «$m» NON e' nel binario: la cura non c'e'"
			exit 2
		fi
		ok "marca presente: «$m»"
	done

	# ⛔⛔⭐ E L'OPZIONE TOLTA SI VERIFICA **BATTENDOLA**, non cercandola.
	#
	#      `--linea-morta-permille` e' stata tolta il 23 agosto 2026 dopo che
	#      questo banco l'aveva refutata, e un binario che la accettasse ancora
	#      sarebbe la cura VECCHIA — quella che dava rossi diversi sugli stessi
	#      numeri.  ⇒ Va verificato.
	#
	# ⛔⛔ MA NON CON UN `grep` SUL BINARIO, e ci sono cascato: `[M]` 23 ago
	#      2026, il primo giro di questo controllo ha dato ROSSO su un binario
	#      GIUSTO.  La stringa c'e' eccome — sta nel **testo d'aiuto**, dove
	#      `main.c` spiega perche' l'opzione non esiste piu'.  ⇒ Cercare
	#      l'assenza di una stringa risponde a «e' scritta da qualche parte?»
	#      e non a «viene ACCETTATA?», che e' l'unica domanda che conta.
	#      ⚠ E' la forma di `LEZIONI.md` §1.9: un controllo che risponde a una
	#        domanda diversa da quella che credi.
	#
	# ⇒ Si BATTE l'opzione e si guarda che il binario la RIFIUTI: aiuto in
	#   uscita e codice diverso da zero.  ⚠ Porta 7999 e nessun certificato: il
	#   rifiuto arriva nel giro degli argomenti, prima di aprire qualunque cosa.
	B2LIB=/srv/src/b2/ngtcp2/build/lib:/srv/src/b2/prefisso/lib
	RC=$(ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'LD_LIBRARY_PATH=$B2LIB $DENTRO_ALB/src/remotix --linea-morta-permille 50 \
		  --porta 7999 >/dev/null 2>&1; echo \$?'" | tail -1 | tr -d '\r')
	if [ "${RC:-0}" = "0" ]; then
		ko "⛔⛔ il binario ACCETTA «--linea-morta-permille» (uscita $RC): questa e'"
		ko "     la cura VECCHIA, quella refutata.  NON misuro."
		exit 2
	fi
	ok "⭐ «--linea-morta-permille» viene RIFIUTATA (uscita $RC): e' la cura NUOVA"
	exit 0 ;;
utente)
	# ⛔ Prima il mio, con `07-b64-terreno.sh` (che sa gia' farlo)…
	bash "$QUI/banchi/07-b64-terreno.sh" utente || exit 2
	# …e poi il SECONDO, che quello script non sa fare.
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' env \
		 UTENTE2=$UTENTE2 UID_B2=$UID_B2 PAROLA_UTENTE2=$PAROLA_UTENTE2 LAV=$LAV \
		 bash $ALBERO/banchi/09-b81-terreno.sh --sul-server utente2"
	exit $? ;;
*)
	# ⛔ Tutto il resto e' `07-b64-terreno.sh`, con il MIO ambiente esportato:
	#    non se ne riscrive una riga.
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
esac
