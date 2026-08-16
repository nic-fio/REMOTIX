#!/bin/bash
#
# attrezzi-allinea-innesto.sh — ⛔ GIRA SUL SERVER (fuori dal contenitore).
# Rimette dentro l'innesto i tre file che B3 ci copia, e RICOSTRUISCE.
#
#   bash /media/REMOTIX/src/attrezzi-allinea-innesto.sh guarda   dice e basta
#   bash /media/REMOTIX/src/attrezzi-allinea-innesto.sh allinea  copia + ninja + terreno
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' ESISTE — IL CONTROLLO C'ERA, LA CURA NO
#
# `[M]` la notte fra l'11 e il 12 agosto 2026.  La cura del congedo
# (`DECISIONI.md` §1.12) aveva aggiornato `rcp/rcp.c` alle 13:43; l'innesto —
# `b2/ngtcp2/examples/rcp.c`, cioe' il file da cui si compila il server che SEI
# BANCHI interrogano — era rimasto al codice del mattino.  Per mezza giornata:
#
#   · le certificazioni di B3, B5, B6, B7, B8, B13 erano SCADUTE (i loro file
#     erano cambiati) — e questo il registro lo diceva;
#   · ⛔ ma erano anche IRRIPETIBILI, e questo non lo diceva nessuno:
#     rilanciarle avrebbe scritto sei righe con la data di stanotte **sul
#     codice di prima**.
#
# ⭐ A vederlo e' stato `01-b0-terreno.sh`, in mezzo secondo, al primo giro:
#    *«examples/rcp.c NON e' rcp/rcp.c ⇒ il server misura una versione che
#    nessuno sta leggendo»*.  ⛔ Ma poi la cura e' stata fatta A MANO — `cp` e
#    `ninja` battuti sulla riga di comando — e una cura a mano torna: e' la
#    stessa ragione per cui esiste `01-p5-accendi.sh`.
#
# ⇒ Il controllo dice CHE COSA non va; questo file dice COME si rimette.
#
# ---------------------------------------------------------------------------
# ⛔ E SI RIFIUTA SE NELL'INNESTO C'E' UN GUASTO INNESTATO
#
# B12 e B11 innestano guasti PROPRIO in `examples/rcp.c`.  ⛔ Copiarci sopra il
# sorgente mentre un giro e' in corso toglierebbe il guasto **sotto chi lo sta
# misurando**, e quel giro direbbe «il banco non e' diventato rosso» di un
# banco a cui e' stato tolto l'imputato di mano.  ⇒ Se le marche ci sono, qui
# ci si ferma e lo si dice.
#
# ⛔ E si guarda l'ESITO di `ninja`, non la presenza del binario dopo: e' la
#    trappola gia' pagata su B11 (`LEZIONI.md` §1.9 punto 8) — un binario di
#    due ore prima risponde «esisto» come uno di adesso.
set -uo pipefail

E=${ENTRA:-/media/REMOTIX/enter.sh}
FUORI=${FUORI:-/media/REMOTIX/src}
DENTRO=${DENTRO:-/srv/src}
ESEMPI_FUORI=$FUORI/b2/ngtcp2/examples
ESEMPI_DENTRO=$DENTRO/b2/ngtcp2/examples
FILE="rcp.c rcp.h autenticazione.c"

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

AZIONE=${1:-guarda}
case "$AZIONE" in guarda|allinea) ;; *) echo "uso: $0 [guarda|allinea]"; exit 2 ;; esac

# ---------------------------------------------------------------------------
log "1. I tre file che B3 copia dentro l'innesto"
DIVERSI=""
MANCANTI=0
for f in $FILE; do
	s=$FUORI/rcp/$f
	d=$ESEMPI_FUORI/$f
	if [ ! -f "$s" ] || [ ! -f "$d" ]; then
		ko "⛔ non posso confrontare «$f»: manca $( [ -f "$s" ] || echo "rcp/$f" ) $( [ -f "$d" ] || echo "examples/$f" )"
		MANCANTI=$((MANCANTI+1))
		continue
	fi
	a=$(md5sum "$s" | cut -d' ' -f1)
	b=$(md5sum "$d" | cut -d' ' -f1)
	if [ "$a" = "$b" ]; then
		ok "$f identico  ($a)"
	else
		ko "⛔ $f DIVERSO — sorgente $a · innesto $b"
		# ⭐ E si dice QUANTE righe ballano, perche' «diverso» e «diverso di
		#    una cura intera» mandano a guardare in due posti diversi.
		inf "   righe che cambiano: $(diff "$s" "$d" | grep -c '^[<>]')"
		DIVERSI="$DIVERSI $f"
	fi
