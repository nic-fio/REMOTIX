/*
 * rcp.h — the RCP/1 handshake, server side.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHAT IT KNOWS AND WHAT IT DOES NOT KNOW
 *
 * This module knows `RCP.md` and **nothing else**: it does not know QUIC is
 * underneath, it does not know WebTransport is on top, it opens no socket and
 * does not look at the clock.  It receives bytes, returns bytes, and asks its
 * host to send them.
 *
 * ⭐ It is not aesthetic tidiness: it is the reason it will be able to move from
 *    the ngtcp2 example server to the real server without being rewritten — and
 *    the reason why `DECISIONS.md` §6.4, if it were reopened one day, would not
 *    take the protocol away with it.
 *
 * ---------------------------------------------------------------------------
 * ⛔ TIME COMES FROM OUTSIDE
 *
 * `RCP.md` §4.6 imposes three ceilings on the handshake, and §4.4-bis imposes a
 * **fixed delay of one second** before answering `CREDENTIALS` — even
 * when the answer is `ADMITTED`.  A module that called `clock_gettime()`
 * itself would be impossible to test: one would have to really **wait**.
 * Here the time is passed by the host, with `rcp_time()`, and a bench can
 * make it run as it likes.
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* The major version this module speaks — RCP.md §9. */
#define RCP_VERSION 1

/* ⛔⭐⭐ THE SESSION CAP — ONE NUMBER ONLY, AND IT LIVES HERE.
 *
 *     Until 25 Aug 2026 this number was written by hand in FOUR
 *     places, and ⛔ **three of those places declared in writing a link that
 *     the compiler did not know about**:
 *
 *       | where                      | what the comment said                 |
 *       |----------------------------|---------------------------------------|
 *       | `rcp.c` `MAX_ATTACCATE`    | (the original, `static`, never in this header) |
 *       | `child.c` `MAX_FIGLI`     | *«this one will follow it from the same place»* — and it did not |
 *       | `helper.c` `MAX_IN_FLIGHT` | *«it is the same `MAX_ATTACCATE` as `rcp.c`»* — and it was not |
 *       | `main.c` `QUANTI_PRESENTI` | (no declared link, same number by chance) |
 *
 * ⛔ `[M]` §6.4 proved it in the field: compiling the tree with
 *    `MAX_ATTACCATE=2`, `MAX_FIGLI` stayed **16** — that is the slot table
 *    filled up at two while the children table still accepted
 *    fourteen, **for users who would have been refused**.  ⇒ Four hand
 *    copies of the same number are the «second road» that `CODER.md` §2-bis
 *    forbids: four numbers that can diverge, and diverge in silence.
 *
 * ⭐ From here on the number is ONE, and whoever changes it changes it in one place.
 *    The quantities that follow it are all **«one per user served»**:
 *      · `rcp.c` `MAX_ATTACCATE`   — the slots of the session registry;
 *      · `child.c` `MAX_FIGLI`    — the processes/stages, one per user (I2);
 *      · `main.c` `QUANTI_PRESENTI`— the abandonment clock, one per user;
 *      · `webtransport.c` `WT_PALCHI` — the stage's canvas for the re-attach.
 *
 * ⛔⛔ And `helper.c` `MAX_IN_FLIGHT` does **NOT follow it, on purpose**: that is
 *      another quantity — the authentications **in flight at the same
 *      instant**, which are counted even when the active sessions are ZERO.
 *      The full reason sits next to that `#define`, because that is where
 *      someone will be tempted to tie it back.
 *
 * ⭐⭐ AND SINCE 25 AUG 2026 (evening) THE NUMBER IS **CONFIGURABLE** — phase 10,
 *     `--session-cap N`.  The `#define` below stays, and it is the
 *     **DEFAULT**; the value in force is told by `rcp_cap()`, and it is moved
 *     by `rcp_cap_set()` only once, at startup, before a session
 *     exists.  ⇒ The four tables are **allocated** on that number instead of
 *     being fixed-size arrays: `[M]` §3.3 had verified that the five
 *     functions that walk `attached[]` do **only linear scans** and
 *     that no invariant rests on the 16.
 *
 * ⛔⛔ AND THE DEFAULT WENT FROM 16 TO **10**, which is the number of
 *      `SPECS.md` §5.5 — the only one a document has ever promised.  The
 *      16 had not been chosen: it was the first convenient number of a
 *      «small» list, copied into four places.  ⚠ Whoever wants yesterday's
 *      sixteen types `--session-cap 16`, and the startup line declares it.
 *
 * ⚠ AND IT REMAINS AN **ADMINISTRATIVE** CAP, not a physical limit: whoever does
 *   not fit receives `0x0E` («the table is full»), not `0x06` («this machine has
 *   no more composition capacity»).  ⭐ The two ADD UP — §8.1 **D5** — and
 *   the gesture the user can make is different: *«try again, or ask for the
 *   cap to be raised»* versus *«try again, or come in asking for less
 *   quality»*.  The second is the budget, and it lives in `budget.h`. */
#define RCP_SESSION_CAP 10

/* The cap **in force**.  ⭐ Before anyone moves it, it is the default above:
 * whoever reads this function always has an answer, never a zero. */
int rcp_cap(void);

/* ⛔ Moves it, and **only once**: returns `false` — declaring it in the log
 *    — if the tables have already been allocated, because then there would be
 *    two numbers in force in the same process, which is exactly the «second
 *    road» that `CODER.md` §2-bis forbids. */
bool rcp_cap_set(int how_many);

/* ⭐ PHASE 18 — the video codecs the HERE_I_AM OFFERS («hevc,h264» · «h264» · «»),
 *    measured at startup by the parent (`child_video_capabilities()`), not written.
 *    ⛔ With «» every HELLO ends in NOTHING_IN_COMMON, declared.  The
 *    default («hevc,h264») serves only the bench harness. */
void rcp_video_codec_set(const char *listing);
const char *rcp_video_codec(void);

/* ⏳ `RCP.md` §13 (PROPOSED, `DECISIONS.md` §11.32, open): `PACE`.
 *
 * ⛔ OFF by default (I6: fewer frames is something the user SEES).  On only
 *    with `--decoder-pace`: then `HERE_I_AM` declares `video.pace=yes` — but
 *    only on sessions whose host connected the `pace` hook.  The startup line
 *    is written by `main.c`, on AND off. */
void rcp_pace_offer(bool on);
bool rcp_pace_offered(void);
/* The clamp of §13.5.  ⚠ `RCP_PACE_TOP_FPS` is the stage's own rate
 * (`MOTION_FPS` in `child.c`): a ceiling at or above it is no ceiling. */
#define RCP_PACE_FLOOR_FPS 5u
#define RCP_PACE_TOP_FPS 60u
#define RCP_PACE_GAP_MS 250u
uint16_t rcp_pace_clamp(uint32_t asked);

/* The reasons of §8.2.  Code 0 MUST NOT be used (§3.1). */
enum {
	RCP_CLOSED_BY_USER = 0x01,
	RCP_INACTIVITY = 0x02,
	RCP_SESSION_ABANDONED = 0x03,
	RCP_LOCAL_SESSION_PREVAILED = 0x04,
	RCP_ALREADY_ACTIVE_LOCALLY = 0x05,
	RCP_BUDGET_FULL = 0x06,
	RCP_WRONG_CREDENTIALS = 0x07,
	RCP_TOO_MANY_ATTEMPTS = 0x08,
	RCP_NOTHING_IN_COMMON = 0x09,
	RCP_INCOMPATIBLE_VERSION = 0x0A,
	RCP_PROTOCOL_ERROR = 0x0B,
	RCP_SERVER_CLOSING = 0x0C,
	RCP_TIMED_OUT = 0x0D,
	RCP_SESSION_UNSERVABLE = 0x0E,
	RCP_ALREADY_ACTIVE_REMOTELY = 0x0F,
	/* ⭐ 15 Aug 2026, `DECISIONS.md` §4.1-quater: the user has LOGGED OUT of the
	 * desktop («Log out»).  ⛔ It is NOT `0x01`: that is the wire dropping and
	 * it carries the promise «reattach and find everything again», which after a
	 * logout is false — the graphical session has ended and the programs are closed. */
	RCP_SESSION_TERMINATED = 0x10,
};

typedef struct rcp_session rcp_session;

/* ⛔⭐ The two NON-COUNT answers of the `input_release_all` hook (§7.3): the
 *     reason they exist is written on the hook, further below.  ⚠ They are
 *     negative on purpose, so a real count can never resemble them. */
#define RCP_RELEASE_NO_COUNT (-1)
#define RCP_RELEASE_IMPOSSIBLE (-2)

