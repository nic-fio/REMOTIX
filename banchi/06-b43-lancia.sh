#!/bin/bash
#
# 06-b43-lancia.sh — ⛔ GIRA SUL SERVER (NIC-OS), **DA ROOT**, fuori dal
# contenitore.  Il banco che misura **quanto si tiene il posto**.
#
#   sudo bash .../06-b43-lancia.sh congedo    il congedo pulito (0x01)
#   sudo bash .../06-b43-lancia.sh chiusura   CONNECTION_CLOSE, senza CONGEDO
#   sudo bash .../06-b43-lancia.sh sigkill    ⛔ il client ammazzato
#   sudo bash .../06-b43-lancia.sh sigstop    ⛔ il client congelato = rete staccata
#   sudo bash .../06-b43-lancia.sh vivo       ⛔ vivo sul filo e muto su RCP
#   sudo bash .../06-b43-lancia.sh tutti
#
# ===========================================================================
# ⛔⛔ LA DOMANDA, E L'IPOTESI DA CUI SI PARTE
# ===========================================================================
#
# `fasi/06-la-tela-e-la-vista.md` §7.2: *«il posto si lascia dopo **~75 s** di
# silenzio, non i 30 di §5.3: `[?]` quale sia il tetto vero»*.
#
# ⭐ **Il mandato e' avversariale**, e si parte dall'ipotesi che §5.3 **abbia
#    ragione** — *«il client che tace da 30 secondi e' staccato»* — cercando la
#    prova che non e' cosi'.  ⇒ Gli attesi si scrivono QUI, prima della misura,
#    in due colonne: che cosa si vedrebbe se §5.3 fosse in vigore, e che cosa
#    se il tetto vero fosse un altro.
#
#   caso        se §5.3 e' in vigore          se il tetto vero e' un altro
#   ---------   ---------------------------   ------------------------------
#   congedo     posto libero **subito**       un ritardo qualunque
#   chiusura    posto libero **subito**       un ritardo qualunque
#   sigkill     posto libero a **~30 s**      un numero diverso da 30
#   sigstop     posto libero a **~30 s**      un numero diverso da 30
#   vivo        ⛔ **il posto NON si lascia** ⇒ e questo NON contraddice §5.3:
#               `rcp.c:7041` conta i PACCHETTI, e un client vivo ne manda.
#               La §5.3 dice «il CLIENT tace»; il prodotto legge «il FILO
#               tace».  Sono due frasi diverse, e questo caso le separa.
#
# ⛔ E il numero che serve a chi scrive banchi e' **il peggiore dei casi che
#    puo' capitargli**, non la media dei cinque.
#
# ===========================================================================
# ⛔ I TRE OROLOGI CHE SI SEPARANO — e sono tre fatti, non tre stime
# ===========================================================================
#
#  T1  il **posto**: da quando il client se n'e' andato a quando il server
#      scrive `STACCATO per silenzio` e i posti occupati scendono.
#      ⇒ si legge nel registro, con la sua millesima.
#  T2  la **sessione nuova**: da quando il client se n'e' andato a quando un
#      ALTRO client riesce davvero ad attaccarsi.  ⇒ lo dice la sonda, e ⛔
#      non il registro: E1, «scritto non e' in vigore».
#  T3  il **figlio**: se e quando il processo del palco muore.  ⇒ `ps`, non il
#      registro.  ⚠ L'invariante I4 dice che NON deve morire, e allora T3 e'
#      «mai» — che e' una misura anche lui, e va scritta.
#
# ===========================================================================
# ⛔ LE TRAPPOLE DI QUESTO BANCO, IN TESTA
# ===========================================================================
#
#  1. ⛔⛔ **L'orologio del silenzio ruba 30 s alle prove.**  Fra «il client e'
#     attaccato» e «lo ammazzo» devono passare POCHI secondi: se ne passassero
#     trenta, §5.3 avrebbe gia' lasciato il posto da sola e si misurerebbe
#     un'altra cosa.  ⇒ `RESPIRO` e' 5 s, e il banco **rifiuta** di misurare se
#     fra `ATTACCATO` e la partenza sono passati piu' di 20 s.
#  2. ⛔ **`--parlantina` sempre**: senza, il figlio tace in silenzio.
#  3. ⛔ **Il primo attacco crea la sessione grafica e costa decine di
#     secondi**: c'e' un giro di RISCALDAMENTO, e i suoi numeri si buttano.
#  4. ⛔ **Nessun browser qui dentro.**  La pagina rilascia da sola su
#     `blur`/`visibilitychange`/`pagehide`: un browser che si chiude bene NON
#     e' il caso «se ne va male», e misurarlo darebbe il numero del congedo
#     credendo di misurare l'abbandono.  ⇒ Il client e' `06-b43-occupante.py`.
#  5. ⚠ Otto banchi su questa macchina: **il carico si scrive accanto a ogni
#     numero**, o il numero non e' una misura.
#
# ===========================================================================
# ⭐⭐ QUEL CHE HA MISURATO — `[M]` 22 agosto 2026, porta 7801, utente
#      `provar7`, sessione GNOME headless vera sul ferro, carico 0,86-1,40
# ===========================================================================
#
#   modo        T1 posto lasciato        T2 un altro entra      via
#   ---------   ----------------------   --------------------   --------------
#   congedo         5 ms                  1750 ms (1 tentativo)  congedo 0x01
#   chiusura        7 ms                  1572 ms (1 tentativo)  la conn. muore
#   sigkill     30006 · 30522 · 30004    30013 · 30520 · 31372   §2.2 / §5.3
#   sigstop     31090 · 31197 · 30009    31079 · 31185 · 31163   §5.3 / §2.2
#   vivo        ⛔ MAI in 150 s           ⛔ 95 NO su 95          —
#   vivo lungo  ⛔ MAI in **744,9 s**      ⛔ 26 NO su 26          —
#
# ⚠ Il giro lungo doveva durare 1900 s e si e' fermato a 744,9 s ⛔ **non per
#   una scadenza del prodotto**: alle 06:17:38 un altro agente ha preso la
#   porta 7801 e il mio server e' stato fermato.  ⇒ **744,9 s e' un limite
#   INFERIORE misurato**, non il tetto: il tetto vero e' l'inattivita'
#   dell'utente, 1800 s in vigore (letta dal registro d'avvio), e il suo
#   meccanismo e' provato dal controllo positivo qui sotto.  Chi rifara' questo
#   giro lo porti fino in fondo.
#
# ⛔⛔ **IL TETTO VERO E' 30 s, NON 75** — `SPECIFICHE.md` §5.3 e' onorata.  Il
#      peggiore misurato su sei distacchi cattivi e' **31,2 s** dal fatto, e
#      **31,4 s** perche' un altro client sia dentro.
#
# ⛔⛔ E LE STRADE SONO **DUE**, con lo stesso numero e nomi diversi: in 3
#      distacchi su 6 il posto l'ha lasciato l'orologio di §5.3
#      (`STACCATO per silenzio`, granularita' 1 s ⇒ 30,0-31,2 s), negli altri 3
#      la morte della connessione QUIC (`IDLE_MS 30000` in `trasporto.c` ⇒
#      30,00 s esatti).  ⚠ **Quale delle due arrivi prima e' un testa o croce**,
#      e le due lasciano righe di registro diverse e stati diversi.  ⇒ Un banco
#      che aspetti `STACCATO per silenzio` per sapere che il posto e' libero
#      **e' rosso una volta su due**, ed e' precisamente il difetto che questo
#      banco e' nato per spiegare.
#
# ⛔⛔ E IL MODO DI MORIRE NON CAMBIA NIENTE: `SIGKILL` (presa chiusa, il kernel
#      risponde ICMP «port unreachable») e `SIGSTOP` (presa aperta, buco nero)
#      danno gli stessi numeri.  ⇒ ngtcp2 non reagisce all'ICMP, e non c'e'
#      niente da guadagnare a chiudere la presa «bene».
#
# ⛔⛔⭐ MA C'E' UN CASO CHE NON FINISCE MAI IN 30 s, ED E' QUELLO CHE MORDE:
#      **il client vivo sul filo e muto su RCP**.  Il server accende dei PING
#      ogni 10 s (`webtransport.c`, `WT_TIENILA_VIVA_NS`), lo stack QUIC del
#      client risponde da solo, ogni risposta rinnova `ultima_vita`, e ⛔ **il
#      posto non si libera piu'**: 95 bussate su 95 respinte con
#      `GIA_ATTIVA_REMOTA` in 150 s.
#      ⇒ Lo libera il SECONDO orologio di §5.3, l'inattivita' dell'utente, che
#        di suo e' **30 minuti**.
#
# ⭐ IL CONTROLLO POSITIVO — e senza, i 30 s di sopra non varrebbero niente.
#    Con `accendi --inattivita-s 25` lo stesso caso `vivo` ha lasciato il posto
#    a **19 835 ms**, via `CONGEDO 0x02 INATTIVITA`.  ⇒ Questo banco **sa
#    vedere** un rilascio a un'ora diversa da 30 s: i 30 s non sono un suo
#    artefatto, e il «mai» del caso `vivo` non e' cecita'.
#
# ===========================================================================
# ⭐⭐⭐ LA RIGA PER CHI SCRIVE BANCHI
# ===========================================================================
#
#   ⛔ **Dopo che un client se n'e' andato male, prima di 35 secondi non
#      riprovare** — a meno che tu non abbia visto la sua presa chiudersi
#      davvero.  ⚠ E «male» vuol dire «senza `CONGEDO`»: 31,2 s misurati nel
#      caso peggiore, arrotondati in su perche' l'orologio di §5.3 ha una
#      granularita' di 1 s e la macchina e' condivisa.
#
#   ⛔⛔ **E se il processo del client e' ancora vivo, 35 s non bastano: il
#        posto resta occupato fino a 30 MINUTI.**  Non si conta sui 30 s
#        finche' non si e' visto morire il processo — `pgrep`, non `pkill`.
#
#   ⭐ **E la strada che non aspetta**: rispetto ai due tetti, **riaccendere il
#      SERVER libera tutti i posti nell'istante stesso**, perche' i posti
#      stanno nella memoria del processo che serve (`rcp.c`, `posti[]`), e
#      ⛔ **non costa una partenza a freddo**: la sessione grafica vive fuori
#      dal server e sopravvive.  `[M]` dopo `terreno accendi`, il primo attacco
#      e' arrivato a `SESSIONE` in **1,03 s** — cioe' il solo secondo fisso di
#      §4.4-bis.  ⇒ Un banco che ha un server suo **non deve aspettare niente**:
#      lo riaccende.
#      ⚠ E si dichiara che cosa NON dice quel numero: `SESSIONE` in 1,03 s vuol
#        dire «posto preso e messaggio spedito», ⛔ non «i pixel ci sono».  Il
#        registro dello stesso istante dice *«il palco per la tela 1280x800 non
#        c'e' ANCORA»*: il figlio nasce e aggancia dopo.  Chi misura i
#        fotogrammi aspetti il primo fotogramma, non `SESSIONE`.
#
#   ⭐ E se il client e' tuo, **fallo congedare**: `CONGEDO 0x01` libera il
#      posto in **5-7 ms**.
#
# ===========================================================================
# ⛔⛔ CHE COSA QUESTO BANCO **NON** HA MISURATO, E VA DETTO PRIMA DEL RESTO
# ===========================================================================
#
#  1. ⛔ **Nessun browser.**  La scena che ha morso davvero — *«ammazzando
#     Firefox il posto restava occupato»* — e' riprodotta **sul filo**, con un
#     client di prova, non con Firefox.  ⚠ Quel che questo banco puo' dire e'
#     che, se il processo del browser muore davvero (presa chiusa), il posto si
#     libera in 30 s; e che, se resta vivo, non si libera.  ⛔ **Quanto ci
#     metta Firefox a chiudere davvero la presa quando lo si ammazza, qui non
#     e' misurato** — ed e' il pezzo che manca per spiegare il «~75 s» del
#     documento.  L'ipotesi che questo banco lascia in eredita': **~45 s del
#     browser che non muore subito + i 30 s del prodotto**.  Chi ha il browser
#     lo misuri: `pkill -9 firefox` e poi `ss -unp | grep <porta>`.
#
#  2. ⚠ **Una macchina sola, zero RTT**: client e server sono tutt'e due su
#     192.168.0.2.  ⛔ Su rete vera la gara fra §5.3 e §2.2 puo' cambiare esito
#     (la regola RFC 9000 «l'idle riparte anche quando si SPEDISCE» sposta
#     `§2.2` piu' in la').  ⭐ Il campione dal vivo lo conferma dall'altra
#     parte: nel registro di `04-vero`, con un browser vero da 192.168.0.3,
#     `STACCATO per silenzio` a **30013, 30492, 30701, 30939 ms** — sempre
#     §5.3, sempre ~30 s.
#
#  3. ⚠ **Lo zero della misura e' il mio `date +%s%N`, non l'ultimo pacchetto
#     del client.**  `[M]` fino a 1,1 s di scarto fra i due (T1 31090 ms mentre
#     il server contava 30003 ms dal suo ultimo pacchetto).  ⇒ I numeri di
#     questo banco sono **larghi**, e la larghezza va nel verso giusto per una
#     regola del tipo «aspetta almeno N».
#
#  4. ⚠ **Il riscaldamento cambia la scena**: ogni caso misurato e' un
#     RIattacco su un figlio gia' vivo, mai una partenza a freddo.  E' la scena
#     dei banchi, ed e' dichiarata — non e' la scena del primo utente del
#     giorno.
#
#  5. ⛔ **Il TERZO orologio (abbandono) non e' misurato.**  Il giro A/B che
#     doveva separare «con un tasto» da «senza nessun tasto» — perche'
#     `presenza_segna()` (`main.c:508`) e' chiamata da **un posto solo**,
#     `input_al_figlio()` (`main.c:552`), ⇒ chi non tocca niente non entra in
#     `presenti[]` e l'orologio dell'abbandono non parte mai — e' stato
#     **contaminato dalla stessa collisione di porta** e i suoi numeri si
#     buttano.  ⚠ La lettura del codice resta, ⛔ ma e' una lettura, non una
#     misura: qui e' un `[?]`, e vale la pena chiuderlo perche' un desktop che
#     non scade mai costa 477 MB (§5.3) su una macchina con otto banchi.
set -uo pipefail

