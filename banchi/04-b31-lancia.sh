#!/bin/bash
#
# 04-b31-lancia.sh — ⛔ GIRA SU CHUWI, dove sta il deposito.  Il banco
# dell'anello **O1** della fase 4: ⭐ **l'apparizione del desktop**.
#
#   bash banchi/04-b31-lancia.sh certifica    lo STRUMENTO, senza il prodotto
#   bash banchi/04-b31-lancia.sh porte        conta le porte degli altri
#   bash banchi/04-b31-lancia.sh porta        manda src/ e i banchi su NIC-OS
#   bash banchi/04-b31-lancia.sh costruisci   `make` nel contenitore
#   bash banchi/04-b31-lancia.sh utente       l'utente del banco
#   bash banchi/04-b31-lancia.sh sessione     GNOME senza --virtual-monitor
#   bash banchi/04-b31-lancia.sh scena        la scena che si muove
#   bash banchi/04-b31-lancia.sh accendi      il server sulla 7711
#   bash banchi/04-b31-lancia.sh misura <etichetta> [attesa]
#   bash banchi/04-b31-lancia.sh g1 <etichetta>   ⛔ la sessione muore sotto il figlio
#   bash banchi/04-b31-lancia.sh g2 <etichetta>   ⛔ il figlio nasce senza sessione
#   bash banchi/04-b31-lancia.sh esiti
#   bash banchi/04-b31-lancia.sh registro
#   bash banchi/04-b31-lancia.sh spegni · pulisci
#
# ---------------------------------------------------------------------------
# ⛔ LE REGOLE DI CASA CHE QUESTO FILE RISPETTA
#
#   · ⛔ **MAI una redirezione ATTORNO a `ssh` o a `enter.sh`**: la richiesta di
#     parola d'ordine di `sudo` va sullo stderr, e una redirezione la mangia —
#     il comando resta appeso per sempre, in silenzio.  ⇒ Si passa da
#     `fondamenta/strumenti/sshpw.py`;
#   · ⛔ **un file non ha livelli di virgolette**: quel che deve girare dentro il
#     contenitore sta in uno script sul server;
#   · le porte sono le **7711-7715**, di questo anello e di nessun altro.  ⛔ La
#     7448, la 7501, la 7561, la 7571, la 7601 e la 7691 si CONTANO e non si
#     toccano;
#   · l'albero dei sorgenti e' **04-o1-src**, che nessun altro anello usa;
#   · ⛔ ban, socket del comando e certificati sono PROPRI (`RCP.md` §4.4-bis).
#
# ---------------------------------------------------------------------------
# ⛔⭐ IL GIRO CHE CERTIFICA — e l'ordine non e' un'opinione (`CODER.md` §3.3)
#
#   1. `certifica`                    lo strumento sa dire VERDE, TARDI, MAI,
#                                     ZERO — e i suoi conti sono quelli di A1
#   2. `misura prima`                 ⛔ DEVE dire **ROSSO**, coi suoi ~5 s
#   3. `g1 prima` · `g2 prima`        ⛔ DEVONO far comparire i due gemelli
#   4. (la cura in `src/figlio.c`, `src/cattura.c`)
#   5. `misura dopo` · `g1 dopo` · `g2 dopo`   ⭐ e allora i numeri valgono
#
# ⚠ Un banco che nascesse verde non avrebbe mai visto il difetto, e la cura
#   scritta sopra di lui sarebbe scritta al buio (`CODER.md` §3.4).
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
RADICE=$(cd -- "$QUI/.." && pwd)
SSHPW="$RADICE/fondamenta/strumenti/sshpw.py"

FUORI=/media/REMOTIX/src
ALBERO=$FUORI/04-o1-src
LAV=/media/REMOTIX/tmp/04-b31
LAV_DENTRO=/srv/remotix/tmp/04-b31
ALBERO_DENTRO=/srv/src/04-o1-src
PORTA=${PORTA:-7711}
UTENTE=${UTENTE:-provao1}
PAROLA=${PAROLA:-provao1-2026}
ESITI=$LAV_DENTRO/04-b31-esiti.jsonl

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

