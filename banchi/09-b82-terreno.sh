#!/usr/bin/env bash
# ===========================================================================
# 09-b82-terreno — il terreno del banco «LE APPLICAZIONI AVVIATE DA FUORI»
#                  (agente NR7)
#
#   porta 7970 · utente `provanr7` (uid 1070) · albero /media/REMOTIX/src/09nr7-src
#   lavoro /media/REMOTIX/tmp/09nr7 · unita' remotix-7970
#
# ⛔ NON RISCRIVE `07-b64-terreno.sh`: gli passa il MIO ambiente e lo chiama.
#    L'unico passo che fa da se' e' il PRIMO, e per due ragioni:
#
#   1. ⛔ **I sorgenti vengono dall'ALBERO DI LAVORO**, non da `git archive`
#      (che e' quel che fa `09-b76-terreno.sh`).  Il mandato di oggi lo chiede
#      per nome, e l'`md5` di `figlio.c`/`sessione.c`/`mutter.c` si DICHIARA
#      all'accensione: un nome di cartella e' un'intenzione, l'`md5` e' un
#      fatto.  ⚠ Il prezzo: se un altro agente sta a meta' di una modifica su
#      `src/`, quella modifica entra in questo binario — per questo l'`md5` si
#      stampa, e chi legge il rapporto puo' verificarlo.
#   2. ⛔ Si porta anche `banchi/09-b82-mostra.sh`, che e' lo strumento che
#      questo banco esiste per lasciare: `07-b64-terreno.sh porta` non lo
#      spedisce, e uno strumento che sta solo sul portatile non serve a nessuno.
#
# Uso (dal portatile):
#     bash banchi/09-b82-terreno.sh porta      # albero di lavoro + compila
#     bash banchi/09-b82-terreno.sh utente
#     bash banchi/09-b82-terreno.sh accendi
#     bash banchi/09-b82-terreno.sh stato
#     bash banchi/09-b82-terreno.sh spegni
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-7970}
export UTENTE=${UTENTE:-provanr7}
export UID_B=${UID_B:-1070}
export PAROLA_UTENTE=${PAROLA_UTENTE:-nr7-finestre-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/09nr7-src}
export LAV=${LAV:-/media/REMOTIX/tmp/09nr7}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/09nr7-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/09nr7}
export UNITA=${UNITA:-remotix-$PORTA}

QUI=$(cd "$(dirname "$0")/.." && pwd)
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

PASSO=${1:-stato}
case "$PASSO" in
porta)
	log "1 · I sorgenti DELL'ALBERO DI LAVORO in $ALBERO"
	printf '    --  HEAD = %s · git status = %s\n' \
		"$(cd "$QUI" && git rev-parse --short HEAD)" \
		"$(cd "$QUI" && git status --short | wc -l) file modificati"
	printf '    --  md5 figlio.c   = %s\n' "$(md5sum "$QUI/src/figlio.c"   | cut -d' ' -f1)"
	printf '    --  md5 sessione.c = %s\n' "$(md5sum "$QUI/src/sessione.c" | cut -d' ' -f1)"
	printf '    --  md5 mutter.c   = %s\n' "$(md5sum "$QUI/src/mutter.c"   | cut -d' ' -f1)"
	# ⛔ Si ESCLUDONO oggetti e binario del portatile: spedendoli, `make`
	#    troverebbe tutto aggiornato e resterebbe il binario del portatile.
	tar -C "$QUI" --exclude='*.o' --exclude='src/remotix' -czf - \
		src banchi/rcp \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/01-b4-validatore.py \
		banchi/09-b82-mostra.sh \
		banchi/attrezzi-gruppi-scheda.sh banchi/07-b64-terreno.sh | \
		ssh -o BatchMode=yes "$MACCHINA" \
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
	ssh -o BatchMode=yes "$MACCHINA" "md5sum $ALBERO/src/remotix" | sed 's/^/    --  md5 binario: /'
	exit 0 ;;
*)
	# ⛔ Tutto il resto e' `07-b64-terreno.sh`, con il MIO ambiente esportato:
	#    non se ne riscrive una riga.
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
esac
