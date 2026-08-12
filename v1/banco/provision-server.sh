#!/bin/bash
#
# provision-server.sh — la macchina di runtime E' IL SERVER, sul ferro nudo.
#
# Deciso dall'utente il 6 agosto 2026: «le prove che riguardano l'hardware
# devono essere fatte su HW nativo, senza avere di mezzo tutta l'infrastruttura
# dell'hypervisor» — e, subito dopo, «usiamo il server nativamente, non tramite
# un container: basta installare gnome sul server».
#
#   bash /media/REMOTIX/provision-server.sh            tutto
#   bash /media/REMOTIX/provision-server.sh monitor    SOLO la §4 (la Shell e il
#                                                      suo monitor virtuale)
#
# ⛔ Il secondo modo esiste per una ragione precisa, non per comodita': la §4 e'
#    l'unica sezione che protegge un difetto GIA' PAGATO — la sessione viva e
#    NERA — e va potuta rimettere, e riprovare, senza far girare apt, senza
#    toccare polkit e senza fermare `remotix.service`.  Una cura che per essere
#    riprovata chiede di rifare tutto non viene riprovata.
#
# ---------------------------------------------------------------------------
# CHE COSA CADE, E VA SAPUTO
#
# ⛔ §6.1 di SPECIFICA.md — «niente deve finire fuori da /media/REMOTIX» — QUI
#    NON VALE PIU', per decisione dell'utente.  Questo script installa pacchetti
#    nel sistema dell'host.  Non e' una svista: e' il prezzo del ferro nudo, ed
#    e' stato scelto sapendolo.
#
# ⚠ IL ROOTFS DEL SERVER VIVE IN RAM e si azzera a ogni riavvio: dopo ogni
#   riavvio questo script va rieseguito.  Per questo la cache di apt sta su
#   `/media` — la seconda volta non scarica niente e costa secondi.
#
# ⛔ §6.2 diceva «macchina di sviluppo e macchina di runtime assolutamente
#    distinte», e adesso sono la stessa.  Il vincolo aveva una ragione — una
#    sessione grafica che muore non deve portarsi via l'ambiente di
#    compilazione — e la ragione resta vera: il codice si compila sempre nel
#    contenitore (`enter.sh`), e qui ci gira soltanto.
#
# ---------------------------------------------------------------------------
# CHE COSA SI GUADAGNA, che e' il punto di tutto
#
# Cadono tutti e quattro i falsanti di §8.6-bis di REFERENCE.md in un colpo:
#
#   | quel che la VM falsava        | sul ferro                                |
#   |-------------------------------|------------------------------------------|
#   | niente 3D (virtio-gpu)        | la iGPU vera, senza VFIO                 |
#   | rete SLIRP in spazio utente   | la rete del server                       |
#   | quattro vCPU                  | venti thread                             |
#   | Mutter su scheda passata      | Mutter sulla scheda, e basta             |
#
# L'ultima riga e' quella per cui si sta facendo tutto questo: dal 6 agosto il
# compositore disegna su una scheda che arriva attraverso l'hypervisor, ed e'
# l'unica cosa nuova rispetto alle fasi 2-8.
# ---------------------------------------------------------------------------
set -euo pipefail

BASE=/media/REMOTIX
CACHE_APT="$BASE/cache/apt"
UTENTE=${SUDO_USER:-$(id -un)}
UID_UTENTE=$(id -u "$UTENTE")
BINARIO="$BASE/src/remotix-c/build/src/remotix"

MODO=${1:-tutto}

# ⛔ LA MISURA DEL MONITOR VIRTUALE — vedi la §4, che e' il motivo per cui
#    questa riga esiste.  1920x1080 e' la misura che la fase 1 gia' annuncia
#    alla pagina («tela 1920x1080», `PIANO.md` fase 1) e quella con cui F2.1 ha
#    certificato il banco della sessione il 12 agosto 2026.
MISURA_MONITOR=${MISURA_MONITOR:-1920x1080}
DROPIN_SHELL=/etc/systemd/user/org.gnome.Shell@wayland.service.d/remotix-headless.conf

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }

