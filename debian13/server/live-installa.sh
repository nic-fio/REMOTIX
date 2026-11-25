#!/bin/bash
# live-installa.sh - TEST installer for a real machine booted from a Debian 13 live image
# (13.8.0: GNOME, KDE Plasma, Xfce, LXQt).  Run as root from the live terminal:
#     wget -qO- http://192.168.0.22:8830/installa.sh | sudo bash
# It does what the user manual asks of the administrator: apt install of the .deb (apt brings what the package
# Recommends: labwc, wlr-randr, xwayland, the video drivers...), then `systemctl enable --now remotix`.
# It STOPS with a clear message when the network is missing (apt needs the Debian archive).
# Nothing else on the system is changed, except the two test users (and, only if the file chiave.pub is served, an
# ssh key for root: see accesso_tablet).
# Re-runnable.  Optional environment: SORGENTE (where the files are), PORTA (only for container tests).
set -euo pipefail
export LC_ALL=C DEBIAN_FRONTEND=noninteractive

SORGENTE=${SORGENTE:-http://192.168.0.22:8830}
PACCHETTO=remotix_1.2.0-1+deb13_amd64.deb   # name of the .deb served by SORGENTE (with its .sha256): change it here
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
PORTA_REALE=
pulisci() {
    [ -n "$TMP" ] || return 0
    if [ "$RIUSCITO" -eq 1 ] && [ "$AVVISI" -eq 0 ]; then
        rm -rf "$TMP"
    else
        echo "I file e i registri di questa prova sono rimasti in: $TMP" >&2
    fi
}
trap pulisci EXIT

controlli() {
    passo "1. Controlli iniziali"
    [ "$(id -u)" -eq 0 ] || fine "Questo programma va lanciato come amministratore. Scrivi:  wget -qO- $SORGENTE/installa.sh | sudo bash"
    ok "Sei amministratore (root)."
    local versione=
    # shellcheck disable=SC1091
    versione=$(. /etc/os-release 2>/dev/null && echo "${ID:-?} ${VERSION_ID:-?}") || versione="sconosciuto"
    if [ "$versione" = "debian 13" ]; then
        ok "Sistema: Debian 13."
    else
        avviso "Il sistema non e' Debian 13 (risulta: $versione). Il pacchetto e' fatto per Debian 13."
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
    # the network is needed twice: the file server above and the Debian archive (apt installs labwc and the rest from it)
    if [ -z "$(ip -4 route show default 2>/dev/null || true)" ]; then
        fine "Manca la rete: nessuna strada verso l'esterno (nessuna rotta di default). Collega la macchina alla rete e rilancia."
    fi
    if wget -q --spider -T 10 -t 1 http://deb.debian.org/debian/ 2>/dev/null; then
        ok "La rete raggiunge l'archivio di Debian."
    else
        fine "Non riesco a raggiungere deb.debian.org: senza la rete apt non puo' installare labwc e le altre parti del programma. Controlla la rete e rilancia."
    fi
}

scarica() {
    passo "2. Scarico il pacchetto e controllo che sia integro"
    TMP=$(mktemp -d /var/tmp/remotix-live.XXXXXX)
    chmod 755 "$TMP"   # apt reads the file as an unprivileged user
    wget -q -T 20 -t 2 -O "$TMP/$PACCHETTO" "$SORGENTE/$PACCHETTO" \
        || fine "Non riesco a scaricare il pacchetto da $SORGENTE. Il server di sviluppo e' acceso? E' nella stessa rete? Controlla l'indirizzo."
    wget -q -T 20 -t 2 -O "$TMP/$PACCHETTO.sha256" "$SORGENTE/$PACCHETTO.sha256" \
        || fine "Non riesco a scaricare il file di controllo ($PACCHETTO.sha256) da $SORGENTE."
    local atteso reale
    atteso=$(awk 'NR==1{print $1}' "$TMP/$PACCHETTO.sha256")
    reale=$(sha256sum "$TMP/$PACCHETTO" | awk '{print $1}')
    if [ -z "$atteso" ] || [ "$atteso" != "$reale" ]; then
        fine "Il pacchetto scaricato NON e' quello atteso (controllo sha256 fallito). Non installo nulla."
    fi
    ok "Pacchetto scaricato e verificato (sha256 uguale)."
}

prepara_apt() {
    passo "3. Preparo apt"
    echo "Aggiorno l'elenco dei pacchetti (apt-get update)..."
    apt-get -o DPkg::Lock::Timeout=180 update -qq </dev/null >"$TMP/update.log" 2>&1 || {
        tail -n 8 "$TMP/update.log" >&2
        if grep -qi lock "$TMP/update.log"; then fine "Il sistema sta gia' aggiornando, riprova tra qualche minuto."; fi
        fine "apt-get update non e' riuscito: manca la rete o l'archivio non risponde. Controlla la rete e rilancia."
    }
    ok "Elenco dei pacchetti aggiornato."
    local pol; pol=$(apt-cache policy labwc 2>/dev/null || true)
    if grep -q 'Candidate: [0-9]' <<<"$pol"; then ok "labwc e' disponibile negli archivi."; else avviso "labwc non risulta disponibile negli archivi: XFCE e LXQt non partirebbero da remoto (controlla /etc/apt/sources.list: serve «main»)."; fi
}

installa() {
    passo "4. Installo REMOTIX (con tutto cio' che raccomanda)"
    echo "Puo' richiedere qualche minuto..."
    if apt-get -o DPkg::Lock::Timeout=180 -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold install -y --reinstall "$TMP/$PACCHETTO" </dev/null >"$TMP/install.log" 2>&1; then
        ok "REMOTIX installato ($(dpkg-query -W -f='${Version}' remotix))."
        grep -E 'remotix: ' "$TMP/install.log" | sed 's/^/     /' || true
    else
        tail -n 15 "$TMP/install.log" >&2
        if grep -qi lock "$TMP/install.log"; then fine "Il sistema sta gia' aggiornando, riprova tra qualche minuto."; fi
        fine "L'installazione non e' riuscita (vedi le ultime righe qui sopra)."
    fi
    # labwc & co. are Recommends: apt brings them unless the live has apt told not to; check, and bring them by hand if missing
    local m=() p
    for p in labwc wlr-randr xwayland fonts-dejavu-core; do
        dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -q '^install ok installed' || m+=("$p")
    done
    if [ ${#m[@]} -gt 0 ]; then
        avviso "apt non ha portato: ${m[*]}. Li installo ora."
        apt-get -o DPkg::Lock::Timeout=180 install -y "${m[@]}" </dev/null >"$TMP/raccomandati.log" 2>&1 \
            || { tail -n 10 "$TMP/raccomandati.log" >&2; fine "Non riesco a installare ${m[*]} (manca la rete?). Senza labwc XFCE e LXQt non partono da remoto."; }
        ok "Installati: ${m[*]}."
    else
        ok "labwc, wlr-randr, xwayland e il carattere di base sono presenti."
    fi
}

crea_utenti() {
    passo "5. Utenti di prova"
    local u
    for u in "${UTENTI[@]}"; do
        if id "$u" >/dev/null 2>&1; then
            ok "L'utente $u esiste gia': non lo tocco (nemmeno la password)."
        else
            useradd -m -s /bin/bash "$u" || fine "Non riesco a creare l'utente $u."
            echo "$u:$PASSWORD" | chpasswd || fine "Non riesco a impostare la password di $u."
            ok "Creato l'utente $u (password $PASSWORD)."
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

avvia() {
    passo "6. Avvio il servizio"
    if [ -n "${PORTA:-}" ]; then
        # container tests only: every box needs its own port
        avviso "Porta scelta da te: $PORTA (solo per le prove nei contenitori)."
        mkdir -p /etc/remotix/remotix.conf.d
        echo "REMOTIX_PORT=$PORTA" > /etc/remotix/remotix.conf.d/10-box-port.conf
    fi
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
    if command -v ufw >/dev/null 2>&1 && [ -n "$(ufw status 2>/dev/null | grep '^Status: active' || true)" ]; then
        avviso "Il firewall ufw e' ATTIVO: da un altro dispositivo non si entra finche' non apri la porta. Non l'ho toccato. Per aprirla scrivi:  sudo ufw allow REMOTIX (profilo del pacchetto, TCP e UDP)"
    fi
}

prova_codifica() {
    passo "7. Prova di codifica sulla scheda video"
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
    passo "Accesso per chi segue la prova dal tablet (facoltativo)"
    {
        install -d -m 700 /root/.ssh
        touch /root/.ssh/authorized_keys
        chmod 600 /root/.ssh/authorized_keys
        local riga
        riga=$(awk 'NR==1' "$chiave")
        grep -qxF "$riga" /root/.ssh/authorized_keys || echo "$riga" >>/root/.ssh/authorized_keys
        if ! systemctl cat ssh >/dev/null 2>&1; then
            apt-get -o DPkg::Lock::Timeout=180 install -y openssh-server </dev/null >"$TMP/ssh.log" 2>&1
        fi
        systemctl start ssh
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
    echo "(L'utente della live, user, non va bene da remoto: ha lo schermo locale aperto e non entra.)"
    echo
    echo "Tre prove suggerite:"
    echo "  a) Da un altro dispositivo entra come ${UTENTI[0]}: deve comparire il desktop."
    echo "  b) Con il desktop remoto aperto, sullo schermo della macchina fai «Cambia utente» ed entra come ${UTENTI[0]}:"
    echo "     il desktop remoto deve chiudersi e l'accesso locale arrivare al desktop al primo colpo."
    echo "  c) Con ${UTENTI[0]} ancora dentro in locale, riprova da remoto come ${UTENTI[0]}: deve essere rifiutato"
    echo "     («gia' connesso in locale»). Poi esci dall'accesso locale e rientra da remoto: deve tornare il desktop."
    echo
    echo "Per togliere REMOTIX:  sudo apt remove remotix   (oppure  sudo apt purge remotix  per cancellare anche le impostazioni)"
}

# everything in one function, called last: bash reads a piped script line by line and apt/dpkg must not eat the rest of it
main() {
    controlli
    scarica
    prepara_apt
    accesso_tablet
    installa
    crea_utenti
    avvia
    prova_codifica
    riepilogo
    RIUSCITO=1
}

main "$@"
