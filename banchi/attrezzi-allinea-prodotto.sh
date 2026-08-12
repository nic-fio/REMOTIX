#!/bin/bash
#
# attrezzi-allinea-prodotto.sh — ⛔ GIRA SU CHUWI, dove sta il deposito.
# Porta l'albero del PRODOTTO (`src/`) dentro la macchina di prova, e
# RICOSTRUISCE.  E' il gemello di `attrezzi-allinea-innesto.sh`, per l'altro
# dei due server.
#
#   bash banchi/attrezzi-allinea-prodotto.sh guarda   dice e basta
#   bash banchi/attrezzi-allinea-prodotto.sh allinea  copia + costruisci + terreno
#   bash banchi/attrezzi-allinea-prodotto.sh prova    ⭐ il controllo positivo:
#                                                     costruisce una divergenza
#                                                     su una copia e pretende
#                                                     che `guarda` la veda
#
# Esce 0 se e' allineato · 1 se non lo e' (o se l'allineamento non e' finito)
# 2 se non ha potuto guardare · 3 se un passo e' fallito.
# ⛔ E «non ho potuto guardare» NON e' «va bene»: sono quattro esiti, non due.
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' ESISTE — LA PROPAGAZIONE NON LA FACEVA NESSUNO
#
# `README.md`, riquadro della notte fra l'11 e il 12 agosto 2026, scritto
# subito dopo la cura dell'innesto:
#
#     ⚠ E nessun attrezzo fa quella propagazione — i banchi la controllano
#       soltanto: e' il motivo per cui il disallineamento e' rimasto li' mezza
#       giornata.
#
# ⛔ E il giorno dopo la stessa forma si e' ripresentata sull'altro albero.
# `[M]` 12 agosto 2026, sera: `/media/REMOTIX/src/remotix/rcp.c` era
# `1adce15b…` mentre `src/rcp.c` del deposito era `6d858886…`; `main.c`,
# `trasporto.c`, `webtransport.c`, `rcp.h`, `trasporto.h`, `webtransport.h` e
# il `Makefile` erano vecchi; e `aiutante.c` e `aiutante.h` — i due file NUOVI
# della cura PAM — sul server **non c'erano affatto**.
#
# ⇒ Il prodotto acceso sulla 7448 girava senza la cura PAM, e chiunque lo
#   avesse interrogato avrebbe misurato il server di ieri credendo di misurare
#   quello di oggi.  E' la stessa forma pagata gia' due volte: l'innesto
#   disallineato (sei certificazioni salvate per un soffio dal controllo del
#   terreno) e il server di casa che per tredici ore ha girato su un binario
#   cancellato (`01-casa-7448.sh`, riquadro in testa).
#
# ⇒ I controlli dicono CHE COSA non va; questo file dice COME si rimette.
#
# ---------------------------------------------------------------------------
# ⛔⭐ L'ALBERO SI COPIA INTERO, E L'ELENCO NON SI SCRIVE A MANO
#
# E' la lezione che questo difetto insegna piu' di ogni altra: i due file che
# mancavano **del tutto** erano i due file NUOVI.  Un elenco ricopiato a mano
# — `rcp.c rcp.h autenticazione.c`, come nell'attrezzo dell'innesto, dove i
# file da portare sono tre per costruzione — qui avrebbe portato i vecchi e
# dimenticato i nuovi, cioe' avrebbe lasciato in piedi esattamente il difetto
# che deve curare.  ⚠ E' la forma di **R12-A.45** e della lacuna **L2** del
# terreno: una riga ricopiata invecchia in silenzio.
#
# ⭐ Quindi: si enumera `src/` e si porta **tutto quel che c'e'**, qualunque
#    cosa sia.  Un file nuovo entra da solo.
#
# ⛔ E quel che sta di la' e non sta di qua **si dichiara e non si cancella**:
#    `remotix` e i `.o` sono il prodotto della costruzione e devono restare;
#    qualunque altra cosa e' un rilievo per chi legge, non una cosa da buttare
#    di nascosto.
#
# ---------------------------------------------------------------------------
# ⛔ E SI RIFIUTA SE C'E' UN GUASTO INNESTATO — DALLE DUE PARTI
#
# `attrezzi-allinea-innesto.sh` guarda il guasto solo nel bersaglio, e li' e'
# giusto: B11 e B12 innestano proprio dentro `examples/`.  ⛔ Qui il verso che
# conta di piu' e' **l'altro**: se un guasto finisse nell'albero di partenza
# (`01-p5-guasto-ritiro.py` prende `--pagina <percorso>` e nessuno gli impedisce
# di puntare a `src/pagina.html`; il catalogo dei guasti nomina i suoi bersagli
# per percorso, e un percorso sbagliato e' gia' costato R12-A.45) questo
# attrezzo lo **propagherebbe nel prodotto di casa** e lo ricostruirebbe dentro
# il binario che tutti interrogano.
#
# ⇒ Si guardano tutt'e due gli alberi, e in tutt'e due un ritrovamento ferma
#   il giro.  ⚠ E la marca **non si ricopia**: si chiede a `01-b12-guasti.py`,
#   perche' il giorno in cui il catalogo la cambia un ago ricopiato qui
#   smetterebbe di trovare qualsiasi cosa **e diventerebbe verde** (e' la cura
#   che `01-b0-terreno.sh` ha gia' fatto sulla lacuna L2).
#
# ---------------------------------------------------------------------------
# ⛔⭐ E «IDENTICI» NON BASTA, DUE VOLTE
#
#  1. **il binario dev'essere piu' nuovo dei sorgenti.**  Dopo la copia i file
#     hanno la data di adesso: un binario costruito prima e' vecchio anche se
#     il contenuto combacia.  Se il giro si fermasse fra la copia e la
#     costruzione — a chi ha scritto l'attrezzo dell'innesto l'ha fermato un
#     `timeout` — resterebbe una scena in cui le impronte combaciano, `guarda`
#     direbbe «allineato», e il terreno boccerebbe lo stesso.  ⇒ Si guarda
#     anche l'orologio.
#
#  2. ⛔ **il processo vivo dev'essere quello del disco.**  Sorgenti allineati e
#     binario ricostruito lasciano ancora il server della 7448 in esecuzione
#     sul binario di prima — che e' **precisamente** il difetto delle tredici
#     ore.  ⇒ `allinea` finisce chiedendolo a `01-casa-7448.sh stato`, e se la
#     risposta e' no **non si dichiara finito**: esce 1 e nomina la cura.
#
# ⛔ E NON RIACCENDE DA SE'.  Sulla 7448 possono esserci giri di altri, e
#    spegnere il server sotto chi lo sta misurando e' il danno che tutta questa
#    famiglia di attrezzi esiste per non fare.  ⇒ Questo file **propaga e
#    dichiara**; a riaccendere e' chi ha in mano la porta, con il file di casa.
#
# ---------------------------------------------------------------------------
# ⛔ MAI UNA REDIREZIONE **ATTORNO** A `ssh` O A `enter.sh`
#
# `fasi/00-ambiente.md` B3.3, pagata **cinque** volte — la quinta il 12 agosto
# 2026 dentro `attrezzi-allinea-innesto.sh`, cioe' nel file preso a modello
# qui: `sudo -v -S -p` fermo **5 minuti e 28 secondi in silenzio**, coi sorgenti
# gia' copiati e il binario ancora vecchio, cioe' la scena peggiore.
#
# ⭐ Da cui i DUE portatori, che sono la regola di casa (`01-p5-lancia.sh`):
#
#     SSH       legge — chiave, `BatchMode`, niente `sudo`, stdout pulito:
#               il suo stdout si puo' catturare perche' non c'e' nessuna
#               domanda che possa perdersi;
#     SSH_ROOT  comanda — `sshpw.py`, che digita la parola d'ordine su un pty
#               perche' `enter.sh --root` chiama `sudo`.  ⛔ Il suo stdout NON
#               si cattura e NON si redirige: la redirezione va **dentro** le
#               virgolette, su un file del server, e il file lo si riporta con
#               `--get` e lo si legge qui.
#
# ⛔ E si guarda l'ESITO del costruttore, non la presenza del binario dopo:
#    `LEZIONI.md` §1.9 punto 8 — un binario di due ore prima risponde «esisto»
#    come uno di adesso.
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
RADICE=$(dirname "$QUI")

