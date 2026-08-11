#!/bin/bash
#
# 01-b10-lancia.sh — gira SUL SERVER.  B10: il secondo utente.
#
#   BERSAGLIO=prodotto bash /media/REMOTIX/src/01-b10-lancia.sh elenco
#   BERSAGLIO=prodotto bash /media/REMOTIX/src/01-b10-lancia.sh sano
#   BERSAGLIO=prodotto bash /media/REMOTIX/src/01-b10-lancia.sh guasto
#   BERSAGLIO=prodotto bash /media/REMOTIX/src/01-b10-lancia.sh certifica
#
# ⛔ `BERSAGLIO` e' obbligatoria — `01-b0-bersaglio.sh`, l'unico posto in cui i
#    due server sono descritti.
#
# ---------------------------------------------------------------------------
# ⛔ CHE COSA E' B10, IN UNA RIGA
#
# Un utente **diverso da quello che possiede il processo del server** completa
# la stretta di mano fino a `SESSIONE`.  La misura vera sta in
# `01-b10-secondo-utente.py`, e le quattro cause di «non entra» — con la
# distinzione fra loro, che e' il punto — stanno scritte li'.
#
# ---------------------------------------------------------------------------
# ⛔ L'ISOLAMENTO, sera dell'11 agosto 2026 — cinque agenti sulla stessa macchina
#
# Questo giro nasce con quattro banchi che girano in parallelo sullo stesso
# server, e i pezzi di stato che si pestano i piedi sono tre: la porta, il file
# dei ban e il socket del comando di sblocco.  ⭐ Da cui i valori qui sotto, e
# ⛔ **la porta 7448 non si tocca**: e' il prodotto che gli altri stanno
# misurando, e accendercene un secondo sopra farebbe misurare a loro il nostro
# processo (rilievi R8.15, R12-A.7).
#
#   PORTA         7491   il prodotto SANO, acceso da noi
#   PORTA_GUASTO  7492   la copia guasta, per la certificazione
#   ban           /srv/src/tmp/sera-b10-ban
#   socket        /srv/src/tmp/sera-b10.sock
#
# ⚠ E questo banco AUTENTICA, quindi BANNA (B0.3): fa tentativi falliti, e
#   ogni giro **parte e finisce con lo sblocco dichiarato**, sul proprio file.
#
# ---------------------------------------------------------------------------
# ⛔ LA PAROLA D'ORDINE DI `prova2` NON PASSA DA NESSUNA RIGA DI COMANDO
#
# `fasi/01-filo-nudo.md` la nomina fra i compromessi **non** accettati.  Qui la
# parola:
#
#   · si legge da `/media/REMOTIX/credenziali-banchi` (0600), dove l'ha scritta
#     il provisioning — ⛔ non si genera e non si crea l'utente a mano;
#   · si scrive in un file `0600` con `printf`, che e' un **builtin** della
#     shell: nemmeno la scrittura passa per un processo con la parola in `argv`;
#   · arriva al banco come `--parola-file`, mai come `--parola`;
#   · il file si cancella con `trap`, anche se il giro muore.
#
# ⚠ Resta una copia in chiaro su disco per la durata del giro, ed e' dichiarata:
#   e' il prezzo per non averla in `ps`, dove la vede chiunque.
#
# ---------------------------------------------------------------------------
# ⛔⭐ LA CERTIFICAZIONE, E PERCHE' IL GUASTO NON SI APPLICA AL PRODOTTO VERO
#
# `PIANO.md` §0.3 regola 4: un banco che non e' mai stato visto diventare rosso
# non prova niente.  Il guasto di B10 e' **rimettere la guardia** che rifiuta
# chi non possiede il processo — se B10 resta verde con quella addosso, B10 non
# guarda quel che dice di guardare.
#
# ⛔ Ma costruire il guasto dentro `/srv/src/remotix` vorrebbe dire riscrivere
#    il binario del prodotto **che gli altri banchi stanno misurando in questo
#    momento**, e per qualche minuto lasciare sotto i loro piedi un server
#    bugiardo.  ⭐ Quindi il guasto vive su una **copia intera** dell'albero,
#    `/srv/src/sera-b10-remotix`, con la sua porta — la stessa forma che
#    `01-p1-prodotto.sh` ha adottato la stessa sera per la stessa ragione.
#
# ⚠ E la copia si rifa' PRIMA di ogni giro (`01-b12-guasti.py`,
#   `prepara_copia()`): una copia rimasta da un giro precedente potrebbe
#   portarsi dietro il guasto di quel giro, e il banco partirebbe gia' rosso —
#   cioe' il verde di partenza, che e' meta' della certificazione, sarebbe
#   perso senza che nessuno lo veda.
#
# ⛔ E i sorgenti della copia si confrontano con quelli del prodotto: se non
#    fossero identici, il rosso del giro guasto parlerebbe di un altro
#    programma.
#
# ---------------------------------------------------------------------------
# ⛔ NIENTE REDIREZIONI ATTORNO A `enter.sh`: si redirige DENTRO le virgolette e
#    si legge il file dopo.  Fuori si porta via la richiesta di password di
#    sudo, e lo script resta ad aspettare una domanda che nessuno vede.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
CRED=/media/REMOTIX/credenziali-banchi

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

