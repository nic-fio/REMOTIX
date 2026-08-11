#!/bin/bash
#
# 01-b8-lancia.sh — gira SUL SERVER.  B8: il secondo fisso, e IL BAN dell'indirizzo.
#
#   bash /media/REMOTIX/src/01-b8-lancia.sh              10 blocchi = 20 campioni/caso
#   bash /media/REMOTIX/src/01-b8-lancia.sh 3            un giro corto, per provare il banco
#   bash /media/REMOTIX/src/01-b8-lancia.sh previsione   che cosa mi aspetto, senza misurare
#   bash /media/REMOTIX/src/01-b8-lancia.sh costruisci   rimette gli innesti e ricompila
#
# ---------------------------------------------------------------------------
# ⛔ CHE COSA MISURA — e la spiegazione lunga sta in `01-b8-cronometro.py`
#
# `RCP.md` §4.4 vieta di distinguere nel MOTIVO fra «utente inesistente» e
# «parola sbagliata».  §4.4-bis impone il **ritardo fisso di un secondo** perche'
# quella distinzione non si legga col **cronometro**, e — dal 10 agosto 2026,
# per decisione dell'utente — **il ban dell'indirizzo**: tre autenticazioni
# fallite dallo stesso indirizzo dentro cinque minuti, e quell'indirizzo e' fuori
# per dodici ore.
#
# ---------------------------------------------------------------------------
# ⛔ DUE VITE DEL SERVER, NON DODICI — e questa e' la differenza piu' grande
#
# La forma precedente di questo banco spegneva e riaccendeva il processo **a
# ogni blocco**, e lo scriveva in testa al file: *«l'unico modo di ripartire da
# contatori azzerati e' un processo nuovo — `rcp_azzera_registro_sessioni()`
# esiste ma non la chiama nessuno»*.  ⭐ Adesso la chiama qualcuno: §4.4-bis
# vuole un **comando di sblocco**, l'11 agosto 2026 e' nato lato ospite, e
# `01-b8-sblocca.py` e' il lato di chi comanda.
#
# Le due vite che restano hanno una ragione ciascuna:
#
#   la prima    i campioni del secondo fisso, e tutto il giro del ban;
#   la seconda  ⛔ **solo** per provare che il ban SOPRAVVIVE al riavvio —
#               invariante I7, e senza quella riga il ban vive in memoria e un
#               aggiornamento del pacchetto regala tre tentativi a chiunque.
#
# ⛔ E LO SBLOCCO NON SI CHIAMA MAI DENTRO IL GIRO DEL BAN (regola B0.3): gli
#    sblocchi di questo banco sono in tre posti, tutti dichiarati e tutti
#    stampati — prima di cominciare, fra un blocco di campioni e l'altro, e in
#    fondo, dove lo sblocco non e' un attrezzo ma **la cosa provata**.
#
# ---------------------------------------------------------------------------
# ⛔ E PERCHE' IL SERVER SI ACCENDE SU 0.0.0.0
#
# Il conto di §4.4-bis e' **per indirizzo di provenienza**.  Su `0.0.0.0` la
# stessa macchina raggiunge il server come `127.0.0.1` e come `192.168.0.2`: due
# chiavi diverse, due fallimenti ciascuna per blocco, e il margine sotto la
# soglia di tre.  ⭐ E non si crede sulla parola: il registro del server scrive
# `da=<indirizzo>:<porta>`, e il verdetto **conta quanti indirizzi distinti ha
# visto il server** (`LEZIONI.md` §1.9: un denominatore si legge dove la cosa
# succede).
#
# ⛔ Nessuna redirezione ATTORNO a `enter.sh` (si porterebbe via la richiesta di
#    password di sudo) e nessuna sottoshell in secondo piano: la regola del 10
#    agosto 2026, pagata quattro volte.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
WT="$FUORI/01-b2-lancia-wt.sh"
SORG=$DENTRO/b2/ngtcp2/examples/http3_server_proto_codec.cc
SORG_MAIN=$DENTRO/b2/ngtcp2/examples/server.cc
SERVER=$DENTRO/b2/ngtcp2/build/examples/bsslserver
PORTA=7447
LEGAME=0.0.0.0
INDIRIZZI=127.0.0.1,192.168.0.2
# ⛔ Le due strade del padrone di casa (§4.4-bis), passate al server come
#    opzioni: dove stanno i ban fra un riavvio e l'altro, e da dove si comanda
#    di toglierne uno.
BAN_FILE=$DENTRO/b8-ban.txt
COMANDO=$DENTRO/b8-comando.sock
PER_CASO=2          # terzine per blocco: 2 fallimenti per indirizzo, soglia 3
# ⛔ E LE CREDENZIALI STANNO QUI, IN CHIARO E ACCANTO A QUELLE DEGLI ALTRI
#    BANCHI.  Fino all'11 agosto 2026 questo banco si portava dentro il proprio
#    valore predefinito — `prova` — mentre `01-b3-lancia.sh`, `01-b6-lancia.sh` e
#    `01-b7-lancia.sh` usano tutti e tre `parola-di-prova`: nessuna
#    autenticazione di B8 e' mai riuscita, e il caso «giusta» era una copia del
#    caso «sbagliata».  ⚠ Un valore predefinito nascosto in un altro file e' un
#    valore che nessuno confronta.
UTENTE=prova
PAROLA=parola-di-prova

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

