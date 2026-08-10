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
#
# ⛔ MA «CHE COSA» SI LEGGE DAL VERDETTO, NON DALLA TRACCIA DEGLI EVENTI —
#    `[M]` 10 agosto 2026, ed e' il difetto che questo controllo aveva ADDOSSO
#    DALLA NASCITA, cioe' dalla cura di R8.4 di poche ore prima.
#
#    Qui si cercava `connessione TERMINATA` su TUTTO il registro della prima.
#    ⚠ Ma quella riga il cliente la stampa ANCHE quando la finestra di
#    `--resta` finisce bene: esce, `connect()` chiude la connessione, e
#    aioquic alza `ConnectionTerminated` codice 0.  Il registro del giro
#    diceva, in quest'ordine:
#        ⭐ ancora attaccato dopo 25.0 s: niente e' caduto
#        [quic] connessione TERMINATA: codice 0 · (nessun motivo)
#    e il banco leggeva la seconda riga come una prova contro il server.
#
# ⛔ IL SERVER AVEVA RAGIONE, e il suo registro lo dimostra: `posto PRESO`
#    (:48499), `posto NEGATO` alla seconda con `congedo motivo=0x0f`, cinque
#    PING di trasporto per tenere viva la prima, e `posto LASCIATO` **solo
#    dopo** aver RICEVUTO il `CONNECTION_CLOSE` della prima.  Tre cause con lo
#    stesso aspetto — il server che chiude, QUIC che scade, il cliente che
#    esce da se' — e questo grep le confondeva tutt'e tre.
#
# ⭐ La cura: si chiede al cliente il suo VERDETTO, che e' una riga sola e
#    dice chi e' caduto e quando.  E si pretende il controllo positivo
#    (`CODER.md` §3.10): non «non trovo niente di brutto», ma «il cliente ha
#    vegliato per tutta la finestra e dichiara che niente e' caduto».
SOPRAVVISSUTA=no
grep -q "ancora attaccato dopo" "$QUI/b3-viva.log" && SOPRAVVISSUTA=si
CADUTA=$(grep -m1 "NON sono rimasto attaccato" "$QUI/b3-viva.log" \
         | sed 's/.*NON sono rimasto attaccato: //')
if [ "$VIVA" -eq 0 ] && [ "$SOPRAVVISSUTA" = si ] && [ -z "$CADUTA" ]; then
	ok "⭐ e la PRIMA e' sopravvissuta: nessun client vivo viene spodestato"
	inf "   (uscita 0, e il cliente dichiara di aver vegliato senza cadute)"
elif [ -n "$CADUTA" ]; then
	# ⛔ E NON SI ACCUSA IL SERVER SENZA AVERLO RICONOSCIUTO: solo la sessione
	#    WebTransport chiusa da lui e' uno spodestamento.  Una connessione
	#    caduta da se' e' un'altra cosa, e darla al server e' il rosso puntato
	#    sull'imputato sbagliato — il difetto piu' caro che questo progetto ha
	#    pagato.
	ko "⛔ la prima NON e' sopravvissuta (uscita $VIVA): $CADUTA"
	case "$CADUTA" in
	*"chiusa dal server"*)
		ko "   il server ha spodestato chi c'era, ed e' il contrario di I2" ;;
	*)
		ko "   ⚠ ma NON e' il server ad aver chiuso la sessione: prima di dare"
		ko "     il rosso al prodotto, si guarda il registro del server" ;;
	esac
	tail -5 "$QUI/b3-viva.log" | sed 's/^/        /'
	ESITO=1
else
	ko "⛔ la prima non ha dichiarato niente (uscita $VIVA): il giro non prova"
	ko "   niente, e il verde sarebbe da assenza di prove"
	tail -5 "$QUI/b3-viva.log" | sed 's/^/        /'
	ESITO=1
fi
exit "$ESITO"
