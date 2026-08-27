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


# ⛔ Le porte degli altri.  ⚠ 7700 e 7730 sono entrate il 22 agosto 2026: erano
#    vive sulla macchina e questa riga non le contava — un elenco fermo al 14
#    agosto e' un elenco che non protegge piu' niente.
ALTRUI="7448 7501 7561 7571 7700 7730 7781"

vicini() {
	local r=""
	for p in $ALTRUI; do
		r="$r$p: $(ss -tuln 2>/dev/null | grep -c ":$p\b") · "
	done
	printf '%sascoltatori (NON miei)\n' "$r"
}

# ⛔⭐ E QUI SI CONFRONTA, invece di stampare e basta — `LEZIONI.md` §1.20.
#     `vicini()` scriveva i conti prima e dopo ogni azione e **nessuna riga li
#     guardava**: accendere il proprio server sulla porta di un altro sarebbe
#     passato con un `NO` gia' stampato sopra.
non_e_di_altri() {
	local p
	for p in $ALTRUI; do
		[ "$PORTA" = "$p" ] && {
			ko "⛔ la $PORTA e' di un ALTRO anello ($ALTRUI): non l'accendo"
			exit 2; }
	done
	return 0
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

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔⭐ LA CARTELLA DEI DROP-IN NON E' MIA DA SOLO — cura del 22 agosto 2026
#
# ⛔ IL DIFETTO, con la sua data.  `[M]` 22 agosto 2026, primo giro di questo
#    banco con l'utente `provai6`: `sessione con` ha scritto il suo
#    `zz-remotix-monitor.conf` con `--virtual-monitor`, ha riletto l'ExecStart
#    in vigore e ci ha trovato **`--headless --no-x11` e basta**.
#    In quella cartella c'era gia'
#
#        /run/user/1006/systemd/user.control/…/zz-senza-monitor.conf
#
#    lasciato li' da un ALTRO banco — `04-b31`, `04-b32`, `06-b33`, `06-b34` e
#    `06-b35-terreno.sh` scrivono tutti quel nome.  ⛔ E **`zz-s` viene dopo
#    `zz-r`**: vinceva lui.
#
# ⭐ IL BANCO NON HA MENTITO — e va detto, perche' e' la meta' buona: il
#    controllo «scritto non e' in vigore» (forma E1) ha rifiutato di misurare
#    ed e' uscito **3**.  ⚠ Senza quel controllo avrei misurato una sessione
#    SENZA monitor virtuale credendola CON, e il giro «rosso-prima» sarebbe
#    uscito verde — cioe' il banco avrebbe assolto il difetto che esiste per
#    trovare.
#
# ⛔⛔ E LA STESSA TRAPPOLA STA SUL PRODOTTO: `src/sessione.c:735` scrive
#     **`zz-remotix-monitor.conf`**, lo stesso nome che perde contro
#     `zz-senza-monitor.conf`.  ⇒ Su un utente dove un altro banco e' passato,
#     il drop-in del prodotto non entra in vigore e nessuno se ne accorge.
#     ⚠ Non e' un difetto di prodotto — nessun utente vero ha quel file — ma e'
#       una miccia posata fra banchi di anelli diversi, e va dichiarata.
#
# ⇒ La cartella si SPAZZA prima di scriverci, e si dice che cosa si e' tolto.
#   ⛔ Non «si spera che sia vuota»: `/run/user/$UID_B` sopravvive al riavvio
#     della sessione (c'e' il linger), quindi quel che c'e' e' di ieri.
# ═══════════════════════════════════════════════════════════════════════════
spazza_dropin() {
	local dir="$1" tieni="${2:-}" f n=0
	[ -d "$dir" ] || return 0
	for f in "$dir"/*.conf; do
		[ -e "$f" ] || continue
		[ "$(basename "$f")" = "$tieni" ] && continue
		inf "⚠ tolgo un drop-in che NON e' di questo banco: $(basename "$f")"
		sed 's/^/            /' "$f"
		rm -f "$f"
		n=$((n+1))
	done
	[ "$n" -gt 0 ] && inf "spazzati $n drop-in estranei da $dir"
	return 0
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
	# ⛔⛔ QUI NON C'ERA NIENTE, e l'inquilino nasceva CIECO — fase 10 §7.4.
	gruppi_scheda_dai_a "$UTENTE" || exit 3
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
	# ⛔ Prima di scrivere: vedi il riquadro «la cartella dei drop-in non e' mia
	#    da solo».  Il mio si riscrive comunque, quindi non si tiene niente.
	spazza_dropin "$DIR"
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

congeda)
	# ⛔⭐ IL PASSO CHE MANCAVA FRA «rosso-prima» E «nasci» — 22 agosto 2026.
	#
	#     `sessione.h:240`: `sessione_assicura()` **«si avvia solo da
	#     SESSIONE_MORTA»**.  ⇒ Chiamandolo su una sessione gia' viva — quella
	#     del giro rosso, con `--virtual-monitor` addosso — il prodotto fa la
	#     cosa giusta e **non la tocca**: `[M]` 22 agosto, `assicura: 3 MONITOR
	#     SCELTO DA SE (l'ho fatta nascere io: no)`.
	#
	# ⛔ Il banco leggeva quel 3 come un guasto e usciva 3, ⚠ mentre il difetto
	#    era suo: il giro certificante scritto in testa a `04-b20-lancia.sh`
	#    passava da `sessione con` a `nasci` **senza congedare in mezzo**, e
	#    quindi non poteva mai arrivare al giro verde.  E' la forma «un
	#    attrezzo che muore su dati veri accusa i dati».
	#
	# ⛔ E QUI NON SI SCRIVE NESSUN DROP-IN: la cartella si lascia VUOTA, cosi'
	#    quel che entrera' in vigore dopo lo avra' scritto **il prodotto** e la
	#    differenza fra i due giri resta una riga di prodotto (`CODER.md` §3.6).
	log "Congedo la sessione di $UTENTE e lascio la cartella dei drop-in VUOTA"
	inf "$(vicini)"
	spazza_dropin "/run/user/$UID_B/systemd/user.control/$UNITA.d"
	come_utente systemctl --user daemon-reload >/dev/null 2>&1
	if pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1; then
		come_utente gdbus call --session -d org.gnome.SessionManager \
			-o /org/gnome/SessionManager \
			-m org.gnome.SessionManager.Logout 2 >/dev/null 2>&1
		g=0
		while [ $g -lt 60 ] && pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1; do
			sleep 0.5; g=$((g+1))
		done
		come_utente systemctl --user reset-failed >/dev/null 2>&1
	fi
	# ⛔ E si VERIFICA che se ne sia andata, invece di sperarlo: se restasse,
	#    `nasci` direbbe di nuovo 3 e la colpa sembrerebbe del prodotto.
	if pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1; then
		ko "⛔ la sessione NON se n'e' andata: non chiamo `nasci`"
		for p in $(pgrep -u "$UID_B" -x gnome-shell); do
			inf "resta gnome-shell $p: $(tr '\0' ' ' < /proc/$p/cmdline)"
		done
		exit 3
	fi
	ok "nessun gnome-shell di $UTENTE, e nessun drop-in in $UNITA.d"
	ls -la "/run/user/$UID_B/systemd/user.control/$UNITA.d" 2>&1 | sed 's/^/        /'
	exit 0 ;;

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
	# ⛔ E si spazza TUTTA la cartella, non solo il file del banco: il drop-in
	#    che il prodotto sta per scrivere si chiama `zz-remotix-monitor.conf` e
	#    PERDE contro un `zz-senza-monitor.conf` di un altro banco (riquadro
	#    «la cartella dei drop-in non e' mia da solo»).  ⚠ Lasciandolo, il
	#    prodotto scriverebbe e non entrerebbe in vigore — e il banco
	#    misurerebbe la cura di qualcun altro credendola la sua.
	spazza_dropin "/run/user/$UID_B/systemd/user.control/$UNITA.d"
	rm -f "/run/user/$UID_B/systemd/user.control/$UNITA.d/zz-remotix-monitor.conf"
	come_utente systemctl --user daemon-reload >/dev/null 2>&1
	inf "ExecStart senza il mio drop-in: $(come_utente systemctl --user show -p ExecStart --value "$UNITA")"
	come_utente env LD_LIBRARY_PATH="$LIBS" "$P" assicura "$MISURA"
	n=$?
	# ⛔⭐ L'ATTESO SCRITTO PRIMA, E CONFRONTATO — `LEZIONI.md` §1.20.
	#     Questo numero veniva STAMPATO e passato all'uscita, e nessuna riga
	#     diceva quale fosse quello giusto: chi legge «ha detto 1» non ha modo
	#     di sapere che dopo la cura **1 NERA e' il caso sano** (lo dice
	#     `04-b20-nasci.c`, e chi legge il registro non ha quel file davanti).
	# ⚠ L'uscita resta `SessioneStato` grezzo: nessuno deve tradurre.  Qui si
	#   aggiunge la FRASE, non una traduzione del numero.
	ATTESO_NASCI=${ATTESO_NASCI:-1}
	if [ "$n" = "$ATTESO_NASCI" ]; then
		ok "sessione_assicura ha detto $n, ed e' l'atteso ($ATTESO_NASCI): dopo"\
" la cura la sessione remota sana e' NERA — zero monitor propri, e il monitor"\
" lo monta la cattura al primo client"
	else
		ko "⛔ sessione_assicura ha detto $n, atteso $ATTESO_NASCI"
		[ "$n" = 3 ] && inf "⚠ 3 SCELTO DA SE quasi sempre vuol dire che c'era"\
" gia' una sessione viva: `sessione_assicura()` si avvia solo da SESSIONE_MORTA"\
" (src/sessione.h:240).  ⇒ e' il BANCO che ha saltato «congeda»."
	fi
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
	non_e_di_altri
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
