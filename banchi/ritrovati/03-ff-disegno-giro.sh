cd /home/nicfio/Documenti/REMOTIX
for motore in chrome firefox; do
  for f in "--con-finestra" ""; do
    echo ""; echo "═══════════ disegno/$motore/$([ -n "$f" ] && echo finestra || echo headless) ═══════════"
    python3 banchi/03-ff-disegno.py "$motore" 3 --porta 8875 --schermo :75 --pezzi 120 $f
    echo "   ⇒ uscita $?"; sleep 3
  done
done
echo "== fine disegno"
