#!/bin/bash
#
# 06-b42-contesa.sh — ⭐⭐ LA CONTESA FRA CINQUE SESSIONI GRAFICHE, ricreata a
# comando: `gnome-shell` + PipeWire + una scena che si muove, cinque volte, e
# la sottofase 6.3 misurata in mezzo.
#
# ⛔⛔ QUESTO BANCO SPOSTA I MILLISECONDI DI TUTTA LA MACCHINA — piu' di quanto
#     li spostasse la contesa GPU di `06-b41`, perche' qui il carico non e'
#     cinque `ffmpeg`, sono cinque **desktop**.  ⇒ Ogni comando che accende un
#     contendente pretende `B42_FINESTRA=si` nell'ambiente, e senza si ferma.
#
#   bash .../06-b42-contesa.sh finestra          ⭐ quanto dura e chi disturba —
#                                                  e NON accende NIENTE
#   bash .../06-b42-contesa.sh strumenti         ⭐ i controlli positivi dei due
#                                                  attrezzi (niente sessioni)
#   sudo bash .../06-b42-contesa.sh utenti       crea provac1..provac5
#   sudo bash .../06-b42-contesa.sh misurato-su  UNA sessione: provac1 + 7811
#   sudo bash .../06-b42-contesa.sh sonda-prova  ⭐⭐ IL CONTROLLO POSITIVO DELLA
#                                                  SONDA: fermo il compositore
#                                                  300 ms e la sonda DEVE vederlo
#   sudo B42_FINESTRA=si .../06-b42-contesa.sh contendenti-su [N]
#   sudo bash .../06-b42-contesa.sh contendenti-giu
#   sudo B42_FINESTRA=si .../06-b42-contesa.sh certifica [N]
#                                                ⭐⭐ LA SCENA CONTENDE DAVVERO?
#   sudo B42_FINESTRA=si .../06-b42-contesa.sh misura [N] [giri]
#                                                la scena intera, col verdetto
#   sudo bash .../06-b42-contesa.sh stato
#   sudo bash .../06-b42-contesa.sh spegni-tutto
#   sudo bash .../06-b42-contesa.sh pulisci      ⛔ toglie i cinque utenti, e lo
#                                                  VERIFICA
#
# ===========================================================================
# ⛔ PERCHE' ESISTE — `fasi/06` §4.8, §7.1 e §5.8
# ===========================================================================
#
# Il **16 agosto 2026**, con **cinque banchi accesi**, la 6.3 misuro' **4 giri
# rotti su 18**, e `NON_ORA` con mediana **22 ms e due casi a 3 000**.  A
# macchina ferma, il 17, la stessa scena da' **0 su 18** e `NON_ORA` a **6 ms**.
# ⇒ Il verde del 17 vale **«sotto carico CPU»**, non «sotto contesa», e il 4/18
# **non e' mai stato riprodotto**.
#
# ⭐ Il 21 agosto notte una causa e' stata **ESCLUSA con la misura** (§5.8): la
#    contesa sull'**iGPU** non e'.  La scena c'era e funzionava — un
#    codificatore da solo **382 fotogrammi/s**, cinque insieme **184 ciascuno**
#    (**2,08×**) — ⛔ ma il prodotto non se n'e' accorto, perche' a 18
#    fotogrammi/s di 1280x800 chiede all'iGPU circa **un cinquantesimo** di quel
#    che chiedono cinque codificatori a 1920x1080.  ⭐ E il banco **si e'
#    rifiutato di dare il verdetto**.
#
# ⭐⭐ Dove invece il segnale c'e': la latenza «Mutter» ha **13 e 17 campioni
#     oltre il tetto** su ~57, in **tutt'e due** le meta' — un quarto delle
#     richieste al produttore senza risposta entro un secondo, ed e' la stessa
#     firma del 16 agosto.  ⇒ **L'imputato di adesso e' il COMPOSITORE: cinque
#     sessioni grafiche, non cinque codificatori.**
#
# ===========================================================================
# ⛔⛔ IL MANDATO E' AVVERSARIALE — si parte dall'ipotesi che NEMMENO QUESTA
#     contesa muova niente
# ===========================================================================
#
# Se il 4/18 non torna, la conclusione onesta e' *«nemmeno cinque sessioni
# grafiche bastano»* — la **seconda** causa esclusa — ⛔ **non** «la scena del
# 16 agosto era innocua».  Un banco che potesse solo confermare non sarebbe un
# banco.
#
# ===========================================================================
# ⛔ LA TRAPPOLA CHE QUESTO BANCO POTEVA PAGARE, E LA PAGA UNA VOLTA SOLA
# ===========================================================================
#
# ⛔⛔ **Una `gnome-shell --headless --no-x11` senza monitor virtuale e senza
#     nessuno attaccato NON COMPONE NIENTE.**  Non ha una superficie su cui
#     disegnare finche' un `RecordVirtual` non gliela crea.  ⇒ «Cinque sessioni
#     grafiche accese» sarebbero **cinque processi fermi**, `pgrep` li
#     conterebbe tutti, e la contesa sarebbe un'etichetta.
#
# ⇒ Per questo ogni contendente porta **anche un client attaccato** che
#   *guarda* (`06-b35-tela.py --giro guarda`): e' lui che accende lo screencast,
#   fa comporre Mutter, fa girare PipeWire e fa lavorare il codificatore.  E per
#   questo il verdetto pretende la **vitalita'**: i tick di CPU di ogni
#   `gnome-shell` e di ogni figlio, presi prima e dopo.  Un processo che non
#   consuma non compone.
#
# ===========================================================================
# ⛔ IL FERRO, E VA DETTO ACCANTO A OGNI NUMERO
# ===========================================================================
#
# **Intel UHD 730 integrata**, **20 core**, 31 GB.  Non una scheda potente.
#
# ⛔ INTOCCABILI: la **7700**, la **7730**, l'utente **`prova`**; la **7781** e'
#    del coordinatore.  Gli utenti `provai6` `provat6` `provap6` `prova2`
#    `provaa7` `provav7` `provar7` sono di altri agenti **che lavorano adesso**:
#    non si toccano, e questo banco si rifiuta di nominarli.
#
# ⚠ L'orologio di questa macchina e' indietro di DUE ORE rispetto al portatile.
set -uo pipefail