IND=${IND:-192.168.0.2}
UTE=${UTE:-nicfio}

# ⛔ Gli alberi si DICHIARANO, come `SORG=` in `01-b0-terreno.sh`: di alberi
#    `remotix` su quella macchina ce ne sono cinque, e indovinare quale sia
#    quello di casa e' la domanda che D5 ha gia' pagato.
FONTE=${FONTE:-$RADICE/src}                    # qui, su CHUWI
DEST=${DEST:-/media/REMOTIX/src/remotix}       # la', visto dall'HOST
CASA=${CASA:-/srv/src/01-casa-7448.sh}         # dentro il contenitore
TERRENO=${TERRENO:-/media/REMOTIX/src/01-b0-terreno.sh}
ENTRA=${ENTRA:-/media/REMOTIX/enter.sh}
# ⚠ Il registro della costruzione porta un nome PROPRIO: due attrezzi che
#   scrivessero lo stesso file si leggerebbero l'esito a vicenda.  ⛔ E si
#   nomina DUE VOLTE, perche' lo stesso file ha due nomi: `/media/REMOTIX/src`
#   sull'host e `/srv/src` dentro il contenitore (`enter.sh` lo monta li').
#   Ricavare l'uno dall'altro con una sostituzione sarebbe un percorso
#   indovinato, e un percorso indovinato un giorno cambia.
LOG_LA=${LOG_LA:-/media/REMOTIX/src/attrezzi-allinea-prodotto-costr.log}
LOG_DENTRO=${LOG_DENTRO:-/srv/src/attrezzi-allinea-prodotto-costr.log}

