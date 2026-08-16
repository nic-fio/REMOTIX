#!/bin/bash
#
# 06-b33-lancia.sh — ⛔⛔ IL RIATTACCO CHE COMANDA.  Sottofase 6.1 della fase 6.
#
#   ⚠ GIRA SUL SERVER (192.168.0.2), come utente `nicfio`, NON da root e NON
#     dentro il contenitore: e' lui che chiama tutte e due le cose.
#
#   bash 06-b33-lancia.sh <file-parola-sudo> tutto
#   bash 06-b33-lancia.sh <file-parola-sudo> testimone   la finestra Wayland
#   bash 06-b33-lancia.sh <file-parola-sudo> terminale   ⭐ l'applicazione VERA
#   bash 06-b33-lancia.sh <file-parola-sudo> tenuto      ⛔ la scena cattiva
#   bash 06-b33-lancia.sh <file-parola-sudo> cura        ⭐ la cura, simulata
#   bash 06-b33-lancia.sh <file-parola-sudo> quattro     le righe della fase 4
#
# ===========================================================================
# ⛔ L'ATTESO, DICHIARATO PRIMA — `CODER.md` §3.3
# ===========================================================================
#
#  A1  ATTACCA 1264x800  →  `SESSIONE` concede **1264x800**, lati pari
#  A2  al RIATTACCO, ATTACCA 1000x640  →  `SESSIONE` concede **1264x800**,
#      cioe' la tela che il PALCO ha gia' (`rcp.c:2177-2205`, I4) — ⛔ NON la
#      chiesta.  Fotogrammi scartati: **0**
#  A3  `ADATTA_TELA(1000x640)`  →  `TELA(esito=1 ADATTATA, 1000x640)`
#  A4  il testimone DENTRO la sessione scrive **`RITELA` 1264x800 → 1000x640**
#  A5  `ricambi_puntatore` ≥ 1 e `ricambi_tastiera` **= 0** — `[R]`
#      `meta-eis-client.c:197-206`, `remove_viewport_devices` guarda solo TOUCH
#      e POINTER_ABSOLUTE, e la tastiera non e' ne' l'uno ne' l'altro
#  A6  e DOPO il riattacco il testimone vede: il puntatore alle coordinate
#      **esatte**, `KEY_ENTER` giu' e su, `KEY_A` (cioe' la `LETTERA` «a», che
#      prova che la disposizione e' stata riletta), `BTN_LEFT` giu' e su
#
# ⭐ E L'IPOTESI CHE QUESTO BANCO PARTE PER SMENTIRE e' **A6**: *«il riattacco
#   riaggancia i dispositivi e tutto funziona»*.  Se fosse falsa, l'applicazione
#   aperta prima dello stacco non riceverebbe piu' niente — `[M]` 10 agosto
#   2026, banco S7: *«testimone prima dell'iniettore ⇒ non arriva NIENTE»*.
#
# ===========================================================================
# ⛔⛔ IL LIMITE, IN TESTA PERCHE' NESSUNO CI CADA IN VERDE
# ===========================================================================
#
# **In questo banco non c'e' nessun browser e nessun Xvfb.**  Il testimone e'
# una finestra Wayland nativa e il cliente e' un QUIC nativo.
#
#   ⇒ `LEZIONI.md` §1.15 — *su Xvfb `requestAnimationFrame` non gira MAI, e in
#     Blink l'evento `resize` si consegna dentro il giro di rendering* — **non
#     tocca** nessuna misura di qui: nessun cammino misurato passa da un quadro.
#   ⇒ ⛔ **E per la stessa ragione questo banco NON PUO' DIRE NIENTE** sulla
#     scala di disegno del client, su `imageRendering: pixelated`, ne' sul
#     cammino della pagina che insegue la finestra.  Quelli vivono nel browser
#     e sono della sottofase **6.5**: chi cercasse qui la loro rimisura
#     troverebbe un silenzio, e il silenzio non e' un verde.
#
# ⭐ **Si giudica prima il palco**: se il testimone non ha visto nemmeno una
#   riga, o se non c'e' stato nessun `RITELA`, il giudice dice «IL BANCO, NON IL
#   PRODOTTO» invece di accusare `input.c`.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
PAROLA_SUDO=${1:?serve il file 0600 con la parola di sudo}
COSA=${2:-tutto}

