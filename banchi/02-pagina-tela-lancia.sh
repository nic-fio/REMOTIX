#!/bin/bash
#
# 02-pagina-tela-lancia.sh — che cosa fa un `VideoDecoder` VERO quando la tela
#                            cambia a meta' sessione.  `RCP.md` §5.2 · §6.2 · §7.1
#
#   SCHERMO=:10 SCHERMO_VERO=1 bash banchi/02-pagina-tela-lancia.sh
#   MOTORI=chrome  …                                   uno solo
#   GUASTO=lettore …                                   con un guasto innestato
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' QUESTO BANCO ESISTE
#
# `RCP.md` §6.2 e' stato corretto oggi: la misura di un fotogramma vale la
# **tela IN VIGORE**, e §7.1 la lascia cambiare a meta' sessione.  ⛔ Ne segue
# un buco: §5.2 impone una **chiave** dopo `SESSIONE`, ma dopo un
# `TELA(ADATTATA)` il decodificatore riparte da zero **una seconda volta**, e
# nessuna riga dice che il primo fotogramma alla misura nuova debba essere una
# chiave.
#
# ⚠ E il buco non si cura scrivendo la riga.  §5.2 si motiva con un `[S]` —
#   *«il decodificatore non solleva errori»* — che su questo caso NON e' stato
#   misurato da nessuno.  Se il decodificatore protesta, il client se ne accorge
#   e la riga rende poco; se **dipinge spazzatura in silenzio**, e' la forma di
#   P6 di F2.5 e la riga va scritta.
#
# ---------------------------------------------------------------------------
# ⛔ E SI MISURA SU DUE MOTORI **E SU DUE CODEC**, e non e' pignoleria
#
# `DECISIONI.md` §1.13: HEVC con un **ripiego negoziato**, e il ripiego e' AV1.
# ⇒ Il prodotto avra' DUE percorsi di decodifica, non uno.  Una regola di
#   `RCP.md` scritta misurando un codec solo sarebbe una regola verificata su
#   meta' degli utenti — la forma **E10**.  `[M]` 12 ago 2026 (F2.5): HEVC
#   arriva al pixel **solo** su Chrome con la GPU; AV1 dipinge in tutte e
#   quattro le caselle.  Se i due codec si comportassero diversamente **qui**,
#   quella e' la scoperta.
#
# ---------------------------------------------------------------------------
# ⚠ LA SCENA, DICHIARATA — e su HEVC decide la risposta
#
# `[M]` 12 ago 2026 (F2.5 §1): su Linux il decodificatore HEVC di Chrome e'
# quello della **piattaforma** (VA-API).  Su uno schermo finto non c'e' GPU e
# **ogni** stringa HEVC viene rifiutata.  ⇒ Su Xvfb questo banco misurerebbe
# HEVC su un motore che HEVC non ce l'ha, e i suoi zeri non direbbero niente
# sulla domanda posta.  Per questo la scena di riferimento e' lo schermo VERO
# `:10` — il display di GNOME di questa macchina (⚠ `:0` qui non esiste).
#
# ⛔ Porta **7533**, che e' quella assegnata a questo giro: la 7515 e' di F2.5,
#    la 7448 e la 7501 stanno su NIC-OS e non si toccano, la 7452 e' di S1b.
#
# ---------------------------------------------------------------------------
# ⛔ IL CATALOGO DELLE CERTIFICAZIONI — chi scrive un banco lo certifica nello
#    stesso giro (regola nata l'11 agosto), e l'atteso e' scritto PRIMA.
#
# | nome | comando | atteso sano | guasto | atteso guasto |
# |---|---|---|---|---|
# | `f25t-sequenze` | `python3 banchi/02-pagina-tela-sequenze.py` | 4 sequenze,
#   due misure diverse e due pattern diversi, e il primo pezzo si accorcia
#   togliendo i parameter set | costruire le due tele con lo stesso pattern |
#   ⛔ si ferma: «ha dipinto il nuovo» e «tiene il vecchio» non si
#   distinguerebbero |
# | `f25t-lettore` | `… GUASTO=lettore …` | P2 verde (1/8 su tela grigia), e i
#   casi b1/b2 su HEVC **SBAGLIATI** | il classificatore risponde sempre «la
#   tinta attesa» | ⛔ **P2 rosso (8/8)** e b1/b2 che diventano **GIUSTI**.
#   `[M]` 12 ago 2026: come atteso ⇒ il «SBAGLIATI» viene DAVVERO dai pixel |
# | `f25t-muto` | `… GUASTO=muto …` | ogni caso che protesta esce `…/ERRORE` |
#   i testi degli errori vengono buttati dal giudizio | ⛔ ogni `…/ERRORE`
#   diventa `…/MUTO`.  `[M]` 12 ago 2026: come atteso ⇒ «in silenzio» questo
#   banco lo sa vedere, e non e' una parola.  ⚠ Il registro conserva i testi
#   apposta: un giro guasto deve restare diagnosticabile |
# | `f25t-intero` | `SCHERMO=:10 SCHERMO_VERO=1 bash banchi/02-pagina-tela-lancia.sh` |
#   P1/P2 verdi a TUTT'E DUE le misure, (a) e P7 verdi su ogni codec presente,
#   uscita 0 | — | — |
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
PORTA=${PORTA:-7533}
SCHERMO=${SCHERMO:-:76}
TELA=${TELA:-1280x1024}
MOTORI=${MOTORI:-chrome firefox}
GUASTO=${GUASTO:-}
ATTESA=${ATTESA:-180}
REGISTRO=$QUI/02-pagina-tela-esiti.jsonl
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
log "1. Le sequenze — due tele, due pattern, due codec"

