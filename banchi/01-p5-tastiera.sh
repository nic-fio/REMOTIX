#!/bin/bash
#
# 01-p5-tastiera.sh — LA SONDA S3, e insieme LA CERTIFICAZIONE DELLA MECCANICA.
#
#   bash banchi/01-p5-tastiera.sh              i due motori
#   bash banchi/01-p5-tastiera.sh firefox      uno solo
#
# ⚠ GIRA DA QUESTA PARTE DEL FILO: i browser stanno sul portatile (`CHUWI`), non
#   sul server.  ⭐ E il bersaglio e' **FINTO**: una pagina servita da
#   127.0.0.1.  ⛔ Nessun byte di questo banco tocca il prodotto, e nessuna riga
#   di questo banco vale come misura del prodotto.
#
# ===========================================================================
# ⛔ I DUE MESTIERI, E VANNO TENUTI DISTINTI
#
#   1. **S3, la meta' che il portatile puo' dare** (`SPECIFICHE.md` §7.3-bis):
#      *che cosa si perde, motore per motore*.  ⚠ La meta' su DeX resta NON
#      MISURATA — e' l'uso primario, ci vuole il telefono, e «il Chrome del
#      portatile lo fa» non dice niente del Chrome del telefono: forma d'errore
#      **E10** (`DECISIONI.md` §5-bis.0-ter).
#
#   2. ⭐ **Il controllo positivo della meccanica di `01-p5-lancia.sh`**, che e'
#      il banco vero contro il prodotto e che oggi NON si puo' eseguire — il
#      binario del prodotto e' in ricostruzione.  `LEZIONI.md` §1.2: *il banco si
#      certifica prima della misura*.  Qui si certifica, contro un bersaglio
#      finto, che:
#
#        - i due browser si accendono su uno schermo finto e ci restano;
#        - `xdotool` scrive DENTRO la finestra giusta, sullo schermo giusto;
#        - il raccoglitore riceve e `01-p5-esiti.jsonl` si scrive.
#
#      ⛔ Senza questo, il giorno del giro vero un silenzio avrebbe **quattro**
#         cause indistinguibili — il server, la pagina, il browser, la tastiera
#         — e il rosso finirebbe sulla prima che viene in mente.
#
# ===========================================================================
# ⛔ I TRE STATI, E IL SECONDO NON SI VEDE DA DENTRO LA PAGINA
#
# §7.3-bis: *«consegnata · consegnata E RISERVATA · non consegnata»*, e *«la
# misura non e' arriva? ma arriva E BASTA?»*.  Dalla pagina si vede solo se la
# battuta e' arrivata.  Il secondo testimone e' qui fuori:
#
#     consegnata            la battuta arriva, e fuori non cambia niente
#     consegnata+riservata  la battuta arriva **e** il browser fa la sua —
#                           lo dicono le finestre contate da `xdotool` e gli
#                           eventi `blur`/`visibilitychange` della pagina
#     non consegnata        la battuta non arriva
#
# ===========================================================================
# ⛔ LA SCENA, DICHIARATA — e non e' quella dell'utente
#
#   schermo   Xvfb :79, 1280x1024x24, **senza gestore di finestre**
#   browser   NON `--headless`: la' Chrome si dichiara `HeadlessChrome/151`,
#             cioe' un motore con un altro nome (`[M]` 10 agosto 2026, B2)
#   profili   usa-e-getta, e si BUTTANO: il 10 agosto sei giri hanno lasciato
#             740 MB in /tmp e fermato un `git commit`
#
# ⚠ Senza gestore di finestre, `alt+Tab` e il tasto Meta non li intercetta
#   nessuno: quelle righe la sonda le marca `verdetto=0` e **non entrano nel
#   conto**.  Dichiararle e' meglio che ometterle — un vicolo cieco non
#   trascritto e' un vicolo cieco che si ripercorre.
# ===========================================================================
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
PORTA=${PORTA:-8855}
SCHERMO=${SCHERMO:-:79}
MISURA=${MISURA:-1280x1024}
REG=$QUI/01-p5-registro.py
T=$(mktemp -d)

