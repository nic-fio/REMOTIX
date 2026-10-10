#!/bin/bash
# 19-nv-macchina.sh — the NVIDIA bench, ON THE RENTED MACHINE, as root.
#
#   bash /opt/remotix-nv/albero/banchi/19-nvidia/19-nv-macchina.sh STEP
#
# Usually no person launches it: `19-nvidia.sh` launches it from the laptop
# (`tutto IP`), in a systemd unit that survives ssh dropping.
#
# THE STEPS, in the order of `tutto` (fasi/19-nvidia.md §2.4, task of 1 Oct 2026):
#   aggiorna     an Ubuntu OLDER than 26.04 is brought to 26.04 with do-release-upgrade,
#                    one hop and one reboot at a time (20.04 ⇒ 22.04 ⇒ 24.04 ⇒ 26.04): the rental companies
#                    offer Ubuntu, and not always 26.04 (5 Oct 2026). ⛔ "pulisci" does NOT undo it
#   controlli    (a) card, driver, DRM nodes, ICD, vulkaninfo with
#                    VK_KHR_video_encode_h264/h265; and the SNAPSHOT of the machine
#                    as it was (packages, /etc/apt, users, units): "pulisci" needs it
#   driver       the NVIDIA driver with its Vulkan ICD and nvidia-drm modeset=1, ONLY
#                    if missing; if it touches the kernel it exits with 10 = reboot
#   dipendenze   (b) XFCE under labwc, the test tools, Firefox ESR, Chrome,
#                    the bench user `rxbanco`
#   remotix      (b) REMOTIX from the `fase-19` .deb WITH THE INSTALLER (plan, apply):
#                    the refusal, if any, is already a result
#   codifica     (c) `remotix --prova-codifica` h264 and hevc: must say route "vulkan"
#   confronto    (d) `banchi/19-vulkan/19-confronto.sh` on the NVIDIA (quality,
#                    decoding of every frame, new canvas, canvas in a LOOP, keyframe, ceiling)
#   suite        (e) the subset of the phase 15 suite (F-001 F-002 F-003 F-011
#                    F-013 F-016 F-018) on XFCE under headless labwc, Firefox and Chrome
#   raccogli     (f) logs and evidence in ONE archive, to take to the laptop
#   pulisci      (g) the machine as we found it (wants the archive already taken away)
#   stato        how far we got
#   tutto        from the first to the last before "pulisci", skipping those already done
#
# Exit: 0 green · 1 red · 3 could not look · 10 a reboot is needed
# (then `tutto` is run again, and it resumes from the next step).
# Variables: PORTA (7447), FORZA=1 (goes on even after a red check), PROVE=f003,f013 and
# BROWSER_SUITE=firefox (only those tests / that browser, to repeat a test), DESKTOP_NV=gnome
# (GNOME in addition to XFCE, and the suite on GNOME; =kde: Plasma, and GNOME removed; =lxqt: LXQt, and the others removed), CLIENTE_SCHEDA=1
# (the browsers draw on the card: counter-test only),
# RIFAI="step step" (redoes steps already done), LAVORO (/var/lib/remotix-nv).
#
# ⛔ Performance is NOT judged here: the times the benches write stay
#    in the evidence, the judgement is on behaviour (decoding, route, tests).
set -u
export LC_ALL=C.UTF-8 DEBIAN_FRONTEND=noninteractive
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
VALIGIA=$(cd "$ALBERO/.." && pwd)
LAVORO=${LAVORO:-/var/lib/remotix-nv}
PRIMA=$LAVORO/prima
FATTO=$LAVORO/fatto
EVID=$LAVORO/evidenze
PORTA=${PORTA:-7447}
UTENTE_BANCO=rxbanco
BIN=/usr/libexec/remotix/remotix
APT=(apt-get -y -q -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold)
mkdir -p "$LAVORO" "$FATTO" "$EVID"

ok()     { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()     { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
avviso() { printf '    \033[1;33m!!\033[0m  %s\n' "$*"; }
log()    { printf '\n\033[1m== %s · %s\033[0m\n' "$(date +%H:%M:%S)" "$*"; }
# one line per step in passi.txt: the summary the laptop shows at the end
esito()  { printf '%s\t%s\t%s\t%s\n' "$(date -Is)" "$1" "$2" "$3" >> "$EVID/passi.txt"; }

distro() { . /etc/os-release; echo "${ID:-?} ${VERSION_ID:-?}"; }
famiglia() {
	case "$(distro)" in
	"debian 13") echo debian ;;
	"ubuntu 26.04") echo ubuntu ;;
	*) echo altra ;;
	esac
}

# the NVIDIA's DRM render node (renderD128…), "" if absent
nodo_nvidia() {
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
candidato() { apt-cache policy "$1" 2>/dev/null | awk '/Candidate:/{print $2}' | grep -q -v -e "(none)" -e "^$"; }
disponibili() { local p; for p; do candidato "$p" && echo "$p"; done; }

# installed: "ii", but also "it"/"iU" (installed, with triggers or configuration pending)
installati() { dpkg-query -W -f='${db:Status-Abbrev} ${Package}\n' 2>/dev/null | awk '$1 ~ /^i/{print $2}' | sort -u; }

# ═══════════════════════════════════════════════════════════════════════════
#  THE SNAPSHOT OF THE MACHINE AS IT WAS (once only: it is pulisci's "before")
# ═══════════════════════════════════════════════════════════════════════════
fotografa_prima() {
	[ -f "$PRIMA/fatta" ] && return 0
	mkdir -p "$PRIMA"
	installati > "$PRIMA/pacchetti.txt"
	apt-mark showmanual 2>/dev/null | sort > "$PRIMA/manuali.txt"
	tar -C / -cpf "$PRIMA/etc-apt.tar" etc/apt
	getent passwd | cut -d: -f1 | sort > "$PRIMA/utenti.txt"
	ls /etc/modprobe.d > "$PRIMA/modprobe.txt" 2>/dev/null
	systemctl list-unit-files --state=enabled --no-legend 2>/dev/null | awk '{print $1}' | sort > "$PRIMA/unita.txt"
	[ -e /etc/remotix ] && echo si > "$PRIMA/etc-remotix"
	cat /proc/cmdline > "$PRIMA/cmdline.txt"
	date -Is > "$PRIMA/fatta"
	ok "snapshot of the machine as it was: $(wc -l < "$PRIMA/pacchetti.txt") packages, $(wc -l < "$PRIMA/utenti.txt") users"
}

# ═══════════════════════════════════════════════════════════════════════════
#  (a) THE CHECKS
# ═══════════════════════════════════════════════════════════════════════════
# Old Ubuntu ⇒ a version hop and a reboot (exit 10); 26.04 or Debian 13 ⇒ nothing.
# ⛔ Irreversible: the machine is returned upgraded, and "pulisci" declares it.
aggiorna() {
	log "(0) the system version"
	. /etc/os-release
	if [ "${ID:-}" != ubuntu ] || [ "$(famiglia)" != altra ]; then
		ok "$(distro): nothing to upgrade"
		return 0
	fi
	local da=$VERSION_ID f="$EVID/aggiorna-$VERSION_ID.txt"
	case "$da" in 20.04|22.04|24.04) ;; *) ko "ubuntu $da: I can only upgrade from 20.04, 22.04 and 24.04"; esito aggiorna ROSSO "ubuntu $da"; return 1 ;; esac
	[ "$(id -u)" = 0 ] || { ko "root is required"; return 1; }
	# do-release-upgrade refuses if the system is not up to date or is waiting for a reboot
	log "ubuntu $da: first upgrading the packages of $da"
	{ "${APT[@]}" update && "${APT[@]}" dist-upgrade && "${APT[@]}" install ubuntu-release-upgrader-core; } > "$f" 2>&1 \
		|| { ko "upgrade of $da failed ($f)"; esito aggiorna ROSSO "dist-upgrade $da"; return 1; }
	if [ -f /var/run/reboot-required ]; then
		touch "$LAVORO/riavvio-chiesto"
		log "the upgraded $da asks for a reboot before the hop"
		return 10
	fi
	sed -i -E 's/^Prompt=.*/Prompt=lts/' /etc/update-manager/release-upgrades 2>/dev/null
	log "ubuntu $da: hop to the next LTS version (half an hour or more)"
	# -f DistUpgradeViewNonInteractive: no questions, changed configuration files are kept
	if ! do-release-upgrade -f DistUpgradeViewNonInteractive >> "$f" 2>&1; then
		# before the .1 the hop between LTS is not offered yet: -d forces it
		if grep -q -i "no new release" "$f"; then
			avviso "the hop is not offered yet: forcing it with -d"
			do-release-upgrade -d -f DistUpgradeViewNonInteractive >> "$f" 2>&1 \
				|| { ko "do-release-upgrade -d failed ($f)"; esito aggiorna ROSSO "hop from $da"; return 1; }
		else
			ko "do-release-upgrade failed ($f)"; esito aggiorna ROSSO "hop from $da"; return 1
		fi
	fi
	esito aggiorna RIAVVIO "ubuntu $da ⇒ $(. /etc/os-release; echo "$VERSION_ID")"
	touch "$LAVORO/riavvio-chiesto"
	return 10
}

