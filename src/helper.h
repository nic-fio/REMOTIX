/*
 * helper.h — ⭐ THE PROCESS THAT QUERIES PAM IN PLACE OF THE SINGLE THREAD.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY IT EXISTS, WITH THE NUMBER NEXT TO IT
 *
 * `DECISIONS.md` §1.10, 11 Aug 2026, from the user.  The server runs in a single
 * `poll` loop (`main.c`) and the PAM check **blocks that thread**: `[M]` B8,
 * evening of 11 August, **from 1.0 to 2.2 seconds per attempt** (medians
 * 2123 · 2198 · 1086 ms) — and ⭐ **the delay is added by PAM, not by us**:
 * +1034 ms beyond the fixed second on the rejected against +84 ms on the
 * admitted, which is the signature of `pam_faildelay`.
 *
 * ⛔ Up to phase 1 the symptom was «the last of ten waits ten seconds»:
 *    unpleasant and contained.  ⛔ From phase 2 onwards it becomes **the
 *    screen of everyone connected freezing for one or two seconds every time
 *    someone else logs in** — and whoever sees it will blame the video,
 *    because that is where it shows.  It is the «the symptom does not name the
 *    cause» form of `LESSONS.md` §1.6, and curing it now means not letting it
 *    be born.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ A PROCESS, NOT A THREAD — and it is the user's decision, not a
 *     preference of style
 *
 * §1.10: *«with a helper process, not with a thread: PAM is not reliably
 * reentrant, and a thread would bring troubles of its own into the cure of a
 * concurrency problem»*.
 *
 * ⭐ And here we go one step further, because it costs ten lines: **every PAM
 *    transaction lives in a process that does ONE ONLY and then dies**.  Hence
 *    the three-storey shape:
 *
 *      the server       never calls PAM.  It writes a request on a socket
 *                       and goes back to the `poll` — which is the whole point;
 *      the dispatcher   a child, started once at boot.  It never calls PAM
 *                       either: it reads a request and forks;
 *      the grandchild   calls PAM ONCE, writes the outcome, exits.
 *
 * ⛔ PAM's reentrancy is thus not «handled»: **it is not in play**.  No
 *    process that touches `libpam` touches it twice, and the PAM modules —
 *    which are someone else's code, loaded at runtime, with `getpwnam`,
 *    sockets to `nscd`, `dlopen` inside — share nothing with anyone.
 *
 * ⭐ And the second gain, which the single thread did not have: **ten logging
 *    in together do not queue**, because the grandchildren are ten processes.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ INVARIANT I3, AND HOW TO MAKE SURE THAT FAILURE IS A «NO»
 *
 * I3 (`CODER.md` §2): *the guard starts from denied.  Whoever does not pass the
 * validator receives not one pixel and commands nothing.*  ⛔ A helper that
 * answered «yes» for a lost message, an expired timeout or a dead process
 * would be I3 violated, and it is the worst defect this work could produce.
 * The seven roads by which something can go wrong, and where each one comes
 * out:
 *
 *   1. the helper did not start            `helper_ask` -> false -> NO
 *   2. the socket is full / EAGAIN         `helper_ask` -> false -> NO
 *   3. too many requests in flight (> 16)  `helper_ask` -> false -> NO
 *   4. the dispatcher is dead (EOF)        all requests in flight -> NO
 *   5. the grandchild died without answering the request expires   -> NO
 *   6. the answer is short or mangled      it is discarded         -> then (5)
 *   7. the answer carries a byte that is not exactly 1 -> NO
 *
 * ⛔ **There is no road leading to `true` without a `PAM_SUCCESS` on both
 *    steps of `rcp_authenticate()`**: the `true` is born at a single point of the
 *    program, and it is the byte `1` written by the grandchild after receiving
 *    that `PAM_SUCCESS`.  Every other combination of bytes, every different
 *    length and every silence is a «no».
 *
 * ⚠ And the SOCKET IS `SOCK_SEQPACKET`, not `SOCK_STREAM`: with the messages
 *   delimited by the kernel a request cannot arrive halfway, and an answer
 *   cannot merge with that of another grandchild.  ⛔ With a stream a framing
 *   of our own would have been needed — that is, a piece of code in which a
 *   defect produces «someone else's answer», which is I3 violated by a parsing
 *   error.
 *
 * ---------------------------------------------------------------------------
 * ⚠ AND THE PASSWORD GOES THROUGH HERE
 *
 * `RCP.md` §4.4: «the password sits in clear in the memory of whoever receives
 * it, must be zeroed as soon as PAM has answered, and must not appear in any
 * log».  ⛔ This module adds **two copies** to those R9.8 has already
 * catalogued — the message in the sender's buffer and the one in the
 * receiver's buffer — and zeroes both as soon as they have served.  The socket
 * is an anonymous pair created by `socketpair()`: it has no name in the
 * filesystem, cannot be connected to from outside, and dies with the two
 * processes.
 */
