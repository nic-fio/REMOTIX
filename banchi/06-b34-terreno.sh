#!/bin/bash
#
# 06-b34-terreno.sh — ⛔ GIRA SUL SERVER (NIC-OS), **FUORI** dal contenitore e
# **DA ROOT**.  Il terreno della SOTTOFASE 6.2 — *la tastiera che rinasce*.
#
#   sudo bash .../06-b34-terreno.sh utente          crea `provat6` (uid 1007)
#   sudo bash .../06-b34-terreno.sh sessione        GNOME **senza** --virtual-monitor
#   sudo bash .../06-b34-terreno.sh disposizione it la disposizione DELLA SESSIONE
#   sudo bash .../06-b34-terreno.sh disposizione-leggi
#   sudo bash .../06-b34-terreno.sh testimone       ⭐ il testimone DENTRO la sessione
#   sudo bash .../06-b34-terreno.sh testimone-azzera
#   sudo bash .../06-b34-terreno.sh testimone-leggi
#   sudo bash .../06-b34-terreno.sh testimone-via
#   sudo bash .../06-b34-terreno.sh accendi         il server sulla 7721
#   sudo bash .../06-b34-terreno.sh spegni
#   sudo bash .../06-b34-terreno.sh registro [n]    la coda del registro
#   sudo bash .../06-b34-terreno.sh ricambi         ⭐ i ricambi di tastiera CONTATI
#   sudo bash .../06-b34-terreno.sh pulisci
#
# ===========================================================================
# ⛔ IL MODELLO E' `04-b31-terreno.sh`, COPIATO E ADATTATO — non modificato
# ===========================================================================
#
# Le cinque regole dell'isolamento (`fasi/06-la-tela-e-la-vista.md` §0-bis):
# utente proprio (`provat6`), porta propria (7721), ban/socket/certificati
# propri.  ⛔ `prova` e la 7700 NON SI TOCCANO.
#
# ⭐ E nel gruppo `render` **e** `video`: senza, il codificatore ripiega in
#    software e il banco misurerebbe il ripiego (`[M]` 4,8 ms → 100 ms).
#
# ⛔ E **senza** `--virtual-monitor`: e' la cura di A1.
#
# ===========================================================================
# ⭐⭐ CHE COSA QUESTO TERRENO HA IN PIU' DI QUELLO DI `04-b31`
# ===========================================================================
#
#  1. ⛔ **`disposizione`** — cambia la disposizione **della sessione**, che e'
#     l'unica cosa che fa davvero rinascere il dispositivo tastiera di `libei`
#     (`STUDI.md` §gnome §9: un cambio di keymap **distrugge e ricrea** il
#     dispositivo, e il puntatore al vecchio smette di funzionare **senza
#     errore**).  ⚠ Si passa da `gsettings org.gnome.desktop.input-sources`,
#     cioe' dalla strada che un utente vero percorre — non da una scorciatoia
#     interna a Mutter che il prodotto non vedrebbe mai;
#
#  2. ⛔⭐ **`testimone`** — un terminale **DENTRO la sessione grafica** che
#     scrive ogni carattere che gli arriva, **col suo istante**.  `CODER.md`
#     §3.8: il registro di chi manda dice che ha chiamato una funzione, non che
#     il byte e' arrivato.  ⛔ Un desktop vuoto non testimonia niente.
#
#     ⚠ E il carattere si scrive **in esadecimale UTF-8**, non com'e': `z`, `y`,
#       `è` e l'a-capo hanno tutti l'aspetto di «qualcosa» in un file di testo,
#       e la differenza fra `y` (79) e `z` (7a) e' **esattamente** la misura di
#       questa sottofase.  Un testimone che stampasse il carattere e basta
#       renderebbe indistinguibili «e' arrivato l'altro» e «non e' arrivato
#       niente» per ogni carattere non stampabile.
set -uo pipefail

