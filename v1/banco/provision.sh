#!/bin/bash
#
# REMOTIX - provisioning dell'ambiente di sviluppo
# =================================================
#
# Il server e' un sistema live: "/" vive in RAM e si azzera a ogni riavvio.
# Tutto cio' che deve sopravvivere risiede su /media/REMOTIX (NVMe, 1,8 TB).
#
# Questo script e' IDEMPOTENTE: rilanciarlo dopo un riavvio ricostruisce
# solo cio' che manca, saltando quello che e' gia' a posto.
#
#   Uso:   bash /media/REMOTIX/provision.sh
#
#
# CONFINAMENTO IN /media/REMOTIX
# ------------------------------
# Lo script NON installa nulla nel sistema host e NON tocca i dischi: non
# partiziona, non formatta, non monta dispositivi a blocchi.
#
# Tutto cio' che scrive su disco sta sotto /media/REMOTIX. Le uniche tracce
# fuori da li' non risiedono su disco e svaniscono al riavvio:
#
#   - i bind mount, che sono voci nella tabella di montaggio del kernel
#     (si annullano con la funzione umount_chroot piu' sotto);
#   - il file temporaneo con cui sudo ricorda la password, in RAM.
#
#
# Struttura creata:
#
#   /media/REMOTIX/devroot     contenitore Debian con la toolchain
#   /media/REMOTIX/src         sorgenti del progetto
#   /media/REMOTIX/hosttools   mmdebstrap e moduli perl, per non installarli sull'host
#   /media/REMOTIX/cache       cache dei pacchetti .deb
#   /media/REMOTIX/tmp         temporanei (tiene TMPDIR fuori da /tmp)
#   /media/REMOTIX/enter.sh    script per entrare nel contenitore
#
set -euo pipefail

# evita gli avvisi di locale mancante nei sottoprocessi perl
export LC_ALL=C

BASE=/media/REMOTIX
DEVROOT="$BASE/devroot"
SRC="$BASE/src"
TOOLS="$BASE/hosttools"
CACHE="$BASE/cache"
TMP="$BASE/tmp"

SUITE=trixie
MIRROR=http://deb.debian.org/debian
PERLV=5.40

DEV_USER=dev
DEV_UID=$(id -u)
DEV_GID=$(id -g)

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

