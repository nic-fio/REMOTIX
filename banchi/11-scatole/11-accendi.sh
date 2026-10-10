#!/bin/bash
# ===========================================================================
# 11-accendi.sh — builds and starts ONE box of the safety net
#
#   bash 11-accendi.sh costruisci [gnome]     rebuilds the image from the recipe
#   bash 11-accendi.sh accendi    [gnome]     knocks down and restarts the box
#        REMOTIX_SCHEDA=amd bash 11-accendi.sh accendi [gnome]   ... on the RX 6800
#                                         (default intel: phase 16 §11)
#   bash 11-accendi.sh passo0     [gnome]     runs step 0 inside
#   bash 11-accendi.sh c1         [gnome] [n]  the session is born and shows
#   bash 11-accendi.sh c2         [gnome] [--applicazione-che-muore|--finestra-che-non-si-apre]
#   bash 11-accendi.sh c3         [gnome] [--scena-ferma|--fotogramma-ripetuto|--codificatore-fermo]
#   bash 11-accendi.sh c4         [gnome] [--senza-tasto|--scena-sorda]  the key reaches the screen
#   bash 11-accendi.sh c6         [gnome] [--uccidi-la-sessione]  detaches and finds itself again
#   bash 11-accendi.sh c8         [gnome] [--senza-cura]  the second one opens the browser
#   bash 11-accendi.sh c8b        [gnome] [--senza-cura]  the page shows FROM THE CLIENT
#   bash 11-accendi.sh c5         [gnome] [--senza-sorgente]  the sound is not silence
#   bash 11-accendi.sh c7         [gnome] [--solo-distacco|--lascia-un-processo]
#   bash 11-accendi.sh c9         [gnome]     the log says WHOM it is talking about
#   bash 11-accendi.sh c17        [gnome] [--senza-copia]  the clipboard in both directions
#   bash 11-accendi.sh c18        [gnome] [--senza-usermod]  the product sets the groups
#   bash 11-accendi.sh c19        [gnome] [--lascia-un-inquilino|--lascia-una-casa]
#                                         nobody from the net stays inside
#   bash 11-accendi.sh c20        [gnome] [--scena-che-lampeggia]
#                                         rebirth after «Log out» brings no ghosts
#   bash 11-accendi.sh c10                    the twin copies (does NOT want the box)
#   bash 11-accendi.sh impronta   [gnome]     prints the fingerprint (R3)
#   bash 11-accendi.sh eta        [gnome]     how old the box is (the guard)
#   bash 11-accendi.sh bilancio   [gnome]     server, tenants, /tmp: what is there now
#   bash 11-accendi.sh spegni     [gnome]
#
# ⚠ C2 · C3 · C4 · C6 · C8b · C17 run USEFULLY only where the product provides
#   what they want (image, input, clipboard): the list, per desktop and per
#   mesh, is in `11-capacita-del-prodotto.sh` — the same one the
#   hook reads.  `[R]` 21 Sep 2026: gnome and kde everything; xfce only the image;
#   lxqt nothing.  Launched by hand where something is missing they give **3** — «I could
#   not look» — and that is right.
#
# ⛔ It runs ON THE TEST MACHINE, as administrator.
# ===========================================================================
#
# ⛔⛔ THE EXTRA PERMISSIONS, AND WHY EACH ONE — none out of habit
#
# Every permission added moves the box away from the real machine, ⇒ and
# so each one must be justified by what breaks without it.  `[M]` 25 August
# 2026, measured one by one at step 0:
#
#   --systemd=always        the first process must be `systemd`, or the
#                           question of step 0 cannot even be asked
#   --device /dev/dri       ⭐ THE REAL GRAPHICS CARD.  It is the reason we
#                           use boxes and not virtual machines (D1)
#   --cap-add=AUDIT_CONTROL ⛔ without it, `pam_loginuid.so` (which in Debian is
#                           `required`) fails and THE USER MANAGER DOES NOT START
#   --cap-add=AUDIT_WRITE   goes with the previous one in the same PAM chain
#   --network=host          ⚠ it is NOT a choice: `netavark` on this machine
#                           cannot apply the network rules
#                           («nft did not return successfully»).  ⛔ And it has a
#                           PRICE that must be written: four boxes started
#                           together share the host's ports, so
#                           each will have to have ITS OWN port — or they will step on
#                           each other's toes in a way that looks like a fault of the
#                           product.  ⇒ To be reviewed when C14 is done.
#
# ⛔ And what was NOT done, on purpose: `--privileged`.  A generic
#    permission would have let everything through and taught nothing:
#    the list above is what the product REALLY ASKS FOR, and it is a
#    result of step 0, not a convenience.
# ===========================================================================
set -uo pipefail

DESKTOP=${2:-gnome}
BASE=$(cd "$(dirname "$0")" && pwd)
NOME="rete11-$DESKTOP"
IMMAGINE="rete11/$DESKTOP:p0"
RICETTA="$BASE/Contenitore.$DESKTOP"
# ⭐ phase 20 §7: `<desktop>-xrdp` is the box of that desktop with xrdp, from ONE
#   recipe only (Contenitore.xrdp) built on top of the measurements image.
DESKTOP_BASE=${DESKTOP%-xrdp}
ARGOMENTI_RICETTA=""
if [ "$DESKTOP_BASE" != "$DESKTOP" ]; then
	RICETTA="$BASE/Contenitore.xrdp"
	ARGOMENTI_RICETTA="--build-arg DESKTOP=$DESKTOP_BASE"
fi
# ⭐ What the product can do, and on which desktop: the SAME list as the
#   hook, in one place only.  ⛔ If it is missing, the gate stays CLOSED and says so.
if [ -r "$BASE/11-capacita-del-prodotto.sh" ]; then
	. "$BASE/11-capacita-del-prodotto.sh"
else
	prodotto_pronto() {
		printf '11-capacita-del-prodotto.sh is missing next to 11-accendi.sh: I do not know what the product can do'
		return 1
	}
fi
# ⚠ One port per box: with `--network=host` the four boxes share
#   the host's ports, so two on the same port would step on each other's toes
#   in a way that looks like a fault of the product.
case "$DESKTOP" in
  gnome) PORTA=8511 ;;
  kde)   PORTA=8512 ;;
  xfce)  PORTA=8513 ;;
  lxqt)  PORTA=8514 ;;
  *)     PORTA=8519 ;;
esac

