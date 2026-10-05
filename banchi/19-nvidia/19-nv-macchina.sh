#!/bin/bash
# 19-nv-macchina.sh — il banco NVIDIA, SULLA MACCHINA A NOLEGGIO, da root.
#
#   bash /opt/remotix-nv/albero/banchi/19-nvidia/19-nv-macchina.sh PASSO
#
# Di solito non lo lancia una persona: lo lancia `19-nvidia.sh` dal portatile
# (`tutto IP`), in un'unita' di systemd che sopravvive alla caduta di ssh.
#
# I PASSI, nell'ordine di `tutto` (fasi/19-nvidia.md §2.4, compito del 1 ott 2026):
#   aggiorna     una Ubuntu PIU' VECCHIA della 26.04 la porta alla 26.04 con do-release-upgrade,
#                    un salto e un riavvio alla volta (20.04 ⇒ 22.04 ⇒ 24.04 ⇒ 26.04): i noleggiatori
#                    offrono Ubuntu, e non sempre la 26.04 (5 ott 2026). ⛔ «pulisci» NON lo disfa
#   controlli    (a) scheda, driver, nodi DRM, ICD, vulkaninfo con
#                    VK_KHR_video_encode_h264/h265; e la FOTOGRAFIA della macchina
#                    com'era (pacchetti, /etc/apt, utenti, unita'): serve a «pulisci»
#   driver       il driver NVIDIA col suo ICD Vulkan e nvidia-drm modeset=1, SOLO
#                    se mancano; se tocca il nucleo esce con 10 = riavvio
#   dipendenze   (b) XFCE sotto labwc, gli attrezzi delle prove, Firefox ESR, Chrome,
#                    l'utente del banco `rxbanco`
#   remotix      (b) REMOTIX dal .deb di `fase-19` CON L'INSTALLATORE (piano, applica):
#                    il rifiuto, se c'e', e' gia' un risultato
#   codifica     (c) `remotix --prova-codifica` h264 e hevc: deve dire strada «vulkan»
#   confronto    (d) `banchi/19-vulkan/19-confronto.sh` sulla NVIDIA (qualita',
#                    decodifica di ogni fotogramma, tela nuova, tela in CICLO, chiave, tetto)
#   suite        (e) il sottoinsieme della suite della fase 15 (F-001 F-002 F-003 F-011
#                    F-013 F-016 F-018) su XFCE sotto labwc senza schermo, Firefox e Chrome
#   raccogli     (f) registri ed evidenze in UN archivio, da portare sul portatile
#   pulisci      (g) la macchina come l'abbiamo trovata (vuole l'archivio gia' portato via)
#   stato        dove si e' arrivati
#   tutto        dal primo all'ultimo prima di «pulisci», saltando quelli gia' fatti
#
# Uscita: 0 verde · 1 rosso · 3 non ho potuto guardare · 10 serve un riavvio
# (poi si rilancia `tutto`, e riparte dal passo dopo).
# Variabili: PORTA (7447), FORZA=1 (va avanti anche dopo un controllo rosso),
# RIFAI="passo passo" (rifa' passi gia' fatti), LAVORO (/var/lib/remotix-nv).
#
# ⛔ Le prestazioni NON si giudicano qui: i tempi che i banchi scrivono restano
#    nelle evidenze, il giudizio e' del comportamento (decodifica, strada, prove).
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
# una riga per passo in passi.txt: il riassunto che il portatile mostra alla fine
esito()  { printf '%s\t%s\t%s\t%s\n' "$(date -Is)" "$1" "$2" "$3" >> "$EVID/passi.txt"; }

distro() { . /etc/os-release; echo "${ID:-?} ${VERSION_ID:-?}"; }
famiglia() {
	case "$(distro)" in
	"debian 13") echo debian ;;
	"ubuntu 26.04") echo ubuntu ;;
	*) echo altra ;;
	esac
}

# il nodo DRM di rendering della NVIDIA (renderD128…), "" se non c'e'
nodo_nvidia() {
	local n d
	for n in /dev/dri/renderD*; do
		[ -e "$n" ] || continue
		d=$(basename "$(readlink -f "/sys/class/drm/$(basename "$n")/device/driver")" 2>/dev/null)
		[ "$d" = nvidia ] && { basename "$n"; return 0; }
	done
	return 1
}

# il file ICD della NVIDIA (nvidia_icd.json, nvidia_icd.x86_64.json…), "" se non c'e'
icd_nvidia() {
	local f
	for f in /usr/share/vulkan/icd.d/nvidia_icd*.json /etc/vulkan/icd.d/nvidia_icd*.json; do
		[ -e "$f" ] && { echo "$f"; return 0; }
	done
	return 1
}

# i pacchetti dell'elenco che il deposito ha davvero
# un pacchetto VERO col suo candidato: «apt-cache show» dice si' anche a un nome solo citato
# (`[M]` 1 ott 2026, Ubuntu 26.04: firefox-esr e' «Candidate: (none)» e show esce con 0)
candidato() { apt-cache policy "$1" 2>/dev/null | awk '/Candidate:/{print $2}' | grep -q -v -e "(none)" -e "^$"; }
disponibili() { local p; for p; do candidato "$p" && echo "$p"; done; }

# installati: «ii», ma anche «it»/«iU» (installato, coi trigger o la configurazione in sospeso)
installati() { dpkg-query -W -f='${db:Status-Abbrev} ${Package}\n' 2>/dev/null | awk '$1 ~ /^i/{print $2}' | sort -u; }

# ═══════════════════════════════════════════════════════════════════════════
#  LA FOTOGRAFIA DELLA MACCHINA COM'ERA (una volta sola: e' il «prima» di pulisci)
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
	ok "fotografata la macchina com'era: $(wc -l < "$PRIMA/pacchetti.txt") pacchetti, $(wc -l < "$PRIMA/utenti.txt") utenti"
}

