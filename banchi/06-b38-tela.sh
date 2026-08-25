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
#   · ⭐⛔ **E DAL 22 AGOSTO 2026 LA REGOLA DEL SECONDO E' ESERCITATA, non
#     solo arbitrabile.**  Qui c'era scritto: *«questi cinque giri non mandano
#     nessun `PUNTATORE`: la regola del secondo di grazia e' arbitrabile ma qui
#     non e' esercitata»*.  ⇒ Adesso ci sono il **sesto** e il **settimo**
#     giro: una coordinata della tela vecchia a **1,5 s** (oltre il secondo:
#     il server DEVE rifiutare) e a **0,25 s** (dentro: il server DEVE saturare
#     e l'arbitro DEVE dire «non giudicabile»);
#   · ⛔⛔ **E IL METRO FINALE NON E' L'ARBITRO: E' DOVE E' FINITO IL
#     PUNTATORE.**  Un server che rifiutasse la coordinata *dicendolo nel
#     registro* e la applicasse lo stesso passerebbe l'arbitro — §7.1 giudica
#     byte, e i byte non sanno niente del compositore.  ⇒ I giri 6 e 7 leggono
#     **due testimoni in piu'**, e nessuno dei due e' il filo di controllo:
#       · il **registro del server**, dove c'e' la riga con le coordinate
#         **iniettate** — cioe' il punto d'arrivo, dopo la saturazione;
#       · il campo **`input` di §6.2** nelle intestazioni dei fotogrammi, che
#         porta *«l'identificatore dell'ultimo input INIETTATO»*: e' il filo
#         che contraddice il filo, e lo legge `06-b38-puntatore.py`;
#   · ⭐⛔⛔ **E IL BANCO SA VEDERE IL DIFETTO — `[M]` 22 agosto 2026, e il
#     numero che conta e' che l'ARBITRO DA SOLO NON LO VEDE.**
#
#     Controllo positivo (`PIANO.md` §0.3 punto 4), su un server **guasto
#     apposta**: una copia dell'albero con `#define TELA_GRAZIA 60000` al posto
#     di `1000` in `src/rcp.c` **e** in `banchi/rcp/rcp.c` (il gemello, o il
#     Makefile si rifiuta di compilare), costruita e accesa sulla 7722 con un
#     `LAV` suo.  ⇒ Un server che **perdona per un minuto** invece che per un
#     secondo.
#
#     `[M]` Il sesto giro contro quel server:
#       · il `PUNTATORE` a 1501 ms viene **INIETTATO**: il registro dice
#         *«SATURATA a (799,599) … sono passati 1521 ms su 60000»*;
#       · ⛔⛔ **l'arbitro esce 0 e dichiara ⭐ CONFORME.**  Dice *«oltre il
#         secondo — ma dopo di lui il server non dice piu' niente e la
#         registrazione finisce: NON si giudica se abbia chiuso o taciuto»* —
#         onesto, e verde.  ⚠ Perche' §7.1 lo fa concludere **solo** se il
#         server parla ancora sul canale di CONTROLLO dopo il puntatore tardo,
#         e un server indulgente che tace non gliene da' l'occasione;
#       · ⭐ e il banco esce **1**, su **cinque** righe rosse: l'uscita del
#         cliente (0 invece di 4), la frase che l'arbitro NON ha detto, la riga
#         di rifiuto che il registro NON porta, il campo `input = 1` di §6.2,
#         e `DOVE_E_FINITO 799,599`;
#       · ⚠ e il **settimo** giro contro lo stesso server guasto resta
#         **verde**, com'e' giusto: 250 ms stanno dentro tutt'e due le grazie.
#         Un banco che diventasse rosso dappertutto non starebbe misurando.
#
#     ⇒ ⛔ **La riga da ricordare**: su questa regola «l'arbitro dice conforme»
#        NON e' una misura.  Quel che tiene sono i due testimoni qui sopra, e
#        vanno letti tutt'e due.
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
	inf "il cliente esce $e   (0 = a posto · 4 = caduta · 5 = ⛔ nessun TELA · 6 = ⛔ scena non esercitabile)"
	[ "$e" = 6 ] && ko "   ⛔ 6 = la scena chiesta NON e' esercitabile: il giro non ha misurato niente"
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

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⛔⛔ IL SESTO E IL SETTIMO GIRO — IL SECONDO DI GRAZIA DI §7.1, PUNTATO
#       CONTRO IL SERVER.  22 agosto 2026.
#
# §7.1: *«Dopo aver mandato `TELA(ADATTATA)` il server DEVE accettare per **un
# secondo** coordinate di input valide sulla tela **precedente**, saturandole
# alla nuova e scrivendolo nel registro; passato quel secondo, sono
# `ERRORE_PROTOCOLLO`»*.
#
# ⛔⛔ LA TRAPPOLA, DISINNESCATA PRIMA DI SCEGLIERE I DUE ISTANTI.
#
#      La regola e' del **SERVER**; la registrazione la prende il **CLIENT**.
#      §11.1: *«Una registrazione presa al client vede quando e' ARRIVATO il
#      `TELA` e quando e' PARTITO il `PUNTATORE`: un intervallo piu' CORTO di
#      quello che il server ha misurato, di mezzo giro di rete per lato»*.
#
#      ⇒ Il confine e' asimmetrico, e i due errori non si somigliano:
#        · un caso «oltre» a 1,5 s e' **sicuro**, perche' l'intervallo del
#          server e' ancora piu' lungo: 1,5 s qui non puo' essere 0,9 s la';
#        · un caso «dentro» a 0,95 s **non lo e'**: con 60 ms di giro di rete
#          il server ne misura 1,01 e rifiuta — e il banco darebbe il rosso a
#          un prodotto che ha ragione.
#
# ⭐ ⇒ I DUE ISTANTI SONO SCELTI LONTANI DAL CONFINE, E SI DICHIARA QUANTO:
#      **1500 ms** (margine +500 ms) e **250 ms** (margine −750 ms, cioe' ci
#      vorrebbe un giro di rete di 750 ms su una LAN per portarlo oltre).
#
# ⭐⭐ E L'ASIMMETRIA NON E' PIU' UN RAGIONAMENTO: E' MISURATA — 22 agosto 2026.
#
#    §11.1 dice che l'intervallo del server e' **piu' lungo**; qui si vede di
#    quanto, perche' i due numeri esistono tutt'e due — il `dt` della traccia e
#    quello che il server scrive di suo nel registro (*«sono passati N ms su
#    1000»*, *«scaduto da N ms»*).  ⛔ Nove coppie, carico 1,0-1,6 (otto agenti
#    sulla macchina), su LAN:
#
#      | client |  server | differenza |
#      |   251  |    262  |    +11     |
#      |   252  |    265  |    +13     |
#      |  1502  |   1516  |    +14     |
#      |  1501  |   1515  |    +14     |
#      |   252  |    270  |    +18     |
#      |  1501  |   1521  |    +20     |
#      |  1501  |   1521  |    +20     |
#      |   251  |    272  |    +21     |
#      |  1501  |   1526  |    +25     |
#
#    ⇒ **Il segno e' sempre lo stesso** (9 su 9: il server misura di piu'), e la
#      grandezza sta fra **11 e 25 ms**.  ⚠ E il numero non si estrapola: e' di
#      QUESTA rete e di QUESTO carico.  Vale a giustificare i margini scelti —
#      500 e 750 ms sono venti volte il peggiore — **non** a spostarli piu'
#      vicino al confine.  ⛔ Un caso «dentro» a 0,99 s sarebbe a 1,01 s per il
#      server nel giro peggiore di questi nove: rosso su un prodotto che ha
#      ragione.
#      ⚠ Il margine lo stampa `06-b38-puntatore.py` a ogni giro, letto dagli
#        `istante_ms` VERI: se un giorno la rete o il carico lo mangiassero, si
#        vedrebbe **prima** del verdetto invece di dopo.
#
# ⛔ E LA COORDINATA NON E' SCELTA QUI: la calcola il cliente, ed e' l'ULTIMO
#    PIXEL della tela precedente — `(1264-1, 800-1)` = `(1263,799)`.  Due
#    ragioni:
#      · e' valida sulla tela di prima **per definizione** (§7.3), quindi la
#        scena e' quella di §7.1 e non «una coordinata sbagliata», che §7.1
#        NON copre e per cui il server ha una riga di registro diversa;
#      · saturata, deve finire **esattamente** su `(800-1, 600-1)` =
#        `(799,599)` — un punto NOTO.  ⭐ E' il controllo che attraversa la
#        conversione delle coordinate, come in `banchi/07-b51-due-browser.py`.
# ═══════════════════════════════════════════════════════════════════════════

