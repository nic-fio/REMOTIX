#!/bin/bash
#
# 01-p5-lancia.sh — ⭐ IL GIRO CON UN BROWSER VERO CONTRO IL PRODOTTO,
#                      SU DUE MOTORI, CON DUE COLONNE E NON UNA.
#
#   bash banchi/01-p5-lancia.sh              i due motori, nell'ordine
#   bash banchi/01-p5-lancia.sh chrome       uno solo — E LO DICHIARA
#
# ⚠ GIRA DA QUESTA PARTE DEL FILO: i browser stanno su `CHUWI`, il prodotto sta
#   su `NIC-OS` (192.168.0.2, porta **7448** — ⛔ non 7447, che e' l'innesto di
#   B2).  Ed e' anche la posizione giusta: il prodotto ha il browser su una
#   macchina e il server su un'altra, e una misura fatta tutta dentro il server
#   non proverebbe la parte di rete.
#
# ===========================================================================
# ⛔ PERCHE' ESISTE — E NON E' PIGNOLERIA
#
# L'unica traccia di un giro con un browser vero contro il prodotto e' un
# **commento dentro `src/pagina.html`**: Firefox, notte del 10 agosto 2026.  Di
# **Chrome contro questo server non c'e' nessuna traccia**, e il criterio di B2
# vuole *«due motori su due»*.
#
# ⛔ E i difetti piu' cari di questa fase vivevano **nella differenza fra i due
#    motori** — con un motore solo quella differenza non si vede:
#
#   - il **posto** (§8.2 `0x0F`) non si liberava quando a chiudere il canale era
#     il SERVER: visto **solo su Chrome**, perche' su Firefox il trasporto
#     chiudeva lo stream in tempo e il posto se ne andava lo stesso;
#   - ⛔ ~~**il congedo arriva per due strade diverse, una per motore**: Chrome lo
#     manda come byte sul canale di controllo; Firefox azzera il canale e il
#     motivo arriva dentro il codice di chiusura della sessione~~ — ⛔ **FALSA, e
#     smentita per misura l'11 agosto 2026** (`banchi/01-p5-ff-*`, due giri per
#     motore).  Non erano due strade per due motori: era **lo stesso difetto di
#     prodotto** visto attraverso due smontaggi diversi.  Quel che su Chrome
#     sembrava «il motivo nel codice di chiusura» era la chiusura col codice
#     **`0x0`, che §3.1 VIETA** — e questo banco la contava come un congedo
#     perche' non leggeva il motivo (vedi `01-p5-registro.py`, cura della stessa
#     notte).  ⭐ Curato il prodotto, **tutt'e due i motori consegnano tutt'e due
#     le strade** col motivo `0x01`.
#     ⚠ La regola del verdetto per motore **resta**, e il punto sopra la regge da
#       solo: cambia la ragione, non la regola.
#
# ⭐ Da cui la regola di questo banco: **un verdetto per motore, mai uno solo.**
#    Un verdetto unico su due motori nasconde esattamente la cosa che si cerca.
#
# ===========================================================================
# ⛔ DA DOVE VIENE IL VERDETTO, E PERCHE' NON DALLA PAGINA
#
# La pagina in prova e' `src/pagina.html`: e' **del prodotto**, non e' nostra, e
# non si tocca.  Non spedisce nessun esito a nessuno — mostra `#esito` e
# `#registro` a schermo, e basta.
#
# ⭐ Quindi il verdetto viene dal **registro del server**, cioe' dal lato che
#    deve ricevere (`CODER.md` §3.8: *«il registro di chi manda dice che ha
#    chiamato una funzione, non che il byte e' arrivato»* — e qui a mandare
#    `CREDENZIALI` e' il browser, a riceverle il server).
#
# ⛔ E L'ATTRIBUZIONE AL MOTORE NON SI FA A TEMPO.  Gli orologi delle due
#    macchine sono a **due ore di distanza** (`[M]` 11 agosto 2026: qui CEST,
#    la' UTC), e segmentare un registro altrui col proprio orologio e' la
#    settima veste di `LEZIONI.md` §1.9 — il rosso puntato sull'imputato
#    sbagliato.
#
# ⭐ La cura sono **due marcatori che scrive il BROWSER stesso**: prima e dopo
#    ogni gamba, il motore in prova naviga su
#
#        https://192.168.0.2:7448/p5-<motore>-<gamba>-<giro>-inizio|fine
#
#    che `pagina.c` non riconosce e serve con un 404 — ⛔ **ma prima logga la
#    riga** `GET /p5-… da <indirizzo>`.  Tutto quel che sta fra le due righe e'
#    di quel motore, scritto **con l'orologio del server**, e nessuna aritmetica
#    fra fusi entra nel verdetto.
#
# ⚠ E i marcatori li batte il BROWSER, non `curl`: un marcatore di `curl`
#   proverebbe che questa macchina raggiunge il server, non che il motore in
#   prova ci sia arrivato — e sono due fatti diversi, uno dei quali e' proprio
#   quello in prova.
#
# ===========================================================================
# ⛔ IL BAN, E QUANTI TENTATIVI QUESTO BANCO SPENDE — SI DICHIARA
#
# `RCP.md` §4.4-bis: **tre autenticazioni fallite dallo stesso indirizzo dentro
# cinque minuti, e quell'indirizzo e' fuori per DODICI ORE**, con il ban su
# file.  ⚠ E questa macchina e' l'indirizzo da cui lavorano anche gli altri
# (`fasi/01-filo-nudo.md`, regola B0.3).
#
#   ⭐ QUESTO BANCO SPENDE **UN SOLO TENTATIVO FALLITO PER MOTORE**, e mai due
#      in volo insieme.  L'ordine delle gambe non e' di comodo, e' la cura:
#
#        N1  impronta storpiata   → ⛔ ZERO tentativi: la sessione non si apre,
#                                    `CREDENZIALI` non parte nemmeno
#        N2  parola sbagliata     → 1 tentativo fallito.  Il conto va a 1 di 3
#        P   il giro buono        → ⭐ un accesso RIUSCITO, e §4.4-bis dice che
#                                    azzera il conto: `rcp.c` lo scrive, e
#                                    questo banco **pretende di leggerlo**
#                                    («il conto dei falliti torna a zero»)
#
#   ⛔ E se dopo N2 la digitazione risulta finita nel posto sbagliato, il banco
#      **si ferma**: non riprova alla cieca.  Un secondo tentativo speso per un
#      difetto del pilota e' meta' del budget di tutti gli altri banchi.
#
#   ⛔ E LO SBLOCCO SI DICHIARA NEL REGISTRO, o «il ban non e' scattato» e
#      «qualcuno l'ha tolto» hanno lo stesso aspetto.  Lo strumento e'
#      `banchi/01-b8-sblocca.py` — non e' un pezzo di B8, e' lo strumento di
#      B0.3 — e il suo `PING` e' il denominatore: senza, «il ban non e'
#      scattato» e «lo sblocco non e' mai arrivato a nessuno» si somigliano.
#
# ===========================================================================
# ⛔ CHE COSA QUESTO BANCO **NON** MISURA, E VA LETTO PRIMA DEL VERDETTO
#
#   1. **L'avviso sul caricamento della PAGINA c'e', ed e' atteso.**  §4.1-bis:
#      `serverCertificateHashes` *«non copre il caricamento della pagina, che e'
#      una connessione TCP a se'.  Li' resta l'avviso con il clic»*.  ⛔ Quindi
#      «nessun avviso» vale per la **SESSIONE WebTransport**, non per la pagina:
#      qui l'avviso della pagina si supera **dalla stessa porta dell'utente** —
#      `thisisunsafe` su Chrome (la scorciatoia che chiama lo stesso `proceed`
#      del bottone «Procedi»), il bottone «Accetto il rischio» su Firefox — e il
#      fatto che si sia superato **si verifica dal registro del server**, non si
#      presume.  ⛔ `--ignore-certificate-errors` non compare in nessuna riga di
#      questo file, per la stessa ragione per cui non compare in
#      `01-s1b-eccezione.sh`: sarebbe il modo piu' rapido di far aprire la
#      pagina e il modo piu' sicuro di non misurare piu' niente.
#
#   2. **Che la pagina abbia RICEVUTO `SESSIONE`** non si legge dal registro del
#      server, che dice solo di averlo spedito.  Le due prove indirette che
#      questo banco raccoglie sono: (a) la pagina non manda nessun `CONGEDO` di
#      protesta, e (b) alla chiusura del browser il server registra il congedo
#      del client e **il posto lasciato**, che uno stato precedente a `SESSIONE`
#      non produrrebbe.  ⚠ E' una prova indiretta, e §1.11 vale: prova quel che
#      prova.  ⭐ La terza e' la **fotografia** dello schermo, che e' quel che
#      l'utente vede (invariante I8) — ma la fotografia non la confronta il
#      banco: e' materiale per chi legge, e come tale e' dichiarata.
#
#   3. **Le proprieta' di trasporto delle sei di B2** — datagram, credito uni,
#      migrazione, niente 0-RTT, `allowPooling` — non le guarda: le guarda
#      `01-b2-sonda-trasporto.py`, che e' di un altro (agente 4).
# ===========================================================================
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
RADICE=$(dirname "$QUI")
REG=$QUI/01-p5-registro.py

IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7448}
PORTA_LOC=${PORTA_LOC:-8855}
SCHERMO=${SCHERMO:-:79}
MISURA=${MISURA:-1280x1024}
UTENTE=${UTENTE:-prova}
PAROLA=${PAROLA:-parola-di-prova}
# ⚠ La parola sbagliata e' sbagliata **di proposito e in modo riconoscibile**:
#   se finisse per caso in un registro, chi legge deve capire subito che non e'
#   la parola di nessuno.
PAROLA_STORTA=${PAROLA_STORTA:-questa-e-sbagliata-apposta-P5}
LOG_SERVER=${LOG_SERVER:-/media/REMOTIX/src/remotix-browser.log}
SOCK=${SOCK:-/srv/src/b8-comando.sock}
COPIE=$QUI/01-p5-copie
SSH="ssh -o BatchMode=yes -o ConnectTimeout=10 nicfio@$IND"

# ⛔ OGNI RIGA DEL REGISTRO DICE CONTRO CHE COSA HA MISURATO — la convenzione di
#    `01-b0-bersaglio.py`.  ⚠ Qui e' il **prodotto** sulla 7448, non l'innesto
#    sulla 7447: hanno la stessa forma di registro e numeri che si somigliano,
#    e senza questo campo chi li mettesse insieme «per avere piu' campioni»
#    calcolerebbe la mediana di due popolazioni diverse.
export BERSAGLIO=prodotto
export PORTA_BERSAGLIO=$PORTA

GIRO="p5-$(date +%Y%m%d-%H%M%S)-$RANDOM"
T=$(mktemp -d)

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

MOTORI=${1:-tutti}
ESITO=0
PID_X=
PID_RACC=
PID_BR=
INDIRIZZO_VISTO=""
SBLOCCHI=""

congedo()
{
	[ -n "$PID_BR" ]   && { kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; }
	[ -n "$PID_RACC" ] && { kill "$PID_RACC" 2>/dev/null; wait "$PID_RACC" 2>/dev/null; }
	[ -n "$PID_X" ]    && { kill "$PID_X" 2>/dev/null; wait "$PID_X" 2>/dev/null; }
	sleep 1
	rm -rf "$T"
}
trap congedo EXIT

X() { env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO "$@"; }

registra() { python3 "$REG" aggiungi "$1" >/dev/null; }

# ---------------------------------------------------------------------------
# Il registro del server, scaricato qui.  ⛔ E lo stato di questa lettura SI
# PROVA: un registro mancante, un ssh caduto e un server mai partito arrivano
# tutti come «zero righe», che ha la stessa faccia di «nessuna violazione».
scarica_registro()
{
	local dove=$1 stato
	$SSH "cat '$LOG_SERVER'; printf 'P5-FINE=%s\n' \$?" >"$dove" 2>"$T/ssh.err"
	stato=$(sed -n 's/^P5-FINE=\([0-9][0-9]*\)$/\1/p' "$dove" | tail -1)
	if [ -z "$stato" ]; then
		ko "⛔ il comando remoto non e' arrivato in fondo: nessun «P5-FINE»."
		ko "   Non e' «il registro e' vuoto»: e' «non ho potuto guardare»."
		sed -n '1,4p' "$T/ssh.err" | sed 's/^/        /'
		return 3
	fi
	if [ "$stato" -ne 0 ]; then
		ko "⛔ «$LOG_SERVER» non si e' letto (cat esce $stato)."
		sed -n '1,4p' "$dove" | sed 's/^/        /'
		return 3
	fi
	return 0
}

# ---------------------------------------------------------------------------
log "0. La scena, e si dichiara PRIMA di misurare (B0.1)"
inf "giro          : $GIRO"
inf "prodotto      : https://$IND:$PORTA   ⛔ il PRODOTTO, non l'innesto sulla 7447"
inf "utente        : $UTENTE"
inf "registro srv  : $LOG_SERVER"
inf "socket sblocco: $SOCK"
inf "⚠ ORE: questa stazione e' su $(date +%Z), il server e' su UTC — due ore di"
inf "  scarto.  Nessun passo di questo banco si decide confrontando i due orologi."

# ---------------------------------------------------------------------------
log "1. I browser di QUESTA macchina, con le versioni LETTE"
# ⛔ Le versioni si leggono dal binario che sta per girare.  Un numero copiato
#    da un documento invece che letto e' la forma d'errore E5, e i documenti di
#    questo progetto ne portano due (Chrome 151, Firefox 140) che vengono da
#    misure di due giorni fa.
VER_CHROME=""
VER_FIREFOX=""
command -v google-chrome >/dev/null && VER_CHROME=$(google-chrome --version 2>&1 | head -1)
command -v firefox       >/dev/null && VER_FIREFOX=$(firefox --version 2>&1 | head -1)
inf "google-chrome : ${VER_CHROME:-ASSENTE}"
inf "firefox       : ${VER_FIREFOX:-ASSENTE}"
inf "⚠ e la versione del BINARIO non e' quella che il motore DICHIARA: Chrome"
inf "  riduce l'userAgent a «151.0.0.0», Firefox ESR dichiara «140.0».  Quella"
inf "  dichiarata la scrive la sonda di N1, e nel registro ci sono tutt'e due."
for t in xdotool Xvfb xdpyinfo curl openssl import; do
	command -v "$t" >/dev/null || { ko "⛔ manca «$t»: il banco non si pilota"; exit 2; }
done
ok "gli attrezzi ci sono tutti"

# ---------------------------------------------------------------------------
log "2. Lo schermo finto, e si VERIFICA di che misura sia"
if [ -e "/tmp/.X11-unix/X${SCHERMO#:}" ]; then
	DIM=$(X xdpyinfo 2>"$T/xdpy.err" | sed -n 's/^  dimensions: *\([0-9x]*\).*/\1/p' | head -1)
	if [ "$DIM" != "$MISURA" ]; then
		ko "⛔ $SCHERMO e' acceso a ${DIM:-IGNOTA} e questo banco dichiara $MISURA."
		ko "   ⚠ 01-s1b-eccezione.sh usa :77 e 01-s5-tela.sh usa :78: probabilmente"
		ko "   e' rimasto appeso un giro di un altro banco.  Chiudilo per PID (mai"
		ko "   con pkill -f), o rilancia con SCHERMO=:80."
		exit 2
	fi
	inf "lo schermo $SCHERMO era gia' acceso, ed e' della misura dichiarata ($DIM)"
else
	Xvfb "$SCHERMO" -screen 0 "${MISURA}x24" >"$T/xvfb.log" 2>&1 &
	PID_X=$!
	sleep 2
	[ -d "/proc/$PID_X" ] || { ko "Xvfb non e' partito:"; sed 's/^/        /' "$T/xvfb.log"; exit 2; }
	DIM=$(X xdpyinfo 2>/dev/null | sed -n 's/^  dimensions: *\([0-9x]*\).*/\1/p' | head -1)
	[ "$DIM" = "$MISURA" ] || { ko "⛔ chiesto $MISURA, letto ${DIM:-niente}"; exit 2; }
	ok "schermo finto $SCHERMO — chiesto $MISURA, letto $DIM"
