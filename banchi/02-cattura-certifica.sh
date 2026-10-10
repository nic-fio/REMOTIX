#!/bin/bash
#
# 02-cattura-certifica.sh — runs ON THE SERVER.  ⛔ The certification of the
# F2.2 bench on the B12 model: healthy N → fault M → healed N, with the expected numbers
# **written before the round**.
#
#   bash /media/REMOTIX/src/02-cattura-certifica.sh            healthy round + the four faults
#   bash /media/REMOTIX/src/02-cattura-certifica.sh PREFISSO   reuses a healthy round already done
#
# ===========================================================================
# ⛔ WHY IT EXISTS, AND WHY IN THE SAME ROUND AS WHOEVER WRITES THE BENCH
#
# ⭐ The rule born on 11 Aug 2026: *whoever writes a bench certifies it in the
#    same round*, or the count never goes down.  And `PIANO.md` §0.3 point 4: every
#    phase, before declaring a number, proves that its bench can see the
#    defect it is looking for.
#
# ⛔ And for F2.2 the question is not academic.  The defect this bench exists
#    to see is **a black and valid frame**: a buffer of the right
#    size, with the right stride, the right damage, the right sequence — and
#    nothing inside.  ⛔ It is the worst fault of this sub-phase because every
#    other tool of the project would promote it: `misura-cattura` of phase 0
#    would count 36 frames per second and would not look inside even one.
#
# ⇒ A bench that cannot tell a black frame from a full one **would give
#   confidence**, and it is precisely the case `REVIEWER.md` §1 calls the
#   worst: *«a defect in the bench is found by nothing, and it poisons every
#   following measurement because it gives confidence»*.
#
# ===========================================================================
# ⛔ THE FAULT IS INJECTED INTO THE PIXELS, AND TOUCHES NEITHER THE PRODUCER NOR THE JUDGE
#
# It is the reason why the producer (`02-cattura-fotogramma.c`) and the judge
# (`02-cattura-giudica.py`) are two separate programs: between the two there is a file,
# and in that file anything can be put.  ⭐ No recompilation,
# no line changed, no `git`.  The fault is the **data**, which is the most
# honest way of breaking a judge.
#
# ⛔ AND ALWAYS ON A COPY, with the original kept aside and the fingerprint next to it
#    — like `01-b12-guasti.py`, which never touches the file to be broken.
#
# ===========================================================================
# ⛔ THE EXPECTATIONS, WRITTEN BEFORE THE ROUND (B0.4)
#
#   the HEALTHY round exits 0 (VERDE) — and it is not a widened expectation: the frame
#   is there, it is 1920×1080 as requested, and it contains the «bandiera» scene.
#   ⚠ If the healthy round did NOT exit 0, the certification **stops**: no
#     fault is injected on a bench already red, because the red afterwards would not
#     say anything (`FASI.md` §00-ambiente, and the lesson of B13).
#
#   | # | the fault injected into the .raw | expected | REQUIRED mark           | FORBIDDEN mark |
#   |---|-------------------------------|--------|-------------------------|---------------|
#   | G1| full black, same bytes        |   1    | FOTOGRAMMA NERO         | —             |
#   | G2| uniform grey, same bytes      |   1    | SCENA NON RICONOSCIUTA  | FOTOGRAMMA NERO |
#   | G3| last bytes cut off            |   1    | BYTE NON TORNANO        | —             |
#   | G4| the «first» copied onto «steady»|  1    | IL BUFFER NON E' CAMBIATO| FOTOGRAMMA NERO |
#
#   and the HEALED one goes back to 0 after each.
#
# ⭐ THE TWO COLUMNS «REQUIRED» AND «FORBIDDEN» ARE THE HALF THAT COUNTS, and without the
#    second this certification would be a performance:
#
#   - **G2** is the fault that tells a judge from a brightness
#     meter.  A uniform grey is not black: calling it black would mean
#     getting the worst diagnosis wrong precisely in the case where it is needed, and the cure
#     would be looked for on the wrong side — the same half day that
#     `PIANO.md` tells about for the black session;
#   - **G4** is the fault of trap 8 of `LEZIONI.md` §4: *«the last
#     frame must be kept and resent, or whoever connects to a still desktop
#     stays on black»*.  An old buffer resent is a
#     perfectly valid frame, not black, with the scene inside — ⛔ **green on every
#     check that looks at a single frame**.  It shows only by comparing
#     two, and that is why the producer takes two.
#
# ⛔ And a fault that is NOT in this table, declared instead of kept silent:
#    **the buffer of the wrong card** (`LEZIONI.md` §4 trap 6, two GPUs
#    on this machine).  It cannot be injected here and this bench would not
#    see it: on the memory road the pixels arrive anyway.  It stays a
#    `[?]` of the report, not something this green acquits.
# ===========================================================================
set -uo pipefail

