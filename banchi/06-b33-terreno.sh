#!/bin/bash
#
# 06-b33-terreno.sh — ⛔ GIRA SUL SERVER (NIC-OS), **FUORI** dal contenitore e
# **DA ROOT**.  Il terreno della SOTTOFASE 6.1 — *il riattacco che comanda*.
#
#   sudo bash .../06-b33-terreno.sh utente        crea `provai6` (uid 1006)
#   sudo bash .../06-b33-terreno.sh sessione      GNOME **senza** --virtual-monitor
#   sudo bash .../06-b33-terreno.sh accendi       il server sulla 7781
#   sudo bash .../06-b33-terreno.sh spegni
#   sudo bash .../06-b33-terreno.sh testimone LxA la finestra Wayland che RICEVE
#   sudo bash .../06-b33-terreno.sh testimone-via
#   sudo bash .../06-b33-terreno.sh righe         quante righe ha visto finora
#   sudo bash .../06-b33-terreno.sh coda <n>      le ultime n righe viste
#   sudo bash .../06-b33-terreno.sh terminale     ⭐ L'APPLICAZIONE APERTA PRIMA
#   sudo bash .../06-b33-terreno.sh terminale-via
#   sudo bash .../06-b33-terreno.sh invii         quanti «Invio» ha ricevuto
#   sudo bash .../06-b33-terreno.sh monitor       quanti schermi, e di che misura
#   sudo bash .../06-b33-terreno.sh carico        ⚠ uptime: ogni misura di tempo lo porta
#   sudo bash .../06-b33-terreno.sh registro <n>  la coda del registro del server
#   sudo bash .../06-b33-terreno.sh conta <str>   quante volte <str> sta nel registro
#   sudo bash .../06-b33-terreno.sh iniettore-accendi <LxA>  ⛔⛔ §7.1: il
#                                                 risveglio della cattura, senza
#                                                 nessun ADATTA_TELA
#   sudo bash .../06-b33-terreno.sh iniettore-di "<comando>"
#   sudo bash .../06-b33-terreno.sh iniettore-dice <n>   solo le righe B33R
#   sudo bash .../06-b33-terreno.sh iniettore-spegni
#   sudo bash .../06-b33-terreno.sh pulisci
#
# ===========================================================================
# ⛔ E' UNA COPIA ADATTATA di `04-b31-terreno.sh`, non una riscrittura
# ===========================================================================
#
# Quel file ha gia' pagato tre cose che qui non si ripagano: le TRE strade che
# NON rimettono in piedi una sessione uccisa, il drop-in che `terminate-user`
# porta via con `/run/user/<uid>`, e il conto dei monitor **diviso per due**
# (`GetCurrentState` elenca ogni schermo due volte).  ⇒ Si copia e si adatta.
#
# ⭐ E QUEL CHE QUESTO AGGIUNGE, che li' non serviva: il **testimone dentro la
#    sessione** (`CODER.md` §3.8 — il registro di chi manda dice che ha chiamato
#    una funzione, non che il desktop ha ricevuto) in due forme, e tutte e due
#    aperte **PRIMA dello stacco**:
#
#      · `testimone`   la finestra Wayland di `06-b33-testimone.c`: una riga
#                      JSON per ogni evento che il compositore le consegna.
#                      Lo STRUMENTO — conta, e distingue «zero» da «non ho
#                      guardato» perche' il numero di riga cresce sempre;
#      · `terminale`   un `gnome-terminal` col ciclo che l'utente giudicherebbe:
#                      `while IFS= read -r _; do date +%s%N >> …; done`.
#                      L'APPLICAZIONE VERA — un cliente Wayland **partito prima**
#                      che i dispositivi di input di questo giro esistano, che e'
#                      esattamente il punto 3 del mandato.
#
# ⛔ E NON si accendono insieme: la finestra a schermo intero prende il fuoco, e
#    il terminale sotto non riceverebbe un tasto.  Sono DUE SCENE, e il
#    lanciatore le fa una per volta dichiarando quale.
#
# ===========================================================================
# ⛔ `prova` E LA 7700 NON SI TOCCANO — e le porte che non sono mie
# ===========================================================================
#
# 7448 · 7501 · 7561 · 7571 · 7601 · 7691 · 7700 · 7711-7715 · 7721-7725 ·
# 7731-7735 · 7751-7755 · 7761-7765.  Si CONTANO prima e dopo, e non si toccano.
# ⚠ Ban, socket del comando, certificati e registro sono PROPRI: due server che
#   condividessero il file dei ban si metterebbero fuori uso a vicenda
#   (`RCP.md` §4.4-bis).
set -uo pipefail

