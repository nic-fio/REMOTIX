#!/bin/bash
#
# 02-giudizio-catena.sh — ⭐⭐ IL METRO DI F2.6 SULLA CATENA VERA.
#
#   bash banchi/02-giudizio-catena.sh
#   PORTA=7561 UTENTE=nicfio bash banchi/02-giudizio-catena.sh
#
# ⚠ GIRA SU CHUWI, dove stanno i browser; il prodotto sta su NIC-OS.
# ⛔ Porta di diagnosi e servente di questo giro: **7601**.  7448, 7501 e la
#   7561 — quella che l'utente guarda — si CONTANO prima e dopo.  ⚠ E la 7561
#   e' anche il BERSAGLIO: si legge, non si tocca.
#
# ===========================================================================
# ⛔⭐ CHE COSA FA, E PERCHE' NON L'AVEVA MAI FATTO NESSUNO
#
# `PIANO.md` fase 2: *«il fotogramma decodificato confrontato con quello
# catturato.  Non "il programma non e' crollato": **i pixel**»*.
# `P2-6-montaggio.md` §7 punto 1 dichiarava che cosa mancava: **il termine
# `pagina`**, che si legge solo da dentro la pagina.  §4.2 dello stesso
# rapporto aveva misurato l'altro termine — `riferimento ⟷ cattura`, 48,27 dB
# — e lo scriveva a chiare lettere: *«questo NON e' il metro intero»*.
#
# ⇒ Qui i quattro ingressi si mettono insieme per la prima volta:
#
#     cattura      il buffer BGRx che il PRODOTTO ha scritto con `--rilievo`
#     flusso       il flusso Annex-B / OBU che il PRODOTTO ha spedito
#     riferimento  lo stesso flusso decodificato da `ffmpeg` — ⭐ il SECONDO
#                  LETTORE che `PIANO.md` §0.4 dichiara mancante
#     pagina       ⭐ `getImageData` dalla tela del prodotto, in un browser vero
#                  collegato al server vero (`02-giudizio-catena.py`)
#
# ===========================================================================
# ⛔ E QUEL CHE QUESTO GIRO **NON** PUO' GIUDICARE, SCRITTO PRIMA
#
# La scena e' **il desktop dell'utente**, non la mira di F2.6.  ⇒ tre dei
# dodici guasti sono ciechi in questo giro — «piani» (M4), «otto-bit» (M7) e
# «ribaltato» (i marcatori di M-V) — e il metro lo **conta e lo stampa** invece
# di portarsi dietro la cifra 12 della certificazione, che vale sulla mira.
# La cura non e' una soglia: e' **la mira sul monitor virtuale**, che
# `P2-6` §7 punto 2 tiene aperta.
#
# ⚠ E M6 (freschezza) non esiste su un'immagine ferma: la fase 2 cattura UNA
#   volta all'accensione, quindi non c'e' nessun «giro precedente» con una
#   scena diversa.  Si dichiara con `--senza-freschezza`, non si finge.
#
# ===========================================================================
# ⛔ MAI UNA REDIREZIONE ATTORNO A `ssh` — pagata sei volte.  Si passa da
#    `v1/strumenti/sshpw.py`, che la parola la scrive sul pty solo a chi la
#    chiede.  ⚠ Qui di la' non serve nessun `sudo`: si legge e basta.
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
RADICE=$(cd "$QUI/.." && pwd)
SSHPW=$RADICE/v1/strumenti/sshpw.py
IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7561}
SCHERMO=${SCHERMO:-:103}
# ⛔ Lo schermo finto e' piu' GRANDE della tela: la finestra la porta alla
#    misura esatta `Emulation.setDeviceMetricsOverride`, e uno schermo piu'
#    piccolo la taglierebbe in silenzio.
FINTO=${FINTO:-2200x1400}
TELA=${TELA:-1920x1080}
UTENTE=${UTENTE:-nicfio}
DIAGNOSI=${DIAGNOSI:-9603}
RILIEVO=${RILIEVO:-/media/REMOTIX/tmp/02-montaggio/rilievo}
# ⚠ Gli ingressi grezzi sono 30 MB a giro e NON stanno nel deposito: stessa
#   convenzione di `02-giudizio-confronto.sh` (`/tmp/remotix-f26-$USER`).  Quel
#   che resta nel deposito e' la riga di `02-giudizio-esiti.jsonl` e la
#   fotografia — cioe' quel che si rilegge, non quel che si rifa'.
LAV=${LAV:-/tmp/remotix-f26-catena-$USER}
COPIE=${COPIE:-$QUI/02-giudizio-catena-copie}
ESITI=${ESITI:-$QUI/02-giudizio-esiti.jsonl}
GIRO=${GIRO:-catena-vera-$(date +%Y%m%d-%H%M%S)}

