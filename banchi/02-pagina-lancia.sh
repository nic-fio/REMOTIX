#!/bin/bash
#
# 02-pagina-lancia.sh — F2.5: dal byte al PIXEL DIPINTO, su browser veri.
#                       `PIANO.md` fase 2 · `web.md` §4 · `CODER.md` §2 (I8)
#
#   bash banchi/02-pagina-lancia.sh                 i due motori, schermo finto
#   SCHERMO=:0 bash banchi/02-pagina-lancia.sh      sullo schermo VERO
#   MOTORI=chrome bash banchi/02-pagina-lancia.sh   uno solo
#   GUASTO=pixel bash banchi/02-pagina-lancia.sh    con un guasto innestato
#
# ⚠ GIRA DA QUESTA PARTE DEL FILO: i browser stanno su CHUWI, non su NIC-OS.
#   Su NIC-OS non si tocca niente (mandato §4): 7448 e 7501 sono accese apposta.
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' QUESTO BANCO ESISTE, E CHE MISURA SBAGLIATA IMPEDISCE
#
# La fase 2 finisce quando **l'utente vede il proprio desktop dentro una scheda
# del browser**.  Il modo piu' facile di dichiararla finita senza che sia vero
# e' guardare il numero che esce dal decodificatore invece del pixel:
#
#     `VideoDecoder.isConfigSupported({codec:"hev1…"})` → `true`
#     `configure()` non lancia
#     `decode()` non lancia
#     ⇒ «la pagina decodifica HEVC»
#
# ⛔ Tutte e tre sono compatibili con una tela **nera**.  `web.md` §9.1 lo dice
#    per l'hardware — *«cambiare strato non regala immunita': una promessa di
#    un'API va trattata come la dichiarazione di un compositore»* — e vale
#    identico un gradino piu' in basso, sulla decodifica stessa.  L'invariante
#    I8 di `CODER.md` §2 chiude la questione: **il metro e' quel che l'utente
#    vede, non il numero che esce dal banco.**
#
# ⇒ Qui si guarda la tela.  Si rileggono i pixel dipinti, si classificano
#   contro un pattern noto, e i pixel escono dal browser — miniatura nel
#   registro, PNG su disco — perche' **F2.6 giudichi sui pixel e non sul nostro
#   verdetto**.
#
# ---------------------------------------------------------------------------
# ⛔ IL CONTROLLO POSITIVO, E PERCHE' NON E' IN CODA MA IN MEZZO
#
# Il mandato §3.2 chiede *«un controllo positivo in coda a ogni esecuzione»*.
# Qui ce n'e' uno in coda (§6: il raccoglitore ha ricevuto e il verdetto sa
# leggere) **e uno prima della misura**, che e' quello che conta:
#
#   ⭐ **VP9** — un flusso che ogni motore decodifica.  Se HEVC cade e VP9
#      riesce, il «no» e' di HEVC.  ⛔ Se cadono tutti e due, il «no» e' di
#      questa pagina, e su HEVC **non si scrive niente**.
#
# Senza, un rosso su Firefox sarebbe indistinguibile fra «Firefox non fa HEVC»
# e «il banco non funziona su Firefox»: la forma d'errore **E10** vista
# dall'altra parte, e la stessa che `web.md` §3.3 racconta come il rilievo piu'
# grave della revisione R2 — *«il controllo positivo era cieco, e la sua
# conclusione era la conclusione sbagliata su un dato mancante»*.
#
# ---------------------------------------------------------------------------
# ⛔ ZERO E FALLIMENTO — `REVIEWER.md` §1 punto 4
#
# Niente `2>/dev/null`, nessuno stato d'uscita buttato in una catena di `|`.
# «Nessun esito» ha quattro cause con lo stesso aspetto, e ciascuna ha qui la
# sua riga: il browser che non parte · la pagina che non si apre · le sequenze
# che mancano · la misura che c'e' stata e l'esito non e' uscito.  Il
# raccoglitore stampa **ogni richiesta**, e il conto delle richieste e' il
# denominatore.
#
# ---------------------------------------------------------------------------
# ⚠ LA SCENA, DICHIARATA
#
# Schermo finto **Xvfb 1280x1024x24** sul display `:75` — che non e' quello di
# S5 (`:78`) ne' quelli in uso (`:10`, `:1024`, `:1025`): due banchi sullo
# stesso display si rubano il fuoco, ed e' gia' successo.  Porta **7515**, che
# e' quella assegnata a F2.5 dal mandato §2.
#
# ⛔ E LA SCENA NON SI MUOVE, di proposito, ed e' l'unica volta in cui va bene:
#    `LEZIONI.md` §1.1 vuole una scena in movimento perche' un compositore
#    manda un fotogramma solo quando qualcosa cambia — ma qui non c'e' nessun
#    compositore da misurare.  Il flusso e' **un file**, costruito da noi,
#    identico a ogni giro: e' proprio la sua immobilita' che rende leggibile la
#    differenza fra un giro e l'altro.
# ---------------------------------------------------------------------------
set -uo pipefail