REGISTRO=$LAV/registro.log
marca_log() { sudo_mio stat -c %s "$REGISTRO" 2>/dev/null || echo 0; }
log_da()    { sudo_mio tail -c "+$(( ${1:-0} + 1 ))" "$REGISTRO" 2>/dev/null; }

# ⛔ La riga di registro che dice **dove e' finito il puntatore**: `rcp.c`
#    scrive «input id=N (era M) PUNTATORE (x,y)» con le coordinate GIA'
#    saturate, e questa e' la sola grandezza che attraversa la conversione.
#    ⚠ L'ancora e' `input id=`, non la sola parola `PUNTATORE`: nel registro
#      quella parola compare anche nelle righe di RIFIUTO, e cercarla nuda
#      darebbe un «e' arrivato» su un input che e' stato buttato.  E' la
#      trappola dello `strstr` nudo, gia' pagata su questi file.
dove_e_finito() {
	sed -n 's/.*input id=[0-9]* (era [0-9]*) PUNTATORE (\([0-9]*,[0-9]*\)).*/\1/p' \
	    | tail -1
}

# ── il denominatore del filo, e i due testimoni in piu' ────────────────────
# ⛔ Non e' un secondo giudice: il verdetto su §7.1 resta dell'arbitro.  Questi
#    numeri dicono **se la scena e' avvenuta** e **dove e' finito il
#    puntatore** — le due domande che «conforme» non risponde.
grazia() # nome · dt-atteso · punto-atteso · frase-dell-arbitro · marca · riga-del-registro-attesa · input-nei-fotogrammi
{
	local nome=$1 dtatteso=$2 puntoatteso=$3 frase=$4 marca=$5 rigattesa=$6
	local inpatteso=$7
	local T=$LAV/$nome.rcpreg
	log "   ⤷ i due testimoni del giro «$nome»"
	if [ ! -f "$T" ]; then
		ko "⛔ nessuna traccia: non si giudica niente"; BENE=1; return 1
	fi
	python3 "$ALB/banchi/06-b38-puntatore.py" "$T" 2>&1 \
	    | tee "$LAV/$nome-puntatore.txt" | sed 's/^/    | /'

	# 1. la scena e' avvenuta?
	local scena dt sat
	scena=$(sed -n 's/^PUNT_SCENA \(.*\)/\1/p' "$LAV/$nome-puntatore.txt" | tail -1)
	dt=$(sed -n 's/^PUNT_DT \(.*\)/\1/p' "$LAV/$nome-puntatore.txt" | tail -1)
	sat=$(sed -n 's/^PUNT_SATURAZIONE_ATTESA \(.*\)/\1/p' "$LAV/$nome-puntatore.txt" | tail -1)
	if [ "$scena" != "si" ]; then
		ko "⛔ la scena di §7.1 NON e' avvenuta: nessun PUNTATORE nella traccia"
		BENE=1; return 1
	fi
	ok "la scena c'e': un PUNTATORE dopo il TELA(ADATTATA)"
	# ⛔ Il `dt` si CONFRONTA, e con una tolleranza dichiarata: fra il momento
	#    in cui il cliente decide e quello in cui il byte parte passa del
	#    tempo, e sotto carico ne passa di piu'.  ⚠ 200 ms e' largo di
	#    proposito — serve a vedere un ritardo *sbagliato di scala*, non a
	#    misurare la latenza: quel che tiene la regola e' il margine dal
	#    confine (500 e 750 ms), non la precisione di questo confronto.
	local basso=$((dtatteso - 200)) alto=$((dtatteso + 200))
	if [ "$dt" -ge "$basso" ] && [ "$dt" -le "$alto" ]; then
		inf "dt registrato $dt ms (atteso $dtatteso ± 200) — e il margine dal secondo sta qui sopra"
	else
		ko "⛔ dt registrato $dt ms, e l'atteso era $dtatteso ± 200: il giro NON ha esercitato l'istante che dichiarava"
		BENE=1
	fi
	if [ "$sat" != "$puntoatteso" ]; then
		ko "⛔ la saturazione attesa e' ($sat) e il giro dichiarava ($puntoatteso): le tele non sono quelle che credevo"
		BENE=1
	fi

	# 2. che cosa dice l'ARBITRO su §7.1 — ⛔ e NON basta che esca 0.
	#    `[M]` 22 agosto 2026, su registrazioni costruite: un PUNTATORE oltre
	#    il secondo dopo cui il server **tace** fa uscire l'arbitro **0**
	#    esattamente come uno dopo cui il server **congeda**.  ⇒ Leggere solo
	#    il codice d'uscita darebbe verde a «non si giudica».
	if grep -aqF "$frase" "$LAV/$nome-arbitro.txt"; then
		ok "⭐ l'arbitro dice quel che il giro pretendeva: «$frase»"
	else
		ko "⛔ l'arbitro NON dice «$frase» — e senza quella frase l'uscita 0 vuol dire «non ho giudicato»"
		BENE=1
	fi

	# 3. ⭐⛔ IL REGISTRO DEL SERVER — dove e' finito il puntatore
	local coda arrivo
	coda=$(log_da "$marca")
	printf '%s\n' "$coda" | grep -aE 'grazia|GRAZIA|PUNTATORE|congedo motivo|input id=' \
	    | sed 's/^/    | /' | tail -20
	if printf '%s\n' "$coda" | grep -aqE "$rigattesa"; then
		ok "⭐ il registro del server porta la riga attesa"
	else
		ko "⛔ il registro del server NON porta «$rigattesa»"
		BENE=1
	fi
	arrivo=$(printf '%s\n' "$coda" | dove_e_finito)
	printf 'DOVE_E_FINITO %s\n' "${arrivo:-nessuna-iniezione}"

	# 4. ⭐⛔ IL TERZO TESTIMONE, E STA SUL FILO: il campo `input` di §6.2.
	#    *«L'identificatore dell'ultimo input INIETTATO prima della cattura»*.
	#    ⇒ E' il filo che contraddice il filo: un server che rifiutasse a
	#      parole e iniettasse nei fatti lo direbbe QUI, in un campo che
	#      nessun altro controllo guarda.
	local fi fd
	fi=$(sed -n 's/^FOT_INPUT \(.*\)/\1/p' "$LAV/$nome-puntatore.txt" | tail -1)
	fd=$(sed -n 's/^FOT_DOPO \(.*\)/\1/p' "$LAV/$nome-puntatore.txt" | tail -1)
	# ⛔ L'uno si cerca come ELEMENTO dell'elenco, non come sottostringa: con un
	#    `grep 1` nudo il valore «10» o «21» direbbe di si'.  E' la trappola
	#    dello `strstr` nudo — gia' pagata su questi file con «scaduto da 1500
	#    ms» che combaciava con «500».
	case "$inpatteso" in
	"1")
		if printf '%s' "$fi" | grep -qE '(^|,)1(,|$)'; then
			ok "⭐ §6.2: un fotogramma dopo il PUNTATORE dichiara «input = 1» — l'iniezione e' scritta sul FILO, non solo nel registro del server"
		else
			ko "⛔ nessun fotogramma dichiara «input = 1» ($fd fotogrammi dopo, campo «input» = $fi): o non e' stato iniettato, o non e' passato niente"
			BENE=1
		fi ;;
	"no-1")
		if [ "$fd" = 0 ]; then
			inf "⚠ zero fotogrammi dopo il PUNTATORE: il campo «input» NON puo' dire niente — e si dichiara, invece di leggerlo come un no"
		elif printf '%s' "$fi" | grep -qE '(^|,)1(,|$)'; then
			ko "⛔⛔ un fotogramma dichiara «input = 1» DOPO un PUNTATORE che il server dice di aver rifiutato: §7.1 detta e non fatta"
			BENE=1
		else
			ok "⭐ nessun fotogramma dichiara «input = 1» ($fd dopo il PUNTATORE): il rifiuto e' vero anche sul filo"
		fi ;;
	esac
	return 0
}