SSH="ssh -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new $UTE@$IND"
SCP="scp -q -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new"
SSH_ROOT=${SSH_ROOT:-python3 $RADICE/v1/strumenti/sshpw.py}

VERDE=$'\033[1;32m'; ROSSO=$'\033[1;31m'; GIALLO=$'\033[1;33m'; GRIGIO=$'\033[0m'
ok()  { printf '    %sOK%s  %s\n' "$VERDE" "$GRIGIO" "$*"; }
ko()  { printf '    %sNO%s  %s\n' "$ROSSO" "$GRIGIO" "$*"; }
dub() { printf '    %s??%s  %s\n' "$GIALLO" "$GRIGIO" "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

AZIONE=${1:-guarda}
case "$AZIONE" in guarda|allinea|prova) ;;
*) echo "uso: $0 [guarda|allinea|prova]"; exit 2 ;; esac

T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT

# ===========================================================================
# `prova` si tira da parte subito: costruisce la sua scena e richiama `guarda`
# su una COPIA.  Sta in fondo al file, qui c'e' solo il salto.
if [ "$AZIONE" = prova ]; then
	PROVA=1
else
	PROVA=0
fi

# ---------------------------------------------------------------------------
log "0. Gli alberi, dichiarati (B0.1: si dichiara E si verifica)"
inf "sorgente (CHUWI): $FONTE"
inf "prodotto (NIC-OS): $DEST"
if [ ! -d "$FONTE" ]; then
	ko "⛔ l'albero sorgente non c'e': $FONTE"
	exit 2
