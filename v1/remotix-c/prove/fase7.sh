#!/bin/bash
#
# Prova della fase 7: la misura della rete e il regolatore.
#
#   bash /media/REMOTIX/src/remotix-c/prove/fase7.sh
#
# ⚠ QUESTA PROVA USA LA SCENA SINTETICA ANCHE NELLA VM, e non e' pigrizia.
#
#   Quel che si misura qui e' il rapporto fra rete e fotogrammi, e serve un
#   produttore che non si fermi mai: un desktop vero, fermo, non manda niente e
#   il regolatore non ha nulla da regolare.  La scena sintetica disegna trenta
#   volte al secondo per sempre, quindi la strozzatura si vede subito e si vede
#   sola — §5.4 di SPECIFICA.md, isolare finche' il sospetto e' uno.
#   Che il palco vero regga la strozzatura lo dice la non regressione di fase 6.
#
# ⚠ SI STROZZA LA RETE DELLA VM, CHE E' ANCHE QUELLA DI SSH.
#   Per questo la rimozione del `tc` e' armata DUE volte: una alla fine della
#   sezione, e una a orologeria dentro la VM.  Senza la seconda, un guasto
#   dello script lascerebbe la macchina strozzata e la colpa sembrerebbe di
#   REMOTIX — che e' esattamente lo scambio di persona costato in fase 5.
#
# ⚠ LE DUE REGOLE DI FASE 5 SUL PILOTARE I DUE AMBIENTI VALGONO ANCHE QUI:
#   `ssh` senza `-n` eredita lo standard input dello script, e l'uscita di
#   `enter.sh` non si mette mai in una pipe.
set -u

BASE=/media/REMOTIX
BIN_LOCALE="$BASE/src/remotix-c/build/src/remotix"
BIN_CNT=/srv/src/remotix-c/build/src/remotix
PORTA=3389        # REMOTIX nella VM
PORTA_CNT=3390    # REMOTIX nel contenitore
DISPLAY_CLI=:110
TITOLO=REMOTIXFASE7
BANCO=/srv/remotix/tmp/banco-b          # come lo vede il contenitore
BANCO_FUORI=/media/REMOTIX/tmp/banco-b  # la stessa cartella, vista dal server
MISURA=${MISURA:-1282x802}

# La strozzatura.  Il ritardo serve piu' della banda: su una rete locale l'RTT
# e' vicino a zero e la soglia del regolatore resta al minimo, quindi senza
# ritardo la prova non distinguerebbe un regolatore che usa l'RTT da uno che
# non lo guarda affatto.
RITARDO_MS=${RITARDO_MS:-120}
# La banda si dichiara in kbit perche' deve MORDERE: a quattro megabit la scena
# sintetica passa intera e il regolatore non ha niente da fare, quindi la prova
# direbbe «non si e' bloccato» senza aver mai rallentato niente.
BANDA_KBIT=${BANDA_KBIT:-250}
IFACCIA=${IFACCIA:-enp0s2}

# Da dove si comanda la macchina di runtime: dal 6 agosto 2026 e' il server
# stesso (§6.2 di SPECIFICA.md).  `RUNTIME=vm` riporta i banchi sulla VM.
. "$(dirname "$0")/runtime.sh"
cnt() { bash "$BASE/enter.sh" "$@"; }

titolo() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()     { printf '    \033[1;32mOK\033[0m    %s\n' "$*"; }
ko()     { printf '    \033[1;31mNO\033[0m    %s\n' "$*"; GUASTI=$((GUASTI+1)); }
inf()    { printf '    --    %s\n' "$*"; }
GUASTI=0

conta() { printf '%s\n' "$1" | grep -cF "$2"; }

# L'ultimo valore di un campo del riassunto della rete.  Il riassunto ha una
# forma sola — «rete: RTT 0.2 ms (minimo 0.1), banda 80 kbit/s, in volo 1 di 2,
# spediti 412» — e si legge con un'espressione sola invece che con cinque.
campo() { # $1 = registro   $2 = etichetta   -> l'ultimo valore, intero
    printf '%s\n' "$1" | grep -F 'rete: RTT' | tail -1 \
        | grep -oE "$2 [0-9]+" | grep -oE '[0-9]+' | tail -1
}
rtt_intero() { # l'RTT medio in ms, arrotondato per difetto
    printf '%s\n' "$1" | grep -F 'rete: RTT' | tail -1 \
        | sed -n 's/.*rete: RTT \([0-9]*\)\..*/\1/p'
}

