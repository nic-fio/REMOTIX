#!/bin/bash
#
# 02-sessione-lancia.sh — il banco della sotto-fase F2.1: la sessione GNOME
# headless nasce, e nasce CON un monitor virtuale della misura chiesta.
#
#   bash 02-sessione-lancia.sh guarda        guarda e basta: non tocca niente
#   bash 02-sessione-lancia.sh sano          la avvia CON --virtual-monitor
#   bash 02-sessione-lancia.sh guasto        la avvia SENZA — la prova M9
#   bash 02-sessione-lancia.sh dispositivi   quando nasce il puntatore virtuale
#   bash 02-sessione-lancia.sh ferma         Logout(2)
#   bash 02-sessione-lancia.sh certifica     sano → guasto → risanato
#   bash 02-sessione-lancia.sh come-al-riavvio  la fa rinascere SENZA nessun
#                                            drop-in di questo banco: com'e'
#                                            dopo un riavvio del server
#   bash 02-sessione-lancia.sh guardia [...] la guardia da mettere davanti a una
#                                            misura altrui (→ 02-sessione-guardia.sh)
#
# ⛔ GIRA SULL'HOST DI NIC-OS, non dentro il contenitore: la sessione grafica
#    vive li', con logind, systemd --user e /dev/dri veri.
#
# ===========================================================================
# ⛔ PERCHE' ESISTE, E NON E' «PER AVVIARE UNA SESSIONE»
# ===========================================================================
#
# Avviare una sessione lo sa fare gia' `banchi/00-sessione-gnome.sh`, della
# fase 0.  Quello che quel banco NON fa, e che e' tutto il motivo di questo
# file, e' chiedere il MONITOR:
#
#   ⛔ `00-sessione-gnome.sh` non nomina mai `--virtual-monitor`, e nemmeno
#      `--headless`: si affida al drop-in che `v1/banco/provision-server.sh`
#      (righe 224-231) scrive in /etc/systemd/user, che mette `--headless
#      --no-x11` e **basta**.  ⇒ Ogni sessione avviata cosi' e' NERA.
#
#   ⭐ E non e' una deduzione.  `[M]` 12 agosto 2026, aprendo questo giro: la
#      sessione GNOME viva su NIC-OS da due giorni — gnome-shell 214465,
#      IsSessionRunning true, cinquanta nomi sul bus, Nautilus e il Terminale
#      accesi — rispondeva a GetCurrentState con **zero monitor e zero monitor
#      logici**.  Il guasto di `STUDI.md` §gnome §13 M9 non era da innestare: era
#      addosso alla macchina, e nessuno se n'era accorto.
#
# ⇒ Un banco della fase 2 che misurasse la cattura su quella sessione leggerebbe
#   zero fotogrammi e manderebbe a cercare il difetto dentro PipeWire.  Questo
#   script esiste per rendere quel guasto IMPOSSIBILE DA CONFONDERE: lo sa
#   accendere, lo sa spegnere, e lo strumento gli da' un numero suo.
#
# ===========================================================================
# ⛔ E UNA SECONDA COSA CHE LA SESSIONE NERA FA, E CHE NESSUN DOCUMENTO DICEVA
# ===========================================================================
#
# `[M]` 12 agosto 2026, e l'ho pagata io: su una sessione headless con ZERO
# monitor, `org.gnome.Shell.Screenshot.Screenshot` fa cadere gnome-shell.
#
#     CRITICAL: cogl_texture_2d_new_with_size: assertion 'width >= 1' failed
#     WARNING : Failed to take screenshot: Failed to create 0x0 texture
#
# e siccome l'unita' porta `OnFailure=gnome-session-shutdown.target` con
# `Restart=no`, se ne va **tutta la sessione**.  ⇒ La sessione nera non e' solo
# «viva e nera»: e' **fragile**, e cade al primo che le chiede un fotogramma per
# la via della Shell.  Chi vedesse cadere la sessione a meta' di una misura
# cerchera' il difetto nel proprio codice.
#
# ===========================================================================
# ⛔ IL DROP-IN: DOVE SI SCRIVE, E PERCHE' NON DOVE SEMBRA
# ===========================================================================
#
# `gnome-session` NON lancia gnome-shell: fa partire l'unita' d'utente
# `org.gnome.Shell@wayland.service`, il cui `ExecStart` e' fisso.  Per cambiare
# la riga di comando serve un drop-in — ed e' quel che `src/sessione.c:671` fa
# **solo per KWin** (letto il 12 ago 2026: la riga e' proprio
# `if (tipo == COMPOSITORE_KWIN && !scrivi_dropin(...))`, e sul ramo GNOME
# `larghezza` e `altezza` non le legge nessuno).
#
# ⭐ Qui si scrive in `$XDG_RUNTIME_DIR/systemd/user.control/`, come fa v1 per
#    KWin, per tre ragioni:
#      1. non serve root — l'unita' e' d'UTENTE;
#      2. sparisce da se' al riavvio: un banco non deve lasciare configurazione
#         addosso alla macchina;
#      3. il nome comincia per `zz-` **apposta**: i drop-in di tutte le
#         cartelle si applicano in ordine di NOME FILE, e in
#         /etc/systemd/user ce n'e' gia' uno che si chiama
#         `remotix-headless.conf`.  `zz-…` viene dopo, quindi vince.
#
# ⛔ E scritto non e' in vigore (E1).  Dopo ogni avvio si rilegge la riga di
#    comando del PROCESSO, e se non combacia con quel che si e' chiesto, il
#    verdetto e' DISACCORDO (uscita 6), non «va bene lo stesso».
#
# ===========================================================================
# ⛔ QUEL CHE QUESTO BANCO NON TOCCA, E COME SE NE ACCERTA
# ===========================================================================
#
# Su NIC-OS girano due server voluti, sulla **7448** e sulla **7501**, e non
# sono di questo giro.  Vivono dentro il contenitore e non dipendono dalla
# sessione grafica — ma «non dipendono» era un'ipotesi finche' non l'ho
# guardata, quindi questo script CONTA i loro ascoltatori prima e dopo ogni
# ciclo, e se il numero cala si ferma e lo dice.
#
# ⭐ E la porta di questo banco, la **7511**, non serve a parlare con nessuno:
#    e' il LUCCHETTO.  Una sessione grafica e' una per utente (invariante I2):
#    due copie di questo banco che la ciclano insieme si darebbero due misure
#    diverse sotto la stessa etichetta.  Chi non riesce a prendere la 7511 non
#    parte.
#
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
STRUMENTO=${STRUMENTO:-$QUI/02-sessione-stato.py}
ESITI=${ESITI:-$QUI/02-sessione-esiti.jsonl}
SCENE=${SCENE:-$QUI/02-sessione-scene}