SRC=${SRC:-/media/REMOTIX/src/06-i-src}
DENTRO=${DENTRO:-/srv/src/06-i-src}
LAV=${LAV:-/media/REMOTIX/tmp/06-i}
LAV_D=${LAV_D:-/srv/remotix/tmp/06-i}
T=$SRC/banchi/06-b33-terreno.sh
ESITI=$LAV/06-b33-esiti.jsonl
TELA_A=${TELA_A:-1264x800}
TELA_B=${TELA_B:-1000x640}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; ESITO=1; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ESITO=0

[ -r "$PAROLA_SUDO" ] || { ko "⛔ $PAROLA_SUDO non si legge"; exit 2; }

sudo_mio() { printf '%s\n' "$(cat "$PAROLA_SUDO")" | sudo -S -p 'Password: ' "$@"; }
dentro()   { printf '%s\n' "$(cat "$PAROLA_SUDO")" | bash /media/REMOTIX/enter.sh "$@"; }

cliente() { # $1 = etichetta · $2 = modo|attacco · $3 = scena
	if [ "$2" = attacco ]; then
		dentro "cd $DENTRO/banchi && python3 06-b33-cliente.py --porta 7781 \
			--parola-file $LAV_D/parola --lavoro $LAV_D --tela-a $TELA_A \
			--tela-b $TELA_B --etichetta $1 --solo attacco --prima 6 \
			--scena '$3'"
	else
		dentro "cd $DENTRO/banchi && python3 06-b33-cliente.py --porta 7781 \
			--parola-file $LAV_D/parola --lavoro $LAV_D --tela-a $TELA_A \
			--tela-b $TELA_B --etichetta $1 --modo $2 --prima 5 --pausa 3 \
			--dopo 5 --scena '$3'"
	fi
}

# ⚠ Ogni misura di tempo porta accanto il CARICO: cinque banchi girano sulla
#   stessa macchina, e un numero preso sotto carico e non dichiarato tale e' un
#   numero falso (documento di fase §0-bis).
carico() { sudo_mio bash "$T" carico | sed 's/^/        /'; }

# ⛔ La scena si rimonta da capo: server spento e riacceso (che e' anche l'unica
#    cosa che sblocca il conto dei pulsanti del posto, se un giro «tenuto»
#    l'aveva lasciato giu'), palco fatto nascere alla tela A, e SOLO ALLORA si
#    apre l'applicazione — che e' il punto 3 del mandato.
rimonta() {
	sudo_mio bash "$T" spegni  > /dev/null 2>&1
	sleep 2
	sudo_mio bash "$T" accendi > /dev/null 2>&1 || { ko "il server non si accende"; return 3; }
	cliente rim-nasc attacco "nascita del palco alla tela $TELA_A" > /dev/null 2>&1
	return 0
}

case "$COSA" in
testimone|tenuto|cura)
	MODO=$COSA; [ "$COSA" = testimone ] && MODO=comanda
	log "La scena: testimone Wayland APERTO PRIMA dello stacco · modo $MODO"
	carico
	rimonta || exit 3
	sudo_mio bash "$T" testimone "$TELA_A" || { ko "⛔ IL BANCO: il testimone non si apre"; exit 3; }
	ok "l'applicazione e' APERTA, e nessun client e' attaccato"
	cliente "b33-$COSA" "$MODO" \
		"testimone Wayland aperto PRIMA dello stacco, modo $MODO"
	sudo_mio python3 "$SRC/banchi/06-b33-giudice.py" --visto "$LAV/visto.jsonl" \
		--registro "$LAV/registro.log" --da 5 --modo "$MODO" \
		--etichetta "b33-$COSA" --tela-b "$TELA_B" --esiti "$ESITI" \
		--scena "testimone Wayland aperto prima dello stacco"
	carico
	exit $ESITO ;;

