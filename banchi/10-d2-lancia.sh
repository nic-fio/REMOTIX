#!/bin/bash
# ===========================================================================
# 10-d2-lancia — IL GIRO DEL BANCO DEL BUDGET, in ordine.
#
# ⛔ `certifica` e' il CANCELLO: se non passa, non si misura.  Un banco che non
#    sa dare rosso non sta provando niente, e il budget entrerebbe nel prodotto
#    senza che nessuno l'abbia messo alla prova (`LEZIONI.md` §1.29).
#
#   bash banchi/10-d2-lancia.sh certifica    ⭐ a secco: NIENTE macchina, NIENTE GPU
#   bash banchi/10-d2-lancia.sh prepara      utenti + sorgenti + compila
#   bash banchi/10-d2-lancia.sh dichiara     ⭐ che cosa il BINARIO sa fare
#   bash banchi/10-d2-lancia.sh fisico       ⭐ D2 e D6-fisico: ZERO GPU
#   bash banchi/10-d2-lancia.sh vero         ⛔ tutte e sei: VUOLE il lucchetto
#   bash banchi/10-d2-lancia.sh sgombra
#   bash banchi/10-d2-lancia.sh tutto        certifica → prepara → dichiara → fisico
#
# ⭐ PERCHE' `fisico` E' UN PASSO A SE'.  Col binario di oggi `--budget-mpixel-s`
#    non esiste: il server rifiuta l'opzione, stampa la sua guida e **muore
#    prima di aprire la porta**.  ⇒ D2 e il braccio fisico di D6 escono «non ho
#    misurato» senza aprire una sola sessione grafica, cioe' **senza toccare la
#    GPU** — e si possono girare mentre un altro agente misura.
# ⛔ `vero` no: apre sessioni grafiche vere e **vuole il lucchetto**.
# ===========================================================================
set -uo pipefail
QUI=$(cd "$(dirname "$0")/.." && pwd)
cd "$QUI" || exit 2

export PORTA=${PORTA:-8260}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10d2-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10d2}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10d2-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10d2}
export UNITA=${UNITA:-remotix-$PORTA}
export IO_SONO=${IO_SONO:-10-d2}
export SHM_BASE=${SHM_BASE:-10d2}
export FUORI=${FUORI:-/tmp/10-d2}
export LUCCHETTO=${LUCCHETTO:-/media/REMOTIX/tmp/.lucchetto-gpu.d}

log() { printf '\n\033[1m######## %s\033[0m\n' "$*"; }

PASSO=${1:-tutto}
shift || true

case "$PASSO" in
certifica)
	log "⭐ --certifica — a secco, senza macchina e senza il prodotto nuovo"
	exec python3 banchi/10-d2-budget.py --certifica "$@" ;;
prepara)
	log "1 · i tre utenti (⛔ la parola NON si rifa': §5.4)"
	bash banchi/10-d2-terreno.sh utenti || exit 2
	log "2 · i sorgenti e la compilazione"
	exec bash banchi/10-d2-terreno.sh porta ;;
dichiara)
	exec bash banchi/10-d2-terreno.sh dichiara ;;
fisico)
	log "⭐ D2 e D6-fisico — ZERO GPU: col binario di oggi il server non parte"
	python3 banchi/10-d2-budget.py misura --domanda 2 --senza-lucchetto "$@"
	rc=$?
	python3 banchi/10-d2-budget.py misura --domanda 6 --braccio fisico \
		--senza-lucchetto "$@"
	[ $? -gt $rc ] && rc=$?
	exit $rc ;;
vero)
	log "⛔ tutte e sei — e questo passo PRENDE IL LUCCHETTO"
	exec python3 banchi/10-d2-budget.py misura \
		--domanda 1 --domanda 2 --domanda 3 --domanda 4 --domanda 5 \
		--domanda 6 "$@" ;;
sgombra)
	bash banchi/10-d2-terreno.sh spegni
	exec bash banchi/10-d2-terreno.sh sgombra ;;
tutto)
	bash "$0" certifica || { echo "⛔ la certificazione non passa: NON misuro"; exit 2; }
	bash "$0" prepara || exit 2
	bash "$0" dichiara
	bash "$0" fisico
	exec bash "$0" sgombra ;;
*)
	sed -n '1,26p' "$0"
	exit 2 ;;
esac
