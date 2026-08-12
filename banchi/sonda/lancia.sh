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

# ⛔⭐ E CHE LA CURA DI D12 ABBIA CHIUSO NON SI CREDE: SI GUARDA IN `ps`.
#
# `LEZIONI.md` §1.9: «non l'ho trovata» e «non ho guardato» hanno lo stesso
# aspetto, e la prova qui e' un'**ASSENZA** — che si dimostra solo con accanto
# un denominatore che dica «lo strumento, in quell'istante, stava guardando».
# ⇒ Il secondo ago e' il PERCORSO DEL PROFILO, che in `argv` c'e' di sicuro
#   (`--profile "$prof"`): se sparisse anche quello, lo zero della parola
#   varrebbe «non ho guardato» e non «non c'era».
#
# ⛔ E IL GUARDIANO NON DEVE CREARE IL DIFETTO CHE CERCA: `ps` si legge in una
#    variabile e il confronto lo fa **bash**.  Un `grep "$parola"` metterebbe la
#    parola nell'`argv` del `grep`, e il guardiano sarebbe la falla.
guardia_ps() # $1 = ago che NON deve comparire · $2 = ago che DEVE comparire
{
  local i righe uno=0 due=0
  for i in $(seq 1 40); do
    righe=$(ps -ww -eo args)
    [ -n "$1" ] && case "$righe" in *"$1"*) uno=$((uno + 1)) ;; esac
    [ -n "$2" ] && case "$righe" in *"$2"*) due=$((due + 1)) ;; esac
    sleep 0.25
  done
  printf '%s %s\n' "$uno" "$due" > "$QUI/guardia-ps"
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

  # ⛔⭐ LA TERZA META' DELLA CURA DEL FRAMMENTO — difetto **D12**, 12 agosto
  #     2026, e qui la forma e' DIVERSA da quella di tutti gli altri banchi.
  #
  # Negli altri la parola era un `--parola` da togliere.  ⛔ Qui sta **dentro
  # l'indirizzo**, e l'indirizzo si dava a `firefox` come argomento: finiva
  # nell'`argv` di `setsid`, in quello di `xvfb-run` e in quello di `firefox`,
  # cioe' in `/proc/<pid>/cmdline`, che su Linux e' leggibile da chiunque.
  #
  # ⚠ E questa e' la falla che le prime due meta' NON toccavano, ed e' la
  #   ragione per cui vale la pena scriverlo qui: R12-A.34 ha spostato la parola
  #   dalla query al frammento — cioe' fuori dai registri HTTP — e l'ha tolta
  #   dal terminale, e in tutto quel tempo `ps` continuava a stamparla intera.
  #   ⛔ Tre cure sullo stesso segreto, e la piu' facile da vedere era l'ultima.
  #
  # ⭐ LA CURA, e non poteva essere `--parola-file`: `firefox` non prende
  #    l'indirizzo da un file.  Lo prende pero' dal **proprio profilo** —
  #    `browser.startup.homepage` — e il profilo e' una cartella nostra, di
  #    questo giro, che questa stessa funzione butta e VERIFICA di aver buttato.
  #    ⇒ L'indirizzo passa da `user.js` (0600, in una cartella 0700) e
  #    `firefox` si lancia **senza nessun indirizzo fra gli argomenti**.
  #
  # ⚠ E si dichiara che cosa questa cura NON compra: la parola resta nel
  #   profilo, esattamente come gia' ci restava dentro `recovery.jsonlz4`.  Il
  #   conto dei file sporchi qui sotto SALIRA', ed e' giusto che salga — e' la
  #   verita' che si misurava gia' prima.  Quel che sparisce e' `ps`, che era
  #   l'unico posto dove a guardare bastava essere sulla macchina.
  #
  # ⛔ Le tre righe in piu' non sono ornamento: su un profilo NUOVO Firefox
  #    mostrerebbe la pagina di benvenuto invece della propria home, e la sonda
  #    resterebbe ad aspettare un esito che non arriva mai — che ha lo stesso
  #    aspetto di «il server non risponde».
  ( umask 077
    {
      printf 'user_pref("browser.startup.homepage", "%s");\n' "$U"
      printf 'user_pref("browser.startup.page", 1);\n'
      printf 'user_pref("browser.startup.firstrunSkipsHomepage", false);\n'
      printf 'user_pref("browser.startup.homepage_override.mstone", "ignore");\n'
      printf 'user_pref("browser.aboutwelcome.enabled", false);\n'
      printf 'user_pref("datareporting.policy.dataSubmissionEnabled", false);\n'
      printf 'user_pref("datareporting.policy.firstRunURL", "");\n'
    } > "$prof/user.js" ) || { ko "⛔ non si scrive $prof/user.js"; return 2; }
  chmod 700 "$prof"; chmod 600 "$prof/user.js"

  # ⚠ `setsid` mette Firefox e il suo Xvfb in un gruppo tutto loro, cosi' il
  #   TERM qui sotto puo' provare a prenderli in blocco.  ⛔ Ma e' un tentativo,
  #   non il criterio: il criterio e' `/proc`, e la ragione sta nella corsa
  #   raccontata piu' sotto.
  # ⛔ E NIENTE INDIRIZZO FRA GLI ARGOMENTI: e' la cura di D12 (qui sopra).
  rm -f "$QUI/guardia-ps"
  guardia_ps "$2" "$prof" &
  local pg=$!
  setsid xvfb-run -a firefox --no-remote --profile "$prof" \
      > "$QUI/ff-$1.log" 2>&1 &
  local p=$!
  local i=0
  while [ "$i" -lt 45 ]; do
    [ -s "$QUI/esiti.jsonl" ] && break
    sleep 1; i=$((i+1))
  done

  # ── ⛔ D12: la misura, con il suo denominatore ─────────────────────────────
  wait "$pg" 2>/dev/null
  local vp=0 vf=0
  if [ -r "$QUI/guardia-ps" ]; then
    vp=$(cut -d' ' -f1 "$QUI/guardia-ps"); vf=$(cut -d' ' -f2 "$QUI/guardia-ps")
  fi
  echo "    -- D12/ps: la PAROLA vista $vp volte · il PROFILO (che in argv c'e')"
  echo "       visto $vf volte"
  if [ "${vf:-0}" -lt 1 ]; then
    ko "⚠ non ho visto in «ps» nemmeno il profilo, che in «argv» c'era di"
    ko "  sicuro: allora lo zero della parola e' «non ho guardato», non «non"
    ko "  c'era».  ⛔ Non e' un verde, e si dichiara."
  elif [ "${vp:-1}" -gt 0 ]; then
    ko "⛔⛔ LA PAROLA E' ANCORA IN «ps» ($vp volte su $vf): D12 NON e' chiuso qui"
  else
    ok "⭐ D12 chiuso per misura: nello stesso istante «ps» vedeva il profilo"
    ok "   ($vf volte) e NON vedeva la parola"
  fi

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
