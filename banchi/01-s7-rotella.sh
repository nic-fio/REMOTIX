#!/bin/bash
#
# 01-s7-rotella.sh — S7: da che parte gira la rotella.  `RCP.md` §7.3
#
#   bash 01-s7-rotella.sh            la misura intera, e rimette la macchina com'era
#   bash 01-s7-rotella.sh --tieni    la stessa, ma lascia in piedi il monitor virtuale
#
# ⚠ GIRA SUL SERVER (192.168.0.2), dentro la sessione dell'utente.  Il browser
#   di questa misura NON e' quello del portatile: la pagina deve stare
#   **dentro** il compositore in cui iniettiamo, o non misura il compositore.
#
# ---------------------------------------------------------------------------
# CHE COSA MISURA
#
# `RCP.md` §7.3 tiene `[?]` il SEGNO della rotella: il client manda `+120`
# perche' l'utente ha girato la rotella **in su**, e nessuno sa se il server
# debba iniettare `+120` o `-120` per far andare lo schermo remoto dalla stessa
# parte.  Questo banco inietta con `libei` — la strada del prodotto — e guarda
# che cosa arriva alla pagina.
#
# ⭐ E la pagina e' lo strumento GIUSTO, non uno comodo: `deltaY` dell'evento
#    `wheel` e' la stessa grandezza che il client di RCP legge quando l'utente
#    gira la rotella davvero.  Il confronto e' fra due usi della stessa
#    convenzione, non fra due mondi.
#
# ---------------------------------------------------------------------------
# ⛔ I TRE CONTROLLI, E DUE DI LORO SONO QUELLI CHE DICONO *NO*
#
#   1. IL SEGNO OPPOSTO.  Si inietta anche `-120`.  Se la pagina va dalla
#      stessa parte, non si sta misurando il segno: si sta misurando che
#      «qualcosa si muove».  ⭐ E' il controllo che la prima stesura del banco
#      aveva gia' scritto giusto.
#
#   2. `natural-scroll` NEI DUE STATI.  Se il segno cambia con la gsetting,
#      il numero che finirebbe in `RCP.md` §7.3 sarebbe **il segno della
#      configurazione di QUESTA scrivania**, e il sintomo per l'utente sarebbe
#      «la rotella va al contrario» su meta' delle installazioni — forma E11.
#      ⛔ E' il controllo che mancava (rilievo R3.25).
#
#      ⛔ E L'INIETTORE SI RIFA' DA CAPO A OGNI STATO.  Un compositore puo'
#         leggere le preferenze del dispositivo **quando il dispositivo
#         nasce**: cambiando la gsetting sotto a un dispositivo gia' vivo, il
#         controllo direbbe «il segno non cambia» anche in un mondo dove
#         cambia — cioe' sarebbe cieco proprio nel caso che deve vedere.
#
#   3. IL SILENZIO.  Alla fine si sta fermi dieci secondi senza iniettare
#      niente e si verifica che la pagina NON registri scatti.  Senza, «la
#      pagina ha visto uno scatto» non dimostra che l'abbiamo mandato noi.
#
# E due controlli positivi sullo strumento, prima di tutti: la pagina dichiara
# di essersi messa a 8 000 pixel dal bordo (se il documento non scorre, ogni
# «non si e' mossa» che segue non vorrebbe dire niente — `LEZIONI.md` §1.9
# regola 2), e dichiara la misura dello schermo che vede, che deve essere
# quella del monitor virtuale che abbiamo chiesto.
#
# ---------------------------------------------------------------------------
# ⛔ LO STATO INIZIALE, DICHIARATO E VERIFICATO (B0.1)
#
#   - una sessione GNOME viva e headless (`00-sessione-gnome.sh stato`);
#   - ⛔ **un monitor**.  Una Shell `--headless` senza `--virtual-monitor` ha
#     ZERO monitor logici (`[M]` 10 agosto 2026: `GetCurrentState` risponde
#     `[]`), e senza monitor non c'e' una finestra dove mandare uno scatto.
#     ⚠ E `RecordVirtual` da solo NON basta: misurato, i monitor restano zero
#     finche' un consumatore PipeWire non negozia la misura.  Quindi qui si
#     aggiunge `--virtual-monitor` all'unita' della Shell, si riavvia, **e si
#     verifica sulla riga di comando del processo** che l'opzione sia in
#     vigore — non che sia scritta nel file (`LEZIONI.md` §1.11);
#   - i due `natural-scroll` di partenza (mouse e touchpad), che si rimettono.
#
# ⛔ E TUTTO QUEL CHE SI CAMBIA SI DICHIARA E SI RIMETTE: il drop-in di
#    systemd, le gsetting, la sessione.  Uno stato che sopravvive alla prova
#    falsa la prova dopo — regola B0.2, scritta per l'eccezione del
#    certificato ma vera anche per una scrivania.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
PORTA=${PORTA:-8877}
REGISTRO=$QUI/01-s7-esiti.jsonl
SESSIONE_SH=${SESSIONE_SH:-/media/REMOTIX/tmp/00-sessione-gnome.sh}
DROPIN_DIR=$HOME/.config/systemd/user/org.gnome.Shell@wayland.service.d
# ⛔ `zz-`, e il nome NON e' estetica: `[M]` 10 agosto 2026.  systemd ordina i
#    drop-in **per nome di file**, mescolando le cartelle — non per precedenza
#    della cartella.  La fase 0 ha messo il suo in
#    `/etc/systemd/user/…/remotix-headless.conf`, e un file chiamato
#    `99-s7-…` gli finisce PRIMA: il primo giro di questo banco ha scritto il
#    drop-in, riavviato la sessione, e trovato la Shell ancora senza
#    `--virtual-monitor`.  ⭐ L'ha detto il controllo B0.1 — «si verifica sulla
#    riga di comando del processo, non sul file» — invece di misurare per
#    mezz'ora una finestra che non esisteva.
DROPIN=$DROPIN_DIR/zz-s7-monitor-virtuale.conf
TELA=${TELA:-1920x1080}
PAROLA=${PAROLA:-nicfio}
TIENI=0
[ "${1:-}" = --tieni ] && TIENI=1

