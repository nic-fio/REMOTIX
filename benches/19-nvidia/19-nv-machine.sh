#!/bin/bash
# 19-nv-machine.sh — the NVIDIA bench, ON THE RENTED MACHINE, as root.
#
#   bash /opt/remotix-nv/tree/benches/19-nvidia/19-nv-machine.sh STEP
#
# Usually no person launches it: `19-nvidia.sh` launches it from the laptop
# (`all IP`), in a systemd unit that survives ssh dropping.
#
# THE STEPS, in the order of `all` (phases/19-nvidia.md §2.4, task of 1 Oct 2026):
#   upgrade     an Ubuntu OLDER than 26.04 is brought to 26.04 with do-release-upgrade,
#                    one hop and one reboot at a time (20.04 ⇒ 22.04 ⇒ 24.04 ⇒ 26.04): the rental companies
#                    offer Ubuntu, and not always 26.04 (5 Oct 2026). ⛔ "clean" does NOT undo it
#   checks    (a) card, driver, DRM nodes, ICD, vulkaninfo with
#                    VK_KHR_video_encode_h264/h265; and the SNAPSHOT of the machine
#                    as it was (packages, /etc/apt, users, units): "clean" needs it
#   driver       the NVIDIA driver with its Vulkan ICD and nvidia-drm modeset=1, ONLY
#                    if missing; if it touches the kernel it exits with 10 = reboot
#   deps   (b) XFCE under labwc, the test tools, Firefox ESR, Chrome (these two only with
#                    CLIENTS=machine), the bench user `rxbanco`
#   remotix      (b) REMOTIX from the `fase-19` .deb WITH THE INSTALLER (plan, apply):
#                    the refusal, if any, is already a result
#   porta (port)  (b2) CLIENTS=home only: REMOTIX listens on a non-loopback address, and its port
#                    (TCP+UDP) is opened ONLY towards the client's address, if a firewall is active
#                    (ufw or nftables); the rule is recorded and `clean` removes it
#   encode     (c) `remotix --encoding-test` h264 and hevc: must say route "vulkan"
#   comparison    (d) `benches/19-vulkan/19-compare.sh` on the NVIDIA (quality,
#                    decoding of every frame, new canvas, canvas in a LOOP, keyframe, ceiling)
#   suite        (e) the subset of the phase 15 suite (F-001 F-002 F-003 F-011
#                    F-013 F-016 F-018) on XFCE under headless labwc, Firefox and Chrome
#                    — CLIENTS=machine only; with CLIENTS=home the browsers are at HOME:
#                    `19-nvidia.sh suite-casa IP`, run on the home server
#   collect     (f) logs and evidence in ONE archive, to take to the laptop
#   clean      (g) the machine as we found it (wants the archive already taken away)
#   status        how far we got
#   record     (home) `record STEP OUTCOME TEXT`: a line in passi.txt written from outside
#                    (suite-casa leaves there «browsers at home, RTT N ms»)
#   all        from the first to the last before "clean", skipping those already done.
#                    CLIENTS=home: it stops BEFORE `suite` and `collect` (the suite is at home):
#                    then `suite-casa IP`, then `collect IP`
#
# Exit: 0 green · 1 red · 3 could not look · 10 a reboot is needed
# (then `all` is run again, and it resumes from the next step).
# Variables: CLIENTS=home|machine (home by default: the clients' browsers are on the home server and
# come in over the internet, like real users; machine = the browsers on this machine, as before),
# CLIENT_ADDR (the address the clients come from: 19-nvidia.sh reads it from ssh and passes it),
# PORT (7447), FORCE=1 (goes on even after a red check), TESTS=f003,f013 and
# BROWSER_SUITE=firefox (only those tests / that browser, to repeat a test), DESKTOP_NV=gnome
# (GNOME in addition to XFCE, and the suite on GNOME; =kde: Plasma, and GNOME removed; =lxqt: LXQt, and the others removed), CLIENT_CARD=1
# (the browsers draw on the card: counter-test only),
# REDO="step step" (redoes steps already done), WORKDIR (/var/lib/remotix-nv).
#
# ⛔ Performance is NOT judged here: the times the benches write stay
#    in the evidence, the judgement is on behaviour (decoding, route, tests).
set -u
export LC_ALL=C.UTF-8 DEBIAN_FRONTEND=noninteractive
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../.." && pwd)
SUITCASE=$(cd "$TREE/.." && pwd)
WORKDIR=${WORKDIR:-/var/lib/remotix-nv}
BEFORE=$WORKDIR/prima
DONE=$WORKDIR/fatto
EVID=$WORKDIR/evidenze
PORT=${PORT:-7447}
# ⭐ 27 Oct 2026: WHERE THE BROWSERS ARE.  home (default): at home, on the home server, as real users over
#    internet — this machine runs only REMOTIX and the desktop, so the card is measured without the browsers
#    on its back and the network is the real one.  machine: as it has always been (the fallback, if the
#    provider will not open the UDP port).
CLIENTS=${CLIENTS:-home}
CLIENT_ADDR=${CLIENT_ADDR:-}
FWREC=$WORKDIR/firewall-regole          # what `porta` opened: «ufw PROTO ADDR PORT» / «nft FAMILY TABLE CHAIN PORT»
BENCH_USER=rxbanco
BIN=/usr/libexec/remotix/remotix
APT=(apt-get -y -q -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold)
case "$CLIENTS" in home|machine) ;; *) echo "CLIENTS=$CLIENTS: home or machine"; exit 2 ;; esac
mkdir -p "$WORKDIR" "$DONE" "$EVID"

ok()     { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()     { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
warning() { printf '    \033[1;33m!!\033[0m  %s\n' "$*"; }
log()    { printf '\n\033[1m== %s · %s\033[0m\n' "$(date +%H:%M:%S)" "$*"; }
# one line per step in passi.txt: the summary the laptop shows at the end
outcome()  { printf '%s\t%s\t%s\t%s\n' "$(date -Is)" "$1" "$2" "$3" >> "$EVID/passi.txt"; }

distro() { . /etc/os-release; echo "${ID:-?} ${VERSION_ID:-?}"; }
family() {
	case "$(distro)" in
	"debian 13") echo debian ;;
	"ubuntu 26.04") echo ubuntu ;;
	*) echo altra ;;
	esac
}

# the NVIDIA's DRM render node (renderD128…), "" if absent
nvidia_node() {
	local n d
	for n in /dev/dri/renderD*; do
		[ -e "$n" ] || continue
		d=$(basename "$(readlink -f "/sys/class/drm/$(basename "$n")/device/driver")" 2>/dev/null)
		[ "$d" = nvidia ] && { basename "$n"; return 0; }
	done
	return 1
}

# the NVIDIA's ICD file (nvidia_icd.json, nvidia_icd.x86_64.json…), "" if absent
icd_nvidia() {
	local f
	for f in /usr/share/vulkan/icd.d/nvidia_icd*.json /etc/vulkan/icd.d/nvidia_icd*.json; do
		[ -e "$f" ] && { echo "$f"; return 0; }
	done
	return 1
}

# the packages of the list that the repository really has
# a REAL package with its candidate: "apt-cache show" says yes even to a name only mentioned
# (`[M]` 1 Oct 2026, Ubuntu 26.04: firefox-esr is "Candidate: (none)" and show exits with 0)
has_candidate() { apt-cache policy "$1" 2>/dev/null | awk '/Candidate:/{print $2}' | grep -q -v -e "(none)" -e "^$"; }
available() { local p; for p; do has_candidate "$p" && echo "$p"; done; }

# installed: "ii", but also "it"/"iU" (installed, with triggers or configuration pending)
installs() { dpkg-query -W -f='${db:Status-Abbrev} ${Package}\n' 2>/dev/null | awk '$1 ~ /^i/{print $2}' | sort -u; }

# ═══════════════════════════════════════════════════════════════════════════
#  THE SNAPSHOT OF THE MACHINE AS IT WAS (once only: it is clean's "before")
# ═══════════════════════════════════════════════════════════════════════════
snapshot_first() {
	[ -f "$BEFORE/fatta" ] && return 0
	mkdir -p "$BEFORE"
	installs > "$BEFORE/pacchetti.txt"
	apt-mark showmanual 2>/dev/null | sort > "$BEFORE/manuali.txt"
	tar -C / -cpf "$BEFORE/etc-apt.tar" etc/apt
	getent passwd | cut -d: -f1 | sort > "$BEFORE/utenti.txt"
	ls /etc/modprobe.d > "$BEFORE/modprobe.txt" 2>/dev/null
	systemctl list-unit-files --state=enabled --no-legend 2>/dev/null | awk '{print $1}' | sort > "$BEFORE/unita.txt"
	[ -e /etc/remotix ] && echo si > "$BEFORE/etc-remotix"
	cat /proc/cmdline > "$BEFORE/cmdline.txt"
	date -Is > "$BEFORE/fatta"
	ok "snapshot of the machine as it was: $(wc -l < "$BEFORE/pacchetti.txt") packages, $(wc -l < "$BEFORE/utenti.txt") users"
}