done
[ "$MANCANTI" -gt 0 ] && { ko "⛔ con dei file mancanti non allineo niente"; exit 2; }

# ⚠ E si dichiara quel che il terreno NON confronta: oggi guarda solo rcp.c.
# ⛔ E niente apici inversi dentro le virgolette doppie: la prima volta che ho
#    girato questo file la riga qui sotto ha ESEGUITO «01-b0-terreno.sh» invece
#    di stamparlo — «command not found» in mezzo a un attrezzo che funzionava.
inf "⚠ 01-b0-terreno.sh confronta solo rcp.c; qui si guardano tutti e tre"

# ---------------------------------------------------------------------------
# ⛔⭐ E «IDENTICI» NON BASTA: IL BINARIO DEV'ESSERE PIU' NUOVO DEI SORGENTI.
#
# `[M]` 12 agosto 2026, e l'ha trovato la prova di questo stesso attrezzo: dopo
# la copia i tre file hanno la DATA DI ADESSO, quindi un binario costruito
# prima e' vecchio anche se il contenuto e' lo stesso.  ⛔ Se il giro si ferma
# fra la copia e `ninja` — a me l'ha fermato un `timeout` — resta una scena in
# cui le impronte combaciano, `guarda` direbbe «allineato», e il terreno
# boccerebbe lo stesso con «il binario e' piu' vecchio di un sorgente che
# dichiara».  ⇒ Si guarda anche l'orologio, non solo le impronte.
BINARIO=$FUORI/b2/ngtcp2/build/examples/bsslserver
VECCHIO=""
if [ -f "$BINARIO" ]; then
	for f in $FILE; do
		[ "$ESEMPI_FUORI/$f" -nt "$BINARIO" ] && VECCHIO="$VECCHIO $f"
	done
	if [ -n "$VECCHIO" ]; then
		ko "⛔ il binario e' PIU' VECCHIO di:$VECCHIO"
		inf "   bsslserver: $(stat -c %y "$BINARIO" | cut -c1-19)"
		inf "   ⇒ va ricostruito anche se le impronte combaciano"
	else
		ok "e il binario e' piu' nuovo di tutti e tre ($(stat -c %y "$BINARIO" | cut -c1-19))"
	fi
else
	ko "⛔ $BINARIO non c'e': l'innesto non e' mai stato costruito"
	VECCHIO=" (manca il binario)"
fi

if [ -z "$DIVERSI" ] && [ -z "$VECCHIO" ]; then
	ok "⭐ l'innesto e' gia' allineato ai sorgenti, e il binario e' di dopo"
	[ "$AZIONE" = guarda ] && exit 0
	inf "niente da copiare e niente da ricostruire: si va dritti al terreno"
fi

# ---------------------------------------------------------------------------
log "2. ⛔ C'e' un guasto innestato dentro l'innesto?"
TROVATI=0
for m in "REMOTIX B12 GUASTO" "REMOTIX B11"; do
	n=$(grep -ac "$m" "$ESEMPI_FUORI/rcp.c" 2>/dev/null)
	if [ "${n:-0}" -gt 0 ]; then
		ko "⛔ «$m» compare $n volta/e in examples/rcp.c"
		TROVATI=$((TROVATI+1))
	else
		ok "nessuna traccia di «$m»"
	fi
done
if [ "$TROVATI" -gt 0 ]; then
	ko "⛔ NON TOCCO NIENTE: c'e' un guasto innestato, e ricopiarci sopra il"
	ko "   sorgente lo toglierebbe SOTTO chi lo sta misurando — quel giro"
	ko "   scriverebbe «il banco non e' diventato rosso» di un banco a cui"
	ko "   e' stato tolto l'imputato di mano."
	ko "   ⇒ Aspetta che il giro finisca, o toglilo con «--togli»."
	exit 3
fi

if [ "$AZIONE" = guarda ]; then
	inf "«guarda» si ferma qui: per copiare e ricostruire, «allinea»"
	exit 1
fi

