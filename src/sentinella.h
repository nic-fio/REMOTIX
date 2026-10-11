/*
 * sentinella.h — who watches the LOCAL graphical sessions, and on whose behalf.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE JOB, in one line
 *
 * `SPECIFICHE.md` §5.1 promises four behaviours, and two of them never
 * had anyone doing them:
 *
 *   · the user has a LOCAL graphical session and opens a remote one
 *       ⇒ the remote one is REFUSED, reason `0x05 ALREADY_ACTIVE_LOCALLY`;
 *   · the user has a live remote one and opens a LOCAL one
 *       ⇒ ⛔ the LOCAL one WINS: the remote one is closed, `0x04 LOCAL_SESSION_PREVAILED`.
 *
 * ⛔ The two codes have been in `rcp.h` since 9 August 2026 and **no line of
 *    any `.c` sent them**: it is the same fault shape as finding B-7
 *    (`RCP_SERVER_CLOSING` defined and with no sender), where whoever was
 *    connected waited the thirty seconds of silence and read «network
 *    error».  This file is the missing sender.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ WHAT A «LOCAL GRAPHICAL SESSION» IS — and the obvious draft is WRONG
 *
 * The criterion that comes to mind is *«graphical `Type` and `Remote = false`»*.
 * ⛔ With that we would refuse ourselves, on the first day.
 *
 * `[R]` **We do not call `pam_set_item(PAM_RHOST, …)` anywhere** —
 * `autenticazione.c` does `pam_start` and nothing more — so `pam_systemd` creates
 * OUR sessions without a remote host, and logind marks them `Remote=no`.  One
 * of our sessions would pass for local, and the second user who connects
 * would be turned away with `0x05` by itself.
 *
 * ⭐ **The discriminant is the SEAT, not `Remote`.**  A local session sits on a
 *    seat (`seat0`): a real screen, keyboard and mouse are attached
 *    to that machine.  Our headless one has no seat — and it is the
 *    SAME property on which Mutter decides `is_headless()` (`DECISIONI.md`
 *    §4.3-bis).  ⇒ The two things stand together: the day our
 *    session had a seat, we would lose headless **and** refuse
 *    ourselves, and the log would say both things.
 *
 * ⚠ `Remote` is checked anyway, as a second belt: when `PAM_RHOST`
 *   is set (phase 5, `FASI.md` §05-la-sessione §1.4) it will become true for
 *   ours, and then two independent criteria will say the same thing.
 *
 * ---------------------------------------------------------------------------
 * ⚠ WHY SYNCHRONOUS, and not a thread as in v1
 *
 * v1 (`fondamenta/remotix-c/src/sentinella.c`, 307 lines) kept a `GMainLoop` in a
 * thread of its own, with `SessionNew`/`SessionRemoved`.  ⛔ There the server ran INSIDE
 * the session of ONE person and the question was «is there a local one?»; here the server
 * is a system one and the question is «is there a local one **of this user**?», which
 * is asked at two moments only:
 *
 *   · when someone ATTACHES        — once per session, the cost does not show;
 *   · while someone IS attached    — a re-check every couple of seconds.
 *
 * ⇒ A synchronous call with a SHORT wait costs less than a thread and a
 *   mutex, and does not add a second thread to a program that has only one by
 *   choice.  ⛔ But the short wait is mandatory: this `poll` loop is the
 *   same one that delivers the frames, and `LEZIONI.md` §6.2-bis says that
 *   *a wait that protects one link is a delay for all the others*.
 */
#ifndef REMOTIX_SENTINEL_H
#define REMOTIX_SENTINEL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct sentinel sentinel;

/* Opens the connection to the SYSTEM bus (logind is not on the session
 * one).  ⛔ Returns NULL if the bus is missing: then the rule of §5.1
 * is NOT in force, and the caller writes it in the log instead of carrying on
 * as if nothing happened. */
sentinel *sentinel_open(void);

void sentinel_close(sentinel *s);

/*
 * «Does this user have a LOCAL graphical session, right now?»
 *
 * `description` — if not NULL — receives which session it is, for the
 * server log: id, type and seat.  ⛔ It never ends up in the body of a
 * farewell (§8.2).
 *
 * ⚠ A logind error answers `false`, and writes a line: «I don't know» and «there
 *   isn't one» are two different facts, and locking everyone out because logind does not
 *   answer would punish those who did nothing wrong (invariant I1).
 */
bool sentinel_local(sentinel *s, const char *user, char *description,
                       size_t how_much);

