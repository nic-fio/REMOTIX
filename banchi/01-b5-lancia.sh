#!/bin/bash
#
# 01-b5-lancia.sh — gira SUL SERVER.  B5: le prove di violazione.
#
#   BERSAGLIO=innesto  bash /media/REMOTIX/src/01-b5-lancia.sh            tutto
#   BERSAGLIO=prodotto bash /media/REMOTIX/src/01-b5-lancia.sh solo tela  un pezzo solo
#   BERSAGLIO=innesto  bash /media/REMOTIX/src/01-b5-lancia.sh elenco     le previsioni
#
# ⛔ `BERSAGLIO` E' OBBLIGATORIA — vedi `01-b0-bersaglio.sh`, che e' l'unico
#    posto in cui i due server sono descritti.
#
# ---------------------------------------------------------------------------
# ⛔ CHE COSA CAMBIA PUNTANDO B5 AL PRODOTTO — la previsione, scritta PRIMA
#
# | cosa | innesto | prodotto | perche' |
# |---|---|---|---|
# | i motivi sul filo (`ERRORE_PROTOCOLLO`, `NIENTE_IN_COMUNE`, …) | uguali | uguali | ⭐ li decide `rcp.c`, che e' **identico byte per byte** nei due server (md5 `cb7af778…`) |
# | la scelta del codec e lo scarto nel registro (§4.3) | c'e' | c'e' | stesse righe, stesso `rcp.c` |
# | `0x01` input e `0x02` appunti su uno stream unidirezionale | «violazione» | ⭐ **leciti**, la sessione resta viva | `src/webtransport.c` `smista_uni()`: *«nell'innesto entrambi erano segnati violazione, e un client conforme che apriva il canale di input si vedeva scartare OGNI byte per sempre»*.  ⚠ B5 oggi **non li prova**: e' un buco, non una differenza attesa |
# | l'**eco** sugli stream aperti dal banco | c'e' (30 byte, e' il «byte che torna» di B2) | ⛔ **NON c'e'** | `src/webtransport.c` `scarta_stream_di_troppo()`: *«i byte si buttano, e NON si rimandano indietro»*.  ⚠ Nessuno strumento la deve **aspettare**: chi lo fa resta appeso, ed e' il rosso che il 10 agosto e' stato diagnosticato per ore come difetto del certificato |
# | il tetto d'inattivita' | 120 s, chiesto da noi | ⛔ **30 s, non scelto da noi** | `IDLE_MS` in `src/trasporto.c`, e nessuna opzione lo tocca.  I casi di B5 aspettano al massimo 12 s: ci stanno, ma il margine passa da 108 s a 18 s |
# | la riga di riassunto «REMOTIX B3\|B5» | c'e' | ⛔ non c'e' | il prodotto scrive `HH:MM:SS.mmm <area>`: si conta l'impronta del bersaglio, non quella dell'innesto |
# | il limitatore (7 falliti) | banna in memoria, muore col processo | banna **su file** | il file dei ban e' per banco e si butta all'inizio, e in fondo si sblocca **dichiarandolo** (B0.3) |
#
# ⛔ CON UN FILTRO IL GIRO E' PARZIALE, E LO DICE.  Le misure che non dipendono
#    dai casi selezionati — il percorso, il giro completo, il limitatore, e le
#    due righe di registro di §4.3 — NON si eseguono, e l'esito verde si legge
#    «i casi selezionati passano», mai «B5 passa».  ⚠ E un filtro che non
#    combacia con nessun nome esce **2**, non 0: «non ho niente da misurare»
#    non e' «tutto passato» (rilievo R7.15).
#
# ---------------------------------------------------------------------------
# ⛔ CHE COSA PROVA, E LA META' CHE SI DIMENTICA
#
# `RCP.md` §3 e' la regola di rigore: quel che non si capisce non si ignora, la
# connessione cade, col motivo.  ⭐ Ma **una regola di rigore non si prova
# facendo le cose giuste**: un server che non controlla niente passa tutti i
# giri di B3 e cade il giorno in cui qualcuno gli manda un byte storto.
#
# ⛔ E dopo ogni violazione si controlla che **il server sia ancora li'**
#    (B0.5).  Un server ucciso dal nucleo «fa cadere la connessione» esattamente
#    come uno che congeda — e si porta via **le sessioni di tutti gli altri**.
#
# ---------------------------------------------------------------------------
# ⛔ E IL REGISTRO DEL SERVER SI GUARDA, MA NON E' L'ARBITRO
#
# Il motivo lo verifica **il lato che riceve** (§8.1): il registro del server e'
# la stessa mano che ha scritto il codice.  ⚠ Due cose pero' esistono SOLO nel
# registro, perche' §4.3 le impone li': la **scelta del codec** e lo **scarto**
# delle voci sconosciute.  Quelle si leggono di la', ed e' dichiarato.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

