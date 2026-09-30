#!/bin/bash
#
# 17-scatola.sh — fase 17, T10: una macchina della matrice come SCATOLA (podman, systemd dentro, la
# scheda vera del server), coi verbi di 17-vm.sh che 17-t10.sh usa: cosi' il copione di §7.3 gira
# uguale, e cambia solo chi accende la macchina.  Serve alle due macchine che in VM non hanno lo
# screencast di KWin (debian13-kde, leap16-kde: fasi/17 §9, T10; decisione dell'utente 1 ott 2026).
#
#   (sul server, come nicfio, con sudo valido)   bash 17-scatola.sh <verbo> <macchina> …
#     costruisci <m>        l'immagine dalla ricetta Contenitore.<m> (qui accanto)
#     torna <m> [foto]      butta giu' la scatola: la prossima accensione riparte dall'immagine
#     avvia <m>             accende (systemd, la scheda Intel, sshd sulla porta sua) e aspetta ssh
#     ssh <m> cmd…          un comando dentro, da root, via ssh su 127.0.0.1:<porta ssh>
#     ferma <m>             spegne (la scatola resta, spenta)
#     riavvia <m>           il riavvio DELLA SCATOLA (podman restart): il riavvio vero della macchina
#                           non si prova qui — e' verde sulle altre 30 in VM (§7.5)
#     porte <m>             stampa «<porta ssh> <porta REMOTIX>»
#     stato <m>
#
# Porte (--network=host: sono dell'ospite, una per scatola; ⛔ NON quelle della suite 7447/7448,
# 8511-8514, ne' delle VM 23xx/75xx): debian13-kde ssh 8541 REMOTIX 8531 · leap16-kde 8542/8532.
# Permessi come banchi/11-scatole/11-accendi.sh, misurati la' uno per uno: --systemd=always,
# AUDIT_WRITE+AUDIT_CONTROL (pam_loginuid), SYS_ADMIN (polkit), SYS_NICE+WAKE_ALARM (kwin_wayland e
# powerdevil hanno la capacita' scritta sul file), --network=host (netavark non applica le regole).
# La scheda: SOLO la Intel integrata, per percorso PCI, coi nomi card0/renderD128 dentro.
set -uo pipefail
QUI=$(cd "$(dirname "$0")" && pwd)
verbo=${1:?verbo}; m=${2:?macchina}; shift 2
case $m in
debian13-kde) PSSH=8541; PRX=8531 ;;
leap16-kde)   PSSH=8542; PRX=8532 ;;
*) echo "⛔ $m: non e' una macchina da scatola (debian13-kde | leap16-kde)"; exit 2 ;;
esac
NOME="t10-kde-${m%%-*}"
IMMAGINE="t10/$m:cliente"
CHIAVE=${CHIAVE:-/media/REMOTIX/vm17/ssh/id_ed25519}
P() { sudo -n podman "$@"; }
ok()  { printf '  OK  %s\n' "$*"; }
die() { printf '  NO  %s\n' "$*"; exit 1; }
ssh_s() {
	ssh -i "$CHIAVE" -p "$PSSH" -o BatchMode=yes -o ConnectTimeout=5 \
		-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR \
		root@127.0.0.1 "$@"
}
accesa() { [ "$(P inspect -f '{{.State.Running}}' "$NOME" 2>/dev/null)" = true ]; }
aspetta_ssh() {  # aspetta_ssh <secondi>
	local t=0
	until ssh_s true 2>/dev/null; do
		accesa || die "la scatola $NOME si e' fermata"
		sleep 2; t=$((t + 2))
		[ "$t" -lt "$1" ] || die "ssh non risponde dopo $1 s"
	done
	ok "ssh risponde dopo ${t} s"
}

case $verbo in
porte) echo "$PSSH $PRX" ;;
stato) P ps -a --filter "name=^$NOME\$" --format '{{.Names}} {{.Status}} {{.Image}}' ;;
costruisci)
	[ -f "$QUI/Contenitore.$m" ] || die "manca $QUI/Contenitore.$m"
	[ -f "$QUI/chiave-banco.pub" ] || cp "$CHIAVE.pub" "$QUI/chiave-banco.pub"
	P build --network=host --build-arg "PORTA_SSH=$PSSH" -f "$QUI/Contenitore.$m" -t "$IMMAGINE" "$QUI" || die "costruzione fallita"
	ok "immagine $IMMAGINE"
	;;
torna)
	P rm -f -t 0 "$NOME" >/dev/null 2>&1
	ok "$NOME buttata giu': ripartira' dall'immagine $IMMAGINE (la «foto» ${1:-cliente})"
	;;
avvia)
	accesa && { ok "$NOME e' gia' accesa"; exit 0; }
	PCI=0000:00:02.0
	CARD=$(readlink -f "/dev/dri/by-path/pci-$PCI-card"); RENDER=$(readlink -f "/dev/dri/by-path/pci-$PCI-render")
	[ "$(basename "$(readlink -f "/sys/class/drm/$(basename "$RENDER")/device/driver")")" = i915 ] || die "il nodo $RENDER non e' della Intel: non accendo"
	P rm -f -t 0 "$NOME" >/dev/null 2>&1
	P run -d --name "$NOME" \
		--systemd=always --pids-limit 16384 --network=host \
		--device "$CARD:/dev/dri/card0" --device "$RENDER:/dev/dri/renderD128" \
		--cap-add=AUDIT_WRITE --cap-add=AUDIT_CONTROL --cap-add=SYS_ADMIN --cap-add=SYS_NICE --cap-add=WAKE_ALARM \
		"$IMMAGINE" >/dev/null || die "podman run fallito"
	for _ in $(seq 1 90); do
		S=$(P exec "$NOME" systemctl is-system-running 2>&1 | head -1)
		case $S in running|degraded) break ;; esac
		sleep 1
	done
	ok "$NOME accesa (systemd: ${S:-ignoto}; scheda $CARD→card0, $RENDER→renderD128; ssh :$PSSH, REMOTIX :$PRX)"
	aspetta_ssh 60
	;;
ssh) ssh_s "$@" ;;
ferma)
	accesa || { ok "$NOME e' gia' spenta"; exit 0; }
	P stop -t 15 "$NOME" >/dev/null && ok "$NOME spenta (resta, spenta)"
	;;
riavvia)
	accesa || die "$NOME e' spenta"
	a0=$(P inspect -f '{{.State.StartedAt}}' "$NOME")
	P restart -t 15 "$NOME" >/dev/null || die "podman restart fallito"
	a1=$(P inspect -f '{{.State.StartedAt}}' "$NOME")
	[ "$a0" != "$a1" ] || die "la scatola non e' ripartita (StartedAt invariato)"
	for _ in $(seq 1 90); do
		S=$(P exec "$NOME" systemctl is-system-running 2>&1 | head -1)
		case $S in running|degraded) break ;; esac
		sleep 1
	done
	ok "riavviata: il contenitore e' ripartito ($a0 → $a1; systemd ${S:-ignoto})"
	aspetta_ssh 60
	;;
*) echo "verbo sconosciuto: $verbo"; exit 2 ;;
esac
