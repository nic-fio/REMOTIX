#!/bin/bash
#
# 01-b0-bersaglio.sh — ⛔ LA FORMA UNICA CON CUI B5, B6, B7 E B8 SCELGONO
#                        CONTRO QUALE SERVER MISURANO.
#
#   BERSAGLIO=innesto  bash 01-b5-lancia.sh
#   BERSAGLIO=prodotto bash 01-b5-lancia.sh
#
# ⛔ **OBBLIGATORIA, E SENZA VALORE PREDEFINITO.**  I tre valori leciti sono
#    `innesto`, `prodotto` e `controllo`, ed e' la stessa forma con cui la sonda
#    del trasporto sceglie il proprio bersaglio: due convenzioni diverse per la
#    stessa cosa sono il difetto delle cuciture che la revisione dell'11 agosto
#    2026 ha gia' trovato una volta.  ⚠ Un predefinito qui sarebbe **il modo
#    piu' comodo di misurare il server sbagliato**: chi rilancia un banco a
#    memoria non digita la variabile, e il giro finirebbe contro l'innesto con
#    in testa la parola «prodotto» solo nella testa di chi guarda.
#
# Non e' un banco: e' il pezzo che i quattro banchi hanno in comune, e sta in un
# file solo per una ragione pagata l'11 agosto 2026 (rilievo R12C.5).  La
# finestra di cinque minuti di §4.4-bis era **copiata** in quattro documenti
# invece che rimandata, e le quattro copie non erano uguali: un banco scritto da
# una delle copie sbagliate avrebbe dato rosso sul codice giusto.  ⛔ Quattro
# copie di questo profilo dentro quattro script di lancio sono lo stesso difetto
# con un vestito nuovo — e stavolta sarebbero copie di codice, che divergono
# ancora piu' in fretta di quelle di un documento.
#
# ---------------------------------------------------------------------------
# ⛔⭐ I DUE SERVER, E PERCHE' NON SONO LO STESSO PROGRAMMA
#
#   innesto    `bsslserver`, porta **7447**.  E' il server d'esempio di ngtcp2
#              con dentro `01-b2-ngtcp2-wt-innesta.py` (WebTransport) e
#              `01-b3-rcp-innesta.py` (RCP + il ban lato ospite).  E' quel che
#              tutti i banchi hanno acceso fino all'11 agosto 2026, ed e'
#              l'unico posto in cui certe misure sono gia' state prese: ⛔ non
#              si butta e non si sostituisce.
#
#   prodotto   il binario `remotix` di `src/`, porta **7448**.  E' quel che
#              l'utente installera'.
#
# ⛔ `src/rcp.c` e `banchi/rcp/rcp.c` sono IDENTICI byte per byte (impronta
#    `cb7af778…`, verificata l'11 agosto 2026).  ⚠ Ma **tutto quel che gli sta
#    attorno e' stato scritto due volte, da due mani che non si sono parlate**:
#    lo strato WebTransport, il trasporto, la pagina, il comando di sblocco, il
#    percorso di spegnimento.  E nei punti in cui le due stesure divergono, una
#    porta scritta la dimostrazione che l'altra non funzionava — i commenti di
#    `src/webtransport.c` la citano otto volte, sempre nella forma «nell'innesto
#    questo mancava / qui moriva la connessione».
#
# ⛔⭐ DA CUI IL DOVERE DI QUESTO FILE, e non e' zelo: la prima volta che un
#     banco viene puntato al prodotto **dara' rossi su un server che le cose le
#     fa**.  Il precedente di questo progetto dice che quando un banco e' rosso
#     e il codice sembra funzionare, si cerca nel codice per ore prima di
#     sospettare della misura (`LEZIONI.md` §1.9 punto 3, e la settima veste).
#     Quindi ogni rosso che un banco puo' dare **deve poter dire da solo se
#     accusa il prodotto o accusa la propria gamba**, e le tre cure sono qui:
#
#       1. il bersaglio si DICHIARA e si scrive nel registro di ogni giro;
#       2. il bersaglio si VERIFICA sul filo e nel registro del server —
#          `bersaglio_impronta` —, perche' «l'ho dichiarato» e «e' quello» sono
#          due fatti diversi (`LEZIONI.md` §1.9, corollario 5: un denominatore
#          si legge dove la cosa succede);
#       3. le differenze note fra i due server stanno **in questo file**, in una
#          tabella, e i banchi le leggono invece di scoprirle da capo.
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' UNA VARIABILE D'AMBIENTE, E NON UN ARGOMENTO
#
# I quattro banchi hanno quattro grammatiche di argomenti diverse e gia' piene:
#
#   01-b5-lancia.sh  [tutto|elenco|solo] [filtro]
#   01-b6-lancia.sh  [tutto|sani|ping|elenco]
#   01-b7-lancia.sh  [tutto|elenco|frasi|solo] [filtro]
#   01-b8-lancia.sh  [<numero di blocchi>|previsione|costruisci]
#
# ⛔ Non esiste una posizione libera che voglia dire la stessa cosa in tutt'e
#    quattro, e infilarla in posizioni diverse sarebbe **quattro forme**, cioe'
#    il contrario di quel che serve.  `BERSAGLIO=` sta davanti a tutte e quattro
#    le righe di comando, uguale.
#
# ⚠ E NON si eredita dentro il contenitore: `enter.sh` fa `env -i` e cancella
#   l'ambiente.  Quindi ogni script di lancio la legge QUI, fuori, e la passa ai
#   banchi in Python come `--bersaglio <nome>` sulla riga di comando — dove si
#   vede, invece che come una variabile che qualcuno crede di aver passato.
#
# ---------------------------------------------------------------------------
# ⛔ E UN VALORE SCONOSCIUTO NON RIPIEGA SU «innesto»
#
# `BERSAGLIO=produtto` (con l'errore di battitura) misurerebbe l'innesto
# dichiarando il prodotto, e il registro del giro porterebbe la parola giusta
# sul server sbagliato.  ⭐ Si esce **2**, e si dicono i due valori leciti.
# ---------------------------------------------------------------------------

