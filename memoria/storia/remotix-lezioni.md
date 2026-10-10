---
name: remotix-lezioni
description: "REMOTIX — LEZIONI.md, written on 7 Aug 2026: the lessons of the GNOME support in the form needed by whoever opens the next desktop. To be read before phase 11"
metadata: 
  node_type: memory
  type: project
  originSessionId: 1aac11ab-166c-4641-9520-e34064b18f20
  modified: 2026-08-07T21:12:00.405Z
---

Since 7 Aug 2026 the project has a fifth document: **`LEZIONI.md`**, asked for by the user
when closing GNOME — *«mettere in un documento tutte le lezioni apprese… potrebbe tornarci utile per i
prossimi DE»*.

**The division with `REFERENCE.md` is sharp and must be kept**: there **what to do with Mutter** (and half of
those rules will fall when the compositor changes), here **what stays true when the compositor changes**,
with alongside **how much it cost to learn it**.

The three sections used first when opening a new desktop:

| | |
|---|---|
| **§3** | the **eleven questions** to ask a new compositor, with the answers already known for Mutter, KWin and wlroots — and the bench tools that answer them |
| **§9** | the eight-step **recipe** to open support for a desktop |
| **§8** | the **dead ends already walked**, not to be repeated |

`PIANO.md` phase 11 declares it **binding** like §7.0 of `SPECIFICA.md`: it is read before
writing a line.

**The lesson the document puts last, and that sums them all up**: the project never
stopped on a difficult problem — it stopped every time on **a measurement that did not measure what
we believed**.

⭐ **And on the evening of 7 Aug the first KDE bench added two, §1.9 and §1.10**, which are the
proof of the lesson above:

- **a denied read is not a read that says zero.** `ls /proc/<pid>/fd | grep dri` printed
  nothing and we read it as «zero DRM nodes»: the kernel was denying the directory. Hence: a measurement that
  can say «zero» must distinguish zero from failure; **every tool wants a positive
  control**; and when read code and measurement contradict each other, **suspicion goes first to the measurement** —
  the code has no environment.
- **a permission can depend on an environment variable that nobody documents**, and before trying
  variants of your own file you turn on the log of the component that denies.

See [[remotix-prossimo-kde]] for the concrete case.

See [[remotix-metodo-documentazione]] and [[remotix-requisito-prestazione]].
