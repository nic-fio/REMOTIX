#!/bin/bash
#
# 01-b7-lancia.sh — gira SUL SERVER.  B7: il congedo, dal lato che riceve.
#
#   BERSAGLIO=innesto  bash .../01-b7-lancia.sh              tutto
#   BERSAGLIO=prodotto bash .../01-b7-lancia.sh solo tempo   un caso solo
#   BERSAGLIO=innesto  bash .../01-b7-lancia.sh elenco       le previsioni
#   BERSAGLIO=prodotto bash .../01-b7-lancia.sh frasi        e le frasi di §8.2
#
# ⛔ `BERSAGLIO` E' OBBLIGATORIA — vedi `01-b0-bersaglio.sh`.
#
# ---------------------------------------------------------------------------
# ⛔⭐ CHE COSA CAMBIA PUNTANDO B7 AL PRODOTTO — la previsione, scritta PRIMA
#
# | cosa | innesto | prodotto | perche' |
# |---|---|---|---|
# | ⭐ **i motivi provocabili** | **7** su 15 | ⛔ **8** su 15 | `src/main.c` congeda tutte le sessioni con `SERVER_IN_CHIUSURA` `0x0C` prima di uscire, e ASPETTA fino a 2 s che i byte escano.  L'innesto non ha nessun percorso di spegnimento (grep: zero occorrenze in `01-b3-rcp-innesta.py`).  ⛔ **Se B7 puntato al prodotto continua a dire «7 su 7», il denominatore e' sbagliato e il banco guarda dall'altra parte** |
# | il caso `server-in-chiusura` | non esiste | ⭐ esiste, e **spegne il server** | gira per ultimo, in un'invocazione sua, e B0.5 non gli si applica: la morte del server E' la cosa provata |
# | dove si misura l'esclusione di `0x0C` | `rcp/rcp.c` + `01-b3-rcp-innesta.py`, attesi **zero** | `main.c` + `trasporto.c` + `webtransport.c` + `rcp.c`, attesi **piu' di zero** | ⛔ `rcp.c` e' identico byte per byte nei due server: cercarlo li' direbbe «zero» su tutt'e due, ed e' un denominatore letto dove la cosa NON succede |
# | `§3.1 punto 1` nel registro | riga `REMOTIX B3: congedo motivo=0xNN` | riga `HH:MM:SS.mmm rcp congedo motivo=0xNN` | ⛔ la scrive `rcp.c`, uguale — a cambiare e' **il prefisso**.  Cercare «REMOTIX B3: » avrebbe dato «punto 1 assente» su TUTTI i casi del prodotto |
# | gli altri sei motivi | uguali | uguali | li decide `rcp.c`, identico |
# | `gia-attiva-remota` (0x0F) | il posto si libera alla morte della CONNESSIONE | ⭐ si libera alla chiusura dello **stream** | `src/webtransport.c` `wt_stream_chiuso()`.  ⚠ Col cliente di prova i due istanti coincidono, quindi qui **non** ci si aspetta differenza: la differenza la vede un browser (B11, `[M]` 7 «posto NEGATO» su 9 con Chrome) |
# | il tetto d'inattivita' | 120 s, chiesto da noi | ⛔ 30 s, **non scelto da noi** | `IDLE_MS` in `src/trasporto.c`.  Il caso `tempo-scaduto` tace 20 s: ci sta sotto i 30, ma il margine passa da 100 s a 10 s |
# | l'eco di B2 sugli stream | c'e' | ⛔ non c'e' | `scarta_stream_di_troppo()`: «i byte si buttano e NON si rimandano indietro».  B7 non la aspetta mai, quindi non lo tocca — ⚠ ma nessuno strumento nuovo la deve aspettare |
#
# ⛔ CON UN FILTRO IL GIRO E' PARZIALE, E LO DICE.  L'esito verde si legge «i
#    casi selezionati passano», mai «B7 passa».  ⚠ E un filtro che non combacia
#    con nessun nome esce **2**, non 0: «non ho niente da misurare» non e'
#    «tutto passato».
#
# ---------------------------------------------------------------------------
# ⛔ CHE COSA PROVA
#
# `RCP.md` §8.1: *«il congedo si verifica dal lato che lo riceve, mai dal
# registro di chi lo manda»*.  In v1, per **tre fasi**, il server scriveva
# «congedo il client» mentre il client scriveva «errore di rete»
# (`LEZIONI.md` §1.7).
#
# ⛔ E le strade sono DUE (§3.1): il `CONGEDO` sul canale di controllo **e** il
#    codice del motivo nella chiusura della sessione WebTransport.  Si contano
#    **separatamente**, con due denominatori, perche' il 10 agosto 2026 la
#    seconda mancava in **quattordici casi su trentasei** e nessun banco se
#    n'era accorto: bastava che arrivasse la prima.
#
# ⛔ Il guasto di `fasi/01-filo-nudo.md` §C1 — «si toglie la spedizione del
#    `CONGEDO` e si lascia il codice nella chiusura» — deve far diventare
#    ROSSO questo banco.  Se resta verde sta facendo una `||` dove serve una
#    `&&`.
#
# ---------------------------------------------------------------------------
# ⛔ E IL REGISTRO DEL SERVER SI LEGGE IN DUE PUNTI SOLI, DICHIARATI
#
#   · §3.1 **punto 1** — la riga «che cosa non ho capito», che e' per
#     definizione una riga di chi chiude: e' il punto 1 a chiederla;
#   · il verso **client→server** — dove chi riceve E' il server.
#
# Il motivo che il server MANDA lo giudicano sempre e solo le due strade, lette
# sul filo dal cliente di prova.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
UTENTE=prova
PAROLA=parola-di-prova

