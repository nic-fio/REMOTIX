/*
 * rcp.c — the RCP/1 handshake, server side.
 *
 * Every rule below carries a paragraph number next to it: whoever changes one
 * must change `RCP.md` first, or the two drift apart in silence.
 */
#include "rcp.h"

#include <arpa/inet.h> /* the ban key: IPv4 whole, IPv6 the /64 (`rcp_key_address`) */
#include <errno.h> /* §4.4-bis: «there is no file yet» and «I could not
                    * read it» are two different facts, and what tells them
                    * apart is `errno` alone (`LESSONS.md` §1.9 rule 1) */
#include <fcntl.h>
#include <netinet/in.h>
#include <pwd.h> /* §4.4-bis D: is the name a user of this machine? (the log) */
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/random.h> /* the secret of the log tags */
#include <sys/stat.h>
#include <unistd.h>
#include <time.h> /* §4.4-bis: the ban file carries an ABSOLUTE time,
                    * because `now` is monotonic and restarts with every process */

/* ------------------------------------------------------------------------ */
/* The control channel types — §7.1                                          */
enum {
	T_HELLO = 0x0001,
	T_HERE_I_AM = 0x0002,
	T_CREDENTIALS = 0x0003,
	T_ADMITTED = 0x0004,
	T_REJECTED = 0x0005,
	T_ATTACH = 0x0006,
	T_SESSION = 0x0007,
	/* §7.2 — the cursor SHAPE, server → client, on the control channel
	 * (§5).  ⚠ The POSITION never travels in this direction: it belongs to the
	 * client, which draws the pointer itself (`SPECS.md` §7.1). */
	T_CURSOR_SHAPE = 0x000A,
	T_FAREWELL = 0x000C,
	/* ⭐ §5.2, §7.1: «the client asks for a keyframe».  Served since 12 Aug
	 * 2026, together with the video channel: while there was no video, this type
	 * fell into the `default` and made a conforming client that had seen a gap
	 * **lose the session** — the price the log declared
	 * («phase 1 does not needs it yet»). */
	T_REQUEST_KEY = 0x000D,
	/* ⭐ §7.6, 15 Aug 2026: «the user wants to leave».  ⛔ It is not the
	 * `FAREWELL`, which leaves the session alive: this one ENDS it. */
	T_TERMINATE_SESSION = 0x0011,
	/* ⭐ §7.1 — «the client asks for a canvas of another size», and the answer
	 * `CANVAS` that declares the outcome.  ⛔ Served since 14 Aug 2026: before,
	 * `FIT_CANVAS` fell into the `default` and made a conforming client **lose
	 * the session**, and `CANVAS` was sent **by no line at all** —
	 * `rcp_canvas_adapted_now()` changed the state and wrote to the log, but
	 * nothing went out on the wire.  It is the pair that `DECISIONS.md` §5.0-sexies
	 * switches on. */
	T_FIT_CANVAS = 0x000B,
	T_CANVAS = 0x000E,
	/* ⛔⭐ §7.1 — «the view has changed: new width and height».  Served
	 *     since 16 Aug 2026 (phase 6, sub-phase 6.4): before, it fell into the
	 *     `default` with the line «phase 1 does not needs it yet», and the price
	 *     was written there in full — **a conforming client that narrows the
	 *     window loses the session**, that is, literally the symptom that finding
	 *     R1.17 of §7.1 was written to make impossible.
	 *
	 * ⚠ And what it does is little for a declared reason, not out of laziness:
	 *   §7.1 says the view **MUST NOT** change the canvas and that «in RCP/1 not
	 *   even the size of what is encoded changes».  ⇒ It is validated, kept and
	 *   logged.  The canvas belongs to the SESSION, the view to the
	 *   CONNECTION. */
	T_VIEW = 0x0008,
	/* ⭐ §7.1 `0x0009` — «the keyboard layout has changed».  ⛔ Served
	 *    since 16 Aug 2026: before, it fell into the `default` and CLOSED the
	 *    session of a conforming client, which is the exact twin of the `VIEW`
	 *    defect.  It carries out `DECISIONS.md` §5-bis.7, and it is the message
	 *    with which the keyboard is changed **without detaching**. */
	T_LAYOUT = 0x0009,
	T_BENCH_MARK = 0x000F,
	T_BENCH_OUTCOME = 0x0010,
	/* ⏳ `RCP.md` §13 — PROPOSED, not normative (`DECISIONS.md` §11.32, open):
	 *    «my decoder is behind, no more than N frames per second».  ⛔ Lawful
	 *    ONLY with `video.pace` negotiated on both sides: without it, it is
	 *    `PROTOCOL_ERROR` like any capability used without asking (§4.3). */
	T_PACE = 0x0012,
};

/* ------------------------------------------------------------------------ */
/* ⭐ THE INPUT CHANNEL TYPES — §7.3, and the high byte is 0x01 (§2.5)        */
enum {
	T_POINTER = 0x0101,
	T_BUTTON = 0x0102,
	T_WHEEL = 0x0103,
	T_LETTER = 0x0104,
	T_KEY_POSITION = 0x0105,
};

/* ⛔ HOW LONG EACH BODY IS — §7.3, with the two common fields in front.
 *
 *   u32 id + u64 instant                              = 12  (all)
 *   POINTER       + u32 x + u32 y                   = 20
 *   BUTTON        + u16 code + u8 pressed         = 15
 *   WHEEL         + i32 axis_x + i32 axis_y         = 20
 *   LETTER         + u32 character                   = 16
 *   KEY_POSITION + u16 code + u8 pressed         = 15
 *
 * ⛔ §6.0: no field is aligned and no padding is allowed — so
 *    15 is fifteen, not sixteen.  It is exactly the shape of the defect fixed
 *    in §6.2 on 9 Aug 2026 (the «four bytes that make the numbers add up»), and
 *    on a fifteen-byte message a C `struct` would hold sixteen on
 *    every compiler this project uses. */
/* ------------------------------------------------------------------------ */
/* ⭐ THE CLIPBOARD CHANNEL TYPES — §7.4, and the high byte is 0x02 (§2.5)    */
enum {
	T_CLIPBOARD_ANNOUNCE = 0x0201, /* «I have new text» */
	T_CLIPBOARD_ASK = 0x0202,   /* «send it to me» */
	T_CLIPBOARD_TEXT = 0x0203,    /* UTF-8 */
};

/* ⛔ HOW LONG EACH BODY IS — §7.4.
 *
 *   ANNOUNCE  u32 transfer + u32 length        = 8, FIXED
 *   ASK    u32 transfer                        = 4, FIXED
 *   TEXT     u32 transfer + bytes to the end     = 4 + n, VARIABLE
 *
 * ⛔⭐ AND THE SECOND LENGTH IS NOT THERE, and it is a fix of 9 Aug 2026
 *     (finding R1.20): `CLIPBOARD_TEXT` carried a `u32 length` **inside** a
 *     message that already has its length in the framing of §6.1 — two
 *     truths about the same fact, which is the defect §2.2 forbids in those
 *     words.  ⇒ The text is read **up to the end of the message**, and the
 *     ceiling is the one of §5.4. */
#define A_ANNOUNCEMENT 8u
#define A_ASK 4u
#define A_TEXT_MIN 4u

/* ⛔ How many clipboard channel streams are kept open at once.
 *
 * §2.5 wants «one **per transfer**», and sets no ceiling on the number of
 * transfers: the ceiling is set by this module, because every open stream is
 * a buffer that lives in the session.  ⚠ Eight is generous: in the client →
 * session direction a transfer is one announcement and one text, and more than
 * two or three at once means someone is holding the copy key down.
 *
 * ⛔ And when the table is full the session is NOT closed: the oldest one
 *    WITHOUT pending bytes is thrown away, and ⛔ **it is written to the log**
 *    (§3: «every tolerance must be written to the log; a silent tolerance is
 *    indistinguishable from a defect»).  ⚠ If they are all halfway through a
 *    message, then that is a real violation and the client is sent away: it
 *    means the client opens streams and does not finish them. */
#define A_STREAM_MAX 8

/* ⛔ The backstop for paste requests, in milliseconds — see the box in
 *    `rcp_time()`.  ⚠ WIDER than the child's 4000 ms, and the reason is
 *    written there: the two backstops pay two different debts. */
#define CLIPBOARD_BACKSTOP 8000

#define I_COMMON 12u
#define I_POINTER (I_COMMON + 8u)
#define I_BUTTON (I_COMMON + 3u)
#define I_WHEEL (I_COMMON + 8u)
#define I_LETTER (I_COMMON + 4u)
#define I_POSITION (I_COMMON + 3u)

/* ⛔⭐ THE INPUT BUFFER IS SMALL **BY CONSTRUCTION**, and it is not a
 *     shortcut: it is §6.1 applied before allocating, taken to the extreme this
 *     channel allows.
 *
 *     On the control channel the declared length can only be known by
 *     reading the body (the capabilities of `HELLO` are a list), so the
 *     buffer grows up to 1 MiB.  ⛔ Not here: the five types of §7.3 all
 *     have a FIXED length known from the `kind` alone.  ⇒ As soon as the six
 *     header bytes have arrived it is already known whether the length is the
 *     right one, and a wrong length is `PROTOCOL_ERROR` BEFORE a
 *     single byte of body is buffered (§6.1: «the length is checked
 *     before allocating»).
 *
 * ⭐ Hence: 6 + 20 = 26 bytes are enough forever, and they fit in the session
 *    without a `malloc`.  Whoever announces a megabyte on this stream does not
 *    get a megabyte: they get a farewell after six bytes. */
#define I_ACCUMULATION 32u

/* §7.1 — the second of grace after a canvas change, in milliseconds.
 * ⚠ The comparison is `<=`: «for one second» includes millisecond 1000. */
#define CANVAS_GRACE 1000

/* §7.5 — the outcome of the bench function.  ⛔ DECISIONS §11.6: everything of the
 * bench function exists only in the test build (`make BENCH=1`, `-DREMOTIX_BENCH`);
 * in the installed binary `BENCH_MARK` is a type like any unknown one. */
#ifdef REMOTIX_BENCH
enum {
	BENCH_ACCEPTED = 1,
	BENCH_REFUSED = 2,
	BENCH_FEATURE_OFF = 1,
	BENCH_DELAY_OUT_OF_RANGE = 2,
};

/* ⛔ §7.5 rule 1: the bench function is OFF unless the administrator
 * switches it on — invariant I6, and here it literally paints over someone's
 * desktop.  In phase 1 there is no configuration yet, so it is
 * simply off: it is the default state of every server, and it is what B5
 * puts to the test. */
#define BENCH_ON 0
/* §7.5 rule 4: `delay_ms` MUST be between 0 and 10 000. */
#define BENCH_DELAY_MAX 10000
#endif /* REMOTIX_BENCH */

/* The ceilings of §4.6, in milliseconds. */
#define CAP_HELLO 5000
#define CAP_CREDENTIALS 60000
/* ⛔ TEN seconds, not sixty — finding R9.9, 10 Aug 2026.
 *
 * §4.6, table, third row: «`ADMITTED` sent → `ATTACH` received → 10 s».
 * Here there was 60 000, that is the same number as the row above: the shape
 * of the defect that is copied from the previous row and not reread.
 *
 * ⚠ The ceiling exists because «a connection that stops halfway through the
 *   handshake holds a slot and declares it to no one» (§4.6): at 60 000 that
 *   slot — the one of §4.4-bis and the one of the registry of sessions not yet
 *   taken — was held SIX TIMES longer than the document allows.
 *
 * ⛔ And no bench saw it: B6 (the three ceilings) is not written yet, and in
 *    `01-b5-violations.py` there is no case on the ceilings.  The defect sat
 *    exactly where the bench does not look. */
#define CAP_ATTACH 10000
/* §4.4-bis: the fixed delay, and it applies to ADMITTED TOO. */
#define FIXED_DELAY 1000
/* ⛔⭐ THE FLOOR OF EVERY REFUSAL — 25 Oct 2026.  `[M]` pam-tempi (present since 1.0): a user in the denied list
 *    (`pam_listfile`, `requisite`, before the password) was refused in ~1.1 s, i.e. only the fixed second above, while
 *    a real user with a wrong password and a user that does not exist took ~2.0-2.2 s (the failure delay of
 *    `pam_unix`/`pam_faildelay`, which runs INSIDE the helper): the time told whether a name was in the list.
 *    ⇒ A refusal that goes out as `0x07` (WRONG_CREDENTIALS: PAM's no — denied, wrong password, no such user, a
 *    locked account —, and the attempt without a verdict) leaves NOT BEFORE this floor; a success keeps FIXED_DELAY.
 *    ⛔ NOT the others: the limiter's `0x08` and our own `0x0E` already say by their BYTE which road they took, so the
 *    time reveals nothing more, and a connection in wait-verdict cannot be evicted (transport.c): holding them 2.5 s
 *    would let ~51 CREDENTIALS per second fill the 128 pre-login places instead of 128 per second.  The floor is higher
 *    than PAM's failure delay (random, up to 2.5 s with the default 2 s base): a refusal slower than the floor is
 *    paced by PAM, as before, and only that tail could still be told apart — so the number is a margin to be
 *    re-measured with pam-tempi, not a proof.  It is a FLOOR, like FIXED_DELAY: the verdict arriving later still
 *    sets the pace. */
#define REJECT_FLOOR 2500

/* ⛔⭐ THE VERDICT CEILING — 12 Aug 2026, `DECISIONS.md` §1.10.
 *
 * It is not a ceiling of `RCP.md` §4.6: those three measure the CLIENT, and this
 * one measures US.  ⛔ It exists because since 12 August the PAM answer comes
 * from another process, and another process can die: without this number a
 * session would stay in `wait-verdict` forever, that is a client hanging
 * on a silence — precisely what §8.1 forbids.
 *
 * ⚠ It is the SECOND net, not the first: the helper already has its own
 *   deadline at 8 s (`helper.c`).  ⛔ There are two on purpose, and they live
 *   in two different processes: the first cannot fire if the one at fault is
 *   precisely the one holding it.  Twelve seconds, that is more than its own,
 *   so in the normal case the no comes from there — with its log line — and
 *   this ceiling stays the last word instead of the first.
 *
 * ⛔ And the deadline counts as NO: `cred_good` is not touched, and it starts
 *    from false. */
#define VERDICT_CAP 12000

/* ⛔ THE SILENCE CLOCK — `SPECS.md` §5.3, `DECISIONS.md` §4.4.
 *
 * Thirty seconds without a byte FROM THE CLIENT and the client «is considered
 * detached»: it no longer holds the slot, and whoever arrives gets in.  It is
 * the rule that makes the case «the phone died in a tunnel and now I cannot
 * get back in» disappear.
 *
 * ⛔⛔⭐ AND HERE BELOW IT SAID THE OPPOSITE OF WHAT THE CODE DOES — 16
 *      Aug 2026, fixed together with the repair of the clock.
 *
 *      It said: ~~«it is measured on RCP bytes, not on QUIC ones: the
 *      transport sends acknowledgements and heartbeats on its own, and a clock
 *      resting on those would say "alive" of a client that has not spoken for
 *      an hour»~~.  ⚠ The fear was real and must be faced, not erased:
 *      **a client alive on the wire but with a dead page now holds the slot.**
 *
 * ⭐ But the choice was reversed on a measurement, not on an opinion: counting
 *    RCP bytes, **a user who was READING lost the slot after thirty
 *    seconds** — touches nothing, sends nothing — and a second device
 *    took it away.  `[M]` 16 August: `DETACHED for silence` at 30013 ms
 *    with the connection alive, and then `slot TAKEN` by a second tab while
 *    the first was watching.  ⇒ Counting bytes did not measure «the client is
 *    there»: it measured «the user is typing», which is the OTHER clock of
 *    §5.3, the thirty-MINUTE one.
 *
 * ⭐ And finding R3.19 stays satisfied, because the clock was not outsourced
 *    to QUIC: the thirty-second ceiling stays OURS, and what is looked at is
 *    the last packet **decrypted and authenticated** (`last_life`).  With
 *    `max_idle_timeout` at 120 seconds (as when this was written; the transport
 *    announces 30 today, `IDLE_MS` in `transport.c`) this server still detaches at 30.
 *
 * ⚠ And what happens to the connection of whoever is silent, the document does
 *   NOT say.  Here the choice is to **leave it open** and free only the slot:
 *   closing it would be a farewell, and §8.2 has no reason meaning «you have
 *   been quiet for a while».  The choice is declared in `PHASES.md`
 *   §01-filo-nudo, because it is a point where RCP.md allows two readings. */
#define SILENCE 30000

/* ⛔⛔⭐⭐ THE GHOST EVICTION — 23 Aug 2026, phase 9, and it is NOT a
 *        new clock of §5.3: it is a shortcut inside the first.
 *
 * ⛔ THE FACT, measured.  `[M]` 23 August (`benches/09-b78-opening.py`): the only
 *    way a session opening really fails under loss is
 *    `ATTACH` → `FAREWELL(0x0F)`.  With the client killed by `-9` — that is a
 *    goodbye NEVER SAID, which to the server is identical to a goodbye LOST —
 *    one counts **eleven refusals in a row, and the slot is free again at
 *    +30.5 s**: that is `SILENCE`.  ⛔ And the box above DECLARES that that
 *    clock «makes the case "the phone died in a tunnel" disappear».  It does
 *    not make it disappear: it **lasts thirty seconds**, and in those thirty
 *    seconds the sentence the user reads — «you already have an active session
 *    elsewhere» — speaks of THEIR session, dead a moment before.
 *
 * ⛔⛔ AND THE DIRECTOR'S DECISION OF 23 AUGUST MAKES IT THE NORMAL CASE, no
 *      longer the accident: on a bad network **the wire drops and the user
 *      reconnects by hand**.  Whoever reconnects by hand finds their own ghost
 *      denying them the slot, and on a line that loses in bursts they find it
 *      every time. ⇒ This cure is the prerequisite of that decision, not an extra.
 *
 * ⛔ WHY `SILENCE` WAS NOT LOWERED — road (a), discarded on a
 *    measurement and not on an opinion.  At 10 s it would break the case that
 *    on 16 Aug 2026 cost the repair of the two clocks: `[M]` on a still
 *    scene, between two authenticated packets of the BROWSER there are
 *    **15004, 15005, 15002 ms** — its keep-alive, which is not ours.  A ceiling
 *    at 10 s would detach **every** client that watches and does not touch, at
 *    every keep-alive round, and the line of `rcp_sign_of_life()` that warns at
 *    `SILENCE/2` would go from 15 s to 5 s, that is it would shout on every
 *    healthy session.  ⇒ It is not a number with a single job: it governs three
 *    (the slot, the §7.3 release on detach, and the warning threshold).  It
 *    stays 30.
 *
 * ⭐ THE ROAD CHOSEN, (b): the slot can be TAKEN AWAY EARLIER, but only from
 *    whoever has all three of these things together —
 *      1. it is the slot **of the same user** who is asking to get in
 *         (⛔ between different users it would be a security hole, not a
 *         convenience: see the explicit check in `handle_attach()`);
 *      2. it has been silent for more than `eviction_ms`;
 *      3. and someone **is asking** for that slot — it does not fire on its own,
 *         so a lone session is never touched by this rule.
 *
 * ⭐ AND IT DOES NOT CONTRADICT `RCP.md` §8.2 — *«no attached and alive client is
 *    ever ousted»* — it APPLIES it: the occupant here is attached but **not
 *    alive**, and until today the only clock that could tell the two apart
 *    was the thirty-second one.  ⚠ It must be written here, or the next reader
 *    will believe §8.2 was violated.
 *
 * ⚠⚠ THE PRICE, AND IT IS THE REASON FOR THE DEFAULT VALUE.  The only thing that
 *    tells «dead» from «alive and still» is how long it is silent, and how long
 *    an ALIVE client is silent is not up to us: it is up to its browser's
 *    keep-alive, `[M]` 15 s.  ⇒ A threshold below 15 s would let the second
 *    device win almost always — that is it would switch off invariant I2 on
 *    every idle desk, and would give whoever stole the password the means to
 *    throw out the real user, which today `0x0F` prevents.  That is why the
 *    default is `SILENCE / 2`: it is the point beyond which we have NEVER
 *    measured an alive client, and it is the same number at which
 *    `rcp_sign_of_life()` already writes «the margin is getting thin».  One
 *    number, one meaning.
 *
 * ⭐ THE REAL CURE LIES ELSEWHERE, and it must be said: if the server sent PINGs
 *    even during an active session (`PHASES.md` §05-la-sessione §6-bis,
 *    `src/webtransport.c` — NOT this file), the `last_life` of an alive client
 *    would never again be older than a couple of seconds, and this threshold
 *    could go down to 3.  With that in place the ghost lasts a breath; without
 *    it, it lasts half as long as before.
 *
 * ⛔ IT WAS BORN OFF — invariant I6.  ⚠ And the switch was NOT for the false
 *    sentence (that one is always fixed, further below): it was for the
 *    EVICTION, which is a new way in which the server takes something away
 *    from a session, and
 *    `DECISIONS.md` §4.1-bis says the server does not throw out a healthy
 *    session.  If the threshold were badly tuned it would throw out a live one,
 *    which is much worse than a wrong message. ⇒ It is switched on by whoever
 *    has looked.
 *
 * ⭐⭐⭐ AND WHOEVER LOOKED HAS DECIDED — 24 Aug 2026.  Since 24 August the
 *      default is **15 000 ms** (`SILENCE / 2`, the number of the box
 *      above), and `0` remains the only way to switch it off (`--eviction-ms 0`).
 *      ⇒ The premise of I6 is satisfied, not bypassed: the switch is still
 *      there, it is just turned the other way.
 *
 * ⚠ THE PRICE AND THE GAIN, DECLARED — `[M]` 23-24 Aug 2026: the ghost
 *   goes from **32.13 s and 14 refusals** to **16.83 s and 7 refusals**.  ⛔ That
 *   is exactly half, and it is exactly what the number promises: one does not go
 *   below 15 s, because the browser's keep-alive is silent for `[M]` 15 s and an
 *   ALIVE and still client would be evicted (⇒ I2 off on every idle desk).
 *
 * ⛔ The value in force is WRITTEN at startup, on or off, like the three
 *    clocks of §5.3 — a ceiling nobody can read is the E1 shape. */
#define DEFAULT_EVICTION (SILENCE / 2) /* 15 s: see the box */
static uint64_t eviction_ms = DEFAULT_EVICTION; /* 0 = off, ⭐ since 24 Aug
                                                   *    2026 it is born ON */

void rcp_eviction_set(uint64_t ms)
{
	eviction_ms = ms;
}

uint64_t rcp_eviction(void) { return eviction_ms; }
uint64_t rcp_eviction_recommended(void) { return DEFAULT_EVICTION; }

/* ⛔⭐ THE SECOND CLOCK OF §5.3 — «user inactivity», and until 16
 *     Aug 2026 IT DID NOT EXIST.
 *
 *     `SPECS.md` §5.3: *«30 minutes without input ⇒ REMOTIX **detaches**
 *     the client: getting back in takes user and password»*, and *«"input" is
 *     what the user sends, not what they watch: whoever spends half an hour
 *     watching a video without touching anything is detached.  The cost is
 *     small — reattaching is quick»*.  `RCP.md` §8.2 already gives it reason `0x02`.
 *
 * ⛔ And `RCP_INACTIVITY = 0x02` sat in `rcp.h` **without a line using it**:
 *    the E1 shape, «written is not in force».  A farewell reason declared
 *    in the protocol and never sent is a promise that another implementation
 *    would have had to handle for nothing.
 *
 * ⭐ THIS one is measured on USER GESTURES (`last_input`): the five input
 *    messages of `RCP.md` §7.3 — `POINTER`, `BUTTON`, `WHEEL`, `LETTER`,
 *    `KEY_POSITION` — once judged valid, in `handle_input()`.
 *
 * ⛔⭐ 15 Oct 2026 — UNTIL TODAY IT WAS MEASURED ON ANY RCP BYTE (`last_byte`),
 *     on control, input and clipboard, and that broke the sentence of §5.3
 *     quoted above.  The page sends messages ON ITS OWN while the user only
 *     watches — `REQUEST_KEY` after a hole, `PACE`, the opening
 *     `CLIPBOARD_ANNOUNCE`, the canvas and layout updates — and each of them
 *     put the half hour back to zero: ⇒ a tab left open on an abandoned desk
 *     held its session (and the slot, I2) FOREVER.  The 60-minute clock of
 *     `main.c` (`input_to_child()`) already counted the five gestures only;
 *     ⇒ now the two count THE SAME THING, which is what §5.3 writes: «the
 *     ceiling feeds on the same five gestures of §7.3 that feed the
 *     30-minute clock».
 *
 * ⚠ What does NOT count, and why:
 *     · every CONTROL message — automatic (`REQUEST_KEY`, `PACE`, `VIEW`,
 *       `LAYOUT`, `FIT_CANVAS`) or not a gesture on the desktop;
 *     · the CLIPBOARD — `CLIPBOARD_ANNOUNCE` leaves the page by itself at
 *       the opening and on focus; and a paste the user really makes on the
 *       remote desktop is a `Ctrl+V`, that is `KEY_POSITION`, which counts;
 *     · the server's own key release at detach (§7.3): it does not pass
 *       through `handle_input()`, and it must not — it happens exactly when
 *       the user leaves.
 *
 * ⛔ The connection-liveness clocks (silence 30 s, ghost eviction) are NOT
 *    this one: they look at `last_life`, refreshed by any packet and any
 *    RCP byte, as before.
 *
 * ⚠ CONFIGURABLE, and §5.3 demands it: *«the second and the third are
 *   configurable, with those values as defaults»*.  ⛔ And the value in force
 *   is WRITTEN to the log at startup: so the number is read instead of being
 *   waited for half an hour — which is also the only way to test it without
 *   tying up a machine. */
#define DEFAULT_INACTIVITY 1800000u /* 30 minutes */
static uint64_t inactivity_ms = DEFAULT_INACTIVITY;

void rcp_inactivity_set(uint64_t ms)
{
	/* ⛔ Zero means OFF, and it is a legitimate value: whoever watches a video
	 *    for hours on their own machine does not want to be thrown out.  ⚠ It is
	 *    declared to whoever sews things together, who writes it to the log. */
	inactivity_ms = ms;
}

uint64_t rcp_inactivity(void) { return inactivity_ms; }

/* ⛔⭐ THE CEILING OF §6.1 BELONGS TO THE **MESSAGE**, NOT TO THE BODY — finding
 *     B-14, night of 10 Aug 2026.
 *
 *     §6.1 says «no **message** MUST exceed 1 MiB», and that «message»
 *     includes the six framing bytes is established by §5.4, which for the
 *     clipboard chooses 1 000 000 and not 1 MiB **precisely because** «the
 *     message carrying it has six framing bytes and four of length, and a
 *     ceiling equal to the message's (§6.1) would make illegal the text
 *     exactly as large as the ceiling».
 *
 * ⛔ Until tonight the comparison was `lung > MAX_MESSAGE` with `lung` =
 *    length of the **body**: a `HELLO` with a 1 048 576-byte body was
 *    accepted, that is **1 048 582 bytes on the wire**, six over the ceiling.
 *    ⚠ Six bytes do no harm; two readings that give different bytes for the
 *    same input do: a validator written by reading §6.1 would mark red a
 *    message this server accepts, and that is what §0 exists to prevent.
 *
 * ⭐ Hence the two names, instead of one: `MAX_MESSAGE` is the ceiling of the
 *    document, `MAX_BODY` is what is left of it for the body.  The number of
 *    the document stays written only once. */
#define MAX_MESSAGE (1024u * 1024u) /* §6.1, FRAMING INCLUDED */
#define MAX_BODY (MAX_MESSAGE - 6u)

/* ⛔ THE BUFFER IS THE CEILING OF §6.1, NOT A NUMBER OF ITS OWN — finding R9.13.
 *
 * Here there were 64 KiB, and §6.1 says «no message MUST exceed 1 MiB» —
 * that is **up to 1 MiB is conforming**.  The two numbers sat two lines
 * apart and did not agree: every message between 64 KiB and 1 MiB died with
 * `PROTOCOL_ERROR` and the detail «too many bytes waiting for a body»,
 * before its header was even looked at.  ⚠ A `HELLO` with
 * four hundred capabilities with a legitimate and unknown name (≈ 82 KiB) is
 * conforming to §6.1 and §4.3 in every part, and §3 exception 1 requires
 * ignoring unknown names and **carrying on**: the server sent it away.
 *
 * ⚠ And there was a second effect: the check `lung > MAX_MESSAGE` was
 *   reachable ONLY from the length declared in the header, never from the
 *   bytes — the ceiling of §6.1 was not the ceiling of this server.
 *
 * ⭐ But a megabyte per connection taken at opening would be a gift to whoever
 *    opens a thousand connections: the buffer **grows on demand** and only up to
 *    this ceiling (see `accumulate()`).
 *
 * ⚠ And since the night of 10 Aug 2026 it is `MAX_MESSAGE` **exactly**, not
 *   `6 + MAX_MESSAGE`: the longest message this server accepts is
 *   1 MiB framing included (finding B-14), so there is nothing to
 *   buffer beyond that number. */
#define MAX_ACCUMULATION MAX_MESSAGE

enum state {
	S_WAIT_HELLO,
	S_WAIT_CREDENTIALS,
	S_WAIT_VERDICT, /* CREDENTIALS received, the fixed delay is running */
	S_WAIT_ATTACH,
	S_ACTIVE,
	/* ⛔ ACTIVE BUT WITHOUT A SLOT: it has been silent for thirty seconds —
	 * finding R9.2.  The state exists because «no longer holds the slot» and
	 * «is still active» are two different things, and keeping them under the
	 * same label left TWO `active` sessions for the same user — what I2
	 * forbids.  See the box above `rcp_time()`. */
	S_DETACHED,
	S_FINISHED,
};

static const char *STATE_NAMES[] = {"wait-hello",   "wait-credentials",
                                   "wait-verdict", "wait-attach",
                                   "active", "detached-by-silence",
                                   "finished"};

struct rcp_session {
	rcp_hooks g;
	enum state state;
	char provenance[64];
	/* ⛔ THE ADDRESS WITHOUT THE PORT, and it is not a detail: see the box
	 * above `rcp_key_address()`. */
	char address[64];
	char user[257];
	/* ⭐ The layout the client DECLARED in `ATTACH` (§4.5),
	 *    kept for two things: applying it when the session is open
	 *    (`DECISIONS.md` §5-bis.7), and recognising at `LAYOUT` (0x0009)
	 *    whether it has really changed.  ⚠ 64 bytes plus the NUL: it is the
	 *    ceiling of §4.5. */
	char layout[65];
	uint64_t since;   /* when the current state began */
	/* ⛔⛔⭐ TWO CLOCKS, NOT ONE — and until 16 Aug 2026 there was only one
	 *      doing the job of both.
	 *
	 *      `SPECS.md` §5.3 keeps TWO, with two different meanings:
	 *
	 *        · «CLIENT silence», 30 SECONDS — «a client that is silent is a
	 *          client that has detached», and the paragraph says why: *«the 30
	 *          seconds cover only real interruptions»*;
	 *        · «USER inactivity», 30 MINUTES — «whoever spends half an hour
	 *          watching a video without touching anything is detached».
	 *
	 *      ⛔ the user clock (then `last_byte`) was used for the FIRST: a
	 *         client that watches and does not touch sends nothing, and thirty
	 *         seconds without touching the keyboard counted as «the client is gone».
	 *
	 *      `[M]` 16 August, with the browser: session open, no input, and at
	 *      30013 ms «DETACHED for silence, slots taken: 0» — while the
	 *      connection was alive (QUIC did not make a sound for 111 s, and a
	 *      single key took the slot back on the SAME connection).  ⛔ And the
	 *      price was paid: a second tab got in and took the desktop of the
	 *      first, which froze.  It is I2 broken in the case that `RCP.md` §8.2
	 *      names in writing — *«an alive client holds the slot, and the new one
	 *      is refused»*. */
	uint64_t last_input; /* the last valid gesture of §7.3: the USER (§5.3) */
	uint64_t last_life; /* the last authenticated packet: the CLIENT (§5.3) */
	uint64_t cred_arrival; /* when CREDENTIALS arrived */
	bool cred_good;      /* the verdict, already computed but not yet told */
	uint8_t cred_reason;  /* if not good */
	/* ⭐ THE CHECK ASKED OF ANOTHER PROCESS — `DECISIONS.md` §1.10.
	 *
	 * ⛔ `expected_verdict` is true between the question and the answer, and it
	 *    is the reason why `cred_good` is no longer enough on its own: before
	 *    12 Aug 2026 the verdict was already ready when the state became
	 *    `wait-verdict`, because PAM had blocked the thread.  ⚠ Now
	 *    `wait-verdict` waits for TWO things: the fixed second of §4.4-bis
	 *    and the helper's answer — and the order between the two is not
	 *    guaranteed.
	 *
	 * ⛔ And while `expected_verdict` is true, `cred_good` is **false**: if
	 *    something went wrong in the middle, what is read is a no
	 *    (invariant I3). */
	bool expected_verdict;
	uint64_t ticket;     /* the number by which the answer is recognised */
	/* ⛔ `true` when the no does NOT come from PAM but from us (helper off,
	 * request expired): it does not count as a failed attempt of §4.4-bis.  A
	 * server defect that banned the user for twelve hours would be «the
	 * worst diagnosis this project could produce» (§4.4-bis). */
	bool refusal_is_ours;
	/* the name may be looked up in the system for the log only if the limiter
	 * let the attempt through (a flood of refused attempts must not cost an
	 * NSS lookup each) */
	bool user_lookup_ok;
	bool is_attached;       /* holds a slot in the registry of sessions */
	/* ⛔ The buffer is allocated on demand, and zeroed before being freed:
	 * `CREDENTIALS` passes through it, that is the password in clear (§4.4).
	 * See `accumulate()` and `rcp_free()` — findings R9.8 and R9.13. */
	uint8_t *acc;
	size_t acc_len, acc_cap;
	/* the negotiated capabilities, for the log (§4.3: the choice is written) */
	char codec[32];
	char depth[32];
	char audio[32];
	/* ⛔ THE DECODER CEILING — `video.max_size` of §4.3.
	 *
	 * `0` means «the client did not declare it», and it is not the same thing
	 * as «declared it zero»: §4.5 constrains the granted canvas **only if the
	 * client declared it**.  ⚠ Before the night of 10 Aug 2026 these two
	 * fields did not exist: the name was recognised as legitimate in
	 * `KNOWN_NAMES` and the value was thrown away — finding B-1. */
	uint32_t max_l, max_a;
	/* ⛔⭐ THE DECODER LEVEL — `video.level` of §4.3, and until
	 *     23 Aug 2026 it was the UNCURED TWIN of `max_l/max_a`: the name
	 *     was in `KNOWN_NAMES` and the value was **thrown away**, exactly
	 *     finding B-1 one field further on.
	 *
	 * ⛔ It is in TENTHS: `5.1` ⇒ `51`, `5` ⇒ `50`.  A `float` for a number that
	 *    comes out of a string and ends up in a comparison would be two ways of
	 *    writing `5.1` that are not equal — and the comparison is all this
	 *    field exists for.
	 * ⚠ `0` means «the client did not declare it», and it does NOT mean «low»:
	 *   whoever reads this field must not pick one on their own.  §4.3
	 *   requires the server not to EXCEED what the client declares, and on a
	 *   client that declares nothing there is nothing not to exceed. */
	uint32_t livello_x10;

	/* ==================================================================== */
	/* ⭐ THE VIDEO CHANNEL — §2.5, §5.1, §5.2, §6.2                        */

	/* ⛔⭐ «`SESSION` HAS BEEN SENT», AND NOT «THE STATE IS ACTIVE».
	 *
	 * §2.5 writes the rule with these words: «no video stream before having
	 * sent `SESSION`».  ⚠ The `active` state is very close and is NOT the
	 * same thing — it is a **proxy quantity**: it changes with
	 * `S_DETACHED` (a session that has been silent for thirty seconds sent
	 * `SESSION` long ago), and it would not change at all if one day the state
	 * were set to `active` one line before sending the message.
	 *
	 * ⛔ This flag is switched on IN THE SAME line that sends `SESSION`, and
	 *    only if the message really went out (`if (!w.full)`).
	 *
	 * ⭐ `LESSONS.md` §1.13, applied while writing: *«one names the real
	 *    quantity of the phenomenon, and looks whether the protocol already
	 *    carries it»*.  Here the phenomenon is «the client knows the canvas and
	 *    the codec», and the fact that tells it is `SESSION` — not a server state. */
	bool session_sent;

	/* ⛔ §6.2: THE CANVAS **IN FORCE**, which is the one granted in `SESSION`
	 * (§4.5) **or** the last one granted by `CANVAS(FITTED)` (§7.1).  ⚠ `0`
	 * here is not a size: it is «there is no canvas yet», and `sessione_
	 * spedita` is the fact that says so. */
	uint32_t canvas_w, canvas_h;
	/* ⛔⭐ THE VIEW — §7.1, and it sits **next to** the canvas on purpose: they
	 *     are two different quantities and the line separating them is normative.
	 *
	 *   · the **canvas** belongs to the SESSION: it outlives the client (I4),
	 *     only `FIT_CANVAS` changes it, and it constrains the frame size (§6.2);
	 *   · the **view** belongs to the CONNECTION: it is «the size at which the
	 *     client will draw», it arrives with `ATTACH` (§4.5) and `VIEW`
	 *     updates it (§7.1).  ⛔ It **MUST NOT** change the canvas, and in RCP/1
	 *     it does not even change the size of what is encoded: the server sends
	 *     the whole canvas and the client rescales (`SPECS.md` §6.1).
	 *
	 * ⚠ And the limits are OTHERS: §7.1, finding R1.17 — «any size from 1x1
	 *   up is legal, odd included».  The canvas limits exist for the encoder's
	 *   blocks, and they do not apply to the view because in RCP/1 the view
	 *   touches no encoder.
	 *
	 * ⚠ Today this number decides nothing, and that is declared: it serves «to
	 *   choose how many bits to spend» (§7.1), and the choice of bits belongs to
	 *   the encoder phase.  ⛔ But it is KEPT all the same, because the
	 *   alternative is reading it and throwing it away — that is a protocol
	 *   field the server declares it understood and does not hold anywhere. */
	uint32_t vista_l, vista_a;

	/* ⛔ §6.2: the frame counter.  `0` = **none sent**, and it is the meaning
	 * §7.1 gives to zero in `REQUEST_KEY`: here it is not an implicit
	 * sentinel (§6.0), it is the declared one. */
	uint32_t video_number;

	/* ⛔ §5.2: «the next frame MUST be a keyframe».  True:
	 *   · as soon as `SESSION` has gone out            (first point of the rules)
	 *   · after a `CANVAS(FITTED)` that CHANGES the size  (second point)
	 *   · when the client sends `REQUEST_KEY`         (§5.2, §7.1) */
	bool needs_key;
	/* Why it is needed, for the log: the three reasons are not the same thing
	 * and whoever diagnoses must be able to tell them apart. */
	const char *needs_key_reason;

	/* ⛔ §5.2, exception 5 of §3: «the server MAY ignore a
	 * `REQUEST_KEY` that arrives within 200 ms **of the last keyframe it
	 * sent**» — ⛔ not of the last request received, and the difference is
	 * not a nuance: counting from requests, two insistent clients push the
	 * clock forward forever and the keyframe never leaves. */
	uint64_t last_key_ms;
	bool never_sent_key;
	/* ⛔ 22 Sep 2026 — the `nr` of the last keyframe sent: the 200 ms grace
	 *    applies only to whoever has NOT yet seen that keyframe
	 *    (`handle_key_request()`). */
	uint32_t last_key_number;

	/* The frame open right now — §5.1, one stream per frame.
	 * ⛔ `video_is_open` and not «`stream` is -1»: `0` is a legitimate stream
	 *    identifier, and a sentinel taken from a valid value is what §6.0
	 *    forbids for protocol fields.  It is not done here either. */
	bool video_is_open;
	int64_t video_stream;
	bool video_is_key;      /* §5.2: a keyframe is NOT abandoned */
	uint32_t video_its_number;
	size_t video_to_write; /* the data bytes DECLARED in `do_open` */
	size_t video_written;     /* those gone out so far */
	uint64_t video_open_ms; /* the session time when it was opened */
	/* The count of abandonments, for the log: §5.1 wants every
	 * abandonment to be visible, and a count without a denominator is not a
	 * measurement (`LESSONS.md` §1.9). */
	uint32_t video_sent, video_abandoned;

	/* ==================================================================== */
	/* ⭐ THE INPUT CHANNEL — §2.5, §7.1, §7.3                              */

	/* §2.5: the input stream is **only one**.  ⛔ `inp_stream_known` and not
	 * «`inp_stream` is -1»: a stream 0 is a legitimate identifier, and a
	 * sentinel taken from a valid value is what §6.0 forbids. */
	bool inp_stream_known;
	int64_t inp_stream;
	/* The buffer, fixed: see the box of `I_ACCUMULATION`. */
	uint8_t inp_acc[I_ACCUMULATION];
	size_t inp_acc_len;

	/* ⛔ §7.3: «the `id` grows by **at least one** with every message, **across
	 *    the whole input channel** — not one per type».  ⇒ ONE counter, and only
	 *    one: five per-type counters would accept
	 *    `POINTER(4)` after `BUTTON(9)`, and then the `input` field of the
	 *    frames (§6.2) would no longer come back consistent with anything.
	 * ⚠ `0` = none yet, and it is the value §7.3 reserves. */
	uint32_t inp_last_id;
	/* ⛔ §6.2: what comes back in the `input` field of the frames — and it moves
	 * forward ONLY when the hook has answered 0.  See `rcp_input_last_injected()`. */
	uint32_t inp_last_injected;
	/* The count, and they are THREE numbers because the facts are three: how
	 * many arrived, how many injected, how many refused by the injector.
	 * ⛔ «Zero injected» on its own does not tell a mute compositor from a
	 * still client. */
	uint32_t inp_arrived, inp_injected, inp_not_injected;

	/* ==================================================================== */
	/* ⭐ THE CLIPBOARD CHANNEL — §7.4, §5.4, §2.5                          */

	/* ⛔⭐ EACH SIDE NUMBERS ITS OWN TRANSFERS, from 1 upwards (§7.4,
	 *     finding R1.11).  ⇒ Two counters, and they have two different owners:
	 *     ⛔ confusing them is exactly the defect the identifier was born
	 *     to remove — «with two announcements open in the two directions, the
	 *     user copies here while pasting there, and the two implementations pair
	 *     the requests with the announcements in a different order and **swap the
	 *     texts**».
	 *
	 * ⚠ `0` = «no announcement yet», and §7.4 reserves zero: transfers
	 *   start from 1.  It is not an implicit sentinel (§6.0), it is the one
	 *   declared by the protocol. */
	uint32_t app_my_id;  /* the last one *I* announced */
	/* ⛔ How many bytes the last text the SESSION gave us had: it serves to
	 *    know whether the session has something to lose.  See the rule
	 *    of the empty announcement, further below. */
	size_t app_my_len;
	uint32_t app_peer_id;  /* the last one the CLIENT announced */
	uint32_t app_peer_len; /* how many bytes that announcement said */

	/* ⛔ The text the SESSION copied, kept here waiting for someone to
	 *    ask for it.  §7.4: «one announces and asks, instead of pushing».
	 *
	 * ⚠ There is ONLY ONE, and it is the current one: §7.4 says that an
	 *   `CLIPBOARD_ASK` arriving when the announcement has already been
	 *   superseded by a more recent one **is served with the current text**,
	 *   and the sender writes it to the log.  ⇒ Keeping the old ones would needs
	 *   no purpose and would be memory growing with every copy. */
	char *app_text;
	size_t app_text_n;
	/* ⛔ The text above arrived BEFORE `SESSION` and has not yet been
	 *    announced: it is announced as soon as the session is open
	 *    (`announce_kept`). */
	bool app_kept;

	/* ⛔ The serials of the SESSION's requests waiting for the client's text.
	 *
	 * ⚠ There can be more than one: two programs pasting together are
	 *   two `SelectionTransfer`, and the wire carries a single `CLIPBOARD_ASK` —
	 *   the answer serves **all** of them, because they ask for the same
	 *   transfer identifier, that is the same text. */
	uint32_t app_serial[A_STREAM_MAX];
	int app_serial_n;
	/* ⛔ Has an `CLIPBOARD_ASK` for the queued batch already gone out?  ⚠ It is
	 *    needed because requests can arrive BEFORE the announcement (see
	 *    `rcp_clipboard_ask`), and then the question leaves when the
	 *    announcement arrives: without this flag one would leave for every
	 *    request already queued, and the client would receive three `ASK`
	 *    for a single text. */
	bool app_requested;
	/* ⛔⭐ AND WHICH ONE, not only «whether».  §7.4 says two things that look
	 *     like one: an `CLIPBOARD_TEXT` that NOBODY asked for is
	 *     `PROTOCOL_ERROR`, but a request served when the announcement has
	 *     already been superseded is served **with the current text** and is not
	 *     an error (the fifth exception of §3).  ⇒ The comparison must be made
	 *     with what I ASKED FOR, not with the live announcement: between the
	 *     question and the answer the client may have announced again, and then
	 *     the number is old by construction.
	 * ⚠ `[M]` 20 Aug 2026: it really happened, in the opposite direction — the
	 *   PAGE closed the session because of this, and the user saw «Firefox got
	 *   stuck with the clipboard». */
	uint32_t app_requested_id;

	/* ⛔⛔⭐ THE OFFER THAT WAITS FOR THE END OF THE TRANSFER — 21 Aug 2026,
	 *      and Mutter stated the defect in its own words: *«Transfer serial 2
	 *      doesn't match any transfer request»* (bench `07-b56`).
	 *
	 * ⚠ Offering the selection to the compositor (`SetSelection`) CANCELS the
	 *   transfers in flight: it is the compositor that, seeing a new selection,
	 *   throws away the requests open on the old one.  ⛔ And we were re-offering
	 *   precisely while serving — the client rereads the clipboard when asked,
	 *   announces the new text, and that announcement killed the paste
	 *   that had caused it.  ⇒ Whoever was pasting saw **empty**.
	 *
	 * ⭐ So the offer is POSTPONED: while someone is waiting, the
	 *    compositor stays the owner of what it has, and the new offer leaves
	 *    when the answer has gone out. */
	bool app_offer_later;

	/* The incoming streams, one per transfer (§2.5).  ⛔ The buffer is
	 * allocated on demand and **after** validating the declared length:
	 * §6.1 — «a receiver that allocates `length` bytes and then checks has
	 * already given a megabyte to anyone who can write six bytes». */
	struct {
		bool used;
		int64_t stream;
		uint8_t head[6];
		size_t head_n;
		uint16_t kind;
		uint32_t lung;
		uint8_t *body;
		size_t body_n;
	} app_in[A_STREAM_MAX];

	/* The count, and the facts are four because they are diagnosed separately:
	 * how many announcements I made, how many were asked of me, how many I
	 * received from the client, how many I asked of it. */
	uint32_t app_announced, app_served, app_received, app_asked;
	/* When the FIRST request of the batch was queued: the backstop of
	 * `rcp_time()` counts from here. */
	uint64_t app_requested_ms;

	/* ⛔ §4.3: did the client declare `clipboard.text = yes`?  ⚠ `false` is the
	 *    initial state and it is the right value: a `HELLO` without that
	 *    capability is a client that does not want the clipboard, not a client
	 *    that wants it by default. */
	bool negotiate_clipboard;
	/* ⏳ §13 — `PACE`.  `pace_declared`: OUR `HERE_I_AM` said
	 *    `video.pace=yes`; `pace_client`: the `HELLO` did.  Both ⇒ lawful.
	 *    `pace_in_force` is what the child has (0 = no ceiling);
	 *    `pace_pending` waits for the `RCP_PACE_GAP_MS` window to end. */
	bool pace_declared, pace_client, pace_has_pending, pace_ever_sent;
	uint16_t pace_in_force, pace_pending;
	uint64_t pace_sent_ms;
	uint32_t pace_received, pace_superseded;
	/* ⚠ §7.3: the client's `instant`, in microseconds.  ⛔ And NO RULE of this
	 *   module CONSUMES IT: «in a page the monotonic clock is in milliseconds
	 *   and its grain is deliberately coarsened — the client writes
	 *   `milliseconds × 1000` and MUST NOT suggest a precision it does not
	 *   have» (finding R1.27).  It is here for the log and for diagnosis —
	 *   «when the user moved their hand» instead of «when the byte arrived» —
	 *   and ⛔ no measurement is built on it: the delay is measured by the closed
	 *   loop of `DECISIONS.md` §2.6, and the frame carries back the `id`, not
	 *   the instant. */
	uint64_t inp_last_instant_us;

	/* ⛔ §7.1 / §3 exception 3 — THE SECOND OF GRACE.  The PREVIOUS canvas and
	 * the moment it was replaced: for one second a coordinate valid on that one
	 * is CLAMPED to the new one instead of closing the session.
	 * ⚠ `canvas_prev_w == 0` means «no grace in progress», and it is legitimate
	 *   because a canvas of zero width has never been granted (§4.5). */
	uint32_t canvas_prev_w, canvas_prev_h;
	uint64_t canvas_grace_since;
	/* How many coordinates the grace has saved: §3 wants «every tolerance to be
	 * written to the log», and a count makes it possible to notice that a
	 * tolerance has started covering the normal case. */
	uint32_t inp_graces;
	/* ⛔ §7.3, last paragraph: the release on detach is done **only
	 * once**.  The three roads that end a connection — farewell, silence,
	 * error — can be travelled in a row, and calling the hook twice does no
	 * harm but writes two lines that say different things about the same
	 * fact. */
	bool inp_released;

	/* ⛔⭐⭐ THE `FIT_CANVAS` PASSED TO THE STAGE AND NOT YET ANSWERED — §7.1,
	 *     and the chain `children_recanvas()` → `capture_resize()`
	 *     (`DECISIONS.md` §5.0-sexies).
	 *
	 * ⛔ IT EXISTS BECAUSE THE ANSWER DOES NOT COME BACK FROM WHERE THE QUESTION
	 *    LEAVES.  The stage lives in another process, and the only way of knowing
	 *    that the compositor has obeyed is **to see a frame arrive at the new
	 *    size**: it can take a few tens of milliseconds (`[M]` Mutter 41.6
	 *    ms, labwc 5.1 ms), one of a size DIFFERENT from the one asked for can
	 *    arrive (§4.5 allows it), and none may arrive at all.
	 *
	 * ⛔ AND THIS IS PRECISELY WHY A WAIT WITH A BACKSTOP IS NEEDED: §7.1
	 *    requires that *«to every `FIT_CANVAS` the server MUST answer with a
	 *    `CANVAS`, successful or not.  A silence leaves the client waiting
	 *    forever»* — and on the client that silence is not just a wait: §6.2
	 *    makes it HOLD BACK frames while a request is unanswered, that is it
	 *    makes its queue grow in memory.
	 *
	 * ⚠ `canvas_flight_from == 0` together with `canvas_flight` false: no request in
	 *   flight.  And if a second one arrives while the first is in flight, the
	 *   second REPLACES the first and the `CANVAS` that goes out counts for both:
	 *   the count on the client would go down by one only — ⛔ that is why the
	 *   first is ANSWERED before accepting the second (see `T_FIT_CANVAS`). */
	bool canvas_flight;
	uint32_t canvas_flight_w, canvas_flight_h;
	uint64_t canvas_flight_from;
	/* ⛔ SINCE WHEN the stage delivers a size different from the canvas in force
	 *    WITHOUT anyone having asked for it.  ⚠ Zero = they agree.
	 *
	 * ⛔ It is not a duplicate of `canvas_flight_from`, and it is the other case of
	 *    the same family: there the disagreement was wanted by us and one waits
	 *    for it to end; here nobody wanted it, and the first move is **asking
	 *    the stage to go back** to the canvas in force.  If after
	 *    `RCP_CANVAS_WAIT_MS` it has not gone back, its size is adopted: a
	 *    session with an unexpected canvas is worth more than a session that
	 *    does not see a pixel (`SPECS.md` §8.3, and I1 — «an ugly session
	 *    is worth more than a closed session»). */
	uint64_t canvas_mismatch_since;
	/* How long to wait before asking the stage again to go back: it doubles at
	 * every attempt that came to nothing, up to `RCP_CANVAS_RETRY_MAX_MS`. */
	uint64_t canvas_mismatch_wait;
};

/* Declared here because the attempt limiter, below, MUST be able to
 * write to the log: a limit reached in silence is a limit that does not
 * exist (§3, and finding R9.1). */
static void reg(rcp_session *s, const char *fmt, ...)
    __attribute__((format(printf, 2, 3)));
/* ⛔⭐ §7.3 — «On detach everything is released».  Declared here because
 *     THREE roads call it that sit higher up than where it is defined — the
 *     farewell, the silence of §5.3 and the end of the session — and the three
 *     are exactly the three that §7.3 names: «by farewell, by silence, by
 *     error».  Defined in the input channel section, where the rest is. */
static void release_on_detach(rcp_session *s, const char *why);

/* ⛔ §5.3 / finding R9.2 — the slot taken back by whoever speaks again.
 * Declared here because the client's bytes come in through TWO doors
 * (`rcp_receive()` and `rcp_receive_input()`) and the second sits higher up
 * than the definition. */
static bool speak_again(rcp_session *s);

/* ⛔⭐⭐ THE KEYFRAME DEBT IS SWITCHED ON AND OFF BY TWO FUNCTIONS ONLY — 23
 *      Aug 2026, and the reason is a comment that had already lied TWICE.
 *      The box of the video channel said «switched on in THREE places», and the
 *      places were four; corrected to «FIVE», and the places were nine.
 *      ⇒ A list kept by hand ages at the first new branch, and it ages in
 *      silence: no bench can notice, because the number is not a
 *      behaviour.  ⛔ The cure is not counting better: it is removing the
 *      count.  From here on the list is made by the compiler — `grep -n
 *      'key_needed(' src/rcp.c` is the list, always and by construction.
 * ⚠ Defined in the video channel section, where the rest is; declared here
 *   because the first switch-on (`SESSION` sent, §5.2) sits higher up. */
static void key_needed(rcp_session *s, const char *why);
static void announce_kept(rcp_session *s);
static void key_paid(rcp_session *s);

/* ------------------------------------------------------------------------ */
/* ⛔ THE REGISTRY OF ATTACHED SESSIONS — §8.2 reason 0x0F
 *
 * «The one refused is whoever arrives, not whoever was there»: no attached
 * and alive client is ever ousted.  A small list is enough here: the bench
 * opens two or three, and a real server will replace it with its session
 * table — but the RULE lives here, not there.                              */
/* ⛔⭐ THE NUMBER IS NO LONGER HERE — 25 Aug 2026.  It lives in `rcp.h`
 *     (`RCP_SESSION_CAP`), together with the box that explains why it was
 *     written by hand in four places and why now it is only one.
 *
 * ⭐⭐ AND SINCE THE EVENING OF 25 AUGUST IT IS NOT EVEN A FIXED SIZE: the
 *     table is **allocated** on the cap in force (`--session-cap`).  ⛔ The
 *     `MAX_ATTACCATE` that was here **has disappeared**, and it was not left
 *     alongside as a «maximum»: it would have been a second number, that is the
 *     second road of `CODER.md` §2-bis.
 * ⭐ `[M]` §3.3 had verified that the five functions below do **only
 *    linear scans with `strcmp`** — no index arithmetic, no invariant resting
 *    on the 16 — and that is why the change costs a `calloc` and a counter. */
static int cap_in_effect = RCP_SESSION_CAP;
static int how_many_slots;   /* ⛔ 0 until the table is allocated */
static struct slot {
	char user[257];
	bool used;
	/* ⛔⭐ WHO holds the slot, and it is not a duplicate of the name — 23 Aug
	 *    2026, the ghost eviction.  The name says THAT the slot is taken; to
	 *    know whether the occupant is still ALIVE one needs its `last_life`,
	 *    which lives in its session and could not be reached from here.
	 *
	 * ⚠ And it cannot be left dangling: ALL the roads that free the slot
	 *   pass through `slot_leave()` — `dismiss()`, `rcp_free()`,
	 *   `rcp_closed_by_client()`, `rcp_channel_closed()`, the client's
	 *   `FAREWELL` and the silence of `rcp_time()` — and that one zeroes it.
	 *   ⛔ Whoever adds a sixth road makes it pass through there, or this
	 *   pointer becomes a read of freed memory. */
	rcp_session *chi;
} *attached;

int rcp_cap(void)
{
	return cap_in_effect;
}

bool rcp_cap_set(int how_many)
{
	if (how_many < 1)
		return false;
	/* ⛔ Only once, and before a session exists: if the table is already
	 *    there, moving its number would leave TWO caps in force in the same
	 *    process — the allocated size and the declared number — which is
	 *    precisely the defect the four `#define`s at 16 had. */
	if (attached)
		return false;
	cap_in_effect = how_many;
	return true;
}

/* ⛔ The table is allocated at the first slot request, and **only once**.
 * ⚠ If `calloc` fails, the caller treats it as «no more slots»: it is a
 *   declared fallback, and the no arrives on the wire with a reason instead of
 *   with a segmentation fault. */
static bool ready_slots(void)
{
	if (attached)
		return true;
	attached = (struct slot *)calloc((size_t)cap_in_effect,
	                                   sizeof *attached);
	if (!attached)
		return false;
	how_many_slots = cap_in_effect;
	return true;
}

static bool slot_occupied(const char *user)
{
	for (int i = 0; i < how_many_slots; i++)
		if (attached[i].used && strcmp(attached[i].user, user) == 0)
			return true;
	return false;
}

/* The session holding that user's slot, or NULL. */
static rcp_session *slot_holder(const char *user)
{
	for (int i = 0; i < how_many_slots; i++)
		if (attached[i].used && strcmp(attached[i].user, user) == 0)
			return attached[i].chi;
	return NULL;
}

/* ⛔⭐ TWO DIFFERENT FACTS CANNOT HAVE THE SAME OUTCOME — finding R9.3.
 *
 * `slot_take()` returned `false` for two things that do not even resemble
 * each other: «this user's slot is taken» and «the table is full».
 * The caller deduced only one of them, and sent the client away with
 * `ALREADY_ACTIVE_REMOTELY`.
 *
 * ⛔ The seventeenth user of a multi-tenant machine (`SPECS.md`
 *    §5.5) — who never opened anything anywhere — received
 *    `FAREWELL(0x0F)`, and the client, as §8.2 requires, built from it the
 *    sentence «you already have an active session elsewhere».  **It is
 *    false.**  It is literally the symptom that the box above
 *    `rcp_closed_by_client()` declares it went to cure: «it tells me I am
 *    already connected, and it is not true».  The cure back then removed one
 *    of the two roads; this was the other.
 *
 * ⭐ The right reason for the full table is §8.2 `0x0E`
 *    SESSION_UNSERVABLE: «the attach is well formed but cannot be
 *    served», and it MUST carry the detail in the body — which is exactly
 *    this case. */
enum outcome_slot {
	SLOT_TAKEN,
	SLOT_OCCUPIED,       /* there is already a client attached to THIS session */
	SLOT_NO_MORE_SLOTS /* the registry of sessions is full */
};

/* ⚠ It takes the SESSION and no longer just the name: the registry must know
 *   WHO holds the slot, for the ghost eviction (see `DEFAULT_EVICTION`). */
static enum outcome_slot slot_take(rcp_session *s)
{
	const char *user = s->user;

	if (slot_occupied(user))
		return SLOT_OCCUPIED;
	/* ⛔ Here — and only here — the table is born: it is the only place that ADDS. */
	if (!ready_slots())
		return SLOT_NO_MORE_SLOTS;
	for (int i = 0; i < how_many_slots; i++) {
		if (!attached[i].used) {
			attached[i].used = true;
			attached[i].chi = s;
			snprintf(attached[i].user, sizeof attached[i].user, "%s",
			         user);
			return SLOT_TAKEN;
		}
	}
	return SLOT_NO_MORE_SLOTS;
}

static int taken_slots(void)
{
	int n = 0;
	for (int i = 0; i < how_many_slots; i++)
		if (attached[i].used)
			n++;
	return n;
}

static void slot_leave(const char *user)
{
	for (int i = 0; i < how_many_slots; i++)
		if (attached[i].used && strcmp(attached[i].user, user) == 0) {
			attached[i].used = false;
			/* ⛔ And the pointer is zeroed HERE, together with the slot: it is
			 * the only point from which one can guarantee that a session about
			 * to be freed does not stay attached to the registry. */
			attached[i].chi = NULL;
		}
}

/* ------------------------------------------------------------------------ */
/* ⛔⭐ THE LOGIN DEFENCES — §4.4-bis, rewritten on 24 Oct 2026 (SPEC CHANGE
 * from 1.0: `docs/1.5/DECISIONS-11.md`, section «The defences of the login»)
 *
 * WHAT THE 1.0 SAID (`DECISIONS.md` §1.9, 10 Aug 2026): three consecutive
 * failed authentications from the same address, and that address is out for 12
 * hours — a single counter, on the address, the user name does not count.
 *
 * ⛔ WHAT IS HERE NOW, AND IT MUST BE KNOWN WHEN READING THIS FILE.  The
 *    decision is the project leader's (delegated by the user, 24 Oct 2026,
 *    after the opinions of Gemini, ChatGPT, gpt-oss-20b and Laguna) and it
 *    changes the 1.0 on four points:
 *
 *  A. THE KEY.  IPv4: the whole address.  IPv6: the /64 (a subscriber gets a
 *     /64 at least and rotates inside it for free: counting the single
 *     address would be a limiter that is not there).  Plus one aggregate on
 *     the IPv6 /48.  The rule is the one of `address_key()` in `transport.c`
 *     (§1.9-bis): `::ffff:a.b.c.d` and NAT64 are the IPv4 inside, `::1` stays
 *     whole.  It lives in `rcp_key_address()`, and only there.
 *
 *  B. ATTEMPTS IN FLIGHT ARE BOOKED AT `CREDENTIALS`, not at the verdict.
 *     Since 12 Aug 2026 PAM answers after 1.0-2.2 s and the thread does not
 *     wait: a burst of N connections sent together would all find «0
 *     failures» and all reach PAM.  ⛔ So the counters are «failed + in
 *     flight», the check and the booking are ONE step (`login_reserve()`,
 *     the process is single-threaded), at most 2 verifications for the same
 *     (key, user) at once.  The verdict is booked by the NAME and the ADDRESS
 *     of the request (`struct flight` in `helper.c` keeps both), not by the
 *     session: if the connection died while PAM was answering, the true
 *     verdict is counted all the same (`rcp_orphan_verdict()`).
 *       · an attempt WITHOUT a verdict (PAM timeout in the helper, the 12 s
 *         ceiling of `rcp_time()`) COUNTS AS FAILED: a PAM that «does not
 *         answer» is exactly what an attacker would try to produce;
 *       · a refusal that is OUR defect and in which the question never left
 *         (helper off, socket full, 16 already in flight) does NOT count:
 *         `login_release()` gives the booking back.
 *
 *  C. THREE LEVELS OF COUNTERS, sliding window (the time of the last N
 *     failures is kept, not their number: see the ⚠ below):
 *         (key, user)   5 failed in  5 min   -> ban of (key, user)
 *         key          12 failed in  5 min   -> ban of the key, any user
 *         IPv6 /48     30 failed in 10 min   -> ban of the /48
 *     The ban is PROGRESSIVE for each level: 15 min, then 1 h, then 12 h (the
 *     maximum, which is the 1.0 duration); the memory of the previous bans is
 *     forgotten after 24 h without a ban.  ⭐ A successful login resets ONLY
 *     the failures of (key, user): not the recidivism, not the aggregates (an
 *     attacker owning one valid account must not be able to wash the key's
 *     count with it).
 *
 *    ⚠ The window is SLIDING and not anchored to the first failure: with the
 *      window anchored to the first, failures at 0:00, 4:59 and 5:01 would
 *      restart the count from ONE.  ⛔ Whoever tries passwords at a pace just
 *      slower than the window would never be stopped, and it is exactly the
 *      shape of defect that «the code was there and did nothing» has already
 *      produced once in this file.
 *
 *  D. THE LOG does not carry a name that is not a user of this machine:
 *     `unknown user [a1b2c3]`, the HMAC-SHA256 of the name cut to 6 hex,
 *     under a secret of the server (`log-secret`, 0600, next to the QUIC
 *     token secret).  Whoever typed the password in the user field leaves no
 *     password in a file that is kept (§11.1); the same name gives the same
 *     tag, so repeated tries are still recognisable.  A real user is named.
 *
 * ⛔ THE BAN SURVIVES A RESTART (`DECISIONS.md` §1.9, invariant I7): a ban
 *    that resets on restart is a protection that loses itself.  The file is
 *    written by `save_ban()`; `rcp_ban_load()` reads it back at startup, and
 *    also the OLD format (one «[address] epoch» per line = the 12 h ban of the
 *    1.0), which it converts.
 *
 *    ⚠ And the file carries an **absolute** time, not `now`: `now` is a
 *      MONOTONIC clock that restarts from an arbitrary point with every
 *      process.  The epoch in seconds is written and converted back at load.
 *
 * ⛔ AND THERE ARE TWO WAYS OUT: the ban passing, or `rcp_unblock()` — the
 *    unblock command, which requires access to the machine.  ⭐ It removes
 *    EVERY level that concerns the address (its (key, user) pairs, the key,
 *    the /48), recidivism included.  It is also what makes B8 possible.
 *    Every unblock is written to the log.
 *
 * ⚠ THE TABLE HAS A BOTTOM, and finding R9.1 applies identically: if
 *   `lcreate()` could fail silently, an uncounted failure would be a limiter
 *   that is not there.  ⛔ The victim is NEVER a banned entry, and never one
 *   with an attempt in flight: if the only candidates are those, the NEW entry
 *   is refused (`LV_FULL`: the attempt is refused with `TOO_MANY_ATTEMPTS`, the
 *   refusal is counted and written) instead of erasing somebody's ban.  Before
 *   that, entries with nothing to remember are taken back, and then the
 *   oldest one without recidivism, declared in the log.
 *   `[?]` That 256 slots are enough is not measured.
 *
 * ⛔ AND THERE IS NO EXPIRY FOR QUIET other than what is written above: the
 *    slots are given back when an entry has nothing left to remember.      */
#define MAX_ATTEMPTS 256
#define LEVELS 3
#define MAX_RING 30 /* the largest limit of the three levels */

/* The three levels of counters.  The ORDER is the order of the arrays below. */
enum { LK_USER = 0, LK_KEY = 1, LK_NET48 = 2 };
static const int LIMIT[LEVELS] = {5, 12, 30};
static const uint64_t WINDOW_MS[LEVELS] = {300000u, 300000u, 600000u};
static const char *const LEVEL_NAME[LEVELS] = {"user on this address",
                                               "address", "IPv6 /48"};
/* The progressive duration: the n-th ban of a level lasts LADDER_MS[n-1]. */
static const uint64_t LADDER_MS[3] = {900000u, 3600000u, 43200000u};
#define FORGET_MS 86400000u /* 24 h without a ban and the recidivism is forgotten */
#define MAX_PER_USER_IN_FLIGHT 2

struct lentry {
	bool used;
	uint8_t kind;      /* LK_* */
	char address[64];  /* the key, or the /48 for LK_NET48 */
	/* LK_USER only: the HMAC-SHA256 of the name, 64 hex digits, NEVER the name
	 * (the ban file is kept on disk: §11.1, 24 Oct 2026). */
	char user[65];
	/* ⛔ The time of the LAST `LIMIT[kind]` failures, not their number: it is
	 * what is needed to answer «N within the window» without anchoring the
	 * window to the first.  `amount` says how many slots are full. */
	uint64_t failure_times[MAX_RING];
	int amount;
	int in_flight;       /* booked at CREDENTIALS, not yet resolved */
	uint64_t banned_until; /* monotonic, like `now`; 0 = never banned */
	uint8_t level;       /* bans suffered, 0..2: the next one lasts LADDER_MS[level] */
	uint64_t last_touch;
};
static struct lentry attempts[MAX_ATTEMPTS];

/* ⭐ THE KEYS THAT LOGGED IN LATELY — 15 Oct 2026, `DECISIONS.md` §11.39 addendum
 *    (ported from 4d9eb72b).  The last ADMITTED verdict of a §4.4-bis key, in
 *    memory only (the monotonic clock does not survive a restart, so neither
 *    does this): it serves `rcp_asking_for_known_key()` and nothing else.  A
 *    ring of GOOD_KEYS: the same key takes its place again, else an empty one,
 *    else the oldest. */
#define GOOD_KEYS 64
#define GOOD_AGE 2592000000ull /* 30 days, ms */
static struct { char key[64]; uint64_t when; } good_keys[GOOD_KEYS];

static void good_note(const char *key, uint64_t now)
{
	int pick = 0;
	for (int k = 0; k < GOOD_KEYS; k++) {
		if (good_keys[k].key[0] && strcmp(good_keys[k].key, key) == 0) {
			pick = k;
			goto found;
		}
	}
	for (int k = 0; k < GOOD_KEYS; k++) {
		if (!good_keys[k].key[0]) {
			pick = k;
			goto found;
		}
		if (good_keys[k].when < good_keys[pick].when)
			pick = k;
	}
found:
	snprintf(good_keys[pick].key, sizeof good_keys[pick].key, "%s", key);
	good_keys[pick].when = now;
}

static bool good_recent(const char *key, uint64_t now)
{
	for (int k = 0; k < GOOD_KEYS; k++)
		if (good_keys[k].key[0] && strcmp(good_keys[k].key, key) == 0)
			/* ⚠ A login stamped LATER than `now` is recent, not 584 million
			 *   years old: `login_resolve()` may run with the helper's clock,
			 *   a few hundred ms ahead of a connection's `now`, and the
			 *   unsigned subtraction would wrap (fresh-eyes review 24c7b668). */
			return good_keys[k].when >= now || now - good_keys[k].when <= GOOD_AGE;
	return false;
}

/* ⭐ Set only around the call to `ask_verify` (`rcp.h`). */
static bool asking_for_known_key;

bool rcp_asking_for_known_key(void)
{
	return asking_for_known_key;
}
static unsigned login_refused_full; /* refusals because of a full table, since the start */

static char ban_path[512]; /* empty = not persisted (the bench, usually) */
/* ⛔⭐ THE ADDRESS WITHOUT THE PORT — found by B5 on 10 Aug 2026
 *
 * §4.4-bis wants «a counter per **source address**».  The first draft of this
 * module passed it `s->provenance`, which is `192.168.0.2:44661` — **with the
 * port**.  And §4.4 allows **a single attempt per connection**, so the port
 * changes at every attempt: that counter was **always 1**, and it never
 * blocked anyone.
 *
 * ⚠ It is the worst shape of defect: the code was there, it looked right, it
 *   read well, and **it did nothing**.  No single-connection test sees it; no
 *   log names it; the symptom — «a password can be tried forever» — never
 *   shows up on its own.
 *
 * ⭐ It was found by the B5 check that tries SEVEN failed attempts with
 *    SEVEN DIFFERENT NAMES from the same address: with equal names the
 *    **per-name** counter covered the hole, and the bench would have been green.
 *    ⛔ From today that counter no longer exists, so the seven-name test is the
 *    only possible form — and it is what B8 demands.
 *
 * ⚠ It is cut at the LAST colon, not the first: an IPv6 address is
 *   `[fe80::1]:44661`, and cutting at the first would produce `[fe80`.
 *
 * ⛔ AND THE KEY CARRIES SQUARE BRACKETS EVEN FOR IPv4 — `[M]` 10 Aug
 *    2026, read in the server log and not deduced: `util::straddr()` of the
 *    ngtcp2 example **always** writes `[127.0.0.1]:55680`, so the key this
 *    module counts is `[127.0.0.1]`, with the brackets, and it is the one that
 *    ends up in the ban file.  ⚠ Whoever calls from outside — the unblock
 *    command, which receives an address typed by a person — must go through
 *    `rcp_key_address()`, or it will look for `192.168.0.2` where
 *    `[192.168.0.2]` is written and will be told «it was not banned».
 *
 * ⛔ AND HERE THERE WAS AN ASSUMPTION THAT THE UNBLOCK COMMAND BREAKS: that the
 *    port is always there.  Until today the only caller was the session, which
 *    carries `[fe80::1]:44661`; the unblock command carries `[fe80::1]` and
 *    nothing else, and cutting at the last colon reduced it to `[fe80:`.
 *    ⭐ The guard is one line: if it ends with `]` the port is not there, so
 *    there is nothing to cut.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ AND ON 10 AUG 2026 (NIGHT) THIS FUNCTION WAS REMOVED — finding B-8
 *
 * It was called `solo_indirizzo()` and removed the port **without adding the
 * brackets**.  Three places called it: `rcp_open()`, `rcp_banned()` and
 * `rcp_unblock()`.  On the first ones it did no harm **by chance** — the host
 * already added the brackets itself — but on the two PUBLIC functions the
 * harm was measurable:
 *
 *     rcp_banned("192.168.0.2")   = 0     ⛔ «it is not banned»
 *     rcp_banned("[192.168.0.2]") = 1
 *
 * ⚠ And the form that answered **false** is exactly the one that
 *   `page.c` builds for IPv4 (`getnameinfo` + `"%s:%s"`).  Today it does no
 *   harm only because the caller normalises **first**, that is because the
 *   normalisation belonged to **the caller** — which is precisely what
 *   §4.4-bis forbids with a ⛔ and what `rcp.h` promises to do **in
 *   here**.
 *
 * ⭐ The cure is not adding the brackets to `solo_indirizzo()`: it is not having
 *    **two** functions that make the key.  One remains — the one below —
 *    and all three places use it.  ⚠ It is idempotent by construction, so
 *    whoever normalises twice gets the same key and no existing caller
 *    changes behaviour.
 * ------------------------------------------------------------------------ */

/* ⛔ The ban KEY, in the exact form in which §4.4-bis counts it — and the
 * reason why it is public lies entirely in one measurement.
 *
 * The host has two roads that arrive here, and they carry the address in two
 * different forms:
 *
 *   the session        `util::straddr()`, that is `[127.0.0.1]:55680` — brackets
 *                      and port, and this is the form that made the key;
 *   the command        what a person types: `127.0.0.1`, with nothing.
 *
 * ⛔ If the host built it itself, the day `straddr()` changed form the unblock
 *    command would start answering «it was not banned» to every address,
 *    forever and in silence: a command that always says the same thing has no
 *    symptom.  The format of the key is known by this file, and it is the
 *    only one that must know it.
 *
 * ⚠ The rule on colons, and it is worth the line it costs: with brackets the
 *   port is always recognisable; without, `127.0.0.1:53` has ONE colon (host
 *   and port) and `fe80::1` has two or more (and it is all address).  It is
 *   exactly the reason brackets exist.
 *
 * ⭐ AND SINCE 10 AUG 2026 (NIGHT) IT IS THE ONLY ONE that makes the key, inside
 *    and outside: `rcp_open()`, `rcp_banned()` and `rcp_unblock()` call it.
 *    See the box above, finding B-8. */
void rcp_key_address(const char *text, char *report, size_t cap)
{
	char bare[64];
	if (!text)
		text = "?";
	if (text[0] == '[') {
		const char *fine = strchr(text, ']');
		size_t n = fine ? (size_t)(fine - text) - 1 : strlen(text) - 1;
		if (n >= sizeof bare)
			n = sizeof bare - 1;
		memcpy(bare, text + 1, n);
		bare[n] = 0;
	} else {
		const char *first = strchr(text, ':');
		const char *last = strrchr(text, ':');
		/* a single colon = host:port; two or more = bare IPv6 */
		size_t n = (first && first == last) ? (size_t)(first - text)
		                                      : strlen(text);
		if (n >= sizeof bare)
			n = sizeof bare - 1;
		memcpy(bare, text, n);
		bare[n] = 0;
	}
	/* ⛔⭐ §4.4-bis A (24 Oct 2026): IPv4 whole, IPv6 the /64.  The rule is the
	 *    one of `address_key()` in `transport.c`: `::ffff:a.b.c.d` and NAT64
	 *    (64:ff9b::/96) are the IPv4 inside, `::1` stays whole, any other IPv6
	 *    loses its lower 64 bits.  ⚠ The result is again a valid address in
	 *    brackets, so the function stays IDEMPOTENT (the page and the host call
	 *    it twice on purpose).  What is not an address (a typo at the unblock
	 *    command, a zone id) is kept as it was: «[text]». */
	struct in_addr a4;
	struct in6_addr a6;
	char t[INET6_ADDRSTRLEN], parse[64];
	/* ⛔ A link-local address arrives with its zone, `fe80::x%eth0`, and
	 *    `inet_pton` refuses it: the key would be the whole address and a
	 *    LAN attacker could rotate addresses for free.  The `%zone` is cut
	 *    for parsing and it also goes to the /64: on a LAN users share one
	 *    counter, and that is accepted (project lead, 24 Oct 2026). */
	snprintf(parse, sizeof parse, "%s", bare);
	{
		char *z = strchr(parse, '%');
		if (z)
			*z = 0;
	}
	if (inet_pton(AF_INET, parse, &a4) == 1 && inet_ntop(AF_INET, &a4, t, sizeof t)) {
		snprintf(report, cap, "[%s]", t);
		return;
	}
	if (inet_pton(AF_INET6, parse, &a6) == 1) {
		static const uint8_t NAT64[12] = {0x00, 0x64, 0xff, 0x9b};
		if (IN6_IS_ADDR_V4MAPPED(&a6) || memcmp(a6.s6_addr, NAT64, sizeof NAT64) == 0) {
			if (inet_ntop(AF_INET, a6.s6_addr + 12, t, sizeof t)) {
				snprintf(report, cap, "[%s]", t);
				return;
			}
		} else if (!IN6_IS_ADDR_LOOPBACK(&a6)) {
			memset(a6.s6_addr + 8, 0, 8);
		}
		if (inet_ntop(AF_INET6, &a6, t, sizeof t)) {
			snprintf(report, cap, "[%s]", t);
			return;
		}
	}
	snprintf(report, cap, "[%s]", bare);
}

/* ------------------------------------------------------------------------ */
/* THE LINES OF THE LIMITER.  The counting code below is PURE: it takes `now`
 * as an argument, reads no clock and writes no log (`benches/unit/login-ban`
 * drives it with a simulated clock).  What it has to say it hands back in a
 * struct, and these functions write it — to the session, or, when the
 * connection is already gone, to the line function the caller gave.        */
struct sink {
	rcp_session *s;
	rcp_line_fn fn;
	void *ctx;
};

static void say(const struct sink *k, const char *fmt, ...)
    __attribute__((format(printf, 2, 3)));
static void say(const struct sink *k, const char *fmt, ...)
{
	char line[512];
	va_list ap;
	if (!k)
		return;
	va_start(ap, fmt);
	vsnprintf(line, sizeof line, fmt, ap);
	va_end(ap);
	if (k->s)
		reg(k->s, "%s", line);
	else if (k->fn)
		k->fn(k->ctx, line);
}

/* ------------------------------------------------------------------------ */
/* D — THE NAME IN THE LOG: HMAC-SHA256 truncated to 6 hex digits, under a
 * secret of the server.  SHA-256 is written out here (60 lines) and not taken
 * from OpenSSL on purpose: this file is compiled alone in the benches and in
 * the fuzz harness, which link nothing but the log stub — and a dependency
 * added to the module that must stay a twin of `benches/rcp/` is a build that
 * breaks far from where it was caused.  The unit test checks it against the
 * RFC 4231 vector.                                                         */
struct sha256 {
	uint32_t h[8];
	uint8_t buf[64];
	uint64_t total;
	size_t fill;
};

static const uint32_t SHA_K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1,
    0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
    0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
    0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
    0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
    0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2};

static uint32_t ror32(uint32_t x, int r) { return (x >> r) | (x << (32 - r)); }

static void sha256_block(struct sha256 *c, const uint8_t *p)
{
	uint32_t w[64], a, b, d, e, f, g, h, cc;
	for (int i = 0; i < 16; i++)
		w[i] = (uint32_t)p[4 * i] << 24 | (uint32_t)p[4 * i + 1] << 16 |
		       (uint32_t)p[4 * i + 2] << 8 | p[4 * i + 3];
	for (int i = 16; i < 64; i++) {
		uint32_t s0 = ror32(w[i - 15], 7) ^ ror32(w[i - 15], 18) ^ (w[i - 15] >> 3);
		uint32_t s1 = ror32(w[i - 2], 17) ^ ror32(w[i - 2], 19) ^ (w[i - 2] >> 10);
		w[i] = w[i - 16] + s0 + w[i - 7] + s1;
	}
	a = c->h[0]; b = c->h[1]; cc = c->h[2]; d = c->h[3];
	e = c->h[4]; f = c->h[5]; g = c->h[6]; h = c->h[7];
	for (int i = 0; i < 64; i++) {
		uint32_t S1 = ror32(e, 6) ^ ror32(e, 11) ^ ror32(e, 25);
		uint32_t ch = (e & f) ^ (~e & g);
		uint32_t t1 = h + S1 + ch + SHA_K[i] + w[i];
		uint32_t S0 = ror32(a, 2) ^ ror32(a, 13) ^ ror32(a, 22);
		uint32_t mj = (a & b) ^ (a & cc) ^ (b & cc);
		uint32_t t2 = S0 + mj;
		h = g; g = f; f = e; e = d + t1;
		d = cc; cc = b; b = a; a = t1 + t2;
	}
	c->h[0] += a; c->h[1] += b; c->h[2] += cc; c->h[3] += d;
	c->h[4] += e; c->h[5] += f; c->h[6] += g; c->h[7] += h;
}

static void sha256_init(struct sha256 *c)
{
	static const uint32_t H0[8] = {0x6a09e667, 0xbb67ae85, 0x3c6ef372,
	                               0xa54ff53a, 0x510e527f, 0x9b05688c,
	                               0x1f83d9ab, 0x5be0cd19};
	memcpy(c->h, H0, sizeof H0);
	c->total = 0;
	c->fill = 0;
}

static void sha256_update(struct sha256 *c, const void *data, size_t n)
{
	const uint8_t *p = data;
	c->total += n;
	while (n > 0) {
		size_t take = 64 - c->fill < n ? 64 - c->fill : n;
		memcpy(c->buf + c->fill, p, take);
		c->fill += take;
		p += take;
		n -= take;
		if (c->fill == 64) {
			sha256_block(c, c->buf);
			c->fill = 0;
		}
	}
}

static void sha256_final(struct sha256 *c, uint8_t out[32])
{
	uint64_t bits = c->total * 8;
	uint8_t pad = 0x80;
	sha256_update(c, &pad, 1);
	pad = 0;
	while (c->fill != 56)
		sha256_update(c, &pad, 1);
	uint8_t len[8];
	for (int i = 0; i < 8; i++)
		len[i] = (uint8_t)(bits >> (56 - 8 * i));
	sha256_update(c, len, 8);
	for (int i = 0; i < 8; i++) {
		out[4 * i] = (uint8_t)(c->h[i] >> 24);
		out[4 * i + 1] = (uint8_t)(c->h[i] >> 16);
		out[4 * i + 2] = (uint8_t)(c->h[i] >> 8);
		out[4 * i + 3] = (uint8_t)c->h[i];
	}
}

static void hmac_sha256(const uint8_t *key, size_t klen, const void *msg,
                        size_t mlen, uint8_t out[32])
{
	uint8_t k[64] = {0}, pad[64], inner[32];
	struct sha256 c;
	if (klen > 64) {
		sha256_init(&c);
		sha256_update(&c, key, klen);
		sha256_final(&c, k);
	} else {
		memcpy(k, key, klen);
	}
	for (int i = 0; i < 64; i++)
		pad[i] = k[i] ^ 0x36;
	sha256_init(&c);
	sha256_update(&c, pad, 64);
	sha256_update(&c, msg, mlen);
	sha256_final(&c, inner);
	for (int i = 0; i < 64; i++)
		pad[i] = k[i] ^ 0x5c;
	sha256_init(&c);
	sha256_update(&c, pad, 64);
	sha256_update(&c, inner, 32);
	sha256_final(&c, out);
	explicit_bzero(k, sizeof k);
	explicit_bzero(pad, sizeof pad);
}

#define LOG_SECRET_FILE "log-secret"
static uint8_t log_secret[32];
static bool log_secret_ready;

/* Fills the secret from the kernel.  ⛔ If it cannot, `log_secret_ready`
 * stays false and `log_user()` prints a tag of question marks: a name in
 * clear is NEVER the fallback, because the fallback is the road that is taken
 * when nobody is looking. */
static bool log_secret_random(void)
{
	size_t got = 0;
	while (got < sizeof log_secret) {
		ssize_t n = getrandom(log_secret + got, sizeof log_secret - got, 0);
		if (n < 0 && errno == EINTR)
			continue;
		if (n <= 0)
			return false;
		got += (size_t)n;
	}
	return true;
}

/* Reads `<dir>/log-secret` or makes it (0600), exactly like `secret_load()`
 * of `transport.c` does for the QUIC token secret, in the same directory.
 * Returns 1 = read, 0 = made and written, -1 = the secret of this run only
 * (memory): the tags change at every restart, and the caller says so;
 * -2 = no secret at all (the tags are «??????»). */
int rcp_log_secret_load(const char *dir)
{
	log_secret_ready = false;
	if (!dir || !*dir) {
		log_secret_ready = log_secret_random();
		return log_secret_ready ? -1 : -2;
	}
	char path[600], tmp[620];
	/* The directory may not exist yet: this runs before `certificates_prepare()`
	 * (the ban file needs the secret first), which makes it with the same mode. */
	if (mkdir(dir, 0700) != 0 && errno != EEXIST) {
		log_secret_ready = log_secret_random();
		return log_secret_ready ? -1 : -2;
	}
	snprintf(path, sizeof path, "%s/%s", dir, LOG_SECRET_FILE);
	int fd = open(path, O_RDONLY | O_CLOEXEC);
	if (fd >= 0) {
		uint8_t buf[sizeof log_secret + 1];
		ssize_t n = read(fd, buf, sizeof buf);
		struct stat st;
		bool ok = n == (ssize_t)sizeof log_secret && fstat(fd, &st) == 0 &&
		          (st.st_mode & 077) == 0;
		close(fd);
		if (ok) {
			memcpy(log_secret, buf, sizeof log_secret);
			explicit_bzero(buf, sizeof buf);
			log_secret_ready = true;
			return 1;
		}
		explicit_bzero(buf, sizeof buf);
		/* a file of the wrong size or readable by others: replaced */
	}
	if (!log_secret_random())
		return -2;
	log_secret_ready = true;
	snprintf(tmp, sizeof tmp, "%s.new", path);
	fd = open(tmp, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0600);
	if (fd < 0)
		return -1;
	bool wrote = write(fd, log_secret, sizeof log_secret) == (ssize_t)sizeof log_secret &&
	             fsync(fd) == 0;
	close(fd);
	if (!wrote || rename(tmp, path) != 0) {
		/* the temporary one must not stay (a failed rename leaves it for ever) */
		unlink(tmp);
		return -1;
	}
	return 0;
}

/* The name as it goes to the log: itself if it is a user of this machine,
 * `unknown user [hmac6]` if it is not.  ⚠ `getpwnam_r` may ask NSS, and a
 * line written for a REFUSED attempt (banned, busy, table full) must not make
 * the server do that lookup for a flood: with `lookup` false the lookup is not
 * made and the tag is written with a neutral word, `user [hmac6]` (it does
 * not say whether the name exists).  A failure of the lookup is treated as
 * «unknown» (the cautious side).  ⛔ Writes into `out`; the return value is
 * `user` itself or `out`. */
static const char *log_user(const char *user, char *out, size_t cap, bool lookup)
{
	if (!user || !*user)
		return "";
	if (lookup) {
		struct passwd pw, *res = NULL;
		char spare[2048];
		if (getpwnam_r(user, &pw, spare, sizeof spare, &res) == 0 && res)
			return user;
	}
	if (!log_secret_ready)
		log_secret_ready = log_secret_random();
	if (!log_secret_ready) {
		snprintf(out, cap, "%suser [??????]", lookup ? "unknown " : "");
		return out;
	}
	uint8_t mac[32];
	hmac_sha256(log_secret, sizeof log_secret, user, strlen(user), mac);
	snprintf(out, cap, "%suser [%02x%02x%02x]", lookup ? "unknown " : "", mac[0],
	         mac[1], mac[2]);
	return out;
}

/* The key of a name inside the counters and the ban file: the FULL HMAC-SHA256
 * in hex.  ⛔ The ban file holds this and never the name (24 Oct 2026): a file
 * kept on disk, 0600 or not, is not where the names of the people who failed
 * belong.  ⚠ The secret must be loaded BEFORE `rcp_ban_load()` (main.c does it),
 * or the bans of a restart would not match any name.  Without a secret (no
 * kernel randomness: it does not happen) the bytes are zero and the key is a
 * plain keyed-by-zero hash: the counters still count. */
static void user_key(const char *user, char out[65])
{
	uint8_t mac[32];
	if (!log_secret_ready)
		log_secret_ready = log_secret_random();
	hmac_sha256(log_secret, sizeof log_secret, user ? user : "", user ? strlen(user) : 0, mac);
	for (int i = 0; i < 32; i++)
		snprintf(out + 2 * i, 3, "%02x", mac[i]);
}

/* ------------------------------------------------------------------------ */
/* THE COUNTERS.                                                             */

/* The /48 of a key, if it has one: only the IPv6 keys that are neither an
 * IPv4 nor loopback (those `rcp_key_address()` has already reduced).  The key
 * is already the /64, so it is the same text with 16 more bits zeroed. */
static bool key_net48(const char *key, char *out, size_t cap)
{
	char bare[64];
	size_t n = strlen(key);
	if (n < 3 || key[0] != '[' || key[n - 1] != ']' || n - 2 >= sizeof bare)
		return false;
	memcpy(bare, key + 1, n - 2);
	bare[n - 2] = 0;
	{
		char *z = strchr(bare, '%'); /* a zone id never reaches a key, but cut it all the same */
		if (z)
			*z = 0;
	}
	struct in6_addr a;
	if (inet_pton(AF_INET6, bare, &a) != 1 || IN6_IS_ADDR_LOOPBACK(&a) ||
	    IN6_IS_ADDR_V4MAPPED(&a))
		return false;
	memset(a.s6_addr + 6, 0, 10);
	char t[INET6_ADDRSTRLEN];
	if (!inet_ntop(AF_INET6, &a, t, sizeof t))
		return false;
	snprintf(out, cap, "[%s]", t);
	return true;
}

static uint8_t level_now(const struct lentry *e, uint64_t now)
{
	if (e->level > 0 && now >= e->banned_until + FORGET_MS)
		return 0; /* 24 h without a ban: forgotten */
	return e->level;
}

static bool is_banned(const struct lentry *e, uint64_t now)
{
	return now < e->banned_until;
}

static int failed_inside(const struct lentry *e, uint64_t now)
{
	int n = 0;
	for (int k = 0; k < e->amount; k++)
		/* a stamp in the future (>= now: a clock that went back) is inside the
		 * window: the unsigned subtraction would wrap and forget the failure */
		if (e->failure_times[k] >= now || now - e->failure_times[k] <= WINDOW_MS[e->kind])
			n++;
	return n;
}

/* Nothing to remember: it can be taken back with no loss. */
static bool lentry_idle(const struct lentry *e, uint64_t now)
{
	return e->in_flight == 0 && !is_banned(e, now) && level_now(e, now) == 0 &&
	       failed_inside(e, now) == 0;
}

/* Only looks: ⛔ querying the guard MUST NOT consume a slot. */
static int lfind(int kind, const char *address, const char *user)
{
	for (int i = 0; i < MAX_ATTEMPTS; i++)
		if (attempts[i].used && attempts[i].kind == kind &&
		    strcmp(attempts[i].address, address) == 0 &&
		    (kind != LK_USER || strcmp(attempts[i].user, user) == 0))
			return i;
	return -1;
}

/* Creates an entry, or returns -1 if the table is full of things that must not
 * be thrown away.  ⛔ NEVER a banned entry and never one with an attempt in
 * flight (nor one of `avoid`, the entries the caller is holding): if there is
 * nothing else, -1 and the caller REFUSES the attempt and counts the refusal.
 * Order of preference: free slot, entry with nothing to remember, oldest
 * entry without recidivism, oldest one with it.  The last two are declared
 * in `evicted` (empty if nothing was thrown away that held something). */
static int lcreate(int kind, const char *address, const char *user, uint64_t now,
                   const int avoid[LEVELS], char *evicted, size_t evcap)
{
	int slot = -1, victim = -1, victim_class = 99;
	for (int k = 0; k < MAX_ATTEMPTS; k++) {
		if (!attempts[k].used) {
			slot = k;
			break;
		}
		const struct lentry *e = &attempts[k];
		bool held = false;
		for (int j = 0; j < LEVELS; j++)
			if (avoid && avoid[j] == k)
				held = true;
		if (held || e->in_flight > 0 || is_banned(e, now))
			continue;
		int cls = lentry_idle(e, now) ? 0 : (level_now(e, now) == 0 ? 1 : 2);
		if (cls < victim_class ||
		    (cls == victim_class && e->last_touch < attempts[victim].last_touch)) {
			victim = k;
			victim_class = cls;
		}
	}
	if (slot < 0) {
		if (victim < 0)
			return -1;
		slot = victim;
		if (victim_class > 0 && evicted && evcap)
			snprintf(evicted, evcap, "%s %s", LEVEL_NAME[attempts[slot].kind],
			         attempts[slot].address);
	}
	memset(&attempts[slot], 0, sizeof attempts[slot]);
	attempts[slot].used = true;
	attempts[slot].kind = (uint8_t)kind;
	attempts[slot].last_touch = now;
	snprintf(attempts[slot].address, sizeof attempts[slot].address, "%s", address);
	if (kind == LK_USER && user)
		snprintf(attempts[slot].user, sizeof attempts[slot].user, "%s", user);
	return slot;
}

enum login_verdict {
	LV_OK,     /* booked: ask PAM */
	LV_BANNED, /* a level is banned: do not ask PAM */
	LV_BUSY,   /* the counters (failed + in flight) are at the limit: do not ask PAM */
	LV_FULL    /* the table has no place for the entry: do not ask PAM, counted */
};

struct login_info {
	int kind;          /* the level that decided (LK_*) */
	uint64_t remain;   /* LV_BANNED: ms left */
	char evicted[96];  /* an entry with something in it was thrown away to make room */
};

/* B — THE CHECK AND THE BOOKING IN ONE STEP.  Called at `CREDENTIALS`, before
 * PAM.  The counters are «failed in the window + in flight»; the attempt that
 * would bring any level to its limit is not let through, and it is NOT a
 * failure (no ban is born from a refusal).  At most
 * `MAX_PER_USER_IN_FLIGHT` for the same (key, user). */
static enum login_verdict login_reserve(const char *key, const char *user,
                                        uint64_t now, struct login_info *info)
{
	char key48[64], uk[65];
	bool has48 = key_net48(key, key48, sizeof key48);
	int idx[LEVELS];
	memset(info, 0, sizeof *info);
	user_key(user, uk);
	user = uk; /* from here the user is its HMAC */
	idx[LK_USER] = lfind(LK_USER, key, user);
	idx[LK_KEY] = lfind(LK_KEY, key, NULL);
	idx[LK_NET48] = has48 ? lfind(LK_NET48, key48, NULL) : -1;
	/* the widest level first: it is the one that says the most */
	for (int j = LEVELS - 1; j >= 0; j--)
		if (idx[j] >= 0 && is_banned(&attempts[idx[j]], now)) {
			info->kind = j;
			info->remain = attempts[idx[j]].banned_until - now;
			return LV_BANNED;
		}
	for (int j = 0; j < LEVELS; j++) {
		if ((j == LK_NET48 && !has48) || idx[j] >= 0)
			continue;
		idx[j] = lcreate(j, j == LK_NET48 ? key48 : key, user, now, idx,
		                 info->evicted, sizeof info->evicted);
		if (idx[j] < 0) {
			login_refused_full++;
			info->kind = j;
			return LV_FULL;
		}
	}
	for (int j = 0; j < LEVELS; j++) {
		if (idx[j] < 0)
			continue;
		const struct lentry *e = &attempts[idx[j]];
		if ((j == LK_USER && e->in_flight >= MAX_PER_USER_IN_FLIGHT) ||
		    failed_inside(e, now) + e->in_flight >= LIMIT[j]) {
			info->kind = j;
			return LV_BUSY;
		}
	}
	for (int j = 0; j < LEVELS; j++) {
		if (idx[j] < 0)
			continue;
		attempts[idx[j]].in_flight++;
		attempts[idx[j]].last_touch = now;
	}
	return LV_OK;
}

/* The booking given back WITHOUT counting anything: the question to PAM never
 * left, and that is our defect (I3: a no that is not the user's fault). */
static void login_release(const char *key, const char *user)
{
	char key48[64], uk[65];
	int idx[LEVELS];
	user_key(user, uk);
	user = uk;
	idx[LK_USER] = lfind(LK_USER, key, user);
	idx[LK_KEY] = lfind(LK_KEY, key, NULL);
	idx[LK_NET48] = key_net48(key, key48, sizeof key48)
	                    ? lfind(LK_NET48, key48, NULL) : -1;
	for (int j = 0; j < LEVELS; j++)
		if (idx[j] >= 0 && attempts[idx[j]].in_flight > 0)
			attempts[idx[j]].in_flight--;
}

struct login_result {
	bool already[LEVELS];     /* the level was banned already: nothing added */
	int inside[LEVELS];       /* failures in the window, this one included */
	bool banned[LEVELS];      /* this failure fired a ban on the level */
	uint64_t ban_ms[LEVELS];
	int ban_number[LEVELS];   /* 1, 2, 3.. (the ladder stops at the third duration) */
	int reset_amount;         /* success: how many failures of (key, user) were wiped */
	int refused_full;         /* levels that could not be counted: the table is full */
	char evicted[96];
};

/* The VERDICT: the booking is resolved.  `admitted` resets ONLY the failures
 * of (key, user) — not the recidivism, not the key, not the /48.  A failure
 * is added to the three levels, and the level that reaches its limit inside
 * its window is banned for the next step of the ladder.  ⛔ A failure is
 * never dropped for lack of room: the entry is created, evicting if it has to
 * (and declaring it), and only if nothing can be evicted is the level skipped
 * and `refused_full` raised. */
static void login_resolve(const char *key, const char *user, bool admitted,
                          uint64_t now, struct login_result *r)
{
	char key48[64], uk[65];
	bool has48 = key_net48(key, key48, sizeof key48);
	int idx[LEVELS];
	memset(r, 0, sizeof *r);
	user_key(user, uk);
	user = uk; /* from here the user is its HMAC */
	idx[LK_USER] = lfind(LK_USER, key, user);
	idx[LK_KEY] = lfind(LK_KEY, key, NULL);
	idx[LK_NET48] = has48 ? lfind(LK_NET48, key48, NULL) : -1;
	if (!admitted)
		for (int j = 0; j < LEVELS; j++) {
			if ((j == LK_NET48 && !has48) || idx[j] >= 0)
				continue;
			idx[j] = lcreate(j, j == LK_NET48 ? key48 : key, user, now, idx,
			                 r->evicted, sizeof r->evicted);
			if (idx[j] < 0) {
				login_refused_full++;
				r->refused_full++;
			}
		}
	for (int j = 0; j < LEVELS; j++) {
		if (idx[j] < 0)
			continue;
		struct lentry *e = &attempts[idx[j]];
		if (e->in_flight > 0)
			e->in_flight--;
		e->last_touch = now;
		if (admitted) {
			if (j == LK_USER) {
				r->reset_amount = failed_inside(e, now);
				e->amount = 0;
			}
			if (j == LK_KEY)
				good_note(key, now);
			continue;
		}
		if (is_banned(e, now)) {
			r->already[j] = true; /* a ban fired while this one was in flight */
			continue;
		}
		if (e->amount < LIMIT[j]) {
			e->failure_times[e->amount++] = now;
		} else {
			memmove(e->failure_times, e->failure_times + 1,
			        (size_t)(LIMIT[j] - 1) * sizeof e->failure_times[0]);
			e->failure_times[LIMIT[j] - 1] = now;
		}
		r->inside[j] = failed_inside(e, now);
		if (r->inside[j] >= LIMIT[j]) {
			uint8_t lv = level_now(e, now);
			e->banned_until = now + LADDER_MS[lv];
			e->level = lv < 2 ? (uint8_t)(lv + 1) : 2;
			e->amount = 0; /* the count restarts after the ban */
			r->banned[j] = true;
			r->ban_ms[j] = LADDER_MS[lv];
			r->ban_number[j] = lv + 1;
		}
	}
}

/* ⭐ §11.47 B (ported from 249c534a): the ticket whose «no» PAM gave while
 *    `pam_faillock` had the account locked; 0 = none.  Set by the host only
 *    around ONE delivery (`rcp_refusal_locked()`, `rcp.h`). */
static uint64_t locked_ticket;

void rcp_refusal_locked(uint64_t ticket)
{
	locked_ticket = ticket;
}

/* ⭐ 1.5 (`DECISIONS.md` §11.50, D4b): the ticket the helper answered «not
 *    checked» for (its dispatcher's cap, a fork that failed, a helper that
 *    died or is down); 0 = none.  Set by the host only around ONE delivery
 *    (`rcp_refusal_unchecked()`, `rcp.h`). */
static uint64_t unchecked_ticket;

void rcp_refusal_unchecked(uint64_t ticket)
{
	unchecked_ticket = ticket;
}

/* ⛔⭐ A «NO» THAT DOES NOT COUNT — `DECISIONS.md` §11.47 B (the user, 15 Oct
 *     2026).  Both must hold:
 *       1. the helper said «refused while `pam_faillock` had the account
 *          LOCKED» for THIS delivery — PAM's own words, seen before the
 *          password was asked (`authentication.c`, `FAILLOCK_LOCKED`): while it
 *          lasts no password can pass, the right one included, so the guess
 *          was useless;
 *       2. the key (§4.4-bis) had an ADMITTED login during the last 30 days
 *          (`good_recent()`: the SAME notion as the two PAM places kept for a
 *          known key, `RESERVED_FOR_KNOWN`).
 *     ⛔ Why 2: only a REAL account can be locked (`pam_faillock` ignores
 *        unknown users), so «not counted» for anyone would be a user-name
 *        oracle (§4.4, §11.39).  For a key that never logged in the no counts
 *        exactly as before; the owner coming back from home or office does not
 *        ban themselves.
 *     ⭐ In the model of §4.4-bis B «not counted» is `login_release()` (the
 *        booking given back, no failure added), as for the defects of ours;
 *        the caller does that when this returns true.
 *     ⚠ `ticket` is the one of THIS delivery, on the orphan road too
 *       (`rcp_orphan_verdict()` gets it from `transport_verdict_from()`): the mark is
 *       set only around ONE delivery and it must be THAT delivery's, so a mark
 *       left by another request never excuses this one.
 *     ⚠ Nothing else changes: the ban check before PAM, the checks in flight
 *       per address, the fixed second and `REJECTED 0x07` on the wire. */
static bool refusal_uncounted(const struct sink *k, uint64_t ticket,
                              const char *key, uint64_t now)
{
	if (!locked_ticket || ticket != locked_ticket)
		return false;
	if (!good_recent(key, now)) {
		say(k, "PAM refused request %llu while pam_faillock had the account "
		       "LOCKED; %s never logged in (30 days), so it COUNTS as a "
		       "failed attempt (DECISIONS.md §11.47)",
		    (unsigned long long)locked_ticket, key);
		return false;
	}
	say(k, "⚠ PAM refused request %llu while pam_faillock had the account "
	       "LOCKED (even a right password is refused until it unlocks, or "
	       "`faillock --user <name> --reset`): %s logged in lately, so it is "
	       "NOT counted towards the ban — the booking is given back (§4.4-bis, "
	       "DECISIONS.md §11.47)",
	    (unsigned long long)locked_ticket, key);
	return true;
}

/* The ban file.  Defined below; declared here because the report below
 * writes it when a ban is born. */
static void save_ban(const struct sink *k, uint64_t now);

/* Says what `login_resolve()` found, and writes the ban file if a ban was born. */
static void login_report(const struct sink *k, const char *key, const char *user,
                         bool admitted, const struct login_result *r, uint64_t now)
{
	char tag[96];
	const char *shown = log_user(user, tag, sizeof tag, true);
	bool any_ban = false;
	if (r->evicted[0])
		say(k, "⚠ attempt table full (%d entries): evicted the entry «%s» to "
		       "make room — §4.4-bis",
		    MAX_ATTEMPTS, r->evicted);
	if (r->refused_full)
		say(k, "⛔ attempt table full and without a place that can be freed "
		       "(everything in it is banned or in flight): %d level(s) of this "
		       "failure could NOT be counted.  Refusals for this reason so "
		       "far: %u — §4.4-bis",
		    r->refused_full, login_refused_full);
	if (admitted) {
		say(k, "successful login from %s as %s: the failures of this user on "
		       "this address go back to zero (there were %d); the recidivism "
		       "and the counters of the address and of the /48 are NOT touched "
		       "— §4.4-bis",
		    key, shown, r->reset_amount);
		return;
	}
	say(k, "failed attempt from %s as %s: %d of %d for the user, %d of %d for the "
	       "address, %d of %d for the IPv6 /48 within the window (§4.4-bis)",
	    key, shown, r->inside[LK_USER], LIMIT[LK_USER], r->inside[LK_KEY],
	    LIMIT[LK_KEY], r->inside[LK_NET48], LIMIT[LK_NET48]);
	for (int j = 0; j < LEVELS; j++) {
		if (r->already[j])
			say(k, "the %s was already banned when this verdict arrived: "
			       "nothing added (§4.4-bis)",
			    LEVEL_NAME[j]);
		if (!r->banned[j])
			continue;
		any_ban = true;
		say(k, "⛔ BANNED %s of %s%s%s for %llu minutes (ban number %d, the "
		       "ladder is 15 min / 1 h / 12 h and ends there): %d failures "
		       "within %llu minutes (§4.4-bis, DECISIONS-11.md)",
		    LEVEL_NAME[j], key, j == LK_USER ? " as " : "",
		    j == LK_USER ? shown : "", (unsigned long long)(r->ban_ms[j] / 60000u),
		    r->ban_number[j], LIMIT[j], (unsigned long long)(WINDOW_MS[j] / 60000u));
	}
	if (any_ban)
		save_ban(k, now);
}

/* ⛔ Writes to file the bans in force and the recidivism not yet forgotten,
 * one line each, with the expiry in seconds since the epoch.  Called at every
 * change — new ban, unblock — because a ban that lives only in memory until
 * the next periodic save is a ban that a sudden restart takes away (I7).
 *
 * THE FORMAT (since 24 Oct 2026):   B2 <U|K|N> <level> <epoch> <key>[ <user>]
 *   U = (key, user), K = key, N = IPv6 /48; `level` = bans suffered (0..2);
 *   `epoch` = when the ban ends (in the past for a ban that has ended and is
 *   only remembered); the user, last because it may contain spaces, only for U.
 * The 1.0 wrote «<[address]> <epoch>»: `rcp_ban_load()` still reads it.
 *
 * ⚠ It writes to a temporary file and renames: a `rename()` is atomic, and
 *   a ban file truncated halfway by a restart would be worse than no
 *   file — it would say «these addresses were not banned». */
static void save_ban(const struct sink *k, uint64_t now)
{
	if (ban_path[0] == 0)
		return;
	char tmp[sizeof ban_path + 8];
	snprintf(tmp, sizeof tmp, "%s.new", ban_path);
	/* ⛔ 0600 from the first byte (`open`, not `fopen`: the file is born with the
	 *    right mode, no moment in which it is readable by others). */
	int fd = open(tmp, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0600);
	FILE *f = fd >= 0 ? fdopen(fd, "w") : NULL;
	if (fd >= 0 && !f)
		close(fd);
	if (f && fchmod(fd, 0600) != 0) {
		fclose(f);
		f = NULL;
	}
	if (!f) {
		say(k, "⛔ could not write the ban file «%s»: the ban "
		       "lives only in memory and a restart removes it (§4.4-bis)",
		    tmp);
		return;
	}
	static const char KIND_CHAR[LEVELS] = {'U', 'K', 'N'};
	time_t t_now = time(NULL);
	int amount = 0;
	for (int i = 0; i < MAX_ATTEMPTS; i++) {
		const struct lentry *e = &attempts[i];
		if (!e->used || level_now(e, now) == 0)
			continue;
		long long epoch =
		    is_banned(e, now)
		        ? (long long)t_now + (long long)((e->banned_until - now) / 1000)
		        : (long long)t_now - (long long)((now - e->banned_until) / 1000);
		fprintf(f, "B2 %c %d %lld %s%s%s\n", KIND_CHAR[e->kind],
		        (int)level_now(e, now), epoch, e->address,
		        e->kind == LK_USER ? " " : "", e->kind == LK_USER ? e->user : "");
		if (is_banned(e, now))
			amount++;
	}
	/* ⚠ fsync BEFORE the rename: a rename that survives a crash with a file
	 *    that does not is the «truncated ban file» this function exists to avoid. */
	bool bad = ferror(f) != 0 || fflush(f) != 0 || fsync(fd) != 0;
	if (fclose(f) != 0)
		bad = true;
	if (bad || rename(tmp, ban_path) != 0)
		say(k, "⛔ could not write/rename the ban file «%s»", ban_path);
	else
		say(k, "the ban file is up to date: %d bans in force in «%s»", amount,
		    ban_path);
}

/* ------------------------------------------------------------------------ */
/* What the HOST calls: the page over TCP and the unblock command.
 *
 * ⛔ The page is served ALL THE SAME to a banned address, and says the attempts
 *    are used up (`DECISIONS.md` §1.9): whoever is banned by mistake is almost
 *    always the owner, and a network error would tell them nothing.  Whoever
 *    serves the page calls `rcp_banned()` and writes the sentence.
 *    ⚠ The page does not know the user: it answers for the levels that do
 *    not depend on it (the address, the /48).                              */
bool rcp_banned(const char *provenance, uint64_t now, uint64_t *remain_ms)
{
	char addr[64], addr48[64];
	uint64_t best = 0;
	bool any = false;
	/* ⛔ The key is made by `rcp_key_address()`, not by cutting the port:
	 *    `rcp.h` promises that «`provenance` may carry the port: it is cut
	 *    in here», and whoever believes the header passes
	 *    `192.168.0.2` without brackets — finding B-8. */
	rcp_key_address(provenance, addr, sizeof addr);
	int idx[2] = {lfind(LK_KEY, addr, NULL), -1};
	if (key_net48(addr, addr48, sizeof addr48))
		idx[1] = lfind(LK_NET48, addr48, NULL);
	for (int j = 0; j < 2; j++)
		if (idx[j] >= 0 && is_banned(&attempts[idx[j]], now)) {
			uint64_t rem = attempts[idx[j]].banned_until - now;
			any = true;
			if (rem > best)
				best = rem;
		}
	if (remain_ms)
		*remain_ms = best;
	return any;
}

/* ⛔ The unblock command.  Returns `true` if something that was BANNED was
 * removed: «it was not banned» and «I unblocked it» are two different facts,
 * and whoever commands must be able to tell them apart.  It removes EVERY
 * level that concerns the address: its (key, user) pairs, the key, the /48 —
 * bans, recidivism and failures; only the in-flight bookings stay (their
 * verdicts are still to come, and they will give them back).
 * ⚠ And the unblock is written to the log by the caller, which has the
 * context: here there is no session to hang it on. */
bool rcp_unblock(const char *address, uint64_t now)
{
	char addr[64], addr48[64];
	bool was_banned = false, touched = false;
	/* ⛔ §4.4-bis: «whoever types `192.168.0.2` at the unblock command MUST
	 *    reach the same key: normalisation belongs to the server, not to
	 *    whoever commands» — finding B-8. */
	rcp_key_address(address, addr, sizeof addr);
	bool has48 = key_net48(addr, addr48, sizeof addr48);
	for (int i = 0; i < MAX_ATTEMPTS; i++) {
		struct lentry *e = &attempts[i];
		if (!e->used)
			continue;
		bool mine = ((e->kind == LK_USER || e->kind == LK_KEY) &&
		             strcmp(e->address, addr) == 0) ||
		            (e->kind == LK_NET48 && has48 && strcmp(e->address, addr48) == 0);
		if (!mine)
			continue;
		if (is_banned(e, now))
			was_banned = true;
		touched = true;
		int flight = e->in_flight;
		char kind = (char)e->kind;
		char address_copy[64], user_copy[65];
		snprintf(address_copy, sizeof address_copy, "%s", e->address);
		snprintf(user_copy, sizeof user_copy, "%s", e->user);
		memset(e, 0, sizeof *e);
		if (flight > 0) { /* keep the booking: the verdict will come */
			e->used = true;
			e->kind = (uint8_t)kind;
			e->in_flight = flight;
			e->last_touch = now;
			snprintf(e->address, sizeof e->address, "%s", address_copy);
			snprintf(e->user, sizeof e->user, "%s", user_copy);
		}
	}
	if (touched)
		save_ban(NULL, now);
	return was_banned;
}

/* ⛔ Declares where the ban file lives and reads it back: a ban that does not
 * survive a restart is a protection that gets lost (I7).  Returns how many
 * bans in force it loaded, or -1 if the file was there and could not be read —
 * ⚠ «zero bans» and «I could not look» are two different facts
 * (`LESSONS.md` §1.9 rule 1), and the caller must print them differently.
 *
 * ⭐ It reads BOTH formats.  An old line, «[address] epoch», is the 12-hour ban
 *    of the 1.0: it becomes a ban of the key (the /64 for IPv6) at the top of
 *    the ladder; the file is rewritten in the new format at the next change.
 * ⚠ The recidivism of a ban that ended less than 24 h ago is read back too.
 *   `now` can be smaller than the time since that ban (it restarts with the
 *   process): then the end of the ban is clamped to 1, and the memory lasts a
 *   little longer than it should — the cautious side. */
int rcp_ban_load(const char *fpath, uint64_t now)
{
	ban_path[0] = 0;
	if (!fpath || !*fpath)
		return 0;
	snprintf(ban_path, sizeof ban_path, "%s", fpath);
	FILE *f = fopen(ban_path, "r");
	if (!f) {
		/* ⛔ HERE LAY THE SEVENTH GUISE OF THE DEFECT, INSIDE THE FUNCTION THE
		 *    HEADER DECLARES IMMUNE.  `rcp.h` promises «-1 if the file was
		 *    there and could not be read», and this line returned `0` on
		 *    ANY failure of `fopen()`: a file without permissions, a path whose
		 *    parent is not a directory, a disk that does not answer — all
		 *    «zero bans», that is **the protection switched off with the air of
		 *    having nothing to protect** (`LESSONS.md` §1.9 rule 1, and I7).
		 *
		 * ⭐ Only one datum tells the two facts apart, and it is `errno`:
		 *    `ENOENT` means the file has not been born yet — no bans, and it is
		 *    not an error — and any other value means the file is there (or it
		 *    could not even be asked) and could not be looked at.  ⚠ The caller
		 *    MUST treat `-1` as a fault and not as a zero: whoever serves the
		 *    page says so, and whoever starts the server stops. */
		return errno == ENOENT ? 0 : -1;
	}
	static const int none[LEVELS] = {-1, -1, -1};
	time_t t_now = time(NULL);
	char line[1024];
	int amount = 0;
	while (fgets(line, sizeof line, f)) {
		char key[64] = "", user[65] = "";
		int kind = LK_KEY, level = 2;
		long long exp = 0;
		line[strcspn(line, "\r\n")] = 0;
		if (strncmp(line, "B2 ", 3) == 0) {
			char kc = 0;
			int off = 0;
			if (sscanf(line + 3, "%c %d %lld %n", &kc, &level, &exp, &off) < 3 ||
			    level < 0 || level > 2)
				continue;
			kind = kc == 'U' ? LK_USER : kc == 'K' ? LK_KEY : kc == 'N' ? LK_NET48 : -1;
			if (kind < 0)
				continue;
			const char *p = line + 3 + off, *sp = strchr(p, ' ');
			size_t kl = sp ? (size_t)(sp - p) : strlen(p);
			if (kl == 0 || kl >= sizeof key)
				continue;
			memcpy(key, p, kl);
			key[kl] = 0;
			if (kind == LK_USER) {
				/* the HMAC of the name: exactly 64 lowercase hex digits */
				if (!sp || strlen(sp + 1) != 64 ||
				    strspn(sp + 1, "0123456789abcdef") != 64)
					continue;
				snprintf(user, sizeof user, "%s", sp + 1);
			}
		} else {
			char addr[64];
			if (sscanf(line, "%63s %lld", addr, &exp) != 2 || exp <= (long long)t_now)
				continue; /* not a line, or expired while the server was off */
			snprintf(key, sizeof key, "%s", addr);
		}
		char norm[64];
		rcp_key_address(key, norm, sizeof norm); /* idempotent: also converts the old forms */
		/* ⛔ A file is input: a negative epoch is not a time, and a ban can
		 *    never last more than the top of the ladder — a corrupt or
		 *    hostile line must not make a ban of 100 years nor overflow. */
		if (exp < 0)
			continue;
		uint64_t until;
		if (exp > (long long)t_now) {
			uint64_t left_s = (uint64_t)(exp - (long long)t_now);
			if (left_s > LADDER_MS[2] / 1000u)
				left_s = LADDER_MS[2] / 1000u;
			until = now + left_s * 1000u;
		} else {
			uint64_t ago = (uint64_t)((long long)t_now - exp) * 1000u;
			if (level == 0 || ago >= FORGET_MS)
				continue; /* ended and forgotten */
			until = ago < now ? now - ago : 1;
		}
		int i = lfind(kind, norm, user);
		if (i < 0)
			i = lcreate(kind, norm, user, now, none, NULL, 0);
		if (i < 0)
			continue; /* the table is full of bans: nothing to evict */
		if (until > attempts[i].banned_until)
			attempts[i].banned_until = until;
		if (level > attempts[i].level)
			attempts[i].level = (uint8_t)level;
		/* ⛔ No count is rebuilt: what survives the restart is the BAN and
		 * the memory of it, not the attempts that produced it. */
		if (is_banned(&attempts[i], now)) {
			if (attempts[i].level == 0)
				attempts[i].level = 1; /* a ban in force is at least the first */
			amount++;
		}
	}
	/* ⚠ And a read that stops halfway is also «I could not look»: `fgets`
	 *   returns NULL both at end of file and on an error, and the two are told
	 *   apart only with `ferror()`.  A ban file read halfway would say «these
	 *   addresses were not banned». */
	int broken = ferror(f);
	fclose(f);
	return broken ? -1 : amount;
}

/* A verdict that arrives when its CONNECTION IS GONE — the client closed
 * while PAM was answering.  ⛔ It is counted all the same, from the name and
 * the address that the request in flight carries (`struct flight`,
 * `helper.c`): otherwise opening a connection per attempt and closing it at
 * once would be the way to try passwords for free.  `rhost` is the bare
 * address of PAM_RHOST.  The lines go to `fn`, because there is no session to
 * hang them on. */
void rcp_orphan_verdict(const char *user, const char *rhost, bool admitted,
                        bool lost, uint64_t ticket, uint64_t now, rcp_line_fn fn, void *ctx)
{
	struct sink k = {NULL, fn, ctx};
	struct login_result r;
	char key[64];
	if (!user || !*user || !rhost || !*rhost) {
		say(&k, "⚠ verdict of a connection that is gone, without name or "
		        "address: NOT counted (§4.4-bis)");
		return;
	}
	rcp_key_address(rhost, key, sizeof key);
	/* ⭐ D4b: «not checked» (`rcp_refusal_unchecked()`) is the same case as a
	 *    dead helper: our defect, nothing counted, the booking given back. */
	if (!admitted && unchecked_ticket && ticket == unchecked_ticket)
		lost = true;
	if (lost) {
		/* ⛔ The helper died: that is a defect of OURS, and it must not ban
		 *    anybody.  The booking is given back and nothing is counted. */
		login_release(key, user);
		say(&k, "⭐ the connection was gone and the PAM helper died before "
		        "answering: our defect, the booking is given back and NOTHING "
		        "is counted (§4.4-bis)");
		return;
	}
	if (!admitted && refusal_uncounted(&k, ticket, key, now)) {
		login_release(key, user);
		return;
	}
	login_resolve(key, user, admitted, now, &r);
	say(&k, "⭐ the connection was gone when PAM answered (%s): the verdict is "
	        "counted all the same (§4.4-bis)",
	    admitted ? "admitted" : "refused");
	login_report(&k, key, user, admitted, &r, now);
}

/* ⛔ For the bench only: between one test and the next one starts from zero.
 * In a real server nobody calls it, and it is written in the header. */
void rcp_reset_session_log(void)
{
	/* ⚠ The table is allocated (phase 10): the cells that exist are zeroed,
	 *   and if it is not there yet there is nothing to zero. */
	if (attached)
		memset(attached, 0, (size_t)how_many_slots * sizeof *attached);
	memset(attempts, 0, sizeof attempts);
	login_refused_full = 0;
}

/* ------------------------------------------------------------------------ */
/* Writing the types of §6.0, big-endian, without alignment and without
 * padding.                                                                  */
typedef struct {
	uint8_t *b;
	size_t cap, len;
	bool full;
} writer;

static void sc_byte(writer *s, uint8_t v)
{
	if (s->len + 1 > s->cap) {
		s->full = true;
		return;
	}
	s->b[s->len++] = v;
}
static void sc_u16(writer *s, uint16_t v)
{
	sc_byte(s, (uint8_t)(v >> 8));
	sc_byte(s, (uint8_t)v);
}
static void sc_u32(writer *s, uint32_t v)
{
	sc_byte(s, (uint8_t)(v >> 24));
	sc_byte(s, (uint8_t)(v >> 16));
	sc_byte(s, (uint8_t)(v >> 8));
	sc_byte(s, (uint8_t)v);
}
/* ⛔ §6.0: `u64` big-endian, and it serves only the `instant` field of §6.2 —
 * the only eight-byte integer RCP/1 puts on the wire. */
static void sc_u64(writer *s, uint64_t v)
{
	for (int i = 7; i >= 0; i--)
		sc_byte(s, (uint8_t)(v >> (i * 8)));
}
static void sc_str(writer *s, const char *t)
{
	size_t n = strlen(t);
	sc_u16(s, (uint16_t)n);
	for (size_t i = 0; i < n; i++)
		sc_byte(s, (uint8_t)t[i]);
}

/* Reading, with the bounds check BEFORE taking the bytes. */
typedef struct {
	const uint8_t *b;
	size_t len, i;
	bool too_short;
} reader;

static uint8_t le_u8(reader *l)
{
	if (l->i + 1 > l->len) {
		l->too_short = true;
		return 0;
	}
	return l->b[l->i++];
}
static uint16_t le_u16(reader *l)
{
	uint16_t a = le_u8(l);
	return (uint16_t)((a << 8) | le_u8(l));
}
static uint32_t le_u32(reader *l)
{
	uint32_t a = le_u16(l);
	return (a << 16) | le_u16(l);
}
/* Copies a string into `report` (which must have room for n+1 bytes).
 * ⛔ It does not validate UTF-8: that is done by `valid_utf8`, called where needed. */
static size_t le_str(reader *l, char *report, size_t cap)
{
	uint16_t n = le_u16(l);
	if (l->too_short || l->i + n > l->len) {
		l->too_short = true;
		return 0;
	}
	if (n + 1u > cap) {
		/* longer than the field allows: the caller will say so */
		l->i += n;
		return (size_t)n;
	}
	memcpy(report, l->b + l->i, n);
	report[n] = 0;
	l->i += n;
	return n;
}

/* §6.0: invalid UTF-8 is PROTOCOL_ERROR. */
static bool valid_utf8(const char *s, size_t n)
{
	size_t i = 0;
	while (i < n) {
		uint8_t c = (uint8_t)s[i];
		size_t extra;
		if (c < 0x80)
			extra = 0;
		else if ((c & 0xE0) == 0xC0 && c >= 0xC2)
			extra = 1;
		else if ((c & 0xF0) == 0xE0)
			extra = 2;
		else if ((c & 0xF8) == 0xF0 && c <= 0xF4)
			extra = 3;
		else
			return false;
		/* ⚠ The continuation bytes must ALL BE THERE: without this
		 * check a sequence truncated at the end of the string would pass. */
		if (i + extra >= n)
			return false;
		for (size_t k = 1; k <= extra; k++)
			if ((((uint8_t)s[i + k]) & 0xC0) != 0x80)
				return false;
		i += extra + 1;
	}
	return true;
}

/* ⛔⭐ A NUL BYTE IN THE MIDDLE OF A STRING — finding R9.11.
 *
 * §6.0 says a string is «exactly `length` bytes».  All the validations of
 * this module work on the DECLARED LENGTH; all the uses work on the C STRING
 * that `le_str` terminates with a zero (`%s`, `strcmp`, `entry_present`,
 * `strchr`, and PAM).  A `0x00` in the middle separates the two readings, and
 * `valid_utf8()` accepts it because `c < 0x80`:
 *
 *   `audio.codec` with value `opus\0pcm` — eight bytes, within the limit —
 *   sent away with `NOTHING_IN_COMMON` a client that had declared
 *   `pcm`, that is it denied the fallback to whoever had not refused it;
 *   a user `root\0nemo` — nine bytes on the wire — sent `root` to PAM, and the
 *   log and the key of §4.4-bis said `root`.  What arrived and what was judged
 *   were two different strings, and no line said so.
 *
 * ⭐ §4.3 already closes it for capabilities: «a value is **printable** UTF-8
 *    text».  Here it is applied to the letter — and it also applies to the user
 *    name, for a second reason: the log is a file that is kept (§11.1), and a
 *    newline inside a name writes lines into it that nobody sent. */
static bool printable_text(const char *s, size_t n)
{
	if (!valid_utf8(s, n))
		return false;
	for (size_t i = 0; i < n; i++) {
		uint8_t c = (uint8_t)s[i];
		if (c < 0x20 || c == 0x7F) /* the C0 controls and DEL: 0x00 included */
			return false;
	}
	return true;
}

/* §8.2: the reasons are sixteen, from 0x01 to 0x10 (`SESSION_TERMINATED`, 15 Aug
 * 2026, is one of them, and a client FAREWELL carrying it is accepted).  ⛔ And
 * §3.1: «code 0 means closing without a reason and MUST NOT be used». */
static bool reason_for_82(uint8_t m) { return m >= 0x01 && m <= 0x10; }

/* ------------------------------------------------------------------------ */
/* (the declaration is at the top, above the attempt limiter) */
static void reg(rcp_session *s, const char *fmt, ...)
{
	char line[512];
	va_list ap;
	va_start(ap, fmt);
	vsnprintf(line, sizeof line, fmt, ap);
	va_end(ap);
	if (s->g.record)
		s->g.record(s->g.ctx, line);
}

static void send_message(rcp_session *s, uint16_t kind, const uint8_t *body,
                            size_t n)
{
	uint8_t head[6];
	writer w = {head, sizeof head, 0, false};
	sc_u16(&w, kind);
	sc_u32(&w, (uint32_t)n);
	uint8_t *overall = (uint8_t *)malloc(6 + n);
	if (!overall)
		return;
	memcpy(overall, head, 6);
	if (n)
		memcpy(overall + 6, body, n);
	s->g.send_msg(s->g.ctx, overall, 6 + n);
	free(overall);
}

/* ⛔ §3.1, in order: one writes to the log WHAT happened, sends FAREWELL if
 * the channel is still usable, closes the session with the reason code.
 * The two roads exist because if one breaks the other still carries the
 * reason — in v1 the server wrote «farewell» and the client read
 * «network error» for three phases.                                         */
static void dismiss(rcp_session *s, uint8_t reason, const char *detail)
{
	if (s->state == S_FINISHED)
		return;
	reg(s, "farewell reason=%#04x detail=%s state=%s", reason, detail,
	    STATE_NAMES[s->state]);
	/* ⛔⭐ §7.3 — AND BEFORE ANYTHING ELSE WHAT IS PRESSED IS RELEASED.
	 *
	 *     «When a connection ends — by farewell, by silence, by
	 *     error — the server MUST release every key and every button that
	 *     are pressed».  ⛔ It sits HERE, inside `dismiss()`, and not next to
	 *     each of its thirty calls: `RCP.md` §11 calls it «the rule
	 *     with the highest harm/cost ratio of the document», and a rule with
	 *     that ratio is not entrusted to the discipline of whoever writes the
	 *     thirty-first.  It is invariant I7 read from inside — the protection
	 *     lives in the program, not in a line that can get lost.
	 *
	 * ⚠ The symptom one buys: a Ctrl left down in a session that
	 *   outlives the client makes the desktop unusable on reattach, and
	 *   nobody connects the two things. */
	release_on_detach(s, "farewell");
	uint8_t body[512];
	writer w = {body, sizeof body, 0, false};
	sc_byte(&w, reason);
	sc_str(&w, detail);
	if (!w.full)
		send_message(s, T_FAREWELL, body, w.len);
	if (s->is_attached) {
		slot_leave(s->user);
		s->is_attached = false;
	}
	s->state = S_FINISHED;
	s->g.close(s->g.ctx, reason);
}

/* ⛔ `REJECTED` is the farewell of authentication: after it one closes with
 * the same reason, and does NOT also send FAREWELL (§4.4).                   */
static void reject(rcp_session *s, uint8_t reason)
{
	char tag[96];
	reg(s, "rejected reason=%#04x user=%s from=%s", reason,
	    log_user(s->user, tag, sizeof tag, s->user_lookup_ok), s->provenance);
	uint8_t body[1];
	body[0] = reason;
	send_message(s, T_REJECTED, body, 1);
	s->state = S_FINISHED;
	s->g.close(s->g.ctx, reason);
}

/* ------------------------------------------------------------------------ */
/* §4.3 — the capabilities                                                   */
static bool valid_name(const char *n, size_t len)
{
	if (len < 1 || len > 64)
		return false;
	for (size_t i = 0; i < len; i++) {
		char c = n[i];
		if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '.' ||
		      c == '_'))
			return false;
	}
	return true;
}

/* An entry inside a comma-separated list. */
static bool entry_present(const char *list, const char *entry)
{
	size_t n = strlen(entry);
	const char *p = list;
	while (*p) {
		const char *comma = strchr(p, ',');
		size_t m = comma ? (size_t)(comma - p) : strlen(p);
		if (m == n && strncmp(p, entry, n) == 0)
			return true;
		p = comma ? comma + 1 : p + m;
	}
	return false;
}

/* Intersects two comma-separated lists, in the CLIENT's order (§4.3:
 * «the one who chooses is the server, within the intersection, following the
 * client's order of preference»).  Returns the first common entry, or NULL.
 *
 * ⛔ `discards` collects the entries thrown away because we do not know them.
 *    §4.3 says they are discarded; ⚠ but a discard that is not written is a
 *    successful negotiation with the opposite of what was wanted inside it —
 *    trap 4 of `LESSONS.md` §4 — and the symptom arrives months later, in the
 *    form of «it is slow and nobody understands why».
 *
 * ⛔⭐ AND THREE DISCARDS DID NOT GO THROUGH `discards` — finding R9.12, that is
 *    three silent tolerances inside the very function that takes care of the
 *    log:
 *
 *      an entry ≥ 31 bytes long: `n + 1 < cap` was false, because `cap` is
 *      `sizeof s->codec` = 32 — and that condition governed the
 *      CLASSIFICATION, not only the choice.  The entry was not compared,
 *      was not chosen and did not end up among the discards;
 *      an empty entry (`hevc,,av1`): same;
 *      the entries that did not fit in the discard buffer: discarded twice,
 *      and the second time in silence.
 *
 *    `video.codec = av1,questo.codec.ha.un.name.lunghissimo` chose `av1` and
 *    wrote `negotiated video.codec=av1` **without** the discard line: the
 *    day a client of tomorrow offers a codec with a long name, the
 *    log — which §4.3 declares «the only place where that fact appears» —
 *    would not contain it.  §3: «a silent tolerance is indistinguishable from
 *    a defect».
 *
 * ⭐ `*amount` counts ALL the discards, even those that do not fit in the
 *    buffer: the number tells the truth even when the list is truncated. */
static const char *first_in_common(const char *client_list, const char *our,
                                char *report, size_t cap, char *discards,
                                size_t cap_discards, int *amount)
{
	if (discards && cap_discards)
		discards[0] = 0;
	*amount = 0;
	const char *choice = NULL;
	const char *p = client_list;
	while (*p) {
		const char *comma = strchr(p, ',');
		size_t n = comma ? (size_t)(comma - p) : strlen(p);
		/* ⚠ 257 and not 64: a capability value goes up to 256 bytes (§4.3),
		 *   and an entry that does not fit in the comparison buffer is
		 *   precisely the entry that used to vanish. */
		char entry[257];
		const char *to_discard = NULL;
		if (n == 0) {
			/* `hevc,,av1`: §4.3 wants entries separated by commas, and an empty
			 * entry is not an entry.  It is not closed — it changes nothing of
			 * what is negotiated — but it is WRITTEN. */
			to_discard = "(empty)";
		} else if (n >= sizeof entry) {
			to_discard = "(entry longer than the allowed value)";
		} else {
			memcpy(entry, p, n);
			entry[n] = 0;
			/* ⛔ An unknown entry INSIDE a list is discarded, as an unknown
			 * name is discarded: it is the mechanism by which a client of
			 * tomorrow will talk to a server of today. */
			if (entry_present(our, entry)) {
				/* ⚠ The FIRST common one is kept, but one does not leave: the
				 *   entries after it must still be classified, or the discard
				 *   that gets written would be only the one preceding the choice. */
				if (!choice) {
					if (n + 1 > cap) {
						/* ⚠ It cannot happen: `our` is one of our constants
						 *   and our entries are short.  If it happened, the
						 *   entry is not lost in silence — it is discarded and
						 *   written, which is the point of this finding. */
						to_discard = entry;
					} else {
						/* ⚠ `%.*s` and not `%s`: to the compiler the length of
						 *   `entry` is unknown, and with `%s` it warns about a
						 *   truncation that the guard above has already
						 *   excluded.  A warning known to be harmless is a
						 *   warning one stops reading the next day. */
						snprintf(report, cap, "%.*s", (int)n, entry);
						choice = report;
					}
				}
			} else {
				to_discard = entry;
			}
		}
		if (to_discard) {
			(*amount)++;
			if (discards && cap_discards) {
				size_t g = strlen(discards);
				size_t m = strlen(to_discard);
				if (g + m + 2 < cap_discards)
					snprintf(discards + g, cap_discards - g, "%s%s", g ? "," : "",
					         to_discard);
			}
		}
		p = comma ? comma + 1 : p + n;
	}
	return choice;
}

/* What this server declares. */
/* ⛔⭐⭐ AV1 HAS GONE — 20 Aug 2026, `DECISIONS.md` §1.13-ter, decided
 *     by the user: «the choice is forced: we must abandon AV1».
 *
 * The three reasons, and the third arrived last:
 *   1. **Firefox for Android** has neither HEVC nor AV1 ⇒ for that browser the
 *      product did not exist, against the promise of §1.6;
 *   2. `[M]` AV1 was the only codec **without hardware anywhere** in
 *      this setup — software at both ends;
 *   3. ⛔ `[M]` 20 August: with AV1 **Firefox paints rectangular blocks**
 *      where Chrome and `ffmpeg/dav1d`, **on the same bytes and at the same
 *      instant**, are clean.  It was the suspect of the artefact hunt.
 *
 * ⚠ Number 2 of §6.2 stays AV1 forever: it is not reused (an old client
 *   that heard «2» would paint garbage without an error).  Here it leaves the
 *   NEGOTIATION, not the register of numbers. */
#define OUR_DEFAULT_CODEC "hevc,h264"
#define OUR_DEPTH "8,10"

/* ⭐⭐ PHASE 18 (30 Sep 2026) — THE CODEC LIST IS MEASURED, NOT WRITTEN.
 *
 * The parent SETS it at startup after the probe of `child_video_capabilities()`:
 * «hevc» only if the card encodes HEVC, «h264» only if the card encodes
 * H.264, «» if nothing — ⛔ phase 19 (1 Oct 2026, `DECISIONS.md` §10.27): the
 * software fallback (OpenH264) has gone, no processor without a card.
 * ⛔ The browser must not
 * receive an offer the server cannot keep: negotiating «hevc» and
 * then not opening it was a black screen without a line naming it.
 * ⚠ The default stays yesterday's for the bench harness
 *   (`benches/rcp/`), which has no card to probe; the product ALWAYS writes it
 *   (`main.c`), and with the list empty every HELLO ends in
 *   NOTHING_IN_COMMON — declared at startup and in the farewell. */
static char our_codec[64] = OUR_DEFAULT_CODEC;

void rcp_video_codec_set(const char *list)
{
	snprintf(our_codec, sizeof our_codec, "%s", list ? list : "");
}

const char *rcp_video_codec(void)
{
	return our_codec;
}
#define OUR_AUDIO "opus,pcm"

/* ⏳ §13 — PROPOSED.  ⛔ Born OFF (I6).  ⚠ Like the other switches of this
 *    module, the value in force is written at startup by whoever sews things
 *    together (`main.c`), on AND off. */
static bool pace_offered;

void rcp_pace_offer(bool on) { pace_offered = on; }

bool rcp_pace_offered(void) { return pace_offered; }

/* ⛔ §13.5 — every `u16` is legal and is CLAMPED, never refused: 0 and
 *    everything from the stage's own rate up mean «no ceiling», below the
 *    floor means the floor.  ⇒ A client can only LOWER its own rate, and
 *    never below `RCP_PACE_FLOOR_FPS`. */
uint16_t rcp_pace_clamp(uint32_t asked)
{
	if (asked == 0 || asked >= RCP_PACE_TOP_FPS)
		return 0;
	if (asked < RCP_PACE_FLOOR_FPS)
		return (uint16_t)RCP_PACE_FLOOR_FPS;
	return (uint16_t)asked;
}

static void send_here_i_am(rcp_session *s)
{
	uint8_t body[1024];
	writer w = {body, sizeof body, 0, false};
	/* ⛔ 24 Oct 2026: counted from what is WRITTEN — since 84fdf573 `bench.mark`
	 *    exists only in a BENCH build, and the product build declared 5 and
	 *    wrote 4 (the page's DataView read past the end of the message). */
	uint16_t n_caps = 4; /* video.codec, video.depth, audio.codec, clipboard.text */
#ifdef REMOTIX_BENCH
	n_caps++; /* bench.mark (§7.5), only in the bench build */
#endif
	/* ⏳ §13: declared only when switched on AND when the host can apply it —
	 *    declaring a capability nobody serves is the lie §4.3 forbids. */
	s->pace_declared = pace_offered && s->g.pace;
	if (s->pace_declared)
		n_caps++;
	sc_u16(&w, RCP_VERSION);
	sc_u16(&w, n_caps);
	sc_str(&w, "video.codec");
	sc_str(&w, our_codec);
	sc_str(&w, "video.depth");
	sc_str(&w, OUR_DEPTH);
	sc_str(&w, "audio.codec");
	sc_str(&w, OUR_AUDIO);
	sc_str(&w, "clipboard.text");
	sc_str(&w, "yes");
	/* ⛔ §4.3: `bench.mark` is `no` in every normal installation, and a
	 * server that declared it `yes` by mistake writes it to the log at every
	 * startup.
	 *
	 * ⛔⭐ AND THE DECLARATION IS READ FROM THE SWITCH, NOT FROM A CONSTANT —
	 *    finding R9.14.  Here there was the string `"no"` written by hand:
	 *    bringing `BENCH_ON` to 1 — the only way foreseen today to switch
	 *    the function on — the server ACCEPTED `BENCH_MARK` and painted on
	 *    someone's desktop while its `HERE_I_AM` kept declaring `no`.  Two
	 *    places that must change together and no link between them: §7.5
	 *    rule 3 («the server MUST declare it»), and invariant I6.
	 *    ⚠ The log line of the switch-on is in `rcp_open()`, which is
	 *      the only «startup» this module knows. */
#ifdef REMOTIX_BENCH
	sc_str(&w, "bench.mark");
	sc_str(&w, BENCH_ON ? "yes" : "no");
#endif
	if (s->pace_declared) {
		sc_str(&w, "video.pace");
		sc_str(&w, "yes");
	}
	if (!w.full)
		send_message(s, T_HERE_I_AM, body, w.len);
}

/* ------------------------------------------------------------------------ */
/* ⛔⭐ `video.max_size` — THE DECODER CEILING (§4.3, §4.5)
 *
 * Reads `WIDTHxHEIGHT` in **pixels**, that is two decimal integers separated
 * by a lowercase `x` and nothing else.  Returns `false` if the string does not
 * have that form.
 *
 * ⛔ And the form is checked in full, digit by digit, instead of trusting
 *    `sscanf("%ux%u")`: that accepts `1080.75x2340.25` reading `1080` and
 *    stopping at the dot, that is it would take as good a ceiling the client
 *    did not declare.  ⚠ It is exactly the value our page sent before the
 *    night of 10 Aug 2026 (finding B-6): a phone at factor 2.75 sends
 *    `1080.75x2340.25`.
 *
 * ⚠ Zero is not a size: a ceiling of 0 pixels cannot be respected by any
 *   legal canvas, and treating it as a number would send away every `ATTACH`
 *   with `SESSION_UNSERVABLE` without anything naming the field. */
static bool parse_max_size(const char *v, uint32_t *l, uint32_t *a)
{
	unsigned long long n[2] = {0, 0};
	int how_many[2] = {0, 0};
	int i = 0;

	for (const char *p = v; *p; p++) {
		if (*p == 'x' && i == 0) {
			i = 1;
			continue;
		}
		if (*p < '0' || *p > '9')
			return false;
		if (how_many[i] > 9) /* more than ten digits: beyond any screen */
			return false;
		n[i] = n[i] * 10u + (unsigned)(*p - '0');
		how_many[i]++;
	}
	if (i != 1 || how_many[0] == 0 || how_many[1] == 0)
		return false;
	if (n[0] == 0 || n[1] == 0 || n[0] > 0xffffffffull || n[1] > 0xffffffffull)
		return false;
	*l = (uint32_t)n[0];
	*a = (uint32_t)n[1];
	return true;
}

/* ------------------------------------------------------------------------ */
/* ⛔⭐ `video.level` — THE DECODER LEVEL (§4.3)
 *
 * Reads `MAJOR` or `MAJOR.MINOR` — `5`, `5.1`, `3.0` — and returns the
 * number in TENTHS: `5.1` ⇒ `51`, `5` ⇒ `50`.  ⚠ `false` if the string does not
 * have that form.
 *
 * ⛔ Why tenths and not a `double`: because the value serves a
 *    COMPARISON, and two roads that write `5.1` in floating point can give
 *    two numbers that are not equal.  ⭐ And tenths are also the alphabet in
 *    which the level is written in decoder strings: H.264 carries
 *    `level_idc = major*10 + minor` (`51` = `0x33`, the tail of
 *    `avc1.640033`), HEVC carries `general_level_idc = (major*10 +
 *    minor) * 3` (`153` = `L153`).  ⇒ A level read here and one read
 *    from the SPS on the other side compare without tables.
 *
 * ⚠ The form is checked digit by digit, and for the same reason as
 *   `parse_max_size()`: `sscanf("%u.%u")` would take as good
 *   `5.1.2` stopping at the second dot, that is a level the client did not
 *   declare.  ⛔ And the minor part is ONE digit: `5.10` is not a form
 *   that §4.3 defines, and reading it as `5.1` would be guessing.
 *
 * ⚠ Zero is not a level: no stream can respect it, and taking it as good
 *   would make every session write «produced 4.0 > asked 0.0». */
static bool parse_level(const char *v, uint32_t *x10)
{
	unsigned greater = 0, less = 0;
	int major_digits = 0, minor_digits = 0;
	bool after_point = false;

	for (const char *p = v; *p; p++) {
		if (*p == '.' && !after_point) {
			after_point = true;
			continue;
		}
		if (*p < '0' || *p > '9')
			return false;
		if (after_point) {
			if (minor_digits > 0) /* `5.10`: §4.3 does not define this form */
				return false;
			less = (unsigned)(*p - '0');
			minor_digits++;
		} else {
			if (major_digits > 2) /* more than three digits: no such level exists */
				return false;
			greater = greater * 10u + (unsigned)(*p - '0');
			major_digits++;
		}
	}
	if (major_digits == 0 || (after_point && minor_digits == 0))
		return false;
	if (greater == 0)
		return false;
	*x10 = greater * 10u + less;
	return true;
}

/* ------------------------------------------------------------------------ */
/* How many UNKNOWN capability names this server can remember for the
 * duplicate check of §4.3 — see the box inside `handle_hello()`. */
#define MAX_SEEN 64

static bool handle_hello(rcp_session *s, reader *l)
{
	uint16_t version = le_u16(l);
	if (l->too_short) {
		dismiss(s, RCP_PROTOCOL_ERROR, "HELLO without version");
		return false;
	}
	/* ⛔ §2.4: «the two MUST match» — the path `/rcp/1` says 1, and a
	 * `HELLO(2)` on that path is INCOMPATIBLE_VERSION, **not a
	 * negotiation to resolve**.
	 *
	 * ⚠ And here `RCP.md` contradicts itself, and it is the second contradiction
	 *   found in this document by a bench (the first was the underscore of §4.3,
	 *   found by the B4 validator).  §9 says: *«the server chooses the highest
	 *   it can speak that does not exceed the one of the HELLO»* — that is 1, and
	 *   an `HERE_I_AM(1)`.  §2.4 says `INCOMPATIBLE_VERSION`.  The two rules give
	 *   **different bytes on the wire for the same input**, and neither of the
	 *   two cites the other.
	 *
	 * ⭐ §2.4 wins, because it is the more specific and because it is the one
	 *    written to resolve precisely this case (finding R1.24).  ⚠ The first
	 *    round of this module had applied §9 to the letter and ACCEPTED a
	 *    HELLO(2): B5 found it.  It is in `PHASES.md` §01-filo-nudo.
	 *
	 * ⚠ And the comparison is with the version of the PATH, which here is the
	 *   only one the server serves.  A server that served `/rcp/1` and `/rcp/2`
	 *   would pass here the version of the path, not a constant. */
	if (version != RCP_VERSION) {
		dismiss(s, RCP_INCOMPATIBLE_VERSION,
		        "the HELLO version is not the one of the path");
		return false;
	}
	uint16_t how_many = le_u16(l);
	/* ⛔⭐ THE MEMORY OF NAMES ALREADY SEEN HAD A BOTTOM, AND BEYOND THE BOTTOM
	 *    «THE LAST ONE WON» — finding R9.6.
	 *
	 *    §4.3: «a name repeated twice is PROTOCOL_ERROR.  "The last one
	 *    wins" and "the first one wins" are two different implementations of
	 *    the same document».  `how_many` is a `u16`: the client can declare up
	 *    to 65 535 capabilities, and here 32 were remembered — with an `if`
	 *    without `else` and without a log line.  A `HELLO` with 32 capabilities
	 *    with a legitimate and unknown name followed by `video.codec=hevc` and
	 *    `video.codec=av1` was not sent away: `snprintf` ran twice and
	 *    **the second won**.  ⚠ The `capacita-ripetuta` case of B5 uses THREE
	 *    capabilities: it stays green forever.
	 *
	 * ⭐ The cure has two halves, because the two cases do not weigh the same:
	 *
	 *    the KNOWN names — the nine of §4.3 — are remembered **all, always**,
	 *    in a bit mask.  They are the ones that change the behaviour, and
	 *    the duplicate that does harm is theirs;
	 *
	 *    the UNKNOWN names are remembered up to `MAX_SEEN`, and beyond that
	 *    number ⛔ **it is written to the log** that from there on the
	 *    repetition of an unknown name is no longer detectable.  §3: «every
	 *    tolerance must be written to the log; a silent tolerance is
	 *    indistinguishable from a defect».
	 *
	 * ⚠ Why one does not simply close when the memory runs out: a `HELLO` with
	 *   four hundred unknown capabilities is CONFORMING (§6.1), and §3 exception 1
	 *   requires ignoring them and carrying on.  Closing would be a red on the
	 *   right code of tomorrow's client — the opposite defect, and it costs more. */
	static const char *const KNOWN_NAMES[] = {
	    "video.codec",   "video.depth", "video.level",
	    "video.max_size", "audio.codec", "input.touch",
	    "clipboard.text", "client.name",
	    /* ⏳ §13, PROPOSED: known on both sides, so a repetition is caught */
	    "video.pace",
#ifdef REMOTIX_BENCH
	    "bench.mark",
#endif
	    NULL};
	char seen_items[MAX_SEEN][65];
	int n_seen = 0;
	uint16_t seen_known = 0;
	bool logged_out_of_memory = false;
	char c_codec[257] = "", c_prof[257] = "", c_audio[257] = "";
	char c_size[257] = "", c_level[257] = "";
	for (uint16_t k = 0; k < how_many; k++) {
		char name[65], value[257];
		size_t ln = le_str(l, name, sizeof name);
		size_t lv = le_str(l, value, sizeof value);
		if (l->too_short) {
			dismiss(s, RCP_PROTOCOL_ERROR, "capability list truncated");
			return false;
		}
		if (!valid_name(name, ln)) {
			dismiss(s, RCP_PROTOCOL_ERROR, "malformed capability name");
			return false;
		}
		if (lv == 0) {
			dismiss(s, RCP_PROTOCOL_ERROR, "capability with an empty value");
			return false;
		}
		/* ⚠ The order of the two terms of the `||` is not indifferent and is not
		 *   to be touched: `lv > 256` FIRST prevents `printable_text` from
		 *   reading beyond the buffer when the string does not fit (see the
		 *   comment of `le_str`, and suspicion R9.18 which stays open). */
		if (lv > 256 || !printable_text(value, lv)) {
			dismiss(s, RCP_PROTOCOL_ERROR, "invalid capability value");
			return false;
		}
		/* ⛔ A repeated name is PROTOCOL_ERROR: «the last one wins» and «the
		 * first one wins» are two implementations of the same document. */
		bool repeated = false;
		int known = -1;
		for (int i = 0; KNOWN_NAMES[i]; i++)
			if (strcmp(KNOWN_NAMES[i], name) == 0) {
				known = i;
				break;
			}
		if (known >= 0) {
			repeated = (seen_known >> known) & 1u;
			seen_known |= (uint16_t)(1u << known);
		} else {
			for (int i = 0; i < n_seen; i++)
				if (strcmp(seen_items[i], name) == 0) {
					repeated = true;
					break;
				}
			if (n_seen < MAX_SEEN) {
				snprintf(seen_items[n_seen++], sizeof seen_items[0], "%s", name);
			} else if (!logged_out_of_memory) {
				logged_out_of_memory = true;
				reg(s, "⚠ more than %d capabilities with an unknown name: from "
				       "here on the REPETITION of an unknown name is no longer "
				       "detectable (§4.3), and the names of §4.3 all remain so",
				    MAX_SEEN);
			}
		}
		if (repeated) {
			dismiss(s, RCP_PROTOCOL_ERROR, "repeated capability");
			return false;
		}
		/* ⛔ A capability from the wrong side is PROTOCOL_ERROR: the name is
		 * known, so the exception for unknown names does not cover it. */
#ifdef REMOTIX_BENCH
		if (strcmp(name, "bench.mark") == 0) {
			dismiss(s, RCP_PROTOCOL_ERROR, "bench.mark does not come from the client");
			return false;
		}
#endif
		if (strcmp(name, "video.codec") == 0)
			snprintf(c_codec, sizeof c_codec, "%s", value);
		else if (strcmp(name, "video.depth") == 0)
			snprintf(c_prof, sizeof c_prof, "%s", value);
		else if (strcmp(name, "audio.codec") == 0)
			snprintf(c_audio, sizeof c_audio, "%s", value);
		else if (strcmp(name, "video.max_size") == 0)
			snprintf(c_size, sizeof c_size, "%s", value);
		/* ⛔⭐ `video.level` — AND UNTIL TODAY THIS LINE WAS NOT THERE.  The
		 *     name was in `KNOWN_NAMES` (that is the server knew it was
		 *     REPEATED), the value went through the loop and nobody kept it:
		 *     the exact same shape as B-1 on `video.max_size`, and with
		 *     the same mute symptom of §4.3 — «the browser does not open the
		 *     stream». */
		else if (strcmp(name, "video.level") == 0)
			snprintf(c_level, sizeof c_level, "%s", value);
		/* ⭐⭐ §7.4 — `clipboard.text`, and until 17 Aug 2026 this value
		 *     was recognised as a legitimate name and then **thrown away**: it
		 *     was exactly the shape of finding B-1 on `video.max_size`.
		 *
		 * ⛔ And it serves two things that cannot be done without it: NOT
		 *    announcing clipboard to a client that did not ask for it, and
		 *    REFUSING bytes on channel `0x02` from a client that did not declare
		 *    it — that is a capability used without negotiating it, which is the
		 *    case §4.3 exists to make impossible.
		 * ⚠ Any value other than `yes` counts as `no`: §4.3 says the values
		 *   of this capability are two, and a third value is a client that
		 *   declares something the document does not define — it is treated as
		 *   the no, and the negotiation line writes it. */
		else if (strcmp(name, "clipboard.text") == 0)
			s->negotiate_clipboard = strcmp(value, "yes") == 0;
		/* ⏳ §13: any value other than `yes` counts as `no`, as for
		 *    `clipboard.text`. */
		else if (strcmp(name, "video.pace") == 0)
			s->pace_client = strcmp(value, "yes") == 0;
	}
	/* ⛔⭐ THE DECODER CEILING IS KEPT — finding B-1, night of 10 Aug
	 *     2026.  §4.5: «the granted canvas MUST respect
	 *     `video.max_size` if the client declared it», and §4.3: «it does
	 *     not change the canvas: it is a ceiling […] because the decoder of a
	 *     phone has limits its screen does not declare».
	 *
	 * ⛔ Before today this value was recognised as a legitimate name and then
	 *    **thrown away**: the server granted exactly what the client
	 *    asked for, even twice what it had declared it could
	 *    decode.  ⚠ And the symptom is not a network error: it is «the browser
	 *    does not open the stream» in phase 2, with the diagnosis aimed at the
	 *    encoder.
	 *
	 * ⛔ And a MALFORMED value is not taken as good and not thrown away in
	 *    silence: §3 exception 1 allows ignoring a value one does not
	 *    understand, and the line below that table requires **writing it to the
	 *    log** — «a silent tolerance is indistinguishable from a
	 *    defect». */
	if (c_size[0]) {
		if (parse_max_size(c_size, &s->max_l, &s->max_a)) {
			reg(s, "the client declares video.max_size=%ux%u: it is the "
			       "ceiling the granted canvas MUST respect (§4.5)",
			    s->max_l, s->max_a);
		} else {
			s->max_l = s->max_a = 0;
			reg(s, "⚠ TOLERANCE (§3 exception 1): video.max_size=«%s» "
			       "does not have the WIDTHxHEIGHT form of §4.3 (whole pixels) — "
			       "the value is ignored, and the canvas will have NO ceiling",
			    c_size);
		}
	}

	/* ⛔⭐⭐ `video.level` — THE SECOND DECODER CEILING, and until
	 *      23 Aug 2026 the server DID NOT READ IT.
	 *
	 * `RCP.md` §4.3, row 701 of the capability table: *«the maximum level it
	 * can decode, e.g. `5.1`.  ⛔ The server **MUST** emit a stream of a level
	 * not higher, and **does not guess it**: a level declared too low does not
	 * give a network error, **it makes the decoder refuse the configuration**
	 * and the symptom is "the browser does not open the stream" (finding O12)»*.
	 *
	 * ⛔ AND IT IS PRECISELY BECAUSE THE SYMPTOM IS MUTE THAT THE NUMBER IS
	 *    WRITTEN.  A wrong level produces a red nowhere: it produces a black
	 *    screen, and a hunt that starts from the encoder or from the network —
	 *    that is from the wrong side.  These lines are the only place where
	 *    the REQUESTED number appears, and without them there is nothing to
	 *    compare with the one produced.
	 *
	 * ⛔⚠ AND THE COMPARISON IS NOT MADE HERE, but since tonight IT IS MADE — in
	 *     the child.  This module does not see a byte of stream:
	 *     `rcp_video_send()` receives opaque data, and §4.3 is the only
	 *     document rcp.c knows (see the box of `rcp.h`).  ⇒ Here the requested
	 *     number is read and HANDED OVER (`rcp_level_negotiated()`); the
	 *     produced level is read from the SPS (`encoder.c`,
	 *     `read_h264_sps`/`read_hevc_sps`) and the comparison is made by
	 *     whoever has both numbers in hand, that is the child.
	 *     ⛔ Until 23 Aug 2026 the chain was not there, and the defect was
	 *       MEASURED: `video.level=5.1` requested, **5.2** produced at
	 *       3840x2160.  The chain is `rcp.h` → `webtransport.c` (the hook
	 *       `wt_video_request`) → `main.c` → `child.h` (`children_video`) →
	 *       `child.c` (`struct body_video`, which kept its `fill` byte
	 *       free on purpose).  It is the same chain the negotiated DEPTH
	 *       travelled on 17 Aug 2026 — and that day the defect was
	 *       identical: two true numbers in two processes, and nobody putting
	 *       them side by side.
	 *
	 * ⛔ A MALFORMED value is not taken as good and not thrown away in
	 *    silence, as for `video.max_size`: §3 exception 1 allows
	 *    ignoring it, and the line below that table requires writing it. */
	if (c_level[0]) {
		if (parse_level(c_level, &s->livello_x10)) {
			reg(s, "the client declares video.level=%s (= %u.%u, that is "
			       "level_idc %u in H.264 and L%u in HEVC): §4.3 forbids the "
			       "server to emit a stream HIGHER than this",
			    c_level, s->livello_x10 / 10u, s->livello_x10 % 10u,
			    s->livello_x10, s->livello_x10 * 3u);
			reg(s, "⭐ and since tonight this number CROSSES the process "
			       "boundary: `rcp_level_negotiated()` → `webtransport` → "
			       "`main` → `children_video()` → the child, which IMPOSES it on "
			       "the encoder and then reads it back from the SPS (R31).  ⚠ The "
			       "verdict is in the child's «§4.3 — LIVELLO» line, not "
			       "here: here there is only the requested number");
		} else {
			s->livello_x10 = 0;
			reg(s, "⚠ TOLERANCE (§3 exception 1): video.level=«%s» does not "
			       "have the MAJOR.MINOR form of §4.3 (e.g. «5.1») — the value is "
			       "ignored, and §4.3 will have no level to enforce",
			    c_level);
		}
	} else {
		/* ⚠ §4.3 does not OBLIGE the client to declare it, and the absence is
		 *   written all the same: «not declared» and «declared and thrown away»
		 *   look the same in yesterday's log, and they are two different things. */
		reg(s, "the client does NOT declare video.level: §4.3 does not "
		       "require it, and the server does not guess one — no level ceiling");
	}

	/* ⛔ §4.3: `pcm` and `8` MUST be declared by BOTH — `pcm` is the
	 * base always available, and it serves as a positive control when Opus is
	 * not negotiated.  ⚠ And whoever does not declare them is sent away with
	 * NOTHING_IN_COMMON, **not** with PROTOCOL_ERROR: it did not write
	 * wrongly, it has nothing to talk about.  Without this check the
	 * intersection is enough on its own — a client that offers only `opus`
	 * passes — and nobody applies the line of §4.3. */
	if (!entry_present(c_audio, "pcm")) {
		dismiss(s, RCP_NOTHING_IN_COMMON,
		        "the client does not declare pcm in audio.codec");
		return false;
	}
	if (!entry_present(c_prof, "8")) {
		dismiss(s, RCP_NOTHING_IN_COMMON,
		        "the client does not declare 8 in video.depth");
		return false;
	}
	/* ⛔ If the intersection is empty the client is sent away with
	 * NOTHING_IN_COMMON, not with PROTOCOL_ERROR: it did not write wrongly,
	 * it has nothing to talk about. */
	char sc_codec[257], sc_prof[257], sc_audio[257];
	int n_codec = 0, n_prof = 0, n_audio = 0;
	if (!our_codec[0]) {
		/* ⛔ Phase 18-19: the server cannot encode anything, and says so with
		 *    the name of the cause — the startup log carries the reason. */
		dismiss(s, RCP_NOTHING_IN_COMMON,
		        "this server cannot encode video: no capable card, "
		        "no codec in HERE_I_AM (REMOTIX encodes only on the card — "
		        "see the startup log)");
		return false;
	}
	if (!first_in_common(c_codec, our_codec, s->codec, sizeof s->codec,
	                  sc_codec, sizeof sc_codec, &n_codec) ||
	    !first_in_common(c_prof, OUR_DEPTH, s->depth,
	                  sizeof s->depth, sc_prof, sizeof sc_prof, &n_prof) ||
	    !first_in_common(c_audio, OUR_AUDIO, s->audio, sizeof s->audio,
	                  sc_audio, sizeof sc_audio, &n_audio)) {
		dismiss(s, RCP_NOTHING_IN_COMMON, "no shared codec");
		return false;
	}
	/* ⛔ The choice is WRITTEN: a successful negotiation with the opposite
	 * of what was wanted inside it is seen only if someone writes it. */
	reg(s, "negoziato video.codec=%s video.depth=%s audio.codec=%s",
	    s->codec, s->depth, s->audio);
	/* ⛔ And the DISCARD is written in turn: «I chose hevc» does not say that
	 * vp9 was thrown away, and the day tomorrow's client offers a codec this
	 * server does not know, the log is the only place where that fact
	 * appears. */
	/* ⚠ And HOW MANY there are is written too, not only which: the list can be
	 *   truncated by the buffer, the number cannot (finding R9.12). */
	if (n_codec || n_prof || n_audio)
		reg(s, "discarded unknown entries: video.codec=[%s] (%d) "
		       "video.depth=[%s] (%d) audio.codec=[%s] (%d)",
		    sc_codec, n_codec, sc_prof, n_prof, sc_audio, n_audio);
	send_here_i_am(s);
	s->state = S_WAIT_CREDENTIALS;
	return true;
}

static bool handle_credentials(rcp_session *s, reader *l, uint64_t now)
{
	char user[257], password[1025];
	size_t lu = le_str(l, user, sizeof user);
	size_t lp = le_str(l, password, sizeof password);
	/* ⛔ THE LOCAL COPY IS ZEROED ON EVERY ROAD, NOT ONLY ON THE GOOD ONE —
	 * finding R9.8.  The zeroing sat at the bottom, after the PAM answer: on
	 * every error path that sends the client away below — user not UTF-8, user
	 * or password out of range — the password stayed on the stack.  The
	 * `utente-vuoto` case of B5 is exactly this: a 1024-byte password, a user
	 * of zero, and one leaves from here.  ⚠ The three repeated lines are
	 * deliberate: a common exit `goto` reads worse than three lines that say
	 * the same thing where one happens to look. */
	if (l->too_short) {
		explicit_bzero(password, sizeof password);
		dismiss(s, RCP_PROTOCOL_ERROR, "CREDENTIALS truncated");
		return false;
	}
	/* §4.4: the ranges.  An empty string is legal by §6.0, and without
	 * these limits a `CREDENTIALS` with two zero-byte strings would be
	 * conforming — and an attacker would increment no counter. */
	if (lu < 1 || lu > 256 || lp < 1 || lp > 1024) {
		explicit_bzero(password, sizeof password);
		dismiss(s, RCP_PROTOCOL_ERROR, "user or password out of range");
		return false;
	}
	/* ⛔ §4.3 applies to capabilities, but the reason for `printable_text`
	 * applies here more than anywhere (finding R9.11): a nine-byte `root\0nemo`
	 * passed the ranges, passed `valid_utf8`, and sent `root` to PAM.
	 * What arrived and what is judged must be the same string, or the log and
	 * the key of §4.4-bis name a user that was not on the wire. */
	if (!printable_text(user, lu)) {
		explicit_bzero(password, sizeof password);
		dismiss(s, RCP_PROTOCOL_ERROR,
		        "the user is not printable UTF-8 text");
		return false;
	}
	/* ⚠ Of the password ONLY the NUL byte is checked, and the reason is the
	 *   same: with a zero in the middle PAM would judge a prefix of what
	 *   arrived.  ⛔ It is not required to be printable: §4.4 does not ask it,
	 *   and a password can contain whatever it wants. */
	if (strlen(password) != lp) {
		explicit_bzero(password, sizeof password);
		dismiss(s, RCP_PROTOCOL_ERROR,
		        "the password contains a null byte: what arrives and what "
		        "would be judged would be two different things");
		return false;
	}
	snprintf(s->user, sizeof s->user, "%s", user);
	/* ⛔ Three lines of instrumentation, and they are not incidental: on 10 Aug
	 * 2026 the handshake stopped here and «CREDENTIALS did not arrive»
	 * and «PAM does not answer» looked the same — that is like nothing.
	 * ⚠ The password does NOT appear, at any level (§4.4) — and since today
	 *   neither does its EXACT LENGTH, which was here: §11.1 treats the log as a
	 *   file that is kept, and the length of every password tried,
	 *   successful or not, is not something to keep (finding R9.8).  To tell
	 *   «it did not arrive» from «PAM does not answer» this line is
	 *   enough. */
	char tag[96];

	/* ⛔ The limiter BEFORE PAM, and the refusal is immediate: §4.4-bis says
	 * the wait is a WINDOW in which one refuses, not a delay — with a single
	 * attempt per connection, a server that delayed by fifteen minutes
	 * would never deliver the refusal. */
	/* ⛔⭐ AND FROM HERE DOWN ONE STARTS FROM DENIED, ALWAYS — invariant I3.
	 *
	 * Before 12 Aug 2026 `cred_good` took its value inside the only `else`
	 * below, and there was no other road: PAM had already answered when this
	 * function returned.  ⚠ Now the roads are four — banned, helper that does
	 * not take the question, synchronous fallback check, and the good road
	 * that WAITS — and three of them leave here without any verdict in hand.
	 * A field left at its previous value on one of those roads would be a
	 * «yes» arrived by inertia. */
	s->cred_good = false;
	s->cred_reason = RCP_WRONG_CREDENTIALS;
	s->expected_verdict = false;
	s->refusal_is_ours = false;
	struct login_info linfo;
	enum login_verdict lv = login_reserve(s->address, s->user, now, &linfo);
	/* ⛔ The name is looked up in the system (`getpwnam_r`, for the tag of the
	 *    log) only if the limiter let the attempt through: a refused flood
	 *    must not cost an NSS lookup per attempt.  The refused ones are logged
	 *    with the tag only, `user [hmac6]`. */
	s->user_lookup_ok = lv == LV_OK;
	reg(s, "CREDENTIALS received user=%s (with password)",
	    log_user(s->user, tag, sizeof tag, s->user_lookup_ok));
	if (linfo.evicted[0])
		reg(s, "⚠ attempt table full (%d entries): evicted the entry «%s» to "
		       "make room — §4.4-bis",
		    MAX_ATTEMPTS, linfo.evicted);
	if (lv != LV_OK) {
		/* ⛔ The limiter refuses WITHOUT querying PAM, and it must be known from
		 * reading the reason on the wire: `TOO_MANY_ATTEMPTS` and
		 * `WRONG_CREDENTIALS` cannot come from the same road.  ⭐ It is the
		 * byte that on 10 Aug 2026 separated the two suspects of B8 — whoever
		 * reads a `WRONG_CREDENTIALS` is looking at PAM, not at this line.
		 * ⚠ Nothing is booked and nothing is counted: a refusal is not a
		 * failed attempt (no ban is born from refusals). */
		s->cred_good = false;
		s->cred_reason = RCP_TOO_MANY_ATTEMPTS;
		if (lv == LV_BANNED)
			reg(s, "⛔ %s of %s BANNED: %llu minutes remain, PAM is not "
			       "queried (§4.4-bis)",
			    LEVEL_NAME[linfo.kind], s->address,
			    (unsigned long long)((linfo.remain + 59999u) / 60000u));
		else if (lv == LV_BUSY)
			reg(s, "⛔ too many attempts in flight or just failed for the %s "
			       "of %s: PAM is not queried, and the refusal is NOT a failed "
			       "attempt (§4.4-bis B)",
			    LEVEL_NAME[linfo.kind], s->address);
		else
			reg(s, "⛔ attempt table full and nothing in it can be freed "
			       "(banned or in flight): refused, PAM is not queried.  "
			       "Refusals for this reason so far: %u (§4.4-bis)",
			    login_refused_full);
	} else if (s->g.ask_verify) {
		/* ⭐⭐ THE GOOD ROAD — `DECISIONS.md` §1.10, 12 Aug 2026.
		 *
		 * ⛔ Here one does NOT wait for PAM.  One asks a helper process and
		 *    returns at once to the host, which returns to its `poll`: it is the
		 *    only way in which «while one authenticates, the others do not
		 *    notice» can be true on a single-threaded server.
		 *
		 * ⚠ And the FAILURE of §4.4-bis is not counted here: now one knows that
		 *   one asked, not what was answered.  What happened here is the
		 *   BOOKING (`login_reserve()`, above): the attempt counts as «in
		 *   flight» for the three levels until the verdict, which turns it into
		 *   a failure or gives it back — `rcp_verdict()`, or
		 *   `rcp_orphan_verdict()` if the connection is gone by then. */
		/* ⭐ A key that logged in lately may take the two PAM slots kept for it
		 *    (`rcp_asking_for_known_key()`, §11.39 addendum). */
		asking_for_known_key = good_recent(s->address, now);
		bool asked = s->g.ask_verify(s->g.ctx, user, password, &s->ticket);
		asking_for_known_key = false;
		if (asked) {
			s->expected_verdict = true;
			reg(s, "PAM asked of the helper, request %llu: the thread stays "
			       "free (DECISIONS.md §1.10)",
			    (unsigned long long)s->ticket);
		} else {
			/* ⛔ THE QUESTION DID NOT LEAVE ⇒ NO, at once.  It is I3 to the
			 *    letter: «design so that failure is a no, not a maybe».
			 * ⚠ And it does not count as a failed attempt: the defect is OURS,
			 *   and §4.4-bis lists among the things that do not ban precisely
			 *   those that «would ban someone who did nothing wrong». */
			s->refusal_is_ours = true;
			login_release(s->address, s->user);
			reg(s, "⛔ the question to PAM did not leave: REJECTED without appeal "
			       "(invariant I3).  ⚠ And it does NOT count as a failed attempt "
			       "of §4.4-bis: the defect is ours, and a ban for a defect of "
			       "ours would be the worst possible diagnosis.  The booking is "
			       "given back");
		}
	} else {
		/* ⛔⭐ NO SYNCHRONOUS FALLBACK ANY MORE — D4b of `DECISIONS.md` §11.50,
		 *     a DELIBERATE change of behaviour.  Until D4b a host without the
		 *     asynchronous hook (the helper not started) had PAM called
		 *     right here, which stops the server's only loop for 1-2 s at every
		 *     attempt.  Now: no helper hook ⇒ the check is NOT made, the login
		 *     is REFUSED as ours (`0x0E`, not `0x07`), nothing is counted and
		 *     the booking is given back — the same road as a question that
		 *     did not leave, which is exactly what this is. */
		s->refusal_is_ours = true;
		login_release(s->address, s->user);
		reg(s, "⛔ no helper: the check was NOT made, REJECTED as ours "
		       "(invariant I3), NOT counted as a failed attempt of §4.4-bis; "
		       "the booking is given back");
	}
	/* ⛔ The password is zeroed as soon as PAM has answered, and does not appear
	 * in any log at any level (§4.4).
	 * ⚠ This zeroes the local COPY.  The original arrived inside `s->acc`
	 *   and stays there until the message is consumed: the tail of the
	 *   buffer is zeroed in `drain()`, and whatever is left over in
	 *   `rcp_free()`.  Both were uncovered (finding R9.8).
	 * ⭐ It is `explicit_bzero()` and not `memset`: an optimising compiler is
	 *   ALLOWED to remove a `memset` of a buffer that is no longer read
	 *   (suspicion R9.20, cured by DECISIONS §11.6). */
	explicit_bzero(password, sizeof password);

	s->cred_arrival = now;
	s->state = S_WAIT_VERDICT;
	s->since = now;
	return true;
}

/* ⛔⛔⭐ THE ALPHABET OF THE NAME — 21 Aug 2026, bench `06-b34` case 8, and
 *      ⚠ IT IS THE D1 SHAPE THAT SURVIVED ITS OWN CURE.
 *
 *      On 16 August the fixed list of 20 layouts was removed and the
 *      question «does this machine have it?» went to XKB (the hook
 *      `layout_exists`, `webtransport.c:1626` → `keyboard.c`).  ⛔ But
 *      IN FRONT OF that hook a SECOND hand-written list had remained, and
 *      nobody had looked at it: **which characters are allowed in the name**.
 *
 * `[M]` Measured by asking the system through the product itself
 *   (`06-b34-table.c list`, that is `src/keyboard.c`), on all the **590**
 *   layout/variant pairs that `/usr/share/X11/xkb/rules/evdev.lst`
 *   declares on the test machine: **589 compile**, that is the machine
 *   has them.  ⛔ And **9 of those 589 have an uppercase letter in the name**:
 *
 *     de(T3)   ie(CloGaelach)   ie(UnicodeExpert)   in(tamilnet_TAB)
 *     in(tamilnet_TSCII)   jp(OADG109A)   lk(tam_TAB)
 *     ru(phonetic_YAZHERTY)   ua(macOS)
 *
 *   `[M]` On the wire, before this cure: `de(T3)`, `jp(OADG109A)` and
 *   `ua(macOS)` received **`0x0b PROTOCOL_ERROR`** — which is WORSE than
 *   `SESSION_UNSERVABLE`, because it says «your client is broken» and sends
 *   people looking for the fault on the other side of the wire.
 *
 * ⛔ And the other direction, also measured: `it()` — EMPTY variant — was well
 *    formed for this function and malformed for `keyboard.c:valid_shape`,
 *    ⇒ `0x0e` went out on a **malformed** string.  §4.5 wants the two faults
 *    DISTINCT, and there they were merged.
 *
 * ⇒ ⭐ THE CURE IS THAT THE FORM BE ONE ONLY: here the same alphabet as
 *   `keyboard.c:allowed_char()` is used — `[A-Za-z0-9_-]` — and the same
 *   rule on the empty variant.  ⛔ Two form checks written twice give
 *   two answers under the same label, which is the **E2** error shape.
 *
 * ⚠ And the defence this function carries is NOT loosened: the dot, the slash
 *   and the comma stay out of the alphabet, so `../../etc/passwd` and `it,`
 *   are refused as before — and it is the only thing this function
 *   protects, because the string ends up inside the XKB `include`
 *   machinery, which opens files by name (`keyboard.c:172`).
 *
 * ⚠ The declared price: `IT` passes the form and goes to the hook, which
 *   answers «I do not have it» ⇒ `0x0e` instead of `0x0b`.  XKB distinguishes
 *   case and `symbols/IT` does not exist: «well formed, unknown» IS the right
 *   answer.
 */
static bool layout_char_allowed(char c)
{
	return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
	       (c >= '0' && c <= '9') || c == '_' || c == '-';
}

static bool layout_well_formed(const char *d, size_t n)
{
	/* §4.5: an XKB name, possibly with the variant in parentheses. */
	if (n < 1 || n > 64)
		return false;
	size_t i = 0;
	while (i < n && layout_char_allowed(d[i]))
		i++;
	if (i == 0)
		return false;
	if (i == n)
		return true;
	/* ⛔ `n < i + 3` = the variant is EMPTY (`it()`): malformed, not unknown. */
	if (d[i] != '(' || d[n - 1] != ')' || n < i + 3)
		return false;
	for (size_t k = i + 1; k + 1 < n; k++)
		if (!layout_char_allowed(d[k]))
			return false;
	return true;
}

/* ⛔ §4.5 distinguishes TWO faults, and wants two different reasons:
 *
 *   malformed              PROTOCOL_ERROR     — it wrote wrongly
 *   well formed, unknown   SESSION_UNSERVABLE — it wrote correctly something
 *                                                   this machine does not have
 *
 * ⚠ A server that merged them would give `PROTOCOL_ERROR` to whoever has a
 *   Swedish keyboard on a machine without the Swedish XKB package, and the
 *   symptom would be «the client is broken» instead of «the machine lacks a
 *   layout».
 *
 * `[?]` ⚠ **And the list below is from phase 1, and it must be declared.**
 *   «What the system knows» is known by the system, not by RCP: a real server
 *   asks XKB.  In phase 1 there is no compositor (`SESSION` declares
 *   `desktop=unknown`), so there is nobody to ask, and the choice is a
 *   fixed list.  ⛔ What the bench tests is **that the two faults are
 *   distinct**, not which layouts exist: the day the question goes to XKB,
 *   this function changes and B5 stays as it is. */
static bool layout_in_list(const char *d)
{
	static const char *NOTE[] = {"it", "us", "gb", "de", "fr", "es", "pt",
	                             "ru", "se", "no", "dk", "fi", "pl", "cz",
	                             "ch", "at", "be", "nl", "br", "jp", NULL};
	/* The variant in parentheses does not change the layout: `de(neo)` is `de`
	 * with another map, and whoever has `de` has both. */
	size_t n = 0;
	while (d[n] && d[n] != '(')
		n++;
	for (int i = 0; NOTE[i]; i++)
		if (strlen(NOTE[i]) == n && strncmp(NOTE[i], d, n) == 0)
			return true;
	return false;
}

/* ⛔⛔⭐ AND NOW THE QUESTION GOES TO XKB — 16 Aug 2026, bench `06-b34` case 5.
 *
 *      The list above was from phase 1, and its own note said that «a real
 *      server asks XKB».  ⛔ `[M]` as long as it decided:
 *      **`hu`, `tr`, `gr` and `ua` exist in `/usr/share/X11/xkb/symbols/` on
 *      this machine and were refused** with `SESSION_UNSERVABLE`.
 *      ⇒ A Hungarian user was denied the session by a hand-written list, and
 *        the log told them «layout unknown to this machine» — a
 *        FALSE sentence, which is the worst way of being wrong.
 *
 *      ⚠ And as long as the declared layout touched nothing the defect was
 *        invisible: it just refused.  With §5-bis.7 carried out, it becomes the
 *        difference between «the Hungarian works» and «the Hungarian does not
 *        get in».
 *
 * ⛔ THE THREE OUTCOMES STAY THREE, and the third is the one that costs: if the
 *    hook is not there (the twin of `benches/rcp/`, the bare-QUIC harnesses)
 *    **it could not be asked**, and «I did not look» is not «it does not exist»
 *    (`LESSONS.md` §1.9 rule 1).  ⇒ There one falls back on the phase 1 list
 *    **declaring it**, instead of accepting everything or refusing everything
 *    in silence.
 *
 *   `1` known · `0` no · `-1` could not be asked (already declared) */
static int layout_known(rcp_session *s, const char *d)
{
	if (s->g.layout_exists) {
		int r = s->g.layout_exists(s->g.ctx, d);
		if (r >= 0)
			return r;
		reg(s, "⚠ DECLARED FALLBACK (§4.5): the «layout_exists» hook "
		       "could not answer for «%s» — falling back on the phase 1 "
		       "list, which is NOT what this machine really has",
		    d);
	} else {
		reg(s, "⚠ DECLARED FALLBACK (§4.5): no «layout_exists» hook "
		       "on this server — the question «does %s exist?» did NOT go to XKB, "
		       "and the answer comes from the fixed phase 1 list",
		    d);
	}
	return layout_in_list(d) ? 1 : 0;
}

/* ⛔⭐ THE STAGE IS ASKED TO SET THE LAYOUT, AND THE OUTCOME IS DECLARED.
 *
 * `why` says where the request comes from — «the attach» or «LAYOUT
 * (0x0009)» — and ends up in the log: six hours later, whoever reads must be
 * able to tell a layout set on reattach from one changed by hand by the user,
 * because the two faults that follow them are different.
 *
 * ⛔ The fallback is DECLARED (`CODER.md` §4.2): without the hook the layout
 *    is NOT applied, and keeping quiet would mean leaving the user with
 *    `Ctrl+Z` on the wrong key and no line explaining it.
 *
 * ⚠ `true` = the request has LEFT, not «is in force»: who knows that is the
 *   child, and it is the child that writes the line with the name of the keymap
 *   `libei` really hands it.  Same rule as the release on detach — a number (or
 *   an outcome) invented here would be worse than none. */
static void apply_layout(rcp_session *s, const char *why)
{
	if (!s->layout[0])
		return;
	if (!s->g.layout) {
		reg(s, "⚠ DECLARED FALLBACK (§5-bis.7): %s declared the "
		       "layout «%s», but this server does NOT have the hook to "
		       "apply it — the session keeps the one it has.  ⛔ The LETTERS "
		       "will come out right all the same (they are translated on the "
		       "session's keymap), but the SHORTCUTS will not: `Ctrl+Z` will land "
		       "on the key that position has in the OTHER layout (§7.3)",
		    why, s->layout);
		return;
	}
	if (s->g.layout(s->g.ctx, s->layout))
		reg(s, "⭐ §5-bis.7: %s declared «%s» — request SENT to the "
		       "stage.  ⚠ This line does NOT say it is in force: who knows that is "
		       "the child, and it writes it with the name `libei` hands it",
		    why, s->layout);
	else
		reg(s, "⛔ §5-bis.7: %s declared «%s» and the request did NOT "
		       "leave: the session keeps the layout it has, and the "
		       "shortcuts will stay out of step",
		    why, s->layout);
}

/* ⛔⭐⭐ THE GHOST EVICTION — the rule is in the box above
 *      `DEFAULT_EVICTION`, here is the how.
 *
 * Returns `true` if the slot has been freed (and then whoever arrives can
 * ask for it again), `false` if the occupant stays where it is.  ⚠ `*mute`
 * ALWAYS comes out set with the occupant's milliseconds of silence — it serves
 * the log line and the sentence, even when eviction is off.
 *
 * ⛔⛔ THE CHECK THAT CANNOT BE REMOVED IS THE USER ONE.  The rule
 *      applies **only between clients of the same user**: evicting the client
 *      of another user would not be a convenience, it would be a security hole —
 *      anyone could bring down someone else's desktop simply by
 *      knocking.  ⚠ Today the registry of slots is indexed BY NAME, so
 *      `SLOT_OCCUPIED` already implies «same user»; the check below is
 *      redundant **by construction, not by design**, and the day the
 *      registry became the session table of a real server
 *      (the session cap, §4.6) it would be the only thing holding.  It is
 *      not removed.
 *
 * ⛔ And the occupant is NOT sent away: it is put exactly in the state in
 *    which the silence of §5.3 puts it in `rcp_time()` — slot left,
 *    `S_DETACHED`, and whatever was pressed released (§7.3).  ⭐ From there
 *    `speak_again()` already knows what to do with it should the wire come
 *    back to life: the slot is no longer its own, and it gets `0x0F` with the
 *    sentence «the slot of this session was taken by another client
 *    while this one was silent» — which in that case is TRUE.  ⚠ Verified by reading
 *    it, not taken for granted: that function restarts **only** from
 *    `S_DETACHED`, and that is why the state is changed here and one does not
 *    just remove the slot (finding R9.2). */
static bool evict_ghost(rcp_session *arrival, uint64_t now,
                                uint64_t *mute)
{
	rcp_session *o = slot_holder(arrival->user);

	*mute = 0;
	/* ⚠ A slot taken without an owner should not exist; if it did,
	 *   it is not the case to evict in the dark — one denies, and the log will
	 *   say the occupant's silence was zero. */
	if (!o || o == arrival)
		return false;
	*mute = now > o->last_life ? now - o->last_life : 0;
	if (!eviction_ms)
		return false;
	/* ⛔ The user check — see the box above. */
	if (strcmp(o->user, arrival->user) != 0) {
		reg(arrival, "⛔ EVICTION DENIED: the slot belongs to «%s» and the one "
		            "asking is «%s» — between different users there is NEVER an "
		            "eviction, and this registry should not even be able to "
		            "propose it",
		    o->user, arrival->user);
		return false;
	}
	/* ⚠ Only an ACTIVE occupant holding the slot is evicted: anyone
	 *   else is not the case this rule describes. */
	if (o->state != S_ACTIVE || !o->is_attached)
		return false;
	if (*mute <= eviction_ms)
		return false;

	reg(o, "⭐ EVICTION for silence: %llu ms without a PACKET from %s (threshold "
	       "%llu ms) — the slot of %s goes to the client arriving from %s "
	       "(§4.4: whoever is silent is detached; §8.2 is NOT violated, this "
	       "occupant was attached but not alive) (slots taken now: %d)",
	    (unsigned long long)*mute, o->provenance,
	    (unsigned long long)eviction_ms, o->user, arrival->provenance,
	    taken_slots() - 1);
	slot_leave(o->user);
	o->is_attached = false;
	o->state = S_DETACHED;
	/* ⛔ §7.3: on detach everything is released.  A Ctrl left down in the
	 * ghost would make the desktop unusable for whoever gets in now — and it
	 * is precisely whoever gets in now who must find it clean. */
	release_on_detach(o, "eviction for silence");
	return true;
}

/* ⚠ `now` serves the ghost eviction, which compares the occupant's
 *   `last_life` with now.  It comes from `drain()`, as for
 *   `handle_credentials()`: it is the instant of the packet carrying the `ATTACH`. */
static bool handle_attach(rcp_session *s, reader *l, uint64_t now)
{
	uint32_t tl = le_u32(l), ta = le_u32(l);
	/* ⛔ §7.1: the view does NOT have the constraints of the canvas — «any size
	 * from 1x1 up is legal, odd included» (finding R1.17).  Here NOTHING is
	 * checked, and it is deliberate.
	 *
	 * ⚠ Whoever writes `ATTACH` in C writes ONE `valida_misura()` and calls it
	 *   four times: it is the natural thing to do, and it produces a server that
	 *   **closes the session because the user narrowed the window**.  On a
	 *   phone at factor 2.75 the view is odd almost always — 393 logical
	 *   pixels are 1080.75 physical (finding R4.10).  B5 tests it with
	 *   `300x801` and `1x1`, which MUST pass. */
	uint32_t vl = le_u32(l), va = le_u32(l);
	char avail[65];
	/* ⛔ …NOTHING except one thing, and it is the only one §7.1 demands: **from
	 *    1x1 up**.  A zero is not a small view, it is the absence of a view, and
	 *    §6.0 forbids implicit sentinel values — a client that sends 0 has a
	 *    defect, and letting it pass would hide it together with the log line
	 *    that would say so.  The real check is further below, after
	 *    truncation has been ruled out. */
	size_t ld = le_str(l, avail, sizeof avail);
	if (l->too_short) {
		dismiss(s, RCP_PROTOCOL_ERROR, "ATTACH truncated");
		return false;
	}
	/* ⛔⭐ ABOVE THE MAXIMUM IT IS REDUCED, THE CLIENT IS NOT SENT AWAY — 1 Oct
	 *     2026, canvas at most 4096x2304 (the user's decision, box in `rcp.h`).
	 *     Until that day a canvas beyond 7680x4320 was `PROTOCOL_ERROR`.
	 *
	 * ⚠ A browser on a 5K or ultrawide monitor asks for its window, and it
	 *   did nothing wrong: §4.5 already allows a granted canvas different from
	 *   the one requested.  ⇒ The side that overflows goes to the maximum and
	 *   the other stays — the rule of `rcp_size_allowed()` and of
	 *   `canvas_to_request()` in the page, so `ATTACH` and `FIT_CANVAS` grant
	 *   the same number.
	 * ⛔ It is done BEFORE the parity check: the maximum is even, and a
	 *    5121 that becomes 4096 is no longer an odd number to refuse. */
	if (tl > RCP_CANVAS_MAX_W || ta > RCP_CANVAS_MAX_H) {
		uint32_t requested_w = tl, requested_h = ta;
		if (tl > RCP_CANVAS_MAX_W)
			tl = RCP_CANVAS_MAX_W;
		if (ta > RCP_CANVAS_MAX_H)
			ta = RCP_CANVAS_MAX_H;
		reg(s, "⚠ DECLARED FALLBACK (§4.5): ATTACH asks for the canvas %ux%u, "
		       "beyond the maximum %ux%u — I reduce it to %ux%u (the side that "
		       "overflows to the maximum, the other as it is)",
		    requested_w, requested_h, RCP_CANVAS_MAX_W, RCP_CANVAS_MAX_H, tl,
		    ta);
	}
	/* ⛔ The minimum and parity stay normative: an odd size is rounded by the
	 * encoder, in silence — two different sizes under the same label, which is
	 * the E2 shape. */
	if (tl < RCP_CANVAS_MIN_W || ta < RCP_CANVAS_MIN_H || (tl % 2) || (ta % 2)) {
		dismiss(s, RCP_PROTOCOL_ERROR, "canvas below the minimum or odd");
		return false;
	}
	/* ⛔ And the ONLY limit of the view, §7.1: «any size **from 1x1 up**».
	 *    ⚠ Above it says nothing is checked here, and this line does not
	 *    contradict it: «from 1x1 up» is the range the arbiter DECLARES, and a
	 *    zero lies outside it just as 100000 lies outside the canvas.  Whoever
	 *    let it pass would have a `u32` field with a value that means nothing,
	 *    and the defect would show further on — when someone divided by it. */
	if (!vl || !va) {
		dismiss(s, RCP_PROTOCOL_ERROR,
		        "view with a zero side: §7.1 admits any size from "
		        "1x1 up, and zero is not a size");
		return false;
	}
	if (!layout_well_formed(avail, ld)) {
		dismiss(s, RCP_PROTOCOL_ERROR, "malformed layout");
		return false;
	}
	if (!layout_known(s, avail)) {
		/* ⛔ §8.2: SESSION_UNSERVABLE «MUST carry the detail in the
		 * body», and `dismiss()` puts it there.  The detail is NOT shown to the
		 * user (§8.2): the client builds the sentence from the code. */
		char d[128];
		snprintf(d, sizeof d, "layout unknown to this machine: %s",
		         avail);
		dismiss(s, RCP_SESSION_UNSERVABLE, d);
		return false;
	}
	/* ⛔ And it is kept: it is needed further below, when the session is open
	 *    and it can finally be APPLIED (§5-bis.7).  ⚠ Not before `SESSION`: if
	 *    the attach is refused (slot taken, local session) we would have
	 *    changed the layout for a user who did not get in. */
	snprintf(s->layout, sizeof s->layout, "%s", avail);

	/* ⛔⭐ §5.1 of `SPECS.md`, reason `0x05 ALREADY_ACTIVE_LOCALLY` — and it comes
	 *     BEFORE the slot, on purpose.
	 *
	 * ⛔ Asking for the slot and then releasing it would have the same outcome
	 *    for this client and a DIFFERENT one for the registry: for an instant the
	 *    slot would appear taken by whoever is about to be refused, and another
	 *    client of the same user arriving at that instant would read
	 *    `0x0F` — «you already have an attached session» — which is false.
	 *
	 * ⚠ And the hook is optional: if it is not there, the rule is NOT applied,
	 *   and the log line says so.  «No local session» and «nobody
	 *   looked» are two different facts (`LESSONS.md` §1.9 rule 1). */
	if (s->g.session_local) {
		char which[160];

		which[0] = '\0';
		if (s->g.session_local(s->g.ctx, s->user, which, sizeof which)) {
			reg(s, "⛔ attach DENIED to %s from %s: they already have a LOCAL "
			       "graphical session (%s) — §5.1, reason 0x05",
			    s->user, s->provenance,
			    which[0] ? which : "without detail");
			/* ⛔ The detail in the body does NOT name the other session:
			 * §8.2 says what the client may know. */
			dismiss(s, RCP_ALREADY_ACTIVE_LOCALLY,
			        "this user already has a local graphical "
			        "session");
			return false;
		}
	} else {
		reg(s, "⚠ no «session_local» hook: the rule of §5.1 (reason "
		       "0x05) is NOT applied on this server");
	}

	/* ⛔ §8.2 reason 0x0F: the one refused is whoever ARRIVES, not whoever was there. */
	/* ⛔ The slot is ASKED for, and the outcome is written with how many were taken.
	 * ⚠ On 10 Aug 2026 the third round of B3 could not tell «the
	 *   server does not look at the registry» from «the slot had already been
	 *   freed»: they are two opposite defects, and without this line they give
	 *   the same red. */
	/* ⛔ And the two ways of not having a slot do NOT have the same reason — see
	 * the box above `slot_take()`, finding R9.3. */
	switch (slot_take(s)) {
	case SLOT_TAKEN:
		break;
	case SLOT_OCCUPIED: {
		/* ⭐ BEFORE DENYING ONE LOOKS WHETHER THE OCCUPANT IS ALIVE — 23 Aug
		 *    2026, the ghost eviction (the box above `DEFAULT_EVICTION`).
		 * ⚠ `mute` is ALWAYS computed, even with eviction off: it is the number
		 *   that whoever reads the log was missing to know whether that slot
		 *   belonged to an alive client or to a corpse. */
		uint64_t mute = 0;
		char details[192];

		if (evict_ghost(s, now, &mute) && slot_take(s) == SLOT_TAKEN)
			break;
		reg(s, "slot DENIED to %s from %s: another client of this same user "
		       "holds it (taken: %d) — that occupant gave a sign of life "
		       "%llu ms ago, and the eviction %s",
		    s->user, s->provenance, taken_slots(),
		    (unsigned long long)mute,
		    eviction_ms ? "did NOT fire (threshold in force)"
		               : "is switched OFF by hand (--eviction-ms 0; since 24 Aug "
		                 "2026 the default is 15000)");
		/* ⛔⛔ AND THE SENTENCE NO LONGER DIAGNOSES — 23 Aug 2026.
		 *
		 * It said «there is already a client attached to this session», and the
		 * client built from it **«you already have an active session
		 * elsewhere»**.  ⛔ For whoever reads it after their wire dropped that
		 * sentence is FALSE: that session is theirs, and it died a moment
		 * before.  ⚠ And the server has no way of knowing which of the two it
		 * is: it does not tell a second device from the user themselves who
		 * dropped an instant ago.
		 *
		 * ⇒ One says **only what the server really knows**: that the slot
		 *    appears taken, and how long that occupant has been silent.  The
		 *    number carries with it the answer to the real question of whoever
		 *    reads — «was it me?» — without asserting it: 300 ms means there
		 *    really is someone else, 4000 ms that it almost certainly was them.
		 *
		 * ⚠ The sentence the user SEES is not this one: the page does not read
		 *   the detail, it has its own table (`src/page.html`, `REASON_TEXT[0x0F]`).
		 *   That line changes only if the director chooses the sentence — it is
		 *   the only thing in this cure that is not decided alone. */
		snprintf(details, sizeof details,
		         "the slot of this session is held by a client that "
		         "gave a sign of life %llu ms ago",
		         (unsigned long long)mute);
		dismiss(s, RCP_ALREADY_ACTIVE_REMOTELY, details);
		return false;
	}
	case SLOT_NO_MORE_SLOTS:
		/* ⛔ §8.2 `0x0E`: «well formed but cannot be served», and it MUST carry
		 * the detail in the body — which `dismiss()` puts there.  ⚠ Saying `0x0F`
		 * to this user would be telling them «you already have a session
		 * elsewhere», which is false: they have none, it is the server that has
		 * no more slots. */
		reg(s, "⛔ slot DENIED to %s from %s: the session registry of "
		       "this server is FULL (%d of %d) — it is NOT 0x0F, this user "
		       "has no session elsewhere",
		    s->user, s->provenance, taken_slots(), cap_in_effect);
		dismiss(s, RCP_SESSION_UNSERVABLE,
		        "the session registry of this server is full");
		return false;
	}
	s->is_attached = true;
	reg(s, "slot TAKEN by %s via %s (taken now: %d)", s->user,
	    s->provenance, taken_slots());

	/* ⛔⭐ THE GRANTED CANVAS RESPECTS `video.max_size` — §4.5, finding B-1
	 *
	 *     «The granted canvas MUST respect `video.max_size` if the client
	 *     declared it, and respect in any case the limits and the parity
	 *     above.»  They are two constraints, and both must be satisfied: dividing
	 *     is not enough.
	 *
	 * ⚠ It is reduced keeping the PROPORTIONS, and each side is not cut to its
	 *   ceiling: cutting the sides independently would change the ratio of the
	 *   canvas and the remote desktop would arrive squashed — a defect one
	 *   SEES and that no error code names.  §4.5 allows it
	 *   explicitly: «the granted canvas may differ from the one
	 *   requested […] the client MUST adapt by rescaling».
	 *
	 * ⛔ And the fallback IS WRITTEN TO THE LOG — the same line of §4.5 requires
	 *    it for the KDE fallback, and it applies identically here: a canvas
	 *    different from the one requested, without a line saying why, is
	 *    indistinguishable from a calculation error.
	 *
	 * ⚠ And if not even the MINIMUM legal canvas (320x240) fits under the
	 *   ceiling, an illegal canvas is not granted and one does not keep quiet:
	 *   §4.5 «if the attach cannot be served, the server sends the client away
	 *   with one of the reasons of §8.2 — never with a silence». */
	if (s->max_l && (tl > s->max_l || ta > s->max_a)) {
		uint32_t cl = tl, ca = ta;
		uint32_t requested_w = tl, requested_h = ta;
		/* The side that limits most: cross comparison, without floating-point
		 * divisions. */
		if ((uint64_t)tl * s->max_a <= (uint64_t)ta * s->max_l) {
			ca = s->max_a;
			cl = (uint32_t)(((uint64_t)tl * s->max_a) / ta);
		} else {
			cl = s->max_l;
			ca = (uint32_t)(((uint64_t)ta * s->max_l) / tl);
		}
		cl -= cl % 2; /* §4.5: both EVEN */
		ca -= ca % 2;
		if (cl < 320)
			cl = 320;
		if (ca < 240)
			ca = 240;
		if (cl > s->max_l || ca > s->max_a) {
			char d[160];
			snprintf(d, sizeof d,
			         "video.max_size=%ux%u is below the minimum legal "
			         "canvas of 320x240 (§4.5)",
			         s->max_l, s->max_a);
			reg(s, "⛔ canvas NOT granted to %s: requested %ux%u, ceiling %ux%u — "
			       "not even 320x240 fits under it",
			    s->user, requested_w, requested_h, s->max_l, s->max_a);
			dismiss(s, RCP_SESSION_UNSERVABLE, d);
			return false;
		}
		tl = cl;
		ta = ca;
		reg(s, "⚠ DECLARED FALLBACK (§4.5): canvas requested %ux%u, decoder "
		       "ceiling %ux%u (video.max_size) — GRANTED %ux%u, "
		       "proportions kept, both even",
		    requested_w, requested_h, s->max_l, s->max_a, tl, ta);
	}

	/* ⛔⭐⭐ AND BEFORE GRANTING, THE STAGE IS ASKED WHAT SIZE IT HAS — the cure
	 *     for the RE-ATTACH, `DECISIONS.md` §5.0-sexies («⏳ for when the
	 *     re-attach is tackled: the solution is already measured»).
	 *
	 * ⛔ The case: the stage outlives the client (invariant I4), the canvas is born at
	 *    every attach (§5.0).  Whoever detaches from the DeX with the canvas at
	 *    1912x1044 and reattaches from the laptop asks for 1920x1080 — and the
	 *    stage keeps delivering 1912x1044.  §6.2 forbids sending a frame whose
	 *    size is not the canvas in force ⇒ **zero pixels**, and the only line
	 *    that would say so would be «canvas in force X but the frame is Y», said
	 *    once.
	 *
	 * ⇒ What the stage HAS is granted, and §4.5 allows it in writing: «the
	 *   granted canvas may differ from the one requested».  ⭐ Then the page
	 *   sends its `FIT_CANVAS` and one gets where one wanted — but passing
	 *   through a state in which pixels arrive instead of one in which they do
	 *   not.
	 *
	 * ⚠ And the limits are ALL checked again, because the stage's size did not
	 *   go through this gate: §4.5 (320..4096 x 240..2304, even) and the decoder
	 *   ceiling of THIS client.  ⛔ If it does not pass them it is not granted
	 *   and one does not keep quiet: `rcp_tela_concessa()` takes care of it, and
	 *   at the first frame it will ask the stage to come back. */
	if (s->g.stage_canvas) {
		uint32_t pl = 0, pa = 0;
		if (s->g.stage_canvas(s->g.ctx, &pl, &pa) && pl && pa
		    && (pl != tl || pa != ta)) {
			if (pl < RCP_CANVAS_MIN_W || pl > RCP_CANVAS_MAX_W
			    || pa < RCP_CANVAS_MIN_H || pa > RCP_CANVAS_MAX_H
			    || (pl % 2) || (pa % 2))
				reg(s, "⚠ the stage has the canvas %ux%u, which §4.5 does not "
				       "allow in `SESSION` (%u..%u x %u..%u, even): I grant %ux%u "
				       "as requested, and at the first frame the stage will be "
				       "asked to come here",
				    pl, pa, RCP_CANVAS_MIN_W, RCP_CANVAS_MAX_W,
				    RCP_CANVAS_MIN_H, RCP_CANVAS_MAX_H, tl, ta);
			else if (s->max_l && (pl > s->max_l || pa > s->max_a))
				reg(s, "⚠ the stage has the canvas %ux%u, beyond the "
				       "video.max_size of this client (%ux%u): I grant "
				       "%ux%u, and at the first frame the stage will be asked "
				       "to come here",
				    pl, pa, s->max_l, s->max_a, tl, ta);
			else {
				reg(s, "⚠ DECLARED FALLBACK (§4.5): canvas %ux%u requested, but "
				       "the stage of %s already has one — %ux%u — and it outlives "
				       "the client (I4).  GRANTED the stage's: so the "
				       "frames arrive at once, and the page can ask for "
				       "its size with `FIT_CANVAS`",
				    tl, ta, s->user, pl, pa);
				tl = pl;
				ta = pa;
			}
		}
	}

	uint8_t body[128];
	writer w = {body, sizeof body, 0, false};
	/* ⭐ D-001 (phase 15): the REAL state and desktop, if the host knows them —
	 *    the why is on the two hooks in `rcp.h`.  ⚠ Without hooks it stays what
	 *    it was: `NEW` and `unknown`. */
	bool resumed = s->g.session_resumed && s->g.session_resumed(s->g.ctx);
	const char *desktop = s->g.desktop ? s->g.desktop(s->g.ctx) : NULL;

	if (!desktop || !desktop[0])
		desktop = "unknown";
	sc_byte(&w, resumed ? 2 : 1); /* §4.5: 1 = NEW, 2 = RESUMED */
	sc_u32(&w, tl);
	sc_u32(&w, ta);
	sc_str(&w, desktop);
	reg(s, "SESSION to %s: %s, canvas %ux%u, desktop %s", s->user,
	    resumed ? "RESUMED (the stage was already there)" : "NEW", tl, ta, desktop);
	if (!w.full) {
		send_message(s, T_SESSION, body, w.len);
		/* ⛔⭐ THE VIDEO CHANNEL OPENS **HERE**, AND NOT ONE LINE HIGHER.
		 *
		 * §2.5: «one per frame, ⛔ and **none before having sent
		 * `SESSION`**: whoever receives one before closes with
		 * `PROTOCOL_ERROR`».  It is invariant **I3** on the wire — *whoever
		 * does not pass the validator does not receive a pixel*.
		 *
		 * ⛔ The three lines sit INSIDE the `if`: if the body had not fit
		 *    in the buffer, `SESSION` would not have left, and a video channel
		 *    opened all the same would send frames to a client that knows
		 *    neither the canvas nor the codec.  ⚠ Outside the `if` they would
		 *    look the same and they are not. */
		s->canvas_w = tl;
		s->canvas_h = ta;
		/* ⛔ And the view of the `ATTACH` IS KEPT, instead of being read and
		 *    thrown away: §4.5 defines it as «the size at which the client
		 *    will draw», and `VIEW` (§7.1) is the message that CHANGES it — if
		 *    there were no starting value, the first `VIEW` would change
		 *    a field that has never been anything. */
		s->vista_l = vl;
		s->vista_a = va;
		s->session_sent = true;
		/* ⛔ §5.2, first point: «the first frame the server sends
		 * after `SESSION` MUST be a keyframe». */
		key_needed(s, "it is the first after SESSION (§5.2)");
		s->never_sent_key = true;
	}
	reg(s, "session open user=%s via=%s canvas=%ux%u view=%ux%u "
	       "layout=%s",
	    s->user, s->provenance, tl, ta, vl, va, avail);
	s->state = S_ACTIVE;
	announce_kept(s);

	/* ⛔⭐⭐ AND NOW THE LAYOUT IS APPLIED — `DECISIONS.md` §5-bis.7,
	 *      decided on 8 Aug 2026 and CONFIRMED by the user on the 16th.
	 *
	 * ⛔ Until tonight this line was not there, and the message above —
	 *    «layout=%s» — was **all the server did** with the
	 *    string: it validated it and wrote it.  `[M]` bench `06-b34` case 2:
	 *    reattaching to an `it` session declaring `us`, `è` and `ò` arrived,
	 *    which on `us` exist on no key.
	 *
	 * ⭐ And it is done HERE, after `SESSION`, not up there at validation: if
	 *    the attach had been refused (slot taken, local session, canvas out of
	 *    limits) we would have changed the layout for a user who did not get
	 *    in — and the session outlives the client (I4), so the harm would stay
	 *    there even afterwards.
	 *
	 * ⚠ And it applies to the attach AND to the reattach, because `ATTACH` is
	 *   the same message for both: it is precisely what §5-bis.7 asks —
	 *   *«at session creation or re-attach the keyboard is renegotiated
	 *   too»*. */
	apply_layout(s, "the attach");

	/*
	 * ⭐⭐⭐ AND THE STAGE KNOWS AT ONCE — 16 Aug 2026, and without this line
	 *      the stage was born at a size nobody had asked for.
	 *
	 * ⛔ THE DEFECT, and it has three faces that looked like three defects: the
	 *    child is born with a default canvas (1920x1080) and changes it only
	 *    when an `FIT_CANVAS` arrives.  As long as the page asked for 1920x1080
	 *    at `ATTACH` and corrected itself right after, that message always
	 *    arrived — ⛔ but it was a dance: every session was born wrong and
	 *    resized, and resizing is a race (the backstop of §7.1, the stage being
	 *    mounted, `libei` recreating the devices).  `[M]` it was lost one time
	 *    in three.
	 *
	 * ⇒ Once the page was cured — it now asks for the window from `ATTACH`
	 *   on, as §5.0-sexies has said since 14 August — the dance disappeared
	 *   **and with it the message**: there is nothing left to correct, so nobody
	 *   told the child any more how big the canvas is.  ⭐ The stage was born at
	 *   1920x1080 and the frames were all thrown away.
	 *
	 * ⇒ ⭐ The SERVER says it, here, at the instant the canvas is decided.  It is
	 *   the right place for a reason that holds beyond this case: **whoever
	 *   decides a number is whoever must tell it to whoever uses it**.  Before,
	 *   the client said it on the rebound, and it worked by accident.
	 *
	 * ⚠ And it is not a disguised `FIT_CANVAS`: it answers no message and
	 *   sends nothing on the wire.  If the stage already has that size — the
	 *   re-attach — the child answers «I already have it» and nothing happens.
	 */
	if (s->g.recanvas) {
		reg(s, "⭐ §4.5: I tell the stage that the canvas of this session is %ux%u — "
		       "so it is born that way instead of being born at a size of its own "
		       "and having to change it (and the change is a race)",
		    tl, ta);
		s->g.recanvas(s->g.ctx, tl, ta);
	}
	return true;
}

/* ========================================================================= */
/* ⭐⛔ THE VIDEO CHANNEL — §2.5, §5.1, §5.2, §6.2                            */
/*                                                                           */
/* ⛔ THE ELEVEN RULES, AND WHERE EACH ONE LIVES IN THESE LINES               */
/*                                                                           */
/*  P1  §2.5   no video stream before having SENT `SESSION`                  */
/*             ⇒ `s->session_sent`, switched on by the line that sends it */
/*  P2  §6.2   `nr` starts from 1, 0 is reserved, and AT WRAPAROUND it is */
/*             skipped ⇒ `next_number()`                                  */
/*  P3  §2.5   video lives ONLY on a unidirectional stream of the server      */
/*             ⇒ `g.video_apri`, and never `g.send_msg` (which is control)       */
/*  P4  §6.2   FIN before the 28 bytes is `PROTOCOL_ERROR`                 */
/*             ⇒ the 28 bytes go out in ONE write, and if not it is RESET     */
/*  P5  §6.2   `w.`/`height` are the canvas IN FORCE                     */
/*             ⇒ `s->canvas_w/canvas_h`, which the caller cannot pass             */
/*  P6  §5.2   the first frame after `SESSION` MUST be a keyframe            */
/*  P9  §5.2   and the same at every canvas change                            */
/*             ⇒ `s->needs_key`, switched on ONLY by `key_needed()`      */
/*               and off ONLY by `key_paid()` — see the box of           */
/*               the two functions below, which carries the list of causes    */
/*  §6.2       the 16 MiB ceiling binds the sender FIRST                      */
/*             ⇒ the check is before opening the stream: not a byte leaves    */
/*  §6.2       FIN ⇒ complete · `RESET_STREAM` ⇒ thrown away                  */
/*             ⇒ `rcp_video_finish()` versus `rcp_video_abandon()`         */
/*  §6.2       `codec` MUST be the one negotiated in §4.3                     */
/*             ⇒ `rcp_codec_negotiated()`, and not even this is a parameter    */
/*  §5.1/§5.2  every abandonment in the log, and a KEYFRAME is not abandoned  */
/*                                                                           */
/* ⛔ AND THE SHAPE OF ALL THREE RULES «BY CONSTRUCTION»: `w.`,           */
/*    `height`, `codec` and `nr` **are not parameters of any public      */
/*    function**.  Whoever encodes cannot get them wrong because they cannot  */
/*    touch them.  ⚠ The alternative road — passing them and checking them —  */
/*    would have been shorter and would have put the protection where it can  */
/*    get lost (invariant I7, read from inside the program).                  */

/* ⛔⭐⭐⭐ THE KEYFRAME DEBT — AND THE COMMENT THAT HAD LIED TWICE.
 *
 * This box said *«switched on in THREE places and off in one»*, and the places
 * were FOUR.  Corrected, it said *«FIVE»*, and the lines that switch it on
 * are NINE, for SEVEN causes.  ⛔ Two corrections by hand, two lies: the third
 * was already bought, because the number is not a behaviour — no bench
 * can see that a list has fallen behind, and neither can the compiler.
 *
 * ⭐ ⇒ THE CURE IS NOT COUNTING BETTER, IT IS REMOVING THE COUNT.  The field is
 *      switched on ONLY by `key_needed()` and off ONLY by `key_paid()`.
 *      The authoritative list is therefore `grep -n 'key_needed(' src/rcp.c`,
 *      which cannot age: a new branch that switched on the debt without
 *      passing through here would have to assign the field by hand, and that
 *      shows in a review — while a wrong number inside a comment shows in
 *      none.
 *
 * ⚠ AND WHAT A BENCH CAN VERIFY, if one day one wants it written:
 *   not «how many there are» — which is what ages — but that **the field is
 *   not touched outside the two functions**.  They are two `grep` lines on this
 *   file, and they sit next to the `GEMELLATI` check of the `Makefile`, which
 *   already compares two copies of the same module:
 *
 *     grep -n 'needs_key *=' src/rcp.c   ⇒ MUST give 2 lines only, and they
 *                                             are the two inside the functions
 *                                             below
 *     grep -n 'needs_key_reason *=' src/rcp.c   ⇒ the same 2
 *
 *   ⛔ This check does NOT age with the addition of a cause: it is precisely
 *      the addition of a cause that leaves it green, provided it goes through
 *      the funnel.
 *
 * ⛔ THE SEVEN CAUSES, and the line of each as of 23 Aug 2026 (⚠ the lines are
 *    a courtesy for whoever reads today, NOT the authoritative list — that is
 *    the `grep` above):
 *
 *   1. §5.2  `SESSION` has been sent: the first frame after it
 *            MUST be a keyframe                                     line 2774
 *   2. §5.2  the canvas has changed (`CANVAS` adapted): the first at the new
 *            size MUST be a keyframe                                 line 3234
 *   3. §5.1  a delta was abandoned IN THE QUEUE downstream          line 3601
 *   4. §2.3  a delta was SKIPPED for lack of room — defect B-18,
 *            and it is the cause the old comment did not have       line 3663
 *   5. §5.2  a delta was abandoned by `rcp_video_abandon()`       line 3699
 *   6. §5.2  a frame BROKE HALFWAY — and it is ONE cause on THREE
 *            lines, which is precisely the way the count went wrong:
 *            the 28-byte header did not go out whole (line 3871), a
 *            piece did not go out (line 3883), the FIN arrived with fewer
 *            bytes than declared (line 3908)
 *   7. §5.2  the client sent `REQUEST_KEY`                      line 5689
 *
 * ⛔ AND IT IS SWITCHED OFF IN ONE PLACE ONLY: the keyframe has GONE OUT whole
 *    (line 3919).
 *    ⚠ And it is switched off there and not at the opening of the stream: a
 *      frame opened and then broken has paid nothing, and switching off the
 *      debt at opening would leave the client without a keyframe with the
 *      server convinced of the opposite.
 */
static void key_needed(rcp_session *s, const char *why)
{
	s->needs_key = true;
	s->needs_key_reason = why;
}

static void key_paid(rcp_session *s)
{
	s->needs_key = false;
	s->needs_key_reason = NULL;
}

/* §6.2 — the two values of the `kind` field. */
#define V_KEY 0x0301
#define V_DELTA 0x0302
/* §6.2 — the header is exactly 28 bytes, without padding. */
#define V_HEADER 28
/* ⛔ §6.2 — «the server MUST NOT produce a frame longer than 16 MiB».
 * ⚠ And the ceiling belongs to the FRAME, that is header included: that is how
 *   the receiver counts it, seeing a single stream and not knowing where our
 *   structure ends.  A ceiling counted on the data alone would let through 28
 *   bytes too many, and the difference shows only at the limit — where the
 *   benches put their cases on purpose. */
#define V_CAP (16u * 1024u * 1024u)
/* ⛔ §5.2, exception 5 of §3: 200 ms from the last keyframe SENT. */
#define V_GRACE_KEY 200

/* ⛔ §6.2 — THE COUNTER, AND THE TWO LINES THAT GOVERN IT.
 *
 *   «The first frame of a session carries `nr = 1`, and `0` is
 *    reserved»  —  «And at counter wraparound `0` is skipped: the arithmetic is
 *    module 2^32 […] and from `0xFFFFFFFF` one goes to `1`».
 *
 * ⚠ The second line came in two hours after the first, on 12 Aug 2026,
 *   because without it the reserved value came back into circulation on its own
 *   after two years and two months of session — only once in a lifetime, and
 *   nobody would have connected it to `REQUEST_KEY`.  ⛔ The two lines are
 *   here one under the other on purpose: separating them is how the second
 *   gets lost. */
static uint32_t next_number(uint32_t last)
{
	uint32_t n = last + 1; /* module 2^32, by definition of the type */
	if (n == 0)
		n = 1;
	return n;
}

uint8_t rcp_depth_negotiated(const rcp_session *s)
{
	/* ⛔⭐⭐ AND THIS READER WAS NOT THERE, and its absence cost the most
	 *      expensive defect found so far — 17 Aug 2026, evening, on Firefox.
	 *
	 *      §4.3 has `video.depth` negotiated and the choice ends up in here.
	 *      ⛔ But **nobody read it**: the child wrote `r.depth = 10`
	 *      by hand, for every codec, and the stream went out at 10 bits **while
	 *      `HERE_I_AM` declared 8**.
	 *
	 * ⚠ On Chrome it did not show: HEVC carries its parameters inside the stream
	 *   (VPS/SPS) and the decoder reconfigures itself.  ⛔ On Firefox +
	 *   AV1 no: the page configures `av01.0.12M.08` — the NEGOTIATED depth —
	 *   and dav1d trusts the string.  `[M]` first artefacts, then the
	 *   decoder gets stuck and the desktop freezes.
	 *
	 * ⭐ And it is the same shape as `LESSONS.md` §7.5: **two truths about the
	 *    same fact, and no line binding them**.  The codec crossed the process
	 *    boundary, the depth did not — and no bench could see it, because the
	 *    two numbers live in two different processes.
	 *
	 * ⚠ `0` = not yet negotiated, and it is NOT «8»: whoever has not negotiated
	 *   has no depth, and picking one for them would redo by hand the defect
	 *   this function exists to remove. */
	if (!s || !s->depth[0])
		return 0;
	if (strcmp(s->depth, "8") == 0)
		return 8;
	if (strcmp(s->depth, "10") == 0)
		return 10;
	return 0;
}

uint8_t rcp_level_negotiated(const rcp_session *s)
{
	/* ⛔⭐⭐ AND THIS READER IS FROM 23 AUG 2026, and it is born from a
	 *      MEASUREMENT: canvas 3840x2160, H.264, the client declares
	 *      `video.level=5.1` and the server produces a stream of level
	 *      **5.2**.  §4.3 row 701 is a MUST — *«the server MUST emit a stream
	 *      of a level not higher, and does not guess it»* — and the server
	 *      overshot.
	 *
	 * ⛔ Until tonight the REQUESTED number stopped in here: it was written
	 *    to the log and nobody read it.  The PRODUCED number lives in the
	 *    child (`encoder.c`, from the SPS), which is another process — two
	 *    truths about the same fact, `LESSONS.md` §7.5, exactly the shape of
	 *    the depth of 17 August.  ⇒ Now it crosses the boundary by the same
	 *    road as that one: `rcp.h` → `webtransport.c` → `main.c` →
	 *    `children_video()` → `struct body_video`.
	 *
	 * ⚠ In TENTHS, which is the alphabet of §4.3 (`5.1` ⇒ `51`) and the one the
	 *   child converts back from for each codec — H.264 uses it as is
	 *   (`level_idc`), HEVC triples it (`general_level_idc`).  ⛔ A `uint8_t`
	 *   is more than enough: `6.2` is 62, and §4.3 defines nothing above.
	 *
	 * ⚠ `0` = the client did not declare it (§4.3 does not require it) or wrote
	 *   it malformed, and it does NOT mean «low»: it means «no ceiling», and
	 *   the receiver must not invent one. */
	if (!s || !s->livello_x10 || s->livello_x10 > 255u)
		return 0;
	return (uint8_t) s->livello_x10;
}

uint8_t rcp_codec_negotiated(const rcp_session *s)
{
	if (!s)
		return 0;
	/* §6.2: «`codec`: 1 = HEVC, 2 = AV1.  MUST be the one negotiated in
	 * §4.3».  ⛔ The string is chosen by `first_in_common()` on the client's `HELLO`,
	 * and the translation lives HERE and nowhere else: two tables that
	 * map the same names diverge, and it is the same shape of the defect that
	 * §0 of `RCP.md` exists to remove. */
	if (strcmp(s->codec, "hevc") == 0)
		return 1;
	/* ⚠ `av1` stays HERE and not in `our_codec`: the number is assigned
	 *   forever (§6.2), and this line is its declared tomb — it is no longer
	 *   negotiated, but if it appeared it would be translated right. */
	if (strcmp(s->codec, "av1") == 0)
		return 2;
	if (strcmp(s->codec, "h264") == 0)
		return 3;
	return 0; /* not yet negotiated, or a name RCP/1 does not define */
}

uint8_t rcp_audio_negotiated(const rcp_session *s)
{
	if (!s)
		return 0;
	/* §6.3: «`codec`: 1 = Opus, 2 = PCM (§5.3)».  ⛔ As for video, the
	 * translation from the negotiated name to the number on the wire lives HERE
	 * and nowhere else. */
	if (strcmp(s->audio, "opus") == 0)
		return 1;
	if (strcmp(s->audio, "pcm") == 0)
		return 2;
	return 0; /* not yet negotiated, or a name RCP/1 does not define */
}

bool rcp_canvas_in_effect(const rcp_session *s, uint32_t *lar, uint32_t *h)
{
	if (!s || !s->session_sent)
		return false;
	if (lar)
		*lar = s->canvas_w;
	if (h)
		*h = s->canvas_h;
	return true;
}

/* The declaration, and why the view is NOT the canvas, are in `rcp.h`. */
bool rcp_vista(const rcp_session *s, uint32_t *lar, uint32_t *h)
{
	if (!s || !s->session_sent)
		return false;
	if (lar)
		*lar = s->vista_l;
	if (h)
		*h = s->vista_a;
	return true;
}

bool rcp_video_needs_key(const rcp_session *s)
{
	return s && s->needs_key;
}

uint32_t rcp_video_last_number(const rcp_session *s)
{
	return s ? s->video_number : 0;
}

/* ⛔ §7.1 — the canvas has changed, and §5.2 opens the debt ONLY if it really
 * changed.  See the box in `rcp.h`.
 *
 * ⚠ DECLARED FALLBACK (`CODER.md` §4.2): this form has no clock,
 *   so it CANNOT open the second of grace of §7.1 on the coordinates in
 *   flight — and a silent fallback produces two behaviours under the same
 *   label.  The log line says so; whoever serves `FIT_CANVAS` on the wire
 *   uses `rcp_canvas_adapted_now()`. */
void rcp_canvas_adapted(rcp_session *s, uint32_t lar, uint32_t h)
{
	if (!s || !s->session_sent)
		return;
	if (lar != s->canvas_w || h != s->canvas_h)
		reg(s, "⚠ DECLARED FALLBACK: `rcp_canvas_adapted()` without the time — the "
		       "SECOND OF GRACE of §7.1 on the coordinates of the old canvas "
		       "does NOT open, and a `POINTER` in flight will be refused with "
		       "`PROTOCOL_ERROR`.  Whoever serves `FIT_CANVAS` on the wire should "
		       "call `rcp_canvas_adapted_now()`");
	rcp_canvas_adapted_now(s, lar, h, 0);
	/* ⛔⭐ AND THE GRACE REALLY CLOSES, instead of opening with date ZERO —
	 *     16 Aug 2026, sub-phase 6.4, found by reading.
	 *
	 * ⚠ Without these two lines the line above **said something false**:
	 *   `rcp_canvas_adapted_now(…, 0)` sets `canvas_grace_since = 0` and fills
	 *   `tela_prec_*`, and the grace appears OPEN for all instants smaller than
	 *   `CANVAS_GRACE` — that is the first second of the clock.  ⛔ With a
	 *   monotonic system clock one never gets there and the defect does not
	 *   show; ⚠ with the artificial clock of a bench starting from zero it does,
	 *   and it is precisely the place where this module is mounted bare.
	 *
	 * ⇒ A fallback that declares one thing and does another is worse than the
	 *   fallback: it is the E2 shape, two behaviours under the same label, and
	 *   it is what the `reg()` above exists NOT to be.
	 *
	 * ⛔ And it is NOT measured by any bench, declared instead of kept quiet: to
	 *    test it one would need a clock starting below one second, and the
	 *    handshake of §4.4-bis already consumes fifteen hundred milliseconds. */
	s->canvas_prev_w = 0;
	s->canvas_prev_h = 0;
	s->canvas_grace_since = 0;
}

/* The declaration, the why and the two sizes that kill are in `rcp.h`:
 * here there is only the rule. */
bool rcp_size_allowed(uint32_t width, uint32_t height, uint32_t *out_w,
                        uint32_t *out_h)
{
	uint32_t l, a;

	if (out_w)
		*out_w = 0;
	if (out_h)
		*out_h = 0;
	/* ⛔ The ceiling is checked BEFORE truncating: truncating 100000 to even would
	 * give 100000, that is a number still able to kill the compositor.
	 *
	 * ⛔⭐ AND THE LIMITS ARE THOSE OF §4.5, PER SIDE — corrected on the night of
	 *     15 Aug 2026, while refuting.  The first draft used 200..8192 **on
	 *     both sides**, and `RCP.md` §4.5 is normative: *«width and height
	 *     of the canvas MUST be between 320x240 and 7680x4320»* (the maximum of
	 *     the time; today 4096x2304).  ⚠ The two rules
	 *     already diverged — `ATTACH` applied §4.5 and `FIT_CANVAS` did not —
	 *     and it was **unreachable** as long as `FIT_CANVAS` always answered
	 *     `COMPOSITOR_UNABLE`.  ⛔ The concrete case: one narrows the bottom
	 *     edge of the window, `FIT_CANVAS(1600, 230)` was granted, and
	 *     at RE-ATTACH the same size was refused by `ATTACH` — the
	 *     server not granting in `SESSION` a canvas it had granted itself
	 *     in `CANVAS`.
	 *
	 * ⚠ And the real ceiling of the compositor stays below: `[M]` beyond 16384 per
	 *   side `gnome-shell` dies, and 4096 is well below — see the box in `rcp.h`.
	 *
	 * ⛔⭐ SINCE 1 OCT 2026 ABOVE THE MAXIMUM IT IS REDUCED, NOT REFUSED
	 *     (box in `rcp.h`): the side that overflows goes TO THE MAXIMUM, the
	 *     other stays.  ⚠ And the ceiling is always applied BEFORE truncating:
	 *     100000 becomes 4096, not a number still able to kill the compositor. */
	if (width < RCP_CANVAS_MIN_W || height < RCP_CANVAS_MIN_H)
		return false;
	if (width > RCP_CANVAS_MAX_W)
		width = RCP_CANVAS_MAX_W;
	if (height > RCP_CANVAS_MAX_H)
		height = RCP_CANVAS_MAX_H;
	/* ⚠ DOWNWARDS, always: upwards one would go out of the browser window, and
	 * the extra pixel would come back as a band or as a scale — that is as the
	 * thing this decision removes. */
	l = width & ~1u;
	a = height & ~1u;
	/* ⛔ And truncation cannot bring it below the minimum: 321 -> 320 is
	 * still allowed, but the rule is written instead of trusting that the
	 * numbers add up. */
	if (l < RCP_CANVAS_MIN_W || a < RCP_CANVAS_MIN_H)
		return false;
	if (out_w)
		*out_w = l;
	if (out_h)
		*out_h = a;
	return true;
}

/* ⛔⭐ THE `CANVAS` MESSAGE ON THE WIRE — §7.1.
 *
 * ⚠ Until 14 Aug 2026 this piece did NOT exist: `rcp_canvas_adapted_now()`
 *   changed the canvas in force, opened the grace and wrote to the log, but the
 *   client received **nothing**.  ⇒ A client that had asked for a size would
 *   have been left waiting for an answer nobody sent, and the defect would
 *   have looked like «adaptation does not work» instead of «it is not
 *   written».  It is the shape of fault this project pays for most often: the
 *   piece missing **between** two pieces that are there.
 *
 * `outcome`  1 = FITTED, 2 = REFUSED
 * `reason` 0 if adapted; 1 = COMPOSITOR_UNABLE, 2 = SIZE_OUT_OF_RANGE,
 *          3 = NOT_NOW
 * ⛔ And the two size fields are **the canvas IN FORCE AFTER this message**,
 *    not the one requested: on a refusal they are the previous one, and it is
 *    the only line that tells the client what to continue with. */
static void send_canvas(rcp_session *s, uint8_t outcome, uint8_t reason,
                       uint32_t lar, uint32_t h)
{
	uint8_t body[10];
	writer w = {body, sizeof body, 0, false};

	sc_byte(&w, outcome);
	sc_byte(&w, reason);
	sc_u32(&w, lar);
	sc_u32(&w, h);
	if (w.full) {
		reg(s, "⛔ CANVAS not sent: the body does not fit (our defect)");
		return;
	}
	send_message(s, T_CANVAS, body, w.len);
	reg(s, "CANVAS sent: outcome %u, reason %u, canvas in force %ux%u (§7.1)",
	    outcome, reason, lar, h);
}

/* ⛔ §7.1 / §3 exception 3 — the form that knows WHEN, and opens the grace. */
void rcp_canvas_adapted_now(rcp_session *s, uint32_t lar, uint32_t h,
                           uint64_t now_ms)
{
	if (!s || !s->session_sent)
		return;
	if (lar == s->canvas_w && h == s->canvas_h) {
		/* ⛔ §7.1 answers `CANVAS` even to an `FIT_CANVAS` asking for the
		 * size that is already there: there is no «new size» there, and opening
		 * the keyframe debt would stop the video on a healthy session —
		 * the red to the wrong suspect that this family of rules has
		 * already paid for four times (P8 → P11 → P13 → P14). */
		reg(s, "CANVAS(FITTED) at the size that was already there (%ux%u): the "
		       "canvas in force does not change and §5.2 does NOT open the keyframe debt",
		    lar, h);
		/* ⛔ One answers ALL THE SAME: §7.1 wants one `CANVAS` for every
		 *    `FIT_CANVAS`, and a client that received nothing would wait forever. */
		send_canvas(s, 1 /* FITTED */, 0, s->canvas_w, s->canvas_h);
		return;
	}
	reg(s, "canvas IN FORCE changed from %ux%u to %ux%u (§7.1): from here §6.2 binds "
	       "width/height to the new one, and §5.2 wants a KEYFRAME at the new "
	       "size",
	    s->canvas_w, s->canvas_h, lar, h);
	/* ⛔ §7.1, third exception of §3 — THE GRACE OPENS HERE, and the previous
	 * canvas is kept BEFORE replacing it: «inputs that left before the answer
	 * arrived are not a defect of the client».  ⚠ One second, and no more:
	 * beyond it, the MUST of §7.3 is whole again. */
	s->canvas_prev_w = s->canvas_w;
	s->canvas_prev_h = s->canvas_h;
	s->canvas_grace_since = now_ms;
	s->canvas_w = lar;
	s->canvas_h = h;
	key_needed(s, "it is the first at the new size after CANVAS (§5.2)");
	/* ⛔ And the message goes out AFTER the state has changed, not before: the two
	 *    size fields must state the canvas **in force after**, and it is the only
	 *    order in which they can state it without copying it into a separate
	 *    variable. */
	send_canvas(s, 1 /* FITTED */, 0, s->canvas_w, s->canvas_h);
}

/* ⛔⭐⭐ «THE STAGE MUST SERVE THE CANVAS IN FORCE» — and when it does not, it is
 *     ASKED AGAIN, with a growing wait.
 *
 * ⛔ It is the only honest way out of the disagreement, and the reason lies in
 *    the protocol: §6.2 forbids sending a frame whose size is not the canvas in
 *    force, and §7.1 gives the server no way to change the canvas **on its own
 *    initiative** — an unrequested `CANVAS` is `PROTOCOL_ERROR` for the
 *    client.  ⇒ Of the two parties in disagreement, the one that must move is
 *    the stage, which is ours.
 *
 * ⚠ And the wait grows because the case in which it does not move exists (a
 *   compositor that cannot resize): without it, this line would ask the same
 *   thing at every frame — sixty renegotiations per second, which is the shape
 *   of the 30.8 GB of log of 14 August at another point of the chain.
 *
 * ⚠ Meanwhile the session shows the last good image: ugly and alive
 *   (I1).  The log says so at every attempt, so whoever watches tells «the
 *   desktop is still» from «the desktop is no longer there». */
static void canvas_recall_stage(rcp_session *s, uint64_t now_ms)
{
	/* ⛔⛔⛔ WHOEVER DOES NOT HOLD THE SLOT DOES NOT COMMAND THE STAGE — and
	 *      without this line two sessions of the same user FIGHT OVER the
	 *      canvas, forever.
	 *
	 * `[M]` 15 Aug 2026, morning, the user's REAL session — and it is a defect
	 * I introduced myself last night, found from their «on Android the mouse no
	 * longer takes clicks»:
	 *
	 *   05:10  the laptop attaches, canvas 2544x926
	 *   05:12  silent for thirty seconds ⇒ DETACHED for silence, leaves the slot —
	 *          ⛔ but the session stays alive, with its video channel on and
	 *          its canvas in force
	 *   05:14  the phone attaches, canvas 2560x926
	 *   05:14  from here **seventeen requests per second**: the laptop asks for
	 *          2544, the phone 2560, the laptop 2544 … forever
	 *
	 * ⇒ And every round **restarts the PipeWire stream**, which on Mutter destroys
	 *   and recreates the `libei` devices: `[M]` 640 pointer «replacements», and
	 *   the input region never in agreement with the canvas («⚠ the region
	 *   2560x926 is NOT as big as the canvas 2544x926: I scale the
	 *   coordinates»).  ⛔ The symptom for the user names none of this: **clicks
	 *   no longer take**.
	 *
	 * ⛔ And the growing wait was NOT enough, for a reason that must be said: it
	 *    resets when the stage arrives where this session wants it — which in
	 *    the ping-pong happens at every round.  A time backstop does not cure two
	 *    masters: it cures one insistent master.
	 *
	 * ⇒ ⭐ The cure is the invariant that was already there: I2 says **a single
	 *   graphical session per user**, and the slot (§8.2 `0x0F`) is the way this
	 *   module enforces it.  Whoever does not hold the slot **watches** — does
	 *   not command.  ⚠ And when it speaks again it takes the slot back, and from
	 *   that moment it is the one in command. */
	if (!s->is_attached) {
		if (!s->canvas_mismatch_since) {
			s->canvas_mismatch_since = now_ms;
			reg(s, "⚠ the stage is not at the canvas in force %ux%u, but this "
			       "session does NOT hold the slot (I2): I ask it nothing — "
			       "whoever is attached commands.  ⛔ Two sessions commanding "
			       "the same stage would fight over it at every frame",
			    s->canvas_w, s->canvas_h);
		}
		return;
	}
	if (!s->g.recanvas) {
		if (!s->canvas_mismatch_since) {
			s->canvas_mismatch_since = now_ms;
			reg(s, "⛔ the stage is not at the canvas in force %ux%u and I have no "
			       "hook to ask it to come there: from here all frames are "
			       "discarded (§6.2), and this line is the only one that says so",
			    s->canvas_w, s->canvas_h);
		}
		return;
	}
	if (s->canvas_mismatch_since
	    && now_ms - s->canvas_mismatch_since < s->canvas_mismatch_wait)
		return; /* asked only recently: one does not insist at every frame */

	/* ⛔⭐⭐ TO WHICH SIZE THE STAGE IS CALLED BACK, AND IT IS NOT ALWAYS THE CANVAS
	 *      IN FORCE — cure of 16 Aug 2026, bench `06-b36` case 13.
	 *
	 * ⛔ THE SCENE, and it is the one the box of §7.1 names first: *«a
	 *    remount of the graphical session after a crash»*.  The user narrows
	 *    the window, the server passes `FIT_CANVAS(1600x900)` to the stage, and
	 *    an instant later the stage remounts at 1024x768 on its own — that is NOT
	 *    in response to anything.  Branch 3 of `rcp_canvas_from_stage()` does not
	 *    recognise the request and ends up here.
	 *
	 * ⛔ Calling it back to the canvas IN FORCE (1920x1080) the server contradicts
	 *    the request it passed on itself an instant before, and **condemns to
	 *    `NOT_NOW` an `FIT_CANVAS` that was about to succeed**: the stage goes
	 *    back to 1920x1080, the backstop of §7.1 expires, and the user sees their
	 *    window refused by a server that itself asked the stage to go back.
	 *    ⚠ No bench saw it, because the count of `CANVAS`s adds up: only one,
	 *    and it is the `NOT_NOW` — the green to the wrong suspect.
	 *
	 * ⇒ If a request is IN FLIGHT the stage is called back to **that** size.
	 *   ⛔ And it is not a disguised unsolicited `CANVAS`, which is the thing never
	 *   to do: nothing goes out on the wire.  §3, exception 8: as long as there
	 *   is an unanswered `FIT_CANVAS` the client HOLDS BACK frames of a size
	 *   never announced, so asking the stage for the size in flight is exactly
	 *   the size the client is ready to receive.
	 *
	 * ⚠ And if the stage gets there, `rcp_canvas_from_stage()` recognises it as an
	 *   answer (`intended` = what was asked for) and the `CANVAS(FITTED)` goes out
	 *   by the normal road: the user's request SUCCEEDS instead of
	 *   expiring. */
	uint32_t target_w = s->canvas_flight ? s->canvas_flight_w : s->canvas_w;
	uint32_t target_h = s->canvas_flight ? s->canvas_flight_h : s->canvas_h;

	if (!s->canvas_mismatch_since) {
		s->canvas_mismatch_wait = RCP_CANVAS_RETRY_MS;
		if (s->canvas_flight)
			reg(s, "⛔ the stage went its own way WHILE %ux%u was in flight: "
			       "I ask it for %ux%u — the size IN FLIGHT, not the canvas in force "
			       "%ux%u.  ⚠ Calling it back would condemn to NOT_NOW an "
			       "`FIT_CANVAS` that is about to succeed, and §3 exception 8 says "
			       "the client HOLDS BACK frames while it waits for the answer",
			    s->canvas_flight_w, s->canvas_flight_h, target_w, target_h, s->canvas_w,
			    s->canvas_h);
		else
			reg(s, "⛔ the stage is not at the canvas in force %ux%u: §6.2 forbids "
			       "sending a frame of a different size, so from here nothing "
			       "leaves any more.  I ask it for %ux%u — and I will insist with "
			       "a growing wait, because a `CANVAS` nobody "
			       "asked for would make the client close the session (§6.2)",
			    s->canvas_w, s->canvas_h, target_w, target_h);
	} else {
		s->canvas_mismatch_wait *= 2;
		if (s->canvas_mismatch_wait > RCP_CANVAS_RETRY_MAX_MS)
			s->canvas_mismatch_wait = RCP_CANVAS_RETRY_MAX_MS;
		reg(s, "⛔ the stage is not yet at %ux%u (canvas in force %ux%u%s): "
		       "request repeated, next in %llu ms",
		    target_w, target_h, s->canvas_w, s->canvas_h,
		    s->canvas_flight ? ", with a request in flight" : "",
		    (unsigned long long)s->canvas_mismatch_wait);
	}
	s->canvas_mismatch_since = now_ms;
	s->g.recanvas(s->g.ctx, target_w, target_h);
}

/* ⭐⭐ THE STAGE'S ANSWER — see `rcp.h`, and the three cases are three.
 *
 * ⛔⛔ AND WHAT THIS FUNCTION **NO LONGER DOES**, because it was the most
 *     serious defect of the first draft: **it never sends a `CANVAS` nobody
 *     asked for.**
 *
 *     The first draft, when the stage changed size on its own, adopted its size
 *     and sent `CANVAS` so as not to leave the session without pixels.  ⚠ It
 *     looked like the kind choice and ⛔ it was fatal: §6.2 says the client
 *     holds back a size never announced **only while it has an unanswered
 *     `FIT_CANVAS`**, and there it has none ⇒ `PROTOCOL_ERROR`, session
 *     closed.  And the frame travels on a stream of its own, so it can arrive
 *     **before** the `CANVAS` that would justify it: half the time.
 *
 * ⇒ The stage must needs the canvas in force, and if it is not there it is
 *   ASKED AGAIN, with a growing wait.  ⚠ Meanwhile the session shows the last
 *   good image: it is ugly and alive, which is what I1 requires. */
void rcp_canvas_from_stage(rcp_session *s, uint32_t intended_w, uint32_t intended_h,
                        uint32_t got_w, uint32_t got_h, uint64_t now_ms)
{
	if (!s || !s->session_sent)
		return;

	/* --- 1. the stage did not make it ---------------------------------- */
	/* ⛔ `0x0` is not a size: it is «I did not make it», and it must be told
	 *    apart from silence (`CODER.md` §3.10).  ⇒ If it was answering a request
	 *    of OURS, `NOT_NOW` is answered **now** instead of letting the backstop
	 *    expire: three seconds of waiting for news that is already there. */
	if (!got_w || !got_h) {
		if (s->canvas_flight && intended_w == s->canvas_flight_w
		    && intended_h == s->canvas_flight_h) {
			reg(s, "the stage could not give the canvas %ux%u: NOT_NOW at once, "
			       "without waiting for the %u ms backstop (§7.1).  The canvas stays "
			       "%ux%u",
			    intended_w, intended_h, (unsigned)RCP_CANVAS_WAIT_MS, s->canvas_w,
			    s->canvas_h);
			s->canvas_flight = false;
			send_canvas(s, 2 /* REFUSED */, 3 /* NOT_NOW */, s->canvas_w,
			           s->canvas_h);
		}
		return;
	}

	/* --- 2. the stage is where it must be ------------------------------ */
	if (got_w == s->canvas_w && got_h == s->canvas_h) {
		if (s->canvas_mismatch_since) {
			reg(s, "⭐ the stage is back at the canvas in force %ux%u: the "
			       "disagreement is over",
			    got_w, got_h);
			s->canvas_mismatch_since = 0;
			s->canvas_mismatch_wait = 0;
		}
		/* ⛔ And if the request in flight asked for PRECISELY this size, it is
		 *    an answer: the stage already had it.  ⚠ Without this line, asking
		 *    for the size that is already there while another is in flight would
		 *    close with no frame — and one would end up on the three-second
		 *    backstop. */
		if (s->canvas_flight && intended_w == s->canvas_flight_w
		    && intended_h == s->canvas_flight_h) {
			s->canvas_flight = false;
			reg(s, "CANVAS(FITTED) %ux%u: the stage already had that size",
			    got_w, got_h);
			send_canvas(s, 1 /* FITTED */, 0, s->canvas_w, s->canvas_h);
		}
		return;
	}
	/* --- 3. the stage is elsewhere ------------------------------------- */
	/* ⛔⭐ AND IT IS ADOPTED **ONLY** IF IT ANSWERS OUR REQUEST, that is if
	 *     `intended` is the one we asked for.  ⚠ The size OBTAINED may be yet
	 *     another — §4.5 allows it, and on KWin < 6.8 it is the normal road —
	 *     but the RECOGNITION is made on the question, not on the answer.
	 *     ⛔ Recognising on the answer was the defect of the two chained
	 *     requests: the frame of the first was taken as the answer to the
	 *     second, and the desktop settled on the wrong size. */
	if (s->canvas_flight && intended_w == s->canvas_flight_w
	    && intended_h == s->canvas_flight_h) {
		if (got_w != intended_w || got_h != intended_h)
			reg(s, "⚠ the stage granted %ux%u where %ux%u was asked: §4.5 "
			       "allows it, and the `CANVAS` leaving now carries the REAL "
			       "size",
			    got_w, got_h, intended_w, intended_h);
		/* ⛔ The decoder ceiling is NOT overridden here either (§4.5): a
		 *    canvas the client cannot decode is a black screen declared
		 *    instead of kept quiet — but black all the same. */
		if (s->max_l && (got_w > s->max_l || got_h > s->max_a)) {
			reg(s, "⛔ the stage gave %ux%u, beyond the video.max_size of "
			       "this client (%ux%u): I do NOT adopt it, and I answer NOT_NOW.  "
			       "The canvas stays %ux%u and the stage is asked for that one",
			    got_w, got_h, s->max_l, s->max_a, s->canvas_w, s->canvas_h);
			s->canvas_flight = false;
			send_canvas(s, 2 /* REFUSED */, 3 /* NOT_NOW */, s->canvas_w,
			           s->canvas_h);
			canvas_recall_stage(s, now_ms);
			return;
		}
		s->canvas_flight = false;
		s->canvas_mismatch_since = 0;
		s->canvas_mismatch_wait = 0;
		/* ⛔ And the rest is done by the function that was already there: it
		 *    changes the canvas in force, opens the second of grace on the
		 *    coordinates, marks the keyframe debt (§5.2) and sends `CANVAS(FITTED)`. */
		rcp_canvas_adapted_now(s, got_w, got_h, now_ms);
		return;
	}

	/* ═══════════════════════════════════════════════════════════════════
	 * ⛔⛔ 4. THE STAGE WAS ALREADY THERE AND DOES NOT MOVE — and the video never
	 *      started.  22 Sep 2026, the user's manual test on KDE.
	 *
	 * ⛔ THE SCENE, and they found it: the server restarts, the Plasma session
	 *    OUTLIVES it (invariant I4) with its stage at 2544x926, and the
	 *    client comes back in from a window of another size asking for
	 *    2560x962.  ⚠ The table of the stages' canvases lives in the PROCESS:
	 *    with the restart it resets, so the `ATTACH` fallback — «what the
	 *    stage HAS is granted» — has nothing to grant and passes the client's
	 *    size.  ⇒ Canvas in force 2560x962, stage 2544x926, and §6.2 forbids
	 *    sending a frame of a different size: **black screen forever**,
	 *    while the log repeats «I ask it for 2560x962» with a wait that
	 *    doubles.  ⛔ And KWin `--virtual` does not resize: the request
	 *    cannot succeed either today or in an hour.  `[M]` cured by hand by
	 *    closing the user's session, which is the opposite of what I4 promises.
	 *
	 * ⭐ THE CURE: the stage's size is adopted, exactly as `ATTACH` does
	 *    when it knows it — ⛔ but ONLY as long as not even one frame has gone out.
	 *    Before the first frame the client has not seen a pixel at this
	 *    canvas, has none in flight, and there is no race between streams
	 *    to arbitrate: the `CANVAS` leaving now is the only truth it will
	 *    ever have had.  ⚠ After the first frame NOTHING is touched and one
	 *    keeps asking, because there an unsolicited `CANVAS` would contradict
	 *    frames already delivered (§6.2) — and the rule is written in
	 *    `RCP.md` §7.1 instead of only here.
	 *
	 * ⚠ And the limits are checked again, as in branch 3: §4.5 and the decoder
	 *   ceiling of THIS client.  A stage out of limits is not adopted
	 *   — one keeps asking, and the black screen stays declared. */
	if (!s->video_sent && !s->canvas_flight
	    && (got_w != s->canvas_w || got_h != s->canvas_h)) {
		uint32_t pl = 0, pa = 0;
		if (!rcp_size_allowed(got_w, got_h, &pl, &pa)
		    || pl != got_w || pa != got_h) {
			reg(s, "⚠ the stage is at %ux%u, which §4.5 does not allow: I do NOT "
			       "adopt it and keep asking for the canvas in force %ux%u",
			    got_w, got_h, s->canvas_w, s->canvas_h);
		} else if (s->max_l && (got_w > s->max_l || got_h > s->max_a)) {
			reg(s, "⚠ the stage is at %ux%u, beyond the video.max_size of "
			       "this client (%ux%u): I do NOT adopt it and keep "
			       "asking for the canvas in force %ux%u",
			    got_w, got_h, s->max_l, s->max_a, s->canvas_w, s->canvas_h);
		} else {
			reg(s, "⭐ §7.1: the stage was already at %ux%u when this session was "
			       "born (canvas in force %ux%u) and NO frame has gone out "
			       "yet: I ADOPT its size instead of asking it for one "
			       "it cannot give.  ⛔ Without this line a compositor that "
			       "does not resize (KWin --virtual) leaves the screen black "
			       "forever after a server restart",
			    got_w, got_h, s->canvas_w, s->canvas_h);
			s->canvas_mismatch_since = 0;
			s->canvas_mismatch_wait = 0;
			rcp_canvas_adapted_now(s, got_w, got_h, now_ms);
			return;
		}
	}

	/* ⛔ No request of ours, or a different request: the stage is elsewhere
	 *    on its own.  ⚠ It may be a remount after a crash of the graphical
	 *    session, or the late frame of a request that has already expired.  ⇒
	 *    The canvas in force is ASKED FOR AGAIN, and nothing is adopted. */
	canvas_recall_stage(s, now_ms);
}

bool rcp_canvas_postpone(rcp_session *s, uint32_t intended_w, uint32_t intended_h,
                      uint64_t now_ms)
{
	if (!s || !s->canvas_flight)
		return false;
	if (intended_w != s->canvas_flight_w || intended_h != s->canvas_flight_h)
		return false;
	/* ⭐ The start is moved, the backstop is not lengthened: so the ceiling of
	 *    §7.1 stays what it is, and counts from when someone is really trying. */
	s->canvas_flight_from = now_ms;
	reg(s, "§7.1: the stage is NOT there YET for the canvas %ux%u — the %u ms "
	       "backstop is POSTPONED instead of answering NOT_NOW to a question about "
	       "to get a real answer",
	    intended_w, intended_h, (unsigned)RCP_CANVAS_WAIT_MS);
	return true;
}

bool rcp_canvas_in_flight(const rcp_session *s, uint32_t *lar, uint32_t *h)
{
	if (!s || !s->canvas_flight)
		return false;
	if (lar)
		*lar = s->canvas_flight_w;
	if (h)
		*h = s->canvas_flight_h;
	return true;
}

/* ⛔ §7.1 — THE BACKSTOP OF THE WAIT: «to every `FIT_CANVAS` the server MUST
 *    answer with a `CANVAS`, successful or not».  Called by `rcp_time()`, that is
 *    by the only place that sees time pass even when no byte arrives.
 *
 * ⚠ And the delay is NOT measured from when the message arrived but from when
 *   the question LEFT for the stage: they are the same instant today, and the
 *   day a queue sat in between they would no longer be. */
static void canvas_expires(rcp_session *s, uint64_t now_ms)
{
	if (!s->canvas_flight)
		return;
	if (now_ms - s->canvas_flight_from < RCP_CANVAS_WAIT_MS)
		return;
	reg(s, "⛔ FIT_CANVAS %ux%u: the stage did not deliver a frame at "
	       "that size within %u ms — I answer NOT_NOW (§7.1: a silence "
	       "would leave the client waiting forever, and §6.2 makes it "
	       "HOLD BACK frames while it waits).  The canvas stays %ux%u",
	    s->canvas_flight_w, s->canvas_flight_h, (unsigned)RCP_CANVAS_WAIT_MS, s->canvas_w,
	    s->canvas_h);
	s->canvas_flight = false;
	send_canvas(s, 2 /* REFUSED */, 3 /* NOT_NOW */, s->canvas_w, s->canvas_h);
}

void rcp_video_counts(const rcp_session *s, uint32_t *shipped,
                     uint32_t *abandoned)
{
	if (shipped)
		*shipped = s ? s->video_sent : 0;
	if (abandoned)
		*abandoned = s ? s->video_abandoned : 0;
}

/* ⛔⭐ §5.1 — THE ABANDONMENT DECIDED DOWNSTREAM, AND WHY THE ONE ABOVE WAS NOT
 * ENOUGH.
 *
 * `rcp_video_abandon()` below can abandon **the open frame**, that is one
 * still missing a piece to write.  ⛔ But the scene §5.1 describes in its own
 * words — «the server MAY call `RESET_STREAM` on a frame that is no longer
 * needed, **because a more recent one has already left**» — is not that one:
 * there the old frame was written WHOLE and closed with FIN, and it sits still
 * in the transport's output queue because the line does not carry it away.
 * For RCP that frame is already finished (`video_is_open` is false), and
 * `rcp_video_abandon()` would return `false` without writing a line.
 *
 * ⇒ Whoever holds the queue — `webtransport.c` — is the only one that knows
 *   which frames are still **on the wire or before the wire**, and therefore
 *   the only one that can decide the abandonment of §5.1.  ⛔ But the three
 *   consequences of that abandonment belong to RCP and not to it: the mandatory
 *   log line (§5.1), the count of the abandoned, and ⛔ **the keyframe debt**
 *   (§5.2 — «when the server abandons a delta it MUST send a keyframe as soon
 *   as it can»).  Leaving them to whoever holds the queue would mean two copies
 *   of the same state, which is the shape `RCP.md` §0 exists to remove.
 *
 * ⛔ AND THE KEYFRAME IS NOT ABANDONED EVEN DOWNSTREAM: §5.2 forbids it without
 *    distinguishing who decides.  Here it is REFUSED and written, as above —
 *    otherwise the rule would apply to one road and not to the other, and
 *    which of the two is travelled would depend on how fast the line is. */
bool rcp_video_abandoned_downstream(rcp_session *s, uint32_t nr, bool key,
                                   size_t unsent_bytes, const char *why)
{
	if (!s)
		return false;
	if (key) {
		reg(s, "⛔ I do NOT abandon frame %u in the queue: it is a KEYFRAME, and "
		       "§5.2 forbids it downstream too (reason asked: %s) — %zu bytes "
		       "were left to go out",
		    nr, why ? why : "undeclared", unsent_bytes);
		return false;
	}
	s->video_abandoned++;
	/* ⛔ §5.1: «every abandonment MUST be written to the log: a frame lost in
	 * silence and one abandoned on purpose look the same from the receiving
	 * side».  ⚠ And it says how many bytes did NOT go out: it is the
	 * difference between «I threw it away before spending bandwidth» and «I had
	 * almost sent it already», which are two different facts for whoever
	 * regulates the rate. */
	reg(s, "frame %u ABANDONED IN THE QUEUE (§5.1, RESET_STREAM): %zu bytes "
	       "did not go out, why: %s — sent %u, abandoned %u",
	    nr, unsent_bytes, why ? why : "undeclared",
	    s->video_sent, s->video_abandoned);
	/* ⛔ §5.2: «when the server abandons a delta, it MUST send a keyframe
	 * as soon as it can — without waiting for the client to ask». */
	key_needed(s, "a delta was abandoned in the queue (§5.1)");
	return true;
}

/* ⛔ §2.3 — THE MISSING STREAM CREDIT, WRITTEN TO THE LOG FROM ONE PLACE ONLY.
 *
 * §2.3 ends like this: «and in both cases **it is written to the log**», where
 * the two cases are the delta thrown away and the keyframe that waits.  ⛔ The
 * line exists because without it the symptom is *«screen frozen, and no line in
 * the log saying why»* — finding R1.9 names it word for word.
 *
 * ⚠ And the counter of the abandoned is NOT touched: here the stream was never
 *   born, so there is nothing to reset on the wire and the `nr` has not
 *   been consumed (§6.2: «NOT for those it does not send at all»).  They are
 *   two different quantities and keeping them together would confuse whoever
 *   diagnoses. */
void rcp_video_no_credit(rcp_session *s, bool key, uint64_t remain)
{
	if (!s)
		return;
	if (key) {
		reg(s, "⛔ §2.3: no unidirectional stream for a KEYFRAME (the client "
		       "still grants %llu).  ⚠ The keyframe is NOT thrown away: §5.2 "
		       "wants it, the debt stays on and it is retried at the next "
		       "frame — «waiting for a free slot» is exactly what "
		       "§2.3 prescribes for keyframes",
		    (unsigned long long)remain);
		return;
	}
	reg(s, "⚠ §2.3: no unidirectional stream for the delta that came after "
	       "%u (the client still grants %llu): the delta is THROWN AWAY — «an "
	       "old delta is no longer needed, a new one is already arriving».  ⛔ "
	       "And it is not a fatal error: the session holds (§2.3)",
	    s->video_number, (unsigned long long)remain);
	/* ⛔⭐ AND THE KEYFRAME DEBT IS SWITCHED ON — it was missing, and it is defect
	 *     B-18.
	 *
	 *   §5.2: «when the server abandons a delta, it MUST send a keyframe as
	 *   soon as it can, without waiting for the client to ask».  The two
	 *   twins that abandon a delta already do so — the abandonment in the queue
	 *   (above, §5.1) and `rcp_video_abandon()` (below, §5.2) — and HERE the
	 *   harm seen from the receiving side is the same: the decoder is missing a
	 *   delta, and from there on it produces images more and more broken.
	 *
	 * ⛔ AND HERE IT IS NEEDED MORE THAN IN THE TWO TWINS, because the client
	 *    NEVER notices on its own:
	 *      · the `nr` has NOT been consumed (the box above, §6.2),
	 *        so in the numbers there remains **no gap** — and it is the only signal
	 *        on which §5.2 has the client ask for a keyframe;
	 *      · the encoder runs with an infinite GOP (`chiavi_ogni = 0`, in
	 *        `encoder_of()` of `src/child.c` — line 4220 as of 23 Aug
	 *        2026; ⚠ the reference said `src/child.c:1568`, which is a point
	 *        of the file that code has not lived in for a while: it is the same
	 *        disease as the count of switch-ons below, and that is why here
	 *        there is the NAME of the function, which does not drift with the
	 *        lines), so another keyframe would **never again** arrive on its own.
	 *    ⇒ Without this line, ONE SINGLE delta skipped for lack of room
	 *      wrecks the image **forever and in silence**: no error,
	 *      no line, and the client has no way of asking for the cure.
	 *
	 * ⚠ And if room is still missing when the keyframe is ready, one does not fall
	 *   back into the case forbidden by R1.9: the `key` branch above does NOT
	 *   throw it away — it keeps the debt on and retries at the next frame, which
	 *   is what §2.3 prescribes for keyframes. */
	key_needed(s, "a delta was skipped for lack of room (§2.3), and "
	                "no gap remains in the numbers");
}

/* ⛔ §5.1 — the abandonment, and §5.2 forbids abandoning a KEYFRAME. */
bool rcp_video_abandon(rcp_session *s, const char *why)
{
	if (!s || !s->video_is_open)
		return false;
	if (s->video_is_key) {
		/* ⛔ §5.2: «the server MUST NOT abandon a keyframe.
		 * Abandoning the cure is not a cure».  ⚠ And the refusal is WRITTEN: a
		 * prohibition enforced in silence is indistinguishable from a
		 * prohibition nobody applied. */
		reg(s, "⛔ I do NOT abandon frame %u: it is a KEYFRAME, and §5.2 "
		       "forbids it (reason asked: %s)",
		    s->video_its_number, why ? why : "undeclared");
		return false;
	}
	s->g.video_reset(s->g.ctx, s->video_stream);
	s->video_is_open = false;
	s->video_abandoned++;
	/* ⛔ §5.1: «every abandonment MUST be written to the log: a frame lost in
	 * silence and one abandoned on purpose look the same from the receiving
	 * side». */
	reg(s, "frame %u ABANDONED (§5.1) after %zu bytes of %zu, stream %lld, "
	       "why: %s — sent %u, abandoned %u",
	    s->video_its_number, s->video_written, s->video_to_write,
	    (long long)s->video_stream, why ? why : "undeclared",
	    s->video_sent, s->video_abandoned);
	/* ⛔ §5.2: «when the server abandons a delta, it MUST send a
	 * keyframe as soon as it can — without waiting for the client to
	 * ask, because the client notices one network round trip later».
	 * ⭐ It is the only cure we have: at a missing delta the decoder raises
	 * no error, it just produces images more and more broken. */
	key_needed(s, "a delta was abandoned (§5.2)");
	return true;
}

/* ⛔⭐⭐⭐ THE FRAME THROWN AWAY **BEFORE THE WIRE** — the form the receiver
 *        does not see, and that until 23 Sep 2026 DID NOT PAY THE KEYFRAME.
 *
 * `RCP.md` §5.1 lists TWO observable forms of abandonment — the stream
 * reset (A) and the gap in the `nr`s (B) — and then names a third that
 * «is not observable at all», the delta thrown away for lack of credit
 * (§2.3, cause 4).  ⛔ Of that third form there were **three instances**, and
 * only one paid the debt:
 *
 *   | who throws away                    | number consumed | debt paid |
 *   |---|---|---|
 *   | §2.3, the credit run out           | no | ✅ `rcp_video_no_credit()` |
 *   | ⛔ the RATE REGULATOR (phase 9)     | no | ⛔ **none** |
 *   | ⛔ the CANVAS THAT DOES NOT MATCH (§6.2) | no | ⛔ **none** |
 *
 * ⭐⭐ It is §1.20 once more: *«a cure is sought wherever it applies, not where
 *     it was found»*.  The cure of cause 4 was written for the credit, and the
 *     two branches born later — the phase 9 regulator and the canvas check —
 *     throw away an **already encoded** frame in the very same way
 *     without anyone noticing.
 *
 * ⛔⛔ THE HARM, AND WHY NO COUNTER SEES IT — `[M]` 23 Sep 2026,
 *      box `rete11-gnome`, scenario `due-inquilini`, 180 s, two rounds:
 *
 *      | | Firefox (H.264) | Chrome (HEVC) |
 *      |---|---|---|
 *      | frames sent | 6938, numbered 1…6938 | 7351, numbered 1…7351 |
 *      | **gaps in the numbering** | **0** | **0** |
 *      | frames never sent because of the rate | **27** | **38** |
 *      | KEYFRAMES sent in the whole session | **1** | **1** |
 *      | `REQUEST_KEY` received | **0** | **0** |
 *
 *      ⇒ 65 encoded frames thrown away, and the client could not notice
 *        in any way: the numbering that reaches it is CONTINUOUS, because the
 *        `nr` is born in `rcp_video_open()` and those frames never get
 *        there.  ⛔ And the encoder runs with an infinite GOP
 *        (`chiavi_ogni = 0`, `encoder_of()` in `src/child.c`): after
 *        keyframe 1 another keyframe **never again** arrives on its own.
 *      ⇒ The user saw the image IN TILES — the still areas (the icons)
 *        stayed the wrong mosaic, the moving ones were repainted
 *        and looked healthy — with **all counters green**.  It is exactly
 *        what §5.2 describes: *«at a missing delta the decoder raises no
 *        error, it just produces images more and more broken until the
 *        next keyframe»*.
 *
 * ⚠ WHY A NEW FUNCTION AND NOT `rcp_video_abandoned_downstream()`: that one
 *   is form **A**, and its line says «ABANDONED IN THE QUEUE (§5.1,
 *   RESET_STREAM): N bytes did not go out».  Here no stream was ever born
 *   and no byte went out: using it would write into the log one form in place
 *   of another — the E8 shape that `RCP.md` §11.1 (finding P7) exists to
 *   remove — and would make `video_abandoned` grow, which the box of
 *   `rcp_video_no_credit()` above expressly forbids («here the stream
 *   was never born, so there is nothing to reset on the wire and the `nr`
 *   has not been consumed»).
 *
 * ⚠ And the debt is ALWAYS switched on, even if what is thrown away was a
 *   KEYFRAME: a keyframe thrown away before the wire is not an «abandoned»
 *   keyframe in the sense of §5.2 — nothing was denied to it, it simply could
 *   not leave with those numbers (wrong canvas).  ⛔ Leaving the debt off there
 *   would mean no keyframe ever again, which is the worse fault of the two.
 *
 * ⭐ And it goes through the funnel: `key_needed()`.  The `needs_key` field
 *    is not touched by hand — see the box of the two functions, and the check
 *    `grep -n 'needs_key *=' src/rcp.c` which must give TWO lines only. */
void rcp_video_discarded_before_wire(rcp_session *s, bool key,
                                       const char *why)
{
	if (!s)
		return;
	/* ⛔ §5.1: «every abandonment MUST be written to the log: a frame lost in
	 * silence and one abandoned on purpose look the same from the receiving
	 * side».  ⭐ AND HERE IT COUNTS DOUBLE, because from the receiving side
	 * this has **no** look at all: the log line is the only place in the world
	 * where this fact exists.
	 *
	 * ⚠ BUT ONE LINE PER EPISODE, NOT PER FRAME: under congestion this
	 *   branch is travelled at 60/s, and sixty lines per second are the defect of
	 *   the 30.8 GB of log — the one that `key_interval_ms()` and the line
	 *   «the rate GOES DOWN» already exist not to redo.  ⭐ And the episode has a
	 *   NATURAL boundary and not a clock: as long as the debt is on the cure
	 *   is already travelling and the fact has not changed; when it goes off it
	 *   means a keyframe has GONE OUT WHOLE (`key_paid()`), and the next
	 *   discard is a new fact that deserves its own line.
	 * ⛔ AND THE COUNT IS NOT LOST: how many frames were thrown away is
	 *    already known by the counters of `webtransport.c` — `video_rate_lowered`
	 *    for the regulator and `video_skipped` for the canvas — and they are
	 *    written by the «rate of …» line (one per second) and by the session's
	 *    «tally finale».
	 *    ⇒ Here the line carries the CAUSE, which is not there; the number is
	 *      there, which does not fit here. */
	if (!s->needs_key)
		reg(s, "⛔ %s frame THROWN AWAY BEFORE THE WIRE (the third form of §5.1, "
		       "the one the receiver does not see): %s.  ⚠ No stream opened, "
		       "no byte gone out, and the `nr` has NOT been consumed — after "
		       "%u the next in sequence will arrive, so no gap remains in the "
		       "numbers and the client cannot ask for anything.  ⭐ §5.2: the "
		       "KEYFRAME debt is switched on here, or the image stays broken "
		       "forever.  ⚠ One line per debt EPISODE: how many were "
		       "thrown away is said by `video_rate_lowered` and `video_skipped` "
		       "in the «rate of …» line and in the final count",
		    key ? "KEYFRAME" : "delta", why ? why : "undeclared",
		    s->video_number);
	/* ⛔ AND THE DEBT IS ALWAYS SWITCHED ON, line or no line: it is a boolean, it
	 *    costs nothing to switch it on again, and tying it to the line would mean
	 *    tying a cure to a decision about log volume — which is the way to lose
	 *    the cure the day someone touches the backstop. */
	key_needed(s, "a frame was thrown away before the wire, and no gap "
	                "remains in the numbers (§5.1 third form, §5.2)");
}

int rcp_video_open(rcp_session *s, bool key, size_t length,
                   uint64_t instant_us, uint32_t input, uint64_t now_ms)
{
	if (!s)
		return RCP_VIDEO_NO_CHANNEL;

	/* ⛔ ALL FOUR HOOKS OR NONE.  A host that could open and not
	 * reset could not honour §5.1, and would notice halfway through a
	 * frame: here the thing is said before opening anything. */
	if (!s->g.video_open || !s->g.video_write || !s->g.video_fin ||
	    !s->g.video_reset)
		return RCP_VIDEO_NO_CHANNEL;

	if (s->video_is_open)
		return RCP_VIDEO_ALREADY_OPEN;

	/* ⛔ P1 / §2.5 / invariant I3 — «none before having sent
	 * `SESSION`».  ⚠ And the FINISHED session counts as «no longer»: after a
	 * farewell the control channel is no longer there, and a frame that
	 * left now would reach nobody. */
	if (!s->session_sent || s->state == S_FINISHED) {
		reg(s, "⛔ NO VIDEO: `SESSION` has not been sent (state %s) — "
		       "§2.5 forbids opening a video stream before, and it is "
		       "invariant I3 on the wire",
		    STATE_NAMES[s->state]);
		return RCP_VIDEO_BEFORE_SESSION;
	}

	/* ⛔ P6 and P9 / §5.2 — the first after `SESSION`, and the first at the new
	 * size after a `CANVAS`, MUST be a keyframe.  ⚠ Here one REFUSES
	 * instead of promoting the delta to keyframe: promoting it would be lying
	 * about the `kind` field, and the frame would not become decodable on its own.
	 * The encoder has the right answer — `rcp_video_needs_key()` — and can
	 * ask it BEFORE encoding. */
	if (!key && s->needs_key) {
		reg(s, "⛔ FRAME NOT SENT: it is a delta and §5.2 wants a KEYFRAME "
		       "(%s).  ⚠ Asking `rcp_video_needs_key()` before "
		       "encoding costs nothing; here the frame is thrown away",
		    s->needs_key_reason ? s->needs_key_reason : "§5.2");
		return RCP_VIDEO_NEEDS_KEY;
	}

	/* ⛔ §6.2 — THE CEILING BINDS THE SENDER BEFORE ANYTHING ELSE, and that is
	 * why the check sits HERE: before opening the stream, before a byte leaves.
	 * «If encoding produced a larger one, it MUST re-encode it at lower
	 * quality and write it to the log — never send it».
	 *
	 * ⚠ And the comparison is `>` and not `>=`: exactly 16 MiB is legal, the
	 *   ceiling is a maximum.  The difference shows on one case only, and it is
	 *   the case the benches put there on purpose. */
	if (length > (size_t)(V_CAP - V_HEADER)) {
		reg(s, "⛔ FRAME NOT SENT: %zu data bytes + %d of "
		       "header exceed the %u of the §6.2 ceiling — it is RE-ENCODED at "
		       "lower quality, not sent",
		    length, V_HEADER, V_CAP);
		return RCP_VIDEO_TOO_LARGE;
	}

	uint8_t codec = rcp_codec_negotiated(s);
	if (codec == 0) {
		/* §6.2: «MUST be the one negotiated in §4.3».  If there is no
		 * negotiation there is no legitimate value to write, and inventing one
		 * would be the E2 shape — two behaviours under the same label. */
		reg(s, "⛔ NO VIDEO: no codec negotiated in §4.3 (codec=«%s»), and "
		       "§6.2 wants the negotiated one",
		    s->codec);
		return RCP_VIDEO_NO_CHANNEL;
	}

	int64_t stream = 0;
	/* ⛔ P3 / §2.5 — «only on a unidirectional stream opened by the server: a
	 * `0x03` on the control channel is `PROTOCOL_ERROR`».  ⭐ The control
	 * channel in this module is written with `s->g.send_msg`, and from here down
	 * that function does not appear: it is the only way of making the rule
	 * impossible to violate instead of easy to respect. */
	uint64_t remain = 0;
	if (!s->g.video_open(s->g.ctx, &stream, &remain)) {
		/* ⛔ §2.3 — and the two cases are NOT the same case: a delta is thrown
		 * away, a keyframe waits.  The line is written by one function only,
		 * because two lines written in two places diverge. */
		rcp_video_no_credit(s, key, remain);
		return RCP_VIDEO_STREAM_NOT_OPEN;
	}

	uint32_t num = next_number(s->video_number);

	/* ⛔ §6.2 — THE 28 BYTES, IN THIS ORDER AND WITHOUT A BYTE OF PADDING.
	 *
	 *   0  kind u16 · 2 codec u16 · 4 w. u32 · 8 height u32 ·
	 *   12 nr u32 · 16 instant u64 · 24 input u32 · 28 data
	 *
	 * ⚠ The drawing said «… 24 │ 32» until 9 Aug 2026: four bytes of
	 *   padding never declared, which two implementations could guess
	 *   the same without anyone noticing.  ⛔ `writer` writes byte
	 *   by byte in network order on purpose: a C `struct` with `memcpy` here
	 *   would bring that defect back, and not even a bench would see it until the
	 *   two sides ran on two different architectures. */
	uint8_t head[V_HEADER];
	writer w = {head, sizeof head, 0, false};
	sc_u16(&w, key ? V_KEY : V_DELTA);
	sc_u16(&w, codec);
	/* ⛔ P5 / §6.2: the canvas IN FORCE — the one of `SESSION` (§4.5) or
	 * the last one granted by `CANVAS` (§7.1).  Not a parameter. */
	sc_u32(&w, s->canvas_w);
	sc_u32(&w, s->canvas_h);
	sc_u32(&w, num);
	/* ⚠ §6.2: microseconds of the server's MONOTONIC clock at capture.
	 *   It is not a time of day, and the client MUST NOT compare it with its own. */
	sc_u64(&w, instant_us);
	/* §6.2, §7.3: the last input injected before capture, 0 if none. */
	sc_u32(&w, input);

	/* ⛔ P4 / §6.2 — «a stream closed with FIN before the 28 bytes
	 * of the header is `PROTOCOL_ERROR`: it is not a short frame, it is
	 * a length that does not add up».
	 *
	 * ⭐ Hence the form of these six lines: the 28 bytes go out in **a single**
	 *    write, and if they do not, it is RESET.  A stream reset at zero
	 *    bytes is an abandoned frame — §5.1, legal, the session holds —
	 *    while a FIN at zero bytes would be `PROTOCOL_ERROR` and would bring
	 *    down a session in which the one at fault was us.
	 *    ⛔ The two closures are NOT interchangeable, and that is all of §6.2. */
	if (w.full || !s->g.video_write(s->g.ctx, stream, head, sizeof head)) {
		s->g.video_reset(s->g.ctx, stream);
		reg(s, "⛔ the 28 header bytes of frame %u did not "
		       "go out: stream %lld RESET (§6.2) — ⚠ never closed with FIN, or "
		       "it would have been «a length that does not add up»",
		    num, (long long)stream);
		/* The number has been consumed: §6.2 says the counter grows
		 * «including those it then abandons», and a gap «means something». */
		s->video_number = num;
		return RCP_VIDEO_BROKEN_MIDWAY;
	}

	s->video_is_open = true;
	s->video_stream = stream;
	s->video_is_key = key;
	s->video_its_number = num;
	s->video_to_write = length;
	s->video_written = 0;
	s->video_number = num;
	/* ⛔ The time is kept FROM HERE, and one does not go and ask the `instant`
	 * field for it: `instant` is the CAPTURE clock in microseconds (§6.2) and
	 * `now_ms` the session clock in milliseconds.  That they are the same clock
	 * is likely and is written nowhere — and deriving one from the other
	 * would be indexing the 200 ms of §5.2 on a proxy quantity
	 * (`LESSONS.md` §1.13). */
	s->video_open_ms = now_ms;
	return RCP_VIDEO_SENT;
}

int rcp_video_piece(rcp_session *s, const uint8_t *data, size_t len)
{
	if (!s || !s->video_is_open)
		return RCP_VIDEO_STREAM_NOT_OPEN;
	if (len == 0)
		return RCP_VIDEO_SENT;
	/* ⛔ More bytes than were declared would mean that the ceiling of §6.2
	 * was checked on one number and the wire carries another:
	 * the check would become a formality.  It is reset. */
	if (len > s->video_to_write - s->video_written) {
		reg(s, "⛔ frame %u wants to write %zu bytes beyond the %zu "
		       "declared: stream RESET — the ceiling of §6.2 had been "
		       "checked on the declared bytes",
		    s->video_its_number, len, s->video_to_write);
		s->g.video_reset(s->g.ctx, s->video_stream);
		s->video_is_open = false;
		s->video_abandoned++;
		key_needed(s, "a frame broke halfway (§5.2)");
		return RCP_VIDEO_BROKEN_MIDWAY;
	}
	if (!s->g.video_write(s->g.ctx, s->video_stream, data, len)) {
		s->g.video_reset(s->g.ctx, s->video_stream);
		s->video_is_open = false;
		s->video_abandoned++;
		reg(s, "⛔ frame %u broke at %zu bytes of %zu: stream "
		       "RESET (§6.2) — the client throws it away and treats it as a gap, "
		       "which is true; with a FIN it would have handed it to the "
		       "decoder, which is false",
		    s->video_its_number, s->video_written, s->video_to_write);
		key_needed(s, "a frame broke halfway (§5.2)");
		return RCP_VIDEO_BROKEN_MIDWAY;
	}
	s->video_written += len;
	return RCP_VIDEO_SENT;
}

int rcp_video_finish(rcp_session *s)
{
	if (!s || !s->video_is_open)
		return RCP_VIDEO_STREAM_NOT_OPEN;
	/* ⛔ §6.2 — «a stream closed with FIN carries a COMPLETE frame».  The
	 * FIN is a statement, not a way of closing: if bytes are missing it is
	 * reset, and the client will treat the frame as a gap instead of
	 * handing half an image to the decoder (finding R1.7, 9 Aug
	 * 2026 — «an abandoned frame and a complete one looked the
	 * same», the E8 error shape). */
	if (s->video_written != s->video_to_write) {
		reg(s, "⛔ frame %u has %zu bytes of the %zu declared: stream "
		       "RESET instead of closed with FIN — FIN means COMPLETE "
		       "(§6.2)",
		    s->video_its_number, s->video_written, s->video_to_write);
		s->g.video_reset(s->g.ctx, s->video_stream);
		s->video_is_open = false;
		s->video_abandoned++;
		key_needed(s, "a frame broke halfway (§5.2)");
		return RCP_VIDEO_BROKEN_MIDWAY;
	}
	s->g.video_fin(s->g.ctx, s->video_stream);
	s->video_is_open = false;
	s->video_sent++;
	if (s->video_is_key) {
		/* ⛔ §5.2: the debt is paid ONCE.  ⚠ And it is switched off HERE and not
		 * at opening: a frame opened and then broken has paid nothing,
		 * and switching off the debt there would have left the client without a
		 * keyframe with the server convinced it had sent one. */
		key_paid(s);
		s->never_sent_key = false;
		/* ⛔ §5.2 / §3 exception 5 — the 200 ms clock starts from HERE, that is
		 * from the keyframe SENT.  ⚠ And «sent» means «the bytes left
		 * us», not «it arrived»: see finding P17 in the report, which
		 * declares the difference instead of correcting it on its own initiative. */
		s->last_key_ms = s->video_open_ms;
		s->last_key_number = s->video_its_number;
	}
	reg(s, "frame %u SENT: %s, codec %u, %ux%u, %zu data bytes, "
	       "stream %lld, FIN (§6.2: complete) — sent %u, abandoned %u",
	    s->video_its_number, s->video_is_key ? "KEYFRAME 0x0301" : "delta 0x0302",
	    rcp_codec_negotiated(s), s->canvas_w, s->canvas_h, s->video_written,
	    (long long)s->video_stream, s->video_sent, s->video_abandoned);
	return RCP_VIDEO_SENT;
}

int rcp_video_send(rcp_session *s, bool key, const uint8_t *data,
                       size_t len, uint64_t instant_us, uint32_t input,
                       uint64_t now_ms)
{
	int e = rcp_video_open(s, key, len, instant_us, input, now_ms);
	if (e != RCP_VIDEO_SENT)
		return e;
	if (len) {
		e = rcp_video_piece(s, data, len);
		if (e != RCP_VIDEO_SENT)
			return e;
	}
	return rcp_video_finish(s);
}

/* ========================================================================= */
/* ⭐ THE INPUT CHANNEL — `RCP.md` §2.5, §3, §3.1, §6.0, §6.1, §7.1, §7.3    */
/*                                                                           */
/* ⛔ WHAT THIS SECTION DOES NOT KNOW, AND IT IS HALF ITS JOB:                */
/*    it does not know what `libei` is, it does not know what a keyboard      */
/*    layout is, it does not know what a device is.  It reads bytes, judges   */
/*    them against §7.3 line by line, and calls one of the five hooks.  The   */
/*    other half — the one that touches the real desktop — is in `src/input.c`. */
/*                                                                           */
/* ⛔ AND THE RIGOR RULE (§3) APPLIES HERE AS ELSEWHERE: an unknown type, a   */
/*    length that does not add up, a field out of range, a message in the     */
/*    wrong state ⇒ `PROTOCOL_ERROR`, with the reason, by both roads of    */
/*    §3.1.  ⚠ With ONE declared exception, and it is the third of the list   */
/*    of §3: the second of grace of §7.1.                                     */

/* ⛔⭐ §7.3 — «On detach everything is released», and the four roads that
 *     end a connection all pass through here.
 *
 * ⚠ And the fallback is DECLARED (`CODER.md` §4.2): if the hook is not there,
 *   this function writes that it is not there instead of keeping quiet —
 *   because «no key was pressed» and «I could not release anything» look the
 *   same, and it is `LESSONS.md` §1.9 rule 1 in the field where it costs most:
 *   the symptom of both is a desktop that does not respond on reattach. */
static void release_on_detach(rcp_session *s, const char *why)
{
	if (!s || s->inp_released)
		return;
	s->inp_released = true;
	if (!s->g.input_release_all) {
		/* ⛔ It is written ONLY if this channel has seen something pass: on a
		 * session without input — the in-process benches, the ngtcp2 harness —
		 * the line would be noise at every farewell, and noise makes people stop
		 * reading the log precisely where it is needed. */
		if (s->inp_arrived)
			reg(s, "⚠ DECLARED FALLBACK (§7.3): the connection ends (%s) and "
			       "this server does NOT have the release hook — %u inputs had "
			       "arrived and %u injected.  If something was left pressed, "
			       "it stays pressed",
			    why, s->inp_arrived, s->inp_injected);
		return;
	}
	int amount = s->g.input_release_all(s->g.ctx);
	/* ⛔⛔⭐ THREE OUTCOMES, THREE DIFFERENT LINES — 16 Aug 2026, and before there
	 *      was only one that printed `amount` as if it were always a count.
	 *
	 *      In the real product it NEVER is: the one holding the map of pressed
	 *      keys is the child, and its answer does not come back.  ⇒ The
	 *      line said «0 were pressed» at every detach, including the four
	 *      in which the child, just below, wrote `2`.
	 *
	 *      ⚠ An invented number is worse than no number, and here it was the
	 *        worst possible: a ZERO on a rule whose only way of failing is
	 *        releasing nothing.  `LESSONS.md` §1.9 — «empty» and
	 *        «right» with the same face. */
	if (amount == RCP_RELEASE_IMPOSSIBLE) {
		reg(s, "⛔ §7.3 — RELEASE ON DETACH (%s): the release could NOT be "
		       "requested from the stage.  ⚠ If something was pressed, it STAYS "
		       "pressed: on reattach the desktop may be unusable, and "
		       "this is the line that connects the two",
		    why);
		return;
	}
	if (amount == RCP_RELEASE_NO_COUNT) {
		reg(s, "⭐ §7.3 — RELEASE ON DETACH (%s): request SENT to the stage. "
		       " ⚠ This line does NOT carry the number, because the one who knows "
		       "it is the child: the real count is the line «release at detach: "
		       "N keys and buttons», a few milliseconds further down",
		    why);
		return;
	}
	reg(s, "⭐ §7.3 — RELEASE ON DETACH (%s): %d keys and buttons were "
	       "pressed and have been released.  ⚠ Zero is a normal outcome and is NOT "
	       "a failure: it means nothing was down",
	    why, amount);
}

/* ⛔ §3.1 applied to this channel: one writes WHAT — the type, the field, the
 * value, the state — and then sends the farewell by both roads.  ⭐ The `FAREWELL`
 * goes out on the CONTROL channel even when the violation arrived on the
 * input stream, and it is §3.1 point 2 to the letter: «on the control channel,
 * **if the control channel is still usable**» — and here it usually is. */
static void viola_input(rcp_session *s, const char *fmt, ...)
    __attribute__((format(printf, 2, 3)));

/* ⭐ THE MODIFIERS, the only keys whose code goes into the log (phase 16
 *    §12): Ctrl 29/97, Shift 42/54, Alt 56/100, CapsLock 58, Meta 125/126.
 * ⚠ Twin of `log_speakable_key()` (`src/log.c`): this module
 *   is also mounted without the server's log (`benches/rcp/`), and so it
 *   carries the list with it. */
static bool speakable_key(unsigned c)
{
	switch (c) {
	case 29: case 42: case 54: case 56: case 58:
	case 97: case 100: case 125: case 126:
		return true;
	default:
		return false;
	}
}
static void viola_input(rcp_session *s, const char *fmt, ...)
{
	char d[224];
	va_list ap;
	va_start(ap, fmt);
	vsnprintf(d, sizeof d, fmt, ap);
	va_end(ap);
	dismiss(s, RCP_PROTOCOL_ERROR, d);
}

/* How many body bytes this type of §7.3 expects.  ⛔ `0` = a type this
 * channel does not know, and then it is `PROTOCOL_ERROR` (§3): none of the five
 * has an empty body, so zero is not ambiguous. */
static uint32_t input_size(uint16_t kind)
{
	switch (kind) {
	case T_POINTER:
		return I_POINTER;
	case T_BUTTON:
		return I_BUTTON;
	case T_WHEEL:
		return I_WHEEL;
	case T_LETTER:
		return I_LETTER;
	case T_KEY_POSITION:
		return I_POSITION;
	default:
		return 0;
	}
}

static const char *input_name(uint16_t kind)
{
	switch (kind) {
	case T_POINTER:
		return "POINTER";
	case T_BUTTON:
		return "BUTTON";
	case T_WHEEL:
		return "WHEEL";
	case T_LETTER:
		return "LETTER";
	case T_KEY_POSITION:
		return "KEY_POSITION";
	default:
		return "?";
	}
}

/* ⛔ All five hooks or none — the same rule as the four of video, and for the
 * same reason: a channel that could move the pointer and could not
 * release a button would leave the desktop worse than it found it. */
static bool has_input_channel(const rcp_session *s)
{
	return s->g.input_pointer && s->g.input_button && s->g.input_wheel &&
	       s->g.input_letter && s->g.input_position;
}

/* ⛔⭐ THE INJECTION SCOREKEEPER — and the outcomes are THREE, not two.
 *
 *   0  delivered to the compositor  ⇒ the `id` advances in the `input` field of §6.2
 *  -1  not delivered                ⇒ it does NOT advance, and it is written
 *   1  (`LETTER` only) the character cannot be produced with the session's
 *      layout ⇒ it does NOT advance, and §7.3 REQUIRES writing it: «the server MUST
 *      write it to the log and MUST NOT send a different character nor
 *      keep quiet».
 *
 * ⛔ None of the three is a violation by the CLIENT: the message was valid, and
 *    closing the session because our compositor said no
 *    would punish whoever did nothing wrong — «an ugly session is worth more than
 *    a closed session» (`CODER.md` §1). */
static void mark_injection(rcp_session *s, uint16_t kind, uint32_t id,
                            int outcome, const char *what)
{
	if (outcome == 0) {
		s->inp_injected++;
		/* ⛔ §6.2: it is HERE that the number that will come back in the frames
		 * advances — at the only point where «injected» is a fact and not a hope. */
		s->inp_last_injected = id;
		return;
	}
	s->inp_not_injected++;
	if (outcome == 1 && kind == T_LETTER)
		reg(s, "⛔ §7.3: the LETTER %s (input id=%u) CANNOT be produced with the "
		       "layout of this session.  ⚠ No different character is sent "
		       "and one does not keep quiet: this is the line, and the `input` field "
		       "of the frames stays at %u because nothing was injected",
		    what, id, s->inp_last_injected);
	else
		reg(s, "⚠ %s (input id=%u, %s) was NOT delivered to the compositor "
		       "(outcome %d): the session HOLDS — the client did nothing "
		       "wrong — and the `input` field of §6.2 stays at %u",
		    input_name(kind), id, what, outcome, s->inp_last_injected);
}

/* ⛔ §7.3 — THE COORDINATES, and this is the function that already has a finding
 *    (R1.16) written against it.
 *
 *   «`0 ≤ x < canvas_width`, `0 ≤ y < canvas_height`.  On a 1920×1080 canvas
 *    the bottom-right corner is **1919, 1079**.»
 *
 * ⭐ Hence the two cases that must be kept apart, and getting them wrong cost a
 *    finding: **1919 on a 1920 canvas PASSES** — it is the last pixel, not an
 *    error — while **1920 on a 1920 canvas does NOT pass**.  The first of the two
 *    is the one a check written with `>` instead of `>=` ruins in silence,
 *    and the symptom would be a column of pixels on the right that cannot be
 *    clicked.
 *
 * ⛔ AND THE SECOND OF GRACE (§7.1, third exception of §3) is the other half:
 *    «a page that divides the mouse position by the scale factor and
 *    rounds up produces 1920 on a canvas of 1920: one reading
 *    injects it, the other CLOSES THE SESSION — and closing the session for a
 *    rounding is the thing `SPECS.md` §8.3 forbids».  ⇒ For one
 *    second after a canvas change a coordinate valid on the PREVIOUS one is
 *    CLAMPED to the last valid pixel instead of killing the session.
 *
 * ⚠ Outside that second, and outside a canvas change, the MUST of §7.3 stays
 *   whole: close.  ⛔ The grace is NOT a general tolerance on the
 *   coordinates — it would be the indulgence §3 exists to remove — and that is
 *   why it has a start date and a duration.
 *
 * Returns `true` if it can be injected; fills `*sx`/`*sy` with what must be
 * injected (equal to the input, save for clamping). */
static bool allowed_coordinates(rcp_session *s, uint32_t id, uint32_t x,
                               uint32_t y, uint64_t now, uint32_t *sx,
                               uint32_t *sy)
{
	*sx = x;
	*sy = y;
	/* ⛔ The normal case, and the comparison is `<` because they are PIXEL INDICES. */
	if (x < s->canvas_w && y < s->canvas_h)
		return true;

	bool grace_open = s->canvas_prev_w != 0 && s->canvas_prev_h != 0 &&
	                     now >= s->canvas_grace_since &&
	                     now - s->canvas_grace_since <= CANVAS_GRACE;
	if (grace_open && x < s->canvas_prev_w && y < s->canvas_prev_h) {
		*sx = x < s->canvas_w ? x : s->canvas_w - 1;
		*sy = y < s->canvas_h ? y : s->canvas_h - 1;
		s->inp_graces++;
		/* ⛔ §3: «every tolerance must be written to the log.  A silent
		 * tolerance is indistinguishable from a defect». */
		reg(s, "⭐ §7.1 SECOND OF GRACE (time no. %u): input id=%u carries "
		       "(%u,%u), valid on the previous canvas %ux%u and outside the canvas "
		       "in force %ux%u — CLAMPED to (%u,%u) instead of closing.  %llu ms "
		       "of %d have passed since the canvas change",
		    s->inp_graces, id, x, y, s->canvas_prev_w, s->canvas_prev_h, s->canvas_w,
		    s->canvas_h, *sx, *sy,
		    (unsigned long long)(now - s->canvas_grace_since), CANVAS_GRACE);
		return true;
	}

	/* ⛔ §3.1 point 1: one says WHAT, and one also says why the grace did not
	 * cover — «out of range» alone would send people looking for the defect in
	 * the client even when the defect is a second expired by one millisecond. */
	if (s->canvas_prev_w && !grace_open)
		viola_input(s, "POINTER id=%u at (%u,%u): outside the canvas in "
		               "force %ux%u (§7.3: 0<=x<%u, 0<=y<%u), and the grace second "
		               "of §7.1 expired %llu ms ago",
		            id, x, y, s->canvas_w, s->canvas_h, s->canvas_w, s->canvas_h,
		            (unsigned long long)(now > s->canvas_grace_since + CANVAS_GRACE
		                                     ? now - s->canvas_grace_since -
		                                           CANVAS_GRACE
		                                     : 0));
	else if (grace_open)
		viola_input(s, "POINTER id=%u at (%u,%u): outside the canvas in "
		               "force %ux%u AND outside the previous %ux%u — the grace of "
		               "§7.1 covers the coordinates of the old canvas, "
		               "not wrong coordinates",
		            id, x, y, s->canvas_w, s->canvas_h, s->canvas_prev_w,
		            s->canvas_prev_h);
	else
		viola_input(s, "POINTER id=%u at (%u,%u): outside the canvas %ux%u "
		               "— §7.3 wants 0<=x<%u and 0<=y<%u, and the bottom right "
		               "corner is (%u,%u)",
		            id, x, y, s->canvas_w, s->canvas_h, s->canvas_w, s->canvas_h,
		            s->canvas_w - 1, s->canvas_h - 1);
	return false;
}

/* A whole input message, already framed.  `false` = session finished. */
static bool handle_input(rcp_session *s, uint16_t kind, const uint8_t *body,
                         uint32_t lung, uint64_t now)
{
	reader l = {body, lung, 0, false};
	uint32_t id = le_u32(&l);
	uint64_t instant = 0;
	for (int i = 0; i < 8; i++)
		instant = (instant << 8) | le_u8(&l);

	/* ⛔ §7.3: «⛔ 0 is reserved and means "no input"».  It is the value that
	 * §6.2 puts in the `input` field of frames when there has been nothing:
	 * accepting it here would mean that a frame could no longer say «nothing
	 * was injected» without also saying «the first was injected» —
	 * that is the implicit sentinel value §6.0 forbids. */
	if (id == 0) {
		viola_input(s, "%s with id=0: §7.3 reserves zero and gives it "
		               "the meaning «no input» in the `input` field of "
		               "the frames (§6.2)",
		            input_name(kind));
		return false;
	}
	/* ⛔⭐ §7.3: «it grows by AT LEAST ONE with every message, ACROSS THE WHOLE
	 *     INPUT CHANNEL — not one per type.  It is what comes back in the `input`
	 *     field of frames (§6.2), and with separate counters nothing would add up».
	 *
	 * ⚠ «At least one» and not «exactly one»: jumps are legitimate — a client
	 *   that discards an event of its own must not lie about the number — and what
	 *   is not legitimate is going back or repeating.
	 *
	 * ⛔ And the case that unmasks separate counters is only one, and it must go in
	 *    the bench: `BUTTON(9)` and then `POINTER(4)`.  With one counter per
	 *    type that 4 is a legitimate «first POINTER» and passes; with the written
	 *    rule it is a violation.  A bench that sent only increasing ids within
	 *    each type would not tell the two implementations apart. */
	if (id <= s->inp_last_id) {
		viola_input(s, "%s with id=%u, and the last id of THIS CHANNEL was %u: "
		               "§7.3 wants it to grow by at least one over the whole channel, "
		               "not one per type",
		            input_name(kind), id, s->inp_last_id);
		return false;
	}

	uint32_t previous = s->inp_last_id;
	int outcome = -1;
	char what[96];

	switch (kind) {
	case T_POINTER: {
		uint32_t x = le_u32(&l), y = le_u32(&l);
		uint32_t sx = 0, sy = 0;
		if (!allowed_coordinates(s, id, x, y, now, &sx, &sy))
			return false;
		s->inp_last_id = id;
		s->inp_last_instant_us = instant;
		snprintf(what, sizeof what, "(%u,%u)", sx, sy);
		outcome = has_input_channel(s) ? s->g.input_pointer(s->g.ctx, sx, sy) : -1;
		break;
	}
	case T_BUTTON:
	case T_KEY_POSITION: {
		uint16_t code = le_u16(&l);
		uint8_t pressed = le_u8(&l);
		/* ⛔ §7.3: «1 = pressed, 0 = released», and §3 closes on «a field out of
		 * range».  ⚠ A 2 read as «true» would be the exact shape of the
		 * lenient parser: two implementations that behave the same
		 * until one of the two sends 2 by mistake, and then the key stays
		 * down forever and nobody knows why. */
		if (pressed > 1) {
			viola_input(s, "%s id=%u code=%u with pressed=%u: §7.3 admits 1 "
			               "(pressed) and 0 (released), and nothing else",
			            input_name(kind), id, code, pressed);
			return false;
		}
		s->inp_last_id = id;
		s->inp_last_instant_us = instant;
		/* ⛔⛔ PHASE 16 §12: «keystrokes are logged as "key", never as a
		 *      character» — and an evdev code IS a character, up to the
		 *      layout: this line, one per keystroke, turned the
		 *      log into a keylogger.  ⭐ The code stays for
		 *      BUTTONS and for MODIFIERS (`speakable_key()`), which
		 *      say nothing about what is being typed and are the ones that stay
		 *      down (§11). */
		if (kind == T_BUTTON || speakable_key(code))
			snprintf(what, sizeof what, "evdev code %u (%#x) %s", code,
			         code, pressed ? "pressed" : "released");
		else
			snprintf(what, sizeof what, "key %s",
			         pressed ? "pressed" : "released");
		if (!has_input_channel(s))
			outcome = -1;
		else if (kind == T_BUTTON)
			outcome = s->g.input_button(s->g.ctx, code, pressed);
		else
			outcome = s->g.input_position(s->g.ctx, code, pressed);
		break;
	}
	case T_WHEEL: {
		/* ⛔ §6.0: `i32` in two's complement.  The cast from `uint32_t` to
		 * `int32_t` is implementation-defined up to C17; here it is done by
		 * hand, so the value does not depend on the compiler. */
		uint32_t ux = le_u32(&l), uy = le_u32(&l);
		int32_t ax = (int32_t)(ux <= 0x7FFFFFFFu ? (int64_t)ux
		                                         : (int64_t)ux - 4294967296LL);
		int32_t ay = (int32_t)(uy <= 0x7FFFFFFFu ? (int64_t)uy
		                                         : (int64_t)uy - 4294967296LL);
		s->inp_last_id = id;
		s->inp_last_instant_us = instant;
		/* ⛔⛔ AND HERE NOTHING IS TOUCHED: neither the sign, nor the rounding.
		 *
		 *     The sign of the vertical axis is inverted by `input_wheel()`, ONLY
		 *     ONCE and in one place only — it is written in `src/input.h` and in
		 *     `RCP.md` §7.3, box «The sign of the wheel», `[M]` 10 Aug
		 *     2026.  ⛔ Inverting it here too CANCELS it, and the symptom — «the
		 *     wheel goes backwards» — is the E11 error shape that that
		 *     box exists to avoid.
		 *
		 * ⚠ And half notches exist: 120 is one notch, **60 is half a notch and
		 *   is NOT rounded to zero**.  `STUDIES.md` §gnome §9 says that
		 *   `ei_device_scroll_discrete` does an integer division by 120 and
		 *   eats them — but that is a choice of `input.c`, not of here: on this
		 *   side the number passes whole, as it arrived. */
		snprintf(what, sizeof what, "axis_x=%ld axis_y=%ld (120 = one notch)",
		         (long)ax, (long)ay);
		outcome = has_input_channel(s) ? s->g.input_wheel(s->g.ctx, ax, ay) : -1;
		break;
	}
	case T_LETTER: {
		uint32_t car = le_u32(&l);
		/* ⛔ §7.3: «a UNICODE SCALAR VALUE: from 0 to 0x10FFFF, excluding the
		 * surrogates 0xD800-0xDFFF.  Out of range is `PROTOCOL_ERROR`».
		 *
		 * ⚠ «Scalar value» is the technical term, and the surrogates are
		 *   precisely what distinguishes it from «code point»: a
		 *   check that stopped at `car > 0x10FFFF` would let through
		 *   0xD800, which cannot even be written in UTF-8.  ⛔ It is the case
		 *   a page produces on its own: JavaScript counts in UTF-16, and
		 *   `charCodeAt` on an emoji returns **half a surrogate pair**.
		 *   Whoever writes the client with `charCodeAt` instead of `codePointAt` sends
		 *   0xD83D, and the defect must be seen here — not injected as if it were a
		 *   letter.
		 *
		 * ⚠ And ZERO IS LEGITIMATE: U+0000 is a valid scalar value, and §7.3 says
		 *   «from 0».  ⛔ It is not a duplicate of the rule on the `id`, where zero is
		 *   reserved: they are two different fields with two different rules, and
		 *   copying the first onto the second would refuse a character that
		 *   the arbiter allows. */
		if (car > 0x10FFFFu) {
			viola_input(s, "LETTER id=%u with character U+%X: §7.3 wants a "
			               "Unicode scalar value, from 0 to 0x10FFFF",
			            id, car);
			return false;
		}
		if (car >= 0xD800u && car <= 0xDFFFu) {
			viola_input(s, "LETTER id=%u with character U+%04X: it is half of a "
			               "surrogate pair, and §7.3 excludes them — a Unicode "
			               "scalar value does not include 0xD800-0xDFFF",
			            id, car);
			return false;
		}
		s->inp_last_id = id;
		s->inp_last_instant_us = instant;
		/* ⛔ PHASE 16 §12: the character is NOT written (see KEY_POSITION
		 *    above).  ⚠ The two `viola_input` above still quote it:
		 *    they are values a letter cannot be, not keystrokes. */
		snprintf(what, sizeof what, "«a character»");
		outcome = has_input_channel(s) ? s->g.input_letter(s->g.ctx, car) : -1;
		break;
	}
	default:
		/* Never reached: `input_size()` has already refused the types it does
		 * not know, before buffering a byte.  The line is here so that the
		 * day the two lists drifted apart someone would say so. */
		viola_input(s, "type %#06x on the input channel: §7.3 defines five, from "
		               "0x0101 to 0x0105",
		            kind);
		return false;
	}

	s->inp_arrived++;
	/* ⛔⭐ §5.3 — THE ONLY PLACE WHERE THE 30-MINUTE CLOCK IS RESET: a whole
	 *     gesture of §7.3, judged valid.  ⚠ Even when it is NOT injected
	 *     (no hooks, below): the user did make it, and the clock measures
	 *     the user, not the desktop.  The reason is at `DEFAULT_INACTIVITY`. */
	s->last_input = now;
	if (!has_input_channel(s)) {
		/* ⛔ «I have no input channel» is NOT «the client got it wrong».  The
		 * message was valid in every part — we have just judged it —
		 * and closing here would punish whoever did nothing wrong.  ⚠ It is the same
		 * distinction as `RCP_VIDEO_NO_CHANNEL`, and the fallback is DECLARED
		 * (`CODER.md` §4.2): this is the line. */
		s->inp_not_injected++;
		reg(s, "⚠ %s id=%u %s: VALID and NOT injected — this server does not have the "
		       "five hooks of the input channel (§7.3).  The session HOLDS",
		    input_name(kind), id, what);
	} else {
		mark_injection(s, kind, id, outcome, what);
	}

	/* ⚠ The `instant` appears in the log and in no count: §7.3 says that
	 *   «no rule of this document consumes it», and that in a page the
	 *   grain is deliberately coarsened — `milliseconds × 1000` (finding
	 *   R1.27).  ⛔ Whoever derived a delay from it would measure the grain of a
	 *   browser's `performance.now()`, not our loop. */
	reg(s, "input id=%u (was %u) %s %s · client instant %llu us ⚠ coarsened "
	       "grain, §7.3: no measurement is built on it",
	    id, previous, input_name(kind), what,
	    (unsigned long long)instant);
	return true;
}

/* ========================================================================= */
/* ⭐ THE CURSOR — `RCP.md` §7.2, §5.5, §5, §6.1                             */
/*                                                                           */
/* ⛔ WHO CHECKS WHAT, and the line is read only once:                        */
/*                                                                           */
/*    · the limits of **§5.5** — 256 per side, the hotspot inside             */
/*      the image, `0×0` with `0,0` for the hidden one — are enforced by      */
/*      `src/cursor.c` (A6), and HERE THEY ARE NOT CHECKED AGAIN.  Two checks */
/*      on the same rule in two places become two different rules the        */
/*      day one changes, and it is the shape of defect `RCP.md` §0            */
/*      exists to prevent;                                                    */
/*    · the **length of the message** belongs to this module, and §7.2 writes */
/*      it with a MUST: «the length of the message MUST be exactly            */
/*      `8 + width × height × 4`».                                       */
/*                                                                           */
/* ⛔⭐ AND THE CONSEQUENCE OF GETTING IT WRONG IS OURS, NOT THE CLIENT'S: §7.2 */
/*     says a length that does not add up is `PROTOCOL_ERROR` — but the    */
/*     one detecting it is THE RECEIVER.  ⇒ A crooked message sent from here  */
/*     makes **the page** close the session, and the server log would know    */
/*     nothing about it.  «A cursor made of someone else's memory» is the     */
/*     symptom §7.2 names; the lost session is what the user sees.            */
/*                                                                           */
/* ⇒ Hence the rule of this function: **when in doubt it is not sent**, and   */
/*   one writes why (`CODER.md` §4.2 — the fallback is DECLARED).  A cursor   */
/*   that does not update is ugly; a session that drops is broken.            */

int rcp_cursor_shape(rcp_session *s, uint16_t width, uint16_t height,
                      int16_t hot_x, int16_t hot_y,
                      const uint8_t *bitmap, size_t image_n)
{
	if (!s)
		return -1;
	/* §5: the cursor lives on the CONTROL channel, and before `SESSION` there
	 * is nobody to draw it — the client is not yet attached (§4.5).
	 * ⚠ It is nobody's violation: it is a shape arriving too early
	 *   from capture, which starts before the client attaches. */
	if (s->state == S_FINISHED || !s->session_sent) {
		reg(s, "⚠ CURSOR_SHAPE %ux%u NOT sent: `SESSION` has not gone out "
		       "(state %s) — §5, and it is nobody's error: capture "
		       "begins before the client attaches",
		    width, height, STATE_NAMES[s->state]);
		return -1;
	}

	/* ⛔⭐ §5.5 — «ONLY ONE OF THE TWO AT ZERO IS `PROTOCOL_ERROR`», and this
	 *     check sits HERE EVEN THOUGH IT IS ALREADY IN `cursor.c` — decided by the
	 *     coordinator on 14 Aug 2026, after this report had
	 *     flagged it as an open hole.
	 *
	 * ⛔ And it is NOT going back to duplicating the limits of §5.5: the split is
	 *    another one, and it must be read because it is the reason this line does
	 *    not contradict the box above —
	 *
	 *      `cursor.c` decides **what** that cursor is: how big it is,
	 *                  where the hotspot is, whether it is hidden or not received;
	 *      `rcp.c`     ⛔ must not **EMIT** a message the specification
	 *                  forbids, EVER, by any road.
	 *
	 * ⛔⭐ AND THIS IS THE ONLY CASE IN WHICH THE LENGTH CHECK — which is
	 *     right — **IS NOT ENOUGH**: `0×5` gives `0 × 5 × 4 = 0` image bytes,
	 *     that is a message of **eight bytes** whose length **ADDS UP**.  The
	 *     malformed value passes precisely the check that should stop it, and
	 *     none of the other lines of this function looks at it.
	 *
	 * ⚠ The price of not having it: if one day someone called this function
	 *   from a road that does not pass through `cursor.c`, the client would receive a
	 *   message that §5.5 ORDERS it to refuse ⇒ **the session would drop
	 *   through our fault**, and the server log would know nothing about it.
	 *
	 * ⛔ And the pair is told apart only with both cases in the bench: `0×0` is
	 *    the HIDDEN cursor and **must pass**, `0×5` and `5×0` must not.  A check
	 *    that refused all zeros would be green with `0×0` alone — and would make
	 *    the hidden cursor disappear forever, that is the symptom «the pointer
	 *    stays still when I enter a text field». */
	if ((width == 0) != (height == 0)) {
		reg(s, "⛔ CURSOR_SHAPE %ux%u NOT sent: §5.5 wants both sizes at "
		       "zero TOGETHER for the hidden cursor, and «only one of the two at "
		       "zero is PROTOCOL_ERROR».  ⚠ The length WOULD ADD UP (8 bytes, "
		       "no pixel): it is the only case in which the length check "
		       "is not enough, and sending it would make THE PAGE close the session",
		    width, height);
		return -1;
	}

	/* ⛔ §7.2 — THE LENGTH, and it is COMPUTED in one place only.
	 *
	 * ⚠ `(size_t)` on the factors, and it is not pedantry: `width` and `height`
	 *   are `uint16_t` and in C they promote to `int`.  `65535 * 65535 * 4` in
	 *   `int` is **signed overflow**, that is undefined behaviour —
	 *   the compiler is free to give anything, and with `-O2` it usually
	 *   gives a small number.  It is the same defect the bench certification
	 *   found on 14 Aug 2026 on `6u + lung`, in another field and
	 *   with the same mechanism: the narrow arithmetic nobody looks at. */
	size_t pixel = (size_t)width * (size_t)height;
	size_t byte_image = pixel * 4u;

	/* ⛔ The length declared by the caller and the one §7.2 imposes must
	 * match.  ⭐ And the comparison is NOT a formality: without `image_n`
	 * this function would read `width × height × 4` bytes **on trust**
	 * — that is it would do exactly what §7.2 describes as «I read what is
	 * there and go on», only on the sender's side, where we would be the ones
	 * packaging the cursor made of someone else's memory. */
	if (byte_image != image_n) {
		reg(s, "⛔ CURSOR_SHAPE %ux%u NOT sent: §7.2 wants %zu image "
		       "bytes (8 + %ux%ux4 in the message) and the caller brings "
		       "%zu.  ⚠ Sending it would make THE PAGE close the session for "
		       "PROTOCOL_ERROR, and this log would not know it",
		    width, height, byte_image, width, height, image_n);
		return -1;
	}
	/* ⛔ «Zero bytes» and «no pointer» are two different facts: the HIDDEN
	 * cursor of §5.5 is `0×0` **and** no byte, and there `NULL` is right.  With
	 * a size on it, instead, a `NULL` is a defect of the caller — and
	 * reading it would be the end of the process. */
	if (byte_image && !bitmap) {
		reg(s, "⛔ CURSOR_SHAPE %ux%u NOT sent: the size wants %zu bytes and "
		       "the image pointer is NULL",
		    width, height, byte_image);
		return -1;
	}

	/* ⛔ §6.1 — «no message MUST exceed 1 MiB», framing included
	 * (finding B-14).  ⭐ THIS rule belongs to this module, not to `cursor.c`:
	 * there lives §5.5 (256 per side), here §6.1 — and they are two different
	 * paragraphs with two different numbers.  ⚠ At the maximum §5.5 allows,
	 * 256×256, the message weighs 262 158 bytes: **it passes**, and must pass.
	 * A ceiling set wrongly here would kill the largest cursor the arbiter allows. */
	if (byte_image + 8u + 6u > MAX_MESSAGE) {
		reg(s, "⛔ CURSOR_SHAPE %ux%u NOT sent: the message would weigh %zu "
		       "bytes and §6.1 allows %u, framing included.  ⚠ §5.5 stops "
		       "at 256 per side and at that size it is 262 158: if we get here, "
		       "the limit of §5.5 was not enforced upstream",
		    width, height, byte_image + 8u + 6u, MAX_MESSAGE);
		return -1;
	}

	/* ⛔ §7.2 — THE EIGHT BYTES, IN THIS ORDER AND WITHOUT PADDING (§6.0):
	 *   0 width u16 · 2 height u16 · 4 hot_x i16 · 6 hot_y i16 · 8 …
	 *
	 * ⚠ `serial` of `CursorShape` does NOT travel: it is the number by which
	 *   `cursor.c` recognises that the shape has not changed, and §7.2 does not
	 *   provide for it.  Putting it on the wire would be a field two implementations
	 *   guess differently.
	 * ⚠ And the POSITION is not there, because §7.2 says it «never travels in
	 *   this direction»: here only the shape travels. */
	size_t n = 8u + byte_image;
	uint8_t *body = (uint8_t *)malloc(n);
	if (!body) {
		reg(s, "⛔ CURSOR_SHAPE %ux%u NOT sent: out of memory (%zu bytes)",
		    width, height, n);
		return -1;
	}
	writer w = {body, n, 0, false};
	sc_u16(&w, width);
	sc_u16(&w, height);
	/* §6.0: `i16` in two's complement, big-endian.  The conversion to
	 * `uint16_t` is defined by the language and gives exactly those bits. */
	sc_u16(&w, (uint16_t)hot_x);
	sc_u16(&w, (uint16_t)hot_y);
	if (byte_image)
		memcpy(body + 8, bitmap, byte_image);
	/* ⛔⭐ AND `n` IS SENT, NOT `w.len` — found by the bench at the first round,
	 *     14 Aug 2026.
	 *
	 *     `writer` counts the bytes that went through IT, and the image gets
	 *     there with a `memcpy` that `w.len` does not see: after the four `sc_u16`
	 *     it is **8**, and sending `w.len` sent a `CURSOR_SHAPE` declaring
	 *     `width=16, height=16` with **eight bytes of body**.
	 *
	 * ⛔ That is exactly the length that does not add up, produced by us: the page
	 *    would have closed with `PROTOCOL_ERROR` at every cursor shape change,
	 *    and the symptom for the user would have been «the session drops
	 *    when I move the mouse over an edge».  ⚠ The server log wrote
	 *    the right line — «%zu bytes of body = 8 + 16x16x4» — because it
	 *    computed it from `n`: **the log told the truth and the wire something
	 *    else**, which is the shape of defect for which `CODER.md` §3.8 wants
	 *    verification from the receiving side.
	 *
	 * ⭐ What saw it was not a rereading: it was the judge, which reopens the
	 *    bytes that went out and redoes the count of §7.2 on them. */
	if (w.full || w.len != 8u) {
		/* Never reached: `body` is `n` big and the fields are eight bytes.  The
		 * line is there so that the day it were no longer true someone would
		 * say so, instead of sending a crooked message. */
		reg(s, "⛔ CURSOR_SHAPE NOT sent: the eight bytes of the fields did not "
		       "go out (written %zu)",
		    w.len);
		free(body);
		return -1;
	}

	/* ⛔⭐ THE IMAGE IS COPIED IN HERE, AND THE CALL DOES NOT KEEP IT.
	 *
	 *     `src/cursor.h` says so: «it lives until the next callback: whoever
	 *     wants to keep it copies it».  ⇒ When this function returns, this module
	 *     no longer has any pointer to those bytes.
	 *
	 * ⚠ The price, declared: the bytes are copied TWICE — here into
	 *   `body`, and then in `send_message()` which puts the six framing
	 *   bytes in front.  ⛔ It is paid on purpose: the framing of §6.1 is written
	 *   in ONE place only, and copying it here to save a `memcpy` would put
	 *   two readers on the same field.  At the maximum of §5.5 it is 256 KiB on an
	 *   event that happens when the SHAPE changes — not at every frame, because
	 *   `cursor.c` removes the repeats. */
	send_message(s, T_CURSOR_SHAPE, body, n);
	free(body);

	if (width == 0 && height == 0)
		reg(s, "⭐ CURSOR_SHAPE: HIDDEN cursor (§5.5), 8 bytes of body");
	else
		reg(s, "⭐ CURSOR_SHAPE %ux%u sent, hotspot (%d,%d): %zu bytes "
		       "of body = 8 + %ux%ux4 (§7.2)",
		    width, height, hot_x, hot_y, n, width, height);
	return 0;
}

uint32_t rcp_input_last_injected(const rcp_session *s)
{
	return s ? s->inp_last_injected : 0;
}

uint32_t rcp_input_last_id(const rcp_session *s)
{
	return s ? s->inp_last_id : 0;
}

bool rcp_receive_input(rcp_session *s, int64_t stream, const uint8_t *data,
                      size_t len, uint64_t now)
{
	if (!s)
		return false;
	if (s->state == S_FINISHED) {
		/* ⚠ As in `rcp_receive()`: it is the only place from which one observes a
		 *   client that sends after the end (§4.2), and keeping quiet would make
		 *   whoever insists indistinguishable from whoever stopped.  ⛔ But here one
		 *   does not judge «farewell or attempt»: §8.1 wants the farewell on the
		 *   CONTROL channel, and a `FAREWELL` on this stream would anyway be a
		 *   channel in the wrong direction. */
		reg(s, "⛔ %zu bytes on input stream %lld AFTER the end of the "
		       "session from %s: §4.2 forbids sending on any channel",
		    len, (long long)stream, s->provenance);
		return false;
	}

	/* ⛔⭐ §2.5 — «the input stream is opened AFTER receiving `SESSION`».
	 *
	 *     ⚠ And the quantity to look at is «`SESSION` HAS GONE OUT», not «the
	 *       state is active»: it is the same choice already made for video, and for
	 *       the same reason (see the `session_sent` field).
	 *
	 * ⛔⭐ AND THIS TIME THE JUDGEMENT IS LEGITIMATE, while the twin of P20 was
	 *     not, and it is worth saying why: there the CLIENT could not measure
	 *     the order between two independent streams; here the SERVER measures
	 *     something IT did — whether it sent `SESSION` or not.  It is the «local,
	 *     monotonic quantity independent of delivery» of P20, from the right
	 *     side: if `SESSION` has not gone out, the client has not received it,
	 *     and no packet loss can change that. */
	if (!s->session_sent) {
		viola_input(s, "bytes on the input stream (%lld) before `SESSION` "
		               "has gone out: §2.5 opens it AFTER receiving it (state: "
		               "%s)",
		            (long long)stream, STATE_NAMES[s->state]);
		return false;
	}

	/* ⛔ §2.5: «**only one**, and kept open». */
	if (!s->inp_stream_known) {
		s->inp_stream_known = true;
		s->inp_stream = stream;
		reg(s, "⭐ INPUT channel open on stream %lld (§2.5: only one, "
		       "after `SESSION`, and kept open).  The injection hooks: %s",
		    (long long)stream,
		    has_input_channel(s) ? "connected" : "⚠ NOT connected");
	} else if (stream != s->inp_stream) {
		viola_input(s, "a SECOND input stream (%lld) while the first (%lld) "
		               "is still the one: §2.5 admits only one",
		            (long long)stream, (long long)s->inp_stream);
		return false;
	}

	/* ⛔ The silence clock (§5.3) is also reset on input bytes, and it is not a
	 * convenience: without this line whoever uses the desktop **without
	 * writing anything on the control channel** — that is anyone just
	 * moving the mouse — loses the slot after thirty seconds while
	 * working.  §5.3 says «without a byte FROM THE CLIENT», and these are bytes
	 * of the client.
	 * ⚠ The INACTIVITY clock (`last_input`) is NOT reset here, on bytes: it is
	 *   reset in `handle_input()`, on a whole gesture judged valid — a
	 *   fragment or a message refused is not «the user did something». */
	/* ⛔⭐ THE SIGN OF LIFE, for a reason that comes before
	 *     convenience: **an RCP byte arrived inside a packet**.  If
	 *     the byte is there, the packet was there — saying it here is not a
	 *     shortcut, it is the same thing said where it is seen.
	 *
	 * ⚠ And it makes `rcp_sign_of_life()` a PURE ADDITION: it covers the case in
	 *   which packets arrive WITHOUT RCP bytes — that is the user who watches and
	 *   does not touch, which is the case it was born for.  ⛔ Without this line
	 *   the in-process benches (`04-b31`, `01-b12`) would have no sign of life:
	 *   they do not go through the transport, and they would detach thirty seconds
	 *   after opening whatever they did. */
	s->last_life = now;
	if (!speak_again(s))
		return false;

	while (len) {
		/* ⛔⭐ THE LENGTH IS CHECKED ON THE SIX HEADER BYTES, BEFORE
		 *     BUFFERING A BYTE OF BODY — §6.1: «the length is checked
		 *     before allocating.  A receiver that allocates `length` bytes and
		 *     then checks has already given a megabyte to anyone who can write
		 *     six bytes».
		 *
		 * ⭐ On this channel it can be done all the way, and on control it cannot:
		 *    the five types of §7.3 have a FIXED length, known from the `kind`
		 *    alone.  ⇒ The buffer never exceeds 26 bytes, and whoever announces a
		 *    megabyte gets six and a farewell. */
		size_t space = I_ACCUMULATION - s->inp_acc_len;
		size_t amount = len < space ? len : space;
		if (amount == 0) {
			/* Never reached as long as the pruning below works: the line
			 * is there so that the day it did not work someone would say so,
			 * instead of going round in circles. */
			viola_input(s, "input stream accumulation full (%zu bytes) "
			               "without a whole message: it is OUR defect",
			            s->inp_acc_len);
			return false;
		}
		memcpy(s->inp_acc + s->inp_acc_len, data, amount);
		s->inp_acc_len += amount;
		data += amount;
		len -= amount;

		for (;;) {
			if (s->inp_acc_len < 6)
				break;
			reader hdr = {s->inp_acc, s->inp_acc_len, 0, false};
			uint16_t kind = le_u16(&hdr);
			uint32_t lung = le_u32(&hdr);

			/* ⛔ §2.5: on this stream the high byte is 0x01.  A `0x00` here is
			 * «the control channel on a unidirectional stream», a `0x03`
			 * is «video from the client»: they are violations with different names,
			 * and §3.1 point 1 wants the name. */
			if ((kind >> 8) != 0x01) {
				const char *chi = (kind >> 8) == 0x00   ? "CONTROL, which lives "
				                                          "only on the first "
				                                          "bidirectional stream"
				                  : (kind >> 8) == 0x02 ? "the CLIPBOARD, "
				                                          "which wants a stream "
				                                          "of its own per transfer"
				                  : (kind >> 8) == 0x03 ? "VIDEO, which belongs to "
				                                          "the server and goes the "
				                                          "other way"
				                  : (kind >> 8) == 0x04 ? "AUDIO, which lives only "
				                                          "on datagrams"
				                                        : "a channel that §2.5 does "
				                                          "not define";
				/* ⚠ `0x%02x` and not `%#04x`: the latter, on the value ZERO, does
				 *   not print the prefix — it writes `0000` — and the control
				 *   channel is precisely `0x00`.  The most important high byte
				 *   of all would have been the only unreadable one. */
				viola_input(s, "type %#06x on the input stream: the high byte "
				               "0x%02x is %s (§2.5)",
				            kind, (unsigned)(kind >> 8), chi);
				return false;
			}

			uint32_t wait = input_size(kind);
			if (wait == 0) {
				viola_input(s, "type %#06x on the input channel: §7.3 "
				               "defines FIVE — 0x0101 POINTER, 0x0102 "
				               "BUTTON, 0x0103 WHEEL, 0x0104 LETTER, 0x0105 "
				               "KEY_POSITION",
				            kind);
				return false;
			}
			/* ⛔ §6.1: «`length` MUST be the exact number of body bytes.  A
			 * receiver that reads a length inconsistent with what the type
			 * expects MUST close».  ⚠ And one says in which direction it is
			 * wrong: «more» and «fewer» send people looking for two different
			 * defects in the client. */
			if (lung != wait) {
				if (lung > MAX_BODY)
					viola_input(s, "%s (%#06x) announces %u body bytes: beyond "
					               "the 1 MiB ceiling of §6.1, and §7.3 wants "
					               "exactly %u",
					            input_name(kind), kind, lung, wait);
				else
					viola_input(s, "%s (%#06x) announces %u body bytes and §7.3 "
					               "expects %u (%u of id+istante plus %u of its "
					               "own): %s",
					            input_name(kind), kind, lung, wait, I_COMMON,
					            wait - I_COMMON,
					            lung > wait ? "EXTRA bytes, and §6.0 admits "
					                            "no padding"
					                          : "MISSING bytes");
				return false;
			}
			/* ⛔⭐ `(size_t)6u`, AND NOT `6u` — found by the bench certification
			 *     on 14 Aug 2026, injecting the `lunghezza-tardiva`
			 *     fault.
			 *
			 *     `lung` is `uint32_t`: `6u + lung` is computed at **32 bits**, and
			 *     with `lung = 0xFFFFFFFF` the result is not 4 294 967 301 —
			 *     it is **5**.  ⇒ A comparison `inp_acc_len < 6u + lung` would say
			 *     «the body has all arrived» after six bytes, and four gigabytes
			 *     of someone else's memory would be read starting from a buffer
			 *     of 32.
			 *
			 * ⚠ Here it is NOT reachable — the check `lung != wait` sits
			 *   above and closes first — but «not reachable today» and «not
			 *   dangerous» are two different facts: whoever tomorrow moved that
			 *   check by three lines would put the out-of-bounds read back
			 *   without anything changing colour.  ⭐ It is invariant I7 read
			 *   from inside: the protection lives in the program, not in the order
			 *   in which someone left two `if`s. */
			if (s->inp_acc_len < (size_t)6u + lung)
				break; /* the body has not all arrived */

			if (!handle_input(s, kind, s->inp_acc + 6, lung, now))
				return false;

			size_t consumed = (size_t)6u + lung;
			memmove(s->inp_acc, s->inp_acc + consumed,
			        s->inp_acc_len - consumed);
			s->inp_acc_len -= consumed;
		}
	}
	return true;
}

/* ========================================================================== */
/* ⭐⭐ THE CLIPBOARD — §7.4, §5.4, §2.5                                      */
/*                                                                            */
/* ⛔ AND THE DIRECTION USED MOST IS THE ONE THAT COSTS MOST WORK: «I copy an */
/*    address on the phone and paste it into the session» (`DECISIONS.md`    */
/*    §5-ter.1).  Over there we already have the text; over here it has to be */
/*    asked for **while someone is waiting with a finger on Ctrl+V**.         */

static bool has_clipboard_channel(const rcp_session *s)
{
	return s->g.clipboard_open && s->g.clipboard_write && s->g.clipboard_fin
	       && s->g.clipboard_offer && s->g.clipboard_response;
}

static void clipboard_violation(rcp_session *s, const char *fmt, ...)
    __attribute__((format(printf, 2, 3)));
static void clipboard_violation(rcp_session *s, const char *fmt, ...)
{
	char d[224];
	va_list ap;
	va_start(ap, fmt);
	vsnprintf(d, sizeof d, fmt, ap);
	va_end(ap);
	dismiss(s, RCP_PROTOCOL_ERROR, d);
}

/*
 * Sends ONE clipboard channel message, on its own stream, and closes it.
 *
 * ⛔⭐ ONE STREAM PER MESSAGE, AND NOT PER TRANSFER — and it is a point where
 *     §2.5 allows two readings, so the choice is written here instead of
 *     staying implicit (`PLAN.md` §0.4).
 *
 *     §2.5 says «one **per transfer**».  A transfer on our side is made of two
 *     messages far apart in time — `CLIPBOARD_ANNOUNCE` now, `CLIPBOARD_TEXT`
 *     **if and when** someone asks — and keeping a stream open between the two
 *     would mean keeping it open **forever** in the vast majority of cases:
 *     one copies much more often than one pastes, and §2.5 grants the server a
 *     finite number of streams.
 *
 * ⭐ And it can be done, because what binds the messages of a transfer is NOT
 *    the stream: it is the `transfer` field, which exists exactly for this
 *    (finding R1.11, 9 Aug 2026).  The receiver pairs by identifier, and which
 *    stream it arrived on nobody looks at.
 *
 * ⚠ The price, declared: a client that counted streams to count transfers
 *   would count double.  No line of `RCP.md` tells it to do so, and it has the
 *   field it must look at.
 */
static bool send_clipboard(rcp_session *s, uint16_t kind, const uint8_t *body,
                          size_t body_n, const char *queue, size_t tail_n)
{
	uint8_t head[6];
	int64_t stream = 0;
	uint64_t remain = 0;

	if (!has_clipboard_channel(s))
		return false;

	if (!s->g.clipboard_open(s->g.ctx, &stream, &remain)) {
		/* ⛔ Not a byte has left, and that is better than half a message.  ⚠ The
		 *    line says **how many streams remain**, asked of whoever holds the
		 *    transport: without that number «it could not be done» points
		 *    nowhere — it is the same reason as the video's `remain` (§2.3). */
		reg(s, "⛔ CLIPBOARD: no unidirectional stream for message "
		       "%#06x — the client still grants %llu (§2.5 wants one per "
		       "transfer)",
		    kind, (unsigned long long)remain);
		return false;
	}

	head[0] = (uint8_t)(kind >> 8);
	head[1] = (uint8_t)(kind & 0xFF);
	{
		uint32_t lung = (uint32_t)(body_n + tail_n);
		head[2] = (uint8_t)(lung >> 24);
		head[3] = (uint8_t)(lung >> 16);
		head[4] = (uint8_t)(lung >> 8);
		head[5] = (uint8_t)lung;
	}

	if (!s->g.clipboard_write(s->g.ctx, stream, head, sizeof head)
	    || (body_n && !s->g.clipboard_write(s->g.ctx, stream, body, body_n))
	    || (tail_n
	        && !s->g.clipboard_write(s->g.ctx, stream, (const uint8_t *)queue,
	                                tail_n))) {
		/* ⛔ The stream is closed all the same: an open and mute stream holds a
		 *    slot in the client's count and never becomes a message — «empty
		 *    and forbidden with the same face», from the side of whoever waits.
		 * ⚠ The FIN on a half message is less bad than no FIN: the receiver
		 *   finds an incomplete framing and says so, instead of waiting for
		 *   bytes that will not arrive. */
		reg(s, "⛔ CLIPBOARD: message %#06x did not get into the queue on "
		       "stream %lld: I close the stream halfway",
		    kind, (long long)stream);
		s->g.clipboard_fin(s->g.ctx, stream);
		return false;
	}
	s->g.clipboard_fin(s->g.ctx, stream);
	return true;
}

/*
 * ⛔⭐ THE HELD TEXT IS ANNOUNCED WHEN THE SESSION OPENS — 19 Sep 2026.
 *
 * `[M]` phase 12, `kde` box: a client that REATTACHES to a live child makes
 * the desktop clipboard be reread (`child.c`, the reattach branch), and the
 * read arrives while the RCP session is still in `wait-verdict`.  The
 * text was held — «for whoever will attach» — ⛔ but nobody ever announced it
 * afterwards: the client got in and did not know what was in the clipboard.
 * ⇒ It is announced here, after `SESSION` (§2.5: no stream before).
 */
static void announce_kept(rcp_session *s)
{
	uint8_t body[A_ANNOUNCEMENT];
	writer w = {body, sizeof body, 0, false};

	if (!s->app_kept || !s->app_text || !s->session_sent)
		return;
	s->app_kept = false;
	sc_u32(&w, s->app_my_id);
	sc_u32(&w, (uint32_t)s->app_text_n);
	if (w.full || !send_clipboard(s, T_CLIPBOARD_ANNOUNCE, body, w.len, NULL, 0))
		return;
	s->app_announced++;
	reg(s, "⭐ CLIPBOARD §7.4: announced transfer %u to the client — %zu bytes "
	       "copied in the session BEFORE it opened, and held until now",
	    s->app_my_id, s->app_text_n);
}

bool rcp_clipboard_from_session(rcp_session *s, const char *text, size_t byte)
{
	uint8_t body[A_ANNOUNCEMENT];
	writer w = {body, sizeof body, 0, false};
	char *copied;

	if (!s || !text)
		return false;

	/* ⛔ §5.4 — «larger text: it is not announced at all, and the sender writes
	 *    it to the log.  It MUST NOT be truncated».  ⚠ And the comparison is
	 *    `>`: a text **exactly** as large as the ceiling is legitimate, and it is
	 *    the limit case for which §5.4 chose 1 000 000 instead of 1 MiB. */
	if (byte > RCP_CLIPBOARD_CAP) {
		reg(s, "⛔ CLIPBOARD: the session copied %zu bytes, beyond the ceiling of "
		       "§5.4 (%u): it is NOT announced, and NOT truncated — a cut text "
		       "pasted into a terminal is worse than a missing text",
		    byte, RCP_CLIPBOARD_CAP);
		return false;
	}

	if (!s->session_sent || s->state == S_FINISHED) {
		/* ⚠ It is nobody's error: the graphical session outlives the
		 *   client (I4), so one can copy when there is not yet — or no longer —
		 *   anyone to announce it to.  ⛔ But the text is KEPT: whoever attaches
		 *   later finds it again, and it is the case that `STUDIES.md`
		 *   §gnome §10 calls «whoever reconnects». */
		reg(s, "CLIPBOARD: the session copied %zu bytes and there is nobody to "
		       "announce them to (state %s): the text is kept for whoever "
		       "attaches",
		    byte, STATE_NAMES[s->state]);
	}

	if (!s->negotiate_clipboard) {
		reg(s, "CLIPBOARD: the session copied %zu bytes and the client did not "
		       "declare `clipboard.text` (§4.3): nothing is announced",
		    byte);
		return false;
	}

	copied = (char *)malloc(byte + 1u);
	if (!copied) {
		reg(s, "⛔ CLIPBOARD: %zu bytes copied from the session do not fit in "
		       "memory: no announcement",
		    byte);
		return false;
	}
	memcpy(copied, text, byte);
	copied[byte] = 0;
	if (s->app_text)
		explicit_bzero(s->app_text, s->app_text_n);
	free(s->app_text);
	s->app_text = copied;
	s->app_text_n = byte;

	/* ⛔ §7.4: «each side numbers **its own** transfers, from 1
	 *    upwards».  ⚠ Zero is reserved — it means «no announcement» —
	 *    so at counter wraparound it is skipped, as the `nr` of the
	 *    frames of §6.2 does for the same reason. */
	s->app_my_id = s->app_my_id == 0xFFFFFFFFu ? 1u : s->app_my_id + 1u;
	s->app_my_len = byte;

	if (!s->session_sent || s->state == S_FINISHED) {
		s->app_kept = s->state != S_FINISHED;
		return false;
	}
	s->app_kept = false;

	sc_u32(&w, s->app_my_id);
	sc_u32(&w, (uint32_t)byte);
	if (w.full)
		return false;

	if (!send_clipboard(s, T_CLIPBOARD_ANNOUNCE, body, w.len, NULL, 0))
		return false;

	s->app_announced++;
	reg(s, "⭐ CLIPBOARD §7.4: announced transfer %u to the client — %zu bytes "
	       "of text copied in the session.  ⚠ Nothing is sent until "
	       "it asks for them",
	    s->app_my_id, byte);
	return true;
}

bool rcp_clipboard_ask(rcp_session *s, uint32_t serial, uint64_t now_ms)
{
	uint8_t body[A_ASK];
	writer w = {body, sizeof body, 0, false};

	if (!s)
		return false;

	if (!s->session_sent || s->state == S_FINISHED) {
		reg(s, "CLIPBOARD: someone in the session is pasting (request %u) and "
		       "there is no client attached (state %s)",
		    serial, STATE_NAMES[s->state]);
		return false;
	}

	/* ⛔ The request is queued BEFORE sending: if the text arrived
	 *    between the sending and the note — impossible today, the module is
	 *    single-threaded — the answer would find nobody to needs.  ⚠ It is the
	 *    same shape as the rule «first the credit is counted, then delivered»
	 *    of `webtransport.c`: the order costs nothing and removes a class of
	 *    defects. */
	if (s->app_serial_n >= A_STREAM_MAX) {
		reg(s, "⛔ CLIPBOARD: already %d paste requests waiting for the client's "
		       "text: request %u does not fit.  ⚠ The host must answer «I do not "
		       "have it» to this one, or the pasting application stays hanging",
		    s->app_serial_n, serial);
		return false;
	}
	s->app_serial[s->app_serial_n++] = serial;
	/* ⛔ The backstop clock starts from the FIRST request of the batch, not
	 *    from the last: it is the first that is waiting, and it is its wait
	 *    that must be limited. */
	if (s->app_serial_n == 1)
		s->app_requested_ms = now_ms;

	/* ⛔⭐⭐ AND IF THE CLIENT HAS NOT YET ANNOUNCED ANYTHING, ONE WAITS — and
	 *      this is the cure for the race between `Ctrl+V` and the reading of the
	 *      clipboard, which `SPECS.md` §9 names and declares it does NOT
	 *      want to solve like Xpra.
	 *
	 *      The race, in full: the user hits `Ctrl+V` in the browser.  The keys
	 *      leave on the input channel and arrive at the desktop; the clipboard
	 *      announcement leaves on the clipboard channel and travels the same
	 *      road.  ⛔ But the desktop, having received the `Ctrl+V`, asks for the
	 *      text **at once** — and the announcement may not have arrived yet.
	 *      ⇒ The FIRST paste of every new text would come back empty.
	 *
	 * ⛔ Xpra's cure is delaying **every keystroke by 100 ms**: §9 refuses it
	 *    with a number — «for us it is twice the delay ceiling», that is one
	 *    would pay on every key of every session for something that happens
	 *    when pasting.
	 *
	 * ⭐ The replacement costs nothing and touches no key: the request is
	 *    QUEUED and the question leaves when the announcement arrives (see
	 *    `T_CLIPBOARD_ANNOUNCE` in `handle_clipboard`).  ⚠ And the wait is already
	 *    limited by someone else: the child's time backstop answers «I do not
	 *    have it» to whoever pastes if the announcement never arrives — ⛔ and
	 *    that backstop is there because the debt towards the compositor is the
	 *    child's, not ours. */
	if (s->app_peer_id == 0) {
		reg(s, "⭐ CLIPBOARD: someone in the session is pasting (request %u) and "
		       "the client's announcement has not arrived yet: the question WAITS "
		       "for the announcement instead of coming back empty (§9 — the race "
		       "with `Ctrl+V`, cured without delaying keys)",
		    serial);
		return true;
	}
	/* ⚠ One `ASK` for the batch, not one per request: two programs that
	 *   paste together ask for the same transfer, that is the same text, and
	 *   the answer serves them all. */
	if (s->app_requested) {
		reg(s, "CLIPBOARD: request %u joins transfer %u already "
		       "asked for: a single question, and the answer serves them all",
		    serial, s->app_peer_id);
		return true;
	}

	sc_u32(&w, s->app_peer_id);
	if (w.full || !send_clipboard(s, T_CLIPBOARD_ASK, body, w.len, NULL, 0)) {
		s->app_serial_n--;
		return false;
	}

	s->app_requested = true;
	s->app_requested_id = s->app_peer_id;
	s->app_asked++;
	reg(s, "⭐ CLIPBOARD §7.4: asked the client for transfer %u (%u bytes "
	       "announced) — someone in the session is pasting (request %u)",
	    s->app_peer_id, s->app_peer_len, serial);
	return true;
}

/* The question that had been left waiting for the announcement: now it is here.
 * ⛔ `false` = it did not leave, and then the queued requests stay hanging on
 *    the child's time backstop. */
static bool clipboard_ask_backlog(rcp_session *s)
{
	uint8_t body[A_ASK];
	writer w = {body, sizeof body, 0, false};

	if (s->app_serial_n == 0 || s->app_requested || s->app_peer_id == 0)
		return false;

	sc_u32(&w, s->app_peer_id);
	if (w.full || !send_clipboard(s, T_CLIPBOARD_ASK, body, w.len, NULL, 0))
		return false;

	s->app_requested = true;
	s->app_requested_id = s->app_peer_id;
	s->app_asked++;
	reg(s, "⭐ CLIPBOARD §9: announcement %u has arrived, and there were already %d "
	       "paste requests waiting for it: the question leaves NOW.  It is the "
	       "race with `Ctrl+V`, won without delaying a single key",
	    s->app_peer_id, s->app_serial_n);
	return true;
}

/* Serves ALL the waiting requests with the same text: they ask for the same
 * transfer identifier, that is the same content.  ⛔ And the queue is emptied
 * **before** answering: an answer that re-entered here must not find again the
 * requests it is already serving. */
static void clipboard_serve_pending(rcp_session *s, const char *text,
                                    size_t byte)
{
	uint32_t serial[A_STREAM_MAX];
	int amount = s->app_serial_n;

	memcpy(serial, s->app_serial, sizeof serial);
	s->app_serial_n = 0;
	s->app_requested = false;

	if (!s->g.clipboard_response) {
		reg(s, "⛔ CLIPBOARD: %d paste requests without any hook to "
		       "answer: whoever pastes stays hanging until the backstop expires "
		       "on the other side of the boundary",
		    amount);
		return;
	}
	for (int i = 0; i < amount; i++)
		s->g.clipboard_response(s->g.ctx, serial[i], text, byte);
	if (amount)
		reg(s, "⭐ CLIPBOARD: %zu bytes from the client delivered to %d paste "
		       "requests",
		    byte, amount);

	/* ⭐ And NOW the offer that had been postponed: the transfer is over,
	 *    and the compositor can take the new selection without throwing
	 *    anything away. */
	if (s->app_offer_later && s->g.clipboard_offer) {
		s->app_offer_later = false;
		if (!s->g.clipboard_offer(s->g.ctx))
			reg(s, "⛔ CLIPBOARD: the postponed offer did not succeed: inside the "
			       "desktop the next paste will not find the new text");
		else
			reg(s, "⭐ CLIPBOARD: the paste served, the postponed offer has "
			       "left: the desktop has the client's NEW text");
	}
}

/* A whole message of the clipboard channel.  `false` = the session is over. */
static bool handle_clipboard(rcp_session *s, uint16_t kind, const uint8_t *body,
                           uint32_t lung)
{
	reader l = {body, lung, 0, false};
	uint32_t xform;

	switch (kind) {
	case T_CLIPBOARD_ANNOUNCE: {
		uint32_t amount;

		xform = le_u32(&l);
		amount = le_u32(&l);
		if (l.too_short)
			return true; /* the fixed size has already been validated */

		/* ⛔ §7.4: transfers are numbered «from 1 upwards», and zero is
		 *    reserved.  An announcement with `transfer = 0` is not a poor
		 *    announcement: it is an identifier that can never be asked for. */
		if (xform == 0) {
			clipboard_violation(s, "CLIPBOARD_ANNOUNCE with transfer 0: §7.4 numbers "
			                 "them from 1, and 0 means «no announcement»");
			return false;
		}
		/* ⛔ §5.4: the ceiling binds the sender first of all, but whoever
		 *    receives a larger announcement must not get ready to take it in: it
		 *    is a client that has violated §5.4, and §3 makes no discounts. */
		if (amount > RCP_CLIPBOARD_CAP) {
			clipboard_violation(s, "CLIPBOARD_ANNOUNCE of %u bytes: §5.4 stops at %u, and beyond "
			                 "the ceiling NOTHING is announced at all",
			              amount, RCP_CLIPBOARD_CAP);
			return false;
		}

		s->app_peer_id = xform;
		s->app_peer_len = amount;
		reg(s, "⭐ CLIPBOARD §7.4: the client announces transfer %u — %u "
		       "bytes.  ⚠ Nothing is pulled until someone in the session "
		       "pastes",
		    xform, amount);

		/* ⛔ And it is OFFERED to the session, at once: without this step the
		 *    compositor does not own the selection, and inside the desktop
		 *    **one cannot even try to paste** — the key does nothing, and there
		 *    is no error anywhere. */
		if (!s->g.clipboard_offer) {
			reg(s, "⚠ CLIPBOARD: no hook to offer to the session — the "
			       "client copied some text and inside the desktop it will not "
			       "be possible to paste.  ⛔ It is not an error of the client: it "
			       "is this server that does not have that channel");
			return true;
		}
		/* ⛔⛔⭐ AND AN EMPTY ANNOUNCEMENT IS OFFERED ALL THE SAME, and it is a
		 *      choice.
		 *
		 * ⚠ The client sends a zero-byte announcement as soon as the session is
		 *   born, to be found when someone on this side pastes with the mouse:
		 *   without it, the server would never ask it anything (see
		 *   `rcp_clipboard_ask`).
		 *   ⛔ And offering means taking the selection, which is ONE: the
		 *     desktop clipboard changes hands.
		 * ⭐ It changes hands but is NOT lost: if the client has nothing to give,
		 *   `clipboard.c` gives back to the session the last text the session
		 *   itself had given us.  ⇒ The content is safe, and the road of
		 *   pasting with the mouse stays open.
		 * ⚠ Here there was a rule that did NOT offer on empty announcements: it
		 *   protected the clipboard but closed the mouse road, and the protection
		 *   sits better where it is now — where the text really is. */

		/* ⛔ But NOT while someone is pasting: see `app_offer_later`. */
		if (s->app_serial_n > 0) {
			s->app_offer_later = true;
			reg(s, "⚠ CLIPBOARD: announcement %u arrives while %d paste "
			       "requests are waiting for the text: the offer to the session is "
			       "POSTPONED, or the compositor would throw away precisely "
			       "the paste in progress",
			    xform, s->app_serial_n);
			clipboard_ask_backlog(s);
			return true;
		}
		if (!s->g.clipboard_offer(s->g.ctx))
			reg(s, "⛔ CLIPBOARD: the offer of transfer %u to the session did not "
			       "succeed: inside the desktop it will not be possible to paste "
			       "what the client copied",
			    xform);

		/* ⭐⭐ AND HERE THE RACE WITH `Ctrl+V` IS WON: if someone was already
		 *     pasting when the announcement arrived, the question leaves now
		 *     instead of having come back empty a moment ago (§9, and the box of
		 *     `rcp_clipboard_ask`). */
		clipboard_ask_backlog(s);
		return true;
	}

	case T_CLIPBOARD_ASK: {
		xform = le_u32(&l);
		if (l.too_short)
			return true;

		/* ⛔ §7.4: «an `CLIPBOARD_ASK` with an identifier that does not
		 *    match any live announcement is `PROTOCOL_ERROR`».  ⚠ And
		 *    «live» includes superseded ones: see the case just below, which is
		 *    the FIFTH exception declared in §3. */
		if (xform == 0 || xform > s->app_my_id) {
			clipboard_violation(s, "CLIPBOARD_ASK for transfer %u, which "
			                 "matches no announcement: I have made %u "
			                 "(§7.4)",
			              xform, s->app_my_id);
			return false;
		}
		if (!s->app_text) {
			/* ⚠ It can happen: one announced, and then the stage was taken down
			 *   carrying the text away.  It is not the client's fault, and §3.1
			 *   wants it said instead of kept quiet. */
			reg(s, "⛔ CLIPBOARD: the client asks for transfer %u and the text "
			       "is no longer there: nothing will reach it",
			    xform);
			return true;
		}
		/* ⛔⭐ THE FIFTH EXCEPTION DECLARED IN §3 — §7.4: «an `CLIPBOARD_ASK`
		 *     arriving when the announcement has already been superseded by a
		 *     more recent one **is served with the current text**, and the
		 *     sender writes it to the log: it is the normal race between two
		 *     people copying, not an error».
		 * ⚠ And one ANSWERS with the identifier ASKED FOR, not the current one:
		 *   the client expects an answer to its question, and changing the
		 *   number under it would be an answer it cannot pair. */
		if (xform != s->app_my_id)
			reg(s, "⚠ CLIPBOARD §7.4: the client asks for transfer %u, which has "
			       "already been superseded by %u: I serve it with the CURRENT text "
			       "(%zu bytes).  It is the normal race between two people copying, "
			       "not an error",
			    xform, s->app_my_id, s->app_text_n);

		{
			uint8_t head_body[A_TEXT_MIN];
			writer w = {head_body, sizeof head_body, 0, false};

			sc_u32(&w, xform);
			if (w.full)
				return true;
			if (send_clipboard(s, T_CLIPBOARD_TEXT, head_body, w.len,
			                  s->app_text, s->app_text_n)) {
				s->app_served++;
				reg(s, "⭐ CLIPBOARD §7.4: sent %zu bytes to the client "
				       "(transfer %u)",
				    s->app_text_n, xform);
			}
		}
		return true;
	}
	case T_CLIPBOARD_TEXT: {
		const char *text;
		size_t byte;

		xform = le_u32(&l);
		if (l.too_short)
			return true;
		text = (const char *)body + A_TEXT_MIN;
		byte = lung - A_TEXT_MIN;

		/* ⛔ §7.4: «an `CLIPBOARD_TEXT` nobody asked for is
		 *    `PROTOCOL_ERROR`: the clipboard is pulled, not pushed». */
		if (s->app_serial_n == 0) {
			clipboard_violation(s, "CLIPBOARD_TEXT (transfer %u, %zu bytes) that "
			                 "nobody asked for: §7.4 — the clipboard is "
			                 "pulled, not pushed",
			              xform, byte);
			return false;
		}
		/* ⛔⛔⭐ AND HERE THE SESSION WAS CLOSED FOR A NORMAL RACE — the same
		 *      line, with the same mistake, that on 20 Aug 2026 in the PAGE
		 *      produced «Firefox got stuck with the clipboard».
		 *
		 * ⚠ The comparison was with the LIVE announcement: if between our
		 *   question and its answer the client announced again (two copies in a
		 *   millisecond — `[M]`, it happens), the answer carries the OLD number
		 *   by construction, and §7.4 says it is served with the current text and
		 *   **is not an error**.  ⇒ One compares with what one ASKED FOR. */
		if (xform != s->app_requested_id && xform != s->app_peer_id) {
			clipboard_violation(s, "CLIPBOARD_TEXT for transfer %u, which I never "
			                 "asked for (I asked for %u, the live announcement "
			                 "is %u): §7.4 — the clipboard is pulled, "
			                 "not pushed",
			              xform, s->app_requested_id, s->app_peer_id);
			return false;
		}
		if (xform != s->app_peer_id)
			reg(s, "⚠ CLIPBOARD §7.4: the text of transfer %u arrives when "
			       "the live announcement is %u: it is the normal race between two "
			       "people copying, and the text is the CURRENT one",
			    xform, s->app_peer_id);
		/* ⛔ And the announcement said how many bytes: if the text carries a
		 *    different number, one of the two messages lies.  §6.1 — «a length
		 *    inconsistent with what the type foresees».  ⚠ Here the expected
		 *    length does not come from the type, it comes from the announcement
		 *    of the same side: it is the same rule applied to a promise the
		 *    client made itself. */
		/* ⚠ And the size is demanded ONLY on the live transfer: on a
		 *   superseded one the client served the text of NOW, which is not the
		 *   one announced back then — demanding the old length would refuse
		 *   precisely what the exception allows. */
		if (xform == s->app_peer_id && byte != s->app_peer_len) {
			clipboard_violation(s, "CLIPBOARD_TEXT carries %zu bytes and announcement "
			                 "%u declared %u (§7.4)",
			              byte, xform, s->app_peer_len);
			return false;
		}
		/* ⛔ §5.4: «the text MUST be valid UTF-8».  ⚠ And it is validated HERE,
		 *    before letting it cross the process boundary: an invalid text
		 *    delivered to the compositor is a defect of OURS with the face of a
		 *    defect of the desktop. */
		if (!valid_utf8(text, byte)) {
			clipboard_violation(s, "CLIPBOARD_TEXT (transfer %u, %zu bytes) is not "
			                 "valid UTF-8, and §5.4 demands it",
			              xform, byte);
			return false;
		}
		/* ⛔⭐ AND NO ZEROS IN THE MIDDLE — finding R9.11 applied to this channel.
		 *
		 *     `valid_utf8()` accepts it (`c < 0x80`), ⛔ but from here on the
		 *     text crosses a process boundary and reaches `clipboard.c`, which
		 *     delivers it to the compositor.  ⚠ And the OPPOSITE direction
		 *     already refuses it (`clipboard.c`, `read_text`): accepting it
		 *     here would mean two different rules for the same quantity in the
		 *     two directions, that is a text that can be pasted into the desktop
		 *     and cannot be copied from inside.
		 * ⚠ And `printable_text()` is NOT used, which would be the «ready
		 *   made» function: it also refuses `\n` and `\t`, ⛔ that is it would
		 *   refuse **any text copied from an editor**.  The right rule is
		 *   stricter than UTF-8 and wider than «printable». */
		if (memchr(text, 0, byte)) {
			clipboard_violation(s, "CLIPBOARD_TEXT (transfer %u, %zu bytes) carries "
			                 "a zero in the middle: what would be pasted "
			                 "would be shorter than what the announcement promised",
			              xform, byte);
			return false;
		}

		s->app_received++;
		clipboard_serve_pending(s, text, byte);
		return true;
	}

	default:
		/* ⛔ §7.4 defines THREE, and the high byte has already been recognised
		 *    as `0x02`: here we are on a clipboard channel type that does not
		 *    exist.  §3: it is not ignored. */
		clipboard_violation(s, "type %#06x on the clipboard channel: §7.4 defines THREE "
		                 "— 0x0201 ANNOUNCE, 0x0202 ASK, 0x0203 TEXT",
		              kind);
		return false;
	}
}

/* The slot of this stream in the table, creating it if needed.  NULL = there
 * is no slot, and the caller has already sent the client away. */
static int clipboard_slot(rcp_session *s, int64_t stream)
{
	int free_slot = -1;

	for (int i = 0; i < A_STREAM_MAX; i++)
		if (s->app_in[i].used && s->app_in[i].stream == stream)
			return i;
	for (int i = 0; i < A_STREAM_MAX; i++)
		if (!s->app_in[i].used) {
			free_slot = i;
			break;
		}
	/* ⛔ Full: the first one WITHOUT pending bytes is thrown away — an open and
	 *    empty stream takes nothing away from anyone — and ⛔ it is written to
	 *    the log, because §3 wants every tolerance to be visible. */
	if (free_slot < 0)
		for (int i = 0; i < A_STREAM_MAX; i++)
			if (s->app_in[i].head_n == 0 && !s->app_in[i].body) {
				reg(s, "⚠ CLIPBOARD: %d streams open at once (§2.5 wants one "
				       "per transfer): I let go of %lld, which had no "
				       "pending bytes",
				    A_STREAM_MAX, (long long)s->app_in[i].stream);
				free_slot = i;
				break;
			}
	if (free_slot < 0) {
		/* ⛔ All halfway through a message: it is a client that opens streams and
		 *    does not finish them, and it is no longer a tolerance — it is §3. */
		clipboard_violation(s, "%d clipboard streams open together and all halfway "
		                 "through a message: §2.5 wants one per transfer",
		              A_STREAM_MAX);
		return -1;
	}

	if (s->app_in[free_slot].body)
		explicit_bzero(s->app_in[free_slot].body, s->app_in[free_slot].lung);
	free(s->app_in[free_slot].body);
	memset(&s->app_in[free_slot], 0, sizeof s->app_in[free_slot]);
	s->app_in[free_slot].used = true;
	s->app_in[free_slot].stream = stream;
	return free_slot;
}

static void clipboard_slot_free(rcp_session *s, int i)
{
	if (s->app_in[i].body)
		explicit_bzero(s->app_in[i].body, s->app_in[i].lung);
	free(s->app_in[i].body);
	memset(&s->app_in[i], 0, sizeof s->app_in[i]);
}

bool rcp_receive_clipboard(rcp_session *s, int64_t stream, const uint8_t *data,
                        size_t len, bool fin, uint64_t now)
{
	int i;

	if (!s)
		return false;
	if (s->state == S_FINISHED) {
		reg(s, "⛔ %zu bytes on clipboard stream %lld AFTER the end of the "
		       "session from %s: §4.2 forbids sending on any channel",
		    len, (long long)stream, s->provenance);
		return false;
	}

	/* ⛔ §2.5, like input: nothing before `SESSION` has gone out. */
	if (!s->session_sent) {
		clipboard_violation(s, "bytes on the clipboard stream (%lld) before "
		                 "`SESSION` has gone out (state: %s)",
		              (long long)stream, STATE_NAMES[s->state]);
		return false;
	}

	/* ⛔ §4.3: the client did not declare `clipboard.text`, and now it sends some.
	 *    ⚠ It is NOT a tolerance: it is a non-negotiated capability used all
	 *    the same, that is the case §4.3 exists to make impossible. */
	if (!s->negotiate_clipboard) {
		clipboard_violation(s, "bytes on the clipboard channel from a client that "
		                 "did not declare `clipboard.text` in `HELLO` (§4.3)");
		return false;
	}

	/* ⛔ The sign of life only: the clipboard is NOT user input for the
	 *    30-minute clock (see `DEFAULT_INACTIVITY`) — the page announces by
	 *    itself, and a real paste on the desktop is a `KEY_POSITION`. */
	s->last_life = now;
	if (!speak_again(s))
		return false;

	i = clipboard_slot(s, stream);
	if (i < 0)
		return false;

	while (len) {
		/* First the six framing bytes (§6.1), and one at a time if needed:
		 * a packet can cut them in the middle. */
		if (s->app_in[i].head_n < 6) {
			size_t missing = 6 - s->app_in[i].head_n;
			size_t amount = len < missing ? len : missing;

			memcpy(s->app_in[i].head + s->app_in[i].head_n, data, amount);
			s->app_in[i].head_n += amount;
			data += amount;
			len -= amount;
			if (s->app_in[i].head_n < 6)
				break;

			{
				reader hdr = {s->app_in[i].head, 6, 0, false};
				uint16_t kind = le_u16(&hdr);
				uint32_t lung = le_u32(&hdr);
				uint32_t min_wait, max_wait;

				/* ⛔ §2.5: on this stream the high byte is 0x02. */
				if ((kind >> 8) != 0x02) {
					clipboard_violation(s, "type %#06x on the clipboard stream: the "
					                 "high byte 0x%02x is not the clipboard channel "
					                 "(§2.5)",
					              kind, (unsigned)(kind >> 8));
					return false;
				}
				/* ⛔ The length is validated BEFORE allocating — §6.1, and on the
				 *    three types of §7.4 one already knows what to expect: two have
				 *    a fixed size and the third has a minimum and a ceiling.
				 * ⭐ So whoever announces a megabyte on a `ASK` does not get
				 *    a megabyte: it gets six bytes and a farewell. */
				switch (kind) {
				case T_CLIPBOARD_ANNOUNCE:
					min_wait = max_wait = A_ANNOUNCEMENT;
					break;
				case T_CLIPBOARD_ASK:
					min_wait = max_wait = A_ASK;
					break;
				case T_CLIPBOARD_TEXT:
					min_wait = A_TEXT_MIN;
					max_wait = A_TEXT_MIN + RCP_CLIPBOARD_CAP;
					break;
				default:
					clipboard_violation(s, "type %#06x on the clipboard channel: §7.4 "
					                 "defines THREE — 0x0201 ANNOUNCE, 0x0202 "
					                 "ASK, 0x0203 TEXT",
					              kind);
					return false;
				}
				if (lung < min_wait || lung > max_wait) {
					clipboard_violation(s, "message %#06x announces %u body bytes "
					                 "and §7.4 wants between %u and %u: %s",
					              kind, lung, min_wait, max_wait,
					              lung < min_wait
					                  ? "MISSING bytes"
					                  : "EXTRA bytes — and beyond the ceiling of §5.4 "
					                    "the text is not announced at all");
					return false;
				}
				s->app_in[i].kind = kind;
				s->app_in[i].lung = lung;
				s->app_in[i].body_n = 0;
				if (lung) {
					s->app_in[i].body = (uint8_t *)malloc(lung);
					if (!s->app_in[i].body) {
						reg(s, "⛔ CLIPBOARD: %u bytes of body do not fit in "
						       "memory: I throw the message away and close the stream",
						    lung);
						clipboard_slot_free(s, i);
						return true;
					}
				}
			}
		}

		/* Then the body. */
		{
			size_t missing = s->app_in[i].lung - s->app_in[i].body_n;
			size_t amount = len < missing ? len : missing;

			if (amount) {
				memcpy(s->app_in[i].body + s->app_in[i].body_n, data, amount);
				s->app_in[i].body_n += amount;
				data += amount;
				len -= amount;
			}
			if (s->app_in[i].body_n < s->app_in[i].lung)
				break;
		}

		{
			uint16_t kind = s->app_in[i].kind;
			uint32_t lung = s->app_in[i].lung;
			uint8_t *body = s->app_in[i].body;
			bool alive;

			/* ⛔ The slot is reset BEFORE handling the message: `tratta_
			 *    clipboard` can send (and so re-enter this module), and a slot
			 *    left half full would be a state nobody knows any more whom it
			 *    belongs to.  ⚠ `body` stays valid: the memory is ours until
			 *    we free it three lines further down. */
			s->app_in[i].body = NULL;
			s->app_in[i].body_n = 0;
			s->app_in[i].head_n = 0;
			s->app_in[i].lung = 0;

			alive = handle_clipboard(s, kind, body, lung);
			if (body)
				explicit_bzero(body, lung);
			free(body);
			if (!alive)
				return false;
		}
	}

	/* ⛔ §6.1 and §2.5: a stream that ends halfway through a message does not
	 *    carry a short message — it carries a length that does not add up.
	 *    ⚠ And here the client is NOT sent away: the half message has not done
	 *    anything yet, and closing the session for a truncated stream would also
	 *    punish the client whose network dropped halfway through a transfer.
	 *    ⇒ It is declared and thrown away — and it is a WRITTEN tolerance (§3). */
	if (fin) {
		if (s->app_in[i].head_n || s->app_in[i].body)
			reg(s, "⚠ CLIPBOARD: stream %lld ended with a message halfway "
			       "(%zu header bytes, %zu of body out of %u): it is thrown away.  "
			       "I do not send the client away — a truncated transfer is not a "
			       "client making a mistake",
			    (long long)stream, s->app_in[i].head_n, s->app_in[i].body_n,
			    s->app_in[i].lung);
		clipboard_slot_free(s, i);
	}
	return true;
}

/* ⏳ §13.5 — the pending value reaches the child when the window of
 *    `RCP_PACE_GAP_MS` since the last one has passed.  ⛔ It never closes for
 *    frequency: a reliable stream can hand over in one packet two messages
 *    sent a second apart. */
static void pace_flush(rcp_session *s, uint64_t now)
{
	uint16_t v;

	if (!s->pace_has_pending)
		return;
	if (s->pace_ever_sent && now - s->pace_sent_ms < RCP_PACE_GAP_MS)
		return;
	s->pace_has_pending = false;
	v = s->pace_pending;
	if (v == s->pace_in_force)
		return;
	/* ⚠ The window starts now even if the hook fails: a stage that cannot be
	 *   reached must not cost one log line per message. */
	s->pace_sent_ms = now;
	s->pace_ever_sent = true;
	if (!s->g.pace || !s->g.pace(s->g.ctx, v)) {
		reg(s, "⚠ PACE %u/s from %s did NOT reach the stage: the rate stays "
		       "%s", (unsigned)v, s->user,
		    s->pace_in_force ? "at the previous ceiling" : "without a ceiling");
		return;
	}
	/* ⛔ I1: every drop of the rate is declared, with the number that
	 *    decided it — here it is the CLIENT's number, and the line says so. */
	if (v)
		reg(s, "⏳ PACE (§13): %s's decoder is behind ⇒ at most %u frames/s "
		       "(before: %s%u).  %u PACE received, %u superseded inside %u ms",
		    s->user, (unsigned)v, s->pace_in_force ? "" : "no ceiling, ",
		    (unsigned)s->pace_in_force, s->pace_received, s->pace_superseded,
		    RCP_PACE_GAP_MS);
	else
		reg(s, "⏳ PACE (§13): %s's decoder has caught up ⇒ the ceiling of "
		       "%u frames/s is LIFTED.  %u PACE received, %u superseded",
		    s->user, (unsigned)s->pace_in_force, s->pace_received,
		    s->pace_superseded);
	s->pace_in_force = v;
}

static bool handle_pace(rcp_session *s, reader *l, uint64_t now)
{
	uint16_t asked = le_u16(l);
	uint16_t v;

	if (l->too_short) {
		dismiss(s, RCP_PROTOCOL_ERROR, "PACE without `max_fps`");
		return false;
	}
	/* ⛔ Like `REQUEST_KEY`: there is no frame to pace before `SESSION`. */
	if (!s->session_sent) {
		dismiss(s, RCP_PROTOCOL_ERROR, "PACE before SESSION: there is no frame");
		return false;
	}
	s->pace_received++;
	v = rcp_pace_clamp(asked);
	if (s->pace_has_pending)
		s->pace_superseded++;
	s->pace_pending = v;
	s->pace_has_pending = true;
	pace_flush(s, now);
	return true;
}

/* ⛔ §5.2 and §7.1 — `REQUEST_KEY`, served since 12 Aug 2026.
 *
 * ⚠ Until today this type fell into the `default` of the switch and made a
 *   conforming client that had seen a gap **lose the session**: the log
 *   declared it («phase 1 does not needs it yet»), and the price was
 *   declared but real.  With the video channel that price can no longer be
 *   paid, because §5.2 obliges the client to send it.
 *
 * ⛔ And the CLOCK COUNTS FROM THE LAST KEYFRAME SENT, not from the last request
 *    received: «counting from requests, two insistent clients push the clock
 *    forward forever and the keyframe never leaves».                        */
static bool handle_key_request(rcp_session *s, reader *l, uint64_t now)
{
	uint32_t last = le_u32(l);
	if (l->too_short) {
		dismiss(s, RCP_PROTOCOL_ERROR,
		        "REQUEST_KEY without `last_number`");
		return false;
	}
	/* §5.2: it is served only with the session open — before there are no
	 * frames to notice anything about. */
	if (!s->session_sent) {
		dismiss(s, RCP_PROTOCOL_ERROR,
		        "REQUEST_KEY before SESSION: there is no frame");
		return false;
	}
	/* ⛔ §7.1: «`last_number`: the last decoded frame, **0 if
	 * none**».  It is the meaning P2 reserved for zero in §6.2: here it is
	 * read, not guessed. */
	/* ⛔⛔ 22 Sep 2026 — THE GRACE IS FOR DUPLICATES, not for new gaps.
	 *     A request with `last_number` equal to or newer than the last
	 *     keyframe sent says the client has ALREADY decoded that keyframe: the
	 *     gap came afterwards, and ignoring it leaves it frozen forever (the
	 *     page does not ask for a second one for the same gap).
	 *     `[M]` Firefox on KDE, heavy video: «ignored — 157 ms» with
	 *     `last_number` = the keyframe just arrived, and the page frozen
	 *     until the line died.  ⚠ Comparison in serial-number arithmetic: the
	 *     `nr` of §6.2 wraps around. */
	bool already_seen = (int32_t)(last - s->last_key_number) >= 0;
	if (!s->never_sent_key && !already_seen &&
	    now - s->last_key_ms < V_GRACE_KEY) {
		/* ⛔ §3: «every tolerance must be written to the log.  A silent
		 * tolerance is indistinguishable from a defect».  It is exception 5. */
		reg(s, "⚠ DECLARED TOLERANCE (§3 exception 5, §5.2): "
		       "REQUEST_KEY(last_number=%u) ignored — %llu ms have "
		       "passed since the last KEYFRAME sent, fewer than the %d allowed",
		    last, (unsigned long long)(now - s->last_key_ms),
		    V_GRACE_KEY);
		return true;
	}
	reg(s, "REQUEST_KEY(last_number=%u) accepted (§5.2): the next "
	       "frame will be a KEYFRAME — last one sent by us: %u",
	    last, s->video_number);
	key_needed(s, "the client asked for one (§5.2)");
	return true;
}

/* ------------------------------------------------------------------------ */
#ifdef REMOTIX_BENCH
/* ⭐ §7.5 — THE BENCH FUNCTION, AND THE CASE THAT MUST NOT BRING ANYTHING DOWN
 *
 * ⛔ This is the only control channel message to which a conforming server
 *    answers **by refusing without closing**.  The two rules:
 *
 *    rule 2    off -> `BENCH_OUTCOME(REFUSED, FEATURE_OFF)`.  ⛔ It MUST
 *              NOT stay silent and MUST NOT close: «a client asking for a
 *              function that is off has violated nothing», and a silence leaves
 *              the phase 3 bench waiting forever — the symptom would be
 *              «the bench got stuck», which names neither the function nor
 *              the switch;
 *    rule 4    `delay_ms` outside 0..10 000 -> `DELAY_OUT_OF_RANGE`, and
 *              ⛔ **not** `PROTOCOL_ERROR`: bringing down the session of the
 *              bench being calibrated is the same bad idea §7.1 avoids for
 *              out-of-limit sizes.
 *
 * ⚠ And the ORDER between the two `RCP.md` does not say: with the function off
 *   AND the delay out of limits, the defensible reasons are two.  ⭐ Here the
 *   parameter is checked FIRST, because it is the one the bench can correct:
 *   telling it «off» when it also got the number wrong makes it switch the
 *   function on and find the same refusal, with a different reason, at the
 *   second round.  The choice is declared in `PHASES.md` §01-filo-nudo.
 *
 * ⛔ Rule 5: every `BENCH_MARK` is written to the log — refusals too.
 *    «A session that paints coloured squares on a person's desktop must be
 *    able to prove it from the log.» */
static bool handle_bench_mark(rcp_session *s, reader *l)
{
	uint32_t id = le_u32(l), color = le_u32(l), delay = le_u32(l);
	if (l->too_short) {
		dismiss(s, RCP_PROTOCOL_ERROR, "BENCH_MARK truncated");
		return false;
	}
	/* ⛔ §7.5: «0 is reserved».  A zero id is not a wrong bench parameter,
	 * it is a malformed message: here the session drops.
	 * ⚠ Our choice — the document says «reserved» and does not say the outcome. */
	if (id == 0) {
		dismiss(s, RCP_PROTOCOL_ERROR, "BENCH_MARK with id 0, which is reserved");
		return false;
	}

	uint8_t outcome = BENCH_REFUSED, reason;
	if (delay > BENCH_DELAY_MAX) {
		reason = BENCH_DELAY_OUT_OF_RANGE;
	} else if (!BENCH_ON) {
		reason = BENCH_FEATURE_OFF;
	} else {
		/* In phase 1 there is no frame to paint on: the function stays off,
		 * and this branch exists so as not to forget that switching it on
		 * must be written to the log (rule 5). */
		outcome = BENCH_ACCEPTED;
		reason = 0;
	}
	reg(s, "BENCH_MARK id=%u color=%#08x delay=%u ms -> %s reason=%u",
	    id, color, delay,
	    outcome == BENCH_ACCEPTED ? "ACCEPTED" : "REFUSED", reason);

	uint8_t body[32];
	writer w = {body, sizeof body, 0, false};
	sc_u32(&w, id);
	sc_byte(&w, outcome);
	sc_byte(&w, reason);
	/* ⛔ `instant`: 0 if refused, «and it is the only meaning of *absent*
	 * for this field» (§6.0). */
	for (int i = 0; i < 8; i++)
		sc_byte(&w, 0);
	if (!w.full)
		send_message(s, T_BENCH_OUTCOME, body, w.len);
	/* ⭐ And the session STAYS OPEN. */
	return true;
}

#endif /* REMOTIX_BENCH */

/* ------------------------------------------------------------------------ */
rcp_session *rcp_open(const rcp_hooks *g, const char *provenance,
                       uint64_t now_ms)
{
	rcp_session *s = (rcp_session *)calloc(1, sizeof *s);
	if (!s)
		return NULL;
	s->g = *g;
	s->state = S_WAIT_HELLO;
	s->since = now_ms;
	s->last_input = now_ms;
	/* ⛔ And THIS too starts from now, not from zero: a session just
	 *    opened has not yet seen a packet pass through the hands of this
	 *    module, and a zero would make it detach for silence at the first round. */
	s->last_life = now_ms;
	snprintf(s->provenance, sizeof s->provenance, "%s",
	         provenance ? provenance : "?");
	rcp_key_address(s->provenance, s->address, sizeof s->address);
	reg(s, "control channel opened from %s (address for §4.4-bis: %s)",
	    s->provenance, s->address);
	/* ⛔ §7.5 rule 5 and §4.3: «a server that declared it `yes` by mistake
	 * writes it to the log at every startup».  This module has no startup — it
	 * opens no socket and reads no configuration — and the first moment it sees
	 * is the opening of a channel: the line sits here (finding R9.14).  ⚠ Whoever
	 * diagnoses a coloured square on someone's desktop must be able to trace
	 * back to the line saying the function was on. */
#ifdef REMOTIX_BENCH
	if (BENCH_ON)
		reg(s, "⛔ the BENCH FUNCTION is ON (§7.5): this server accepts "
		       "BENCH_MARK and paints over the desktop, and `HERE_I_AM` declares "
		       "bench.mark=yes");
#endif
	return s;
}

void rcp_free(rcp_session *s)
{
	if (!s)
		return;
	/* ⛔ §7.3 — the last of the roads, and the safety net of all the others:
	 * whatever happened, one passes through here.  ⚠ `inp_released` alone
	 * prevents releasing twice. */
	release_on_detach(s, "the session is being freed");
	/* ⏳ §13.5 — the ceiling belongs to the SESSION: it is lifted with it, or
	 *    the next client of this user would inherit a slow desktop. */
	if (s->pace_in_force && s->g.pace) {
		s->g.pace(s->g.ctx, 0);
		reg(s, "⏳ PACE (§13): the session ends, the ceiling of %u frames/s is "
		       "LIFTED", (unsigned)s->pace_in_force);
		s->pace_in_force = 0;
	}
	/* ⛔ §6.2 — A VIDEO STREAM LEFT HALFWAY IS RESET, NOT ABANDONED TO THE
	 * TRANSPORT.  A frame open when the session ends is by definition
	 * incomplete: resetting it says so, and it is the only closing that means
	 * «throw it away».  ⚠ And one goes through the hook, not through
	 * `rcp_video_abandon()`: that one refuses keyframes (§5.2) and is right
	 * while the session lives — here there is nothing left to protect, and a
	 * keyframe left open would stay open forever. */
	if (s->video_is_open && s->g.video_reset) {
		s->g.video_reset(s->g.ctx, s->video_stream);
		s->video_is_open = false;
		reg(s, "⚠ frame %u was still open at the end of the session: "
		       "stream %lld RESET (§6.2), %zu bytes out of %zu",
		    s->video_its_number, (long long)s->video_stream, s->video_written,
		    s->video_to_write);
	}
	if (s->is_attached) {
		slot_leave(s->user);
		reg(s, "slot LEFT by %s via %s (taken now: %d)", s->user,
		    s->provenance, taken_slots());
	}
	/* ⛔ The buffer is zeroed BEFORE freeing it — finding R9.8.  The
	 * `CREDENTIALS` passed through it, and on every road that sends the client
	 * away before consuming the message the password in clear is still there.
	 * `free()` zeroes nothing: those bytes ended up in the freed heap,
	 * available to any later allocation of a process that serves ALL the
	 * users of the machine (`SPECS.md` §5.5). */
	if (s->acc) {
		explicit_bzero(s->acc, s->acc_cap);
		free(s->acc);
	}
	/* ⛔⭐ AND THE CLIPBOARD IS FREED HERE, both sides.
	 *
	 * ⛔ And it is ZEROED first, like the buffer and for a reason of the same
	 *    family: what the user copies is often precisely what they would not
	 *    want to leave lying around — a password pasted from a credential
	 *    manager passes **whole** through this buffer.  ⚠ `free()` zeroes
	 *    nothing, and this process serves ALL the users of the machine
	 *    (`SPECS.md` §5.5). */
	if (s->app_text) {
		explicit_bzero(s->app_text, s->app_text_n);
		free(s->app_text);
	}
	for (int i = 0; i < A_STREAM_MAX; i++)
		if (s->app_in[i].body) {
			explicit_bzero(s->app_in[i].body, s->app_in[i].lung);
			free(s->app_in[i].body);
		}
	memset(s, 0, sizeof *s);
	free(s);
}

bool rcp_is_finished(const rcp_session *s) { return s && s->state == S_FINISHED; }

/* ⭐ Past the fixed second with a «yes» (`ADMITTED` sent): the session is a
 *    login, not a knock.  Before it the name is only what the client CLAIMED
 *    at `CREDENTIALS`, and nothing may be said about that account (§4.4). */
bool rcp_logged_in(const rcp_session *s)
{
	return s && s->state >= S_WAIT_ATTACH && s->state != S_FINISHED;
}

/* ⛔⭐ §4.2 — THE SESSION IS OVER BECAUSE THE CLIENT SAYS SO, AND THE SLOT IS
 * LEFT NOW, NOT WHEN THE TRANSPORT HAS FINISHED TAKING ITSELF DOWN.
 *
 * The client closes the WebTransport session with a capsule carrying the
 * reason (§3.1 point 3).  ⚠ Waiting for the streams to close before freeing the
 * slot (§8.2 reason 0x0F) means keeping it taken for the whole time of the
 * teardown — and whoever reconnects **at once** is told there is already a
 * session.
 *
 * ⭐ Found by B11 on 10 Aug 2026: two consecutive cases, the second
 *    refused with `ALREADY_ACTIVE_REMOTELY` because the first had not yet finished
 *    leaving.  ⛔ On the bench it is a red case now and then; for whoever uses
 *    the product it is «it tells me I am already connected, and it is not true». */
void rcp_closed_by_client(rcp_session *s, uint8_t code)
{
	/* ⚠ No guard on the state: the slot is left even if the session had
	 *   already ended by another road — `is_attached` alone prevents leaving it
	 *   twice, and it is the only thing that matters. */
	if (!s)
		return;
	reg(s, "the page closed the session, reason %#04x: §4.2, the session "
	       "is over (state: %s)",
	    code, STATE_NAMES[s->state]);
	/* ⛔ §7.3: the third road — the page leaves without going through
	 * `dismiss()`.  A browser closed with the little cross arrives here. */
	release_on_detach(s, "the page closed the session");
	if (s->is_attached) {
		slot_leave(s->user);
		s->is_attached = false;
		reg(s, "slot LEFT by %s via %s (taken now: %d)", s->user,
		    s->provenance, taken_slots());
	}
	s->state = S_FINISHED;
}

bool rcp_awaits_verdict(const rcp_session *s, uint64_t ticket)
{
	/* the walls of `rcp_verdict()`: alive, in wait-verdict, asked, its own number */
	return s && s->state == S_WAIT_VERDICT && s->expected_verdict &&
	       s->ticket == ticket;
}

const char *rcp_state_name(const rcp_session *s)
{
	return s ? STATE_NAMES[s->state] : "?";
}

const char *rcp_user(const rcp_session *s) { return s ? s->user : ""; }

/* ⛔⭐ THE DECODER CEILING, BROUGHT OUTSIDE — phase 10, 25 Aug 2026.
 *
 *     `max_l`/`max_a` had existed since 10 August (finding B-1) and served ONE
 *     thing only: not granting a canvas the client cannot decode
 *     (§4.5).  ⭐ The budget needs them for another: it is the **upper bound of
 *     the cost** of whoever is knocking, and it is known from `HELLO` on — that
 *     is long before the canvas is decided.  ⇒ No new field, no new channel:
 *     only an accessor.
 *
 * ⚠ `false` = «the client did not declare it», and it is a fact different from
 *   «zero» (§4.5 constrains the granted canvas **only if the client declared it**). */
bool rcp_max_size(const rcp_session *s, uint32_t *l, uint32_t *a)
{
	if (!s || !s->max_l || !s->max_a)
		return false;
	if (l)
		*l = s->max_l;
	if (a)
		*a = s->max_a;
	return true;
}

/* ⛔⭐ §5.3 — «THE CLIENT IS STILL THERE», and the TRANSPORT says so, not RCP.
 *
 *     `transport.c` calls it after every packet `ngtcp2_conn_read_pkt()`
 *     has accepted: that is **decrypted and authenticated**.  ⛔ It is not
 *     enough for a UDP datagram to arrive — anyone can send one with someone
 *     else's address, and would keep someone else's slot taken.
 *
 * ⭐ It is the only sign of life that exists when the user watches and does not
 *    touch, and it is the RIGHT one: in the test of 16 August the wire was cut at
 *    13:33:13 and this clock declared it at 13:33:43 — **thirty seconds
 *    flat**, while the RCP bytes clock had declared it 36 seconds EARLIER, and
 *    wrongly.
 *
 * ⚠ No new message, no heartbeat to add to the page: the signal was already
 *   there and nobody passed it through here. */
void rcp_sign_of_life(rcp_session *s, uint64_t now_ms)
{
	if (!s || s->state == S_FINISHED)
		return;
	/* ⛔⭐⭐ AND THE GAP BETWEEN TWO PACKETS IS WATCHED, because this repair
	 *      RESTS ON AN ASSUMPTION: that between one packet and the next less
	 *      than the ceiling of §5.3 passes.
	 *
	 * ⛔ Nobody guarantees it.  The transport PINGs are on ONLY in the
	 *    credentials window, and for a written reason (`webtransport.c`,
	 *    `keepalive_rule()`: keeping them always on would change the
	 *    meaning of the 30 s of §2.2).  ⇒ During the session packets arrive
	 *    because SOMETHING moves — frames, cursor, acknowledgements — and on a
	 *    still scene with nobody touching anything it is not certain that
	 *    something moves often enough.
	 *
	 * ⚠ So when the gap exceeds HALF the ceiling it is WRITTEN.  It is the only
	 *   way to see the day COMING when it is no longer enough, instead of
	 *   discovering it from a user thrown out while reading — that is not to
	 *   redo, in the cure, the defect the cure came to remove: a protection
	 *   resting on something nobody can look at.
	 *
	 * ⛔⭐ `[M]` AND AT THE FIRST RUN THIS LINE ALREADY SPOKE, 16 Aug 2026:
	 *      session still for 260 s, the slot held — ⛔ but the gap between two
	 *      packets is **15004, 15005, 15002 ms**, that is EXACTLY FIFTEEN
	 *      SECONDS, a clean half of the ceiling.
	 *
	 *      ⇒ The margin is 2x, and it is very regular because it is NOT OURS: it
	 *      is the browser's keep-alive.  ⚠ A different browser, or Chrome
	 *      changing that number, and slots start dropping again.  ⛔ The real
	 *      cure — sending PINGs even with the session active — is a DECISION,
	 *      not a repair: it changes the meaning of the 30 s of §2.2 for the
	 *      FROZEN tab, which `SPECS.md` §5.3 says must be detached.  It is
	 *      written in `PHASES.md` §05-la-sessione §6-bis and waits for the user. */
	if (now_ms > s->last_life && now_ms - s->last_life > SILENCE / 2)
		reg(s, "⚠ §5.3: between two packets from %s %llu ms have passed, and the "
		       "silence ceiling is %u — the margin is getting thin",
		    s->provenance, (unsigned long long)(now_ms - s->last_life),
		    (unsigned)SILENCE);
	s->last_life = now_ms;
}

/* ⛔ The buffer grows on demand up to the ceiling of §6.1 (see MAX_ACCUMULATION).
 *
 * ⚠ And `realloc` is NOT used: that buffer contains the `CREDENTIALS` in clear,
 *   and a `realloc` that moves leaves the old copy in the heap without zeroing
 *   it — that is it would put back the defect R9.8 came to remove.  One
 *   allocates, copies, ZEROES the old one, frees.
 *
 * Returns: 1 done · 0 does not fit (the caller sends the client away) · -1 memory. */
static int accumulate(rcp_session *s, const uint8_t *data, size_t n)
{
	if (s->acc_len + n > MAX_ACCUMULATION)
		return 0;
	if (s->acc_len + n > s->acc_cap) {
		size_t new_one = s->acc_cap ? s->acc_cap : 8192u;
		while (new_one < s->acc_len + n)
			new_one *= 2;
		if (new_one > MAX_ACCUMULATION)
			new_one = MAX_ACCUMULATION;
		uint8_t *p = (uint8_t *)malloc(new_one);
		if (!p)
			return -1;
		if (s->acc) {
			memcpy(p, s->acc, s->acc_len);
			explicit_bzero(s->acc, s->acc_cap);
			free(s->acc);
		}
		s->acc = p;
		s->acc_cap = new_one;
	}
	memcpy(s->acc + s->acc_len, data, n);
	s->acc_len += n;
	return 1;
}
/* ⛔⭐ HOW LONG THE FIELDS OF THIS TYPE ARE — finding R9.4, and the defect was
 *    the ORDER, not the check.
 *
 * §6.1: «a receiver that reads a length inconsistent with what the type
 * foresees MUST close with `PROTOCOL_ERROR`», and §3: «MUST NOT carry on».
 * The check `l.i != lung` was there, and it was written right — but it sat AFTER
 * `keep_going = tratta_*()`, that is after the message had been executed in
 * full, with all its effects on the wire and on the state:
 *
 *   a `HELLO` with four padding bytes at the tail — the
 *   `lunghezza-in-piu` case of B5 — received `HERE_I_AM` and ONLY THEN the farewell;
 *   an `ATTACH` with one byte at the tail took the slot, sent `SESSION`,
 *   wrote «session open» and then sent the client away: on the wire, in this
 *   order, `SESSION` and `FAREWELL(0x0B)`.  ⛔ A client that has received
 *   `SESSION` is authorised by §2.5 to open its input stream, and it opened it
 *   on a session that was dying;
 *   a `CREDENTIALS` with one byte at the tail made PAM be queried and MOVED the
 *   counters of §4.4-bis — that is precisely the property B5 checks with
 *   `malformati-non-contano`, and it checked it on the other half of the
 *   malformed ones.
 *
 * ⚠ This function is a SECOND reader of the same fields, and the two can
 *   drift apart: whoever changes a body in `tratta_*()` changes it here too.  The
 *   check that remains AFTER the switch is not a duplicate — it is what
 *   notices.
 *
 * ⭐ And it returns `false` when the body is SHORTER than the fields: that case
 *    it leaves to `tratta_*()`, which can say which field was missing.  §3.1
 *    point 1 wants «what» was not understood, and «HELLO without version» is worth
 *    more than «the length does not add up». */
static bool measure_fields(uint16_t kind, const uint8_t *body, uint32_t lung,
                         size_t *amount)
{
	reader l = {body, lung, 0, false};
	char buf[1025];
	switch (kind) {
	case T_HELLO: {
		le_u16(&l);
		uint16_t how_many = le_u16(&l);
		for (uint16_t k = 0; k < how_many && !l.too_short; k++) {
			le_str(&l, buf, sizeof buf);
			le_str(&l, buf, sizeof buf);
		}
		break;
	}
	case T_CREDENTIALS:
		le_str(&l, buf, sizeof buf);
		le_str(&l, buf, sizeof buf);
		break;
	case T_ATTACH:
		le_u32(&l);
		le_u32(&l);
		le_u32(&l);
		le_u32(&l);
		le_str(&l, buf, sizeof buf);
		break;
#ifdef REMOTIX_BENCH
	case T_BENCH_MARK:
		le_u32(&l);
		le_u32(&l);
		le_u32(&l);
		break;
#endif
	case T_FAREWELL:
		le_u8(&l);
		le_str(&l, buf, sizeof buf);
		break;
	/* §7.1: `REQUEST_KEY` ├── u32 last_number.  Four bytes, and not one
	 * more: a longer body is `PROTOCOL_ERROR` as for the others
	 * (§6.1), and this line is what makes it happen. */
	case T_REQUEST_KEY:
		le_u32(&l);
		break;
	/* ⏳ §13: `PACE` ├── u16 max_fps.  Two bytes, not one more. */
	case T_PACE:
		le_u16(&l);
		break;
	/* ⭐ §7.6: `TERMINATE_SESSION` has an EMPTY body — there is nothing to say
	 * beyond the fact.  ⚠ And a longer body is `PROTOCOL_ERROR` as for
	 * all the others (§6.1): not «whatever is left over is ignored». */
	case T_TERMINATE_SESSION:
		break;
	/* ⛔⭐⭐ `FIT_CANVAS` AND `VIEW` — two `u32` each (§7.1), and BOTH were
	 *      MISSING: 16 Aug 2026, bench `06-b36` case 20.
	 *
	 * ⚠ It is **R9.4 again**, on the most recent message: the comment at the top
	 *   of this function tells the defect — «an `ATTACH` with one byte at the
	 *   tail took the slot, sent `SESSION` and THEN sent the client away» — and
	 *   `FIT_CANVAS`, served on 14 August, never entered the list.
	 *
	 * ⛔ The price `[M]`: a 12-byte `FIT_CANVAS` fell into the `default`,
	 *    this function returned `false` (that is «I do not judge it»), the
	 *    `T_FIT_CANVAS` branch passed the request to the stage **in full** and
	 *    only the check `l.i != lung` AFTER the switch sent the client away.  ⇒
	 *    On the wire a `CANVAS` and then a `FAREWELL`, and on the compositor a real
	 *    resize — which restarts the PipeWire stream and on Mutter destroys and
	 *    recreates the `libei` devices.  §3: «MUST NOT carry on».
	 *
	 * ⚠ `VIEW` comes in here together because it comes into the switch
	 *   together: whoever adds a type and does not add its line here reopens the
	 *   same hole. */
	case T_FIT_CANVAS:
	case T_VIEW:
		le_u32(&l);
		le_u32(&l);
		break;
	default:
		/* a type we will not get to handle anyway: the switch decides, and
		 * its log line is more precise than this one */
		return false;
	}
	if (l.too_short)
		return false;
	*amount = l.i;
	return true;
}

/* Has the wire stopped at the boundary between two messages?  It serves
 * `judge_after_end()`: if the server closed while a body was halfway,
 * the bytes arriving afterwards do NOT start with a header, and reading them
 * as such means giving a name to two body bytes. */
static bool a_confine(const rcp_session *s)
{
	if (s->acc_len == 0)
		return true;
	if (s->acc_len < 6)
		return false;
	reader l = {s->acc, s->acc_len, 0, false};
	le_u16(&l);
	uint32_t lung = le_u32(&l);
	return s->acc_len >= 6u + (size_t)lung;
}

/* ⛔⭐ AFTER THE END ONE JUDGES ON MESSAGES, NOT ON THE FIRST SIX BYTES OF THE
 *    PIECE — finding R9.15.
 *
 * §4.4 forbids the client ONE thing: **retrying**.  §8.1 imposes another:
 * whoever closes MUST send `FAREWELL` with the reason.  ⭐ The two meet when
 * the server errs AFTER `REJECTED` — the `respinto-poi-congedo` case of B11: the
 * page sees a message that should not have arrived, closes as §3 requires, and
 * its `FAREWELL` leaves when for us the session is already over.
 *
 * ⚠ On 10 Aug 2026 that 69-byte `FAREWELL` was counted as «sent after the
 *   end», and the red went to the page that was doing exactly what §8.1
 *   requires of it.  ⛔ The cure of that day however read **the first two bytes
 *   of `data`** and acquitted the WHOLE piece: whoever wrote in a single go
 *   `FAREWELL` **plus** a second `CREDENTIALS` walked away with the
 *   acquittal, and the violation B11 exists to accusations appeared in no line.
 *   The false red had become a false green, which is the same shape — and the
 *   document one relies on, §4.4, speaks of MESSAGES. */
static void judge_after_end(rcp_session *s, const uint8_t *data,
                                 size_t len)
{
	if (!a_confine(s)) {
		reg(s, "⚠ %zu bytes arrived AFTER the end of the session from %s, and they "
		       "CANNOT be judged: the wire had stopped halfway through a body, "
		       "so these bytes do not start with a header",
		    len, s->provenance);
		return;
	}
	size_t off = 0;
	int amount = 0;
	uint16_t first = 0;
	while (off + 6 <= len) {
		reader l = {data + off, len - off, 0, false};
		uint16_t kind = le_u16(&l);
		uint32_t lung = le_u32(&l);
		if (lung > MAX_BODY || (size_t)6 + lung > len - off)
			break; /* the last one is truncated: `off < len` will say so */
		if (amount == 0)
			first = kind;
		amount++;
		off += 6 + lung;
	}
	if (amount == 1 && first == T_FAREWELL && off == len) {
		reg(s, "⭐ parting FAREWELL from %s with the session already over: §8.1 "
		       "REQUIRES it of whoever closes, and §4.4 forbids attempts, not partings "
		       "— %zu bytes, a single message, and they are not too many",
		    s->provenance, len);
		return;
	}
	if (amount >= 1 && first == T_FAREWELL) {
		reg(s, "⛔ from %s a parting FAREWELL AND THEN something else: %d messages "
		       "in %zu bytes (%zu bytes beyond the last whole one).  §8.1 requires "
		       "the parting, §4.4 forbids everything else",
		    s->provenance, amount, len, len - off);
		return;
	}
	reg(s, "⛔ %zu bytes arrived AFTER the end of the session from %s: %d whole "
	       "messages, the first of type %#06x",
	    len, s->provenance, amount, first);
}

/* Extracts from the buffer all the whole messages that are there.  `false` = the
 * session is over, and the caller must not buffer anything else. */
static bool drain(rcp_session *s, uint64_t now)
{
	for (;;) {
		if (s->acc_len < 6)
			return true;
		reader hdr = {s->acc, s->acc_len, 0, false};
		uint16_t kind = le_u16(&hdr);
		uint32_t lung = le_u32(&hdr);
		/* ⛔ The length is checked BEFORE allocating: whoever allocates and then
		 * checks has already given a megabyte to anyone who can write six bytes. */
		/* ⛔ And the ceiling belongs to the MESSAGE, framing included (§6.1 read
		 * together with §5.4) — finding B-14: here `lung` is the BODY, and the
		 * longest body allowed is `MAX_MESSAGE - 6`. */
		if (lung > MAX_BODY) {
			dismiss(s, RCP_PROTOCOL_ERROR, "message over 1 MiB");
			return false;
		}
		if (s->acc_len < 6u + lung)
			return true; /* the body has not all arrived */

		/* §2.5: on the control channel the high byte of the type is 0x00. */
		if ((kind >> 8) != 0x00) {
			dismiss(s, RCP_PROTOCOL_ERROR, "high byte of the type is not control");
			return false;
		}
		/* ⛔ AND HERE, BEFORE ANY EFFECT: the declared length must be the one of
		 * the type's fields (§6.1).  See `measure_fields()`. */
		size_t wait = 0;
		if (measure_fields(kind, s->acc + 6, lung, &wait) && wait != lung) {
			char d[128];
			snprintf(d, sizeof d,
			         "type %#06x: the length declares %u bytes and the "
			         "fields the type expects take %zu",
			         kind, lung, wait);
			dismiss(s, RCP_PROTOCOL_ERROR, d);
			return false;
		}
		reader l = {s->acc + 6, lung, 0, false};
		bool keep_going = true;
		switch (kind) {
		case T_HELLO:
			if (s->state != S_WAIT_HELLO) {
				dismiss(s, RCP_PROTOCOL_ERROR, "HELLO in the wrong state");
				return false;
			}
			keep_going = handle_hello(s, &l);
			break;
		case T_CREDENTIALS:
			if (s->state != S_WAIT_CREDENTIALS) {
				dismiss(s, RCP_PROTOCOL_ERROR, "CREDENTIALS in the wrong state");
				return false;
			}
			keep_going = handle_credentials(s, &l, now);
			break;
		case T_ATTACH:
			if (s->state != S_WAIT_ATTACH) {
				dismiss(s, RCP_PROTOCOL_ERROR, "ATTACH in the wrong state");
				return false;
			}
			keep_going = handle_attach(s, &l, now);
			break;
#ifdef REMOTIX_BENCH
		case T_BENCH_MARK:
			/* §7.5: the mark is painted on a frame, and frames
			 * start with `SESSION`.  Before, it is a message in the wrong
			 * state like all the others. */
			if (s->state != S_ACTIVE) {
				dismiss(s, RCP_PROTOCOL_ERROR,
				        "BENCH_MARK in the wrong state");
				return false;
			}
			keep_going = handle_bench_mark(s, &l);
			break;
#endif
		case T_REQUEST_KEY:
			/* ⛔ §5.2: a keyframe is asked for because there is a gap between
			 * frames, and frames start with `SESSION`.  Before, it is a
			 * message in the wrong state like all the others (§1, §3).
			 * ⚠ `S_DETACHED` is fine: that session sent `SESSION` long
			 *   ago, it only left the slot for silence (R9.2) — and refusing
			 *   it a keyframe would be punishing the client for a ceiling
			 *   of the server. */
			if (s->state != S_ACTIVE && s->state != S_DETACHED) {
				dismiss(s, RCP_PROTOCOL_ERROR,
				        "REQUEST_KEY in the wrong state");
				return false;
			}
			keep_going = handle_key_request(s, &l, now);
			break;
		case T_PACE:
			/* ⏳ §13.3 — the same states as `REQUEST_KEY`, and only with the
			 *    capability negotiated on BOTH sides. */
			if (s->state != S_ACTIVE && s->state != S_DETACHED) {
				dismiss(s, RCP_PROTOCOL_ERROR, "PACE in the wrong state");
				return false;
			}
			if (!s->pace_declared || !s->pace_client) {
				dismiss(s, RCP_PROTOCOL_ERROR,
				        s->pace_declared
				            ? "PACE without video.pace=yes in the HELLO (§13.2)"
				            : "PACE, and this server did not declare video.pace "
				              "(§13.2)");
				return false;
			}
			keep_going = handle_pace(s, &l, now);
			break;
		case T_TERMINATE_SESSION:
			/*
			 * ⭐⭐ §7.6 — «I AM DONE», and it is the other exit of
			 *     `DECISIONS.md` §4.1-ter.
			 *
			 * ⛔ ONLY WITH THE SESSION ATTACHED: before `ATTACH` there is no
			 *    graphical session to end, and §3 makes no allowances.
			 * ⚠ `S_DETACHED` is fine for the same reason as
			 *   `REQUEST_KEY`: that client has the session, it only
			 *   left the slot for silence.
			 */
			if (s->state != S_ACTIVE && s->state != S_DETACHED) {
				dismiss(s, RCP_PROTOCOL_ERROR,
				        "TERMINATE_SESSION in the wrong state");
				return false;
			}
			reg(s, "⭐ §7.6: %s asked to LEAVE — the graphical session "
			       "ends and its programs close.  ⛔ It is NOT a "
			       "detach: at the next attach a NEW one will be born",
			    s->user);
			/*
			 * ⛔⛔ THE ORDER IS NORMATIVE, and it is not a preference: the farewell
			 *     FIRST, the request to end AFTER.  When the compositor falls
			 *     the stage falls with it and the channel is no longer
			 *     needed — a `0x10` sent afterwards is a reason that exists
			 *     and that nobody receives, that is finding B-7.
			 */
			dismiss(s, RCP_SESSION_TERMINATED,
			        "the user asked to leave the session");
			if (s->g.terminate_session)
				s->g.terminate_session(s->g.ctx);
			else
				reg(s, "⚠ no «terminate_session» hook: the client was "
				       "sent away with 0x10 but the graphical session was NOT "
				       "touched.  ⛔ The two truths do not match, "
				       "and this line is the only place where it shows");
			return false;
		case T_FAREWELL: {
			/* ⛔⭐ FOUR THINGS IN NINE LINES — finding R9.5.
			 *
			 *   1. `lung` was never looked at: `le_u8()` on an empty body
			 *      sets `too_short` and returns 0, and nobody read `too_short`;
			 *   2. that zero was PLUGGED (`reason ? reason : 0x01`): the
			 *      server INVENTED `CLOSED_BY_USER` for a reason the
			 *      client had not sent.  ⛔ The log wrote
			 *      `reason=0x00` and the session closed with `0x01`: two
			 *      truths about the same fact, which is the shape §3.1
			 *      point 3 exists for;
			 *   3. the `detail` was not read — neither as a string, nor as
			 *      UTF-8, nor as a length — and it is exactly what §8.2
			 *      assigns to the LOG;
			 *   4. the reason was sent back without validation inside the
			 *      session close code, where §3.1 point 3 wants «the code
			 *      of the reason OF §8.2».
			 *
			 * ⛔ And §3.1: «code 0 means closing without a reason and MUST
			 *    NOT be used».  A `FAREWELL(0x00)` is a violation by the
			 *    client, not a reason to guess — and it is the same case that
			 *    B11 demands of the PAGE when the one at fault is the server. */
			uint8_t reason = le_u8(&l);
			size_t p = l.i;
			char details[257];
			size_t ld = le_str(&l, details, sizeof details);
			if (l.too_short) {
				dismiss(s, RCP_PROTOCOL_ERROR,
				        "FAREWELL without reason or without detail");
				return false;
			}
			/* ⚠ The detail is validated on the BYTES THAT ARRIVED, not on the
			 *   copy: §7.1 puts no ceiling on it and `le_str` does not copy what
			 *   does not fit (see its comment).  So even a detail longer than
			 *   our field is judged instead of ignored. */
			if (!valid_utf8((const char *)(l.b + p + 2), ld)) {
				dismiss(s, RCP_PROTOCOL_ERROR,
				        "the FAREWELL detail is not valid UTF-8 (§6.0)");
				return false;
			}
			if (!reason_for_82(reason)) {
				char d[96];
				snprintf(d, sizeof d,
				         "FAREWELL with reason %#04x, which is not a reason "
				         "of §8.2 (and §3.1 forbids code 0)",
				         reason);
				dismiss(s, RCP_PROTOCOL_ERROR, d);
				return false;
			}
			reg(s, "the client takes its farewell, reason=%#04x detail=%s", reason,
			    ld < sizeof details ? details
			                     : "(longer than the field: not reported)");
			/* ⛔ §7.3: and this is the MOST TRAVELLED road of all when the
			 * product is healthy — the client leaving properly.  If the
			 * release lived only in `dismiss()` it would be missing right here. */
			release_on_detach(s, "client farewell");
			s->state = S_FINISHED;
			/* ⛔⭐ AND THE SLOT LEFT IS WRITTEN, as in the other three places —
			 * cure of the late evening of 11 Aug 2026.
			 *
			 * This was the only one of the four places that free the slot NOT
			 * to call `reg()`: `rcp_free`, `rcp_pagina_ha_chiuso` and
			 * `rcp_channel_closed` all write it.  ⛔ And the hole lay
			 * precisely on the road §8.1 REQUIRES — the client taking its
			 * farewell — that is the most travelled of all when the product is
			 * healthy.
			 *
			 * ⚠ The slot was really freed: `[M]` 11 Aug 2026, twelve
			 *   sessions in a row in the logs of `01-p5-ff-*`, and every later
			 *   «slot TAKEN» says «taken now: 1».  The defect was not
			 *   a leak, it was that **invariant §8.2 `0x0F` could no longer
			 *   be observed**: P5 judges the final number of «taken
			 *   now», and on this road no line carried it. ⇒ The bench
			 *   would have written «THE SLOT WAS NOT FREED» on a server that
			 *   had done its job — a red to the wrong suspect,
			 *   which is the seventh guise of `LESSONS.md` §1.9.
			 *
			 * ⛔ And before the cure of the farewell it was INVISIBLE: the client
			 *    never took its farewell, so this line was never travelled and
			 *    the slot always went away through the inactivity ceiling, which
			 *    writes its own line. */
			if (s->is_attached) {
				slot_leave(s->user);
				s->is_attached = false;
				reg(s, "slot LEFT by %s via %s (taken now: %d)",
				    s->user, s->provenance, taken_slots());
			}
			/* ⭐ The same number the log has just written: a single
			 * truth about the fact, on both roads of §3.1. */
			s->g.close(s->g.ctx, reason);
			return false;
		}
		case T_VIEW: {
			/* ⛔⭐⭐ §7.1 — «the view has changed», and it is the message this
			 *      server made pay most dearly without serving it.
			 *
			 * ⚠ Until 16 Aug 2026 it fell into the `default` with the line «it
			 *   belongs to the client and §7.1 defines it, but phase 1 does not
			 *   needs it yet», and the price was declared there in full: **a
			 *   conforming client that narrows the window loses the session**.
			 *   ⛔ And it is literally the symptom that finding R1.17 of §7.1 was
			 *   written to make impossible: *«the user narrows the browser
			 *   window to 300 pixels […] with the old line the client had three
			 *   choices, all bad — send `VIEW(300x800)` and have the session
			 *   closed because it resized a window»*.
			 *   The document removed the bad line from the client side; the
			 *   server applied it all the same.
			 *
			 * ⛔⭐ AND WHAT THIS BRANCH **DOES NOT DO** IS THE NORMATIVE HALF:
			 *
			 *   · **it does not touch the canvas**.  §7.1: «`VIEW` MUST NOT
			 *     change the canvas […] The only message that changes the canvas
			 *     is `FIT_CANVAS`».  ⚠ The wrong form here is not «closes», it
			 *     is «works too much»: a server that took the view for a canvas
			 *     request would shrink the desktop of whoever only narrowed the
			 *     window, and **without sending any `CANVAS`** — that is the two
			 *     sides drifting apart in silence (E2);
			 *   · **it does not touch the encoder**.  §7.1: «in RCP/1 not even
			 *     the size of what is encoded changes»; §6.2 binds
			 *     `w.`/`height` to the canvas in force, and whoever receives
			 *     others closes.  ⇒ Encoding at the view would make the client close;
			 *   · **it answers nothing on the wire**.  §7.1 foresees no
			 *     answer to `VIEW`, and §6.2 makes the client close the session
			 *     in front of a `CANVAS` it did not ask for: a «thanks, received»
			 *     written as `CANVAS` would kill the session;
			 *   · **it does not apply the canvas limits**.  §7.1 after R1.17:
			 *     «any size from 1x1 up is legal, odd included».
			 *
			 * ⇒ Validate, keep, write.  It is little, and it is what the arbiter
			 *   asks: the canvas belongs to the SESSION, the view to the CONNECTION. */
			uint32_t new_w = le_u32(&l);
			uint32_t new_h = le_u32(&l);

			if (l.too_short) {
				dismiss(s, RCP_PROTOCOL_ERROR,
				        "VIEW short: §7.1 wants two u32");
				return false;
			}
			/* ⛔ The state: §7.1 puts `VIEW` among the messages of the session,
			 *    and a view without a session has nothing to describe.
			 *    Same guard as `FIT_CANVAS`, and for the same reason. */
			if (!s->session_sent) {
				dismiss(s, RCP_PROTOCOL_ERROR,
				        "VIEW before SESSION: §7.1 admits it only with "
				        "the session open");
				return false;
			}
			/* ⛔ The only limit, and zero lies outside it — as in `ATTACH`, and
			 *    the rule is written in the two places because the two messages
			 *    arrive by different roads.  ⚠ If one day they became three,
			 *    it becomes a function. */
			if (!new_w || !new_h) {
				dismiss(s, RCP_PROTOCOL_ERROR,
				        "VIEW with a zero side: §7.1 admits any "
				        "size from 1x1 up, and zero is not a size");
				return false;
			}
			reg(s, "VIEW: the client's window goes from %ux%u to %ux%u (§7.1) "
			       "— ⛔ the canvas does NOT change and stays %ux%u, and in RCP/1 not "
			       "even the size of what is encoded changes: the client "
			       "rescales.  The limits of §4.5 do not apply to the view "
			       "(R1.17): any size from 1x1 up, odd included",
			    s->vista_l, s->vista_a, new_w, new_h, s->canvas_w, s->canvas_h);
			s->vista_l = new_w;
			s->vista_a = new_h;
			break;
		}

		case T_LAYOUT: {
			/* ⛔⭐⭐ §7.1 `0x0009` — «the keyboard layout has changed»,
			 *      and it is the exact twin of `VIEW`: until 16 Aug 2026
			 *      it fell into the same `default` and **closed the session of a
			 *      conforming client**.  `[M]` bench `06-b34` case 3: farewell
			 *      `0x0b PROTOCOL_ERROR`, connection dropped.
			 *
			 * ⚠ The symptom, in one line: *the user changes keyboard layout
			 *   while working, and the session drops.*  It is the same
			 *   shape that finding R1.17 of §7.1 exists to make
			 *   impossible — punishing whoever does what the arbiter defines.
			 *
			 * ⭐ And now it is REALLY needed: with §5-bis.7 carried out, this is the
			 *    message with which the layout is changed **without
			 *    detaching**.  Without it, the only way of changing keyboard
			 *    would be closing the session and reattaching.
			 *
			 * ⛔⛔ AND HERE THE ARBITER DOES NOT SAY SOMETHING THE PRODUCT MUST
			 *     DECIDE: what is done if the layout is well formed but
			 *     **unknown**.  At `ATTACH` §4.5 says it (farewell
			 *     `SESSION_UNSERVABLE`); with the session open it does not.
			 *
			 *     ⇒ Here the CHOICE is **not to close**: the one in force is
			 *       kept and the reason is written.  The reason is `SPECS.md`
			 *       §8.3 — *«never detach»* — and I1: closing the session of whoever
			 *       chose a keyboard this machine does not have means taking
			 *       away their work for a fault that costs them nothing, since
			 *       the previous keyboard still works.  ⚠ At `ATTACH` it is
			 *       different, and rightly so: there is no session there to save.
			 *     ⚠ It is a PRODUCT rule the arbiter does not name: it must be
			 *       carried into `RCP.md` §7.1, and the report delivers it. */
			char new_one[65];
			size_t ln = le_str(&l, new_one, sizeof new_one);

			if (l.too_short) {
				dismiss(s, RCP_PROTOCOL_ERROR,
				        "LAYOUT short: §7.1 wants a string");
				return false;
			}
			/* ⛔ The state, as for `VIEW`: §7.1 puts `LAYOUT` among the
			 *    messages of the session, and a layout without a session has
			 *    nothing to change. */
			if (!s->session_sent) {
				dismiss(s, RCP_PROTOCOL_ERROR,
				        "LAYOUT before SESSION: §7.1 admits it only with "
				        "the session open");
				return false;
			}
			/* ⛔ The FORM stays `PROTOCOL_ERROR` here too, and it is not an
			 *    inconsistency with the line above: §4.5 keeps the two faults
			 *    distinct because they are two different defects — whoever sends
			 *    «../../etc/passwd» has a broken (or hostile) client, whoever sends
			 *    «hu» only has a keyboard this machine does not have. */
			if (!layout_well_formed(new_one, ln)) {
				dismiss(s, RCP_PROTOCOL_ERROR,
				        "LAYOUT malformed");
				return false;
			}
			if (!layout_known(s, new_one)) {
				reg(s, "⚠ LAYOUT «%s»: this machine does not have it.  ⛔ The "
				       "session is NOT closed (§8.3, «never detach») and keeps "
				       "«%s»: the previous keyboard still works, and taking away "
				       "the work for a missing keyboard would cost more than the "
				       "fault.  ⚠ At `ATTACH` §4.5 wants the farewell, and there it is "
				       "right: there is no session to save",
				    new_one, s->layout[0] ? s->layout : "the session's own");
				break;
			}
			if (strcmp(new_one, s->layout) == 0) {
				/* ⚠ It is written all the same: a client that sends the same
				 *   layout again is not a fault, but a keymap replacement
				 *   costs Mutter the DESTRUCTION of the keyboard device
				 *   (`STUDIES.md` §gnome §9) — and not doing it for nothing is a
				 *   saving one sees. */
				reg(s, "LAYOUT «%s»: it is already the one in force, I ask "
				       "nothing of the stage (a useless replacement would cost the "
				       "destruction of the keyboard device)",
				    new_one);
				break;
			}
			reg(s, "LAYOUT: from «%s» to «%s», with the session OPEN (§7.1 0x0009)",
			    s->layout[0] ? s->layout : "(none)", new_one);
			snprintf(s->layout, sizeof s->layout, "%s", new_one);
			apply_layout(s, "LAYOUT (0x0009)");
			/* ⛔ And NOTHING is answered on the wire: §7.1 foresees no
			 *    answer to `LAYOUT`, exactly as for `VIEW`.  A
			 *    «thanks, received» invented here would be an unsolicited
			 *    message, and §6.2 makes the client close the session in front
			 *    of a message it did not ask for. */
			break;
		}
		case T_FIT_CANVAS: {
			/* ⛔⭐⭐ §7.1 — «the client asks for a canvas of another size».
			 *
			 * ⚠ Until 14 Aug 2026 this type fell into the `default` and made a
			 *   conforming client **lose the session**, with the line «phase 1
			 *   does not needs it yet».  ⛔ And it was a violation of ours:
			 *   `RCP.md:483` point 4 says an out-of-limits size is refused
			 *   with `CANVAS(SIZE_OUT_OF_RANGE)` **instead of closing**, and the
			 *   reason is written next to it — «the user who drags a window
			 *   badly must not lose the session».
			 *
			 * ⇒ Now one always answers, and the client knows **what to
			 *   continue with**: the two fields of `CANVAS` carry the canvas in
			 *   force AFTER the answer, which on a refusal is the previous one. */
			uint32_t requested_w = le_u32(&l);
			uint32_t requested_h = le_u32(&l);
			uint32_t good_w = 0, good_h = 0;

			if (l.too_short) {
				dismiss(s, RCP_PROTOCOL_ERROR,
				        "FIT_CANVAS short: §7.1 wants two u32");
				return false;
			}
			if (!s->session_sent) {
				dismiss(s, RCP_PROTOCOL_ERROR,
				        "FIT_CANVAS before SESSION: §7.1 admits it only with "
				        "the session open");
				return false;
			}
			/* ⛔⭐ AND HERE NO GUARD ON THE SLOT IS NEEDED, and it must be said
			 *     because the first draft of this cure had put one: it would have
			 *     been **dead code that looks alive**.
			 *
			 * `speak_again()` runs at the top of `rcp_receive()`, before
			 * any message: a session detached for silence either takes the slot
			 * back (and then commands by full right) or is sent away with §8.2
			 * `0x0F`.  ⇒ Whoever gets this far ALWAYS holds the slot, and an
			 * `if` that cannot be false is worse than nothing: the day that rule
			 * changed, nobody would know this line was duplicating it.
			 * ⚠ The LIVE guard is the other one, in `canvas_recall_stage()`:
			 * there the session without a slot really gets there, because the
			 * FRAMES reach it even when it is silent (bench `04-b31`, case 18). */
			/* ⛔ The ceiling and parity live in ONE place only, and not here:
			 *    `rcp_size_allowed()` (`rcp.h`).  Rewriting the same rule here
			 *    would mean having two, and the day one changes the defect is
			 *    «the server accepts a size the compositor cannot take» — that
			 *    is the session of whoever hosts us dying in silence. */
			if (!rcp_size_allowed(requested_w, requested_h, &good_w, &good_h)) {
				reg(s, "FIT_CANVAS %ux%u REFUSED: below the minimum of §4.5 "
				       "(%ux%u .. %ux%u) — the canvas stays %ux%u",
				    requested_w, requested_h, RCP_CANVAS_MIN_W, RCP_CANVAS_MIN_H,
				    RCP_CANVAS_MAX_W, RCP_CANVAS_MAX_H, s->canvas_w, s->canvas_h);
				send_canvas(s, 2 /* REFUSED */, 2 /* SIZE_OUT_OF_RANGE */,
				           s->canvas_w, s->canvas_h);
				break;
			}
			/* ⛔⭐ ABOVE THE MAXIMUM IT IS REDUCED AND SAID — 1 Oct 2026, canvas at
			 *     most 4096x2304 (box in `rcp.h`).  A 5K monitor is not an
			 *     error of the client: `CANVAS(FITTED)` will tell it the real size,
			 *     and this line says why it is not the one requested. */
			if (requested_w > RCP_CANVAS_MAX_W || requested_h > RCP_CANVAS_MAX_H)
				reg(s, "⚠ DECLARED FALLBACK (§4.5): FIT_CANVAS %ux%u beyond the "
				       "canvas maximum %ux%u — reduced to %ux%u (the side that "
				       "overflows to the maximum, the other as it is)",
				    requested_w, requested_h, RCP_CANVAS_MAX_W,
				    RCP_CANVAS_MAX_H, good_w, good_h);
			/* ⛔⛔ AND THE DECODER CEILING IS RESPECTED HERE TOO — §4.5:
			 *     *«the granted canvas MUST respect `video.max_size` if the
			 *     client declared it»*.  ⚠ Defect found while refuting: this
			 *     check was in `ATTACH` — where it reduces in proportion, with
			 *     even sides, and declares it — and **not** here.  ⇒ A hi-dpi
			 *     client asking for the size of its own window in physical pixels
			 *     could get a canvas granted that its decoder cannot take, and
			 *     from there there was no going back: the screen stops and does
			 *     not restart.
			 *
			 * ⚠ It is REDUCED instead of refused, because the client did nothing
			 *   wrong — it asked for the size of its window — and `CANVAS` will
			 *   tell it what it got.  It is the same choice as §4.5 in
			 *   `ATTACH`, with the same arithmetic. */
			if (s->max_l && (good_w > s->max_l || good_h > s->max_a)) {
				uint32_t prev_w = good_w, prev_h = good_h;
				uint32_t cl, ca;
				/* The side that limits most: cross comparison, without
				 * floating-point divisions. */
				if ((uint64_t)good_w * s->max_a <= (uint64_t)good_h * s->max_l) {
					ca = s->max_a;
					cl = (uint32_t)(((uint64_t)good_w * s->max_a) / good_h);
				} else {
					cl = s->max_l;
					ca = (uint32_t)(((uint64_t)good_h * s->max_l) / good_w);
				}
				/* ⛔ And the result goes back through the same rule: the reduction
				 *    may have produced an odd number or one below the minimum, and
				 *    rewriting parity here would mean having it in two
				 *    places. */
				if (!rcp_size_allowed(cl, ca, &good_w, &good_h)) {
					reg(s, "FIT_CANVAS %ux%u REFUSED: reduced to the "
					       "video.max_size (%ux%u) it would give %ux%u, which §4.5 "
					       "does not allow — the canvas stays %ux%u",
					    requested_w, requested_h, s->max_l, s->max_a, cl, ca,
					    s->canvas_w, s->canvas_h);
					send_canvas(s, 2 /* REFUSED */, 2 /* SIZE_OUT_OF_RANGE */,
					           s->canvas_w, s->canvas_h);
					break;
				}
				reg(s, "⚠ DECLARED FALLBACK (§4.5): FIT_CANVAS %ux%u exceeds the "
				       "video.max_size of this client (%ux%u) — reduced to "
				       "%ux%u, proportions kept, both even",
				    prev_w, prev_h, s->max_l, s->max_a, good_w, good_h);
			}
			/* ⭐⭐ AND HERE STARTS THE CHAIN THAT WAS MISSING ON 14 AUG 2026.
			 *
			 * ⚠ Until yesterday this point answered `COMPOSITOR_UNABLE`
			 *   NAMING the missing piece — *«`children_recanvas()` →
			 *   `capture_resize()` is missing»* — and it was true.  Now the
			 *   two pieces are there, and the answer is no longer a line: it is a
			 *   round trip to the compositor and back.
			 *
			 * ⛔ THE FIRST CASE IS THE ONE THAT MUST MOVE NOTHING: the size
			 *    requested is already the one in force.  ⚠ It is not a textbook
			 *    case — it is the most frequent of all: the client sends the size
			 *    of its window at every resize, and whoever drags an edge
			 *    sends twenty per second.  Passing it to the stage would mean
			 *    restarting the stream for nothing, that is **losing a frame at
			 *    every useless request** (`STUDIES.md` §kde §8.2-bis).
			 *
			 * ⚠ But only if there is no request already in flight: if there is one,
			 *   the stage is going ELSEWHERE, and this is a change of mind that
			 *   must really be passed on. */
			if (good_w == s->canvas_w && good_h == s->canvas_h && !s->canvas_flight) {
				/* ⛔ It answers `CANVAS(FITTED)` and does NOT open the keyframe
				 *    debt: the «size that was already there» form of
				 *    `rcp_canvas_adapted_now()` does it, and exists for this. */
				rcp_canvas_adapted_now(s, good_w, good_h, now);
				break;
			}

			/* ⛔ NO HOOK = COMPOSITOR_UNABLE, and it is the TRUE answer for
			 *    whoever hosts us without a stage: the in-process benches of phase 1
			 *    and the harness of `benches/01-b3-graft-rcp.py`.  §7.1: «if the
			 *    compositor cannot resize, the server MUST answer with
			 *    `CANVAS(REFUSED, COMPOSITOR_UNABLE)`, and the client MUST
			 *    show the entry as off.  It MUST NOT pretend it
			 *    succeeded». */
			if (!s->g.recanvas) {
				reg(s, "FIT_CANVAS %ux%u → %ux%u allowed, but this host has no "
				       "stage to resize (hook `recanvas` not "
				       "connected): COMPOSITOR_UNABLE, and the canvas stays %ux%u",
				    requested_w, requested_h, good_w, good_h, s->canvas_w, s->canvas_h);
				send_canvas(s, 2 /* REFUSED */, 1 /* COMPOSITOR_UNABLE */,
				           s->canvas_w, s->canvas_h);
				break;
			}

			/* ⛔⭐ A REQUEST IN FLIGHT IS ANSWERED BEFORE ACCEPTING ANOTHER
			 *     — §7.1: «the n-th `CANVAS` answers the n-th `FIT_CANVAS`».
			 *
			 * ⚠ The client KEEPS COUNT of the unanswered requests (§6.2, and
			 *   from it decides whether to hold back a frame or close the session).
			 *   If two `FIT_CANVAS` received only one `CANVAS`, that count would
			 *   never return to zero and the client would hold back frames
			 *   forever — that is its memory.  ⛔ Whoever drags an edge sends
			 *   exactly two in a row: it is not a rare case, it is THE case. */
			if (s->canvas_flight) {
				reg(s, "FIT_CANVAS %ux%u arrived while %ux%u was still in flight "
				       "to the stage: I answer NOT_NOW to the FIRST (§7.1 wants one "
				       "CANVAS for each) and pass on the second",
				    good_w, good_h, s->canvas_flight_w, s->canvas_flight_h);
				send_canvas(s, 2 /* REFUSED */, 3 /* NOT_NOW */, s->canvas_w,
				           s->canvas_h);
				s->canvas_flight = false;
			}

			/* ⛔ And the hook says whether the QUESTION left, not whether the canvas
			 *    changed: the proof arrives with a frame, and
			 *    `rcp_tela_concessa()` brings it in here. */
			if (!s->g.recanvas(s->g.ctx, good_w, good_h)) {
				reg(s, "⛔ FIT_CANVAS %ux%u → %ux%u: the request did NOT leave "
				       "for the stage (no child, or the socket did not "
				       "take it).  NOT_NOW, and the canvas stays %ux%u",
				    requested_w, requested_h, good_w, good_h, s->canvas_w, s->canvas_h);
				send_canvas(s, 2 /* REFUSED */, 3 /* NOT_NOW */, s->canvas_w,
				           s->canvas_h);
				break;
			}
			s->canvas_flight = true;
			s->canvas_flight_w = good_w;
			s->canvas_flight_h = good_h;
			s->canvas_flight_from = now;
			/* ⛔ And the previous disagreement is CLOSED: from now the stage has a
			 *    new request, and dating the backstop on an old disagreement would
			 *    make it expire backwards. */
			s->canvas_mismatch_since = 0;
			s->canvas_mismatch_wait = 0;
			reg(s, "⭐ FIT_CANVAS %ux%u → %ux%u PASSED to the stage (`children_recanvas()` "
			       "→ `capture_resize()`).  ⚠ No `CANVAS` now: the "
			       "answer is the first frame at the new size, and if it does not "
			       "arrive within %u ms NOT_NOW is answered (§7.1)",
			    requested_w, requested_h, good_w, good_h,
			    (unsigned)RCP_CANVAS_WAIT_MS);
			break;
		}
		default: {
			/* §7.1 + §3: an unknown type on the control channel is not
			 * ignored — the connection drops.
			 *
			 * ⛔ But §3.1 point 1 asks to write WHAT was not understood,
			 * and «unknown» would be false for half the cases: `HERE_I_AM`,
			 * `ADMITTED`, `REJECTED`, `SESSION`, `CURSOR_SHAPE`, `CANVAS` and
			 * `BENCH_OUTCOME` are KNOWN types that travel in the other direction
			 * (§7.1).  A client sending one has a different defect from one
			 * that invents a type, and the log must tell them apart.
			 *
			 * ⛔⭐ AND THE FOUR THAT REMAIN ARE NOT «UNKNOWN» — finding
			 *    R9.7.  §7.1 numbers them and assigns them to the CLIENT: `0x0008 VIEW`,
			 *    `0x0009 LAYOUT`, `0x000B FIT_CANVAS`,
			 *    `0x000D REQUEST_KEY`.  Writing «unknown» on a type
			 *    the arbiter defines is saying something false in the log, and it is
			 *    the same defect the paragraph above declares it
			 *    corrected for the server's types.
			 *
			 * ⭐ AND SINCE 16 AUG 2026 **ONE** REMAINS: `0x0009 LAYOUT`.
			 *    The other three went away one at a time, and each one
			 *    took away the same price — a session lost to a conforming
			 *    client:
			 *      · `0x000D REQUEST_KEY` on 12 August, with the video channel:
			 *        §5.2 obliges the client to send it as soon as it sees a gap;
			 *      · `0x000B FIT_CANVAS` on 14 August, with the stage able to
			 *        resize: §7.1 requires a `CANVAS` for it with a MUST;
			 *      · `0x0008 VIEW` on 16 August, sub-phase 6.4: it is the most
			 *        expensive of the three, because it required **nothing** — the
			 *        view does not touch the canvas, does not touch the encoder and
			 *        has no answer.  ⛔ Keeping it was enough, and for two phases it
			 *        closed the session of whoever narrowed the browser window.
			 *
			 * ⚠ And `0x0009 LAYOUT` stays out with a REAL price, not through
			 *   forgetfulness: renegotiating a keymap destroys and recreates the
			 *   `libei` keyboard device (`STUDIES.md` §gnome §9), and that
			 *   chain belongs to sub-phase 6.2.  ⛔ As long as it stays out, a
			 *   conforming client that changes layout **loses the session**, and
			 *   this line is what says so: whoever reads «not yet served in phase
			 *   1» knows the defect is ours and knows where it disappears; whoever
			 *   read «unknown» went looking for a defect of the client. */
			bool del_server = kind == T_HERE_I_AM || kind == T_ADMITTED ||
			                  kind == T_REJECTED || kind == T_SESSION ||
			                  kind == T_CURSOR_SHAPE ||
			                  kind == 0x000E /* CANVAS */ ||
			                  kind == T_BENCH_OUTCOME;
			const char *del_client = NULL;
			switch (kind) {
			/* ⚠ `0x0008 VIEW` no longer appears here: since 16 Aug 2026 it has
			 *   a case of its own and never reaches the `default` — like `0x000B`
			 *   on the 14th.  Removed instead of left «for safety»: an
			 *   unreachable branch naming a served type is a line that
			 *   lies to whoever reads the log, and it is the defect this
			 *   same paragraph declares it corrected for the others. */
			/* ⚠ `0x000B FIT_CANVAS` no longer appears here: since 14 Aug 2026 it
			 *   has a case of its own and never reaches the `default`.  Removed
			 *   instead of left «for safety»: an unreachable branch naming a
			 *   served type is a line that lies to whoever reads. */
			default:
				break;
			}
			char d[160];
			if (del_server)
				snprintf(d, sizeof d, "type %#06x: it belongs to the server, not to the client",
				         kind);
			else if (del_client)
				snprintf(d, sizeof d,
				         "type %#06x %s: it belongs to the client and §7.1 defines it, "
				         "but phase 1 does not serve it yet",
				         kind, del_client);
			else
				snprintf(d, sizeof d, "unknown type %#06x on control",
				         kind);
			dismiss(s, RCP_PROTOCOL_ERROR, d);
			return false;
		}
		}
		if (!keep_going)
			return false;
		/* ⛔ §6.0: one advances by the DECLARED length, not by how much was
		 * read.  ⚠ The check here is not a duplicate of the one before
		 * the switch: that one speaks BEFORE the effects and is the check of
		 * §6.1; this one fires only if `measure_fields()` and `tratta_*()` have
		 * drifted apart, that is if someone changed a body in one place only. */
		if (l.i != lung) {
			dismiss(s, RCP_PROTOCOL_ERROR,
			        "the body has more bytes than the expected fields");
			return false;
		}
		size_t before = s->acc_len;
		memmove(s->acc, s->acc + 6 + lung, s->acc_len - 6 - lung);
		s->acc_len -= 6 + lung;
		/* ⛔ AND THE TAIL IS ZEROED — finding R9.8.  The `memmove` slid the
		 * remainder down and left the bytes of the message just consumed where
		 * they were: those of a `CREDENTIALS` are the password in clear, and
		 * they stayed in the session until the end of the connection.
		 * §4.4: «it must be zeroed as soon as PAM has answered». */
		explicit_bzero(s->acc + s->acc_len, before - s->acc_len);
		s->since = now;
	}
}

/* ⛔⭐ WHOEVER HAS BEEN SILENT FOR THIRTY SECONDS IS NO LONGER ATTACHED, AND WHEN
 *    THEY SPEAK AGAIN THEY MUST KNOW IT — finding R9.2.
 *
 *    The silence branch of `rcp_time()` left the slot and set
 *    `is_attached = false`, but the state stayed `S_ACTIVE`: from there on the
 *    server had TWO «active» sessions for the same user — what I2
 *    forbids — and the first kept being served as if nothing had happened,
 *    without ever having received a `FAREWELL`, a reason or a close code.  §8.2:
 *    «no attached and alive client is ever ousted», and that one was
 *    ousted in silence.
 *
 * ⭐ The slot can be TAKEN BACK, and it is not a concession: §8.2 says that «the
 *    criterion is the silence clock, not the intention of whoever arrives», and
 *    the case the clock exists to needs is the phone back from the
 *    tunnel.  If nobody has taken the slot, that client resumes
 *    exactly from where it was.
 *
 * ⛔ If instead the slot has been taken, the farewell is `ALREADY_ACTIVE_REMOTELY` and
 *    the sentence the client will build from it — «you already have an active
 *    session elsewhere» — this time is TRUE.  ⚠ And it stays true that «the one
 *    refused is whoever arrives»: here whoever arrives is them, whoever was
 *    there is the other.
 *
 * ⛔⭐ AND IT IS A FUNCTION, since 14 Aug 2026, because now the client's bytes
 *     come in through TWO doors — `rcp_receive()` and `rcp_receive_input()`.
 *     ⚠ Leaving it written by hand inside the first would have meant that
 *     whoever speaks again **by moving the mouse** does not take back the slot,
 *     and the symptom would have been: the video restarts if you type, not if
 *     you move your hand.  Two copies of a state diverge, and this is the copy
 *     that was not made.
 *
 * Returns `false` if the session has been sent away. */
static bool speak_again(rcp_session *s)
{
	if (s->state != S_DETACHED)
		return true;
	if (slot_take(s) == SLOT_TAKEN) {
		s->is_attached = true;
		s->state = S_ACTIVE;
		/* ⛔ §7.3: the release on detach has already happened (the silence
		 * triggered it), and this session starts again with free hands: if it
		 * fell silent a second time, the release must be able to fire again. */
		s->inp_released = false;
		reg(s, "⭐ slot TAKEN BACK by %s via %s after the silence: nobody "
		       "else had taken it (taken now: %d)",
		    s->user, s->provenance, taken_slots());
		return true;
	}
	reg(s, "⛔ %s speaks again after the silence, but their slot belongs "
	       "to another client: §8.2 0x0F, and this time it is true",
	    s->user);
	dismiss(s, RCP_ALREADY_ACTIVE_REMOTELY,
	        "the slot of this session was taken by another client "
	        "while this one was silent");
	return false;
}

bool rcp_receive(rcp_session *s, const uint8_t *data, size_t len, uint64_t now)
{
	if (s->state == S_FINISHED) {
		/* ⛔ And it is WRITTEN.  §4.4 says that after `REJECTED` the client must
		 * not retry on the same connection, and §4.2 that after the end of the
		 * session nothing more is sent: they are two MUSTs of the CLIENT, and
		 * the only place from which they can be observed is here.  ⚠ Without
		 * this line a client that retries is indistinguishable from one that
		 * stopped — B11 would measure the server's silence instead of the
		 * page's behaviour.
		 *
		 * ⛔⭐ BUT NOT EVERYTHING THAT ARRIVES AFTER THE END IS A VIOLATION, and
		 *    counting it all together pointed a red at the wrong
		 *    suspect — the seventh guise of `LESSONS.md` §1.9.
		 *
		 * §4.4 forbids the client ONE thing: **retrying**.  §8.1 imposes
		 * another: whoever closes **MUST** send `FAREWELL` with the reason.  ⭐ The
		 * two meet when the server errs AFTER `REJECTED` — the
		 * `respinto-poi-congedo` case of B11: the page sees a message that should
		 * not have arrived, closes as §3 requires, and its `FAREWELL` leaves
		 * when for us the session is already over.
		 *
		 * ⚠ On 10 Aug 2026 that 69-byte `FAREWELL` was counted as
		 *   «sent after the end», and the red went to the page that was
		 *   doing **exactly** what §8.1 requires of it.  ⛔ The control
		 *   channel had no FIN: §4.2 had nothing to do with it, and the only
		 *   rule in play — §4.4 — speaks of attempts, not of partings.
		 *
		 * ⭐ So one distinguishes, and distinguishes **on messages**, not on the
		 *    first six bytes of the piece: see `judge_after_end()`, finding R9.15. */
		judge_after_end(s, data, len);
		return false;
	}
	/* ⭐ The sign of life is reset here, on RCP bytes, because a byte that
	 *    arrived is a packet that arrived.  ⚠ The long reason is on the other
	 *    of the two calls, in `rcp_receive_input()`.
	 * ⛔ And the user's INACTIVITY clock is NOT: nothing on the control
	 *    channel is a gesture, and much of it leaves the page on its own
	 *    (`REQUEST_KEY`, `PACE`) — see `DEFAULT_INACTIVITY`. */
	s->last_life = now;

	/* ⚠ The connection is not closed for silence alone — that choice is
	 *   declared in the box at the top and does not change.  What changes is
	 *   that the STATE tells the truth.  See `speak_again()`, finding R9.2. */
	if (!speak_again(s))
		return false;

	/* ⛔ It is buffered IN PIECES and drained after each one: so the ceiling is
	 * the one of §6.1 and not that of a buffer, and a big piece does not die
	 * because more messages fit inside it (finding R9.13). */
	while (len) {
		size_t space = MAX_ACCUMULATION - s->acc_len;
		if (space == 0) {
			dismiss(s, RCP_PROTOCOL_ERROR, "too many bytes waiting for a body");
			return false;
		}
		size_t amount = len < space ? len : space;
		int outcome = accumulate(s, data, amount);
		if (outcome == 0) {
			dismiss(s, RCP_PROTOCOL_ERROR, "too many bytes waiting for a body");
			return false;
		}
		if (outcome < 0) {
			/* ⚠ §8.2 has no reason meaning «memory is exhausted»:
			 *   `SESSION_UNSERVABLE` is the closest — «cannot be
			 *   served» — and carries the detail in the body.  Our choice, and
			 *   declared here so that it is not read as a rule. */
			dismiss(s, RCP_SESSION_UNSERVABLE,
			        "out of memory in the control channel accumulation");
			return false;
		}
		data += amount;
		len -= amount;
		if (!drain(s, now))
			return false;
	}
	return true;
}

/* ⛔ §2.5 — the violation that does NOT come from the control channel.
 *
 * Whoever opens one stream too many, or puts the wrong channel inside it, has
 * sent no control message: the violation is detected by the HOST, which
 * is the only one that sees the streams.  ⛔ But the closing must stay that of
 * §3.1 — log, `FAREWELL` on the control channel if it is still usable,
 * and the reason code in the closing of the session — and those three things
 * only this module knows how to do.
 *
 * ⚠ It is the **second conditional of §3.1** that makes the case interesting:
 *   here the control channel is usually still good, so the `FAREWELL`
 *   really leaves.  A bench that demanded all three points ALWAYS would give
 *   red on the right code the day it was not (finding R3.3).
 *
 * ⛔⭐ AND WITH THE SESSION OVER ONE DOES NOT KEEP QUIET — finding R9.16.  This
 *    function went entirely and only through `dismiss()`, which if the state is
 *    `S_FINISHED` leaves at the first line: no log, no `FAREWELL`, no close code.
 *    A client that takes its farewell properly and THEN opens a stream in the
 *    wrong direction (§2.5) left **no** trace — and the host, which saw that
 *    stream, has no other place to say it.
 *
 * ⚠ The comparison is internal to this file: `rcp_receive()` writes «bytes
 *   arrived AFTER the end of the session» precisely because «the only place
 *   from which they can be observed is here».  For STREAMS that place is this
 *   function. */
/* ⛔⭐ THE FAREWELL THAT COMES FROM OUTSIDE — §8.1, and the case it was written
 *     for is `SERVER_CLOSING` (§8.2, `0x0C`).  Finding B-7, night of
 *     10 Aug 2026.
 *
 *     `0x0C` was defined in `rcp.h` and **no line of the product emitted it**:
 *     at a `systemctl stop` with an active session the server freed everything
 *     and kept quiet.  The client stayed waiting for the 30 s of inactivity
 *     and showed «network error» — that is literally the defect of
 *     `LESSONS.md` §1.7 that §3.1 exists to remove.
 *
 * ⚠ Whoever closes MUST send `FAREWELL` with the reason **and** repeat the reason
 *   in the close code: both roads are travelled by `dismiss()`, and that is
 *   why this function does nothing but call it.  ⛔ The reason is chosen
 *   by the host, because only it knows why it is closing. */
void rcp_dismiss(rcp_session *s, uint8_t reason, const char *detail)
{
	if (!s || s->state == S_FINISHED)
		return;
	dismiss(s, reason, detail ? detail : "");
}

void rcp_violation(rcp_session *s, const char *detail)
{
	if (!s)
		return;
	if (s->state == S_FINISHED) {
		/* ⛔ §3.1 point 1 applies all the same: one writes WHAT.  Points 2 and
		 * 3 do not, and rightly — the session is already closed with its
		 * reason, and sending a second one would state two truths about the
		 * same fact. */
		reg(s, "⛔ violation detected AFTER the end of the session from %s: %s "
		       "— the session was already closed, so no FAREWELL and no "
		       "close code (§3.1), but the log names it",
		    s->provenance, detail);
		return;
	}
	dismiss(s, RCP_PROTOCOL_ERROR, detail);
}

/* ⛔⭐ §4.2 — THE CONTROL CHANNEL CLOSING IS THE END OF THE SESSION,
 * AND IT HOLDS EVEN WHEN THE ONE CLOSING IT IS THE SERVER.
 *
 * From that instant no client message can arrive any more — §4.2 forbids it
 * to send on any channel — so the slot (§8.2 reason 0x0F) would be freed by
 * NOBODY until the death of the connection.  And a connection, a browser keeps
 * it alive.
 *
 * ⭐ Found by B11 on 10 Aug 2026, and only on Chrome: after the case in which
 *    the server closes the channel with a FIN, the three following cases received
 *    `ALREADY_ACTIVE_REMOTELY`.  Not on Firefox — there the transport closed the stream
 *    in time and `rcp_free()` arrived all the same.  ⛔ The defect lived in the
 *    difference between two engines, and no test client could see it.
 *
 * ⚠ The session is not freed and not sent away: sending a `FAREWELL` on a
 *   channel we have just closed makes no sense, and the reason — if there was
 *   one — has already travelled in the close code (§3.1 point 3).  It stays alive
 *   because it is the only point from which one observes a client sending after
 *   the end, which is the MUST of §4.2.                                      */
void rcp_channel_closed(rcp_session *s)
{
	if (!s || s->state == S_FINISHED)
		return;
	reg(s, "the control channel closed on the server side: "
	       "§4.2, the session is over (state: %s)",
	    STATE_NAMES[s->state]);
	/* ⛔ §7.3: the fourth road — the channel dies and does not go through `dismiss()`. */
	release_on_detach(s, "the control channel closed");
	if (s->is_attached) {
		slot_leave(s->user);
		s->is_attached = false;
		reg(s, "slot LEFT by %s via %s (taken now: %d)", s->user,
		    s->provenance, taken_slots());
	}
	s->state = S_FINISHED;
}

/* ⭐ THE OUTCOME OF THE ASYNCHRONOUS CHECK COMES BACK IN HERE — `DECISIONS.md` §1.10.
 *
 * ⛔ AND THERE ARE FOUR WALLS BEFORE TOUCHING `cred_good`, one for each
 *    road by which a «yes» could get in where it must not (invariant I3):
 *
 *   1. the session must be alive and in `wait-verdict` — a verdict that
 *      arrives on a session already `active` cannot reopen it;
 *   2. it must HAVE BEEN ASKED (`expected_verdict`) — so an invented request
 *      finds nobody waiting for it;
 *   3. the number must be ITS OWN — the request belongs to the process, not to
 *      the session, and without this comparison one user's answer could
 *      admit another.  ⛔ It is the wall that counts most;
 *   4. `expected_verdict` is switched off HERE: a second answer for the same
 *      request does not get in, and «I received two verdicts» does not become
 *      «the last one wins».
 *
 * ⚠ And it sends nothing on the wire: `rcp_time()` takes care of that, when
 *   the fixed second of §4.4-bis has passed too. */
bool rcp_verdict(rcp_session *s, uint64_t ticket, bool admitted,
                  uint64_t now)
{
	if (!s || s->state != S_WAIT_VERDICT || !s->expected_verdict)
		return false;
	if (s->ticket != ticket)
		return false;

	s->expected_verdict = false;
	s->cred_good = admitted;
	s->cred_reason = RCP_WRONG_CREDENTIALS;
	/* ⛔⭐ D4b (`DECISIONS.md` §11.50, §11.39): the helper could NOT check
	 *     (the bracket of `rcp_refusal_unchecked()`).  Refused as ours, at the
	 *     fixed second and not at the 12 s net: `0x0E` on the wire, and the
	 *     count of §4.4-bis is NOT touched — PAM never judged.  Same road as
	 *     `rcp_verdict_lost()`. */
	if (!admitted && unchecked_ticket && ticket == unchecked_ticket) {
		s->cred_good = false;
		s->refusal_is_ours = true;
		login_release(s->address, s->user);
		reg(s, "⛔ the helper could NOT check request %llu (its cap, a failed "
		       "fork, or it died): REJECTED as ours — 0x0E at the fixed second, "
		       "NOT counted towards the ban, the booking is given back "
		       "(DECISIONS.md §11.50)",
		    (unsigned long long)ticket);
		return true;
	}
	reg(s, "PAM answered (request %llu): %s  ⭐ and the thread never "
	       "stopped (DECISIONS.md §1.10)",
	    (unsigned long long)ticket, admitted ? "admitted" : "refused");

	/* ⛔ THE BOOKING OF §4.4-bis IS RESOLVED HERE, and this is the point where
	 *    the fact «an attempt failed» exists.  A «no» also covers the PAM
	 *    timeout of the helper (`helper_expired()` delivers a refusal): an
	 *    attempt without a verdict COUNTS AS FAILED — plan B of 24 Oct 2026.
	 *    The rule of the 1.0 («three in five minutes, twelve hours») is
	 *    replaced by the three levels above `LIMIT`. */
	{
		struct sink k = {s, NULL, NULL};
		struct login_result r;
		if (!admitted && refusal_uncounted(&k, ticket, s->address, now)) {
			login_release(s->address, s->user);
		} else {
			login_resolve(s->address, s->user, admitted, now, &r);
			login_report(&k, s->address, s->user, admitted, &r, now);
		}
	}
	return true;
}

/* ⛔ The helper died (or the request was lost by OUR hand) while this session
 * waited: the walls of `rcp_verdict()` all the same, but the answer is a no
 * that is OUR defect — the booking is given back and NOTHING is counted
 * (24 Oct 2026, project lead).  The PAM timeout is not this: it is a verdict
 * of `rcp_verdict()` with `admitted` false, and it counts. */
bool rcp_verdict_lost(rcp_session *s, uint64_t ticket)
{
	if (!s || s->state != S_WAIT_VERDICT || !s->expected_verdict)
		return false;
	if (s->ticket != ticket)
		return false;
	s->expected_verdict = false;
	s->cred_good = false;
	s->cred_reason = RCP_WRONG_CREDENTIALS;
	s->refusal_is_ours = true;
	login_release(s->address, s->user);
	reg(s, "⛔ the PAM helper died before answering (request %llu): REJECTED "
	       "(invariant I3), our defect, and the booking is given back without "
	       "counting anything (§4.4-bis)",
	    (unsigned long long)ticket);
	return true;
}

bool rcp_time(rcp_session *s, uint64_t now)
{
	if (s->state == S_FINISHED)
		return false;
	/* ⏳ §13.5: a `PACE` held back by the 250 ms window goes out here. */
	pace_flush(s, now);

	/* ⛔⛔ THE BACKSTOP OF PASTE REQUESTS, and without it the clipboard
	 *      channel works only once.
	 *
	 *      The case: the text is asked of the client (`CLIPBOARD_ASK`) and the
	 *      client never answers — it has detached, or cannot needs that
	 *      transfer.  ⛔ The queue does not empty, `app_requested` stays true, and
	 *      from there on **every later paste queues behind a question that
	 *      will never have an answer**: the symptom is «the clipboard worked
	 *      once and then never again», which nobody connects to a client that
	 *      did not answer half an hour ago.
	 *
	 * ⚠ And this backstop is WIDER than the child's (4 s) on purpose: there
	 *   the debt towards the compositor is paid — whoever pastes has already had
	 *   their empty answer — here the channel is put back on its feet.  ⛔ Narrowing
	 *   it until they coincide would make the two things expire together, and a
	 *   text arriving at just the right millisecond would no longer find anyone
	 *   to needs on either side. */
	if (s->app_serial_n > 0 && now - s->app_requested_ms > CLIPBOARD_BACKSTOP) {
		reg(s, "⚠ CLIPBOARD: %d paste requests without an answer from the client "
		       "after %llu ms (backstop %d): the queue is emptied.  ⛔ Whoever was "
		       "pasting has already had their empty answer from the child; this "
		       "backstop serves not to leave the channel blocked for the pastes AFTER",
		    s->app_serial_n, (unsigned long long)(now - s->app_requested_ms),
		    CLIPBOARD_BACKSTOP);
		s->app_serial_n = 0;
		s->app_requested = false;
	}

	/* ⛔ §4.4-bis: the fixed delay applies to ADMITTED TOO.  Applying it only
	 * to refusals would put the timing back on the other side, and the
	 * distinction §4.4 forbids writing in the reason would be read with a stopwatch. */
	if (s->state == S_WAIT_VERDICT) {
		/* ⛔⭐ NOW TWO THINGS ARE AWAITED, AND THE ORDER IS NOT GUARANTEED —
		 *     `DECISIONS.md` §1.10, 12 Aug 2026.
		 *
		 *     The fixed second of §4.4-bis and the helper's answer.  Until
		 *     yesterday the second had already arrived when this state
		 *     began — PAM had blocked the thread — and here it was enough to
		 *     look at the clock.
		 *
		 * ⭐ And the time of whoever authenticates does NOT change: PAM takes
		 *    from 1.0 to 2.2 s (`[M]` B8), so the verdict almost always arrives
		 *    AFTER the fixed second and it is the verdict that sets the pace —
		 *    exactly as before.  What changes is that meanwhile the thread works.
		 *
		 * ⛔ And the fixed second stays a FLOOR, not a ceiling: an
		 *    answer arrived in 10 ms does not make `ADMITTED` go out in 10 ms,
		 *    because §4.4-bis wants the stopwatch not to distinguish what
		 *    the reason does not distinguish. */
		if (s->expected_verdict && now - s->cred_arrival > VERDICT_CAP) {
			/* ⛔ The safety net, and it counts as NO.  `cred_good` has been false
			 *    since `CREDENTIALS` arrived: one stops waiting.
			 * ⭐ And since 24 Oct 2026 (§4.4-bis B) an attempt WITHOUT a verdict
			 *    COUNTS AS FAILED: a PAM that «does not answer» is what an
			 *    attacker would try to produce, and the booking made at
			 *    `CREDENTIALS` must be resolved anyway.  (The helper's own
			 *    ceiling is 8 s, lower than this one: here we arrive only if
			 *    the helper itself did not deliver.) */
			s->expected_verdict = false;
			reg(s, "⛔ no verdict from the helper after %llu ms (ceiling %d): "
			       "REJECTED, and it COUNTS as a failed attempt of §4.4-bis "
			       "(an attempt without a verdict is not a free attempt)",
			    (unsigned long long)(now - s->cred_arrival), VERDICT_CAP);
			{
				struct sink k = {s, NULL, NULL};
				struct login_result r;
				login_resolve(s->address, s->user, false, now, &r);
				login_report(&k, s->address, s->user, false, &r, now);
			}
		}
		if (s->expected_verdict)
			return true; /* PAM is still answering, and meanwhile the thread turns */
		/* ⛔ `<=` and not `<`: `now` and `cred_arrival` are TRUNCATED milliseconds,
		 *    so a difference of 1000 can be 999.x real ms.  `[M]` 23
		 *    Sep 2026: 15 admitted out of 50 at 999 ms on gnome, 16 out of 50 on kde —
		 *    and the test client, which watches §4.4-bis, left saying
		 *    «less than a second» (C20 «I could not look» on gnome and kde).
		 *    The fixed second is a FLOOR: at most 1 ms more is paid. */
		/* ⛔ The byte first, because it decides the wait: `0x07` (PAM's no) waits for REJECT_FLOOR; a success, the
		 *    limiter's `0x08` and our own `0x0E` (refusal_is_ours: the check was not made) wait for FIXED_DELAY.
		 *    `cred_good` is final here (the verdict is in, `expected_verdict` is false). */
		uint8_t reason = s->cred_reason;
		if (s->refusal_is_ours && reason == RCP_WRONG_CREDENTIALS)
			reason = RCP_SESSION_UNSERVABLE;
		const uint64_t floor_ms = (s->cred_good || reason != RCP_WRONG_CREDENTIALS) ? FIXED_DELAY : REJECT_FLOOR;
		if (now - s->cred_arrival <= floor_ms)
			return true;
		reg(s, "the %s has passed (%llu ms)", floor_ms == REJECT_FLOOR ? "refusal floor" : "fixed second",
		    (unsigned long long)(now - s->cred_arrival));
		if (s->cred_good) {
			send_message(s, T_ADMITTED, NULL, 0);
			s->state = S_WAIT_ATTACH;
			s->since = now;
			reg(s, "admitted user=%s from=%s", s->user, s->provenance);
			return true;
		}
		/* ⛔⭐ A CHECK THE SERVER COULD NOT MAKE IS `SESSION_UNSERVABLE`, NOT
		 *     `WRONG_CREDENTIALS` — `DECISIONS.md` §11.39, the user's decision
		 *     of 15 Oct 2026 (option C).  The helper dead or down, the question
		 *     that did not leave: PAM never judged the password, so «wrong
		 *     password» was false and sent the owner to retype a right one.
		 *     §4.4 forbids telling «no such user» from «wrong password»; this
		 *     byte says neither — the check never happened, and it says no
		 *     more than the timing already says.
		 * ⚠ The road is `refusal_is_ours`, set ONLY by the two roads that
		 *   give the booking back without counting (`rcp_credentials()` when
		 *   the question did not leave, `rcp_verdict_lost()`), and only where
		 *   the reason is still `WRONG_CREDENTIALS`: the limiter's refusals
		 *   (`TOO_MANY_ATTEMPTS`, 0x08) never set it and keep their byte.
		 * ⛔ NOT here: «PAM could not judge» (`authentication.c`) is a PAM
		 *   answer, and the attempt WITHOUT a verdict (the helper's timeout,
		 *   `VERDICT_CAP`) COUNTS as failed since 24 Oct 2026 (§4.4-bis B):
		 *   both stay `0x07` and counted.  So on the wire «counted» is exactly
		 *   `0x07`, and «not counted and not the limiter's» is exactly `0x0E`.
		 *   Same fixed second, same count (none): only the byte changes.
		 * ⛔ ONE exception to «counted is exactly 0x07»: the no PAM gives while
		 *   `pam_faillock` has the account LOCKED, for a key with an admitted
		 *   login in the last 30 days (§11.47 B, `refusal_uncounted()`), is NOT
		 *   counted and still goes out as 0x07 — 0x0E would reveal that the
		 *   account exists. */
		/* `reason` was computed above, with the conversion, because the wait depends on it */
		if (s->refusal_is_ours) {
			reg(s, "⛔ and this REJECTED is OURS, not PAM's: the check was "
			       "not made — reason %#04x on the wire (§4.4, DECISIONS.md "
			       "§11.39), and the counters of §4.4-bis were NOT touched "
			       "(the booking was given back)",
			    reason);
		}
		reject(s, reason);
		return false;
	}

	/* ⛔ The silence: whoever has been silent for thirty seconds no longer holds the slot.
	 * ⚠ The connection stays open — see the box at the top.
	 *
	 * ⛔⭐ AND THE STATE CHANGES WITH THE SLOT — finding R9.2.  Here the slot was
	 *    left and `is_attached = false` was set, but the state stayed
	 *    `S_ACTIVE`: `rcp_state_name()` kept answering «active» — and
	 *    it is what the host queries — and `s->state != S_ACTIVE` is the only
	 *    guard of `BENCH_MARK`.  After a second client had got in,
	 *    the server had TWO «active» sessions for the same user, which is
	 *    precisely what I2 forbids.
	 *
	 *    ⚠ The box at the top declares a choice — leaving the connection
	 *      open — and it is defensible.  ⛔ But «not closing the connection» and
	 *      «staying active» are two different things, and the second was not
	 *      declared anywhere.  The way back from here is in
	 *      `rcp_receive()`: the slot is taken back if it is free. */
	/* ⛔⭐ AND `last_life` IS LOOKED AT, NOT `last_input` — the repair of 16
	 *     Aug 2026, and the long reason is on the field, at the top of the file.
	 *
	 * ⚠ `last_input` is the clock of USER INACTIVITY (30 minutes, §5.3), just
	 *   below.  ⛔ Keeping one only for two jobs is the defect we have just
	 *   paid for: it is not done again. */
	if (s->state == S_ACTIVE && s->is_attached &&
	    now - s->last_life > SILENCE) {
		slot_leave(s->user);
		s->is_attached = false;
		s->state = S_DETACHED;
		reg(s, "DETACHED for silence: %llu ms without a PACKET from %s — and "
		       "the last user gesture is from %llu ms ago (§5.3: here what counts is the "
		       "client that is silent, not the user who does not touch) "
		       "(slots taken now: %d; state: %s)",
		    (unsigned long long)(now - s->last_life), s->provenance,
		    (unsigned long long)(now - s->last_input),
		    taken_slots(), STATE_NAMES[s->state]);
		/* ⛔⭐ §7.3 NAMES SILENCE FIRST among the three ways in which «a
		 *     connection ends», and it is the worst case of the three: here the
		 *     client has said nothing and will say nothing more — it is the
		 *     phone dead in the tunnel — while the GRAPHICAL SESSION
		 *     survives (invariant I4).  A Ctrl pressed a moment before
		 *     the line dropped would stay pressed on the real desktop, and
		 *     the user would find it so on reattach.
		 * ⚠ And the RCP session is not over: here only the slot has been
		 *   left.  If it speaks again, `inp_released` is switched back on in
		 *   `rcp_receive()`/`rcp_receive_input()` together with the slot taken back. */
		release_on_detach(s, "silence of §5.3");
	}

	/* ⛔⭐ §5.3 — USER INACTIVITY, the second of the three clocks.
	 *
	 *     «30 minutes without input ⇒ REMOTIX detaches the client: getting back
	 *     in takes user and password.»  ⇒ It is a FAREWELL, not a detach for
	 *     silence: the connection closes with reason `0x02`, and the page
	 *     goes back to the login form.
	 *
	 * ⛔ And the order with the clock above is NOT indifferent: silence first.
	 *    A client that has stopped answering on the wire must be
	 *    declared detached — so whoever arrives gets in (§8.2) — and not
	 *    sent away for inactivity, which would mean «the user was there and
	 *    touched nothing».  ⚠ They are two different things and produce two
	 *    different sentences for whoever reads.
	 *
	 * ⚠ And `s->is_attached` is looked at: a session that does not hold the slot
	 *   has no user to declare inactive.  ⭐ The GRAPHICAL SESSION survives
	 *   anyway (I4): this farewell detaches the client, it does not close the
	 *   desktop — that is the THIRD clock, and it is another thing. */
	if (inactivity_ms && s->state == S_ACTIVE && s->is_attached &&
	    now - s->last_input > inactivity_ms) {
		char d[192];
		snprintf(d, sizeof d,
		         "%llu ms without user input (ceiling %llu): §5.3, and "
		         "getting back in takes user and password",
		         (unsigned long long)(now - s->last_input),
		         (unsigned long long)inactivity_ms);
		reg(s, "⭐ §5.3 — INACTIVITY: %s.  ⚠ The graphical session STAYS (I4): "
		       "the client is detached, the desktop is not closed",
		    d);
		dismiss(s, RCP_INACTIVITY, d);
		/* ⛔ `false` as for the other ceilings: the session is over, and the
		 *    caller must not keep working on it. */
		return false;
	}

	/* ⛔ §7.1 — the backstop of the `FIT_CANVAS` wait.  ⚠ It sits HERE, and not
	 *    where the frames arrive, for the lesson of `rule_heartbeat` (paid for
	 *    on 11 August with B6): a deadline that fires only when something
	 *    arrives is a deadline that never fires — and the case that matters is
	 *    precisely the one in which nothing arrives. */
	canvas_expires(s, now);

	uint64_t cap = 0;
	const char *which = NULL;
	if (s->state == S_WAIT_HELLO) {
		cap = CAP_HELLO;
		which = "HELLO";
	} else if (s->state == S_WAIT_CREDENTIALS) {
		cap = CAP_CREDENTIALS;
		which = "CREDENTIALS";
	} else if (s->state == S_WAIT_ATTACH) {
		cap = CAP_ATTACH;
		which = "ATTACH";
	}
	if (cap && now - s->since > cap) {
		char d[64];
		snprintf(d, sizeof d, "ceiling expired for %s", which);
		dismiss(s, RCP_TIMED_OUT, d);
		return false;
	}
	return true;
}
