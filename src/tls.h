/*
 * tls.h — i due contesti TLS, uno per ascoltatore.
 *
 * ---------------------------------------------------------------------------
 * ⛔ SONO DUE PERCHE' I CERTIFICATI SONO DUE (`RCP.md` §4.1-bis)
 *
 *   quello di QUIC   presenta il certificato BREVE, e si rifa' a ogni
 *                    rotazione;
 *   quello del TCP   presenta il LONGEVO, e non si rifa' quasi mai.
 *
 * ⚠ Un solo `SSL_CTX` per tutt'e due sarebbe il difetto di B13.1 scritto in un
 *   punto in cui nessuno lo cerca.
 *
 * ---------------------------------------------------------------------------
 * ⭐ PERCHE' OPENSSL E NON BORINGSSL
 *
 * Il banco B2 ha misurato con BoringSSL, perche' e' quel che l'esempio di
 * ngtcp2 monta di serie.  ⛔ Nel prodotto la pila e' `ngtcp2_crypto_ossl`
 * sull'OpenSSL di sistema (3.5, che porta l'API QUIC nativa): e' `CODER.md`
 * §4.1 — dipendere, non riscrivere, e nemmeno impacchettare una seconda
 * libreria di crittografia dentro il binario.  ⚠ E' un cambiamento di pila
 * rispetto alla misura di B2: va dichiarato, non dato per equivalente.
 */
#ifndef REMOTIX_TLS_H
#define REMOTIX_TLS_H

#include <openssl/ssl.h>
#include <stdbool.h>

/* Il contesto per QUIC: ALPN `h3`, 0-RTT SPENTO, certificato di sessione. */
SSL_CTX *tls_contesto_quic(const char *pem, const char *key);

/* Il contesto per la pagina in TCP: ALPN `http/1.1`, certificato longevo. */
SSL_CTX *tls_contesto_pagina(const char *pem, const char *key);

#endif
