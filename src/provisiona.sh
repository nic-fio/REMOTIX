#!/bin/bash
#
# provisiona.sh — the machine hosting REMOTIX, put into the state the
# product expects.  ⛔ And it is CHECKED at the end, instead of believed.
#
#   sudo bash src/provisiona.sh            everything
#   sudo bash src/provisiona.sh verifica   only the checks, touches nothing
#
# ---------------------------------------------------------------------------
# ⛔⛔ WHY `fondamenta/banco/provision-server.sh` IS NO LONGER USED
#
# `[M]` On the night of 15 August 2026 that script, rerun after a reboot,
# put back the WRONG state and cost us an evening.  In three
# points it works AGAINST v2:
#
#   1. ⛔ it writes `--virtual-monitor 1920x1080` into the Shell's drop-in.  Since 14
#      August that monitor is the DEFECT — "the session takes a monitor of its own,
#      the capture mounts a second one, and the user looks at the empty one"
#      (`sessione.h`).  v2 writes its own `zz-` drop-in to override it;
#   2. ⛔ the polkit rule covers 3 actions of 12 and **misses precisely the
#      `*-multiple-sessions` ones**, that is it fails in the multi-user case it was
#      written for (`DECISIONI.md` §4.7);
#   3. ⛔ it does not recreate the test users nor their groups — and the rootfs lives in
#      RAM, so every reboot takes them away.
#
# ---------------------------------------------------------------------------
# ⭐ WHAT THE PRODUCT CANNOT DO BY ITSELF, and it is the only thing that is here
#
# `DECISIONI.md` §1.10-ter, §4.6-quinquies and §4.7: the product sets by itself everything
# concerning the SESSION (the settings, the drop-in, the inhibition) —
# invariant I7.  ⛔ Only what wants root and holds for the MACHINE stays here:
# the accounts, the groups, polkit, logind, udev, PAM.
set -uo pipefail

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; ESITO=1; }
inf() { printf '    --  %s\n' "$*"; }
tit() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

ESITO=0
QUI=$(cd "$(dirname "$0")" && pwd)
SOLO_VERIFICA=${1:-}

[ "$(id -u)" -eq 0 ] || { echo "⛔ root needed"; exit 2; }

# ---------------------------------------------------------------------------
# ⭐⭐ THE CARD'S GROUPS ARE READ FROM THE NODE — 27 August 2026, phase 11.
#
# ⛔ Here there was `usermod -aG video,render`, that is TWO NAMES NAILED DOWN.  They are
#    right on this distribution and false on the next: the group of
#    `/dev/dri/renderD128` is what the kernel and udev decided on THIS
#    machine, and the only way to know it is **to ask them** — `stat -c %g`.
# ⛔ And the nodes are walked instead of nailing `renderD128`: `renderD128` and
#    `renderD129` swap between two boots (see step 5), and `cardN` and
#    `renderDN` have DIFFERENT groups (`video` and `render`) that are both needed.
# ⚠ A gid is not passed to `usermod -aG`: the NAME is passed, derived from the
#   number with `getent group`.  The number stays what is CHECKED, because a
#   name can change meaning and a gid cannot.
# ⛔⛔ AND THE EXCLUDED NODE IS SKIPPED — 18 September 2026, at the first reprovisioning
#    after the break.  `gpu-udev.sh` puts the discrete card in the `remotix-nogpu` group
#    precisely so that NOBODY is in it.  `[M]` Reading all nodes without
#    distinction, at the second round this script would have put `prova` and `prova2`
#    in `remotix-nogpu`, that is reopened the Radeon to the test users — and the
#    check demanded it: «prova is NOT in the card's groups:
#    remotix-nogpu».  ⇒ One would measure on the wrong card without knowing it.
# ---------------------------------------------------------------------------
GRUPPO_ESCLUSO=remotix-nogpu

gid_della_scheda() {
	local n g escluso
	escluso=$(getent group "$GRUPPO_ESCLUSO" | cut -d: -f3)
	for n in /dev/dri/card[0-9]* /dev/dri/renderD[0-9]*; do
		[ -e "$n" ] || continue
		g=$(stat -c %g "$n" 2>/dev/null) || continue
		[ -n "$escluso" ] && [ "$g" = "$escluso" ] && continue
		printf '%s\n' "$g"
	done | sort -un
}

