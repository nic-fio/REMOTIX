#!/usr/bin/env bash
#
# ===========================================================================
# 07-b64-terreno — il terreno dell'agente A8: utente `provar7`, albero,
#                  server sulla 7801.
# ===========================================================================
#
# ⛔ ISOLAMENTO, e per questo banco vale doppio perche' tocca la RETE:
#      porta **7801** · albero `/media/REMOTIX/src/07-r-src` ·
#      lavoro `/media/REMOTIX/tmp/07-r` · utente **provar7** (uid 1018) ·
#      unita' `remotix-7801.service`, ban-file, socket e certificati propri.
#
#    ⛔⛔ NON SI TOCCANO: la **7700**, la **7730** (il server dell'utente, ed e'
#         acceso) e l'utente **`prova`**.  Il ban di §4.4-bis e' per INDIRIZZO e
#         dura 12 ore: un banco che lo fa scattare mette fuori uso tutti gli
#         altri, perche' partono tutti dallo stesso indirizzo.
#
# ⛔ D12 — la parola d'ordine non passa MAI dalla riga di comando: si scrive in
#    un file `0600` e la si da' a `chpasswd` sullo stdin.
#
# ⛔ Il gruppo **`render`**: senza, la sessione grafica non apre il nodo DRM e
#    il sintomo e' «il desktop non parte», che assomiglia a dieci altre cose.
#
# ⛔ `enable-linger`, o il gestore d'utente muore con l'ultima sessione logind e
#    `/run/user/<uid>` sparisce sotto i piedi di PipeWire.
#
# Uso (dal portatile):
#     bash banchi/07-b64-terreno.sh utente
#     bash banchi/07-b64-terreno.sh porta          # sorgenti + compila
#     bash banchi/07-b64-terreno.sh accendi
#     bash banchi/07-b64-terreno.sh spegni
#     bash banchi/07-b64-terreno.sh stato
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7801}
UTENTE=${UTENTE:-provar7}
UID_B=${UID_B:-1018}
PAROLA_UTENTE=${PAROLA_UTENTE:-r7-audio-2026}
ALBERO=${ALBERO:-/media/REMOTIX/src/07-r-src}
LAV=${LAV:-/media/REMOTIX/tmp/07-r}
DENTRO_ALB=${DENTRO_ALB:-/srv/src/07-r-src}
DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/07-r}
UNITA=${UNITA:-remotix-$PORTA}

# ⛔ Le porte che NON sono mie: si CONTANO prima e dopo, e non si toccano mai.
VICINE="7700 7710 7720 7730"

