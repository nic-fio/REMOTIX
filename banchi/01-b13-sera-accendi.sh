#!/bin/bash
#
# 01-b13-sera-accendi.sh — gira DENTRO il contenitore.  Accende il PRODOTTO su
# una porta di questo agente, per il giro nuovo della sonda (B13, sera dell'11
# agosto 2026).
#
#   bash /srv/src/01-b13-sera-accendi.sh accendi
#   bash /srv/src/01-b13-sera-accendi.sh spegni
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' NON SI USA LA 7448
#
# La 7448 e' del prodotto di un altro agente e la 7447 e' dell'innesto: sono
# porte che questo giro non tocca.  ⛔ E non e' prudenza generica: la sonda fa
# DUE giri, e il secondo sbaglia la parola d'ordine apposta — cioe' consuma il
# conto di `RCP.md` §4.4-bis **sul server che interroga**.  Farlo sul server di
# un altro banco vorrebbe dire lasciargli addosso un tentativo che non ha fatto,
# e al quarto un ban di dodici ore su questo indirizzo.
#
# ⭐ Da cui: porta 7481, file dei ban `tmp/sera-b13-ban`, socket di comando
#    `tmp/sera-b13.sock`, certificati in `tmp/sera-b13-cert`.  Nessun altro
#    banco nomina nessuno dei quattro.
#
# ---------------------------------------------------------------------------
# ⛔ B0.7: MARCATORI, NON `sleep`.  «Il processo e' vivo» e «la porta risponde»
#    sono due cose, e la seconda e' quella che serve alla sonda.
set -uo pipefail

D=/srv/src/remotix
TMP=/srv/src/tmp
PORTA=${PORTA:-7481}
IND=${IND:-192.168.0.2}

CERT=$TMP/sera-b13-cert
BAN=$TMP/sera-b13-ban
SOCK=$TMP/sera-b13.sock
LOG=$TMP/sera-b13-server.log
PIDF=$TMP/sera-b13-server.pid

mkdir -p "$TMP"

case "${1:-accendi}" in
spegni)
	if [ -f "$PIDF" ]; then
		pid=$(cat "$PIDF")
		# ⛔ Si spegne PER PID, e solo il proprio: `pkill -f` prenderebbe anche
		#    il server di un altro agente, che e' esattamente il danno che
		#    questo banco esiste per non fare.
		kill "$pid" 2>/dev/null
		g=0
		while [ -d "/proc/$pid" ] && [ "$g" -lt 20 ]; do sleep 0.5; g=$((g+1)); done
		[ -d "/proc/$pid" ] && printf 'NO  il pid %s non e\x27 morto\n' "$pid" \
		                    || printf 'OK  spento (pid %s)\n' "$pid"
		rm -f "$PIDF"
	else
		printf '--  nessun %s: non c\x27era niente di mio acceso\n' "$PIDF"
	fi
	rm -f "$SOCK"
	exit 0 ;;
accendi) ;;
*) echo "uso: $0 [accendi|spegni]"; exit 2 ;;
esac

# ── lo stato iniziale (B0.1): la porta dev'essere libera, e si VERIFICA ──────
n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
if ! command -v ss >/dev/null; then
	echo "NO  ⛔ «ss» non c'e': non ho guardato la porta, e non lo chiamo libero"
	exit 2
fi
if [ "$n" -ne 0 ]; then
	echo "NO  ⛔ la porta $PORTA e' gia' occupata ($n righe): non e' mia, non la tocco"
	ss -tuln | grep ":$PORTA\b"
	exit 2
fi
echo "OK  porta $PORTA libera (ss ha guardato e ha stampato $n righe su di lei)"

if [ ! -x "$D/remotix" ]; then
	echo "NO  ⛔ $D/remotix non c'e' o non e' eseguibile"
	exit 2
fi
echo "--  binario: $(sha256sum "$D/remotix" | cut -d' ' -f1)  $(stat -c '%y' "$D/remotix")"

rm -f "$LOG" "$PIDF" "$SOCK" "$BAN" "$BAN.nuovo"
mkdir -p "$CERT"
nohup "$D/remotix" --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
      --certificati "$CERT" --pagina "$D/pagina.html" \
      --ban-file "$BAN" --comando-socket "$SOCK" --parlantina \
      > "$LOG" 2>&1 &
pid=$!
echo "$pid" > "$PIDF"

# ⭐ IL MARCATORE: non «sono passati 3 secondi», ma «la porta risponde».
g=0
while [ "$g" -lt 60 ]; do
	[ -d "/proc/$pid" ] || break
	if [ "$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")" -ge 2 ]; then
		break
	fi
	sleep 0.5; g=$((g+1))
done
if [ ! -d "/proc/$pid" ]; then
	echo "NO  ⛔ il server e' morto subito.  Il registro dice:"
	sed 's/^/        /' "$LOG"
	exit 3
fi
righe=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
if [ "$righe" -lt 2 ]; then
	echo "NO  ⛔ il processo $pid e' vivo ma su :$PORTA ci sono $righe ascoltatori"
	echo "    §2.4 ne vuole DUE — UDP per RCP, TCP per la pagina — e la sonda"
	echo "    li usa tutt'e due: senza il TCP non ritira nemmeno l'impronta."
	sed 's/^/        /' "$LOG"
	exit 3
fi
echo "OK  acceso, pid $pid, $righe ascoltatori su :$PORTA dopo $((g/2)) s d'attesa"
echo "--  registro: $LOG · ban: $BAN · socket: $SOCK · certificati: $CERT"
sed 's/^/        /' "$LOG"