/* The hooks towards the host.  Three, and no more. */
typedef struct {
	void *ctx;
	/* Sends bytes on the control channel (the bidirectional stream the
	 * client opened first — §4.2). */
	void (*send_msg)(void *ctx, const uint8_t *data, size_t len);
	/* ⛔ §3.1 point 3: closes the WebTransport SESSION with the application
	 * error code equal to the reason code.  Not the QUIC connection: that one
	 * can carry other things, and a page cannot close it. */
	void (*close)(void *ctx, uint8_t reason);
	/* One line in the server log.  ⛔ §3.1 point 1: one writes WHAT was not
	 * understood, not «protocol error». */
	void (*record)(void *ctx, const char *line);
	/* Checks the credentials.  Separate because PAM has nothing to do with the
	 * protocol, and so that a bench can replace it by declaring it.
	 *
	 * (D4b of `DECISIONS.md` §11.50: the SYNCHRONOUS `verify` hook is GONE.  A
	 *  host without `ask_verify` has its logins refused as ours, `0x0E`, not
	 *  counted — see `rcp_credentials()`.) */
	/* ⭐ THE ASYNCHRONOUS CHECK — `DECISIONS.md` §1.10, 12 Aug 2026.
	 *
	 * ⛔ `verify` blocks whoever calls it, and in the product whoever calls it
	 *    is the server's only `poll` loop: `[M]` B8, 11 Aug 2026, **from 1.0 to
	 *    2.2 seconds** during which nobody else receives a packet.  This hook
	 *    instead **returns at once**: it asks a helper process for the check and
	 *    leaves a request number, and the outcome comes back through `rcp_verdict()`.
	 *
	 * Returns `false` if the question **did not leave**.  ⛔ And then
	 * the outcome is NO, at once and without appeal — invariant I3: failure is
	 * a no, not a maybe.
	 *
	 * ⚠ If it is NULL (D4b) there is no check at all: the login is refused as
	 *   ours (`0x0E`, not counted).  A bench that needs a login to succeed sets
	 *   this hook and calls `rcp_verdict()`. */
	bool (*ask_verify)(void *ctx, const char *user, const char *password,
	                        uint64_t *ticket);

	/* ------------------------------------------------------------------ */
	/* ⭐ THE FOUR HOOKS OF THE VIDEO CHANNEL — §2.5, §5.1, §6.2.
	 *
	 * ⛔ THEY ARE FOUR AND NOT ONE, and the reason is normative: §6.2 says that
	 *    **how the stream ends is part of the message** — FIN means
	 *    «complete frame», `RESET_STREAM` means «incomplete, throw it
	 *    away».  A single hook that «sends a frame» could not tell
	 *    the difference, and an abandoned frame and a complete one would again
	 *    look the same: it is the **E8** error shape, and on this
	 *    exact field it has already been paid for (finding R1.7, 9 Aug 2026).
	 *
	 * ⛔ AND THEY ARE **OPTIONAL**: if `video_open` is NULL this server has no
	 *    video channel, and `rcp_video_open()` returns
	 *    `RCP_VIDEO_NO_CHANNEL` instead of keeping quiet.  ⚠ «I have no video
	 *    channel» and «the frame did not leave» are two different facts
	 *    (`LESSONS.md` §1.9 rule 1), and the in-process benches of phase 1 have
	 *    no unidirectional streams to offer.
	 *
	 * ⚠ Whoever connects them connects ALL FOUR: a host that could
	 *   open and could not reset would not be able to honour §5.1, and the module
	 *   notices and refuses to open. */

	/* ⛔ §2.5: opens a **new unidirectional** stream, one **per
	 * frame**, from the server to the client.  ⛔ It is NOT the control
	 * channel: a `0x03` on the control channel is `PROTOCOL_ERROR`
	 * (§2.5, row `0x03`).  Returns `true` and fills `stream` with
	 * the identifier, or `false` if one cannot be opened right now —
	 * ⚠ and then nothing has been sent, which is better than half a frame.
	 *
	 * ⛔⭐ AND `remain` IS AN OUTPUT PARAMETER, NOT A LUXURY — §2.3, phase 3.
	 *
	 *     §2.3 imposes two DIFFERENT behaviours when the stream does not open:
	 *     a **delta** is thrown away, a **keyframe** waits.  The one that must
	 *     choose is this module, which knows whether the frame is a keyframe;
	 *     ⛔ but the number that explains why — how many streams the client
	 *     still grants — is known only by whoever holds the transport.  Without
	 *     bringing it back here, the log line §2.3 demands («and in
	 *     both cases it is written to the log») would say «it could
	 *     not be done» without saying how much is missing, that is the symptom
	 *     *«screen frozen, and no line saying why»* of finding R1.9.
	 *
	 *     ⚠ Whoever does not know writes `0` and the line will say so. */
	bool (*video_open)(void *ctx, int64_t *stream, uint64_t *remain);
	/* Writes bytes on that stream.  ⛔ `false` means «they did not get in»,
	 * and the caller RESETS: a stream missing a piece is not closed with FIN,
	 * because FIN means «complete» (§6.2). */
	bool (*video_write)(void *ctx, int64_t stream, const uint8_t *data,
	                     size_t len);
	/* ⛔ §6.2: FIN ⇒ the frame is **complete** and is handed to the
	 * decoder. */
	void (*video_fin)(void *ctx, int64_t stream);
	/* ⛔ §5.1, §6.2: `RESET_STREAM` ⇒ the frame is **incomplete**, the
	 * client throws it away, does NOT hand it over, and treats it as a gap. */
	void (*video_reset)(void *ctx, int64_t stream);

	/* ------------------------------------------------------------------ */
	/* ⭐ THE SIX HOOKS OF THE INPUT CHANNEL — `RCP.md` §7.3, and the signatures
	 *    are those of `src/input.h` field by field.
	 *
	 * ⛔⭐ WHY THEY ARE HOOKS AND NOT AN `#include "input.h"` — and it is not a
	 *     matter of style, it is the `Makefile`.
	 *
	 *     `src/input.h` says, in its header, that the one calling those
	 *     functions is `rcp.c`.  ⛔ But `rcp.c` exists in TWO folders —
	 *     `src/` and `benches/rcp/` — and the `Makefile` (variable `GEMELLATI`)
	 *     demands that the two copies match byte for byte.  The second
	 *     is copied by `benches/01-b3-graft-rcp.py` into
	 *     ngtcp2's `examples/`, where `input.h` **is not there and cannot
	 *     go**: that file lists exactly three names
	 *     (`rcp.c`, `rcp.h`, `authentication.c`).
	 *     ⇒ An `#include "input.h"` here does NOT compile the harness, that is it
	 *       switches off B3, B5, B6, B8 and B11 in one go.
	 *
	 * ⭐ And the shape of the hooks is the one this file already uses for the other
	 *    two things `rcp.c` cannot know: PAM (`verify`) and the
	 *    stream (`video_*`).  «It receives bytes, returns bytes, and asks its
	 *    host to act» — the header of this file, applied.
	 *
	 * ⛔ THEY ARE **OPTIONAL**, and their absence is NOT a violation by the
	 *    client: a server without an input channel **still validates** the
	 *    message (that is protocol, and §3 makes no discounts) and then writes
	 *    to the log that it did not inject it.  ⚠ «I have no input channel»
	 *    and «the client got it wrong» are two different facts, and closing the
	 *    session for the first would punish whoever did nothing wrong.
	 *
	 * ⚠ Whoever connects them connects ALL FIVE: `rcp.c` looks at the first and
	 *   if it is there demands the others, because a channel that can move the
	 *   pointer and cannot release a button leaves the desktop worse than
	 *   it found it.
	 *
	 * ⛔ THE RETURN VALUE IS THAT OF `input.h`, and it has THREE states, not
	 *    two: `0` delivered to the compositor · `-1` no · `1` — only for
	 *    `input_letter` — «that character CANNOT be produced with the
	 *    session's layout», which §7.3 requires to be written to the
	 *    log and forbids replacing with another letter or with silence. */
	int (*input_pointer)(void *ctx, uint32_t x, uint32_t y);
	int (*input_button)(void *ctx, uint16_t code, int pressed);
	/* ⛔⛔ THE SIGN IS NOT INVERTED HERE, AND IT IS NOT INVERTED IN `rcp.c`.
	 *
	 *     `RCP.md` §7.3 (box «The sign of the wheel», `[M]` 10 Aug
	 *     2026) requires the server to invert the vertical axis, and
	 *     `src/input.h` declares that the inversion happens **inside
	 *     `input_wheel()`, only once, in one place only**.  Inverting it
	 *     here too would cancel it, and the symptom — «the wheel goes the
	 *     wrong way» — is the E11 error shape that box exists to
	 *     avoid.
	 * ⚠ And half notches pass whole: 120 = one notch, 60 = half, and
	 *   `rcp.c` does NOT round. */
	int (*input_wheel)(void *ctx, int32_t axis_x, int32_t axis_y);
	int (*input_letter)(void *ctx, uint32_t character);
	int (*input_position)(void *ctx, uint16_t code, int pressed);
	/* ⛔⭐ §7.3, last paragraph: «On detach everything is released.  When a
	 *     connection ends — by farewell, by silence, by error — the
	 *     server MUST release every key and every button that are
	 *     pressed».  ⭐ `RCP.md` §11 calls it «the rule with the highest
	 *     harm/cost ratio of the document».
	 *
	 * ⛔ And the hook is HERE because the three ways in which «a connection
	 *    ends» are all three observed from inside this module, and from
	 *    nowhere else together: the farewell (`dismiss()`), the thirty-second
	 *    silence (`rcp_time()`), the error (`rcp_violation()`).
	 *
	 * ⚠ `input.h` assigns it to `child.c` too («calls
	 *   `input_release_all()` on detach»), and the two calls do not
	 *   quarrel: the function releases what APPEARS pressed and the second
	 *   time finds nothing to release — it returns 0.  ⛔ But the
	 *   duplicate must be coordinated, not endured: see the report
	 *   `fasi/rapporti/F4-A3-filo-input.md`.
	 *
	 * ⛔⛔⭐ AND THE ANSWER HAS THREE VALUES, NOT ONE — 16 Aug 2026, and it was
	 *      found by the first browser test of this rule.
	 *
	 *      It said «returns how many it released, so that the bench can
	 *      count them», and in the real product that count **cannot exist here**:
	 *      whoever presses and releases is the CHILD, another process, and the
	 *      answer does not come back.  ⇒ `webtransport.c` answered `0`
	 *      meaning «the request has left», and `rcp.c` wrote it to the
	 *      log as «0 were pressed».
	 *
	 *      `[M]` Measured: four detaches with the key and the button REALLY
	 *      down — the line said `0` and the child, two lines below, `2`.
	 *      ⛔ It is `LESSONS.md` §1.9 in the worst place: the rule with the
	 *      highest harm/cost ratio of the document had as its only witness one
	 *      that always said «nothing was down», that is **the face of green
	 *      on a release that had not happened at all**.
	 *
	 *   `>= 0`                     → the REAL count (known by whoever sews: in-process
	 *                                benches, `04-b23`, `04-b24`);
	 *   `RCP_RELEASE_NO_COUNT` → asked, and SOMEONE ELSE knows the count — one
	 *                                writes where to look for it, not a number;
	 *   `RCP_RELEASE_IMPOSSIBLE` → ⛔ it could NOT be asked: if something
	 *                                was pressed, **it stays pressed**. */
	int (*input_release_all)(void *ctx);

	/* ⭐⭐ THE CANVAS HOOK — §7.1 `FIT_CANVAS`, and `DECISIONS.md`
	 *     §5.0-sexies: *«the server's canvas asks for the size of the client's
	 *     canvas»*.
	 *
	 * ⛔ IT IS OPTIONAL, and its absence is NOT a defect of the client: a host
	 *    that does not connect it cannot resize, and §7.1 says what to
	 *    answer — `CANVAS(REFUSED, COMPOSITOR_UNABLE)`, which is true and
	 *    does not close the session.  ⚠ It is what the phase 1 benches did,
	 *    and it is what the product did until 15 Aug 2026.
	 *
	 * ⛔⭐ THE RETURN VALUE IS «THE QUESTION HAS LEFT», NOT «THE CANVAS HAS
	 *     CHANGED», and confusing the two is the defect this box exists to
	 *     avoid.  `[M]` 14 Aug 2026: asking labwc for the size the output
	 *     ALREADY HAS answers «succeeded» **without sending any
	 *     event**; and §4.5 allows the compositor to grant a size
	 *     different from the one requested.  ⇒ Whoever answers `true` is only
	 *     saying «I asked whoever is in charge».
	 *
	 * ⇒ The canvas in force changes — and `CANVAS` leaves — only when the
	 *   proof arrives: a frame at the new size, which the host brings back in
	 *   here with `rcp_tela_concessa()`.  ⛔ And if it does not arrive, the
	 *   `RCP_CANVAS_WAIT_MS` backstop takes care of it: §7.1 wants an answer anyway.
	 *
	 * ⚠ The size arriving here has already gone through `rcp_size_allowed()`:
	 *   range and parity are guaranteed, and the host does not check them again —
	 *   two rules on the same value in two places become two different rules
	 *   the day one of them changes. */
	bool (*recanvas)(void *ctx, uint32_t width, uint32_t height);

	/* ⛔⭐⭐ THE TWO LAYOUT HOOKS — `DECISIONS.md` §5-bis.7, decided
	 *      by the user on 8 Aug 2026 and CONFIRMED on the 16th: *«for keyboards
	 *      the same reasoning as for resolutions applies: at session creation or
	 *      re-attach the keyboard is renegotiated too»*.
	 *
	 * ⛔ Until 16 Aug 2026 that decision **had never been carried out**:
	 *    `ATTACH` validated the string and wrote it to the log, and there it
	 *    ended.  `[M]` (bench `06-b34`, case 2): reattaching to an `it` session
	 *    declaring `us`, `è` and `ò` arrived — which on `us` **exist on no
	 *    key**.  That is, the declared layout touched nothing.
	 *
	 * ⭐ And the real harm is NOT the convenience of two accents — `SPECS.md`
	 *    §7.3 and `DECISIONS.md` §5-bis.6: letters travel as **letters**,
	 *    but shortcuts travel as **positions**, and positions match only if
	 *    the two layouts are the same.  On a German keyboard the `Z` sits where
	 *    on ours the `Y` sits:
	 *    ⛔ **without renegotiating, `Ctrl+Z` lands on another key** — and the
	 *    symptom the user describes is «undo does not work», which nobody
	 *    connects to the layout.
	 *
	 * ⚠ They are OPTIONAL like the five of input, and for the same reason: a
	 *   server without a stage still validates the message (that is
	 *   protocol) and then DECLARES it did not apply it.  ⛔ «I have no
	 *   stage» and «the client got it wrong» are two different facts. */

	/* «Does this machine know this layout?» — ⛔ and the answer is known by
	 * **XKB**, not by a hand-written list.
	 *
	 *   `1`  yes          · `0`  no, and §4.5 wants `SESSION_UNSERVABLE`
	 *   `-1` ⛔ it could NOT be asked — and it is NOT «no»: it is declared.
	 *
	 * ⛔ Why it is a hook and not a call to `keyboard.c`: this file is
	 *    **twinned** with `benches/rcp/rcp.c`, which is compiled inside ngtcp2's
	 *    `examples/` — where `xkbcommon` is not there and cannot
	 *    go.  Same reason, and same shape, as the input hooks. */
	int (*layout_exists)(void *ctx, const char *name);

	/* «Put THIS layout in the session» — §5-bis.7 carried out.
	 *
	 * ⛔ The direction is this one and not the other: the letter is NOT
	 *    translated with a keymap of ours keeping the session as it is.
	 *    `keyboard.h` explains it and `keyboard.c` measures it: with our keymap
	 *    and their session **different characters** come out, which §7.3
	 *    forbids.  ⇒ The layout OF THE SESSION is changed, and then it is read
	 *    back from `libei` as it has always been done: `[M]` bench `06-b34`
	 *    case 2s measures that this round holds — device destroyed and
	 *    recreated, keymap reread, right character.
	 *
	 * `true` = the request has left.  ⚠ NOT «is in force»: who knows that is the
	 * child, and it writes it itself.  As for the release, a number invented here
	 * would be worse than no number. */
	bool (*layout)(void *ctx, const char *name);

	/* ⛔⭐⭐ «WHAT SIZE DOES THE STAGE HAVE NOW?» — and without this question the
	 *     RE-ATTACH is born with two truths.
	 *
	 * ⛔ THE CASE, and it is the one `DECISIONS.md` §5.0-sexies notes as
	 *    inevitable: the stage outlives the client (invariant I4) and the canvas
	 *    is born at every attach (§5.0).  ⇒ The user detaches from the DeX with the
	 *    canvas at 1912×1044 and reattaches from the laptop, where the page asks
	 *    for 1920×1080.  §4.5 would say to grant what is asked — ⛔ but the
	 *    stage keeps delivering 1912×1044, and §6.2 requires NOT sending a
	 *    frame whose size is not the canvas in force.  ⇒ **Zero pixels, and
	 *    no line saying why**, until someone moves the canvas.
	 *
	 * ⇒ One ASKS, instead of granting blindly: if the stage already has a
	 *   size, `SESSION` grants THAT one (§4.5 allows it explicitly, and the
	 *   page declares it in the log), and the session starts in agreement with
	 *   the world.  ⭐ Then the page sends its `FIT_CANVAS` and one gets where
	 *   one wanted — but passing through a state in which pixels arrive.
	 *
	 * ⛔ IT IS OPTIONAL: whoever does not connect it grants what the client asks,
	 *    which is exactly the behaviour before 15 Aug 2026.
	 *
	 * `false` = «I do not know» — no stage, or no frame yet.  ⚠ It is not
	 * «0x0»: the difference is the same as for `rcp_canvas_in_effect()`. */
	bool (*stage_canvas)(void *ctx, uint32_t *width, uint32_t *height);

	/* ⛔⭐ «DOES THIS USER ALREADY HAVE A LOCAL GRAPHICAL SESSION?» — §5.1 of
	 *     `SPECS.md`, reason `0x05 ALREADY_ACTIVE_LOCALLY`.
	 *
	 * ⛔ IT IS A HOOK AND NOT A CALL TO logind, for the same reason as the
	 *    six of input: `rcp.c` exists in TWO folders and the copy in
	 *    `benches/rcp/` is grafted inside ngtcp2's `examples/`, where there is
	 *    neither `gio-2.0` nor a system bus.  An `#include <gio/gio.h>`
	 *    here would switch off B3, B5, B6, B8 and B11 in one go.
	 *
	 * ⛔ IT IS OPTIONAL, and its absence is NOT a violation by the client: whoever
	 *    does not connect it does not apply the rule of §5.1, and ⛔ `rcp.c` WRITES
	 *    IT TO THE LOG instead of keeping quiet (`CODER.md` §4.2: the fallback is
	 *    declared).  ⚠ A rule that is not there and a rule that says «no» are
	 *    two different facts, and in the log they must stay so.
	 *
	 * `description` — if not NULL — receives which session it is, for the
	 * server log.  ⛔ It does NOT end up in the body of the farewell: §8.2 forbids
	 * telling the client the facts of other people's sessions.
	 *
	 * Returns `true` if a **local** graphical session of that user
	 * exists right now. */
	bool (*session_local)(void *ctx, const char *user, char *description,
	                        size_t how_much);

	/* ⛔⭐ «THE USER HAS ASKED TO LEAVE» — `RCP.md` §7.6, `TERMINATE_SESSION`.
	 *
	 * ⛔ It is the other half of `DECISIONS.md` §4.1-ter: the wire dropping leaves
	 *    the session alive (I4), this ENDS it — and with it the user's
	 *    programs close.
	 *
	 * ⚠ Called AFTER the `0x10` farewell has left, and the order is
	 *   normative: when the compositor falls, the stage falls with it and the
	 *   channel is no longer needed.  A `0x10` sent afterwards is finding B-7
	 *   under a new name.
	 *
	 * ⛔ IT IS OPTIONAL: whoever does not connect it cannot needs §7.6, and does
	 *    `rcp.c` answer `PROTOCOL_ERROR`? ⚠ NO — it sends the farewell all the
	 *    same with `0x10` and writes to the log that the session was not touched.
	 *    «The client got it wrong» and «this server cannot do it» are two
	 *    different facts, and punishing the client for the second would be
	 *    punishing whoever did nothing wrong. */
	/* ------------------------------------------------------------------ */
	/* ⭐⭐ THE FIVE CLIPBOARD HOOKS — `RCP.md` §7.4, §5.4, §2.5.
	 *
	 * ⛔ THEY ARE FIVE AND NOT ONE, and the division follows that of the protocol:
	 *    three look at the WIRE (opening a stream, writing on it, closing it) and
	 *    two look at the SESSION (offering, answering).  A single hook that
	 *    «sends the clipboard» could not tell the two directions apart,
	 *    and the two directions are not symmetric: on one side one announces,
	 *    on the other one pulls.
	 *
	 * ⛔ AND THEY ARE **OPTIONAL**: a host that does not connect them has no
	 *    clipboard, and ⛔ `rcp.c` WRITES IT TO THE LOG instead of keeping quiet.
	 *    ⚠ «This server has no clipboard» and «the client got it wrong» are two
	 *    different facts: an `CLIPBOARD_ANNOUNCE` arriving at a server without a
	 *    channel is still VALIDATED — that is protocol, and §3 makes no
	 *    discounts — and then one declares it was not served.
	 *
	 * ⚠ Whoever connects them connects ALL FIVE: `rcp.c` looks at the first and
	 *   if it is there demands the others.  A channel that could announce and
	 *   could not answer whoever pastes would leave **the pasting application
	 *   hanging** — and the symptom is «the desktop froze».
	 *
	 * ⛔⭐ AND WHY THE `video_*` ARE NOT REUSED, though they open the same kind
	 *     of stream: `video_open` remembers which stream it opened, because §5.1
	 *     makes it reset **the previous one** when a more recent one leaves.  A
	 *     clipboard transfer that went through there would become the
	 *     «previous frame» of the next one — that is it would be reset
	 *     halfway by a rule that does not concern it. */

	/* ⛔ §2.5: opens a **new unidirectional** stream from the server to the
	 * client.  ⚠ `false` = «not now», and then not a byte has left —
	 * better than half a message.  `remain` receives how many streams the client
	 * still grants, as for video, and whoever does not know writes `0`. */
	bool (*clipboard_open)(void *ctx, int64_t *stream, uint64_t *remain);
	/* Writes bytes on that stream.  `false` = «they did not get in». */
	bool (*clipboard_write)(void *ctx, int64_t stream, const uint8_t *data,
	                       size_t len);
	/* ⛔ Closes the stream with FIN: the transfer is over.  ⚠ Unlike
	 * video, here FIN is not a statement about the content — the length
	 * is already in the framing of §6.1 — it is the end of the transfer. */
	void (*clipboard_fin)(void *ctx, int64_t stream);

	/* ⭐ «THE CLIENT HAS COPIED SOME TEXT»: offer it to the session.
	 *
	 * ⛔ It does NOT carry the text, and it is the «one announces and then pulls»
	 *    of §7.4: the text will be asked of whoever has it when someone really
	 *    pastes.
	 * `true` = the request has left.  ⚠ NOT «the session has it»: who knows that
	 * is the compositor, and whoever sews things together writes it. */
	bool (*clipboard_offer)(void *ctx);

	/* ⭐ The answer to whoever, inside the session, is pasting.  `text` NULL =
	 * «I do not have it», ⛔ **which is an answer all the same** and is the one that
	 * unblocks whoever is pasting.  `serial` is the number the session gave to
	 * its request, and it comes back as is. */
	bool (*clipboard_response)(void *ctx, uint32_t serial, const char *text,
	                         size_t byte);

	void (*terminate_session)(void *ctx);

	/* ⭐ `SESSION` TELLS THE TRUTH — defect D-001, phase 15 (25 Sep 2026).
	 *
	 * ⛔ Since phase 1 `SESSION` sent a FIXED `1 = NEW` and `«sconosciuto»`,
	 *    even to whoever came back into their desktop and on any desktop: the
	 *    page wrote «new session, unknown desktop» to everyone.
	 *
	 * `session_resumed` — `true` if this user's stage WAS ALREADY THERE when
	 *   PAM admitted them (§4.5: `2 = RESUMED`).  ⚠ The fact is known at the
	 *   verdict, not at `SESSION`: by that point the newborn child is already
	 *   there, and asking there would say «resumed» to everyone.
	 * `desktop` — one of the names of §4.5 (`gnome · kde · xfce · lxqt ·
	 *   sconosciuto`).
	 *
	 * ⛔ OPTIONAL, like the others: whoever does not connect them (the wire
	 *    benches, where there is no stage) sends what it sent before — `NEW` and
	 *    `sconosciuto` — which for them is true. */
	bool (*session_resumed)(void *ctx);
	const char *(*desktop)(void *ctx);

	/* ⏳ `RCP.md` §13, PROPOSED and not normative — `PACE`: «the client's
	 *    decoder is behind, do not send me more than `max_fps` frames per
	 *    second».  `max_fps` arrives ALREADY CLAMPED (0 = no ceiling, or
	 *    `RCP_PACE_FLOOR_FPS..RCP_PACE_TOP_FPS - 1`), at most once per
	 *    `RCP_PACE_GAP_MS`, and 0 again when the session ends.
	 * ⛔ OPTIONAL: without it the server does not declare `video.pace`, so no
	 *    client may send `PACE` — the wire stays today's. */
	bool (*pace)(void *ctx, uint16_t max_fps);
} rcp_hooks;

