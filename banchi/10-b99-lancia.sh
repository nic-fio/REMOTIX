#!/usr/bin/env bash
# ===========================================================================
# 10-b99-lancia — IL PREDITTORE, dall'inizio alla fine (agente 10-B10)
#
#   porta 8200 · albero /media/REMOTIX/src/10b10-src · lavoro /media/REMOTIX/tmp/10b10
#   unita' remotix-8200 · lucchetto GPU «10-b10» · utenti provamt1…11 CONDIVISI
#
# ⛔ L'ORDINE NON E' UNA COMODITA', E' IL METODO:
#
#     1. `--certifica`   il banco si e' visto dare ROSSO, o non e' un banco
#     2. `taratura`      il metro si tara PRIMA (`LEZIONI.md` §1.33)
#     3. `raccogli`      i dati che ci sono — giornali di 10-b92 + esiti di 10-b88
#     4. `indietro`      la verifica all'indietro ⛔ (che da sola NON basta)
#     5. `convalida`     e la prova che non e' un ricalco: si tara su k gradini
#                        e si predicono gli altri
#     6. `sigilla`       ⛔⛔ LE PREVISIONI, PRIMA DEL GIRO, con l'ancora sulla
#                        macchina di prova
#     7. `avanti`        il giro vero (fa girare `10-b92`, non lo riscrive)
#     8. `confronta`     ⛔ e si rifiuta di confrontare se l'ancora non c'e', se
#                        l'impronta non torna, o se la misura e' piu' vecchia
#                        dell'ancora
#
# ⛔⛔ IL PROTOCOLLO DELLE RISORSE CONDIVISE (preambolo del giro 2):
#     lucchetto PRIMA, palchi orfani verificati, `sgombra` alla fine col
#     lucchetto ANCORA IN MANO.  ⚠ Gran parte di questo incarico e' sui dati
#     gia' raccolti: il turno si prende **solo** per i giri in avanti, e corti.
# ===========================================================================
set -uo pipefail
QUI=$(cd "$(dirname "$0")/.." && pwd)

export MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
export PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-8200}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10b10-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10b10}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10b10-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10b10}
export UNITA=${UNITA:-remotix-$PORTA}
export IO_SONO=${IO_SONO:-10-b10}
export SHM_BASE=${SHM_BASE:-10b99}
export LUCCHETTO=${LUCCHETTO:-/media/REMOTIX/tmp/.lucchetto-gpu.d}
export FUORI=${FUORI:-/tmp/10-b99}

export QUI_B99="$QUI"
B99="python3 -u $QUI/banchi/10-b99-predittore.py"
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

PASSO=${1:-tutto}
GIORNALI=${GIORNALI:-$FUORI/giornali}
NOME=${NOME:-V1}
TELA=${TELA:-864x480}
QUANTI=${QUANTI:-11}
DURATA=${DURATA:-30}
SCENA_B92=${SCENA_B92:-satura}

case "$PASSO" in
prepara)
	# ⛔ Una volta sola: l'albero, il binario, l'unita'.  ⚠ Gli utenti
	#    `provamt*` sono CONDIVISI e li provvede chi arriva per primo:
	#    `bash banchi/10-b91-terreno-dieci.sh utenti`.
	log "l'albero e il binario"
	bash "$QUI/banchi/10-b91-terreno-dieci.sh" porta || exit 2
	log "l'unita' sulla $PORTA"
	UTENTE=provamt1 UID_B=1110 \
		bash "$QUI/banchi/10-b91-terreno-dieci.sh" accendi || exit 2
	exit 0 ;;

certifica)  exec $B99 --certifica ;;
pratico)    exec $B99 pratico ;;

dati)
	log "⛔ IL METRO SI TARA PRIMA"
	$B99 taratura || exit 1
	log "i dati che ci sono — i giornali di 10-b92"
	rm -f "$QUI/banchi/10-b99-misure.jsonl"
	$B99 raccogli --remoto "${REMOTO_B92:-/media/REMOTIX/tmp/10a6}" \
		--scena satura \
		--etichetta "10-b92 · salita a undici · 1080p · scena satura" || exit 2
	log "e quelli del CODIFICATORE NUDO — servono a farsi RIFIUTARE"
	$B99 raccogli --b88 || exit 2
	exit 0 ;;

