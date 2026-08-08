#!/bin/bash
#
# Prova della fase 11, voce 1: REMOTIX manda il DESKTOP DI KDE?
#
#   bash /media/REMOTIX/src/remotix-c/prove/fase11.sh
#
# Va eseguita SUL SERVER, come quelle delle fasi 3 e 6: mette insieme la
# macchina di runtime — dove gira Plasma e gira REMOTIX — e il contenitore di
# sviluppo, dove c'e' il client di prova.
#
# Che cosa guarda, in ordine di importanza:
#
#   1. IL CANCELLO.  `zkde_screencast_unstable_v1` non viene annunciato a chi non
#      lo dichiara in un `.desktop` installato, e il sintomo e' «questo
#      compositore non ha il protocollo».  Finche' questo controllo e' rosso,
#      ogni altro numero e' teoria (`kde.md` §3);
#   2. la misura: su KWin la decide il COMPOSITORE, e la tela deve prendere la
#      sua — non quella che il client ha chiesto (`kde.md` §8.1);
#   3. la COPIA ZERO, che su KDE non e' un'ottimizzazione ma la condizione dei
#      60 fotogrammi a 4K (`kde.md` §5.7);
#   4. l'attesa della fence: KWin fa `glFlush` e non `glFinish`, quindi il
#      buffer arriva col disegno in corso e chi non aspetta codifica il
#      fotogramma di prima (`kde.md` §4.8);
#   5. i buffer di SOLO CURSORE, scartati: in modo cursore «metadato» ogni
#      movimento del mouse ne produce uno, e chi lo consegna mostra
#      un'immagine vecchia (`kde.md` §4.7);
#   6. che il client veda il desktop.
#
# ⚠ La Radeon viene negata ai PERMESSI DEL NODO per la durata della prova, e
#   ripristinata da una trap in ogni caso — uscita normale, errore,
#   interruzione.  E' la sola via che ottiene la Intel senza chiudere il
#   cancello della cattura: `InaccessiblePaths=` nell'unita' del compositore
#   funziona per la GPU e NEGA il permesso (`kde.md` §5.6 e §3.3-bis).  Per il
#   prodotto l'equivalente stabile e' una regola udev per id PCI, ed e' la
#   voce 3 del piano.
set -u

# Due modi.  Senza argomento: la prova funzionale, «si vede il desktop di KDE».
# Con `misura`: quanti fotogrammi la cattura consegna davvero, con una scena
# dichiarata e sempre in movimento — che e' l'unica forma di misura che valga
# (`LEZIONI.md` §1.1: un compositore manda un fotogramma solo quando qualcosa
# cambia, e una scena ferma misura la scena, non il compositore).
MODO=${1:-prova}

BASE=/media/REMOTIX
BIN_LOCALE="$BASE/src/remotix-c/build/src/remotix"
PORTA=${PORTA:-3393}
LARGHEZZA=${LARGHEZZA:-1920}
ALTEZZA=${ALTEZZA:-1080}
# La misura che il CLIENT chiede, apposta diversa da quella del compositore: e'
# il controllo n.2, e con due numeri uguali non proverebbe niente.
MISURA_CLIENT=${MISURA_CLIENT:-1280x720}
DISPLAY_CLI=:111
SECONDI=${SECONDI:-12}

. "$(dirname "$0")/runtime.sh"
cnt() { bash "$BASE/enter.sh" "$@"; }

titolo() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()     { printf '    \033[1;32mOK\033[0m    %s\n' "$*"; }
ko()     { printf '    \033[1;31mNO\033[0m    %s\n' "$*"; GUASTI=$((GUASTI+1)); }
inf()    { printf '    --    %s\n' "$*"; }
GUASTI=0

[ -x "$BIN_LOCALE" ] || { echo "manca $BIN_LOCALE: costruiscilo prima"; exit 1; }

U=$(id -u)
export XDG_RUNTIME_DIR="/run/user/$U"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
# ⛔ SENZA QUESTA IL CANCELLO RESTA CHIUSO, e il file `.desktop` non c'entra:
#    l'indice dei servizi di KDE si costruisce a partire da
#    `${XDG_MENU_PREFIX}applications.menu`, e Debian non installa
#    `applications.menu`.  Senza prefisso `kbuildsycoca6` esce con stato ZERO e
#    non indicizza NIENTE — nemmeno le 133 applicazioni di sistema — e KWin dice
#    «Could not find the desktop file».  Cinque prove per trovarla, il 7 agosto
#    2026 (`kde.md` §3.3-bis, `LEZIONI.md` §1.10).
export XDG_MENU_PREFIX=plasma-
export LANG=C.UTF-8 LC_ALL=C.UTF-8
unset WAYLAND_DISPLAY DISPLAY QT_QPA_PLATFORM

