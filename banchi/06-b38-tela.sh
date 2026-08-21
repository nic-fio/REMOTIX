#!/bin/bash
#
# 06-b38-tela.sh — ⭐ la strada della TELA contro il PRODOTTO, giudicata dall'arbitro.
#
#   gira SUL SERVER, come nicfio.  ⭐ E l'utente, la porta e l'albero si
#   passano dall'ambiente — non sono piu' cablati:
#
#     PORTA=7721 UTENTE=provat6 UID_B=1007 \
#     PAROLA_DA_FILE=/home/nicfio/.pa10-provat6 \
#     PAROLA_SUDO=/home/nicfio/.pa10-sudo \
#     ALB=/media/REMOTIX/src/06-a10-src LAV=/media/REMOTIX/tmp/06-a10 \
#     DENTRO_ALB=/srv/src/06-a10-src DENTRO_LAV=/srv/remotix/tmp/06-a10 \
#     bash $ALB/banchi/06-b38-tela.sh
#
# ---------------------------------------------------------------------------
# ⛔ CHE COSA PROVA, E CHE COSA **NON** PROVA
#
# Sottofase 6.6.  `01-b4-validatore.py` e' certificato sul portatile su **56**
# registrazioni **costruite**, ciascuna accusata sul byte dichiarato prima, e su
# **23** mutazioni dell'arbitro.  ⭐ Quella meta' vale di piu' e sta in piedi da
# sola: non le serve nessun server.
#
# ⛔ **Questa meta' e' l'altra, e «conforme» qui NON vuol dire «funziona»**:
#
#   · dice che i **byte** che il prodotto mette sul filo rispettano `RCP.md`
#     §7.1, §4.5, §6.2 e §11.1 nei casi che questi giri esercitano;
#   · ⛔ **NON dice che i PIXEL siano cambiati**: il palco, il compositore e
#     l'immagine non passano di qui.  Chi guarda i pixel e' la sottofase 6.3 col
#     compositore vero, e il testimone e' l'utente;
#   · ⭐⛔ **MA «senza toccare il palco» adesso si vede** — 21 agosto 2026.  La
#     frase che stava qui — *«un server che rispondesse `TELA(ADATTATA,
#     1264x800)` senza toccare il palco uscirebbe conforme da questo banco»* —
#     era vera fino a stamattina.  Con `RCPREG 0x00 0x03` la traccia porta
#     l'**istante** e i **28 byte di §6.2** di ogni fotogramma, e l'arbitro ha
#     **T4**: dopo un `TELA(ADATTATA, LxA)`, se passano fotogrammi per piu' di
#     tre secondi e nessuno dichiara `LxA`, la tela e' stata detta e non fatta.
#     ⚠ Resta una prova sui BYTE: dice che il flusso e' cambiato di misura, non
#       che l'immagine sia giusta;
#   · ⭐ **e le coordinate in volo di §7.1 sono arbitrabili, in UN VERSO SOLO**.
#     Anche questa riga diceva il contrario, e la ragione era vera: §11.1 non
#     registrava il tempo.  Adesso lo registra, e l'arbitro conclude **solo**
#     quando l'intervallo misurato al client supera il secondo — perche' quello
#     del server e' piu' lungo, mai piu' corto.  ⛔ Sotto il secondo **dice** che
#     non si giudica, invece di tacere;
#   · ⚠ e questi cinque giri **non mandano nessun `PUNTATORE`**: la regola del
#     secondo di grazia e' arbitrabile ma qui non e' esercitata, ed e' la
#     prossima cosa da aggiungere — dichiarata invece che sottintesa;
#   · ⚠ e i tempi qui dentro sono presi **sotto carico**, con gli altri banchi
#     della fase 6 accesi.  Si dichiarano col carico accanto, e non si
#     confrontano con numeri presi a macchina ferma.
#
# ---------------------------------------------------------------------------
# ⛔ L'ISOLAMENTO — le cinque regole di `fasi/06-la-tela-e-la-vista.md` §0-bis
#
#   di serie: porta 7761 · utente `prova2` · albero `/media/REMOTIX/src/06-a-src`
#   ⭐ il 21 agosto 2026 il giro vero e' stato fatto su **7721 · `provat6` (uid
#   1007) · `/media/REMOTIX/src/06-a10-src`**, con ban, socket del comando e
#   certificati propri.
#
# ⛔⛔ `prova`, la porta **7700** e la **7730** NON SI TOCCANO: sono dell'utente.
# ⛔ E la **7771** e' di un altro agente: non si spegne.
# ⛔ E non si chiama mai `06-b35-terreno.sh pulisci`: fa `userdel -r`, e `prova2`
#    e' un utente di sistema che altri banchi usano.
set -uo pipefail

