#!/usr/bin/env bash
# ===========================================================================
# 10-b2-lancia — la campagna del banco DEL BROWSER VERO (incarico 10-b2)
#
#   porta 8120 · utenti provadec1 / provadec1b · albero /media/REMOTIX/src/10b2-src
#   lavoro /media/REMOTIX/tmp/10b2 · unita' remotix-8120 · lucchetto GPU 10-b2
#
# ⛔ IL LUCCHETTO DELLA GPU DEV'ESSERE GIA' IN MANO: questo copione **non lo
#    prende**.  Lo prende chi lo lancia, e lo molla lui, perche' la campagna
#    dura piu' di un giro e il lucchetto si molla appena finito.
#
# ⛔ E NON PARTE SE `--certifica` NON PASSA: un banco che non si e' visto dare
#    rosso non e' un banco (`LEZIONI.md` §1.29).
#
# Prima, una volta sola:
#     bash banchi/10-b2-terreno.sh utenti
#     bash banchi/10-b2-terreno.sh porta
#
# L'ordine dei giri, e la ragione di ciascuno:
#   1  la certificazione                        ⛔ i guasti innestati
#   2  il controllo del terreno (`10-b0`)       ⛔ prima di misurare
#   3  la taratura dello strumento «capsula»    ⛔ il metro si tara PRIMA
#   4  la sessione ferma, 120 s                 `[?]` 1
#   5  la sessione ferma, 300 s                 ⚠ i giri corti sottostimano (§1.32)
#   6  il braccio di controllo, silenzio SPENTO ⛔ senza, non si attribuisce niente
#   6-bis il difetto della FINESTRA, A/B su due altezze — trovato per caso
#   7  la capsula, 10 giri, a tabella piena     `[?]` 2 — ⭐ ed e' IL VERDE della frase
#   7-bis ⛔ il ROSSO: la frase `0x0E` di IERI rimessa nella pagina servita
#   7-ter ⛔⛔ il file dice una cosa e il browser un'altra (`0x0F` sul filo)
#   8  si lascia la macchina come la si e' trovata, e lo si VERIFICA
# ===========================================================================
set -uo pipefail
QUI=$(cd "$(dirname "$0")/.." && pwd)

export MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
export PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-8120}
export UTENTE=${UTENTE:-provadec1}
export UID_B=${UID_B:-1100}
export PAROLA_UTENTE=${PAROLA_UTENTE:-b2-browser-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10b2-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10b2}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10b2-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10b2}
export UNITA=${UNITA:-remotix-$PORTA}
export FUORI=${FUORI:-/tmp/10-b2}
export LUCCHETTO=${LUCCHETTO:-/media/REMOTIX/tmp/.lucchetto-gpu.d}
# ⚠ Le porte degli ALTRI incarichi di questo giro: si DICHIARANO, non si tacciono.
export PORTE_AMMESSE=${PORTE_AMMESSE:-"8130 8140 8150 8160 8170 8180 8190 8200 8210"}

mkdir -p "$FUORI"
B="python3 -u $QUI/banchi/10-b2-browser.py"
T="bash $QUI/banchi/10-b2-terreno.sh"

titolo() { printf '\n\033[1m═══ %s\033[0m\n' "$*"; }

titolo "1 · ⛔ LA CERTIFICAZIONE — i guasti innestati devono dare rosso"
if ! $B --certifica; then
	printf '    \033[1;31mNO\033[0m  ⛔ la certificazione non passa: NON MISURO\n'
	exit 2
fi

titolo "2 · ⛔ IL CONTROLLO DEL TERRENO — e prima si sgombrano i MIEI palchi"
# ⛔ Lo sgombero PRIMA del controllo, non dopo: `10-b0` guarda se il posto di
#    `provadec1` e' libero, e un palco lasciato dal giro precedente lo farebbe
#    dare rosso — su una macchina sana.
$T sgombra
CHI=10-b2 PORTA=$PORTA UTENTE=$UTENTE ALBERO=$ALBERO LAV=$LAV \
	LUCCHETTO_MIO=1 PALCO_AMMESSO=${PALCO_AMMESSO:-0} \
	bash "$QUI/banchi/10-b0-terreno.sh" || {
	printf '    \033[1;31mNO\033[0m  ⛔ il terreno non regge: NON MISURO\n'; exit 1; }

titolo "3 · ⛔ LA TARATURA DELLO STRUMENTO «CAPSULA» (uccide il server, poi lo riaccendo)"
$T spegni >/dev/null 2>&1
$T accendi || exit 2
$B --scena taratura || { printf '⛔ metro non tarato: NON MISURO\n'; exit 3; }
$T accendi || exit 2

titolo '4 · [?] 1 — LA SESSIONE FERMA DI UN BROWSER VERO, 120 s'
$T sgombra
$B --scena viva --durata 120

titolo "5 · ⚠ E A UNA SECONDA DURATA (LEZIONI.md §1.32), 300 s"
$T sgombra
$B --scena viva --durata 300

titolo "6 · ⭐ IL BRACCIO DI CONTROLLO — silenzio dell'audio SPENTO a mano"
$T sgombra
$T spegni
OPZIONI_SERVER='--niente-audio-silenzio' $T accendi || exit 2
$B --scena viva --durata 120 --senza-audio-silenzio

