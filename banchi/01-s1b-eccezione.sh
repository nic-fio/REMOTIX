#!/bin/bash
#
# 01-s1b-eccezione.sh — S1b: quanti giorni dura l'eccezione sul certificato,
# su Chrome.  ⏳ E' un orologio da SETTE GIORNI: si avvia una volta e si
# interroga una volta al giorno.
#
#   bash banchi/01-s1b-eccezione.sh avvia    ⏳ il giorno 0: concede l'eccezione
#   bash banchi/01-s1b-eccezione.sh oggi        un giro di controllo (ogni giorno)
#   bash banchi/01-s1b-eccezione.sh stato       che cosa si sa finora
#
# ⚠ GIRA DA QUESTA PARTE DEL FILO — i browser stanno sul portatile, non sul
#   server (come `01-b2-lancia-sonda.sh`).  Il sito sta sul server.
#
# ---------------------------------------------------------------------------
# CHE COSA MISURA, E CHE COS'E' GIA' NOTO
#
# `[R]` `kCertErrorBypassExpirationInSeconds = 604800` — una settimana — in
# `stateful_ssl_host_state_delegate.cc:43`, col commento *«Certificate error
# bypasses are remembered for one week»* (S1 §3.1).  ⛔ **Questa misura non
# serve a sapere il numero: serve a sapere se quel numero regge sul campo.**
# `STUDI.md` §web §8 lo dice con queste parole.
#
# ⛔ E S1 §4.2 P5 **non e' questa prova**.  `FASI.md` §01-filo-nudo manda a
#    `S1 §4.2 P5` per S1b, ma P5 e' la prova del contesto sicuro (Service
#    Worker, keyboard lock, appunti, `isSecureContext`).  **Nel rapporto S1 non
#    esiste nessuna prova di banco sulla durata**: la durata e' solo sorgente
#    letto.  Questo banco e' nuovo, e il rimando va corretto.
#
# ---------------------------------------------------------------------------
# ⛔ IL CONTROLLO CHE DICE *NO*, E SONO TRE
#
#   1. L'IMPRONTA DEL CERTIFICATO DELLA PAGINA, letta dal filo all'inizio e a
#      ogni giro, deve essere LA STESSA.  L'eccezione di Chrome e' indicizzata
#      sulla coppia (impronta, codice d'errore) `[R]`: se il certificato
#      cambia — un riavvio, un altro banco che rigenera — l'avviso ricompare
#      **subito**, e senza questo controllo si scriverebbe «l'eccezione e'
#      durata quattro giorni» (rilievo R3.15).
#      ⛔ E si legge **dal filo** (`openssl s_client`), non dal file sul
#      server: quel che conta e' il certificato che il browser riceve.
#
#   2. UN PROFILO NUOVO DEVE VEDERE L'AVVISO.  E' la domanda «come apparirebbe
#      il caso opposto?» (`LEZIONI.md` §1.11): se anche un profilo appena nato
#      arriva alla pagina, allora «la pagina si e' aperta» non dimostra niente
#      — vorrebbe dire che il certificato e' diventato fidato, o che lo
#      strumento non sa vedere l'avviso.
#
#   3. IL SITO DEVE ESSERE VIVO.  Prima di ogni verdetto si prende il
#      certificato dal filo: se non risponde, «la pagina non si e' aperta» non
#      vuol dire «l'eccezione e' scaduta», vuol dire che non c'e' nessuno
#      dall'altra parte.  Tre cause, un solo silenzio.
#
#   4. ⛔⭐ IL CANALE DI LETTURA DEVE FUNZIONARE — ed e' nato l'11 agosto 2026,
#      dal rilievo A27, che e' il piu' grave che questo file abbia avuto.
#
#      `visita()` rispondeva **NO** in ogni caso che non fosse un riscontro:
#      ssh caduto, credenziali rifiutate, `01-s1b-visite.jsonl` cancellato o
#      rinominato, il sito acceso da un percorso diverso.  ⛔ E il controllo
#      numero 2 — «un profilo nuovo deve NON arrivare» — legge **lo stesso
#      canale**: a canale rotto il profilo nuovo da' NO, e quel controllo **si
#      dichiara passato da se'**.
#
#      Caso concreto, e non e' teorico: qualcuno ripulisce
#      `/media/REMOTIX/src/01-s1b-visite.jsonl`.  Il giro di domani stampa «un
#      profilo appena nato NON arriva alla pagina: lo strumento distingue», poi
#      «la pagina NON si apre», e chiude con **«OK a 1.00 giorni l'eccezione NON
#      c'e' piu': e' questo il numero di S1b»** — il numero della misura, in
#      verde, da uno strumento muto.  ⛔ Ed e' un orologio da sette giorni: se
#      sbaglia, se ne accorge qualcuno **fra una settimana**.
#
#      ⭐ Il controllo positivo che chiude il buco: **una visita che e'
#      certamente avvenuta deve comparire nel registro**.  Si spedisce al sito
#      un `POST /esito` con un token nostro — la stessa strada che la pagina
#      usa con `sendBeacon` — e poi lo si rilegge dal registro con lo stesso
#      `ssh` di `visita()`.  Se non torna, il canale e' rotto e **nessun
#      verdetto si da'**.
#      ⚠ E si dichiara che cosa questo controllo NON prova: non prova che un
#        BROWSER arrivi alla pagina (li' c'e' di mezzo l'interstiziale, che e'
#        quel che si misura).  Prova che il server scrive, che `ssh` legge e
#        che il `grep` trova — cioe' i tre pezzi su cui il verdetto poggia e
#        che nessun altro controllo guardava.
#
# ---------------------------------------------------------------------------
# ⛔ LE TRE TRAPPOLE GIA' PAGATE DA ALTRI, EVITATE QUI
#
#   - ⛔ **niente `localhost`**: Chrome ha una corsia riservata per localhost
#     (`ssl_manager.cc:290-297`), e li' la misura non rappresenta niente.  Si
#     usa l'indirizzo privato del server, da un'altra macchina — S1 §4.5.3.
#   - ⛔ **niente navigazione privata**: e' un deposito diverso da quello
#     normale, e accettare di la' e provare di qua non misura la stessa cosa
#     — S1 §4.5.1.  Qui il profilo e' nostro, persistente, e vive fuori dal
#     deposito di chiunque altro.
#   - ⛔ **l'indirizzo cambia a ogni giro** (`?giro=…`): senza, la pagina
#     potrebbe arrivare **dalla cache** e il banco leggerebbe «l'eccezione
#     regge» il giorno dopo che e' scaduta.
#
# ⛔ E `--ignore-certificate-errors` NON compare in questo file.  Sarebbe il
#    modo piu' rapido di far aprire la pagina e il modo piu' sicuro di non
#    misurare piu' niente.
#
# ---------------------------------------------------------------------------
# DOVE VIVE LO STATO
#
#   ~/.remotix-s1b/profilo   il profilo di Chrome che porta l'eccezione.
#                            ⛔ FUORI dal deposito del progetto apposta: e'
#                            grosso, cambia da solo, e deve sopravvivere sette
#                            giorni senza che nessun `git` lo tocchi.
#   banchi/01-s1b-stato.jsonl  una riga per giro, con la data, l'impronta e la
#                            versione esatta di Chrome.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
RADICE=$(dirname "$QUI")
IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7452}
CERTDIR=${CERTDIR:-/media/REMOTIX/s1b-certificato}
SRC=/media/REMOTIX/src
PROFILO=${PROFILO:-$HOME/.remotix-s1b/profilo}
STATO=$QUI/01-s1b-stato.jsonl
SCHERMO=${SCHERMO:-:77}
T=$(mktemp -d)

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }
ssh_()  { python3 "$RADICE/v1/strumenti/sshpw.py" "$@"; }