VERDE=$'\033[1;32m'; ROSSO=$'\033[1;31m'; GIALLO=$'\033[1;33m'; GRIGIO=$'\033[0m'
ok()  { printf '    %sOK%s  %s\n' "$VERDE" "$GRIGIO" "$*"; }
ko()  { printf '    %sNO%s  %s\n' "$ROSSO" "$GRIGIO" "$*"; }
dub() { printf '    %s??%s  %s\n' "$GIALLO" "$GRIGIO" "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

T=$(mktemp -d)
XVFB=""; BROWSER=""
ripulisci() {
	[ -n "$BROWSER" ] && { kill "$BROWSER" 2>/dev/null; wait "$BROWSER" 2>/dev/null; }
	[ -n "$XVFB" ] && kill "$XVFB" 2>/dev/null
	rm -rf "$T"
}
trap ripulisci EXIT
X() { env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO "$@"; }
la()  { timeout 600 python3 "$SSHPW" "$1"; }
prendi() { timeout 900 python3 "$SSHPW" --get "$1" "$2"; }

vicini() {
	local r=""
	for p in 7448 7501 7561; do
		r="$r$p: $(ssh -o BatchMode=yes -o ConnectTimeout=8 "nicfio@$IND" \
		           "ss -tuln | grep -c ':$p\b'" 2>/dev/null | tr -d '\r') · "
	done
	printf '%s\n' "${r%· }"
}

L=${TELA%x*}; A=${TELA#*x}
mkdir -p "$LAV" "$COPIE"

log "0. Gli attrezzi, la scena e i vicini"
for t in Xvfb xdpyinfo google-chrome python3 curl ffmpeg ffprobe; do
	command -v "$t" >/dev/null || { ko "⛔ manca «$t»"; exit 2; }
done
python3 -c 'import numpy' 2>/dev/null || { ko "⛔ manca numpy"; exit 2; }
ok "Xvfb · google-chrome · ffmpeg · ffprobe · numpy"
inf "vicini PRIMA — $(vicini)"
inf "bersaglio https://$IND:$PORTA/ · utente «$UTENTE» · tela $TELA"
inf "giro: $GIRO"

log "1. Il bersaglio risponde, e serve LA PAGINA DI OGGI"
cod=$(curl -k -s -o "$T/pagina.html" -w '%{http_code}' --max-time 15 "https://$IND:$PORTA/")
[ "$cod" = "200" ] || { ko "⛔ GET / → $cod"; exit 2; }
n=$(grep -c 'adatta_vista' "$T/pagina.html")
ok "GET / → 200, $(wc -c < "$T/pagina.html") byte"
if [ "$n" -gt 0 ]; then
	ok "⭐ la pagina SERVITA porta «adatta_vista» $n volte: e' quella curata"
else
	ko "⛔ la pagina servita e' quella di PRIMA della cura: il processo va"
	ko "   riavviato (legge il file una volta sola all'accensione)"
	exit 2
fi

log "2. La parola d'ordine, in un file 0600 (difetto D12)"
PW=$(sed -n 's/^[Pp]ass[[:space:]]*:[[:space:]]*//p' "$HOME/SERVER.ssh" | tr -d ' \r\n')
[ -n "$PW" ] || { ko "⛔ non ho letto la parola da ~/SERVER.ssh"; exit 2; }
umask 077
printf '%s' "$PW" > "$T/parola"; unset PW
ok "scritta in $T/parola — non passa da nessun argv"

log "3. Xvfb e Chrome"
Xvfb "$SCHERMO" -screen 0 "${FINTO}x24" >"$T/xvfb.log" 2>&1 &
XVFB=$!
for i in $(seq 40); do X xdpyinfo >/dev/null 2>&1 && break; sleep 0.25; done
X xdpyinfo >/dev/null 2>&1 || { ko "⛔ Xvfb non risponde"; cat "$T/xvfb.log"; exit 2; }
inf "Xvfb $SCHERMO a $FINTO, pid $XVFB"
mkdir -p "$T/profilo"
# ⚠ Nessun `--ignore-certificate-errors`: l'interstiziale si BATTE, come fa
#   l'utente la prima volta (`02-pagina-misura-prova.py`).
X google-chrome --user-data-dir="$T/profilo" --no-first-run \
	--no-default-browser-check --disable-gpu \
	--remote-debugging-port="$DIAGNOSI" --remote-allow-origins='*' \
	--window-size=${FINTO%x*},${FINTO#*x} --window-position=0,0 \
	about:blank >"$T/chrome.log" 2>&1 &
BROWSER=$!
inf "Chrome pid $BROWSER, porta di diagnosi $DIAGNOSI"

log "4. ⭐⭐ I PIXEL DELLA TELA DEL PRODOTTO, FUORI DAL BROWSER"
python3 "$QUI/02-giudizio-catena.py" --url "https://$IND:$PORTA/" \
	--diagnosi "$DIAGNOSI" --utente "$UTENTE" --parola-file "$T/parola" \
	--tela "$TELA" --fuori-pixel "$LAV/pagina.rgb24" \
	--fuori-json "$LAV/pagina.json" --copia "$COPIE/$GIRO-scheda.png"
s=$?
rm -f "$T/parola"
if [ "$s" -ne 0 ]; then
	ko "⛔ i pixel non sono usciti (stato $s): il metro non ha un ingresso."
	ko "   ⛔ stato 2 — NON MISURATO.  Non e' un bocciato del prodotto."
	inf "vicini DOPO — $(vicini)"
	exit 2
fi

log "5. Il rilievo del PRODOTTO — cattura e flusso, presi da NIC-OS"
# ⛔ Un rilievo di ieri e un rilievo di adesso hanno la stessa faccia in `ls`, e
#    confrontare la tela di adesso con la cattura di ieri sarebbe innestare da
#    soli il guasto «fotogramma del giro precedente» — quello che in questo giro
#    nessuno strumento vede, perche' M6 e' spento su un'immagine ferma.
#
# ⛔⭐ MA LA FRESCHEZZA NON SI MISURA SUL MIO GIRO, e la prima stesura sbagliava
#    proprio qui — `[M]` 13 agosto 2026, secondo giro: *«cattura.bgrx e' di 171 s
#    fa: NON e' di questo giro»*, su un rilievo perfettamente valido.
#
#    La causa e' un invariante del prodotto, non un difetto: **il palco
#    appartiene alla sessione, non alla connessione** (I4).  Il figlio nasce al
#    primo ingresso, cattura UNA volta e **sopravvive al distacco**; chi rientra
#    riceve **lo stesso** fotogramma (`P2-7-figlio.md` §4.2 — *«ricatturare
#    consegnerebbe due immagini diverse sotto la stessa etichetta»*).
#    ⇒ Pretendere un rilievo nato col mio browser vuol dire pretendere che il
#      prodotto violi I4.
#
# ⇒ La grandezza vera del fenomeno e' **l'accensione del server**: il rilievo
#   dev'essere di QUESTO server, non di uno di ieri.  (`LEZIONI.md` §1.13: una
#   tolleranza si scrive sulla grandezza vera, o si sposta a ogni rilettura.)
PIDF=${PIDF:-/media/REMOTIX/tmp/02-montaggio/pid}
# ⛔⛔ E LA REDIREZIONE STA DENTRO IL COMANDO REMOTO, MAI ATTORNO A `ssh`.
#    Pagata sei volte: una richiesta di parola d'ordine va sullo stderr, e una
#    redirezione attorno alla chiamata la mangia — il comando resta appeso in
#    silenzio.  ⇒ di la' si scrive un file, di qua lo si prende con `scp`, e
#    ⚠ «un file non ha livelli di virgolette».
la "{ ls -l --time-style=+%s $RILIEVO/; \
      echo \"ADESSO \$(date +%s)\"; \
      echo \"ETA \$(ps -o etimes= -p \$(cat $PIDF) | tr -d ' ')\"; \
    } > /tmp/02-giudizio-catena-ls.txt; \
    echo '--- il listato e nel file, e adesso lo prendo con scp:'; \
    cat /tmp/02-giudizio-catena-ls.txt"
prendi /tmp/02-giudizio-catena-ls.txt "$T/rilievo-ls.txt" \
	|| { ko "⛔ non ho preso il listato del rilievo: non dico niente della sua"
	     ko "   freschezza, e stato 2 invece di un verde sulla fiducia"; exit 2; }
ADESSO=$(awk '$1 == "ADESSO" {print $2}' "$T/rilievo-ls.txt")
ETA=$(awk '$1 == "ETA" {print $2}' "$T/rilievo-ls.txt")
# ⛔ E se l'eta' del server non si legge, non si tira a indovinare: «non ho
#    potuto guardare» non e' «va bene» (`LEZIONI.md` §1.9).
case "${ADESSO:-x}${ETA:-x}" in
*x*) ko "⛔ non ho letto l'ora del server o l'eta' del suo processo (adesso"
     ko "   «$ADESSO», eta' «$ETA»): senza, «il rilievo e' fresco» sarebbe una"
     ko "   speranza.  ⇒ stato 2."; exit 2 ;;
esac
ACCESO=$((ADESSO - ETA))
inf "il server della $PORTA e' acceso da $ETA s ⇒ dalle $(date -d "@$ACCESO" +%H:%M:%S)"
vecchi=0
for f in cattura.bgrx flusso-av1.obu flusso-hevc.265; do
	t=$(awk -v n="$f" '$NF == n {print $(NF-1)}' "$T/rilievo-ls.txt")
	if [ -z "$t" ]; then
		inf "⚠ $f non c'e' nel rilievo"
		continue
	fi
	if [ "$t" -lt "$ACCESO" ]; then
		ko "⛔ $f e' di $((ACCESO - t)) s PRIMA dell'accensione del server: e' il"
		ko "   rilievo di un server morto, e la tela di adesso non lo riguarda"
		vecchi=$((vecchi+1))
	else
		ok "$f e' di questo server (scritto $((t - ACCESO)) s dopo l'accensione, $((ADESSO - t)) s fa)"
	fi
done
[ "$vecchi" -eq 0 ] || { ko "⛔ stato 2: il rilievo e' di un altro server"; exit 2; }

for f in cattura.bgrx flusso-av1.obu flusso-hevc.265; do
	prendi "$RILIEVO/$f" "$LAV/$f" || inf "⚠ $f non preso"
done
[ -s "$LAV/cattura.bgrx" ] || { ko "⛔ la cattura non e' arrivata"; exit 2; }
ok "cattura.bgrx $(wc -c < "$LAV/cattura.bgrx") byte"

# ⛔ QUALE FLUSSO?  Quello del codec che la PAGINA ha negoziato, non quello che
#    fa comodo: il deposito ne ha due (§«La forma scelta» di P2-6), e giudicare
#    la tela contro l'altro misurerebbe due codifiche diverse.
CODEC=$(python3 - "$LAV/pagina.json" <<'PY'
import json, re, sys
d = json.load(open(sys.argv[1]))
r = ((d.get("stato") or {}).get("registro") or "")
m = re.search(r"negoziato:\s*codec\s*(\w+)", r)
print(m.group(1) if m else "")
PY
)
case "$CODEC" in
av1)  FLUSSO=$LAV/flusso-av1.obu;  FORMATO=obu ;;
hevc) FLUSSO=$LAV/flusso-hevc.265; FORMATO=hevc ;;
*)    ko "⛔ non ho letto dal registro della pagina quale codec e' stato"
      ko "   negoziato: senza, non so quale dei due flussi giudicare"
      exit 2 ;;