AZIONE=${1:-10}

# ---------------------------------------------------------------------------
log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

if [ "$AZIONE" = previsione ]; then
	bash "$ENTRA" --root "python3 $DENTRO/01-b8-cronometro.py --previsione"
	exit 0
fi

# ---------------------------------------------------------------------------
# ⛔ `costruisci` — e sta qui perche' l'11 agosto 2026 l'innesto e' cambiato: il
#    ban lato ospite vive in `server.cc`, che fino a ieri questo innesto non
#    toccava.  Un binario di ieri non ha ne' la pagina in TCP ne' il comando di
#    sblocco, e il sintomo sarebbe «il banco non riesce a sbloccare» — cioe' il
#    rosso sull'imputato sbagliato.
if [ "$AZIONE" = costruisci ]; then
	log "1. Gli innesti si tolgono e si rimettono"
	inf "⛔ applicarne uno sopra l'altro lascerebbe due copie dello stesso"
	inf "   codice, e la seconda non si vede"
	bash "$ENTRA" --root "python3 $DENTRO/01-b3-rcp-innesta.py --togli > /dev/null"
	bash "$ENTRA" --root "python3 $DENTRO/01-b2-ngtcp2-wt-innesta.py --togli > /dev/null"
	bash "$ENTRA" --root "python3 $DENTRO/01-b2-ngtcp2-wt-innesta.py" \
		| grep -E "appiglio|righe|CODICE" | sed 's/^/        /'
	bash "$ENTRA" --root "python3 $DENTRO/01-b3-rcp-innesta.py" \
		| grep -E "appiglio|NO |file nostri" | sed 's/^/        /'
	# ⛔ E si CONTA l'innesto nei due file, prima di compilare: un innesto che
	#    non trova un appiglio stampa «NO» e va avanti.
	QUANTI=$(bash "$ENTRA" --root "grep -c 'REMOTIX B3' $SORG_MAIN" | tr -cd '0-9')
	if [ "${QUANTI:-0}" -lt 5 ]; then
		ko "⛔ il ban lato ospite NON e' in server.cc (righe «REMOTIX B3»: ${QUANTI:-0})"
		ko "   si compilerebbe un server senza pagina in TCP e senza comando di"
		ko "   sblocco, e B8 darebbe rosso su cose che il server non ha mai avuto"
		exit 3
	fi
	ok "il ban lato ospite e' in server.cc ($QUANTI righe «REMOTIX B3»)"
	log "2. Si compila"
	rm -f "$FUORI/b8-compila.log"
	if ! bash "$ENTRA" --root \
		"ninja -C $DENTRO/b2/ngtcp2/build bsslserver > $DENTRO/b8-compila.log 2>&1"; then
		ko "la compilazione e' fallita:"
		if [ -f "$FUORI/b8-compila.log" ]; then
			tail -30 "$FUORI/b8-compila.log" | sed 's/^/        /'
		else
			ko "   ⛔ e il registro di compilazione NON ESISTE: non e' ninja che"
			ko "      ha taciuto, e' che non si e' arrivati a lanciarlo"
		fi
		exit 3
	fi
	ok "compilato — adesso rilancia «01-b8-lancia.sh <blocchi>»"
	exit 0