# ---------------------------------------------------------------------------
# ⛔⛔ THE EXTRA PERMISSIONS **THIS** DESKTOP ASKS FOR, and no other.
#
# `[M]` 26 August 2026, and it is worth reading: the GNOME box holds with
# the common permissions; ⛔ the PLASMA one does not.  `/usr/bin/kwin_wayland` carries
# `cap_sys_nice=ep`, and a program with a capability written on the file
# **cannot even be started** if that capability is not in the box's
# set: `env: kwin_wayland: Operation not permitted`.
#
# ⭐⭐ AND IT IS THE THESIS OF THE PHASE, happening at the first attempt: **the second
#     desktop asked for something the first did not ask for.**  ⇒ Discovering it
#     now costs ten minutes; discovering it inside phase 12, in the middle of the
#     new code, would have cost half a day and a wrong diagnosis.
#
# ⚠ And it is NOT given to everyone: giving it to GNOME too would mean testing GNOME in an
#   environment different from the one it really runs in — that is moving the
#   box away from the product for our own convenience.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ⛔⛔ AND A PERMISSION THAT HOLDS FOR ALL, found on 27 August 2026 — `SYS_ADMIN`
#
# `[M]` Without it, inside the box **`polkit.service` does not start** (it exits `217/USER`)
# and `upower.service` dies behind it: **1 213 restarts**.  ⛔ And `gnome-shell`
# calls them SYNCHRONOUSLY at startup: it takes **four 25 000 ms timeouts in
# a row** ⇒ for **~97 seconds Mutter answers nothing**, neither D-Bus nor
# Wayland.
#
# ⭐⭐ AND IT IS THE REASON FOR THE DEFECT THAT LOOKED LIKE THE PRODUCT'S: the session **is not
#     born blind — it is born ~97 s late**.  `[M]` gu1 98,0 s · gu2 101,0 s
#     · gu3 95,5 s, and then `negotiated format: 1920x1080` and the frames start.
#     ⇒ The benches were looking in a window shorter than the phenomenon.
#
# ⚠ And this permission does NOT move the box away from the real machine: it
#   BRINGS IT CLOSER.  On the real machine `polkit` works; ⛔ it was the box that was
#   different, and the difference showed as a fault of the product.
# ---------------------------------------------------------------------------
CAPS_COMUNI="--cap-add=SYS_ADMIN"

case "$DESKTOP" in
  # ⭐ WAKE_ALARM (phase 12, 19 Sep 2026): `org_kde_powerdevil` carries the
  #   file capability `cap_wake_alarm=ep`, and an executable with a capability
  #   OUTSIDE the container's bound does not run at all ⇒ `[M]` 203/EXEC
  #   «Operation not permitted», powerdevil dead at every session.  Same
  #   reason as above: on the real machine it starts, and the permission BRINGS IT CLOSER.
  kde|kde-xrdp) CAPS="$CAPS_COMUNI --cap-add=SYS_NICE --cap-add=WAKE_ALARM" ;;
  *)   CAPS="$CAPS_COMUNI" ;;
esac

ok()  { printf '  \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '  \033[1;31mNO\033[0m  %s\n' "$*"; }
log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE `/tmp/mozilla` LEFTOVER — THE CURE IS NO LONGER HERE, 27 Aug 2026
#
# ⛔ It is the defect that made C2 RED and C3 and C4 SILENT in the first
#    `--famiglia tutto` run on all four boxes: `/tmp/mozilla` stayed with the
#    FIRST tenant that had taken it — the one of C8/C8b, which run first —
#    ⚠ and the symptom was on the most poisonous side possible: **it looked as if the
#    session did not paint**, while it was alive, painted and with Firefox stuck
#    on the profile choice.
#
# ⚠ For one day the cure was HERE, that is in the piece that lines them up.
# ⛔⛔ AND IT WAS THE WRONG PLACE: a mesh that needs to be «prepared
#     from outside» is, when launched by hand or by another hook, a mesh that gives a
#     **false red** — and it is the defect that costs most in this net.
#
# ⭐ Since 27 August 2026 the cure is INSIDE C2, C3 and C4 (`cura_della_provvista`,
#   which imports C8's `applica_la_cura`, that is the lines of `src/provisiona.sh`):
#   every mesh gives a REAL `~/.cache` to the tenant it creates, ⇒ whose
#   `/tmp/mozilla` is no longer concerns them.  ⛔ And none deletes another's
#   leftover: in parallel (C14) it would make it fall.
# ⇒ ⛔ Here there is nothing left to do, and nothing is put back: two places that
#   do the same thing are two places to diverge from.
# ═══════════════════════════════════════════════════════════════════════════

# ⭐ C10 is the only mesh that does NOT want a box: it reads files of the repository,
#    before compiling.  ⛔ It is BEFORE the administrator check on purpose —
#    you do not need to be root to read three sources — and ⛔ it is NOT run inside the
#    box: there `src/` does not exist, and the mesh would say «I could not look» for
#    ever, which is the cousin of the perpetual red (LEZIONI.md §1.49).
if [ "${1:-}" = c10 ]; then
	shift
	exec python3 "$BASE/11-c10-le-copie-gemelle.py" "$@"
fi

[ "$(id -u)" = 0 ] || { ko "must be run as administrator"; exit 2; }
[ -f "$RICETTA" ] || { ko "I cannot find the recipe $RICETTA"; exit 2; }

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ HOW OLD A BOX IS — the guard, 21 September 2026
#
# `[M]` 21 Sep 2026: after ~14 hours and hundreds of sessions in the same
# box C17 turned RED on gnome and kde; with yesterday's binary (which was
# green) in the old box it was red anyway, and with the new binary in a
# box REBUILT from scratch it was green 2 out of 2.  ⇒ The state a box
# accumulates broke a mesh, ⛔ and the net blamed the product.
# ⭐ The cause found (`[?]`, from the code) and cured is in C17: a fixed file in
#   /tmp.  ⚠ But the category remains, and this guard is there so that it does not come back
#   silently: every launch of a mesh that starts sessions is COUNTED inside
#   the box, and if the box is too old it is said — ⛔ ONE LINE, not
#   a red: the age of the box is not a judgement on the product.
#
# ⚠ The counter lives INSIDE the box, on purpose: `accendi` recreates the
#   container from the image, and the counter disappears with it ⇒ no
#   reset to remember, and no number that outlives the box.
# ⚠ It counts the LAUNCHES that go through here — from the hook AND by hand, because both
#   go through `11-accendi.sh cN`.  ⛔ It does not count C14 (it enters by itself with
#   `podman exec`): it is a floor, not an exact count, and it is said.
#   «sessions» = the launches, with C1 worth its runs; ⚠ still a floor:
#   C8 and C9 start two.
#
# ⛔ THE THRESHOLDS belong to the GUARD and nothing else: they touch no mesh.
#   `[?]` About half of what broke C17 (~14 h, «hundreds» of
#   sessions): the guard must speak BEFORE the defect, not next to it.
#   A `tutto` run on a box is worth `[R]` ~36 launches and ~45 sessions, in
#   less than 3 hours ⇒ a run that starts from a rebuilt box does not trigger it.
# ═══════════════════════════════════════════════════════════════════════════
GUARDIA_ORE=8
GUARDIA_SESSIONI=100
CONTATORE=/var/lib/rete11/lanci-dalla-nascita
NASCITA=/var/lib/rete11/nascita

# ⭐ The age in hours (with one decimal), or «ignota».  First the file `accendi`
#   writes; ⚠ for the boxes started BEFORE this cure, the creation date
#   of the container (`[?]` podman's `.Created.Unix` field has not been
#   tried on this machine: if it does not answer a number, we say «ignota»).
eta_in_ore() {
	local nata adesso
	nata=$(podman exec "$NOME" cat "$NASCITA" 2>/dev/null)
	case "$nata" in ''|*[!0-9]*) nata=$(podman inspect --format '{{.Created.Unix}}' "$NOME" 2>/dev/null) ;; esac
	case "$nata" in ''|*[!0-9]*) printf 'ignota'; return ;; esac
	adesso=$(date +%s)
	awk -v a="$adesso" -v n="$nata" 'BEGIN { printf "%.1f", (a - n) / 3600 }'
}

# ⭐ One line only, for machines: `ore=… lanci=… sessioni=… guardia=entro|SUPERATA`
#   (or `spenta`).  The hook reads it and writes it in the log.
riga_eta() {
	local conti lanci sessioni ore guardia=entro
	if [ "$(podman inspect --format '{{.State.Running}}' "$NOME" 2>/dev/null)" != true ]; then
		printf 'spenta'; return
	fi
	conti=$(podman exec "$NOME" sh -c "test -r $CONTATORE && awk '{ n++; s += \$3 } END { print n+0, s+0 }' $CONTATORE || echo ignoti ignoti" 2>/dev/null)
	lanci=${conti%% *}; sessioni=${conti##* }
	case "$lanci" in ''|*[!0-9]*) lanci=ignoti; sessioni=ignoti ;; esac
	case "$sessioni" in ''|*[!0-9]*) sessioni=ignoti ;; esac
	ore=$(eta_in_ore)
	case "$ore" in ignota) : ;; *) awk -v o="$ore" -v g="$GUARDIA_ORE" 'BEGIN { exit !(o >= g) }' && guardia=SUPERATA ;; esac
	case "$sessioni" in ignoti) : ;; *) [ "$sessioni" -ge "$GUARDIA_SESSIONI" ] && guardia=SUPERATA ;; esac
	printf 'ore=%s lanci=%s sessioni=%s guardia=%s' "$ore" "$lanci" "$sessioni" "$guardia"
}