fi

# ---------------------------------------------------------------------------
log "3. Il prodotto risponde? E l'impronta pubblicata e' UNA sola?"
# ⛔ `curl -k` qui NON e' una scorciatoia sulla misura: non tocca nessun profilo
#    e non concede nessuna eccezione a nessun browser.  E' lo strumento che si
#    certifica, non il fatto che si misura — la stessa distinzione scritta in
#    `01-s1b-eccezione.sh`.
if ! curl -sk --max-time 15 "https://$IND:$PORTA/impronta" -o "$T/impronta.json" 2>"$T/curl.err"; then
	ko "⛔ il prodotto non risponde su https://$IND:$PORTA/impronta:"
	sed 's/^/        /' "$T/curl.err"
	ko "   ⛔ Questo NON e' «il giro e' fallito»: e' «non c'e' nessuno dall'altra"
	ko "   parte».  Accendilo cosi' (dentro il contenitore, da root):"
	ko "     bash /media/REMOTIX/enter.sh --root \\"
	ko "       \"/srv/src/remotix/remotix --indirizzo 0.0.0.0 --nome $IND --porta $PORTA \\"
	ko "        --certificati /srv/src/remotix-cert --pagina /srv/src/remotix/pagina.html \\"
	ko "        --ban /srv/src/remotix-ban --comando-socket $SOCK\""
	ko "   ⛔ E il «--comando-socket» NON e' facoltativo per questo banco: senza,"
	ko "   il comando di sblocco di §4.4-bis non esiste, e il controllo che dice"
	ko "   NO non si puo' disfare per dodici ore."
	exit 3
fi
sed 's/^/        /' "$T/impronta.json"
IMPRONTA=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("impronta",""))' "$T/impronta.json" 2>/dev/null)
if [ ${#IMPRONTA} -ne 44 ]; then
	ko "⛔ l'impronta dell'endpoint ha ${#IMPRONTA} caratteri invece di 44"
	ko "   (un SHA-256 in base64 e' 43 cifre piu' il riempimento: 42 vorrebbe dire"
	ko "   che qualcuno ha tagliato la prima)"
	exit 4
fi
ok "impronta della SESSIONE, dall'endpoint /impronta: $IMPRONTA"

# ⛔ E la pagina deve portare LA STESSA.  Se le due divergono, la sessione non
#    si apre e **nessun errore nomina l'impronta**: il sintomo e' «WebTransport
#    non si connette», ed e' esattamente il difetto del rilievo R1.14 di RCP.md.
curl -sk --max-time 15 "https://$IND:$PORTA/" -o "$T/pagina.html" 2>/dev/null
IMPRONTA_PAGINA=$(sed -n 's/.*IMPRONTA_SERVITA = "\([^"]*\)".*/\1/p' "$T/pagina.html" | head -1)
if [ "$IMPRONTA_PAGINA" != "$IMPRONTA" ]; then
	ko "⛔ la pagina pubblica «$IMPRONTA_PAGINA» e l'endpoint dice «$IMPRONTA»:"
	ko "   sono due impronte diverse per lo stesso certificato di sessione."
	ESITO=1
else
	ok "⭐ la pagina pubblica la stessa impronta dell'endpoint (§4.1-bis)"
fi
if grep -qF "__IMPRONTA__" "$T/pagina.html"; then
	ko "⛔ il segno «__IMPRONTA__» e' rimasto NON sostituito nella pagina servita"
	ESITO=1
fi

# ⛔ E I CERTIFICATI SONO DUE, NON UNO — §4.1-bis, e si verifica qui perche'
#    nessun'altra riga di questo banco lo guarderebbe.  Quello della PAGINA e'
#    longevo (l'eccezione dell'utente vive li'); quello della SESSIONE ruota da
#    se' sotto i 14 giorni.  ⚠ Confonderli fa ricomparire l'avviso ogni due
#    settimane, e nessuno collegherebbe le due cose.
printf 'Q\n' | timeout 15 openssl s_client -connect "$IND:$PORTA" >"$T/catena.txt" 2>/dev/null
if grep -qF "BEGIN CERTIFICATE" "$T/catena.txt"; then
	IMPRONTA_PAG_FILO=$(openssl x509 -in "$T/catena.txt" -outform der 2>/dev/null \
		| openssl dgst -sha256 -binary | base64 -w0)
	CURVA=$(openssl x509 -in "$T/catena.txt" -noout -text 2>/dev/null \
		| sed -n 's/.*ASN1 OID: \(.*\)/\1/p' | head -1)
	FINE=$(openssl x509 -in "$T/catena.txt" -noout -enddate 2>/dev/null | cut -d= -f2)
	inf "certificato della PAGINA, letto DAL FILO: $IMPRONTA_PAG_FILO"
	inf "  curva: ${CURVA:-IGNOTA}   scade: ${FINE:-IGNOTA}"
	if [ "$IMPRONTA_PAG_FILO" = "$IMPRONTA" ]; then
		ko "⛔ IL CERTIFICATO DELLA PAGINA E QUELLO DELLA SESSIONE SONO LO STESSO."
		ko "   §4.1-bis ne vuole DUE: uno longevo per la pagina — su cui vive"
		ko "   l'eccezione dell'utente — e uno breve per la sessione, che ruota."
		ko "   Con uno solo, l'avviso ricompare ogni quattordici giorni."
		ESITO=1
	else
		ok "⭐ i due certificati sono DAVVERO due (§4.1-bis)"
	fi
	case "$CURVA" in
	prime256v1|P-256) ok "e la chiave della pagina e' ECDSA P-256, come §4.1 impone" ;;
	*) ko "⛔ la curva della pagina e' «${CURVA:-IGNOTA}», e §4.1 impone P-256"; ESITO=1 ;;
	esac
else
	ko "⛔ nessun certificato sul filo TCP: non e' «l'avviso non c'e'», e'"
	ko "   «non c'e' nessuno».  Tre cause con la stessa faccia."
	ESITO=1
fi

# ---------------------------------------------------------------------------
log "4. ⭐ IL CONTROLLO POSITIVO DEL CANALE DI LETTURA (la cura di A27)"
# Si scrive una riga nel registro del server passando dalla STESSA porta della
# pagina, e la si rilegge con lo STESSO `ssh` che leggera' il verdetto.  Se il
# marcatore torna, i tre pezzi su cui il verdetto poggia — il server che scrive,
# `ssh` che legge, il `grep` che trova — funzionano tutti e tre.
#
# ⛔ Senza, ogni «passo non trovato» vorrebbe dire «non ho potuto guardare», e
#    il banco darebbe rosso al prodotto per un `ssh` caduto.
MARCA_CANALE="p5-canale-$GIRO"
curl -sk --max-time 15 -o /dev/null "https://$IND:$PORTA/$MARCA_CANALE" 2>/dev/null
sleep 1
if ! scarica_registro "$T/reg0.txt"; then
	ko "   ⛔ senza il registro del server questo banco non ha nessun verdetto"
	exit 3
fi
QUANTE=$(grep -c "$MARCA_CANALE" "$T/reg0.txt")
if [ "$QUANTE" -lt 1 ]; then
	ko "⛔ IL CANALE DI LETTURA E' ROTTO: ho appena chiesto «/$MARCA_CANALE» al"
	ko "   prodotto e rileggendo il registro non lo trovo (righe guardate:"
	ko "   $(wc -l < "$T/reg0.txt"))."
	ko "   ⛔ Allora ogni «passo non trovato» di questo giro vorrebbe dire «non ho"
	ko "   potuto guardare».  Nessun verdetto si da'."
	exit 3