fi

case "$AZIONE" in
	''|*[!0-9]*)
		ko "argomento sconosciuto: «$AZIONE»  (un numero | previsione | costruisci)"
		exit 2 ;;
esac
BLOCCHI=$AZIONE
if [ "$BLOCCHI" -lt 1 ]; then
	ko "zero blocchi: non c'e' niente da misurare, e non e' «tutto passato»"
	exit 2
fi

# ---------------------------------------------------------------------------
# ⛔ LO STATO INIZIALE SI DICHIARA E SI VERIFICA — B0.1.
#
#    ⛔ E qui lo stato che sopravvive di piu' e' IL FILE DEI BAN: dal 10 agosto
#       2026 sta su disco, quindi sopravvive anche al riavvio del server (B0.2).
#       Un ban di ieri renderebbe rosso tutto quel che segue, e il rosso
#       finirebbe sull'imputato sbagliato — quindi il file si BUTTA, e lo si
#       dice.  ⚠ E' un banco: in produzione buttare quel file e' togliere la
#       protezione a tutti.
log "1. Lo stato iniziale"
GIRO=$(date +%Y%m%d-%H%M%S)
rm -f "$FUORI/b8-fatti.jsonl" "$FUORI/b8-server.log" "$FUORI/b8-stato.txt"
bash "$ENTRA" --root "rm -f $BAN_FILE $BAN_FILE.nuovo $COMANDO"
inf "giro: $GIRO"
inf "blocchi: $BLOCCHI  ·  campioni tenuti per caso: $((BLOCCHI * PER_CASO))"
inf "⛔ buttato il file dei ban «$BAN_FILE» (B0.2: e' lo stato che sopravvive"
inf "   di piu' fra tutti — al riavvio del server compreso)"
inf "⚠ vite del server: 2 (una per i campioni e il ban, una per la persistenza)"
inf "⚠ durata dell'ordine di $(( BLOCCHI * 6 * 4 / 60 + 2 ))–$(( BLOCCHI * 6 * 6 / 60 + 4 )) minuti"
inf "⚠ e fa $((BLOCCHI * 4 + 9)) autenticazioni FALLITE sull'utente di prova: se un"
inf "  giorno la pila PAM avesse un pam_faillock, quell'utente si bloccherebbe"

# ⛔ CHE SERVER E' QUELLO CHE STO PER ACCENDERE — e adesso i file sono DUE.
#    Un binario senza l'innesto di RCP non risponderebbe a `CIAO`; uno senza il
#    ban lato ospite non servirebbe nessuna pagina in TCP e non aprirebbe nessun
#    socket di comando.  ⚠ Un binario piu' VECCHIO del sorgente innestato e' un
#    binario che quell'innesto non ce l'ha (`LEZIONI.md` §1.9, ottava veste).
bash "$ENTRA" --root \
	"{ grep -c 'REMOTIX B3' $SORG; grep -c 'REMOTIX B3' $SORG_MAIN; stat -c %Y $SORG; stat -c %Y $SORG_MAIN; stat -c %Y $SERVER; stat -c %y $SERVER; } > $DENTRO/b8-stato.txt 2>&1"
if [ ! -f "$FUORI/b8-stato.txt" ]; then
	ko "non ho potuto guardare lo stato del server: il file non e' stato scritto"
	exit 2