SANO=${SANO:-/media/REMOTIX/src/06-c-src}
LAV=${LAV:-/media/REMOTIX/tmp/06-c}
C_LAV=${C_LAV:-/srv/remotix/tmp/06-c}
C_SANO=${C_SANO:-/srv/src/06-c-src}
ENTER=${ENTER:-/media/REMOTIX/enter.sh}
T="$SANO/banchi/06-b42-terreno.sh"

# I miei cinque, e nessun altro.  provac1 e' quello MISURATO; 2..5 contendono.
UTENTI=(provac1 provac2 provac3 provac4 provac5)
UIDS=(1030 1031 1032 1033 1034)
PORTE=(7811 7812 7813 7814 7815)

MARCA_CLIENT=06-b42-contendente        # ⛔ la marca che rende `pkill` sicuro
CODA_CONTENDENTE=${CODA_CONTENDENTE:-1800}

# ⭐⭐ QUANTO PESA UN CONTENDENTE — e il numero e' MISURATO, non scelto a occhio.
#
# `[M]` 22 agosto 2026, un contendente con **una** finestra e la tela a
# 1280x800: `gnome-shell` **8,8 %** di un core, il figlio di remotix **30 %**,
# il terminale **4,7 %** — in tutto ~44 % di un core.  ⛔ Quattro cosi' su una
# macchina da **20 core** fanno **0,35 core di compositore**: non contenderebbero
# niente, e il banco lo direbbe rifiutando il verdetto.
#
# ⇒ Un contendente porta **tre** finestre che si muovono e una tela **1920x1080**.
#   ⚠ E si DICHIARA: e' un banco piu' grasso del minimo, scelto per dare alla
#     contesa una possibilita'.  ⛔ La sessione MISURATA **non si tocca**: resta
#     una finestra a 1280x800, perche' e' la scena della 6.3 e cambiarla
#     renderebbe il conto non confrontabile col 4/18 del 16 agosto.
FINESTRE_CONT=${FINESTRE_CONT:-3}
LARG_CONT=${LARG_CONT:-1920}
ALT_CONT=${ALT_CONT:-1080}
SCENA_DICH=${SCENA_DICH:-"gnome-terminal che scrive lora ogni 50 ms, GNOME headless senza --virtual-monitor"}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ⛔ NIENTE APOSTROFI nella scena dichiarata: si infila dentro `--scena '...'` e
#    un apostrofo chiude gli apici — il comando diventa rotto e `enter.sh` esce
#    **senza eseguire niente**, in 350 ms.  Il banco conterebbe zero su un
#    registro in cui nessuno ha scritto.  (Difetto gia' pagato dal 6.3, il 16
#    agosto 2026.)
case "$SCENA_DICH" in
*\'*) ko "⛔ SCENA_DICH contiene un apostrofo: il comando si romperebbe in silenzio"
      exit 2 ;;
esac

banco()  { local i=$1; shift
	UTENTE=${UTENTI[$i]} UID_B=${UIDS[$i]} PORTA=${PORTE[$i]} \
		LAV="$LAV/c$((i + 1))" bash "$T" "$@"; }

carico_stampa() {
	printf 'CARICO %s · ORA %s · remotix %s · gnome-shell %s · client-contendenti %s\n' \
		"$(uptime | sed 's/.*load average: //')" \
		"$(date +%H:%M:%S)" \
		"$(pgrep -c -x remotix; :)" \
		"$(pgrep -c -x gnome-shell; :)" \
		"$(quanti_client)"
}

# ⛔⛔ SI CONTANO SOLO I `python3`, NON TUTTO QUEL CHE PORTA LA MARCA.
#     `enter.sh` non fa `exec`: un solo client lascia in giro **cinque**
#     processi con la stessa riga di comando —
#     `bash enter.sh` → `sudo` → `chroot` → `bash -lc` → `python3`.
#     ⇒ `pgrep -fc` avrebbe contato **cinque contendenti dove ce n'era uno**, e
#       il controllo «ne sono partiti N su N» sarebbe passato **anche con un
#       solo client acceso**: un verde per costruzione dentro la guardia che
#       esiste apposta per impedirlo.
quanti_client() {
	local n=0 p
	for p in $(pgrep -f -- "$MARCA_CLIENT" 2>/dev/null); do
		case "$(cat "/proc/$p/comm" 2>/dev/null)" in
		python3*) n=$((n + 1)) ;;
		esac
	done
	printf '%s' "$n"
}

finestra_o_niente() {
	if [ "${B42_FINESTRA:-no}" != "si" ]; then
		ko "⛔ QUESTA SCENA ACCENDE CINQUE DESKTOP: sposta i millisecondi di"
		ko "   TUTTI gli altri banchi sulla macchina.  Serve la finestra del"
		ko "   coordinatore.  Poi:"
		ko "       sudo B42_FINESTRA=si bash $0 $*"
		exit 9
	fi
}

# ⛔ La parola d'ordine non passa MAI da `argv` (D12): file 0600, e il
#    proprietario e' l'utente del CONTENITORE (uid 1000), che e' chi legge.
parola_per() {
	# ⛔ Due righe, non una: `local i=$1 d="...$i..."` espande TUTTI gli
	#    argomenti prima di eseguire il builtin, quindi `$i` sarebbe ancora
	#    quello di fuori — e sotto `set -u` la shell muore.  ⚠ Difetto mio,
	#    trovato al primo giro a vuoto della certificazione.
	local i=$1
	local d="$LAV/c$((i + 1))"
	# ⛔ La cartella e' dell'utente del CONTENITORE (uid 1000): e' lui che ci
	#    scrive i JSON del giro.  Una cartella `root:root 0755` fatta da qui
	#    lascerebbe il client senza posto dove scrivere, e il banco leggerebbe
	#    «nessun file» — che non e' «nessun giro rotto».
	install -d -o 1000 -g 1000 -m 775 "$d"
	( umask 077; printf '%s\n' "${UTENTI[$i]}-2026" > "$d/parola" )
	chmod 600 "$d/parola"
	chown 1000:1000 "$d/parola"
}