PORTA=${PORTA:-7721}
IND=${IND:-192.168.0.2}
UTENTE=${UTENTE:-provat6}
UID_B=${UID_B:-1007}
PAROLA=${PAROLA:-provat6-2026}
D=${D:-/media/REMOTIX/src/06-t-src/src}
LAV=${LAV:-/media/REMOTIX/tmp/06-t}
LIBS=${LIBS:-/media/REMOTIX/src/b2/ngtcp2/build/lib:/media/REMOTIX/src/b2/ngtcp2/build/crypto/ossl:/media/REMOTIX/src/b2/prefisso/lib}
UNITA=org.gnome.Shell@wayland.service

CERT=$LAV/certificati
BAN=$LAV/ban
SOCK=$LAV/comando.sock
LOG=$LAV/registro.log
PIDF=$LAV/pid
RILIEVO=$LAV/rilievo
TEST=/home/$UTENTE/testimone.txt
BANCHI=${BANCHI:-$(cd "$(dirname "$0")" && pwd)}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I GRUPPI DELLA SCHEDA SI DANNO IN UN POSTO SOLO — `attrezzi-gruppi-scheda.sh`
#
# ⛔ Qui c'era `usermod -aG render,video` (o niente affatto), coi NOMI
#    INCHIODATI e senza rileggere: due difetti in una riga sola.  La ragione
#    per cui la cura sta in un file a parte, e i numeri che la giustificano,
#    stanno nel riquadro in testa a quel file — ⛔ non si ricopiano qui, o
#    diventano dieci posti da cui divergere (`LEZIONI.md` §1.47).
# ═══════════════════════════════════════════════════════════════════════════
GRUPPI_SCHEDA_SH=${GRUPPI_SCHEDA_SH:-$(cd "$(dirname "$0")" && pwd)/attrezzi-gruppi-scheda.sh}
[ -f "$GRUPPI_SCHEDA_SH" ] || { ko "⛔ manca $GRUPPI_SCHEDA_SH: senza, l'inquilino nascerebbe CIECO"; exit 2; }
. "$GRUPPI_SCHEDA_SH"


# ⛔ Le porte che NON sono mie: si CONTANO prima e dopo, non si toccano.
vicini() {
	local r=""
	for p in 7448 7501 7561 7571 7601 7691 7700 7711 7781 7731 7751 7761; do
		r="$r$p:$(ss -tuln 2>/dev/null | grep -c ":$p\b") "
	done
	printf '%s— ascoltatori (NON miei)\n' "$r"
}

# ⛔ Tutto quel che va fatto DENTRO la sessione dell'utente passa di qui: uid,
#    gid, ambiente composto da zero (`CODER.md` §4.5).
come_utente() {
	setpriv --reuid="$UID_B" --regid="$UID_B" --init-groups \
		env -i \
		HOME="/home/$UTENTE" USER="$UTENTE" SHELL= LANG=C.UTF-8 \
		PATH=/usr/local/bin:/usr/bin:/bin \
		XDG_RUNTIME_DIR="/run/user/$UID_B" \
		DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$UID_B/bus" \
		XDG_CURRENT_DESKTOP=GNOME XDG_SESSION_DESKTOP=gnome \
		XDG_SESSION_TYPE=wayland \
		"$@"
}

mio_pid() {
	local p
	if [ -f "$PIDF" ]; then
		p=$(cat "$PIDF" 2>/dev/null)
		[ -n "$p" ] && [ -d "/proc/$p" ] && { echo "$p"; return 0; }
	fi
	p=$(pgrep -f "remotix .*--porta $PORTA" | head -1)
	[ -n "$p" ] && { echo "$p"; return 0; }
	return 1
}

# ⛔ Il figlio di QUESTO server: si cerca fra i figli del MIO pid.  Un
#    `pgrep -f -- --figlio-interno` prenderebbe i figli degli altri anelli, che
#    girano sulla stessa macchina (cinque banchi in parallelo).
mio_figlio() {
	local s f
	s=$(mio_pid) || return 1
	for f in $(pgrep -P "$s" 2>/dev/null); do
		[ -r "/proc/$f/cmdline" ] || continue
		case "$(tr '\0' ' ' < "/proc/$f/cmdline" 2>/dev/null)" in
		*--figlio-interno*) echo "$f"; return 0 ;;
		esac
	done
	return 1
}

