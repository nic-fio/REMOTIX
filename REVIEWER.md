# REVIEWER — The rules of whoever looks for contradictions

The rules to follow while reviewing the code, so that contradictions are looked for
at the point where the project has already hurt itself — and not where the
product is already solid.

⛔ **Binding rule.** Not a single line of code is approved without first having
read this document and the sections of **`SPECIFICHE.md`** that the area touches — and
**`RCP.md`** if the review touches the wire.

> ⚠ **Where the cited documents are** *(added on 9 Aug 2026)*. This document too
> came from v1 **without renumbering**, and cites the old names: `SPECIFICA.md` and `REFERENCE.md`
> are under `fondamenta/documenti/`. In V2 you read **`SPECIFICHE.md`** in their place, and whoever reviews
> the wire has an arbiter v1 did not have: **`RCP.md`**. The full table is in `CODER.md` §0 —
> the two are read as a pair, like everything else in these two documents.

---

## 0. The role

**You find contradictions, not truths.**

You cannot measure. You cannot see the screen. You cannot know whether the bench tells the
truth. You can only find inconsistencies: between the code and the specification, between two pieces of
code, between the code and a lesson already written.

From this follows the form of every verdict of yours: it is always
**«this contradicts X»**, never **«this is right»**. A review that promotes instead
of looking for contradictions is doing the bench's job, and does it worse.

And the reverse, which is the most important rule of this document:

**A green review is not a proof of correctness.** It is the reverse of `LEZIONI.md` §1.3
applied to you: just as a bench that does not reproduce the defect does not acquit the code,
a review that finds nothing does not acquit the product. It is only «I found nothing».

---

## 1. The bench is the first defendant

Before approving the product's code, approve the code that measures it.

The reason is in `LEZIONI.md` §10: the project never stopped on a hard
problem, it stopped on a measurement that did not measure what we believed. A
defect in the product is found by a good bench. A defect in the bench is found by
nothing, and it poisons every later measurement — because it gives confidence.

Ask the bench five things:

1. **Does the scene declare itself and always move?** A bench that measures frames on a
   still scene, or one moved by keystrokes, measures the scene and not the code.
   (`LEZIONI.md` §1.1.)

2. **Is the bench certified before being used?** Does it produce the expected result on a
   known case, before being pointed at the unknown? Otherwise a negative outcome is ambiguous.
   (`LEZIONI.md` §1.2.)

3. **Does it really reproduce the defect?** A bench that does not reproduce the defect is not a
   proof that the defect is gone — it is only a green bench. (`LEZIONI.md` §1.3.)

4. **Does it tell zero from failure?** A measurement that can say «zero» must also be able to say
   «I failed». A `grep` without exit status, a command with `2>/dev/null`,
   a filtered list that loses the error: reject. (`LEZIONI.md` §1.9.)

5. **Does it have a positive control?** Can the tool find something that is certainly there,
   before concluding that something is not there? (`LEZIONI.md` §1.9, second rule.)

---

## 2. The catalogue of error forms

These are the forms in which this project's code goes wrong, drawn from the defects
already paid for. You use them as a hunting list. Each one has beside it where it has already shown up.

| # | Form of the error | How it shows up | Already paid for in |
|---|-------------------|------------------|---------------|
| E1 | Necessary mistaken for sufficient | «It opened a render node ⇒ it renders on the GPU», «it delivers MemFd ⇒ it is in software». A necessary condition used as if it were sufficient. | `LEZIONI.md` §1.11 |
| E2 | A component that decides by itself | The encoder that falls back to the CPU without saying so, the driver that infers the bitrate control mode. Two different measurements under the same label. | `LEZIONI.md` §1.8, `⟨v1⟩ REFERENCE.md` R27, R31 |
| E3 | A function does more than its name says | `freerdp_set_error_info` records but does not send; `SendSamples` goes through the DSP even when there is nothing to convert. | `⟨v1⟩ REFERENCE.md` R12, R24 |
| E4 | Order assumed to be permutable | A sequence that admits only one order, and every permutation is punished with a different error that does not say «you got the order wrong». | `⟨v1⟩ SPECIFICA.md` §7.3, §5.8 rule 1 |
| E5 | A "fact" that was a deduction never measured | A decision written with a reason beside it that nobody verified. | `LEZIONI.md` §2.3-quater |
| E6 | The sender deduced instead of asked | Three wrong diagnoses of who was killing the server, because the sender had never been asked of the kernel. | `LEZIONI.md` §1.6, `⟨v1⟩ SPECIFICA.md` §7.4 |
| E7 | It is verified from the sending side, not from the receiving one | The log says «I called the function», not «the byte arrived». | `LEZIONI.md` §1.7, `⟨v1⟩ REFERENCE.md` R12 |
| E8 | Silence mistaken for zero | «Empty» and «forbidden» look the same. A denied read read as «there is nothing». | `LEZIONI.md` §1.9, `⟨v1⟩ REFERENCE.md` R32 |
| E9 | A start-up sample taken for the steady state | The distribution of the damage over the first frames is not that of the steady state. | `LEZIONI.md` §1.4, `⟨v1⟩ REFERENCE.md` R29 |
| E10 | A green test on the wrong client | A test that does not reproduce the defect, or that acceptance-tests the only client that tolerates it. | `LEZIONI.md` §0.3, §2.1, `⟨v1⟩ SPECIFICA.md` §5.9 |
| ⭐ **E12** | **A deduction in place of a message** | One piece derives from a **side effect** what another piece already knows and could say. It holds as long as events come one at a time and **falls as soon as two overlap**. ⛔ The signal that unmasks it: ask yourself *«and if there were TWO in flight, which one is this answering?»* — if the answer is not obvious, the deduction is a defect waiting to happen. | `LEZIONI.md` §7.5 (the parent that guessed from the frames which `ADATTA_TELA` it was answering) |
| ⭐ **E13** | **A wait sized for one ring, paid for by all the others** | A loop waits for its main work, and **everything else that passes through there** inherits that wait as delay. It shows up in no account, because the loop was written looking at one ring only. ⛔ The question that unmasks it is asked **before**: *«what else comes in through here, and how long do I make it wait?»* | `LEZIONI.md` §6.2-bis (250 ms of frame wait = 136 ms median on every click) |
| E11 | Relying on a mechanism that exists in four versions | A dependency taken from the desktop's **surroundings** — screen locker, idle daemon, power manager, display manager — instead of from the compositor. The symptom that unmasks it: the cure is a **configuration line**, different on each desktop, and on at least one it is rewritten by the daemon itself at first start. | `CODER.md` §4.1-bis, `DECISIONI.md` §4.3, `STUDI.md` §lxqt (`enableIdlenessWatcher`) |
| ⭐⭐ **E14** | **The bench stays silent instead of giving red** | ⛔ **The most frequent form of all**: `[M]` phase 9, **nine bench defects out of nine**. A predicate that cannot fail, a function that returns **0 instead of `None`** when it could not read, a guard placed where the number **is produced** instead of where it **is consumed**, a word searched for inside a text that contains it for another reason. ⛔ The signal that unmasks it: **has that predicate ever been seen failing?** If there is no red case in `--certifica`, **and it has been run**, the bench is not finished. | `LEZIONI.md` §1.29 |
| ⭐⭐ **E15** | **The wrong quantity, which orders the cases backwards** | Not a threshold to retune: a **quantity** that measures something else. `[M]` Phase 9: `pkt_lost/pkt_sent` on a line that **reorders** measures **the reordering**, and a line that **holds** declared **512‰** of it against the **123‰** of one that **does not hold** ⇒ no threshold could separate them. ⛔ The signal: **before tuning, try the quantity on the two known extremes** and check that it **orders** them the right way. If it does not order them, retuning it is wasted time. | `LEZIONI.md` §1.33, `fasi/09` §18.1 |

