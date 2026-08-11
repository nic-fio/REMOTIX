#!/bin/bash
#
# ⛔⛔⛔ NON CREDERE AL VERDE DI QUESTO FILE — DIFETTO NOTO, 11 agosto 2026 sera
#
#   Questo strumento ha ASSOLTO la pagina per sbaglio, e l'assoluzione e' finita
#   in un rapporto e in due documenti prima che qualcuno la smentisse.
#
#   ⛔ LA RIGA 318 (`chiusura=...`) conta
#         "la pagina ha chiuso la sessione, motivo"
#      SENZA GUARDARE IL MOTIVO.  Chiudendo la scheda, Chrome smonta la sessione
#      col codice 0x0 — che §3.1 VIETA, e che il server registra come
#      "⛔ VIOLAZIONE §3.1 ... A verbale va ERRORE_PROTOCOLLO" — e questo
#      contatore l'ha contata come un CONGEDO, stampando
#      «⭐⭐ LA PAGINA FA QUEL CHE §8.1 LE IMPONE».
#
#   ⛔ E LA SCENA E' SBAGLIATA: `ctrl+w` sull'UNICA scheda fa USCIRE Firefox, e
#      in quel caso non esce niente per NESSUNA via — nemmeno per una pagina
#      senza difetti.  La scena vuole DUE schede.
#
#   ⭐ La misura che attribuisce davvero e' `01-p5-ff-lancia.sh` (pagina
#      strumentata su una copia, tracciatore che NON passa da WebTransport), e
#      il verdetto e': il congedo che non esce e' della PAGINA, su tutt'e due i
#      motori — `src/pagina.html:620` azzera `congeda_corrente` un millisecondo
#      dopo SESSIONE, e il gestore di `pagehide` e' codice morto.
#
#   Le due cure di questo file, da fare prima di rilanciarlo: contare
#   `motivo 0x01`, non una chiusura qualunque; e aprire la seconda scheda.
#   ⛔ Il file resta qui com'e' — SENZA le cure — perche' e' la prova di come
#      l'assoluzione e' nata: si corregge con una misura nuova, non cancellando
#      quella sbagliata.
#
# ---------------------------------------------------------------------------
# 01-p5-congedo.sh — ⛔ DI CHI E' IL CONGEDO CHE NON ARRIVA?  Una misura sola,
#                      che serve a dare un NOME all'imputato.
#
#   PORTA=7501 SCHERMO=:79 bash banchi/01-p5-congedo.sh chrome
#
# ⚠ GIRA DA CHUWI (i browser stanno di qua) contro una COPIA del prodotto su
#   una porta propria.  ⛔ Mai la 7448, mai la 7447.
#
# ===========================================================================
# ⛔ PERCHE' ESISTE — e non e' un banco, e' un ARBITRATO
#
# `[M]` 11 agosto 2026, sera, banco P5 contro la copia sulla 7501: su Chrome la
# stretta di mano arriva fino a `SESSIONE` (14 controlli su 15), e l'unico
# punto che cade e' il CONGEDO — chiusa la scheda con `ctrl+w`, il client non
# manda niente per nessuna delle due strade di §3.1, e a liberare il posto e'
# il tetto d'inattivita' di 30 s.
#
# ⛔ Ma «il congedo non arriva» ha DUE imputati, e P5 non li distingue:
#
#   1. **la pagina del prodotto** — il gestore di `pagehide` non spedisce;
#   2. **il pilota del banco** — il `ctrl+w` non e' mai arrivato alla finestra,
#      e allora `pagehide` non e' nemmeno scattato: si sta misurando il
#      silenzio di un gesto che non c'e' stato.
#
# ⚠ E i due non pesano uguale, perche' `src/pagina.html:331` **un gestore ce
#   l'ha**, scritto apposta e col suo commento.  ⛔ Accusare il prodotto di una
#   cosa che il prodotto fa sarebbe la seconda volta in questa fase (la prima
#   fu B3, dove il colpevole era il buffer di Python) — cioe' la settima veste
#   di `LEZIONI.md` §1.9, il rosso puntato sull'imputato sbagliato.
#
# ===========================================================================
# ⛔⭐ IL DISEGNO, E PERCHE' IL CONTROLLO POSITIVO E' «NAVIGARE VIA»
#
# La pagina non ha nessun bottone di scollegamento: `congeda_corrente` lo
# chiama **solo** `pagehide` (e il ramo d'errore del protocollo).  ⇒ Non esiste
# una «chiusura volontaria dal bottone» da mettere a confronto.
#
# ⭐ Ma esiste un secondo gesto dell'utente che scatena **lo stesso identico
#    `pagehide`**: cambiare pagina.  E' la via giusta, perche' separa le due
#    domande che `ctrl+w` tiene insieme:
#
#      scena A — si naviga altrove dalla barra dell'indirizzo (`ctrl+l`)
#                ⇒ `pagehide` scatta DI SICURO, e il gesto e' verificabile
#                   perche' la pagina nuova arriva al server come marcatore
#      scena B — si chiude la scheda con `ctrl+w`
#                ⇒ `pagehide` scatta SOLO SE il tasto e' arrivato
#
#   | A | B | l'imputato ha questo nome                                      |
#   |---|---|---------------------------------------------------------------|
#   | si| no| ⛔ **il pilota**: `pagehide` funziona, il `ctrl+w` non arriva   |
#   | no| no| ⛔ **la pagina**: il gestore c'e' e non spedisce                |
#   | si| si| ⭐ il congedo funziona per tutt'e due: il rosso di P5 veniva da |
#   |   |   | altro, e si va a cercarlo li'                                  |
#   | no| si| ⚠ scena impossibile a prima vista: si dichiara e non si spiega  |
#
# ⛔ E IL TESTIMONE E' IL REGISTRO DEL SERVER, non il verdetto di un banco:
#    §8.1 parla di byte che escono, e a vederli arrivare e' chi riceve
#    (`CODER.md` §3.8).
#
# ⛔ E SI LEGGE A +8 SECONDI, NON A +40.  Il tetto d'inattivita' di §2.2 libera
#    il posto a 30 s: leggere dopo confonderebbe «si e' congedato» con «e'
#    stato staccato per silenzio», che sono esattamente i due esiti da
#    separare.  ⭐ Un congedo, se esce, esce subito.
#
# ===========================================================================
# ⛔ IL CONTROLLO POSITIVO DEL PILOTA, e senza non si da' nessun verdetto
#
# Dopo ogni gesto si guarda **col DISPLAY giusto** se la finestra col titolo
# «REMOTIX» c'e' ancora.  ⚠ Se dopo `ctrl+w` la finestra e' ancora li', il
# tasto NON e' arrivato, e allora «il congedo non c'e'» vuol dire «non ho
# potuto guardare» — che non e' un rosso del prodotto.
#
# ⛔ E la funzione `X` davanti a `xdotool` non e' un vezzo: `01-p5-lancia.sh`
#    riga 589 batte `xdotool key ctrl+w` **senza** `X`, cioe' sul `DISPLAY`
#    dell'ambiente e non sullo schermo finto — ed e' il primo sospettato di
#    tutta questa storia.
#
# ===========================================================================
# ⛔ IL BAN: questo giro NON ne spende niente
#
# Si usa **sempre la parola giusta**: nessun tentativo fallito, quindi nessun
# conto di §4.4-bis che si muove, quindi nessuno sblocco da dichiarare (B0.3).
# ⭐ E il server e' una COPIA con il file dei ban suo: anche se sbagliassimo,
#    resterebbe dentro questo giro.
# ===========================================================================
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)

IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7501}
SCHERMO=${SCHERMO:-:79}
MISURA=${MISURA:-1280x1024}
UTENTE=${UTENTE:-prova}
PAROLA=${PAROLA:-parola-di-prova}
LOG_SERVER=${LOG_SERVER:-/media/REMOTIX/src/tmp/sera-p15-browser.log}
MOTORE=${1:-chrome}

SSH="ssh -o BatchMode=yes -o ConnectTimeout=10 nicfio@$IND"
GIRO="cong-$(date +%Y%m%d-%H%M%S)-$RANDOM"
T=$(mktemp -d)

log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
dub() { printf '    \033[1;33m??\033[0m  %s\n' "$*"; }

PID_X=; PID_BR=
congedo_finale()
{
	[ -n "$PID_BR" ] && { kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; }
	[ -n "$PID_X" ]  && { kill "$PID_X"  2>/dev/null; wait "$PID_X"  2>/dev/null; }
	rm -rf "$T"
}
trap congedo_finale EXIT

X() { env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO "$@"; }

# ---------------------------------------------------------------------------
# ⛔ Il registro del server, e lo stato della LETTURA si prova: un registro
#    mancante, un ssh caduto e un server mai partito arrivano tutti come «zero
#    righe», che ha la stessa faccia di «nessun congedo».
scarica() # $1 = dove
{
	local stato
	$SSH "cat '$LOG_SERVER'; printf 'FINE=%s\n' \$?" >"$1" 2>"$T/ssh.err"
	stato=$(sed -n 's/^FINE=\([0-9][0-9]*\)$/\1/p' "$1" | tail -1)
	[ -n "$stato" ] && [ "$stato" -eq 0 ] && return 0
	ko "⛔ il registro del server non si e' letto: non e' «non c'e' congedo»,"
	ko "   e' «non ho potuto guardare»."
	sed -n '1,3p' "$T/ssh.err" | sed 's/^/        /'
	return 3
}