PORTA=${PORTA:-7781}
IND=${IND:-192.168.0.2}
UTENTE=${UTENTE:-provai6}
UID_B=${UID_B:-1006}
PAROLA=${PAROLA:-provai6-2026}
D=${D:-/media/REMOTIX/src/06-i-src/src}
LAV=${LAV:-/media/REMOTIX/tmp/06-i}
LIBS=${LIBS:-/media/REMOTIX/src/b2/ngtcp2/build/lib:/media/REMOTIX/src/b2/ngtcp2/build/crypto/ossl:/media/REMOTIX/src/b2/prefisso/lib}
UNITA=org.gnome.Shell@wayland.service

CERT=$LAV/certificati
BAN=$LAV/ban
SOCK=$LAV/comando.sock
LOG=$LAV/registro.log
PIDF=$LAV/pid
RILIEVO=$LAV/rilievo
VISTO=$LAV/visto.jsonl
INVII=$LAV/invii.txt
TESTIMONE=$LAV/06-b33-testimone
INIETTORE=$LAV/06-b33-risveglio
INILOG=$LAV/06-b33-risveglio.log
INIFIFO=$LAV/06-b33-risveglio.fifo

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
	for p in 7448 7501 7561 7571 7601 7691 7700 7711 7721 7731 7751 7761; do
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

