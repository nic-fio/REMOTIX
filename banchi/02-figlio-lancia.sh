#!/bin/bash
#
# 02-figlio-lancia.sh — ⛔ GIRA SU CHUWI.  Il banco «un figlio per utente» —
# `DECISIONI.md` §1.10-bis.
#
#   bash banchi/02-figlio-lancia.sh previsione   l'atteso, PRIMA del giro
#   bash banchi/02-figlio-lancia.sh porte        conta 7448 · 7501 · 7561
#   bash banchi/02-figlio-lancia.sh porta        copia src/ e i banchi su NIC-OS
#   bash banchi/02-figlio-lancia.sh costruisci   `make` nel contenitore
#   bash banchi/02-figlio-lancia.sh terreno      la parola di prova, 0600
#   bash banchi/02-figlio-lancia.sh bus          root NON ci arriva, l'utente si'
#   bash banchi/02-figlio-lancia.sh accendi      il server DA ROOT sulla 7571
#   bash banchi/02-figlio-lancia.sh misura [caso]
#   bash banchi/02-figlio-lancia.sh guasto <uid|cieco>   innesta + ricostruisce
#   bash banchi/02-figlio-lancia.sh registro
#   bash banchi/02-figlio-lancia.sh spegni
#
# ---------------------------------------------------------------------------
# ⛔ LE REGOLE DI CASA CHE QUESTO FILE RISPETTA, E CIASCUNA E' STATA PAGATA
#
#   · ⛔ **MAI una redirezione ATTORNO a `ssh` o a `enter.sh`** — pagata SEI
#     volte.  La richiesta di parola d'ordine di `sudo` va sullo stderr, e una
#     redirezione la mangia: il comando resta appeso per sempre, in silenzio.
#     ⇒ Qui si passa da `fondamenta/strumenti/sshpw.py`, che la parola la scrive sul
#     pty **solo quando qualcuno la chiede**, e non si redirige niente;
#   · ⛔ **un file non ha livelli di virgolette**: quel che deve girare dentro
#     il contenitore sta in uno script sul server, non dentro `ssh → enter.sh →
#     bash -c`.  Un `$(...)` che muore in mezzo ha gia' fatto girare un caso
#     «l'aiutante e' morto» su un aiutante vivo (`PAM-filo-unico.md` §6);
#   · la porta e' la **7571**, di questo banco e di nessun altro.  ⛔ La 7448,
#     la 7501 e la **7561 — dove l'utente sta guardando il proprio desktop** —
#     si CONTANO prima e dopo, e non si toccano;
#   · l'albero dei sorgenti e' **02-figlio-src**, non quello da cui girano gli
#     altri tre server: un guasto innestato qui non puo' arrivare a loro;
#   · la parola d'ordine non passa mai da `argv` (difetto **D12**).
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
RADICE=$(cd -- "$QUI/.." && pwd)
SSHPW="$RADICE/fondamenta/strumenti/sshpw.py"
FUORI=/media/REMOTIX/src
ALBERO=$FUORI/02-figlio-src
DENTRO=/srv/src
PORTA=7571
LAV=/media/REMOTIX/tmp/02-figlio
LAV_DENTRO=/srv/remotix/tmp/02-figlio
UTENTE=${UTENTE:-nicfio}
UTENTE2=${UTENTE2:-prova}

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

fuori()  { timeout 900 python3 "$SSHPW" "$1"; }
dentro() { timeout 900 python3 "$SSHPW" "bash /media/REMOTIX/enter.sh --root \"$1\""; }
metti()  { timeout 300 python3 "$SSHPW" --put "$1" "$2"; }

AZIONE=${1:-}

case "$AZIONE" in
previsione)
	python3 "$QUI/02-figlio-prova.py" --previsione
	exit 0 ;;

porte)
	log "Le porte degli altri, contate — NON si toccano"
	fuori "ss -tuln | grep -E ':(7448|7501|7561|7571)\b' | sort"
	exit 0 ;;

