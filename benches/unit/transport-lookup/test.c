/*
 * test.c — the hashed CID map and the hashed ring of used Retry tokens (src/lookup.h) against the LINEAR scans that
 * src/transport.c used to do (cid_find / cid_bind / cid_unbind / cid_unbind_all, token_used / token_keep): the same
 * answers for the same sequence of operations, duplicates and holes and growth and expiry included.
 *
 * HOW: lookup.h is included alone (no ngtcp2, no OpenSSL).  The reference below is the old code, copied (the types renamed).
 * A seeded generator drives both with random binds (a small id space, so the same id is often bound twice), unbinds by id and by
 * connection, and lookups of bound and unknown ids; after EVERY operation a sample of lookups must agree; the whole table is
 * compared at the end.  Tokens: random hashes from a small space, a clock that moves, 20000 keeps over the 4096 ring; `used` and
 * the count of forgotten (still valid, overwritten) tokens must agree after every step.
 *   1. SipHash-2-4 against the reference vectors (key 00..0f, inputs of 0 and 1 and 8 and 15 bytes);
 *   2. the CID map against the scan: 200000 operations, 3 seeds;
 *   3. a map of 2304 consecutive ids (what 256 connections x 9 ids look like): the longest chain stays short, and a DIFFERENT key
 *      gives a different layout (the key matters);
 *   4. the token ring against the scan: 20000 keeps, expiry, overwrite of valid ones (forgotten), replays;
 *   5. a miss costs far less than a scan: 2304 entries, 200000 lookups, timed against the scan (not a pass/fail on the clock: the
 *      numbers are printed; the check is that the hash is not slower).
 *   6. an id is released by its value, by its connection and by the free of the map, and the hole is reused (cid-firmati: the map is
 *      always searched, whatever the tag of an id says, so a connection is found by any id it was given).
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=1 --memory=512m -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && gcc -std=gnu11 -O2 -Wall -Wextra -I/albero/src /albero/benches/unit/transport-lookup/test.c -o test && ./test'
 * Exit code 0 = every check passed.
 */
#define _GNU_SOURCE
#include "lookup.h"