# ⭐ Il figlio di QUESTO server, e non un figlio qualunque: sulla stessa macchina
#    girano i server delle altre sei sottofasi.
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
	log "L'utente della sottofase 6.1: $UTENTE (uid $UID_B)"
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
	# ⭐ `render` E `video`, o il codificatore ripiega in software: `[M]` 4,8 ms
	#    → 100 ms per fotogramma, e il banco misurerebbe il ripiego.
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
	# ⛔⭐ `MUTTER_DEBUG` — 21 agosto 2026, e serve a trasformare in `[M]` una
	#     catena che finora era tutta `[R]` dentro Mutter.
	#
	#     Con `MUTTER_DEBUG=eis,input` il compositore stampa da se' le due righe
	#     che decidono la diagnosi di §7.1:
	#       ✅ `Dropping repeated press of button 0x110, count 2`
	#          ⇒ il conto del POSTO e' rimasto giu' (`meta-seat-impl.c:899-908`)
	#       ⛔ `Releasing pressed buttons while destroying virtual input device`
	#          ⇒ se COMPARISSE, Mutter avrebbe una rete che rilascia da se', e
	#            tutta la lettura del sorgente sarebbe da rifare.
	#
	# ⚠ Si mette come `Environment=` nel drop-in perche' la sessione la lancia
	#   `gnome-session`, non noi: una variabile esportata qui non arriverebbe.
	#   ⛔ Ed e' SPENTO di predefinito: il chiacchiericcio di `input` su una
	#   sessione viva riempie il giornale, e un banco che cambia il carico della
	#   macchina misura anche quello.
	if [ -n "${MUTTER_DEBUG:-}" ]; then
		printf '[Service]\nEnvironment=MUTTER_DEBUG=%s\nExecStart=\nExecStart=/usr/bin/gnome-shell --headless --no-x11\n' \
			"$MUTTER_DEBUG" > "$FILE"
		inf "⭐ MUTTER_DEBUG=$MUTTER_DEBUG nel drop-in"
	else
		printf '[Service]\nExecStart=\nExecStart=/usr/bin/gnome-shell --headless --no-x11\n' > "$FILE"
	fi
	chown "$UID_B:$UID_B" "$FILE"
	inf "scritto $FILE"

	if pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1; then
		# ⛔ E si DICE che il drop-in nuovo NON e' in vigore: `gnome-shell` ha
		#    letto il suo ambiente all'avvio, e riscrivere il file non cambia
		#    niente a un processo gia' partito.  ⚠ Chi vuole `MUTTER_DEBUG` deve
		#    passare da `sessione-via` — e senza questa riga crederebbe di
		#    averlo acceso.
		[ -n "${MUTTER_DEBUG:-}" ] && \
			ko "⚠ MA la sessione e' gia' viva: MUTTER_DEBUG NON e' in vigore. Fai «sessione-via» prima"
		ok "c'e' gia' una sessione viva — non la rifaccio"
		exec bash "$0" monitor
	fi

	# ⛔⭐ Le tre strade che NON funzionano sono misurate in `04-b31-terreno.sh`
	#     (14 agosto 2026): `systemctl --user start org.gnome.Shell@wayland`
	#     rifiuta *«may be requested by dependency only»*, lo stesso il gestore
	#     di sessione, e un `gnome-session` nuovo col gestore ancora **active**
	#     esce **in silenzio**.  ⇒ Si aspetta l'`inactive` e poi si parte.
	inf "la sessione non c'e': aspetto che il gestore sia inactive"
	come_utente systemctl --user reset-failed >/dev/null 2>&1
	g=0
	while [ $g -lt 40 ]; do
		come_utente systemctl --user is-active gnome-session-manager@gnome.service \
			>/dev/null 2>&1 || break
		sleep 0.5; g=$((g+1))
	done
	if come_utente systemctl --user is-active gnome-session-manager@gnome.service >/dev/null 2>&1; then
		ko "⚠ il gestore non se ne va: ULTIMA SPIAGGIA — butto giu' tutto"
		loginctl terminate-user "$UTENTE" >/dev/null 2>&1
		sleep 3
		pkill -9 -u "$UID_B" 2>/dev/null
		sleep 1
		loginctl enable-linger "$UTENTE" >/dev/null 2>&1
		g=0
		while [ $g -lt 60 ]; do
			[ -S "/run/user/$UID_B/bus" ] && break
			sleep 0.5; g=$((g+1))
		done
		[ -S "/run/user/$UID_B/bus" ] || { ko "⛔ il bus non e' tornato"; exit 3; }
		# ⛔ E il drop-in si riscrive: `terminate-user` ha portato via
		#    `/run/user/<uid>` con dentro `user.control`, e senza questa riga
		#    l'`ExecStart` in vigore torna a quello di SISTEMA, con
		#    `--virtual-monitor`.
		install -d -o "$UID_B" -g "$UID_B" -m 700 "$DIR" || { ko "⛔ non ho rifatto $DIR"; exit 2; }
		if [ -n "${MUTTER_DEBUG:-}" ]; then
			printf '[Service]\nEnvironment=MUTTER_DEBUG=%s\nExecStart=\nExecStart=/usr/bin/gnome-shell --headless --no-x11\n' \
				"$MUTTER_DEBUG" > "$FILE"
		else
			printf '[Service]\nExecStart=\nExecStart=/usr/bin/gnome-shell --headless --no-x11\n' > "$FILE"
		fi
		chown "$UID_B:$UID_B" "$FILE"
	else
		ok "il gestore di sessione e' inactive: gnome-session puo' ripartire"
	fi

	come_utente systemctl --user daemon-reload || { ko "⛔ daemon-reload"; exit 2; }
	come_utente systemctl --user reset-failed >/dev/null 2>&1
	come_utente systemctl --user start pipewire.socket pipewire-pulse.socket >/dev/null 2>&1
	come_utente systemctl --user start pipewire.service wireplumber.service >/dev/null 2>&1
	if come_utente systemctl --user is-active pipewire.service >/dev/null 2>&1; then
		ok "PipeWire e' vivo: senza, la cattura non avrebbe nessun nodo"
	else
		ko "⚠ PipeWire NON e' vivo: la cattura non trovera' nessun nodo"
	fi
	# ⛔ SCRITTO NON E' IN VIGORE (forma E1): si rilegge dal gestore.
	VIG=$(come_utente systemctl --user show -p ExecStart --value "$UNITA")
	inf "ExecStart in vigore: $VIG"
	case "$VIG" in *--no-x11*) ok "c'e' «--no-x11»" ;;
		*) ko "⛔ «--no-x11» NON c'e': un altro drop-in vince sul mio"; exit 3 ;;
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
	for p in $(pgrep -u "$UID_B" -x gnome-shell); do
		inf "gnome-shell $p: $(tr '\0' ' ' < /proc/$p/cmdline)"
	done
	exec bash "$0" monitor ;;

