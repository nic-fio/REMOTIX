#!/usr/bin/env bash
# ===========================================================================
# 10-b93-terreno — il terreno del banco DELLA TABELLA PIENA (agente 10-A8)
#
#   porta 8030 · utenti `provadec4` (1103), `provadec5` (1104), `provadec6` (1105)
#   albero /media/REMOTIX/src/10a8-src · lavoro /media/REMOTIX/tmp/10a8
#   unita' remotix-8030 · lucchetto GPU `10-a8`
#
# ⛔ NON RISCRIVE `07-b64-terreno.sh`: gli passa il MIO ambiente e lo chiama,
#    come fa `09-b86-terreno.sh`.  L'unico passo tutto mio e' `porta`, e la
#    ragione e' la riga qui sotto.
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐⭐ IL TRUCCO CHE RENDE QUESTO BANCO POSSIBILE, E CHE VA DICHIARATO
# ═══════════════════════════════════════════════════════════════════════════
#
# Riempire una tabella da **16** vuol dire aprire sedici sessioni GRAFICHE vere
# su un i5-13500T: costoso, lento, e misurerebbe la MACCHINA invece del
# COMPORTAMENTO.  ⇒ Questo albero si compila con `MAX_ATTACCATE` **piccolo**
# (predefinito **2**, `MAX_ATT=n` per cambiarlo), e la tabella si riempie con
# due clienti.
#
# ⛔ **CHE COSA SI MISURA ALLORA**: il comportamento AL RIEMPIMENTO — quale
#    motivo esce sul filo, che cosa vede chi era gia' dentro, che cosa resta
#    appeso dopo un rifiuto.  ⛔ **NON** si misura il NUMERO: due non e' dieci e
#    non e' sedici, e nessuna riga di questo banco pretende il contrario.
#
# ⛔ E LA MODIFICA VIVE SOLO QUI, SULLA MACCHINA DI PROVA: `src/rcp.c` del
#    repository non si tocca.  Il `sed` gira DOPO lo scaricamento del tar, sulla
#    copia in `$ALBERO`.
#
# ⛔⛔ E VA FATTO SU TUTT'E DUE LE COPIE — `src/rcp.c` **e** `banchi/rcp/rcp.c`:
#      il Makefile confronta le gemelle (rilievo R12.3) e si RIFIUTA di
#      compilare se divergono.  Un `sed` su una sola delle due non da' un
#      binario con 16: da' un errore di compilazione.
#
# ⚠ `MAX_FIGLI` (`figlio.c:91`) **non** si tocca, ed e' voluto: il commento
#   accanto dichiara che «segue» `MAX_ATTACCATE`, ma sono due `#define`
#   separati e nessuno li lega.  Lasciandolo a 16 il banco MISURA la
#   divergenza invece di nasconderla.
#
# Uso (dal portatile):
#     bash banchi/10-b93-terreno.sh utenti      # tutt'e tre
#     MAX_ATT=2 bash banchi/10-b93-terreno.sh porta
#     bash banchi/10-b93-terreno.sh accendi
#     bash banchi/10-b93-terreno.sh stato
#     bash banchi/10-b93-terreno.sh spegni
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
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
MAX_ATT=${MAX_ATT:-2}

# I miei tre utenti, in ordine: (nome uid)
UTENTI="provadec4:1103 provadec5:1104 provadec6:1105"

QUI=$(cd "$(dirname "$0")/.." && pwd)
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

