#!/bin/bash
# ===========================================================================
# 11-hook.sh — ⭐⭐ WHEN THE NET STARTS, AND WHAT STARTS
# ===========================================================================
#
#   bash 11-hook.sh decide                 says what it would do, and why
#   bash 11-hook.sh run [--dry-run]         decides and runs
#   bash 11-hook.sh run --family net           ⭐ almost zero cost, really
#   bash 11-hook.sh run --family whole-net    ⛔ + C14: [M] ~800 s, and it
#                                                    takes the FOUR boxes
#   bash 11-hook.sh run --family all --box gnome
#   bash 11-hook.sh remote [--dry-run]       ⭐ decides HERE, runs THERE, and reports back
#   bash 11-hook.sh install [pre-push|pre-commit] [--here-only]
#   bash 11-hook.sh installed             is it there or not, and where
#   bash 11-hook.sh log [n]           the last n runs
#
# ===========================================================================
# ⛔⛔ DEFINED BY PATH, NOT BY GOOD WILL — `phases/11…` §5.1
# ===========================================================================
#
# ⚠ The difference is not formal.  A hook that ASKS whoever is working *«do you want to
#   run the net?»* is a hook that, the day one is in a hurry, does not run —
#   ⛔ and the days one is in a hurry are exactly those when things
#   break.
# ⇒ Here the question is not asked: we look at **which files changed**, and from those
#   follows what starts.  Whoever works has no lever to pull.
#
#   `src/` is touched (the product)    ⇒ the FUNZIONA family
#   the benches or the net are touched ⇒ NETWORK: C10-C13, C15.  ⭐ Almost
#                                        zero cost, and ⭐ none starts a session
#   what C14 depends on is touched     ⇒ RETE-INTERA: the net PLUS C14.
#     (`11-c14-*`, `11-c8-*`, `11-start.sh`, a `Containerfile.*`)
#     ⛔ `[M]` ~800 s, and it takes all four boxes for thirteen minutes
#   a `Containerfile.<new>` appears      ⇒ new desktop: everything on the new one, PLUS
#                                        the regression on the old ones
#   only documents are touched         ⇒ ⭐ NOTHING, and it says so.  A hook that
#                                        runs even when it is not needed is a
#                                        hook that someone will switch off
#
# ⚠ AND ONE THING THE PATH CANNOT TELL, declared instead of hidden:
#   *«before closing a phase»* is not a file that changes — it is a decision.
#   ⇒ That one is asked for by name (`--family all`), and that is fine: ⛔ pretending
#     a path could guess it would mean a rule that never
#     fires and that nobody notices has not fired.
#
# ===========================================================================
# ⛔⛔ THE 3-MINUTE CEILING, AND THE TESTS THAT WERE CUT
# ===========================================================================
#
# `phases/11…` §5.1: under 3 minutes for the fast family.  Above 5 begins
# the risk that it gets switched off; above 10 it is almost certain.  ⛔ And the rule on what
# to do when the time does not fit: **tests are cut, the ceiling is not
# raised.**
#
# `[M]` 26 August 2026 (`phases/11…` §7-bis.13): **one C1 run costs 74
# seconds.**  ⇒ In the 180 seconds **TWO runs** fit, and that is all.
#
# ⇒ ⭐⭐ WHAT WAS CUT FROM THE FAST FAMILY, and what it costs:
#
#   · **C1 from the third run on** (eight runs out of ten).  ⛔ Cost: the phase
#     document says the birth fault is INTERMITTENT, and with two runs
#     a fault that strikes once in five goes unnoticed more than
#     half the time.  ⚠ Today it does not bite — `[M]` 26 Aug 2026: ten sessions
#     out of ten are born blind, and two runs are enough to notice — ⛔ but the
#     day the defect is cured and becomes rare again, TWO RUNS WILL NOT
#     BE ENOUGH ANY MORE, and this line is there to remember it.
#   · **C8, both tests.**  ⛔ It is the most important mesh of the list,
#     and this cut is the most expensive of all: the second tenant's defect
#     is NOT looked at at every change.  ⚠ It stays in the `all` family, that is
#     before closing a phase.  ⇒ `[?]` The real cost: the first start of
#     Firefox in a cold box exceeds 25 s (`LESSONS.md` §1.45), and two
#     tenants for four boxes do not fit in three minutes in any way.
#   · ⭐⭐ **THE FIVE NEW ONES OF 27 AUGUST — C2, C3, C4, C6, C8b.**  None
#     enters the fast family, and it is not a postponement: `[M]` the ceiling is full at
#     **173 s out of 180**, and §5.1 says an extra mesh is SWAPPED, not
#     added.  ⛔ Here there is nothing to swap — the cheapest of these costs
#     more than the whole fast family, because each brings a session to life.
#     ⇒ They are in `all` and in `new-desktop`.
#     ⚠ AND THE COST OF THE CUT, declared: between a push and the closing of a
#     phase, **nobody looks whether a window opens, whether the frames change,
#     whether a key reaches the screen, whether a desktop finds itself again after a
#     detach, and whether the page shows from the client**.  ⛔ They are five of the six
#     questions the user asks himself looking at the screen.  ⇒ The cure is not
#     raising the ceiling: it is making a session cheaper to bring to life.
#   · **step 0.**  It looks at the ENVIRONMENT, which does not change when `src/` changes.
#     ⚠ Low and declared cost: if someone rebuilds a box without
#     saying so, the fast family does not notice.  ⭐ But **C11** notices,
#     which is in the fast family — and that is why it is there.
#
# ⛔ And the ceiling is NOT believed: every run is TIMED and the time ends up in the
#    log.  If it overruns, the hook says so out loud instead of carrying on.
#    ⇒ The `[?]` of the three minutes will become an `[M]` at the first real run.
#
# ===========================================================================
# ⭐⭐ AND IT LEAVES A TRACE — because without a trace C12 and C13 do not exist
# ===========================================================================
#
# One run per line, in `11-gancio-registro.jsonl`, append-only and never rewritten.
# ⛔ And among the fields there is one worth more than the others: **`dry`**.
#
# ⚠ A dry run (`--dry-run`) is NOT a run.  If it counted, one
#   `--dry-run` would be enough to make C12 say *«the hook is alive»* for a week, ⛔ that is
#   the net would tell itself it is running while it is not.  ⇒ The line is
#   written anyway (it serves whoever diagnoses), but it carries `"dry": true`, and
#   **C12 and C13 throw it away**.  ⭐ And both have that case inside their
#   certification, that is it is proven and not promised.
#
# ⛔ NO nested `sh -c` in here: `LESSONS.md` §1.46 — a command that
#    loses its quotes runs nothing and returns 0, that is a bench that
#    did not run and says «succeeded».  Every mesh is called with an ARRAY.
# ===========================================================================
set -uo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
# ⛔ Inside a git hook, git exports GIT_DIR: with it, `--show-toplevel` answers
#    the current folder (benches/11-boxes) and not the root of the repository —
#    `[M]` 3 Oct 2026, pre-push from a worktree: «I cannot find
#    banchi/11-scatole/fondamenta/strumenti/sshpw.py».  ⇒ We ask without it.
ROOT=$(env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE git -C "$HERE" rev-parse --show-toplevel 2>/dev/null)
LOG="$HERE/11-gancio-registro.jsonl"

# ⭐⭐ WHAT THE PRODUCT CAN DO, AND ON WHICH DESKTOP — the list is in ONE
#    place only, read also by `11-start.sh` (phase 13, 21 Sep 2026: before
#    there were two whitelists written by hand, and misaligned).
# ⛔ And if the file were missing the gate stays CLOSED and says so: no product
#    mesh runs «because the list was not there», and none stays silent.
if [ -r "$HERE/11-product-capabilities.sh" ]; then
	. "$HERE/11-product-capabilities.sh"
else
	product_ready() {
		printf '11-product-capabilities.sh is missing next to the hook: I do not know what the product can do'
		return 1
	}
fi

# ⚠ Every log line says ON WHICH MACHINE it was written.  ⛔ It is not an
#   ornament: since the runs of two machines end up in the same file
#   (`11-register-merge.py`), a line without this field is a line of which one no
#   longer knows whether it saw boxes or only a git repository.
HOST_WHERE=$(hostname 2>/dev/null) || HOST_WHERE=""
[ -n "$HOST_WHERE" ] || HOST_WHERE=sconosciuta

# ---------------------------------------------------------------------------
# ⭐⭐ THE TEST MACHINE — where the hook RUNS.  `DECISIONS.md`
#    §4.6-novemdecies: deciding needs the repository, running needs the boxes.
# ---------------------------------------------------------------------------
NETWORK11_REMOTE=/media/REMOTIX/rete11
# ⚠ The unit name can be changed (`--unit`) for one reason only: two
#   runs together on the same machine would step on each other's unit and log.
#   ⛔ It is not a lever to run fewer things — those do not exist.
REMOTE_UNIT=rete11-gancio
# ⛔ The wait ceiling of the remote half.  ⚠ It is NOT the 3-minute ceiling: it is
#   how long we wait before saying «I could not look».  The
#   `all` family costs `[M]` 1 704 s (§7-bis.16), so it cannot be 180.
#
# ⛔⛔ AND IT WAS 2 400, THAT IS A QUARTER OF WHAT IS NEEDED — 20 September 2026.
#
# `[M]` That number is from 27 August, when the `all` family cost 1 704 s
# on two boxes and fewer meshes.  Since then phase 12 has measured runs of
# **9 075 s** (increment 11, 20 Sep) and **10 645 s** (increment 4, 19 Sep) —
# `phases/12-kde.md`.  ⇒ With 2 400 this half gives up after 40 minutes and writes
# «I could not look» **while over there the run is still measuring**: a 3
# that says nothing about the product but about the clock of whoever waits.  The point was
# already written as open in `phases/12-kde.md` (the ceiling of the remote delegation).
#
# ⭐ And the ceiling is not the protection: the protection is the question about the unit
#   inside `wait_remote` — if over there it dies, we return at once, ceiling or no ceiling.
#   ⇒ The ceiling only serves not to wait for ever on a unit that is alive and silent, and
#     so it can be wide: four hours, against runs of three.
WAIT_REMOTE=14400

# ⛔ The ceiling is HERE, declared, and it is printed in every run: a verdict without
#    its yardstick is an opinion.
FAST_CAP=180

# ⚠ How much each mesh is expected to cost.  It serves ONE thing only: not
#   starting a mesh that does not fit in the remaining time.  ⛔ It is a forecast,
#   not a measurement — only C1 has an `[M]` under it:
#     C1   `[M]` 74 s per run, 26 Aug 2026, `phases/11…` §7-bis.13
#     C11  `[?]` queries four boxes with dpkg, seconds
#     C12  `[?]` reads two files
#     C13  `[?]` reads one file
#     C14  ⛔ `[M]` **786 s** — §7-bis.16, full run of 26 Aug 2026. And
#          ⛔ it starts all four boxes TOGETHER: it is not an almost-zero-cost
#          mesh, and that is why it is NO LONGER in the `net` family
#     C15  `[?]` reads one file, like C12 and C13
#     C5   `[M]` 71 s per run — 27 Aug 2026, after the cure of the dead ceilings
#          (`--wait-sink` 26 s + `--stay` 51 s).  ⛔ Before it said 45, which was
#          the measurement from BEFORE the cure: an old cost makes a mesh skip
#          that would fit, or starts one that does not fit
#   ⭐⭐ THE FIVE NEW MESHES of 27 August 2026 — the costs are next
#   to their declaration below, with the real mark of each.
#     C7   `[M]` 26 s the normal run, 25 s «only detaches», 37 s with the
#          fault injected (26 Aug 2026, XFCE box) — declared 30
#     C9   `[M]` 50 s (--stay 45), 26 Aug 2026, lxqt box
#     C10  ⭐ `[M]` **0,039 s** — reads three files and one line of the Makefile.
#          26 Aug 2026, median over ten runs on the laptop
COST_C1_ROUND=74
# ⛔ 27 Aug 2026: it was **45**, that is the measurement from BEFORE C5 was cured of its
#    dead ceilings.  ⚠ A cost that lags behind is not harmless: it governs whether
#    a mesh is started or skipped.
COST_C5=71
COST_C7=30
COST_C9=50
COST_C10=1
COST_C11=20
COST_C12=5
COST_C13=5
COST_C14=800
COST_C15=5
# ⭐ C16 `[M]` **0,79 s** — median over five runs on the laptop, 28 Aug 2026.
#    It reads 17 documents (48 000 lines) and the list of the repository's files.
COST_C16=1

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE FIVE NEW MESHES — 27 August 2026.  ⛔ NONE is in the fast
#    family, and it is not an oversight: `[M]` the ceiling is full at 173 s out of 180, and
#    §5.1 says an extra mesh is SWAPPED, not added.  Here there is
#    nothing to swap: the cheapest of these costs more than the whole
#    fast family.  ⇒ They are in `all` and in `new-desktop`.
# ⚠ And they do NOT run on every box: each runs where the product provides the
#   capabilities it wants (image, input, clipboard), and otherwise it SKIPS
#   saying which one is missing.  The list is in `11-product-capabilities.sh`.
#   `[R]` 21 Sep 2026: gnome and kde everything; xfce only the image (phase 13,
#   increment 2); lxqt nothing — the product does not recognise it.
# ═══════════════════════════════════════════════════════════════════════════
# ⭐ `[M]` 27 August 2026, cured rete11-gnome box, normal run timed
#   by the system.  ⚠ With the fault injected C2 opens TWO tenants and costs double
#   (`[M]` 418 and 419 s); C3 with the encoder stopped costs `[M]` 321 s.
COST_C2=210
COST_C3=162
COST_C4=32
COST_C6=205
COST_C8B=378

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE STAGE CEILING OF C2 AND C3 — ⛔ one number, in one place only.
#
# `[M]` 27 August 2026, cured gnome box: the stage is born in **2,1 · 2,2 ·
# 2,3 · 4,1 · 4,2 seconds** (five runs) — maximum **4,2 s**.  ⛔ The default
# value inside the two meshes is still **200 s**, which came from the ~97 s of
# when in the box `polkit` did not start.
#
# ⛔⛔ And in C2 and C3 that number is NOT a deadline: it is an ADDEND.  The two
#     meshes compute `--stay = attesa-palco + ... `, that is how long the client
#     stays attached: with 200 the client stays attached 255 s **even when the
#     stage was born after 2 seconds**.  ⇒ 140 seconds thrown away at every tenant.
# ⚠ In C4 and C6 instead it is a real deadline (we wait UNTIL it is born), and
#   so it is not passed here: lengthening or shortening it does not change the cost, and
#   a ceiling passed from outside without a reason is noise.
#
# ⇒ **60 s = 14 times the measured maximum.**  ⛔ And the right place for this
#   number is the `default` of the two meshes: it is here because on 27 August the
#   meshes were in the hands of another agent and two must not touch them at once.
#   ⚠ The day the default goes down, this line must be REMOVED, not left.
# ═══════════════════════════════════════════════════════════════════════════
CAP_STAGE_C2C3=60

FAST_ROUNDS=2

KNOWN_DESKTOPS="gnome kde xfce lxqt"