export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=$XDG_RUNTIME_DIR/bus}

# ---------------------------------------------------------------------------
# ⛔ `--pulisci`, e serve a chiudere un buco che questo banco ha aperto da se'.
#
#    `[M]` 10 agosto 2026: con `--tieni` il drop-in resta.  Il giro dopo trova
#    la Shell **gia'** con `--virtual-monitor`, conclude «non l'ho messo io» e
#    non lo toglie: lo stato resta sulla macchina di tutti, e nessuno dei due
#    giri ha fatto niente di sbagliato.  E' la regola B0.2 vista dal lato di
#    chi lo stato lo lascia invece di trovarlo.
# ---------------------------------------------------------------------------
if [ "${1:-}" = --pulisci ]; then
	if [ -f "$DROPIN" ]; then
		rm -f "$DROPIN"
		systemctl --user daemon-reload
		printf 'tolto %s: riavvio la sessione\n' "$DROPIN"
		bash "$SESSIONE_SH" ferma
		bash "$SESSIONE_SH" avvia
		printf 'gnome-shell adesso: %s\n' \
		    "$(tr '\0' ' ' < "/proc/$(pgrep -u "$(id -u)" -x gnome-shell | head -1)/cmdline")"
	else
		printf 'nessun drop-in di S7 da togliere\n'
	fi
	exit 0
fi

T=$(mktemp -d)
log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

ESITO=0
DROPIN_NOSTRO=0
MOUSE_PRIMA=
TOUCH_PRIMA=
PID_FF=
PID_INI=
PID_RACC=

ferma_iniettore()
{
	[ -z "$PID_INI" ] && return 0
	exec 9>&- 2>/dev/null
	kill "$PID_INI" 2>/dev/null
	wait "$PID_INI" 2>/dev/null
	PID_INI=
}

