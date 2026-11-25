#!/usr/bin/env bash
# build-rpm.sh — builds REMOTIX's RPM for Fedora 45 on the `costruzione` VM (no containers).
#
#     build/build-rpm.sh [label]
#
# Run it on the machine that has the tree and ssh access to the server `nicfio@192.168.0.2` (the tablet does NOT compile: all the work
# happens in the VM).  The VM must be on: `vm-radeon.sh accendi costruzione virtuale` (the script does not start or stop it).
#
# What it does:
#   1. copies the tree (src/, rpm/, LICENSE.md, THIRD-PARTY-LICENSES) to the VM, in a scratch folder ~/rpmwork/<label>;
#   2. installs the build dependencies there (dnf builddep from the spec, plus cmake/ninja/git for the static QUIC libraries);
#   3. builds static ngtcp2 1.25.0 / nghttp3 1.18.0 into /usr/local with build/quic-static.sh, once (skipped if already there);
#   4. runs rpmbuild -bb; checks the finished package (R13 bench not in binary, R4 ldd: nothing missing, no dynamic ngtcp2/nghttp3):
#      the script fails if a check says NO or if one of the two lines is missing;
#   5. brings the .rpm and the logs back to /media/REMOTIX-FEDORA/pacchetti/<label>/ on the server.
# <label>: only [A-Za-z0-9._-], not «.» nor «..»; if the folder on the server exists already the script stops (a previous package is
# never overwritten).  Environment (optional): RX_SERVER (default nicfio@192.168.0.2), RX_GUEST_PORT (default 2355, the guest's ssh port
# on the server).  OpenSSL: the system's openssl-devel (4.0); there is no fallback to openssl3 (it was never needed: put it back, whole,
# if it ever is).
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/.." && pwd)
LABEL=${1:-$(date +%Y%m%d-%H%M)}
case "$LABEL" in
""|.|..|*[!A-Za-z0-9._-]*) echo "label \"$LABEL\": only letters, digits, dot, underscore and dash, and not . or .." >&2; exit 2 ;;
esac
SERVER=${RX_SERVER:-nicfio@192.168.0.2}
GUESTPORT=${RX_GUEST_PORT:-2355}
OUTDIR=/media/REMOTIX-FEDORA/pacchetti/$LABEL
VERSION=$(sed -n 's/^Version:[[:space:]]*//p' "$TREE/rpm/remotix.spec")
SSHOPT=(-o BatchMode=yes -o StrictHostKeyChecking=no)
GKEY=/media/REMOTIX-FEDORA/vm-radeon/costruzione/vmkey
GSSH="ssh -o BatchMode=yes -o StrictHostKeyChecking=no -i $GKEY -p $GUESTPORT prova@127.0.0.1"
# guest <command>: a command in the VM (through the server); the whole command line is quoted once
guest() { ssh "${SSHOPT[@]}" "$SERVER" "export TERM=dumb; $GSSH $(printf '%q' "$*")"; }
WORK="~/rpmwork/$LABEL"
SUDO='echo prova2026 | sudo -S -p ""'   # the VM's own test user (password of the bench)

# the parent folder only (never the label's: its existence is the check below)
ssh "${SSHOPT[@]}" "$SERVER" "mkdir -p /media/REMOTIX-FEDORA/pacchetti" || exit 2
# never overwrite a previous package
if ssh "${SSHOPT[@]}" "$SERVER" "test -e '$OUTDIR'"; then
	echo "$OUTDIR exists already on the server: choose another label (a previous package is never overwritten)" >&2
	exit 2
fi