PID_X=
congedo()
{
	[ -n "$PID_X" ] && { kill "$PID_X" 2>/dev/null; wait "$PID_X" 2>/dev/null; }
	rm -rf "$T"
}
trap congedo EXIT

# ---------------------------------------------------------------------------
# Il sito, sul server.
#
# ⛔ Il certificato si genera UNA VOLTA SOLA e non si rigenera mai: rigenerarlo
#    e' precisamente il modo di azzerare l'orologio senza accorgersene.  Il
#    programma qui sotto lo crea solo se non c'e', e lo dice.
# ---------------------------------------------------------------------------
accendi_sito()
{
	ssh_ "bash $SRC/01-s1b-sito.sh accendi $IND $PORTA $CERTDIR" >"$T/acceso.log" 2>&1
	local stato=$?
	sed 's/^/        /' "$T/acceso.log"
	return $stato
}

spegni_sito()
{
	ssh_ "bash $SRC/01-s1b-sito.sh spegni" >/dev/null 2>&1
}

# ⛔ L'impronta si prende DAL FILO: e' il certificato che il browser riceve.
#    Leggerla dal file sul server sarebbe leggere le nostre intenzioni.
impronta_dal_filo()
{
	printf 'Q\n' | timeout 15 openssl s_client -connect "$IND:$PORTA" >"$T/catena.txt" 2>/dev/null
	if ! grep -F "BEGIN CERTIFICATE" "$T/catena.txt" >/dev/null 2>&1; then
		return 1
	fi
	openssl x509 -in "$T/catena.txt" -outform der 2>/dev/null \
	    | openssl dgst -sha256 -binary | base64 -w0
}

# ---------------------------------------------------------------------------
# Lo schermo finto.
#
# ⛔ `xvfb-run` no, `Xvfb` a mano si: il numero dello schermo deve essere NOTO,
#    o `xdotool` non sa dove scrivere.  E Chrome gira **non** in `--headless`:
#    la lezione di B2 del 10 agosto dice che li' si dichiara
#    `HeadlessChrome/151`, cioe' un motore con un altro nome — e questa misura
#    e' su Chrome, non su un suo cugino.
# ---------------------------------------------------------------------------
MISURA=1280x1024
accendi_schermo()
{
	if [ -e "/tmp/.X11-unix/X${SCHERMO#:}" ]; then
		# ⛔ RILIEVO A29, 11 agosto 2026: «se esiste, uso quello» — e non si
		#    verificava ne' di che geometria fosse ne' chi l'avesse acceso.
		#    `01-s5-tela.sh` usa lo **stesso numero di schermo** predefinito e
		#    lo apre a 1920x1080; qui serve 1280x1024.  Un giro di S5 rimasto
		#    appeso lascia li' uno schermo di un'altra misura, e la finestra di
		#    Chrome — che `xdotool` deve trovare e cliccare a **coordinate
		#    fisse** (`mousemove 640 500`) — nascerebbe su una scena diversa da
		#    quella dichiarata nel rapporto.  B0.1 vuole che lo stato iniziale
		#    si dichiari **e si verifichi**.
		local dim
		dim=$(env -u WAYLAND_DISPLAY xdpyinfo -display "$SCHERMO" 2>"$T/xdpy.err" \
		    | sed -n 's/^  dimensions:  *\([0-9x]*\).*/\1/p')
		if [ -z "$dim" ]; then
			ko "⛔ lo schermo $SCHERMO risulta in uso e non so di che misura sia:"
			sed 's/^/        /' "$T/xdpy.err"
			ko "   «Non lo so» non si arrotonda a «va bene»: la concessione si"
			ko "   batte a coordinate fisse, e su una scena ignota clicca a caso."
			return 1
		fi
		if [ "$dim" != "$MISURA" ]; then
			ko "⛔ lo schermo $SCHERMO e' gia' acceso a $dim, e questo banco"
			ko "   dichiara $MISURA.  ⚠ 01-s5-tela.sh usa lo stesso numero di"
			ko "   schermo a 1920x1080: probabilmente e' rimasto appeso un suo"
			ko "   giro.  Chiudilo (per PID, mai con pkill -f) e rilancia, oppure"
			ko "   lancia questo con SCHERMO=:78."
			return 1
		fi
		inf "lo schermo $SCHERMO era gia' acceso, ed e' della misura dichiarata"
		inf "($dim): verificato, non supposto"
		return 0
	fi
	Xvfb "$SCHERMO" -screen 0 ${MISURA}x24 >"$T/xvfb.log" 2>&1 &
	PID_X=$!
	sleep 2
	if [ ! -d "/proc/$PID_X" ]; then
		ko "Xvfb non e' partito:"
		sed 's/^/        /' "$T/xvfb.log"
		return 1
	fi
	return 0
}