esac
ok "⭐ la pagina ha negoziato «$CODEC» ⇒ il flusso giudicato e' $(basename "$FLUSSO")"
[ -s "$FLUSSO" ] || { ko "⛔ $FLUSSO non c'e' o e' vuoto"; exit 2; }
inf "$(basename "$FLUSSO") $(wc -c < "$FLUSSO") byte"

log "6. ⛔ Controllo positivo — che cosa dice ffprobe DEL FLUSSO VERO"
px=$(ffprobe -hide_banner -v error -select_streams v:0 \
	-show_entries stream=pix_fmt -of csv=p=0 -f "$FORMATO" "$FLUSSO")
prof=$(ffprobe -hide_banner -v error -select_streams v:0 \
	-show_entries stream=profile -of csv=p=0 -f "$FORMATO" "$FLUSSO")
mis=$(ffprobe -hide_banner -v error -select_streams v:0 \
	-show_entries stream=width,height -of csv=p=0 -f "$FORMATO" "$FLUSSO")
if [ -z "$px" ]; then
	ko "⛔ ffprobe non ha detto NIENTE sul formato dei pixel."
	ko "   ⛔ Vuoto e «a 8 bit» hanno lo stesso aspetto: qui ci si ferma."
	exit 2
fi
# ⛔⭐ LA GAMMA SI CHIEDE AL FLUSSO, NON SI DECIDE QUI — e questa riga e' nata
#    da un ROSSO di questo banco, `[M]` 13 agosto 2026, primo giro sulla catena
#    vera.  La prima stesura decodificava il riferimento con
#    `scale=in_range=full`, copiata dalla catena FINTA, che codifica con
#    `-color_range pc`.  ⛔ Il prodotto invece scrive **`color_range=tv`**, cioe'
#    gamma LIMITATA — e il browser, che legge il VUI, la espandeva
#    correttamente mentre il mio riferimento no.
#    ⇒ M5 e' uscito con guadagno **1,1745 / 1,1686 / 1,1281** e scarti
#      −19/255: e' **esattamente** la firma «gamma limitata letta come piena»
#      che M5 dichiara nella propria ragione (255/219 = 1,164).
#    ⛔ E l'imputato era IL BANCO, non il client: `REVIEWER.md` §1 — il banco e'
#      il primo imputato — applicato alla lettera, e il metro ha nominato da se'
#      la propria causa.
rng=$(ffprobe -hide_banner -v error -select_streams v:0 \
	-show_entries stream=color_range -of csv=p=0 -f "$FORMATO" "$FLUSSO")