controlli() {
	log "(a) the initial checks"
	local f="$EVID/controlli.txt" rosso=0 manca_driver=0
	: > "$f"
	scrivi() { printf '%s: %s\n' "$1" "$2" >> "$f"; }
	[ "$(id -u)" = 0 ] || { ko "root is required"; return 1; }
	scrivi distribuzione "$(. /etc/os-release; echo "$PRETTY_NAME")"
	scrivi nucleo "$(uname -r)"
	scrivi processore "$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2- | sed 's/^ //') ($(nproc) threads)"
	scrivi memoria "$(awk '/MemTotal/{printf "%.0f GiB", $2/1048576}' /proc/meminfo)"
	if [ "$(famiglia)" = altra ]; then
		ko "distribution $(distro): REMOTIX wants Debian 13 or Ubuntu 26.04 (OpenSSL 3.5, labwc, libei)"
		scrivi verdetto.distribuzione ROSSO; rosso=1
	else
		ok "distribution $(distro)"
		scrivi verdetto.distribuzione VERDE
	fi
	fotografa_prima
	# the check's tools: few, and if we install them "pulisci" removes them
	if ! command -v vulkaninfo >/dev/null || ! command -v lspci >/dev/null; then
		"${APT[@]}" update >/dev/null 2>&1
		"${APT[@]}" install --no-install-recommends vulkan-tools pciutils >/dev/null 2>&1 \
			&& ok "vulkan-tools and pciutils installed to look" || avviso "vulkan-tools/pciutils not installed"
	fi
	# the card, from the bus: it is there even without a driver
	local pci
	pci=$(lspci -nn 2>/dev/null | grep -i -E 'vga|3d|display' | grep -i '10de' || true)
	if [ -z "$pci" ]; then
		ko "no NVIDIA card on the PCI bus"
		scrivi verdetto.scheda ROSSO; rosso=1
	else
		ok "card: $pci"
		scrivi scheda "$pci"
	fi
	lspci -nnk > "$EVID/lspci.txt" 2>&1
	# the driver
	local nome="" ver="" maggiore=0
	if command -v nvidia-smi >/dev/null && nvidia-smi >/dev/null 2>&1; then
		nome=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
		ver=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)
		maggiore=${ver%%.*}
		nvidia-smi -q > "$EVID/nvidia-smi.txt" 2>&1
		scrivi scheda.nome "$nome"; scrivi driver.versione "$ver"
		if [ "${maggiore:-0}" -ge 550 ] 2>/dev/null; then
			ok "driver NVIDIA $ver ($nome)"
		else
			ko "NVIDIA driver $ver: 550 or newer is required (Vulkan Video encode)"
			scrivi verdetto.driver ROSSO; rosso=1
		fi
		# ⛔ the compute cards without NVENC (A100, H100…): Vulkan Video encode is not there
		if echo "$nome" | grep -q -E '(^|[ -])(A100|A800|A30|H100|H200|H800|B100|B200|GH200)([ -]|$)'; then
			ko "$nome has no video encoder (NVENC): REMOTIX cannot encode here"
			scrivi verdetto.nvenc ROSSO; rosso=1
		fi
		grep -i -A3 'Encoder Stats' "$EVID/nvidia-smi.txt" > /dev/null 2>&1 && scrivi nvenc "encoder statistics present in nvidia-smi -q"
	else
		avviso "nvidia-smi does not answer: the driver is missing (or not loaded) ⇒ the \"driver\" step installs it"
		scrivi driver.versione nessuno; manca_driver=1
	fi
	# the modules and modeset
	local ms
	ms=$(cat /sys/module/nvidia_drm/parameters/modeset 2>/dev/null || echo "?")
	scrivi nvidia_drm.modeset "$ms"
	grep -E '^nvidia' /proc/modules > "$EVID/moduli.txt" 2>&1
	[ "$ms" = Y ] && ok "nvidia-drm modeset=Y" || avviso "nvidia-drm modeset=$ms ⇒ the \"driver\" step sets it to 1 (GBM needs it, i.e. labwc on the card)"
	# the DRM nodes
	local n d riga=""
	for n in /dev/dri/card* /dev/dri/renderD*; do
		[ -e "$n" ] || continue
		d=$(basename "$(readlink -f "/sys/class/drm/$(basename "$n")/device/driver")" 2>/dev/null)
		riga="$riga $(basename "$n")=$d"
	done
	scrivi nodi "${riga:- nessuno}"
	local nv
	nv=$(nodo_nvidia || true)
	scrivi nodo.nvidia "${nv:-nessuno}"
	if [ -n "$nv" ]; then
		if [ "$nv" = renderD128 ]; then
			ok "the NVIDIA is renderD128 (the node the server encodes on)"
		else
			avviso "the NVIDIA is $nv, not renderD128: the SERVER encodes on renderD128 ($riga) ⇒ suite (e) is not valid and is skipped; (c) and (d) are done on the right node"
			scrivi verdetto.nodo GIALLO
		fi
	elif [ $manca_driver = 0 ]; then
		ko "the driver is there but no renderD* belongs to the NVIDIA (nvidia-drm not loaded?)"
		scrivi verdetto.nodo ROSSO; rosso=1
	fi
	# the ICD and vulkaninfo
	local icd
	icd=$(icd_nvidia || true)
	scrivi icd "${icd:-nessuno}"
	ls -l /usr/share/vulkan/icd.d /etc/vulkan/icd.d > "$EVID/icd.txt" 2>&1
	if [ -z "$icd" ]; then
		avviso "no NVIDIA Vulkan ICD ⇒ the \"driver\" step installs it (and the installer, without it, would say RX-GPU-004)"
	elif command -v vulkaninfo >/dev/null; then
		VK_DRIVER_FILES=$icd VK_ICD_FILENAMES=$icd vulkaninfo > "$EVID/vulkaninfo.txt" 2>&1
		VK_DRIVER_FILES=$icd VK_ICD_FILENAMES=$icd vulkaninfo --summary > "$EVID/vulkaninfo-riassunto.txt" 2>&1
		local e mancano=""
		for e in VK_KHR_video_queue VK_KHR_video_encode_queue VK_KHR_video_encode_h264 VK_KHR_video_encode_h265 \
			VK_EXT_external_memory_dma_buf VK_EXT_image_drm_format_modifier VK_EXT_physical_device_drm; do
			if grep -q "$e" "$EVID/vulkaninfo.txt"; then scrivi "vulkan.$e" si; else scrivi "vulkan.$e" NO; mancano="$mancano $e"; fi
		done
		if [ -z "$mancano" ]; then
			ok "vulkaninfo: H.264 and H.265 encoding, dmabuf, modifiers, DRM node"
		else
			ko "vulkaninfo: missing$mancano"
			case "$mancano" in *encode*) scrivi verdetto.vulkan ROSSO; rosso=1 ;; esac
		fi
	fi
	if [ $rosso = 0 ]; then scrivi verdetto VERDE; ok "checks GREEN"; esito controlli VERDE "$nome $ver $nv"
	else scrivi verdetto ROSSO; ko "checks RED (see $f)"; esito controlli ROSSO "see controlli.txt"; fi
	return $rosso
}