# ⛔ Il client dei contendenti si spegne SEMPRE, anche se il giro muore a meta'.
spegni_client() {
	pkill -f -- "$MARCA_CLIENT" 2>/dev/null
	local g=0
	while [ "$(quanti_client)" != "0" ] && [ $g -lt 40 ]; do
		sleep 0.25; g=$((g + 1))
	done
	pkill -9 -f -- "$MARCA_CLIENT" 2>/dev/null
	sleep 0.5
}

[ "${1:-stato}" = "finestra" ] || [ "${1:-}" = "strumenti" ] || {
	[ "$(id -u)" -eq 0 ] || { ko "⛔ va lanciato DA ROOT"; exit 2; }
}
mkdir -p "$LAV/sonde"; chmod 1777 "$LAV/sonde"

case "${1:-stato}" in

finestra)
	cat <<'FINE'

⭐ LA FINESTRA CHE SERVE — e questo comando non accende NIENTE

    che cosa accende      5 sessioni GNOME headless (provac1..provac5), ognuna
                          con PipeWire, un server remotix (7811-7815) e finestre
                          che scrivono lora ogni 50 ms.
                            · la sessione MISURATA: 1 finestra, tela 1280x800 —
                              e' la scena della 6.3, e non si tocca;
                            · le 4 CONTENDENTI: 3 finestre, tela 1920x1080, e
                              un client attaccato che GUARDA.
                          ⛔ Senza quel client una sessione headless non compone
                            niente: sarebbe un processo fermo con un nome grosso.
                          ⚠ E il peso e' MISURATO: `[M]` un contendente magro
                            (1 finestra, 1280x800) fa lavorare gnome-shell
                            all'8,8 % di un core — su 20 core non contenderebbe
                            niente, e il banco rifiuterebbe il verdetto.

    che cosa NON tocca    la 7700, la 7730, l'utente `prova`, la 7781 del
                          coordinatore, e i sette utenti degli altri agenti.

    chi disturba          ⛔ TUTTI, e piu' della finestra GPU del 21 agosto: il
                          carico qui non e' cinque `ffmpeg`, sono cinque
                          DESKTOP — 20 core, ma anche migliaia di risvegli al
                          secondo e cinque cicli di composizione.  Ogni misura
                          di tempo presa da un altro banco mentre questo gira e'
                          un numero falso.

    durata, a spanne      utenti + 5 sessioni + 5 server            ~6 min
                          controllo positivo della sonda            ~1 min
                          certificazione della scena (2 sonde)      ~4 min
                          18 giri incatenati SOTTO contesa          ~5 min
                          18 giri incatenati A RIPOSO (stessa ora)  ~5 min
                          spegnimento, vitalita', verdetto          ~3 min
                          ------------------------------------------------
                          ⇒ **una finestra di 30 minuti**, e va bene anche
                            spezzata: la parte che disturba davvero sono i
                            ~15 minuti fra `contendenti-su` e `contendenti-giu`.

    ⚠ E se serve accorciare: `misura 5 10` fa 10 giri per meta' invece di 18,
      ⛔ ma il 4/18 del 16 agosto e' su DICIOTTO, e un denominatore diverso non
        si confronta con quello.  ⇒ 18, o si dichiara che non e' lo stesso conto.

FINE
	exit 0 ;;

strumenti)
	# ⭐ I controlli positivi dei DUE attrezzi, prima di credere a qualunque
	#    numero.  ⛔ Non tocca ne' sessioni ne' server: gira ovunque, e proprio
	#    per questo si puo' rifare prima di ogni giro.
	log "⭐ I CONTROLLI POSITIVI DEGLI ATTREZZI (LEZIONI.md §1.2, §1.9)"
	python3 "$SANO/banchi/06-b42-sonda-compositore.py" --controllo || exit $?
	printf '\n'
	python3 "$SANO/banchi/06-b42-verdetto.py" --controllo || exit $?
	exit 0 ;;

utenti)
	log "I cinque utenti del banco — ⛔ tutti NUOVI, nessuno di un altro agente"
	for i in 0 1 2 3 4; do
		banco "$i" utente || exit $?
	done
	ok "provac1..provac5 pronti (uid 1030-1034, porte 7811-7815)"
	exit 0 ;;

misurato-su)
	# ⚠ UNA sola sessione: e' quel che questo banco puo' accendere SENZA la
	#   finestra, ed e' il carico di un agente qualunque fra i dieci.
	log "La sessione MISURATA — ${UTENTI[0]}, porta ${PORTE[0]}"
	banco 0 utente   || exit $?
	banco 0 sessione || exit $?
	banco 0 scena    || exit $?
	banco 0 spegni   > /dev/null 2>&1
	banco 0 accendi  || exit $?
	carico_stampa
	exit 0 ;;

misurato-giu)
	banco 0 spegni
	banco 0 scena-via
	exit 0 ;;