fuori()  { timeout 1800 python3 "$SSHPW" "$1"; }
dentro() { timeout 1800 python3 "$SSHPW" "bash /media/REMOTIX/enter.sh --root \"$1\""; }
radice() { timeout 1800 python3 "$SSHPW" "sudo -S -p 'Password sudo: ' $1"; }
metti()  { timeout 900 python3 "$SSHPW" --put "$1" "$2"; }
prendi() { timeout 900 python3 "$SSHPW" --get "$1" "$2"; }

case "${1:-}" in
certifica)
	log "1. Lo STRUMENTO, prima del prodotto"
	inf "il ciclo a vuoto — gira qui, non vuole ne' rete ne' ffmpeg"
	python3 "$QUI/04-b31-gemelli.py" --certifica || exit $?
	inf "il cronometro e il giudice dei pixel — vogliono ffmpeg: nel contenitore"
	dentro "cd $ALBERO_DENTRO/banchi && python3 04-b31-apparizione.py --certifica --lavoro $LAV_DENTRO/cert"
	exit $? ;;

porte)
	log "Le porte degli altri, contate — NON si toccano"
	fuori "ss -tuln | grep -E ':(7448|7501|7561|7571|7601|7691|7711)\b' | sort"
	exit 0 ;;

porta)
	log "I sorgenti, in un albero MIO"
	# ⛔⛔ E PRIMA DI TUTTO SI SPEGNE IL SERVER, e non e' pulizia.
	#
	#     `[M]` 14 agosto 2026, primo giro di questo banco: ho ricopiato
	#     l'albero **a server acceso**.  Il `rm -rf` ha cancellato il binario
	#     sotto i piedi del processo, che ha continuato a girare sull'inode
	#     morto — e al primo login il figlio ha fatto `execve` su un percorso
	#     che non c'era piu': ⛔ **uscita 37**, nessun palco, e il banco ha detto
	#     ZERO FOTOGRAMMI.  ⚠ Il registro accusava il PRODOTTO di un difetto del
	#     lanciatore, e i due hanno la stessa faccia da fuori.
	radice "bash $ALBERO/banchi/04-b31-terreno.sh spegni" 2>/dev/null
	# ⛔ La cartella si CANCELLA prima di ricopiarla: un file di ieri rimasto
	#    li' dentro risponde «esisto» come uno di adesso.
	radice "rm -rf $ALBERO"
	fuori "mkdir -p $ALBERO/banchi/rcp && mkdir -p $LAV" \
		|| { ko "non ho potuto rifare $ALBERO"; exit 2; }
	# ⛔ L'albero si prende da **HEAD**, non dalla cartella di lavoro: altri
	#    anelli stanno scrivendo dentro `src/`, e un albero mezzo loro e mezzo
	#    mio non e' ne' il prodotto ne' la cura.
	#    ⚠ `figlio.c`, `cattura.c` e `cattura.h` invece si prendono dalla
	#      cartella di lavoro, perche' sono i file di O1 ed e' li' che la cura
	#      vive.
	T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
	(cd "$RADICE" && git archive HEAD src banchi/rcp) | tar -x -C "$T" || exit 2
	# ⛔⭐ E CON `PRIMA=1` NON SI COPIA NIENTE: l'albero resta quello di HEAD,
	#     cioe' **il prodotto com'e'**.  ⚠ Serve al giro che `CODER.md` §3.4
	#     pretende: il banco deve far comparire il difetto **prima** che la cura
	#     esista, o la cura e' scritta al buio.
	if [ "${PRIMA:-0}" = 1 ]; then
		inf "⛔ PRIMA=1: figlio.c · cattura.c · cattura.h restano quelli di HEAD"
	else
		for f in figlio.c cattura.c cattura.h; do
			cp "$RADICE/src/$f" "$T/src/$f" || exit 2
		done
	fi
	mkdir -p "$T/banchi"
	# ⭐ `attrezzi-gruppi-scheda.sh` va CON il terreno (vedi il suo riquadro).
	cp "$QUI/attrezzi-gruppi-scheda.sh" \
	   "$QUI/04-b31-cliente.py" "$QUI/04-b31-apparizione.py" \
	   "$QUI/04-b31-gemelli.py" "$QUI/04-b31-terreno.sh" \
	   "$QUI/04-b31-costruisci.sh" "$QUI/04-b20-desktop-vero.py" \
	   "$QUI/02-filo-cliente.py" "$QUI/02-filo-fotogramma.py" \
	   "$QUI/01-b3-cliente.py" "$T/banchi/" || exit 2
	tar czf /tmp/04-o1-src.tgz -C "$T" src banchi || exit 2
	metti /tmp/04-o1-src.tgz "$ALBERO/src.tgz" || { ko "scp fallito"; exit 2; }
	fuori "cd $ALBERO && tar xzf src.tgz && rm -f src.tgz && ls src | wc -l && ls banchi"
	ok "portati in $ALBERO"
	exit 0 ;;

