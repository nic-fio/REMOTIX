#!/bin/sh
# REMOTIX — the single installation file (DECISIONS §10.36, fasi/17-l-installatore.md).
#
#     sudo sh remotix-VERSION.run            install REMOTIX (or upgrade it to this version)
#     sh remotix-VERSION.run check           examine the machine: what REMOTIX can do, what is missing
#     sudo sh remotix-VERSION.run tui        the same installation in a text interface
#
# This header is packaging/rilascio.sh's: below the __PAYLOAD__ line there is a tar.gz with the
# installation engine (remotix-install), LICENSE.md (the REMOTIX licence), THIRD-PARTY-LICENSES (the licences of the third-party
# components inside) and the REMOTIX packages of every supported distribution (packages/<target>/). Nothing is added to the system's repositories: the package manager installs
# those files, and takes their dependencies from the repositories the machine already has.
# REMOTIX does not change the system: what is missing is said, and providing it is up to the administrator.
set -eu
VERSIONE=''
PAYLOAD_SHA256=''

errore() { echo "remotix: $*" >&2; exit 1; }

comando=${1:-install}
[ $# -gt 0 ] && shift
case $comando in
install | tui) [ "$(id -u)" -eq 0 ] || errore "run it as administrator: sudo sh $0 $comando" ;;
check) ;;
version) echo "REMOTIX $VERSIONE"; exit 0 ;;
*) errore "usage: sudo sh $0 [install|check|tui] [--port N]" ;;
esac
for p in tar gzip sha256sum awk mktemp; do
	command -v "$p" >/dev/null 2>&1 || errore "$p is missing"
done
riga=$(awk '/^__PAYLOAD__$/ { print NR + 1; exit 0 }' "$0")
[ -n "$riga" ] || errore "$0: the file is damaged (no payload): download it again"
dir=$(mktemp -d /var/tmp/remotix-run.XXXXXX)
trap 'rm -rf "$dir"' EXIT INT TERM
tail -n +"$riga" "$0" >"$dir/payload.tar.gz"
if [ -n "$PAYLOAD_SHA256" ]; then
	echo "$PAYLOAD_SHA256  $dir/payload.tar.gz" | sha256sum -c --status - ||
		errore "$0: the file is damaged (sha256 does not match): download it again"
fi
tar -xzf "$dir/payload.tar.gz" -C "$dir"
rm -f "$dir/payload.tar.gz"
codice=0
case $comando in
install | tui) "$dir/remotix-install" "$comando" --bundle "$dir/packages" "$@" || codice=$? ;;
check) "$dir/remotix-install" check "$@" || codice=$? ;;
esac
exit $codice
__PAYLOAD__