log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

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
# LA META' CHE GIRA SULLA MACCHINA DI PROVA, DA ROOT
# ═══════════════════════════════════════════════════════════════════════════
if [ "${1:-}" = "--sul-server" ]; then
	PASSO=${2:-stato}
	[ "$(id -u)" -eq 0 ] || { ko "⛔ «--sul-server» va eseguito DA ROOT"; exit 2; }
	mkdir -p "$LAV" 2>/dev/null

	vicini() {
		local r="" p
		for p in $VICINE; do r="$r$p:$(ss -tuln 2>/dev/null | grep -c ":$p\b") "; done
		printf '%s— ascoltatori NON miei (si contano, non si toccano)' "$r"
	}

	case "$PASSO" in
	utente)
		log "L'utente del banco: $UTENTE (uid $UID_B)"
		inf "$(vicini)"
		C_ERA_GIA=no
		if id "$UTENTE" >/dev/null 2>&1; then
			C_ERA_GIA=si
			ok "c'e' gia' — non lo rifaccio"
		else
			useradd -m -u "$UID_B" -s /bin/bash "$UTENTE" || {
				ko "⛔ useradd non e' riuscito"; exit 2; }
			ok "creato"
		fi
		# ⛔ D12: la parola in un file 0600, mai in argv.  `chpasswd` la legge
		#    dallo stdin, e il file lo cancelliamo subito dopo.
		#
		# ⛔⛔ E NON SI RIFA' A UN UTENTE CHE ESISTE GIA' — 25 agosto 2026.
		#
		#   `[M]` In fase 10 gli utenti sono CONDIVISI fra piu' banchi, e questo
		#   passo riscriveva la parola a ogni chiamata: l'ultimo che chiamava
		#   `utente` vinceva, e gli altri leggevano «credenziali errate» su una
		#   macchina sana.
		#   ⛔⛔ E ogni respinto consuma uno dei TRE tentativi del ban per
		#     INDIRIZZO (`RCP.md` §4.4-bis), che dura DODICI ORE e mette fuori
		#     uso ogni altro banco che parta da qui.
		#
		#   ⇒ Se l'utente c'era gia', la parola NON si tocca.  Chi ha davvero
		#     bisogno di riposarla lo chiede: `RIFAI_PAROLA=1`.
		if [ "${C_ERA_GIA:-no}" = si ] && [ "${RIFAI_PAROLA:-0}" != 1 ]; then
			ok "⭐ parola NON toccata: l'utente c'era gia' (RIFAI_PAROLA=1 per forzare)"
		else
			( umask 077; printf '%s:%s\n' "$UTENTE" "$PAROLA_UTENTE" > "$LAV/.chp" )
			chmod 600 "$LAV/.chp"
			chpasswd < "$LAV/.chp" || { ko "⛔ chpasswd fallito"; rm -f "$LAV/.chp"; exit 2; }
			rm -f "$LAV/.chp"
			ok "parola d'ordine posta (dallo stdin, mai in argv — D12)"
		fi
		# ⛔ Qui c'erano i due nomi INCHIODATI e nessuna rilettura.
		gruppi_scheda_dai_a "$UTENTE" || exit 3
		ok "gruppi: $(id -nG "$UTENTE")"
		loginctl enable-linger "$UTENTE" || { ko "⛔ enable-linger fallito"; exit 2; }
		ok "linger acceso: /run/user/$UID_B vivra' anche senza nessuno collegato"
		ls -ld "/run/user/$UID_B" 2>&1 | sed 's/^/        /'
		# La parola che serve al cliente, in un file 0600 dentro il lavoro.
		( umask 077; printf '%s\n' "$PAROLA_UTENTE" > "$LAV/parola" )
		chmod 600 "$LAV/parola"
		ok "la parola sta in $LAV/parola, 0600 (il cliente la legge con --parola-file)"
		exit 0 ;;

	accendi)
		log "Il server del banco, sulla $PORTA — unita' $UNITA.service"
		inf "$(vicini)"
		mkdir -p "$LAV/certificati" "$LAV/rilievo"; chmod 1777 "$LAV/rilievo"
		chmod 755 "$LAV"   # ⚠ `provar7` deve poter leggere il file del tono
		: > "$LAV/registro.log"

		B2=/media/REMOTIX/src/b2
		export LD_LIBRARY_PATH="$B2/ngtcp2/build/lib:$B2/prefisso/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
		# ⛔ La trappola 1 di `riavvia-7700.sh`: senza questo controllo il binario
		#    prende la ngtcp2 di sistema, parte benissimo e ABORTA al primo che
		#    si collega.  Si verifica PRIMA di accendere.
		MANCA=$(ldd "$ALBERO/src/remotix" | grep -E 'ngtcp2|nghttp3' | grep -vc "$B2" || true)
		if [ "$MANCA" != "0" ]; then
			ko "⛔ NON parto: ngtcp2/nghttp3 non verrebbero da $B2 —"
			ldd "$ALBERO/src/remotix" | grep -E 'ngtcp2|nghttp3' | sed 's/^/        /'
			exit 2
		fi
		ok "ldd: ngtcp2 e nghttp3 vengono da $B2"

		systemctl stop "$UNITA.service" 2>/dev/null
		systemctl reset-failed "$UNITA.service" 2>/dev/null
		i=0
		while ss -uln 2>/dev/null | grep -q ":$PORTA " && [ $i -lt 50 ]; do i=$((i+1)); sleep 0.2; done

		# ⛔ Unita' di SISTEMA, non `setsid` da questa ssh: `pam_systemd` non
		#    crea una seconda sessione di logind per il figlio e `/run/user/<uid>`
		#    non esiste — trappola 4 di `riavvia-7700.sh`.
		# ⛔ E le DUE proprieta' che questo banco misura: `LimitRTPRIO=20` e
		#    `LimitNICE=-11`.  ⚠ Si possono togliere dal lanciatore
		#    (SENZA_RT=1) — ed e' il controllo positivo di R26.
		# ⭐ `RTPRIO=` si puo' cambiare dal lanciatore, ed e' l'A/B di R26: 20 e'
		#    quel che l'unita' concede oggi, 95 e' quel che PipeWire vorrebbe.
		RT_PROP=(--property=LimitRTPRIO=${RTPRIO:-20} --property=LimitNICE=-11)
		if [ "${SENZA_RT:-0}" = 1 ]; then
			RT_PROP=(--property=LimitRTPRIO=0)
			inf "⛔ SENZA_RT=1: l'unita' NON concede il tempo reale (controllo di R26)"
		fi
		inf "l'unita' concede LimitRTPRIO=${SENZA_RT:+0}${RTPRIO:-20}"
		# ⭐ `--parlantina`: il figlio senza parlantina TACE IN SILENZIO.
		# shellcheck disable=SC2086
		systemd-run \
			--unit="$UNITA" --collect --description="REMOTIX, banco 07-b64 (A8)" \
			--working-directory="$ALBERO/src" \
			--setenv=LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
			--property=StandardOutput=append:$LAV/registro.log \
			--property=StandardError=append:$LAV/registro.log \
			--property=KillMode=mixed \
			"${RT_PROP[@]}" \
			"$ALBERO/src/remotix" \
			--indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
			--certificati "$LAV/certificati" \
			--pagina "$ALBERO/src/pagina.html" \
			--ban-file "$LAV/ban" \
			--comando-socket "$LAV/comando.sock" \
			--rilievo "$LAV/rilievo" \
			${OPZIONI_SERVER:-} \
			--parlantina >/dev/null || { ko "⛔ systemd-run ha rifiutato"; exit 2; }

		i=0; PID=0
		while [ $i -lt 50 ]; do
			PID=$(systemctl show -p MainPID --value "$UNITA.service" 2>/dev/null || echo 0)
			[ "$PID" != "0" ] && [ -n "$PID" ] && break
			i=$((i+1)); sleep 0.1
		done
		if [ "$PID" = "0" ] || [ -z "$PID" ]; then
			ko "⛔ il server non e' partito — le ultime righe:"
			tail -20 "$LAV/registro.log" | sed 's/^/        /'
			exit 2
		fi
		ok "server $PID sulla porta $PORTA"
		# ⛔⛔ E I LIMITI SI LEGGONO DOPO L'`exec`, NON APPENA C'E' UN PID.
		#
		#     `[M]` 21 agosto 2026, e il banco ha mentito due volte prima che me
		#     ne accorgessi: `systemctl show -p MainPID` pubblica il pid **della
		#     forcata**, e i rlimit dell'unita' li applica quel figlio subito
		#     PRIMA di `execve`.  ⇒ Chi legge `/proc/PID/limits` in quella
		#     finestra vede i limiti di **systemd**, cioe' `0 0`, e scrive
		#     «l'unita' non concede il tempo reale» su un'unita' che lo concede.
		#     ⚠ E' un rosso su codice giusto, la forma di `LEZIONI.md` §2.3.
		#
		# ⇒ Si aspetta che il pid sia DAVVERO il nostro binario, e solo allora
		#   si legge.  ⭐ E se non lo diventa, lo si dichiara invece di leggere
		#   quel che capita.
		i=0
		while [ $i -lt 50 ]; do
			case "$(readlink -f "/proc/$PID/exe" 2>/dev/null)" in
			*/remotix) break ;;
			esac
			i=$((i+1)); sleep 0.1
		done
		if [ $i -ge 50 ]; then
			ko "⚠ dopo 5 s /proc/$PID/exe non e' ancora «remotix»: NON leggo i limiti"
		else
			grep -E 'Max realtime|Max nice' "/proc/$PID/limits" | sed 's/^/        LIM /'
		fi
		# ⛔⛔ E «ACCESO» VUOL DIRE CHE QUALCUNO ASCOLTA — 25 agosto 2026.
		#
		#   `[M]` Con un'opzione che il binario non conosce, il server stampa la
		#   propria guida ed esce: `systemd-run` ha gia' pubblicato un MainPID,
		#   e questo passo diceva «OK server 1265806 sulla porta 8260» **uscendo
		#   ZERO**, con l'unita' gia' `inactive/success` e **nessun ascoltatore**.
		#
		#   ⛔ Un banco che si fidasse di quell'uscita direbbe «acceso», poi «la
		#     tabella non si riempie», e finirebbe per ACCUSARE IL PRODOTTO di un
		#     difetto che era **un'opzione inesistente**.  E' «silenzio invece di
		#     rosso» (`LEZIONI.md` §1.29) un piano piu' su: nel terreno.
		#
		# ⇒ Il terreno non dichiara acceso finche' non vede un ASCOLTATORE sulla
		#   porta.  Se non c'e', si stampano le ultime righe del registro — che
		#   sono quelle che dicono **perche'** — e si esce ROSSI.
		i=0
		while [ $i -lt 50 ]; do
			ss -uln 2>/dev/null | grep -q ":$PORTA " && break
			i=$((i+1)); sleep 0.1
		done
		if [ $i -ge 50 ]; then
			ko "⛔⛔ NESSUNO ASCOLTA sulla $PORTA dopo 5 s: il server NON e' acceso"
			inf "unita': $(systemctl is-active "$UNITA.service" 2>/dev/null) · le ultime righe:"
			tail -25 "$LAV/registro.log" | sed 's/^/        /'
			exit 2
		fi
		ok "⭐ qualcuno ascolta sulla $PORTA — questo, non il pid, e' «acceso»"
		inf "$(vicini)"
		exit 0 ;;

	sblocca)
		log "Lo sblocco dell'indirizzo — §4.4-bis"
		bash /media/REMOTIX/enter.sh --root \
			"python3 $DENTRO_ALB/banchi/01-b8-sblocca.py --socket $DENTRO_LAV/comando.sock $IND"
		inf "sblocco di $IND: uscita $?"
		exit 0 ;;

	spegni)
		log "Spengo $UNITA.service (e SOLO quella)"
		systemctl stop "$UNITA.service" 2>/dev/null
		systemctl reset-failed "$UNITA.service" 2>/dev/null
		ok "spento · $(vicini)"
		exit 0 ;;

	*)
		log "Stato"
		inf "$(vicini)"
		inf "unita': $(systemctl is-active "$UNITA.service" 2>/dev/null)"
		inf "carico: $(uptime | sed 's/.*average/media/')"
		exit 0 ;;
	esac
