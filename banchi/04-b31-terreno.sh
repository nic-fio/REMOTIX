#!/bin/bash
#
# 04-b31-terreno.sh — ⛔ GIRA SUL SERVER (NIC-OS), **FUORI** dal contenitore e
# **DA ROOT**.  Prepara il terreno del banco O1 — *l'apparizione del desktop* —
# e accende il server sulla 7711.
#
#   sudo bash .../04-b31-terreno.sh utente        crea l'utente del banco
#   sudo bash .../04-b31-terreno.sh sessione      GNOME **senza** --virtual-monitor
#   sudo bash .../04-b31-terreno.sh sessione-via  ⛔ uccide la sessione grafica
#   sudo bash .../04-b31-terreno.sh scena         la scena che si muove
#   sudo bash .../04-b31-terreno.sh scena-via
#   sudo bash .../04-b31-terreno.sh accendi       il server sulla 7711
#   sudo bash .../04-b31-terreno.sh spegni
#   sudo bash .../04-b31-terreno.sh figlio        ⭐ il figlio: pid, CPU, registro
#   sudo bash .../04-b31-terreno.sh spia <s>      ⛔ quanto CRESCE il registro in <s>
#   sudo bash .../04-b31-terreno.sh monitor
#   sudo bash .../04-b31-terreno.sh pulisci
#
# ===========================================================================
# ⛔ PERCHE' UN UTENTE TUTTO SUO, E NON `prova`
# ===========================================================================
#
# `SPECIFICHE.md` §5.1: **una sola sessione grafica per utente**.  ⛔ E questo
# banco, per due delle sue tre scene, deve **uccidere la sessione grafica** —
# che su `prova` vorrebbe dire togliere all'utente l'unico posto dove oggi il
# desktop vero si vede (deciso il 14 agosto 2026).  ⇒ `provao1`, uid 1004, che
# nasce e muore con questo banco.
#
# ⭐ E nel gruppo `render`: `[M]` senza, il codificatore ripiega in software e
#    passa da 4,8 ms a 100 ms per fotogramma — cioe' il banco misurerebbe il
#    ripiego invece del prodotto.
#
# ⛔ E **senza** `--virtual-monitor`: e' la cura di A1 (`FASI.md` §04-si-comanda
#    §A1).  Con quell'opzione la shell resta sul monitor di casa e il nostro
#    `RecordVirtual` cattura uno schermo in piu', vuoto — cioe' il banco
#    misurerebbe un difetto gia' curato da un altro anello, e non il proprio.
#
# ===========================================================================
# ⛔ LE PORTE CHE NON SONO MIE — 7448 · 7501 · 7561 · 7571 · 7601 · 7691
# ===========================================================================
#
# Si CONTANO prima e dopo ogni azione, e non si toccano.  ⚠ E ban, socket del
# comando, certificati e registro sono PROPRI: due server che condividessero il
# file dei ban si metterebbero fuori uso a vicenda (`RCP.md` §4.4-bis).
set -uo pipefail

PORTA=${PORTA:-7711}
IND=${IND:-192.168.0.2}
UTENTE=${UTENTE:-provao1}
UID_B=${UID_B:-1004}
PAROLA=${PAROLA:-provao1-2026}
D=${D:-/media/REMOTIX/src/04-o1-src/src}
LAV=${LAV:-/media/REMOTIX/tmp/04-b31}
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
	for p in 7448 7501 7561 7571 7601 7691; do
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

# ⭐ Il figlio di QUESTO server, e non un figlio qualunque: si cerca fra i figli
#    del mio pid.  ⛔ `pgrep -f -- --figlio-interno` da solo prenderebbe i figli
#    dei server degli altri anelli, che girano sulla stessa macchina.
mio_figlio() {
	local s f
	s=$(mio_pid) || return 1
	for f in $(pgrep -P "$s" 2>/dev/null); do
		# ⚠ Fra il `pgrep` e questa riga il processo puo' essere morto, e la
		#   redirezione fallita la scrive la SHELL, non `tr`: `2>/dev/null` su
		#   `tr` non la prende.  ⛔ Un banco che stampa un errore che non e' un
		#   errore si legge come un banco rotto.
		[ -r "/proc/$f/cmdline" ] || continue
		case "$(tr '\0' ' ' < "/proc/$f/cmdline" 2>/dev/null)" in
		*--figlio-interno*) echo "$f"; return 0 ;;
		esac
	done
	return 1
}