# ═══════════════════════════════════════════════════════════════════════════
#  (a) THE CHECKS
# ═══════════════════════════════════════════════════════════════════════════
# Old Ubuntu ⇒ a version hop and a reboot (exit 10); 26.04 or Debian 13 ⇒ nothing.
# ⛔ Irreversible: the machine is returned upgraded, and "clean" declares it.
upgrade() {
	log "(0) the system version"
	. /etc/os-release
	if [ "${ID:-}" != ubuntu ] || [ "$(family)" != altra ]; then
		ok "$(distro): nothing to upgrade"
		return 0
	fi
	local da=$VERSION_ID f="$EVID/aggiorna-$VERSION_ID.txt"
	case "$da" in 20.04|22.04|24.04) ;; *) ko "ubuntu $da: I can only upgrade from 20.04, 22.04 and 24.04"; outcome upgrade ROSSO "ubuntu $da"; return 1 ;; esac
	[ "$(id -u)" = 0 ] || { ko "root is required"; return 1; }
	# do-release-upgrade refuses if the system is not up to date or is waiting for a reboot
	log "ubuntu $da: first upgrading the packages of $da"
	{ "${APT[@]}" update && "${APT[@]}" dist-upgrade && "${APT[@]}" install ubuntu-release-upgrader-core; } > "$f" 2>&1 \
		|| { ko "upgrade of $da failed ($f)"; outcome upgrade ROSSO "dist-upgrade $da"; return 1; }
	if [ -f /var/run/reboot-required ]; then
		touch "$WORKDIR/riavvio-chiesto"
		log "the upgraded $da asks for a reboot before the hop"
		return 10
	fi
	sed -i -E 's/^Prompt=.*/Prompt=lts/' /etc/update-manager/release-upgrades 2>/dev/null
	log "ubuntu $da: hop to the next LTS version (half an hour or more)"
	# -f DistUpgradeViewNonInteractive: no questions, changed configuration files are kept
	if ! do-release-upgrade -f DistUpgradeViewNonInteractive >> "$f" 2>&1; then
		# before the .1 the hop between LTS is not offered yet: -d forces it
		if grep -q -i "no new release" "$f"; then
			warning "the hop is not offered yet: forcing it with -d"
			do-release-upgrade -d -f DistUpgradeViewNonInteractive >> "$f" 2>&1 \
				|| { ko "do-release-upgrade -d failed ($f)"; outcome upgrade ROSSO "hop from $da"; return 1; }
		else
			ko "do-release-upgrade failed ($f)"; outcome upgrade ROSSO "hop from $da"; return 1
		fi
	fi
	outcome upgrade RIAVVIO "ubuntu $da ⇒ $(. /etc/os-release; echo "$VERSION_ID")"
	touch "$WORKDIR/riavvio-chiesto"
	return 10
}

checks() {
	log "(a) the initial checks"
	local f="$EVID/controlli.txt" red=0 missing_driver=0
	: > "$f"
	write() { printf '%s: %s\n' "$1" "$2" >> "$f"; }
	[ "$(id -u)" = 0 ] || { ko "root is required"; return 1; }
	write distribuzione "$(. /etc/os-release; echo "$PRETTY_NAME")"
	write nucleo "$(uname -r)"
	write processore "$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2- | sed 's/^ //') ($(nproc) threads)"
	write memoria "$(awk '/MemTotal/{printf "%.0f GiB", $2/1048576}' /proc/meminfo)"
	if [ "$(family)" = altra ]; then
		ko "distribution $(distro): REMOTIX wants Debian 13 or Ubuntu 26.04 (OpenSSL 3.5, labwc, libei)"
		write verdetto.distribuzione ROSSO; red=1
	else
		ok "distribution $(distro)"
		write verdetto.distribuzione VERDE
	fi
	snapshot_first
	# the check's tools: few, and if we install them "clean" removes them
	if ! command -v vulkaninfo >/dev/null || ! command -v lspci >/dev/null; then
		"${APT[@]}" update >/dev/null 2>&1
		"${APT[@]}" install --no-install-recommends vulkan-tools pciutils >/dev/null 2>&1 \
			&& ok "vulkan-tools and pciutils installed to look" || warning "vulkan-tools/pciutils not installed"
	fi
	# the card, from the bus: it is there even without a driver
	local pci
	pci=$(lspci -nn 2>/dev/null | grep -i -E 'vga|3d|display' | grep -i '10de' || true)
	if [ -z "$pci" ]; then
		ko "no NVIDIA card on the PCI bus"
		write verdetto.scheda ROSSO; red=1
	else
		ok "card: $pci"
		write scheda "$pci"
	fi
	lspci -nnk > "$EVID/lspci.txt" 2>&1
	# the driver
	local name="" ver="" greater=0
	if command -v nvidia-smi >/dev/null && nvidia-smi >/dev/null 2>&1; then
		name=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
		ver=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)
		greater=${ver%%.*}
		nvidia-smi -q > "$EVID/nvidia-smi.txt" 2>&1
		write scheda.name "$name"; write driver.versione "$ver"
		if [ "${greater:-0}" -ge 550 ] 2>/dev/null; then
			ok "driver NVIDIA $ver ($name)"
		else
			ko "NVIDIA driver $ver: 550 or newer is required (Vulkan Video encode)"
			write verdetto.driver ROSSO; red=1
		fi
		# ⛔ the compute cards without NVENC (A100, H100…): Vulkan Video encode is not there
		if echo "$name" | grep -q -E '(^|[ -])(A100|A800|A30|H100|H200|H800|B100|B200|GH200)([ -]|$)'; then
			ko "$name has no video encoder (NVENC): REMOTIX cannot encode here"
			write verdetto.nvenc ROSSO; red=1
		fi
		grep -i -A3 'Encoder Stats' "$EVID/nvidia-smi.txt" > /dev/null 2>&1 && write nvenc "encoder statistics present in nvidia-smi -q"
	else
		warning "nvidia-smi does not answer: the driver is missing (or not loaded) ⇒ the \"driver\" step installs it"
		write driver.versione nessuno; missing_driver=1
	fi
	# the modules and modeset
	local ms
	ms=$(cat /sys/module/nvidia_drm/parameters/modeset 2>/dev/null || echo "?")
	write nvidia_drm.modeset "$ms"
	grep -E '^nvidia' /proc/modules > "$EVID/moduli.txt" 2>&1
	[ "$ms" = Y ] && ok "nvidia-drm modeset=Y" || warning "nvidia-drm modeset=$ms ⇒ the \"driver\" step sets it to 1 (GBM needs it, i.e. labwc on the card)"
	# the DRM nodes
	local n d line=""
	for n in /dev/dri/card* /dev/dri/renderD*; do
		[ -e "$n" ] || continue
		d=$(basename "$(readlink -f "/sys/class/drm/$(basename "$n")/device/driver")" 2>/dev/null)
		line="$line $(basename "$n")=$d"
	done
	write nodi "${line:- nessuno}"
	local nv
	nv=$(nvidia_node || true)
	write nodo.nvidia "${nv:-nessuno}"
	if [ -n "$nv" ]; then
		if [ "$nv" = renderD128 ]; then
			ok "the NVIDIA is renderD128 (the node the server encodes on)"
		else
			warning "the NVIDIA is $nv, not renderD128: the SERVER encodes on renderD128 ($line) ⇒ suite (e) is not valid and is skipped; (c) and (d) are done on the right node"
			write verdetto.nodo GIALLO
		fi
	elif [ $missing_driver = 0 ]; then
		ko "the driver is there but no renderD* belongs to the NVIDIA (nvidia-drm not loaded?)"
		write verdetto.nodo ROSSO; red=1
	fi
	# the ICD and vulkaninfo
	local icd
	icd=$(icd_nvidia || true)
	write icd "${icd:-nessuno}"
	ls -l /usr/share/vulkan/icd.d /etc/vulkan/icd.d > "$EVID/icd.txt" 2>&1
	if [ -z "$icd" ]; then
		warning "no NVIDIA Vulkan ICD ⇒ the \"driver\" step installs it (and the installer, without it, would say RX-GPU-004)"
	elif command -v vulkaninfo >/dev/null; then
		VK_DRIVER_FILES=$icd VK_ICD_FILENAMES=$icd vulkaninfo > "$EVID/vulkaninfo.txt" 2>&1
		VK_DRIVER_FILES=$icd VK_ICD_FILENAMES=$icd vulkaninfo --summary > "$EVID/vulkaninfo-riassunto.txt" 2>&1
		local e missing=""
		for e in VK_KHR_video_queue VK_KHR_video_encode_queue VK_KHR_video_encode_h264 VK_KHR_video_encode_h265 \
			VK_EXT_external_memory_dma_buf VK_EXT_image_drm_format_modifier VK_EXT_physical_device_drm; do
			if grep -q "$e" "$EVID/vulkaninfo.txt"; then write "vulkan.$e" si; else write "vulkan.$e" NO; missing="$missing $e"; fi
		done
		if [ -z "$missing" ]; then
			ok "vulkaninfo: H.264 and H.265 encoding, dmabuf, modifiers, DRM node"
		else
			ko "vulkaninfo: missing$missing"
			case "$missing" in *encode*) write verdetto.vulkan ROSSO; red=1 ;; esac
		fi
	fi
	if [ $red = 0 ]; then write verdetto VERDE; ok "checks GREEN"; outcome checks VERDE "$name $ver $nv"
	else write verdetto ROSSO; ko "checks RED (see $f)"; outcome controlli ROSSO "see controlli.txt"; fi
	return $red
}

