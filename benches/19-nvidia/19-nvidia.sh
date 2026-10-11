#!/bin/bash
# 19-nvidia.sh — the bench of the rented NVIDIA machine, driven FROM THE LAPTOP.
#
#   bash benches/19-nvidia/19-nvidia.sh prepare           # BEFORE the rental: the suitcase
#   bash benches/19-nvidia/19-nvidia.sh all IP          # sends, starts, follows (reboot included), collects
#   bash benches/19-nvidia/19-nvidia.sh clean IP        # AFTER collecting: the machine as found
#
#   and piece by piece:  send IP · start IP [STEP] · follow IP · status IP · collect IP · enter IP
#
# Variables: ACCOUNT (root; a user with passwordless "sudo" is fine: ubuntu, debian, admin),
# SSH_PORT (22), SSH_KEY (an ssh key file), CONTAINER=name (the LOCAL test: podman exec
# instead of ssh, for the steps that do not touch the GPU — see 19-nv-test-in-container.sh).
#
# The suitcase (`prepare`) lives in costruzione-uscita/19-nvidia/ (ignored by git): the REMOTIX .debs
# for Debian 13 and Ubuntu 26.04 built from THIS tree (run it from a checkout of
# `fase-19`), the installer, and the benches needed on the machine.  The evidence comes back to
# misure/19-nvidia/.
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../.." && pwd)
OUTPUT=${OUTPUT:-$TREE/costruzione-uscita}
VAL=$OUTPUT/19-nvidia
SIZES=$TREE/misure/19-nvidia
FAR=/opt/remotix-nv
WORKDIR=/var/lib/remotix-nv
UNIT=remotix-nv-banco
ACCOUNT=${ACCOUNT:-root}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
log() { printf '\n\033[1m== %s · %s\033[0m\n' "$(date +%H:%M:%S)" "$*"; }

# ── the road to the machine: ssh, or podman exec for the local test ──────────────────────────
PRE=""
[ "$ACCOUNT" != root ] && PRE="sudo -n"
far() {  # far 'command' — runs as root on the machine (the command travels on stdin:
	#             no quotes to escape, whatever the login shell is)
	if [ -n "${CONTAINER:-}" ]; then
		printf '%s\n' "$1" | podman exec -i "$CONTAINER" bash -s
	else
		printf '%s\n' "$1" | ssh -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 -o ConnectTimeout=15 \
			${SSH_KEY:+-i "$SSH_KEY"} -p "${SSH_PORT:-22}" "$ACCOUNT@$IP" "$PRE bash -s"
	fi
}

needs_ip() {
	IP=${1:-}
	[ -n "$IP" ] || [ -n "${CONTAINER:-}" ] || { echo "the machine's address is required"; exit 2; }
	IP=${IP:-contenitore}
}