indietro)   exec $B99 indietro --scena satura ;;
convalida)  exec $B99 convalida --scena satura ;;
moneta)     exec $B99 moneta --scena "${SCENA:-codificatore-nudo}" ;;
sigilla)    exec $B99 sigilla ${NOME:+--nome $NOME} ;;

avanti)
	# ⛔ 1 · IL LUCCHETTO PRIMA DEGLI UTENTI
	log "⛔ il lucchetto della GPU, e poi gli utenti condivisi"
	python3 - <<'PY' || exit 2
import importlib.util, os
os.environ.setdefault("LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-gpu.d")
s = importlib.util.spec_from_file_location(
    "luc", os.path.join(os.environ["QUI_B99"], "banchi/09-lucchetto.py"))
l = importlib.util.module_from_spec(s); s.loader.exec_module(l)
l.prendi(os.environ.get("IO_SONO", "10-b10"), secondi=300, attesa=7200)
PY
	# ⛔ 2 · I PALCHI ORFANI, col lucchetto in mano
	log "⛔ i palchi orfani, PRIMA di misurare"
	QUANTI=10 bash "$QUI/banchi/10-b91-terreno-dieci.sh" stato
	# ⛔ 3 · si molla e 10-b92 lo riprende da se' (non e' rientrante)
	python3 - <<'PY'
import importlib.util, os
os.environ.setdefault("LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-gpu.d")
s = importlib.util.spec_from_file_location(
    "luc", os.path.join(os.environ["QUI_B99"], "banchi/09-lucchetto.py"))
l = importlib.util.module_from_spec(s); s.loader.exec_module(l)
l.molla(os.environ.get("IO_SONO", "10-b10"))
PY
	# ⭐ 4 · IL GIRO — e NON parte se il sigillo non c'e'
	log "⭐ il giro «$NOME» — tela $TELA · scena $SCENA_B92 · $QUANTI sessioni"
	TELA=$TELA SCENA=$SCENA_B92 QUANTI=$QUANTI \
		$B99 avanti --nome "$NOME" --tela "$TELA" --quanti "$QUANTI" \
		--durata "$DURATA" --scena-b92 "$SCENA_B92"
	exit $? ;;

confronta)
	mkdir -p "$GIORNALI"
	log "porto i giornali del giro da $LAV"
	python3 - <<PY || exit 2
import importlib.util, os, sys
s = importlib.util.spec_from_file_location(
    "b99", "$QUI/banchi/10-b99-predittore.py")
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
sys.exit(0 if m.porta_giornali("$LAV", "$GIORNALI") else 2)
PY
	exec $B99 confronta --nome "$NOME" --giornali "$GIORNALI" ;;

sgombra)
	# ⛔ Col lucchetto ANCORA IN MANO, e poi si verifica invece di dichiarare.
	log "⛔ sgombro: palchi, unita', e la verifica"
	QUANTI=10 bash "$QUI/banchi/10-b91-terreno-dieci.sh" sgombra
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' systemctl stop $UNITA.service"
	ssh -o BatchMode=yes "$MACCHINA" \
		"echo '--- porte ---'; ss -uln | grep -c ':$PORTA ' ;
		 echo '--- remotix miei ---'; pgrep -af '$ALBERO' | wc -l ;
		 echo '--- netem lo ---'; tc qdisc show dev lo ;
		 echo '--- netem enp7s0 ---'; tc qdisc show dev enp7s0 | head -1"
	exit 0 ;;

tutto)
	$B99 --certifica || { ko "⛔ la certificazione non passa: NON MISURO"; exit 2; }
	"$0" dati || exit 2
	"$0" indietro
	"$0" convalida
	SCENA=codificatore-nudo "$0" moneta
	"$0" pratico
	exit 0 ;;

*)
	ko "passo sconosciuto: $PASSO"
	sed -n '/^# ====/,/^# ====/p' "$0" | head -30
	exit 2 ;;
esac
