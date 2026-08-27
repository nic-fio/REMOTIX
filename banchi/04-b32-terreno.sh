#!/bin/bash
#
# 04-b32-terreno.sh — ⛔ GIRA SUL SERVER (NIC-OS), **FUORI** dal contenitore e
# **DA ROOT**.  Prepara il terreno dell'anello **O2** (l'anello input → vetro,
# banco `04-b30`) e accende tutto quel che sta di la':
#
#   sudo bash .../04-b32-terreno.sh utente           crea l'utente del banco
#   sudo bash .../04-b32-terreno.sh sessione         GNOME **senza** --virtual-monitor
#   sudo bash .../04-b32-terreno.sh monitor          quanti monitor, e di che nome
#   sudo bash .../04-b32-terreno.sh accendi          il prodotto sulla 7722
#   sudo bash .../04-b32-terreno.sh ponte-accendi    il ponte 7721 -> 7722, ancora 7723
#   sudo bash .../04-b32-terreno.sh scena-avvia      la scena SUL MONITOR CATTURATO
#   sudo bash .../04-b32-terreno.sh scena-conta | scena-ferma
#   sudo bash .../04-b32-terreno.sh stato | registro | spegni | pulisci
#
# ⛔ E `scena-costruisci` gira DENTRO il contenitore (sull'host non c'e' `gcc`).
#
# ===========================================================================
# ⛔⛔ PERCHE' UN UTENTE TUTTO SUO — E QUI VALE DUE VOLTE
# ===========================================================================
#
# `SPECIFICHE.md` §5.1: **una sola sessione grafica per utente**.  E in questo
# momento sulla macchina ci sono gia':
#   · `nicfio`   — la sessione da cui l'utente lavora;
#   · ⛔ `prova` — **dove l'utente sta usando REMOTIX adesso** (porta 7700), e
#     `04-b20-terreno.sh` lo dice gia': attaccandosi con un secondo server
#     comparirebbe un secondo monitor e la scena non sarebbe piu' quella che si
#     vuole misurare;
#   · `provaa1`  — l'utente del banco A1.
# ⇒ Il mio e' `provao2` (uid 1003), e non tocco nessuno dei tre.
#
# ===========================================================================
# ⛔⛔ IL GRUPPO `render`, E COSTA 95 ms SE LO SI DIMENTICA
# ===========================================================================
#
# `[M]` 14 agosto 2026: la codifica e' in hardware (`hevc_vaapi`,
# `/dev/dri/renderD128`, **4 800 us**).  ⛔ Senza il gruppo `render` il nodo non
# si apre, il codificatore **ripiega in software** e passa a **100 ms**: si
# misurerebbe un prodotto che non esiste.  ⚠ E il ripiego e' silenzioso quanto
# basta a non accorgersene finche' non si legge il numero.
#
# ⚠ Il prodotto gira da ROOT (il palco appartiene all'utente, invariante I3),
#   quindi il gruppo serve al FIGLIO, che scende a `provao2`.
#
# ===========================================================================
# ⛔ IL DROP-IN — e il difetto ci sta gia', non si inventa
# ===========================================================================
#
# `[M]` su questa macchina `--virtual-monitor` lo impone
#     /etc/systemd/user/org.gnome.Shell@wayland.service.d/remotix-headless.conf
# cioe' un drop-in **di sistema**, valido per QUALUNQUE utente — l'invariante
# **I7** violata da una riga di configurazione.  ⇒ Un utente nuovo nasce col
# difetto addosso, e il desktop sarebbe VUOTO (A1: `0 fotogrammi`, verdetto
# VUOTO).  Qui si scrive `zz-senza-monitor.conf` **nella configurazione
# dell'utente**, che vince su quella di sistema, e ⛔ **la vittoria si VERIFICA
# rileggendo l'`ExecStart` in vigore**, non si spera.
#
# ===========================================================================
# ⛔ LE PORTE — 7721-7725 SONO MIE, TUTTE LE ALTRE NO
# ===========================================================================
#
#   7721   il PONTE (quello che il browser apre)
#   7722   il prodotto, dietro il ponte
#   7723   l'ancora dell'orologio — ⛔ NON passa dal ritardatore
#   ⛔ ALTRUI, si CONTANO e non si toccano:
#          7448 · 7501 · 7561 · 7571 · **7700** (l'utente ci sta lavorando)
#          7601-05 A1 · 7611-15 A2 · 7621-25 A3 · 7631-35 A4 · 7641-45 A5
#          7651-55 A6 · 7661-65 A7 · 7671-75 A8 · 7681-85 A9 · 7691-95 (A10)
set -uo pipefail

