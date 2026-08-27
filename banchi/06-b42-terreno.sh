#!/bin/bash
#
# 06-b42-terreno.sh — ⛔ GIRA SUL SERVER (NIC-OS), **FUORI** dal contenitore e
# **DA ROOT**.  UNA sessione grafica completa, e questo banco ne accende CINQUE.
#
#   UTENTE=provac1 UID_B=1030 PORTA=7811 LAV=/media/REMOTIX/tmp/06-c/c1 \
#     sudo -E bash .../06-b42-terreno.sh utente|sessione|scena|accendi|...
#
#   utente        crea l'utente, gruppi `render` e `video`, linger
#   sessione      GNOME headless **senza** --virtual-monitor
#   scena         la scena che SI MUOVE (un terminale che scrive l'ora)
#   scena-via
#   accendi       il server remotix sulla sua porta
#   spegni
#   monitor       quanti schermi vede Mutter (⚠ e' un controllo, non la misura)
#   registro-da   marca il registro (offset)
#   carico        uptime + conteggi, per ogni riga di tempo
#   cpu           ⭐ il tempo di CPU di gnome-shell e del figlio — e' la PROVA
#                 che questa sessione sta davvero componendo, non solo esistendo
#   stato · pulisci
#
# ===========================================================================
# ⛔ PERCHE' ESISTE, INVECE DI RIUSARE `06-b35-terreno.sh`
# ===========================================================================
#
# Perche' quello e' **di un altro agente, che ci lavora adesso**, e perche' e'
# scritto per **una** sessione (`provap6`, uid 1008, porta 7731).  Qui servono
# **cinque** sessioni indipendenti, e l'identita' arriva TUTTA dall'ambiente:
# `UTENTE`, `UID_B`, `PORTA`, `LAV`.  ⛔ Nessun valore di quel banco compare
# qui come predefinito: un predefinito sbagliato accenderebbe una sessione
# sull'utente di qualcun altro, e `SPECIFICHE.md` §5.1 dice **una sola sessione
# grafica per utente** — gliela porterei via.
#
# ⭐ Il grosso del contenuto e' ripreso da `banchi/06-b35-terreno.sh` e da
#    `banchi/04-b31-terreno.sh`, comprese le trappole gia' pagate.  ⚠ Le
#    ripeto invece di citarle perche' un banco che rimanda per le sue trappole
#    e' un banco che le ripaga.
#
# ===========================================================================
# ⛔ LE TRAPPOLE, E OGNUNA E' GIA' COSTATA
# ===========================================================================
#
#  1. ⛔ **il gruppo `render` (e `video`)**: senza, il codificatore ripiega in
#     software — `[M]` 100 ms per fotogramma invece di 4,8 — e la sessione non
#     tocca l'iGPU.  ⇒ si VERIFICA che sia in vigore, e si esce rosso;
#  2. ⛔ **senza `--virtual-monitor`**: con quell'opzione si cattura uno schermo
#     in piu', vuoto (la cura di A1, `FASI.md` §04-si-comanda);
#  3. ⛔ **la parola d'ordine non passa MAI da `argv`** (difetto D12): file
#     `0600` scritto con `printf`, dato a `chpasswd` sullo **standard input**, e
#     una `trap` che lo cancella anche se il giro muore a meta';
#  4. ⛔ **ban-file, socket, certificati e registro PROPRI**: due server che
#     condividessero il file dei ban si metterebbero fuori uso a vicenda
#     (`RCP.md` §4.4-bis), e qui ne girano cinque MIEI piu' quelli di nove
#     altri agenti;
#  5. ⛔ **`--parlantina`**: senza, `registro_dettaglio()` di `figlio.c` finisce
#     nel nulla e i rami sembrano «non scattati».  Una diagnostica che tace non
#     e' neutra: mente;
#  6. ⛔ **la marca del registro si azzera con il registro** (difetto trovato il
#     21 agosto 2026): una marca piu' grande del file fa restituire ZERO a ogni
#     `tail -c`, e lo zero e' il numero che rassicura;
#  7. ⛔ **una sessione headless senza nessuno attaccato NON COMPONE NIENTE**:
#     `gnome-shell --headless --no-x11` senza monitor virtuale non ha una
#     superficie su cui disegnare finche' un `RecordVirtual` non gliela crea.
#     ⇒ Una «sessione di contesa» senza un client attaccato e' un processo
#     fermo con un nome altisonante.  ⚠ Per questo il comando `cpu` esiste, ed
#     e' quello che il banco guarda prima di credere alla scena.
#
# ===========================================================================
# ⛔ LE PORTE — le mie sono 7811-7815, le altre si CONTANO e non si toccano
# ===========================================================================
#
#   ⛔⛔ INTOCCABILI: **7700** e **7730** e l'utente **`prova`**.  La **7781**
#        e' del coordinatore.
#
# ⚠ E l'orologio di questa macchina e' indietro di DUE ORE rispetto al
#   portatile: le ore che stampa sono le sue.
#
# ⚠ Il ferro: **Intel UHD 730 integrata**, 20 core.  Va detto accanto a ogni
#   numero.
set -uo pipefail