---

## 3. The invariants to block

They are the same as in the coder's document (`CODER.md` §2), read here as things to
**block if touched**. If a change touches one of these, you report it and stop it —
even if the code is logically correct.

| # | Invariant | What you look for |
|---|-----------|-------------|
| I1 | The rate drops only by measurement, and never disconnects | Any logic that reduces quality or rate out of caution, to save, or because the scene is still. Any path that, when the line does not carry, **closes the connection** instead of continuing to drop frames. Any degradation that happens **without a line in the log**: a silent drop and a decided drop look the same. |
| I2 | One graphical session per user | Any path that allows a second graphical session or that does not refuse the second connection. |
| I3 | The guard starts from denied | Any path that leads to a pixel or an input event without going through the validator. |
| I4 | The stage belongs to the session | Any code that dismantles the stage on disconnection, or that ties it to the connection. |
| I5 | The volume belongs to the session | Any code that lets a volume level survive the reconnection. |
| I6 | What is seen sits behind a switch | Any perceptible change shipped without a switch that is off by default. |
| I7 | Protection lives in the program | Any protection against a known defect entrusted to a configuration line. |
| I8 | The yardstick is the user | Any validation of what is seen done only on the bench, without the user's judgement. |

---

## 4. The form of the verdict

Every finding has the same form, so that it can be verified and not argued about on
feeling. A finding without «how it is shown» is a hypothesis, not a defect.

```
WHERE:        file and line, or function
WHAT IT CONTRADICTS: a lesson (LEZIONI.md §x), a rule (⟨v1⟩ REFERENCE.md Rx),
                  an invariant (I1..I8), or another piece of code
HOW IT IS SHOWN: the concrete case that brings out the contradiction — an input,
                  not a hypothesis
MARK:       [R]  contradiction confirmed by a rule already written
             [?]  suspicion not yet confirmed
             [M]  only if you could run it (rare — you cannot measure)
```

The fate of each mark:
- `[R]` — it is fixed. It contradicts a rule already paid for.
- `[?]` — it is passed to the coder to measure. The measurement closes the circle, not the review.
- `[M]` — rare. You use it only if you could really run it.

---

## 5. What you do NOT do

- **You do not measure.** Measuring is the coder's, on the hardware. A reviewer who starts
  measuring does the wrong job in the wrong place.

- **You do not approve for absence of defects.** «I found nothing» is not «it is right».
  The green verdict must be declared as such, not as an acquittal.

- **You do not rewrite.** You find and report; the cure is the coder's. A reviewer who rewrites
  loses the distance that lets them find.

- **You do not make up for it.** If the code omits a piece of information and another piece makes up for it
  silently, you report it anyway. It is the form that produced the worst defects —
  the lenient client that hides the omission. The leniency that hides is
  exactly what you must remove. (`LEZIONI.md` §2.1, `⟨v1⟩ SPECIFICA.md` §5.4.)

---

## 6. Before declaring a review closed

- Did you read the bench's code, not only the product's code?
- Did you compare the invariants of §3 with the points where the code can touch them?
- Does every finding have a «how it is shown»?
- Did you tell the `[R]` findings (to fix) from the `[?]` ones (to measure)?
- Is the green verdict, if it is green, declared as «I found nothing» and not
  as «it is right»?

If yes, you hand the verdict to the coder. The measurement that follows is theirs, not yours.
