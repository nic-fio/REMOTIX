#!/bin/bash
#
# 01-b6-lancia.sh — gira SUL SERVER.  B6: i tre tetti della stretta di mano.
#
#   BERSAGLIO=innesto  bash .../01-b6-lancia.sh          tutto (due fasi)
#   BERSAGLIO=prodotto bash .../01-b6-lancia.sh sani     solo la fase «sani»
#   BERSAGLIO=prodotto bash .../01-b6-lancia.sh ping     solo la fase «ping»
#   BERSAGLIO=innesto  bash .../01-b6-lancia.sh elenco   le previsioni
#
# ⛔ `BERSAGLIO` E' OBBLIGATORIA — vedi `01-b0-bersaglio.sh`.
#
# ---------------------------------------------------------------------------
# ⛔⭐ CHE COSA CAMBIA PUNTANDO B6 AL PRODOTTO — la previsione, scritta PRIMA
#
# | cosa | innesto | prodotto | perche' |
# |---|---|---|---|
# | i tre tetti (5 · 60 · 10 s) | uguali | uguali | sono i `#define TETTO_*` di `rcp.c`, **identico byte per byte** nei due server |
# | ⛔ **il tetto del TRASPORTO** | si sceglie: 120 s / 15 s | ⛔ **30 s fissi** | `#define IDLE_MS 30000` in `src/trasporto.c`, e nessuna opzione lo tocca (nessun `getenv` in tutto `src/`) |
# | ⛔ **le due fasi** | indipendenti | ⛔ **NON indipendenti** | 30 s stanno sotto i 60 s delle credenziali: `credenziali-tetto` (sani) e `credenziali-tetto-sotto-il-trasporto` (ping) misurano LA STESSA COSA.  ⚠ CIAO (5 s) e ATTACCA (10 s) restano puliti — 30 > 10.  ⛔ Contarli come due conferme sarebbe contare due volte la stessa misura |
# | `cert-morte-silenziosa` | muore a 15 s | muore a **30 s** | e' il tetto del trasporto, letto dal pari |
# | `credenziali-presto` (tace 42 s) | passa sotto un tetto di 120 s | ⭐ passa **solo se i PING ci sono** | 42 s > 30 s: sul prodotto questo caso diventa una **seconda prova dei PING**, gratis, ed e' un guadagno — non una perdita |
# | il cronometro del primo tetto | armato dall'apertura del canale | uguale | `src/webtransport.c` `rcp_avvia()` arma `regola_battito()` nella stessa riga di `rcp_apri()`.  ⚠ Il commento dice *«nell'innesto questo mancava»*: se `ciao-tetto` desse «niente» sull'innesto e 5 s sul prodotto, la differenza e' **questa**, non §4.6 |
# | `ciao-senza-controllo` (R3.27, seconda risposta) | resta appesa fino a 120 s | ⚠ muore a **30 s** — per INATTIVITA', non per un tetto | e' lo stesso «non c'e' nessun tetto», con addosso un tempo di QUIC piu' corto.  ⛔ Il banco deve leggerlo come `morte-silenziosa`, non come «tetto scaduto»: la R3.27 resta APERTA su tutt'e due i bersagli |
# | il ban | vive nel processo, muore col riavvio | ⛔ vive **su file** | riaccendere non basta piu' (I7): il file dei ban di B6 si butta all'inizio, e si sblocca PRIMA del giro, dichiarandolo |
# | il registro | ⛔ **non esisteva** | ⛔ **non esisteva** | ⚠ i tre numeri del 10 agosto — 5,0 · 60,1 · 10,0 s — non sono riverificabili da nessuno.  Da questo giro c'e' `b6-esiti-<bersaglio>.jsonl` |
#
# ⛔ CON UN FILTRO IL GIRO E' PARZIALE, E LO DICE.  La fase «sani» misura i tre
#    tetti; la fase «ping» misura **la cura di §4.6**, cioe' che il server
#    tenga viva la connessione coi PING del trasporto.  Un verde su una sola
#    delle due si legge «quella meta' passa», mai «B6 passa».
#
# ---------------------------------------------------------------------------
# ⛔ CHE COSA MISURA, IN UNA RIGA D'UTENTE
#
# *«Quanto ci mette a dirti che non ce l'ha fatta, invece di restare li'
# appeso.»*  `RCP.md` §4.6 mette tre tetti alla stretta di mano — 5 s al
# `CIAO`, 60 s alle `CREDENZIALI`, 10 s all'`ATTACCA` — e scaduto un tetto il
# server DEVE congedare con `TEMPO_SCADUTO` `0x0D`, per le due strade di §3.1.
#
# ⛔ **Non prima, non dopo, e col motivo giusto**: il banco prova tutt'e tre le
#    cose, e il «non prima» e' la meta' che nessuno scrive (vedi i casi
#    `-presto` in `01-b6-tetti.py`).
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' DUE FASI, E PERCHE' LA SECONDA E' QUELLA CHE PROVA QUALCOSA
#
# `RCP.md` §4.6, riquadro del rilievo R1.8: i 60 secondi della parola d'ordine
# erano **irraggiungibili**, perche' mentre l'utente digita sul filo non passa
# niente e al trentesimo secondo scatta il tempo di inattivita' di QUIC — la
# connessione muore **in silenzio, senza motivo**, prima che il tetto dei 60
# possa scadere.  La cura e' del server: i **PING del trasporto**.
#
#   fase «sani»  il tetto del trasporto e' portato a **120 s**, sopra tutti e
#                tre i tetti del protocollo: qui i tre numeri si leggono
#                puliti, perche' a chiudere puo' essere solo RCP.
#                ⚠ Ma con 120 s **anche un server che non manda un PING**
#                darebbe 60 s: questa fase da sola benedirebbe la violazione
#                che §4.6 esiste per curare — `LEZIONI.md` §1.3, ed e' la
#                stessa forma del rilievo R3.19 su B3.
#
#   fase «ping»  ⭐ il tetto del trasporto e' portato **SOTTO** il tetto del
#                protocollo: `TETTO_PING`, cioe' 15 s contro 60.  Se i PING
#                ci sono, `TEMPO_SCADUTO` arriva **lo stesso a 60 s**, dopo
#                aver attraversato quattro volte il tetto del trasporto.  Se
#                non ci sono, la connessione muore intorno ai 15 s **senza
#                motivo** — la firma che §4.6 descrive, con un numero che non
#                si confonde con nessuno dei tre tetti.
#
# ⛔ E IL TETTO DEL TRASPORTO SI LEGGE DAL PARI, NON SI DA' PER MESSO — e' il
#    rilievo R8.3, pagato su `01-b3-quarto-giro.sh`: fino al 10 agosto 2026 la
#    premessa era scritta in un commento e nessuno accendeva il server con
#    l'opzione.  Qui la sonda di B2 lo chiede al filo prima di ogni fase, e se
#    non e' il numero atteso **la fase non parte**.
#
# ---------------------------------------------------------------------------
# ⛔ I TRE NUMERI CHE QUESTO BANCO CONFRONTA, E IL FATTO DATATO
#
#   il DOCUMENTO   `RCP.md` §4.6 — scritto a mano in `01-b6-tetti.py`;
#   il CODICE      i `#define TETTO_*`, letti qui sotto **dalla copia che e'
#                  stata compilata** (`examples/rcp.c`) e confrontati con il
#                  sorgente (`rcp/rcp.c`), perche' una copia stantia darebbe un
#                  numero che nel binario non c'e';
#   la MISURA      quel che arriva sul filo.
#
# ⛔ Il 10 agosto 2026, rilievo R9.9, `TETTO_ATTACCA` e' stato portato da
#    **60 000 a 10 000 ms** sulla sola lettura di §4.6, **senza che nessuno lo
#    misurasse**, e il commento nel codice lo dichiara: *«nessun banco lo
#    vedeva: B6 non e' ancora scritto»*.  ⭐ Questo banco e' il primo testimone
#    di quel numero.  Se documento e codice non vanno d'accordo lo dice, e non
#    si adatta a nessuno dei due.
#
# ---------------------------------------------------------------------------
# ⛔ E IL REGISTRO DEL SERVER SI GUARDA, MA NON E' L'ARBITRO
#
# Il motivo lo verifica **il lato che riceve** (§8.1): il registro del server
# e' la stessa mano che ha scritto il codice.  Le righe «scaduto il tetto per
# …» si stampano in fondo come **diagnosi**, ed e' dichiarato.
#
# ---------------------------------------------------------------------------
# ⛔ LO STATO INIZIALE (B0.1, B0.2, B0.3)
#
#  · il server si **ricostruisce e si riaccende** a ogni fase: e' anche l'unico
#    modo di azzerare i due contatori di §4.4-bis e il registro delle sessioni.
#    ⚠ `rcp_azzera_registro_sessioni()` esiste in `rcp.c` **ma non ha nessun
#      chiamante innestato**: da fuori non si puo' chiamare, e chi legge la
#      riga in `rcp.h` crede che il banco la usi.  Non la usa: riaccende;
#  · l'indirizzo di provenienza e' lo stesso di tutti gli altri banchi, e dal
#    10 agosto 2026 il conto di §4.4-bis e' **uno solo, sul solo indirizzo**, e
#    porta a un **ban di dodici ore** (B0.3).  ⚠ La riga vecchia diceva «per
#    nome e per indirizzo», ed era la forma precedente.  Il primo controllo di
#    `01-b6-tetti.py` e' una stretta di mano intera: se torna
#    `TROPPI_TENTATIVI`, il banco **si ferma con l'uscita 5** e dice che il ban
#    e' di un altro banco, invece di dare rosso ai tetti.
#
# ⭐ E LA DICHIARAZIONE CHE B0.3 PRETENDE, PERCHE' «non e' scattato» E
#    «qualcuno l'ha tolto» HANNO LO STESSO ASPETTO:
#
#      ⛔ **B6 non chiama il comando di sblocco, e dice perche'.**  Il comando
#         esiste — `01-b8-sblocca.py`, che parla al server su una presa di
#         comando (`--comando-socket`) — ma vuole un server **acceso con quella
#         opzione**, e B6 accende il proprio senza.  ⭐ La cura che B6 usa e'
#         piu' forte: **riaccende il server a ogni fase**, e il conto di
#         §4.4-bis vive nel processo, quindi riparte da zero.
#         ⚠ *Fino a stasera questa riga diceva che il comando «non esiste».
#         Era vero quando e' stata scritta e ha smesso di esserlo nel giro
#         di un'ora: e' la forma **E5**, un fatto che era una deduzione mai
#         riverificata.*
#
#      ⭐ **E B6 non fallisce mai un'autenticazione**: tutti i suoi casi usano
#         le credenziali buone, o si fermano prima di `CREDENZIALI`.  Quindi
#         **non consuma il conto** e non lascia un ban addosso ai banchi che
#         vengono dopo.  E' l'unico modo che questo banco ha di rispettare
#         B0.3 senza una cura che non esiste.
#
# ---------------------------------------------------------------------------
# ⛔ NESSUNA REDIREZIONE ATTORNO A `enter.sh`
#
#    `bash enter.sh --root "..." > file 2>&1` si porta via **la richiesta di
#    password di sudo**, e lo script resta ad aspettare una domanda che nessuno
#    vede.  ⚠ Non e' `>/dev/null`: e' **qualunque** redirezione attorno a
#    `enter.sh` (10 agosto 2026, su `01-b5-lancia.sh`).  Le redirezioni vanno
#    DENTRO le virgolette del comando remoto.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
UTENTE=prova
PAROLA=parola-di-prova