fi
ok "⭐ una richiesta certamente avvenuta si rilegge nel registro ($QUANTE volta/e)"
# ⭐ E DA QUI SI LEGGE CON CHE INDIRIZZO IL SERVER CI VEDE — non si presume.
#    §4.4-bis: la chiave del conto porta le parentesi quadre anche in IPv4
#    (`[192.168.0.3]`), «perche' e' cosi' che lo scrive chi ospita».  Chi digita
#    l'indirizzo nudo al comando di sblocco deve arrivare alla stessa chiave, e
#    a normalizzare e' il server: qui si legge quel che il server ha scritto.
INDIRIZZO_VISTO=$(grep "$MARCA_CANALE" "$T/reg0.txt" | tail -1 \
	| sed -n 's/.* da \[\{0,1\}\([0-9.]*\)\]\{0,1\}:[0-9]*.*/\1/p')
inf "il server ci vede come: «${INDIRIZZO_VISTO:-NON LETTO}»"
if [ -z "$INDIRIZZO_VISTO" ]; then
	ko "⛔ non ho potuto leggere con che indirizzo il server ci vede: allora non"
	ko "   so quale sbloccare, e lo sblocco «riuscito» su un indirizzo qualunque"
	ko "   risponderebbe NON-BANNATO per sempre e senza sintomo (§4.4-bis)."
	ESITO=1
fi

# ---------------------------------------------------------------------------
log "5. ⛔ IL COMANDO DI SBLOCCO — il PING e' il denominatore (B0.3)"
sblocca() # $1 = etichetta del momento
{
	local quando=$1 uscita testo
	testo=$($SSH "bash /media/REMOTIX/enter.sh --root \"python3 /srv/src/01-b8-sblocca.py --socket $SOCK ${INDIRIZZO_VISTO:-$IND}\"" 2>&1)
	uscita=$?
	printf '%s\n' "$testo" | sed 's/^/        /'
	# ⛔ Tre esiti, non due: TOLTO · NON-BANNATO · «non ho potuto parlare».
	local esito=IGNOTO
	case "$testo" in
	*SBLOCCATO*|*TOLTO*)  esito=TOLTO ;;
	*NON-BANNATO*)        esito=NON-BANNATO ;;
	esac
	SBLOCCHI="$SBLOCCHI $quando=$esito"
	registra "{\"banco\":\"P5\",\"giro\":\"$GIRO\",\"tipo\":\"SBLOCCO\",\"quando\":\"$quando\",\"indirizzo\":\"${INDIRIZZO_VISTO:-$IND}\",\"esito\":\"$esito\",\"uscita\":$uscita}"
	inf "sblocco «$quando»: $esito"
}

PING=$($SSH "bash /media/REMOTIX/enter.sh --root \"python3 /srv/src/01-b8-sblocca.py --socket $SOCK --ping\"" 2>&1)
printf '%s\n' "$PING" | sed 's/^/        /'
COMANDO_VIVO=no
case "$PING" in *PONG*|*c'e'*) COMANDO_VIVO=si ;; esac
registra "{\"banco\":\"P5\",\"giro\":\"$GIRO\",\"tipo\":\"PING-SBLOCCO\",\"vivo\":\"$COMANDO_VIVO\",\"socket\":\"$SOCK\"}"
if [ "$COMANDO_VIVO" = si ]; then
	ok "⭐ il comando di sblocco risponde: la gamba N2 si puo' disfare"
	sblocca prima
else
	ko "⛔ IL COMANDO DI SBLOCCO NON RISPONDE su «$SOCK»."
	ko "   Il server e' stato acceso senza «--comando-socket», oppure il socket"
	ko "   e' altrove.  ⛔ Allora la gamba N2 (parola sbagliata) NON SI FA: un"
	ko "   tentativo fallito che non si puo' disfare e' un terzo del budget di"
	ko "   tutti i banchi di questa macchina, per dodici ore."
	inf "⚠ il giro prosegue SENZA il controllo negativo sull'autenticazione, e"
	inf "  questo si scrive nel verdetto: e' un giro con un controllo in meno."
fi

# ---------------------------------------------------------------------------
log "6. Il raccoglitore locale (serve la sonda di N1)"
python3 -u "$QUI/01-p5-raccogli.py" "$PORTA_LOC" >"$T/racc.log" 2>&1 &
PID_RACC=$!
sleep 1
[ -d "/proc/$PID_RACC" ] || { ko "il raccoglitore non e' partito:"; sed 's/^/        /' "$T/racc.log"; exit 3; }
ok "raccoglitore su 127.0.0.1:$PORTA_LOC"
mkdir -p "$COPIE"

righe() { python3 "$REG" righe 2>/dev/null; }

# ---------------------------------------------------------------------------
# Il fuoco alla finestra che porta la pagina — per NOME, non per classe.
# ⛔ `xdotool search --class firefox-esr` trova NOVE finestre con un solo
#    Firefox acceso (`[M]` 11 agosto 2026, `01-p5-tastiera.sh`), e
#    `windowactivate` prende la prima, che non e' quella del documento: si
#    batterebbe dentro una finestra che non ascolta.  Il titolo invece e' uno.
fuoco() # $1 = pezzo di titolo
{
	local viste
	viste=$(X xdotool search --name "$1" 2>/dev/null | wc -l)
	[ "$viste" -eq 0 ] && return 1
	X xdotool search --name "$1" windowactivate --sync >/dev/null 2>&1
	X xdotool search --name "$1" windowfocus --sync >/dev/null 2>&1
	return 0
}

# ⛔⭐ IL FUOCO PRIMA DI OGNI GAMBA, E NON DENTRO IL RAMO DI UNA SOLA — cura
#     dell'11 agosto 2026, sera, e il difetto l'ha trovato una FOTOGRAFIA.
#
# `[M]` `01-p5-copie/firefox-p-sessione-1-pagina.png`: Firefox fermo sulla
# pagina del marcatore d'**avvio**, con tre schede aperte — `naviga()` aveva
# battuto `ctrl+l`, l'URL e `Invio`, e la pagina non era cambiata.  ⛔ La
# ragione sta nella struttura: l'unica chiamata a `fuoco` stava **dentro il
# ramo di N2**, e con il comando di sblocco che non risponde quel ramo si
# salta — si arrivava alla gamba `P` **senza aver mai dato il fuoco a nessuna
# finestra**.  ⚠ Su Chrome non si vedeva, perche' la finestra appena aperta
# prende il fuoco da se': la stessa cura mancante, invisibile su un motore su
# due — che e' esattamente la ragione per cui questo banco vuole DUE colonne.
#
# ⛔ E il titolo non e' sempre «REMOTIX»: all'inizio della gamba la finestra sta
#    sul marcatore, che il server serve con un 404 e il cui titolo porta
#    l'indirizzo.  Si provano tutt'e due, in ordine, e si dichiara se nessuno
#    dei due si trova — invece di battere tasti nel vuoto.
# ⚠ E UN LIMITE MISURATO DI QUESTA FUNZIONE, scritto invece che taciuto.
#   `[M]` 11 agosto 2026, 13:29: all'inizio della gamba `p-sessione` su Firefox
#   questa funzione ha detto NO — la finestra stava sul marcatore d'avvio, e il
#   suo titolo non conteneva ne' «REMOTIX» ne' l'indirizzo.  ⛔ Il messaggio che
#   ne segue («i tasti andrebbero a nessuno») era **fuorviante**: i tasti sono
#   arrivati lo stesso, perche' quella finestra il fuoco ce l'aveva gia', e la
#   gamba e' andata avanti fino a `SESSIONE`.
#   ⭐ Il seguito giusto e' aggiungere il nome del motore fra i titoli provati —
#      ⛔ e NON e' stato fatto stasera: cambiare il pilota **dopo** aver misurato
#      e prima di rimisurare vorrebbe dire pubblicare un banco che nessuno ha
#      girato.  Si scrive qui, e lo fa il prossimo giro.
fuoco_prodotto()
{
	fuoco "REMOTIX" && return 0
	fuoco "$IND" && return 0
	return 1
}

# ⭐ Quante finestre portano quel titolo — ed e' il modo con cui questo banco
#    verifica che la SCHEDA in prova sia sparita.
# ⛔ Il titolo e' quello della scheda ATTIVA (`<title>REMOTIX</title>`,
#    `src/pagina.html:49`): con due schede aperte, chiusa quella in prova il
#    fuoco passa all'altra e il conto va da 1 a 0.  ⇒ «1 → 0» dice **la scheda
#    si e' chiusa**, e non dice niente sul programma, che e' quel che serve.
finestre() { X xdotool search --name "${1:-REMOTIX}" 2>/dev/null | wc -l; }