QUI=${QUI:-/media/REMOTIX/tmp/02-cattura}
SRC=${SRC:-/media/REMOTIX/src}
GIUDICE=$SRC/02-cattura-giudica.py
LANCIA=$SRC/02-cattura-lancia.sh
SCENA=${SCENA:-bandiera}
mkdir -p "$QUI" || { echo "⛔ I cannot create $QUI" >&2; exit 2; }
REGISTRO=$QUI/certificazione-$(date -u +%Y%m%d-%H%M%S).log

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

ATTESO_SANO=0

# ---------------------------------------------------------------------------
#  The injection: always on a copy, with the fingerprint before and after
# ---------------------------------------------------------------------------
innesta()
{
	local che=$1 regime=$2 primo=$3
	python3 - "$che" "$regime" "$primo" <<'FINE'
import os, sys
che, regime, primo = sys.argv[1:4]
n = os.path.getsize(regime)
if che == "nero":
    dati = bytes(n)
elif che == "grigio":
    # ⛔ Not just any grey: BGRx with B=G=R=128 and x=255, that is a
    #    perfectly valid and perfectly useless frame.
    dati = bytes([128, 128, 128, 255]) * (n // 4) + bytes(n % 4)
elif che == "troncato":
    dati = open(regime, "rb").read()[: n - 40000]
elif che == "copia":
    dati = open(primo, "rb").read()
    if len(dati) > n:
        dati = dati[:n]
    elif len(dati) < n:
        dati = dati + bytes(n - len(dati))
else:
    print("unknown fault:", che, file=sys.stderr)
    sys.exit(2)
open(regime, "wb").write(dati)
print("    --  injected «%s»: %d bytes (they were %d)" % (che, len(dati), n))
FINE
	return $?
}

impronta() { sha256sum "$1" | cut -d' ' -f1; }

# ---------------------------------------------------------------------------
#  A round of the judge, and the comparison with the expectation written beforehand
# ---------------------------------------------------------------------------
giudica()
{
	local prefisso=$1 dove=$2
	python3 -u "$GIUDICE" --manifesto "$prefisso.json" --scena "$SCENA" \
	        --json "$dove.json" > "$dove.log" 2>&1
	return $?
}

marche_di()
{
	# ⛔ Only the RED marks: a warning on the `primo` frame — where the scene
	#    is not there yet — is not a finding, and counting it here would pass off as
	#    «the fault was seen» a noise that was there in the healthy round too.
	python3 -c '
import json, sys
v = json.load(open(sys.argv[1]))
m = [r["marca"] for f in v.get("fotogrammi", {}).values()
     for r in f.get("rilievi", []) if r.get("rosso", True)]
m += [r["marca"] for r in v.get("confronto_primo_regime", {}).get("rilievi", [])]
print(" ".join(sorted(set(m))))' "$1"
}

verifica()
{
	local nome=$1 uscita=$2 atteso=$3 marche=$4 pretesa=$5 vietata=$6
	local buono=si
	if [ "$uscita" != "$atteso" ]; then
		ko "$nome: exit $uscita, expected $atteso"; buono=
	fi
	if [ -n "$pretesa" ] && [[ "$marche" != *"$pretesa"* ]]; then
		ko "$nome: the REQUIRED mark «$pretesa» is missing — found: ${marche:-none}"; buono=
	fi
	if [ -n "$vietata" ] && [[ "$marche" == *"$vietata"* ]]; then
		ko "$nome: the FORBIDDEN mark «$vietata» is there — the judge gets the diagnosis wrong"; buono=
	fi
	if [ -n "$buono" ]; then
		ok "$nome: exit $uscita as expected, marks: ${marche:-none}"
		return 0
	fi
	return 1
}

# ===========================================================================
{
log "0. THE INITIAL STATE — declared and checked (B0.1)"
for f in "$GIUDICE" "$LANCIA"; do
	if [ ! -r "$f" ]; then ko "⛔ cannot read: $f"; exit 2; fi
done
ok "the two files of the bench can be read"

log "0-bis. THE JUDGE FIRST OF ALL: does it pass its own positive control?"
inf "⛔ A bench is not certified with an uncertified tool: it would be measuring"
inf "   with a ruler whose scale was never checked (LEZIONI.md §1.2)."
python3 -u "$GIUDICE" --solo-controllo-positivo
if [ $? -ne 0 ]; then
	ko "⛔ the judge is NOT certified: the certification stops here"
	exit 2
fi
ok "the judge finds the flag, calls black the black, and does NOT call black the grey"

# ---------------------------------------------------------------------------
log "1. THE HEALTHY ROUND — and the expectation is $ATTESO_SANO, written beforehand"
PREFISSO=${1:-}
if [ -z "$PREFISSO" ]; then
	inf "no prefix given: I do a real round with $LANCIA"
	SCENA=$SCENA bash "$LANCIA" misura
	U_LANCIA=$?
	inf "the healthy round exited with $U_LANCIA"
	# ⛔ The exit is not enough: the PREFIX of the round is needed, and it is taken from the
	#    most recent file instead of guessed.  ⚠ And the list is built with a
	#    glob, not with `ls` inside a pipe: «no file» and «ls failed»
	#    look the same in a chain of `|`, and it is item 3 of
	#    `FASI.md` §00-ambiente — «no line found» was a denied read.
	CANDIDATI=()
	for m in "$QUI"/giro-*.json; do
		case "$m" in *-verdetto.json) continue ;; esac
		[ -f "$m" ] && CANDIDATI+=("$m")
	done
	if [ ${#CANDIDATI[@]} -eq 0 ]; then
		ko "⛔ no manifest in $QUI: the healthy round produced nothing."
		inf "⚠ It is not «the bench is broken»: it is «there was no round»."
		exit 2
	fi
	PREFISSO=$(ls -t "${CANDIDATI[@]}" | head -1)
	PREFISSO=${PREFISSO%.json}
fi
if [ -z "$PREFISSO" ] || [ ! -f "$PREFISSO.json" ]; then
	ko "⛔ I cannot find the manifest of the healthy round ($PREFISSO.json)"
	exit 2
fi
ok "healthy round: $PREFISSO"

REGIME=$PREFISSO-regime.raw
PRIMO=$PREFISSO-primo.raw
if [ ! -f "$REGIME" ] || [ ! -f "$PRIMO" ]; then
	ko "⛔ the two .raw of the healthy round are missing: there is nothing to break"
	inf "⚠ and this is NOT a broken bench: it is a round that took no frames."
	exit 2
fi

# ⛔ THE ORIGINAL IS PUT ASIDE BEFORE TOUCHING IT, with the fingerprint next to it.
ORIGINALE=$QUI/originale-regime.raw
cp -f "$REGIME" "$ORIGINALE" || exit 2
IMP_ORIG=$(impronta "$ORIGINALE")
inf "original put aside: $ORIGINALE"
inf "fingerprint: $IMP_ORIG"

giudica "$PREFISSO" "$QUI/cert-sano"; U_SANO=$?
M_SANO=$(marche_di "$QUI/cert-sano.json")
verifica "sano" "$U_SANO" "$ATTESO_SANO" "$M_SANO" "" ""
if [ $? -ne 0 ]; then
	ko "⛔ THE HEALTHY ROUND IS NOT HEALTHY: the certification stops."
	inf "Injecting a fault on a bench already red would give a red that says nothing."
	inf "The judge's log:"
	sed 's/^/       /' "$QUI/cert-sano.log"
	cp -f "$ORIGINALE" "$REGIME"
	exit 2
fi

# ---------------------------------------------------------------------------
FALLITI=0
#      name        expected  REQUIRED mark             FORBIDDEN mark
GUASTI=(
	"nero|1|FOTOGRAMMA NERO|"
	"grigio|1|SCENA NON RICONOSCIUTA|FOTOGRAMMA NERO"
	"troncato|1|BYTE NON TORNANO|"
	"copia|1|IL BUFFER NON E' CAMBIATO|FOTOGRAMMA NERO"
)
for voce in "${GUASTI[@]}"; do
	IFS='|' read -r NOME ATT PRETESA VIETATA <<< "$voce"

	log "2. FAULT «$NOME» — expected $ATT, required mark «$PRETESA», forbidden «${VIETATA:-none}»"
	cp -f "$ORIGINALE" "$REGIME" || exit 2
	innesta "$NOME" "$REGIME" "$PRIMO" || { ko "injection failed"; FALLITI=$((FALLITI+1)); continue; }
	inf "fingerprint after the injection: $(impronta "$REGIME")"

	giudica "$PREFISSO" "$QUI/cert-guasto-$NOME"; U=$?
	M=$(marche_di "$QUI/cert-guasto-$NOME.json")
	verifica "guasto/$NOME" "$U" "$ATT" "$M" "$PRETESA" "$VIETATA" || FALLITI=$((FALLITI+1))

	log "3. HEALED after «$NOME» — expected $ATTESO_SANO"
	cp -f "$ORIGINALE" "$REGIME" || exit 2
	IMP=$(impronta "$REGIME")
	if [ "$IMP" != "$IMP_ORIG" ]; then
		ko "⛔ the healing did not put the file back as it was: $IMP ≠ $IMP_ORIG"
		FALLITI=$((FALLITI+1))
	else
		ok "the fingerprint went back to the one before: $IMP"
	fi
	giudica "$PREFISSO" "$QUI/cert-risano-$NOME"; U=$?
	M=$(marche_di "$QUI/cert-risano-$NOME.json")
	verifica "risanato/$NOME" "$U" "$ATTESO_SANO" "$M" "" "" || FALLITI=$((FALLITI+1))
done

# ---------------------------------------------------------------------------
log "4. THE VERDICT OF THE CERTIFICATION"
cp -f "$ORIGINALE" "$REGIME"
if [ $FALLITI -eq 0 ]; then
	ok "⭐ THE F2.2 BENCH IS CERTIFIED: healthy $ATTESO_SANO → four faults → healed $ATTESO_SANO"
	inf "⚠ And this does not say the bench is right: it says it can see THESE four"
	inf "  defects. «I found nothing» is not «it is right» (REVIEWER.md §0)."
	ESITO=0
else
	ko "⛔ THE CERTIFICATION DOES NOT PASS: $FALLITI checks failed."
	inf "Until it passes, no number of this bench counts."
	ESITO=1
fi
inf "the full log of this round: $REGISTRO"

# The catalogue, in the form of 01-b12-guasti.py, printed here so that it stays
# next to the numbers instead of in a separate document.
cat <<FINE

  THE LINE FOR THE CATALOGUE OF CERTIFICATIONS
  ────────────────────────────────────────────────────────────────────────
  name            F2.2 — capture (the black and valid frame)
  command         bash /media/REMOTIX/src/02-cattura-certifica.sh
  expected healthy 0 (VERDE: a 1920×1080 frame that contains the scene)
  faults          nero · grigio · troncato · copia — injected into the .raw, never
                  into the code, always on a copy with the original aside
  expected fault  1  each, with the required mark AND the forbidden one
  expected healed 0  after each, with the fingerprint back to the one before
  cost            file-copy (no recompilation)
  reference       fasi/rapporti/F2-2-cattura.md · STUDI.md §gnome §3.1 §13 M9 ·
                  LEZIONI.md §1.9 §4 trap 8 · REVIEWER.md §1 point 4, E1

FINE
exit $ESITO
} 2>&1 | tee "$REGISTRO"
exit "${PIPESTATUS[0]}"