# ---------------------------------------------------------------------------
if [ -n "$DIVERSI" ]; then
	log "3. Si copia il sorgente dentro l'innesto"
	for f in $DIVERSI; do
		bash "$E" --root "cp $DENTRO/rcp/$f $ESEMPI_DENTRO/$f" || {
			ko "⛔ la copia di «$f» e' fallita"; exit 3; }
		a=$(md5sum "$FUORI/rcp/$f" | cut -d' ' -f1)
		b=$(md5sum "$ESEMPI_FUORI/$f" | cut -d' ' -f1)
		[ "$a" = "$b" ] && ok "$f copiato, e le impronte adesso combaciano ($a)" \
		                || { ko "⛔ $f copiato ma le impronte NON combaciano"; exit 3; }
	done

fi

if [ -n "$DIVERSI" ] || [ -n "$VECCHIO" ]; then
	log "4. Si ricostruisce — e si guarda l'ESITO, non il binario"
	# ⛔⭐ QUI C'ERA `>/dev/null 2>&1` **ATTORNO** A `enter.sh`, ED E' LA
	#     TRAPPOLA CHE `FASI.md` §00-ambiente B3.3 DICHIARA PAGATA QUATTRO
	#     VOLTE — questa e' la quinta.  `[M]` 12 agosto 2026, 15:22-15:32.
	#
	# `enter.sh` chiede la parola d'ordine di `sudo` con `sudo -v -S -p`: la
	# richiesta esce su **stderr** e la risposta si legge da stdin.  Buttando
	# via lo stderr, la domanda non arriva a nessuno — e chi lancia il giro da
	# un'altra macchina non puo' rispondere a una domanda che non vede.
	# ⚠ E il sintomo e' quello che inganna: non un errore, ma un attrezzo
	#   **lento**.  `[M]` `ps` sul server: `sudo -v -S -p Password sudo:` fermo
	#   da 5 minuti e 28 secondi, con `attrezzi-allinea-innesto.sh` bloccato
	#   subito **dopo la copia e prima di `ninja`** — cioe' con i sorgenti gia'
	#   sostituiti e il binario ancora quello di prima: la scena PEGGIORE, che
	#   e' esattamente quella che il commento in cima a questo file descrive.
	# ⛔ Da un terminale interattivo il difetto e' invisibile finche' il credito
	#    di `sudo` regge: si vede solo quando scade — cioe' sui giri lunghi.
	#
	# ⭐ La cura e' quella di casa (`01-b12-lancia.sh`, `01-p1-prodotto.sh`): si
	#    redirige **dentro** le virgolette, su un file, e il file lo si legge
	#    dopo.  Cosi' l'esito resta quello di `ninja` e l'errore non si perde.
	rm -f "$FUORI/attrezzi-allinea-ninja.log"
	if bash "$E" --root "ninja -C $DENTRO/b2/ngtcp2/build bsslserver > $DENTRO/attrezzi-allinea-ninja.log 2>&1"; then
		ok "⭐ bsslserver ricostruito"
		# ⚠ E si dice quante regole ha eseguito: «ninja non aveva niente da
		#   fare» e «ninja ha ricompilato» escono tutt'e due 0, e dopo una
		#   copia di sorgenti le due cose non sono la stessa.
		inf "   $(tail -1 "$FUORI/attrezzi-allinea-ninja.log" 2>/dev/null)"
	else
		ko "⛔ la compilazione e' FALLITA: il binario che c'e' e' quello di"
		ko "   prima, e adesso il sorgente e' cambiato sotto di lui — cioe'"
		ko "   la scena PEGGIORE.  L'errore:"
		[ -f "$FUORI/attrezzi-allinea-ninja.log" ] \
			&& tail -20 "$FUORI/attrezzi-allinea-ninja.log" | sed 's/^/        /' \
			|| ko "   ⛔ e non c'e' nemmeno il registro di ninja: non ho letto niente"
		exit 3
	fi
fi

# ---------------------------------------------------------------------------
log "5. ⛔ E lo dice il terreno, non io"
bash "$FUORI/01-b0-terreno.sh" innesto
T=$?
if [ "$T" -eq 0 ]; then
	printf '\n    \033[1;32m⭐ innesto allineato, e il terreno regge\033[0m\n'
else
	printf '\n    \033[1;31m⛔ il terreno NON regge (uscita %s): non lanciare banchi\033[0m\n' "$T"
fi
exit "$T"
