#!/bin/bash
#
# 06-b34-lancia.sh — ⛔ GIRA SUL SERVER (NIC-OS), **DA ROOT**, fuori dal
# contenitore.  Il banco della SOTTOFASE 6.2 — *la tastiera che rinasce*.
#
#   sudo bash .../06-b34-lancia.sh caso1        riattacco con la STESSA disposizione
#   sudo bash .../06-b34-lancia.sh caso2        riattacco DICHIARANDONE un'altra
#   sudo bash .../06-b34-lancia.sh caso2s       ⭐ la disposizione DELLA SESSIONE cambia
#   sudo bash .../06-b34-lancia.sh caso3        DISPOSIZIONE (0x0009) a sessione aperta
#   sudo bash .../06-b34-lancia.sh caso4        ⛔ il tasto premuto al distacco (§11)
#   sudo bash .../06-b34-lancia.sh caso5        disposizione ignota o malformata
#   sudo bash .../06-b34-lancia.sh caso7        ⛔ le disposizioni ESOTICHE, e il metro e' IL CARATTERE
#   sudo bash .../06-b34-lancia.sh caso8        ⛔ l'ALFABETO del nome: le varianti che la macchina HA
#   sudo bash .../06-b34-lancia.sh tutti
#
# ===========================================================================
# ⛔⛔ LA DOMANDA DELLA SOTTOFASE, E L'IPOTESI DA CUI SI PARTE
# ===========================================================================
#
# `SPECIFICHE.md` §7.3: *«La disposizione della sessione si rinegozia a ogni
# attacco e riattacco, come la risoluzione»*.
#
# ⭐ **Il mandato e' avversariale**: si parte dall'ipotesi che quella frase sia
#    **falsa**, e si cerca la prova.  ⇒ L'atteso di ciascun caso e' scritto
#    QUI, **prima** della misura, in **due colonne**: quel che si vedrebbe se
#    la frase fosse vera, e quel che si vedrebbe se fosse falsa.  Un banco che
#    dichiarasse un atteso solo non saprebbe distinguere fra «l'ho refutata» e
#    «non ho capito che cosa guardavo».
#
# ===========================================================================
# ⛔ LA TAVOLA DELLE POSIZIONI — calcolata da `06-b34-tabella.c`, non da me
# ===========================================================================
#
#   carattere   it        us        de
#   a           30        30        30       ⭐ IL CANARINO: uguale in tutte
#   z           44        44        21       ⛔ la prova cattiva
#   y           21        21        44
#   è           26        —         —        il guasto e' un'ASSENZA
#   ò           39        —         —
#   \           41        43        100+12
#   @           100+16    42+3      100+16
#
# ⛔⛔ E DA QUESTA TAVOLA VIENE FUORI CHE IL MANDATO SBAGLIAVA L'ESEMPIO:
#    diceva *«`it` → `us`, dove `z`/`y` e le accentate si spostano»*.  ⛔ `z` e
#    `y` **NON si spostano** fra `it` e `us`: sono tutt'e due QWERTY, e la `z`
#    sta sul 44 in tutt'e due.  Lo scambio `z`/`y` e' di **`de`** (QWERTZ).
#
#    ⇒ Le due coppie provano due guasti DIVERSI, e servono tutt'e due:
#      · `it`/`us`  il carattere **sparisce** (`è`, `ò` non esistono su `us`)
#      · `it`/`de`  il carattere **cambia** — mandando il 44 su una sessione
#        `de` esce una **`y`**, che e' precisamente cio' che `RCP.md` §7.3
#        vieta e che nessuno collegherebbe alla disposizione.
#
# ===========================================================================
# ⛔ IL PRELUDIO, E PERCHE' C'E' — costato mezz'ora il 16 agosto 2026
# ===========================================================================
#
# I primi tre giri hanno dato **testimone vuoto**, e sembrava la misura.  ⛔ Non
# lo era: i caratteri arrivavano, e andavano nella **casella di ricerca
# dell'overview** di GNOME Shell perche' nessuna finestra aveva il fuoco.  ⭐ La
# prova e' una fotografia del desktop con dentro «zya» scritto nella ricerca.
#
# ⇒ Ogni prova comincia con tre **⎋**, che chiudono l'overview e portano il
#   fuoco sul testimone; `06-b34-leggi.py` butta tutto fino all'ultimo ⎋.
# ⇒ E ogni sonda e' racchiusa fra due **canarini `a`**: se mancano, la prova
#   non e' ROSSA, e' **INVALIDA** — non si e' misurata la tastiera, si e'
#   misurato il fuoco (`LEZIONI.md` §1.9 regola 1).
#
# ===========================================================================
# ⛔ IL LIMITE DI QUESTO BANCO, SCRITTO IN TESTA
# ===========================================================================
#
#  1. ⛔ **QUESTO BANCO NON PILOTA NESSUN BROWSER, E NON GIRA SU Xvfb.**  Chi
#     provoca i tasti e' `06-b34-cliente.py`, un client RCP che parla il filo
#     di `RCP.md` §7.3 direttamente; chi li riceve e' un terminale **dentro
#     una sessione GNOME vera**, sul ferro.
#
#     ⚠ La ragione per cui va detto: `LEZIONI.md` §1.15, `[M]` 13 agosto 2026 —
#     **su Xvfb `requestAnimationFrame` non gira MAI** (0 quadri in 3 s, con e
#     senza GPU, con `visibilityState` a «visible»), e in **Blink** l'evento
#     `resize` si consegna **dentro** il giro di rendering: senza quadri non
#     arriva mai.  ⇒ Su un banco a browser, **ogni cammino della pagina che
#     sta dietro a un quadro e' codice morto, e il banco resta verde**.
#
#     ⇒ Qui quel difetto **non puo' esserci**, ma non perche' siamo stati
#       bravi: perche' **la pagina non e' nel giro**.  ⛔ E questo e' anche il
#       limite: quel che questo banco misura e' il **server**, non la pagina.
#       Che `pagina.html` mandi la disposizione giusta al momento giusto
#       resta `[?]` per questa sottofase, e va provato dove c'e' un browser
#       vero (sottofase 6.5).
#
#  2. ⭐ **SI GIUDICA PRIMA IL PALCO.**  Qui il palco non sono i quadri del
#     browser: sono **il fuoco della tastiera dentro la sessione** e **il
#     dispositivo di `libei` vivo**.  I due giudici stanno prima di ogni
#     misura, e se non passano il banco dice «IL PALCO, NON IL PRODOTTO»:
#
#       · i **canarini `a`** in testa e in coda a ogni sonda — se mancano, la
#         prova e' **INVALIDA**, non rossa (e la prima sera ne sono servite
#         tre per capirlo);
#       · **`ricambi_tastiera`** e **`KEYMAP CAMBIATA`** letti nel registro
#         PRIMA e DOPO — se il caso 2s non li fa crescere, non si e' provocato
#         nessun ricambio e il verdetto sul carattere non vuol dire niente.
set -uo pipefail

PORTA=${PORTA:-7721}
UTENTE=${UTENTE:-provat6}
UID_B=${UID_B:-1007}
LAVH=${LAVH:-/media/REMOTIX/tmp/06-t}          # visto dall'host
LAVC=${LAVC:-/srv/remotix/tmp/06-t}            # lo stesso, visto dal contenitore
CB=${CB:-/srv/src/06-t-src/banchi}             # i banchi, visti dal contenitore
BH=${BH:-/media/REMOTIX/src/06-t-src/banchi}   # i banchi, visti dall'host
PAR=$LAVC/parola
TERRENO=$BH/06-b34-terreno.sh
LOG=$LAVH/registro.log
TEST=/home/$UTENTE/testimone.txt
ESITI=$LAVH/06-b34-esiti.jsonl

# ⛔ Il preludio: tre ⎋ per uscire dall'overview.  Le sonde NON contengono mai
#    un ⎋, o `06-b34-leggi.py` taglierebbe la misura invece del preludio.
PRE='P:1:1 P:1:0 A:0.8 P:1:1 P:1:0 A:0.8 P:1:1 P:1:0 A:1.2'
# Le sonde, in punti di codice: a è ò \ @ a  ·  a z y \ a
SONDA_ACC='U:61 U:E8 U:F2 U:5C U:40 U:61'
SONDA_ZY='U:61 U:7A U:79 U:5C U:61'

