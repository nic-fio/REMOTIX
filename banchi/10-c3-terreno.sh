#!/usr/bin/env bash
# ===========================================================================
# 10-c3-terreno — il terreno del banco DEI PALCHI PIENI (incarico 10-C3, P3)
#
#   porta 8230 · utenti `provadec4` (1103), `provadec5` (1104), `provadec6` (1105)
#   albero /media/REMOTIX/src/10c3-src · lavoro /media/REMOTIX/tmp/10c3
#   unita' remotix-8230 · lucchetto GPU `10-c3`
#
# ⛔ NON RISCRIVE `07-b64-terreno.sh`: gli passa il MIO ambiente e lo chiama,
#    come fanno `09-b86-terreno.sh` e `10-b93-terreno.sh`.  I passi tutti miei
#    sono `porta` (il sed + la compilazione + la lettura di quel che ho
#    costruito) e `utenti`.
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐⭐ IL TRUCCO, DICHIARATO — ed e' quello di `10-b93-terreno.sh`, SPOSTATO
# ═══════════════════════════════════════════════════════════════════════════
#
# Riempire una tabella da **16** vuol dire aprire sedici sessioni GRAFICHE vere
# su un i5-13500T: costoso, lento, e misurerebbe la MACCHINA invece del
# COMPORTAMENTO.  ⇒ Questo albero si compila col tetto **piccolo**
# (`TETTO=n`, predefinito **2**), e le tabelle si riempiono con due clienti.
#
# ⛔ **QUEL CHE SI MISURA E' IL COMPORTAMENTO AL RIEMPIMENTO, NON IL NUMERO.**
#    Due non e' dieci e non e' sedici, e nessuna riga di questo banco pretende
#    il contrario.
#
# ⭐⭐ E LA DIFFERENZA CON `10-b93` E' TUTTA IN UNA RIGA DEL `sed`.
#
#    `10-b93` faceva `sed` su **`#define MAX_ATTACCATE 16`** in `src/rcp.c` e
#    nella gemella, e dichiarava per iscritto che `MAX_FIGLI` sarebbe rimasto
#    **16** — «cosi' il banco MISURA la divergenza invece di nasconderla».
#    `[M]` §6.4 l'ha vista: due posti e quattordici figli ancora disponibili.
#
#    ⛔ Da oggi quel `#define` **non esiste piu'**: il numero e' UNO e sta in
#       `src/rcp.h` (`RCP_TETTO_SESSIONI`).  ⇒ Questo terreno fa `sed` su
#       **una riga sola**, in `rcp.h` e nella sua gemella, e il passo 4
#       verifica che **tutti e quattro** l'abbiano seguita.
#    ⚠ Se il passo 4 trovasse un numero fuori posto, il legame si e' rotto di
#      nuovo: e' esattamente la prova che oggi darebbe rosso sul prodotto di
#      ieri.
#
# ⛔ E LA MODIFICA VIVE SOLO QUI, SULLA MACCHINA DI PROVA: `src/` del
#    repository non si tocca.  Il `sed` gira DOPO lo scaricamento del tar.
# ⛔⛔ E VA FATTO SU TUTT'E DUE LE COPIE — `src/rcp.h` **e** `banchi/rcp/rcp.h`:
#      il Makefile confronta le gemelle (rilievo R12.3) e si RIFIUTA di
#      compilare se divergono.
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔ I GUASTI CHE SI INNESTANO DA QUI — `LEZIONI.md` §1.29
# ═══════════════════════════════════════════════════════════════════════════
#
#   GUASTO=nessuno          il prodotto com'e' (predefinito)
#   GUASTO=congedo-muto     ⛔ rimette il difetto **P3**: il no non esce sul
#                           filo.  Il figlio non nasce lo stesso, l'utente
#                           riceve AMMESSO e SESSIONE e guarda il nero
#   GUASTO=figli-slegati    ⛔ rimette il `#define` a mano di `figlio.c`
#                           (`MAX_FIGLI 16`): i due tetti tornano a divergere,
#                           e il desktop si accende a chi verra' respinto
#   GUASTO=palchi-otto      ⛔ rimette `WT_PALCHI 8`
#   GUASTO=presenti-slegati ⛔ rimette `QUANTI_PRESENTI 16`
#
# ⚠ Ogni guasto e' un `sed` che DEVE mordere: se il modello non si trova, il
#   passo esce 2 invece di compilare il prodotto sano dichiarando di aver
#   compilato quello guasto (`LEZIONI.md` §1.9: «il controllo positivo»).
#
# Uso (dal portatile):
#     bash banchi/10-c3-terreno.sh utenti
#     TETTO=2 bash banchi/10-c3-terreno.sh porta
#     TETTO=2 GUASTO=congedo-muto bash banchi/10-c3-terreno.sh porta
#     bash banchi/10-c3-terreno.sh accendi
#     bash banchi/10-c3-terreno.sh stato
#     bash banchi/10-c3-terreno.sh spegni
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-8230}
export UTENTE=${UTENTE:-provadec4}
export UID_B=${UID_B:-1103}
export PAROLA_UTENTE=${PAROLA_UTENTE:-dec-pieno-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10c3-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10c3}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10c3-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10c3}
export UNITA=${UNITA:-remotix-$PORTA}
TETTO=${TETTO:-2}
GUASTO=${GUASTO:-nessuno}

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
	# ⛔ Tre utenti, e servono tutti e tre: con il tetto a 2 due riempiono le
	#    tabelle e il TERZO e' il respinto.  ⚠ E il respinto dev'essere un
	#    utente DIVERSO, o riceverebbe `0x0F` (posto occupato) invece del no di
	#    capacita' — sono due strade diverse, e `[M]` §6.4 le ha gia' separate.
	for u in $UTENTI; do
		n=${u%%:*}; i=${u##*:}
		log "utente $n (uid $i)"
		UTENTE=$n UID_B=$i bash "$QUI/banchi/07-b64-terreno.sh" utente || exit 2
	done
	exit 0 ;;

porta)
	log "1 · I sorgenti in $ALBERO — tetto $TETTO, guasto «$GUASTO»"
	printf '    --  HEAD = %s\n' "$(cd "$QUI" && git rev-parse --short HEAD)"
	inf "md5 locale rcp.h:   $(md5sum "$QUI/src/rcp.h" | cut -d' ' -f1)"
	inf "md5 locale main.c:  $(md5sum "$QUI/src/main.c" | cut -d' ' -f1)"
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
		banchi/07-b64-terreno.sh banchi/10-c3-terreno.sh | \
		gzip | ssh -o BatchMode=yes "$MACCHINA" \
		"mkdir -p $ALBERO && tar -C $ALBERO -xzf -" || {
		ko "⛔ i sorgenti non sono arrivati"; exit 2; }
	ok "sorgenti in $ALBERO"

	log "2 · ⛔ IL SED DEL TETTO, su UNA riga e su DUE copie gemelle"
	ssh -o BatchMode=yes "$MACCHINA" "
		set -e
		for f in $ALBERO/src/rcp.h $ALBERO/banchi/rcp/rcp.h; do
			grep -q '^#define RCP_TETTO_SESSIONI 16\$' \$f || {
				echo '⛔ il modello del tetto NON si trova in '\$f; exit 3; }
			sed -i 's/^#define RCP_TETTO_SESSIONI 16\$/#define RCP_TETTO_SESSIONI $TETTO/' \$f
			grep -n '^#define RCP_TETTO_SESSIONI' \$f
		done
		cmp -s $ALBERO/src/rcp.h $ALBERO/banchi/rcp/rcp.h && echo 'gemelle: uguali'
	" || { ko "⛔ il sed del tetto non e' riuscito"; exit 2; }

	if [ "$GUASTO" != nessuno ]; then
		log "3 · ⛔⛔ IL GUASTO «$GUASTO» — innestato di proposito"
		case "$GUASTO" in
		congedo-muto)
			G_FILE=$ALBERO/src/main.c
			G_DA='	if (senza_palco[0]) {'
			G_A='	if (0 \&\& senza_palco[0]) { /* GUASTO congedo-muto */' ;;
		figli-slegati)
			G_FILE=$ALBERO/src/figlio.c
			G_DA='#define MAX_FIGLI RCP_TETTO_SESSIONI'
			G_A='#define MAX_FIGLI 16 \/* GUASTO figli-slegati *\/' ;;
		palchi-otto)
			G_FILE=$ALBERO/src/webtransport.c
			G_DA='#define WT_PALCHI RCP_TETTO_SESSIONI'
			G_A='#define WT_PALCHI 8 \/* GUASTO palchi-otto *\/' ;;
		presenti-slegati)
			G_FILE=$ALBERO/src/main.c
			G_DA='#define QUANTI_PRESENTI RCP_TETTO_SESSIONI'
			G_A='#define QUANTI_PRESENTI 16 \/* GUASTO presenti-slegati *\/' ;;
		*)
			ko "⛔ guasto «$GUASTO» sconosciuto"; exit 2 ;;
		esac
		# ⛔⭐ E IL MODELLO PER `sed` NON E' QUELLO PER `grep -F` — costato mezz'ora
		#     il 25 agosto 2026.  `if (senza_palco[0]) {` dato a `sed` cosi'
		#     com'e' e' un'espressione REGOLARE: `[0]` non e' «parentesi quadra,
		#     zero, parentesi quadra», e' una classe che vale `0`.  ⇒ Il modello
		#     cercava `senza_palco0`, non lo trovava, e il `sed` usciva **0**
		#     senza aver sostituito niente — cioe' la forma d'errore peggiore
		#     che ci sia: «riuscito» senza aver fatto.
		# ⇒ Le quadre, il punto, l'asterisco e gli ancoraggi si scudano qui.
		G_RE=$(printf '%s' "$G_DA" | sed 's/[][\\.*^$]/\\&/g')
		# ⛔ E il modello DEVE mordere: si controlla PRIMA con `grep -F` (che non
		#    interpreta niente) e DOPO che la riga nuova ci sia davvero.
		ssh -o BatchMode=yes "$MACCHINA" "
			set -e
			grep -qF '$G_DA' $G_FILE || {
				echo '⛔ il modello del guasto NON si trova in $G_FILE'; exit 3; }
			sed -i 's|^$G_RE\$|$G_A|' $G_FILE
			grep -n 'GUASTO $GUASTO' $G_FILE
		" || { ko "⛔ il guasto non si e' innestato: NON compilo"; exit 2; }
		ok "guasto «$GUASTO» dentro $G_FILE"
	fi

	log "4 · Compilo dentro il contenitore"
	if ! ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
		  bash $DENTRO_ALB/src/costruisci.sh 2>&1 | tail -25'"; then
		ko "⛔ la compilazione e' fallita: NON accendo niente"
		exit 2
	fi
	ok "compilato"
	exit 0 ;;

