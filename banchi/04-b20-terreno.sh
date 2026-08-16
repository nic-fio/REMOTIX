#!/bin/bash
#
# 04-b20-terreno.sh — ⛔ GIRA SUL SERVER (NIC-OS), **FUORI** dal contenitore e
# **DA ROOT**.  Prepara il terreno del banco A1 e accende il server sulla 7601.
#
#   sudo bash .../04-b20-terreno.sh utente          crea l'utente del banco
#   sudo bash .../04-b20-terreno.sh sessione con    GNOME **con** --virtual-monitor
#   sudo bash .../04-b20-terreno.sh sessione senza  GNOME **senza** (la cura)
#   sudo bash .../04-b20-terreno.sh monitor         quanti monitor, e di che nome
#   sudo bash .../04-b20-terreno.sh accendi         il server sulla 7601
#   sudo bash .../04-b20-terreno.sh spegni
#   sudo bash .../04-b20-terreno.sh pulisci         toglie l'utente del banco
#
# ===========================================================================
# ⛔ PERCHE' UN UTENTE TUTTO SUO, E NON `prova`
# ===========================================================================
#
# `SPECIFICHE.md` §5.1: **una sola sessione grafica per utente**.  ⇒ Per fare
# l'A/B — la stessa macchina, lo stesso minuto, con e senza `--virtual-monitor`
# — servono due sessioni, e su un utente solo non ci stanno.
#
# ⛔ E ne' `nicfio` ne' `prova` si toccano, per due ragioni diverse:
#   · `nicfio` ha la sessione da cui l'utente lavora;
#   · ⭐ `prova` e' **l'unico posto dove oggi il desktop vero si vede** (deciso
#     dall'utente il 14 agosto 2026), e in questo momento ha gia' un figlio
#     attaccato — quello del server 7571.  ⛔ `[M]` 14 agosto: la sua sessione ha
#     UN monitor, «Virtual remote monitor» 0x000001, che e' il `RecordVirtual`
#     di quel figlio.  Attaccandosi con un SECONDO server ne comparirebbe un
#     altro, e la scena non sarebbe piu' quella che si vuole misurare.
#
# ===========================================================================
# ⛔ LA SCENA — E IL DIFETTO NON SI INVENTA, CI STA GIA'
# ===========================================================================
#
# `[M]` 14 agosto 2026: su questa macchina `--virtual-monitor` NON lo chiede il
# prodotto.  Lo chiede
#
#     /etc/systemd/user/org.gnome.Shell@wayland.service.d/remotix-headless.conf
#
# cioe' un drop-in **di sistema**, che vale per QUALUNQUE utente — ⛔ ed e'
# esattamente «una riga di configurazione che si puo' perdere» dell'invariante
# **I7**.  ⇒ Un utente nuovo nasce **col difetto addosso, gratis**: e' il giro
# `sessione con`.  Il giro `sessione senza` ci mette sopra il drop-in che il
# prodotto CURATO scrive — `zz-remotix-monitor.conf`, che vince perche' `zz-`
# viene dopo `remotix-` in ordine di nome file — e la differenza fra i due giri
# e' **una riga di prodotto**.
#
# ⚠ E la vittoria si VERIFICA rileggendo l'`ExecStart` in vigore, non si spera:
#   e' la stessa regola che `src/sessione.c:668` mette nel prodotto.
#
# ===========================================================================
# ⛔ LE PORTE CHE NON SONO MIE — 7448 · 7501 · 7561 · 7571
# ===========================================================================
#
# Si CONTANO prima e dopo ogni azione.  ⚠ E ban, socket del comando, certificati
# e registro sono PROPRI: due server che condividessero il file dei ban si
# metterebbero fuori uso a vicenda (`RCP.md` §4.4-bis).
set -uo pipefail

PORTA=${PORTA:-7601}
IND=${IND:-192.168.0.2}
UTENTE=${UTENTE:-provaa1}
UID_B=${UID_B:-1002}
PAROLA=${PAROLA:-provaa1-2026}
D=${D:-/media/REMOTIX/src/04-a1-src/src}
LAV=${LAV:-/media/REMOTIX/tmp/04-b20}
LIBS=${LIBS:-/media/REMOTIX/src/b2/ngtcp2/build/lib:/media/REMOTIX/src/b2/ngtcp2/build/crypto/ossl:/media/REMOTIX/src/b2/prefisso/lib}
MISURA=${MISURA:-1920x1080}
UNITA=org.gnome.Shell@wayland.service

CERT=$LAV/certificati
BAN=$LAV/ban
SOCK=$LAV/comando.sock
LOG=$LAV/registro.log
PIDF=$LAV/pid
RILIEVO=$LAV/rilievo

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