# ⚠ Questo file si include con `.` o `source`, non si esegue.  Se qualcuno lo
#   lancia da solo, lo dice invece di non fare niente in silenzio.
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	printf '    \033[1;31mNO\033[0m  ⛔ 01-b0-bersaglio.sh non si esegue: si include.\n'
	printf '        SIGLA=b5 . /media/REMOTIX/src/01-b0-bersaglio.sh\n'
	exit 2
fi

# ---------------------------------------------------------------------------
# I posti, e sono gli stessi per tutti i banchi.
B0_ENTRA=/media/REMOTIX/enter.sh
B0_FUORI=/media/REMOTIX/src          # come lo vede il server
B0_DENTRO=/srv/src                   # lo stesso posto, come lo vede il contenitore

# ⛔ La sigla del banco che include questo file: entra nei nomi del file dei
#    ban, del socket di comando e dei registri.  Senza, due banchi diversi si
#    scriverebbero addosso — ed e' il tipo di stato che sopravvive fra un banco
#    e l'altro che B0.2 elenca per primo.
B0_SIGLA=${SIGLA:-b0}

b0_ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
b0_ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
b0_inf() { printf '    --  %s\n' "$*"; }

# ---------------------------------------------------------------------------
# ⛔ IL PROFILO.  Una riga per differenza, e ogni differenza ha una ragione
#    leggibile nel codice dei due server.
# ---------------------------------------------------------------------------
# ⛔ NIENTE `${BERSAGLIO:-innesto}`: la variabile e' obbligatoria.
if [ -z "${BERSAGLIO:-}" ]; then
	b0_ko "⛔ manca BERSAGLIO, e non ho un valore predefinito."
	b0_ko "   I tre valori sono «innesto», «prodotto» e «controllo»:"
	b0_ko "     BERSAGLIO=innesto  bash .../01-${B0_SIGLA}-lancia.sh …"
	b0_ko "     BERSAGLIO=prodotto bash .../01-${B0_SIGLA}-lancia.sh …"
	b0_ko "   ⛔ Un predefinito qui sarebbe il modo piu' comodo di misurare il"
	b0_ko "      server sbagliato: chi rilancia a memoria non digita la"
	b0_ko "      variabile, e il giro finirebbe contro l'innesto con in testa"
	b0_ko "      la parola «prodotto» solo nella testa di chi guarda."
	exit 2
fi
B_NOME=$BERSAGLIO

case "$B_NOME" in
innesto)
	B_PORTA=7447
	B_IND=192.168.0.2
	B_LEGAME=0.0.0.0
	B_INDIRIZZI=127.0.0.1,192.168.0.2
	B_CERT=/media/REMOTIX/b2-certificati      # ⚠ percorso DENTRO il contenitore
	B_ESE="$B0_DENTRO/b2/ngtcp2/build/examples/bsslserver"
	B_LIBS="$B0_DENTRO/b2/ngtcp2/build/lib"
	B_COMM=bsslserver                         # /proc/<pid>/comm atteso
	# ⛔ L'impronta: OGNI riga di registro di questo server comincia per
	#    «REMOTIX B3: » o «REMOTIX B5: » (le mette l'innesto), oppure e' una
	#    riga dell'esempio di ngtcp2.  Basta che ce ne siano.
	B_IMPRONTA='REMOTIX B[35]:'
	B_CONTROLLO='REMOTIX B3'
	# ⭐ Il tetto d'inattivita' del trasporto SI SCEGLIE: l'esempio di ngtcp2
	#    prende `--timeout=Ns`.
	B_IDLE_SCELTA=si
	B_IDLE_LUNGO=120000     # sopra tutti e tre i tetti di §4.6: chiude solo RCP
	B_IDLE_CORTO=15000      # sotto i 60 s delle credenziali: la fase «ping»
	# ⛔ Dove puo' vivere un percorso di spegnimento, per B7.  Il denominatore
	#    si legge DOVE LA COSA SUCCEDE: in `rcp.c` non ci sara' mai, perche'
	#    `rcp.c` non sa che esista un processo.
	B_SORGENTI="$B0_DENTRO/rcp/rcp.c,$B0_DENTRO/01-b3-rcp-innesta.py"
	B_SPEGNIMENTO=no        # ⇒ B7 ha SETTE motivi provocabili
	# Le righe che il ban lato ospite scrive all'avvio (B8 le confronta).
	B_R_BAN_CARICATI='ban caricati:'
	B_R_BAN_ILLEGGIBILE='NON HO POTUTO LEGGERE il file dei ban'
	B_R_COMANDO_VIVO="il comando di sblocco ascolta su"
	B_R_PAGINA='pagina TCP a'
	B_BAN_ILLEGGIBILE_PARTE=si  # l'innesto parte lo stesso e lo scrive
	;;
