#!/bin/bash
#
# 06-b41-contesa.sh — ⭐⭐ LA CONTESA SULLA GPU, ricreata a comando.
#
# ⛔⛔ QUESTO BANCO SPOSTA I MILLISECONDI DI TUTTA LA MACCHINA.  Non si lancia
#     senza la finestra del coordinatore: ogni comando che accende carico
#     pretende `B39_FINESTRA=si` nell'ambiente, e senza si ferma.
#
#   bash .../06-b41-contesa.sh finestra     ⭐ quanto dura e chi disturba — e
#                                             NON accende niente
#   sudo bash .../06-b41-contesa.sh clip    la clip cruda in /dev/shm
#   sudo B39_FINESTRA=si .../06-b41-contesa.sh certifica [N]
#                                           ⭐⭐ IL CONTROLLO POSITIVO DELLA
#                                              SCENA: la contesa c'e' davvero?
#   sudo B39_FINESTRA=si .../06-b41-contesa.sh carico [N]     accende N codificatori
#   sudo bash .../06-b41-contesa.sh scarico  li spegne tutti, e lo verifica
#   sudo bash .../06-b41-contesa.sh stato    chi tiene aperto renderD128
#   sudo B39_FINESTRA=si .../06-b41-contesa.sh misura [N] [giri]
#                                           la scena intera, col verdetto
#   sudo bash .../06-b41-contesa.sh pulisci
#
# ===========================================================================
# ⛔ PERCHE' ESISTE — `fasi/06-la-tela-e-la-vista.md` §4.8 e §7.1
# ===========================================================================
#
# Le richieste incatenate diedero **4 rotti su 18** il 16 agosto, con **cinque
# banchi e cinque codificatori sullo stesso iGPU**.  Rimisurate il 17 agosto a
# macchina ferma: **0 su 18** — ⛔ **ma il controllo positivo non ha reso**,
# perche' togliendo la cura sospetta (`rcp.c:2847`) escono **ancora 0 su 18**.
# ⇒ *Non si sa che cosa tenga quella scena.*  L'unica differenza rimasta fra
# le due occasioni e' la **contesa sulla GPU**, e finche' non si ricrea quel
# verde vale «a macchina ferma e sotto carico CPU», non «sotto contesa GPU».
#
# ⚠ E c'e' gia' un indizio, misurato il 21 agosto sul registro del 16:
#   `06-b35-tempi.py` su `06-p/registro.log` (cinque banchi accesi) da'
#   `NON_ORA` con mediana **22 ms** e **due casi a 3 000 ms** — cioe' la
#   scadenza intera di §7.1.  Sul registro del 17 (macchina ferma) `NON_ORA`
#   sta a **6 ms** e nessuno arriva alla scadenza.  ⇒ La contesa **muove
#   davvero** questa scena; resta da vedere se muove il verdetto.
#
# ===========================================================================
# ⛔ IL FERRO, E VA DETTO ACCANTO A OGNI NUMERO
# ===========================================================================
#
# **Intel UHD 730 integrata**, non una scheda potente.  Un codificatore VA-API
# da solo fa `[M]` ~300 fotogrammi/s a 1920x1080 (21 agosto 2026, misurato):
# cioe' gia' cinque volte quel che chiede il prodotto a 60/s.  ⇒ Cinque
# codificatori insieme la satura, ed e' il punto.
#
# ⛔ E IL CARICO **NON E' IL PRODOTTO**: sono `ffmpeg -c:v h264_vaapi` sullo
#    stesso `/dev/dri/renderD128`.  Questo e' voluto — la variabile che §4.8
#    isola e' *la contesa sulla GPU*, non «cinque desktop».  ⚠ Quel che questa
#    scena **non** ricrea, e va scritto: cinque compositori, cinque PipeWire e
#    cinque sessioni GNOME.  Se il verdetto non si muove, la conclusione onesta
#    e' «la GPU da sola non basta», non «la scena del 16 agosto era innocua».
#
# ===========================================================================
# ⛔ LE TRAPPOLE CHE QUESTO BANCO NON PUO' RIPAGARE
# ===========================================================================
#
# 1. ⛔⛔ **una contesa che non c'e' e' peggio di nessuna contesa**: darebbe un
#    verde con l'etichetta «sotto contesa GPU».  ⇒ `certifica` **misura** che
#    i codificatori rallentano davvero, e `misura` **si rifiuta** di dare un
#    verdetto se la certificazione non e' passata;
# 2. ⛔ **l'utente di sessione deve stare nel gruppo `render`**: senza, il
#    codificatore del prodotto ripiega in software (`[M]` 100 ms per
#    fotogramma invece di 4,8) e la «contesa GPU» che credi di misurare non
#    tocca il prodotto.  ⇒ si verifica, non si suppone;
# 3. ⛔ **il carico va spento anche se il giro si rompe a meta'**: `trap`
#    sull'uscita, e `scarico` **conta** i processi rimasti invece di sperare;
# 4. ⛔ **i processi si riconoscono da una marca propria** (`06-b41-carico`):
#    un `pkill ffmpeg` prenderebbe anche quel che stanno facendo gli altri
#    nove agenti sulla stessa macchina.
set -uo pipefail