#
# ⚠ IL BANCO GIRA A LIVELLO «TRACCIA», e va detto perche' non e' gratis: a quel
#   livello il registro annota OGNI TASTO — e' a tutti gli effetti un
#   registratore di battitura, password comprese (§5.8 di SPECIFICA.md), ed e'
#   per questo che nel servizio vero sta sotto `diagnostica`.  Qui serve: i tasti
#   inoltrati e gli scatti della rotella si scrivono li', e a `diagnostica` un
#   banco che li cerca li trova assenti — cioe' rosso su codice giusto, che e' il
#   difetto piu' costoso che un banco possa avere.
LOG="$XDG_RUNTIME_DIR/fase11"; rm -rf "$LOG"; mkdir -p "$LOG"
DIR="$XDG_RUNTIME_DIR/systemd/user.control/plasma-kwin_wayland.service.d"

#
# ⛔ LO STDERR DI `sudo` NON SI REDIRIGE, e questa riga e' una trappola gia'
#    pagata in fase 1: `sudo -S` legge la parola d'ordine dallo standard input e
#    scrive la richiesta sullo standard ERROR.  Chi redirige lo stderr del banco
#    in un file lascia appeso per sempre, IN SILENZIO, chi la deve fornire.
#
#    Da cui il modo di eseguire questo banco da fuori: si redirige il solo
#    stdout, e lo stderr resta sul terminale.
#
#        bash prove/fase11.sh > /tmp/f11.out
#
# E per la stessa ragione il sudo lo si chiede UNA VOLTA, qui, e solo se serve:
# senza `INTEL=1` il banco non tocca nessun permesso e non ne ha bisogno.
INTEL=${INTEL:-0}
if [ "$INTEL" = 1 ]; then
    echo "== la password di sudo, una volta sola ==" >&2
    sudo -S -p 'Password: ' -v >/dev/null || exit 1
fi
bash "$BASE/enter.sh" true || exit 1

GRUPPO_RADEON=$(stat -c %G /dev/dri/renderD129 2>/dev/null || echo render)
pulisci() {
    pkill -x remotix 2>/dev/null
    gdbus call --session --dest org.kde.Shutdown --object-path /Shutdown \
        --method org.kde.Shutdown.logout >/dev/null 2>&1
    for i in $(seq 20); do pgrep -x plasmashell >/dev/null || break; sleep 1; done
    for p in plasmashell kwin_wayland ksmserver kded6 Xwayland kglobalacceld xembedsniproxy; do
        pkill -x $p 2>/dev/null
    done
    #
    # ⛔ NON BASTA UCCIDERE I PROCESSI: BISOGNA ASPETTARE CHE SYSTEMD ABBIA
    #    FINITO.
    #
    #    Uccidendo `kwin_wayland` il gestore d'utente mette in coda un lavoro di
    #    «stop» sulla sua unita'; se nel frattempo si chiede di far partire la
    #    sessione nuova, systemd rifiuta l'INTERA transazione:
    #
    #      «Transaction for plasma-workspace-wayland.target/start is destructive
    #       (plasma-kwin_wayland.service has 'stop' job queued...)»
    #
    #    e `startplasma-wayland` esce dicendo soltanto «Could not start Plasma
    #    session».  Cioe': un banco che rifa' la sessione due volte di fila
    #    fallisce la seconda, e il messaggio non nomina la causa.
    #    [M, 8 agosto 2026, alla seconda esecuzione di questo banco]
    systemctl --user stop plasma-workspace.target plasma-workspace-wayland.target \
        plasma-kwin_wayland.service 2>/dev/null
    for i in $(seq 20); do
        [ "$(systemctl --user is-active plasma-kwin_wayland.service 2>/dev/null)" = inactive ] && break
        sleep 1
    done
    rm -rf "$DIR"; systemctl --user daemon-reload 2>/dev/null
    [ "$INTEL" = 1 ] && sudo -n chgrp "$GRUPPO_RADEON" /dev/dri/renderD129 2>/dev/null
    # ⛔ LO STDERR NON SI REDIRIGE: dentro `enter.sh` c'e' un `sudo`, e la sua
    #    richiesta finita in /dev/null lascia appeso per sempre chi la deve
    #    fornire.  E' la stessa trappola della fase 1, e la si ripaga ogni volta
    #    che si scrive `2>&1` per abitudine.
    cnt "pkill -f '^Xvfb $DISPLAY_CLI'" >/dev/null
}
trap pulisci EXIT INT TERM
pulisci

