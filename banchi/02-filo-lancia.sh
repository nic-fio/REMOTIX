#!/usr/bin/env bash
# =========================================================================
# 02-filo-lancia.sh — ⛔ F2.4: il giro intero del banco del filo, fase 2.
#
#     ./02-filo-lancia.sh              tutto quel che si puo' girare OGGI
#     ./02-filo-lancia.sh --elenco     le previsioni, senza misurare
#     ./02-filo-lancia.sh --vivo       ⏳ anche il cliente, contro la 7514
#
# =========================================================================
# ⛔ PERCHE' QUESTO SCRIPT ESISTE, E NON E' «per comodita'»
#
# `PIANO.md` §0.4 momento 1: il revisore interviene **appena il banco esiste,
# PRIMA che il prodotto sia scritto**.  Il prodotto della fase 2 non c'e':
#
#     grep -c '0x0301\|0x0302' src/rcp.c src/webtransport.c src/pagina.html
#     -> 0 · 0 · 0        `[M]` 12 agosto 2026
#
# ⛔ Da cui il mestiere di questo file: **mettere in fila quel che si puo'
#    misurare oggi, e DICHIARARE quel che non si puo'**.  Un giro che girasse
#    solo i pezzi che passano e tacesse sugli altri sarebbe la peggiore delle
#    prove: verde, e su niente.
#
# ⚠ E la regola **B0.4** di `FASI.md` §01-filo-nudo vale qui piu' che altrove:
#   *«l'atteso lo confronta il banco, non chi legge»*.  Ogni pezzo qui sotto
#   esce con uno stato, e questo file lo **confronta** — non lo stampa e basta.
#
# =========================================================================
# ⛔ LE TRE TRAPPOLE DI SHELL CHE QUESTO FILE NON RIPETE
#
#  1. ⛔ **niente `2>/dev/null`, e nessuno stato d'uscita buttato in una
#     catena di `|`** (`REVIEWER.md` §1 punto 4).  «Zero» e «fallimento» hanno
#     lo stesso aspetto quando l'errore e' stato mangiato, ed e' la forma
#     d'errore **E8**;
#
#  2. ⛔ **mai una redirezione ATTORNO a `ssh` o a `enter.sh`**.  La richiesta
#     di parola d'ordine di `sudo` esce su **stderr**: buttandola via, nessuno
#     puo' rispondere, e il comando resta **appeso per sempre, in silenzio**.
#     ⚠ `FASI.md` §00-ambiente B3.3 — pagata **quattro volte**, due delle quali
#     nella sola notte dell'11 agosto 2026, e due di quelle **dentro i file
#     che la trappola la descrivono in testa**;
#
#  3. ⛔ **`set -e` NON basta e qui non c'e'**: fa uscire al primo rosso, e un
#     giro che si ferma al primo rosso non dice quanto aveva coperto.  Si
#     contano i rossi e si va avanti, e alla fine c'e' un denominatore.
#
# =========================================================================
# ⛔ LO STATO INIZIALE, DICHIARATO **E VERIFICATO** — regola B0.1
#
# *«Un banco che non sa da che stato parte misura la storia della macchina.»*
#
#  · la porta di F2.4 e' la **7514**, e questo script verifica che sia libera
#    prima di dire qualunque cosa.  ⛔ Se e' occupata **non si spegne niente**:
#    si dichiara e si esce.  Sulla **7448** gira il prodotto di casa e sulla
#    **7501** il bersaglio di P5, accesi apposta (mandato §4);
#  · i pezzi che girano su CHUWI **non toccano la rete**: il giudice del
#    fotogramma e l'arbitro delle registrazioni non hanno dipendenze, ed e'
#    voluto — chi revisiona il banco prima del prodotto non ha il contenitore;
#  · `aioquic` sta **solo dentro il contenitore**, e la sua assenza si
#    **dichiara**: ⛔ un pezzo saltato in silenzio e un pezzo passato hanno lo
#    stesso aspetto.
# =========================================================================
set -u

QUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ESITI="$QUI/02-filo-esiti.jsonl"
PORTA=7514
VERDE=$'\033[1;32m'; ROSSO=$'\033[1;31m'; GIALLO=$'\033[1;33m'; GRIGIO=$'\033[0m'

ROSSI=0
FATTI=0
SALTATI=0

dice() { printf '%s\n' "$*"; }