prodotto)
	B_PORTA=7448
	B_IND=192.168.0.2
	B_LEGAME=0.0.0.0
	B_INDIRIZZI=127.0.0.1,192.168.0.2
	B_CERT="$B0_DENTRO/remotix-cert"
	B_ESE="$B0_DENTRO/remotix/remotix"
	B_LIBS=""
	B_COMM=remotix
	# ⛔ L'impronta del prodotto: `registro.c` scrive «HH:MM:SS.mmm <area> …»,
	#    con l'area fra avvio·quic·wt·rcp·pagina·cert.  Nessuna riga porta
	#    «REMOTIX B3», e nessuna riga dell'innesto porta questa forma: le due
	#    impronte si escludono a vicenda, ed e' quel che le rende utili.
	B_IMPRONTA='^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]\.[0-9][0-9][0-9] (avvio|quic|wt|rcp|pagina|cert) '
	B_CONTROLLO='REMOTIX_V2 — fase 1, il filo nudo'
	# ⛔ IL TETTO D'INATTIVITA' NON SI SCEGLIE: `src/trasporto.c` ha
	#    `#define IDLE_MS 30000` e nessuna opzione lo tocca (verificato col
	#    grep l'11 agosto 2026: nessun `getenv` in tutto `src/`).  ⚠ Chiedere
	#    120 s al prodotto e' una richiesta che NON si puo' esaudire, e
	#    `bersaglio_accendi` si rifiuta invece di accendere qualcosa di diverso
	#    da quel che gli e' stato chiesto (`CODER.md` §3.9: se non obbedisce,
	#    dichiara il fallimento, non ripiegare in silenzio).
	B_IDLE_SCELTA=no
	B_IDLE_LUNGO=30000
	B_IDLE_CORTO=30000
	# ⛔ Il percorso di spegnimento del prodotto NON sta in `rcp.c`: sta in
	#    `main.c` (che congeda tutti prima di uscire), in `trasporto.c`
	#    (`trasporto_congeda_tutte`) e in `webtransport.c` (`wt_congeda`).
	#    Cercarlo in `rcp.c` — che e' identico nei due server — direbbe «zero»
	#    su tutt'e due i bersagli, ed e' un denominatore letto dove la cosa NON
	#    succede.
	B_SORGENTI="$B0_DENTRO/remotix/rcp.c,$B0_DENTRO/remotix/main.c,$B0_DENTRO/remotix/trasporto.c,$B0_DENTRO/remotix/webtransport.c"
	B_SPEGNIMENTO=si        # ⇒ B7 ha OTTO motivi provocabili
	B_R_BAN_CARICATI='indirizzi caricati'
	B_R_BAN_ILLEGGIBILE="c'e' e NON si e' potuto leggere"
	B_R_COMANDO_VIVO="il comando di sblocco ascolta su"
	B_R_PAGINA='ascolto TCP su'
	# ⛔⭐ E QUI I DUE SERVER FANNO DUE COSE OPPOSTE: se il file dei ban c'e' e
	#     non si legge, il prodotto **NON PARTE** (`src/main.c`: «non e' «zero
	#     ban», e' la protezione di §4.4-bis spenta.  Non si parte.»), mentre
	#     l'innesto parte e lo scrive.  ⚠ Quindi su questo bersaglio quel caso
	#     non si osserva come «una riga nel registro»: si osserva come «il
	#     server non si e' acceso», e un banco che cercasse la riga darebbe
	#     rosso su un server che fa **di piu'** di quel che gli si chiede.
	B_BAN_ILLEGGIBILE_PARTE=no
	;;
controllo)
	# ⛔ IL TERZO VALORE ESISTE NELLA GRAMMATICA E NON IN QUESTI QUATTRO
	#    BANCHI — e lo si dice, invece di farlo cadere su «innesto».
	#
	# `controllo` e' il bersaglio che DEVE far diventare rosso il banco: il
	# server guasto di proposito, cioe' la certificazione di `LEZIONI.md` §1.2
	# fatta su un processo intero invece che su un fatto costruito a mano.  Per
	# B5, B6, B7 e B8 quel server oggi **non esiste**: `01-b11-guasto-innesta.py`
	# guasta il server verso la PAGINA (B11), non verso il filo, e B8 la propria
	# certificazione la fa altrove (`--certifica`, su fatti costruiti a mano).
	#
	# ⚠ Scriverlo qui, e uscire 2, e' la differenza fra «non c'e'» e «c'e' e non
	#   fa niente»: chi lancia `BERSAGLIO=controllo` deve leggere una riga, non
	#   ottenere un verde dell'innesto.
	b0_ko "⛔ BERSAGLIO=controllo: la grammatica lo prevede, questi quattro"
	b0_ko "   banchi non ce l'hanno ancora."
	b0_ko "   Sarebbe il server GUASTO DI PROPOSITO, quello contro cui il banco"
	b0_ko "   deve diventare rosso (LEZIONI.md §1.2).  Oggi esiste solo verso la"
	b0_ko "   pagina (01-b11-guasto-innesta.py), non verso il filo."
	b0_ko "   ⛔ E non ripiego su «innesto»: un controllo che in realta' misura"
	b0_ko "      il caso sano e' peggio di un controllo assente, perche' stampa"
	b0_ko "      un verde."
	exit 2
	;;
*)
	b0_ko "⛔ BERSAGLIO=«$B_NOME» non esiste."
	b0_ko "   I tre valori sono «innesto», «prodotto» e «controllo»."
	b0_ko "   ⛔ E non ripiego su nessuno: misurerei un server dichiarandone un"
	b0_ko "      altro, e il registro del giro porterebbe la parola giusta sul"
	b0_ko "      server sbagliato."
	exit 2
	;;
esac

# ⛔ Uno per banco, e per BERSAGLIO.  Due banchi non condividono mai un file dei
#    ban ne' un socket: il conto di §4.4-bis vive nel processo che serve, e
#    dargliene uno per banco e' l'unico isolamento che non dipenda da chi si
#    ricorda di sbloccare.  ⚠ E va DICHIARATO, perche' cambia che cosa vuol dire
#    un verde di B0.3: in produzione il file e' uno solo.
B_BAN="$B0_DENTRO/${B0_SIGLA}-${B_NOME}-ban.txt"
B_COMANDO="$B0_DENTRO/${B0_SIGLA}-${B_NOME}-comando.sock"
# Il registro dei fatti del banco, uno per bersaglio: due giri contro due server
# diversi non finiscono mai nello stesso file, e ogni riga lo ripete comunque.
B_ESITI="$B0_DENTRO/${B0_SIGLA}-esiti-${B_NOME}.jsonl"
B_ESITI_FUORI="$B0_FUORI/${B0_SIGLA}-esiti-${B_NOME}.jsonl"