sonda-prova)
	# ⭐⭐ IL CONTROLLO POSITIVO DELLA **SONDA**, e non e' lo stesso di
	#     `--controllo`: quello prova che sa contare, questo prova che sta
	#     guardando **il compositore**.
	#
	#     ⛔ Il metro: si ferma `gnome-shell` con SIGSTOP per 300 ms.  Se la
	#     sonda NON registra un campione da almeno 250 ms, non sta misurando il
	#     ciclo principale di Mutter — sta misurando qualcos'altro, e ogni
	#     «dilatazione» che dichiarera' poi sara' di un'altra cosa.
	#     ⚠ Il fermo dura 300 ms su una sessione mia e usa e getta.
	log "⭐⭐ La sonda vede il compositore?  (SIGSTOP 300 ms a gnome-shell)"
	S=$(pgrep -u "${UIDS[0]}" -x gnome-shell | head -1)
	[ -n "$S" ] || { ko "⛔ nessun gnome-shell di ${UTENTI[0]}: fai «misurato-su»"; exit 3; }
	inf "gnome-shell di ${UTENTI[0]}: pid $S"
	U="$LAV/sonde/prova-fermo.json"
	rm -f "$U"
	( sleep 2; kill -STOP "$S"; sleep 0.3; kill -CONT "$S" ) &
	FERMO=$!
	banco 0 sonda --campioni 250 --passo 0.02 --uscita "$U" --etichetta fermo
	u=$?
	wait "$FERMO" 2>/dev/null
	# ⛔ E si RIMETTE IN MOTO comunque: un compositore lasciato in STOP e' una
	#    sessione morta che sembra viva.
	kill -CONT "$S" 2>/dev/null
	[ "$u" -eq 0 ] || { ko "⛔ la sonda e' uscita con $u"; exit "$u"; }
	python3 - "$U" <<-'PY'
	import json, sys
	d = json.load(open(sys.argv[1]))
	p = d["magra"]["peggiore_ms"]
	print(f"\n    peggiore campione: {p:.1f} ms  (il fermo era 300 ms)")
	if p >= 250:
	    print("    \033[1;32mOK\033[0m  ⭐ LA SONDA VEDE IL COMPOSITORE: il fermo"
	          " di 300 ms e' nei campioni.")
	    sys.exit(0)
	print("    \033[1;31mNO\033[0m  ⛔ LA SONDA NON HA VISTO UN FERMO DI 300 ms.")
	print("        ⇒ Non sta misurando il ciclo principale di Mutter, e ogni")
	print("          «dilatazione» che dichiarerebbe poi sarebbe di un'altra cosa.")
	sys.exit(4)
	PY
	exit $? ;;

# ---------------------------------------------------------------------------
contendenti-su)
	finestra_o_niente contendenti-su "${2:-4}"
	N=${2:-4}
	log "⛔ Accendo $N SESSIONI DI CONTESA — la macchina rallenta per TUTTI"
	carico_stampa
	for i in $(seq 1 "$N"); do
		banco "$i" utente   || exit $?
		banco "$i" sessione || exit $?
		banco "$i" scena "$FINESTRE_CONT" || exit $?
		banco "$i" spegni   > /dev/null 2>&1
		banco "$i" accendi  || exit $?
		parola_per "$i"
		# ⭐⭐ IL CLIENT CHE GUARDA — senza di lui la sessione non compone
		#     niente (vedi il riquadro in testa).  ⛔ E la redirezione sta
		#     DENTRO il comando passato a `enter.sh`, non attorno: attorno si
		#     mangerebbe la richiesta di `sudo` e il comando resterebbe appeso
		#     per sempre, in silenzio (trappola 8 del §0-bis).
		nohup bash "$ENTER" \
			"python3 $C_SANO/banchi/06-b35-tela.py --porta ${PORTE[$i]} \
			 --utente ${UTENTI[$i]} --parola-file $C_LAV/c$((i + 1))/parola \
			 --lavoro $C_LAV/c$((i + 1)) --giro guarda \
			 --larghezza $LARG_CONT --altezza $ALT_CONT \
			 --coda $CODA_CONTENDENTE --ping-ogni 3 \
			 --etichetta $MARCA_CLIENT-$i --scena '$SCENA_DICH' \
			 > $C_LAV/c$((i + 1))/client.txt 2>&1" \
			>> "$LAV/c$((i + 1))/enter.txt" 2>&1 &
		inf "contendente $i acceso (${UTENTI[$i]} / ${PORTE[$i]})"
	done
	# ⛔ Si aspetta che i client SIANO ARRIVATI A SESSIONE, e si verifica: un
	#    client che non si attacca lascia la sessione ferma, e la contesa
	#    sarebbe di N-1.
	inf "aspetto che i $N client si attacchino..."
	g=0
	while [ $g -lt 90 ]; do
		v=$(quanti_client)
		[ "$v" -ge "$N" ] && break
		sleep 1; g=$((g + 1))
	done
	v=$(quanti_client)
	if [ "$v" -lt "$N" ] 2>/dev/null; then
		ko "⛔ solo $v client su $N: la contesa NON e' quella dichiarata"
		for i in $(seq 1 "$N"); do
			printf '        c%s: ' "$((i + 1))"
			tail -3 "$LAV/c$((i + 1))/client.txt" 2>/dev/null | tr '\n' ' '
			printf '\n'
		done
		exit 3
	fi
	ok "$v client attaccati"
	sleep 8      # ⚠ il regime, non l'avvio: si lascia salire lo screencast
	carico_stampa
	exit 0 ;;

contendenti-giu)
	log "Spengo le sessioni di contesa — e lo VERIFICO, non lo spero"
	spegni_client
	rc=0
	for i in 1 2 3 4; do
		banco "$i" spegni   > /dev/null 2>&1
		# ⛔ E la scena si spegne DAVVERO: una scena sopravvissuta al «riposo»
		#    renderebbe le due meta' meno diverse di quanto dicono, cioe'
		#    abbasserebbe la dilatazione — nella direzione che rassicura.
		# ⛔ Niente pipe qui: `cmd | sed` restituisce lo stato di **sed**, e
		#    l'errore di `banco` sparirebbe.  Si cattura, poi si stampa.
		u=$(banco "$i" scena-via 2>&1) || rc=1
		printf '%s\n' "$u" | sed 's/^/    /'
	done
	[ "$rc" -eq 0 ] || { ko "⛔ una scena di contesa NON si e' spenta"; exit 3; }
	v=$(quanti_client)
	if [ "$v" = "0" ]; then ok "zero client di contesa rimasti"
	else ko "⛔ ne restano $v: ogni misura presa adesso da chiunque e' falsa"; exit 3; fi
	# ⚠ Le sessioni GNOME restano in piedi ma senza nessuno attaccato non
	#   compongono: e' il punto della trappola in testa.  ⛔ Per il giro «a
	#   riposo» questo BASTA, e si dichiara — non e' «macchina ferma».
	inf "⚠ le 4 sessioni GNOME restano vive ma SENZA nessuno attaccato:"
	inf "  non compongono piu'.  Non e' «macchina ferma»: e' «senza contesa»."
	carico_stampa
	exit 0 ;;

