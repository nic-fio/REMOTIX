#!/bin/bash
#
# 06-b35-terreno.sh — ⛔ GIRA SUL SERVER (NIC-OS), **FUORI** dal contenitore e
# **DA ROOT**.  Il terreno della SOTTOFASE 6.3 — *il palco che cambia misura*.
#
#   sudo bash .../06-b35-terreno.sh utente        crea `provap6` (uid 1008)
#   sudo bash .../06-b35-terreno.sh sessione      GNOME **senza** --virtual-monitor
#   sudo bash .../06-b35-terreno.sh sessione-via  ⛔ uccide la sessione grafica
#   sudo bash .../06-b35-terreno.sh scena         la scena che SI MUOVE
#   sudo bash .../06-b35-terreno.sh scena-via
#   sudo bash .../06-b35-terreno.sh accendi       il server sulla 7731
#   sudo bash .../06-b35-terreno.sh spegni
#   sudo bash .../06-b35-terreno.sh figlio        pid, CPU, registro
#   sudo bash .../06-b35-terreno.sh registro-da   marca il registro (offset)
#   sudo bash .../06-b35-terreno.sh registro-tela dalla marca in poi, le righe
#                                                 della tela — ⭐ e' LA MISURA
#   sudo bash .../06-b35-terreno.sh carico        uptime, per ogni riga di tempo
#   sudo bash .../06-b35-terreno.sh sessione-via-sfondo <s>
#   sudo bash .../06-b35-terreno.sh pulisci
#
# ===========================================================================
# ⛔ PERCHE' UN UTENTE TUTTO SUO, E LE CINQUE REGOLE DELL'ISOLAMENTO
# ===========================================================================
#
# `SPECIFICHE.md` §5.1: **una sola sessione grafica per utente**, e questa
# sottofase deve **uccidere la sessione grafica** per provocare il rimontaggio
# di `RCP.md` §7.1.  ⇒ `provap6`, uid 1008, che nasce e muore con questo banco.
# ⛔⛔ `prova` e la 7700 NON SI TOCCANO: sono il banco dell'utente.
#
# ⭐ E nel gruppo `render` **e `video`**: `[M]` senza, il codificatore ripiega in
#    software — 100 ms per fotogramma invece di 4,8 — e il banco misurerebbe il
#    ripiego invece del prodotto.
#
# ⛔ E **senza** `--virtual-monitor`: la cura di A1 (`FASI.md` §04-si-comanda).
#    Con quell'opzione il nostro `RecordVirtual` cattura uno schermo in piu',
#    vuoto: si misurerebbe un difetto gia' curato da un altro anello.
#
# ⛔ Ban, socket del comando, certificati e registro sono PROPRI: due server che
#    condividessero il file dei ban si metterebbero fuori uso a vicenda
#    (`RCP.md` §4.4-bis), e qui girano cinque banchi insieme.
#
# ===========================================================================
# ⛔ LE PORTE CHE NON SONO MIE — si CONTANO, non si toccano
# ===========================================================================
#
#   7448 · 7501 · 7561 · 7571 · 7601 · 7691 · 7700 · 7711-7715 · 7721-7725 ·
#   7751-7755 · 7761-7765 · 7781-7785
#
# Le mie sono la 7731-7735, e questo banco ne usa **una**: la 7731.
#
# ⚠ E l'orologio di questa macchina e' indietro di DUE ORE rispetto al
#   portatile: le ore che stampa sono le sue.
set -uo pipefail

PORTA=${PORTA:-7731}
IND=${IND:-192.168.0.2}
UTENTE=${UTENTE:-provap6}
UID_B=${UID_B:-1008}
PAROLA=${PAROLA:-provap6-2026}
D=${D:-/media/REMOTIX/src/06-p-src/src}
LAV=${LAV:-/media/REMOTIX/tmp/06-p}
LIBS=${LIBS:-/media/REMOTIX/src/b2/ngtcp2/build/lib:/media/REMOTIX/src/b2/ngtcp2/build/crypto/ossl:/media/REMOTIX/src/b2/prefisso/lib}
UNITA=org.gnome.Shell@wayland.service