B_PID=""
B_LOG=""
B_LOG_FUORI=""
# ⛔ L'impronta md5 del binario MISURATO, e l'ora sua e del sorgente piu'
#    recente.  Le riempie `bersaglio_pronto`, e finiscono nel registro di ogni
#    giro: `LEZIONI.md` §1.9 ottava veste — «il file c'e'» e «il file e' quello
#    che ho appena costruito» sono due domande diverse, e un binario di ieri
#    risponde «si'» alla prima.  ⚠ `[M]` 11 agosto 2026: il binario del prodotto
#    sul server era delle 21:08 e `trasporto.c` delle 22:10, e il registro
#    dell'ultima accensione portava una formulazione di DUE generazioni prima.
B_MD5=""
B_BIN_QUANDO=""
B_SORG_PIU_RECENTE=""
# L'identificatore del giro: lo stesso per tutte le righe del registro, e per
# tutti i programmi che questo giro lancia.
B_GIRO=$(date +%Y%m%d-%H%M%S)

# ---------------------------------------------------------------------------
# ⛔ LA DICHIARAZIONE, e va stampata PRIMA di qualunque numero.
bersaglio_dichiara()
{
	printf '\n\033[1m== Il bersaglio\033[0m\n'
	b0_ok "BERSAGLIO=$B_NOME  ·  $B_ESE  ·  porta $B_PORTA"
	b0_inf "ban: $B_BAN"
	b0_inf "comando di sblocco: $B_COMANDO"
	b0_inf "registro dei fatti: $B_ESITI_FUORI"
	b0_inf "tetto d'inattivita' del trasporto: ${B_IDLE_LUNGO} ms$(
		[ "$B_IDLE_SCELTA" = no ] && printf ' ⛔ NON SCELTO DA NOI (IDLE_MS in trasporto.c)')"
	b0_inf "percorso di spegnimento (SERVER_IN_CHIUSURA 0x0C): $B_SPEGNIMENTO"
	b0_inf "impronta md5 del binario: ${B_MD5:-⛔ non ancora presa}"
	b0_inf "binario del $(date -d "@${B_BIN_QUANDO:-0}" '+%d %b %H:%M:%S' 2>/dev/null || echo '—')\
 · sorgente piu' recente: ${B_SORG_PIU_RECENTE:-—}"
	if [ "$B_NOME" = prodotto ]; then
		b0_inf "⚠ e' la prima volta che questo banco misura il prodotto: un rosso"
		b0_inf "  qui sotto va letto prima come «la mia gamba non regge sul"
		b0_inf "  bersaglio nuovo» e poi come «il prodotto sbaglia» (LEZIONI.md"
		b0_inf "  §1.9 punto 3).  Le differenze gia' note stanno in"
		b0_inf "  01-b0-bersaglio.sh e nella previsione di ogni banco."
	fi
}

# ---------------------------------------------------------------------------
# ⛔ CHI TIENE LA PORTA — e «non si sa» non si arrotonda a «libera».
#
# Preso da `01-b6-lancia.sh` (rilievi R12-A.7 e R12-A.23), che e' la stesura
# piu' forte delle quattro: il comando remoto stampa da se' il proprio stato
# d'uscita, e c'e' il controllo positivo dello strumento — `ss` stampa sempre
# almeno la propria intestazione, e se non stampa niente non ha guardato niente.
#
# ⛔ E si guardano UDP **e** TCP: tutt'e due i server ascoltano sulla stessa
#    porta con due protocolli (`RCP.md` §2.4), e un banco che guardasse solo
#    l'UDP direbbe «libera» con la pagina di un altro giro ancora in ascolto.
B0_USCITA=""
b0_dentro() # $1 = comando remoto.  Uscita in $B0_USCITA, stato = quello del comando
{
	local tutto stato
	tutto=$(bash "$B0_ENTRA" --root "$1"'; printf "\nB0-FINE=%s\n" $?')
	stato=$(printf '%s\n' "$tutto" | sed -n 's/^B0-FINE=\([0-9][0-9]*\)$/\1/p' | tail -1)
	B0_USCITA=$(printf '%s\n' "$tutto" | grep -v '^B0-FINE=')
	if [ -z "$stato" ]; then
		return 125   # non e' arrivato in fondo: non e' uno zero
	fi
	return "$stato"
}

B_CHI=""
bersaglio_porta() # 0 = occupata ($B_CHI) · 1 = libera · 2 = non si sa
{
	local st
	b0_dentro "ss -ulnp; ss -tlnp"
	st=$?
	if [ "$st" -ne 0 ]; then
		b0_ko "⛔ «ss» non ha risposto dentro il contenitore (uscita $st):"
		printf '%s\n' "$B0_USCITA" | tail -5 | sed 's/^/        /'
		return 2
	fi
	if [ -z "$B0_USCITA" ]; then
		b0_ko "⛔ «ss» non ha stampato NIENTE, nemmeno l'intestazione:"
		b0_ko "   lo strumento e' muto, e il suo silenzio non e' una porta libera"
		return 2
	fi
	B_CHI=$(printf '%s\n' "$B0_USCITA" | grep ":$B_PORTA ")
	[ -n "$B_CHI" ]
}

