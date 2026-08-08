#!/bin/bash
# Chiude Firefox mentre il client sta fotografando.
sleep 2
pkill -x firefox 2>/dev/null || pkill -f firefox-esr 2>/dev/null
echo "firefox chiuso"