vitalita)
	# ⭐ I tick di CPU dei contendenti — la PROVA che hanno composto.
	#    `vitalita <file-da>` scrive lo scatto iniziale;
	#    `vitalita <file-da> <file-a>` scrive il confronto per il verdetto.
	DA=${2:-}
	A=${3:-}
	[ -n "$DA" ] || { ko "⛔ serve il file"; exit 2; }
	if [ -z "$A" ]; then
		{ for i in 1 2 3 4; do banco "$i" cpu; done; } > "$DA"
		ok "scatto iniziale in $DA"
		exit 0
	fi
	{ for i in 1 2 3 4; do banco "$i" cpu; done; } > "$LAV/vitalita-fine.txt"
	python3 - "$DA" "$LAV/vitalita-fine.txt" "$A" <<-'PY'
	import json, sys
	def leggi(p):
	    blocchi, cur = [], {}
	    for r in open(p):
	        if not r.strip():
	            continue
	        k, _, v = r.strip().partition(' ')
	        if k == 'UTENTE' and cur:
	            blocchi.append(cur); cur = {}
	        cur[k] = v
	    if cur:
	        blocchi.append(cur)
	    return {b['UTENTE']: b for b in blocchi}
	a, b = leggi(sys.argv[1]), leggi(sys.argv[2])
	hz = float(next(iter(b.values()))['HZ']) if b else 100.0
	out = {'sessioni': []}
	for u in sorted(b):
	    if u not in a:
	        continue
	    dt = (int(b[u]['ORA_NS']) - int(a[u]['ORA_NS'])) / 1e9
	    if dt <= 0:
	        continue
	    def q(k):
	        return (int(b[u][k]) - int(a[u][k])) / hz / dt
	    # ⛔ Se il pid e' cambiato, il conto dei tick NON e' una differenza:
	    #    il processo e' un altro, e i suoi tick partono da zero.  ⚠ Si
	    #    dichiara invece di calcolare un numero che sembra buono.
	    cambiato = (a[u]['SHELL_PID'] != b[u]['SHELL_PID']
	                or a[u]['FIGLIO_PID'] != b[u]['FIGLIO_PID'])
	    out['sessioni'].append({
	        'utente': u, 'finestra_s': round(dt, 1),
	        'quota_shell': round(q('SHELL_TICK'), 4) if not cambiato else 0.0,
	        'quota_figlio': round(q('FIGLIO_TICK'), 4) if not cambiato else 0.0,
	        'quota_terminale': round(q('TERMINALE_TICK'), 4) if not cambiato else 0.0,
	        'pid_cambiato': cambiato,
	    })
	json.dump(out, open(sys.argv[3], 'w'), indent=1)
	for s in out['sessioni']:
	    nota = '  ⛔ PID CAMBIATO: il processo e un altro' if s['pid_cambiato'] else ''
	    print(f"    {s['utente']}: shell {s['quota_shell']*100:6.1f} %"
	          f" · figlio {s['quota_figlio']*100:6.1f} %"
	          f" · terminale {s['quota_terminale']*100:6.1f} %"
	          f"  (su {s['finestra_s']} s){nota}")
	PY
	exit $? ;;