costruisci)
	log "2. Compilo nel contenitore"
	dentro "bash $ALBERO_DENTRO/banchi/04-b31-costruisci.sh"
	exit $? ;;

utente)
	log "3. L'utente del banco"
	radice "bash $ALBERO/banchi/04-b31-terreno.sh utente"
	exit $? ;;

sessione)
	log "4. La sessione GNOME di $UTENTE — SENZA --virtual-monitor"
	radice "bash $ALBERO/banchi/04-b31-terreno.sh sessione"
	exit $? ;;

sessione-via)
	radice "bash $ALBERO/banchi/04-b31-terreno.sh sessione-via"
	exit $? ;;

scena)
	log "4-bis. ⛔ La scena, che si DICHIARA e si MUOVE (CODER.md §3.2)"
	radice "bash $ALBERO/banchi/04-b31-terreno.sh scena"
	exit $? ;;

scena-via)
	radice "bash $ALBERO/banchi/04-b31-terreno.sh scena-via"
	exit $? ;;

accendi)
	log "5. Il server sulla $PORTA"
	radice "bash $ALBERO/banchi/04-b31-terreno.sh accendi"
	exit $? ;;

parola)
	dentro "mkdir -p $LAV_DENTRO && printf '%s' '$PAROLA' > $LAV_DENTRO/parola && chmod 600 $LAV_DENTRO/parola"
	exit $? ;;

misura)
	ET=${2:?uso: misura <etichetta> [attesa]}
	AT=${3:-25}
	SC=${SCENA:-"sessione GNOME viva, una finestra che scrive l ora 5 volte al secondo; il client si attacca ADESSO"}
	log "6. ⭐ LOGIN → PRIMO PIXEL VERO — «$ET»"
	bash "$0" parola >/dev/null 2>&1
	radice "bash $ALBERO/banchi/04-b31-terreno.sh monitor"
	dentro "cd $ALBERO_DENTRO/banchi && python3 04-b31-cliente.py --porta $PORTA --utente $UTENTE --parola-file $LAV_DENTRO/parola --lavoro $LAV_DENTRO --etichetta $ET --attesa $AT --scena '$SC'"
	u=$?
	[ $u -eq 2 ] && { ko "la stretta di mano non e' arrivata a SESSIONE: non si e' misurato niente"; exit 2; }
	dentro "cd $ALBERO_DENTRO/banchi && python3 04-b31-apparizione.py --misura $LAV_DENTRO/$ET-misura.json --lavoro $LAV_DENTRO --esiti $ESITI"
	exit $? ;;

