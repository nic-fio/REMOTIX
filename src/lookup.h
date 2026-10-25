/*
 * lookup.h — the two tables that transport.c searched LINEARLY for every packet, now hashed.
 *
 *   · the CID map (`cid_find()`): up to 256 connections x 9 connection ids (the client may ask for up to 8 and the original
 *     DCID is bound too) = ~2300 entries, scanned in full for every packet whose DCID is unknown — i.e. for the packets a
 *     flood sends (measured on an Intel N100: ~4.4 us a miss, ~2 us a hit at 2304 entries; 0.1 us with the 72 entries of 8 users);
 *   · the ring of used Retry tokens (`token_used()`): 4096 entries scanned for every Initial with a valid token (~3.8 us, always).
 *
 * ⛔ A hash with a KEY: the CID map is hashed with SipHash-2-4 under a key the attacker does not know (it is derived from the
 *    server's static secret by transport_open_fd()), so he cannot choose DCIDs that fall in one chain.  The token ring is
 *    indexed by the token's own hash, which is already keyed (token_hash() in transport.c).
 * ⭐ Same answers as the linear scans, DUPLICATES included: cid_find() returns the entry with the LOWEST array index among
 *    those with the same id (the first one a scan finds), a hole is filled lowest-first, unbinding an id releases all its
 *    entries.  benches/unit/transport-lookup/test.c runs both against each other.
 * No ngtcp2 here: a plain struct with the same layout as ngtcp2_cid, so a test can include this file alone.
 */
#ifndef LOOKUP_H
#define LOOKUP_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* ── SipHash-2-4 ─────────────────────────────────────────────────────────── */
static inline uint64_t lk_rotl(uint64_t x, int b) { return (x << b) | (x >> (64 - b)); }
static inline uint64_t lk_le64(const uint8_t *p)
{
	uint64_t v = 0;
	for (int i = 7; i >= 0; i--)
		v = (v << 8) | p[i];
	return v;
}
#define LK_SIPROUND                                                                 \
	do {                                                                        \
		v0 += v1; v1 = lk_rotl(v1, 13); v1 ^= v0; v0 = lk_rotl(v0, 32);     \
		v2 += v3; v3 = lk_rotl(v3, 16); v3 ^= v2;                           \
		v0 += v3; v3 = lk_rotl(v3, 21); v3 ^= v0;                           \
		v2 += v1; v1 = lk_rotl(v1, 17); v1 ^= v2; v2 = lk_rotl(v2, 32);     \
	} while (0)
static inline uint64_t lk_sip(const uint8_t key[16], const uint8_t *in, size_t n)
{
	uint64_t k0 = lk_le64(key), k1 = lk_le64(key + 8);
	uint64_t v0 = k0 ^ 0x736f6d6570736575ull, v1 = k1 ^ 0x646f72616e646f6dull;
	uint64_t v2 = k0 ^ 0x6c7967656e657261ull, v3 = k1 ^ 0x7465646279746573ull;
	const uint8_t *end = in + (n & ~(size_t)7);
	uint64_t b = (uint64_t)n << 56;

	for (; in != end; in += 8) {
		uint64_t m = lk_le64(in);
		v3 ^= m;
		LK_SIPROUND;
		LK_SIPROUND;
		v0 ^= m;
	}
	for (size_t i = 0; i < (n & 7); i++)
		b |= (uint64_t)in[i] << (8 * i);
	v3 ^= b;
	LK_SIPROUND;
	LK_SIPROUND;
	v0 ^= b;
	v2 ^= 0xff;
	LK_SIPROUND;
	LK_SIPROUND;
	LK_SIPROUND;
	LK_SIPROUND;
	return v0 ^ v1 ^ v2 ^ v3;
}

/* ── the CID map ─────────────────────────────────────────────────────────── */
#define LK_CID_MAX 20 /* NGTCP2_MAX_CIDLEN */
typedef struct {
	size_t datalen;
	uint8_t data[LK_CID_MAX];
} lk_cid;