# ---------------------------------------------------------------------------
# Pacchetti necessari DENTRO il contenitore.
# Sono le dipendenze di compilazione del progetto: FreeRDP 3, GLib, Wayland,
# VA-API, PipeWire, PAM.
#
# Il progetto si scrive in C e si costruisce con meson (§8-bis di SPECIFICA.md),
# come il riferimento gnome-remote-desktop.
# ---------------------------------------------------------------------------
CONTAINER_PKGS=(
    # toolchain di base
    build-essential pkg-config git curl ca-certificates less nano
    clang clangd clang-format gdb
    cmake ninja-build meson nasm

    # FreeRDP 3: e' lo stack RDP del progetto (vincolo del 3 agosto 2026).
    # freerdp3-dev porta i .pc di freerdp3, freerdp-client3 e freerdp-server3;
    # libwinpr3-dev quello di winpr3.
    freerdp3-dev libwinpr3-dev

    # GLib e GIO: ciclo eventi, D-Bus, tipi di base — come il riferimento
    libglib2.0-dev

    # Wayland e input
    libwayland-dev wayland-protocols libxkbcommon-dev
    libinput-dev libudev-dev libseat-dev

    # libei: il trasporto dell'input verso il compositore, deciso il 4 agosto
    # 2026 chiudendo la fase 3 (§5.8 di SPECIFICA.md).  E' la strada del
    # riferimento, ed e' l'unica che consegni la disposizione di tastiera della
    # sessione — che chiude la questione aperta n.7 invece di rimandarla.
    # xkbcommon (gia' sopra) serve a leggere quella keymap.
    libei-dev

    # grafica e codec
    libdrm-dev libgbm-dev libegl-dev libgles-dev
    libva-dev libvulkan-dev

    # libavcodec: il codificatore H.264 della fase 9, scelto per nome a
    # runtime.  Non si parla a VA-API ne' a NVENC direttamente (§3.1 di
    # SPECIFICA.md): un solo percorso di codice, e il costruttore e' una
    # stringa.  libswscale fa la conversione BGRx → NV12.
    libavcodec-dev libavutil-dev libswscale-dev

    # audio
    libpipewire-0.3-dev

    # autenticazione, sessioni, rete
    libpam0g-dev libssl-dev libdbus-1-dev libsystemd-dev

    # diagnostica
    vainfo ffmpeg
    # xdotool guida il client dentro l'Xvfb del banco (prove/fase4.sh).
    # ⚠ Mente: perde la prima battuta di una raffica dopo un clic, e consegna
    # la posizione PRECEDENTE del puntatore (§5.8 di SPECIFICA.md).  Le prove
    # cercano la COPPIA di letture attesa, non la prima e l'ultima.
    xdotool

    # costruzione dell'immagine di avvio della VM di runtime (vm.sh)
    xorriso

    # font, necessari a ffmpeg per generare le scene di calibrazione
    fonts-dejavu-core

    # driver VA-API per Intel e AMD, usati dalle prove di codifica
    intel-media-va-driver mesa-va-drivers

    # ⭐ REMOTIX V2, banco B2 della fase 1 — 9 agosto 2026.
    # Go serve a compilare BoringSSL, che e' la sola pila TLS con cui
    # `lsquic` e `quiche` sanno parlare QUIC.  Non e' una dipendenza del
    # prodotto: e' una dipendenza di COSTRUZIONE delle candidate, e sta qui
    # invece che nella memoria di chi ha lanciato il banco (`LEZIONI.md`
    # §2.5-bis: le dipendenze installate a mano diventano invisibili in un
    # giorno).
    golang-go
    # libevent: `lsquic` la vuole per costruire i suoi programmi d'esempio, che
    # sono il modo piu' economico di avere un server HTTP/3 vero da puntare
    # contro un browser vero.  Serve al banco, non al prodotto.
    libevent-dev
    # libev: la stessa cosa per `ngtcp2`.  ⚠ E' UN'ALTRA libreria, non una
    # variante del nome: `ngtcp2/examples/CMakeLists.txt` cerca `libev`, e con
    # la sola `libevent-dev` installata il cmake mette
    # LIBEV_LIBRARY-NOTFOUND e ⛔ SALTA GLI ESEMPI IN SILENZIO — cioe' la
    # costruzione riesce, e il server che serviva non c'e'.  Visto sul ferro
    # il 10 agosto 2026 `[M]`.
    libev-dev
    # ⭐ aioquic: due mestieri, e nessuno dei due e' il prodotto.
    #   1. e' il CONTROLLO POSITIVO di B2 — una sessione WebTransport che DEVE
    #      riuscire, senza la quale «la candidata non apre la sessione» e «il
    #      banco non sa aprirne nessuna» hanno lo stesso aspetto;
    #   2. e' il CLIENTE DI PROVA della fase 1 (B9), cioe' il secondo lettore
    #      di `RCP.md` — in un linguaggio diverso dal server e dalla pagina.
    # `[M]` 9 agosto 2026: la 1.2.0 porta WebTransport (29 occorrenze nel
    # modulo h3, l'evento WebTransportStreamDataReceived e
    # create_webtransport_stream).  Era una `[?]` del rilievo R3.21, e se
    # fosse stata «no» sarebbe caduto l'arbitro.
    python3-aioquic
)

# pacchetti scaricati e scompattati in $TOOLS, per non installarli sull'host
HOST_TOOL_DEBS=(mmdebstrap perl perl-modules-$PERLV libperl$PERLV libdpkg-perl)

# ---------------------------------------------------------------------------
# 0. Privilegi
# ---------------------------------------------------------------------------
if ! sudo -n true 2>/dev/null; then
    log "Privilegi di amministratore"
    # -S legge la password da stdin, se fornita via pipe; altrimenti chiede.
    # La richiesta NON va lasciata vuota: chi fornisce la password da standard
    # input (script, automazioni) non avrebbe nulla da riconoscere e resterebbe
    # in attesa per sempre, senza che compaia alcun messaggio.
    sudo -v -S -p 'Password sudo: '
