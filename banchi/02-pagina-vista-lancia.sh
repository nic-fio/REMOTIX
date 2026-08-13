#!/bin/bash
#
# 02-pagina-vista-lancia.sh — ⭐⭐ IL PALCO DEL BANCO CHE MISURA **QUANTO
# GRANDE** VIENE DIPINTO IL FOTOGRAMMA.  Il giro e il verdetto stanno in
# `02-pagina-vista-prova.py`; qui c'e' solo la scena.
#
#   bash banchi/02-pagina-vista-lancia.sh                tutte le scene + i guasti
#   GIRI="vista-piu-larga" bash banchi/02-pagina-vista-lancia.sh
#   GUASTI="" bash banchi/02-pagina-vista-lancia.sh      solo le scene sane
#
#   ⭐ E CONTRO IL SERVER VERO, cioe' la pagina che la 7561 SERVE davvero:
#      URL_SANO=https://192.168.0.2:7561/ bash banchi/02-pagina-vista-lancia.sh
#
#   ⛔ Perche' e' un giro DIVERSO, e non un doppione.  Il giro normale misura la
#      pagina del DEPOSITO (`src/pagina.html`) servita da un `http.server` di
#      casa.  ⛔ Ma il processo del prodotto la pagina la legge UNA VOLTA SOLA
#      all'accensione (`src/pagina.c:590`): deposito curato e pagina servita
#      sono due fatti diversi, ed e' esattamente lo scarto che il 13 agosto ha
#      lasciato la cura scritta e fuori servizio.  ⇒ Con `URL_SANO` il banco
#      misura quel che l'utente scarica, non quel che noi abbiamo scritto.
#   ⚠ E i GUASTI restano di casa: si innestano in una COPIA servita da noi, e
#     sul server vero non si innestano — quindi con `URL_SANO` il banco gira le
#     sole scene sane, e lo dichiara invece di far credere di aver certificato.
#
# ⚠ GIRA SU CHUWI, dove stanno i browser.  ⛔ Porta di questo giro: **7591**.
#   7448, 7501 e 7561 si contano prima e dopo e NON si toccano — ⛔ la 7561 e'
#   il server che l'utente sta guardando adesso.
#
# ===========================================================================
# ⛔⭐ QUESTO BANCO NON HA BISOGNO DEL SERVER, ED E' UNA SCELTA
#
# Il difetto del 13 agosto sta fra il fotogramma DECODIFICATO e il vetro: la
# meta' di catena che comincia dove il filo finisce.  ⇒ Il banco serve la
# pagina del prodotto da un `http.server` su **127.0.0.1:7591** — che e' un
# contesto sicuro, quindi WebCodecs c'e' — e le consegna un fotogramma chiave
# vero passando dal suo `Schermo.stream_video`, cioe' dal percorso del prodotto.
#
# ⭐ Il guadagno: la scena e' RIPETIBILE.  La misura della finestra, il fattore
#    di scala e la misura del fotogramma li decide il banco, e sono le tre cose
#    che il difetto mette in relazione.  ⛔ Con un server vero la tela sarebbe
#    quella che il server concede e la finestra quella che c'e': due delle tre
#    non si potrebbero scegliere, e il caso «vista piu' grande della tela»
#    — quello in cui l'immagine va INGRANDITA — non si potrebbe apparecchiare
#    affatto.
#
# ⚠ Quel che questo banco NON prova: che il filo consegni.  Lo provano gia'
#   `02-filo-lancia.sh` e `02-pagina-misura-lancia.sh`, e duplicarlo qui
#   sarebbe misurare due volte la stessa cosa e zero volte quella nuova.
#
# ===========================================================================
# ⛔ E I DUE GUASTI SONO PARTE DEL BANCO, non un'appendice.  `CODER.md` §4.6:
#    un banco che non sappia diventare rosso non dice niente quando e' verde.
#    ⇒ Dopo le scene sane si riservono le stesse scene su una pagina guasta, e
#      il banco e' verde solo se quelle sono ROSSE.
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
RADICE=$(cd "$QUI/.." && pwd)
IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7591}
SCHERMO=${SCHERMO:-:91}
# ⛔ Lo schermo finto e' PIU' GRANDE della piu' grande delle scene: la misura
#    della finestra la decide `Emulation.setDeviceMetricsOverride` a pagina
#    viva, e uno schermo piu' piccolo la taglierebbe in silenzio.
TELA=${TELA:-2600x1500}
DIAGNOSI=${DIAGNOSI:-9591}
SORGENTE=${SORGENTE:-$RADICE/src/pagina.html}
# ⛔ Vuoto = il giro di casa.  Pieno = si misura la pagina che un server VERO
#    sta servendo in questo istante (vedi la testata).
URL_SANO=${URL_SANO:-}
GIRI=${GIRI:-vista-piu-larga vista-piu-grande vista-piu-piccola fattore-2 ridimensiona}
# ⛔ I guasti si provano sulla scena dell'utente: finestra larga, tela 16:9.
GUASTI=${GUASTI:-cornice-fissa uno-a-uno}
# ⛔⭐ E QUESTI DUE SULLA SCENA «RIDIMENSIONA», che e' l'unica in cui il blocco
#    «dopo» esiste — 13 agosto 2026.  Prima i guasti giravano SOLO su
#    `vista-piu-larga`, e le quattro pretese del ridimensionamento (fra cui
#    «ricomposizioni > prima») non erano mai state provate capaci di arrossire:
#    verdi da sempre, e nessuno sapeva se sapessero fare altro (`CODER.md`
#    §4.6, `LEZIONI.md` §2.2).
GUASTI_RIDIM=${GUASTI_RIDIM:-ridimensiona-sordo deposito-perso}
# ⛔ Contro un server vero i guasti non esistono: si innestano in una copia, e
#    la copia qui non c'e'.  Si tolgono, e si dice perche'.
[ -n "$URL_SANO" ] && { GUASTI=""; GUASTI_RIDIM=""; }
GIRO_GUASTO=${GIRO_GUASTO:-vista-piu-larga}
ESITI=${ESITI:-$QUI/02-pagina-vista-esiti.jsonl}
COPIE=${COPIE:-$QUI/02-pagina-vista-copie}

