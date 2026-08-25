#!/bin/bash
#
# 02-pagina-prodotto-certifica.sh — SANO → GUASTO → RISANATO sul banco che punta
#                                   sul PRODOTTO (`src/pagina.html`).
#
#   bash banchi/02-pagina-prodotto-certifica.sh          tutti i guasti
#   bash banchi/02-pagina-prodotto-certifica.sh pixel    uno solo
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' NON BASTA `02-pagina-certifica.sh`
#
# Quello certifica il banco che misura IL BROWSER.  Questo certifica il banco
# che misura IL PRODOTTO, e i due hanno un controllo in piu' e una scena
# diversa.  ⭐ La regola dell'11 agosto 2026 — *chi scrive un banco lo
# certifica nello stesso giro* — vale per il banco nuovo come per quello
# vecchio.
#
# ---------------------------------------------------------------------------
# ⚠ LA SCENA, DICHIARATA — E QUI E' UNA SCELTA, non un'abitudine
#
# ⛔ Si certifica su **Xvfb**, uno schermo FINTO su un display tutto suo, e NON
#    sul display che l'utente sta usando.  `CODER.md` §3.2: una misura fatta sul
#    display vero dipende da quante finestre erano aperte e da quanto era carica
#    la GPU in quel momento — e un browser che si apre sulla scrivania di
#    qualcuno e' un banco che gli mette le mani addosso.
#
# ⛔ E il prezzo si dichiara: su Xvfb non c'e' GPU, e su Linux il decodificatore
#    HEVC di Chrome e' quello della PIATTAFORMA (VA-API).  `[M]` 12 agosto 2026:
#    su schermo finto ogni stringa HEVC e' rifiutata.  ⇒ Qui `HEVC=arriva` NON
#    si puo' pretendere, e non e' una debolezza della certificazione: il
#    controllo positivo del percorso del prodotto e' **P9 (AV1)**, che `[M]`
#    arriva al pixel in tutte e quattro le caselle — con GPU e senza — ed e'
#    proprio la ragione per cui AV1 e' il ripiego negoziato (`DECISIONI.md`
#    §1.13).
#
# ⚠ Chi volesse anche `HEVC=arriva` deve girare sul display vero, e allora
#   quella e' una scelta da scrivere accanto al numero.
#
# ---------------------------------------------------------------------------
# ⛔ GLI ATTESI, SCRITTI PRIMA — la tabella e' il documento, non il commento
#
# | guasto     | che cosa rompe                          | atteso GUASTO             |
# |------------|-----------------------------------------|---------------------------|
# | (nessuno)  | —                                       | P1..P6 e **P9** verdi     |
# | `pixel`    | la tela si copre di grigio DOPO la      | ⛔ **P4 rosso** e **P9    |
# |            | decodifica e prima della rilettura      | rosso**, P1 e P2 VERDI    |
# | `lettore`  | il classificatore risponde sempre       | ⛔ **P2 rosso** e **P3    |
# |            | «la tinta attesa»                       | rosso**                   |
# | `scambio`  | al prodotto vanno i byte dell'ALTRO     | ⛔ **P5 rosso**           |
# |            | pattern                                 |                           |
# | `muto`     | i testi degli errori si buttano         | ⛔ **P6 rosso**, P1 e P4  |
# |            |                                         | verdi                     |
#
# ⛔ Che P1 e P2 restino VERDI sotto `pixel` fa parte dell'atteso: e' quel che
#    dice a chi legge che il rosso e' del percorso del video e non del lettore.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
export BERSAGLIO=prodotto
export SCHERMO=${SCHERMO:-:81}
export PORTA=${PORTA:-7551}
export MOTORI=${MOTORI:-chrome}
GUASTI=${*:-pixel lettore scambio muto}

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

ESITO=0
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT

# giro_con <guasto> <pretese…>
giro_con()
{
	local guasto=$1; shift
	local nome=${guasto:-sano}
	if GUASTO="$guasto" bash "$QUI/02-pagina-lancia.sh" >"$T/$nome.log" 2>&1; then
		:
	fi
	# ⛔ Il giro si ripesca dal registro del lancio, non si indovina: due giri
	#    nello stesso secondo avrebbero lo stesso nome se lo componessimo noi.
	local giro
	giro=$(sed -n 's/.*ha finito il giro \(f25p-[a-z0-9-]*\).*/\1/p' \
	       "$T/$nome.log" | tail -1)
	if [ -z "$giro" ]; then
		ko "il giro «$nome» non e' arrivato in fondo: nessuna pretesa e'"
		ko "   verificabile, e questo NON e' un guasto riprodotto"
		sed -n '/== 4/,/== 5/p' "$T/$nome.log" | sed 's/^/        /'
		ESITO=1
		return 1
	fi
	inf "giro: $giro"
	local pretese=()
	local p
	for p in "$@"; do pretese+=(--pretendi "$p"); done
	if python3 "$QUI/02-pagina-verdetto.py" "$giro" "${pretese[@]}" \
	   | sed -n '/le pretese di questo giro/,$p' | sed 's/^/    /'; then
		:
	fi
	# ⛔ Lo stato d'uscita va preso dal comando, non dalla catena di `|`.
	python3 "$QUI/02-pagina-verdetto.py" "$giro" "${pretese[@]}" >/dev/null 2>&1
	local codice=$?
	if [ "$codice" -eq 0 ]; then
		ok "«$nome»: le pretese sono state onorate"
	else
		ko "«$nome»: una pretesa non e' stata onorata (vedi sopra)"
		ESITO=1
	fi
	return 0
}

log "0. La scena, e perche' e' questa"
inf "schermo: Xvfb FINTO $SCHERMO (nessuna GPU) · porta $PORTA · motori: $MOTORI"
inf "⛔ Su questa scena HEVC non arriva al pixel, ed e' misurato: il controllo"
inf "   positivo del percorso del prodotto e' P9 (AV1), che arriva anche senza"
inf "   GPU.  ⚠ Non si tocca il display dell'utente (CODER.md §3.2)."

log "1. SANO — i sei controlli del banco piu' P9, il percorso del prodotto"
giro_con "" P1=verde P2=verde P3=verde P4=verde P5=verde P6=verde P9=verde

for g in $GUASTI; do
	case "$g" in
	pixel)
		log "2. GUASTO «pixel» — la tela si copre di grigio prima della rilettura"
		inf "atteso: P4 ROSSO e P9 ROSSO · P1 e P2 restano VERDI"
		giro_con pixel P4=rosso P9=rosso P1=verde P2=verde
		;;
	lettore)
		log "3. GUASTO «lettore» — il classificatore risponde sempre giusto"
		inf "atteso: P2 ROSSO e P3 ROSSO"
		giro_con lettore P2=rosso P3=rosso
		;;
	scambio)
		log "4. GUASTO «scambio» — al prodotto vanno i byte dell'ALTRO pattern"
		inf "atteso: P5 ROSSO"
		giro_con scambio P5=rosso
		;;
	muto)
		log "5. GUASTO «muto» — gli errori si buttano invece di registrarli"
		inf "atteso: P6 ROSSO — «zero» e «sono fallito» tornano ad avere lo"
		inf "        stesso aspetto (REVIEWER.md §1 punto 4)"
		giro_con muto P6=rosso P1=verde P4=verde
		;;
	*)
		ko "guasto sconosciuto: $g"
		ESITO=1
		;;
	esac
done

log "6. RISANATO — si toglie il guasto e si rifa' il giro sano"
giro_con "" P1=verde P2=verde P3=verde P4=verde P5=verde P6=verde P9=verde

log "Esito della certificazione"
if [ "$ESITO" -eq 0 ]; then
	ok "sano → guasto → risanato: ogni guasto ha fatto virare quel che doveva,"
	ok "   e SOLO quel che doveva"
else
	ko "la certificazione non e' passata: un banco che non riproduce il difetto"
	ko "   non e' una prova di correttezza (LEZIONI.md §1.3)"
fi
exit "$ESITO"