# ---------------------------------------------------------------------------
# `systemctl --user` DELL'UTENTE, non di chi sta eseguendo lo script.
#
# ⛔ Se questo script viene lanciato con `sudo`, `systemctl --user` parlerebbe
#    al gestore di ROOT — che non ha nessuna Shell — e il `daemon-reload` non
#    arriverebbe mai a chi deve leggerlo.  Sembrerebbe fatto, e non lo sarebbe:
#    e' la stessa forma del gestore d'utente non riavviato della §2.
# ---------------------------------------------------------------------------
utente_systemctl()
{
	if [ -n "${SUDO_USER:-}" ]; then
		sudo -u "$UTENTE" \
			XDG_RUNTIME_DIR="/run/user/$UID_UTENTE" \
			DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$UID_UTENTE/bus" \
			systemctl --user "$@"
	else
		systemctl --user "$@"
	fi
}

# ===========================================================================
# ⛔ §4 — LA SHELL SENZA SCHERMO, MA **CON** UN MONITOR VIRTUALE
# ===========================================================================
#
# Uscite di questa sezione, scritte prima:
#
#   0  il drop-in e' scritto, e' IN VIGORE con `--virtual-monitor`, e la Shell
#      viva (se c'e') la porta sulla sua riga di comando
#   1  il drop-in e' scritto e NON e' in vigore: un altro drop-in vince sul mio
#      — non e' un dettaglio di forma, e' il difetto che torna
#   2  in vigore, ma la Shell VIVA e' nata prima: quella sessione e' ancora
#      NERA e va rifatta nascere.  Scritto non e' in vigore (E1)
#
# ---------------------------------------------------------------------------
# PERCHE' C'E' `--virtual-monitor`, E PERCHE' NON C'ERA
# ---------------------------------------------------------------------------
#
# ⛔ Dal 9 agosto 2026 alle 10:19 al 12 agosto questa sezione scriveva
#    `--headless --no-x11` e BASTA.  In headless Mutter mette
#    `needs_outputs = false` (`gnome.md` §3.1): la sessione parte, prende i
#    cinquanta nomi sul bus, `IsSessionRunning` risponde `true`, Nautilus e il
#    Terminale si accendono — e `GetCurrentState` dichiara **zero monitor**.
#    Viva, completa, e NERA.
#
# ⭐ E non e' un timore: `[M]` 12 agosto 2026, F2.1.  La sessione viva su questa
#    macchina dal 10 agosto alle 21:01 era esattamente quella, e ci e' rimasta
#    **due giorni** senza che nessuno se ne accorgesse, perche' tutti quelli che
#    l'hanno guardata hanno fatto UNA domanda sola — «e' viva?» — e la risposta
#    era si'.  La seconda domanda — «ha un monitor?» — non gliel'ha fatta
#    nessuno.  Chi avesse misurato la cattura la' sopra avrebbe letto zero
#    fotogrammi e sarebbe andato a cercare il difetto dentro PipeWire.
#
# ⚠ E la sessione nera non e' solo cieca: e' FRAGILE.  `Shell.Screenshot` su
#   zero monitor fa tentare a Mutter una texture 0x0, l'assert
#   `cogl_texture_2d_new_with_size: width >= 1` fallisce, e siccome l'unita'
#   porta `OnFailure=gnome-session-shutdown.target` se ne va TUTTA la sessione
#   `[M]`.  ⛔ Quindi non si controlla se c'e' un monitor chiedendo uno
#   screenshot: si chiede `GetCurrentState`, che e' quel che fa
#   `banchi/02-sessione-guardia.sh`.
#
# ---------------------------------------------------------------------------
# ⛔ E QUESTA CURA E' **I7 A META'**, E VA DETTO QUI INVECE CHE SCOPERTO DOPO
# ---------------------------------------------------------------------------
#
# `CODER.md` §2 I7: *la protezione di un difetto noto sta nel programma, non in
# una riga di configurazione che si puo' perdere*.  Questa E' una riga di
# configurazione, su un rootfs che vive in RAM: sopravvive al riavvio solo
# perche' dopo ogni riavvio questo script va rieseguito — che e' la stessa
# fragilita' per cui la riga di guardia del DMA-BUF e' finita nel codice il 7
# agosto (vedi la §6 qui sotto, ed e' la stessa storia).
#
# ⇒ La cura DEFINITIVA e' di prodotto e sta scritta nel rapporto di F2.1:
#   `v1/remotix-c/src/sessione.c:671` scrive il drop-in del monitor **solo se il
#   compositore e' KWin**, e sul ramo GNOME `larghezza` e `altezza` entrano in
#   `sessione_assicura()` e si perdono.  Finche' quella riga non cambia, la
#   protezione sta qui — e qui si dichiara mezza, invece di far credere che sia
#   intera.
# ---------------------------------------------------------------------------
sezione_monitor()
{
	log "gnome-shell headless, e CON il monitor virtuale $MISURA_MONITOR"
	sudo mkdir -p /etc/systemd/user/org.gnome.Shell@wayland.service.d
	# ⛔ SI SCRIVE SEMPRE, non solo se manca: un file che c'e' gia' puo' essere
	#    quello vecchio senza l'opzione, ed e' precisamente il caso che si e'
	#    pagato.  Vale la stessa regola del predefinito del DMA-BUF, §6.
	sudo tee "$DROPIN_SHELL" >/dev/null <<CONF
[Service]
ExecStart=
ExecStart=/usr/bin/gnome-shell --headless --no-x11 --virtual-monitor $MISURA_MONITOR
CONF
	ok "scritto $DROPIN_SHELL"

	# Le unita' d'utente le legge il gestore DELL'UTENTE: senza questo, il file
	# c'e' e non lo conosce nessuno.
	utente_systemctl daemon-reload || { ko "daemon-reload d'utente fallito"; return 1; }

	# ⛔ SCRITTO NON E' IN VIGORE (E1: necessario preso per sufficiente).  I
	#    drop-in di TUTTE le cartelle si applicano in ordine di NOME FILE, e su
	#    questa macchina ce ne sono altri due — `00-registro.conf` nella home e
	#    `zz-f21-monitor.conf` in $XDG_RUNTIME_DIR.  Un file che comincia per
	#    `zz-` vince su questo: se qualcuno ne ha lasciato uno in giro, questa
	#    sezione deve DIRLO, non dare per buono di aver vinto.
	local vigore
	vigore=$(utente_systemctl show -p ExecStart --value org.gnome.Shell@wayland.service)
	inf "ExecStart in vigore: $vigore"
	case "$vigore" in
	*--virtual-monitor\ $MISURA_MONITOR*)
		ok "il monitor virtuale $MISURA_MONITOR e' IN VIGORE" ;;
	*)
		ko "⛔ ho scritto --virtual-monitor $MISURA_MONITOR e il gestore d'utente NON lo dice."
		ko "   Un altro drop-in vince sul mio.  I drop-in in vigore sono:"
		utente_systemctl show -p DropInPaths --value org.gnome.Shell@wayland.service \
		    | tr ' ' '\n' | sed 's/^/        /'
		ko "   ⇒ togli quello che vince (per F2.1: bash banchi/02-sessione-lancia.sh pulisci)"
		return 1 ;;
	esac

	# ⛔ E IL DROP-IN VALE DALLA PROSSIMA NASCITA DELLA SHELL, NON PER QUELLA
	#    VIVA.  E' il modo esatto in cui il difetto puo' restare invisibile
	#    un'altra volta: si riesegue il provisioning, si legge «OK», e la
	#    sessione che sta girando e' ancora quella nera di prima.
	local viva righe=""
	if viva=$(pgrep -u "$UID_UTENTE" -x gnome-shell); then
		for p in $viva; do
			righe="$righe $(tr '\0' ' ' <"/proc/$p/cmdline")"
		done
		case "$righe" in
		*--virtual-monitor*)
			ok "e la Shell viva (pid $(echo $viva | tr '\n' ' ')) la porta gia'" ;;
		*)
			ko "⛔ IL DROP-IN E' A POSTO, MA LA SESSIONE CHE STA GIRANDO E' NERA."
			ko "   La Shell viva e' nata prima ed ha ancora la riga vecchia:"
			ko "  $righe"
			ko "   ⇒ va fatta rinascere:  bash /media/REMOTIX/f21/02-sessione-lancia.sh sano"
			ko "   ⇒ e si verifica con:   bash /media/REMOTIX/f21/02-sessione-guardia.sh"
			return 2 ;;
		esac
	else
		# ⛔ Zero e fallimento sono due cose diverse: `pgrep` esce 1 se non ha
		#    trovato niente, 2 o piu' se e' ANDATO MALE.
		local e=$?
		if [ "$e" -eq 1 ]; then
			inf "nessuna sessione viva adesso: la prossima nascera' col monitor"
		else
			ko "⛔ pgrep e' uscito con $e: non ho potuto guardare la Shell viva"
			return 1
		fi
	fi
	return 0
}

