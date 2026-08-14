#!/bin/bash
#
# 04-b20-lancia.sh — ⛔ GIRA SU CHUWI, dove sta il deposito.  Il banco dell'anello
# A1 della fase 4: **il desktop vero**.
#
#   bash banchi/04-b20-lancia.sh certifica   lo STRUMENTO, senza il prodotto
#   bash banchi/04-b20-lancia.sh porte       conta 7448 · 7501 · 7561 · 7571
#   bash banchi/04-b20-lancia.sh porta       manda src/ e i banchi su NIC-OS
#   bash banchi/04-b20-lancia.sh costruisci  `make` nel contenitore
#   bash banchi/04-b20-lancia.sh utente      l'utente del banco
#   bash banchi/04-b20-lancia.sh sessione <con|senza>
#   bash banchi/04-b20-lancia.sh nasci       ⭐ la sessione la fa nascere IL PRODOTTO
#   bash banchi/04-b20-lancia.sh accendi     il server sulla 7601
#   bash banchi/04-b20-lancia.sh misura <etichetta> [tela]
#   bash banchi/04-b20-lancia.sh registro
#   bash banchi/04-b20-lancia.sh spegni
#   bash banchi/04-b20-lancia.sh pulisci
#
# ---------------------------------------------------------------------------
# ⛔ LE REGOLE DI CASA CHE QUESTO FILE RISPETTA
#
#   · ⛔ **MAI una redirezione ATTORNO a `ssh` o a `enter.sh`**: la richiesta di
#     parola d'ordine di `sudo` va sullo stderr, e una redirezione la mangia —
#     il comando resta appeso per sempre, in silenzio.  ⇒ Si passa da
#     `v1/strumenti/sshpw.py`;
#   · ⛔ **un file non ha livelli di virgolette**: quel che deve girare dentro il
#     contenitore sta in uno script sul server, non dentro `ssh → enter.sh →
#     bash -c`;
#   · le porte sono le **7601-7605**, di questo anello e di nessun altro.  ⛔ La
#     7448, la 7501, la 7561 e la 7571 si CONTANO prima e dopo, e non si toccano;
#   · l'albero dei sorgenti e' **04-a1-src**, che nessun altro anello usa: cosi'
#     la cura di A1 non puo' arrivare ai banchi degli altri nove;
#   · ⛔ ban, socket del comando e certificati sono PROPRI: due server che
#     condividessero il file dei ban si metterebbero fuori uso a vicenda
#     (`RCP.md` §4.4-bis).
#
# ---------------------------------------------------------------------------
# ⛔⭐ IL GIRO CHE CERTIFICA — e l'ordine non e' un'opinione (`CODER.md` §3.3)
#
#   1. `certifica`            lo strumento sa dire SHELL e sa dire VUOTO?
#   2. `sessione con` + `misura rosso-prima`     ⛔ DEVE dire **VUOTO**
#   3. (la cura in `src/sessione.c`) + `costruisci`
#   4. `nasci` + `misura verde-dopo`             ⭐ DEVE dire **SHELL**
#
# ⚠ Un banco che nascesse verde non avrebbe mai visto il difetto, e la cura
#   scritta sopra di lui sarebbe scritta al buio.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
RADICE=$(cd -- "$QUI/.." && pwd)
SSHPW="$RADICE/v1/strumenti/sshpw.py"

FUORI=/media/REMOTIX/src
ALBERO=$FUORI/04-a1-src
LAV=/media/REMOTIX/tmp/04-b20
LAV_DENTRO=/srv/remotix/tmp/04-b20
ALBERO_DENTRO=/srv/src/04-a1-src
PORTA=${PORTA:-7601}
UTENTE=${UTENTE:-provaa1}
PAROLA=${PAROLA:-provaa1-2026}
ESITI=$LAV_DENTRO/04-b20-esiti.jsonl

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

fuori()  { timeout 1200 python3 "$SSHPW" "$1"; }
dentro() { timeout 1200 python3 "$SSHPW" "bash /media/REMOTIX/enter.sh --root \"$1\""; }
radice() { timeout 1200 python3 "$SSHPW" "sudo -S -p 'Password sudo: ' $1"; }
metti()  { timeout 600 python3 "$SSHPW" --put "$1" "$2"; }