#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static int checks, bad;
#define CHECK(cond, ...)                                                          \
	do {                                                                      \
		checks++;                                                         \
		if (!(cond)) {                                                    \
			bad++;                                                    \
			printf("  FAIL %s:%d  %s  -- ", __FILE__, __LINE__, #cond); \
			printf(__VA_ARGS__);                                      \
			printf("\n");                                             \
		}                                                                 \
	} while (0)

static uint64_t rng_state;
static uint64_t rnd(void)
{
	rng_state ^= rng_state << 13;
	rng_state ^= rng_state >> 7;
	rng_state ^= rng_state << 17;
	return rng_state;
}

/* ── the reference: the old linear code of transport.c ─────────────────── */
typedef struct {
	lk_cid cid;
	void *c;
	bool used;
} ref_entry;
typedef struct {
	ref_entry *e;
	size_t n, cap;
} ref_map;

static void *ref_find(const ref_map *t, const uint8_t *dcid, size_t len)
{
	for (size_t i = 0; i < t->n; i++) {
		if (!t->e[i].used)
			continue;
		if (t->e[i].cid.datalen == len && memcmp(t->e[i].cid.data, dcid, len) == 0)
			return t->e[i].c;
	}
	return NULL;
}
static void ref_bind(ref_map *t, const lk_cid *cid, void *c)
{
	for (size_t i = 0; i < t->n; i++)
		if (!t->e[i].used) {
			t->e[i].cid = *cid;
			t->e[i].c = c;
			t->e[i].used = true;
			return;
		}
	if (t->n == t->cap) {
		size_t nc = t->cap ? t->cap * 2 : 32;
		t->e = realloc(t->e, nc * sizeof *t->e);
		t->cap = nc;
	}
	t->e[t->n].cid = *cid;
	t->e[t->n].c = c;
	t->e[t->n].used = true;
	t->n++;
}
static void ref_unbind(ref_map *t, const lk_cid *cid)
{
	for (size_t i = 0; i < t->n; i++)
		if (t->e[i].used && t->e[i].cid.datalen == cid->datalen && memcmp(t->e[i].cid.data, cid->data, cid->datalen) == 0)
			t->e[i].used = false;
}
static void ref_unbind_all(ref_map *t, void *c)
{
	for (size_t i = 0; i < t->n; i++)
		if (t->e[i].used && t->e[i].c == c)
			t->e[i].used = false;
}

typedef struct {
	struct {
		uint64_t hash, until;
	} r[LK_TOKENS];
	size_t next;
	unsigned forgotten;
} ref_ring;
static bool ref_tok_used(const ref_ring *g, uint64_t h, uint64_t now)
{
	for (size_t i = 0; i < LK_TOKENS; i++)
		if (g->r[i].until > now && g->r[i].hash == h)
			return true;
	return false;
}
static void ref_tok_keep(ref_ring *g, uint64_t h, uint64_t now, uint64_t until)
{
	size_t i = g->next;
	if (g->r[i].until > now)
		g->forgotten++;
	g->r[i].hash = h;
	g->r[i].until = until;
	g->next = (i + 1) % LK_TOKENS;
}

/* ids from a small space so that the same id is often bound again (duplicates), with lengths 1..20 */
static lk_cid make_id(unsigned space)
{
	lk_cid c;
	unsigned v = (unsigned)(rnd() % space);

	memset(&c, 0, sizeof c);
	c.datalen = 1 + v % LK_CID_MAX;
	for (size_t i = 0; i < c.datalen; i++)
		c.data[i] = (uint8_t)(v * 31 + i * 7);
	return c;
}

static void test_sip(void)
{
	uint8_t key[16], in[16];

	for (int i = 0; i < 16; i++) {
		key[i] = (uint8_t)i;
		in[i] = (uint8_t)i;
	}
	/* the reference vectors of SipHash-2-4 (Aumasson-Bernstein), key 000102..0f, input 00 01 02 ... */
	CHECK(lk_sip(key, in, 0) == 0x726fdb47dd0e0e31ull, "siphash of 0 bytes %016llx", (unsigned long long)lk_sip(key, in, 0));
	CHECK(lk_sip(key, in, 1) == 0x74f839c593dc67fdull, "siphash of 1 byte");
	CHECK(lk_sip(key, in, 8) == 0x93f5f5799a932462ull, "siphash of 8 bytes");
	CHECK(lk_sip(key, in, 15) == 0xa129ca6149be45e5ull, "siphash of 15 bytes");
}

static void test_cid_equivalence(void)
{
	static const uint64_t SEEDS[3] = {0x9e3779b97f4a7c15ull, 0x0123456789abcdefull, 0xdeadbeefcafef00dull};
	void *conns[40];

	for (int i = 0; i < 40; i++)
		conns[i] = (void *)(uintptr_t)(0x1000 + 16 * i);
	for (int s = 0; s < 3; s++) {
		lk_cidmap m;
		ref_map r;
		long disagree = 0, ops = 0;

		memset(&m, 0, sizeof m);
		memset(&r, 0, sizeof r);
		for (int i = 0; i < 16; i++)
			m.key[i] = (uint8_t)(s * 40 + i); /* a key, as transport_open_fd() sets one */
		rng_state = SEEDS[s];
		for (int op = 0; op < 200000; op++, ops++) {
			unsigned k = (unsigned)(rnd() % 100);
			unsigned space = op < 100000 ? 700 : 3000; /* grows the table past several doublings, then holes */

			if (k < 45) {
				lk_cid id = make_id(space);
				void *c = conns[rnd() % 40];

				if (!lk_cid_bind(&m, &id, c))
					disagree++;
				ref_bind(&r, &id, c);
			} else if (k < 70) {
				lk_cid id = make_id(space);

				lk_cid_unbind(&m, &id);
				ref_unbind(&r, &id);
			} else if (k < 72) {
				void *c = conns[rnd() % 40];

				lk_cid_unbind_all(&m, c);
				ref_unbind_all(&r, c);
			}
			for (int q = 0; q < 4; q++) {
				lk_cid id = make_id(space + 50); /* some unknown ids too */

				if (lk_cid_find(&m, id.data, id.datalen) != ref_find(&r, id.data, id.datalen))
					disagree++;
			}
		}
		/* the whole table, at the end: every id of the space */
		for (unsigned v = 0; v < 3100; v++) {
			lk_cid id;

			memset(&id, 0, sizeof id);
			id.datalen = 1 + v % LK_CID_MAX;
			for (size_t i = 0; i < id.datalen; i++)
				id.data[i] = (uint8_t)(v * 31 + i * 7);
			if (lk_cid_find(&m, id.data, id.datalen) != ref_find(&r, id.data, id.datalen))
				disagree++;
		}
		/* the table itself, slot by slot: the same holes, the same ids, the same owners */
		{
			long slots = 0;

			for (size_t i = 0; i < m.n && i < r.n; i++)
				if (m.e[i].used != r.e[i].used ||
				    (m.e[i].used && (m.e[i].c != r.e[i].c || m.e[i].cid.datalen != r.e[i].cid.datalen ||
				                     memcmp(m.e[i].cid.data, r.e[i].cid.data, m.e[i].cid.datalen) != 0)))
					slots++;
			CHECK(slots == 0, "seed %d: %ld slots of the final table differ from the reference, entry by entry", s, slots);
		}
		CHECK(disagree == 0, "seed %d: the hashed map and the scan disagree %ld times in %ld operations (%zu entries, %zu in the reference)",
		      s, disagree, ops, m.n, r.n);
		CHECK(m.n == r.n, "seed %d: the same number of entries ever appended (%zu / %zu): the lowest hole is filled first", s, m.n, r.n);
		lk_cid_free(&m);
		free(r.e);
	}
}

static void test_chains(void)
{
	lk_cidmap a, b;
	size_t longest[2] = {0, 0};
	void *c = (void *)0x1000;

	memset(&a, 0, sizeof a);
	memset(&b, 0, sizeof b);
	for (int i = 0; i < 16; i++) {
		a.key[i] = (uint8_t)i;
		b.key[i] = (uint8_t)(0xf0 + i);
	}
	for (int i = 0; i < 2304; i++) { /* 256 connections x 9 ids, here consecutive: the worst friendly case for a weak hash */
		lk_cid id;

		memset(&id, 0, sizeof id);
		id.datalen = 18;
		id.data[0] = (uint8_t)i;
		id.data[1] = (uint8_t)(i >> 8);
		CHECK(lk_cid_bind(&a, &id, c) && lk_cid_bind(&b, &id, c), "bind %d", i);
	}
	CHECK(a.nb >= 2 * a.cap, "buckets %zu >= 2 x capacity %zu", a.nb, a.cap);
	for (int k = 0; k < 2; k++) {
		lk_cidmap *m = k ? &b : &a;

		for (size_t bk = 0; bk < m->nb; bk++) {
			size_t len = 0;

			for (uint32_t x = m->bucket[bk]; x; x = m->e[x - 1].next)
				len++;
			if (len > longest[k])
				longest[k] = len;
		}
	}
	CHECK(longest[0] <= 12 && longest[1] <= 12, "the longest chain stays short: %zu and %zu for 2304 ids", longest[0], longest[1]);
	{
		size_t differ = 0;

		for (int i = 0; i < 2304; i++)
			if (lk_bucket_of(&a, a.e[i].cid.data, 18) != lk_bucket_of(&b, a.e[i].cid.data, 18))
				differ++;
		CHECK(differ > 2000, "the key matters: another key puts %zu of 2304 ids in other buckets", differ);
	}
	lk_cid_free(&a);
	lk_cid_free(&b);
}

static void test_tokens(void)
{
	static lk_ring g;
	static ref_ring r;
	long disagree = 0;
	uint64_t now = 1000;
	unsigned forgot = 0;

	rng_state = 0x1234abcd5678ef01ull;
	memset(&g, 0, sizeof g);
	memset(&r, 0, sizeof r);
	for (int step = 0; step < 20000; step++) {
		uint64_t h = rnd() % 6000, life = 10 * 1000 + (rnd() % 3) * 5000;

		now += 1 + rnd() % 3; /* the clock moves: the oldest entries expire while the ring is still being filled */
		if (lk_tok_used(&g, h, now) != ref_tok_used(&r, h, now))
			disagree++;
		if (lk_tok_keep(&g, h, now, now + life))
			forgot++;
		ref_tok_keep(&r, h, now, now + life);
		for (int q = 0; q < 3; q++) {
			uint64_t p = rnd() % 6500;

			if (lk_tok_used(&g, p, now) != ref_tok_used(&r, p, now))
				disagree++;
		}
	}
	for (uint64_t h = 0; h < 6500; h++)
		if (lk_tok_used(&g, h, now) != ref_tok_used(&r, h, now) || lk_tok_used(&g, h, now + 30000) != ref_tok_used(&r, h, now + 30000))
			disagree++;
	CHECK(disagree == 0, "the hashed ring and the scan disagree %ld times", disagree);
	CHECK(forgot == r.forgotten, "the same count of tokens forgotten while still valid: %u / %u", forgot, r.forgotten);
	CHECK(g.next == r.next, "the ring advances the same way");
	/* a used token is reported until it expires, an unused one never */
	{
		static lk_ring z;

		memset(&z, 0, sizeof z);
		CHECK(!lk_tok_used(&z, 0, 5) && !lk_tok_used(&z, 77, 5), "an empty ring knows nothing (hash 0 included)");
		lk_tok_keep(&z, 77, 5, 5 + 10);
		CHECK(lk_tok_used(&z, 77, 14) && !lk_tok_used(&z, 77, 15) && !lk_tok_used(&z, 78, 6), "used until the instant it expires");
	}
}

static uint64_t ns(void)
{
	struct timespec t;

	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t)t.tv_sec * 1000000000ull + (uint64_t)t.tv_nsec;
}