# ---------------------------------------------------------------------------
# Una visita, con un profilo dato.  Stampa «SI» o «NO» e torna 0 sempre:
# l'esito e' un dato, non un guasto.
#
#   $1 = cartella del profilo   $2 = etichetta   $3 = «concedi» oppure vuoto
# ---------------------------------------------------------------------------
visita()
{
	local profilo=$1 etichetta=$2 concedi=${3:-}
	local giro url pid
	giro="$etichetta-$(date +%s)-$RANDOM"
	url="https://$IND:$PORTA/01-s1b-pagina.html?giro=$giro"

	mkdir -p "$profilo"
	# ⛔ `env -u WAYLAND_DISPLAY` E `--ozone-platform=x11`, E SONO IL CUORE
	#    DELL'AVVIO.  `[M]` 10 agosto 2026: questa macchina ha
	#    `WAYLAND_DISPLAY=wayland-0`, e Chrome 151 sceglie Wayland da se'.
	#    Con `DISPLAY=:77` davanti al comando la finestra si apriva LO STESSO
	#    sulla scrivania vera dell'utente, mentre `xdotool` cercava su :77 e
	#    trovava **zero finestre**: il banco concludeva «la concessione e'
	#    fallita» e la causa era che stava guardando un altro schermo.
	#    ⚠ Ed e' anche una scortesia evitata: nessuna finestra sbuca piu' in
	#      faccia a chi sta lavorando.
	env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO google-chrome --ozone-platform=x11 \
	    --user-data-dir="$profilo" \
	    --no-first-run --no-default-browser-check --disable-sync \
	    --window-size=1280,1000 "$url" >"$T/chrome-$etichetta.log" 2>&1 &
	pid=$!
	sleep 14

	if [ "$concedi" = concedi ]; then
		# ⛔ LA CONCESSIONE PASSA PER LA STESSA PORTA DELL'UTENTE.
		#    «thisisunsafe» battuto sull'interstiziale chiama lo stesso
		#    `proceed` del bottone «Procedi»: e' una scorciatoia di tastiera,
		#    non un interruttore che salta il meccanismo.  ⚠ Che sia davvero lo
		#    stesso percorso NON si crede sulla parola: subito dopo il banco
		#    legge la SCADENZA memorizzata nel profilo, e se non e' a sette
		#    giorni lo dice.
		# ⛔ LA DIAGNOSTICA VA SU STANDARD ERROR, e non e' pignoleria: questa
		#    funzione RESTITUISCE «SI» o «NO» stampandolo, e chi la chiama la
		#    cattura con `$(...)`.  `[M]` 10 agosto 2026: con le righe di
		#    diagnostica sullo stesso flusso, il valore restituito diventava
		#    «--  concedo l'eccezione…\nSI», che non e' uguale a «SI» — e il
		#    banco ha dichiarato fallita una concessione **riuscita**.  Un
		#    rosso su strumento sano, per un flusso sbagliato.
		inf "concedo l'eccezione: batto «thisisunsafe» sull'interstiziale" >&2
		env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO xdotool search --onlyvisible --class chrome >"$T/finestre.txt" 2>&1
		inf "finestre di Chrome trovate: $(wc -l < "$T/finestre.txt")" >&2
		env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO xdotool search --onlyvisible --class chrome windowactivate --sync \
		    windowfocus --sync >/dev/null 2>&1
		env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO xdotool mousemove 640 500 click 1 >/dev/null 2>&1
		sleep 1
		env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO xdotool type --delay 120 'thisisunsafe' >/dev/null 2>&1
		sleep 10
	fi

	# ⛔ Si chiude con TERM e si aspetta: Chrome scrive `Preferences` all'uscita,
	#    e un `kill -9` porterebbe via la decisione appena presa insieme al
	#    processo.
	kill "$pid" 2>/dev/null
	wait "$pid" 2>/dev/null
	sleep 3

	cerca_nel_registro "$giro"
}

# ---------------------------------------------------------------------------
# ⛔ LA LETTURA DEL REGISTRO DELLE VISITE — TRE ESITI, NON DUE (rilievo A27).
#
# Stampa «SI» · «NO» · «IGNOTO», e torna 0 sempre: l'esito e' un dato.
#
# ⛔ «Il token non c'e'» e «non ho potuto guardare» erano la stessa stringa, e
#    la seconda e' quella che fa scrivere il numero di S1b da uno strumento
#    muto.  Qui il comando remoto **si fa stampare il proprio stato d'uscita**
#    (la forma di `01-b11-guasto.sh:92-102`), invece di fidarsi che `ssh` lo
#    propaghi:
#      grep -c  →  0 trovato · 1 non trovato · ≥2 ⛔ non ho potuto leggere
#    e se il marcatore `S1B-FINE=` non torna affatto, il comando non e' nemmeno
#    arrivato in fondo — che e' un terzo fatto ancora.
# ⚠ Niente `grep -q` dentro un tubo con `pipefail` e niente `| tail` su un
#   comando remoto: sono due trappole gia' pagate da questo progetto.  Il testo
#   torna in una variabile, e si taglia QUI.
#
# ---------------------------------------------------------------------------
# ⛔⭐ RILIEVO A31, 11 agosto 2026 — LA CURA DI A27 AVEVA LO STESSO BUCO,
#     ENTRATO DA UN'ALTRA PORTA, E OGGI HA MENTITO DUE VOLTE DI FILA.
#
# Il conto si leggeva **dalla riga 1** (`sed -n '1s/…'`).  Ma la riga 1 di un
# comando remoto non appartiene al comando: e' la roba di `ssh`.  `[M]` 11
# agosto 2026, uscita vera:
#     riga 1: «nicfio@192.168.0.2's password: »
#     riga 2: «tput: No value for $TERM and no -T specified»
#     riga 3: «1»                ← il conto, che nessuno guardava
#     riga 4: «S1B-FINE=0»       ← e grep dice: TROVATO
# Il conto usciva **vuoto**, `${conto:-0}` lo arrotondava a **zero**, e la
# funzione stampava un **«NO» pulito e sicuro** — mentre la riga accanto,
# nello stesso testo, diceva «trovato».  ⛔ I due fatti erano tutt'e due
# presenti e si contraddicevano, e il programma credeva a quello che veniva
# dal posto fragile.
#
# ⚠ E nessuno l'aveva rotta scrivendo questa funzione: e' cambiato il RUMORE
#   di `ssh` — chiave installata, `$TERM` assente — cioe' un pezzo che questo
#   file non nomina nemmeno.  Uno strumento che poggia sul NUMERO DI RIGA di
#   un'uscita altrui si rompe per fatti che non sono suoi.
#
# ⭐ Due cure, e la seconda vale piu' della prima:
#   1. ogni valore torna **etichettato** (`S1B-CONTO=`), quindi si trova
#      ovunque stia, e il rumore non ha piu' un posto in cui contare.
#   2. i due fatti **devono andare d'accordo**: `grep` che dice «trovato» e un
#      conto di zero e' una contraddizione, e da una contraddizione non esce
#      un verdetto — esce «IGNOTO».  E' quel confronto, non l'etichetta, che
#      avrebbe fermato oggi la bugia.
# ---------------------------------------------------------------------------
cerca_nel_registro() # $1 = il token da cercare
{
	local token=$1 tutto stato conto
	tutto=$(ssh_ "n=\$(grep -c -F '$token' $SRC/01-s1b-visite.jsonl 2>/dev/null); s=\$?; printf 'S1B-CONTO=%s\nS1B-FINE=%s\n' \"\$n\" \"\$s\"" 2>&1)
	stato=$(printf '%s\n' "$tutto" | sed -n 's/^S1B-FINE=\([0-9][0-9]*\)$/\1/p' | head -1)
	conto=$(printf '%s\n' "$tutto" | sed -n 's/^S1B-CONTO=\([0-9][0-9]*\)$/\1/p' | head -1)
	if [ -z "$stato" ]; then
		printf 'IGNOTO\n'
		{ ko "⛔ il comando remoto non e' arrivato in fondo: nessun «S1B-FINE»."
		  ko "   Non e' «la visita non c'e'»: e' «non ho potuto guardare»."
		  printf '%s\n' "$tutto" | sed -n '1,4p' | sed 's/^/        /'; } >&2
		return 0
	fi
	if [ "$stato" -ge 2 ]; then
		printf 'IGNOTO\n'
		{ ko "⛔ il registro delle visite non si e' potuto leggere (grep esce $stato):"
		  printf '%s\n' "$tutto" | sed -n '1,4p' | sed 's/^/        /'
		  ko "   ⛔ «non l'ho trovato» e «non ho potuto leggere» sono due fatti."; } >&2
		return 0
	fi
	if [ -z "$conto" ]; then
		printf 'IGNOTO\n'
		{ ko "⛔ il conto non e' tornato («S1B-CONTO=» non c'e'), e grep dice $stato."
		  ko "   ⛔ Un conto assente NON si arrotonda a zero: e' A31 in persona."
		  printf '%s\n' "$tutto" | sed -n '1,4p' | sed 's/^/        /'; } >&2
		return 0
	fi
	# ⭐ IL CONFRONTO CHE OGGI AVREBBE FERMATO LA BUGIA: grep dice 0 quando ha
	#    trovato qualcosa, e allora il conto deve essere > 0.  Se i due fatti si
	#    contraddicono, il testo non e' quello che credo di star leggendo.
	if { [ "$stato" -eq 0 ] && [ "$conto" -eq 0 ]; } || \
	   { [ "$stato" -eq 1 ] && [ "$conto" -gt 0 ]; }; then
		printf 'IGNOTO\n'
		{ ko "⛔ I DUE FATTI SI CONTRADDICONO: grep esce $stato (0=trovato,"
		  ko "   1=non trovato) ma il conto e' $conto.  Non e' possibile."
		  ko "   ⛔ Da una contraddizione non esce un verdetto — vedi A31."
		  printf '%s\n' "$tutto" | sed -n '1,6p' | sed 's/^/        /'; } >&2
		return 0
	fi
	if [ "$conto" -gt 0 ]; then
		printf 'SI\n'
	else
		printf 'NO\n'
	fi
}

