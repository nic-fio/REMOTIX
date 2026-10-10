#!/bin/bash
#
# 17-t10.sh — phase 17, T10: the WHOLE round of §7.3 on one machine of the matrix, with the single
# package of a real release (packaging/rilascio.sh: remotix-X.Y.Z-R.run), as the administrator would
# use it. Redone on 10 Oct 2026 for the installer of DECISIONI §10.36: no repository, no answer
# file; REMOTIX does not modify the system and what is missing is put in by the administrator.
#
#   (on the server, as nicfio)   sg kvm -c 'bash 17-t10.sh <host> [client|iso|container_box]'
#     e.g. bash 17-t10.sh fedora44-kde           (photo «cliente», the machine <distro>-<desktop>)
#          bash 17-t10.sh debian13-gnome iso     (photo «iso», the machine <distro>-<desktop>-iso)
#          bash 17-t10.sh debian13-kde container_box   (the BOX with the real card: scatole/17-scatola.sh,
#                                                 with valid sudo; the machine <distro>-<desktop>-container_box)
#
# ⭐ «scatola» (1 Oct 2026): the SAME script runs in a container with the server's card (§7.5);
#   only who turns the machine on changes (scatole/17-scatola.sh, the same verbs as 17-vm.sh), and
#   step 4 is the reboot OF THE CONTAINER, stated. ⚠ Since phase 19 REMOTIX wants a card that
#   encodes: in a VM the preflight check refuses it (RX-GPU-*), so the real round is in a box.
#
# The two releases: $T10/run-N.run and run-N1.run (with their .sha256 alongside), copied into the machine.
#
# The script (fasi/17 §7.3), one step after the other, and every step with its evidence:
#   0. photo; power on; the person «prova» (already in the group of the card node: R33), their ssh key;
#      the .run N inside, `sha256sum -c`, `sh remotix-N.run check` (what is missing: it is written down),
#      then THE ADMINISTRATOR prepares the machine (17-amministratore.sh: third-party repositories,
#      drivers, desktop pieces, port in the firewall), and `check` again: nothing must be missing any more;
#   1. «prima» fingerprint (17-t3-impronta*.sh of the family) — AFTER the administrator's preparation;
#   2. INSTALL: `sudo sh remotix-N.run install --port … --users prova`, and to the question «Proceed?»
#      it answers «y» from stdin, like a person ⇒ operation CONFIRMED, `remotix-install status`
#      GREEN, the service listening; libraries seen with the uid of «prova» (R4);
#   3. a REAL browser (Chrome) gets in and sees the desktop (17-t1c-guarda.sh);
#   4. real REBOOT of the machine (boot_id), and back in with the browser (R15);
#   5. UPDATE to N+1: the .run N+1 run again (sh remotix-N1.run install, «y»), a browser stays
#      connected (t8-browser.py); the stage (pid) before and after must match (R7), the browser
#      gets back in and sees the desktop again (R10), the version is N+1, status again;
#   6. UNINSTALL (uninstall --purge, «y») with an ssh session of «prova» writing the time every
#      second (R43); «dopo» fingerprint and comparison with «prima» (R6): only the lines naming
#      REMOTIX and the groups of «prova» are looked at; and ~/.local/state/remotix/sessione.log, which
#      was there after the browser, is NO longer in any home (user's decision, 1 Oct 2026);
#   7. shuts down and puts the photo back (even if the test falls).
# Result: one line `T10 <host> <state> PASS|FAIL steps…` at the bottom of outcomes/<m>/esito.txt and in
# t10/giro.log. Evidence in /media/REMOTIX/vm17/t10/esiti/<host>[-iso]/.
# ⛔ At most 4 VMs on in all; it does not touch a machine already turned on by others. Every machine has
#   ITS OWN labwc for the browser (T1C=t10/t1c/<host>): four rounds together do not cover each other.
set -uo pipefail
m0=${1:?machine}; state=${2:-client}
BOX=""
case $state in client) m=$m0; picture=client ;; iso) m=$m0-iso; picture=iso ;; container_box) m=$m0-scatola; picture=client; BOX=1 ;; *) echo "state: client | iso | container_box"; exit 2 ;; esac
R=/media/REMOTIX/vm17
T10=${T10:-$R/t10}
E=$T10/outcomes/$m
HERE=$(cd "$(dirname "$0")" && pwd)
RUN_N=${RUN_N:-$T10/run-N.run}; RUN_N1=${RUN_N1:-$T10/run-N1.run}
if [ -n "$BOX" ]; then
	# the box: the verbs of 17-vm.sh from scatole/17-scatola.sh, the machine is named as in the VM
	V="bash ${BOXES:-$HERE/scatole}/17-scatola.sh"; MV=$m0