fi
# ⛔ Il denominatore: quanti file sto per confrontare.  «Tutti quelli guardati
#    combaciano» e' vero anche quando i guardati sono zero (LEZIONI.md §1.9
#    regola 6).
FILE=$(cd "$FONTE" && find . -maxdepth 1 -type f -printf '%f\n' | sort)
N_QUI=$(printf '%s\n' "$FILE" | grep -c . )
# ⛔ E la stessa lista con gli SPAZI, per poterci chiedere «c'e' dentro?».
#    ⚠ La prima stesura interrogava quella a capo con `case " $FILE " in *" $n "*`,
#    che non puo' combaciare mai: fra un nome e l'altro c'e' un a-capo, non uno
#    spazio.  ⇒ Il controllo delle date saltava OGNI file e la dichiarazione dei
#    file «solo di la'» li elencava TUTTI — due controlli che non controllavano
#    niente, cioe' la forma D5.  L'ha trovata il primo giro vero.
ELENCO=" $(printf '%s ' $FILE)"
if [ "$N_QUI" -eq 0 ]; then
	ko "⛔ in $FONTE non c'e' nessun file: non allineo niente e non dico che va bene"
	exit 2
fi
ok "$N_QUI file nell'albero sorgente"

if [ "$PROVA" -eq 1 ]; then
	# --- la scena della prova si costruisce prima di guardare qualsiasi cosa
	SCRATCH=${SCRATCH:-/media/REMOTIX/src/tmp/prova-allinea-prodotto}
	SPORCA=${SPORCA:-Makefile}
	log "P. ⭐ IL CONTROLLO POSITIVO — «questo attrezzo sa dire di NO?»"
	inf "⛔ Un attrezzo che dicesse sempre «allineato» sarebbe peggio di nessun"
	inf "   attrezzo: darebbe fiducia (CODER.md §4.6).  Qui la divergenza si"
	inf "   COSTRUISCE, su una copia che non e' di nessuno, e l'atteso lo"
	inf "   confronta il programma — non chi legge (B0.4)."
	inf "copia di prova: $SCRATCH   ·   file da sporcare: $SPORCA"

	$SSH "rm -rf $SCRATCH && mkdir -p $(dirname "$SCRATCH") && cp -R --preserve=timestamps $DEST $SCRATCH" || {
		ko "⛔ non ho potuto fare la copia di prova"; exit 2; }
	ok "copia fatta"

	printf '\n  ---- giro 1: i due alberi COMBACIANO, e ci si aspetta che taccia\n'
	DEST=$SCRATCH bash "$0" guarda
	G1=$?
	printf '\n  ---- giro 2: UN file sporcato, e ci si aspetta che lo dica\n'
	$SSH "printf '\n# riga aggiunta dalla prova di attrezzi-allinea-prodotto.sh\n' >> $SCRATCH/$SPORCA" || {
		ko "⛔ non ho potuto sporcare $SPORCA"; $SSH "rm -rf $SCRATCH"; exit 2; }
	DEST=$SCRATCH bash "$0" guarda > "$T/giro2.txt" 2>&1
	G2=$?
	cat "$T/giro2.txt"

	$SSH "rm -rf $SCRATCH" || dub "⚠ la copia di prova non si e' cancellata: $SCRATCH"

	log "P. Il verdetto della prova"
	FALLE=0
	if [ "$G1" -eq 0 ]; then
		ok "giro 1: uscita 0 — con gli alberi identici TACE"
	else
		ko "⛔ giro 1: uscita $G1 invece di 0.  O gli alberi non erano allineati"
		ko "   prima della prova, o l'attrezzo dice di no anche quando non c'e'"
		ko "   niente da dire — e allora i suoi «no» non valgono niente."
		FALLE=$((FALLE+1))
	fi
	if [ "$G2" -eq 1 ]; then
		ok "giro 2: uscita 1 — la divergenza costruita l'ha vista"
	else
		ko "⛔ giro 2: uscita $G2 invece di 1: NON ha visto un file cambiato"
		FALLE=$((FALLE+1))
	fi
	if grep -q "DIVERSO" "$T/giro2.txt" && grep -q "^.*$SPORCA DIVERSO" "$T/giro2.txt"; then
		ok "e lo dice del file GIUSTO: «$SPORCA DIVERSO» compare nell'uscita"
	else
		ko "⛔ e' diventato rosso ma non nomina «$SPORCA»: e' rosso per un'altra"
		ko "   ragione, e questo non e' un controllo positivo"
		FALLE=$((FALLE+1))
	fi
	# ⛔ E UNO SOLO: un attrezzo che dichiarasse diversi TUTTI i file sarebbe
	#    rosso lo stesso, e non saprebbe indicare niente.
	N_DIV=$(grep -c ' DIVERSO — ' "$T/giro2.txt")
	if [ "$N_DIV" -eq 1 ]; then
		ok "e ne nomina UNO SOLO ($N_DIV): sa distinguere, non solo protestare"
	else
		ko "⛔ dichiara $N_DIV file diversi, e ne ho sporcato uno: non distingue"
		FALLE=$((FALLE+1))
	fi
	if [ "$FALLE" -eq 0 ]; then
		printf '\n    %s⭐ IL CONTROLLO POSITIVO PASSA: tace quando combaciano, e quando%s\n' "$VERDE" "$GRIGIO"
		printf '    %s   divergono lo dice, e dice quale.%s\n' "$VERDE" "$GRIGIO"
		exit 0
	fi
	printf '\n    %s⛔ IL CONTROLLO POSITIVO NON PASSA: %s cose su 4 non tornano.%s\n' "$ROSSO" "$FALLE" "$GRIGIO"
	printf '    %s   ⇒ i verdetti di questo attrezzo non valgono finche non torna.%s\n' "$ROSSO" "$GRIGIO"
	exit 1