typedef struct {
	lk_cid cid;
	void *c;
	bool used;
	bool plain; /* the id carries no valid tag (cid.h): counted in `plain_n` of the map */
	uint32_t next; /* the next entry of the same bucket, as index + 1; 0 = end */
} lk_entry;

typedef struct {
	lk_entry *e;
	size_t n, cap;       /* n = entries ever appended (holes included), as `ncids` was */
	uint32_t *bucket;    /* index + 1 of the first entry of each bucket; 0 = empty */
	size_t nb;           /* a power of two, >= 2 * cap, 0 before the first bind */
	size_t lowest_hole;  /* every index below it is used */
	size_t plain_n;      /* how many used entries are `plain` (cid-firmati: 0 in steady state) */
	uint8_t key[16];     /* SipHash key: set by the owner, all zero is valid (the fuzz harness) */
} lk_cidmap;

static inline size_t lk_bucket_of(const lk_cidmap *m, const uint8_t *id, size_t len)
{
	return (size_t)(lk_sip(m->key, id, len) & (uint64_t)(m->nb - 1));
}

static inline void lk_link(lk_cidmap *m, size_t i)
{
	size_t b = lk_bucket_of(m, m->e[i].cid.data, m->e[i].cid.datalen);

	m->e[i].next = m->bucket[b];
	m->bucket[b] = (uint32_t)(i + 1);
}

static inline void lk_unlink(lk_cidmap *m, size_t i)
{
	size_t b = lk_bucket_of(m, m->e[i].cid.data, m->e[i].cid.datalen);

	for (uint32_t *pp = &m->bucket[b]; *pp; pp = &m->e[*pp - 1].next)
		if (*pp == (uint32_t)(i + 1)) {
			*pp = m->e[i].next;
			break;
		}
}

/* The buckets again, for `cap` entries.  false = out of memory (the map is left as it was). */
static inline bool lk_rebuild(lk_cidmap *m, size_t cap)
{
	size_t nb = 64;
	uint32_t *nbk;

	while (nb < 2 * cap)
		nb <<= 1;
	nbk = calloc(nb, sizeof *nbk);
	if (!nbk)
		return false;
	free(m->bucket);
	m->bucket = nbk;
	m->nb = nb;
	for (size_t i = 0; i < m->n; i++)
		if (m->e[i].used)
			lk_link(m, i);
	return true;
}

/* false = out of memory.  An id that could not be bound must be refused by the caller (see cid_bind()). */
static inline bool lk_cid_bind_p(lk_cidmap *m, const lk_cid *cid, void *c, bool plain)
{
	size_t i = m->lowest_hole;

	while (i < m->n && m->e[i].used)
		i++;
	m->lowest_hole = i;
	if (i == m->n) {
		if (m->n == m->cap) {
			size_t nc = m->cap ? m->cap * 2 : 32;
			lk_entry *ne = realloc(m->e, nc * sizeof *ne);

			if (!ne)
				return false;
			m->e = ne;
			m->cap = nc;
		}
		if (m->nb < 2 * m->cap && !lk_rebuild(m, m->cap))
			return false;
		m->n++;
	}
	m->e[i].cid = *cid;
	m->e[i].c = c;
	m->e[i].used = true;
	m->e[i].plain = plain;
	m->plain_n += plain;
	lk_link(m, i);
	m->lowest_hole = i + 1;
	return true;
}

static inline bool lk_cid_bind(lk_cidmap *m, const lk_cid *cid, void *c)
{
	return lk_cid_bind_p(m, cid, c, false);
}

