/* budget.h — ⭐⭐⭐ THE COMPOSITION BUDGET, phase 10 (25 Aug 2026).
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * ⛔ THE DEFECT THIS MODULE CURES
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * Until today the product **had no budget: it accepted everyone and starved
 * everyone together**.  `[M]` `fasi/10-…md` §S.2: on the saturated scene the
 * eleventh gets in with **`negati 0`**, and the first session goes from **39.60
 * to 0.96 fps** — **−97.6 %** — with **104 paired reds** against invariant
 * **I1** (*«the rate falls only on measure, and never disconnect»*) and against
 * `DECISIONI.md` §4.6-bis.
 *
 * ⭐ The yardstick of the phase was set by the director (`DECISIONI.md` §4.6-septies):
 *    *«six RDP on a modest integrated card is not a bad result»* ⇒ **the
 *    phase must not let ten in: it must STOP WHERE IT MUST, SAYING SO.**
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * ⛔ 1 · THE QUANTITY IS **COMPOSITION**, NOT ENCODING
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * `DECISIONI.md` §4.6 says *«the real limit is set by the encoder, and it is
 * measured in pixels per second»*.  ⛔ `[M]` **On this hardware it is not true**
 * (§6.11, §6.15):
 *
 *   | where it gives way   | `[M]`                                          |
 *   |----------------------|------------------------------------------------|
 *   | the bare encoder     | **1.86 Gpixel/s** in H.264 · 2.33 in HEVC      |
 *   | ⭐ **composition**     | ⛔ **0.97 Gpixel/s** — HALF, and it is `rcs0` |
 *
 * ⛔ And what saturates `rcs0` is **`gnome-shell` at 99.5 %**, while `remotix`
 *    sits at **0.00 %**: the bottleneck is something that **is not ours**, and
 *    that the budget can only **count**, not reduce.
 *
 * ⇒ The currency is the **COMPOSED PIXEL**, and it is shown: `[M]` §6.9 — at
 *   the breaking points the Mpixel/s coincide within **0.6 %** as the canvas
 *   varies, while the frames/s differ by **74.9 %**.
 *
 * ⛔ And `us_codifica` is NOT counted — the number the first design (§3.2)
 *    proposed as «the real cost»: `[M]` §6.9 it is a **DELAY, not a COST**,
 *    its curve has a fixed term twenty-five times the real one, and tuning on
 *    it **would overrate a 480p canvas by a factor of two**.
 *
 * ⭐ And the ingredients were all already in the parent's hands:
 *    `deposita_fotogramma()` (`main.c`) receives **every** frame with width,
 *    height, instant and bytes, and the child calls it **without guards** on
 *    «someone is watching» ⇒ ⭐⭐ **the parent also sees the GHOSTS** — the
 *    sessions that encode without anyone watching (§3.2), which cost the GPU
 *    as much as the others and which a count kept on RCP slots **would not see**.
 *    ⇒ No new channel between parent and child was needed: what was needed
 *      was **an accumulator**, and it is this module.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * ⛔⛔ 2 · BEFORE THE PIXELS, LOOK AT THE **DELAY**
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * `[M]` §6.9: at eight sessions the total delivered is **26.6 Mpixel/s against
 * 480** ⇒ the count on pixels would say *«there is room for five more»*
 * **while everyone sits at 1.5 fps**.  ⛔ **After the cliff the delivered
 * COLLAPSES, and a budget that looks only at pixels lies precisely when it is
 * needed.**
 *
 * ⇒ There is a gate before the sum, and the threshold is **measured, not
 *   chosen**: `[M]` the healthy steps sit at **≤ 13.1 ms**, the broken ones at
 *   **≥ 39.9 ms**, ⭐ **no overlap** ⇒ the threshold is their **geometric
 *   mean**, **22.9 ms**.  A session that delivers little **with 600 ms of
 *   delay** is *throttled*, not *idle* — and they are two facts the delivered
 *   alone does not tell apart (`LEZIONI.md` §1.31, §1.34: the mechanism next to
 *   the symptom, and here the mechanism is the DELAY, not the keyframes, which
 *   `[M]` stay at **zero** even inside the collapse, 0 out of 8 741).
 *
 * ⚠ AND THE TWO THINGS THIS THRESHOLD IS **NOT**:
 *   · **it is not universal**: it belongs to **that scene** (1080p H.264, real
 *     GNOME desktops, on i5-13500T + UHD 730).  On other hardware it must be
 *     measured again;
 *   · **it is not the quantity of the mechanism**: the delay the parent
 *     measures is an **upper bound** of the compositor's buffer hold time —
 *     prudent in the right direction, but not the same thing.
 *   ⛔ And the second half of the yardstick **does not cross the process
 *     boundary**: the compositor's «runway» is `(buffer_distinti − 2) × 16.67
 *     ms`, and `buffer_distinti` (`cattura.h`) lives **in the child**.  §6.9
 *     keeps the more prudent of the measurement and the runway; here we have
 *     the measurement only, and it is declared instead of pretending they are
 *     the same thing.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * ⛔⛔ 3 · THE RESERVE — and the WAKE-UP, which is the real hole
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * `[M]` §6.16: eight **idle** sessions admitted when they cost `[M]` **0.01 %
 * each** wake up **in 19 ms** and ask for **8 × 14.4 = 115 %**, plus the
 * incumbent: ⛔⛔ **130 % of an engine that has 100.**  Whoever was working
 * loses **95.9 %** of their rate and their delay goes **×78** (9.7 → 756 ms).
 *
 * ⛔ **And the rate regulator of phase 9 cannot remedy it**: it lives in the
 *    parent and holds back frames **already composed and already encoded**
 *    (§3.2) — that is, it acts after the GPU cost has already been paid.
 *
 * ⇒ ⭐ **The reserve is the only defence.**  The demand of whoever is inside is
 *   not what it delivers now: it is **the larger of what it delivers and a
 *   fraction `F` of its worst case** (its canvas at the maximum rate of this
 *   hardware).  An idle session does not cost zero: it costs its reserve.
 *
 * `[M]` §6.9, on the data of the climb to eleven:
 *
 *   | rule            | false NO | false YES | cap saturated | cap idle    |
 *   |-----------------|----------|-----------|---------------|-------------|
 *   | `F = 0`         |    0     |     0     |       6       | ⛔ unlimited |
 *   | ⭐ **`F = 0.5`** |  **0**   |   **0**   |     **6**     | ⭐ **10**    |
 *   | `F = 1`         |    1     |     0     |       5       |      6      |
 *
 * ⭐ **The TEN of `SPECIFICHE.md` §5.5 found again by MEASUREMENT instead of by
 *    promise** — and the overshoot on wake-up goes from **1 640×** to **2×**.
 * ⭐ `F = 0` is the «delivered» rule, `F = 1` is the «worst» rule: **it is the
 *    same rule with the knob in the director's hand** (`--riserva`).
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * ⛔ 4 · THE MARGIN IS WRITTEN ON BOTH SIDES, AND THE TWO ERRORS DO NOT COST THE SAME
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * `LEZIONI.md` §1.33:
 *
 *   **false NO**   says «it does not hold» and it did hold ⇒ **a user refused
 *                  for nothing**.  It costs **one user**.
 *   **false YES**  says «it holds» and it did not ⇒ ⛔⛔ **it starves whoever
 *                  was working**, and violates **I1**.  It costs **everyone**.
 *
 * `[M]` §6.9: the measured margin is **+1.65 %** above the highest demand that
 * held and **−13.7 %** below the lowest one that gave way ⇒ ⭐ **the margin on
 * the side that starves everyone is EIGHT TIMES the one on the side that costs
 * one user**, and it is the right direction.  ⇒ Every fallback of this module
 * goes in the **uncomfortable** direction: what is not known is counted at the
 * **worst case**.
 *
 * ⛔ And «I have not measured» is not «zero» (`CODER.md`): a session just born
 *    that has not delivered anything yet **does not cost zero** — it costs its
 *    worst case, until it is known.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * ⛔ 5 · THE BUDGET DOES NOT SELF-TUNE, AND IS BORN OFF
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * `[M]` §6.9: **before the machine has given way once, the capacity that was
 * read is a LOWER BOUND, not a ceiling** — it is *«the point where one stopped
 * trying»*.  ⇒ ⛔ **The product must not deduce its own ceiling by itself**:
 * either it is given with `--budget-mpixel-s N`, or **there is no budget**.  A
 * ceiling deduced from a climb that never made the machine give way would
 * refuse users for a number nobody has verified.
 *
 * ⭐ And by `CODER.md` **I6** — *what changes what the user SEES stays behind a
 *    switch that is off until they have looked at it* — the budget is born
 *    **OFF** (`--budget-mpixel-s 0`).  This module **acquires a function**, it
 *    does not cure an appearance defect: a rejected user is the most visible
 *    thing a server can do, and it does not turn itself on.
 */
