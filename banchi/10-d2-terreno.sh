#!/usr/bin/env bash
# ===========================================================================
# 10-d2-terreno — IL TERRENO DEL BANCO DEL BUDGET.
#
#   porta 8260 · utenti `provadec4` (1103) `provadec5` (1104) `provadec6` (1105)
#   albero /media/REMOTIX/src/10d2-src · lavoro /media/REMOTIX/tmp/10d2
#   unita' remotix-8260 · ban-file, socket e certificati suoi
#
# ===========================================================================
# ⛔ CHE COSA NON RISCRIVE — e non e' pigrizia, e' la regola di 09-b86
# ===========================================================================
#
# Tutto quel che riguarda **un** utente e **il** server e' gia' scritto e gia'
# certificato in `banchi/07-b64-terreno.sh`: la parola d'ordine che non passa
# da `argv` (D12), i gruppi `render,video`, `enable-linger`, il controllo `ldd`
# su ngtcp2/nghttp3 prima di accendere, l'unita' di sistema invece di un
# `setsid`, la lettura dei limiti DOPO l'`exec`.  ⇒ Qui non se ne riscrive una
# riga: si esporta il PROPRIO ambiente e si CHIAMA quello.
#
# ⭐ Questo file aggiunge le tre cose che nascono dal BUDGET:
#
#   1. `OPZIONI_SERVER` — le opzioni del budget passano al server **cosi'
#      com'e' scritto nel banco**, e se il server le rifiuta il passo
#      `accendi` **fallisce invece di accendere senza**;
#   2. il `sed` sul tetto amministrativo, con la CONTA DEL MORSO;
#   3. `dichiara` — ⛔ che cosa il binario sa fare, letto DAL BINARIO: se
#      `--budget-mpixel-s` non c'e' dentro `src/remotix`, il banco lo sa PRIMA
#      di accendere invece di scoprirlo da un'uscita non zero.
#
# ===========================================================================
# ⛔⛔ LA PAROLA D'ORDINE NON SI RIFA' — §5.4, e l'ha pagata un altro
# ===========================================================================
#
# `provadec4/5/6` sono utenti che esistono gia' e che altri banchi usano.
# ⛔ L'ultimo che chiama `chpasswd` vince, e gli altri leggono «credenziali
#    errate» su una macchina sana — ⛔⛔ **e ogni respinto consuma uno dei tre
#    tentativi del ban per INDIRIZZO, che dura DODICI ORE** e mette fuori uso
#    ogni altro agente, perche' partiamo tutti dallo stesso indirizzo.
# ⇒ `07-b64-terreno.sh` non la tocca piu' se l'utente c'era gia'; qui
#   `RIFAI_PAROLA` **non si mette mai**, e chi ne avesse bisogno lo chiede a
#   mano e sa che cosa sta facendo.
#
# ===========================================================================
# ⛔ L'ISOLAMENTO
# ===========================================================================
#
# ⛔⛔ NON SI TOCCANO: `prova`, `prova2`, `provanr*`, `provar7`, `provan9`,
#      `provamt*`, e nessuna porta che non sia la **8260**.
# ⛔ Nessun `netem`: questo banco non tocca la rete di nessuno.
#
# Uso (dal portatile):
#     bash banchi/10-d2-terreno.sh utenti           # i tre (parola NON toccata)
#     MAX_ATT=2 bash banchi/10-d2-terreno.sh porta  # sorgenti + sed + compila
#     bash banchi/10-d2-terreno.sh porta            # senza sed: tetto = 16
#     OPZIONI_SERVER='--budget-mpixel-s 1' bash banchi/10-d2-terreno.sh accendi
#     bash banchi/10-d2-terreno.sh dichiara         # che cosa sa fare il binario
#     bash banchi/10-d2-terreno.sh stato
#     bash banchi/10-d2-terreno.sh sblocca          # ⛔ sul MIO socket
#     bash banchi/10-d2-terreno.sh spegni
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-8260}
export UTENTE=${UTENTE:-provadec4}
export UID_B=${UID_B:-1103}
# ⚠ La stessa parola di `10-b93-terreno.sh`: sono gli STESSI tre utenti, e due
#   parole diverse per lo stesso utente sono il modo piu' rapido di far
#   scattare il ban per indirizzo.
export PAROLA_UTENTE=${PAROLA_UTENTE:-dec-pieno-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10d2-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10d2}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10d2-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10d2}
export UNITA=${UNITA:-remotix-$PORTA}
export OPZIONI_SERVER=${OPZIONI_SERVER:-}

# ⛔ Vuoto = NON si tocca il `#define`.  Il tetto resta quello del prodotto, ed
#    e' la condizione di D1 e del braccio FISICO di D6.
MAX_ATT=${MAX_ATT:-}

UTENTI="provadec4:1103 provadec5:1104 provadec6:1105"

QUI=$(cd "$(dirname "$0")/.." && pwd)
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

