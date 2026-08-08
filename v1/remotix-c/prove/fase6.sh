#!/bin/bash
#
# Prova della fase 6: la risoluzione segue la finestra.
#
#   bash /media/REMOTIX/src/remotix-c/prove/fase6.sh
#
# ⚠ QUESTA PROVA NON SI PUO' FARE SU MSTSC, e non e' una svista.
#
#   mstsc apre il canale `Microsoft::Windows::RDS::DisplayControl` — §1.2 di
#   REFERENCE.md lo ha misurato fra i suoi canali dinamici — ma NON manda un
#   `MONITOR_LAYOUT` quando si trascina il bordo della finestra: §5.7 di
#   SPECIFICA.md lo mette nero su bianco, «mstsc: negozia EGFX subito, NON
#   ridimensiona da se'».  E' anche il motivo per cui le regole 1 e 2 di quel
#   paragrafo le ha trovate il client Android e non lui.
#
#   Trascinare il bordo su mstsc quindi non prova niente: se l'immagine segue e'
#   il client che scala, se non segue non e' un difetto nostro.  Il
#   ridimensionamento si esercita dove esiste — `xfreerdp3 /dynamic-resolution`
#   qui, e RDM a mano — mentre su mstsc la fase 6 e' una prova di NON
#   REGRESSIONE: il canale si apre anche per lui, le capacita' partono anche per
#   lui, e un PDU malformato o una superficie cancellata a sproposito si
#   vedrebbero proprio la', che e' il client severo.  Quella parte sta in fondo,
#   fra le cose da guardare a mano.
#
# ⚠ LE DUE REGOLE DI FASE 5 SUL PILOTARE I DUE AMBIENTI VALGONO ANCHE QUI:
#   `ssh` senza `-n` eredita lo standard input dello script, e l'uscita di
#   `enter.sh` non si mette mai in una pipe — dentro ci finisce la richiesta di
#   password di `sudo`, e chi la deve fornire resta appeso in silenzio.  Per
#   questo i registri si leggono DAL SERVER, dalla cartella condivisa.
set -u

BASE=/media/REMOTIX
BIN_LOCALE="$BASE/src/remotix-c/build/src/remotix"
BIN_CNT=/srv/src/remotix-c/build/src/remotix
PORTA=3389        # REMOTIX nella VM
PORTA_CNT=3390    # REMOTIX nel contenitore, con la scena sintetica
DISPLAY_CLI=:110
TITOLO=REMOTIXFASE6
BANCO=/srv/remotix/tmp/banco-b          # come lo vede il contenitore
BANCO_FUORI=/media/REMOTIX/tmp/banco-b  # la stessa cartella, vista dal server

# La misura di partenza e le due a cui si va.  Non sono tonde apposta: una
# misura gia' allineata a 16 e 64 nasconderebbe gli sbagli di allineamento
# (R4), che sono il primo sospetto quando un ridimensionamento sporca
# l'immagine.
MISURA_A=${MISURA_A:-1282x802}
LARG_B=${LARG_B:-1600};  ALT_B=${ALT_B:-902}
LARG_C=${LARG_C:-1100};  ALT_C=${ALT_C:-700}
LARG_D=${LARG_D:-1420};  ALT_D=${ALT_D:-820}

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

[ -x "$BIN_LOCALE" ] || { echo "manca $BIN_LOCALE: costruiscilo prima"; exit 1; }
mkdir -p "$BANCO_FUORI"
bash "$BASE/enter.sh" true || exit 1

