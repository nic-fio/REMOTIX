#!/usr/bin/env bash
# ===========================================================================
# 10-b2-terreno — il terreno del banco DEL BROWSER VERO (incarico 10-b2)
#
#   porta 8120 · utenti `provadec1` (1100) e `provadec1b` (1123)
#   albero /media/REMOTIX/src/10b2-src · lavoro /media/REMOTIX/tmp/10b2
#   unita' remotix-8120 · lucchetto GPU `10-b2`
#
# ⛔ NON RISCRIVE `07-b64-terreno.sh`: gli passa il MIO ambiente e lo chiama,
#    come fanno `09-b86-terreno.sh` e `10-b93-terreno.sh`.  L'unico passo tutto
#    mio e' `porta`.
#
# ⛔⛔ GLI UTENTI `provamt1…provamt11` NON SI TOCCANO: sono condivisi fra altri
#      cinque incarichi con un protocollo suo.  Questo banco non ne apre uno.
#
# ⚠ `provadec1b` (uid **1123**, libero il 24 agosto 2026) e' **nuovo**, ed e'
#   mio: serve alla scena della **tabella piena**, dove il respinto dev'essere
#   un utente DIVERSO da chi e' dentro — altrimenti riceve `0x0F` (posto
#   occupato) invece di `0x0E` (tabella piena): sono due strade diverse di
#   `posto_prendi()`.
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐ IL TRUCCO, DICHIARATO — e vale SOLO per la scena della tabella piena
# ═══════════════════════════════════════════════════════════════════════════
#
# `MAX_ATT=n` ricompila l'albero con `#define MAX_ATTACCATE n` (il `sed` su
# **tutt'e due** le copie gemelle, o il Makefile rifiuta — R12.3).  Senza
# `MAX_ATT` **non si tocca niente**: l'albero e' quello del repository.
#
# ⛔ La scena della **sessione ferma** (`--scena viva`) si misura sull'albero
#    INTATTO: `MAX_ATTACCATE` non c'entra niente con le cure della fase 9, ma
#    un binario ritoccato che misura la sopravvivenza sarebbe una misura da
#    spiegare, e una misura da spiegare vale meno di una da leggere.
#
# ⛔ E la modifica vive SOLO sulla macchina di prova: `src/rcp.c` del
#    repository non si tocca mai.
#
# Uso (dal portatile):
#     bash banchi/10-b2-terreno.sh utenti      # tutt'e due
#     bash banchi/10-b2-terreno.sh porta       # albero INTATTO
#     MAX_ATT=1 bash banchi/10-b2-terreno.sh porta
#     bash banchi/10-b2-terreno.sh accendi     # OPZIONI_SERVER='…' per le cure
#     bash banchi/10-b2-terreno.sh stato
#     bash banchi/10-b2-terreno.sh spegni
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-8120}
export UTENTE=${UTENTE:-provadec1}
export UID_B=${UID_B:-1100}
export PAROLA_UTENTE=${PAROLA_UTENTE:-b2-browser-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10b2-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10b2}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10b2-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10b2}
export UNITA=${UNITA:-remotix-$PORTA}
MAX_ATT=${MAX_ATT:-}

# I miei due utenti, in ordine: (nome uid)
UTENTI="provadec1:1100 provadec1b:1123"

QUI=$(cd "$(dirname "$0")/.." && pwd)
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

