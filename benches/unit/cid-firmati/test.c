/*
 * test.c — unit test of src/cid.c (the server's Connection IDs that carry a tag; `cid-firmati`, R9 of the audit of 25 Oct 2026).
 *
 * HOW: the REAL src/cid.c over the REAL OpenSSL (no stubs: what is tested is also that EVP_MAC_init(ctx, NULL, ...) restarts the
 * MAC with the same key, which a stub could not tell).  The expected tag is computed apart, with the one-shot HMAC() and the key
 * derived by hand, so the module is checked against the definition in cid.h and not against itself.
 *
 * What it covers:
 *   shape       an id is CID_LEN bytes; every id made verifies; a wrong length does not (0, 17, 19, 20, 21)
 *   definition  nonce = first 10 bytes; tag = first 8 bytes of HMAC-SHA256(HMAC-SHA256(secret, "REMOTIX CID v2"), 'C' nonce epoch(8, big endian))
 *               for a connection id, and of ... 'R' nonce for the id of a Retry
 *   epoch       (rilettura M1) an id verifies in its epoch and in the next one, not two epochs later, not before it was made; epoch 0 has no
 *               «epoch before»; the Retry id never verifies as a connection id (and the other way round)
 *   forgery     each of the 144 single-bit flips of 200 ids fails; 200 000 random ids pass none; an all-zero id does not
 *   restart     a NEW key from the same secret (a restarted server) accepts ids made before; another secret does not
 *   reuse       interleaved make/ok on one key for 100 000 rounds stay correct (the MAC context is reused between calls)
 *   unique      100 000 ids made are all different
 *   errors      NULL key, NULL / empty secret; a failing HMAC (the context loses its key) counts in cidkey_errors(), makes ok/make say false, and does not
 *               count a plain forgery
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=1 --memory=512m -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && gcc -std=gnu11 -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=undefined -Wall -Wextra -I/albero/src \
 *        /albero/benches/unit/cid-firmati/test.c -lcrypto -o test && ./test'
 * Exit code 0 = every check passed.
 */
#include "cid.c" /* the module itself, to reach its struct (errors) */