# ⛔ OGNI RIGA DEL REGISTRO DICE CONTRO CHE COSA HA MISURATO — la convenzione di
#    `01-b0-bersaglio.py`.  Qui il bersaglio e' **finto**, e va scritto: senza,
#    queste righe e quelle del giro contro il prodotto starebbero nello stesso
#    file con la stessa forma e nessuno saprebbe quali sono quali.
export BERSAGLIO=finto-locale
export PORTA_BERSAGLIO=$PORTA

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

MOTORI=${1:-tutti}
ESITO=0
PID_X=
PID_RACC=
PID_BR=

congedo()
{
	[ -n "$PID_BR" ]   && { kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; }
	[ -n "$PID_RACC" ] && { kill "$PID_RACC" 2>/dev/null; wait "$PID_RACC" 2>/dev/null; }
	[ -n "$PID_X" ]    && { kill "$PID_X" 2>/dev/null; wait "$PID_X" 2>/dev/null; }
	rm -rf "$T"
}
trap congedo EXIT

X() { env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO "$@"; }

# ---------------------------------------------------------------------------
# ⛔ IL FUOCO SI DA' ALLA FINESTRA CHE PORTA LA PAGINA, NON ALLA PRIMA DELLA
#    CLASSE — e questa riga e' costata un giro intero.
#
# `[M]` 11 agosto 2026: `xdotool search --class firefox-esr` trova **nove**
# finestre su uno schermo con un solo Firefox — cornici, finestre di servizio,
# oggetti senza nome — e `windowactivate` prendeva la prima, che non e' quella
# del documento.  ⛔ Il banco batteva «a» dentro una finestra che non ascolta, e
# il controllo positivo diceva giustamente di no: senza di lui il giro avrebbe
# dichiarato che **Firefox si tiene tutte e trentadue le combinazioni**.
#
# ⭐ Il titolo del documento invece e' una cosa sola, e la portano tutt'e due i
#    motori nel nome della finestra: si cerca per NOME.  ⚠ Il titolo sta in un
#    posto solo — il `<title>` di `01-p5-tastiera.html` — e questa stringa ne e'
#    un pezzo: se cambia la', questa ricerca non trova piu' niente **e lo dice**,
#    invece di battere a caso.
TITOLO=${TITOLO:-sonda S3}
fuoco_alla_pagina()
{
	local viste
	viste=$(X xdotool search --name "$TITOLO" 2>/dev/null | wc -l)
	if [ "$viste" -eq 0 ]; then
		return 1
	fi
	X xdotool search --name "$TITOLO" windowactivate --sync >/dev/null 2>&1
	X xdotool search --name "$TITOLO" windowfocus --sync >/dev/null 2>&1
	return 0
}

# ---------------------------------------------------------------------------
log "1. Lo schermo finto, e si VERIFICA di che misura sia"
# ⛔ Rilievo A29 di S1b, applicato qui: «se esiste, uso quello» non basta.  Tre
#    banchi di questo progetto aprono uno Xvfb, e due usano numeri vicini
#    (:77 S1b, :78 S5): un giro rimasto appeso lascia li' uno schermo di
#    un'altra geometria, e `xdotool` batterebbe su una scena diversa da quella
#    dichiarata nel rapporto.  B0.1 vuole che lo stato iniziale si dichiari **e
#    si verifichi**.
if [ -e "/tmp/.X11-unix/X${SCHERMO#:}" ]; then
	DIM=$(X xdpyinfo 2>"$T/xdpy.err" | sed -n 's/^  dimensions: *\([0-9x]*\).*/\1/p' | head -1)
	if [ -z "$DIM" ]; then
		ko "⛔ lo schermo $SCHERMO risulta in uso e non so di che misura sia:"
		sed 's/^/        /' "$T/xdpy.err"
		ko "   «Non lo so» non si arrotonda a «va bene»."
		exit 2
	fi
	if [ "$DIM" != "$MISURA" ]; then
		ko "⛔ $SCHERMO e' acceso a $DIM e questo banco dichiara $MISURA."
		ko "   Chiudilo per PID (mai con pkill -f), o rilancia con SCHERMO=:80."
		exit 2
	fi
	inf "lo schermo $SCHERMO era gia' acceso, ed e' della misura dichiarata ($DIM)"