fi
INNESTO=$(sed -n 1p "$FUORI/b8-stato.txt")
OSPITE=$(sed -n 2p "$FUORI/b8-stato.txt")
T_SORG=$(sed -n 3p "$FUORI/b8-stato.txt")
T_MAIN=$(sed -n 4p "$FUORI/b8-stato.txt")
T_BIN=$(sed -n 5p "$FUORI/b8-stato.txt")
QUANDO=$(sed -n 6p "$FUORI/b8-stato.txt")
case "$INNESTO$OSPITE" in
	''|*[!0-9]*) ko "non ho potuto contare l'innesto di RCP nei sorgenti:"
	             sed 's/^/        /' "$FUORI/b8-stato.txt"; exit 2 ;;
esac
if [ "$INNESTO" -lt 3 ]; then
	ko "⛔ l'innesto di RCP NON e' nel codec ($INNESTO righe «REMOTIX B3»)"
	ko "   questo server non parla RCP: «01-b8-lancia.sh costruisci»"
	exit 3
fi
if [ "$OSPITE" -lt 5 ]; then
	ko "⛔ il BAN LATO OSPITE non e' in server.cc ($OSPITE righe «REMOTIX B3»)"
	ko "   questo server non serve nessuna pagina in TCP e non ha nessun comando"
	ko "   di sblocco: «01-b8-lancia.sh costruisci»"
	exit 3
fi
ok "l'innesto e' nei due file (codec $INNESTO righe · ospite $OSPITE) · binario del $QUANDO"
if [ "$T_BIN" -lt "$T_SORG" ] || [ "$T_BIN" -lt "$T_MAIN" ]; then
	ko "⛔ il binario e' PIU' VECCHIO di un sorgente innestato: dentro non c'e'"
	ko "   quel che si legge nel .cc.  «01-b8-lancia.sh costruisci»"
	exit 3
fi

# ---------------------------------------------------------------------------
# ⛔ 1-bis. LA CERTIFICAZIONE CHE IL FILO NON PUO' FARE, E SI FA **PRIMA**.
#
# `01-b8-prova-ban.c` prova i tre pezzi del ban che sul filo si vedrebbero solo
# aspettando dodici ore, riavviando una macchina o rompendo i permessi di un
# file che gira da root — dove root i permessi li ignora.
#
# ⛔ RILIEVO A20, 11 agosto 2026: fino a stanotte `grep -rn "01-b8-prova-ban"`
#    su tutto l'albero non trovava **nessun chiamante**.  Una certificazione che
#    nessuno esegue non e' una certificazione: e' un file che dice di essere una
#    prova.  Adesso la chiama questo giro, e il suo stato d'uscita conta.
#
# ⛔ E si esegue da UTENTE NORMALE, non dentro il contenitore: la sezione 4 —
#    «zero ban» contro «non ho potuto leggere» — da root sarebbe verde per
#    costruzione, ed e' precisamente il controllo piu' vuoto di tutti.  Il file
#    lo sa e si fa rosso da se' se lo si lancia da root.
log "1-bis. ⛔ La certificazione fuori dal filo (LEZIONI.md §1.2: PRIMA)"
PB=/tmp/b8-prova-ban.$$
if ! command -v gcc >/dev/null 2>&1; then
	ko "⛔ gcc non c'e' su questa macchina: la certificazione di "
	ko "   01-b8-prova-ban.c NON E' STATA ESEGUITA."
	ko "   ⛔ E non e' «passata»: e' un pezzo di B8 che nessuno ha provato."
	ko "   Cura: lanciarla dove gcc c'e', da utente normale:"
	ko "     gcc -std=c11 -Wall -Wextra -I$FUORI/rcp -o /tmp/pb \\"
	ko "         $FUORI/01-b8-prova-ban.c $FUORI/rcp/rcp.c && /tmp/pb"
	exit 3
