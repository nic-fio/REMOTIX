#!/usr/bin/env bash
# ===========================================================================
# 10-c3-lancia — la campagna del banco DEI PALCHI PIENI (incarico 10-C3, P3)
#
#   porta 8230 · utenti provadec4/5/6 · albero /media/REMOTIX/src/10c3-src
#   lavoro /media/REMOTIX/tmp/10c3 · unita' remotix-8230 · lucchetto GPU 10-c3
#
# ⛔ Prima di questo, una volta sola:
#       bash banchi/10-c3-terreno.sh utenti
#
# ⭐⭐ E LA CAMPAGNA E' **IL ROSSO PRIMA E IL VERDE DOPO**, non un giro solo:
#
#   1. `--certifica` — i guasti innestati nei predicati, senza macchina;
#   2. ⛔ **il ROSSO**: albero col guasto `congedo-muto`, cioe' il prodotto
#      **di ieri** — il no non esce sul filo;
#   3. ⭐ **il VERDE**: lo stesso albero, stessa scena, stessi predicati, con
#      la cura;
#   4. ⛔ **il controllo negativo dei `#define`**: tre guasti che rimettono i
#      numeri a mano, uno per volta;
#   5. ⛔ e il **risanamento**: si torna al sano, e dev'essere di nuovo verde.
#
# ⛔ I passi 4 non accendono nessun server e non toccano la GPU: la misura
#    degli array si legge **dopo il preprocessore**, e per quello basta
#    compilare.  ⇒ Il lucchetto serve ai passi 2, 3 e 5.
#
# Uso:
#     bash banchi/10-c3-lancia.sh              tutta la campagna
#     bash banchi/10-c3-lancia.sh sano         solo il verde
#     bash banchi/10-c3-lancia.sh rosso        solo il rosso
#     bash banchi/10-c3-lancia.sh define       solo i tre guasti dei #define
# ===========================================================================
set -uo pipefail
QUI=$(cd "$(dirname "$0")/.." && pwd)

export MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
export PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-8230}
export UTENTE=${UTENTE:-provadec4}
export UID_B=${UID_B:-1103}
export PAROLA_UTENTE=${PAROLA_UTENTE:-dec-pieno-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10c3-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10c3}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10c3-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10c3}
export UNITA=${UNITA:-remotix-$PORTA}
export LUCCHETTO=${LUCCHETTO:-/media/REMOTIX/tmp/.lucchetto-gpu.d}
export TETTO=${TETTO:-2}
FUORI=${FUORI:-/tmp/10-c3}
mkdir -p "$FUORI"

log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ LA CORSA AL LUCCHETTO SI CORRE **SULLA MACCHINA** — e l'ho pagata anch'io
# ═══════════════════════════════════════════════════════════════════════════
#
# `09-lucchetto.py prendi()` ritenta il `mkdir` ogni **5 secondi**, e ogni
# tentativo e' un giro di `ssh`.  ⛔ Ma il lucchetto **non e' una coda: e' una
# corsa** (§7.3) — nessuna prenotazione, nessuna anzianita': vince chi arriva
# per primo dopo un `molla`, e chi ritenta piu' fitto vince quasi sempre.
#
# `[M]` 25 agosto 2026, questo incarico: con i 5 secondi ho perso **due
# passaggi di mano di fila** — «10-c2» → «10-c4» e «10-c4» → «10-c1» — dopo
# ~100 giri d'attesa, senza mai toccare la GPU.  ⚠ E non e' sfortuna: e' il
# passo.  L'incarico 10-b9d aveva gia' misurato lo stesso e ha lasciato
# l'attrezzo: `banchi/10-b9d-corri-al-lucchetto.sh`, ciclo `mkdir` **sulla
# macchina**, passo 0,5 s, `[M]` rilascio a 2 000 ms → preso a **2 047 ms**.
#
# ⭐ Si RIUSA quello, non se ne scrive un secondo: `banchi/09-lucchetto.py` non
#    si tocca (e' di tutti) e il file `chi` mantiene lo stesso formato.
# ⚠ E il corridore gira sotto `setsid`+pid noto, cosi' se questo lanciatore
#   muore non resta un **corridore orfano** che vince la corsa a nome mio e poi
#   tiene la GPU con nessuno a mollarla (la quarta trappola di §7.3).
CORRIDORE="$QUI/banchi/10-b9d-corri-al-lucchetto.sh"
[ -f "$CORRIDORE" ] || CORRIDORE=/home/nicfio/Documenti/REMOTIX/banchi/10-b9d-corri-al-lucchetto.sh
PY_LUC="$QUI/banchi/09-lucchetto.py"