static void test_speed(void)
{
	lk_cidmap m;
	ref_map r;
	uintptr_t acc = 0;
	uint8_t miss[18];
	uint64_t t0;
	double hash_ns, scan_ns;
	const int reps = 100000;

	memset(&m, 0, sizeof m);
	memset(&r, 0, sizeof r);
	rng_state = 77;
	for (int i = 0; i < 2304; i++) {
		lk_cid id;

		memset(&id, 0, sizeof id);
		id.datalen = 18;
		for (int k = 0; k < 18; k++)
			id.data[k] = (uint8_t)rnd();
		lk_cid_bind(&m, &id, (void *)(uintptr_t)(i + 1));
		ref_bind(&r, &id, (void *)(uintptr_t)(i + 1));
	}
	for (int k = 0; k < 18; k++)
		miss[k] = (uint8_t)rnd();
	t0 = ns();
	for (int i = 0; i < reps; i++) {
		miss[0] = (uint8_t)i;
		miss[1] = (uint8_t)(i >> 8);
		acc += (uintptr_t)lk_cid_find(&m, miss, 18);
	}
	hash_ns = (double)(ns() - t0) / reps;
	t0 = ns();
	for (int i = 0; i < reps; i++) {
		miss[0] = (uint8_t)i;
		miss[1] = (uint8_t)(i >> 8);
		acc += (uintptr_t)ref_find(&r, miss, 18);
	}
	scan_ns = (double)(ns() - t0) / reps;
	printf("  2304 ids, a lookup of an unknown id: hashed %.0f ns, scan %.0f ns\n", hash_ns, scan_ns);
	CHECK(hash_ns < scan_ns, "the hashed lookup is faster than the scan (%.0f ns against %.0f ns)", hash_ns, scan_ns);
	if (acc == 1)
		puts("");
	lk_cid_free(&m);
	free(r.e);
}