fi
if ! gcc -std=c11 -Wall -Wextra -I"$FUORI/rcp" -o "$PB" \
	"$FUORI/01-b8-prova-ban.c" "$FUORI/rcp/rcp.c" 2>"$FUORI/b8-prova-ban.log"; then
	ko "⛔ 01-b8-prova-ban.c non compila contro $FUORI/rcp/rcp.c:"
	tail -20 "$FUORI/b8-prova-ban.log" | sed 's/^/        /'
	ko "   ⚠ e «non compila» NON e' «passa»: l'ottava veste di LEZIONI.md §1.9"
	ko "   dice di guardare l'esito del costruttore, non la presenza del file"
	exit 3
fi
"$PB"
PROVA_BAN=$?
rm -f "$PB"
if [ "$PROVA_BAN" -ne 0 ]; then
	ko "⛔ la certificazione fuori dal filo NON passa (uscita $PROVA_BAN):"
	ko "   finche' e' rossa, i tre pezzi del ban che il filo non vede non sono"
	ko "   provati da niente, e il verde del giro qui sotto vale meno"
	exit 3
fi
ok "certificazione fuori dal filo: passata (il denominatore lo stampa lei)"

# ---------------------------------------------------------------------------
# ⛔ E la previsione si stampa PRIMA dei numeri, o non e' una previsione.
log "2. Che cosa mi aspetto, prima di misurare"
bash "$ENTRA" --root "python3 $DENTRO/01-b8-cronometro.py --previsione"

# ---------------------------------------------------------------------------
CRONO="python3 -u $DENTRO/01-b8-cronometro.py --porta $PORTA \
	--indirizzi $INDIRIZZI --giro $GIRO --comando $COMANDO \
	--utente $UTENTE --parola $PAROLA \
	--uscita $DENTRO/b8-fatti.jsonl"

ACCENDI() # $1 = perche'
{
	bash "$WT" accendi "$LEGAME" "$PORTA" \
		"--ban-file=$BAN_FILE" "--comando-socket=$COMANDO"
	if [ $? -ne 0 ]; then
		ko "il server non si e' acceso per «$1»"
		return 4
	fi
	PID=$(cat "$FUORI/b2-wt.pid" 2>/dev/null)
	# ⛔ E si guarda che cosa ha DETTO all'avvio sul ban: «zero ban» e «non ho
	#    potuto leggere il file» sono due fatti diversi, e la riga che li
	#    distingue e' l'unica prova che la persistenza e' accesa.
	#
	# ⛔ RILIEVO A21, 11 agosto 2026: fino a stanotte questa parte STAMPAVA e
	#    non confrontava niente — «si stampa *e* si confronta, e lo stato
	#    d'uscita e' quello del confronto» (B0.4) — e se il registro non fosse
	#    esistito `grep` avrebbe scritto su stderr e lo script sarebbe
	#    proseguito senza una parola.  Cioe' l'accensione dichiarava, nel
	#    commento due righe piu' su, un controllo che non faceva: le due cose
	#    che quel commento dice di distinguere restavano indistinte proprio li'.
	#    ⚠ Il verdetto poi le guarda (`leggi_registro`), ma chi legge il giro
	#      dal vivo crede a questa riga, ed e' un'ora prima.
	inf "quel che ha detto del ban all'avvio (stampato E confrontato — B0.4):"
	if [ ! -f "$FUORI/b2-wt.log" ]; then
		ko "⛔ il registro del server NON ESISTE ($FUORI/b2-wt.log): non e' «il"
		ko "   server non ha detto niente sul ban», e' che non ho potuto guardare"
		return 4
	fi
	grep -E "ban caricati|NON HO POTUTO LEGGERE il file dei ban|ban lato ospite|pagina e' servita|comando di sblocco" \
		"$FUORI/b2-wt.log" | sed 's/^/        /'
	CARICHI=$(grep -c "ban caricati:" "$FUORI/b2-wt.log")
	ILLEGGIBILI=$(grep -c "NON HO POTUTO LEGGERE il file dei ban" "$FUORI/b2-wt.log")
	SOCKET=$(grep -c "il comando di sblocco ascolta su" "$FUORI/b2-wt.log")
	if [ "$ILLEGGIBILI" -gt 0 ]; then
		ko "⛔ il server dichiara di NON aver potuto leggere il file dei ban."
		ko "   ⛔ Questo NON e' «zero ban»: la persistenza di §4.4-bis parte da"
		ko "   uno stato ignoto, e ogni riga sul ban che segue vale meno di zero"
		return 4
	fi
	if [ "$CARICHI" -eq 0 ]; then
		ko "⛔ il server non ha detto NIENTE sul ban all'avvio (nessuna riga"
		ko "   «ban caricati:» e nessuna riga «NON HO POTUTO LEGGERE»)."
		ko "   ⛔ E' proprio la coppia che questo controllo esiste per separare:"
		ko "   senza una delle due, «zero ban» e «non ho potuto guardare» hanno"
		ko "   la stessa faccia (LEZIONI.md §1.9 regola 1)"
		return 4
	fi
	ok "il server ha dichiarato lo stato del ban: $CARICHI righe «ban caricati:»"
	ok "   e 0 righe «non ho potuto leggere» — sono due fatti, e sono distinti"
	if [ "$SOCKET" -eq 0 ]; then
		ko "⛔ il comando di sblocco NON e' in ascolto: «$COMANDO» non e' nato."
		ko "   Senza, ogni sblocco di questo giro esce 3 e B0.3 non si applica —"
		ko "   e il sintomo, piu' avanti, sarebbe «il banco non riesce a"
		ko "   sbloccare», cioe' il rosso sull'imputato sbagliato"
		return 4
	fi
	ok "il comando di sblocco ascolta (B0.3 ha lo strumento che pretende)"
	return 0
}