# ⛔ NESSUN PREDEFINITO PER L'IDENTITA': un errore qui accende una sessione
#    sull'utente di un altro agente.  Si pretende, non si indovina.
UTENTE=${UTENTE:-}
UID_B=${UID_B:-}
PORTA=${PORTA:-}
LAV=${LAV:-}
IND=${IND:-192.168.0.2}
D=${D:-/media/REMOTIX/src/06-c-src/src}
LIBS=${LIBS:-/media/REMOTIX/src/b2/ngtcp2/build/lib:/media/REMOTIX/src/b2/ngtcp2/build/crypto/ossl:/media/REMOTIX/src/b2/prefisso/lib}
UNITA=org.gnome.Shell@wayland.service

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


for v in UTENTE UID_B PORTA LAV; do
	if [ -z "${!v}" ]; then
		ko "⛔ manca «$v» nell'ambiente: questo banco NON indovina l'identita'"
		ko "   di una sessione — indovinarla vuol dire portarla via a qualcuno."
		exit 2
	fi
done
case "$UTENTE" in
prova|prova2|provai6|provat6|provap6|provaw6|provao1|provaa7|provav7|provar7)
	ko "⛔ «$UTENTE» e' di un ALTRO banco che sta lavorando adesso: mi fermo."
	exit 2 ;;
esac
case "$PORTA" in
7700|7730|7781) ko "⛔ la porta $PORTA e' intoccabile: mi fermo."; exit 2 ;;
esac
[ "$PORTA" -ge 7811 ] && [ "$PORTA" -le 7815 ] || {
	ko "⛔ la porta $PORTA non e' fra le mie (7811-7815): mi fermo."; exit 2; }

PAROLA=${PAROLA:-$UTENTE-2026}
CERT=$LAV/certificati
BAN=$LAV/ban
SOCK=$LAV/comando.sock
LOG=$LAV/registro.log
PIDF=$LAV/pid
RILIEVO=$LAV/rilievo
MARCA=$LAV/registro.marca
SCENA_MARCA="banco-C-scena-$UTENTE"

# ⛔ Le porte degli altri si CONTANO prima e dopo: se una sparisce mentre giro,
#    l'ho rotta io.  ⚠ Il conto si stampa, non si giudica qui.
vicini() {
	local r="" p
	for p in 7448 7501 7561 7571 7601 7691 7700 7711 7721 7730 7731 7751 7761 7771 7781 7791; do
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

# ⭐ Il figlio di QUESTO server: sulla macchina ne girano una dozzina.
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

# ⭐ I tick di CPU (utime+stime) di un pid — la prova che un processo LAVORA.
tick() {
	local p=$1
	[ -r "/proc/$p/stat" ] || { printf '0'; return; }
	awk '{ n = NF; print $(14) + $(15) }' "/proc/$p/stat" 2>/dev/null || printf '0'
}

[ "$(id -u)" -eq 0 ] || { ko "⛔ va lanciato DA ROOT"; exit 2; }
mkdir -p "$LAV"

case "${1:-stato}" in
utente)
	log "L'utente del banco: $UTENTE (uid $UID_B), porta $PORTA"
	inf "$(vicini)"
	if id "$UTENTE" >/dev/null 2>&1; then
		ok "c'e' gia' — non lo rifaccio (una sessione per utente, I2)"
	else
		useradd -m -u "$UID_B" -s /bin/bash "$UTENTE" || {
			ko "⛔ useradd non e' riuscito"; exit 2; }
		ok "creato"
	fi
	# ⛔ D12: la parola non passa MAI da `argv`.  File 0600, `chpasswd` la
	#    legge dallo standard input, e la `trap` lo cancella comunque vada.
	PF=$(mktemp "$LAV/.parola-utente.XXXXXX") || { ko "⛔ mktemp"; exit 2; }
	trap 'rm -f "$PF"' EXIT
	chmod 600 "$PF"
	printf '%s:%s\n' "$UTENTE" "$PAROLA" > "$PF"
	chpasswd < "$PF" || {
		ko "⛔ la parola d'ordine non e' stata posta: PAM dira' sempre di no"
		exit 2; }
	rm -f "$PF"
	ok "parola d'ordine posta (da file 0600, mai da argv — D12)"
	# ⛔ Qui c'erano i due nomi INCHIODATI, e un `usermod` fallito non fermava
	#    niente: il banco tirava dritto e misurava una sessione cieca.
	gruppi_scheda_dai_a "$UTENTE" || exit 3
	inf "gruppi: $(id -nG "$UTENTE")"
	loginctl enable-linger "$UTENTE" || { ko "⛔ enable-linger fallito"; exit 2; }
	ok "linger acceso: /run/user/$UID_B vivra' anche senza nessuno collegato"
	exit 0 ;;