# ⛔ Il confronto lo fa QUESTA funzione, non chi legge (B0.4).
pezzo() {
    local nome="$1" atteso="$2"; shift 2
    dice ""
    dice "== $nome   (atteso: uscita $atteso)"
    "$@"
    local visto=$?
    FATTI=$((FATTI + 1))
    if [ "$visto" -eq "$atteso" ]; then
        dice "   ${VERDE}OK${GRIGIO}  $nome: uscita $visto"
    else
        dice "   ${ROSSO}NO${GRIGIO}  $nome: uscita $visto, atteso $atteso"
        ROSSI=$((ROSSI + 1))
    fi
}

salta() {
    local nome="$1" perche="$2"
    SALTATI=$((SALTATI + 1))
    dice ""
    dice "   ${GIALLO}--${GRIGIO}  $nome: SALTATO — $perche"
    dice "       ⛔ e «saltato» non e' «passato»: entra nel conto finale"
}

# -------------------------------------------------------------------------
if [ "${1:-}" = "--elenco" ]; then
    dice "== F2.4 — le previsioni, tutte, prima di qualunque giro"
    python3 "$QUI/02-filo-fotogramma.py" --elenco
    dice ""
    python3 "$QUI/02-filo-validatore.py" --elenco
    dice ""
    python3 "$QUI/02-filo-cliente.py" --elenco
    exit 0
fi

dice "==========================================================="
dice "  F2.4 — IL FILO: un fotogramma da RCP alla pagina"
dice "==========================================================="
dice ""
dice "== ⛔ lo stato iniziale, dichiarato E verificato (B0.1)"
dice "   macchina: $(uname -n)   python: $(python3 -V)"

# ⛔ La porta si guarda, non si libera.  E se `ss` non c'e' si DICE, invece di
#    concludere «libera» da un comando che non ha girato (forma E8).
if command -v ss >/dev/null; then
    OCCUPANTI="$(ss -lun | grep -c ":$PORTA " || true)"
    if [ "$OCCUPANTI" -eq 0 ]; then
        dice "   porta $PORTA: ${VERDE}libera${GRIGIO} (${OCCUPANTI} ascoltatori)"
    else
        dice "   porta $PORTA: ${ROSSO}OCCUPATA${GRIGIO} da $OCCUPANTI ascoltatori"
        dice "   ⛔ NON si spegne niente.  Si dichiara e si esce: sulla 7448 gira"
        dice "      il prodotto di casa e sulla 7501 il bersaglio di P5."
        exit 2
    fi
else
    dice "   porta $PORTA: ${GIALLO}NON GUARDATA${GRIGIO} — \`ss\` non c'e' su"
    dice "      questa macchina.  ⛔ E «non guardata» non e' «libera»."
fi

# ⛔ La presenza di aioquic si DICHIARA, e decide che cosa si puo' girare.
if python3 -c "import aioquic" 2>&1 | grep -q ModuleNotFoundError; then
    AIOQUIC=no
    dice "   aioquic: ${GIALLO}assente${GRIGIO} — i pezzi dal vivo non si girano"
    dice "      ⚠ sta solo dentro il contenitore (\`/media/REMOTIX/enter.sh\`)"
else
    AIOQUIC=si
    dice "   aioquic: ${VERDE}presente${GRIGIO}"
fi

# ⛔ E lo stato del PRODOTTO, che e' la ragione per cui meta' di questo banco
#    non si puo' ancora girare.  Si conta, non si crede.
VIDEO_NEL_PRODOTTO=0
for f in "$QUI/../src/rcp.c" "$QUI/../src/webtransport.c" "$QUI/../src/pagina.html"; do
    if [ -r "$f" ]; then
        N="$(grep -c '0x0301\|0x0302' "$f" || true)"
        VIDEO_NEL_PRODOTTO=$((VIDEO_NEL_PRODOTTO + N))
    fi
done
dice "   il prodotto della fase 2: $VIDEO_NEL_PRODOTTO occorrenze di 0x0301/0x0302 in src/"
if [ "$VIDEO_NEL_PRODOTTO" -eq 0 ]; then
    dice "      ⏳ zero: il video non e' ancora scritto, ed e' il momento giusto"
    dice "         per un banco (\`PIANO.md\` §0.4 momento 1)"
fi

# -------------------------------------------------------------------------
dice ""
dice "==========================================================="
dice "  QUEL CHE SI MISURA OGGI, SENZA PRODOTTO E SENZA RETE"
dice "==========================================================="

pezzo "il giudice del fotogramma" 0 \
    python3 "$QUI/02-filo-fotogramma.py" --uscita "$ESITI"

pezzo "la certificazione del giudice (sano -> guasto -> risanato)" 0 \
    python3 "$QUI/02-filo-fotogramma.py" --certifica --uscita "$ESITI"

pezzo "l'arbitro del canale video, certificato contro G4" 0 \
    python3 "$QUI/02-filo-validatore.py" --certifica --uscita "$ESITI"

