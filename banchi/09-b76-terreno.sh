#!/usr/bin/env bash
# ===========================================================================
# 09-b76-terreno — il terreno del banco della RETE CATTIVA (agente NR1)
#
#   porta 7930 · utente `provanr1` (uid 1030) · albero /media/REMOTIX/src/09nr1-src
#   lavoro /media/REMOTIX/tmp/09nr1 · unita' remotix-7930
#
# ⛔ NON RISCRIVE `07-b64-terreno.sh`: gli passa il MIO ambiente e lo chiama.
#    L'unico passo che fa da se' e' il PRIMO, e ha una ragione precisa:
#
# ⛔⭐ I SORGENTI SI PRENDONO DA `git archive HEAD`, NON DALL'ALBERO DI LAVORO.
#     `07-b64-terreno.sh porta` fa `tar` della cartella di lavoro; oggi (23
#     agosto 2026) su `src/` stanno lavorando ALTRI DUE agenti, e spedire la
#     loro cartella a meta' modifica vorrebbe dire misurare la rete cattiva su
#     un binario che nessuno ha deciso di spedire — ⚠ e un binario che non
#     compila avrebbe la stessa faccia di un terreno assente.
#     ⇒ `git archive HEAD` e' il prodotto **come e' stato committato**, non
#       tocca la cartella di lavoro di nessuno, ed e' ripetibile.
#
# ⛔ E si porta anche `banchi/01-b4-validatore.py`: e' l'ARBITRO del formato
#    §11.1, e il lettore della traccia di `09-b70-ritmo.py` lo cerca
#    dentro l'albero.  `07-b64-terreno.sh porta` non lo spedisce.
#
# Uso (dal portatile):
#     bash banchi/09-b76-terreno.sh porta      # git archive + compila
#     bash banchi/09-b76-terreno.sh utente
#     bash banchi/09-b76-terreno.sh accendi
#     bash banchi/09-b76-terreno.sh stato
#     bash banchi/09-b76-terreno.sh spegni
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-7930}
export UTENTE=${UTENTE:-provanr1}
export UID_B=${UID_B:-1030}
export PAROLA_UTENTE=${PAROLA_UTENTE:-nr1-rete-cattiva-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/09nr1-src}
export LAV=${LAV:-/media/REMOTIX/tmp/09nr1}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/09nr1-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/09nr1}
export UNITA=${UNITA:-remotix-$PORTA}

QUI=$(cd "$(dirname "$0")/.." && pwd)
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

PASSO=${1:-stato}
case "$PASSO" in
porta)
	log "1 · I sorgenti COMMITTATI (git archive HEAD) in $ALBERO"
	printf '    --  HEAD = %s\n' "$(cd "$QUI" && git rev-parse --short HEAD)"
	(cd "$QUI" && git archive --format=tar HEAD \
		src banchi/rcp \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/01-b4-validatore.py \
		banchi/attrezzi-gruppi-scheda.sh banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py) | \
		gzip | ssh -o BatchMode=yes "$MACCHINA" \
		"mkdir -p $ALBERO && tar -C $ALBERO -xzf -" || {
		ko "⛔ i sorgenti non sono arrivati"; exit 2; }
	ok "sorgenti in $ALBERO"

	log "2 · Compilo dentro il contenitore sulla macchina di prova"
	if ! ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
		  bash $DENTRO_ALB/src/costruisci.sh 2>&1 | tail -20'"; then
		ko "⛔ la compilazione e' fallita: NON accendo niente"
		exit 2
	fi
	ok "compilato"
	exit 0 ;;
*)
	# ⛔ Tutto il resto e' `07-b64-terreno.sh`, con il MIO ambiente esportato:
	#    non se ne riscrive una riga.
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
esac
