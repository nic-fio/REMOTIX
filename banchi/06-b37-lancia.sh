#!/bin/bash
#
# 06-b37-lancia.sh — SOTTOFASE 6.5, «la pagina e i numeri del browser».
#                    `SPECIFICHE.md` §6.1-bis · §6.2 · §6.4 · `RCP.md` §7.1, §4.5
#
#   bash banchi/06-b37-lancia.sh                    tutte le scene, tutti e due i motori
#   bash banchi/06-b37-lancia.sh chrome numeri      una scena, un motore
#   bash banchi/06-b37-lancia.sh firefox pixel
#   SCHERMO=:0 bash banchi/06-b37-lancia.sh chrome pixel    sullo schermo VERO
#
# ⚠ GIRA DA QUESTA PARTE DEL FILO — sul portatile: i browser stanno di qua, e
#   nessuna di queste tre scene ha bisogno del server.  ⛔ Quel che il server
#   deve confermare (la scala 1,000 con un fotogramma VERO) sta in
#   `06-b37-filo.sh` e vuole la macchina di prova.
#
# ===========================================================================
# ⛔ DA CHE PARTE SI STA MISURANDO — si dichiara, perche' sono due mestieri
#
#   `numeri`  la PAGINA e basta: `misura_vista()`, `tela_da_chiedere()`, lo
#             zoom, l'arrotondamento, i lati dispari.  Nessuna iniezione.
#   `pixel`   la PAGINA con un fotogramma FINTO iniettato, e il verdetto si
#             legge sui PIXEL dello schermo X, non sulle variabili che li hanno
#             prodotti (invariante **I8**).  ⛔ L'iniezione e' dichiarata in ogni
#             riga di esito (`iniezione: si`).
#   `voce`    il messaggio `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)` INIETTATO
#             nella pagina — ⛔ non arriva dal filo, e si dice.
#
# ⚠ Su Xvfb il pezzo fra «disegno finito» e «pixel acceso» non esiste
#   (`STUDI.md` §web §6.2): qui non si dichiara nessun tempo.  Si dichiara la
#   GEOMETRIA, che su Xvfb e' la stessa — e dove non lo e' (il ricampionamento
#   lo fa il rasterizzatore) sta scritto nel verdetto della scena `pixel`.
# ===========================================================================
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
RADICE=$(cd "$QUI/.." && pwd)

MOTORE=${1:-tutti}
SCENA=${2:-tutte}

PORTA=${PORTA:-8871}
SCHERMO=${SCHERMO:-:79}
TELA_X=${TELA_X:-1600x1000x24}
ESITI=${ESITI:-$QUI/06-b37-esiti.jsonl}
# ⛔⭐ IL FATTORE DI SCALA DEL DISPOSITIVO — e NON e' lo zoom di pagina.
#    Windows scala il sistema al 125 % o al 150 %: il browser nasce con
#    `devicePixelRatio` gia' non intero, senza che nessuno prema `Ctrl +`.
#    ⚠ `[M]` 16 agosto 2026: il PC dell'utente e' al **125 %**, cioe' dpr 1,25 —
#      un valore che sul portatile non esiste e che nessuna misura di questo
#      progetto aveva mai visto.  Qui si finge, e si dichiara che si finge.
FATTORE=${FATTORE:-}
T=$(mktemp -d)

log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf -- '    --  %s\n' "$*"; }

ESITO=0
PID_X=; PID_RACC=; PID_BR=

congedo()
{
	[ -n "$PID_BR" ]   && { kill "$PID_BR"   2>/dev/null; wait "$PID_BR"   2>/dev/null; }
	[ -n "$PID_RACC" ] && { kill "$PID_RACC" 2>/dev/null; wait "$PID_RACC" 2>/dev/null; }
	[ -n "$PID_X" ]    && { kill "$PID_X"    2>/dev/null; wait "$PID_X"    2>/dev/null; }
	rm -rf "$T"
}
trap congedo EXIT

# ---------------------------------------------------------------------------
log "1. La copia strumentata — e il prodotto resta intatto"
PAGINA=$T/pagina.html
# ⛔ Di suo si strumenta IL PRODOTTO.  ⚠ `SORGENTE=` serve a una cosa sola, ed e'
#    la 3.4 di `CODER.md`: rimettere in piedi la pagina PRIMA di una cura, per
#    far vedere al banco il difetto vivo.  Chi lo usa lo dichiara nel rapporto.
SORGENTE=${SORGENTE:-$RADICE/src/pagina.html}
python3 "$QUI/06-b37-strumenta.py" "$SORGENTE" "$PAGINA" \
	|| { ko "strumentazione fallita"; exit 2; }
inf "$(wc -l < "$SORGENTE") righe di prodotto + la sonda"
[ "$SORGENTE" = "$RADICE/src/pagina.html" ] || inf "⚠ NON e' il prodotto: $SORGENTE"

# ---------------------------------------------------------------------------
log "2. Lo schermo finto, e la verita' fuori dal browser"
if [ "$SCHERMO" = ":0" ]; then
	inf "⚠ schermo VERO: si apriranno finestre sulla scrivania"
else
	Xvfb "$SCHERMO" -screen 0 "$TELA_X" >"$T/xvfb.log" 2>&1 &
	PID_X=$!
	sleep 2
	[ -d "/proc/$PID_X" ] || { ko "Xvfb non e' partito:"; sed 's/^/        /' "$T/xvfb.log"; exit 2; }