fi

# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE GIRA SUL PORTATILE
# ═══════════════════════════════════════════════════════════════════════════
QUI=$(cd "$(dirname "$0")/.." && pwd)
SUL_SERVER="bash $ALBERO/banchi/$(basename "$0") --sul-server"

# ⛔ Il copione remoto e' un FILE gia' sulla macchina, e `sudo -S` riceve solo
#    la parola: `printf … | sudo -S bash -s` darebbe a bash uno stdin vuoto, e
#    «non ha fatto niente» avrebbe la stessa faccia di «ha funzionato».
# ⛔ E niente `</dev/null` in coda: quel redirect vince su `sudo -S`, che allora
#    non legge piu' la parola («no password was provided»).
remoto() { ssh -o BatchMode=yes "$MACCHINA" \
	"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' env $1 $SUL_SERVER $2"; }

PASSO=${1:-stato}
case "$PASSO" in
porta)
	log "1 · Porto i sorgenti in $ALBERO"
	# ⛔ SENZA `sudo`: `printf … | sudo -S` mangerebbe lo stdin, che qui E' lo
	#    stream del `tar`.  E non serve: /media/REMOTIX/src e' di `nicfio`.
	# ⛔ Si porta anche `banchi/rcp`: il Makefile si rifiuta di compilare se non
	#    puo' confrontare le due copie di `rcp.c` (R12.3).
	# ⛔ E si ESCLUDONO oggetti e binario del portatile: spedendoli, `make`
	#    troverebbe tutto aggiornato e resterebbe il binario del portatile — la
	#    forma D5, «un binario stantio resta verde».
	tar -C "$QUI" --exclude='*.o' --exclude='src/remotix' -czf - \
		src banchi/rcp \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/07-b42-giudice.py \
		banchi/attrezzi-gruppi-scheda.sh banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py | \
		ssh -o BatchMode=yes "$MACCHINA" "mkdir -p $ALBERO && tar -C $ALBERO -xzf -" || {
		ko "⛔ i sorgenti non sono arrivati"; exit 2; }
	ok "sorgenti in $ALBERO"

	log "2 · Compilo dentro il contenitore"
	if ! ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
		  bash $DENTRO_ALB/src/costruisci.sh 2>&1 | tail -20'"; then
		ko "⛔ la compilazione e' fallita: NON accendo niente"
		exit 2
	fi
	ok "compilato"
	exit 0 ;;