PORTA=${PORTA:-7801}
UTENTE=${UTENTE:-provar7}
UID_B=${UID_B:-1018}
LAVH=${LAVH:-/media/REMOTIX/tmp/06-b7}          # visto dall'host
LAVC=${LAVC:-/srv/remotix/tmp/06-b7}            # lo stesso, dal contenitore
CB=${CB:-/srv/src/06-b7-src/banchi}             # i banchi, dal contenitore
BH=${BH:-/media/REMOTIX/src/06-b7-src/banchi}   # i banchi, dall'host
PAR=$LAVC/parola
TERRENO=$BH/06-b43-terreno.sh
LOG=$LAVH/registro.log
ESITI=$LAVH/06-b43-esiti.jsonl
RESPIRO=${RESPIRO:-5}
INTERVALLO=${INTERVALLO:-0.4}   # fra due bussate della sonda
TASTO=${TASTO:-0}            # ⛔ un tasto solo: accende l'orologio dell'abbandono
SEGUI=${SEGUI:-0}            # secondi in piu' a guardare SE E QUANDO muore il figlio
TETTO=${TETTO:-200}          # per quanto si aspetta che il posto si liberi
SCENA=${SCENA:-non dichiarata}

ESITO=0
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; ESITO=1; }
dub() { printf '    \033[1;33m??\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { ko "⛔ va lanciato DA ROOT"; exit 2; }
case "$SCENA" in *"'"*) ko "⛔ apostrofo nella scena"; exit 2 ;; esac

