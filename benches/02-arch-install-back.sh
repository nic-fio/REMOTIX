#!/bin/sh
# 02-arch-install-back.sh — packaging/arch/remotix.install: net_back() and post_remove (the --back marker).
# No podman, no root: the script's paths are rewritten into a temporary directory and remotix-net-move is a stub.
#   sh benches/02-arch-install-back.sh          (from the tree root)
# Checks: a --back that succeeds leaves no marker and post_remove deletes net/; a --back that exits non-zero, or exits 0
# and leaves a file in net/, leaves /run/remotix/back-incomplete and post_remove KEEPS net/ and says so.
# Exit status: 0 green, 1 red, 3 could not look.
set -u
HERE=$(cd "$(dirname "$0")/.." && pwd)
T=$(mktemp -d) || exit 3
trap 'rm -rf "$T"' EXIT
mkdir -p "$T/bin" "$T/lib" "$T/run" "$T/var/net" || exit 3
# paths -> the temporary directory
sed -e "s#/usr/lib/remotix#$T/lib#g" -e "s#/run/remotix#$T/run#g" -e "s#/var/lib/remotix#$T/var#g" \
	"$HERE/packaging/arch/remotix.install" > "$T/inst.sh" || exit 3
printf '#!/bin/sh\nexit 0\n' > "$T/bin/systemctl"; chmod +x "$T/bin/systemctl"
PATH="$T/bin:$PATH"
fails=0
ok() { echo "ok   $*"; }
no() { echo "FAIL $*"; fails=$((fails + 1)); }
# the stub: what it does is chosen by $MODE
cat > "$T/lib/remotix-net-move" <<EOF
#!/bin/sh
case "\$MODE" in
fail) rm -rf "$T/var/net/certificates" "$T/var/net/ban"; exit 1 ;;   # moves everything, then exits 1: only the rc counts
leave) exit 0 ;;                       # exits 0 and leaves net/ban where it is
good) rm -rf "$T/var/net/certificates" "$T/var/net/ban"; exit 0 ;;
esac
EOF
chmod +x "$T/lib/remotix-net-move"
run() {   # run MODE: a fresh net/ with a certificate and a ban, then pre_remove and post_remove
	rm -rf "$T/var" "$T/run"; mkdir -p "$T/var/net/certificates"     # no $T/run: install -d must make it
	: > "$T/var/net/certificates/page.pem"; : > "$T/var/net/ban"
	MODE=$1 sh -c ". '$T/inst.sh'; pre_remove; post_remove" > "$T/out" 2>&1
}
run good
[ ! -e "$T/run/back-incomplete" ] && [ ! -e "$T/var/net" ] && ok "--back succeeded: no marker, net/ deleted by post_remove" || no "good case: marker or net/ wrong"
run fail
[ -e "$T/run/back-incomplete" ] && [ -d "$T/var/net" ] && grep -q "net/ kept" "$T/out" && ok "--back exited 1 (nothing left in net/): marker, net/ kept and said" || no "fail case"
run leave
[ -e "$T/run/back-incomplete" ] && [ -f "$T/var/net/ban" ] && grep -q "net/ kept" "$T/out" && ok "--back left a file (exit 0): marker, net/ kept and said" || no "leave case"
# a stale marker of an earlier failed run is cleared by a --back that succeeds
mkdir -p "$T/run"; : > "$T/run/back-incomplete"
rm -rf "$T/var"; mkdir -p "$T/var/net"
MODE=good sh -c ". '$T/inst.sh'; net_back" >/dev/null 2>&1
[ ! -e "$T/run/back-incomplete" ] && ok "a successful --back removes the stale marker" || no "stale marker stayed"
[ "$fails" = 0 ] && { echo "GREEN"; exit 0; } || { echo "RED ($fails)"; exit 1; }