else
	Xvfb "$SCHERMO" -screen 0 "${MISURA}x24" >"$T/xvfb.log" 2>&1 &
	PID_X=$!
	sleep 2
	if [ ! -d "/proc/$PID_X" ]; then
		ko "Xvfb non e' partito:"
		sed 's/^/        /' "$T/xvfb.log"
		exit 2
	fi
	DIM=$(X xdpyinfo 2>/dev/null | sed -n 's/^  dimensions: *\([0-9x]*\).*/\1/p' | head -1)
	ok "schermo finto $SCHERMO acceso — chiesto $MISURA, letto ${DIM:-IGNOTO}"
	# ⛔ E si LEGGE, non si presume uguale a quel che si e' chiesto (S5, punto 2).
	if [ "$DIM" != "$MISURA" ]; then
		ko "⛔ ho chiesto $MISURA e leggo ${DIM:-niente}: la scena non e' quella"
		ko "   dichiarata, e un rapporto che dice $MISURA sarebbe falso"
		exit 2
	fi
fi
inf "⚠ e NON c'e' nessun gestore di finestre: alt+Tab e il tasto Meta non li"
inf "  intercetta nessuno.  Quelle righe si dichiarano e non si giudicano."

# ---------------------------------------------------------------------------
log "2. Il raccoglitore, su 127.0.0.1:$PORTA"
python3 -u "$QUI/01-p5-raccogli.py" "$PORTA" >"$T/racc.log" 2>&1 &
PID_RACC=$!
sleep 1
if [ ! -d "/proc/$PID_RACC" ]; then
	ko "il raccoglitore non e' partito:"
	sed 's/^/        /' "$T/racc.log"
	exit 3
fi
ok "raccoglitore in ascolto, PID $PID_RACC"

# ⛔ E IL SEGNAPOSTO SI VALIDA — difetto trovato al primo giro, 11 agosto 2026.
#
#    Questa riga diceva `python3 "$REG" righe 2>/dev/null || echo 0`.  Al primo
#    giro il registro non esisteva ancora: l'attrezzo stampava `0` **e usciva
#    non-zero**, quindi il `||` stampava un SECONDO `0`.  Il segnaposto valeva
#    «0\n0», `--da` non lo accettava, e ogni lettura successiva usciva in errore
#    — col banco che dichiarava «la pagina non e' nata» mentre la pagina era
#    viva e spediva `VIVA` ogni due secondi, sotto gli occhi di chi leggeva.
#
# ⭐ E' la settima veste di `LEZIONI.md` §1.9: il rosso puntato sull'imputato
#    sbagliato.  La cura sta in due posti — l'attrezzo adesso dice che un
#    registro inesistente ha zero righe (e non e' un guasto), e qui il valore
#    **si controlla che sia un numero** invece di fidarsi.
righe()
{
	local v
	v=$(python3 "$REG" righe 2>"$T/righe.err")
	case "$v" in
	''|*[!0-9]*)
		ko "⛔ il conto delle righe del registro non e' un numero («$v»):" >&2
		sed 's/^/        /' "$T/righe.err" >&2
		printf '%s\n' "-1"
		return 1
		;;
	esac
	printf '%s\n' "$v"
}