# ⛔⛔⭐ IL BIT CHE DISTINGUE VERDE DA ROSSO — 21 agosto 2026, rilievo 4 della
#      revisione avversariale di A9.
#
#      Questo copione **non usciva mai diverso da zero**: stampava `NO` in rosso
#      e poi tornava 0, e i casi 3, 4a e 5 non avevano nemmeno un `ok`/`ko`.
#      ⛔ Un banco che non ha un bit non si puo' incatenare a niente — non a un
#      `if`, non a una costruzione, non a un altro banco — e sopra tutto: chi lo
#      lancia deve **leggere** per sapere com'e' andata.  ⚠ E' `LEZIONI.md`
#      §1.2 nella sua forma piu' banale: la misura c'era, il giudizio no.
#
# ⇒ Da qui in poi ogni `ko` alza `ESITO`, e il copione esce con quello.
#   ⚠ `dub` NON lo alza: un «non so» non e' un rosso, ed e' l'unico modo di
#     tenere separati «ho misurato e non va» e «non ho potuto misurare».
#     Quest'ultimo ha un codice suo, 9, che `batti` gia' ritorna.
ESITO=0
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { ESITO=1; printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
dub() { printf '    \033[1;33m??\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
att() { printf '    \033[1mATTESO (dichiarato PRIMA)\033[0m  %s\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { ko "⛔ va lanciato DA ROOT"; exit 2; }

carico() { uptime | sed 's/.*average: //'; }

# ⛔ Il registro NON si azzera fra un caso e l'altro: si segna dove siamo
#    arrivati, e si guarda solo quel che e' cresciuto.  Azzerarlo butterebbe
#    via il ricambio che il caso precedente ha provocato — e i ricambi si
#    contano sull'INTERA vita del figlio, non su una finestra.
SEGNO=0
segna() { SEGNO=$(stat -c %s "$LOG" 2>/dev/null || echo 0); }
cresciuto() { tail -c "+$((SEGNO + 1))" "$LOG" 2>/dev/null; }

ricambi_ora() { grep -c 'la tastiera e. stata TOLTA dal compositore' "$LOG" 2>/dev/null | head -1; }
keymap_ora()  { grep -c 'KEYMAP CAMBIATA' "$LOG" 2>/dev/null | head -1; }

azzera_testimone() { : > "$TEST"; chown "$UID_B:$UID_B" "$TEST"; }

# batti <etichetta> <disposizione dichiarata> <copione> [altri argomenti]
# ⛔ La redirezione sta DENTRO la stringa che il contenitore esegue, non
#    ATTORNO a `enter.sh`: attorno si mangerebbe la richiesta di `sudo` e il
#    comando resterebbe appeso in silenzio, per sempre (trappola 8).
batti() {
	local et=$1 disp=$2 cop=$3; shift 3

	# ⛔ La scena finisce dentro `--scena '...'`, dentro una stringa che il
	#    contenitore esegue: un apostrofo chiude l'apice e il client NON PARTE.
	#    ⚠ E il sintomo e' un testimone VUOTO, cioe' l'aspetto di «il carattere
	#      non e' arrivato».  ⇒ Si rifiuta, invece di sperare.
	case "$SCENA$disp$cop" in
	*"'"*) ko "⛔ IL BANCO, NON IL PRODOTTO: c'e' un apostrofo negli argomenti"
	       ko "   scena: $SCENA"
	       return 9 ;;
	esac

	rm -f "$LAVH/$et-cliente.json"
	bash /media/REMOTIX/enter.sh --root \
		"python3 $CB/06-b34-cliente.py --porta $PORTA --utente $UTENTE \
		 --parola-file $PAR --disposizione '$disp' --copione '$cop' \
		 --etichetta $et --lavoro $LAVC --scena '$SCENA' $* \
		 >> $LAVC/$et.log 2>&1"
	local u=$?

	# ⛔⭐ SI VERIFICA CHE IL CLIENT SIA PARTITO — `LEZIONI.md` §1.9 regola 1.
	#    «il client non e' partito» e «il carattere non e' arrivato» danno lo
	#    stesso testimone vuoto, e il secondo accusa il prodotto di un difetto
	#    del banco.  Il JSON esiste solo se il client e' arrivato in fondo.
	# ⚠ I casi 3 e 5 escono 2 APPOSTA (congedo atteso), e li' il JSON c'e' lo
	#   stesso: e' il JSON che si guarda, non il codice d'uscita.
	if [ ! -s "$LAVH/$et-cliente.json" ]; then
		ko "⛔ IL BANCO, NON IL PRODOTTO: il client «$et» non ha lasciato"
		ko "   nessun esito (uscita $u).  Coda del suo registro:"
		tail -6 "$LAVH/$et.log" 2>/dev/null | sed 's/^/        /'
		return 9
	fi
	return $u
}

# leggi <atteso> [canarino] — il verdetto del testimone
leggi() {
	local atteso=${1-} can=${2-a}
	python3 "$BH/06-b34-leggi.py" "$TEST" --atteso "$atteso" --canarino "$can"
}

registra() {
	printf '%s\n' "$1" >> "$ESITI"
}

# ⛔⭐ sonda_attacca <prefisso> <disposizione> <atteso>
#
#   L'atteso e' una parola sola: `APRE` · `0x0B` · `0x0E`.
#
# ⛔ Nasce il 21 agosto 2026 dal rilievo 4 di A9: il caso 5 stampava «sessione»
#    e «congedo» e **non li confrontava con niente**, quindi non poteva essere
#    ne' verde ne' rosso — e infatti il suo atteso e' rimasto rovesciato per
#    cinque giorni senza che nessuno se ne accorgesse.  ⚠ Un banco senza
#    verdetto non invecchia male: **non invecchia affatto**, perche' nessuno
#    puo' vedere quando ha smesso di dire il vero.
sonda_attacca() {
	local pre=$1 d=$2 atteso=$3
	local et; et="$pre-$(printf '%s' "$d" | tr -c 'a-zA-Z0-9' '_')"
	[ "$et" = "$pre-" ] && et="$pre-vuota"
	SCENA="$pre: ATTACCA con disposizione «$d»"
	batti "$et" "$d" "A:0.2" >/dev/null 2>&1
	local esito
	esito=$(python3 -c "
import json
try:
    j=json.load(open('$LAVH/$et-cliente.json'))
    if j.get('sessione'): print('APRE')
    else:
        c=str(j.get('congedo'))
        print('0x0B' if '0x0b' in c else ('0x0E' if '0x0e' in c else c))
except Exception:
    print('NIENTE')
")
	if [ "$esito" = "$atteso" ]; then
		ok "$(printf '%-26s %s' "«$d»" "$esito")"
	else
		ko "$(printf '%-26s %s   ⛔ ATTESO %s' "«$d»" "$esito" "$atteso")"
	fi
	registra "{\"caso\":\"$pre\",\"disposizione\":\"$d\",\"atteso\":\"$atteso\",\"misurato\":\"$esito\",\"carico\":\"$(carico)\",\"quando\":\"$(date -Iseconds)\"}"
}

CASO=${1:-tutti}

fai_caso1() {
	SCENA="caso1 — sessione «it»; ci si attacca dichiarando «it», si stacca, si riattacca dichiarando ANCORA «it»"
	log "CASO 1 — il riattacco con la STESSA disposizione (controllo positivo)"
	inf "carico: $(carico)"
	bash "$TERRENO" disposizione it >/dev/null 2>&1
	att "arriva «aèò\\@a» tutt'e due le volte."
	inf "⚠ E' il controllo positivo di «CODER.md» §3.3: se questo caso non e'"
	inf "   verde, il rosso degli altri non vuol dire niente."
	segna
	local r0; r0=$(ricambi_ora)

	azzera_testimone
	SCENA="caso1-A: primo attacco, dichiarata «it», sessione «it»"
	batti c1a it "$PRE $SONDA_ACC"
	inf "— primo attacco (dichiarata «it») —"
	leggi 'aèò\@a'
	local v1=$?

	azzera_testimone
	SCENA="caso1-B: RIattacco, dichiarata ancora «it», sessione «it»"
	batti c1b it "$PRE $SONDA_ACC"
	inf "— riattacco (dichiarata «it») —"
	leggi 'aèò\@a'
	local v2=$?

	local r1; r1=$(ricambi_ora)
	inf "ricambi_tastiera: $r0 → $r1"
	if [ "$v1" -eq 0 ] && [ "$v2" -eq 0 ]; then
		ok "controllo positivo VERDE: il banco sa produrre l'atteso"
	else
		ko "⛔ il controllo positivo NON e' verde ($v1/$v2): quel che segue non vale"
	fi
	registra "{\"caso\":\"1\",\"verdetto_a\":$v1,\"verdetto_b\":$v2,\"ricambi\":[$r0,$r1],\"carico\":\"$(carico)\",\"quando\":\"$(date -Iseconds)\"}"
}

fai_caso2() {
	log "CASO 2 — il riattacco DICHIARANDO un'altra disposizione"
	inf "carico: $(carico)"
	bash "$TERRENO" disposizione it >/dev/null 2>&1
	inf "la sessione resta «it»; cambia solo quel che il client DICHIARA in ATTACCA"
	att "⭐ L ATTESO E CAMBIATO IL 16 AGOSTO SERA, PERCHE E CAMBIATO IL CONTRATTO."
	att "   Il primo giro di questa sottofase misuro che §7.3 era FALSA: la"
	att "   disposizione dichiarata non toccava niente, e arrivava «aeo\\@a»"
	att "   identico a «it».  ⭐ L utente ha CONFERMATO §5-bis.7 — comanda il"
	att "   client — e adesso l atteso e l altro:"
	att "SE §5-bis.7 e ATTUATA ⇒ dichiarando «us» la sessione DIVENTA «us», e"
	att "   la e-grave e la o-grave — che su «us» non stanno su nessun tasto —"
	att "   NON arrivano: il testimone vede «a\\@a», e ricambi_tastiera CRESCE."
	att "SE NON e attuata (il difetto di ieri) ⇒ arriva tutto, e ricambi fermo."
	segna
	local r0 k0; r0=$(ricambi_ora); k0=$(keymap_ora)

	azzera_testimone
	SCENA="caso2-US: riattacco dichiarando «us», sessione «it»"
	batti c2us us "$PRE $SONDA_ACC"
	inf "— riattacco dichiarando «us» (sessione «it» all inizio) —"
	leggi 'a\@a'
	local vus=$?

	azzera_testimone
	SCENA="caso2-DE: riattacco dichiarando «de», sessione «it»"
	batti c2de de "$PRE $SONDA_ZY"
	inf "— riattacco dichiarando «de» (sessione «it»), sonda z/y —"
	leggi 'azy\a'
	local vde=$?

	local r1 k1; r1=$(ricambi_ora); k1=$(keymap_ora)
	inf "ricambi_tastiera: $r0 → $r1   ·   KEYMAP CAMBIATA: $k0 → $k1"
	if grep -q 'RIPIEGO DICHIARATO' "$LOG" 2>/dev/null; then
		inf "«RIPIEGO DICHIARATO» c'e' nel registro"
	else
		inf "⛔ «RIPIEGO DICHIARATO» NON compare: il confronto non e' stato fatto"
	fi
	# ⛔⭐ E IL VERDETTO ESCE DAL JSON — 21 agosto 2026, rilievo 4 di A9: i due
	#     verdetti sul carattere erano calcolati e scritti **solo** dentro
	#     `$ESITI`, cioe' nessuno li vedeva mai.
	if [ "$vus" -eq 0 ] && [ "$vde" -eq 0 ]; then
		ok "il carattere combacia in tutt'e due i giri (us e de)"
	else
		ko "⛔ ROSSO sul carattere: us=$vus de=$vde (0 = combacia)"
	fi
	[ "$k1" -gt "$k0" ] && ok "la keymap e' cambiata al riattacco (§5-bis.7 attuata)" \
		|| ko "⛔ KEYMAP CAMBIATA fermo a $k0: la disposizione dichiarata non ha toccato niente"
	registra "{\"caso\":\"2\",\"us\":$vus,\"de\":$vde,\"ricambi\":[$r0,$r1],\"keymap\":[$k0,$k1],\"esito\":$ESITO,\"carico\":\"$(carico)\",\"quando\":\"$(date -Iseconds)\"}"
}

fai_caso2s() {
	log "CASO 2s ⭐ — la disposizione DELLA SESSIONE cambia: «it» → «de»"
	inf "carico: $(carico)"
	inf "⛔ E' l'unica leva che fa DAVVERO rinascere il dispositivo tastiera:"
	inf "   STUDI.md §gnome §9 · meta-eis-client.c:761-781 — un cambio di keymap"
	inf "   fa «eis_device_remove» + «add_device», e il puntatore al vecchio"
	inf "   smette di funzionare SENZA ERRORE."
	att "se la keymap E' riletta a ogni DEVICE_ADDED ⇒ arriva «azy\\a»"
	att "se la keymap e' RIMASTA QUELLA VECCHIA    ⇒ arriva «ayz^a»"
	att "   (si manda il 44, che su «de» fa la «y»: un carattere DIVERSO)"
	att "e in tutt'e due i casi ricambi_tastiera DEVE crescere di almeno 1."
	# ⛔⛔ LA SCENA DI QUESTO CASO HA UN PRESUPPOSTO, E VA IMPOSTO — non
	#     sperato.  `[M]` 16 agosto 2026, trovato dal CONTROLLO POSITIVO:
	#     riacceso il server col binario guasto, il caso restava **verde** e
	#     `ricambi_tastiera` faceva 0 → 0.
	#
	# ⇒ La ragione: il palco muore col server (il figlio e la sua `libei`).  Se
	#   il figlio NASCE quando la sessione e' gia' `de`, il primo `DEVICE_ADDED`
	#   gli consegna gia' il tedesco: **non c'e' nessun ricambio da reggere**, e
	#   perfino la keymap letta una volta sola e' quella giusta.  ⛔ Cioe' il
	#   banco dichiarava verde un guasto vivo — `CODER.md` §3.4 in atto, dentro
	#   il banco che quel guasto doveva scoprire.
	#
	# ⇒ Il presupposto e': **il palco esiste GIA', e ha la keymap `it`**, prima
	#   che la disposizione cambi.  Si impone con un attacco di riscaldamento, e
	#   si VERIFICA che il figlio ci sia (`LEZIONI.md` §1.9 regola 1).
	bash "$TERRENO" disposizione it >/dev/null 2>&1
	sleep 1
	SCENA="caso2s-riscaldamento: si fa nascere il palco con la sessione ancora su it"
	batti c2s0 it "A:0.5"
	if bash "$TERRENO" figlio | grep -q 'FIGLIO nessuno'; then
		ko "⛔ IL PALCO, NON IL PRODOTTO: il figlio non c'e' dopo il"
		ko "   riscaldamento — non ci sara' nessun ricambio da reggere"
		return 9
	fi

	# ⛔⛔ E NON BASTA CHE IL FIGLIO CI SIA: DEVE AVERE L'ITALIANO.  `[M]` 16
	#     agosto 2026, e l'ha trovato il controllo positivo — due volte.
	#
	#     Il figlio sopravvive al distacco (I4) ma NON al riavvio del server, e
	#     nasce con la disposizione che la sessione ha **in quel momento**.  Se
	#     e' nato quando la sessione era gia' `de`, il cambio `it` → `de` non
	#     porta da nessuna parte: perfino una keymap letta una volta sola e'
	#     quella giusta, e il banco dichiara VERDE un guasto vivo.
	#
	# ⇒ Si RILEGGE quel che il palco ha davvero in mano — l'ultima riga
	#   «disposizione in vigore» del registro — invece di dedurlo da quel che
	#   `gsettings` dice.  «L'ho impostata» e «e' in vigore nel palco» sono due
	#   fatti diversi, ed e' la forma **E1**.
	local vig
	vig=$(grep 'disposizione in vigore (consegnata dalla sessione)' "$LOG" 2>/dev/null | tail -1)
	inf "il palco ha in mano: ${vig:-(nessuna riga)}"
	case "$vig" in
	*"[Italian]"*) ok "palco vivo E italiano: adesso il cambio e' un RICAMBIO vero" ;;
	*) ko "⛔ IL PALCO, NON IL PRODOTTO: il palco non ha l'italiano in mano."
	   ko "   Il cambio verso «de» non sarebbe un ricambio da reggere, e il"
	   ko "   verdetto sul carattere non vorrebbe dire niente."
	   ko "   ⇒ Rimedio: «disposizione it», poi «spegni»+«accendi», poi di nuovo qui."
	   return 9 ;;
	esac

	segna
	local r0 k0; r0=$(ricambi_ora); k0=$(keymap_ora)

	bash "$TERRENO" disposizione de
	sleep 2
	azzera_testimone
	SCENA="caso2s: la SESSIONE e’ passata a «de»; il client dichiara «de»"
	batti c2s de "$PRE $SONDA_ZY"
	inf "— sessione «de», sonda z/y —"
	leggi 'azy\a'
	local v=$?

	local r1 k1; r1=$(ricambi_ora); k1=$(keymap_ora)
	inf "ricambi_tastiera: $r0 → $r1   ·   KEYMAP CAMBIATA: $k0 → $k1"
	[ "$r1" -gt "$r0" ] && ok "il ricambio C'E' STATO ed e' contato" \
		|| ko "⛔ ricambi_tastiera NON e' cresciuto: il dispositivo non e' rinato"
	# ⛔ E anche qui il verdetto sul carattere esce dal JSON (rilievo 4 di A9).
	[ "$v" -eq 0 ] && ok "il carattere combacia: «azy\\a» sulla sessione tedesca" \
		|| ko "⛔ ROSSO sul carattere (verdetto $v): la keymap usata non e' quella della sessione"
	cresciuto | grep -E 'KEYMAP CAMBIATA|TOLTA dal compositore|disposizione in vigore' | tail -8 | sed 's/^/        /'
	registra "{\"caso\":\"2s\",\"verdetto\":$v,\"ricambi\":[$r0,$r1],\"keymap\":[$k0,$k1],\"carico\":\"$(carico)\",\"quando\":\"$(date -Iseconds)\"}"
	bash "$TERRENO" disposizione it >/dev/null 2>&1
}

fai_caso3() {
	log "CASO 3 — DISPOSIZIONE (0x0009) mandato A SESSIONE APERTA"
	inf "carico: $(carico)"
	att "⭐ ANCHE QUESTO ATTESO E CAMBIATO, ed e una cura di stasera."
	att "   Prima 0x0009 cadeva nel «default» e la connessione veniva CHIUSA con"
	att "   ERRORE_PROTOCOLLO: «l utente cambia disposizione mentre lavora e la"
	att "   sessione gli cade» — il gemello esatto del difetto di VISTA."
	att "⇒ ATTESO ADESSO: la connessione RESTA VIVA, nessun messaggio sul filo"
	att "   (§7.1 non ne prevede), e la keymap della sessione CAMBIA."
	segna
	azzera_testimone
	SCENA="caso3: DISPOSIZIONE(0x0009) «de» a sessione aperta, sessione «it»"
	batti c3 it "$PRE $SONDA_ACC" --manda-disposizione de
	inf "— che cosa ha visto il client —"
	python3 -c "
import json,sys
d=json.load(open('$LAVH/c3-cliente.json'))
for k in ('sessione','disposizione_mandata','dopo_disposizione','congedo','errore'):
    print('        %-22s %s' % (k, d.get(k)))
" 2>&1 | tail -8
	inf "— che cosa ha scritto il server —"
	cresciuto | grep -iE 'congedo|0x0009|DISPOSIZIONE' | tail -6 | sed 's/^/        /'
	# ⛔⭐ E ADESSO C'E' UN VERDETTO — 21 agosto 2026, rilievo 4 di A9.
	#     Questo caso stampava un JSON e non diceva mai se fosse andato bene:
	#     l'atteso era dichiarato in cinque righe e non confrontato con niente.
	#     ⛔ Un numero stampato e non confrontato e' un difetto.
	local c3viva c3keymap
	c3viva=$(python3 -c "
import json
d=json.load(open('$LAVH/c3-cliente.json'))
print(1 if (d.get('sessione') and not d.get('congedo') and not d.get('errore')
            and 'viva' in str(d.get('dopo_disposizione'))) else 0)
" 2>/dev/null || echo 0)
	c3keymap=$(cresciuto | grep -c "KEYMAP CAMBIATA.*disposizione «de " 2>/dev/null | head -1)
	if [ "${c3viva:-0}" = 1 ]; then
		ok "la connessione e RESTATA VIVA e nessun messaggio e arrivato sul filo"
	else
		ko "⛔ ROSSO: 0x0009 a sessione aperta NON lascia viva la connessione —"
		ko "   e il sintomo per l utente e «cambio tastiera e la sessione cade»"
	fi
	if [ "${c3keymap:-0}" -ge 1 ]; then
		ok "e la keymap della sessione e passata a «de» (riga KEYMAP CAMBIATA)"
	else
		ko "⛔ ROSSO: nessuna «KEYMAP CAMBIATA … disposizione «de …»: il"
		ko "   messaggio non ha cambiato niente, cioe non serve a niente"
	fi
	registra "{\"caso\":\"3\",\"viva\":${c3viva:-0},\"keymap_de\":${c3keymap:-0},\"esito\":$ESITO,\"carico\":\"$(carico)\",\"quando\":\"$(date -Iseconds)\"}"
}

fai_caso4() {
	log "CASO 4 ⛔ — IL TASTO PREMUTO AL DISTACCO (RCP.md §11)"
	inf "carico: $(carico)"
	inf "⛔ «la regola col rapporto danno/costo piu' alto del documento»: un"
	inf "   Maiusc rimasto giu' in una sessione che sopravvive al client"
	inf "   (invariante I4) rende il desktop inservibile, e nessuno collega le"
	inf "   due cose."
	inf "⚠ E il modo SILENZIOSO di fallire e' mandare il rilascio al dispositivo"
	inf "   VECCHIO: «input.c:184-188» manda a «in->tastiera_dev», e se fra il"
	inf "   premere e lo staccarsi il dispositivo e' stato ricreato, il vecchio"
	inf "   non da' errore — semplicemente non arriva niente."
	att "SE il rilascio funziona   ⇒ dopo il riattacco arriva «az» (minuscole)"
	att "SE il Maiusc e' rimasto giu' ⇒ arriva «AZ» (MAIUSCOLE)"
	att "SE non arriva niente     ⇒ INVALIDA (fuoco perso), non rossa"
	bash "$TERRENO" disposizione it >/dev/null 2>&1
	segna

	# --- 4a: si stacca col Maiusc giu', SENZA cambiare disposizione --------
	azzera_testimone
	SCENA="caso4a: si stacca col Maiusc (42) PREMUTO; sessione «it»"
	batti c4a it "$PRE U:61" --lascia-premuto 42
	inf "— il distacco col Maiusc giu' —"
	cresciuto | grep -iE 'rilascio al distacco|RILASCIO AL DISTACCO' | tail -4 | sed 's/^/        /'
	# ⛔⭐ 4a HA UN VERDETTO — 21 agosto 2026, rilievo 4 di A9.  Qui non c'e'
	#     nessun ricambio di dispositivo: il Maiusc e' premuto sullo STESSO
	#     dispositivo con cui ci si stacca, quindi il rilascio DEVE partire e
	#     DEVE essere contato.  ⇒ «rilascio al distacco: 0» qui e' un rosso
	#     secco, senza le sottigliezze degli orfani di 4b.
	local ril4a
	ril4a=$(cresciuto | grep 'rilascio al distacco:' | tail -1 \
	        | sed 's/.*rilascio al distacco: \([0-9]*\).*/\1/')
	inf "il «rilascio al distacco» di 4a: ${ril4a:-(nessuno)}"
	if [ "${ril4a:-0}" -ge 1 ] 2>/dev/null; then
		ok "il Maiusc e stato rilasciato e CONTATO (${ril4a})"
	else
		ko "⛔ ROSSO: «rilascio al distacco: ${ril4a:-nessuna riga}» — un tasto"
		ko "   premuto sullo stesso dispositivo con cui ci si stacca DEVE"
		ko "   partire, e qui non e partito (RCP.md §11)"
	fi
	sleep 1
	azzera_testimone
	SCENA="caso4a-B: riattacco dichiarando «us», e si guarda se il Maiusc e’ rimasto giu’"
	batti c4ab us "$PRE U:61 U:7A"
	inf "— riattacco (dichiarata «us»): minuscole o MAIUSCOLE? —"
	leggi 'az' ''
	local v4a=$?
	# ⛔ E il testimone si CONFRONTA, non si guarda: «az» minuscolo = il Maiusc
	#    non e' rimasto giu'.  «AZ» = e' rimasto, ed e' il desktop inservibile
	#    di `RCP.md` §11.
	case $v4a in
	0) ok "al riattacco arrivano MINUSCOLE: il Maiusc non e rimasto giu" ;;
	3) ko "⛔ INVALIDA: dal testimone non e arrivato niente — non si e misurato" ;;
	*) ko "⛔ ROSSO: al riattacco NON arriva «az» — se sono MAIUSCOLE, il Maiusc"
	   ko "   e rimasto premuto nella sessione e il desktop e inservibile" ;;
	esac
	registra "{\"caso\":\"4a\",\"rilascio\":${ril4a:-null},\"verdetto\":$v4a,\"esito\":$ESITO,\"carico\":\"$(carico)\",\"quando\":\"$(date -Iseconds)\"}"

	# --- 4b: il dispositivo RINASCE mentre il tasto e' giu' ----------------
	log "CASO 4b ⛔⛔ — il dispositivo RINASCE mentre il tasto e' premuto"
	inf "⛔ E' il modo silenzioso di fallire, provocato apposta: si preme il"
	inf "   Maiusc, si cambia la disposizione DELLA SESSIONE (il dispositivo"
	inf "   muore e rinasce col tasto ancora segnato), e poi ci si stacca."
	att "il rilascio deve arrivare al dispositivo NUOVO: dopo il riattacco «az»"
	att "se e' andato al vecchio (o non e' partito) ⇒ «AZ», e il registro dice"
	att "«rilascio al distacco: 0» — cioe' uno ZERO che si legge come «non c'era"
	att "niente premuto», che e' il peggiore dei silenzi."
	local r0; r0=$(ricambi_ora)
	azzera_testimone
	SCENA="caso4b: Maiusc giu’ + cambio keymap della sessione + distacco"
	# ⛔⛔ IL CAMBIO SI AGGANCIA AL TASTO, NON A UN `sleep` — `[M]` 16 agosto
	#     2026, e l'ha trovato il controllo positivo B.
	#
	#     Con `sleep 9` il ricambio e' caduto **0,4 s PRIMA** che il Maiusc
	#     andasse giu': il dispositivo moriva quando non c'era ancora niente di
	#     premuto, il guasto innestato non aveva niente da azzerare e il
	#     controllo positivo restava **verde**.  ⇒ Un banco tarato su un
	#     cronometro misura il cronometro.
	#
	# ⇒ Si aspetta la riga che dice che il tasto 42 e' **premuto davvero**
	#   (`rcp.c`, canale di input) e SOLO ALLORA si cambia la disposizione.
	#   Cosi' il dispositivo muore col tasto giu', che e' la scena dichiarata.
	# ⚠ E c'e' un tetto: se quella riga non arriva, si rinuncia e lo si DICE —
	#   un cambio fatto lo stesso misurerebbe un'altra scena senza dirlo.
	# ⛔ E si guarda SOLO da adesso in poi.  `[M]` 16 agosto 2026: guardando da
	#    `$SEGNO` — l'inizio del caso 4 — la spia trovava il Maiusc del caso
	#    **4a**, che era gia' passato, e cambiava la disposizione **subito**,
	#    cioe' prima ancora che il tasto di 4b esistesse.  ⇒ Una spia che
	#    guarda troppo indietro trova sempre qualcosa, ed e' la stessa forma
	#    d'errore del canarino: si crede di aver visto l'evento e si e' visto
	#    quello di prima.
	# ⛔⭐ E LA SPIA LASCIA UNA TRACCIA, invece di dirlo solo a video — 21 agosto
	#     2026.  Il verdetto di 4b deve poter distinguere «la scena non e'
	#     avvenuta» da «il prodotto ha sbagliato», e la prova che la scena e'
	#     avvenuta dev'essere **indipendente da quel che il prodotto scrive
	#     sugli orfani** — altrimenti il controllo positivo, che gli orfani li
	#     toglie, verrebbe letto come «il banco non ha provocato niente».
	local marca4b scena4b
	scena4b=$LAVH/c4b-scena
	rm -f "$scena4b"
	marca4b=$(stat -c %s "$LOG" 2>/dev/null || echo 0)
	(
		g=0
		while [ $g -lt 300 ]; do
			if tail -c "+$((marca4b + 1))" "$LOG" 2>/dev/null \
			   | grep -q 'POSIZIONE_TASTO codice evdev 42 .* premuto'; then
				printf '    --  ⭐ il Maiusc E GIU: adesso cambio la disposizione\n'
				bash "$TERRENO" disposizione de >/dev/null 2>&1
				: > "$scena4b"
				exit 0
			fi
			sleep 0.1; g=$((g+1))
		done
		printf '    --  ⛔ IL BANCO: il tasto 42 non e mai risultato premuto in 30 s,\n'
		printf '    --     NON ho cambiato la disposizione: la scena non e quella\n'
	) &
	local sfondo=$!
	batti c4b it "$PRE U:61" --lascia-premuto 42 --prima-del-distacco 8
	wait $sfondo 2>/dev/null
	inf "— il distacco, col dispositivo appena rinato —"
	cresciuto | grep -iE 'rilascio al distacco|TOLTA dal compositore|KEYMAP CAMBIATA' | tail -6 | sed 's/^/        /'

	# ⛔⛔ IL NUMERO SI PRENDE ADESSO, non alla fine del caso — `[M]` 16 agosto
	#     2026, e sul binario SANO diceva **0** mentre il vero conto era 1.
	#
	#     La riga «rilascio al distacco» la scrive OGNI distacco, e dopo questo
	#     ne viene un altro: quello del giro di riattacco che va a guardare le
	#     maiuscole, che non ha niente di premuto e scrive **0**.  ⇒ Prendendo
	#     l ULTIMA riga del caso si legge il numero del distacco SBAGLIATO, e si
	#     accusa il prodotto di aver perso un tasto che non aveva perso.
	#
	# ⚠ E' la stessa famiglia di `LEZIONI.md` §1.9: il numero c era, si e letto
	#   quello di un altro.
	local ril4b
	ril4b=$(cresciuto | grep 'rilascio al distacco:' | tail -1 \
	        | sed 's/.*rilascio al distacco: \([0-9]*\).*/\1/')
	inf "il «rilascio al distacco» DI QUESTO distacco: ${ril4b:-(nessuno)}"
	local r1; r1=$(ricambi_ora)
	inf "ricambi_tastiera: $r0 → $r1"
	sleep 1
	azzera_testimone
	SCENA="caso4b-B: riattacco dichiarando «it», sessione ora «de»"
	batti c4bb it "$PRE U:61 U:7A"
	inf "— riattacco: minuscole o MAIUSCOLE? —"
	leggi '' ''

	# ⛔⛔ E IL VERDETTO DI 4b NON PUO' STARE SUL CARATTERE — `[M]` 16 agosto
	#     2026, e l'ha stabilito il controllo positivo B, che e' andato a finire
	#     dove non me l'aspettavo.
	#
	#     Col guasto «i tasti se ne vanno col dispositivo» innestato, il nostro
	#     conto e' diventato **`rilascio al distacco: 0`** — cioe' esattamente
	#     la firma rossa dichiarata — ⛔ **ma dal testimone e' arrivato «az»
	#     minuscolo lo stesso**.  ⇒ **Mutter rilascia da se' i tasti tenuti giu'
	#     su un dispositivo che distrugge**: il compositore ci copre il guasto.
	#
	# ⚠ Da cui: sul CARATTERE, 4b e' verde col codice giusto **e col codice
	#   sbagliato**.  E' `CODER.md` §3.4 nella sua forma piu' insidiosa — una
	#   prova verde mentre il difetto e' vivo — e la cura non e' guardare piu'
	#   forte il carattere: e' **cambiare grandezza**.
	#
	# ⇒ Il verdetto di 4b sta sul NUMERO che il figlio scrive: se il ricambio e'
	#   avvenuto col tasto giu', il rilascio DEVE contare almeno 1.  Uno zero li'
	#   vuol dire che il nostro conto ha perso il tasto — e il giorno che il
	#   compositore non ci coprisse (KWin, wlroots: fase 11) il desktop
	#   dell'utente resterebbe col Maiusc premuto.
	# ⛔⛔⭐ E IL VERDETTO E' CAMBIATO UN'ALTRA VOLTA — 16 agosto sera, e questa
	#      volta perche' e' cambiato IL CODICE, non il contratto.
	#
	#      La stesura di prima pretendeva «rilascio al distacco >= 1».  ⛔ Con
	#      `input.c` di stasera quel numero e' **giustamente 0**: l'anello del
	#      puntatore (sottofase 6.1) ha MISURATO che
	#      `meta-eis-client.c:638-645` **scarta in silenzio** un rilascio
	#      mandato sul dispositivo NUOVO per un tasto premuto sul VECCHIO.
	#      ⇒ Quel rilascio non puo' partire, e fingere di contarlo sarebbe
	#        scrivere «fatto» accanto a un desktop col tasto giu'.
	#
	# ⇒ La grandezza che discrimina non e' piu' il conto, e' **la
	#   DICHIARAZIONE**: l'orfano dev'essere NOMINATO nel registro.
	#     · `0` **con** la riga sugli ORFANI  = onesto, ed e' verde;
	#     · `0` **senza** nessuna riga        = ⛔ il silenzio, ed e' il difetto.
	#
	# ⚠ E che il desktop resti sano lo dice il testimone, non questo numero:
	#   `[M]` arriva «az» minuscolo perche' **Mutter rilascia da se'** i tasti
	#   del dispositivo che distrugge (misurato dal controllo positivo B).
	# ⛔⛔⭐ E IL VERDETTO E' CAMBIATO UNA TERZA VOLTA — 21 agosto 2026, rilievo 3
	#      della revisione avversariale di A9, ⛔ **e il ramo verde era la firma
	#      della scena MANCATA**.
	#
	#      Diceva: `ril4b >= 1` ⇒ *«il rilascio e' PARTITO sul dispositivo
	#      nuovo»*, verde.  ⛔ Ma se la scena RIESCE — cioe' se il dispositivo
	#      muore col tasto giu' — `segna_orfani()` (`input.c:709`) marca quel
	#      tasto come orfano, e `input_rilascia_tutto()` (`input.c:1299`) conta
	#      gli orfani **in una variabile diversa**: `quanti` resta a **zero**.
	#      ⇒ `ril4b >= 1` si puo' ottenere **soltanto se il ricambio non e'
	#        avvenuto**, cioe' quel verde certificava che la scena NON era
	#        successa.  ⚠ E' il difetto peggiore che un banco possa avere: dava
	#        il colore giusto per la ragione opposta.
	#
	#      ⛔ E il conto che l'avrebbe smascherato — `r0 → r1` — era **stampato
	#        e mai confrontato**, mentre il caso 2s lo confronta davvero.
	#        *«Ogni numero che il banco stampa e non confronta e' un difetto.»*
	#
	# ⇒ IL VERDETTO ADESSO HA DUE PIANI, e il primo NON e' sul prodotto:
	#
	#   1. **la scena e' avvenuta?**  E la prova NON puo' venire da quel che il
	#      prodotto scrive sugli orfani — sarebbe circolare, e il controllo
	#      positivo (che gli orfani li toglie) verrebbe letto come «il banco non
	#      ha provocato niente».  ⇒ Le due prove indipendenti sono:
	#        · la spia ha visto il **tasto 42 premuto** e SOLO ALLORA ha cambiato
	#          la disposizione (il file `c4b-scena`);
	#        · `r1 > r0`: il dispositivo tastiera e' **davvero** morto.
	#      Se una manca ⇒ non e' rosso, e' **IL BANCO**.
	#   2. solo allora si guarda il prodotto:
	#      · `0` **con** la riga sugli ORFANI  = onesto, ed e' VERDE;
	#      · `0` **senza** nessuna riga        = ⛔ il silenzio, ed e' il difetto
	#        (ed e' esattamente quel che produce il guasto «tasti-col-vecchio»);
	#      · `>= 1` con la scena avvenuta      = ⛔ il tasto NON e' stato marcato
	#        orfano: il conto degli orfani ha perso il ricambio.
	local orfani scena_orfani
	orfani=$(cresciuto | grep -c 'ORFANI\|NON PARTE' 2>/dev/null | head -1)
	scena_orfani=$(cresciuto | grep -c 'erano PREMUTI sul dispositivo che il compositore ha appena tolto' 2>/dev/null | head -1)
	inf "righe che dichiarano un ORFANO in questo caso: ${orfani:-0}"
	inf "righe «erano PREMUTI sul dispositivo appena tolto»: ${scena_orfani:-0}"
	inf "ricambi_tastiera: $r0 → $r1   (⛔ adesso CONFRONTATO, non solo stampato)"
	[ -f "$scena4b" ] && inf "la spia ha cambiato la keymap COL TASTO GIU: si" \
		|| inf "la spia ha cambiato la keymap COL TASTO GIU: NO"

	if [ ! -f "$scena4b" ] || [ "${r1:-0}" -le "${r0:-0}" ]; then
		ko "⛔ IL BANCO, NON IL PRODOTTO: la scena di 4b NON e avvenuta."
		ko "   spia col tasto giu: $([ -f "$scena4b" ] && echo si || echo NO) · ricambi $r0 → $r1"
		ko "   ⇒ il dispositivo non e morto col tasto giu, e QUALUNQUE colore"
		ko "     sul prodotto sarebbe rubato.  Rimedio: allungare l attesa fra"
		ko "     il tasto e il cambio di keymap, e rilanciare."
	elif [ "${ril4b:-0}" -ge 1 ] 2>/dev/null; then
		ko "⛔ ROSSO: la scena E avvenuta, eppure «rilascio al distacco:"
		ko "   ${ril4b}» conta dei rilasci NORMALI — cioe il tasto premuto sul"
		ko "   dispositivo morto NON e stato marcato orfano.  Il conto degli"
		ko "   orfani ha perso il ricambio, ed e il difetto che 4b cerca."
	elif [ "${orfani:-0}" -ge 1 ]; then
		ok "⭐ la scena E avvenuta, zero rilasci, e l ORFANO E DICHIARATO:"
		inf "   e la verita, non un silenzio (il rilascio non poteva partire:"
		inf "   meta-eis-client.c:638-645 lo scarta senza errore)"
	else
		ko "⛔ ROSSO: «rilascio al distacco: ${ril4b:-?}» e NESSUNA riga sugli"
		ko "   orfani — cioe uno ZERO che si legge come «non c era niente premuto»."
		ko "   ⚠ E su un compositore che non ci coprisse, il Maiusc resterebbe giu."
	fi
	registra "{\"caso\":\"4b\",\"ricambi\":[$r0,$r1],\"rilascio\":${ril4b:-null},\"orfani\":${orfani:-0},\"scena_orfani\":${scena_orfani:-0},\"esito\":$ESITO,\"carico\":\"$(carico)\",\"quando\":\"$(date -Iseconds)\"}"
	bash "$TERRENO" disposizione it >/dev/null 2>&1
}

