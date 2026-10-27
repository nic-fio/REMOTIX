#!/bin/bash
# 19-nvidia.sh — the bench of the rented NVIDIA machine, driven FROM THE LAPTOP (or from the home server).
#
#   bash benches/19-nvidia/19-nvidia.sh prepare           # BEFORE the rental: the suitcase
#   bash benches/19-nvidia/19-nvidia.sh all IP          # sends, starts, follows (reboot included); collects
#                                                       #   (CLIENTS=machine) or stops, machine ready (CLIENTS=home)
#   bash benches/19-nvidia/19-nvidia.sh suite-casa IP   # CLIENTS=home: the tests, browsers at HOME (run on the home server)
#   bash benches/19-nvidia/19-nvidia.sh collect IP      # the evidence archive to this machine
#   bash benches/19-nvidia/19-nvidia.sh clean IP        # AFTER collecting: the machine as found
#
#   and piece by piece:  send IP · start IP [STEP] · follow IP · status IP · collect IP · enter IP
#
# CLIENTS=home (default) | machine: where the browsers of the suite are.  home: at home (the home server,
# 192.168.0.2, connects over internet like a real user; the machine runs only REMOTIX and the desktop; the
# firewall opens the port only towards the address ssh comes from, CLIENT_ADDR to force it).  machine: the browsers
# on the rented machine, as the bench has always done (the fallback if the provider will not open the UDP port).
# Other variables: PORT (7447), DESKTOP_NV (xfce), TESTS, BROWSER_SUITE, PREFLIGHT (path, or skip), RTT_WIDEN_MS (30), FAR_LOG.
# Variables: ACCOUNT (root; a user with passwordless "sudo" is fine: ubuntu, debian, admin),
# SSH_PORT (22), SSH_KEY (an ssh key file), CONTAINER=name (the LOCAL test: podman exec
# instead of ssh, for the steps that do not touch the GPU — see 19-nv-test-in-container.sh; with
# `suite-casa`, a HOME container (rete11-xfce) acting as the machine — see the comment above suite_home).
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
CLIENTS=${CLIENTS:-home}
case "$CLIENTS" in home|machine) ;; *) echo "CLIENTS=$CLIENTS: home or machine"; exit 2 ;; esac

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
warning() { printf '    \033[1;33m!!\033[0m  %s\n' "$*"; }
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

