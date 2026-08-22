#!/bin/bash
#
# 06-b37-guasti.sh — ⛔⛔⭐ IL CERTIFICATORE DELLA SOTTOFASE 6.5.
#
#   bash banchi/06-b37-guasti.sh                 tutti i guasti, su chrome
#   bash banchi/06-b37-guasti.sh firefox         idem, su firefox
#   bash banchi/06-b37-guasti.sh chrome G1 G4    solo due guasti
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ CHE COSA CERTIFICA, E CHE COSA NO.
#
#   Per ogni guasto di `06-b37-guasti.py` questo script fa DUE giri della stessa
#   scena, e li pretende TUTT'E DUE:
#
#     1. il giro **SANO** — la scena sul prodotto — deve uscire **VERDE**;
#     2. il giro **GUASTO** — la stessa scena su una COPIA con il guasto dentro
#        — deve uscire **ROSSO**, ⛔ e deve stampare **la frase dichiarata prima**.
#
# ⛔ E LA SECONDA META' DELLA SECONDA CONDIZIONE E' TUTTO IL PUNTO.  Un giro che
#    diventa rosso *per qualunque motivo* non certifica niente: il browser che
#    non si apre, la finestra che non si stringe, il raccoglitore che muore
#    danno tutti un rosso.  ⇒ Si pretende che nel testo compaia la riga del caso
#    DICHIARATO.  E' il rilievo 2 della revisione del 21 agosto: `06-b33`
#    confrontava un'APPARTENENZA invece di un'uguaglianza, e un giro
#    completamente fallito confermava OGNI guasto.
#
# ⛔ E il giro SANO non e' una formalita': senza, un banco rotto che dice rosso
#    sempre passerebbe per un banco che sa vedere.
#
# ⚠ Quel che questo certificatore NON dice: che il prodotto sia giusto.  Dice
#   che il BANCO sa diventare rosso nel caso che dichiara — `REVIEWER.md` §1
#   punto 3, e `LEZIONI.md` §1.3.
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
RADICE=$(cd "$QUI/.." && pwd)

MOTORE=${1:-chrome}
shift 2>/dev/null || true
QUALI=${*:-}

PORTA=${PORTA:-7761}
SCHERMO=${SCHERMO:-:761}
ESITI=${ESITI:-$QUI/06-b37-esiti-guasti.jsonl}
# ⛔ I registri dei giri NON si cancellano: quando un guasto non conferma, la
#    prima cosa che serve e' il testo del giro, e un `trap rm -rf` lo porta via
#    proprio quando ce n'e' bisogno.
LAVORO=$(mktemp -d -t 06-b37-guasti-XXXXXX)

log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf -- '    --  %s\n' "$*"; }

log "0. Le ancore, verificate materialmente sul sorgente di oggi"
python3 "$QUI/06-b37-guasti.py" --ancore "$RADICE/src/pagina.html" \
	|| { ko "un'ancora e' scaduta: NON si certifica niente"; exit 2; }

# ⛔⭐ I CASI SI LEGGONO DA `06-b37-guasti.py`, E STANNO IN UN POSTO SOLO.
#    Ogni riga: guasto · scena · fattore · frase attesa.
# ⚠ Qui c'era una copia dell'elenco: due autorita' sullo stesso dato (la forma
#   E2), e la copia era gia' divergente — dichiarava G3 su `numeri` mentre il
#   guasto lo dichiara su `sfora`.  ⇒ Il certificatore avrebbe preteso una
#   frase che il guasto non promette piu'.
# ⛔ E la frase porta il «NO  » davanti apposta dove serve: `A6:` da solo
#    comparirebbe anche nella riga VERDE «OK  A6: …» — cioe' il certificatore si
#    sarebbe dato ragione da solo su un giro rosso per tutt'altro motivo.
mapfile -t CASI < <(python3 "$QUI/06-b37-guasti.py" --casi)
[ "${#CASI[@]}" -gt 0 ] || { ko "nessun caso dichiarato da 06-b37-guasti.py"; exit 2; }
inf "${#CASI[@]} casi dichiarati da 06-b37-guasti.py"

# gira <sorgente> <scena> <fattore> <guasto> <file-uscita>
gira()
{
	local sorgente=$1 scena=$2 fattore=$3 guasto=$4 uscita=$5
	SORGENTE="$sorgente" FATTORE="$fattore" PORTA="$PORTA" SCHERMO="$SCHERMO" \
		ESITI="$ESITI" B37_GUASTO="$guasto" \
		PIXEL_DIR="${PIXEL_DIR:-/tmp/06-b37-pixel}" \
		bash "$QUI/06-b37-lancia.sh" "$MOTORE" "$scena" >"$uscita" 2>&1
	return $?
}