# ---------------------------------------------------------------------------
titolo "1. Il file che apre il cancello"
# ---------------------------------------------------------------------------
# Si installa PRIMA di avviare la sessione: l'indice dei servizi lo ricostruisce
# il primo processo KDE che lo usa, e a quel punto il file c'e' gia'.
"$BIN_LOCALE" --installa-desktop 2>&1 | sed 's/^/    /'
DESKTOP="$HOME/.local/share/applications/org.kde.remotix.desktop"
if grep -q "^Exec=$BIN_LOCALE\$" "$DESKTOP" 2>/dev/null; then
    ok "il .desktop nomina il binario vero"
else
    ko "il .desktop non nomina $BIN_LOCALE: KWin negherebbe il permesso"
fi
grep -q 'zkde_screencast_unstable_v1' "$DESKTOP" && \
    ok "dichiara l'interfaccia della cattura" || ko "manca X-KDE-Wayland-Interfaces"

# ---------------------------------------------------------------------------
titolo "2. La scheda su cui KWin disegnera'"
# ---------------------------------------------------------------------------
# ⛔ CON `--virtual` NON ESISTE ALCUNA LEVA: `findRenderDevice()` prende la PRIMA
#    che si apre, e `KWIN_DRM_DEVICES` vale solo per il backend `drm`
#    (`kde.md` §5.6).  La si sceglie quindi rendendo l'altra non apribile — e la
#    sola via che non chiude anche il cancello della cattura sono i PERMESSI DEL
#    NODO.  Qui e' facoltativa perche' tocca `/dev`, e un banco che modifica i
#    permessi dei dispositivi della macchina dell'utente non lo si fa di
#    nascosto: per il prodotto la stessa cosa si scrive come regola udev per id
#    PCI, ed e' la voce 3 del piano.
if [ "$INTEL" = 1 ]; then
    sudo -n chgrp root /dev/dri/renderD129
    inf "renderD129 (Radeon) ora e' $(stat -c '%A %U:%G' /dev/dri/renderD129): fuori portata"
else
    inf "INTEL=1 per negare la Radeon e misurare sulla scheda del prodotto; senza, KWin"
    inf "prende la prima che si apre e il renderer lo dichiara il controllo qui sotto"
fi

# ---------------------------------------------------------------------------
if [ "$MODO" = sessione ]; then
titolo "3. La sessione la avvia REMOTIX, non questo script"
# ---------------------------------------------------------------------------
#
# ⛔ E' IL CONTROLLO CHE CONTA DELLA VOCE 3, e per averlo il banco deve
#    ASTENERSI: niente drop-in, niente `startplasma-wayland`, niente attesa.  La
#    macchina e' come dopo un riavvio — nessun desktop, nessun gestore d'accesso
#    — e il primo client che bussa deve trovarne uno.
inf "nessuna sessione, nessun drop-in: la macchina e' come appena avviata"
inf "il desktop dovra' venire $MISURA_CLIENT, cioe' la misura che chiede il client"
SOCKET=""
else
titolo "3. La sessione Plasma senza monitor"
# ---------------------------------------------------------------------------
mkdir -p "$DIR"
{
    echo "[Service]"
    echo "ExecStart="
    # ⛔ NIENTE `InaccessiblePaths=` NE' ALTRO CHE IMPLICHI UN MOUNT NAMESPACE:
    #    chiude il cancello della cattura, e in silenzio (`kde.md` §3.3-bis).
    echo "ExecStart=/bin/sh -c 'exec /usr/bin/kwin_wayland_wrapper --xwayland --virtual" \
         "--width $LARGHEZZA --height $ALTEZZA --no-lockscreen 2>>$LOG/kwin.log'"
    echo "Environment=\"QT_LOGGING_RULES=KWIN_UTILS.debug=true\""
} > "$DIR/remotix.conf"
systemctl --user daemon-reload