/* Opens an RCP session on a newborn control channel.
 * `provenance` is the address of whoever connects: it serves the per-address
 * counter of §4.4-bis and the log.  `now_ms` is a monotonic clock. */
rcp_session *rcp_open(const rcp_hooks *g, const char *provenance,
                       uint64_t now_ms);

/* Closes and frees.  If the session was attached, frees the slot. */
void rcp_free(rcp_session *s);

/* Bytes arrived on the control channel.
 * Returns false if the session has ended (by farewell or by violation). */
bool rcp_receive(rcp_session *s, const uint8_t *data, size_t len,
                uint64_t now_ms);

/* Makes time pass: the ceilings of §4.6 and the fixed delay of §4.4-bis.
 * Returns false if the session has ended. */
bool rcp_time(rcp_session *s, uint64_t now_ms);

/* ⭐ The outcome of the asynchronous check comes back through here —
 * `DECISIONS.md` §1.10.
 *
 * ⛔ Returns `true` only if the request belonged TO THIS session and the
 *    session was really waiting for it.  The host uses it to recognise whom to
 *    deliver to: it passes the request to all live sessions, and only one
 *    takes it.  ⚠ A request that finds nobody **is lost, and rightly so**:
 *    it means the connection died while PAM was answering.
 *
 * ⛔ And the count of §4.4-bis moves HERE, no longer when `CREDENTIALS` arrives:
 *    it is here that one knows whether the attempt failed.
 *
 * ⚠ It sends NOTHING on the wire: `ADMITTED`/`REJECTED` go out from `rcp_time()`,
 *   because the fixed delay of §4.4-bis must have expired — and the verdict,
 *   now, can arrive before or after it. */