case "$rng" in
tv|mpeg)  IN_RANGE=limited; GAMMA=limitata ;;
pc|jpeg)  IN_RANGE=full;    GAMMA=piena ;;
*)        ko "⛔ il flusso NON dichiara la gamma (color_range = «$rng»)."
          ko "   ⚠ «non dichiarata» e «piena» non sono la stessa cosa: senza il"
          ko "     VUI il decodificatore INDOVINA, e l'indovinato sbagliato ha"
          ko "     la firma di un difetto del client (M5, guadagno 1,164)."
          ko "   ⇒ stato 2: qui non si da' nessun numero."
          exit 2 ;;
esac
ok "⭐ il flusso DICHIARA la gamma: color_range «$rng» ⇒ $GAMMA"
inf "pix_fmt «$px» · profilo «$prof» · misura «$mis»"
case "$px" in
*10le|*10be) ok "il flusso e' a 10 bit — ⚠ e sono 8 bit PROMOSSI: la sorgente"
             inf "   Mutter da' BGRx, misurato (F2.2).  M7 e' comunque spento"
             inf "   in questo giro: la scena non ha zone sfumate dichiarate" ;;
*)           dub "⚠ il flusso e' $px, NON a 10 bit: si dichiara e si prosegue —"
             dub "   M7 e' gia' spento su questa scena, quindi non cambia nulla" ;;
