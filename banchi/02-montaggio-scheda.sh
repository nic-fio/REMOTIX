#!/bin/bash
#
# 02-montaggio-scheda.sh — ⭐⭐ IL METRO DELLA FASE, GUARDATO DAL LATO
# DELL'UTENTE: **il desktop dentro una scheda del browser**.
#
#   bash banchi/02-montaggio-scheda.sh            un giro su Chrome
#   SCHERMO=:0 SCHERMO_VERO=1 bash …              sullo schermo VERO
#
# ⚠ GIRA SU CHUWI, dove stanno i browser; il prodotto sta su NIC-OS, porta
#   **7561** (quella del montaggio).  ⭐ Ed e' la posizione giusta: il prodotto
#   ha il browser su una macchina e il server su un'altra, e una misura fatta
#   tutta dentro il server non proverebbe la parte di rete.
#
# ===========================================================================
# ⛔ CHE COSA PRODUCE, E CHE COSA NON DIMOSTRA
#
# Produce **una fotografia dello schermo finto** dopo che la pagina si e'
# collegata, piu' i pixel della tela ritagliati da li'.  ⇒ E' la risposta alla
# domanda dell'invariante **I8** — *il metro e' quel che l'utente vede* — e
# **non** e' il metro a due piani di F2.6.
#
# ⛔ La differenza va detta, perche' confonderle sarebbe la forma piu' cara:
#
#   · il metro di F2.6 confronta i pixel della TELA riletti con `getImageData`
#     contro il fotogramma catturato, e pretende PSNR-Y ≥ 45 dB.  Quella
#     rilettura la puo' fare **solo la pagina**, dall'interno;
#   · qui i pixel arrivano da una FOTOGRAFIA della finestra: ci passano in
#     mezzo il ridimensionamento della tela nella pagina, la decorazione del
#     browser e la profondita' dello schermo finto.  ⇒ Un PSNR calcolato di
#     qui misura anche quelli, e ⛔ **non e' il numero di F2.6**.
#
# ⇒ Quel che questo file dimostra e' esattamente una cosa, ed e' quella che
#   `FASI.md` §02-primo-fotogramma mette come metro della fase: **che
#   l'immagine del desktop compaia dentro la scheda**.
#
# ===========================================================================
# ⛔ LA SCENA SI DICHIARA — `CODER.md` §3.2
#
# Schermo **finto** Xvfb (predefinito `:78`), mai quello dell'utente.  ⚠ E il
# prezzo si dichiara: su Xvfb non c'e' GPU, quindi su Linux Chrome **non ha un
# decodificatore HEVC** (`[M]` F2.5) e la pagina negoziera' **AV1** — che e'
# il ripiego previsto da `DECISIONI.md` §1.13, non un difetto.
#
# ===========================================================================
# ⛔ LA PAROLA D'ORDINE NON PASSA DALL'`argv` — difetto D12.
#    `xdotool type --file`, come in `01-p5-lancia.sh`: un `ps` durante il giro
#    non la vede.  Qui e' quella pubblica dei banchi, e la regola vale lo
#    stesso: una disciplina che si applica solo quando conviene non e' una
#    disciplina.
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7561}
SCHERMO=${SCHERMO:-:78}
# ⛔⭐ LA TELA DELLO SCHERMO FINTO DEV'ESSERE ≥ 1920×1080, E NON E' UN
#     CAPRICCIO — `[M]` 12 agosto 2026, primo giro con la scheda.
#
#     `src/pagina.html` riga 1390 dichiara `video.misura_massima` come
#     `screen.width × devicePixelRatio`, e §4.5 permette al server di RIDURRE
#     la tela per starci dentro.  ⛔ Su uno schermo finto 1600×1000 il server
#     concede **1600×900**, il fotogramma in deposito e' 1920×1080, e
#     `video_forse()` rifiuta di spedirlo — giustamente: l'intestazione di
#     §6.2 direbbe una misura e i pixel ne porterebbero un'altra.
#
# ⇒ Lo schermo finto si dichiara **piu' grande della tela**, o la fase 2 non
#   ha niente da mostrare.  ⚠ E questo NON e' un difetto del prodotto: e' la
#   `[?]` che il montaggio lascia aperta — un solo fotogramma, a una sola
#   misura, contro una tela che si negozia per sessione.
TELA=${TELA:-2048x1280}
UTENTE=${UTENTE:-prova}
PAROLA=${PAROLA:-parola-di-prova}
ATTESA=${ATTESA:-25}
# ⚠ Dove stanno i due campi sulla tela dichiarata (`[M]`, letti in
#   `02-montaggio-copie/2-pagina.png`).  Si dichiarano invece di indovinarli.
X_UTENTE=${X_UTENTE:-$(( ${TELA%x*} / 2 ))}; Y_UTENTE=${Y_UTENTE:-208}
X_PAROLA=${X_PAROLA:-$(( ${TELA%x*} / 2 ))}; Y_PAROLA=${Y_PAROLA:-280}
COPIE=${COPIE:-$QUI/02-montaggio-copie}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

T=$(mktemp -d)
XVFB=""
BROWSER=""
ripulisci() {
	[ -n "$BROWSER" ] && kill "$BROWSER" 2>/dev/null
	[ -n "$XVFB" ] && kill "$XVFB" 2>/dev/null
	rm -rf "$T"
}
trap ripulisci EXIT

X() { env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO "$@"; }

log "0. Gli attrezzi, e la scena"
for t in Xvfb xdotool xdpyinfo import google-chrome; do
	command -v "$t" >/dev/null || { ko "⛔ manca «$t»"; exit 2; }