# ⭐ Counts a launch and, if the box is old, SAYS so — one line.
#   ⛔ If the count fails (box off) we stay silent: the mesh will say it
#   by itself, and a second message about the same fault would be noise.
#   ⚠ Cost `[?]` two or three `podman exec`, under a second: against the `[M]`
#   74 s of a C1 run it does not move the fast family's ceiling.
conta_un_lancio() {
	local maglia=$1 quante=$2 riga
	case "$quante" in ''|*[!0-9]*) quante=1 ;; esac
	podman exec "$NOME" sh -c "mkdir -p /var/lib/rete11 && echo $(date +%s) $maglia $quante >> $CONTATORE" >/dev/null 2>&1 || return 0
	riga=$(riga_eta)
	case "$riga" in
	*guardia=SUPERATA*)
		printf '  \033[1;33m⚠\033[0m  box %s OLD (%s; guard: %s hours or %s sessions) — a red here may be the BOX'"'"'s: «11-accendi.sh accendi|prodotto|server %s» and try again\n' \
			"$NOME" "$riga" "$GUARDIA_ORE" "$GUARDIA_SESSIONI" "$DESKTOP" ;;
	esac
}

case "${1:-}" in
c1)                                     conta_un_lancio c1 "${3:-5}" ;;
c2|c3|c4|c5|c6|c7|c8|c8b|c9|c17|c18|passo0) conta_un_lancio "$1" 1 ;;
esac

case "${1:-}" in

costruisci)
	log "Building the $DESKTOP image from the recipe"
	# ⭐ phase 18 (1 Oct 2026): the box's Firefox is the HOST's one
	#   (recipe, block 4-ter): the .deb is taken from the host's package cache
	#   and put in the build context (`pacchetti/`).
	#   ⛔ If it is missing, we stop: a box with a Firefox different from the one
	#   of the earlier measurements is not the same box, and we would find out later.
	FF_DEB=/media/REMOTIX/cache/apt-host/firefox-esr_140.16.0esr-1~deb13u1_amd64.deb
	mkdir -p "$BASE/pacchetti"
	if [ ! -f "$BASE/pacchetti/$(basename "$FF_DEB")" ]; then
		cp "$FF_DEB" "$BASE/pacchetti/" \
			|| { ko "$FF_DEB is missing: the box would have a Firefox different from the host"; exit 1; }
	fi
	# ⚠ `--network=host` here too: without it, the build does not reach the
	#   packages (same reason as above, measured on 25 August 2026).
	podman build --network=host $ARGOMENTI_RICETTA -f "$RICETTA" -t "$IMMAGINE" "$BASE" || exit 1
	ok "image $IMMAGINE"
	;;