fi

# ---------------------------------------------------------------------------
log "1. Le impronte, file per file"

# ⛔ Lo stdout di `$SSH` si cattura, e si puo': la chiave non chiede niente e
#    non c'e' nessun `sudo` di mezzo.  E' il portatore che LEGGE.
if ! $SSH "find $DEST -maxdepth 1 -type f -exec md5sum {} +" > "$T/la-md5.txt" 2>"$T/la-md5.err"; then
	# ⛔ Tre esiti, non due: l'albero non c'e' · c'e' ed e' vuoto · non ho
	#    potuto guardare.  E il terzo non ha la faccia del secondo.
	if [ ! -s "$T/la-md5.txt" ] && grep -q 'No such file' "$T/la-md5.err"; then
		ko "⛔ l'albero del prodotto non c'e' di la': $DEST"
	else
		dub "⛔ non ho potuto leggere le impronte di la':"
		sed 's/^/        /' "$T/la-md5.err"
	fi
	exit 2
fi
$SSH "find $DEST -maxdepth 1 -type f -printf '%T@ %f\n'" > "$T/la-ore.txt" || {
	dub "⛔ non ho potuto leggere le date di la'"; exit 2; }

DIVERSI=""
NUOVI=""
UGUALI=0
for f in $FILE; do
	a=$(md5sum "$FONTE/$f" | cut -d' ' -f1)
	b=$(awk -v n="$DEST/$f" '$2==n{print $1}' "$T/la-md5.txt")
	if [ -z "$b" ]; then
		ko "⛔ $f NON C'E' di la' — $a"
		NUOVI="$NUOVI $f"
		continue
	fi
	if [ "$a" = "$b" ]; then
		UGUALI=$((UGUALI+1))
	else
		ko "⛔ $f DIVERSO — qui $a · la' $b"
		# ⭐ E si dice QUANTE righe ballano: «diverso» e «diverso di una cura
		#    intera» mandano a guardare in due posti diversi.
		if $SCP "$UTE@$IND:$DEST/$f" "$T/la-$f"; then
			inf "   righe che cambiano: $(diff "$FONTE/$f" "$T/la-$f" | grep -c '^[<>]')"
		else
			inf "   ⚠ non ho potuto riportare la copia di la': non conto le righe"
		fi
		DIVERSI="$DIVERSI $f"
	fi