PORTA=${PORTA:-7721}
PORTA_DENTRO=${PORTA_DENTRO:-7722}
PORTA_ANCORA=${PORTA_ANCORA:-7723}
IND=${IND:-192.168.0.2}
UTENTE=${UTENTE:-provao2}
UID_B=${UID_B:-1003}
PAROLA=${PAROLA:-provao2-2026}
D=${D:-/media/REMOTIX/src/04-b30-src/src}
LAV=${LAV:-/media/REMOTIX/tmp/04-b30}
LIBS=${LIBS:-/media/REMOTIX/src/b2/ngtcp2/build/lib:/media/REMOTIX/src/b2/ngtcp2/build/crypto/ossl:/media/REMOTIX/src/b2/prefisso/lib}
PONTE=${PONTE:-/media/REMOTIX/src/04-b30-ponte.py}
SCENA_LAV=${SCENA_LAV:-/media/REMOTIX/src/04-b30-scena-lav}
SCENA_C=${SCENA_C:-/media/REMOTIX/src/04-b30-scena.c}
SHM=${SHM:-remotix-04-b30}
UNITA=org.gnome.Shell@wayland.service

CERT=$LAV/certificati
BAN=$LAV/ban-$PORTA_DENTRO
SOCK=$LAV/comando-$PORTA_DENTRO.sock
LOG=$LAV/registro.log
PIDF=$LAV/pid
RILIEVO=$LAV/rilievo
COMANDO=$LAV/comando
VERBALE_PONTE=$LAV/ponte.json
PONTE_PIDF=$LAV/ponte.pid
PONTE_LOG=$LAV/ponte.log

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


vicini() {
	local r=""
	if ! command -v ss >/dev/null; then
		printf '⛔ NON GUARDATE (manca «ss») — e questo non e'"'"' «libere»\n'
		return
	fi
	for p in 7448 7501 7561 7571 7700; do
		r="$r$p: $(ss -tuln 2>/dev/null | grep -c ":$p\b") · "
	done
	printf '%sascoltatori (NON miei)\n' "$r"
}

# ⛔ Tutto quel che va fatto DENTRO la sessione dell'utente passa di qui: uid,
#    gid, ambiente composto da zero (`CODER.md` §4.5).  ⚠ `SHELL` vuota e
#    `XDG_SESSION_TYPE=wayland`, o l'unita' della Shell non parte affatto.
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

vivo() { [ -f "$1" ] && p=$(cat "$1" 2>/dev/null) && [ -n "$p" ] && [ -d "/proc/$p" ] && printf '%s' "$p"; }

mio_pid() {
	local p
	if [ -f "$PIDF" ]; then
		p=$(cat "$PIDF" 2>/dev/null)
		[ -n "$p" ] && [ -d "/proc/$p" ] && { echo "$p"; return 0; }
	fi
	p=$(pgrep -f "remotix .*--porta $PORTA_DENTRO" | head -1)
	[ -n "$p" ] && { echo "$p"; return 0; }
	return 1
}