naviga() # $1 = url
{
	X xdotool key --clearmodifiers ctrl+l >/dev/null 2>&1; sleep 1
	X xdotool type --clearmodifiers --delay 25 "$1" >/dev/null 2>&1; sleep 1
	X xdotool key --clearmodifiers Return >/dev/null 2>&1
}

fuoco() # $1 = pezzo di titolo.  Esce 0 se ha trovato ALMENO una finestra.
{
	local viste
	viste=$(X xdotool search --name "$1" 2>/dev/null | wc -l)
	[ "$viste" -eq 0 ] && return 1
	X xdotool search --name "$1" windowactivate --sync >/dev/null 2>&1
	X xdotool search --name "$1" windowfocus --sync >/dev/null 2>&1
	return 0
}

finestre() # $1 = pezzo di titolo.  Quante ce ne sono ADESSO.
{
	X xdotool search --name "$1" 2>/dev/null | wc -l
}

accedi() # entra fino a SESSIONE dalla pagina, come farebbe l'utente
{
	fuoco REMOTIX || return 1
	X xdotool mousemove 640 820 click 1 >/dev/null 2>&1; sleep 1
	X xdotool key --clearmodifiers Tab >/dev/null 2>&1; sleep 1
	X xdotool type --clearmodifiers --delay 40 "$UTENTE" >/dev/null 2>&1
	X xdotool key --clearmodifiers Tab >/dev/null 2>&1; sleep 1
	X xdotool type --clearmodifiers --delay 40 "$PAROLA" >/dev/null 2>&1; sleep 1
	X xdotool key --clearmodifiers Return >/dev/null 2>&1
	# ⚠ Il tetto e' generoso apposta: §4.4-bis impone un secondo fisso, e PAM
	#   ne ha aggiunti fino a 2,6 in altre misure.
	sleep 12
	return 0
}

# `fra <file> <da> <a> <espressione>` — quante volte, FRA i due marcatori.
fra() # $1 registro, $2 marca inizio, $3 marca fine, $4 espressione
{
	awk -v a="$2" -v b="$3" -v e="$4" '
		index($0,a) { dentro=1 }
		dentro && index($0,b) { dentro=0 }
		dentro && $0 ~ e { n++ }
		END { print n+0 }' "$1"
}