# ⛔ Il bersaglio: una forma sola per i quattro banchi, in un file solo.
SIGLA=b6

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

# shellcheck source=01-b0-bersaglio.sh
. "$FUORI/01-b0-bersaglio.sh"
IND=$B_IND
PORTA=$B_PORTA
# ⛔ I due tetti del trasporto vengono dal PROFILO, non da qui.  Sull'innesto
#    sono 120 000 e 15 000 ms; sul prodotto sono 30 000 tutt'e due, perche'
#    `IDLE_MS` non si sposta — e quando coincidono le due fasi NON sono
#    indipendenti, e il banco lo dichiara invece di contarle due volte.
TETTO_SANI=$B_IDLE_LUNGO
TETTO_PING=$B_IDLE_CORTO

AZIONE=${1:-tutto}
case "$AZIONE" in
	tutto|sani|ping|elenco) ;;
	*) ko "azione sconosciuta: $AZIONE  (tutto | sani | ping | elenco)"; exit 2 ;;
esac

log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

# ---------------------------------------------------------------------------
# ⛔ LA SENTINELLA: «vuoto» non e' «zero» — rilievi R12-A.7 e R12-A.23, e la
#    cura era gia' scritta nella stessa cartella, in `01-b11-guasto.sh:92-129`.
#
# `CHI=$(bash "$ENTRA" --root "ss -ulnp | grep ':$PORTA '")` diceva «porta
# libera» in tre casi opposti: la porta e' davvero libera · `ss` non c'e' nel
# contenitore · `enter.sh` non ha eseguito il comando.  ⛔ E qui l'aggravante
# era che quella lettura avveniva **una volta sola, all'inizio**: B6 era
# l'unico dei quattro banchi a non ricontrollare la porta fra le due fasi.
#
# ⭐ Il comando remoto stampa da se' il proprio stato d'uscita, e in piu' c'e'
#    il controllo positivo dello strumento: `ss` stampa sempre almeno la
#    propria intestazione, e se non stampa niente non ha guardato niente.
# ⚠ La sostituzione di comando e' lecita da qui in poi e non prima: la riga
#   `--root "true"` qui sopra e' quella che si prende la richiesta di password.
#   Il divieto in cima a questo file riguarda le REDIREZIONI attorno a
#   `enter.sh`, che si porterebbero via quella domanda.
USCITA=""
dentro() # $1 = comando remoto.  Uscita in $USCITA, stato = quello del comando
{
	local tutto stato
	tutto=$(bash "$ENTRA" --root "$1"'; printf "\nB6-FINE=%s\n" $?')
	stato=$(printf '%s\n' "$tutto" | sed -n 's/^B6-FINE=\([0-9][0-9]*\)$/\1/p' | tail -1)
	USCITA=$(printf '%s\n' "$tutto" | grep -v '^B6-FINE=')
	if [ -z "$stato" ]; then
		return 125   # non e' arrivato in fondo: non e' uno zero
	fi
	return "$stato"
}