# ⛔ Il monitor NON si scrive a mano: lo dice il registro del MIO prodotto, che
#    l'ha chiesto a Mutter.  Un nome indovinato mette la scena sul palco di un
#    altro banco — `[M]` 13 agosto 2026, zero fotogrammi per dieci secondi con
#    la catena perfettamente funzionante.
monitor_catturato() {
	grep -ao 'monitor «[^»]*»' "$LOG" 2>/dev/null | tail -1 \
		| sed 's/monitor «//; s/»//'
}

[ "$(id -u)" -eq 0 ] || { ko "⛔ va lanciato DA ROOT: il palco appartiene all'utente (I3)"; exit 2; }
mkdir -p "$LAV"

case "${1:-stato}" in
utente)
	log "L'utente del banco O2: $UTENTE (uid $UID_B)"
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
	# ⛔ La verifica c'era gia' ed era la meta' giusta — ma cercava il NOME
	#    «render»: su una macchina dove il nodo appartiene a un altro gruppo
	#    avrebbe detto OK a un inquilino cieco.  Adesso confronta i NUMERI.
	gruppi_scheda_dai_a "$UTENTE" || exit 3
	inf "id: $(id "$UTENTE")"
	loginctl enable-linger "$UTENTE" || { ko "⛔ enable-linger fallito"; exit 2; }
	ok "linger acceso: /run/user/$UID_B vivra' anche senza nessuno collegato"
	ls -ld "/run/user/$UID_B" 2>&1 | sed 's/^/        /'
	exit 0 ;;

sessione)
	log "La sessione GNOME di $UTENTE — ⛔ SENZA --virtual-monitor (A1)"
	inf "$(vicini)"
	id "$UTENTE" >/dev/null 2>&1 || { ko "⛔ l'utente non c'e': fai «utente»"; exit 2; }

	DIR="/home/$UTENTE/.config/systemd/user/$UNITA.d"
	FILE="$DIR/zz-senza-monitor.conf"
	install -d -o "$UID_B" -g "$UID_B" -m 755 "/home/$UTENTE/.config" \
		"/home/$UTENTE/.config/systemd" "/home/$UTENTE/.config/systemd/user" \
		"/home/$UTENTE/.config/systemd/user/$UNITA.d" || { ko "⛔ non ho fatto $DIR"; exit 2; }
	printf '[Service]\nExecStart=\nExecStart=/usr/bin/gnome-shell --headless --no-x11\n' > "$FILE"
	chown "$UID_B:$UID_B" "$FILE"
	inf "scritto $FILE:"
	sed 's/^/        /' "$FILE"

	if pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1; then
		inf "c'e' gia' una sessione: la congedo (Logout 2)"
		come_utente gdbus call --session -d org.gnome.SessionManager \
			-o /org/gnome/SessionManager \
			-m org.gnome.SessionManager.Logout 2 >/dev/null 2>&1
		g=0
		while [ $g -lt 60 ]; do
			pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 || break
			sleep 0.5; g=$((g+1))
		done
		come_utente systemctl --user reset-failed >/dev/null 2>&1
		pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 && {
			ko "⛔ la sessione vecchia non se n'e' andata: non ne avvio una seconda"
			exit 3; }
		ok "la sessione vecchia e' uscita"
	fi

	come_utente systemctl --user daemon-reload || { ko "⛔ daemon-reload"; exit 2; }

	# ⛔ SCRITTO NON E' IN VIGORE: si rilegge dal gestore.  ⚠ E si guarda anche
	#    l'ASSENZA — e' proprio l'assenza che deve vincere sul drop-in di sistema.
	VIG=$(come_utente systemctl --user show -p ExecStart --value "$UNITA")
	inf "ExecStart in vigore: $VIG"
	case "$VIG" in *--no-x11*) ok "c'e' «--no-x11»" ;;
		*) ko "⛔ «--no-x11» NON c'e': un altro drop-in vince sul mio"; exit 3 ;;
	esac
	case "$VIG" in *--virtual-monitor*)
		ko "⛔ c'e' ancora «--virtual-monitor»: il desktop sarebbe VUOTO (A1)"
		exit 3 ;;
	*) ok "⭐ e NON c'e' «--virtual-monitor»: il monitor sara' quello di RecordVirtual, e la shell ci finira' sopra" ;;
	esac

	log "Avvio la sessione"
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
	for p in $(pgrep -u "$UID_B" -x gnome-shell); do
		inf "gnome-shell $p: $(tr '\0' ' ' < /proc/$p/cmdline)"
	done
	exec bash "$0" monitor ;;