MISURA=${MISURA:-1920x1080}
PORTA_LUCCHETTO=${PORTA_LUCCHETTO:-7511}
PORTE_DA_NON_TOCCARE=${PORTE_DA_NON_TOCCARE:-"7448 7501"}

U=$(id -u)
RUNTIME=${XDG_RUNTIME_DIR:-/run/user/$U}
REGISTRO=$RUNTIME/remotix-sessione.log
REGISTRO_SHELL=$RUNTIME/mutter.log
DROPIN_DIR=$RUNTIME/systemd/user.control/org.gnome.Shell@wayland.service.d
DROPIN=$DROPIN_DIR/zz-f21-monitor.conf
# ⛔ Il drop-in PERSISTENTE, quello che scrive `v1/banco/provision-server.sh`.
#    Il nostro sta in $XDG_RUNTIME_DIR e sparisce da se' al riavvio — che e'
#    giusto per un banco, ed e' esattamente il motivo per cui va guardato anche
#    quest'altro: se il monitor lo tiene in piedi SOLO il nostro, la macchina
#    torna nera al primo riavvio e il difetto ricomincia da capo.
DROPIN_PERSISTENTE=${DROPIN_PERSISTENTE:-/etc/systemd/user/org.gnome.Shell@wayland.service.d/remotix-headless.conf}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
att() { printf '    \033[1;33m⚠\033[0m   %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ---------------------------------------------------------------------------
# ⛔ IL LUCCHETTO SULLA 7511 — non un ascoltatore, un DIRITTO A CICLARE.
# Si tiene con un processo `nc`/python che occupa la porta finche' vive.
# ---------------------------------------------------------------------------
PID_LUCCHETTO=""
prendi_lucchetto()
{
	python3 -c "
import socket, sys, time
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
try:
    s.bind(('127.0.0.1', $PORTA_LUCCHETTO))
except OSError as e:
    print('occupata: %s' % e); sys.exit(1)
s.listen(1)
print('preso')
sys.stdout.flush()
time.sleep(86400)
" &
	PID_LUCCHETTO=$!
	sleep 1
	if ! kill -0 "$PID_LUCCHETTO" 2>/dev/null; then
		ko "⛔ la porta $PORTA_LUCCHETTO e' gia' occupata: un'altra copia di questo"
		ko "   banco sta ciclando la sessione.  Non parto: due cicli insieme"
		ko "   darebbero due misure diverse sotto la stessa etichetta."
		return 1
	fi
	ok "lucchetto preso sulla $PORTA_LUCCHETTO (pid $PID_LUCCHETTO)"
	return 0
}
molla_lucchetto()
{
	[ -n "$PID_LUCCHETTO" ] && kill "$PID_LUCCHETTO" 2>/dev/null
	PID_LUCCHETTO=""
}
trap molla_lucchetto EXIT

# ---------------------------------------------------------------------------
conta_ascoltatori() # $1 = porta
{
	ss -tuln | grep -c ":$1\b"
}

vicini_prima()
{
	VICINI=""
	for p in $PORTE_DA_NON_TOCCARE; do
		VICINI="$VICINI $p:$(conta_ascoltatori "$p")"
	done
	inf "i vicini che non tocco, prima:$VICINI"
}

vicini_dopo()
{
	local guai=0 p n atteso
	for p in $PORTE_DA_NON_TOCCARE; do
		atteso=$(echo "$VICINI" | tr ' ' '\n' | grep "^$p:" | cut -d: -f2)
		n=$(conta_ascoltatori "$p")
		if [ "$n" -lt "${atteso:-0}" ]; then
			ko "⛔ sulla $p gli ascoltatori sono passati da $atteso a $n:"
			ko "   ho toccato qualcosa che non era mio.  FERMO TUTTO."
			guai=1
		fi
	done
	[ "$guai" -eq 0 ] && ok "i due server voluti sono ancora tutti e due in piedi"
	return $guai
}

# ---------------------------------------------------------------------------
# L'ambiente, composto da zero — la ricetta di `sessione.c:componi_ambiente`.
#
# ⛔ SHELL VUOTA: `gnome-session.in:3-14` si ri-esegue dentro una shell di LOGIN
#    se `$SHELL` e' non vuota e sta in /etc/shells, e si riporta dentro
#    `~/.profile`.  Il controllo vero e' `[ -n "$SHELL" ]`, quindi vuota e
#    assente vanno tutt'e due bene — e v1 la lascia ASSENTE, perche' compone
#    l'ambiente da zero e SHELL non la mette (zero occorrenze in `sessione.c`).
#    Qui la si mette VUOTA, che e' la stessa cosa e si vede nel `/proc/…/environ`.
#
# ⛔ XDG_SESSION_TYPE=wayland SERVE: l'unita' della Shell porta
#    `ConditionEnvironment=XDG_SESSION_TYPE=wayland` (verificato nel file
#    installato su NIC-OS il 12 ago 2026), e senza il compositore non parte
#    affatto — sessione monca, e nessuna riga che dica perche'.
# ---------------------------------------------------------------------------
avvia_sessione()
{
	env -i \
		HOME="$HOME" \
		USER="$(id -un)" \
		PATH=/usr/local/bin:/usr/bin:/bin \
		SHELL= \
		LANG=C.UTF-8 \
		XDG_RUNTIME_DIR="$RUNTIME" \
		DBUS_SESSION_BUS_ADDRESS="unix:path=$RUNTIME/bus" \
		XDG_CURRENT_DESKTOP=GNOME \
		XDG_SESSION_DESKTOP=gnome \
		XDG_SESSION_TYPE=wayland \
		setsid --fork sh -c "exec >>'$REGISTRO' 2>&1; exec gnome-session --session=gnome"
}

viva() { pgrep -u "$U" -x gnome-shell >/dev/null; }

# ⛔ Il congedo e' `Logout(2)`, non `systemctl --user stop`: `gnome-session` non
#    esce dopo aver avviato il target, apre un fifo e dorme (`STUDI.md` §gnome §3.2),
#    e `Logout(1)` mostra il dialogo se esiste un inibitore — in una sessione
#    non presidiata non gli risponde nessuno.
# ⛔ E si aspetta `inactive`, NON «diverso da active»: `is-active` passa per
#    `deactivating`, e ripartire li' dentro e' un'altra prima esecuzione
#    (`fasi/00-ambiente.md`, difetto 4 della fase 0).
ferma_e_aspetta()
{
	local scadenza=$((SECONDS + ${1:-60})) stato
	gdbus call --session -d org.gnome.SessionManager -o /org/gnome/SessionManager \
	    -m org.gnome.SessionManager.Logout 2 >/dev/null
	while [ $SECONDS -lt $scadenza ]; do
		stato=$(systemctl --user is-active gnome-session-manager@gnome.service)
		case "$stato" in
		inactive|failed|unknown)
			if ! viva; then
				systemctl --user reset-failed
				return 0
			fi
			;;
		esac
		sleep 0.5
	done
	return 1
}

