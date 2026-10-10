#!/bin/bash
#
# 17-scatola.sh — fase 17: una macchina della matrice come SCATOLA (podman, systemd dentro, la scheda
# vera del server), coi verbi di 17-vm.sh che 17-t10.sh usa: così il copione di §7.3 gira uguale, e
# cambia solo chi accende la macchina. Dal 10 ott 2026 vale per le 26 combinazioni (fasi/17 §3): le
# VM non hanno una scheda, e dalla fase 19 l'installatore rifiuta una macchina senza (§10.27).
#
#   (sul server, come nicfio, con sudo valido)   [REMOTIX_SCHEDA=intel|amd] bash 17-scatola.sh <verbo> <m> …
#     costruisci <m>        l'immagine dalla ricetta della distribuzione (Contenitore.<famiglia>,
#                           il desktop come argomento)
#     costruisci-tutte      le 26 immagini, una dopo l'altra (registro in $T17/costruzione.log)
#     torna <m> [foto]      butta giù la scatola: la prossima accensione riparte dall'immagine
#     avvia <m>             accende (systemd, la scheda, sshd sulla porta sua) e aspetta ssh
#     ssh <m> cmd…          un comando dentro, da root, via ssh su 127.0.0.1:<porta ssh>
#     ferma <m>             spegne (la scatola resta, spenta)
#     riavvia <m>           il riavvio DELLA SCATOLA (podman restart): il riavvio vero della macchina
#                           non si prova qui — è verde sulle 32 in VM del 1 ott (§7.5)
#     porte <m>             stampa «<porta ssh> <porta REMOTIX>»
#     stato <m> | elenco    una scatola | le 26 e le accese
#
# <m> = <distro>-<desktop>: debian13, ubuntu2604, fedora44, arch, tumbleweed, leap16 × gnome, kde,
# xfce, lxqt; alma10 × gnome, kde.
#
# ⭐ IN PARALLELO, fino a 4 (memoria «banchi in parallelo»: porta, ban-file e socket propri, o il ban
#   di uno ferma tutti). Ogni scatola ha:
#   · nome proprio, con la scheda: t17-<m>-<scheda> (la stessa macchina può girare su Intel e Radeon);
#   · porte proprie dell'ospite (--network=host): ssh 8600+10n+k, REMOTIX 8800+10n+k, e +100 sulla
#     Radeon (n = distribuzione 1-7, k = desktop 1-4) ⇒ 8611…8674 / 8811…8874 (Intel),
#     8711…8774 / 8911…8974 (Radeon). ⛔ Mai quelle della suite (7447/7448, 8511-8514) né delle VM
#     (23xx/75xx);
#   · ban-file, socket e /run di REMOTIX DENTRO la scatola (filesystem suo): nessuna condivisione.
#   ⛔ Non prende la serratura delle scatole di rete11 (/media/REMOTIX/rete11/.scatole.lock): quella
#   protegge gli inquilini c<n>u<n> delle scatole rete11-* dallo sgombero del gancio, e le t17-* non
#   ne hanno. Il tetto di 4 lo tiene `avvia` contando le t17-* accese.
#
# Permessi come banchi/11-scatole/11-accendi.sh, misurati là uno per uno: --systemd=always,
# AUDIT_WRITE+AUDIT_CONTROL (pam_loginuid), SYS_ADMIN (polkit), SYS_NICE+WAKE_ALARM (kwin_wayland e
# powerdevil hanno la capacità scritta sul file), --network=host (netavark non applica le regole).
# La scheda: per percorso PCI e driver (i915 | amdgpu), coi nomi card0/renderD128 dentro, e ANCHE col
# nome vero se è diverso (libdrm ricostruisce il nome dal minor: 11-accendi.sh, prova-amd-1).
set -uo pipefail
QUI=$(cd "$(dirname "$0")" && pwd)
T17=${T17:-/media/REMOTIX/vm17/t17}
CHIAVE=${CHIAVE:-/media/REMOTIX/vm17/ssh/id_ed25519}
SCHEDA=${REMOTIX_SCHEDA:-intel}
TETTO=${T17_TETTO:-4}
MATRICE="debian13 ubuntu2604 fedora44 arch tumbleweed leap16 alma10"
P() { sudo -n podman "$@"; }
ok()  { printf '  OK  %s\n' "$*"; }
die() { printf '  NO  %s\n' "$*"; exit 1; }