g1)
	# ⛔⭐ IL PRIMO DIFETTO GEMELLO — la sessione grafica muore SOTTO un figlio
	#     vivo.  ⚠ Il client resta attaccato per tutto il tempo, in PRIMO PIANO:
	#     e' quel che tiene `codec_chiesto` diverso da zero, cioe' la condizione
	#     del ciclo.  Chi lo mandasse in sottofondo misurerebbe un figlio che
	#     nessuno guarda — e quello, giustamente, non gira a vuoto.
	ET=${2:?uso: g1 <etichetta>}
	log "7. ⛔ GEMELLO 1 — la sessione grafica muore sotto un figlio vivo, «$ET»"
	bash "$0" parola >/dev/null 2>&1
	# ⛔ La sessione DEVE essere viva prima di cominciare, e il controllo non si
	#    fa in silenzio: `[M]` 14 agosto 2026, un giro di questo banco e' partito
	#    con la sessione gia' morta dal giro precedente — e ha misurato l'ALTRO
	#    gemello credendo di misurare questo.  ⚠ Due misure sotto la stessa
	#    etichetta e' peggio che non misurare.
	radice "bash $ALBERO/banchi/04-b31-terreno.sh sessione" | tail -3 \
		|| { ko "⛔ la sessione non riparte: la scena di G1 non si puo' fare"; exit 3; }
	radice "bash $ALBERO/banchi/04-b31-terreno.sh scena" | tail -1
	# ⛔ E il server si RIACCENDE, perche' il figlio della volta scorsa e' vivo e
	#    l'invariante I2 lo riconsegnerebbe: un figlio nato senza sessione non e'
	#    la scena di G1.
	radice "bash $ALBERO/banchi/04-b31-terreno.sh spegni" | tail -1
	radice "bash $ALBERO/banchi/04-b31-terreno.sh accendi" | tail -1 \
		|| { ko "⛔ il server non riparte"; exit 3; }
	inf "armo la scena: fra 8 s uccido la sessione, poi 3 s di spia"
	radice "bash $ALBERO/banchi/04-b31-terreno.sh gemello1-sfondo 8 3" | tail -1
	inf "e adesso il client, in primo piano, per 20 s"
	dentro "cd $ALBERO_DENTRO/banchi && python3 04-b31-cliente.py --porta $PORTA --utente $UTENTE --parola-file $LAV_DENTRO/parola --lavoro $LAV_DENTRO --etichetta $ET-cli --attesa 20 --chiedi-chiave-ogni 0.5 --scena 'il client resta attaccato e CHIEDE CHIAVI mentre la sessione grafica muore' 2>&1 | tail -6"
	radice "bash $ALBERO/banchi/04-b31-terreno.sh gemello1-leggi" > "/tmp/$ET-spia.txt" 2>&1
	sed 's/^/        /' "/tmp/$ET-spia.txt"
	radice "bash $ALBERO/banchi/04-b31-terreno.sh figlio"
	python3 "$QUI/04-b31-gemelli.py" --spia "/tmp/$ET-spia.txt" --etichetta "$ET" \
		--scena "sessione grafica uccisa sotto un figlio vivo, client ATTACCATO" \
		--esiti "$RADICE/banchi/04-b31-esiti.jsonl"
	exit $? ;;

