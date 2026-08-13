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
# ⛔ Di difetto i banchi RIFIUTANO di misurare se non sono soli (§0-bis del
#    piano).  Si toglie solo dichiarandolo: `ESIGI= bash 03-ff-lancia.sh`.
ESIGI="${ESIGI---esigi-solitudine}"
echo "== CORSIA D — campagna del $(date '+%F %T')  ·  $GIRI giri, $PEZZI pezzi"

# ⛔⛔ IL CANCELLO, e nasce da cinque rifiuti PAGATI la notte del 13 agosto.
#
# ⚠ Con la macchina libera e nessun altro agente in campo, cinque configurazioni
#   su otto si sono rifiutate di misurare: `carico a 1 minuto 1,29`, e ⛔ **il
#   vicino ero io**.  Il carico e' una media a un minuto: la configurazione
#   appena finita lascia una scia che l'arbitro legge come contesa — ed e'
#   esattamente il limite che `03-solo.py` dichiara di se' («non sa distinguere
#   il proprio rumore da quello d'altri»).
#
# ⭐ La cura NON e' alzare la soglia — quella e' la definizione di «solo» del
#   progetto e non e' mia da toccare.  E' **aspettare che la macchina sia
#   davvero ferma**, chiedendolo all'arbitro invece che a un `sleep` indovinato.
aspetta_di_essere_solo() {
  local t=0
  while [ "$t" -lt 300 ]; do
    if python3 banchi/03-solo.py > /dev/null 2>&1; then
      [ "$t" -gt 0 ] && echo "   ⏳ ho aspettato $t s che la MIA scia si spegnesse"
      return 0
    fi
    sleep 10; t=$((t + 10))
  done
  echo "   ⛔ 300 s e non sono ancora solo: lascio decidere al banco, che rifiutera'"
  return 1
}

for banco in decodifica disegno; do
  if [ "$banco" = decodifica ]; then P0=8870; S0=70; else P0=8875; S0=75; fi
  for motore in chrome firefox; do
    for finestra in "--con-finestra" ""; do
      etichetta="$banco/$motore/$([ -n "$finestra" ] && echo finestra || echo headless)"
      echo ""
      echo "═══════════ $etichetta ═══════════"
      # ⛔ Il cancello sta PRIMA della misura, non dopo: dopo sarebbe una
      #   consolazione, prima e' una condizione.
      aspetta_di_essere_solo
      python3 "banchi/03-ff-$banco.py" "$motore" "$GIRI" \
              --porta "$P0" --schermo ":$S0" --pezzi "$PEZZI" $finestra $ESIGI
      echo "   ⇒ uscita $?"
      # ⚠ Le porte restano le stesse perche' i giri sono in SERIE e ogni giro
      #   chiude il suo servitore e spegne il suo Xvfb.  ⛔ Restano dentro
      #   8870-8879, che e' la fascia della corsia D.
    done
  done
done
echo ""
echo "== fine campagna $(date '+%F %T')"