congedo()
{
	printf '\n\033[1m== Il congedo\033[0m\n'
	[ -n "$PID_FF" ]   && { kill "$PID_FF"   2>/dev/null; wait "$PID_FF"   2>/dev/null; }
	ferma_iniettore
	[ -n "$PID_RACC" ] && { kill "$PID_RACC" 2>/dev/null; wait "$PID_RACC" 2>/dev/null; }
	if [ -n "$MOUSE_PRIMA" ]; then
		gsettings set org.gnome.desktop.peripherals.mouse natural-scroll "$MOUSE_PRIMA"
		gsettings set org.gnome.desktop.peripherals.touchpad natural-scroll "$TOUCH_PRIMA"
		inf "natural-scroll rimesso: mouse=$MOUSE_PRIMA touchpad=$TOUCH_PRIMA"
	fi
	if [ "$DROPIN_NOSTRO" = 1 ] && [ "$TIENI" = 0 ]; then
		rm -f "$DROPIN"
		systemctl --user daemon-reload
		inf "tolto il drop-in $DROPIN: la sessione torna com'era"
		bash "$SESSIONE_SH" ferma
		bash "$SESSIONE_SH" avvia
	elif [ "$DROPIN_NOSTRO" = 1 ]; then
		inf "⚠ IL DROP-IN RESTA ($DROPIN): la sessione ha ancora un monitor virtuale"
	fi
	rm -rf "$T"
}
trap congedo EXIT

# ---------------------------------------------------------------------------
log "1. Lo stato iniziale (B0.1)"

bash "$SESSIONE_SH" stato
if ! pgrep -u "$(id -u)" -x gnome-shell >/dev/null; then
	inf "non c'e' una sessione: la avvio"
	bash "$SESSIONE_SH" avvia || { ko "la sessione non parte: la misura non comincia"; exit 2; }
fi

riga_shell() { tr '\0' ' ' < "/proc/$(pgrep -u "$(id -u)" -x gnome-shell | head -1)/cmdline"; }

RIGA=$(riga_shell)
inf "gnome-shell: $RIGA"
case "$RIGA" in
*--virtual-monitor*)
	ok "la Shell ha gia' un monitor virtuale: non tocco l'unita'"
	;;
*)
	inf "nessun monitor virtuale: aggiungo il drop-in e riavvio la sessione"
	mkdir -p "$DROPIN_DIR"
	cat >"$DROPIN" <<CONF
[Service]
ExecStart=
ExecStart=/usr/bin/gnome-shell --headless --no-x11 --virtual-monitor $TELA
CONF
	DROPIN_NOSTRO=1
	systemctl --user daemon-reload
	bash "$SESSIONE_SH" ferma || { ko "la sessione non si e' fermata"; exit 2; }
	bash "$SESSIONE_SH" avvia || { ko "la sessione non e' ripartita"; exit 2; }
	RIGA=$(riga_shell)
	inf "gnome-shell adesso: $RIGA"
	# ⛔ Si verifica sulla RIGA DI COMANDO DEL PROCESSO, non sul file: che
	#    l'opzione sia scritta non e' che sia in vigore.
	case "$RIGA" in
	*--virtual-monitor*) ok "il monitor virtuale e' in vigore" ;;
	*)  ko "il drop-in non ha avuto effetto: la Shell gira senza --virtual-monitor"; exit 2 ;;
	esac
	;;
esac
sleep 2
gdbus call --session -d org.gnome.Mutter.DisplayConfig -o /org/gnome/Mutter/DisplayConfig \
    -m org.gnome.Mutter.DisplayConfig.GetCurrentState >"$T/monitor.txt" 2>&1
inf "DisplayConfig dice (primi 300 caratteri):"
printf '        %s\n' "$(cut -c1-300 "$T/monitor.txt")"

