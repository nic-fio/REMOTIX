#!/bin/bash
#
# 02-pagina-misura-lancia.sh — ⭐⭐ LA SCENA DEL BANCO CHE PRENDE IL DIFETTO
# DELLE DUE GRANDEZZE CONFUSE.  Il giro e il verdetto stanno in
# `02-pagina-misura-prova.py`; qui c'e' solo il palco.
#
#   bash banchi/02-pagina-misura-lancia.sh              i due giri
#   TELA=1600x900 bash banchi/02-pagina-misura-lancia.sh
#   GIRI=telefono bash banchi/02-pagina-misura-lancia.sh
#
# ⚠ GIRA SU CHUWI, dove stanno i browser; il prodotto sta su NIC-OS.  ⛔ Porta
#   di questo giro: **7581**.  7448 e 7501 si contano prima e dopo e NON si
#   toccano; la 7561 e' il server che l'utente apre, e nemmeno quella.
#
# ===========================================================================
# ⛔ LA SCENA E' UNO SCHERMO PIU' CORTO DI 1080, ED E' TUTTO IL PUNTO
#
# `[M]` 13 agosto 2026, registro del server sulla 7561, sessioni dell'utente
# `nicfio` delle 05:48 e delle 05:55: il client dichiarava
# `video.misura_massima=2560x1010`, il server concedeva una tela di
# **1794x1010**, e il fotogramma catturato — 1920x1080 — non partiva.
#
# ⛔ Nessun banco l'aveva preso: le pagine di prova dichiarano `3840x2160` o
#    `2048x1280` a mano, e `02-montaggio-scheda.sh` apparecchia apposta uno
#    schermo finto piu' GRANDE della tela.  ⇒ Qui si fa il contrario: **2560x1010
#    esatti**, cioe' lo schermo su cui l'utente non ha visto niente.
#
# ===========================================================================
# ⛔ LA PAROLA D'ORDINE NON PASSA DALL'`argv` — difetto D12.  Si legge da
#    `~/SERVER.ssh`, si scrive in un file 0600, e il banco riceve **il percorso
#    del file**.  ⚠ L'utente e' `nicfio` e non `prova`: dal 12 agosto il palco
#    e' del FIGLIO, che gira come l'utente ammesso, e su questa macchina
#    l'unica sessione grafica con dentro qualcosa da catturare e' quella di
#    `nicfio` (`DECISIONI.md` §1.10-bis).
#
# ===========================================================================
# ⛔ MAI UNA REDIREZIONE ATTORNO A `ssh` — `FASI.md` §00-ambiente B3.3, pagata
#    sei volte.  Qui non serve nessun `sudo` di la': si legge e basta.
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7581}
SCHERMO=${SCHERMO:-:79}
# ⛔ 2560x1010: LA MISURA VERA dello schermo su cui l'utente non ha visto
#    niente.  Un banco che l'arrotondasse a 2560x1080 non porrebbe la domanda.
TELA=${TELA:-2560x1010}
UTENTE=${UTENTE:-nicfio}
DIAGNOSI=${DIAGNOSI:-9581}
TETTO_TELEFONO=${TETTO_TELEFONO:-1280x720}
GIRI=${GIRI:-schermo-corto telefono}
ESITI=${ESITI:-$QUI/02-pagina-misura-esiti.jsonl}
COPIE=${COPIE:-$QUI/02-pagina-misura-copie}