fotografia() # $1 = nome del file
{
	X import -window root "$COPIE/$1.png" >/dev/null 2>&1 \
		&& inf "fotografia: $COPIE/$1.png  (⚠ materiale per chi legge, NON un verdetto)"
}

# Naviga la finestra corrente su un indirizzo, dalla barra come farebbe l'utente.
naviga() # $1 = url
{
	X xdotool key --clearmodifiers ctrl+l >/dev/null 2>&1
	sleep 1
	X xdotool type --clearmodifiers --delay 25 "$1" >/dev/null 2>&1
	sleep 1
	X xdotool key --clearmodifiers Return >/dev/null 2>&1
}

# ---------------------------------------------------------------------------
# ⛔ L'AVVISO DEL CERTIFICATO DELLA PAGINA — si supera dalla porta dell'utente.
#
# Chrome  : «thisisunsafe» battuto sull'interstiziale chiama lo stesso `proceed`
#           del bottone «Procedi»: e' una scorciatoia di tastiera, non un
#           interruttore che salta il meccanismo (`[M]` 10 agosto 2026, S1b).
# Firefox : il bottone «Avanzate…» e poi «Accetta il rischio e continua».  ⚠ Non
#           esiste una scorciatoia equivalente: si batte `Tab`+`Return` sui due
#           bottoni, e se non basta si clicca a coordinate.  ⛔ Che sia riuscito
#           NON si crede sulla parola: lo dice il marcatore nel registro del
#           server, tre righe piu' giu'.
supera_avviso() # $1 = motore
{
	case "$1" in
	chrome)
		X xdotool mousemove 640 500 click 1 >/dev/null 2>&1
		sleep 1
		X xdotool type --clearmodifiers --delay 120 'thisisunsafe' >/dev/null 2>&1
		;;
	firefox)
		# ⭐ DUE CLIC A COORDINATE **MISURATE**, non contate a tentoni.
		#
		#    `[M]` 11 agosto 2026, su questa macchina, contro un sito HTTPS
		#    finto con certificato autofirmato P-256 su `192.168.0.3:8443` —
		#    cioe' **senza toccare il prodotto**.  Su Firefox 140.13.0esr, con
		#    schermo 1280x1024 e finestra `--width 1280 --height 1000`:
		#
		#      «Advanced…»                    (962, 656)
		#      «Accept the Risk and Continue»  (881, 965)
		#
		#    e il marcatore e' arrivato al sito.  ⚠ La prima stesura contava sei
		#    tabulazioni e poi otto: un numero inventato, che non era stato
		#    provato da nessuno.
		#
		# ⛔ E LE COORDINATE DIPENDONO DALLA GEOMETRIA DICHIARATA piu' in alto
		#    ($MISURA e la finestra a 1280x1000): cambiarla senza rifare questa
		#    misura fa cliccare nel vuoto.  Il fallimento pero' non e' muto — lo
		#    dice il marcatore che non arriva, tre passi piu' giu'.
		#
		# ⚠ E resta un `[?]`: la lingua.  Qui l'interfaccia e' in inglese; con un
		#   Firefox in italiano i bottoni cambiano larghezza, non posizione
		#   verticale, e il clic dovrebbe reggere lo stesso — ma non e' misurato.
		X xdotool mousemove 962 656 click 1 >/dev/null 2>&1
		sleep 3
		X xdotool mousemove 881 965 click 1 >/dev/null 2>&1
		;;
	esac
	sleep 6
}

