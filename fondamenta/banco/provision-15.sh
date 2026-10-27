#!/bin/bash
#
# provision-15.sh — rimette in piedi il server per REMOTIX 1.5 dopo un riavvio.
#
# Va lanciato COME ROOT, via sudo (l'account non ha password):
#
#   echo | sudo -S -p "" bash /media/REMOTIX-15/repo/fondamenta/banco/provision-15.sh
#   echo | sudo -S -p "" env REMOTIX_SENZA_BROWSER=1 bash .../provision-15.sh   salta Firefox e Chrome
#
# Nasce da `provision-server.sh` (la macchina di runtime sul ferro), ma e' piu'
# piccolo: qui non c'e' GNOME headless ne' la iGPU della 1.0 originale.  Serve a
# compilare la 1.0 nel contenitore, costruire i box di test e far girare la
# suite (PIANO.md, passo 0).
#
# ⚠ IL ROOTFS DEL SERVER VIVE IN RAM e si azzera a ogni riavvio: dopo ogni
#   riavvio questo script va rieseguito.  I dati veri stanno su `/media`
#   (disco): la cache di apt, l'archivio di podman, il repository.  Per questo
#   la seconda volta non scarica niente e costa secondi.
#
# ⛔ Niente file grandi in `/`, `/tmp`, `~`: sono RAM e non vanno in swap.
#    Tutto quel che pesa sta in `/media/REMOTIX-15`.
#
# ⭐ RILANCIABILE SENZA DANNI: ogni passo controlla prima e riscrive solo quel
#    che manca o e' diverso.
set -euo pipefail
export LC_ALL=C   # niente avvisi di locale da apt/perl: il server non ha it_IT

BASE=/media/REMOTIX-15
LINK=/media/REMOTIX
CACHE_APT="$BASE/cache/apt"
CACHE_APT_HOST="$BASE/cache/apt-host"
# Root, e via sudo: da root "vero" la storage.conf dell'utente finirebbe in /root.
if [ "$(id -u)" -ne 0 ]; then
    echo "NO  va lanciato come root: echo | sudo -S -p \"\" bash $0" >&2
    exit 1
fi
if [ -z "${SUDO_USER:-}" ] || [ "$SUDO_USER" = root ]; then
    echo "NO  va lanciato via sudo da un utente (serve SUDO_USER): echo | sudo -S -p \"\" bash $0" >&2
    exit 1
fi
UTENTE=$SUDO_USER
CASA=$(getent passwd "$UTENTE" | cut -d: -f6)
UID_UTENTE=$(id -u "$UTENTE")

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }


# ⚠ Il disco deve esserci: senza, ogni `mkdir` qui sotto scriverebbe nella RAM
#   del rootfs e riempirebbe proprio quel che si vuole proteggere.
if ! mountpoint -q /media && [ "$(df --output=source /media | tail -1)" = "$(df --output=source / | tail -1)" ]; then
    ko "/media non e' un disco a parte: mi fermo (scriverei nella RAM)"
    exit 1
fi
if [ ! -d "$BASE" ]; then
    ko "$BASE non esiste: il passo 1 del PIANO (disposizione su disco) non e' stato fatto"
    exit 1
fi

# ---------------------------------------------------------------------------
# 1. Le cartelle su disco e il link /media/REMOTIX
#
# ⭐ Gli script della 1.0 cercano tutto in `/media/REMOTIX/...`: il link fa
#    finire quei percorsi in `/media/REMOTIX-15`.
# ---------------------------------------------------------------------------
log "Cartelle su $BASE e link $LINK"
for d in cache/apt/partial cache/apt-host rete11 misure tmp podman/root podman/user; do
    mkdir -p "$BASE/$d" 2>/dev/null || mkdir -p "$BASE/$d"
done
chown "$UTENTE:$UTENTE" "$BASE/cache" "$BASE/cache/apt-host" "$BASE/rete11" "$BASE/misure" "$BASE/tmp" 2>/dev/null || true
chmod 700 "$BASE/podman/user"
chown "$UTENTE:$UTENTE" "$BASE/podman/user"
if [ -L "$LINK" ] && [ "$(readlink "$LINK")" = "$BASE" ]; then
    ok "$LINK -> $BASE gia' c'e'"
elif [ -e "$LINK" ] && [ ! -L "$LINK" ]; then
    ko "$LINK esiste ed e' una cartella vera: non la tocco"
    exit 1
else
    ln -sfn "$BASE" "$LINK"
    ok "$LINK -> $BASE"
fi

# ---------------------------------------------------------------------------
# 2. La cache di apt su /media
# ---------------------------------------------------------------------------
log "Cache dei pacchetti su $CACHE_APT"
sh -c "printf 'Dir::Cache::archives \"%s\";\n' '$CACHE_APT' > /etc/apt/apt.conf.d/99-remotix-cache"
ok "i .deb scaricati sopravvivono al riavvio"