definisci)
	# ═══════════════════════════════════════════════════════════════════════
	# ⭐⭐ LA PROVA DEI `#define`, e si legge DOPO IL PREPROCESSORE
	# ═══════════════════════════════════════════════════════════════════════
	#
	# ⛔ Guardare i `#define` nei sorgenti risponde alla domanda sbagliata:
	#    dice come sono SCRITTI, non che numero il compilatore ha visto.  ⚠ E'
	#    esattamente l'errore che il commento di `figlio.c` faceva da mesi —
	#    dichiarava un legame, e il legame non c'era.
	#
	# ⇒ Si chiede al preprocessore VERO, con gli stessi `-I` della
	#   compilazione, e si legge la **misura degli array**, che e' il posto in
	#   cui quel numero diventa un fatto:
	#       rcp.c          attaccate[N]
	#       figlio.c       struct figlio v[N]
	#       main.c         presenti[N]
	#       webtransport.c palchi[N]
	#   ⭐ E `aiutante.c` `in_volo[16]` DEVE restare 16: e' l'altra grandezza,
	#     e questo passo la guarda apposta per far vedere che NON ha seguito.
	log "La prova dei #define — dopo il preprocessore, dentro il contenitore"
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'bash $DENTRO_ALB/banchi/10-c3-terreno.sh --dentro-preprocessore $DENTRO_ALB'"
	exit $? ;;

