#!/usr/bin/env bash
# ===========================================================================
# 10-b93-terreno — il terreno del banco DELLA TABELLA PIENA (agente 10-A8)
#
#   porta 8030 · utenti `provadec4` (1103), `provadec5` (1104), `provadec6` (1105)
#   albero /media/REMOTIX/src/10a8-src · lavoro /media/REMOTIX/tmp/10a8
#   unita' remotix-8030 · lucchetto GPU `10-a8`
#
# ⛔ NON RISCRIVE `07-b64-terreno.sh`: gli passa il MIO ambiente e lo chiama,
#    come fa `09-b86-terreno.sh`.  L'unico passo tutto mio e' `porta`, e la
#    ragione e' la riga qui sotto.
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐⭐ IL TRUCCO CHE RENDE QUESTO BANCO POSSIBILE, E CHE VA DICHIARATO
# ═══════════════════════════════════════════════════════════════════════════
#
# Riempire una tabella da **16** vuol dire aprire sedici sessioni GRAFICHE vere
# su un i5-13500T: costoso, lento, e misurerebbe la MACCHINA invece del
# COMPORTAMENTO.  ⇒ Questo albero si compila con `MAX_ATTACCATE` **piccolo**
# (predefinito **2**, `MAX_ATT=n` per cambiarlo), e la tabella si riempie con
# due clienti.
#
# ⛔ **CHE COSA SI MISURA ALLORA**: il comportamento AL RIEMPIMENTO — quale
#    motivo esce sul filo, che cosa vede chi era gia' dentro, che cosa resta
#    appeso dopo un rifiuto.  ⛔ **NON** si misura il NUMERO: due non e' dieci e
#    non e' sedici, e nessuna riga di questo banco pretende il contrario.
#
# ⭐⭐ E DAL 25 AGOSTO 2026 NON SI RICOMPILA PIU' NIENTE: il tetto e'
#     **`--tetto-sessioni N`**, un'opzione all'avvio.  ⇒ L'albero sulla macchina
#     di prova e' quello del repository **byte per byte**, non ci sono gemelle
#     da riallineare a mano (R12.3), e la guardia guarda il **server acceso**
#     invece del testo da cui nascera'.
#
# ⛔ Il `sed` che stava qui e' stato tolto perche' non serviva piu', e la
#    ragione per cui era pericoloso resta scritta accanto al passo `porta`: un
#    `sed` su un modello che non c'e' esce **0 senza sostituire**, e il terreno
#    dichiara successo su un binario che non e' quello che si crede.
#
# ⚠ `MAX_FIGLI` (`figlio.c:91`) **non** si tocca, ed e' voluto: il commento
#   accanto dichiara che «segue» `MAX_ATTACCATE`, ma sono due `#define`
#   separati e nessuno li lega.  Lasciandolo a 16 il banco MISURA la
#   divergenza invece di nasconderla.
#
# Uso (dal portatile):
#     bash banchi/10-b93-terreno.sh utenti      # tutt'e tre
#     MAX_ATT=2 bash banchi/10-b93-terreno.sh porta
#     bash banchi/10-b93-terreno.sh accendi
#     bash banchi/10-b93-terreno.sh stato
#     bash banchi/10-b93-terreno.sh spegni
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-8030}
export UTENTE=${UTENTE:-provadec4}
export UID_B=${UID_B:-1103}
export PAROLA_UTENTE=${PAROLA_UTENTE:-dec-pieno-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10a8-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10a8}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10a8-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10a8}
export UNITA=${UNITA:-remotix-$PORTA}
MAX_ATT=${MAX_ATT:-2}

# I miei tre utenti, in ordine: (nome uid)
UTENTI="provadec4:1103 provadec5:1104 provadec6:1105"

QUI=$(cd "$(dirname "$0")/.." && pwd)
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