case "${1:-}" in
certifica)
	log "Lo STRUMENTO, prima del prodotto — deve saper dire tutt'e due le cose"
	python3 "$QUI/04-b20-desktop-vero.py" --certifica --lavoro /tmp/04-b20
	exit $? ;;

porte)
	log "Le porte degli altri, contate — NON si toccano"
	fuori "ss -tuln | grep -E ':(7448|7501|7561|7571|7601)\b' | sort"
	exit 0 ;;

porta)
	log "1. I sorgenti, in un albero MIO"
	# ⛔ La cartella si CANCELLA prima di ricopiarla: un file di ieri rimasto
	#    li' dentro risponde «esisto» come uno di adesso.
	# ⛔ La cartella la cancella ROOT: `__pycache__` lo scrive il python del
	#    contenitore, che gira da root, e un `rm` d'utente si ferma li'.
	radice "rm -rf $ALBERO"
	fuori "mkdir -p $ALBERO/banchi/rcp && mkdir -p $LAV" \
		|| { ko "non ho potuto rifare $ALBERO"; exit 2; }
	# ⛔ E l'albero si prende da **HEAD**, non dalla cartella di lavoro: in
	#    questo momento altri nove anelli stanno scrivendo dentro `src/`, e un
	#    albero mezzo loro e mezzo mio non e' ne' il prodotto ne' la cura.
	#    ⚠ `src/sessione.c` invece si prende dalla cartella di lavoro, perche'
	#      e' il file di A1 ed e' li' che la cura vive.
	T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
	(cd "$RADICE" && git archive HEAD src banchi/rcp) | tar -x -C "$T" || exit 2
	cp "$RADICE/src/sessione.c" "$T/src/sessione.c" || exit 2
	mkdir -p "$T/banchi"
	cp "$QUI/04-b20-desktop-vero.py" "$QUI/04-b20-terreno.sh" \
	   "$QUI/04-b20-nasci.c" "$QUI/04-b20-costruisci.sh" \
	   "$QUI/04-b20-persistenza.sh" "$QUI/04-b20-stacco.sh" "$QUI/02-filo-cliente.py" \
	   "$QUI/02-filo-fotogramma.py" "$QUI/01-b3-cliente.py" "$T/banchi/" || exit 2
	tar czf /tmp/04-a1-src.tgz -C "$T" src banchi || exit 2
	metti /tmp/04-a1-src.tgz "$ALBERO/src.tgz" || { ko "scp fallito"; exit 2; }
	fuori "cd $ALBERO && tar xzf src.tgz && rm -f src.tgz && ls src | wc -l && ls banchi"
	ok "portati in $ALBERO"
	exit 0 ;;

costruisci)
	log "2. Compilo nel contenitore"
	# ⛔ Dentro uno SCRIPT, non dentro le virgolette: un `$(pkg-config …)`
	#    scritto qui lo espanderebbe la shell dell'host, dove non c'e'.
	dentro "bash $ALBERO_DENTRO/banchi/04-b20-costruisci.sh"
	exit $? ;;

utente)
	log "3. L'utente del banco"
	radice "bash $ALBERO/banchi/04-b20-terreno.sh utente"
	exit $? ;;

sessione)
	MODO=${2:?uso: sessione <con|senza>}
	log "4. La sessione GNOME di $UTENTE — $MODO --virtual-monitor"
	radice "bash $ALBERO/banchi/04-b20-terreno.sh sessione $MODO"
	exit $? ;;

nasci)
	# ⭐ QUI LA SESSIONE LA FA NASCERE IL PRODOTTO, non il banco: il drop-in lo
	#    scrive `scrivi_dropin()`, e il numero che esce e' `SessioneStato`.
	log "4-bis. ⭐ La sessione la fa nascere IL PRODOTTO (sessione_assicura)"
	radice "bash $ALBERO/banchi/04-b20-terreno.sh nasci"
	exit $? ;;