SIGLA=b10
# shellcheck source=01-b0-bersaglio.sh
. "$FUORI/01-b0-bersaglio.sh"

# ── ⛔ L'isolamento della sera: si sovrascrive quel che il profilo fissa, e lo
#    si DICHIARA.  Un banco che usasse la 7448 misurerebbe il server di un
#    altro agente, o gli spegnerebbe il suo.
PORTA_SANO=${PORTA_SANO:-7491}
PORTA_GUASTO=${PORTA_GUASTO:-7492}
B_PORTA=$PORTA_SANO
B_BAN=$DENTRO/tmp/sera-b10-ban
B_COMANDO=$DENTRO/tmp/sera-b10.sock
COPIA_FUORI=$FUORI/sera-b10-remotix
COPIA_DENTRO=$DENTRO/sera-b10-remotix
PAROLA_FUORI=$FUORI/tmp/sera-b10-parola
PAROLA_DENTRO=$DENTRO/tmp/sera-b10-parola
USCITA_BANCO=$FUORI/01-b10-esiti-$B_NOME.jsonl

AZIONE=${1:-sano}

# ---------------------------------------------------------------------------
# ⛔ Il file della parola, e la sua fine.  `trap` sull'EXIT: se il giro muore a
#    meta', la parola non resta sul disco a ricordo.
ripulisci()
{
	rm -f "$PAROLA_FUORI"
	[ -n "${B_PID:-}" ] && bersaglio_spegni >/dev/null 2>&1
	true
}
trap ripulisci EXIT

# ---------------------------------------------------------------------------
# ⛔⭐ QUANTE VOLTE LA MARCA COMPARE — e i suoi esiti sono TRE, non due.
#
# `grep -c` esce **1** quando non trova niente: non e' un errore, e' la
# risposta «zero».  ⛔ Scritto `$(grep -c … || echo 0)`, quel ramo scatta
# proprio quando il conto e' zero e ci appiccica un secondo zero: la variabile
# vale la stringa «0\n0», e il confronto muore con «integer expression
# expected».  `[M]` 11 agosto 2026, sera: il primo `certifica` di B10 ha
# stampato i tre giri giusti — 0 → 1 → 0, marca 2 nel guasto e 0 nei due sani —
# e poi ⛔ **ha dichiarato B10 NON CERTIFICATO** per questa riga.
#
# ⚠ Ed e' la stessa forma gia' pagata e gia' scritta in `01-b0-terreno.sh`
#   (`conta()`, rilievo A31) e su S1b (rilievo A31 di quel giro): lo stato
#   d'uscita di `grep` va LETTO — 0 trovato · 1 non trovato · ≥2 non ho potuto
#   leggere — e solo il terzo e' «?».
conta_marca() # $1 = file
{
	local n s
	if [ ! -f "$1" ]; then printf '?\n'; return; fi
	n=$(grep -c -F -- 'CAUSA-1-GUARDIA-PRE-PAM' "$1" 2>/dev/null)
	s=$?
	if [ "$s" -ge 2 ] || [ -z "$n" ]; then printf '?\n'; else printf '%s\n' "$n"; fi
}