# ===========================================================================
# Gli script che girano DENTRO il contenitore.
#
# Stanno su file invece che sulla riga di comando di `enter.sh` per una ragione
# pagata in fase 4: un comando inline che mette qualcosa in secondo piano lascia
# la sessione appesa alle pipe che quel qualcosa ha ereditato, e lo si scopre
# come un passo che «non torna» pur essendo gia' andato a buon fine.
# ===========================================================================
cat > "$BANCO_FUORI/fase6-client.sh" <<CLIENT
#!/bin/bash
# \$1 = porta   \$2 = nome del registro del client
set -u
pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null; sleep 1
Xvfb $DISPLAY_CLI -screen 0 2400x1600x24 -nolisten tcp >/dev/null 2>&1 &
sleep 2
cd $BANCO || exit 1
rm -f "\$2"
setsid nohup env DISPLAY=$DISPLAY_CLI xfreerdp3 /v:127.0.0.1:\$1 /gfx:AVC420 \\
    /cert:ignore /sec:tls /u:prova /p:prova /size:$MISURA_A /dynamic-resolution \\
    /title:$TITOLO /log-level:INFO >"\$2" 2>&1 </dev/null &
sleep 8
ID=\$(DISPLAY=$DISPLAY_CLI xdotool search --name $TITOLO 2>/dev/null | head -1)
[ -n "\$ID" ] && echo "   finestra del client: \$ID" || echo "   NESSUNA finestra trovata"
echo "\$ID" > $BANCO/fase6-finestra
CLIENT

cat > "$BANCO_FUORI/fase6-ridimensiona.sh" <<RIDIM
#!/bin/bash
# \$1 = larghezza   \$2 = altezza   \$3 = secondi di attesa dopo
set -u
ID=\$(cat $BANCO/fase6-finestra 2>/dev/null)
[ -n "\$ID" ] || { echo "   nessuna finestra da ridimensionare"; exit 1; }
# ⚠ Il client di FreeRDP non manda piu' di un layout ogni 200 ms
# (RESIZE_MIN_DELAY): una raffica piu' fitta di cosi' la accorpa LUI, e la
# prova misurerebbe il client invece del server.
DISPLAY=$DISPLAY_CLI xdotool windowsize \$ID \$1 \$2
sleep \$3
echo "   finestra portata a \$1x\$2"
RIDIM

cat > "$BANCO_FUORI/fase6-protocollo.sh" <<PROTO
#!/bin/bash
# REMOTIX con la SCENA SINTETICA, dentro il contenitore: nessuna sessione
# grafica, nessun palco, nessun PipeWire.  Se il ridimensionamento non si vede
# qui, il sospetto cade su una cosa sola — il protocollo — ed e' la lezione di
# §5.4 di SPECIFICA.md applicata alla fase 6.
set -u
pkill -f "remotix --porta $PORTA_CNT" 2>/dev/null; sleep 1
cd $BANCO || exit 1
rm -f fase6-protocollo.log
setsid nohup $BIN_CNT --porta $PORTA_CNT --registro diagnostica \\
    --senza-autenticazione --immagine-di-prova >fase6-protocollo.log 2>&1 </dev/null &
sleep 2
pgrep -f "remotix --porta $PORTA_CNT" >/dev/null \\
    && echo "   REMOTIX (scena sintetica) avviato sulla $PORTA_CNT" \\
    || { echo "   NON avviato"; exit 1; }
PROTO

cat > "$BANCO_FUORI/fase6-raffica.sh" <<RAFFICA
#!/bin/bash
# La raffica vera: le misure si mandano DENTRO UNA SOLA invocazione.
#
# ⚠ Chiamare \`fase6-ridimensiona.sh\` una volta per misura non produce nessuna
#   raffica, e ci si casca: ogni giro costa una sessione SSH e un ingresso nel
#   contenitore, cioe' piu' di un secondo — piu' del tempo che il server impiega
#   ad applicare un ridimensionamento.  Le richieste arriverebbero in fila
#   indiana, e la prova direbbe di aver collaudato l'accorpamento senza averlo
#   mai fatto scattare.
set -u
ID=\$(cat $BANCO/fase6-finestra 2>/dev/null)
[ -n "\$ID" ] || { echo "   nessuna finestra da ridimensionare"; exit 1; }
for m in "1500 860" "1420 820" "1340 780" "1260 740" "1180 700" "1520 880" "1360 800" "1240 720"; do
    set -- \$m
    DISPLAY=$DISPLAY_CLI xdotool windowsize \$ID \$1 \$2
    # Il client di FreeRDP non manda piu' di un layout ogni 200 ms
    # (RESIZE_MIN_DELAY): sotto quella soglia accorpa LUI, e si misurerebbe il
    # client invece del server.  Sopra di poco, e le richieste si accavallano
    # sul server, che e' esattamente il caso da provare.
    sleep 0.3