bool rcp_verdict(rcp_session *s, uint64_t ticket, bool admitted,
                  uint64_t now_ms);

/* ⛔ §8.1: whoever closes MUST send `FAREWELL` with a reason BEFORE closing the
 * WebTransport session, and MUST repeat the reason in the application error
 * code of the close (§3.1).  This function travels both roads; the §8.2
 * reason is chosen by the host, because only it knows why it is closing.
 *
 * ⭐ The case it was born for (finding B-7, night of 10 Aug 2026): the server
 *    shutting down, that is `RCP_SERVER_CLOSING`.  That reason was defined
 *    above and no line of the product emitted it: whoever was connected
 *    waited the 30 s of inactivity and read «network error».
 *
 * ⚠ On a session already ended it does nothing and it is not an error: sending
 *   a second reason for the same fact would tell two truths about the same thing. */
void rcp_dismiss(rcp_session *s, uint8_t reason, const char *detail);

/* ⛔ §2.5: a violation detected by the host — one stream too many, a
 * channel in the wrong direction — closed as §3.1 says.  The host sees the
 * streams; only this module knows how to close. */
void rcp_violation(rcp_session *s, const char *detail);

/* ⛔ §4.2: the control channel has closed, and its closing IS the end of
 * the session — EVEN when the one closing it was the server.  The host is
 * the only one that sees the FIN; only this module knows what it entails.
 *
 * ⚠ The session is NOT freed: it stays alive to observe the bytes that §4.2
 *   forbids the client to send after the end.  What is left is the SLOT. */
void rcp_channel_closed(rcp_session *s);

/* ⭐ §3.1 point 3: the reason also travels in the close code, and only the host
 * sees that road.  To judge it one needs to know whether the session had
 * already ended when the code arrived — because it is exactly there that the
 * client's `FAREWELL` could no longer go through the channel. */
bool rcp_is_finished(const rcp_session *s);
/* `ADMITTED` was sent and the session is not over (wait-attach, active,
 * detached): before that the user name is only the one claimed at CREDENTIALS. */
bool rcp_logged_in(const rcp_session *s);

/* ⛔ §4.2: the page has closed the WebTransport session, and said so with the
 * reason inside the close.  The slot (§8.2 reason 0x0F) is left HERE:
 * waiting for the transport to finish tearing down keeps it taken against
 * whoever reconnects right away. */
void rcp_closed_by_client(rcp_session *s, uint8_t code);

/* For the bench and for the log.
 *
 * ⚠ The names are: `wait-hello` · `wait-credentials` · `wait-verdict` ·
 *   `wait-attach` · `active` · `detached-by-silence` · `finished`.
 *
 * ⛔ `detached-by-silence` is from 10 Aug 2026, finding R9.2: a session
 *    that has been silent for thirty seconds has left the slot (§8.2 reason 0x0F)
 *    and **is no longer active**.  Before, it stayed `active`, and the server
 *    ended up with two «active» sessions for the same user — what invariant I2
 *    forbids.  Whoever compares this string must know the case exists; if it
 *    speaks again and the slot is free, the session goes back to `active` by itself. */
const char *rcp_state_name(const rcp_session *s);
/* ⭐ True when THIS session still waits for PAM's answer to `ticket` — the
 *    session `rcp_verdict()` would hand it to.  For `main.c`: a yes nobody waits
 *    for any more (the client hung up, the session finished while PAM judged)
 *    must not start a desktop for nobody. */
bool rcp_awaits_verdict(const rcp_session *s, uint64_t ticket);
/* ⭐ §11.47 B (`DECISIONS.md`, 15 Oct 2026): the «no» about to be delivered for
 *    `ticket` (through `rcp_verdict()` or `rcp_orphan_verdict()`) was given
 *    while `pam_faillock` had the account LOCKED.  The host (`helper.c`) sets
 *    it just before ONE delivery and calls it with 0 just after.  Such a no is
 *    NOT counted towards the ban (the booking is given back) when its key had
 *    an admitted login in the last 30 days (the notion of the places kept for
 *    a known key), and counts as any other otherwise.  The wire does not change. */
void rcp_refusal_locked(uint64_t ticket);
/* ⭐ 1.5 (`DECISIONS.md` §11.50, D4b): the «no» about to be delivered for
 *    `ticket` is the helper's «not checked» (its dispatcher's cap, a fork that
 *    failed, a helper that died or is down): set just before ONE delivery, 0
 *    just after, like `rcp_refusal_locked()`.  Such a no is refused as OURS at
 *    the fixed second — `0x0E`, never counted, the booking given back —
 *    instead of waiting for the 12 s net.  An orphan (the client hung up) is
 *    given back the same way. */
void rcp_refusal_unchecked(uint64_t ticket);

/* ⭐ THE TWO PAM SLOTS KEPT FOR A KNOWN KEY — 15 Oct 2026, `DECISIONS.md`
 *    §11.39 addendum.  True ONLY while `rcp.c` is inside `ask_verify` for
 *    credentials whose key (§4.4-bis: IPv4 address or IPv6 /64) had an ADMITTED
 *    login during the last 30 days (`GOOD_AGE`, kept in memory: a restart
 *    forgets it); false at every other instant.  `helper.c` reads it in
 *    `helper_ask()`: an unknown key may take 14 of the 16 checks in flight, a
 *    known one all 16 — so a flood from fresh addresses cannot keep the owner out. */
bool rcp_asking_for_known_key(void);
const char *rcp_user(const rcp_session *s);

/* ⛔⭐ THE CLIENT'S DECODER CEILING — `video.max_size` of §4.3,
 *     and until 25 Aug 2026 **it did not leave this module**.
 *
 * ⭐ It serves the BUDGET (phase 10), and it is the piece it was missing: at
 *    `delivery_verdict()` the session's canvas **is not decided yet** (it is
 *    decided at `SESSION`), but its **ceiling** is known from the `HELLO` —
 *    §4.5 requires the granted canvas not to exceed this number.  ⇒ Counting the
 *    ceiling one counts an **upper bound** of the cost of the newcomer, which is
 *    the uncomfortable direction, that is the right one (`LESSONS.md` §1.33).
 *
 * ⚠ Returns `false` when the client **did not declare it**, and it is not the
 *   same thing as «declared it zero»: whoever receives `false` falls back on the
 *   stage's canvas, and not on a zero. */
bool rcp_max_size(const rcp_session *s, uint32_t *l, uint32_t *a);

/* ⛔⭐ §5.3 — «the client is still there»: the TRANSPORT calls it after every
 *     DECRYPTED AND AUTHENTICATED packet, and the thirty-second clock depends on
 *     it.  ⚠ Not on the last user gesture: that is the clock of *user
 *     inactivity*, which is thirty MINUTES and not thirty seconds.  The long
 *     reason — and the measurement that imposed it — is on the field
 *     `last_life` in `rcp.c`. */
void rcp_sign_of_life(rcp_session *s, uint64_t now_ms);

/* ⛔⭐ §5.3 — THE SECOND CLOCK: «30 minutes without input ⇒ REMOTIX detaches the
 *     client, and getting back in takes user and password».  The farewell goes
 *     out with reason `0x02 INACTIVITY` of §8.2.
 *
 * ⚠ CONFIGURABLE because §5.3 demands it — *«the second and the third are
 *   configurable, with those values as defaults»* — and **0 means
 *   off**: whoever watches a video for hours on their own machine does not want
 *   to be thrown out.  ⛔ Whoever sews things together MUST write the value in
 *   force to the log: a half-hour ceiling nobody can read is tested only by
 *   waiting half an hour, and that is the way never to test it. */
void rcp_inactivity_set(uint64_t ms);
uint64_t rcp_inactivity(void);