# ---------------------------------------------------------------------------
# ⛔ LA PAROLA D'ORDINE NON PASSA PIU' DALLA RIGA DI COMANDO — difetto **D12**,
#    curato il 12 agosto 2026.
#
# ⛔ QUI LA PAROLA finiva dentro la stringa che `bash $ENTRA --root "…"` riceve
#    come argomento: cioe' nell'`argv` di `bash`, in quello di `sudo` e in
#    quello di `python3`.  `/proc/<pid>/cmdline` su Linux e' **leggibile da
#    chiunque**, e un `ps` lanciato da un altro utente durante il giro la
#    stampava per intero.  ⚠ E i banchi di questa macchina girano mentre ci
#    lavorano altri.
#
# ⭐ LA STRADA E' QUELLA GIA' IN CASA (`banchi/01-b10-lancia.sh`), e non un
#    secondo modo: un file `0600` scritto con `printf` — un **builtin** della
#    shell, quindi nemmeno la scrittura passa per un processo con la parola in
#    `argv` — passato al banco come `--parola-file`, e cancellato con una
#    `trap` anche se il giro muore a meta'.
#
# ⚠ Nel `cmdline` finisce il PERCORSO, non la parola, e il file e' `0600`:
#   chi non e' noi non lo apre.
# ⚠ E il nome porta la sigla del banco: due giri che scrivessero lo stesso
#   file si cancellerebbero la parola a vicenda — la stessa forma che ha fatto
#   nascere il `PREFISSO` di `01-p5-accendi.sh`.
PAROLA_FUORI=$FUORI/tmp/b7-parola
PAROLA_DENTRO=$DENTRO/tmp/b7-parola

ripulisci_parola() { rm -f "$PAROLA_FUORI"; }
trap ripulisci_parola EXIT

# ⛔ `umask` IN UNA SOTTOSHELL — la riga che B10 ha pagato con un giro intero:
#    `umask 077` nudo resta addosso a tutto quel che viene dopo, compresi i
#    comandi mandati dentro il contenitore, e li' fa scrivere a root dei file
#    che poi `nicfio` non rilegge piu'.
mkdir -p "$FUORI/tmp" \
	&& ( umask 077; : > "$PAROLA_FUORI" ) \
	&& chmod 600 "$PAROLA_FUORI" \
	|| { printf '    ⛔ non si scrive %s: il giro non parte\n' "$PAROLA_FUORI"; exit 2; }
printf '%s\n' "$PAROLA" > "$PAROLA_FUORI"

# ⛔ Il bersaglio: una forma sola per i quattro banchi, in un file solo.
SIGLA=b7

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