done
[ "$UGUALI" -gt 0 ] && ok "$UGUALI file su $N_QUI gia' identici"

# ⛔ E quel che sta di la' e non sta di qua si DICHIARA — non si cancella.
SOLO_LA=""
while read -r _imp per; do
	n=$(basename "$per")
	case "$ELENCO" in *" $n "*) continue ;; esac
	case "$n" in *.o|remotix) continue ;; esac   # il prodotto della costruzione
	SOLO_LA="$SOLO_LA $n"
done < "$T/la-md5.txt"
if [ -n "$SOLO_LA" ]; then
	dub "⚠ di la' ci sono file che qui non esistono, e NON li tocco:$SOLO_LA"
	dub "   (non li cancello: cancellare di nascosto e' come copiare di nascosto)"
fi

# ---------------------------------------------------------------------------
log "2. Il binario e' piu' nuovo dei sorgenti?"
BIN_ORA=$(awk '$2=="remotix"{print $1}' "$T/la-ore.txt")
VECCHIO=""
if [ -z "$BIN_ORA" ]; then
	ko "⛔ di la' non c'e' nessun binario «remotix»: il prodotto non e' mai stato"
	ko "   costruito in $DEST"
	VECCHIO=" (manca il binario)"
else
	while read -r ora nome; do
		[ "$nome" = remotix ] && continue
		case "$nome" in *.o) continue ;; esac
		case "$ELENCO" in *" $nome "*) ;; *) continue ;; esac
		if awk -v a="$ora" -v b="$BIN_ORA" 'BEGIN{exit !(a>b)}'; then
			VECCHIO="$VECCHIO $nome"
		fi
	done < "$T/la-ore.txt"
	# ⚠ E i file che di la' ancora non ci sono contano come «piu' nuovi»: un
	#   binario che non li ha mai compilati e' vecchio per definizione.
	[ -n "$NUOVI" ] && VECCHIO="$VECCHIO$NUOVI"
	if [ -n "$VECCHIO" ]; then
		ko "⛔ il binario e' PIU' VECCHIO di:$VECCHIO"
		inf "   remotix: $(date -d "@${BIN_ORA%.*}" '+%Y-%m-%d %H:%M:%S %Z')  (orologio di CHUWI)"
		inf "   ⇒ va ricostruito anche se le impronte combaciano"
	else
		ok "il binario e' piu' nuovo di tutti i sorgenti ($(date -d "@${BIN_ORA%.*}" '+%Y-%m-%d %H:%M:%S %Z'), orologio di CHUWI)"
	fi
fi

if [ -z "$DIVERSI" ] && [ -z "$NUOVI" ] && [ -z "$VECCHIO" ]; then
	ok "⭐ il prodotto di la' e' gia' allineato ai sorgenti, e il binario e' di dopo"
	[ "$AZIONE" = guarda ] && exit 0
	inf "niente da copiare e niente da ricostruire: si va dritti al terreno"
fi

# ---------------------------------------------------------------------------
log "3. ⛔ C'e' un guasto innestato in uno dei due alberi?"
# ⚠ La marca si chiede al catalogo, non si ricopia: se `01-b12-guasti.py` la
#   cambia, un ago ricopiato qui smetterebbe di trovare qualunque cosa e questo
#   controllo diventerebbe VERDE.  E' la cura della lacuna L2 del terreno.
MARCA12=$(python3 - "$QUI/01-b12-guasti.py" <<'PY'
import importlib.util, sys
s = importlib.util.spec_from_file_location("b12", sys.argv[1])
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
print(m.MARCA)
PY
)
if [ -z "$MARCA12" ]; then
	dub "⛔ non ho potuto leggere la marca da 01-b12-guasti.py: NON dico che"
	dub "   non ci sono guasti — dico che non ho guardato"
	exit 2