# ---------------------------------------------------------------------------
# 3. L'archivio di podman, fuori dalla RAM
#
# ⛔ Senza questo le immagini (gigabyte) andrebbero nel rootfs e il server
#    finirebbe la memoria: e' il motivo del passo 0.  Due file: uno per
#    podman come root (`sudo podman`, che usano i box) e uno per l'utente
#    (che compila nel contenitore).
# ---------------------------------------------------------------------------
scrivi_storage() # $1 = file, $2 = runroot, $3 = graphroot, $4 = "root" o "utente"
{
    local nuovo
    nuovo=$(printf '[storage]\ndriver = "overlay"\nrunroot = "%s"\ngraphroot = "%s"\n' "$2" "$3")
    if [ -f "$1" ] && [ "$(cat "$1")" = "$nuovo" ]; then
        ok "$1 gia' a posto"
        return
    fi
    if [ "$4" = root ]; then
        mkdir -p "$(dirname "$1")"
        printf '%s\n' "$nuovo" > "$1"
    else
        mkdir -p "$(dirname "$1")"
        printf '%s\n' "$nuovo" > "$1"
        chown "$UTENTE:$UTENTE" "$(dirname "$1")" "$1" 2>/dev/null || true
    fi
    ok "scritto $1"
}
log "storage.conf di podman (root e utente)"
scrivi_storage /etc/containers/storage.conf /run/containers/storage "$BASE/podman/root" root
scrivi_storage "$CASA/.config/containers/storage.conf" "/run/user/$UID_UTENTE/containers" "$BASE/podman/user" utente

# ---------------------------------------------------------------------------
# 4. I pacchetti dell'host
# ---------------------------------------------------------------------------
PKGS=(
    # per compilare nel contenitore e per muovere il repository
    git podman make gcc pkg-config rsync
    # la rete dei container senza privilegi
    uidmap slirp4netns passt netavark aardvark-dns
    # podman --init (il contenitore di compilazione di verifica-rami e i test root): senza, «catatonit: executable file
    # not found» e la verifica della rete va 1 PASS / 68 FAIL in 16 s (27 ott 2026, dopo un riavvio)
    catatonit
    # la suite: i banchi in Python (immagini, matematica) e l'ambiente isolato
    python3-venv python3-pil python3-numpy python3-xlib wlr-randr libpulse0 pipewire pipewire-pulse wireplumber
    # la suite (F-014C/D, F-015C): wl-copy/wl-paste fuori dal browser, tasti (wtype), focus (wlrctl),
    # il compositore senza schermo (labwc, di 15-compositors.sh)
    wl-clipboard xclip wtype wlrctl labwc
    # controllo del codice: shellcheck (SC2154 trova i nomi tradotti a meta') e pyflakes
    shellcheck pyflakes3
    # il banco 30-perf: carico per motore della GPU Intel (intel_gpu_top)
    intel-gpu-tools
    # Firefox (il client dei banchi) decodifica H.264/HEVC con libavcodec: senza, ogni login dice «nothing in common»
    # (26 ott 2026, dopo un riavvio: prima c era perché installato a mano nel sistema live)
    libavcodec61
    # ...e la decodifica IN HARDWARE dei client (Radeon: radeonsi via VA-API): senza, i 6 Firefox del 30-perf
    # decodificano in CPU (13 core a 6 utenti) e la misura diventa del client, non del prodotto (26 ott 2026)
    mesa-va-drivers vainfo zstd
    # il qemu estratto in strumenti/qemu (VM Alma per SELinux) vuole libnl-3 dall'host (26 ott 2026, dopo un riavvio)
    libnl-3-200
    # i modelli locali (llama-server -dev Vulkan0 sulla Radeon): senza RADV vedono solo la CPU
    mesa-vulkan-drivers
    # per scaricare e per la chiave del repository di Chrome
    curl ca-certificates gnupg
)

log "Pacchetti dell'host"
MANCANTI=()
for p in "${PKGS[@]}"; do
    dpkg -s "$p" >/dev/null 2>&1 || MANCANTI+=("$p")
