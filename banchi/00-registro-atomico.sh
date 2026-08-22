#!/usr/bin/env bash
#
# 00-registro-atomico — IL REGISTRO NON SI DEVE INTRECCIARE SOTTO CARICO.
#
# ⛔ PERCHE' ESISTE, ed e' un debito pagato in ritardo.
#
#    Il 21 agosto 2026 `src/registro.c` componeva ogni riga con TRE chiamate
#    su uno `stderr` non bufferizzato.  Padre e figlio appendono allo STESSO
#    file: quando le scritture si accavallano, un corpo finisce dopo l'a-capo
#    altrui e nasce una riga SENZA MARCA TEMPORALE.
#    `[M]` su un registro vero da 3,0 MB: 23 righe orfane su 28 035, e 3 su 80
#    delle «tela CHIESTA al produttore» — il 3,8 % di una famiglia su cui un
#    attrezzo contava.  Il sintomo era un attrezzo di banco che moriva con
#    `ValueError`, e per arrivarci ci e' voluto un giro di banco.
#
# ⛔⛔ E LA RAGIONE PER CUI QUESTO FILE NASCE OGGI E NON ALLORA: la cura fu
#     provata con un programmino usa-e-getta, e il programmino fu buttato.
#     ⇒ `banchi/00-ancore.py` (22 agosto) ha poi misurato che **nessun
#     innestatore nomina `registro.c`**: la funzione curata non aveva, e non
#     aveva mai avuto, NESSUN controllo positivo.  Una cura provata una volta
#     e mai piu' e' una cura che nessuno difende.
#
# ⭐ Il registro e' lo strumento di diagnosi principale del progetto
#    (`LEZIONI.md` §2.7 e §1.21): se mente sotto carico, mente proprio quando
#    serve — e a macchina ferma non si riproduce.
#
# Uso:  bash banchi/00-registro-atomico.sh [--figli 6] [--righe 800]
#
#   Uscita 0 = zero righe nostre spezzate E il guasto innestato le produce.
#   Uscita 1 = il prodotto si intreccia.
#   Uscita 2 = ⛔ IL BANCO E' CIECO: col guasto dentro non ha visto niente,
#              quindi il suo verde non vale.  (E' il caso che conta.)
set -u
QUI=$(cd "$(dirname "$0")/.." && pwd)
LAV=$(mktemp -d); trap 'rm -rf "$LAV"' EXIT
FIGLI=6; RIGHE=800
while [ $# -gt 0 ]; do
	case "$1" in
	--figli) FIGLI=$2; shift 2 ;;
	--righe) RIGHE=$2; shift 2 ;;
	*) echo "⛔ argomento ignoto: $1" >&2; exit 2 ;;
	esac
done

# ── il testimone: N processi che appendono allo STESSO registro ─────────────
cat > "$LAV/prova.c" <<'EOF'
#include "registro.h"
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>
int main(int argc, char **argv)
{
	int figli = atoi(argv[1]), righe = atoi(argv[2]);
	for (int f = 0; f < figli; f++)
		if (fork() == 0) {
			for (int i = 0; i < righe; i++)
				registro_dice("prova",
				  "figlio %d riga %d — tela CHIESTA al produttore 2560x1440, e "
				  "un corpo lungo abbastanza da far litigare le write fra loro",
				  f, i);
			_exit(0);
		}
	for (int f = 0; f < figli; f++) wait(NULL);
	return 0;
}
EOF

# ⛔ IL GUASTO: si rimette la forma di PRIMA — tre chiamate su stderr non
#    bufferizzato — in una COPIA.  ⚠ Non e' un guasto inventato: e' il codice
#    che c'era, e il banco deve saperlo accusare.
cat > "$LAV/guasto.c" <<'EOF'
#include "registro.h"
#include <stdarg.h>
#include <stdio.h>
#include <time.h>
static bool parlantina;
void registro_parlantina(bool a) { parlantina = a; }
bool registro_parla_molto(void) { return parlantina; }
uint64_t registro_ora_ms(void)
{
	struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
	return (uint64_t)ts.tv_sec * 1000u + (uint64_t)(ts.tv_nsec / 1000000);
}
static void riga(const char *area, const char *fmt, va_list ap)
{
	struct timespec ts; struct tm tm; char quando[32];
	clock_gettime(CLOCK_REALTIME, &ts); localtime_r(&ts.tv_sec, &tm);
	strftime(quando, sizeof quando, "%H:%M:%S", &tm);
	fprintf(stderr, "%s.%03ld %-7s ", quando, ts.tv_nsec / 1000000, area);
	vfprintf(stderr, fmt, ap);
	fputc('\n', stderr);
	fflush(stderr);
}
void registro_dice(const char *area, const char *fmt, ...)
{ va_list ap; va_start(ap, fmt); riga(area, fmt, ap); va_end(ap); }
void registro_dettaglio(const char *area, const char *fmt, ...)
{ va_list ap; if (!parlantina) return; va_start(ap, fmt); riga(area, fmt, ap); va_end(ap); }
EOF

giro() { # $1 = sorgente di registro   $2 = etichetta
	gcc -O2 -I "$QUI/src" -o "$LAV/p" "$LAV/prova.c" "$1" 2>"$LAV/cc.txt" || {
		echo "⛔ non compila ($2):"; cat "$LAV/cc.txt"; exit 2; }
	"$LAV/p" "$FIGLI" "$RIGHE" 2> "$LAV/$2.log"
	local tot orf fam
	tot=$(wc -l < "$LAV/$2.log")
	# ⛔ «orfana» = riga senza marca temporale in testa.  E si conta anche la
	#    FAMIGLIA su cui un attrezzo conterebbe: e' il numero che sposta una
	#    diagnosi, non il totale.
	orf=$(grep -cvE '^[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3} ' "$LAV/$2.log" || true)
	fam=$(grep -c 'tela CHIESTA al produttore' "$LAV/$2.log" || true)
	echo "$tot $orf $fam"
}

ATTESE=$((FIGLI * RIGHE))
echo "⏳ $FIGLI processi × $RIGHE righe = $ATTESE righe attese, sullo stesso registro"

read -r T1 O1 F1 <<<"$(giro "$QUI/src/registro.c" sano)"
echo "   prodotto:   $T1 righe · orfane $O1 · «tela CHIESTA» $F1/$ATTESE"
read -r T2 O2 F2 <<<"$(giro "$LAV/guasto.c" guasto)"
echo "   col guasto: $T2 righe · orfane $O2 · «tela CHIESTA» $F2/$ATTESE"

# ⛔ PRIMA il controllo positivo: un banco che non sa diventare rosso non e'
#    un banco, e questo e' l'unico modo di saperlo.
if [ "$O2" -eq 0 ] && [ "$F2" -eq "$ATTESE" ]; then
	echo "⛔⛔ IL BANCO E' CIECO: col guasto dentro non ha visto NIENTE."
	echo "    ⇒ Il verde del prodotto non vale.  Alza --figli o --righe."
	exit 2
fi
echo "   ⭐ il guasto si vede: $O2 righe orfane e $((ATTESE - F2)) righe di famiglia perdute"

if [ "$O1" -ne 0 ] || [ "$F1" -ne "$ATTESE" ]; then
	echo "⛔ IL PRODOTTO SI INTRECCIA: $O1 orfane, e la famiglia conta $F1 invece di $ATTESE"
	exit 1
fi
echo "⭐ VERDE — zero righe spezzate, e la famiglia conta tutte e $ATTESE"
