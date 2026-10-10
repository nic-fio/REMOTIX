#!/bin/bash
# 19-nvidia.sh — the bench of the rented NVIDIA machine, driven FROM THE LAPTOP.
#
#   bash banchi/19-nvidia/19-nvidia.sh prepara           # BEFORE the rental: the suitcase
#   bash banchi/19-nvidia/19-nvidia.sh tutto IP          # sends, starts, follows (reboot included), collects
#   bash banchi/19-nvidia/19-nvidia.sh pulisci IP        # AFTER collecting: the machine as found
#
#   and piece by piece:  manda IP · avvia IP [STEP] · segui IP · stato IP · raccogli IP · entra IP
#
# Variables: UTENTE (root; a user with passwordless "sudo" is fine: ubuntu, debian, admin),
# PORTA_SSH (22), CHIAVE (an ssh key file), CONTENITORE=name (the LOCAL test: podman exec
# instead of ssh, for the steps that do not touch the GPU — see 19-nv-prova-contenitore.sh).
#
# The suitcase (`prepara`) lives in costruzione-uscita/19-nvidia/ (ignored by git): the REMOTIX .debs
# for Debian 13 and Ubuntu 26.04 built from THIS tree (run it from a checkout of
# `fase-19`), the installer, and the benches needed on the machine.  The evidence comes back to
# misure/19-nvidia/.
set -u
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
USCITA=${USCITA:-$ALBERO/costruzione-uscita}
VAL=$USCITA/19-nvidia
MISURE=$ALBERO/misure/19-nvidia
LONTANO=/opt/remotix-nv
LAVORO=/var/lib/remotix-nv
UNITA=remotix-nv-banco
UTENTE=${UTENTE:-root}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
log() { printf '\n\033[1m== %s · %s\033[0m\n' "$(date +%H:%M:%S)" "$*"; }

# ── the road to the machine: ssh, or podman exec for the local test ──────────────────────────
PRE=""
[ "$UTENTE" != root ] && PRE="sudo -n"
lontano() {  # lontano 'command' — runs as root on the machine (the command travels on stdin:
	#             no quotes to escape, whatever the login shell is)
	if [ -n "${CONTENITORE:-}" ]; then
		printf '%s\n' "$1" | podman exec -i "$CONTENITORE" bash -s
	else
		printf '%s\n' "$1" | ssh -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 -o ConnectTimeout=15 \
			${CHIAVE:+-i "$CHIAVE"} -p "${PORTA_SSH:-22}" "$UTENTE@$IP" "$PRE bash -s"
	fi
}

serve_ip() {
	IP=${1:-}
	[ -n "$IP" ] || [ -n "${CONTENITORE:-}" ] || { echo "the machine's address is required"; exit 2; }
	IP=${IP:-contenitore}
}