CERT=$LAV/certificati
BAN=$LAV/ban
SOCK=$LAV/comando.sock
LOG=$LAV/registro.log
PIDF=$LAV/pid
RILIEVO=$LAV/rilievo
MARCA=$LAV/registro.marca

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ⛔ Le porte degli altri si CONTANO prima e dopo: se una sparisce mentre giro,
#    l'ho rotta io.  ⚠ E il conto si stampa, non si giudica qui.
vicini() {
	local r="" p
	for p in 7448 7501 7561 7571 7601 7691 7700 7711 7721 7751 7761 7781; do
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

# ⭐ Il figlio di QUESTO server, non un figlio qualunque: cinque banchi girano
#    sulla stessa macchina e `pgrep -f -- --figlio-interno` li prenderebbe tutti.
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
	# ⭐ `render` E `video`, o il codificatore ripiega in software: `[M]` 4,8 ms
	#    → 100 ms per fotogramma, e il banco misurerebbe il ripiego.
	for g in render video; do
		if getent group "$g" >/dev/null 2>&1; then
			usermod -aG "$g" "$UTENTE" && ok "nel gruppo «$g»"
		else
			ko "⛔ il gruppo «$g» non esiste"
		fi
	done
	inf "gruppi: $(id -nG "$UTENTE")"
	# ⛔ E si VERIFICA invece di sperare (forma E1: scritto non e' in vigore).
	case " $(id -nG "$UTENTE") " in
	*" render "*) ok "⭐ «render» in vigore: la codifica sara' in HARDWARE" ;;
	*) ko "⛔ «render» NON in vigore: misurerei il ripiego software"; exit 3 ;;
	esac
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

	# ⛔⭐ Le tre strade che NON funzionano sono misurate e scritte in
	#     `banchi/04-b31-terreno.sh`: qui si usa quella che funziona.
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
		#    /run/user/<uid> con dentro `user.control`, e senza questa riga
		#    l'`ExecStart` in vigore torna a quello di SISTEMA, con
		#    `--virtual-monitor`.  ⭐ Si RILEGGE invece di sperare.
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
	exec bash "$0" monitor ;;

sessione-via)
	# ⛔⭐ LA SCENA DEL «RIMONTAGGIO DOPO UNA CADUTA» — `RCP.md` §7.1 la nomina
	#     per prima: *«un rimontaggio della sessione grafica dopo una caduta»*.
	#     ⚠ Si uccide **solo la sessione**, non il figlio e non il server.
	log "⛔ Uccido la sessione grafica di $UTENTE — il figlio resta vivo"
	f=$(mio_figlio) && inf "il figlio del mio server e' il pid $f (resta vivo)"
	n=$(pgrep -u "$UID_B" -x gnome-shell | tr '\n' ' ')
	inf "gnome-shell: ${n:-nessuno}"
	come_utente gdbus call --session -d org.gnome.SessionManager \
		-o /org/gnome/SessionManager -m org.gnome.SessionManager.Logout 2 \
		>/dev/null 2>&1
	sleep 3
	pkill -u "$UID_B" -x gnome-shell 2>/dev/null
	g=0
	while [ $g -lt 30 ]; do
		pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 || break
		sleep 0.5; g=$((g+1))
	done
	pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 && {
		pkill -9 -u "$UID_B" -x gnome-shell 2>/dev/null; sleep 2; }
	if pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1; then
		ko "⛔ la sessione non e' morta: la scena NON e' quella che dico"; exit 3
	fi
	ok "la sessione grafica e' morta ($(date +%H:%M:%S.%3N))"
	if f=$(mio_figlio); then
		ok "⛔ e il figlio $f e' ANCORA VIVO — e' la scena del rimontaggio"
	else
		inf "il figlio non c'e' piu' (o non c'era)"
	fi
	exit 0 ;;

