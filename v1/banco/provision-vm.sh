#!/bin/bash
#
# REMOTIX - provisioning della macchina virtuale di runtime
# ==========================================================
#
# Questo script gira DENTRO la VM, non sul server. Si lancia dall'esterno con:
#
#   bash /media/REMOTIX/vm.sh provision
#
# La VM e' effimera: "vm.sh reset" la riporta allo stato di fabbrica, e questo
# script la rimette in piedi. E' idempotente, quindi rilanciarlo e' innocuo.
#
#
# CRITERIO: IL MINIMO INDISPENSABILE
# ----------------------------------
# Si installano singoli pacchetti, non i metapacchetti di comodo, e SEMPRE
# senza i pacchetti raccomandati. La differenza misurata e' netta: 498
# pacchetti invece di 902, senza perdere nulla di essenziale.
#
# Anche senza raccomandati entrano comunque PipeWire, WirePlumber,
# xdg-desktop-portal-gnome, XWayland, gnome-settings-daemon e dbus-user-session,
# cioe' proprio i componenti che servono alla cattura dello schermo e alla
# sessione senza monitor. Mutter non compare come pacchetto a se' perche'
# gnome-shell lo incorpora come libreria (libmutter-16-0).
#
# Fra i raccomandati ci sarebbe anche gnome-remote-desktop, il server RDP di
# GNOME, che si contenderebbe con REMOTIX la porta 3389. Lo installiamo di
# proposito ma DISATTIVATO: serve come termine di paragone, perche' sa avviare
# una sessione GNOME senza monitor e ci permette di accertare che la cosa
# funzioni su questa VM indipendentemente dal nostro codice.
#
set -euo pipefail
export LC_ALL=C DEBIAN_FRONTEND=noninteractive

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

# ---------------------------------------------------------------------------
# GNOME ridotto all'osso. Primo bersaglio del piano di sviluppo.
# ---------------------------------------------------------------------------
GNOME_PKGS=(
    gnome-shell            # il compositor (Mutter incorporato) e la shell
    gnome-session          # avvio e gestione della sessione
    gnome-control-center   # impostazioni, utile per provare schermo e input
    nautilus               # gestore file, utile per provare la clipboard
    gnome-terminal         # terminale nella sessione remota
)

# Riferimento, installato ma tenuto disattivato.
REFERENCE_PKGS=(
    gnome-remote-desktop
)

# ---------------------------------------------------------------------------
# Fase 9: quel che serve a codificare in GPU.
#
# Si installano SEMPRE, anche quando la scheda non e' stata ceduta: sono pochi
# megabyte, e la VM e' effimera — un provisioning che dipendesse dalla presenza
# della GPU produrrebbe due macchine diverse a seconda del giorno, cioe' misure
# non confrontabili.
#
# ⚠ Il firmware non e' un di piu': senza, i915 nella VM scrive «Failed to load
#   DMC firmware» e «GuC firmware fetch failed», e quel che resta e' una scheda
#   che si inizializza a meta'. Misurato il 6 agosto 2026, al primo avvio con la
#   scheda passata.
#
#   ⛔ E il pacchetto e' `firmware-intel-graphics`, NON `firmware-misc-nonfree`:
#      su Trixie il firmware delle Intel e' stato staccato in un pacchetto suo.
#      Installando quello sbagliato `dpkg -l` e' contento, `/lib/firmware/i915`
#      non esiste, e il registro del kernel continua a dire la stessa cosa —
#      cioe' si crede di aver corretto e non si e' corretto niente.
#
#   ⚠ E VA CARICATO ALL'AVVIO: i915 cerca il firmware quando si inizializza,
#      non dopo. Installarlo a macchina accesa non cambia nulla finche' non si
#      riavvia la VM.
#
# ⚠ Il driver VA-API dev'essere **iHD** (`intel-media-va-driver`): il vecchio
#   i965 si ferma alle generazioni precedenti alla 12, e questa e' una Raptor
#   Lake. Con il driver sbagliato `vainfo` elenca profili di sola decodifica e
#   la fase 9 non avrebbe dove appoggiarsi.
GPU_PKGS=(
    firmware-intel-graphics   # DMC e GuC, che i915 cerca all'avvio
    firmware-misc-nonfree     # il resto, per non dipendere dalla scheda
    intel-media-va-driver     # iHD: il driver VA-API delle Intel moderne
    va-driver-all             # gli altri, per non dipendere dalla scheda
    vainfo                    # dice quali profili la scheda sa CODIFICARE
    ffmpeg                    # diagnosi: `ffmpeg -encoders` dice che c'e' davvero
)