# ═══════════════════════════════════════════════════════════════════════════
#  (a) I CONTROLLI
# ═══════════════════════════════════════════════════════════════════════════
# Ubuntu vecchia ⇒ un salto di versione e un riavvio (uscita 10); la 26.04 o Debian 13 ⇒ niente.
# ⛔ Irreversibile: la macchina si restituisce aggiornata, e «pulisci» lo dichiara.
aggiorna() {
	log "(0) la versione del sistema"
	. /etc/os-release
	if [ "${ID:-}" != ubuntu ] || [ "$(famiglia)" != altra ]; then
		ok "$(distro): niente da aggiornare"
		return 0
	fi
	local da=$VERSION_ID f="$EVID/aggiorna-$VERSION_ID.txt"
	case "$da" in 20.04|22.04|24.04) ;; *) ko "ubuntu $da: so salire solo da 20.04, 22.04 e 24.04"; esito aggiorna ROSSO "ubuntu $da"; return 1 ;; esac
	[ "$(id -u)" = 0 ] || { ko "serve root"; return 1; }
	# do-release-upgrade si rifiuta se il sistema non e' aggiornato o aspetta un riavvio
	log "ubuntu $da: prima aggiorno i pacchetti della $da"
	{ "${APT[@]}" update && "${APT[@]}" dist-upgrade && "${APT[@]}" install ubuntu-release-upgrader-core; } > "$f" 2>&1 \
		|| { ko "aggiornamento della $da non riuscito ($f)"; esito aggiorna ROSSO "dist-upgrade $da"; return 1; }
	if [ -f /var/run/reboot-required ]; then
		touch "$LAVORO/riavvio-chiesto"
		log "la $da aggiornata chiede un riavvio prima del salto"
		return 10
	fi
	sed -i -E 's/^Prompt=.*/Prompt=lts/' /etc/update-manager/release-upgrades 2>/dev/null
	log "ubuntu $da: salto alla versione LTS dopo (mezz'ora o piu')"
	# -f DistUpgradeViewNonInteractive: nessuna domanda, i file di configurazione cambiati si tengono
	if ! do-release-upgrade -f DistUpgradeViewNonInteractive >> "$f" 2>&1; then
		# prima della .1 il salto fra LTS non e' ancora offerto: -d lo forza
		if grep -q -i "no new release" "$f"; then
			avviso "il salto non e' ancora offerto: lo forzo con -d"
			do-release-upgrade -d -f DistUpgradeViewNonInteractive >> "$f" 2>&1 \
				|| { ko "do-release-upgrade -d non riuscito ($f)"; esito aggiorna ROSSO "salto da $da"; return 1; }
		else
			ko "do-release-upgrade non riuscito ($f)"; esito aggiorna ROSSO "salto da $da"; return 1
		fi
	fi
	esito aggiorna RIAVVIO "ubuntu $da ⇒ $(. /etc/os-release; echo "$VERSION_ID")"
	touch "$LAVORO/riavvio-chiesto"
	return 10
}

controlli() {
	log "(a) i controlli iniziali"
	local f="$EVID/controlli.txt" rosso=0 manca_driver=0
	: > "$f"
	scrivi() { printf '%s: %s\n' "$1" "$2" >> "$f"; }
	[ "$(id -u)" = 0 ] || { ko "serve root"; return 1; }
	scrivi distribuzione "$(. /etc/os-release; echo "$PRETTY_NAME")"
	scrivi nucleo "$(uname -r)"
	scrivi processore "$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2- | sed 's/^ //') ($(nproc) fili)"
	scrivi memoria "$(awk '/MemTotal/{printf "%.0f GiB", $2/1048576}' /proc/meminfo)"
	if [ "$(famiglia)" = altra ]; then
		ko "distribuzione $(distro): REMOTIX vuole Debian 13 o Ubuntu 26.04 (OpenSSL 3.5, labwc, libei)"
		scrivi verdetto.distribuzione ROSSO; rosso=1
	else
		ok "distribuzione $(distro)"
		scrivi verdetto.distribuzione VERDE
	fi
	fotografa_prima
	# gli attrezzi del controllo: pochi, e se li mettiamo noi li toglie «pulisci»
	if ! command -v vulkaninfo >/dev/null || ! command -v lspci >/dev/null; then
		"${APT[@]}" update >/dev/null 2>&1
		"${APT[@]}" install --no-install-recommends vulkan-tools pciutils >/dev/null 2>&1 \
			&& ok "vulkan-tools e pciutils installati per guardare" || avviso "vulkan-tools/pciutils non installati"
	fi
	# la scheda, dal bus: c'e' anche senza driver
	local pci
	pci=$(lspci -nn 2>/dev/null | grep -i -E 'vga|3d|display' | grep -i '10de' || true)
	if [ -z "$pci" ]; then
		ko "nessuna scheda NVIDIA sul bus PCI"
		scrivi verdetto.scheda ROSSO; rosso=1
	else
		ok "scheda: $pci"
		scrivi scheda "$pci"
	fi
	lspci -nnk > "$EVID/lspci.txt" 2>&1
	# il driver
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
			ko "driver NVIDIA $ver: serve 550 o piu' (Vulkan Video encode)"
			scrivi verdetto.driver ROSSO; rosso=1
		fi
		# ⛔ le schede da calcolo senza NVENC (A100, H100…): Vulkan Video encode non c'e'
		if echo "$nome" | grep -q -E '(^|[ -])(A100|A800|A30|H100|H200|H800|B100|B200|GH200)([ -]|$)'; then
			ko "$nome non ha il codificatore video (NVENC): qui REMOTIX non puo' codificare"
			scrivi verdetto.nvenc ROSSO; rosso=1
		fi
		grep -i -A3 'Encoder Stats' "$EVID/nvidia-smi.txt" > /dev/null 2>&1 && scrivi nvenc "statistiche dell'encoder presenti in nvidia-smi -q"
	else
		avviso "nvidia-smi non risponde: il driver non c'e' (o non e' caricato) ⇒ lo mette il passo «driver»"
		scrivi driver.versione nessuno; manca_driver=1
	fi
	# i moduli e modeset
	local ms
	ms=$(cat /sys/module/nvidia_drm/parameters/modeset 2>/dev/null || echo "?")
	scrivi nvidia_drm.modeset "$ms"
	grep -E '^nvidia' /proc/modules > "$EVID/moduli.txt" 2>&1
	[ "$ms" = Y ] && ok "nvidia-drm modeset=Y" || avviso "nvidia-drm modeset=$ms ⇒ il passo «driver» lo mette a 1 (serve a GBM, cioe' a labwc sulla scheda)"
	# i nodi DRM
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
			ok "la NVIDIA e' renderD128 (il nodo su cui codifica il server)"
		else
			avviso "la NVIDIA e' $nv, non renderD128: il SERVER codifica su renderD128 ($riga) ⇒ la suite (e) non e' valida e si salta; (c) e (d) si fanno sul nodo giusto"
			scrivi verdetto.nodo GIALLO
		fi
	elif [ $manca_driver = 0 ]; then
		ko "il driver c'e' ma nessun renderD* e' della NVIDIA (nvidia-drm non caricato?)"
		scrivi verdetto.nodo ROSSO; rosso=1
	fi
	# l'ICD e vulkaninfo
	local icd
	icd=$(icd_nvidia || true)
	scrivi icd "${icd:-nessuno}"
	ls -l /usr/share/vulkan/icd.d /etc/vulkan/icd.d > "$EVID/icd.txt" 2>&1
	if [ -z "$icd" ]; then
		avviso "nessun ICD Vulkan della NVIDIA ⇒ lo mette il passo «driver» (e l'installatore, senza, direbbe RX-GPU-004)"
	elif command -v vulkaninfo >/dev/null; then
		VK_DRIVER_FILES=$icd VK_ICD_FILENAMES=$icd vulkaninfo > "$EVID/vulkaninfo.txt" 2>&1
		VK_DRIVER_FILES=$icd VK_ICD_FILENAMES=$icd vulkaninfo --summary > "$EVID/vulkaninfo-riassunto.txt" 2>&1
		local e mancano=""
		for e in VK_KHR_video_queue VK_KHR_video_encode_queue VK_KHR_video_encode_h264 VK_KHR_video_encode_h265 \
			VK_EXT_external_memory_dma_buf VK_EXT_image_drm_format_modifier VK_EXT_physical_device_drm; do
			if grep -q "$e" "$EVID/vulkaninfo.txt"; then scrivi "vulkan.$e" si; else scrivi "vulkan.$e" NO; mancano="$mancano $e"; fi
		done
		if [ -z "$mancano" ]; then
			ok "vulkaninfo: codifica H.264 e H.265, dmabuf, modificatori, nodo DRM"
		else
			ko "vulkaninfo: mancano$mancano"
			case "$mancano" in *encode*) scrivi verdetto.vulkan ROSSO; rosso=1 ;; esac
		fi
	fi
	if [ $rosso = 0 ]; then scrivi verdetto VERDE; ok "controlli VERDI"; esito controlli VERDE "$nome $ver $nv"
	else scrivi verdetto ROSSO; ko "controlli ROSSI (vedi $f)"; esito controlli ROSSO "vedi controlli.txt"; fi
	return $rosso
}