sessione-via-sfondo)
	# ⛔ La sessione la si uccide MENTRE il client e' attaccato, e il client sta
	#    in un'altra stretta di mano (dentro il contenitore).  ⚠ La redirezione
	#    sta QUI DENTRO, in un file sul server: attorno a `ssh`/`enter.sh` si
	#    mangerebbe la richiesta di `sudo` e il comando resterebbe appeso.
	rm -f "$LAV/sessione-via.txt"
	nohup bash -c "sleep ${2:-8}; bash '$0' sessione-via; sleep ${3:-2}; bash '$0' sessione" \
		> "$LAV/sessione-via.txt" 2>&1 &
	ok "armato: uccido la sessione fra ${2:-8} s e la rimetto ${3:-2} s dopo"
	exit 0 ;;

sessione-via-leggi)
	cat "$LAV/sessione-via.txt" 2>/dev/null
	exit 0 ;;

scena)
	# ⛔⭐ LA SCENA SI DICHIARA E SI MUOVE SEMPRE — `CODER.md` §3.2.
	#
	# ⛔ IL DIFETTO PIU' COSTOSO DI QUESTA ZONA, gia' pagato due volte: su
	#    Wayland il ridimensionamento **si compie solo quando il compositore
	#    consegna un fotogramma nuovo**, e su un desktop appena nato non cambia
	#    niente.  ⇒ Un desktop fermo fa apparire «rotto» un codice sano.
	#
	# ⚠ E il passo e' 50 ms e non 200: questo banco misura QUANTO CI METTE una
	#   tela a cambiare, e la risoluzione della misura non puo' essere piu'
	#   grossa del passo della scena.  Con 200 ms un ridimensionamento «a 41 ms»
	#   si leggerebbe come «a 200».
	log "La scena: una finestra che scrive l'ora ogni 50 ms, su $UTENTE"
	come_utente pkill -f 'banco-P6-scena' >/dev/null 2>&1
	come_utente setsid --fork gnome-terminal --title=banco-P6-scena -- \
		bash -c 'while true; do date +%H:%M:%S.%N; sleep 0.05; done' \
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
	come_utente pkill -f 'banco-P6-scena' 2>/dev/null
	ok "scena spenta"
	exit 0 ;;

monitor)
	# ⚠ E' un CONTROLLO, non la misura.  ⛔ E il conto e' DIVISO PER DUE:
	#    `GetCurrentState` elenca ogni schermo due volte (trovato da A1).
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
	log "Il server del banco P6, sulla $PORTA — DA ROOT"
	inf "$(vicini)"
	[ -x "$D/remotix" ] || { ko "⛔ $D/remotix non c'e'"; exit 2; }
	[ -f "$D/pagina.html" ] || { ko "⛔ $D/pagina.html non c'e'"; exit 2; }
	n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
	[ "$n" -eq 0 ] || { ko "⛔ la $PORTA e' gia' occupata"; exit 2; }
	[ -f /etc/pam.d/remotix ] || { ko "⛔ /etc/pam.d/remotix non c'e'"; exit 2; }
	mkdir -p "$CERT" "$RILIEVO"; chmod 1777 "$RILIEVO"
	# ⛔ Il registro si azzera a ogni accensione: una misura di crescita su un
	#    file che porta dentro la corsa di ieri non e' una misura.
	: > "$LOG"
	# ⛔⛔ E LA MARCA VA AZZERATA CON LUI — difetto trovato il 21 agosto 2026,
	#     con la prova in mano: `06-i/registro.marca` valeva **825 758** su un
	#     `registro.log` da **45 373 byte**.  ⇒ Ogni `tail -c "+$((M+1))"` dopo
	#     un riavvio non prendeva NIENTE, e `registro-tela`, `tempi` e
	#     `ricambi_dalla_marca` restituivano **zero** su un giro vero.
	#     ⚠ Uno zero che nessuno metteva in dubbio, perche' e' il numero che
	#     rassicura: e' `fasi/06 §5.2` un'altra volta.
	echo 0 > "$MARCA"
	export LD_LIBRARY_PATH="$LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
	ldd "$D/remotix" | grep -q 'not found' && {
		ko "⛔ manca una libreria:"; ldd "$D/remotix" | grep 'not found' | sed 's/^/        /'
		exit 2; }
	# ⭐ `--parlantina`: ⛔ IL FIGLIO SENZA PARLANTINA TACE IN SILENZIO, e ha
	#    gia' mentito nella direzione peggiore — per ore si e' concluso che certi
	#    rami «non scattavano mai» *perche' la loro riga non compariva*.
	#    `registro_dettaglio()` di `figlio.c` finisce nel nulla senza questa
	#    opzione, e proprio il ramo `GIA_COSI` di §7.1 e' scritto cosi'.
	nohup "$D/remotix" --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
		--certificati "$CERT" --pagina "$D/pagina.html" \
		--ban-file "$BAN" --comando-socket "$SOCK" \
		--parlantina \
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
	inf "$(vicini)"
	exit 0 ;;