done
ok "Xvfb · xdotool · import · google-chrome"

if [ "$SCHERMO" = ":0" ] || [ -n "${SCHERMO_VERO:-}" ]; then
	SCENA="schermo-VERO-$SCHERMO"
	inf "⚠ schermo VERO: si aprira' una finestra sulla scrivania"
	X xdpyinfo >/dev/null 2>&1 || { ko "⛔ il display $SCHERMO non risponde"; exit 2; }
else
	SCENA="xvfb-FINTO-$SCHERMO-$TELA"
	Xvfb "$SCHERMO" -screen 0 "${TELA}x24" >"$T/xvfb.log" 2>&1 &
	XVFB=$!
	for i in $(seq 40); do X xdpyinfo >/dev/null 2>&1 && break; sleep 0.25; done
	X xdpyinfo >/dev/null 2>&1 || { ko "⛔ Xvfb non risponde"; cat "$T/xvfb.log"; exit 2; }
fi
inf "scena: $SCENA"
inf "bersaglio: https://$IND:$PORTA/"
mkdir -p "$COPIE"

log "1. Il bersaglio risponde? (prima di dare la colpa al browser)"
if curl -k -s -o "$T/pagina.html" -w '%{http_code}' --max-time 10 \
        "https://$IND:$PORTA/" > "$T/codice.txt"; then
	cod=$(cat "$T/codice.txt")
	byte=$(wc -c < "$T/pagina.html")
	if [ "$cod" = "200" ]; then
		ok "GET / → $cod, $byte byte"
	else
		ko "⛔ GET / → $cod: il server c'e' ma non serve la pagina"; exit 1
	fi
else
	ko "⛔ nessuna risposta da https://$IND:$PORTA/ — non e' un difetto del browser"
	exit 1
fi

log "2. Il browser, e la scheda"
# ⛔ `thisisunsafe` e non `--ignore-certificate-errors`: quel flag toglierebbe
#    dalla misura proprio la cosa che l'utente fa la prima volta (accettare
#    l'avviso), e la fase 1 quella l'ha certificata cosi'.
mkdir -p "$T/profilo"
X google-chrome --user-data-dir="$T/profilo" --no-first-run --no-default-browser-check \
	--disable-gpu --window-size=${TELA%x*},${TELA#*x} --window-position=0,0 \
	"https://$IND:$PORTA/" >"$T/chrome.log" 2>&1 &
BROWSER=$!
sleep 6
X import -window root "$COPIE/1-avviso.png" 2>/dev/null && inf "copia: $COPIE/1-avviso.png"

# L'interstiziale di Chrome: si batte la parola magica sulla finestra.
X xdotool search --name "." windowactivate --sync 2>/dev/null | head -1 >/dev/null
X xdotool type --clearmodifiers --delay 30 "thisisunsafe" 2>/dev/null
sleep 5
X import -window root "$COPIE/2-pagina.png" 2>/dev/null && inf "copia: $COPIE/2-pagina.png"

log "3. Le credenziali — e la parola d'ordine passa da un FILE"
printf '%s' "$PAROLA" > "$T/parola"
chmod 600 "$T/parola"
# ⛔⭐ SI CLICCA SUL CAMPO, non si spera che sia gia' a fuoco — difetto del
#     banco trovato al PRIMO giro, `[M]` 12 agosto 2026.
#
#     La prima stesura batteva l'utente e poi `Tab`.  ⛔ Al momento del primo
#     `type` il fuoco non era su nessun campo: l'utente si e' perso, il `Tab`
#     ha portato il fuoco sul campo «Utente», e la PAROLA D'ORDINE e' finita
#     dentro il campo dell'utente — si legge in `2-pagina.png`.
#     ⚠ E il giro sarebbe finito con «nessun fotogramma» e la colpa sul
#       server: il rosso puntato sull'imputato sbagliato, di nuovo.
#
# ⚠ Le coordinate sono della tela dichiarata, e si vedono nella copia 2: un
#   banco che le indovinasse sarebbe muto il giorno in cui la pagina cambia —
#   qui la copia 3 lo mostra prima che il giro finisca.
X xdotool mousemove "$X_UTENTE" "$Y_UTENTE" click 1 2>/dev/null
sleep 0.4
X xdotool type --clearmodifiers --delay 40 "$UTENTE" 2>/dev/null
X xdotool mousemove "$X_PAROLA" "$Y_PAROLA" click 1 2>/dev/null
sleep 0.4
X xdotool type --clearmodifiers --delay 40 --file "$T/parola" 2>/dev/null
rm -f "$T/parola"
X import -window root "$COPIE/3-compilata.png" 2>/dev/null
X xdotool key --clearmodifiers Return 2>/dev/null

log "4. ⭐ E adesso si aspetta il fotogramma"
inf "attesa: $ATTESA s"
sleep "$ATTESA"
X import -window root "$COPIE/4-scheda.png" 2>/dev/null

if [ -f "$COPIE/4-scheda.png" ]; then
	ok "⭐ la fotografia della scheda: $COPIE/4-scheda.png"
	inf "$(identify "$COPIE/4-scheda.png" 2>/dev/null || echo '(identify non c'"'"'e')"
else
	ko "⛔ non ho potuto fotografare lo schermo"
	exit 1
fi

log "5. ⛔ E il verdetto NON lo do io: lo da' chi guarda"
inf "⚠ Una fotografia dice «c'e' un'immagine», non «e' la sua».  Il confronto"
inf "  a pixel e' di F2.6, e il metro finale e' l'utente (I8)."
inf "scena: $SCENA · bersaglio https://$IND:$PORTA/ · utente $UTENTE"
exit 0