# I tick di CPU consumati da un processo (utime + stime), da /proc.
cpu_tick() {
	local p=$1 c
	c=$(awk '{print $14+$15}' "/proc/$p/stat" 2>/dev/null) || return 1
	[ -n "$c" ] && echo "$c" || return 1
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
	# ⛔ Qui c'era il solo `render`, per NOME e senza rileggere: mancava `video`
	#    (il gruppo di `cardN`), che e' meta' della cura di fase 10 §7.4.
	gruppi_scheda_dai_a "$UTENTE" || exit 3
	inf "gruppi: $(id -nG "$UTENTE")"
	loginctl enable-linger "$UTENTE" || { ko "⛔ enable-linger fallito"; exit 2; }
	ok "linger acceso: /run/user/$UID_B vivra' anche senza nessuno collegato"
	exit 0 ;;

sessione)
	log "La sessione GNOME di $UTENTE — ⭐ SENZA --virtual-monitor (la cura di A1)"
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
		exec bash "$0" monitor
	fi

	# ⛔⭐ COME SI RIMETTE IN PIEDI UNA SESSIONE CHE ABBIAMO UCCISO — e le tre
	#     strade che NON funzionano, misurate una per una il 14 agosto 2026:
	#
	#   · `systemctl --user start org.gnome.Shell@wayland.service` ⇒ ⛔ *«may be
	#     requested by dependency only»*;
	#   · `systemctl --user stop|start gnome-session-manager@gnome.service` ⇒ ⛔
	#     lo stesso rifiuto;
	#   · un `gnome-session --session=gnome` nuovo mentre il gestore e' ancora
	#     **active** ⇒ ⛔ esce **in silenzio**, e il sintomo e' «la sessione non
	#     e' partita in 60 s» con un registro VUOTO — cioe' il banco accusava la
	#     macchina di una cosa che non aveva fatto.
	#
	# ⇒ ⭐ La strada che funziona: il congedo si CHIEDE al gestore
	#   (`org.gnome.SessionManager.Logout 2`, in `sessione-via`), si aspetta che
	#   diventi **inactive**, e allora `gnome-session` riparte.
	# ⛔ E `terminate-user` resta l'ULTIMA SPIAGGIA, dichiarata: butta giu' anche
	#    il figlio del server, e in due scene di questo banco e' proprio la sua
	#    sopravvivenza il difetto da mostrare.
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
		ko "⛔ e questo uccide anche il figlio del server: la scena cambia"
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
		#    l'`ExecStart` in vigore torna a essere quello di SISTEMA, con
		#    `--virtual-monitor`.  ⭐ Il banco se n'e' accorto da solo perche'
		#    RILEGGE invece di sperare.
		install -d -o "$UID_B" -g "$UID_B" -m 700 "$DIR" || { ko "⛔ non ho rifatto $DIR"; exit 2; }
		printf '[Service]\nExecStart=\nExecStart=/usr/bin/gnome-shell --headless --no-x11\n' > "$FILE"
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
	# ⛔ SCRITTO NON E' IN VIGORE (forma E1): si rilegge dal gestore, e si guarda
	#    anche l'ASSENZA — e' proprio l'assenza che serve qui.
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
	# ⛔⭐ LA SCENA DEL PRIMO DIFETTO GEMELLO: la sessione grafica muore SOTTO un
	#     figlio vivo.  ⚠ Si uccide **solo la sessione**, non il figlio e non il
	#     server: e' precisamente la differenza che il difetto sfrutta.
	log "⛔ Uccido la sessione grafica di $UTENTE — il figlio resta vivo"
	f=$(mio_figlio) && inf "il figlio del mio server e' il pid $f (resta vivo)"
	n=$(pgrep -u "$UID_B" -x gnome-shell | tr '\n' ' ')
	inf "gnome-shell: ${n:-nessuno}"
	# ⛔⭐ IL CONGEDO SI CHIEDE AL GESTORE, non si `stop`pa l'unita': `[M]` 14
	#     agosto 2026, `systemctl --user stop gnome-session-manager@gnome` esce
	#     *«may be requested by dependency only»* — e la sessione resta in piedi
	#     con l'aria di essere stata fermata.
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
	if pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1; then
		pkill -9 -u "$UID_B" -x gnome-shell 2>/dev/null; sleep 2
	fi
	if pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1; then
		ko "⛔ la sessione non e' morta: la scena NON e' quella che dico"; exit 3
	fi
	ok "la sessione grafica e' morta"
	# ⛔⭐ E ANCHE PIPEWIRE, e NON e' accanimento: e' la differenza fra due
	#     scene, MISURATA.
	#
	# `[M]` 14 agosto 2026: uccidendo il solo `gnome-shell`, il flusso PipeWire
	# resta vivo e `cattura_prendi` continua a tornare **ZERO** — quattro attese
	# a vuoto al secondo, una riga di registro al secondo, nessun ciclo a vuoto.
	# ⛔ Cioe' il banco diceva VERDE, e il difetto dell'utente non compariva.
	#
	# ⚠ Il registro della sessione vera dice `connection error`, che e' il
	#   messaggio della **connessione al demone PipeWire caduta** — cioe' quel
	#   che succede quando se ne va la sessione dell'utente INTERA, non il solo
	#   compositore.  ⇒ La scena si fa faithful, e si dichiara quale delle due e'.
	come_utente systemctl --user stop wireplumber.service >/dev/null 2>&1
	come_utente systemctl --user stop pipewire.service pipewire.socket >/dev/null 2>&1
	come_utente systemctl --user stop pipewire-pulse.service pipewire-pulse.socket >/dev/null 2>&1
	pkill -u "$UID_B" -x pipewire 2>/dev/null
	pkill -u "$UID_B" -x wireplumber 2>/dev/null
	sleep 1
	if pgrep -u "$UID_B" -x pipewire >/dev/null 2>&1; then
		ko "⚠ PipeWire e' ancora vivo: la cattura NON andra' in «connection error»"
	else
		ok "⛔ e anche PipeWire se n'e' andato: e' la scena del «connection error»"
	fi
	if f=$(mio_figlio); then
		ok "⛔ e il figlio $f e' ANCORA VIVO — e' esattamente la scena del difetto"
	else
		inf "il figlio non c'e' piu' (o non c'era)"
	fi
	exit 0 ;;