# ---------------------------------------------------------------------------
# prova_motore <nome> <binario> <comando...>
# ---------------------------------------------------------------------------
PROVATI=0
SALTATI=0
prova_motore()
{
	local nome=$1 binario=$2 classe=$3; shift 3
	log "3. $nome"
	if ! command -v "$binario" >/dev/null; then
		inf "⚠ $binario non c'e' su questa macchina: si salta, E SI DICE"
		SALTATI=$((SALTATI + 1))
		return 0
	fi
	# ⛔ La versione si LEGGE dal binario che sta per girare, non si copia da un
	#    documento: un numero copiato invece che letto e' la forma d'errore E5.
	#    ⚠ E resta detto che questa e' la versione del BINARIO: quella che il
	#      motore DICHIARA (userAgent) la scrive la pagina, e le due non
	#      coincidono per costruzione — Chrome riduce l'UA a `151.0.0.0`,
	#      Firefox ESR dichiara `140.0` dove il binario e' `140.13.0esr`.
	local versione
	versione=$("$binario" --version 2>&1 | head -1)
	inf "binario : $versione"
	PROVATI=$((PROVATI + 1))

	local giro="p5s3-$nome-$(date +%s)-$RANDOM"
	local url="http://127.0.0.1:$PORTA/01-p5-tastiera.html?giro=$giro"
	local n0
	n0=$(righe)
	mkdir -p "$T/$nome"
	X "$@" "$url" >"$T/$nome.log" 2>&1 &
	PID_BR=$!

	# ── La pagina e' nata? ────────────────────────────────────────────────
	# ⛔ IL DENOMINATORE, e qui morde: «nessuna battuta» ha due cause opposte —
	#    il browser non ha aperto la pagina, oppure l'ha aperta e la battuta non
	#    e' arrivata — e senza questo controllo hanno lo stesso aspetto.
	local i=0 pronta=""
	while [ "$i" -lt 30 ]; do
		pronta=$(python3 "$REG" cerca --giro "$giro" --da "$n0" --tipo PRONTA 2>/dev/null) && break
		sleep 1
		i=$((i + 1))
	done
	if [ -z "$pronta" ]; then
		ko "$nome non ha mai detto PRONTA in $i secondi: la pagina non e' nata"
		inf "richieste al raccoglitore: $(grep -c '^richiesta: ' "$T/racc.log")"
		tail -6 "$T/racc.log" | sed 's/^/        /'
		tail -5 "$T/$nome.log" | sed 's/^/        /'
		ESITO=1
		kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; PID_BR=
		return 1
	fi
	ok "la pagina e' nata e sa spedire (dopo $i s)"

	# Che cosa il motore espone — e' un dato, non un giudizio.
	python3 "$REG" cerca --giro "$giro" --da "$n0" --tipo API | sed 's/^/        /'

	# ── L'elenco viene DALLA PAGINA, non da qui ───────────────────────────
	if ! python3 "$REG" elenco --giro "$giro" --da "$n0" >"$T/$nome.elenco" 2>"$T/$nome.elenco.err"; then
		ko "⛔ la pagina non ha dichiarato il suo elenco: senza, questo banco"
		ko "   avrebbe una copia sua, e due elenchi che si disallineano sono due"
		ko "   misure diverse sotto la stessa etichetta"
		sed 's/^/        /' "$T/$nome.elenco.err"
		ESITO=1
		kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; PID_BR=
		return 1
	fi
	inf "combinazioni dichiarate dalla pagina: $(wc -l < "$T/$nome.elenco")"

	# ── Il fuoco alla finestra ────────────────────────────────────────────
	#
	# ⛔ E IL SECONDO TESTIMONE SI CERTIFICA PRIMA DI USARLO.  Le finestre
	#    contate da `xdotool` sono meta' della prova sul caso «consegnata E
	#    riservata»: se la classe non combacia il conto vale ZERO sempre, la
	#    differenza «prima→dopo» e' sempre nulla, e quel caso **non si puo'
	#    osservare** — un testimone muto che dichiara «non e' successo niente».
	#    ⚠ `[M]` 11 agosto 2026: la classe di Firefox su questa macchina e'
	#      `firefox-esr` (`Navigator` e' il NOME DELL'ISTANZA, che vuole
	#      `--classname`), e col valore sbagliato il banco ha trovato 0 finestre
	#      e non ha dato nessun verdetto — che e' la cosa giusta da fare, ma la
	#      causa la dice questa riga.
	X xdotool search --class "$classe" >"$T/$nome.finestre0" 2>/dev/null
	local quante_finestre
	quante_finestre=$(wc -l < "$T/$nome.finestre0")
	inf "finestre di «$classe» all'inizio: $quante_finestre"
	if [ "$quante_finestre" -eq 0 ]; then
		ko "⛔ nessuna finestra di classe «$classe» su $SCHERMO: il secondo"
		ko "   testimone e' muto, e senza di lui «consegnata E riservata» — il"
		ko "   peggiore dei tre stati di §7.3-bis — non si puo' distinguere da"
		ko "   «consegnata».  Nessun verdetto per questo motore."
		ESITO=1
		kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; PID_BR=
		return 1
	fi
	if ! fuoco_alla_pagina; then
		ko "⛔ nessuna finestra col titolo «$TITOLO» su $SCHERMO: non so a chi"
		ko "   dare il fuoco, e battere a caso non e' una misura."
		ESITO=1
		kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; PID_BR=
		return 1
	fi
	inf "fuoco dato alla finestra col titolo «$TITOLO» ($(X xdotool search --name "$TITOLO" 2>/dev/null | wc -l) trovata/e)"
	sleep 1

	# ⭐ IL CONTROLLO POSITIVO DELLA TASTIERA, e viene PRIMA di tutto il resto.
	#    Si batte una lettera che nessun browser si tiene: se non arriva, allora
	#    «non consegnata» di tutte le righe dopo vorrebbe dire «xdotool non
	#    scrive qui», e il banco dichiarerebbe che i motori si tengono tutto
	#    mentre il difetto e' nel pilota.  ⛔ Senza, ogni riga rossa e' ambigua.
	local n1
	n1=$(righe)
	X xdotool key --clearmodifiers a >/dev/null 2>&1
	sleep 2
	local prova
	prova=$(python3 "$REG" battuta --giro "$giro" --da "$n1" 2>/dev/null | tr '\t' ' ')
	if [ -z "$prova" ]; then
		ko "⛔ IL CONTROLLO POSITIVO DELLA TASTIERA NON PASSA: ho battuto «a» e"
		ko "   la pagina non l'ha vista.  Allora ogni «non consegnata» piu' sotto"
		ko "   direbbe «xdotool non scrive qui», non «il browser se la tiene»:"
		ko "   nessun verdetto si da'."
		ESITO=1
		kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; PID_BR=
		return 1
	fi
	ok "⭐ controllo positivo della tastiera: «a» arriva alla pagina — $prova"

	# ── Le combinazioni, una per volta ────────────────────────────────────
	local esiti=$T/$nome.esiti.tsv
	: >"$esiti"
	local idx xdo giudica distruttiva che
	local scena_persa=0
	while IFS=$'\t' read -r idx xdo giudica distruttiva che; do
		local n prima dopo battuta fuoco stato nA controllo
		# ── ⛔ IL CONTROLLO DI DESTINAZIONE, PRIMA DI OGNI BATTUTA ──────────
		#
		#    Terzo difetto trovato dalla certificazione, 11 agosto 2026, e il
		#    peggiore dei tre perche' produceva un ROSSO PLAUSIBILE.  Dopo
		#    `ctrl+t` Chrome apre una scheda nuova e il fuoco va li': le quattro
		#    combinazioni successive risultavano `NON-CONSEGNATA` — cioe' «il
		#    browser se le tiene» — mentre la verita' era che **la pagina non
		#    era piu' la destinataria di niente**.  Un rosso sull'imputato
		#    sbagliato (`LEZIONI.md` §1.9, settima veste), e per giunta sulle
		#    combinazioni piu' interessanti.
		#
		# ⭐ La cura e' il controllo positivo di §1.9 regola 2, ripetuto a ogni
		#    riga invece che una volta sola: si batte una lettera che nessun
		#    browser si tiene, e se non arriva **non si giudica**.  Costa un
		#    secondo per combinazione e toglie una colonna intera di falsi.
		# ⭐ E LA SCENA SI PROVA A RIPRENDERE, UNA VOLTA, PRIMA DI RINUNCIARE.
		#    `[M]` 11 agosto 2026: su Firefox `ctrl+Tab` cambia scheda davvero —
		#    e' il caso «consegnata E riservata» che §7.3-bis nomina per nome —
		#    e senza il recupero le venti combinazioni successive restavano
		#    NON-GIUDICABILI per colpa di quella prima.  ⚠ Il fatto che la scena
		#    fosse da riprendere resta scritto: e' la riga «riservata» di prima,
		#    non si perde.
		if [ "$scena_persa" -eq 0 ]; then
			nA=$(righe)
			X xdotool key --clearmodifiers a >/dev/null 2>&1
			sleep 1
			controllo=$(python3 "$REG" battuta --giro "$giro" --da "$nA" 2>/dev/null)
			if [ -z "$controllo" ]; then
				# ⛔ E IL RECUPERO E' A TRE MOSSE, PERCHE' LE SCENE PERSE SONO
				#    DI DUE SPECIE.  `[M]` 11 agosto 2026:
				#
				#      Chrome, `ctrl+t`   → una FINESTRA nuova sullo schermo:
				#                           il fuoco X la riporta indietro;
				#      Firefox, `ctrl+Tab`→ una SCHEDA nella stessa finestra:
				#                           ⛔ il fuoco X non serve a niente —
				#                           la finestra e' gia' quella giusta,
				#                           e la pagina e' dietro.  Ci vuole
				#                           una battuta di navigazione fra
				#                           schede.
				#
				#    ⚠ Le mosse di recupero sono battute anche loro, e due di
				#      esse sono nell'elenco: si danno FUORI dalla finestra di
				#      misura di ogni riga (prima del segnaposto `n`), quindi
				#      non entrano in nessun verdetto.  Dichiararlo e' quel che
				#      le rende innocue.
				local mossa
				# ⚠ `Escape` viene per primo, ed e' il caso di Firefox: con una
				#   sola scheda `ctrl+Tab` non cambia scheda — apre il pannello
				#   delle anteprime, che si prende il fuoco e che nessuna
				#   navigazione fra schede richiude.  Il `Tab` all'indietro e
				#   `ctrl+1` restano per il caso opposto (piu' schede davvero).
				for mossa in Escape FUOCO ctrl+shift+Tab ctrl+1 F6; do
					if [ "$mossa" = FUOCO ]; then
						fuoco_alla_pagina
					else
						X xdotool key --clearmodifiers "$mossa" >/dev/null 2>&1
					fi
					sleep 1
					nA=$(righe)
					X xdotool key --clearmodifiers a >/dev/null 2>&1
					sleep 1
					controllo=$(python3 "$REG" battuta --giro "$giro" --da "$nA" 2>/dev/null)
					[ -n "$controllo" ] && break
				done
				[ -z "$controllo" ] && scena_persa=1
			fi
		fi
		if [ "$scena_persa" -eq 1 ]; then
			printf '    \033[1;33m?\033[0m  %-16s %-24s %s\n' \
				"$xdo" "NON-GIUDICABILE" "la pagina non riceve piu': scena persa"
			printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
				"$idx" "$xdo" "NON-GIUDICABILE" 0 "—" "—" "$che" >>"$esiti"
			continue
		fi
		n=$(righe)
		prima=$(X xdotool search --class "$classe" 2>/dev/null | wc -l)
		X xdotool key --clearmodifiers "$xdo" >/dev/null 2>&1
		sleep 1
		dopo=$(X xdotool search --class "$classe" 2>/dev/null | wc -l)
		# ⛔ E LE COLONNE NON SI MESCOLANO — secondo difetto del primo giro.
		#    `battuta` torna una riga a TABULAZIONI (n, key, code, modificatori,
		#    cancelable), e finiva dentro un `printf` a tabulazioni: le colonne
		#    scivolavano di quattro posti, e nel registro il campo «che cosa fa
		#    questa combinazione» conteneva la lettera del tasto.  Le tabulazioni
		#    si spengono qui, dove nascono.
		battuta=$(python3 "$REG" battuta --giro "$giro" --da "$n" 2>/dev/null | tr '\t' ' ')
		fuoco=$(python3 "$REG" cerca --giro "$giro" --da "$n" --tipo FUOCO 2>/dev/null | tr '\t' ' ')
		# ── I tre stati di §7.3-bis ───────────────────────────────────────
		if [ -z "$battuta" ]; then
			stato=NON-CONSEGNATA
		elif [ "$prima" != "$dopo" ] || [ -n "$fuoco" ]; then
			stato=CONSEGNATA-E-RISERVATA
		else
			stato=CONSEGNATA
		fi
		printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
			"$idx" "$xdo" "$stato" "$giudica" "$prima→$dopo" \
			"${battuta:-—}" "$che" >>"$esiti"
		case "$stato" in
		CONSEGNATA)             printf '    \033[1;32m✓\033[0m  %-16s %-24s %s\n' "$xdo" "$stato" "$che" ;;
		CONSEGNATA-E-RISERVATA) printf '    \033[1;33m!\033[0m  %-16s %-24s %s\n' "$xdo" "$stato" "$che" ;;
		*)                      printf '    \033[1;31m·\033[0m  %-16s %-24s %s\n' "$xdo" "$stato" "$che" ;;
		esac
		# Dopo una distruttiva la pagina puo' non esserci piu': si rimette il
		# fuoco e si tira avanti, ma senza fingere che sia la stessa scena.
		if [ "$distruttiva" = 1 ]; then
			fuoco_alla_pagina
			sleep 1
		fi
	done < "$T/$nome.elenco"

	# ── La riga di registro di questo motore ──────────────────────────────
	python3 - "$REG" "$giro" "$nome" "$versione" "$esiti" "$SCHERMO" "$MISURA" <<'PY'