PASSO=${1:-stato}
case "$PASSO" in
utenti)
	# ⛔ Tre utenti, e servono tutti e tre: con `MAX_ATTACCATE=2` due riempiono
	#    la tabella e il TERZO e' il respinto.  ⚠ E il respinto dev'essere un
	#    utente DIVERSO, o riceverebbe `0x0F` (posto occupato) invece di `0x0E`
	#    (tabella piena) — sono due strade diverse di `posto_prendi()`.
	for u in $UTENTI; do
		n=${u%%:*}; i=${u##*:}
		log "utente $n (uid $i)"
		UTENTE=$n UID_B=$i bash "$QUI/banchi/07-b64-terreno.sh" utente || exit 2
	done
	exit 0 ;;

porta)
	log "1 · I sorgenti in $ALBERO — e il MIO MAX_ATTACCATE=$MAX_ATT"
	printf '    --  HEAD = %s\n' "$(cd "$QUI" && git rev-parse --short HEAD)"
	inf "md5 locale rcp.c:    $(md5sum "$QUI/src/rcp.c" | cut -d' ' -f1)"
	inf "md5 locale figlio.c: $(md5sum "$QUI/src/figlio.c" | cut -d' ' -f1)"
	inf "md5 locale main.c:   $(md5sum "$QUI/src/main.c" | cut -d' ' -f1)"
	for f in rcp.c rcp.h autenticazione.c; do
		if ! cmp -s "$QUI/src/$f" "$QUI/banchi/rcp/$f"; then
			ko "⛔ src/$f e banchi/rcp/$f DIVERGONO gia' nel repo (R12.3)"
			exit 2
		fi
	done
	ok "le due copie gemelle sono allineate nel repository"
	tar -C "$QUI" --exclude='src/remotix' --exclude='src/*.o' -cf - \
		src banchi/rcp \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/01-b4-validatore.py \
		banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py | \
		gzip | ssh -o BatchMode=yes "$MACCHINA" \
		"mkdir -p $ALBERO && tar -C $ALBERO -xzf -" || {
		ko "⛔ i sorgenti non sono arrivati"; exit 2; }
	ok "sorgenti in $ALBERO"

	log "2 · ⭐ NESSUN SED: il tetto si muove A CALDO con «--tetto-sessioni $MAX_ATT»"
	# ⛔⛔ E QUI C'ERA UN `sed` CHE RICOMPILAVA IL PRODOTTO — tolto il 25 agosto
	#     2026, ed e' la cura del difetto 5 dell'incarico F3.
	#
	#   La storia in tre righe, perche' e' istruttiva:
	#     1. erano QUATTRO `#define` a 16 copiati a mano, e questo copione ne
	#        sostituiva uno solo in `rcp.c`;
	#     2. la cura C3 li ha unificati in `RCP_TETTO_SESSIONI`, e il `sed`
	#        andava su un modello **che non c'era piu'**: usciva **0 senza
	#        sostituire**, il terreno dichiarava successo, il tetto restava 16 e
	#        il banco misurava «tabella piena» su una tabella da sedici.  ⇒ Ci
	#        fu messa una guardia che CONTAVA se aveva morso;
	#     3. ⭐ ma nel frattempo il prodotto ha imparato a farlo da se':
	#        **`--tetto-sessioni N`** lo muove **all'avvio**, e la riga d'avvio
	#        dichiara il valore in vigore accanto al predefinito.
	#
	# ⇒ ⭐ Un `sed` che ricompila non serve piu', e toglierlo toglie con se':
	#     una ricompilazione per giro · la gemella R12.3 da tenere allineata a
	#     mano · e soprattutto ⛔ **un albero che non e' piu' quello del
	#     repository**, cioe' un binario da spiegare invece che da leggere.
	# ⛔ E LA GUARDIA NON SPARISCE, CAMBIA POSTO: prima verificava che il `sed`
	#    avesse morso sui SORGENTI; adesso `accendi` verifica che il tetto sia
	#    in vigore nel SERVER ACCESO, leggendolo dalla riga d'avvio.  ⭐ E' una
	#    guardia migliore: guarda il prodotto che gira, non il testo da cui
	#    nascera' (`LEZIONI.md` §1.6).
	ssh -o BatchMode=yes "$MACCHINA" "
		grep -h '^#define RCP_TETTO_SESSIONI' $ALBERO/src/rcp.h
		cmp -s $ALBERO/src/rcp.h $ALBERO/banchi/rcp/rcp.h && echo 'gemelle rcp.h: uguali'
		cmp -s $ALBERO/src/rcp.c $ALBERO/banchi/rcp/rcp.c && echo 'gemelle rcp.c: uguali'
	" || { ko "⛔ non ho potuto rileggere le gemelle"; exit 2; }
	inf "⭐ l'albero e' quello del repository, byte per byte: il tetto lo muove"
	inf "   l'opzione all'accensione, non una ricompilazione"

	log "3 · Compilo dentro il contenitore"
	if ! ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
		  bash $DENTRO_ALB/src/costruisci.sh 2>&1 | tail -25'"; then
		ko "⛔ la compilazione e' fallita: NON accendo niente"
		exit 2
	fi
	ok "compilato"

	# ⛔⭐ E IL BINARIO CHE MISURO E' QUELLO CHE CREDO.  Tre gambe, e la terza
	#     e' l'unica che parli del BINARIO e non dei sorgenti:
	#       a. l'md5 dei due sorgenti gemelli e il `#define` letto da tutt'e due;
	#       b. l'md5 del binario e la sua eta' RISPETTO a rcp.c (un binario piu'
	#          vecchio del sorgente e' la forma D5, «stantio ma verde»);
	#       c. ⭐ il numero letto DAL BINARIO: la riga di §8.2 che il prodotto
	#          scrive quando la tabella e' piena porta `%d su %d`, e il secondo
	#          `%d` E' `MAX_ATTACCATE`.  ⚠ Quella riga la produce il BANCO, a
	#          giro fatto: qui si controlla solo che il formato sia nel binario,
	#          cioe' che il banco avra' da dove leggerlo.
	log "4 · ⛔ CHE COSA HO COSTRUITO"
	inf "⚠ i due «#define» qui sotto sono il PREDEFINITO, non il valore in"
	inf "  vigore: quello lo muove «--tetto-sessioni» e lo dichiara il server"
	inf "  acceso — si legge nel passo «accendi»"
	ssh -o BatchMode=yes "$MACCHINA" "
		echo \"#define src:     \$(grep -h '^#define RCP_TETTO_SESSIONI' $ALBERO/src/rcp.h)\"
		echo \"#define gemella: \$(grep -h '^#define RCP_TETTO_SESSIONI' $ALBERO/banchi/rcp/rcp.h)\"
		echo \"#define figli:   \$(grep -h '^#define MAX_FIGLI' $ALBERO/src/figlio.c)\"
		echo \"md5 rcp.c:       \$(md5sum $ALBERO/src/rcp.c | cut -d' ' -f1)\"
		echo \"md5 figlio.c:    \$(md5sum $ALBERO/src/figlio.c | cut -d' ' -f1)\"
		echo \"md5 binario:     \$(md5sum $ALBERO/src/remotix | cut -d' ' -f1)\"
		echo \"eta' binario:    \$(stat -c %Y $ALBERO/src/remotix) · rcp.c: \$(stat -c %Y $ALBERO/src/rcp.c)\"
		if [ \$(stat -c %Y $ALBERO/src/remotix) -ge \$(stat -c %Y $ALBERO/src/rcp.c) ]; then
			echo '⭐ il binario e\" piu\" giovane del sorgente'
		else
			echo '⛔ IL BINARIO E\" PIU\" VECCHIO DEL SORGENTE: forma D5'
		fi
		if grep -qa \"e' PIENO (%d su %d)\" $ALBERO/src/remotix; then
			echo \"⭐ la riga «PIENO (%d su %d)» c'e' nel binario: il banco avra' da dove leggere il numero\"
		else
			echo \"⛔ la riga «PIENO (%d su %d)» NON c'e' nel binario\"
		fi
	" || { ko "non ho potuto rileggere il binario"; exit 2; }
	exit 0 ;;

