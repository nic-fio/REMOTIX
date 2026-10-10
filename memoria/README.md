# Claude's memory — repository copy

In here are the notes that Claude Code keeps on **how to work on this
project**: not what the code does (that can be reread), but the things one
learns only once and pays dearly for twice — that Nic is the director and not the
programmer, that performance is declared on the modest hardware, that a bench
is LOOKED AT before calling him, that rebooting the server loses the ssh key.

⛔ **Why it ended up in here**: it lived in `~/.claude/projects/…/memory/`,
that is outside the repository — in a place that a cleanup of the tablet takes away
without noticing. Nic's decision, 28 Aug 2026.

## How to put it back in its place on a new machine

    cp memoria/*.md ~/.claude/projects/-home-nicfio-REMOTIX/memory/

⚠ The name of that folder is derived from the project's **path**. If one
day the repository is no longer in `/home/nicfio/REMOTIX`, the
name changes: look at which folder exists under `~/.claude/projects/` and
copy there.

⚠ This is a **copy**, not the live original: when Claude writes a new note
it writes it in `~/.claude/`, not here. Every now and then it must be copied again.

`MEMORY.md` is the index — one line per note — and it is what Claude rereads
at every session.
