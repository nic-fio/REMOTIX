#!/bin/bash
#
# 04-b27-lancia.sh — il banco del MODO CLASSICO (anello A7 della fase 4).
#
#   bash banchi/04-b27-lancia.sh              certifica il giudice, poi gira
#   bash banchi/04-b27-lancia.sh --solo-certifica
#
# ---------------------------------------------------------------------------
# ⚠ LA SCENA, DICHIARATA — e si verifica dall'altro capo, non qui
#
# Il browser sta su CHUWI, sul desktop VERO dell'utente: `XDG_SESSION_TYPE` dice
# `wayland` e ⛔ **Chrome ignora `DISPLAY`**.  ⛔ NON si passa
# `--ozone-platform=x11`: curerebbe la scena distruggendo la misura.  ⇒ Quel che
# la scena era davvero lo scrive il raccoglitore in ogni riga di
# `04-b27-esiti.jsonl`, letto dall'ambiente e dallo `userAgent` del browser
# stesso — non da questa intestazione, che invecchierebbe in silenzio.
#
# ⛔ PORTE 7661-7665, e sono le mie (mandato A7):
#     7661  il servitore del banco (serve `src/pagina.html` e raccoglie i byte)
#     7662  la porta di diagnosi di Chrome
#   Non si tocca 7448 · 7501 · 7561 · 7571, ne' le porte degli altri anelli.
#
# ⛔ E IL PROFILO DI CHROME E' NUOVO E SUO: un profilo condiviso con la sessione
#    dell'utente porterebbe dentro le sue schede, le sue estensioni e il suo
#    stato di permessi — cioe' una scena che cambia da un giro all'altro.
# ---------------------------------------------------------------------------
set -u

QUI="$(cd "$(dirname "$0")" && pwd)"
RADICE="$(dirname "$QUI")"
PORTA=7661
DIAGNOSI=7662
PROFILO="/tmp/04-b27-profilo"
REGISTRO="$QUI/04-b27-registro.jsonl"

cd "$RADICE" || exit 2

echo "══ 1. IL GIUDICE SI CERTIFICA PRIMA DELLA MISURA (CODER.md §3.3) ══"
python3 "$QUI/04-b27-classico.py" --certifica
CERT=$?
if [ "$CERT" -ne 0 ]; then
  echo "⛔ il giudice non e' certificato: non si misura niente."
  exit 3
fi
if [ "${1:-}" = "--solo-certifica" ]; then exit 0; fi

echo
echo "══ 2. LA SCENA ══"
echo "  utente        $(id -un) (uid $(id -u))"
echo "  sessione      XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-?} "\
"WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-?} DISPLAY=${DISPLAY:-?}"
echo "  browser       $(google-chrome --version 2>&1)"
echo "  ⚠ la finestra si apre sul desktop VERO: e' quel che il mandato chiede,"
echo "    e il palco si verifica dall'altro capo (userAgent nel registro)."

for p in "$PORTA" "$DIAGNOSI"; do
  if ss -ltn 2>/dev/null | grep -q ":$p "; then
    echo "⛔ la porta $p e' gia' occupata: mi fermo invece di misurare la"
    echo "   pagina di qualcun altro."
    exit 4
  fi
done

rm -rf "$PROFILO"
mkdir -p "$PROFILO"

echo
echo "══ 3. CHROME ══"
google-chrome \
  --user-data-dir="$PROFILO" \
  --remote-debugging-port="$DIAGNOSI" \
  --remote-allow-origins='*' \
  --no-first-run --no-default-browser-check \
  --disable-features=Translate,MediaRouter \
  --window-size=1500,900 \
  "about:blank" >"$PROFILO/chrome.log" 2>&1 &
CHROME=$!
echo "  chrome pid $CHROME, diagnosi su $DIAGNOSI, profilo $PROFILO"

# ⛔ Il colpo di grazia e' registrato: se il banco muore, la finestra non resta
#    aperta sul desktop dell'utente.
trap 'kill "$CHROME" 2>/dev/null; wait "$CHROME" 2>/dev/null' EXIT

sleep 3

echo
echo "══ 4. LA MISURA ══"
python3 "$QUI/04-b27-classico.py" --gira --porta "$PORTA" \
        --diagnosi "$DIAGNOSI" --registro "$REGISTRO"
ESITO=$?

echo
echo "══ 5. DOVE SI RICONTROLLA ══"
echo "  esiti     $QUI/04-b27-esiti.jsonl"
echo "  registro  $REGISTRO   (i byte, in esadecimale, fase per fase)"
echo "  rigiudica python3 banchi/04-b27-classico.py --verdetto $REGISTRO"
exit "$ESITO"