sessione-via)
	log "⛔ Uccido la sessione grafica di $UTENTE"
	come_utente gdbus call --session -d org.gnome.SessionManager \
		-o /org/gnome/SessionManager -m org.gnome.SessionManager.Logout 2 \
		>/dev/null 2>&1
	sleep 4
	pkill -u "$UID_B" -x gnome-shell 2>/dev/null
	g=0
	while [ $g -lt 30 ]; do
		pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 || break
		sleep 0.5; g=$((g+1))
	done
	pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 && \
		{ pkill -9 -u "$UID_B" -x gnome-shell 2>/dev/null; sleep 2; }
	pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 \
		&& { ko "⛔ la sessione non e' morta"; exit 3; } || ok "la sessione grafica e' morta"
	exit 0 ;;

# ---------------------------------------------------------------------------
# ⭐ IL TESTIMONE — la finestra Wayland che RICEVE
# ---------------------------------------------------------------------------
testimone)
	# ⛔ Si apre **PRIMA dello stacco**, e la sua misura e' quella della tela in
	#    vigore ADESSO: sceglie il `wl_output` per misura, e se non c'e' esce
	#    dicendolo invece di finire sullo schermo sbagliato (forma E2).
	M=${2:?serve la misura, es. 1264x800}
	log "Il testimone Wayland sul monitor $M"
	[ -x "$TESTIMONE" ] || { ko "⛔ $TESTIMONE non c'e': fai «costruisci»"; exit 2; }
	pkill -u "$UID_B" -f 06-b33-testimone 2>/dev/null; sleep 1
	# ⛔ Il file NON si azzera a ogni riapertura, e nemmeno si tiene per sempre:
	#    si azzera QUI, all'apertura, e il numero di riga riparte da 1 col
	#    processo.  ⚠ Chi confronta due giri deve leggere il conto, non il file.
	: > "$VISTO"; chmod 666 "$VISTO"
	come_utente setsid --fork sh -c \
		"exec >>'$VISTO' 2>&1; exec '$TESTIMONE' --misura $M"
	g=0
	while [ $g -lt 40 ]; do
		grep -q '"tipo":"PRONTA"' "$VISTO" 2>/dev/null && break
		grep -q '"tipo":"ERRORE"' "$VISTO" 2>/dev/null && break
		sleep 0.25; g=$((g+1))
	done
	if grep -q '"tipo":"PRONTA"' "$VISTO" 2>/dev/null; then
		ok "aperto: $(grep '"tipo":"PRONTA"' "$VISTO" | tail -1)"
		exit 0
	fi
	ko "⛔ il testimone NON si e' aperto:"
	tail -12 "$VISTO" 2>/dev/null | sed 's/^/        /'
	exit 3 ;;

testimone-via)
	pkill -u "$UID_B" -f 06-b33-testimone 2>/dev/null
	ok "testimone spento"
	exit 0 ;;

righe)
	# ⛔ Il CONTATORE, non «ho trovato righe»: «zero eventi» e «non ho guardato»
	#    hanno lo stesso aspetto senza un denominatore che cresce.
	printf 'RIGHE %s\n' "$(wc -l < "$VISTO" 2>/dev/null || echo 0)"
	exit 0 ;;

coda)
	tail -n "${2:-20}" "$VISTO" 2>/dev/null
	exit 0 ;;

dopo)
	# le righe con n > $2 — cioe' quel che e' arrivato DA un istante in poi
	awk -v s="${2:-0}" -F'"n":' '{split($2,a,","); if (a[1]+0 > s) print}' \
		"$VISTO" 2>/dev/null
	exit 0 ;;

