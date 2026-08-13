#!/bin/bash
#
# 03-b15-lancia.sh — ⛔ GIRA SU CHUWI.  Il banco dello STEP 3 della fase 3.
#
#   bash banchi/03-b15-lancia.sh certifica   ⭐ gira QUI, senza rete e senza server
#   bash banchi/03-b15-lancia.sh porte       conta 7448 · 7501 · 7561 · 7603
#   bash banchi/03-b15-lancia.sh porta       copia src/ e i banchi sulla macchina
#   bash banchi/03-b15-lancia.sh costruisci  `make` dentro il contenitore
#   bash banchi/03-b15-lancia.sh terreno     la parola di prova, 0600
#   bash banchi/03-b15-lancia.sh accendi     il server DA ROOT sulla 7603
#   bash banchi/03-b15-lancia.sh misura [caso]
#   bash banchi/03-b15-lancia.sh registro [quante]
#   bash banchi/03-b15-lancia.sh spegni
#   bash banchi/03-b15-lancia.sh tutto       porta · costruisci · riaccendi · misura
#
# ---------------------------------------------------------------------------
# ⛔ LE REGOLE DI CASA CHE QUESTO FILE RISPETTA, E CIASCUNA E' STATA PAGATA
#
#   · ⛔ **MAI una redirezione ATTORNO a `ssh` o a `enter.sh`** — pagata SEI
#     volte.  La richiesta di parola d'ordine di `sudo` va sullo stderr, e una
#     redirezione la mangia: il comando resta appeso per sempre, in silenzio.
#     ⇒ Si passa da `v1/strumenti/sshpw.py`, e non si redirige niente;
#   · ⛔ **un file non ha livelli di virgolette**: quel che deve girare dentro
#     il contenitore sta in uno script SUL SERVER, non dentro
#     `ssh → enter.sh → bash -c`.  In particolare `&` dentro tre livelli di
#     virgolette non arriva dove sembra;
#   · la porta e' la **7603**, di questo step e di nessun altro.  ⛔ La 7448, la
#     7501 e la **7561 — dove l'utente sta guardando il proprio desktop** — si
#     CONTANO prima e dopo, e non si toccano.  ⚠ E gli altri step della fase 3
#     hanno 7601, 7602, 7604, 7605: si contano anche quelle, come contorno;
#   · l'albero dei sorgenti e' **03-b15-src**, una COPIA: il guasto si innesta
#     nella copia, mai nel prodotto di casa;
#   · la parola d'ordine non passa mai da `argv` (difetto D12);
#   · ⛔ **niente `set -e`**: si contano i rossi e si va avanti, cosi' alla fine
#     c'e' un denominatore.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
RADICE=$(cd -- "$QUI/.." && pwd)
SSHPW="$RADICE/v1/strumenti/sshpw.py"
FUORI=/media/REMOTIX/src
ALBERO=$FUORI/03-b15-src
DENTRO=/srv/src
PORTA=7603
LAV=/media/REMOTIX/tmp/03-b15
LAV_DENTRO=/srv/remotix/tmp/03-b15
UTENTE=${UTENTE:-nicfio}

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

fuori()  { timeout 900 python3 "$SSHPW" "$1"; }
dentro() { timeout 900 python3 "$SSHPW" "bash /media/REMOTIX/enter.sh --root \"$1\""; }
metti()  { timeout 300 python3 "$SSHPW" --put "$1" "$2"; }

AZIONE=${1:-}

case "$AZIONE" in
certifica)
	# ⛔ Gira QUI, su CHUWI, senza rete e senza server: e' la ragione per cui i
	#    sei controlli sono funzioni pure sul verbale.  Chi revisiona il banco
	#    lo puo' leggere e provare senza toccare la macchina.
	python3 "$QUI/03-b15-movimento.py" --certifica
	exit $? ;;

elenco)
	python3 "$QUI/03-b15-movimento.py" --elenco
	exit 0 ;;