scrivi_la_parola()
{
	local p
	# ⚠ `sed` legge il file: la parola non compare in nessun `argv`.
	p=$(sed -n 's/^prova2:[[:space:]]*//p' "$CRED" 2>/dev/null | head -1)
	if [ -z "$p" ]; then
		ko "⛔ nessuna parola per «prova2» in $CRED"
		ko "   ⭐ l'utente e la sua parola nascono dal PROVISIONING:"
		ko "     /media/REMOTIX/provision-server.sh (passo 5-bis) — non a mano"
		return 2
	fi
	# ⛔ `umask` IN UNA SOTTOSHELL, e questa riga e' costata il primo giro della
	#    sera dell'11 agosto 2026.  Scritto `umask 077` nudo, il valore resta
	#    per TUTTO il resto dello script — compresi i comandi che
	#    `01-b0-bersaglio.sh` manda dentro il contenitore, che lo ereditano.
	#    ⇒ `b0_binario_e_sorgenti` scriveva il suo file da root con modo 0600,
	#    e poi non riusciva a rileggerlo da `nicfio`: il banco si e' fermato
	#    con «il binario non c'e' o non si legge», cioe' ⛔ **il rosso puntato
	#    sull'imputato sbagliato** — il binario c'era ed era giusto.
	( umask 077; : > "$PAROLA_FUORI" ) || return 2
	chmod 600 "$PAROLA_FUORI"
	# ⛔ `printf` e' un builtin: nessun processo con la parola in argv, quindi
	#    niente in `ps`.
	printf '%s\n' "$p" > "$PAROLA_FUORI"
	ok "la parola di «prova2» e' in $PAROLA_FUORI (0600) — mai in una riga di comando"
	return 0
}

# ---------------------------------------------------------------------------
# Il banco vero, dentro il contenitore.  ⛔ L'uscita si cattura in un file
# (redirezione DENTRO le virgolette) e si stampa qui: serve per cercarci la
# marca del guasto, che e' quel che B12 pretende.
gira_il_banco() # $1 = etichetta
{
	local et=$1 f="$DENTRO/01-b10-uscita-$et.txt" ff="$FUORI/01-b10-uscita-$et.txt"
	rm -f "$ff"
	# ⛔ LA CHIAMATA STA SU UNA RIGA SOLA, e non e' una svista di stile.
	#    `01-b0-chiamate.py` — l'attrezzo che controlla che chi chiama un banco
	#    gli passi quel che pretende — legge **riga per riga** e non unisce le
	#    continuazioni con `\`.  `[M]` 11 agosto 2026: scritta su otto righe,
	#    questa stessa chiamata veniva accusata di essere «SENZA --parola-file,
	#    --pid-server, --porta, --registro-server» — ⛔ un rosso falso dentro
	#    l'attrezzo che esiste per togliere i rossi falsi, e su un giro che era
	#    appena passato verde.  ⚠ Il difetto e' dell'attrezzo e sta scritto nel
	#    rapporto; qui si paga una riga lunga per non lasciarlo acceso.
	bash "$ENTRA" --root \
		"python3 -u $DENTRO/01-b10-secondo-utente.py --bersaglio $B_NOME --indirizzo $B_IND --porta $B_PORTA --utente prova2 --parola-file $PAROLA_DENTRO --utente-controllo prova --pid-server $B_PID --registro-server $B_LOG --servizio-pam remotix --socket-comando $B_COMANDO --indirizzo-client $B_IND --uscita $DENTRO/01-b10-esiti-$B_NOME.jsonl --md5 ${B_MD5:-ignota} --giro ${B_GIRO}-$et > $f 2>&1"
	local stato=$?
	if [ -f "$ff" ]; then
		sed 's/^/    │ /' "$ff"
	else
		ko "⛔ l'uscita del banco NON esiste: non e' il banco che ha taciuto,"
		ko "   e' che non si e' arrivati a lanciarlo"
	fi
	return "$stato"
}

# ---------------------------------------------------------------------------
# Un giro intero contro un server acceso da noi.  ⛔ Parte e finisce con lo
# sblocco dichiarato: questo banco autentica, quindi banna (B0.3).
un_giro() # $1 = etichetta
{
	local et=$1 stato
	log "Il server si accende (porta $B_PORTA)"
	bersaglio_accendi "$et" "$B_IDLE_LUNGO" || return 4
	inf "il comando di sblocco risponde? (PING — il denominatore di B0.3)"
	bersaglio_ping || { ko "⛔ il comando di sblocco non risponde: in fondo non"
	                    ko "   potrei rimettere la macchina a posto"; }
	log "Lo stato iniziale del ban (B0.1, B0.3) — sblocco DICHIARATO"
	bersaglio_sblocca "B10 parte da «nessun ban», e lo dichiara invece di sperarlo"

	log "Il banco"
	gira_il_banco "$et"
	stato=$?

	log "Lo sblocco finale (B0.3) — questo banco ha fatto tentativi FALLITI"
	bersaglio_sblocca "B10 ha respinto di proposito almeno una parola sbagliata"
	log "Ho misurato il server che ho dichiarato?"
	bersaglio_impronta
	bersaglio_spegni
	return "$stato"
}