# ---------------------------------------------------------------------------
# Il contenuto.  E' lo stesso elenco di `provision-vm.sh`, e non e' pigrizia:
# due macchine di runtime con dentro cose diverse darebbero misure non
# confrontabili, e il senso del trasloco e' proprio poter confrontare.
# ---------------------------------------------------------------------------
PKGS=(
    # GNOME ridotto all'osso: il compositore e' il bersaglio del progetto
    gnome-shell gnome-session gnome-control-center nautilus gnome-terminal
    # il browser serve alla riproduzione del difetto: il video si guarda li'
    firefox-esr
    # suono: sorgente e destinazione (§3.2 di SPECIFICA.md)
    pipewire pipewire-pulse wireplumber
    # quel che il binario pretende a runtime.  Il binario NON si compila qui:
    # si compila nel contenitore e si copia — §6.2 vale ancora per questo.
    libfreerdp3-3 libfreerdp-server3-3 libwinpr3-3
    libpipewire-0.3-0 libei1 libxkbcommon0
    libavcodec61 libavutil59 libswscale8 libavfilter10
    # fase 9: la scheda, e stavolta e' quella vera
    intel-media-va-driver va-driver-all vainfo
    #
    # ⛔ QUEL CHE MANCAVA, E CHE SI E' VISTO SOLO RIAVVIANDO — 8 agosto 2026.
    #    Erano tutti installati a mano mesi prima: il provisioning li ereditava
    #    senza dichiararli, e il primo riavvio vero ha lasciato la macchina senza.
    #    Chi rimette una macchina non deve scoprire i pezzi mancanti uno per uno.
    #
    # fase 11: il secondo compositore.  Non parte da solo — lo avvia REMOTIX
    # quando un client si collega con --compositore kwin — ma se non c'e' il
    # pacchetto non c'e' niente da avviare.
    kwin-wayland kwin-common plasma-workspace
    # i banchi dell'audio (prove/fase11-volume.sh): pactl, parecord, paplay
    pulseaudio-utils
    # i banchi degli appunti (prove/fase11-appunti.sh): i due versi della clipboard
    wl-clipboard xclip
)