/* the release of ids (cid-firmati, rilettura M1): by value, by connection, and the hole is reused */
static void test_release(void)
{
	lk_cidmap m;
	lk_cid a = {.datalen = 18}, b = {.datalen = 18}, c = {.datalen = 18}, d = {.datalen = 18};
	void *x = (void *)(uintptr_t)1, *y = (void *)(uintptr_t)2;

	memset(&m, 0, sizeof m);
	a.data[0] = 1;
	b.data[0] = 2;
	c.data[0] = 3;
	d.data[0] = 4;
	CHECK(lk_cid_bind(&m, &a, x) && lk_cid_bind(&m, &b, x) && lk_cid_bind(&m, &c, y) && lk_cid_bind(&m, &d, y), "four binds");
	CHECK(lk_cid_find(&m, a.data, 18) == x && lk_cid_find(&m, c.data, 18) == y, "found, whatever the bytes of the id are");
	lk_cid_unbind(&m, &a);
	CHECK(lk_cid_find(&m, a.data, 18) == NULL && lk_cid_find(&m, b.data, 18) == x, "an id released by its value, the other of the connection stays");
	lk_cid_unbind_all(&m, y);
	CHECK(lk_cid_find(&m, c.data, 18) == NULL && lk_cid_find(&m, d.data, 18) == NULL, "the connection gone with all its ids");
	CHECK(lk_cid_bind(&m, &a, x) && lk_cid_find(&m, a.data, 18) == x, "the hole is reused");
	lk_cid_free(&m);
	CHECK(lk_cid_find(&m, a.data, 18) == NULL, "freed map: nothing found");
}

int main(void)
{
	alarm(120); /* a broken chain can loop for ever: that is a failure, not a hang */
	test_sip();
	test_cid_equivalence();
	test_chains();
	test_tokens();
	test_release();
	test_speed();
	printf("\n%d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
