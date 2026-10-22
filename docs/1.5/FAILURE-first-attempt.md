# REMOTIX 1.5 — declared a failure (19 Oct 2026)

The 1.5 effort in this repository (13–19 Oct 2026) was stopped and declared a failure by the project owner.
**Nothing here is a release.** The working version is **1.0.0** (tag `v1.0.0`). The last 1.5 build,
1.4.99-13, was never tagged.

## What 1.5 was meant to be

1.0 plus the hardening decided in [DECISIONS.md](DECISIONS.md) §11: small fixes, no `/diary`, render-node
permission at first login, QUIC Retry + Stateless Reset, QUIC connection limits, protected login page, mute
«server full» messages, `pam_faillock`, fuzzing, and a non-root network side (§11.11, §11.50).

For 1.5 the owner **lowered two requirements** of 1.0 (§11.51): the maximum resolution is **3K** (1.0 aimed at
4K, canvas up to 4096 px wide), and at most **8 users** per machine — or the highest number that still works well.

## Why it failed

- **Slower than 1.0.** The final pair-load run (18 Oct 2026, run `20261018-195446`, Intel and Radeon together,
  users 1→8 × 10 min per desktop) was judged a step back from 1.0.
- **The benches and the test suite were not trustworthy.** They broke several times and their bugs were
  mistaken for product results: GNOME measured on the Radeon only, a false «host not quiet» stop, climbs
  killed mid-run, a smoke test BLOCKED by its own leftovers.
- **The AI assistant's work (Claude Code).** The 1.5 code, the benches and the test suite were written and run by
  Claude Code, with many agents in parallel, many branches and fixes on top of fixes. Its failures cost the owner
  about a week and **~500 € of extra credits thrown away**, without a result better than 1.0.

## Lessons for any restart

1. Start again from `v1.0.0`, not from this code.
2. Build one small bench first and validate it on 1.0 (two runs that agree) before measuring anything else.
3. One security point at a time, each measured A/B against 1.0; a point that makes it slower does not go in.
4. No parallel agents; an estimate and the owner's OK before each step.

## State of this repository

Kept as a read-only archive. `main` is the last 1.5 state (load suite included) and carries the tag
`1.5-scartata`. All other branches were deleted on 19 Oct 2026; older history stays reachable through the tags.