# Chi tiene la porta UDP.  0 = occupata (le righe in $CHI) · 1 = libera ·
# 2 = non si sa, e ⛔ «non si sa» non si arrotonda a «libera».
CHI=""
chi_tiene_la_porta()
{
	local st
	dentro "ss -ulnp"
	st=$?
	if [ "$st" -ne 0 ]; then
		ko "⛔ «ss -ulnp» non ha risposto dentro il contenitore (uscita $st):"
		printf '%s\n' "$USCITA" | tail -5 | sed 's/^/        /'
		return 2
	fi
	if [ -z "$USCITA" ]; then
		ko "⛔ «ss -ulnp» non ha stampato NIENTE, nemmeno l'intestazione:"
		ko "   lo strumento e' muto, e il suo silenzio non e' una porta libera"
		return 2
	fi
	CHI=$(printf '%s\n' "$USCITA" | grep ":$PORTA ")
	[ -n "$CHI" ]
}

if [ "$AZIONE" = elenco ]; then
	bash "$ENTRA" --root "python3 $DENTRO/01-b6-tetti.py --bersaglio $B_NOME --elenco"
	exit 0
fi

# ---------------------------------------------------------------------------
# ⛔ 1. IL SERVER SI PREPARA — e le due strade non sono la stessa (vedi
#    `01-b0-bersaglio.sh`).  ⚠ Sull'innesto il pezzo che conta e' quello che fa
#    SCORRERE IL TEMPO: senza `rcp_tempo()` nel percorso di scrittura nessun
#    tetto scade mai, e B6 stamperebbe tre rossi contro un modulo intatto.
#    Sul prodotto quel pezzo e' `wt_battito_ns()`/`wt_batti()`, che il ciclo di
#    `main.c` chiama sempre: non c'e' un innesto che possa mancare.
bersaglio_pronto || exit 3