esac
[ "$mis" = "$L,$A" ] || { ko "⛔ il flusso e' $mis e la tela e' $L,$A: non sono"
	ko "   la stessa immagine, e non ridimensiono niente"; exit 2; }

log "7. La cattura e il riferimento — ⭐ e il riferimento e' il SECONDO LETTORE"
# ⛔ BGRx → RGB, e i due nomi non sono un dettaglio: interpretare BGRx come
#    RGBx **e'** il guasto «piani scambiati», prodotto da noi (cucitura F2.2).
python3 - "$LAV/cattura.bgrx" "$LAV/cattura.rgb48" "$L" "$A" <<'PY'
import sys
import numpy as np
crudo, fuori, L, A = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
dati = np.fromfile(crudo, dtype=np.uint8)
atteso = L * A * 4
if dati.size < atteso:
    raise SystemExit("⛔ la cattura ha %d byte, ne servivano %d per %dx%d BGRx"
                     % (dati.size, atteso, L, A))
a = dati[:atteso].reshape(A, L, 4)
# BGRx: byte 0 = B, 1 = G, 2 = R, 3 = riempimento (F2.2, [M] su Mutter)
rgb = a[:, :, [2, 1, 0]].astype(np.uint16)
# a 16 bit come li vuole il metro, replicando l'ottetto: 0xNN → 0xNNNN, che e'
# la scala esatta (255 → 65535), non uno spostamento di 8 bit.
(rgb * 257).astype("<u2").tofile(fuori)
print("    OK  %s: %dx%d BGRx → rgb48le, %d byte" % (fuori, L, A, L * A * 6))
PY
[ -s "$LAV/cattura.rgb48" ] || { ko "⛔ la conversione della cattura non e' riuscita"; exit 2; }

# ⛔ `in_range` E' QUELLO CHE IL FLUSSO DICHIARA (letto al passo 6), e
#    `out_range=full` perche' l'RGB e' pieno per definizione.  ⚠ Scriverlo a
#    mano e' quel che ha fatto sbagliare il primo giro.
ffmpeg -hide_banner -loglevel error -y -f "$FORMATO" -i "$FLUSSO" \
	-frames:v 1 -vf "scale=in_range=$IN_RANGE:out_range=full" \
	-pix_fmt rgb48le -f rawvideo "$LAV/riferimento.rgb48" || {
	ko "⛔ ffmpeg non ha decodificato il flusso in rgb48le"; exit 2; }
ffmpeg -hide_banner -loglevel error -y -f "$FORMATO" -i "$FLUSSO" \
	-frames:v 1 -pix_fmt yuv420p10le -f rawvideo "$LAV/riferimento.yuv" || {
	ko "⛔ ffmpeg non ha decodificato il flusso in yuv420p10le"; exit 2; }
ok "riferimento.rgb48 $(wc -c < "$LAV/riferimento.rgb48") byte · "\
"riferimento.yuv $(wc -c < "$LAV/riferimento.yuv") byte"

