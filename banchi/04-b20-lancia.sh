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
#   bash banchi/04-b20-lancia.sh valida <etichetta> [codec] [tela]  ⭐ l'altro lettore
#   bash banchi/04-b20-lancia.sh congeda    ⛔ prima di «nasci», sempre
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
#   2. `sessione con` + `scena` + `accendi` + `misura rosso-prima`
#                                                ⛔ DEVE dire **VUOTO**
#   3. (la cura in `src/sessione.c`) + `costruisci`
#   4. ⛔ `spegni` + `congeda`   ← il passo che mancava, e senza cui il 4-bis
#                                  non puo' funzionare (vedi sotto)
#   5. `nasci` + `scena` + `accendi` + `misura verde-dopo`
#                                                ⭐ DEVE dire **SHELL**
#
# ⚠ Un banco che nascesse verde non avrebbe mai visto il difetto, e la cura
#   scritta sopra di lui sarebbe scritta al buio.
#
# ⛔⭐ PERCHE' IL PASSO 4 E' ENTRATO — 22 agosto 2026, e la colpa era del banco.
#
#     `src/sessione.h:240`: `sessione_assicura()` **«si avvia solo da
#     SESSIONE_MORTA»**.  L'ordine scritto qui sopra andava da `sessione con`
#     dritto a `nasci`, con la sessione del giro rosso ancora viva: `[M]` il
#     prodotto ha risposto **3 SCELTO DA SE**, cioe' «c'e' gia' una sessione
#     con due monitor e NON la tocco» — che e' la cosa giusta.  ⛔ Il banco
#     usciva 3 e sembrava un rosso contro il prodotto.  ⚠ E' la forma «un
#     attrezzo che muore su dati veri accusa i dati, e quasi sempre ha torto».
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
RADICE=$(cd -- "$QUI/.." && pwd)
SSHPW="$RADICE/v1/strumenti/sshpw.py"

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔⭐ ERA PARAMETRICO A META', E NON SI VEDEVA — cura del 22 agosto 2026
#
# Fino a stamattina questo file leggeva `PORTA` e `UTENTE` dall'ambiente ⛔ e
# poi NON li passava dall'altra parte: `radice "bash …/04-b20-terreno.sh
# accendi"` attraversa `ssh` e `sudo`, che l'ambiente **non lo portano**.
# ⇒ Con `PORTA=7711 bash 04-b20-lancia.sh accendi` il server nasceva sulla
# **7601** (il predefinito di `terreno.sh`) e `misura` mandava il client sulla
# **7711**.  Il sintomo sarebbe stato «il client non si collega», cioe' ⛔ **un
# rosso contro il prodotto per un difetto del banco**.  ⚠ E' la forma che il 21
# agosto notte ha gia' prodotto un verdetto rosso falso su un altro banco:
# «l'utente della sessione era parametrico da un lato e fisso dall'altro».
#
# ⭐ La cura, e vale per tutte le variabili insieme: `$AMB` si compone qui una
#    volta sola e si mette **davanti a ogni comando remoto**.  ⛔ Chi aggiunge
#    un sottocomando nuovo deve passare da `radice`/`dentro`, che l'ambiente
#    ce l'hanno gia' dentro: fuori di li' torna il difetto.
#
# ⭐ E ALBERO e LAV adesso si spostano — la stessa regola che `07-b41-accendi.sh`
#    si e' data il 17 agosto: «due banchi che spingono sorgenti nella stessa
#    cartella si sovrascrivono a vicenda».  ⚠ I predefiniti NON cambiano.
# ═══════════════════════════════════════════════════════════════════════════
FUORI=/media/REMOTIX/src
ALBERO=${ALBERO:-$FUORI/04-a1-src}
LAV=${LAV:-/media/REMOTIX/tmp/04-b20}
# ⛔ I due nomi DENTRO il contenitore si derivano, non si riscrivono: e' la
#    trappola di `07-b41` — «con un albero diverso si compilava quello di prima
#    e si accendeva quello nuovo, e i due avevano la stessa faccia».
LAV_DENTRO=/srv/remotix/tmp/$(basename "$LAV")
ALBERO_DENTRO=/srv/src/$(basename "$ALBERO")
PORTA=${PORTA:-7601}
UTENTE=${UTENTE:-provaa1}
UID_B=${UID_B:-1002}
PAROLA=${PAROLA:-provaa1-2026}
MISURA=${MISURA:-1920x1080}
ESITI=$LAV_DENTRO/04-b20-esiti.jsonl
# ⛔ LA SCENA SI DICHIARA, e la dichiarazione deve essere VERA — `CODER.md` §3.2.
#    ⚠ Era una costante scritta dentro il comando: «nessuna finestra, nessun
#      input».  ⛔ Ma il giro certificante passa per `scena`, che apre una
#      finestra di `gnome-terminal` che scrive l'ora — cioe' la riga accanto a
#      ogni numero in `04-b20-esiti.jsonl` **descriveva un'altra scena**.
SCENA=${SCENA:-"sessione GNOME di $UTENTE, scena banco-A1-scena accesa: una finestra gnome-terminal che scrive l ora ogni 0,2 s. L oggetto e il PRIMO fotogramma chiave"}

