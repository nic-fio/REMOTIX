#!/bin/bash
#
# Prova della fase 3: REMOTIX manda il DESKTOP VERO?
#
# Va eseguita SUL SERVER, non nel contenitore, perche' mette insieme due
# macchine che sono distinte per vincolo (§6.2 di SPECIFICA.md):
#
#   - la VM di runtime, dove c'e' GNOME e dove gira REMOTIX;
#   - il contenitore di sviluppo, dove c'e' il client FreeRDP strumentato.
#
#   bash /media/REMOTIX/src/remotix-c/prove/fase3.sh
#
# Cosa guarda, in ordine di importanza:
#
#   1. la sequenza di Mutter e' andata a buon fine (nodo PipeWire annunciato);
#   2. la MISURA NEGOZIATA e' quella chiesta — e' la divergenza aperta di §11.1
#      di gnome-remote-desktop.md, rettangolo singolo contro intervallo chiuso;
#   3. i fotogrammi arrivano al client;
#   4. R9: alla SECONDA connessione il desktop ricompare all'istante, su un
#      desktop fermo, perche' l'ultimo fotogramma e' stato conservato;
#   5. il palco NON viene smontato alla disconnessione — se lo fosse, Mutter
#      resterebbe con zero schermi e nel registro della Shell comparirebbe
#      «Removed virtual monitor».
set -u

BASE=/media/REMOTIX
BIN_LOCALE="$BASE/src/remotix-c/build/src/remotix"
MISURA=${MISURA:-1282x802}
GFX=${GFX:-AVC420}
PORTA=3389            # inoltrata da QEMU: 127.0.0.1:3389 sul server = la VM
DISPLAY_CLI=:103
BANCO=/srv/remotix/tmp/banco-b

# Da dove si comanda la macchina di runtime: dal 6 agosto 2026 e' il server
# stesso (§6.2 di SPECIFICA.md).  `RUNTIME=vm` riporta i banchi sulla VM.
. "$(dirname "$0")/runtime.sh"
cnt() { bash "$BASE/enter.sh" "$@"; }

titolo() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()     { printf '    \033[1;32mOK\033[0m    %s\n' "$*"; }
ko()     { printf '    \033[1;31mNO\033[0m    %s\n' "$*"; GUASTI=$((GUASTI+1)); }
inf()    { printf '    --    %s\n' "$*"; }
GUASTI=0

[ -x "$BIN_LOCALE" ] || { echo "manca $BIN_LOCALE: costruiscilo prima"; exit 1; }

# Le credenziali di sudo si prendono ADESSO, con una chiamata che non redirige
# nulla.  Piu' avanti l'uscita del contenitore passa per delle pipe, e la
# richiesta di password di sudo finita in una pipe lascia appeso per sempre chi
# la deve fornire, in silenzio: e' una delle avvertenze pagate della fase 1.
bash "$BASE/enter.sh" true || exit 1

# ---------------------------------------------------------------------------
titolo "1. Porto il binario nella VM e lo avvio"
# ---------------------------------------------------------------------------
# Prima si ferma quello vecchio: un binario in esecuzione non si sovrascrive,
# e scp fallisce con un «dest open: Failure» che non nomina la causa.
vm "pkill -x remotix; sleep 1" >/dev/null 2>&1
copia "$BIN_LOCALE" >/dev/null || exit 1
vm "rm -f ~/remotix.log; bash avvia-remotix.sh --aperto" || exit 1

# ---------------------------------------------------------------------------
titolo "2. Prima connessione (il desktop si allestisce da zero)"
# ---------------------------------------------------------------------------
cnt "
    # Il pattern e' ANCORATO, e non e' pignoleria: senza l'accento circonflesso
    # «pkill -f» trova la stringa anche nella riga di comando della shell che
    # sta eseguendo questo blocco, e la shell si uccide da sola.  Il sintomo e'
    # un blocco che non stampa nulla e un «Terminated» comparso altrove.
    pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null
    Xvfb $DISPLAY_CLI -screen 0 1400x900x24 -nolisten tcp >/dev/null 2>&1 &
    sleep 2
    cd $BANCO && rm -f fase3-rect.txt fase3-prog.txt
    DISPLAY=$DISPLAY_CLI \
    LD_PRELOAD='$BANCO/spia-progressive.so:$BANCO/spia-avc420.so' \
    SPIA_PROGRESSIVE='$BANCO/fase3-prog.txt' SPIA_AVC420='$BANCO/fase3-rect.txt' \
        timeout 25 xfreerdp3 /v:127.0.0.1:$PORTA /gfx:$GFX /cert:ignore /sec:tls \
        /u:prova /p:prova /size:$MISURA /log-level:WARN >fase3-client.log 2>&1
    echo \"   fotogrammi ricevuti: \$(grep -c '^fotogramma' fase3-rect.txt 2>/dev/null || echo 0) AVC420, \$(wc -l < fase3-prog.txt 2>/dev/null || echo 0) Progressive\"
"