# ⛔ Il bersaglio: una forma sola per i quattro banchi, in un file solo.
SIGLA=b5
# shellcheck source=01-b0-bersaglio.sh
. "$FUORI/01-b0-bersaglio.sh"
IND=$B_IND
PORTA=$B_PORTA

AZIONE=${1:-tutto}
FILTRO=${2:-}

log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

if [ "$AZIONE" = elenco ]; then
	bash "$ENTRA" --root "python3 $DENTRO/01-b5-violazioni.py --bersaglio $B_NOME --elenco"
	exit 0
fi

bersaglio_dichiara

# ---------------------------------------------------------------------------
# ⛔ 1. IL SERVER SI PREPARA — e le due strade non sono la stessa.
#
#   innesto   gli innesti si tolgono e si rimettono, si conta la marca nei
#             sorgenti e si compila guardando l'esito del costruttore;
#   prodotto  ⛔ NON si ricompila: `src/` non e' di questo banco, e un banco che
#             ricompila quel che misura si toglie il testimone indipendente.  Si
#             verifica soltanto che il binario ci sia e sia piu' recente di ogni
#             sorgente — `[M]` 11 agosto 2026, il binario del prodotto era piu'
#             vecchio di `trasporto.c` di un'ora, e il registro dell'ultima
#             accensione portava una formulazione di due generazioni prima.
#
# ⚠ E in tutt'e due i casi si prende l'impronta **md5 del binario**, che finisce
#   nel registro di questo giro: e' l'unico modo di sapere, sei ore dopo, se due
#   giri hanno misurato lo stesso programma.
#
# ⛔ NESSUNA REDIREZIONE ATTORNO A `enter.sh` — si porterebbe via la richiesta di
#    password di sudo, e lo script resterebbe ad aspettare una domanda che
#    nessuno vede.  E' successo di nuovo il 10 agosto 2026 su QUESTO file,
#    quattro giri dopo che la lezione era stata scritta.  Le redirezioni stanno
#    dentro le virgolette del comando remoto (vedi `01-b0-bersaglio.sh`).
bersaglio_pronto || exit 3

# ---------------------------------------------------------------------------
# ⛔ 2. LO STATO INIZIALE DEL BAN — B0.1 e B0.2.
#
# B5 fa **sette autenticazioni fallite di fila** (`limitatore()`), quindi si
# banna da solo: e' voluto, ed e' quel che prova il contatore per indirizzo.
# ⛔ Ma il ban del prodotto sta su FILE, e un ban di ieri renderebbe rosso tutto
#    quel che segue con il rosso sull'imputato sbagliato.  Il file e' di questo
#    banco soltanto — `01-b0-bersaglio.sh` gliene da' uno per banco e per
#    bersaglio — e si butta qui.
log "2. Lo stato iniziale del ban (B0.1, B0.2)"
bersaglio_butta_il_ban
inf "⚠ e questo banco fa 7 autenticazioni FALLITE di fila: si banna da solo,"
inf "  ed e' la cosa che prova.  Lo sblocco sta in fondo, dichiarato (B0.3)"

# ---------------------------------------------------------------------------
log "3. Il server si accende"
inf "⚠ il tetto d'inattivita' e' \$B_IDLE_LUNGO = $B_IDLE_LUNGO ms: alcuni casi"
inf "  aspettano fino a dodici secondi per essere sicuri che il congedo NON"
inf "  arrivi, e un tetto piu' corto chiuderebbe la connessione per conto suo —"
inf "  il banco leggerebbe «e' caduta» dove non e' caduto niente (R3.19)"
if [ "$B_IDLE_SCELTA" = no ]; then
	inf "⛔ e su questo bersaglio quel numero NON lo scegliamo noi: e' IDLE_MS"
	inf "   in src/trasporto.c.  Il margine sopra i 12 s passa da 108 s a 18 s"