g2)
	# ⛔⭐ IL SECONDO DIFETTO GEMELLO — il figlio nasce quando la sessione non
	#     c'e'.  ⚠ E la prova non e' «il primo attacco fallisce»: e' che il
	#     SECONDO, con la sessione ormai viva, trova lo stesso figlio rotto
	#     (invariante I2) e non vede niente lo stesso.
	ET=${2:?uso: g2 <etichetta>}
	log "8. ⛔ GEMELLO 2 — il figlio nasce SENZA sessione, «$ET»"
	bash "$0" parola >/dev/null 2>&1
	inf "spengo il server e la sessione, e riaccendo il solo server"
	radice "bash $ALBERO/banchi/04-b31-terreno.sh spegni"
	radice "bash $ALBERO/banchi/04-b31-terreno.sh sessione-via"
	radice "bash $ALBERO/banchi/04-b31-terreno.sh accendi" || exit 3
	inf "primo attacco: la sessione NON c'e' ⇒ il figlio prende un palco vuoto"
	# ⛔ La spia gira MENTRE il client e' attaccato, non dopo: un figlio che non
	#    guarda piu' nessuno non gira a vuoto nemmeno quando e' rotto.
	radice "bash $ALBERO/banchi/04-b31-terreno.sh spia-sfondo 6 3" | tail -1
	dentro "cd $ALBERO_DENTRO/banchi && python3 04-b31-cliente.py --porta $PORTA --utente $UTENTE --parola-file $LAV_DENTRO/parola --lavoro $LAV_DENTRO --etichetta $ET-a --attesa 12 --chiedi-chiave-ogni 0.5 --scena 'la sessione grafica NON c e quando il figlio nasce' 2>&1 | tail -8"
	radice "bash $ALBERO/banchi/04-b31-terreno.sh spia-sfondo-leggi" > "/tmp/$ET-spia.txt" 2>&1
	sed 's/^/        /' "/tmp/$ET-spia.txt"
	radice "bash $ALBERO/banchi/04-b31-terreno.sh figlio"
	# ⚠ E si guarda anche QUI se il figlio gira a vuoto: un figlio nato senza
	#   palco, con un client attaccato, brucia un nucleo **in silenzio** — il
	#   registro non cresce, e un banco che guardasse solo il disco lo
	#   dichiarerebbe sano.  `[M]` 14 agosto 2026, ed e' la faccia muta dello
	#   stesso difetto.
	python3 "$QUI/04-b31-gemelli.py" --spia "/tmp/$ET-spia.txt" --etichetta "$ET-ciclo" \
		--scena "figlio nato SENZA sessione grafica, client attaccato" \
		--esiti "$RADICE/banchi/04-b31-esiti.jsonl"
	inf "⭐ adesso la sessione nasce, e si muove"
	radice "bash $ALBERO/banchi/04-b31-terreno.sh sessione" || exit 3
	radice "bash $ALBERO/banchi/04-b31-terreno.sh scena" || exit 3
	inf "SECONDO attacco: la sessione c'e'.  ⛔ I2 consegna lo STESSO figlio"
	dentro "cd $ALBERO_DENTRO/banchi && python3 04-b31-cliente.py --porta $PORTA --utente $UTENTE --parola-file $LAV_DENTRO/parola --lavoro $LAV_DENTRO --etichetta $ET-b --attesa 20 --scena 'la sessione c e ADESSO, ma il figlio e quello nato senza'"
	radice "bash $ALBERO/banchi/04-b31-terreno.sh figlio"
	dentro "cd $ALBERO_DENTRO/banchi && python3 04-b31-apparizione.py --misura $LAV_DENTRO/$ET-b-misura.json --lavoro $LAV_DENTRO --esiti $ESITI"
	exit $? ;;

figlio)
	radice "bash $ALBERO/banchi/04-b31-terreno.sh figlio"
	exit $? ;;

esiti)
	log "Gli esiti"
	prendi "$LAV/04-b31-esiti.jsonl" "$RADICE/banchi/04-b31-esiti.jsonl" \
		|| fuori "cat $LAV/04-b31-esiti.jsonl"
	[ -f "$RADICE/banchi/04-b31-esiti.jsonl" ] && cat "$RADICE/banchi/04-b31-esiti.jsonl"
	exit 0 ;;

prendi)
	ET=${2:?uso: prendi <nome-file>}
	prendi "$LAV/$ET" "/tmp/$ET"
	exit $? ;;

registro)
	fuori "tail -${2:-80} $LAV/registro.log"
	exit 0 ;;

spegni)
	radice "bash $ALBERO/banchi/04-b31-terreno.sh spegni"
	exit $? ;;

stato)
	radice "bash $ALBERO/banchi/04-b31-terreno.sh stato"
	exit $? ;;

pulisci)
	radice "bash $ALBERO/banchi/04-b31-terreno.sh pulisci"
	exit $? ;;

*)
	sed -n '2,25p' "$0"
	exit 2 ;;
esac
