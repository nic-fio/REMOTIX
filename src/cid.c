/* cid.c — see cid.h. */
#include "cid.h"

#include <stdlib.h>
#include <string.h>

#include <openssl/core_names.h>
#include <openssl/crypto.h>
#include <openssl/evp.h>
#include <openssl/params.h>
#include <openssl/rand.h>

struct cidkey {
	EVP_MAC *mac;
	EVP_MAC_CTX *ctx; /* the key is set once; EVP_MAC_init(ctx, NULL, ...) restarts the MAC with the same key (~170 ns) */
};

static bool tag_of(cidkey *k, const uint8_t *nonce, uint8_t tag[CID_TAG])
{
	uint8_t full[32];
	size_t n = 0;
	if (!EVP_MAC_init(k->ctx, NULL, 0, NULL) || !EVP_MAC_update(k->ctx, nonce, CID_NONCE) ||
	    !EVP_MAC_final(k->ctx, full, &n, sizeof full) || n < CID_TAG)
		return false;
	memcpy(tag, full, CID_TAG);
	OPENSSL_cleanse(full, sizeof full);
	return true;
}

cidkey *cidkey_new(const uint8_t *secret, size_t secretlen)
{
	static const char DOMAIN[] = "REMOTIX CID v1";
	uint8_t key[32] = {0};
	size_t n = 0;
	cidkey *k = calloc(1, sizeof *k);
	OSSL_PARAM p[2];
	EVP_MAC_CTX *derive = NULL;
	if (!k || !secret || secretlen == 0)
		goto bad;
	k->mac = EVP_MAC_fetch(NULL, "HMAC", NULL);
	if (!k->mac)
		goto bad;
	p[0] = OSSL_PARAM_construct_utf8_string(OSSL_MAC_PARAM_DIGEST, (char *)"SHA256", 0);
	p[1] = OSSL_PARAM_construct_end();
	/* the key of the ids: HMAC(secret, DOMAIN) — a different key from every other use of the secret */
	derive = EVP_MAC_CTX_new(k->mac);
	if (!derive || !EVP_MAC_init(derive, secret, secretlen, p) || !EVP_MAC_update(derive, (const uint8_t *)DOMAIN, sizeof DOMAIN - 1) ||
	    !EVP_MAC_final(derive, key, &n, sizeof key) || n != sizeof key)
		goto bad;
	k->ctx = EVP_MAC_CTX_new(k->mac);
	if (!k->ctx || !EVP_MAC_init(k->ctx, key, sizeof key, p))
		goto bad;
	EVP_MAC_CTX_free(derive);
	OPENSSL_cleanse(key, sizeof key);
	return k;
bad:
	EVP_MAC_CTX_free(derive);
	OPENSSL_cleanse(key, sizeof key);
	cidkey_free(k);
	return NULL;
}

void cidkey_free(cidkey *k)
{
	if (!k)
		return;
	EVP_MAC_CTX_free(k->ctx);
	EVP_MAC_free(k->mac);
	free(k);
}

bool cidkey_make(cidkey *k, uint8_t cid[CID_LEN])
{
	if (!k || RAND_bytes(cid, CID_NONCE) != 1)
		return false;
	return tag_of(k, cid, cid + CID_NONCE);
}

bool cidkey_ok(cidkey *k, const uint8_t *cid, size_t len)
{
	uint8_t tag[CID_TAG];
	if (!k || len != CID_LEN || !tag_of(k, cid, tag))
		return false;
	return CRYPTO_memcmp(tag, cid + CID_NONCE, CID_TAG) == 0;
}