# ---------------------------------------------------------------------------
# 0. Privilegi
# ---------------------------------------------------------------------------
if ! sudo -n true 2>/dev/null; then
    log "Privilegi di amministratore"
    sudo -v -S -p 'Password sudo: '
fi

# ---------------------------------------------------------------------------
# 0-bis. I due modi.  `monitor` fa la sola §4 ed esce col suo numero.
# ---------------------------------------------------------------------------
case "$MODO" in
tutto) ;;
monitor)
    E=0
    sezione_monitor || E=$?
    exit $E
    ;;
*)
    echo "uso: $0 [tutto|monitor]" >&2
    exit 2
    ;;
esac

# ---------------------------------------------------------------------------
# 1. La cache di apt su /media
#
# Il rootfs si azzera a ogni riavvio; la cache no.  Senza questo, ogni riavvio
# del server costa un download di quasi un gigabyte prima di poter provare
# qualcosa — cioe' la differenza fra «riprovo» e «riprovo domani».
# ---------------------------------------------------------------------------
log "Cache dei pacchetti su $CACHE_APT"
mkdir -p "$CACHE_APT/partial" "$CACHE_APT/lists/partial"
sudo tee /etc/apt/apt.conf.d/99-remotix-cache >/dev/null <<CONF
Dir::Cache::archives "$CACHE_APT";
CONF
ok "i .deb scaricati sopravvivono al riavvio"

