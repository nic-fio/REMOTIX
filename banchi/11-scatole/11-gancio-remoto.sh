#!/bin/bash
# ===========================================================================
# 11-gancio-remoto.sh — ⭐ THE PIECE THAT RUNS **ON THE TEST MACHINE**
# ===========================================================================
#
#   bash 11-gancio-remoto.sh <file-esito> gira --famiglia rete …
#
# ⛔ A person does not launch it: `11-gancio.sh remoto` launches it from the laptop,
#    inside a `systemd-run` unit, because the fast family costs `[M]` 173 s
#    and a long command over direct ssh does not make it home.
#
# ---------------------------------------------------------------------------
# ⛔⛔ IT EXISTS FOR ONE REASON ONLY, and it must be said: **a transient unit that
#     SUCCEEDS disappears.**
#
# `systemd-run --unit=X …`: when the command exits **0**, systemd collects
# the unit and `systemctl is-active X` answers `inactive`.  ⇒ ⛔ From outside
# «gone because it went well» and **«never started»** look exactly
# the same — and `systemctl show -p ExecMainStatus` answers **empty** in
# both cases.
# ⇒ ⚠ Whoever launched it would read a silence and would have to guess.  It is the
#   error shape of `LEZIONI.md` §1.46: a run that did not run and that
#   looks like a successful one.
#
# ⭐ So the outcome is not deduced from systemd: **it is written to a file**, and whoever
#   launched it reads it.  The file is also the «I am done» signal: as long as it is not
#   there, the run is still running.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)

if [ $# -lt 1 ]; then
	printf 'usage: bash %s <file-esito> gira --famiglia <nome> …\n' "$0" >&2
	exit 2
fi

ESITO_FILE=$1
shift

# ⛔ It is deleted HERE, not only by whoever launches: an old outcome file read as
#    if it belonged to this run is a run reporting the outcome of another.
rm -f "$ESITO_FILE"

bash "$QUI/11-gancio.sh" "$@"
E=$?

# ⚠ And it is written **after**, never before: the file appearing means «finished».
printf '%s\n' "$E" > "$ESITO_FILE"
chmod 644 "$ESITO_FILE" 2>/dev/null

exit "$E"
