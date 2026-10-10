#!/bin/bash
# Removes the v1 leftovers in fondamenta/ that nothing uses any more (user decision, 10 Oct 2026).
# The list of files that go is english-migration/fondamenta-tolti.txt; the files stay in git history.
set -euo pipefail
cd "$(dirname "$0")/.."
[ "$(git branch --show-current)" = full-english ] || { echo "not on full-english"; exit 1; }
n=$(wc -l < english-migration/fondamenta-tolti.txt)
xargs -a english-migration/fondamenta-tolti.txt -d '\n' git rm -q --
find fondamenta -type d -empty -delete
git commit -q -m "🧹 v1 leftovers in fondamenta/ removed (user decision 10 Oct 2026): $n files out

Kept: fondamenta/documenti (measured v1 docs), remotix-c/src whole (read as reference),
the calibration videos (DECISIONI §6.1), banco/ scripts still used, banco-compositori.
Checked by a reviewer. List in english-migration/fondamenta-tolti.txt;
the removed files remain in git history.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
git push -q
echo "done: $n files removed, $(git ls-files fondamenta | wc -l) remain in fondamenta/"