# shellcheck source=01-b0-bersaglio.sh
. "$FUORI/01-b0-bersaglio.sh"
IND=$B_IND
PORTA=$B_PORTA
# ⛔ La radice dei sorgenti da cui si misura l'esclusione di 0x0C: dipende dal
#    bersaglio, e NON e' `rcp.c` da solo.
DENTRO_SORG=$DENTRO

AZIONE=${1:-tutto}
FILTRO=${2:-}

log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

if [ "$AZIONE" = elenco ]; then
	bash "$ENTRA" --root "python3 $DENTRO/01-b7-congedo.py --bersaglio $B_NOME --elenco"
	exit $?
fi

FRASI=
[ "$AZIONE" = frasi ] && FRASI=--frasi

# ---------------------------------------------------------------------------
# ⛔ 1. IL SERVER SI PREPARA — e le due strade non sono la stessa.
#
#   innesto   gli innesti si tolgono e si rimettono, si conta la marca nei
#             sorgenti, si compila guardando l'esito del costruttore, e poi si
#             prende l'impronta md5 del binario;
#   prodotto  ⛔ NON si ricompila — `src/` non e' di questo banco, e un banco
#             che ricompila quel che misura si toglie il testimone indipendente
#             — e ci si ferma se il binario e' piu' vecchio di un sorgente.
#             `[M]` 11 agosto 2026: lo era, di un'ora.
#
# ⛔ NESSUNA REDIREZIONE ATTORNO A `enter.sh`: si porterebbe via la richiesta di
#    password di sudo, e lo script resterebbe ad aspettare una domanda che
#    nessuno vede.  Le redirezioni stanno dentro le virgolette del comando
#    remoto (vedi `01-b0-bersaglio.sh`).
bersaglio_pronto || exit 3

# ⛔ E LA CHIUSURA RIMANDATA DEV'ESSERCI, perche' e' precisamente la cura del
#    difetto che B7 esiste per sorvegliare: senza, la capsula di chiusura non
#    parte su nessuna violazione trovata al primo messaggio — 14 casi su 36, il
#    10 agosto 2026.  ⚠ Trovarla assente non e' un rosso di B7: e' il banco che
#    dice «stai per misurare un server diverso da quello che credi».
# ⚠ E il file dove sta cambia col bersaglio: nell'innesto e' il codec innestato,
#   nel prodotto e' `webtransport.c` (`chiudi_sessione()`).
if [ "$B_NOME" = innesto ]; then
	DOVE_RIMANDO=$DENTRO/b2/ngtcp2/examples/http3_server_proto_codec.cc
else
	DOVE_RIMANDO=$DENTRO/remotix/webtransport.c
fi
RIMANDO=$(bash "$ENTRA" --root "grep -c 'RIMANDATA' $DOVE_RIMANDO" | tr -cd '0-9')
if [ "${RIMANDO:-0}" -ge 1 ]; then
	ok "la chiusura rimandata (§3.1 punto 3) c'e' in $(basename "$DOVE_RIMANDO")"
else
	ko "⚠ la chiusura RIMANDATA non c'e' in $DOVE_RIMANDO: se la seconda"
	ko "  strada risultera' assente, la causa e' QUESTA e non il modulo RCP"
fi

# ---------------------------------------------------------------------------
# ⛔ 2. LO STATO INIZIALE DEL BAN — B0.1, B0.2, B0.3.
#
# B7 fallisce **un** tentativo di autenticazione (B0.3 lo dice), cioe' consuma
# uno dei tre di §4.4-bis: da solo non banna, ma sommato a un residuo di un
# altro giro si'.  ⛔ E sul prodotto il ban sta su FILE: un ban di ieri
# renderebbe rosso tutto quel che segue, con il rosso sull'imputato sbagliato.
log "2. Lo stato iniziale del ban (B0.1, B0.2)"
bersaglio_butta_il_ban

# ---------------------------------------------------------------------------
log "3. Il server si accende"
inf "⚠ tetto d'inattivita' \$B_IDLE_LUNGO = $B_IDLE_LUNGO ms: il caso"
inf "  «tempo-scaduto» tace per venti secondi, e un tetto piu' corto"
inf "  chiuderebbe la connessione per conto suo — il banco leggerebbe «e'"
inf "  caduta» dove non e' caduto niente, e per giunta SENZA motivo, cioe'"
inf "  proprio la forma che B7 deve saper distinguere da un congedo"
if [ "$B_IDLE_SCELTA" = no ]; then
	inf "⛔ e su questo bersaglio quel numero non lo scegliamo noi (IDLE_MS in"
	inf "   src/trasporto.c): il margine sopra i 20 s passa da 100 s a 10 s"
