/*
 * transport.h — THE UDP LISTENER: QUIC, and the connections that live on it.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE FIRST OF THE TWO LISTENERS (`RCP.md` §2.4)
 *
 * «7447, and they are TWO listeners with the same number: UDP for HTTP/3 and
 * WebTransport, TCP for the first load of the page.»  This file is the UDP
 * one; `page.h` is the TCP one.
 *
 * ⚠ And the two things are INDEPENDENT — measurement S1, `RCP.md` §2.4:
 *   WebTransport does not use `Alt-Svc` at all, it opens its connection on its
 *   own.  ⛔ The silent fallback to TCP that the plan declared as a danger
 *   CANNOT happen, because there is no fallback to make.  Whoever reads
 *   `PLAN.md` phase 1 will still find written «and the `Alt-Svc`
 *   announcement that binds them»: that line predates the measurement, and
 *   `RCP.md` §2.4 corrects it with a ⛔.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE TRANSPORT PARAMETERS THAT ARE NORMATIVE, AND WHERE THEY ARE
 *
 * `RCP.md` §2.2 and §2.3 impose on the SERVER — not on the client, which is a
 * browser and chooses its own parameters:
 *
 *   max_idle_timeout          30 s, imposed by the server (§2.2)
 *   datagram                  enabled (§2.2) — and without the transport
 *                             parameter, announcing SETTINGS_H3_DATAGRAM=1 is
 *                             a protocol error
 *   at least 16 uni streams   AVAILABLE AT ALL TIMES to the client (§2.3): their
 *                             example grants 3, and with that credit the
 *                             client would not even open the input stream —
 *                             the symptom would be «the desktop does not
 *                             respond».
 *                             ⛔ **19** are granted: the three unidirectional
 *                             ones of HTTP/3 (control + the two of QPACK) are
 *                             open from the first second and never close, so
 *                             16 as a TOTAL were 13 as availability
 *                             (finding B-12)
 *   no 0-RTT                  (§2.3) — it is in `tls.c`, where it is turned off
 *   migration not disabled    (§2.3) — `disable_active_migration` is not touched
 */
#ifndef REMOTIX_TRANSPORT_H
#define REMOTIX_TRANSPORT_H

#include "helper.h"

#include <openssl/ssl.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct transport transport;

/* Opens the UDP socket and prepares the stack.  `port` is the same as TCP's.
 *
 * ⭐ `help` is the PAM helper (`DECISIONS.md` §1.10), started by `main.c`
 *    BEFORE this call — so the child process inherits neither the UDP socket
 *    nor the TCP listener.  ⚠ NULL is allowed: the server checks the
 *    credentials synchronously, that is stopping the thread, and it is the
 *    declared fallback of `CODER.md` §4.2.
 *
 * ⭐ `secret_dir` (`DECISIONS.md` §11.9) is where `quic-secret` is kept (0600):
 *    the static secret from which both the Retry tokens and the Stateless
 *    Reset tokens are derived.  ⚠ It must survive a restart, or a reset sent
 *    after it would carry a token the client has never heard of.  If the file
 *    cannot be read or written the secret of the run is used, and it is
 *    declared in the log. */
transport *transport_open(const char *address, const char *port, SSL_CTX *ctx,
                          helper *help, const char *secret_dir);

/* ⭐ Delivers a PAM verdict to the connection that was waiting for it (§1.10).
 * ⚠ If nobody waits for it any more it writes it in the log and throws it
 *   away: it is what happens when the connection dies while PAM answers. */
/* ⭐ D-001: `resumed` = that user's stage already existed before this verdict;
 * it travels up to `SESSION` (§4.5, `2 = RESUMED`). */
/* ⭐ 24 Oct 2026 (§4.4-bis B): `user` and `rhost` are the NAME and the bare
 * ADDRESS the request in flight carried (`struct flight`, `helper.c`): if the
 * connection is gone the verdict is counted from them, not thrown away. */
void transport_verdict_from(transport *t, uint64_t ticket, bool admitted,
                            bool resumed, const char *user, const char *rhost,
                            bool lost);
/* The old form, without the name and the address (nothing is counted if the
 * connection is gone): kept for the harnesses. */
void transport_verdict(transport *t, uint64_t ticket, bool admitted,
                        bool resumed);
void transport_close(transport *t);

int transport_fd(const transport *t);

/* ⛔ After a rotation of the session certificate the TLS context changes: the
 * connections already open keep theirs, the new ones take this one.  Whoever
 * does not redo it serves for fourteen days a certificate whose fingerprint
 * the page no longer publishes. */
void transport_context(transport *t, SSL_CTX *ctx);

/* The socket is readable: everything there is gets read. */
void transport_read(transport *t);

/* Whatever there is to write is written on all connections. */
void transport_write(transport *t);

/* Milliseconds from now to the first timer that expires, or -1 if there is none.
 * ⛔ It is not «zero if there is none»: zero means «now», and confusing the two
 *    makes the loop spin idle burning a CPU. */
int transport_wait_ms(const transport *t);

/* Expires the ripe timers (QUIC's and ours) and writes again. */
void transport_expired(transport *t);

/* ⭐ 1.5 (security review, 15 Oct 2026): the caps on connections — at most
 * `max_connections` at once, `max_pending` of them NOT YET LOGGED IN, and of those
 * `pending_per_address` from one IPv4 address or IPv6 /64 and `pending_per_48` from
 * one IPv6 /48.  0 = the default (256, 128, 8, 32).  When the server is full the
 * oldest connection that has not reached its credentials is closed for the
 * newcomer; a full place, or full with nobody to close, is refused with
 * CONNECTION_REFUSED and nothing kept.  One log line every 10 s at most.  The
 * reasons, the address rule (the same as `rcp_key_address()`) and why a migrated
 * connection keeps counting against its birth address are in the box on
 * `MAX_CONNECTIONS` in `transport.c`.  Call it right after `transport_open()`. */
void transport_limits(transport *t, size_t max_connections, size_t max_pending,
                      size_t pending_per_address, size_t pending_per_48);

/* How many connections are alive.  For the log. */
size_t transport_count(const transport *t);

/* ⛔ §8.1 — «never with a silence»: sends `FAREWELL` with the reason to all live
 * sessions and closes each one with the reason's code (§3.1 point 3).  It is
 * called by whoever shuts the server down, with `RCP_SERVER_CLOSING` (§8.2,
 * `0x0C`).
 *
 * ⭐ Returns how many connections still have bytes to get out: whoever shuts
 *    down runs the loop until it is zero (or until its patience runs out),
 *    because «handed to ngtcp2» is not «out on the wire». */
const char *transport_remain_reason(const transport *t);
size_t transport_dismiss_all(transport *t, uint8_t reason, const char *why);

#endif