monitor)
	# ⚠ E' un CONTROLLO, non la misura: dice quanti schermi ci sono, non su
	#   quale sta la barra.  Il verdetto sull'anello lo da' `04-b30`.
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
	log "Il prodotto dell'anello O2, sulla $PORTA_DENTRO — DA ROOT"
	inf "$(vicini)"
	[ -x "$D/remotix" ] || { ko "⛔ $D/remotix non c'e'"; exit 2; }
	[ -f "$D/pagina.html" ] || { ko "⛔ $D/pagina.html non c'e'"; exit 2; }
	command -v ss >/dev/null || { ko "⛔ «ss» non c'e': non chiamo libera una porta che non ho guardato"; exit 2; }
	n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA_DENTRO\b")
	[ "$n" -eq 0 ] || { ko "⛔ la $PORTA_DENTRO e' gia' occupata ($n righe)"; exit 2; }
	[ -f /etc/pam.d/remotix ] || { ko "⛔ /etc/pam.d/remotix non c'e': ogni parola sara' rifiutata"; exit 2; }
	mkdir -p "$CERT" "$RILIEVO"; chmod 1777 "$RILIEVO"
	export LD_LIBRARY_PATH="$LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
	ldd "$D/remotix" | grep -q 'not found' && {
		ko "⛔ manca una libreria:"; ldd "$D/remotix" | grep 'not found' | sed 's/^/        /'
		exit 2; }
	nohup "$D/remotix" --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA_DENTRO" \
		--certificati "$CERT" --pagina "$D/pagina.html" \
		--ban-file "$BAN" --comando-socket "$SOCK" \
		--rilievo "$RILIEVO" --parlantina >> "$LOG" 2>&1 &
	pid=$!; echo "$pid" > "$PIDF"
	g=0
	while [ $g -lt 60 ]; do
		[ -d "/proc/$pid" ] || break
		[ "$(ss -tuln 2>/dev/null | grep -c ":$PORTA_DENTRO\b")" -ge 2 ] && break
		sleep 0.5; g=$((g+1))
	done
	[ -d "/proc/$pid" ] || { ko "⛔ il server e' morto subito:"; tail -20 "$LOG" | sed 's/^/        /'; exit 3; }
	righe=$(ss -tuln | grep -c ":$PORTA_DENTRO\b")
	[ "$righe" -ge 2 ] || { ko "⛔ pid $pid vivo ma $righe ascoltatori: ne servono DUE"; tail -20 "$LOG" | sed 's/^/        /'; exit 3; }
	ok "acceso, pid $pid, $righe ascoltatori su :$PORTA_DENTRO"
	inf "$(vicini)"
	exit 0 ;;

