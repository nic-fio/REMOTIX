#!/bin/bash
#
# Prova della fase 4: il desktop si comanda?
#
# Va eseguita SUL SERVER, come la fase 3, perche' mette insieme la VM (dove c'e'
# GNOME e gira REMOTIX) e il contenitore (dove c'e' il client).
#
#   bash /media/REMOTIX/src/remotix-c/prove/fase4.sh
#
# ⚠ LE PROVE AUTOMATICHE CON xdotool MENTONO, e il documento lo dice da prima
#   che questa prova esistesse (§5.8 di SPECIFICA.md):
#
#     - perde di tanto in tanto la prima battuta di una raffica mandata subito
#       dopo un clic;
#     - il client consegna a volte la posizione PRECEDENTE del puntatore.
#
#   Da cui la regola per chi misura l'input: **si cerca la coppia di letture
#   attesa, non la prima e l'ultima**, e si manda un movimento di spurgo che
#   faccia uscire quello tenuto indietro.  Questa prova fa entrambe le cose.
#
# Il registro va a livello `traccia`, che annota OGNI tasto: e' a tutti gli
# effetti un registratore di battitura.  Sta a `traccia` apposta, e qui si usa
# perche' e' un banco, non un server.
set -u

BASE=/media/REMOTIX
BIN_LOCALE="$BASE/src/remotix-c/build/src/remotix"
MISURA=${MISURA:-1282x802}
PORTA=3389
DISPLAY_CLI=:108
TITOLO=REMOTIXPROVA
BANCO=/srv/remotix/tmp/banco-b

# ⚠ Lo standard input va staccato: `ssh` senza `-n` eredita quello dello
# script, e quando quello e' un terminale che non finisce mai la sessione
# remota resta aperta anche dopo che il comando e' finito.  Il sintomo e' un
# passo che «non torna» pur essendo gia' andato a buon fine.
# Da dove si comanda la macchina di runtime: dal 6 agosto 2026 e' il server
# stesso (§6.2 di SPECIFICA.md).  `RUNTIME=vm` riporta i banchi sulla VM.
. "$(dirname "$0")/runtime.sh"
cnt() { bash "$BASE/enter.sh" "$@"; }

titolo() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()     { printf '    \033[1;32mOK\033[0m    %s\n' "$*"; }
ko()     { printf '    \033[1;31mNO\033[0m    %s\n' "$*"; GUASTI=$((GUASTI+1)); }
GUASTI=0

[ -x "$BIN_LOCALE" ] || { echo "manca $BIN_LOCALE: costruiscilo prima"; exit 1; }
bash "$BASE/enter.sh" true || exit 1

# ---------------------------------------------------------------------------
titolo "1. REMOTIX nella VM, con il registro a «traccia»"
# ---------------------------------------------------------------------------
vm "pkill -x remotix; sleep 1" >/dev/null 2>&1
copia "$BIN_LOCALE" >/dev/null || exit 1
# L'avvio passa per uno script nella VM, come la fase 3: un comando inline che
# mette qualcosa in secondo piano lascia la sessione SSH appesa alle pipe che
# quel qualcosa ha ereditato, e la si scopre come un passo che non torna.
cat > "$BASE/tmp/avvia-traccia.sh" <<'AVVIO'
#!/bin/bash
cd "$HOME" || exit 1
pkill -x remotix 2>/dev/null
sleep 1
rm -f "$HOME/remotix.log"
setsid nohup ./remotix --porta 3389 --registro traccia --senza-autenticazione \
    >"$HOME/remotix.log" 2>&1 </dev/null &
sleep 3
pgrep -x remotix >/dev/null && echo "   REMOTIX avviato" || { echo "   NON avviato"; exit 1; }
AVVIO
copia "$BASE/tmp/avvia-traccia.sh" >/dev/null || exit 1
vm "bash avvia-traccia.sh" || exit 1