scena)
	log "4-ter. ⛔ La scena, che si DICHIARA e si MUOVE (CODER.md §3.2)"
	radice "bash $ALBERO/banchi/04-b20-terreno.sh scena"
	exit $? ;;

scena-via)
	radice "bash $ALBERO/banchi/04-b20-terreno.sh scena-via"
	exit $? ;;

accendi)
	log "5. Il server sulla $PORTA"
	radice "bash $ALBERO/banchi/04-b20-terreno.sh accendi"
	exit $? ;;

misura)
	ET=${2:?uso: misura <etichetta> [tela]}
	TELA=${3:-1920x1080}
	L=${TELA%x*}; A=${TELA#*x}
	log "6. Il client RICEVE, e il banco giudica — «$ET», tela chiesta $TELA"
	# ⛔ Il conteggio dei monitor PRIMA: e' un controllo, non la misura.
	radice "bash $ALBERO/banchi/04-b20-terreno.sh monitor"
	dentro "printf '%s' '$PAROLA' > $LAV_DENTRO/parola && chmod 600 $LAV_DENTRO/parola"
	dentro "cd $ALBERO_DENTRO/banchi && python3 02-filo-cliente.py --porta $PORTA --utente $UTENTE --parola-file $LAV_DENTRO/parola --larghezza $L --altezza $A --attesa 40 --registra $LAV_DENTRO/$ET.rcpreg 2>&1 | tail -25"
	radice "bash $ALBERO/banchi/04-b20-terreno.sh monitor"
	dentro "cd $ALBERO_DENTRO/banchi && python3 04-b20-desktop-vero.py --registrazione $LAV_DENTRO/$ET.rcpreg --lavoro $LAV_DENTRO --etichetta $ET --scena 'sessione GNOME appena aperta, nessuna finestra, nessun input: l oggetto e il PRIMO fotogramma chiave' --esiti $ESITI"
	exit $? ;;

rilievo)
	ET=${2:?uso: rilievo <etichetta>}
	# ⚠ Il fotogramma che il figlio scrive quando PRENDE il palco: e' il lato
	#   che MANDA, e si dichiara.  ⛔ Serve quando dall'altra parte non arriva
	#   niente: dice **che cosa** non arrivava, e non sostituisce §3.8.
	log "⚠ Il rilievo del lato che MANDA — «$ET»"
	dentro "cd $ALBERO_DENTRO/banchi && python3 04-b20-desktop-vero.py --grezzo $LAV_DENTRO/rilievo/cattura.bgrx --lavoro $LAV_DENTRO --etichetta $ET --scena 'primo fotogramma chiave, preso da prendi_il_palco' --esiti $ESITI"
	exit $? ;;

prendi)
	ET=${2:?uso: prendi <etichetta>}
	log "L'immagine giudicata, portata qui per essere GUARDATA (I8)"
	timeout 600 python3 "$SSHPW" --get "$LAV/$ET-fotogramma.png" "/tmp/$ET-fotogramma.png" \
		|| fuori "ls -la $LAV/$ET-fotogramma.png"
	exit $? ;;

persistenza)
	# ⛔ La seconda domanda di A1: che cosa succede allo schermo QUANDO IL CLIENT
	#    SI STACCA.  ⚠ Sta tutta in uno script sul server perche' alterna misure
	#    sull'host e un client dentro il contenitore, e dura una ventina di
	#    minuti: spezzarla da qui sarebbe una stretta di mano in mezzo a ogni
	#    misura.
	log "⛔ La persistenza del palco allo stacco — I4 / SPECIFICHE.md §5.2"
	radice "bash $ALBERO/banchi/04-b20-stacco.sh giro"
	exit $? ;;

persistenza-prepara)
	radice "bash $ALBERO/banchi/04-b20-persistenza.sh prepara"
	exit $? ;;

registro)
	fuori "tail -60 $LAV/registro.log"
	exit 0 ;;

spegni)
	radice "bash $ALBERO/banchi/04-b20-terreno.sh spegni"
	exit $? ;;

pulisci)
	radice "bash $ALBERO/banchi/04-b20-terreno.sh pulisci"
	exit $? ;;

*)
	sed -n '2,30p' "$0"
	exit 2 ;;
esac