fi

# ---------------------------------------------------------------------------
# 1. Cartelle persistenti
# ---------------------------------------------------------------------------
log "Cartelle di lavoro su $BASE"
for d in "$SRC" "$CACHE" "$TMP" "$TOOLS/debs" "$TOOLS/root"; do
    [ -d "$d" ] || mkdir -p "$d"
done
export TMPDIR="$TMP"
ok "pronte (TMPDIR confinato in $TMP)"

# ---------------------------------------------------------------------------
# 2. Strumenti host, confinati in $TOOLS
#    Scaricati come .deb e scompattati: nessuna installazione nel sistema.
# ---------------------------------------------------------------------------
log "Strumenti di bootstrap (confinati in $TOOLS)"
MM="$TOOLS/root/usr/bin/mmdebstrap"
export PERL5LIB="$TOOLS/root/usr/share/perl/$PERLV:$TOOLS/root/usr/lib/x86_64-linux-gnu/perl/$PERLV:$TOOLS/root/usr/share/perl5:$TOOLS/root/usr/lib/x86_64-linux-gnu/perl5/$PERLV"

if [ -x "$MM" ] && "$MM" --version >/dev/null 2>&1; then
    ok "mmdebstrap gia' disponibile ($("$MM" --version))"
else
    inf "scarico e scompatto: ${HOST_TOOL_DEBS[*]}"
    ( cd "$TOOLS/debs" && apt-get download "${HOST_TOOL_DEBS[@]}" >/dev/null 2>&1 )
    for d in "$TOOLS"/debs/*.deb; do
        dpkg-deb -x "$d" "$TOOLS/root"
    done
    "$MM" --version >/dev/null
    ok "mmdebstrap pronto ($("$MM" --version))"
fi

# ---------------------------------------------------------------------------
# 3. Bind mount di servizio
#
#    ATTENZIONE - queste funzioni vanno definite PRIMA di qualunque
#    cancellazione. Dentro il contenitore vengono montati /dev, /sys e
#    soprattutto $SRC: un "rm -rf" sul contenitore mentre quei mount sono
#    attivi cancellerebbe i file veri, non le cartelle vuote di appoggio.
# ---------------------------------------------------------------------------
# ⚠ I due `--rbind` vanno resi SLAVE subito dopo, e non e' un dettaglio.
#
# Un `--rbind` lascia la propagazione condivisa con l'originale: quando
# `umount_chroot` fa `umount -R "$DEVROOT/dev"`, lo smontaggio **si propaga
# all'indietro** e smonta `/dev/pts` **del server**. Da quel momento il kernel
# non puo' piu' allocare pseudo-terminali e nessuno riesce piu' ad aprire una
# sessione SSH interattiva:
#
#     PTY allocation request failed on channel 0
#
# Il guasto e' insidioso perche' l'autenticazione continua a funzionare — si
# entra, ma senza terminale — e i comandi non interattivi (`ssh host comando`,
# cioe' tutto cio' che fanno gli script di questo progetto) passano senza
# accorgersi di nulla. E' successo davvero il 3 agosto: il server e' rimasto
# senza `/dev/pts` per ore, e se n'e' accorto solo l'utente provando a entrare.
#
# `--make-rslave` mantiene la visibilita' dei sottomount dentro il contenitore e
# impedisce che le operazioni fatte li' dentro tornino indietro.
#
# Rimedio se ricapita:
#     sudo mount -t devpts devpts /dev/pts -o gid=5,mode=620,ptmxmode=000
mount_chroot() {
    sudo mkdir -p "$DEVROOT"/{proc,sys,dev,srv/src,srv/remotix}
    mountpoint -q "$DEVROOT/proc"        || sudo mount -t proc proc      "$DEVROOT/proc"
    mountpoint -q "$DEVROOT/sys"         || { sudo mount --rbind /sys "$DEVROOT/sys"
                                              sudo mount --make-rslave "$DEVROOT/sys"; }
    mountpoint -q "$DEVROOT/dev"         || { sudo mount --rbind /dev "$DEVROOT/dev"
                                              sudo mount --make-rslave "$DEVROOT/dev"; }
    mountpoint -q "$DEVROOT/srv/src"     || sudo mount --bind "$SRC"     "$DEVROOT/srv/src"
    # l'intera area di lavoro, per gli strumenti che devono agire su file
    # fuori dai sorgenti (per esempio costruire l'immagine di avvio della VM)
    mountpoint -q "$DEVROOT/srv/remotix" || sudo mount --bind "$BASE"    "$DEVROOT/srv/remotix"
}

# annulla i bind mount: riporta la tabella di montaggio com'era
umount_chroot() {
    for m in opt/rust srv/remotix srv/src dev sys proc; do   # opt/rust: residuo del progetto in Rust, si smonta se c'e' ancora
        if mountpoint -q "$DEVROOT/$m" 2>/dev/null; then
            sudo umount -R "$DEVROOT/$m" 2>/dev/null \
                || sudo umount -R -l "$DEVROOT/$m" 2>/dev/null || true
        fi
    done
}

# rete di sicurezza: verifica che sotto $DEVROOT non resti alcun mount.
# Se ne trova, si ferma invece di cancellare.
assert_no_mounts() {
    if mount | grep -qF " $DEVROOT"; then
        printf '\n\033[1;31mERRORE\033[0m mount ancora attivi sotto %s\n' "$DEVROOT" >&2
        mount | grep -F " $DEVROOT" >&2
        printf 'Interrompo per non cancellare file montati.\n' >&2
        exit 1
    fi
}

# a fine script i mount vengono sempre sciolti, comunque sia andata
trap umount_chroot EXIT

# ---------------------------------------------------------------------------
# 4. Root filesystem del contenitore
#    Risiede su NVMe: si crea una volta sola e sopravvive ai riavvii.
#
#    L'idempotenza si basa su un marcatore scritto SOLO a bootstrap riuscito.
#    Non ci si puo' basare su /etc/os-release: quel file esiste anche in un
#    rootfs incompleto, lasciato da un tentativo interrotto.
# ---------------------------------------------------------------------------
BOOT_MARKER="$DEVROOT/.remotix-bootstrap-ok"

log "Contenitore Debian $SUITE"
if [ -f "$BOOT_MARKER" ]; then
    ok "gia' presente ($(sudo du -sh --exclude=proc --exclude=sys --exclude=dev "$DEVROOT" 2>/dev/null | cut -f1))"
else
    if [ -d "$DEVROOT" ]; then
        inf "trovato contenitore incompleto: lo rimuovo"
        umount_chroot
        assert_no_mounts
        sudo rm -rf "$DEVROOT"
    fi
    inf "creazione in corso, scarica circa 250 MB..."
    sudo TMPDIR="$TMP" PERL5LIB="$PERL5LIB" LC_ALL=C "$MM" \
        --mode=root --variant=important \
        --components="main contrib non-free non-free-firmware" \
        "$SUITE" "$DEVROOT" "$MIRROR"
    # il marcatore certifica che il bootstrap e' arrivato in fondo
    sudo touch "$BOOT_MARKER"
    ok "rootfs creato"
fi

log "Bind mount di servizio"
mount_chroot
sudo cp -f /etc/resolv.conf "$DEVROOT/etc/resolv.conf"
ok "proc, sys, dev, src collegati"

# esegue un comando dentro il contenitore, come root
in_chroot() {
    sudo chroot "$DEVROOT" /usr/bin/env -i \
        PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        HOME=/root LC_ALL=C DEBIAN_FRONTEND=noninteractive TMPDIR=/tmp \
        /bin/bash -c "$*"
}

# esegue un comando dentro il contenitore, come utente di sviluppo
in_chroot_dev() {
    sudo chroot "$DEVROOT" /usr/bin/env -i \
        PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        HOME=/home/$DEV_USER USER=$DEV_USER LC_ALL=C \
        setpriv --reuid=$DEV_UID --regid=$DEV_GID --init-groups \
        /bin/bash -c "$*"
}

# ---------------------------------------------------------------------------
# 5. Utente di sviluppo dentro il contenitore
#    Ha lo stesso UID dell'utente esterno: i file creati durante la
#    compilazione restano modificabili anche da fuori dal contenitore.
# ---------------------------------------------------------------------------
log "Utente di sviluppo nel contenitore (uid $DEV_UID)"
if in_chroot "id -u $DEV_USER >/dev/null 2>&1"; then
    ok "utente '$DEV_USER' gia' presente"
else
    in_chroot "groupadd -g $DEV_GID $DEV_USER 2>/dev/null || true
               useradd -u $DEV_UID -g $DEV_GID -m -s /bin/bash $DEV_USER"
    ok "utente '$DEV_USER' creato"
fi

# ---------------------------------------------------------------------------
# 6. Dipendenze di compilazione dentro il contenitore
# ---------------------------------------------------------------------------
log "Dipendenze di compilazione nel contenitore"
NEEDED=$(in_chroot "
    miss=''
    for p in ${CONTAINER_PKGS[*]}; do
        dpkg -s \$p >/dev/null 2>&1 || miss=\"\$miss \$p\"
    done
    echo \$miss
")
if [ -n "${NEEDED// /}" ]; then
    inf "mancanti:$NEEDED"
    in_chroot "apt-get update -qq && apt-get install -y -qq $NEEDED"
    ok "installate"
else
    ok "gia' presenti (${#CONTAINER_PKGS[@]} pacchetti)"
fi

# ---------------------------------------------------------------------------
# 7. Verifica della toolchain C e delle librerie di FreeRDP
#    Non si installa nulla qui: i pacchetti sono gia' arrivati al punto 6.
#    Si controlla che pkg-config li trovi, perche' un .pc mancante si
#    manifesta molto piu' tardi, come un errore di meson incomprensibile.
# ---------------------------------------------------------------------------
log "Toolchain C e FreeRDP 3"
MANCANTI=$(in_chroot "
    m=''
    for p in freerdp3 freerdp-server3 winpr3 glib-2.0 gio-2.0 libpipewire-0.3 libsystemd libei-1.0 xkbcommon; do
        pkg-config --exists \$p 2>/dev/null || m=\"\$m \$p\"
    done
    echo \$m
")
if [ -n "${MANCANTI// /}" ]; then
    printf '\n\033[1;31mERRORE\033[0m pkg-config non trova:%s\n' "$MANCANTI" >&2
    exit 1
fi
inf "gcc      $(in_chroot 'gcc -dumpversion')"
inf "meson    $(in_chroot 'meson --version')"
inf "freerdp3 $(in_chroot 'pkg-config --modversion freerdp3')"
ok "tutte le dipendenze sono visibili a pkg-config"

# ---------------------------------------------------------------------------
# 7b. Profilo di shell dentro il contenitore
#     La shell di login rilegge /etc/profile e sovrascrive il PATH ereditato:
#     quel che serve al progetto va dichiarato qui.
# ---------------------------------------------------------------------------
log "Profilo di shell nel contenitore"
sudo tee "$DEVROOT/etc/profile.d/remotix.sh" >/dev/null <<'PROFILE'
# Ambiente di sviluppo REMOTIX
export REMOTIX_SRC=/srv/src/remotix-c
export REMOTIX_BUILD=/srv/src/remotix-c/build
PROFILE
ok "/etc/profile.d/remotix.sh"

# ---------------------------------------------------------------------------
# 8. Script di ingresso
# ---------------------------------------------------------------------------
log "Script di ingresso"
cat > "$BASE/enter.sh" <<ENTER
#!/bin/bash
#
# Entra nel contenitore di sviluppo REMOTIX.
#
#   bash /media/REMOTIX/enter.sh            apre una shell interattiva
#   bash /media/REMOTIX/enter.sh <comando>  esegue un comando e esce
#   bash /media/REMOTIX/enter.sh --root ... come sopra, ma da amministratore
#
# La modalita' --root serve per le operazioni di manutenzione (installare
# pacchetti) e per accedere ai nodi GPU: l'utente esterno non appartiene ai
# gruppi video e render del sistema host, e non li si vuole modificare.
#
# I sorgenti sono in /srv/src; il progetto in C sta in /srv/src/remotix-c.
#
# La password di sudo puo' essere digitata, oppure fornita da standard input:
#   printf '%s\n' "\$PASSWORD" | bash /media/REMOTIX/enter.sh "ninja -C \$REMOTIX_BUILD"
#
set -euo pipefail

DEVROOT=$DEVROOT

# Acquisisce le credenziali una volta sola. Con -S le legge da standard input
# se ce ne sono, altrimenti le chiede a terminale.
if ! sudo -n true 2>/dev/null; then
    # La richiesta NON va lasciata vuota: chi fornisce la password da standard
    # input (script, automazioni) non avrebbe nulla da riconoscere e resterebbe
    # in attesa per sempre, senza che compaia alcun messaggio.
    sudo -v -S -p 'Password sudo: '
fi

sudo mkdir -p "\$DEVROOT"/{proc,sys,dev,srv/src,srv/remotix}
mountpoint -q "\$DEVROOT/proc"        || sudo mount -t proc proc  "\$DEVROOT/proc"
# I --rbind vanno resi slave: senza, un umount ricorsivo qui dentro si propaga
# all'originale e smonta /dev/pts DEL SERVER, che resta senza pseudo-terminali
# e non fa piu' entrare nessuno in SSH ("PTY allocation request failed").
mountpoint -q "\$DEVROOT/sys"         || { sudo mount --rbind /sys "\$DEVROOT/sys"
                                           sudo mount --make-rslave "\$DEVROOT/sys"; }
mountpoint -q "\$DEVROOT/dev"         || { sudo mount --rbind /dev "\$DEVROOT/dev"
                                           sudo mount --make-rslave "\$DEVROOT/dev"; }
mountpoint -q "\$DEVROOT/srv/src"     || sudo mount --bind $SRC     "\$DEVROOT/srv/src"
mountpoint -q "\$DEVROOT/srv/remotix" || sudo mount --bind $BASE    "\$DEVROOT/srv/remotix"
sudo cp -f /etc/resolv.conf "\$DEVROOT/etc/resolv.conf"

AS_ROOT=no
if [ "\${1:-}" = "--root" ]; then AS_ROOT=yes; shift; fi

if [ \$# -eq 0 ]; then
    set -- /bin/bash -l
else
    set -- /bin/bash -lc "\$*"
fi

# NB: niente "exec". Sostituendo il processo si perderebbe l'associazione
# delle credenziali sudo gia' validate, e in assenza di terminale la
# password verrebbe richiesta di nuovo senza poter essere letta.
if [ "\$AS_ROOT" = yes ]; then
    sudo chroot "\$DEVROOT" /usr/bin/env -i \\
        PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \\
        HOME=/root USER=root TERM="\${TERM:-xterm}" LC_ALL=C.UTF-8 \\
        "\$@"
else
    sudo chroot "\$DEVROOT" /usr/bin/env -i \\
        PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \\
        HOME=/home/$DEV_USER USER=$DEV_USER TERM="\${TERM:-xterm}" LC_ALL=C.UTF-8 \\
        setpriv --reuid=$DEV_UID --regid=$DEV_GID --init-groups \\
        "\$@"
fi
ENTER
chmod +x "$BASE/enter.sh"
ok "$BASE/enter.sh"

# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------
log "Ambiente pronto"
printf '
    contenitore   %s
    sorgenti      %s   ->  /srv/src
    progetto      %s/remotix-c   ->  /srv/src/remotix-c
    ingresso      bash %s/enter.sh

    gcc:        %s
    meson:      %s
    FreeRDP:    %s

    Si costruisce cosi'\'':
        bash %s/enter.sh "meson setup \$REMOTIX_BUILD \$REMOTIX_SRC"
        bash %s/enter.sh "ninja -C \$REMOTIX_BUILD"

    Nulla e'\'' stato installato nel sistema host.

' "$DEVROOT" "$SRC" "$SRC" "$BASE" \
  "$(in_chroot 'gcc -dumpversion' 2>/dev/null || echo '?')" \
  "$(in_chroot 'meson --version' 2>/dev/null || echo '?')" \
  "$(in_chroot 'pkg-config --modversion freerdp3' 2>/dev/null || echo '?')" \
  "$BASE" "$BASE"