pezzo "l'arbitro su una registrazione conforme" 0 \
    python3 "$QUI/02-filo-validatore.py" \
        "$QUI/02-filo-prove/02-filo-prova-buona.rcpreg" --uscita "$ESITI"

# ⛔ E IL ROSSO CHE DEVE ESSERE ROSSO — il controllo positivo dell'arbitro.
#
#    §11: *«prima di concludere che il validatore non trova errori, gli si da'
#    una registrazione CON UN ERRORE DENTRO e si verifica che lo veda.  Uno
#    strumento che non ha mai trovato niente non e' uno strumento pulito: e'
#    uno strumento non certificato»*.
pezzo "⭐ l'arbitro su una registrazione NON conforme (deve uscire 1)" 1 \
    python3 "$QUI/02-filo-validatore.py" \
        "$QUI/02-filo-prove/02-filo-prova-tipo-storto.rcpreg"

# ⛔ E QUELLO CHE DEVE DIRE «NON HO NIENTE DA GIUDICARE» (uscita 3).
#
#    E' la meta' che si dimentica: un arbitro che uscisse 0 su una
#    registrazione senza un byte di video **assolverebbe senza aver guardato**,
#    ed e' il rilievo R7.4 della fase 1.
pezzo "⭐ l'arbitro su una registrazione senza video (deve uscire 3)" 3 \
    python3 "$QUI/02-filo-validatore.py" \
        "$QUI/02-filo-prove/02-filo-prova-solo-controllo.rcpreg"

# -------------------------------------------------------------------------
dice ""
dice "==========================================================="
dice "  QUEL CHE NON SI PUO' MISURARE OGGI, E PERCHE'"
dice "==========================================================="

if [ "${1:-}" = "--vivo" ] && [ "$AIOQUIC" = si ] && [ "$VIDEO_NEL_PRODOTTO" -gt 0 ]; then
    pezzo "il cliente di prova riceve il fotogramma (porta $PORTA)" 0 \
        python3 "$QUI/02-filo-cliente.py" --porta "$PORTA" \
            --registra "$QUI/02-filo-prove/02-filo-vivo.rcpreg" \
            --uscita "$ESITI"
    pezzo "l'arbitro sulla traccia dal vivo" 0 \
        python3 "$QUI/02-filo-validatore.py" \
            "$QUI/02-filo-prove/02-filo-vivo.rcpreg" --uscita "$ESITI"
else
    salta "il cliente di prova, dal vivo" \
        "il prodotto non spedisce fotogrammi ($VIDEO_NEL_PRODOTTO occorrenze), \
aioquic=$AIOQUIC, --vivo=${1:-no}"
    dice "       ⏳ il suo primo giro E' la prima misura della fase 2, e va"
    dice "          fatto sulla $PORTA, dentro il contenitore"
fi

salta "i pixel decodificati contro quelli catturati" \
    "e' F2.6, e non e' una misura di protocollo"
salta "il credito degli stream oltre i 256 fotogrammi (§2.3)" \
    "la fase 2 consegna UN fotogramma fermo: e' la fase 3"

# -------------------------------------------------------------------------
dice ""
dice "==========================================================="
dice "  IL VERDETTO, CON IL SUO DENOMINATORE"
dice "==========================================================="
dice ""
dice "   pezzi girati:  $FATTI"
dice "   pezzi saltati: $SALTATI   ⛔ e «saltato» non e' «passato»"
dice "   registro:      $ESITI"
dice ""
# ⛔ LE LETTURE DOPPIE, E IL CONTO DELLE REGOLE CHE HANNO UN CASO CHE LE FA
#    SCATTARE.
#
# ⚠ Fino all'11 agosto qui si stampavano le quattro ambiguita' di `RCP.md` con
#   il testo da proporre.  ⭐ Il 12 agosto 2026 quelle quattro sono ENTRATE nel
#   documento (§2.5, §5.2, §6.2) insieme alle altre tre, e questo blocco e'
#   diventato la domanda opposta:
#
#     ⛔ *le regole nuove ce l'hanno, l'ingresso che le fa scattare?*
#
#   Un arbitro che conosce una regola e non ha il caso che la viola non la fa
#   rispettare, e il verde che da' e' quello che da' fiducia.  E il caso che la
#   **rispetta** conta quanto l'altro: senza, una regola scritta troppo larga
#   resterebbe verde su tutto il banco.
dice "== ⭐⛔ LE RIGHE ENTRATE IN \`RCP.md\` IL 12 AGOSTO 2026"
dice "   Sette di mattina (P1-P7), **due di sera** — P8 da D14 (la grazia sui"
dice "   fotogrammi in volo) e P9 da D13 (la chiave vera a ogni cambio di tela) —"
dice "   e ⛔ **due nate dalle due di sera**: P10 (§5.2, QUANDO il client"
dice "   riconfigura) e P11 (§6.2, la finestra al posto de «la precedente»),"
dice "   trovate applicando le prime e curate il giro dopo.  Il numero non e'"
dice "   scritto qui: lo contano i due arbitri."
dice "   Il conto lo calcolano i due arbitri cercando i casi per nome: una"
dice "   regola che perdesse uno dei due diventa rossa qui, non fra sei mesi."
python3 "$QUI/02-filo-fotogramma.py" --elenco | grep -E 'regole con TUTT' | \
    sed 's/^ */   giudice del fotogramma:  /'