[ -x "$BIN_LOCALE" ] || { echo "manca $BIN_LOCALE: costruiscilo prima"; exit 1; }
mkdir -p "$BANCO_FUORI"
bash "$BASE/enter.sh" true || exit 1

# ===========================================================================
# Gli script che girano DENTRO il contenitore.
# ===========================================================================
cat > "$BANCO_FUORI/fase7-client.sh" <<CLIENT
#!/bin/bash
# \$1 = porta   \$2 = nome del registro del client
set -u
pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null; sleep 1
Xvfb $DISPLAY_CLI -screen 0 2400x1600x24 -nolisten tcp >/dev/null 2>&1 &
sleep 2
cd $BANCO || exit 1
rm -f "\$2"
setsid nohup env DISPLAY=$DISPLAY_CLI xfreerdp3 /v:127.0.0.1:\$1 /gfx:AVC420 \\
    /cert:ignore /sec:tls /u:prova /p:prova /size:$MISURA \\
    /title:$TITOLO /log-level:INFO >"\$2" 2>&1 </dev/null &
sleep 6
pgrep -x xfreerdp3 >/dev/null && echo "   client collegato" || echo "   client NON partito"
CLIENT

cat > "$BANCO_FUORI/fase7-server.sh" <<SERVER
#!/bin/bash
# REMOTIX nel contenitore, scena sintetica.  \$1 = opzioni in piu'
set -u
pkill -f "remotix --porta $PORTA_CNT" 2>/dev/null; sleep 1
cd $BANCO || exit 1
rm -f fase7-cnt.log
setsid nohup $BIN_CNT --porta $PORTA_CNT --registro traccia \\
    --senza-autenticazione --immagine-di-prova \$1 >fase7-cnt.log 2>&1 </dev/null &
sleep 2
pgrep -f "remotix --porta $PORTA_CNT" >/dev/null \\
    && echo "   REMOTIX avviato sulla $PORTA_CNT \$1" \\
    || { echo "   NON avviato"; exit 1; }
SERVER

cat > "$BANCO_FUORI/fase7-chiudi.sh" <<CHIUDI
#!/bin/bash
set -u
pkill -x xfreerdp3 2>/dev/null
pkill -f "remotix --porta $PORTA_CNT" 2>/dev/null
pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null
sleep 1
echo "   banco del contenitore sgombrato"
CHIUDI

# ===========================================================================
titolo "1. La misura, da sola: scena sintetica dentro il contenitore"
# ===========================================================================
cnt "bash $BANCO/fase7-server.sh ''" || exit 1
cnt "bash $BANCO/fase7-client.sh $PORTA_CNT fase7-cnt-client.log"
inf "lascio misurare per dodici secondi"
sleep 12
REG=$(cat "$BANCO_FUORI/fase7-cnt.log" 2>/dev/null)

if printf '%s\n' "$REG" | grep -qF "misura della rete attiva"; then
    ok "il client dichiara l'autodetect e la misura si e' accesa"
else
    ko "la misura non si e' accesa: senza RNS_UD_CS_SUPPORT_NETCHAR_AUTODETECT non c'e' niente da regolare"
    inf "$(printf '%s\n' "$REG" | grep -F 'misura della rete' | head -1)"
fi

RIASSUNTI=$(conta "$REG" "rete: RTT")
if [ "${RIASSUNTI:-0}" -ge 3 ]; then
    ok "il registro racconta la rete: $RIASSUNTI riassunti"
    inf "$(printf '%s\n' "$REG" | grep -F 'rete: RTT' | tail -1 | sed 's/^[^ ]* *[A-Z]* *//')"
else
    ko "solo $RIASSUNTI riassunti: le sonde non tornano, o non partono"
fi