# ⛔⭐ E PER LA SCENA A IL SEGMENTO NON PUO' CHIUDERSI SUL MARCATORE DI FINE —
#     difetto del PRIMO giro di questo strumento, 11 agosto 2026 ore 13:22.
#
# Nella scena A il marcatore di fine e' **la pagina su cui si naviga**: quindi
# `pagehide` scatta mentre quella richiesta e' in volo, e la riga del congedo
# puo' arrivare al server **dopo** la riga del marcatore.  ⇒ `fra()` la
# tagliava fuori, e il primo giro ha letto «zero congedi» su una scena che non
# aveva ancora finito di parlare.  ⚠ Uno zero da segmento sbagliato ha la
# stessa faccia di uno zero vero, ed e' il difetto che questo file esiste per
# non commettere.
# ⭐ Qui si conta DAL marcatore d'inizio fino in fondo al registro: il giro e'
#    solo e la sua coda non e' di nessun altro.
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
inf "bersaglio  : https://$IND:$PORTA   ⛔ una COPIA del prodotto, non la 7448"
inf "motore     : $MOTORE"
inf "registro   : $LOG_SERVER"
inf "⛔ nessun tentativo di autenticazione FALLITO: si usa sempre la parola"
inf "   giusta, quindi nessun conto di §4.4-bis si muove e non c'e' niente da"
inf "   sbloccare (B0.3)."

for t in xdotool Xvfb xdpyinfo curl; do
	command -v "$t" >/dev/null || { ko "⛔ manca «$t»"; exit 2; }
done
command -v google-chrome >/dev/null || { ko "⛔ google-chrome non c'e'"; exit 2; }
inf "google-chrome: $(google-chrome --version 2>&1 | head -1)"

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

log "2. Il bersaglio risponde, e il canale di lettura si certifica (A27)"
curl -sk --max-time 15 -o /dev/null "https://$IND:$PORTA/$GIRO-canale" 2>/dev/null || {
	ko "⛔ nessuno risponde su https://$IND:$PORTA — non e' «il giro e' fallito»,"
	ko "   e' «non c'e' nessuno dall'altra parte»."
	exit 3
}
sleep 1
scarica "$T/reg0.txt" || exit 3
if ! grep -q "$GIRO-canale" "$T/reg0.txt"; then
	ko "⛔ IL CANALE DI LETTURA E' ROTTO: ho chiesto «/$GIRO-canale» e rileggendo"
	ko "   il registro non lo trovo (righe guardate: $(wc -l < "$T/reg0.txt"))."
	ko "   ⛔ Allora ogni «congedo non trovato» vorrebbe dire «non ho guardato»."
	exit 3
fi
ok "⭐ una richiesta certamente avvenuta si rilegge nel registro"

