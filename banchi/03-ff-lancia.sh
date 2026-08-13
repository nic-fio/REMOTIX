#!/bin/bash
# ⭐ CORSIA D — la campagna intera, e ⛔ **UNA CONFIGURAZIONE ALLA VOLTA**.
#
# ⛔ Non e' comodita': due giri in parallelo si misurerebbero a vicenda su una
#    macchina a 4 nuclei, e i numeri avrebbero lo stesso aspetto di quelli buoni
#    (§0-bis del piano, e due giri di griglia gia' buttati cosi' il 13 agosto).
#
# ⭐ E le quattro configurazioni non sono un ventaglio di comodo: sono le due
#    variabili del palco incrociate — **motore** (Firefox / Chrome) per
#    **finestra** (con finestra su Xvfb / `--headless`) — perche' il 13 agosto
#    una bandiera del banco ha deciso l'esito di una domanda sul motore.
#
# ⛔ Porte 8870-8879, schermi :70 in su.  Le protette 7448 · 7501 · 7561 si
#    contano dentro ogni banco, prima e dopo.
set -u
cd "$(dirname "$0")/.." || exit 1
GIRI="${GIRI:-3}"
PEZZI="${PEZZI:-120}"
echo "== CORSIA D — campagna del $(date '+%F %T')  ·  $GIRI giri, $PEZZI pezzi"

for banco in decodifica disegno; do
  if [ "$banco" = decodifica ]; then P0=8870; S0=70; else P0=8875; S0=75; fi
  for motore in chrome firefox; do
    for finestra in "--con-finestra" ""; do
      etichetta="$banco/$motore/$([ -n "$finestra" ] && echo finestra || echo headless)"
      echo ""
      echo "═══════════ $etichetta ═══════════"
      python3 "banchi/03-ff-$banco.py" "$motore" "$GIRI" \
              --porta "$P0" --schermo ":$S0" --pezzi "$PEZZI" $finestra
      echo "   ⇒ uscita $?"
      # ⚠ Le porte restano le stesse perche' i giri sono in SERIE e ogni giro
      #   chiude il suo servitore e spegne il suo Xvfb.  ⛔ Restano dentro
      #   8870-8879, che e' la fascia della corsia D.
      sleep 3
    done
  done
done
echo ""
echo "== fine campagna $(date '+%F %T')"