scena)
	# ⛔⭐ LA SCENA SI DICHIARA E SI MUOVE SEMPRE — `CODER.md` §3.2.  Con la
	#     cattura a `framerate 0/1` su un desktop FERMO non arriva un solo
	#     fotogramma: un banco che misurasse li' misurerebbe la scena.
	# ⚠ E qui la scena serve a una cosa in piu': senza, «il primo pixel vero non
	#   arriva mai» e «il desktop e' fermo» avrebbero la stessa faccia.
	log "La scena: una finestra che scrive l'ora, sulla sessione di $UTENTE"
	come_utente pkill -f 'banco-O1-scena' >/dev/null 2>&1
	come_utente setsid --fork gnome-terminal --title=banco-O1-scena -- \
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
	come_utente pkill -f 'banco-O1-scena' 2>/dev/null
	ok "scena spenta"
	exit 0 ;;

monitor)
	# ⚠ E' un CONTROLLO, non la misura: `GetCurrentState` dice quanti schermi ci
	#   sono, non su quale sta la barra.  Il verdetto lo da' il giudice sui pixel.
	# ⛔ E il conto e' DIVISO PER DUE: `GetCurrentState` elenca ogni schermo due
	#    volte (trovato da A1 il 14 agosto 2026, e sbagliava nella direzione che
	#    rassicura).
	n=$(come_utente busctl --user call org.gnome.Mutter.DisplayConfig \
		/org/gnome/Mutter/DisplayConfig org.gnome.Mutter.DisplayConfig \
		GetCurrentState 2>/dev/null | tr ' ' '\n' | grep -c '"Meta-')
	printf 'MONITOR %s\n' "$((n / 2))"
	come_utente busctl --user call org.gnome.Mutter.DisplayConfig \
		/org/gnome/Mutter/DisplayConfig org.gnome.Mutter.DisplayConfig \
		GetCurrentState 2>&1 | tr ' ' '\n' \
		| grep -E '^"(Meta-[0-9]+|MetaVirtualMonitor|Virtual)' | sed 's/^/        /'
	exit 0 ;;