done
echo "   raffica di 8 misure mandata in 2,4 secondi"
RAFFICA

cat > "$BANCO_FUORI/fase6-lento.sh" <<LENTO
#!/bin/bash
# Tre trascinamenti BEN DISTANZIATI: tre secondi l'uno dall'altro, cioe' molto
# piu' del mezzo secondo che il server impiega ad applicare.  E' il modo in cui
# si ridimensiona davvero — si trascina, ci si ferma, si guarda — e qui la
# misura finale dev'essere ESATTAMENTE l'ultima chiesta.
set -u
ID=\$(cat $BANCO/fase6-finestra 2>/dev/null)
[ -n "\$ID" ] || { echo "   nessuna finestra da ridimensionare"; exit 1; }
for m in "1500 860" "1300 760" "$LARG_D $ALT_D"; do
    set -- \$m
    DISPLAY=$DISPLAY_CLI xdotool windowsize \$ID \$1 \$2
    sleep 3
done
echo "   tre trascinamenti distanziati, ultimo $LARG_D x $ALT_D"
LENTO

cat > "$BANCO_FUORI/fase6-chiudi.sh" <<CHIUDI
#!/bin/bash
set -u
pkill -x xfreerdp3 2>/dev/null
pkill -f "remotix --porta $PORTA_CNT" 2>/dev/null
pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null
sleep 1
echo "   banco del contenitore sgombrato"
CHIUDI

# ===========================================================================
titolo "1. Il protocollo da solo: scena sintetica, dentro il contenitore"
# ===========================================================================
cnt "bash $BANCO/fase6-protocollo.sh" || exit 1
cnt "bash $BANCO/fase6-client.sh $PORTA_CNT fase6-proto-client.log"

# Quanti canali dinamici il client ha caricato PRIMA di qualunque
# ridimensionamento.  Serve al controllo di R7 piu' sotto: una riattivazione
# butta giu' i canali dinamici e il client li ricarica, quindi questo numero
# cresce.  E' l'unico segnale di riattivazione che il registro del client
# mostri a livello INFO — e la regola e' che il congedo, come la riattivazione,
# si verifica dal lato che la subisce.
CANALI_PRIMA=$(grep -c 'Loading Dynamic Virtual Channel' \
    "$BANCO_FUORI/fase6-proto-client.log" 2>/dev/null)

cnt "bash $BANCO/fase6-ridimensiona.sh $LARG_B $ALT_B 5"
cnt "bash $BANCO/fase6-ridimensiona.sh $LARG_C $ALT_C 5"

# Il registro del client si fotografa ADESSO, prima di sgombrare il banco:
# `pkill` gli fa scrivere «Network disconnect!», e un controllo che leggesse
# dopo troverebbe la firma di un difetto che ha causato lui.
cp "$BANCO_FUORI/fase6-proto-client.log" "$BANCO_FUORI/fase6-proto-client.istantanea" 2>/dev/null
CLI="$BANCO_FUORI/fase6-proto-client.istantanea"
VIVO=$(cnt "pgrep -x xfreerdp3 >/dev/null && echo VIVO" | grep -c VIVO)

REG=$(cat "$BANCO_FUORI/fase6-protocollo.log" 2>/dev/null)

if printf '%s\n' "$REG" | grep -qF "canale DISP aperto: al massimo"; then
    ok "il canale MS-RDPEDISP e' stato aperto e le capacita' sono partite"
    inf "$(printf '%s\n' "$REG" | grep -F 'canale DISP aperto: al massimo' | head -1 \
           | sed 's/^[^ ]* *[A-Z]* *//')"