/* The connection of the entry with this id and the LOWEST index (what a scan from 0 returns), or NULL. */
static inline void *lk_cid_find(const lk_cidmap *m, const uint8_t *id, size_t len)
{
	const lk_entry *best = NULL;
	size_t best_i = 0;

	if (!m->nb || len > LK_CID_MAX)
		return NULL;
	for (uint32_t k = m->bucket[lk_bucket_of(m, id, len)]; k; k = m->e[k - 1].next) {
		const lk_entry *x = &m->e[k - 1];

		if (x->used && x->cid.datalen == len && memcmp(x->cid.data, id, len) == 0 && (!best || (size_t)(k - 1) < best_i)) {
			best = x;
			best_i = k - 1;
		}
	}
	return best ? best->c : NULL;
}

static inline void lk_release(lk_cidmap *m, size_t i)
{
	lk_unlink(m, i);
	m->e[i].used = false;
	m->plain_n -= m->e[i].plain;
	if (i < m->lowest_hole)
		m->lowest_hole = i;
}

/* Every entry with this id is released (duplicates too). */
static inline void lk_cid_unbind(lk_cidmap *m, const lk_cid *cid)
{
	if (!m->nb || cid->datalen > LK_CID_MAX)
		return;
	for (uint32_t k = m->bucket[lk_bucket_of(m, cid->data, cid->datalen)]; k;) {
		size_t i = k - 1;

		k = m->e[i].next; /* read before the entry is unlinked */
		if (m->e[i].used && m->e[i].cid.datalen == cid->datalen && memcmp(m->e[i].cid.data, cid->data, cid->datalen) == 0)
			lk_release(m, i);
	}
}

static inline void lk_cid_unbind_all(lk_cidmap *m, void *c)
{
	for (size_t i = 0; i < m->n; i++)
		if (m->e[i].used && m->e[i].c == c)
			lk_release(m, i);
}

static inline void lk_cid_free(lk_cidmap *m)
{
	free(m->e);
	free(m->bucket);
	memset(m, 0, sizeof *m);
}

/* ── the ring of used Retry tokens ───────────────────────────────────────── */
#define LK_TOKENS 4096
#define LK_TOKEN_BUCKETS 8192 /* >= 2 * LK_TOKENS, a power of two */

typedef struct {
	uint64_t hash;
	uint64_t until;
	uint32_t next;   /* same bucket, index + 1 */
	bool linked;
} lk_tok;

typedef struct {
	lk_tok r[LK_TOKENS];
	uint32_t bucket[LK_TOKEN_BUCKETS];
	size_t next; /* the slot the next token overwrites */
} lk_ring;

static inline size_t lk_tok_bucket(uint64_t h) { return (size_t)((h ^ (h >> 32) ^ (h >> 17)) & (LK_TOKEN_BUCKETS - 1)); }

/* Is there an entry with this hash that has not expired?  (what `token_used()` scanned for) */
static inline bool lk_tok_used(const lk_ring *g, uint64_t h, uint64_t now)
{
	for (uint32_t k = g->bucket[lk_tok_bucket(h)]; k; k = g->r[k - 1].next)
		if (g->r[k - 1].until > now && g->r[k - 1].hash == h)
			return true;
	return false;
}

/* Remembers `h` until `until`, over the oldest slot.  true = that slot still held a token that had NOT expired (forgotten). */
static inline bool lk_tok_keep(lk_ring *g, uint64_t h, uint64_t now, uint64_t until)
{
	size_t i = g->next;
	bool forgot = g->r[i].until > now;

	if (g->r[i].linked)
		for (uint32_t *pp = &g->bucket[lk_tok_bucket(g->r[i].hash)]; *pp; pp = &g->r[*pp - 1].next)
			if (*pp == (uint32_t)(i + 1)) {
				*pp = g->r[i].next;
				break;
			}
	g->r[i].hash = h;
	g->r[i].until = until;
	g->r[i].linked = true;
	g->r[i].next = g->bucket[lk_tok_bucket(h)];
	g->bucket[lk_tok_bucket(h)] = (uint32_t)(i + 1);
	g->next = (i + 1) % LK_TOKENS;
	return forgot;
}

#endif
