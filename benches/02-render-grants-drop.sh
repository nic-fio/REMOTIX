#!/bin/sh
# 02-render-grants-drop.sh — the removal scripts of the three packagings take the card grants (ACL on /dev/dri/renderD*) back
# with `remotix --drop-render-grants`, BEFORE the record is deleted (R-1 of the page audit, DECISIONS-11 §11.4).
# No podman, no root: each script's paths are rewritten into a temporary directory and the binary is a stub.
#   sh benches/02-render-grants-drop.sh          (from the tree root)
# Checks, for Debian (prerm remove, postrm purge), Arch (pre_remove, post_remove) and RPM (the %preun block):
#   · a removal runs the binary once with --drop-render-grants, before the record is deleted;
#   · the binary exits 1 (some ACL left): a warning, the marker /run/remotix/render-grants-kept, and the record is KEPT
#     (Debian, Arch; rpm deletes its %ghost record anyway and only says so);
#   · an UPGRADE does not run it (Debian `upgrade`, rpm $1 = 1);
#   · no binary: nothing runs, nothing fails.
# The binary's own logic is checked by benches/unit/render-grant (checks 35-40).
# Exit status: 0 green, 1 red, 3 could not look.
set -u
HERE=$(cd "$(dirname "$0")/.." && pwd)
T=$(mktemp -d) || exit 3
trap 'rm -rf "$T"' EXIT
mkdir -p "$T/bin" "$T/lib" "$T/run" "$T/var" || exit 3
fails=0
ok() { echo "ok   $*"; }
no() { echo "FAIL $*"; fails=$((fails + 1)); }
printf '#!/bin/sh\nexit 0\n' > "$T/bin/systemctl"; printf '#!/bin/sh\nexit 0\n' > "$T/bin/deb-systemd-invoke"; chmod +x "$T/bin/"*
PATH="$T/bin:$PATH"
# the stub binary: records its arguments, answers by $MODE (good: 0; left: 1)
stub() {   # stub DIR/remotix
	cat > "$1" <<STUB
#!/bin/sh
echo "\$*" >> "$T/calls"
[ -f "$T/var/render-grants" ] && echo "record-present-at-call" >> "$T/calls"
[ "\${MODE:-good}" = left ] && exit 1
exit 0
STUB
	chmod +x "$1"
}
fresh() { rm -rf "$T/var" "$T/run" "$T/calls" "$T/out"; mkdir -p "$T/var"; : > "$T/var/render-grants"; : > "$T/var/render-grants.new"; : > "$T/var/ban"; }
rw() { sed -e "s#/usr/libexec/remotix#$T/lib#g" -e "s#/usr/lib/remotix#$T/lib#g" -e "s#/run/remotix#$T/run#g" -e "s#/var/lib/remotix#$T/var#g" "$1"; }

# ── Debian ──
rw "$HERE/packaging/debian/remotix.prerm" > "$T/prerm.sh" || exit 3
rw "$HERE/packaging/debian/remotix.postrm" > "$T/postrm.sh" || exit 3
mkdir -p "$T/lib"; stub "$T/lib/remotix"
fresh; MODE=good sh "$T/prerm.sh" remove > "$T/out" 2>&1; sh "$T/postrm.sh" purge >> "$T/out" 2>&1
[ "$(grep -c -- '--drop-render-grants' "$T/calls" 2>/dev/null)" = 1 ] && grep -q record-present-at-call "$T/calls" && [ ! -e "$T/var/render-grants" ] && [ ! -e "$T/run/render-grants-kept" ] \
	&& ok "Debian remove+purge: the binary runs once with the record still there, then purge deletes the record" || no "Debian good case ($(cat "$T/calls" 2>/dev/null | tr '\n' ' '))"
fresh; MODE=left sh "$T/prerm.sh" remove > "$T/out" 2>&1; sh "$T/postrm.sh" purge >> "$T/out" 2>&1
[ -f "$T/var/render-grants" ] && grep -q "could not all be taken back" "$T/out" \
	&& ok "Debian, grants left (exit 1): warning, purge KEEPS the record" || no "Debian left case"