VERDE=$'\033[1;32m'; ROSSO=$'\033[1;31m'; GIALLO=$'\033[1;33m'; GRIGIO=$'\033[0m'
ok()  { printf '    %sOK%s  %s\n' "$VERDE" "$GRIGIO" "$*"; }
ko()  { printf '    %sNO%s  %s\n' "$ROSSO" "$GRIGIO" "$*"; }
dub() { printf '    %s??%s  %s\n' "$GIALLO" "$GRIGIO" "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

T=$(mktemp -d)
XVFB=""; BROWSER=""
ripulisci() {
	[ -n "$BROWSER" ] && kill "$BROWSER" 2>/dev/null
	[ -n "$XVFB" ] && kill "$XVFB" 2>/dev/null
	rm -rf "$T"
}
trap ripulisci EXIT
X() { env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO "$@"; }

# ⛔ I due server che non sono miei si contano PRIMA e DOPO.
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
inf "vicini PRIMA — $(vicini)"
inf "scena: xvfb-FINTO-$SCHERMO-$TELA   ·   bersaglio https://$IND:$PORTA/"
inf "⚠ schermo alto ${TELA#*x} pixel: PIU' CORTO della tela di 1080 che la pagina chiede"

log "1. Il bersaglio risponde? (prima di dare la colpa al browser)"
cod=$(curl -k -s -o "$T/pagina.html" -w '%{http_code}' --max-time 10 "https://$IND:$PORTA/")
byte=$(wc -c < "$T/pagina.html" 2>/dev/null || echo 0)
[ "$cod" = "200" ] || { ko "⛔ GET / → $cod da https://$IND:$PORTA/"; exit 1; }
ok "GET / → 200, $byte byte"
# ⛔ E si guarda che sia LA PAGINA DI OGGI: un banco che misurasse la pagina di
#    ieri direbbe «il difetto c'e' ancora» di una cura gia' fatta.
if grep -q 'SONDE_MISURA' "$T/pagina.html"; then
	ok "⭐ la pagina servita porta SONDE_MISURA: e' quella con la cura"
else
	ko "⛔ la pagina servita NON porta SONDE_MISURA: il server sta servendo"
	ko "   una pagina vecchia.  Cura: bash banchi/attrezzi-allinea-prodotto.sh allinea"
	ko "   e poi riaccendi il server della $PORTA."
	exit 1
fi

log "2. La parola d'ordine, in un file 0600 (difetto D12)"
PW=$(awk -F: '/^[Pp]ass/{print $2}' ~/SERVER.ssh | tr -d ' \r\n')
[ -n "$PW" ] || { ko "⛔ non ho letto la parola da ~/SERVER.ssh"; exit 2; }
printf '%s' "$PW" > "$T/parola"; unset PW
chmod 600 "$T/parola"
ok "scritta in $T/parola (0600) — non passa da nessun argv"

mkdir -p "$COPIE"
GUAI=0
for g in $GIRI; do
	log "3. Il giro «$g» — scena nuova, browser nuovo"
	# ⛔ Xvfb e Chrome si rifanno a ogni giro: un profilo riusato porterebbe
	#    dentro la scelta del certificato del giro prima, e il secondo giro
	#    misurerebbe una scena diversa da quella dichiarata.
	Xvfb "$SCHERMO" -screen 0 "${TELA}x24" >"$T/xvfb-$g.log" 2>&1 &
	XVFB=$!
	for i in $(seq 40); do X xdpyinfo >/dev/null 2>&1 && break; sleep 0.25; done
	X xdpyinfo >/dev/null 2>&1 || { ko "⛔ Xvfb non risponde"; cat "$T/xvfb-$g.log"; exit 2; }
	inf "Xvfb $SCHERMO a $TELA, pid $XVFB"

	mkdir -p "$T/profilo-$g"
	X google-chrome --user-data-dir="$T/profilo-$g" --no-first-run \
		--no-default-browser-check --disable-gpu \
		--remote-debugging-port="$DIAGNOSI" --remote-allow-origins='*' \
		--window-size=${TELA%x*},${TELA#*x} --window-position=0,0 \
		about:blank >"$T/chrome-$g.log" 2>&1 &
	BROWSER=$!
	inf "Chrome pid $BROWSER, porta di diagnosi $DIAGNOSI"

	TETTO=""
	[ "$g" = telefono ] && TETTO="$TETTO_TELEFONO"
	python3 "$QUI/02-pagina-misura-prova.py" --giro "$g" \
		--url "https://$IND:$PORTA/" --diagnosi "$DIAGNOSI" \
		--utente "$UTENTE" --parola-file "$T/parola" \
		--tetto "$TETTO" --uscita "$ESITI"
	s=$?
	[ "$s" -ne 0 ] && GUAI=$((GUAI+1))

	# ⭐ La fotografia si prende PRIMA di spegnere: e' quel che l'utente
	#    vedrebbe, ed e' l'unica cosa che un umano puo' controllare a mano.
	command -v import >/dev/null && X import -window root "$COPIE/$g.png" 2>/dev/null \
		&& inf "copia: $COPIE/$g.png"

	kill "$BROWSER" 2>/dev/null; BROWSER=""
	kill "$XVFB" 2>/dev/null; XVFB=""
	# ⚠ Il posto lo lascia gia' la pagina (`02-pagina-misura-prova.py` naviga
	#   via prima di staccare), e questa pausa e' la cintura: il server libera
	#   il posto quando il congedo arriva, non quando il browser muore.
	sleep 5
done

rm -f "$T/parola"
log "4. I vicini, contati DOPO"
inf "vicini DOPO — $(vicini)"

printf '\n'
if [ "$GUAI" -eq 0 ]; then
	printf '    %s⭐ i giri sono tutti verdi: la pagina del prodotto, su uno schermo%s\n' "$VERDE" "$GRIGIO"
	printf '    %s   piu%s corto di 1080, finisce con un fotogramma dipinto — e un%s\n' "$VERDE" "'" "$GRIGIO"
	printf '    %s   decodificatore che si ferma prima continua a dichiararlo.%s\n' "$VERDE" "$GRIGIO"
	exit 0
fi
printf '    %s⛔ %s giri su %s non sono verdi.%s\n' "$ROSSO" "$GUAI" "$(echo $GIRI | wc -w)" "$GRIGIO"
exit 1