# ---------------------------------------------------------------------------
# ⭐⭐ L'APPLICAZIONE APERTA PRIMA — il terminale col ciclo `read`
# ---------------------------------------------------------------------------
terminale)
	# ⛔ E' il punto 3 del mandato reso una scena: un cliente Wayland partito
	#    **prima** che i dispositivi di input di questo giro esistano.  `[M]` 10
	#    agosto 2026 (banco S7): *testimone prima dell'iniettore ⇒ non arriva
	#    NIENTE*.  Al riattacco i dispositivi si distruggono e si ricreano sotto
	#    applicazioni **che nessuno riavviera'** — e questa e' una di quelle.
	#
	# ⚠ Ogni `Invio` che ARRIVA AL DESKTOP scrive una riga in nanosecondi.  Un
	#   desktop vuoto non testimonia niente (trappola 9 del documento di fase).
	log "Il terminale col testimone — l'applicazione che nessuno riavviera'"
	# ⛔ LA MARCA VA DENTRO IL CICLO, NON NEL TITOLO — `[M]` 16 agosto 2026, e
	#    il banco ci e' cascato: `gnome-terminal` e' un client SOTTILE che passa
	#    la richiesta a `gnome-terminal-server` e **esce**.  ⇒ Il processo che
	#    porta `--title=b33-invii` nella riga di comando sparisce dopo un
	#    istante, e il ciclo vero e' un figlio del server con una riga di
	#    comando che quel titolo non ce l'ha.  Un `pgrep -f b33-invii` non lo
	#    trova mai, e il banco resta appeso ad aspettare una cosa che c'e'.
	come_utente pkill -f 'b33-ciclo-invii' >/dev/null 2>&1; sleep 1
	rm -f "$INVII"; : > "$INVII"; chmod 666 "$INVII"
	come_utente setsid --fork gnome-terminal --title=b33-invii -- \
		bash -c "# b33-ciclo-invii
			while IFS= read -r _; do date +%s%N >> '$INVII'; done" \
		>/dev/null 2>&1
	g=0
	while [ $g -lt 40 ]; do
		pgrep -u "$UID_B" -f 'b33-ciclo-invii' >/dev/null 2>&1 && \
			pgrep -u "$UID_B" -f 'gnome-terminal-server' >/dev/null 2>&1 && break
		sleep 0.5; g=$((g+1))
	done
	n=$(pgrep -u "$UID_B" -f 'b33-ciclo-invii' 2>/dev/null | wc -l)
	m=$(pgrep -u "$UID_B" -f 'gnome-terminal-server' 2>/dev/null | wc -l)
	inf "processi «b33-ciclo-invii»: $n · gnome-terminal-server: $m"
	if [ "$n" -gt 0 ] && [ "$m" -gt 0 ]; then
		ok "il terminale e' aperto, e il ciclo aspetta gli Invio"
	else
		ko "⛔ il terminale NON si e' aperto: quel che segue non misura niente"
		exit 3
	fi
	exit 0 ;;

terminale-via)
	come_utente pkill -f 'b33-ciclo-invii' 2>/dev/null
	ok "terminale spento"
	exit 0 ;;

invii)
	printf 'INVII %s\n' "$(wc -l < "$INVII" 2>/dev/null || echo 0)"
	exit 0 ;;