/* ⛔⭐⭐ THE GHOST EVICTION — phase 9, 23 Aug 2026.  ⚠ It is NOT a fourth
 *      clock of §5.3: it is a shortcut inside the first, and it fires ONLY
 *      when a client of the same user is asking for that slot.
 *
 * If the occupant of a slot has been silent for longer than this threshold, the
 * slot is taken from it and goes to whoever arrives; the occupant ends up in the
 * same state the thirty-second silence puts it in (`staccata`), and if it speaks
 * again it is told so with `0x0F` — and that time the sentence is true.
 *
 * ⭐⭐ SINCE 24 AUG 2026 THE DEFAULT IS **15 000 ms**, that is ON —
 *     the user's decision, after having looked (§19.6, §20.3).  ⛔ `0` =
 *     OFF, and it is the only way to switch it off: `--eviction-ms 0`.  ⚠ Until
 *     23 August the default was `0` for invariant I6.
 * ⚠ `[M]` 23-24 Aug 2026: the ghost goes from 32.13 s / 14 refusals to 16.83 s /
 *   7 refusals.
 * ⚠ The RECOMMENDED value is given by `rcp_eviction_recommended()` — 15 000 ms,
 *   that is half of the silence clock — and the reason (the browser's keep-alive,
 *   `[M]` 15 s) is in the box above `DEFAULT_EVICTION` in `rcp.c`.  Below
 *   that number one risks evicting an ALIVE and still client, that is
 *   switching off invariant I2.
 * ⛔ Whoever sews things together MUST write the value in force to the log, on
 *   or off: a threshold nobody can read is the E1 shape. */
void rcp_eviction_set(uint64_t ms);
uint64_t rcp_eviction(void);
uint64_t rcp_eviction_recommended(void);

/* ⛔ Resets the registry of active sessions.  It serves ONLY the bench, between
 * one test and the next: in a real server nobody calls it. */
void rcp_reset_session_log(void);

/* ========================================================================= */
/* ⭐ THE VIDEO CHANNEL — `RCP.md` §2.5, §5.1, §5.2, §6.2                     */
/*                                                                           */
/* ⛔ WHY IT LIVES HERE AND NOT IN A MODULE OF ITS OWN                        */
/*                                                                           */
/* Seven of the eleven rules of the video channel do not speak of the 28      */
/* bytes: they speak of the **state of the session**.  «No stream before      */
/* having sent `SESSION`» (§2.5) is the state; «`w.`/`height` are the   */
/* canvas in force» (§6.2) is the canvas granted by `SESSION` or by the last */
/* `CANVAS`; «`codec` MUST be the negotiated one» is §4.3; «the first frame     */
/* MUST be a keyframe» (§5.2) is the first **after `SESSION`**; and          */
/* `REQUEST_KEY` arrives on the control channel.                          */
/*                                                                           */
/* ⇒ A separate `video.c` would have to **copy** that state, and two copies   */
/*   of a state diverge: it is the same reason `RCP.md` §0 exists for,        */
/*   applied inside a single program.  ⭐ And it has a second effect, which   */
/*   shows in the `Makefile`: **zero lines to add**, because `rcp.c` is       */
/*   already compiled and already compared with `benches/rcp/` at every build. */
/*                                                                           */
/* ⛔ AND WHAT THIS MODULE DOES NOT DO, DECLARED: it does not look **inside** */
/*    the codec bytes.  §5.2 wants the keyframe to be a **real** keyframe —   */
/*    VPS/SPS/PPS in front of the IDR — and that half can be judged only by   */
/*    whoever knows HEVC/AV1.  Here it is declared instead of passed off as   */
/*    covered.                                                                */

/* The outcomes of `rcp_video_open()` and of `rcp_video_send()`.
 * ⛔ They are SEVEN and not two, because the facts are seven: the caller must be
 *    able to tell «re-encode smaller» from «send me a keyframe» from «you
 *    have not sent `SESSION` yet».  A single `false` would put them under the
 *    same label, which is the E2 error shape. */
enum {
	RCP_VIDEO_SENT = 0,
	/* the four hooks are not there: this server has no video channel */
	RCP_VIDEO_NO_CHANNEL,
	/* ⛔ §2.5 / invariant I3: `SESSION` has not left yet */
	RCP_VIDEO_BEFORE_SESSION,
	/* ⛔ §5.2: a KEYFRAME is needed — the first after `SESSION`, the first at the
	 * new size after a `CANVAS`, or the one the client asked for */
	RCP_VIDEO_NEEDS_KEY,
	/* ⛔ §6.2: beyond 16 MiB.  One RE-ENCODES at lower quality — it is not
	 * sent, and not a byte has left */
	RCP_VIDEO_TOO_LARGE,
	/* a stream could not be opened right now: nothing has left */
	RCP_VIDEO_STREAM_NOT_OPEN,
	/* the write broke halfway: the stream was RESET (§6.2), and the
	 * client will treat it as a gap — never as a short frame */
	RCP_VIDEO_BROKEN_MIDWAY,
	/* there is already a frame open on this session: that one is finished or
	 * abandoned first */
	RCP_VIDEO_ALREADY_OPEN,
};

/* ⛔ OPENS THE FRAME and writes the **28 bytes** of §6.2 into it.
 *
 * `key`      §5.2: `0x0301` if true, `0x0302` if false.
 * `length`   how many bytes of DATA will follow.  ⛔ It is declared **first**,
 *               and it is not a convenience: §6.2 says «the ceiling binds first
 *               of all the sender», and a ceiling checked while the bytes go out
 *               would already have sent the first 16 MiB.  Whoever encodes
 *               has the length of the access unit.
 * `instant_us`  microseconds of the **server's monotonic clock** at
 *               capture (§6.2).  ⚠ It is not a time of day.
 * `input`       the identifier of the last input injected before the
 *               capture, 0 if none (§6.2, §7.3).
 * `now_ms`      the session clock, as for `rcp_receive()`.  ⛔ It is a separate
 *               parameter and is NOT derived from `instant_us`: that is the
 *               capture clock, and that the two are the same is likely and
 *               written nowhere.  It serves the 200 ms of §5.2 (exception 5
 *               of §3).
 *
 * ⛔ AND WHAT IS **NOT** PASSED IS THE POINT: `w.`, `height`, `codec` and
 *    `nr` are not parameters.  This module sets them, from the canvas in
 *    force (§4.5, §7.1), from the negotiation of §4.3 and from its own counter
 *    (§6.2).  ⭐ So the three rules cannot be violated **by construction**
 *    instead of by the caller's discipline — which is invariant I7 read from
 *    inside: the protection lives in the program, not in a line that can get
 *    lost. */
int rcp_video_open(rcp_session *s, bool key, size_t length,
                   uint64_t instant_us, uint32_t input, uint64_t now_ms);

/* Writes a piece of the data of the open frame.  ⛔ If they do not get in, the
 * stream is RESET in here (§6.2) and `RCP_VIDEO_BROKEN_MIDWAY` is returned:
 * a half frame closed with FIN would be a complete frame for the receiver. */
int rcp_video_piece(rcp_session *s, const uint8_t *data, size_t len);

/* ⛔ §6.2: closes with **FIN**, and only if the declared `length` bytes have
 * all gone out.  If some are missing, it resets and returns
 * `RCP_VIDEO_BROKEN_MIDWAY`: «FIN» is a statement, not a way of closing. */
int rcp_video_finish(rcp_session *s);

/* ⛔ §5.1: abandons the open frame with `RESET_STREAM`, because a more recent
 * one has already left.  ⛔ And §5.2 forbids abandoning a **keyframe**: here it
 * is refused and `false` is returned — «abandoning the cure is not a cure».
 * ⛔ Every abandonment ends up in the log (§5.1): «a frame lost in silence and
 * one abandoned on purpose look the same from the receiving side». */
bool rcp_video_abandon(rcp_session *s, const char *why);
/* ⛔⭐ §5.1 — THE ABANDONMENT OF A FRAME ALREADY CLOSED WITH FIN BUT STILL
 *     QUEUED, that is **the scene §5.1 really describes**: «the server MAY
 *     call `RESET_STREAM` on a frame that is no longer needed — because a more
 *     recent one has already left — and the bytes not yet sent do not
 *     leave at all».
 *
 * ⛔ It is not the same thing as `rcp_video_abandon()`, and the two cannot be
 *    merged: that one abandons the **open** frame, still missing a piece to
 *    write; this one abandons a **finished** one, which for RCP has already left
 *    and for the transport is still sitting in the queue.  Only whoever holds the
 *    queue knows it; only this module must write the line, count and switch the
 *    keyframe debt back on.  ⇒ The cut passes through here.
 *
 * `key` is passed by the caller because §5.2 forbids abandoning a keyframe
 * **downstream too**: here it is refused, written, and `false` is returned.
 * `unsent_bytes` goes into the line: «I threw it away before spending
 * bandwidth» and «I had almost sent it already» are two different facts. */
bool rcp_video_abandoned_downstream(rcp_session *s, uint32_t nr, bool key,
                                   size_t unsent_bytes, const char *why);

/* ⛔ §2.3 — the mandatory line for when the stream **does not open**: «and in
 * both cases it is written to the log».  `rcp_video_open()` calls it by
 * itself; it is here so that a bench can name it. */
void rcp_video_no_credit(rcp_session *s, bool key, uint64_t remain);

/* ⛔⭐⭐ THE ALREADY ENCODED FRAME THAT DOES NOT LEAVE — and whoever throws it
 *      away MUST go through here, always.
 *
 * It is the **third form** of §5.1, the one `RCP.md` calls «not observable
 * at all»: no stream opened, no byte gone out, and the `nr` not
 * consumed ⇒ the client gets a numbering **without gaps**, and §5.2 makes it
 * ask for a keyframe only on a gap.  ⛔ No counter, neither its nor ours,
 * can see this discard: the log line and the keyframe debt are
 * the only cure, and this function calls it.
 *
 * ⚠ It is NOT `rcp_video_abandoned_downstream()`: that is form A (stream
 *   reset, bytes already spent) and it would write to the log one form in place
 *   of another.  ⚠ And it does NOT touch `video_abandoned`, for the reason the
 *   box of `rcp_video_no_credit()` declares: on the wire there is nothing
 *   to reset.
 *
 * ⛔ THE TWO CALLERS, as of 23 Sep 2026, and both are in
 *    `webtransport.c` because it is the one that decides whether a frame leaves:
 *      · the RATE REGULATOR of phase 9 (`rate_brake()` ⇒ `true`);
 *      · the CANVAS THAT DOES NOT MATCH (§6.2), the frame captured at a size
 *        that is not the one in force.
 *    ⚠ A third branch that throws away an already encoded frame without calling
 *      this function redoes the defect of 23 Sep 2026 in full. */
void rcp_video_discarded_before_wire(rcp_session *s, bool key,
                                       const char *why);

/* How many frames this session has sent and how many it has abandoned.
 * ⛔ The two numbers together, always: «zero abandoned» on its own does not
 * tell a line that carries from a channel that has never sent anything. */
void rcp_video_counts(const rcp_session *s, uint32_t *shipped,
                     uint32_t *abandoned);

/* The convenience: opens, writes and closes in one call.  ⛔ The 16 MiB ceiling
 * is applied BEFORE opening the stream, so on a frame too large
 * not a byte leaves and nothing is opened. */
int rcp_video_send(rcp_session *s, bool key, const uint8_t *data,
                       size_t len, uint64_t instant_us, uint32_t input,
                       uint64_t now_ms);