--dentro-preprocessore)
	# Gira DENTRO il contenitore.  $2 = albero visto da dentro.
	ALB=${2:?serve l albero}
	B2=/srv/src/b2
	INC="-I$B2/ngtcp2/build/lib/includes -I$B2/ngtcp2/lib/includes \
-I$B2/nghttp3/build/lib/includes -I$B2/nghttp3/lib/includes -I$B2/prefisso/include"
	PKG=$(pkg-config --cflags gio-2.0 libpipewire-0.3 libdrm libavcodec libavutil libswscale 2>/dev/null)
	for coppia in "rcp.c:attaccate:attaccate" \
	              "figlio.c:v:struct figlio v" \
	              "main.c:presenti:presenti" \
	              "webtransport.c:palchi:palchi" \
	              "aiutante.c:volo:struct volo volo"; do
		f=$(printf '%s' "$coppia" | cut -d: -f1)
		nome=$(printf '%s' "$coppia" | cut -d: -f2)
		modello=$(printf '%s' "$coppia" | cut -d: -f3)
		# shellcheck disable=SC2086
		out=$(cc -E -std=gnu11 -I"$ALB/src" $INC $PKG "$ALB/src/$f" 2>/dev/null |
		      grep -oE "$modello\[[0-9]+\]" | head -1)
		if [ -z "$out" ]; then
			printf 'DEFINE %-16s %-12s ?? non ho potuto leggere\n' "$f" "$nome"
		else
			printf 'DEFINE %-16s %-12s %s\n' "$f" "$nome" "$out"
		fi
	done
	exit 0 ;;

*)
	# ⛔ Tutto il resto e' `07-b64-terreno.sh`, con il MIO ambiente esportato.
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
esac
