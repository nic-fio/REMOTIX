#!/bin/bash
#
# 01-b3-quarto-giro.sh — ⚠ gira DENTRO il contenitore.
#
#   ⛔ la 2ª DOPO IL SILENZIO della 1ª — 35 secondi, con `max_idle_timeout`
#      alzato a 120.
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' 35 SECONDI A TIMEOUT 120, E NON 30 A TIMEOUT PREDEFINITO
#
# E' il rilievo **R3.19**, ed e' la differenza fra una prova e una benedizione.
#
# Con il tetto d'inattivita' predefinito (30 s), a chiudere la prima connessione
# sarebbe **QUIC**: la struttura legata alla connessione si libererebbe da se',
# e un server **senza nessuna nozione di sessione staccata** resterebbe verde.
# ⛔ Il banco benedirebbe la violazione di **I4**.
#
# Alzando il tetto a 120 secondi, dopo 35 la connessione della prima e' ancora
# **viva** — e se il posto si libera lo stesso, e' perche' il server ha il suo
# **orologio del silenzio** (`SPECIFICHE.md` §5.3, `DECISIONI.md` §4.4).
#
# ⛔ E IL TETTO SI MISURA, NON SI DA' PER MESSO — rilievo R8.3.
#
#    Fino al 10 agosto 2026 questa era una premessa scritta in un commento e
#    basta: nessuno accendeva il server con `--timeout=120s` per B3, e nessuno
#    leggeva il tetto dal filo.  Col tetto predefinito la prima connessione al
#    minuto 35 **e' gia' caduta da sola**, il posto si libera senza che il
#    server abbia nessun orologio, e ⛔ **il giro benedice la violazione che
#    dichiara di escludere** — E5, un «fatto» che era una deduzione.
#
#    ⭐ Adesso il primo passo del giro chiede il tetto AL PARI, con la sonda di
#       B2 che gia' lo sa leggere.  Se non e' 120 000 ms il giro non parte.
#
#    Il server va acceso cosi', dall'altra macchina:
#
#      bash /media/REMOTIX/src/01-b2-lancia-wt.sh accendi 192.168.0.2 7447 --timeout=120s
#
# ---------------------------------------------------------------------------
# ⛔ E IL CONTROLLO CHE DICE NO, SENZA IL QUALE NON SI PROVA NIENTE
#
# «Dopo 35 secondi la seconda entra» e' compatibile con **«la seconda entra
# sempre»**, cioe' con un server che non guarda il registro affatto.  Per
# questo il giro ha due tempi:
#
#   a +6 s   la seconda DEVE essere rifiutata con GIA_ATTIVA_REMOTA
#   a +35 s  la terza  DEVE entrare
#
# ⭐ Sono lo stesso server, lo stesso utente e lo stesso silenzio: cambia solo
#    l'orologio.  Senza il primo tempo, il secondo non dimostra l'orologio.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=/srv/src
IND=${1:-192.168.0.2}
PORTA=${2:-7447}
UTENTE=prova
PAROLA=parola-di-prova

# ---------------------------------------------------------------------------
# ⛔ LA PAROLA D'ORDINE NON PASSA PIU' DALLA RIGA DI COMANDO — difetto **D12**,
#    curato il 12 agosto 2026.
#
# ⛔ QUI C'ERA `--parola-file "$PAROLA_FILE"`, e `python3` e' un PROCESSO: la parola
#    stava nel suo `argv`, cioe' in `/proc/<pid>/cmdline`, che su Linux e'
#    **leggibile da chiunque** — un `ps` durante il giro la stampava per
#    intero, e i banchi di questa macchina girano mentre ci lavorano altri.
#
# ⭐ LA STRADA E' QUELLA GIA' IN CASA (`banchi/01-b10-lancia.sh`), e non un
#    secondo modo: un file `0600` scritto con `printf` — un **builtin** della
#    shell, quindi nemmeno la scrittura passa per un processo con la parola in
#    `argv` — passato al banco come `--parola-file`, e cancellato con una
#    `trap` anche se il giro muore a meta'.  Nel `cmdline` finisce il PERCORSO.
#
# ⚠ E il nome porta la sigla di CHI lo scrive: due giri che scrivessero lo
#   stesso file si cancellerebbero la parola a vicenda — la stessa forma che ha
#   fatto nascere il `PREFISSO` di `01-p5-accendi.sh`.
PAROLA_FILE=$QUI/tmp/b3-quarto-parola

ripulisci_parola() { rm -f "$PAROLA_FILE"; }
trap ripulisci_parola EXIT

# ⛔ `umask` IN UNA SOTTOSHELL — la riga che B10 ha pagato con un giro intero:
#    `umask 077` nudo resta addosso a tutto quel che viene dopo.
mkdir -p "$QUI/tmp" \
	&& ( umask 077; : > "$PAROLA_FILE" ) \
	&& chmod 600 "$PAROLA_FILE" \
	|| { printf '    ⛔ non si scrive %s: il giro non parte\n' "$PAROLA_FILE"; exit 2; }