[ "$(id -u)" -eq 0 ] || { ko "⛔ va lanciato DA ROOT"; exit 2; }
mkdir -p "$LAV"

case "${1:-stato}" in
utente)
	log "L'utente della sottofase 6.2: $UTENTE (uid $UID_B)"
	inf "$(vicini)"
	if id "$UTENTE" >/dev/null 2>&1; then
		ok "c'e' gia' — non lo rifaccio (una sessione per utente, I2)"
	else
		useradd -m -u "$UID_B" -s /bin/bash "$UTENTE" || {
			ko "⛔ useradd non e' riuscito"; exit 2; }
		ok "creato"
	fi
	printf '%s:%s\n' "$UTENTE" "$PAROLA" | chpasswd || {
		ko "⛔ la parola d'ordine non e' stata posta: PAM dira' sempre di no"
		exit 2; }
	ok "parola d'ordine posta"
	# ⭐ `render` E `video`: senza, il codificatore ripiega in software e lo
	#    dichiara — `[M]` 100 ms per fotogramma invece di 4,8.
	# ⛔ Qui c'erano i due nomi INCHIODATI, e un `usermod` fallito non fermava
	#    niente: il banco tirava dritto e misurava una sessione cieca.
	gruppi_scheda_dai_a "$UTENTE" || exit 3
	inf "gruppi: $(id -nG "$UTENTE")"
	loginctl enable-linger "$UTENTE" || { ko "⛔ enable-linger fallito"; exit 2; }
	ok "linger acceso: /run/user/$UID_B vivra' anche senza nessuno collegato"
	exit 0 ;;

sessione)
	log "La sessione GNOME di $UTENTE — ⭐ SENZA --virtual-monitor"
	inf "$(vicini)"
	id "$UTENTE" >/dev/null 2>&1 || { ko "⛔ l'utente non c'e': fai «utente»"; exit 2; }

	DIR="/run/user/$UID_B/systemd/user.control/$UNITA.d"
	FILE="$DIR/zz-senza-monitor.conf"
	install -d -o "$UID_B" -g "$UID_B" -m 700 "$DIR" || { ko "⛔ non ho fatto $DIR"; exit 2; }
	printf '[Service]\nExecStart=\nExecStart=/usr/bin/gnome-shell --headless --no-x11\n' > "$FILE"
	chown "$UID_B:$UID_B" "$FILE"
	inf "scritto $FILE"

	if pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1; then
		ok "c'e' gia' una sessione viva — non la rifaccio"
		exit 0
	fi

	come_utente systemctl --user reset-failed >/dev/null 2>&1
	g=0
	while [ $g -lt 40 ]; do
		come_utente systemctl --user is-active gnome-session-manager@gnome.service \
			>/dev/null 2>&1 || break
		sleep 0.5; g=$((g+1))
	done
	come_utente systemctl --user daemon-reload || { ko "⛔ daemon-reload"; exit 2; }
	come_utente systemctl --user reset-failed >/dev/null 2>&1
	come_utente systemctl --user start pipewire.socket pipewire-pulse.socket >/dev/null 2>&1
	come_utente systemctl --user start pipewire.service wireplumber.service >/dev/null 2>&1
	if come_utente systemctl --user is-active pipewire.service >/dev/null 2>&1; then
		ok "PipeWire e' vivo"
	else
		ko "⚠ PipeWire NON e' vivo: la cattura non trovera' nessun nodo"
	fi
	# ⛔ SCRITTO NON E' IN VIGORE (forma E1): si rilegge dal gestore.
	VIG=$(come_utente systemctl --user show -p ExecStart --value "$UNITA")
	inf "ExecStart in vigore: $VIG"
	case "$VIG" in *--no-x11*) ok "c'e' «--no-x11»" ;;
		*) ko "⛔ «--no-x11» NON c'e'"; exit 3 ;;
	esac
	case "$VIG" in *--virtual-monitor*)
		ko "⛔ c'e' ancora «--virtual-monitor»: la scena non e' quella che credo"
		exit 3 ;;
	*) ok "e NON c'e' «--virtual-monitor»" ;;
	esac

	come_utente setsid --fork sh -c \
		"exec >>/run/user/$UID_B/remotix-sessione.log 2>&1; exec gnome-session --session=gnome"
	g=0
	while [ $g -lt 120 ]; do
		if pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 \
		   && come_utente busctl --user list 2>/dev/null | grep -q org.gnome.Shell; then
			break
		fi
		sleep 0.5; g=$((g+1))
	done
	pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 || {
		ko "⛔ la sessione non e' partita in $((g/2)) s"
		tail -20 "/run/user/$UID_B/remotix-sessione.log" 2>&1 | sed 's/^/        /'
		exit 3; }
	ok "sessione viva dopo $((g/2)) s"
	exit 0 ;;

