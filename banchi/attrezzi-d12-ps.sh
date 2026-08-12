#!/bin/bash
#
# attrezzi-d12-ps.sh — ⛔ LA CURA DI **D12** NON SI DICHIARA: SI GUARDA IN `ps`.
#
#   bash /media/REMOTIX/src/attrezzi-d12-ps.sh        (gira DOVE stanno i banchi)
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' ESISTE — e non e' una formalita'
#
# `LEZIONI.md` §1.9: «non l'ho trovata» e «non ho guardato» hanno lo stesso
# aspetto.  Una cura dichiarata senza la misura che la prova e' la forma **E5**
# — un fatto che era una deduzione.  ⛔ E qui il rischio e' peggio del solito:
# la prova e' un'**ASSENZA**, e un'assenza si dimostra solo con accanto un
# controllo positivo che dica «lo strumento, in quell'istante, stava guardando».
#
# ⇒ Il numero che conta non e' lo zero: e' il **denominatore** accanto allo
#   zero.  Senza, «la parola non c'era» e «non ho guardato» sono la stessa riga.
#
# ---------------------------------------------------------------------------
# ⛔ LE DUE META' SI FANNO CON LO STESSO STRUMENTO, E NELLA SCENA VERA
#
# Cambia **soltanto da dove `01-b3-cliente.py` prende la parola**:
#
#   A  `bash enter.sh --root "python3 … --parola <esca>"`       il testo in argv
#   B  `bash enter.sh --root "python3 … --parola-file <file>"`  il testo nel file
#
# ⛔ E si passa da `enter.sh` davvero, non da un `bash -c` che gli somiglia: e'
#    li' che il difetto viveva.  La catena e' `bash` → `sudo` → `chroot` →
#    `bash -lc` → `python3`, e la stringa la portano **tutti e cinque**: un
#    conto piu' alto di uno non e' un vezzo, e' il denominatore vero.
#
# ⛔⭐ E IL CONTENITORE E' UN `chroot`, NON UN NAMESPACE DI PID — ed e' la
#     ragione per cui D12 e' grave e non teorico: i processi di dentro si
#     vedono **tutti** in `ps` sull'host, da qualunque utente.  Un banco che
#     gira «dentro» non e' nascosto a nessuno.
#     ⇒ Questo attrezzo gira SULL'HOST e guarda dentro.
#
# ⚠ E si mira a una porta dove non c'e' nessuno: si misura il `cmdline`, non la
#   stretta di mano.  E' voluto, ed e' la stessa scelta del passo 2-bis di
#   `01-p5-lancia.sh`.
# ⛔ Niente redirezioni ATTORNO a `enter.sh`: si redirige DENTRO le virgolette e
#    si legge il file dopo.  Fuori si porta via la richiesta di parola d'ordine
#    di `sudo`, e lo script resta appeso per sempre, in silenzio.
#
# ---------------------------------------------------------------------------
# ⛔ E IL GUARDIANO NON DEVE CREARE IL DIFETTO CHE CERCA
#
# `ps` si legge **in una variabile** e il confronto lo fa **bash**.  Un
# `grep "$parola"` metterebbe la parola nell'`argv` del `grep`, e il guardiano
# sarebbe la falla.  (La stessa riga di `guardia_ps` in `01-p5-lancia.sh`.)
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
CLIENTE=$DENTRO/01-b3-cliente.py
# ⛔ Una porta dove non c'e' nessuno, e NON una delle accese apposta: la 7448 e
#    la 7501 non si toccano.  Qui non si apre niente — ci si prova a collegare.
PORTA=${PORTA:-7523}
PAROLA=${PAROLA:-parola-di-prova-D12}

T=$FUORI/tmp/d12-ps
T_DENTRO=$DENTRO/tmp/d12-ps
PAROLA_FILE=$T/parola
PAROLA_FILE_DENTRO=$T_DENTRO/parola
ESCA="d12-esca-ps-$$-$RANDOM"
ESITO=0

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

congedo() { rm -rf "$T"; }
trap congedo EXIT

mkdir -p "$T" || { printf '⛔ non si crea %s\n' "$T"; exit 2; }
[ -r "$FUORI/01-b3-cliente.py" ] || { ko "⛔ non si legge $FUORI/01-b3-cliente.py"; exit 2; }

# ⛔ Il guardiano.  $1 = ago che NON deve comparire · $2 = ago che DEVE comparire
guardia_ps()
{
	local i righe uno=0 due=0
	for i in $(seq 1 30); do
		righe=$(ps -ww -eo args)
		[ -n "$1" ] && case "$righe" in *"$1"*) uno=$((uno + 1)) ;; esac
		[ -n "$2" ] && case "$righe" in *"$2"*) due=$((due + 1)) ;; esac
		sleep 0.08
	done
	printf '%s %s\n' "$uno" "$due" > "$T/guardia"
}

log "0. La scena, dichiarata prima di misurare"
inf "cliente : $CLIENTE (dentro il contenitore)"
inf "porta   : $PORTA  ⛔ nessuno ascolta li': si misura il cmdline, non la rete"
inf "macchina: $(hostname) — e si guarda in «ps» DELL'HOST"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

