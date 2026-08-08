#!/bin/bash
#
# Prova della fase 5: la sessione vive, e le regole d'accesso valgono.
#
#   bash /media/REMOTIX/src/remotix-c/prove/fase5.sh
#
# Il pezzo di riguardo e' il LOGOUT, e il numero che conta e' uno solo: quanto
# passa fra «la sessione sta uscendo» e «connessione conclusa».  Si misura
# dentro il registro del server, cioe' con UN SOLO orologio: la VM e il server
# sono due macchine, e confrontare i loro tempi darebbe un numero che non
# significa niente.
#
# ⚠ La sezione «Logout» della prova precedente e' rimasta VERDE per tutto il
#   tempo in cui il difetto c'era, perche' verificava che `xfreerdp3` morisse —
#   e xfreerdp alla chiusura del socket esce da solo.  Collaudava cioe' l'unico
#   dei tre client che tollerava l'omissione.  Qui si misura a decimi di secondo
#   E si verifica che il client abbia ricevuto il MOTIVO, non solo una chiusura.
set -u

BASE=/media/REMOTIX
BIN_LOCALE="$BASE/src/remotix-c/build/src/remotix"
MISURA=${MISURA:-1282x802}
PORTA=3389
DISPLAY_CLI=:109
BANCO=/srv/remotix/tmp/banco-b       # come lo vede il contenitore
BANCO_FUORI=/media/REMOTIX/tmp/banco-b   # la stessa cartella, vista dal server

# ⚠ DUE REGOLE SUL PILOTARE QUESTI DUE AMBIENTI DA FUORI, entrambe pagate:
#
#   1. `ssh` senza `-n` eredita lo standard input dello script: staccarlo evita
#      che la sessione remota resti aperta dopo che il comando e' finito.
#   2. L'uscita di `enter.sh` NON si mette mai in una pipe ne' in un `$(...)`:
#      la' dentro finisce anche la richiesta di password di `sudo`, e chi la
#      deve fornire resta appeso per sempre, in silenzio.  Per questo i
#      controlli leggono i registri del client DAL SERVER — la cartella e' la
#      stessa, vista con due nomi — invece di chiederli al contenitore.
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
bash "$BASE/enter.sh" true || exit 1

# ⚠ Il server ora e' un'unita' systemd: si ferma con `systemctl stop`, non con
# `pkill`.  Ucciderlo a mano lo fa uscire con errore, e `Restart=on-failure` lo
# fa ripartire subito su una porta che il successore sta gia' prendendo: il
# risultato e' un ciclo di riavvii (visto salire a 33) in cui `pgrep` trova il
# server ora si' ora no.
avvia_server() {
    vm "sudo systemctl stop remotix.service 2>/dev/null; sleep 1" >/dev/null 2>&1
    vm "rm -f ~/remotix.log; bash avvia-remotix.sh --aperto" >/dev/null || exit 1
}
client_sfondo() {   # $1 = nome del registro
    cnt "
        pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null; sleep 1
        Xvfb $DISPLAY_CLI -screen 0 1500x1000x24 -nolisten tcp >/dev/null 2>&1 &
        sleep 2
        cd $BANCO
        setsid nohup env DISPLAY=$DISPLAY_CLI xfreerdp3 /v:127.0.0.1:$PORTA /gfx:AVC420 \
            /cert:ignore /sec:tls /u:prova /p:prova /size:$MISURA /log-level:INFO \
            >$1 2>&1 </dev/null &
        sleep 1
        echo '   client avviato'
    "
}

# ===========================================================================
titolo "1. Logout: il client deve cadere subito, e sapere perche'"
# ===========================================================================
# Il binario si ferma PRIMA di sovrascriverlo: un eseguibile in esecuzione non
# si rimpiazza, e scp fallisce con un «dest open: Failure» che non nomina la
# causa.
vm "sudo systemctl stop remotix.service 2>/dev/null; sleep 1" >/dev/null 2>&1
copia "$BIN_LOCALE" >/dev/null || exit 1
avvia_server
client_sfondo fase5-logout.log
inf "aspetto che il desktop sia in piedi e che ci si registri con gnome-session"
sleep 20

vm "gdbus call --session --dest org.gnome.SessionManager \
      --object-path /org/gnome/SessionManager \
      --method org.gnome.SessionManager.Logout 1" >/dev/null 2>&1 \
    && inf "«Esci» richiesto" || ko "Logout non richiesto: la sessione non risponde"
sleep 8

cnt "pgrep -x xfreerdp3 >/dev/null && echo '   il client e ancora vivo' || echo '   il client e caduto'"
REG=$(vm "cat ~/remotix.log")