ponte-accendi)
	log "Il PONTE: $PORTA (tcp+udp) -> $PORTA_DENTRO, ancora su $PORTA_ANCORA"
	[ -f "$PONTE" ] || { ko "⛔ $PONTE non c'e'"; exit 2; }
	if p=$(vivo "$PONTE_PIDF"); then ok "il ponte e' gia' vivo (pid $p)"; exit 0; fi
	command -v ss >/dev/null || { ko "⛔ «ss» non c'e'"; exit 2; }
	for p in "$PORTA" "$PORTA_ANCORA"; do
		n=$(ss -tuln 2>/dev/null | grep -c ":$p\b")
		[ "$n" -eq 0 ] || { ko "⛔ la porta $p e' gia' occupata ($n righe): non e' mia, non la tocco"; exit 2; }
	done
	[ -f "$COMANDO" ] || printf 'ritardo_ms=0\nfuori_ordine=0\ngiro=-\n' > "$COMANDO"
	chmod 666 "$COMANDO"
	nohup python3 "$PONTE" --fuori "$PORTA" --dentro "$PORTA_DENTRO" \
	      --orologio "$PORTA_ANCORA" --comando "$COMANDO" \
	      --verbale "$VERBALE_PONTE" >> "$PONTE_LOG" 2>&1 &
	echo $! > "$PONTE_PIDF"
	g=0
	while [ "$g" -lt 40 ]; do
		[ "$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")" -ge 2 ] && break
		sleep 0.25; g=$((g+1))
	done
	righe=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
	[ "$righe" -ge 2 ] || { ko "⛔ il ponte non ascolta in due (tcp+udp): $righe righe"
		tail -10 "$PONTE_LOG" | sed 's/^/        /'; exit 3; }
	ok "ponte acceso (pid $(cat "$PONTE_PIDF")), $righe ascoltatori su :$PORTA"
	ok "ancora su :$PORTA_ANCORA — ⛔ e NON passa dal ritardatore"
	exit 0 ;;

ponte-ferma)
	if p=$(vivo "$PONTE_PIDF"); then
		kill "$p" 2>/dev/null; sleep 0.5
		[ -d "/proc/$p" ] && kill -9 "$p" 2>/dev/null
		ok "ponte fermo (pid $p)"; rm -f "$PONTE_PIDF"
	else inf "nessun ponte mio acceso"; fi
	exit 0 ;;

scena-avvia)
	# ⛔⭐ LA SCENA DEVE STARE SUL MONITOR CHE SI STA CATTURANDO, e il nome NON
	#     si scrive a mano: lo dice il registro del MIO prodotto.
	USCITA=${2:-}
	[ -S "/run/user/$UID_B/wayland-0" ] || { ko "⛔ /run/user/$UID_B/wayland-0 non c'e'"; exit 2; }
	[ -x "$SCENA_LAV/04-b30-scena" ] || { ko "⛔ la scena non e' costruita: «scena-costruisci»"; exit 2; }
	[ -n "$USCITA" ] || USCITA=$(monitor_catturato)
	if [ -z "$USCITA" ] || [ "$USCITA" = "(non l'ho saputo dire)" ]; then
		ko "⛔ non so su quale monitor sta il palco del MIO prodotto: il registro"
		ko "   ($LOG) non lo nomina.  ⚠ Non accendo la scena «da qualche parte»:"
		ko "   sarebbe uno zero puntato sull'imputato sbagliato."
		inf "   ⇒ Serve che qualcuno sia ENTRATO nella sessione: il monitor"
		inf "     virtuale nasce col figlio, non con il server."
		exit 2
	fi
	inf "il palco del MIO prodotto e' il monitor «$USCITA» (letto dal registro, non dedotto)"
	if p=$(vivo "$LAV/scena.pid"); then ok "la scena e' gia' viva (pid $p)"; exit 0; fi
	: >> "$LAV/scena.log"; chmod 666 "$LAV/scena.log"
	come_utente env WAYLAND_DISPLAY=wayland-0 \
		nohup stdbuf -oL -eL "$SCENA_LAV/04-b30-scena" --uscita "$USCITA" \
		    --movimento barra --danno preciso --shm "$SHM" \
		    --giro "b30-$(date +%H%M%S)" --loquace \
		    >> "$LAV/scena.log" 2>&1 &
	# ⛔ IL PID SI CERCA, NON SI EREDITA: `$!` qui e' il capofila della catena
	#    `setpriv → env → nohup`, e non e' detto che sia la scena.  ⚠ Un pid
	#    sbagliato fa dire «viva» a un processo che non e' lei, e «morta» a lei.
	sleep 1
	pid=$(pgrep -u "$UID_B" -f '04-b30-scena --uscita' | head -1)
	[ -n "$pid" ] || { ko "⛔ la scena non e' partita:"; tail -25 "$LAV/scena.log" | sed 's/^/        /'; exit 3; }
	echo "$pid" > "$LAV/scena.pid"
	# ⛔ E «viva» non e' «disegna»: si guarda il CONTO nel blocco di stato, che
	#    lo scrive lei stessa, e si pretende che CRESCA (`LEZIONI.md` §1.9).
	a=$(od -An -tu8 -j24 -N8 "/dev/shm/$SHM" 2>/dev/null | tr -d ' ')
	sleep 1
	b=$(od -An -tu8 -j24 -N8 "/dev/shm/$SHM" 2>/dev/null | tr -d ' ')
	if [ -n "$a" ] && [ -n "$b" ] && [ "$b" -gt "$a" ] 2>/dev/null; then
		ok "⭐ scena viva sul monitor «$USCITA» (pid $pid) e DISEGNA: $a → $b in un secondo"
		tail -4 "$LAV/scena.log" | sed 's/^/        /'
	else
		ko "⛔ la scena e' viva ma il conto dei disegni non cresce ($a → $b):"
		ko "   NON dico che sta disegnando («vivo» non e' «disegna»)"
		tail -15 "$LAV/scena.log" | sed 's/^/        /'
		exit 3
	fi
	exit 0 ;;

