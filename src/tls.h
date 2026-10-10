/*
 * tls.h — the two TLS contexts, one per listener.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THERE ARE TWO BECAUSE THERE ARE TWO CERTIFICATES (`RCP.md` §4.1-bis)
 *
 *   the QUIC one    presents the SHORT certificate, and is rebuilt at every
 *                   rotation;
 *   the TCP one     presents the LONG-LIVED one, and is almost never rebuilt.
 *
 * ⚠ A single `SSL_CTX` for both would be the defect of B13.1 written in a
 *   place where nobody looks for it.
 *
 * ---------------------------------------------------------------------------
 * ⭐ WHY OPENSSL AND NOT BORINGSSL
 *
 * Bench B2 measured with BoringSSL, because that is what the ngtcp2 example
 * builds with by default.  ⛔ In the product the stack is `ngtcp2_crypto_ossl`
 * on the system OpenSSL (3.5, which carries the native QUIC API): this is
 * `CODER.md` §4.1 — depend, do not rewrite, and do not bundle a second
 * cryptography library inside the binary either.  ⚠ It is a change of stack
 * compared to B2's measurement: it must be declared, not taken as equivalent.
 */
#ifndef REMOTIX_TLS_H
#define REMOTIX_TLS_H

#include <openssl/ssl.h>
#include <stdbool.h>

/* The QUIC context: ALPN `h3`, 0-RTT OFF, session certificate. */
SSL_CTX *tls_contesto_quic(const char *pem, const char *key);

/* The context for the page over TCP: ALPN `http/1.1`, long-lived certificate. */
SSL_CTX *tls_contesto_pagina(const char *pem, const char *key);

#endif