SPEGNI()
{
	printf '\n===== %s =====\n' "$1" >> "$FUORI/b8-server.log"
	if [ -f "$FUORI/b2-wt.log" ]; then
		cat "$FUORI/b2-wt.log" >> "$FUORI/b8-server.log"
	else
		printf '(nessun registro per questa vita)\n' >> "$FUORI/b8-server.log"
	fi
	bash "$WT" spegni
}

VIVO() # ⛔ B0.5: dopo ogni prova il server dev'essere ancora li'
{
	if [ -n "${PID:-}" ] && [ -d "/proc/$PID" ]; then
		ok "il server e' ancora vivo dopo «$1» (PID $PID)"
		return 0
	fi
	ko "⛔ IL SERVER E' MORTO durante «$1»"
	return 4
}

# ---------------------------------------------------------------------------
log "3. La PRIMA vita del server — i campioni e il giro del ban"
ACCENDI "prima vita" || exit 4

log "3.0  Lo stato iniziale, dichiarato E verificato (B0.1)"
inf "⛔ e questo sblocco e' PRIMA del giro, non dentro (B0.3)"
bash "$ENTRA" --root "$CRONO --stato-iniziale"
if [ $? -ne 0 ]; then
	ko "⛔ lo stato iniziale non e' quello dichiarato: mi fermo"
	ko "   misurare da uno stato ignoto vuol dire misurare la storia della macchina"
	SPEGNI "prima vita (stato iniziale fallito)"
	exit 2
fi

# ⛔ LA SCALDATA E' UN BLOCCO INTERO, IL NUMERO ZERO — forma E9.
#    Le prime connessioni della vita di un processo pagano la cache fredda, i
#    moduli di PAM che si aprono, le arene di malloc che crescono.  ⚠ Qui non si
#    lascia al caso: il blocco 0 e' una terzina — **uno per caso**, quindi la
#    strada del successo *e* quella del fallimento — ed e' scartato **per regola
#    scritta prima**, mai a posteriori.  ⭐ E si stampa lo stesso, coi suoi
#    tempi: scartare in silenzio e' il modo piu' comodo di nascondere un numero
#    scomodo.
log "3.0b  la SCALDATA — una terzina, scartata per regola scritta prima (E9)"
bash "$ENTRA" --root "$CRONO --campioni --blocco 0 --per-caso 1"
VIVO "la scaldata" || exit 4
bash "$ENTRA" --root "$CRONO --sblocca $INDIRIZZI --perche dopo-la-scaldata"

