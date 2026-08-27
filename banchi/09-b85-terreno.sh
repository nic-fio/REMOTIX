#!/bin/sh
# 09-b85-terreno.sh — il terreno del banco della SINCRONIA AUDIO-VIDEO.
#
#   bash banchi/09-b85-terreno.sh porta     # sorgenti + costruisci + md5
#   bash banchi/09-b85-terreno.sh utente    # provanr10, uid 1073
#   bash banchi/09-b85-terreno.sh accendi   # remotix-7973
#   bash banchi/09-b85-terreno.sh spegni | stato | sblocca
#
# ⛔ NON riscrive `07-b64-terreno.sh`: esporta il proprio ambiente, fa da se' il
#    solo passo `porta` (che deve spedire ANCHE i file `09-b85-*`, che in HEAD
#    non ci sono) e delega tutto il resto con `exec`.
#
# ⛔⛔ L'ISOLAMENTO, e non e' burocrazia: porta 7973, utente `provanr10`, unita'
#     `remotix-7973`, albero e lavoro propri.  ⚠ Sulla macchina girano ADESSO
#     `remotix-7900`, `-7910`, `-7920` (⛔ la 7920 e' la sessione VIVA
#     dell'utente) e i banchi di altri agenti su 7940-7971: un banco che
#     riusasse una di quelle porte, o l'utente `prova2`, spegnerebbe la
#     sessione di qualcun altro senza dare rosso.
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-7973}
export UTENTE=${UTENTE:-provanr10}
export UID_B=${UID_B:-1073}
export PAROLA_UTENTE=${PAROLA_UTENTE:-nr10-sincronia-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/09nr10-src}
export LAV=${LAV:-/media/REMOTIX/tmp/09nr10}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/09nr10-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/09nr10}
export UNITA=${UNITA:-remotix-$PORTA}

QUI=$(cd "$(dirname "$0")/.." && pwd)
PASSO=${1:-}

ko() { printf '   ⛔ %s\n' "$*"; }
ok() { printf '   ✅ %s\n' "$*"; }

case "$PASSO" in
porta)
	printf '\n== i sorgenti verso %s (albero MIO, non quello di nessun altro)\n' "$ALBERO"
	# ⛔ `git archive HEAD` e NON l'albero di lavoro per `src/`: altri agenti
	#    stanno lavorando su `src/` in questo momento, e un `tar` dell'albero
	#    di lavoro potrebbe portarsi via una cura a meta' — cioe' misurare un
	#    prodotto che non esiste in nessun punto della storia.  ⚠ Il prezzo
	#    e' che una cura non committata NON si misura da qui, e va bene: questo
	#    banco misura il prodotto di HEAD.
	SHA=$(cd "$QUI" && git rev-parse --short HEAD) || { ko "git non risponde"; exit 2; }
	printf '   ⭐ punto della storia: %s\n' "$SHA"
	(cd "$QUI" && git archive --format=tar "$SHA" \
		src banchi/rcp \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/01-b4-validatore.py \
		banchi/attrezzi-gruppi-scheda.sh banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py) | \
		gzip | ssh -o BatchMode=yes "$MACCHINA" \
		"rm -rf $ALBERO/src && mkdir -p $ALBERO && tar -C $ALBERO -xzf -" || {
		ko "⛔ i sorgenti non sono arrivati"; exit 2; }
	# ⛔ E POI I MIEI, che in HEAD non ci sono: sono i file di questo banco, e
	#    senza di loro sulla macchina non si genera nessuna claquette.
	#    ⚠ Niente `sudo` sul tar: `sudo -S` mangerebbe lo stdin, che qui E' il
	#      flusso del tar.  `/media/REMOTIX/src` e' di `nicfio`.
	(cd "$QUI" && tar -czf - banchi/09-b85-claquette.py banchi/09-b85-metro.py \
		banchi/09-b85-cliente.py banchi/09-lucchetto.py) | \
		ssh -o BatchMode=yes "$MACCHINA" "tar -C $ALBERO -xzf -" || {
		ko "⛔ i file 09-b85 non sono arrivati"; exit 2; }
	printf '\n== si compila DENTRO il contenitore\n'
	if ! ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
		  bash $DENTRO_ALB/src/costruisci.sh 2>&1 | tail -25'"; then
		ko "⛔ la compilazione e' fallita: NON accendo niente"
		exit 2
	fi
	printf '\n== l%s impronta del binario, dichiarata SUBITO\n' "'"
	ssh -o BatchMode=yes "$MACCHINA" "md5sum $ALBERO/src/remotix" | sed 's/^/        /'
	ok "terreno pronto"
	;;
*)
	# ⛔ Tutto il resto e' `07-b64-terreno.sh`, con il MIO ambiente esportato:
	#    non se ne riscrive una riga.  ⚠ Il passo `utente` fa `useradd`,
	#    `render`+`video`, `enable-linger` e la parola in un file 0600; il
	#    passo `accendi` fa l'unita' `systemd-run` con `--parlantina`.
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
esac
