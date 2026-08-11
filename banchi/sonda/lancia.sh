#!/bin/bash
# lancia.sh — un BROWSER VERO contro il server di src/.  Gira SULL'HOST (il
# browser sta li'), il server gira nel contenitore.
set -uo pipefail
QUI=$(cd -- "$(dirname -- "$0")" && pwd)
IND=${1:-192.168.0.2}
PORTA=${2:-7448}
RACC=8898
ok() { printf '    OK  %s\n' "$*"; }
ko() { printf '    NO  %s\n' "$*"; }
log(){ printf '\n== %s\n' "$*"; }

command -v firefox >/dev/null || { ko "firefox non c'e'"; exit 2; }
command -v xvfb-run >/dev/null || { ko "xvfb-run non c'e'"; exit 2; }
firefox --version

log "L'impronta la si chiede AL SERVER, non la si indovina"
IMP=$(curl -sk "https://$IND:$PORTA/impronta" | python3 -c 'import json,sys;print(json.load(sys.stdin)["impronta"])')
[ -n "$IMP" ] || { ko "nessuna impronta da https://$IND:$PORTA/impronta"; exit 2; }
echo "    impronta: $IMP"

rm -f "$QUI/esiti.jsonl"
python3 "$QUI/racc.py" $RACC > "$QUI/racc.log" 2>&1 &
PR=$!
sleep 1
[ -d "/proc/$PR" ] || { ko "raccoglitore morto"; cat "$QUI/racc.log"; exit 2; }
ok "raccoglitore su 127.0.0.1:$RACC"

giro() # $1 = etichetta, $2 = parola
{
  local prof="$QUI/prof-$1"
  rm -rf "$prof"; mkdir -p "$prof"
  local U="http://127.0.0.1:$RACC/sonda-rcp.html?base=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=""))' "https://$IND:$PORTA")&impronta=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=""))' "$IMP")#utente=prova&parola=$2"
  log "giro «$1»"
  # ⛔ E QUI L'INDIRIZZO SI STAMPA MASCHERATO — R12-A.34, seconda meta'.
  #    Spostare la parola nel frammento la toglie dal registro HTTP, ma questa
  #    riga la scriveva sul terminale, e il terminale di un giro finisce in un
  #    file come tutto il resto.  ⚠ Una cura a meta' e' peggio di nessuna: fa
  #    credere che il buco sia chiuso.
  echo "    ${U%%#*}#utente=prova&parola=<NON SI STAMPA>"
  xvfb-run -a firefox --no-remote --profile "$prof" "$U" > "$QUI/ff-$1.log" 2>&1 &
  local p=$!
  local i=0
  while [ "$i" -lt 45 ]; do
    [ -s "$QUI/esiti.jsonl" ] && break
    sleep 1; i=$((i+1))
  done
  kill "$p" 2>/dev/null; wait "$p" 2>/dev/null
  if [ ! -s "$QUI/esiti.jsonl" ]; then
    ko "nessun esito in $i secondi"
    echo "    -- richieste ricevute dal raccoglitore: $(grep -c '^richiesta: ' "$QUI/racc.log")"
    tail -6 "$QUI/racc.log" | sed 's/^/        /'
    tail -8 "$QUI/ff-$1.log" | sed 's/^/        /'
    return 1
  fi
  ok "esito ricevuto dopo $i secondi"
  cat "$QUI/esiti.jsonl" | python3 -c '
import json,sys
for r in sys.stdin:
    d=json.loads(r)
    print("        esito :", d.get("esito"))
    print("        motore:", (d.get("motore") or "")[:90])
    print("        detta :", d.get("dettaglio"))
    for x in (d.get("righe") or []): print("          .", x)
'
  return 0
}

giro ammesso parola-di-prova; E1=$?
rm -f "$QUI/esiti.jsonl"
giro respinto parola-SBAGLIATA; E2=$?

kill "$PR" 2>/dev/null
log "esiti: ammesso=$E1 respinto=$E2"
