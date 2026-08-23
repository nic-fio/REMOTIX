#!/usr/bin/env bash
# ===========================================================================
# 09-b80-terreno — il terreno del banco DEL DIRUPO (agente NR5)
#
#   porta 7950 · utente `provanr5` (uid 1050) · albero /media/REMOTIX/src/09nr5-src
#   lavoro /media/REMOTIX/tmp/09nr5 · unita' remotix-7950
#
# ⛔ NON RISCRIVE `07-b64-terreno.sh` ne' `09-b76-terreno.sh`: e' `09-b76-terreno.sh`
#    con il MIO ambiente **e una cosa in piu'**, che e' la ragione per cui esiste.
#
# ⭐⭐ LA COSA IN PIU': L'ALBERO SI PORTA DA UN PUNTO QUALSIASI DELLA STORIA.
#    `09-b76-terreno.sh` fa `git archive HEAD` e basta.  Qui la domanda e'
#    *«il binario c'entra?»*, e per rispondere servono DUE alberi vivi nella
#    stessa ora: quello di `HEAD` e quello di `51b5994` (il giro di prima).
#    ⇒ `PUNTO=51b5994 ALBERO=/media/REMOTIX/src/09nr5b-src bash … porta`
#
# ⛔ E OGNI ALBERO DICHIARA IL SUO `md5`.  Due binari che si confrontano senza
#    la loro impronta sono due nomi, non due binari: se il secondo `porta` non
#    avesse ricompilato niente, la griglia «prima/dopo» sarebbe la stessa
#    griglia due volte e nessuno se ne accorgerebbe.
#
# Uso (dal portatile):
#     bash banchi/09-b80-terreno.sh porta                 # HEAD
#     PUNTO=51b5994 ALBERO=/media/REMOTIX/src/09nr5b-src \
#         bash banchi/09-b80-terreno.sh porta             # il binario di prima
#     bash banchi/09-b80-terreno.sh utente
#     bash banchi/09-b80-terreno.sh accendi
#     bash banchi/09-b80-terreno.sh impronta
#     bash banchi/09-b80-terreno.sh stato
#     bash banchi/09-b80-terreno.sh spegni
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-7950}
export UTENTE=${UTENTE:-provanr5}
export UID_B=${UID_B:-1050}
export PAROLA_UTENTE=${PAROLA_UTENTE:-nr5-dirupo-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/09nr5-src}
export LAV=${LAV:-/media/REMOTIX/tmp/09nr5}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/$(basename "$ALBERO")}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/09nr5}
export UNITA=${UNITA:-remotix-$PORTA}
PUNTO=${PUNTO:-HEAD}

QUI=$(cd "$(dirname "$0")/.." && pwd)
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

impronta() {
	ssh -o BatchMode=yes "$MACCHINA" \
		"md5sum $ALBERO/src/remotix 2>/dev/null || echo 'NON C E'"
}

PASSO=${1:-stato}
case "$PASSO" in
porta)
	log "1 · I sorgenti di «$PUNTO» (git archive) in $ALBERO"
	SHA=$(cd "$QUI" && git rev-parse --short "$PUNTO") || { ko "punto «$PUNTO» sconosciuto"; exit 2; }
	inf "$PUNTO = $SHA"
	# ⛔ Le stesse voci di `09-b76-terreno.sh`, e nello stesso ordine: se qui
	#    mancasse `01-b4-validatore.py` il lettore della traccia morirebbe a
	#    ogni giro e OGNI cella della griglia sembrerebbe una sessione morta.
	(cd "$QUI" && git archive --format=tar "$SHA" \
		src banchi/rcp \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/01-b4-validatore.py \
		banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py) | \
		gzip | ssh -o BatchMode=yes "$MACCHINA" \
		"rm -rf $ALBERO/src && mkdir -p $ALBERO && tar -C $ALBERO -xzf -" || {
		ko "⛔ i sorgenti non sono arrivati"; exit 2; }
	ok "sorgenti di $SHA in $ALBERO"

	log "2 · Compilo dentro il contenitore sulla macchina di prova"
	if ! ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
		  bash $DENTRO_ALB/src/costruisci.sh 2>&1 | tail -20'"; then
		ko "⛔ la compilazione e' fallita: NON accendo niente"
		exit 2
	fi
	ok "compilato"
	# ⛔ L'impronta si dichiara SUBITO, non a griglia finita.
	log "3 · L'impronta del binario — «$PUNTO» = $SHA"
	inf "$(impronta)"
	# ⭐ E si controlla che la riga `rete-quic` ci sia o non ci sia, che e' la
	#   sola differenza fra i due punti della storia (⇒ il sospetto del punto 4).
	inf "righe «rete-quic» nel binario: $(ssh -o BatchMode=yes "$MACCHINA" \
		"grep -ac 'rete-quic ' $ALBERO/src/remotix 2>/dev/null || echo 0")"
	exit 0 ;;
impronta)
	inf "$(impronta)"
	inf "righe «rete-quic» nel binario: $(ssh -o BatchMode=yes "$MACCHINA" \
		"grep -ac 'rete-quic ' $ALBERO/src/remotix 2>/dev/null || echo 0")"
	exit 0 ;;
*)
	# ⛔ Tutto il resto e' `07-b64-terreno.sh`, con il MIO ambiente esportato:
	#    non se ne riscrive una riga.
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
esac