# ---------------------------------------------------------------------------
titolo "2. Client, e poi si comanda"
# ---------------------------------------------------------------------------
# Il pattern di pkill e' ANCORATO: senza, «pkill -f» trova la stringa nella
# riga di comando della shell che esegue questo blocco e la shell si uccide da
# sola — costato un giro alla fase 3.
cnt "
    pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null; sleep 1
    Xvfb $DISPLAY_CLI -screen 0 1500x1000x24 -nolisten tcp >/dev/null 2>&1 &
    sleep 2
    export DISPLAY=$DISPLAY_CLI
    cd $BANCO
    timeout 75 xfreerdp3 /v:127.0.0.1:$PORTA /gfx:AVC420 /cert:ignore /sec:tls \
        /u:prova /p:prova /size:$MISURA /title:$TITOLO /log-level:WARN >fase4-client.log 2>&1 &
    sleep 12

    FIN=\$(xdotool search --name $TITOLO | head -1)
    if [ -z \"\$FIN\" ]; then echo '   !! finestra del client non trovata'; exit 1; fi
    xdotool windowfocus \$FIN; xdotool windowactivate \$FIN 2>/dev/null
    echo \"   finestra \$FIN: \$(xdotool getwindowgeometry \$FIN | tr '\n' ' ')\"

    # --- tastiera: Super apre la panoramica, poi si scrive ------------------
    xdotool key --window \$FIN --clearmodifiers super; sleep 2
    xdotool type --window \$FIN --delay 120 'remotix'; sleep 2
    xwd -root -silent > fase4-tastiera.xwd 2>/dev/null
    ffmpeg -y -loglevel error -i fase4-tastiera.xwd fase4-tastiera.png
    xdotool key --window \$FIN --clearmodifiers Escape; sleep 1

    # --- puntatore: spurgo, poi tre posizioni distinte ----------------------
    # Lo spurgo fa uscire la lettura tenuta indietro dal client; le tre
    # posizioni si cercano poi COME COPPIA nel registro, non come prima e
    # ultima riga.
    xdotool mousemove --sync 5 5;       sleep 1
    xdotool mousemove --sync 300 200;   sleep 1
    xdotool mousemove --sync 900 640;   sleep 1
    xdotool mousemove --sync 1100 100;  sleep 1
    xdotool mousemove --sync 5 5;       sleep 1

    # --- rotella: uno scatto in su' e uno in giu' ---------------------------
    xdotool mousemove --sync 600 400; sleep 1
    xdotool click 4; sleep 1
    xdotool click 5; sleep 1

    # --- un clic vero, sullo sfondo del desktop, dove non apre nulla --------
    xdotool click 1; sleep 1

    # --- si tiene giu' un modificatore e si uccide il client di netto -------
    xdotool keydown --window \$FIN shift; sleep 1
    pkill -f '^timeout 75 xfreerdp3' 2>/dev/null
    pkill -x xfreerdp3 2>/dev/null
    sleep 3
    pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null
    echo '   comandi inviati'
"

# ---------------------------------------------------------------------------
titolo "3. Il verdetto, letto nel registro del server"
# ---------------------------------------------------------------------------
REG=$(vm "cat ~/remotix.log" 2>/dev/null)
vm "pkill -x remotix" >/dev/null 2>&1
contiene() { printf '%s\n' "$REG" | grep -qF "$1"; }
conta()    { printf '%s\n' "$REG" | grep -cF "$1"; }

if contiene "canale di input aperto verso il compositore"; then
    ok "il canale libei si e' aperto"
else
    ko "nessun canale libei: ConnectToEIS non ha funzionato"
fi

if contiene "tastiera e mouse collegati alla sessione"; then
    ok "i gestori d'input sono stati installati"
else
    ko "i gestori d'input non sono stati installati"
fi

DISP=$(printf '%s\n' "$REG" | grep -F "disposizione della sessione letta da libei" | head -1)
if [ -n "$DISP" ]; then
    ok "${DISP#* INFO    }"
else
    ko "la disposizione di tastiera non e' stata letta: il percorso Unicode e' spento"
fi

REGIONE=$(printf '%s\n' "$REG" | grep -F "regione del puntatore" | head -1)
if [ -n "$REGIONE" ]; then
    ok "${REGIONE#* DIAGN   }"
else
    ko "nessuna regione libei: le coordinate non vengono riscalate"
fi

N_TASTI=$(conta "tasto evdev")
if [ "$N_TASTI" -ge 10 ]; then
    ok "$N_TASTI eventi di tastiera inoltrati al compositore"
else
    ko "solo $N_TASTI eventi di tastiera: la tastiera non passa"
fi

# La coppia attesa, non la prima e l'ultima riga.
MANCANTI=""
for punto in "x=300.0 y=200.0" "x=900.0 y=640.0" "x=1100.0 y=100.0"; do
    contiene "puntatore $punto" || MANCANTI="$MANCANTI [$punto]"
done
if [ -z "$MANCANTI" ]; then
    ok "le tre posizioni del puntatore sono arrivate esatte"
else
    ko "posizioni del puntatore mancanti:$MANCANTI"
fi

# Uno scatto deve valere UNO scatto: il canale di input avanzato di FreeRDP
# porta le stesse unita' moltiplicate per 0x10000, e preso alla lettera uno
# scatto varrebbe 7 864 320 — che Mutter scarta senza dire perche'.
if contiene "asse dx=0 dy=-10" && contiene "asse dx=0 dy=10"; then
    ok "la rotella: uno scatto vale uno scatto, nei due versi"
else
    ko "la rotella non e' arrivata come attesa (servono «asse dx=0 dy=-10» e «dy=10»)"
fi

# 272 e' BTN_LEFT (0x110) in `linux/input-event-codes.h`.
if contiene "bottone 272 giu'" && contiene "bottone 272 su'"; then
    ok "il clic arriva, premuto e rilasciato"
else
    ko "il clic non e' arrivato appaiato (servono «bottone 272 giu'» e «su'»)"
fi

if contiene "rilascio quel che era rimasto premuto"; then
    ok "$(printf '%s\n' "$REG" | grep -F 'rilascio quel che era rimasto premuto' | head -1 | sed 's/^[^ ]* *[A-Z]* *//')"
else
    ko "niente e' stato rilasciato a fine connessione: lo stato resta sporco"
fi

# ---------------------------------------------------------------------------
titolo "4. Che cosa dice la sessione remota"
# ---------------------------------------------------------------------------
SESS=$(vm "grep -iE 'invalid key|libei|eis' /run/user/1000/remotix-sessione.log 2>/dev/null | tail -5")
if [ -n "$SESS" ]; then
    printf '%s\n' "$SESS" | sed 's/^/    /'
else
    ok "nessuna lamentela da Mutter sugli eventi ricevuti"
fi

# ---------------------------------------------------------------------------
# ⛔ LA PROVA NON LASCIA LA MACCHINA SPENTA.
#
# Questa prova avvia REMOTIX a mano, con il registro a «traccia», e alla fine
# lo lasciava giu'.  Chi finisce la suite va a provare a mano dai tre client,
# trova la porta muta e legge «server morto» — cioe' il contrario di quello che
# la prova ha appena dimostrato.
#
# La regola sta in fondo a `fase5.sh`, dove e' stata scritta il 4 agosto dopo
# averla pagata una volta.  Il 5 agosto e' stata pagata una seconda volta,
# perche' qui e in `fase3.sh` non era mai stata applicata: una regola scritta
# in un posto solo vale solo in quel posto.
#
# Si riavvia il SERVIZIO, che riporta anche il registro al livello normale: il
# livello «traccia» annota ogni tasto, ed e' un registratore di battitura che
# non deve restare acceso su una macchina che si usa a mano.
# ---------------------------------------------------------------------------
vm "sudo systemctl restart remotix.service; sleep 2" >/dev/null 2>&1
if vm "systemctl is-active --quiet remotix.service"; then
    echo "    il server e' stato riavviato: la macchina resta pronta per la prova a mano"
else
    echo "    ATTENZIONE: il server NON e' ripartito, la macchina resta senza"
fi

echo
echo "    La fotografia della panoramica con «remotix» scritto sta in"
echo "    $BASE/tmp/banco-b/fase4-tastiera.png — e' la prova che la tastiera scrive."
echo
if [ "$GUASTI" -eq 0 ]; then
    printf '\033[1;32m==> tutti i controlli sono passati\033[0m\n'
else
    printf '\033[1;31m==> %d controlli falliti\033[0m\n' "$GUASTI"
fi
echo "    La prova che conta resta l'occhio, sui TRE client: si apre un terminale"
echo "    nella sessione remota e ci si scrive dentro."
exit $((GUASTI > 0))