# ═══════════════════════════════════════════════════════════════════════════
prepare() {
	log "prepare: the suitcase (before the rental, on the laptop)"
	command -v podman >/dev/null || { ko "podman is required"; exit 2; }
	local branch hash dirty=""
	branch=$(git -C "$TREE" rev-parse --abbrev-ref HEAD)
	hash=$(git -C "$TREE" rev-parse --short HEAD)
	[ -n "$(git -C "$TREE" status --porcelain -- src packaging installer benches)" ] && dirty="+modifiche"
	[ "$branch" = fase-19 ] || echo "    ⚠ the branch is \"$branch\", not fase-19: the suitcase carries $hash$dirty, and says so"
	rm -rf "$VAL/valigia"
	mkdir -p "$VAL/valigia/pacchetti" "$VAL/valigia/bin" "$VAL/valigia/albero"
	log "the REMOTIX .debs (src/build-targets/build-deb.sh debian13 ubuntu2604)"
	if ! OUTPUT=$OUTPUT bash "$TREE/src/build-targets/build-deb.sh" debian13 ubuntu2604 > "$VAL/costruisci-deb.log" 2>&1; then
		ko "build-deb.sh failed ($VAL/costruisci-deb.log)"; tail -n 5 "$VAL/costruisci-deb.log"; exit 1
	fi
	cp "$OUTPUT"/deb-debian13/remotix_*.deb "$OUTPUT"/deb-ubuntu2604/remotix_*.deb "$VAL/valigia/pacchetti/" \
		|| { ko "the .debs are missing"; exit 1; }
	grep -h . "$OUTPUT"/deb-*/controlli.txt 2>/dev/null | sed 's/^/      /'
	ok "$(ls "$VAL/valigia/pacchetti" | tr '\n' ' ')"
	log "the installer (installer/build.sh)"
	bash "$TREE/installer/build.sh" > "$VAL/costruisci-installatore.log" 2>&1 \
		|| { ko "installer not built ($VAL/costruisci-installatore.log)"; exit 1; }
	cp "$TREE/installer/uscita/remotix-install" "$VAL/valigia/bin/"
	ok "remotix-install $("$VAL/valigia/bin/remotix-install" version 2>/dev/null)"
	log "the benches (like 15-ship.sh) and the sources for bench 19"
	tree_in_suitcase
	{
		echo "$hash$dirty ($branch) · $(git -C "$TREE" log -1 --format='%cd %s' --date=short HEAD | cut -c1-120)"
		echo "prepared: $(date -Is) on $(hostname)"
		(cd "$VAL/valigia" && sha256sum pacchetti/*.deb bin/remotix-install)
	} > "$VAL/valigia/VERSIONE"
	tar -C "$VAL/valigia" -czf "$VAL/valigia.tgz" .
	ok "suitcase: $VAL/valigia.tgz ($(du -h "$VAL/valigia.tgz" | cut -f1)) · $(head -1 "$VAL/valigia/VERSIONE")"
}

# the benches and sources of the CURRENT tree into the suitcase (not the packages)
tree_in_suitcase() {
	rm -rf "$VAL/valigia/albero"
	mkdir -p "$VAL/valigia/albero"
	(
		cd "$TREE" || exit 1
		{
			ls benches/*.py benches/*.sh benches/*.html benches/*.js 2>/dev/null
			find benches/11-boxes benches/15-suite benches/19-vulkan benches/19-nvidia -type f ! -name '*.pyc' \
				! -path '*/__pycache__/*' ! -name '*registro*.jsonl' ! -name 'rapporto-*'
			find src -maxdepth 1 -type f
		} | tar -cf - -T - | tar -xf - -C "$VAL/valigia/albero"
	)
}

send() {
	log "sending the suitcase to $IP"
	[ -f "$VAL/valigia.tgz" ] || { ko "the suitcase is missing: first \"$0 prepare\""; exit 1; }
	# ⛔ 5 Oct 2026: TESTS and BROWSER_SUITE added to the bench AFTER the suitcase did not arrive —
	#    `send` shipped the benches from when the suitcase had been made, and the machine ran the
	#    whole suite. ⇒ The benches (not the packages) are refreshed from the tree at every `send`,
	#    and the VERSION says so
	if [ -d "$VAL/valigia/pacchetti" ]; then
		tree_in_suitcase
		sed -i '/^benches refreshed:/d' "$VAL/valigia/VERSIONE"
		echo "benches refreshed: $(date -Is) from $(git -C "$TREE" rev-parse --short HEAD)$( \
			[ -n "$(git -C "$TREE" status --porcelain -- benches)" ] && echo +modifiche)" >> "$VAL/valigia/VERSIONE"
		tar -C "$VAL/valigia" -czf "$VAL/valigia.tgz" .
	fi
	if [ -n "${CONTAINER:-}" ]; then
		podman exec "$CONTAINER" mkdir -p "$FAR"
		podman exec -i "$CONTAINER" tar -xzf - -C "$FAR" < "$VAL/valigia.tgz" || exit 1
	else
		ssh -o StrictHostKeyChecking=accept-new ${SSH_KEY:+-i "$SSH_KEY"} -p "${SSH_PORT:-22}" "$ACCOUNT@$IP" \
			"$PRE rm -rf $FAR && $PRE mkdir -p $FAR && $PRE tar -xzf - -C $FAR" < "$VAL/valigia.tgz" || exit 1
	fi
	ok "$(far "head -1 $FAR/VERSIONE")"
}

start() {
	local p=${1:-all}
	log "starting \"$p\" on the machine (a systemd unit: ssh may drop)"
	if far "systemctl is-active --quiet $UNIT"; then ko "the bench is already running ($UNIT)"; return 1; fi
	far "mkdir -p $WORKDIR && rm -f $WORKDIR/uscita && echo '=== avvio $p $(date -Is)' >> $WORKDIR/banco.log && \
		systemctl reset-failed $UNIT 2>/dev/null; \
		systemd-run --unit=$UNIT --collect --property=StandardOutput=append:$WORKDIR/banco.log \
		--property=StandardError=append:$WORKDIR/banco.log --setenv=FORCE=${FORCE:-0} --setenv=REDO='${REDO:-}' \
		--setenv=TESTS='${TESTS:-}' --setenv=BROWSER_SUITE='${BROWSER_SUITE:-}' --setenv=CLIENT_CARD='${CLIENT_CARD:-0}' --setenv=DESKTOP_NV='${DESKTOP_NV:-xfce}' \
		/bin/bash $FAR/albero/benches/19-nvidia/19-nv-machine.sh $p" \
		&& ok "started"
}

# follows the log until the bench writes its exit code; returns that exit code
follow() {
	log "following the bench (Ctrl-C does not stop it: run \"follow\" again)"
	local da=0 lines u
	da=$(far "wc -l < $WORKDIR/banco.log" 2>/dev/null || echo 0)
	da=$(( ${da:-0} > 40 ? da - 40 : 0 ))
	while :; do
		lines=$(far "tail -n +$((da + 1)) $WORKDIR/banco.log 2>/dev/null")
		if [ -n "$lines" ]; then
			printf '%s\n' "$lines"
			da=$((da + $(printf '%s\n' "$lines" | wc -l)))
		fi
		if ! far "systemctl is-active --quiet $UNIT" 2>/dev/null; then
			u=$(far "cat $WORKDIR/uscita 2>/dev/null")
			[ -n "$u" ] && { log "the bench has finished: exit $u"; return "$u"; }
			# ssh dropped or machine rebooting: retry
			far true 2>/dev/null || { sleep 20; continue; }
			log "the bench is not running and has not written its exit code (stopped by hand?)"; return 3
		fi
		sleep 20
	done
}

wait_ssh() {
	local i
	for i in $(seq 1 60); do
		sleep 15
		far true >/dev/null 2>&1 && { ok "the machine answers"; return 0; }
	done
	ko "after 15 minutes the machine does not answer"; return 1
}

collect() {
	log "collecting the evidence archive"
	far "bash $FAR/albero/benches/19-nvidia/19-nv-machine.sh collect" | tail -n 3
	local name sha
	name=$(far "cat $WORKDIR/archivio")
	sha=$(far "cat $WORKDIR/archivio.sha256")
	[ -n "$name" ] || { ko "no archive"; return 1; }
	mkdir -p "$SIZES"
	far "cat $WORKDIR/$name" > "$SIZES/$name"
	if [ "$(sha256sum "$SIZES/$name" | cut -d' ' -f1)" = "$sha" ]; then
		far "touch $WORKDIR/raccolto"
		ok "$SIZES/$name (sha256 equal)"
		tar -xzf "$SIZES/$name" -O evidenze/passi.txt 2>/dev/null | sed 's/^/      /'
	else
		ko "sha256 differs: run \"collect\" again"; return 1
	fi
}

clean() {
	log "cleaning the machine"
	far "FORCE=${FORCE:-0} bash $FAR/albero/benches/19-nvidia/19-nv-machine.sh clean" || return 1
	far "rm -rf $FAR $WORKDIR" && ok "suitcase and work folder removed"
	far "cat /run/reboot-required 2>/dev/null; true"
}

all() {
	send
	start all || exit 1
	follow; local u=$? n=0
	# more than one reboot (5 Oct 2026): the Ubuntu upgrade asks for one per hop, the driver one
	while [ "$u" = 10 ] && [ $n -lt 10 ]; do
		n=$((n + 1))
		log "the bench asks for a REBOOT ($n; upgrade/driver/ICD/modeset): rebooting and resuming"
		[ -n "${CONTAINER:-}" ] && { ko "a container cannot be rebooted"; exit 1; }
		far "systemctl reboot" || true
		wait_ssh || exit 1
		start all || exit 1
		follow; u=$?
	done
	collect
	log "END: exit $u · the evidence in $SIZES · the cleanup: \"$0 clean $IP\""
	return "$u"
}

ACTION=${1:-}
case "$ACTION" in
prepare) prepare ;;
send|follow|collect|clean|all) needs_ip "${2:-}"; "$ACTION" ;;
start) needs_ip "${2:-}"; start "${3:-tutto}" ;;
status) needs_ip "${2:-}"; far "bash $FAR/albero/benches/19-nvidia/19-nv-machine.sh status" ;;
enter) needs_ip "${2:-}"; ssh ${SSH_KEY:+-i "$SSH_KEY"} -p "${SSH_PORT:-22}" "$ACCOUNT@$IP" ;;
*) sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
