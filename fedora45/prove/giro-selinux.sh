#!/bin/bash
# giro-selinux.sh <gnome|kde|xfce|lxqt> [--extra] - the automatic checks of the SELinux step (step 5, 22 Nov 2026) on ONE VM, with the Radeon.
# Run ON THE DEV SERVER, from prove/, with the VM switched on WITH the card, the package installed and the service enabled; SELinux enforcing, the
# policy as the package leaves it (no `permissive`, dontaudit NOT disabled).  Prints PASS/FAIL/BLOCKED lines; the AVCs are looked at afterwards
# (`ausearch -m avc,user_avc,selinux_err -ts <start>`, the START line says when).
#   gnome, kde:  base, input, lifecycle, clipboard, audio, desktop, (kde: birth, live, resize, exit | gnome: resize), prelocal
#   xfce, lxqt:  giro-<de>-radeon.sh (the same plus the real local-login tests with lightdm / sddm; user lc1 must exist)
#   --extra:     multiuser, media, resilience, phone, ban (the rest of all.sh)
# Failures that are the same WITHOUT the SELinux wall (found by running them on the packages l6 / k4b): see docs/REGISTRO-problemi.md F29.
cd "$(dirname "$0")" || exit 2
export RX_BANCO=vm RX_TEMPO=2
B=${1:?usage: giro-selinux.sh gnome|kde|xfce|lxqt [--extra]}
echo "START $(date +%T)"
run() { echo "== $*"; timeout 1500 "$@" --box $B 2>&1 | grep -aE "^(PASS|FAIL|BLOCKED|RESULT)" | cut -c1-260; }
case $B in
gnome|kde)
  run python3 check-base.py --browser chrome
  run python3 check-input.py
  run python3 check-lifecycle.py
  run python3 check-clipboard.py
  run python3 check-audio.py
  run python3 check-desktop.py
  if [ $B = kde ]; then
    for k in check-kde-birth check-kde-live check-kde-resize check-kde-exit; do run python3 $k.py; done
  else
    run python3 check-resize.py --rounds 5
  fi
  run python3 check-prelocal.py
  ;;
xfce|lxqt)
  sh giro-$B-radeon.sh 2>&1 | cut -c1-260
  ;;
esac
if [ "${2:-}" = --extra ]; then
  for c in check-multiuser check-media check-resilience check-phone check-ban; do run python3 $c.py; done
fi
echo "END $(date +%T)"
