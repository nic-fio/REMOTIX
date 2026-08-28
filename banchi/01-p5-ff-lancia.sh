#!/bin/bash
#
# 01-p5-ff-lancia.sh — ⛔ DI CHI E' IL CONGEDO CHE NON ESCE SU FIREFOX?
#                        L'attribuzione, con le prove prese DAL LATO DEL BROWSER.
#
#   bash banchi/01-p5-ff-lancia.sh                    i quattro giri, su firefox
#   bash banchi/01-p5-ff-lancia.sh chrome             gli stessi, su chrome
#   bash banchi/01-p5-ff-lancia.sh firefox vivo       un solo giro
#
# ⚠ GIRA DA CHUWI (i browser stanno di qua) contro una COPIA del prodotto sulla
#   ⭐ PORTA 7511, che serve la PAGINA STRUMENTATA di questo banco.
#   ⛔ Mai la 7448 (c'e' un server vivo che non e' nostro), mai la 7447, mai le
#      7471-7475 (l'agente di B8 sta lavorando li').
#
# ===========================================================================
# ⛔ PERCHE' ESISTE — LA DOMANDA CHE IL REGISTRO DEL SERVER NON PUO' CHIUDERE
#
# `[M]` 11 agosto 2026, sera, banco P5 sulla 7501.  Chiusa la scheda con
# `ctrl+w`, su **Firefox 140.13.0esr** al server non arriva nessun congedo: il
# client chiude con un **`FIN` nudo** sul canale di controllo, il posto e'
# `LASCIATO` in modo ordinato e `STACCATO per silenzio` vale 0.  ⇒ Il gesto e'
# arrivato, la sessione si e' chiusa bene, e il client non ha detto PERCHE'.
#
# ⛔ Ma da quella parte del filo restano DUE imputati che non si distinguono:
#
#   1. **la pagina** non ha spedito niente dentro `pagehide`;
#   2. **Gecko** ha buttato via quel che la pagina ha spedito dentro `pagehide`.
#
# I due arrivano IDENTICI al server: in tutt'e due i casi non arriva niente.
# ⭐ La sola cosa che li separa e' una traccia scritta DA DENTRO la pagina, che
#    sopravviva alla chiusura della scheda — e il portatore e'
#    `navigator.sendBeacon`, che non passa da WebTransport e quindi non
#    condivide il destino di quel che si misura (vedi `01-p5-ff-strumenta.py`).
#
# ===========================================================================
# ⛔⭐ I QUATTRO GIRI, E OGNUNO SEPARA UNA COPPIA
#
#   fedele  — il prodotto tale e quale, con le sole tracce aggiunte.  Dice se
#             `pagehide` scatta, e con che cosa in mano.
#   vivo    — ⭐ IL CONTROLLO POSITIVO: cinque secondi dopo `SESSIONE`, a scheda
#             VIVA e visibile, si chiama lo STESSO `congeda()` con lo STESSO
#             motivo.  Se qui il congedo arriva al server e dentro `pagehide`
#             no, l'imputato e' quel che succede a `pagehide` — non `congeda()`.
#   tenace  — dentro `pagehide` si chiama `congeda()` per una via che NON puo'
#             essere nulla.  Separa «non e' stata chiamata» da «e' stata
#             chiamata e non e' uscito niente».
#   codice  — dentro `pagehide` SOLO la seconda strada di §3.1, senza nessun
#             `await` davanti.  Separa «l'attesa non si e' mai risolta» da «il
#             motore butta via anche il codice di chiusura».
#
# ⛔ E SI GIRA DUE VOLTE.  Questo progetto ha gia' pagato un banco che cambiava
#    verdetto fra due giri identici: due esiti concordi, o il verdetto e' «c'e'
#    una corsa» e si scrive cosi'.
#
# ===========================================================================
# ⛔ IL BAN: SI DICHIARA PRIMA E DOPO, SUL PROPRIO FILE
#
# Si usa **sempre la parola giusta**, quindi nessun conto di §4.4-bis si muove.
# ⭐ Ma lo sblocco si CHIEDE lo stesso, all'inizio e alla fine, sul socket del
#    server di questo giro (`tmp/sera-ff.sock`, ban `tmp/sera-ff-ban`): un ban
#    mai scattato e un ban tolto hanno lo stesso aspetto, e le due righe
#    dichiarate sono l'unica cosa che li distingue (B0.3).
# ===========================================================================
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)

IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7511}
SCHERMO=${SCHERMO:-:77}
MISURA=${MISURA:-1280x1024}
UTENTE=${UTENTE:-prova}
PAROLA=${PAROLA:-parola-di-prova}
SOCK=${SOCK:-/srv/src/tmp/sera-ff.sock}
# ⛔ L'indirizzo da sbloccare e' quello del BROWSER visto dal server (chuwi),
#    non quello del server: un ban di §4.4-bis sta sulla chiave di CHI TENTA.
IND_CLIENTE=${IND_CLIENTE:-192.168.0.3}
LOG_SERVER=${LOG_SERVER:-/media/REMOTIX/src/tmp/sera-ff-server.log}
SSHPW="python3 $QUI/../fondamenta/strumenti/sshpw.py"

MOTORE=${1:-firefox}
SOLO=${2:-tutte}
# ⛔⭐ IL GESTO, E PERCHE' NON E' UN DETTAGLIO DI COMODO.
#
#   ctrl-w     chiude la scheda.  E' la scena di §8.2 `CHIUSO_DALL_UTENTE`, ed
#              e' quella in prova.
#   naviga-via ⭐ IL CONTROLLO DEL TRACCIATORE: `pagehide` scatta DI SICURO
#              (lo impone la specifica quando il documento viene sostituito), e
#              la pagina nuova arriva al server come marcatore.  ⇒ Se qui le
#              tracce di `pagehide` ARRIVANO e con `ctrl+w` no, allora con
#              `ctrl+w` l'evento non e' arrivato alla pagina — e non e' «la
#              pagina non ha spedito».  ⛔ Senza questo controllo, «nessuna
#              traccia» e «nessun gestore» hanno la stessa faccia.
GESTO=${3:-ctrl-w}

GIRO=$(date +%H%M%S)-$RANDOM
T=$(mktemp -d)
FUORI=${FUORI:-$QUI/01-p5-ff-esiti.jsonl}

log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf -- '    --  %s\n' "$*"; }
dub() { printf '    \033[1;33m??\033[0m  %s\n' "$*"; }

PID_X=; PID_BR=
congedo_finale()
{
	[ -n "$PID_BR" ] && { kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; }
	[ -n "$PID_X" ]  && { kill "$PID_X"  2>/dev/null; wait "$PID_X"  2>/dev/null; }
	rm -f "${PAROLA_FILE:-}"
	rm -rf "$T"
}
trap congedo_finale EXIT

X() { env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO "$@"; }

# ---------------------------------------------------------------------------
# ⛔ LA PAROLA D'ORDINE NON PASSA DALLA RIGA DI COMANDO — difetto **D12**,
#    curato il 12 agosto 2026 insieme a `01-p5-lancia.sh`.
#
# ⛔ Qui c'era `X xdotool type … "$PAROLA"`, e `xdotool` e' un PROCESSO: la
#    parola stava nel suo `argv`, cioe' in `/proc/<pid>/cmdline`, che su Linux
#    e' leggibile da chiunque — un `ps` durante il giro la stampava per intero.
#
# ⭐ La strada e' quella gia' in casa (`banchi/01-b10-lancia.sh`): un file
#    `0600` scritto con `printf`, che e' un **builtin** della shell — nemmeno la
#    scrittura passa per un processo con la parola in `argv` — e cancellato
#    subito.  ⛔ Senza a-capo in fondo: `xdotool` lo batterebbe come `Invio`.
#
# ⚠ Il pezzo in piu' rispetto a B10 e' `xdotool type --file`, che legge quel che
#   deve battere da un file invece che dagli argomenti: nel `cmdline` finisce il
#   PERCORSO, non la parola.  `[M]` controllo positivo con `xev`, 12 agosto
#   2026: dieci caratteri battuti esatti e nessun `Return` in coda.
# ⚠ La misura che PROVA la chiusura (un `ps` durante la battuta, con il suo
#   controllo positivo) sta in `01-p5-lancia.sh`, passo 2-bis: e' lo stesso
#   codice, e rifarla qui misurerebbe due volte la stessa cosa.
PAROLA_FILE=$T/parola-da-battere