terminale)
	# ⛔⛔ L'APPLICAZIONE VERA, e non il nostro strumento: un `gnome-terminal`
	#     col ciclo che il documento di fase nomina per esteso.  Ogni `Invio`
	#     che ARRIVA AL DESKTOP scrive una riga in nanosecondi.
	#
	# ⭐ Vale piu' del testimone Wayland per una ragione sola, ed e' quella che
	#   il mandato chiede: il testimone e' un cliente che abbiamo scritto noi e
	#   che si apre a schermo intero prendendo il fuoco; questo e'
	#   un'applicazione qualunque, con dentro una shell, che nessuno riavviera'.
	log "La scena: il TERMINALE aperto PRIMA dello stacco — l'applicazione vera"
	carico
	rimonta || exit 3
	sudo_mio bash "$T" testimone-via > /dev/null 2>&1
	sudo_mio bash "$T" terminale || { ko "⛔ IL BANCO: il terminale non si apre"; exit 3; }
	PRIMA=$(sudo_mio bash "$T" invii | awk '{print $2}')
	inf "Invio ricevuti PRIMA del giro: $PRIMA"
	cliente b33-terminale comanda \
		"gnome-terminal col ciclo read aperto PRIMA dello stacco"
	sleep 2
	DOPO=$(sudo_mio bash "$T" invii | awk '{print $2}')
	inf "Invio ricevuti DOPO il giro: $DOPO"
	# ⛔ Il cliente manda DUE `KEY_ENTER` giu'+su dopo il riattacco.  ⚠ E il
	#    conto e' una DIFFERENZA su un contatore che ha gia' dimostrato di
	#    contare, non «ho trovato delle righe».
	if [ "$((DOPO - PRIMA))" -ge 2 ]; then
		ok "⭐ l'applicazione APERTA PRIMA ha ricevuto $((DOPO - PRIMA)) Invio DOPO il riattacco"
	else
		ko "⛔ ne ha ricevuti $((DOPO - PRIMA)) invece di 2: l'input non arriva "
		ko "   alle applicazioni gia' aperte dopo il ricambio dei dispositivi"
	fi
	carico
	exit $ESITO ;;

quattro)
	# ⭐ LA RIMISURA DELLE QUATTRO RIGHE DELLA FASE 4, sotto questa fase e con
	#    questa scena.  ⛔ E la seconda **non si puo' rimisurare qui**: si dice.
	log "Le quattro righe della fase 4, rimisurate"
	carico
	R=$LAV/registro.log

	inf "1. la tela concordata all'ATTACCO (atteso: la misura chiesta, lati pari)"
	grep -o 'sessione aperta utente=[^ ]* via=[^ ]* tela=[0-9]*x[0-9]*' "$R" \
		| tail -3 | sed 's/^/        /'

	inf "2. la scala di DISEGNO del client e «pixelated»"
	echo "        ⛔ NON RIMISURABILE QUI: e' una proprieta' della PAGINA, e in"
	echo "           questo banco non c'e' nessun browser.  E' della sottofase 6.5."
	echo "        ⭐ Quel che si puo' rimisurare e' la META' che e' del SERVER —"
	echo "           la scala del monitor che montiamo, da cui quella dipende:"
	grep -o 'guardia 2[^·]*' "$R" | tail -2 | sed 's/^/        /'
	grep -o 'scala [^ ]* su «Meta-[0-9]*»' "$R" | tail -2 | sed 's/^/        /'

	inf "3. il RIATTACCO a misura diversa (atteso: SESSIONE concede quella del palco, 0 scartati)"
	grep -o 'RIPIEGO DICHIARATO (§4.5): chiesta la tela [0-9x]* .* CONCESSA quella del palco' "$R" \
		| tail -2 | sed 's/^/        /'
	grep -o 'spediti [0-9]*, abbandonati [0-9]*' "$R" | tail -1 | sed 's/^/        /'

	inf "4. il RIDIMENSIONAMENTO a caldo (era 6 ms dalla risposta del palco alla chiave)"
	# ⛔ I due confini si stampano tutti e due, e si dice quale e' quale: il
	#    numero della fase 4 e' il secondo, e chi confrontasse il primo
	#    troverebbe un peggioramento che non c'e'.
	echo "        confine A — ADATTA_TELA ricevuto → TELA spedita (tutto il giro):"
	grep -E 'ADATTA_TELA .* GIRATA al palco|TELA spedita' "$R" | tail -6 | sed 's/^/          /'
	echo "        confine B — «TELA NUOVA DAL PALCO» → «TELA spedita» (il numero della fase 4):"
	grep -E 'TELA NUOVA DAL PALCO|TELA spedita' "$R" | tail -4 | sed 's/^/          /'
	carico
	exit 0 ;;

tutto)
	bash "$0" "$PAROLA_SUDO" testimone
	bash "$0" "$PAROLA_SUDO" terminale
	bash "$0" "$PAROLA_SUDO" tenuto
	bash "$0" "$PAROLA_SUDO" cura
	bash "$0" "$PAROLA_SUDO" quattro
	exit 0 ;;

*)
	echo "⛔ non so fare «$COSA»"; exit 2 ;;
esac