/* ⛔ §7.1 — `CANVAS(FITTED, lar, h)` has just been answered: from here on the
 * canvas **in force** is this one, and §6.2 binds to it the `w.`/`height`
 * of every following frame.
 *
 * ⛔ And if the size has REALLY changed it opens the debt of §5.2: the first
 *    frame at the new size MUST be a keyframe.  ⚠ If the size does **not**
 *    change the debt is NOT opened — §7.1 makes one answer `CANVAS` even to an
 *    `FIT_CANVAS` asking for the size in force, and opening the debt there
 *    would stop the video on a healthy session every time the user drags a
 *    window and puts it back where it was.
 *
 * ⚠ The one answering `CANVAS` is not this module: the answer needs a
 *   compositor that can resize, and `FIT_CANVAS` is not served yet
 *   (see the log of `rcp_receive`).  This function exists so that the day it
 *   is, the rule of §6.2 lives **in one place only** — here — instead of
 *   being copied next to whoever sends the `CANVAS`. */
/* ⛔⭐⭐ THE SIZE ALLOWED FOR THE CANVAS — §7.1, and it lives HERE because the
 *      one who must apply it is whoever reads `FIT_CANVAS` from the wire.
 *
 * ⛔⛔ NOBODY ELSE SETS THE CEILING, and above the ceiling there is no error:
 *     there is a **silent death**.  `[M]` 14 Aug 2026, measured on the real
 *     compositors:
 *
 *       · beyond **16384** per side `gnome-shell` DIES («Failed to create
 *         texture 2d») — and 16386 is INSIDE the `MAX_SIZE` that Mutter
 *         **declares**, that is the declared limit lies;
 *       · on labwc `32768x32768` kills the compositor with **zero log
 *         lines**, even in verbose mode.
 *
 * ⇒ With the fixed-size canvas no client could get there.  Since
 *   `DECISIONS.md` §5.0-sexies the client ASKS for the size ⇒ any client
 *   could switch off the session of its host, and the guard
 *   becomes mandatory.
 *
 * ⛔⭐⭐ AND THE LIMITS ARE THOSE OF §4.5, PER SIDE — corrected on the night of 15
 *      Aug 2026, while refuting, and the first draft had **invented its own**.
 *
 *      It said 200..8192 on both sides, with the `[S]` of MS-RDPEDISP
 *      next to it.  ⛔ But `RCP.md` §4.5 is NORMATIVE and says something else —
 *      *«width and height of the canvas MUST be between 320x240 and 7680x4320»*
 *      (the maximum of the time) —
 *      and `ATTACH` already applied it.  ⇒ They were two rules on the same number
 *      in two places, that is precisely what the box at the bottom of `capture.h`
 *      declares it wants to avoid.
 *
 * ⚠ And the divergence was **unreachable** as long as `FIT_CANVAS` always
 *   answered `COMPOSITOR_UNABLE`: it came alive the night the chain
 *   was written.  The concrete case is the bottom edge of the window
 *   pulled up: `FIT_CANVAS(1600, 230)` was granted, and the same size
 *   was then REFUSED by `ATTACH` at re-attach.
 *
 * ⛔ And PARITY is OURS, not the compositors': `[M]` labwc grants odd sizes
 *   too, and it is our 4:2:0 that refuses them
 *   (`src/encoder.c:1373`).  One truncates DOWNWARDS and SAYS so, with
 *   `CANVAS` carrying back the real size.
 *
 * ⛔⭐⭐ THE MAXIMUM IS 4096x2304 SINCE 1 OCT 2026 — the user's decision
 *      (phase 19): *«4096 max width is perfectly fine, I never demanded
 *      more»*.  Until that day it was 7680x4320.
 *
 *   · 4096 for WIDTH because `[M]` 22 Aug 2026 `h264_vaapi` on
 *     `EncSliceLP` (Intel) accepts **32-4096 px per side** (4096x2160 yes,
 *     4112x2160 no), and Firefox on Linux receives only H.264: a wider canvas
 *     went only in HEVC, that is only on Chrome, and Firefox was left without video.
 *   · 2304 for HEIGHT because 4096x2304 is **36864 macroblocks**, that is
 *     exactly the `MaxFS` of H.264 levels 5.1 and 5.2 (table A-1, the
 *     same as in `src/vadirect.c`): it is 16:9 at 4096, DCI 4096x2160 fits,
 *     and beyond it level 6 would be needed — which the page does not declare
 *     (`video.level = 5.1`).
 *
 * ⛔⭐ AND ABOVE THE MAXIMUM IT IS NO LONGER REFUSED: IT IS REDUCED.  A browser on
 *    a 5K or ultrawide monitor did nothing wrong — it asked for its
 *    window — and §4.5 already allows the server a canvas different from the one
 *    requested.  ⇒ The side that overflows is brought TO THE MAXIMUM, the other
 *    stays as it is (5120x2880 → 4096x2304, 5120x1440 → 4096x1440): it is the
 *    same rule the page applies in `canvas_to_request()`, so server and page
 *    arrive at the same number.  ⚠ Nothing is distorted: the canvas is the
 *    desktop, and the page lays it out at scale at most 1 with bands (`border()`).
 *    ⛔ BELOW the minimum instead it is refused as before: there no legal
 *    canvas fits inside.
 *
 * `out_w`/`out_h` receive the nearest allowed size: each side beyond
 * the maximum brought to the maximum, then truncated to even.  Returns `false`
 * only if the request is BELOW the minimum: then one answers
 * `CANVAS(REFUSED, SIZE_OUT_OF_RANGE)`.  ⚠ Whoever must know whether the size
 * was reduced compares `fuori_*` with the request. */
/* ⛔⭐ THE HIGHEST NUMBER §6.2 DEFINES FOR VIDEO — 1 = HEVC,
 *     2 = AV1, 3 = H.264 (`DECISIONS.md` §1.13-ter, 20 Aug 2026).
 *
 * ⚠ It lives HERE, in `rcp.h`, because it is a fact of the PROTOCOL and three
 *   modules read it: `child.c` (which refuses an unknown number from the
 *   parent), `webtransport.c` (which refuses a frame with an unknown number) and
 *   `rcp.c`.  ⛔ On 20 August those three places had three numbers written by
 *   hand, and one fell behind: **every H.264 frame was thrown away in
 *   silence** for half an hour, with the session alive and the counters at zero. */
#define RCP_CODEC_VIDEO_MAX 3u

#define RCP_CANVAS_MIN_W 320u
#define RCP_CANVAS_MAX_W 4096u
#define RCP_CANVAS_MIN_H 240u
#define RCP_CANVAS_MAX_H 2304u
bool rcp_size_allowed(uint32_t width, uint32_t height, uint32_t *out_w,
                        uint32_t *out_h);

void rcp_canvas_adapted(rcp_session *s, uint32_t lar, uint32_t h);

/* ⛔⭐⭐ HOW LONG ONE WAITS FOR THE FRAME THAT PROVES THE CHANGE — §7.1.
 *
 * ⚠ It is NOT the resize time: `[M]` 14 Aug 2026 that is **41.6
 *   ms** on Mutter and **5.1 ms** on labwc.  It is the backstop beyond which one
 *   stops waiting and ANSWERS all the same, because §7.1 says *«to every
 *   `FIT_CANVAS` the server MUST answer with a `CANVAS`, successful or not.  A
 *   silence leaves the client waiting forever»* — and §6.2 makes it
 *   HOLD BACK frames until that answer arrives.
 *
 * ⛔ Three seconds and not three hundred milliseconds, and the reason is measured:
 *    on a STILL desktop the new frame arrives because the renegotiation itself
 *    makes it arrive, ⚠ but between the request and the pixels there is a
 *    process boundary, a compositor and — if the stage has fallen — a remount.  A
 *    backstop too short would say `NOT_NOW` to a change that was succeeding, and
 *    the client would show «fit the desktop» as off on a server that can
 *    do it.
 * ⚠ And the price of a backstop too long is paid by the client's memory (the
 *   queue of frames held back of §6.2): that is why a backstop exists, and not
 *   «one waits». */
#define RCP_CANVAS_WAIT_MS 3000u

/* ⛔ How often the stage is ASKED AGAIN to come to the canvas in force, when it
 *    has one of its own.  It doubles at every attempt that comes to nothing, up
 *    to the maximum.
 * ⚠ It is not the resize time (`[M]` 41.6 ms on Mutter): it is the step
 *   with which one insists, and it grows because the «it does not move» case exists. */
#define RCP_CANVAS_RETRY_MS 500u
#define RCP_CANVAS_RETRY_MAX_MS 8000u

/* ⭐⭐ THE STAGE'S ANSWER — the other half of the `recanvas` hook: the question goes
 *     out there, the answer comes back in here.  It is carried by the CHILD, the
 *     only one that knows what the compositor has really done.
 *
 * ⛔⭐ WHY IT CARRIES **TWO** SIZES, and the new one is not enough: `voluta_*` says
 *     which request it answers.  ⚠ Without it, two chained `FIT_CANVAS` — that is
 *     a user dragging the edge of the window — made the frame of the FIRST be
 *     taken as the answer to the SECOND, and the desktop settled on the wrong
 *     size **with the message counts in order**.
 *
 * ⛔ `got_w == 0` = «the stage did not make it»: `NOT_NOW` is answered
 *    at once, instead of letting the `RCP_CANVAS_WAIT_MS` backstop expire for
 *    news that is already there.
 *
 * ⛔⛔ AND WHAT IT DOES NOT DO, because it was the most serious defect of the
 *     first draft: **it never sends a `CANVAS` nobody asked for.**  §6.2 says the
 *     client holds back a size never announced only while it has an
 *     unanswered `FIT_CANVAS`; without one, it is `PROTOCOL_ERROR` — and the
 *     frame, which travels on a stream of its own, can arrive **before** the
 *     `CANVAS` that would justify it.  ⇒ When the stage is elsewhere on its own, it
 *     is ASKED AGAIN for the canvas in force with a growing wait, and nothing
 *     is adopted. */
void rcp_canvas_from_stage(rcp_session *s, uint32_t intended_w, uint32_t intended_h,
                        uint32_t got_w, uint32_t got_h, uint64_t now_ms);

/* ⛔ Is there an `FIT_CANVAS` passed to the stage and not yet answered?  ⚠ It
 * serves whoever sees the frames to know whether an unexpected size is a
 * legitimate race or a new fact — and the bench, to read the state instead of
 * deducing it from timings. */
bool rcp_canvas_in_flight(const rcp_session *s, uint32_t *lar, uint32_t *h);

/* ⭐⭐ «THE STAGE IS NOT THERE YET»: the §7.1 backstop is POSTPONED — 16 Aug 2026.
 *
 * ⛔ THE DEFECT IT CURES, measured three times in one morning: after a logout the
 *    graphical session is gone, and the next login brings it to life.  The
 *    client asks for its canvas at once; the stage mounts five seconds later — ⛔
 *    but the `RCP_CANVAS_WAIT_MS` backstop fires at three, and from that moment
 *    the request is CLOSED.  When the stage arrives at the right size, for this
 *    module it no longer answers anything: it is sent back to the canvas in
 *    force, and the user looks at a desktop smaller than the window — the BLACK
 *    BANDS.
 *
 * ⚠ And it is not «raising the timeout»: it is stopping DEDUCING.  The child knows
 *   whether the stage is not there yet, and now it says so (`LESSONS.md` §7.5).
 *   The backstop stays at three seconds for all the cases in which nobody
 *   promised anything.
 *
 * `true` if the request in flight was precisely that one and the backstop has
 * been postponed.  ⛔ It sends nothing on the wire: it only moves a deadline. */
