#!/bin/bash
#
# 04-b28-lancia.sh — il banco del MODO A TOCCO (anello A8 della fase 4).
#
#   bash banchi/04-b28-lancia.sh              certifica il giudice, poi gira
#   bash banchi/04-b28-lancia.sh --solo-certifica
#
# ---------------------------------------------------------------------------
# ⚠ LA SCENA, DICHIARATA — e si verifica dall'altro capo, non qui
#
# Il browser si apre sul desktop VERO dell'utente.  ⛔ Non si sposta su uno
# schermo finto per far tornare i conti: quel che la scena era davvero lo
# scrive il raccoglitore in ogni riga di `04-b28-esiti.jsonl`, letto
# dall'ambiente e dallo `userAgent` del browser — non da questa intestazione,
# che invecchierebbe in silenzio.
#
# ⛔ E IL TOCCO LO DICHIARA IL BANCO: `Emulation.setTouchEmulationEnabled`.
#    ⚠ Quel che se ne ricava e' l'EMULAZIONE, non un dito (`LEZIONI.md` §1.11):
#      da qui escono i confini del RICONOSCITORE — che sono deterministici — e
#      **nessun numero su come si comporta una mano vera**.  Il giudizio sui
#      gesti resta di Nic, con un dito.
#
# ⛔ PORTE 7671-7675, e sono le mie (mandato A8):
#     7671  il servitore del banco (serve `src/pagina.html` e raccoglie i byte)
#     7672  la porta di diagnosi di Chrome
#   Non si tocca 7448 · 7501 · 7561 · 7571, ne' le porte degli altri anelli.
#
# ⛔ E IL PROFILO DI CHROME E' NUOVO E SUO: un profilo condiviso con la sessione
#    dell'utente porterebbe dentro le sue schede, le sue estensioni e il suo
#    stato di permessi — cioe' una scena che cambia da un giro all'altro.
# ---------------------------------------------------------------------------
set -u

QUI="$(cd "$(dirname "$0")" && pwd)"
RADICE="$(dirname "$QUI")"
PORTA=7671
DIAGNOSI=7672
PROFILO="/tmp/04-b28-profilo"
REGISTRO="$QUI/04-b28-registro.jsonl"

cd "$RADICE" || exit 2

echo "══ 1. IL GIUDICE SI CERTIFICA PRIMA DELLA MISURA (CODER.md §3.3) ══"
python3 "$QUI/04-b28-gesti.py" --certifica
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
echo "  ⚠ la finestra si apre sul desktop VERO, e il tocco e' DICHIARATO dal"
echo "    banco (CDP): quel che si misura sono i confini del riconoscitore."

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
python3 "$QUI/04-b28-gesti.py" --gira --porta "$PORTA" \
        --diagnosi "$DIAGNOSI" --registro "$REGISTRO"
ESITO=$?

echo
echo "══ 5. DOVE SI RICONTROLLA ══"
echo "  esiti     $QUI/04-b28-esiti.jsonl"
echo "  registro  $REGISTRO   (i byte, in esadecimale, gesto per gesto)"
echo "  rigiudica python3 banchi/04-b28-gesti.py --verdetto $REGISTRO"
exit "$ESITO"