setsid nohup startplasma-wayland > "$LOG/plasma.log" 2>&1 &
for i in $(seq 60); do pgrep -x plasmashell >/dev/null && break; sleep 1; done
sleep 5
SOCKET=$(ls -1 "$XDG_RUNTIME_DIR" | grep -E '^wayland-[0-9]+$' | head -1)
if pgrep -x plasmashell >/dev/null && [ -n "$SOCKET" ]; then
    ok "sessione Plasma in piedi, socket $SOCKET"
else
    ko "la sessione Plasma non e' partita: vedi $LOG/plasma.log"
    exit 1
fi
fi
RENDERER=$(gdbus call --session --dest org.kde.KWin --object-path /KWin \
    --method org.kde.KWin.supportInformation 2>/dev/null \
    | grep -aoE 'OpenGL renderer string: [^\\]*' | head -1)
if [ "$MODO" = sessione ]; then RENDERER=""; fi
# ⛔ E' L'UNICA PROVA CHE REGGE.  «Il render node e' aperto» non prova niente —
#    lo apre il costruttore del backend anche in QPainter — e `KWIN_COMPOSE=O2`
#    non protegge affatto: KWin ripiega in software E PARTE (`kde.md` §5.4).
if [ "$MODO" = sessione ]; then
    inf "il renderer si guardera' dopo, quando la sessione ci sara'"
elif [ -z "$RENDERER" ]; then
    ko "KWin non dichiara nessun renderer OpenGL: sta componendo in QPainter"
elif echo "$RENDERER" | grep -qi 'llvmpipe\|softpipe'; then
    ko "$RENDERER — e' rendering software travestito da GPU"
else
    ok "$RENDERER"
fi

# ---------------------------------------------------------------------------
titolo "4. REMOTIX si collega al compositore"
# ---------------------------------------------------------------------------
rm -f "$LOG/remotix.log"
# ⛔ NEL MODO `sessione` NON SI PASSA `WAYLAND_DISPLAY`, ed e' un controllo: il
#    servizio vero non ce l'ha — lo avvia systemd, o una shell SSH — e deve
#    trovare il socket da se', sapendo che il numero CAMBIA a ogni sessione
#    (`kde.md` §6.6).
WAYLAND_DISPLAY="$SOCKET" setsid nohup "$BIN_LOCALE" \
    --compositore kwin --senza-autenticazione --porta "$PORTA" \
    --registro traccia > "$LOG/remotix.log" 2>&1 &
sleep 2
if ss -ltn 2>/dev/null | grep -q ":$PORTA"; then
    ok "REMOTIX in ascolto sulla $PORTA"
else
    ko "REMOTIX non ascolta: vedi $LOG/remotix.log"
    tail -20 "$LOG/remotix.log" | sed 's/^/       /'
    exit 1
fi

# ---------------------------------------------------------------------------
titolo "5. Un client, e quel che vede"
# ---------------------------------------------------------------------------
#
# ⛔ I FOTOGRAMMI SI CONTANO DAL LATO CHE LI RICEVE.  Il nostro registro dice
#    che abbiamo chiamato una funzione, non che il byte e' arrivato: e' il
#    corollario di R12, pagato per tre fasi.  `spia-avc420.so` e' l'innesto che
#    legge i rettangoli COME ARRIVANO DAL FILO, dentro il client.
BANCO=/srv/remotix/tmp/banco-b
cnt "
    pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null
    Xvfb $DISPLAY_CLI -screen 0 2560x1440x24 >/dev/null 2>&1 &
    sleep 2
    cd $BANCO && rm -f fase11-rect.txt
    DISPLAY=$DISPLAY_CLI LD_PRELOAD=$BANCO/spia-avc420.so \
    SPIA_AVC420=$BANCO/fase11-rect.txt \
        timeout $SECONDI xfreerdp3 /v:127.0.0.1:$PORTA \
        /size:$MISURA_CLIENT /gfx:AVC420 /cert:ignore /sec:tls /u:prova /p:prova \
        /log-level:WARN >/tmp/fase11-client.log 2>&1
    echo \"    --    fotogrammi contati DENTRO il client: \$(grep -c '^fotogramma' $BANCO/fase11-rect.txt 2>/dev/null || echo 0)\"
    pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null
    true"

R="$LOG/remotix.log"

