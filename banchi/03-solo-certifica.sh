#!/bin/bash
# ⭐ LA CERTIFICAZIONE DI `03-solo` — sano → guasto → risanato, e il verdetto
#    finisce in un file di esiti che `01-b12-guasti.py --giudica` sa leggere.
#
# ⛔ La copia si rifa' SEMPRE (ci pensa `--applica`), e l'impronta del file
#    originale si riverifica alla fine: «tolto» si MISURA, non si spera.
#
# ⚠ E il giro sano gira PER PRIMO: se la macchina non e' libera, `--prova`
#   esce 2 («non giudicabile») e questa certificazione si ferma li' invece di
#   scrivere un rosso che sarebbe della scena, non del banco.
set -u
QUI="$(cd "$(dirname "$0")" && pwd)"
CAT="$QUI/01-b12-guasti.py"
COPIA="$QUI/01-b12-copie/03-solo.py"
ESITI="${1:-$QUI/03-solo-esiti.jsonl}"

rosso () { printf '\033[1;31m%s\033[0m\n' "$*"; }
verde () { printf '\033[1;32m%s\033[0m\n' "$*"; }

# ⛔ La marca si LEGGE dal catalogo, non si ricopia qui: due verita' sulla
#    stessa stringa e' il modo in cui una marca invecchia in silenzio.
MARCA="$(python3 "$CAT" --marca 03-solo)"
[ -n "$MARCA" ] || { rosso "⛔ il catalogo non da' una marca per 03-solo"; exit 2; }
echo "   marca attesa nel rosso: «$MARCA»"

IMPRONTA_PRIMA="$(sha256sum "$QUI/03-solo.py" | cut -c1-16)"
echo "   03-solo.py prima: $IMPRONTA_PRIMA"

: > "$ESITI"

giro () {
  passo="$1"
  echo
  echo "== PASSO $passo"
  # ⛔ La copia si esegue DALLA COPIA: eseguire l'originale col guasto fermo in
  #    una cartella che nessuno legge e' la trappola n.2 di questo catalogo.
  uscita_testo="$(timeout 300 python3 "$COPIA" --prova 2>&1)"
  uscita=$?
  echo "$uscita_testo" | sed 's/^/      /'
  vista=false
  echo "$uscita_testo" | grep -qF "$MARCA" && vista=true
  echo "      ⇒ uscita $uscita · marca vista: $vista"
  printf '{"sigla":"03-solo","passo":"%s","uscita":%d,"marca_vista":%s}\n' \
      "$passo" "$uscita" "$vista" >> "$ESITI"
  # ⛔ E il numero se ne va per un canale SUO, non per stdout: la prima
  #    versione lo pescava con `| tail -1` e si portava dietro la riga di
  #    prosa «⇒ uscita 0 · marca vista: false», che non e' mai uguale a «2».
  #    ⇒ Il controllo «la scena era sporca?» non e' mai scattato, e il giro e'
  #    proseguito su un passo sano che non valeva niente.
  echo "$uscita" > "$QUI/.03-solo-ultimo"
}

python3 "$CAT" --applica 03-solo >/dev/null 2>&1 || true   # prepara la copia
python3 "$CAT" --togli 03-solo   >/dev/null 2>&1 || true   # e la rimette sana
python3 "$CAT" --applica 03-solo >/dev/null 2>&1 || true
python3 "$CAT" --togli 03-solo   >/dev/null 2>&1 || true

# ── SANO ───────────────────────────────────────────────────────────────────
python3 "$CAT" --verifica 03-solo >/dev/null 2>&1
giro sano
u_sano="$(cat "$QUI/.03-solo-ultimo")"
if [ "$u_sano" = "2" ]; then
  rosso "⛔ NON GIUDICABILE: al passo sano la macchina non era libera."
  rosso "   ⇒ Non e' un rosso del banco: e' una scena sporca. Si rifa' a macchina ferma."
  exit 2
fi

# ── GUASTO ─────────────────────────────────────────────────────────────────
python3 "$CAT" --applica 03-solo | sed 's/^/   /'
giro guasto
u_guasto="$(cat "$QUI/.03-solo-ultimo")"

# ── RISANATO ───────────────────────────────────────────────────────────────
python3 "$CAT" --togli 03-solo | sed 's/^/   /'
giro risano
u_risano="$(cat "$QUI/.03-solo-ultimo")"

echo
echo "== IL GIUDIZIO"
# ⛔⛔ LA SCENA SI MISURA, NON SI SCRIVE A MANO — e questa riga nasce da un
#    errore fatto qui dentro: il primo giro ha scritto in registro una scena
#    che NON diceva quanto fosse carica la macchina, mentre era carica al punto
#    da rendere il giro non giudicabile.  Una scena scritta a mano dice sempre
#    quel che chi l'ha scritta si aspettava.
CARICO="$(cut -d' ' -f1-3 /proc/loadavg)"
PORTE="$(ss -ltn 2>/dev/null | grep -oE ':7[0-9]{3}' | sort -u | tr '\n' ' ')"
python3 "$CAT" --giudica "$ESITI" \
    --scena "banco — CHUWI, nessuna rete e nessun prodotto: 03-solo.py --prova \
sulla propria copia 01-b12-copie/03-solo.py. Il vicino del passo 2 e' un processo \
Python che cicla, acceso e spento DAL BANCO STESSO. \
⭐ CARICO al giudizio: $CARICO — porte 7xxx viste: ${PORTE:-nessuna}. \
⛔ 7448, 7501 e 7561 non toccate (questo giro non apre nessuna porta)."
g=$?

IMPRONTA_DOPO="$(sha256sum "$QUI/03-solo.py" | cut -c1-16)"
echo "   03-solo.py dopo: $IMPRONTA_DOPO"
if [ "$IMPRONTA_PRIMA" != "$IMPRONTA_DOPO" ]; then
  rosso "⛔ l'ORIGINALE e' cambiato durante il giro: $IMPRONTA_PRIMA → $IMPRONTA_DOPO"
  exit 1
fi
verde "   ⭐ l'originale e' tornato identico byte per byte"
exit $g