import json, subprocess, sys
reg, giro, motore, versione, esiti, schermo, misura = sys.argv[1:8]
righe = []
for r in open(esiti, encoding="utf-8"):
    c = r.rstrip("\n").split("\t")
    if len(c) >= 7:
        righe.append({"n": int(c[0]), "battuta": c[1], "stato": c[2],
                      "nel_verdetto": c[3] == "1", "finestre": c[4],
                      "vista_dalla_pagina": c[5], "che": c[6]})
giudicate = [r for r in righe if r["nel_verdetto"]]
conto = {}
for r in giudicate:
    conto[r["stato"]] = conto.get(r["stato"], 0) + 1
d = {
    "banco": "P5-S3", "giro": giro, "tipo": "VERDETTO-S3",
    "motore_binario": versione,
    "bersaglio": "FINTO — pagina locale su 127.0.0.1; nessun byte verso il prodotto",
    "scena": {"schermo": schermo, "misura": misura,
              "gestore_finestre": "NESSUNO — alt+Tab e Meta non sono rappresentativi"},
    "combinazioni_dichiarate": len(righe),
    "combinazioni_giudicate": len(giudicate),
    "conto": conto,
    "dettaglio": righe,
    "non_misurato": "la meta' su DeX e su Chrome per Android: manca il dispositivo (E10)",
}
subprocess.run([sys.executable, reg, "aggiungi", json.dumps(d, ensure_ascii=False)], check=True)
print(f"    --  giudicate {len(giudicate)} su {len(righe)} dichiarate: {conto}")
PY

	kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; PID_BR=
	sleep 1
	return 0
}