# ═══════════════════════════════════════════════════════════════════════════
#  IL DRIVER (solo se manca qualcosa; il nucleo ⇒ riavvio)
# ═══════════════════════════════════════════════════════════════════════════
driver() {
	log "il driver NVIDIA, il suo ICD Vulkan, modeset"
	local riavvio=0 fam
	fam=$(famiglia)
	"${APT[@]}" update >/dev/null 2>&1
	if ! nvidia-smi >/dev/null 2>&1; then
		avviso "il driver manca: lo installo dalla distribuzione"
		if [ "$fam" = debian ]; then
			# non-free e non-free-firmware (la fotografia di /etc/apt e' in prima/)
			sed -i -E '/^Components:/{/non-free( |$)/!s/$/ contrib non-free non-free-firmware/}' /etc/apt/sources.list.d/*.sources 2>/dev/null
			[ -f /etc/apt/sources.list ] && sed -i -E '/^deb /{/non-free( |$)/!s/$/ contrib non-free non-free-firmware/}' /etc/apt/sources.list
			"${APT[@]}" update >/dev/null 2>&1
			"${APT[@]}" install "linux-headers-$(uname -r)" nvidia-driver nvidia-vulkan-icd firmware-misc-nonfree \
				$(disponibili libnvidia-egl-gbm1 libnvidia-egl-wayland1) > "$EVID/driver-installa.txt" 2>&1 \
				|| { ko "installazione del driver fallita (driver-installa.txt)"; esito driver ROSSO "installazione fallita"; return 1; }
		else
			"${APT[@]}" install ubuntu-drivers-common > "$EVID/driver-installa.txt" 2>&1
			ubuntu-drivers devices >> "$EVID/driver-installa.txt" 2>&1
			# ⛔ non «--gpgpu»: quello e' il driver senza grafica, SENZA libnvidia-gl (niente ICD Vulkan)
			ubuntu-drivers install >> "$EVID/driver-installa.txt" 2>&1 \
				|| { ko "ubuntu-drivers install fallito (driver-installa.txt)"; esito driver ROSSO "installazione fallita"; return 1; }
		fi
		ok "driver installato: serve un riavvio"
		riavvio=1
	fi
	if ! icd_nvidia >/dev/null; then
		local pk=""
		if [ "$fam" = debian ]; then
			pk=nvidia-vulkan-icd
		else
			local m srv=""
			m=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -1 | cut -d. -f1)
			[ -z "$m" ] && m=$(dpkg-query -W -f='${Package}\n' 'nvidia-driver-*' 'nvidia-headless-*' 2>/dev/null | grep -o -E '[0-9]{3}' | sort -n | tail -1)
			dpkg-query -W -f='${Package}\n' 2>/dev/null | grep -q -E "^nvidia-(headless|utils|driver)-$m-server$" && srv=-server
			pk="libnvidia-gl-$m$srv"
		fi
		avviso "l'ICD Vulkan della NVIDIA manca (driver «senza grafica»?): $pk"
		"${APT[@]}" install "$pk" >> "$EVID/driver-installa.txt" 2>&1 \
			&& ok "ICD: $(icd_nvidia || echo 'ANCORA NIENTE')" \
			|| { ko "$pk non si installa: il driver non e' quello della distribuzione? Rimedio a mano"; esito driver ROSSO "ICD mancante"; return 1; }
	fi
	local ms
	ms=$(cat /sys/module/nvidia_drm/parameters/modeset 2>/dev/null || echo "?")
	if [ "$ms" != Y ] && ! grep -q -s 'nvidia-drm modeset=1' /etc/modprobe.d/*.conf; then
		echo 'options nvidia-drm modeset=1' > /etc/modprobe.d/remotix-nv.conf
		command -v update-initramfs >/dev/null && update-initramfs -u >> "$EVID/driver-installa.txt" 2>&1
		ok "nvidia-drm modeset=1 in /etc/modprobe.d/remotix-nv.conf (lo toglie «pulisci»): serve un riavvio"
		riavvio=1
	fi
	if [ $riavvio = 1 ]; then
		esito driver RIAVVIO "driver/ICD/modeset cambiati"
		touch "$LAVORO/riavvio-chiesto"
		return 10
	fi
	ok "driver, ICD e modeset a posto: niente da fare"
	esito driver VERDE "$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"
	return 0
}

# ═══════════════════════════════════════════════════════════════════════════
#  (b) LE DIPENDENZE: il desktop leggero, gli attrezzi delle prove, i browser
# ═══════════════════════════════════════════════════════════════════════════
# La memoria di scorta (5 ott 2026: la macchina a noleggio puo' avere 8 GB, il banco ne chiedeva 16).
# Senza, a memoria finita il sistema uccide il browser a meta' prova, e il rosso sembrerebbe del
# prodotto.  Sotto i 12 GiB e senza scorta: un file da 4 GiB, che «pulisci» toglie.
SCORTA=/remotix-nv.scorta
scorta() {
	local kib
	kib=$(awk '/MemTotal/{print $2}' /proc/meminfo)
	if [ "$kib" -ge $((12 * 1048576)) ]; then ok "memoria $((kib / 1048576)) GiB: la scorta non serve"; return 0; fi
	if [ -n "$(swapon --noheadings 2>/dev/null)" ]; then ok "memoria $((kib / 1048576)) GiB, scorta gia' presente: $(swapon --noheadings --show=NAME,SIZE | tr '\n' ' ')"; return 0; fi
	if fallocate -l 4G "$SCORTA" 2>/dev/null || dd if=/dev/zero of="$SCORTA" bs=1M count=4096 status=none; then
		chmod 600 "$SCORTA"
		if mkswap "$SCORTA" > /dev/null 2>&1 && swapon "$SCORTA" 2>/dev/null; then
			ok "memoria $((kib / 1048576)) GiB ⇒ scorta di 4 GiB accesa ($SCORTA)"
			return 0
		fi
	fi
	rm -f "$SCORTA"
	avviso "memoria $((kib / 1048576)) GiB e la scorta non si accende: un rosso per memoria finita va letto nel registro del kernel (oom)"
}

dipendenze() {
	log "(b) le dipendenze: XFCE sotto labwc, attrezzi, Firefox ESR, Chrome"
	local fam
	fam=$(famiglia)
	if [ "$fam" = ubuntu ] && ! grep -q -s -E '^Components:.*universe' /etc/apt/sources.list.d/ubuntu.sources; then
		sed -i -E '/^Components:/{/universe/!s/$/ universe/}' /etc/apt/sources.list.d/ubuntu.sources
		ok "universe acceso (labwc, xfdesktop4, glslc stanno li')"
	fi
	"${APT[@]}" update > "$EVID/dipendenze.txt" 2>&1
	scorta
	# il desktop come nella scatola rete11-xfce (banchi/11-scatole/Contenitore.xfce), senza scatola
	local desktop=(labwc xfce4-session xfce4-panel xfdesktop4 xfce4-terminal thunar xwayland wlr-randr
		dbus-user-session libpam-systemd sudo fonts-dejavu-core pipewire pipewire-pulse wireplumber wl-clipboard)
	# gli attrezzi delle prove: ffmpeg/ffplay (F-013 e il banco 19 MISURANO con ffmpeg: non entra nel
	# prodotto), python3 con PIL e numpy (il giudice dei pixel), e quel che serve a compilare il banco 19
	local attrezzi=(ffmpeg python3 python3-numpy python3-pil curl ca-certificates gnupg vulkan-tools
		gcc libc6-dev pkg-config libva-dev libvulkan-dev libgbm-dev libdrm-dev glslc)
	# la scheda: il ponte GBM/EGL della NVIDIA, se il driver e' quello della distribuzione
	local nv=()
	[ "$fam" = debian ] && mapfile -t nv < <(disponibili libnvidia-egl-gbm1 libnvidia-egl-wayland1)
	if ! "${APT[@]}" install --no-install-recommends "${desktop[@]}" "${attrezzi[@]}" "${nv[@]}" >> "$EVID/dipendenze.txt" 2>&1; then
		ko "apt-get install fallito (dipendenze.txt)"; esito dipendenze ROSSO "apt fallito"; return 1
	fi
	ok "desktop e attrezzi"
	# Firefox ESR: Debian ce l'ha; su Ubuntu «firefox» e' uno snap ⇒ il deposito di Mozilla
	if [ "$fam" = ubuntu ] && ! candidato firefox-esr; then
		install -d -m 0755 /etc/apt/keyrings
		curl -fsSL https://packages.mozilla.org/apt/repo-signing-key.gpg -o /etc/apt/keyrings/packages.mozilla.org.asc
		echo "deb [signed-by=/etc/apt/keyrings/packages.mozilla.org.asc] https://packages.mozilla.org/apt mozilla main" \
			> /etc/apt/sources.list.d/mozilla.list
		"${APT[@]}" update >> "$EVID/dipendenze.txt" 2>&1
	fi
	"${APT[@]}" install --no-install-recommends firefox-esr libpci3 >> "$EVID/dipendenze.txt" 2>&1 \
		&& ok "Firefox ESR: $(firefox-esr --version 2>/dev/null)" \
		|| { ko "firefox-esr non si installa"; esito dipendenze ROSSO "firefox-esr"; return 1; }
	# ⭐ 5 ott 2026, `[M]` RTX 4090: Firefox ESR 153 (deposito di Mozilla) alla prima apertura mette
	#    la finestra «Welcome to Firefox / Terms of Use» SOPRA la pagina di prova, e F-003 non la
	#    trova.  Le scatole hanno la 140, che non la mostra.  ⇒ La si salta con una regola di
	#    Firefox (la toglie «pulisci» insieme al pacchetto: e' nella sua cartella).
	mkdir -p /usr/lib/firefox-esr/distribution
	printf '%s\n' '{"policies": {"SkipTermsOfUse": true, "DisableTelemetry": true, "DontCheckDefaultBrowser": true, "OverrideFirstRunPage": "", "OverridePostUpdatePage": ""}}' \
		> /usr/lib/firefox-esr/distribution/policies.json
	# ⭐ 5 ott 2026, `[M]`: il pacchetto di Mozilla fa girare Firefox come «firefox-bin», quello di
	#    Debian come «firefox-esr» — e le prove della suite (F-016/F-017) cercano e uccidono la scena
	#    per NOME (`pgrep -x firefox-esr`).  ⇒ Le prove restano IDENTICHE e si allinea il nome: un
	#    collegamento fisico col nome giusto, nella cartella di Firefox (la toglie «pulisci»).
	if [ -x /usr/lib/firefox-esr/firefox-bin ] && [ ! -e /usr/lib/firefox-esr/firefox-esr ]; then
		ln -f /usr/lib/firefox-esr/firefox-bin /usr/lib/firefox-esr/firefox-esr
		ln -sfn /usr/lib/firefox-esr/firefox-esr /usr/bin/firefox-esr
		touch "$LAVORO/firefox-esr-nome"
	fi
	# Chrome: il .deb di Google (si porta il suo deposito: lo toglie «pulisci» con /etc/apt)
	if ! command -v google-chrome >/dev/null; then
		curl -fsSL -o /var/tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
			&& "${APT[@]}" install /var/tmp/google-chrome.deb >> "$EVID/dipendenze.txt" 2>&1
		rm -f /var/tmp/google-chrome.deb
	fi
	command -v google-chrome >/dev/null && ok "Chrome: $(google-chrome --version 2>/dev/null)" \
		|| { ko "Chrome non si installa"; esito dipendenze ROSSO chrome; return 1; }
	# il «firefox» che i banchi lanciano (07-b46: `firefox --marionette`) e' il firefox-esr
	mkdir -p "$VALIGIA/bin"
	ln -sf "$(command -v firefox-esr)" "$VALIGIA/bin/firefox"
	# l'utente del banco: i browser NON girano da root; sudo senza parola per entrare «nella scatola»
	# (che qui e' la macchina stessa); linger per avere /run/user/<uid> e il suo labwc
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
		echo "ffmpeg: $(ffmpeg -version 2>/dev/null | head -1)"
		echo "mesa/vulkan loader: $(dpkg-query -W -f='${Version}' libvulkan1 2>/dev/null)"
	} > "$EVID/versioni.txt"
	esito dipendenze VERDE "$(tr '\n' ' ' < "$EVID/versioni.txt" | cut -c1-200)"
	return 0
}

# ═══════════════════════════════════════════════════════════════════════════
#  (b) REMOTIX, CON L'INSTALLATORE
# ═══════════════════════════════════════════════════════════════════════════
remotix() {
	log "(b) REMOTIX dal .deb, con l'installatore"
	local fam deb ri="$VALIGIA/bin/remotix-install" e=0
	fam=$(famiglia)
	case $fam in
	debian) deb=$(ls "$VALIGIA"/pacchetti/remotix_*deb13*_amd64.deb 2>/dev/null | head -1) ;;
	ubuntu) deb=$(ls "$VALIGIA"/pacchetti/remotix_*ubuntu26.04*_amd64.deb 2>/dev/null | head -1) ;;
	*) deb="" ;;
	esac
	[ -n "$deb" ] || { ko "nessun .deb per $(distro) in $VALIGIA/pacchetti"; esito remotix ROSSO "manca il .deb"; return 1; }
	ok "pacchetto: $(basename "$deb")"
	# il controllo preliminare dell'installatore (in sola lettura): RX-GPU-*, la strada vulkan, l'ICD
	"$ri" verifica --lingua it > "$EVID/installatore-verifica.txt" 2>&1
	"$ri" verifica --json > "$EVID/installatore-verifica.json" 2>&1
	grep -o -E 'RX-[A-Z0-9]+-[0-9]+' "$EVID/installatore-verifica.txt" | sort -u | tr '\n' ' ' > "$LAVORO/codici-verifica"
	ok "verifica: codici $(cat "$LAVORO/codici-verifica")"
	if "$ri" piano --installa --pacchetto "$deb" --porta "$PORTA" --utente "$UTENTE_BANCO" \
		--uscita "$LAVORO/piano.json" --lingua it > "$EVID/installatore-piano.txt" 2>&1 \
		&& "$ri" applica "$LAVORO/piano.json" --approva --lingua it > "$EVID/installatore-applica.txt" 2>&1; then
		ok "l'installatore ha installato REMOTIX"
		echo installatore > "$LAVORO/come-installato"
	else
		e=$?
		ko "l'installatore NON ha installato (uscita $e): $(tail -3 "$EVID/installatore-applica.txt" "$EVID/installatore-piano.txt" 2>/dev/null | tr '\n' ' ' | cut -c1-300)"
		avviso "⇒ il rifiuto e' un risultato (evidenze installatore-*); per andare avanti coi passi c-e il pacchetto si mette col gestore"
		"${APT[@]}" install "$deb" > "$EVID/remotix-apt.txt" 2>&1 \
			|| { ko "nemmeno apt lo installa (remotix-apt.txt)"; esito remotix ROSSO "non installato"; return 1; }
		usermod -aG video,render "$UTENTE_BANCO"
		echo apt > "$LAVORO/come-installato"
	fi
	# ⭐ il server del banco: stessa unita' del prodotto, con due cose dichiarate e reversibili:
	#   il nome nel certificato (si entra da 127.0.0.1) e il registro di dettaglio; e lo stderr in un
	#   FILE, come nelle scatole (/var/lib/rete11/registro.log): la suite lo legge riga per riga
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
		ok "il server ascolta su $PORTA"
	else
		ko "il server non ascolta su $PORTA dopo 60 s"; tail -20 "$LAVORO/registro.log" 2>/dev/null | sed 's/^/      /'
		esito remotix ROSSO "non ascolta"; return 1
	fi
	grep -a -E 'strada|QUESTO SERVER NON SA|ECCOMI|offerti|⛔' "$LAVORO/registro.log" | head -20 > "$EVID/server-avvio.txt"
	"$ri" certifica --lingua it > "$EVID/installatore-certifica.txt" 2>&1; local c=$?
	ok "certifica: uscita $c"
	esito remotix VERDE "$(cat "$LAVORO/come-installato") · verifica: $(cat "$LAVORO/codici-verifica") · certifica $c"
	return 0
}

# ═══════════════════════════════════════════════════════════════════════════
#  (c) LA PROVA DELLA CODIFICA
# ═══════════════════════════════════════════════════════════════════════════
codifica() {
	log "(c) remotix --prova-codifica"
	local nv f="$EVID/prova-codifica.txt" rosso=0 c riga
	nv=$(nodo_nvidia || true)
	[ -x "$BIN" ] || { ko "manca $BIN"; esito codifica ROSSO "binario assente"; return 1; }
	: > "$f"
	prova() {  # prova ETICHETTA ARGOMENTI…
		local et=$1; shift
		"$@" > "$LAVORO/prova.json" 2> "$EVID/prova-codifica-$et.registro"; c=$?
		riga=$(tail -1 "$LAVORO/prova.json")
		printf '%s\tcodice %s\t%s\n' "$et" "$c" "$riga" | tee -a "$f"
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
		ok "H.264 e HEVC sulla scheda, strada vulkan"
		esito codifica VERDE "h264 e hevc: strada vulkan"
	else
		ko "la strada non e' «vulkan» per H.264 e HEVC (vedi prova-codifica.txt)"
		esito codifica ROSSO "vedi prova-codifica.txt"
	fi
	return $rosso
}

# ═══════════════════════════════════════════════════════════════════════════
#  (d) IL BANCO 19-CONFRONTO SULLA NVIDIA
# ═══════════════════════════════════════════════════════════════════════════
confronto() {
	log "(d) banchi/19-vulkan/19-confronto.sh sulla NVIDIA"
	local nv u="$LAVORO/confronto"
	nv=$(nodo_nvidia || true)
	[ -n "$nv" ] || { ko "nessun nodo NVIDIA"; esito confronto ROSSO "niente nodo"; return 1; }
	mkdir -p "$u"
	# ⭐ niente «vaapi» fra i motori: sulla NVIDIA VA-API non codifica (nvidia-vaapi-driver solo decodifica)
	ALBERO=$ALBERO USCITA=$u NODO_RADEON=${nv#renderD} MOTORI="vulkan scheda" ORDINE_PRODOTTO=1 \
		bash "$ALBERO/banchi/19-vulkan/19-confronto.sh" tutto > "$EVID/confronto.txt" 2>&1
	local c=$?
	cp -f "$u/esiti.jsonl" "$u/tabella.txt" "$u"/capacita-*.json "$EVID/" 2>/dev/null
	local tot buone
	tot=$(grep -c . "$u/esiti.jsonl" 2>/dev/null || echo 0)
	# buona = codice 0, OGNI fotogramma decodificato da ffmpeg (FOTOGRAMMI del banco, 120), nessun errore
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
		ok "19-confronto: $buone prove su $tot col codice 0 e ogni fotogramma decodificato"
		esito confronto VERDE "$buone/$tot"
		return 0
	fi
	ko "19-confronto: uscita $c, $buone prove buone su $tot (confronto.txt, esiti.jsonl)"
	esito confronto ROSSO "$buone/$tot, uscita $c"
	return 1
}

# ═══════════════════════════════════════════════════════════════════════════
#  (e) LA SUITE: XFCE sotto labwc (lo accende il prodotto), i browser in un labwc loro
# ═══════════════════════════════════════════════════════════════════════════
suite() {
	log "(e) la suite della fase 15, sottoinsieme, su XFCE"
	local nv u uid sock="" modo=finestra
	nv=$(nodo_nvidia || true)
	u="$LAVORO/suite"
	mkdir -p "$u"
	chown "$UTENTE_BANCO:" "$u" 2>/dev/null
	if [ "$nv" != renderD128 ]; then
		ko "il server codifica su renderD128 e la NVIDIA e' «${nv:-nessuno}»: la suite qui non direbbe niente della NVIDIA"
		esito suite NON-GUARDATA "la NVIDIA non e' renderD128"
		return 3
	fi
	ss -ltn | grep -q ":$PORTA " || { ko "il server non ascolta su $PORTA"; esito suite NON-GUARDATA "server spento"; return 3; }
	uid=$(id -u "$UTENTE_BANCO")
	# il compositore DEI BROWSER, come banchi/15-suite/15-compositori.sh: labwc senza schermo a
	# 3840x2160. ⚠ Disegna in software (pixman): e' il cliente, e non deve dipendere dalla scheda
	# che si sta provando. La sessione di XFCE invece la accende il PRODOTTO, sulla scheda
	pkill -u "$UTENTE_BANCO" -x labwc 2>/dev/null
	local prima
	prima=$(ls "/run/user/$uid" 2>/dev/null | grep -E '^wayland-[0-9]+$' | sort)
	runuser -u "$UTENTE_BANCO" -- env -u WAYLAND_DISPLAY -u DISPLAY XDG_RUNTIME_DIR="/run/user/$uid" \
		WLR_BACKENDS=headless WLR_RENDERER=pixman WLR_LIBINPUT_NO_DEVICES=1 \
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
		ok "il compositore dei browser: $sock ($usc 3840x2160, pixman)"
	else
		modo=headless
		avviso "il labwc dei browser non e' nato (compositore-browser.log): i browser vanno HEADLESS, e lo si dichiara"
	fi
	local sistema
	sistema="$(. /etc/os-release; echo "$PRETTY_NAME") · $(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>/dev/null | head -1) · XFCE sotto labwc · browser: $modo"
	runuser -u "$UTENTE_BANCO" -- env XDG_RUNTIME_DIR="/run/user/$uid" WAYLAND_DISPLAY="$sock" \
		PATH="$VALIGIA/bin:$PATH" RXNV_REGISTRO="$LAVORO/registro.log" RXNV_SISTEMA="$sistema" \
		RXNV_VERSIONE="$(head -1 "$VALIGIA/VERSIONE" 2>/dev/null)" \
		python3 "$QUI/19-nv-suite.py" --registro "$u/registro.jsonl" --evidenze "$u" \
		--porta "$PORTA" --modo "$modo" > "$EVID/suite.txt" 2>&1
	local c=$?
	pkill -u "$UTENTE_BANCO" -x labwc 2>/dev/null
	python3 "$ALBERO/banchi/15-suite/15-rapporto.py" --registro "$u/registro.jsonl" --giro 19-nvidia --testo \
		> "$EVID/suite-rapporto.txt" 2>&1
	python3 "$ALBERO/banchi/15-suite/15-rapporto.py" --registro "$u/registro.jsonl" --giro 19-nvidia \
		--html "$EVID/suite-rapporto.html" > /dev/null 2>&1
	# quale strada hanno preso le sessioni vere, e se labwc e' andato sulla scheda o su pixman
	grep -a -E 'strada (vulkan|vaapi)|pixman|NON SA CODIFICARE|DEVICE_LOST|Xid' "$LAVORO/registro.log" | sort | uniq -c | sort -rn | head -30 \
		> "$EVID/suite-strade.txt"
	tail -3 "$EVID/suite.txt" | sed 's/^/      /'
	case $c in
	0) ok "suite VERDE"; esito suite VERDE "$(tail -1 "$EVID/suite.txt")" ;;
	3) avviso "suite con prove non guardate"; esito suite NON-GUARDATA "$(tail -1 "$EVID/suite.txt")" ;;
	*) ko "suite ROSSA"; esito suite ROSSO "$(tail -1 "$EVID/suite.txt")" ;;
	esac
	return $c
}

# ═══════════════════════════════════════════════════════════════════════════
#  (f) RACCOGLI
# ═══════════════════════════════════════════════════════════════════════════
raccogli() {
	log "(f) raccolgo registri ed evidenze"
	journalctl -b --no-pager > "$EVID/journal.txt" 2>&1
	journalctl -k -b --no-pager > "$EVID/nucleo.txt" 2>&1
	grep -i -E 'NVRM|Xid|nvidia' "$EVID/nucleo.txt" > "$EVID/nucleo-nvidia.txt" 2>/dev/null
	nvidia-smi -q > "$EVID/nvidia-smi-fine.txt" 2>&1
	cp -f "$LAVORO/registro.log" "$EVID/server-registro.log" 2>/dev/null
	cp -f "$VALIGIA/VERSIONE" "$EVID/" 2>/dev/null
	cp -f "$LAVORO/piano.json" "$EVID/" 2>/dev/null
	local nome
	nome="remotix-nv-$(hostname -s)-$(date +%Y%m%d-%H%M).tar.gz"
	# i flussi e le sorgenti grezze del banco 19 restano fuori: pesano, e gli esiti li descrivono
	tar -C "$LAVORO" -czf "$LAVORO/$nome" --exclude='*.bin' --exclude='*.bgrx' \
		evidenze confronto suite prima 2>/dev/null
	echo "$nome" > "$LAVORO/archivio"
	sha256sum "$LAVORO/$nome" | cut -d' ' -f1 > "$LAVORO/archivio.sha256"
	ok "archivio: $LAVORO/$nome ($(du -h "$LAVORO/$nome" | cut -f1))"
	esito raccogli VERDE "$nome"
}

# ═══════════════════════════════════════════════════════════════════════════
#  (g) PULISCI: la macchina come l'abbiamo trovata
# ═══════════════════════════════════════════════════════════════════════════
pulisci() {
	log "(g) pulisco"
	if [ ! -f "$LAVORO/raccolto" ] && [ "${FORZA:-0}" != 1 ]; then
		ko "l'archivio non risulta portato sul portatile ($LAVORO/raccolto): prima «19-nvidia.sh raccogli IP» (o FORZA=1)"
		return 1
	fi
	[ -f "$PRIMA/fatta" ] || { ko "manca la fotografia di com'era la macchina ($PRIMA): non so che cosa togliere"; return 1; }
	local riavvio=0 u
	# 1. le prove e i processi del banco
	systemctl stop remotix-nv-banco.service 2>/dev/null
	for u in $(getent passwd | cut -d: -f1 | grep -E "^($UTENTE_BANCO|c[0-9]+b?u[0-9]+)$"); do
		loginctl terminate-user "$u" 2>/dev/null
		pkill -KILL -u "$u" 2>/dev/null
	done
	# 2. REMOTIX: con l'installatore se l'ha messo lui, poi i nostri due file
	if [ -x /usr/bin/remotix-install ] || [ -x "$VALIGIA/bin/remotix-install" ]; then
		local ri=/usr/bin/remotix-install
		[ -x $ri ] || ri=$VALIGIA/bin/remotix-install
		if $ri disinstalla --purge --uscita "$LAVORO/disinstalla.json" --lingua it > "$LAVORO/disinstalla.txt" 2>&1 \
			&& $ri applica "$LAVORO/disinstalla.json" --approva --lingua it >> "$LAVORO/disinstalla.txt" 2>&1; then
			ok "REMOTIX disinstallato dall'installatore"
		else
			avviso "l'installatore non ha disinstallato (disinstalla.txt): tolgo col gestore"
		fi
	fi
	systemctl disable --now remotix.service 2>/dev/null
	rm -f /etc/remotix/remotix.conf.d/remotix-nv.conf /etc/systemd/system/remotix.service.d/remotix-nv.conf
	rmdir /etc/systemd/system/remotix.service.d 2>/dev/null
	systemctl daemon-reload
	# 3. gli utenti del banco (gli altri utenti nuovi, creati dai pacchetti, si DICHIARANO)
	for u in $(getent passwd | cut -d: -f1 | grep -E "^($UTENTE_BANCO|c[0-9]+b?u[0-9]+)$"); do
		loginctl disable-linger "$u" 2>/dev/null
		userdel -r "$u" > /dev/null 2>&1 || userdel "$u" 2>/dev/null
		rm -rf "/home/${u:?}"
	done
	rm -f /etc/sudoers.d/remotix-nv
	# 3-ter. Firefox: la regola e il nome allineato (prima dei pacchetti: sono nella sua cartella)
	rm -f /usr/lib/firefox-esr/distribution/policies.json
	if [ -f "$LAVORO/firefox-esr-nome" ]; then
		rm -f /usr/lib/firefox-esr/firefox-esr
		ln -sfn ../lib/firefox-esr/firefox /usr/bin/firefox-esr
	fi
	# 3-bis. la memoria di scorta, se l'avevamo messa noi
	if [ -f "$SCORTA" ]; then swapoff "$SCORTA" 2>/dev/null; rm -f "$SCORTA"; ok "scorta tolta"; fi
	# 4. modeset, se l'avevamo messo noi
	if [ -f /etc/modprobe.d/remotix-nv.conf ]; then
		rm -f /etc/modprobe.d/remotix-nv.conf
		command -v update-initramfs >/dev/null && update-initramfs -u > /dev/null 2>&1
		riavvio=1
	fi
	# 5. i pacchetti NUOVI (quelli che non c'erano nella fotografia), driver compreso se l'abbiamo messo noi
	local nuovi
	nuovi=$(comm -13 "$PRIMA/pacchetti.txt" <(installati))
	if [ -n "$nuovi" ]; then
		echo "$nuovi" > "$LAVORO/pacchetti-tolti.txt"
		echo "$nuovi" | grep -q -E '^(nvidia-driver|nvidia-kernel|nvidia-dkms|linux-headers|linux-modules-nvidia)' && riavvio=1
		# ⛔ PRIMA la simulazione: se apt, per togliere i nuovi, toglierebbe anche UN SOLO pacchetto
		#    che c'era, non si toglie niente e lo si dice (`[M]` 1 ott 2026, prova nel contenitore:
		#    un purge cieco si e' fermato a meta' sul «sudo» e ha lasciato dpkg in sospeso)
		local tolti fuori
		# shellcheck disable=SC2086
		tolti=$(SUDO_FORCE_REMOVE=yes apt-get -s purge $nuovi 2>/dev/null | awk '/^Purg /{print $2}' | sed 's/:.*//' | sort -u)
		fuori=$(comm -12 "$PRIMA/pacchetti.txt" <(echo "$tolti"))
		if [ -n "$fuori" ]; then
			avviso "apt toglierebbe anche pacchetti che c'erano: $(echo "$fuori" | tr '\n' ' ') ⇒ non tolgo niente col gestore"
		else
			# shellcheck disable=SC2086
			SUDO_FORCE_REMOVE=yes "${APT[@]}" purge $nuovi > "$LAVORO/purge.txt" 2>&1 \
				&& ok "tolti $(echo "$nuovi" | wc -l) pacchetti nuovi" \
				|| avviso "apt-get purge con errori (purge.txt)"
		fi
		dpkg --configure -a > /dev/null 2>&1
	fi
	# 6. /etc/apt com'era (depositi di Google e Mozilla, non-free, universe)
	rm -rf /etc/apt
	tar -C / -xpf "$PRIMA/etc-apt.tar"
	"${APT[@]}" update > /dev/null 2>&1
	ok "/etc/apt com'era"
	if [ ! -f "$PRIMA/etc-remotix" ]; then rm -rf /etc/remotix /var/lib/remotix; fi
	# 7. che cosa resta diverso, detto
	local dopo_p dopo_u
	dopo_p=$(comm -3 "$PRIMA/pacchetti.txt" <(installati) | tr -d '\t' | tr '\n' ' ')
	dopo_u=$(comm -13 "$PRIMA/utenti.txt" <(getent passwd | cut -d: -f1 | sort) | tr '\n' ' ')
	{
		echo "pacchetti diversi da prima: ${dopo_p:-nessuno}"
		echo "utenti in piu' (dai pacchetti): ${dopo_u:-nessuno}"
		echo "riavvio consigliato: $([ $riavvio = 1 ] && echo si || echo no)"
	} | tee "$LAVORO/pulito.txt" | sed 's/^/    /'
	[ $riavvio = 1 ] && avviso "RIAVVIO CONSIGLIATO: driver o modeset tolti"
	ok "pulito (la valigia $VALIGIA e $LAVORO li toglie il portatile, a script finito)"
	return 0
}