# ---------------------------------------------------------------------------
# ⭐ IL BERSAGLIO — 12 agosto 2026, quando il prodotto e' esistito
#
#   BERSAGLIO=banco     `02-pagina-prova.html`     misura IL BROWSER (il giro
#                                                  originale di F2.5)
#   BERSAGLIO=prodotto  `02-pagina-prodotto.html`  misura `src/pagina.html`,
#                                                  cioe' LA PAGINA CHE L'UTENTE
#                                                  APRE, guidandone l'oggetto
#                                                  `Schermo` dentro un iframe
#
# ⛔ Sono due domande diverse e le risposte non si sostituiscono: «il browser
#    decodifica HEVC» non dice che il prodotto lo dipinga, e viceversa.  La
#    riga di esito porta il bersaglio, come porta la scena.
BERSAGLIO=${BERSAGLIO:-banco}
case "$BERSAGLIO" in
banco)    PAGINA=02-pagina-prova.html ;;
prodotto) PAGINA=02-pagina-prodotto.html ;;
*) echo "NO  BERSAGLIO dev'essere «banco» o «prodotto», non «$BERSAGLIO»"; exit 2 ;;
esac

QUI=$(cd "$(dirname "$0")" && pwd)
PORTA=${PORTA:-7515}
SCHERMO=${SCHERMO:-:75}
TELA=${TELA:-1280x1024}
MOTORI=${MOTORI:-chrome firefox}
GUASTO=${GUASTO:-}
ATTESA=${ATTESA:-90}
REGISTRO=$QUI/02-pagina-esiti.jsonl
T=$(mktemp -d)

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

ESITO=0
PID_X=
PID_RACC=
PID_BR=
GIRI=()

congedo()
{
	[ -n "$PID_BR" ]   && { kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; }
	[ -n "$PID_RACC" ] && { kill "$PID_RACC" 2>/dev/null; wait "$PID_RACC" 2>/dev/null; }
	[ -n "$PID_X" ]    && { kill "$PID_X" 2>/dev/null; wait "$PID_X" 2>/dev/null; }
	rm -rf "$T"
}
trap congedo EXIT

# ---------------------------------------------------------------------------
log "1. Le sequenze — il flusso noto"

# ⛔ Si RICOSTRUISCONO se mancano, e non si prosegue senza: una sequenza
#    assente fa misurare «zero fotogrammi» su un flusso mai arrivato, e il
#    banco accuserebbe il browser di un difetto del banco.
if ! python3 "$QUI/02-pagina-sequenze.py" --elenca; then
	inf "le sequenze non ci sono: si costruiscono adesso"
	if ! python3 "$QUI/02-pagina-sequenze.py"; then
		ko "le sequenze non si costruiscono: senza flusso non c'e' misura"
		exit 2
	fi
fi

# ⛔ Il controllo VP9 DEVE esserci, e si guarda che ci sia PRIMA di accendere
#    un browser: senza di lui un «no» su HEVC non e' leggibile (vedi sopra).
if [ ! -f "$QUI/02-pagina-sequenze/A-vp9.json" ]; then
	ko "manca la sequenza di controllo A-vp9: senza, un rosso su HEVC non si"
	ko "   distingue da un banco rotto, e questo banco non gira"
	exit 2
fi
ok "il flusso di controllo (VP9) c'e'"

# ---------------------------------------------------------------------------
log "2. Lo schermo"