# ---------------------------------------------------------------------------
# ⛔ IL BINARIO CHE STO PER ACCENDERE E' QUELLO CHE CREDO? — `LEZIONI.md` §1.9,
#    ottava veste: «il file c'e'» e «il file e' quello che ho appena costruito»
#    sono due domande diverse, e un binario di ieri risponde «si'» alla prima.
#
# ⚠ Le due strade sono diverse apposta:
#     innesto   gli innesti si tolgono e si rimettono, si CONTA la marca nei
#               due sorgenti, e poi si compila guardando l'esito del
#               costruttore;
#     prodotto  ⛔ QUESTO FILE NON COMPILA IL PRODOTTO.  `src/` non e' di
#               nessun banco, e un banco che ricompila quel che misura si
#               toglie il testimone indipendente.  Si VERIFICA soltanto — il
#               binario c'e', ed e' piu' recente di ogni `.c` — e se non lo e'
#               si dice come rifarlo e ci si ferma.
#
# ⛔⭐ E LA VERIFICA VERA E' UNA SOLA, PER TUTT'E DUE I BERSAGLI:
#     l'impronta md5 del binario, la sua ora, e l'ora del sorgente piu' recente.
#     Se il binario e' piu' vecchio, **non si misura**.
#
#     `[M]` 11 agosto 2026 — e non e' un'ipotesi: il binario del prodotto sul
#     server era delle 21:08 e `trasporto.c` delle 22:10.  Il registro
#     dell'ultima accensione portava una formulazione di **due generazioni
#     prima**, e chiunque avesse misurato quel processo avrebbe attribuito al
#     codice di stanotte il comportamento di ieri sera.
b0_binario_e_sorgenti() # $1 = elenco di glob dei sorgenti, gia' quotato per la shell remota
{
	local glob=$1 f="$B0_FUORI/${B0_SIGLA}-${B_NOME}-binario.txt"
	rm -f "$f"
	bash "$B0_ENTRA" --root \
		"{ md5sum $B_ESE 2>/dev/null | cut -d' ' -f1 || echo x; \
		   stat -c %Y $B_ESE 2>/dev/null || echo x; \
		   ls -t $glob 2>/dev/null | head -1; \
		   stat -c %Y \$(ls -t $glob 2>/dev/null | head -1) 2>/dev/null || echo x; \
		 } > $B0_DENTRO/${B0_SIGLA}-${B_NOME}-binario.txt 2>&1"
	if [ ! -f "$f" ]; then
		b0_ko "⛔ non ho potuto guardare il binario: il file non e' stato"
		b0_ko "   scritto.  Non e' «e' vecchio», e' che non si e' guardato"
		return 3
	fi
	B_MD5=$(sed -n 1p "$f")
	B_BIN_QUANDO=$(sed -n 2p "$f")
	B_SORG_PIU_RECENTE=$(sed -n 3p "$f")
	local t_src
	t_src=$(sed -n 4p "$f")
	case "$B_MD5" in
	''|*[!0-9a-f]*)
		b0_ko "⛔ il binario «$B_ESE» non c'e' o non si legge:"
		sed 's/^/        /' "$f"
		return 3 ;;
	esac
	case "$B_BIN_QUANDO" in
	''|*[!0-9]*) b0_ko "⛔ non ho potuto leggere l'ora del binario"; return 3 ;;
	esac
	case "$t_src" in
	''|*[!0-9]*)
		b0_ko "⛔ non ho potuto leggere l'ora del sorgente piu' recente."
		b0_ko "   ⛔ E questo NON e' «il binario e' aggiornato»: e' che non l'ho"
		b0_ko "      potuto sapere (LEZIONI.md §1.9 regola 1)"
		return 3 ;;
	esac
	if [ "$B_BIN_QUANDO" -lt "$t_src" ]; then
		b0_ko "⛔ IL BINARIO E' PIU' VECCHIO DEL SORGENTE «$B_SORG_PIU_RECENTE»."
		b0_ko "   Dentro non c'e' quel che si legge nel .c, e ogni rosso di"
		b0_ko "   questo giro accuserebbe codice che il server non ha mai"
		b0_ko "   eseguito.  ⛔ Non misuro."
		if [ "$B_NOME" = prodotto ]; then
			b0_ko "   Si rifa' con:"
			b0_ko "     bash $B0_ENTRA --root \"bash $B0_DENTRO/remotix/costruisci.sh\""
		else
			b0_ko "   Si rifa' rilanciando questo stesso banco: l'innesto si"
			b0_ko "   ricompila da se' (ma qui la compilazione e' gia' passata,"
			b0_ko "   quindi guarda se qualcuno tiene un binario vecchio)"
		fi
		return 3
	fi
	b0_ok "binario verificato: md5 ${B_MD5:0:12}… · piu' recente di ogni"\
"sorgente (il piu' recente e' «$B_SORG_PIU_RECENTE»)"
	return 0
}

