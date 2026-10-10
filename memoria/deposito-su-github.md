---
name: deposito-su-github
description: since 28 Aug 2026 the project is called REMOTIX (no longer _V2); since 29 Aug 2026 it has NO local copy — single source github.com/nic-fio/REMOTIX, public
metadata:
  type: project
---

**The project is called REMOTIX.** The «_V2» was dropped on 28 Aug 2026: it served
to distinguish it from v1, and v1 no longer exists as a project of its own.

- ⛔ **NO local folder.** `~/Documenti/REMOTIX` was deleted on
  29 Aug 2026: «l'unica fonte di verita' e' il repository GitHub», so as not to
  have duplicates scattered on the tablet. ⇒ To work on it **you clone**.
- repository: `https://github.com/nic-fio/REMOTIX` — **PUBLIC since 29 Aug 2026**, default branch
  `fase-10-cure` (`master` is stuck at 9 Aug, it is not the working branch)
- ⚠ After every clone the hook **is not there**: `.git/hooks/` is not versioned.
  ⇒ `bash banchi/11-scatole/11-gancio.sh installa pre-push`, otherwise
  pushes go through without any check — and this time **silently**, because an
  absent hook does not exit 127: it simply is not there.

⭐ **OPENED ON 29 AUG 2026 — and the password stays inside, by choice.**

⛔ **It is NOT an open problem, and must not be proposed again.** The line
`printf 'nicfio\n' | sudo -S ...` is in **117 files** of the benches and in **62
commits** of the history, and it stays there. The test machine lives on a **closed local
network**: it cannot be reached from outside, so that password
opens nothing to anyone. Decided by the user on 29 Aug 2026.

⚠ This note said the opposite until this morning — «it stays private», «it must be
changed when the server comes back». ⛔ It was the wrong assessment, and it rested on
a risk that does not exist here.

⚠ The count of «9 files» that was written here was wrong by a factor of twelve.
`[M]` 29 Aug 2026: `git grep -Il "sudo -S" | wc -l` ⇒ **117**. ⭐ The number is
verified, not quoted from memory — this holds for every count in these notes.

⭐ **What was v1 is under `fondamenta/`** (renamed on 28 Aug 2026: «non voglio
riferimenti a cose passate»)** and it is NOT an archive, and it is NOT an archive**:
`fondamenta/strumenti/sshpw.py` (39 calls), `fondamenta/remotix-c/src` (34), `fondamenta/banco/enter.sh`
and the videos of `fondamenta/calibrazione/` are live equipment of the benches.
See [[costruire-serve-il-contenitore]] and [[riavvio-perde-la-chiave-ssh]].

⚠ **The measurement logs were not renamed**: `*.jsonl` and `*.log` still carry
«REMOTIX_V2», and they must. They are records of measurements made, and they say under what name
the product ran that day. ⭐ A log is appended to, not corrected.

⚠ **The rebranding has not been retested on the hardware** (machine under repair since
27 Aug): when the server comes back, the first round of the anti-regression net also counts
as acceptance test. The startup mark changed on both sides together —
`src/main.c` writes it, `01-b0-bersaglio`, `10-b96`, `10-b90` and `11-c9`
check it. See [[progetto-in-pausa-agosto-2026]].

⚠ Outside the repository and NOT on GitHub: `~/SERVER.ssh` and `~/.ssh/id_ed25519`,
DELETED on 28 Aug 2026: see [[credenziali-da-rigenerare]].

⛔⛔ **THE HOOK CARRIES AN ABSOLUTE PATH, and it lives OUTSIDE the repository.**
`.git/hooks/pre-push` is not versioned and contains the path written out in full:
renaming the project folder **kills it silently**, and from that moment
`git push` is REFUSED (the hook exits 127). ⚠ And with `git push --quiet` the
message is not seen: it looks like it went through, and the commit stays at home.
⇒ After every move of the folder: `bash banchi/11-scatole/11-gancio.sh installa pre-push`,
and then CHECK that the commit is on GitHub — do not trust the command's output.