if [ "$B_NOME" = innesto ]; then
	SORG=$DENTRO/b2/ngtcp2/examples/http3_server_proto_codec.cc
	QUANTI=$(bash "$ENTRA" --root "grep -c 'rcp_tempo(rcp_' $SORG" | tr -cd '0-9')
	if [ "${QUANTI:-0}" -ge 1 ]; then
		ok "la chiamata a rcp_tempo() e' nel sorgente ($QUANTI)"
	else
		ko "⛔ la chiamata a rcp_tempo() NON e' nel sorgente: il tempo di RCP"
		ko "   non scorrerebbe, nessun tetto scadrebbe, e i tre rossi"
		ko "   sarebbero del banco"
		exit 3
	fi
else
	# ⭐ Il controllo equivalente sul prodotto, e si MISURA come l'altro.
	QUANTI=$(bash "$ENTRA" --root "grep -c 'wt_batti(' $DENTRO/remotix/trasporto.c" | tr -cd '0-9')
	if [ "${QUANTI:-0}" -ge 1 ]; then
		ok "il ciclo del prodotto chiama wt_batti() ($QUANTI): il tempo di RCP scorre"
	else
		ko "⛔ `wt_batti()` non compare in trasporto.c: senza, l'orologio di"
		ko "   RCP non avanza e nessun tetto di §4.6 scade mai.  I tre rossi"
		ko "   sarebbero del banco, non di §4.6"
		exit 3
	fi
fi

# ---------------------------------------------------------------------------
# ⛔ 1-bis. LO STATO INIZIALE DEL BAN — B0.1, B0.2, B0.3.
#
# ⭐ B6 non fallisce MAI un'autenticazione: tutti i suoi casi usano le
#    credenziali buone o si fermano prima di `CREDENZIALI`.  Quindi non consuma
#    il conto e non lascia un ban addosso a chi viene dopo.
# ⛔ Ma puo' TROVARLO: il ban del prodotto sta su file e sopravvive al riavvio
#    (I7), quindi «riaccendere il server» — che era la cura di B6 — non basta
#    piu'.  Il file dei ban di B6 e' suo soltanto, e si butta qui.
log "1-bis. Lo stato iniziale del ban (B0.1, B0.2, B0.3)"
bersaglio_butta_il_ban
inf "⭐ e B6 non fallisce mai un'autenticazione: non consuma il conto, e non"
inf "   lascia un ban a nessuno"