sessione)
	log "La sessione GNOME di $UTENTE — ⭐ SENZA --virtual-monitor (la cura di A1)"
	id "$UTENTE" >/dev/null 2>&1 || { ko "⛔ l'utente non c'e': fai «utente»"; exit 2; }

	DIR="/run/user/$UID_B/systemd/user.control/$UNITA.d"
	FILE="$DIR/zz-senza-monitor.conf"
	install -d -o "$UID_B" -g "$UID_B" -m 700 "$DIR" || { ko "⛔ non ho fatto $DIR"; exit 2; }
	printf '[Service]\nExecStart=\nExecStart=/usr/bin/gnome-shell --headless --no-x11\n' > "$FILE"
	chown "$UID_B:$UID_B" "$FILE"

	if pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1; then
		ok "c'e' gia' una sessione viva — non la rifaccio"
		exec bash "$0" monitor
	fi

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
		#    /run/user/<uid> con dentro `user.control`.
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
		ko "⛔ PipeWire NON e' vivo: la cattura non trovera' nessun nodo"
		exit 3
	fi
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

scena)
	# ⛔⭐ LA SCENA SI DICHIARA E SI MUOVE SEMPRE — `CODER.md` §3.2.  Su
	#     Wayland il ridimensionamento si compie solo quando il compositore
	#     consegna un fotogramma NUOVO: su un desktop fermo un codice sano
	#     sembra rotto.  ⚠ E il passo e' 50 ms, non 200: la risoluzione della
	#     misura non puo' essere piu' grossa del passo della scena.
	# ⚠ `scena [quante]`: la sessione MISURATA ne vuole **una** — e' la scena
	#   della 6.3, e cambiarla cambierebbe la misura da confrontare col 16
	#   agosto.  Le sessioni di CONTESA ne vogliono di piu': una sola finestra
	#   fa lavorare `gnome-shell` `[M]` all'8,8 % di un core, e quattro sessioni
	#   cosi' su venti core non contendono niente.  ⛔ E si DICHIARA, perche' un
	#   carico gonfiato in silenzio e' una scena diversa da quella detta.
	QUANTE=${2:-1}
	log "La scena di $UTENTE: $QUANTE terminali che scrivono l'ora ogni 50 ms"
	come_utente pkill -f "$SCENA_MARCA" >/dev/null 2>&1
	sleep 1
	for k in $(seq 1 "$QUANTE"); do
		# ⛔ LA MARCA VA DENTRO IL CICLO, non solo nel titolo.  `gnome-terminal`
		#    e' un client: chi resta vivo e' il `bash` figlio del
		#    `gnome-terminal-server`, e nella SUA riga di comando il titolo non
		#    compare.  ⇒ `pkill -f <marca>` non avrebbe spento niente, e la
		#    scena sarebbe sopravvissuta a `scena-via` — cioe' al giro «a
		#    riposo» sarebbero rimaste accese le scene dei contendenti.
		#    ⚠ Il commento in coda finisce in `argv`, ed e' li' che si vede.
		come_utente setsid --fork gnome-terminal --title="$SCENA_MARCA-$k" -- \
			bash -c "while true; do date +%H:%M:%S.%N; sleep 0.05; done # $SCENA_MARCA-$k" \
			>/dev/null 2>&1
		sleep 1
	done
	sleep 5
	n=$(pgrep -u "$UID_B" -f 'while true; do date' 2>/dev/null | wc -l)
	m=$(pgrep -u "$UID_B" -f 'gnome-terminal-server' 2>/dev/null | wc -l)
	inf "cicli che scrivono l'ora: $n (chiesti $QUANTE) · gnome-terminal-server: $m"
	if [ "$n" -lt "$QUANTE" ]; then
		ko "⛔ ne sono partiti $n su $QUANTE: la scena NON e' quella dichiarata"
		exit 3
	fi
	if [ "$n" -gt 0 ] && [ "$m" -gt 0 ]; then
		ok "la scena e' accesa, e si muove"
	else
		ko "⛔ la scena NON si e' accesa: quel che segue misurerebbe un fermo"
		exit 3
	fi
	exit 0 ;;