else
    ko "il canale DISP non si e' aperto: nessun client potra' chiedere una misura"
fi

CHIESTE=$(conta "$REG" "il client chiede una misura nuova")
if [ "$CHIESTE" -ge 2 ]; then
    ok "il client ha chiesto $CHIESTE misure nuove: i MONITOR_LAYOUT arrivano e si leggono"
else
    ko "sono arrivate $CHIESTE richieste di misura invece di 2: il canale non porta i layout"
fi

TELE=$(conta "$REG" "ridimensiono la tela grafica")
if [ "$TELE" -ge 2 ]; then
    ok "la tela grafica e' stata ridichiarata $TELE volte, senza riattivazione (R7)"
else
    ko "la tela e' stata ridichiarata $TELE volte: il ridimensionamento non arriva in fondo"
fi

# ⛔ R7 LETTA DAL LATO DEL CLIENT, che e' il lato che la subisce.
#
# Il nostro registro puo' dire «ridichiaro la tela» quanto vuole: se al client
# fosse arrivato un `Deactivate All`, lui butterebbe giu' i canali dinamici e li
# ricaricherebbe.  Il conto dei «Loading Dynamic Virtual Channel» e' quindi il
# segnale della riattivazione visto da chi la paga — ed e' la stessa regola di
# metodo che in fase 5 e' costata il difetto piu' grosso del progetto: un
# congedo si verifica dal lato che lo deve ricevere.
CANALI_DOPO=$(grep -c 'Loading Dynamic Virtual Channel' "$CLI" 2>/dev/null)
if [ "$VIVO" -eq 1 ] && [ "${CANALI_DOPO:-9}" -eq "${CANALI_PRIMA:-0}" ] \
   && ! grep -qiE 'Network disconnect|transport_read_layer' "$CLI" 2>/dev/null; then
    ok "il client non ha ricaricato canali e non e' caduto: nessuna riattivazione (R7)"
else
    ko "il client ha ricaricato i canali ($CANALI_PRIMA → $CANALI_DOPO) o e' caduto: R7 violata"
fi

if printf '%s\n' "$REG" | grep -F "ridimensiono la tela grafica" | grep -q "${LARG_C}x${ALT_C}"; then
    ok "l'ultima misura chiesta (${LARG_C}x${ALT_C}) e' quella arrivata alla tela"
else
    ko "la tela non e' arrivata all'ultima misura chiesta (${LARG_C}x${ALT_C})"
fi

cnt "bash $BANCO/fase6-chiudi.sh"

# ===========================================================================
titolo "2. Il desktop vero, nella VM: si ridimensiona senza rifare la cattura"
# ===========================================================================
vm "sudo systemctl stop remotix.service 2>/dev/null; sleep 1" >/dev/null 2>&1
copia "$BIN_LOCALE" >/dev/null || exit 1
vm "rm -f ~/remotix.log; bash avvia-remotix.sh --aperto" >/dev/null || exit 1

cnt "bash $BANCO/fase6-client.sh $PORTA fase6-vm-client.log"
inf "aspetto che il desktop sia in piedi"
sleep 12
cnt "bash $BANCO/fase6-ridimensiona.sh $LARG_B $ALT_B 8"

REG=$(vm "cat ~/remotix.log")

if printf '%s\n' "$REG" | grep -qF "ridimensiono il palco"; then
    ok "il palco ha preso la misura nuova"
    inf "$(printf '%s\n' "$REG" | grep -F 'ridimensiono il palco' | head -1 | sed 's/^[^ ]* *[A-Z]* *//')"
else
    ko "il palco non e' stato ridimensionato"
fi

# ⛔ IL CONTROLLO CHE DA' IL NOME ALLA FASE.
#
# Fino alla fase 5 un cambio di misura smontava e rimontava: cattura nuova,
# controllo nuovo, dispositivi virtuali nuovi, e i tasti premuti persi per
# strada (§5.8 di SPECIFICA.md).  Questa riga dice che non succede piu'.
if printf '%s\n' "$REG" | grep -qF "senza rifare la cattura"; then
    ok "la misura e' cambiata SENZA rifare la cattura: pw_stream_update_params"