# ---------------------------------------------------------------------------
titolo "5-bis. L'input: tastiera, puntatore, rotella"
# ---------------------------------------------------------------------------
# ⚠ `xdotool` MENTE, ed e' scritto in §5.8 di SPECIFICA.md: perde battute e
#   consegna la posizione precedente del puntatore.  Qui non si conta quel che
#   si e' mandato — si cerca nel registro del SERVER quel che e' stato inoltrato
#   al compositore, che e' l'unico lato che sappia la verita'.
# ⛔ NIENTE VARIABILI DI SHELL DENTRO QUESTO BLOCCO.  Il testo attraversa tre
#    livelli di virgolette — questo script, `enter.sh`, la shell del chroot — e
#    una `$` sfuggita di mano produce un comando che non fa quel che sembra.
#    `xdotool` concatena i propri comandi: `search ... windowactivate %1` fa la
#    stessa cosa senza passare da una variabile.
cnt "
    pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null
    Xvfb $DISPLAY_CLI -screen 0 2560x1440x24 >/dev/null 2>&1 &
    sleep 2
    DISPLAY=$DISPLAY_CLI timeout 25 xfreerdp3 /v:127.0.0.1:$PORTA \
        /size:$MISURA_CLIENT /gfx:AVC420 /cert:ignore /sec:tls /u:prova /p:prova \
        /log-level:WARN >/tmp/fase11-input.log 2>&1 &
    sleep 6
    DISPLAY=$DISPLAY_CLI xdotool search --name FreeRDP windowfocus %1
    sleep 1
    DISPLAY=$DISPLAY_CLI xdotool search --name FreeRDP type --window %1 --delay 80 remotix
    sleep 1
    DISPLAY=$DISPLAY_CLI xdotool mousemove --sync 400 300
    sleep 1
    DISPLAY=$DISPLAY_CLI xdotool mousemove --sync 700 500
    sleep 1
    DISPLAY=$DISPLAY_CLI xdotool click 4
    sleep 1
    DISPLAY=$DISPLAY_CLI xdotool click 5
    sleep 3
    pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null
    true"
sleep 1

if grep -q 'canale di input concesso da KWin' "$R"; then
    ok "$(grep -o 'canale di input concesso da KWin.*' "$R" | head -1)"
else
    ko "KWin non ha concesso il canale di input: la sessione resta di sola visione"
fi
if grep -q 'disposizione della sessione' "$R"; then
    ok "$(grep -o 'disposizione della sessione.*' "$R" | head -1)"
else
    inf "nessuna disposizione letta da libei: il percorso Unicode resterebbe spento"
fi
TASTI=$(grep -c 'tasto evdev' "$R" 2>/dev/null || echo 0)
if [ "$TASTI" -gt 0 ]; then
    ok "$TASTI eventi di tastiera inoltrati al compositore"
else
    ko "nessun tasto e' arrivato al compositore"
fi
REG=$(grep -o 'regione del puntatore: .*' "$R" | head -1)
if [ -n "$REG" ]; then
    ok "$REG"
else
    ko "nessuna regione del puntatore: le coordinate assolute finirebbero altrove"
fi
# ⛔ LA ROTELLA SI GUARDA NEL VERSO GIUSTO, e non e' pedanteria: il banco della
#    fase 4 cercava «asse dy=-10» mentre il registro scriveva «asse dx=0 dy=-10»
#    — rosso con il codice giusto.  Qui si cerca il numero, non la riga.
SU=$(grep -c 'scatti dx=0 dy=-120' "$R" 2>/dev/null || echo 0)
GIU=$(grep -c 'scatti dx=0 dy=120' "$R" 2>/dev/null || echo 0)
if [ "$SU" -gt 0 ] && [ "$GIU" -gt 0 ]; then
    ok "la rotella arriva come SCATTI DISCRETI nei due versi ($SU su', $GIU giu')"
elif grep -q 'scatti d' "$R"; then
    inf "scatti visti: $(grep -o 'scatti dx=[-0-9]* dy=[-0-9]*' "$R" | sort -u | tr '\n' ' ')"
    ko "la rotella non ha prodotto uno scatto per verso"
else
    ko "nessuno scatto di rotella: su KWin lo scroll continuo non produce nulla"
fi
if grep -q 'lucchetti secondo KWin' "$R"; then
    ok "$(grep -o 'lucchetti secondo KWin.*' "$R" | head -1)"
else
    ko "org_kde_kwin_keystate non parla: BlocMaiusc e BlocNum resterebbero indovinati"
