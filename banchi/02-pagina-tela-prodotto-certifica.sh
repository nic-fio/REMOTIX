#!/bin/bash
#
# 02-pagina-tela-prodotto-certifica.sh — SANO → GUASTO → RISANATO sul banco che
#   misura se `src/pagina.html` APPLICA le regole del cambio di tela.
#
#   bash banchi/02-pagina-tela-prodotto-certifica.sh
#
# ---------------------------------------------------------------------------
# ⛔ GLI ATTESI, SCRITTI PRIMA
#
# | guasto    | che cosa rompe                    | atteso                        |
# |-----------|-----------------------------------|-------------------------------|
# | (nessuno) | —                                 | T1, T5, T4, T11 **verdi**     |
# | `muto`    | butta i testi degli errori del    | ⛔ T4 **rosso** — «il prodotto|
# |           | prodotto                          | ha rifiutato E HA DETTO       |
# |           |                                   | perche'» smette di essere vero|
# | `ordine`  | ⭐ in T5 il fotogramma alla misura| ⛔ T5 **rosso**.  Senza questo|
# |           | vecchia porta un numero MAGGIORE  | giro, «l'ordine si applica    |
# |           | invece che minore                 | prima della misura» sarebbe   |
# |           |                                   | verde anche in un prodotto che|
# |           |                                   | guarda solo la misura — il    |
# |           |                                   | fotogramma sarebbe rifiutato  |
# |           |                                   | lo stesso, per la ragione     |
# |           |                                   | SBAGLIATA                     |
# | `pixel`   | la tela si copre di grigio DOPO   | ⛔ T1, T3, T7 **rossi** (sono |
# |           | la decodifica e prima della       | quelli che guardano i pixel), |
# |           | rilettura                         | T13 **verde** (regole)        |
# | `lettore` | il classificatore risponde sempre | ⛔ il BANCO si dichiara **non |
# |           | «la tinta attesa»                 | valido**: P2 dice 8/8 su una  |
# |           |                                   | tela grigia, e allora dei casi|
# |           |                                   | non si scrive niente          |
#
# ⚠ LA SCENA: Xvfb, uno schermo FINTO su un display suo — mai quello
#   dell'utente (`CODER.md` §3.2).  Su questa scena HEVC non arriva al pixel, e
#   i casi HEVC che vogliono un decodificatore vivo escono SALTATI, dichiarati.
#   I casi di sole regole (T10, T12..T15) valgono su tutt'e due i codec.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
export BERSAGLIO=prodotto
export SCHERMO=${SCHERMO:-:82}
export PORTA=${PORTA:-7552}
export MOTORI=${MOTORI:-chrome}

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

ESITO=0
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT

giro_con()
{
	local guasto=$1; shift
	local nome=${guasto:-sano}
	if GUASTO="$guasto" bash "$QUI/02-pagina-tela-lancia.sh" >"$T/$nome.log" 2>&1; then
		:
	fi
	local giro
	giro=$(sed -n 's/.*ha finito il giro \(f25tp-[a-z0-9-]*\).*/\1/p' \
	       "$T/$nome.log" | tail -1)
	if [ -z "$giro" ]; then
		ko "il giro «$nome» non e' arrivato in fondo: NON e' un guasto riprodotto"
		tail -20 "$T/$nome.log" | sed 's/^/        /'
		ESITO=1
		return 1
	fi
	inf "giro: $giro"
	local pretese=()
	local p
	for p in "$@"; do pretese+=(--pretendi "$p"); done
	python3 "$QUI/02-pagina-tela-prodotto-verdetto.py" "$giro" "${pretese[@]}" \
	  | sed -n '/le pretese di questo giro/,$p' | sed 's/^/    /'
	# ⛔ Lo stato d'uscita si prende dal comando, non dalla catena di `|`.
	python3 "$QUI/02-pagina-tela-prodotto-verdetto.py" "$giro" "${pretese[@]}" \
	  >/dev/null 2>&1
	local codice=$?
	if [ "$codice" -eq 0 ]; then ok "«$nome»: le pretese sono state onorate"
	else ko "«$nome»: una pretesa non e' stata onorata"; ESITO=1; fi
	return 0
}

log "0. La scena"
inf "Xvfb FINTO $SCHERMO · porta $PORTA · motori: $MOTORI"
inf "⚠ Non si tocca il display dell'utente (CODER.md §3.2)."

log "1. SANO"
giro_con "" T1-controllo-av1=verde T5-ordine-prima-della-misura-av1=verde \
             T4-dopo-la-chiave-la-vecchia-uccide-av1=verde \
             T11-buco-nei-numeri-av1=verde

log "2. GUASTO «ordine» — in T5 il fotogramma vecchio porta un numero MAGGIORE"
inf "atteso: T5 ROSSO, e gli altri restano verdi"
giro_con ordine T5-ordine-prima-della-misura-av1=rosso T1-controllo-av1=verde \
                T4-dopo-la-chiave-la-vecchia-uccide-av1=verde

log "3. GUASTO «muto» — i testi degli errori del prodotto si buttano"
inf "atteso: T4 ROSSO — «ha rifiutato E ha detto perche'» smette di essere vero"
giro_con muto T4-dopo-la-chiave-la-vecchia-uccide-av1=rosso T1-controllo-av1=verde

log "4. GUASTO «pixel» — la tela si copre di grigio prima della rilettura"
inf "atteso: T1, T3 e T7 ROSSI (guardano i pixel) · T13 VERDE (regole, non pixel)"
# ⛔⭐ E' il guasto che ha trovato un difetto DI QUESTO BANCO il 12 agosto 2026:
#    non faceva virare niente, perche' gli attesi di T1/T3/T7 contavano
#    fotogrammi e non guardavano `celle_giuste`.  Il «controllo positivo del
#    percorso video» non guardava il video (LEZIONI.md §1.3).
giro_con pixel T1-controllo-av1=rosso T3-riconfigura-sulla-chiave-av1=rosso \
               T7-misura-mai-annunciata-trattenuta-av1=rosso \
               T13-codec-non-negoziato-av1=verde

log "4-bis. GUASTO «lettore» — il classificatore risponde sempre giusto"
inf "atteso: il BANCO diventa NON VALIDO (P2 dice 8/8 su una tela grigia), e"
inf "        allora dei casi non si scrive niente — non serve nessuna pretesa"
if GUASTO=lettore bash "$QUI/02-pagina-tela-lancia.sh" >"$T/lettore.log" 2>&1; then
	ko "col guasto «lettore» il banco e' uscito VALIDO: un classificatore che"
	ko "   risponde sempre giusto passerebbe ogni caso, e ogni verde sarebbe vuoto"
	ESITO=1
else
	ok "«lettore»: il banco si e' dichiarato NON VALIDO, come atteso"
fi

log "5. RISANATO"
giro_con "" T1-controllo-av1=verde T5-ordine-prima-della-misura-av1=verde \
             T4-dopo-la-chiave-la-vecchia-uccide-av1=verde \
             T11-buco-nei-numeri-av1=verde

log "Esito della certificazione"
if [ "$ESITO" -eq 0 ]; then
	ok "sano → guasto → risanato: ogni guasto ha fatto virare quel che doveva"
else
	ko "la certificazione non e' passata (LEZIONI.md §1.3)"
fi
exit "$ESITO"