digita_parola() # $1 = la parola da battere.  ⛔ E' una FUNZIONE, non un
{               #      programma: la chiamata non crea nessun `argv`.
	local stato
	# ⛔ `umask` IN UNA SOTTOSHELL — la riga che B10 ha pagato con un giro intero.
	( umask 077; : > "$PAROLA_FILE" ) || return 2
	chmod 600 "$PAROLA_FILE" || return 2
	printf '%s' "$1" > "$PAROLA_FILE"
	X xdotool type --clearmodifiers --delay 40 --file "$PAROLA_FILE"
	stato=$?
	rm -f "$PAROLA_FILE"
	return "$stato"
}


registra() { printf '%s\n' "$1" >> "$FUORI"; }

# ---------------------------------------------------------------------------
# ⛔ Lo stato della LETTURA si prova: un registro mancante, un ssh caduto e un
#    server mai partito arrivano tutti come «zero righe», che ha la stessa
#    faccia di «nessuna traccia».
scarica() # $1 = dove
{
	local stato
	$SSHPW "cat '$LOG_SERVER'; printf 'FF-FINE=%s\n' \$?" >"$1" 2>"$T/ssh.err"
	stato=$(sed -n 's/^FF-FINE=\([0-9][0-9]*\)$/\1/p' "$1" | tail -1)
	[ -n "$stato" ] && [ "$stato" -eq 0 ] && return 0
	ko "⛔ il registro del server non si e' letto: non e' «non c'e' traccia»,"
	ko "   e' «non ho potuto guardare»."
	sed -n '1,3p' "$T/ssh.err" | sed 's/^/        /'
	return 3
}

sblocca() # $1 = quando
{
	local testo
	testo=$($SSHPW "bash /media/REMOTIX/enter.sh --root \"python3 /srv/src/01-b8-sblocca.py --socket $SOCK $IND_CLIENTE\"" 2>&1 | tail -3)
	inf "sblocco $1 — sul MIO ban file (tmp/sera-ff-ban): $(printf '%s' "$testo" | tr '\n' ' ')"
	registra "{\"banco\":\"P5-FF\",\"giro\":\"$GIRO\",\"tipo\":\"SBLOCCO\",\"quando\":\"$1\"}"
}

fuoco() # $1 = pezzo di titolo
{
	local viste
	viste=$(X xdotool search --name "$1" 2>/dev/null | wc -l)
	[ "$viste" -eq 0 ] && return 1
	X xdotool search --name "$1" windowactivate --sync >/dev/null 2>&1
	X xdotool search --name "$1" windowfocus --sync >/dev/null 2>&1
	return 0
}
fuoco_pagina() { fuoco REMOTIX && return 0; fuoco "$IND" && return 0; return 1; }
finestre() { X xdotool search --name "${1:-REMOTIX}" 2>/dev/null | wc -l; }

naviga() # $1 = url
{
	X xdotool key --clearmodifiers ctrl+l >/dev/null 2>&1; sleep 1
	X xdotool type --clearmodifiers --delay 25 "$1" >/dev/null 2>&1; sleep 1
	X xdotool key --clearmodifiers Return >/dev/null 2>&1
}

supera_avviso()
{
	case "$MOTORE" in
	chrome)
		X xdotool mousemove 640 500 click 1 >/dev/null 2>&1; sleep 1
		X xdotool type --clearmodifiers --delay 120 'thisisunsafe' >/dev/null 2>&1 ;;
	firefox)
		# ⛔ Coordinate MISURATE l'11 agosto 2026 su Firefox 140.13.0esr con
		#    schermo 1280x1024 e finestra 1280x1000 (`01-p5-lancia.sh:518`).
		X xdotool mousemove 962 656 click 1 >/dev/null 2>&1; sleep 3
		X xdotool mousemove 881 965 click 1 >/dev/null 2>&1 ;;
	esac
	sleep 6
}