fai_caso5() {
	log "CASO 5 — la disposizione IGNOTA o MALFORMATA"
	inf "carico: $(carico)"
	att "«RCP.md» §4.5 vuole i due guasti DISTINTI:"
	att "   fuori forma          ⇒ ERRORE_PROTOCOLLO (0x0B)"
	att "   ben formata, ignota  ⇒ SESSIONE_NON_SERVIBILE (0x0E)"
	# ⛔⭐ L'ATTESO DI QUESTO CASO E' CAMBIATO — 21 agosto 2026, e non perche'
	#     abbia cambiato idea io: perche' e' cambiato IL CODICE.
	#
	#     La stesura di ieri diceva *«hu e tr esistono su questa macchina ma
	#     NON sono nell'elenco: l'atteso e' che vengano RIFIUTATI»* e *«la
	#     variante non la controlla nessuno: it(nonesiste) PASSA»*.  ⛔ Tutt'e
	#     due le righe adesso sono FALSE: la cura del 16 agosto ha portato la
	#     domanda a XKB (`webtransport.c:1626` → `tastiera.c`), e la variante
	#     ci entra dentro perche' `it(nonesiste)` non compila.
	#
	# ⚠ Si riscrive l'atteso invece di lasciarlo: un atteso che descrive il
	#   codice di ieri fa leggere una cura come una regressione.
	att "⭐ CAMBIATO il 21 agosto 2026 — la domanda «esiste?» adesso va a XKB:"
	att "   ⇒ «hu» e «tr» esistono su questa macchina: l'atteso e' che PASSINO."
	att "   ⇒ «it(nonesiste)» e' ben formato ma non compila: RIFIUTATA con 0x0E."
	att "   ⇒ «it()» e' FUORI FORMA (variante vuota): l'atteso e' 0x0B, non 0x0E."
	att "   ⇒ «IT» e' ben formato ma questa macchina non ce l'ha (XKB distingue"
	att "     le maiuscole): l'atteso e' 0x0E — e fino al 21 agosto era 0x0B."
	segna
	# ⛔ Ogni riga ha il suo atteso ACCANTO, e viene confrontato: prima erano
	#    dieci stampe senza giudizio.
	sonda_attacca c5 "zz"                 0x0E
	sonda_attacca c5 "it(qwertz)"         0x0E
	sonda_attacca c5 "it(nonesiste)"      0x0E
	sonda_attacca c5 "it()"               0x0B
	sonda_attacca c5 "de(neo)"            APRE
	sonda_attacca c5 "hu"                 APRE
	sonda_attacca c5 "tr"                 APRE
	sonda_attacca c5 "../../etc/passwd"   0x0B
	sonda_attacca c5 "IT"                 0x0E
	sonda_attacca c5 "it,"                0x0B
	sonda_attacca c5 ""                   0x0B
	inf "— che cosa ha scritto il server —"
	cresciuto | grep -iE 'congedo motivo|disposizione' | tail -20 | sed 's/^/        /'
}