fi
MARCA11=$(grep -m1 '^MARCA = ' "$QUI/01-b11-guasto-innesta.py" | cut -d'"' -f2)
[ -n "$MARCA11" ] || { dub "⛔ marca di B11 non letta: non guardo a meta'"; exit 2; }
inf "aghi letti dai cataloghi: «$MARCA12» · «$MARCA11»"

TROVATI=0
# --- di qua (l'albero da cui si copia): il verso che conta di piu'
# ⛔ Lo stato di `grep` sono TRE fatti e non due — `LEZIONI.md` §1.9 regola 1:
#    0 = trovato · 1 = non c'e' (che e' una RISPOSTA) · ≥2 = non ho potuto
#    guardare (che non e' una risposta).  Solo il terzo e' un «??».
for m in "$MARCA12" "$MARCA11"; do
	grep -rlF -e "$m" "$FONTE" > "$T/qua-guasti.txt"
	s=$?
	if [ "$s" -eq 0 ]; then
		ko "⛔ «$m» compare NELL'ALBERO SORGENTE:"
		sed 's/^/        /' "$T/qua-guasti.txt"
		TROVATI=$((TROVATI+1))
	elif [ "$s" -gt 1 ]; then
		dub "⛔ non ho potuto cercare «$m» in $FONTE (grep: $s)"
		exit 2
	else
		ok "nessuna traccia di «$m» in $FONTE"
	fi
done
# --- di la' (l'albero su cui si scrive)
for m in "$MARCA12" "$MARCA11"; do
	$SSH "grep -lF -e '$m' -- $DEST/*" > "$T/la-guasti.txt"
	s=$?
	if [ "$s" -eq 0 ]; then
		ko "⛔ «$m» compare NEL PRODOTTO di la':"
		sed 's/^/        /' "$T/la-guasti.txt"
		TROVATI=$((TROVATI+1))
	elif [ "$s" -gt 1 ]; then
		dub "⛔ non ho potuto cercare «$m» in $DEST (uscita $s)"
		exit 2
	else
		ok "nessuna traccia di «$m» in $DEST"
	fi
done
if [ "$TROVATI" -gt 0 ]; then
	ko "⛔ NON TOCCO NIENTE: c'e' un guasto innestato."
	ko "   Se sta nell'albero SORGENTE, copiarlo lo metterebbe nel prodotto che"
	ko "   tutti interrogano; se sta nel PRODOTTO, ricopiarci sopra lo"
	ko "   toglierebbe SOTTO chi lo sta misurando — e quel giro direbbe «il"
	ko "   banco non e' diventato rosso» di un banco a cui e' stato tolto"
	ko "   l'imputato di mano."
	ko "   ⇒ Aspetta che il giro finisca, o toglilo con «--togli»."
	exit 3
fi

if [ "$AZIONE" = guarda ]; then
	inf "«guarda» si ferma qui: per copiare e ricostruire, «allinea»"
	exit 1
fi

# ---------------------------------------------------------------------------
if [ -n "$DIVERSI" ] || [ -n "$NUOVI" ]; then
	log "4. Si copiano i sorgenti dentro il prodotto"
	for f in $DIVERSI $NUOVI; do
		$SCP "$FONTE/$f" "$UTE@$IND:$DEST/$f" || {
			ko "⛔ la copia di «$f» e' fallita"; exit 3; }
		a=$(md5sum "$FONTE/$f" | cut -d' ' -f1)
		$SSH "md5sum $DEST/$f" > "$T/dopo.txt" || {
			ko "⛔ «$f» copiato ma non ho potuto rileggerlo"; exit 3; }
		b=$(cut -d' ' -f1 < "$T/dopo.txt")
		if [ "$a" = "$b" ]; then
			ok "$f copiato, e le impronte adesso combaciano ($a)"
		else
			ko "⛔ $f copiato ma le impronte NON combaciano: $a ≠ $b"
			exit 3
		fi
	done
fi