# ---------------------------------------------------------------------------
# ⛔⛔ WHERE THE GIT HOOKS ARE — and it is not a single line, for a reason.
#
# `git --git-path` returns a path **relative to the folder given to `-C`**, not
# to the root of the repository.  `[M]` 26 August 2026: called from `benches/11-boxes`
# it answers `../../.git/hooks`.  ⇒ Using it as it is means a path that
# depends on where one was when it was called — that is a hook that
# sometimes installs in the right place and sometimes not, without saying so.
# ⚠ And the very same defect bit C12, which said «not installed» for
#   ever.  ⇒ The resolution is HERE, in one place only.
# ---------------------------------------------------------------------------
hooks_dir() {
	local c
	c=$(git -C "$ROOT" rev-parse --git-path hooks 2>/dev/null) || return 1
	case "$c" in
	/*) printf '%s' "$c" ;;
	*)  printf '%s/%s' "$ROOT" "$c" ;;
	esac
}

ok()  { printf '  \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '  \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '      %s\n' "$*"; }
log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

# ---------------------------------------------------------------------------
# ⚠ The only JSON writing in this file, and it is in one place only on purpose: a
#   second point that builds JSON is a second point that can build it
#   crooked without anyone noticing.
# ---------------------------------------------------------------------------
json_string() {
	local s=${1-}
	s=${s//\\/\\\\}
	s=${s//\"/\\\"}
	s=${s//$'\n'/ }
	s=${s//$'\t'/ }
	printf '"%s"' "$s"
}

json_list() {
	local first=1 v
	printf '['
	for v in "$@"; do
		[ $first -eq 1 ] || printf ','
		first=0
		json_string "$v"
	done
	printf ']'
}

# ---------------------------------------------------------------------------
# ⭐ WHAT HAS CHANGED — and where it is looked at from
#
# ⚠ The comparison is NOT the same for every trigger, and it must be the
#   right one or the hook looks at the wrong place:
#     pre-commit   what is about to enter the commit    (`--cached`)
#     pre-push     what is about to leave               (`@{upstream}..HEAD`)
#     by hand      what is under one's hands now        (tree + staged)
# ---------------------------------------------------------------------------
changed() {
	local trigger=$1
	# ⛔ Without a repository there is nothing to list, and it is NOT an error: it is the
	#    test machine, where the hook RUNS instead of DECIDING.
	#    ⚠ Without this line three `git: command not found` came out at every run,
	#      that is noise that looks like a fault.
	[ -n "$ROOT" ] || return 0
	case "$trigger" in
	pre-commit)
		git -C "$ROOT" diff --name-only --cached
		;;
	pre-push)
		# ⚠ If there is no upstream branch (new branch), the difference cannot be
		#   made: the last commit is looked at.  ⛔ And looking at TOO MUCH is
		#   preferred to too little — a hook that skips
		#   is worse than a hook that runs more.
		local upstream
		upstream=$(git -C "$ROOT" rev-parse --abbrev-ref '@{upstream}' 2>/dev/null)
		if [ -n "$upstream" ]; then
			git -C "$ROOT" diff --name-only "$upstream..HEAD"
		else
			git -C "$ROOT" show --name-only --pretty=format: HEAD
		fi
		;;
	*)
		git -C "$ROOT" diff --name-only HEAD
		git -C "$ROOT" diff --name-only --cached
		git -C "$ROOT" ls-files --others --exclude-standard
		;;
	esac | sed '/^$/d' | sort -u
}

# ---------------------------------------------------------------------------
# ⭐⭐ THE RULE, all here: from the paths to the family.
#
# ⛔ And the order counts: «new desktop» wins over everything, because it is the case where
#    the regression on the old ones is needed most — and it is also the only one where the
#    path can say something nobody thought of declaring.
# ---------------------------------------------------------------------------
decide_family() {
	local -n _list=$1
	local f touches_product=0 touches_network=0 fresh=""

	# A new desktop is recognised by an ADDED recipe, not a modified one.
	local added
	added=$(git -C "$ROOT" diff --name-only --diff-filter=A --cached 2>/dev/null
	           git -C "$ROOT" ls-files --others --exclude-standard 2>/dev/null)
	for f in $added; do
		case "$f" in
		benches/11-boxes/Containerfile.*)
			local name=${f##*Containerfile.}
			case " $KNOWN_DESKTOPS " in
			*" $name "*) : ;;
			*) fresh="$name" ;;
			esac
			;;
		esac
	done

	# ═══════════════════════════════════════════════════════════════════
	# ⭐⭐ AND THE FOUR PATHS C14 DEPENDS ON — declared, not guessed.
	#
	# ⛔ C14 is no longer in the `net` family (it costs `[M]` 786 s and takes
	#    the four boxes: see `family_network`).  ⚠ But just removing it
	#    would mean that a change **to C14 itself** no longer makes it
	#    run — that is §5.2, *«a test that catches nothing is removed»*,
	#    obtained by disuse instead of by decision.
	# ⇒ ⭐ So it is not removed: it is MOVED onto a path of its own.  And the path
	#   is not arbitrary — they are the four things that, when they change, change
	#   precisely what C14 measures:
	#
	#   `11-start.sh`      ⭐ the PORT MAP lives inside it (lines 58-62,
	#                        gnome 8511 · kde 8512 · xfce 8513 · lxqt 8514), and
	#                        that is where the price of `--network=host` is written.
	#                        ⛔ C14 **copies** those ports — and a copied number
	#                        that changes on one side only is exactly
	#                        the defect C14 exists to catch
	#   `Containerfile.*`      the box recipe: if how it is born changes, whether
	#                        two can be on together changes
	#   `11-c8-*`            ⭐ it is C14's PROBE (it uses C8's test A): if the probe
	#                        changes, the fingerprint C14 compares changes
	#   `11-c14-*`           the mesh itself
	# ═══════════════════════════════════════════════════════════════════
	# ═══════════════════════════════════════════════════════════════════
	# ⭐⭐ AND THE PAPERS — 28 August 2026, and before today they decided NOTHING.
	#
	# ⛔ A commit that touched only `*.md` fell into the `nothing` branch: the net never
	#    looked at the papers.  ⇒ It is the reason why a line coordinate
	#    could rot for three days without anything noticing
	#    (`MASTERPLAN.md`, `src/child.c:3290` → 3482).
	# ⭐ It costs 0,79 s and starts nothing: it keeps the pact of §4.2 better than
	#    any other mesh.
	# ═══════════════════════════════════════════════════════════════════
	local touches_c14=0 touches_cards=0
	for f in "${_list[@]}"; do
		case "$f" in
		src/*|web/*)          touches_product=1 ;;
		esac
		case "$f" in
		*.md)                 touches_cards=1 ;;
		esac
		case "$f" in
		*/11-start.sh|*/Containerfile.*|*/11-c8-*|*/11-c14-*) touches_c14=1 ;;
		esac
		case "$f" in
		benches/*)             touches_network=1 ;;
		esac
	done

	if [ -n "$fresh" ]; then
		printf 'new-desktop:%s' "$fresh"
	elif [ $touches_product -eq 1 ]; then
		printf 'works'
	elif [ $touches_c14 -eq 1 ]; then
		printf 'whole-net'
	elif [ $touches_network -eq 1 ]; then
		printf 'net'
	elif [ $touches_cards -eq 1 ]; then
		printf 'papers'
	else
		printf 'nothing'
	fi
}

why_family() {
	case "${1%%:*}" in
	new-desktop) printf 'the recipe of a desktop that was not there has appeared: %s' "${1##*:}" ;;
	works)      printf 'the PRODUCT has changed (src/ or web/)' ;;
	whole-net)   printf 'something C14 depends on has changed (accendi, a recipe, C8, C14) ⇒ ⛔ ~800 s and the four boxes' ;;
	net)          printf 'the benches or the net have changed (benches/)' ;;
	nothing)        printf 'nothing the net looks at has changed' ;;
	esac
}

# ---------------------------------------------------------------------------
# ⭐ RUNNING A MESH, timing it — and without shells in between.
#
# It fills three global variables, and does not return a string to split: ⛔ a
# string to split is a place where an outcome can get lost silently.
# ---------------------------------------------------------------------------
M_OUTCOME=0
M_SECONDS=0
# ⭐ C10's outcome, kept aside: it decides whether it makes sense to inject a fault into it.
OUTCOME_C10=3
executed_json=""

# ---------------------------------------------------------------------------
# ⛔⛔ THE CLEAR-OUT, IN ONE PLACE ONLY — 22 September 2026
#
# ⚠ The meshes delete their tenant **before** creating it, not after: it is
#   intended («from scratch includes from scratch with respect to myself of yesterday»),
#   ⛔ but it means that between one run and the next the tenant REMAINS.  `[M]` 22 Sep
#   2026, after `--family all`: 22-24 live tenants in each of the three
#   boxes, with their `/home`, plus failed `user@…` units and orphans in
#   `/tmp`.  Only C6, C7 and C17 really cleared out.
#
# ⭐ And it is done HERE, not eleven times: whoever adds a mesh tomorrow must not
#    remember anything.  ⛔ The pattern is BOUNDED to the net's name space
#    — `c<number>[b]u<number>` — and it is not a global `pkill`: §7.3 of
#    phase 10 stays respected, `nictest` and `provanic` are not touched.
# ⚠ And the `runuser` that acts as the tenants' parent is **root**'s: it must be resumed
#   (`-CONT`) before closing it, or it stays stopped in `T` with a zombie child —
#   the leftover found in all three boxes (see `11-c3`).
# ---------------------------------------------------------------------------
clear_out_tenants() {
	local d=$1 removed
	[ "$DRY_RUN" = 1 ] && return 0
	# ⛔ WE CLEAR OUT ONLY WITH THE BOXES LOCK IN HAND (29 Sep 2026): the
	#   PAPERS do not take it (they start nothing), but the clear-out after C16
	#   ran anyway ⇒ `[M]` 10:32:18, a push of documents only during a
	#   run of the suite deleted the tenants of f016 in GNOME and LXQt, and
	#   the failed reattaches banned the address: 12 FAIL and 102 BLOCKED.
	[ -n "${REMOTIX_KEPT_BOXES:-}" ] || return 0
	box_on "$d" || return 0
	removed=$(podman exec "rete11-$d" sh -c '
		tolti=""
		for u in $(awk -F: "\$1 ~ /^c[0-9]+b?u[0-9]+$/ {print \$1}" /etc/passwd); do
			id=$(id -u "$u" 2>/dev/null)
			# ⛔ The pattern must NOT catch itself: the command line of
			#    this shell contains «runuser -u <u>», and a `pkill -f` would
			#    take it.  `[c]3u2` matches `c3u2` as an expression and not as
			#    text (22 Sep 2026, the shell was killing itself).
			m="runuser -u [$(printf %s "$u" | cut -c1)]$(printf %s "$u" | cut -c2-) "
			loginctl terminate-user "$u" >/dev/null 2>&1
			pkill -CONT -f "$m" >/dev/null 2>&1
			pkill -CONT -u "$u" >/dev/null 2>&1
			pkill -KILL -f "$m" >/dev/null 2>&1
			pkill -KILL -u "$u" >/dev/null 2>&1
			sleep 0.2
			userdel -r "$u" >/dev/null 2>&1 || userdel "$u" >/dev/null 2>&1
			[ -n "$id" ] && systemctl reset-failed "user@$id.service" >/dev/null 2>&1
			[ -n "$id" ] && find /tmp -maxdepth 1 -uid "$id" -exec rm -rf {} + 2>/dev/null
			tolti="$tolti $u"
		done
		printf "%s" "$tolti"
	' 2>/dev/null)
	[ -n "$removed" ] && inf "cleared out of $d:$removed"
	return 0
}

# ⚠ The meshes that do not name a box (C10, C11, C14, C16) leave
#   tenants in the boxes they touched: we sweep where work was done.
clear_out_after_mesh() {
	local name=$1 d
	case "$name" in
	*\(*\)*) d=${name#*(}; d=${d%%)*}; clear_out_tenants "$d" ;;
	*)         for d in $KNOWN_DESKTOPS; do clear_out_tenants "$d"; done ;;
	esac
}

run_mesh() {
	local name=$1 fault=$2; shift 2
	local before after

	if [ "$DRY_RUN" = 1 ]; then
		inf "(dry run) $name  ⇒  $*"
		M_OUTCOME=-1
		M_SECONDS=0
	else
		before=$SECONDS
		"$@"
		M_OUTCOME=$?
		after=$SECONDS
		M_SECONDS=$((after - before))
		case "$M_OUTCOME" in
		0) ok  "$name — holds  (${M_SECONDS}s)" ;;
		1) ko  "$name — DOES NOT HOLD  (${M_SECONDS}s)" ;;
		# ⭐ 23 Sep 2026: 2 had a name only in the code, and in the report
		#   it came out as «outcome 2» — which the reader has to go and look up.
		#   ⛔ It is the exit of C10, C12, C15 and C16 on the test machine: the
		#   question is not asked there, and it must be written like this instead of as a number.
		2) inf "?   $name — the terrain does not hold  (${M_SECONDS}s)" ;;
		3) inf "?   $name — I could not look  (${M_SECONDS}s)" ;;
		4) inf "?   $name — the turn never came  (${M_SECONDS}s)" ;;
		*) inf "?   $name — outcome $M_OUTCOME  (${M_SECONDS}s)" ;;
		esac
	fi

	# ═══════════════════════════════════════════════════════════════════
	# ⛔⛔ AND HERE IS SOMETHING THAT, IF LOST, MAKES C13 A LIE.
	#
	# A mesh with the FAULT INJECTED reads **THE OTHER WAY ROUND**: `C8 --no-fix`
	# exits **0** when the fault WAS SEEN, and **1** when it was NOT.
	# ⇒ That is, on an injected run `0` is the good news.
	#
	# ⚠ If this inversion stayed implicit, C13 would go looking for «a run
	#   with an injected fault and a red», ⛔ and it would find it even when the
	#   red comes from ANOTHER mesh — for example from C1, which really has the real
	#   fault.  ⇒ C13 would say «the net can give red» having looked at a
	#   mesh that has nothing to do with it.
	#
	# ⭐ So the inversion lives HERE, in one place only, and the log gets the
	#   fact instead of the raw outcome: **`ha_visto_il_guasto`**.  C13 reads
	#   that and does not need to know anything about how C8 exits.
	# ═══════════════════════════════════════════════════════════════════
	local seen=""
	# ⚠ In a dry run nothing was seen, in either direction: the
	#   key is not written at all.  ⛔ Writing it `false` would say «the fault
	#   was not seen», which is an accusation against a test that did not run.
	#
	# ═══════════════════════════════════════════════════════════════════
	# ⛔⛔⛔ AND OUTCOME **3** MADE THE SAME ACCUSATION, for all the meshes
	#      except C10.  27 August 2026, finding of an agent sent to refute.
	#
	# Here there was `if outcome = 0 … else false`: ⇒ a `3` — «I could not
	# look» — ended up written as **`ha_visto_il_guasto: false`**, that is *«the
	# fault passed under its nose and it did not see it»*.
	# ⛔ But a mesh that did not look has neither seen nor missed: it is
	#    exactly the `--dry-run` case above, and there the rule was already there.
	# ⇒ The day the injected ones on a box all came out 3 (server
	#   stopped, box not started, product not yet inside), ⛔ **C13
	#   would start shouting «the net can no longer give red» while the net
	#   is perfectly fine** — the defect C13 exists to catch, produced by the
	#   hook itself.
	#
	# ⛔⛔ AND OMITTING THE KEY IS NOT ENOUGH, which was the obvious cure: **C13 counts the
	#     meshes by `grafted_fault`**, and for it an ABSENT key means
	#     «not seen» (`11-c13…` has that case inside its certification: *«and
	#     nothing is known of its outcome ⇒ RED»*, and rightly so).
	# ⇒ So `grafted_fault` falls too: if the mesh did not judge,
	#   **in this run it was not certified**, and the line says so.  ⭐ It is the
	#   same shape `skip_mesh` has always used — `grafted_fault:false`
	#   plus the REASON — instead of two different ways of saying the same thing.
	# ⚠ And the fact is not lost: `innesto_non_giudicato` remains, for whoever diagnoses.
	# ═══════════════════════════════════════════════════════════════════
	local fault_written=$fault
	if [ "$fault" = true ] && [ "$DRY_RUN" != 1 ]; then
		case "$M_OUTCOME" in
		0)
			seen=',"saw_the_fault":true'
			ok "  ⭐ the injected fault WAS SEEN — the net can still give red"
			;;
		1)
			seen=',"saw_the_fault":false'
			ko "  ⛔⛔ the injected fault was NOT seen (outcome $M_OUTCOME)"
			;;
		*)
			# ⛔ Neither `true` nor `false`: it did not look.  ⚠ And it is said out loud —
			#   «I could not inject the fault» is information, not a
			#   silence, and a 3 that repeats is a fault of the bench (§5.2).
			fault_written=false
			seen=',"graft_not_judged":true'
			inf "  ⚠ the fault was injected and the mesh COULD NOT LOOK (outcome $M_OUTCOME)"
			inf "    ⇒ this run does NOT certify it, and ⛔ does not accuse it either:"
			inf "      for C13 it is as if the fault had not been injected"
			;;
		esac
	fi

	# ⭐ AND HERE WE SWEEP, however it went: a mesh that ends badly is the one
	#   that leaves the most behind.
	clear_out_after_mesh "$name"

	[ -n "$executed_json" ] && executed_json="$executed_json,"
	executed_json="$executed_json{\"name\":$(json_string "$name"),\"outcome\":$M_OUTCOME,\"seconds\":$M_SECONDS,\"fault_grafted\":$fault_written$seen}"
}

skip_mesh() {
	local name=$1 why=$2
	inf "⚠ SKIPPED $name — $why"
	[ -n "$executed_json" ] && executed_json="$executed_json,"
	executed_json="$executed_json{\"name\":$(json_string "$name"),\"outcome\":3,\"seconds\":0,\"fault_grafted\":false,\"saltata\":$(json_string "$why")}"
}

# ---------------------------------------------------------------------------
# ⛔⛔ THE MESHES ARE LOOKED UP BY PREFIX, not by full name.
#
# ⚠ A mesh that is not there is NOT a green and NOT a red: it is «I could not
#   look».  ⛔ Taking it as good because the file is missing would be the
#   error shape this phase exists not to repeat.
#
# ⭐ And the prefix is not laziness: `[M]` 26 August 2026, the first draft
#   pinned `11-c14-le-scatole-non-si-disturbano.py`, and the real file is
#   called `11-c14-they-do-not-interfere.py`.  ⇒ The hook would have said «SKIPPED
#   C14 — the file is not there» for ever, ⛔ and it would have been right from a wrong
#   point of view: the mesh was there, it was me calling it by the wrong name.
# ⚠ And if there were TWO with the same number we do not guess: we
#   say so, because choosing silently would mean running one mesh and
#   believing it is another.
# ---------------------------------------------------------------------------
WHICH_MESH=""
find_mesh() {
	local nr=$1 matches
	WHICH_MESH=""
	matches=$(ls "$HERE"/11-"$nr"-*.py 2>/dev/null)
	case $(printf '%s\n' "$matches" | sed '/^$/d' | wc -l) in
	0) return 1 ;;
	1) WHICH_MESH=$matches; return 0 ;;
	*) WHICH_MESH="TROPPE"; return 1 ;;
	esac
}

# ---------------------------------------------------------------------------
RUN_MESH() { python3 "$1"; }
RUN_C1()  { bash "$HERE/11-start.sh" c1 "$1" "$2"; }
RUN_C2()  { bash "$HERE/11-start.sh" c2 "$1" "${@:2}"; }
RUN_C3()  { bash "$HERE/11-start.sh" c3 "$1" "${@:2}"; }
RUN_C4()  { bash "$HERE/11-start.sh" c4 "$1" "${@:2}"; }
RUN_C6()  { bash "$HERE/11-start.sh" c6 "$1" "${@:2}"; }
RUN_C8()  { bash "$HERE/11-start.sh" c8 "$1" "${@:2}"; }
RUN_C8B() { bash "$HERE/11-start.sh" c8b "$1" "${@:2}"; }
RUN_C5()  { bash "$HERE/11-start.sh" c5 "$1" "${@:2}"; }
RUN_C7()  { bash "$HERE/11-start.sh" c7 "$1" "${@:2}"; }
RUN_C9()  { bash "$HERE/11-start.sh" c9 "$1" "${@:2}"; }
RUN_C17() { bash "$HERE/11-start.sh" c17 "$1" "${@:2}"; }
RUN_C18() { bash "$HERE/11-start.sh" c18 "$1" "${@:2}"; }
RUN_C19() { bash "$HERE/11-start.sh" c19 "$1" "${@:2}"; }
RUN_C20() { bash "$HERE/11-start.sh" c20 "$1" "${@:2}"; }
# ⭐ C24 «Log out ten times» (phase 14-15): it is not in the «product» step of
#   11-start.sh, so it copies itself into the box before running.
RUN_C24() {
	local p; case "$1" in gnome) p=8511;; kde) p=8512;; xfce) p=8513;; lxqt) p=8514;; esac
	podman cp "$HERE/11-c24-log-out-always-closes.py" "rete11-$1:/opt/remotix/" &&
	podman exec "rete11-$1" python3 -u /opt/remotix/11-c24-log-out-always-closes.py --port "$p" "${@:2}"
}
# ⭐ C21 (phase 14, 24 Sep 2026) does NOT run inside the box: it wants the REAL BROWSERS,
#   which live on the host inside the screenless labwc of the benches user.
#   ⇒ It is launched as that user (browsers as administrator do not start) and
#   from the whole benches tree, because it imports `12-c20-real.py` and
#   `12-real-clients.py` (imported, not copied).  ⚠ If the screenless labwc
#   is not there, C21 says 3 and names it: a 3 is not a green.
REAL_BENCHES=${REMOTIX_REAL_BENCHES:-/media/REMOTIX/src/controllo/benches}
REAL_USER=${REMOTIX_REAL_USER:-nicfio}
RUN_C21() {
	local u; u=$(id -u "$REAL_USER" 2>/dev/null) || return 3
	runuser -u "$REAL_USER" -- env XDG_RUNTIME_DIR="/run/user/$u" \
		WAYLAND_DISPLAY="${REMOTIX_REAL_WAYLAND:-wayland-0}" \
		REMOTIX_NESTED_SCREEN=1 REMOTIX_ON_SERVER=1 \
		REMOTIX_CHROME_OPTIONS=--ozone-platform=wayland MOZ_ENABLE_WAYLAND=1 \
		python3 "$REAL_BENCHES/11-boxes/11-c21-on-the-edge-the-shape-changes.py" \
		--box "$1" --visible "${@:2}"
}
RUN_C22() {
	local u; u=$(id -u "$REAL_USER" 2>/dev/null) || return 3
	runuser -u "$REAL_USER" -- env XDG_RUNTIME_DIR="/run/user/$u" \
		WAYLAND_DISPLAY="${REMOTIX_REAL_WAYLAND:-wayland-0}" \
		REMOTIX_NESTED_SCREEN=1 REMOTIX_ON_SERVER=1 \
		REMOTIX_CHROME_OPTIONS=--ozone-platform=wayland MOZ_ENABLE_WAYLAND=1 \
		python3 "$REAL_BENCHES/11-boxes/11-c22-the-edge-drags.py" \
		--box "$1" --visible "${@:2}"
}
RUN_C23() {
	local u; u=$(id -u "$REAL_USER" 2>/dev/null) || return 3
	runuser -u "$REAL_USER" -- env XDG_RUNTIME_DIR="/run/user/$u" \
		WAYLAND_DISPLAY="${REMOTIX_REAL_WAYLAND:-wayland-0}" \
		REMOTIX_NESTED_SCREEN=1 REMOTIX_ON_SERVER=1 \
		REMOTIX_CHROME_OPTIONS=--ozone-platform=wayland MOZ_ENABLE_WAYLAND=1 \
		python3 "$REAL_BENCHES/11-boxes/11-c23-shift-and-arrows-select.py" \
		--box "$1" --visible "${@:2}"
}
# ⭐ THE FUNCTIONAL SUITE (phase 15) — the new net, decided by the user on 24 Sep
#   2026: the 4 desktops in parallel with the REAL browsers, each test with its fault,
#   plus the short technical layer (C7 C9 C18 C19 per desktop, C14 together).
#   It runs as the browsers user, from the whole benches tree; ⛔ ~2 hours.
RUN_SUITE() {
	local u; u=$(id -u "$REAL_USER" 2>/dev/null) || return 3
	runuser -u "$REAL_USER" -- env XDG_RUNTIME_DIR="/run/user/$u" \
		python3 "$REAL_BENCHES/15-suite/15-round.py" --round "${SUITE_ROUND:-rete}" --technical-layer
}
# ⭐ C10 with the fault injected: it runs ON THE REPOSITORY, not on a box — ⇒ it is the
#   only mesh with an injected fault that the laptop half of the hook can
#   run.  ⛔ Without it, C13 on that half could never turn green.
RUN_C10G() { python3 "$1" --grafted-fault; }
RUN_P0()  { bash "$HERE/11-start.sh" step0 "$1"; }

# ---------------------------------------------------------------------------
# THE FAMILIES
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ⭐ THE PAPERS — the smallest family there is: one mesh only, 0,79 s.
#
# ⛔ It is needed because a commit of documents only used to run nothing,
#    and the papers were the only thing in the project nobody watched.
# ---------------------------------------------------------------------------
family_papers() {
	if find_mesh c16; then
		run_mesh C16 false RUN_MESH "$WHICH_MESH"
	else
		skip_mesh C16 "the file is not there"
	fi
}

family_network() {
	# ═══════════════════════════════════════════════════════════════════
	# ⛔⛔ C14 USED TO BE IN HERE, AND THE LINE NEXT TO IT PROMISED «almost zero cost,
	#     and none starts a session (§4.2)».  ⛔ **It was false, by a lot.**
	#
	# `[M]` §7-bis.16, full run of 26 August 2026: **C14 costs 786 s**, and
	# to measure that the boxes do not disturb each other it starts **all four
	# together** and runs C8's test A inside them.
	# ⇒ ⚠ Whoever read that line believed they could launch `--family net`
	#   next to another measurement without disturbing it: ⛔ and instead it took the
	#   four boxes for thirteen minutes.  ⛔ It is the trap of `LESSONS.md`
	#   §1.50 — a comment that describes a quantity different from the one the
	#   code governs — made worse by the number here being 786 against «zero».
	#
	# ⭐⭐ AND THE CURE CHOSEN IS **TO SPLIT**, not to rewrite the comment.  Because:
	#
	#   · ⛔ **just declaring was not enough.**  The real cost was already written
	#     in a comment, and the family cost 786 s all the same: a sign is not
	#     a cure.  And this family fires on EVERY change to `benches/`,
	#     that is — in this phase — on almost every push.  ⇒ Thirteen minutes at every
	#     push are exactly the thing §5.1 says makes a hook get **switched off**.
	#   · ⛔ **just moving it to `all` would have made it rot.**  A
	#     change to C14 itself would no longer have made it run: §5.2 says
	#     that *«a test that catches nothing is removed, and the reason is written»*
	#     ⛔ — not that it is left to die of disuse.
	#   · ⭐ **Splitting keeps both**: `net` goes back to being what
	#     §4.2 promised, and C14 stays hooked **to the path it depends on**
	#     (`decide_family`, where it is written which and why), as well as to
	#     `all`, to `new-desktop`, and to the name `--family whole-net`.
	#
	# ⭐ THE COST OF THIS FAMILY, now true: **on the laptop** `[M]` about
	#   1 s (C11 does not find the boxes and says «I could not look»);
	#   **on the test machine** `[M]` ~11 s, which is C11 — and none starts
	#   a session.  ⇒ The pact of §4.2 is kept instead of inherited.
	#
	# ⛔ THE PRICE, declared: a change to `benches/` that does NOT touch the
	#    four paths of C14 no longer runs C14.  ⚠ If one day it were
	#    discovered that C14 depends on something else, the cure is **adding that
	#    path** up there, ⛔ not putting it back in here.
	# ═══════════════════════════════════════════════════════════════════
	local n
	# ⚠ C10 is a mesh of the PRODUCT (§4.1), not of the net — it is here because the
	#   twin half lives in `benches/rcp/`: a change there fires THIS
	#   family, and it is ⛔ exactly the change that breaks the twin.
	#   ⭐ And it keeps the pact of §4.2: almost zero cost, and it starts nothing.
	# ⭐ C15 looks at whether the REMOTE HALF really runs: it reads the log, it costs
	#   as much as C12 and C13, ⛔ and on the test machine it exits **2** on purpose (there the
	#   log is not the merged memory, and it would be green whatever happens).
	for n in c10 c11 c12 c13 c15 c16; do
		local N=${n^^}
		if find_mesh "$n"; then
			run_mesh "$N" false RUN_MESH "$WHICH_MESH"
			# ⭐ C10's outcome is kept aside: it is needed shortly to decide
			#   whether it makes sense to inject a fault into it.
			[ "$n" = c10 ] && OUTCOME_C10=$M_OUTCOME
		elif [ "$WHICH_MESH" = TROPPE ]; then
			skip_mesh "$N" "there is MORE THAN ONE with this number: I do not guess"
		else
			skip_mesh "$N" "the file is not there"
		fi
	done
	# ⭐⭐ AND THE INJECTED FAULT, §3.6.  ⛔ It is not a luxury: it is the only line of
	#    this family that keeps C13 alive when the hook runs on the
	#    laptop, where there are no boxes.  It costs `[M]` 0,1 s.
	# ⛔ And here too: only if C10 could look — see `family_fast`.
	if find_mesh c10; then
		if [ "${OUTCOME_C10:-3}" = 0 ] || [ "${OUTCOME_C10:-3}" = 1 ]; then
			run_mesh "C10 guasto innestato" true RUN_C10G "$WHICH_MESH"
		else
			skip_mesh "C10 guasto innestato" "C10 did not look (there is no repository here): there is nothing to inject into"
		fi
	fi
}

# ---------------------------------------------------------------------------
# ⭐⭐ THE NET **PLUS C14** — and the cost is said BEFORE starting.
#
# ⛔ Saying it afterwards would be useless: whoever realises they launched the wrong
#    thing must be able to stop it, not read the bill thirteen minutes
#    later.  ⚠ It is the same reason the ceiling is respected before
#    starting a mesh instead of cutting it off half-way (§5.1).
# ---------------------------------------------------------------------------
family_full_network() {
	family_network
	log "and now C14 — ⛔ [M] 786 s (§7-bis.16), and IT TAKES THE FOUR BOXES"
	inf "⛔ if someone is measuring on rete11-* right now, this run"
	inf "  takes them away: §3.4, one box at a time because of the card"
	inf "  lock.  ⇒ Stop it with Ctrl-C now, not in thirteen minutes."
	inf "⚠ and for the net WITHOUT C14: --family net  ([M] ~11 s, starts nothing)"
	if find_mesh c14; then
		run_mesh C14 false RUN_MESH "$WHICH_MESH"
	elif [ "$WHICH_MESH" = TROPPE ]; then
		skip_mesh C14 "there is MORE THAN ONE with this number: I do not guess"
	else
		skip_mesh C14 "the file is not there"
	fi
}

family_fast() {
	# ⛔ The ceiling is RESPECTED before starting a mesh, it is not cut off
	#    half-way: cutting off would give a red that is not the product's — the
	#    error shape of `LESSONS.md` §1.45.
	local spent left
	# ⭐⭐ C10 FIRST, and for two reasons: it runs **before compiling** (it is the
	#    moment when the defect is stopped at zero cost), and ⛔ it costs less than the
	#    resolution of this stopwatch, which counts in whole seconds.
	#    `[M]` 26 Aug 2026: 0,039 s median over ten runs.
	# ⚠ §5.1 says the ceiling is full (153 s out of 180) and that an extra mesh must be
	#   SWAPPED, not added.  ⭐ Here there is nothing to swap: 0,04 s do not
	#   move a number counted in whole seconds — and the ceiling stays 153 s.
	if find_mesh c10; then
		run_mesh C10 false RUN_MESH "$WHICH_MESH"
		# ⭐ and its injected fault, which costs `[M]` 0,1 s: it is what
		#   allows C13 to say «the net can still give red» even in a
		#   fast run, without starting anything.
		# ⛔⛔ BUT ONLY IF C10 COULD LOOK.  On the test machine the
		#    repository is not there (§4.6-novemdecies): C10 would say «I do not know», the
		#    injected fault too.
		#    ⇒ If it could not look nothing is injected: there is no reason
		#      to run a test that cannot judge.
		# ⚠ 27 August 2026 — THIS GUARD IS NO LONGER THE ONLY DEFENCE, and it is
		#   right to say so because before it was: without it, `run_mesh` wrote
		#   `ha_visto_il_guasto: false` on an outcome 3, that is an accusation against the net
		#   for a fault nobody had judged.  ⭐ Now that rule
		#   lives INSIDE `run_mesh` and holds for ALL the meshes, not for C10
		#   only.  ⇒ It stays here because it does two more things: it does not waste the
		#   run, and it writes a more precise reason than «could not look».
		if [ "$M_OUTCOME" = 0 ] || [ "$M_OUTCOME" = 1 ]; then
			run_mesh "C10 guasto innestato" true RUN_C10G "$WHICH_MESH"
		else
			skip_mesh "C10 guasto innestato" "C10 did not look (there is no repository here): there is nothing to inject into"
		fi
	else
		skip_mesh C10 "the file is not there (or there is more than one)"
	fi

	# ⛔⛔ AND HERE TOO THE MESH IS LOOKED UP BY PREFIX, it is not called by name.
	#    `[M]` 26 August 2026, first real run on the test machine: here
	#    it said `GIRA_C11`, a function **that does not exist** ⇒ the shell
	#    said `command not found`, the outcome was **127**, and the run
	#    went on as if nothing had happened: ⛔ the fast family ran **without
	#    its first mesh**, and the log kept a number that
	#    means nothing.
	# ⚠ And it was seen only by running it: `bash -n` passes, because the syntax
	#   is valid (`LESSONS.md` §1.40).
	if find_mesh c11; then
		run_mesh C11 false RUN_MESH "$WHICH_MESH"
	else
		skip_mesh C11 "the file is not there (or there is more than one)"
	fi

	spent=$SECONDS; left=$((FAST_CAP - spent))
	local cost=$((COST_C1_ROUND * FAST_ROUNDS))
	if [ $left -lt $cost ]; then
		skip_mesh "C1x$FAST_ROUNDS" "${left}s remain and ~${cost}s are needed (ceiling ${FAST_CAP}s)"
	else
		local d
		# ⚠ `gnome` only because of the CEILING, not because the product cannot
		#   do anything else: today it starts kde and xfce too
		#   (`11-product-capabilities.sh`), but two C1 runs of `[M]` 74 s
		#   each already take 148 out of 180, and an extra box is SWAPPED, not added
		#   (§5.1).  ⛔ Adding one is a decision about the ceiling, not here.
		for d in gnome; do
			run_mesh "C1($d)x$FAST_ROUNDS" false RUN_C1 "$d" "$FAST_ROUNDS"
		done
	fi
	inf "⚠ cut from the fast family, and declared why at the top of this file:"
	inf "  C1 from the third run on · C5 · C7 · C8 (both tests) · C9 · step 0"
	inf "  ⛔ and the FIVE NEW ONES of 27 August: C2 · C3 · C4 · C6 · C8b"
	inf "  ⚠ and the ceiling is FULL: [M] 173 s out of 180 (26 Aug 2026, test machine)."
	inf "    ⛔ C5 (71 s), C7 (26 s) and C9 (50 s) do NOT fit: an extra mesh"
	inf "    is SWAPPED, not added (§5.1).  ⭐ C10 is there because it costs 0,04 s."
	inf "    ⛔ And the five new ones alone cost more than this whole family:"
	inf "      one session to bring to life each.  ⇒ they are in tutto and desktop-nuovo."
}

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE FIVE NEW MESHES, in one place only — 27 August 2026.
#
# ⛔ They are here and not copied twice on purpose: `family_all` and
#    `family_new_desktop` both want them, and two identical lists
#    are two lists that the next day are not any more — and nobody
#    notices, because both keep running (`LESSONS.md` §1.46).
#
# ⚠ And today they are SEVEN, not five: C17 (phase 12, 19 Sep 2026) has been in here
#   since then — and until 21 Sep it was AFTER the gate's `return`, that is
#   it skipped without being named in the log (`phases/13-xfce.md`, «The bench»,
#   point 1); and C20 since 23 Sep 2026.  The function name stayed for whoever
#   looks for it.
#
# ⭐⭐ THE GATE — phase 13, 21 Sep 2026: ONE MESH AT A TIME, and by
#     CAPABILITY, not by desktop name.
#   Before there was a single `if`, *«the product can only start GNOME and KDE»*, which
#   skipped everything as a block with that sentence.  ⛔ Since XFCE is born and shows
#   (C1(xfce) green, increment 2) the sentence is false: the meshes that look at
#   PIXELS can judge, those that want input or the clipboard still
#   cannot.  ⇒ Each mesh asks `product_ready` (in
#   `11-product-capabilities.sh`, read also by `11-start.sh`) whether the
#   desktop has what it wants; if something is missing it SKIPS, with its name and with
#   the missing capability written in the log.
# ⚠ And skipping is not caution: on a box where the product does not provide a
#   capability these meshes would spend minutes to say «I could not
#   look» — and a 3 that repeats because of a decision taken on purpose is the
#   cousin of the perpetual red (§1.49).
# ⛔ And the gate touches NO yardstick: a mesh that passes runs with the
#   same arguments, the same thresholds and the same injected faults as before.
#   `[R]` On gnome and kde (all capabilities) the sequence is identical to the one
#   before, line by line: C2×3, C3×4, C4×3, C6×2, C8b×2, C17×2.
# ═══════════════════════════════════════════════════════════════════════════
five_new() {
	local d=$1 why
	# ⭐ PHASE 12, INCREMENT 3 (19 Sep 2026) — the product starts KDE too, and
	#   on `kde` C3, C4 and C6 are `[M]` GREEN with their faults seen
	#   (`phases/12-kde.md`).  And with increment 4 also C2 and C8b, adapted to the
	#   Plasma splash screen; and since 19 Sep also C3's «encoder
	#   stopped» fault.
	# ⭐ PHASE 13, INCREMENT 2 (21 Sep 2026) — on `xfce` the image arrives:
	#   C2, C3 and C8b open.  ⛔ C4, C6 and C17 stay closed, and say which
	#   capability is missing (`11-product-capabilities.sh`).

	# ⭐ C2 — a window opens.  ⛔ It looks at THE PIXEL: the process count
	#   said 1 in both cases (phases/10… §7.4), and `--window-that-does-not-open`
	#   proves it instead of asserting it — the application stays ALIVE and does not paint.
	local P=(--wait-stage "$CAP_STAGE_C2C3")
	# ⭐ Increment 4: C2 looks at 240 frames for the «before», and the
	#   Plasma splash screen no longer stops it — opened to kde.
	if ! why=$(product_ready C2 "$d"); then
		skip_mesh "C2($d)" "${why:-the gate did not answer} — its 2 injected faults skipped with it"
	else
		run_mesh "C2($d)" false RUN_C2 "$d" "${P[@]}"
		run_mesh "C2($d) guasto innestato" true RUN_C2 "$d" "${P[@]}" --dying-app
		run_mesh "C2($d) guasto innestato (finestra cieca)" true RUN_C2 "$d" "${P[@]}" --window-that-does-not-open
	fi

	# ⭐ C3 — the frames arrive and the scene CHANGES.
	# ⚠ `--still-scene` is NOT an injected fault: it is the NEGATIVE control, and
	#   with the scene still C3 must not give red (`[M]` phases/09… §3.1: with a still
	#   scene 0,03 frames/s come out, and it is a RESULT).
	if ! why=$(product_ready C3 "$d"); then
		skip_mesh "C3($d)" "${why:-the gate did not answer} — the still scene and its 2 injected faults skipped with it"
	else
		run_mesh "C3($d)" false RUN_C3 "$d" "${P[@]}"
		run_mesh "C3($d) scena ferma" false RUN_C3 "$d" "${P[@]}" --still-scene
		run_mesh "C3($d) guasto innestato" true RUN_C3 "$d" "${P[@]}" --repeated-frame
		# ⭐ Since C3 of 19 Sep 2026 (the desktop still before the scene, and a COUNTED
		#   breath before the injection) this fault is seen on KDE too.
		run_mesh "C3($d) guasto innestato (codificatore fermo)" true RUN_C3 "$d" "${P[@]}" --stopped-encoder
	fi

	# ⭐ C4 — the key reaches the screen.  ⛔ It is the only mesh that
	#   judges a PIXEL crossing the product THERE AND BACK: C8 judges
	#   the browser alone, C5 judges bytes.
	if ! why=$(product_ready C4 "$d"); then
		skip_mesh "C4($d)" "${why:-the gate did not answer} — its 2 injected faults skipped with it"
	else
		run_mesh "C4($d)" false RUN_C4 "$d"
		run_mesh "C4($d) guasto innestato" true RUN_C4 "$d" --no-key
		run_mesh "C4($d) guasto innestato (coda)" true RUN_C4 "$d" --deaf-scene
	fi

	# ⭐⭐ C6 — detaches and finds itself again.  ⚠ It does NOT contradict C7 `--detach-only`:
	#   C7 asks «is the child alive?», C6 asks «and is what the child kept
	#   up FOUND AGAIN?».  ⛔ Whoever, seeing C6 red, made C7 red too
	#   «for consistency», would break the healthy mesh.
	if ! why=$(product_ready C6 "$d"); then
		skip_mesh "C6($d)" "${why:-the gate did not answer} — its injected fault skipped with it"
	else
		run_mesh "C6($d)" false RUN_C6 "$d"
		run_mesh "C6($d) guasto innestato" true RUN_C6 "$d" --kill-session
	fi

	# ⭐ C8b — and the same page shows FROM THE CLIENT.  ⛔ C8a does not go through the
	#   product: it looks at the browser inside the session.  This one looks at the pixels
	#   that reach the client.
	# ⭐ Increment 4: C8b's «before» is the first non-black frame —
	#   opened to kde.
	# ⚠ `11-start.sh c8b` has a gate of its own (for whoever launches it by hand), ⭐ but
	#   it reads the SAME list: the two can no longer say different things.
	if ! why=$(product_ready C8b "$d"); then
		skip_mesh "C8b($d)" "${why:-the gate did not answer} — its injected fault skipped with it"
	else
		run_mesh "C8b($d)" false RUN_C8B "$d"
		run_mesh "C8b($d) guasto innestato" true RUN_C8B "$d" --no-fix
	fi

	# ⭐ C17 — the clipboard both ways, and whoever reattaches (phase 12, 19 Sep
	#   2026).  `[M]` 19 Sep: kde green, and red on «R» only with the binary from
	#   before the cure; since 20 Sep green on gnome too (the GTK arbiter with the
	#   focus given by the client's click).
	# ⛔ Until 21 Sep here it said *«No desktop gate HERE»*,
	#   and it was false: these two lines were AFTER the gate's `return`,
	#   and on xfce and lxqt C17 skipped without being named.  ⇒ Now it has its own
	#   gate, like the others: it wants the image, the INPUT (the click that gives
	#   the focus to the arbiter goes through the product) and the clipboard.
	if ! why=$(product_ready C17 "$d"); then
		skip_mesh "C17($d)" "${why:-the gate did not answer} — its injected fault skipped with it"
	else
		run_mesh "C17($d)" false RUN_C17 "$d"
		run_mesh "C17($d) guasto innestato" true RUN_C17 "$d" --no-copy
	fi

	# ⭐⭐ C20 — rebirth after «Log out» brings no ghosts (23 Sep 2026).
	#   ⛔ It is the defect the USER found on 22 Sep on KDE with Chrome:
	#     after «Log out» and a new login the screen alternated three images, and
	#     ⛔ **without any error anywhere** — the product does not
	#     notice, the client does not notice, only whoever looks notices.
	#   ⭐ It comes from `benches/13-w4-rinascita-senza-fantasmi.sh`, which
	#     measured it; entering the net it took its injected fault
	#     (`--flashing-scene`), stopped knowing what Plasma is, and
	#     took a net name for its tenant (`c20u<n>`) — ⇒ so
	#     C19 sees it and the hook's clear-out removes it.
	#   ⚠ It wants the IMAGE, and it looks for the «Log out» gesture by itself: if in that
	#     box none of the three menus is there, it says 3 and names the one that is
	#     missing — ⛔ and a 3 is not a green.
	if ! why=$(product_ready C20 "$d"); then
		skip_mesh "C20($d)" "${why:-the gate did not answer} — its injected fault skipped with it"
	else
		run_mesh "C20($d)" false RUN_C20 "$d"
		run_mesh "C20($d) guasto innestato" true RUN_C20 "$d" --flashing-scene
		run_mesh "C24($d)" false RUN_C24 "$d"
		run_mesh "C24($d) guasto innestato" true RUN_C24 "$d" --reenter-at-once
	fi
	# ⭐ C21 — on the edge the shape changes (phase 14, user's decision of 24
	#   Sep: the real pointer shape on all four desktops).  It wants
	#   the «shape» capability; the `--wrong-shape` fault is judged by the
	#   PIXELS of the shape, not by a counter.
	if ! why=$(product_ready C21 "$d"); then
		skip_mesh "C21($d)" "${why:-the gate did not answer} — its injected fault skipped with it"
	else
		run_mesh "C21($d)" false RUN_C21 "$d"
		run_mesh "C21($d) guasto innestato" true RUN_C21 "$d" --wrong-shape
	fi
	# ⭐ C22 — dragging the edge the window widens (phase 14: the user,
	#   24 Sep, «resizing by dragging the edge on all the
	#   DEs»).  Judged by the PHOTOGRAPH: the right edge moves, the others do not.
	if ! why=$(product_ready C22 "$d"); then
		skip_mesh "C22($d)" "${why:-the gate did not answer} — its injected fault skipped with it"
	else
		run_mesh "C22($d)" false RUN_C22 "$d"
		run_mesh "C22($d) guasto innestato" true RUN_C22 "$d" --no-button
	fi
	# ⭐ C23 — Shift and arrows select (phase 14: the user, 24 Sep, «selection
	#   with Shift+arrows on all the DEs»).  The judgement is made on the
	#   PHOTOGRAPH of the field, not on a counter.
	if ! why=$(product_ready C23 "$d"); then
		skip_mesh "C23($d)" "${why:-the gate did not answer} — its injected fault skipped with it"
	else
		run_mesh "C23($d)" false RUN_C23 "$d"
		run_mesh "C23($d) guasto innestato" true RUN_C23 "$d" --no-shift
	fi
}

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ AND THE LAST MESH OF EVERY BOX — C19, «nobody from the net stays
#      inside».  23 September 2026, `phases/13-xfce.md` «What remains».
#
# ⛔⛔ IT GOES AT THE END, AND IT IS NOT A MATTER OF TASTE: this mesh prepares
#     nothing and proves nothing on its own — ⭐ **it judges the work of all the
#     others**.  Launched on a freshly rebuilt box it would say green and would not
#     have looked at anything.  ⇒ It comes after the last mesh that opens a
#     session, and before the balance.
#
# ⚠ And its green depends on the CLEAR-OUT that `run_mesh` does after every
#   mesh: if someone removed that, C19 would turn red the next
#   day — ⭐ and that is precisely why it exists.  Before it the
#   dirt was an `inf` line annotated `succeeded=true`, that is the net
#   could leave twenty tenants inside a box and call itself green.
# ═══════════════════════════════════════════════════════════════════════════
box_stays_clean() {
	local d=$1
	run_mesh "C19($d)" false RUN_C19 "$d"
	# ⛔ The two injected faults, and they are TWO because they look at two different
	#    leftovers: a LIVE tenant (which `pgrep` and `getent` see) and ⭐ a
	#    HOME WITHOUT A USER — the `userdel` without `-r`, which no count of
	#    processes and no count of users would ever catch.
	run_mesh "C19($d) guasto innestato" true RUN_C19 "$d" --leave-a-tenant
	run_mesh "C19($d) guasto innestato (solo la casa)" true RUN_C19 "$d" --leave-a-home
}

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ THE BOXES ARE REBUILT AT THE START OF `all` — 21 September 2026
#
# ⛔ Until now a full run started from the boxes AS IT FOUND THEM.
#    `[M]` 21 Sep 2026: after ~14 hours and hundreds of sessions in the same
#    box C17 turned RED on gnome and kde (direction «session →
#    device»).  Bisection: with yesterday's binary (green yesterday) in the old
#    box it was red anyway; with the new binary in the box rebuilt from
#    scratch, green 2 out of 2.  ⇒ Category C: the state accumulated by the box
#    broke a mesh, and the net accused the product of a red that was not its own.
#
# `[?]` WHAT ACCUMULATES, read from the code (it was not possible to get in):
#   · ⭐ `/tmp/remotix-arbitro-copia.log` — ONE fixed name written and removed
#     by C17's TENANT, never removed at the end ⇒ it stays with the uid of the first
#     `c17uNNN`; /tmp is «sticky», and a tenant with another uid neither
#     removes nor rewrites it ⇒ the copy command does not start ⇒ B and R
#     red.  It is the most likely cause, and it is CURED in C17 (the name carries
#     the tenant, and it is removed at the end).
#   · the uids that climb: `useradd` gives max+1, so a tenant's uid
#     depends on WHO REMAINED.  `[M]` in kde `user@4024` and `user@4025`
#     failed, with `provanic` at 4011: tenants that survived a dead run
#     (a `userdel` that fails with a process still alive).  ⇒ It is what
#     shifts C17's uid and makes the file above bite.
#   · the FAILED `user@…` units stay listed until someone does
#     `reset-failed`: step 0 shows them, and the box is «degraded».
#   · the first tenant's `/tmp/mozilla` (C2 already says so, and the cure has been in the
#     meshes since August); the per-tenant files in /tmp (`c4-…`, `c5-…`, `c8-…`)
#     that are not removed; `/var/lib/rete11/survey`, which grows at every session.
#
# ⭐ THE CURE: the `all` family (and `new-desktop`) starts by REBUILDING every
#   box it runs on — `turn_on` (the container is recreated from the image,
#   and everything that was there disappears with it), `product`, `server` — and it
#   DECLARES it: in the log, field `boxes`, with the seconds and the age the
#   box had before being thrown away.
# ⛔ The fast family (`works`, ceiling 180 s) rebuilds NOTHING: a box
#   costs `[?]` 15-40 s (the wait for systemd inside up to 30 s, the servers up
#   to 20 s), and the ceiling is full.  ⇒ There the GUARD speaks (`11-start.sh`,
#   `age_line`): one line, not a red, if the box has passed its hours or
#   its sessions.
# ⚠ THE COST in `all`: `[?]` 1-3 minutes for four boxes, against runs of
#   `[M]` 9 075-10 645 s (phase 12) ⇒ ~1-2 %.  It becomes `[M]` at the first run: the
#   seconds of each end up in the log.
# ⛔ And it takes the boxes: a session open inside dies.  It is already the price
#   of `all` (C14 takes the four boxes and restarts the servers).
#
# ⛔⛔ THE BINARY STAYS THE SAME IN THE FOUR (C11 checks it): `product`
#     copies from `/rete11/prodotto`, that is from the SAME folder for all.  With
#     `--box X` only X is rebuilt, ⚠ and in the other running ones only the
#     product is put back (they are not rebuilt and their servers are not restarted), so C11
#     and C14 at the end of the run compare four identical binaries.  One that is off is said.
# ═══════════════════════════════════════════════════════════════════════════
ALL_DESKTOPS="gnome kde xfce lxqt"
BOXES_JSON=""

annotate_box() {
	local d=$1 what=$2 seconds=$3 succeeded=$4 says=$5
	[ -n "$BOXES_JSON" ] && BOXES_JSON="$BOXES_JSON,"
	BOXES_JSON="$BOXES_JSON{\"desktop\":$(json_string "$d"),\"what\":$(json_string "$what"),\"seconds\":$seconds,\"succeeded\":$succeeded,\"says\":$(json_string "$says")}"
}

# ⚠ `11-start.sh` also prints its «OK/NO»: we keep ONLY the line that has
#   the expected shape, or we say it is not known.  ⛔ A «must be run as
#   administrator» read as an age would be an invented measurement.
line_from_turn_on() {
	local action=$1 d=$2 shape=$3 r
	r=$(bash "$HERE/11-start.sh" "$action" "$d" 2>/dev/null | grep -E "^($shape|spenta)" | tail -1)
	printf '%s' "${r:-ignota}"
}

box_on() {
	[ "$(podman inspect --format '{{.State.Running}}' "rete11-$1" 2>/dev/null)" = true ]
}

redo_one_box() {
	local d=$1 before step t0 s has_failed=""
	before=$(line_from_turn_on age "$d" 'hours=')
	if [ "$DRY_RUN" = 1 ]; then
		inf "(dry run) I would rebuild the box $d  (now: $before)"
		return 0
	fi
	# ⛔ Without the image NOTHING is knocked down: `turn_on` would remove the
	#    box that is there without being able to rebuild it.  It is used as it is, and said.
	if ! command -v podman >/dev/null 2>&1 || ! podman image exists "rete11/$d:p0" 2>/dev/null; then
		ko "the box $d was NOT rebuilt: the image rete11/$d:p0 is not here"
		inf "  ⇒ its meshes run on the box AS THEY FIND IT ($before)"
		annotate_box "$d" "redone" 0 false "the image is missing: used as it was ($before)"
		return 1
	fi
	inf "the box $d before being thrown away: $before"
	t0=$SECONDS
	for step in start product server; do
		if ! bash "$HERE/11-start.sh" "$step" "$d"; then
			has_failed=$step
			break
		fi
	done
	s=$((SECONDS - t0))
	if [ -z "$has_failed" ]; then
		ok "box $d rebuilt from scratch — start, product, server — in ${s}s"
		annotate_box "$d" "redone" "$s" true "it was: $before"
	else
		ko "box $d: «$has_failed» did not succeed (${s}s) ⇒ its meshes will say «I could not look»"
		annotate_box "$d" "redone" "$s" false "failed «$has_failed»; it was: $before"
	fi
}

redo_boxes() {
	local d t0 asked=" $* "
	log "the boxes are REBUILT from scratch before measuring: $*"
	inf "⛔ a full run no longer starts from the dirt of the runs before (21 Sep 2026, C17)"
	for d in "$@"; do
		redo_one_box "$d"
	done
	# ⛔ The same binary in the four: the others, if running, take this run's
	#    product (and that is all: no server restarted, no
	#    box thrown away — they were not asked for).
	for d in $ALL_DESKTOPS; do
		case "$asked" in *" $d "*) continue ;; esac
		if [ "$DRY_RUN" = 1 ]; then
			inf "(dry run) I would put the product back in $d, without rebuilding it"
			continue
		fi
		if ! box_on "$d"; then
			inf "⚠ $d is off: not rebuilt and not aligned ⇒ C11 will say whether the binary differs"
			continue
		fi
		t0=$SECONDS
		if bash "$HERE/11-start.sh" product "$d" >/dev/null 2>&1; then
			inf "⭐ $d not rebuilt (not asked for), but with this run's product ($((SECONDS - t0))s)"
			annotate_box "$d" "solo il prodotto" "$((SECONDS - t0))" true "not asked for: not rebuilt, binary aligned"
		else
			ko "$d: I could not put the product back in ⇒ C11 will say whether the binary differs"
			annotate_box "$d" "solo il prodotto" "$((SECONDS - t0))" false "product not put back"
		fi
	done
}

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ AND THE REBUILD MUST NOT HIDE A LEAK OF THE PRODUCT.
#
# ⚠ Rebuilding the boxes wipes the box's dirt, ⛔ but it would also wipe
#   the signs of a product that leaks something at every session: the net
#   would be green for ever, because it would never live long enough to see it.
# ⭐ So every box has a BALANCE right before and right after its
#   meshes (`11-start.sh balance`), on the same server — no mesh
#   of the run restarts it, only C14 which comes after.  ~40-50 sessions in between.
#   And the balance is split by OWNER:
#     · the SERVER (descriptors, threads, children): if it grows, it is the PRODUCT — and
#       no rebuild cures it.  ⚠ A yellow line, out loud.
#     · the BOX (leftover tenants, sessions, failed units, /tmp without an
#       owner): if it grows, it is dirt of the benches or of systemd — and it is
#       what the rebuild removes from the next run.
# ⚠ It is not a red: a new measurement without an injected fault does not judge
#   (§3.6).  `[?]` The first run will say whether the server goes back to its floor
#   when the last session is closed; from there a mesh can be made of it.
#
# ⭐⭐ AND FOR THE BOX COLUMN THAT DAY HAS COME — 23 Sep 2026.
#     The line *«the BOX got dirty»* below stays an `inf` line
#     annotated `succeeded=true`, ⛔ but it is no longer the only thing that looks at that
#     fact: **C19** (`box_stays_clean`, right before this
#     balance) makes a VERDICT of it, with its injected fault.
#   ⚠ And the two count in a DIFFERENT way, on purpose:
#     · `bilancio` counts by **uid** (`>= 1000`, excluding `provanic`) ⇒ for it
#       ⛔ `nictest` is a tenant, and that is perfectly fine: it is a measurement, not a
#       judgement, and whoever diagnoses wants to see everything.
#     · C19 counts by **NAME**, on the net's name space
#       (`c<n>[b]u<n>`) ⇒ `nictest` does not fall into it by shape, and the mesh
#       never gives red for the user of the manual tests.
#   ⛔ If one day the two said different things, the one that judges is C19.
# ⭐ And the age guard stays on OUTSIDE `all`: whoever works with the
#   fast family or by hand on old boxes sees the line, and if a red
#   disappears by rebuilding the box the balance says which column it came from.
# ═══════════════════════════════════════════════════════════════════════════
BALANCE_BEFORE=""

value_of() {
	local x=" $1 "
	case "$x" in *" $2="*) ;; *) return 0 ;; esac
	x=${x#* $2=}
	printf '%s' "${x%% *}"
}

balance_before() {
	BALANCE_BEFORE=""
	[ "$DRY_RUN" = 1 ] && return 0
	BALANCE_BEFORE=$(line_from_turn_on balance "$1" 'server_pid=')
}

balance_after() {
	local d=$1 after k a b product_growth="" box_growth="" note=""
	[ "$DRY_RUN" = 1 ] && return 0
	after=$(line_from_turn_on balance "$d" 'server_pid=')
	case "$BALANCE_BEFORE$after" in
	*ignota*|*spenta*)
		inf "⚠ bilancio($d): not readable (before «$BALANCE_BEFORE», after «$after»)"
		annotate_box "$d" "balance" 0 false "before: $BALANCE_BEFORE; after: $after"
		return 0 ;;
	esac
	a=$(value_of "$BALANCE_BEFORE" server_pid); b=$(value_of "$after" server_pid)
	if [ "$b" = 0 ] && [ "$a" != 0 ]; then
		note="the server is NO LONGER THERE at the end of the meshes"
	elif [ "$a" != "$b" ]; then
		note="the server changed in between ($a→$b): the product column is not compared"
	else
		for k in server_fd server_fili server_figli; do
			a=$(value_of "$BALANCE_BEFORE" "$k"); b=$(value_of "$after" "$k")
			case "$a$b" in ''|*[!0-9]*) continue ;; esac
			[ "$b" -gt "$a" ] && product_growth="$product_growth $k $a→$b"
		done
	fi
	for k in inquilini sessioni fallite user_fallite tmp_orfani; do
		a=$(value_of "$BALANCE_BEFORE" "$k"); b=$(value_of "$after" "$k")
		case "$a$b" in ''|*[!0-9]*) continue ;; esac
		[ "$b" -gt "$a" ] && box_growth="$box_growth $k $a→$b"
	done
	inf "bilancio($d) before: $BALANCE_BEFORE"
	inf "bilancio($d) after : $after"
	[ -n "$note" ] && printf '  \033[1;33m⚠\033[0m  bilancio(%s): %s\n' "$d" "$note"
	if [ -n "$product_growth" ]; then
		printf '  \033[1;33m⚠\033[0m  bilancio(%s): the SERVER grew between the first and the last mesh:%s — it may be a leak of the PRODUCT, and rebuilding the box does NOT cure it\n' "$d" "$product_growth"
	fi
	[ -n "$box_growth" ] && inf "⚠ bilancio($d): the BOX got dirty:$box_growth — benches or systemd, not the server"
	annotate_box "$d" "balance" 0 true "before: $BALANCE_BEFORE; after: $after; product:${product_growth:- nothing}${note:+ ($note)}; box:${box_growth:- nothing}"
}

# ⭐ THE GUARD at the end of the run: the age of every box in the log, and ONE line
#   out loud if it has passed the threshold (the thresholds are in `11-start.sh`).
#   ⚠ It is called AFTER stopping the stopwatch: `[?]` ~1 s for four
#   boxes, which in the fast family must not enter the ceiling.
box_guard() {
	local d line
	[ "$DRY_RUN" = 1 ] && return 0
	command -v podman >/dev/null 2>&1 || return 0
	for d in "$@"; do
		line=$(line_from_turn_on age "$d" 'hours=')
		case "$line" in spenta|ignota) continue ;; esac
		annotate_box "$d" "eta a fine giro" 0 true "$line"
		case "$line" in
		*guardia=SUPERATA*)
			printf '  \033[1;33m⚠\033[0m  box %s OLD: %s — it is not a red; if something is red, rebuild the box and try again before accusing the product\n' "$d" "$line" ;;
		esac
	done
}

family_all() {
	# ⛔ No ceiling here: it is the family for before closing a phase, and §3.4
	#    says ONE BOX AT A TIME, in a row, because of the card lock.
	local d
	# ⭐ From CLEAN boxes, and declared (see `redo_boxes`).
	# shellcheck disable=SC2086
	redo_boxes $KNOWN_DESKTOPS
	for d in $KNOWN_DESKTOPS; do
		log "box $d"
		balance_before "$d"
		run_mesh "passo0($d)" false RUN_P0 "$d"
		run_mesh "C1($d)x10" false RUN_C1 "$d" 10
		run_mesh "C8($d)" false RUN_C8 "$d" --no-session
		# ⭐⭐ AND HERE IS THE HALF THAT COUNTS: the INJECTED fault.
		#    §3.6 — «every test of the list has, mandatorily, its
		#    injected fault, and that case must be run, not imagined».
		#    ⇒ It is this line that keeps C13 alive.
		run_mesh "C8($d) guasto innestato" true RUN_C8 "$d" --no-session --no-fix

		# ⭐ C5 — the sound: ⛔ today it is the only mesh that crosses the product
		#   from top to bottom, because it judges BYTES and not pixels (§7-bis.18).
		run_mesh "C5($d)" false RUN_C5 "$d"
		run_mesh "C5($d) guasto innestato" true RUN_C5 "$d" --no-source

		# ⭐ C7 — the leftovers.  ⚠ «only detaches» must NOT give red (I4):
		#   the stage belongs to the session and survives the disconnection.
		run_mesh "C7($d)" false RUN_C7 "$d"
		run_mesh "C7($d) detach only" false RUN_C7 "$d" --detach-only
		# ⚠ `--wait-close 10` is not a borrowed ceiling (§1.45): with the
		#   fault injected it is KNOWN that the field will not become free again, and 10 s are
		#   nine times the measured closing (`[M]` 1,13 s).
		run_mesh "C7($d) guasto innestato" true RUN_C7 "$d" --leave-a-process --wait-close 10

		# ⭐ C9 — the log.  The fault is injected on the REAL DATA, defacing the
		#   in-memory copy of the slice: the log on disk is not touched.
		run_mesh "C9($d)" false RUN_C9 "$d"
		run_mesh "C9($d) guasto innestato" true RUN_C9 "$d" --remove-name everything

		# ⭐⭐ C18 — the card groups are set by the PRODUCT (§7.21), and
		#    this is the only mesh that arrives WITHOUT groups: all the others
		#    give them to themselves (`ensure_groups`) and so hide
		#    that piece.  ⛔ Like C1, C5, C7, C9 it does not go through the
		#    capabilities gate: the enrolment lives in the parent, before the `fork`, and does not
		#    even know which compositor will be born — ⇒ it holds on EVERY desktop.
		run_mesh "C18($d)" false RUN_C18 "$d"
		run_mesh "C18($d) guasto innestato" true RUN_C18 "$d" --no-usermod

		# ⭐⭐ And the product meshes — each where the product provides what
		#    it wants, and the reason for every skip is written inside
		#    `five_new` (and in `11-product-capabilities.sh`).
		five_new "$d"
		# ⭐⭐ AND THE LAST ONE: nobody from the net must remain in here.
		#    ⛔ After all the others, or it would not judge their work.
		box_stays_clean "$d"
		# ⛔ And the balance: if the SERVER grew, the rebuild would never
		#    have shown it — this line says it.
		balance_after "$d"
	done
	# ⭐ `rete_intera`, that is **with C14** — and here it is right: this is the
	#   family for before closing a phase, the 786 s are already budgeted
	#   (`[M]` 786 out of 1 704, §7-bis.16), and no other test is running.
	family_full_network
}

family_new_desktop() {
	local fresh=$1 d
	log "the new desktop: $fresh"
	# ⭐ From CLEAN boxes here too: the new one and the old ones of the regression.
	local to_redo="$fresh"
	for d in $KNOWN_DESKTOPS; do
		[ "$d" = "$fresh" ] || to_redo="$to_redo $d"
	done
	# shellcheck disable=SC2086
	redo_boxes $to_redo
	balance_before "$fresh"
	run_mesh "passo0($fresh)" false RUN_P0 "$fresh"
	run_mesh "C1($fresh)x10" false RUN_C1 "$fresh" 10
	run_mesh "C8($fresh)" false RUN_C8 "$fresh" --no-session
	run_mesh "C8($fresh) guasto innestato" true RUN_C8 "$fresh" --no-session --no-fix
	run_mesh "C5($fresh)" false RUN_C5 "$fresh"
	run_mesh "C5($fresh) guasto innestato" true RUN_C5 "$fresh" --no-source
	run_mesh "C7($fresh)" false RUN_C7 "$fresh"
	run_mesh "C7($fresh) guasto innestato" true RUN_C7 "$fresh" --leave-a-process --wait-close 10
	run_mesh "C9($fresh)" false RUN_C9 "$fresh"
	run_mesh "C9($fresh) guasto innestato" true RUN_C9 "$fresh" --remove-name everything
	run_mesh "C18($fresh)" false RUN_C18 "$fresh"
	run_mesh "C18($fresh) guasto innestato" true RUN_C18 "$fresh" --no-usermod
	# ⭐⭐ The product meshes.  ⚠ A new desktop is not in
	#    `11-product-capabilities.sh` ⇒ they are all skipped, and the reason ends up
	#    in the log — ⛔ and that is exactly the place where one wants to read it: the
	#    day the product can start it, its line is written THERE, and
	#    this one starts running without anybody having to touch it.
	five_new "$fresh"
	box_stays_clean "$fresh"
	balance_after "$fresh"
	log "and the REGRESSION on the old ones — ⭐ without rewriting a line of the list"
	for d in $KNOWN_DESKTOPS; do
		[ "$d" = "$fresh" ] && continue
		run_mesh "C1($d)x$FAST_ROUNDS" false RUN_C1 "$d" "$FAST_ROUNDS"
	done
	# ⭐⭐ AND HERE C14 IS NEEDED MORE THAN EVER, not less: with one more box the
	#    question *«the boxes do not disturb each other»* has a new answer, and the
	#    port map of `11-start.sh` has a new entry to assign.
	family_full_network
}

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ THE TWO HALVES, WIRED — and it is not a convenience: it is the cure of the fault
#      declared in `DECISIONS.md` §4.6-novemdecies.
#
# ⛔ Until now the hook had two halves on two machines and **only one of the two
#    was hooked to anything**: on the laptop there is the repository and there is the
#    `pre-push`, but there only C10, C12, C13 can run — `[M]` one second.
#    The real meshes want the boxes and the card, that is the test machine,
#    ⛔ where there is no git and so **nothing starts them**: today a
#    person launches them by hand.  ⇒ It is the exact way these nets die
#    silently (§4.2): they exist, they are perfect, and nothing starts.
#
# ⭐ From here on: **we decide where the repository is, we run where the
#   boxes are, and the memory comes back to one place only.**
# ═══════════════════════════════════════════════════════════════════════════

# ---------------------------------------------------------------------------
# ⭐ THE HALF HERE — the meshes that want the REPOSITORY and not the boxes.
#
# ⚠ They are THREE, and they are always the same whatever the family: C10, its
#   injected fault, ⭐ and **C15** — which reads the freshly merged memory and says whether
#   the half OVER THERE is really running (see at the end of this function).
#   ⛔ It is not a choice of convenience — §4.6-unetvicies: on the
#   test machine C10 can only say «I could not look», so
#   **the injected fault that keeps C13 alive can only be born here.**
#   ⇒ If this half did not run, C13 would have as its only food runs in which
#     no fault was ever injected, and would say red for ever.
# ---------------------------------------------------------------------------
meta_local() {
	if find_mesh c10; then
		run_mesh C10 false RUN_MESH "$WHICH_MESH"
		if [ "$M_OUTCOME" = 0 ] || [ "$M_OUTCOME" = 1 ]; then
			run_mesh "C10 guasto innestato" true RUN_C10G "$WHICH_MESH"
		else
			skip_mesh "C10 guasto innestato" "C10 did not look: there is nothing to inject into"
		fi
	elif [ "$WHICH_MESH" = TROPPE ]; then
		skip_mesh C10 "there is MORE THAN ONE with this number: I do not guess"
	else
		skip_mesh C10 "the file is not there"
	fi

	# ═══════════════════════════════════════════════════════════════════
	# ⭐⭐⭐ AND C15, **HERE AND ONLY HERE BETWEEN THE TWO HALVES** — and it is the place that
	#      makes it a mesh instead of an ornament.
	#
	# ⛔ C15 reads the MERGED MEMORY, and the merged memory is born two lines ago:
	#    `meta_remote` has just brought back and appended the lines of the test
	#    machine (`merge_logs`).  ⇒ A successful remote run makes it
	#    turn green at the same instant it happens.
	# ⛔ And if the remote half said 3, the merge did NOT happen: C15 reads
	#    the log from before, and rightly so — that run on the boxes did not
	#    happen.  ⇒ ⭐ That is how «a frequent 3» (§5.2) becomes a red
	#    line instead of staying an impression.
	#
	# ⚠⚠ AND WHAT IT BUYS MUST BE SAID, because it is a decision and not a
	#    detail: **a red from C15 BLOCKS the push**, while the 3 of the remote
	#    half does not block it.  ⛔ It looks like an inconsistency and it is not: §5.2 says
	#    that *«the single 3 is neutral; a FREQUENT 3 is a fault of the bench»*.
	#    ⇒ The test machine switched off this morning stops nobody; ⛔ the
	#      test machine switched off for eight days stops the push, because at
	#      that point one is pushing code nobody has measured.
	#    ⭐ And one goes back to green with one command, which C15 itself prints.
	# ═══════════════════════════════════════════════════════════════════
	if find_mesh c15; then
		run_mesh C15 false RUN_MESH "$WHICH_MESH"
	elif [ "$WHICH_MESH" = TROPPE ]; then
		skip_mesh C15 "there is MORE THAN ONE with this number: I do not guess"
	else
		skip_mesh C15 "the file is not there"
	fi
}

# ---------------------------------------------------------------------------
SSHPW=""
sshpw() { python3 "$SSHPW" "$@"; }

# ⚠ An annotation, not a mesh: it says whether the DELEGATION worked.
#   ⛔ It is needed because otherwise a switched-off test machine would be invisible:
#     the local half would write its green line, C12 would say «the hook is
#     alive», C13 would say «the net can give red» — ⛔ and on the boxes
#     nothing would have run for weeks.  ⇒ With this line in the log,
#     §5.2 bites: «a frequent 3 is a fault of the bench, not an outcome».
annotate_remote() {
	local outcome=$1 seconds=$2 note=$3
	[ -n "$executed_json" ] && executed_json="$executed_json,"
	executed_json="$executed_json{\"name\":\"la meta remota\",\"outcome\":$outcome,\"seconds\":$seconds,\"fault_grafted\":false,\"machine\":$(json_string "$NETWORK11_REMOTE"),\"note\":$(json_string "$note")}"
}

# ---------------------------------------------------------------------------
# ⛔⛔ THE WAITING IS NOT DONE BY THIS MACHINE, and it is not a detail.
#
# A `systemctl is-active` every five seconds for half an hour is **four hundred
# ssh connections**, each `[M]` 0,28 s: ⇒ two minutes thrown away and four hundred
# password prompts.  ⛔ And not even one long wait: a command that stays
# on direct ssh beyond a minute and a half does not make it home.
# ⇒ One minute at a time, and the one waiting is the test machine.
#
# ⚠ And we wait for **the outcome file**, not for systemd's state: a transient
#   unit that succeeds DISAPPEARS, and «gone» looks like «not started»
#   (`11-hook-remote.sh`, and it says why).
# ---------------------------------------------------------------------------
#
# ⛔⛔ AND WE ALSO LOOK WHETHER THE UNIT IS STILL ALIVE — `[M]` 27 August 2026, and
#     it was caught by this mechanism's injected fault, not by a reading.
#
# The first draft waited **only** for the outcome file.  ⇒ If the unit died
# without writing it — the launcher file is not there, `bash` does not start, systemd
# marks it `failed` — ⛔ **this function kept waiting 2 400 seconds**
# for a file that would never arrive.  ⚠ And the symptom was the deceiving one:
# not an error, but a «slow» push (the same shape as `sshpw.py`, where it is
# written out in full).
#
# ⭐ AND THE ORDER OF THE TWO QUESTIONS IS NOT FREE: **first the file, then the unit.**
#   The launcher writes the outcome **before** exiting ⇒ if the unit has disappeared, the
#   file is already there.  ⛔ Asking about the unit first there would be a gap in which
#   a successful run would be declared dead.
wait_remote() {
	local outcome_f=$1 cap=$2 spent=0 response=""
	while [ "$spent" -lt "$cap" ]; do
		# ⛔⛔ AND THE STEP IS 2 SECONDS, NOT 5 — and it is an account on the ceiling,
		#    not a taste.  `[M]` §5.1: the fast family is at **173 s out of 180**,
		#    that is seven seconds of margin.  ⚠ Whoever waits pays, on top of the run,
		#    the ROUNDING of this question: with a 5 s step one could
		#    lose 5 s at the end, and 173 + 5 + the round of the commands **breaks through**.
		#    ⇒ With a 2 s step the rounding stays inside the margin.
		# ⚠ The list of rounds is built by the laptop (`seq`), so the line
		#   that reaches the test machine has nothing to expand.
		response=$(sshpw "for i in $(seq 1 30 | tr '\n' ' '); do [ -f $outcome_f ] && break; systemctl is-active --quiet $REMOTE_UNIT || break; sleep 2; done; cat $outcome_f 2>/dev/null || { systemctl is-active --quiet $REMOTE_UNIT && echo ANCORA || echo MORTA; }" 2>/dev/null \
			| tr -d '\r' | grep -E '^[0-9]+$|^ANCORA$|^MORTA$' | tail -n 1)
		case "$response" in
		''|ANCORA) : ;;
		*) printf '%s' "$response"; return 0 ;;
		esac
		spent=$((spent + 60))
		# ⛔ On STDERR: this function is called inside `$(…)`, and what goes
		#    on stdout IS the answer.  `[M]` 18 Sep 2026: the remote half
		#    took 77 s, this line ended up in front of the «0», and a green
		#    run was recorded as «3 — I could not look».
		inf "  … the remote half is still running (${spent}s)" >&2
	done
	printf 'ATTESA'
	return 1
}

# ---------------------------------------------------------------------------
# ⭐ THE HALF OVER THERE — it is launched, waited for, read, and brought back.
#    It fills R_OUTCOME (0 green · 1 red · 3 I could not look) and R_NOTE.
# ---------------------------------------------------------------------------
R_OUTCOME=3
R_NOTE=""
meta_remote() {
	local fam=$1 inn=$2
	local log="$NETWORK11_REMOTE/$REMOTE_UNIT.log"
	local outcome_f="$NETWORK11_REMOTE/$REMOTE_UNIT.esito"
	# ⚠ `sudo` is needed because the box meshes go through `podman`, and the
	#   log over there has always been root's.  ⛔ And the price must be said: if the
	#   hook ran there as `nicfio`, appending to the log would fail with
	#   «Permission denied» and the run **would leave no trace** despite having
	#   measured everything.  `[M]` 27 August 2026, tried.
	local S="sudo -S -p 'Password sudo: '"
	local opt="" response="" before after

	[ "$DRY_RUN" = 1 ] && opt="$opt --dry-run"
	# ⚠ In quotes: `--box "gnome kde"` carries a SPACE, and without the quotes
	#   the remote half receives «kde» as a command of its own.  `[M]` 20 Sep 2026: the
	#   run did not start and the line only said «I could not launch».
	[ -n "$REQUESTED_BOX" ] && opt="$opt --box \"$REQUESTED_BOX\""

	before=$SECONDS
	# ⛔⛔ FIRST OF ALL: A RUN ALREADY IN PROGRESS IS NOT TOUCHED — 20 Sep 2026.
	#
	# `[M]` This morning's `pre-push` found the unit busy with a net
	# launched by hand, it could not launch its own (right), ⛔ but it had
	# ALREADY DELETED the log — and the run in progress kept writing to a
	# file that no longer existed.  ⇒ We look first, and if it is running we exit 3
	# saying so: «busy» and «I cannot reach it» are two different diagnoses.
	if sshpw "systemctl is-active --quiet $REMOTE_UNIT" >/dev/null 2>&1; then
		R_OUTCOME=3
		R_NOTE="on the test machine a run is ALREADY in progress ($REMOTE_UNIT)"
		ko "⛔ $R_NOTE"
		inf "  ⇒ I launch nothing and do not touch its log: one box at a time"
		inf "    (§3.4, the card lock).  Try again when it has finished"
		M_SECONDS=$((SECONDS - before))
		return 3
	fi
	# ⛔ The log and the outcome file are deleted FIRST: an old outcome read
	#    as if it belonged to this run is a run that reports about another.
	sshpw "$S systemctl reset-failed $REMOTE_UNIT 2>/dev/null; $S rm -f $log $outcome_f" >/dev/null 2>&1

	inf "launch: $NETWORK11_REMOTE/11-hook.sh run --family $fam --trigger $inn$opt"
	if ! sshpw "$S systemd-run --unit=$REMOTE_UNIT --property=StandardOutput=append:$log --property=StandardError=append:$log --property=WorkingDirectory=$NETWORK11_REMOTE bash $NETWORK11_REMOTE/11-hook-remote.sh $outcome_f run --family $fam --trigger $inn$opt" >/dev/null 2>&1; then
		after=$SECONDS
		R_OUTCOME=3
		R_NOTE="I could not launch the run on the test machine"
		ko "⛔ $R_NOTE"
		inf "  ⇒ it is an «I could not look» (outcome 3), ⛔ NOT a green:"
		inf "    the log line carries it written, and §5.2 says that a repeated"
		inf "    3 is a fault of the bench"
		M_SECONDS=$((after - before))
		return 3
	fi

	response=$(wait_remote "$outcome_f" "$WAIT_REMOTE")
	after=$SECONDS
	M_SECONDS=$((after - before))

	# ⭐ The log is brought home with scp (`--get`), ⛔ never by capturing the stdout of
	#   a remote `cat`: the password prompt also ends up in there
	#   (`fondamenta/strumenti/sshpw.py`, and it says why).
	local scratch_dir
	scratch_dir=$(mktemp -d)
	sshpw --get "$log" "$scratch_dir/remoto.log" >/dev/null 2>&1
	if [ -s "$scratch_dir/remoto.log" ]; then
		log "what the test machine said"
		sed 's/^/  | /' "$scratch_dir/remoto.log"
	fi

	# ⛔ And the two ways of not knowing are TWO, and they must be said separately: «it did not
	#    finish» and «it died without saying anything» are cured in different places.
	if [ "$response" = ATTESA ] || [ "$response" = MORTA ]; then
		R_OUTCOME=3
		if [ "$response" = MORTA ]; then
			R_NOTE="the remote half's unit died without writing an outcome"
			ko "⛔ $R_NOTE"
			inf "  ⇒ look at the log above and «systemctl status $REMOTE_UNIT»"
			inf "    on the test machine: the run did not even start"
		else
			R_NOTE="the remote half did not finish within ${WAIT_REMOTE}s"
			ko "⛔ $R_NOTE"
		fi
		rm -rf "$scratch_dir"
		return 3
	fi

	# ⭐⭐ AND NOW THE MEMORY COMES BACK — the other half of the problem.
	merge_logs "$scratch_dir"
	rm -rf "$scratch_dir"

	case "$response" in
	0) R_OUTCOME=0; R_NOTE="the remote half is green" ;;
	1) R_OUTCOME=1; R_NOTE="⛔ the remote half gave RED" ;;
	*) R_OUTCOME=3; R_NOTE="the remote half exited $response (terrain, or wrong usage)" ;;
	esac
	return 0
}

# ---------------------------------------------------------------------------
# ⭐⭐ ONE MEMORY ONLY — and it lives HERE, on the laptop.
#
# ⛔ It is not a preference: it is the only place where the two meshes that read
#    that memory can judge.  C12 needs the git repository to know
#    where the hooks are, and on the test machine it exits **2** — and §7-bis.16 says
#    that *it is the right answer*.  ⇒ The laptop is where the net looks at itself in the
#    mirror; the test machine is where it **runs**.
# ⚠ The log over there is NOT deleted and NOT emptied: it stays the local memory
#   of that machine, and serves whoever diagnoses there.  Here a copy of it is taken.
# ---------------------------------------------------------------------------
merge_logs() {
	local scratch_dir=$1
	local remote="$NETWORK11_REMOTE/11-gancio-registro.jsonl"
	sshpw --get "$remote" "$scratch_dir/registro-remoto.jsonl" >/dev/null 2>&1
	if [ ! -s "$scratch_dir/registro-remoto.jsonl" ]; then
		ko "⚠ I could not bring back the test machine's log"
		inf "  ⇒ the run over there really happened, but here nothing would be known"
		inf "    of it: C13 would not see it.  ⛔ It is a fault, not a detail"
		return 3
	fi
	python3 "$HERE/11-register-merge.py" "$LOG" "$scratch_dir/registro-remoto.jsonl"
}

# ---------------------------------------------------------------------------
write_log() {
	local family=$1 trigger=$2 exceeded=$3 seconds=$4 red=$5 fault=$6
	shift 6
	{
		printf '{'
		printf '"instant":%s,' "$(json_string "$(date -Is)")"
		printf '"where":%s,' "$(json_string "$HOST_WHERE")"
		printf '"trigger":%s,' "$(json_string "$trigger")"
		printf '"family":%s,' "$(json_string "$family")"
		printf '"dry":%s,' "$([ "$DRY_RUN" = 1 ] && echo true || echo false)"
		printf '"changed":%s,' "$(json_list "$@")"
		printf '"meshes":[%s],' "$executed_json"
		# ⭐ The boxes: rebuilt (with the seconds), balances, age at the end of the run.
		#   ⚠ Outside `meshes` on purpose: they are not judgements, and C12, C13 and C15
		#   must not count them as greens or as reds.
		printf '"boxes":[%s],' "$BOXES_JSON"
		printf '"fault_grafted":%s,' "$fault"
		printf '"went_red":%s,' "$red"
		printf '"seconds":%s,' "$seconds"
		printf '"cap":%s,' "$([ "$family" = works ] && echo "$FAST_CAP" || echo null)"
		printf '"exceeded":%s' "$exceeded"
		printf '}\n'
	} >> "$LOG"
	# ═══════════════════════════════════════════════════════════════════
	# ⛔⛔ AND WE CHECK WHETHER THE LINE REALLY WENT DOWN.
	#
	# `[M]` 27 August 2026, tried on the test machine: the log there is
	# **root's** — the runs launched with `systemd-run` wrote it, and the modes
	# are `-rw-r--r--`.  ⇒ A run launched by hand as `nicfio` does a `>>` that
	# fails with *«Permission denied»*, ⛔ **and this script carries on**:
	# `set -uo pipefail` has no `e`, and the next line prints «no
	# red».
	# ⇒ ⛔ A run that measured everything, left no trace, and said
	#   it had gone well.  ⚠ And the damage is not in the run: it is that C12 and C13
	#   live on that trace — the net would lose its memory without
	#   anyone noticing, which is §4.2 again.
	# ⭐ The permission is not repaired from here (it is not a bench's job): it is SAID.
	# ═══════════════════════════════════════════════════════════════════
	if [ ! -w "$LOG" ] && [ -e "$LOG" ]; then
		ko "⛔⛔ I COULD NOT WRITE TO THE LOG: $LOG"
		inf "  ⇒ this run measured everything and ⛔ LEFT NO TRACE."
		inf "    C12 will say the hook does not run and C13 that nobody puts it"
		inf "    to the test, and both will be right from a wrong"
		inf "    point of view."
		inf "  ⚠ it belongs to $(stat -c %U "$LOG" 2>/dev/null): either launch it with"
		inf "    the same user, or change the file's owner"
		return 1
	fi
}

# ---------------------------------------------------------------------------
# ⛔⛔ GIT IS NEEDED TO **DECIDE**, NOT TO **RUN** — and the difference is something
#     that was discovered at the first real run, `[M]` 26 August 2026.
#
# ⚠ The two halves of this hook live in two different places:
#     · DECIDING what to run needs the repository ⇒ it lives on the laptop
#     · RUNNING needs the boxes and the graphics card ⇒ it lives on the test
#       machine, ⛔ **where the repository is NOT**
#   ⇒ The first draft demanded git always, and exited **2** («bad terrain»)
#     on the only machine able to run the meshes: that is ⛔ **the hook
#     could not be timed where it really runs.**
#
# ⭐ So: if the family is ASKED FOR BY NAME there is nothing to decide, and the
#   repository is not needed.  If it is not asked for, it is needed — and then it is said.
# ⚠ And the log always marks which of the two roads was taken, so whoever
#   reads knows whether that run looked at paths or obeyed a name.
# ---------------------------------------------------------------------------
DRY_RUN=0
ACTION=${1:-decide}
shift 2>/dev/null || true
REQUESTED_FAMILY=""
REQUESTED_BOX=""
HERE_ONLY=0
TRIGGER="manual"
# ⛔⛔ AND THE ARGUMENTS THAT ARE NOT OPTIONS ARE PUT ASIDE, not thrown away.
#
# `[M]` 26 August 2026, and the test bench caught it at the first run: the first
# draft did `shift` on EVERYTHING inside this loop, ⇒ when `install` then
# went to read `$1` there was nothing left and it fell back on the default.
# ⛔ Result: `install pre-commit` **installed `pre-push`**, and said «OK».
# ⚠ That is, the hook did something different from what was asked and reported
#   success — the same error family as `LESSONS.md` §1.46, and this time
#   inside the hook itself.
RESTO=()
while [ $# -gt 0 ]; do
	case "$1" in
	--dry-run)    DRY_RUN=1 ;;
	--family) REQUESTED_FAMILY=${2:-}; shift ;;
	# ⛔⛔ AND ONE CAN ASK FOR A SINGLE BOX, and it is a necessity, not a luxury.
	#    `[M]` 26 August 2026: the `all` family runs the PRODUCT meshes on
	#    all four desktops, ⛔ and back then the product could start
	#    ONE: a run that for three quarters does not judge costs an hour and teaches
	#    nothing.  ⚠ Today (21 Sep 2026) it starts THREE — gnome, kde and xfce, xfce
	#    with the image only — and lxqt stays out (`11-product-capabilities.sh`).
	#    ⭐ The option is still useful: a single box costs a quarter.
	# ⚠ And NO «if the desktop is gnome» is put inside the families: that
	#   would be a per-compositor exception in disguise (`DECISIONS.md` §5.1-bis).
	#   ⭐ Here it is whoever launches who says which box to run on, and it stays written
	#     in the log.  ⛔ What the product can do on each is NOT
	#     decided here: it is in `11-product-capabilities.sh`, by capability.
	--box)  KNOWN_DESKTOPS=${2:-}; REQUESTED_BOX=${2:-}; shift ;;
	--trigger)  TRIGGER=${2:-mano}; shift ;;
	# ⚠ The name of the remote half's unit — it serves to run two runs
	#   together without stepping on each other's unit and log.  ⛔ It does not decide what runs.
	--unit)    REMOTE_UNIT=${2:-$REMOTE_UNIT}; shift ;;
	# ⚠ `install … --here-only`: the installed hook runs ONLY the laptop
	#   half.  ⛔ It is a declared fallback, not the default — see
	#   `install`, where it is written what it costs.
	--here-only) HERE_ONLY=1 ;;
	*)          RESTO+=("$1") ;;
	esac
	shift
done
set -- "${RESTO[@]+"${RESTO[@]}"}"

# ⛔ Now that we know whether the family was asked for by name, we can say whether the
#    repository was really needed.
if [ -z "$ROOT" ] && [ -z "$REQUESTED_FAMILY" ]; then
	ko "I am not inside a git repository, and no family was asked for by name"
	ko "⇒ I have no way to DECIDE what to run (--family <nome> does not need it)"
	exit 2
fi

case "$ACTION" in

decide|run)
	mapfile -t LIST < <(changed "$TRIGGER")
	if [ -n "$REQUESTED_FAMILY" ]; then
		FAMILY="$REQUESTED_FAMILY"
		REASON_TEXT="asked for by name"
	else
		FAMILY=$(decide_family LIST)
		REASON_TEXT=$(why_family "$FAMILY")
	fi

	log "The hook — trigger: $TRIGGER"
	inf "files changed: ${#LIST[@]}"
	for f in "${LIST[@]:0:12}"; do inf "  · $f"; done
	[ ${#LIST[@]} -gt 12 ] && inf "  … and $(( ${#LIST[@]} - 12 )) more"
	inf "family: ${FAMILY%%:*}   ⇐ $REASON_TEXT"
	[ "${FAMILY%%:*}" = works ] && inf "ceiling: ${FAST_CAP}s (⛔ and if it overruns tests are cut, the ceiling is not raised)"

	if [ "$ACTION" = decide ]; then
		exit 0
	fi

	if [ "${FAMILY%%:*}" = nothing ]; then
		inf "⭐ nothing starts — and it is not laziness: a hook that runs when"
		inf "  it is not needed is a hook that someone will switch off"
		exit 0
	fi

	# ⛔ THE BOXES BELONG TO ONE BENCH AT A TIME (29 Sep 2026): every mesh clears out
	#   ALL the `c<n>u<n>` tenants ⇒ a push during a run of the suite
	#   deleted its newly born tenants (`[M]` «user unknown», 04:28, 04:40 and
	#   04:42 of 29 Sep: 4 FAIL and 36 BLOCKED).  The same lock as 15-round.py and
	#   16-climb.py; the PAPERS do not touch the boxes and do not ask for it.  If a
	#   long bench is in progress the hook says NO and the push waits for it to end.
	#   ⚠ Without the lock `clear_out_tenants` touches nothing: it is the same
	#   variable, REMOTIX_KEPT_BOXES, that says «the boxes are ours».
	if [ "${FAMILY%%:*}" != papers ] && [ -z "${REMOTIX_KEPT_BOXES:-}" ]; then
		# ⚠ not in /run/lock («sticky»: root does not reopen nicfio's file, `[M]`)
		BOX_LOCK=/media/REMOTIX/rete11/.scatole.lock
		exec 9<>"$BOX_LOCK" || { ko "I cannot open $BOX_LOCK"; exit 2; }
		chmod 666 "$BOX_LOCK" 2>/dev/null
		if ! flock -n -x 9; then
			ko "the boxes are already held by another bench ($(head -c 200 "$BOX_LOCK" 2>/dev/null || echo ?)):"
			ko "⇒ the hook does not start, or it would clear out its tenants. Try again when the bench is over."
			exit 1
		fi
		: > "$BOX_LOCK"
		printf "11-hook %s pid %d" "${FAMILY%%:*}" $$ >&9
		export REMOTIX_KEPT_BOXES="11-hook"
	fi

	SECONDS=0
	case "${FAMILY%%:*}" in
	works)      log "family FUNZIONA"; family_fast ;;
	# ⛔ AND THE LINE THAT IS PRINTED SAYS THE REAL COST.  Here it said
	#    «C11-C14 + C10, which starts nothing»: ⛔ it was the same false
	#    promise as the comment, but **printed**, that is seen by someone at the
	#    exact moment it mattered.
	papers)         log "the PAPERS — C16 only  ⭐ [M] 0,79 s, and it starts nothing"; family_papers ;;
	net)          log "the NET — C10, C11, C12, C13, C15  ⭐ [M] ~11 s, and none starts a session"; family_network ;;
	whole-net)   log "the NET **PLUS C14** — ⛔ [M] ~800 s, and it takes the FOUR boxes"; family_full_network ;;
	all)         log "EVERYTHING — before closing a phase"; family_all ;;
	suite)         log "the FUNCTIONAL SUITE — 4 desktops x 2 real browsers + technical layer, ⛔ ~2 hours"; run_mesh "SUITE" false RUN_SUITE ;;
	new-desktop) family_new_desktop "${FAMILY##*:}" ;;
	*)             ko "unknown family: $FAMILY"; exit 2 ;;
	esac
	DURATION=$SECONDS

	# ⭐ THE AGE GUARD — after the stopwatch, on purpose (see
	#   `box_guard`): one line if a box is old, never a red.
	# shellcheck disable=SC2086
	case "${FAMILY%%:*}" in
	works|whole-net|all) box_guard $KNOWN_DESKTOPS ;;
	new-desktop)              box_guard "${FAMILY##*:}" $KNOWN_DESKTOPS ;;
	esac

	# ⛔ «gave red» means OUTCOME 1 — a judgement.  ⚠ 3 is NOT a
	#    red (§4.5), and counting it as one would make C13 green by mistake.
	RED=false
	FAULT=false
	printf '%s' "$executed_json" | grep -q '"outcome":1' && RED=true
	printf '%s' "$executed_json" | grep -q '"fault_grafted":true' && FAULT=true

	EXCEEDED=false
	if [ "${FAMILY%%:*}" = works ] && [ "$DURATION" -gt "$FAST_CAP" ]; then
		EXCEEDED=true
	fi

	write_log "${FAMILY%%:*}" "$TRIGGER" "$EXCEEDED" "$DURATION" "$RED" "$FAULT" "${LIST[@]}"

	log "outcome of the run"
	inf "duration: ${DURATION}s"
	if [ "$EXCEEDED" = true ]; then
		ko "⛔ IT OVERRAN THE CEILING: ${DURATION}s against ${FAST_CAP}s"
		inf "⇒ §5.1: tests are CUT, the ceiling is not raised.  ⚠ And this is"
		inf "  now an [M], no longer a [?]: the number is in the log"
	fi
	if [ "$DRY_RUN" = 1 ]; then
		inf "⚠ DRY run: it measured nothing, and the log line carries"
		inf "  «secco: true» — ⛔ C12 and C13 throw it away, and they must"
		exit 0
	fi
	if [ "$RED" = true ]; then
		# §5.2, the red policy: red in FUNZIONA BLOCKS.
		ko "⛔ RED — §5.2: it is repaired before going on, it is not filed away"
		inf "  as «we will see».  ⚠ And an intermittent red IS a red:"
		inf "  the test is not repeated hoping for green"
		exit 1
	fi
	ok "no red"
	exit 0
	;;

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ `remote` — THE WHOLE RUN, on the two machines
#
# ⛔⛔ AND THE ORDER OF THE STEPS IS NOT FREE: first THERE, then HERE.
#
# The remote half writes its line on the test machine; that line must
# be able to be appended to the log here, and `11-register-merge.py` appends
# **only what is newer than the most recent line already present**.
# ⇒ If the local line were written first, it would be more recent than the
#   remote one, ⛔ **and the remote line would never get in** — that is the run on the
#   boxes would really have run and the memory would know nothing of it.
# ⇒ So: we run over there, bring back, and **only at the end** write the
#   line here, which is the last one in time order too.
# ═══════════════════════════════════════════════════════════════════════════
remote)
	# ⛔ This is the half that DECIDES: without a repository it has nothing to look at.
	if [ -z "$ROOT" ]; then
		ko "«remote» is launched from the LAPTOP, where the repository is"
		ko "⇒ the repository is not here: if this is the test machine, the"
		ko "  command is «gira --family <nome>», and the laptop launches it"
		exit 2
	fi
	SSHPW="$ROOT/fondamenta/strumenti/sshpw.py"
	if [ ! -f "$SSHPW" ]; then
		ko "I cannot find $SSHPW: without it the test machine cannot be reached"
		exit 2
	fi

	mapfile -t LIST < <(changed "$TRIGGER")
	if [ -n "$REQUESTED_FAMILY" ]; then
		FAMILY="$REQUESTED_FAMILY"
		REASON_TEXT="asked for by name"
	else
		FAMILY=$(decide_family LIST)
		REASON_TEXT=$(why_family "$FAMILY")
	fi

	log "The hook, THE TWO HALVES — trigger: $TRIGGER"
	inf "decides HERE ($HOST_WHERE, where the repository is)"
	inf "runs THERE  ($NETWORK11_REMOTE, where the boxes and the card are)"
	inf "files changed: ${#LIST[@]}"
	for f in "${LIST[@]:0:12}"; do inf "  · $f"; done
	[ ${#LIST[@]} -gt 12 ] && inf "  … and $(( ${#LIST[@]} - 12 )) more"
	inf "family: ${FAMILY%%:*}   ⇐ $REASON_TEXT"

	if [ "${FAMILY%%:*}" = nothing ]; then
		inf "⭐ nothing starts, neither here nor there — and it is not laziness: a hook"
		inf "  that runs when it is not needed is a hook that someone will switch off"
		inf "  ⇒ ⭐ and it is also the reason why the price of this road is NOT"
		inf "    «every push becomes slow»: the pushes that touch only the"
		inf "    documents cost **zero seconds**"
		exit 0
	fi

	SECONDS=0

	# 1 · THERE — the real meshes, on the boxes
	log "the half OVER THERE — the boxes and the card"
	meta_remote "${FAMILY%%:*}" "$TRIGGER-remoto"
	R_SECONDS=$M_SECONDS
	annotate_remote "$R_OUTCOME" "$R_SECONDS" "$R_NOTE"

	# 2 · HERE — the meshes that want the repository
	log "the half HERE — the repository"
	meta_local

	DURATION=$SECONDS

	RED=false
	FAULT=false
	printf '%s' "$executed_json" | grep -q '"outcome":1' && RED=true
	printf '%s' "$executed_json" | grep -q '"fault_grafted":true' && FAULT=true

	# ⚠ And the ceiling is judged on the time WHOEVER WORKS WAITS — that is the whole
	#   run, there and back included.  ⛔ The line written over there carries
	#   another number, and it is right that there are two: that one says what the
	#   meshes cost, this one what the push costs.
	EXCEEDED=false
	if [ "${FAMILY%%:*}" = works ] && [ "$DURATION" -gt "$FAST_CAP" ]; then
		EXCEEDED=true
	fi

	write_log "${FAMILY%%:*}" "$TRIGGER" "$EXCEEDED" "$DURATION" "$RED" "$FAULT" "${LIST[@]}"

	log "outcome of the run, both halves"
	inf "total duration (what whoever pushes waits): ${DURATION}s"
	inf "of which the remote half: ${R_SECONDS}s"
	inf "the remote half: $R_NOTE"
	if [ "$EXCEEDED" = true ]; then
		ko "⛔ IT OVERRAN THE CEILING: ${DURATION}s against ${FAST_CAP}s"
		inf "⇒ §5.1: tests are CUT, the ceiling is not raised"
	fi
	if [ "$DRY_RUN" = 1 ]; then
		inf "⚠ DRY run: it measured nothing, and the log lines —"
		inf "  the one here and the one over there — carry «secco: true».  ⛔ C12 and"
		inf "  C13 throw them away, and they must"
		exit 0
	fi
	if [ "$RED" = true ]; then
		ko "⛔ RED — §5.2: it is repaired before going on"
		exit 1
	fi
	if [ "$R_OUTCOME" = 3 ]; then
		inf "⚠ and it does not block, by declared choice: a hook that stops the"
		inf "  work because a SECOND machine does not answer is a hook that"
		inf "  someone will switch off.  ⛔ But the «I could not look» stays"
		inf "  written in the log, and §5.2 says that a repeated 3 is a fault"
		exit 0
	fi
	ok "no red, neither here nor there"
	exit 0
	;;

install)
	WHICH=${1:-pre-push}
	case "$WHICH" in
	pre-commit|pre-push) : ;;
	# ⛔ A name that is not known is NOT ignored by falling back on the default:
	#    it is refused.  Falling back would mean installing something different from
	#    what was asked and saying «OK» — the defect this file has already had.
	*) ko "unknown hook: «$WHICH» — they are pre-commit or pre-push"; exit 2 ;;
	esac
	# ⚠ And the choice of the default is DECLARED, not obvious.
	#   §5.1 says «src/ is touched», which sounds like a commit.  ⛔ But the fast
	#   family costs up to three minutes, and three minutes at EVERY commit are
	#   exactly the thing §5.1 itself says makes a hook get switched off.
	#   ⇒ Default `pre-push`: one pays once per push instead of once
	#     per commit.  Whoever wants the other asks for it by name, and knows why.
	FOLDER=$(hooks_dir)
	[ -d "$FOLDER" ] || mkdir -p "$FOLDER"
	# ⚠ It was called `HOST_WHERE`, and it was renamed: `HOST_WHERE` is now the name
	#   of the machine, and it ends up in every log line.  ⛔ Two variables
	#   with the same name in a script without `local` are a value that
	#   changes under the feet of whoever is not looking.
	HOOK_PATH="$FOLDER/$WHICH"
	# ═══════════════════════════════════════════════════════════════════
	# ⛔⛔ AND WHAT THE INSTALLED HOOK CALLS IS `remote`, NOT `run`.
	#
	# `run`, here on the laptop, runs **one second** of meshes: C10, C12,
	# C13.  ⛔ The meshes that look at the product want the boxes and the
	# card, which are on the other machine — so a `pre-push` that calls
	# `run` is a hook that fires, says green, and **has not looked at the
	# product**.  ⇒ It is the net that dies silently of §4.2, made worse by
	# the log saying it is running.
	# ⭐ `remote` decides here and has it run there.
	# ═══════════════════════════════════════════════════════════════════
	if [ "$HERE_ONLY" = 1 ]; then
		HOOK_ACTION=gira
	else
		HOOK_ACTION=remoto
	fi
	{
		printf '#!/bin/sh\n'
		printf '# rete11 — installed by 11-hook.sh on %s\n' "$(date -Is)"
		printf '# ⛔ Defined BY PATH: and this file decides nothing,\n'
		printf '#    it passes the ball to the hook, which looks at the changed files.\n'
		printf 'exec bash %s %s --trigger %s\n' "$HERE/11-hook.sh" "$HOOK_ACTION" "$WHICH"
	} > "$HOOK_PATH"
	chmod 755 "$HOOK_PATH"
	ok "hook installed: $HOOK_PATH"
	inf "action: $HOOK_ACTION"
	if [ "$HERE_ONLY" = 1 ]; then
		ko "⚠ ⛔ HALF INSTALLED: with «--here-only» this hook runs"
		inf '  only C10 and its injected fault — [M] one second — and ⛔ does NOT'
		inf "  look at the product: the product meshes want the boxes."
		inf "  ⇒ C12 will say «the hook is alive» and C13 «the net can give red»,"
		inf "    ⛔ and both will tell the truth having looked at a tenth of the"
		inf "    net.  ⚠ It is used when the test machine is not there, knowing"
		inf "    what one is buying"
	else
		inf "⇒ ⭐ decides here (the repository) and runs on $NETWORK11_REMOTE (the boxes)"
		inf "⇒ and now C12 can say whether it is alive"
	fi
	;;

installed)
	FOLDER=$(hooks_dir)
	LOCATED=0
	for q in pre-commit pre-push; do
		D="$FOLDER/$q"
		if [ -f "$D" ] && grep -q '11-hook.sh' "$D" 2>/dev/null; then
			if [ -x "$D" ]; then ok "$q  ⇒  $D"; else ko "$q is there but is NOT executable: $D"; fi
			# ⛔⛔ AND IT IS NOT ENOUGH THAT THE HOOK IS THERE: WHICH ACTION it calls counts.
			#    `run`, on the laptop, is one second of meshes and does NOT look at the
			#    product.  ⇒ A hook installed like that fires, says green, and
			#    has measured nothing of the boxes: it is the net that dies
			#    silently (§4.2) with the log saying it is running.
			#    ⚠ C12 does not make this distinction — it checks that the file NAMES
			#      the hook.  ⇒ Until it does, this line says it.
			if grep -q '11-hook.sh remote' "$D" 2>/dev/null; then
				inf "  ⭐ it calls «remote»: decides here, runs on the boxes"
			elif grep -q '11-hook.sh run' "$D" 2>/dev/null; then
				ko "  ⚠ it calls «run»: here only the repository half runs"
				inf "    ⇒ the product meshes do NOT run.  To wire them:"
				inf "      bash 11-hook.sh install $q"
			fi
			LOCATED=1
		fi
	done
	[ $LOCATED -eq 0 ] && ko "the hook is NOT installed in $FOLDER"
	printf '\n'
	if [ -f "$LOG" ]; then
		inf "log: $LOG ($(grep -c . "$LOG") lines)"
	else
		ko "⛔ no log: the hook has NEVER run"
	fi
	;;

log)
	N=${1:-10}
	case "$N" in ''|*[!0-9]*) N=10 ;; esac
	[ -f "$LOG" ] || { ko "no log: the hook has never run"; exit 1; }
	tail -n "$N" "$LOG"
	;;

*)
	sed -n '2,14p' "$0"
	exit 2 ;;
esac