# ---------------------------------------------------------------------------
# 2. La scheda dev'essere dell'host
#
# ⛔ FINCHE' LA VM E' ACCESA LA iGPU E' SUA: e' legata a `vfio-pci` e
#    `/dev/dri` dell'host non la contiene affatto.  Si spegne la VM e si
#    restituisce.
# ---------------------------------------------------------------------------
log "La iGPU Intel dev'essere dell'host"
if pgrep -f 'qemu-system-x86_64 -name remotix-vm' >/dev/null 2>&1; then
    inf "la VM e' accesa: la fermo"
    bash "$BASE/vm.sh" ferma >/dev/null 2>&1 || pkill -f 'qemu-system-x86_64 -name remotix-vm' || true
    sleep 3
fi
if [ -e /sys/bus/pci/devices/0000:00:02.0/driver ]; then
    DRV=$(basename "$(readlink -f /sys/bus/pci/devices/0000:00:02.0/driver)")
    [ "$DRV" = vfio-pci ] && bash "$BASE/vm.sh" gpu restituisci
fi
inf "nodi DRM: $(ls /dev/dri 2>/dev/null | tr '\n' ' ')"

# ⛔ E L UTENTE DEVE POTERLA APRIRE.  I nodi di rendering appartengono al gruppo
#    `render`, e chi non ci sta dentro riceve «Failed to open the given device!»
#    — che sembra una scheda assente e invece e' un permesso.  Nella VM l utente
#    era gia' nei gruppi giusti perche' li' lo creava cloud-init; qui no.
if ! id -nG "$UTENTE" | grep -qw render; then
    sudo usermod -aG render,video "$UTENTE"
    inf "$UTENTE aggiunto a render e video"
    # ⛔ E IL GESTORE SYSTEMD DELL UTENTE VA RIAVVIATO, o non serve a niente.
    #
    #    La Shell non la lancia REMOTIX: la lancia `systemd --user`, che era gia'
    #    in piedi — il linger lo tiene acceso — e i gruppi supplementari di un
    #    processo vivo non cambiano.  Senza questo riavvio la Shell nasce senza
    #    `video` e `render`, non puo' aprire /dev/dri, e Mutter ripiega sul
    #    RENDERING IN SOFTWARE: nessun errore da nessuna parte, e la cattura a
    #    copia zero non si accende perche' non ci sono DMA-BUF da consegnare.
    #    Misurato il 6 agosto 2026, al primo giro sul ferro.
    sudo systemctl stop remotix.service 2>/dev/null || true
    sudo systemctl restart "user@$UID_UTENTE.service" || true
    sleep 2
    inf "gestore systemd dell'utente riavviato: la Shell nascera' nei gruppi giusti"
fi

# ---------------------------------------------------------------------------
# 3. I pacchetti
# ---------------------------------------------------------------------------
log "Contenuto della macchina di runtime"
MANCANTI=()
for p in "${PKGS[@]}"; do
    dpkg -s "$p" >/dev/null 2>&1 || MANCANTI+=("$p")