utente)
	# ⛔ `RIFAI_PAROLA` DEVE ATTRAVERSARE L'ssh — 25 agosto 2026.
	#   La cura di stamattina (non rifare la parola a un utente che esiste
	#   gia') l'aveva messa nella meta' che gira SUL SERVER, ma la variabile
	#   non era in questo elenco: `RIFAI_PAROLA=1` non arrivava di la' e non
	#   faceva niente.  ⚠ E il modo in cui falliva e' il solito: nessun
	#   errore, nessuna riga, la parola semplicemente non veniva rifatta.
	remoto "UTENTE=$UTENTE UID_B=$UID_B PAROLA_UTENTE=$PAROLA_UTENTE LAV=$LAV RIFAI_PAROLA=${RIFAI_PAROLA:-0}" utente ;;
accendi)
	remoto "PORTA=$PORTA IND=$IND ALBERO=$ALBERO LAV=$LAV UNITA=$UNITA SENZA_RT=${SENZA_RT:-0} RTPRIO=${RTPRIO:-20} OPZIONI_SERVER='${OPZIONI_SERVER:-}'" accendi ;;
sblocca)
	remoto "IND=$IND DENTRO_ALB=$DENTRO_ALB DENTRO_LAV=$DENTRO_LAV" sblocca ;;
spegni)
	remoto "PORTA=$PORTA LAV=$LAV UNITA=$UNITA" spegni ;;
*)
	remoto "PORTA=$PORTA LAV=$LAV UNITA=$UNITA" stato ;;
esac