vicini() {
	local r=""
	for p in 7448 7501 7561 7571; do
		r="$r$p: $(ss -tuln 2>/dev/null | grep -c ":$p\b") · "
	done
	printf '%sascoltatori (NON miei)\n' "$r"
}

# ⛔ Tutto quel che va fatto DENTRO la sessione dell'utente passa di qui: uid,
#    gid, ambiente composto da zero.  ⚠ `SHELL` vuota (`STUDI.md` §gnome §3.1) e
#    `XDG_SESSION_TYPE=wayland` (senza, l'unita' della Shell non parte affatto
#    per via del suo `ConditionEnvironment`).
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

[ "$(id -u)" -eq 0 ] || { ko "⛔ va lanciato DA ROOT"; exit 2; }
mkdir -p "$LAV"

case "${1:-stato}" in
utente)
	log "L'utente del banco: $UTENTE (uid $UID_B)"
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
	# ⛔ `enable-linger`, o il gestore d'utente muore appena l'ultima sessione
	#    logind se ne va, e con lui la sessione grafica.
	loginctl enable-linger "$UTENTE" || { ko "⛔ enable-linger fallito"; exit 2; }
	ok "linger acceso: /run/user/$UID_B vivra' anche senza nessuno collegato"
	ls -ld "/run/user/$UID_B" 2>&1 | sed 's/^/        /'
	exit 0 ;;

sessione)
	MODO=${2:-}
	case "$MODO" in con|senza) ;; *) ko "uso: sessione <con|senza>"; exit 2 ;; esac
	log "La sessione GNOME di $UTENTE — $MODO --virtual-monitor"
	inf "$(vicini)"
	id "$UTENTE" >/dev/null 2>&1 || { ko "⛔ l'utente non c'e': fai «utente»"; exit 2; }

	DIR="/run/user/$UID_B/systemd/user.control/$UNITA.d"
	FILE="$DIR/zz-remotix-monitor.conf"
	install -d -o "$UID_B" -g "$UID_B" -m 700 "$DIR" || { ko "⛔ non ho fatto $DIR"; exit 2; }
	if [ "$MODO" = con ]; then
		# ⛔ E' la riga che `src/sessione.c:650` scrive OGGI, parola per parola.
		printf '[Service]\nExecStart=\nExecStart=/usr/bin/gnome-shell --headless --no-x11 --virtual-monitor %s\n' \
			"$MISURA" > "$FILE"
		ATTESO="--virtual-monitor"
		VIETATO=""
	else
		# ⛔ E' la riga che `src/sessione.c:650` scrive DOPO LA CURA.
		printf '[Service]\nExecStart=\nExecStart=/usr/bin/gnome-shell --headless --no-x11\n' > "$FILE"
		ATTESO="--no-x11"
		VIETATO="--virtual-monitor"
	fi
	chown "$UID_B:$UID_B" "$FILE"
	inf "scritto $FILE:"
	sed 's/^/        /' "$FILE"

	# ⛔ Se c'e' una sessione viva, la si CONGEDA e si aspetta `inactive` — non
	#    «diverso da active»: `is-active` passa per `deactivating`, e ripartire
	#    li' dentro e' un'altra prima esecuzione (`STUDI.md` §gnome, fase 0 difetto 4).
	if pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1; then
		inf "c'e' gia' una sessione: la congedo (Logout 2)"
		come_utente gdbus call --session -d org.gnome.SessionManager \
			-o /org/gnome/SessionManager \
			-m org.gnome.SessionManager.Logout 2 >/dev/null 2>&1
		g=0
		while [ $g -lt 60 ]; do
			s=$(come_utente systemctl --user is-active gnome-session-manager@gnome.service 2>/dev/null)
			case "$s" in inactive|failed|unknown)
				pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 || break ;;
			esac
			sleep 0.5; g=$((g+1))
		done
		come_utente systemctl --user reset-failed >/dev/null 2>&1
		pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 && {
			ko "⛔ la sessione vecchia non se n'e' andata: non ne avvio una seconda"
			exit 3; }
		ok "la sessione vecchia e' uscita"
	fi

	come_utente systemctl --user daemon-reload || { ko "⛔ daemon-reload"; exit 2; }

	# ⛔ SCRITTO NON E' IN VIGORE (forma E1): si rilegge dal gestore.  ⚠ E si
	#    guarda anche l'ASSENZA, non solo la presenza: e' proprio l'assenza che
	#    il giro «senza» deve ottenere contro il drop-in di sistema.
	VIG=$(come_utente systemctl --user show -p ExecStart --value "$UNITA")
	inf "ExecStart in vigore: $VIG"
	case "$VIG" in *"$ATTESO"*) ok "c'e' «$ATTESO»" ;;
		*) ko "⛔ «$ATTESO» NON c'e': un altro drop-in vince sul mio"; exit 3 ;;
	esac
	if [ -n "$VIETATO" ]; then
		case "$VIG" in *"$VIETATO"*)
			ko "⛔ c'e' ancora «$VIETATO»: la scena non e' quella che credo"
			exit 3 ;;
		*) ok "e NON c'e' «$VIETATO»" ;;
		esac
	fi

	log "Avvio la sessione"
	come_utente setsid --fork sh -c \
		"exec >>/run/user/$UID_B/remotix-sessione.log 2>&1; exec gnome-session --session=gnome"
	g=0
	while [ $g -lt 90 ]; do
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
	# ⚠ E si legge la RIGA DI COMANDO del processo, non il file: che l'opzione
	#   sia scritta non e' che sia in vigore.
	for p in $(pgrep -u "$UID_B" -x gnome-shell); do
		inf "gnome-shell $p: $(tr '\0' ' ' < /proc/$p/cmdline)"
	done
	exec bash "$0" monitor ;;

