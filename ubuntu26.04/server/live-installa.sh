#!/bin/bash
# live-installa.sh - TEST installer for a real machine booted from an Ubuntu 26.04 live image
# (Ubuntu, Kubuntu, Xubuntu, Lubuntu).  Run as root from the live terminal:
#     wget -qO- http://192.168.0.22:8830/installa.sh | sudo bash
# It does exactly what the user manual asks of the administrator (ch. 2): apt install of the .deb, then
# `systemctl enable --now remotix`.  Nothing else on the system is changed, except the two test users.
# Re-runnable.  Optional environment: SORGENTE (where the files are), PORTA (only for container tests).
set -euo pipefail
export LC_ALL=C DEBIAN_FRONTEND=noninteractive

SORGENTE=${SORGENTE:-http://192.168.0.22:8830}
PACCHETTO=remotix_1.2.0-1+ubuntu26.04_amd64.deb
UTENTI=(prova prova2)
PASSWORD=prova2026

# colours only on a terminal; questions only if the script is a file run from a terminal (not from a pipe)
if [ -t 1 ]; then B=$'\033[1m'; V=$'\033[32m'; R=$'\033[31m'; G=$'\033[33m'; N=$'\033[0m'; else B=; V=; R=; G=; N=; fi
INTERATTIVO=0; if [ -t 0 ] && [ -t 1 ]; then INTERATTIVO=1; fi

passo() { echo; echo "${B}== $* ==${N}"; }
ok()    { echo "${V}OK${N}   $*"; }
avviso(){ echo "${G}ATTENZIONE${N} $*"; }
fine()  { echo "${R}ERRORE${N} $*" >&2; exit 1; }

TMP=
pulisci() { [ -z "$TMP" ] || rm -rf "$TMP"; }
trap pulisci EXIT

controlli() {
    passo "1. Controlli iniziali"
    [ "$(id -u)" -eq 0 ] || fine "Questo programma va lanciato come amministratore. Scrivi:  wget -qO- $SORGENTE/installa.sh | sudo bash"
    ok "Sei amministratore (root)."
    local versione=
    # shellcheck disable=SC1091
    versione=$(. /etc/os-release 2>/dev/null && echo "${ID:-?} ${VERSION_ID:-?}") || versione="sconosciuto"
    if [ "$versione" = "ubuntu 26.04" ]; then
        ok "Sistema: Ubuntu 26.04."
    else
        avviso "Il sistema non e' Ubuntu 26.04 (risulta: $versione). Il pacchetto e' fatto per Ubuntu 26.04."
        if [ "$INTERATTIVO" -eq 1 ]; then
            local r=; read -r -p "Vuoi continuare lo stesso? [s/N] " r || r=n
            case "$r" in s|S|si|SI|y|Y) ;; *) fine "Interrotto su tua richiesta." ;; esac
        else
            avviso "Non posso chiedere conferma: proseguo."
        fi
    fi
    local de=()
    command -v gnome-shell >/dev/null 2>&1 && de+=("GNOME (Ubuntu)")
    { command -v startplasma-wayland >/dev/null 2>&1 || command -v plasmashell >/dev/null 2>&1; } && de+=("KDE Plasma (Kubuntu)")
    command -v xfce4-session >/dev/null 2>&1 && de+=("XFCE (Xubuntu)")
    command -v lxqt-session >/dev/null 2>&1 && de+=("LXQt (Lubuntu)")
    if [ ${#de[@]} -gt 0 ]; then ok "Desktop trovato: ${de[*]}."; else avviso "Non riconosco nessun desktop tra GNOME, KDE, XFCE, LXQt."; fi
    if wget -q --spider -T 10 -t 1 http://archive.ubuntu.com/ubuntu/ 2>/dev/null; then
        ok "La rete raggiunge l'archivio di Ubuntu."
    else
        avviso "Non riesco a raggiungere archive.ubuntu.com: se la live usa un altro archivio va bene, altrimenti controlla la rete."
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

componenti_universe() {
    # true if some apt source lists the universe component
    local t; t=$(cat /etc/apt/sources.list.d/*.sources /etc/apt/sources.list /etc/apt/sources.list.d/*.list 2>/dev/null || true)
    grep -Eq '^(Components:.*\buniverse\b|deb .*\buniverse\b)' <<<"$t"
}

prepara_apt() {
    passo "3. Preparo apt"
    if componenti_universe; then
        ok "Il componente «universe» e' gia' attivo."
    else
        avviso "Il componente «universe» non e' attivo: lo attivo (serve per il programma labwc)."
        if command -v add-apt-repository >/dev/null 2>&1 && add-apt-repository -y universe </dev/null >/dev/null 2>&1; then
            ok "«universe» attivato con add-apt-repository."
        elif [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then
            [ -e /etc/apt/sources.list.d/ubuntu.sources.prima-di-remotix ] || cp /etc/apt/sources.list.d/ubuntu.sources /etc/apt/sources.list.d/ubuntu.sources.prima-di-remotix
            sed -i -E '/^Components:/{/universe/!s/$/ universe/}' /etc/apt/sources.list.d/ubuntu.sources
            componenti_universe || fine "Non riesco ad attivare «universe». Attivalo a mano e rilancia."
            ok "«universe» aggiunto in ubuntu.sources (copia dell'originale: ubuntu.sources.prima-di-remotix)."
        else
            fine "Non riesco ad attivare «universe». Attivalo a mano e rilancia."
        fi
    fi
    echo "Aggiorno l'elenco dei pacchetti (apt-get update)..."
    apt-get -o DPkg::Lock::Timeout=180 update -qq </dev/null >"$TMP/update.log" 2>&1 || {
        tail -n 8 "$TMP/update.log" >&2
        if grep -qi lock "$TMP/update.log"; then fine "Il sistema sta gia' aggiornando, riprova tra qualche minuto."; fi
        fine "apt-get update non e' riuscito: controlla la rete."
    }
    ok "Elenco dei pacchetti aggiornato."
    local pol; pol=$(apt-cache policy labwc 2>/dev/null || true)
    if grep -q 'Candidate: [0-9]' <<<"$pol"; then ok "labwc e' disponibile."; else avviso "labwc non risulta disponibile: XFCE e LXQt non partirebbero da remoto."; fi
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
    p=$(cat /usr/share/remotix/remotix.conf /etc/remotix/remotix.conf.d/*.conf 2>/dev/null | sed -n 's/^REMOTIX_PORT=//p' | tail -n 1)
    echo "${p:-7447}"
}

# no `grep -q` after a pipe: with pipefail an early exit of grep could turn a match into a failure
in_ascolto() { [ -n "$(ss -ltn "sport = :$PORTA_REALE" 2>/dev/null | grep LISTEN || true)" ]; }

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
        if systemctl is-active --quiet remotix && in_ascolto; then break; fi
        sleep 1
    done
    systemctl is-active --quiet remotix || { journalctl -u remotix -n 15 --no-pager >&2 || true; fine "Il servizio REMOTIX non e' attivo."; }
    ok "Servizio REMOTIX attivo."
    in_ascolto || fine "Il servizio e' attivo ma la porta $PORTA_REALE non e' in ascolto."
    ok "La porta $PORTA_REALE e' in ascolto."
    if command -v ufw >/dev/null 2>&1 && [ -n "$(ufw status 2>/dev/null | grep '^Status: active' || true)" ]; then
        avviso "Il firewall ufw e' ATTIVO: da un altro dispositivo non si entra finche' non apri la porta. Non l'ho toccato. Per aprirla scrivi:  sudo ufw allow REMOTIX"
    fi
}

riepilogo() {
    local ip u
    echo; echo "${B}=====================================================${N}"
    echo "${B}   REMOTIX e' pronto. Ora usa un ALTRO dispositivo.${N}"
    echo "${B}=====================================================${N}"
    local ips; ips=$(ip -4 -o addr show scope global 2>/dev/null | awk '{split($4,a,"/"); print a[1]}' || true)
    [ -n "$ips" ] || echo "Nessun indirizzo di rete: la macchina e' collegata?"
    echo "Apri nel browser (Chrome o Firefox) uno di questi indirizzi:"
    for ip in $ips; do
        echo "     https://$ip:$PORTA_REALE"
    done
    echo "Il browser avvisera' che il certificato non e' fidato: e' normale, scegli di continuare."
    echo "Utenti di prova:   ${UTENTI[0]}  e  ${UTENTI[1]}   password: $PASSWORD"
    echo "(L'utente della live non va bene: ha lo schermo locale aperto e non entra da remoto.)"
    echo
    echo "Tre prove suggerite:"
    echo "  a) Da un altro dispositivo entra come ${UTENTI[0]}: deve comparire il desktop."
    echo "  b) Con la sessione remota aperta, sullo schermo della macchina fai «Cambia utente» ed entra come ${UTENTI[0]}:"
    echo "     la sessione remota deve chiudersi e l'accesso locale entrare al primo colpo."
    echo "  c) Esci dall'accesso locale e rientra da remoto."
    echo
    echo "Per togliere REMOTIX:  sudo apt remove remotix   (oppure  sudo apt purge remotix  per cancellare anche le impostazioni)"
}

# everything in one function, called last: bash reads a piped script line by line and apt/dpkg must not eat the rest of it
main() {
    controlli
    scarica
    prepara_apt
    installa
    crea_utenti
    avvia
    riepilogo
}

main "$@"