disposizione)
	# ⛔⭐ LA DISPOSIZIONE **DELLA SESSIONE** — ed e' l'unica leva che fa
	#     rinascere il dispositivo tastiera di `libei`.
	#
	# ⚠ Si passa da `gsettings`, cioe' dalla strada che percorre un utente vero
	#   che cambia disposizione dalle impostazioni di GNOME.  ⛔ Non da una
	#   scorciatoia interna: una leva che il prodotto non vedrebbe mai in
	#   esercizio proverebbe un percorso che non esiste.
	Q=${2:-it}
	log "La disposizione DELLA SESSIONE → «$Q»"
	pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 || {
		ko "⛔ la sessione non c'e': non c'e' niente da cambiare"; exit 2; }
	PRIMA=$(come_utente gsettings get org.gnome.desktop.input-sources sources 2>&1)
	inf "prima: $PRIMA"
	come_utente gsettings set org.gnome.desktop.input-sources sources \
		"[('xkb','$Q')]" || { ko "⛔ gsettings set non e' riuscito"; exit 3; }
	# ⚠ E anche `current`, o GNOME resta sull'indice di prima quando la lista
	#   si accorcia.
	come_utente gsettings set org.gnome.desktop.input-sources current 0 >/dev/null 2>&1
	sleep 2
	DOPO=$(come_utente gsettings get org.gnome.desktop.input-sources sources 2>&1)
	inf "dopo:  $DOPO"
	# ⛔ SCRITTO NON E' IN VIGORE: si RILEGGE, e si guarda che sia cambiato.
	case "$DOPO" in *"'$Q'"*) ok "in vigore: $DOPO" ;;
		*) ko "⛔ NON e' in vigore: $DOPO"; exit 3 ;;
	esac
	exit 0 ;;

disposizione-leggi)
	printf 'DISPOSIZIONE %s\n' \
		"$(come_utente gsettings get org.gnome.desktop.input-sources sources 2>&1)"
	exit 0 ;;