stato() {
	log "a che punto siamo"
	local p
	for p in aggiorna controlli driver dipendenze remotix codifica confronto suite raccogli; do
		if [ -f "$FATTO/$p" ]; then printf '    %-11s fatto  %s\n' "$p" "$(cat "$FATTO/$p")"; else printf '    %-11s —\n' "$p"; fi
	done
	[ -f "$EVID/passi.txt" ] && { echo; sed 's/^/    /' "$EVID/passi.txt"; }
}

# un passo, ricordandosi che e' stato fatto (con l'uscita): «tutto» non lo rifa'
passo() {
	local p=$1 c
	"$p"; c=$?
	[ $c != 10 ] && echo "uscita $c · $(date -Is)" > "$FATTO/$p"
	return $c
}

tutto() {
	local p c peggio=0
	# dopo il riavvio chiesto dal passo «driver» si rifanno i controlli e il driver: il verdetto
	# di (a) dev'essere sul driver vero, quello caricato adesso
	if [ -f "$LAVORO/riavvio-chiesto" ]; then
		rm -f "$LAVORO/riavvio-chiesto" "$FATTO/controlli" "$FATTO/driver"
		log "dopo il riavvio: rifaccio controlli e driver"
	fi
	for p in aggiorna controlli driver dipendenze remotix codifica confronto suite raccogli; do
		case " ${RIFAI:-} " in *" $p "*) rm -f "$FATTO/$p" ;; esac
		if [ -f "$FATTO/$p" ] && [ "$p" != raccogli ]; then
			log "$p: gia' fatto ($(cat "$FATTO/$p")), salto"
			continue
		fi
		passo "$p"; c=$?
		case $c in
		10) log "SERVE UN RIAVVIO: poi si rilancia «tutto»"; return 10 ;;
		0) ;;
		*)
			[ $c -gt $peggio ] && peggio=$c
			if [ "$p" = controlli ] && [ "${FORZA:-0}" != 1 ]; then
				log "controlli ROSSI: mi fermo (FORZA=1 per andare avanti lo stesso)"
				raccogli
				return 1
			fi
			if [ "$p" = dipendenze ] || [ "$p" = remotix ]; then
				log "$p non riuscito: senza, i passi dopo non hanno senso"
				raccogli
				return 1
			fi
			;;
		esac
	done
	log "FINE"
	sed 's/^/    /' "$EVID/passi.txt"
	return $peggio
}

AZIONE=${1:-stato}
case "$AZIONE" in
aggiorna|controlli|driver|dipendenze|remotix|codifica|confronto|suite)
	passo "$AZIONE"; c=$? ;;
raccogli|pulisci|stato) "$AZIONE"; c=$? ;;
tutto) tutto; c=$? ;;
*) echo "uso: $0 aggiorna|controlli|driver|dipendenze|remotix|codifica|confronto|suite|raccogli|pulisci|stato|tutto"; exit 2 ;;
esac
echo "$c" > "$LAVORO/uscita"
exit "$c"