M6=$(marca_log)
# ⛔ ATTESO DEL CLIENTE = **4**, e non 0: §7.1 dice «passato quel secondo, sono
#    ERRORE_PROTOCOLLO», e §3 dice che un errore di protocollo CHIUDE.  ⇒ Un
#    cliente che restasse attaccato sarebbe la prova che il server ha
#    perdonato.  ⚠ E l'atteso si dichiara qui, prima di guardare.
giro "6-grazia-scaduta" 4 2 "?" "TELA(ADATTATA)" \
     "⭐ un PUNTATORE (1263,799) — valido sulla tela vecchia 1264x800, fuori dalla nuova — a 1500 ms dal TELA(ADATTATA): OLTRE il secondo di §7.1, e il server DEVE chiudere con ERRORE_PROTOCOLLO.  ⛔ E NIENTE DEVE ESSERE INIETTATO" -- \
     --adatta 1264x800 --adatta 800x600@1 --puntatore-vecchia 1.5 \
     --chiave-dopo 1 --resta 5
grazia "6-grazia-scaduta" 1500 "799,599" \
       "oltre il secondo — e il server ha CONGEDATO" "$M6" \
       "PUNTATORE id=[0-9]+ a \(1263,799\).*secondo di grazia di §7\.1 e' scaduto" \
       "no-1"