macchine() {  # le 26, una per riga
	local d e
	for d in $MATRICE; do
		for e in gnome kde xfce lxqt; do
			[ "$d" = alma10 ] && case $e in xfce|lxqt) continue ;; esac
			echo "$d-$e"
		done
	done
}

scegli() {  # scegli <m>: imposta D, DE, n, k, FAM, ARGS, PSSH, PRX, NOME, IMMAGINE
	m=$1; D=${m%%-*}; DE=${m#*-}
	macchine | grep -qx "$m" || die "$m: non è nella matrice (bash 17-scatola.sh elenco)"
	local y; n=0; for y in $MATRICE; do n=$((n + 1)); [ "$y" = "$D" ] && break; done
	case $DE in gnome) k=1 ;; kde) k=2 ;; xfce) k=3 ;; lxqt) k=4 ;; esac
	ARGS=(--build-arg "DESKTOP=$DE")
	case $D in
	tumbleweed) FAM=suse; ARGS+=(--build-arg BASE=tumbleweed) ;;
	leap16)     FAM=suse; ARGS+=(--build-arg BASE=leap:16.0) ;;
	*)          FAM=$D ;;
	esac
	case $SCHEDA in
	intel) DRV=i915; s=0 ;;
	amd)   DRV=amdgpu; s=100 ;;
	*) die "REMOTIX_SCHEDA=«$SCHEDA»: vale intel o amd" ;;
	esac
	PSSH=$((8600 + s + 10 * n + k)); PRX=$((8800 + s + 10 * n + k))
	NOME="t17-$m-$SCHEDA"
	IMMAGINE="t17/$m:cliente"
}

ssh_s() {
	ssh -i "$CHIAVE" -p "$PSSH" -o BatchMode=yes -o ConnectTimeout=5 \
		-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR \
		root@127.0.0.1 "$@"
}
accesa() { [ "$(P inspect -f '{{.State.Running}}' "$NOME" 2>/dev/null)" = true ]; }
aspetta_systemd() {
	local S=""
	for _ in $(seq 1 120); do
		S=$(P exec "$NOME" systemctl is-system-running 2>&1 | head -1)
		case $S in running|degraded) break ;; esac
		sleep 1
	done
	echo "${S:-ignoto}"
}
aspetta_ssh() {  # aspetta_ssh <secondi>
	local t=0
	until ssh_s true 2>/dev/null; do
		accesa || die "la scatola $NOME si è fermata"
		sleep 2; t=$((t + 2))
		[ "$t" -lt "$1" ] || die "ssh non risponde dopo $1 s"
	done
	ok "ssh risponde dopo ${t} s"
}

costruisci() {  # costruisci <m>
	scegli "$1"
	[ -f "$QUI/Contenitore.$FAM" ] || die "manca $QUI/Contenitore.$FAM"
	[ -f "$QUI/chiave-banco.pub" ] || cp "$CHIAVE.pub" "$QUI/chiave-banco.pub" || die "manca $CHIAVE.pub"
	# l'immagine non dipende dalla scheda né dalla porta: la porta ssh di costruzione è quella Intel,
	# e `avvia` la riscrive per la Radeon (sotto)
	P build --network=host "${ARGS[@]}" --build-arg "PORTA_SSH=$PSSH" \
		-f "$QUI/Contenitore.$FAM" -t "$IMMAGINE" "$QUI" || die "costruzione di $m fallita"
	ok "immagine $IMMAGINE"
}

verbo=${1:?verbo}; shift
case $verbo in
elenco)
	for x in $(macchine); do
		scegli "$x"
		printf '%-18s ssh %s REMOTIX %s  %s\n' "$x" "$PSSH" "$PRX" \
			"$(P image exists "$IMMAGINE" && echo immagine || echo '—')$(accesa && echo ' · ACCESA')"
	done
	exit 0 ;;
costruisci-tutte)
	mkdir -p "$T17"
	for x in $(macchine); do
		t0=$(date +%s)
		if ( costruisci "$x" ) >>"$T17/costruzione.log" 2>&1; then e=OK; else e=FALLITA; fi
		printf '%s %-18s %s in %s s\n' "$(date -u +%H:%M:%S)" "$x" "$e" "$(( $(date +%s) - t0 ))" | tee -a "$T17/costruzione.log"
	done
	exit 0 ;;