# ⛔ I TETTI SCRITTI NEL CODICE, LETTI DALLA COPIA CHE SI COMPILA.
#
#    `01-b3-rcp-innesta.py` COPIA `rcp/rcp.c` in `examples/`: e' quella copia
#    che finisce nel binario.  Leggere solo il sorgente direbbe un numero che
#    nel server in esecuzione potrebbe non esserci — e' la stessa forma del
#    registro di compilazione vecchio (E8: «vecchio» e «assente» hanno lo
#    stesso aspetto).  Qui si leggono tutt'e due e si pretende che combacino.
#
# ⛔ E «non ho potuto leggere» non e' «zero»: se il `grep` non trova la riga si
#    dichiara, e il confronto documento/codice **non si fa** invece di farsi
#    con un numero inventato.
leggi_tetto() # $1 = file, $2 = nome del define
{
	local f=$1 n=$2 v=""
	[ -r "$f" ] || return 1
	v=$(grep -E "^#define[[:space:]]+$n[[:space:]]+[0-9]+" "$f" \
		| head -1 | awk '{print $3}')
	[ -n "$v" ] || return 1
	printf '%s' "$v"
}

log "2. I tetti scritti nel CODICE — e il numero cambiato il 10 agosto"
# ⛔ I DUE FILE DIPENDONO DAL BERSAGLIO, e il confronto e' lo stesso.
#
#   innesto   `01-b3-rcp-innesta.py` COPIA `rcp/rcp.c` in `examples/`: e' quella
#             copia che finisce nel binario, e leggere solo il sorgente direbbe
#             un numero che nel server in esecuzione potrebbe non esserci.
#   prodotto  ⭐ non c'e' nessuna copia: il Makefile compila `src/rcp.c` sul
#             posto.  ⚠ Il confronto si fa lo stesso, fra `src/rcp.c` e
#             `banchi/rcp/rcp.c` — che DEVONO restare identici byte per byte
#             (md5 `cb7af778…`): il giorno in cui divergessero, i banchi e il
#             prodotto misurerebbero due protocolli diversi con lo stesso nome.
if [ "$B_NOME" = innesto ]; then
	SORGENTE_RCP=$FUORI/rcp/rcp.c
	COMPILATO_RCP=$FUORI/b2/ngtcp2/examples/rcp.c
else
	SORGENTE_RCP=$FUORI/rcp/rcp.c
	COMPILATO_RCP=$FUORI/remotix/rcp.c