# ---------------------------------------------------------------------------
log "5. Si ricostruisce — con il file di casa, e si guarda l'ESITO"
# ⭐ Non si riscrive la costruzione: la fa gia' `01-casa-7448.sh costruisci`,
#    che sa dove sta l'albero, quale gemello confrontare, e che l'esito si
#    legge da `costruisci.sh` e non da `test -x` (CODER.md §4.1, dipendere).
#
# ⛔⭐ E LA REDIREZIONE STA **DENTRO** LE VIRGOLETTE.  `enter.sh --root` chiama
#     `sudo`, la domanda esce su stderr, e una redirezione messa attorno la
#     mangia: il comando resta appeso per sempre, in silenzio — e il sintomo
#     non e' un errore, e' un attrezzo «lento».  `fasi/00-ambiente.md` B3.3,
#     pagata cinque volte, l'ultima proprio nel file preso a modello qui.
$SSH "rm -f $LOG_LA" || dub "⚠ non ho potuto togliere il registro vecchio: quel che leggero potrebbe essere di prima"
$SSH_ROOT "bash $ENTRA --root \"bash $CASA costruisci > $LOG_DENTRO 2>&1\""
S_COSTR=$?
$SCP "$UTE@$IND:$LOG_LA" "$T/costr.log" || dub "⚠ il registro della costruzione non si e' potuto riportare"
if [ "$S_COSTR" -eq 0 ]; then
	ok "⭐ remotix ricostruito"
	[ -f "$T/costr.log" ] && tail -3 "$T/costr.log" | sed 's/^/        /'
else
	ko "⛔ la costruzione e' FALLITA (uscita $S_COSTR): il binario che c'e' e'"
	ko "   quello di prima, e adesso i sorgenti sono cambiati sotto di lui —"
	ko "   cioe' la scena PEGGIORE.  L'errore:"
	if [ -f "$T/costr.log" ]; then
		tail -30 "$T/costr.log" | sed 's/^/        /'
	else
		ko "   ⛔ e non c'e' nemmeno il registro: non ho letto niente"
	fi
	exit 3
fi

# ---------------------------------------------------------------------------
log "6. ⛔ E lo dice il terreno, non io"
# ⚠ SULL'HOST, non dentro il contenitore: `01-b0-terreno.sh` legge
#   `/media/REMOTIX/...`, che dentro il chroot si chiama in un altro modo.
$SSH "bash $TERRENO prodotto"
S_TERR=$?

# ---------------------------------------------------------------------------
log "7. ⛔ E il processo vivo sta eseguendo il binario nuovo?"
inf "sorgenti allineati e binario ricostruito NON bastano: il server acceso"
inf "gira ancora quello di prima, ed e' il difetto delle tredici ore."
$SSH_ROOT "bash $ENTRA --root \"bash $CASA stato\""
S_STATO=$?

printf '\n'
if [ "$S_TERR" -ne 0 ]; then
	printf '    %s⛔ il terreno NON regge (uscita %s): non lanciare banchi.%s\n' "$ROSSO" "$S_TERR" "$GRIGIO"
	exit 1
fi
if [ "$S_STATO" -ne 0 ]; then
	printf '    %s⛔ i SORGENTI sono allineati e il binario e'"'"' di adesso, ma il%s\n' "$ROSSO" "$GRIGIO"
	printf '    %s   server acceso NON sta eseguendo quel binario (uscita %s).%s\n' "$ROSSO" "$S_STATO" "$GRIGIO"
	printf '       ⇒ La cura, da chi ha in mano la porta:\n'
	printf '            bash %s --root "bash %s riaccendi"\n' "$ENTRA" "$CASA"
	printf '       ⚠ Non la faccio io: sulla 7448 possono esserci giri di altri,\n'
	printf '         e spegnere un server sotto chi lo misura e'"'"' il danno che\n'
	printf '         questa famiglia di attrezzi esiste per non fare.\n'
	exit 1
fi
printf '    %s⭐ prodotto allineato: sorgenti, binario e processo dicono la stessa cosa.%s\n' "$VERDE" "$GRIGIO"
exit 0
