#!/usr/bin/env bash
# ===========================================================================
# 10-d1-terreno — il terreno del banco DEL BUDGET (incarico 10-D1)
#
#   porta 8250 · utenti CONDIVISI `provamt1`…`provamt11` (uid 1110-1120)
#   albero /media/REMOTIX/src/10d1-src · lavoro /media/REMOTIX/tmp/10d1
#   unita' remotix-8250 · lucchetto GPU `10-d1`
#
# ===========================================================================
# ⛔ CHE COSA NON RISCRIVE
# ===========================================================================
#
# Tutto quel che riguarda **i dieci utenti** e **il server** e' gia' scritto e
# gia' certificato in `10-b91-terreno-dieci.sh` (che a sua volta delega ogni
# singolo utente a `07-b64-terreno.sh`).  ⇒ Qui si esporta il PROPRIO ambiente
# e si CHIAMA quello, come fanno `09-b86` e `10-c3`.
#
# ⭐ L'unico passo tutto mio e' `porta`, e per una ragione precisa:
#
# ⛔⛔ IL `porta` DI `10-b91` NON PUO' PIU' FUNZIONARE SU QUEST'ALBERO, e non e'
#      un difetto suo: il suo passo 3 fa `grep 'define MAX_ATTACCATE'`,
#      `'define MAX_FIGLI'` e `'define WT_PALCHI'`, e ⛔ **quei tre `#define`
#      non esistono piu'**.  Dalla sera del 25 agosto 2026 le quattro tabelle
#      si ALLOCANO sul tetto in vigore (`--tetto-sessioni`), e il numero non e'
#      piu' una misura di array: e' `rcp_tetto()`.
#      ⇒ L'ultimo `grep` uscirebbe 1, l'`ssh` con lui, e il terreno direbbe
#        «non ho potuto rileggere il binario» **su una compilazione riuscita**.
#
# ⭐ Qui i tre `grep` sono sostituiti dalla domanda giusta — *«che numero e' in
#    vigore?»* — che si legge dalla **riga d'avvio del server**, non dai
#    sorgenti.  ⚠ E' la stessa lezione di `10-c3-terreno.sh definisci` («i
#    `#define` si leggono dopo il preprocessore, non nei sorgenti»), portata un
#    passo piu' in la': adesso il numero non e' nemmeno piu' di compilazione.
#
# Uso (dal portatile):
#     bash banchi/10-d1-terreno.sh porta       # sorgenti + compila + md5
#     bash banchi/10-d1-terreno.sh utenti      # gli undici CONDIVISI
#     OPZIONI_SERVER='--budget-mpixel-s 480' bash banchi/10-d1-terreno.sh accendi
#     bash banchi/10-d1-terreno.sh stato
#     bash banchi/10-d1-terreno.sh avvio       # ⭐ la riga d'avvio del budget
#     bash banchi/10-d1-terreno.sh spegni
#     bash banchi/10-d1-terreno.sh sgombra
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-8250}
export PAROLA_UTENTE=${PAROLA_UTENTE:-mt-dieci-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10d1-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10d1}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10d1-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10d1}
export UNITA=${UNITA:-remotix-$PORTA}
export QUANTI=${QUANTI:-10}
export CON_UNDICESIMO=${CON_UNDICESIMO:-1}

QUI=$(cd "$(dirname "$0")/.." && pwd)
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

PASSO=${1:-stato}
case "$PASSO" in
porta)
	log "1 · I sorgenti in $ALBERO"
	printf '    --  HEAD = %s (⚠ e NON e" quel che spedisco)\n' \
		"$(cd "$QUI" && git rev-parse --short HEAD)"
	for f in rcp.c rcp.h main.c figlio.c webtransport.c budget.c budget.h; do
		inf "md5 locale $f: $(md5sum "$QUI/src/$f" | cut -d' ' -f1)"
	done
	# ⛔ Le gemelle di R12.3 si controllano QUI: `costruisci.sh` si rifiuta di
	#    compilare se divergono, e un rifiuto a 200 km costa un giro di ssh.
	for f in rcp.c rcp.h autenticazione.c; do
		if ! cmp -s "$QUI/src/$f" "$QUI/banchi/rcp/$f"; then
			ko "⛔ src/$f e banchi/rcp/$f DIVERGONO (R12.3)"
			exit 2
		fi
	done
	ok "le due copie gemelle sono allineate nel repository"
	# ⛔ Si escludono `*.o` e `src/remotix`: spedendoli, `make` troverebbe tutto
	#    aggiornato e resterebbe il binario del PORTATILE — la forma D5.
	tar -C "$QUI" --exclude='src/remotix' --exclude='src/*.o' -cf - \
		src banchi/rcp \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/01-b4-validatore.py \
		banchi/attrezzi-gruppi-scheda.sh banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py \
		banchi/10-b91-terreno-dieci.sh banchi/10-b92-dieci.py \
		banchi/10-d1-terreno.sh | \
		gzip | ssh -o BatchMode=yes "$MACCHINA" \
		"mkdir -p $ALBERO && tar -C $ALBERO -xzf -" || {
		ko "⛔ i sorgenti non sono arrivati"; exit 2; }
	ok "sorgenti in $ALBERO"

	log "2 · Compilo dentro il contenitore"
	if ! ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
		  bash $DENTRO_ALB/src/costruisci.sh 2>&1 | tail -25'"; then
		ko "⛔ la compilazione e' fallita: NON accendo niente"
		exit 2
	fi
	ok "compilato"

	log "3 · ⛔ CHE COSA HO COSTRUITO — e il budget dev'essere DENTRO il binario"
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \"
		 echo md5 binario:   \\\$(md5sum $ALBERO/src/remotix | cut -d' ' -f1)
		 echo md5 budget.c:  \\\$(md5sum $ALBERO/src/budget.c | cut -d' ' -f1)
		 echo tetto sorgente: \\\$(grep -n 'define RCP_TETTO_SESSIONI' $ALBERO/src/rcp.h)
		 echo -n 'le tre opzioni nel binario: '
		 for o in budget-mpixel-s tetto-sessioni riserva; do
		   if grep -aq -- \\\"--\\\$o\\\" $ALBERO/src/remotix; then echo -n \\\"\\\$o=SI \\\"; else echo -n \\\"\\\$o=NO \\\"; fi
		 done; echo\"" \
		|| { ko "non ho potuto rileggere il binario"; exit 2; }
	exit 0 ;;

avvio)
	# ⭐ IL NUMERO IN VIGORE SI LEGGE DALLA RIGA D'AVVIO, non dai sorgenti.
	#    ⛔ E' la domanda giusta: dal 25 agosto sera il tetto non e' piu' un
	#      `#define`, quindi «com'e' scritto» e «che cosa e' in vigore» sono due
	#      fatti che possono divergere — ed e' proprio la divergenza che `[M]`
	#      §6.4 aveva misurato sui quattro `#define` a mano.
	log "La riga d'avvio del budget e del tetto — letta dal registro"
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \"
		 grep -aE 'budget|tetto AMMINISTRATIVO' $LAV/registro.log | tail -6\"" \
		|| { ko "non ho potuto leggere il registro"; exit 2; }
	exit 0 ;;

*)
	# ⛔ Tutto il resto e' `10-b91-terreno-dieci.sh`, col MIO ambiente.
	exec bash "$QUI/banchi/10-b91-terreno-dieci.sh" "$PASSO" ;;
esac