bool rcp_canvas_postpone(rcp_session *s, uint32_t intended_w, uint32_t intended_h,
                      uint64_t now_ms);

/* For the log, for the bench and for whoever captures.  ⛔ `false` when the
 * canvas is not there yet, which is NOT «0x0» (§6.0: no sentinel values). */
bool rcp_canvas_in_effect(const rcp_session *s, uint32_t *lar, uint32_t *h);

/* ⛔⭐ THE VIEW — §7.1, and it is NOT the canvas.  16 Aug 2026, sub-phase 6.4.
 *
 *   · the **canvas** belongs to the SESSION: it outlives the client (I4), only
 *     `FIT_CANVAS` changes it, and it constrains the frame size (§6.2);
 *   · the **view** belongs to the CONNECTION: «the size at which the client
 *     will draw», it arrives with `ATTACH` (§4.5) and `VIEW` updates it (§7.1).
 *
 * ⛔ §7.1: «`VIEW` **MUST NOT** change the canvas, and in RCP/1 it does not
 *    even change the size of what is encoded»: the server sends the whole canvas
 *    and the client rescales (`SPECS.md` §6.1).  ⇒ Whoever reads this number
 *    uses it for **how many bits to spend**, never for what to encode — a
 *    small window watched on a small screen does not deserve the bits of a
 *    large one.
 *
 * ⚠ And its limits are OTHERS: finding R1.17 — «any size **from 1x1
 *   up** is legal, **odd included**».  ⛔ Whoever applied the canvas limits to it
 *   would close the session of whoever narrows the browser window, and on a
 *   phone at factor 2.75 the view is odd almost always.
 *
 * `false` when `SESSION` has not left yet — which is NOT «0x0». */
bool rcp_vista(const rcp_session *s, uint32_t *lar, uint32_t *h);

/* §4.3/§6.2: 1 = HEVC, 2 = AV1.  ⛔ `0` = not yet negotiated. */
uint8_t rcp_codec_negotiated(const rcp_session *s);

/* ⭐⭐ The depth negotiated in §4.3 — **8** or **10**, `0` if there is none.
 *
 * ⛔ AND IT MUST BE READ, or a depth different from the declared one is sent on
 *    the wire: it is the defect measured on 17 Aug 2026 on Firefox, and the
 *    full box is on the implementation in `rcp.c`. */
uint8_t rcp_depth_negotiated(const rcp_session *s);

/* ⭐⭐ THE LEVEL the client declared in §4.3 (`video.level`), in
 *     TENTHS: `5.1` ⇒ **51**.  `0` = not declared, or declared malformed.
 *
 * ⛔ AND IT MUST BE READ, or the server OVERSHOOTS: `[M]` 23 Aug 2026, canvas
 *    3840x2160, H.264, the client declares 5.1 and the stream goes out at **5.2**.
 *    §4.3 row 701 is a MUST, and the symptom of a wrong level is not an error —
 *    it is the browser's decoder refusing the configuration, that is
 *    «nothing is seen» without a line saying why.
 *
 * ⚠ `0` does NOT mean «low»: it means «no ceiling», and the receiver must not
 *   invent one. */
uint8_t rcp_level_negotiated(const rcp_session *s);

/*
 * §4.3/§6.3: 1 = Opus, 2 = PCM.  ⛔ `0` = not yet negotiated.
 *
 * ⚠ The numbers are NOT the same as video, and the coincidence of the values 1
 *   and 2 is a trap: there 1 is HEVC, here 1 is Opus.  They are two tables of two
 *   different paragraphs (§6.2 and §6.3), and whoever passed one where the other
 *   goes would get a formally valid datagram with the wrong codec inside.
 */
uint8_t rcp_audio_negotiated(const rcp_session *s);
/* ⛔ §5.2: «must the next frame be a keyframe?».  It is asked by whoever
 * encodes, because they decide the frame type. */
bool rcp_video_needs_key(const rcp_session *s);
/* The `nr` (§6.2) of the last frame sent.  ⛔ `0` means
 * «none», and it is the meaning §6.2 and §7.1 give to zero. */
uint32_t rcp_video_last_number(const rcp_session *s);

/* ========================================================================= */
/* ⭐ THE INPUT CHANNEL — `RCP.md` §2.5, §3, §6.1, §7.1, §7.3                */
/*                                                                           */
/* ⛔ WHY IT LIVES HERE AND NOT IN A MODULE OF ITS OWN — the same reason as   */
/*    video.                                                                  */
/*                                                                           */
/* Of the rules of §7.3 almost none speaks of the twenty bytes of the        */
/* message: they speak of the **state of the session**.  «The input stream   */
/* opens after receiving `SESSION`, and there is only one» is §2.5; «the    */
/* coordinates lie inside the canvas» is the canvas granted by `SESSION`    */
/* (§4.5) or the last one of `CANVAS` (§7.1); «the second of grace» is the     */
/* MOMENT of that `CANVAS`; and the `id` this channel carries is the same      */
/* number §6.2 brings back in the `input` field of every frame.              */
/*                                                                           */
/* ⇒ A separate `input_filo.c` would have to copy that state, and two copies */
/*   of a state diverge.                                                     */
/*                                                                           */
/* ⛔ AND WHAT THIS MODULE DOES NOT DO, DECLARED: it does not know `libei`,   */
/*    it does not know `xkbcommon`, it does not know what a keyboard layout   */
/*    is and it does not keep count of what is pressed.  It decodes,          */
/*    VALIDATES and hands over to the hooks above; the other half belongs to  */
/*    `src/input.c`.                                                          */

/* ⛔ Bytes arrived on the **input stream** (§2.5: unidirectional, opened by the
 *    client, **only one**, after `SESSION`, and kept open).
 *
 * `stream` is the identifier the host uses — the same number the
 * `video_*` hooks exchange.  ⛔ It serves one thing only, and it is not a luxury:
 * §2.5 says «**only one**», and without an identifier this module cannot
 * tell the second input stream from the continuation of the first.  ⚠ The
 * host cannot judge it in our place: it sees the streams but does not know which
 * one is «input» until it has read the first two bytes of the payload, and the
 * rule of §2.5 belongs to this module together with all the others.
 *
 * Returns `false` if the session has ended (by farewell or by violation),
 * exactly like `rcp_receive()`.
 *
 * ⛔ And the silence clock (§5.3) is reset HERE too: input bytes are client
 *    bytes like the others, and a user who for thirty seconds does nothing but
 *    move the mouse **is not silent**.  Without this line they would lose the
 *    slot while using the desktop. */
bool rcp_receive_input(rcp_session *s, int64_t stream, const uint8_t *data,
                      size_t len, uint64_t now_ms);

/* ========================================================================= */
/* ⭐⭐ THE CLIPBOARD — `RCP.md` §7.4, §5.4, §2.5                            */
/*                                                                           */
/* ⛔ PLAIN UTF-8 TEXT ONLY, and there is no field declaring a type: §7.4     */
/*    writes it in these words — «it does not exist because there is nothing  */
/*    to choose».  `DECISIONS.md` §5-ter.1, decided by the user on            */
/*    9 Aug 2026 and confirmed again on the 17th.                            */

/* ⛔ §5.4 — the ceiling of a transfer.  ⚠ **1 000 000 bytes, not 1 MiB**, and
 *    the reason is written in §5.4: the message carrying it has six bytes of
 *    framing and four of identifier, and a ceiling equal to the message's
 *    (§6.1, 1 MiB) would make **illegal the text exactly as large as the
 *    ceiling**. */
#define RCP_CLIPBOARD_CAP 1000000u

/*
 * The bytes of a clipboard channel stream (§2.5, high byte `0x02`).
 *
 * ⛔ Unlike input, here the streams are **one per transfer**, and
 *    so there is more than one alive at once: this module keeps a small
 *    table of them, and `fin` is what frees a slot in it.
 *
 * ⚠ `fin` = «the stream has ended».  ⛔ And it does NOT mean «the message is
 *   complete»: the length is in the framing of §6.1, and a message halfway
 *   through on a stream that ends is `PROTOCOL_ERROR` — not a short
 *   message.
 *
 * Returns `false` if the session has ended, like `rcp_receive()`.
 */
bool rcp_receive_clipboard(rcp_session *s, int64_t stream, const uint8_t *data,
                        size_t len, bool fin, uint64_t now_ms);

/*
 * ⭐ «THE SESSION HAS COPIED THIS TEXT» — it is announced to the client (§7.4).
 *
 * ⛔ The text is KEPT, and not sent: §7.4 announces and then waits for an
 *    `CLIPBOARD_ASK`.  «Whoever copies a whole document sends it to
 *    nobody until someone pastes».
 *
 * ⛔ And beyond `RCP_CLIPBOARD_CAP` **it is not announced at all** (§5.4), and the
 *    line goes into the log: it is NOT truncated — «a truncated text pasted into a
 *    terminal is worse than a missing text».
 *
 * `false` = no announcement has left, and the log says why.
 */
bool rcp_clipboard_from_session(rcp_session *s, const char *text, size_t byte);

/*
 * ⭐ «SOMEONE IN THE SESSION IS PASTING»: the client is asked for the text it
 *    had announced (`CLIPBOARD_ASK`).
 *
 * `serial` is the number of the request on the session's side, and this
 * module keeps it aside to return it with the answer.
 *
 * ⛔ `false` = the question did not leave — no live announcement from the client,
 *    no channel, or the stream did not open.  ⚠ And then the host MUST
 *    answer «I do not have it» to whoever is pasting, at once: the debt towards the
 *    compositor does not extinguish itself.
 */
bool rcp_clipboard_ask(rcp_session *s, uint32_t serial, uint64_t now_ms);

/* ⭐ §6.2, `input` field: «the identifier of the last input **injected**
 *    before the capture; 0 if none».
 *
 * ⛔ **INJECTED**, not «received», and the difference shows on every message
 *    the compositor refuses or that a layout cannot produce: what the frame
 *    promises is that the effect of that input is already in the scene, and of
 *    an input not injected there is no effect to see.
 *    ⇒ This number moves forward only when the hook has answered 0.
 *
 * ⚠ It is read BY WHOEVER CAPTURES, at the instant of capture, and passed to
 *   `rcp_video_open()`.  ⛔ `rcp_video_open()` does not set it by itself, and it
 *   is not an oversight: «the last injected **before the capture**» is a fact
 *   of the instant of capture, and only whoever captures knows it — between the
 *   capture and the call the whole encoding passes.  Taking it here would say
 *   «the last injected before SENDING», which is a higher number and a bigger
 *   promise than the one the frame can keep. */
uint32_t rcp_input_last_injected(const rcp_session *s);