porte)
	log "Le porte, contate — 7448 · 7501 · 7561 NON si toccano"
	fuori "ss -tuln | grep -E ':(7448|7501|7561|760[1-5])\b' | sort"
	exit 0 ;;

porta)
	log "1. I sorgenti del prodotto, in un albero MIO (una COPIA)"
	# ⛔ La cartella si CANCELLA prima di ricopiarla: un file di ieri rimasto
	#    li' dentro risponde «esisto» come uno di adesso.  ⚠ E su CHUWI `rsync`
	#    non c'e' — misurato, non supposto.
	fuori "rm -rf $ALBERO/src $ALBERO/banchi && mkdir -p $ALBERO/src $ALBERO/banchi/rcp && mkdir -p $LAV" \
		|| { ko "non ho potuto rifare $ALBERO"; exit 2; }
	tar czf /tmp/03-b15-src.tgz -C "$RADICE" src banchi/rcp || { ko "tar fallito"; exit 2; }
	metti /tmp/03-b15-src.tgz "$ALBERO/src.tgz" || { ko "scp fallito"; exit 2; }
	fuori "cd $ALBERO && tar xzf src.tgz && ls src/figlio.c banchi/rcp/rcp.c" \
		|| { ko "l'albero non si e' srotolato"; exit 2; }
	log "2. E i banchi, accanto agli altri"
	# ⛔ `03-b15-movimento.py` carica i fratelli con `os.path.join(QUI, ...)`:
	#    devono stare nella STESSA cartella, o l'import per nome-file fallisce.
	# ⛔ `03-scena.c` e' dello STEP 2 e non si tocca: si porta e si compila in
	#    una cartella mia.  Si dipende, non si riscrive (`CODER.md` §4.1).
	for f in 03-b15-movimento.py 03-b15-accendi.sh 01-b3-cliente.py \
	         02-filo-fotogramma.py 03-scena.c; do
		metti "$QUI/$f" "$FUORI/$f" || { ko "scp di $f fallito"; exit 2; }
	done
	ok "quattro file → $FUORI/"
	exit 0 ;;

costruisci)
	log "make, dentro il contenitore, nell'albero 03-b15-src"
	# ⛔ `costruisci.sh` butta il binario vecchio PRIMA di costruire, confronta
	#    `rcp.c` con la copia gemella e verifica le marche dentro il binario:
	#    «c'e'» diventa «e' di adesso».
	dentro "cd $DENTRO/03-b15-src/src && bash costruisci.sh"
	exit $? ;;

terreno)
	log "La parola d'ordine, in un file 0600 (difetto D12)"
	# ⛔ Si scrive con un builtin della shell: nemmeno la scrittura passa da un
	#    processo, quindi non compare in `ps`.
	PW=$(sed -n 's/^pass[[:space:]]*:[[:space:]]*//p' "$HOME/SERVER.ssh" 2>/dev/null)
	[ -n "$PW" ] || { ko "⛔ non ho letto la parola da ~/SERVER.ssh"; exit 2; }
	umask 077
	printf '%s' "$PW" > /tmp/03-b15-parola
	fuori "mkdir -p $FUORI/tmp" || exit 2
	metti /tmp/03-b15-parola "$FUORI/tmp/03-b15-parola" || exit 2
	rm -f /tmp/03-b15-parola
	fuori "chmod 600 $FUORI/tmp/03-b15-parola && ls -l $FUORI/tmp/03-b15-parola"
	ok "la parola e' sulla macchina, 0600, e mai in un argv"
	exit 0 ;;

scena-costruisci)
	log "La scena dello step 2, costruita DENTRO il contenitore"
	# ⛔ Di la' ci sono `gcc`, `pkg-config` e `wayland-scanner`; sull'host no —
	#    `[M]` 13 agosto 2026.  Qui si costruisce, di la' si esegue: e' lo stesso
	#    taglio del prodotto.  ⚠ Le due variabili portano i nomi DENTRO il
	#    contenitore; il ramo e' in un FILE, non in una riga annidata.
	dentro "SCENA_LAV=$DENTRO/03-b15-scena SCENA_C=$DENTRO/03-scena.c bash $DENTRO/03-b15-accendi.sh scena-costruisci"
	exit $? ;;

