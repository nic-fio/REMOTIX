#!/bin/bash
#
# 01-b3-terzo-giro.sh — ⚠ gira DENTRO il contenitore, chiamato da
#                       01-b3-lancia.sh con una sola riga.
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' UN FILE A PARTE
#
# Il terzo giro di B3 vuole due clienti contemporanei: uno che resta attaccato
# e uno che arriva dopo.  Scriverlo dal di fuori significa una sottoshell in
# secondo piano, o una sostituzione di comando, attorno a `enter.sh` — e
# tutt'e due si portano via la richiesta di password di sudo, lasciando lo
# script ad aspettare una domanda che nessuno vede.  Il 10 agosto 2026 e'
# successo tre volte in un giorno, in tre vesti diverse.
#
# ⭐ Qui dentro non c'e' nessun sudo e nessuna shell annidata: due processi e
#    due file.
#
# ---------------------------------------------------------------------------
# CHE COSA PROVA, E LA META' CHE SI DIMENTICA
#
#   - la SECONDA connessione dev'essere rifiutata con GIA_ATTIVA_REMOTA (0x0F)
#   - ⛔ e la PRIMA deve SOPRAVVIVERE: «chi viene rifiutato e' chi arriva, non
#     chi c'era».  Un server che spodestasse il primo darebbe alla seconda
#     esattamente lo stesso rosso, ed e' il comportamento opposto.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=/srv/src
IND=${1:-192.168.0.2}
PORTA=${2:-7447}
UTENTE=prova
PAROLA=parola-di-prova

ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

# ⛔ E SI BUTTANO ANCHE LE DUE REGISTRAZIONI — rilievo R8.5.
#
#    Fino al 10 agosto qui si buttavano i registri e non i `.rcpreg`, che sono
#    esattamente i file che l'arbitro di B4 giudica.  Il caso concreto: si
#    spegne il server, il giro esce a meta' senza scrivere niente, e il
#    validatore trova la registrazione di IERI e stampa «⭐ conforme» mentre il
#    cliente di questo giro non si e' nemmeno collegato.  E' il verde da un file
#    stantio che `01-b3-lancia.sh` dichiarava curato — ma la cura stava solo nel
#    file che lancia i primi due giri, non in questo.
rm -f "$QUI/b3-viva.log" "$QUI/b3-terza.log" "$QUI/b3-viva.attaccato" \
      "$QUI/b3-viva.rcpreg" "$QUI/b3-terza.rcpreg"

# ⚠ `python3 -u`: senza, lo stdout rediretto su file resta nel buffer fino
#   all'uscita del processo.  E' meta' della causa del difetto qui sotto.
python3 -u "$QUI/01-b3-cliente.py" --indirizzo "$IND" --porta "$PORTA" \
	--utente "$UTENTE" --parola "$PAROLA" \
	--registra "$QUI/b3-viva.rcpreg" --resta 25 \
	--segnale "$QUI/b3-viva.attaccato" > "$QUI/b3-viva.log" 2>&1 &
PRIMA=$!

# ⛔ Si aspetta un FILE, non una riga di registro.
#
#    Il primo giro del 10 agosto cercava la parola «SESSIONE» nel registro
#    della prima connessione — e Python bufferizza lo stdout su file: quella
#    riga compariva solo all'uscita del processo, cioe' **nell'istante in cui
#    la prima si staccava**.  Il banco diceva «la prima e' attaccata» leggendo
#    una verita' appena scaduta, la seconda arrivava sempre a posto libero, e
#    ⛔ **il rosso finiva sul server, che non c'entrava niente**.
#
# ⭐ Un file scritto e chiuso e' un fatto; una riga stampata e' una speranza
#    sul momento in cui qualcuno la vedra'.
ATTACCATA=no
for _ in $(seq 1 15); do
	if [ -f "$QUI/b3-viva.attaccato" ]; then
		ATTACCATA=si
		break
	fi
	sleep 1
done
if [ "$ATTACCATA" != si ]; then
	ko "la prima non si e' attaccata: il terzo giro non prova niente"
	sed 's/^/        /' "$QUI/b3-viva.log"
	kill "$PRIMA" 2>/dev/null
	exit 3
fi
ok "la prima e' attaccata"