# ---------------------------------------------------------------------------
# ⭐ IL CONTROLLO POSITIVO DEL CANALE — la cura di A27.
#
# Si scrive una riga nel registro passando dalla STESSA porta della pagina
# (`POST /esito`, che e' quel che `sendBeacon` fa) e la si rilegge con lo
# STESSO `ssh` di `visita()`.  Se il token torna, i tre pezzi su cui il
# verdetto poggia — il server che scrive, `ssh` che legge, il `grep` che trova
# — funzionano tutti e tre; se non torna, non si da' nessun verdetto.
#
# ⛔ `curl -k` qui NON e' una scorciatoia sulla misura: non tocca nessun
#    profilo e non concede nessuna eccezione.  E' lo strumento che si certifica,
#    non il fatto che si misura — e resta vero che `--ignore-certificate-errors`
#    non compare in nessuna riga di Chrome, che e' l'altra cosa.
# ---------------------------------------------------------------------------
CANALE=IGNOTO
controlla_canale()
{
	local token risposta esito
	token="canale-$(date +%s)-$RANDOM"
	risposta=$(curl -sk --max-time 15 -o /dev/null -w '%{http_code}' \
	    -X POST -H 'Content-Type: application/json' \
	    --data "{\"giro\":\"$token\",\"tipo\":\"CONTROLLO-CANALE\"}" \
	    "https://$IND:$PORTA/esito" 2>"$T/curl.err")
	if [ "$risposta" != 204 ]; then
		ko "⛔ il sito non ha accettato la riga di controllo (HTTP «${risposta:-—}»):"
		sed 's/^/        /' "$T/curl.err"
		CANALE=NO
		return 1
	fi
	sleep 1
	esito=$(cerca_nel_registro "$token")
	case "$esito" in
	SI)	ok "⭐ CONTROLLO POSITIVO DEL CANALE: una visita che e' certamente"
		ok "   avvenuta si rilegge nel registro.  Da adesso «NO» vuol dire"
		ok "   davvero «non e' arrivata», e non «non ho potuto guardare»"
		CANALE=SI
		return 0 ;;
	*)	ko "⛔ IL CANALE DI LETTURA E' ROTTO: ho appena scritto una riga nel"
		ko "   registro passando dalla porta della pagina, e rileggendolo non la"
		ko "   trovo (esito «$esito»)."
		ko "   ⛔ Allora ogni «NO» di questo giro vuol dire «non ho potuto"
		ko "   guardare», compreso quello del profilo nuovo — che si"
		ko "   dichiarerebbe passato da se'.  Nessun verdetto si da'."
		CANALE=$esito
		return 1 ;;
	esac
}

# ---------------------------------------------------------------------------
# La scadenza che Chrome si e' segnato, letta dal profilo.
#
# ⚠ E' una seconda misura sullo stesso fatto, non la stessa: la prima e' «la
#   pagina si apre ancora», questa e' «che cosa Chrome dice di aver deciso».
#   Due strumenti diversi sullo stesso fatto — e se si contraddicono, e' un
#   dato anche quello.
# ⛔ E' materiale NUOVO: il rapporto S1 nomina `StatefulSSLHostStateDelegate`
#   ma non dice dove finisca su disco.  Quindi qui non si presume: si cerca, e
#   se non si trova si scrive «IGNOTO», non «zero».
# ---------------------------------------------------------------------------
scadenza_memorizzata()
{
	python3 - "$PROFILO" <<'PY'
import json, os, sys
from datetime import datetime, timezone

radice = sys.argv[1]
trovati = []
for cartella, _, file in os.walk(radice):
    if "Preferences" in file:
        percorso = os.path.join(cartella, "Preferences")
        try:
            dati = json.load(open(percorso, encoding="utf-8"))
        except Exception:
            continue
        decisioni = (dati.get("profile", {}).get("content_settings", {})
                         .get("exceptions", {}).get("ssl_cert_decisions"))
        if decisioni:
            trovati.append((percorso, decisioni))

if not trovati:
    print("IGNOTO: nessuna voce `ssl_cert_decisions` in nessun `Preferences` sotto", radice)
    print("        ⚠ non e' «zero decisioni»: e' «non l'ho trovata dove guardavo».")
    sys.exit(0)

for percorso, decisioni in trovati:
    for chiave, voce in decisioni.items():
        impostazione = voce.get("setting") or {}
        scadenza = voce.get("expiration") or impostazione.get("decision_expiration_time")
        versione = impostazione.get("version")
        decisioni_host = impostazione.get("cert_exceptions_map") or impostazione
        print(f"chiave   : {chiave}")
        print(f"file     : {percorso}")
        print(f"contenuto: {json.dumps(impostazione, ensure_ascii=False)[:400]}")
        if scadenza:
            # ⛔ NON e' un tempo Unix: Chrome conta in MICROSECONDI dal
            #    1° gennaio 1601 (`base::Time`).  `[M]` 10 agosto 2026: letto
            #    come tempo Unix, «13431474587889370» diventa un anno che non
            #    esiste, e il banco stampava «valore non interpretabile» su un
            #    numero perfettamente sano.  I 11 644 473 600 secondi sono la
            #    distanza fra le due origini.
            try:
                secondi = float(scadenza) / 1e6 - 11644473600
                quando = datetime.fromtimestamp(secondi, timezone.utc)
                resta = (quando - datetime.now(timezone.utc)).total_seconds()
                print(f"scadenza : {quando.isoformat()}  (fra {resta/86400:.3f} giorni, "
                      f"{resta:.0f} s)")
                print(f"           ⇒ atteso 604800 s (7 giorni) al momento della concessione,")
                print(f"             che e' il [R] di S1 §3.1 letto adesso da un secondo strumento")
            except Exception as sbaglio:
                print(f"scadenza : valore non interpretabile: {scadenza!r} ({sbaglio})")
        else:
            print("scadenza : IGNOTA — la voce c'e' ma non porta una scadenza leggibile")
        _ = versione, decisioni_host
PY
}