SANO=${SANO:-/media/REMOTIX/src/06-p-src}
LAV=${LAV:-/media/REMOTIX/tmp/06-p}
PORTA=${PORTA:-7731}
UTENTE=${UTENTE:-provap6}
NODO=${NODO:-/dev/dri/renderD128}
CLIP=${CLIP:-/dev/shm/06-b41-clip.nv12}
MARCA=06-b41-carico              # ⛔ la marca che rende `pkill` sicuro
LARG=${LARG:-1920}
ALT=${ALT:-1080}
FOTO=${FOTO:-60}                 # fotogrammi nella clip
ENTER=${ENTER:-/media/REMOTIX/enter.sh}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

dentro() { printf '%s\n' "$PAROLA_SUDO" | bash "$ENTER" --root "$*"; }

carico_stampa() {
	printf 'CARICO %s · ORA %s · remotix %s · gnome-shell %s · %s aperto da %s\n' \
		"$(uptime | sed 's/.*load average: //')" \
		"$(date +%H:%M:%S)" \
		"$(pgrep -c -x remotix; :)" \
		"$(pgrep -c -x gnome-shell; :)" \
		"$NODO" \
		"$(ls -l /proc/*/fd 2>/dev/null | grep -c "$(basename "$NODO")")"
}

quanti_carichi() {
	local n
	n=$(pgrep -fc -- "$MARCA")
	case $? in 0|1) : ;; *) echo '??'; return ;; esac
	printf '%s' "${n:-0}"
}

finestra_o_niente() {
	if [ "${B39_FINESTRA:-no}" != "si" ]; then
		ko "⛔ QUESTA SCENA SPOSTA I MILLISECONDI DI TUTTI GLI ALTRI BANCHI."
		ko "   Serve la finestra del coordinatore.  Poi:"
		ko "       sudo B39_FINESTRA=si bash $0 $*"
		exit 9
	fi
}

# ⛔ Il carico si spegne SEMPRE, anche se il giro muore a meta'.
spegni_carico() {
	pkill -f -- "$MARCA" 2>/dev/null
	local g=0
	while [ "$(quanti_carichi)" != "0" ] && [ $g -lt 40 ]; do
		sleep 0.25; g=$((g + 1))
	done
	pkill -9 -f -- "$MARCA" 2>/dev/null
	sleep 0.5
}

[ "${1:-stato}" = "finestra" ] || {
	[ "$(id -u)" -eq 0 ] || { ko "⛔ va lanciato DA ROOT"; exit 2; }
}

case "${1:-stato}" in

finestra)
	cat <<'FINE'

