#!/bin/bash
# 04-b23-lancia.sh — ⛔ B23: il filo del canale di input (`RCP.md` §7.3).
#
#     bash banchi/04-b23-lancia.sh
#     bash banchi/04-b23-lancia.sh --senza-certificazione   (piu' svelto)
#
# ===========================================================================
# ⛔ L'ORDINE E' UNA MISURA, e va letto: prima si certifica il banco, poi lo si
#    crede.
#
#    `CODER.md` §3.3: «accerta che il banco sappia produrre il risultato atteso
#    PRIMA di puntarlo sull'incognita».  ⛔ E §3.4, che e' il rovescio piu'
#    insidioso perche' il banco e' verde: «un banco che NON riproduce non e' una
#    prova di correttezza».
#
#    ⇒ Qui il giro e' TRE cose in quest'ordine:
#      1. il GEMELLO combacia?  Senza, il costruttore si ferma per tutti e dieci
#         gli anelli, e non e' un problema di questo banco solo;
#      2. la CERTIFICAZIONE — dodici guasti innestati, uno per giro, e ciascuno
#         deve far diventare B23 rosso esattamente dove dichiarato;
#      3. e solo allora il giro vero.
#
# ===========================================================================
# ⚠ QUESTO BANCO NON APRE NESSUNA PORTA, e va detto perche' e' un'eccezione.
#
# Le porte 7621-7625 sono di A3 e restano libere: B23 gira **in processo**, e
# non c'e' niente da mettere in rete.  ⛔ La ragione e' dichiarata e non e' una
# comodita': `src/webtransport.c` oggi i byte del canale di input li SCARTA
# (`G_UNI_OK`, e la riga di registro lo dice), e quel file non e' di questo
# anello.  La cucitura si chiede al coordinatore — vedi
# `fasi/rapporti/F4-A3-filo-input.md`.
#
# ⚠ E siccome non apre porte, non fa scattare nessun ban di §4.4-bis e non ha
#   bisogno ne' di un `--ban-file` suo ne' di un `--comando-socket`: gli altri
#   nove anelli non se ne accorgono nemmeno.
set -u

QUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RADICE="$(cd "$QUI/.." && pwd)"
USCITA="${USCITA:-/tmp/b23}"
CERTIFICA=1
[ "${1:-}" = "--senza-certificazione" ] && CERTIFICA=0

VERDE=$'\033[32m'; ROSSO=$'\033[31m'; GRIGIO=$'\033[0m'
mkdir -p "$USCITA"
GUASTI=0

echo "== ⛔ 1. IL GEMELLO — `src/` e `banchi/rcp/` devono combaciare"
echo "      (il \`Makefile\`, variabile GEMELLATI, ferma la costruzione se no)"
for f in rcp.c rcp.h autenticazione.c; do
	if [ ! -f "$RADICE/banchi/rcp/$f" ]; then
		# ⛔ E i tre fatti sono TRE: «combaciano», «divergono», «non c'e'».  Il
		#    terzo con l'aria del primo e' un controllo spento che sembra acceso.
		echo "   ${ROSSO}⛔ banchi/rcp/$f NON C'E': non ho potuto guardare${GRIGIO}"
		GUASTI=$((GUASTI + 1))
	elif diff -q "$RADICE/src/$f" "$RADICE/banchi/rcp/$f" > /dev/null; then
		echo "   ${VERDE}✅${GRIGIO} $f"
	else
		echo "   ${ROSSO}⛔ $f DIVERGE:${GRIGIO}"
		diff -u "$RADICE/src/$f" "$RADICE/banchi/rcp/$f" | head -30
		GUASTI=$((GUASTI + 1))
	fi
done
if [ "$GUASTI" -ne 0 ]; then
	echo "   ${ROSSO}⛔ ci si ferma qui: un gemello mezzo ferma TUTTI gli anelli${GRIGIO}"
	exit 2
fi

if [ "$CERTIFICA" -eq 1 ]; then
	echo
	echo "== ⛔ 2. LA CERTIFICAZIONE — il banco sa vedere il difetto?"
	# ⛔ QUANTI SONO NON STA SCRITTO QUI: il numero lo stampa `04-b23-guasti.py`
	#    dal proprio catalogo.  ⚠ Qui c'era «dodici», ed erano gia' sedici — la
	#    forma esatta del rilievo R7.14: un numero scritto a mano e' il numero che
	#    nessuno ricalcola.
	echo "      ⚠ i guasti del catalogo, innestati in \`banchi/rcp/rcp.c\` uno per"
	echo "        giro e rimessi a posto in un \`finally\`.  Dura qualche minuto."
	python3 "$QUI/04-b23-guasti.py" --uscita "$USCITA" || GUASTI=$((GUASTI + 1))
	# ⛔ E si RIGUARDA il gemello: la certificazione scrive su quel file, e un
	#    ripristino mancato lo scopre questo controllo, non il prossimo che
	#    compila.
	diff -q "$RADICE/src/rcp.c" "$RADICE/banchi/rcp/rcp.c" > /dev/null || {
		echo "   ${ROSSO}⛔⛔ il gemello NON e' tornato a posto dopo la certificazione${GRIGIO}"
		GUASTI=$((GUASTI + 1))
	}
else
	echo
	echo "== ⚠ 2. CERTIFICAZIONE SALTATA (--senza-certificazione)"
	echo "      ⛔ Il verde che segue vale meno: nessuno ha verificato che questo"
	echo "        banco sappia diventare rosso.  Non si chiude una fase cosi'."
fi

echo
echo "== ⭐ 3. IL GIRO VERO"
python3 "$QUI/04-b23-filo-input.py" --uscita "$USCITA" || GUASTI=$((GUASTI + 1))

echo
if [ "$GUASTI" -ne 0 ]; then
	echo "   ${ROSSO}⛔ B23 NON passa${GRIGIO}"
	exit 1
fi
echo "   ${VERDE}⭐ B23 passa, ed e' certificato${GRIGIO}"
echo "   la traccia e il verdetto: $USCITA"
exit 0
