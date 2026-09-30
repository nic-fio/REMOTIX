#!/bin/bash
# t6-giornale.sh — (dentro la VM, da root) le righe di REMOTIX che contano per T6, dal «dal» in poi:
# figlio, PAM, sessione, palco, i ⛔; una volta sola (il giornale le ha doppie: testo e campi).
#   bash t6-giornale.sh [dal]     es. «-10min», «07:27:00»
dal=${1:--10min}
journalctl -b --no-pager -o cat --since "$dal" _COMM=remotix + SYSLOG_IDENTIFIER=remotix + _COMM=remotix-figlio 2>/dev/null \
	| grep -aE '^[0-9]{2}:[0-9]{2}' \
	| grep -avE ' (rcp|budget|quic|cert) ' \
	| grep -aE 'figlio|PAM|pam|sessione|palco|⛔|ammess|rifiut|negat|ban|SELinux|contesto|exit|uscit|stato' \
	| grep -av 'guardiano: chiamate' | cut -c1-260 | tail -${RIGHE:-40}
echo "--- pam e audit (servizio remotix):"
journalctl -b --no-pager -o cat --since "$dal" 2>/dev/null | grep -aE 'remotix' | grep -aE 'pam_|AUDIT(1100|1101|1105|2300)|faillock|avc' | cut -c1-260 | tail -12
