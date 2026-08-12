#!/bin/bash
#
# 02-pagina-certifica.sh — F2.5: SANO → GUASTO → RISANATO, con i numeri attesi
#                          scritti PRIMA del giro.
#
#   bash banchi/02-pagina-certifica.sh              tutti i guasti
#   bash banchi/02-pagina-certifica.sh pixel        uno solo
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' ESISTE: PERCHE' UN BANCO VERDE NON E' UN BANCO CHE VEDE
#
# `LEZIONI.md` §1.3: *«un banco che NON riproduce il difetto non e' una prova
# di correttezza — e' piu' insidioso, perche' il banco e' verde»*.  E
# `REVIEWER.md` §1 punto 3 lo chiede per primo, prima del prodotto.
#
# ⭐ E vale la regola nata l'11 agosto 2026: **chi scrive un banco lo certifica
#    nello stesso giro**, o il conto non cala mai.  Questo script e' quel giro.
#
# ---------------------------------------------------------------------------
# ⛔ GLI ATTESI, SCRITTI PRIMA — e la tabella e' il documento, non il commento
#
# | guasto     | che cosa rompe                         | atteso SANO | atteso GUASTO       |
# |------------|----------------------------------------|-------------|---------------------|
# | (nessuno)  | —                                      | P1..P5 verdi, HEVC=arriva | —      |
# | `pixel`    | dipinge un grigio piatto invece del    | P4 verde    | ⛔ **P4 rosso**     |
# |            | fotogramma decodificato                |             | e P1, P2 **verdi**  |
# | `lettore`  | il classificatore risponde sempre      | P2 verde    | ⛔ **P2 rosso**     |
# |            | «la tinta attesa»                      | P3 verde    | e **P3 rosso**      |
# | `scambio`  | da' al decodificatore i byte dell'ALTRO| P5 verde    | ⛔ **P5 rosso**     |
# |            | pattern                                |             |                     |
# | `muto`     | butta i testi degli errori invece di   | P6 verde    | ⛔ **P6 rosso**     |
# |            | registrarli                            |             |                     |
# | `livello`  | dichiara nella stringa di codec un     | HEVC=arriva | ⛔ atteso            |
# |            | livello piu' basso del vero (§4.3 O12) |             | **non-arriva** —     |
# |            |                                        |             | **SMENTITO**, §5     |
#
# ⛔ **Che P1 e P2 restino VERDI sotto il guasto `pixel` fa parte dell'atteso**,
#    e non e' un dettaglio: e' quel che dice a chi legge che il rosso e' del
#    percorso del video e non del lettore.  Un guasto che facesse virare tutto
#    non insegnerebbe dov'e' il difetto — insegnerebbe solo che qualcosa c'e'.
#
# ⚠ E il guasto `livello` non e' come gli altri tre: quelli rompono il BANCO
#   apposta, questo mette in scena un difetto che il PRODOTTO puo' avere
#   davvero (`RCP.md` §4.3, rilievo O12: un livello dichiarato troppo basso non
#   da' un errore di rete, **fa rifiutare la configurazione dal
#   decodificatore**).  Serve a sapere che aspetto ha, prima che capiti.
#
# ---------------------------------------------------------------------------
# ⚠ LA SCENA, DICHIARATA — e qui decide il risultato
#
# ⛔ Si certifica sullo **schermo VERO** (`:10`), non su Xvfb: `[M]` 12 agosto
#    2026, su schermo finto Chrome rifiuta OGNI stringa HEVC, perche' su Linux
#    il suo decodificatore HEVC e' quello della piattaforma e senza GPU non
#    c'e'.  Su Xvfb il caso `sano` avrebbe `HEVC=non-arriva` **gia' da sano**,
#    e il guasto `livello` non farebbe virare niente: sarebbe una
#    certificazione che passa senza aver certificato nulla.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
export SCHERMO=${SCHERMO:-:10}
export SCHERMO_VERO=${SCHERMO_VERO:-1}
export MOTORI=${MOTORI:-chrome}
GUASTI=${*:-pixel lettore scambio muto livello}

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

ESITO=0
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT

# giro_con <guasto> <pretese…>  — lancia un giro e verifica le pretese
giro_con()
{
	local guasto=$1; shift
	local nome=${guasto:-sano}
	if GUASTO="$guasto" bash "$QUI/02-pagina-lancia.sh" >"$T/$nome.log" 2>&1; then
		:
	fi
	# ⛔ Il giro va ripescato dal registro del lancio, non indovinato: due
	#    giri nello stesso secondo avrebbero lo stesso nome se lo componessimo
	#    noi, e «l'ultima riga» e' il rilievo R8.10.
	local giro
	giro=$(sed -n 's/.*ha finito il giro \(f25-[a-z0-9-]*\).*/\1/p' "$T/$nome.log" | tail -1)
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
	# ⛔ Lo stato d'uscita va preso dal comando, non dalla catena di `|`: e' il
	#    difetto 2 della quarta regola di `LEZIONI.md` §1.9, pagato tre volte
	#    in un'ora la sera del 9 agosto.
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

# ---------------------------------------------------------------------------
log "0. La scena, e perche' e' questa"
inf "schermo: $SCHERMO (VERO, con la GPU) · motori: $MOTORI"
inf "⛔ Su Xvfb il caso «sano» avrebbe HEVC=non-arriva gia' da sano, e la"
inf "   certificazione passerebbe senza aver certificato niente."

# ---------------------------------------------------------------------------
log "1. SANO — i SEI controlli verdi, e HEVC che arriva al pixel"
giro_con "" P1=verde P2=verde P3=verde P4=verde P5=verde P6=verde HEVC=arriva

# ---------------------------------------------------------------------------
for g in $GUASTI; do
	case "$g" in
	pixel)
		log "2. GUASTO «pixel» — si dipinge un grigio invece del fotogramma"
		inf "atteso: P4 ROSSO · P1 e P2 restano VERDI (il rosso e' del video,"
		inf "        non del lettore)"
		giro_con pixel P4=rosso P1=verde P2=verde
		;;
	lettore)
		log "3. GUASTO «lettore» — il classificatore risponde sempre giusto"
		inf "atteso: P2 ROSSO e P3 ROSSO"
		giro_con lettore P2=rosso P3=rosso
		;;
	scambio)
		log "4. GUASTO «scambio» — al decodificatore vanno i byte dell'ALTRO pattern"
		inf "atteso: P5 ROSSO"
		giro_con scambio P5=rosso
		;;
	muto)
		log "5. GUASTO «muto» — gli errori si buttano invece di registrarli"
		inf "atteso: P6 ROSSO — «zero» e «sono fallito» tornano ad avere lo"
		inf "        stesso aspetto (REVIEWER.md §1 punto 4)"
		giro_con muto P6=rosso P1=verde P4=verde
		;;
	livello)
		log "6. «livello» — NON e' un guasto del banco: e' una MISURA, e l'atteso"
		log "   scritto prima e' stato SMENTITO"
		# ⛔⭐ QUI L'ATTESO SCRITTO PRIMA NON E' STATO ONORATO, E NON SI RITOCCA.
		#
		# L'atteso era `HEVC=non-arriva`, e veniva da `RCP.md` §4.3 rilievo
		# **O12**: *«un livello dichiarato troppo basso non da' un errore di
		# rete — fa rifiutare la configurazione dal decodificatore, e il
		# sintomo e' "il browser non apre il flusso"»*.
		#
		# `[M]` 12 agosto 2026, Chrome 151.0.7922.108 su Linux, schermo vero:
		# chiesto **`hev1.2.4.L30.90`** (livello 1.0) su un flusso 640x480 il
		# cui livello vero e' **3.0**, `isConfigSupported` ha risposto **true**,
		# la configurazione e' passata e la pagina ha dipinto **8 celle su 8**.
		# ⇒ Su questo motore il livello dichiarato **non viene fatto
		#   rispettare**, e il guasto non fa virare niente.
		#
		# ⛔ Il fatto verificato che il guasto sia ENTRATO IN VIGORE e' quel che
		#    rende leggibile il non-viraggio: `codec_chiesto` nel registro dice
		#    `hev1.2.4.L30.90`, non la stringa buona.  Senza quella verifica
		#    questo sarebbe stato «il guasto non si e' innestato»
		#    (`LEZIONI.md` §1.11, corollario: non basta dire al componente cosa
		#    fare, va verificato che abbia obbedito).
		#
		# ⚠ E la conseguenza NON e' rassicurante, e va scritta nel verso
		#   giusto: un livello sbagliato che **non** viene rifiutato e' peggio
		#   di uno rifiutato, perche' toglie il sintomo che lo diagnosticava.
		#   Il conto lo paghera' il dispositivo che quel livello lo fa
		#   rispettare davvero, e li' il sintomo tornera' — altrove.
		inf "atteso scritto prima: HEVC=non-arriva  (RCP.md §4.3, O12)"
		inf "⛔ SMENTITO il 12 ago 2026 su Chrome 151/Linux: il livello"
		inf "   dichiarato non viene fatto rispettare — si pretende quel che"
		inf "   la misura dice, e la smentita sta nel rapporto, non qui"
		giro_con livello HEVC=arriva
		;;
	*)
		ko "guasto sconosciuto: $g"
		ESITO=1
		;;
	esac
done

# ---------------------------------------------------------------------------
log "7. RISANATO — si toglie il guasto e si rifa' il giro sano"
# ⛔ Il terzo tempo NON e' una formalita': senza, un guasto che avesse lasciato
#    qualcosa dietro di se' — una sequenza riscritta, un profilo sporco —
#    verrebbe scoperto dal giro di domani, e attribuito a domani.
giro_con "" P1=verde P2=verde P3=verde P4=verde P5=verde P6=verde HEVC=arriva

# ---------------------------------------------------------------------------
log "Esito della certificazione"
if [ "$ESITO" -eq 0 ]; then
	ok "sano → guasto → risanato: ogni guasto ha fatto virare quel che doveva,"
	ok "   e SOLO quel che doveva"
else
	ko "la certificazione non e' passata: un banco che non riproduce il difetto"
	ko "   non e' una prova di correttezza (LEZIONI.md §1.3)"
fi
exit "$ESITO"
