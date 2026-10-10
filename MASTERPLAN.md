# MASTERPLAN — what is done AFTERWARDS

*Opened on **25 Aug 2026**, by decision of the user:*

> *«Per gli altri DE non ci portiamo dietro questo buco, per GNOME potremmo fare una manutenzione
> evolutiva al termine del progetto, insieme all'integrazione di altre funzioni. Potrebbe essere
> utile creare un documento `MASTERPLAN.md` dove annotare tutte queste cose da fare al termine del
> progetto.»*

⇒ The decision is in [`DECISIONI.md` §0.4](DECISIONI.md).

---

## What this document is — and what it is NOT

**It is** the list of the things that will be done **when the product is finished**: improvements, choices
deferred on purpose, features that were not in the initial pact.

⛔ **It is not**:

| | |
|---|---|
| the decision register | that is [`DECISIONI.md`](DECISIONI.md), and every entry here **refers** there instead of copying |
| the list of open questions | that is `DECISIONI.md` **§7** — there are the holes in the *thinking*, here the work of *afterwards* |
| the phase plan | that is [`PIANO.md`](PIANO.md). ⛔ **If something must happen BEFORE the end, it does not belong here: it belongs there, with its phase** |
| a list of faults | a fault does not wait for the end of the project. If it is broken it is cured, and if it is not cured it is declared in the phase |

---

## ⛔⛔ THE RULE THAT KEEPS THIS DOCUMENT STANDING — and it is not a formality

> ### Every entry must say **what it costs never to do it, EVER**.

⛔ **A list of things to do afterwards is the drawer where things go to die.** Everything ends up in it, it
grows, nobody rereads it, and at some point looking at it only causes anxiety — and a document that causes
anxiety is no longer opened.

⇒ ⭐ **The cost of «never» is the only information that is really needed**, because it is what separates *«must be
done»* from *«would be nice»*, and that choice is made by the user, not by whoever writes the entry.

⚠ And the reverse, which is worth as much as the rule: **an entry whose cost of «never» is ZERO is deleted**.
It is not kept out of respect: it is removed, and the document stays short enough to be reread.

---

## The template of an entry

```markdown
### M<n> · <title in plain words>

**What it is**            two lines, without jargon
**Where it comes from**        the phase and the document where it was born, with the date
**What it costs if it is NEVER done**   ⛔ the line that decides everything
**What is needed first** the measurement or the test that makes the choice informed
**How much it weighs**          `[?]` until it has really been looked at
```

---

# The entries

## M2 · ⚠ QVBR has never been switched on, and the test that would be needed has not been done

**What it is.** A different way of making the encoder work. Today it is **off**, and the factory
numbers apply (ceiling 10, reserve 0.5).

**Where it comes from.** Phase 10, `fasi/10-multi-tenant-e-il-budget.md` **§10-bis**: two decisions **not
taken**, with the defaults in force.

**What it costs if it is NEVER done.** ⭐ **On a single user, nothing**: the regulator already does its
job, and phase 10 argued it. ⛔ The doubt concerns **ten together on a real wire**, and
that round has not been done: in phase 10 the clients ran inside the machine, so **the wire was
counted, not tested**.

**What is needed first.** Ten clients **on a real network**, not inside the machine. ⚠ It is a test that
needs equipment, not an afternoon.

**How much it weighs.** `[?]`

---

## M3 · ⚠ The algorithm that decides how hard to push on the wire has never been chosen

**What it is.** On the wire the transport uses **CUBIC**. ⛔ Nobody chose it: it is what was there.

**Where it comes from.** Phase 9, listed among the open things in the `README.md`.

**What it costs if it is NEVER done.** `[?]` **Nobody knows, and that is the point.** The contrast
test has never been done **because no option exposes it** — so it is not that we
tried it and it was fine: we never tried it.
⚠ On healthy networks it would probably change nothing; the suspicion concerns **dirty networks**, which
are the theme on which the user corrected the target of phase 9.

**What is needed first.** An option that exposes it, and two rounds on the same dirty wire.

**How much it weighs.** `[?]` The work is small, the payoff **uncertain**.

---

## M5 · Choosing the desktop when there is more than one on the machine

**What it is.** Today a machine has **one** desktop, and REMOTIX starts that one. With GNOME and KDE
installed together, nobody can say «KDE for me»: neither the user from the page, nor whoever administers the server.

**Where it comes from.** Phase 12, when opening KDE — `DECISIONI.md` **§4.6-duodetricies**, 18 Sep 2026:
*«la funzionalità di scelta di desktop multipli la lasciamo per una futura implementazione»*.

**What it costs if it is NEVER done.** On a machine with a single desktop, **nothing**. On one with two,
the second **cannot be reached** by REMOTIX: GNOME wins, always, for all users. ⚠ Whoever
installs KDE beside GNOME and expects to use it remotely is disappointed without a clear message —
that is why the server writes it in the log at start-up.