done
if [ ${#MANCANTI[@]} -gt 0 ]; then
    inf "mancanti: ${MANCANTI[*]}"
    sudo apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends "${MANCANTI[@]}"
    ok "installati"
else
    ok "gia' presenti (${#PKGS[@]} pacchetti)"
fi

# Il binario e' stato compilato nel contenitore: qui deve solo TROVARE le sue
# librerie.  Se ne manca una lo si scopre adesso, non quando un client si
# collega e il servizio non parte senza spiegare perche'.
if [ -x "$BINARIO" ]; then
    if MANCA=$(ldd "$BINARIO" 2>/dev/null | grep 'not found'); then
        ko "al binario mancano delle librerie sull'host:"
        printf '%s\n' "$MANCA" | sed 's/^/        /'
    else
        ok "il binario del contenitore trova tutte le sue librerie qui"
    fi
else
    inf "il binario non c'e' ancora: compilalo con enter.sh"
fi

# ---------------------------------------------------------------------------
# 3-bis. I banchi devono poter guidare il servizio senza fermarsi a chiedere
#
# ⛔ `sudo` CHE CHIEDE LA PASSWORD CON LO STANDARD INPUT CHIUSO NON TORNA PIU'.
#
#    I banchi eseguono i comandi con lo standard input da /dev/null — regola
#    pagata in fase 4, perche' un comando che eredita un terminale che non
#    finisce mai non torna — e `sudo` in quelle condizioni non puo' chiedere
#    niente.  Nella VM non si vedeva: cloud-init da' `sudo` senza password.  Sul
#    server no, e il sintomo arriva travestito — il servizio che non riparte e
#    il client del banco respinto perche' l'autenticazione era ancora accesa.
#
# ⚠ E' una concessione di privilegio su una macchina vera, quindi e' RISTRETTA
#   ai quattro comandi che i banchi usano davvero.  `tee` in particolare e'
#   limitato a UN file: `sudo tee` senza vincoli equivale a scrivere ovunque
#   come root, cioe' a `sudo` intero.
#
#   Vive nel rootfs in RAM: sparisce da se' al riavvio.
# ---------------------------------------------------------------------------
log "I banchi possono guidare il servizio"
sudo tee /etc/sudoers.d/remotix-banchi >/dev/null <<SUDOERS
$UTENTE ALL=(root) NOPASSWD: /usr/bin/systemctl, /usr/bin/loginctl, /usr/sbin/nft, /usr/bin/tee /etc/default/remotix
SUDOERS
sudo chmod 440 /etc/sudoers.d/remotix-banchi
sudo visudo -c -q -f /etc/sudoers.d/remotix-banchi && ok "quattro comandi, senza password" \
    || { ko "regola sudoers non valida: la tolgo"; sudo rm -f /etc/sudoers.d/remotix-banchi; }

# ---------------------------------------------------------------------------
# 4. La Shell senza schermo, MA CON UN MONITOR (§5.9-bis di SPECIFICA.md)
#
# L'unita' della Shell non prevede `--headless` sulla riga di comando: si
# sovrascrive.  Sta in /etc/systemd/user perche' vale per l'utente qualunque sia
# la sua home — e la home, a differenza del rootfs, e' su /media? no: e' in RAM
# anch'essa, quindi tutto qui dentro va rifatto a ogni riavvio.  Lo script e'
# idempotente apposta.
#
# ⛔ Il corpo, e il perche' per intero, stanno in `sezione_monitor()` in testa:
#    e' l'unica sezione che si puo' rifare da sola (`provision-server.sh
#    monitor`), perche' e' l'unica che protegge un difetto gia' pagato.
# ---------------------------------------------------------------------------
E_MONITOR=0
sezione_monitor || E_MONITOR=$?

# ---------------------------------------------------------------------------
# 5. Quel che una sessione remota non deve poter fare (§3.4-bis)
#
# ⚠ QUI PESA PIU' CHE NELLA VM, ed e' il motivo per cui non si salta: adesso la
#   macchina che una sessione remota potrebbe spegnere e' IL SERVER, non una VM
#   effimera.  E il server ha il rootfs in RAM: uno spegnimento da lontano si
#   ripara andando fisicamente davanti alla macchina, e si porta via tutto quel
#   che questo script ha installato.
# ---------------------------------------------------------------------------
log "Sospensione e spegnimento tolti alla sessione remota"
sudo mkdir -p /etc/systemd/sleep.conf.d /etc/polkit-1/rules.d
sudo tee /etc/systemd/sleep.conf.d/remotix-niente-sospensione.conf >/dev/null <<'CONF'
[Sleep]
AllowSuspend=no
AllowHibernation=no
AllowSuspendThenHibernate=no
AllowHybridSleep=no
CONF
sudo tee /etc/polkit-1/rules.d/49-remotix-niente-spegnimento.rules >/dev/null <<'RULES'
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.login1.power-off" ||
        action.id == "org.freedesktop.login1.reboot" ||
        action.id == "org.freedesktop.login1.halt")
        return polkit.Result.NO;
});
RULES
sudo systemctl restart polkit >/dev/null || true
ok "sleep.conf e polkit"