if ! python3 "$QUI/02-pagina-tela-sequenze.py" --elenca; then
	inf "le sequenze non ci sono (o non sono quattro): si costruiscono adesso"
	if ! python3 "$QUI/02-pagina-tela-sequenze.py"; then
		ko "le sequenze non si costruiscono: senza flusso non c'e' misura"
		exit 2
	fi
fi

# ---------------------------------------------------------------------------
log "2. Lo schermo"

if [ "$SCHERMO" = ":0" ] || [ -n "${SCHERMO_VERO:-}" ]; then
	inf "⚠ schermo VERO ($SCHERMO): il browser vedra' la GPU — e su HEVC quella"
	inf "   e' meta' della misura (F2.5 §1)"
	if ! env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO xdpyinfo >"$T/xdpyinfo.txt" 2>&1; then
		ko "il display $SCHERMO non risponde: non c'e' niente su cui aprire"
		sed -n '1,4p' "$T/xdpyinfo.txt" | sed 's/^/        /'
		exit 2
	fi
	inf "risoluzione letta fuori dal browser: $(sed -n 's/^  dimensions: *\([0-9]*x[0-9]*\) pixels.*/\1/p' "$T/xdpyinfo.txt" | head -1)"
else
	# ⛔ `:76`, e non `:75` (F2.5) ne' `:78` (S5) ne' `:10`/`:1024`/`:1025` (in
	#    uso): due banchi sullo stesso display si rubano il fuoco.
	Xvfb "$SCHERMO" -screen 0 "${TELA}x24" >"$T/xvfb.log" 2>&1 &
	PID_X=$!
	sleep 2
	if [ ! -d "/proc/$PID_X" ]; then
		ko "Xvfb non e' partito:"
		sed 's/^/        /' "$T/xvfb.log"
		exit 2
	fi
	inf "schermo finto $SCHERMO, chiesto ${TELA}x24"
	inf "⚠ su questa scena HEVC non ha GPU e sara' zero: e' un fatto gia'"
	inf "   misurato (F2.5 §1), non una misura di questo banco"
fi

# ---------------------------------------------------------------------------
log "3. Il raccoglitore, sulla porta $PORTA"

if ss -ltn "sport = :$PORTA" | grep -q ":$PORTA"; then
	ko "la porta $PORTA e' gia' occupata:"
	ss -ltnp "sport = :$PORTA" | sed 's/^/        /'
	exit 3
fi

python3 -u "$QUI/02-pagina-tela-raccogli.py" "$PORTA" >"$T/racc.log" 2>&1 &
PID_RACC=$!
sleep 1
if [ ! -d "/proc/$PID_RACC" ]; then
	ko "il raccoglitore non e' partito:"
	sed 's/^/        /' "$T/racc.log"
	exit 3
