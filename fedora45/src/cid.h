/*
 * cid.h — the server's Connection IDs that carry their own proof (`cid-firmati`, after R9 of the network audit,
 * 25 Oct 2026).
 *
 * ⭐ WHY.  A short-header packet for a connection the server does not know is answered with a Stateless Reset
 *    (RFC 9000 §10.3), up to 100 a second for the whole server (`RESET_PER_SECOND`, transport.c).  Anyone can send
 *    100 such packets a second with any destination id, from any address: the cap is used up, and the real client
 *    that lost its connection (the server restarted) waits the 30 s of the idle timeout instead of learning it at once.
 *
 * ⭐ WHAT.  Every id the server issues — its first one, every NEW_CONNECTION_ID — is `CID_NONCE` random bytes followed by
 *    `CID_TAG` bytes of HMAC-SHA256 under a key derived from the static secret (the same `quic-secret` file the Stateless
 *    Reset tokens come from), truncated, over «'C', the nonce and the EPOCH» (an epoch is `CID_EPOCH_S` seconds of UTC clock).
 *    A packet whose destination id carries a valid tag of this epoch or of the one before is one the server could have
 *    issued a short time ago; one that does not, is not.  64 bits of tag: a guess passes with probability 2^-64.
 *
 * ⭐ rilettura (25 Oct 2026, M1).  Two things the first version did not have, found when reading the merged code:
 *    · the tag EXPIRES: an id someone collected (a Retry gives one to whoever asks, a handshake gives seven more) was a «signed» id
 *      for ever and could spend the 100 Resets a second of the ids this server issued.  Now it counts as signed for 1 to 2 epochs
 *      (1 to 2 hours) and then as any unknown id (the small budget).  A long session keeps working: the tag only chooses WHICH
 *      Reset budget an UNKNOWN id uses, never whether a packet finds its connection (transport.c always searches its map);
 *    ⚠ THE LIMIT THAT REMAINS (declared, not closed): a handshake gives the client `active_connection_id_limit` = 7 ids, each one «signed»
 *      for 1 to 2 hours, and each may be answered once a second (transport.c, `reset_id`).  So about 100 collected ids — some 13-15
 *      handshakes an hour, well under what `hsrate.h` allows one address (4 a second) — can still use up the 100 Resets a second of
 *      the signed budget, from spoofed sources.  What it costs the clients: a session that lost the server then gets its Reset from
 *      the budget of the unsigned ids (10 a second) or waits the 30 s of idle timeout; with at most 8 users that is enough.
 *      Closing it would take a budget per source that cannot be spoofed, and there is none before the handshake.
 *    · the id of the RETRY has its own label ('R', no epoch): it is bound to the connection that follows, and is found there,
 *      but it never counts as signed for a Reset — it is given to anybody who sends an Initial, with no handshake behind it.
 *
 * ⭐ THE KEY IS DERIVED FROM THE STATIC SECRET, NOT FROM THE RUN.  An id issued before a restart must still be
 *    recognised after it: its Stateless Reset token is derived from the same secret (`ngtcp2_crypto_generate_
 *    stateless_reset_token`), so the reset a client accepts exists exactly as long as the tag verifies.  If the secret
 *    is replaced (the file lost), both go together: the client would discard the reset anyway.
 *
 * ⚠ NOT SECRET, NOT AN AUTHENTICATION OF THE CLIENT: the id travels in the clear; whoever has seen one can reuse it.
 *    It only tells «issued by this server (key) and not forged blind».
 *
 * ⚠ Single-threaded, like `transport.c`: the HMAC context is reused between calls.
 */
#ifndef REMOTIX_CID_H
#define REMOTIX_CID_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define CID_LEN 18   /* = SCIDLEN of transport.c; ngtcp2 allows up to 20 (NGTCP2_MAX_CIDLEN) */
#define CID_NONCE 10 /* random bytes */
#define CID_TAG 8    /* bytes of HMAC-SHA256, truncated (CID_NONCE + CID_TAG == CID_LEN) */

typedef struct cidkey cidkey;

#define CID_EPOCH_S 3600 /* an epoch: an hour of UTC clock (transport.c: time / CID_EPOCH_S) */

/* The key from the static secret (domain-separated: HMAC(secret, "REMOTIX CID v2")); NULL if it cannot be made. */
cidkey *cidkey_new(const uint8_t *secret, size_t secretlen);
void cidkey_free(cidkey *k);

/* How many times the HMAC itself failed (not a bad tag: a failure of OpenSSL).  When it fails, `cidkey_ok()` answers false — the id
 * is treated as not signed — and `cidkey_make()` false; a counter that grows is what the caller writes in the log (rate limited). */
unsigned cidkey_errors(const cidkey *k);

/* Fills `cid[0..CID_LEN)` with a fresh CONNECTION id of `epoch` (the first id of a connection, a NEW_CONNECTION_ID).  False if the
 * system RNG fails (nothing usable written). */
bool cidkey_make(cidkey *k, uint8_t cid[CID_LEN], uint64_t epoch);

/* Fills it with a fresh id for a RETRY (no epoch): `cidkey_ok()` says false for it, `cidkey_ok_retry()` true. */
bool cidkey_make_retry(cidkey *k, uint8_t cid[CID_LEN]);

/* True if `cid[0..len)` has the length and the tag of a CONNECTION id this key made in `epoch` or in the one before (never wraps below
 * 0).  Constant time in the tag. */
bool cidkey_ok(cidkey *k, const uint8_t *cid, size_t len, uint64_t epoch);

/* True if it is an id made by `cidkey_make_retry()` with this key (for the tests: the product needs no more than «it is not signed»). */
bool cidkey_ok_retry(cidkey *k, const uint8_t *cid, size_t len);

#endif