**What is needed first.** That the user says **who** chooses (the administrator for the machine, or each
user for themselves). ⛔ The second touches the page and the protocol, and changes `RCP.md`.

**How much it weighs.** `[?]` With the choice per machine, little: a setting. With the choice per user,
a new feature.

---

## M6 · Printing on the printer of whoever is connected (PDF only, from server to client)

**What it is.** A «REMOTIX» virtual printer on the server turns the print job into a **PDF**; the PDF reaches the
page, which opens the browser's print dialog, and whoever is connected prints on **their own** printer (the one at
home, for those working from outside; the network ones already installed on their PC, for those in the office). ⛔ **PDF only,
only from server to client** (user, 10 Oct 2026), never the other way. ⭐ **One technology for every printer**
(user: *«niente casi particolari per stampanti locali o stampanti remote: usiamo la stessa tecnologia per
entrambi i casi»*): the print goes where the device of whoever is connected knows how to print. The printers that
the administrator configures by themselves on the server (CUPS) are the system's business, not a REMOTIX feature.

**Where it comes from.** 10 Oct 2026, from the comparison with commercial products: *«trovo la condivisione di files
piuttosto pericolosa, mentre si potrebbe ragionare sul discorso stampanti»*; then *«solo pdf, server -> client. La
annotiamo nel masterplan»*. The decision is in `DECISIONI.md` §10.41; until then it was outside the project
(`SPECIFICHE.md` §12).

**What it costs if it is NEVER done.** From REMOTIX **you cannot print**: whoever works has to get the document
by other means (email, a shared folder) — that is, exactly the file transfers we do not want — or
the administrator has to configure the printers on the server by hand, one by one. For a small company it is one of the
first questions.

**What is needed first.** ⚠ Declaring to the administrator that **printing is taking a document out**: from the
print dialog the browser can also save it as PDF. ⇒ The proposed rules: **off until the administrator
switches it on**; **every print job in the log** (who, when, how many pages); the PDF is not saved on the client by
REMOTIX, it goes only to the print dialog. Then: which virtual printer (CUPS with a backend of ours, or
`cups-pdf`), a new channel in `RCP.md` for the PDF, the test on the four desktops and on the served browsers.

**How much it weighs.** `[?]` Not really looked at. Rough estimate: a small phase (virtual printer, a channel,
the print dialog in the page, the bench). ⚠ The price of use: every print goes through the browser's dialog and
asks for a click (browsers do not print silently).

---

# ⚠ The things someone might want to put here, and do NOT belong here

⛔ For the document to stay short, it must also say what it **refuses**.

| | where it goes instead | why |
|---|---|---|
| updating the server without throwing anyone out | **`PIANO.md`, phase 15** | it is already a phase. It does not wait for the end |
| the delay that exceeds the ceiling | stays `[?]` in `DECISIONI.md` §2.5 | it is a **declared quantity**, not deferred work |
| hot resizing | ⛔ **out of the product** (`DECISIONI.md` §5.1-bis) | removed **by decision of the user**. Deferring is different from removing, and this one is removed |
| the session that is born blind | **phase 11**, the acceptance test of the network | it is a **live fault**. A fault does not wait for the end of the project |
| a wrong sentence in a comment | it is fixed **at once** | it is not work: it is two minutes |

---

## How this document is kept

1. ⛔ **An entry gets in only with the line «what it costs if it is never done» filled in.** Without that
   line it is not an entry: it is a wish.
2. ⛔ **An entry whose cost of «never» becomes zero is DELETED**, and why is written at the bottom.
3. ⛔ **Entries are not renumbered** when one goes away: `M3` stays `M3` forever, or the
   references from other documents point into the void.
4. ⚠ **This document decides nothing.** When an entry is tackled, the decision goes into
   `DECISIONI.md` and the work into `PIANO.md`; here the reference remains.
5. ⭐ **It is reread at the closing of every phase**, together with the `README.md` — it is the only way for a
   list of the «afterwards» not to become archaeology.

---

## The removed entries

⭐ **21 Sep 2026, decision of the user**: *«M2, M3 e M5 sono gli unici punti da conservare
nel masterplan»* (then, on 10 Oct, **M6** came in). ⇒ Removed, and the numbers are **not** reused (rule 3):

| | what it was | why it left |
|---|---|---|
| **M1** | GNOME delivers fewer frames than it is asked for (to get 60 you would have to ask it for more, and `MOVIMENTO_FPS` is a constant) | decided by the user: it is no longer work for «afterwards». The fact stays written in `DECISIONI.md` §2.5-bis |
| **M4** | two clients on the same desktop at the same time | decided by the user: it is not work for «afterwards». Invariant I2 (one seat per user) stays as it is, `DECISIONI.md` §7.3 |