fi
FUORI=$(env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO xdpyinfo 2>/dev/null \
	| sed -n 's/^  dimensions: *\([0-9]*x[0-9]*\) pixels.*/\1/p' | head -1)
[ -n "$FUORI" ] || { ko "xdpyinfo non risponde su $SCHERMO"; exit 2; }
ok "schermo $SCHERMO, risoluzione letta con xdpyinfo: $FUORI"

# ---------------------------------------------------------------------------
log "3. Il raccoglitore"
python3 -u "$QUI/06-b37-raccogli.py" "$PORTA" "$PAGINA" "$ESITI" >"$T/racc.log" 2>&1 &
PID_RACC=$!
sleep 1
[ -d "/proc/$PID_RACC" ] || { ko "il raccoglitore non e' partito:"; sed 's/^/        /' "$T/racc.log"; exit 3; }
ok "raccoglitore su 127.0.0.1:$PORTA (esiti in $ESITI)"

# ---------------------------------------------------------------------------
# accendi_motore <nome> — apre il browser sulla pagina, e lascia il pid in PID_BR
accendi_motore()
{
	local nome=$1 coda=${2:-}
	local url="http://127.0.0.1:$PORTA/pagina.html?giro=$nome-$(date +%s)$coda"
	rm -rf "$T/profilo-$nome"; mkdir -p "$T/profilo-$nome"
	case $nome in
	chrome)
		command -v google-chrome >/dev/null || return 1
		local scala=()
		[ -n "$FATTORE" ] && scala=(--force-device-scale-factor="$FATTORE")
		env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO google-chrome \
			--ozone-platform=x11 --user-data-dir="$T/profilo-$nome" \
			--no-first-run --no-default-browser-check --disable-sync \
			--disable-features=Translate --window-size=1200,760 \
			"${scala[@]}" \
			--window-position=0,0 "$url" >"$T/$nome.log" 2>&1 &
		;;
	firefox)
		command -v firefox >/dev/null || return 1
		# ⛔ Il profilo e' PROPRIO e nuovo a ogni giro: uno zoom ricordato da un
		#    giro precedente e' una scena che non hai dichiarato.
		cat >"$T/profilo-$nome/user.js" <<-'PREF'
		user_pref("browser.shell.checkDefaultBrowser", false);
		user_pref("datareporting.policy.firstRunURL", "");
		user_pref("datareporting.policy.dataSubmissionEnabled", false);
		user_pref("browser.aboutwelcome.enabled", false);
		user_pref("browser.startup.homepage_override.mstone", "ignore");
		user_pref("browser.zoom.siteSpecific", false);
		PREF
		# ⚠ Su Gecko il fattore del dispositivo e' una preferenza, non
		#   un'opzione: `layout.css.devPixelsPerPx`.  ⛔ E i passi dello zoom di
		#   pagina di Firefox NON contengono il 125 % (110-120-133-150): senza
		#   questa preferenza il caso dell'utente Windows su Firefox NON si
		#   riproduce affatto.
		[ -n "$FATTORE" ] && printf 'user_pref("layout.css.devPixelsPerPx", "%s");\n' \
			"$FATTORE" >>"$T/profilo-$nome/user.js"
		env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO firefox --no-remote \
			--profile "$T/profilo-$nome" --width 1200 --height 760 \
			"$url" >"$T/$nome.log" 2>&1 &
		;;
	*) return 1 ;;
	esac
	PID_BR=$!
	return 0
}

spegni_motore()
{
	[ -n "$PID_BR" ] && { kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; }
	PID_BR=
	sleep 2
}

# gira_scena <motore> <scena>
gira_scena()
{
	local nome=$1 scena=$2 script=
	case $scena in
	numeri) script=$QUI/06-b37-numeri.py ;;
	pixel)  script=$QUI/06-b37-pixel.py ;;
	voce)   script=$QUI/06-b37-voce.py ;;
	sfora)  script=$QUI/06-b37-sfora.py ;;
	coordinate) script=$QUI/06-b37-coordinate.py ;;
	windows) script=$QUI/06-b37-windows.py ;;
	modi)   script=$QUI/06-b37-modi.py ;;
	*) ko "scena sconosciuta: $scena"; return 2 ;;
	esac
	log "$nome · scena «$scena»${FATTORE:+ · fattore del dispositivo $FATTORE}"
	if ! accendi_motore "$nome"; then
		inf "⚠ $nome non c'e' su questa macchina: si salta, E SI DICE"
		return 0
	fi
	FATTORE="$FATTORE" python3 -u "$script" "$PORTA" "$SCHERMO" "$PID_BR" "$nome" "$ESITI"
	local e=$?
	[ "$e" -ne 0 ] && ESITO=1
	spegni_motore
	return 0
}

MOTORI=$MOTORE
[ "$MOTORE" = tutti ] && MOTORI="chrome firefox"
SCENE=$SCENA
[ "$SCENA" = tutte ] && SCENE="numeri pixel sfora coordinate modi voce"

for m in $MOTORI; do
	for s in $SCENE; do
		gira_scena "$m" "$s"
	done
done

log "Esito"
if [ "$ESITO" -eq 0 ]; then
	ok "06-b37: tutte le scene chieste hanno dato il verdetto atteso"
else
	ko "06-b37: qualcosa non torna — vedi sopra"
fi
inf "⛔ resta NON MISURATO: il DeX vero (il telefono ce l'ha l'utente) e il"
inf "   ricampionamento su GPU vera — qui rasterizza il software di Xvfb"
inf "riga per riga: $ESITI"
exit "$ESITO"