porta)
	log "1. I sorgenti del prodotto, in un albero MIO"
	# ⛔ La cartella si CANCELLA prima di ricopiarla: un file di ieri rimasto
	#    li' dentro risponde «esisto» come uno di adesso.  ⚠ E su CHUWI `rsync`
	#    non c'e' — misurato, non supposto.
	fuori "rm -rf $ALBERO/src $ALBERO/banchi && mkdir -p $ALBERO/src $ALBERO/banchi/rcp" \
		|| { ko "non ho potuto rifare $ALBERO"; exit 2; }
	tar czf /tmp/02-figlio-src.tgz -C "$RADICE" src banchi/rcp \
		|| { ko "tar fallito"; exit 2; }
	metti /tmp/02-figlio-src.tgz "$ALBERO/src.tgz" || { ko "scp fallito"; exit 2; }
	fuori "cd $ALBERO && tar xzf src.tgz && ls src/figlio.c banchi/rcp/rcp.c" \
		|| { ko "l'albero non si e' srotolato"; exit 2; }
	log "2. E i banchi, accanto agli altri"
	for f in 02-figlio-prova.py 02-figlio-accendi.sh 02-filo-cliente.py \
	         01-b3-cliente.py 02-filo-fotogramma.py; do
		metti "$QUI/$f" "$FUORI/$f" || { ko "scp di $f fallito"; exit 2; }
	done
	ok "cinque banchi → $FUORI/"
	exit 0 ;;

costruisci)
	log "make, dentro il contenitore, nell'albero 02-figlio-src"
	# ⛔ `costruisci.sh` butta il binario vecchio PRIMA di costruire, confronta
	#    `rcp.c` con la copia gemella e verifica le marche dentro il binario.
	dentro "cd $DENTRO/02-figlio-src/src && bash costruisci.sh"
	exit $? ;;

terreno)
	log "La parola d'ordine di prova, in un file 0600 (difetto D12)"
	# ⛔ Si scrive con un builtin della shell: nemmeno la scrittura passa da un
	#    processo, quindi non compare in `ps`.  ⚠ E' la parola PUBBLICA dei
	#    banchi per «prova»; per «nicfio» e' quella di ~/SERVER.ssh, che questo
	#    file NON stampa mai.
	PW=$(sed -n 's/^pass[[:space:]]*:[[:space:]]*//p' "$HOME/SERVER.ssh" 2>/dev/null)
	[ -n "$PW" ] || { ko "⛔ non ho letto la parola da ~/SERVER.ssh"; exit 2; }
	umask 077
	printf '%s' "$PW" > /tmp/02-figlio-parola
	metti /tmp/02-figlio-parola "$FUORI/tmp/02-figlio-parola" || exit 2
	rm -f /tmp/02-figlio-parola
	printf '%s' "parola-di-prova" > /tmp/02-figlio-parola2
	metti /tmp/02-figlio-parola2 "$FUORI/tmp/02-figlio-parola2" || exit 2
	rm -f /tmp/02-figlio-parola2
	fuori "chmod 600 $FUORI/tmp/02-figlio-parola $FUORI/tmp/02-figlio-parola2 && ls -l $FUORI/tmp/02-figlio-parola*"
	ok "le due parole sono su NIC-OS, 0600, e mai in un argv"
	exit 0 ;;

bus)
	log "⛔ Il controllo che regge tutto il mandato, rimisurato adesso"
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/02-figlio-accendi.sh bus"
	exit $? ;;

accendi)
	log "Il server DA ROOT sulla $PORTA"
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/02-figlio-accendi.sh accendi"
	exit $? ;;

riaccendi)
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/02-figlio-accendi.sh riaccendi"
	exit $? ;;

spegni)
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/02-figlio-accendi.sh spegni"
	exit $? ;;

stato)
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/02-figlio-accendi.sh stato"
	exit $? ;;

guasto)
	CASO=${2:-uid}
	log "⛔ Innesto il guasto «$CASO» NELLA COPIA, e ricostruisco"
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/02-figlio-accendi.sh guasto $CASO" || exit 2
	dentro "cd $DENTRO/02-figlio-src/src && bash costruisci.sh"
	exit $? ;;

misura)
	CASO=${2:-tutti}
	log "La misura — caso «$CASO»"
	# ⛔ Il pid del server si legge dal FILE DEL PID di questo banco, non da
	#    `pgrep remotix`: quello troverebbe anche i server degli altri tre.
	dentro "python3 $DENTRO/02-figlio-prova.py --caso $CASO --porta $PORTA --pid-file $LAV_DENTRO/pid --registro $LAV_DENTRO/registro.log --utente $UTENTE --parola-file $DENTRO/tmp/02-figlio-parola --utente2 $UTENTE2 --lavoro $DENTRO/tmp --uscita $DENTRO/02-figlio-esiti.jsonl"
	exit $? ;;

registro)
	log "Le righe «figlio» e «video» del server"
	fuori "grep -E '^[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3} (figlio|video|avvio) ' $LAV/registro.log | tail -60"
	exit 0 ;;

*)
	sed -n '2,20p' "$0"
	exit 2 ;;
esac