# ⛔ IL CONTROLLO CHE DA' IL NOME ALLA SEZIONE, e la guardia sul difetto piu'
#    costoso della fase.
#
# `WTSVirtualChannelWrite` su un canale dinamico ACCODA e basta: i byte partono
# quando il ciclo svuota la coda.  I PDU di autodetect invece vanno dritti sul
# socket.  Mandare Start e Stop attorno all'invio del fotogramma li manda
# quindi entrambi PRIMA di lui, e il client risponde di aver contato dieci
# byte.  Il numero misurato qui e' la sola cosa che distingue una misura vera
# da una che gira senza pesare niente.
BYTE=$(printf '%s\n' "$REG" | grep -oE 'banda misurata: [0-9]+ byte' \
       | grep -oE '[0-9]+' | sort -n | tail -1)
if [ -n "${BYTE:-}" ] && [ "$BYTE" -ge 10240 ]; then
    ok "la banda si misura sul fotogramma vero: $BYTE byte contati dal client"
else
    ko "il client ha contato ${BYTE:-0} byte: lo Stop scavalca il fotogramma, la misura e' vuota"
fi

BANDA=$(campo "$REG" "banda")
if [ -n "${BANDA:-}" ] && [ "$BANDA" -gt 0 ]; then
    ok "la banda stimata e' un numero: $BANDA kbit/s"
else
    ko "la banda resta a zero: nessun risultato dal client"
fi

# La misura si aggancia solo ai fotogrammi grossi (§16): un fotogramma piccolo
# non deve farla partire.  Se ne fosse partita una su un fotogramma sotto i
# 10 KB, la traccia lo direbbe.
PICCOLI=$(printf '%s\n' "$REG" | grep -oE "ci si puo' misurare la banda" | wc -l)
MINIMI=$(printf '%s\n' "$REG" | grep -oE 'fotogramma da [0-9]+ byte' | grep -oE '[0-9]+' \
         | sort -n | head -1)
if [ -z "${MINIMI:-}" ] || [ "$MINIMI" -ge 10240 ]; then
    ok "solo i fotogrammi da almeno 10 KB avviano una misura ($PICCOLI in tutto, il piu' piccolo ${MINIMI:-nessuno})"
else
    ko "una misura e' partita su un fotogramma da $MINIMI byte: sotto i 10 KB il risultato e' rumore"
fi

cnt "bash $BANCO/fase7-chiudi.sh"

# ===========================================================================
titolo "2. Il client smette di riscontrare: il regolatore si toglie di mezzo"
# ===========================================================================
# §5 di REFERENCE.md: `queueDepth == 0xFFFFFFFF` significa «non ti mando piu'
# riscontri».  Un regolatore che continua ad aspettarli si ferma PER SEMPRE, e
# nessuno dei tre client di riferimento lo chiede a comando: si finge.
cnt "bash $BANCO/fase7-server.sh --fingi-riscontri-sospesi" || exit 1
cnt "bash $BANCO/fase7-client.sh $PORTA_CNT fase7-sosp-client.log"
inf "aspetto che la finta scatti e che passi altro tempo dopo"
sleep 14
REG=$(cat "$BANCO_FUORI/fase7-cnt.log" 2>/dev/null)

if printf '%s\n' "$REG" | grep -qF "il regolatore si toglie di mezzo"; then
    ok "la sospensione e' stata riconosciuta e detta"
else
    ko "la sospensione non e' stata riconosciuta"
fi

# Il controllo vero: DOPO la sospensione i fotogrammi continuano a partire.
# Si contano sul registro, prima e dopo la riga della sospensione.
DOPO=$(printf '%s\n' "$REG" | sed -n '/il regolatore si toglie di mezzo/,$p' \
       | grep -c 'spedito')
if [ "${DOPO:-0}" -ge 30 ]; then
    ok "dopo la sospensione sono partiti altri $DOPO fotogrammi: non si e' bloccato"
else
    ko "dopo la sospensione sono partiti solo $DOPO fotogrammi: il regolatore aspetta riscontri che non arriveranno"
fi

VIVO=$(cnt "pgrep -x xfreerdp3 >/dev/null && echo VIVO" | grep -c VIVO)
if [ "$VIVO" -eq 1 ]; then
    ok "il client e' ancora collegato"