# ═══════════════════════════════════════════════════════════════════════════
#  THE DRIVER (only if something is missing; the kernel ⇒ reboot)
# ═══════════════════════════════════════════════════════════════════════════
driver() {
	log "the NVIDIA driver, its Vulkan ICD, modeset"
	local riavvio=0 fam
	fam=$(famiglia)
	"${APT[@]}" update >/dev/null 2>&1
	if ! nvidia-smi >/dev/null 2>&1; then
		avviso "the driver is missing: installing it from the distribution"
		if [ "$fam" = debian ]; then
			# non-free and non-free-firmware (the snapshot of /etc/apt is in prima/)
			sed -i -E '/^Components:/{/non-free( |$)/!s/$/ contrib non-free non-free-firmware/}' /etc/apt/sources.list.d/*.sources 2>/dev/null
			[ -f /etc/apt/sources.list ] && sed -i -E '/^deb /{/non-free( |$)/!s/$/ contrib non-free non-free-firmware/}' /etc/apt/sources.list
			"${APT[@]}" update >/dev/null 2>&1
			"${APT[@]}" install "linux-headers-$(uname -r)" nvidia-driver nvidia-vulkan-icd firmware-misc-nonfree \
				$(disponibili libnvidia-egl-gbm1 libnvidia-egl-wayland1) > "$EVID/driver-installa.txt" 2>&1 \
				|| { ko "driver installation failed (driver-installa.txt)"; esito driver ROSSO "installation failed"; return 1; }
		else
			"${APT[@]}" install ubuntu-drivers-common > "$EVID/driver-installa.txt" 2>&1
			ubuntu-drivers devices >> "$EVID/driver-installa.txt" 2>&1
			# ⛔ not "--gpgpu": that is the driver without graphics, WITHOUT libnvidia-gl (no Vulkan ICD)
			ubuntu-drivers install >> "$EVID/driver-installa.txt" 2>&1 \
				|| { ko "ubuntu-drivers install failed (driver-installa.txt)"; esito driver ROSSO "installation failed"; return 1; }
		fi
		ok "driver installed: a reboot is needed"
		riavvio=1
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
		avviso "the NVIDIA Vulkan ICD is missing (\"headless\" driver?): $pk"
		"${APT[@]}" install "$pk" >> "$EVID/driver-installa.txt" 2>&1 \
			&& ok "ICD: $(icd_nvidia || echo 'STILL NOTHING')" \
			|| { ko "$pk does not install: is the driver not the distribution's? Fix by hand"; esito driver ROSSO "ICD missing"; return 1; }
	fi
	local ms
	ms=$(cat /sys/module/nvidia_drm/parameters/modeset 2>/dev/null || echo "?")
	if [ "$ms" != Y ] && ! grep -q -s 'nvidia-drm modeset=1' /etc/modprobe.d/*.conf; then
		echo 'options nvidia-drm modeset=1' > /etc/modprobe.d/remotix-nv.conf
		command -v update-initramfs >/dev/null && update-initramfs -u >> "$EVID/driver-installa.txt" 2>&1
		ok "nvidia-drm modeset=1 in /etc/modprobe.d/remotix-nv.conf (\"pulisci\" removes it): a reboot is needed"
		riavvio=1
	fi
	if [ $riavvio = 1 ]; then
		esito driver RIAVVIO "driver/ICD/modeset changed"
		touch "$LAVORO/riavvio-chiesto"
		return 10
	fi
	ok "driver, ICD and modeset in place: nothing to do"
	esito driver VERDE "$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"
	return 0
}

# ═══════════════════════════════════════════════════════════════════════════
#  (b) THE DEPENDENCIES: the light desktop, the test tools, the browsers
# ═══════════════════════════════════════════════════════════════════════════
# The spare memory (5 Oct 2026: the rented machine may have 8 GB, the bench asked for 16).
# Without it, when memory runs out the system kills the browser mid-test, and the red would look like the
# product's.  Under 12 GiB and without swap: a 4 GiB file, which "pulisci" removes.
SCORTA=/remotix-nv.scorta
scorta() {
	local kib
	kib=$(awk '/MemTotal/{print $2}' /proc/meminfo)
	if [ "$kib" -ge $((12 * 1048576)) ]; then ok "memory $((kib / 1048576)) GiB: no swap needed"; return 0; fi
	if [ -n "$(swapon --noheadings 2>/dev/null)" ]; then ok "memory $((kib / 1048576)) GiB, swap already present: $(swapon --noheadings --show=NAME,SIZE | tr '\n' ' ')"; return 0; fi
	if fallocate -l 4G "$SCORTA" 2>/dev/null || dd if=/dev/zero of="$SCORTA" bs=1M count=4096 status=none; then
		chmod 600 "$SCORTA"
		if mkswap "$SCORTA" > /dev/null 2>&1 && swapon "$SCORTA" 2>/dev/null; then
			ok "memory $((kib / 1048576)) GiB ⇒ 4 GiB swap turned on ($SCORTA)"
			return 0
		fi
	fi
	rm -f "$SCORTA"
	avviso "memory $((kib / 1048576)) GiB and the swap does not turn on: a red from memory running out must be read in the kernel log (oom)"
}

dipendenze() {
	log "(b) the dependencies: XFCE under labwc, tools, Firefox ESR, Chrome"
	local fam
	fam=$(famiglia)
	if [ "$fam" = ubuntu ] && ! grep -q -s -E '^Components:.*universe' /etc/apt/sources.list.d/ubuntu.sources; then
		sed -i -E '/^Components:/{/universe/!s/$/ universe/}' /etc/apt/sources.list.d/ubuntu.sources
		ok "universe enabled (labwc, xfdesktop4, glslc live there)"
	fi
	"${APT[@]}" update > "$EVID/dipendenze.txt" 2>&1
	scorta
	# the desktop as in the rete11-xfce box (banchi/11-scatole/Contenitore.xfce), without a box
	local desktop=(labwc xfce4-session xfce4-panel xfdesktop4 xfce4-terminal thunar xwayland wlr-randr
		dbus-user-session libpam-systemd sudo fonts-dejavu-core pipewire pipewire-pulse wireplumber wl-clipboard)
	# ⭐ DESKTOP_NV=gnome (6 Oct 2026, user's choice: the remaining rental time on GNOME):
	#    GNOME IN ADDITION to XFCE. The product, finding both, chooses GNOME (sessione.c,
	#    riconosci_desktop); on Ubuntu the default "ubuntu" session (D8). Like the
	#    rete11-gnome box (Contenitore.gnome), without gdm: the product starts the session
	[ "${DESKTOP_NV:-xfce}" = gnome ] && desktop+=(ubuntu-session gnome-shell gnome-session
		gnome-terminal nautilus)
	# ⭐ DESKTOP_NV=kde (6 Oct 2026, user's choice): Plasma like the rete11-kde box
	#    (Contenitore.kde). ⛔ With GNOME present the product chooses GNOME (riconosci_desktop):
	#    `gnome-session` is REMOVED first, and that is said
	# ⭐ DESKTOP_NV=lxqt (6 Oct 2026, user's choice): LXQt like the rete11-lxqt box
	#    (Contenitore.lxqt). ⛔ The product chooses KDE before XFCE and XFCE before LXQt
	#    (riconosci_desktop): `plasma-workspace` and `xfce4-session` are REMOVED first
	if [ "${DESKTOP_NV:-xfce}" = lxqt ]; then
		# ⚠ and the XFCE packages leave the list, or the installation below would put them back
		local tieni=() x
		for x in "${desktop[@]}"; do
			case $x in xfce4-*|xfdesktop4|thunar) ;; *) tieni+=("$x") ;; esac
		done
		desktop=("${tieni[@]}" lxqt-session lxqt-core qt6-wayland lxqt-menu-data lxqt-powermanagement
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
	local attrezzi=(ffmpeg python3 python3-numpy python3-pil curl ca-certificates gnupg vulkan-tools
		gcc libc6-dev pkg-config libva-dev libvulkan-dev libgbm-dev libdrm-dev glslc)
	# the card: the NVIDIA GBM/EGL bridge, if the driver is the distribution's
	local nv=()
	[ "$fam" = debian ] && mapfile -t nv < <(disponibili libnvidia-egl-gbm1 libnvidia-egl-wayland1)
	if ! "${APT[@]}" install --no-install-recommends "${desktop[@]}" "${attrezzi[@]}" "${nv[@]}" >> "$EVID/dipendenze.txt" 2>&1; then
		ko "apt-get install failed (dipendenze.txt)"; esito dipendenze ROSSO "apt failed"; return 1
	fi
	ok "desktop and tools"
	# Firefox ESR: Debian has it; on Ubuntu "firefox" is a snap ⇒ Mozilla's repository
	if [ "$fam" = ubuntu ] && ! candidato firefox-esr; then
		install -d -m 0755 /etc/apt/keyrings
		curl -fsSL https://packages.mozilla.org/apt/repo-signing-key.gpg -o /etc/apt/keyrings/packages.mozilla.org.asc
		echo "deb [signed-by=/etc/apt/keyrings/packages.mozilla.org.asc] https://packages.mozilla.org/apt mozilla main" \
			> /etc/apt/sources.list.d/mozilla.list
		"${APT[@]}" update >> "$EVID/dipendenze.txt" 2>&1
	fi
	"${APT[@]}" install --no-install-recommends firefox-esr libpci3 >> "$EVID/dipendenze.txt" 2>&1 \
		&& ok "Firefox ESR: $(firefox-esr --version 2>/dev/null)" \
		|| { ko "firefox-esr does not install"; esito dipendenze ROSSO "firefox-esr"; return 1; }
	# ⭐ 5 Oct 2026, `[M]` RTX 4090: Firefox ESR 153 (Mozilla's repository) on first start puts
	#    the "Welcome to Firefox / Terms of Use" window ABOVE the test page, and F-003 does not
	#    find it.  The boxes have 140, which does not show it.  ⇒ It is skipped with a Firefox
	#    policy ("pulisci" removes it together with the package: it is in its folder).
	mkdir -p /usr/lib/firefox-esr/distribution
	printf '%s\n' '{"policies": {"SkipTermsOfUse": true, "DisableTelemetry": true, "DontCheckDefaultBrowser": true, "OverrideFirstRunPage": "", "OverridePostUpdatePage": ""}}' \
		> /usr/lib/firefox-esr/distribution/policies.json
	# ⭐ 5 Oct 2026, `[M]`: Mozilla's package runs Firefox as "firefox-bin", Debian's
	#    as "firefox-esr" — and the suite's tests (F-016/F-017) look for and kill the scene
	#    by NAME (`pgrep -x firefox-esr`).  ⇒ The tests stay IDENTICAL and the name is aligned: a
	#    hard link with the right name, in Firefox's folder ("pulisci" removes it).
	# ⛔ 6 Oct 2026: it was "only if the link is missing" — after a `pulisci` and a new run the
	#    hard link was still there and /usr/bin/firefox-esr was not ⇒ F-016 BLOCKED. Always redone
	if [ -x /usr/lib/firefox-esr/firefox-bin ]; then
		ln -f /usr/lib/firefox-esr/firefox-bin /usr/lib/firefox-esr/firefox-esr
		ln -sfn /usr/lib/firefox-esr/firefox-esr /usr/bin/firefox-esr
		touch "$LAVORO/firefox-esr-nome"
	fi
	# Chrome: Google's .deb (it brings its repository: "pulisci" removes it with /etc/apt)
	if ! command -v google-chrome >/dev/null; then
		curl -fsSL -o /var/tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
			&& "${APT[@]}" install /var/tmp/google-chrome.deb >> "$EVID/dipendenze.txt" 2>&1
		rm -f /var/tmp/google-chrome.deb
	fi
	command -v google-chrome >/dev/null && ok "Chrome: $(google-chrome --version 2>/dev/null)" \
		|| { ko "Chrome does not install"; esito dipendenze ROSSO chrome; return 1; }
	# the "firefox" the benches launch (07-b46: `firefox --marionette`) is firefox-esr
	mkdir -p "$VALIGIA/bin"
	ln -sf "$(command -v firefox-esr)" "$VALIGIA/bin/firefox"
	# the bench user: the browsers do NOT run as root; passwordless sudo to get "into the box"
	# (which here is the machine itself); linger to have /run/user/<uid> and its labwc
	if ! id "$UTENTE_BANCO" >/dev/null 2>&1; then
		useradd -m -s /bin/bash "$UTENTE_BANCO"
	fi
	getent group render >/dev/null || groupadd -r render
	usermod -aG video,render "$UTENTE_BANCO"
	echo "$UTENTE_BANCO ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/remotix-nv
	chmod 0440 /etc/sudoers.d/remotix-nv
	loginctl enable-linger "$UTENTE_BANCO"
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
	esito dipendenze VERDE "$(tr '\n' ' ' < "$EVID/versioni.txt" | cut -c1-200)"
	return 0
}

# ═══════════════════════════════════════════════════════════════════════════
#  (b) REMOTIX, WITH THE INSTALLER
# ═══════════════════════════════════════════════════════════════════════════
remotix() {
	log "(b) REMOTIX from the .deb, with the installer"
	local fam deb ri="$VALIGIA/bin/remotix-install" e=0
	fam=$(famiglia)
	case $fam in
	debian) deb=$(ls "$VALIGIA"/pacchetti/remotix_*deb13*_amd64.deb 2>/dev/null | head -1) ;;
	ubuntu) deb=$(ls "$VALIGIA"/pacchetti/remotix_*ubuntu26.04*_amd64.deb 2>/dev/null | head -1) ;;
	*) deb="" ;;
	esac
	[ -n "$deb" ] || { ko "no .deb for $(distro) in $VALIGIA/pacchetti"; esito remotix ROSSO "the .deb is missing"; return 1; }
	ok "package: $(basename "$deb")"
	# the installer's preliminary check (read only): RX-GPU-*, the vulkan route, the ICD
	"$ri" check > "$EVID/installatore-verifica.txt" 2>&1
	"$ri" check --json > "$EVID/installatore-verifica.json" 2>&1
	grep -o -E 'RX-[A-Z0-9]+-[0-9]+' "$EVID/installatore-verifica.txt" | sort -u | tr '\n' ' ' > "$LAVORO/codici-verifica"
	ok "check: codes $(cat "$LAVORO/codici-verifica")"
	# the single package in small (DECISIONI §10.36): the packages/<target>/ folder with the .deb, and
	# `install` answering "y" to the question like a person
	local bers
	case $fam in debian) bers=debian13 ;; ubuntu) bers=ubuntu2604 ;; esac
	rm -rf "$LAVORO/bundle"; mkdir -p "$LAVORO/bundle/$bers"; cp "$deb" "$LAVORO/bundle/$bers/"
	if printf 'y\n' | "$ri" install --bundle "$LAVORO/bundle" --port "$PORTA" --users "$UTENTE_BANCO" \
		> "$EVID/installatore-applica.txt" 2>&1; then
		ok "the installer installed REMOTIX"
		echo installatore > "$LAVORO/come-installato"
	else
		e=$?
		ko "the installer did NOT install (exit $e): $(tail -n 3 "$EVID/installatore-applica.txt" 2>/dev/null | tr '\n' ' ' | cut -c1-300)"
		avviso "⇒ the refusal is a result (evidence installatore-*); to go on with steps c-e the package is installed with the package manager"
		"${APT[@]}" install "$deb" > "$EVID/remotix-apt.txt" 2>&1 \
			|| { ko "not even apt installs it (remotix-apt.txt)"; esito remotix ROSSO "not installed"; return 1; }
		usermod -aG video,render "$UTENTE_BANCO"
		echo apt > "$LAVORO/come-installato"
	fi
	# ⭐ the bench's server: the same unit as the product, with two declared and reversible things:
	#   the name in the certificate (entry from 127.0.0.1) and the detailed log; and stderr to a
	#   FILE, as in the boxes (/var/lib/rete11/registro.log): the suite reads it line by line
	mkdir -p /etc/remotix/remotix.conf.d /etc/systemd/system/remotix.service.d
	printf 'REMOTIX_PORTA=%s\nREMOTIX_OPZIONI=--nome 127.0.0.1 --parlantina\n' "$PORTA" > /etc/remotix/remotix.conf.d/remotix-nv.conf
	printf '[Service]\nStandardOutput=append:%s/registro.log\nStandardError=append:%s/registro.log\n' "$LAVORO" "$LAVORO" \
		> /etc/systemd/system/remotix.service.d/remotix-nv.conf
	systemctl daemon-reload
	systemctl enable remotix.service >/dev/null 2>&1
	systemctl restart remotix.service
	local i pronto=0
	for i in $(seq 1 60); do
		if ss -ltn 2>/dev/null | grep -q ":$PORTA "; then pronto=1; break; fi
		sleep 1
	done
	if [ $pronto = 1 ]; then
		ok "the server listens on $PORTA"
	else
		ko "the server is not listening on $PORTA after 60 s"; tail -n 20 "$LAVORO/registro.log" 2>/dev/null | sed 's/^/      /'
		esito remotix ROSSO "not listening"; return 1
	fi
	grep -a -E 'route|THIS SERVER CANNOT|ECCOMI|offered|⛔' "$LAVORO/registro.log" | head -20 > "$EVID/server-avvio.txt"
	"$ri" status > "$EVID/installatore-certifica.txt" 2>&1; local c=$?
	ok "certify: exit $c"
	esito remotix VERDE "$(cat "$LAVORO/come-installato") · check: $(cat "$LAVORO/codici-verifica") · certify $c"
	return 0
}

# ═══════════════════════════════════════════════════════════════════════════
#  (c) THE ENCODING TEST
# ═══════════════════════════════════════════════════════════════════════════
codifica() {
	log "(c) remotix --prova-codifica"
	local nv f="$EVID/prova-codifica.txt" rosso=0 c riga
	nv=$(nodo_nvidia || true)
	[ -x "$BIN" ] || { ko "missing $BIN"; esito codifica ROSSO "binary absent"; return 1; }
	: > "$f"
	prova() {  # prova LABEL ARGUMENTS…
		local et=$1; shift
		"$@" > "$LAVORO/prova.json" 2> "$EVID/prova-codifica-$et.registro"; c=$?
		riga=$(tail -n 1 "$LAVORO/prova.json")
		printf '%s\tcode %s\t%s\n' "$et" "$c" "$riga" | tee -a "$f"
	}
	local cod
	for cod in h264 hevc; do
		prova "$cod-predefinito" "$BIN" --prova-codifica "$cod"
		echo "$riga" | grep -q '"strada":"vulkan"' && echo "$riga" | grep -q '"esito":"hardware"' || rosso=1
		[ -n "$nv" ] && [ "$nv" != renderD128 ] && prova "$cod-$nv" "$BIN" --prova-codifica "$cod" --nodo "/dev/dri/$nv"
		[ -n "$nv" ] && prova "$cod-vulkan-$nv" "$BIN" --prova-codifica "$cod" --nodo "/dev/dri/$nv" --codifica vulkan
		prova "$cod-come-$UTENTE_BANCO" runuser -u "$UTENTE_BANCO" -- "$BIN" --prova-codifica "$cod"
	done
	if [ $rosso = 0 ]; then
		ok "H.264 and HEVC on the card, route vulkan"
		esito codifica VERDE "h264 and hevc: route vulkan"
	else
		ko "the route is not \"vulkan\" for H.264 and HEVC (see prova-codifica.txt)"
		esito codifica ROSSO "see prova-codifica.txt"
	fi
	return $rosso
}

# ═══════════════════════════════════════════════════════════════════════════
#  (d) THE 19-CONFRONTO BENCH ON THE NVIDIA
# ═══════════════════════════════════════════════════════════════════════════
confronto() {
	log "(d) banchi/19-vulkan/19-confronto.sh on the NVIDIA"
	local nv u="$LAVORO/confronto"
	nv=$(nodo_nvidia || true)
	[ -n "$nv" ] || { ko "no NVIDIA node"; esito confronto ROSSO "no node"; return 1; }
	mkdir -p "$u"
	# ⭐ no "vaapi" among the engines: on the NVIDIA VA-API does not encode (nvidia-vaapi-driver only decodes)
	ALBERO=$ALBERO USCITA=$u NODO_RADEON=${nv#renderD} MOTORI="vulkan scheda" ORDINE_PRODOTTO=1 \
		bash "$ALBERO/banchi/19-vulkan/19-confronto.sh" tutto > "$EVID/confronto.txt" 2>&1
	local c=$?
	cp -f "$u/esiti.jsonl" "$u/tabella.txt" "$u"/capacita-*.json "$EVID/" 2>/dev/null
	local tot buone
	tot=$(grep -c . "$u/esiti.jsonl" 2>/dev/null || echo 0)
	# good = code 0, EVERY frame decoded by ffmpeg (the bench's FOTOGRAMMI, 120), no error
	buone=$(python3 - "$u/esiti.jsonl" "${FOTOGRAMMI:-120}" <<'EOF' 2>/dev/null
import json, sys
n = 0
for r in open(sys.argv[1]):
    try:
        e = json.loads(r)
    except ValueError:
        continue
    if e.get("codice") == 0 and str(e.get("decodificati")) == sys.argv[2] and not e.get("errori_decodifica"):
        n += 1
print(n)
EOF
)
	if [ "$c" = 0 ] && [ "$tot" -gt 0 ] && [ "${buone:-0}" = "$tot" ]; then
		ok "19-confronto: $buone tests out of $tot with code 0 and every frame decoded"
		esito confronto VERDE "$buone/$tot"
		return 0
	fi
	ko "19-confronto: exit $c, $buone good tests out of $tot (confronto.txt, esiti.jsonl)"
	esito confronto ROSSO "$buone/$tot, exit $c"
	return 1
}

# ═══════════════════════════════════════════════════════════════════════════
#  (e) THE SUITE: XFCE under labwc (the product starts it), the browsers in a labwc of their own
# ═══════════════════════════════════════════════════════════════════════════
suite() {
	log "(e) the phase 15 suite, subset, on XFCE"
	local nv u uid sock="" modo=finestra
	nv=$(nodo_nvidia || true)
	u="$LAVORO/suite"
	mkdir -p "$u"
	chown "$UTENTE_BANCO:" "$u" 2>/dev/null
	if [ "$nv" != renderD128 ]; then
		ko "the server encodes on renderD128 and the NVIDIA is \"${nv:-none}\": the suite here would say nothing about the NVIDIA"
		esito suite NON-GUARDATA "the NVIDIA is not renderD128"
		return 3
	fi
	ss -ltn | grep -q ":$PORTA " || { ko "the server is not listening on $PORTA"; esito suite NON-GUARDATA "server off"; return 3; }
	uid=$(id -u "$UTENTE_BANCO")
	# THE BROWSERS' compositor, like banchi/15-suite/15-compositori.sh: headless labwc at
	# 3840x2160. ⚠ It draws in software (pixman): it is the client, and must not depend on the card
	# under test. The XFCE session instead is started by the PRODUCT, on the card
	# ⭐ 6 Oct 2026: the scenes the tests open INSIDE the session (F-021: `accendi_scena`)
	#    are looked for in /opt/remotix, where they live on the boxes. If the folder was not there, it is
	#    ours: `pulisci` removes it
	if [ ! -d /opt/remotix ]; then mkdir -p /opt/remotix && touch "$LAVORO/opt-remotix-nostra"; fi
	cp "$ALBERO"/banchi/11-scatole/11-c*-scena.html /opt/remotix/ 2>/dev/null
	chmod 755 /opt/remotix; chmod 644 /opt/remotix/*.html 2>/dev/null
	pkill -u "$UTENTE_BANCO" -x labwc 2>/dev/null
	# ⛔ 5 Oct 2026: `pkill` does not wait. If the previous labwc is still alive, its
	#    "wayland-0" ends up in the "prima" list, the new one is reborn with the SAME name and
	#    below nothing new is seen ⇒ HEADLESS browsers (784x512) for a whole run
	local j
	for j in $(seq 1 40); do pgrep -u "$UTENTE_BANCO" -x labwc > /dev/null || break; sleep 0.25; done
	local prima
	prima=$(ls "/run/user/$uid" 2>/dev/null | grep -E '^wayland-[0-9]+$' | sort)
	# ⭐ CLIENTE_SCHEDA=1 (5 Oct 2026): the browsers' compositor on the card (gles2) instead
	#    of in software — ONLY for the counter-test "is the red the software client's?". The
	#    run declares it, and such a run does NOT count as the NVIDIA suite
	local rend=pixman
	[ "${CLIENTE_SCHEDA:-0}" = 1 ] && rend=gles2
	runuser -u "$UTENTE_BANCO" -- env -u WAYLAND_DISPLAY -u DISPLAY XDG_RUNTIME_DIR="/run/user/$uid" \
		WLR_BACKENDS=headless WLR_RENDERER=$rend WLR_LIBINPUT_NO_DEVICES=1 \
		setsid labwc < /dev/null > "$u/compositore-browser.log" 2>&1 &
	local i
	for i in $(seq 1 40); do
		sock=$(comm -13 <(echo "$prima") <(ls "/run/user/$uid" 2>/dev/null | grep -E '^wayland-[0-9]+$' | sort) | head -1)
		[ -n "$sock" ] && break
		sleep 0.25
	done
	if [ -n "$sock" ]; then
		sleep 0.5
		local usc
		usc=$(runuser -u "$UTENTE_BANCO" -- env XDG_RUNTIME_DIR="/run/user/$uid" WAYLAND_DISPLAY="$sock" wlr-randr 2>/dev/null | awk 'NR==1{print $1}')
		runuser -u "$UTENTE_BANCO" -- env XDG_RUNTIME_DIR="/run/user/$uid" WAYLAND_DISPLAY="$sock" \
			wlr-randr --output "$usc" --custom-mode 3840x2160 >> "$u/compositore-browser.log" 2>&1
		ok "the browsers' compositor: $sock ($usc 3840x2160, $rend)"
		[ "$rend" = pixman ] || avviso "⛔ CLIENTE_SCHEDA=1: the browsers draw on the card — counter-test, NOT the NVIDIA suite"
	else
		modo=headless
		avviso "the browsers' labwc was not born (compositore-browser.log): the browsers go HEADLESS, and that is declared"
	fi
	local sistema
	sistema="$(. /etc/os-release; echo "$PRETTY_NAME") · $(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>/dev/null | head -1) · ${DESKTOP_NV:-xfce} · browser: $modo"
	runuser -u "$UTENTE_BANCO" -- env XDG_RUNTIME_DIR="/run/user/$uid" WAYLAND_DISPLAY="$sock" \
		PATH="$VALIGIA/bin:$PATH" RXNV_REGISTRO="$LAVORO/registro.log" RXNV_SISTEMA="$sistema" \
		RXNV_VERSIONE="$(head -1 "$VALIGIA/VERSIONE" 2>/dev/null)" \
		python3 "$QUI/19-nv-suite.py" --registro "$u/registro.jsonl" --evidenze "$u" \
		--porta "$PORTA" --modo "$modo" --desktop "${DESKTOP_NV:-xfce}" ${PROVE:+--prove "$PROVE"} ${BROWSER_SUITE:+--browser "$BROWSER_SUITE"} \
		> "$EVID/suite.txt" 2>&1
	local c=$?
	pkill -u "$UTENTE_BANCO" -x labwc 2>/dev/null
	python3 "$ALBERO/banchi/15-suite/15-rapporto.py" --registro "$u/registro.jsonl" --giro 19-nvidia --testo \
		> "$EVID/suite-rapporto.txt" 2>&1
	python3 "$ALBERO/banchi/15-suite/15-rapporto.py" --registro "$u/registro.jsonl" --giro 19-nvidia \
		--html "$EVID/suite-rapporto.html" > /dev/null 2>&1
	# which route the real sessions took, and whether labwc went on the card or on pixman
	grep -a -E 'route (vulkan|vaapi)|pixman|CANNOT ENCODE|DEVICE_LOST|Xid' "$LAVORO/registro.log" | sort | uniq -c | sort -rn | head -30 \
		> "$EVID/suite-strade.txt"
	tail -n 3 "$EVID/suite.txt" | sed 's/^/      /'
	case $c in
	0) ok "suite GREEN"; esito suite VERDE "$(tail -n 1 "$EVID/suite.txt")" ;;
	3) avviso "suite with tests not looked at"; esito suite NON-GUARDATA "$(tail -n 1 "$EVID/suite.txt")" ;;
	*) ko "suite RED"; esito suite ROSSO "$(tail -n 1 "$EVID/suite.txt")" ;;
	esac
	return $c
}

# ═══════════════════════════════════════════════════════════════════════════
#  (f) COLLECT
# ═══════════════════════════════════════════════════════════════════════════
raccogli() {
	log "(f) collecting logs and evidence"
	journalctl -b --no-pager > "$EVID/journal.txt" 2>&1
	journalctl -k -b --no-pager > "$EVID/nucleo.txt" 2>&1
	grep -i -E 'NVRM|Xid|nvidia' "$EVID/nucleo.txt" > "$EVID/nucleo-nvidia.txt" 2>/dev/null
	nvidia-smi -q > "$EVID/nvidia-smi-fine.txt" 2>&1
	cp -f "$LAVORO/registro.log" "$EVID/server-registro.log" 2>/dev/null
	cp -f "$VALIGIA/VERSIONE" "$EVID/" 2>/dev/null
	cp -f "$LAVORO/piano.json" "$EVID/" 2>/dev/null
	local nome
	nome="remotix-nv-$(hostname -s)-$(date +%Y%m%d-%H%M).tar.gz"
	# the streams and raw sources of bench 19 stay out: they are heavy, and the outcomes describe them
	tar -C "$LAVORO" -czf "$LAVORO/$nome" --exclude='*.bin' --exclude='*.bgrx' \
		evidenze confronto suite prima 2>/dev/null
	echo "$nome" > "$LAVORO/archivio"
	sha256sum "$LAVORO/$nome" | cut -d' ' -f1 > "$LAVORO/archivio.sha256"
	ok "archive: $LAVORO/$nome ($(du -h "$LAVORO/$nome" | cut -f1))"
	esito raccogli VERDE "$nome"
}

# ═══════════════════════════════════════════════════════════════════════════
#  (g) PULISCI: the machine as we found it
# ═══════════════════════════════════════════════════════════════════════════
pulisci() {
	log "(g) cleaning"
	if [ ! -f "$LAVORO/raccolto" ] && [ "${FORZA:-0}" != 1 ]; then
		ko "the archive does not appear to have been taken to the laptop ($LAVORO/raccolto): first \"19-nvidia.sh raccogli IP\" (or FORZA=1)"
		return 1
	fi
	[ -f "$PRIMA/fatta" ] || { ko "the snapshot of how the machine was is missing ($PRIMA): I do not know what to remove"; return 1; }
	local riavvio=0 u
	# 1. the bench's tests and processes
	systemctl stop remotix-nv-banco.service 2>/dev/null
	for u in $(getent passwd | cut -d: -f1 | grep -E "^($UTENTE_BANCO|c[0-9]+b?u[0-9]+)$"); do
		loginctl terminate-user "$u" 2>/dev/null
		pkill -KILL -u "$u" 2>/dev/null
	done
	[ -f "$LAVORO/opt-remotix-nostra" ] && rm -rf /opt/remotix
	# 2. REMOTIX: with the installer if it installed it, then our two files
	if [ -x /usr/bin/remotix-install ] || [ -x "$VALIGIA/bin/remotix-install" ]; then
		local ri=/usr/bin/remotix-install
		[ -x $ri ] || ri=$VALIGIA/bin/remotix-install
		if printf 'y\n' | $ri uninstall --purge > "$LAVORO/disinstalla.txt" 2>&1; then
			ok "REMOTIX uninstalled by the installer"
		else
			avviso "the installer did not uninstall (disinstalla.txt): removing with the package manager"
		fi
	fi
	systemctl disable --now remotix.service 2>/dev/null
	rm -f /etc/remotix/remotix.conf.d/remotix-nv.conf /etc/systemd/system/remotix.service.d/remotix-nv.conf
	rmdir /etc/systemd/system/remotix.service.d 2>/dev/null
	systemctl daemon-reload
	# 3. the bench users (the other new users, created by the packages, are DECLARED)
	for u in $(getent passwd | cut -d: -f1 | grep -E "^($UTENTE_BANCO|c[0-9]+b?u[0-9]+)$"); do
		loginctl disable-linger "$u" 2>/dev/null
		userdel -r "$u" > /dev/null 2>&1 || userdel "$u" 2>/dev/null
		rm -rf "/home/${u:?}"
	done
	rm -f /etc/sudoers.d/remotix-nv
	# 3-ter. Firefox: the policy and the aligned name (before the packages: they are in its folder)
	rm -f /usr/lib/firefox-esr/distribution/policies.json
	if [ -f "$LAVORO/firefox-esr-nome" ]; then
		rm -f /usr/lib/firefox-esr/firefox-esr
		ln -sfn ../lib/firefox-esr/firefox /usr/bin/firefox-esr
	fi
	# 3-bis. the spare memory, if we had added it
	if [ -f "$SCORTA" ]; then swapoff "$SCORTA" 2>/dev/null; rm -f "$SCORTA"; ok "swap removed"; fi
	# 4. modeset, if we had set it
	if [ -f /etc/modprobe.d/remotix-nv.conf ]; then
		rm -f /etc/modprobe.d/remotix-nv.conf
		command -v update-initramfs >/dev/null && update-initramfs -u > /dev/null 2>&1
		riavvio=1
	fi
	# 5. the NEW packages (those not in the snapshot), driver included if we installed it
	local nuovi
	nuovi=$(comm -13 "$PRIMA/pacchetti.txt" <(installati))
	if [ -n "$nuovi" ]; then
		echo "$nuovi" > "$LAVORO/pacchetti-tolti.txt"
		echo "$nuovi" | grep -q -E '^(nvidia-driver|nvidia-kernel|nvidia-dkms|linux-headers|linux-modules-nvidia)' && riavvio=1
		# ⛔ FIRST the simulation: if apt, to remove the new ones, would also remove EVEN ONE package
		#    that was there, nothing is removed and that is said (`[M]` 1 Oct 2026, test in the container:
		#    a blind purge stopped half-way on "sudo" and left dpkg pending)
		local tolti fuori
		# shellcheck disable=SC2086
		tolti=$(SUDO_FORCE_REMOVE=yes apt-get -s purge $nuovi 2>/dev/null | awk '/^Purg /{print $2}' | sed 's/:.*//' | sort -u)
		fuori=$(comm -12 "$PRIMA/pacchetti.txt" <(echo "$tolti"))
		if [ -n "$fuori" ]; then
			avviso "apt would also remove packages that were there: $(echo "$fuori" | tr '\n' ' ') ⇒ removing nothing with the package manager"
		else
			# shellcheck disable=SC2086
			SUDO_FORCE_REMOVE=yes "${APT[@]}" purge $nuovi > "$LAVORO/purge.txt" 2>&1 \
				&& ok "removed $(echo "$nuovi" | wc -l) new packages" \
				|| avviso "apt-get purge with errors (purge.txt)"
		fi
		dpkg --configure -a > /dev/null 2>&1
	fi
	# 6. /etc/apt as it was (Google and Mozilla repositories, non-free, universe)
	rm -rf /etc/apt
	tar -C / -xpf "$PRIMA/etc-apt.tar"
	"${APT[@]}" update > /dev/null 2>&1
	ok "/etc/apt as it was"
	if [ ! -f "$PRIMA/etc-remotix" ]; then rm -rf /etc/remotix /var/lib/remotix; fi
	# 7. what is still different, said
	local dopo_p dopo_u
	dopo_p=$(comm -3 "$PRIMA/pacchetti.txt" <(installati) | tr -d '\t' | tr '\n' ' ')
	dopo_u=$(comm -13 "$PRIMA/utenti.txt" <(getent passwd | cut -d: -f1 | sort) | tr '\n' ' ')
	{
		echo "packages different from before: ${dopo_p:-none}"
		echo "extra users (from the packages): ${dopo_u:-none}"
		echo "reboot recommended: $([ $riavvio = 1 ] && echo yes || echo no)"
	} | tee "$LAVORO/pulito.txt" | sed 's/^/    /'
	[ $riavvio = 1 ] && avviso "REBOOT RECOMMENDED: driver or modeset removed"
	ok "clean (the suitcase $VALIGIA and $LAVORO are removed by the laptop, once the script ends)"
	return 0
}