# ---------------------------------------------------------------------------
# ⛔⛔ L'INIETTORE DI §7.1 — la seconda porta del clic che muore
# ---------------------------------------------------------------------------
iniettore-accendi)
	# sudo bash 06-b33-terreno.sh iniettore-accendi <LxA>
	#
	# ⛔ Gira DENTRO la sessione di `provai6`, come lui: apre una sessione
	#    `RemoteDesktop` sua, monta un monitor virtuale suo e chiama
	#    `cattura_risveglia()` — la funzione del prodotto.  ⚠ NON e' il server:
	#    qui non c'e' QUIC e non c'e' `rcp.c`, ed e' voluto (`CODER.md` §3.6).
	#
	# ⛔ E NON si accende insieme al server della 7781: due sessioni
	#    `RemoteDesktop` sullo stesso utente montano due monitor, e il testimone
	#    finirebbe su quello sbagliato — cioe' misurerebbe un silenzio.
	#
	# ⛔⛔ LO STDIN E' UNA FIFO APERTA IN LETTURA **E SCRITTURA** (`exec 3<>`), e
	#      non e' un vezzo: una fifo aperta in sola lettura da' **EOF** ogni
	#      volta che l'ultimo scrittore chiude, cioe' dopo OGNI comando — e il
	#      programma uscirebbe con 5 («stdin chiuso senza fine») al primo giro.
	#      Il sintomo sarebbe «l'iniettore muore da solo», e nessuno lo
	#      collegherebbe alla fifo.
	M=${2:-1264x800}
	log "L'iniettore del risveglio, tela $M"
	[ -x "$INIETTORE" ] || { ko "⛔ $INIETTORE non c'e': fai «06-b33-risveglio-costruisci.sh»"; exit 2; }
	if pid=$(mio_pid); then
		ko "⛔ il server della $PORTA e' acceso (pid $pid): spegnilo, o le sessioni sono due"
		exit 2
	fi
	pkill -u "$UID_B" -f 06-b33-risveglio 2>/dev/null; sleep 1
	rm -f "$INIFIFO"; mkfifo -m 666 "$INIFIFO" || { ko "⛔ la fifo non si crea"; exit 2; }
	: > "$INILOG"; chmod 666 "$INILOG"
	come_utente setsid --fork sh -c \
		"exec >>'$INILOG' 2>&1; exec 3<>'$INIFIFO'; exec '$INIETTORE' --tela $M <&3"
	g=0
	while [ $g -lt 120 ]; do
		grep -qa '^B33R: PRONTO' "$INILOG" 2>/dev/null && break
		grep -qa '^B33R: ERRORE' "$INILOG" 2>/dev/null && break
		sleep 0.5; g=$((g+1))
	done
	if grep -qa '^B33R: PRONTO' "$INILOG" 2>/dev/null; then
		ok "l'iniettore e' PRONTO dopo $((g/2)) s"
		grep -a '^B33R: ' "$INILOG" | sed 's/^/        /'
		exit 0
	fi
	ko "⛔ l'iniettore NON e' pronto:"
	tail -25 "$INILOG" 2>/dev/null | sed 's/^/        /'
	exit 3 ;;

iniettore-di)
	# sudo bash 06-b33-terreno.sh iniettore-di "pulsante 272 1"
	shift
	pgrep -u "$UID_B" -f 06-b33-risveglio >/dev/null 2>&1 || {
		ko "⛔ l'iniettore non e' vivo: il comando «$*» non lo legge nessuno"; exit 3; }
	printf '%s\n' "$*" > "$INIFIFO"
	exit 0 ;;

iniettore-spegni)
	if pgrep -u "$UID_B" -f 06-b33-risveglio >/dev/null 2>&1; then
		printf 'fine\n' > "$INIFIFO" 2>/dev/null
		g=0
		while [ $g -lt 20 ]; do
			pgrep -u "$UID_B" -f 06-b33-risveglio >/dev/null 2>&1 || break
			sleep 0.5; g=$((g+1))
		done
		pkill -9 -u "$UID_B" -f 06-b33-risveglio 2>/dev/null
	fi
	rm -f "$INIFIFO"
	ok "iniettore spento"
	exit 0 ;;

giornale)
	# ⛔⭐ QUEL CHE DICE MUTTER DI SE STESSO — la voce del compositore, che non
	#     e' ne' la nostra ne' quella del testimone.  Serve solo con
	#     `MUTTER_DEBUG` acceso (vedi «sessione»).
	#
	#   sudo bash 06-b33-terreno.sh giornale [da-quando] [filtro]
	journalctl _UID="$UID_B" --since "${2:--3 min}" --no-pager -o cat 2>/dev/null \
		| grep -Ea "${3:-Dropping repeated|Releasing pressed buttons|Updating viewports|Counting release}"
	exit 0 ;;

giornale-tutto)
	journalctl _UID="$UID_B" --since "${2:--3 min}" --no-pager -o cat 2>/dev/null | tail -n "${3:-200}"
	exit 0 ;;

iniettore-registro)
	tail -n "${2:-80}" "$INILOG" 2>/dev/null
	exit 0 ;;

iniettore-dice)
	# ⛔ Solo le righe dell'iniettore, non il registro del prodotto: sono due
	#    voci diverse e mescolarle e' il modo di credere a chi manda.
	grep -a '^B33R: ' "$INILOG" 2>/dev/null | tail -n "${2:-40}"
	exit 0 ;;