fi
bersaglio_accendi filo "$B_IDLE_LUNGO" || exit 4
PID=$B_PID

# ⛔ E IL COMANDO DI SBLOCCO DEVE ESSERE VIVO **PRIMA**, non alla fine: il `PING`
#    e' il denominatore di B0.3.  Senza, «il ban non e' scattato» e «lo sblocco
#    non e' mai arrivato a nessuno» hanno di nuovo lo stesso aspetto — e lo si
#    scoprirebbe in fondo, a misure fatte.
inf "il comando di sblocco risponde? (PING — il denominatore di B0.3)"
bersaglio_ping || { ko "⛔ il comando di sblocco non risponde: in fondo non"
                    ko "   potrei rimettere la macchina a posto, e me ne"
                    ko "   accorgerei a misure fatte.  Mi fermo adesso."
                    bersaglio_spegni; exit 4; }

fermare() { bersaglio_spegni; }

# ---------------------------------------------------------------------------
# ⛔ 3-bis. HO MISURATO IL SERVER CHE HO DICHIARATO? — e si chiede al registro
#    del server, non alla riga di comando che ho scritto io.
log "3-bis. L'impronta del bersaglio (LEZIONI.md §1.9, corollario 5)"
bersaglio_impronta
case $? in
0) : ;;
1) ko "⛔ mi fermo: i numeri finirebbero sul bersaglio sbagliato"; fermare; exit 6 ;;
*) ko "⛔ mi fermo: non so che cosa sto per misurare"; fermare; exit 6 ;;
esac

# ---------------------------------------------------------------------------
log "4. Le violazioni"
OPZ=$(bersaglio_opzioni_python)
if [ -n "$FILTRO" ]; then
	bash "$ENTRA" --root "python3 -u $DENTRO/01-b5-violazioni.py --indirizzo $IND $OPZ --solo $FILTRO"
else
	bash "$ENTRA" --root "python3 -u $DENTRO/01-b5-violazioni.py --indirizzo $IND $OPZ"
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
log "6. Le due righe che vivono solo nel registro (§4.3)"
inf "la SCELTA del codec, e lo SCARTO delle voci sconosciute"
#
# ⛔ DUE CONTROLLI CHE PRIMA GIRAVANO SEMPRE, E DAVANO ROSSO SU UNA REGOLA CHE
#    NESSUNO AVEVA CHIESTO AL SERVER DI APPLICARE.
#
#    Lo scarto di `vp9` lo sollecitano due soli casi — `hevc-e-vp9` e
#    `capacita-sconosciuta`.  Con `01-b5-lancia.sh solo tela` quei casi non
#    girano, il `grep` non trova niente, e il banco accusava il server di non
#    aver scritto una riga che nessuno gli aveva dato occasione di scrivere.
#    E' esattamente il difetto che questo stesso script dichiara di temere per
#    l'innesto, venti righe piu' in su (rilievo R7.15).
#
# ⛔ E `grep -q` su un file che NON C'E' esce 2, non 1: «la riga manca» e «il
#    registro non si legge» finivano nello stesso ramo `else`, cioe' la forma
#    E8.  Il file si guarda prima, e si dice quale delle due cose e' successa.
riga_nel_registro() {   # $1 = motivo cercato, $2 = frase in caso d'assenza
	if [ ! -f "$B_LOG_FUORI" ]; then
		ko "⛔ IL REGISTRO NON SI LEGGE: $B_LOG_FUORI non esiste"
		ko "   non e' il server che non ha scritto — e' che non si legge."
		ko "   (volume non mappato? server mai partito? nome cambiato?)"
		ESITO=1
		return
	fi
	if grep -q "$1" "$B_LOG_FUORI"; then
		ok "c'e':"
		grep -m2 "$1" "$B_LOG_FUORI" | sed 's/^/        /'
	else
		ko "$2"
		ESITO=1
	fi
}

if [ -n "$FILTRO" ]; then
	inf "⚠ SALTATO: filtro «$FILTRO» attivo.  Queste due righe le producono"
	inf "  i casi hevc-e-vp9 e capacita-sconosciuta, che potrebbero non"
	inf "  essere stati selezionati: un rosso qui sarebbe un rosso su una"
	inf "  regola che il server non ha mai avuto occasione di applicare"