testimone)
	# ⛔⭐ IL TESTIMONE STA **DENTRO** LA SESSIONE GRAFICA (`CODER.md` §3.8).
	#
	# Un terminale nel desktop, e dentro un ciclo che legge **un carattere per
	# volta** e scrive l'istante in nanosecondi accanto ai suoi byte UTF-8 in
	# esadecimale.
	#
	# ⛔ Perche' l'esadecimale e non il carattere: la misura di questa sottofase
	#    e' *«e' arrivata la `z` o la `y`?»*, e in un file di testo `z`, `y`,
	#    `è`, l'a-capo e «niente» hanno tutti l'aspetto di qualcosa.  In
	#    esadecimale `7a` e `79` non si confondono, e l'assenza si vede.
	#
	# ⚠ E il file sta nella HOME dell'utente, non in `/tmp`: cinque banchi
	#   girano su questa macchina e `/tmp/testimone.txt` sarebbe di tutti.
	log "Il testimone, DENTRO la sessione di $UTENTE"
	pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 || {
		ko "⛔ la sessione non c'e': un desktop vuoto non testimonia niente"; exit 2; }
	# ⛔⛔ SI PARTE DA UNA FINESTRA SOLA, E SI VERIFICA — `[M]` 16 agosto 2026.
	#
	#     `pkill -f 'banco-T6-testimone'` NON trova niente: quel testo sta negli
	#     argomenti di `gnome-terminal`, che e' un client sottile ed esce
	#     subito; il ciclo vero e' un `bash -c` la cui riga di comando contiene
	#     il PERCORSO DEL FILE, non il titolo.  ⇒ A ogni riaccensione si
	#     accumulava una finestra in piu': **cinque**, alla fine, e il fuoco
	#     finiva su una qualunque di loro.
	#     ⚠ Il sintomo era un testimone VUOTO — cioe' l'aspetto di «il carattere
	#       non e' arrivato» mentre arrivava a una finestra sorella.
	# ⇒ Si butta giu' il SERVER dei terminali, che e' l'unico modo di essere
	#   certi che dopo non ci sia nessun'altra finestra.
	come_utente pkill -u "$UID_B" -f '06-b34-testimone.py' >/dev/null 2>&1
	come_utente pkill -u "$UID_B" -f 'gnome-terminal-server' >/dev/null 2>&1
	sleep 2
	n=$(pgrep -u "$UID_B" -f 'gnome-terminal-server' 2>/dev/null | wc -l)
	if [ "$n" -ne 0 ]; then
		ko "⛔ IL BANCO: restano $n gnome-terminal-server, il fuoco sara' ambiguo"
		exit 3
	fi
	: > "$TEST"; chown "$UID_B:$UID_B" "$TEST"
	# ⛔⭐⭐ `stty -isig -ixon` — E SENZA, LA PROVA DI `Ctrl+Z` NON ESISTE.
	#
	#     La scena che conta (`DECISIONI.md` §5-bis.6) e' **`Ctrl+Z` su
	#     disposizione diversa**: le lettere viaggiano come lettere, le
	#     scorciatoie come POSIZIONI, e su una tastiera tedesca la `Z` sta dove
	#     da noi sta la `Y`.  ⇒ In un terminale la differenza si legge benissimo:
	#
	#         Ctrl+Z → byte **1a**        Ctrl+Y → byte **19**
	#
	#     ⛔ Ma di suo il driver del terminale **non li consegna**: `ISIG` fa di
	#        `Ctrl+Z` un SIGTSTP, che **sospende il testimone** invece di
	#        scrivere una riga — e il file resterebbe vuoto, cioe' l'aspetto di
	#        «non e' arrivato niente».  E `IXON` si mangia `Ctrl+S`/`Ctrl+Q`.
	#     ⇒ Si spengono tutt'e due: cosi' la scorciatoia arriva come **byte**, e
	#       il testimone misura la POSIZIONE che il compositore ha risolto.
	# ⛔ Il testimone e' un programma a parte (`06-b34-testimone.py`), e NON un
	#    ciclo `bash`: `read -N` di bash rimette `ISIG` a ogni giro, e `Ctrl+Z`
	#    diventava SIGTSTP invece di arrivare come byte — cioe' il file restava
	#    vuoto proprio sulla prova che questa sottofase esiste per fare.
	#    Il perche' per intero sta in testa a quel file.
	come_utente setsid --fork gnome-terminal --title=banco-T6-testimone -- \
		python3 "$BANCHI/06-b34-testimone.py" "$TEST" \
		>/dev/null 2>&1
	g=0
	while [ $g -lt 40 ]; do
		grep -q PRONTO "$TEST" 2>/dev/null && break
		sleep 0.5; g=$((g+1))
	done
	if ! grep -q PRONTO "$TEST" 2>/dev/null; then
		ko "⛔ il testimone non ha scritto PRONTO in $((g/2)) s: non c'e' terminale"
		exit 3
	fi
	ok "testimone acceso dopo $((g/2)) s — $TEST"
	# ⛔ SCRITTO NON E' IN VIGORE: si conta, e se non e' UNA sola si dice.
	m=$(pgrep -u "$UID_B" -f 'gnome-terminal-server' 2>/dev/null | wc -l)
	c=$(pgrep -u "$UID_B" -f '06-b34-testimone.py' 2>/dev/null | wc -l)
	inf "gnome-terminal-server: $m · cicli che scrivono nel testimone: $c"
	[ "$c" -eq 1 ] || ko "⛔ IL BANCO: i cicli sono $c, non 1 — il fuoco e' ambiguo"
	exit 0 ;;