PORTA=${PORTA:-7761}
UTENTE=${UTENTE:-prova2}
ALB=${ALB:-/media/REMOTIX/src/06-a-src}
LAV=${LAV:-/media/REMOTIX/tmp/06-a}
DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/06-a}
DENTRO_ALB=${DENTRO_ALB:-/srv/src/06-a-src}
IND=${IND:-192.168.0.2}
UID_B=${UID_B:-1002}     # ⛔ l'uid dell'utente del banco: cambia con l'utente
PAROLA_SUDO=${PAROLA_SUDO:-/home/nicfio/.p6a-sudo}

log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
BENE=0

# ⛔ La parola di `sudo` e quella di `prova2` NON passano mai dalla riga di
#    comando (difetto D12): si leggono da file con `sed`, e `printf` e' un
#    builtin — nemmeno la scrittura passa per un processo con la parola in argv.
sudo_mio() { printf '%s\n' "$(cat "$PAROLA_SUDO")" | sudo -S -p 'Password: ' "$@"; }
dentro()   { printf '%s\n' "$(cat "$PAROLA_SUDO")" | bash /media/REMOTIX/enter.sh --root "$1"; }

PAROLA_FILE=$LAV/parola-b38
DENTRO_PAROLA=$DENTRO_LAV/parola-b38
ripulisci() { rm -f "$PAROLA_FILE"; }
trap ripulisci EXIT

# ---------------------------------------------------------------------------
log "0. Il terreno — e si VERIFICA, non si spera"
inf "carico: $(uptime | sed 's/.*average/media/')"
inf "orologio di questa macchina: $(date)   ⚠ e' indietro di 2 h sul portatile"
[ -x "$ALB/src/remotix" ] || { ko "«$ALB/src/remotix» non c'e' o non e' eseguibile"; exit 2; }
inf "impronta del rcp.c misurato: $(sha256sum "$ALB/src/rcp.c" | cut -c1-64)"
inf "binario: $(stat -c '%y  %s byte' "$ALB/src/remotix")"
n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
[ "$n" -eq 0 ] || { ko "la porta $PORTA e' gia' occupata: non si accende sopra"; exit 2; }
[ -f /etc/pam.d/remotix ] || { ko "manca /etc/pam.d/remotix: PAM direbbe sempre di no"; exit 2; }
ok "binario, porta $PORTA libera, PAM a posto"