certifica)
	# ⭐⭐ IL CONTROLLO POSITIVO DELLA SCENA — `LEZIONI.md` §1.2 e §1.9.
	#     ⛔ Prima di credere a un verdetto preso «sotto contesa di
	#     compositori» si dimostra, con un numero preso FUORI dal prodotto, che
	#     il compositore rallenta davvero.  Se non rallenta, tutto quel che
	#     segue e' un'etichetta.
	#
	# ⛔ E la sonda si prende con la sessione misurata NELLO STESSO STATO delle
	#    due meta': con un client attaccato che guarda.  Una sonda presa su una
	#    sessione a vuoto certificherebbe una scena diversa da quella misurata.
	finestra_o_niente certifica "${2:-4}"
	N=${2:-4}
	log "⭐ Il compositore rallenta davvero?  0 contendenti contro $N"

	sonda_con_client() {   # $1 = etichetta
		local et=$1
		parola_per 0
		# ⛔⛔ `--coda 95` E NON DI PIU', PERCHE' IL CLIENT DEVE FINIRE DA SE'.
		#     Difetto mio, trovato al primo giro a vuoto: uccidevo il client
		#     della prima meta' con `pkill`, e la connessione moriva **senza
		#     chiudersi**.  `SPECIFICHE.md` §5.3 tiene allora il posto per
		#     trenta secondi ⇒ il client della SECONDA meta' si prendeva
		#     `CONGEDO 0x0f GIA_ATTIVA_REMOTA` e non misurava niente.
		#     ⚠ Si e' visto solo perche' la guardia «il client e' vivo?»
		#       c'era: senza, la sonda avrebbe misurato un compositore FERMO e
		#       il numero sarebbe uscito bellissimo — piu' basso del vero.
		# ⇒ 12 s di regime + 60 s di sonda + margine = 95, e poi si ASPETTA.
		nohup bash "$ENTER" \
			"python3 $C_SANO/banchi/06-b35-tela.py --porta ${PORTE[0]} \
			 --utente ${UTENTI[0]} --parola-file $C_LAV/c1/parola \
			 --lavoro $C_LAV/c1 --giro guarda --coda 95 --ping-ogni 3 \
			 --etichetta 06-b42-sonda-cliente --scena '$SCENA_DICH' \
			 > $C_LAV/c1/sonda-cliente.txt 2>&1" \
			>> "$LAV/c1/enter.txt" 2>&1 &
		sleep 12      # ⚠ il regime: la stretta di mano e i primi fotogrammi
		if ! pgrep -f 06-b42-sonda-cliente >/dev/null 2>&1; then
			ko "⛔ il client della sonda non e' vivo: la sessione misurata NON"
			ko "   sta componendo, e la sonda leggerebbe un compositore fermo"
			tail -6 "$LAV/c1/sonda-cliente.txt" 2>/dev/null | sed 's/^/        /'
			return 3
		fi
		# ⚠ 1 200 campioni a 50 ms = **60 s**.  ⛔ Non meno: la firma che si
		#   cerca e' una CODA (il p95 e il peggiore), e una coda su 400
		#   campioni presi in 8 s e' un aneddoto, non una distribuzione.
		banco 0 sonda --campioni 1200 --passo 0.05 \
			--uscita "$LAV/sonde/$et.json" --etichetta "$et"
		local u=$?
		# ⛔ E si verifica che il client fosse vivo ANCHE ALLA FINE: se e'
		#    caduto a meta', meta' sonda ha guardato un compositore fermo.
		if ! pgrep -f 06-b42-sonda-cliente >/dev/null 2>&1; then
			ko "⛔ il client della sonda e' morto PRIMA della fine: meta' della"
			ko "   sonda ha guardato un compositore che non componeva"
			tail -6 "$LAV/c1/sonda-cliente.txt" 2>/dev/null | sed 's/^/        /'
			return 4
		fi
		inf "aspetto che il client della sonda si chiuda DA SE' (posto libero)"
		local g=0
		while pgrep -f 06-b42-sonda-cliente >/dev/null 2>&1 && [ $g -lt 120 ]; do
			sleep 1; g=$((g + 1))
		done
		if pgrep -f 06-b42-sonda-cliente >/dev/null 2>&1; then
			ko "⚠ non si e' chiuso in $g s: lo uccido e aspetto i 30 s di §5.3"
			pkill -f 06-b42-sonda-cliente 2>/dev/null
			sleep 35
		fi
		return $u
	}

	# ⛔ Ordine: prima SENZA, poi CON.  Se si facesse il contrario, il «senza»
	#    cadrebbe dopo lo spegnimento dei contendenti, con le cache calde e la
	#    macchina che si sta ancora sistemando.
	if [ "$(quanti_client)" != "0" ]; then
		ko "⛔ ci sono gia' $(quanti_client) contendenti accesi: il «senza»"
		ko '   non sarebbe un «senza».  ⇒ «contendenti-giu» prima.'
		exit 3
	fi
	carico_stampa
	sonda_con_client solo || exit $?
	B42_FINESTRA=si bash "$0" contendenti-su "$N" || exit $?
	carico_stampa
	sonda_con_client contesa || exit $?
	carico_stampa

	python3 - "$LAV/sonde/solo.json" "$LAV/sonde/contesa.json" \
		"$LAV/06-b42-certificato.json" <<-'PY'
	import json, sys
	solo = json.load(open(sys.argv[1]))['magra']
	cont = json.load(open(sys.argv[2]))['magra']
	# ⛔ LE SOGLIE SI DICHIARANO PRIMA, e sono LARGHE apposta: servono a
	#    smascherare una contesa ASSENTE, non a misurarne la grandezza.
	#    ⚠ Due criteri, e basta UNO — perche' la firma del 16 agosto e' una
	#      CODA (due casi a 3 000 ms con la mediana a 22), non uno spostamento
	#      del centro.  Un banco che guardasse solo la mediana non la vedrebbe.
	MIN_P95, MIN_MED = 1.50, 1.25
	rp = cont['p95_ms'] / solo['p95_ms'] if solo['p95_ms'] else 0
	rm = cont['mediana_ms'] / solo['mediana_ms'] if solo['mediana_ms'] else 0
	print(f"\n    ciclo principale di Mutter, {solo['n']} + {cont['n']} campioni:")
	print(f"        senza contendenti   mediana {solo['mediana_ms']:7.2f} ms"
	      f" · p95 {solo['p95_ms']:8.2f} · peggiore {solo['peggiore_ms']:8.2f}"
	      f" · oltre 50 ms {solo['oltre_50ms']}")
	print(f"        con contendenti     mediana {cont['mediana_ms']:7.2f} ms"
	      f" · p95 {cont['p95_ms']:8.2f} · peggiore {cont['peggiore_ms']:8.2f}"
	      f" · oltre 50 ms {cont['oltre_50ms']}")
	print(f"        ⇒ mediana {rm:.2f}×  ·  p95 {rp:.2f}×"
	      f"   (soglie dichiarate: mediana {MIN_MED}× oppure p95 {MIN_P95}×)")
	esito = rp >= MIN_P95 or rm >= MIN_MED
	quale = ('p95' if rp >= MIN_P95 else 'mediana') if esito else '-'
	motivo = (f"ciclo di Mutter: mediana {rm:.2f}×, p95 {rp:.2f}×"
	          f" — passa per «{quale}»" if esito else
	          f"ciclo di Mutter fermo: mediana {rm:.2f}×, p95 {rp:.2f}×,"
	          f" sotto le soglie dichiarate")
	json.dump({'certificata': esito, 'motivo': motivo,
	           'rapporto_mediana': round(rm, 3), 'rapporto_p95': round(rp, 3),
	           'solo': solo, 'contesa': cont,
	           'ferro': 'Intel UHD 730 integrata, 20 core'},
	          open(sys.argv[3], 'w'), indent=1)
	if esito:
	    print("\n    \033[1;32mOK\033[0m  ⭐ SCENA CERTIFICATA: " + motivo)
	    sys.exit(0)
	print("\n    \033[1;31mNO\033[0m  ⛔ SCENA NON CERTIFICATA: " + motivo)
	print("        ⇒ Cinque sessioni grafiche NON rallentano il compositore di")
	print("          questa macchina (20 core).  Qualunque verdetto preso adesso")
	print("          con l'etichetta «sotto contesa» sarebbe un verde per")
	print("          costruzione — ed e' peggio di nessun caso.")
	sys.exit(4)
	PY
	u=$?
	# ⛔⛔ DIFETTO MIO, TROVATO USANDOLO: quando la certificazione FALLISCE i
	#     contendenti restavano accesi.  ⚠ Il 22 agosto sono rimasti su per
	#     **sei minuti** dopo un `certifica` fallito, e in quei sei minuti ogni
	#     millisecondo misurato da chiunque altro sulla macchina era falso —
	#     senza che nessuno lo sapesse.  ⇒ Chi accende carico lo spegne anche
	#     quando la sua misura non riesce: e' la disciplina della finestra, e
	#     vale **soprattutto** sul cammino dell'errore.
	#     ⚠ Se invece PASSA, restano su apposta: e' `misura` che li usa subito
	#       dopo, e spegnerli per riaccenderli cambierebbe la scena a meta'.
	if [ "$u" -ne 0 ]; then
		ko "⛔ certificazione fallita ⇒ spengo i contendenti, non li lascio a"
		ko "   falsare i millisecondi degli altri nove agenti"
		bash "$0" contendenti-giu
	fi
	exit "$u" ;;