log "8. Le due dichiarazioni: il colore e la scena"
# ⛔ Si dichiara quel che si e' CHIESTO, riga per riga.  Dichiarare non prova
#    che sia stato fatto: quello lo verifica M5 sui pixel.
cat > "$LAV/colore.json" <<JSON
{
  "cattura":     {"spazio": "RGB", "matrice": "nessuna", "gamma": "piena",
                  "nota": "Mutter consegna BGRx: 8 bit veri, range misurato 0-255 (F2.2)"},
  "codifica":    {"matrice": "bt709", "gamma": "$GAMMA", "gamma_ingresso": "piena",
                  "primarie": "bt709",
                  "nota": "LETTO dal flusso con ffprobe (color_range = $rng), non deciso qui"},
  "riferimento": {"matrice": "bt709", "gamma": "$GAMMA", "primarie": "bt709"},
  "pagina":      {"matrice": "bt709", "gamma": "$GAMMA", "primarie": "bt709"}
}
JSON
# ⛔⭐ LA SCENA SI DICHIARA, E LE DUE DICHIARAZIONI NON SONO EQUIVALENTI.
#
#    `MIRA_JSON=…`  la scena della sessione **e' la mira** di F2.6 (messa sul
#                   monitor virtuale come sfondo del desktop, vedi §«la mira»
#                   qui sotto): allora M4, M7 e i marcatori di M-V hanno dove
#                   guardare, e i dodici guasti sono dodici.
#    senza           la scena e' il desktop qualunque dell'utente: tre
#                   strumenti si spengono, e il metro **conta** da se' quanti
#                   guasti questo giro non avrebbe visto.
#
# ⛔ E la dichiarazione non si crede sulla parola: il metro cerca i quattro
#    marcatori d'angolo NELLA CATTURA, e se non ci sono non da' nessun verdetto
#    (M-V).  ⇒ dire «e' la mira» quando non lo e' produce uno stato 1, non un
#    verde comodo.
SCENA_NOME=desktop-vero
if [ -n "${MIRA_JSON:-}" ]; then
	[ -s "$MIRA_JSON" ] || { ko "⛔ MIRA_JSON=«$MIRA_JSON» non c'e' o e' vuoto"; exit 2; }
	SCENA_NOME=$(python3 - "$MIRA_JSON" "$LAV/scena.json" "$L" "$A" "$GIRO" <<'PY'
import json, sys
dentro, fuori, L, A, giro = (sys.argv[1], sys.argv[2], int(sys.argv[3]),
                             int(sys.argv[4]), sys.argv[5])
m = json.load(open(dentro))
# ⛔ La misura della mira e quella della tela devono coincidere: una mira di
#    un'altra misura vorrebbe dire zone nel posto sbagliato, cioe' uno
#    strumento che guarda dove il segnale non c'e'.
if int(m["larghezza"]) != L or int(m["altezza"]) != A:
    raise SystemExit("⛔ la mira e' %dx%d e la tela e' %dx%d: le zone "
                     "cadrebbero nel posto sbagliato"
                     % (m["larghezza"], m["altezza"], L, A))
m["nome"] = "mira-" + str(m.get("giro", "?"))
m["mira"] = True
m["giro_del_metro"] = giro
m["perche"] = ("⭐ La scena della sessione E' la mira di F2.6: messa sul "
               "monitor virtuale come sfondo del desktop, cioe' come l'unica "
               "cosa che Mutter dipinge sul monitor che il prodotto cattura.  "
               "⇒ M4 (i tre riquadri a luminanza uguale), M7 (la sfumatura "
               "dichiarata) e i marcatori d'angolo di M-V hanno dove guardare, "
               "e i dodici guasti sono dodici.  ⛔ E la dichiarazione non basta: "
               "i marcatori si CERCANO nella cattura.")
json.dump(m, open(fuori, "w"), ensure_ascii=False, indent=1)
sys.stderr.write("    OK  %s: mira=true «%s», %dx%d\n"
                 % (fuori, m["nome"], L, A))
print(m["nome"])
PY
	) || { ko "⛔ la scena della mira non si e' scritta"; exit 2; }
	ok "⭐ la scena dichiarata e' LA MIRA: «$SCENA_NOME»"
