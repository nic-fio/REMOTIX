/*
 * cid.h — the server's Connection IDs that carry their own proof (`cid-firmati`, after R9 of the network audit,
 * 25 Oct 2026).
 *
 * ⭐ WHY.  A short-header packet for a connection the server does not know is answered with a Stateless Reset
 *    (RFC 9000 §10.3), up to 100 a second for the whole server (`RESET_PER_SECOND`, transport.c).  Anyone can send
 *    100 such packets a second with any destination id, from any address: the cap is used up, and the real client
 *    that lost its connection (the server restarted) waits the 30 s of the idle timeout instead of learning it at once.
 *
 * ⭐ WHAT.  Every id the server issues — its first one, the one of the Retry, every NEW_CONNECTION_ID — is
 *    `CID_NONCE` random bytes followed by `CID_TAG` bytes of HMAC-SHA256 under a key derived from the static secret
 *    (the same `quic-secret` file the Stateless Reset tokens come from), truncated.  A packet whose destination id
 *    carries a valid tag is one the server could have issued; one that does not, is not.  64 bits of tag: a guess
 *    passes with probability 2^-64.
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

/* The key from the static secret (domain-separated: HMAC(secret, "REMOTIX CID v1")); NULL if it cannot be made. */
cidkey *cidkey_new(const uint8_t *secret, size_t secretlen);
void cidkey_free(cidkey *k);

/* Fills `cid[0..CID_LEN)` with a fresh signed id.  False if the system RNG fails (nothing usable written). */
bool cidkey_make(cidkey *k, uint8_t cid[CID_LEN]);

/* True if `cid[0..len)` has the length and the tag of an id this key makes.  Constant time in the tag. */
bool cidkey_ok(cidkey *k, const uint8_t *cid, size_t len);

#endif