testimone-azzera)
	: > "$TEST"; chown "$UID_B:$UID_B" "$TEST"
	printf 'AZZERATO %s\n' "$(date +%s%N)"
	exit 0 ;;

testimone-leggi)
	cat "$TEST" 2>/dev/null
	exit 0 ;;

testimone-via)
	come_utente pkill -u "$UID_B" -f '06-b34-testimone.py' 2>/dev/null
	ok "testimone spento"
	exit 0 ;;

accendi)
	log "Il server della sottofase 6.2, sulla $PORTA — DA ROOT"
	inf "$(vicini)"
	[ -x "$D/remotix" ] || { ko "⛔ $D/remotix non c'e'"; exit 2; }
	[ -f "$D/pagina.html" ] || { ko "⛔ $D/pagina.html non c'e'"; exit 2; }
	n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
	[ "$n" -eq 0 ] || { ko "⛔ la $PORTA e' gia' occupata"; exit 2; }
	[ -f /etc/pam.d/remotix ] || { ko "⛔ /etc/pam.d/remotix non c'e'"; exit 2; }
	mkdir -p "$CERT" "$RILIEVO"; chmod 1777 "$RILIEVO"
	: > "$LOG"
	export LD_LIBRARY_PATH="$LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
	ldd "$D/remotix" | grep -q 'not found' && {
		ko "⛔ manca una libreria:"; ldd "$D/remotix" | grep 'not found' | sed 's/^/        /'
		exit 2; }
	# ⛔ `--parlantina`: il figlio senza tace IN SILENZIO, e `registro_dettaglio()`
	#    finisce nel nulla.  L'assenza di una riga non e' la prova che il ramo
	#    non e' scattato (trappola 1 del documento di fase).
	nohup "$D/remotix" --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
		--certificati "$CERT" --pagina "$D/pagina.html" \
		--ban-file "$BAN" --comando-socket "$SOCK" \
		--rilievo "$RILIEVO" --parlantina >> "$LOG" 2>&1 &
	pid=$!; echo "$pid" > "$PIDF"
	g=0
	while [ $g -lt 60 ]; do
		[ -d "/proc/$pid" ] || break
		[ "$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")" -ge 2 ] && break
		sleep 0.5; g=$((g+1))
	done
	[ -d "/proc/$pid" ] || { ko "⛔ il server e' morto subito:"; tail -20 "$LOG" | sed 's/^/        /'; exit 3; }
	ok "acceso, pid $pid, $(ss -tuln | grep -c ":$PORTA\b") ascoltatori"
	inf "$(vicini)"
	exit 0 ;;

registro)
	tail -n "${2:-120}" "$LOG" 2>/dev/null
	exit 0 ;;

registro-cerca)
	grep -n -- "${2:-tastiera}" "$LOG" 2>/dev/null | tail -n "${3:-60}"
	exit 0 ;;

ricambi)
	# ⭐ I RICAMBI SI LEGGONO, NON SI DEDUCONO.  `input.c:521-523` scrive una
	#    riga numerata a ogni `DEVICE_REMOVED` della tastiera.
	# ⛔ E si stampa anche lo ZERO: «nessun ricambio» e «non ho guardato» hanno
	#    lo stesso aspetto se si stampa solo quando c'e' qualcosa.
	printf 'RICAMBI_TASTIERA %s\n' \
		"$(grep -c 'la tastiera e. stata TOLTA dal compositore' "$LOG" 2>/dev/null || echo 0)"
	printf 'RICAMBI_PUNTATORE %s\n' \
		"$(grep -c 'il puntatore e. stato TOLTO dal compositore' "$LOG" 2>/dev/null || echo 0)"
	printf 'KEYMAP_CAMBIATA %s\n' \
		"$(grep -c 'KEYMAP CAMBIATA' "$LOG" 2>/dev/null || echo 0)"
	printf 'RILASCI %s\n' \
		"$(grep -c 'rilascio al distacco' "$LOG" 2>/dev/null || echo 0)"
	grep -h 'KEYMAP CAMBIATA\|la tastiera e. stata TOLTA\|rilascio al distacco\|disposizione in vigore' \
		"$LOG" 2>/dev/null | tail -30
	exit 0 ;;