⭐ LA FINESTRA CHE SERVE — e questo comando non accende NIENTE

    che cosa accende      5 `ffmpeg -c:v h264_vaapi` su /dev/dri/renderD128
                          + 1 sessione GNOME `provap6` + 1 server sulla 7731
    che cosa NON tocca    la 7700, la 7730 e l'utente `prova`
    chi disturba          ⛔ TUTTI: la GPU e' una sola (Intel UHD 730
                          integrata).  Ogni misura di tempo presa da un altro
                          banco mentre questo gira e' un numero falso.

    durata, a spanne      certificazione della scena      ~2 min
                          terreno (utente + sessione + server)  ~2 min
                          18 giri incatenati SOTTO contesa      ~4 min
                          18 giri incatenati SENZA contesa      ~4 min   (il
                                                     paragone nella stessa ora)
                          18 giri col guasto innestato          ~5 min
                          spegnimento e verifica                ~1 min
                          ------------------------------------------------
                          ⇒ **una finestra di 20 minuti**, e va bene anche
                            spezzata in due da 10.

    ⭐ E nella stessa finestra ci sta il secondo lavoro, che vuole lo stesso
      terreno: **rifare `06-b35-certifica.sh`** dopo i quattro rattoppi della
      revisione avversariale (il metro SANO, l'ordine marca/accensione,
      l'esito del costruttore, il controllo positivo sul registro).
      Cinque ricompilazioni e sei giri: **altri ~15 minuti**.
      ⚠ E il giro sano di quel certificatore va preso **sotto la stessa
        contesa**, o la regola di G1 non distinguera' il guasto dal carico.
      ⇒ **35 minuti in tutto**, se si fanno insieme.

FINE
	exit 0 ;;

clip)
	# ⛔ La clip sta in memoria e si legge in ciclo: se la sorgente fosse
	#    `testsrc2` dal vivo, meta' del carico sarebbe **CPU** e la contesa
	#    misurata non sarebbe quella della GPU.  ⚠ E' la differenza fra
	#    «sotto carico CPU» e «sotto contesa GPU», cioe' tutta la domanda.
	log "La clip cruda, in memoria — $LARG x $ALT, $FOTO fotogrammi nv12"
	if dentro "test -s $CLIP"; then
		ok "c'e' gia': $(dentro "stat -c %s $CLIP") byte"
		exit 0
	fi
	dentro "ffmpeg -hide_banner -loglevel error -y -f lavfi \
	        -i testsrc2=size=${LARG}x${ALT}:rate=60 -frames:v $FOTO \
	        -pix_fmt nv12 -f rawvideo $CLIP" || { ko "⛔ ffmpeg non l'ha fatta"; exit 3; }
	ok "$(dentro "stat -c %s $CLIP") byte in $CLIP"
	exit 0 ;;

stato)
	log "Chi tiene aperto $NODO, e quanto carico c'e'"
	carico_stampa
	inf "codificatori di QUESTO banco vivi: $(quanti_carichi)"
	printf '    processi con %s aperto:\n' "$NODO"
	for d in /proc/[0-9]*; do
		p=${d#/proc/}
		if ls -l "$d/fd" 2>/dev/null | grep -q "$(basename "$NODO")"; then
			printf '        %-8s %s\n' "$p" \
				"$(tr '\0' ' ' < "$d/cmdline" 2>/dev/null | cut -c1-90)"
		fi
	done
	exit 0 ;;

carico)
	finestra_o_niente carico "${2:-5}"
	N=${2:-5}
	log "Accendo $N codificatori VA-API su $NODO — ⛔ la macchina rallenta per TUTTI"
	dentro "test -s $CLIP" || { ko "⛔ manca la clip: lancia prima «clip»"; exit 3; }
	carico_stampa
	for i in $(seq 1 "$N"); do
		# `-metadata comment=$MARCA` mette la marca nella riga di comando:
		# ⛔ e' quel che rende `pkill -f` sicuro fra dieci agenti.
		dentro "nohup ffmpeg -hide_banner -loglevel error \
		        -init_hw_device vaapi=va:$NODO -filter_hw_device va \
		        -stream_loop -1 -f rawvideo -pix_fmt nv12 -s ${LARG}x${ALT} \
		        -r 60 -i $CLIP -vf hwupload -c:v h264_vaapi -b:v 8M \
		        -metadata comment=$MARCA-$i -f null - \
		        >/dev/null 2>&1 &" >/dev/null 2>&1
	done
	sleep 2
	v=$(quanti_carichi)
	if [ "$v" -lt "$N" ] 2>/dev/null; then
		ko "⛔ ne sono partiti $v su $N: la contesa NON e' quella dichiarata"
		exit 3
	fi
	ok "$v codificatori accesi"
	carico_stampa
	exit 0 ;;