bersaglio_pronto()
{
	if [ "$B_NOME" = innesto ]; then
		local sorg="$B0_DENTRO/b2/ngtcp2/examples/http3_server_proto_codec.cc"
		local main="$B0_DENTRO/b2/ngtcp2/examples/server.cc"
		printf '\n\033[1m== Il server dell'\''innesto si rimette e si ricompila\033[0m\n'
		b0_inf "⛔ gli innesti si TOLGONO e si rimettono: applicarne uno sopra"
		b0_inf "   l'altro lascerebbe due copie dello stesso codice"
		bash "$B0_ENTRA" --root "python3 $B0_DENTRO/01-b3-rcp-innesta.py --togli > /dev/null"
		bash "$B0_ENTRA" --root "python3 $B0_DENTRO/01-b2-ngtcp2-wt-innesta.py --togli > /dev/null"
		bash "$B0_ENTRA" --root "python3 $B0_DENTRO/01-b2-ngtcp2-wt-innesta.py" \
			| grep -E "appiglio|righe|CODICE" | sed 's/^/        /'
		bash "$B0_ENTRA" --root "python3 $B0_DENTRO/01-b3-rcp-innesta.py" \
			| grep -E "appiglio|NO |file nostri" | sed 's/^/        /'
		local q o
		q=$(bash "$B0_ENTRA" --root "grep -c 'REMOTIX B3' $sorg" | tr -cd '0-9')
		o=$(bash "$B0_ENTRA" --root "grep -c 'REMOTIX B3' $main" | tr -cd '0-9')
		if [ "${q:-0}" -lt 3 ]; then
			b0_ko "⛔ lo strato RCP NON e' nel codec (righe «REMOTIX B3»: ${q:-0})"
			return 3
		fi
		if [ "${o:-0}" -lt 5 ]; then
			b0_ko "⛔ il ban lato ospite NON e' in server.cc (righe: ${o:-0}):"
			b0_ko "   niente pagina in TCP e niente comando di sblocco"
			return 3
		fi
		b0_ok "l'innesto e' nei due file (codec $q righe · ospite $o)"
		rm -f "$B0_FUORI/${B0_SIGLA}-compila.log"
		if ! bash "$B0_ENTRA" --root \
			"ninja -C $B0_DENTRO/b2/ngtcp2/build bsslserver > $B0_DENTRO/${B0_SIGLA}-compila.log 2>&1"; then
			b0_ko "la compilazione e' fallita:"
			if [ -f "$B0_FUORI/${B0_SIGLA}-compila.log" ]; then
				tail -25 "$B0_FUORI/${B0_SIGLA}-compila.log" | sed 's/^/        /'
			else
				b0_ko "   ⛔ e il registro di compilazione NON ESISTE: non e'"
				b0_ko "      ninja che ha taciuto, e' che non si e' arrivati a"
				b0_ko "      lanciarlo"
			fi
			return 3
		fi
		b0_ok "compilato"
		# ⛔ E anche qui si guarda l'esito del COSTRUTTORE e poi il binario:
		#    `ninja` puo' uscire 0 senza aver rifatto niente, e i sorgenti
		#    innestati sono appena cambiati.
		b0_binario_e_sorgenti \
			"$B0_DENTRO/b2/ngtcp2/examples/*.cc $B0_DENTRO/b2/ngtcp2/examples/*.c $B0_DENTRO/rcp/rcp.c" \
			|| return 3
		return 0
	fi

	# ── il prodotto ────────────────────────────────────────────────────────
	printf '\n\033[1m== Il prodotto — si VERIFICA, non si ricompila\033[0m\n'
	b0_inf "⛔ un banco che ricompila quel che misura si toglie il testimone"
	b0_inf "   indipendente: qui si guarda soltanto il binario, e se non e' piu'"
	b0_inf "   recente dei sorgenti ci si ferma"
	b0_binario_e_sorgenti "$B0_DENTRO/remotix/*.c $B0_DENTRO/remotix/*.h" || return 3
	return 0
}

# ---------------------------------------------------------------------------
# ⛔ L'ACCENSIONE.  Una forma sola, due comandi diversi — e il banco chiede il
#    tetto d'inattivita' che gli serve, non quello che il bersaglio gli concede.
#
#   bersaglio_accendi <etichetta> <idle_ms> [opzioni in piu']
#
# ⛔ Se il bersaglio non puo' esaudire la richiesta, NON accende: esce 5.  Un
#    server acceso con un tetto diverso da quello chiesto misurerebbe un'altra
#    cosa sotto la stessa etichetta — `CODER.md` §3.9, forma E2.
bersaglio_accendi()
{
	local et=$1 idle=$2
	shift 2
	B_LOG="$B0_DENTRO/${B0_SIGLA}-${B_NOME}-${et}.log"
	B_LOG_FUORI="$B0_FUORI/${B0_SIGLA}-${B_NOME}-${et}.log"
	rm -f "$B_LOG_FUORI" "$B0_FUORI/${B0_SIGLA}-${B_NOME}-${et}.pid"

	if [ "$B_IDLE_SCELTA" = no ] && [ "$idle" != "$B_IDLE_LUNGO" ]; then
		b0_ko "⛔ il bersaglio «$B_NOME» NON sa accendere con un tetto"
		b0_ko "   d'inattivita' di $idle ms: `IDLE_MS` in src/trasporto.c e'"
		b0_ko "   $B_IDLE_LUNGO ms e nessuna opzione lo tocca."
		b0_ko "   ⛔ E non accendo lo stesso dichiarando $idle: sarebbe misurare"
		b0_ko "      una cosa sotto l'etichetta di un'altra (CODER.md §3.9)."
		b0_ko "   Il banco deve chiedere \$B_IDLE_LUNGO / \$B_IDLE_CORTO, che su"
		b0_ko "   questo bersaglio valgono tutt'e due $B_IDLE_LUNGO."
		return 5
	fi

	# ⛔ E LA PORTA SI GUARDA PRIMA DI OGNI ACCENSIONE, non una volta all'inizio
	#    del banco: fra la prima fase e la seconda ci sta un altro server.
	#    ⚠ «Non si sa» non si arrotonda a «libera»: un secondo server sopra il
	#      primo misurerebbe il server di un altro giro, e il rosso finirebbe
	#      sull'imputato sbagliato (rilievi R8.15, R12-A.7, R12-A.23).
	bersaglio_porta
	case $? in
	0)	b0_ko "⛔ la porta $B_PORTA e' GIA' OCCUPATA: non accendo niente."
		printf '%s\n' "$B_CHI" | sed 's/^/        /'
		b0_ko "   fermalo per PID (mai con pkill -f) e rilancia"
		return 5 ;;
	1)	: ;;
	*)	b0_ko "⛔ non si e' potuto sapere chi tiene la porta $B_PORTA, e «non si"
		b0_ko "   sa» non si arrotonda a «libera»: non accendo"
		return 5 ;;
	esac

	local ts=$((idle / 1000))
	if [ "$B_NOME" = innesto ]; then
		bash "$B0_ENTRA" --root \
			"nohup env LD_LIBRARY_PATH=$B_LIBS $B_ESE --timeout=${ts}s --ban-file=$B_BAN --comando-socket=$B_COMANDO $* $B_LEGAME $B_PORTA $B_CERT/sessione.key $B_CERT/sessione.pem < /dev/null > $B_LOG 2>&1 & echo \$! > $B0_DENTRO/${B0_SIGLA}-${B_NOME}-${et}.pid"
	else
		bash "$B0_ENTRA" --root \
			"nohup $B_ESE --indirizzo $B_LEGAME --nome $B_IND --porta $B_PORTA --certificati $B_CERT --pagina $B0_DENTRO/remotix/pagina.html --ban-file $B_BAN --comando-socket $B_COMANDO $* < /dev/null > $B_LOG 2>&1 & echo \$! > $B0_DENTRO/${B0_SIGLA}-${B_NOME}-${et}.pid"
	fi
	sleep 2
	B_PID=$(cat "$B0_FUORI/${B0_SIGLA}-${B_NOME}-${et}.pid" 2>/dev/null)
	# ⛔ `/proc`, non `kill -0`: il server e' di root e questo script no, e da
	#    utente normale `kill -0` risponde «operazione non permessa», che non e'
	#    «non esiste» (LEZIONI.md §1.9, sesta veste).
	if [ -z "$B_PID" ] || [ ! -d "/proc/$B_PID" ]; then
		b0_ko "⛔ il server «$B_NOME» non e' partito.  Il registro dice:"
		if [ -f "$B_LOG_FUORI" ]; then
			tail -20 "$B_LOG_FUORI" | sed 's/^/        /'
		else
			b0_ko "   ⛔ e il registro NON ESISTE: non e' il server che ha"
			b0_ko "      taciuto, e' che non si e' arrivati a lanciarlo"
		fi
		if [ "$B_NOME" = prodotto ] && [ "$B_BAN_ILLEGGIBILE_PARTE" = no ]; then
			b0_inf "⚠ e su questo bersaglio «non parte» ha una causa in piu' che"
			b0_inf "  l'innesto non ha: se «$B_BAN» c'e' e non si legge, il"
			b0_inf "  prodotto RIFIUTA di partire apposta (src/main.c).  Guarda"
			b0_inf "  la riga «NON si e' potuto leggere» qui sopra prima di"
			b0_inf "  cercare altrove"
		fi
		return 4
	fi
	b0_ok "acceso «$B_NOME» (PID $B_PID · porta $B_PORTA · tetto ${ts}s) — registro $B_LOG_FUORI"
	return 0
}