nomi_della_scheda() {
	local g nome nomi=""
	for g in $(gid_della_scheda); do
		nome=$(getent group "$g" | cut -d: -f1)
		[ -n "$nome" ] || continue
		case ",$nomi," in *",$nome,"*) continue ;; esac
		nomi="${nomi:+$nomi,}$nome"
	done
	printf '%s' "$nomi"
}

GRUPPI_SCHEDA=$(nomi_della_scheda)

# ---------------------------------------------------------------------------
# 1. The test users, and ⛔ THEIR GROUPS
#
# ⛔⛔ `video` and `render` are NOT a convenience of the test environment: they are a
#     REQUIREMENT of the product, and the reason is headless.  On a normal desktop
#     GPU access is given by logind with an **ACL** (udev tag `uaccess`)
#     to the user of the active session **on a seat**; ⇒ our session has no
#     seat on purpose, so that ACL never arrives and without the
#     groups Mesa falls back to llvmpipe **without an error**.
#
# `[M]` 15 August 2026: the symptom is "slow", not "broken" — a command in the
# terminal that answers after a second, and the compositor composing by hand a
# 2544x926 desktop.
#
# ⛔⛔⭐ AND ON 27 AUGUST 2026 THE SYMPTOM TURNED OUT WORSE THAN "SLOW": it is
#      **BLIND**.  `[M]` On the real machine, a tenant without the two groups
#      NEVER sees — **0 sessions of 4**, zero frames, never in 90 seconds —
#      while the tenants with the groups see **17 of 17** in ~2.0 s.  ⭐ And the
#      counter-test, on the same user: given the two groups and the user manager
#      restarted ⇒ **2.04 s**.
# ⛔⛔ It is `fasi/10-multi-tenant-e-il-budget.md` §7.4, "the session born
#      blind": `provanic4/5/6` never succeeded in **98 · 55 · 50** attempts, and
#      they are exactly and only the three users that did not have the two groups.
#      ⇒ It blocked five tests and postponed a phase, and never gave an
#      error.  ⭐ From today the PRODUCT notices it and writes it to the log
#      at the birth of every session (`figlio.c`, `gruppi_della_scheda()`).
# ---------------------------------------------------------------------------
if [ "$SOLO_VERIFICA" != "verifica" ]; then
	tit "The test users, with the groups headless makes us lose"
	if [ -z "$GRUPPI_SCHEDA" ]; then
		ko "⛔ no group readable from the /dev/dri nodes: the tenants will be born BLIND"
	fi
	for u in prova:1001 prova2:1002; do
		n=${u%%:*}; i=${u##*:}
		id -u "$n" >/dev/null 2>&1 || useradd -u "$i" -m -s /bin/bash "$n"
		[ -n "$GRUPPI_SCHEDA" ] && usermod -aG "$GRUPPI_SCHEDA" "$n"
	done
	printf 'prova:prova2026\nprova2:prova2026\n' | chpasswd
	ok "prova and prova2, in the groups READ FROM THE NODES: ${GRUPPI_SCHEDA:-none}"

	# -------------------------------------------------------------------
	# ⭐⭐ AND ALL THE PEOPLE ALREADY ON THE MACHINE — decided by the user on 20
	#     September 2026: "the installation procedure adds the users
	#     present in the system to the video and render groups".
	#
	# ⛔ The PEOPLE, not the service accounts: `www-data`, `systemd-*` and
	#    company do not open graphical sessions, and giving them the card would be
	#    a permission given away to whoever will never use it.  ⇒ The boundary is the one
	#    the distribution uses: `UID_MIN`..`UID_MAX` of `/etc/login.defs`,
	#    READ from there and not nailed down (same rule as the groups: we ask
	#    the machine).  ⚠ `nobody` (65534) stays out by itself.
	# ⚠ Whoever is created LATER does not pass through here: that is handled by the product
	#   at the first connection (`figlio.c`, `iscrivi_ai_gruppi_della_scheda`).
	# -------------------------------------------------------------------
	if [ -n "$GRUPPI_SCHEDA" ]; then
		MIN=$(awk '$1 == "UID_MIN"  { print $2 }' /etc/login.defs 2>/dev/null)
		MAX=$(awk '$1 == "UID_MAX"  { print $2 }' /etc/login.defs 2>/dev/null)
		QUANTI=0; GIA=0
		for n in $(getent passwd | awk -F: -v a="${MIN:-1000}" -v b="${MAX:-60000}" \
		           '$3 >= a && $3 <= b && $7 !~ /(nologin|false)$/ { print $1 }'); do
			if id -nG "$n" | tr ' ' '\n' | grep -qxF "$(printf '%s' "$GRUPPI_SCHEDA" | cut -d, -f1)"; then
				GIA=$((GIA + 1))
			fi
			usermod -aG "$GRUPPI_SCHEDA" "$n" && QUANTI=$((QUANTI + 1))
		done
		ok "people of the machine in the card's groups: $QUANTI (uid ${MIN:-1000}..${MAX:-60000}, with a real shell)"
		inf "⚠ whoever is created later is enrolled by the product at the FIRST connection"
	fi

	# -------------------------------------------------------------------
	# ⛔⛔ `~/.cache` MUST BE A FOLDER OF ITS OWN, not a link to /tmp
	#
	# `[M]` 25 August 2026, task F2 — and it is the defect for which the director
	# said three times "Firefox does not work".
	#
	# `/etc/skel/.cache` of this machine is a LINK to `/tmp`.
	# ⭐⭐ AND IT IS NOT A FAULT: it is a DELIBERATE CHOICE of the user about how
	#    his operating system must work — *".cache pointing to /tmp is a
	#    deliberate choice of mine"*, 25 August 2026, `DECISIONI.md` §4.6-undecies.
	#    ⛔ So here NOTHING of the system is repaired: his choice stays.
	# ⛔ The defect is OURS: `useradd -m` copies the skeleton ⇒ the ten users
	#    we create are ALL born writing to the same place.
	# Firefox keeps the **local** profile under `$HOME/.cache/mozilla`, that is
	# under `/tmp/mozilla`.  ⛔ The FIRST user who opens the browser creates
	# `/tmp/mozilla` **in their name and with mode 0700**; from that moment no other
	# user can write there, `profiles.ini` is never born, and the browser opens
	# a window saying *"Your Firefox profile cannot be loaded"* — that is
	# **it is unusable for everyone except the first**.
	#
	# ⭐⭐ AND IT IS MULTI-TENANCY THAT MAKES IT CERTAIN, not rare: it is a
	#    defect that on a single-user machine is never seen, and that on
	#    ten users bites nine.  ⇒ It is HERE and not in the product: it is the machine
	#    that must be in order (`SPECIFICHE.md` §5.9, part A).
	#
	# `[M]` The proof, without a browser in between: from `provanic3`
	#     `mkdir -p ~/.cache/mozilla`
	#     → `Permission denied`, with `prova2`'s `/tmp/mozilla`, mode 0700.
	# `[M]` And with the remedy, headless and without REMOTIX: `profiles.ini` is born.
	#
	# ⚠ The `/tmp/mozilla` of whoever already has it is not touched: it is not ours and it is not
	#   known who uses it.  ⛔ And neither `/etc/skel` nor the user's
	#   home is touched: that is their home.  A real `~/.cache` is given ONLY
	#   to the users we create.
	# -------------------------------------------------------------------
	for u in prova prova2; do
		c="/home/$u/.cache"
		if [ -L "$c" ]; then
			rm -f "$c"
			mkdir -p "$c"
			chown "$u:$u" "$c"
			chmod 700 "$c"
			inf "⚠ $u had ~/.cache as a link: remade as a real folder"
		elif [ ! -d "$c" ]; then
			mkdir -p "$c"
			chown "$u:$u" "$c"
			chmod 700 "$c"
		fi
	done
	ok "~/.cache is a folder of each user: the browser can make its profile"

	# -------------------------------------------------------------------
	# ⛔⭐ LINGER, and it is not a convenience: it is 2.6 seconds for every login
	#
	# `[M]` 16 August 2026, measured on the log.  Without linger, the user
	# manager (`user@UID.service`, that is `systemd --user` plus the bus) DIES at
	# every logout and is REBORN at the next login.  ⇒ The child, which as the first thing
	# connects to the session bus, got stuck inside that connection:
	#
	#     without linger   2.6 s (and 13.7 s at the first round after a reboot)
	#     with linger      ⭐ 18 ms
	#
	# ⛔ And there was worse: `loginctl` showed the user in `State=closing` for
	#    tens of seconds, and two rounds out of ten waited 29 and 32 seconds
	#    for a manager that did not finish shutting down.
	#
	# ⚠ And it does NOT contradict §1.10-ter, which refused linger AS A SUBSTITUTE
	#   for the PAM session: there the problem was the class (`manager` instead of
	#   `user`), and it stays true.  ⭐ Here linger sits UNDER the PAM session, not
	#   in its place: the session of class `user` is opened by the product
	#   anyway, and linger only keeps the manager warm between one login and the next.
	# -------------------------------------------------------------------
	for u in prova prova2; do
		loginctl enable-linger "$u" >/dev/null 2>&1
	done
	ok "linger on: the user manager stays warm between one login and the next"
	inf "⚠ the groups reach the compositor only when the user manager is"
	inf "   REBORN: if you change the groups with the session alive, stop it first"

	# -------------------------------------------------------------------
	# 2. ⛔ AWAY with v1's drop-in with the extra monitor
	# -------------------------------------------------------------------
	tit "v1's drop-in with the extra monitor"
	# ⭐ PHASE 17 (fasi/17-l-installatore.md §5.1): since GNOME 50 the Shell is
	#    org.gnome.Shell@user.service, instance of the template org.gnome.Shell@.service
	#    ⇒ all three folders are checked.  ⚠ ONLY our file is removed,
	#    and the folder only if it stays empty: the template's one holds for GDM too.
	TOLTI=0
	for d in org.gnome.Shell@wayland.service.d org.gnome.Shell@user.service.d \
	         org.gnome.Shell@.service.d; do
		f=/etc/systemd/user/$d/remotix-headless.conf
		if [ -e "$f" ]; then
			rm -f "$f"
			rmdir "/etc/systemd/user/$d" 2>/dev/null || true
			ok "removed $f: v2 writes its own, without --virtual-monitor"
			TOLTI=$((TOLTI + 1))
		fi
	done
	[ "$TOLTI" -eq 0 ] && ok "it was not there"

	# -------------------------------------------------------------------
	# 3. The three belts of §4.7
	# -------------------------------------------------------------------
	tit "Nobody switches the server off (DECISIONI.md §4.7)"
	install -D -m 644 "$QUI/remotix-niente-spegnimento.rules" \
		/etc/polkit-1/rules.d/50-remotix-niente-spegnimento.rules
	rm -f /etc/polkit-1/rules.d/49-remotix-niente-spegnimento.rules
	install -D -m 644 "$QUI/remotix-tasti.conf" \
		/etc/systemd/logind.conf.d/remotix-tasti.conf
	mkdir -p /etc/systemd/sleep.conf.d
	cat > /etc/systemd/sleep.conf.d/remotix-niente-sospensione.conf <<'CONF'
# ⛔ The strongest belt of the three: here SYSTEMD refuses, not polkit, and it holds
#    for root too — `[M]` 15 Aug 2026, `CanSuspend="no"` even from root.
[Sleep]
AllowSuspend=no
AllowHibernation=no
AllowSuspendThenHibernate=no
AllowHybridSleep=no
CONF
	systemctl restart polkit >/dev/null 2>&1
	systemctl reload systemd-logind >/dev/null 2>&1 || systemctl restart systemd-logind >/dev/null 2>&1
	ok "polkit (12 actions), logind (keys), sleep.conf"

	# -------------------------------------------------------------------
	# 4. The PAM service
	# -------------------------------------------------------------------
	tit "The PAM service"
	# ⭐ PHASE 17: the PAM file excludes whoever is in /etc/remotix/utenti-negati, and
	#    with onerr=fail if the file is missing NOBODY gets in ⇒ the file first.
	#    It is not rewritten if it is there: it is a choice of whoever administers.
	if [ ! -f /etc/remotix/utenti-negati ]; then
		install -D -m 644 -o root -g root /dev/null /etc/remotix/utenti-negati
		echo root > /etc/remotix/utenti-negati
	fi
	ok "/etc/remotix/utenti-negati ($(tr '\n' ' ' < /etc/remotix/utenti-negati))"
	install -D -m 644 "$QUI/remotix.pam" /etc/pam.d/remotix
	ok "/etc/pam.d/remotix"

	# -------------------------------------------------------------------
	# 4-bis. ⛔ THE BENCHES DRIVE THE SERVICE WITHOUT STOPPING TO ASK
	#
	# ✅ Decided by the user on 18 September 2026: "put in the script".
	# `[M]` That day, first round after the break, `11-gancio.sh remoto`
	# stopped FOREVER at the first command.  It sends `sudo -S … systemctl
	# reset-failed … 2>/dev/null`: the password prompt goes to
	# standard error, standard error goes to the void, `sshpw.py` sees
	# nothing to answer, and `sudo` waits.
	# ⇒ It worked because `provision-server.sh` (§3-bis) wrote this
	#   rule, and moving to this script the rule had been LOST.
	# ⚠ Restricted to the four commands the benches really use, and `tee` to ONE
	#   file: `sudo tee` without constraints is equivalent to full `sudo`.  It lives in the
	#   rootfs in RAM: it disappears by itself at reboot.
	# -------------------------------------------------------------------
	tit "The benches drive the service without a password"
	UTENTE_BANCHI=${SUDO_USER:-nicfio}
	printf '%s ALL=(root) NOPASSWD: /usr/bin/systemctl, /usr/bin/loginctl, /usr/sbin/nft, /usr/bin/tee /etc/default/remotix\n' \
		"$UTENTE_BANCHI" > /etc/sudoers.d/remotix-banchi
	chmod 440 /etc/sudoers.d/remotix-banchi
	if visudo -c -q -f /etc/sudoers.d/remotix-banchi; then
		ok "$UTENTE_BANCHI: four commands without a password"
	else
		rm -f /etc/sudoers.d/remotix-banchi
		ko "sudoers rule not valid: removed"
	fi

	# -------------------------------------------------------------------
	# 5. ⛔ THE CARD: measurements are made on the INTEGRATED one — §4.6-quinquies
	#
	# "The tests must be done on the integrated GPU, otherwise we are rigging the game"
	# — the user, 15 August 2026.  ⚠ By PCI address and not by node
	# number: `renderD128` and `renderD129` swap between two boots.
	# -------------------------------------------------------------------
	tit "The card: the discrete one is excluded"
	DISCRETA=""
	for c in /sys/class/drm/card[0-9]; do
		[ -e "$c/device/driver" ] || continue
		drv=$(basename "$(readlink -f "$c/device/driver")")
		pci=$(basename "$(readlink -f "$c/device")")
		case "$drv" in
		amdgpu|nvidia|nouveau) DISCRETA="$pci"; inf "discrete: $drv at $pci" ;;
		*)                     inf "integrated: $drv at $pci" ;;
		esac
	done
	if [ -n "$DISCRETA" ] && [ -x /media/REMOTIX/gpu-udev.sh ]; then
		bash /media/REMOTIX/gpu-udev.sh "$DISCRETA" >/dev/null 2>&1 \
			&& ok "excluded $DISCRETA: measurements on the integrated one" \
			|| ko "the udev rule did not go in"
	elif [ -z "$DISCRETA" ]; then
		ok "a single card: nothing to exclude"
	else
		ko "/media/REMOTIX/gpu-udev.sh is missing"
	fi

	# -------------------------------------------------------------------
	# 6. ⛔⭐⭐ THE THREE REQUIREMENTS MULTI-TENANCY WANTS AND THAT WERE NOT
	#          WRITTEN ANYWHERE — 27 August 2026, measured on the
	#          real machine BY DOING the thing, not by inspecting it.
	#
	#   1. ⛔ THE SERVER MUST RUN AS **ROOT**, or multi-tenancy does not exist.
	#      `[M]` With `User=nicfio` the product itself writes «this process
	#      is uid 1000: it is NOT root — PAM will be able to check only its own
	#      user», and every other tenant gets `0x07
	#      CREDENZIALI_ERRATE`.  As root: «uid 0: it can check anyone's
	#      password with PAM».
	#   2. ⛔ THE BINARY MUST BE WHERE THE TENANT CAN EXECUTE IT.  `[M]`
	#      `/home/nicfio` is `0700`: the child, which runs with the
	#      tenant's uid, **does not traverse** that folder and exits with 37 —
	#      "could not execute the server binary".
	#   3. ⛔ `LD_LIBRARY_PATH` DOES NOT REACH THE CHILD.  `figlio.c` composes
	#      the environment **from scratch** and does `execve` (CODER.md §4.5): a library
	#      outside the system paths makes the child exit with **127**, and the
	#      parent's variable does not reach it.  ⇒ The cure is HERE, where
	#      root is needed: `/etc/ld.so.conf.d/` plus `ldconfig`.
	#
	# ⚠ Point 1 is FIXED by this script (a drop-in), points 2 and 3 are
	#   CHECKED by doing them — delivering the binary is not provisioning's job.
	# -------------------------------------------------------------------
	tit "The three requirements of multi-tenancy (27 Aug 2026)"
	if systemctl cat remotix.service >/dev/null 2>&1; then
		QUALE=$(systemctl show remotix.service -p User --value 2>/dev/null)
		if [ -n "$QUALE" ] && [ "$QUALE" != "root" ]; then
			install -d -m 755 /etc/systemd/system/remotix.service.d
			cat > /etc/systemd/system/remotix.service.d/zz-remotix-root.conf <<'CONF'