fi
bersaglio_accendi filo "$B_IDLE_LUNGO" || exit 4
PID=$B_PID

inf "il comando di sblocco risponde? (PING — il denominatore di B0.3)"
bersaglio_ping || { ko "⛔ il comando di sblocco non risponde: in fondo non"
                    ko "   potrei rimettere la macchina a posto"
                    bersaglio_spegni; exit 4; }

# ⛔ 3-bis. HO MISURATO IL SERVER CHE HO DICHIARATO?
log "3-bis. L'impronta del bersaglio (LEZIONI.md §1.9, corollario 5)"
bersaglio_impronta
case $? in
0) : ;;
*) ko "⛔ mi fermo: i numeri finirebbero sul bersaglio sbagliato"
   bersaglio_spegni; exit 6 ;;
esac

fermare() { bersaglio_spegni; }

# ---------------------------------------------------------------------------
log "4. Il congedo, dal lato che riceve"
OPZ=$(bersaglio_opzioni_python)
COMUNE="--indirizzo $IND $OPZ --utente $UTENTE --parola-file $PAROLA_DENTRO \
	--registro $B_LOG --pagina $DENTRO/01-b11-pagina.html --dentro $DENTRO_SORG"
if [ -n "$FILTRO" ]; then
	bash "$ENTRA" --root "python3 -u $DENTRO/01-b7-congedo.py $COMUNE --solo $FILTRO"
else
	# ⛔ Il giro normale ESCLUDE `server-in-chiusura`, che spegne il server:
	#    gira dopo, con il server riacceso apposta (punto 7).
	bash "$ENTRA" --root "python3 -u $DENTRO/01-b7-congedo.py $COMUNE $FRASI --escludi server-in-chiusura"
fi
ESITO=$?

# ---------------------------------------------------------------------------
log "5. ⛔ Il server e' ancora vivo? — B0.5, dal di fuori"
inf "il banco lo chiede a ogni caso; questo lo chiede al SISTEMA, che e' un"
inf "testimone diverso: un processo puo' rispondere e avere gia' perso i figli"
if [ -d "/proc/$PID" ]; then
	ok "il processo $PID c'e' ancora"
else
	ko "⛔ IL SERVER E' MORTO durante il banco"
	ESITO=1
fi

# ---------------------------------------------------------------------------
log "6. Le due strade, come le ha scritte il server"
inf "⚠ QUESTO NON E' IL VERDETTO — il verdetto e' quello del punto 4, letto dal"
inf "  lato che riceve (§8.1).  Qui si guarda l'altra meta' della stessa storia:"
inf "  se le due colonne non si somigliano, il registro e il filo raccontano due"
inf "  cose diverse, ed e' la forma di difetto che §3.1 punto 3 esiste per"
inf "  smascherare"
if [ -f "$B_LOG_FUORI" ]; then
	# ⛔ Si conta e si stampa: un `grep -c` che dice 0 e un file che non si
	#    legge sono due fatti diversi, e il ramo qui sotto li tiene separati.
	C1=$(grep -c "congedo motivo=" "$B_LOG_FUORI")
	C2=$(grep -c "chiusa la sessione WebTransport" "$B_LOG_FUORI")
	C3=$(grep -c "chiusura della sessione RIMANDATA" "$B_LOG_FUORI")
	inf "congedi spediti (§3.1 punto 2, dal lato di chi manda): ${C1:-0}"
	inf "chiusure di sessione USCITE (§3.1 punto 3):             ${C2:-0}"
	inf "chiusure soltanto RIMANDATE:                            ${C3:-0}"
	if [ "${C3:-0}" -gt "${C2:-0}" ]; then
		ko "⛔ ${C3} chiusure rimandate e solo ${C2} uscite: qualche capsula"
		ko "   non e' mai partita — e' il difetto delle 14 su 36 del 10 agosto"
	fi
	grep "congedo motivo=" "$B_LOG_FUORI" | tail -8 | sed 's/^/        /'