# ---------------------------------------------------------------------------
# ⭐ I DUE NUMERI DI CHROME, LETTI GREZZI — e sono il pezzo di S1b che non
#    aveva bisogno di aspettare nessuno.
#
# Nel profilo Chrome scrive DUE istanti, non uno:
#   `last_modified`             quando ha preso la decisione
#   `decision_expiration_time`  quando la butta
# ⛔ Il rapporto confrontava la SCADENZA col nostro orologio al momento del
#    clic, e trovava 13,111 s di scarto sui 604 800 attesi — poi dichiarati
#    `[?]`.  Quei 13 secondi erano la distanza fra DUE OROLOGI (il nostro che
#    leggeva, il suo che scriveva), non un difetto della costante.
# ⭐ Presi tutt'e due dalla stessa mano, lo scarto e' di TRENTA MICROSECONDI.
#    Stampa una riga sola: «<inizio> <scadenza> <differenza in secondi>».
# ---------------------------------------------------------------------------
due_numeri() # $1 = profilo
{
	python3 - "$1" <<'PY'
import json, os, sys
for cartella, _, file in os.walk(sys.argv[1]):
    if "Preferences" not in file:
        continue
    try:
        d = json.load(open(os.path.join(cartella, "Preferences"), encoding="utf-8"))
    except Exception:
        continue
    dec = (d.get("profile", {}).get("content_settings", {})
             .get("exceptions", {}).get("ssl_cert_decisions")) or {}
    for chiave, voce in dec.items():
        imp = voce.get("setting") or {}
        sca = imp.get("decision_expiration_time") or voce.get("expiration")
        mod = voce.get("last_modified")
        if sca and mod:
            print(mod, sca, (int(sca) - int(mod)) / 1e6, chiave)
            sys.exit(0)
sys.exit(1)
PY
}

# ---------------------------------------------------------------------------
# ⭐ SPOSTARE LA SCADENZA INVECE DI ASPETTARLA.
#
# Riscrive `decision_expiration_time` (e `expiration`, se c'e') a «adesso piu'
# $2 secondi», che puo' essere NEGATIVO.  Torna 0 se ha toccato almeno una
# voce, 1 se non ne ha trovate — ⛔ e «non ne ho trovate» non e' «fatto».
#
# ⚠ CHE COSA QUESTO NON DIMOSTRA, detto prima di usarlo: che il giorno 7 nel
#   mondo vero succeda questo.  Dimostra che Chrome **onora l'istante che si e'
#   segnato**.  Messo insieme a `due_numeri` — che quell'istante e' il clic piu'
#   604 800 s — i due fatti danno la durata senza aspettarla.
#
# ⛔ E si lavora SEMPRE SU UNA COPIA: il profilo vero porta l'orologio dei sette
#    giorni, che e' la conferma gratis del 17-18 agosto.  Rovinarlo per fare
#    prima sarebbe pagare la fretta con l'unica prova indipendente che c'e'.
# ---------------------------------------------------------------------------
scrivi_scadenza() # $1 = profilo (una COPIA)   $2 = secondi da adesso
{
	python3 - "$1" "$2" <<'PY'
import json, os, sys, time
radice, delta = sys.argv[1], float(sys.argv[2])
# base::Time conta in microsecondi dal 1° gennaio 1601.
adesso = (time.time() + 11644473600) * 1e6
nuovo = str(int(adesso + delta * 1e6))
toccati = 0
for cartella, _, file in os.walk(radice):
    if "Preferences" not in file:
        continue
    percorso = os.path.join(cartella, "Preferences")
    try:
        d = json.load(open(percorso, encoding="utf-8"))
    except Exception:
        continue
    dec = (d.get("profile", {}).get("content_settings", {})
             .get("exceptions", {}).get("ssl_cert_decisions"))
    if not dec:
        continue
    for chiave, voce in dec.items():
        imp = voce.get("setting") or {}
        if "decision_expiration_time" in imp:
            print(f"        {chiave}")
            print(f"          decision_expiration_time: {imp['decision_expiration_time']} → {nuovo}")
            imp["decision_expiration_time"] = nuovo
            toccati += 1
        if "expiration" in voce and voce["expiration"] not in ("0", 0):
            voce["expiration"] = nuovo
            toccati += 1
    with open(percorso, "w", encoding="utf-8") as f:
        json.dump(d, f)
sys.exit(0 if toccati else 1)
PY
}

registra() # $1 = json compatto
{
	python3 - "$STATO" "$1" <<'PY'
import json, sys
from datetime import datetime, timezone
d = json.loads(sys.argv[2])
d["ora"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
with open(sys.argv[1], "a", encoding="utf-8") as f:
    f.write(json.dumps(d, ensure_ascii=False) + "\n")
print("registrato:", json.dumps(d, ensure_ascii=False))
PY
}

impronta_giorno0()
{
	python3 - "$STATO" <<'PY'
import json, os, sys
if not os.path.exists(sys.argv[1]):
    sys.exit(1)
for riga in open(sys.argv[1], encoding="utf-8"):
    try:
        d = json.loads(riga)
    except Exception:
        continue
    if d.get("giro") == "avvia" and d.get("impronta"):
        print(d["impronta"], d["ora"], sep="\t")
        sys.exit(0)
sys.exit(1)
PY
}

# ===========================================================================
COMANDO=${1:-oggi}
VERSIONE=$(google-chrome --version 2>&1)

case "$COMANDO" in
stato)
	log "Che cosa si sa finora"
	if [ -f "$STATO" ]; then
		cat "$STATO"
	else
		inf "nessun giro registrato: l'orologio non e' ancora partito"
	fi
	exit 0
	;;
avvia|oggi|scavalca) ;;
*) echo "uso: $0 {avvia|oggi|scavalca|stato}" >&2; exit 2 ;;
esac

log "1. Il sito, sul server"
if ! accendi_sito; then
	ko "il sito non si e' acceso: senza, non c'e' niente da misurare"
	exit 3
fi
trap 'spegni_sito; congedo' EXIT

log "2. ⛔ Il controllo dell'impronta — quello senza cui la misura mente"
IMPRONTA=$(impronta_dal_filo)
if [ -z "$IMPRONTA" ]; then
	ko "il sito non presenta nessun certificato sul filo ($IND:$PORTA)."
	ko "   ⛔ Questo NON e' «l'eccezione e' scaduta»: e' «non c'e' nessuno»."
	exit 3
fi
ok "certificato servito, impronta SHA-256 del DER: $IMPRONTA"
APPROVATI=$((${APPROVATI:-0} + 1))

log "2-bis. ⭐ Il controllo positivo del CANALE DI LETTURA (A27)"
if controlla_canale; then
	APPROVATI=$((APPROVATI + 1))
fi