# ---------------------------------------------------------------------------
# UNA GAMBA CONTRO LA PAGINA DEL PRODOTTO.
#   $1 = motore   $2 = etichetta della gamba   $3 = parola da digitare
#   $4 = scenario atteso per `01-p5-registro.py passi`
# ---------------------------------------------------------------------------
gamba_pagina()
{
	local motore=$1 gamba=$2 parola=$3 atteso=$4
	local marca_a="p5-$motore-$gamba-$GIRO-inizio"
	local marca_b="p5-$motore-$gamba-$GIRO-fine"
	# ⭐ Il marcatore della SECONDA scheda: e' la prova che il browser ne aveva
	#    davvero due quando si e' battuto `ctrl+w`, e la da' il registro del
	#    server invece della parola del pilota.
	local marca_c="p5-$motore-$gamba-$GIRO-secondascheda"
	local gesto_fatto=ignoto
	log "   gamba «$gamba» su $motore — atteso: $atteso"

	# ⛔ Il fuoco PRIMA di battere qualunque tasto, e se non si trova la finestra
	#    lo si dice: un `ctrl+l` battuto nel vuoto lascia la pagina dov'era, e il
	#    banco misurerebbe il silenzio di un gesto mai fatto.
	if ! fuoco_prodotto; then
		ko "⛔ non trovo nessuna finestra del browser in prova (ne' «REMOTIX» ne'"
		ko "   «$IND»): da qui in poi i tasti andrebbero a nessuno, e quel che"
		ko "   non arriva al server non sarebbe un fatto sul prodotto."
	fi
	naviga "https://$IND:$PORTA/$marca_a"
	sleep 4
	naviga "https://$IND:$PORTA/"
	sleep 6
	fotografia "$motore-$gamba-1-pagina"

	# ── La digitazione ────────────────────────────────────────────────────
	# ⛔ Si clicca nel corpo della pagina e si tabula fino al primo campo: gli
	#    unici elementi raggiungibili sono `#utente`, `#parola` e `#vai`.  ⚠ Che
	#    la digitazione sia finita dove doveva NON si presume: lo dice il
	#    registro del server, che scrive `CREDENZIALI ricevute utente=<nome>` —
	#    cioe' il banco verifica SE STESSO dal lato che riceve.
	X xdotool mousemove 640 820 click 1 >/dev/null 2>&1
	sleep 1
	X xdotool key --clearmodifiers Tab >/dev/null 2>&1
	sleep 1
	X xdotool type --clearmodifiers --delay 40 "$UTENTE" >/dev/null 2>&1
	X xdotool key --clearmodifiers Tab >/dev/null 2>&1
	sleep 1
	X xdotool type --clearmodifiers --delay 40 "$parola" >/dev/null 2>&1
	sleep 1
	X xdotool key --clearmodifiers Return >/dev/null 2>&1

	# ⚠ Il tetto e' generoso apposta: §4.4-bis impone al server **un secondo
	#   fisso** prima di ogni risposta a `CREDENZIALI`, e B8 ha misurato una
	#   mediana di 2636 ms perche' a governare i tempi e' PAM.
	sleep 12
	fotografia "$motore-$gamba-2-esito"

	# ── La chiusura, e ⛔ e' un passo della misura, non una pulizia ─────────
	#
	#    Il posto si libera QUI, e «occupati adesso: 0» e' la riga che dice se
	#    §8.2 `0x0F` e' rispettata.
	#
	# ⛔ E SI ASPETTA PIU' DEL TETTO D'INATTIVITA', NON CINQUE SECONDI.  `[M]`
	#    11 agosto 2026, dal registro vero del 10 agosto
	#    (`/media/REMOTIX/src/remotix-browser.log`): un browser chiuso di colpo
	#    **non manda nessun congedo**, e il posto se n'e' andato con
	#    `STACCATO per silenzio: 30269 ms … (posti occupati adesso: 0)` — cioe'
	#    trenta secondi dopo, il `max_idle_timeout` di §2.2.  ⚠ Un banco che
	#    guardasse il registro dopo cinque secondi scriverebbe «IL POSTO NON SI
	#    E' LIBERATO» su un server che stava per liberarlo, e sarebbe un rosso
	#    sul difetto piu' caro della fase — dato all'imputato sbagliato.
	# ⛔⭐ SI CHIUDE LA SCHEDA COME LA CHIUDEREBBE L'UTENTE, e non si ammazza
	#     il browser — misurato l'11 agosto 2026, su tutt'e due i motori.
	#
	#     Qui c'era solo `kill "$PID_BR"`.  ⛔ Un browser che riceve un segnale
	#     NON esegue piu' JavaScript: `pagehide` non arriva, la pagina non puo'
	#     congedarsi, e il banco misurava «il client non si e' congedato» su un
	#     client a cui non era stato dato modo di farlo.  E' la settima veste —
	#     un banco che accusa il codice sbagliato — nella forma piu' difficile
	#     da vedere, perche' il rosso e' **vero**: il congedo davvero non c'era.
	#
	# ⭐ `ctrl+w` e' il gesto dell'utente, ed e' esattamente la scena che §8.2
	#    `CHIUSO_DALL_UTENTE` descrive.  ⚠ E S3 di questo stesso banco ha
	#    misurato che su tutt'e due i motori quel tasto e' RISERVATO al browser:
	#    qui e' la proprieta' che serve, non un ostacolo.
	#
	# ⚠ Il segnale resta come fondo: se la scheda non si chiude entro 5 s, si
	#   ammazza il processo e LO SI DICHIARA — un banco che aspetta per sempre
	#   non e' piu' un banco.
	if [ -n "$PID_BR" ]; then
		# ⛔⭐ `X xdotool`, NON `xdotool` — e questa riga sola vale mezza serata.
		#
		#     `[M]` 11 agosto 2026, `01-p5-congedo.sh`: qui c'era `xdotool key
		#     --clearmodifiers ctrl+w` **senza `X`**, cioe' senza
		#     `DISPLAY=$SCHERMO`.  Il tasto andava sul display dell'ambiente —
		#     che in una sessione di banco non e' lo schermo finto — e la scheda
		#     non si chiudeva col gesto: niente `pagehide`, niente congedo.
		#     ⛔ E il banco scriveva **«nessun congedo, per nessuna delle due
		#     strade di §3.1»**, che e' un'accusa al PRODOTTO per un tasto che
		#     non era mai arrivato.  La settima veste di `LEZIONI.md` §1.9, e la
		#     seconda volta in questa fase (dopo B3, dove il colpevole era il
		#     buffer di Python).
		#     ⭐ Con `X` davanti, misurato sulla stessa scena: il gesto arriva
		#        (finestre 1 → 0) e **il congedo esce** — motivo nel codice di
		#        chiusura, posto LASCIATO, zero `STACCATO per silenzio`.
		# ⛔⭐ E LA SCENA VUOLE DUE SCHEDE — cura della tarda serata dell'11
		#     agosto 2026, e a insegnarla e' stato `banchi/01-p5-ff-*`.
		#
		#     `[M]` Con UNA sola scheda `ctrl+w` non chiude la scheda: **fa
		#     uscire Firefox**.  Quel che si misurava non era «l'utente chiude
		#     la scheda» ma «il programma termina» — ⛔ e in quella scena non
		#     esce niente per NESSUNA via, nemmeno per le varianti che
		#     scavalcano il difetto, provate una a una.  ⇒ Un'assenza di congedo
		#     raccolta li' e' un'accusa al prodotto per una scena che non e'
		#     quella di §8.2 `CHIUSO_DALL_UTENTE`.
		#
		# ⭐ Qui si apre una SECONDA scheda su un marcatore verificabile, si
		#    torna sulla prima con `ctrl+shift+Tab` e si batte `ctrl+w`: la
		#    scheda muore, il browser resta VIVO, ed e' la scena che l'utente fa
		#    davvero.
		#
		# ⛔ E CHE IL BROWSER RESTI VIVO NON E' PIU' UN SINTOMO: E' L'ATTESO.
		#    Qui c'erano cinque secondi d'attesa che il processo morisse e, se
		#    non moriva, la riga «da qui in poi l'assenza di congedo non e' un
		#    verdetto».  Nella scena nuova quella riga direbbe **il falso** — il
		#    browser e' vivo *perche'* la scheda si e' chiusa bene.
		if fuoco_prodotto; then
			local prima dopo vive
			prima=$(finestre)
			inf "finestre col titolo «REMOTIX» PRIMA del gesto: $prima"
			X xdotool key --clearmodifiers ctrl+t >/dev/null 2>&1
			sleep 2
			X xdotool type --clearmodifiers --delay 25 "https://$IND:$PORTA/$marca_c" >/dev/null 2>&1
			sleep 1
			X xdotool key --clearmodifiers Return >/dev/null 2>&1
			sleep 5
			X xdotool key --clearmodifiers ctrl+shift+Tab >/dev/null 2>&1
			sleep 2
			X xdotool key --clearmodifiers ctrl+w 2>/dev/null
			# ⚠ Otto secondi: il congedo esce dentro `pagehide`, cioe' subito, e
			#   quel che non e' uscito qui non uscira' piu'.
			sleep 8
			dopo=$(finestre)
			vive=$(X xdotool search --name . 2>/dev/null | wc -l)
			inf "finestre col titolo «REMOTIX» DOPO: $dopo  ·  finestre del browser: $vive"
			if [ "$dopo" -lt "$prima" ] && [ "$vive" -gt 0 ]; then
				gesto_fatto=fatto
				ok "⭐ la SCHEDA si e' chiusa e il BROWSER e' vivo: e' la scena di"
				ok "   §8.2 CHIUSO_DALL_UTENTE, e se la pagina si congeda e' qui"
				ok "   che lo fa"
			else
				gesto_fatto=scena-sbagliata
				ko "⛔ la scena non e' quella dichiarata: finestre $prima → $dopo,"
				ko "   finestre del browser $vive.  Il congedo che segue — o la sua"
				ko "   assenza — NON e' giudicabile"
			fi
		else
			gesto_fatto=nessuna-finestra
			ko "⛔ non trovo la finestra: la scheda non e' stata chiusa col gesto,"
			ko "   e il congedo che segue (o la sua assenza) NON e' giudicabile"
		fi
		# ⚠ E adesso si chiude il browser, che resta vivo PER DISEGNO: non e' un
		#   ripiego e non toglie niente alla misura — la scheda in prova non c'e'
		#   piu' da otto secondi.
		kill "$PID_BR" 2>/dev/null
		wait "$PID_BR" 2>/dev/null
		PID_BR=
	fi
	inf "si aspettano 40 s: se il client non si congeda, il posto lo libera il"
	inf "tetto d'inattivita' di 30 s (§2.2), e le due strade si distinguono"
	sleep 40
	# ⚠ Il marcatore di fine lo batte curl, non il browser: il browser non c'e'
	#   piu', ed e' proprio la sua assenza che si sta misurando.  Il marcatore
	#   serve solo a chiudere il segmento, e questo si dichiara.
	curl -sk --max-time 15 -o /dev/null "https://$IND:$PORTA/$marca_b" 2>/dev/null
	sleep 1

	if ! scarica_registro "$T/$motore-$gamba.log"; then
		ko "il registro del server non si e' letto: nessun verdetto per questa gamba"
		return 3
	fi

	# ⛔⭐ CHE IL BROWSER AVESSE DAVVERO DUE SCHEDE NON SI CREDE AL PILOTA: lo
	#     dice il registro del server.  «Ho battuto ctrl+t» e «la seconda scheda
	#     e' nata» sono due fatti diversi, e a separarli e' una richiesta
	#     arrivata — la stessa forma con cui questo banco verifica l'avviso del
	#     certificato e la digitazione.
	if ! grep -q "$marca_c" "$T/$motore-$gamba.log"; then
		ko "⛔ IL BROWSER NON AVEVA DUE SCHEDE: il marcatore «$marca_c» non e' nel"
		ko "   registro del server.  Allora «ctrl+w» puo' aver chiuso il PROGRAMMA"
		ko "   invece della scheda, e in quella scena non esce niente per nessuna"
		ko "   via — nemmeno da un prodotto sano."
		gesto_fatto=senza-seconda-scheda
	fi

	# ⛔ E la conseguenza si tira QUI, non la tira chi legge.
	if [ "$gesto_fatto" != fatto ]; then
		if [ "$atteso" = sessione ]; then
			ko "⛔ questa gamba NON DA' UN VERDETTO ($gesto_fatto): lo scenario"
			ko "   «sessione» giudica il congedo, e il congedo si giudica solo su"
			ko "   una chiusura di SCHEDA.  ⚠ Un rosso preso qui sarebbe dato"
			ko "   all'imputato sbagliato — e' gia' successo due volte in questa"
			ko "   fase (LEZIONI.md §1.9)."
			return 3
		fi
		inf "⚠ la scena della chiusura non e' quella dichiarata ($gesto_fatto), ⭐ ma"
		inf "  lo scenario «$atteso» non giudica il congedo: si prosegue, e sta"
		inf "  scritto"
	fi
	python3 "$REG" passi --log "$T/$motore-$gamba.log" \
		--marca-inizio "$marca_a" --marca-fine "$marca_b" \
		--atteso "$atteso" --utente "$UTENTE" \
		--registra "{\"banco\":\"P5\",\"giro\":\"$GIRO\",\"gamba\":\"$gamba\",\"motore\":\"$motore\",\"motore_binario\":\"$(eval echo \$VER_$(echo "$motore" | tr a-z A-Z))\",\"origine\":\"https://$IND:$PORTA/ — la pagina del PRODOTTO, non nostra\"}"
	return $?
}