# ⛔ L'ambiente che DEVE attraversare `ssh` e `sudo`.  ⚠ `D` e' la cartella dei
#    sorgenti come la vede l'HOST (terreno.sh gira fuori dal contenitore).
AMB="PORTA=$PORTA UTENTE=$UTENTE UID_B=$UID_B PAROLA=$PAROLA MISURA=$MISURA \
D=$ALBERO/src LAV=$LAV DENTRO=$LAV_DENTRO BANCHI_DENTRO=$ALBERO_DENTRO/banchi"
# ⛔⛔ E DENTRO IL CONTENITORE `LAV` NON E' LA STESSA CARTELLA: `/media/REMOTIX`
#     li' si chiama `/srv/remotix`.  ⚠ Passando `$AMB` anche a `dentro()`,
#     `04-b20-costruisci.sh` avrebbe scritto il programma minimo in un percorso
#     che dentro il contenitore non esiste — e il difetto sarebbe stato «non
#     trovo 04-b20-nasci» addossato a `nasci`, che non c'entra niente.
AMB_D="PORTA=$PORTA UTENTE=$UTENTE MISURA=$MISURA LAV=$LAV_DENTRO"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

fuori()  { timeout 1200 python3 "$SSHPW" "$1"; }
# ⛔ `env $AMB` davanti a TUTT'E DUE: vedi il riquadro «era parametrico a meta'».
# ⛔ `export …;` e NON `env …`: quel che si manda qui dentro non e' sempre un
#    comando semplice — `cd X && python3 …` con `env` davanti fa
#    «env: 'cd': No such file or directory», perche' `cd` e' una parola della
#    shell e non un programma.  `[M]` 22 agosto 2026, primo giro di `misura`.
dentro() { timeout 1200 python3 "$SSHPW" "bash /media/REMOTIX/enter.sh --root \"export $AMB_D; $1\""; }
radice() { timeout 1200 python3 "$SSHPW" "sudo -S -p 'Password sudo: ' env $AMB $1"; }
metti()  { timeout 600 python3 "$SSHPW" --put "$1" "$2"; }

case "${1:-}" in
certifica)
	log "Lo STRUMENTO, prima del prodotto — deve saper dire tutt'e due le cose"
	python3 "$QUI/04-b20-desktop-vero.py" --certifica --lavoro /tmp/04-b20
	exit $? ;;

porte)
	log "Le porte degli altri, contate — NON si toccano"
	# ⚠ 7700 e 7730 sono entrate il 22 agosto 2026: erano vive e questo elenco
	#   non le contava.  ⛔ E si conta anche LA MIA, che qui e' parametrica.
	fuori "ss -tuln | grep -E ':(7448|7501|7561|7571|7700|7730|7781|$PORTA)\b' | sort"
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
	# ⭐ `attrezzi-gruppi-scheda.sh` va CON il terreno: senza, `utente` si
	#    ferma di la' con «manca …» (e fa bene: un inquilino cieco non si crea).
	cp "$QUI/attrezzi-gruppi-scheda.sh" \
	   "$QUI/04-b20-desktop-vero.py" "$QUI/04-b20-terreno.sh" \
	   "$QUI/04-b20-nasci.c" "$QUI/04-b20-costruisci.sh" \
	   "$QUI/04-b20-persistenza.sh" "$QUI/04-b20-stacco.sh" "$QUI/02-filo-cliente.py" \
	   "$QUI/02-filo-fotogramma.py" "$QUI/01-b3-cliente.py" \
	   "$QUI/02-filo-validatore.py" "$T/banchi/" || exit 2
	# ⛔ `02-filo-validatore.py` e' entrato il 22 agosto 2026: il client stampa
	#    «e va data a `02-filo-validatore.py`, che e' l'altro lettore» ⛔ e poi
	#    quel file non era nell'albero.  ⇒ Il consiglio non si poteva seguire, e
	#    la registrazione aveva **un lettore solo** — cioe' il formato §11.1 era
	#    verificato da chi lo scrive e da un suo parente, che e' la condizione
	#    del difetto «due programmi della stessa mano che vanno d'accordo».
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

