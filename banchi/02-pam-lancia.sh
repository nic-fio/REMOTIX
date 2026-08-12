#!/bin/bash
#
# 02-pam-lancia.sh — ⛔ GIRA SU CHUWI.  Il banco «quanto sta fermo chi NON si
# sta autenticando» — `DECISIONI.md` §1.10.
#
#   bash banchi/02-pam-lancia.sh previsione     l'atteso, PRIMA del giro
#   bash banchi/02-pam-lancia.sh porta          copia src/ e i banchi su NIC-OS
#   bash banchi/02-pam-lancia.sh costruisci     copia + `make` nel contenitore
#   bash banchi/02-pam-lancia.sh accendi
#   bash banchi/02-pam-lancia.sh misura <bloccato|libero|nessuna> [giri]
#   bash banchi/02-pam-lancia.sh registro
#   bash banchi/02-pam-lancia.sh spegni
#   bash banchi/02-pam-lancia.sh porte          conta la 7448 e la 7501
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' ESISTE QUESTO FILE, E NON UNA RICETTA IN PROSA
#
# La stessa ragione di `01-p5-accendi.sh`: una ricetta scritta a parole la
# ricopia a mano chi la usa, e il 11 agosto 2026 e' stata sbagliata in due modi
# che un file non avrebbe sbagliato — il server acceso dalla cartella sbagliata
# (e la sua pagina non trovata), e una `&` dentro tre livelli di virgolette
# (`ssh` → `enter.sh` → `bash -c`) che non arriva dove sembra.
#
# ---------------------------------------------------------------------------
# ⛔ LE REGOLE DI CASA CHE QUESTO FILE RISPETTA, E CIASCUNA E' STATA PAGATA
#
#   · MAI una redirezione ATTORNO a `ssh` o a `enter.sh` — la richiesta di
#     parola d'ordine di `sudo` va sullo stderr, e una redirezione la mangia:
#     il comando resta appeso per sempre, IN SILENZIO.  ⛔ Pagata QUATTRO
#     volte, due delle quali nella sola notte dell'11 agosto 2026.  Qui la
#     parola di `sudo` entra dallo **stdin** di `ssh` — che e' la strada che
#     `enter.sh` documenta — e l'uscita non si redirige mai;
#   · la porta e' la **7531**, di questo banco e di nessun altro, e ban,
#     socket, registro, certificati e file del pid portano il prefisso
#     `pam2-7531`;
#   · la **7448** e la **7501** (e la **7522** di un altro giro) non si toccano:
#     si CONTANO prima e dopo, col passo `porte`;
#   · la parola d'ordine dei banchi non passa mai da `argv` (difetto **D12**):
#     un file `0600` scritto con `printf`, che e' un builtin della shell.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
RADICE=$(cd -- "$QUI/.." && pwd)
SERVER=nicfio@192.168.0.2
ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
PORTA=7531
PREFISSO=pam2-7531
UTENTE=prova
UTENTE_CATTIVO=prova2
ESITI_DENTRO=$DENTRO/02-pam-esiti.jsonl

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

# ⛔ La parola di `sudo` sta in ~/SERVER.ssh e si legge da li': scriverla in
#    questo file la metterebbe nel deposito.
PW=$(sed -n 's/^pass[[:space:]]*:[[:space:]]*//p' "$HOME/SERVER.ssh" 2>/dev/null)
if [ -z "$PW" ]; then
	ko "⛔ non ho letto la parola di sudo da ~/SERVER.ssh: non e' «vuota», e'"
	ko "   «non l'ho trovata».  Senza, ogni comando dentro il contenitore"
	ko "   resterebbe appeso ad aspettarla."
	exit 2
fi

# ⭐ Una funzione sola per entrare, cosi' la forma non si scrive due volte in
#    due modi diversi.  ⚠ La parola entra dallo STDIN di ssh, MAI dall'argv.
dentro() { printf '%s\n' "$PW" | ssh "$SERVER" "bash $ENTRA --root \"$1\""; }
fuori()  { ssh "$SERVER" "$1"; }

AZIONE=${1:-}

case "$AZIONE" in
previsione)
	python3 "$QUI/02-pam-fermo.py" --previsione
	exit 0 ;;

porte)
	# ⛔ Si CONTANO, non si toccano.  E si contano PRIMA e DOPO: «erano accese»
	#    e «le ho lasciate accese» sono due fatti diversi.
	log "Le porte degli altri, contate"
	fuori "ss -tuln | grep -E ':(7447|7448|7501|7511|7522|7531)\b' | sort"
	exit 0 ;;

