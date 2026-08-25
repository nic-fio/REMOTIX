#!/usr/bin/env bash
# ===========================================================================
# 10-d1-taratura — ⛔⭐ IL METRO SI TARA PRIMA (`LEZIONI.md` §1.33).
#
# ⛔ IL PROBLEMA.  L'aritmetica del budget e' scritta **due volte**: in
#    `banchi/10-b99-predittore.py` — certificato, 86 casi, 0 rossi, ed e' da li'
#    che vengono i numeri di §6.9 — e in `src/budget.c`, che e' il prodotto.
#    ⛔ Due copie della stessa regola in due linguaggi sono due numeri che
#    possono divergere, e divergerebbero **in silenzio**: sul campo si vedrebbe
#    solo «e' entrato uno di piu'», che nessuno collega a un'aritmetica.
#
# ⇒ Qui si fanno girare **le stesse scene** nei due, e si CONFRONTANO i
#   verdetti.  ⚠ Il C non viene riscritto: si monta `src/budget.c` com'e'
#   (`banchi/10-d1-conto.c` e' solo il pilota).
#
# ⭐⭐ E LE SCENE NON SONO INVENTATE: sono i casi di §6.9, quelli su cui il
#     predittore dichiara `[M]` **0 falsi si' e 0 falsi no**, piu' i due
#     estremi della manopola (`--riserva 0` = «consegnato», `1` = «peggiore»).
#
# ⛔ E NON SOSTITUISCE LA MISURA: qui non c'e' nessuna GPU e nessun desktop.
#    Questo dice *«il conto e' quello che credo»*; se la macchina regga davvero
#    quel conto lo dice `10-d1-lancia.sh`, e sono due domande diverse.
#
# Uso:  bash banchi/10-d1-taratura.sh
#       Esce 0 se tutte le scene combaciano, 1 se una diverge, 2 se non ho
#       potuto confrontare (che NON e' un verde).
# ===========================================================================
set -uo pipefail
QUI=$(cd "$(dirname "$0")/.." && pwd)
FUORI=${FUORI:-/tmp/10-d1}
mkdir -p "$FUORI"
CONTO="$FUORI/conto"

