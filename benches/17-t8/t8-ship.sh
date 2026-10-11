#!/usr/bin/env bash
#
# ⛔ HISTORY (10 Oct 2026, DECISIONI §10.36): this bench tests an installer that no longer exists —
#   separate plan/approve/apply, signed archive and install.sh, third-party repositories, firewall and
#   belts set by the engine, answer files. Today: one .run, `install` with the [y/N] question, and
#   REMOTIX that does not modify the system. It stays as the history of the tests of 29 Sep - 1 Oct 2026; the real
#   run is benches/17-distro/17-t10.sh. It is not launched.
# t8-ship.sh — carries the test archive and the T8 bench to the server, and starts the two HTTP servers.
#
#   (on the laptop)   [ARCHIVE_DIR=name PORT=n] bash benches/17-t8/t8-ship.sh [archive] [third-party]
#
#   /media/REMOTIX/vm17/$ARCHIVE_DIR/     the REMOTIX archive (ARCHIVE_DIR=archive), on 127.0.0.1:$PORT (8717;
#                                  from the VM: 10.0.2.2:$PORT). An archive of ITS OWN (for example the one from
#                                  packaging/release.sh: ARCHIVE_DIR=rilascio PORT=8737) does not touch the one
#                                  of T8, which other benches use
#   /media/REMOTIX/vm17/terzi/     the THIRD-PARTY archive of R18, on 127.0.0.1:8719
#   /media/REMOTIX/vm17/t8/        t8-vm.sh, t8-browser.py; t1c/17-t1c-look.sh updated
# ⚠ There is no rsync on the laptop: tar via ssh. The HTTP server is python3 -m http.server (read only).
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../.." && pwd)
A=${1:-$TREE/costruzione-uscita/archivio}
TZ_=${2:-$TREE/costruzione-uscita/t8-third-party/terzi}
S=nicfio@192.168.0.2
V=/media/REMOTIX/vm17
ARCHIVE_DIR=${ARCHIVE_DIR:-archivio}
PORT=${PORT:-8717}
tar -C "$A" -cf - . | ssh -o BatchMode=yes $S "rm -rf $V/$ARCHIVE_DIR.nuovo && mkdir -p $V/$ARCHIVE_DIR.nuovo $V/t8 && tar -C $V/$ARCHIVE_DIR.nuovo -xf - && rm -rf $V/$ARCHIVE_DIR && mv $V/$ARCHIVE_DIR.nuovo $V/$ARCHIVE_DIR"
if [ -d "$TZ_" ]; then
	tar -C "$TZ_" -cf - . | ssh -o BatchMode=yes $S "rm -rf $V/terzi && mkdir -p $V/terzi && tar -C $V/terzi -xf -"
fi
scp -q "$HERE/t8-vm.sh" "$HERE/t8-browser.py" $S:$V/t8/
scp -q "$TREE/benches/17-distro/17-t1c-look.sh" $S:$V/t1c/
# ⚠ two separate ssh calls: pkill -f on the same line as the starter finds ssh's shell and kills it;
#   [h] keeps it from finding itself
ssh -o BatchMode=yes $S "pkill -f '[h]ttp.server $PORT '; pkill -f '[h]ttp.server 8719 '" 2>&1 | grep -v tput || true
ssh -o BatchMode=yes $S "
for p in $PORT:$V/$ARCHIVE_DIR 8719:$V/terzi; do
	n=\${p%%:*}; d=\${p#*:}
	[ -d \$d ] && (setsid nohup python3 -m http.server \$n --bind 127.0.0.1 --directory \$d >$V/t8/http-\$n.log 2>&1 </dev/null &)
done
sleep 1
curl -s -o /dev/null -w 'archive ($ARCHIVE_DIR): %{http_code}\n' http://127.0.0.1:$PORT/chiavi/LEGGIMI
curl -s -o /dev/null -w 'third-party: %{http_code}\n' http://127.0.0.1:8719/terzi.asc" 2>&1 | grep -v tput