misura)
	# La scena intera.  ⛔ Ordine: certifica → contesa → riposo, e i due giri
	#    nella STESSA ora, perche' il paragone regge solo cosi'.
	finestra_o_niente misura "${2:-4}" "${3:-18}"
	N=${2:-4}; GIRI=${3:-18}
	trap 'spegni_client' EXIT

	log "⭐⭐ LE RICHIESTE INCATENATE SOTTO CONTESA DI COMPOSITORI"
	inf "$N sessioni di contesa + 1 misurata · $GIRI giri per meta'"
	inf "⚠ Intel UHD 730 integrata, 20 core.  Ogni numero col carico accanto."

	# ⛔ 1 · gli attrezzi si controllano PRIMA di credergli.
	bash "$0" strumenti > "$LAV/strumenti.txt" 2>&1 || {
		ko "⛔ un attrezzo non passa il suo controllo positivo:"
		tail -20 "$LAV/strumenti.txt" | sed 's/^/        /'; exit 4; }
	ok "i due attrezzi passano il loro controllo positivo"

	# ⛔ 2 · l'utente misurato DEVE stare nel gruppo `render`, o il
	#       codificatore ripiega in software e la contesa non lo tocca.
	if id -nG "${UTENTI[0]}" 2>/dev/null | tr ' ' '\n' | grep -qx render; then
		ok "«${UTENTI[0]}» e' nel gruppo render"
	else
		ko "⛔ «${UTENTI[0]}» NON e' nel gruppo render: misurerei il ripiego"
		ko "   software (100 ms invece di 4,8).  ⇒ Non si misura."
		exit 3
	fi

	# ⛔ 3 · il terreno misurato dev'esserci: un giro contro una porta muta
	#       darebbe «zero rotti» su zero misure.
	n=$(ss -tuln 2>/dev/null | grep -c ":${PORTE[0]}\b")
	[ "${n:-0}" -ge 1 ] || { ko "⛔ nessuno ascolta sulla ${PORTE[0]}: fai «misurato-su»"; exit 3; }
	ok "il server della ${PORTE[0]} risponde ($n ascoltatori)"

	# ⛔ 4 · la sonda si controlla contro un fermo NOTO, o non si sa che cosa
	#       stia guardando.
	bash "$0" sonda-prova || { ko "⛔ la sonda non vede il compositore"; exit 4; }

	# ⛔ 5 · la scena si certifica.  `certifica` accende anche i contendenti.
	B42_FINESTRA=si bash "$0" certifica "$N" || {
		ko "⛔ scena non certificata: NON si misura"; bash "$0" contendenti-giu; exit 4; }

	# ⛔⛔ IL DIFETTO CHE `06-b41` HA GIA' COMMESSO, il 21 agosto 2026: `misura`
	#     copio' i JSON **del 16 agosto** come se fossero il giro appena fatto —
	#     sei giri nati da tre file di cinque giorni prima, con dentro un ritmo
	#     perfettamente plausibile.  ⭐ Fu visto SOLO perche' le due meta' erano
	#     identiche byte per byte.
	# ⇒ Due difese: si cancella prima, e si prende solo quel che e' PIU' NUOVO
	#   di una marca presa un istante prima.  Un file piu' vecchio non e' un
	#   giro: e' un ricordo.  ⛔ E zero giri raccolti = ci si ferma.
	raccogli() {   # $1 = prefisso · $2 = file-marca
		local pref=$1 marca=$2 r presi=0 vecchi=0 assenti=0
		for r in $(seq 1 "$GIRI"); do
			local f="$LAV/c1/06-b35-c30r$r.json"
			if [ ! -f "$f" ]; then assenti=$((assenti + 1)); continue; fi
			if [ ! "$f" -nt "$marca" ]; then vecchi=$((vecchi + 1)); continue; fi
			cp -f "$f" "$LAV/06-b42-$pref-r$r.json"; presi=$((presi + 1))
		done
		inf "$pref: $presi giri presi · $assenti senza file · ⛔ $vecchi PIU' VECCHI della marca (scartati)"
		[ "$vecchi" -eq 0 ] || ko "⛔ $vecchi file erano di un giro precedente: NON entrano"
		if [ "$presi" -eq 0 ]; then
			ko "⛔ ZERO giri raccolti per «$pref»: il client non ha misurato niente."
			ko "   ⚠ Guarda $LAV/c1/inc-*.txt — e NON e' «zero rotti»."
			return 1
		fi
		return 0
	}

	# ⛔ Il giro incatenato, 18 volte.  ⚠ La tela di PARTENZA si fissa
	#    (`--base`): il palco sopravvive al client (I4), e senza, ogni giro
	#    partirebbe dove l'ha lasciato il precedente.
	# ⛔ E LA FETTA DI REGISTRO SI PRENDE PER OGNI META', non una volta sola.
	#    La marca si riscrive a ogni giro: con una marca sola, le latenze
	#    «Mutter» in fondo sarebbero quelle della **seconda** meta' con
	#    l'etichetta di tutte e due — cioe' il numero che interessa (la firma
	#    del 16 agosto sotto contesa) sarebbe proprio quello perduto.
	incatenate() {
		local et=$1 r
		parola_per 0
		banco 0 registro-da > /dev/null
		for r in $(seq 1 "$GIRI"); do
			bash "$ENTER" \
				"python3 $C_SANO/banchi/06-b35-tela.py --porta ${PORTE[0]} \
				 --utente ${UTENTI[0]} --parola-file $C_LAV/c1/parola \
				 --lavoro $C_LAV/c1 --giro incatenate --etichetta c30r$r \
				 --base 1280x800 --intervallo 30 --coda 6 \
				 --scena '$SCENA_DICH' > $C_LAV/c1/inc-30-$r.txt 2>&1" \
				>> "$LAV/c1/enter.txt" 2>&1
			printf '.'
		done
		printf '\n'
		local M B
		M=$(cat "$LAV/c1/registro.marca" 2>/dev/null); [ -n "$M" ] || M=0
		B=$(stat -c %s "$LAV/c1/registro.log" 2>/dev/null); [ -n "$B" ] || B=0
		if [ "$M" -gt "$B" ]; then
			ko "⛔ MARCA SCADUTA per «$et»: il registro e' stato azzerato dopo"
			ko "   la marca ⇒ le latenze sarebbero uno ZERO PER COSTRUZIONE"
			return 3
		fi
		tail -c "+$((M + 1))" "$LAV/c1/registro.log" > "$LAV/giro-$et.log" 2>/dev/null
		inf "fetta di registro «$et»: $(stat -c %s "$LAV/giro-$et.log") byte"
		return 0
	}

	# 6 · i giri SOTTO contesa
	log "I $GIRI giri SOTTO contesa ($N sessioni che compongono)"
	rm -f "$LAV/c1"/06-b35-c30r*.json "$LAV"/06-b42-contesa-r*.json
	touch "$LAV/06-b42-marca-contesa"
	bash "$0" vitalita "$LAV/vitalita-da.txt" || exit $?
	carico_stampa
	incatenate contesa || exit $?
	carico_stampa
	bash "$0" vitalita "$LAV/vitalita-da.txt" "$LAV/06-b42-vitalita.json" || exit $?
	raccogli contesa "$LAV/06-b42-marca-contesa" || { bash "$0" contendenti-giu; exit 4; }
	# ⛔ E si verifica che i contendenti fossero vivi ALLA FINE, non solo
	#    all'inizio: se sono morti a meta' giro, meta' misura e' «a riposo» con
	#    l'etichetta «sotto contesa».
	VIVI=$(quanti_client)
	if [ "$VIVI" != "$N" ]; then
		ko "⛔ a fine giro erano vivi $VIVI client su $N: la contesa NON e'"
		ko "   durata tutta la misura, e l'etichetta sarebbe falsa"
		bash "$0" contendenti-giu
		exit 4
	fi
	ok "i $N client di contesa erano ancora vivi a fine giro"
	bash "$0" contendenti-giu || exit $?

	# 7 · gli stessi giri SENZA contesa, nella stessa ora — e' il paragone
	log "Gli stessi $GIRI giri SENZA contesa (stessa ora, stesso albero)"
	rm -f "$LAV/c1"/06-b35-c30r*.json "$LAV"/06-b42-riposo-r*.json
	touch "$LAV/06-b42-marca-riposo"
	carico_stampa
	incatenate riposo || exit $?
	carico_stampa
	raccogli riposo "$LAV/06-b42-marca-riposo" || exit 4

	# ⭐ LE LATENZE DAL REGISTRO — la firma «Mutter» del 16 agosto: mediana
	#    22 ms e due casi a 3 000, contro 6 ms a macchina ferma.  ⚠ E' quel che
	#    §5.8 ha visto muoversi anche quando il verdetto non si muoveva: qui si
	#    guarda **meta' per meta'**, non tutto insieme.
	for m in contesa riposo; do
		log "LE LATENZE DAL REGISTRO — meta' «$m»"
		python3 "$SANO/banchi/06-b35-tempi.py" "$LAV/giro-$m.log" --dettaglio \
			| tail -45
	done

	log "IL VERDETTO"
	python3 "$SANO/banchi/06-b42-verdetto.py" "$LAV" --giri "$GIRI" \
		--certificato "$LAV/06-b42-certificato.json" \
		--vitalita "$LAV/06-b42-vitalita.json"
	exit $? ;;

