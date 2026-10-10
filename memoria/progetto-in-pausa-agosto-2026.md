---
name: progetto-in-pausa-agosto-2026
description: paused from 27 Aug to 18 Sep 2026 (surgery); RESUMED on 18 Sep with the server rebuilt from scratch; on the 28th the project moved to GitHub and the documentation was cleaned up. It resumes from KDE, with the server coming back from repair
metadata:
  type: project
---

⭐ **RESUMED on 18 Sep 2026**: server reprovisioned from scratch ([[riavvio-perde-la-chiave-ssh]]), and the first round of the net is the acceptance test.

**REMOTIX was paused from 27 Aug 2026** — Nic is having surgery. It
resumes in a few weeks. ⛔ Nothing has been left halfway: phase 11 is
closed, and the entry point is the ⏸ box at the top of `README.md`.

## What happened on 28 Aug, with the project stopped

⭐ Two things, and Nic called them *«un compito non piu' rimandabile»*:

1. **The project left the tablet.** It lives on `github.com/nic-fio/REMOTIX`,
   private. The tablet was emptied: v1 deleted, credentials deleted,
   41 → 33 GB. See [[deposito-su-github]] and [[credenziali-da-rigenerare]].

2. **The documentation was cleaned up.** 272 rotten line coordinates, 78
   blind cross-references, 36 broken links, 2 binding documents that pointed to the
   specification of v1, 4 statements that the code had already disproved, and a
   section (`DECISIONI.md` §4.6-septies) quoted by five documents and **never
   written**. ⇒ All closed, and ⭐ **the net now has `C16`**, which goes red by
   itself if a paper starts lying again — even on a documents-only commit,
   which before triggered nothing.

## When the server comes back from repair, in order

1. Redo the credentials — [[credenziali-da-rigenerare]]. ⛔ As long as they are not there,
   the 46 calls of `sshpw.py` do not reach the machine: **it is intended, it is not a
   fault**.
2. In the same round, remove the clear-text `sudo` password from the 9 benches —
   it is the only thing that forces the repository to stay private.
3. ⭐ The first round of the anti-regression net also counts as **acceptance test of the
   rebranding and of the cleanup**: neither of the two has been retested on the hardware.
4. Then the real work resumes: **phase 12, KDE** — the three reds of `C1` on
   kde/xfce/lxqt are not a defect, they are the mandate.

⚠ Still open, and not urgent: 23 benches of phase 8 were never
committed ⇒ those measurements are not reproducible. ⭐ Nic's decision: *«le
misure tienile come stanno»*. It is written in `banchi/11-scatole/11-c16-eccezioni.txt`.
