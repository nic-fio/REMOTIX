#!/usr/bin/env bash
# ===========================================================================
# 10-b93-lancia — il giro del banco DELLA TABELLA PIENA (agente 10-A8)
#
#   porta 8030 · utenti provadec4/5/6 · albero /media/REMOTIX/src/10a8-src
#   lavoro /media/REMOTIX/tmp/10a8 · unita' remotix-8030 · lucchetto GPU 10-a8
#
# ⛔ Prima di questo, una volta sola:
#       bash banchi/10-b93-terreno.sh utenti
#       MAX_ATT=2 bash banchi/10-b93-terreno.sh porta
#       bash banchi/10-b93-terreno.sh accendi
#
# ⛔ E il giro NON parte se `--certifica` non passa: un banco che non si e' visto
#    dare rosso non e' un banco (`LEZIONI.md` §1.29).
# ===========================================================================
set -uo pipefail
QUI=$(cd "$(dirname "$0")/.." && pwd)

export MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
export PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
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
export FUORI=${FUORI:-/tmp/10-b93}
export LUCCHETTO=${LUCCHETTO:-/media/REMOTIX/tmp/.lucchetto-gpu.d}

mkdir -p "$FUORI"

printf '\n\033[1m== ⛔ PRIMA LA CERTIFICAZIONE: i guasti innestati devono dare rosso\033[0m\n'
if ! python3 -u "$QUI/banchi/10-b93-pieno.py" --certifica; then
	printf '    \033[1;31mNO\033[0m  ⛔ la certificazione non passa: NON MISURO\n'
	exit 2
fi

printf '\n\033[1m== ⭐ IL GIRO VERO\033[0m\n'
exec python3 -u "$QUI/banchi/10-b93-pieno.py" \
	--fuori "$FUORI/esiti.json" "$@"