# ⛔ La parola di `prova2` si legge, non si scrive qui: l'host la porta in
#    `src/provisiona.sh`, ed e' quella che PAM verifica — ⚠ **non** quella di
#    `/media/REMOTIX/credenziali-banchi`, che e' del `prova2` del CONTENITORE.
#    Sono due utenti diversi con lo stesso nome, e le due parole si somigliano
#    abbastanza da far perdere un'ora.
# ⛔⛔ E SI PRENDE DALLA RIGA DI `chpasswd`, NON DALLA PRIMA CHE COMBACIA.
#
#    Primo giro del 16 agosto 2026: senza `grep chpasswd` la prima occorrenza di
#    `prova2:` in quel file e' la riga `for u in prova:1001 prova2:1002`, ⇒ il
#    banco ha usato **`1002`** — l'uid — come parola d'ordine, e ha preso cinque
#    `RESPINTO(CREDENZIALI_ERRATE)` seguiti da `TROPPI_TENTATIVI`: il ban di
#    §4.4-bis, fatto scattare da un difetto del banco.
#    ⚠ E il rosso sembrava del prodotto: cinque tracce **conformi** in cui la
#      tela non veniva esercitata affatto.  A dirlo e' stato il denominatore —
#      *«0 coppie ADATTA_TELA/TELA chiuse»* — non il colore del verdetto.
# ⭐ E DAL 21 AGOSTO 2026 LA PAROLA SI PUO' PASSARE, invece di dedurla soltanto.
#    ⚠ `provisiona.sh` conosce `prova` e `prova2` e basta: gli utenti dei banchi
#    di fase 6 (`provat6`, `provap6`, …) nascono dai loro terreni e in quel file
#    NON ci sono.  ⇒ Con un utente diverso il `grep` tornava vuoto e il banco
#    usciva 2 dicendo «non ho trovato la parola» — vero e inutile.
#    ⛔ E resta un FILE, mai un argv (difetto D12).
if [ -n "${PAROLA_DA_FILE:-}" ]; then
	[ -r "$PAROLA_DA_FILE" ] || { ko "PAROLA_DA_FILE non si legge"; exit 2; }
	P=$(cat "$PAROLA_DA_FILE")
	inf "la parola di $UTENTE viene da PAROLA_DA_FILE, non da provisiona.sh"
else
	P=$(grep 'chpasswd' "$ALB/src/provisiona.sh" \
	    | grep -o "$UTENTE:[A-Za-z0-9._-]*" | head -1 | cut -d: -f2)
fi
[ -n "$P" ] || { ko "non ho trovato la parola di $UTENTE"; exit 2; }
mkdir -p "$LAV"
( umask 077; : > "$PAROLA_FILE" ) && chmod 600 "$PAROLA_FILE" \
  || { ko "non si scrive $PAROLA_FILE"; exit 2; }
printf '%s\n' "$P" > "$PAROLA_FILE"
unset P
ok "la parola di $UTENTE sta in un file 0600 — mai in un argv (D12)"

# ---------------------------------------------------------------------------
log "1. Si accende il server — porta $PORTA, tutto suo"
sudo_mio env PORTA="$PORTA" UTENTE="$UTENTE" UID_B="$UID_B" \
     D="$ALB/src" LAV="$LAV" \
     bash "$ALB/banchi/06-b35-terreno.sh" accendi
A=$?
[ "$A" -eq 0 ] || { ko "il server non si e' acceso (uscita $A)"; exit 2; }
ok "acceso"

spegni() {
	sudo_mio env PORTA="$PORTA" UTENTE="$UTENTE" D="$ALB/src" LAV="$LAV" \
	     bash "$ALB/banchi/06-b35-terreno.sh" spegni
	ripulisci
}
trap spegni EXIT