attendi() # aspetta un EVENTO, con un tetto dichiarato
{
	local scadenza=$((SECONDS + ${1:-60}))
	while [ $SECONDS -lt $scadenza ]; do
		if viva && gdbus call --session -d org.gnome.SessionManager \
		    -o /org/gnome/SessionManager \
		    -m org.gnome.SessionManager.IsSessionRunning 2>&1 | grep -q true
		then
			return 0
		fi
		sleep 0.5
	done
	return 1
}

# ---------------------------------------------------------------------------
# ⛔ TRE modi, e il terzo e' nato il 12 agosto per una ragione che vale piu'
#    degli altri due:
#
#   con    il drop-in di questo banco CHIEDE il monitor        → la scena sana
#   senza  il drop-in di questo banco NON lo chiede            → il guasto M9
#   nudo   ⭐ NESSUN drop-in di questo banco: la sessione nasce con la sola
#          configurazione PERSISTENTE della macchina, cioe' **com'e' dopo un
#          riavvio**.  E' l'unico modo di misurare l'esito di un riavvio senza
#          riavviare il server — che non si puo' fare, perche' dentro il
#          contenitore girano due server voluti (7448, 7501) e il rootfs vive
#          in RAM.
#
#   ⛔ E «nudo» NON E' UN RIAVVIO, e va detto ogni volta: non prova che /media
#      si rimonti, che il rootfs torni, che qualcuno rilanci
#      `provision-server.sh`.  Prova l'ULTIMO anello — data la configurazione
#      persistente, una sessione appena nata ha il monitor? — che e'
#      precisamente l'anello che il 10 agosto ha ceduto.  Gli altri anelli
#      restano `[?]` finche' un riavvio vero non li tocca.
scrivi_dropin() # $1 = "con" | "senza" | "nudo"
{
	case "$1" in
	con)
		mkdir -p "$DROPIN_DIR"
		cat >"$DROPIN" <<CONF