# ---------------------------------------------------------------------------
# 6. REMOTIX come servizio
#
# Identica all'unita' della VM, compresi i due limiti di R26: senza,
# `RLIMIT_RTPRIO` resta a zero, PipeWire non puo' chiedere `SCHED_FIFO` e sotto
# carico la cattura audio perde campioni.
# ---------------------------------------------------------------------------
log "REMOTIX come servizio di sistema"
sudo tee /etc/systemd/system/remotix.service >/dev/null <<UNITA
[Unit]
Description=REMOTIX — server RDP per Linux (sul ferro)
After=network.target systemd-logind.service
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=$UTENTE
EnvironmentFile=-/etc/default/remotix
Environment=XDG_RUNTIME_DIR=/run/user/$UID_UTENTE
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$UID_UTENTE/bus
ExecStart=/home/$UTENTE/remotix --porta 3389 \$REMOTIX_OPZIONI
Restart=on-failure
RestartSec=2
LimitRTPRIO=20
LimitNICE=-11
Slice=system.slice
StandardOutput=append:/home/$UTENTE/remotix.log
StandardError=append:/home/$UTENTE/remotix.log

[Install]
WantedBy=multi-user.target
UNITA
# ⛔ LA COPIA ZERO NASCE SPENTA, dal 7 agosto 2026, e non e' prudenza generica.
#
#    Con `REMOTIX_DMABUF` non impostata la cattura passa dal DMA-BUF, e li' il
#    buffer che Mutter presta non e' un fotogramma intero: e' il buffer di
#    qualche giro fa con ridipinta dentro la sola parte cambiata (misurato: 282
#    fotogrammi su 300).  Il client vede riapparire schermate gia' passate.
#    R29 di REFERENCE.md ha la diagnosi per intero e i due tentativi falliti.
#
#    Costo di tenerla spenta: 18 ms di CPU per fotogramma invece di 6.  La
#    codifica H.264 resta in GPU: quella funziona.
#    ⛔ E DAL 7 AGOSTO IL PREDEFINITO STA NEL CODICE (`palco.c`), non qui.  Il
#       file d'ambiente vive in RAM ed e' stato riscritto per cambiare la porta:
#       la riga di guardia e' sparita con lui e il difetto e' tornato in faccia
#       all'utente lo stesso giorno.  Questa riga resta per chiarezza — chi
#       legge il file deve vedere com'e' configurato — ma non e' piu' lei a
#       proteggere: si SCRIVE SEMPRE, non solo alla prima volta.
[ -f /etc/default/remotix ] || printf 'REMOTIX_OPZIONI=--registro diagnostica\n' | sudo tee /etc/default/remotix >/dev/null
grep -q '^REMOTIX_DMABUF=' /etc/default/remotix \
    || printf 'REMOTIX_DMABUF=0\n' | sudo tee -a /etc/default/remotix >/dev/null
sudo loginctl enable-linger "$UTENTE" 2>/dev/null || true
sudo systemctl daemon-reload
ok "remotix.service, con LimitRTPRIO=20 (R26)"

# ---------------------------------------------------------------------------
# 7. Lo script di guida, gemello di vm.sh
# ---------------------------------------------------------------------------
log "Script di guida"
cat > "$BASE/server.sh" <<'GUIDA'
#!/bin/bash
#
# server.sh — guida la macchina di runtime, che adesso E' il server.
#
#   server.sh copia [file]   porta il binario compilato in ~ e riavvia
#   server.sh avvia          accende il servizio
#   server.sh ferma          lo spegne
#   server.sh stato          e' vivo?  e la sessione grafica?
#   server.sh registro [n]   le ultime n righe
#   server.sh opzioni <...>  riscrive /etc/default/remotix e riavvia
#
# Gemello di `vm.sh`, con gli stessi verbi: i banchi non devono imparare due
# vocabolari.  Quel che manca e' `ssh`, perche' non c'e' piu' nessun altrove
# dove entrare — ed e' esattamente il punto del trasloco.
set -u
BASE=/media/REMOTIX
BINARIO="$BASE/src/remotix-c/build/src/remotix"
CASA="$HOME"