#ifndef REMOTIX_HELPER_H
#define REMOTIX_HELPER_H

#include <stdbool.h>
#include <stdint.h>

typedef struct helper helper;

/* ⛔ It is started EARLY, and the reason is that the child inherits the
 *    descriptors: started after `transport_open()` it would carry along the
 *    UDP socket and the TCP listener, and the port would stay held by it even
 *    after the server's death.  ⚠ Returns NULL if it could not be started, and
 *    the caller MUST be able to tell «started» from «not started»: without a
 *    helper every authentication is a NO. */
helper *helper_turn_on(void);

/* Closes the socket and sends `SIGTERM` to the dispatcher. */
void helper_turn_off(helper *a);

/* The descriptor to put in the `poll`, or -1 if the helper is off/dead. */
int helper_descriptor(const helper *a);

/* ⛔ Asks for the check and RETURNS AT ONCE.  `true` = the question has left
 * and an answer will arrive (or expire); `false` = **it has not left**, and the
 * caller must treat it as an immediate «no».
 * `ticket` comes out with the number by which the answer will be recognised. */
bool helper_ask(helper *a, const char *user, const char *password,
                     const char *provenance, uint64_t now_ms,
                     uint64_t *ticket);

/* ⛔⭐ AND THE DELIVERY ALSO CARRIES THE USER'S NAME — 12 Aug 2026,
 *     `DECISIONS.md` §1.10-bis.
 *
 *     Until today the request number was enough: whoever knew which session
 *     it belonged to was `rcp.c`, and the name was of no use to anyone.  ⛔ Now
 *     it is needed: when the answer is «yes», the parent must spawn **that
 *     user's child** (`child.h`), and the only place of the program that has
 *     both the request number and the name is this one — the name arrived in
 *     `helper_ask()`.
 *
 * ⚠ The name lives in the table of requests in flight next to the expiry:
 *   ⛔ **the password does not**, and it is not a detail — §4.4 wants it
 *   zeroed as soon as PAM has answered, and here not even one copy remains. */
/* ⭐ PHASE 17 T6: and the client's ADDRESS (bare, like sshd's `PAM_RHOST`;
 *    "" if unknown), which on «yes» goes to the child's PAM session. */
/* ⭐ 24 Oct 2026 (§4.4-bis B): `lost` is true when the verdict is a «no» because
 *    the HELPER DIED with the request in flight — our defect, which must not
 *    count as a failed attempt.  The PAM timeout (`helper_expired()`) is NOT
 *    `lost`: it counts.  `rhost` is always the request's own address, even
 *    when the helper is dead, because the connection may be gone and the
 *    booking is resolved with the name and the address. */
typedef void (*HelperVerdict)(void *ctx, uint64_t ticket, bool admitted,
                                 const char *user, const char *rhost, bool lost);

/* Reads the ready answers and delivers them one by one.  To be called when the
 * descriptor is readable.
 * ⛔ If the dispatcher is dead, it delivers a «no» for every request in flight:
 *    a request without an answer is a wait nobody closes. */
void helper_move(helper *a, HelperVerdict delivery, void *ctx);

/* ⛔ Expires the requests that are too old, delivering a «no».  It is the
 * safety net of case 5: a grandchild killed halfway writes nothing, and
 * without this call the session would stay in `wait-verdict` forever. */
void helper_expired(helper *a, uint64_t now_ms, HelperVerdict delivery,
                      void *ctx);

/* How many requests are in flight.  For the log. */
int helper_in_flight(const helper *a);

#endif