# ---------------------------------------------------------------------------
# N1 — LA SONDA CHE DICE SI' E LA SONDA CHE DICE NO, sullo stesso browser,
#      sulla stessa pagina, nello stesso giro (S1 §4.4).
#
# ⛔ Perche' NON passa dalla pagina del prodotto: l'impronta la scrive il server
#    dentro `src/pagina.html`, e per storpiarla bisognerebbe modificare la
#    pagina del prodotto — cioe' misurare codice che abbiamo cambiato noi.  La
#    sonda di B2 e' NOSTRA, apre la sessione con l'impronta che le si da', e
#    manda un `CIAO` conforme aspettando l'`ECCOMI`: contro il prodotto e' la
#    prova giusta, ed e' meccanica che esiste gia'.
#
# ⛔ E i due esiti valgono SOLO INSIEME.  S1 §4.4: *«solo con P2 verde e P3
#    rosso il risultato significa qualcosa»* — con P3 verde il banco non
#    distingue niente, e con P2 rosso non si sta misurando l'impronta, si sta
#    misurando un server che non risponde.
# ---------------------------------------------------------------------------
gamba_sonda() # $1 = motore   $2 = binario   $3.. = comando
{
	local motore=$1; shift
	local storpiata
	# ⛔ «Sbagliata di un byte», non «un'altra impronta»: un valore qualunque
	#    potrebbe fallire per la lunghezza o per il base64, e allora il rosso
	#    non direbbe niente sul confronto dell'impronta.
	storpiata=$(python3 - "$IMPRONTA" <<'PY'
import base64, sys
b = bytearray(base64.b64decode(sys.argv[1]))
b[0] ^= 0x01
print(base64.b64encode(bytes(b)).decode())
PY
)
	local esito_gamba=0 caso
	for caso in giusta storpiata; do
		local imp=$IMPRONTA atteso=APERTA
		if [ "$caso" = storpiata ]; then imp=$storpiata; atteso=NON-APERTA; fi
		local giro_sonda="$GIRO-$motore-n1-$caso"
		local n0 url visto i
		n0=$(righe)
		url="http://127.0.0.1:$PORTA_LOC/01-b2-sonda.html?avvia=1&url=https://$IND:$PORTA/rcp/1&impronta=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=""))' "$imp")"
		rm -rf "$T/$motore-n1"; mkdir -p "$T/$motore-n1"
		X "$@" "$url" >"$T/$motore-n1-$caso.log" 2>&1 &
		PID_BR=$!
		i=0; visto=""
		while [ "$i" -lt 45 ]; do
			visto=$(python3 - "$QUI/01-p5-esiti.jsonl" "$n0" "https://$IND:$PORTA/rcp/1" <<'PY'
import json, os, sys
p, n0, ind = sys.argv[1], int(sys.argv[2]), sys.argv[3]
if not os.path.exists(p):
    sys.exit(1)
righe = open(p, encoding="utf-8").read().splitlines()
for i in range(len(righe), n0, -1):
    try:
        d = json.loads(righe[i - 1])
    except Exception:
        continue
    if d.get("banco") or d.get("indirizzo") != ind:
        continue
    print(d.get("esito"), (d.get("motore") or "")[:100], sep="\t")
    sys.exit(0)
sys.exit(1)
PY
) && break
			sleep 1
			i=$((i + 1))
		done
		kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; PID_BR=
		if [ -z "$visto" ]; then
			ko "N1/$caso su $motore: nessun esito in $i s"
			inf "richieste al raccoglitore: $(grep -c '^richiesta: ' "$T/racc.log")"
			tail -4 "$T/$motore-n1-$caso.log" | sed 's/^/        /'
			esito_gamba=1
			continue
		fi
		local e m
		IFS=$'\t' read -r e m <<< "$visto"
		if [ "$e" = "$atteso" ]; then
			ok "N1/$caso su $motore: $e (atteso $atteso) — $m"
		else
			ko "⛔ N1/$caso su $motore: $e, atteso $atteso"
			[ "$caso" = storpiata ] && ko "   ⛔ con l'impronta storpiata che passa, questo banco non distingue niente"
			[ "$caso" = giusta ]    && ko "   ⛔ con l'impronta giusta che NON passa, non si sta misurando l'impronta"
			esito_gamba=1
		fi
		registra "{\"banco\":\"P5\",\"giro\":\"$GIRO\",\"tipo\":\"N1\",\"motore\":\"$motore\",\"caso\":\"$caso\",\"impronta\":\"$imp\",\"atteso\":\"$atteso\",\"visto\":\"$e\",\"motore_dichiarato\":\"$m\"}"
		sleep 2
	done
	return $esito_gamba
}