# ═══════════════════════════════════════════════════════════════════════════
prepara() {
	log "prepara: the suitcase (before the rental, on the laptop)"
	command -v podman >/dev/null || { ko "podman is required"; exit 2; }
	local ramo hash sporco=""
	ramo=$(git -C "$ALBERO" rev-parse --abbrev-ref HEAD)
	hash=$(git -C "$ALBERO" rev-parse --short HEAD)
	[ -n "$(git -C "$ALBERO" status --porcelain -- src packaging installatore banchi)" ] && sporco="+modifiche"
	[ "$ramo" = fase-19 ] || echo "    ⚠ the branch is \"$ramo\", not fase-19: the suitcase carries $hash$sporco, and says so"
	rm -rf "$VAL/valigia"
	mkdir -p "$VAL/valigia/pacchetti" "$VAL/valigia/bin" "$VAL/valigia/albero"
	log "the REMOTIX .debs (src/costruzione/costruisci-deb.sh debian13 ubuntu2604)"
	if ! USCITA=$USCITA bash "$ALBERO/src/costruzione/costruisci-deb.sh" debian13 ubuntu2604 > "$VAL/costruisci-deb.log" 2>&1; then
		ko "costruisci-deb.sh failed ($VAL/costruisci-deb.log)"; tail -n 5 "$VAL/costruisci-deb.log"; exit 1
	fi
	cp "$USCITA"/deb-debian13/remotix_*.deb "$USCITA"/deb-ubuntu2604/remotix_*.deb "$VAL/valigia/pacchetti/" \
		|| { ko "the .debs are missing"; exit 1; }
	grep -h . "$USCITA"/deb-*/controlli.txt 2>/dev/null | sed 's/^/      /'
	ok "$(ls "$VAL/valigia/pacchetti" | tr '\n' ' ')"
	log "the installer (installatore/costruisci.sh)"
	bash "$ALBERO/installatore/costruisci.sh" > "$VAL/costruisci-installatore.log" 2>&1 \
		|| { ko "installer not built ($VAL/costruisci-installatore.log)"; exit 1; }
	cp "$ALBERO/installatore/uscita/remotix-install" "$VAL/valigia/bin/"
	ok "remotix-install $("$VAL/valigia/bin/remotix-install" version 2>/dev/null)"
	log "the benches (like 15-porta.sh) and the sources for bench 19"
	albero_in_valigia
	{
		echo "$hash$sporco ($ramo) · $(git -C "$ALBERO" log -1 --format='%cd %s' --date=short HEAD | cut -c1-120)"
		echo "prepared: $(date -Is) on $(hostname)"
		(cd "$VAL/valigia" && sha256sum pacchetti/*.deb bin/remotix-install)
	} > "$VAL/valigia/VERSIONE"
	tar -C "$VAL/valigia" -czf "$VAL/valigia.tgz" .
	ok "suitcase: $VAL/valigia.tgz ($(du -h "$VAL/valigia.tgz" | cut -f1)) · $(head -1 "$VAL/valigia/VERSIONE")"
}

# the benches and sources of the CURRENT tree into the suitcase (not the packages)
albero_in_valigia() {
	rm -rf "$VAL/valigia/albero"
	mkdir -p "$VAL/valigia/albero"
	(
		cd "$ALBERO" || exit 1
		{
			ls banchi/*.py banchi/*.sh banchi/*.html banchi/*.js 2>/dev/null
			find banchi/11-scatole banchi/15-suite banchi/19-vulkan banchi/19-nvidia -type f ! -name '*.pyc' \
				! -path '*/__pycache__/*' ! -name '*registro*.jsonl' ! -name 'rapporto-*'
			find src -maxdepth 1 -type f
		} | tar -cf - -T - | tar -xf - -C "$VAL/valigia/albero"
	)
}

manda() {
	log "sending the suitcase to $IP"
	[ -f "$VAL/valigia.tgz" ] || { ko "the suitcase is missing: first \"$0 prepara\""; exit 1; }
	# ⛔ 5 Oct 2026: PROVE and BROWSER_SUITE added to the bench AFTER the suitcase did not arrive —
	#    `manda` shipped the benches from when the suitcase had been made, and the machine ran the
	#    whole suite. ⇒ The benches (not the packages) are refreshed from the tree at every `manda`,
	#    and the VERSIONE says so
	if [ -d "$VAL/valigia/pacchetti" ]; then
		albero_in_valigia
		sed -i '/^benches refreshed:/d' "$VAL/valigia/VERSIONE"
		echo "benches refreshed: $(date -Is) from $(git -C "$ALBERO" rev-parse --short HEAD)$( \
			[ -n "$(git -C "$ALBERO" status --porcelain -- banchi)" ] && echo +modifiche)" >> "$VAL/valigia/VERSIONE"
		tar -C "$VAL/valigia" -czf "$VAL/valigia.tgz" .
	fi
	if [ -n "${CONTENITORE:-}" ]; then
		podman exec "$CONTENITORE" mkdir -p "$LONTANO"
		podman exec -i "$CONTENITORE" tar -xzf - -C "$LONTANO" < "$VAL/valigia.tgz" || exit 1
	else
		ssh -o StrictHostKeyChecking=accept-new ${CHIAVE:+-i "$CHIAVE"} -p "${PORTA_SSH:-22}" "$UTENTE@$IP" \
			"$PRE rm -rf $LONTANO && $PRE mkdir -p $LONTANO && $PRE tar -xzf - -C $LONTANO" < "$VAL/valigia.tgz" || exit 1
	fi
	ok "$(lontano "head -1 $LONTANO/VERSIONE")"
}

avvia() {
	local p=${1:-tutto}
	log "starting \"$p\" on the machine (a systemd unit: ssh may drop)"
	if lontano "systemctl is-active --quiet $UNITA"; then ko "the bench is already running ($UNITA)"; return 1; fi
	lontano "mkdir -p $LAVORO && rm -f $LAVORO/uscita && echo '=== avvio $p $(date -Is)' >> $LAVORO/banco.log && \
		systemctl reset-failed $UNITA 2>/dev/null; \
		systemd-run --unit=$UNITA --collect --property=StandardOutput=append:$LAVORO/banco.log \
		--property=StandardError=append:$LAVORO/banco.log --setenv=FORZA=${FORZA:-0} --setenv=RIFAI='${RIFAI:-}' \
		--setenv=PROVE='${PROVE:-}' --setenv=BROWSER_SUITE='${BROWSER_SUITE:-}' --setenv=CLIENTE_SCHEDA='${CLIENTE_SCHEDA:-0}' --setenv=DESKTOP_NV='${DESKTOP_NV:-xfce}' \
		/bin/bash $LONTANO/albero/banchi/19-nvidia/19-nv-macchina.sh $p" \
		&& ok "started"
}

# follows the log until the bench writes its exit code; returns that exit code
segui() {
	log "following the bench (Ctrl-C does not stop it: run \"segui\" again)"
	local da=0 righe u
	da=$(lontano "wc -l < $LAVORO/banco.log" 2>/dev/null || echo 0)
	da=$(( ${da:-0} > 40 ? da - 40 : 0 ))
	while :; do
		righe=$(lontano "tail -n +$((da + 1)) $LAVORO/banco.log 2>/dev/null")
		if [ -n "$righe" ]; then
			printf '%s\n' "$righe"
			da=$((da + $(printf '%s\n' "$righe" | wc -l)))
		fi
		if ! lontano "systemctl is-active --quiet $UNITA" 2>/dev/null; then
			u=$(lontano "cat $LAVORO/uscita 2>/dev/null")
			[ -n "$u" ] && { log "the bench has finished: exit $u"; return "$u"; }
			# ssh dropped or machine rebooting: retry
			lontano true 2>/dev/null || { sleep 20; continue; }
			log "the bench is not running and has not written its exit code (stopped by hand?)"; return 3
		fi
		sleep 20
	done
}

aspetta_ssh() {
	local i
	for i in $(seq 1 60); do
		sleep 15
		lontano true >/dev/null 2>&1 && { ok "the machine answers"; return 0; }
	done
	ko "after 15 minutes the machine does not answer"; return 1
}

raccogli() {
	log "collecting the evidence archive"
	lontano "bash $LONTANO/albero/banchi/19-nvidia/19-nv-macchina.sh raccogli" | tail -n 3
	local nome sha
	nome=$(lontano "cat $LAVORO/archivio")
	sha=$(lontano "cat $LAVORO/archivio.sha256")
	[ -n "$nome" ] || { ko "no archive"; return 1; }
	mkdir -p "$MISURE"
	lontano "cat $LAVORO/$nome" > "$MISURE/$nome"
	if [ "$(sha256sum "$MISURE/$nome" | cut -d' ' -f1)" = "$sha" ]; then
		lontano "touch $LAVORO/raccolto"
		ok "$MISURE/$nome (sha256 equal)"
		tar -xzf "$MISURE/$nome" -O evidenze/passi.txt 2>/dev/null | sed 's/^/      /'
	else
		ko "sha256 differs: run \"raccogli\" again"; return 1
	fi
}

pulisci() {
	log "cleaning the machine"
	lontano "FORZA=${FORZA:-0} bash $LONTANO/albero/banchi/19-nvidia/19-nv-macchina.sh pulisci" || return 1
	lontano "rm -rf $LONTANO $LAVORO" && ok "suitcase and work folder removed"
	lontano "cat /run/reboot-required 2>/dev/null; true"
}

tutto() {
	manda
	avvia tutto || exit 1
	segui; local u=$? n=0
	# more than one reboot (5 Oct 2026): the Ubuntu upgrade asks for one per hop, the driver one
	while [ "$u" = 10 ] && [ $n -lt 10 ]; do
		n=$((n + 1))
		log "the bench asks for a REBOOT ($n; upgrade/driver/ICD/modeset): rebooting and resuming"
		[ -n "${CONTENITORE:-}" ] && { ko "a container cannot be rebooted"; exit 1; }
		lontano "systemctl reboot" || true
		aspetta_ssh || exit 1
		avvia tutto || exit 1
		segui; u=$?
	done
	raccogli
	log "END: exit $u · the evidence in $MISURE · the cleanup: \"$0 pulisci $IP\""
	return "$u"
}

AZIONE=${1:-}
case "$AZIONE" in
prepara) prepara ;;
manda|segui|raccogli|pulisci|tutto) serve_ip "${2:-}"; "$AZIONE" ;;
avvia) serve_ip "${2:-}"; avvia "${3:-tutto}" ;;
stato) serve_ip "${2:-}"; lontano "bash $LONTANO/albero/banchi/19-nvidia/19-nv-macchina.sh stato" ;;
entra) serve_ip "${2:-}"; ssh ${CHIAVE:+-i "$CHIAVE"} -p "${PORTA_SSH:-22}" "$UTENTE@$IP" ;;
*) sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
