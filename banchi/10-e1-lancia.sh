#!/usr/bin/env bash
# ===========================================================================
# 10-e1-lancia — ⛔⛔ LE QUATTRO CURE **INSIEME**, sull'albero CUCITO.
#
#   porta 8310 · albero /media/REMOTIX/src/10e1-src · lavoro /media/REMOTIX/tmp/10e1
#   unita' remotix-8310 · lucchetto GPU `10-e1`
#
# ⛔ Il lucchetto NON si prende qui: lo tiene `banchi/10-e1-lucchetto.sh`, che
#    corre la corsa **sulla macchina** (§7.3).  Qui si VERIFICA che sia mio
#    prima di ogni tappa, e se non lo e' ci si ferma.
#
# ⛔⛔ E OGNI TAPPA VUOLE UN BINARIO DIVERSO, che e' la ragione per cui questo
#      copione esiste invece di quattro comandi a mano:
#
#        C3 · tetto **2**            (`10-c3-terreno.sh porta`, TETTO=2)
#        C2 · albero **nudo**        (`10-c2-terreno.sh porta`) + LimitCORE
#        C4 · lo stesso nudo         (nessuna ricostruzione)
#        C1 · nudo + **guardiano finto** (`10-c1-terreno.sh porta`)
#
#      ⇒ L'ordine non e' un gusto: e' quello che costa **due** ricostruzioni
#        invece di quattro, e ogni ricostruzione dentro il lucchetto e' tempo
#        tolto agli altri agenti.
#
# ⛔ E LE PAROLE D'ORDINE NON SI RIFANNO (l'incarico lo vieta): il passo
#    `utenti` di ogni terreno oggi **non tocca** la parola di un utente che
#    esiste gia' (`RIFAI_PAROLA=1` per forzare), e serve solo a riposare
#    `linger`, i gruppi e il file `$LAV/parola`.
#
# Uso:
#     bash banchi/10-e1-lancia.sh c3|c2|c4|c1|tutto
# ===========================================================================
set -uo pipefail
QUI=$(cd "$(dirname "$0")/.." && pwd)

export MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
export PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-8310}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10e1-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10e1}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10e1-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10e1}
export UNITA=${UNITA:-remotix-$PORTA}
export LUCCHETTO=${LUCCHETTO:-/media/REMOTIX/tmp/.lucchetto-gpu.d}
export IO_SONO=${IO_SONO:-10-e1}
FUORI=${FUORI:-/tmp/10-e1}
mkdir -p "$FUORI"

log() { printf '\n\033[1m######## %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

mio() {
	# ⛔ Il lucchetto dev'essere MIO, non «libero»: libero vuol dire che
	#    qualcuno puo' prenderlo mentre misuro.
	local chi
	chi=$(LUCCHETTO=$LUCCHETTO python3 "$QUI/banchi/09-lucchetto.py" stato 2>&1 | tr -d '\n')
	case "$chi" in
	*"«$IO_SONO»"*) inf "lucchetto: $chi"; return 0 ;;
	*) ko "⛔ il lucchetto NON e' mio: $chi — mi fermo"; return 1 ;;
	esac
}

# ⛔⛔ IL TERRENO DELLA FASE — `10-b0-terreno.sh`, PRIMA DI OGNI MISURA.
#
#     ⚠ E il suo predicato T5.2 confronta **byte per byte** i sorgenti sulla
#       macchina con quelli di `REPO`.  ⛔ Due tappe di questo giro compilano un
#       albero MODIFICATO — C3 col tetto a 2, C1 col guardiano finto — e li'
#       T5.2 **deve** fallire se gli si da' il repository nudo.
#     ⇒ Non si spegne il controllo: gli si da' il termine di paragone giusto,
#       una copia su cui gira la STESSA modifica.  (E' la stessa scelta che
#       `10-c1-terreno.sh` fa gia' con `STAGING`.)
terreno_fase() {
	local repo=$1 utente=$2 palco=${3:-0}
	local altre
	altre=$(ssh -o BatchMode=yes "$MACCHINA" \
	        "ss -uln | grep -oE ':[78][0-9]{3} ' | tr -d ': ' | sort -u" 2>/dev/null \
	        | grep -v "^$PORTA\$" | tr '\n' ' ')
	inf "porte di altri incarichi, dichiarate e non toccate: ${altre:-nessuna}"
	CHI=$IO_SONO PORTA=$PORTA UTENTE=$utente ALBERO=$ALBERO LAV=$LAV \
		REPO="$repo" LUCCHETTO=$LUCCHETTO LUCCHETTO_MIO=1 \
		PORTE_AMMESSE="$altre" PALCO_AMMESSO="$palco" \
		bash "$QUI/banchi/10-b0-terreno.sh" > "$FUORI/terreno.log" 2>&1
	local rc=$?
	grep -E "NO |IL TERRENO" "$FUORI/terreno.log" | sed 's/^/    | /' | tail -20
	case $rc in
	0) ok "⭐ il terreno della fase regge" ;;
	2) ko "⚠ 10-b0-terreno esce 2: NON HO POTUTO VERIFICARE il terreno" ;;
	*) ko "⛔ il terreno NON regge (uscita $rc)" ;;
	esac
	return $rc
}