inf "adesso arriva la seconda"
# ⚠ `--resta 25` sulla prima, e questo controllo qui: la finestra d'attacco
#   arriva a 15 s e la seconda ne prende almeno due — se la prima fosse uscita
#   PER CONTO SUO prima che la seconda arrivi, il giro misurerebbe «posto
#   libero» credendo di misurare «posto occupato», e nessun codice d'uscita lo
#   direbbe.  ⭐ Qui `/proc` si usa per INVALIDARE, non per concludere: un
#   processo che non c'e' piu' non e' certamente attaccato.
if [ ! -d "/proc/$PRIMA" ]; then
	ko "la prima e' gia' uscita prima che la seconda arrivasse: la finestra"
	ko "   non regge, e questo giro non prova niente"
	tail -5 "$QUI/b3-viva.log" | sed 's/^/        /'
	exit 3
fi
python3 "$QUI/01-b3-cliente.py" --indirizzo "$IND" --porta "$PORTA" \
	--utente "$UTENTE" --parola "$PAROLA" \
	--registra "$QUI/b3-terza.rcpreg" > "$QUI/b3-terza.log" 2>&1
SECONDA=$?
tail -4 "$QUI/b3-terza.log" | sed 's/^/        /'

ESITO=0
if grep -q "GIA_ATTIVA_REMOTA" "$QUI/b3-terza.log"; then
	ok "⭐ la seconda e' rifiutata con GIA_ATTIVA_REMOTA (0x0F), uscita $SECONDA"
	# ⚠ Questa e' una stringa stampata, non i byte: chi giudica i byte e' il
	#   validatore di B4, e adesso la traccia del rifiuto gliela si consegna —
	#   `b3-terza.rcpreg` si scrive anche quando la stretta di mano non riesce
	#   (rilievo R8.9, curato in 01-b3-cliente.py).
	if [ -f "$QUI/b3-terza.rcpreg" ]; then
		inf "la traccia del rifiuto e' in b3-terza.rcpreg, per l'arbitro"
	else
		ko "⛔ ma la traccia del rifiuto NON e' stata scritta: l'arbitro di"
		ko "   B4 non avra' niente da giudicare"
		ESITO=1
	fi
else
	ko "⛔ la seconda NON e' stata rifiutata con 0x0F (uscita $SECONDA)"
	ESITO=1
fi

wait "$PRIMA"
VIVA=$?
# ⛔ «LA PRIMA E' SOPRAVVISSUTA» NON SI LEGGE DA UN PROCESSO CHE DORME —
#    rilievo R8.4.
#
#    Il codice d'uscita da solo diceva 0 qualunque cosa fosse successa alla
#    connessione: un server che spodestasse il primo per far posto al secondo —
#    cioe' il comportamento OPPOSTO a I2, e quello che questo giro esiste per
#    escludere — lasciava `VIVA=0` e faceva stampare «nessun client vivo viene
#    spodestato».  ⭐ La prova stava nel file accanto e si leggeva solo nel ramo
#    rosso: la riga `[wt] sessione chiusa dal server` in b3-viva.log.
#
# ⭐ Adesso sono due letture indipendenti: il cliente esce 4 se qualcosa e'
#    caduto, e il suo registro dice CHE COSA.
SPODESTATA=
if grep -q "sessione chiusa dal server" "$QUI/b3-viva.log"; then
	SPODESTATA="il server le ha chiuso la sessione"
elif grep -q "connessione TERMINATA" "$QUI/b3-viva.log"; then
	SPODESTATA="la connessione e' stata terminata"
fi
if [ "$VIVA" -eq 0 ] && [ -z "$SPODESTATA" ]; then
	ok "⭐ e la PRIMA e' sopravvissuta: nessun client vivo viene spodestato"
	inf "   (uscita 0, e nel suo registro non c'e' nessuna caduta)"
else
	ko "⛔ la prima NON e' sopravvissuta (uscita $VIVA): ${SPODESTATA:-uscita non zero}"
	ko "   il server ha spodestato chi c'era, ed e' il contrario di I2"
	tail -5 "$QUI/b3-viva.log" | sed 's/^/        /'
	ESITO=1
fi
exit "$ESITO"