else
    ko "il client e' caduto durante la sospensione dei riscontri"
fi

cnt "bash $BANCO/fase7-chiudi.sh"

# ===========================================================================
titolo "3. La rete strozzata: rallenta senza bloccarsi"
# ===========================================================================
vm "sudo systemctl stop remotix.service 2>/dev/null; sleep 1" >/dev/null 2>&1
copia "$BIN_LOCALE" >/dev/null || exit 1

# La scena sintetica anche qui, come servizio: un produttore che non si ferma.
vm "printf 'REMOTIX_OPZIONI=--registro diagnostica --senza-autenticazione --immagine-di-prova\n' \
    | sudo tee /etc/default/remotix >/dev/null; rm -f ~/remotix.log; \
    sudo systemctl restart remotix.service; sleep 3; \
    systemctl is-active --quiet remotix.service && echo VIVO" | grep -q VIVO \
    || { echo "REMOTIX non e' partito nella VM"; exit 1; }

cnt "bash $BANCO/fase7-client.sh $PORTA fase7-vm-client.log"
# Il ritmo a rete libera si misura su una FINESTRA, non sul totale diviso per il
# tempo d'attesa: il contatore parte dalla connessione, che e' avvenuta prima, e
# dividerlo per l'attesa gonfia il numero — al banco dava 53 fotogrammi al
# secondo con il tetto a 30.
sleep 4
SPEDITI_A=$(campo "$(vm "cat ~/remotix.log")" "spediti")
inf "misuro la rete libera per otto secondi"
sleep 8
REG=$(vm "cat ~/remotix.log")
RTT_LIBERO=$(rtt_intero "$REG")
SOGLIA_LIBERA=$(campo "$REG" "di")
SPEDITI_PRIMA=$(campo "$REG" "spediti")
RIGHE_PRIMA=$(printf '%s\n' "$REG" | wc -l)
inf "rete libera: RTT ${RTT_LIBERO:-?} ms, soglia ${SOGLIA_LIBERA:-?}, spediti ${SPEDITI_PRIMA:-?}"

# ⚠ La rimozione a orologeria, armata PRIMA di strozzare.
#   `systemd-run --on-active` invece di un `sleep` in secondo piano: il timer
#   vive in `system.slice` e sopravvive alla sessione SSH che lo ha armato — e
#   se la strozzatura tagliasse proprio quella sessione, un `sleep` ereditato da
#   lei morirebbe con lei, cioe' proprio quando serve.
#
#   ⛔ E IL TIMER DI IERI SI SPEGNE PRIMA DI ARMARE QUELLO DI OGGI.  Con un nome
#      di unita' fisso, `systemd-run` fallisce se ne esiste gia' una in attesa —
#      e a fallire e' quello NUOVO, lasciando in carica il VECCHIO.  Due
#      esecuzioni ravvicinate della prova bastano: il timer della prima toglie la
#      strozzatura a meta' della seconda, i controlli sui valori finali cadono, e
#      il sospetto va sul regolatore invece che sul banco.  Misurato il 5 agosto.
vm "sudo systemctl stop fase7-sblocca.timer fase7-sblocca.service 2>/dev/null; \
    sudo systemd-run --on-active=90 --unit=fase7-sblocca \
    /usr/sbin/tc qdisc del dev $IFACCIA root" >/dev/null 2>&1
vm "sudo /usr/sbin/tc qdisc replace dev $IFACCIA root netem delay ${RITARDO_MS}ms rate ${BANDA_KBIT}kbit \
    && echo STROZZATA" | grep -q STROZZATA \
    && inf "rete strozzata: ${RITARDO_MS} ms di ritardo, ${BANDA_KBIT} kbit/s" \
    || { ko "tc non ha applicato la strozzatura"; }

