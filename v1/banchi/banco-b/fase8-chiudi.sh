#!/bin/bash
set -u
pkill -x xfreerdp3 2>/dev/null
pkill -f '^Xvfb :110' 2>/dev/null
sleep 1
echo "   banco del contenitore sgombrato"