PASSO=${1:-stato}
case "$PASSO" in
utenti)
	# ⛔ Tre utenti, e servono tutti e tre: con `MAX_ATTACCATE=2` due riempiono
	#    la tabella e il TERZO e' il respinto.  ⚠ E il respinto dev'essere un
	#    utente DIVERSO, o riceverebbe `0x0F` (posto occupato) invece di `0x0E`
	#    (tabella piena) — sono due strade diverse di `posto_prendi()`.
	for u in $UTENTI; do
		n=${u%%:*}; i=${u##*:}
		log "utente $n (uid $i)"
		UTENTE=$n UID_B=$i bash "$QUI/banchi/07-b64-terreno.sh" utente || exit 2
	done
	exit 0 ;;

porta)
	log "1 · I sorgenti in $ALBERO — e il MIO MAX_ATTACCATE=$MAX_ATT"
	printf '    --  HEAD = %s\n' "$(cd "$QUI" && git rev-parse --short HEAD)"
	inf "md5 locale rcp.c:    $(md5sum "$QUI/src/rcp.c" | cut -d' ' -f1)"
	inf "md5 locale figlio.c: $(md5sum "$QUI/src/figlio.c" | cut -d' ' -f1)"
	inf "md5 locale main.c:   $(md5sum "$QUI/src/main.c" | cut -d' ' -f1)"
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
		banchi/01-b4-validatore.py \
		banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py | \
		gzip | ssh -o BatchMode=yes "$MACCHINA" \
		"mkdir -p $ALBERO && tar -C $ALBERO -xzf -" || {
		ko "⛔ i sorgenti non sono arrivati"; exit 2; }
	ok "sorgenti in $ALBERO"

	log "2 · ⛔ IL SED, sulle DUE copie gemelle — e solo qui, mai nel repository"
	# ⛔⛔ IL NUMERO SI E' SPOSTATO — 25 agosto 2026, cura C3 della fase 10.
	#
	#   Prima erano QUATTRO `#define` a 16 copiati a mano, e questo copione ne
	#   sostituiva uno solo, in `rcp.c`.  Adesso il numero e' UNO —
	#   `RCP_TETTO_SESSIONI` in `rcp.h` — e lo seguono `MAX_ATTACCATE`,
	#   `MAX_FIGLI`, `QUANTI_PRESENTI` e `WT_PALCHI`.
	#
	# ⛔⛔ E il modo in cui questo copione falliva era il PEGGIORE: un `sed` su
	#   un modello che non c'e' piu' esce **0 senza sostituire**, il terreno
	#   dichiarava successo, il tetto restava 16, e il banco finiva in «non ho
	#   misurato» — cioe' un guasto che non morde travestito da terreno sano.
	#   ⇒ Adesso si CONTA se la sostituzione ha morso, e se non ha morso su
	#     tutt'e due le gemelle il terreno si FERMA.
	ssh -o BatchMode=yes "$MACCHINA" "bash -s" <<SED_FINE || { ko "⛔ il sed non ha morso: il tetto sarebbe rimasto 16 e il banco avrebbe detto «non ho misurato»"; exit 2; }
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
cmp -s $ALBERO/src/rcp.c $ALBERO/banchi/rcp/rcp.c && echo 'gemelle rcp.c: uguali'
SED_FINE

	log "3 · Compilo dentro il contenitore"
	if ! ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
		  bash $DENTRO_ALB/src/costruisci.sh 2>&1 | tail -25'"; then
		ko "⛔ la compilazione e' fallita: NON accendo niente"
		exit 2
	fi
	ok "compilato"

	# ⛔⭐ E IL BINARIO CHE MISURO E' QUELLO CHE CREDO.  Tre gambe, e la terza
	#     e' l'unica che parli del BINARIO e non dei sorgenti:
	#       a. l'md5 dei due sorgenti gemelli e il `#define` letto da tutt'e due;
	#       b. l'md5 del binario e la sua eta' RISPETTO a rcp.c (un binario piu'
	#          vecchio del sorgente e' la forma D5, «stantio ma verde»);
	#       c. ⭐ il numero letto DAL BINARIO: la riga di §8.2 che il prodotto
	#          scrive quando la tabella e' piena porta `%d su %d`, e il secondo
	#          `%d` E' `MAX_ATTACCATE`.  ⚠ Quella riga la produce il BANCO, a
	#          giro fatto: qui si controlla solo che il formato sia nel binario,
	#          cioe' che il banco avra' da dove leggerlo.
	log "4 · ⛔ CHE COSA HO COSTRUITO"
	ssh -o BatchMode=yes "$MACCHINA" "
		echo \"#define src:     \$(grep -h '^#define RCP_TETTO_SESSIONI' $ALBERO/src/rcp.h)\"
		echo \"#define gemella: \$(grep -h '^#define RCP_TETTO_SESSIONI' $ALBERO/banchi/rcp/rcp.h)\"
		echo \"#define figli:   \$(grep -h '^#define MAX_FIGLI' $ALBERO/src/figlio.c)\"
		echo \"md5 rcp.c:       \$(md5sum $ALBERO/src/rcp.c | cut -d' ' -f1)\"
		echo \"md5 figlio.c:    \$(md5sum $ALBERO/src/figlio.c | cut -d' ' -f1)\"
		echo \"md5 binario:     \$(md5sum $ALBERO/src/remotix | cut -d' ' -f1)\"
		echo \"eta' binario:    \$(stat -c %Y $ALBERO/src/remotix) · rcp.c: \$(stat -c %Y $ALBERO/src/rcp.c)\"
		if [ \$(stat -c %Y $ALBERO/src/remotix) -ge \$(stat -c %Y $ALBERO/src/rcp.c) ]; then
			echo '⭐ il binario e\" piu\" giovane del sorgente'
		else
			echo '⛔ IL BINARIO E\" PIU\" VECCHIO DEL SORGENTE: forma D5'
		fi
		if grep -qa \"e' PIENO (%d su %d)\" $ALBERO/src/remotix; then
			echo \"⭐ la riga «PIENO (%d su %d)» c'e' nel binario: il banco avra' da dove leggere il numero\"
		else
			echo \"⛔ la riga «PIENO (%d su %d)» NON c'e' nel binario\"
		fi
	" || { ko "non ho potuto rileggere il binario"; exit 2; }
	exit 0 ;;

*)
	# ⛔ Tutto il resto e' `07-b64-terreno.sh`, con il MIO ambiente esportato.
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
esac