[Service]
ExecStart=
ExecStart=/usr/bin/gnome-shell --headless --no-x11 --virtual-monitor $MISURA
CONF
		;;
	senza)
		mkdir -p "$DROPIN_DIR"
		cat >"$DROPIN" <<CONF
[Service]
ExecStart=
ExecStart=/usr/bin/gnome-shell --headless --no-x11
CONF
		;;
	nudo)
		rm -f "$DROPIN"
		rmdir "$DROPIN_DIR" 2>&1 | grep -v "Directory not empty" || true
		;;
	*) ko "⛔ modo di drop-in ignoto: $1"; return 1 ;;
	esac
	systemctl --user daemon-reload || return 1
	# ⛔ E si VERIFICA che il drop-in sia in vigore, non che sia scritto.
	local vigore
	vigore=$(systemctl --user show -p ExecStart --value org.gnome.Shell@wayland.service)
	inf "ExecStart in vigore: $vigore"
	case "$1:$vigore" in
	con:*--virtual-monitor\ $MISURA*) ok "il drop-in CON monitor e' in vigore" ;;
	senza:*--virtual-monitor*)
		ko "⛔ ho chiesto SENZA e systemd dice ancora --virtual-monitor:"
		ko "   un altro drop-in vince sul mio.  Non misuro."
		return 1 ;;
	senza:*) ok "il drop-in SENZA monitor e' in vigore" ;;
	nudo:*--virtual-monitor*)
		ok "senza nessun drop-in mio il monitor lo chiede la configurazione"
		ok "PERSISTENTE della macchina: e' quel che si trovera' al riavvio" ;;
	nudo:*)
		att "⚠ senza i drop-in di questo banco nessuno chiede il monitor:"
		att "  e' esattamente quel che la macchina fa dopo un riavvio" ;;
	*)
		ko "⛔ ho chiesto CON $MISURA e systemd non lo dice: il mio drop-in"
		ko "   non vince.  Non misuro — un banco che non impone la scena"
		ko "   misura la scena di qualcun altro."
		return 1 ;;
	esac
	return 0
}