# ⛔ `SCHERMO_VERO=1` NON E' UNA COMODITA': E' META' DELLA MISURA.
#    `[M]` 12 agosto 2026: su Xvfb, Chrome su Linux rifiuta OGNI stringa HEVC —
#    perche' su Linux il decodificatore HEVC di Chrome e' quello della
#    PIATTAFORMA (VA-API), e su uno schermo finto senza GPU non c'e'.  ⇒ La
#    domanda «questo browser decodifica HEVC?» ha due risposte diverse sulle
#    due scene, e chi ne misurasse una sola scriverebbe un `[M]` che vale per
#    meta' degli utenti.  Il display vero di questa macchina e' `:10`, non `:0`:
#    e' il display di GNOME, e va detto perche' `:0` qui non esiste.
if [ "$SCHERMO" = ":0" ] || [ -n "${SCHERMO_VERO:-}" ]; then
	inf "⚠ schermo VERO ($SCHERMO): si apriranno finestre sulla scrivania,"
	inf "   e il browser vedra' la GPU — che e' precisamente il punto"
	if ! env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO xdpyinfo >"$T/xdpyinfo.txt" 2>&1; then
		ko "il display $SCHERMO non risponde: non c'e' niente su cui aprire"
		sed -n '1,4p' "$T/xdpyinfo.txt" | sed 's/^/        /'
		exit 2
	fi
	inf "risoluzione letta fuori dal browser: $(sed -n 's/^  dimensions: *\([0-9]*x[0-9]*\) pixels.*/\1/p' "$T/xdpyinfo.txt" | head -1)"
else
	Xvfb "$SCHERMO" -screen 0 "${TELA}x24" >"$T/xvfb.log" 2>&1 &
	PID_X=$!
	sleep 2
	if [ ! -d "/proc/$PID_X" ]; then
		ko "Xvfb non e' partito:"
		sed 's/^/        /' "$T/xvfb.log"
		exit 2
	fi
	inf "schermo finto $SCHERMO, chiesto ${TELA}x24"
fi

# ---------------------------------------------------------------------------
log "3. Il raccoglitore, sulla porta $PORTA"

# ⛔ Se la porta e' gia' occupata ci si ferma dicendolo: due banchi sulla stessa
#    porta si fermano a vicenda (mandato §4), e il sintomo — «la pagina non si
#    apre» — non nomina la porta.
if ss -ltn "sport = :$PORTA" | grep -q ":$PORTA"; then
	ko "la porta $PORTA e' gia' occupata da qualcun altro:"
	ss -ltnp "sport = :$PORTA" | sed 's/^/        /'
	exit 3
fi

python3 -u "$QUI/02-pagina-raccogli.py" "$PORTA" >"$T/racc.log" 2>&1 &
PID_RACC=$!
sleep 1
if [ ! -d "/proc/$PID_RACC" ]; then
	ko "il raccoglitore non e' partito:"
	sed 's/^/        /' "$T/racc.log"
	exit 3
fi
ok "raccoglitore su 127.0.0.1:$PORTA"

# ---------------------------------------------------------------------------
# Attende la riga FINITO del giro dato.  ⛔ Si cerca **il giro**, non «l'ultima
# riga»: e' il rilievo R8.10 di B2, ripagato da S7 la stessa sera.
attendi_fine()
{
	local giro=$1 secondi=$2 i=0
	while [ "$i" -lt "$secondi" ]; do
		if python3 - "$REGISTRO" "$giro" <<'PY'
import json, os, sys
percorso, giro = sys.argv[1], sys.argv[2]
if not os.path.exists(percorso):
    sys.exit(1)
for riga in open(percorso, encoding="utf-8"):
    try:
        d = json.loads(riga)
    except Exception:
        continue
    if d.get("giro") == giro and d.get("tipo") == "FINITO":
        sys.exit(0)
sys.exit(1)
PY
		then
			return 0
		fi
		sleep 1
		i=$((i + 1))
	done
	return 1
}