/*
 * ⭐⭐⭐ «WHICH OF THESE USERS HAVE A LOCAL GRAPHICAL SESSION?» — ONE
 *       QUESTION FOR ALL, and it comes from a MEASURED defect.
 *
 * ⛔⛔ THE DEFECT THIS FUNCTION EXISTS TO REMOVE — finding P4 of
 *      `fasi/10-multi-tenant-e-il-budget.md` §8.2, measured in §6.13.
 *
 *      The re-check of §5.1 (`wt_watch_locals()`) called `sentinel_local()`
 *      **once per attached tenant**, and each call is a SYNCHRONOUS
 *      round trip on D-Bus inside the same `poll` that delivers the frames.
 *      `[M]` 25 August 2026: the calls per re-check are **1 · 3 · 5 · 7** at
 *      N = 1/3/5/7 — linear in the tenants — and what governs the damage is the
 *      PRODUCT `P = N × D`, where D is how long logind takes.
 *      ⛔ The frontier shrinks as **1/N** and crosses the **300 ms** that
 *         `WAIT_MS` below already allows itself at ~4 tenants: at **N=7 with
 *         D=286 ms** every desktop collapses to **1.3 frames/s with a p95 of two
 *         seconds**, ⛔⛔ *and not a line is written*, because nobody
 *         disconnects.  The SILENT degradation, which for `CODER.md` §1-bis weighs more
 *         than the frames.
 *
 * ⭐⭐ AND THE CURE LIES IN THE NUMBERS, not in elegance — `[M]` §6.13:
 *
 *      · `ListSessions` costs **2.4-2.6 ms** and ⛔ **does NOT grow with the number of
 *        logind sessions** (from 63 to 72 the median GOES DOWN, slope −34.6 µs
 *        per session).  ⇒ The cost is not in the call: it is in MAKING IT N TIMES.
 *      · `ListSessions` returns **ALL** the sessions of the machine.
 *        ⇒ A single answer already contains every tenant's.
 *
 *      ⇒ The cost goes from `N × D` to **`D`**, and it is a change of shape, not
 *        a mitigation: there is no cache to expire and no round-robin
 *        to tune — things that would have added a second truth about
 *        «now» (`LEZIONI.md` §1.9) for a defect that is closed at the root.
 *
 * ⚠ THE COST THAT REMAINS, declared: the sessions with a SEAT must be opened one
 *   by one (`GetAll` on the properties) to know whether they are graphical.  ⛔ But those
 *   are the **machine's local** sessions — on a headless machine they are
 *   zero, and they are independent of the number of our tenants anyway.  ⇒ The
 *   term that grew with N is gone; this one was never there.
 *
 * `users`   — the names to look for, `amount` in all.  ⚠ They may repeat: the
 *              answer is by POSITION, so the caller does not have to deduplicate.
 * `local`   — a vector of `amount` booleans, filled by this function.
 * `which_ones`    — if not NULL, `amount` slices of `width` bytes each, each
 *              with the description of the session found (for the LOG:
 *              §8.2 forbids telling the client facts about other people's sessions).
 *
 * ⛔ Returns how many it found with a local one.  ⚠ If logind does not answer,
 *    it returns 0 and sets everything to `false` — «I don't know» is treated as «there isn't one»,
 *    which is the only choice that does not punish those who did nothing wrong
 *    (invariant I1), and it is the same one `sentinel_local()` makes.
 */
size_t sentinel_locals(sentinel *s, const char *const *users, size_t amount,
                         bool *local, char *which_ones, size_t width);

/*
 * ⭐ «IS POWER-OFF REALLY FORBIDDEN?» — `DECISIONI.md` §4.7, the check that
 * invariant I7 demands: the three belts are configuration lines, and a
 * protection that lives in a file must be **verified**, not believed.
 *
 * Asks logind `CanPowerOff`/`CanReboot`/`CanSuspend`/`CanHibernate` and
 * demands **`no`** from all four.  ⛔ «challenge» is NOT enough: it shows the
 * menu entry instead of removing it.
 *
 * ⛔⛔ THE CHILD CALLS IT, NEVER THE SERVER: `[M]` root is answered «yes»
 *     because logind looks at `CAP_SYS_BOOT` before polkit.
 */
bool sentinel_shutdown_forbidden(sentinel *s, char *detail, size_t how_much);

/*
 * ⭐ «IS MY SESSION SEATLESS?» — `DECISIONI.md` §4.3-bis, measurement M2.
 *
 * Without a seat Mutter is **headless**, and it is the only form in which the GNOME
 * screen locker does not revoke our capture and input.  ⚠ Since 15 August 2026 the session
 * is born seatless **by construction** (`figlio.c`, step 2-bis) — ⛔ but
 * «written» is not «in force» (`REVIEWER.md` E1), and this is the line that
 * verifies it AFTER startup.
 *
 * `false` also when there is no session at all: it is a WORSE case, not
 * a better one, and `which` says so.
 */
bool sentinel_without_seat(sentinel *s, char *which, size_t how_much);

/* How many calls were made, and the slowest in milliseconds — the number
 * that says whether the «synchronous» choice holds.  ⛔ It is here and not in a comment:
 * `CODER.md` §6 wants a fallback to be MEASURABLE, not believed.
 *
 * ⛔⛔ AND UNTIL 25 AUGUST 2026 NOBODY CALLED IT — side finding of
 *      §6.13.  The counter was there, the header declared why it was there, and
 *      **nothing ended up in the log**: the «synchronous» choice could be
 *      believed, not re-measured.  It is form E1 of `REVIEWER.md` — an
 *      instrument that exists and does not speak is worse than a missing instrument,
 *      because whoever reads the code believes the measurement is there.
 *  ⇒ From today `main.c` calls it, writing **one line a minute** with these
 *    two numbers next to the number of tenants served: it is the count with which
 *    the cure of §8.2 P4 can be **refuted** instead of remembered.
 *
 * ⛔ AND ON 25 AUGUST 2026 THIS SENTENCE WAS STILL HALF FALSE (finding R7 of
 *    §5.5): the line was there, ⛔ **but the number of tenants was not** — that is,
 *    exactly the denominator that makes the cure refutable was missing.  ⭐ Now
 *    the line carries `tenants=` (from `wt_tenants_served()`), and the three numbers
 *    are read together: `calls=` must follow the RE-CHECKS, not `tenants=`. */
void sentinel_counts(const sentinel *s, uint64_t *calls,
                      uint64_t *worst_ms);

#endif