fai_caso6() {
	log "CASO 6 ⛔⛔ — «Ctrl+Z» SU DISPOSIZIONE DIVERSA (la scena che l utente sente)"
	inf "carico: $(carico)"
	inf "⛔ «DECISIONI.md» §5-bis.6: le lettere viaggiano come LETTERE, le"
	inf "   scorciatoie come POSIZIONI.  Su una tastiera tedesca la «Z» sta dove"
	inf "   da noi sta la «Y» — evdev 21 contro 44.  ⇒ Un client tedesco che"
	inf "   preme «Ctrl+Z» manda Ctrl + evdev 21."
	inf "⚠ E in un terminale la differenza si legge in un byte:"
	inf "     Ctrl+Z = 1a   ·   Ctrl+Y = 19"
	att "SE la disposizione e RINEGOZIATA (§5-bis.7 attuata) ⇒ la sessione e «de»,"
	att "   evdev 21 e la «Z», e arriva **1a** — l annulla annulla."
	att "SE NON e rinegoziata (il difetto di ieri sera) ⇒ la sessione resta «it»,"
	att "   evdev 21 e la «Y», e arriva **19** — cioe «rifai» invece di «annulla»."
	att "⛔ Nessuno dei due e un errore visibile: e il sintomo «l annulla non"
	att "   funziona», che nessuno collega alla disposizione."

	# ⛔ Si parte SEMPRE da «it», e lo si impone: il caso misura il passaggio.
	bash "$TERRENO" disposizione it >/dev/null 2>&1
	sleep 2
	segna
	azzera_testimone
	# Ctrl (29) giu' · evdev 21 giu' e su · Ctrl su — cioe' «Ctrl+Z» battuto su
	# una tastiera TEDESCA, che e' quel che il client dichiara di avere.
	SCENA="caso6: il client dichiara «de» e batte Ctrl+evdev21, cioe Ctrl+Z su tastiera tedesca"
	batti c6 de "$PRE P:29:1 P:21:1 P:21:0 P:29:0"
	inf "— che cosa e arrivato al testimone —"
	python3 "$BH/06-b34-leggi.py" "$TEST" --canarino ''
	local arrivato
	arrivato=$(python3 "$BH/06-b34-leggi.py" "$TEST" --canarino '' --zitto \
	           | grep -o '«.*»' | head -1)
	inf "— e che cosa ha fatto il server —"
	cresciuto | grep -iE '5-bis.7|disposizione «|KEYMAP CAMBIATA|TOLTA dal compositore' \
		| tail -6 | sed 's/^/        /'
	case "$arrivato" in
	*$'\x1a'*) ok "⭐ e arrivato Ctrl+Z (1a): la disposizione E stata rinegoziata" ;;
	*$'\x19'*) ko "⛔ ROSSO: e arrivato Ctrl+Y (19) — la disposizione NON e stata"
	            ko "   rinegoziata, e l annulla dell utente fa «rifai»" ;;
	*) dub "?? non e arrivato ne 1a ne 19: guarda le righe qui sopra" ;;
	esac
	registra "{\"caso\":\"6\",\"carico\":\"$(carico)\",\"quando\":\"$(date -Iseconds)\"}"
}