# ---------------------------------------------------------------------------
# prova_motore <nome> <binario> <opzioni…>
# ---------------------------------------------------------------------------
prova_motore()
{
	local nome=$1 binario=$2; shift 2
	log "4. $nome"
	if ! command -v "$binario" >/dev/null; then
		# ⛔ Si DICE, invece di far calare il denominatore in silenzio.
		inf "⚠ $binario non c'e' su questa macchina: si salta, E SI DICE"
		return 0
	fi
	inf "versione: $("$binario" --version 2>&1 | head -1)"

	# ⛔ Il prefisso del giro cambia SOLO per il bersaglio «prodotto», e non e'
	#    un gusto: `02-pagina-certifica.sh` ripesca il giro dal registro con
	#    `f25-[a-z0-9-]*`, e rinominare anche i giri del banco avrebbe fatto
	#    fallire la certificazione GIA' FATTA con «il giro non e' arrivato in
	#    fondo» — cioe' con la frase sbagliata.
	local giro="f25-$nome-$(date +%s)"
	[ "$BERSAGLIO" = prodotto ] && giro="f25p-$nome-$(date +%s)"
	GIRI+=("$giro")
	# ⛔ La scena viaggia nell'indirizzo e finisce in OGNI riga del registro:
	#    su Linux il decodificatore HEVC di Chrome e' quello della piattaforma,
	#    e senza GPU non c'e'.  Lo stesso browser da' due risposte diverse su
	#    due schermi, e un numero senza la scena accanto e' due numeri sotto la
	#    stessa etichetta (`LEZIONI.md` §1.1, forma E2).
	# ⛔ La scena dice anche SE E' FINTA O VERA, per esteso: «:10» da solo non
	#    lo dice a chi rilegge fra sei mesi, e la differenza fra i due vale
	#    `arriva` contro `non-arriva` su HEVC.
	local scena
	if [ "$SCHERMO" = ":0" ] || [ -n "${SCHERMO_VERO:-}" ]; then
		scena="schermo-VERO-$SCHERMO"
	else
		scena="xvfb-FINTO-$SCHERMO-$TELA"
	fi
	local url="http://127.0.0.1:$PORTA/$PAGINA?giro=$giro&scena=$scena"
	[ -n "$GUASTO" ] && url="$url&guasta=$GUASTO"

	local prima_richieste=0
	[ -f "$T/racc.log" ] && prima_richieste=$(grep -c '^richiesta: ' "$T/racc.log")

	mkdir -p "$T/$nome"
	env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO "$@" "$url" >"$T/$nome.log" 2>&1 &
	PID_BR=$!

	if attendi_fine "$giro" "$ATTESA"; then
		ok "$nome ha finito il giro $giro"
	else
		ko "$nome non ha scritto la riga FINITO entro $ATTESA s"
		# ⛔ IL DENOMINATORE: distinguere le quattro cause di «nessun esito».
		local dopo
		dopo=$(grep -c '^richiesta: ' "$T/racc.log")
		inf "richieste al raccoglitore durante il giro: $((dopo - prima_richieste))"
		if [ "$((dopo - prima_richieste))" -eq 0 ]; then
			inf "⛔ ZERO richieste: il browser non ha nemmeno aperto la pagina."
			inf "   Non e' una misura su WebCodecs — e' il browser che non parte."
		else
			inf "⛔ la pagina si e' aperta e non ha finito: le righe scritte"
			inf "   fin qui sono un giro a meta', e il verdetto lo dira'."
		fi
		if grep -q '404' "$T/racc.log"; then
			inf "⚠ ci sono dei 404 nel registro del raccoglitore:"
			grep '404' "$T/racc.log" | head -5 | sed 's/^/        /'
		fi
		tail -8 "$T/$nome.log" | sed 's/^/        /'
		ESITO=1
	fi

	kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; PID_BR=
	sleep 1
	return 0
}

for m in $MOTORI; do
	case "$m" in
	chrome)
		# ⚠ Nessun `--enable-features`: si misura il Chrome che l'utente ha.
		#   Un flag che accende una strada che il browser di serie non ha
		#   produce un `[M]` che non vale per nessun utente (E10).
		prova_motore chrome google-chrome google-chrome \
			--ozone-platform=x11 --user-data-dir="$T/profilo-chrome" \
			--no-first-run --no-default-browser-check --disable-sync \
			--disable-features=Translate --window-size=1000,900
		;;
	firefox)
		# ⚠ Idem: profilo nuovo, nessuna preferenza toccata.
		# ⛔ La cartella del profilo si CREA prima, e niente `--width/--height`:
		#    `[M]` 12 agosto 2026, Firefox 140 ESR — con quelle due opzioni il
		#    browser non apriva la pagina affatto, e il banco ha registrato
		#    «ZERO richieste al raccoglitore».  ⭐ Il denominatore ha fatto
		#    esattamente il suo mestiere: senza, quel giro sarebbe stato letto
		#    come «Firefox non decodifica niente» invece che «Firefox non e'
		#    partito» (`LEZIONI.md` §1.9).
		mkdir -p "$T/profilo-firefox"
		prova_motore firefox firefox firefox --no-remote \
			--profile "$T/profilo-firefox"
		;;
	*)
		ko "motore sconosciuto: $m"
		ESITO=1
		;;
	esac