MOUSE_PRIMA=$(gsettings get org.gnome.desktop.peripherals.mouse natural-scroll)
TOUCH_PRIMA=$(gsettings get org.gnome.desktop.peripherals.touchpad natural-scroll)
inf "natural-scroll di partenza: mouse=$MOUSE_PRIMA touchpad=$TOUCH_PRIMA (si rimettono in fondo)"

# ---------------------------------------------------------------------------
log "2. L'iniettore"

BIN=/media/REMOTIX/tmp/01-s7-rotella
inf "compilazione nel devroot (gcc e gli header di libei stanno li', non sul sistema)"
printf '%s\n' "$PAROLA" | bash /media/REMOTIX/enter.sh \
    "gcc -O1 -Wall -o /srv/src/01-s7-rotella-bin /srv/src/01-s7-rotella.c \
     \$(pkg-config --cflags --libs libei-1.0 gio-2.0 gio-unix-2.0)"
if [ ! -x /media/REMOTIX/src/01-s7-rotella-bin ]; then
	ko "l'iniettore non si e' compilato: vedi sopra"
	exit 3
fi
cp /media/REMOTIX/src/01-s7-rotella-bin "$BIN"
ok "iniettore compilato: $BIN"

# ---------------------------------------------------------------------------
log "3. Il raccoglitore"

python3 -u "$QUI/01-s7-raccogli.py" "$PORTA" >"$T/racc.log" 2>&1 &
PID_RACC=$!
sleep 1
if [ ! -d "/proc/$PID_RACC" ]; then
	ko "il raccoglitore non e' partito:"
	sed 's/^/        /' "$T/racc.log"
	exit 4
fi
ok "raccoglitore su 127.0.0.1:$PORTA"

systemctl --user show-environment >"$T/ambiente.txt" 2>&1
WD=$(sed -n 's/^WAYLAND_DISPLAY=//p' "$T/ambiente.txt" | head -1)
if [ -z "$WD" ]; then
	ko "la sessione non pubblica WAYLAND_DISPLAY: il browser non troverebbe il compositore"
	exit 4
fi
inf "WAYLAND_DISPLAY=$WD"
URL="http://127.0.0.1:$PORTA/01-s7-pagina.html"

# ---------------------------------------------------------------------------
# Il lettore del registro.
#
# ⛔ IL SEGNAPOSTO E' IL NUMERO DI RIGA DEL FILE, NON IL CONTATORE DELLA PAGINA.
#
#    `[M]` 10 agosto 2026, secondo giro di questo banco: il contatore della
#    pagina riparte da 1 a ogni caricamento.  Il registro conteneva gia' una
#    riga `n=1` del giro precedente, il segnaposto valeva 1, e la riga nuova —
#    `n=1` anche lei — non e' mai stata «maggiore del segnaposto».  Il banco ha
#    stampato «la pagina non ha detto PRONTA in 45 s» **mentre il raccoglitore
#    la stava scrivendo**: un rosso su strumento sano, e la causa vera era il
#    modo di cercare.
#
#    Adesso il segnaposto e' la posizione nel file (che cresce sempre) e la
#    riga si riconosce ANCHE dal marchio del giro, che la pagina sorteggia a
#    ogni caricamento.  Sono le due meta' del rilievo R8.10 di B2 insieme.
#
# Stampa: riga<TAB>giro<TAB>deltaY<TAB>scorrimento<TAB>partenza<TAB>schermo<TAB>motore
leggi_riga() # $1 = riga minima (esclusiva), $2 = tipo, $3 = marchio del giro (o vuoto)
{
	python3 - "$REGISTRO" "$1" "$2" "${3:-}" <<'PY'
import json, os, sys
percorso, minimo, tipo, giro = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
if not os.path.exists(percorso):
    sys.exit(1)
righe = open(percorso, encoding="utf-8").read().splitlines()
for i in range(minimo, len(righe)):
    try:
        d = json.loads(righe[i])
    except Exception:
        continue
    if d.get("tipo") != tipo:
        continue
    if giro and d.get("giro") != giro:
        continue
    print(i + 1, d.get("giro"), d.get("deltaY"), d.get("scorrimento"), d.get("partenza"),
          d.get("schermo"), (d.get("motore") or "")[:120], sep="\t")
    sys.exit(0)
sys.exit(1)
PY
}