# ---------------------------------------------------------------------------
# ⛔ «SANA ADESSO» NON E' «SANA DOPO IL RIAVVIO» — e la differenza si dice ogni
#    volta, non si scopre.
#
# Il drop-in di questo banco vive in `$XDG_RUNTIME_DIR`, che il riavvio si porta
# via insieme a tutto il rootfs (che su NIC-OS sta in RAM).  Se la sessione ha
# il monitor solo grazie a lui, la macchina e' sana **per questa accensione** —
# ed e' la stessa mezza verita' di `LEZIONI.md` §2.5-bis: un ripristino si prova
# riavviando, non rileggendo lo script.
#
# ⇒ Chi rende il monitor persistente e' `provision-server.sh` §4, che dopo ogni
#   riavvio va rieseguito comunque.  Questa funzione guarda se quella riga c'e',
#   e se non c'e' lo dice FORTE invece di lasciar credere che sia finita.
# ---------------------------------------------------------------------------
dilo_se_non_persiste()
{
	if [ ! -r "$DROPIN_PERSISTENTE" ]; then
		att "⚠ il drop-in persistente non c'e' o non lo leggo:"
		att "  $DROPIN_PERSISTENTE"
		att "  ⇒ dopo un riavvio del server la sessione torna NERA."
		att "  Si rimette con: bash /media/REMOTIX/provision-server.sh monitor"
		return 1
	fi
	if grep -q -- '--virtual-monitor' "$DROPIN_PERSISTENTE"; then
		ok "e sopravvive al riavvio: --virtual-monitor sta anche nel drop-in"
		inf "persistente ($DROPIN_PERSISTENTE), che provision-server.sh riscrive"
		return 0
	fi
	att "⚠⚠ SANA ADESSO, NERA AL PROSSIMO RIAVVIO."
	att "  Il monitor lo tiene in piedi SOLO il drop-in di questo banco, che sta"
	att "  in \$XDG_RUNTIME_DIR e il riavvio se lo porta via; quello persistente"
	att "  ($DROPIN_PERSISTENTE)"
	att "  NON nomina --virtual-monitor — ed e' il difetto che ha tenuto questa"
	att "  macchina nera dal 10 al 12 agosto (I7: la protezione sta nel"
	att "  programma, non in una riga di configurazione che si puo' perdere)."
	att "  Si cura con: bash /media/REMOTIX/provision-server.sh monitor"
	return 1
}

togli_dropin()
{
	rm -f "$DROPIN"
	rmdir "$DROPIN_DIR" 2>&1 | grep -v "Directory not empty" || true
	systemctl --user daemon-reload
}

# ⛔ LA RIGA DI COMANDO E' PIATTA, E LE DUE RESE SONO SCRITTE PER ESTESO —
#    lacuna L3, 12 agosto 2026.
#
# C'era un vettore: `local extra=(); [ -n "${2:-}" ] && extra=(--registra "$2")`,
# e poi `"${extra[@]}"` in coda alla chiamata.  Due righe in meno, e ⛔ la
# chiamata **fuori da ogni controllo statico**: `01-b0-chiamate.py` vedeva una
# variabile sola dove argparse aspetta un'opzione, non poteva sapere se
# portasse dentro un `--qualcosa`, e la dichiarava IGNOTA — ne' rossa ne'
# verde.  E' la cucitura che ha gia' fatto uscire rosso un banco sano due
# volte: B6 il 10 agosto, B7 l'11 (`01-b0-chiamate.py`, in testa).
#
# ⚠ La ripetizione delle sei parole comuni e' il prezzo, e si paga: due righe
#   leggibili valgono piu' di una riga che nessuno strumento sa leggere.
misura() # $1 = etichetta della scena; $2 = file dove registrarla (facoltativo)
{
	if [ -n "${2:-}" ]; then
		python3 "$STRUMENTO" --attesa "$MISURA" --dal-bus \
		    --etichetta "$1" --esiti "$ESITI" --registra "$2"
		return $?
	fi
	python3 "$STRUMENTO" --attesa "$MISURA" --dal-bus \
	    --etichetta "$1" --esiti "$ESITI"
	return $?
}