# ⛔⛔ THE SERVER RUNS AS ROOT, and it is not a convenience: it is the condition of
#     multi-tenancy.  `[M]` 27 Aug 2026: with a non-root `User=`, PAM can
#     verify the password ONLY of the service's user, and every other
#     tenant gets `0x07 CREDENZIALI_ERRATE`.
[Service]
User=root
Group=root
CONF
			systemctl daemon-reload >/dev/null 2>&1
			ok "drop-in zz-remotix-root.conf written (it was User=$QUALE)"
			inf "⚠ the service was NOT restarted: it takes effect at the next restart of the service"
		else
			ok "remotix.service already runs as root"
		fi
	else
		inf "remotix.service is not installed on this machine: nothing to correct"
	fi

	# ⭐ The libraries outside the system paths are REGISTERED, because the
	#   environment variable does not cross the child's `execve`.
	LIBRERIE=""
	for c in /opt/remotix/lib /opt/remotix/solo "$QUI/lib-remotix"; do
		[ -d "$c" ] || continue
		LIBRERIE="$c"
		break
	done
	if [ -n "$LIBRERIE" ]; then
		printf '# ⛔ `LD_LIBRARY_PATH` does not reach the child (execve with an environment from\n#    scratch): the libraries of the product are registered here.\n%s\n' \
			"$LIBRERIE" > /etc/ld.so.conf.d/zz-remotix.conf
		ldconfig
		ok "product libraries registered: $LIBRERIE (ldconfig done)"
	else
		inf "no product library folder to register"
	fi