accendi)
	log "Starting the box $NOME"
	# ⭐ WHICH CARD GOES IN — REMOTIX_SCHEDA=intel|amd, default `intel`.
	#   Phase 16 §11: two campaigns, the Intel UHD 770 and then the RX 6800.  ⛔ It is
	#   checked BEFORE knocking down the box: a wrong name must not
	#   cost the box that is there.  See the «NO RADEON» block further down.
	SCHEDA=${REMOTIX_SCHEDA:-intel}
	case "$SCHEDA" in
	intel) DRIVER_SCHEDA="i915|xe"; NOME_SCHEDA="the integrated Intel" ;;
	amd)   DRIVER_SCHEDA="amdgpu";  NOME_SCHEDA="the Radeon (amdgpu)" ;;
	*)     ko "REMOTIX_SCHEDA=«$SCHEDA»: it is intel or amd"; exit 1 ;;
	esac
	# ⛔ `-t 0`, that is we kill instead of asking nicely.  `[M]` 25 August
	#    2026: a normal `podman rm -f` on this box stayed hung
	#    **over four minutes** waiting for an orderly shutdown that never
	#    came, ⛔ and in the meantime it also blocked the following `podman` calls.
	# ⚠ And there remains something to understand, written instead of forgotten: **why does the
	#   box not shut down by itself?**  It does not affect step 0 (the box is
	#   disposable), ⛔ but it affects C7 — «everything closes and nothing remains» — and
	#   there that question becomes the target, not a nuisance.
	# ⛔ First we KILL, then remove, then replace anyway.
	#    `[M]` 26 August 2026: an `rm -f` alone left the box standing
	#    (orderly shutdown that never arrives), and the next run died with
	#    «that name is already in use» — ⛔ a red that had nothing to do with
	#    what was being tested.
	podman kill -s KILL "$NOME" >/dev/null 2>&1
	podman rm -f -t 0 "$NOME" >/dev/null 2>&1
	# ═══════════════════════════════════════════════════════════════════
	# ⛔⛔ `--pids-limit` — IT IS A CURE, NOT A PRECAUTIONARY WIDENING.
	#
	# `[M]` 27 August 2026, measured inside rete11-gnome while a session
	# with Firefox was alive:
	#
	#     /sys/fs/cgroup/pids.max                 = 2048   (podman's default)
	#     /sys/fs/cgroup/init.scope/pids.max      =  307   ⇐ 15% of 2048
	#     /sys/fs/cgroup/init.scope/pids.current  =  260   ⇐ Firefox and its threads
	#
	# ⭐ `podman exec` puts what it launches in **init.scope**, and systemd inside
	#   the box gives it its `DefaultTasksMax=15%` computed on podman's
	#   limit.  ⇒ With a live session **47 threads** were left in all: `[M]`
	#   python stopped at **38** with «can't start new thread», and ⛔ **ffmpeg
	#   could no longer open the PNG encoder**
	#   (`ff_frame_thread_encoder_init failed`, EAGAIN).
	#
	# ⛔⛔ AND THE SYMPTOM WAS ON THE WRONG SIDE: the meshes that look at the
	#     pixel (C2, C3, C4, C6, C8b) exited **3** saying *«N frames
	#     arrived but ffmpeg made no image of them»* — that is a fault
	#     of the BOX presenting itself as a limit of the bench.  ⚠ And the
	#     same ffmpeg, on the same stream, succeeded a minute later, with the
	#     session cleared out: the proof that it was not the stream.
	#
	# ⇒ 16384 ⇒ init.scope reaches **2457**, that is ~9 times the 260 measured.
	# ⭐ And it does NOT move the box away from the real machine: it brings it closer.  On the
	#   real machine there is no thread cap at all.
	# ═══════════════════════════════════════════════════════════════════
	# ═══════════════════════════════════════════════════════════════════
	# ⛔⛔ NO RADEON — ONLY THE INTEGRATED INTEL GOES INTO THE BOX.
	#
	# ✅ User's decision, 18 September 2026: *«no RADEON. We stay
	#    pinned on the integrated Intel»*.  Here there was `--device /dev/dri`, that is
	#    ALL the nodes: inside the box there was also the Radeon (`renderD129`,
	#    group `remotix-nogpu`), and `attrezzi-gruppi-scheda.sh` — which reads all
	#    the nodes — put the tenant ALSO in that group.  `[M]` 18 Sep 2026,
	#    C1: «c1u1 put into the groups READ FROM THE NODES: video remotix-nogpu render».
	#    ⇒ The exclusion of `gpu-udev.sh` held on the host and NOT in the boxes.
	#
	# ⭐ The cure is at the root: the Radeon inside DOES NOT EXIST.  Only
	#   the two nodes of the card with the `i915`/`xe` driver are passed, found by PCI
	#   ADDRESS and not by name — `renderD128` and `renderD129` swap between two
	#   boots — and inside they ALWAYS take the names `card0` and `renderD128`, the ones
	#   step 0 and the meshes expect.
	#
	# ⭐ PHASE 16 §11, the Radeon campaign: with `REMOTIX_SCHEDA=amd` the
	#   RX 6800 goes in INSTEAD of the Intel — found the same way (driver
	#   `amdgpu`, PCI address) and with the SAME names inside, `card0` and
	#   `renderD128`: the product opens `/dev/dri/renderD128` written in the code
	#   (`figlio.c`, NODO_RENDERING) and must not be touched.  ⛔ Always ONE card
	#   only inside: in the AMD campaign the Intel is NOT there, or the box's
	#   compositor could pick it and two machines would be measured.
	# ⚠ On the host the Radeon's nodes belong to the `remotix-nogpu` group (990,
	#   `gpu-udev.sh`), and the product SKIPS that name (`provisiona.sh`).  Inside
	#   gid 990 is taken by `render` (rete11-allinea-gruppi, at startup); below,
	#   if nobody had taken it, ⛔ it is NOT called `remotix-nogpu`.
	# ⛔ The default stays `intel`, and with `intel` this step does EXACTLY
	#   what it did before (same lines, same checks).
	# ═══════════════════════════════════════════════════════════════════
	INTEL_CARD=""; INTEL_RENDER=""
	for C in /sys/class/drm/card[0-9]*; do
		case "$C" in *-*) continue ;; esac
		[ -e "$C/device/driver" ] || continue
		DRV_C=$(basename "$(readlink -f "$C/device/driver")")
		case "|$DRIVER_SCHEDA|" in *"|$DRV_C|"*) ;; *) continue ;; esac
		PCI=$(basename "$(readlink -f "$C/device")")
		INTEL_CARD=$(readlink -f "/dev/dri/by-path/pci-$PCI-card" 2>/dev/null)
		INTEL_RENDER=$(readlink -f "/dev/dri/by-path/pci-$PCI-render" 2>/dev/null)
		break
	done
	# ⚠ The `INTEL_*` names stay so as not to touch the Intel lines: with
	#   REMOTIX_SCHEDA=amd the Radeon is inside.
	if [ ! -e "$INTEL_CARD" ] || [ ! -e "$INTEL_RENDER" ]; then
		ko "⛔ I cannot find $NOME_SCHEDA (driver ${DRIVER_SCHEDA//|//}): NOT starting — the box is not born on another card"
		exit 1
	fi
	if [ "$SCHEDA" = intel ]; then
		ok "card: only the integrated Intel — $INTEL_CARD → card0, $INTEL_RENDER → renderD128"
	else
		ok "card: only the Radeon ($PCI, $DRV_C) — $INTEL_CARD → card0, $INTEL_RENDER → renderD128 (REMOTIX_SCHEDA=amd)"
	fi
	# ⭐⭐ THE NODES ALSO GO IN WITH THEIR REAL NAME — `[M]` 25 September 2026,
	#   prova-amd-1 (phase 16 §11): inside the box the Radeon was `card0` and
	#   `renderD128`, but with the host's NUMBERS (226:1 and 226:129).  libdrm
	#   (`drmGetNodeTypeFromFd`, xf86drm.c) does NOT believe the name the node was
	#   opened with: from the minor it rebuilds `/dev/dri/renderD129` and checks whether it
	#   EXISTS — inside it did not ⇒ «not a DRM node» (-1) for both.
	#   MEASURED consequences, same box:
	#     · wlroots: «'/dev/dri/renderD128' is not a DRM render node» ⇒ pixman
	#       ⇒ no zwp_linux_dmabuf_v1 ⇒ the pixels go through memory
	#       (our stretch p95 205 ms instead of ~20);
	#     · libva: `vaGetDisplayDRM` returns NULL ⇒ «VA-API did not
	#       open … Generic error» ⇒ libx264 in software.
	#   On the Intel it did not show ONLY because today its nodes really are
	#   card0/renderD128: ⛔ «renderD128 and renderD129 swap between two boots»
	#   (above), so it holds for both cards.
	# ⇒ The node goes in TWICE: with the name the product opens (card0/renderD128,
	#   written in figlio.c) and with the name libdrm rebuilds from the minor.  They are
	#   the same device (same maj:min), and libdrm folds them into one
	#   (`drmFoldDuplicatedDevices`).  When the two names coincide (Intel today)
	#   nothing is added: identical to before.
	NODI_VERI=""; NOMI_DENTRO="card0 renderD128"
	for N in "$INTEL_CARD" "$INTEL_RENDER"; do
		case "$N" in /dev/dri/card0|/dev/dri/renderD128) ;;
		*) NODI_VERI="$NODI_VERI --device $N:$N"; NOMI_DENTRO="$NOMI_DENTRO $(basename "$N")" ;;
		esac
	done
	[ -n "$NODI_VERI" ] && ok "and the nodes ALSO go in with their real name (libdrm looks them up by minor):$NODI_VERI"
	NOMI_DENTRO=$(printf '%s\n' $NOMI_DENTRO | sort -u | tr '\n' ' ')

	# shellcheck disable=SC2086
	podman run -d --replace --name "$NOME" \
		--systemd=always \
		--pids-limit 16384 \
		--network=host \
		--device "$INTEL_CARD:/dev/dri/card0" \
		--device "$INTEL_RENDER:/dev/dri/renderD128" \
		$NODI_VERI \
		--cap-add=AUDIT_WRITE \
		--cap-add=AUDIT_CONTROL \
		$CAPS \
		-v "$BASE:/rete11:ro" \
		"$IMMAGINE" >/dev/null || exit 1

	# ⛔ We WAIT for the system inside to have started, we do not count to ten.
	#    A clock deadline is a deadline that fires whenever it happens to.
	for _ in $(seq 1 60); do
		S=$(podman exec "$NOME" systemctl is-system-running 2>&1 | head -1)
		case "$S" in running|degraded) break ;; esac
		sleep 0.5
	done
	ok "$NOME started (internal state: ${S:-unknown})"
	# ⭐ The birth date, for the age guard (see `riga_eta`).  ⚠ The
	#   launch counter is NOT reset: it was born with the container, that is now.
	podman exec "$NOME" sh -c "mkdir -p /var/lib/rete11 && date +%s > $NASCITA" >/dev/null 2>&1 \
		|| ko "I could not write the birth date: the age guard will fall back on podman"

	# ═══════════════════════════════════════════════════════════════════
	# ⭐⭐ EVERY NODE OF THE CARD MUST HAVE, INSIDE, A GROUP WITH A NAME.
	#
	# ⚠ The recipe (`Contenitore.*`) aligns **one node only**, `renderD128`.
	#   `[M]` 27 August 2026, test machine: the nodes are FOUR —
	#   `card0` and `card1` (group `video`), `renderD128` (`render`, 991) and
	#   ⛔ `renderD129`, which on the host belongs to `remotix-nogpu` (990),
	#   ⛔ **a group that did not exist inside the box at all**.
	#
	# ⇒ `[M]` The tool `attrezzi-gruppi-scheda.sh` — which C1, C5, C6, C7 and C9
	#   now call — looks at ALL the nodes and stops with its code 5,
	#   *«a gid of the nodes has no name in /etc/group»*: ⛔ the meshes
	#   exited **3 in one second**, without measuring anything.  ⚠ And they were
	#   right: a gid without a name is a group nobody can join.
	#
	# ⭐ Here the name is NOT pinned: the gid is read from the NODE (`stat`) and the
	#   name from the HOST (`getent`), and the same number with the same
	#   name is created inside.  ⛔ If that name inside is already taken by another number,
	#   we fall back on `scheda<gid>` instead of failing silently.
	# ⚠ And only the GROUP is created: who must join it is decided by
	#   the tool, not by this file.
	# ═══════════════════════════════════════════════════════════════════
	# ⛔ Only the two Intel nodes: they are the only ones that exist inside.
	for N in "$INTEL_CARD" "$INTEL_RENDER"; do
		[ -e "$N" ] || continue
		G=$(stat -c %g "$N" 2>/dev/null) || continue
		[ -n "$G" ] || continue
		podman exec "$NOME" getent group "$G" >/dev/null 2>&1 && continue
		NOME_G=$(getent group "$G" 2>/dev/null | cut -d: -f1)
		[ -n "$NOME_G" ] || NOME_G="scheda$G"
		# ⛔ The name the product excludes does not go in: in the AMD campaign it
		#   would be the card closed to the tenant, that is the blind session.
		[ "$NOME_G" = remotix-nogpu ] && NOME_G="scheda$G"
		if podman exec "$NOME" groupadd -g "$G" "$NOME_G" >/dev/null 2>&1; then
			ok "group $G ($NOME_G) created inside, for $N"
		elif podman exec "$NOME" groupadd -g "$G" "scheda$G" >/dev/null 2>&1; then
			ok "group $G (scheda$G) created inside, for $N — the name $NOME_G was already taken"
		else
			ko "gid $G of $N has NO name inside: the meshes will exit 3"
		fi
	done

	# The proof that the group alignment REALLY happened — «written is not
	# in force»: it is read back from the node, not from the unit's log.
	G_NODO=$(stat -c %g "$INTEL_RENDER" 2>/dev/null)
	G_DENTRO=$(podman exec "$NOME" sh -c 'id -G provanic' 2>/dev/null)
	if printf '%s\n' $G_DENTRO | grep -qx "$G_NODO"; then
		ok "the tenant is in the card's group ($G_NODO)"
	else
		ko "the tenant is NOT in the card's group ($G_NODO): its groups are $G_DENTRO"
		ko "⛔ this way the compositor would fall back on software, and the numbers would be false"
	fi

	# ⛔ «Written is not in force»: we LOOK inside that the Radeon is not there.
	DENTRO=$(podman exec "$NOME" sh -c 'ls /dev/dri | sort | tr "\n" " "' 2>/dev/null)
	if [ "$DENTRO" = "$NOMI_DENTRO" ]; then
		if [ "$SCHEDA" = intel ]; then
			ok "inside there are only the Intel nodes: $DENTRO"
		else
			ok "inside there are only the Radeon nodes: $DENTRO"
		fi
	else
		ko "⛔ inside /dev/dri there is «$DENTRO», not «$NOMI_DENTRO»: shutting down"
		podman rm -f -t 0 "$NOME" >/dev/null 2>&1
		exit 1
	fi
	;;

