#!/bin/bash
#
# 04-b25-lancia.sh — il banco della tastiera, e LA SUA CERTIFICAZIONE.
#
# ⛔ Due lavori, e il secondo viene prima nell'ordine di fiducia:
#
#   1. compila `src/tastiera.c` insieme al banco e lo esegue;
#   2. ⛔ compila il banco contro TRE implementazioni sbagliate di proposito
#      (`04-b25-guasti.c`) e PRETENDE che dica ROSSO su ciascuna, e ROSSO SULLA
#      PROVA GIUSTA.  Un banco che non ha mai visto il difetto non e' una prova
#      (`CODER.md` §3.3, §3.4, §4.6).
#
# ⚠ Non serve ne' una sessione, ne' un compositore, ne' `libei`, ne' una porta:
#   il modulo e' una funzione pura e si prova isolata (`CODER.md` §3.6).  Gira
#   uguale sulla macchina di sviluppo e nel contenitore della macchina di prova.
#
#   uso:  bash banchi/04-b25-lancia.sh          (dalla radice del deposito)
#
set -u

QUI="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$QUI" || exit 2
FUORI="${FUORI:-/tmp/04-b25-$$}"
mkdir -p "$FUORI" || exit 2

CC="${CC:-cc}"
CFLAGS="-O1 -g -Wall -Wextra -Werror=implicit-function-declaration"
XKB_CFLAGS="$(pkg-config --cflags xkbcommon 2>/dev/null)"
XKB_LIBS="$(pkg-config --libs xkbcommon 2>/dev/null)"

if [ -z "$XKB_LIBS" ]; then
	echo "⛔ xkbcommon non c'e' (pkg-config): il banco non puo' misurare niente."
	echo "   Debian/Trixie: apt install libxkbcommon-dev"
	exit 2
fi

echo "== xkbcommon $(pkg-config --modversion xkbcommon)  ·  $(uname -n)  ·  $(date -Is)"

# ---------------------------------------------------------------------------
# 1. IL PRODOTTO
# ---------------------------------------------------------------------------
echo
echo "———— 1. IL PRODOTTO — src/tastiera.c ————"
# shellcheck disable=SC2086
$CC $CFLAGS $XKB_CFLAGS -o "$FUORI/banco" \
	banchi/04-b25-tastiera.c src/tastiera.c src/registro.c $XKB_LIBS || {
	echo "⛔ il prodotto non compila"
	exit 2
}

"$FUORI/banco" banchi/04-b25-esiti.jsonl
PRODOTTO=$?

# ---------------------------------------------------------------------------
# 2. LA CERTIFICAZIONE — il banco deve saper dire ROSSO
# ---------------------------------------------------------------------------
echo
echo "———— 2. LA CERTIFICAZIONE — quattro difetti messi apposta ————"
echo "     (se una di queste righe dicesse VERDE, il banco non proverebbe niente)"
echo

# guasto → un pezzo della riga «prova» che DEVE risultare rossa
declare -A ATTESA=(
	[1]='U+00E9) su «us»'
	[2]='U+00E9) su «it»'
	[3]='zz_non_esiste'
	[4]='sessione «it» + negoziata «us»'
)
declare -A COSA=(
	[1]='manda la «e» al posto della «é»'
	[2]='dimentica i modificatori'
	[3]='ripiega su «us» in silenzio'
	[4]='si fida del nome negoziato, non della keymap della sessione'
)

CERTIFICATO=0
for G in 1 2 3 4; do
	# shellcheck disable=SC2086
	$CC $CFLAGS -DGUASTO=$G $XKB_CFLAGS -o "$FUORI/guasto$G" \
		banchi/04-b25-tastiera.c banchi/04-b25-guasti.c $XKB_LIBS 2>"$FUORI/cc$G.txt" || {
		echo "⛔ il guasto $G non compila:"
		sed 's/^/     /' "$FUORI/cc$G.txt"
		CERTIFICATO=1
		continue
	}

	"$FUORI/guasto$G" "$FUORI/esiti-guasto$G.jsonl" >"$FUORI/uscita$G.txt" 2>&1
	USCITA=$?

	# ⛔ Non basta «ha detto rosso»: deve aver detto rosso SULLA PROVA GIUSTA.
	#    Un banco che va rosso per un motivo qualunque non ha visto il difetto.
	RIGA=$(grep -F "${ATTESA[$G]}" "$FUORI/esiti-guasto$G.jsonl" 2>/dev/null | grep -c '"esito":"rosso"')

	if [ "$USCITA" -eq 1 ] && [ "$RIGA" -ge 1 ]; then
		printf '  ✅ guasto %d (%s) ⇒ il banco dice ROSSO, e sulla prova giusta\n' "$G" "${COSA[$G]}"
		grep -F "${ATTESA[$G]}" "$FUORI/esiti-guasto$G.jsonl" |
			grep '"esito":"rosso"' | head -1 | sed 's/^/       /'
	else
		printf '  ⛔ guasto %d (%s) NON e'"'"' stato visto: uscita=%d, righe rosse attese=%d\n' \
			"$G" "${COSA[$G]}" "$USCITA" "$RIGA"
		echo "     ⇒ IL BANCO NON E' CERTIFICATO: il suo verde non vale niente."
		sed 's/^/       /' "$FUORI/uscita$G.txt" | tail -30
		CERTIFICATO=1
	fi
done

# ---------------------------------------------------------------------------
echo
echo "———— L'ESITO ————"
if [ "$CERTIFICATO" -ne 0 ]; then
	echo "⛔ IL BANCO NON E' CERTIFICATO — non si crede al suo verde (CODER.md §3.3)."
	echo "   i file: $FUORI"
	exit 2
fi
echo "✅ il banco e' CERTIFICATO: ha visto tutt'e quattro i difetti, ciascuno sulla sua prova."
if [ "$PRODOTTO" -eq 0 ]; then
	echo "✅ e src/tastiera.c passa: banchi/04-b25-esiti.jsonl"
	rm -rf "$FUORI"
	exit 0
fi
echo "⛔ ma src/tastiera.c NON passa (uscita $PRODOTTO): banchi/04-b25-esiti.jsonl"
echo "   i file del giro: $FUORI"
exit 1