# ---------------------------------------------------------------------------
prova_motore() # $1 = nome  $2 = binario  $3 = titolo della pagina  $4.. = comando
{
	local motore=$1 binario=$2 titolo=$3; shift 3
	log "7. ═══ $motore ═══"
	if ! command -v "$binario" >/dev/null; then
		inf "⚠ $binario non c'e' su questa macchina: si salta, E SI DICE"
		registra "{\"banco\":\"P5\",\"giro\":\"$GIRO\",\"tipo\":\"MOTORE-SALTATO\",\"motore\":\"$motore\"}"
		return 0
	fi
	PROVATI=$((PROVATI + 1))
	local male=0

	# ⛔ LA CARTELLA DEL PROFILO SI CREA PRIMA, E QUESTO BANCO L'AVEVA SBAGLIATO.
	#
	#    `[M]` 11 agosto 2026, e l'ha trovato una FOTOGRAFIA: con `--profile` su
	#    una cartella che non esiste, Firefox si ferma su una finestrella
	#    «Your Firefox profile cannot be loaded» e **non chiede mai la pagina**.
	#    Al server arrivano zero richieste e nel registro del browser non c'e'
	#    niente: un silenzio su tutt'e due i lati, per una cartella mancante.
	#    ⚠ E' lo stesso difetto gia' scritto in `01-b2-lancia-sonda.sh` il 10
	#    agosto — una cura applicata in un posto solo, che e' la forma che
	#    questo progetto paga piu' spesso.
	#
	# ⭐ E le tre preferenze qui sotto tolgono la scheda di benvenuto: senza,
	#    Firefox apre DUE schede al primo avvio, e la pagina in prova non e'
	#    l'unica — cioe' la scena non e' quella dichiarata.
	mkdir -p "$T/$motore-p"
	if [ "$motore" = firefox ]; then
		cat > "$T/$motore-p/user.js" <<'FINE'
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("datareporting.policy.firstRunURL", "");
user_pref("browser.aboutwelcome.enabled", false);
FINE
	fi

	log "   N1 — l'impronta giusta deve APRIRE, quella storpiata deve FALLIRE"
	gamba_sonda "$motore" "$@" || male=1

	# ── La finestra contro il prodotto ────────────────────────────────────
	rm -rf "$T/$motore"; mkdir -p "$T/$motore"
	X "$@" "https://$IND:$PORTA/p5-$motore-avvio-$GIRO" >"$T/$motore.log" 2>&1 &
	PID_BR=$!
	sleep 12
	fotografia "$motore-0-avviso"
	supera_avviso "$motore"
	# ⛔ CHE L'AVVISO SIA STATO SUPERATO NON SI PRESUME: lo dice il registro del
	#    server.  «La pagina non si e' aperta» e «il browser non e' partito» e
	#    «l'avviso non si e' superato» hanno tutti la stessa faccia da qui.
	sleep 2
	if scarica_registro "$T/$motore-avvio.log"; then
		if grep -q "p5-$motore-avvio-$GIRO" "$T/$motore-avvio.log"; then
			ok "⭐ l'avviso del certificato della PAGINA e' stato superato: il"
			ok "   marcatore del browser e' arrivato al server"
			registra "{\"banco\":\"P5\",\"giro\":\"$GIRO\",\"tipo\":\"AVVISO-PAGINA\",\"motore\":\"$motore\",\"superato\":\"si\",\"nota\":\"§4.1-bis: l'impronta NON copre il caricamento della pagina — l'avviso qui e' atteso\"}"
		else
			ko "⛔ il marcatore di $motore NON e' arrivato al server: l'avviso del"
			ko "   certificato della pagina non e' stato superato."
			ko "   ⛔ E allora le gambe N2 e P non misurerebbero il prodotto: si"
			ko "   fermano qui, per questo motore."
			fotografia "$motore-0-avviso-non-superato"
			registra "{\"banco\":\"P5\",\"giro\":\"$GIRO\",\"tipo\":\"AVVISO-PAGINA\",\"motore\":\"$motore\",\"superato\":\"no\"}"
			kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; PID_BR=
			return 1
		fi
	fi

	# ── N2: il controllo che dice NO sull'autenticazione ───────────────────
	if [ "$COMANDO_VIVO" = si ]; then
		if ! fuoco "REMOTIX"; then inf "⚠ non trovo la finestra col titolo REMOTIX"; fi
		gamba_pagina "$motore" n2-parola-sbagliata "$PAROLA_STORTA" respinto || male=1
		# ⛔ E SI GUARDA CHE IL NOME DIGITATO SIA ARRIVATO INTERO: se il server ha
		#    letto un altro nome, la digitazione e' finita nel posto sbagliato, e
		#    il tentativo speso e' colpa del pilota.  In quel caso non si riprova.
		if ! grep -q "CREDENZIALI ricevute utente=$UTENTE" "$T/$motore-n2-parola-sbagliata.log" 2>/dev/null; then
			ko "⛔ il server non ha letto «utente=$UTENTE»: la digitazione non e'"
			ko "   finita dove doveva.  ⛔ NON si riprova: un secondo tentativo"
			ko "   fallito per un difetto del pilota e' due terzi del budget di"
			ko "   §4.4-bis, e sarebbe speso senza misurare niente."
			grep "CREDENZIALI ricevute" "$T/$motore-n2-parola-sbagliata.log" 2>/dev/null | tail -2 | sed 's/^/        /'
			kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; PID_BR=
			return 1
		fi
		# Si riapre la finestra per la gamba buona: N2 l'ha chiusa apposta.
		X "$@" "https://$IND:$PORTA/p5-$motore-ripresa-$GIRO" >"$T/$motore-2.log" 2>&1 &
		PID_BR=$!
		sleep 10
	else
		inf "⚠ N2 SALTATA: senza comando di sblocco un tentativo fallito non si"
		inf "  disfa per dodici ore.  Il verdetto lo dichiara."
		registra "{\"banco\":\"P5\",\"giro\":\"$GIRO\",\"tipo\":\"N2-SALTATA\",\"motore\":\"$motore\",\"perche\":\"il comando di sblocco di §4.4-bis non risponde\"}"
	fi

	# ── P: il giro buono, fino a SESSIONE ─────────────────────────────────
	gamba_pagina "$motore" p-sessione "$PAROLA" sessione || male=1

	registra "{\"banco\":\"P5\",\"giro\":\"$GIRO\",\"tipo\":\"VERDETTO-MOTORE\",\"motore\":\"$motore\",\"esito\":\"$([ $male -eq 0 ] && echo CONFORME || echo NON-CONFORME)\"}"
	[ "$male" -eq 0 ] && ok "⭐ $motore: il giro passa" || ko "⛔ $motore: qualcosa non passa"
	return "$male"
}

PROVATI=0
if [ "$MOTORI" = tutti ] || [ "$MOTORI" = chrome ]; then
	prova_motore chrome google-chrome REMOTIX \
		google-chrome --ozone-platform=x11 --user-data-dir="$T/chrome-p" \
		--no-first-run --no-default-browser-check --disable-sync \
		--window-size=1280,1000 || ESITO=1
fi
if [ "$MOTORI" = tutti ] || [ "$MOTORI" = firefox ]; then
	prova_motore firefox firefox REMOTIX \
		firefox --no-remote --profile "$T/firefox-p" --width 1280 --height 1000 || ESITO=1
fi

# ---------------------------------------------------------------------------
log "8. Lo sblocco finale, e SI DICHIARA"
if [ "$COMANDO_VIVO" = si ]; then
	sblocca dopo
else
	inf "⚠ nessuno sblocco: il comando non risponde (vedi il punto 5)"
fi
inf "sblocchi di questo giro:${SBLOCCHI:- nessuno}"
inf "⛔ Un ban tolto e un ban mai scattato hanno lo stesso aspetto: le due righe"
inf "  qui sopra sono quel che li distingue, e stanno anche in 01-p5-esiti.jsonl."

log "Esito — ⛔ DUE COLONNE, NON UNA"
inf "motori provati: $PROVATI"
if [ "$PROVATI" -eq 0 ]; then
	ko "⛔ NESSUN motore provato: questo non e' un esito.  «Tutti quelli provati"
	ko "   sono andati bene» e' vero anche quando i provati sono zero."
	exit 6
fi
if [ "$PROVATI" -lt 2 ]; then
	ko "⛔ UN MOTORE SOLO: il criterio di B2 vuole DUE MOTORI SU DUE, e i difetti"
	ko "   piu' cari di questa fase vivevano nella DIFFERENZA fra i due — il posto"
	ko "   che non si liberava, le due strade del congedo.  Questo giro non le"
	ko "   puo' vedere, e non e' un verdetto su B2."
	ESITO=1
fi
python3 - "$QUI/01-p5-esiti.jsonl" "$GIRO" <<'PY'
import json, sys
try:
    righe = [json.loads(r) for r in open(sys.argv[1], encoding="utf-8") if r.strip()]
except Exception as e:
    print("    non ho potuto rileggere il registro:", e); sys.exit(0)
mie = [d for d in righe if d.get("giro") == sys.argv[2]]
print(f"    -- righe di questo giro nel registro: {len(mie)} (su {len(righe)} totali)")
per = {}
for d in mie:
    if d.get("tipo") == "PASSI":
        per.setdefault(d.get("motore"), {})[d.get("gamba")] = d["esito"].get("verdetto")
    if d.get("tipo") == "N1":
        per.setdefault(d.get("motore"), {})[f"n1-{d.get('caso')}"] = \
            ("ok" if d.get("visto") == d.get("atteso") else "NO")
if not per:
    print("    ⛔ nessuna colonna: non c'e' niente da mettere a confronto"); sys.exit(0)
gambe = sorted({g for v in per.values() for g in v})
print(f"    {'gamba':<24}" + "".join(f"{m:<18}" for m in per))
for g in gambe:
    print(f"    {g:<24}" + "".join(f"{str(per[m].get(g, '—')):<18}" for m in per))
PY
if [ "$ESITO" -eq 0 ]; then
	ok "⭐ P5: il prodotto regge il giro con un browser vero su due motori"
else
	ko "⛔ P5: qualcosa non passa — vedi sopra, colonna per colonna"
fi
inf "il dettaglio sta in $QUI/01-p5-esiti.jsonl, le fotografie in $COPIE"
exit "$ESITO"