carico() { uptime | sed 's/.*average: //'; }

# ⛔ Il registro timbra `HH:MM:SS.mmm` con l'orologio della macchina, lo stesso
#    di `date +%s%N`: si converte QUI, sulla macchina, e nessun tempo
#    attraversa la rete.
riga_ns() {
	local riga=$1 oggi hhmmss ms
	hhmmss=$(printf '%s' "$riga" | cut -c1-8)
	ms=$(printf '%s' "$riga" | cut -c10-12)
	oggi=$(date +%Y-%m-%d)
	printf '%s' "$(( $(date -d "$oggi $hhmmss" +%s) * 1000000000 + 10#$ms * 1000000 ))"
}

righe_nuove() { tail -n "+$1" "$LOG" 2>/dev/null; }

# ── il riscaldamento: il PRIMO attacco fa nascere la sessione grafica ───────
riscalda() {
	log "Riscaldamento — ⛔ i suoi numeri si BUTTANO"
	rm -f "$LAVH/warm-diario.txt" "$LAVH/warm-occupante.json"
	bash /media/REMOTIX/enter.sh --root \
		"python3 $CB/06-b43-occupante.py --porta $PORTA --utente $UTENTE \
		 --parola-file $PAR --uscita congedo --tieni 3 --etichetta warm \
		 --lavoro $LAVC --scena 'riscaldamento' > $LAVC/warm.log 2>&1"
	if grep -q ATTACCATO "$LAVH/warm-diario.txt" 2>/dev/null; then
		ok "il palco c'e': $(grep ATTACCATO "$LAVH/warm-diario.txt")"
	else
		ko "⛔ IL BANCO, NON IL PRODOTTO: il riscaldamento non si e' attaccato"
		tail -12 "$LAVH/warm.log" 2>/dev/null | sed 's/^/        /'
		return 9
	fi
	# ⚠ E si aspetta che il posto torni libero prima di cominciare: un caso
	#   che partisse su un posto ancora occupato misurerebbe il congedo di
	#   prima.
	sleep 3
	return 0
}