scena-stato)
	# ⛔ IL BLOCCO DI STATO DELLA SCENA, GREZZO — e **DUE VOLTE**, non una.
	#
	#    Il blocco ha un seqlock: chi lo legge una volta sola puo' pescare un
	#    conto nuovo con un istante vecchio e credere a un ritardo mai esistito
	#    (`03-marca.py`).  ⇒ Si consegnano due istantanee, e chi legge pretende
	#    che `seq` sia PARI e UGUALE nelle due.  ⚠ E se il file non c'e' si dice
	#    «non ho potuto guardare», che non e' «l'input non e' arrivato».
	[ -e "/dev/shm/$SHM" ] || { ko "⛔ /dev/shm/$SHM non esiste: la scena non e' mai partita, o ha un altro --shm.  ⚠ NON e' «zero eventi»"; exit 2; }
	base64 -w0 "/dev/shm/$SHM"; echo
	base64 -w0 "/dev/shm/$SHM"; echo
	exit 0 ;;

scena-conta)
	[ -f "$LAV/scena.log" ] || { ko "⛔ nessun registro della scena: non ho guardato"; exit 2; }
	if p=$(vivo "$LAV/scena.pid"); then ok "scena viva, pid $p"; else ko "⛔ la scena NON e' viva"; fi
	tail -8 "$LAV/scena.log"
	exit 0 ;;

scena-ferma)
	pkill -u "$UID_B" -f '04-b30-scena --uscita' 2>/dev/null
	sleep 1
	if p=$(vivo "$LAV/scena.pid"); then
		kill "$p" 2>/dev/null
		g=0; while [ -d "/proc/$p" ] && [ "$g" -lt 20 ]; do sleep 0.25; g=$((g+1)); done
		[ -d "/proc/$p" ] && ko "⛔ la scena (pid $p) non e' morta" || ok "scena ferma (pid $p)"
		rm -f "$LAV/scena.pid"
	else
		inf "nessuna scena mia accesa"
	fi
	exit 0 ;;