attendi_riga() # $1 = riga minima, $2 = tipo, $3 = secondi, $4 = giro
{
	local i=0 trovata=""
	while [ "$i" -lt "${3:-20}" ]; do
		trovata=$(leggi_riga "$1" "$2" "${4:-}") && { printf '%s\n' "$trovata"; return 0; }
		sleep 1
		i=$((i + 1))
	done
	return 1
}

# ---------------------------------------------------------------------------
# ⛔⛔ L'ORDINE FRA INIETTORE E BROWSER, ED E' LA COSA PIU' CARA IMPARATA QUI.
#
# `[M]` 10 agosto 2026, dopo tre giri a vuoto:
#
#   - browser avviato PRIMA dell'iniettore  ⇒ alla pagina non arriva NIENTE:
#     ne' rotella, ne' bottoni, **ne' il movimento del puntatore**;
#   - iniettore avviato PRIMA del browser   ⇒ arriva tutto.
#
# E in tutt'e due i casi Mutter riceve l'iniezione: l'orologio
# dell'inattivita' (`org.gnome.Mutter.IdleMonitor.GetIdletime`) cade da 35 952
# ms a 1 013 ms al primo movimento.  Cioe' il compositore la prende e non la
# consegna alla finestra.
#
# ⚠ La spiegazione plausibile — una sessione senza dispositivi fisici annuncia
#   un `wl_seat` **senza puntatore**, e il cliente che parte prima non si
#   iscrive mai — resta `[?]`: non l'abbiamo verificata.  Quel che e' `[M]` e'
#   l'ordine.
#
# ⭐ E NON E' UN DETTAGLIO DI BANCO: nel prodotto la sessione grafica nasce
#    senza alcun dispositivo di input, e le applicazioni aperte **prima** che
#    un client si colleghi potrebbero trovarsi nello stesso stato — l'utente
#    muove il mouse e quella finestra non risponde.  E' una domanda per le
#    fasi 2 e 6, e va posta li' invece di essere riscoperta da un utente.
# ---------------------------------------------------------------------------
avvia_iniettore()
{
	mkfifo "$T/comandi.$$"
	"$BIN" <"$T/comandi.$$" >>"$T/iniettore.log" 2>&1 &
	PID_INI=$!
	exec 9>"$T/comandi.$$"
	rm -f "$T/comandi.$$"
	# ⛔ Si aspetta il dispositivo ASSOLUTO — riga intera, non prefisso:
	#    «PRONTO» e' l'inizio di «PRONTO-RELATIVO», e col relativo il puntatore
	#    finisce dove capita.  Solo se dopo venti secondi non arriva ci si
	#    accontenta del relativo, E LO SI DICE.
	local i=0
	while [ "$i" -lt 20 ]; do
		if grep -x "S7: PRONTO" "$T/iniettore.log" >/dev/null 2>&1; then
			return 0
		fi
		sleep 1
		i=$((i + 1))
	done
	if grep -x "S7: PRONTO-RELATIVO" "$T/iniettore.log" >/dev/null 2>&1; then
		inf "⚠ nessun dispositivo ASSOLUTO: si va in relativo, e la posizione del"
		inf "  puntatore non e' garantita"
		return 0
	fi
	return 1
}