PRIMA=$(impronta_giorno0)
if [ -n "$PRIMA" ]; then
	IFS=$'\t' read -r IMP0 ORA0 <<< "$PRIMA"
	if [ "$IMP0" = "$IMPRONTA" ]; then
		ok "e' LA STESSA del giorno 0 ($ORA0): l'orologio misura una cosa sola"
		APPROVATI=$((APPROVATI + 1))
	else
		ko "⛔ L'IMPRONTA E' CAMBIATA dal giorno 0:"
		ko "     giorno 0: $IMP0"
		ko "     adesso  : $IMPRONTA"
		ko "   L'eccezione di Chrome e' indicizzata sull'impronta: da adesso"
		ko "   l'avviso ricompare per il CERTIFICATO NUOVO, non per il tempo."
		ko "   ⛔ La misura e' da rifare da capo, e il numero non si scrive."
		registra "{\"giro\":\"oggi\",\"esito\":\"IMPRONTA_CAMBIATA\",\"impronta\":\"$IMPRONTA\",\"impronta_giorno0\":\"$IMP0\",\"chrome\":\"$VERSIONE\"}"
		exit 4
	fi
fi

log "3. Lo schermo finto e il browser"
if ! accendi_schermo; then exit 3; fi
inf "Chrome: $VERSIONE"
inf "profilo persistente: $PROFILO"

if [ "$COMANDO" = avvia ]; then
	log "4. ⏳ GIORNO 0 — si concede l'eccezione"
	if [ -d "$PROFILO" ]; then
		inf "⚠ il profilo esiste gia': se l'orologio era gia' partito, questo giro"
		inf "  lo RIAVVIA e il conto ricomincia da oggi.  Lo si dice."
	fi
	# ⛔ E l'orologio dei sette giorni NON si avvia da uno strumento muto: se il
	#    canale di lettura non e' certificato, «la pagina non si apriva prima» e
	#    «la pagina si apre adesso» sono tutt'e due indistinguibili dal silenzio,
	#    e il giorno 0 verrebbe preso su niente (A27).
	if [ "$CANALE" != SI ]; then
		ko "⛔ non avvio niente: il canale di lettura non e' certificato."
		ko "   Un orologio da sette giorni fatto partire da uno strumento muto"
		ko "   si scopre rotto fra una settimana."
		exit 6
	fi
	PRIMA_CONCESSIONE=$(visita "$PROFILO" prima "")
	inf "prima di concedere, la pagina si apriva? $PRIMA_CONCESSIONE"
	if [ "$PRIMA_CONCESSIONE" = SI ]; then
		ko "⛔ la pagina si apre GIA' senza aver concesso niente."
		ko "   Allora non c'e' nessun avviso da superare, e la durata"
		ko "   dell'eccezione non e' quel che si sta per misurare."
		exit 5
	fi
	if [ "$PRIMA_CONCESSIONE" != NO ]; then
		ko "⛔ non so se la pagina si aprisse gia' ($PRIMA_CONCESSIONE): non e'"
		ko "   «non si apriva», e non si parte da uno stato ignoto (B0.1)."
		exit 6
	fi
	DOPO=$(visita "$PROFILO" concessione concedi)
	if [ "$DOPO" = SI ]; then
		ok "eccezione concessa: la pagina adesso si apre"
	else
		ko "la pagina NON si apre nemmeno dopo aver battuto «thisisunsafe»."
		ko "   ⛔ L'orologio NON e' partito.  Da fare a mano, una volta:"
		ko "     DISPLAY=:0 google-chrome --user-data-dir=$PROFILO https://$IND:$PORTA/01-s1b-pagina.html"
		ko "     e cliccare «Avanzate» → «Procedi su $IND (non sicuro)»."
		registra "{\"giro\":\"avvia\",\"esito\":\"CONCESSIONE_FALLITA\",\"impronta\":\"$IMPRONTA\",\"chrome\":\"$VERSIONE\"}"
		exit 5
	fi
	log "5. La scadenza che Chrome si e' segnato"
	scadenza_memorizzata | tee "$T/scadenza.txt" | sed 's/^/        /'
	SCAD=$(sed -n 's/^scadenza : //p' "$T/scadenza.txt" | head -1)
	registra "{\"giro\":\"avvia\",\"esito\":\"CONCESSA\",\"impronta\":\"$IMPRONTA\",\"chrome\":\"$VERSIONE\",\"scadenza_memorizzata\":\"${SCAD:-IGNOTA}\"}"