figlio)
	if f=$(mio_figlio); then printf 'FIGLIO %s\n' "$f"; else printf 'FIGLIO nessuno\n'; fi
	printf 'REGISTRO_BYTE %s\n' "$(stat -c %s "$LOG" 2>/dev/null || echo 0)"
	printf 'CARICO %s\n' "$(uptime | sed 's/.*average: //')"
	exit 0 ;;

spegni)
	log "Spengo la $PORTA"
	if ! pid=$(mio_pid); then ok "non c'era niente sulla $PORTA"; exit 0; fi
	miei=""
	for f in $(pgrep -P "$pid" 2>/dev/null); do
		[ -r "/proc/$f/cmdline" ] || continue
		case "$(tr '\0' ' ' < /proc/$f/cmdline 2>/dev/null)" in
		*--figlio-interno*) miei="$miei $f" ;;
		esac
	done
	kill "$pid" 2>/dev/null
	g=0; while [ -d "/proc/$pid" ] && [ $g -lt 30 ]; do sleep 0.5; g=$((g+1)); done
	[ -d "/proc/$pid" ] && kill -9 "$pid" 2>/dev/null
	rm -f "$PIDF"
	restano=""
	for f in $miei; do
		[ -r "/proc/$f/cmdline" ] || continue
		case "$(tr '\0' ' ' < /proc/$f/cmdline 2>/dev/null)" in
		*--figlio-interno*) restano="$restano $f" ;;
		esac
	done
	if [ -z "$restano" ]; then ok "spento, e nessun figlio MIO e' rimasto orfano"
	else ko "⛔ figli MIEI orfani:$restano"; for f in $restano; do kill -9 "$f" 2>/dev/null; done; fi
	inf "$(vicini)"
	exit 0 ;;

pulisci)
	log "Tolgo l'utente della sottofase 6.2"
	bash "$0" spegni
	come_utente gdbus call --session -d org.gnome.SessionManager \
		-o /org/gnome/SessionManager -m org.gnome.SessionManager.Logout 2 \
		>/dev/null 2>&1
	sleep 3
	loginctl disable-linger "$UTENTE" 2>/dev/null
	pkill -u "$UID_B" 2>/dev/null; sleep 2; pkill -9 -u "$UID_B" 2>/dev/null
	userdel -r "$UTENTE" 2>&1 | sed 's/^/        /'
	ok "fatto"
	inf "$(vicini)"
	exit 0 ;;

stato|*)
	log "Stato — sottofase 6.2, porta $PORTA, utente $UTENTE"
	inf "$(vicini)"
	inf "utente $UTENTE: $(id "$UTENTE" 2>&1)"
	for p in $(pgrep -u "$UID_B" -x gnome-shell 2>/dev/null); do
		inf "gnome-shell $p: $(tr '\0' ' ' < /proc/$p/cmdline)"
	done
	inf "disposizione: $(come_utente gsettings get org.gnome.desktop.input-sources sources 2>&1)"
	if pid=$(mio_pid); then inf "server $PORTA: pid $pid"; else inf "server $PORTA: spento"; fi
	if f=$(mio_figlio); then inf "figlio: $f"; else inf "figlio: nessuno"; fi
	inf "registro: $(stat -c %s "$LOG" 2>/dev/null || echo 0) byte"
	inf "testimone: $(wc -l < "$TEST" 2>/dev/null || echo 0) righe"
	inf "carico: $(uptime | sed 's/.*average: //')"
	exit 0 ;;
esac