avvia_browser()
{
	mkdir -p "$T/profilo"
	cat >"$T/profilo/user.js" <<'PREF'
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.reportingpolicy.firstRun", false);
user_pref("browser.sessionstore.resume_from_crash", false);
user_pref("general.smoothScroll", false);
PREF
	N=$(wc -l < "$REGISTRO" 2>/dev/null || echo 0)
	MOZ_ENABLE_WAYLAND=1 WAYLAND_DISPLAY="$WD" \
		firefox --kiosk --no-remote --profile "$T/profilo" "$URL" >"$T/firefox.log" 2>&1 &
	PID_FF=$!
	local pronta
	pronta=$(attendi_riga "$N" PRONTA 45)
	if [ -z "$pronta" ]; then
		ko "la pagina non ha detto PRONTA in 45 s."
		# ⛔ IL DENOMINATORE: il browser ha almeno CHIESTO la pagina?
		inf "richieste arrivate al raccoglitore: $(grep -c '^richiesta: ' "$T/racc.log")"
		inf "registro di Firefox:"
		tail -6 "$T/firefox.log" | sed 's/^/        /'
		return 1
	fi
	local partenza schermo motore
	IFS=$'\t' read -r N GIRO _ _ partenza schermo motore <<< "$pronta"
	ok "pagina viva (giro «$GIRO»).  motore: $motore"
	# ⛔ CONTROLLO POSITIVO 1 — il documento scorre davvero?
	if [ "$partenza" = 8000 ]; then
		ok "il documento scorre: la pagina si e' messa a $partenza px dal bordo"
	else
		ko "la pagina si e' messa a «$partenza» invece di 8000: il documento NON scorre,"
		ko "   e ogni «non si e' mossa» che segue non vorrebbe dire niente"
		return 1
	fi
	# ⛔ CONTROLLO POSITIVO 2 — lo schermo che la pagina vede e' il nostro monitor.
	if [ "$schermo" = "$TELA" ]; then
		ok "la pagina vede uno schermo $schermo, cioe' il monitor virtuale chiesto"
	else
		inf "⚠ la pagina vede uno schermo $schermo, chiesto $TELA: la misura del segno"
		inf "  regge lo stesso, ma la scena e' diversa da quella dichiarata"
	fi
	return 0
}

ferma_browser()
{
	[ -z "$PID_FF" ] && return 0
	kill "$PID_FF" 2>/dev/null
	wait "$PID_FF" 2>/dev/null
	PID_FF=
	sleep 2
}

# ---------------------------------------------------------------------------
ESITI=$T/esiti.tsv
: >"$ESITI"

giro() # $1 = etichetta, $2... = comando per l'iniettore
{
	local etichetta=$1; shift
	local riga n delta scorrimento

	printf 'centro\n' >&9
	sleep 1
	printf '%s\n' "$*" >&9
	riga=$(attendi_riga "$N" SCATTO 15 "$GIRO")
	if [ -z "$riga" ]; then
		ko "$etichetta: la pagina non ha registrato NIENTE"
		inf "l'iniettore dice:"
		tail -3 "$T/iniettore.log" | sed 's/^/        /'
		printf '%s\tNIENTE\tNIENTE\n' "$etichetta" >>"$ESITI"
		ESITO=1
		return 1
	fi
	IFS=$'\t' read -r n _ delta scorrimento _ _ _ <<< "$riga"
	N=$n
	printf '%s\t%s\t%s\n' "$etichetta" "$delta" "$scorrimento" >>"$ESITI"
	ok "$etichetta: deltaY=$delta  scorrimento=$scorrimento px"
	sleep 1
	return 0
}