scena-via)
	# ⛔ E si CONTA quel che resta: «ho lanciato pkill» non e' «la scena e'
	#    spenta», e una scena sopravvissuta al giro «a riposo» renderebbe le
	#    due meta' meno diverse di quanto dicono.
	come_utente pkill -f "$SCENA_MARCA" 2>/dev/null
	sleep 1
	pkill -9 -u "$UID_B" -f "$SCENA_MARCA" 2>/dev/null
	sleep 0.5
	n=$(pgrep -u "$UID_B" -f 'while true; do date' 2>/dev/null | wc -l)
	if [ "$n" -eq 0 ]; then ok "scena di $UTENTE spenta (0 cicli rimasti)"
	else ko "⛔ restano $n cicli della scena di $UTENTE"; exit 3; fi
	exit 0 ;;

monitor)
	# ⚠ E' un CONTROLLO, non la misura.  ⛔ Il conto e' DIVISO PER DUE:
	#    `GetCurrentState` elenca ogni schermo due volte (trovato da A1).
	n=$(come_utente busctl --user call org.gnome.Mutter.DisplayConfig \
		/org/gnome/Mutter/DisplayConfig org.gnome.Mutter.DisplayConfig \
		GetCurrentState 2>/dev/null | tr ' ' '\n' | grep -c '"Meta-')
	printf 'MONITOR %s\n' "$((n / 2))"
	exit 0 ;;

accendi)
	log "Il server di $UTENTE, sulla $PORTA — DA ROOT"
	[ -x "$D/remotix" ] || { ko "⛔ $D/remotix non c'e'"; exit 2; }
	[ -f "$D/pagina.html" ] || { ko "⛔ $D/pagina.html non c'e'"; exit 2; }
	n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
	[ "$n" -eq 0 ] || { ko "⛔ la $PORTA e' gia' occupata"; exit 2; }
	[ -f /etc/pam.d/remotix ] || { ko "⛔ /etc/pam.d/remotix non c'e'"; exit 2; }
	mkdir -p "$CERT" "$RILIEVO"; chmod 1777 "$RILIEVO"
	: > "$LOG"
	# ⛔ E LA MARCA VA AZZERATA CON LUI, o ogni `tail -c` dopo un riavvio non
	#    prende NIENTE e i conti restituiscono zero su un giro vero.
	echo 0 > "$MARCA"
	export LD_LIBRARY_PATH="$LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
	if ldd "$D/remotix" | grep -q 'not found'; then
		ko "⛔ manca una libreria:"; ldd "$D/remotix" | grep 'not found' | sed 's/^/        /'
		exit 2
	fi
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
	exit 0 ;;

parlantina-c-e)
	# ⛔⛔ SI VERIFICA CHE IL FIGLIO PARLI: una diagnostica che tace mente.
	if [ ! -r "$LOG" ]; then
		ko "⛔ il registro «$LOG» non si legge: non e' uno ZERO, e' un GUASTO"
		exit 3
	fi
	m=$(grep -acE 'senza palco e QUALCUNO GUARDA|ridimensionamento a .* e. la misura che il flusso HA|input [0-9]+ \(azione' "$LOG")
	u=$?
	case $u in 0|1) : ;; *) ko "⛔ grep e' uscito con $u: il conto NON e' una misura"; exit 3 ;; esac
	[ -n "$m" ] || m=0
	printf 'PARLANTINA_RIGHE %s\n' "$m"
	if [ "$m" -gt 0 ]; then ok "⭐ $m righe di registro_dettaglio(): il figlio PARLA"
	else ko "⛔ ZERO righe di dettaglio: o il ramo non scatta, o il figlio TACE"; exit 4; fi
	exit 0 ;;

registro-da)
	stat -c %s "$LOG" 2>/dev/null > "$MARCA" || echo 0 > "$MARCA"
	printf 'MARCA %s\n' "$(cat "$MARCA")"
	exit 0 ;;

registro-tela)
	M=$(cat "$MARCA" 2>/dev/null); [ -n "$M" ] || M=0
	B=$(stat -c %s "$LOG" 2>/dev/null); [ -n "$B" ] || B=0
	if [ "$M" -gt "$B" ]; then
		ko "⛔ MARCA SCADUTA: marca $M byte, registro $B byte — ZERO PER COSTRUZIONE"
		exit 3
	fi
	tail -c "+$((M + 1))" "$LOG" 2>/dev/null | grep -aE \
		'TELA|tela|palco|MISURA DIVERGENTE|fotogramma SCARTATO|geometria|ridimensionament|CONCESSO DIVERSO|disaccordo|NON lo spedisco'
	exit 0 ;;