nasci)
	# ⭐⛔ QUI LA SESSIONE LA FA NASCERE IL PRODOTTO — `CODER.md` §3.6.
	#
	#     Il drop-in lo scrive `scrivi_dropin()` di `src/sessione.c`, non una
	#     riga di questo file: cosi' la differenza fra il giro rosso e il giro
	#     verde e' **una riga di prodotto**, e il banco non giudica se stesso.
	#
	# ⚠ E il numero che esce e' `SessioneStato`: dopo la cura, su una sessione
	#   remota sana, e' **1 NERA** — zero monitor propri — e NON e' un guasto.
	log "La sessione la fa nascere IL PRODOTTO: sessione_assicura($MISURA)"
	inf "$(vicini)"
	P=$LAV/04-b20-nasci
	[ -x "$P" ] || { ko "⛔ $P non c'e': fai «costruisci»"; exit 2; }
	# ⛔ Il drop-in del giro precedente si toglie: e' del BANCO, e lasciarlo
	#    vorrebbe dire far vincere la scena sopra il prodotto.
	rm -f "/run/user/$UID_B/systemd/user.control/$UNITA.d/zz-remotix-monitor.conf"
	come_utente systemctl --user daemon-reload >/dev/null 2>&1
	inf "ExecStart senza il mio drop-in: $(come_utente systemctl --user show -p ExecStart --value "$UNITA")"
	come_utente env LD_LIBRARY_PATH="$LIBS" "$P" assicura "$MISURA"
	n=$?
	inf "sessione_assicura ha detto $n"
	for p in $(pgrep -u "$UID_B" -x gnome-shell); do
		inf "gnome-shell $p: $(tr '\0' ' ' < /proc/$p/cmdline)"
	done
	inf "ExecStart in vigore ADESSO: $(come_utente systemctl --user show -p ExecStart --value "$UNITA")"
	bash "$0" monitor
	exit "$n" ;;

scena)
	# ⛔⭐ LA SCENA SI DICHIARA E SI MUOVE SEMPRE — `CODER.md` §3.2.
	#
	#     `[M]` 14 agosto 2026: con la cattura a `framerate 0/1` (`cattura.h`)
	#     su un desktop FERMO **non arriva un solo fotogramma**, ne' prima ne'
	#     dopo la cura — l'orologio di GNOME scatta una volta al minuto e basta.
	#     ⇒ Un banco che misurasse su quel fermo misurerebbe la scena, non il
	#       prodotto: quindi la scena si accende, e si accende su **quello
	#       schermo li'**, che dopo la cura e' l'unico che c'e'.
	#
	# ⚠ E la scena e' una FINESTRA VERA, non un quadrato che lampeggia: cosi'
	#   quel che si vede e' il desktop dell'utente — che e' il metro (I8).
	log "La scena: una finestra che scrive l'ora, sulla sessione di $UTENTE"
	come_utente pkill -f 'banco-A1-scena' >/dev/null 2>&1
	# ⚠ `gnome-terminal` e' un CLIENT: chiede la finestra a
	#   `gnome-terminal-server` via D-Bus e se ne va subito.  ⛔ Cercare il suo
	#   processo direbbe sempre «non c'e'» — si cerca il ciclo che scrive l'ora,
	#   che e' figlio del server e sta li' finche' la finestra sta li'.
	come_utente setsid --fork gnome-terminal --title=banco-A1-scena -- \
		bash -c 'while true; do date +%H:%M:%S.%N; sleep 0.2; done' \
		>/dev/null 2>&1
	sleep 6
	n=$(pgrep -u "$UID_B" -f 'while true; do date' 2>/dev/null | wc -l)
	m=$(pgrep -u "$UID_B" -f 'gnome-terminal-server' 2>/dev/null | wc -l)
	inf "cicli che scrivono l'ora: $n · gnome-terminal-server: $m"
	if [ "$n" -gt 0 ] && [ "$m" -gt 0 ]; then
		ok "la scena e' accesa, e si muove"
	else
		ko "⛔ la scena NON si e' accesa: quel che segue misurerebbe un fermo"
		exit 3
	fi
	exit 0 ;;