if printf '%s\n' "$REG" | grep -qF "registrati con gnome-session"; then
    ok "registrati con gnome-session: l'uscita si sa subito"
else
    ko "NON registrati con gnome-session: dell'uscita ci si accorge alla morte della cattura"
fi

USCITA=$(printf '%s\n' "$REG" | grep -F "la sessione grafica sta uscendo" | head -1 | cut -d' ' -f1)
FINE=$(printf '%s\n' "$REG" | grep -F "connessione conclusa" | head -1 | cut -d' ' -f1)
if [ -n "$USCITA" ] && [ -n "$FINE" ]; then
    DELTA=$(vm "python3 -c \"
from datetime import datetime as d
a=d.strptime('$USCITA','%H:%M:%S.%f'); b=d.strptime('$FINE','%H:%M:%S.%f')
print('%.2f'%((b-a).total_seconds()))\"" 2>/dev/null | tr -d '\r')
    if [ -n "$DELTA" ] && awk "BEGIN{exit !($DELTA <= 2.0)}"; then
        ok "il client e' caduto ${DELTA}s dopo l'annuncio dell'uscita (soglia: 2 s)"
    else
        ko "il client e' caduto dopo ${DELTA:-?}s: troppo tardi"
    fi
else
    ko "l'annuncio dell'uscita non c'e' nel registro (era: «la sessione grafica sta uscendo»)"
fi

# Il motivo, non solo la chiusura: e' cio' che distingue questa prova da quella
# che restava verde.
if grep -q ERRINFO_LOGOFF_BY_USER "$BANCO_FUORI/fase5-logout.log" 2>/dev/null; then
    ok "il client ha ricevuto ERRINFO_LOGOFF_BY_USER: sa PERCHE' e' finita"
else
    ko "il client non ha ricevuto alcun motivo: e' il difetto che lascia Android a fissare lo schermo"
fi

if printf '%s\n' "$REG" | grep -qF "palco smontato"; then
    ok "il palco e' stato smontato: chi si ricollega ne trova uno nuovo"
else
    ko "il palco non e' stato smontato: chi si ricollega lo troverebbe «gia' montato» — schermo nero"
fi

# -------------------------------------------------------------------------
# ⛔ IL CONTROLLO CHE MANCAVA, ED E' QUELLO CHE L'UTENTE HA VISTO ROMPERSI.
#
# Dopo un «Esci» REMOTIX deve RESTARE IN PIEDI: alla connessione successiva e'
# lui che riavvia la sessione (§5.9-bis di SPECIFICA.md).  Se muore, l'utente
# si ritrova un server morto e nessun desktop, e non c'e' piu' nessuno che
# possa rimediare.
#
# Il difetto era il prezzo nascosto di `RegisterClient`: registrandosi, si dice
# a gnome-session «sono una tua applicazione», e alla fine della sessione lui
# fa con noi quel che fa con le applicazioni.  Ora ci si sfila con
# `UnregisterClient` appena si sa che la sessione sta finendo.
# -------------------------------------------------------------------------
if vm "pgrep -x remotix >/dev/null"; then
    ok "REMOTIX e' sopravvissuto al logout: puo' riaprire la sessione a chi torna"
else
    ko "REMOTIX E' MORTO col logout: chi torna trova un server spento"
fi
if printf '%s\n' "$REG" | grep -qE "arrivato SIG"; then
    inf "$(printf '%s\n' "$REG" | grep -E 'arrivato SIG' | head -1 | sed 's/^[^ ]* *[A-Z]* *//')"
fi

# -------------------------------------------------------------------------
titolo "1-bis. Chi torna dopo il logout ritrova un desktop"
# -------------------------------------------------------------------------
if vm "pgrep -x remotix >/dev/null"; then
    cnt "
        pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null; sleep 1
        Xvfb $DISPLAY_CLI -screen 0 1500x1000x24 -nolisten tcp >/dev/null 2>&1 &
        sleep 2
        cd $BANCO
        DISPLAY=$DISPLAY_CLI timeout 60 xfreerdp3 /v:127.0.0.1:$PORTA /gfx:AVC420 /cert:ignore \
            /sec:tls /u:prova /p:prova /size:$MISURA /log-level:WARN >fase5-ritorno.log 2>&1
        echo '   client di ritorno concluso'
    "
    REG=$(vm "cat ~/remotix.log")
    if printf '%s\n' "$REG" | grep -qF "nessuna sessione grafica: la avvio"; then
        ok "la sessione e' stata riavviata da REMOTIX per chi e' tornato"
    else
        ko "nessuna sessione riavviata: chi torna non trova un desktop"
    fi
    if [ "$(printf '%s\n' "$REG" | grep -cF 'palco montato')" -ge 2 ]; then
        ok "il palco e' stato rimontato sulla sessione nuova"
    else
        ko "il palco non e' stato rimontato"
    fi