inf "lascio lavorare la rete strozzata per venti secondi"
sleep 20
REG=$(vm "cat ~/remotix.log")
RTT_STROZZO=$(rtt_intero "$REG")
SOGLIA_STROZZO=$(campo "$REG" "di")
SPEDITI_DOPO=$(campo "$REG" "spediti")
STROZZI=$(conta "$REG" "strozzo:")
# Solo la parte di registro scritta DURANTE la strozzatura: i valori di prima
# racconterebbero la rete libera e nasconderebbero quel che si vuole vedere.
FINESTRA=$(printf '%s\n' "$REG" | tail -n +$((RIGHE_PRIMA + 1)))
MAX_VOLO=$(printf '%s\n' "$FINESTRA" | grep -F 'rete: RTT' \
           | grep -oE 'in volo [0-9]+' | grep -oE '[0-9]+' | sort -n | tail -1)
MAX_SOGLIA=$(printf '%s\n' "$FINESTRA" | grep -F 'rete: RTT' \
             | grep -oE ' di [0-9]+' | grep -oE '[0-9]+' | sort -n | tail -1)

if [ -n "${RTT_STROZZO:-}" ] && [ "$RTT_STROZZO" -ge $((RITARDO_MS / 2)) ]; then
    ok "l'RTT misurato segue il ritardo iniettato: ${RTT_LIBERO:-?} ms → $RTT_STROZZO ms"
else
    ko "l'RTT misurato e' ${RTT_STROZZO:-?} ms con ${RITARDO_MS} ms iniettati: la misura non vede la rete"
fi

# ⛔ IL CONTROLLO CHE DISTINGUE QUESTO REGOLATORE DA UNA COSTANTE.
#
# La soglia si ricava dall'RTT: quanti fotogrammi stanno in volo nel tempo di
# un round trip, piu' due.  Se non cresce quando la rete si allunga, il numero
# scritto nel registro e' un due travestito.
if [ -n "${SOGLIA_STROZZO:-}" ] && [ "$SOGLIA_STROZZO" -gt "${SOGLIA_LIBERA:-2}" ]; then
    ok "la soglia del regolatore e' cresciuta con l'RTT: ${SOGLIA_LIBERA:-?} → $SOGLIA_STROZZO"
else
    ko "la soglia e' rimasta ${SOGLIA_STROZZO:-?}: non e' ricavata dall'RTT"
fi

if [ "${STROZZI:-0}" -ge 1 ]; then
    ok "il regolatore e' intervenuto $STROZZI volte"
    inf "$(printf '%s\n' "$REG" | grep -F 'strozzo:' | tail -1 | sed 's/^[^ ]* *[A-Z]* *//')"
else
    ko "il regolatore non e' mai intervenuto: la banda non e' abbastanza stretta, o non guarda niente"
fi

# ⛔ «INVECE DI CRESCERE ALL'INFINITO» — la frase del piano, presa alla lettera.
#
# Un server senza regolatore continua a produrre mentre la rete non smaltisce, e
# il conto dei non riscontrati sale finche' la memoria o il socket cedono.  Che
# resti sotto la soglia e' la sola prova che qualcuno lo sta tenendo.
if [ -n "${MAX_VOLO:-}" ] && [ "$MAX_VOLO" -le "${MAX_SOGLIA:-0}" ]; then
    ok "i fotogrammi in volo non sono mai andati oltre la soglia: al massimo $MAX_VOLO su $MAX_SOGLIA"
else
    ko "i fotogrammi in volo sono arrivati a ${MAX_VOLO:-?} con soglia ${MAX_SOGLIA:-?}: il conto cresce da solo"
fi

# «Rallenta senza bloccarsi»: i fotogrammi devono continuare a partire, e con
# una rete cosi' stretta devono essere MENO di quelli a rete libera.
CRESCITA=$(( ${SPEDITI_DOPO:-0} - ${SPEDITI_PRIMA:-0} ))
RITMO_STROZZO=$(( CRESCITA / 20 ))
RITMO_LIBERO=$(( (${SPEDITI_PRIMA:-0} - ${SPEDITI_A:-0}) / 8 ))
if [ "$CRESCITA" -ge 20 ]; then
    ok "sotto strozzatura i fotogrammi continuano a partire: $CRESCITA in venti secondi"
else
    ko "sotto strozzatura sono partiti solo $CRESCITA fotogrammi: si e' bloccato"