# ⛔ IL DENOMINATORE, PRIMA DI OGNI SERIE: la strada dall'iniettore alla pagina
#    e' aperta?  Si muove il puntatore in tre punti e si guarda se la pagina lo
#    vede.  Senza, «non ha visto lo scatto» e «l'input non arriva affatto»
#    hanno lo stesso aspetto — ed e' esattamente il difetto che ha mangiato tre
#    giri di questo banco.
#    ⚠ `org.gnome.Shell.Introspect.GetWindows` sarebbe la strada breve per
#      sapere se c'e' una finestra, ma risponde «GetWindows is not allowed»
#      (`[M]` 10 agosto 2026): e' riservata alla Shell.
il_puntatore_arriva()
{
	local prima
	prima=$(wc -l < "$REGISTRO" 2>/dev/null || echo 0)
	printf 'muovi 400 300\n' >&9; sleep 1
	printf 'muovi 960 540\n' >&9; sleep 1
	printf 'muovi 500 700\n' >&9; sleep 1
	if leggi_riga "$prima" PUNTATORE "$GIRO" >/dev/null; then
		ok "la pagina VEDE muoversi il puntatore: la strada e' aperta"
		return 0
	fi
	ko "la pagina non vede nemmeno il PUNTATORE muoversi: quel che segue non"
	ko "   misurerebbe il segno della rotella, misurerebbe che l'input non arriva"
	return 1
}

for STATO in false true; do
	log "4. La scena, con natural-scroll = $STATO"
	gsettings set org.gnome.desktop.peripherals.mouse natural-scroll "$STATO"
	gsettings set org.gnome.desktop.peripherals.touchpad natural-scroll "$STATO"
	inf "letto indietro: mouse=$(gsettings get org.gnome.desktop.peripherals.mouse natural-scroll) touchpad=$(gsettings get org.gnome.desktop.peripherals.touchpad natural-scroll)"
	sleep 1
	# ⛔ Ordine: PRIMA l'iniettore, POI il browser.  E la scena si rifa' intera
	#    a ogni stato, cosi' anche il dispositivo nasce con la gsetting gia'
	#    cambiata — un compositore che legge le preferenze alla nascita del
	#    dispositivo renderebbe cieco un controllo fatto a dispositivo vivo.
	printf '\n--- iniettore, natural-scroll=%s ---\n' "$STATO" >>"$T/iniettore.log"
	if ! avvia_iniettore; then
		ko "l'iniettore non ha ottenuto un dispositivo:"
		sed 's/^/        /' "$T/iniettore.log"
		exit 6
	fi
	sed -n '/^--- iniettore, natural-scroll='"$STATO"'/,$p' "$T/iniettore.log" | sed 's/^/        /'
	if ! avvia_browser; then
		ferma_iniettore
		exit 5
	fi
	if ! il_puntatore_arriva; then
		ESITO=1
	fi
	giro "scatto+120/$STATO" "scatto 0 120"
	giro "scatto-120/$STATO" "scatto 0 -120"
	if [ "$STATO" = false ]; then
		# In piu': lo scorrimento liscio.  Il prodotto usa gli scatti, ma se
		# `ei_device_scroll_delta` avesse il segno opposto, il giorno che
		# qualcuno la usasse il difetto nascerebbe muto.
		giro "liscio+120/$STATO" "liscio 0 120"
	fi
	# ---------------------------------------------------------------------
	log "4-bis. Il controllo del silenzio (natural-scroll = $STATO)"
	inf "dieci secondi senza iniettare niente: la pagina NON deve registrare scatti"
	PRIMA_SILENZIO=$N
	sleep 10
	if leggi_riga "$PRIMA_SILENZIO" SCATTO "$GIRO" >/dev/null; then
		ko "la pagina ha registrato uno scatto che NESSUNO ha mandato:"
		ko "   allora «la pagina ha visto uno scatto» non dimostra che l'abbiamo mandato noi"
		leggi_riga "$PRIMA_SILENZIO" SCATTO "$GIRO" | sed 's/^/        /'
		ESITO=1
	else
		ok "silenzio: gli scatti registrati sono quelli iniettati"
	fi
	ferma_browser
	ferma_iniettore
done

# ---------------------------------------------------------------------------
log "5. Il verdetto — lo calcola il banco, non chi legge (B0.4)"
python3 - "$ESITI" <<'PY'
import sys

esiti = {}
for riga in open(sys.argv[1], encoding="utf-8"):
    parti = riga.rstrip("\n").split("\t")
    if len(parti) == 3:
        esiti[parti[0]] = parti[1:]