scarico)
	log "Spengo il carico — e lo VERIFICO, non lo spero"
	spegni_carico
	v=$(quanti_carichi)
	if [ "$v" = "0" ]; then
		ok "zero codificatori del banco rimasti"
	else
		ko "⛔ ne restano $v: la macchina resta rallentata, e ogni misura"
		ko "   presa adesso da chiunque e' falsa"
		exit 3
	fi
	carico_stampa
	exit 0 ;;

certifica)
	# ⭐⭐ IL CONTROLLO POSITIVO DELLA SCENA — `LEZIONI.md` §1.2 e §1.9.
	#     ⛔ Prima di credere a un verdetto preso «sotto contesa GPU» si
	#     dimostra che la contesa **c'e'**.  Il metro: la GPU e' una sola,
	#     quindi N codificatori insieme devono fare **meno** fotogrammi al
	#     secondo ciascuno di uno da solo.  Se non calano, non stanno
	#     contendendo niente e tutto quel che segue e' un'etichetta falsa.
	finestra_o_niente certifica "${2:-5}"
	N=${2:-5}
	log "⭐ La contesa c'e' davvero?  1 codificatore contro $N"
	dentro "test -s $CLIP" || { ko "⛔ manca la clip: lancia prima «clip»"; exit 3; }
	trap 'spegni_carico' EXIT
	carico_stampa

	misura_fps() {   # $1 = quanti insieme · stampa i fotogrammi/s del PRIMO
		local quanti=$1 i
		for i in $(seq 2 "$quanti"); do
			dentro "nohup ffmpeg -hide_banner -loglevel error \
			        -init_hw_device vaapi=va:$NODO -filter_hw_device va \
			        -stream_loop -1 -f rawvideo -pix_fmt nv12 \
			        -s ${LARG}x${ALT} -r 60 -i $CLIP -vf hwupload \
			        -c:v h264_vaapi -b:v 8M -metadata comment=$MARCA-$i \
			        -f null - >/dev/null 2>&1 &" >/dev/null 2>&1
		done
		[ "$quanti" -gt 1 ] && sleep 2
		local t0 t1
		t0=$(date +%s%N)
		dentro "ffmpeg -hide_banner -loglevel error \
		        -init_hw_device vaapi=va:$NODO -filter_hw_device va \
		        -stream_loop 9 -f rawvideo -pix_fmt nv12 -s ${LARG}x${ALT} \
		        -r 60 -i $CLIP -vf hwupload -c:v h264_vaapi -b:v 8M \
		        -metadata comment=$MARCA-0 -f null -" >/dev/null 2>&1
		t1=$(date +%s%N)
		spegni_carico
		printf '%s' "$(( (FOTO * 10 * 1000000000) / (t1 - t0) ))"
	}

	UNO=$(misura_fps 1)
	inf "1 codificatore da solo:  $UNO fotogrammi/s   [$LARG x $ALT, H.264 VA-API, Intel UHD 730]"
	TANTI=$(misura_fps "$N")
	inf "$N codificatori insieme: $TANTI fotogrammi/s ciascuno (misurato sul primo)"
	carico_stampa

	# ⛔ La soglia si dichiara PRIMA: con la GPU condivisa fra N, il primo
	#    deve scendere sotto i 2/3 di quando era solo.  E' larga apposta —
	#    serve a smascherare una contesa **assente**, non a misurarla.
	SOGLIA=$(( UNO * 2 / 3 ))
	printf '\n'
	if [ "$TANTI" -lt "$SOGLIA" ]; then
		ok "⭐ CONTESA CERTIFICATA: $TANTI < $SOGLIA (2/3 di $UNO)"
		ok "   ⇒ i $N codificatori si contendono davvero lo stesso iGPU"
		echo "CONTESA_CERTIFICATA uno=$UNO tanti=$TANTI n=$N $(date +%s)" \
			> "$LAV/06-b41-certificato.txt"
		exit 0
	fi
	ko "⛔ CONTESA NON CERTIFICATA: $TANTI non e' sotto $SOGLIA (2/3 di $UNO)"
	ko "   ⇒ la scena NON contende la GPU.  Qualunque verdetto preso adesso"
	ko "     con l'etichetta «sotto contesa GPU» sarebbe un verde per"
	ko "     costruzione — ed e' peggio di nessun caso."
	rm -f "$LAV/06-b41-certificato.txt"
	exit 4 ;;