prodotto)
	# ⛔⛔ AND THE BINARY IS REMOVED BEFORE PUTTING IT BACK.  `[M]` 26 August 2026: with the
	#    server on, `cp` on the binary answers **«Text file busy»** and the action
	#    fails entirely — ⛔ a red that is NOT the product's but the order's
	#    of the commands, that is the most poisonous error shape: it looks like a fault.
	# ⚠ And the cure is NOT to stop the server first: `[M]` tried, `systemctl stop
	#   rete11-server` inside the box **does not return** (it stays hung over two
	#   minutes) ⇒ the action hangs instead of failing, which is worse.
	#   ⭐ The file is removed and rewritten: removing an executable in use is
	#     allowed, overwriting it is not.  The old server keeps running with
	#     its inode until the next `11-accendi.sh server`, and it is declared.
	# ⛔ THE PRODUCT IS PUT INSIDE, IT IS NOT BUILT INSIDE (R1 of the phase
	#    document): one binary only, compiled once, copied identical into all
	#    the boxes.  If every box compiled its own, the comparisons between
	#    desktops would be worth nothing — and it is the fault the user named
	#    first: «if on the GNOME container we have remotix v1 and on the
	#    KDE container remotix v1.2 we crash» (D5).
	#
	# ⛔⛔ AND THE LIBRARIES MUST BE TAKEN WHERE THE REAL SERVER TAKES THEM.
	#     `[M]` 26 August 2026, and it cost us a run: in the machine's `/lib`
	#     there is `libngtcp2.so.16` version 16.2.9, but the product runs with the one
	#     built in `src/b2/ngtcp2/build/lib`, 16.11.0.  Same name, same
	#     «so.16», ⛔ DIFFERENT THING.
	#     ⇒ With the wrong one the server STARTS, says all its startup
	#       lines, ⛔ and DIES at the first client with
	#       `ngtcp2_settingslen_version: Unreachable` — while the client sees
	#       only «Idle timeout».  ⚠ The symptom was on the wrong side.
	#
	# ⚠⚠ AND NO APOSTROPHES inside the `sh -c` block below: `CODER.md` §4-bis.
	#    `[M]` 26 August 2026: an apostrophe in a comment closed the string
	#    half-way, and the script ran the leftover pieces as commands.  ⛔ `bash -n`
	#    does NOT catch it, because the syntax stays valid.
	log "Putting the product inside $NOME"
	podman exec "$NOME" sh -c '
		set -e
		mkdir -p /opt/remotix/lib /var/lib/rete11/certificati /var/lib/rete11/rilievo
		rm -f /opt/remotix/remotix
		cp /rete11/prodotto/remotix          /opt/remotix/
		cp /rete11/prodotto/pagina.html      /opt/remotix/
		cp /rete11/prodotto/01-b3-cliente.py /opt/remotix/
		cp /rete11/11-c1-nasce-e-si-vede.py  /opt/remotix/
		cp /rete11/11-c2-una-finestra-si-apre.py /opt/remotix/
		cp /rete11/11-c2-finestra.html       /opt/remotix/
		cp /rete11/11-c3-i-fotogrammi-cambiano.py /opt/remotix/
		cp /rete11/11-c3-scena.html          /opt/remotix/
		cp /rete11/11-c4-il-tasto-arriva-allo-schermo.py /opt/remotix/
		cp /rete11/11-c6-si-stacca-e-si-ritrova.py /opt/remotix/
		cp /rete11/11-c8-il-secondo-apre-il-browser.py /opt/remotix/
		cp /rete11/11-c8b-la-pagina-si-vede-dal-cliente.py /opt/remotix/
		cp /rete11/11-c8-pagina.html         /opt/remotix/
		cp /rete11/11-c5-il-suono-non-e-silenzio.py /opt/remotix/
		cp /rete11/11-c7-si-chiude-e-non-resta-niente.py /opt/remotix/
		cp /rete11/11-c9-il-registro-dice-di-chi.py /opt/remotix/
		cp /rete11/11-c17-gli-appunti-vanno-nei-due-versi.py /opt/remotix/
		cp /rete11/11-c18-i-gruppi-li-mette-il-prodotto.py /opt/remotix/
		cp /rete11/11-c19-la-scatola-resta-pulita.py /opt/remotix/
		cp /rete11/11-c20-la-rinascita-non-porta-fantasmi.py /opt/remotix/
		cp /rete11/11-c20-scena.html                        /opt/remotix/
		cp /rete11/appunti-gtk.py             /opt/remotix/
		cp /rete11/10-f1-testimone.py        /opt/remotix/
		# ⭐⭐ THE CARD GROUPS TOOL — 27 August 2026.
		# `[M]` The oldest defect of the project, «the session is born blind»,
		# was the tenant NOT in the groups of the /dev/dri nodes: 17 out of 17 see with the
		# groups, 0 out of 4 without.  ⇒ C1, C5, C6, C7 and C9 call this tool
		# and without it they exit 3 — and they are right.
		# ⚠ And it is CARRIED, the logic is not copied: in the repository it lives in
		#   `banchi/`, that is one floor above `$BASE`, and on the test machine it
		#   sits flat in `/media/REMOTIX/rete11` like `10-f1-testimone.py`.
		#   ⛔ A second mount was not needed and would have brought inside also
		#   all the rest of that folder.
		cp /rete11/attrezzi-gruppi-scheda.sh /opt/remotix/
		cp /rete11/prodotto/remotix.pam      /etc/pam.d/remotix
		# ⭐ THE DENIED USERS FILE, like src/provisiona.sh — 3 October 2026.
		# The product PAM (phase 17, D3) opens with pam_listfile on this file,
		# onerr=fail: without it, NOBODY gets in.  Same lines as the real machine.
		if [ ! -f /etc/remotix/utenti-negati ]; then
			install -D -m 644 -o root -g root /dev/null /etc/remotix/utenti-negati
			echo root > /etc/remotix/utenti-negati
		fi
		# ⭐ THE THREE BELTS OF DECISIONI.md §4.7 — phase 12, 19 September 2026.
		# `[M]` The user test on KDE: from the Plasma menu it was possible to
		# power off, because the box answered «challenge» and the real machine
		# answers «no».  `src/provisiona.sh` puts them on the real machine, and
		# nobody had ever put them in the boxes: the box was DIFFERENT.
		# ⚠ Same lines as provisiona.sh, same files: no copy of the logic.
		install -D -m 644 /rete11/prodotto/remotix-niente-spegnimento.rules /etc/polkit-1/rules.d/50-remotix-niente-spegnimento.rules
		install -D -m 644 /rete11/prodotto/remotix-tasti.conf /etc/systemd/logind.conf.d/remotix-tasti.conf
		mkdir -p /etc/systemd/sleep.conf.d
		printf "[Sleep]\nAllowSuspend=no\nAllowHibernation=no\nAllowSuspendThenHibernate=no\nAllowHybridSleep=no\n" > /etc/systemd/sleep.conf.d/remotix-niente-sospensione.conf
		systemctl restart polkit >/dev/null 2>&1 || true
		systemctl reload systemd-logind >/dev/null 2>&1 || true
		# ⭐ THE KWIN PERMISSION IS SET BY THE BENCH, LIKE THE PACKAGE — phase 17.
		# Until phase 16 the server wrote it as root; since phase 17
		# (§6.5-bis) the file belongs to the package and the product only CHECKS it
		# (RX-KDE-001/002/003).  ⇒ Without this line KDE in the boxes no longer
		# shows.  Same content as packaging/debian/org.kde.remotix.desktop,
		# with Exec on the box binary.  In all the boxes, like the
		# package, which does not look at the desktop.
		mkdir -p /usr/share/applications
		printf "[Desktop Entry]\nType=Application\nName=REMOTIX\nComment=The desktop in the browser\nExec=/opt/remotix/remotix\nNoDisplay=true\nX-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1\n" > /usr/share/applications/org.kde.remotix.desktop
		chmod 644 /usr/share/applications/org.kde.remotix.desktop
		rm -f /opt/remotix/lib/*
		cp -a /rete11/prodotto/lib/* /opt/remotix/lib/
		echo /opt/remotix/lib > /etc/ld.so.conf.d/rete11.conf
		ldconfig 2>/dev/null || true
	' || { ko "I could not put the product inside"; exit 1; }

	MANCA=$(podman exec "$NOME" sh -c 'ldd /opt/remotix/remotix | grep -c "not found"' 2>/dev/null)
	if [ "${MANCA:-9}" = 0 ]; then
		ok "the product is inside, and all the libraries resolve"
		podman exec "$NOME" sh -c 'ldd /opt/remotix/remotix | grep -E "ngtcp2|nghttp3"' | sed 's/^/      /'
	else
		ko "$MANCA libraries do not resolve: the server will die and nobody will know why"
		podman exec "$NOME" sh -c 'ldd /opt/remotix/remotix | grep "not found"' | sed 's/^/      /'
		exit 1
	fi
	# ⛔ And the PAM file is checked AFTER putting it: «written is not in force».
	if podman exec "$NOME" test -f /etc/pam.d/remotix; then
		ok "the product's PAM chain is installed"
	else
		ko "/etc/pam.d/remotix is NOT there: PAM will fall back on «other» = pam_deny, and EVERY right password will be refused"
		exit 1
	fi
	;;

server)
	log "Starting the server inside $NOME on port $PORTA"
	# ⭐ phase 16 (§2): the session ceiling is raised for the stress campaign,
	#   from outside: `sudo env REMOTIX_TETTO_SESSIONI=17 bash 11-accendi.sh server D`.
	#   Without the variable, no option: the product's default (10).
	TETTO=""
	case "${REMOTIX_TETTO_SESSIONI:-}" in
	'') ;;
	*[!0-9]*) ko "REMOTIX_TETTO_SESSIONI=«$REMOTIX_TETTO_SESSIONI» is not a number"; exit 1 ;;
	*) TETTO="--tetto-sessioni $REMOTIX_TETTO_SESSIONI"; ok "session ceiling: $REMOTIX_TETTO_SESSIONI" ;;
	esac
	podman exec "$NOME" sh -c "
		systemctl stop rete11-server 2>/dev/null
		systemctl reset-failed rete11-server 2>/dev/null
		rm -f /var/lib/rete11/registro.log
		systemd-run --unit=rete11-server \
			--working-directory=/opt/remotix \
			--property=StandardOutput=append:/var/lib/rete11/registro.log \
			--property=StandardError=append:/var/lib/rete11/registro.log \
			--property=KillMode=mixed \
			/opt/remotix/remotix --indirizzo 0.0.0.0 --nome 127.0.0.1 --porta $PORTA $TETTO \
			--certificati /var/lib/rete11/certificati --pagina /opt/remotix/pagina.html \
			--ban-file /var/lib/rete11/ban --comando-socket /var/lib/rete11/comando.sock \
			--rilievo /var/lib/rete11/rilievo --parlantina --journal
	" >/dev/null 2>&1

	# ⛔ We wait for it to LISTEN, not for the process to exist: «on» means
	#    someone listening on the port — lesson of phase 10 (§1.36), where a
	#    server with a live process and nobody listening passed for on.
	PRONTO=0
	for _ in $(seq 1 40); do
		if podman exec "$NOME" grep -q "ready: https" /var/lib/rete11/registro.log 2>/dev/null; then
			PRONTO=1; break
		fi
		sleep 0.5
	done
	if [ "$PRONTO" = 1 ]; then
		ok "the server listens on $PORTA"
		podman exec "$NOME" grep -c "⛔" /var/lib/rete11/registro.log 2>/dev/null \
			| sed 's/^/      red lines in the startup log: /'
	else
		ko "the server did not say it was ready within 20 s"
		podman exec "$NOME" tail -8 /var/lib/rete11/registro.log 2>/dev/null | sed 's/^/      /'
		exit 1
	fi
	;;

c1)
	log "C1 — the session is born and shows (inside $NOME)"
	GIRI=${3:-5}
	# ⛔ NO `sh -c` in here, and it is not a whim: `[M]` 26 August 2026, a
	#    `podman exec ... sh -c "cd … && python3 …"` nested inside `systemd-run`
	#    inside `ssh` lost its quotes along the way, ⛔ ran NOTHING
	#    and returned **0** — that is a bench that did not run and says «succeeded».
	# ⇒ The program is called by absolute path, with no shell in between.
	shift 3 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c1-nasce-e-si-vede.py \
		--giri "$GIRI" --porta "$PORTA" "$@"
	exit $?
	;;

c2)
	log "C2 — a window opens (inside $NOME)"
	# ⛔ `--applicazione-che-muore` and `--finestra-che-non-si-apre` are the
	#    ACCEPTANCE TESTS: with the fault injected the outcome reads the other way round, and the
	#    green becomes a red.
	# ⭐ The second is the one that counts: the application stays ALIVE and paints
	#    nothing ⇒ the process count says 1 as in the healthy case, and the pixel
	#    says NO.
	# ⚠ It wants the IMAGE: gnome, kde, xfce (`11-capacita-del-prodotto.sh`).
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c2-una-finestra-si-apre.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c3)
	log "C3 — the frames arrive, and the scene CHANGES (inside $NOME)"
	# ⛔ `--fotogramma-ripetuto` and `--codificatore-fermo` are the ACCEPTANCE TESTS.
	# ⭐ `--scena-ferma` is the NEGATIVE control: with the scene still the mesh
	#    must NOT give red (with a still scene Mutter delivers nothing, and it is a
	#    RESULT — src/figlio.c:3373).
	# ⚠ It wants the IMAGE: gnome, kde, xfce (`11-capacita-del-prodotto.sh`).
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c3-i-fotogrammi-cambiano.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c4)
	log "C4 — the key reaches the screen (inside $NOME)"
	# ⛔ `--senza-tasto` (head) and `--scena-sorda` (tail) are the ACCEPTANCE TESTS: with the
	#    fault injected the outcome reads the other way round, and the green becomes a red.
	# ⚠ It wants the IMAGE and the INPUT: gnome and kde (`11-capacita-del-prodotto.sh`).
	#   On xfce input is increment 3: launched by hand there it will give 3, and that is right.
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c4-il-tasto-arriva-allo-schermo.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c6)
	log "C6 — detaches and finds itself again (inside $NOME)"
	# ⛔ `--uccidi-la-sessione` is the ACCEPTANCE TEST: with the fault injected the outcome
	#    reads the other way round, and the green becomes a red.
	# ⚠ The plan wants it with INPUT: gnome and kde (`11-capacita-del-prodotto.sh`,
	#    where it is also written why that dependency must be looked at again).
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c6-si-stacca-e-si-ritrova.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c8)
	log "C8 — the second user opens the browser (inside $NOME)"
	# ⛔ And `--senza-cura` is passed for the ACCEPTANCE TEST: with the fault injected
	#    the outcome reads the other way round, and the green becomes a red.
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c8-il-secondo-apre-il-browser.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c8b)
	log "C8b — and the same page shows FROM THE CLIENT (inside $NOME)"
	# ⛔ ONLY WHERE THE PRODUCT PROVIDES THE IMAGE.  Elsewhere this mesh would say
	#    «I could not look» for ever, which is the cousin of the perpetual
	#    red (LEZIONI.md §1.49).
	# ⭐ Until 21 Sep 2026 here there was a whitelist of its own («gnome or kde»),
	#   TWIN of the hook's but misaligned: it covered only C8b.  ⇒ Now it
	#   reads the SAME list as the hook (`11-capacita-del-prodotto.sh`), and the
	#   two can no longer say different things.
	if ! perche=$(prodotto_pronto C8b "$DESKTOP"); then
		log "C8b does not run on $DESKTOP: ${perche:-the gate did not answer}"
		exit 3
	fi
	# ⛔ `--senza-cura` is the ACCEPTANCE TEST: the outcome reads the other way round.
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u \
		/opt/remotix/11-c8b-la-pagina-si-vede-dal-cliente.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c5)
	log "C5 — the sound is there and is not silence (inside $NOME)"
	# ⛔ `--senza-sorgente` is the ACCEPTANCE TEST: with the fault injected the outcome reads
	#    the other way round, and the green becomes a red.
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c5-il-suono-non-e-silenzio.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c7)
	log "C7 — everything closes, and nothing remains (inside $NOME)"
	# ⛔ `--lascia-un-processo` is the ACCEPTANCE TEST.
	# ⭐ `--solo-distacco` is the case that must NOT give red: the client
	#    leaves and the stage stays up (I4).
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c7-si-chiude-e-non-resta-niente.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c9)
	log "C9 — the log says WHOM it is talking about (inside $NOME)"
	# ⛔ The mesh opens TWO tenants and keeps them alive TOGETHER: it is the strong form,
	#    and with one only it would not prove what it says.
	# ⚠ The injected fault is asked for with `--togli-nome tutto`, and it defaces the
	#   in-memory COPY of the slice: the log on disk is not touched.
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c9-il-registro-dice-di-chi.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c18)
	log "C18 — the card groups are set by the PRODUCT (inside $NOME)"
	# ⭐ The ONLY mesh that does NOT give the groups to its tenant: it is the fact it
	#   looks at (§7.21).  ⛔ All the others give them with `garantisci_i_gruppi`,
	#   and in doing so they hide this piece of the product.
	# ⚠ The fault is asked for with `--senza-usermod`: `usermod` disappears for the
	#   length of the run and is always put back, even if the run dies.
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c18-i-gruppi-li-mette-il-prodotto.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c19)
	log "C19 — nobody from the net stays inside (inside $NOME)"
	# ⭐⭐ NO GATE, and it is intended: this mesh asks NOTHING of the
	#    product — it looks at the box, and the box exists on every desktop.
	#    ⇒ Like C1, C5, C7, C9, C18 it does not go through `11-capacita-del-prodotto.sh`.
	# ⛔ And it must be launched AFTER the others, not before: it judges what the others
	#    have left.  Launched on a freshly rebuilt box it says green and
	#    proves nothing — it is the hook that puts it in the right place.
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c19-la-scatola-resta-pulita.py "$@"
	exit $?
	;;

c20)
	log "C20 — rebirth after «Log out» brings no ghosts (inside $NOME)"
	# ⛔ ONLY WHERE THE PRODUCT PROVIDES THE IMAGE: the first judge is the PIXELS
	#    of the second login, and without image there is nothing to look at.
	if ! perche=$(prodotto_pronto C20 "$DESKTOP"); then
		log "C20 does not run on $DESKTOP: ${perche:-the gate did not answer}"
		exit 3
	fi
	# ⛔ `--scena-che-lampeggia` is the ACCEPTANCE TEST: the outcome reads the other way round.
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u \
		/opt/remotix/11-c20-la-rinascita-non-porta-fantasmi.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c17)
	log "C17 — the clipboard goes both ways (inside $NOME)"
	# ⛔ `--senza-copia` is the ACCEPTANCE TEST: nobody copies anything, and the three facts
	#    (A, B, R) must come out red.
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c17-gli-appunti-vanno-nei-due-versi.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

passo0)
	log "Step 0 inside $NOME"
	podman exec "$NOME" bash /rete11/11-passo0.sh
	exit $?
	;;

eta)
	# ⭐ The guard, for machines: one line `ore=… lanci=… sessioni=… guardia=…`.
	riga_eta; printf '\n'
	;;

bilancio)
	# ═══════════════════════════════════════════════════════════════════
	# ⭐⭐ THE BALANCE — what is in the box NOW, in one line.
	#
	# ⛔ It serves NOT TO HIDE a real leak of the product.  Rebuilding the
	#    boxes at the start of `tutto` removes the box's dirt, ⚠ but it
	#    would also remove the symptoms of a product that leaks something at every
	#    session (a descriptor, a thread, a child, a user).  ⇒ The hook
	#    takes this balance right before and right after the meshes of a
	#    box — on the SAME server, which is not restarted in between — and
	#    compares.  ⭐ And the entries are split by OWNER:
	#      server_*   the PRODUCT's: the server process and its children
	#      the rest   the BOX's or the BENCHES': leftover tenants, failed
	#                 units, ownerless files in /tmp, logind sessions
	#    ⇒ «the box gets dirty» and «the product leaks» fall into two different
	#      columns instead of a single red.
	# ⚠ It does NOT judge (no outcome 1): it is a new measurement without an injected
	#   fault, and §3.6 does not allow a judgement without one.  It prints and writes.
	# ⚠ And NO APOSTROPHES in the script below (`CODER.md` §4-bis): it goes through
	#   `sh -s`, but the rule holds for every script sent inside.
	# ═══════════════════════════════════════════════════════════════════
	podman exec -i "$NOME" sh -s <<'COPIONE' 2>/dev/null || printf 'spenta\n'
P=$(systemctl show -p MainPID --value rete11-server 2>/dev/null)
case "$P" in ''|0|*[!0-9]*) P=0 ;; esac
[ -d "/proc/$P" ] || P=0
if [ "$P" != 0 ]; then
	FD=$(ls "/proc/$P/fd" 2>/dev/null | wc -l)
	FILI=$(awk '/^Threads:/ { print $2 }' "/proc/$P/status" 2>/dev/null)
	RSS=$(awk '/^VmRSS:/ { print $2 }' "/proc/$P/status" 2>/dev/null)
	FIGLI=$(pgrep -P "$P" 2>/dev/null | wc -l)
else
	FD=-; FILI=-; RSS=-; FIGLI=-
fi
INQ=$(getent passwd | awk -F: '$3 >= 1000 && $3 < 60000 && $1 != "provanic" { n++ } END { print n + 0 }')
SES=$(loginctl list-sessions --no-legend 2>/dev/null | wc -l)
PROC=$(ls -d /proc/[0-9]* 2>/dev/null | wc -l)
FALL=$(systemctl --failed --no-legend --plain 2>/dev/null | wc -l)
UFALL=$(systemctl --failed --no-legend --plain 2>/dev/null | grep -c "^user@")
TMP=$(find /tmp -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)
ORF=$(find /tmp -mindepth 1 -maxdepth 1 -nouser 2>/dev/null | wc -l)
RIL=$(find /var/lib/rete11/rilievo -type f 2>/dev/null | wc -l)
echo "server_pid=$P server_fd=${FD:--} server_fili=${FILI:--} server_rss_kb=${RSS:--} server_figli=${FIGLI:--} inquilini=$INQ sessioni=$SES processi=$PROC fallite=$FALL user_fallite=$UFALL tmp=$TMP tmp_orfani=$ORF rilievo=$RIL"
COPIONE
	;;

impronta)
	# ⛔ R3 of the phase document: alignment is CHECKED.  Here we print
	#    what must be compared across the four boxes — ⭐ the recipe COUNTS
	#    AS MUCH AS the binary: a rebuilt box that pulls in a newer desktop
	#    has the same binary and a different environment.
	printf 'box          : %s\n' "$NOME"
	printf 'image        : %s\n' "$(podman image inspect "$IMMAGINE" --format '{{.Id}}' 2>/dev/null | cut -c1-16)"
	printf 'recipe (md5) : %s\n' "$(md5sum "$RICETTA" | cut -c1-16)"
	# ⭐ The desktop package is told by the ADAPTER, not by this file: so
	#   the fingerprint holds for all four without a single «if the desktop is…».
	PACCO=$(podman exec "$NOME" sh -c '. /usr/local/lib/rete11/adattatore.sh 2>/dev/null && adattatore_pacchetto' 2>/dev/null)
	printf 'desktop      : %s %s\n' "${PACCO:-unknown}" \
	       "$(podman exec "$NOME" sh -c "dpkg-query -W -f='\${Version}' ${PACCO:-x} 2>/dev/null || echo unknown" 2>/dev/null)"
	printf 'mesa         : %s\n' "$(podman exec "$NOME" sh -c 'dpkg-query -W -f="${Version}" mesa-va-drivers 2>/dev/null || echo unknown' 2>/dev/null)"
	printf 'product      : %s\n' "$(podman exec "$NOME" sh -c 'md5sum /opt/remotix/remotix 2>/dev/null | cut -c1-16 || echo "(not inside yet)"' 2>/dev/null)"
	;;

spegni)
	podman rm -f -t 0 "$NOME" >/dev/null 2>&1 && ok "$NOME off" || ko "it was not there"
	;;

*)
	# ⛔⛔ AND THE HELP IS NO LONGER PRINTED BY COUNTING LINES.
	#    `[M]` 27 August 2026: here there was `sed -n 2,16p`, and with the five new
	#    meshes the usage block got longer ⇒ the help silently cut
	#    its last lines, that is `impronta` and `spegni` disappeared
	#    from the help while staying in the program.  ⚠ A line number pinned
	#    inside a file that grows is a sign that falls off by itself.
	# ⇒ Now it prints from line 3 up to the `# ====` line that closes the
	#   block, whatever its number: the file can grow as much as it likes.
	sed -n '3,/^# ====/{/^# ====/d; p;}' "$0"
	exit 2 ;;
esac