done

# ---------------------------------------------------------------------------
log "5. Il verdetto — lo calcola il banco, fuori dal browser (B0.4)"

if [ "${#GIRI[@]}" -eq 0 ]; then
	ko "nessun motore e' stato provato: non e' un esito, e' un banco che non ha"
	ko "   misurato niente"
	exit 1
fi
python3 "$QUI/02-pagina-verdetto.py" "${GIRI[@]}"
VERDETTO=$?
[ "$VERDETTO" -ne 0 ] && ESITO=1

# ---------------------------------------------------------------------------
log "6. Il controllo positivo in coda — lo strumento sa trovare quel che c'e'?"

# ⛔ Tre domande, e non sono una formalita': sono le tre cose che, se rotte,
#    farebbero leggere ogni giro futuro come «non e' successo niente».
RIGHE_GIRO=$(python3 - "$REGISTRO" "${GIRI[@]}" <<'PY'
import json, os, sys
percorso, giri = sys.argv[1], set(sys.argv[2:])
n = 0
if os.path.exists(percorso):
    for riga in open(percorso, encoding="utf-8"):
        try:
            d = json.loads(riga)
        except Exception:
            continue
        if d.get("giro") in giri:
            n += 1
print(n)
PY
)
if [ "$RIGHE_GIRO" -gt 0 ]; then
	ok "il registro ha $RIGHE_GIRO righe di questo giro (il raccoglitore riceve"
	ok "   e il lettore le ritrova: «zero righe» sarebbe stato distinguibile)"
else
	ko "ZERO righe di questo giro nel registro: il portatore degli esiti non"
	ko "   funziona, e ogni misura di questo banco sarebbe illeggibile"
	ESITO=1
fi

RICHIESTE=$(grep -c '^richiesta: ' "$T/racc.log")
if [ "$RICHIESTE" -gt 0 ]; then
	ok "il raccoglitore ha servito $RICHIESTE richieste (il denominatore c'e')"
else
	ko "ZERO richieste al raccoglitore: nessun browser ha aperto la pagina"
	ESITO=1
fi

PIXEL=$(ls "$QUI/02-pagina-pixel" 2>/dev/null | wc -l)
inf "PNG dei pixel dipinti su disco: $PIXEL  (in banchi/02-pagina-pixel/)"
inf "⛔ Sono la consegna a F2.6: il confronto vero lo fa lei, sui pixel, non"
inf "   sul verdetto di questo banco."

log "Esito"
# ⛔ LA SCENA E IL BERSAGLIO NELLA RIGA DI ESITO, non solo nel registro: due
#    giri con numeri diversi e la stessa riga d'esito sono due numeri sotto la
#    stessa etichetta (forma E2).
if [ "$SCHERMO" = ":0" ] || [ -n "${SCHERMO_VERO:-}" ]; then
	inf "scena: schermo VERO $SCHERMO — il browser vede la GPU, e su Linux e'"
	inf "       li' che HEVC esiste (VA-API).  ⚠ E' una scelta, non un caso."
else
	inf "scena: Xvfb FINTO $SCHERMO ${TELA}x24 — nessuna GPU.  ⛔ Su questa scena"
	inf "       HEVC non arriva al pixel su Chrome, ed e' MISURATO: e' la scena,"
	inf "       non il prodotto.  Il ripiego AV1 arriva lo stesso."
fi
inf "bersaglio: $BERSAGLIO ($PAGINA)"
if [ "$ESITO" -eq 0 ]; then
	ok "F2.5: il giro e' andato, e il banco e' valido"
else
	ko "F2.5: qualcosa non torna — vedi sopra"
fi
inf "il dettaglio riga per riga sta in $REGISTRO"
inf "⚠ Un «no» su HEVC NON e' un rosso del banco: e' una misura, e va letta"
inf "   in §5 (DECISIONI.md §2.7 — l'altezza la mette il client)."
exit "$ESITO"