# giro <etichetta> <modo>
giro() {
	local et=$1 modo=$2
	local uscita tieni
	case "$modo" in
	congedo)  uscita=congedo;  tieni=$RESPIRO ;;
	chiusura) uscita=chiusura; tieni=$RESPIRO ;;
	*)        uscita=resta;    tieni=$((TETTO + 120)) ;;
	esac

	log "CASO «$modo» — etichetta $et"
	inf "carico prima: $(carico)"
	local MARCA
	MARCA=$(( $(wc -l < "$LOG" 2>/dev/null || echo 0) + 1 ))
	rm -f "$LAVH/$et-diario.txt" "$LAVH/$et-occupante.json" \
	      "$LAVH/$et-sonda.json" "$LAVH/$et-sonda.jsonl"

	# ── l'occupante, in secondo piano ──────────────────────────────────────
	bash /media/REMOTIX/enter.sh --root \
		"python3 $CB/06-b43-occupante.py --porta $PORTA --utente $UTENTE \
		 --parola-file $PAR --uscita $uscita --tieni $tieni --etichetta $et \
		 --un-tasto $TASTO \
		 --lavoro $LAVC --scena '$SCENA / $modo' > $LAVC/$et.log 2>&1" &
	local guscio=$!

	local g=0
	while [ $g -lt 240 ]; do
		grep -q ATTACCATO "$LAVH/$et-diario.txt" 2>/dev/null && break
		grep -q 'NON_ATTACCATO\|ROSSO\|ECCEZIONE' "$LAVH/$et-diario.txt" 2>/dev/null && break
		sleep 0.5; g=$((g+1))
	done
	if ! grep -q ATTACCATO "$LAVH/$et-diario.txt" 2>/dev/null; then
		ko "⛔ IL BANCO, NON IL PRODOTTO: «$et» non si e' attaccato in $((g/2)) s"
		tail -12 "$LAVH/$et.log" 2>/dev/null | sed 's/^/        /'
		kill "$guscio" 2>/dev/null
		return 9
	fi
	local ATT_NS PID STATO
	ATT_NS=$(awk '/ATTACCATO/{print $1; exit}' "$LAVH/$et-diario.txt")
	PID=$(awk '/AVVIO/{for(i=1;i<=NF;i++) if($i ~ /^pid=/){sub("pid=","",$i); print $i; exit}}' \
	      "$LAVH/$et-diario.txt")
	STATO=$(awk '/ATTACCATO/{for(i=1;i<=NF;i++) if($i ~ /^stato=/){sub("stato=","",$i); print $i; exit}}' \
	      "$LAVH/$et-diario.txt")
	ok "attaccato (pid $PID, SESSIONE stato=$STATO — 1=NUOVA 2=RIPRESA)"
	local FIGLIO_PRIMA
	FIGLIO_PRIMA=$(bash "$TERRENO" figlio | awk '/^FIGLIO/{print $2}')
	inf "figlio prima: $FIGLIO_PRIMA"

	# ── ⛔ il respiro, e il rifiuto se e' troppo lungo ─────────────────────
	sleep "$RESPIRO"
	local T0 SCARTO
	case "$modo" in
	congedo|chiusura)
		g=0
		while [ $g -lt 120 ]; do
			grep -q 'PARTO_' "$LAVH/$et-diario.txt" 2>/dev/null && break
			sleep 0.25; g=$((g+1))
		done
		T0=$(awk '/PARTO_/{print $1; exit}' "$LAVH/$et-diario.txt")
		;;
	sigkill)
		T0=$(date +%s%N); kill -9 "$PID" 2>/dev/null
		inf "⛔ SIGKILL a $PID: la presa si chiude, il kernel rispondera' ICMP" ;;
	sigstop)
		T0=$(date +%s%N); kill -STOP "$PID" 2>/dev/null
		inf "⛔ SIGSTOP a $PID: la presa resta aperta e nessuno risponde piu'" ;;
	vivo)
		T0=$(date +%s%N)
		inf "⛔ nessuno lo tocca: vivo sul filo, muto su RCP" ;;
	esac
	if [ -z "${T0:-}" ]; then
		ko "⛔ IL BANCO: non ho l'istante della partenza"; kill "$guscio" 2>/dev/null; return 9
	fi
	SCARTO=$(( (T0 - ATT_NS) / 1000000 ))
	inf "fra ATTACCATO e la partenza: $SCARTO ms"
	if [ "$SCARTO" -gt 20000 ]; then
		ko "⛔ IL BANCO, NON IL PRODOTTO: sono passati $SCARTO ms > 20000 —"
		ko "   §5.3 puo' aver gia' lasciato il posto da solo (trappola 1)"
		kill "$guscio" 2>/dev/null; return 9
	fi

	# ── la sonda, subito, in secondo piano ─────────────────────────────────
	bash /media/REMOTIX/enter.sh --root \
		"python3 $CB/06-b43-sonda.py --porta $PORTA --utente $UTENTE \
		 --parola-file $PAR --tetto $TETTO --intervallo $INTERVALLO --da-quando $T0 \
		 --etichetta $et --lavoro $LAVC --scena '$SCENA / $modo' \
		 > $LAVC/$et-sonda.log 2>&1" &
	local sonda=$!

	# ── T1: il registro, e T3: il figlio ───────────────────────────────────
	#
	# ⛔⛔ E SI GUARDA IL **POSTO**, NON LA RIGA CHE CI ASPETTAVAMO — e questa
	#     e' la cura del primo giro di questo banco, `[M]` 22 agosto 2026.
	#
	#     La prima stesura cercava solo `STACCATO per silenzio`, cioe' la riga
	#     dell'orologio di §5.3.  ⛔ Quella riga **non arriva mai**: a lasciare
	#     il posto e' la morte della connessione QUIC (`trasporto.c`,
	#     `IDLE_MS 30000`), che scatta un pelo prima.  ⇒ Il banco vedeva un
	#     posto liberarsi e riportava «T1: niente», cioe' accusava se stesso di
	#     non aver misurato mentre la misura era li'.
	#
	# ⭐ Adesso il fatto misurato e' **`posto LASCIATO … occupati adesso: 0`**,
	#    che e' quel che conta per chi aspetta il posto, e ACCANTO si scrive
	#    **da quale strada** e' arrivato — perche' le due strade hanno lo stesso
	#    numero e ragioni diverse, e confonderle e' come non aver misurato.
	local T1_NS="" T1_MS="" DENTRO_MS="" RCP_MS="" T3_MS="" FIG_VIVO=1 VIA=""
	g=0
	while [ $g -lt $((TETTO * 2)) ]; do
		if [ -z "$T1_NS" ]; then
			local r
			r=$(righe_nuove "$MARCA" | grep -m1 'posto LASCIATO')
			if [ -n "$r" ]; then
				T1_NS=$(riga_ns "$r")
				T1_MS=$(( (T1_NS - T0) / 1000000 ))
				local rs
				rs=$(righe_nuove "$MARCA" | grep -m1 'STACCATO per silenzio')
				if [ -n "$rs" ]; then
					VIA="§5.3 (STACCATO per silenzio)"
					DENTRO_MS=$(printf '%s' "$rs" | sed -n 's/.*STACCATO per silenzio: \([0-9]*\) ms.*/\1/p')
					RCP_MS=$(printf '%s' "$rs" | sed -n 's/.*ultimo byte di RCP e. di \([0-9]*\) ms.*/\1/p')
				elif righe_nuove "$MARCA" | grep -q 'trenta secondi di silenzio, staccato'; then
					VIA="§2.2 (idle di QUIC: la CONNESSIONE muore)"
				elif righe_nuove "$MARCA" | grep -q 'CONGEDO 0x02\|motivo 0x02\|INATTIVITA'; then
					VIA="§5.3 (inattivita' dell'utente: CONGEDO 0x02)"
				elif righe_nuove "$MARCA" | grep -q 'congedo\|CONGEDO'; then
					VIA="congedo del client (0x01)"
				elif righe_nuove "$MARCA" | grep -q 'chiusa (ne restano'; then
					VIA="la connessione QUIC chiusa dal client"
				else
					VIA="ignota"
				fi
				ok "T1 · posto lasciato dopo ${T1_MS} ms — via $VIA${DENTRO_MS:+ (il server dice: $DENTRO_MS ms senza un PACCHETTO, $RCP_MS ms senza un byte di RCP)}"
			fi
		fi
		if [ "$FIG_VIVO" = 1 ] && [ -n "$FIGLIO_PRIMA" ] && [ "$FIGLIO_PRIMA" != "nessuno" ]; then
			if [ ! -d "/proc/$FIGLIO_PRIMA" ]; then
				FIG_VIVO=0
				T3_MS=$(( ($(date +%s%N) - T0) / 1000000 ))
				inf "T3 · il figlio $FIGLIO_PRIMA e' morto dopo ~${T3_MS} ms"
			fi
		fi
		[ -s "$LAVH/$et-sonda.json" ] && break
		sleep 0.5; g=$((g+1))
	done
	wait "$sonda" 2>/dev/null

	# ── ⛔ E SI CONTINUA A GUARDARE IL FIGLIO — la domanda 2 del mandato ────
	#
	# T1 e T2 finiscono a ~30 s; il TERZO orologio di §5.3 — l'abbandono —
	# scade molto dopo.  ⛔ Smettere di guardare quando la sonda e' entrata
	# vorrebbe dire scrivere «il figlio non e' morto» dopo averlo guardato per
	# trenta secondi, che non e' una misura: e' un'attesa troppo corta
	# travestita da risultato.
	if [ "$SEGUI" -gt 0 ] && [ -n "$FIGLIO_PRIMA" ] && [ "$FIGLIO_PRIMA" != "nessuno" ]; then
		inf "guardo il figlio $FIGLIO_PRIMA per altri $SEGUI s"
		g=0
		while [ $g -lt $((SEGUI * 2)) ] && [ "$FIG_VIVO" = 1 ]; do
			if [ ! -d "/proc/$FIGLIO_PRIMA" ]; then
				FIG_VIVO=0
				T3_MS=$(( ($(date +%s%N) - T0) / 1000000 ))
				ok "T3 · il figlio $FIGLIO_PRIMA e' morto dopo ${T3_MS} ms"
			fi
			sleep 0.5; g=$((g+1))
		done
		[ "$FIG_VIVO" = 1 ] && dub "T3 · il figlio $FIGLIO_PRIMA e' ANCORA VIVO dopo $SEGUI s in piu'"
	fi

	# ── si rimette in piedi quel che si e' rotto ───────────────────────────
	case "$modo" in
	sigstop) kill -CONT "$PID" 2>/dev/null; sleep 0.2; kill -9 "$PID" 2>/dev/null ;;
	vivo)    kill -9 "$PID" 2>/dev/null ;;
	esac
	kill "$guscio" 2>/dev/null
	wait "$guscio" 2>/dev/null

	# ── T2, dalla sonda ────────────────────────────────────────────────────
	local T2_MS="" T2_NO="" T2_FORK="" T2_STATO=""
	if [ -s "$LAVH/$et-sonda.json" ]; then
		T2_MS=$(python3 -c "import json,sys;d=json.load(open('$LAVH/$et-sonda.json'));print(d.get('entrato_ms') or '')")
		T2_NO=$(python3 -c "import json,sys;d=json.load(open('$LAVH/$et-sonda.json'));print(d.get('ultimo_respinto_ms') or '')")
		T2_FORK=$(python3 -c "import json,sys;d=json.load(open('$LAVH/$et-sonda.json'));print(d.get('incertezza_ms') or '')")
		T2_STATO=$(python3 -c "import json,sys;d=json.load(open('$LAVH/$et-sonda.json'));print(d.get('stato_sessione') or '')")
	fi
	if [ -n "$T2_MS" ]; then
		ok "T2 · un ALTRO client e' entrato dopo ${T2_MS} ms (ultimo NO a ${T2_NO} ms, forchetta ${T2_FORK} ms, SESSIONE stato=$T2_STATO)"
	else
		ko "T2 · nessun altro client e' riuscito a entrare in $TETTO s"
	fi
	local FIGLIO_DOPO
	FIGLIO_DOPO=$(bash "$TERRENO" figlio | awk '/^FIGLIO/{print $2}')
	if [ "$FIGLIO_DOPO" = "$FIGLIO_PRIMA" ]; then
		ok "T3 · il figlio $FIGLIO_PRIMA e' LO STESSO: la sessione grafica e' sopravvissuta (I4)"
	else
		dub "T3 · il figlio e' cambiato: $FIGLIO_PRIMA → $FIGLIO_DOPO"
	fi

	python3 - "$ESITI" <<FINE