stage=$(mktemp -d "${TMPDIR:-/tmp}/rx-rpm.XXXXXX") || exit 2
trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/remotix-$VERSION"
cp -a "$TREE/src" "$TREE/LICENSE.md" "$TREE/THIRD-PARTY-LICENSES" "$stage/remotix-$VERSION/"
[ -d "$TREE/selinux" ] && cp -a "$TREE/selinux" "$stage/remotix-$VERSION/selinux"
# leftovers of a local build must not enter the package
rm -f "$stage/remotix-$VERSION/src/remotix" "$stage/remotix-$VERSION/src"/*.o "$stage/remotix-$VERSION/src"/*-protocol.c "$stage/remotix-$VERSION/src"/*-client-protocol.h
tar -C "$stage" -czf "$stage/remotix-$VERSION.tar.gz" "remotix-$VERSION"
mkdir -p "$stage/pack"
cp "$stage/remotix-$VERSION.tar.gz" "$TREE/rpm"/* "$stage/pack/"
cp "$HERE/quic-static.sh" "$stage/pack/"

echo "== guest"
hn=$(guest hostname) || { echo "the build VM does not answer (is it on?)" >&2; exit 2; }
case "$hn" in rx-costruzione) echo "   $hn" ;; *) echo "unexpected guest name: $hn" >&2; exit 2 ;; esac
guest "rm -rf $WORK && mkdir -p $WORK" || exit 1
tar -C "$stage/pack" -cf - . | ssh "${SSHOPT[@]}" "$SERVER" "$GSSH 'tar -C $WORK -xf -'" || { echo "copy failed" >&2; exit 1; }

echo "== dependencies"
guest "$SUDO dnf -y install cmake ninja-build git gcc-c++ rpm-build selinux-policy-devel >$WORK/dnf.log 2>&1 && $SUDO dnf -y builddep $WORK/remotix.spec >>$WORK/dnf.log 2>&1" \
	|| { echo "dnf failed (see $WORK/dnf.log in the guest)" >&2; guest "tail -20 $WORK/dnf.log" >&2; exit 1; }

echo "== static ngtcp2/nghttp3"
if ! guest 'test "$(PKG_CONFIG_PATH=/usr/local/lib/pkgconfig pkg-config --modversion libngtcp2 2>/dev/null)" = 1.25.0 && test "$(PKG_CONFIG_PATH=/usr/local/lib/pkgconfig pkg-config --modversion libnghttp3)" = 1.18.0 && test -f /usr/local/lib/libngtcp2_crypto_ossl.a'; then
	guest "$SUDO sh $WORK/quic-static.sh >$WORK/quic.log 2>&1" \
		|| { echo "quic-static failed (see $WORK/quic.log in the guest)" >&2; guest "tail -30 $WORK/quic.log" >&2; exit 1; }
fi

echo "== rpmbuild"
SRCS="remotix-$VERSION.tar.gz remotix.service remotix.sysusers remotix.tmpfiles remotix.conf denied-users remotix-no-suspend.conf needrestart.conf remotix.firewalld.xml org.kde.remotix.desktop"
guest "mkdir -p ~/rpmbuild/SOURCES ~/rpmbuild/SPECS && cd $WORK && cp $SRCS ~/rpmbuild/SOURCES/ && cp remotix.spec ~/rpmbuild/SPECS/ && cd ~/rpmbuild && rm -rf RPMS && rpmbuild -bb SPECS/remotix.spec >$WORK/rpmbuild.log 2>&1" \
	|| { echo "rpmbuild failed (see $WORK/rpmbuild.log in the guest)" >&2; guest "tail -40 $WORK/rpmbuild.log" >&2; exit 1; }

echo "== checks"
# the two lines R13 and R4 must be there and say SI: a failure of rpm2cpio or of ldd leaves a line missing, which fails here
guest "cd ~/rpmbuild/RPMS && rpm=\$(ls */remotix-*.rpm | head -1) && {
  d=\$(mktemp -d) && rpm2cpio \$rpm | (cd \$d && cpio -idm 2>/dev/null)
  bin=\$d/usr/libexec/remotix/remotix
  if [ -x \$bin ]; then
    n=\$(strings \$bin | grep -c 'the BENCH FUNCTION is ON')
    [ \"\$n\" = 0 ] && echo 'R13 bench-in-binary SI (none)' || echo 'R13 bench-in-binary NO'
    l=\$(ldd \$bin)
    if echo \"\$l\" | grep -q 'not found'; then echo 'R4 ldd NO (not found)'
    elif echo \"\$l\" | grep -qE 'ngtcp2|nghttp3'; then echo 'R4 ldd NO (dynamic ngtcp2/nghttp3)'
    else echo \"R4 ldd SI (\$(echo \"\$l\" | wc -l) libraries)\"; fi
    echo \"linked: \$(echo \"\$l\" | grep -E 'libssl|libcrypto' | tr '\n' ' ')\"
  else echo 'R13 NO (binary not found in the package)'; echo 'R4 NO (binary not found in the package)'; fi
  echo Requires:; rpm -qpR \$rpm; echo Recommends:; rpm -qp --recommends \$rpm; echo Provides:; rpm -qp --provides \$rpm
  echo Files:; rpm -qpl \$rpm; rm -rf \$d; } >$WORK/controlli.txt 2>&1"
ctl=$(guest "cat $WORK/controlli.txt") || { echo "could not read the checks" >&2; exit 1; }
printf '%s\n' "$ctl" | grep -E '^(R13|R4|linked:)'
rc=0
printf '%s\n' "$ctl" | grep -q '^R13 bench-in-binary SI' || { echo "R13 line missing or NO" >&2; rc=1; }
printf '%s\n' "$ctl" | grep -q '^R4 ldd SI' || { echo "R4 line missing or NO" >&2; rc=1; }
printf '%s\n' "$ctl" | grep -qE '^R[0-9]+ .* NO( |$)' && { echo "a check says NO" >&2; rc=1; }
[ "$rc" = 0 ] || { echo "checks FAILED: no package is brought back (it stays in the guest, ~/rpmbuild/RPMS)" >&2; exit 1; }

echo "== back to the server: $OUTDIR"
ssh "${SSHOPT[@]}" "$SERVER" "mkdir '$OUTDIR' && cd '$OUTDIR' && $GSSH 'cd ~/rpmbuild && tar -cf - RPMS' | tar -xf - && $GSSH 'cd $WORK && tar -cf - *.log controlli.txt' | tar -xf - && mv RPMS/*/*.rpm . && rmdir RPMS/* RPMS && ls -l" || { echo "bringing the package back failed" >&2; exit 1; }
exit 0