palco)
	# ⛔ Gira DA ROOT apposta: `ls /proc/<pid>/fd` da utente normale risponde
	#    «Permission denied», e un lettore ingenuo leggerebbe zero nodi DRM e
	#    concluderebbe «codifica in SOFTWARE» — cioe' il numero sbagliato al
	#    contrario (`LEZIONI.md` §2.0).
	# ⛔ SOLO I MIEI PROCESSI, e non e' pignoleria: `pgrep -x remotix` prende
	#    anche il server dell'utente sulla 7700 e quelli degli altri banchi, e
	#    l'unione dei loro descrittori direbbe «hardware» anche se il MIO
	#    codificatore fosse ripiegato in software.  ⇒ Si parte dal mio pid e si
	#    scende ai suoi figli.
	pids=""
	if mp=$(mio_pid); then pids="$mp $(pgrep -P "$mp" 2>/dev/null | tr '\n' ' ')"; fi
	n=0; letti=0; negati=0; nodi=""
	for p in $pids; do
		n=$((n+1))
		if elenco=$(ls -l "/proc/$p/fd" 2>/dev/null); then
			letti=$((letti+1))
			nodi="$nodi $(printf '%s\n' "$elenco" | grep -o 'renderD[0-9]*' | sort -u | tr '\n' ' ')"
		else
			negati=$((negati+1))
		fi
	done
	nodi=$(printf '%s' "$nodi" | tr ' ' '\n' | grep -v '^$' | sort -u | tr '\n' ',' | sed 's/,$//')
	printf '{"utente":"%s","processi_remotix":%d,"letti":%d,"negati":%d,"nodi_di_rendering":"%s"}\n' \
	       "$(id -un)" "$n" "$letti" "$negati" "$nodi"
	exit 0 ;;

registro) tail -"${2:-60}" "$LOG"; exit 0 ;;

stato)
	log "Lo stato dell'anello O2"
	inf "$(vicini)"
	inf "utente $UTENTE: $(id "$UTENTE" 2>&1)"
	for p in $(pgrep -u "$UID_B" -x gnome-shell 2>/dev/null); do
		inf "gnome-shell $p: $(tr '\0' ' ' < /proc/$p/cmdline)"
	done
	if p=$(mio_pid); then ok "prodotto acceso: pid $p, porta $PORTA_DENTRO"
	else ko "il prodotto NON e' acceso"; fi
	if p=$(vivo "$PONTE_PIDF"); then ok "ponte acceso: pid $p, porta $PORTA"
	else ko "il ponte NON e' acceso"; fi
	if p=$(vivo "$LAV/scena.pid"); then ok "scena viva: pid $p"
	else inf "scena: non accesa (⚠ e senza scena questo banco non misura niente)"; fi
	inf "monitor catturato (dal registro): «$(monitor_catturato)»"
	[ -f "$COMANDO" ] && inf "comando del ponte: $(tr '\n' ' ' < "$COMANDO")"
	exit 0 ;;

spegni)
	log "Spengo — ⛔ SOLO le mie cose"
	inf "$(vicini)"
	bash "$0" scena-ferma
	bash "$0" ponte-ferma
	if pid=$(mio_pid); then
		miei=""
		for f in $(pgrep -P "$pid" 2>/dev/null); do
			case "$(tr '\0' ' ' < /proc/$f/cmdline 2>/dev/null)" in
			*--figlio-interno*) miei="$miei $f" ;;
			esac
		done
		kill "$pid" 2>/dev/null
		g=0; while [ -d "/proc/$pid" ] && [ $g -lt 40 ]; do sleep 0.5; g=$((g+1)); done
		[ -d "/proc/$pid" ] && kill -9 "$pid" 2>/dev/null
		rm -f "$PIDF"
		restano=""
		for f in $miei; do [ -d "/proc/$f" ] && restano="$restano $f"; done
		[ -z "$restano" ] && ok "prodotto spento, e nessun figlio MIO orfano" \
			|| ko "⛔ figli MIEI orfani:$restano"
	else
		inf "nessun prodotto mio acceso"
	fi
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

*)
	sed -n '2,20p' "$0"; exit 2 ;;
esac