congeda)
	# ⛔ Va fatto FRA il giro rosso e `nasci`: `sessione_assicura()` si avvia
	#    solo da `SESSIONE_MORTA` (`src/sessione.h:240`).  Il riquadro sta in
	#    `04-b20-terreno.sh`, caso `congeda`.
	log "4-bis-a. Congedo la sessione del giro precedente"
	radice "bash $ALBERO/banchi/04-b20-terreno.sh congeda"
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
	# ⛔⭐ LA REGISTRAZIONE DI IERI SI BUTTA PRIMA, e non e' pignoleria: se il
	#    client non parte, il giudice qui sotto legge il file del giro
	#    precedente e da' un verdetto **su una misura vecchia**.  E' la forma
	#    D5 — «un artefatto stantio resta verde» — e non lascia nessuna
	#    traccia, perche' il verdetto arriva puntuale.
	#    `[M]` 22 agosto 2026: il client e' morto davvero (`env: 'cd': No such
	#    file or directory`) e questa riga non c'era.
	dentro "rm -f $LAV_DENTRO/$ET.rcpreg"
	dentro "printf '%s' '$PAROLA' > $LAV_DENTRO/parola && chmod 600 $LAV_DENTRO/parola"
	# ⛔ E l'esito del client si GUARDA.  ⚠ Prima c'era `… 2>&1 | tail -25`, e
	#    la pipe **mangia il codice d'uscita**: il client poteva morire e il
	#    giro proseguiva senza una riga che lo dicesse (§1.20, «l'esito
	#    d'uscita catturato e mai confrontato», qui nemmeno catturato).
	# ⛔ Il `tail` si fa in un secondo giro, su un file: un `{ …; echo $?; } |
	#    tail` qui dentro sarebbe il terzo livello di virgolette
	#    (host → ssh → enter.sh), che e' la regola di casa che questo file
	#    dichiara di rispettare in testa.
	# ⚠ Un client caduto NON ferma il giro: «il client e' caduto» e «non e'
	#   arrivato niente» sono due frasi diverse, e il giudice deve poter dire
	#   la seconda — ma adesso la prima si vede.
	dentro "cd $ALBERO_DENTRO/banchi && python3 02-filo-cliente.py --porta $PORTA --utente $UTENTE --parola-file $LAV_DENTRO/parola --larghezza $L --altezza $A --attesa 40 --registra $LAV_DENTRO/$ET.rcpreg > $LAV_DENTRO/$ET-client.log 2>&1"
	CU=$?
	dentro "tail -25 $LAV_DENTRO/$ET-client.log"
	if [ "$CU" -eq 0 ]; then ok "il client e' uscito 0"
	else ko "⛔ il client e' uscito $CU — quel che segue giudica una "\
"registrazione INCOMPLETA, se c'e'"; fi
	radice "bash $ALBERO/banchi/04-b20-terreno.sh monitor"
	dentro "cd $ALBERO_DENTRO/banchi && python3 04-b20-desktop-vero.py --registrazione $LAV_DENTRO/$ET.rcpreg --lavoro $LAV_DENTRO --etichetta $ET --scena '$SCENA' --esiti $ESITI"
	exit $? ;;

valida)
	# ⛔⭐ IL SECONDO LETTORE — 22 agosto 2026.
	#
	#     `RCP.md` §11.1: il formato e' passato a `RCPREG 0x00 0x03` il 21
	#     agosto, e la sua tenuta si prova facendolo leggere da **tutti** i
	#     lettori, non da uno.  ⛔ Fino a ieri questo giro ne usava uno solo
	#     (`04-b20-desktop-vero.py`), che e' della stessa mano di chi scrive:
	#     due programmi della stessa mano che vanno d'accordo non confermano
	#     niente (`PIANO.md` §0.4).
	#
	# ⛔ E il CODEC si dichiara da fuori, non si indovina: l'arbitro lo dice da
	#    solo — «un arbitro che li indovinasse starebbe giudicando i propri
	#    predefiniti».  ⚠ `[M]` 22 agosto: passandogli `--codec 2` su una
	#    sessione negoziata a 1 ha detto NON CONFORME, ed **aveva ragione lui**.
	ET=${2:?uso: valida <etichetta> [codec] [tela]}
	CODEC=${3:-1}
	TELA=${4:-1920x1080}
	L=${TELA%x*}; A=${TELA#*x}
	log "6-bis. ⭐ L'ALTRO lettore del formato §11.1 — «$ET», codec $CODEC, tela $TELA"
	dentro "cd $ALBERO_DENTRO/banchi && python3 02-filo-validatore.py $LAV_DENTRO/$ET.rcpreg --codec $CODEC --tela-larghezza $L --tela-altezza $A --uscita $LAV_DENTRO/04-b20-filo-esiti.jsonl 2>&1 | tail -12"
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