else
    ko "non si puo' provare il ritorno: il server non c'e' piu'"
fi

# ===========================================================================
titolo "2. La seconda connessione viene rifiutata, e con un messaggio"
# ===========================================================================
avvia_server
client_sfondo fase5-primo.log
sleep 18

cnt "
    cd $BANCO
    DISPLAY=$DISPLAY_CLI timeout 20 xfreerdp3 /v:127.0.0.1:$PORTA /gfx:AVC420 /cert:ignore \
        /sec:tls /u:prova /p:prova /size:$MISURA /log-level:INFO >fase5-secondo.log 2>&1
    echo \"   il secondo client e' uscito con \$?\"
"
REG=$(vm "cat ~/remotix.log")

if printf '%s\n' "$REG" | grep -qF "rifiuto: c'e' gia' un client collegato"; then
    ok "il portiere ha rifiutato la seconda connessione"
else
    ko "la seconda connessione NON e' stata rifiutata"
fi
if grep -q ERRINFO_SERVER_DENIED_CONNECTION "$BANCO_FUORI/fase5-secondo.log" 2>/dev/null; then
    ok "il secondo client ha ricevuto ERRINFO_SERVER_DENIED_CONNECTION, non un errore di rete"
else
    ko "il secondo client non ha ricevuto il codice di rifiuto"
fi
# Il contenitore e' un chroot, non un namespace di processi: i suoi processi si
# vedono anche da qui.
if pgrep -x xfreerdp3 >/dev/null; then
    ok "il primo client non e' stato disturbato"
else
    ko "il primo client e' caduto: chi e' dentro non va toccato"
fi

# ===========================================================================
titolo "3. Riaggancio: chi torna ritrova il palco montato"
# ===========================================================================
cnt "pkill -x xfreerdp3 2>/dev/null; sleep 3; echo '   primo client chiuso'"
cnt "
    cd $BANCO
    DISPLAY=$DISPLAY_CLI timeout 12 xfreerdp3 /v:127.0.0.1:$PORTA /gfx:AVC420 /cert:ignore \
        /sec:tls /u:prova /p:prova /size:$MISURA /log-level:WARN >fase5-terzo.log 2>&1
    pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null
    echo '   terzo client concluso'
"
REG=$(vm "cat ~/remotix.log")

if [ "$(printf '%s\n' "$REG" | grep -cF "palco gia' montato della misura giusta")" -ge 1 ]; then
    ok "il palco e' stato riusato: il desktop ricompare all'istante, con le finestre dov'erano"
else
    ko "il palco e' stato rifatto: il riaggancio non funziona"
fi
if [ "$(printf '%s\n' "$REG" | grep -cF "monitor virtuale montato")" -le 1 ]; then
    ok "una sola «nuova sorgente» in tutta la sessione: e' la firma di una sessione sana"
else
    inf "$(printf '%s\n' "$REG" | grep -cF 'monitor virtuale montato') montaggi del monitor virtuale"
fi

# ===========================================================================
titolo "Registro del server, in coda"
# ===========================================================================
printf '%s\n' "$REG" | grep -vE 'libx264|TRACC' | tail -18

# ===========================================================================
# La prova NON lascia la macchina spenta.
#
# Fermare il servizio alla fine era tecnicamente corretto e praticamente una
# trappola: chi finisce la suite va a provare a mano dai tre client, trova la
# porta muta e legge «server morto» — che e' esattamente cio' che la fase 5
# esiste per non far succedere.  Costato una diagnosi il 4 agosto.
# ===========================================================================
vm "sudo systemctl restart remotix.service; sleep 1" >/dev/null 2>&1
if vm "systemctl is-active --quiet remotix.service"; then
    inf "il server e' stato riavviato: la macchina resta pronta per la prova a mano"
else
    inf "ATTENZIONE: il server NON e' ripartito, la macchina resta senza"
fi

echo
if [ "$GUASTI" -eq 0 ]; then
    printf '\033[1;32m==> tutti i controlli sono passati\033[0m\n'
else
    printf '\033[1;31m==> %d controlli falliti\033[0m\n' "$GUASTI"
fi
echo "    Restano da guardare a mano i casi 6 e 8 della tabella delle nove"
echo "    combinazioni — quelli che coinvolgono una sessione grafica LOCALE."
exit $((GUASTI > 0))