accendi)
	log "Il server del banco O1, sulla $PORTA — DA ROOT"
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
	nohup "$D/remotix" --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
		--certificati "$CERT" --pagina "$D/pagina.html" \
		--ban-file "$BAN" --comando-socket "$SOCK" \
		--rilievo "$RILIEVO" >> "$LOG" 2>&1 &
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

figlio)
	# ⭐ Chi e' il figlio, e come sta.  ⛔ Le due grandezze che il difetto del
	#    ciclo a vuoto muove sono la CPU e il REGISTRO: si leggono tutt'e due,
	#    perche' una sola non distingue «gira a vuoto in silenzio» da «scrive».
	if f=$(mio_figlio); then
		printf 'FIGLIO %s\n' "$f"
		printf 'FIGLIO_TICK %s\n' "$(cpu_tick "$f")"
		printf 'FIGLIO_STATO %s\n' "$(awk '{print $3}' /proc/$f/stat 2>/dev/null)"
	else
		printf 'FIGLIO nessuno\n'
	fi
	printf 'REGISTRO_BYTE %s\n' "$(stat -c %s "$LOG" 2>/dev/null || echo 0)"
	printf 'HZ %s\n' "$(getconf CLK_TCK)"
	exit 0 ;;

spia-sfondo)
	# ⛔⭐ LA SPIA SI ARMA PRIMA, e gira MENTRE il client e' attaccato.
	#
	#     `[M]` 14 agosto 2026: una spia lanciata DOPO il client misurava un
	#     figlio che non guarda piu' nessuno — `codec_chiesto` a zero, `poll`
	#     con il tetto, CPU a zero.  ⛔ Diceva VERDE su un figlio che un minuto
	#     prima bruciava un nucleo intero.
	rm -f "$LAV/spia-sfondo.txt"
	nohup bash -c "sleep ${2:-6}; bash '$0' spia ${3:-3}" > "$LAV/spia-sfondo.txt" 2>&1 &
	ok "spia armata: fra ${2:-6} s, finestra ${3:-3} s"
	exit 0 ;;

spia-sfondo-leggi)
	cat "$LAV/spia-sfondo.txt" 2>/dev/null
	exit 0 ;;

gemello1-sfondo)
	# ⛔⭐ LA SCENA DEL PRIMO GEMELLO, TUTTA DA UNA PARTE SOLA — e non e' una
	#     comodita': e' l'unico modo perche' il client resti ATTACCATO mentre la
	#     sessione grafica muore.
	#
	# `[M]` 14 agosto 2026, primo giro: il client girava dentro il contenitore,
	# lanciato con `nohup` da una stretta di mano `ssh` che finiva subito dopo.
	# ⛔ Alla chiusura della stretta di mano il client moriva, `codec_chiesto`
	# tornava a zero, e il ciclo si metteva ad aspettare sul socket: **il banco
	# diceva VERDE sul difetto vivo** (`CODER.md` §3.4, la forma peggiore).
	# ⇒ Adesso il client resta in primo piano nella SUA stretta di mano, e la
	#   sessione la uccide questo script, in sottofondo, sull'host.
	rm -f "$LAV/gemello1.txt"
	nohup bash "$0" gemello1 "${2:-8}" "${3:-3}" > "$LAV/gemello1.txt" 2>&1 &
	ok "gemello1 armato: uccido la sessione fra ${2:-8} s, spia ${3:-3} s"
	exit 0 ;;