PASSO=${1:-stato}
case "$PASSO" in
utenti)
	for u in $UTENTI; do
		n=${u%%:*}; i=${u##*:}
		log "utente $n (uid $i)"
		UTENTE=$n UID_B=$i bash "$QUI/banchi/07-b64-terreno.sh" utente || exit 2
	done
	exit 0 ;;

porta)
	log "1 · I sorgenti in $ALBERO"
	printf '    --  HEAD = %s\n' "$(cd "$QUI" && git rev-parse --short HEAD)"
	inf "md5 locale rcp.c:         $(md5sum "$QUI/src/rcp.c" | cut -d' ' -f1)"
	inf "md5 locale webtransport.c: $(md5sum "$QUI/src/webtransport.c" | cut -d' ' -f1)"
	inf "md5 locale audio.c:       $(md5sum "$QUI/src/audio.c" | cut -d' ' -f1)"
	inf "md5 locale pagina.html:   $(md5sum "$QUI/src/pagina.html" | cut -d' ' -f1)"
	for f in rcp.c rcp.h autenticazione.c; do
		if ! cmp -s "$QUI/src/$f" "$QUI/banchi/rcp/$f"; then
			ko "⛔ src/$f e banchi/rcp/$f DIVERGONO gia' nel repo (R12.3)"
			exit 2
		fi
	done
	ok "le due copie gemelle sono allineate nel repository"
	tar -C "$QUI" --exclude='src/remotix' --exclude='src/*.o' -cf - \
		src banchi/rcp \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/01-b4-validatore.py banchi/10-b2-filo.py \
		banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py | \
		gzip | ssh -o BatchMode=yes "$MACCHINA" \
		"mkdir -p $ALBERO && tar -C $ALBERO -xzf -" || {
		ko "⛔ i sorgenti non sono arrivati"; exit 2; }
	ok "sorgenti in $ALBERO"

	if [ -n "$MAX_ATT" ]; then
		log "2 · ⛔ IL SED, sulle DUE copie gemelle — RCP_TETTO_SESSIONI=$MAX_ATT"
		# ⛔⛔ IL NUMERO SI E' SPOSTATO — 25 agosto 2026, cura C3 della fase 10.
		#
		#   Prima erano QUATTRO `#define` a 16 copiati a mano, e questo copione
		#   sostituiva `#define MAX_ATTACCATE 16` in `rcp.c`.  ⛔ Dopo C3 quella
		#   riga dice `#define MAX_ATTACCATE RCP_TETTO_SESSIONI`: il modello NON
		#   c'e' piu', il `sed` usciva **0 senza sostituire**, il controllo
		#   guardava solo il codice d'uscita, il terreno dichiarava «gemelle:
		#   uguali» e COMPILAVA COL TETTO 16 — cioe' la scena «tabella PIENA»
		#   misurata su una tabella da sedici che due clienti non riempiono mai.
		#   ⇒ Adesso il numero e' UNO, `RCP_TETTO_SESSIONI` in `rcp.h`, e questo
		#     `sed` CONTA se ha morso su tutt'e due le gemelle e si FERMA se no.
		#     (E' la stessa cura di `10-b93-terreno.sh:112`, portata qui.)
		ssh -o BatchMode=yes "$MACCHINA" "bash -s" <<SED_FINE || { ko "⛔ il sed non ha morso: il tetto sarebbe rimasto 16 e il banco avrebbe misurato una tabella da sedici"; exit 2; }
set -e
n=0
for f in $ALBERO/src/rcp.h $ALBERO/banchi/rcp/rcp.h; do
	prima=\$(grep -c '^#define RCP_TETTO_SESSIONI 16\$' "\$f" || true)
	sed -i 's/^#define RCP_TETTO_SESSIONI 16\$/#define RCP_TETTO_SESSIONI $MAX_ATT/' "\$f"
	dopo=\$(grep -c '^#define RCP_TETTO_SESSIONI $MAX_ATT\$' "\$f" || true)
	echo "\$f: prima=\$prima dopo=\$dopo"
	if [ "\$prima" = 1 ] && [ "\$dopo" = 1 ]; then n=\$((n+1)); fi