else
	V="bash $R/17-vm.sh"; MV=$m
fi
PASSWORD=${REMOTIX_TEST_PASSWORD:-prova2026}
FINGERPRINT=17-t3-impronta.sh; FAM=debian
case $m0 in
debian13-*) n=1;; ubuntu2604-*) n=2;;
fedora44-*) n=3; FINGERPRINT=17-t3-impronta-rpm.sh; FAM=fedora;;
arch-*) n=4; FINGERPRINT=17-t3-impronta-arch.sh; FAM=arch;;
tumbleweed-*) n=5; FINGERPRINT=17-t3-impronta-rpm.sh; FAM=suse;;
leap16-*) n=6; FINGERPRINT=17-t3-impronta-rpm.sh; FAM=suse;;
alma10-*) n=7; FINGERPRINT=17-t3-impronta-rpm.sh; FAM=fedora;;
*) echo "unknown machine: $m0"; exit 2;;
esac
k=0; case ${m0#*-} in gnome) k=1;; kde) k=2;; xfce) k=3;; lxqt) k=4;; esac
[ "$state" = iso ] && k=5
PSSH=$((2300 + 10 * n + k)); PRX=$((7500 + 10 * n + k)); PG=7447   # PG: the port INSIDE the machine
if [ -n "$BOX" ]; then read -r PSSH PRX < <($V ports "$MV") || exit 2; PG=$PRX; fi
CH=$R/ssh/id_ed25519
O="-i $CH -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
vm() { $V ssh "$MV" "$@"; }
t() { date -u +%H:%M:%S; }
say() { printf '%s %s\n' "$(t)" "$*" | tee -a "$E/giro.log"; }
STEPS=""
outcome_step() { STEPS="$STEPS $1=$2"; say "   ⇒ $1: $2"; }
fingerprint() { vm 'sudo bash -s' <"$R/t4/$FINGERPRINT" >"$E/impronta-$1.txt" 2>"$E/impronta-$1.err"
             say "   fingerprint «$1»: $(wc -l <"$E/impronta-$1.txt") lines"; }
FINALE=FAIL
fine() {
	[ -n "${CLOCK:-}" ] && kill "$CLOCK" 2>/dev/null
	[ -n "${BROWSER:-}" ] && kill "$BROWSER" 2>/dev/null
	# this machine's labwc
	[ -f "$T1C/labwc.pid" ] && kill "$(cat "$T1C/labwc.pid")" 2>/dev/null
	if [ -n "${LEAVE:-}" ]; then
		say "==> LEAVE=1: the VM $m stays ON for diagnosis (then: 17-vm.sh halt $m; returns $m $picture)"
		row="T10 $m $state $FINALE$STEPS"; echo "$row" | tee -a "$E/esito.txt" >>"$T10/giro.log"; echo "$row"; return
	fi
	say "==> shutting down and putting back the photo «$picture»"
	$V halt "$MV" >/dev/null 2>&1; $V returns "$MV" "$picture" >/dev/null 2>&1
	row="T10 $m $state $FINALE$STEPS"
	echo "$row" | tee -a "$E/esito.txt" >>"$T10/giro.log"
	echo "$row"
}

rm -rf "$E"; mkdir -p "$E" "$T10/t1c"; : >"$E/giro.log"
T1C=$T10/t1c/$m; mkdir -p "$T1C"
if [ -z "$BOX" ]; then
	if pgrep -f "qemu-system.*-name rx-$m " >/dev/null; then echo "⛔ $m is already on: someone else is using it"; exit 2; fi
	[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { echo "⛔ already 4 VMs on"; exit 2; }
fi
for x in "$RUN_N" "$RUN_N1"; do
	[ -s "$x" ] && [ -s "$x.sha256" ] || { echo "⛔ $x (or its .sha256) is missing: the two .run files of packaging/rilascio.sh"; exit 2; }
done
trap fine EXIT
# port: the .run and its sha256 into the machine, with the release name (sha256sum -c wants it)
port_run() {
	local n; n=$(awk '{print $2}' "$1.sha256")
	vm "cat > /tmp/$n" <"$1" && vm "cat > /tmp/$n.sha256" <"$1.sha256" && echo "$n"
}

say "==> 0. $m: photo «$picture», power on (ssh :$PSSH, REMOTIX :$PRX${BOX:+ — BOX with the real card})"
$V returns "$MV" "$picture" >/dev/null || exit 1
$V start "$MV" >"$E/avvia.log" 2>&1 || { tail -5 "$E/avvia.log"; exit 1; }
vm "id -u prova >/dev/null 2>&1 || sudo useradd -m -s /bin/bash prova
echo 'prova:$PASSWORD' | sudo chpasswd
G=\$(for x in /dev/dri/card[0-9]*; do [ -e \$x ] && getent group \$(stat -c %g \$x) | cut -d: -f1; done | sort -u | head -1)
[ -n \"\$G\" ] && sudo gpasswd -a prova \"\$G\" >/dev/null
sudo install -d -m 700 -o prova -g prova ~prova/.ssh
sudo install -m 600 -o prova -g prova ~/.ssh/authorized_keys ~prova/.ssh/authorized_keys
. /etc/os-release; echo \"\$PRETTY_NAME · \$(uname -r) · selinux: \$(getenforce 2>/dev/null || echo -)\"
ls -l /dev/dri/ | grep -c card; id prova" >"$E/macchina.txt" 2>&1
sed 's/^/   /' "$E/macchina.txt" | tee -a "$E/giro.log"
RN=$(port_run "$RUN_N") || { say "⛔ the .run N does not get into the machine"; exit 1; }
vm "cd /tmp && sha256sum -c $RN.sha256 && sh $RN version" >"$E/run-N.txt" 2>&1 || { cat "$E/run-N.txt" | tee -a "$E/giro.log"; exit 1; }
say "   $(tail -1 "$E/run-N.txt")"
vm "cd /tmp && sh $RN check" >"$E/check-prima.txt" 2>&1
say "   check before the preparation: exit $?; missing: $(sed -n '/^MISSING/,/^$/p' "$E/check-prima.txt" | grep -oE 'RX-[A-Z]+-[0-9]+[^[]*' | tr '\n' ' ' | cut -c1-300)"
say "==> 0b. the ADMINISTRATOR prepares the machine (17-amministratore.sh: §10.36, REMOTIX does not do it)"
vm "sudo bash -s $m0 $PG" <"$HERE/17-amministratore.sh" >"$E/amministratore.txt" 2>&1
grep -E '^\+ ' "$E/amministratore.txt" | cut -c1-200 | sed 's/^/   /' | tee -a "$E/giro.log"
vm "cd /tmp && sh $RN check" >"$E/check-dopo.txt" 2>&1; u=$?
if [ $u = 0 ] && ! grep -q '^MISSING' "$E/check-dopo.txt"; then
	outcome_step prepare PASS
else
	say "   check after the preparation: exit $u"; sed -n '/^MISSING/,/^$/p' "$E/check-dopo.txt" | sed 's/^/   /' | tee -a "$E/giro.log"
	outcome_step prepare FAIL; exit 1
fi

say "==> 1. «before» fingerprint"
fingerprint before
vm "id prova" >"$E/gruppi-prima.txt"

say "==> 2. install as the administrator: sudo sh $RN install, and «y» to the question"
T0=$(date +%s)
vm "cd /tmp && printf 'y\\n' | sudo sh $RN install --port $PG --users prova" >"$E/installa.txt" 2>&1
u=$?
OP=$(grep -E '^operation ' "$E/installa.txt" | tail -1)
say "   install: exit $u in $(( $(date +%s) - T0 )) s — $OP"
grep -E 'FAILED|BLOCKED|REFUSED|RX-|MISSING|C-' "$E/installa.txt" | head -12 | cut -c1-240 | sed 's/^/   /' | tee -a "$E/giro.log"
vm "echo \"packages: \$( (dpkg-query -W -f='\${Package}=\${Version} ' remotix remotix-install 2>/dev/null; rpm -q remotix remotix-install remotix-selinux 2>/dev/null; pacman -Q remotix remotix-install 2>/dev/null) | tr '\n' ' ')\"
echo \"service: \$(systemctl is-enabled remotix 2>&1) \$(systemctl is-active remotix 2>&1) · pid \$(systemctl show -p MainPID --value remotix) · listening on $PG: \$(sudo ss -Htulpn | grep -c ':$PG ')\"
id prova
B=\$(ls /usr/libexec/remotix/remotix /usr/lib/remotix/remotix 2>/dev/null | head -1); echo \"R4 libraries not found (uid prova): \$(sudo -u prova ldd \$B 2>&1 | grep -c 'not found') · libav in the binary: \$(ldd \$B | grep -c 'libav\|libswscale')\"
echo --- status:; sudo /usr/bin/remotix-install status 2>&1; echo \"certify: exit \$?\"
echo --- startup log:; sudo journalctl -u remotix.service --no-pager -b 2>/dev/null | grep -aE 'codec offered|OpenH264|ready|RX-|⛔' | tail -6 | cut -c1-200" >"$E/installato.txt" 2>&1
sed 's/^/   /' "$E/installato.txt" | tee -a "$E/giro.log" >/dev/null
grep -E 'packages:|service:|R4 |Certification|certify: exit|codec offered' "$E/installato.txt" | cut -c1-200 | sed 's/^/   /' | tee -a "$E/giro.log"
# with the real card the expected certification is GREEN: every check PASS, no condition
certify_ok() { grep -q 'Certification of .*: GREEN' "$1" && ! grep -qE '^  (FAIL|UNKNOWN) ' "$1" && ! grep -qE '^  C-' "$1"; }
if [ $u = 0 ] && echo "$OP" | grep -qE 'CONFIRMED' && certify_ok "$E/installato.txt" && grep -q 'service: enabled active' "$E/installato.txt" && grep -q "listening on $PG: [1-9]" "$E/installato.txt" && grep -q 'not found (uid prova): 0' "$E/installato.txt"; then
	outcome_step install PASS
else
	outcome_step install FAIL; exit 1
fi

say "==> 3. the real browser (Chrome) on 127.0.0.1:$PRX"
T1C=$T1C T1C_EVIDENCE=$E/browser-1 bash "$R/t1c/17-t1c-guarda.sh" "$m" "$PRX" chrome >"$E/browser-1.log" 2>&1
say "   exit $? — $(grep -E '^T1C ' "$E/browser-1.log" | cut -c1-300)"
if grep -E '^T1C ' "$E/browser-1.log" | grep -q '"outcome": *"PASS"'; then outcome_step browser PASS; else outcome_step browser FAIL; vm "sudo journalctl -u remotix --no-pager -b | tail -40" >"$E/journal-browser-1.txt" 2>&1; exit 1; fi

if [ -n "$BOX" ]; then say "==> 4. reboot OF THE CONTAINER (the real reboot of the machine is not tested in a box: §7.5), and back in"
else say "==> 4. real reboot of the machine (R15), and back in"; fi
RX_VM_RESTART_S=${RX_VM_RESTART_S:-600} $V relaunch "$MV" >"$E/riavvia.log" 2>&1 || { tail -3 "$E/riavvia.log" | tee -a "$E/giro.log"; outcome_step restart FAIL; exit 1; }
grep -E 'rebooted' "$E/riavvia.log" | tail -1 | cut -c1-200 | sed 's/^/   /' | tee -a "$E/giro.log"
vm "echo \"service: \$(systemctl is-active remotix 2>&1) · listening on $PG: \$(sudo ss -Htulpn | grep -c ':$PG ')\"" | tee -a "$E/giro.log"
T1C=$T1C T1C_EVIDENCE=$E/browser-2 bash "$R/t1c/17-t1c-guarda.sh" "$m" "$PRX" chrome >"$E/browser-2.log" 2>&1
say "   exit $? — $(grep -E '^T1C ' "$E/browser-2.log" | cut -c1-300)"
if grep -E '^T1C ' "$E/browser-2.log" | grep -q '"outcome": *"PASS"'; then outcome_step restart PASS; else outcome_step restart FAIL; vm "sudo journalctl -u remotix --no-pager -b | tail -40" >"$E/journal-browser-2.txt" 2>&1; exit 1; fi

say "==> 5. update to N+1: the .run N+1 run again, a browser stays connected"
RN1=$(port_run "$RUN_N1") || { say "⛔ the .run N+1 does not get into the machine"; outcome_step do_update FAIL; exit 1; }
rm -rf "$E/browser-agg"; mkdir -p "$E/browser-agg"
T1C=$T1C T1C_PROGRAM=$R/t8/t8-browser.py T1C_EVIDENCE=$E/browser-agg \
	setsid nohup bash "$R/t1c/17-t1c-guarda.sh" "$m" "$PRX" chrome >"$E/browser-agg.log" 2>&1 </dev/null &
BROWSER=$!
for _ in $(seq 1 150); do [ -f "$E/browser-agg/ready" ] && break; grep -q '^T8 ' "$E/browser-agg.log" && break; sleep 1; done
if [ -f "$E/browser-agg/ready" ]; then say "   connected: the desktop is visible"; else say "   ⛔ the browser does not connect: $(tail -2 "$E/browser-agg.log" | cut -c1-200)"; outcome_step do_update FAIL; exit 1; fi
stage() { vm "for p in gnome-shell kwin_wayland plasmashell labwc xfce4-session lxqt-session; do for x in \$(pgrep -u prova -x \$p); do echo \"\$p \$x\"; done; done | sort"; }
stage >"$E/palco-prima.txt"
say "   stage before: $(tr '\n' ' ' <"$E/palco-prima.txt")"
T0=$(date +%s)
vm "cd /tmp && sha256sum -c $RN1.sha256 && printf 'y\\n' | sudo sh $RN1 install; echo \"update: exit \$?\"
echo --- remotix.service from the journal:
sudo journalctl -u remotix.service --since @$T0 --no-pager -o short-unix 2>/dev/null | grep -aE 'FOUND AGAIN|ready|Stopp|Start|Reload|RX-' | tail -12 | cut -c1-200" >"$E/aggiorna.txt" 2>&1
say "   update with the .run N+1 in $(( $(date +%s) - T0 )) s: $(grep -E 'update: exit' "$E/aggiorna.txt")"
grep -aE 'remotix|FOUND AGAIN' "$E/aggiorna.txt" | tail -8 | cut -c1-200 | sed 's/^/   /' | tee -a "$E/giro.log"
stage >"$E/palco-dopo.txt"
say "   stage after: $(tr '\n' ' ' <"$E/palco-dopo.txt")"
touch "$E/browser-agg/via"
for _ in $(seq 1 300); do grep -q '^T8 ' "$E/browser-agg.log" && break; sleep 1; done
BROWSER=
say "   $(grep '^T8 ' "$E/browser-agg.log" | cut -c1-400)"
vm "echo \"packages: \$( (dpkg-query -W -f='\${Package}=\${Version} ' remotix remotix-install 2>/dev/null; rpm -q remotix remotix-install 2>/dev/null; pacman -Q remotix remotix-install 2>/dev/null) | tr '\n' ' ')\"
echo \"service: \$(systemctl is-active remotix 2>&1) · pid \$(systemctl show -p MainPID --value remotix)\"
sudo /usr/bin/remotix-install version
sudo sh -c '/usr/bin/remotix-install status >/tmp/c.txt 2>&1'; echo \"certify: exit \$?\"; sudo cat /tmp/c.txt" >"$E/aggiornato.txt" 2>&1
grep -E 'packages:|service:|Certification|certify: exit' "$E/aggiornato.txt" | cut -c1-200 | sed 's/^/   /' | tee -a "$E/giro.log"
if grep -q 'update: exit 0' "$E/aggiorna.txt" && grep -E '^T8 ' "$E/browser-agg.log" | grep -q '"outcome": *"PASS"' && cmp -s "$E/palco-prima.txt" "$E/palco-dopo.txt" && [ -s "$E/palco-prima.txt" ] && grep -q "packages:.*${VERSION_N1:-NON_DATA}" "$E/aggiornato.txt" && certify_ok "$E/aggiornato.txt"; then
	outcome_step do_update PASS
else
	outcome_step do_update FAIL
	UPDATE_FAIL=1
fi

say "==> 6. uninstall --purge, with an ssh session of «prova» writing the time (R43)"
# shellcheck disable=SC2086
ssh $O -p "$PSSH" prova@127.0.0.1 'while :; do date +%s >> ~/orologio.txt; sleep 1; done' &
CLOCK=$!
sleep 4
vm "loginctl list-sessions --no-legend" >"$E/sessioni-prima.txt" 2>&1
# the session logs in the homes, BEFORE: the browser left one to «prova» (sessione.c)
vm "sudo find /root /home -path '*/.local/state/remotix*' 2>/dev/null | sort" >"$E/registri-prima.txt" 2>&1
say "   session logs in the homes before: $(tr '\n' ' ' <"$E/registri-prima.txt")"
T0=$(date +%s)
vm "printf 'y\\n' | sudo /usr/bin/remotix-install uninstall --purge" >"$E/disinstalla.txt" 2>&1
u=$?
OPD=$(grep -E '^operation '"$E/disinstalla.txt" | tail -1)
say "   uninstall: exit $u in $(( $(date +%s) - T0 )) s — $OPD"
grep -E 'FAILED|BLOCKED|RX-|sessione.log' "$E/disinstalla.txt" | head -8 | cut -c1-240 | sed 's/^/   /' | tee -a "$E/giro.log"
sleep 3
vm "sudo find /root /home -path '*/.local/state/remotix*' 2>/dev/null | sort" >"$E/registri-dopo.txt" 2>&1
say "   session logs in the homes after: $(tr '\n' ' ' <"$E/registri-dopo.txt")(none = good)"
vm "a=\$(sudo tail -1 ~prova/orologio.txt); sleep 3; b=\$(sudo tail -1 ~prova/orologio.txt); echo \"R43 ssh clock: \$a → \$b\"
echo \"sessions: \$(loginctl list-sessions --no-legend | grep -c prova) of prova · desktops of prova: \$(pgrep -u prova -c -x 'gnome-shell|kwin_wayland|labwc|plasmashell|lxqt-panel|xfce4-panel')\"
echo \"packages left: \$( (dpkg-query -W -f='\${Package} ' 'remotix*' 2>/dev/null; rpm -qa 'remotix*' 2>/dev/null; pacman -Qq 2>/dev/null | grep remotix) | tr '\n' ' ')\"
echo \"service: \$(systemctl is-active remotix 2>&1) · listening on $PG: \$(sudo ss -Htulpn | grep -c ':$PG ') · /var/lib/remotix: \$(sudo ls -A /var/lib/remotix 2>&1 | tr '\n' ' ')\"
echo \"remotix repositories (must be 0: §10.36): \$(ls /etc/apt/sources.list.d /etc/yum.repos.d /etc/zypp/repos.d 2>/dev/null | grep -ci remotix) · pacman.conf: \$(grep -c remotix /etc/pacman.conf 2>/dev/null)\"
id prova" >"$E/dopo.txt" 2>&1
sed 's/^/   /' "$E/dopo.txt" | tee -a "$E/giro.log"
kill "$CLOCK" 2>/dev/null; CLOCK=
vm "sudo rm -f ~prova/orologio.txt"
fingerprint after
diff "$E/impronta-prima.txt" "$E/impronta-dopo.txt" >"$E/diff-R6.txt"
# R6: the DIRECT REMOTIX lines left; the groups of «prova» as before (R33); the rest (caches,
# folder times, gpasswd copies) is read in the diff and stated.
# ⛔ `/var/lib/remotix` excluded (the engine's HISTORY: the `plans`/`operations` folder of the uninstall
#    operation IN PROGRESS cannot be removed while it runs — expected DIRECT leftover, as in T5,
#    §13.1 line 56c93d3; `--purge` removes the rest). A remotix leftover OUTSIDE of there is a real red.
#    `~/.local/state/remotix/sessione.log` is NO longer an exception (user's decision, 1 Oct 2026):
#    the engine removes it, and it is checked above (registri-prima/after) — the homes are not in the fingerprint.
grep -E '^[<>]' "$E/diff-R6.txt" | grep -i 'remotix' | grep -vE 'journal|/var/cache|/var/log|/var/lib/remotix' >"$E/diff-R6-remotix.txt"
# the DOCUMENTED leftover (the engine's history): stated, not red
grep -E '^[<>]' "$E/diff-R6.txt" | grep -iE '/var/lib/remotix' >"$E/diff-R6-attesi.txt" || true
G1=$(sed 's/.*groups=//' "$E/gruppi-prima.txt"); G2=$(grep '^uid=' "$E/dopo.txt" | sed 's/.*groups=//')
say "   R6: $(grep -c '^[<>]' "$E/diff-R6.txt") different lines, of which $(wc -l <"$E/diff-R6-remotix.txt") remotix leftovers NOT expected, $(wc -l <"$E/diff-R6-attesi.txt") expected (engine's history); groups of prova before «$G1» after «$G2»"
a=$(grep 'R43 ssh clock' "$E/dopo.txt" | sed 's/.*: //'); a1=${a%% →*}; a2=${a##*→ }
if [ $u = 0 ] && echo "$OPD" | grep -q 'CONFIRMED' && [ -z "$(grep 'packages left:' "$E/dopo.txt" | cut -d: -f2 | tr -d ' ')" ] && [ "$a1" != "$a2" ] && grep -q 'desktops of prova: 0' "$E/dopo.txt" && [ "$G1" = "$G2" ] && [ ! -s "$E/diff-R6-remotix.txt" ] && grep -q 'sessione.log' "$E/registri-prima.txt" && [ ! -s "$E/registri-dopo.txt" ]; then
	outcome_step uninstall PASS
else
	outcome_step uninstall FAIL
	DIS_FAIL=1
fi
[ -z "${UPDATE_FAIL:-}${DIS_FAIL:-}" ] && FINALE=PASS
exit 0
