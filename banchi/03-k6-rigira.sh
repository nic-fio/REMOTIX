#!/bin/bash
# ⭐ K6 — IL RIGIRATORE DELLE CERTIFICAZIONI SCADUTE
#
# ⛔ Nasce il 13 agosto 2026, notte, e nasce da una confusione vera: `bash
#    03-b17-lancia.sh certifica` stampa «PROMOSSO 54 su 54» e **non certifica
#    niente a catalogo**.  Sono due cose diverse con lo stesso nome:
#
#      l'AUTOPROVA del banco   — «i miei controlli sanno dire di no ai miei
#                                 verbali guasti?»  ⇒ la stampa il banco
#      la CERTIFICAZIONE       — «il banco diventa rosso quando gli si innesta
#                                 dentro il guasto DEL CATALOGO, e torna verde
#                                 quando lo si toglie?»  ⇒ la registra B12
#
#    ⚠ Chi legge «PROMOSSO» e crede di aver rigirato K6 lascia la riga scaduta
#      e non se ne accorge: `--registro` continuera' a dirlo, ma solo se lo si
#      guarda.
#
# uso:  bash banchi/03-k6-rigira.sh <SIGLA> <comando che fa il giro...>
#
# Il comando si esegue **tre volte** — sano, guasto, risanato — e il suo codice
# d'uscita e la sua marca finiscono negli esiti.  ⛔ La copia la prepara e la
# rimette a posto `01-b12-guasti.py`, e l'originale si riverifica per impronta
# alla fine: «tolto» si MISURA.
set -u
QUI="$(cd "$(dirname "$0")" && pwd)"
CAT="$QUI/01-b12-guasti.py"
SIGLA="${1:?serve la sigla del banco}"
shift
[ $# -ge 1 ] || { echo "⛔ serve anche il comando che fa il giro"; exit 2; }

rosso () { printf '\033[1;31m%s\033[0m\n' "$*"; }
verde () { printf '\033[1;32m%s\033[0m\n' "$*"; }

MARCA="$(python3 "$CAT" --marca "$SIGLA")"
[ -n "$MARCA" ] || { rosso "⛔ il catalogo non da' una marca per $SIGLA — e senza marca un rosso non attribuisce niente"; exit 2; }
ATTESO="$(python3 - "$CAT" "$SIGLA" <<'PY'
import importlib.util, sys
s = importlib.util.spec_from_file_location("cat", sys.argv[1])
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print(m.GUASTI[sys.argv[2]]["atteso_sano"])
PY
)"
echo "   banco $SIGLA · marca attesa nel rosso: «$MARCA» · atteso sano: $ATTESO"

COMANDO=("$@")

# ⛔⛔ LA GUARDIA CHE MANCAVA, E MI HA GIA' MORSO — 13 agosto 2026, notte.
#
#    La prima versione di questo rigiratore ha lanciato `03-b17-lancia.sh
#    certifica`, cioe' **l'ORIGINALE**, mentre il guasto stava nella COPIA in
#    `01-b12-copie/`.  ⇒ Il giro «guasto» e' uscito **0 senza marca**, il
#    catalogo ha scritto «provato e NON certificato», e quel rosso era **falso**:
#    il guasto non era mai stato in gioco.
#    ⚠ E' la trappola n.2 del catalogo, quella che il catalogo stesso descrive,
#      fatta dallo strumento scritto per rigirare le certificazioni.
#
#  ⇒ Adesso il rigiratore **pretende che il comando nomini il file guastato**,
#    e se non lo nomina **si rifiuta di partire** invece di consegnare un rosso
#    che non attribuisce niente.
DOVE="$(python3 - "$CAT" "$SIGLA" <<'PY'
import importlib.util, os, sys
s = importlib.util.spec_from_file_location("cat", sys.argv[1])
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print(os.path.basename(os.path.realpath(m.GUASTI[sys.argv[2]]["dove"])))
PY
)"
if ! printf '%s ' "${COMANDO[@]}" | grep -qF "01-b12-copie"; then
  rosso "⛔ il comando NON passa da 01-b12-copie/, dove sta il guasto:"
  rosso "     ${COMANDO[*]}"
  rosso "   ⇒ girerebbe l'ORIGINALE col guasto fermo in una cartella che nessuno"
  rosso "     legge: il banco resterebbe verde e la riga direbbe «non e' diventato"
  rosso "     rosso» di un guasto MAI INNESTATO. Mi rifiuto."
  rosso "   Il file guastato e': $DOVE"
  exit 2
fi

ESITI="$QUI/03-k6-esiti-$SIGLA.jsonl"
: > "$ESITI"

giro () {
  passo="$1"
  echo "== PASSO $passo"
  # ⛔ Il comando si prende da COMANDO e NON dagli argomenti di questa funzione:
  #    `giro sano` passa «sano» come $1, e un `"$@"` qui dentro eseguirebbe
  #    «sano» come se fosse il banco.
  testo="$( "${COMANDO[@]}" 2>&1 </dev/null )"
  u=$?
  vista=false
  printf '%s' "$testo" | grep -qF "$MARCA" && vista=true
  echo "   uscita $u · marca vista: $vista"
  printf '{"sigla":"%s","passo":"%s","uscita":%d,"marca_vista":%s}\n' \
      "$SIGLA" "$passo" "$u" "$vista" >> "$ESITI"
}

giro sano
giro_sano_uscita=$(python3 -c "import json,sys;print(json.loads(open('$ESITI').read().splitlines()[0])['uscita'])")
if [ "$giro_sano_uscita" != "$ATTESO" ]; then
  rosso "⛔ il giro SANO esce $giro_sano_uscita e ne era atteso $ATTESO"
  rosso "   ⇒ NON si innesta niente: un guasto su uno stato di partenza sbagliato non dimostra nulla."
  exit 2
fi

python3 "$CAT" --applica "$SIGLA" | sed 's/^/   /' || { rosso "⛔ innesto fallito"; exit 2; }
giro guasto
python3 "$CAT" --togli "$SIGLA" | sed 's/^/   /' || { rosso "⛔ il guasto NON si e' tolto — ⛔ ALBERO SPORCO"; exit 2; }
giro risano

CARICO="$(cut -d' ' -f1-3 /proc/loadavg)"
PORTE="$(ss -ltn 2>/dev/null | grep -oE ':7[0-9]{3}' | sort -u | tr '\n' ' ')"
echo
python3 "$CAT" --giudica "$ESITI" \
    --scena "K6 — 13 agosto 2026 notte, CHUWI, rigirata a prodotto FERMO dopo la \
cura delle sonde di src/pagina.html. Comando: ${COMANDO[*]}. \
CARICO al giudizio: $CARICO — porte 7xxx viste: ${PORTE:-nessuna}. \
⛔ 7448, 7501 e 7561 non toccate."