fi

# ---------------------------------------------------------------------------
# ⭐ THE CHECK — and it is not a formality: `REVIEWER.md` E1, "written is not in
#    force".  ⚠ What can be checked from root is checked here; the rest
#    — the two Can* seen BY THE USER — is checked by the child at every session, and
#    the reason is that root gets answered "yes" because of `CAP_SYS_BOOT`.
# ---------------------------------------------------------------------------
tit "The check"

# ⭐ The binary is asked of the SERVICE, not guessed: it is the one that will really
#   run.  ⚠ If the service is not there, the tree's one is looked at.
BINARIO=$(systemctl show remotix.service -p ExecStart --value 2>/dev/null \
	| sed -n 's/.*path=\([^ ;]*\).*/\1/p' | head -1)
[ -n "$BINARIO" ] || BINARIO="$QUI/remotix"

# ⛔⭐⭐ REQUIREMENT 1 — the server must run as ROOT, or there is no multi-tenancy.
if systemctl cat remotix.service >/dev/null 2>&1; then
	QUALE=$(systemctl show remotix.service -p User --value 2>/dev/null)
	if [ -z "$QUALE" ] || [ "$QUALE" = "root" ]; then
		ok "remotix.service runs as root: PAM can verify ANYONE's password"
	else
		ko "⛔⛔ remotix.service runs as «$QUALE»: PAM will be able to verify ONLY that user, and every other tenant will get 0x07 CREDENZIALI_ERRATE"
	fi