scena-via)
	come_utente pkill -f 'banco-A1-scena' 2>/dev/null
	ok "scena spenta"
	exit 0 ;;

monitor)
	# ⚠ E' un CONTROLLO, non la misura: `GetCurrentState` dice quanti schermi
	#   ci sono, non su quale sta la barra.  Il verdetto lo da' `04-b20-desktop-vero.py`.
	come_utente busctl --user call org.gnome.Mutter.DisplayConfig \
		/org/gnome/Mutter/DisplayConfig org.gnome.Mutter.DisplayConfig \
		GetCurrentState 2>&1 \
	| tr ' ' '\n' | grep -c '"Meta-' | while read -r n; do
		printf 'MONITOR %s\n' "$((n / 2))"
	done
	come_utente busctl --user call org.gnome.Mutter.DisplayConfig \
		/org/gnome/Mutter/DisplayConfig org.gnome.Mutter.DisplayConfig \
		GetCurrentState 2>&1 | tr ' ' '\n' \
		| grep -E '^"(Meta-[0-9]+|MetaVirtualMonitor|Virtual)' | sed 's/^/        /'
	exit 0 ;;

accendi)
	log "Il server del banco A1, sulla $PORTA — DA ROOT"
	inf "$(vicini)"
	[ -x "$D/remotix" ] || { ko "⛔ $D/remotix non c'e'"; exit 2; }
	[ -f "$D/pagina.html" ] || { ko "⛔ $D/pagina.html non c'e'"; exit 2; }
	n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
	[ "$n" -eq 0 ] || { ko "⛔ la $PORTA e' gia' occupata"; exit 2; }
	[ -f /etc/pam.d/remotix ] || { ko "⛔ /etc/pam.d/remotix non c'e': ogni parola sara' rifiutata"; exit 2; }
	mkdir -p "$CERT" "$RILIEVO"; chmod 1777 "$RILIEVO"
	export LD_LIBRARY_PATH="$LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
	ldd "$D/remotix" | grep -q 'not found' && {
		ko "⛔ manca una libreria:"; ldd "$D/remotix" | grep 'not found' | sed 's/^/        /'
		exit 2; }
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

spegni)
	log "Spengo la $PORTA"
	inf "$(vicini)"
	if ! pid=$(mio_pid); then ok "non c'era niente sulla $PORTA"; exit 0; fi
	miei=""
	for f in $(pgrep -P "$pid" 2>/dev/null); do
		case "$(tr '\0' ' ' < /proc/$f/cmdline 2>/dev/null)" in
		*--figlio-interno*) miei="$miei $f" ;;
		esac
	done
	kill "$pid" 2>/dev/null
	g=0; while [ -d "/proc/$pid" ] && [ $g -lt 30 ]; do sleep 0.5; g=$((g+1)); done
	rm -f "$PIDF"
	restano=""
	for f in $miei; do
		case "$(tr '\0' ' ' < /proc/$f/cmdline 2>/dev/null)" in
		*--figlio-interno*) restano="$restano $f" ;;
		esac
	done
	if [ -z "$restano" ]; then ok "spento, e nessun figlio MIO e' rimasto orfano"
	else ko "⛔ figli MIEI orfani:$restano — attaccati al monitor di qualcuno"; fi
	inf "$(vicini)"
	exit 0 ;;

pulisci)
	log "Tolgo l'utente del banco"
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
	log "Stato"
	inf "$(vicini)"
	inf "utente $UTENTE: $(id "$UTENTE" 2>&1)"
	for p in $(pgrep -u "$UID_B" -x gnome-shell 2>/dev/null); do
		inf "gnome-shell $p: $(tr '\0' ' ' < /proc/$p/cmdline)"
	done
	if pid=$(mio_pid); then inf "server $PORTA: pid $pid"; else inf "server $PORTA: spento"; fi
	exit 0 ;;
esac
