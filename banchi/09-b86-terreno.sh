#!/usr/bin/env bash
# ===========================================================================
# 09-b86-terreno — il terreno del banco DEI PREDEFINITI RIBALTATI (agente NR11)
#
#   porta 7980 · utente `provanr11` (uid 1080)
#   albero /media/REMOTIX/src/09nr11-src · lavoro /media/REMOTIX/tmp/09nr11
#   unita' remotix-7980
#
# ⛔ NON RISCRIVE `07-b64-terreno.sh`: gli passa il MIO ambiente e lo chiama.
#    E' modellato riga per riga su `09-b79-terreno.sh`, e ne conserva la scelta
#    che conta:
#
# ⛔⭐ I SORGENTI SI PRENDONO DALL'ALBERO DI LAVORO, NON DA `git archive HEAD`.
#     HEAD non porta i predefiniti nuovi — cioe' l'unica cosa che questo banco
#     esiste per misurare.  ⇒ Si spedisce l'albero di lavoro, e la sua identita'
#     si DICHIARA con l'md5 dei sorgenti e del binario prodotto: un nome di
#     cartella e' un'intenzione, l'md5 e' un fatto.
#
# ⛔ E il tar deve portare anche `banchi/rcp`: `src/costruisci.sh` confronta
#    `rcp.c`/`rcp.h`/`autenticazione.c` con la copia gemella (rilievo R12.3), e
#    senza quella cartella la costruzione FALLISCE.  ⚠ E le due copie devono
#    essere ALLINEATE, o fallisce lo stesso: `rcp.c` e' cambiato in questa fase.
#
# ⛔ Si porta anche `banchi/01-b4-validatore.py`: e' l'ARBITRO del formato
#    §11.1, e il lettore della traccia di `09-b70-ritmo.py` lo cerca dentro
#    l'albero.  `07-b64-terreno.sh porta` non lo spedisce.
#
# ⛔⛔ LE PORTE CHE NON SONO MIE: **7900**, **7910** e **7920** — e la 7920 e' la
#      sessione VIVA dell'utente.  Non si toccano.  `enp7s0` nemmeno: questo
#      banco non installa nessun `netem`, misura sulla linea com'e'.
#
# Uso (dal portatile):
#     bash banchi/09-b86-terreno.sh porta      # tar dell'albero di lavoro + compila
#     bash banchi/09-b86-terreno.sh utente
#     bash banchi/09-b86-terreno.sh accendi    # OPZIONI_SERVER='...' per spegnere
#     bash banchi/09-b86-terreno.sh stato
#     bash banchi/09-b86-terreno.sh spegni
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-7980}
export UTENTE=${UTENTE:-provanr11}
export UID_B=${UID_B:-1080}
export PAROLA_UTENTE=${PAROLA_UTENTE:-nr11-predefiniti-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/09nr11-src}
export LAV=${LAV:-/media/REMOTIX/tmp/09nr11}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/09nr11-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/09nr11}
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
	inf "md5 locale main.c:         $(md5sum "$QUI/src/main.c" | cut -d' ' -f1)"
	inf "md5 locale webtransport.c: $(md5sum "$QUI/src/webtransport.c" | cut -d' ' -f1)"
	inf "md5 locale rcp.c:          $(md5sum "$QUI/src/rcp.c" | cut -d' ' -f1)"
	inf "md5 locale audio.c:        $(md5sum "$QUI/src/audio.c" | cut -d' ' -f1)"
	inf "md5 locale figlio.c:       $(md5sum "$QUI/src/figlio.c" | cut -d' ' -f1)"
	# ⛔ LE DUE COPIE DI `rcp.c`/`rcp.h` SI CONTROLLANO QUI, non sulla macchina:
	#    `src/costruisci.sh` si rifiuta di compilare se divergono (R12.3), e un
	#    rifiuto a 200 km di distanza costa un giro di ssh per dire una cosa che
	#    si sa gia' adesso.
	for f in rcp.c rcp.h autenticazione.c; do
		if ! cmp -s "$QUI/src/$f" "$QUI/banchi/rcp/$f"; then
			ko "⛔ src/$f e banchi/rcp/$f DIVERGONO: la costruzione fallirebbe (R12.3)"
			exit 2
		fi
	done
	ok "le due copie di rcp.c/rcp.h/autenticazione.c sono allineate"
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
		  bash $DENTRO_ALB/src/costruisci.sh 2>&1 | tail -25'"; then
		ko "⛔ la compilazione e' fallita: NON accendo niente"
		exit 2
	fi
	ok "compilato"

	# ⛔⭐ E IL BINARIO CHE MISURO E' QUELLO CHE CREDO — si dichiara l'md5, e si
	#     controlla che porti DAVVERO le opzioni nuove.  ⚠ E anche che NON porti
	#     piu' i due nomi vecchi come interruttori: un binario stantio li
	#     accetterebbe in silenzio e i tre esiti sarebbero verdi su un prodotto
	#     che non e' questo (forma D5).
	log "3 · ⛔ CHE COSA HO COSTRUITO — md5 e le opzioni, lette dal binario"
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \"
		 echo md5 binario:      \\\$(md5sum $ALBERO/src/remotix | cut -d' ' -f1)
		 echo md5 main.c:       \\\$(md5sum $ALBERO/src/main.c | cut -d' ' -f1)
		 echo md5 webtransport: \\\$(md5sum $ALBERO/src/webtransport.c | cut -d' ' -f1)
		 echo md5 rcp.c:        \\\$(md5sum $ALBERO/src/rcp.c | cut -d' ' -f1)
		 echo md5 audio.c:      \\\$(md5sum $ALBERO/src/audio.c | cut -d' ' -f1)
		 for o in sgombra-soglia-ms sfratto-ms niente-ritmo-adattivo \
		          niente-linea-morta niente-audio-silenzio; do
		   if grep -qa -- --\\\$o $ALBERO/src/remotix; then
		     echo \\\"opzione --\\\$o: ⭐ C'E' nel binario\\\"
		   else
		     echo \\\"opzione --\\\$o: ⛔ NON C'E'\\\"; fi
		 done
		 # ⚠ Si cerca il MACRO IN USO, non il nome: il riquadro di audio.c lo
		 #   nomina apposta per dire che e' stato tolto, e un grep nudo darebbe
		 #   rosso su una riga di documentazione.
		 if grep -qaE '^#.*AUDIO_SILENZIO_PREDEFINITO|= *AUDIO_SILENZIO_PREDEFINITO' \
		      $ALBERO/src/audio.c; then
		   echo \\\"⛔ audio.c USA ancora AUDIO_SILENZIO_PREDEFINITO: due strade\\\"
		 else
		   echo \\\"⭐ il -D AUDIO_SILENZIO_PREDEFINITO non e' piu' in uso in audio.c\\\"; fi\"" \
		|| { ko "non ho potuto rileggere il binario"; exit 2; }
	exit 0 ;;
*)
	# ⛔ Tutto il resto e' `07-b64-terreno.sh`, con il MIO ambiente esportato:
	#    non se ne riscrive una riga.  ⭐ E `OPZIONI_SERVER` passa di li' fino
	#    alla riga di comando del server: e' il solo posto in cui le cure si
	#    SPENGONO, adesso che accendersi lo fanno da sole.
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
esac