# ---------------------------------------------------------------------------
riparti() # $1 = con|senza ; $2 = etichetta ; $3 = file scena (facoltativo)
{
	log "Rimetto la sessione da capo, drop-in «$1»"
	if viva; then
		ferma_e_aspetta 60 || { ko "⛔ non si e' fermata in 60 s"; return 9; }
		ok "sessione fermata"
	else
		inf "non c'era nessuna sessione da fermare"
	fi
	scrivi_dropin "$1" || return 9
	: >"$REGISTRO"
	avvia_sessione
	if ! attendi 60; then
		ko "⛔ la sessione NON e' partita entro 60 s.  Ultime righe:"
		tail -n 25 "$REGISTRO" | sed 's/^/        /'
		return 9
	fi
	ok "sessione partita: $(pgrep -a -u "$U" -x gnome-shell | head -1)"
	# ⚠ La Shell prende il nome sul bus PRIMA di `meta_context_start()`
	#   (`STUDI.md` §gnome §3.2): il nome non e' un indicatore di prontezza.  Si aspetta
	#   che GetCurrentState risponda, che e' il fatto che serve a noi.
	sleep 3
	misura "$2" "${3:-}"
	local e=$?
	# ⛔ E si dice SUBITO se questa salute e' solo di oggi: chi ha appena letto
	#    «SANA» e' esattamente chi deve sapere che al riavvio non lo sara' piu'.
	[ "$1" = con ] && dilo_se_non_persiste
	return $e
}

# ---------------------------------------------------------------------------
# ⛔ QUANDO NASCE IL PUNTATORE VIRTUALE — la domanda che PIANO.md porta qui.
#
# Il fatto misurato dalla sonda S7 il 10 agosto: in una sessione GNOME senza
# dispositivi di input fisici, un client partito PRIMA che il puntatore di
# `libei` esista non riceve niente — ne' rotella, ne' bottoni, ne' il movimento.
# Partito DOPO riceve tutto.  `[M]` sull'ORDINE; la CAUSA e' `[?]`.
#
# ⭐ E leggendo Mutter 48.7 la regola diventa piu' stretta di come il piano la
#    scrive: `ensure_virtual_device()` e' chiamata dai gestori di
#    `NotifyPointerMotion*` e `NotifyPointerButton(pressed)`, **non** da
#    `Start()` (`meta-remote-desktop-session.c:290-321, 780-800, 940-960` [R]).
#    ⇒ Il puntatore non nasce quando la sessione RemoteDesktop parte: nasce al
#      PRIMO MOVIMENTO INIETTATO.  Un banco che aprisse l'applicazione dopo
#      `Start()` ma prima del primo movimento misurerebbe la scena sbagliata
#      credendo di aver rispettato l'ordine.
#
# Qui si misura la CAUSA `[?]`: un client Wayland tenuto vivo attraverso la
# nascita del puntatore riceve un secondo `wl_seat.capabilities`, o no?
#   · se NON lo riceve → la spiegazione del piano regge, e diventa `[M]`;
#   · se lo riceve     → la spiegazione e' sbagliata e la causa e' altrove.
# Il caso opposto e' scritto prima, come vuole `LEZIONI.md` §1.11.
# ---------------------------------------------------------------------------
dispositivi()
{
	local traccia=$RUNTIME/f21-seat.log
	log "0. Lo stato di partenza"
	misura "dispositivi-partenza"; local e=$?
	if [ "$e" -ne 0 ]; then
		att "la sessione non e' sana (uscita $e): la misura dei dispositivi si"
		att "fa lo stesso, ma il numero va letto sapendolo."
	fi

	log "1. Un client Wayland vivo, tenuto acceso ATTRAVERSO la nascita del puntatore"
	# ⛔ E' il client «partito PRIMA» della sonda S7: deve restare vivo per
	#    tutta la misura, o non si sta misurando l'ordine — si sta misurando
	#    due client diversi.
	: >"$traccia"
	WAYLAND_DEBUG=1 WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR="$RUNTIME" \
	    timeout 90 foot -e sleep 85 >>"$traccia" 2>&1 &
	local pid_client=$!
	sleep 6
	if ! kill -0 "$pid_client" 2>/dev/null; then
		ko "⛔ il client non e' rimasto vivo: senza di lui non misuro niente"
		inf "ultime righe della traccia:"
		tail -n 15 "$traccia" | sed 's/^/        /'
		return 3
	fi
	ok "client vivo (pid $pid_client), traccia in $traccia"

	# ⛔ I tre passi D-Bus NON si fanno con tre `gdbus call`: la sessione di
	#    RemoteDesktop e' legata alla CONNESSIONE che l'ha creata, e `gdbus`
	#    ne apre una nuova ogni volta.  Misurato il 12 ago 2026: `Start`
	#    rispondeva «Object does not exist at path» e il puntatore non nasceva
	#    mai — con il passo 3 che dava NO su una scena mai avvenuta.  Il
	#    dettaglio sta in testa a `02-sessione-dispositivi.py`.
	python3 "$QUI/02-sessione-dispositivi.py" --traccia "$traccia" --esiti "$ESITI"
	local esito=$?

	kill "$pid_client" 2>/dev/null
	log "Le tracce restano in $traccia e $traccia.dopo"
	return $esito
}