fi
TETTI_CODICE=""
LETTURA_OK=si
for coppia in "CIAO:TETTO_CIAO" "CREDENZIALI:TETTO_CREDENZIALI" "ATTACCA:TETTO_ATTACCA"; do
	NOME=${coppia%%:*}
	DEF=${coppia##*:}
	A=$(leggi_tetto "$SORGENTE_RCP" "$DEF") || A=""
	B=$(leggi_tetto "$COMPILATO_RCP" "$DEF") || B=""
	if [ -z "$A" ] || [ -z "$B" ]; then
		ko "⛔ $DEF non si legge (sorgente «${A:-—}», copia compilata «${B:-—}»)"
		ko "   Non e' «vale zero»: e' che non si e' potuto guardare."
		LETTURA_OK=no
		continue
	fi
	if [ "$A" != "$B" ]; then
		ko "⛔ $DEF: «$SORGENTE_RCP» dice $A e «$COMPILATO_RCP» dice $B"
		if [ "$B_NOME" = innesto ]; then
			ko "   L'innesto non ha ricopiato rcp.c: il binario non ha il"
			ko "   numero che credi di aver cambiato."
		else
			ko "   ⛔ src/rcp.c e banchi/rcp/rcp.c NON sono piu' identici: da"
			ko "      qui in poi i banchi e il prodotto parlano due protocolli"
			ko "      diversi con lo stesso nome, e nessun confronto fra i due"
			ko "      bersagli vuol piu' dire niente."
		fi
		LETTURA_OK=no
		continue
	fi
	ok "$DEF = $B ms  (sorgente e copia compilata combaciano)"
	TETTI_CODICE="$TETTI_CODICE${TETTI_CODICE:+,}$NOME=$B"
done
if [ "$LETTURA_OK" != si ]; then
	ko "⛔ senza i numeri del codice il banco misurerebbe contro il solo"
	ko "   documento, e il confronto che B6 esiste per fare non si farebbe"
	exit 3
fi
inf "⚠ TETTO_ATTACCA e' passato da 60 000 a 10 000 ms il 10 agosto 2026"
inf "  (R9.9) sulla sola lettura di §4.6, senza misura: questo giro e' il"
inf "  suo primo testimone"

# ---------------------------------------------------------------------------
# ⛔ IL REGISTRO DI COMPILAZIONE SI CANCELLA PRIMA, non dopo: se la
#    compilazione non parte affatto, un `tail` mostrerebbe il registro del giro
#    precedente e la diagnosi partirebbe da un errore che oggi non e' successo.
rm -f "$FUORI/b6-compila.log"
if ! bash "$ENTRA" --root \
	"ninja -C $DENTRO/b2/ngtcp2/build bsslserver > $DENTRO/b6-compila.log 2>&1"; then
	ko "la compilazione e' fallita:"
	if [ -f "$FUORI/b6-compila.log" ]; then
		tail -25 "$FUORI/b6-compila.log" | sed 's/^/        /'
	else
		ko "   ⛔ e il registro di compilazione NON ESISTE: non e' ninja che"
		ko "      ha taciuto, e' che non si e' arrivati a lanciarlo"
	fi
	exit 3
fi
ok "compilato"

# ---------------------------------------------------------------------------
log "3. La porta — la guarda `bersaglio_accendi`, prima di ogni accensione"
inf "⛔ e non una volta sola all'inizio: fra la prima fase e la seconda ci sta"
inf "   un altro server, e «non si sa» non si arrotonda a «libera»"

# ---------------------------------------------------------------------------
PID=""

accendi() # $1 = tetto d'inattivita' in ms, $2 = etichetta
{
	local tms=$1 et=$2
	# ⛔ L'accensione, il controllo della porta e il rifiuto di accendere con un
	#    tetto che il bersaglio non sa dare stanno tutti in `bersaglio_accendi`:
	#    un posto solo per i due server.
	bersaglio_accendi "$et" "$tms" || return 1
	PID=$B_PID
	# ⛔ E SUBITO L'IMPRONTA: ho acceso il server che ho dichiarato?
	bersaglio_impronta || return 1
	return 0
}

# ⛔ SPEGNERE NON E' MANDARE UN `kill` — rilievo R12-A.24.
#
#    `spegni()` mandava il segnale e azzerava `PID` **subito**; `fase ping`
#    chiamava `accendi` pochi millisecondi dopo, sulla stessa porta.  Il
#    sintomo sarebbe stato «il server non e' partito» all'inizio della fase
#    `ping`, cioe' un'uscita 4 — «lo strumento non e' certificato» — su un
#    server sano: il rosso puntato sull'imputato sbagliato.
#
# ⭐ La cura era gia' scritta, la stessa notte, in `01-c2-lancia.sh:139-155`, e
#    perfino il perche': *«fra la morte del processo e il rilascio della porta
#    passa un istante che, se non si aspetta, fa misurare alla scena 1 una
#    porta ancora tenuta»*.  Due mani sullo stesso problema; qui si prende la
#    piu' forte.
# ⛔ `/proc`, non `kill -0`: su un processo di root `kill -0` da utente normale
#    dice «proibito», che non e' «morto».
spegni()
{
	# ⛔ Lo spegnimento sta in `bersaglio_spegni`: aspetta che il processo
	#    sparisca da `/proc` E che la porta si liberi, che sono due cose diverse
	#    (rilievo R12-A.24).  ⚠ Sul prodotto vale doppio: `SIGTERM` non e' la
	#    fine ma l'INIZIO di un percorso — `main.c` congeda tutte le sessioni
	#    con `SERVER_IN_CHIUSURA` e aspetta fino a due secondi che i byte
	#    escano.  Un banco che pretendesse la morte immediata leggerebbe «non
	#    muore» su un server che sta facendo il suo mestiere.
	bersaglio_spegni
}

# ⛔ IL TETTO SI MISURA, NON SI DA' PER MESSO — rilievo R8.3.
#    La sonda di B2 prende i parametri di trasporto **dove arrivano**, cioe'
#    dal pari, invece che dalla configurazione di chi li manda.
# ⚠ Non si guarda il suo codice d'uscita: la sonda giudica sei proprieta' e qui
#   ne interessa una sola.  Si legge il NUMERO, e «non ho letto niente» ha un
#   ramo suo — «vuoto» e «proibito» non hanno lo stesso aspetto.
tetto_dal_pari() # $1 = atteso in ms, $2 = etichetta
{
	local atteso=$1 et=$2 letto=""
	rm -f "$FUORI/b6-$B_NOME-$et-tetto.log"
	bash "$ENTRA" --root \
		"python3 $DENTRO/01-b2-sonda-trasporto.py --indirizzo $IND --porta $PORTA --etichetta b6-$et --idle-atteso $atteso > $DENTRO/b6-$B_NOME-$et-tetto.log 2>&1"
	if [ ! -f "$FUORI/b6-$B_NOME-$et-tetto.log" ]; then
		ko "la sonda non ha scritto niente: non si e' potuto guardare"
		return 2
	fi
	letto=$(grep -m1 'max_idle_timeout *=' "$FUORI/b6-$B_NOME-$et-tetto.log" | tr -dc '0-9')
	if [ -z "$letto" ]; then
		ko "non ho potuto leggere max_idle_timeout dal pari: la fase non parte"
		ko "   (senza il tetto non si sa chi chiudera' — R8.3)"
		tail -6 "$FUORI/b6-$B_NOME-$et-tetto.log" | sed 's/^/        /'
		return 2
	fi
	if [ "$letto" -ne "$atteso" ]; then
		ko "⛔ il tetto d'inattivita' sul filo e' $letto ms, non $atteso"
		ko "   Con questo tetto non si sa se a chiudere sara' RCP o QUIC,"
		ko "   e i numeri di §4.6 non si potrebbero attribuire a nessuno."
		return 2
	fi
	ok "⭐ tetto d'inattivita' misurato sul filo: $letto ms — la premessa regge"
	return 0
}

ESITO=0
FATTE=""

fase() # $1 = nome (sani|ping), $2 = tetto del trasporto in ms
{
	local nome=$1 tms=$2 e=0
	log "Fase «$nome» — tetto del trasporto ${tms} ms"
	if [ "$nome" = ping ]; then
		inf "⭐ il tetto del TRASPORTO sta SOTTO il tetto del PROTOCOLLO"
		inf "  (${tms} ms contro 60 000): se TEMPO_SCADUTO arriva lo stesso a"
		inf "  60 s, i PING di §4.6 ci sono; se muore intorno ai ${tms} ms"
		inf "  senza motivo, mancano — ed e' la firma che §4.6 descrive"
	else
		inf "il tetto del TRASPORTO sta sopra tutti e tre i tetti del"
		inf "protocollo: qui a chiudere puo' essere solo RCP"
		inf "⚠ e per questo questa fase, DA SOLA, non prova i PING"
	fi
	accendi "$tms" "$nome" || { ESITO=4; return 4; }
	if ! tetto_dal_pari "$tms" "$nome"; then
		spegni
		ESITO=5
		return 5
	fi
	bash "$ENTRA" --root \
		"python3 -u $DENTRO/01-b6-tetti.py --indirizzo $IND $(bersaglio_opzioni_python) --utente $UTENTE --parola $PAROLA --fase $nome --idle $tms --tetti-codice $TETTI_CODICE"
	e=$?

	# ⛔ B0.5, dal di fuori.  Il banco lo chiede a ogni caso aprendo una
	#    connessione nuova; questo lo chiede al SISTEMA, che e' un testimone
	#    diverso: un processo puo' rispondere e avere gia' perso i figli.
	if [ -d "/proc/$PID" ]; then
		ok "il processo $PID c'e' ancora (B0.5, dal sistema)"
	else
		ko "⛔ IL SERVER E' MORTO durante la fase «$nome»"
		e=1
	fi

	# ⚠ Il registro del server: diagnosi, NON arbitro (§8.1 vuole il congedo
	#   verificato dal lato che riceve).
	log "Che cosa ha scritto il server nella fase «$nome» — diagnosi, non prova"
	if [ -f "$B_LOG_FUORI" ]; then
		# ⛔ Si conta l'impronta DEL BERSAGLIO: il prodotto non scrive
		#    «REMOTIX B3» da nessuna parte, e uno zero verrebbe letto come
		#    «il server non ha scritto niente».
		grep -cE "$B_IMPRONTA" "$B_LOG_FUORI" \
			| sed 's/^/        righe di registro: /'
		if grep -q "scaduto il tetto per" "$B_LOG_FUORI"; then
			grep "scaduto il tetto per" "$B_LOG_FUORI" | sed 's/^/        /'
		else
			inf "nessuna riga «scaduto il tetto per»: il server non dichiara"
			inf "di aver fatto scadere nessun tetto in questa fase"
		fi
	else
		inf "⛔ nessun registro da riassumere: $B_LOG_FUORI non c'e'"
		inf "   (volume non mappato? server mai partito? nome cambiato?)"
	fi

	# ⛔ E LO SPEGNIMENTO ENTRA NELL'ESITO — rilievo R12-A.24.  Se il server
	#    non e' morto o la porta non si e' liberata, la fase successiva
	#    misurerebbe uno stato che nessuno ha verificato, e il suo rosso non
	#    sarebbe dei tetti.
	if ! spegni; then
		ko "⛔ la fase «$nome» non ha lasciato la macchina come l'ha trovata"
		if [ "$e" -eq 0 ]; then e=5; fi
	fi
	FATTE="$FATTE $nome"
	# ⛔ Tre esiti diversi dal banco, e si conservano: 1 = il server sbaglia,
	#    3 = il server fa quel che il CODICE dice ma il DOCUMENTO dice
	#    un'altra cosa, 5 = lo stato iniziale non era pulito (B0.3).
	if [ "$e" -ne 0 ]; then
		if [ "$ESITO" -eq 0 ] || [ "$e" -eq 1 ]; then
			ESITO=$e
		fi
	fi
	return "$e"
}

# ⛔⭐ E SE I DUE TETTI COINCIDONO, LE DUE FASI NON SONO INDIPENDENTI.
#     Sul prodotto valgono tutt'e due 30 000 ms, perche' `IDLE_MS` non si
#     sposta: `credenziali-tetto` (sani) e `credenziali-tetto-sotto-il-trasporto`
#     (ping) misurano allora LA STESSA COSA, e contarle come due conferme
#     sarebbe contare due volte la stessa misura.
if [ "$TETTO_SANI" = "$TETTO_PING" ]; then
	log "⛔ Le due fasi contro «$B_NOME» NON sono indipendenti"
	inf "il tetto del trasporto vale $TETTO_SANI ms in tutt'e due: e' IDLE_MS"
	inf "in src/trasporto.c, e nessuna opzione lo tocca."
	inf "⚠ CIAO (5 s) e ATTACCA (10 s) restano puliti — 30 s > 10 s — e i loro"
	inf "  due numeri valgono quanto valevano."
	inf "⛔ CREDENZIALI (60 s) no: 30 s < 60 s, quindi in fase «sani» a tenere"
	inf "  viva la connessione sono gia' i PING, esattamente come in «ping»."
	inf "⭐ Il guadagno: «credenziali-presto», che tace 42 s, diventa una"
	inf "  SECONDA prova dei PING invece di un controllo che passa comunque."
fi

if [ "$AZIONE" = tutto ] || [ "$AZIONE" = sani ]; then
	fase sani "$TETTO_SANI"
fi
if [ "$AZIONE" = tutto ] || [ "$AZIONE" = ping ]; then
	fase ping "$TETTO_PING"
fi

# ---------------------------------------------------------------------------
# ⛔ B0.3 — LA DICHIARAZIONE SULLO SBLOCCO, e adesso e' una dichiarazione VERA.
#
# ⚠ Questa sezione diceva «B6 non chiama il comando di sblocco, e dice perche'»,
#   e la ragione era che il comando «vuole un server acceso con quell'opzione, e
#   B6 accende il proprio senza».  ⭐ Adesso lo accende CON: `bersaglio_accendi`
#   passa sempre `--comando-socket`, e il socket e' di B6 soltanto.
# ⛔ B6 comunque non sblocca niente DENTRO il giro, e non ne ha bisogno: non
#    fallisce mai un'autenticazione.  Qui si dice soltanto che la macchina resta
#    come l'ha trovata, e lo si verifica invece di crederci.
log "B0.3 — che cosa lascia dietro questo giro"
inf "⭐ B6 non ha fallito nessuna autenticazione: nessun conto consumato,"
inf "   nessun ban lasciato addosso a chi viene dopo"
inf "⛔ e il suo file dei ban e' «$B_BAN», che nessun altro banco legge"

log "Esito"
inf "bersaglio: $B_NOME  ·  binario md5 ${B_MD5:-ignota}"
inf "fasi eseguite:${FATTE:- nessuna}"
case "$ESITO" in
0)
	if [ "$AZIONE" = tutto ]; then
		ok "⭐ B6 passa: i tre tetti scadono col motivo giusto, non prima e"
		ok "   non dopo, e i PING di §4.6 reggono sotto un trasporto piu'"
		ok "   corto del protocollo"
	else
		ok "⭐ la fase «$AZIONE» passa"
		inf "⚠ e questo NON e' «B6 passa»: il giro era parziale"
	fi
	;;