# ⭐ La copia di raffronto per una tappa che compila un albero modificato.
raffronto() {   # $1 = cartella  $2… = sed da applicare a src/rcp.h e gemella
	local dove=$1; shift
	rm -rf "$dove"; mkdir -p "$dove/src" "$dove/banchi"
	cp -a "$QUI/src/." "$dove/src/"
	rm -f "$dove/src/remotix" "$dove"/src/*.o
	cp -a "$QUI/banchi/rcp" "$dove/banchi/rcp"
	for e in "$@"; do
		sed -i "$e" "$dove/src/rcp.h" "$dove/banchi/rcp/rcp.h"
	done
}

PASSO=${1:-tutto}

# ─────────────────────────────────────────────────────────────────────────
# C3 · l'undicesimo riceve un no — albero col tetto a 2
# ─────────────────────────────────────────────────────────────────────────
tappa_c3() {
	log "C3 · L'UNDICESIMO — tetto 2, utenti provadec4/5/6"
	mio || return 2
	TETTO=2 GUASTO=nessuno bash "$QUI/banchi/10-c3-terreno.sh" porta \
		> "$FUORI/c3-porta.log" 2>&1 || { ko "compilazione fallita"; return 2; }
	ok "compilato col tetto 2 ($(grep -c . "$FUORI/c3-porta.log") righe di registro)"
	UTENTE=provadec4 UID_B=1103 PAROLA_UTENTE=dec-pieno-2026 \
		bash "$QUI/banchi/10-c3-terreno.sh" utenti > "$FUORI/c3-utenti.log" 2>&1 \
		|| { ko "gli utenti non si sono provvisti"; return 2; }
	grep -q "parola NON toccata" "$FUORI/c3-utenti.log" \
		&& ok "⭐ nessuna parola d'ordine rifatta" \
		|| inf "⚠ guarda $FUORI/c3-utenti.log: qualcuno era da creare"
	PAROLA_UTENTE=dec-pieno-2026 bash "$QUI/banchi/10-c3-terreno.sh" accendi \
		|| { ko "il server non e' partito"; return 2; }
	# ⛔⛔ `provadec4/5/6` sono CONDIVISI e i due banchi che li usano dichiarano
	#     parole DIVERSE: si scopre quale sia quella vera **senza rifarla**.
	VERA=$(bash "$QUI/banchi/10-e1-parola.sh" provadec4 dec-pieno-2026 mt-dieci-2026) \
		|| { ko "⛔ nessuna parola buona per provadec4: NON misuro"; return 2; }
	inf "⭐ la parola vera dei provadec4/5/6 e' «$VERA»"
	raffronto /tmp/10-e1-repo-c3 \
		's/^#define RCP_TETTO_SESSIONI 16$/#define RCP_TETTO_SESSIONI 2/'
	terreno_fase /tmp/10-e1-repo-c3 provadec4 || return 2
	PAROLA_UTENTE="$VERA" TETTO=2 python3 -u "$QUI/banchi/10-c3-palchi.py" \
		--tetto 2 --guasto nessuno --jsonl "$FUORI/c3-esiti.jsonl"
	local rc=$?
	# ⭐ Il registro di questa tappa serve anche all'incrocio n. 3.
	ssh -o BatchMode=yes "$MACCHINA" \
	  "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' cp -a $LAV/registro.log $LAV/registro-c3.log" \
	  >/dev/null 2>&1
	bash "$QUI/banchi/10-c3-terreno.sh" spegni >/dev/null 2>&1
	return $rc
}

# ─────────────────────────────────────────────────────────────────────────
# C2 · il ripiego sulla memoria — albero nudo, LimitCORE=infinity
# ─────────────────────────────────────────────────────────────────────────
tappa_c2() {
	log "C2 · IL RIPIEGO SULLA MEMORIA — albero nudo, utente provadec1"
	mio || return 2
	UTENTE=provadec1 UID_B=1100 PAROLA_UTENTE=b2-browser-2026 \
		bash "$QUI/banchi/10-c2-terreno.sh" porta > "$FUORI/c2-porta.log" 2>&1 \
		|| { ko "compilazione fallita"; return 2; }
	ok "albero nudo compilato"
	UTENTE=provadec1 UID_B=1100 PAROLA_UTENTE=b2-browser-2026 \
		bash "$QUI/banchi/10-c2-terreno.sh" utenti > "$FUORI/c2-utenti.log" 2>&1 \
		|| { ko "gli utenti non si sono provvisti"; return 2; }
	# ⛔ I due `sysctl` sono DI TUTTA LA MACCHINA: si rimettono in ogni caso.
	UTENTE=provadec1 bash "$QUI/banchi/10-c2-terreno.sh" core-prepara || return 2
	UTENTE=provadec1 PAROLA_UTENTE=b2-browser-2026 \
		bash "$QUI/banchi/10-c2-terreno.sh" accendi || {
		ko "il server non e' partito"; bash "$QUI/banchi/10-c2-terreno.sh" core-rimetti
		return 2; }
	terreno_fase "$QUI" provadec1 || { bash "$QUI/banchi/10-c2-terreno.sh" core-rimetti; return 2; }
	UTENTE=provadec1 PAROLA_UTENTE=b2-browser-2026 FUORI="$FUORI" \
		python3 -u "$QUI/banchi/10-c2-ripiego.py" --giri 3 \
		--tele 1268x714,1280x714,854x480
	local rc=$?
	ssh -o BatchMode=yes "$MACCHINA" \
	  "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' cp -a $LAV/registro.log $LAV/registro-c2.log" \
	  >/dev/null 2>&1
	bash "$QUI/banchi/10-c2-terreno.sh" core-rimetti
	return $rc
}

# ─────────────────────────────────────────────────────────────────────────
# C4 · il registro dice di chi e' — stesso albero nudo, quattro utenti
# ─────────────────────────────────────────────────────────────────────────
tappa_c4() {
	log "C4 · IL REGISTRO — tre sessioni vere di utenti diversi (provadec4/5/6)"
	mio || return 2
	# ⛔ L'albero porta ancora l'innesto di C1 (o il tetto a 2): si rifa' NUDO,
	#    perche' qui si misura il registro del PRODOTTO, non quello del banco.
	QUANTI=3 bash "$QUI/banchi/10-b96-terreno.sh" porta \
		> "$FUORI/c4-porta.log" 2>&1 || { ko "compilazione fallita"; return 2; }
	ok "albero nudo compilato"
	# ⚠ `utenti` finisce con `exec "$0" stato`, che puo' uscire diverso da zero
	#   per ragioni che non riguardano gli utenti: si guarda, non si abortisce.
	QUANTI=3 PAROLA_UTENTE=dec-pieno-2026 bash "$QUI/banchi/10-b96-terreno.sh" utenti \
		> "$FUORI/c4-utenti.log" 2>&1
	inf "utenti con la parola NON toccata: $(grep -cE 'parola NON toccata' "$FUORI/c4-utenti.log") su 3"
	PAROLA_UTENTE=dec-pieno-2026 bash "$QUI/banchi/10-b96-terreno.sh" accendi \
		|| { ko "il server non e' partito"; return 2; }
	# ⛔ `[M]` 25 agosto 2026: la parola vera dei tre condivisi e' quella di C3
	#    (`dec-pieno-2026`), non quella dichiarata da `10-b96-terreno.sh` — e'
	#    C3 l'ultimo ad averla scritta prima che il terreno smettesse di
	#    riscriverla.  ⇒ Si prova per prima quella, cosi' il tentativo speso e' zero.
	VERA=$(bash "$QUI/banchi/10-e1-parola.sh" provadec4 dec-pieno-2026 mt-dieci-2026) \
		|| { ko "⛔ nessuna parola buona per provadec4: NON misuro"; return 2; }
	inf "⭐ la parola vera e' «$VERA»"
	terreno_fase "$QUI" provadec4 || return 2
	# ⛔ TRE sessioni, non quattro: `provamt1` ha un'altra parola e non si rifa'.
	#    Il riquadro di `10-e1-c4-cieca.py` porta la misura che lo dimostra.
	PAROLA_UTENTE="$VERA" IO_SONO=$IO_SONO FUORI="$FUORI" \
		python3 -u "$QUI/banchi/10-e1-c4-cieca.py" --lucchetto-esterno
	local rc=$?
	ssh -o BatchMode=yes "$MACCHINA" \
	  "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' cp -a $LAV/registro.log $LAV/registro-c4.log" \
	  >/dev/null 2>&1
	bash "$QUI/banchi/10-b96-terreno.sh" sgombra >/dev/null 2>&1
	bash "$QUI/banchi/10-b96-terreno.sh" spegni  >/dev/null 2>&1
	return $rc
}

# ─────────────────────────────────────────────────────────────────────────
# C1 · il guardiano — albero nudo + guardiano finto innestato
# ─────────────────────────────────────────────────────────────────────────
tappa_c1() {
	log "C1 · IL GUARDIANO — albero nudo + guardiano finto, utenti provaf1…7"
	mio || return 2
	BINARIO=remotix-cura-inn STAGING=/tmp/10-e1-repo \
		UTENTE=provaf1 UID_B=1160 PAROLA_UTENTE=f-guardiano-2026 \
		bash "$QUI/banchi/10-c1-terreno.sh" porta > "$FUORI/c1-porta.log" 2>&1 \
		|| { ko "compilazione fallita — vedi $FUORI/c1-porta.log"; return 2; }
	grep -E "la CURA|marca del guardiano|md5 binario" "$FUORI/c1-porta.log" \
		| sed 's/^/    --  /'
	QUANTI=7 UTENTE=provaf1 UID_B=1160 PAROLA_UTENTE=f-guardiano-2026 \
		bash "$QUI/banchi/10-c1-terreno.sh" utenti > "$FUORI/c1-utenti.log" 2>&1 \
		|| { ko "gli utenti non si sono provvisti"; return 2; }
	QUANTI=7 SHM_BASE=10e1 STAGING=/tmp/10-e1-repo FUORI="$FUORI" \
		BINARIO=remotix-cura-inn BINARIO_ALBERO=remotix-cura-inn \
		python3 -u "$QUI/banchi/10-e1-c1-verde.py" "${2:-tutto}"
	local rc=$?
	ssh -o BatchMode=yes "$MACCHINA" \
	  "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' cp -a $LAV/registro.log $LAV/registro-c1.log" \
	  >/dev/null 2>&1
	return $rc
}

# ─────────────────────────────────────────────────────────────────────────
# ⭐ C4 su un registro GIA' SCRITTO — `10-b96-registro.py --analizza`
#
# ⛔ Non sostituisce il giro vero di C4 (la **prova cieca** vuole che si spenga
#    una scena e si chieda al registro chi si e' fermato, e quello vuole la
#    macchina).  ⚠ Ma la frazione attribuibile, le famiglie e gli intrecci si
#    leggono da qualunque registro vero — e quello di C1 ne ha **sette** di
#    sessioni invece di quattro.
# ─────────────────────────────────────────────────────────────────────────
tappa_analizza() {  # $1 = registro sulla macchina
	log "C4 · LA FRAZIONE ATTRIBUIBILE su «$1»"
	IO_SONO=$IO_SONO FUORI="$FUORI" python3 -u "$QUI/banchi/10-b96-registro.py" \
		--analizza "$1" --mega 24
	log "GLI INCROCI su «$1»"
	python3 -u "$QUI/banchi/10-e1-incroci.py" --da-registro "$1" \
		--utente "${2:-provaf1}"
}

case "$PASSO" in
analizza) tappa_analizza "${2:?serve il registro}" "${3:-provaf1}"; exit $? ;;
c3) tappa_c3; exit $? ;;
c2) tappa_c2; exit $? ;;
c4) tappa_c4; exit $? ;;
c1) tappa_c1 "$@"; exit $? ;;
tutto)
	tappa_c3; R3=$?
	tappa_c2; R2=$?
	tappa_c4; R4=$?
	tappa_c1; R1=$?
	log "GLI ESITI"
	inf "C3 $R3 · C2 $R2 · C4 $R4 · C1 $R1  (0 verde · 1 rosso · 3 non ho misurato)"
	exit 0 ;;
*) ko "passo sconosciuto: $PASSO"; exit 2 ;;
esac