fi
if [ "$RITMO_STROZZO" -lt "$RITMO_LIBERO" ]; then
    ok "e sono di meno: $RITMO_LIBERO al secondo a rete libera, $RITMO_STROZZO strozzata"
else
    ko "il ritmo non e' calato ($RITMO_LIBERO → $RITMO_STROZZO al secondo): la strozzatura non morde, la prova non prova niente"
fi

VIVO=$(cnt "pgrep -x xfreerdp3 >/dev/null && echo VIVO" | grep -c VIVO)
if [ "$VIVO" -eq 1 ]; then
    ok "il client e' rimasto collegato per tutta la strozzatura"
else
    ko "il client e' caduto: la strozzatura ha rotto la sessione invece di rallentarla"
fi

# ===========================================================================
titolo "4. Tolta la strozzatura: la misura torna indietro"
# ===========================================================================
vm "sudo systemctl stop fase7-sblocca.timer fase7-sblocca.service 2>/dev/null; \
    sudo /usr/sbin/tc qdisc del dev $IFACCIA root 2>/dev/null; echo TOLTA" >/dev/null 2>&1
inf "aspetto che la misura si riassesti"
sleep 10
REG=$(vm "cat ~/remotix.log")
RTT_FINE=$(rtt_intero "$REG")
SOGLIA_FINE=$(campo "$REG" "di")
SPEDITI_FINE=$(campo "$REG" "spediti")

if [ -n "${RTT_FINE:-}" ] && [ "$RTT_FINE" -lt $((RITARDO_MS / 2)) ]; then
    ok "l'RTT e' tornato a $RTT_FINE ms: la finestra mobile segue la rete che migliora"
else
    ko "l'RTT e' rimasto a ${RTT_FINE:-?} ms: la media non dimentica i campioni vecchi"
fi

if [ -n "${SOGLIA_FINE:-}" ] && [ "$SOGLIA_FINE" -le "${SOGLIA_STROZZO:-99}" ]; then
    ok "la soglia e' tornata a $SOGLIA_FINE"
else
    ko "la soglia e' rimasta a ${SOGLIA_FINE:-?}"
fi

CRESCITA=$(( ${SPEDITI_FINE:-0} - ${SPEDITI_DOPO:-0} ))
if [ "$CRESCITA" -ge 100 ]; then
    ok "a rete libera i fotogrammi sono tornati a scorrere: $CRESCITA in dieci secondi"
else
    ko "solo $CRESCITA fotogrammi in dieci secondi a rete libera: qualcosa e' rimasto strozzato"
fi

cnt "bash $BANCO/fase7-chiudi.sh"

# ===========================================================================
titolo "Riepilogo"
# ===========================================================================
# ⛔ SI RIMETTE IN PIEDI IL SERVIZIO COME LO SI E' TROVATO.
#
#    Vale doppio qui: questa prova cambia /etc/default/remotix per mettere la
#    scena sintetica, e lasciarla accesa vorrebbe dire un server che non mostra
#    piu' il desktop.  E' la lezione di §8.6 di REFERENCE.md — «il server sembra
#    spento» — pagata due volte per non averla scritta.
vm "sudo systemctl stop fase7-sblocca.timer fase7-sblocca.service 2>/dev/null; \
    sudo /usr/sbin/tc qdisc del dev $IFACCIA root 2>/dev/null; \
    printf 'REMOTIX_OPZIONI=--registro diagnostica\n' | sudo tee /etc/default/remotix >/dev/null; \
    sudo systemctl restart remotix.service; sleep 2; \
    systemctl is-active --quiet remotix.service && echo RIPRISTINATO" 2>&1 | grep -q RIPRISTINATO \
    && inf "servizio rimesso in piedi con PAM e senza strozzature" \
    || inf "ATTENZIONE: il servizio nella VM non e' ripartito"

if [ "$GUASTI" -eq 0 ]; then
    printf '\n\033[1;32mFASE 7: tutti i controlli superati\033[0m\n\n'
else
    printf '\n\033[1;31mFASE 7: %d controlli falliti\033[0m\n\n' "$GUASTI"
fi
exit $((GUASTI > 0))