parlantina-c-e)
	# ⛔⛔ SI VERIFICA CHE IL FIGLIO PARLI, **PER PRIMA COSA** — la trappola 1
	#     del documento di fase.  ⚠ Una diagnostica che tace non e' neutra:
	#     mente.  ⇒ Si cerca una riga che SOLO `registro_dettaglio()` puo'
	#     scrivere; se non c'e', tutto quel che segue e' un'assenza che non
	#     dimostra niente (`CODER.md` §3.10).
	log "⛔ Il figlio parla?  (senza --parlantina i rami TACCIONO in silenzio)"
	# ⛔⛔ DIFETTO DEL BANCO, TROVATO IL 21 AGOSTO 2026 E RIPRODOTTO:
	#     `m=$(grep -c ... || echo 0)` non vale zero, vale **«0\n0»**.
	#     `grep -c` stampa gia' «0» E ESCE CON 1 quando non trova niente ⇒ il
	#     `|| echo 0` ne aggiunge un secondo.  Poi `[ "$m" -gt 0 ]` moriva con
	#     *«integer expression expected»* — ⚠ e moriva **solo quando il conto
	#     era zero**, cioe' nell'unico caso per cui questa guardia esiste.
	#     ⛔ E `PARLANTINA_RIGHE` usciva su DUE righe: chi lo leggesse a
	#     macchina leggerebbe un numero che non c'e'.
	#     ⚠ `n` era per giunta calcolato e mai usato: tolto.
	#
	# ⛔ E lo zero si distingue dal fallimento (`LEZIONI.md` §1.9): un registro
	#    che non si legge NON e' «zero righe di dettaglio».
	if [ ! -r "$LOG" ]; then
		ko "⛔ il registro «$LOG» non si legge: non e' uno ZERO, e' un GUASTO"
		exit 3
	fi
	# `-a`: il registro puo' portarsi dentro byte non testuali, e senza questo
	# `grep` lo dichiarerebbe binario invece di contare.
	m=$(grep -acE 'senza palco e QUALCUNO GUARDA|ridimensionamento a .* e. la misura che il flusso HA|input [0-9]+ \(azione' "$LOG")
	u=$?
	case $u in
	0|1) : ;;
	*) ko "⛔ grep e' uscito con $u: il conto NON e' una misura"; exit 3 ;;
	esac
	[ -n "$m" ] || m=0
	printf 'PARLANTINA_RIGHE %s\n' "$m"
	if [ "$m" -gt 0 ]; then
		ok "⭐ trovate $m righe di registro_dettaglio(): il figlio PARLA"
	else
		ko "⛔ ZERO righe di dettaglio: o il ramo non scatta, o il figlio TACE"
		ko "   ⚠ e i due casi hanno la stessa faccia — non si va avanti"
		# ⛔ E si esce ROSSO: un verdetto rosso che esce 0 e' una trappola —
		#    chi incatena i comandi tira dritto sopra la riga che dice di
		#    fermarsi.
		exit 4
	fi
	exit 0 ;;

registro-da)
	# ⭐ La marca: da qui in poi e' il giro che sto misurando.  ⛔ Senza, si
	#    conterebbero anche le righe dei giri di prima — e i conti tornerebbero
	#    sbagliati nella direzione che rassicura.
	stat -c %s "$LOG" 2>/dev/null > "$MARCA" || echo 0 > "$MARCA"
	printf 'MARCA %s\n' "$(cat "$MARCA")"
	exit 0 ;;