else
python3 - "$LAV/scena.json" "$L" "$A" "$GIRO" <<'PY'
import json, sys
fuori, L, A, giro = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
json.dump({
    "nome": "desktop-vero",
    "giro": giro,
    "mira": False,
    "larghezza": L, "altezza": A,
    "zone": {},
    "perche": ("⛔ La scena e' il DESKTOP DELL'UTENTE, non la mira di F2.6: "
               "non ha i quattro marcatori d'angolo, non ha i tre riquadri a "
               "luminanza uguale e non ha zone sfumate dichiarate.  ⇒ M4, M7 e "
               "i marcatori di M-V si dichiarano NON APPLICABILI, e il metro "
               "conta quanti dei dodici guasti questo giro non avrebbe visto.  "
               "⭐ La cura non e' una soglia: e' la mira sul monitor virtuale "
               "(P2-6 §7 punto 2)."),
}, open(fuori, "w"), ensure_ascii=False, indent=1)
print("    OK  %s: mira=false, %dx%d" % (fuori, L, A))
PY
fi

python3 - "$LAV/pagina.json" "$LAV/identita.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
json.dump(d.get("identita") or {}, open(sys.argv[2], "w"),
          ensure_ascii=False, indent=1)
print("    OK  %s (cucitura F2.4)" % sys.argv[2])
PY

log "9. ⭐⭐ IL METRO — i due piani, sulla catena vera"
# ⛔⭐ M6 (LA FRESCHEZZA) VUOLE DUE CATTURE CON SCENE DIVERSE, e su questa
#    catena non si ottengono da sole: il palco appartiene alla sessione (I4), il
#    figlio cattura UNA volta e sopravvive al distacco.  ⇒ le due catture si
#    fanno con **due mire diverse** — il riquadro di rumore ha per seme il nome
#    del giro — e fra l'una e l'altra il server si riaccende, perche' e' l'unico
#    modo in cui il prodotto ricattura senza che nessuno lo violenti.
#
#    `PRECEDENTE=/…/cattura.rgb48` e' la cattura del giro PRIMA, con l'ALTRA
#    mira.  ⛔ Senza, M6 si dichiara non misurato: fingere una cattura
#    precedente sarebbe un verde regalato, e passare la STESSA scena sarebbe
#    peggio — il metro direbbe «il fotogramma e' vecchio» su una catena sana.
ARG_M6=(--senza-freschezza)
if [ -n "${PRECEDENTE:-}" ]; then
	[ -s "$PRECEDENTE" ] || { ko "⛔ PRECEDENTE=«$PRECEDENTE» non c'e'"; exit 2; }
	# ⛔ E LE DUE CATTURE DEVONO ESSERE DIVERSE.  Due file uguali darebbero a M6
	#    un delta di 0 dB, cioe' un rosso su una catena sana: sarebbe il banco a
	#    essere rotto, e il metro accuserebbe il prodotto.
	if cmp -s "$PRECEDENTE" "$LAV/cattura.rgb48"; then
		ko "⛔ la cattura di adesso e quella di prima sono IDENTICHE byte per"
		ko "   byte: la scena non si e' mossa fra i due giri.  M6 direbbe «il"
		ko "   fotogramma e' vecchio» su una catena sana ⇒ stato 2, non un rosso"
		exit 2
	fi
	ok "⭐ la cattura precedente c'e' ed e' DIVERSA da questa: M6 e' misurabile"
	inf "   precedente: $PRECEDENTE"
	ARG_M6=(--cattura-precedente "$PRECEDENTE")
else
	inf "⚠ --senza-freschezza: non c'e' una cattura del giro precedente con una"
	inf "  scena diversa.  M6 si dichiara non misurato."
fi
bash "$QUI/02-giudizio-confronto.sh" giudica \
	--scena "$LAV/scena.json" \
	--cattura "$LAV/cattura.rgb48" \
	--riferimento "$LAV/riferimento.rgb48" \
	--pagina "$LAV/pagina.rgb24" \
	--riferimento-10 "$LAV/riferimento.yuv" \
	--colore "$LAV/colore.json" \
	--identita-pagina "$LAV/identita.json" \
	--scena-nome "$SCENA_NOME" \
	--giro "$GIRO" \
	"${ARG_M6[@]}"
S=$?

