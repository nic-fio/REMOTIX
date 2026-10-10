#!/bin/bash
# Removes the benches of closed phases (user decision, 10 Oct 2026).
# The list of files that go is english-migration/banchi-tolti.txt; the files stay in git history.
set -euo pipefail
cd "$(dirname "$0")/.."
[ "$(git branch --show-current)" = full-english ] || { echo "not on full-english"; exit 1; }
n=$(wc -l < english-migration/banchi-tolti.txt)
xargs -a english-migration/banchi-tolti.txt -d '\n' git rm -q --
find banchi -type d -empty -delete
git commit -q -m "🧹 Benches of closed phases removed (user decision 10 Oct 2026): $n files out

Kept: the safety net (11-*), phases 15–19, rcp/ twins, prodotto/, sonda/, and
everything those really execute, import, compile or read, checked by a
reviewer. Lists in english-migration/banchi-tenuti.txt and banchi-tolti.txt;
the removed files remain in git history.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
git push -q
echo "done: $n files removed, $(git ls-files banchi | wc -l) remain in banchi/"