fi
RICEVUTI=$(grep -c '^fotogramma' "$BASE/tmp/banco-b/fase11-rect.txt" 2>/dev/null || echo 0)
sleep 1

# --- il cancello ------------------------------------------------------------
if grep -q 'il permesso della cattura c' "$R"; then
    ok "$(grep -o 'zkde_screencast_unstable_v1 versione [0-9]*' "$R" | head -1): il cancello e' aperto"
else
    ko "il cancello e' CHIUSO — la causa esatta la dice KWin in $LOG/kwin.log"
    grep -a 'KWIN_UTILS' "$LOG/kwin.log" 2>/dev/null | grep -a remotix | sort -u | sed 's/^/       /'
fi

# --- la cattura -------------------------------------------------------------
if grep -q 'cattura KDE avviata' "$R"; then
    ok "$(grep -o 'cattura KDE avviata.*' "$R" | head -1)"
else
    ko "la cattura non e' partita"
fi

# --- la misura --------------------------------------------------------------
# ⚠ Nel modo `sessione` la domanda e' un'altra: la' il desktop DEVE venire della
#   misura del client, perche' la sessione la avvia REMOTIX con quel numero.  Un
#   controllo che cercasse l'adozione sarebbe rosso proprio quando tutto e'
#   andato meglio del previsto.
if [ "$MODO" = sessione ]; then
    if grep -q "cattura KDE avviata sull'uscita «Virtual-0» (${MISURA_CLIENT%x*}x${MISURA_CLIENT#*x})" "$R"; then
        ok "il desktop e' venuto $MISURA_CLIENT: la misura la ha decisa il client che si e' collegato"
    else
        ko "il desktop non e' della misura chiesta dal client"
    fi
elif grep -q "il desktop servito e' ${LARGHEZZA}x${ALTEZZA}" "$R"; then
    ok "la tela ha preso la misura del compositore (${LARGHEZZA}x${ALTEZZA}), non quella chiesta dal client"
elif grep -q "formato negoziato con" "$R"; then
    inf "misura negoziata: $(grep -o 'formato negoziato con[^,]*, [0-9]*x[0-9]*' "$R" | head -1)"
    ko "la tela non ha adottato la misura del compositore"
else
    ko "nessuna misura negoziata nel registro"
fi

# --- la copia zero ----------------------------------------------------------
if grep -q 'i fotogrammi arrivano come DMA-BUF' "$R"; then
    ok "i pixel passano dalla scheda: copia zero"
else
    ko "niente copia zero — a 4K sono 27 fotogrammi al secondo invece di 59 (kde.md §5.7)"
    grep -o 'i fotogrammi arrivano come.*' "$R" | head -1 | sed 's/^/       /'
fi
MOD=$(grep -o 'modificatore del formato: 0x[0-9a-f]*' "$R" | head -1)
[ -n "$MOD" ] && inf "$MOD (0x0 = lineare, che e' quello che il codificatore vuole)"

# --- la fence ---------------------------------------------------------------
RIASS=$(grep -o 'cattura su [0-9]* fotogrammi:.*' "$R" | tail -1)
if [ -n "$RIASS" ]; then
    inf "$RIASS"
    SCADUTE=$(echo "$RIASS" | grep -o 'attesa scaduta [0-9]*' | grep -o '[0-9]*')
    if [ "${SCADUTE:-0}" -eq 0 ]; then
        ok "l'attesa del disegno non e' mai scaduta: i fotogrammi codificati sono finiti"
    else
        ko "$SCADUTE fotogrammi codificati con il disegno ancora in corso"
    fi
else
    inf "meno di 300 fotogrammi: il riassunto della cattura non e' stato scritto"
fi

# --- i buffer di solo cursore ----------------------------------------------
if grep -q 'buffer di solo cursore' "$R"; then
    ok "i buffer di solo cursore vengono riconosciuti e scartati"
else
    inf "nessun buffer di solo cursore (il mouse non si e' mosso: e' il caso normale di un "
    inf "desktop non presidiato, e non prova che la guardia funzioni)"
fi

# --- il client --------------------------------------------------------------
if grep -q 'EGFX negoziato' "$R"; then
    ok "il client ha negoziato EGFX"
else
    ko "EGFX non negoziato: il client non ha di che disegnare"
fi
if [ "${RICEVUTI:-0}" -gt 0 ]; then
    ok "il client ha DECODIFICATO $RICEVUTI fotogrammi del desktop di KDE"