# ---------------------------------------------------------------------------
# ⛔ LA CERTIFICAZIONE — sano N → guasto M → risanato N, con i numeri
#    SCRITTI PRIMA (mandato §3.3, e la regola nata l'11 agosto: chi scrive un
#    banco lo certifica nello stesso giro).
#
#   atteso sano     0  (SANA)
#   guasto innestato:  si toglie `--virtual-monitor` dal drop-in — cioe' M9 di
#                      `STUDI.md` §gnome §13, il guasto fatto di proposito
#   atteso guasto   1  (NERA: ZERO MONITOR)
#   atteso risanato 0
#
# ⛔ E il verdetto non e' «e' diventato rosso»: dev'essere diventato rosso NEL
#    SUO PUNTO — la marca «NERA: ZERO MONITOR» e non un'altra.  Un banco che
#    diventa rosso per un'altra ragione non e' certificato, e' fortunato.
# ---------------------------------------------------------------------------
certifica()
{
	local A_SANO=0 A_GUASTO=1 MARCA_GUASTO="NERA: ZERO MONITOR"
	log "Gli attesi, SCRITTI PRIMA del giro"
	inf "sano: $A_SANO (SANA) · guasto: $A_GUASTO ($MARCA_GUASTO) · risanato: $A_SANO"
	inf "misura chiesta: $MISURA"
	vicini_prima

	mkdir -p "$SCENE"

	log "1. Il giro SANO — la sessione CON il monitor"
	riparti con "certifica-sano" "$SCENE/sana.json"; local E_SANO=$?
	log "2. Il GUASTO — la stessa sessione SENZA --virtual-monitor (M9)"
	riparti senza "certifica-guasto" "$SCENE/nera.json"; local E_GUASTO=$?
	log "3. Il RISANATO — si rimette il monitor"
	riparti con "certifica-risanato" "$SCENE/sana-2.json"; local E_RIS=$?

	log "Il verdetto, coi tre numeri accanto"
	inf "sano $E_SANO · guasto $E_GUASTO · risanato $E_RIS"
	local falle=0
	[ "$E_SANO" -eq "$A_SANO" ] && ok "il sano e' l'atteso ($E_SANO)" || {
		ko "⛔ il sano e' $E_SANO invece di $A_SANO: il soggetto e' rotto, e un"
		ko "   banco il cui soggetto e' rotto NON si certifica"
		falle=$((falle+1)); }
	[ "$E_GUASTO" -eq "$A_GUASTO" ] && ok "il guasto e' l'atteso ($E_GUASTO = $MARCA_GUASTO)" || {
		ko "⛔ il guasto e' $E_GUASTO invece di $A_GUASTO: o il banco non lo vede,"
		ko "   o e' rosso per un'altra ragione"
		falle=$((falle+1)); }
	[ "$E_RIS" -eq "$A_SANO" ] && ok "il risanato torna al sano ($E_RIS)" || {
		ko "⛔ il risanato e' $E_RIS invece di $A_SANO: il guasto ha lasciato"
		ko "   qualcosa, o il sano non era ripetibile"
		falle=$((falle+1)); }

	vicini_dopo || falle=$((falle+1))

	if [ "$falle" -eq 0 ]; then
		printf '\n    \033[1;32m⭐ F2.1 E'"'"' CERTIFICATO: sano %s → guasto %s (nel suo punto) → risanato %s\033[0m\n' \
		    "$E_SANO" "$E_GUASTO" "$E_RIS"
		printf '    --  e non e'"'"' «il banco e'"'"' giusto»: e'"'"' «il banco sa vedere QUESTO difetto».\n'
		return 0
	fi
	printf '\n    \033[1;31m⛔ F2.1 NON E'"'"' CERTIFICATO: %s cose non tornano\033[0m\n' "$falle"
	return 1
}