porta)
	log "1. I file di questo banco vanno su NIC-OS"
	scp -q "$QUI"/02-pam-fermo.py "$QUI"/02-pam-i3.py "$QUI"/02-pam-accendi.sh \
	       "$SERVER:$FUORI/" \
		|| { ko "scp dei banchi fallito"; exit 2; }
	ok "02-pam-fermo.py e 02-pam-accendi.sh → $FUORI/"
	log "2. E i sorgenti del prodotto, in una cartella MIA"
	# ⛔ La cartella si CANCELLA prima di ricopiarla: un file di ieri rimasto
	#    li' dentro risponde «esisto» come uno di adesso (LEZIONI.md §1.9
	#    punto 8), e `scp` da solo non toglie niente.  ⚠ E `rsync` su CHUWI
	#    NON C'E' — misurato, non supposto: si usa quel che c'e'.
	fuori "rm -rf $FUORI/02-pam-src && mkdir -p $FUORI/02-pam-src" \
		|| { ko "non ho potuto rifare $FUORI/02-pam-src"; exit 2; }
	scp -q "$RADICE"/src/* "$SERVER:$FUORI/02-pam-src/" \
		|| { ko "scp di src/ fallito"; exit 2; }
	ok "src/ → $FUORI/02-pam-src/  ($(ls "$RADICE"/src | wc -l) file)"
	log "3. E la copia gemella di rcp.c, che il Makefile confronta (R12.3)"
	scp -q "$RADICE"/banchi/rcp/* "$SERVER:$FUORI/rcp/" \
		|| { ko "scp di banchi/rcp/ fallito"; exit 2; }
	ok "banchi/rcp/ → $FUORI/rcp/  (⛔ e se divergesse da src/, il make si ferma)"
	exit 0 ;;

costruisci)
	log "Copia e costruzione, dentro il contenitore"
	dentro "bash $DENTRO/02-pam-accendi.sh copia"
	exit $? ;;

guasto)
	# ⛔ Il guasto e' LA CURA TOLTA, e si innesta nella copia.  ⭐ Si risana con
	#    `costruisci`, che rifa' la copia da zero dai sorgenti veri.
	log "Innesto il guasto: il gancio asincrono NON collegato"
	dentro "bash $DENTRO/02-pam-accendi.sh guasto"
	exit $? ;;

accendi)
	log "Il bersaglio di questo banco, sulla $PORTA"
	dentro "bash $DENTRO/02-pam-accendi.sh accendi"
	exit $? ;;

riaccendi)
	# ⛔ Riaccende SENZA cancellare il file dei ban: e' il passo con cui si
	#    prova l'invariante I7 (il ban sopravvive al riavvio).
	log "Riaccendo il bersaglio CONSERVANDO il file dei ban (I7)"
	dentro "bash $DENTRO/02-pam-accendi.sh riaccendi"
	exit $? ;;

spegni)
	log "Spengo il MIO bersaglio (e solo quello)"
	dentro "bash $DENTRO/02-pam-accendi.sh spegni"
	exit $? ;;

registro)
	dentro "bash $DENTRO/02-pam-accendi.sh registro"
	exit $? ;;

misura)
	ATTESA=${2:-nessuna}
	GIRI=${3:-5}
	NOTA=${4:-}
	log "La misura: attesa «$ATTESA», $GIRI giri"
	# ⛔ D12: la parola in un file 0600, scritto con `printf` (un builtin), e
	#    cancellato subito dopo.  Mai in `argv`, che `/proc/<pid>/cmdline`
	#    mostra a chiunque.
	dentro "umask 077; printf '%s\n' 'parola-di-prova' > $DENTRO/tmp/$PREFISSO-parola; chmod 600 $DENTRO/tmp/$PREFISSO-parola"
	dentro "python3 $DENTRO/02-pam-fermo.py --porta $PORTA \
	        --utente $UTENTE --parola-file $DENTRO/tmp/$PREFISSO-parola \
	        --utente-cattivo $UTENTE_CATTIVO \
	        --socket $DENTRO/tmp/$PREFISSO.sock \
	        --giri $GIRI --attesa $ATTESA --esiti $ESITI_DENTRO --nota '$NOTA'"
	ESITO=$?
	dentro "rm -f $DENTRO/tmp/$PREFISSO-parola"
	exit $ESITO ;;

i3)
	CASO=${2:?serve il caso: secondo|ban|ban-dopo-riavvio|morto|insieme|libera}
	log "I3 e §4.4-bis: il caso «$CASO»"
	dentro "umask 077; printf '%s\n' 'parola-di-prova' > $DENTRO/tmp/$PREFISSO-parola; chmod 600 $DENTRO/tmp/$PREFISSO-parola"
	dentro "python3 $DENTRO/02-pam-i3.py --porta $PORTA --utente $UTENTE \
	        --parola-file $DENTRO/tmp/$PREFISSO-parola \
	        --socket $DENTRO/tmp/$PREFISSO.sock --caso $CASO"
	ESITO=$?
	dentro "rm -f $DENTRO/tmp/$PREFISSO-parola"
	exit $ESITO ;;

ammazza-aiutante)
	# ⛔ Il lavoro vero sta in `02-pam-accendi.sh`, che e' un FILE dentro il
	#    contenitore: qui non ci passa nessun `$(...)`, e il pezzo non puo'
	#    morire sulle virgolette lasciando credere di aver funzionato.
	log "Ammazzo l'aiutante di PAM del bersaglio (e solo il suo)"
	dentro "bash $DENTRO/02-pam-accendi.sh ammazza-aiutante"
	exit $? ;;

ritira-esiti)
	scp -q "$SERVER:$FUORI/02-pam-esiti.jsonl" "$QUI/02-pam-esiti.jsonl" \
		&& ok "esiti ritirati in $QUI/02-pam-esiti.jsonl" \
		|| { ko "non ho ritirato gli esiti"; exit 2; }
	exit 0 ;;

*)
	sed -n '2,15p' "$0"
	exit 2 ;;
esac