done
if [ "\$n" != 2 ]; then echo '⛔ il sed NON ha morso su tutt e due le gemelle'; exit 3; fi
grep -n '^#define RCP_TETTO_SESSIONI' $ALBERO/src/rcp.h
cmp -s $ALBERO/src/rcp.h $ALBERO/banchi/rcp/rcp.h && echo 'gemelle rcp.h: uguali'
SED_FINE
	else
		log "2 · ⭐ NESSUN SED: l'albero e' quello del repository, intatto"
	fi

	log "3 · Compilo dentro il contenitore"
	if ! ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
		  bash $DENTRO_ALB/src/costruisci.sh 2>&1 | tail -25'"; then
		ko "⛔ la compilazione e' fallita: NON accendo niente"
		exit 2
	fi
	ok "compilato"

	log "4 · ⛔ CHE COSA HO COSTRUITO — letto dal BINARIO, non dai sorgenti"
	ssh -o BatchMode=yes "$MACCHINA" "
		echo \"#define src:      \$(grep -h '^#define RCP_TETTO_SESSIONI' $ALBERO/src/rcp.h)\"
		echo \"#define gemella:  \$(grep -h '^#define RCP_TETTO_SESSIONI' $ALBERO/banchi/rcp/rcp.h)\"
		echo \"#define figli:    \$(grep -h '^#define MAX_FIGLI' $ALBERO/src/figlio.c)\"
		echo \"md5 binario:      \$(md5sum $ALBERO/src/remotix | cut -d' ' -f1)\"
		echo \"md5 rcp.c:        \$(md5sum $ALBERO/src/rcp.c | cut -d' ' -f1)\"
		echo \"md5 pagina.html:  \$(md5sum $ALBERO/src/pagina.html | cut -d' ' -f1)\"
		if [ \$(stat -c %Y $ALBERO/src/remotix) -ge \$(stat -c %Y $ALBERO/src/rcp.c) ]; then
			echo '⭐ il binario e\" piu\" giovane del sorgente'
		else
			echo '⛔ IL BINARIO E\" PIU\" VECCHIO DEL SORGENTE: forma D5'
		fi
		for o in niente-audio-silenzio niente-linea-morta niente-ritmo-adattivo; do
			if grep -qa -- --\$o $ALBERO/src/remotix; then
				echo \"opzione --\$o: ⭐ C'E' nel binario\"
			else echo \"opzione --\$o: ⛔ NON C'E'\"; fi
		done
		if grep -qa \"e' PIENO (%d su %d)\" $ALBERO/src/remotix; then
			echo \"⭐ la riga «PIENO (%d su %d)» c'e' nel binario\"
		else echo \"⛔ la riga «PIENO (%d su %d)» NON c'e' nel binario\"; fi
	" || { ko "non ho potuto rileggere il binario"; exit 2; }
	exit 0 ;;

sgombra)
	# ⛔ IL PALCO SOPRAVVIVE ALLA SESSIONE, ED E' VOLUTO (invariante I4: «una
	#    sessione ferma vale piu' di una sessione staccata, e il palco puo'
	#    rinascere»).  ⚠ Ma per un banco vuol dire che il SECONDO giro parte da
	#    una scena diversa dal primo — riattacco invece di accensione — e due
	#    scene diverse dette con lo stesso nome sono la forma d'errore di
	#    `LEZIONI.md` §1.30.  ⇒ Fra un giro e l'altro il palco si sgombra, e
	#    **solo il mio**: `pkill -u` sui MIEI due utenti, mai un modello globale.
	log "Sgombro i palchi dei MIEI due utenti (e solo quelli)"
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c '
		 for u in provadec1 provadec1b; do
		   pkill -u \$u -f gnome-session-binary 2>/dev/null
		 done
		 sleep 2
		 for u in provadec1 provadec1b; do
		   echo \"\$u: \$(pgrep -u \$u -c . 2>/dev/null) processi, gnome-shell: \$(pgrep -u \$u -c gnome-shell 2>/dev/null)\"
		 done'" || { ko "⛔ lo sgombero non e' riuscito"; exit 2; }
	exit 0 ;;

*)
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
esac