# ===========================================================================
# ⛔⛔ CASO 7 — LA DISPOSIZIONE ESOTICA, E IL METRO E' **IL CARATTERE**
# ===========================================================================
#
# ⭐ Il caso 5 guarda se la sessione si APRE.  ⛔ «Si apre» non e' la misura:
#    un server che accettasse `hu` e poi lasciasse la sessione italiana
#    aprirebbe benissimo la sessione **e scriverebbe le lettere sbagliate**.
#    ⇒ Qui si guarda il CARATTERE che esce dall'altra parte, che e' l'unica
#      cosa che l'utente ungherese sente.
#
# ⛔ E l'atteso NON lo scrivo io: lo calcola `06-b34-tabella.c esotiche`,
#    cioe' `src/tastiera.c` — lo stesso file che nel prodotto risponde al
#    gancio `disposizione_esiste` e che traduce le LETTERE in posizioni.
#
#      hu   ű U+0171 → evdev 43     ő U+0151 → 26     z → 21 (QWERTZ)
#      tr   ı U+0131 → 23           ğ U+011F → 26
#      gr   α U+03B1 → 30           ⛔ canarino «1», non «a»
#      ua   ї U+0457 → 27           ⛔ canarino «1», non «a»
#      it   ű        → NON PRODUCIBILE   ⭐ e' il controllo negativo
#
# ⚠⚠ E IL CANARINO NON E' SEMPRE LA «a» — ed e' un difetto che questo banco
#    avrebbe avuto se l'atteso me lo fossi scritto a mano: su `gr` il tasto 30
#    fa una **α**, e la `a` non esiste affatto.  Con il canarino `a` ogni prova
#    greca sarebbe uscita **INVALIDA**, e avrei letto un difetto del banco come
#    «il fuoco non c'era».  ⇒ Il canarino di ciascuna disposizione lo sceglie
#    la tabella, chiedendolo alla disposizione.
#
# ⛔⛔ E UN SECONDO INCIAMPO SCHIVATO DALLA STESSA TABELLA: la `ı` turca
#    (U+0131) **e' producibile anche su `it`** (Maiusc+AltGr+23).  ⇒ Usarla
#    come prova per `tr` avrebbe dato un banco **VERDE anche a disposizione NON
#    rinegoziata** — `CODER.md` §3.4 in piena regola.  La prova che discrimina
#    e' la **ğ**, che su `it` non esiste.
#
# ⇒ L'ATTESO IN DUE COLONNE, come vuole il mandato avversariale:
#     rinegoziata      ⇒ «<canarino><esotico><canarino>»
#     NON rinegoziata  ⇒ «<canarino><canarino>» e nel registro la riga
#                        «U+xxxx non e' producibile … NON mandato niente»
#   ⚠ I due esiti si distinguono in un carattere, e nessuno dei due e' un
#     errore visibile: il secondo e' «la mia tastiera non scrive», che nessuno
#     collega alla disposizione.
fai_caso7() {
	log "CASO 7 ⛔⛔ — LE DISPOSIZIONI ESOTICHE, e si giudica IL CARATTERE"
	inf "carico: $(carico)"
	att "l'atteso e' quello di «06-b34-tabella.c esotiche», cioe' del PRODOTTO"

	# prova7 <disposizione> <U+ esotico> <canarino> <canarino in esadecimale> <atteso utf8>
	prova7() {
		local disp=$1 cp=$2 can=$3 canx=$4 atteso=$5
		local et; et="c7-$(printf '%s-%s' "$disp" "$cp" | tr -c 'a-zA-Z0-9-' '_')"

		# ⛔ Si riparte SEMPRE da «it»: senza, la seconda prova esotica
		#    troverebbe la sessione gia' cambiata dalla prima e misurerebbe
		#    «e' rimasta com'era» credendo di misurare «e' cambiata».
		bash "$TERRENO" disposizione it >/dev/null 2>&1
		sleep 1.5
		segna
		local k0; k0=$(keymap_ora)
		azzera_testimone
		SCENA="caso7: sessione «it», il client dichiara «$disp» e batte U+$cp"
		printf '\n    \033[1m%s · U+%s\033[0m\n' "$disp" "$cp"
		att "rinegoziata ⇒ «$atteso»   ·   NON rinegoziata ⇒ «$can$can»"
		batti "$et" "$disp" "$PRE U:$canx U:$cp U:$canx"
		leggi "$atteso" "$can"
		local v=$?
		local k1; k1=$(keymap_ora)
		inf "KEYMAP CAMBIATA: $k0 → $k1"
		# ⛔⛔ E NON BASTA CHE IL CONTATORE CRESCA — difetto del banco trovato
		#     dal controllo positivo C, 21 agosto 2026.  Col guasto innestato
		#     la PRIMA prova stampava lo stesso «la keymap E' cambiata», perche'
		#     il figlio era appena nato e la sua prima keymap conta come un
		#     cambio: `KEYMAP CAMBIATA: … (era: nessuna) → «della sessione
		#     [Italian]»`.  ⚠ Un verde su una riga che dice «Italian» mentre il
		#     client ha dichiarato «hu» e' il verde peggiore che ci sia.
		#   ⇒ Si pretende che la riga NOMINI la disposizione dichiarata.
		if cresciuto | grep -q "KEYMAP CAMBIATA.*disposizione «$disp "; then
			ok "la keymap della sessione e' cambiata E la riga nomina «$disp»"
		else
			ko "⛔ nessuna «KEYMAP CAMBIATA … disposizione «$disp …»: la"
			ko "   disposizione dichiarata NON e' quella che e' andata in vigore"
		fi
		cresciuto | grep -iE 'non e. producibile|KEYMAP CAMBIATA|5-bis.7' | tail -4 | sed 's/^/        /'
		registra "{\"caso\":\"7\",\"disposizione\":\"$disp\",\"carattere\":\"U+$cp\",\"verdetto\":$v,\"keymap\":[$k0,$k1],\"carico\":\"$(carico)\",\"quando\":\"$(date -Iseconds)\"}"
	}

	prova7 hu  171 a 61 $'aűa'
	prova7 hu  151 a 61 $'aőa'
	prova7 tr  11F a 61 $'ağa'
	prova7 gr  3B1 1 31 $'1α1'
	prova7 ua  457 1 31 $'1ї1'
	# ⭐⭐ E LA VARIANTE CON LA MAIUSCOLA, che fino al 21 agosto non arrivava
	#     nemmeno a chiedere: `de(T3)`, la disposizione TIPOGRAFICA tedesca.
	# ⛔ Il carattere non e' scelto da me: `06-b34-tabella.c posizione` dice che
	#    `‑` U+2011 (trattino unificatore) su `de(T3)` sta su **195+100+53** —
	#    tre tasti, e il 195 e' il **livello 5**, che il `de` normale non ha
	#    affatto.  ⇒ Con la sola `de` quel carattere NON e' producibile, e la
	#    prova distingue «ha caricato la variante» da «ha caricato la
	#    disposizione e buttato la variante», che e' il guasto vero da temere.
	prova7 "de(T3)" 2011 a 61 $'a‑a'

	# ⭐⭐ IL CONTROLLO NEGATIVO, e vive DENTRO il caso: la stessa ű su una
	#     sessione dichiarata «it» NON deve arrivare, e il registro deve dirlo.
	#     ⛔ Senza di lui il verde di sopra non distingue «la disposizione e'
	#       stata applicata» da «questo carattere arriva comunque».
	log "CASO 7-neg ⭐ — la stessa «ű» dichiarando «it»: NON deve arrivare"
	att "atteso «aa» (la ű sparisce) + la riga «U+0171 non e' producibile»"
	bash "$TERRENO" disposizione it >/dev/null 2>&1
	sleep 1.5
	segna
	azzera_testimone
	SCENA="caso7-neg: sessione e client su «it», si batte la ű ungherese"
	batti c7-neg it "$PRE U:61 U:171 U:61"
	leggi 'aa' a
	local vn=$?
	local nonprod
	nonprod=$(cresciuto | grep -c "U+0171 non e. producibile")
	inf "righe «U+0171 non e' producibile»: $nonprod"
	if [ "$vn" -eq 0 ] && [ "$nonprod" -ge 1 ]; then
		ok "⭐ il controllo negativo TIENE: la ű non arriva, e il server lo DICE"
	else
		ko "⛔ il controllo negativo NON tiene (verdetto $vn, righe $nonprod):"
		ko "   allora il verde delle prove esotiche non prova la rinegoziazione"
	fi
	registra "{\"caso\":\"7-neg\",\"verdetto\":$vn,\"non_producibile\":$nonprod,\"carico\":\"$(carico)\",\"quando\":\"$(date -Iseconds)\"}"
	bash "$TERRENO" disposizione it >/dev/null 2>&1
}