#ifndef BUDGET_H
#define BUDGET_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* ⛔⭐ THE MAXIMUM RATE PER SESSION — `[M]` **39.54 fps**, and it is not a
 *     choice: it is what **one session alone** delivered on this hardware,
 *     first step of the climb to eleven (§6.9, `10-b99-misure.jsonl`, scene
 *     `satura`, 1920×1080, H.264, i5-13500T · Intel UHD 730 `renderD128`,
 *     phase 9 cures on).
 *
 * ⛔⛔ IT IS THE SECOND NUMBER OF THE MACHINE, and it is measured **together**
 *      with the first: `--budget-mpixel-s` says **how much work** the machine
 *      holds, this one says **how much one session alone asks for when it
 *      pushes**.  ⇒ Whoever takes the product to other hardware and moves one
 *      **measures the other again too**, or the reserve becomes a fraction of
 *      a worst case that does not belong to that machine.  ⚠ It has no option
 *      of its own because the phase wanted **three** and no more (§8.1); the
 *      value in force ends up in the startup line together with the others, so
 *      it is not a hidden number.
 *
 * ⚠ And it is used ONLY for the worst case, never for the delivered: the
 *   delivered is MEASURED, frame by frame, and never estimated. */
#define BUDGET_RITMO_MAX_FOT_S 39.54