else
    ko "nessun fotogramma e' arrivato al client"
    tail -5 "$BASE/devroot/tmp/fase11-client.log" 2>/dev/null | sed 's/^/       /'
fi

# --- il palco sopravvive alla disconnessione (R9, §4.9 di kde.md) -----------
if grep -q 'palco smontato' "$R"; then
    ko "il palco e' stato smontato alla disconnessione: su KWin un UNCONNECTED smonta l'uscita"
else
    ok "il palco e' rimasto montato dopo che il client se n'e' andato"
fi

# ---------------------------------------------------------------------------
if [ "$MODO" = misura ]; then
titolo "6. Quanto consegna la cattura, con la scena in movimento"
# ---------------------------------------------------------------------------
# ⛔ LA SCENA SI DICHIARA, E SI MUOVE SEMPRE.  `weston-simple-egl -f` ridisegna a
#    ogni frame callback del compositore, cioe' chiede il pieno e costa quasi
#    niente di GPU.  E' la forma con cui sono stati misurati i 59 fotogrammi al
#    secondo di `kde.md` §5.7: usare la stessa e' l'unico modo perche' i due
#    numeri si possano confrontare.
WAYLAND_DISPLAY="$SOCKET" setsid nohup weston-simple-egl -f > "$LOG/scena.log" 2>&1 &
sleep 2
# ⛔ `pgrep -x` QUI NON FUNZIONA, e il difetto e' del banco non della scena:
#    `comm` e' troncato a 15 caratteri e «weston-simple-egl» ne ha 17, quindi il
#    confronto esatto fallisce sempre.  Il primo giro di questa misura ha
#    dichiarato «la scena non e' partita» mentre la cattura consegnava 58
#    fotogrammi al secondo — cioe' una prova rossa su un banco che funzionava,
#    che e' il difetto che `LEZIONI.md` §2.3 mette accanto a quello opposto.
if pgrep -f weston-simple-egl >/dev/null; then
    ok "scena in movimento a schermo intero"
else
    ko "la scena non e' partita: senza, quel che si misura e' un desktop fermo"
fi

# Un client tiene su il palco per tutta la misura: senza nessuno collegato il
# palco non esiste, e non c'e' niente da contare.
cnt "
    pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null
    Xvfb $DISPLAY_CLI -screen 0 2560x1440x24 >/dev/null 2>&1 &
    sleep 2
    DISPLAY=$DISPLAY_CLI timeout 40 xfreerdp3 /v:127.0.0.1:$PORTA \
        /size:$MISURA_CLIENT /gfx:AVC420 /cert:ignore /sec:tls /u:prova /p:prova \
        /log-level:WARN >/tmp/fase11-misura.log 2>&1
    pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null
    true"
pkill -f weston-simple-egl 2>/dev/null

# Il ritmo si ricava dai due riassunti della cattura, che escono ogni 300
# fotogrammi: la differenza fra i loro orari e' il tempo di 300 fotogrammi.
python3 - "$R" <<'FINE'
import re, sys, datetime
righe = []
for r in open(sys.argv[1], errors='replace'):
    m = re.match(r'(\d\d):(\d\d):(\d\d)\.(\d+).*cattura su (\d+) fotogrammi', r)
    if m:
        h, mi, se, ms, n = (int(x) for x in m.groups())
        righe.append((h*3600 + mi*60 + se + ms/1000.0, n))
if len(righe) < 2:
    print("    --    meno di 600 fotogrammi consegnati: non c'e' abbastanza per un ritmo")
else:
    dt = righe[-1][0] - righe[0][0]
    dn = righe[-1][1] - righe[0][1]
    if dt > 0:
        print("    \033[1;32mOK\033[0m    la cattura consegna %.1f fotogrammi al secondo "
              "(%d fotogrammi in %.1f s)" % (dn/dt, dn, dt))
    else:
        print("    --    intervallo nullo: niente da dividere")
FINE
RIASS=$(grep -o 'cattura su [0-9]* fotogrammi:.*' "$R" | tail -1)
[ -n "$RIASS" ] && inf "$RIASS"
SCADUTE=$(echo "${RIASS:-}" | grep -o 'attesa scaduta [0-9]*' | grep -o '[0-9]*')
if [ -n "${SCADUTE:-}" ] && [ "${SCADUTE:-0}" -eq 0 ]; then
    ok "l'attesa del disegno non e' mai scaduta"