# ═══════════════════════════════════════════════════════════════════════════
#  THE DRIVER (only if something is missing; the kernel ⇒ reboot)
# ═══════════════════════════════════════════════════════════════════════════
driver() {
	log "the NVIDIA driver, its Vulkan ICD, modeset"
	local restart=0 fam
	fam=$(family)
	"${APT[@]}" update >/dev/null 2>&1
	if ! nvidia-smi >/dev/null 2>&1; then
		warning "the driver is missing: installing it from the distribution"
		if [ "$fam" = debian ]; then
			# non-free and non-free-firmware (the snapshot of /etc/apt is in before/)
			sed -i -E '/^Components:/{/non-free( |$)/!s/$/ contrib non-free non-free-firmware/}' /etc/apt/sources.list.d/*.sources 2>/dev/null
			[ -f /etc/apt/sources.list ] && sed -i -E '/^deb /{/non-free( |$)/!s/$/ contrib non-free non-free-firmware/}' /etc/apt/sources.list
			"${APT[@]}" update >/dev/null 2>&1
			"${APT[@]}" install "linux-headers-$(uname -r)" nvidia-driver nvidia-vulkan-icd firmware-misc-nonfree \
				$(available libnvidia-egl-gbm1 libnvidia-egl-wayland1) > "$EVID/driver-installa.txt" 2>&1 \
				|| { ko "driver installation failed (driver-installa.txt)"; outcome driver ROSSO "installation failed"; return 1; }
		else
			"${APT[@]}" install ubuntu-drivers-common > "$EVID/driver-installa.txt" 2>&1
			ubuntu-drivers devices >> "$EVID/driver-installa.txt" 2>&1
			# ⛔ not "--gpgpu": that is the driver without graphics, WITHOUT libnvidia-gl (no Vulkan ICD)
			ubuntu-drivers install >> "$EVID/driver-installa.txt" 2>&1 \
				|| { ko "ubuntu-drivers install failed (driver-installa.txt)"; outcome driver ROSSO "installation failed"; return 1; }
		fi
		ok "driver installed: a reboot is needed"
		restart=1
	fi
	if ! icd_nvidia >/dev/null; then
		local pk=""
		if [ "$fam" = debian ]; then
			pk=nvidia-vulkan-icd
		else
			local m srv=""
			m=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -1 | cut -d. -f1)
			[ -z "$m" ] && m=$(dpkg-query -W -f='${Package}\n' 'nvidia-driver-*' 'nvidia-headless-*' 2>/dev/null | grep -o -E '[0-9]{3}' | sort -n | tail -n 1)
			dpkg-query -W -f='${Package}\n' 2>/dev/null | grep -q -E "^nvidia-(headless|utils|driver)-$m-server$" && srv=-server
			pk="libnvidia-gl-$m$srv"
		fi
		warning "the NVIDIA Vulkan ICD is missing (\"headless\" driver?): $pk"
		"${APT[@]}" install "$pk" >> "$EVID/driver-installa.txt" 2>&1 \
			&& ok "ICD: $(icd_nvidia || echo 'STILL NOTHING')" \
			|| { ko "$pk does not install: is the driver not the distribution's? Fix by hand"; outcome driver ROSSO "ICD missing"; return 1; }
	fi
	local ms
	ms=$(cat /sys/module/nvidia_drm/parameters/modeset 2>/dev/null || echo "?")
	if [ "$ms" != Y ] && ! grep -q -s 'nvidia-drm modeset=1' /etc/modprobe.d/*.conf; then
		echo 'options nvidia-drm modeset=1' > /etc/modprobe.d/remotix-nv.conf
		command -v update-initramfs >/dev/null && update-initramfs -u >> "$EVID/driver-installa.txt" 2>&1
		ok "nvidia-drm modeset=1 in /etc/modprobe.d/remotix-nv.conf (\"clean\" removes it): a reboot is needed"
		restart=1
	fi
	if [ $restart = 1 ]; then
		outcome driver RIAVVIO "driver/ICD/modeset changed"
		touch "$WORKDIR/riavvio-chiesto"
		return 10
	fi
	ok "driver, ICD and modeset in place: nothing to do"
	outcome driver VERDE "$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"
	return 0
}

# ═══════════════════════════════════════════════════════════════════════════
#  (b) THE DEPENDENCIES: the light desktop, the test tools, the browsers
# ═══════════════════════════════════════════════════════════════════════════
# The spare memory (5 Oct 2026: the rented machine may have 8 GB, the bench asked for 16).
# Without it, when memory runs out the system kills the browser mid-test, and the red would look like the
# product's.  Under 12 GiB and without swap: a 4 GiB file, which "clean" removes.
SPARE=/remotix-nv.scorta
spare() {
	local kib
	kib=$(awk '/MemTotal/{print $2}' /proc/meminfo)
	if [ "$kib" -ge $((12 * 1048576)) ]; then ok "memory $((kib / 1048576)) GiB: no swap needed"; return 0; fi
	if [ -n "$(swapon --noheadings 2>/dev/null)" ]; then ok "memory $((kib / 1048576)) GiB, swap already present: $(swapon --noheadings --show=NAME,SIZE | tr '\n' ' ')"; return 0; fi
	if fallocate -l 4G "$SPARE" 2>/dev/null || dd if=/dev/zero of="$SPARE" bs=1M count=4096 status=none; then
		chmod 600 "$SPARE"
		if mkswap "$SPARE" > /dev/null 2>&1 && swapon "$SPARE" 2>/dev/null; then
			ok "memory $((kib / 1048576)) GiB ⇒ 4 GiB swap turned on ($SPARE)"
			return 0
		fi
	fi
	rm -f "$SPARE"
	warning "memory $((kib / 1048576)) GiB and the swap does not turn on: a red from memory running out must be read in the kernel log (oom)"
}

# Firefox ESR and Chrome, with what the suite's tests need of them (CLIENTS=machine only)
browsers() {
	local fam
	fam=$(family)
	# Firefox ESR: Debian has it; on Ubuntu "firefox" is a snap ⇒ Mozilla's repository
	if [ "$fam" = ubuntu ] && ! has_candidate firefox-esr; then
		install -d -m 0755 /etc/apt/keyrings
		curl -fsSL https://packages.mozilla.org/apt/repo-signing-key.gpg -o /etc/apt/keyrings/packages.mozilla.org.asc
		echo "deb [signed-by=/etc/apt/keyrings/packages.mozilla.org.asc] https://packages.mozilla.org/apt mozilla main" \
			> /etc/apt/sources.list.d/mozilla.list
		"${APT[@]}" update >> "$EVID/dipendenze.txt" 2>&1
	fi
	"${APT[@]}" install --no-install-recommends firefox-esr libpci3 >> "$EVID/dipendenze.txt" 2>&1 \
		&& ok "Firefox ESR: $(firefox-esr --version 2>/dev/null)" \
		|| { ko "firefox-esr does not install"; outcome deps ROSSO "firefox-esr"; return 1; }
	# ⭐ 5 Oct 2026, `[M]` RTX 4090: Firefox ESR 153 (Mozilla's repository) on first start puts
	#    the "Welcome to Firefox / Terms of Use" window ABOVE the test page, and F-003 does not
	#    find it.  The boxes have 140, which does not show it.  ⇒ It is skipped with a Firefox
	#    policy ("clean" removes it together with the package: it is in its folder).
	mkdir -p /usr/lib/firefox-esr/distribution
	printf '%s\n' '{"policies": {"SkipTermsOfUse": true, "DisableTelemetry": true, "DontCheckDefaultBrowser": true, "OverrideFirstRunPage": "", "OverridePostUpdatePage": ""}}' \
		> /usr/lib/firefox-esr/distribution/policies.json
	# ⭐ 5 Oct 2026, `[M]`: Mozilla's package runs Firefox as "firefox-bin", Debian's
	#    as "firefox-esr" — and the suite's tests (F-016/F-017) look for and kill the scene
	#    by NAME (`pgrep -x firefox-esr`).  ⇒ The tests stay IDENTICAL and the name is aligned: a
	#    hard link with the right name, in Firefox's folder ("clean" removes it).
	# ⛔ 6 Oct 2026: it was "only if the link is missing" — after a `clean` and a new run the
	#    hard link was still there and /usr/bin/firefox-esr was not ⇒ F-016 BLOCKED. Always redone
	if [ -x /usr/lib/firefox-esr/firefox-bin ]; then
		ln -f /usr/lib/firefox-esr/firefox-bin /usr/lib/firefox-esr/firefox-esr
		ln -sfn /usr/lib/firefox-esr/firefox-esr /usr/bin/firefox-esr
		touch "$WORKDIR/firefox-esr-nome"
	fi
	# Chrome: Google's .deb (it brings its repository: "clean" removes it with /etc/apt)
	if ! command -v google-chrome >/dev/null; then
		curl -fsSL -o /var/tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
			&& "${APT[@]}" install /var/tmp/google-chrome.deb >> "$EVID/dipendenze.txt" 2>&1
		rm -f /var/tmp/google-chrome.deb
	fi
	command -v google-chrome >/dev/null && ok "Chrome: $(google-chrome --version 2>/dev/null)" \
		|| { ko "Chrome does not install"; outcome deps ROSSO chrome; return 1; }
	# the "firefox" the benches launch (07-b46: `firefox --marionette`) is firefox-esr
	mkdir -p "$SUITCASE/bin"
	ln -sf "$(command -v firefox-esr)" "$SUITCASE/bin/firefox"
	return 0
}

deps() {
	log "(b) the dependencies: XFCE under labwc, tools, Firefox ESR, Chrome"
	local fam
	fam=$(family)
	if [ "$fam" = ubuntu ] && ! grep -q -s -E '^Components:.*universe' /etc/apt/sources.list.d/ubuntu.sources; then
		sed -i -E '/^Components:/{/universe/!s/$/ universe/}' /etc/apt/sources.list.d/ubuntu.sources
		ok "universe enabled (labwc, xfdesktop4, glslc live there)"
	fi
	"${APT[@]}" update > "$EVID/dipendenze.txt" 2>&1
	spare
	# the desktop as in the rete11-xfce box (benches/11-boxes/Containerfile.xfce), without a box
	local desktop=(labwc xfce4-session xfce4-panel xfdesktop4 xfce4-terminal thunar xwayland wlr-randr
		dbus-user-session libpam-systemd sudo fonts-dejavu-core pipewire pipewire-pulse wireplumber wl-clipboard)
	# ⭐ DESKTOP_NV=gnome (6 Oct 2026, user's choice: the remaining rental time on GNOME):
	#    GNOME IN ADDITION to XFCE. The product, finding both, chooses GNOME (session.c,
	#    recognize_desktop); on Ubuntu the default "ubuntu" session (D8). Like the
	#    rete11-gnome box (Containerfile.gnome), without gdm: the product starts the session
	[ "${DESKTOP_NV:-xfce}" = gnome ] && desktop+=(ubuntu-session gnome-shell gnome-session
		gnome-terminal nautilus)
	# ⭐ DESKTOP_NV=kde (6 Oct 2026, user's choice): Plasma like the rete11-kde box
	#    (Containerfile.kde). ⛔ With GNOME present the product chooses GNOME (recognize_desktop):
	#    `gnome-session` is REMOVED first, and that is said
	# ⭐ DESKTOP_NV=lxqt (6 Oct 2026, user's choice): LXQt like the rete11-lxqt box
	#    (Containerfile.lxqt). ⛔ The product chooses KDE before XFCE and XFCE before LXQt
	#    (recognize_desktop): `plasma-workspace` and `xfce4-session` are REMOVED first
	if [ "${DESKTOP_NV:-xfce}" = lxqt ]; then
		# ⚠ and the XFCE packages leave the list, or the installation below would put them back
		local keep=() x
		for x in "${desktop[@]}"; do
			case $x in xfce4-*|xfdesktop4|thunar) ;; *) keep+=("$x") ;; esac
		done
		desktop=("${keep[@]}" lxqt-session lxqt-core qt6-wayland lxqt-menu-data lxqt-powermanagement
			kf6-breeze-icon-theme qt6-svg-plugins)
		local via
		for via in plasma-workspace xfce4-session gnome-session-bin; do
			dpkg-query -W "$via" > /dev/null 2>&1 || continue
			"${APT[@]}" remove "$via" >> "$EVID/dipendenze.txt" 2>&1 \
				&& ok "$via removed: the product must find LXQt"
		done
	fi
	if [ "${DESKTOP_NV:-xfce}" = kde ]; then
		desktop+=(kwin-wayland plasma-workspace plasma-desktop powerdevil konsole dolphin)
		if dpkg-query -W gnome-session-bin > /dev/null 2>&1; then
			"${APT[@]}" remove gnome-session-bin >> "$EVID/dipendenze.txt" 2>&1 \
				&& ok "gnome-session-bin removed: the product must find Plasma, not GNOME"
		fi
	fi
	# the test tools: ffmpeg/ffplay (F-013 and bench 19 MEASURE with ffmpeg: it does not go into the
	# product), python3 with PIL and numpy (the pixel judge), and what is needed to compile bench 19
	local tools=(ffmpeg python3 python3-numpy python3-pil curl ca-certificates gnupg vulkan-tools
		gcc libc6-dev pkg-config libva-dev libvulkan-dev libgbm-dev libdrm-dev glslc)
	# the card: the NVIDIA GBM/EGL bridge, if the driver is the distribution's
	local nv=()
	[ "$fam" = debian ] && mapfile -t nv < <(available libnvidia-egl-gbm1 libnvidia-egl-wayland1)
	if ! "${APT[@]}" install --no-install-recommends "${desktop[@]}" "${tools[@]}" "${nv[@]}" >> "$EVID/dipendenze.txt" 2>&1; then
		ko "apt-get install failed (dipendenze.txt)"; outcome dipendenze ROSSO "apt failed"; return 1
	fi
	ok "desktop and tools"
	# ⭐ 27 Oct 2026: with CLIENTS=home the browsers are at home: nothing of Firefox or Chrome is installed here
	#    (and `clean` has less to take away)
	if [ "$CLIENTS" = machine ]; then
		browsers || return 1
	else
		ok "CLIENTS=home: no Firefox or Chrome on this machine (the browsers are at home)"
	fi
	# the bench user: the browsers do NOT run as root; passwordless sudo to get "into the box"
	# (which here is the machine itself); linger to have /run/user/<uid> and its labwc
	if ! id "$BENCH_USER" >/dev/null 2>&1; then
		useradd -m -s /bin/bash "$BENCH_USER"
	fi
	getent group render >/dev/null || groupadd -r render
	usermod -aG video,render "$BENCH_USER"
	echo "$BENCH_USER ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/remotix-nv
	chmod 0440 /etc/sudoers.d/remotix-nv
	loginctl enable-linger "$BENCH_USER"
	{
		echo "firefox: $(firefox-esr --version 2>/dev/null)"
		echo "chrome: $(google-chrome --version 2>/dev/null)"
		echo "labwc: $(labwc --version 2>/dev/null | head -1)"
		echo "xfce4-session: $(dpkg-query -W -f='${Version}' xfce4-session 2>/dev/null)"
		echo "gnome-shell: $(dpkg-query -W -f='${Version}' gnome-shell 2>/dev/null)"
		echo "plasma-workspace: $(dpkg-query -W -f='${Version}' plasma-workspace 2>/dev/null)"
		echo "lxqt-session: $(dpkg-query -W -f='${Version}' lxqt-session 2>/dev/null)"
		echo "ffmpeg: $(ffmpeg -version 2>/dev/null | head -1)"
		echo "mesa/vulkan loader: $(dpkg-query -W -f='${Version}' libvulkan1 2>/dev/null)"
	} > "$EVID/versioni.txt"
	outcome deps VERDE "$(tr '\n' ' ' < "$EVID/versioni.txt" | cut -c1-200)"
	return 0
}

# ═══════════════════════════════════════════════════════════════════════════
#  (b) REMOTIX, WITH THE INSTALLER
# ═══════════════════════════════════════════════════════════════════════════
remotix() {
	log "(b) REMOTIX from the .deb, with the installer"
	local fam deb ri="$SUITCASE/bin/remotix-install" e=0
	fam=$(family)
	case $fam in
	debian) deb=$(ls "$SUITCASE"/pacchetti/remotix_*deb13*_amd64.deb 2>/dev/null | head -1) ;;
	ubuntu) deb=$(ls "$SUITCASE"/pacchetti/remotix_*ubuntu26.04*_amd64.deb 2>/dev/null | head -1) ;;
	*) deb="" ;;
	esac
	[ -n "$deb" ] || { ko "no .deb for $(distro) in $SUITCASE/pacchetti"; outcome remotix ROSSO "the .deb is missing"; return 1; }
	ok "package: $(basename "$deb")"
	# the installer's preliminary check (read only): RX-GPU-*, the vulkan route, the ICD
	"$ri" check > "$EVID/installatore-verifica.txt" 2>&1
	"$ri" check --json > "$EVID/installatore-verifica.json" 2>&1
	grep -o -E 'RX-[A-Z0-9]+-[0-9]+' "$EVID/installatore-verifica.txt" | sort -u | tr '\n' ' ' > "$WORKDIR/codici-verifica"
	ok "check: codes $(cat "$WORKDIR/codici-verifica")"
	# the single package in small (DECISIONI §10.36): the packages/<target>/ folder with the .deb, and
	# `install` answering "y" to the question like a person
	local tgt
	case $fam in debian) tgt=debian13 ;; ubuntu) tgt=ubuntu2604 ;; esac
	rm -rf "$WORKDIR/bundle"; mkdir -p "$WORKDIR/bundle/$tgt"; cp "$deb" "$WORKDIR/bundle/$tgt/"
	if printf 'y\n' | "$ri" install --bundle "$WORKDIR/bundle" --port "$PORT" --users "$BENCH_USER" \
		> "$EVID/installatore-applica.txt" 2>&1; then
		ok "the installer installed REMOTIX"
		echo installer > "$WORKDIR/come-installato"
	else
		e=$?
		ko "the installer did NOT install (exit $e): $(tail -n 3 "$EVID/installatore-applica.txt" 2>/dev/null | tr '\n' ' ' | cut -c1-300)"
		warning "⇒ the refusal is a result (evidence installer-*); to go on with steps c-e the package is installed with the package manager"
		"${APT[@]}" install "$deb" > "$EVID/remotix-apt.txt" 2>&1 \
			|| { ko "not even apt installs it (remotix-apt.txt)"; outcome remotix ROSSO "not installed"; return 1; }
		usermod -aG video,render "$BENCH_USER"
		echo apt > "$WORKDIR/come-installato"
	fi
	# ⭐ the bench's server: the same unit as the product, with two declared and reversible things:
	#   the name in the certificate (entry from 127.0.0.1) and the detailed log; and stderr to a
	#   FILE, as in the boxes (/var/lib/rete11/registro.log): the suite reads it line by line
	mkdir -p /etc/remotix/remotix.conf.d /etc/systemd/system/remotix.service.d
	printf 'REMOTIX_PORT=%s\nREMOTIX_OPTIONS=--name 127.0.0.1 --verbose\n' "$PORT" > /etc/remotix/remotix.conf.d/remotix-nv.conf
	printf '[Service]\nStandardOutput=append:%s/registro.log\nStandardError=append:%s/registro.log\n' "$WORKDIR" "$WORKDIR" \
		> /etc/systemd/system/remotix.service.d/remotix-nv.conf
	systemctl daemon-reload
	systemctl enable remotix.service >/dev/null 2>&1
	systemctl restart remotix.service
	local i ready=0
	for i in $(seq 1 60); do
		if ss -ltn 2>/dev/null | grep -q ":$PORT "; then ready=1; break; fi
		sleep 1
	done
	if [ $ready = 1 ]; then
		ok "the server listens on $PORT"
		# ⭐ 1.5 (26 Oct 2026): the port is opened by the ROOT side; the network side is a child running as the user
		#   «remotix».  [M] in the container of 19-nv-test-in-container.sh: «fork of the network side: Operation not
		#   permitted» and still «remotix VERDE».  A 1.5 that is not split (the user remotix is absent) is said, not red.
		if id remotix >/dev/null 2>&1; then
			# the criterion of split-box.sh: «--network-side» in the command line (it is born by execve of /proc/self/exe,
			#   so its comm is «exe», not «remotix»), user remotix, parent = the unit's main process (the root side)
			local net="" main
			main=$(systemctl show -p MainPID --value remotix.service 2>/dev/null)
			for i in $(seq 1 30); do
				for net in $(pgrep -u remotix -f -- '--network-side'); do
					[ "$(ps -o ppid= -p "$net" | tr -d ' ')" = "$main" ] && break 2
				done
				net=""; sleep 1
			done
			if [ -n "$net" ]; then
				ok "the network side runs (pid $net, user remotix, child of the root side $main)"
			else
				ko "the network side is NOT running (no «--network-side» process of the user remotix, child of $main, after 30 s)"
				grep -a -E 'network side' "$WORKDIR/registro.log" 2>/dev/null | tail -n 5 | sed 's/^/      /'
				outcome remotix ROSSO "network side not running"; return 1
			fi
		else
			warning "no user remotix: a single-process server (not split)"
		fi
	else
		ko "the server is not listening on $PORT after 60 s"; tail -n 20 "$WORKDIR/registro.log" 2>/dev/null | sed 's/^/      /'
		outcome remotix ROSSO "not listening"; return 1
	fi
	grep -a -E 'route|THIS SERVER CANNOT|HERE_I_AM|offered|⛔|network side' "$WORKDIR/registro.log" | head -20 > "$EVID/server-avvio.txt"
	nv_devices
	"$ri" status > "$EVID/installatore-certifica.txt" 2>&1; local c=$?
	ok "certify: exit $c"
	outcome remotix VERDE "$(cat "$WORKDIR/come-installato") · check: $(cat "$WORKDIR/codici-verifica") · certify $c"
	return 0
}

# ═══════════════════════════════════════════════════════════════════════════
#  (b2) THE PORT, for the clients at home (CLIENTS=home)
# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 27 Oct 2026: the scenes the tests open INSIDE the session (F-021: `turn_on_scene`) are looked for in
#    /opt/remotix, where they live on the boxes. If the folder was not there, it is ours: `clean` removes it.
#    Used by `suite` (CLIENTS=machine) and by `porta` (CLIENTS=home: the tests run at home, the scenes here)
scenes() {
	if [ ! -d /opt/remotix ]; then mkdir -p /opt/remotix && touch "$WORKDIR/opt-remotix-nostra"; fi
	cp "$TREE"/benches/11-boxes/11-c*-scene.html /opt/remotix/ 2>/dev/null
	chmod 755 /opt/remotix; chmod 644 /opt/remotix/*.html 2>/dev/null
}

# does REMOTIX listen on $PORT on an address other than loopback? public_listening tcp|udp
public_listening() {
	local flag=-ltn
	[ "$1" = udp ] && flag=-lun
	ss "$flag" -H 2>/dev/null | awk -v p=":$PORT" '
		{ a = $4; n = length(a) - length(p)
		  if (n > 0 && substr(a, n + 1) == p) { a = substr(a, 1, n); if (a !~ /^127\./ && a != "[::1]") f = 1 } }
		END { exit f ? 0 : 1 }'
}

# the nftables input chains that can block (family table chain, one per line)
nft_chains() {
	command -v nft >/dev/null 2>&1 || return 0
	local fam tab ch
	nft list ruleset 2>/dev/null | awk '
		$1 == "table" { fam = $2; tab = $3 }
		$1 == "chain" { ch = $2 }
		/type filter hook input/ { print fam, tab, ch }' | while read -r fam tab ch; do
		nft list chain "$fam" "$tab" "$ch" 2>/dev/null | grep -q -E 'policy drop|(^|[ ;])(drop|reject)([ ;]|$)' \
			&& echo "$fam $tab $ch"
	done
}

# takes away what `porta` opened (idempotent; `clean` and a new `porta` call it)
fw_close() {
	[ -f "$FWREC" ] || return 0
	local kind a b c d h
	while read -r kind a b c d; do
		case $kind in
		ufw) ufw --force delete allow from "$b" to any port "$c" proto "$a" >/dev/null 2>&1 ;;   # PROTO ADDR PORT
		nft) for h in $(nft -a list chain "$a" "$b" "$c" 2>/dev/null | awk '/comment "remotix-nv"/ {print $NF}'); do
				nft delete rule "$a" "$b" "$c" handle "$h" 2>/dev/null
			done ;;                                                                                 # FAMILY TABLE CHAIN
		esac
	done < "$FWREC"
	rm -f "$FWREC"
}

porta() {
	log "(b2) the port $PORT for the clients at home"
	if [ "$CLIENTS" != home ]; then ok "CLIENTS=machine: the browsers are here, nothing to open"; return 0; fi
	local nv note=""
	nv=$(nvidia_node || true)
	# not a stop (encode and comparison still have to run), but said: as `suite` does, the server encodes on renderD128
	if [ "$nv" != renderD128 ]; then
		warning "the server encodes on renderD128 and the NVIDIA is \"${nv:-none}\": the suite from home would say nothing about the NVIDIA"
		note=" · ⚠ the NVIDIA is not renderD128"
	fi
	# 1. REMOTIX must listen where the clients can reach it, not only on 127.0.0.1
	if public_listening tcp; then
		ok "REMOTIX listens on TCP $PORT on a non-loopback address: $(ss -ltnH 2>/dev/null | awk -v p=":$PORT" '{n=length($4)-length(p); if (substr($4,n+1)==p) print $4}' | tr '\n' ' ')"
	else
		ko "REMOTIX does not listen on TCP $PORT beyond 127.0.0.1 ($(ss -ltnH 2>/dev/null | awk '{print $4}' | grep ":$PORT\$" | tr '\n' ' '))"
		outcome porta ROSSO "not listening beyond loopback"; return 1
	fi
	public_listening udp && ok "REMOTIX listens on UDP $PORT on a non-loopback address" \
		|| warning "no UDP $PORT socket seen beyond loopback: if the product speaks WebTransport the clients will not get in"
	# 2. the scenes the tests will open inside the session
	scenes
	# 3. the firewall: ONLY towards the client's address, and only if one is active
	fw_close
	local fw=none ch fam tab m pr
	if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q '^Status: active'; then
		fw=ufw
	elif [ -n "$(nft_chains)" ]; then
		fw=nftables
	fi
	if [ "$fw" != none ] && ! printf '%s' "$CLIENT_ADDR" | grep -q -E '^[0-9A-Fa-f:.]+$'; then
		ko "a firewall ($fw) is active and the client's address is unknown or odd (\"$CLIENT_ADDR\"): 19-nvidia.sh passes it, or CLIENT_ADDR=…"
		outcome porta ROSSO "firewall $fw, no client address"; return 1
	fi
	: > "$FWREC"
	case $fw in
	ufw)
		for pr in tcp udp; do
			ufw allow from "$CLIENT_ADDR" to any port "$PORT" proto "$pr" >> "$EVID/porta.txt" 2>&1 \
				&& echo "ufw $pr $CLIENT_ADDR $PORT" >> "$FWREC" \
				|| { ko "ufw did not open $pr $PORT (porta.txt)"; outcome porta ROSSO "ufw $pr"; return 1; }
		done
		ok "ufw: $PORT tcp+udp open only from $CLIENT_ADDR" ;;
	nftables)
		case $CLIENT_ADDR in *:*) m=ip6 ;; *) m=ip ;; esac
		while read -r fam tab ch; do
			case "$fam:$m" in ip:ip6|ip6:ip) continue ;; esac     # an address of the other family cannot enter this table
			nft insert rule "$fam" "$tab" "$ch" "$m" saddr "$CLIENT_ADDR" meta l4proto '{ tcp, udp }' th dport "$PORT" \
				accept comment '"remotix-nv"' >> "$EVID/porta.txt" 2>&1 \
				&& echo "nft $fam $tab $ch $PORT" >> "$FWREC" \
				|| { ko "nft did not insert the rule in $fam $tab $ch (porta.txt)"; outcome porta ROSSO "nft $fam $tab $ch"; return 1; }
		done < <(nft_chains)
		[ -s "$FWREC" ] && ok "nftables: $PORT tcp+udp open only from $CLIENT_ADDR ($(awk '{print $4}' "$FWREC" | tr '\n' ' ')chains)" \
			|| warning "nftables blocks, but no table accepts an address of this family: nothing opened" ;;
	*)
		rm -f "$FWREC"
		ok "no active firewall on the machine (ufw/nftables): nothing to open. A firewall of the provider, outside, is not visible from here" ;;
	esac
	outcome porta VERDE "listens beyond loopback · firewall: $fw · open to ${CLIENT_ADDR:-any}$note"
	return 0
}

# a line in passi.txt written from outside (suite-casa): record STEP OUTCOME TEXT
record() {
	local p=${1:-}
	[ -n "$p" ] && [ -n "${2:-}" ] || { echo "usage: $0 record STEP OUTCOME TEXT"; return 2; }
	outcome "$p" "$2" "${3:-}"
	echo "exit 0 · $(date -Is) · from outside" > "$DONE/$p"
}

# ═══════════════════════════════════════════════════════════════════════════
#  (c) THE ENCODING TEST
# ═══════════════════════════════════════════════════════════════════════════
encode() {
	log "(c) remotix --encoding-test"
	local nv f="$EVID/prova-codifica.txt" red=0 c line
	nv=$(nvidia_node || true)
	[ -x "$BIN" ] || { ko "missing $BIN"; outcome encode ROSSO "binary absent"; return 1; }
	: > "$f"
	prova() {  # prova LABEL ARGUMENTS…
		local et=$1; shift
		"$@" > "$WORKDIR/prova.json" 2> "$EVID/prova-codifica-$et.registro"; c=$?
		line=$(tail -n 1 "$WORKDIR/prova.json")
		printf '%s\tcode %s\t%s\n' "$et" "$c" "$line" | tee -a "$f"
	}
	local cod
	for cod in h264 hevc; do
		prova "$cod-predefinito" "$BIN" --encoding-test "$cod"
		echo "$line" | grep -q '"route":"vulkan"' && echo "$line" | grep -q '"outcome":"hardware"' || red=1
		[ -n "$nv" ] && [ "$nv" != renderD128 ] && prova "$cod-$nv" "$BIN" --encoding-test "$cod" --node "/dev/dri/$nv"
		[ -n "$nv" ] && prova "$cod-vulkan-$nv" "$BIN" --encoding-test "$cod" --node "/dev/dri/$nv" --encoding-route vulkan
		prova "$cod-come-$BENCH_USER" runuser -u "$BENCH_USER" -- "$BIN" --encoding-test "$cod"
	done
	if [ $red = 0 ]; then
		ok "H.264 and HEVC on the card, route vulkan"
		outcome encode VERDE "h264 and hevc: route vulkan"
	else
		ko "the route is not \"vulkan\" for H.264 and HEVC (see prova-codifica.txt)"
		outcome encode ROSSO "see prova-codifica.txt"
	fi
	return $red
}

# ═══════════════════════════════════════════════════════════════════════════
#  (d) THE 19-CONFRONTO BENCH ON THE NVIDIA
# ═══════════════════════════════════════════════════════════════════════════
comparison() {
	log "(d) benches/19-vulkan/19-compare.sh on the NVIDIA"
	local nv u="$WORKDIR/confronto"
	nv=$(nvidia_node || true)
	[ -n "$nv" ] || { ko "no NVIDIA node"; outcome comparison ROSSO "no node"; return 1; }
	mkdir -p "$u"
	# ⭐ no "vaapi" among the engines: on the NVIDIA VA-API does not encode (nvidia-vaapi-driver only decodes)
	TREE=$TREE OUTPUT=$u RADEON_NODE=${nv#renderD} ENGINES="vulkan card" PRODUCT_ORDER=1 \
		bash "$TREE/benches/19-vulkan/19-compare.sh" all > "$EVID/confronto.txt" 2>&1
	local c=$?
	cp -f "$u/esiti.jsonl" "$u/tabella.txt" "$u"/capacita-*.json "$EVID/" 2>/dev/null
	local tot good
	tot=$(grep -c . "$u/esiti.jsonl" 2>/dev/null || echo 0)
	# good = code 0, EVERY frame decoded by ffmpeg (the bench's FRAMES, 120), no error
	good=$(python3 - "$u/esiti.jsonl" "${FRAMES:-120}" <<'EOF' 2>/dev/null
import json, sys
n = 0
for r in open(sys.argv[1]):
    try:
        e = json.loads(r)
    except ValueError:
        continue
    if e.get("code") == 0 and str(e.get("decoded")) == sys.argv[2] and not e.get("errori_decodifica"):
        n += 1
print(n)
EOF
)
	if [ "$c" = 0 ] && [ "$tot" -gt 0 ] && [ "${good:-0}" = "$tot" ]; then
		ok "19-compare: $good tests out of $tot with code 0 and every frame decoded"
		outcome comparison VERDE "$good/$tot"
		return 0
	fi
	ko "19-compare: exit $c, $good good tests out of $tot (confronto.txt, esiti.jsonl)"
	outcome comparison ROSSO "$good/$tot, exit $c"
	return 1
}

# ═══════════════════════════════════════════════════════════════════════════
#  (e) THE SUITE: XFCE under labwc (the product starts it), the browsers in a labwc of their own
# ═══════════════════════════════════════════════════════════════════════════
suite() {
	log "(e) the phase 15 suite, subset, on XFCE"
	if [ "$CLIENTS" = home ]; then
		warning "CLIENTS=home: the browsers are at home — run \"19-nvidia.sh suite-casa IP\" on the home server (CLIENTS=machine for the suite here)"
		outcome suite NON-GUARDATA "CLIENTS=home: the suite is run from home (suite-casa)"
		return 3
	fi
	local nv u uid sock="" mode=finestra
	nv=$(nvidia_node || true)
	u="$WORKDIR/suite"
	mkdir -p "$u"
	chown "$BENCH_USER:" "$u" 2>/dev/null
	if [ "$nv" != renderD128 ]; then
		ko "the server encodes on renderD128 and the NVIDIA is \"${nv:-none}\": the suite here would say nothing about the NVIDIA"
		outcome suite NON-GUARDATA "the NVIDIA is not renderD128"
		return 3
	fi
	ss -ltn | grep -q ":$PORT " || { ko "the server is not listening on $PORT"; outcome suite NON-GUARDATA "server off"; return 3; }
	uid=$(id -u "$BENCH_USER")
	# THE BROWSERS' compositor, like benches/15-suite/15-compositors.sh: headless labwc at
	# 3840x2160. ⚠ It draws in software (pixman): it is the client, and must not depend on the card
	# under test. The XFCE session instead is started by the PRODUCT, on the card
	# ⭐ 6 Oct 2026: the scenes the tests open INSIDE the session (F-021: `turn_on_scene`)
	#    are looked for in /opt/remotix, where they live on the boxes. If the folder was not there, it is
	#    ours: `clean` removes it
	scenes
	pkill -u "$BENCH_USER" -x labwc 2>/dev/null
	# ⛔ 5 Oct 2026: `pkill` does not wait. If the previous labwc is still alive, its
	#    "wayland-0" ends up in the "before" list, the new one is reborn with the SAME name and
	#    below nothing new is seen ⇒ HEADLESS browsers (784x512) for a whole run
	local j
	for j in $(seq 1 40); do pgrep -u "$BENCH_USER" -x labwc > /dev/null || break; sleep 0.25; done
	local before
	before=$(ls "/run/user/$uid" 2>/dev/null | grep -E '^wayland-[0-9]+$' | sort)
	# ⭐ CLIENT_CARD=1 (5 Oct 2026): the browsers' compositor on the card (gles2) instead
	#    of in software — ONLY for the counter-test "is the red the software client's?". The
	#    run declares it, and such a run does NOT count as the NVIDIA suite
	local rend=pixman
	[ "${CLIENT_CARD:-0}" = 1 ] && rend=gles2
	runuser -u "$BENCH_USER" -- env -u WAYLAND_DISPLAY -u DISPLAY XDG_RUNTIME_DIR="/run/user/$uid" \
		WLR_BACKENDS=headless WLR_RENDERER=$rend WLR_LIBINPUT_NO_DEVICES=1 \
		setsid labwc < /dev/null > "$u/compositore-browser.log" 2>&1 &
	local i
	for i in $(seq 1 40); do
		sock=$(comm -13 <(echo "$before") <(ls "/run/user/$uid" 2>/dev/null | grep -E '^wayland-[0-9]+$' | sort) | head -1)
		[ -n "$sock" ] && break
		sleep 0.25
	done
	if [ -n "$sock" ]; then
		sleep 0.5
		local usc
		usc=$(runuser -u "$BENCH_USER" -- env XDG_RUNTIME_DIR="/run/user/$uid" WAYLAND_DISPLAY="$sock" wlr-randr 2>/dev/null | awk 'NR==1{print $1}')
		runuser -u "$BENCH_USER" -- env XDG_RUNTIME_DIR="/run/user/$uid" WAYLAND_DISPLAY="$sock" \
			wlr-randr --output "$usc" --custom-mode 3840x2160 >> "$u/compositore-browser.log" 2>&1
		ok "the browsers' compositor: $sock ($usc 3840x2160, $rend)"
		[ "$rend" = pixman ] || warning "⛔ CLIENT_CARD=1: the browsers draw on the card — counter-test, NOT the NVIDIA suite"
	else
		mode=headless
		warning "the browsers' labwc was not born (compositore-browser.log): the browsers go HEADLESS, and that is declared"
	fi
	local system_wide
	system_wide="$(. /etc/os-release; echo "$PRETTY_NAME") · $(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>/dev/null | head -1) · ${DESKTOP_NV:-xfce} · browser: $mode"
	runuser -u "$BENCH_USER" -- env XDG_RUNTIME_DIR="/run/user/$uid" WAYLAND_DISPLAY="$sock" \
		PATH="$SUITCASE/bin:$PATH" RXNV_LOG="$WORKDIR/registro.log" RXNV_SYSTEM="$system_wide" \
		RXNV_VERSION="$(head -1 "$SUITCASE/VERSIONE" 2>/dev/null)" \
		python3 "$HERE/19-nv-suite.py" --log "$u/registro.jsonl" --evidence "$u" \
		--port "$PORT" --mode "$mode" --desktop "${DESKTOP_NV:-xfce}" ${TESTS:+--tests "$TESTS"} ${BROWSER_SUITE:+--browser "$BROWSER_SUITE"} \
		> "$EVID/suite.txt" 2>&1
	local c=$?
	pkill -u "$BENCH_USER" -x labwc 2>/dev/null
	python3 "$TREE/benches/15-suite/15-report.py" --log "$u/registro.jsonl" --round 19-nvidia --text \
		> "$EVID/suite-rapporto.txt" 2>&1
	python3 "$TREE/benches/15-suite/15-report.py" --log "$u/registro.jsonl" --round 19-nvidia \
		--html "$EVID/suite-rapporto.html" > /dev/null 2>&1
	# which route the real sessions took, and whether labwc went on the card or on pixman
	grep -a -E 'route (vulkan|vaapi)|pixman|CANNOT ENCODE|DEVICE_LOST|Xid' "$WORKDIR/registro.log" | sort | uniq -c | sort -rn | head -30 \
		> "$EVID/suite-strade.txt"
	tail -n 3 "$EVID/suite.txt" | sed 's/^/      /'
	case $c in
	0) ok "suite GREEN"; outcome suite VERDE "$(tail -n 1 "$EVID/suite.txt")" ;;
	3) warning "suite with tests not looked at"; outcome suite NON-GUARDATA "$(tail -n 1 "$EVID/suite.txt")" ;;
	*) ko "suite RED"; outcome suite ROSSO "$(tail -n 1 "$EVID/suite.txt")" ;;
	esac
	return $c
}

# ═══════════════════════════════════════════════════════════════════════════
#  (f) COLLECT
# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 26 Oct 2026: the NVIDIA device files and the driver's own modes, BEFORE the suite — 1.5 gives the users the render
#   node only (no more `video`, DECISIONS-11 §11.38): with NVreg_DeviceFileMode 0660 + a group, /dev/nvidia* would be
#   closed to them, the desktop would draw in software and the encoder would find no route, while the log says OK.
nv_devices() {
	ls -l /dev/nvidia* /dev/dri/ > "$EVID/dev-nvidia.txt" 2>&1
	grep -E 'DeviceFile(UID|GID|Mode)|ModifyDeviceFiles' /proc/driver/nvidia/params > "$EVID/nvidia-params.txt" 2>/dev/null
	local mode gid
	mode=$(awk '/DeviceFileMode/{print $2}' "$EVID/nvidia-params.txt" 2>/dev/null)
	gid=$(awk '/DeviceFileGID/{print $2}' "$EVID/nvidia-params.txt" 2>/dev/null)
	if [ -z "$mode" ]; then warning "/proc/driver/nvidia/params unreadable: the device modes are only in dev-nvidia.txt"
	elif [ "$mode" = 438 ]; then ok "NVreg_DeviceFileMode 0666: /dev/nvidia* open to every user"
	else warning "NVreg_DeviceFileMode $(printf '%o' "$mode") gid $gid: /dev/nvidia* NOT open to every user — watch for a black or software desktop (dev-nvidia.txt)"
	fi
}

collect() {
	log "(f) collecting logs and evidence"
	nv_devices
	journalctl -k -b --no-pager 2>/dev/null | grep -a -i 'apparmor=' > "$EVID/apparmor.txt"
	journalctl -b --no-pager > "$EVID/journal.txt" 2>&1
	journalctl -k -b --no-pager > "$EVID/nucleo.txt" 2>&1
	grep -i -E 'NVRM|Xid|nvidia' "$EVID/nucleo.txt" > "$EVID/nucleo-nvidia.txt" 2>/dev/null
	nvidia-smi -q > "$EVID/nvidia-smi-fine.txt" 2>&1
	cp -f "$WORKDIR/registro.log" "$EVID/server-registro.log" 2>/dev/null
	cp -f "$SUITCASE/VERSIONE" "$EVID/" 2>/dev/null
	cp -f "$WORKDIR/piano.json" "$EVID/" 2>/dev/null
	local name
	name="remotix-nv-$(hostname -s)-$(date +%Y%m%d-%H%M).tar.gz"
	# the streams and raw sources of bench 19 stay out: they are heavy, and the outcomes describe them
	tar -C "$WORKDIR" -czf "$WORKDIR/$name" --exclude='*.bin' --exclude='*.bgrx' \
		evidenze confronto suite prima 2>/dev/null
	echo "$name" > "$WORKDIR/archivio"
	sha256sum "$WORKDIR/$name" | cut -d' ' -f1 > "$WORKDIR/archivio.sha256"
	ok "archive: $WORKDIR/$name ($(du -h "$WORKDIR/$name" | cut -f1))"
	outcome collect VERDE "$name"
}

# ═══════════════════════════════════════════════════════════════════════════
#  (g) CLEAN: the machine as we found it
# ═══════════════════════════════════════════════════════════════════════════
clean() {
	log "(g) cleaning"
	if [ ! -f "$WORKDIR/raccolto" ] && [ "${FORCE:-0}" != 1 ]; then
		ko "the archive does not appear to have been taken to the laptop ($WORKDIR/raccolto): first \"19-nvidia.sh collect IP\" (or FORCE=1)"
		return 1
	fi
	[ -f "$BEFORE/fatta" ] || { ko "the snapshot of how the machine was is missing ($BEFORE): I do not know what to remove"; return 1; }
	local restart=0 u
	# 1. the bench's tests and processes
	systemctl stop remotix-nv-banco.service 2>/dev/null
	for u in $(getent passwd | cut -d: -f1 | grep -E "^($BENCH_USER|c[0-9]+b?u[0-9]+)$"); do
		loginctl terminate-user "$u" 2>/dev/null
		pkill -KILL -u "$u" 2>/dev/null
	done
	[ -f "$WORKDIR/opt-remotix-nostra" ] && rm -rf /opt/remotix
	# 1-bis. the firewall rules `porta` opened (CLIENTS=home)
	if [ -f "$FWREC" ]; then fw_close; ok "the firewall rules of the bench removed"; fi
	# 2. REMOTIX: with the installer if it installed it, then our two files
	if [ -x /usr/bin/remotix-install ] || [ -x "$SUITCASE/bin/remotix-install" ]; then
		local ri=/usr/bin/remotix-install
		[ -x $ri ] || ri=$SUITCASE/bin/remotix-install
		if printf 'y\n' | $ri uninstall --purge > "$WORKDIR/disinstalla.txt" 2>&1; then
			ok "REMOTIX uninstalled by the installer"
		else
			warning "the installer did not uninstall (disinstalla.txt): removing with the package manager"
		fi
	fi
	systemctl disable --now remotix.service 2>/dev/null
	rm -f /etc/remotix/remotix.conf.d/remotix-nv.conf /etc/systemd/system/remotix.service.d/remotix-nv.conf
	rmdir /etc/systemd/system/remotix.service.d 2>/dev/null
	systemctl daemon-reload
	# 3. the bench users (the other new users, created by the packages, are DECLARED)
	for u in $(getent passwd | cut -d: -f1 | grep -E "^($BENCH_USER|c[0-9]+b?u[0-9]+)$"); do
		loginctl disable-linger "$u" 2>/dev/null
		userdel -r "$u" > /dev/null 2>&1 || userdel "$u" 2>/dev/null
		rm -rf "/home/${u:?}"
	done
	rm -f /etc/sudoers.d/remotix-nv
	# 3-ter. Firefox: the policy and the aligned name (before the packages: they are in its folder)
	rm -f /usr/lib/firefox-esr/distribution/policies.json
	if [ -f "$WORKDIR/firefox-esr-nome" ]; then
		rm -f /usr/lib/firefox-esr/firefox-esr
		ln -sfn ../lib/firefox-esr/firefox /usr/bin/firefox-esr
	fi
	# 3-bis. the spare memory, if we had added it
	if [ -f "$SPARE" ]; then swapoff "$SPARE" 2>/dev/null; rm -f "$SPARE"; ok "swap removed"; fi
	# 4. modeset, if we had set it
	if [ -f /etc/modprobe.d/remotix-nv.conf ]; then
		rm -f /etc/modprobe.d/remotix-nv.conf
		command -v update-initramfs >/dev/null && update-initramfs -u > /dev/null 2>&1
		restart=1
	fi
	# 5. the NEW packages (those not in the snapshot), driver included if we installed it
	local newcomers
	newcomers=$(comm -13 "$BEFORE/pacchetti.txt" <(installs))
	if [ -n "$newcomers" ]; then
		echo "$newcomers" > "$WORKDIR/pacchetti-tolti.txt"
		echo "$newcomers" | grep -q -E '^(nvidia-driver|nvidia-kernel|nvidia-dkms|linux-headers|linux-modules-nvidia)' && restart=1
		# ⛔ FIRST the simulation: if apt, to remove the new ones, would also remove EVEN ONE package
		#    that was there, nothing is removed and that is said (`[M]` 1 Oct 2026, test in the container:
		#    a blind purge stopped half-way on "sudo" and left dpkg pending)
		local removed report
		# shellcheck disable=SC2086
		removed=$(SUDO_FORCE_REMOVE=yes apt-get -s purge $newcomers 2>/dev/null | awk '/^Purg /{print $2}' | sed 's/:.*//' | sort -u)
		report=$(comm -12 "$BEFORE/pacchetti.txt" <(echo "$removed"))
		if [ -n "$report" ]; then
			warning "apt would also remove packages that were there: $(echo "$report" | tr '\n' ' ') ⇒ removing nothing with the package manager"
		else
			# shellcheck disable=SC2086
			SUDO_FORCE_REMOVE=yes "${APT[@]}" purge $newcomers > "$WORKDIR/purge.txt" 2>&1 \
				&& ok "removed $(echo "$newcomers" | wc -l) new packages" \
				|| warning "apt-get purge with errors (purge.txt)"
		fi
		dpkg --configure -a > /dev/null 2>&1
	fi
	# 6. /etc/apt as it was (Google and Mozilla repositories, non-free, universe)
	rm -rf /etc/apt
	tar -C / -xpf "$BEFORE/etc-apt.tar"
	"${APT[@]}" update > /dev/null 2>&1
	ok "/etc/apt as it was"
	if [ ! -f "$BEFORE/etc-remotix" ]; then rm -rf /etc/remotix /var/lib/remotix; fi
	# 7. what is still different, said
	local after_p after_u
	after_p=$(comm -3 "$BEFORE/pacchetti.txt" <(installs) | tr -d '\t' | tr '\n' ' ')
	after_u=$(comm -13 "$BEFORE/utenti.txt" <(getent passwd | cut -d: -f1 | sort) | tr '\n' ' ')
	{
		echo "packages different from before: ${after_p:-none}"
		echo "extra users (from the packages): ${after_u:-none}"
		echo "reboot recommended: $([ $restart = 1 ] && echo yes || echo no)"
	} | tee "$WORKDIR/pulito.txt" | sed 's/^/    /'
	[ $restart = 1 ] && warning "REBOOT RECOMMENDED: driver or modeset removed"
	ok "clean (the suitcase $SUITCASE and $WORKDIR are removed by the laptop, once the script ends)"
	return 0
}

