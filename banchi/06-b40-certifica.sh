#!/bin/bash
#
# 06-b40-certifica.sh — ⛔ QUESTO BANCO SA VEDERE IL DIFETTO CHE CERCA?
#
#   VENV=... CERTIFICATI=... bash banchi/06-b40-certifica.sh
#
#   uscita 0  il guasto innestato fa cambiare colore ai casi dichiarati, e
#             SOLO a quelli
#   uscita 1  ⛔ no — e allora `06-b40-lancia.sh` non e' uno strumento
#   uscita 2  non si e' potuto far girare
#
# ---------------------------------------------------------------------------
# ⛔ IL GUASTO, E PERCHE' E' PROPRIO QUESTO
#
# `LEZIONI.md` §1.9: uno strumento che non ha mai trovato niente non e' uno
# strumento pulito, e' uno strumento non certificato.  ⇒ Qui si rimette in una
# **copia** di `01-b3-cliente.py` il comportamento che aveva fino al 21 agosto
# 2026 — *«i byte del server si registrano quando qualcuno li tira fuori dalla
# coda»* — e si guarda quali casi diventano verdi.
#
# ⭐ E il guasto non e' inventato per l'occasione: **era il codice vero**, ed e'
#    stato trovato proprio da questo banco.  I tre casi che deve far sparire:
#
#     6-tela-non-sollecitata   T1  §7.1
#     9-tela-dopo-vista        V3  §7.1
#    10-tela-in-piu            T2  §6.2
#
# ⛔ E gli altri sette devono restare **come sono**: un guasto che cambia tutto
#    non dice dove sta il difetto, dice solo che qualcosa si e' rotto.
set -uo pipefail

QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VENV=${VENV:?serve VENV=/percorso/dell/ambiente-virtuale (con aioquic)}
CERTIFICATI=${CERTIFICATI:?serve CERTIFICATI=/percorso/dei/certificati}
COPIA=${COPIA:-/tmp/06-b40-copia}
PORTA=${PORTA:-7744}

log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

log "1. Una COPIA dell'albero dei banchi, e il guasto solo li' dentro"
rm -rf "$COPIA"
mkdir -p "$COPIA" || exit 2
for f in 01-b3-cliente.py 01-b4-validatore.py 06-b40-specchio.py 06-b40-lancia.sh; do
	cp "$QUI/$f" "$COPIA/$f" || exit 2
done
inf "copia in $COPIA   (⛔ l'albero vero non si tocca)"

"$VENV/bin/python" - "$COPIA/01-b3-cliente.py" <<'PYTHON'
import sys
p = sys.argv[1]
s = open(p).read()
a = "            if self.reg is not None:\n                self.reg.aggiungi(SERVER, grezzo)"
b = '    if quale and nome != quale:\n        if nome == "CONGEDO":'
c = "        # ⭐ (registrato all'arrivo da `Cliente._sfoglia()`, non qui)\n        nome = NOME.get(tipo"
# ⛔ L'ANCORA SI VERIFICA, e la sua assenza e' un GUASTO DEL CERTIFICATORE, non
#    un verde: e' la lezione di `04-b31` (G8, l'ancora scaduta il 16 agosto —
#    il guasto piu' grave non si innestava piu' e il banco taceva).
for nome, anc in (("A", a), ("B", b), ("C", c)):
    if anc not in s:
        print(f"?? ancora {nome} NON TROVATA: il guasto non si innesta")
        sys.exit(3)
s = s.replace(a, "            if False:\n                self.reg.aggiungi(SERVER, grezzo)", 1)
s = s.replace(b, "    if reg is not None:\n        reg.aggiungi(SERVER, grezzo)\n" + b, 1)
s = s.replace(c, "        reg.aggiungi(SERVER, grezzo)\n        nome = NOME.get(tipo", 1)
open(p, "w").write(s)
print("guasto innestato: si registra al CONSUMO, com'era prima del 21 agosto 2026")
PYTHON
E=$?
[ "$E" -eq 0 ] || { ko "il guasto non si e' innestato (uscita $E)"; exit 2; }
ok "guasto innestato nella copia"

log "2. Il banco, sull'albero SANO"
VENV="$VENV" CERTIFICATI="$CERTIFICATI" PORTA="$PORTA" \
    LAV="$COPIA/lav-sano" bash "$QUI/06-b40-lancia.sh" > "$COPIA/sano.txt" 2>&1
S=$?
grep -E 'casi con' "$COPIA/sano.txt" | sed 's/^/    /'

log "3. Il banco, sull'albero col GUASTO"
VENV="$VENV" CERTIFICATI="$CERTIFICATI" PORTA="$PORTA" \
    LAV="$COPIA/lav-guasto" bash "$COPIA/06-b40-lancia.sh" > "$COPIA/guasto.txt" 2>&1
G=$?
grep -E 'casi con' "$COPIA/guasto.txt" | sed 's/^/    /'

log "4. Il confronto — ⛔ l'atteso e' scritto qui sopra, non dedotto adesso"
inf "sano: uscita $S (atteso 0)   ·   col guasto: uscita $G (atteso 1)"
BENE=0
[ "$S" -eq 0 ] || { ko "⛔ l'albero SANO non e' verde: non si certifica niente"; BENE=1; }
[ "$G" -eq 1 ] || { ko "⛔ il guasto NON fa fallire il banco: il banco non lo vede"; BENE=1; }

for c in 6-tela-non-sollecitata 9-tela-dopo-vista 10-tela-in-piu; do
	# ⛔ «diventa verde» si legge sulla riga del VERDETTO di quel caso, non sul
	#    colore complessivo: `arbitro 0 (atteso 1)` vuol dire che l'arbitro non
	#    ha piu' niente da accusare, cioe' che il guasto ha tolto i byte dalla
	#    traccia.  ⚠ E si estrae la sezione del caso, o si leggerebbe il
	#    verdetto di un altro.
	if awk -v c="$c" '
	       index($0, "== " c) {v = 1; next}
	       v && /^\033\[1m== / {exit}
	       v {print}' "$COPIA/guasto.txt" | grep -q 'arbitro 0 (atteso 1)'; then
		ok "«$c» col guasto diventa VERDE — il banco lo perde, come dichiarato"
	else
		ko "⛔ «$c» col guasto NON diventa verde: il caso non prova quel che dice"
		BENE=1
	fi
done

log "Esito"
if [ "$BENE" -eq 0 ]; then
	ok "⭐ il banco sa vedere il difetto che cerca — ed e' un difetto VERO,"
	ok "   quello che il cliente aveva fino al 21 agosto 2026"
else
	ko "⛔ non certificato"
fi
exit "$BENE"