else
	riga_nel_registro "negoziato video.codec=hevc" \
		"⛔ la scelta del codec NON e' nel registro: §4.3 la impone"
	riga_nel_registro "scartate voci sconosciute" \
		"⛔ lo scarto di vp9 NON e' nel registro: una negoziazione riuscita con dentro il contrario di quel che si voleva si vede solo se qualcuno la scrive (trappola 4 di LEZIONI.md §4)"
fi

log "7. E che cosa ha scritto il server, in breve"
if [ -f "$B_LOG_FUORI" ]; then
	# ⛔ Si conta l'impronta DEL BERSAGLIO, non quella dell'innesto: il
	#    prodotto non scrive «REMOTIX B3» in nessuna riga, e un conteggio a
	#    zero verrebbe letto come «il server non ha scritto niente».
	grep -cE "$B_IMPRONTA" "$B_LOG_FUORI" \
		| sed 's/^/        righe di registro (impronta del bersaglio): /'
	grep "congedo motivo" "$B_LOG_FUORI" | tail -5 | sed 's/^/        /'
else
	inf "⛔ nessun registro da riassumere: il file non c'e'"
fi

# ---------------------------------------------------------------------------
# ⛔ 8. SI RIMETTE LA MACCHINA A POSTO, E LO SI DICHIARA — regola B0.3.
#
# ⛔ Lo sblocco sta QUI e non altrove: dentro il giro farebbe passare il
#    limitatore per costruzione — «uno sblocco chiamato dentro il giro fa
#    passare tutto il resto» — e B5 il limitatore lo prova.
#
# ⚠ E si dichiara quale dei TRE esiti e' arrivato.  `TOLTO` vuol dire che il ban
#   c'era davvero, cioe' che il limitatore ha funzionato: e' una conferma
#   indipendente, letta dal lato del PADRONE DI CASA invece che dal filo.
#   `NON-BANNATO` dopo sette fallimenti sarebbe una notizia, non una pulizia.
#   «Non ho parlato con nessuno» non e' ne' l'uno ne' l'altro.
log "8. Lo sblocco finale, dichiarato (B0.3)"
inf "⛔ mai prima: dentro il giro farebbe passare il limitatore per costruzione"
inf "⚠ atteso «TOLTO» sull'indirizzo del banco: dopo sette fallimenti il ban"
inf "  c'e', e un «NON-BANNATO» qui sarebbe una notizia sul limitatore, non una"
inf "  pulizia riuscita"
bersaglio_sblocca dopo-b5 "$IND" || {
	ko "⚠ lo sblocco finale non e' andato: l'indirizzo puo' restare fuori"
	ko "  per dodici ore sul file dei ban di QUESTO banco ($B_BAN)"
	ko "  — non su quello degli altri, che ne hanno uno ciascuno"
}

fermare

log "Esito"
# ⛔ TRE ESITI, NON DUE.  `01-b5-violazioni.py` esce 2 quando il filtro non ha
#    selezionato nessun caso: «non ho niente da misurare» non e' «passa», e un
#    errore di battitura nel filtro non deve avere il colore del verde.
if [ "$ESITO" -eq 2 ]; then
	ko "⛔ B5: non c'e' stato niente da misurare (filtro «$FILTRO»)"
elif [ "$ESITO" -eq 0 ]; then
	if [ -n "$FILTRO" ]; then
		ok "⭐ i casi «$FILTRO» passano contro «$B_NOME»"
		inf "⚠ e questo NON e' «B5 passa»: il giro era parziale"
	else
		ok "⭐ B5 passa contro «$B_NOME»"
		inf "⚠ e non e' «B5 passa»: e' «B5 passa contro $B_NOME».  L'altro"
		inf "  bersaglio e' un altro programma, e questo giro non ne dice niente"
	fi
elif [ "$ESITO" -eq 6 ]; then
	ko "⛔ B5: NON HO MISURATO — il bersaglio non e' quello dichiarato"
	ko "   ⚠ questo non e' un rosso del server: e' il banco che si e' fermato"
	ko "     prima di attribuire dei numeri al programma sbagliato"
else
	ko "⛔ B5: qualcosa non passa contro «$B_NOME»"
fi
inf "il registro completo resta in $B_LOG_FUORI"
exit "$ESITO"
