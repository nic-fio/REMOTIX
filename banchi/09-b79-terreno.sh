#!/usr/bin/env bash
# ===========================================================================
# 09-b79-terreno — il terreno del banco DELLE DUE CURE APPAIATE (agente NR4)
#
#   porta 7940 · utente `provanr4` (uid 1040) · albero /media/REMOTIX/src/09nr4-src
#   lavoro /media/REMOTIX/tmp/09nr4 · unita' remotix-7940
#
# ⛔ NON RISCRIVE `07-b64-terreno.sh`: gli passa il MIO ambiente e lo chiama.
#    E' modellato riga per riga su `09-b76-terreno.sh`, con **una** differenza,
#    e la differenza e' il motivo per cui questo file esiste:
#
# ⛔⭐ I SORGENTI SI PRENDONO DALL'ALBERO DI LAVORO, NON DA `git archive HEAD`.
#     `09-b76-terreno.sh` prende HEAD apposta, perche' il 23 agosto su `src/`
#     stavano lavorando altri due agenti e spedire la loro cartella a meta'
#     modifica avrebbe voluto dire misurare su un binario che nessuno aveva
#     deciso di spedire.
#     ⭐ Adesso quegli agenti hanno chiuso, e HEAD e' **vecchio**: non porta ne'
#       `--sgombra-soglia-ms` ne' `--niente-ritmo-adattivo` — cioe' le due cose che
#       questo banco esiste per misurare — ne' i contatori `dgram_persi` /
#       `dgram_falsi` e le righe `rete-quic` con `cwnd`, `srtt_us` e `giudizio=`.
#     ⇒ Qui si spedisce l'albero di lavoro, e la sua identita' si DICHIARA con
#       l'md5 dei sorgenti e del binario prodotto: un nome di cartella e'
#       un'intenzione, l'md5 e' un fatto.
#
# ⛔ E il tar deve portare anche `banchi/rcp`: `src/costruisci.sh` confronta
#    `rcp.c`/`rcp.h`/`autenticazione.c` con la copia gemella (rilievo R12.3), e
#    senza quella cartella la costruzione FALLISCE.
#
# ⛔ Si porta anche `banchi/01-b4-validatore.py`: e' l'ARBITRO del formato
#    §11.1, e il lettore della traccia di `09-b70-ritmo.py` lo cerca dentro
#    l'albero.  `07-b64-terreno.sh porta` non lo spedisce.
#
# ⛔ `enp7s0` non si tocca: qui non si tocca nessuna rete, ma il server nasce
#    sulla 7940 e le 7900/7910/7920/7930/7931/7932 non sono mie.
#
# Uso (dal portatile):
#     bash banchi/09-b79-terreno.sh porta      # tar dell'albero di lavoro + compila
#     bash banchi/09-b79-terreno.sh utente
#     bash banchi/09-b79-terreno.sh accendi    # OPZIONI_SERVER='...' per le cure
#     bash banchi/09-b79-terreno.sh stato
#     bash banchi/09-b79-terreno.sh spegni
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-7940}
export UTENTE=${UTENTE:-provanr4}
export UID_B=${UID_B:-1040}
export PAROLA_UTENTE=${PAROLA_UTENTE:-nr4-due-cure-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/09nr4-src}
export LAV=${LAV:-/media/REMOTIX/tmp/09nr4}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/09nr4-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/09nr4}
export UNITA=${UNITA:-remotix-$PORTA}

QUI=$(cd "$(dirname "$0")/.." && pwd)
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

PASSO=${1:-stato}
case "$PASSO" in
porta)
	log "1 · I sorgenti DELL'ALBERO DI LAVORO in $ALBERO"
	printf '    --  HEAD = %s (⚠ e NON e" quel che spedisco)\n' \
		"$(cd "$QUI" && git rev-parse --short HEAD)"
	inf "md5 locale webtransport.c: $(md5sum "$QUI/src/webtransport.c" | cut -d' ' -f1)"
	inf "md5 locale rcp.c:          $(md5sum "$QUI/src/rcp.c" | cut -d' ' -f1)"
	# ⛔ `banchi/rcp` c'e' o `costruisci.sh` fallisce sul confronto gemello.
	tar -C "$QUI" --exclude='src/remotix' --exclude='src/*.o' -cf - \
		src banchi/rcp \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/01-b4-validatore.py \
		banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py | \
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

	# ⛔⭐ E IL BINARIO CHE MISURO E' QUELLO CHE CREDO — si dichiara l'md5, e si
	#     controlla che porti DAVVERO le due opzioni della fase.  Un binario
	#     vecchio accetterebbe `--sgombra-soglia-ms` con un errore, e un errore
	#     all'avvio ha la stessa faccia di un server che non parte.
	log "3 · ⛔ CHE COSA HO COSTRUITO — md5 e le due opzioni, lette dal binario"
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \"
		 echo md5 binario:      \\\$(md5sum $ALBERO/src/remotix | cut -d' ' -f1)
		 echo md5 webtransport: \\\$(md5sum $ALBERO/src/webtransport.c | cut -d' ' -f1)
		 for o in sgombra-soglia-ms niente-ritmo-adattivo; do
		   if grep -qa -- --\\\$o $ALBERO/src/remotix; then
		     echo \\\"opzione --\\\$o: ⭐ C'E' nel binario\\\"
		   else
		     echo \\\"opzione --\\\$o: ⛔ NON C'E'\\\"; fi
		 done\"" || { ko "non ho potuto rileggere il binario"; exit 2; }
	exit 0 ;;
*)
	# ⛔ Tutto il resto e' `07-b64-terreno.sh`, con il MIO ambiente esportato:
	#    non se ne riscrive una riga.  ⭐ E `OPZIONI_SERVER` passa di li' fino
	#    alla riga di comando del server: e' il solo posto in cui le due cure
	#    si accendono.
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
esac