# ⛔ E IL CONTROLLO CHE L'ARBITRO NON PUO' FARE: nessuna iniezione.  Un server
#    che scrivesse il rifiuto e iniettasse lo stesso uscirebbe conforme.
A6=$(log_da "$M6" | dove_e_finito)
if [ -z "$A6" ]; then
	ok "⭐ NESSUNA iniezione dopo il rifiuto: il puntatore non e' finito da nessuna parte"
else
	ko "⛔⛔ il server ha RIFIUTATO a parole e INIETTATO in ($A6): §7.1 detta e non fatta"
	BENE=1
fi

M7=$(marca_log)
giro "7-grazia-dentro-il-secondo" 0 2 "?" "TELA(ADATTATA)" \
     "⭐ lo stesso PUNTATORE (1263,799) a 250 ms: DENTRO il secondo.  Il server DEVE saturarlo a (799,599) e scriverlo nel registro, la sessione DEVE reggere, e ⛔ l'arbitro DEVE dire «NON e' giudicabile» invece di assolvere" -- \
     --adatta 1264x800 --adatta 800x600@1 --puntatore-vecchia 0.25 \
     --chiave-dopo 1 --resta 5
grazia "7-grazia-dentro-il-secondo" 250 "799,599" \
       "NON e' giudicabile da questa registrazione" "$M7" \
       "§7\.1 SECONDO DI GRAZIA \([0-9]+-esima volta\): input id=[0-9]+ porta \(1263,799\).*SATURATA a \(799,599\)" \
       "1"
# ⭐⛔ E QUESTO E' IL METRO FINALE: dove e' finito il puntatore.
A7=$(log_da "$M7" | dove_e_finito)
if [ "$A7" = "799,599" ]; then
	ok "⭐⭐ IL PUNTATORE E' FINITO IN ($A7) — l'ultimo pixel della tela nuova, come §7.1 vuole"
elif [ -z "$A7" ]; then
	ko "⛔ nessuna iniezione: la grazia e' stata scritta nel registro e NON fatta"
	BENE=1
else
	ko "⛔⛔ il puntatore e' finito in ($A7) invece che in (799,599): la saturazione di §7.1 e' sbagliata"
	BENE=1
fi

# ---------------------------------------------------------------------------
# ⛔ IL BAN SI SBLOCCA, E SI DICHIARA — regola B0.3.  Questo banco autentica,
#    quindi puo' bannare: senza lo sblocco dichiarato, «il ban non e' scattato»
#    e «qualcuno l'ha tolto» hanno la stessa faccia.
log "8. Lo sblocco dell'indirizzo — §4.4-bis, e si DICHIARA"
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