# ===========================================================================
# UNA SCENA.  $1 = etichetta · $2 = come si va via
# ---------------------------------------------------------------------------
CONG_A=-1; CONG_B=-1; GESTO_A=ignoto; GESTO_B=ignoto
scena()
{
	local nome=$1 via=$2
	local ma="$GIRO-$nome-inizio" mb="$GIRO-$nome-fine"
	local prima dopo canale chiusura lasciato silenzio

	log "3.$nome — si entra fino a SESSIONE, poi si va via con «$via»"

	rm -rf "$T/profilo-$nome"; mkdir -p "$T/profilo-$nome"
	X google-chrome --ozone-platform=x11 --user-data-dir="$T/profilo-$nome" \
	  --no-first-run --no-default-browser-check --disable-sync \
	  --window-size=1280,1000 "https://$IND:$PORTA/$ma" \
	  >"$T/br-$nome.log" 2>&1 &
	PID_BR=$!
	sleep 12
	# ⛔ L'avviso del certificato della PAGINA e' atteso (§4.1-bis) e si supera
	#    dalla porta dell'utente: `thisisunsafe` chiama lo stesso `proceed` del
	#    bottone «Procedi».  ⚠ Che sia riuscito lo dice il marcatore, non la fede.
	X xdotool mousemove 640 500 click 1 >/dev/null 2>&1; sleep 1
	X xdotool type --clearmodifiers --delay 120 'thisisunsafe' >/dev/null 2>&1
	sleep 6
	scarica "$T/av-$nome.txt" || return 3
	if ! grep -q "$ma" "$T/av-$nome.txt"; then
		ko "⛔ il marcatore d'inizio non e' arrivato: l'avviso non e' stato"
		ko "   superato, e questa scena non misura niente."
		kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; PID_BR=
		return 1
	fi
	ok "l'avviso e' stato superato: il marcatore d'inizio e' al server"

	naviga "https://$IND:$PORTA/"
	sleep 6
	accedi || { ko "⛔ non trovo la finestra col titolo REMOTIX: non ho pilotato"; }

	prima=$(finestre REMOTIX)
	inf "finestre col titolo «REMOTIX» PRIMA del gesto: $prima"

	case "$via" in
	naviga-via)
		# ⭐ IL CONTROLLO POSITIVO: lo stesso `pagehide` di `ctrl+w`, ma per una
		#    via il cui esito si vede (la pagina nuova arriva al server).
		fuoco REMOTIX || dub "non trovo la finestra: il gesto potrebbe non arrivare"
		naviga "https://$IND:$PORTA/$mb"
		sleep 8
		;;
	ctrl-w)
		# ⛔ E QUI SI BATTE CON `X`, cioe' sullo schermo dichiarato.
		#    `01-p5-lancia.sh:589` lo batte SENZA, ed e' il primo sospettato.
		fuoco REMOTIX || dub "non trovo la finestra: il gesto potrebbe non arrivare"
		X xdotool key --clearmodifiers ctrl+w >/dev/null 2>&1
		sleep 8
		# la scheda chiusa non puo' battere il marcatore di fine: lo chiude curl,
		# e si dichiara — serve solo a chiudere il segmento, non e' una prova.
		curl -sk --max-time 15 -o /dev/null "https://$IND:$PORTA/$mb" 2>/dev/null
		sleep 1
		;;
	esac

	dopo=$(finestre REMOTIX)
	inf "finestre col titolo «REMOTIX» DOPO il gesto: $dopo"

	scarica "$T/reg-$nome.txt" || return 3
	canale=$(da   "$T/reg-$nome.txt" "$ma" "il client si congeda, motivo=")
	chiusura=$(da "$T/reg-$nome.txt" "$ma" "la pagina ha chiuso la sessione, motivo")
	lasciato=$(da "$T/reg-$nome.txt" "$ma" "posto LASCIATO da")
	silenzio=$(da "$T/reg-$nome.txt" "$ma" "STACCATO per silenzio")

	inf "sessione aperta: $(fra "$T/reg-$nome.txt" "$ma" "$mb" "sessione aperta utente=") · posto preso: $(fra "$T/reg-$nome.txt" "$ma" "$mb" "posto PRESO da")"
	inf "CONGEDO sul canale (§3.1 strada 1): $canale"
	inf "motivo nel codice di chiusura (§3.1 strada 2): $chiusura"
	inf "posto LASCIATO: $lasciato · STACCATO per silenzio: $silenzio"

	local tot=$((canale + chiusura))
	# ⛔ B0.4: l'atteso lo confronta il banco.  §8.1 vuole ALMENO UNA delle due
	#    strade; a 8 secondi il tetto dei 30 non puo' aver ancora liberato niente,
	#    quindi «lasciato» senza congedo e «staccato» sono distinguibili.
	if [ "$tot" -gt 0 ]; then
		ok "⭐ il congedo E' USCITO (§8.1 rispettata, $tot su 2 strade)"
	else
		ko "⛔ nessun congedo, per nessuna delle due strade di §3.1"
	fi
	if [ "$nome" = A ]; then
		CONG_A=$tot; GESTO_A=$([ "$dopo" -le "$prima" ] && echo fatto || echo ignoto)
	else
		CONG_B=$tot
		# ⛔ Il controllo positivo del PILOTA: dopo `ctrl+w` la finestra deve
		#    essere sparita.  Se e' ancora li', il tasto non e' arrivato e «non
		#    c'e' congedo» vuol dire «non ho potuto guardare».
		if [ "$prima" -gt 0 ] && [ "$dopo" -lt "$prima" ]; then
			GESTO_B=fatto
			ok "⭐ il gesto E' ARRIVATO: le finestre sono passate da $prima a $dopo"
		else
			GESTO_B=non-arrivato
			ko "⛔ IL GESTO NON E' ARRIVATO: le finestre sono $prima → $dopo."
			ko "   Allora «nessun congedo» qui NON accusa la pagina: accusa il pilota."
		fi
	fi

	kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; PID_BR=
	sleep 2
	return 0
}