stato)
	log "Stato dei cinque banchi"
	carico_stampa
	for i in 0 1 2 3 4; do
		printf '  · %s (uid %s, porta %s): utente %s · gnome-shell %s · porta %s\n' \
			"${UTENTI[$i]}" "${UIDS[$i]}" "${PORTE[$i]}" \
			"$(id -u "${UTENTI[$i]}" 2>/dev/null || echo 'NO')" \
			"$(pgrep -c -u "${UIDS[$i]}" -x gnome-shell 2>/dev/null; :)" \
			"$(ss -tuln 2>/dev/null | grep -c ":${PORTE[$i]}\b")"
	done
	exit 0 ;;

spegni-tutto)
	log "Spengo tutto quel che e' MIO — le sessioni restano, gli utenti anche"
	spegni_client
	for i in 0 1 2 3 4; do
		banco "$i" spegni    > /dev/null 2>&1
		banco "$i" scena-via > /dev/null 2>&1
	done
	carico_stampa
	exit 0 ;;

pulisci)
	# ⛔ E si VERIFICA che i cinque se ne siano andati: «ho lanciato userdel»
	#    non e' «l'utente non c'e' piu'», e lasciare cinque sessioni accese
	#    falserebbe i millisecondi di tutti gli altri per giorni.
	log "⛔ Tolgo i cinque utenti e le loro sessioni"
	spegni_client
	rc=0
	for i in 0 1 2 3 4; do
		banco "$i" pulisci || rc=1
	done
	printf '\n'
	restano=""
	for u in "${UTENTI[@]}"; do
		id "$u" >/dev/null 2>&1 && restano="$restano $u"
	done
	s=$(pgrep -x gnome-shell -u "$(IFS=,; echo "${UIDS[*]}")" 2>/dev/null | wc -l)
	printf 'UTENTI_RIMASTI %s\n' "${restano:-nessuno}"
	printf 'GNOME_SHELL_MIEI_RIMASTI %s\n' "$s"
	printf 'CLIENT_MIEI_RIMASTI %s\n' "$(quanti_client)"
	for p in "${PORTE[@]}"; do
		printf 'PORTA_%s %s\n' "$p" "$(ss -tuln 2>/dev/null | grep -c ":$p\b")"
	done
	carico_stampa
	if [ -n "$restano" ] || [ "$s" != "0" ]; then
		ko "⛔ NON e' pulito: resta$restano, e $s gnome-shell miei"
		exit 3
	fi
	ok "⭐ i cinque utenti e le loro sessioni sono SPENTI e RIMOSSI"
	exit "$rc" ;;

*)
	sed -n '3,30p' "$0"
	exit 0 ;;
esac