# ---------------------------------------------------------------------------
# 0. Attendere che la configurazione iniziale sia conclusa
# ---------------------------------------------------------------------------
if command -v cloud-init >/dev/null 2>&1; then
    log "Configurazione iniziale"
    cloud-init status --wait >/dev/null 2>&1 || true
    ok "conclusa"
fi

# ---------------------------------------------------------------------------
# 1. Indice dei pacchetti
# ---------------------------------------------------------------------------
log "Indice dei pacchetti"
sudo apt-get update -qq
ok "aggiornato"

# ---------------------------------------------------------------------------
# 2. GNOME minimale
# ---------------------------------------------------------------------------
log "GNOME minimale"
MISSING=()
for p in "${GNOME_PKGS[@]}"; do
    dpkg -s "$p" >/dev/null 2>&1 || MISSING+=("$p")
done
if [ ${#MISSING[@]} -gt 0 ]; then
    inf "mancanti: ${MISSING[*]}"
    inf "installazione senza raccomandati, circa 500 pacchetti..."
    sudo apt-get install -y -qq --no-install-recommends "${MISSING[@]}"
    ok "installato"
else
    ok "gia' presente"
fi

# ---------------------------------------------------------------------------
# 3. Riferimento: gnome-remote-desktop, installato ma disattivato
# ---------------------------------------------------------------------------
log "Riferimento gnome-remote-desktop"
MISSING=()
for p in "${REFERENCE_PKGS[@]}"; do
    dpkg -s "$p" >/dev/null 2>&1 || MISSING+=("$p")
done
if [ ${#MISSING[@]} -gt 0 ]; then
    sudo apt-get install -y -qq --no-install-recommends "${MISSING[@]}"
    ok "installato"
else
    ok "gia' presente"
fi

# Va tenuto fermo: occuperebbe la porta 3389, che e' di REMOTIX.
# Si riattiva a mano quando serve come termine di paragone.
inf "lo disattivo (occuperebbe la porta 3389)"
sudo systemctl disable --now gnome-remote-desktop.service   >/dev/null 2>&1 || true
sudo systemctl mask         gnome-remote-desktop.service    >/dev/null 2>&1 || true
sudo systemctl --global disable gnome-remote-desktop.service >/dev/null 2>&1 || true
ok "disattivato e bloccato"
inf "per usarlo come riferimento: sudo systemctl unmask gnome-remote-desktop"

# ---------------------------------------------------------------------------
# 3-bis. Accelerazione hardware (fase 9)
# ---------------------------------------------------------------------------
log "Accelerazione hardware"

# I firmware stanno in `non-free-firmware`, che l'immagine cloud non abilita
# sempre. Si aggiunge la sezione se manca, invece di lasciare fallire l'apt con
# un «impossibile trovare il pacchetto» che sembra un errore di battitura.
if ! grep -rqs 'non-free-firmware' /etc/apt/sources.list /etc/apt/sources.list.d/ 2>/dev/null; then
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then
        sudo sed -i 's/^Components: .*/& non-free-firmware/' /etc/apt/sources.list.d/debian.sources
    else
        sudo sed -i 's/^\(deb .*trixie.*main\)$/\1 non-free-firmware/' /etc/apt/sources.list
    fi
    sudo apt-get update -qq
    inf "sezione non-free-firmware aggiunta"
fi

MISSING=()
for p in "${GPU_PKGS[@]}"; do
    dpkg -s "$p" >/dev/null 2>&1 || MISSING+=("$p")
done
if [ ${#MISSING[@]} -gt 0 ]; then
    inf "mancanti: ${MISSING[*]}"
    sudo apt-get install -y -qq --no-install-recommends "${MISSING[@]}"
    ok "installato"
else
    ok "gia' presente"
fi

# Che cosa c'e' davvero, detto adesso e non scoperto in fase di misura.
if [ -e /dev/dri/renderD128 ]; then
    inf "nodi di rendering: $(ls /dev/dri | tr '\n' ' ')"
    if command -v vainfo >/dev/null 2>&1; then
        ENC=$(vainfo 2>/dev/null | grep -cE 'H264.*Enc' || true)
        if [ "${ENC:-0}" -gt 0 ]; then
            ok "VA-API sa codificare H.264 ($ENC profili)"
        else
            inf "VA-API non offre codifica H.264: la scheda non e' stata ceduta, o manca il driver"
        fi
    fi
else
    inf "nessun nodo di rendering: la VM gira senza GPU (vedi 'vm.sh gpu prendi')"
fi

# ---------------------------------------------------------------------------
# 3-ter. Una sola scheda DRM per l'ospite
# ---------------------------------------------------------------------------
#
# ⛔ MUTTER DISEGNA SULLA SCHEDA CHE TROVA PER PRIMA, e la prima e' la VGA
#    d'emergenza di QEMU (`bochs`), che non ha nodo di rendering: da li'
#    discende la composizione in software, e soprattutto discende che i
#    fotogrammi consegnati a PipeWire siano buffer di QUELLA scheda.  Un DMA-BUF
#    cosi' non si importa nella Intel: la cattura a copia zero della fase 9 non
#    avrebbe dove appoggiarsi, e il ripiego sarebbe silenzioso.
#
#    La VGA d'emergenza serve pero' all'AVVIO — provato il 6 agosto a togliere
#    ogni scheda video dalla riga di QEMU: GRUB annuncia l'avvio e la macchina
#    non risponde piu'.  La si lascia quindi al firmware e la si spegne dentro
#    Linux, che e' l'unico posto dove da' fastidio.
#
#    Resta vero anche senza GPU ceduta: li' la prima scheda diventa virtio-gpu,
#    che un nodo di rendering ce l'ha.
log "Una sola scheda DRM"
if grep -q 'modprobe.blacklist=bochs' /etc/default/grub 2>/dev/null; then
    ok "bochs gia' spento nella riga di comando del kernel"
else
    sudo sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT="\(.*\)"$/GRUB_CMDLINE_LINUX_DEFAULT="\1 modprobe.blacklist=bochs"/' \
        /etc/default/grub
    sudo update-grub >/dev/null 2>&1
    ok "bochs spento (ha effetto al prossimo riavvio della VM)"
fi

# ---------------------------------------------------------------------------
# 4. Nessun gestore di accesso grafico
#    Un display manager tenterebbe di avviare una sessione locale, che qui
#    non ha senso e interferirebbe con le regole di sessione di REMOTIX.
# ---------------------------------------------------------------------------
log "Gestori di accesso grafico"
FOUND=""
for dm in gdm3 lightdm sddm xdm; do
    dpkg -s "$dm" >/dev/null 2>&1 && FOUND="$FOUND $dm"
done
if [ -n "$FOUND" ]; then
    inf "trovati:$FOUND — li disattivo"
    for dm in $FOUND; do
        sudo systemctl disable --now "$dm" >/dev/null 2>&1 || true
    done
    ok "disattivati"
else
    ok "nessuno presente, come desiderato"
fi

# ---------------------------------------------------------------------------
# 5. Servizi audio e portali dell'utente
#    Sono servizi "utente": si attivano nella sessione, non nel sistema.
#    Qui si verifica soltanto che i pezzi ci siano.
# ---------------------------------------------------------------------------
log "Componenti per cattura e audio"
for p in pipewire wireplumber xdg-desktop-portal xdg-desktop-portal-gnome xwayland dbus-user-session; do
    if dpkg -s "$p" >/dev/null 2>&1; then
        printf '    \033[1;32mOK\033[0m  %-28s %s\n' "$p" "$(dpkg-query -W -f='${Version}' "$p" 2>/dev/null)"
    else
        printf '    \033[1;31m--\033[0m  %-28s ASSENTE\n' "$p"
    fi
done

# ---------------------------------------------------------------------------
# 6. Niente sospensione
#
#    Una macchina che ospita sessioni remote non deve potersi sospendere: chi e'
#    collegato da lontano la spegnerebbe sotto i piedi di chi ci sta lavorando
#    da vicino o da un'altra sessione. Il danno non e' suo, e' di terzi.
#
#    Si toglie la CAPACITA', non si nasconde la voce di menu. Cosi' sparisce da
#    se' dal menu di GNOME — che la mostra solo se logind dichiara di potersi
#    sospendere — e insieme sparisce da ogni altra strada: loginctl, un altro
#    ambiente desktop, una scorciatoia di tastiera.
#
#    Si verifica con:
#      busctl call org.freedesktop.login1 /org/freedesktop/login1 \
#             org.freedesktop.login1.Manager CanSuspend
#    Deve rispondere "no". Se risponde "challenge", la voce e' ancora li'.
# ---------------------------------------------------------------------------
log "Sospensione disabilitata"
sudo mkdir -p /etc/systemd/sleep.conf.d
sudo tee /etc/systemd/sleep.conf.d/remotix-niente-sospensione.conf >/dev/null <<'CONF'
# Posato da REMOTIX: una macchina che ospita sessioni remote non si sospende.
[Sleep]
AllowSuspend=no
AllowHibernation=no
AllowSuspendThenHibernate=no
AllowHybridSleep=no
CONF
sudo systemctl restart systemd-logind >/dev/null 2>&1 || true
sleep 1
risposta=$(busctl call org.freedesktop.login1 /org/freedesktop/login1 \
           org.freedesktop.login1.Manager CanSuspend 2>/dev/null || echo '?')
inf "logind risponde CanSuspend = ${risposta}"

# ---------------------------------------------------------------------------
# Spegnimento e riavvio: tolti anche quelli
#
#    Deciso il 2 agosto, insieme alle altre regole di sessione. Valgono le
#    stesse ragioni della sospensione (SPECIFICA.md §3.4-bis): il danno non e'
#    di chi comanda, e' di chi sta lavorando sulla macchina o la usa da un'altra
#    sessione — e uno spegnimento su una macchina remota si ripara solo andandoci
#    fisicamente davanti.
#
#    Qui non basta un file di configurazione come per la sospensione: le due
#    azioni passano da **polkit**, quindi si nega li'. Negandole, `logind`
#    risponde "no" e GNOME smette da se' di mostrare le voci, insieme a
#    `loginctl` e alle scorciatoie — che e' il punto: si toglie la capacita',
#    non si nasconde il pulsante.
#
#    Chi ha `sudo` puo' comunque spegnere, e va bene cosi': quella e'
#    amministrazione della macchina, non una sessione remota che decide per gli
#    altri.
#
#    Verifica:
#      busctl call org.freedesktop.login1 /org/freedesktop/login1 \
#             org.freedesktop.login1.Manager CanPowerOff
#    Deve rispondere "no".
# ---------------------------------------------------------------------------
log "Spegnimento e riavvio disabilitati"
sudo mkdir -p /etc/polkit-1/rules.d
sudo tee /etc/polkit-1/rules.d/49-remotix-niente-spegnimento.rules >/dev/null <<'RULES'
// Posato da REMOTIX: una sessione remota non spegne ne' riavvia la macchina.
polkit.addRule(function(action, subject) {
    if (action.id.indexOf("org.freedesktop.login1.power-off") === 0 ||
        action.id.indexOf("org.freedesktop.login1.reboot") === 0 ||
        action.id.indexOf("org.freedesktop.login1.halt") === 0) {
        return polkit.Result.NO;
    }
});
RULES
sudo systemctl restart polkit >/dev/null 2>&1 || true
sleep 1
for azione in CanPowerOff CanReboot; do
    risposta=$(busctl call org.freedesktop.login1 /org/freedesktop/login1 \
               org.freedesktop.login1.Manager "$azione" 2>/dev/null || echo '?')
    inf "logind risponde $azione = ${risposta}"
done

# ---------------------------------------------------------------------------
# Autenticazione: il servizio PAM di REMOTIX
#
#    PAM sceglie le regole in base al nome del servizio, che e' un file qui
#    dentro. Se manca, PAM ricade su /etc/pam.d/other — che su Debian nega
#    tutto — e il server rifiuta chiunque senza spiegare perche'.
#
#    Si includono i file comuni della distribuzione invece di elencare i moduli:
#    cosi' valgono le stesse regole del resto della macchina, comprese scadenze
#    e blocchi, e non si crea una seconda politica di accesso destinata a
#    divergere.
# ---------------------------------------------------------------------------
log "Servizio PAM per REMOTIX"
sudo tee /etc/pam.d/remotix >/dev/null <<'PAMD'
#%PAM-1.0
# Posato da REMOTIX: autenticazione delle connessioni RDP.
@include common-auth
@include common-account
@include common-password
@include common-session-noninteractive
PAMD
inf "creato /etc/pam.d/remotix"

# ---------------------------------------------------------------------------
# Servizio PAM per lo strumento di prova della sessione locale
#
#    Serve a `finta-sessione-locale`, che apre una sessione grafica su seat0
#    per verificare la regola di §3.4 («la sessione locale vince»). Senza una
#    sessione locale vera quella regola non si potrebbe provare: nella VM non
#    c'e' nessuno seduto davanti allo schermo.
#
#    `pam_rootok` e non `pam_permit`: root apre senza password — e lo strumento
#    root deve esserlo comunque, perche' logind lascia creare sessioni per conto
#    d'altri solo a lui — mentre a chiunque altro la password vera viene chiesta.
#    E' la stessa politica di `su` per root, e lascia il file innocuo anche se
#    resta su una macchina.
#
#    La differenza che conta rispetto al servizio `remotix` e' `common-session`,
#    quello interattivo: e' li' che vive `pam_systemd`, il modulo che registra la
#    sessione in logind, cioe' l'unica ragione per cui questo file esiste.
#
#    Sta qui perche' la VM e' la macchina di prova; nel confezionamento della
#    fase 11 non ci va.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Un secondo utente, solo per le prove
#
#    Serve a verificare che REMOTIX rifiuti chi non e' l'utente della sessione
#    che sta servendo (§3.4). Senza un secondo account la prova non si puo'
#    fare: con uno solo, «tutti quelli che entrano sono quelli giusti» e' vero
#    per caso, non per costruzione.
#
#    Password uguale al nome: e' la VM di prova, che si azzera, e la password
#    compare comunque in `prova-e2e.sh`. Nessun `sudo` per lui.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# nftables: serve a fingere che la rete cada
#
#    `prova-e2e.sh` butta via i pacchetti diretti alla porta RDP per verificare
#    che il server se ne accorga in mezzo minuto (§5.9). Va fatto DENTRO la VM:
#    bloccare dal notebook non servirebbe, perche' la connessione TCP che conta
#    e' quella fra QEMU e il server, e resterebbe viva.
# ---------------------------------------------------------------------------
log "nftables per la prova della caduta di rete"
sudo apt-get install -y --no-install-recommends nftables >/dev/null
inf "nft installato"

log "Utente estraneo per le prove di accesso"
if id estraneo >/dev/null 2>&1; then
    inf "l'utente «estraneo» c'e' gia'"
else
    sudo useradd -m -s /bin/bash estraneo
    printf 'estraneo:estraneo\n' | sudo chpasswd
    inf "creato l'utente «estraneo»"
fi

log "Servizio PAM per la prova della sessione locale"
sudo tee /etc/pam.d/remotix-prova-locale >/dev/null <<'PAMD'
#%PAM-1.0
# Posato da REMOTIX: apertura di una sessione grafica locale, solo per le prove.
auth       sufficient  pam_rootok.so
@include common-auth
@include common-account
@include common-session
PAMD
inf "creato /etc/pam.d/remotix-prova-locale"

# ---------------------------------------------------------------------------
# La sessione GNOME senza monitor
#
#    Dalla fase 5 REMOTIX avvia una sessione intera, non il solo compositore
#    (SPECIFICA.md §5.9-bis). L'unica cosa che una sessione senza schermo ha di
#    diverso e' la riga di comando della Shell, che l'unita' di GNOME non
#    prevede: la si sovrascrive qui, una volta per macchina.
#
#    Senza `--no-x11`, in questa VM Xwayland ogni tanto si porta dietro il
#    compositore (§5.6, questione aperta 8).
# ---------------------------------------------------------------------------
log "Shell di GNOME senza monitor"
sudo mkdir -p /etc/systemd/user/org.gnome.Shell@wayland.service.d
sudo tee /etc/systemd/user/org.gnome.Shell@wayland.service.d/remotix-headless.conf >/dev/null <<'CONF'
# Posato da REMOTIX: la sessione gira senza schermo.
[Service]
ExecStart=
ExecStart=/usr/bin/gnome-shell --headless --no-x11
CONF
systemctl --user daemon-reload >/dev/null 2>&1 || true
inf "gnome-shell partira' con --headless --no-x11"

# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------
log "VM di runtime pronta"
printf '
    sistema:    %s
    pacchetti:  %s installati
    disco:      %s liberi
    logind:     %s

    GNOME e'\'' installato ma NON avviato: nessun gestore di accesso grafico.
    La sessione senza monitor verra'\'' avviata da REMOTIX (fase 2 del piano).

' "$(grep -oP '(?<=PRETTY_NAME=")[^"]*' /etc/os-release)" \
  "$(dpkg -l | grep -c '^ii')" \
  "$(df -h / | tail -1 | awk '{print $4}')" \
  "$(systemctl is-active systemd-logind)"

# ---------------------------------------------------------------------------
# REMOTIX come servizio di SISTEMA — anticipo della fase 11
#
# ⛔ Non e' una comodita': e' l'unico posto in cui il server sopravvive a un
#    «Esci».  L'uscita di GNOME finisce con `exit.target` sul gestore utente,
#    che ferma `user@1000.service` per intero — e sotto quel ramo non
#    sopravvive niente.  Misurato il 4 agosto in tre cgroup diversi
#    (`session-N.scope`, `app.slice`, `background.slice`): SIGTERM in tutti e
#    tre, 250 ms dopo l'annuncio dell'uscita.  `system.slice` e' fuori tiro.
#
#    Senza questo, dopo un logout l'utente si ritrova un server spento e nessun
#    desktop — cioe' l'esatto contrario di quel che la fase 5 promette.
# ---------------------------------------------------------------------------
log "REMOTIX come servizio di sistema"
sudo tee /etc/systemd/system/remotix.service >/dev/null <<'UNITA'
[Unit]
Description=REMOTIX — server RDP per Linux
After=network.target systemd-logind.service
# ⛔ I riavvii vanno LIMITATI.  Con `Restart=on-failure` e nessun tetto, un
#    server che non riesce a prendere la porta riparte all'infinito: visto
#    salire a 33 riavvii in pochi secondi, con `pgrep` che lo trovava ora si'
#    ora no e una prova che sbagliava diagnosi per colpa di quello.  Tre
#    tentativi in un minuto, poi si arrende e lo dice.
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=nicfio
EnvironmentFile=-/etc/default/remotix
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
ExecStart=/home/nicfio/remotix --porta 3389 $REMOTIX_OPZIONI
Restart=on-failure
RestartSec=2
# ⛔ Senza questi due, PipeWire non puo' chiedere SCHED_FIFO — RLIMIT_RTPRIO
#    predefinito e' zero — e sotto carico la cattura audio perde campioni.
#    Misurato il 5 agosto 2026: REFERENCE.md R26.
LimitRTPRIO=20
LimitNICE=-11
Slice=system.slice
StandardOutput=append:/home/nicfio/remotix.log
StandardError=append:/home/nicfio/remotix.log

[Install]
WantedBy=multi-user.target
UNITA
# Il linger tiene in piedi /run/user/1000 e il bus di sessione anche senza
# sessioni aperte: senza, REMOTIX non avrebbe con chi parlare fra un
# collegamento e l'altro.
sudo loginctl enable-linger nicfio
sudo systemctl daemon-reload
sudo systemctl enable remotix.service >/dev/null 2>&1 || true
ok "remotix.service installato in system.slice, con linger acceso"