status() {
	log "where we are"
	local p
	for p in upgrade checks driver deps remotix porta encode comparison suite collect; do
		if [ -f "$DONE/$p" ]; then printf '    %-11s done   %s\n' "$p" "$(cat "$DONE/$p")"; else printf '    %-11s —\n' "$p"; fi
	done
	[ -f "$EVID/passi.txt" ] && { echo; sed 's/^/    /' "$EVID/passi.txt"; }
}

# a step, remembering that it was done (with the exit code): "all" does not redo it
step() {
	local p=$1 c
	"$p"; c=$?
	[ $c != 10 ] && echo "exit $c · $(date -Is)" > "$DONE/$p"
	return $c
}

all() {
	local p c worse=0
	# after the reboot asked for by the "driver" step the checks and the driver are redone: the verdict
	# of (a) must be on the real driver, the one loaded now
	if [ -f "$WORKDIR/riavvio-chiesto" ]; then
		rm -f "$WORKDIR/riavvio-chiesto" "$DONE/checks" "$DONE/driver"
		log "after the reboot: redoing checks and driver"
	fi
	# ⭐ CLIENTS=home: the suite is at home (`suite-casa`) and the evidence is collected AFTER it (`collect`):
	#    here it stops after the comparison.  CLIENTS=machine: the steps are the same as ever
	local steps="upgrade checks driver deps remotix encode comparison suite collect"
	[ "$CLIENTS" = home ] && steps="upgrade checks driver deps remotix porta encode comparison"
	for p in $steps; do
		case " ${REDO:-} " in *" $p "*) rm -f "$DONE/$p" ;; esac
		# porta is redone every time: a firewall rule does not survive a reboot
		if [ -f "$DONE/$p" ] && [ "$p" != collect ] && [ "$p" != porta ]; then
			log "$p: already done ($(cat "$DONE/$p")), skipping"
			continue
		fi
		step "$p"; c=$?
		case $c in
		10) log "A REBOOT IS NEEDED: then \"all\" is run again"; return 10 ;;
		0) ;;
		*)
			[ $c -gt $worse ] && worse=$c
			if [ "$p" = checks ] && [ "${FORCE:-0}" != 1 ]; then
				log "checks RED: stopping (FORCE=1 to go on anyway)"
				collect
				return 1
			fi
			if [ "$p" = deps ] || [ "$p" = remotix ] || [ "$p" = porta ]; then
				log "$p failed: without it, the later steps make no sense"
				collect
				return 1
			fi
			;;
		esac
	done
	log "END"
	sed 's/^/    /' "$EVID/passi.txt"
	[ "$CLIENTS" = home ] && [ $worse = 0 ] && log "the machine is ready: now \"19-nvidia.sh suite-casa IP\" on the home server, then \"collect IP\""
	return $worse
}

ACTION=${1:-status}
case "$ACTION" in
upgrade|checks|driver|deps|remotix|porta|encode|comparison|suite)
	step "$ACTION"; c=$? ;;
collect|clean|status) "$ACTION"; c=$? ;;
record) shift; record "$@"; c=$? ;;
all) all; c=$? ;;
*) echo "usage: $0 upgrade|checks|driver|deps|remotix|porta|encode|comparison|suite|collect|clean|status|record|all"; exit 2 ;;
esac
echo "$c" > "$WORKDIR/uscita"
exit "$c"