/* ⛔⭐ THE DELAY THRESHOLD — `[M]` **22.9 ms**, geometric mean between the worst
 *     13.1 ms of the HEALTHY steps and the best 39.9 ms of the BROKEN ones,
 *     which ⭐ **do not overlap** (§6.9).  ⚠ It belongs to **that scene**: see
 *     the box at the top, point 2. */
#define BUDGET_RITARDO_AFFANNO_MS 22.9

/* ⭐ The knob of `--riserva`, and its measured default (§6.9): at 0.5 the
 *    predictor makes **0 false yes and 0 false no** on the data available. */
#define BUDGET_RISERVA_PREDEFINITA 0.5

/* ⛔ The tolerance on the comparison, and it has a precise reason: the capacity
 *    is the **MEASURED peak**, that is a state that was seen to hold.
 *    Comparing it with a bare `≤` would refuse **precisely that state** as soon
 *    as the arithmetic moves the third digit — a false NO by rounding.
 * ⭐ 1 % is the declared repeatability of the yardstick (`[M]` ±0.6 %, §6.1),
 *    and it is **seventeen times smaller** than the gap between the peak and
 *    the first point that gave way (+17 %): the margin stays entirely on the
 *    prudent side. */
#define BUDGET_TOLLERANZA 0.01

/* ⛔ The outcome, and there are THREE.  ⚠ `BUDGET_NON_SO` is not
 *    `BUDGET_NON_REGGE`: it is «I could not measure», and whoever receives it
 *    **admits** and writes the line.  A budget that refused for not having
 *    been able to measure would make the user pay for a fault of ours. */
enum budget_esito {
	BUDGET_REGGE,
	BUDGET_NON_REGGE,
	BUDGET_NON_SO,
};

/* ⭐ It is turned on once only, at startup, with the numbers of the command line.
 *
 *   `capacita_mpixel_s`  `--budget-mpixel-s`, **0 = OFF** (I6);
 *   `riserva`            `--riserva`, 0..1 (§6.9);
 *   `tela_l`, `tela_a`   the stage canvas, that is the **upper bound** of the
 *                        canvas any session can obtain: it serves as a declared
 *                        fallback for whoever has not delivered anything yet,
 *                        and goes in the uncomfortable direction. */
void budget_accendi(double capacita_mpixel_s, double riserva, uint32_t tela_l,
                    uint32_t tela_a);