scena A naviga-via
scena B ctrl-w

# ===========================================================================
log "4. ⛔ L'IMPUTATO, e si nomina uno solo"
inf "scena A (si naviga via — «pagehide» scatta di sicuro) : congedi = $CONG_A"
inf "scena B (ctrl+w — «pagehide» scatta SOLO se il tasto arriva) : congedi = $CONG_B  ·  gesto: $GESTO_B"
# ⛔ E LA SCENA CHE DECIDE E' LA B, non la coppia.  La domanda dell'arbitrato e'
#    una sola — *chiudendo la scheda, il congedo esce?* — e la scena A serve a
#    dire che cosa vorrebbe dire uno zero in B.  ⚠ Farle pesare uguale
#    trasformerebbe un fatto in una combinazione da interpretare.
E=0
if [ "$CONG_B" -lt 0 ]; then
	dub "⛔ la scena B non si e' potuta misurare: NESSUN verdetto."
	dub "   «Non ho guardato» non e' «non c'e'»."
	E=3
elif [ "$GESTO_B" = non-arrivato ]; then
	ko "⛔ L'IMPUTATO E' IL PILOTA DEL BANCO, e non il prodotto:"
	ko "   il ctrl+w non e' arrivato alla finestra, quindi «pagehide» non e'"
	ko "   nemmeno scattato.  P5 stava misurando il silenzio di un gesto mai fatto."
	E=1
elif [ "$CONG_B" -gt 0 ]; then
	ok "⭐⭐ LA PAGINA FA QUEL CHE §8.1 LE IMPONE: il gesto e' arrivato E il"
	ok "    congedo e' uscito ($CONG_B su 2 strade).  ⛔ Quindi il rosso di P5"
	ok "    NON e' del prodotto: e' del PILOTA di 01-p5-lancia.sh, che batte"
	ok "    «xdotool key ctrl+w» SENZA la funzione X — cioe' su un DISPLAY che"
	ok "    non e' lo schermo finto (riga 589).  Qui il tasto e' stato battuto"
	ok "    con X, e il congedo e' uscito."
	if [ "$CONG_A" -eq 0 ]; then
		dub "⚠ E la scena A dice ZERO, il che NON accusa nessuno: navigando via"
		dub "  «pagehide» ha meno tempo, e Chrome puo' buttare via un messaggio"
		dub "  spedito subito prima di andarsene (difetto 2 di B11, gia' misurato)."
		dub "  ⛔ Resta un [?], e non si arrotonda ne' a bene ne' a male."
	fi
else
	ko "⛔ L'IMPUTATO E' LA PAGINA: il gesto e' arrivato (le finestre sono calate)"
	ko "   e il congedo NON e' uscito, per nessuna delle due strade di §3.1."
	ko "   Il gestore c'e' — src/pagina.html:331 — e non spedisce."
	ko "   ⇒ E' del PRODOTTO, e va scritto come rilievo, non curato qui."
	E=1
fi
inf "⛔ E questo giro non ha speso nessun tentativo fallito: nessun ban, nessuno sblocco."
exit "$E"