gemello1-leggi)
	cat "$LAV/gemello1.txt" 2>/dev/null
	exit 0 ;;

gemello1)
	sleep "${2:-8}"
	bash "$0" sessione-via
	# ⚠ Un secondo perche' il flusso PipeWire se ne accorga: la morte della
	#   sessione e il `connection error` non sono lo stesso istante.
	sleep 1
	bash "$0" spia "${3:-3}"
	bash "$0" tronca
	exit 0 ;;

sonda-gdb-sfondo)
	rm -f "$LAV/sonda-gdb.txt"
	nohup bash "$0" sonda-gdb "${2:-2.5}" > "$LAV/sonda-gdb.txt" 2>&1 &
	ok "sonda gdb accesa, esce in $LAV/sonda-gdb.txt"
	exit 0 ;;

sonda-gdb-leggi)
	cat "$LAV/sonda-gdb.txt" 2>/dev/null
	exit 0 ;;

sonda-gdb)
	# ⛔⭐ E QUANDO IL NUMERO DELLA CHIAMATA NON BASTA, SI GUARDA LA PILA.
	#
	#     `[M]` 14 agosto 2026: due giri della sonda leggera hanno dato due
	#     risposte diverse sullo stesso difetto (`futex` in uno, `recvmsg`
	#     nell'altro) — ⛔ cioe' il campionamento a 50 ms non basta a dire dove
	#     e' fermo il figlio, e due misure sotto la stessa etichetta sono
	#     peggio di nessuna misura.  ⇒ Si chiede a `gdb`, una volta sola, nel
	#     mezzo del buco.
	#
	# ⚠ `gdb` FERMA il processo per il tempo dell'istantanea: e' un attrezzo di
	#   diagnosi, non una misura di tempo, e non si lascia acceso durante un
	#   giro cronometrato.
	D=${2:-2.5}
	g=0
	while [ $g -lt 600 ]; do
		f=$(mio_figlio) && break
		sleep 0.05; g=$((g+1))
	done
	f=$(mio_figlio) || { printf 'SONDA nessun_figlio\n'; exit 4; }
	printf 'SONDA_FIGLIO %s (istantanea fra %s s)\n' "$f" "$D"
	sleep "$D"
	printf '=== %s ===\n' "$(date +%H:%M:%S.%3N)"
	gdb -p "$f" -batch -ex 'thread 1' -ex 'bt 25' 2>&1 \
		| grep -vE '^\[New LWP' | head -40
	exit 0 ;;

sonda-sfondo)
	# ⚠ La sonda va accesa PRIMA che il client si attacchi, e il client gira
	#   dentro il contenitore: sono due strette di mano diverse.  ⛔ La
	#   redirezione sta QUI DENTRO, in un file sul server, e non attorno a
	#   `ssh`/`enter.sh` — dove si mangerebbe la richiesta di parola d'ordine di
	#   `sudo` e il comando resterebbe appeso in silenzio.
	rm -f "$LAV/sonda.txt"
	nohup bash "$0" sonda "${2:-10}" > "$LAV/sonda.txt" 2>&1 &
	ok "sonda accesa in sottofondo, esce in $LAV/sonda.txt"
	exit 0 ;;

sonda-leggi)
	cat "$LAV/sonda.txt" 2>/dev/null
	exit 0 ;;