# ---------------------------------------------------------------------------
# ⛔ Ogni giro dichiara il suo ATTESO **prima**, e poi si guarda.  L'ordine non
#    e' cosmetico: e' la regola B0.4, ed e' l'unica cosa che distingue una
#    misura da una spiegazione di quel che e' successo.
#
# ⛔⛔⛔ E DAL 21 AGOSTO 2026 L'ATTESO SI **CONFRONTA**, non si stampa soltanto.
#
# *Rilievi 4 e 5 della revisione avversariale dei sei banchi (agente A9).*
#
# Fino a stamattina questa funzione:
#   · prendeva `local e=$?` del cliente, lo **stampava** e non lo usava piu';
#   · riceveva l'atteso in `$2`, lo **stampava** e non lo usava piu'.
#
# ⛔ Il risultato misurato dal revisore: **un server che non rispondesse MAI a
#    un `ADATTA_TELA` usciva verde da tutti e cinque i giri**.  Il cliente
#    torna **5** («nessun TELA») con la connessione ancora viva, l'arbitro —
#    giustamente — non accusa una traccia che finisce a sessione viva, e questo
#    banco stampava *«⭐ tutti i giri della tela sono conformi»* sopra un
#    prodotto che la tela non la implementa affatto.
#
# ⚠ E il banco **conosceva gia'** questo modo di sbagliare: il riquadro qui
#   sopra racconta le cinque tracce conformi del 16 agosto in cui *«la tela non
#   veniva esercitata affatto»*, e dice che a smascherarle era stato **il
#   denominatore** — *«0 coppie ADATTA_TELA/TELA chiuse»*.  ⛔ Quel numero
#   l'arbitro lo **stampa** a ogni giro, e `giro()` non lo leggeva.
#
# ⭐ Adesso ogni giro dichiara PRIMA tre numeri, e tutt'e tre si confrontano:
#   l'uscita del **cliente**, le **coppie chiuse** che l'arbitro conta, e la
#   **tela in vigore alla fine** che l'arbitro legge dai byte.
#
# ⛔ Il verdetto resta dell'ARBITRO — questi tre non sono un secondo giudice
#    del protocollo: sono il **denominatore**, cioe' la prova che la scena e'
#    stata esercitata.  «Conforme» senza denominatore vuol dire «non ho
#    guardato», ed e' la differenza fra `LEZIONI.md` §1.3 e una misura.
#
# ⛔⛔ E IL QUARTO NUMERO E' LA **PROVENIENZA** DELLA TELA, non un altro valore —
#     21 agosto 2026, e a chiederlo e' stato il primo giro vero.
#
# `[M]` Il giro 3 pretendeva *«tela alla fine = 1920x1080»* e ha misurato
# **1600x900**: ⭐ non e' un difetto del prodotto, e' un fatto che nessuno aveva
# scritto — **la tela sopravvive alla sessione**.  Il palco resta dove il client
# precedente l'ha lasciato, e il `SESSIONE` del giro dopo concede QUELLA misura,
# non i 1920x1080 che l'`ATTACCA` chiedeva.
#
# ⇒ Un atteso scritto come numero assoluto lega il giro 3 all'ordine dei giri, e
#   un banco che cambia verdetto se lo lanci da solo non e' un banco.  ⛔ Quel
#   che il giro 3 vuole davvero dire e' *«la tela NON e' cambiata»*, cioe' **da
#   dove viene** la tela in vigore alla fine: da `SESSIONE` (nessun
#   `TELA(ADATTATA)` l'ha toccata) o da `TELA(ADATTATA)`.  Quella e' la regola;
#   il numero era un modo indiretto e fragile di dirla.
giro() # nome · uscita-cliente · coppie · tela-finale · da · atteso · -- · opzioni
{
	local nome=$1 uc=$2 coppie=$3 telafine=$4 daatteso=$5 atteso=$6; shift 7
	log "$nome"
	inf "⛔ ATTESO, dichiarato prima: $atteso"
	inf "   e i quattro: cliente=$uc · coppie chiuse=$coppie · tela alla fine=$telafine · viene da=$daatteso"
	rm -f "$LAV/$nome.rcpreg" "$LAV/$nome.txt" "$LAV/$nome-arbitro.txt"
	dentro "python3 -u $DENTRO_ALB/banchi/01-b3-cliente.py \
--indirizzo $IND --porta $PORTA --utente $UTENTE \
--parola-file $DENTRO_PAROLA --registra $DENTRO_LAV/$nome.rcpreg \
$* > $DENTRO_LAV/$nome.txt 2>&1"
	local e=$?
	sed 's/^/    | /' "$LAV/$nome.txt" 2>/dev/null
	inf "il cliente esce $e   (0 = a posto · 4 = caduta · 5 = ⛔ nessun TELA)"
	if [ "$e" != "$uc" ]; then
		ko "⛔ il cliente esce $e e l'atteso era $uc"
		[ "$e" = 5 ] && ko "   ⛔⛔ 5 = NESSUN TELA: il server non risponde ad ADATTA_TELA"
		BENE=1
	fi
	if [ ! -f "$LAV/$nome.rcpreg" ]; then
		ko "nessuna traccia da giudicare per «$nome»"
		BENE=1
		return 1
	fi
	python3 "$ALB/banchi/01-b4-validatore.py" "$LAV/$nome.rcpreg" \
	    2>&1 | tee "$LAV/$nome-arbitro.txt"
	local g=${PIPESTATUS[0]}
	case "$g" in
	0) ok "⭐ l'arbitro dichiara CONFORME la traccia «$nome»" ;;
	1) ko "⛔ NON CONFORME — e il byte e la regola stanno qui sopra" ; BENE=1 ;;
	2) ko "⚠ la REGISTRAZIONE e' rotta: e' un difetto di banco, non del filo" ; BENE=1 ;;
	3) ko "⚠ niente da giudicare: il cliente non ha registrato niente" ; BENE=1 ;;
	esac

	# ── ⭐ IL DENOMINATORE, letto dalla riga che l'arbitro stampa gia' ──────
	local c t
	c=$(sed -n 's/.*la tela: \([0-9]*\) coppie.*/\1/p' "$LAV/$nome-arbitro.txt" | tail -1)
	t=$(sed -n 's/.*tela in vigore alla fine: \([0-9]*x[0-9]*\).*/\1/p' \
	    "$LAV/$nome-arbitro.txt" | tail -1)
	[ -n "$c" ] || c="(l'arbitro non l'ha detto)"
	[ -n "$t" ] || t="(mai dichiarata)"
	if [ "$c" = "$coppie" ]; then
		inf "coppie ADATTA_TELA/TELA chiuse: $c — come dichiarato"
	else
		ko "⛔ coppie chiuse: $c, l'atteso era $coppie — ⚠ la scena NON e' stata esercitata"
		BENE=1
	fi
	# ⭐ LA PROVENIENZA — «la tela e' cambiata?» in una parola, e senza dipendere
	#    dal giro di prima.
	local da
	da=$(sed -n 's/.*tela in vigore alla fine: [0-9]*x[0-9]* da \([A-Z_()]*\).*/\1/p' \
	    "$LAV/$nome-arbitro.txt" | tail -1)
	[ -n "$da" ] || da="(l'arbitro non l'ha detto)"
	if [ "$daatteso" = "?" ]; then
		inf "la tela in vigore alla fine viene da $da   (NON pretesa)"
	elif [ "$da" = "$daatteso" ]; then
		inf "la tela in vigore alla fine viene da $da — come dichiarato"
	else
		ko "⛔ la tela alla fine viene da «$da», e l'atteso era «$daatteso»"
		BENE=1
	fi
	if [ "$telafine" = "?" ]; then
		# ⛔ «?» NON e' «va bene qualunque cosa»: e' «l'atteso e' due, e si
		#    dichiara invece di sceglierne uno».  Il numero si stampa e resta
		#    agli occhi di chi legge — che e' meno di un confronto, e va detto.
		inf "tela in vigore alla fine: $t   ⚠ NON pretesa (due strade legali)"
	elif [ "$t" = "$telafine" ]; then
		inf "tela in vigore alla fine: $t — come dichiarato"
	else
		ko "⛔ tela alla fine: $t, l'atteso era $telafine"
		BENE=1
	fi
	return "$g"
}

