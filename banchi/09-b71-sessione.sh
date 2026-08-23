#!/bin/sh
# 09-b71-sessione.sh — apre una sessione LUNGA in sottofondo, dentro il contenitore.
#
# ⛔ ESISTE PER LA STESSA RAGIONE DI `09-b68-scena.sh`: **un file non ha livelli
#    di virgolette.**  La riga da eseguire e'
#      ssh -> sudo -> setsid nohup bash enter.sh --root 'python3 ... ' >log &
#    cioe' quattro strati di apici, piu' un redirect verso una cartella di root
#    che la shell di `nicfio` non puo' aprire.  Scritto a mano si sbaglia, e si
#    sbaglia nel modo cattivo: la sessione «non parte» e il log e' vuoto.
#
# ⛔ E la sessione dev'essere in SOTTOFONDO, non sincrona come in `09-b68`:
#    qui il banco deve battere i colpi MENTRE il canale video e' aperto.
#
#   sh 09-b71-sessione.sh <nome> <argomenti del cliente...>
#   sh 09-b71-sessione.sh -- spegni
set -u
# ⚠ Cartella di lavoro e albero vengono da fuori — vedi `09-b68-scena.sh`.
LAV=${LAV:-/media/REMOTIX/tmp/09}
CLI=${DENTRO_ALB:-/srv/src/09-src}/banchi/01-b3-cliente.py

if [ "${2:-}" = "spegni" ]; then
	# ⛔⛔ IL `kill -9` DOPO UN SECONDO E' UN GUASTO, non una prudenza.
	#    Il cliente ucciso di forza non manda il CONGEDO: il server tiene la
	#    sessione aperta fino allo scadere dell'inattivita' QUIC, e il giro
	#    dopo si becca ⇒ `CONGEDO invece di SESSIONE: 0x0f GIA_ATTIVA_REMOTA`.
	#    `[M]` 23 ago, 08:06: successo con «prova2», e ha bruciato un giro.
	#    ⇒ si manda TERM e **si aspetta che se ne vada da solo**.
	pkill -f 01-b3-cliente.py 2>/dev/null
	i=0
	while [ $i -lt 30 ]; do
		pgrep -f '01-b3-cliente[.]py' >/dev/null 2>&1 || exit 0
		i=$((i + 1))
		sleep 1
	done
	pkill -9 -f 01-b3-cliente.py 2>/dev/null
	exit 0
fi

NOME=$1
shift
LOG=$LAV/b71-$NOME.log
: > "$LOG"
chmod 666 "$LOG"

setsid nohup bash /media/REMOTIX/enter.sh --root "python3 -u $CLI $*" >>"$LOG" 2>&1 &
echo $! > "$LAV/b71-$NOME.pid"

# ⛔ Non si dichiara «aperta» perche' il processo esiste: si aspetta la riga
#    che lo dice.  `LEZIONI.md` §1.9 — «partita» e «arrivata in fondo» hanno la
#    stessa faccia finche' non si guarda il registro.
i=0
while [ $i -lt 120 ]; do
	if grep -q "SESSIONE" "$LOG" 2>/dev/null; then
		echo "SESSIONE APERTA — $(grep -m1 SESSIONE "$LOG")"
		exit 0
	fi
	if ! pgrep -f 01-b3-cliente.py >/dev/null 2>&1; then
		echo "SESSIONE MORTA prima di aprirsi — il suo registro:"
		tail -30 "$LOG"
		exit 1
	fi
	i=$((i + 1))
	sleep 0.5
done
echo "SESSIONE NON APERTA in 60 s — il suo registro:"
tail -30 "$LOG"
exit 1
