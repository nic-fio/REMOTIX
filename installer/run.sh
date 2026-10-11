#!/bin/sh
# REMOTIX — the single installation file (DECISIONS §10.36, phases/17-the-installer.md).
#
#     sudo sh remotix-VERSION.run            install REMOTIX (or upgrade it to this version)
#     sh remotix-VERSION.run check           examine the machine: what REMOTIX can do, what is missing
#     sudo sh remotix-VERSION.run tui        the same installation in a text interface
#
# This header is packaging/release.sh's: below the __PAYLOAD__ line there is a tar.gz with the
# installation engine (remotix-install), LICENSE.md (the REMOTIX licence), THIRD-PARTY-LICENSES (the licences of the third-party
# components inside) and the REMOTIX packages of every supported distribution (packages/<target>/). Nothing is added to the system's repositories: the package manager installs
# those files, and takes their dependencies from the repositories the machine already has.
# REMOTIX does not change the system: what is missing is said, and providing it is up to the administrator.
set -eu
VERSION=''
PAYLOAD_SHA256=''

error() { echo "remotix: $*" >&2; exit 1; }

command=${1:-install}
[ $# -gt 0 ] && shift
case $command in
install | tui) [ "$(id -u)" -eq 0 ] || error "run it as administrator: sudo sh $0 $command" ;;
check) ;;
version) echo "REMOTIX $VERSION"; exit 0 ;;
*) error "usage: sudo sh $0 [install|check|tui] [--port N]" ;;
esac
for p in tar gzip sha256sum awk mktemp; do
	command -v "$p" >/dev/null 2>&1 || error "$p is missing"
done
line=$(awk '/^__PAYLOAD__$/ { print NR + 1; exit 0 }' "$0")
[ -n "$line" ] || error "$0: the file is damaged (no payload): download it again"
dir=$(mktemp -d /var/tmp/remotix-run.XXXXXX)
trap 'rm -rf "$dir"' EXIT INT TERM
tail -n +"$line" "$0" >"$dir/payload.tar.gz"
if [ -n "$PAYLOAD_SHA256" ]; then
	echo "$PAYLOAD_SHA256  $dir/payload.tar.gz" | sha256sum -c --status - ||
		error "$0: the file is damaged (sha256 does not match): download it again"
fi
tar -xzf "$dir/payload.tar.gz" -C "$dir"
rm -f "$dir/payload.tar.gz"
code=0
case $command in
install | tui) "$dir/remotix-install" "$command" --bundle "$dir/packages" "$@" || code=$? ;;
check) "$dir/remotix-install" check "$@" || code=$? ;;
esac
exit $code
__PAYLOAD__