python3 "$QUI/02-filo-validatore.py" --elenco | grep -E 'righe con TUTT' | \
    sed 's/^ */   arbitro delle registrazioni: /'
dice ""
# ⛔⛔ E LE CURE CHE `RCP.md` NON PORTA ANCORA.  ⚠ Aggiunto la sera del 12
#    agosto 2026 col difetto **D14**, e la sera stessa il blocco ha cambiato
#    contenuto: D14 e' entrato (P8), e al suo posto ci sono i **due punti in
#    cui le cure di quella sera non reggono** — P10 (le due righe nuove si
#    contraddicono sullo stesso fotogramma) e P11 (la grazia nomina «la tela
#    precedente» al singolare, e chi trascina una finestra ne manda due).
#    ⛔ Trovati **applicando** le righe ai due arbitri, che e' lo stesso modo
#    in cui la mattina si erano trovate le due sbagliate su sette.
#    ⚠ Sta in un blocco SUO e non insieme al conto
#    qui sopra: «righe che il documento porta» e «cure che il documento non ha»
#    sono due fatti diversi, e sommarli darebbe un numero che non vuol dire
#    niente.  ⛔ E la coppia ha una forma diversa: la prova che la fa vedere e
#    quella che impedisce di scriverla troppo larga.
dice "== ⛔⛔ LE PROPOSTE ANCORA APERTE — \`RCP.md\` non le porta"
python3 "$QUI/02-filo-fotogramma.py" --elenco | grep -E 'proposte con TUTTI' | \
    sed 's/^ */   giudice del fotogramma:  /'
python3 "$QUI/02-filo-validatore.py" --elenco | grep -E "proposte con TUTT'E DUE" | \
    sed 's/^ */   arbitro delle registrazioni: /'
dice ""
dice "== ⭐⛔ I PUNTI IN CUI \`RCP.md\` NON DECIDE BENE, in questo capitolo"
dice "   ⚠ Due famiglie, e non sono la stessa cosa: una **lettura doppia** fa"
dice "     divergere due implementazioni attente; una **contraddizione interna**"
dice "     le fa convergere sullo stesso byte sbagliato — ed e' peggio, perche'"
dice "     nessun confronto fra due implementazioni la trova."
python3 "$QUI/02-filo-fotogramma.py" --elenco | grep -A1 'AMBIGUO$' | \
    grep -v '^--$' | sed 's/^/   /'
if ! python3 "$QUI/02-filo-fotogramma.py" --elenco | grep -q 'AMBIGUO$'; then
    dice "   ⭐ nessuna: le OTTO che questo banco ha trovato sono entrate tutte"
    dice "      nel documento il 12 agosto 2026 — quattro di mattina (P2 §6.2 ·"
    dice "      P3 §2.5 · P5 §6.2 · P6 §5.2), tre con loro (P1 · P4 · P7), due"
    dice "      di sera (P8 §6.2 · P9 §5.2) e ⛔ due nate DALLE due di sera"
    dice "      (P10 §5.2 · P11 §6.2), trovate applicandole poche ore dopo."
    dice "   ⚠ E questo NON vuol dire che \`RCP.md\` non ne abbia piu': vuol dire"
    dice "     che non ne restano fra quelle che QUESTO banco sa cercare."
fi

dice ""
if [ "$ROSSI" -gt 0 ]; then
    dice "   ${ROSSO}⛔ F2.4: $ROSSI pezzi su $FATTI non passano${GRIGIO}"
    exit 1
fi
dice "   ${VERDE}⭐ F2.4: $FATTI pezzi su $FATTI passano${GRIGIO}"
dice "   ⚠ e NON e' «il fotogramma arriva»: in questo giro non e' passato un"
dice "     byte sulla rete, e $SALTATI pezzi sono stati saltati per mancanza di"
dice "     prodotto.  Il verde vale per quel che il denominatore dice."
exit 0
