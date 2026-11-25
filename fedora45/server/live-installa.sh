#!/bin/bash
# live-installa.sh - TEST installer for a real machine booted from a Fedora 45 live image
# (Workstation/GNOME, KDE, Xfce, LXQt).  Run as root from the live terminal:
#     curl -fsS http://192.168.0.22:8830/installa.sh | sudo bash
# It does what the user manual asks of the administrator: the video codecs from RPM Fusion, dnf install of the .rpm,
# the firewall service (run time only: it is a live), then `systemctl enable --now remotix`.
# Nothing else on the system is changed, except the two test users and, only if the tablet serves a chiave.pub, root's ssh access.
# Re-runnable.  Optional environment: SORGENTE (where the files are).
set -euo pipefail
export LC_ALL=C

SORGENTE=${SORGENTE:-http://192.168.0.22:8830}
PACCHETTO=remotix-1.2.0-1.fc45.x86_64.rpm
UTENTI=(prova prova2)
PASSWORD=prova2026

# colours only on a terminal; questions only if the script is a file run from a terminal (not from a pipe)
if [ -t 1 ]; then B=$'\033[1m'; V=$'\033[32m'; R=$'\033[31m'; G=$'\033[33m'; N=$'\033[0m'; else B=; V=; R=; G=; N=; fi
INTERATTIVO=0; if [ -t 0 ] && [ -t 1 ]; then INTERATTIVO=1; fi

passo() { echo; echo "${B}== $* ==${N}"; }
ok()    { echo "${V}OK${N}   $*"; }
avviso(){ AVVISI=1; echo "${G}ATTENZIONE${N} $*"; }
fine()  { echo "${R}ERRORE${N} $*" >&2; exit 1; }

# TMP is removed only if everything succeeded and no warning was given: otherwise the logs in it are needed
TMP=
RIUSCITO=0
AVVISI=0
CODIFICA_FALLITA=0
SILENZIO=0       # 1 = dnf_codec does not warn (the caller has a second attempt)
pulisci() {
    [ -n "$TMP" ] || return 0
    if [ "$RIUSCITO" -eq 1 ] && [ "$AVVISI" -eq 0 ]; then
        rm -rf "$TMP"
    else
        echo "I file e i registri di questa prova sono rimasti in: $TMP" >&2
    fi
}
trap pulisci EXIT

SCHEDE=()        # one line per render node: "node  pci  driver"
DRIVER_SCHEDE=   # the drivers, space separated
PORTA_REALE=

controlli() {
    passo "1. Controlli iniziali"
    [ "$(id -u)" -eq 0 ] || fine "Questo programma va lanciato come amministratore. Scrivi:  curl -fsS $SORGENTE/installa.sh | sudo bash"
    ok "Sei amministratore (root)."
    local versione=
    # shellcheck disable=SC1091
    versione=$(. /etc/os-release 2>/dev/null && echo "${ID:-?} ${VERSION_ID:-?}") || versione="sconosciuto"
    if [ "$versione" = "fedora 45" ]; then
        ok "Sistema: Fedora 45."
    else
        avviso "Il sistema non e' Fedora 45 (risulta: $versione). Il pacchetto e' fatto per Fedora 45."
        if [ "$INTERATTIVO" -eq 1 ]; then
            local r=; read -r -p "Vuoi continuare lo stesso? [s/N] " r || r=n
            case "$r" in s|S|si|SI|y|Y) ;; *) fine "Interrotto su tua richiesta." ;; esac
        else
            avviso "Non posso chiedere conferma: proseguo."
        fi
    fi
    local de=()
    command -v gnome-shell >/dev/null 2>&1 && de+=("GNOME")
    { command -v startplasma-wayland >/dev/null 2>&1 || command -v plasmashell >/dev/null 2>&1; } && de+=("KDE Plasma")
    command -v xfce4-session >/dev/null 2>&1 && de+=("XFCE")
    command -v lxqt-session >/dev/null 2>&1 && de+=("LXQt")
    if [ ${#de[@]} -gt 0 ]; then ok "Desktop trovato: ${de[*]}."; else avviso "Non riconosco nessun desktop tra GNOME, KDE, XFCE, LXQt."; fi
    if curl -fsS -o /dev/null -m 15 https://mirrors.fedoraproject.org/ 2>/dev/null; then
        ok "La rete raggiunge i server di Fedora."
    else
        avviso "Non riesco a raggiungere mirrors.fedoraproject.org: controlla la rete, altrimenti dnf non scarichera' nulla."
    fi
    local se=
    se=$(getenforce 2>/dev/null || true)
    if [ "$se" = "Enforcing" ]; then
        ok "SELinux: Enforcing."
    else
        avviso "SELinux non e' in modalita' Enforcing (risulta: ${se:-sconosciuto}). La prova sarebbe diversa da quella vera."
    fi
    # the video cards: REMOTIX encodes only on the card
    local n nome pci drv
    for n in /sys/class/drm/renderD*; do
        [ -e "$n" ] || continue
        nome=$(basename "$n")
        pci=$(basename "$(readlink -f "$n/device" 2>/dev/null || true)")
        drv=$(basename "$(readlink "$n/device/driver" 2>/dev/null || true)")
        [ -n "$drv" ] || drv="sconosciuto"
        SCHEDE+=("$nome  $pci  $drv")
        DRIVER_SCHEDE="$DRIVER_SCHEDE $drv"
    done
    if [ ${#SCHEDE[@]} -eq 0 ]; then
        fine "Questa macchina non ha nessuna scheda video utilizzabile (nessun renderD* in /sys/class/drm): il pacchetto si rifiuterebbe di installarsi."
    fi
    ok "Schede video trovate (nodo, indirizzo PCI, driver):"
    local s
    for s in "${SCHEDE[@]}"; do echo "     $s"; done
}

scarica() {
    passo "2. Scarico il pacchetto e controllo che sia integro"
    TMP=$(mktemp -d /var/tmp/remotix-live.XXXXXX)
    chmod 755 "$TMP"
    curl -fsS -m 300 --retry 2 -o "$TMP/$PACCHETTO" "$SORGENTE/$PACCHETTO" \
        || fine "Non riesco a scaricare il pacchetto da $SORGENTE. Il tablet sta servendo i file? E' nella stessa rete? Controlla l'indirizzo."
    curl -fsS -m 60 --retry 2 -o "$TMP/$PACCHETTO.sha256" "$SORGENTE/$PACCHETTO.sha256" \
        || fine "Non riesco a scaricare il file di controllo ($PACCHETTO.sha256) da $SORGENTE."
    local atteso reale
    atteso=$(awk 'NR==1{print $1}' "$TMP/$PACCHETTO.sha256")
    reale=$(sha256sum "$TMP/$PACCHETTO" | awk '{print $1}')
    if [ -z "$atteso" ] || [ "$atteso" != "$reale" ]; then
        fine "Il pacchetto scaricato NON e' quello atteso (controllo sha256 fallito). Non installo nulla."
    fi
    ok "Pacchetto scaricato e verificato (sha256 uguale)."
}

# runs one dnf command with its output in a log; a failure is a warning with the last lines, never blocks
dnf_codec() {
    local nome=$1; shift
    local log="$TMP/codec-$nome.log"
    if "$@" </dev/null >"$log" 2>&1; then
        return 0
    fi
    if [ "$SILENZIO" -eq 0 ]; then
        avviso "Non e' riuscito: $*  (ultime righe del registro, che e' in $log)"
        tail -n 8 "$log" | sed 's/^/     /' >&2 || true
    fi
    return 1
}

codec() {
    passo "4. Codec video (da RPM Fusion, li installa l'amministratore)"
    echo "Puo' richiedere qualche minuto..."
    if rpm -q rpmfusion-free-release >/dev/null 2>&1; then
        ok "RPM Fusion (free) e' gia' attivo."
    elif dnf_codec rpmfusion-free dnf install -y https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-45.noarch.rpm; then
        ok "RPM Fusion (free) attivato."
    fi
    local p
    for p in mesa-va-drivers mesa-vulkan-drivers; do
        if rpm -q "$p-freeworld" >/dev/null 2>&1; then
            ok "$p-freeworld e' gia' installato."
        elif rpm -q "$p" >/dev/null 2>&1; then
            if dnf_codec "$p" dnf swap -y "$p" "$p-freeworld"; then ok "$p sostituito con $p-freeworld."; fi
        else
            if dnf_codec "$p" dnf install -y "$p-freeworld"; then ok "$p-freeworld installato."; fi
        fi
    done
    case " $DRIVER_SCHEDE " in
        *" i915 "*|*" xe "*)
            echo "C'e' una scheda Intel: serve anche il driver intel-media-driver."
            if rpm -q rpmfusion-nonfree-release >/dev/null 2>&1; then
                ok "RPM Fusion (nonfree) e' gia' attivo."
            elif dnf_codec rpmfusion-nonfree dnf install -y https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-45.noarch.rpm; then
                ok "RPM Fusion (nonfree) attivato."
            fi
            if rpm -q intel-media-driver >/dev/null 2>&1; then
                ok "intel-media-driver e' gia' installato."
            else
                local fatto=0
                # the first attempt is silent: if dnf wants to replace libva-intel-media-driver, the second one (--allowerasing) decides
                SILENZIO=1
                dnf_codec intel-media-driver dnf install -y intel-media-driver && fatto=1
                SILENZIO=0
                [ "$fatto" -eq 1 ] || { dnf_codec intel-media-driver-erasing dnf install -y --allowerasing intel-media-driver && fatto=1; }
                if [ "$fatto" -eq 1 ]; then ok "intel-media-driver installato."; fi
            fi
            ;;
    esac
}

installa() {
    passo "5. Installo REMOTIX (con tutto cio' che raccomanda)"
    echo "Puo' richiedere qualche minuto..."
    local comando=install nuova installata
    nuova=${PACCHETTO#remotix-}; nuova=${nuova%.x86_64.rpm}
    installata=$(rpm -q --qf '%{VERSION}-%{RELEASE}' remotix 2>/dev/null || true)
    [ "$installata" != "$nuova" ] || comando=reinstall
    if dnf "$comando" -y "$TMP/$PACCHETTO" </dev/null >"$TMP/install.log" 2>&1; then
        ok "REMOTIX installato ($(rpm -q remotix))."
        grep -E '(^|[[:space:]])remotix: ' "$TMP/install.log" | sed -E 's/^(>>>)?[[:space:]]*/     /' || true
    else
        tail -n 15 "$TMP/install.log" >&2
        fine "L'installazione non e' riuscita (vedi le ultime righe qui sopra)."
    fi
}

crea_utenti() {
    passo "6. Utenti di prova"
    local u
    for u in "${UTENTI[@]}"; do
        if id "$u" >/dev/null 2>&1; then
            ok "L'utente $u esiste gia': non lo tocco (nemmeno la password)."
        else
            useradd -m -s /bin/bash "$u" || fine "Non riesco a creare l'utente $u."
            echo "$u:$PASSWORD" | chpasswd || fine "Non riesco a impostare la password di $u."
            ok "Creato l'utente $u (password $PASSWORD)."
            if [ "$u" = "${UTENTI[0]}" ]; then
                usermod -aG wheel "$u" || fine "Non riesco ad aggiungere $u al gruppo wheel."
                ok "$u e' anche amministratore (gruppo wheel)."
            fi
        fi
    done
}

porta_servizio() {
    # the port as the service will see it: package default, then the files in /etc (last one wins)
    local p
    p=$(cat /usr/share/remotix/remotix.conf /etc/remotix/remotix.conf.d/*.conf 2>/dev/null | sed -n 's/^REMOTIX_PORT=//p' | tail -n 1 || true)
    echo "${p:-7447}"
}

# no `grep -q` after a pipe: with pipefail an early exit of grep could turn a match into a failure
in_ascolto_tcp() { [ -n "$(ss -ltn "sport = :$PORTA_REALE" 2>/dev/null | grep LISTEN || true)" ]; }
# UDP sockets have no LISTEN state: any row after the header is a bound socket
in_ascolto_udp() { [ -n "$(ss -lun "sport = :$PORTA_REALE" 2>/dev/null | tail -n +2 || true)" ]; }

firewall() {
    passo "7. Firewall"
    if [ "$(firewall-cmd --state 2>/dev/null || true)" = "running" ]; then
        if ! firewall-cmd --add-service=remotix >"$TMP/firewall.log" 2>&1; then
            firewall-cmd --reload >>"$TMP/firewall.log" 2>&1 || true
            firewall-cmd --add-service=remotix >>"$TMP/firewall.log" 2>&1 \
                || { tail -n 8 "$TMP/firewall.log" >&2; fine "Non riesco ad aprire il servizio remotix nel firewall (vedi sopra)."; }
        fi
        ok "Firewalld e' attivo: ho aperto il servizio «remotix» solo ora, a runtime (alla riaccensione sparisce: e' una live)."
    else
        ok "Nessun firewall attivo."
    fi
}

avvia() {
    passo "8. Avvio il servizio"
    systemctl enable --now remotix >"$TMP/avvio.log" 2>&1 || { cat "$TMP/avvio.log" >&2; fine "Il servizio non parte: guarda  journalctl -u remotix -n 30"; }
    # already running before (re-run): restart so the port and the new files are in use
    systemctl restart remotix || fine "Il servizio non riparte: guarda  journalctl -u remotix -n 30"
    PORTA_REALE=$(porta_servizio)
    local i
    for i in $(seq 1 20); do
        if systemctl is-active --quiet remotix && in_ascolto_tcp && in_ascolto_udp; then break; fi
        sleep 1
    done
    systemctl is-active --quiet remotix || { journalctl -u remotix -n 15 --no-pager >&2 || true; fine "Il servizio REMOTIX non e' attivo."; }
    ok "Servizio REMOTIX attivo."
    in_ascolto_tcp || fine "Il servizio e' attivo ma la porta TCP $PORTA_REALE (la pagina) non e' in ascolto."
    ok "La porta TCP $PORTA_REALE e' in ascolto."
    in_ascolto_udp || fine "Il servizio e' attivo ma la porta UDP $PORTA_REALE (QUIC, il video) non e' in ascolto."
    ok "La porta UDP $PORTA_REALE e' in ascolto."
}

prova_codifica() {
    passo "9. Prova di codifica sulla scheda video"
    local codice=0
    timeout 30 /usr/libexec/remotix/remotix --encoding-test h264 >"$TMP/codifica.log" 2>&1 </dev/null || codice=$?
    if [ "$codice" -eq 0 ]; then
        ok "La scheda video codifica."
    else
        CODIFICA_FALLITA=1
        tail -n 8 "$TMP/codifica.log" | sed 's/^/     /' >&2 || true
        avviso "LA SCHEDA NON CODIFICA: da remoto non si vedra' il desktop (codice di uscita $codice, registro in $TMP/codifica.log)."
    fi
}

# only for whoever follows the test from the tablet; nothing here ever blocks
accesso_tablet() {
    local chiave="$TMP/chiave.pub"
    curl -fsS -m 10 -o "$chiave" "$SORGENTE/chiave.pub" 2>/dev/null || return 0
    [ -s "$chiave" ] || return 0
    passo "3. Accesso per chi segue la prova dal tablet"
    {
        install -d -m 700 /root/.ssh
        touch /root/.ssh/authorized_keys
        chmod 600 /root/.ssh/authorized_keys
        local riga
        riga=$(awk 'NR==1' "$chiave")
        grep -qxF "$riga" /root/.ssh/authorized_keys || echo "$riga" >>/root/.ssh/authorized_keys
        if command -v restorecon >/dev/null 2>&1; then restorecon -R /root/.ssh || true; fi
        if ! systemctl cat sshd >/dev/null 2>&1; then
            dnf install -y openssh-server </dev/null >"$TMP/ssh.log" 2>&1
        fi
        systemctl start sshd
    } || { avviso "Non sono riuscito ad aprire l'accesso ssh per il tablet (non e' grave: la prova continua)."; return 0; }
    avviso "Ho aperto l'accesso ssh per root con la chiave del tablet: serve solo a leggere i registri di questa prova."
}

riepilogo() {
    local ip
    echo; echo "${B}=====================================================${N}"
    if [ "$CODIFICA_FALLITA" -eq 1 ]; then
        echo "${R}${B}   REMOTIX e' installato ma la scheda non codifica: da remoto non si vedra' il desktop.${N}"
    else
        echo "${B}   REMOTIX e' pronto. Ora usa un ALTRO dispositivo.${N}"
    fi
    echo "${B}=====================================================${N}"
    local ips; ips=$(ip -4 -o addr show scope global 2>/dev/null | awk '{split($4,a,"/"); print a[1]}' || true)
    if [ -n "$ips" ]; then
        echo "Apri nel browser (Chrome o Firefox) uno di questi indirizzi:"
        for ip in $ips; do
            echo "     https://$ip:$PORTA_REALE"
        done
    else
        echo "Nessun indirizzo di rete: la macchina e' collegata?"
    fi
    echo "Il browser avvisera' che il certificato non e' fidato: e' normale, scegli di continuare."
    echo "Utenti di prova:   ${UTENTI[0]}  e  ${UTENTI[1]}   password: $PASSWORD"
    echo "(L'utente della live, liveuser, non va bene da remoto: ha lo schermo locale aperto e non entra.)"
    echo
    echo "Tre prove suggerite:"
    echo "  a) Da un altro dispositivo entra come ${UTENTI[0]}: deve comparire il desktop."
    echo "  b) Con il desktop remoto aperto, sullo schermo della macchina fai «Cambia utente» ed entra come ${UTENTI[0]}:"
    echo "     il desktop remoto deve chiudersi e l'accesso locale arrivare al desktop al primo colpo."
    echo "  c) Con ${UTENTI[0]} ancora dentro in locale, riprova da remoto come ${UTENTI[0]}: deve essere rifiutato"
    echo "     («gia' connesso in locale»). Poi esci dall'accesso locale e rientra da remoto: deve tornare il desktop."
    echo
    echo "Per togliere REMOTIX:  sudo dnf remove remotix"
}

# everything in one function, called last: bash reads a piped script line by line and dnf must not eat the rest of it
main() {
    controlli
    scarica
    accesso_tablet
    codec
    installa
    crea_utenti
    firewall
    avvia
    prova_codifica
    riepilogo
    RIUSCITO=1
}

main "$@"