# ⭐ 27 Oct 2026: the address the machine sees us from, READ FROM SSH ITSELF ($SSH_CONNECTION of the session; no
#    external service). Computed here, where we know how we connect: the bench on the machine runs in a systemd
#    unit, with no ssh session of its own, and `sudo` strips the variable.  CLIENT_ADDR forces it (a jump host,
#    a second address); in the local test (CONTAINER) there is nothing to open: empty.
client_addr() {
	local a
	if [ -n "${CLIENT_ADDR:-}" ]; then echo "$CLIENT_ADDR"; return 0; fi
	[ -n "${CONTAINER:-}" ] && return 0
	a=$(printf '%s\n' 'echo "${SSH_CONNECTION%% *}"' | ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 \
		${SSH_KEY:+-i "$SSH_KEY"} -p "${SSH_PORT:-22}" "$ACCOUNT@$IP" sh -s 2>/dev/null | tail -n 1)
	printf '%s' "$a" | grep -q -E '^[0-9A-Fa-f:.]+$' || return 1
	echo "$a"
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
	local p=${1:-all} ca=""
	log "starting \"$p\" on the machine (a systemd unit: ssh may drop) · CLIENTS=$CLIENTS"
	if [ "$CLIENTS" = home ]; then
		ca=$(client_addr) || { ko "I cannot read from ssh the address the machine sees us from (CLIENT_ADDR=… to give it)"; return 1; }
		[ -n "$ca" ] && ok "the clients come from $ca: the port will be opened towards it only"
	fi
	if far "systemctl is-active --quiet $UNIT"; then ko "the bench is already running ($UNIT)"; return 1; fi
	far "mkdir -p $WORKDIR && rm -f $WORKDIR/uscita && echo '=== avvio $p $(date -Is)' >> $WORKDIR/banco.log && \
		systemctl reset-failed $UNIT 2>/dev/null; \
		systemd-run --unit=$UNIT --collect --property=StandardOutput=append:$WORKDIR/banco.log \
		--property=StandardError=append:$WORKDIR/banco.log --setenv=FORCE=${FORCE:-0} --setenv=REDO='${REDO:-}' \
		--setenv=TESTS='${TESTS:-}' --setenv=BROWSER_SUITE='${BROWSER_SUITE:-}' --setenv=CLIENT_CARD='${CLIENT_CARD:-0}' --setenv=DESKTOP_NV='${DESKTOP_NV:-xfce}' \
		--setenv=CLIENTS=$CLIENTS --setenv=CLIENT_ADDR='$ca' --setenv=PORT='${PORT:-7447}' \
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

# ═══════════════════════════════════════════════════════════════════════════
#  suite-casa: the browsers at HOME, the machine far away (CLIENTS=home)
# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 27 Oct 2026.  Run on the HOME server (192.168.0.2), not on the laptop/tablet (a long job freezes it), after
#    `all IP` has left the machine ready (REMOTIX installed, port open towards this server).  The tests are the
#    same ones of `19-nv-suite.py`; what changes is where things are:
#      - the browsers: here, in the headless labwc of the desktop (15-compositors.sh), as in the phase 15 suite;
#      - the connection: over internet, to IP:PORT, like a real user;
#      - "inside the desktop" (commands, scenes, the server log the tests read): ssh to the machine
#        (CONTAINER=name: the local test, `sudo podman exec` into a home container acting as the machine).
#    Local test, no NVIDIA, no rental (after the net has finished):
#        CONTAINER=rete11-xfce PORT=8513 bash benches/19-nvidia/19-nvidia.sh suite-casa 192.168.0.2
suite_home() {
	local desk=${DESKTOP_NV:-xfce} port=${PORT:-7447} R dir pf sock rtt how code i c off="" t0 t1 r cap=0
	local flog system version text status sshopts ctl sdir
	R=/run/user/$(id -u)
	[ "$CLIENTS" = home ] || { ko "CLIENTS=machine: the suite runs on the machine (\"all\"); suite-casa is for CLIENTS=home"; return 2; }
	dir=$SIZES/suite-casa-$(date +%Y%m%d-%H%M)
	mkdir -p "$dir" || return 1
	log "suite-casa: the browsers at home ($(hostname -s)), the machine at $IP:$port, desktop $desk"
	# 1. the home server must be free: no test or chain alive, free ports, compositors on (the preflight of the
	#    nightly chains, profile suite: it also starts the compositors, a safe repair)
	pf=${PREFLIGHT:-/media/REMOTIX-15/lavori/notti/preflight.sh}
	if [ "$pf" = skip ]; then
		warning "PREFLIGHT=skip: the home server was NOT checked, and that is declared"
		echo "preflight skipped by the operator" > "$dir/preflight.txt"
	else
		[ -r "$pf" ] || { ko "the preflight $pf is not readable (PREFLIGHT=path, or PREFLIGHT=skip)"; return 1; }
		# shellcheck disable=SC2086
		bash "$pf" ${PREFLIGHT_ARGS:-suite --desktop $desk --ripara} 2>&1 | tee "$dir/preflight.txt" | sed 's/^/      /'
		[ "${PIPESTATUS[0]}" = 0 ] || { ko "the home server is not free (preflight.txt): nothing started"; return 1; }
		ok "the home server is free"
	fi
	sock=$(cat "$R/15-compositors/$desk" 2>/dev/null)
	if [ -z "$sock" ] || [ ! -S "$R/$sock" ]; then
		ko "no browsers' compositor for $desk ($R/15-compositors/$desk): bash benches/15-suite/15-compositors.sh start"; return 1
	fi
	ok "browsers' compositor: $sock"
	# 2. the delay towards the machine, measured and written down (ping; if ICMP is filtered, the TCP connection)
	how=ping
	rtt=$(ping -c 10 -i 0.2 -W 2 -q "$IP" 2>/dev/null | awk -F/ '/^(rtt|round-trip)/ {printf "%.0f", $5}')
	if [ -z "$rtt" ]; then
		how="TCP connect"
		rtt=$(for i in 1 2 3 4 5; do curl -sk -o /dev/null -m 10 -w '%{time_connect}\n' "https://$IP:$port/"; done \
			| awk '$1 > 0 {s += $1; n++} END {if (n) printf "%.0f", 1000 * s / n}')
	fi
	[ -n "$rtt" ] || { ko "no answer from $IP (neither ping nor TCP $port)"; return 1; }
	ok "round trip to $IP: $rtt ms ($how)"
	# 3. the port answers from outside: TCP and REMOTIX's own page over https (self-signed certificate: -k)
	code=""
	for i in 1 2 3; do
		code=$(curl -sk -o "$dir/pagina.html" -m 15 -w '%{http_code}' "https://$IP:$port/" 2>/dev/null)
		[ "$code" = 200 ] && break
		sleep 5
	done
	if [ "$code" != 200 ]; then
		ko "REMOTIX's page does not answer on https://$IP:$port/ (code ${code:-none}): the TCP port is closed or the server is down (\"$0 status $IP\")"
		return 1
	fi
	ok "REMOTIX's page answers on https://$IP:$port/ ($(wc -c < "$dir/pagina.html") bytes)"
	# UDP cannot be asked with a question: the first login of F-001 is the proof. If this curl speaks HTTP/3, one try, for information
	if curl --version 2>/dev/null | grep -q -i http3; then
		curl -sk --http3-only -o /dev/null -m 10 "https://$IP:$port/" 2>/dev/null \
			&& ok "HTTP/3 over UDP $port: answers" || warning "HTTP/3 over UDP $port: no answer (information only: the tests will say)"
	fi
	# 4. the clocks: F-003 compares the clock of the scene inside the desktop (the machine's) with ours
	if [ -z "${CONTAINER:-}" ]; then
		t0=$(date +%s.%N); r=$(far "date +%s.%N" 2>/dev/null | tail -n 1); t1=$(date +%s.%N)
		if printf '%s' "$r" | grep -q -E '^[0-9]+\.[0-9]+$'; then
			off=$(awk -v a="$t0" -v b="$t1" -v r="$r" 'BEGIN {printf "%.0f", (r - (a + b) / 2) * 1000}')
			ok "clock of the machine minus ours: $off ms"
			[ "${off#-}" -gt 100 ] && warning "the clocks differ by more than 100 ms: F-003 (image age, cap 1000 ms) adds this to what it measures"
		else
			warning "the machine's clock could not be read"
		fi
	fi
	# 5. the delay and the tests' time limits (the only knob the suite exposes: --cap-s, login and first image, 45 s).
	#    Beyond RTT_WIDEN_MS it grows by RTT/5 seconds and it is SAID. The other limits (F-003 1000 ms…) stay as they are.
	if [ "$rtt" -gt "${RTT_WIDEN_MS:-30}" ]; then
		cap=$((45 + rtt / 5))
		warning "round trip $rtt ms > ${RTT_WIDEN_MS:-30} ms: --cap-s 45 → $cap (declared); the other limits of the tests are NOT widened"
	fi
	# 6. the road to "inside" and the description of the run
	flog=${FAR_LOG:-$WORKDIR/registro.log}
	ctl=""
	if [ -n "${CONTAINER:-}" ]; then
		system="container $CONTAINER"
		version="container $CONTAINER"
		case "$CONTAINER" in rete11-*) flog=${FAR_LOG:-/var/lib/rete11/registro.log} ;; esac
	else
		system=$(far '. /etc/os-release; echo "$PRETTY_NAME · $(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>/dev/null | head -1)"' 2>/dev/null | tail -n 1)
		version=$(far "head -1 $FAR/VERSIONE" 2>/dev/null | tail -n 1)
		# one ssh connection for all the "insides" of the tests (each one would pay the handshake again): closed at the end
		ctl=$R/rxnv-ssh-%C
		sshopts="-o StrictHostKeyChecking=accept-new -o ControlMaster=auto -o ControlPath=$ctl -o ControlPersist=120 -p ${SSH_PORT:-22}${SSH_KEY:+ -i $SSH_KEY}"
	fi
	system="$system · $desk · browsers at home, RTT $rtt ms"
	{
		echo "machine: $IP:$port"
		echo "rtt_ms: $rtt ($how)"
		echo "clock_offset_ms: ${off:-unknown}"
		echo "cap_s: $([ "$cap" -gt 0 ] && echo "$cap (default 45, raised)" || echo "45 (default)")"
		echo "inside: $([ -n "${CONTAINER:-}" ] && echo "container $CONTAINER" || echo "ssh $ACCOUNT@$IP")"
		echo "server_log: $flog"
		echo "browsers: $HOSTNAME, compositor $sock"
	} > "$dir/rete.txt"
	# 7. the run: the same tests, the browsers here, the product there
	local args=(--log "$dir/registro.jsonl" --evidence "$dir" --port "$port" --mode window --desktop "$desk" --host "$IP")
	[ "$cap" -gt 0 ] && args+=(--cap-s "$cap")
	[ -n "${TESTS:-}" ] && args+=(--tests "$TESTS")
	[ -n "${BROWSER_SUITE:-}" ] && args+=(--browser "$BROWSER_SUITE")
	if [ -n "${CONTAINER:-}" ]; then args+=(--container "$CONTAINER")
	else args+=(--ssh "$ACCOUNT@$IP" --ssh-opts "$sshopts" ${PRE:+--sudo "$PRE"}); fi
	log "the tests (${TESTS:-all}) with ${BROWSER_SUITE:-firefox,chrome} at home against $IP:$port"
	env XDG_RUNTIME_DIR="$R" WAYLAND_DISPLAY="$sock" MOZ_ENABLE_WAYLAND=1 RXNV_LOG="$flog" \
		RXNV_SYSTEM="$system" RXNV_VERSION="$version" \
		python3 "$HERE/19-nv-suite.py" "${args[@]}" > "$dir/suite.txt" 2>&1
	c=$?
	[ -n "$ctl" ] && ssh -O exit -o ControlPath="$ctl" "$ACCOUNT@$IP" >/dev/null 2>&1
	tail -n 3 "$dir/suite.txt" | sed 's/^/      /'
	# 8. the report, like the machine does, and the routes the real sessions took (from the machine's log)
	python3 "$TREE/benches/15-suite/15-report.py" --log "$dir/registro.jsonl" --round 19-nvidia --text \
		> "$dir/suite-rapporto.txt" 2>&1
	python3 "$TREE/benches/15-suite/15-report.py" --log "$dir/registro.jsonl" --round 19-nvidia \
		--html "$dir/suite-rapporto.html" > /dev/null 2>&1
	if [ -z "${CONTAINER:-}" ]; then
		far "grep -a -E 'route (vulkan|vaapi)|pixman|CANNOT ENCODE|DEVICE_LOST|Xid' $flog | sort | uniq -c | sort -rn | head -30" \
			> "$dir/suite-strade.txt" 2>/dev/null
	fi
	case $c in 0) status=VERDE ;; 3) status=NON-GUARDATA ;; *) status=ROSSO ;; esac
	text="browsers at home, RTT $rtt ms ($how), clock offset ${off:-?} ms, cap-s $([ "$cap" -gt 0 ] && echo "$cap" || echo 45) · $(tail -n 1 "$dir/suite.txt")"
	text=$(printf '%s' "$text" | tr -d "'\"\\\`\$" | cut -c1-300)
	printf '%s\t%s\t%s\t%s\n' "$(date -Is)" suite "$status" "$text" >> "$dir/passi.txt"
	# 9. the evidence also goes to the machine: the archive of `collect` has it all, with the passi.txt line
	if [ -z "${CONTAINER:-}" ]; then
		sdir=$WORKDIR/evidenze/suite-casa
		if tar -C "$SIZES" -czf - "$(basename "$dir")" | ssh -o StrictHostKeyChecking=accept-new ${SSH_KEY:+-i "$SSH_KEY"} -p "${SSH_PORT:-22}" "$ACCOUNT@$IP" \
			"$PRE mkdir -p $sdir && $PRE tar -xzf - -C $sdir"; then
			far "bash $FAR/albero/benches/19-nvidia/19-nv-machine.sh record suite $status '$text'" >/dev/null 2>&1 \
				&& ok "evidence and passi.txt line sent to the machine (the archive of \"collect\" will have them)"
		else
			warning "the evidence could not be sent to the machine: it stays in $dir"
		fi
	fi
	case $c in
	0) ok "suite GREEN (browsers at home, RTT $rtt ms) · $dir" ;;
	3) warning "suite with tests not looked at · $dir" ;;
	*) ko "suite RED · $dir" ;;
	esac
	return "$c"
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
	if [ "$CLIENTS" = home ] && [ "$u" = 0 ]; then
		# the machine is ready; the suite is run from home, and the evidence is collected AFTER it
		log "END: the machine is ready · next, on the home server: \"$0 suite-casa $IP\", then \"$0 collect $IP\", then \"$0 clean $IP\""
		return 0
	fi
	collect
	log "END: exit $u · the evidence in $SIZES · the cleanup: \"$0 clean $IP\""
	return "$u"
}

ACTION=${1:-}
case "$ACTION" in
prepare) prepare ;;
send|follow|collect|clean|all) needs_ip "${2:-}"; "$ACTION" ;;
start) needs_ip "${2:-}"; start "${3:-all}" ;;
suite-casa) [ -n "${2:-}" ] || { echo "the machine's address is required (also with CONTAINER: the address the container answers on)"; exit 2; }
	IP=$2; suite_home ;;
status) needs_ip "${2:-}"; far "bash $FAR/albero/benches/19-nvidia/19-nv-machine.sh status" ;;
enter) needs_ip "${2:-}"; ssh ${SSH_KEY:+-i "$SSH_KEY"} -p "${SSH_PORT:-22}" "$ACCOUNT@$IP" ;;
*) sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