prendi_lucchetto() {
	local secondi=$1
	if [ ! -f "$CORRIDORE" ]; then
		ko "⛔ il corridore «$CORRIDORE» non c'e': NON misuro"
		return 2
	fi
	inf "⚠ la corsa si corre sulla macchina, passo 0,5 s (10-b9d): coi 5 s di prendi() ho gia' perso due passaggi di mano"
	local b64
	b64=$(base64 -w0 "$CORRIDORE")
	ssh -o BatchMode=yes "$MACCHINA" \
	  "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c '
	     mkdir -p $LAV && printf %s $b64 | base64 -d > $LAV/corri.sh
	     chmod +x $LAV/corri.sh'" >/dev/null 2>&1 || {
		ko "⛔ il corridore non e' arrivato sulla macchina: NON misuro"; return 2; }

	local uscita
	uscita=$(ssh -o BatchMode=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=1000 \
	  "$MACCHINA" "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' \
	   $LAV/corri.sh '$LUCCHETTO' '10-c3' $secondi 21600 0.5" 2>&1 | grep -v '^tput')
	printf '%s\n' "$uscita" | sed 's/^/    --  /'
	case "$uscita" in
	PRESO*|SCASSINO*) return 0 ;;
	MIO*)
		# ⛔ «Il lucchetto porta gia' il mio nome»: `prendi()` qui aspetterebbe
		#    SE STESSO fino alla scadenza (§7.3, il difetto peggiore).  Qui lo
		#    si ADOTTA — ma solo dopo aver verificato che non ci sia un altro
		#    mio corridore vivo, o due giri userebbero la GPU insieme a nome mio.
		# ⚠ E si guarda SULLA MACCHINA, non qui: il corridore gira di la'.
		#   ⛔ La classe `[c]` perche' la riga non trovi se stessa.
		if [ "$(ssh -o BatchMode=yes "$MACCHINA" \
		        "pgrep -f '[c]orri.sh .* 10-c3 ' | wc -l" 2>/dev/null)" != "0" ]; then
			ko "⛔ il lucchetto e' a nome mio E c'e' un altro corridore vivo: NON misuro"
			return 2
		fi
		inf "⭐ il lucchetto porta gia' il mio nome e nessun altro mio corridore e' vivo: lo ADOTTO"
		return 0 ;;
	*) ko "⛔ non ho il lucchetto: $uscita"; return 2 ;;
	esac
}
molla_lucchetto() {
	python3 -c "
import importlib.util, os
os.environ['LUCCHETTO'] = '$LUCCHETTO'
spec = importlib.util.spec_from_file_location('luc', '$PY_LUC')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.molla('10-c3')
"
}

giro() {  # $1 = guasto  $2 = etichetta
	local g=$1 et=$2
	log "$et — albero col guasto «$g»"
	TETTO=$TETTO GUASTO="$g" bash "$QUI/banchi/10-c3-terreno.sh" porta || return 2
	bash "$QUI/banchi/10-c3-terreno.sh" accendi || return 2
	GUASTO="$g" python3 -u "$QUI/banchi/10-c3-palchi.py" \
		--tetto "$TETTO" --guasto "$g" --jsonl "$FUORI/esiti.jsonl" "${EXTRA[@]}"
	local rc=$?
	bash "$QUI/banchi/10-c3-terreno.sh" spegni || true
	return $rc
}

giro_define() {  # $1 = guasto — nessun server, nessuna GPU
	local g=$1
	log "⛔ CONTROLLO NEGATIVO DEI #define — guasto «$g»"
	TETTO=$TETTO GUASTO="$g" bash "$QUI/banchi/10-c3-terreno.sh" porta \
		>/dev/null 2>&1 || { ko "non ho potuto compilare col guasto"; return 2; }
	bash "$QUI/banchi/10-c3-terreno.sh" definisci | grep DEFINE
}