# ---------------------------------------------------------------------------
case "${1:-guarda}" in
guarda)
	# ⛔ Sola lettura: non prende il lucchetto e non tocca niente.
	log "Guardo e basta — non tocco niente"
	vicini_prima
	misura "${2:-guarda}"
	e=$?
	dilo_se_non_persiste
	exit $e
	;;
guardia)
	# ⛔ La guardia da mettere DAVANTI a una misura altrui.  Sta in un file suo
	#    perche' chi la usa non e' questo banco: sono F2.2..F2.6, e devono
	#    poterla infilare davanti al proprio comando senza far partire niente.
	shift
	exec bash "$QUI/02-sessione-guardia.sh" "$@"
	;;
sano)      prendi_lucchetto || exit 2; vicini_prima; riparti con "sano" "${2:-}"; e=$?; vicini_dopo || e=9; exit $e ;;
guasto)    prendi_lucchetto || exit 2; vicini_prima; riparti senza "guasto" "${2:-}"; e=$?; vicini_dopo || e=9; exit $e ;;
come-al-riavvio)
	# ⭐ La prova della PERSISTENZA senza riavviare il server: si tolgono i
	#    drop-in di questo banco e si fa rinascere la sessione con la sola
	#    configurazione che al riavvio ci sarebbe comunque.
	prendi_lucchetto || exit 2
	vicini_prima
	riparti nudo "come-al-riavvio" "${2:-}"; e=$?
	vicini_dopo || e=9
	log "Che cosa dice questo numero, e che cosa NON dice"
	if [ "$e" -eq 0 ]; then
		ok "⭐ una sessione appena nata SENZA nessun drop-in di questo banco ha"
		ok "   il monitor: la cura sta nella configurazione persistente, e"
		ok "   sopravvive alla sparizione di \$XDG_RUNTIME_DIR."
	else
		ko "⛔ senza i drop-in di questo banco la sessione esce $e: dopo un"
		ko "   riavvio del server la macchina torna cosi'."
	fi
	att "⚠ e NON e' un riavvio: che /media si rimonti, che il rootfs torni e"
	att "  che qualcuno rilanci provision-server.sh restano [?] finche' un"
	att "  riavvio vero non li tocca (LEZIONI.md §2.5-bis)."
	exit $e
	;;
dispositivi) prendi_lucchetto || exit 2; dispositivi; exit $? ;;
ferma)     prendi_lucchetto || exit 2; ferma_e_aspetta && { ok "fermata"; exit 0; } || { ko "⛔ non si e' fermata"; exit 1; } ;;
certifica) prendi_lucchetto || exit 2; certifica; exit $? ;;
pulisci)   togli_dropin; ok "drop-in di F2.1 tolto: la macchina torna al suo"; exit 0 ;;
*) echo "uso: $0 {guarda|sano|guasto|come-al-riavvio|dispositivi|ferma|certifica|pulisci|guardia [...]}" >&2; exit 2 ;;
esac