stato() {
	log "where we are"
	local p
	for p in aggiorna controlli driver dipendenze remotix codifica confronto suite raccogli; do
		if [ -f "$FATTO/$p" ]; then printf '    %-11s done   %s\n' "$p" "$(cat "$FATTO/$p")"; else printf '    %-11s —\n' "$p"; fi
	done
	[ -f "$EVID/passi.txt" ] && { echo; sed 's/^/    /' "$EVID/passi.txt"; }
}

# a step, remembering that it was done (with the exit code): "tutto" does not redo it
passo() {
	local p=$1 c
	"$p"; c=$?
	[ $c != 10 ] && echo "exit $c · $(date -Is)" > "$FATTO/$p"
	return $c
}

tutto() {
	local p c peggio=0
	# after the reboot asked for by the "driver" step the checks and the driver are redone: the verdict
	# of (a) must be on the real driver, the one loaded now
	if [ -f "$LAVORO/riavvio-chiesto" ]; then
		rm -f "$LAVORO/riavvio-chiesto" "$FATTO/controlli" "$FATTO/driver"
		log "after the reboot: redoing checks and driver"
	fi
	for p in aggiorna controlli driver dipendenze remotix codifica confronto suite raccogli; do
		case " ${RIFAI:-} " in *" $p "*) rm -f "$FATTO/$p" ;; esac
		if [ -f "$FATTO/$p" ] && [ "$p" != raccogli ]; then
			log "$p: already done ($(cat "$FATTO/$p")), skipping"
			continue
		fi
		passo "$p"; c=$?
		case $c in
		10) log "A REBOOT IS NEEDED: then \"tutto\" is run again"; return 10 ;;
		0) ;;
		*)
			[ $c -gt $peggio ] && peggio=$c
			if [ "$p" = controlli ] && [ "${FORZA:-0}" != 1 ]; then
				log "checks RED: stopping (FORZA=1 to go on anyway)"
				raccogli
				return 1
			fi
			if [ "$p" = dipendenze ] || [ "$p" = remotix ]; then
				log "$p failed: without it, the later steps make no sense"
				raccogli
				return 1
			fi
			;;
		esac
	done
	log "END"
	sed 's/^/    /' "$EVID/passi.txt"
	return $peggio
}

AZIONE=${1:-stato}
case "$AZIONE" in
aggiorna|controlli|driver|dipendenze|remotix|codifica|confronto|suite)
	passo "$AZIONE"; c=$? ;;
raccogli|pulisci|stato) "$AZIONE"; c=$? ;;
tutto) tutto; c=$? ;;
*) echo "usage: $0 aggiorna|controlli|driver|dipendenze|remotix|codifica|confronto|suite|raccogli|pulisci|stato|tutto"; exit 2 ;;
esac
echo "$c" > "$LAVORO/uscita"
exit "$c"