# ===========================================================================
# ⛔⛔ CASO 8 — IL SECONDO ELENCO SCRITTO A MANO: **L'ALFABETO DEL NOME**
# ===========================================================================
#
# ⭐ La cura del 16 agosto ha tolto l'elenco fisso delle 20 disposizioni e ha
#    portato la domanda a XKB.  ⛔ Ma DAVANTI al gancio e' rimasto un secondo
#    elenco scritto a mano, e nessuno l'aveva guardato: **quali caratteri sono
#    ammessi nel nome** (`disposizione_ben_formata`, `rcp.c`).
#
# `[M]` 21 agosto 2026, misurato chiedendolo al sistema attraverso il prodotto
#   (`06-b34-tabella.c elenco`, cioe' `src/tastiera.c`), su tutte le **590**
#   coppie disposizione/variante che `/usr/share/X11/xkb/rules/evdev.lst`
#   dichiara su questa macchina:
#
#     589 su 590 si compilano — questa macchina le HA (l'unica che no e'
#         `custom`, che e' un segnaposto senza file)
#     ⛔ 9 di quelle 589 hanno una MAIUSCOLA nel nome, e il controllo di
#        forma di `rcp.c` ammetteva solo `[a-z0-9]` + `[_-]` nella variante:
#
#          de(T3)  ie(CloGaelach)  ie(UnicodeExpert)  in(tamilnet_TAB)
#          in(tamilnet_TSCII)  jp(OADG109A)  lk(tam_TAB)
#          ru(phonetic_YAZHERTY)  ua(macOS)
#
# ⇒ E' la forma D1 sopravvissuta alla propria cura: un tedesco che usa la T3
#   (la disposizione tipografica) non riceve nemmeno «questa macchina non ce
#   l'ha» — riceve **ERRORE_PROTOCOLLO**, cioe' «il tuo client e' rotto».
#   ⛔ E' il peggiore dei due, perche' manda a cercare il guasto dall'altra
#     parte del filo.
#
# ⚠ E l'altro verso: `it()` — variante VUOTA — era **ben formata** per `rcp.c`
#   e mal formata per `tastiera.c`, ⇒ arrivava `SESSIONE_NON_SERVIBILE` a una
#   stringa fuori forma.  §4.5 vuole i due guasti distinti, e li' erano uniti.
fai_caso8() {
	log "CASO 8 ⛔⛔ — l'ALFABETO del nome: le varianti che la macchina HA"
	inf "carico: $(carico)"
	att "⛔ L'ATTESO LO DA' IL SISTEMA, non io: le 9 qui sotto si compilano su"
	att "   questa macchina (misurato da «06-b34-tabella.c elenco»), quindi"
	att "   DEVONO aprire la sessione.  Un 0x0B su una di loro e' un difetto."
	att "⇒ deve APRIRE:  de(T3) ie(CloGaelach) jp(OADG109A) ua(macOS)"
	att "                ru(phonetic_YAZHERTY) hu(102_qwerty_dot_dead)"
	att "⇒ deve dare 0x0B (fuori forma):   it()  it,  ../../etc/passwd  «»"
	att "⇒ deve dare 0x0E (ben formata, ignota):   it(nonesiste)  zz  IT"
	segna

	# ⛔ Si usa `sonda_attacca`, che e' la stessa del caso 5: due sonde scritte
	#    due volte danno due risposte sotto la stessa etichetta (forma E2).
	sonda8() { sonda_attacca c8 "$1" "$2"; }

	local ESITO8_PRIMA=$ESITO
	printf '\n    \033[1mle varianti che la macchina HA — devono APRIRE\033[0m\n'
	sonda8 "de(T3)"                  APRE
	sonda8 "ie(CloGaelach)"          APRE
	sonda8 "jp(OADG109A)"            APRE
	sonda8 "ua(macOS)"               APRE
	sonda8 "ru(phonetic_YAZHERTY)"   APRE
	sonda8 "hu(102_qwerty_dot_dead)" APRE
	sonda8 "de(neo)"                 APRE
	printf '\n    \033[1mfuori forma — devono dare 0x0B ERRORE_PROTOCOLLO\033[0m\n'
	sonda8 "it()"                    0x0B
	sonda8 "it,"                     0x0B
	sonda8 "../../etc/passwd"        0x0B
	sonda8 "it(a"                    0x0B
	sonda8 "it(a)b"                  0x0B
	sonda8 ""                        0x0B
	printf '\n    \033[1mben formate ma ignote — devono dare 0x0E SESSIONE_NON_SERVIBILE\033[0m\n'
	sonda8 "zz"                      0x0E
	sonda8 "IT"                      0x0E
	sonda8 "it(nonesiste)"           0x0E
	sonda8 "custom"                  0x0E

	printf '\n'
	[ "$ESITO" = "$ESITO8_PRIMA" ] && ok "⭐ CASO 8 VERDE" \
		|| printf '    \033[1;31mNO\033[0m  ⛔ CASO 8 ROSSO — vedi le righe qui sopra\n'
	inf "— che cosa ha scritto il server —"
	cresciuto | grep -iE 'congedo motivo|disposizione' | tail -12 | sed 's/^/        /'
}