esac

scegli "${1:?macchina}"; shift
case $verbo in
porte) echo "$PSSH $PRX" ;;
stato) P ps -a --filter "name=^$NOME\$" --format '{{.Names}} {{.Status}} {{.Image}}' ;;
costruisci) costruisci "$m" ;;
torna)
	P rm -f -t 0 "$NOME" >/dev/null 2>&1
	ok "$NOME buttata giù: ripartirà dall'immagine $IMMAGINE (la «foto» ${1:-cliente})"
	;;
avvia)
	accesa && { ok "$NOME è già accesa"; exit 0; }
	P image exists "$IMMAGINE" || die "manca l'immagine $IMMAGINE: bash 17-scatola.sh costruisci $m"
	accese=$(P ps --filter 'name=^t17-' --format '{{.Names}}' | grep -c . || true)
	[ "$accese" -lt "$TETTO" ] || die "già $accese scatole t17 accese (tetto $TETTO)"
	CARD=""; RENDER=""
	for C in /sys/class/drm/card[0-9]*; do
		case "$C" in *-*) continue ;; esac
		[ -e "$C/device/driver" ] || continue
		[ "$(basename "$(readlink -f "$C/device/driver")")" = "$DRV" ] || continue
		PCI=$(basename "$(readlink -f "$C/device")")
		CARD=$(readlink -f "/dev/dri/by-path/pci-$PCI-card" 2>/dev/null)
		RENDER=$(readlink -f "/dev/dri/by-path/pci-$PCI-render" 2>/dev/null)
		break
	done
	[ -e "$CARD" ] && [ -e "$RENDER" ] || die "non trovo la scheda $SCHEDA (driver $DRV): non accendo su un'altra"
	VERI=()
	for N in "$CARD" "$RENDER"; do
		case "$N" in /dev/dri/card0|/dev/dri/renderD128) ;; *) VERI+=(--device "$N:$N") ;; esac
	done
	P rm -f -t 0 "$NOME" >/dev/null 2>&1
	P run -d --name "$NOME" \
		--systemd=always --pids-limit 16384 --network=host \
		--device "$CARD:/dev/dri/card0" --device "$RENDER:/dev/dri/renderD128" "${VERI[@]}" \
		--cap-add=AUDIT_WRITE --cap-add=AUDIT_CONTROL --cap-add=SYS_ADMIN --cap-add=SYS_NICE --cap-add=WAKE_ALARM \
		"$IMMAGINE" >/dev/null || die "podman run fallito"
	S=$(aspetta_systemd)
	# la porta ssh: l'immagine nasce con quella Intel; sulla Radeon (o se cambia lo schema) la si
	# riscrive prima che il banco entri
	P exec "$NOME" sh -c "grep -q '^Port $PSSH\$' /etc/ssh/sshd_config.d/t17.conf || { sed -i 's/^Port .*/Port $PSSH/' /etc/ssh/sshd_config.d/t17.conf; systemctl restart sshd.service 2>/dev/null || systemctl restart ssh.service; }"
	ok "$NOME accesa (systemd: $S; scheda $CARD→card0, $RENDER→renderD128${VERI:+ e col nome vero}; ssh :$PSSH, REMOTIX :$PRX)"
	aspetta_ssh 90
	;;
ssh) ssh_s "$@" ;;
ferma)
	accesa || { ok "$NOME è già spenta"; exit 0; }
	P stop -t 15 "$NOME" >/dev/null && ok "$NOME spenta (resta, spenta)"
	;;
riavvia)
	accesa || die "$NOME è spenta"
	a0=$(P inspect -f '{{.State.StartedAt}}' "$NOME")
	P restart -t 15 "$NOME" >/dev/null || die "podman restart fallito"
	a1=$(P inspect -f '{{.State.StartedAt}}' "$NOME")
	[ "$a0" != "$a1" ] || die "la scatola non è ripartita (StartedAt invariato)"
	S=$(aspetta_systemd)
	ok "riavviata: il contenitore è ripartito ($a0 → $a1; systemd $S)"
	aspetta_ssh 90
	;;
*) echo "verbo sconosciuto: $verbo"; exit 2 ;;
esac