elif [ "$COMANDO" = scavalca ]; then
	# =====================================================================
	# ⭐ IL GIRO CHE NON ASPETTA SETTE GIORNI.
	#
	# La domanda di S1b e' una sola, e non e' «quanto dura»: e' **che frase si
	# dice all'utente** — «una volta» oppure «una volta a settimana».  Per
	# rispondere servono due fatti, e nessuno dei due ha bisogno del calendario:
	#
	#   1. che istante Chrome si segna          → `due_numeri`, gia' su disco
	#   2. che quell'istante lo ONORI           → si sposta la scadenza indietro
	#
	# ⛔ E un terzo che nessuno aveva posto, e che da solo cambierebbe la
	#    risposta: **Chrome rinnova la scadenza a ogni visita?**  Se lo facesse,
	#    chi si collega tutti i giorni non rivedrebbe mai l'avviso, e «una volta
	#    a settimana» sarebbe falso anche con la costante giusta.  ⏳ L'orologio
	#    da sette giorni **non lo avrebbe mai visto**: lo visita ogni giorno.
	#
	# ⛔ IL PROFILO VERO NON SI TOCCA.  Tutto avviene su una copia; l'orologio
	#    del 17-18 agosto resta in piedi come conferma indipendente e gratis.
	# =====================================================================
	APPROVATI_SC=0

	log "4. ⭐ I due numeri che Chrome si e' scritto da solo"
	if DUE=$(due_numeri "$PROFILO"); then
		read -r N_MOD N_SCA N_DIF N_CHIAVE <<< "$DUE"
		inf "decisione presa : $N_MOD (µs dal 1601)"
		inf "scadenza segnata: $N_SCA"
		inf "chiave           : $N_CHIAVE"
		inf "differenza      : $N_DIF s"
		# ⛔ Il confronto e' fra DUE NUMERI DELLA STESSA MANO: nessun orologio
		#    nostro entra nel conto, quindi nessuno scarto fra orologi da
		#    spiegare.  E' precisamente l'errore che aveva reso `[?]` questa riga.
		if python3 -c 'import sys; sys.exit(0 if abs(float(sys.argv[1])-604800)<1 else 1)' "$N_DIF"; then
			ok "⭐ scadenza − decisione = 604800 s a meno di un secondo:"
			ok "   la costante di S1 §3.1 regge sul campo, misurata [M]"
			APPROVATI_SC=$((APPROVATI_SC + 1))
		else
			ko "⛔ scadenza − decisione = $N_DIF s, e l'atteso e' 604800."
			ko "   ⚠ Questo NON e' uno scarto fra orologi: i due istanti li ha"
			ko "   scritti Chrome. Se non torna, non torna davvero."
		fi
	else
		ko "⛔ nel profilo non trovo la coppia (last_modified, scadenza):"
		ko "   non e' «zero», e' «non l'ho trovata». Niente verdetto su questo."
	fi

	# ⛔ RILIEVO A31, e me l'ero fatto addosso io: da qui in poi OGNI risposta
	#    passa dal registro delle visite.  A canale non certificato, «la copia
	#    non apre» e «non ho potuto guardare» sono la stessa stringa — ed e'
	#    esattamente quel che e' successo al primo giro di questo comando, che
	#    ha dichiarato «COPIA_MUTA» su una visita che nel registro C'ERA.
	#    Il giro `avvia` si ferma qui da sempre; questo si fermava dopo.
	if [ "$CANALE" != SI ]; then
		ko "⛔ NON PROSEGUO: il canale di lettura non e' certificato («$CANALE»)."
		ko "   Ogni «NO» da qui in poi vorrebbe dire «non ho potuto guardare»,"
		ko "   e uscirebbe un verdetto su S1b da uno strumento muto."
		registra "{\"giro\":\"scavalca\",\"esito\":\"CANALE_NON_CERTIFICATO\",\"canale\":\"$CANALE\",\"chrome\":\"$VERSIONE\"}"
		exit 6
	fi

	log "5. La copia — e il primo controllo, che e' sul metodo"
	COPIA=$T/copia
	cp -a "$PROFILO" "$COPIA" || { ko "la copia del profilo non e' riuscita"; exit 3; }
	inf "copiato $PROFILO → $COPIA  ($(du -sh "$COPIA" | cut -f1))"
	PRIMA_SC=$(visita "$COPIA" copia "")
	if [ "$PRIMA_SC" = SI ]; then
		ok "⭐ LA COPIA PORTA L'ECCEZIONE: la pagina si apre."
		ok "   Senza questo, tutto il resto misurerebbe una copia rotta."
		APPROVATI_SC=$((APPROVATI_SC + 1))
	else
		ko "⛔ la copia NON apre la pagina (esito «$PRIMA_SC»)."
		ko "   Allora l'eccezione non sopravvive alla copia, e questo metodo"
		ko "   non e' utilizzabile: ogni «NO» piu' avanti sarebbe gia' spiegato."
		registra "{\"giro\":\"scavalca\",\"esito\":\"COPIA_MUTA\",\"copia_apre\":\"$PRIMA_SC\",\"chrome\":\"$VERSIONE\"}"
		exit 6
	fi

	log "6. ⛔ Chrome rinnova la scadenza quando lo si visita?"
	# ⛔ La domanda che l'orologio da sette giorni non poteva porre, perche' lo
	#    visita tutti i giorni: se ogni visita spostasse la scadenza in avanti,
	#    l'avviso non tornerebbe MAI per chi usa il prodotto — e il banco che
	#    aspetta vedrebbe «regge» al settimo giorno senza sapere perche'.
	if DUE2=$(due_numeri "$COPIA"); then
		read -r M_MOD M_SCA _ _ <<< "$DUE2"
		inf "prima della visita: $N_SCA"
		inf "dopo  la visita   : $M_SCA"
		if [ "$M_SCA" = "$N_SCA" ]; then
			ok "⭐ LA SCADENZA NON SI SPOSTA: visitare la pagina non rinnova"
			ok "   l'eccezione. Quindi «una volta a settimana» vale anche per"
			ok "   chi si collega tutti i giorni"
			RINNOVA=NO
			APPROVATI_SC=$((APPROVATI_SC + 1))
		else
			ko "⛔ LA SCADENZA SI E' SPOSTATA visitando la pagina."
			ko "   Allora chi usa il prodotto ogni giorno non rivede mai"
			ko "   l'avviso, e la frase da dire all'utente cambia."
			RINNOVA=SI
		fi
	else
		ko "⛔ dopo la visita non ritrovo la coppia di istanti"; RINNOVA=IGNOTO
	fi

	log "7. ⛔ IL CONTROLLO CHE DICE *NO*: scadenza spostata IN AVANTI"
	# ⛔ E' il controllo senza cui il punto 8 non dimostra niente.  Al punto 8 la
	#    pagina smettera' di aprirsi: ma «Chrome ha onorato la scadenza» e
	#    «Chrome si e' accorto che gli abbiamo messo le mani nel file e ha
	#    buttato tutto» hanno la STESSA faccia.  ⭐ Qui si usa la stessa,
	#    identica manomissione con una data FUTURA: se passa, la manomissione e'
	#    accettata, e al punto 8 l'unica cosa cambiata sara' il segno.
	if ! scrivi_scadenza "$COPIA" 2592000; then
		ko "⛔ non ho trovato nessuna scadenza da riscrivere: metodo non applicabile"
		exit 6
	fi
	AVANTI=$(visita "$COPIA" avanti "")
	if [ "$AVANTI" = SI ]; then
		ok "⭐ con la scadenza a +30 giorni la pagina si apre ANCORA:"
		ok "   riscrivere quel campo non rompe l'eccezione di per se'"
		APPROVATI_SC=$((APPROVATI_SC + 1))
	else
		ko "⛔ con la scadenza a +30 giorni la pagina NON si apre («$AVANTI»)."
		ko "   Allora e' la SCRITTURA a rompere l'eccezione, non la data: il"
		ko "   punto 8 misurerebbe la nostra manomissione, non Chrome."
		ko "   ⛔ Nessun verdetto. Resta l'orologio del 17-18 agosto."
		registra "{\"giro\":\"scavalca\",\"esito\":\"MANOMISSIONE_RIFIUTATA\",\"avanti\":\"$AVANTI\",\"chrome\":\"$VERSIONE\"}"
		exit 6
	fi

	log "8. ⭐ LA MISURA: scadenza spostata INDIETRO di un giorno"
	scrivi_scadenza "$COPIA" -86400 || { ko "niente da riscrivere"; exit 6; }
	INDIETRO=$(visita "$COPIA" indietro "")
	if [ "$INDIETRO" = NO ]; then
		ok "⭐ con la scadenza gia' passata la pagina NON si apre piu':"
		ok "   Chrome ONORA l'istante che si e' segnato"
		APPROVATI_SC=$((APPROVATI_SC + 1))
	elif [ "$INDIETRO" = SI ]; then
		ko "⛔ con la scadenza GIA' PASSATA la pagina si apre lo stesso."
		ko "   Allora quell'istante Chrome non lo guarda, e la durata"
		ko "   dell'eccezione non e' quella che si e' scritto."
	else
		ko "⛔ esito «$INDIETRO»: non ho potuto guardare. Niente verdetto."
	fi

	log "9. ⛔ E un profilo appena nato deve vedere l'avviso"
	NUOVO_SC=$(visita "$T/profilo-nuovo" nuovo "")
	if [ "$NUOVO_SC" = NO ] && [ "$CANALE" = SI ]; then
		ok "un profilo appena nato NON arriva alla pagina: lo strumento distingue"
		APPROVATI_SC=$((APPROVATI_SC + 1))
	else
		ko "il profilo nuovo da' «$NUOVO_SC» (canale «$CANALE»): controllo non passato"
	fi

	registra "{\"giro\":\"scavalca\",\"differenza_s\":\"${N_DIF:-IGNOTA}\",\"rinnova_a_ogni_visita\":\"${RINNOVA:-IGNOTO}\",\"copia_apre\":\"$PRIMA_SC\",\"avanti_30g\":\"$AVANTI\",\"indietro_1g\":\"$INDIETRO\",\"profilo_nuovo\":\"$NUOVO_SC\",\"approvati\":\"$APPROVATI_SC su 6\",\"impronta\":\"$IMPRONTA\",\"chrome\":\"$VERSIONE\"}"

	log "Esito"
	inf "controlli approvati: $APPROVATI_SC su 6"
	if [ "$APPROVATI_SC" -eq 6 ]; then
		ok "⭐ S1b RISPOSTA, SENZA ASPETTARE: Chrome si segna il clic + 604800 s,"
		ok "   onora quell'istante, e NON lo rinnova visitando la pagina."
		ok "   ⇒ all'utente si dice «una volta a settimana», non «una volta»."
		inf "⚠ Cio' che questo giro NON prova: che il 17 agosto non succeda"
		inf "  anche altro. ⏳ L'orologio vero e' intatto e lo dira' da solo."
	else
		ko "⛔ verdetto NON dato: $APPROVATI_SC su 6. Le righe qui sopra dicono quale."
		exit 6
	fi