# ---------------------------------------------------------------------------
# ⛔⭐ 9-bis — QUANDO M5 DICE NO, SI CHIEDE **DOVE**, E NON LO SI DEDUCE.
#
# M5 nomina due firme: gamma limitata letta come piena (guadagno 1,164) e
# matrice BT.601 letta come BT.709.  ⚠ Un rosso di M5 che non sia nessuna
# delle due e' un numero non interpretabile — e `LEZIONI.md` §1.13 dice che si
# nomina **la grandezza vera del fenomeno**, non una che le somiglia.
#
# ⇒ Questo passo mette le due ipotesi accanto al misurato, decodificando lo
#   stesso flusso nei due modi sbagliati, e separa il guadagno per **piano**:
#   se Y sta a 1,000 e lo scarto e' tutto in Cb/Cr, la causa non e' ne' la
#   gamma ne' la matrice — sono due decodificatori che fanno la crominanza in
#   modo diverso, e la soglia di M5 non e' mai stata tarata su quel caso.
if [ "$S" -eq 1 ]; then
	log "9-bis. ⛔ M5 (o un altro) ha detto no: l'anatomia, invece della deduzione"
	ffmpeg -hide_banner -loglevel error -y -f "$FORMATO" -i "$FLUSSO" -frames:v 1 \
		-vf "scale=in_range=$IN_RANGE:out_range=full:in_color_matrix=bt601" \
		-pix_fmt rgb48le -f rawvideo "$LAV/rif-601.rgb48"
	ffmpeg -hide_banner -loglevel error -y -f "$FORMATO" -i "$FLUSSO" -frames:v 1 \
		-vf "scale=in_range=full:out_range=full" \
		-pix_fmt rgb48le -f rawvideo "$LAV/rif-gamma-piena.rgb48"
	python3 - "$QUI" "$LAV" "$L" "$A" <<'PY'
import importlib.util, os, sys
import numpy as np
QUI, LAV, L, A = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
sp = importlib.util.spec_from_file_location(
    "m", os.path.join(QUI, "02-giudizio-metro.py"))
m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
r48 = lambda p: np.fromfile(p, "<u2")[:L*A*3].reshape(A, L, 3).astype(np.float64) / 65535.0
r24 = lambda p: np.fromfile(p, np.uint8)[:L*A*3].reshape(A, L, 3).astype(np.float64) / 255.0
rif = r48(f"{LAV}/riferimento.rgb48")
pag = r24(f"{LAV}/pagina.rgb24")


def riga(nome, a, b):
    e = m.m5_gamma(a, b)
    g = [round(c["guadagno"], 4) for c in e["canali"]]
    s = [c["scarto_su255"] for c in e["canali"]]
    print(f"    --  {nome:30s} guadagni {g}  scarti {s}  "
          f"PSNR-Y {m.psnr_num(m.luma(a), m.luma(b)):6.2f} dB")


print("    il MISURATO, e le due firme che M5 nomina — decodificate apposta:")
riga("pagina (il browser vero)", pag, rif)
for f, n in (("rif-601.rgb48", "se fosse la MATRICE (601)"),
             ("rif-gamma-piena.rgb48", "se fosse la GAMMA (piena)")):
    p = os.path.join(LAV, f)
    if os.path.exists(p):
        riga(n, r48(p), rif)
KR, KG, KB = m.KR, m.KG, m.KB


def ycc(a):
    Y = KR * a[:, :, 0] + KG * a[:, :, 1] + KB * a[:, :, 2]
    return Y, (a[:, :, 2] - Y) / (2 * (1 - KB)), (a[:, :, 0] - Y) / (2 * (1 - KR))


def reg(x, y):
    g = np.cov(x.ravel(), y.ravel(), bias=True)[0, 1] / np.var(x)
    return g, (y.mean() - g * x.mean()) * 255


print("    ⭐ e lo stesso scarto separato per PIANO — e' la riga che nomina la")
print("       grandezza vera: la gamma e la matrice muovono ANCHE Y, la")
print("       crominanza no.")
pa, rr = ycc(pag), ycc(rif)
for i, n in enumerate(("Y ", "Cb", "Cr")):
    g, s = reg(rr[i], pa[i])
    print(f"    --  piano {n}   guadagno {g:.4f}   scarto {s:+.3f}/255")
PY

fi

log "10. I vicini, contati DOPO"
inf "vicini DOPO — $(vicini)"
inf "gli ingressi restano in $LAV, la fotografia in $COPIE"

printf '\n'
case "$S" in
0) printf '    %s⭐⭐ IL METRO E'"'"' PASSATO SULLA CATENA VERA — stato 0.%s\n' "$VERDE" "$GRIGIO"
   printf '    %s   ⚠ e con i limiti che il metro ha stampato da se%s: leggerli e%s\n' "$VERDE" "'" "$GRIGIO"
   printf '    %s     parte del verdetto, non un contorno.%s\n' "$VERDE" "$GRIGIO" ;;
1) printf '    %s⛔ BOCCIATO — stato 1.  La misura c'"'"'e'"'"' stata, e dice di no.%s\n' "$ROSSO" "$GRIGIO" ;;
2) printf '    %s⛔ NON MISURATO — stato 2.  Non e'"'"' un bocciato del prodotto.%s\n' "$GIALLO" "$GRIGIO" ;;
3) printf '    %s⛔⛔ METRO ROTTO — stato 3.  Il verdetto di questo giro NON VALE.%s\n' "$ROSSO" "$GRIGIO" ;;
esac
exit "$S"