fi
ok "raccoglitore su 127.0.0.1:$PORTA"

# ---------------------------------------------------------------------------
# ⛔ Si cerca **il giro**, non «l'ultima riga» (rilievo R8.10).
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

prova_motore()
{
	local nome=$1 binario=$2; shift 2
	log "4. $nome"
	if ! command -v "$binario" >/dev/null; then
		inf "⚠ $binario non c'e' su questa macchina: si salta, E SI DICE"
		return 0
	fi
	inf "versione: $("$binario" --version 2>&1 | head -1)"

	local giro="f25t-$nome-$(date +%s)"
	GIRI+=("$giro")
	local scena="$SCHERMO-$TELA"
	[ "$SCHERMO" = ":0" ] || [ -n "${SCHERMO_VERO:-}" ] || scena="xvfb-$scena"
	local url="http://127.0.0.1:$PORTA/02-pagina-tela-prova.html?giro=$giro&scena=$scena"
	[ -n "$GUASTO" ] && url="$url&guasta=$GUASTO"

	local prima_richieste=0
	[ -f "$T/racc.log" ] && prima_richieste=$(grep -c '^richiesta: ' "$T/racc.log")

	env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO "$@" "$url" >"$T/$nome.log" 2>&1 &
	PID_BR=$!

	if attendi_fine "$giro" "$ATTESA"; then
		ok "$nome ha finito il giro $giro"
	else
		ko "$nome non ha scritto la riga FINITO entro $ATTESA s"
		# ⛔ IL DENOMINATORE: le tre cause di «nessun esito» hanno lo stesso
		#    aspetto, e senza questo conto la seconda si legge come la prima.
		local dopo
		dopo=$(grep -c '^richiesta: ' "$T/racc.log")
		inf "richieste al raccoglitore durante il giro: $((dopo - prima_richieste))"
		if [ "$((dopo - prima_richieste))" -eq 0 ]; then
			inf "⛔ ZERO richieste: il browser non ha nemmeno aperto la pagina."
			inf "   Non e' una misura su WebCodecs — e' il browser che non parte."
		else
			inf "⛔ la pagina si e' aperta e non ha finito: le righe scritte fin"
			inf "   qui sono un giro a meta', e il verdetto lo dira'."
		fi
		grep '404' "$T/racc.log" | head -5 | sed 's/^/        /'
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
		prova_motore chrome google-chrome google-chrome \
			--ozone-platform=x11 --user-data-dir="$T/profilo-chrome" \
			--no-first-run --no-default-browser-check --disable-sync \
			--disable-features=Translate --window-size=1000,900
		;;
	firefox)
		# ⛔ Niente `--width/--height`: `[M]` 12 ago 2026, con quelle Firefox 140
		#    non apriva la pagina affatto (F2.5, «che cosa non ha funzionato» 5).
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
log "5. Il verdetto — lo calcola il banco, fuori dal browser"

if [ "${#GIRI[@]}" -eq 0 ]; then
	ko "nessun motore provato: non e' un esito, e' un banco che non ha misurato"
	exit 1
fi
python3 "$QUI/02-pagina-tela-verdetto.py" "${GIRI[@]}"
VERDETTO=$?
[ "$VERDETTO" -ne 0 ] && ESITO=1

# ---------------------------------------------------------------------------
log "6. Il controllo positivo in coda"

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
	ok "il registro ha $RIGHE_GIRO righe di questo giro"
else
	ko "ZERO righe di questo giro: il portatore degli esiti non funziona"
	ESITO=1
fi

RICHIESTE=$(grep -c '^richiesta: ' "$T/racc.log")
if [ "$RICHIESTE" -gt 0 ]; then
	ok "il raccoglitore ha servito $RICHIESTE richieste (il denominatore c'e')"
else
	ko "ZERO richieste al raccoglitore: nessun browser ha aperto la pagina"
	ESITO=1
fi

log "Esito"
if [ "$ESITO" -eq 0 ]; then
	ok "il giro e' andato, e il banco e' valido"
else
	ko "qualcosa non torna — vedi sopra"
fi
inf "il dettaglio riga per riga sta in $REGISTRO"
exit "$ESITO"