# Quante righe del registro portano l'espressione, DAL marcatore d'inizio in giu'.
da() # $1 registro, $2 marca inizio, $3 espressione
{
	awk -v a="$2" -v e="$3" '
		index($0,a) { dentro=1 }
		dentro && $0 ~ e { n++ }
		END { print n+0 }' "$1"
}

# ===========================================================================
log "0. La scena, dichiarata PRIMA di misurare (B0.1)"
inf "giro       : $GIRO"
inf "bersaglio  : https://$IND:$PORTA   ⛔ una COPIA del prodotto con la PAGINA"
inf "             STRUMENTATA di questo banco — non la 7448, non la 7448, non la 7471"
inf "motore     : $MOTORE"
inf "registro   : $LOG_SERVER"
inf "⛔ nessun tentativo di autenticazione FALLITO: si usa sempre la parola giusta"

for t in xdotool Xvfb xdpyinfo curl; do
	command -v "$t" >/dev/null || { ko "⛔ manca «$t»"; exit 2; }
done
case "$MOTORE" in
firefox) command -v firefox >/dev/null || { ko "⛔ firefox non c'e'"; exit 2; }
         inf "firefox: $(firefox --version 2>&1 | head -1)" ;;
chrome)  command -v google-chrome >/dev/null || { ko "⛔ google-chrome non c'e'"; exit 2; }
         inf "chrome : $(google-chrome --version 2>&1 | head -1)" ;;
*) ko "motore sconosciuto: $MOTORE"; exit 2 ;;
esac

log "1. Lo schermo finto, e si VERIFICA di che misura sia"
if [ -e "/tmp/.X11-unix/X${SCHERMO#:}" ]; then
	DIM=$(X xdpyinfo 2>/dev/null | sed -n 's/^  dimensions: *\([0-9x]*\).*/\1/p' | head -1)
	[ "$DIM" = "$MISURA" ] || { ko "⛔ $SCHERMO e' a ${DIM:-IGNOTA}, dichiarato $MISURA"; exit 2; }
	inf "lo schermo $SCHERMO era gia' acceso, ed e' della misura dichiarata ($DIM)"
else
	Xvfb "$SCHERMO" -screen 0 "${MISURA}x24" >"$T/xvfb.log" 2>&1 &
	PID_X=$!
	sleep 2
	DIM=$(X xdpyinfo 2>/dev/null | sed -n 's/^  dimensions: *\([0-9x]*\).*/\1/p' | head -1)
	[ "$DIM" = "$MISURA" ] || { ko "⛔ chiesto $MISURA, letto ${DIM:-niente}"; exit 2; }
	ok "schermo finto $SCHERMO — chiesto $MISURA, letto $DIM"
fi

log "2. Il bersaglio risponde, e il canale di LETTURA si certifica (A27)"
curl -sk --max-time 15 -o /dev/null "https://$IND:$PORTA/$GIRO-canale" 2>/dev/null || {
	ko "⛔ nessuno risponde su https://$IND:$PORTA"; exit 3; }
sleep 1
scarica "$T/reg0.txt" || exit 3
grep -q "$GIRO-canale" "$T/reg0.txt" || {
	ko "⛔ IL CANALE DI LETTURA E' ROTTO: ho chiesto «/$GIRO-canale» e rileggendo"
	ko "   il registro non lo trovo.  Allora ogni «traccia mancante» vorrebbe"
	ko "   dire «non ho guardato»."; exit 3; }
ok "⭐ una richiesta certamente avvenuta si rilegge nel registro"

# ⛔ E LA PAGINA SERVITA E' QUELLA STRUMENTATA — si guarda, non si presume.
curl -sk --max-time 15 "https://$IND:$PORTA/" 2>/dev/null > "$T/servita.html"
if ! grep -q 'FINE STRUMENTAZIONE' "$T/servita.html"; then
	ko "⛔ la pagina servita su :$PORTA NON e' quella strumentata: ogni traccia"
	ko "   mancante sarebbe una traccia mai scritta.  Non si misura niente."
	exit 3