elif [ -n "${SCADUTE:-}" ]; then
    ko "$SCADUTE fotogrammi hanno atteso invano: si sarebbe codificato il fotogramma di prima"
fi
fi

# ---------------------------------------------------------------------------
if [ "$MODO" = sessione ]; then
titolo "7. Il logout: la sessione se ne va, e non lascia niente"
# ---------------------------------------------------------------------------
# ⛔ SI GUARDA CHE COSA RESTA, non che il comando sia tornato.  Su KDE la via
#    ordinata puo' ANNULLARSI DA SOLA — dopo dieci secondi KWin mostra una
#    notifica «Cancel Logout / Log Out Anyway» e, se nessuno risponde, aspetta
#    fino a DUE MINUTI (`kde.md` §6.5).  In una sessione non presidiata nessuno
#    risponde mai: il secondo passo — `StopUnit` — non e' un lusso.
if grep -q "unita' del compositore sovrascritta" "$R"; then
    ok "$(grep -o "unita' del compositore sovrascritta.*" "$R" | head -1)"
else
    ko "REMOTIX non ha scritto il drop-in: la sessione sarebbe partita con uno schermo vero"
fi
if grep -q 'avvio la sessione grafica' "$R"; then
    ok "$(grep -o 'avvio la sessione grafica.*' "$R" | head -1 | cut -c1-90)"
else
    ko "REMOTIX non ha avviato nessuna sessione"
fi
if grep -q 'sentinella dell.uscita: sorveglio org.kde.Shutdown' "$R"; then
    ok "la sentinella dell'uscita e' passiva: sorveglia un nome, non si registra"
else
    ko "nessuna sentinella dell'uscita: di un «Esci» ci si accorgerebbe tardi"
fi
if grep -q 'schermo della sessione tenuto acceso' "$R"; then
    ok "$(grep -o 'schermo della sessione tenuto acceso.*' "$R" | head -1)"
else
    ko "nessuna inibizione: dopo dieci minuti lo schermo si spegne da se'"
fi
if pgrep -f 'kwin_wayland.*--no-lockscreen' >/dev/null; then
    ok "il compositore gira senza schermo di blocco"
else
    ko "manca --no-lockscreen: a blocco attivo powerdevil ignora l'inibizione"
fi
RENDERER=$(gdbus call --session --dest org.kde.KWin --object-path /KWin \
    --method org.kde.KWin.supportInformation 2>/dev/null \
    | grep -aoE 'OpenGL renderer string: [^\\]*' | head -1)
[ -n "$RENDERER" ] && ok "$RENDERER" || ko "KWin non dichiara nessun renderer OpenGL"

inf "adesso l'«Esci», dall'interno della sessione"
gdbus call --session --dest org.kde.Shutdown --object-path /Shutdown \
    --method org.kde.Shutdown.logout >/dev/null 2>&1
for i in $(seq 30); do pgrep -x plasmashell >/dev/null || break; sleep 1; done
sleep 3
if grep -q 'la sessione di KDE sta uscendo' "$R"; then
    ok "REMOTIX se n'e' accorto SUBITO, non alla morte della cattura"
else
    ko "l'uscita non e' stata annunciata: il client resterebbe su un'immagine congelata"
fi
RESTANO=$(pgrep -x plasmashell kwin_wayland ksmserver kded6 2>/dev/null | wc -l)
if [ "$RESTANO" -eq 0 ]; then
    ok "il logout non ha lasciato processi"
else
    ko "$RESTANO processi della sessione sono rimasti in piedi"
    pgrep -a -x plasmashell kwin_wayland ksmserver kded6 2>/dev/null | sed 's/^/       /'
fi
if pgrep -x remotix >/dev/null; then
    ok "REMOTIX e' sopravvissuto al logout: puo' riaprire la sessione a chi torna"
else
    ko "REMOTIX e' morto col logout: chi torna non trova nessuno in ascolto"
fi
fi

# ---------------------------------------------------------------------------
titolo "Esito"
# ---------------------------------------------------------------------------
inf "registri in $LOG (remotix.log, kwin.log, plasma.log)"
if [ "$GUASTI" -eq 0 ]; then
    printf '    \033[1;32mtutti i controlli passati\033[0m\n'
else
    printf '    \033[1;31m%d controlli falliti\033[0m\n' "$GUASTI"
fi
exit $((GUASTI > 0))