# ===========================================================================
case "$AZIONE" in
elenco)
	# ⛔ Anche questa su una riga sola: vedi `gira_il_banco`.  ⚠ E i tre
	#    argomenti finti (`/dev/null`, pid 1) ci sono perche' `--elenco` stampa
	#    la previsione e non misura niente: il banco pretende quelle opzioni
	#    sempre, e un'opzione obbligatoria che sparisce in un modo e' il difetto
	#    che `01-b0-chiamate.py` esiste per trovare.
	bash "$ENTRA" --root \
		"python3 $DENTRO/01-b10-secondo-utente.py --bersaglio $B_NOME --porta $B_PORTA --parola-file /dev/null --pid-server 1 --registro-server /dev/null --elenco"
	exit 0
	;;
sano|guasto|certifica) ;;
*)
	ko "⛔ azione «$AZIONE» sconosciuta: elenco · sano · guasto · certifica"
	exit 2
	;;
esac

log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

log "La parola d'ordine del secondo utente"
scrivi_la_parola || exit 2

# ---------------------------------------------------------------------------
# ⛔ IL GIRO SANO — contro il PRODOTTO, il binario che c'e' (non lo ricostruisco:
#    un banco che ricompila quel che misura si toglie il testimone).
giro_sano() # $1 = etichetta (sano · risanato) — ⛔ due giri sani non si
            #      scrivono addosso l'uscita: il terzo giro della
            #      certificazione e' un fatto a se', e va riletto da se'.
{
	local et=${1:-sano}
	B_PORTA=$PORTA_SANO
	B_ESE=$DENTRO/remotix/remotix
	bersaglio_dichiara
	inf "⛔ porta $B_PORTA — la 7448 e' del prodotto degli altri agenti e NON si tocca"
	bersaglio_pronto || return 3
	bersaglio_butta_il_ban
	un_giro "$et"
}

# ---------------------------------------------------------------------------
# ⛔ IL GIRO GUASTO — su una COPIA INTERA dell'albero del prodotto.
giro_guasto()
{
	local n stato
	log "1. La copia dell'albero del prodotto si rifa' DA ZERO"
	inf "⛔ sempre, anche se c'e' gia': una copia di un giro precedente"
	inf "   potrebbe portarsi dietro il guasto di quel giro, e il banco"
	inf "   partirebbe gia' rosso (01-b12-guasti.py, prepara_copia())"
	bash "$ENTRA" --root \
		"rm -rf $COPIA_DENTRO && cp -a $DENTRO/remotix $COPIA_DENTRO && \
		 rm -f $COPIA_DENTRO/remotix $COPIA_DENTRO/*.o && \
		 md5sum $DENTRO/remotix/*.c $DENTRO/remotix/*.h | sed 's|/remotix/|/COPIA/|' > $DENTRO/tmp/sera-b10-md5-orig.txt && \
		 md5sum $COPIA_DENTRO/*.c $COPIA_DENTRO/*.h | sed 's|/sera-b10-remotix/|/COPIA/|' > $DENTRO/tmp/sera-b10-md5-copia.txt && \
		 diff $DENTRO/tmp/sera-b10-md5-orig.txt $DENTRO/tmp/sera-b10-md5-copia.txt" \
		| tail -5
	n=${PIPESTATUS[0]}
	if [ "$n" -ne 0 ]; then
		ko "⛔ la copia NON e' identica ai sorgenti del prodotto (uscita $n):"
		ko "   il rosso di questo giro parlerebbe di un altro programma"
		return 3
	fi
	ok "la copia c'e' e i suoi .c/.h sono identici a quelli del prodotto"

	log "2. Il guasto: si rimette la guardia che rifiuta chi non possiede il processo"
	bash "$ENTRA" --root "python3 $DENTRO/01-b12-guasti.py --applica B10" | tail -12
	n=${PIPESTATUS[0]}
	if [ "$n" -ne 0 ]; then
		ko "⛔ il guasto NON si e' innestato (uscita $n): senza guasto non c'e'"
		ko "   certificazione, e un giro rosso qui sarebbe rosso per altro"
		return 3
	fi

	log "3. Si ricostruisce la copia guasta (⛔ NON il prodotto)"
	inf "GEMELLO=nessuno, e si DICHIARA: la copia guasta diverge apposta da"
	inf "banchi/rcp/autenticazione.c, e il Makefile fermerebbe la costruzione"
	rm -f "$FUORI/01-b10-costruisci.log"
	bash "$ENTRA" --root \
		"GEMELLO=nessuno bash $COPIA_DENTRO/costruisci.sh > $DENTRO/01-b10-costruisci.log 2>&1"
	n=$?
	if [ "$n" -ne 0 ]; then
		ko "⛔ la costruzione della copia guasta e' fallita (uscita $n):"
		tail -20 "$FUORI/01-b10-costruisci.log" 2>/dev/null | sed 's/^/        /'
		return 3
	fi
	ok "costruita: $(grep -c OK "$FUORI/01-b10-costruisci.log" 2>/dev/null) righe OK nel registro di costruzione"
	bash "$ENTRA" --root "grep -c 'REMOTIX B12 GUASTO' $COPIA_DENTRO/autenticazione.c" \
		| sed 's/^/        marche del guasto nel sorgente: /'

	log "4. Il giro col guasto — ⛔ B10 DEVE diventare rosso"
	B_PORTA=$PORTA_GUASTO
	B_ESE=$COPIA_DENTRO/remotix
	B_MD5=""
	bersaglio_dichiara
	b0_binario_e_sorgenti "$COPIA_DENTRO/*.c $COPIA_DENTRO/*.h" || return 3
	bersaglio_butta_il_ban
	un_giro guasto
	stato=$?
	log "5. Si toglie il guasto e si butta la copia"
	bash "$ENTRA" --root "python3 $DENTRO/01-b12-guasti.py --togli B10" | tail -4
	bash "$ENTRA" --root "rm -rf $COPIA_DENTRO"
	inf "⛔ la copia guasta e' sparita: un binario bugiardo dimenticato"
	inf "   avvelenerebbe ogni misura successiva, e nessuno saprebbe che c'era"
	return "$stato"
}