else
	ko "⛔ IL REGISTRO NON SI LEGGE: $B_LOG_FUORI non esiste"
	ko "   non e' il server che non ha scritto — e' che non si legge"
	ko "   (volume non mappato? server mai partito? nome cambiato?)"
	ESITO=1
fi

# ---------------------------------------------------------------------------
# ⭐⛔ 7. IL GIRO DELLO SPEGNIMENTO — e su questo bersaglio esiste, sull'altro no.
#
# `SERVER_IN_CHIUSURA` `0x0C` non si provoca con un byte storto: lo provoca un
# `SIGTERM`.  ⛔ Quindi questo caso **spegne il server**, gira per ultimo e in
# un'invocazione sua, e B0.5 non gli si applica — la morte del server E' la cosa
# provata, e il banco lo dichiara invece di darsi un rosso da solo.
#
# ⚠ E il server si riaccende apposta: quello del punto 3 e' ancora vivo, e lo si
#   spegne prima, per bene, guardando che la porta si liberi.
log "7. ⭐ Il giro dello spegnimento (SERVER_IN_CHIUSURA 0x0C)"
if [ "$B_SPEGNIMENTO" != si ]; then
	inf "⚠ SALTATO: il bersaglio «$B_NOME» non ha nessun percorso di"
	inf "  spegnimento, e i suoi motivi provocabili sono SETTE.  ⛔ Questo non"
	inf "  e' un caso che manca: e' un caso che su questo server non esiste, e"
	inf "  l'esclusione l'ha MISURATA il banco col grep, non io con un commento"
elif [ -n "$FILTRO" ]; then
	inf "⚠ SALTATO: giro parziale (filtro «$FILTRO»)"
else
	fermare
	inf "il server si riaccende: quello di prima ha gia' misurato, e questo"
	inf "caso lo spegnera'"
	if bersaglio_accendi spegnimento "$B_IDLE_LUNGO"; then
		PID=$B_PID
		bersaglio_impronta || { ko "⛔ non e' il bersaglio dichiarato"; ESITO=6; }
		if [ "${ESITO:-0}" -ne 6 ]; then
			OPZ2=$(bersaglio_opzioni_python)
			bash "$ENTRA" --root "python3 -u $DENTRO/01-b7-congedo.py \
				--indirizzo $IND $OPZ2 --utente $UTENTE --parola-file $PAROLA_DENTRO \
				--registro $B_LOG --pagina $DENTRO/01-b11-pagina.html \
				--dentro $DENTRO_SORG --pid-server $PID \
				--solo server-in-chiusura"
			ESITO_SPEGN=$?
			# ⛔ E QUI IL SERVER DEVE ESSERE MORTO, non vivo: e' l'unico punto
			#    del banco in cui B0.5 si legge al contrario.  ⚠ Un server
			#    ancora vivo dopo un SIGTERM non e' «resistente»: e' un server
			#    che non ha eseguito il percorso che si stava misurando.
			#
			# ⛔⭐ MA GLI SI DA' IL TEMPO CHE LUI STESSO DICHIARA — 11 agosto 2026.
			#
			#     Questa riga guardava `/proc/$PID` SUBITO, e fino a oggi era
			#     giusta per accidente: il server rinunciava dopo tre decimi di
			#     secondo.  ⛔ Curato il difetto di §3.1 punto 3, `src/main.c`
			#     aspetta ora fino a **4 s** perche' la capsula di chiusura esca
			#     davvero — e questo banco dichiarava morto un server che stava
			#     facendo esattamente la cosa che il caso esiste per provare.
			#
			# ⚠ L'attesa e' LIMITATA e dichiarata: 8 s, cioe' il budget del
			#   server piu' il doppio del margine.  Un'attesa senza fondo
			#   trasformerebbe «non muore mai» in «il banco si e' piantato».
			ATTESO_MORTE=8
			for _ in $(seq $((ATTESO_MORTE * 10))); do
				[ -d "/proc/$PID" ] || break
				sleep 0.1
			done
			if [ -d "/proc/$PID" ]; then
				ko "⛔ il server e' ANCORA VIVO dopo il SIGTERM: il percorso di"
				ko "   spegnimento di src/main.c non e' stato eseguito, e il"
				ko "   congedo 0x0C che il banco ha (o non ha) letto non viene"
				ko "   da li'.  ⚠ Non e' un verde: e' una misura da rifare"
				ESITO_SPEGN=1
				bersaglio_spegni
			else
				ok "il server e' sparito dopo il SIGTERM, come deve"
				B_PID=""
			fi
			if [ "$ESITO_SPEGN" -ne 0 ] && [ "${ESITO:-0}" -eq 0 ]; then
				ESITO=$ESITO_SPEGN
			fi
		fi
	else
		ko "⛔ il server non si riaccende: il giro dello spegnimento NON e'"
		ko "   stato fatto, e questo non e' «passato»"
		[ "${ESITO:-0}" -eq 0 ] && ESITO=4
	fi