# ⛔⛔ E LA TELA DI PARTENZA **NON E' 1920x1080**: e' quella che il giro prima ha
#     lasciato al palco.  `[M]` 21 agosto 2026, primo giro vero: il `SESSIONE`
#     del giro 2 concede **1264x800** — la misura del giro 1 — a un `ATTACCA`
#     che ne chiedeva 1920x1080.  ⇒ La tela **sopravvive alla sessione**, e
#     nessun documento lo diceva.  Per questo qui si pretende la PROVENIENZA e
#     non il numero, dove il numero dipende dall'ordine.
giro "1-tela-all-attacco" 0 1 "1264x800" "TELA(ADATTATA)" \
     "TELA(ADATTATA, 1264x800) — e' la scena di DECISIONI.md §5.0-sexies" -- \
     --adatta 1264x800 --resta 3

giro "2-tela-a-caldo" 0 2 "1600x900" "TELA(ADATTATA)" \
     "due coppie ADATTA_TELA/TELA in ordine, la seconda a sessione viva" -- \
     --adatta 1264x800 --adatta 1600x900@2 --resta 3

# ⛔ Qui il numero NON si pretende — dipende da quel che il giro 2 ha lasciato —
#    ma la REGOLA sì, ed è tutta nella provenienza: se la tela alla fine viene
#    ancora da `SESSIONE`, nessun `TELA(ADATTATA)` l'ha toccata, che è
#    esattamente «la tela INVARIATA» di §7.1 dopo un rifiuto.
giro "3-fuori-limiti" 0 1 "?" "SESSIONE" \
     "TELA(RIFIUTATA, MISURA_FUORI_LIMITI) e la tela INVARIATA — §4.5, §7.1" -- \
     --adatta 8000x4320 --resta 2