sonda)
	# ⛔⭐ DOVE STA IL FIGLIO MENTRE L'UTENTE ASPETTA — e non si deduce, si
	#     CHIEDE AL NUCLEO (`CODER.md` §3.7).
	#
	#     `[M]` 14 agosto 2026: il registro dice *«0 attese a vuoto»* fra
	#     l'accensione del canale video e il primo fotogramma, cioe' il ciclo
	#     **non ha girato affatto** per quattro secondi.  ⇒ La domanda non e'
	#     «perche' Mutter non consegna», e' **«in quale chiamata di sistema e'
	#     fermo il figlio?»** — e la risposta sta in `/proc/<pid>/syscall` e
	#     `/proc/<pid>/wchan`, non in una deduzione.
	#
	# ⚠ Si aspetta che il figlio NASCA (non c'e' quando parte questo comando) e
	#   poi si campiona.  ⛔ E il numero della chiamata si stampa com'e': una
	#   tabella dei nomi qui dentro sarebbe una traduzione che puo' sbagliare.
	S=${2:-8}
	g=0
	while [ $g -lt 600 ]; do
		f=$(mio_figlio) && break
		sleep 0.05; g=$((g+1))
	done
	f=$(mio_figlio) || { printf 'SONDA nessun_figlio\n'; exit 4; }
	printf 'SONDA_FIGLIO %s\n' "$f"
	n=$(awk "BEGIN{print int($S*10)}")
	i=0
	while [ $i -lt "$n" ]; do
		[ -d "/proc/$f" ] || { printf 'SONDA figlio_morto\n'; break; }
		# ⛔ TUTTI i fili, non solo il primo: «il filo principale aspetta un
		#    futex» non dice ancora **quale** futex, e il ciclo di PipeWire vive
		#    su un filo suo.  ⚠ Guardando il solo filo principale, «aspetta il
		#    lucchetto della cattura» e «aspetta il fotogramma» hanno la stessa
		#    faccia.
		printf '%s' "$(date +%H:%M:%S.%3N)"
		for t in /proc/$f/task/*; do
			printf '  [%s %s %s]' "${t##*/}" \
				"$(cut -d' ' -f1 "$t/syscall" 2>/dev/null)" \
				"$(cat "$t/wchan" 2>/dev/null)"
		done
		printf '\n'
		sleep 0.1; i=$((i+1))
	done
	exit 0 ;;

spia)
	# ⛔⭐ LA MISURA DEL PRIMO DIFETTO GEMELLO, E HA DUE GRANDEZZE.
	#
	#     `[M]` la sessione vera del 14 agosto: 30,8 GB di registro e 112 milioni
	#     di righe identiche, tutte nello stesso millisecondo.  ⇒ Quel che si
	#     misura e' la **crescita del registro** (byte al secondo) e la **CPU
	#     bruciata** dal figlio (frazione di un nucleo).
	#
	# ⚠ E la finestra e' corta apposta: su una macchina vera questo difetto
	#   riempie il disco, e un banco che lo lasciasse correre trenta secondi
	#   sarebbe lui il guasto.  ⛔ Il registro si TRONCA subito dopo.
	S=${2:-3}
	f=$(mio_figlio) || { printf 'SPIA nessun_figlio\n'; exit 4; }
	t0=$(cpu_tick "$f") || { printf 'SPIA figlio_sparito\n'; exit 4; }
	b0=$(stat -c %s "$LOG" 2>/dev/null || echo 0)
	sleep "$S"
	t1=$(cpu_tick "$f") || { printf 'SPIA figlio_morto_durante\n'; exit 4; }
	b1=$(stat -c %s "$LOG" 2>/dev/null || echo 0)
	hz=$(getconf CLK_TCK)
	printf 'SPIA_SECONDI %s\n' "$S"
	printf 'SPIA_TICK %s\n' "$((t1 - t0))"
	printf 'SPIA_HZ %s\n' "$hz"
	printf 'SPIA_BYTE %s\n' "$((b1 - b0))"
	printf 'SPIA_REGISTRO_TOTALE %s\n' "$b1"
	exit 0 ;;

tronca)
	# ⚠ Si tiene la coda, che e' la prova, e si butta il resto: un registro da
	#   qualche giga non si porta a casa e non si legge.
	if [ -f "$LOG" ]; then
		tail -c 200000 "$LOG" > "$LOG.coda" 2>/dev/null
		: > "$LOG"
		cat "$LOG.coda" >> "$LOG" 2>/dev/null
		rm -f "$LOG.coda"
	fi
	ok "registro troncato a $(stat -c %s "$LOG" 2>/dev/null || echo 0) byte"
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
	if f=$(mio_figlio); then inf "figlio: $f"; else inf "figlio: nessuno"; fi
	inf "registro: $(stat -c %s "$LOG" 2>/dev/null || echo 0) byte"
	exit 0 ;;
esac
