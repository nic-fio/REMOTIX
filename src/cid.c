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
	unsigned errors;  /* the times the HMAC itself failed (never seen: OpenSSL out of memory); transport.c writes a line when it grows */
};

#define KIND_CONN 'C'
#define KIND_RETRY 'R'

/* The tag of `kind`: HMAC over «kind, nonce» and, for a connection id, the epoch (big endian, 8 bytes). */
static bool tag_of(cidkey *k, int kind, const uint8_t *nonce, uint64_t epoch, uint8_t tag[CID_TAG])
{
	uint8_t full[32], msg[1 + CID_NONCE + 8];
	size_t n = 0, m = 0;
	msg[m++] = (uint8_t)kind;
	memcpy(msg + m, nonce, CID_NONCE);
	m += CID_NONCE;
	if (kind == KIND_CONN)
		for (int i = 7; i >= 0; i--)
			msg[m++] = (uint8_t)(epoch >> (8 * i));
	if (!EVP_MAC_init(k->ctx, NULL, 0, NULL) || !EVP_MAC_update(k->ctx, msg, m) ||
	    !EVP_MAC_final(k->ctx, full, &n, sizeof full) || n < CID_TAG) {
		k->errors++; /* `cidkey_ok()` then says false (not signed) and `cidkey_make()` false: the caller must not take it for a forgery */
		return false;
	}
	memcpy(tag, full, CID_TAG);
	OPENSSL_cleanse(full, sizeof full);
	return true;
}

cidkey *cidkey_new(const uint8_t *secret, size_t secretlen)
{
	static const char DOMAIN[] = "REMOTIX CID v2";
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

unsigned cidkey_errors(const cidkey *k)
{
	return k ? k->errors : 0;
}

static bool make(cidkey *k, int kind, uint8_t cid[CID_LEN], uint64_t epoch)
{
	if (!k || RAND_bytes(cid, CID_NONCE) != 1)
		return false;
	return tag_of(k, kind, cid, epoch, cid + CID_NONCE);
}

bool cidkey_make(cidkey *k, uint8_t cid[CID_LEN], uint64_t epoch)
{
	return make(k, KIND_CONN, cid, epoch);
}

bool cidkey_make_retry(cidkey *k, uint8_t cid[CID_LEN])
{
	return make(k, KIND_RETRY, cid, 0);
}

/* 1 = the tag of `kind` and `epoch` is the id's, 0 = it is not, -1 = the HMAC itself failed */
static int check(cidkey *k, int kind, const uint8_t *cid, uint64_t epoch)
{
	uint8_t tag[CID_TAG];
	if (!tag_of(k, kind, cid, epoch, tag))
		return -1;
	return CRYPTO_memcmp(tag, cid + CID_NONCE, CID_TAG) == 0;
}

bool cidkey_ok(cidkey *k, const uint8_t *cid, size_t len, uint64_t epoch)
{
	int r;
	if (!k || len != CID_LEN)
		return false;
	r = check(k, KIND_CONN, cid, epoch);
	if (r != 0)
		return r == 1;
	return epoch > 0 && check(k, KIND_CONN, cid, epoch - 1) == 1;
}

bool cidkey_ok_retry(cidkey *k, const uint8_t *cid, size_t len)
{
	if (!k || len != CID_LEN)
		return false;
	return check(k, KIND_RETRY, cid, 0) == 1;
}