scena-avvia|scena-ferma|scena-conta|scena-uscite)
	log "La scena — LEZIONI.md §1.1, e senza non c'e' misura"
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/03-b15-accendi.sh $AZIONE ${2:-}"
	exit $? ;;

accendi)
	log "Il server DA ROOT sulla $PORTA"
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/03-b15-accendi.sh accendi"
	exit $? ;;

riaccendi)
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/03-b15-accendi.sh riaccendi"
	exit $? ;;

spegni)
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/03-b15-accendi.sh spegni"
	exit $? ;;

stato)
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/03-b15-accendi.sh stato"
	exit $? ;;

registro)
	QUANTE=${2:-60}
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/03-b15-accendi.sh registro $QUANTE"
	exit $? ;;

misura)
	CASO=${2:-tutti}
	# ⛔⭐ LA SCENA SI RIACCENDE PRIMA DI OGNI MISURA, E NON E' PRUDENZA.
	#
	#     `[M]` 13 agosto 2026: la scena resta VIVA ma smette di DISEGNARE
	#     quando la sessione precedente si chiude — Mutter non manda piu' i
	#     *frame callback* a una superficie che sta su un monitor che nessuno
	#     sta piu' registrando, e il client resta fermo dentro
	#     `wl_display_dispatch`.  ⇒ La misura dopo contava **zero fotogrammi**
	#     con il prodotto perfettamente funzionante: un rosso puntato
	#     sull'imputato sbagliato, per la seconda volta in un pomeriggio.
	#
	# ⚠ E «viva» non e' «disegna»: e' la stessa distinzione che `scena-avvia`
	#   fa col suo marcatore, ed e' la ragione per cui non basta guardare il pid.
	bash "$0" scena-ferma >/dev/null 2>&1
	log "La misura — caso «$CASO»"
	# ⛔ Dentro il contenitore, perche' aioquic sta li'.  ⚠ `--indirizzo
	#   127.0.0.1`: il server ascolta su 0.0.0.0 e il contenitore condivide la
	#   rete dell'host, quindi il loopback e' lo stesso.
	bash "$0" scena-avvia | tail -3
	dentro "python3 $DENTRO/03-b15-movimento.py --indirizzo 127.0.0.1 --porta $PORTA --utente $UTENTE --parola-file $DENTRO/tmp/03-b15-parola --caso $CASO --registro $LAV_DENTRO/registro.log --uscita $DENTRO/03-b15-esiti.jsonl ${3:-}"
	exit $? ;;

esiti)
	fuori "tail -3 $FUORI/03-b15-esiti.jsonl"
	exit $? ;;

tutto)
	falle=0
	for passo in porta costruisci terreno riaccendi scena-costruisci; do
		bash "$0" "$passo" || { ko "il passo «$passo» e' fallito"; exit 3; }
	done
	# ⛔ La scena si accende DOPO il server e DOPO che un utente e' entrato: il
	#    monitor del palco nasce col figlio, e prima non esiste nessun nome da
	#    chiedere.  ⇒ Un primo giro breve fa nascere il figlio, poi la scena.
	bash "$0" misura movimento --attesa 3 >/dev/null 2>&1
	bash "$0" scena-avvia || { ko "la scena non si accende: NON misuro"; exit 3; }
	bash "$0" misura tutti || falle=$((falle+1))
	printf '\n'
	[ "$falle" -eq 0 ] && ok "⭐ il giro intero e' passato" || ko "⛔ $falle rossi"
	exit "$falle" ;;

*)
	sed -n '2,20p' "$0"
	exit 2 ;;
esac