titolo "6-bis · ⛔ IL DIFETTO CHE NESSUNO CERCAVA — la misura della finestra"
$T sgombra
$T spegni
$T accendi || exit 2
$B --scena finestra --giri "${GIRI_FINESTRA:-5}"

titolo '7 · [?] 2 — LA CAPSULA DI CHIUSURA, a tabella piena (tetto = 1)'
$T sgombra
$T spegni
# ⭐ Il tetto NON ricompila piu' niente: e' «--tetto-sessioni 1» all'accensione
#    (cura del 25 agosto 2026), e il terreno verifica che sia in vigore
#    leggendolo dal server acceso.
MAX_ATT=1 $T accendi || exit 2
$B --scena capsula --giri "${GIRI:-10}"

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐⭐ 7-bis e 7-ter — I DUE CONTROLLI NEGATIVI DELLA FRASE (incarico 10-d3)
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Il giro 7 qui sopra e' IL VERDE.  Un verde senza il rosso di prima non
#    prova niente: prova solo che il banco sa dire di si'.  ⇒ Due giri ancora,
#    e tutt'e due DEVONO finire ROSSI.
#
# 7-bis  si rimette nella pagina servita la frase `0x0E` di IERI — quella che
#        `[M]` §6.4 ha letto dentro Firefox vero 10 su 10 — e il banco deve
#        tornare rosso su «dice di chi» e «da' un gesto».
# 7-ter  ⛔⛔ IL CASO CHE SMASCHERA I BANCHI SCRITTI MALE: pagina NUOVA e
#        giusta, ma il respinto e' lo STESSO utente dell'occupante ⇒ sul filo
#        arriva `0x0F`, non `0x0E`.  Un banco che dichiara la frase leggendo il
#        FILE direbbe verde; questo legge il browser e dice rosso.

titolo '7-bis · ⛔ IL ROSSO DI PRIMA — la frase 0x0E di IERI, rimessa nella pagina servita'
$T sgombra
$T spegni
# ⚠ `FRASE_VECCHIA` resta a `porta`: quella tocca la PAGINA servita, che non e'
#   compilata — il tetto invece entra ad `accendi`, a caldo.
FRASE_VECCHIA="quella sessione non si puo' servire" $T porta || exit 2
MAX_ATT=1 $T accendi || exit 2
$B --scena capsula --giri "${GIRI_ROSSO:-5}" \
	&& printf '    \033[1;31mNO\033[0m  ⛔ il banco NON e" tornato rosso sulla frase di ieri: non sta misurando la cura\n' \
	|| printf '    \033[1;32mOK\033[0m  ⭐ rosso, come deve: il banco sa ancora dire di no\n'

titolo '7-ter · ⛔⛔ IL FILE DICE UNA COSA E IL BROWSER UN"ALTRA (0x0F sul filo, 0x0E nel file)'
$T sgombra
$T spegni
$T porta || exit 2
MAX_ATT=1 $T accendi || exit 2
$B --scena capsula --giri "${GIRI_PUNTO4:-3}" --respinto-uguale --motivo-atteso 0x0E \
	&& printf '    \033[1;31mNO\033[0m  ⛔ il banco NON si e" accorto che i due testi divergono\n' \
	|| printf '    \033[1;32mOK\033[0m  ⭐ rosso: i due testi divergono e il banco lo dice\n'

titolo "8 · ⛔ LA MACCHINA SI LASCIA COME LA SI E' TROVATA"
$T sgombra
$T spegni
# ⭐⭐ E L'ALBERO NON VA PIU' RIMESSO A POSTO, perche' non e' mai stato toccato:
#     dal 25 agosto 2026 il tetto e' «--tetto-sessioni», un'opzione all'avvio.
#     ⛔ Prima qui c'era una ricompilazione di rimessa in ordine, e con lei il
#        rischio di lasciare a chi trovava l'albero domani un binario col tetto
#        di ieri **senza nessun modo di accorgersene**.  ⇒ Quel rischio non
#        esiste piu': si spegne il server, e il tetto se ne va con lui.
printf '    --  albero INTATTO: nessun sed, nessuna ricompilazione (tetto a caldo)\n'
# ⛔⛔ E IL MODELLO SI SCRIVE COL MORSO — 25 agosto 2026, e questo controllo
#      diceva **1** su una macchina PULITA.  `pgrep -f` acchiappa la riga di
#      comando che lo esegue, e qui la riga di comando contiene il modello: il
#      controllo contava se stesso.  ⇒ `[r]emotix`, che come regola trova
#      «remotix» e come testo non e' «remotix» — e `|| true` perche' `pgrep -c`
#      esce 1 quando il conto e' zero, che e' proprio il caso buono.
ssh -o BatchMode=yes "$MACCHINA" "ss -uln | grep -c ':$PORTA ' ; pgrep -c -f '$ALBERO/src/[r]emotix' || true"
printf '\n⭐ finito (i due numeri qui sopra devono essere 0 e 0).\n'
printf '⛔ Adesso MOLLA IL LUCCHETTO: gli altri aspettano.\n'