case "$AZIONE" in
sano)
	giro_sano
	STATO=$?
	log "Esito del giro SANO: $STATO (atteso 0)"
	exit "$STATO"
	;;
guasto)
	giro_guasto
	STATO=$?
	log "Esito del giro GUASTO: $STATO (atteso ≠ 0, con la marca)"
	exit "$STATO"
	;;
certifica)
	# ⛔ LA CERTIFICAZIONE E' TRE GIRI, E IL TERZO NON E' UN DI PIU':
	#    sano (0) → guasto (≠0, con la marca) → risanato (0).  Senza il terzo,
	#    «il guasto e' stato tolto» resta una speranza.
	log "⛔ CERTIFICAZIONE DI B10 — sano → guasto → risanato"
	giro_sano sano;      S1=$?
	giro_guasto;         S2=$?
	giro_sano risanato;  S3=$?
	MARCA=$(conta_marca "$FUORI/01-b10-uscita-guasto.txt")
	MARCA_SANO=$(conta_marca "$FUORI/01-b10-uscita-sano.txt")
	MARCA_RIS=$(conta_marca "$FUORI/01-b10-uscita-risanato.txt")
	log "Il verdetto della certificazione (B0.4: lo confronta il banco)"
	inf "giro sano:      $S1  (atteso 0)"
	inf "giro guasto:    $S2  (atteso ≠ 0)"
	inf "giro risanato:  $S3  (atteso 0)"
	inf "marca «CAUSA-1-GUARDIA-PRE-PAM» nel giro guasto:   $MARCA  (attesa ≥ 1)"
	inf "la stessa marca nel giro SANO:                     $MARCA_SANO  (attesa 0)"
	inf "la stessa marca nel giro RISANATO:                 $MARCA_RIS  (attesa 0)"
	if [ "$MARCA" = "?" ] || [ "$MARCA_SANO" = "?" ] || [ "$MARCA_RIS" = "?" ]; then
		ko "⛔ una delle tre uscite non si e' potuta leggere: «non ho potuto"
		ko "   guardare» non e' «la marca non c'e'», e non e' una certificazione"
		exit 1
	fi
	if [ "$S1" -eq 0 ] && [ "$S2" -ne 0 ] && [ "$S3" -eq 0 ] \
	   && [ "$MARCA" -ge 1 ] && [ "$MARCA_SANO" -eq 0 ] \
	   && [ "$MARCA_RIS" -eq 0 ]; then
		ok "⭐ B10 CERTIFICATO: 0 → $S2 → 0, e il rosso porta la marca del guasto"
		exit 0
	fi
	ko "⛔ B10 NON CERTIFICATO — e il motivo e' uno dei numeri qui sopra."
	ko "   ⚠ Un rosso senza la marca e' un rosso di un'altra causa: non conta."
	exit 1
	;;
esac