#include <openssl/evp.h>
#include <openssl/hmac.h>
#include <openssl/rand.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int checks, bad;
#define CHECK(cond, ...)                                                      \
	do {                                                                  \
		checks++;                                                     \
		if (!(cond)) {                                                \
			bad++;                                                \
			printf("  FAIL %s:%d  %s  -- ", __FILE__, __LINE__, #cond); \
			printf(__VA_ARGS__);                                  \
			printf("\n");                                         \
		}                                                             \
	} while (0)

/* the tag by the definition of cid.h, written apart from src/cid.c */
static void expected_tag(const uint8_t *secret, size_t slen, int kind, const uint8_t *nonce, uint64_t epoch, uint8_t tag[CID_TAG])
{
	uint8_t key[32], full[32], msg[1 + CID_NONCE + 8];
	unsigned n;
	size_t m = 0;
	HMAC(EVP_sha256(), secret, (int)slen, (const uint8_t *)"REMOTIX CID v2", 14, key, &n);
	msg[m++] = (uint8_t)kind;
	memcpy(msg + m, nonce, CID_NONCE);
	m += CID_NONCE;
	if (kind == 'C')
		for (int i = 7; i >= 0; i--)
			msg[m++] = (uint8_t)(epoch >> (8 * i));
	HMAC(EVP_sha256(), key, 32, msg, m, full, &n);
	memcpy(tag, full, CID_TAG);
}

#define EP 123456u /* the epoch of the tests (any) */

static int cmp_id(const void *a, const void *b) { return memcmp(a, b, CID_LEN); }

int main(void)
{
	uint8_t secret[32], secret2[32], id[CID_LEN];
	RAND_bytes(secret, sizeof secret);
	RAND_bytes(secret2, sizeof secret2);
	cidkey *k = cidkey_new(secret, sizeof secret);
	cidkey *k2 = cidkey_new(secret2, sizeof secret2);
	CHECK(k && k2, "keys");

	printf("shape\n");
	CHECK(CID_NONCE + CID_TAG == CID_LEN, "layout");
	CHECK(cidkey_make(k, id, EP) && cidkey_ok(k, id, CID_LEN, EP), "an id made verifies");
	CHECK(!cidkey_ok(k, id, 0, EP) && !cidkey_ok(k, id, CID_LEN - 1, EP) && !cidkey_ok(k, id, CID_LEN + 1, EP) &&
	      !cidkey_ok(k, id, 20, EP) && !cidkey_ok(k, id, 21, EP), "a wrong length does not verify");

	printf("definition\n");
	for (int i = 0; i < 50; i++) {
		uint8_t t[CID_TAG];
		cidkey_make(k, id, EP);
		expected_tag(secret, sizeof secret, 'C', id, EP, t);
		CHECK(memcmp(t, id + CID_NONCE, CID_TAG) == 0, "tag of id %d is the one of the definition", i);
	}

	printf("forgery\n");
	int flips_passed = 0;
	for (int i = 0; i < 200; i++) {
		cidkey_make(k, id, EP);
		for (int b = 0; b < CID_LEN * 8; b++) {
			uint8_t f[CID_LEN];
			memcpy(f, id, CID_LEN);
			f[b / 8] ^= (uint8_t)(1u << (b % 8));
			flips_passed += cidkey_ok(k, f, CID_LEN, EP);
		}
	}
	CHECK(flips_passed == 0, "single-bit flips that still verify: %d of %d", flips_passed, 200 * CID_LEN * 8);
	int random_passed = 0;
	for (int i = 0; i < 200000; i++) {
		uint8_t r[CID_LEN];
		RAND_bytes(r, sizeof r);
		random_passed += cidkey_ok(k, r, CID_LEN, EP);
	}
	CHECK(random_passed == 0, "random ids that verify: %d of 200000", random_passed);
	memset(id, 0, sizeof id);
	CHECK(!cidkey_ok(k, id, CID_LEN, EP), "all zero does not verify");

	printf("restart\n");
	{
		uint8_t old[CID_LEN];
		cidkey_make(k, old, EP);
		cidkey *again = cidkey_new(secret, sizeof secret);   /* the server restarted: same quic-secret file */
		CHECK(again && cidkey_ok(again, old, CID_LEN, EP), "an id made before the restart verifies after it");
		CHECK(!cidkey_ok(k2, old, CID_LEN, EP), "another secret (the file replaced) does not accept it");
		cidkey_free(again);
	}

	printf("reuse\n");
	{
		int wrong = 0;
		uint8_t ids[16][CID_LEN];
		for (int round = 0; round < 100000; round++) {
			int j = round % 16;
			cidkey_make(k, ids[j], EP);
			if (!cidkey_ok(k, ids[j], CID_LEN, EP)) wrong++;
			if (round % 3 == 0) {
				uint8_t junk[CID_LEN];
				memcpy(junk, ids[j], CID_LEN);
				junk[CID_LEN - 1] ^= 1;
				if (cidkey_ok(k, junk, CID_LEN, EP)) wrong++;
			}
		}
		CHECK(wrong == 0, "wrong answers in 100000 interleaved rounds: %d", wrong);
	}

	printf("unique\n");
	{
		enum { N = 100000 };
		uint8_t (*all)[CID_LEN] = malloc((size_t)N * CID_LEN);
		for (int i = 0; i < N; i++) cidkey_make(k, all[i], EP);
		qsort(all, N, CID_LEN, cmp_id);
		int dup = 0;
		for (int i = 1; i < N; i++) dup += memcmp(all[i - 1], all[i], CID_LEN) == 0;
		CHECK(dup == 0, "equal ids among %d: %d", N, dup);
		free(all);
	}

	printf("epoch\n");
	{
		uint8_t e[CID_LEN], r[CID_LEN];
		CHECK(cidkey_make(k, e, 1000), "make at 1000");
		CHECK(cidkey_ok(k, e, CID_LEN, 1000) && cidkey_ok(k, e, CID_LEN, 1001), "verifies in its own epoch and in the next");
		CHECK(!cidkey_ok(k, e, CID_LEN, 1002) && !cidkey_ok(k, e, CID_LEN, 5000), "...and not two epochs later (a collected id stops counting as signed)");
		CHECK(!cidkey_ok(k, e, CID_LEN, 999), "...and not before it was made");
		CHECK(cidkey_make(k, e, 0) && cidkey_ok(k, e, CID_LEN, 0) && cidkey_ok(k, e, CID_LEN, 1) && !cidkey_ok(k, e, CID_LEN, 2),
		      "epoch 0: no epoch before it to look at, and nothing wraps");
		CHECK(cidkey_make(k, e, UINT64_MAX) && cidkey_ok(k, e, CID_LEN, UINT64_MAX), "the largest epoch");
		{
			uint8_t t[CID_TAG];
			cidkey_make(k, e, 7777);
			expected_tag(secret, sizeof secret, 'C', e, 7777, t);
			CHECK(memcmp(t, e + CID_NONCE, CID_TAG) == 0, "the tag covers the epoch as the definition says");
			expected_tag(secret, sizeof secret, 'C', e, 7778, t);
			CHECK(memcmp(t, e + CID_NONCE, CID_TAG) != 0, "...and not another one");
		}
		CHECK(cidkey_make_retry(k, r), "make the id of a Retry");
		{
			uint8_t t[CID_TAG];
			expected_tag(secret, sizeof secret, 'R', r, 0, t);
			CHECK(memcmp(t, r + CID_NONCE, CID_TAG) == 0, "its tag is the one of the definition (label 'R', no epoch)");
		}
		CHECK(cidkey_ok_retry(k, r, CID_LEN) && !cidkey_ok_retry(k, r, CID_LEN - 1), "it verifies as a Retry id");
		for (uint64_t ep = 0; ep < 4; ep++)
			CHECK(!cidkey_ok(k, r, CID_LEN, ep), "...and never as a connection id (epoch %llu)", (unsigned long long)ep);
		cidkey_make(k, e, EP);
		CHECK(!cidkey_ok_retry(k, e, CID_LEN), "a connection id is not a Retry id");
		CHECK(!cidkey_ok_retry(k2, r, CID_LEN), "another secret does not accept the Retry id");
		{
			int pass = 0;
			for (int i = 0; i < 20000; i++) {
				uint8_t x[CID_LEN];
				cidkey_make_retry(k, x);
				pass += cidkey_ok(k, x, CID_LEN, EP);
			}
			CHECK(pass == 0, "20000 Retry ids that verify as connection ids: %d", pass);
		}
	}

	printf("errors\n");
	CHECK(cidkey_new(NULL, 32) == NULL && cidkey_new(secret, 0) == NULL, "NULL / empty secret");
	CHECK(!cidkey_make(NULL, id, EP) && !cidkey_ok(NULL, id, CID_LEN, EP), "NULL key");
	cidkey_free(NULL);
	CHECK(cidkey_errors(k) == 0 && cidkey_errors(NULL) == 0, "no HMAC failure so far (%u)", cidkey_errors(k));
	cidkey_ok(k, id, CID_LEN, EP);
	CHECK(cidkey_errors(k) == 0, "a bad tag is not an HMAC failure");
	{
		cidkey *broken = cidkey_new(secret, sizeof secret);
		uint8_t good[CID_LEN];
		cidkey_make(broken, good, EP);
		EVP_MAC_CTX_free(broken->ctx);
		broken->ctx = EVP_MAC_CTX_new(broken->mac);       /* a context with no key: from here every HMAC fails */
		CHECK(!cidkey_ok(broken, good, CID_LEN, EP), "an id cannot be verified when the HMAC fails: false");
		CHECK(!cidkey_make(broken, good, EP), "and none can be made");
		CHECK(cidkey_errors(broken) == 2, "two failures counted (%u): one for ok() whatever the epochs, one for make()", cidkey_errors(broken));
		cidkey_ok(broken, good, CID_LEN - 1, EP);          /* a wrong length is answered before the HMAC: no failure */
		CHECK(cidkey_errors(broken) == 2, "a wrong length is not an HMAC failure");
		cidkey_free(broken);
	}
	cidkey_free(k);
	cidkey_free(k2);
	printf("\n%d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
