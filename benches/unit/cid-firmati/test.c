/*
 * test.c — unit test of src/cid.c (the server's Connection IDs that carry a tag; `cid-firmati`, R9 of the audit of 25 Oct 2026).
 *
 * HOW: the REAL src/cid.c over the REAL OpenSSL (no stubs: what is tested is also that EVP_MAC_init(ctx, NULL, ...) restarts the
 * MAC with the same key, which a stub could not tell).  The expected tag is computed apart, with the one-shot HMAC() and the key
 * derived by hand, so the module is checked against the definition in cid.h and not against itself.
 *
 * What it covers:
 *   shape       an id is CID_LEN bytes; every id made verifies; a wrong length does not (0, 17, 19, 20, 21)
 *   definition  nonce = first 10 bytes; tag = first 8 bytes of HMAC-SHA256(HMAC-SHA256(secret, "REMOTIX CID v1"), nonce)
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
static void expected_tag(const uint8_t *secret, size_t slen, const uint8_t *nonce, uint8_t tag[CID_TAG])
{
	uint8_t key[32], full[32];
	unsigned n;
	HMAC(EVP_sha256(), secret, (int)slen, (const uint8_t *)"REMOTIX CID v1", 14, key, &n);
	HMAC(EVP_sha256(), key, 32, nonce, CID_NONCE, full, &n);
	memcpy(tag, full, CID_TAG);
}

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
	CHECK(cidkey_make(k, id) && cidkey_ok(k, id, CID_LEN), "an id made verifies");
	CHECK(!cidkey_ok(k, id, 0) && !cidkey_ok(k, id, CID_LEN - 1) && !cidkey_ok(k, id, CID_LEN + 1) &&
	      !cidkey_ok(k, id, 20) && !cidkey_ok(k, id, 21), "a wrong length does not verify");

	printf("definition\n");
	for (int i = 0; i < 50; i++) {
		uint8_t t[CID_TAG];
		cidkey_make(k, id);
		expected_tag(secret, sizeof secret, id, t);
		CHECK(memcmp(t, id + CID_NONCE, CID_TAG) == 0, "tag of id %d is the one of the definition", i);
	}

	printf("forgery\n");
	int flips_passed = 0;
	for (int i = 0; i < 200; i++) {
		cidkey_make(k, id);
		for (int b = 0; b < CID_LEN * 8; b++) {
			uint8_t f[CID_LEN];
			memcpy(f, id, CID_LEN);
			f[b / 8] ^= (uint8_t)(1u << (b % 8));
			flips_passed += cidkey_ok(k, f, CID_LEN);
		}
	}
	CHECK(flips_passed == 0, "single-bit flips that still verify: %d of %d", flips_passed, 200 * CID_LEN * 8);
	int random_passed = 0;
	for (int i = 0; i < 200000; i++) {
		uint8_t r[CID_LEN];
		RAND_bytes(r, sizeof r);
		random_passed += cidkey_ok(k, r, CID_LEN);
	}
	CHECK(random_passed == 0, "random ids that verify: %d of 200000", random_passed);
	memset(id, 0, sizeof id);
	CHECK(!cidkey_ok(k, id, CID_LEN), "all zero does not verify");

	printf("restart\n");
	{
		uint8_t old[CID_LEN];
		cidkey_make(k, old);
		cidkey *again = cidkey_new(secret, sizeof secret);   /* the server restarted: same quic-secret file */
		CHECK(again && cidkey_ok(again, old, CID_LEN), "an id made before the restart verifies after it");
		CHECK(!cidkey_ok(k2, old, CID_LEN), "another secret (the file replaced) does not accept it");
		cidkey_free(again);
	}

	printf("reuse\n");
	{
		int wrong = 0;
		uint8_t ids[16][CID_LEN];
		for (int round = 0; round < 100000; round++) {
			int j = round % 16;
			cidkey_make(k, ids[j]);
			if (!cidkey_ok(k, ids[j], CID_LEN)) wrong++;
			if (round % 3 == 0) {
				uint8_t junk[CID_LEN];
				memcpy(junk, ids[j], CID_LEN);
				junk[CID_LEN - 1] ^= 1;
				if (cidkey_ok(k, junk, CID_LEN)) wrong++;
			}
		}
		CHECK(wrong == 0, "wrong answers in 100000 interleaved rounds: %d", wrong);
	}

	printf("unique\n");
	{
		enum { N = 100000 };
		uint8_t (*all)[CID_LEN] = malloc((size_t)N * CID_LEN);
		for (int i = 0; i < N; i++) cidkey_make(k, all[i]);
		qsort(all, N, CID_LEN, cmp_id);
		int dup = 0;
		for (int i = 1; i < N; i++) dup += memcmp(all[i - 1], all[i], CID_LEN) == 0;
		CHECK(dup == 0, "equal ids among %d: %d", N, dup);
		free(all);
	}

	printf("errors\n");
	CHECK(cidkey_new(NULL, 32) == NULL && cidkey_new(secret, 0) == NULL, "NULL / empty secret");
	CHECK(!cidkey_make(NULL, id) && !cidkey_ok(NULL, id, CID_LEN), "NULL key");
	cidkey_free(NULL);
	CHECK(cidkey_errors(k) == 0 && cidkey_errors(NULL) == 0, "no HMAC failure so far (%u)", cidkey_errors(k));
	cidkey_ok(k, id, CID_LEN);
	CHECK(cidkey_errors(k) == 0, "a bad tag is not an HMAC failure");
	{
		cidkey *broken = cidkey_new(secret, sizeof secret);
		uint8_t good[CID_LEN];
		cidkey_make(broken, good);
		EVP_MAC_CTX_free(broken->ctx);
		broken->ctx = EVP_MAC_CTX_new(broken->mac);       /* a context with no key: from here every HMAC fails */
		CHECK(!cidkey_ok(broken, good, CID_LEN), "an id cannot be verified when the HMAC fails: false");
		CHECK(!cidkey_make(broken, good), "and none can be made");
		CHECK(cidkey_errors(broken) == 2, "two failures counted (%u)", cidkey_errors(broken));
		cidkey_ok(broken, good, CID_LEN - 1);          /* a wrong length is answered before the HMAC: no failure */
		CHECK(cidkey_errors(broken) == 2, "a wrong length is not an HMAC failure");
		cidkey_free(broken);
	}
	cidkey_free(k);
	cidkey_free(k2);
	printf("\n%d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