done
if [ ${#MANCANTI[@]} -gt 0 ]; then
    inf "mancanti: ${MANCANTI[*]}"
    apt-get update -qq
    env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends "${MANCANTI[@]}"
    ok "installati"
else
    ok "gia' presenti (${#PKGS[@]} pacchetti)"
fi

# ---------------------------------------------------------------------------
# 5. Firefox ESR e Chrome sull'host
#
# ⭐ I box di test montano il Firefox dell'HOST (`11-start.sh build` copia il .deb
#    da `cache/apt-host`); il .deb lo procura `benches/11-boxes/11-assemble-product.sh`.
#    Qui si installa sull'host quel .deb stesso, cosi' host e box hanno lo
#    stesso Firefox.  Chrome viene dal repository di Google.
#
# ⚠ Sono scaricamenti da 70-110 MB e un'installazione: con una misura altrui in
#    corso si salta con REMOTIX_SENZA_BROWSER=1.
# ---------------------------------------------------------------------------
FF_VERSIONE=${FF_VERSIONE:-140.16.0esr-1~deb13u1}
FF_DEB="$CACHE_APT_HOST/firefox-esr_${FF_VERSIONE}_amd64.deb"

log "Browser dell'host (Firefox ESR, Chrome)"
if [ -n "${REMOTIX_SENZA_BROWSER:-}" ]; then
    inf "saltati (REMOTIX_SENZA_BROWSER)"
else
    if [ "$(dpkg-query -W -f='${Version}' firefox-esr 2>/dev/null || true)" = "$FF_VERSIONE" ]; then
        ok "firefox-esr $FF_VERSIONE gia' installato"
    elif [ -f "$FF_DEB" ]; then
        env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends "$FF_DEB"
        ok "firefox-esr $FF_VERSIONE installato dal .deb in cache"
    else
        ko "manca $FF_DEB: lancia prima benches/11-boxes/11-assemble-product.sh"
    fi

    if dpkg -s google-chrome-stable >/dev/null 2>&1; then
        ok "google-chrome-stable gia' installato"
    else
        mkdir -p /etc/apt/keyrings
        if [ ! -s /etc/apt/keyrings/google-chrome.gpg ]; then
            curl -fsSL https://dl.google.com/linux/linux_signing_key.pub \
                | gpg --dearmor > /etc/apt/keyrings/google-chrome.gpg
        fi
        sh -c 'printf "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] https://dl.google.com/linux/chrome/deb/ stable main\n" > /etc/apt/sources.list.d/google-chrome.list'
        apt-get update -qq
        env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends google-chrome-stable
        ok "google-chrome-stable installato"
    fi
fi

# ---------------------------------------------------------------------------
# 5b. L'audio dell'utente sull'host: Firefox senza un server pulse non ha uscita audio
# ---------------------------------------------------------------------------
log "Audio dell'utente (pipewire-pulse)"
loginctl enable-linger "$UTENTE" || inf "linger non attivato: l'audio dell'utente partira' solo con una sessione aperta"
for _ in $(seq 1 20); do [ -S /run/user/$UID_UTENTE/bus ] && break; sleep 0.5; done
runuser -u "$UTENTE" -- env XDG_RUNTIME_DIR=/run/user/$UID_UTENTE systemctl --user start pipewire pipewire-pulse wireplumber \
    && ok "pipewire attivo per $UTENTE" || inf "pipewire non avviato: lancialo a mano"

# ---------------------------------------------------------------------------
# 5-bis. Le schede per l'utente: i client dei banchi (Firefox, Chrome) aprono /dev/dri/renderD* per decodificare
#    in hardware; senza i gruppi decodificano in CPU e il 30-perf misura il client (26 ott 2026, dopo un riavvio).
log "Gruppi video e render per $UTENTE"
usermod -aG video,render "$UTENTE" && ok "$UTENTE in video e render (vale dalla prossima sessione ssh)"

# 5-ter. I modelli locali: lo script llm.sh sta sul disco (/media/DOWNLOAD/llama-swap), ~/llm e' un collegamento.
#    (26 ott 2026: l'originale stava in ~/llm, cioe' in RAM, ed e' sparito al riavvio.)
log "Collegamento ~/llm"
if [ -x /media/DOWNLOAD/llama-swap/llm.sh ]; then
    ln -sfn /media/DOWNLOAD/llama-swap "/home/$UTENTE/llm" && chown -h "$UTENTE:$UTENTE" "/home/$UTENTE/llm" && ok "~/llm -> /media/DOWNLOAD/llama-swap"
else
    inf "/media/DOWNLOAD/llama-swap/llm.sh assente: i modelli locali non si accendono"
fi

# 6. Riepilogo: i fatti che contano per non finire la memoria
# ---------------------------------------------------------------------------
log "Riepilogo"
inf "MemAvailable: $(awk '/MemAvailable/{printf "%.1f GB", $2/1048576}' /proc/meminfo)"
inf "podman (root)   graphroot: $(sed -n 's/^graphroot = //p' /etc/containers/storage.conf)"
inf "podman (utente) graphroot: $(sed -n 's/^graphroot = //p' "$CASA/.config/containers/storage.conf")"
ok "provision-15 finito"