else
	log "4. Il giro di oggi"
	ANCORA=$(visita "$PROFILO" oggi "")
	case "$ANCORA" in
	SI)	ok "l'eccezione REGGE: la pagina si apre senza avviso" ;;
	NO)	inf "la pagina NON si apre: o l'eccezione e' scaduta, o e' successo altro" ;;
	*)	ko "⛔ non so se la pagina si sia aperta: il registro non si e' letto" ;;
	esac

	log "5. ⛔ Il controllo che dice *no*: un profilo NUOVO deve vedere l'avviso"
	NUOVO=$(visita "$T/profilo-nuovo" nuovo "")
	if [ "$NUOVO" = NO ]; then
		ok "un profilo appena nato NON arriva alla pagina: lo strumento distingue"
		# ⚠ E questo controllo vale SOLO se il canale di lettura funziona: e'
		#   il punto esatto del rilievo A27 — legge lo stesso canale del
		#   verdetto, e a canale rotto si dichiarerebbe passato da se'.
		if [ "$CANALE" = SI ]; then
			APPROVATI=$((APPROVATI + 1))
		else
			ko "   ⛔ ...ma il canale di lettura non e' certificato: questo «NO»"
			ko "   e' lo stesso «NO» che darebbe uno strumento muto, e NON conta"
			ko "   come controllo passato."
		fi
	elif [ "$NUOVO" = SI ]; then
		ko "⛔ anche un profilo APPENA NATO arriva alla pagina."
		ko "   Allora «la pagina si apre» non dimostra che l'eccezione regga:"
		ko "   il certificato e' diventato fidato, o il banco non vede l'avviso."
		ko "   ⛔ Il verdetto di oggi non vale."
	else
		ko "⛔ del profilo nuovo non so niente: il registro non si e' letto."
	fi

	GIORNI=IGNOTI
	if [ -n "${ORA0:-}" ]; then
		GIORNI=$(python3 -c 'import sys
from datetime import datetime, timezone
a = datetime.fromisoformat(sys.argv[1])
print(f"{(datetime.now(timezone.utc) - a).total_seconds()/86400:.2f}")' "$ORA0")
		inf "giorni trascorsi dal giorno 0: $GIORNI"
	fi
	log "6. La scadenza che Chrome si e' segnato"
	# ⛔ RILIEVO A26, 11 agosto 2026: fino a stanotte questa riga STAMPAVA la
	#    scadenza e la riga di registro **non la portava**, mentre il rapporto
	#    `web/rapporti/S-esiti-sonda.md` la pubblicava come fatto misurato con la
	#    stella.  L'unico giro «avvia» su disco dice «valore non interpretabile»,
	#    e nessun giro successivo lo riscriveva: il numero piu' citato di S1b non
	#    aveva, su disco, nessuna riga che lo sostenesse.
	#    ⭐ Adesso ogni giro «oggi» la registra, quindi dal prossimo giro il
	#    numero ha una provenienza — ed e' l'unico modo di rimetterla senza
	#    rifare il giro «avvia», che azzererebbe l'orologio dei sette giorni.
	scadenza_memorizzata | tee "$T/scadenza-oggi.txt" | sed 's/^/        /'
	SCAD=$(sed -n 's/^scadenza : //p' "$T/scadenza-oggi.txt" | head -1)
	# ⛔ E anche LA CHIAVE: il rapporto pubblicava «l'indicizzazione e' per HOST,
	#    senza porta» citando `https://192.168.0.2:443,*`, e quella chiave era
	#    **trascritta a mano dall'uscita a schermo** — in nessun file.  Un
	#    revisore non la poteva ritrovare da nessuna parte.
	CHIAVE=$(sed -n 's/^chiave   : //p' "$T/scadenza-oggi.txt" | head -1)
	registra "{\"giro\":\"oggi\",\"eccezione_regge\":\"$ANCORA\",\"profilo_nuovo_arriva\":\"$NUOVO\",\"canale_certificato\":\"$CANALE\",\"giorni\":\"$GIORNI\",\"impronta\":\"$IMPRONTA\",\"chrome\":\"$VERSIONE\",\"scadenza_memorizzata\":\"${SCAD:-IGNOTA}\",\"chiave_ssl\":\"${CHIAVE:-IGNOTA}\"}"

	log "Esito di oggi"
	# ⛔ E IL VERDETTO HA UN DENOMINATORE — `LEZIONI.md` §1.9 regola 6: quante
	#    cose ha approvato, e se sono zero non si da' nessun esito.
	inf "controlli approvati da questo giro: $APPROVATI su 4 (certificato sul"
	inf "filo · canale di lettura · impronta del giorno 0 · profilo nuovo)"
	if [ "$APPROVATI" -eq 0 ]; then
		ko "⛔ ZERO controlli approvati: nessun esito.  «Tutti quelli provati"
		ko "   sono andati bene» e' vero anche quando i provati sono zero."
		exit 6
	fi
	if [ "$CANALE" != SI ]; then
		ko "⛔ NIENTE VERDETTO: il canale di lettura non e' certificato."
		ko "   Un «NO» da uno strumento muto ha la stessa faccia di «l'eccezione"
		ko "   e' scaduta», e da quella faccia uscirebbe IL NUMERO DI S1b — in"
		ko "   verde, e con sette giorni di ritardo prima che qualcuno se ne"
		ko "   accorga.  Cura: guarda il registro $SRC/01-s1b-visite.jsonl sul"
		ko "   server e l'accesso ssh, poi rilancia.  L'orologio NON e' perso."
		exit 6
	fi
	if [ "$NUOVO" != NO ]; then
		ko "il controllo che dice *no* non e' passato ($NUOVO): niente verdetto"
		exit 6
	fi
	case "$ANCORA" in
	SI)	ok "a $GIORNI giorni l'eccezione c'e' ancora — e l'atteso e' che cada a 7" ;;
	NO)	ok "a $GIORNI giorni l'eccezione NON c'e' piu': e' questo il numero di S1b"
		inf "⭐ e vale perche' tutte e tre le condizioni sono verificate: il"
		inf "canale di lettura e' certificato, il profilo nuovo e' fuori, e"
		inf "l'impronta e' quella del giorno 0" ;;
	*)	ko "⛔ l'esito della visita e' «$ANCORA»: niente verdetto"; exit 6 ;;
	esac
fi

inf "il registro dei giri sta in $STATO"
