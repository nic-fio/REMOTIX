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

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
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
	registra "{\"caso\":\"2\",\"us\":$vus,\"de\":$vde,\"ricambi\":[$r0,$r1],\"keymap\":[$k0,$k1],\"carico\":\"$(carico)\",\"quando\":\"$(date -Iseconds)\"}"
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
	registra "{\"caso\":\"3\",\"carico\":\"$(carico)\",\"quando\":\"$(date -Iseconds)\"}"
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
	sleep 1
	azzera_testimone
	SCENA="caso4a-B: riattacco dichiarando «us», e si guarda se il Maiusc e’ rimasto giu’"
	batti c4ab us "$PRE U:61 U:7A"
	inf "— riattacco (dichiarata «us»): minuscole o MAIUSCOLE? —"
	leggi '' ''
	registra "{\"caso\":\"4a\",\"carico\":\"$(carico)\",\"quando\":\"$(date -Iseconds)\"}"

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
	local marca4b
	marca4b=$(stat -c %s "$LOG" 2>/dev/null || echo 0)
	(
		g=0
		while [ $g -lt 300 ]; do
			if tail -c "+$((marca4b + 1))" "$LOG" 2>/dev/null \
			   | grep -q 'POSIZIONE_TASTO codice evdev 42 .* premuto'; then
				printf '    --  ⭐ il Maiusc E GIU: adesso cambio la disposizione\n'
				bash "$TERRENO" disposizione de >/dev/null 2>&1
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
	local orfani
	orfani=$(cresciuto | grep -c 'ORFANI\|NON PARTE' 2>/dev/null | head -1)
	inf "righe che dichiarano un ORFANO in questo caso: ${orfani:-0}"
	if [ "${ril4b:-0}" -ge 1 ] 2>/dev/null; then
		ok "il rilascio e PARTITO sul dispositivo nuovo (conto ${ril4b})"
	elif [ "${orfani:-0}" -ge 1 ]; then
		ok "⭐ zero rilasci, ma l ORFANO E DICHIARATO: e la verita, non un silenzio"
		inf "   (il rilascio non poteva partire: meta-eis-client.c:638-645 lo scarta)"
	else
		ko "⛔ ROSSO: «rilascio al distacco: ${ril4b:-?}» e NESSUNA riga sugli"
		ko "   orfani — cioe uno ZERO che si legge come «non c era niente premuto»."
		ko "   ⚠ E su un compositore che non ci coprisse, il Maiusc resterebbe giu."
	fi
	registra "{\"caso\":\"4b\",\"ricambi\":[$r0,$r1],\"carico\":\"$(carico)\",\"quando\":\"$(date -Iseconds)\"}"
	bash "$TERRENO" disposizione it >/dev/null 2>&1
}

fai_caso5() {
	log "CASO 5 — la disposizione IGNOTA o MALFORMATA"
	inf "carico: $(carico)"
	att "«RCP.md» §4.5 vuole i due guasti DISTINTI:"
	att "   fuori forma          ⇒ ERRORE_PROTOCOLLO (0x0B)"
	att "   ben formata, ignota  ⇒ SESSIONE_NON_SERVIBILE (0x0E)"
	att "⛔ E «rcp.c:1970» risponde da un ELENCO FISSO di 20 nomi, non a XKB:"
	att "   ⇒ «hu» e «tr» esistono su questa macchina ma NON sono nell'elenco:"
	att "     l'atteso e' che vengano RIFIUTATI, ed e' un difetto, non la regola."
	att "   ⇒ «it(nonesiste)» e' ben formato e l'elenco guarda solo «it»:"
	att "     l'atteso e' che PASSI, e che la variante non la controlli nessuno."
	segna
	for d in "zz" "it(qwertz)" "it(nonesiste)" "de(neo)" "hu" "tr" "../../etc/passwd" "IT" "it," ""; do
		local et; et=$(printf '%s' "$d" | tr -c 'a-zA-Z0-9' '_')
		[ -z "$et" ] && et=vuota
		SCENA="caso5: ATTACCA con disposizione «$d»"
		printf '\n    \033[1m«%s»\033[0m\n' "$d"
		batti "c5-$et" "$d" "A:0.2"
		python3 -c "
import json
try:
    d=json.load(open('$LAVH/c5-$et-cliente.json'))
    print('        sessione: %s' % (d.get('sessione'),))
    print('        congedo : %s' % (d.get('congedo'),))
except Exception as e:
    print('        ⛔ nessun esito: %s' % e)
" 2>&1 | tail -4
	done
	inf "— che cosa ha scritto il server —"
	cresciuto | grep -iE 'congedo motivo|disposizione' | tail -20 | sed 's/^/        /'
	registra "{\"caso\":\"5\",\"carico\":\"$(carico)\",\"quando\":\"$(date -Iseconds)\"}"
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

case "$CASO" in
caso1)  fai_caso1 ;;
caso2)  fai_caso2 ;;
caso2s) fai_caso2s ;;
caso3)  fai_caso3 ;;
caso4)  fai_caso4 ;;
caso5)  fai_caso5 ;;
caso6)  fai_caso6 ;;
tutti)  fai_caso1; fai_caso2; fai_caso2s; fai_caso3; fai_caso4; fai_caso5; fai_caso6 ;;
*) ko "caso sconosciuto: $CASO"; exit 2 ;;
esac

log "Fatto — esiti in $ESITI"
inf "carico finale: $(carico)"
