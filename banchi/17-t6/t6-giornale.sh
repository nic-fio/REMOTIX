#!/bin/bash
# t6-giornale.sh — (inside the VM, as root) the REMOTIX lines that matter for T6, from "dal" onwards:
# child, PAM, session, stage, the ⛔; once only (the journal has them twice: text and fields).
#   bash t6-giornale.sh [dal]     e.g. "-10min", "07:27:00"
dal=${1:--10min}
journalctl -b --no-pager -o cat --since "$dal" _COMM=remotix + SYSLOG_IDENTIFIER=remotix + _COMM=remotix-figlio 2>/dev/null \
	| grep -aE '^[0-9]{2}:[0-9]{2}' \
	| grep -avE ' (rcp|budget|quic|cert) ' \
	| grep -aE 'figlio|child|PAM|pam|sessione|session|stage|⛔|admitted|refus|denied|ban|SELinux|context|exit|state' \
	| grep -av 'guardiano: chiamate' | cut -c1-260 | tail -${RIGHE:-40}
echo "--- pam and audit (remotix service):"
journalctl -b --no-pager -o cat --since "$dal" 2>/dev/null | grep -aE 'remotix' | grep -aE 'pam_|AUDIT(1100|1101|1105|2300)|faillock|avc' | cut -c1-260 | tail -12