accendi)
	# ⛔⭐⭐ IL TETTO ENTRA QUI, E NON NEL COMPILATORE — 25 agosto 2026.
	#
	#     `--tetto-sessioni N` e' un'opzione del prodotto (`main.c`), sul modello
	#     delle altre: una strada sola, nessuna variabile d'ambiente, nessun
	#     interruttore di compilazione (`CODER.md` §2-bis).
	# ⚠ Si APPENDE a `OPZIONI_SERVER` invece di sostituirlo: chi chiama questo
	#   terreno passa gia' le opzioni delle cure, e mangiargliele sarebbe un
	#   guasto silenzioso — misurerebbe una scena diversa da quella chiesta.
	export OPZIONI_SERVER="${OPZIONI_SERVER:-} --tetto-sessioni $MAX_ATT"
	bash "$QUI/banchi/07-b64-terreno.sh" accendi || exit 2

	# ⛔⛔ E QUI STA LA GUARDIA CHE PRIMA GUARDAVA IL `sed`: il tetto in vigore
	#     si legge DAL SERVER ACCESO, non dai sorgenti.  Se non e' quello
	#     chiesto, il terreno si FERMA — perche' il banco misurerebbe «tabella
	#     piena» su una tabella di un'altra misura, e ⛔ **non darebbe rosso**:
	#     direbbe «non ho misurato», che e' il guasto travestito da terreno sano
	#     (la forma che questo file ha gia' pagato una volta).
	log "4-bis · ⛔ IL TETTO IN VIGORE, letto dal SERVER ACCESO"
	i=0
	VISTO=""
	while [ $i -lt 30 ]; do
		VISTO=$(ssh -o BatchMode=yes "$MACCHINA" \
			"grep -ao 'tetto AMMINISTRATIVO delle sessioni: \*\*[0-9]*\*\*' \
			 $LAV/registro.log 2>/dev/null | tail -1 | grep -o '[0-9]*' || true")
		[ -n "$VISTO" ] && break
		i=$((i+1)); sleep 0.5
	done
	if [ -z "$VISTO" ]; then
		ko "⛔ il server non ha dichiarato nessun tetto: NON so su che tabella"
		ko "   sto per misurare, e un numero che non so non e' un numero"
		exit 2
	fi
	if [ "$VISTO" != "$MAX_ATT" ]; then
		ko "⛔ ho chiesto --tetto-sessioni $MAX_ATT e il server dichiara $VISTO"
		exit 2
	fi
	ok "⭐ il server dichiara il tetto **$VISTO**, ed e' quello che ho chiesto"
	exit 0 ;;

*)
	# ⛔ Tutto il resto e' `07-b64-terreno.sh`, con il MIO ambiente esportato.
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
esac