else
	inf "remotix.service is not installed: the «as root» requirement is left to whoever launches it by hand"
fi

for n in prova prova2; do
	# ⛔⭐ THE NODE'S **GID** IS CHECKED, not the name «render».  A `grep -qw
	#     render` on `id -nG` passes even on a machine where the node
	#     belongs to another group — that is it would say OK to a tenant who
	#     will be born blind.  ⚠ And ALL the nodes' gids are looked at: `cardN` and
	#     `renderDN` have two different ones, and both are needed.
	SUOI=" $(id -G "$n" 2>/dev/null) "
	MANCA=""
	for g in $(gid_della_scheda); do
		case "$SUOI" in *" $g "*) ;; *) MANCA="${MANCA:+$MANCA }$(getent group "$g" | cut -d: -f1) (gid $g)" ;; esac
	done
	if [ -z "$(gid_della_scheda)" ]; then
		ko "⛔ no /dev/dri node: it cannot be said whether $n will see"
	elif [ -z "$MANCA" ]; then
		ok "$n is in ALL the groups of the card's nodes (${GRUPPI_SCHEDA})"
	else
		ko "⛔⛔ $n is NOT in the card's groups: $MANCA — their session WILL BE BORN BLIND (0 of 4 [M], 27 Aug 2026, phase 10 §7.4)"
		inf "   cure: usermod -aG ${GRUPPI_SCHEDA} $n  &&  loginctl terminate-user $n"
	fi
	if [ "$(loginctl show-user "$n" -p Linger --value 2>/dev/null)" = "yes" ]; then
		ok "$n has linger: the user manager is not reborn at every login"
	else
		ko "$n does NOT have linger: every login will pay 2.6 s of user manager being born"
	fi
	# ⛔ And we check that `~/.cache` is THEIRS: if it is a link to `/tmp`, the
	#    browser profile ends up in a shared folder that the first
	#    user takes with mode 0700, and from then on the browser no longer starts
	#    for anyone else.  ⚠ Looking at the link is not enough: we try
	#    to WRITE into it, because "written is not in force" (E1).
	if [ -L "/home/$n/.cache" ]; then
		ko "⛔ $n has ~/.cache as a LINK to $(readlink "/home/$n/.cache"): the browser will not make its profile"
	elif su -s /bin/sh -c "mkdir -p /home/$n/.cache/.prova-remotix && rmdir /home/$n/.cache/.prova-remotix" "$n" 2>/dev/null; then
		ok "$n can write in their ~/.cache (the browser profile fits there)"
	else
		ko "⛔ $n can NOT write in their ~/.cache: the browser will say «Profile Missing»"
	fi

	# ⛔⭐⭐ REQUIREMENTS 2 AND 3 IN A SINGLE TEST, and they are DONE instead of looked at.
	#
	#   The loader is asked to list the binary's libraries **with
	#   the tenant's uid and with the environment AT ZERO** — which is exactly the
	#   condition of the child after `figlio.c`'s `execve`.  ⇒ A single line
	#   answers both questions:
	#     · the binary cannot be traversed (home `0700`) ⇒ «Permission denied»,
	#       and it is the child's exit 37;
	#     · a library is not found ⇒ «not found», and it is exit 127.
	# ⚠ `LD_TRACE_LOADED_OBJECTS` makes it list and NOT execute: no server
	#   starts, and nothing of what is running is touched.
	if [ ! -e "$BINARIO" ]; then
		inf "⚠ $BINARIO is not there: the loader test for $n cannot be done"
	else
		ESCE=$(su -s /bin/sh -c "env -i LD_TRACE_LOADED_OBJECTS=1 '$BINARIO'" "$n" 2>&1)
		if printf '%s' "$ESCE" | grep -q 'not found'; then
			ko "⛔⛔ $n is MISSING some libraries ($(printf '%s' "$ESCE" | grep -c 'not found')): the child will exit with 127.  ⚠ LD_LIBRARY_PATH does NOT reach it: the cure is /etc/ld.so.conf.d + ldconfig"
			printf '%s' "$ESCE" | grep 'not found' | sed 's/^/        /'
		elif printf '%s' "$ESCE" | grep -qi 'permission denied\|cannot execute\|No such file'; then
			ko "⛔⛔ $n can NOT execute $BINARIO: the child will exit with 37.  ⚠ Look at the modes of the folders on the path — a 0700 home stops everything"
			printf '%s' "$ESCE" | head -2 | sed 's/^/        /'
		else
			ok "$n executes $BINARIO and resolves its libraries with the environment AT ZERO (like the child)"
		fi
	fi