else
    ko "la cattura e' stata rifatta: e' il prezzo che la fase 6 esiste per non pagare piu'"
fi

if printf '%s\n' "$REG" | grep -qF "ripiego: rifaccio il palco"; then
    ko "e' scattato il RIPIEGO: il ridimensionamento a caldo non ha funzionato"
    inf "$(printf '%s\n' "$REG" | grep -F 'ridimensionamento a caldo fallito' | head -1)"
else
    ok "nessun ripiego: la strada buona ha retto"
fi

if printf '%s\n' "$REG" | grep -qF "ridimensiono la tela grafica"; then
    ok "la tela grafica e' stata ridichiarata (R7), non si e' riattivata la sessione"
else
    ko "la tela non e' stata ridichiarata: il client resta alla misura di prima"
fi

# La firma di §9 di REFERENCE.md: UNA sola «nuova sorgente» in tutta la
# sessione.  Un secondo montaggio del monitor virtuale a poca distanza dal primo
# significa che il ridimensionamento e' passato per il rimontaggio.
MONTAGGI=$(conta "$REG" "monitor virtuale montato")
if [ "$MONTAGGI" -le 1 ]; then
    ok "una sola «nuova sorgente» in tutta la sessione ($MONTAGGI montaggio)"
else
    ko "$MONTAGGI montaggi del monitor virtuale: il ridimensionamento ne ha fatto uno nuovo"
fi

# Il puntatore: dopo il ridimensionamento la regione su cui si riscalano le
# coordinate assolute deve essere quella NUOVA, altrimenti il mouse finisce a
# meta' schermo e la colpa sembra del client.
REGIONI=$(conta "$REG" "regione del puntatore")
if [ "$REGIONI" -ge 2 ]; then
    ok "la regione del puntatore e' stata riletta dopo il cambio di misura"
    inf "$(printf '%s\n' "$REG" | grep -F 'regione del puntatore' | tail -1 | sed 's/^[^ ]* *[A-Z]* *//')"
else
    ko "la regione del puntatore non e' stata riletta: le coordinate del mouse resteranno vecchie"
fi

# ===========================================================================
titolo "3. La raffica: si trascina il bordo, non si applica un fotogramma per volta"
# ===========================================================================
TRASCINAMENTI=8   # quante misure manda fase6-raffica.sh
PRIMA_TELE=$(conta "$REG" "ridimensiono la tela grafica")
cnt "bash $BANCO/fase6-raffica.sh"
inf "aspetto che la raffica si esaurisca"
sleep 15
REG=$(vm "cat ~/remotix.log")
MEDIO_TELE=$(conta "$REG" "ridimensiono la tela grafica")
APPLICATI=$((MEDIO_TELE - PRIMA_TELE))
ECHI=$(conta "$REG" "scarto l'eco del ridimensionamento")

if [ "$APPLICATI" -ge 1 ]; then
    ok "la raffica e' arrivata in fondo: $APPLICATI ridimensionamenti per $TRASCINAMENTI trascinamenti"
else
    ko "la raffica non ha prodotto nessun ridimensionamento"
fi
if [ "$APPLICATI" -lt "$TRASCINAMENTI" ]; then
    ok "le richieste si sono ACCORPATE: $TRASCINAMENTI trascinamenti → $APPLICATI ridimensionamenti"
else
    ko "nessun accorpamento: $APPLICATI ridimensionamenti per $TRASCINAMENTI trascinamenti — su "\
"Android sarebbero altrettanti riavvii del decodificatore"
fi