if [ "$MOTORI" = tutti ] || [ "$MOTORI" = chrome ]; then
	prova_motore chrome google-chrome chrome \
		google-chrome --ozone-platform=x11 --user-data-dir="$T/chrome" \
		--no-first-run --no-default-browser-check --disable-sync \
		--window-size=1280,1000
fi
if [ "$MOTORI" = tutti ] || [ "$MOTORI" = firefox ]; then
	prova_motore firefox firefox firefox-esr \
		firefox --no-remote --profile "$T/firefox" --width 1280 --height 1000
fi

# ---------------------------------------------------------------------------
log "Esito"
inf "motori provati: $PROVATI — saltati: $SALTATI"
# ⛔ «Tutti quelli provati sono andati bene» e' vero anche quando i provati sono
#    zero: e' la forma di verde piu' vuota che ci sia (`LEZIONI.md` §1.9,
#    regola 6).  Anche un verdetto ha un denominatore.
if [ "$PROVATI" -eq 0 ]; then
	ko "⛔ NESSUN motore provato: questo non e' un esito"
	exit 6
fi
if [ "$PROVATI" -lt 2 ]; then
	inf "⚠ un motore solo: quel che questo giro NON puo' vedere e' proprio la"
	inf "  DIFFERENZA fra i due, che e' dove vivevano i difetti piu' cari della"
	inf "  fase (i tre rossi di B11, il posto che non si liberava)"
fi
if [ "$ESITO" -eq 0 ]; then
	ok "⭐ la meccanica regge: browser accesi, xdotool scrive, il registro si scrive"
	ok "   e S3 ha la sua meta' misurata, motore per motore"
else
	ko "⛔ qualcosa non passa — vedi sopra"
fi
inf "il dettaglio riga per riga sta in $QUI/01-p5-esiti.jsonl"
exit "$ESITO"
