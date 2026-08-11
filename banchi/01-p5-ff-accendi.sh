#!/bin/bash
#
# 01-p5-ff-accendi.sh — ⛔ GIRA DENTRO IL CONTENITORE.  Accende una COPIA del
# prodotto sulla porta 7511, che serve la PAGINA STRUMENTATA di questo banco.
#
#   bash /srv/src/01-p5-ff-accendi.sh accendi
#   bash /srv/src/01-p5-ff-accendi.sh spegni
#
# ---------------------------------------------------------------------------
# ⛔ IL PERIMETRO, E PERCHE' NON E' PRUDENZA GENERICA
#
# La 7448 ha un server VIVO che non e' di questo agente (pid 135877), la 7447 e'
# l'innesto di B2, e le 7471-7475 sono dell'agente di B8, che sta lavorando
# adesso.  ⭐ Questo giro sta tutto dentro 7511-7515, ban `tmp/sera-ff-ban`,
# socket `tmp/sera-ff.sock`, certificati `tmp/sera-ff-cert`, registro
# `tmp/sera-ff-server.log`.  Nessun altro banco nomina nessuno dei cinque.
#
# ⛔ E IL BINARIO E' QUELLO DEL PRODOTTO: si cambia la PAGINA (`--pagina`), non
#    il server.  Quel che si misura e' il comportamento del browser contro il
#    protocollo che il prodotto parla davvero.
#
# ⛔ B0.7: MARCATORI, NON `sleep`.  «Il processo e' vivo» e «la porta risponde»
#    sono due fatti diversi, e alla misura serve il secondo.
set -uo pipefail

D=/srv/src/remotix
TMP=/srv/src/tmp
PORTA=${PORTA:-7511}
IND=${IND:-192.168.0.2}

PAGINA=$TMP/sera-ff-pagina.html
CERT=$TMP/sera-ff-cert
BAN=$TMP/sera-ff-ban
SOCK=$TMP/sera-ff.sock
LOG=$TMP/sera-ff-server.log
PIDF=$TMP/sera-ff-server.pid

mkdir -p "$TMP"

case "${1:-accendi}" in
spegni)
	if [ -f "$PIDF" ]; then
		pid=$(cat "$PIDF")
		# ⛔ Per PID e solo il proprio: `pkill -f remotix` porterebbe via anche
		#    il server della 7448 e quello di B8, che non sono di questo giro.
		kill "$pid" 2>/dev/null
		g=0
		while [ -d "/proc/$pid" ] && [ "$g" -lt 20 ]; do sleep 0.5; g=$((g+1)); done
		[ -d "/proc/$pid" ] && printf 'NO  il pid %s non e\x27 morto\n' "$pid" \
		                    || printf 'OK  spento (pid %s)\n' "$pid"
		rm -f "$PIDF"
	else
		printf -- '--  nessun %s: non c\x27era niente di mio acceso\n' "$PIDF"
	fi
	rm -f "$SOCK"
	exit 0 ;;
accendi) ;;
svuota-registro)
	# ⛔ Fra un giro e l'altro il registro si AZZERA, e si dichiara: contare due
	#    volte le righe del giro precedente e' il modo piu' facile di credere
	#    che due giri concordino.
	: > "$LOG"
	printf 'OK  registro azzerato: %s\n' "$LOG"
	exit 0 ;;
*) echo "uso: $0 [accendi|spegni|svuota-registro]"; exit 2 ;;
esac

command -v ss >/dev/null || { echo "NO  ⛔ «ss» non c'e': non ho guardato la porta, e non la chiamo libera"; exit 2; }
n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
if [ "$n" -ne 0 ]; then
	echo "NO  ⛔ la porta $PORTA e' gia' occupata ($n righe): non e' mia, non la tocco"
	ss -tuln | grep ":$PORTA\b"
	exit 2
fi
echo "OK  porta $PORTA libera (ss ha guardato e ha stampato $n righe su di lei)"

[ -x "$D/remotix" ] || { echo "NO  ⛔ $D/remotix non c'e' o non e' eseguibile"; exit 2; }

# ⛔ LA PAGINA STRUMENTATA DEVE ESSERCI, E DEVE ESSERE QUELLA STRUMENTATA.
#    Senza il `--pagina`, il server servirebbe `pagina.html` del prodotto e
#    questo banco misurerebbe una scena che non ha preparato — e il silenzio
#    delle tracce avrebbe la faccia del silenzio in prova.
[ -f "$PAGINA" ] || { echo "NO  ⛔ $PAGINA non c'e': la copia strumentata non e' arrivata"; exit 2; }
if ! grep -q 'FINE STRUMENTAZIONE' "$PAGINA"; then
	echo "NO  ⛔ $PAGINA non porta il marcatore della strumentazione: e' una copia"
	echo "    del prodotto e basta, e non tracerebbe niente."
	exit 2
fi
echo "--  pagina   : $PAGINA  ($(sha256sum "$PAGINA" | cut -c1-16)…, $(stat -c%s "$PAGINA") byte)"
echo "--  binario  : $(sha256sum "$D/remotix" | cut -c1-16)…  $(stat -c '%y' "$D/remotix")"

rm -f "$LOG" "$PIDF" "$SOCK" "$BAN" "$BAN.nuovo"
mkdir -p "$CERT"
nohup "$D/remotix" --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
      --certificati "$CERT" --pagina "$PAGINA" \
      --ban-file "$BAN" --comando-socket "$SOCK" --parlantina \
      > "$LOG" 2>&1 &
pid=$!
echo "$pid" > "$PIDF"

g=0
while [ "$g" -lt 60 ]; do
	[ -d "/proc/$pid" ] || break
	[ "$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")" -ge 2 ] && break
	sleep 0.5; g=$((g+1))
done
if [ ! -d "/proc/$pid" ]; then
	echo "NO  ⛔ il server e' morto subito.  Il registro dice:"
	sed 's/^/        /' "$LOG"
	exit 3
fi
righe=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
if [ "$righe" -lt 2 ]; then
	echo "NO  ⛔ il processo $pid e' vivo ma su :$PORTA ci sono $righe ascoltatori."
	echo "    §2.4 ne vuole DUE — UDP per RCP, TCP per la pagina — e questo giro"
	echo "    li usa tutt'e due: senza il TCP non arriva nemmeno una traccia."
	sed 's/^/        /' "$LOG"
	exit 3
fi
echo "OK  acceso, pid $pid, $righe ascoltatori su :$PORTA dopo $((g/2)) s d'attesa"
echo "--  registro: $LOG · ban: $BAN · socket: $SOCK"