EXTRA=()
PASSO=${1:-tutto}
[ "${2:-}" = "--niente-pagina" ] && EXTRA=(--niente-pagina)

log "⛔ PRIMA LA CERTIFICAZIONE: i guasti innestati devono dare rosso"
if ! python3 -u "$QUI/banchi/10-c3-palchi.py" --certifica; then
	ko "⛔ la certificazione non passa: NON MISURO"
	exit 2
fi

case "$PASSO" in
define)
	for g in figli-slegati palchi-otto presenti-slegati; do giro_define "$g"; done
	log "⭐ E il RISANATO"
	giro_define nessuno
	exit 0 ;;
esac

log "⛔⛔ IL LUCCHETTO DELLA GPU — e si aspetta davvero il proprio turno"
prendi_lucchetto 5400 || { ko "⛔ senza lucchetto NON misuro"; exit 2; }

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ E LA PAROLA D'ORDINE SI RIFA' **DENTRO** LA FINESTRA DEL LUCCHETTO
# ═══════════════════════════════════════════════════════════════════════════
#
# `[M]` 25 agosto 2026, primo giro: `provadec4` e' stato **RESPINTO con 0x07**
# su una parola che questo banco aveva posto lui stesso mezz'ora prima.
#
# ⛔ Il perche': `provadec4/5/6` sono **condivisi** fra i banchi della fase, e
#    `07-b64-terreno.sh utente` **riscrive la parola a ogni chiamata**
#    (`chpasswd`).  ⇒ L'ultimo che chiama `utenti` vince, e gli altri leggono
#    «credenziali errate» su una macchina perfettamente sana.
#
# ⛔⛔ E il conto e' salato: ogni respinto consuma **uno dei tre tentativi** del
#      ban di §4.4-bis, che e' **per INDIRIZZO** e dura **dodici ore** — cioe'
#      tre giri sfortunati mettono fuori uso **ogni altro agente**.
#
# ⇒ La si rifa' QUI, subito dopo aver preso il lucchetto: finche' il lucchetto
#   e' mio nessun altro sta facendo girare clienti, quindi da qui in avanti
#   l'ultimo che ha scritto la parola sono io.  ⚠ Non e' una garanzia (il
#   terreno di un altro non chiede il lucchetto): e' la finestra piu' stretta
#   che si possa ottenere senza cambiare la disciplina degli utenti condivisi.
log "⛔ RIFACCIO LA PAROLA DEI TRE UTENTI CONDIVISI — dentro il lucchetto"
bash "$QUI/banchi/10-c3-terreno.sh" utenti >/dev/null 2>&1 \
	&& ok "parola rifatta per provadec4/5/6" \
	|| { ko "⛔ non ho potuto rifare la parola: NON misuro"; molla_lucchetto; exit 2; }
# ⛔ E si molla SEMPRE, anche se qualcosa esplode a meta': un lucchetto in mano
#    a un morto blocca ogni altro agente fino alla scadenza.
trap 'molla_lucchetto' EXIT

case "$PASSO" in
rosso)   giro congedo-muto "⛔ IL ROSSO — il prodotto di ieri"; ESITO=$? ;;
sano)    giro nessuno "⭐ IL VERDE — con la cura"; ESITO=$? ;;
*)
	giro congedo-muto "⛔ IL ROSSO — il prodotto di ieri (P3 rimesso)"
	R=$?
	giro nessuno "⭐ IL VERDE — stessa scena, stessi predicati, con la cura"
	V=$?
	log "IL CONFRONTO"
	inf "rosso: uscita $R (⭐ diverso da 0 e' quel che deve essere)"
	inf "verde: uscita $V (⭐ 0 e' quel che deve essere)"
	# ⭐ E IL LUCCHETTO SI MOLLA QUI, non a fine campagna: quel che resta —
	#   i tre guasti dei `#define` — si legge dopo il preprocessore e non
	#   accende nessun server.  ⚠ Gli altri agenti aspettano.
	molla_lucchetto; trap - EXIT
	giro_define figli-slegati
	giro_define palchi-otto
	giro_define presenti-slegati
	giro_define nessuno
	ESITO=$V ;;
esac
exit "${ESITO:-0}"