registro-tela)
	# ⭐⭐ LA MISURA VERA DI QUESTO BANCO sta qui: le righe che la catena scrive.
	#    ⚠ Si stampano TUTTE, in ordine, con l'ora: il giudizio lo da' il
	#    programma che le legge, non questo `grep`.
	M=$(cat "$MARCA" 2>/dev/null); [ -n "$M" ] || M=0
	# ⛔ LA MARCA SCADUTA: se il registro e' stato azzerato da un `accendi` e la
	#    marca no, `tail -c` non prende niente e il banco conta ZERO su un giro
	#    che c'e' stato.  ⚠ Si dichiara, non si tace.
	B=$(stat -c %s "$LOG" 2>/dev/null); [ -n "$B" ] || B=0
	if [ "$M" -gt "$B" ]; then
		ko "⛔ MARCA SCADUTA: marca $M byte, registro $B byte."
		ko "   ⚠ Il registro e' stato azzerato dopo la marca: quel che segue"
		ko "     sarebbe uno ZERO PER COSTRUZIONE.  Rifai «registro-da»."
		exit 3
	fi
	tail -c "+$((M + 1))" "$LOG" 2>/dev/null | grep -aE \
		'TELA|tela|palco|MISURA DIVERGENTE|fotogramma SCARTATO|geometria|ridimensionament|CONCESSO DIVERSO|disaccordo|NON lo spedisco'
	exit 0 ;;

registro-coda)
	tail -n "${2:-80}" "$LOG" 2>/dev/null
	exit 0 ;;

carico)
	# ⚠ Ogni misura di tempo porta accanto il carico: cinque banchi girano sulla
	#   stessa macchina e cinque codificatori sullo stesso iGPU SPOSTANO i
	#   millisecondi.  ⛔ Un numero preso sotto carico e non dichiarato tale e'
	#   un numero falso.
	# ⛔ E lo stesso difetto di `parlantina-c-e`: `pgrep -c` stampa «0» e ESCE
	#    CON 1, quindi `|| echo 0` faceva uscire **due righe** — `REMOTIX_VIVI
	#    0` seguito da un `0` orfano.  Chi legge a macchina prende il numero
	#    sbagliato o si perde la riga dopo.
	conta_processi() {
		local c
		c=$(pgrep -c -x "$1")
		case $? in 0|1) : ;; *) printf '??'; return ;; esac
		printf '%s' "${c:-0}"
	}
	printf 'CARICO %s\n' "$(uptime | sed 's/.*load average: //')"
	printf 'ORA %s\n' "$(date +%Y-%m-%dT%H:%M:%S.%3N)"
	printf 'REMOTIX_VIVI %s\n' "$(conta_processi remotix)"
	printf 'GNOME_SHELL_VIVI %s\n' "$(conta_processi gnome-shell)"
	# ⚠ E il ferro, accanto a ogni numero: e' una **Intel UHD 730 integrata**,
	#   non una scheda potente (`LEZIONI.md` §1.1 — «quale scheda» accanto al
	#   millisecondo).  Qui si conta chi tiene APERTO il nodo di render: e' il
	#   denominatore della contesa sulla GPU.
	printf 'GPU_RENDERD128_APERTI %s\n' \
		"$(ls -l /proc/*/fd 2>/dev/null | grep -c 'renderD128')"
	exit 0 ;;

figlio)
	if f=$(mio_figlio); then
		printf 'FIGLIO %s\n' "$f"
		printf 'FIGLIO_STATO %s\n' "$(awk '{print $3}' /proc/$f/stat 2>/dev/null)"
	else
		printf 'FIGLIO nessuno\n'
	fi
	printf 'REGISTRO_BYTE %s\n' "$(stat -c %s "$LOG" 2>/dev/null || echo 0)"
	exit 0 ;;

spegni)
	log "Spengo la $PORTA"
	if ! pid=$(mio_pid); then ok "non c'era niente sulla $PORTA"; inf "$(vicini)"; exit 0; fi
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
	inf "carico: $(uptime | sed 's/.*load average: //')"
	exit 0 ;;
esac