3)
	ko "⛔ B6: il filo si comporta come il CODICE dice, ma il DOCUMENTO dice"
	ko "   un'altra cosa.  La cura sta in RCP.md, non nel server — e va"
	ko "   scritta con la data e la fonte (CODER.md §5)."
	;;
4)
	ko "⛔ B6: lo strumento non e' certificato, oppure il server non parte:"
	ko "   niente e' stato misurato"
	;;
5)
	ko "⛔ B6: lo stato iniziale non era quello che serve (B0.1/B0.3), oppure"
	ko "   il tetto del trasporto sul filo non e' quello chiesto (R8.3),"
	ko "   oppure lo spegnimento non e' stato verificato (R12-A.24)."
	ko "   Non e' un rosso dei tetti."
	;;
6)
	# ⛔ IL QUARTO ESITO, E NON E' ZELO — rilievo R12-A.25.  Un caso che il
	#    banco non ha saputo classificare finiva fra le prove che il DOCUMENTO
	#    sbaglia, e usciva 3: la cura veniva mandata in `RCP.md` per un
	#    sintomo che poteva essere del server.
	ko "⛔ B6: un caso ha prodotto un esito che il banco NON SA CLASSIFICARE."
	ko "   Non e' «il server sbaglia» e non e' «il documento sbaglia»: e' una"
	ko "   misura da rifare, e la R3.27 resta aperta."
	;;
*)
	ko "⛔ B6: qualcosa non passa"
	;;
esac
inf "i registri del server: $FUORI/b6-$B_NOME-sani.log e $FUORI/b6-$B_NOME-ping.log"
inf "⭐ e i FATTI di questo giro, uno per riga: $B_ESITI_FUORI"
inf "   (fino all'11 agosto 2026 B6 non aveva nessun registro, e i suoi tre"
inf "    numeri — 5,0 · 60,1 · 10,0 s — non sono riverificabili da nessuno)"
exit "$ESITO"