SANI=()          # scena|fattore gia' misurati sani, per non rifarli
sano_visto()
{
	local chiave=$1 v
	for v in "${SANI[@]:-}"; do [ "$v" = "$chiave" ] && return 0; done
	return 1
}

CONFERMATI=0
FALLITI=0
RIGHE=()

for caso in "${CASI[@]}"; do
	IFS='|' read -r G SCENA FATT FRASE <<<"$caso"
	SCENA=$(echo "$SCENA" | tr -d ' ')
	FATT=$(echo "$FATT" | tr -d ' ')
	CHIAVE="$SCENA|$FATT"
	if [ -n "$QUALI" ] && [[ " $QUALI " != *" $G "* ]]; then continue; fi

	log "$G · scena «$SCENA»${FATT:+ · fattore $FATT} — deve dire: «$FRASE»"

	# --- 1. il giro SANO, e si fa una volta sola per scena+fattore ----------
	if sano_visto "$CHIAVE"; then
		inf "il giro sano di «$SCENA${FATT:+ @$FATT}» e' gia' stato fatto: verde"
	else
		S=$LAVORO/sano-$SCENA$FATT.log
		gira "$RADICE/src/pagina.html" "$SCENA" "$FATT" "nessuno" "$S"
		E=$?
		if [ "$E" -ne 0 ]; then
			ko "⛔ IL GIRO SANO E' ROSSO (esito $E): il guasto non si puo'"
			ko "   certificare, perche' il rosso c'e' gia' senza di lui."
			sed -n 's/^/        /p' "$S" | grep -E 'NO |⛔' | head -8
			FALLITI=$((FALLITI+1))
			RIGHE+=("$G|$SCENA|SANO ROSSO")
			continue
		fi
		ok "il giro SANO e' verde"
		SANI+=("$CHIAVE")
	fi

	# --- 2. il giro GUASTO --------------------------------------------------
	COPIA=$LAVORO/pagina-$G.html
	python3 "$QUI/06-b37-guasti.py" "$RADICE/src/pagina.html" "$COPIA" "$G" \
		| sed 's/^/        /' \
		|| { ko "il guasto $G non si e' innestato"; FALLITI=$((FALLITI+1));
		     RIGHE+=("$G|$SCENA|NON INNESTATO"); continue; }
	Gg=$LAVORO/guasto-$G-$SCENA.log
	gira "$COPIA" "$SCENA" "$FATT" "$G" "$Gg"
	E=$?
	if [ "$E" -eq 0 ]; then
		ko "⛔⛔ IL BANCO RESTA VERDE COL GUASTO $G DENTRO: non sa vedere il"
		ko "    difetto che dichiara di cercare, e ogni suo verde e' senza valore"
		FALLITI=$((FALLITI+1))
		RIGHE+=("$G|$SCENA|VERDE COL GUASTO")
		continue
	fi
	if grep -qF "$FRASE" "$Gg"; then
		ok "⭐ $G ha acceso il caso DICHIARATO (esito $E):"
		grep -F "$FRASE" "$Gg" | head -2 | sed 's/^/          /'
		CONFERMATI=$((CONFERMATI+1))
		RIGHE+=("$G|$SCENA|CONFERMATO")
	else
		ko "⛔ il giro e' rosso (esito $E) MA NON per il caso dichiarato:"
		ko "   «$FRASE» non compare.  Un rosso qualunque non certifica niente"
		grep -E '    NO |⛔⛔' "$Gg" | head -6 | sed 's/^/          /'
		FALLITI=$((FALLITI+1))
		RIGHE+=("$G|$SCENA|ROSSO PER ALTRO")
	fi
done

log "Il conto — $MOTORE"
if [ "${#RIGHE[@]}" -eq 0 ]; then
	ko "nessun caso eseguito: «$QUALI» non corrisponde a nessun guasto"
	exit 2
fi
for r in "${RIGHE[@]}"; do
	IFS='|' read -r a b c <<<"$r"
	printf '    %-4s %-11s %s\n' "$a" "$b" "$c"
done
printf '\n'
if [ "$FALLITI" -eq 0 ]; then
	ok "$CONFERMATI casi su $((CONFERMATI+FALLITI)): ogni guasto ha acceso la"
	ok "scena dichiarata, e la stessa scena sul prodotto era verde"
else
	ko "$CONFERMATI confermati, $FALLITI NON confermati su $((CONFERMATI+FALLITI))"
fi
inf "i registri completi dei giri restano in $LAVORO"
inf "gli esiti riga per riga, col numero di giro e il guasto: $ESITI"
exit $([ "$FALLITI" -eq 0 ] && echo 0 || echo 1)