# ⛔ IL CONTROLLO PIU' IMPORTANTE DELLA FASE, ed e' quello che il banco ha
#    trovato rotto la prima volta che e' stato scritto.
#
# Non basta che la raffica venga applicata: deve FERMARSI quando l'utente si
# ferma.  Fino alla guardia sull'eco (ECO_MS in server.c) qui si misuravano 38
# richieste e 37 ridimensionamenti, che continuavano da soli per oltre quaranta
# secondi dopo l'ultimo trascinamento — su Android, altrettanti riavvii del
# decodificatore per un utente che non stava piu' toccando niente.
inf "controllo che il ridimensionamento si sia FERMATO da solo"
sleep 10
REG=$(vm "cat ~/remotix.log")
DOPO_TELE=$(conta "$REG" "ridimensiono la tela grafica")
if [ "$DOPO_TELE" -eq "$MEDIO_TELE" ]; then
    ok "nessun ridimensionamento nei dieci secondi di quiete: il ping-pong non riparte"
else
    ko "$((DOPO_TELE - MEDIO_TELE)) ridimensionamenti a mani ferme: server e client si rincorrono"
fi
if [ "$ECHI" -gt 0 ]; then
    inf "$ECHI eco scartate — e' la guardia che ha rotto la rincorsa"
fi

# ⚠ QUI NON SI PRETENDE L'ULTIMA MISURA DELLA RAFFICA, e la ragione e' misurata.
#
# Ridimensionando, il client porta la propria finestra alla misura che gli
# comunichiamo — e cosi' facendo SOVRASCRIVE il proprio obiettivo, che era il
# trascinamento successivo.  L'intento finale si perde dentro il client, non
# qui: `xf_disp_queueResize` di FreeRDP non spedisce mai subito (si autoblocca
# sui 200 ms di `RESIZE_MIN_DELAY`) e affida l'invio al proprio timer da un
# secondo, che nel frattempo trova un obiettivo gia' riscritto.  Senza gestore
# di finestre, per giunta, `xdotool` e il client si contendono la geometria.
#
# L'esattezza si pretende dove ha senso pretenderla, cioe' su trascinamenti
# distanziati: e' la sezione qui sotto, ed e' anche il modo in cui si
# ridimensiona davvero — si trascina, ci si ferma, si guarda.
ULTIMA=$(printf '%s\n' "$REG" | grep -F "ridimensiono la tela grafica" | tail -1)
if printf '%s\n' "$ULTIMA" | grep -qE '1[0-9]{3}x[78][0-9]{2}'; then
    ok "il desktop e' fermo su una delle misure della raffica"
    inf "$(printf '%s\n' "$ULTIMA" | sed 's/^[^ ]* *[A-Z]* *//')"
else
    ko "il desktop non e' fermo su nessuna misura della raffica"
fi
if vm "pgrep -x remotix >/dev/null"; then
    ok "REMOTIX e' vivo dopo la raffica"
else
    ko "REMOTIX e' morto durante la raffica"
fi
if cnt "pgrep -x xfreerdp3 >/dev/null && echo VIVO" | grep -q VIVO; then
    ok "il client e' vivo dopo la raffica: nessuna disconnessione"
else
    ko "il client e' caduto durante la raffica"
fi

MONTAGGI=$(conta "$REG" "monitor virtuale montato")
if [ "$MONTAGGI" -le 1 ]; then
    ok "ancora un solo montaggio del monitor virtuale, dopo tutta la raffica"
else
    ko "$MONTAGGI montaggi: qualche ridimensionamento e' passato per il rimontaggio"
fi
if printf '%s\n' "$REG" | grep -qF "layout monitor rifiutato"; then
    ko "qualche layout e' stato rifiutato: erano tutti dentro i limiti"
    inf "$(printf '%s\n' "$REG" | grep -F 'layout monitor rifiutato' | head -1)"
else
    ok "nessun layout rifiutato: erano tutti misure legittime"
fi

# ===========================================================================
titolo "4. Trascinamenti distanziati: si finisce ESATTAMENTE dove ci si e' fermati"
# ===========================================================================
PRIMA_TELE=$(conta "$REG" "ridimensiono la tela grafica")
cnt "bash $BANCO/fase6-lento.sh"
sleep 6
REG=$(vm "cat ~/remotix.log")
APPLICATI=$(( $(conta "$REG" "ridimensiono la tela grafica") - PRIMA_TELE ))