log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
dub() { printf '    \033[1;33m??\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

log "1 · Monto src/budget.c COM'E' — nessuna copia, nessuna riscrittura"
if ! cc -std=gnu11 -D_GNU_SOURCE -Wall -Wextra -Wno-unused-parameter \
     -I"$QUI/src" -o "$CONTO" "$QUI/banchi/10-d1-conto.c" "$QUI/src/budget.c"; then
	ko "⛔ non compila: NON confronto (e non e' «combaciano»)"
	exit 2
fi
ok "montato: $CONTO"
inf "md5 di src/budget.c: $(md5sum "$QUI/src/budget.c" | cut -d' ' -f1)"

# ⛔ La capacita' e il ritmo massimo del ferro — `[M]` §6.9, e sono gli STESSI
#    numeri dei due lati: se qui e in `budget.h` divergessero, il confronto
#    misurerebbe la divergenza dei numeri invece che quella delle regole.
CAP=479.8
FPSMAX=39.54
inf "capacita' $CAP Mpixel/s · ritmo max $FPSMAX fot/s — [M] §6.9, i5-13500T · UHD 730"

# ── Le scene: nome | dentro | FOT/S consegnati (0 = FERMA) | ritardo ms | riserva
#
# ⛔ La colonna e' in FOTOGRAMMI al secondo, non in Mpixel/s: e' quel che il
#    padre conta davvero, e i Mpixel/s li ricava lui moltiplicando per la tela.
#    ⚠ Confondere le due colonne fa combaciare i due lati su un ingresso
#      sbagliato — cioe' un verde che non dice niente.  E' successo alla prima
#      stesura di questo file, ed e' scritto qui perche' non risucceda.
#
# ⭐ E i numeri vengono da `10-b99-misure.jsonl`, scena `satura`, divisi per il
#    numero di sessioni del gradino e poi per 2,0736 Mpixel (una 1080p):
#      gradino 5 → 394,8/5 = 78,96 Mpixel/s = 38,08 fot/s   (la sesta ENTRA)
#      gradino 6 → 479,8/6 = 79,97 Mpixel/s = 38,57 fot/s   (la settima NO)
#      gradino 8 →  26,6/8 =  3,33 Mpixel/s =  1,60 fot/s   (il conto MENTE)
SCENE="
sei-sature-la-sesta-entra|5|38.08|9.8|0.5
sette-sature-la-settima-no|6|38.57|13.1|0.5
otto-strozzate-il-conto-mente|8|1.60|654.3|0.5
dieci-ferme-la-decima-entra|9|0|9.8|0.5
undici-ferme-l-undicesima-no|10|0|9.8|0.5
quaranta-ferme-riserva-zero|40|0|9.8|0.0
quaranta-ferme-riserva-uno|40|0|9.8|1.0
cinque-ferme-riserva-uno|5|0|9.8|1.0
"

GUAI=0; VISTE=0; MUTE=0
log "2 · LE SCENE — stessa domanda ai due, e si confrontano i VERDETTI"
printf '    %-34s %-10s %-10s %s\n' scena predittore prodotto esito
while IFS='|' read -r nome dentro fps rit ris; do
	[ -z "${nome:-}" ] && continue
	VISTE=$((VISTE+1))

	# ── il predittore (Python), che e' la copia certificata ───────────────
	PRED=$(FRAZIONE_RISERVA="$ris" python3 - "$QUI" "$dentro" "$fps" "$rit" "$ris" "$CAP" "$FPSMAX" <<'PY' 2>/dev/null
import importlib.util, sys
qui, dentro, fps, rit, ris, cap_v, fpsmax = sys.argv[1:8]
spec = importlib.util.spec_from_file_location("p", qui + "/banchi/10-b99-predittore.py")
m = importlib.util.module_from_spec(spec); sys.modules["p"] = m
spec.loader.exec_module(m)
cap = m.Capacita(mpixel_s=float(cap_v), ritmo_max_fps=float(fpsmax),
                 ferro=m.FERRO, catena=m.CATENA_DESKTOP, scena="satura",
                 misurata_da="10-d1-taratura", tele_provate=["1920x1080"],
                 soffitto_visto=True, ritardo_affanno_ms=22.9)
mp = 1920 * 1080 / 1e6 * float(fps)
dentro_l = [m.Sessione("d%d" % i, 1920, 1080, mpixel_s=mp,
                       ritardo_ms=float(rit)) for i in range(int(dentro))]
v = m.prevedi(dentro_l, m.Sessione("nuovo", 1920, 1080), cap,
              m.REGOLA_RISERVA, frazione=float(ris))
print(v.esito.replace(" ", "-"))
PY
)
	# ── il prodotto (C), che e' `src/budget.c` montato com'e' ────────────
	if [ "$fps" = "0" ]; then
		PROD=$("$CONTO" --capacita "$CAP" --riserva "$ris" --dentro "$dentro" \
			--ritardo-ms "$rit" 2>/dev/null | awk '{print $2}')
	else
		PROD=$("$CONTO" --capacita "$CAP" --riserva "$ris" --dentro "$dentro" \
			--fps "$fps" --ritardo-ms "$rit" 2>/dev/null | awk '{print $2}')
	fi

	# ⛔ «Non ho letto» non e' «combaciano»: si dichiara e si conta a parte.
	if [ -z "${PRED:-}" ] || [ -z "${PROD:-}" ]; then
		printf '    %-34s %-10s %-10s ' "$nome" "${PRED:-??}" "${PROD:-??}"
		dub "non ho potuto confrontare"
		MUTE=$((MUTE+1))
		continue
	fi
	if [ "$PRED" = "$PROD" ]; then
		printf '    %-34s %-10s %-10s \033[1;32mcombaciano\033[0m\n' "$nome" "$PRED" "$PROD"
	else
		printf '    %-34s %-10s %-10s \033[1;31m⛔ DIVERGONO\033[0m\n' "$nome" "$PRED" "$PROD"
		GUAI=$((GUAI+1))
	fi
done <<EOF
$SCENE
EOF

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ 3 · IL CONTROLLO NEGATIVO — «il confronto sa dare rosso?»
# ═══════════════════════════════════════════════════════════════════════════
#
# Un confronto che dicesse «combaciano» su qualunque cosa non e' un confronto.
# ⇒ Si chiede al prodotto la stessa scena con la manopola SPOSTATA, e i due
#   verdetti DEVONO essere diversi: se non lo sono, la manopola non e' in
#   vigore, e allora nemmeno il resto di questa tabella vuol dire niente.
log "3 · ⛔ IL CONTROLLO NEGATIVO — la manopola dev'essere davvero in vigore"
A=$("$CONTO" --capacita "$CAP" --riserva 0.0 --dentro 40 --ritardo-ms 9.8 2>/dev/null | awk '{print $2}')
B=$("$CONTO" --capacita "$CAP" --riserva 1.0 --dentro 40 --ritardo-ms 9.8 2>/dev/null | awk '{print $2}')
inf "quaranta ferme: riserva 0 ⇒ «$A» · riserva 1 ⇒ «$B»"
if [ "$A" = REGGE ] && [ "$B" = NON-REGGE ]; then
	ok "⭐ la manopola morde nei due versi: 0 = «consegnato», 1 = «peggiore»"
else
	ko "⛔ la manopola NON morde: il resto della tabella non vuol dire niente"
	GUAI=$((GUAI+1))
fi
# ⭐ E il secondo: col budget SPENTO non si nega mai — e' il prodotto di ieri.
S=$("$CONTO" --capacita 0 --dentro 40 --ritardo-ms 900 2>/dev/null | awk '{print $2}')
inf "budget SPENTO, quaranta sessioni strozzate a 900 ms ⇒ «$S»"
if [ "$S" = REGGE ]; then
	ok "⭐ spento non nega mai — ed e' il difetto che il budget esiste per curare"
else
	ko "⛔ spento ha negato: I6 e' rotta, il budget non nasce piu' spento"
	GUAI=$((GUAI+1))
fi

log "IL VERDETTO"
inf "$VISTE scene · $GUAI divergenze · $MUTE non confrontate"
if [ "$MUTE" != 0 ]; then
	dub "⛔ «non ho potuto confrontare» NON e' un verde"
	exit 2
fi
if [ "$GUAI" != 0 ]; then
	ko "⛔ le due copie dell'aritmetica DIVERGONO"
	exit 1
fi
ok "⭐ src/budget.c e 10-b99-predittore.py danno lo stesso verdetto su tutte le scene"
exit 0