import json, sys
r = {"banco": "06-b43", "etichetta": "$et", "modo": "$modo",
     "scena": "$SCENA", "carico": "$(carico)".strip(),
     "attaccato_ns": int("$ATT_NS"), "partenza_ns": int("$T0"),
     "respiro_ms": int("$SCARTO"),
     "T1_posto_ms": ${T1_MS:-None},
     "T1_via": "$VIA",
     "T1_dentro_ms": ${DENTRO_MS:-None},
     "T1_ultimo_byte_rcp_ms": ${RCP_MS:-None},
     "T2_sessione_nuova_ms": ${T2_MS:-None},
     "T2_ultimo_no_ms": ${T2_NO:-None},
     "T2_forchetta_ms": ${T2_FORK:-None},
     "T2_stato_sessione": ${T2_STATO:-None},
     "T3_figlio_morto_ms": ${T3_MS:-None},
     "figlio_prima": "$FIGLIO_PRIMA", "figlio_dopo": "$FIGLIO_DOPO"}
open(sys.argv[1], "a").write(json.dumps(r, ensure_ascii=False) + "\n")
FINE
	inf "carico dopo: $(carico)"
	sleep 3
	return 0
}

case "${1:-}" in
congedo|chiusura|sigkill|sigstop|vivo)
	riscalda || exit 9
	giro "${ET:-c-$1}" "$1" ;;
tutti)
	riscalda || exit 9
	for m in congedo chiusura sigkill sigstop vivo; do giro "${ET:-c}-$m" "$m"; done ;;
tabella)
	python3 - "$ESITI" <<'FINE'
import json, sys
righe = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
print(f"{'modo':10} {'T1 posto':>10} {'T2 nuova':>10} {'ultimo NO':>10} "
      f"{'forch.':>8} {'stato':>6} {'T3 figlio':>10}  via / carico")
for r in righe:
    print(f"{r['modo']:10} {str(r['T1_posto_ms']):>10} "
          f"{str(r['T2_sessione_nuova_ms']):>10} {str(r['T2_ultimo_no_ms']):>10} "
          f"{str(r['T2_forchetta_ms']):>8} "
          f"{str(r['T2_stato_sessione']):>6} {str(r['T3_figlio_morto_ms']):>10}  "
          f"{r.get('T1_via','')} · {r['carico']}")
FINE
	exit 0 ;;
*)
	sed -n '3,10p' "$0"; exit 2 ;;
esac

exit $ESITO