printf '%s\n' "$PAROLA" > "$PAROLA_FILE"

ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

cliente() # $1 = etichetta, $2.. = opzioni
{
	local et=$1; shift
	python3 -u "$QUI/01-b3-cliente.py" --indirizzo "$IND" --porta "$PORTA" \
		--utente "$UTENTE" --parola-file "$PAROLA_FILE" \
		--registra "$QUI/b3-$et.rcpreg" "$@" > "$QUI/b3-$et.log" 2>&1
}

# ⛔ Si buttano ANCHE le registrazioni, non solo i registri: un `.rcpreg`
#    rimasto da un giro precedente si fa giudicare «conforme» mentre il cliente
#    di questo giro non si e' nemmeno collegato — e' il verde da un file stantio
#    del 10 agosto 2026 (rilievo R8.5, stessa forma).
rm -f "$QUI/b3-muta.log" "$QUI/b3-muta.attaccato" "$QUI/b3-presto.log" \
      "$QUI/b3-tardi.log" "$QUI/b3-muta.rcpreg" "$QUI/b3-presto.rcpreg" \
      "$QUI/b3-tardi.rcpreg" "$QUI/b3-tetto.log"

# ── IL TETTO D'INATTIVITA', LETTO DAL PARI ──────────────────────────────────
# ⛔ E' la premessa di tutto il giro (vedi in cima): senza i 120 secondi, a
#    liberare il posto al minuto 35 e' QUIC e non il server.  Si legge con la
#    sonda di B2, che i parametri di trasporto li prende dove arrivano invece
#    che dalla configurazione di chi li manda.
# ⚠ Non si guarda il suo codice d'uscita: la sonda giudica cinque proprieta' e
#   qui ne interessa una sola.  Si legge il NUMERO, e «non ho letto niente» ha
#   un ramo suo — «vuoto» e «proibito» non hanno lo stesso aspetto.
TETTO_ATTESO=${TETTO_ATTESO:-120000}
# ⛔ `--bersaglio` e' obbligatorio dall'11 agosto 2026 e non ha predefinito:
#    un giro non deve poter misurare il server sbagliato per distrazione.
#    Questo giro e' scritto per l'INNESTO — i 120 000 ms qui sopra sono suoi,
#    il prodotto ha 30 000 fissi — quindi il valore e' `innesto`, dichiarato e
#    non dedotto.  ⚠ Trovato l'11 agosto 2026 riparando la stessa cucitura in
#    `01-b6-lancia.sh`: la prima cura era stata applicata in un posto solo.
python3 "$QUI/01-b2-sonda-trasporto.py" --bersaglio innesto \
	--indirizzo "$IND" --porta "$PORTA" \
	--etichetta quarto-giro --idle-atteso "$TETTO_ATTESO" \
	> "$QUI/b3-tetto.log" 2>&1
TETTO=$(grep -m1 'max_idle_timeout *=' "$QUI/b3-tetto.log" | tr -dc '0-9')
if [ -z "$TETTO" ]; then
	ko "non ho potuto leggere max_idle_timeout dal pari: il giro non parte"
	ko "   (senza il tetto non si sa chi liberera' il posto — R8.3)"
	tail -6 "$QUI/b3-tetto.log" | sed 's/^/        /'
	exit 5
fi
if [ "$TETTO" -ne "$TETTO_ATTESO" ]; then
	ko "⛔ il tetto d'inattivita' sul filo e' $TETTO ms, non $TETTO_ATTESO"
	ko "   Con questo tetto la prima connessione cade da sola prima dei 35 s,"
	ko "   e «la terza entra» non direbbe niente sull'orologio del server."
	inf "accendi il server con --timeout=120s (vedi l'intestazione)"
	exit 5
fi
ok "⭐ tetto d'inattivita' misurato sul filo: $TETTO ms — la premessa regge"

# La prima si attacca e poi TACE per 45 secondi.  ⚠ Non manda niente: i
# riscontri di QUIC che partono nel frattempo sono del trasporto, e
# l'orologio del silenzio si misura sui byte di RCP.
cliente muta --resta 45 --segnale "$QUI/b3-muta.attaccato" &
MUTA=$!

ATTACCATA=no
for _ in $(seq 1 15); do
	[ -f "$QUI/b3-muta.attaccato" ] && { ATTACCATA=si; break; }
	sleep 1
done
if [ "$ATTACCATA" != si ]; then
	ko "la prima non si e' attaccata: il quarto giro non prova niente"
	sed 's/^/        /' "$QUI/b3-muta.log"
	kill "$MUTA" 2>/dev/null
	exit 3
fi
T0=$(date +%s)
ok "la prima e' attaccata, e da adesso tace"

ESITO=0

# ── a +6 s: il controllo che dice NO ────────────────────────────────────────
sleep 6
inf "+6 s — la seconda arriva PRIMA che l'orologio scatti"
cliente presto
if grep -q "GIA_ATTIVA_REMOTA" "$QUI/b3-presto.log"; then
	ok "⭐ rifiutata con GIA_ATTIVA_REMOTA: il posto e' ancora occupato"