b=1
while [ "$b" -le "$BLOCCHI" ]; do
	log "3.$b  blocco $b di $BLOCCHI — $((PER_CASO * 3)) tentativi"
	bash "$ENTRA" --root "$CRONO --campioni --blocco $b --per-caso $PER_CASO"
	ESITO=$?
	VIVO "blocco $b" || exit 4
	if [ "$ESITO" -eq 2 ]; then
		ko "⛔ il blocco $b non e' partito (piano o stato iniziale): mi fermo"
		ko "   meglio nessun campione che campioni presi fuori dal bilancio"
		SPEGNI "prima vita (blocco $b non partito)"
		exit 2
	fi
	if [ "$ESITO" -ne 0 ]; then
		ko "il blocco $b e' finito male (uscita $ESITO): mi fermo"
		SPEGNI "prima vita (blocco $b fallito)"
		exit "$ESITO"
	fi
	# ⛔ LO SBLOCCO FRA UN BLOCCO E L'ALTRO, E SI DICHIARA — B0.3.
	#    E' la scelta di questo banco fra le due che B8 ammette: «variare
	#    l'indirizzo di provenienza» o «sbloccare fra un blocco e l'altro».
	#    ⚠ Cambia quel che la misura sta misurando, e per questo si stampa: i
	#      campioni sono presi SEMPRE col conto sotto soglia.
	if [ "$b" -lt "$BLOCCHI" ]; then
		bash "$ENTRA" --root "$CRONO --sblocca $INDIRIZZI --perche fra-i-blocchi"
	fi
	b=$((b + 1))
done

# ---------------------------------------------------------------------------
# ⛔ E ADESSO IL GIRO DEL BAN — con uno sblocco PRIMA, e nessuno dentro.
log "4. ⛔ Il giro del ban — e da qui in poi NESSUNO sblocca niente (B0.3)"
inf "lo sblocco qui sotto e' l'ULTIMO prima del giro: serve a partire da un"
inf "conto azzerato, ed e' dichiarato.  ⚠ Se fallisse, il giro del ban se ne"
inf "   accorgerebbe lo stesso — il bilancio dei blocchi tiene ogni indirizzo a"
inf "   due fallimenti, cioe' uno sotto la soglia"
bash "$ENTRA" --root "$CRONO --sblocca $INDIRIZZI --perche prima-del-giro-del-ban"
bash "$ENTRA" --root "$CRONO --ban prima"
ESITO_BAN=$?
VIVO "il giro del ban" || exit 4
if [ "$ESITO_BAN" -eq 2 ]; then
	ko "⛔ il giro del ban non e' partito: il verdetto sarebbe cieco"
	SPEGNI "prima vita (giro del ban non partito)"
	exit 2
fi

SPEGNI "prima vita"

# ---------------------------------------------------------------------------
# ⛔ LA SECONDA VITA — e serve a UNA cosa sola: l'invariante I7.
log "5. ⭐ La SECONDA vita del server — il ban sopravvive al riavvio?"
inf "⛔ il file dei ban NON si tocca: e' l'unica strada per cui il ban puo'"
inf "   tornare, e buttarlo qui vorrebbe dire provare il contrario di quel che"
inf "   si vuole provare"
ACCENDI "seconda vita" || exit 4
bash "$ENTRA" --root "$CRONO --ban dopo"
ESITO_DOPO=$?
VIVO "la persistenza e lo sblocco" || exit 4

# ⛔ E si rimette la macchina a posto PRIMA del verdetto, e lo si dichiara:
#    B0.3 dice che ogni banco che sblocca lo dichiara.  Senza questa riga il
#    banco successivo troverebbe un indirizzo fuori per dodici ore.
log "6. Si rimette la macchina a posto (B0.3)"
bash "$ENTRA" --root "$CRONO --sblocca $INDIRIZZI --perche pulizia-finale"
SPEGNI "seconda vita"