/* ⛔ How many slots the tenant table will have — called **before**
 *    `budget_accendi()`, with the session cap in force.  ⚠ After switch-on it
 *    does nothing: the table is already allocated, and changing its size on
 *    the fly would mean losing the delivered of whoever is there. */
void budget_caselle(int quante);

/* ⭐⭐ THE STARTUP LINE, and it is written **ON AND OFF**.
 *
 * ⛔ And it carries the THREE values in force with the **option name next to
 *    the number** — `--budget-mpixel-s N`, `--tetto-sessioni N`, `--riserva F` —
 *    and it is not pedantry of form: whoever reads the log after a `0x06` must
 *    be able to know **on which numbers** that no was decided, and a bench that
 *    tuned its own oracle on a number different from the one in force would
 *    produce false yeses and false noes **of its own**, not of the product.
 * ⚠ The cap comes from outside (`rcp_tetto()`) because it is not the budget's:
 *   it is the administrative limit, and it sits in the same line only because
 *   the reader needs the three together. */
void budget_riga_avvio(int tetto_sessioni);

/* ⛔⭐ THE COUNT OF THE DENIED, and it is written at EVERY verdict — even when
 *     the budget is OFF, and that is precisely the case that matters.
 *
 *     `[M]` §S.2: the defect can be read in two words — *«the eleventh gets in
 *     with **`negati 0`**»*.  ⇒ A bench must be able to read that number **at
 *     every step**, and reading it **zero** is the fact that proves **I6**:
 *     with the budget off the product behaves as yesterday, and denies nobody.
 *
 * ⚠ The counts are TWO and not one: `negati` are all the noes said at this
 *   door (full table included), `negati_budget` are the `0x06` only.  Adding
 *   them up would pass off a configuration fault as capacity. */
void budget_riga_verdetto(const char *utente, bool ammesso, uint8_t motivo,
                          int tetto_sessioni, const char *perche);

bool budget_acceso(void);

/* ⭐⭐ THE ACCUMULATOR — called for **every** frame of **every** child, from
 *     `deposita_fotogramma()`.  ⛔ Without guards on «someone is watching»: it
 *     is precisely how the count sees the **ghosts** of §3.2.
 *
 * `istante_us` is the `CLOCK_MONOTONIC` stamped **by the child at the instant
 * of capture** — the clock is machine-wide, so comparable here.  ⚠ The delay
 * that comes out of it is *capture → parent*, that is an **upper bound** of
 * the hold time: prudent in the right direction. */
void budget_deposita(const char *utente, uint32_t larghezza, uint32_t altezza,
                     uint64_t istante_us);

/* ⛔ The count is opened, filled with **whoever is inside**, and closed with the
 *    verdict on the newcomer.  ⚠ Three calls and not one because «whoever is
 *    inside» is known by the **stage** table (`figlio.c`), not by this module:
 *    tying them together would mean the budget knows the children, and then
 *    one day it would decide something about them. */
struct budget_conto {
	uint64_t ora_us;
	bool orologio;          /* ⛔ false = I did not read the time: I do not judge */
	double domanda;         /* Mpixel/s already committed */
	int quanti;
	/* ⛔ The first throttled one found: it is the delay gate, and it closes
	 *    the count **before** the sum. */
	char strozzato[257];
	double strozzato_ms;
	/* ⚠ How many of those inside were counted at the worst case because they
	 *   had not delivered yet: it goes into the line, or the demand number
	 *   looks like a measurement when it is a fallback. */
	int al_peggiore;
};

void budget_conto_apri(struct budget_conto *c);
void budget_conto_dentro(struct budget_conto *c, const char *utente);

/* ⭐ The verdict on the newcomer.  `tela_l`/`tela_a` are the **ceiling** of the
 *    canvas it will obtain — `min(stage canvas, the client's video.misura_massima)`
 *    — and the real canvas is decided only at `SESSIONE`, that is later.
 *    ⇒ The ceiling is counted: uncomfortable direction.
 *
 * `perche` receives the sentence that goes into the **body of the CONGEDO** and
 * into the log: it must be readable by a user, not by whoever wrote the code. */
enum budget_esito budget_conto_verdetto(struct budget_conto *c,
                                        const char *nuovo, uint32_t tela_l,
                                        uint32_t tela_a, char *perche,
                                        size_t perche_cap);

#endif /* BUDGET_H */
