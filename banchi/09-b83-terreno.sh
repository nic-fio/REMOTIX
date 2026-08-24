#!/usr/bin/env bash
#
# ===========================================================================
# 09-b83-terreno — il terreno del banco della BIFORCAZIONE.
# ===========================================================================
#
# ⛔ ISOLAMENTO, e per questo banco vale doppio perche' tocca la RETE:
#      porta **7971** · albero `/media/REMOTIX/src/09nr8-src` ·
#      lavoro `/media/REMOTIX/tmp/09nr8` · utente **provanr8** (uid 1071) ·
#      unita' `remotix-7971.service`, ban-file, socket e certificati propri.
#
#    ⛔⛔ NON SI TOCCANO: la **7920** (la sessione VIVA dell'utente) e l'utente
#         **`prova2`**; ne' la **7900** e la **7910**, che sono termini di
#         paragone gia' misurati.  Il ban di §4.4-bis e' per INDIRIZZO e dura 12
#         ore: un banco che lo fa scattare mette fuori uso tutti gli altri.
#
# ⛔ Per tutto quel che non e' l'albero si delega a `07-b64-terreno.sh`, che e'
#    gia' certificato: due descrizioni dello stesso terreno in due file sono due
#    descrizioni che divergono.
#
# ⭐ E l'albero si porta **dall'albero di lavoro**, non da un punto della
#    storia: questo banco misura il prodotto com'e' adesso, e l'`md5` si
#    dichiara subito dopo aver compilato.
#
# Uso (dal portatile):
#     bash banchi/09-b83-terreno.sh porta      # sorgenti dall'albero + compila
#     bash banchi/09-b83-terreno.sh utente
#     bash banchi/09-b83-terreno.sh accendi
#     bash banchi/09-b83-terreno.sh impronta
#     bash banchi/09-b83-terreno.sh spegni
#     bash banchi/09-b83-terreno.sh stato
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-7971}
export UTENTE=${UTENTE:-provanr8}
export UID_B=${UID_B:-1071}
export PAROLA_UTENTE=${PAROLA_UTENTE:-nr8-dirupo-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/09nr8-src}
export LAV=${LAV:-/media/REMOTIX/tmp/09nr8}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/09nr8-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/09nr8}
export UNITA=${UNITA:-remotix-$PORTA}
export MACCHINA PAROLA_SUDO IND

QUI=$(cd "$(dirname "$0")/.." && pwd)
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

PASSO=${1:-stato}

case "$PASSO" in
porta)
	# ⛔ `07-b64-terreno.sh porta` porta i sorgenti dall'albero di lavoro
	#    ESCLUDENDO `*.o` e `src/remotix`: senza quell'esclusione `make`
	#    troverebbe tutto aggiornato e resterebbe il binario del portatile —
	#    la forma D5, «un binario stantio resta verde».
	# ⚠ Ma NON porta `01-b4-validatore.py`, che e' l'arbitro di §11.1: senza,
	#   il lettore della traccia muore a ogni giro e il giornale resta vuoto —
	#   e un giornale vuoto ha la faccia identica a «la sessione non ha
	#   consegnato niente» (`[M]` 23 ago 2026).  ⇒ Si copia subito dopo.
	bash "$QUI/banchi/07-b64-terreno.sh" porta || exit 2
	scp -q "$QUI/banchi/01-b4-validatore.py" "$MACCHINA:$ALBERO/banchi/" || {
		ko "⛔ l'arbitro di §11.1 non e' arrivato nell'albero"; exit 2; }
	ok "l'arbitro di §11.1 e' in $ALBERO/banchi/01-b4-validatore.py"
	exec "$0" impronta ;;
impronta)
	log "L'IMPRONTA DEL BINARIO — si dichiara, non si ricorda"
	ssh -o BatchMode=yes "$MACCHINA" \
		"md5sum $ALBERO/src/remotix; \
		 grep -ac 'rete-quic ' $ALBERO/src/remotix || true" | sed 's/^/    --  /'
	exit 0 ;;
utente|accendi|sblocca|spegni|stato)
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
*)
	ko "passo sconosciuto: $PASSO"; exit 2 ;;
esac
