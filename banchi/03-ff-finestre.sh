#!/bin/bash
# ⛔⛔ IL CASO CHE SMENTISCE UNA RIGA SCRITTA IN TRE DOCUMENTI:
#     «Firefox non apre finestre su Xvfb :81 — 0 finestre in 90 s».
#
# ⭐ La riga e' vera nel FATTO e falsa nella CONSEGUENZA che ne e' stata tratta
#    («⇒ si prova `--headless`, gli esiti rimandati dalla pagina»), perche' la
#    domanda giusta non era **quante finestre si aprono** ma **se la pagina
#    gira**.  Qui si misurano tutt'e due, nello stesso giro:
#
#      · quante finestre di primo livello compaiono sul display (xdotool)
#      · e se la pagina ha girato davvero (la pagina scrive un file per POST)
#
# ⛔ E il controllo che rende leggibile lo zero: **lo stesso conteggio su
#    Chrome**, che le finestre le apre.  Uno zero senza un caso che sa dare
#    diverso da zero non e' una misura.
#
# uso:  bash banchi/03-ff-finestre.sh [secondi]   (difetto: 90, come la riga)
set -u
SEC="${1:-90}"
BASE=/var/tmp/corsia-d/finestre
PORTA=8879
SCHERMO=:78
rm -rf "$BASE"; mkdir -p "$BASE/servita"

cat > "$BASE/servita/index.html" <<'HTML'
<!doctype html><meta charset=utf-8><title>finestre</title><body><pre>ciao</pre>
<script>fetch('/vivo-' + Date.now(), {method: 'POST'}).catch(() => {});</script>
</body>
HTML

python3 -m http.server "$PORTA" --bind 127.0.0.1 --directory "$BASE/servita" \
        > "$BASE/servitore.log" 2>&1 &
PID_SRV=$!
Xvfb "$SCHERMO" -screen 0 1920x1200x24 > /dev/null 2>&1 &
PID_X=$!
# ⛔ La pulizia va in una TRAPPOLA, non in fondo: la prima stesura di questo
#    script e' morta a meta' con `set -u` e ha lasciato acceso il servitore.
#    Il giro dopo non ha potuto legare la porta e ⛔ **avrebbe contato le
#    finestre contro un servitore morto**, cioe' avrebbe dato «0 POST» come se
#    fosse un esito del browser.
trap 'kill "$PID_X" "$PID_SRV" 2>/dev/null' EXIT
sleep 2
# ⛔ E il servitore si CONTROLLA: un banco che misura contro una porta morta
#    consegna uno zero che sembra una misura.
if ! kill -0 "$PID_SRV" 2>/dev/null || ! ss -ltn | grep -q ":$PORTA "; then
  echo "⛔ IL SERVITORE NON E' PARTITO sulla porta $PORTA — non misuro niente."
  sed -n '$p' "$BASE/servitore.log"
  exit 3
fi
export DISPLAY="$SCHERMO"; unset WAYLAND_DISPLAY

conta() {   # ⚠ due modi diversi di contare, perche' uno solo si sbaglia in silenzio
  local a b
  a=$(xdotool search --onlyvisible --name "" 2>/dev/null | wc -l)
  b=$(xwininfo -root -children 2>/dev/null | grep -c '^     0x')
  echo "$a/$b"
}

giro() {
  # ⚠ Tre `local` separati e non uno solo: in un unico `local` la terza
  #   variabile non vede ancora la prima, e con `set -u` il banco muore.
  #   ⭐ `set -u` e' un amico: l'ha detto invece di andare avanti a vuoto.
  local motore="$1"
  local extra="$2"
  local prof="$BASE/prof-$motore$3"
  rm -rf "$prof"; mkdir -p "$prof"
  echo ""
  echo "== $motore $extra   (display $SCHERMO, $SEC s)"
  if [ "$motore" = firefox ]; then
    firefox --profile "$prof" $extra "http://127.0.0.1:$PORTA/" \
            > "$BASE/$motore$3.log" 2>&1 &
  else
    google-chrome --user-data-dir="$prof" --no-first-run \
            --no-default-browser-check --disable-sync $extra \
            "http://127.0.0.1:$PORTA/" > "$BASE/$motore$3.log" 2>&1 &
  fi
  local pid=$! t=0
  while [ "$t" -lt "$SEC" ]; do
    sleep 10; t=$((t + 10))
    echo "   a $t s: finestre (xdotool/xwininfo) = $(conta)   ·  clienti X: $(xlsclients 2>/dev/null | wc -l)"
  done
  # ⭐ LA DOMANDA VERA: la pagina ha girato?  Il POST e' nel registro del servitore.
  local post
  post=$(grep -c '"POST /vivo-' "$BASE/servitore.log" || true)
  echo "   ⇒ finestre alla fine: $(conta)   ·   POST della pagina finora: $post"
  kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
  rm -rf "$prof"
}

echo "== LA SCENA: CHUWI, Xvfb $SCHERMO 1920x1200x24, $(firefox --version), $(google-chrome --version)"
echo "   il conteggio dei POST e' CUMULATIVO: quel che conta e' che salga."
giro chrome  ""           "-finestra"
giro firefox ""           "-finestra"
giro firefox "--headless" "-headless"

kill "$PID_X" "$PID_SRV" 2>/dev/null
wait "$PID_X" "$PID_SRV" 2>/dev/null
echo ""
echo "== il registro del servitore (le richieste vere) =="
grep -E '"(GET|POST) ' "$BASE/servitore.log" | sed 's/^/   /'