if [ "$APPLICATI" -eq 3 ]; then
    ok "tre trascinamenti, tre ridimensionamenti: nessuno perso, nessuno di troppo"
else
    ko "tre trascinamenti hanno prodotto $APPLICATI ridimensionamenti"
fi
if printf '%s\n' "$REG" | grep -F "ridimensiono la tela grafica" | tail -1 \
   | grep -q "${LARG_D}x${ALT_D}"; then
    ok "il desktop e' finito sull'ultima misura chiesta (${LARG_D}x${ALT_D})"
else
    ko "il desktop non e' finito su ${LARG_D}x${ALT_D}"
    inf "$(printf '%s\n' "$REG" | grep -F 'ridimensiono la tela grafica' | tail -1)"
fi

# ===========================================================================
titolo "5. Il ritorno: chi si ricollega a un'altra misura non fa rimontare nulla"
# ===========================================================================
cnt "pkill -x xfreerdp3 2>/dev/null; sleep 3; echo '   client chiuso'"
cnt "bash $BANCO/fase6-client.sh $PORTA fase6-ritorno.log"
sleep 6
REG=$(vm "cat ~/remotix.log")

if printf '%s\n' "$REG" | grep -qF "ridimensiono invece di rimontare"; then
    ok "chi torna a un'altra misura ridimensiona: le finestre restano dov'erano"
else
    inf "nessun ridimensionamento al ritorno (il client ha chiesto la misura che c'era gia')"
fi
MONTAGGI=$(conta "$REG" "monitor virtuale montato")
if [ "$MONTAGGI" -le 1 ]; then
    ok "un solo montaggio del monitor virtuale in tutta la prova"
else
    ko "$MONTAGGI montaggi del monitor virtuale in tutta la prova"
fi

# ===========================================================================
titolo "Registro del server, in coda"
# ===========================================================================
printf '%s\n' "$REG" | grep -vE 'libx264|TRACC' | tail -20

cnt "bash $BANCO/fase6-chiudi.sh"

# La prova NON lascia la macchina spenta: chi finisce la suite va a provare a
# mano dai tre client, e trovare la porta muta e' la trappola pagata in fase 5.
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
cat <<'MANO'

    Restano da guardare a mano, e sono la meta' della fase:

      RDM (Android)  si ruota il telefono avanti e indietro cinque volte di
                     seguito.  E' il modo piu' facile di generare la raffica, e
                     ogni giro e' anche un riavvio del decodificatore.
                     L'immagine deve seguire, e la sessione reggere.

                     ⛔ E' anche l'UNICO modo di esercitare R8 — il layout
                     rinviato.  I client Android chiedono la propria misura
                     entro un decimo di secondo dalla connessione, prima di
                     aver negoziato EGFX; xfreerdp3 no, e infatti in questo
                     banco quel ramo non scatta mai.  Nel registro si deve
                     vedere «la misura chiesta … e' gia' quella in uso»
                     oppure «ridimensiono la tela grafica», MAI un secondo
                     «nuova sorgente».

      RDM, DPI       la stessa connessione esercita anche il controllo sul DPI:
                     RDM dichiara 984 px su 1000 mm, cioe' 24 DPI, e nel
                     registro deve comparire «dimensione fisica scartata».
                     Qui il banco non lo prova, perche' xfreerdp3 dichiara
                     sempre 75 DPI, che e' plausibile.

      mstsc          NON ridimensiona da se': qui non si trascina niente.  Si
                     verifica la NON REGRESSIONE — il desktop compare
                     all'istante, il registro dice «canale DISP aperto» anche
                     per lui, e non compare nessun secondo «nuova sorgente».
                     E' il client severo: se una superficie viene cancellata a
                     sproposito, si vede qui.
MANO
exit $((GUASTI > 0))
