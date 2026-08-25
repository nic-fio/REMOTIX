#!/bin/sh
# ===========================================================================
# 10-b90-sessione — apre e chiude le sessioni DEL BANCO 10-a4, e SOLO quelle.
#
# ⛔⛔ PERCHE' NON RIUSA `09-b71-sessione.sh`, che pure fa la stessa cosa.
#
#     Quel copione chiude con `pkill -f 01-b3-cliente.py`, cioe' **per nome del
#     copione**.  In fase 9 era giusto: c'era un banco solo per volta.  ⛔ Nella
#     fase 10 gli agenti lavorano INSIEME, e ognuno apre i suoi clienti con lo
#     stesso identico nome: quel `pkill` ammazzerebbe **le sessioni dei
#     vicini**, e il vicino se ne accorgerebbe come «la sessione e' morta a
#     meta' misura», che assomiglia a dieci altre cose.
#     ⚠ E' la forma peggiore di rottura dell'isolamento: non da' errore a chi
#       la commette, la paga un altro.
#
# ⇒ Qui i clienti si riconoscono dal MIO ALBERO nella riga di comando
#   (`/srv/src/10a4-src/banchi/01-b3-cliente.py`), che e' l'unica cosa che
#   distingue i miei dai loro.
#
# ⛔ E il congedo si manda con TERM, non con `kill -9`: il cliente ucciso di
#    forza non manda il CONGEDO, il server tiene la sessione aperta fino allo
#    scadere dell'inattivita' QUIC, e il giro dopo si becca
#    `0x0f GIA_ATTIVA_REMOTA`.  `[M]` fase 9, 23 ago 08:06.
#
#   sh 10-b90-sessione.sh <nome> <argomenti del cliente...>
#   sh 10-b90-sessione.sh -- spegni
# ===========================================================================
set -u
LAV=${LAV:-/media/REMOTIX/tmp/10a4}
DENTRO_ALB=${DENTRO_ALB:-/srv/src/10a4-src}
CLI=$DENTRO_ALB/banchi/01-b3-cliente.py
# ⭐ L'ago che riconosce i MIEI e nessun altro.
MIEI="$DENTRO_ALB/banchi/01-b3-cliente.py"

if [ "${2:-}" = "spegni" ]; then
	pkill -f "$MIEI" 2>/dev/null
	i=0
	while [ $i -lt 30 ]; do
		pgrep -f "$MIEI" >/dev/null 2>&1 || exit 0
		i=$((i + 1))
		sleep 1
	done
	# ⚠ Dopo 30 s si insiste, e SI DICE: un `-9` silenzioso lascerebbe il
	#   `GIA_ATTIVA_REMOTA` al giro dopo senza spiegazione.
	echo "⚠ dopo 30 s ci sono ancora clienti miei: mando -9 (il giro dopo puo' becccarsi 0x0f)"
	pkill -9 -f "$MIEI" 2>/dev/null
	exit 0
fi

NOME=$1
shift
LOG=$LAV/b90-$NOME.log
: > "$LOG"
chmod 666 "$LOG"

setsid nohup bash /media/REMOTIX/enter.sh --root "python3 -u $CLI $*" >>"$LOG" 2>&1 &
echo $! > "$LAV/b90-$NOME.pid"

# ⛔ Non si dichiara «aperta» perche' il processo esiste: si aspetta la riga che
#    lo dice (`LEZIONI.md` §1.9).
i=0
while [ $i -lt 240 ]; do
	if grep -q "SESSIONE" "$LOG" 2>/dev/null; then
		echo "SESSIONE APERTA — $(grep -m1 SESSIONE "$LOG")"
		exit 0
	fi
	if ! pgrep -f "$MIEI" >/dev/null 2>&1; then
		echo "SESSIONE MORTA prima di aprirsi — il suo registro:"
		tail -30 "$LOG"
		exit 1
	fi
	i=$((i + 1))
	sleep 0.5
done
echo "SESSIONE NON APERTA in 120 s — il suo registro:"
tail -30 "$LOG"
exit 1
