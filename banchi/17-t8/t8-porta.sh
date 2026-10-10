#!/usr/bin/env bash
#
# ⛔ HISTORY (10 Oct 2026, DECISIONI §10.36): this bench tests an installer that no longer exists —
#   separate plan/approve/apply, signed archive and install.sh, third-party repositories, firewall and
#   belts set by the engine, answer files. Today: one .run, `install` with the [y/N] question, and
#   REMOTIX that does not modify the system. It stays as the history of the tests of 29 Sep - 1 Oct 2026; the real
#   run is banchi/17-distro/17-t10.sh. It is not launched.
# t8-porta.sh — carries the test archive and the T8 bench to the server, and starts the two HTTP servers.
#
#   (on the laptop)   [DOVE=name PORT=n] bash banchi/17-t8/t8-porta.sh [archive] [third-party]
#
#   /media/REMOTIX/vm17/$DOVE/     the REMOTIX archive (DOVE=archive), on 127.0.0.1:$PORT (8717;
#                                  from the VM: 10.0.2.2:$PORT). An archive of ITS OWN (for example the one from
#                                  packaging/rilascio.sh: DOVE=rilascio PORT=8737) does not touch the one
#                                  of T8, which other benches use
#   /media/REMOTIX/vm17/terzi/     the THIRD-PARTY archive of R18, on 127.0.0.1:8719
#   /media/REMOTIX/vm17/t8/        t8-vm.sh, t8-browser.py; t1c/17-t1c-guarda.sh updated
# ⚠ There is no rsync on the laptop: tar via ssh. The HTTP server is python3 -m http.server (read only).
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../.." && pwd)
A=${1:-$TREE/costruzione-uscita/archivio}
TZ_=${2:-$TREE/costruzione-uscita/t8-terzi/third_party}
S=nicfio@192.168.0.2
V=/media/REMOTIX/vm17
DOVE=${DOVE:-archivio}
PORT=${PORT:-8717}
tar -C "$A" -cf - . | ssh -o BatchMode=yes $S "rm -rf $V/$DOVE.fresh && mkdir -p $V/$DOVE.fresh $V/t8 && tar -C $V/$DOVE.fresh -xf - && rm -rf $V/$DOVE && mv $V/$DOVE.fresh $V/$DOVE"
if [ -d "$TZ_" ]; then
	tar -C "$TZ_" -cf - . | ssh -o BatchMode=yes $S "rm -rf $V/third_party && mkdir -p $V/third_party && tar -C $V/third_party -xf -"
fi
scp -q "$HERE/t8-vm.sh" "$HERE/t8-browser.py" $S:$V/t8/
scp -q "$TREE/banchi/17-distro/17-t1c-guarda.sh" $S:$V/t1c/
# ⚠ two separate ssh calls: pkill -f on the same line as the starter finds ssh's shell and kills it;
#   [h] keeps it from finding itself
ssh -o BatchMode=yes $S "pkill -f '[h]ttp.server $PORT '; pkill -f '[h]ttp.server 8719 '" 2>&1 | grep -v tput || true
ssh -o BatchMode=yes $S "
for p in $PORT:$V/$DOVE 8719:$V/third_party; do
	n=\${p%%:*}; d=\${p#*:}
	[ -d \$d ] && (setsid nohup python3 -m http.server \$n --bind 127.0.0.1 --directory \$d >$V/t8/http-\$n.log 2>&1 </dev/null &)
done
sleep 1
curl -s -o /dev/null -w 'archive ($DOVE): %{http_code}\n' http://127.0.0.1:$PORT/keys/LEGGIMI
curl -s -o /dev/null -w 'third-party: %{http_code}\n' http://127.0.0.1:8719/third_party.asc" 2>&1 | grep -v tput