# ---------------------------------------------------------------------------
log "A. IL CONTROLLO POSITIVO — il testo NELL'ARGV: «ps» lo sa vedere?"
guardia_ps "$ESCA" "" &
PID_G=$!
bash "$ENTRA" --root "python3 -u $CLIENTE --indirizzo 127.0.0.1 --porta $PORTA \
	--utente prova --parola $ESCA > $T_DENTRO/a.log 2>&1"
wait "$PID_G" 2>/dev/null
A_VISTA=$(cut -d' ' -f1 "$T/guardia")
inf "«$ESCA» visto $A_VISTA volte in ps"
if [ "${A_VISTA:-0}" -lt 1 ]; then
	ko "⛔ IL CONTROLLO POSITIVO NON PASSA: «ps» non ha visto in «argv» un testo"
	ko "   che ci stava di sicuro.  ⇒ Lo zero della meta' B non varrebbe niente,"
	ko "   e questo attrezzo NON dichiara chiusa la cura di D12."
	ESITO=1
else
	ok "⭐ «ps» vede l'argv di questa stessa catena: sa trovare quel che c'e'"
fi

# ---------------------------------------------------------------------------
log "B. LA CURA — la parola da un file 0600, e il percorso come denominatore"
# ⛔ `umask` in una SOTTOSHELL, e `printf` e' un builtin: nemmeno la scrittura
#    passa per un processo con la parola in `argv`.
( umask 077; : > "$PAROLA_FILE" ) || { ko "non si scrive $PAROLA_FILE"; exit 2; }
chmod 600 "$PAROLA_FILE" || exit 2
printf '%s\n' "$PAROLA" > "$PAROLA_FILE"

guardia_ps "$PAROLA" "$PAROLA_FILE_DENTRO" &
PID_G=$!
bash "$ENTRA" --root "python3 -u $CLIENTE --indirizzo 127.0.0.1 --porta $PORTA \
	--utente prova --parola-file $PAROLA_FILE_DENTRO > $T_DENTRO/b.log 2>&1"
wait "$PID_G" 2>/dev/null
B_PAROLA=$(cut -d' ' -f1 "$T/guardia")
B_FILE=$(cut -d' ' -f2 "$T/guardia")
inf "la PAROLA vista $B_PAROLA volte · il PERCORSO del file visto $B_FILE volte"

if [ "${B_FILE:-0}" -lt 1 ]; then
	ko "⚠ non ho visto in «ps» nemmeno il comando che stava girando: allora lo"
	ko "  zero della parola e' «non ho guardato al momento giusto», non «non"
	ko "  c'era».  ⛔ Non e' un verde, e si dichiara."
	ESITO=1
elif [ "${B_PAROLA:-1}" -gt 0 ]; then
	ko "⛔⛔ LA PAROLA D'ORDINE E' ANCORA IN «ps»: la cura di D12 NON ha chiuso."
	ESITO=1
else
	ok "⭐⭐ D12 CHIUSO PER MISURA: nello stesso istante «ps» vedeva il comando"
	ok "   («--parola-file $PAROLA_FILE_DENTRO», $B_FILE volte) e NON vedeva la parola."
fi

# ---------------------------------------------------------------------------
log "C. ⛔ E il banco ha DAVVERO letto la parola dal file, non un predefinito"
# ⛔ Senza questo passo, «la parola non e' in ps» sarebbe compatibile con «il
#    banco non ha nemmeno provato a leggerla»: due cose diversissime con lo
#    stesso aspetto.  ⭐ Il criterio e' l'uscita del cliente su un file VUOTO —
#    dev'essere 2 con la frase che dice perche'.
: > "$T/vuoto"
bash "$ENTRA" --root "python3 -u $CLIENTE --indirizzo 127.0.0.1 --porta $PORTA \
	--utente prova --parola-file $T_DENTRO/vuoto > $T_DENTRO/c.log 2>&1"
C=$?
if [ "$C" -eq 2 ] && grep -q "e' VUOTO" "$T/c.log"; then
	ok "⭐ file vuoto ⇒ uscita 2 e «il lanciatore non l'ha scritta»: la lettura"
	ok "   del file c'e' davvero, e distingue «vuota» da «non scritta»"
else
	ko "⛔ file vuoto: uscita $C — il banco NON si accorge del file vuoto"
	sed -n '1,4p' "$T/c.log" | sed 's/^/        /'
	ESITO=1
fi

# ---------------------------------------------------------------------------
log "D. ⚠ E il chiamante NON curato deve funzionare, DICENDOLO (compatibilita')"
if grep -q "D12: la parola d'ordine e' arrivata da .--parola." "$T/a.log"; then
	ok "⭐ la meta' A ha stampato l'avviso: chi passa --parola se lo sente dire"
	ok "   ⇒ il ripiego e' dichiarato, non silenzioso (CODER.md §4.2, forma E2)"
else
	ko "⛔ la meta' A NON ha stampato nessun avviso: un ripiego silenzioso"
	ko "   produce due comportamenti sotto la stessa etichetta"
	ESITO=1
fi

log "Esito"
inf "A (argv)      : esca vista $A_VISTA volte   ⇒ il denominatore"
inf "B (file 0600) : parola $B_PAROLA volte · percorso $B_FILE volte"
[ "$ESITO" -eq 0 ] && ok "⭐ D12: chiuso per misura su questa macchina" \
                   || ko "⛔ D12: qualcosa non torna, e sta scritto sopra"
exit "$ESITO"