# ---------------------------------------------------------------------------
# ⛔ LO SPEGNIMENTO NON E' MANDARE UN `kill` — rilievo R12-A.24.  Fra la morte
#    del processo e il rilascio della porta passa un istante che, se non si
#    aspetta, fa trovare alla fase dopo una porta ancora tenuta e le fa dare la
#    colpa a se stessa.
#
# ⚠ E per il prodotto vale doppio: `SIGTERM` non e' la fine, e' l'INIZIO di un
#   percorso — `main.c` congeda tutte le sessioni con `SERVER_IN_CHIUSURA` e
#   aspetta fino a due secondi che i byte escano.  Un banco che si aspettasse la
#   morte immediata leggerebbe «non muore» dove c'e' un server che sta facendo
#   il suo mestiere.
bersaglio_spegni()
{
	local giri=0
	[ -n "${B_PID:-}" ] || return 0
	bash "$B0_ENTRA" --root "kill $B_PID 2>/dev/null || true"
	while [ -d "/proc/$B_PID" ] && [ "$giri" -lt 20 ]; do
		sleep 0.5
		giri=$((giri + 1))
	done
	if [ -d "/proc/$B_PID" ]; then
		b0_ko "⛔ il processo $B_PID e' ancora vivo dopo 10 s"
		B_PID=""
		return 1
	fi
	b0_inf "il processo $B_PID e' sparito (dopo $giri mezzi secondi)"
	B_PID=""
	bersaglio_porta
	case $? in
	0)	b0_ko "⛔ la porta $B_PORTA e' ancora tenuta dopo lo spegnimento:"
		printf '%s\n' "$B_CHI" | sed 's/^/        /'
		return 1 ;;
	1)	b0_inf "la porta $B_PORTA e' libera di nuovo" ; return 0 ;;
	*)	b0_ko "⛔ non si e' potuto sapere se la porta $B_PORTA si e' liberata"
		return 1 ;;
	esac
}