fi

# ---------------------------------------------------------------------------
# ⛔ 8. SI RIMETTE LA MACCHINA A POSTO, E LO SI DICHIARA — B0.3.
#    B7 fallisce un tentativo: da solo non banna, ma il residuo si toglie e si
#    dice quale dei tre esiti e' arrivato.  ⚠ Qui l'atteso e' «NON-BANNATO»: un
#    «TOLTO» vorrebbe dire che qualcosa ha fatto tre fallimenti, e sarebbe una
#    notizia sullo stato iniziale, non una pulizia.
log "8. Lo sblocco finale, dichiarato (B0.3)"
if [ -n "${B_PID:-}" ]; then
	inf "⚠ atteso «NON-BANNATO»: B7 fallisce UN tentativo su tre, e da solo"
	inf "  non banna.  Un «TOLTO» qui sarebbe una notizia sullo stato iniziale"
	bersaglio_sblocca dopo-b7 "$IND" || \
		ko "⚠ lo sblocco finale non e' andato: guarda la riga qui sopra"
else
	# ⛔ E questo NON e' «sbloccato»: e' «non ho parlato con nessuno», che e' il
	#    terzo esito di `01-b8-sblocca.py` e il piu' importante dei tre.
	inf "⚠ NESSUNO SBLOCCO: il server e' gia' spento (l'ha spento il giro dello"
	inf "  spegnimento), quindi il comando non ha nessuno con cui parlare."
	inf "  ⛔ Il ban resta com'era nel file «$B_BAN», che e' di B7 soltanto e si"
	inf "     butta al prossimo giro: nessun altro banco lo legge"
fi

fermare

log "Esito"
# ⛔ QUATTRO ESITI, NON DUE.  `01-b7-congedo.py` esce 2 quando il filtro non ha
#    selezionato niente, e 3 quando lo STRUMENTO non si e' certificato: un
#    banco non certificato non e' un rosso del server, ed e' l'unico modo di
#    non far passare per difetto del prodotto un difetto del banco.
case "$ESITO" in
0)
	if [ -n "$FILTRO" ]; then
		ok "⭐ i casi «$FILTRO» passano contro «$B_NOME»"
		inf "⚠ e questo NON e' «B7 passa»: il giro era parziale"
	else
		ok "⭐ B7 passa contro «$B_NOME» — $( [ "$B_SPEGNIMENTO" = si ] \
			&& printf 'OTTO motivi provocabili' || printf 'SETTE motivi provocabili' )"
		inf "⚠ e non e' «B7 passa»: l'altro bersaglio e' un altro programma,"
		inf "  con un denominatore diverso, e questo giro non ne dice niente"
	fi
	;;
2) ko "⛔ B7: non c'e' stato niente da misurare (filtro «$FILTRO»)" ;;
3)
	ko "⛔ B7 NON HA MISURATO: lo strumento non si e' certificato"
	ko "   ⚠ questo NON e' un rosso del server: e' il banco che si e'"
	ko "     fermato prima di produrre un numero di cui non risponde"
	;;
6) ko "⛔ B7: NON HO MISURATO — il bersaglio non e' quello dichiarato"
   ko "   ⚠ non e' un rosso del server: e' il banco che si e' fermato prima"
   ko "     di attribuire numeri al programma sbagliato" ;;
*) ko "⛔ B7: qualcosa non passa contro «$B_NOME»" ;;
esac
inf "il registro completo resta in $B_LOG_FUORI"
exit "$ESITO"