# ---------------------------------------------------------------------------
monitor)
	# ⛔ Il conto e' DIVISO PER DUE: `GetCurrentState` elenca ogni schermo due
	#    volte (trovato da A1 il 14 agosto 2026).
	n=$(come_utente busctl --user call org.gnome.Mutter.DisplayConfig \
		/org/gnome/Mutter/DisplayConfig org.gnome.Mutter.DisplayConfig \
		GetCurrentState 2>/dev/null | tr ' ' '\n' | grep -c '"Meta-')
	printf 'MONITOR %s\n' "$((n / 2))"
	come_utente busctl --user call org.gnome.Mutter.DisplayConfig \
		/org/gnome/Mutter/DisplayConfig org.gnome.Mutter.DisplayConfig \
		GetCurrentState 2>&1 | tr ' ' '\n' \
		| grep -E '^"(Meta-[0-9]+|MetaVirtualMonitor|Virtual)' | sed 's/^/        /'
	exit 0 ;;

carico)
	# ⚠ Ogni misura di tempo porta accanto il carico: cinque banchi girano sulla
	#   stessa macchina, e un numero preso sotto carico e non dichiarato tale e'
	#   un numero falso (documento di fase §0-bis).
	printf 'CARICO %s\n' "$(uptime | sed 's/.*load average: //')"
	printf 'ORA %s\n' "$(date +%H:%M:%S)"
	printf 'SESSIONI_GNOME %s\n' "$(pgrep -c -x gnome-shell 2>/dev/null || echo 0)"
	printf 'REMOTIX_VIVI %s\n' "$(pgrep -c -x remotix 2>/dev/null || echo 0)"
	exit 0 ;;

accendi)
	log "Il server della sottofase 6.1, sulla $PORTA — DA ROOT"
	inf "$(vicini)"
	[ -x "$D/remotix" ] || { ko "⛔ $D/remotix non c'e'"; exit 2; }
	[ -f "$D/pagina.html" ] || { ko "⛔ $D/pagina.html non c'e'"; exit 2; }
	n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
	[ "$n" -eq 0 ] || { ko "⛔ la $PORTA e' gia' occupata"; exit 2; }
	[ -f /etc/pam.d/remotix ] || { ko "⛔ /etc/pam.d/remotix non c'e'"; exit 2; }
	mkdir -p "$CERT" "$RILIEVO"; chmod 1777 "$RILIEVO"
	# ⛔ Il registro si azzera a ogni accensione: una misura di CRESCITA su un
	#    file che portava dentro la corsa di ieri non e' una misura.
	: > "$LOG"
	export LD_LIBRARY_PATH="$LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
	ldd "$D/remotix" | grep -q 'not found' && {
		ko "⛔ manca una libreria:"; ldd "$D/remotix" | grep 'not found' | sed 's/^/        /'
		exit 2; }
	# ⛔ `--parlantina`: senza, `registro_dettaglio()` di `figlio.c` e di
	#    `input.c` finisce nel nulla e i rami sembrano «non scattati».  Una
	#    diagnostica che tace non e' neutra: mente (trappola 1).
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
	exit 0 ;;

registro)
	tail -n "${2:-60}" "$LOG" 2>/dev/null
	exit 0 ;;

conta)
	printf 'CONTA %s\n' "$(grep -c -- "${2:-input}" "$LOG" 2>/dev/null || echo 0)"
	exit 0 ;;

cerca)
	grep -n -- "${2:-input}" "$LOG" 2>/dev/null | tail -n "${3:-25}"
	exit 0 ;;

registro-byte)
	printf 'REGISTRO_BYTE %s\n' "$(stat -c %s "$LOG" 2>/dev/null || echo 0)"
	printf 'REGISTRO_RIGHE %s\n' "$(wc -l < "$LOG" 2>/dev/null || echo 0)"
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
	log "Tolgo l'utente della sottofase 6.1"
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
	if f=$(mio_figlio); then inf "figlio: $f"; else inf "figlio: nessuno"; fi
	inf "registro: $(stat -c %s "$LOG" 2>/dev/null || echo 0) byte"
	inf "testimone: $(pgrep -u "$UID_B" -f 06-b33-testimone | wc -l) vivo, $(wc -l < "$VISTO" 2>/dev/null || echo 0) righe viste"
	inf "terminale: $(pgrep -u "$UID_B" -f b33-ciclo-invii | wc -l) vivo, $(wc -l < "$INVII" 2>/dev/null || echo 0) Invio ricevuti"
	inf "$(uptime)"
	exit 0 ;;
esac
