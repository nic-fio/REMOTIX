#!/bin/bash
P=$(cat /srv/src/remotix.pid 2>/dev/null)
if [ -n "$P" ] && [ -d "/proc/$P" ]; then kill -TERM "$P"; sleep 1; [ -d "/proc/$P" ] && kill -KILL "$P"; echo "spento $P"; else echo "gia' spento"; fi
rm -f /srv/src/remotix.pid