def segno(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return 0 if v == 0 else (1 if v > 0 else -1)

for nome in ("scatto+120/false", "scatto-120/false", "liscio+120/false",
             "scatto+120/true", "scatto-120/true"):
    d, s = esiti.get(nome, ("NIENTE", "NIENTE"))
    print(f"     {nome:20s} deltaY={d:>10}  scorrimento={s:>8}")

guasti = 0

def controlla(condizione, testo_ok, testo_no):
    global guasti
    if condizione:
        print("    \033[1;32mOK\033[0m ", testo_ok)
    else:
        print("    \033[1;31mNO\033[0m ", testo_no)
        guasti += 1

def d(nome):  return segno(esiti.get(nome, [None, None])[0])
def s(nome):  return segno(esiti.get(nome, [None, None])[1])

piu_f, meno_f = d("scatto+120/false"), d("scatto-120/false")
piu_t, meno_t = d("scatto+120/true"),  d("scatto-120/true")

print()
controlla(piu_f is not None and meno_f is not None and piu_f != 0 and piu_f == -meno_f,
          "+120 e -120 mandano la pagina da parti OPPOSTE: si sta misurando il segno",
          "+120 e -120 danno lo stesso verso (o zero): NON si sta misurando il segno, "
          "e il numero qui sotto non va scritto da nessuna parte")

controlla(s("scatto+120/false") is not None and s("scatto+120/false") == piu_f
          and s("scatto-120/false") == meno_f,
          "l'evento `wheel` e lo spostamento vero della pagina dicono la stessa cosa",
          "l'evento `wheel` e lo spostamento vero NON concordano: uno dei due strumenti "
          "sta guardando un'altra cosa")

controlla(piu_f is not None and piu_t is not None and piu_f == piu_t and meno_f == meno_t,
          "il segno NON cambia con `natural-scroll`: e' una proprieta' del percorso, "
          "non della scrivania di prova",
          "⛔ IL SEGNO CAMBIA CON `natural-scroll`: il numero sarebbe il segno di una "
          "gsetting, e il sintomo per l'utente «la rotella va al contrario» su meta' "
          "delle installazioni — forma E11")

controlla(d("liscio+120/false") is None or d("liscio+120/false") == piu_f,
          "`scroll_delta` e `scroll_discrete` concordano sul verso",
          "⚠ `ei_device_scroll_delta` ha il verso OPPOSTO a `ei_device_scroll_discrete`: "
          "il prodotto usa la seconda, ma chi usasse la prima nascerebbe col segno "
          "sbagliato e senza sintomo")

print()
if piu_f == -1:
    print("    LETTURA: ei_device_scroll_discrete(0, +120) da' deltaY NEGATIVO, cioe' manda")
    print("             il contenuto verso l'INIZIO del documento: +120 di libei == rotella")
    print("             girata IN SU, la stessa convenzione del `+120` del client (RCP §7.3).")
    print("    ⇒ il server RCP inietta il valore del client COSI' COM'E'.")
elif piu_f == +1:
    print("    LETTURA: ei_device_scroll_discrete(0, +120) da' deltaY POSITIVO, cioe' manda")
    print("             il contenuto verso la FINE del documento: +120 di libei == rotella")
    print("             girata IN GIU', l'opposto del `+120` del client (RCP §7.3).")
    print("    ⇒ il server RCP deve INVERTIRE il segno dell'asse verticale.")
else:
    print("    LETTURA: nessuna, e non e' un numero da scrivere da nessuna parte.")

sys.exit(1 if guasti else 0)
PY
[ $? -ne 0 ] && ESITO=1

log "Esito"
if [ "$ESITO" -eq 0 ]; then
	ok "S7 misurata, con i controlli"
else
	ko "S7: almeno un controllo e' caduto — vedi sopra.  ⛔ Il numero NON si scrive"
	ko "   in RCP.md §7.3 finche' i controlli non sono verdi"
fi
inf "il dettaglio riga per riga sta in $REGISTRO"
exit "$ESITO"