done

[ -f /etc/pam.d/remotix ] && ok "/etc/pam.d/remotix is there" \
	|| ko "/etc/pam.d/remotix is missing"
grep -qx root /etc/remotix/utenti-negati 2>/dev/null && ok "root is denied (/etc/remotix/utenti-negati)" \
	|| ko "⛔ /etc/remotix/utenti-negati is missing or does not deny root"
[ -f /etc/sudoers.d/remotix-banchi ] && ok "the benches drive the service without a password" \
	|| ko "⛔ /etc/sudoers.d/remotix-banchi is missing: the remote hook will stop at the first sudo"
# ⭐ D3 (DECISIONI §10.18): the file is sshd's stack, and `pam_systemd` comes from
#    `common-session` — the REAL line is looked at (not a comment), in the file or in the included stack.
if grep -qE '^[[:space:]]*session.*pam_systemd' /etc/pam.d/remotix 2>/dev/null \
	|| { grep -qE '^@include[[:space:]]+common-session[[:space:]]*$' /etc/pam.d/remotix 2>/dev/null \
	     && grep -qE '^[[:space:]]*session.*pam_systemd' /etc/pam.d/common-session 2>/dev/null; }; then
	ok "and it reaches pam_systemd"
else
	ko "⛔ it does NOT reach pam_systemd: without it, the logind session is not born and the compositor does not start"