case "${1:-stato}" in
copia)
    SORGENTE="${2:-$BINARIO}"
    [ -x "$SORGENTE" ] || { echo "manca $SORGENTE: compilalo con enter.sh"; exit 1; }
    sudo systemctl stop remotix.service
    cp -f "$SORGENTE" "$CASA/remotix"
    chmod +x "$CASA/remotix"
    sudo systemctl start remotix.service
    sleep 2
    systemctl is-active --quiet remotix.service && echo "copiato e riavviato" || echo "copiato, ma il servizio NON e' partito"
    ;;
avvia)   sudo systemctl start remotix.service; sleep 2; systemctl is-active remotix.service ;;
ferma)   sudo systemctl stop remotix.service; echo fermato ;;
stato)
    echo "servizio:  $(systemctl is-active remotix.service)"
    # La porta si LEGGE da chi ascolta, non si da' per scontata: `opzioni
    # --porta N` la sposta, e un controllo inchiodato al 3389 direbbe «spento»
    # su un server sanissimo — la diagnosi sbagliata di §8.6 di REFERENCE.md.
    ASCOLTO=$(ss -ltnp 2>/dev/null | awk '/"remotix"/{sub(/.*:/, "", $4); print $4}' | tr '\n' ' ')
    echo "porta:     ${ASCOLTO:-nessuna }in ascolto"
    echo "sessione:  $(pgrep -c gnome-shell) gnome-shell"
    echo "schede:    $(ls /dev/dri 2>/dev/null | tr '\n' ' ')"
    ;;
registro) tail -n "${2:-40}" "$CASA/remotix.log" ;;
opzioni)
    shift
    printf 'REMOTIX_OPZIONI=%s\n' "$*" | sudo tee /etc/default/remotix >/dev/null
    sudo systemctl restart remotix.service; sleep 2
    systemctl is-active --quiet remotix.service && echo "opzioni: $*" || echo "NON riavviato"
    ;;
*) echo "comandi: copia | avvia | ferma | stato | registro [n] | opzioni <...>"; exit 1 ;;
esac
GUIDA
chmod +x "$BASE/server.sh"
ok "$BASE/server.sh"

# Il rootfs del tentativo con nspawn non serve piu': si toglie invece di
# lasciarlo li' a far credere che ci sia ancora un contenitore di runtime.
if [ -d "$BASE/runtime" ]; then
    inf "rimuovo il rootfs del tentativo con nspawn"
    sudo rm -rf "$BASE/runtime"
fi

log "Fatto"
inf "porta il binario:  bash $BASE/server.sh copia"
inf "poi collegati a:   $(hostname -I 2>/dev/null | awk '{print $1}'):3389"
inf "⚠ dopo un riavvio del server questo script va rieseguito: / vive in RAM"
# ⛔ E LA §4 NON SI RIASSUME IN «Fatto».  Se il monitor virtuale non e' in
#    vigore, quel che segue e' una macchina che parte, si collega, e consegna
#    una schermata nera senza un errore da nessuna parte: e' il difetto che ha
#    vissuto due giorni su questa macchina, e non deve poter uscire dal fondo di
#    questo script travestito da riga verde.
if [ "$E_MONITOR" -ne 0 ]; then
    ko "⛔ LA §4 (il monitor virtuale) e' uscita con $E_MONITOR: leggila sopra."
    ko "   Finche' non e' 0, ogni misura che dipende dalla sessione grafica"
    ko "   vale zero — e non per colpa di chi la prende."
    exit "$E_MONITOR"
fi
inf "la sessione grafica si verifica con: bash $BASE/f21/02-sessione-guardia.sh"