carico)
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
	printf 'GPU_RENDERD128_APERTI %s\n' \
		"$(ls -l /proc/*/fd 2>/dev/null | grep -c 'renderD128')"
	exit 0 ;;

cpu)
	# ⭐⭐ LA PROVA CHE QUESTA SESSIONE LAVORA, e non solo esiste.
	#     ⛔ E' la trappola 7 in testa: una sessione headless senza nessuno
	#     attaccato non compone niente.  Un `pgrep` la conterebbe lo stesso, e
	#     la «contesa fra cinque compositori» sarebbe cinque processi fermi.
	#     ⇒ Qui si stampano i tick di CPU, e chi legge fa la differenza fra
	#       due letture.  Un numero, non una presenza.
	s=$(pgrep -u "$UID_B" -x gnome-shell | head -1)
	f=$(mio_figlio || true)
	t=$(pgrep -u "$UID_B" -f 'gnome-terminal-server' | head -1)
	printf 'UTENTE %s\n' "$UTENTE"
	printf 'ORA_NS %s\n' "$(date +%s%N)"
	printf 'HZ %s\n' "$(getconf CLK_TCK)"
	printf 'SHELL_PID %s\n' "${s:-0}"
	printf 'SHELL_TICK %s\n' "$([ -n "$s" ] && tick "$s" || echo 0)"
	printf 'FIGLIO_PID %s\n' "${f:-0}"
	printf 'FIGLIO_TICK %s\n' "$([ -n "$f" ] && tick "$f" || echo 0)"
	printf 'TERMINALE_PID %s\n' "${t:-0}"
	printf 'TERMINALE_TICK %s\n' "$([ -n "$t" ] && tick "$t" || echo 0)"
	exit 0 ;;

sonda)
	# ⭐ La sonda del compositore, DENTRO la sessione di questo utente.
	#    ⛔ Fuori dalla sessione non avrebbe il bus e misurerebbe il nulla —
	#    e un «nulla» misurato sembra un numero.  ⚠ Passa da `come_utente`
	#    perche' l'ambiente si compone da zero (`CODER.md` §4.5).
	shift
	come_utente python3 \
		"$(dirname "$0")/06-b42-sonda-compositore.py" "$@"
	exit $? ;;

figlio)
	if f=$(mio_figlio); then printf 'FIGLIO %s\n' "$f"
	else printf 'FIGLIO nessuno\n'; fi
	printf 'REGISTRO_BYTE %s\n' "$(stat -c %s "$LOG" 2>/dev/null || echo 0)"
	exit 0 ;;

spegni)
	log "Spengo la $PORTA ($UTENTE)"
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
	exit 0 ;;

pulisci)
	log "Tolgo l'utente $UTENTE"
	bash "$0" spegni
	come_utente gdbus call --session -d org.gnome.SessionManager \
		-o /org/gnome/SessionManager -m org.gnome.SessionManager.Logout 2 \
		>/dev/null 2>&1
	sleep 3
	loginctl disable-linger "$UTENTE" 2>/dev/null
	pkill -u "$UID_B" 2>/dev/null; sleep 2; pkill -9 -u "$UID_B" 2>/dev/null
	userdel -r "$UTENTE" 2>&1 | sed 's/^/        /'
	# ⛔ E si VERIFICA che se ne sia andato: «ho lanciato userdel» non e'
	#    «l'utente non c'e' piu'».
	if id "$UTENTE" >/dev/null 2>&1; then
		ko "⛔ «$UTENTE» C'E' ANCORA dopo userdel"
		exit 3
	fi
	ok "«$UTENTE» non c'e' piu'"
	exit 0 ;;

stato|*)
	log "Stato di $UTENTE / $PORTA"
	inf "$(vicini)"
	inf "utente: $(id "$UTENTE" 2>&1)"
	for p in $(pgrep -u "$UID_B" -x gnome-shell 2>/dev/null); do
		inf "gnome-shell $p"
	done
	if pid=$(mio_pid); then inf "server $PORTA: pid $pid"; else inf "server $PORTA: spento"; fi
	if f=$(mio_figlio); then inf "figlio: $f"; else inf "figlio: nessuno"; fi
	inf "registro: $(stat -c %s "$LOG" 2>/dev/null || echo 0) byte"
	inf "carico: $(uptime | sed 's/.*load average: //')"
	exit 0 ;;
esac