fi

[ -f /etc/polkit-1/rules.d/50-remotix-niente-spegnimento.rules ] && ok "the polkit rule is there" \
	|| ko "the polkit rule is missing"
grep -q 'multiple-sessions' /etc/polkit-1/rules.d/50-remotix-niente-spegnimento.rules 2>/dev/null \
	&& ok "and it covers the *-multiple-sessions (the multi-user case)" \
	|| ko "⛔ it does NOT cover the *-multiple-sessions: it fails precisely with multiple users"

VIG=$(systemd-analyze cat-config systemd/logind.conf 2>/dev/null | grep -c '^HandlePowerKey=ignore')
[ "$VIG" -ge 1 ] && ok "the power key is ignored" \
	|| ko "the power key still switches the machine off"

# ⭐ PHASE 17: the three Shell folders (GNOME ≤ 49, GNOME 50, the template)
V1=""
for d in org.gnome.Shell@wayland.service.d org.gnome.Shell@user.service.d \
         org.gnome.Shell@.service.d; do
	[ -e "/etc/systemd/user/$d/remotix-headless.conf" ] && V1="$V1 $d"
done
[ -n "$V1" ] && ko "⛔ v1's drop-in with --virtual-monitor is still there:$V1" \
	|| ok "no v1 drop-in"

echo
if [ "$ESITO" -eq 0 ]; then
	echo "⭐ the machine is in the state the product expects."
else
	echo "⛔ something is not right: read the NOs above."
fi
exit "$ESITO"