# ---------------------------------------------------------------------------
# ⛔⭐ L'IMPRONTA: HO MISURATO IL SERVER CHE HO DICHIARATO?
#
# `LEZIONI.md` §1.9, corollario 5: *un denominatore si legge dove la cosa
# succede — sul filo, non nella configurazione; nel processo, non
# nell'intenzione.*  ⛔ E il caso concreto che questa funzione impedisce e' gia'
# successo in casa: la sonda SNI di B2 dichiarava `server_name spedito:
# '192.168.0.2'` leggendolo dalla CONFIGURAZIONE, e sul filo non andava niente.
#
# Qui l'analogo sarebbe: `BERSAGLIO=prodotto` con la porta 7448 gia' tenuta da
# un innesto di un giro precedente, oppure un binario `remotix` che non e'
# partito e un `bsslserver` di ieri ancora in ascolto.  Il registro del server
# lo dice in una riga, e le due impronte si escludono a vicenda.
#
#   bersaglio_impronta   0 = e' lui · 1 = e' l'ALTRO · 2 = non si e' potuto dire
bersaglio_impronta()
{
	local mie altrui altra
	if [ ! -f "$B_LOG_FUORI" ]; then
		b0_ko "⛔ il registro del server non si legge ($B_LOG_FUORI):"
		b0_ko "   non e' «il server non ha scritto niente», e' che non si guarda"
		return 2
	fi
	altra='REMOTIX B[35]:'
	[ "$B_NOME" = innesto ] && \
		altra='^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]\.[0-9][0-9][0-9] (avvio|quic|wt|rcp|pagina|cert) '
	mie=$(grep -cE "$B_IMPRONTA" "$B_LOG_FUORI")
	altrui=$(grep -cE "$altra" "$B_LOG_FUORI")
	if [ "${mie:-0}" -eq 0 ] && [ "${altrui:-0}" -eq 0 ]; then
		b0_ko "⛔ il registro non porta NESSUNA delle due impronte:"
		b0_ko "   ne' quella di «$B_NOME» ne' quella dell'altro server."
		b0_ko "   ⛔ E' il caso in cui non si sa che cosa si e' misurato, che non"
		b0_ko "      e' «e' quello giusto»: mi fermo prima dei numeri."
		tail -5 "$B_LOG_FUORI" | sed 's/^/        /'
		return 2
	fi
	if [ "${altrui:-0}" -gt 0 ] && [ "${mie:-0}" -eq 0 ]; then
		b0_ko "⛔⭐ HO DICHIARATO «$B_NOME» E IL REGISTRO E' DELL'ALTRO SERVER"
		b0_ko "   ($altrui righe con l'impronta altrui, 0 con la mia)."
		b0_ko "   ⛔ Ogni numero di questo giro sarebbe attribuito al bersaglio"
		b0_ko "      sbagliato: mi fermo qui.  Guarda chi tiene la porta $B_PORTA."
		return 1
	fi
	# ⭐ E il controllo positivo, sullo stesso strumento: la riga d'avvio che
	#    quel server scrive di sicuro.  Senza, «ho trovato la mia impronta»
	#    potrebbe essere un file di un giro precedente rimasto li'.
	if ! grep -qF "$B_CONTROLLO" "$B_LOG_FUORI"; then
		b0_ko "⛔ l'impronta c'e' ($mie righe) ma la riga d'avvio «$B_CONTROLLO»"
		b0_ko "   NON c'e': questo registro puo' essere di un giro precedente."
		b0_ko "   ⛔ Il controllo positivo esiste apposta (LEZIONI.md §1.9,"
		b0_ko "      seconda regola): senza, il mio «l'ho riconosciuto» non vale"
		return 2
	fi
	b0_ok "⭐ il registro e' di «$B_NOME»: $mie righe con la sua impronta, "\
"$altrui con quella dell'altro, e la riga d'avvio c'e'"
	return 0
}

# ---------------------------------------------------------------------------
# ⛔ LO SBLOCCO, E LA SUA DICHIARAZIONE — regola B0.3.
#
# *«Ogni banco che lo chiama lo dichiara, o "il ban non e' scattato" e "qualcuno
# l'ha tolto" hanno lo stesso aspetto.»*  ⛔ E il `PING` **e' il denominatore di
# questa regola**: senza, «il ban non e' scattato» e «lo sblocco non e' mai
# arrivato a nessuno» hanno di nuovo la stessa faccia.
#
#   bersaglio_ping                       il comando c'e' e risponde?
#   bersaglio_sblocca <perche> [ind…]    toglie, e stampa quale dei tre esiti
#
# ⛔ MAI DENTRO IL GIRO DEL BAN DI B8 (B0.3): li' lo sblocco non e' un attrezzo,
#    e' la cosa provata, e chiamarlo prima farebbe passare tutto il resto per
#    costruzione.  Questa funzione non lo sa: lo sa chi la chiama, ed e' per
#    questo che `<perche>` e' obbligatorio e finisce stampato.
bersaglio_ping()
{
	bash "$B0_ENTRA" --root \
		"python3 $B0_DENTRO/01-b8-sblocca.py --socket $B_COMANDO --ping"
}

bersaglio_sblocca() # $1 = perche' · $2… = indirizzi (predefinito: $B_INDIRIZZI)
{
	local perche=$1
	shift
	local elenco=${*:-}
	[ -n "$elenco" ] || elenco=$(printf '%s' "$B_INDIRIZZI" | tr ',' ' ')
	local ind esito=0
	for ind in $elenco; do
		printf '    --  sblocco «%s» (perche: %s):\n' "$ind" "$perche"
		bash "$B0_ENTRA" --root \
			"python3 $B0_DENTRO/01-b8-sblocca.py --socket $B_COMANDO $ind" \
			|| esito=$?
	done
	return "$esito"
}

# ⛔ Lo stato iniziale del ban si dichiara E si verifica — B0.1 e B0.2, dove il
#    file dei ban e' «lo stato che sopravvive di piu' fra tutti, al riavvio del
#    server compreso».  Un ban di ieri renderebbe rosso tutto quel che segue, e
#    il rosso finirebbe sull'imputato sbagliato.
# ⚠ E' un banco: in produzione buttare quel file e' togliere la protezione a
#   tutti.
bersaglio_butta_il_ban()
{
	bash "$B0_ENTRA" --root "rm -f $B_BAN $B_BAN.nuovo $B_COMANDO"
	b0_inf "⛔ buttato il file dei ban «$B_BAN» e il socket «$B_COMANDO»"
	b0_inf "   (B0.2: e' lo stato che sopravvive di piu' fra tutti)"
}

# ⛔ Le opzioni che ogni banco passa al proprio programma in Python.  Una riga
#    sola, perche' il giorno in cui se ne aggiunge una si aggiunga in un posto
#    solo — e perche' il bersaglio finisca nel registro di OGNI giro senza che
#    quattro banchi debbano ricordarselo.
bersaglio_opzioni_python()
{
	printf -- '--bersaglio %s --porta %s --uscita %s --md5 %s --giro %s' \
		"$B_NOME" "$B_PORTA" "$B_ESITI" "${B_MD5:-ignota}" "${B_GIRO:-$(date +%Y%m%d-%H%M%S)}"
}