misura)
	# La scena intera.  ⛔ Ordine: certifica → contesa → riposo, e i due giri
	#    nella STESSA ora, perche' il paragone regge solo cosi'.
	finestra_o_niente misura "${2:-5}" "${3:-18}"
	N=${2:-5}; GIRI=${3:-18}
	trap 'spegni_carico' EXIT

	log "⭐⭐ LE RICHIESTE INCATENATE SOTTO CONTESA GPU — $N codificatori, $GIRI giri"
	inf "⚠ Intel UHD 730 integrata.  Ogni numero va letto col carico accanto."

	# ⛔ 1 · l'utente della sessione DEVE stare nel gruppo `render`, o il
	#       codificatore del prodotto ripiega in software e la contesa non lo
	#       tocca.  Trappola 5 del §0-bis, e si verifica.
	if id -nG "$UTENTE" 2>/dev/null | tr ' ' '\n' | grep -qx render; then
		ok "«$UTENTE» e' nel gruppo render"
	else
		ko "⛔ «$UTENTE» NON e' nel gruppo render: il codificatore ripieghera'"
		ko "   in software (100 ms invece di 4,8) e la contesa GPU non lo"
		ko "   toccherebbe.  ⇒ Non si misura."
		exit 3
	fi

	# ⛔ 1-bis · il terreno dev'esserci gia': questo banco NON accende sessioni
	#           ne' server, li usa.  Un giro contro una porta muta darebbe
	#           «zero rotti» su zero misure.
	n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
	if [ "${n:-0}" -lt 1 ]; then
		ko "⛔ nessuno ascolta sulla $PORTA: manca il terreno."
		ko "   ⇒ sudo bash $SANO/banchi/06-b35-lancia.sh terreno"
		exit 3
	fi
	ok "il server della $PORTA risponde ($n ascoltatori)"

	# ⛔ 2 · la scena si certifica PRIMA.  Senza il certificato, niente verdetto.
	bash "$0" clip || exit $?
	B39_FINESTRA=si bash "$0" certifica "$N" || {
		ko "⛔ scena non certificata: non si misura"; exit 4; }

	# ⛔⛔ IL DIFETTO CHE QUESTO BANCO HA GIA' COMMESSO — 21 agosto 2026, primo
	#     giro della finestra, e l'ho visto perche' le due meta' erano
	#     IDENTICHE byte per byte.
	#
	#     Il client era rotto (gli mancava una dipendenza) ed e' uscito con 1
	#     tutte e 18 le volte, in tutt'e due le meta'.  ⛔ Ma in `$LAV` c'erano
	#     ancora i `06-b35-c30r*.json` del **16 agosto**, e questo ciclo li ha
	#     copiati: `06-b41-contesa-r1..3` e `06-b41-riposo-r1..3` sono nati
	#     **dagli stessi tre file di cinque giorni prima**, con dentro un
	#     ritmo di 31,6 ms perfettamente plausibile.
	#     ⚠ Il verdetto si e' salvato per caso — le due meta' erano uguali.
	#       Se una sola delle due avesse girato, avrei confrontato numeri di
	#       adesso con numeri del 16 e non me ne sarei accorto.
	# ⇒ Due difese, e la seconda e' quella che regge:
	#    1. i file si CANCELLANO prima di ogni meta';
	#    2. si prende solo quel che e' PIU' NUOVO della marca temporale presa
	#       un istante prima della meta'.  Un file piu' vecchio non e' un
	#       giro: e' un ricordo.
	raccogli() {   # $1 = prefisso · $2 = marca (file di riferimento)
		local pref=$1 marca=$2 r presi=0 vecchi=0 assenti=0
		for r in $(seq 1 "$GIRI"); do
			local f="$LAV/06-b35-c30r$r.json"
			if [ ! -f "$f" ]; then assenti=$((assenti + 1)); continue; fi
			if [ ! "$f" -nt "$marca" ]; then vecchi=$((vecchi + 1)); continue; fi
			cp -f "$f" "$LAV/06-b41-$pref-r$r.json"; presi=$((presi + 1))
		done
		inf "$pref: $presi giri presi · $assenti senza file · ⛔ $vecchi PIU' VECCHI della marca (scartati)"
		[ "$vecchi" -eq 0 ] || ko "⛔ $vecchi file erano di un giro precedente: NON entrano nella misura"
		if [ "$presi" -eq 0 ]; then
			ko "⛔ ZERO giri raccolti per «$pref»: il client non ha misurato niente."
			ko "   ⚠ Guarda $LAV/inc-30-*.txt — e NON e' «zero rotti»."
			return 1
		fi
		return 0
	}

	# 3 · i giri SOTTO contesa
	log "I $GIRI giri SOTTO contesa"
	rm -f "$LAV"/06-b35-c30r*.json "$LAV"/06-b41-contesa-r*.json
	touch "$LAV/06-b41-marca-contesa"
	B39_FINESTRA=si bash "$0" carico "$N" || exit $?
	carico_stampa
	bash "$SANO/banchi/06-b35-lancia.sh" incatenate 30 "$GIRI"
	raccogli contesa "$LAV/06-b41-marca-contesa" || { bash "$0" scarico; exit 4; }
	carico_stampa
	# ⛔ E si verifica che i codificatori fossero vivi ALLA FINE, non solo
	#    all'inizio: se sono morti a meta' giro, meta' misura e' «a riposo»
	#    con l'etichetta «sotto contesa».
	VIVI=$(quanti_carichi)
	if [ "$VIVI" != "$N" ]; then
		ko "⛔ a fine giro erano vivi $VIVI codificatori su $N: la contesa NON"
		ko "   e' durata tutta la misura, e l'etichetta sarebbe falsa"
		bash "$0" scarico
		exit 4
	fi
	ok "i $N codificatori erano ancora vivi a fine giro"
	bash "$0" scarico || exit $?

	# 4 · gli stessi giri A RIPOSO, nella stessa ora — e' il paragone
	log "Gli stessi $GIRI giri A RIPOSO (stessa ora, stesso albero)"
	rm -f "$LAV"/06-b35-c30r*.json "$LAV"/06-b41-riposo-r*.json
	touch "$LAV/06-b41-marca-riposo"
	carico_stampa
	bash "$SANO/banchi/06-b35-lancia.sh" incatenate 30 "$GIRI"
	raccogli riposo "$LAV/06-b41-marca-riposo" || exit 4
	carico_stampa

	log "IL VERDETTO"
	python3 "$SANO/banchi/06-b41-verdetto.py" "$LAV" --giri "$GIRI"
	exit $? ;;

pulisci)
	spegni_carico
	dentro "rm -f $CLIP" >/dev/null 2>&1
	rm -f "$LAV"/06-b41-*.json "$LAV/06-b41-certificato.txt"
	ok "pulito"
	exit 0 ;;

*)
	sed -n '3,25p' "$0"
	exit 0 ;;
esac