VERDE=$'\033[1;32m'; ROSSO=$'\033[1;31m'; GIALLO=$'\033[1;33m'; GRIGIO=$'\033[0m'
ok()  { printf '    %sOK%s  %s\n' "$VERDE" "$GRIGIO" "$*"; }
ko()  { printf '    %sNO%s  %s\n' "$ROSSO" "$GRIGIO" "$*"; }
dub() { printf '    %s??%s  %s\n' "$GIALLO" "$GRIGIO" "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

T=$(mktemp -d)
XVFB=""; BROWSER=""; SERVENTE=""
ripulisci() {
	# ⚠ Si aspetta che Chrome sia morto DAVVERO: un `rm` sul suo profilo
	#   mentre ancora scrive lascia una cartella non vuota e un rumore rosso
	#   in fondo a un banco verde.
	[ -n "$BROWSER" ] && { kill "$BROWSER" 2>/dev/null; wait "$BROWSER" 2>/dev/null; }
	[ -n "$XVFB" ] && kill "$XVFB" 2>/dev/null
	[ -n "$SERVENTE" ] && kill "$SERVENTE" 2>/dev/null
	rm -rf "$T"
}
trap ripulisci EXIT
X() { env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO "$@"; }

# ⛔ I server che non sono miei si contano PRIMA e DOPO.  ⚠ La 7561 e' quella
#   che l'utente sta guardando: se questo conto cambia, l'ho rotta io.
# ⛔ MAI UNA REDIREZIONE ATTORNO A `ssh` — `fasi/00-ambiente.md` B3.3, pagata
#    sei volte.  Qui di la' si legge e basta.
vicini() {
	local r=""
	for p in 7448 7501 7561; do
		r="$r$p: $(ssh -o BatchMode=yes -o ConnectTimeout=8 "nicfio@$IND" \
		           "ss -tuln | grep -c ':$p\b'" 2>/dev/null | tr -d '\r') · "
	done
	printf '%s\n' "${r%· }"
}

log "0. Gli attrezzi, la scena e i vicini"
for t in Xvfb xdpyinfo google-chrome python3 curl; do
	command -v "$t" >/dev/null || { ko "⛔ manca «$t»"; exit 2; }
done
ok "Xvfb · xdpyinfo · google-chrome · python3 · curl"
inf "vicini PRIMA (su NIC-OS) — $(vicini)"
mkdir -p "$COPIE"

if [ -n "$URL_SANO" ]; then
	# ⛔⭐ IL CONTROLLO CHE DA' SENSO A TUTTO IL GIRO, e non e' sul deposito:
	#    si SCARICA la pagina dal server e si conta li' dentro.  «La cura e'
	#    scritta» e «la cura e' in servizio» sono due fatti diversi, e il
	#    processo del prodotto legge il file una volta sola all'accensione.
	#    ⚠ Il corpo si scarica in un FILE: `curl | grep -q` chiude la
	#      conduttura al primo riscontro e `pipefail` fa fallire un controllo
	#      su una pagina che c'era.
	log "0-bis. ⭐ La pagina SERVITA da $URL_SANO — contata, non sperata"
	curl -sk --max-time 20 -o "$T/servita-vera.html" "$URL_SANO" \
		|| { ko "⛔ non ho scaricato $URL_SANO: non dico niente della sua pagina"; exit 2; }
	n=$(grep -c 'adatta_vista' "$T/servita-vera.html")
	inf "$(wc -c < "$T/servita-vera.html") byte scaricati"
	if [ "$n" -gt 0 ]; then
		ok "⭐ la pagina SERVITA porta «adatta_vista» $n volte: e' quella con la cura"
	else
		ko "⛔ la pagina SERVITA porta «adatta_vista» ZERO volte: il file sul"
		ko "   disco puo' anche essere curato — il PROCESSO sta servendo quella"
		ko "   di prima, e va riavviato"
		exit 1
	fi
	inf "⚠ e i guasti NON girano in questo modo: si innestano in una copia, e la"
	inf "   copia qui non c'e'. Chi certifica lo strumento e' il giro di casa"
else
	[ -f "$SORGENTE" ] || { ko "⛔ non trovo $SORGENTE"; exit 2; }
	# ⛔ E si guarda che sia la pagina DI OGGI: un banco che misurasse la pagina di
	#    ieri direbbe «il difetto c'e' ancora» di una cura gia' fatta.
	if grep -q 'adatta_vista' "$SORGENTE"; then
		ok '⭐ il sorgente porta «adatta_vista»: e'"'"' la pagina con la cura'
	else
		ko '⛔ il sorgente NON porta «adatta_vista»: e'"'"' la pagina di prima della cura'
		exit 1
	fi

	log "1. Le pagine servite — la sana e le guaste, in cartelle separate"
	python3 "$QUI/02-pagina-vista-prova.py" --prepara sano \
		--sorgente "$SORGENTE" --dentro "$T/sano" >/dev/null || exit 2
	ok "sana: $T/sano/index.html"
	for g in $GUASTI $GUASTI_RIDIM; do
		python3 "$QUI/02-pagina-vista-prova.py" --prepara "$g" \
			--sorgente "$SORGENTE" --dentro "$T/$g" >/dev/null || exit 2
		ok "guasta «$g»: $T/$g/index.html — l'innesto ha trovato il suo testo"
	done
fi

log "2. Xvfb e Chrome, una volta sola per tutte le scene"
# ⚠ Il browser NON si rifa' a ogni scena: qui non c'e' nessun certificato da
#   accettare e nessun posto da lasciare sul server — e rifarlo cinque volte
#   costerebbe cinque sondaggi dei codec (sei decodifiche per codec) per
#   misurare una cosa che non li riguarda.  ⛔ Ma la PAGINA si ricarica a ogni
#   scena: `Page.navigate` rifa' tutto lo stato del prodotto.
Xvfb "$SCHERMO" -screen 0 "${TELA}x24" >"$T/xvfb.log" 2>&1 &
XVFB=$!
for i in $(seq 40); do X xdpyinfo >/dev/null 2>&1 && break; sleep 0.25; done
X xdpyinfo >/dev/null 2>&1 || { ko "⛔ Xvfb non risponde"; cat "$T/xvfb.log"; exit 2; }
inf "Xvfb $SCHERMO a $TELA, pid $XVFB"

mkdir -p "$T/profilo"
# ⛔ Contro il server vero il certificato e' il suo, autofirmato: senza questo
#    Chrome si ferma sull'avviso e il banco misurerebbe la schermata d'avviso.
#    ⚠ Si accende SOLO in quel modo — nel giro di casa non c'e' nessun TLS, e
#    un interruttore acceso sempre nasconderebbe un giorno un errore vero.
CERTI=()
[ -n "$URL_SANO" ] && CERTI=(--ignore-certificate-errors)
X google-chrome --user-data-dir="$T/profilo" --no-first-run \
	--no-default-browser-check --disable-gpu "${CERTI[@]}" \
	--remote-debugging-port="$DIAGNOSI" --remote-allow-origins='*' \
	--window-size=${TELA%x*},${TELA#*x} --window-position=0,0 \
	about:blank >"$T/chrome.log" 2>&1 &
BROWSER=$!
inf "Chrome pid $BROWSER, porta di diagnosi $DIAGNOSI"

GUAI=0
FATTI=0

# ---------------------------------------------------------------------------
# ⛔⭐ UN SERVENTE SOLO, E OGNI PAGINA AL SUO PERCORSO — e questa riga e' nata da
#    un rosso del banco, `[M]` 13 agosto 2026, primo giro.
#
# Prima c'era un servente per pagina, tutti su `http://127.0.0.1:7591/`: stesso
# URL, contenuto diverso.  ⛔ E Chrome ha servito dalla propria CACHE — i due
# giri guasti hanno prodotto numeri IDENTICI a quello sano, cifra per cifra, e
# il banco ha detto «il guasto e' verde» di un guasto che non era mai arrivato
# al browser.  ⚠ E' la forma peggiore: non un rosso sbagliato, un VERDE
# sbagliato che accusa il banco invece della cache.
#
# ⇒ Adesso le pagine stanno tutte sotto la stessa radice e si distinguono per
#   PERCORSO — `/sano/`, `/cornice-fissa/`, `/uno-a-uno/` — cioe' sono URL
#   diversi e la cache non le puo' confondere.  ⛔ E la cache si spegne lo
#   stesso da CDP (`Network.setCacheDisabled`), perche' le stesse scene si
#   rigirano sullo stesso percorso: due cinture, e la seconda costa una riga.
servi() {
	python3 -m http.server "$PORTA" --bind 127.0.0.1 --directory "$T" \
		>"$T/servente.log" 2>&1 &
	SERVENTE=$!
	for i in $(seq 40); do
		curl -s -o /dev/null --max-time 2 "http://127.0.0.1:$PORTA/sano/" && return 0
		sleep 0.25
	done
	ko "⛔ il servente sulla $PORTA non risponde"; cat "$T/servente.log"; return 1
}

log "3. Le scene sane — la pagina del prodotto, cinque viste"
if [ -n "$URL_SANO" ]; then
	SANO=$URL_SANO
	inf "⭐ la pagina la serve IL PRODOTTO: $SANO"
else
	SANO="http://127.0.0.1:$PORTA/sano/"
	servi || exit 2
	inf "servito $T su http://127.0.0.1:$PORTA/ — una cartella per pagina"
fi
# ⛔ E si guarda che al percorso ci sia DAVVERO quella pagina, prima di
#    misurarla: un banco che misurasse la pagina sbagliata direbbe il contrario
#    del vero, e l'ha gia' fatto una volta oggi.
# ⚠ Il corpo si scarica in un FILE e si legge di li'.  Con `curl | grep -q` la
#   `grep` chiude la conduttura al primo riscontro, `curl` muore di SIGPIPE e
#   `pipefail` fa fallire il controllo su una pagina che c'era — `[M]` sul
#   secondo giro di stasera.
for g in sano $GUASTI $GUASTI_RIDIM; do
	if [ "$g" = sano ]; then u=$SANO; else u="http://127.0.0.1:$PORTA/$g/"; fi
	curl -sk --max-time 20 -o "$T/servita-$g.html" "$u"
	if grep -q 'REMOTIX' "$T/servita-$g.html"; then
		ok "$u risponde con la pagina ($(wc -c < "$T/servita-$g.html") byte)"
	else
		ko "⛔ $u non risponde con la pagina"; exit 2
	fi
done
PREF=${PREF:-sano}
for g in $GIRI; do
	python3 "$QUI/02-pagina-vista-prova.py" --giro "$g" --guasto sano \
		--url "$SANO" --diagnosi "$DIAGNOSI" \
		--copia "$COPIE/$PREF-$g.png" --uscita "$ESITI"
	s=$?; FATTI=$((FATTI+1))
	[ "$s" -ne 0 ] && GUAI=$((GUAI+1))
done

if [ -n "$GUASTI" ]; then
	log "4. I guasti — le stesse pretese su una pagina che sbaglia"
	for g in $GUASTI; do
		inf "la pagina guasta «$g» sta su http://127.0.0.1:$PORTA/$g/"
		python3 "$QUI/02-pagina-vista-prova.py" --giro "$GIRO_GUASTO" \
			--guasto "$g" --rosso-atteso \
			--url "http://127.0.0.1:$PORTA/$g/" --diagnosi "$DIAGNOSI" \
			--copia "$COPIE/guasto-$g.png" --uscita "$ESITI"
		s=$?; FATTI=$((FATTI+1))
		[ "$s" -ne 0 ] && GUAI=$((GUAI+1))
	done
fi

if [ -n "$GUASTI_RIDIM" ]; then
	log "4-bis. ⭐ I guasti DEL RIDIMENSIONAMENTO — le quattro pretese del blocco «dopo»"
	for g in $GUASTI_RIDIM; do
		inf "la pagina guasta «$g» sta su http://127.0.0.1:$PORTA/$g/"
		python3 "$QUI/02-pagina-vista-prova.py" --giro ridimensiona \
			--guasto "$g" --rosso-atteso \
			--url "http://127.0.0.1:$PORTA/$g/" --diagnosi "$DIAGNOSI" \
			--copia "$COPIE/guasto-$g.png" --uscita "$ESITI"
		s=$?; FATTI=$((FATTI+1))
		[ "$s" -ne 0 ] && GUAI=$((GUAI+1))
	done
fi

log "5. I vicini, contati DOPO"
inf "vicini DOPO (su NIC-OS) — $(vicini)"

printf '\n'
if [ "$GUAI" -eq 0 ]; then
	printf '    %s⭐ tutti i %s giri sono come dovevano: la pagina riscala alla%s\n' "$VERDE" "$FATTI" "$GRIGIO"
	printf '    %s   vista in tutt%se due i versi, tiene le proporzioni, segue il%s\n' "$VERDE" "'" "$GRIGIO"
	printf '    %s   ridimensionamento.%s\n' "$VERDE" "$GRIGIO"
	# ⛔ La riga dei guasti si stampa SOLO se i guasti sono girati.  ⚠ Dirla
	#    sempre sarebbe la forma peggiore: un verde che si attribuisce una
	#    certificazione che in questo giro non ha fatto.
	if [ -n "$GUASTI$GUASTI_RIDIM" ]; then
		printf '    %s   ⭐ E le %s pagine guaste sono diventate rosse.%s\n' \
			"$VERDE" "$(printf '%s\n' $GUASTI $GUASTI_RIDIM | wc -l)" "$GRIGIO"
	else
		printf '    %s   ⚠ E i guasti in questo giro NON sono girati: questo giro%s\n' "$GIALLO" "$GRIGIO"
		printf '    %s     MISURA la pagina servita, non CERTIFICA lo strumento.%s\n' "$GIALLO" "$GRIGIO"
	fi
	exit 0
fi
printf '    %s⛔ %s giri su %s non sono come dovevano.%s\n' "$ROSSO" "$GUAI" "$FATTI" "$GRIGIO"
exit 1