/* The last `id` **accepted** on the channel — injected or not.  ⛔ For the log and
 * for the bench: together with the previous one it tells «the compositor took
 * nothing» from «nothing arrived», which is `LESSONS.md` §1.9 rule 1 on the
 * field where it costs most (the symptom of both is «the desktop does not
 * respond»). */
uint32_t rcp_input_last_id(const rcp_session *s);

/* ⛔ §7.1 — the version of `rcp_canvas_adapted()` that knows **when**, and opens the
 *    SECOND OF GRACE: «after sending `CANVAS(FITTED)` the server MUST
 *    accept for one second input coordinates valid on the PREVIOUS
 *    canvas, clamping them to the new one and writing it to the log; once
 *    that second has passed, they are `PROTOCOL_ERROR`».  It is the third
 *    exception declared in §3.
 *
 * ⚠ `rcp_canvas_adapted()` stays, does everything else and **does not open the
 *   grace**: it has no clock to start it from.  The fallback is DECLARED
 *   (`CODER.md` §4.2) and a log line declares it, not this comment. */
void rcp_canvas_adapted_now(rcp_session *s, uint32_t lar, uint32_t h,
                           uint64_t now_ms);

/* ========================================================================= */
/* ⭐ THE CURSOR — `RCP.md` §7.2, §5.5, §5, §6.1                             */
/*                                                                           */
/* ⛔ WHY THE PARAMETERS ARE SCALARS AND NOT A `const CursorShape *`.        */
/*                                                                           */
/* `src/cursor.h` defines `CursorShape` and it is the right contract — but  */
/* `rcp.c` exists in TWO folders and the `Makefile` (variable `GEMELLATI`)    */
/* demands they match byte for byte; the second copy is carried by            */
/* `benches/01-b3-graft-rcp.py` into ngtcp2's `examples/`, and that file     */
/* lists THREE names: `rcp.c`, `rcp.h`, `authentication.c`.  ⇒ An             */
/* `#include "cursor.h"` here **does not compile the harness**, that is it   */
/* switches off B3, B5, B6, B8 and B11 in one go.  It is the same reason as   */
/* the input hooks, and the cure is the same: the fields pass as scalars, and */
/* the six-line adapter that unwraps `CursorShape` lives where `cursor.h`   */
/* can be included — that is on the coordinator's side.                       */
/*                                                                           */
/* ⛔ AND WHAT THIS FUNCTION DOES **NOT** CHECK, DECLARED: the limits of      */
/*    §5.5 — 256 per side, the hotspot inside the image, `0×0` with           */
/*    `0,0` for hidden, and «only one of the two at zero is                   */
/*    PROTOCOL_ERROR» — are enforced by `src/cursor.c`.  Here they are    */
/*    not checked again: two checks on the same rule in two places become     */
/*    two different rules the day one of them changes.                        */

/* Sends `CURSOR_SHAPE` (§7.2) on the control channel (§5).
 *
 * `width`/`height`  ⛔ `0` and `0` together = HIDDEN cursor (§5.5).
 * `hot_x`/`hot_y`  the point that «points»; `0,0` if hidden.
 * `bitmap`             `width × height × 4` bytes, PREMULTIPLIED BGRA.
 *                        ⛔ `NULL` is legitimate **only** if there are no bytes
 *                        to send.  ⚠ It is COPIED in here: when this
 *                        function returns, the caller can reuse the buffer —
 *                        and it is what `cursor.h` demands, because there
 *                        the image «lives until the next callback».
 * `image_n`           how many bytes there REALLY are behind `bitmap`.
 *
 * ⛔⭐ `image_n` is NOT redundant, and it is the reason this signature does not
 *     take only the size: §7.2 requires the message length to be
 *     **exactly** `8 + width × height × 4`, and without knowing how many bytes
 *     really exist this function would read `width × height × 4` of them
 *     **on trust** — that is it would do, on the sender's side, precisely the
 *     «I read what is there and carry on» that §7.2 names.  The cursor made of
 *     other people's memory would be packaged by the server.
 *
 * ⛔ Returns `0` if the message HAS LEFT, `-1` if it has not — and in
 *    that case the why is in the log, always.  ⚠ When in doubt one does NOT
 *    send: §7.2 makes THE RECEIVER detect the wrong length, so a crooked message
 *    sent from here makes **the page** close the session and the server log
 *    would know nothing of it.  A cursor that does not update is
 *    ugly; a session that drops is broken (`SPECS.md` §8.3).
 *
 * ⛔⛔ FROM THE LOOP THREAD, NEVER FROM THE REAL-TIME THREAD OF THE CAPTURE.
 *     `capture.c` calls `CursorArrived` on the PipeWire thread
 *     (`cursor_bounce()`, and the box of the loop in `capture.h`); this
 *     module has no lock and `send_msg` writes into the transport's queue.
 *     Whoever sews the two together MUST pass the shape through the loop — and in
 *     the product it already does, because the capture lives in the CHILD and the
 *     session in the parent. */
int rcp_cursor_shape(rcp_session *s, uint16_t width, uint16_t height,
                      int16_t hot_x, int16_t hot_y,
                      const uint8_t *bitmap, size_t image_n);

/* ------------------------------------------------------------------------ */
/* §4.4-bis — THE ADDRESS BAN, and the three things the host must be able to
 * do.  The rule is in `DECISIONS.md` §1.9, decided by the user on 10
 * Aug 2026: three consecutive failed authentications from the same address, and
 * that address is out for twelve hours.
 * ⛔ CHANGED on 24 Oct 2026 (`docs/1.5/DECISIONS-11.md`): three levels of counters
 * ((key, user) 5 in 5 min · key 12 in 5 min · IPv6 /48 30 in 10 min), progressive
 * ban 15 min / 1 h / 12 h, forgotten after 24 h; key = IPv4 whole, IPv6 /64.
 * The 12 hours are now the TOP of the ladder.  `rcp_banned()` answers for the
 * levels that do not depend on the user (key, /48); `rcp_unblock()` clears all. */

/* ⛔ «Is this address banned?», and how long it has left.  It is called **by
 * whoever serves the page over TCP**: §4.4-bis wants the page to load all the
 * same and say the attempts are used up — never a network error, never a silence,
 * because whoever is banned by mistake is almost always the owner.
 * `provenance` may carry the port: it is cut in here. */
bool rcp_banned(const char *provenance, uint64_t now_ms, uint64_t *remain_ms);

/* ⛔ The unblock command — the other way out besides the twelve hours.
 * Returns `true` if the address was really banned: «it was not banned» and
 * «I unblocked it» are two different facts, and whoever commands must be able to
 * tell them apart.  ⭐ It is also what makes bench B8 possible, which wants
 * many more than three samples. */
bool rcp_unblock(const char *address, uint64_t now_ms);

/* ⛔ Declares the ban file and reads it back: without it, the ban lives in memory
 * and a restart takes it away — invariant I7.  Returns how many it loaded,
 * ⛔ and **-1 if the file was there and could not be read**: «zero bans» and «I
 * could not look» are two different facts (`LESSONS.md` §1.9 rule 1), and the
 * caller MUST print them differently — a -1 read as zero is the protection
 * switched off with the air of having nothing to protect.
 * ⚠ An empty or NULL path switches off persistence (it is the bench's case). */
int rcp_ban_load(const char *fpath, uint64_t now_ms);

/* ⛔ The ban key in the form in which §4.4-bis counts it, from any form of
 * address: `127.0.0.1` · `127.0.0.1:53` · `[127.0.0.1]:53` · `fe80::1`
 * all become `[127.0.0.1]` / `[fe80::1]`.
 *
 * ⭐ It serves the UNBLOCK COMMAND, which receives an address typed by a
 *    person while the key was made by the host's `util::straddr()`, which
 *    puts brackets even around IPv4.  Without this function the host would
 *    build it itself, and the day the two forms diverged the unblock would
 *    answer «it was not banned» to every address — in silence, and
 *    forever. */
void rcp_key_address(const char *text, char *report, size_t cap);

/* ⛔⭐ THE LOGIN DEFENCES — 24 Oct 2026 (SPEC CHANGE from 1.0: `docs/1.5/DECISIONS-11.md`).
 *
 * `rcp_key_address()` now gives the ban key of §4.4-bis A: IPv4 the whole
 * address, IPv6 the /64 (`fe80::1` -> `[fe80::]`; `::ffff:a.b.c.d` and NAT64
 * are the IPv4 inside; `::1` whole).  It stays idempotent.
 *
 * A verdict of PAM that arrives when the connection is GONE is counted all the
 * same, from the name and the bare address the request in flight carries
 * (`PAM_RHOST` form).  The lines it has to write go to `fn` (there is no session
 * to hang them on); `fn` may be NULL.  `now_ms` is the clock of `rcp_banned()`. */
typedef void (*rcp_line_fn)(void *ctx, const char *line);
void rcp_orphan_verdict(const char *user, const char *rhost, bool admitted,
                        bool lost, uint64_t ticket, uint64_t now_ms, rcp_line_fn fn, void *ctx);

/* ⛔ The PAM helper DIED while `ticket` was in flight: our defect, so the
 * booking of §4.4-bis is given back and NOTHING is counted (24 Oct 2026).  Same
 * walls as `rcp_verdict()`.  `lost` of `rcp_orphan_verdict()` is the same case
 * for a connection that is gone.  (The PAM timeout is NOT this: it is a
 * `rcp_verdict(..., false, ...)` and it counts as a failure.) */
bool rcp_verdict_lost(rcp_session *s, uint64_t ticket);

/* ⛔⭐ THE NAME OF A USER OF THIS MACHINE, AS THE MACHINE WRITES IT (audit P-R6/Q-R8, 25 Oct 2026).  The registry of slots, the
 * children and the stages are keyed by the NAME, and the name is what the visitor TYPED.  Where the system does not tell two spellings
 * apart (sssd / LDAP with `case_sensitive = false`, which is the usual setting for a directory), «Anna» and «anna» are the same user
 * with two keys: two slots, two children, two desktops of one uid, and a single user could take every slot of the server by varying
 * the capitals.  After PAM has said yes, the name is brought to `pw_name`.
 * `true` = `out` holds the name of the system (it may be the same as `typed`); `false` = the system could not say (the name stays as
 * it was).  ⚠ `getpwnam_r` may ask NSS: it is called only for a login that PAM has already admitted. */
bool rcp_canonical_user(const char *typed, char *out, size_t cap);

/* ⛔ The secret of the tags `unknown user [hmac6]` of the log (§4.4-bis D):
 * `<dir>/log-secret`, 0600, next to the QUIC token secret.  Returns 1 = read,
 * 0 = made and written, -1 = the secret of this run only (the tags change at
 * every restart), -2 = no secret (the tags are «??????»; never the name). */
int rcp_log_secret_load(const char *dir);

/* The same 6-hex tag as `unknown user [hmac6]`, for a line written outside rcp.c (the PAM helper, R3 of 25 Oct 2026).  `out` is 8
 * bytes: 6 hex and the zero, or `??????` when there is no secret.  Never the name. */
void rcp_log_tag(const char *user, char out[8]);

#ifdef __cplusplus
}
#endif