fresh; MODE=good sh "$T/prerm.sh" upgrade 1.4 > "$T/out" 2>&1
[ ! -e "$T/calls" ] && ok "Debian upgrade: the binary is not run" || no "Debian upgrade ran the binary"
fresh; rm -f "$T/lib/remotix"; sh "$T/prerm.sh" remove > "$T/out" 2>&1; rc=$?; sh "$T/postrm.sh" purge >> "$T/out" 2>&1
[ "$rc" = 0 ] && [ ! -e "$T/calls" ] && [ ! -e "$T/var/render-grants" ] && ok "Debian without the binary: nothing runs, purge deletes the record, rc 0" || no "Debian no-binary case"
stub "$T/lib/remotix"

# ── Arch ──
rw "$HERE/packaging/arch/remotix.install" > "$T/arch.sh" || exit 3
rm -f "$T/lib/remotix-net-move"
fresh; MODE=good sh -c ". '$T/arch.sh'; pre_remove; post_remove" > "$T/out" 2>&1
[ "$(grep -c -- '--drop-render-grants' "$T/calls" 2>/dev/null)" = 1 ] && grep -q record-present-at-call "$T/calls" && [ ! -e "$T/var/render-grants" ] \
	&& ok "Arch pre_remove+post_remove: the binary runs once before the record is deleted" || no "Arch good case ($(cat "$T/calls" 2>/dev/null | tr '\n' ' '))"
fresh; MODE=left sh -c ". '$T/arch.sh'; pre_remove; post_remove" > "$T/out" 2>&1
[ -f "$T/var/render-grants" ] && [ -e "$T/run/render-grants-kept" ] && grep -q "render-grants kept" "$T/out" \
	&& ok "Arch, grants left: marker, post_remove KEEPS the record and says so" || no "Arch left case"
fresh; rm -f "$T/lib/remotix"; sh -c ". '$T/arch.sh'; pre_remove; post_remove" > "$T/out" 2>&1; rc=$?
[ "$rc" = 0 ] && [ ! -e "$T/calls" ] && [ ! -e "$T/var/render-grants" ] && ok "Arch without the binary: nothing runs, record deleted, rc 0" || no "Arch no-binary case"
stub "$T/lib/remotix"

# ── RPM: the block between the markers of %preun ──
sed -n '/^# BEGIN drop-render-grants$/,/^# END drop-render-grants$/p' "$HERE/packaging/rpm/remotix.spec" \
	| sed -e "s#%{_libexecdir}/remotix#$T/lib#g" > "$T/rpm.sh"
[ -s "$T/rpm.sh" ] || { echo "no drop-render-grants block in the spec"; exit 3; }
fresh; MODE=good sh -c 'set -- 0; . "'"$T"'/rpm.sh"' > "$T/out" 2>&1
[ "$(grep -c -- '--drop-render-grants' "$T/calls" 2>/dev/null)" = 1 ] && ok "rpm %preun with \$1 = 0 (last removal): the binary runs once" || no "rpm removal case"
fresh; MODE=good sh -c 'set -- 1; . "'"$T"'/rpm.sh"' > "$T/out" 2>&1
[ ! -e "$T/calls" ] && ok "rpm %preun with \$1 = 1 (upgrade): the binary is not run" || no "rpm upgrade ran the binary"
fresh; MODE=left sh -c 'set -- 0; . "'"$T"'/rpm.sh"' > "$T/out" 2>&1; rc=$?
[ "$rc" = 0 ] && grep -q "could not all be taken back" "$T/out" && ok "rpm, grants left: said, the transaction does not fail" || no "rpm left case (rc=$rc)"
[ "$fails" = 0 ] && { echo "GREEN"; exit 0; } || { echo "RED ($fails)"; exit 1; }