fi
ok "⭐ la pagina servita porta la strumentazione ($(wc -c < "$T/servita.html") byte)"

sblocca prima

# ===========================================================================
# UN GIRO.  $1 = variante (fedele|vivo|tenace|codice)
# ---------------------------------------------------------------------------
giro()
{
	local var=$1
	local g="$GIRO-$var"
	local marca="ffm-$g-avvio"
	local prima dopo

	log "3.$var — si entra fino a SESSIONE, poi $([ "$var" = vivo ] \
		&& echo "si ASPETTA a scheda viva" || echo "gesto «$GESTO»")"

	# ⛔⭐ LA SCENA SI PULISCE PRIMA, E QUESTO BANCO L'AVEVA SBAGLIATO.
	#
	#     `[M]` 11 agosto 2026, 15:57, primo giro intero: le varianti `tenace` e
	#     `codice` hanno letto «finestre PRIMA del gesto: 0» e «sessione
	#     stabilita: 0».  ⛔ La ragione: `kill "$PID_BR"` ammazza il processo che
	#     si e' lanciato, ma la FINESTRA della variante precedente puo' restare
	#     sullo schermo — e allora `fuoco` da' il fuoco alla finestra sbagliata e
	#     i tasti finiscono in un browser che non e' quello in prova.  ⚠ Il
	#     risultato non era un errore: era un giro che «non misura niente» con la
	#     faccia di un giro riuscito e muto.
	while [ "$(X xdotool search --name . 2>/dev/null | wc -l)" -gt 0 ]; do
		X xdotool search --name . windowkill >/dev/null 2>&1
		sleep 1
		break
	done
	pkill -f "$T/prof-" >/dev/null 2>&1
	sleep 2
	if [ "$(finestre)" -ne 0 ]; then
		ko "⛔ c'e' ancora una finestra «REMOTIX» prima di cominciare: la scena"
		ko "   non e' quella dichiarata, e questo giro non misura niente."
		return 1
	fi

	rm -rf "$T/prof-$var"; mkdir -p "$T/prof-$var"
	if [ "$MOTORE" = firefox ]; then
		# ⛔ Senza queste tre, Firefox apre DUE schede al primo avvio e la scena
		#    non e' quella dichiarata (`01-p5-lancia.sh:800`).
		cat > "$T/prof-$var/user.js" <<'FINE'
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("datareporting.policy.firstRunURL", "");
user_pref("browser.aboutwelcome.enabled", false);
FINE
		X firefox --no-remote --profile "$T/prof-$var" --width 1280 --height 1000 \
		  "https://$IND:$PORTA/$marca" >"$T/br-$var.log" 2>&1 &
	else
		X google-chrome --ozone-platform=x11 --user-data-dir="$T/prof-$var" \
		  --no-first-run --no-default-browser-check --disable-sync \
		  --window-size=1280,1000 "https://$IND:$PORTA/$marca" \
		  >"$T/br-$var.log" 2>&1 &
	fi
	PID_BR=$!
	sleep 14
	supera_avviso
	scarica "$T/av-$var.txt" || return 3
	if ! grep -q "$marca" "$T/av-$var.txt"; then
		ko "⛔ il marcatore d'avvio non e' arrivato: l'avviso del certificato non"
		ko "   e' stato superato, e questo giro non misura niente."
		kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; PID_BR=
		return 1
	fi
	ok "l'avviso e' stato superato: il marcatore d'avvio e' al server"

	# ⭐ IL FRAMMENTO sceglie la variante, e NON arriva mai al server: i quattro
	#    giri misurano lo STESSO file byte per byte.
	fuoco_pagina || dub "non trovo la finestra: la navigazione potrebbe non arrivare"
	naviga "https://$IND:$PORTA/#$var.$g"
	sleep 8

	fuoco_pagina || dub "non trovo la finestra: i tasti potrebbero non arrivare"
	X xdotool mousemove 640 820 click 1 >/dev/null 2>&1; sleep 1
	X xdotool key --clearmodifiers Tab >/dev/null 2>&1; sleep 1
	X xdotool type --clearmodifiers --delay 40 "$UTENTE" >/dev/null 2>&1
	X xdotool key --clearmodifiers Tab >/dev/null 2>&1; sleep 1
	# ⛔ D12: la parola arriva da un file `0600`, mai da `argv`.
	digita_parola "$PAROLA" || echo "    NO  ⛔ la parola non si e' potuta battere dal file"
	sleep 1
	X xdotool key --clearmodifiers Return >/dev/null 2>&1
	# ⚠ Generoso apposta: §4.4-bis impone un secondo fisso e PAM ne ha aggiunti
	#   fino a 2,6 in altre misure.
	sleep 13

	prima=$(finestre)
	inf "finestre col titolo «REMOTIX» PRIMA del gesto: $prima"

	if [ "$var" = vivo ]; then
		# ⭐ NESSUN GESTO: la scheda resta viva, e a chiamare `congeda()` e' un
		#    timer.  Si aspetta piu' dei cinque secondi del timer.
		inf "⭐ nessun gesto: la scheda resta VIVA e il timer chiama congeda()"
		sleep 12
		dopo=$(finestre)
	elif [ "$GESTO" = ctrl-w-due ]; then
		# ⛔⭐ CHIUDERE LA SCHEDA, SENZA CHIUDERE IL BROWSER — e i due non sono
		#     lo stesso gesto.
		#
		#     Con UNA sola scheda, `ctrl+w` fa uscire Firefox: quel che si misura
		#     non e' «la scheda si chiude», e' «il programma termina».  ⚠ Un
		#     motore puo' saltare `pagehide` mentre esce, e accusarlo di non
		#     averlo scattato «alla chiusura della scheda» sarebbe il rosso
		#     sull'imputato sbagliato.
		# ⭐ Qui si apre una SECONDA scheda su un marcatore verificabile, si
		#    torna sulla prima e si batte `ctrl+w`: la scheda muore, il browser
		#    resta vivo, e la scena e' quella che l'utente fa davvero.
		fuoco_pagina || dub "non trovo la finestra: il gesto potrebbe non arrivare"
		X xdotool key --clearmodifiers ctrl+t >/dev/null 2>&1; sleep 2
		X xdotool type --clearmodifiers --delay 25 "https://$IND:$PORTA/ffm-$g-secondascheda" >/dev/null 2>&1
		sleep 1
		X xdotool key --clearmodifiers Return >/dev/null 2>&1; sleep 5
		X xdotool key --clearmodifiers ctrl+shift+Tab >/dev/null 2>&1; sleep 2
		X xdotool key --clearmodifiers ctrl+w >/dev/null 2>&1
		sleep 10
		dopo=$(finestre)
	elif [ "$GESTO" = naviga-via ]; then
		# ⭐ IL CONTROLLO DEL TRACCIATORE: `pagehide` scatta di sicuro, e la
		#    pagina nuova arriva al server come marcatore verificabile.
		fuoco_pagina || dub "non trovo la finestra: il gesto potrebbe non arrivare"
		naviga "https://$IND:$PORTA/ffm-$g-viaggiato"
		sleep 10
		dopo=$(finestre)
	else
		fuoco_pagina || dub "non trovo la finestra: il gesto potrebbe non arrivare"
		X xdotool key --clearmodifiers ctrl+w >/dev/null 2>&1
		sleep 10
		dopo=$(finestre)
	fi
	inf "finestre col titolo «REMOTIX» DOPO: $dopo"

	scarica "$T/reg-$var.txt" || return 3
	grep -E "$g|$marca" "$T/reg-$var.txt" > "$T/righe-$var.txt"

	# ⛔ E CHE IL GESTO SIA ARRIVATO NON SI PRESUME.
	#    ctrl+w     : la finestra dev'essere sparita.
	#    naviga-via : il marcatore della pagina NUOVA dev'essere al server —
	#                 ⭐ ed e' la prova che il documento e' stato sostituito,
	#                    cioe' che `pagehide` DOVEVA scattare.
	local gesto_fatto=ignoto
	if [ "$var" = vivo ]; then
		gesto_fatto=nessuno
	elif [ "$GESTO" = ctrl-w-due ]; then
		# ⛔ Due prove insieme: la seconda scheda e' arrivata al server (cioe' il
		#    browser aveva davvero DUE schede) e la finestra col titolo REMOTIX
		#    e' sparita (cioe' la scheda in prova si e' chiusa) MA il browser e'
		#    ancora vivo.
		local vive; vive=$(X xdotool search --name . 2>/dev/null | wc -l)
		if grep -q "ffm-$g-secondascheda" "$T/reg-$var.txt" && [ "$dopo" -lt "$prima" ] && [ "$vive" -gt 0 ]; then
			gesto_fatto=fatto
			ok "⭐ il gesto E' ARRIVATO: la seconda scheda e' al server, le finestre"
			ok "   «REMOTIX» sono $prima → $dopo, e il browser e' ANCORA VIVO ($vive finestre)"
		else
			gesto_fatto=non-arrivato
			ko "⛔ IL GESTO NON E' ARRIVATO come dichiarato: seconda scheda al server?"
			ko "   $(grep -c "ffm-$g-secondascheda" "$T/reg-$var.txt") · finestre $prima → $dopo · browser vivo: $vive finestre"
		fi
	elif [ "$GESTO" = naviga-via ]; then
		if grep -q "ffm-$g-viaggiato" "$T/reg-$var.txt"; then
			gesto_fatto=fatto
			ok "⭐ il gesto E' ARRIVATO: la pagina nuova (ffm-$g-viaggiato) e' al server,"
			ok "   quindi il documento e' stato sostituito e «pagehide» doveva scattare"
		else
			gesto_fatto=non-arrivato
			ko "⛔ IL GESTO NON E' ARRIVATO: la pagina nuova non e' al server."
			ko "   Allora «nessuna traccia» qui non accusa nessuno."
		fi
	else
		if [ "$prima" -gt 0 ] && [ "$dopo" -lt "$prima" ]; then
			gesto_fatto=fatto
			ok "⭐ il gesto E' ARRIVATO: le finestre sono passate da $prima a $dopo"
		else
			gesto_fatto=non-arrivato
			ko "⛔ IL GESTO NON E' ARRIVATO: le finestre sono $prima → $dopo."
			ko "   Allora «nessuna traccia» qui non accusa nessuno: accusa il pilota."
		fi
	fi

	# ── I fatti, contati ──────────────────────────────────────────────────
	local sess ph_entrato cc_nulla cc_presente cg_chiamata cg_prima cg_dopo
	local cg_fin cg_close_prima cg_close_dopo canale chiusura viol lasciato silenzio fin_nudo
	sess=$(grep -c "sessione-stabilita" "$T/righe-$var.txt")
	ph_entrato=$(grep -c "ph-entrato" "$T/righe-$var.txt")
	cc_nulla=$(grep -c "ph-congeda_corrente-NULLA" "$T/righe-$var.txt")
	cc_presente=$(grep -c "ph-congeda_corrente-PRESENTE" "$T/righe-$var.txt")
	cg_chiamata=$(grep -c "cg-chiamata-motivo" "$T/righe-$var.txt")
	cg_prima=$(grep -c "cg-prima-di-manda" "$T/righe-$var.txt")
	cg_dopo=$(grep -c "cg-dopo-manda-la-write-si-e-risolta" "$T/righe-$var.txt")
	cg_fin=$(grep -c "cg-dopo-il-FIN-del-canale" "$T/righe-$var.txt")
	cg_close_prima=$(grep -cE "cg-prima-di-wt-close|ph-codice-prima-di-wt-close" "$T/righe-$var.txt")
	cg_close_dopo=$(grep -cE "cg-dopo-wt-close|ph-codice-dopo-wt-close" "$T/righe-$var.txt")
	canale=$(da   "$T/reg-$var.txt" "$marca" "il client si congeda, motivo=")
	chiusura=$(da "$T/reg-$var.txt" "$marca" "la pagina ha chiuso la sessione, motivo")
	viol=$(da     "$T/reg-$var.txt" "$marca" "VIOLAZIONE §3.1")
	fin_nudo=$(da "$T/reg-$var.txt" "$marca" "FIN del CLIENT sul canale di controllo")
	lasciato=$(da "$T/reg-$var.txt" "$marca" "posto LASCIATO da")
	silenzio=$(da "$T/reg-$var.txt" "$marca" "STACCATO per silenzio")

	printf '\n'
	inf "── dal lato del BROWSER (le tracce della pagina) ──"
	inf "  sessione stabilita              : $sess"
	inf "  pagehide E' SCATTATO            : $ph_entrato"
	inf "  congeda_corrente era NULLA      : $cc_nulla   ·  era PRESENTE: $cc_presente"
	inf "  congeda() e' stata CHIAMATA     : $cg_chiamata"
	inf "  prima della write sul canale    : $cg_prima"
	inf "  la write SI E' RISOLTA          : $cg_dopo"
	inf "  il FIN del canale e' passato    : $cg_fin"
	inf "  prima di wt.close(codice)       : $cg_close_prima  ·  dopo: $cg_close_dopo"
	inf "── dal lato del SERVER (chi deve ricevere) ──"
	inf "  CONGEDO sul canale (strada 1)   : $canale"
	inf "  chiusura col codice (strada 2)  : $chiusura   (di cui col codice 0x0, VIETATO: $viol)"
	inf "  FIN nudo sul canale di controllo: $fin_nudo"
	inf "  posto LASCIATO: $lasciato  ·  STACCATO per silenzio: $silenzio"
	inf "  gesto «$GESTO»: $gesto_fatto"

	# ⛔ §8.1 vuole il motivo VERO (0x01 CHIUSO_DALL_UTENTE), non una chiusura
	#    qualunque: una sessione chiusa col codice 0 e' §3.1 VIOLATA, e il server
	#    la mette a verbale come ERRORE_PROTOCOLLO.  ⭐ Contarla come «congedo»
	#    e' l'errore che il primo arbitrato ha commesso.
	local buono
	buono=$(da "$T/reg-$var.txt" "$marca" "motivo 0x01|motivo=0x01")
	if [ "$buono" -gt 0 ]; then
		ok "⭐ §8.1 RISPETTATA: il motivo 0x01 CHIUSO_DALL_UTENTE e' arrivato al server"
	elif [ "$chiusura" -gt 0 ]; then
		ko "⛔ la sessione si e' chiusa MA SENZA IL MOTIVO: $viol chiusure col"
		ko "   codice 0x0, che §3.1 VIETA.  Non e' un congedo: e' il motore che"
		ko "   smonta la sessione da se'."
	else
		ko "⛔ niente: nessuna delle due strade di §3.1"
	fi

	registra "{\"banco\":\"P5-FF\",\"giro\":\"$GIRO\",\"motore\":\"$MOTORE\",\"variante\":\"$var\",\"gesto\":\"$GESTO\",\"gesto_fatto\":\"$gesto_fatto\",\"sessione\":$sess,\"pagehide\":$ph_entrato,\"cc_nulla\":$cc_nulla,\"cc_presente\":$cc_presente,\"congeda_chiamata\":$cg_chiamata,\"write_avviata\":$cg_prima,\"write_risolta\":$cg_dopo,\"fin_canale\":$cg_fin,\"close_prima\":$cg_close_prima,\"close_dopo\":$cg_close_dopo,\"srv_canale\":$canale,\"srv_chiusura\":$chiusura,\"srv_viol31\":$viol,\"srv_fin_nudo\":$fin_nudo,\"srv_motivo_giusto\":$buono,\"srv_lasciato\":$lasciato,\"srv_silenzio\":$silenzio}"

	kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; PID_BR=
	sleep 3
	return 0
}

if [ "$SOLO" = tutte ]; then
	for v in eco fedele vivo tenace codice; do giro "$v"; done
else
	giro "$SOLO"
fi

sblocca dopo

log "4. Le tracce grezze di questo giro restano in $FUORI"
inf "⛔ Il verdetto non lo scrive questo file: lo scrive chi legge le due"
inf "   colonne «pagehide E' SCATTATO» e «congeda() e' stata CHIAMATA»."
exit 0