# ===========================================================================
# ⛔⭐ LA TABELLA SI COSTRUISCE E SI ESEGUE — 21 agosto 2026, rilievo 5 di A9
# ===========================================================================
#
# Il documento di fase vantava *«l'atteso lo calcola il prodotto»*, ⛔ e
# `06-b34-tabella.c` **non era costruito ne' eseguito da nessuno script**: era
# citato in due commenti.  ⚠ Un pregio che nessun copione esercita e' un pregio
# che si puo' perdere senza che niente diventi rosso.
#
# ⇒ Adesso `tabella` e' un caso come gli altri, e i casi 7 e 8 lo chiamano
#   PRIMA di misurare: se l'atteso non si puo' calcolare, non si misura.
TAB=$LAVH/06-b34-tabella
fai_tabella() {
	log "TABELLA — l'atteso, calcolato da «src/tastiera.c» (il PRODOTTO)"
	if ! bash /media/REMOTIX/enter.sh --root \
		"cd $CB && cc -O2 -o $LAVC/06-b34-tabella 06-b34-tabella.c ../src/tastiera.c \
		 ../src/registro.c \$(pkg-config --cflags --libs xkbcommon glib-2.0)" ; then
		ko "⛔ IL BANCO: «06-b34-tabella.c» NON si costruisce — senza di lui"
		ko "   l atteso dei casi 7 e 8 sarebbe una mia opinione"
		return 9
	fi
	ok "costruita: $TAB"
	bash /media/REMOTIX/enter.sh --root "$LAVC/06-b34-tabella esotiche 2>/dev/null" \
		| sed 's/^/        /'
	return 0
}

case "$CASO" in
tabella) fai_tabella ;;
caso1)  fai_caso1 ;;
caso2)  fai_caso2 ;;
caso2s) fai_caso2s ;;
caso3)  fai_caso3 ;;
caso4)  fai_caso4 ;;
caso5)  fai_caso5 ;;
caso6)  fai_caso6 ;;
caso7)  fai_tabella && fai_caso7 ;;
caso8)  fai_tabella && fai_caso8 ;;
tutti)  fai_tabella; fai_caso1; fai_caso2; fai_caso2s; fai_caso3; fai_caso4; fai_caso5; fai_caso6; fai_caso7; fai_caso8 ;;
*) ko "caso sconosciuto: $CASO"; exit 2 ;;
esac

log "Fatto — esiti in $ESITI"
inf "carico finale: $(carico)"
# ⛔ E il verdetto esce anche dalla porta di servizio: `$?`.
if [ "$ESITO" = 0 ]; then
	ok "⭐ VERDE — nessun «NO» in tutto il giro"
else
	printf '    \033[1;31mNO\033[0m  ⛔ ROSSO — c e almeno un «NO» qui sopra\n'
fi
exit "$ESITO"