# ⚠ Qui l'atteso sulla tela finale e' DUE: o il rifiuto (1920x1080), o una
#   concessione pari (1280x800).  ⛔ Un atteso «uno dei due» non si confronta
#   con una stringa sola, e fingere che ce ne sia uno solo sarebbe scegliere al
#   posto del prodotto — quindi qui il numero si DICHIARA e non si pretende, e
#   la riga lo dice invece di lasciarlo credere.
# ⚠ Qui non si pretende NE' il numero NE' la provenienza: §4.5 lascia al server
#   due strade tutt'e due legali — rifiutare il dispari (la tela resta, viene da
#   SESSIONE) o concedere il pari piu' vicino (viene da TELA(ADATTATA)).  ⛔ E
#   sceglierne una al posto del prodotto sarebbe scrivere la specifica qui.
giro "4-lato-dispari" 0 1 "?" "?" \
     "⭐ o TELA(RIFIUTATA, MISURA_FUORI_LIMITI), o una tela concessa PARI: §4.5 vieta il dispari.  ⚠ Ne' il numero ne' la provenienza si pretendono: sono due strade tutt'e due legali" -- \
     --adatta 1281x800 --resta 2

giro "5-vista-non-tocca-la-tela" 0 1 "1264x800" "TELA(ADATTATA)" \
     "nessun TELA dopo la VISTA — §7.1: «VISTA NON DEVE far cambiare la tela».  ⛔ E la tela alla fine DEVE essere ancora 1264x800, quella dell'ADATTA_TELA: se la VISTA l'avesse cambiata, questo numero lo direbbe" -- \
     --adatta 1264x800 --vista 640x401 --resta 3

# ---------------------------------------------------------------------------
# ⛔ IL BAN SI SBLOCCA, E SI DICHIARA — regola B0.3.  Questo banco autentica,
#    quindi puo' bannare: senza lo sblocco dichiarato, «il ban non e' scattato»
#    e «qualcuno l'ha tolto» hanno la stessa faccia.
log "6. Lo sblocco dell'indirizzo — §4.4-bis, e si DICHIARA"
dentro "python3 $DENTRO_ALB/banchi/01-b8-sblocca.py --socket $DENTRO_LAV/comando.sock --ping"
inf "ping al socket del comando: uscita $?"
dentro "python3 $DENTRO_ALB/banchi/01-b8-sblocca.py --socket $DENTRO_LAV/comando.sock $IND"
inf "sblocco di $IND: uscita $?"

log "Esito"
inf "⛔ e si rilegge: «conforme» NON e' «funziona» — vedi l'intestazione"
if [ "$BENE" -eq 0 ]; then
	ok "⭐ tutti i giri della tela sono conformi a RCP.md sui byte"
else
	ko "⛔ qualcosa non e' conforme: il byte e la regola stanno sopra"
fi
exit "$BENE"