# ---------------------------------------------------------------------------
titolo "3. Seconda connessione — R9: il desktop deve ricomparire all'istante"
# ---------------------------------------------------------------------------
# Il desktop e' fermo, quindi Mutter non manda nulla di nuovo: se qualcosa
# arriva, e' l'ultimo fotogramma conservato.  Bastano 6 secondi.
cnt "
    cd $BANCO && rm -f fase3b-rect.txt fase3b-prog.txt
    DISPLAY=$DISPLAY_CLI \
    LD_PRELOAD='$BANCO/spia-progressive.so:$BANCO/spia-avc420.so' \
    SPIA_PROGRESSIVE='$BANCO/fase3b-prog.txt' SPIA_AVC420='$BANCO/fase3b-rect.txt' \
        timeout 8 xfreerdp3 /v:127.0.0.1:$PORTA /gfx:$GFX /cert:ignore /sec:tls \
        /u:prova /p:prova /size:$MISURA /log-level:WARN >fase3b-client.log 2>&1
    echo \"   fotogrammi ricevuti: \$(grep -c '^fotogramma' fase3b-rect.txt 2>/dev/null || echo 0) AVC420, \$(wc -l < fase3b-prog.txt 2>/dev/null || echo 0) Progressive\"
    pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null
"

# ---------------------------------------------------------------------------
titolo "4. Il verdetto, letto nel registro del server"
# ---------------------------------------------------------------------------
REG=$(vm "cat ~/remotix.log" 2>/dev/null)
vm "pkill -x remotix" >/dev/null 2>&1

righe() { printf '%s\n' "$REG" | grep -F "$1"; }
contiene() { printf '%s\n' "$REG" | grep -qF "$1"; }

if contiene "monitor virtuale montato"; then
    ok "$(righe 'monitor virtuale montato' | head -1 | sed 's/^[^ ]* *[A-Z]* *//')"
else
    ko "la sequenza di Mutter non e' arrivata in fondo: nessun nodo PipeWire"
fi

NEGOZIATA=$(righe 'formato negoziato con Mutter' | head -1 | grep -oE '[0-9]+x[0-9]+')
if [ -n "$NEGOZIATA" ]; then
    if [ "$NEGOZIATA" = "$MISURA" ]; then
        ok "misura negoziata $NEGOZIATA, cioe' quella chiesta"
    else
        ko "misura negoziata $NEGOZIATA invece di $MISURA — vedi §11.1 di gnome-remote-desktop.md"
    fi
else
    ko "Mutter non ha negoziato alcun formato"
fi

if contiene "primo fotogramma dal desktop"; then
    ok "$(righe 'primo fotogramma dal desktop' | head -1 | sed 's/^[^ ]* *[A-Z]* *//')"
else
    ko "nessun fotogramma e' mai arrivato dal desktop"
fi

if contiene "palco gia' montato della misura giusta"; then
    ok "alla seconda connessione il palco e' stato RIUSATO (R9, riaggancio)"
else
    ko "il palco e' stato rimontato alla seconda connessione: il desktop non ricompare all'istante"
fi

if contiene "immagine di prova" || contiene "SCENA SINTETICA"; then
    ko "il server stava mandando la scena sintetica, non il desktop"
else
    ok "il server mandava il desktop, non la scena sintetica"
fi

# ---------------------------------------------------------------------------
titolo "5. Il palco resta montato fra un client e l'altro"
# ---------------------------------------------------------------------------
# Se venisse smontato, Mutter resterebbe con zero schermi e da li' partirebbero
# le asserzioni fallite di libmutter: le applicazioni aperte perdono la
# connessione Wayland e quelle nuove non hanno dove aprirsi (questione n.5).
SHELL_LOG=$(vm "cat /run/user/1000/remotix-sessione.log 2>/dev/null | tail -200")
if printf '%s\n' "$SHELL_LOG" | grep -q "Removed virtual monitor"; then
    ko "la Shell ha registrato «Removed virtual monitor»: il palco e' stato smontato"
else
    ok "nessun «Removed virtual monitor» nel registro della Shell"
fi
if printf '%s\n' "$SHELL_LOG" | grep -q "assertion.*logical_monitor"; then
    ko "libmutter e' andata in asserzione fallita: e' il difetto dello schermo mancante"
else
    ok "nessuna asserzione fallita in libmutter"
fi

# ---------------------------------------------------------------------------
titolo "Registro del server, in coda"
# ---------------------------------------------------------------------------
printf '%s\n' "$REG" | grep -vE 'TRACC' | tail -25

# ---------------------------------------------------------------------------
# ⛔ LA PROVA NON LASCIA LA MACCHINA SPENTA.
#
# Questa prova avvia REMOTIX a mano e alla fine lo lasciava giu'.  Era
# tecnicamente corretto e praticamente una trappola: chi finisce la suite va a
# provare a mano dai tre client, trova la porta muta e legge «server morto» —
# cioe' il contrario di quello che la prova ha appena dimostrato.
#
# La regola sta in fondo a `fase5.sh`, dove e' stata scritta il 4 agosto dopo
# averla pagata una volta.  Il 5 agosto e' stata pagata una seconda volta,
# perche' qui e in `fase4.sh` non era mai stata applicata: una regola scritta
# in un posto solo vale solo in quel posto.
# ---------------------------------------------------------------------------
vm "sudo systemctl restart remotix.service; sleep 2" >/dev/null 2>&1
if vm "systemctl is-active --quiet remotix.service"; then
    echo "    il server e' stato riavviato: la macchina resta pronta per la prova a mano"
else
    echo "    ATTENZIONE: il server NON e' ripartito, la macchina resta senza"
fi

echo
if [ "$GUASTI" -eq 0 ]; then
    printf '\033[1;32m==> tutti i controlli sono passati\033[0m\n'
else
    printf '\033[1;31m==> %d controlli falliti\033[0m\n' "$GUASTI"
fi
echo "    La prova che conta resta l'occhio, sui TRE client: xfreerdp3, mstsc, RDM."
exit $((GUASTI > 0))