PASSO=${1:-stato}
case "$PASSO" in
utenti)
	# ⛔ Tre, e servono tutti e tre: due riempiono e il TERZO e' il respinto.
	#    ⚠ E il respinto dev'essere un utente DIVERSO, o riceverebbe `0x0F`
	#      (posto occupato) invece del motivo del tetto — sono due strade
	#      diverse di `posto_prendi()`, e questo banco misura la seconda.
	for u in $UTENTI; do
		n=${u%%:*}; i=${u##*:}
		log "utente $n (uid $i)"
		UTENTE=$n UID_B=$i bash "$QUI/banchi/07-b64-terreno.sh" utente || exit 2
	done
	exit 0 ;;

porta)
	log "1 · I sorgenti in $ALBERO"
	printf '    --  HEAD = %s\n' "$(cd "$QUI" && git rev-parse --short HEAD)"
	for f in rcp.c rcp.h autenticazione.c; do
		if ! cmp -s "$QUI/src/$f" "$QUI/banchi/rcp/$f"; then
			ko "⛔ src/$f e banchi/rcp/$f DIVERGONO gia' nel repo (R12.3)"
			exit 2
		fi
	done
	ok "le due copie gemelle sono allineate nel repository"
	# ⚠ E il `tar` porta anche `banchi/rcp`, o `costruisci.sh` si rifiuta (R12.3).
	tar -C "$QUI" --exclude='src/remotix' --exclude='src/*.o' -cf - \
		src banchi/rcp \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/01-b4-validatore.py \
		banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py | \
		gzip | ssh -o BatchMode=yes "$MACCHINA" \
		"mkdir -p $ALBERO && tar -C $ALBERO -xzf -" || {
		ko "⛔ i sorgenti non sono arrivati"; exit 2; }
	ok "sorgenti in $ALBERO"

	if [ -n "$MAX_ATT" ]; then
		log "2 · ⛔ IL SED sul tetto, sulle DUE gemelle — e MAI nel repository"
		# ⛔⛔ E SI CONTA SE HA MORSO — la cura del 25 agosto 2026.  Un `sed` su
		#     un modello che non c'e' piu' esce **0 senza sostituire**: il
		#     terreno dichiarava successo, il tetto restava 16, e il banco
		#     finiva in «non ho misurato» — cioe' **un guasto che non morde
		#     travestito da terreno sano**, che e' la forma peggiore di tutte.
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
SED_FINE
		ok "il tetto amministrativo di QUESTO albero e' $MAX_ATT"
	else
		inf "⭐ nessun sed: il tetto resta quello del prodotto (e' la scena di D1)"
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
	exec bash "$0" dichiara ;;

dichiara)
	# ⛔⭐ CHE COSA SO DI AVER COSTRUITO — e la terza gamba e' l'unica che parli
	#     del BINARIO e non dei sorgenti.  ⚠ Un banco che scoprisse solo da
	#     un'uscita non zero che l'opzione non c'e' non saprebbe distinguere
	#     «il prodotto non ce l'ha ancora» da «il server e' morto per altro».
	log "⛔ CHE COSA SA FARE IL BINARIO — letto DAL BINARIO"
	ssh -o BatchMode=yes "$MACCHINA" "
		echo \"tetto:      \$(grep -h '^#define RCP_TETTO_SESSIONI' $ALBERO/src/rcp.h)\"
		echo \"md5 rcp.h:  \$(md5sum $ALBERO/src/rcp.h | cut -d' ' -f1)\"
		echo \"md5 binario:\$(md5sum $ALBERO/src/remotix | cut -d' ' -f1)\"
		if [ \$(stat -c %Y $ALBERO/src/remotix) -ge \$(stat -c %Y $ALBERO/src/rcp.h) ]; then
			echo '⭐ il binario e piu giovane del sorgente'
		else
			echo '⛔ IL BINARIO E PIU VECCHIO DEL SORGENTE: forma D5, stantio ma verde'
		fi
		for o in --budget-mpixel-s --tetto-sessioni --riserva; do
			if grep -qa -- \"\$o\" $ALBERO/src/remotix; then
				echo \"⭐ \$o: C'E' nel binario\"
			else
				echo \"⛔ \$o: NON c'e' nel binario ⇒ le domande che lo usano diranno «non ho misurato»\"
			fi
		done
		if grep -qa 'BUDGET_PIENO' $ALBERO/src/remotix; then
			echo \"⭐ la parola BUDGET_PIENO e' nel binario\"
		else
			echo \"⚠ la parola BUDGET_PIENO non compare nel binario (potrebbe essere solo un enum)\"
		fi
	"
	exit 0 ;;

accendi|spegni|stato|sblocca)
	# ⛔ `OPZIONI_SERVER` viaggia esportato: se il server le rifiuta, il passo
	#    `accendi` di 07-b64 esce non-zero e il banco NON misura.
	[ "$PASSO" = accendi ] && inf "opzioni del server: «${OPZIONI_SERVER:-nessuna}»"
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;

sgombra)
	# ⛔⛔ SOLO I MIEI — §7.3: a fine giro un modello GLOBALE combaciava con 24
	#     clienti vivi di un altro banco.  Il mio combacia con la MIA cartella
	#     di lavoro, e la classe di caratteri impedisce al modello di
	#     acchiappare la riga di comando che lo sta eseguendo.
	log "sgombro — SOLO i miei ($DENTRO_LAV)"
	ssh -o BatchMode=yes "$MACCHINA" "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \"
		pkill -f -- '--registra [${DENTRO_LAV:0:1}]${DENTRO_LAV:1}/' ; true
		pkill -f -- '--giornale [${DENTRO_LAV:0:1}]${DENTRO_LAV:1}/' ; true
		for i in 1103 1104 1105; do pkill -u \\\$i -f '0[4]-b30-scena'; done ; true
	\"" || true
	inf "e adesso guardo com'e' rimasta:"
	ssh -o BatchMode=yes "$MACCHINA" "ss -uln | grep -E ':(7[0-9]{3}|8[0-9]{3}) ' || echo 'nessuna porta 7xxx/8xxx aperta'; pgrep -a remotix || echo 'nessun remotix'"
	exit 0 ;;

*)
	sed -n '1,62p' "$0"
	exit 2 ;;
esac
