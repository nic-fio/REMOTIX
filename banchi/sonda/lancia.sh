#!/bin/bash
# lancia.sh — un BROWSER VERO contro il server di src/.  Gira SULL'HOST (il
# browser sta li'), il server gira nel contenitore.
set -uo pipefail
QUI=$(cd -- "$(dirname -- "$0")" && pwd)
IND=${1:-192.168.0.2}
PORTA=${2:-7448}
# ⛔ La porta del raccoglitore e' un PARAMETRO — 11 agosto 2026, sera.  Era
#    fissa a 8898, e due giri della sonda sulla stessa macchina si prendevano
#    la porta a vicenda: il secondo moriva con «raccoglitore morto», che ha
#    esattamente l'aspetto di «la sonda non sa partire».  Sono due cose.
RACC=${3:-8898}
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

# ---------------------------------------------------------------------------
# ⛔ CHI STA ANCORA USANDO QUESTO PROFILO — letto da `/proc`, PID per PID.
#
#    ⛔ Non `pkill -f`: quello sceglie da se' chi ammazzare, e prenderebbe il
#       browser di un altro giro (la regola del progetto: si ferma PER PID).
#    ⭐ Il criterio e' il percorso del profilo, che esiste solo per questo giro,
#       e si confronta con l'argomento INTERO (`grep -x`): «/…/prof-ammesso» e
#       «/…/prof-ammesso-vecchio» sono due cose.
chi_usa_il_profilo() # $1 = profilo
{
  local d
  for d in /proc/[0-9]*; do
    [ -r "$d/cmdline" ] || continue
    if tr '\0' '\n' < "$d/cmdline" 2>/dev/null | grep -qxF -- "$1"; then
      printf '%s\n' "${d#/proc/}"
    fi
  done
}

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
  # ⚠ `setsid` mette Firefox e il suo Xvfb in un gruppo tutto loro, cosi' il
  #   TERM qui sotto puo' provare a prenderli in blocco.  ⛔ Ma e' un tentativo,
  #   non il criterio: il criterio e' `/proc`, e la ragione sta nella corsa
  #   raccontata piu' sotto.
  setsid xvfb-run -a firefox --no-remote --profile "$prof" "$U" \
      > "$QUI/ff-$1.log" 2>&1 &
  local p=$!
  local i=0
  while [ "$i" -lt 45 ]; do
    [ -s "$QUI/esiti.jsonl" ] && break
    sleep 1; i=$((i+1))
  done

  # ⛔⭐ E QUI C'ERA UNA CORSA, ED E' STATA MISURATA — 11 agosto 2026, 12:50 UTC.
  #
  #     `kill "$p"` ammazzava **il capo** — `xvfb-run`, che e' uno script di
  #     shell — e non Firefox, che e' suo figlio.  ⛔ Il profilo veniva
  #     cancellato mentre Firefox era ancora vivo, e Firefox lo **riscriveva
  #     subito dopo**: `[M]` profilo cancellato alle 12:49:54,
  #     `sessionstore-backups/recovery.jsonlz4` ricomparso alle **12:50:10**,
  #     2223 byte, con dentro la parola d'ordine.
  #
  # ⚠ Cioe' la cura c'era, il registro diceva «il profilo si butta adesso», e il
  #   segreto restava sul disco lo stesso.  E' la forma peggiore: una cura che
  #   **stampa di aver funzionato**.
  #
  # ⛔ E LA PRIMA CURA NON E' BASTATA, ED E' STATA MISURATA ANCHE LEI: si e'
  #    passati a `setsid` + `kill -- -$p`, cioe' al GRUPPO, e alle 12:51:31 UTC
  #    `recovery.jsonlz4` e' ricomparso lo stesso (2227 byte, la parola dentro).
  #    ⛔ Il motivo e' che «il gruppo e' morto» rispondeva **subito** — cioe' il
  #    controllo era muto — e un controllo muto e' indistinguibile da un
  #    controllo che passa.
  #
  # ⭐ Da cui il criterio di adesso, che non passa dai gruppi: si guarda in
  #    `/proc` CHI ha ancora questo profilo fra i suoi argomenti.  Il caso
  #    contrario ha un aspetto preciso — l'elenco non si svuota, e questa
  #    funzione esce 3 senza cancellare niente.
  kill -TERM -- "-$p" 2>/dev/null   # il gruppo: si prova, non ci si fida
  wait "$p" 2>/dev/null
  local g=0 vivi
  vivi=$(chi_usa_il_profilo "$prof")
  [ -n "$vivi" ] && kill $vivi 2>/dev/null
  while [ "$g" -lt 60 ]; do
    vivi=$(chi_usa_il_profilo "$prof")
    [ -z "$vivi" ] && break
    sleep 0.5; g=$((g+1))
  done
  if [ -n "$vivi" ]; then
    echo "    -- dopo 30 s col TERM usano ancora il profilo: $(echo $vivi) — KILL"
    kill -KILL $vivi 2>/dev/null
    sleep 1
    vivi=$(chi_usa_il_profilo "$prof")
  fi
  if [ -n "$vivi" ]; then
    ko "⛔ questi processi hanno ancora il profilo aperto: $(echo $vivi)"
    ko "   NON cancello: cancellarlo adesso vorrebbe dire farselo riscrivere"
    return 3
  fi
  echo "    -- browser spento, e lo dice /proc: nessun processo ha piu' «$prof»"
  echo "       fra i suoi argomenti (atteso $(( g / 2 )) s)"

  # ⛔⭐ LA SECONDA META' DELLA CURA DEL FRAMMENTO — 11 agosto 2026, sera.
  #
  #     `sonda-rcp.html` dichiara, nel commento di R12-A.34, che *«il profilo lo
  #     si butta a fine giro (lancia.sh)»*.  ⛔ Non era vero: `lancia.sh`
  #     buttava il profilo all'INIZIO del giro, e quello dell'ultimo giro
  #     restava sul disco — con la parola d'ordine dentro
  #     `sessionstore-backups/recovery.jsonlz4`, perche' il frammento fa parte
  #     dell'indirizzo che il browser salva nella sessione.  ⚠ Una cura scritta
  #     in un commento e non nel codice fa credere che il buco sia chiuso: e'
  #     peggio di nessuna cura.
  #
  # ⭐ E prima di buttarlo si MISURA, invece di buttarlo e basta: cosi' resta
  #    scritto che cosa c'era dentro — se un giorno il frammento smettesse di
  #    finire nella sessione salvata, questa riga passerebbe da N a 0 e si
  #    saprebbe che e' cambiato qualcosa, invece di non saperlo mai.
  local sporchi resta
  sporchi=$(grep -rl --binary-files=text -e "$2" "$prof" 2>/dev/null | wc -l)
  echo "    -- il profilo di questo giro conteneva la parola in $sporchi file"
  echo "       (il frammento resta nella sessione salvata del browser: e' il"
  echo "        limite dichiarato della cura).  Il profilo si butta adesso."
  rm -rf "$prof"
  # ⛔ E la cancellazione si VERIFICA — DUE VOLTE, a distanza.  «Non c'e' piu'»
  #    guardato nell'istante stesso in cui si cancella e' proprio quel che
  #    nascondeva la corsa: la prima volta il controllo passava, e sei secondi
  #    dopo il file era tornato.  ⭐ Il secondo sguardo, cinque secondi dopo, e'
  #    la differenza fra «l'ho cancellato» e «e' rimasto cancellato».
  sleep 5
  if [ -e "$prof" ]; then
    resta=$(find "$prof" -type f 2>/dev/null | wc -l)
    ko "⛔ il profilo $prof e' TORNATO ($resta file) 5 s dopo la cancellazione:"
    ko "   qualcuno lo sta ancora scrivendo, e la cura non ha tenuto"
    grep -rl --binary-files=text -e "$2" "$prof" 2>/dev/null | sed 's/^/        /'
  else
    ok "profilo buttato, e cinque secondi dopo il disco lo conferma ancora"
  fi

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