else
	ko "⛔ NON rifiutata: il server non guarda il registro, e il secondo"
	ko "   tempo di questo giro non dimostrerebbe niente"
	tail -4 "$QUI/b3-presto.log" | sed 's/^/        /'
	ESITO=1
fi

# ── a +35 s: la terza deve ENTRARE ──────────────────────────────────────────
while [ $(( $(date +%s) - T0 )) -lt 35 ]; do
	sleep 1
done
inf "+$(( $(date +%s) - T0 )) s — la terza arriva DOPO i trenta secondi di silenzio"
cliente tardi
ETARDI=$?
# ⛔ NON `grep -q "SESSIONE"` — rilievo R8.1, ed e' la trappola peggiore che
#    questo banco abbia avuto.
#
#    Il rifiuto che questo giro esiste per VEDERE porta la parola «SESSIONE»
#    dentro il proprio messaggio d'errore: il cliente stampa «CONGEDO invece di
#    SESSIONE: motivo 0x0f = GIA_ATTIVA_REMOTA», e il `grep` la trovava.  ⛔ Un
#    server senza orologio del silenzio, che al minuto 35 rifiuta ancora, faceva
#    stampare al banco che l'orologio c'e'.  E una seconda volta:
#    «SESSIONE_NON_SERVIBILE» contiene «SESSIONE» anche lui.
#
# ⭐ Il dato giusto c'era e si buttava: il codice d'uscita del cliente, che e' 0
#    SOLO dopo un `SESSIONE` letto sul filo.
# ⚠ E la registrazione NON e' la prova: da quando si scrive anche il rifiuto
#   (R8.9), `b3-tardi.rcpreg` esiste in tutt'e due i casi — e' materiale per
#   l'arbitro di B4, non un verdetto.
if [ "$ETARDI" -eq 0 ]; then
	ok "⭐ ENTRATA: chi tace e' staccato, chi arriva entra (§5.3, §4.4)"
	inf "   (uscita 0, cioe' SESSIONE letto sul filo; la traccia e' in"
	inf "    b3-tardi.rcpreg, per l'arbitro di B4)"
else
	ko "⛔ NON entrata (uscita $ETARDI): il server non ha l'orologio del"
	ko "   silenzio, oppure lo misura sui byte di QUIC invece che su RCP"
	tail -4 "$QUI/b3-tardi.log" | sed 's/^/        /'
	ESITO=1
fi

# ⛔ E la connessione della prima dev'essere ANCORA VIVA: se fosse caduta,
#    a liberare il posto sarebbe stato QUIC e non il server — che e'
#    esattamente quel che questo giro esiste per escludere.
#
# ⛔ NON si guarda `/proc/$MUTA` — rilievo R8.2.  Quel controllo misura il
#    PROCESSO, non la connessione: il cliente dormiva, e restava vivo e verde
#    anche con la connessione chiusa da QUIC o la sessione chiusa dal server —
#    cioe' era cieco esattamente sull'imputato da escludere.
#
# ⭐ Adesso il cliente resta con gli occhi aperti e DICE che cosa e' caduto
#    (01-b3-cliente.py, il ramo `--resta`).  Qui si leggono le sue righe, e i
#    tre casi hanno tre nomi diversi invece di un `si`/`no`.
#
# ⚠ Dichiarato: le prime due sono letture NEGATIVE — si conclude dall'assenza
#   di una riga.  Regge perche' la riga esiste ed e' stampata dal cliente sul
#   suo evento (`[quic] connessione TERMINATA`, `[wt] sessione chiusa`), con
#   `python3 -u`, quindi sul file c'e' gia' quando la si cerca.
if grep -q "connessione TERMINATA" "$QUI/b3-muta.log"; then
	ko "⛔ la CONNESSIONE della prima e' caduta: a liberare il posto puo'"
	ko "   essere stato il trasporto, e questo giro non prova niente"
	grep "connessione TERMINATA" "$QUI/b3-muta.log" | sed 's/^/        /'
	ESITO=1
elif grep -q "sessione chiusa dal server" "$QUI/b3-muta.log"; then
	ok "⭐ il posto l'ha liberato il SERVER: ha chiuso la sessione della prima"
	grep "sessione chiusa dal server" "$QUI/b3-muta.log" | sed 's/^/        /'
	inf "⚠ la connessione pero' non e' piu' aperta: e' una scelta diversa da"
	inf "  «si libera il posto e si lascia aperta», e va guardata nel registro"
	inf "  del server prima di scriverla da qualche parte"
elif [ -d "/proc/$MUTA" ]; then
	ok "⭐ la connessione della prima e' ancora viva e nessuno l'ha chiusa:"
	ok "   a liberare il posto e' stato il SERVER, non il tetto di QUIC"
else
	ko "⛔ la prima e' uscita da sola senza dire perche': non si puo' dire"
	ko "   chi ha liberato il posto"
	tail -4 "$QUI/b3-muta.log" | sed 's/^/        /'
	ESITO=1
fi

wait "$MUTA" 2>/dev/null
exit "$ESITO"