# ---------------------------------------------------------------------------
log "7. Il verdetto — lo confronta il banco, non chi legge (B0.4)"
bash "$ENTRA" --root "python3 -u $DENTRO/01-b8-cronometro.py --verdetto \
	--giro $GIRO --uscita $DENTRO/b8-fatti.jsonl \
	--registro $DENTRO/b8-server.log"
ESITO=$?

# ---------------------------------------------------------------------------
# ⛔ E IL BANCO SI CERTIFICA — `LEZIONI.md` §1.2, e si fa DOPO perche' si guasta
#    quel che il giro ha appena prodotto.  Un guasto per volta, costruito a
#    mano, e il verdetto deve diventare rosso **in quel punto**: un banco che non
#    riproduce non e' una prova di correttezza (§1.3).
log "8. ⛔ La certificazione: si costruisce il guasto e si pretende il rosso"
bash "$ENTRA" --root "python3 -u $DENTRO/01-b8-cronometro.py --certifica \
	--giro $GIRO --uscita $DENTRO/b8-fatti.jsonl \
	--registro $DENTRO/b8-server.log"
CERT=$?
if [ "$CERT" -ne 0 ]; then
	ko "⛔ la certificazione del GIUDICE non passa: finche' e' rossa, un verde"
	ko "   di B8 non vuol dire niente"
fi

log "Esito"
# ⛔ QUATTRO ESITI, NON DUE.  «Non si separano» e «non ho guardato abbastanza da
#    poterlo dire» sono due fatti con due cure diverse, e dare loro lo stesso
#    colore e' la forma E8 applicata a un verdetto.
# ⛔ CINQUE ESITI, NON DUE.  «Non si separano», «non ho guardato abbastanza da
#    poterlo dire», «si separano ma il colpevole e' PAM» e «il ban non funziona»
#    sono quattro fatti con quattro cure diverse, in quattro file diversi: dare
#    loro lo stesso colore e' la forma E8 applicata a un verdetto.
case "$ESITO" in
	0) ok "⭐ B8 passa — e le risoluzioni qui sopra dicono fin dove ha guardato" ;;
	5) ko "⛔ B8: il BAN passa per intero, ma le mediane SI SEPARANO"
	   inf "⛔ e l'esito 5 si da' SOLO quando l'imputato e' stato MISURATO ed e'"
	   inf "PAM: il verdetto qui sopra stampa i due numeri del registro del"
	   inf "server che lo sostengono (quanto ha aspettato oltre il secondo fisso"
	   inf "sui respinti e sugli ammessi) e quale caso e' il piu' lento sul filo."
	   inf "La cura sta in banchi/rcp/autenticazione.c e nella pila PAM: e' il"
	   inf "[?] che RCP.md §4.4-bis ha gia' dichiarato, e che il ban non chiude."
	   inf "⚠ Se l'imputato fosse stato un altro — o non misurabile — questo"
	   inf "giro sarebbe uscito 1, non 5: l'indulgenza e' scritta per PAM." ;;
	3) ko "⚠ B8 SOSPESO: rilancia con piu' blocchi (adesso $BLOCCHI)" ;;
	2) ko "⛔ B8: non c'e' stato niente da giudicare" ;;
	*) ko "⛔ B8: qualcosa non passa" ;;
esac
if [ "$ESITO_DOPO" -ne 0 ]; then
	ko "⚠ e la fase della persistenza e' uscita $ESITO_DOPO: il verdetto qui"
	ko "  sopra dice quali righe mancano"
fi
# ⛔ E la certificazione entra nell'esito, invece di restare una riga che si
#    legge di sfuggita: un banco non certificato non promuove niente.
if [ "$CERT" -ne 0 ] && [ "$ESITO" -eq 0 ]; then
	ko "⛔ ...ma il banco NON e' certificato: l'esito diventa rosso"
	ESITO=1
fi
inf "i fatti, uno per riga: $FUORI/b8-fatti.jsonl"
inf "il registro del server, tutt'e due le vite: $FUORI/b8-server.log"
inf "il file dei ban: $FUORI/b8-ban.txt (⚠ resta li' apposta, per guardarlo)"
exit "$ESITO"
